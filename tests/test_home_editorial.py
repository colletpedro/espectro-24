"""[rodada editorial] Home editorial — manchete, coleção do dia,
recém-chegados, nenhum pôster.

Como `test_home_nova.py`, a lógica é EXECUTADA sob `node` (selecao.js e
textos_home.js são puros); o resto lê os arquivos. Trava:
  1. a regra de exibição do logo por classe e o título na linha;
  2. países: no máximo 2, nomes em pt-BR (Intl.DisplayNames);
  3. a coleção do dia: determinística, piso de 3, evita a coleção da
     manchete quando há alternativa;
  4. recém-chegados: 3 por dia, da leva mais recente;
  5. nenhum pôster na home: só caminhos de backdrop, still e logo;
  6. os textos novos passam pelo vocabulário proibido e pelo detector de
     nota; forma (véu, hover, cantos, sombra) e o link de coleção em /filmes.
"""
from __future__ import annotations

import re

import pytest

from test_home_nova import (FILMES_REAIS, FRONT, JS, _filme, _node,
                            _proibidos_em, _violacoes_de_nota, precisa_node)

CSS = (FRONT / "css" / "styles.css").read_text(encoding="utf-8")
INICIO = (JS / "inicio.js").read_text(encoding="utf-8")


def _bloco_editorial_css() -> str:
    return CSS[CSS.index("HOME EDITORIAL"):]


# ===========================================================================
# 1. LOGO POR CLASSE
# ===========================================================================

@precisa_node
def test_regra_de_exibicao_do_logo_por_classe():
    casos = {
        "claro": {"logo": {"path": "/a.png", "idioma": "pt-BR", "classe": "claro"}},
        "mono": {"logo": {"path": "/a.png", "idioma": "en", "classe": "escuro_mono"}},
        "cor": {"logo": {"path": "/a.png", "idioma": "pt-BR", "classe": "escuro_cor"}},
        "desligado": {"logo": {"path": "/a.png", "idioma": "en", "classe": "desligado"}},
        "sem_logo": {"logo": None},
        "sem_path": {"logo": {"path": None, "classe": "claro"}},
    }
    out = _node("""const r = {};
        for (const [k, f] of Object.entries(D)) r[k] = S.modoDoLogo(f);
        console.log(JSON.stringify(r));""", casos)
    assert out == {"claro": "logo", "mono": "logo_branco", "cor": "texto",
                   "desligado": "texto", "sem_logo": "texto", "sem_path": "texto"}


@precisa_node
def test_titulo_brasileiro_na_linha_so_com_logo_exibido_que_nao_e_pt_br():
    def f(classe, difere, idioma="en"):
        return {"titulo": "T", "titulo_difere_do_logo": difere,
                "logo": {"path": "/a.png", "idioma": idioma, "classe": classe}}
    casos = {"en_claro": f("claro", True), "en_mono": f("escuro_mono", True),
             "br_claro": f("claro", False, "pt-BR"), "en_cor": f("escuro_cor", True),
             "en_desligado": f("desligado", True),
             "sem_logo": {"titulo": "T", "titulo_difere_do_logo": False, "logo": None}}
    out = _node("""const r = {};
        for (const [k, f] of Object.entries(D)) r[k] = S.tituloNaLinha(f);
        console.log(JSON.stringify(r));""", casos)
    assert out == {"en_claro": True, "en_mono": True, "br_claro": False,
                   "en_cor": False, "en_desligado": False, "sem_logo": False}
    assert "S.tituloNaLinha(f)" in INICIO


def test_logo_branco_por_filtro_css_e_logo_que_falha_vira_texto():
    css = _bloco_editorial_css()
    assert re.search(r"\.ed-manchete__logo\.is-branco\s*\{\s*filter:\s*brightness\(0\)\s+invert\(1\);", css)
    assert '"logo_branco" ? " is-branco"' in INICIO
    assert 'addEventListener("error", tituloEmTexto)' in INICIO


@precisa_node
def test_modo_do_logo_real_coincide_com_a_classe_publicada():
    out = _node("console.log(JSON.stringify(D.map(f => [f.slug, f.logo && f.logo.classe, S.modoDoLogo(f)])));",
                FILMES_REAIS)
    esperado = {"claro": "logo", "escuro_mono": "logo_branco"}
    for slug, classe, modo in out:
        assert modo == esperado.get(classe, "texto"), slug


# ===========================================================================
# 2. PAÍSES
# ===========================================================================

@precisa_node
def test_paises_no_maximo_dois_com_nome_em_pt_br():
    out = _node("""console.log(JSON.stringify({
        max: T.MAX_PAISES,
        tres: T.nomesDosPaises(["US", "GB", "KR"]),
        um: T.nomesDosPaises(["BR"]),
        nada: T.nomesDosPaises([]),
        linha: T.linhaDaManchete({titulo: "O Ódio", diretor: "Mathieu Kassovitz",
                                  paises: ["FR", "DE", "BE"], ano: 1995}, false),
        comTitulo: T.linhaDaManchete({titulo: "O Ódio", diretor: "Mathieu Kassovitz",
                                      paises: ["FR"], ano: 1995}, true),
        recem: T.linhaDiretorAno({diretor: "Céline Sciamma", ano: 2019}),
        reais: D.map(f => T.nomesDosPaises(f.paises).length),
    }));""", FILMES_REAIS)
    assert out["max"] == 2
    assert out["tres"] == ["Estados Unidos", "Reino Unido"]
    assert out["um"] == ["Brasil"] and out["nada"] == []
    assert out["linha"] == "Mathieu Kassovitz · França, Alemanha · 1995"
    assert out["comTitulo"] == "O Ódio · Mathieu Kassovitz · França · 1995"
    assert out["recem"] == "Céline Sciamma · 2019"
    assert all(1 <= n <= 2 for n in out["reais"])


# ===========================================================================
# 3. COLEÇÃO DO DIA
# ===========================================================================

_DIAS = """const dia = i => new Date(Date.UTC(2026, 9, 21) + i * 86400000).toISOString().slice(0, 10);"""


@precisa_node
def test_colecao_do_dia_deterministica_e_independe_da_ordem_do_indice():
    out = _node(_DIAS + """
        const r = [];
        for (let i = 0; i < 60; i++) {
            const a = S.colecaoDoDia(D, dia(i)), b = S.colecaoDoDia(D, dia(i));
            const c = S.colecaoDoDia(JSON.parse(JSON.stringify(D)).reverse(), dia(i));
            r.push([a, b, c].map(x => x.colecao.chave + ":" + x.filmes.map(f => f.slug).join(",")));
        }
        console.log(JSON.stringify(r));""", FILMES_REAIS)
    for a, b, c in out:
        assert a == b == c


@precisa_node
def test_colecao_do_dia_respeita_o_piso_de_tres_e_mostra_ate_quatro():
    out = _node(_DIAS + """
        const r = [];
        for (let i = 0; i < 120; i++) {
            const c = S.colecaoDoDia(D, dia(i));
            r.push({total: c.total, n: c.filmes.length,
                    membros: c.colecao.filmes.map(f => f.slug),
                    mostrados: c.filmes.map(f => f.slug)});
        }
        console.log(JSON.stringify({r, piso: S.PISO_PRATELEIRA, lim: S.LIMITE_COLECAO}));""",
                FILMES_REAIS)
    assert out["piso"] == 3 and out["lim"] == 4
    for c in out["r"]:
        assert c["total"] >= 3
        assert c["n"] == min(4, c["total"])
        assert set(c["mostrados"]) <= set(c["membros"])
        # os mostrados seguem a ordem alfabética da coleção
        assert c["mostrados"] == [s for s in c["membros"] if s in c["mostrados"]]


@precisa_node
def test_coleções_abaixo_do_piso_nunca_sao_a_do_dia():
    def div(eixo, slug):
        return _filme(slug, slug.upper(), contraste="tematico",
                      eixos_acima=[{"eixo": eixo, "lift_pp": 25}])
    filmes = ([div("ritmo", f"r{i}") for i in range(3)]
              + [div("atuacao", f"a{i}") for i in range(2)]          # abaixo do piso
              + [_filme(f"v{i}", f"V{i}", assunto_comum="som_trilha") for i in range(3)])
    out = _node(_DIAS + """
        const r = new Set();
        for (let i = 0; i < 30; i++) r.add(S.colecaoDoDia(D, dia(i)).colecao.chave);
        console.log(JSON.stringify([...r].sort()));""", filmes)
    assert out == ["ritmo", "valorativo:som_trilha"]


@precisa_node
def test_colecao_do_dia_evita_a_da_manchete_quando_ha_alternativa():
    out = _node(_DIAS + """
        const r = [];
        for (let i = 0; i < 730; i++) {
            const m = S.escolhaDoDia(D, dia(i)).filme.slug;
            const c = S.colecaoDoDia(D, dia(i));
            const alternativa = S.ordemDasColecoes(D).some(x => !x.filmes.some(f => f.slug === m));
            r.push({contem: c.colecao.filmes.some(f => f.slug === m), alternativa,
                    chave: c.colecao.chave, evitou: c.evitou});
        }
        console.log(JSON.stringify(r));""", FILMES_REAIS)
    assert all(not d["contem"] for d in out if d["alternativa"])
    assert any(d["evitou"] for d in out)             # a regra é exercitada de fato
    # o salto de meio ciclo: a mesma coleção nunca em dois dias seguidos
    assert all(a["chave"] != b["chave"] for a, b in zip(out, out[1:]))


@precisa_node
def test_colecao_do_dia_sem_alternativa_fica_com_a_da_vez():
    # duas coleções, e a manchete está nas duas
    filmes = ([_filme(f"r{i}", f"R{i}", contraste="tematico",
                      eixos_acima=[{"eixo": "ritmo", "lift_pp": 25}]) for i in range(3)]
              + [_filme(f"v{i}", f"V{i}", assunto_comum="atuacao") for i in range(2)]
              + [_filme("x", "X", contraste="valorativo", assunto_comum="atuacao",
                        eixos_acima=[{"eixo": "ritmo", "lift_pp": 25}])])
    out = _node("""console.log(JSON.stringify(["2026-01-01", "2026-01-02"].map(d => {
        const c = S.colecaoDoDia(D, d, "x"); return [c.colecao.chave, c.evitou]; })));""", filmes)
    assert out == [["ritmo", False], ["valorativo:atuacao", False]]


# ===========================================================================
# 4. RECÉM-CHEGADOS
# ===========================================================================

@precisa_node
def test_recem_chegados_sao_tres_da_leva_e_evitam_a_pagina():
    out = _node(_DIAS + """
        const leva = S.recemChegados(D).filmes.map(f => f.slug);
        const r = [];
        for (let i = 0; i < 60; i++) {
            const m = S.escolhaDoDia(D, dia(i)).filme.slug;
            const c = S.colecaoDoDia(D, dia(i), m).filmes.map(f => f.slug);
            const pagina = [m].concat(c);
            r.push({pagina, recem: S.recemDoDia(D, dia(i), pagina).filmes.map(f => f.slug)});
        }
        console.log(JSON.stringify({leva, r, lim: S.LIMITE_RECEM}));""", FILMES_REAIS)
    assert out["lim"] == 3
    for d in out["r"]:
        assert len(d["recem"]) == 3 == len(set(d["recem"]))
        assert set(d["recem"]) <= set(out["leva"])
        assert not set(d["recem"]) & set(d["pagina"])     # a leva real tem 44


@precisa_node
def test_recem_chegados_leva_pequena_nao_tira_nada():
    filmes = [_filme(f"n{i}", f"N{i}", entrada="2026-09-30") for i in range(3)]
    out = _node("""console.log(JSON.stringify(
        S.recemDoDia(D, "2026-01-05", ["n0"]).filmes.map(f => f.slug)));""", filmes)
    assert out == ["n0", "n1", "n2"]


# ===========================================================================
# 5. NENHUM PÔSTER NA HOME
# ===========================================================================

def test_indice_da_home_sem_campo_de_poster():
    texto = (JS / "indice.js").read_text(encoding="utf-8")
    assert "poster" not in texto
    for f in FILMES_REAIS:
        assert set(f["imagens"]) <= {"backdrop_path", "backdrop_largura", "backdrop_altura"}
        assert f["imagens"].get("backdrop_path"), f["slug"]


def test_a_apresentacao_da_home_nao_monta_poster():
    codigo = re.sub(r"/\*.*?\*/|//[^\n]*", "", INICIO, flags=re.S)
    assert "poster_" not in codigo
    assert "P.montar" not in codigo            # montar, montarBackdrop, montarHeroFaixa
    # toda imagem da home sai de P.url com um caminho de backdrop, still ou logo
    assert set(re.findall(r"P\.url\(([^,]+),", codigo)) == {"path", "f.logo.path"}
    # e `fontes(path)` só recebe quadros da `sequencia` (backdrop + stills)
    assert set(re.findall(r"fontes\(([^)]+)\)", codigo)) == {
        "path", "seq[0]", "seq[1 % seq.length]", "seq[(i + 1"}  # o regex corta no primeiro ")"
    html = (FRONT / "index.html").read_text(encoding="utf-8")
    assert "poster" not in re.sub(r"<!--.*?-->", "", html, flags=re.S).replace("js/poster.js", "")


@precisa_node
def test_sequencia_de_quadros_so_tem_backdrop_e_stills():
    """A mesma regra de `sequencia` (inicio.js): o backdrop publicado e a
    galeria sem o primeiro item — conferida contra os caminhos do índice."""
    for f in FILMES_REAIS:
        assert f["stills"], f["slug"]
        assert all(p.startswith("/") for p in f["stills"])
    assert "(f.stills || []).slice(hero ? 1 : 0)" in INICIO


# ===========================================================================
# 6. TEXTOS NOVOS, FORMA E LINKS
# ===========================================================================

@precisa_node
def test_textos_novos_sem_vocabulario_proibido_nem_nota():
    out = _node("""console.log(JSON.stringify({
        fixos: Object.values(T.DESCRICAO_EIXO).concat(Object.values(T.FRASE_TIPO)),
        rotulos: [T.NOME_SITE, T.LINK_FILMES, T.LINK_METODO, T.ROTULO_COLECAO,
                  T.ROTULO_COLECAO_TODOS, T.ROTULO_RECEM_TODOS, T.verOsFilmes(99)],
        eixos: Object.keys(T.DESCRICAO_EIXO), ordem: S.ORDEM_EIXOS,
        tipos: Object.keys(T.FRASE_TIPO)}));""")
    assert set(out["eixos"]) == set(out["ordem"])
    assert set(out["tipos"]) == {"divisao", "valorativa"}
    for t in out["fixos"]:
        assert _proibidos_em(t) == [], (t, _proibidos_em(t))
        assert not re.search(r"\d|%", t), t
        assert _violacoes_de_nota(t) == [], t
        for g in ("HATERS", "MIXED", "FANS"):     # nenhum grupo nomeado sozinho
            assert g not in t
    for t in out["rotulos"]:
        assert _violacoes_de_nota(t) == [], t


def test_veu_e_constante_unica_com_teto_de_0_35():
    css = _bloco_editorial_css()
    defs = re.findall(r"--ed-veu:\s*([\d.]+)", css)
    assert len(defs) == 1 and float(defs[0]) <= 0.35
    assert css.count("var(--ed-veu)") == 1


def test_imagens_da_home_com_cantos_retos_e_sem_sombra():
    css = _bloco_editorial_css()
    regras = re.findall(r"(\.ed-[^{]*)\{([^}]*)\}", css)
    for seletor, corpo in regras:
        assert "box-shadow" not in corpo, seletor
        assert "text-shadow" not in corpo, seletor
        if "quadro" in seletor or "logo" in seletor:
            for valor in re.findall(r"border-radius:\s*([^;]+);", corpo):
                assert valor.strip() == "0", (seletor, valor)


def test_hover_troca_a_cada_1200ms_e_respeita_movimento_reduzido():
    assert "var INTERVALO_HOVER = 1200;" in INICIO
    assert '"(prefers-reduced-motion: reduce)"' in INICIO
    assert "if (reduzMovimento || !temHover || seq.length < 2) return;" in INICIO


def test_ver_todos_da_colecao_abre_filmes_filtrado():
    assert '"?colecao=" + encodeURIComponent(cd.colecao.chave)' in INICIO
    cat = (JS / "catalogo.js").read_text(encoding="utf-8")
    assert 'get("colecao")' in cat and "SEL.prateleirasBase(INDICE.filmes)" in cat
    filmes = (FRONT / "filmes" / "index.html").read_text(encoding="utf-8")
    for js in ("indice.js", "busca.js", "selecao.js", "textos_home.js"):
        assert filmes.index(js) < filmes.index("catalogo.js"), js


def test_ordem_das_secoes_da_home():
    html = re.sub(r"<!--.*?-->", "", (FRONT / "index.html").read_text(encoding="utf-8"), flags=re.S)
    ordem = [html.index(i) for i in ('id="busca"', 'id="edLinkFilmes"', 'id="edLinkMetodo"',
                                    'id="manchete"', 'id="colecaoDoDia"',
                                    'id="recemChegados"', 'id="verTodos"')]
    assert ordem == sorted(ordem)
    assert 'id="prateleiras"' not in html
