"""[home semanal] Seleção da década, fileiras de gênero e a regra de NENHUM
filme repetido na home. A lógica (semanal.js, selecao.js) é EXECUTADA sob
node. Trava:
  1. nenhum filme repetido em 365 dias simulados;
  2. rotação semanal: mesma década e mesmos gêneros de segunda a domingo,
     troca na segunda, todos os candidatos dentro do ciclo;
  3. pisos (década >= 3, gênero >= 4 depois da não repetição) e blocos que
     somem quando não há candidato;
  4. nenhuma escolha lê a distribuição dos grupos;
  5. textos fixos, links e o Explorar discreto.
"""
from __future__ import annotations

import json
import re
import subprocess
import textwrap

from test_home_nova import (FILMES_REAIS, FRONT, JS, _filme, _proibidos_em,
                            _violacoes_de_nota, precisa_node)


def _w(corpo: str, dados=None):
    script = textwrap.dedent(f"""
        const S = require({json.dumps(str(JS / "selecao.js"))});
        const T = require({json.dumps(str(JS / "textos_home.js"))});
        const X = require({json.dumps(str(JS / "explorar.js"))});
        const W = require({json.dumps(str(JS / "semanal.js"))});
        const D = JSON.parse(require("fs").readFileSync(0, "utf8"));
        const dia = (i, base = "2026-11-02") => new Date(Date.parse(base + "T12:00:00Z") + i * 86400000)
            .toISOString().slice(0, 10);
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], input=json.dumps(dados),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ===========================================================================
# 1. NENHUM FILME REPETIDO
# ===========================================================================

@precisa_node
def test_nenhuma_home_tem_filme_repetido_em_365_dias():
    out = _w("""
        const ruins = [], tamanhos = [];
        for (let i = 0; i < 365; i++) {
            const h = W.homeDoDia(D, dia(i));
            const vistos = new Set(h.slugs);
            tamanhos.push(h.slugs.length);
            if (vistos.size !== h.slugs.length) ruins.push(dia(i));
            if (!h.decada || h.generos.length !== 2) ruins.push("faltou bloco " + dia(i));
        }
        console.log(JSON.stringify({ruins, min: Math.min(...tamanhos), max: Math.max(...tamanhos)}));
    """, FILMES_REAIS)
    assert out["ruins"] == []
    assert out["min"] >= 1 + 3 + 3 + 3 + 4 + 4 - 4   # 1+4(coleção, ou 3)+3+3+4+4 com a coleção no mínimo de 3


@precisa_node
def test_a_lista_de_exclusao_vale_em_todos_os_blocos():
    out = _w("""
        const vistos = new Set();
        for (let i = 0; i < 365; i++) W.homeDoDia(D, dia(i)).slugs.forEach(s => vistos.add(s));
        const cand = [W.decadasCandidatas(D), W.generosCandidatos(D)].map(l =>
            l.some(c => c.filmes.some(f => f.slug === "obsession-2025")));
        console.log(JSON.stringify({visto: vistos.has("obsession-2025"), cand}));
    """, FILMES_REAIS)
    assert out == {"visto": False, "cand": [False, False]}


# ===========================================================================
# 2. ROTAÇÃO SEMANAL
# ===========================================================================

@precisa_node
def test_semana_comeca_na_segunda_em_sao_paulo():
    out = _w("""console.log(JSON.stringify(["2026-11-01", "2026-11-02", "2026-11-08", "2026-11-09",
        "2026-01-04", "2026-01-05", "2025-12-29"].map(d => S.semanaDe(d))));""", [])
    dom, seg, dom2, seg2, jan_dom, jan_seg, dez_seg = out
    assert seg == dom + 1 and dom2 == seg and seg2 == seg + 1
    assert jan_seg == jan_dom + 1 and dez_seg == jan_dom
    # 2026-11-02 é segunda-feira
    import datetime
    assert datetime.date(2026, 11, 2).weekday() == 0


@precisa_node
def test_decada_e_generos_sao_os_da_semana_de_segunda_a_domingo_e_trocam_na_segunda():
    """A década e o par de gêneros da SEMANA (calculados sem filme usado) são
    os mesmos de segunda a domingo; o dia só se afasta deles quando o
    candidato da semana não alcança o mínimo por causa dos filmes já usados
    acima (manchete, coleção, recém-chegados) — a regra "tenta o próximo"."""
    out = _w("""
        const sem = [];
        for (let k = 0; k < 14; k++) {
            const seg = dia(7 * k), dias = [];
            const semDec = W.selecaoDaDecada(D, seg, {}).decada;
            const semGen = W.fileirasDeGenero(D, seg, {}).map(g => g.chave);
            for (let i = 0; i < 7; i++) {
                const d = dia(7 * k + i), h = W.homeDoDia(D, d);
                const n = h.slugs.length - h.decada.filmes.length
                    - h.generos.reduce((t, g) => t + g.filmes.length, 0);
                const antes = new Set(h.slugs.slice(0, n));
                const livres = (filmes, usados) => filmes.filter(f => !usados.has(f.slug)).length;
                const dec = W.decadasCandidatas(D).find(c => c.decada === semDec);
                dias.push({
                    seg, d, mesmaDecada: h.decada.decada === semDec,
                    decadaInviavel: livres(dec.filmes, antes) < 3,
                    gensDoDia: h.generos.map(g => g.chave), semGen,
                    dec: h.decada.decada,
                });
            }
            sem.push({semDec, semGen, dias});
        }
        console.log(JSON.stringify(sem));
    """, FILMES_REAIS)
    for s in out:
        for d in s["dias"]:
            assert d["mesmaDecada"] or d["decadaInviavel"], d
    # o par de gêneros também só se afasta por colisão; na maioria dos dias a
    # semana inteira (década e par) é a mesma
    iguais = sum(1 for s in out for d in s["dias"] if d["mesmaDecada"] and d["gensDoDia"] == d["semGen"])
    assert iguais >= 0.7 * 14 * 7
    # troca na segunda: semanas seguidas têm década e par diferentes
    for a, b in zip(out, out[1:]):
        assert a["semDec"] != b["semDec"] and a["semGen"] != b["semGen"]


@precisa_node
def test_sem_colisao_os_filmes_sao_os_mesmos_na_semana_toda():
    """Os filmes do bloco só mudam no dia em que colidem com a manchete ou a
    coleção; sem colisão, são os da semana."""
    out = _w("""
        const base = dia(0), sem = [];
        const ref = W.selecaoDaDecada(D, base, {});
        const refG = W.fileirasDeGenero(D, base, {});
        for (let i = 0; i < 7; i++) {
            const d = dia(i), h = W.homeDoDia(D, d);
            const antes = new Set(h.slugs.slice(0, h.slugs.length - h.decada.filmes.length
                - h.generos.reduce((n, g) => n + g.filmes.length, 0)));
            const colide = ref.filmes.some(f => antes.has(f.slug));
            sem.push({colide, igual: JSON.stringify(h.decada.filmes.map(f => f.slug))
                === JSON.stringify(ref.filmes.map(f => f.slug))});
        }
        console.log(JSON.stringify(sem));
    """, FILMES_REAIS)
    for d in out:
        assert d["colide"] or d["igual"]


@precisa_node
def test_todos_os_candidatos_aparecem_dentro_do_ciclo():
    out = _w("""
        const dec = W.decadasCandidatas(D).map(c => c.decada);
        const gen = W.generosCandidatos(D).map(c => c.chave);
        const nD = dec.length, nG = gen.length;
        const vd = [], vg = [];
        for (let k = 0; k < Math.max(nD, nG) + 2; k++) {
            const h = W.homeDoDia(D, dia(7 * k));
            vd.push(h.decada.decada);
            h.generos.forEach(g => vg.push(g.chave));
        }
        console.log(JSON.stringify({dec, gen, vd, vg}));
    """, FILMES_REAIS)
    dec, gen = out["dec"], out["gen"]
    # décadas anteriores a 2000, cronológicas
    assert dec == sorted(dec) and all(d < 2000 for d in dec) and dec == [1960, 1970, 1990]
    assert set(out["vd"][:len(dec)]) == set(dec)
    # gêneros: nenhum repete antes de os N terem aparecido (2 por semana)
    n = len(gen)
    assert n == 13
    ciclo = out["vg"][:n]
    assert len(set(ciclo)) == n and set(ciclo) == set(gen)


@precisa_node
def test_ordem_dos_generos_nao_e_por_contagem():
    out = _w("console.log(JSON.stringify(W.generosCandidatos(D).map(c => c.filmes.length)));",
             FILMES_REAIS)
    assert out != sorted(out, reverse=True)


# ===========================================================================
# 3. PISOS E BLOCOS QUE SOMEM
# ===========================================================================

def _catalogo(decadas, generos):
    """decadas: {ano_da_decada: n}; generos: {nome: n} (sobre filmes de 2010)."""
    filmes = []
    for d, n in decadas.items():
        filmes += [_filme(f"d{d}-{i}", f"D{d} {i:02d}", ano=d + 1, generos=[]) for i in range(n)]
    for g, n in generos.items():
        filmes += [_filme(f"g-{g}-{i}", f"G{g} {i:02d}", ano=2015, generos=[g]) for i in range(n)]
    return filmes


@precisa_node
def test_pisos_de_candidato():
    out = _w("""console.log(JSON.stringify({
        d: W.decadasCandidatas(D).map(c => c.decada),
        g: W.generosCandidatos(D).map(c => c.chave).sort()}));""",
             _catalogo({1960: 2, 1970: 3, 1990: 5, 2000: 9}, {"Aa": 5, "Bb": 6, "Cc": 7}))
    assert out["d"] == [1970, 1990]      # 1960 < 3; 2000 em diante nunca
    assert out["g"] == ["bb", "cc"]      # "aa" tem 5 (< 6)


@precisa_node
def test_decada_com_colisao_cai_no_proximo_candidato():
    f = _catalogo({1970: 3, 1990: 4}, {})
    out = _w("""
        const w = S.semanaDe("2026-11-02");
        const cand = W.decadasCandidatas(D).map(c => c.decada);
        const primeira = cand[w % cand.length];
        const usados = {};
        W.decadasCandidatas(D).find(c => c.decada === primeira).filmes.forEach(f => { usados[f.slug] = true; });
        const livre = W.selecaoDaDecada(D, "2026-11-02", {});
        const comUso = W.selecaoDaDecada(D, "2026-11-02", usados);
        // 1970 tem exatamente 3: um usado derruba a década; 1990 (4) com 1 usado ainda serve
        const um = {}; um[W.decadasCandidatas(D)[0].filmes[0].slug] = true;
        console.log(JSON.stringify({primeira, livre: livre.decada,
            comUso: comUso && comUso.decada, n: comUso && comUso.filmes.length,
            um: W.selecaoDaDecada(D, "2026-11-02", um).decada}));""", f)
    assert out["livre"] == out["primeira"]
    assert out["comUso"] is None or out["comUso"] != out["primeira"]
    assert out["n"] in (None, 3)


@precisa_node
def test_decada_abaixo_do_piso_depois_da_nao_repeticao_some():
    f = _catalogo({1970: 3}, {})
    out = _w("""
        const todos = {}; D.forEach(x => { todos[x.slug] = true; });
        const um = {}; um[D.find(x => x.ano < 2000).slug] = true;
        console.log(JSON.stringify({sem: W.selecaoDaDecada(D, "2026-11-02", um),
                                    livre: W.selecaoDaDecada(D, "2026-11-02", {}).filmes.length,
                                    vazio: W.selecaoDaDecada([], "2026-11-02", {})}));""", f)
    assert out == {"sem": None, "livre": 3, "vazio": None}


@precisa_node
def test_genero_exige_4_depois_da_nao_repeticao_e_tenta_o_proximo():
    f = _catalogo({}, {"Aa": 6, "Bb": 6, "Cc": 6})
    out = _w("""
        const dia0 = "2026-11-02";
        const livre = W.fileirasDeGenero(D, dia0, {});
        // gasta 3 filmes do primeiro gênero escolhido: sobram 3 (< 4), ele cai fora
        const u = {}; livre[0].filmes.slice(0, 3).forEach(x => { u[x.slug] = true; });
        const com = W.fileirasDeGenero(D, dia0, u);
        console.log(JSON.stringify({livre: livre.map(g => g.chave), com: com.map(g => g.chave),
            tam: com.map(g => g.filmes.length),
            repetido: com.some(g => g.filmes.some(x => u[x.slug]))}));""", f)
    assert len(out["livre"]) == 2 and len(set(out["livre"])) == 2
    assert out["livre"][0] not in out["com"]
    assert all(t == 4 for t in out["tam"]) and out["repetido"] is False


@precisa_node
def test_blocos_somem_sem_candidato():
    out = _w("""
        const h = W.homeDoDia(D, "2026-11-02");
        console.log(JSON.stringify({dec: h.decada, gen: h.generos.length}));""",
             _catalogo({1960: 2}, {"Aa": 5}) + [_filme("um", "Um"), _filme("dois", "Dois")])
    assert out == {"dec": None, "gen": 0}
    # um único gênero candidato dá uma fileira só, nunca duas iguais
    out = _w("""console.log(JSON.stringify(W.fileirasDeGenero(D, "2026-11-02", {}).map(g => g.chave)));""",
             _catalogo({}, {"Aa": 8}))
    assert out == ["aa"]


# ===========================================================================
# 4. NENHUMA ESCOLHA LÊ A DISTRIBUIÇÃO
# ===========================================================================

@precisa_node
def test_blocos_semanais_nao_leem_a_distribuicao():
    out = _w("""
        const embaralhado = D.map((f, i) => Object.assign({}, f,
            {distribuicao: {negativas: (i * 7) % 90, medianas: (i * 13) % 50, positivas: 1 + (i * 31) % 60}}));
        const r = [];
        for (const base of [D, embaralhado]) {
            const l = [];
            for (let i = 0; i < 120; i++) {
                const h = W.homeDoDia(base, dia(i));
                l.push([h.slugs, h.decada && h.decada.decada, h.generos.map(g => g.chave)]);
            }
            r.push(JSON.stringify(l));
        }
        console.log(JSON.stringify(r[0] === r[1]));""", FILMES_REAIS)
    assert out is True
    fonte = re.sub(r"/\*.*?\*/|//[^\n]*", "", (JS / "semanal.js").read_text(encoding="utf-8"), flags=re.S)
    assert "distribuicao" not in fonte


# ===========================================================================
# 5. TEXTOS, LINKS E EXPLORAR DISCRETO
# ===========================================================================

@precisa_node
def test_textos_da_decada_e_do_explorar():
    out = _w("""console.log(JSON.stringify({
        t: [1960, 1970, 1990].map(T.tituloDaDecada),
        d: [1960, 1970, 1990].map(T.descricaoDaDecada),
        r: T.RESUMO_EXPLORAR}));""", [])
    assert out["t"] == ["Seleção anos 60", "Seleção anos 70", "Seleção anos 90"]
    assert out["d"][2] == "Filmes do catálogo lançados entre 1990 e 1999."
    assert out["r"] == "Explorar por assunto, década, gênero e país"
    for t in out["t"] + out["d"] + [out["r"]]:
        assert _proibidos_em(t) == [], t
        assert _violacoes_de_nota(t) == [], t
    # os únicos algarismos de prosa são os da própria década
    assert re.sub(r"\b(19[6-9]0|19[6-9]9|[6-9]0)\b", "", " ".join(out["t"] + out["d"])).count("1") == 0
    assert not re.search(r"\d", out["r"])


def test_inicio_liga_os_blocos_e_os_links():
    fonte = (JS / "inicio.js").read_text(encoding="utf-8")
    assert 'HREF_CATALOGO + "?decada=" + d.decada' in fonte
    assert 'HREF_CATALOGO + "?genero=" + encodeURIComponent(g.chave)' in fonte
    assert "T.tituloDaDecada(d.decada)" in fonte and "T.descricaoDaDecada(d.decada)" in fonte
    assert "ed-genero__grade" in fonte and "T.partesDiretorAno" in fonte
    # o still grande da década abre no segundo quadro, como o da coleção
    assert fonte.count('"ed-colecao__destaque"') == 1 and "soAno, 1))" in fonte
    html = re.sub(r"<!--.*?-->", "", (FRONT / "index.html").read_text(encoding="utf-8"), flags=re.S)
    assert "js/semanal.js" in html
    assert html.index("js/explorar.js") < html.index("js/semanal.js") < html.index("js/inicio.js")


def test_css_das_fileiras_de_genero_4_colunas_e_2_no_mobile():
    css = (FRONT / "css" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"\.ed-genero__grade\s*\{[^}]*repeat\(4, 1fr\)", css)
    movel = css[css.index("@media (max-width: 699px)"):]
    assert re.search(r"\.ed-genero__grade\s*\{[^}]*repeat\(2, 1fr\)", movel)
    assert "is-colunas" not in css
