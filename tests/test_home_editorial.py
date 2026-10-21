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
     nota; forma (véu, hover, cantos, sombra) e o link de coleção em /filmes;
  7. [rodada editorial 2] o título repetido na linha (normalizado como na
     busca), o véu MEDIDO atrás do texto e a prova de fontes (`?fonte=`).
"""
from __future__ import annotations

import json
import re
import subprocess
import textwrap

import pytest

from test_home_nova import (FILMES_REAIS, FRONT, JS, RAIZ, _filme, _node,
                            _proibidos_em, _violacoes_de_nota, precisa_node)

CSS = (FRONT / "css" / "styles.css").read_text(encoding="utf-8")
INICIO = (JS / "inicio.js").read_text(encoding="utf-8")
# [rodada Explorar] o cartão (still, hover, metadado) saiu de inicio.js para
# cartoes.js, compartilhado com /filmes; os testes de forma leem os dois
CARTOES = (JS / "cartoes.js").read_text(encoding="utf-8")


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
                "logo": {"path": "/a.png", "idioma": idioma, "classe": classe,
                         "titulo": "Outro"}}
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
    """[rodada Explorar] Cobre também cartoes.js, cabecalho.js e catalogo.js
    (/filmes), que montam cartões e links da home e do catálogo."""
    fontes_js = INICIO + CARTOES + "".join(
        (JS / n).read_text(encoding="utf-8") for n in ("cabecalho.js", "catalogo.js", "explorar.js"))
    codigo = re.sub(r"/\*.*?\*/|//[^\n]*", "", fontes_js, flags=re.S)
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
    assert "(f.stills || []).slice(hero ? 1 : 0)" in CARTOES


# ===========================================================================
# 6. TEXTOS NOVOS, FORMA E LINKS
# ===========================================================================

@precisa_node
def test_textos_novos_sem_vocabulario_proibido_nem_nota():
    out = _node("""console.log(JSON.stringify({
        fixos: Object.values(T.DESCRICAO_EIXO).concat(Object.values(T.FRASE_TIPO)),
        rotulos: [T.NOME_SITE, T.LINK_FILMES, T.LINK_METODO, T.ROTULO_COLECAO,
                  T.ROTULO_COLECAO_TODOS, T.ROTULO_RECEM_TODOS,
                  // [rodada Explorar] o link "Ver os N filmes" saiu; entram os do Explorar
                  T.TITULO_EXPLORAR, T.LINK_INDICE, T.VISTA_GRADE, T.VISTA_INDICE,
                  T.MOSTRAR_MAIS, T.FILTRO_VAZIO, T.LIMPAR_FILTROS, T.REMOVER_FILTRO,
                  T.contadorDaPagina(24, 99), T.chipDesde("2026-09-17")]
                  .concat(Object.values(T.ROTULO_GRUPO_EXPLORAR), Object.values(T.QUALQUER)),
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


def test_veu_medido_atras_do_texto_garante_contraste_4_5():
    """[rodada editorial 2] Substitui "véu uniforme com teto de 0,35" (a
    regra de produto mudou: o véu fica SÓ atrás do bloco de texto, com a
    opacidade MEDIDA para contraste WCAG >= 4,5 da justificativa no pior
    still). A constante continua única; o valor dela é o da medição."""
    css = _bloco_editorial_css()
    defs = re.findall(r"--ed-veu:\s*([\d.]+)", css)
    assert len(defs) == 1
    assert css.count("var(--ed-veu)") == 1
    # o véu está na CAIXA do texto, e em nenhum outro lugar
    caixa = re.search(r"\.ed-manchete__caixa\s*\{([^}]*)\}", css).group(1)
    assert "background: rgba(0, 0, 0, var(--ed-veu));" in caixa
    assert "ed-manchete__veu" not in css + INICIO
    medida = json.loads((RAIZ / "dados" / "legibilidade_manchete.json").read_text(encoding="utf-8"))
    assert float(defs[0]) == medida["alfa"]
    assert medida["cor_texto"] == "#f2f0ea" and medida["contraste_minimo"] == 4.5
    contrastes = [c for r in medida["filmes"].values() for c in r["contraste_com_veu"].values()]
    assert min(contrastes) >= 4.5
    assert medida["pior_caso"]["contraste"] == round(min(contrastes), 3)
    # os 98 elegíveis da manchete, nas quatro larguras de desktop
    elegiveis = {f["slug"] for f in FILMES_REAIS} - {"obsession-2025"}
    assert set(medida["filmes"]) == elegiveis
    assert all(set(r["caixas"]) == {"700", "1024", "1440", "1920"}
               for r in medida["filmes"].values())


def test_medida_do_veu_e_a_menor_opacidade_que_passa():
    pytest.importorskip("numpy")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "medir_legibilidade_teste", RAIZ / "scripts" / "medir_legibilidade.py")
    ml = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ml)
    import numpy as np
    branco = np.ones((10, 3))
    # sobre branco puro: (0,87+0,05)/(L(1−a)+0,05) >= 4,5 pede a = 0,58
    a = ml.menor_alfa([branco])
    assert ml.contraste(ml.luminancia_do_fundo(branco, a)) >= 4.5
    assert ml.contraste(ml.luminancia_do_fundo(branco, a - 0.01)) < 4.5
    assert ml.menor_alfa([np.zeros((10, 3))]) == 0.0      # fundo preto: sem véu
    # a região é o recorte da caixa, em frações do still
    img = np.zeros((10, 20, 3)); img[5:, :10] = 1.0
    assert ml.regiao(img, [0, 0.5, 0.5, 1.0]).mean() == 1.0


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
    assert "var INTERVALO_HOVER = 1200;" in CARTOES
    assert '"(prefers-reduced-motion: reduce)"' in CARTOES
    assert "if (reduzMovimento || !temHover || seq.length < 2) return;" in CARTOES


def test_ver_todos_da_colecao_abre_filmes_filtrado():
    assert '"?colecao=" + encodeURIComponent(cd.colecao.chave)' in INICIO
    # [rodada Explorar] o filtro de coleção de /filmes mora em explorar.js
    # (era catalogo.js), com a MESMA regra da home: `S.prateleirasBase`
    exp = (JS / "explorar.js").read_text(encoding="utf-8")
    assert 'p.get("colecao")' in exp and "S.prateleirasBase(filmes)" in exp
    filmes = (FRONT / "filmes" / "index.html").read_text(encoding="utf-8")
    for js in ("indice.js", "busca.js", "selecao.js", "textos_home.js", "explorar.js",
               "cartoes.js"):
        assert filmes.index(js) < filmes.index("catalogo.js"), js


def test_ordem_das_secoes_da_home():
    html = re.sub(r"<!--.*?-->", "", (FRONT / "index.html").read_text(encoding="utf-8"), flags=re.S)
    ordem = [html.index(i) for i in ('id="busca"', 'id="edLinkFilmes"', 'id="edLinkMetodo"',
                                    'id="manchete"', 'id="colecaoDoDia"',
                                    'id="recemChegados"', 'id="explorar"')]
    assert ordem == sorted(ordem)
    assert 'id="prateleiras"' not in html


# ===========================================================================
# 7. [rodada editorial 2] TÍTULO REPETIDO E PROVA DE FONTES
# ===========================================================================

@precisa_node
def test_titulo_na_linha_compara_normalizado_como_na_busca():
    reais = {f["slug"]: f for f in FILMES_REAIS}
    casos = {
        # logo en que escreve o mesmo título: não repete
        "aftersun": reais["aftersun"],
        # o logo real de Interestelar é pt-BR e escreve "INTERESTELAR": não repete
        "interstellar": reais["interstellar"],
        # se o logo exibido fosse o en ("Interstellar"), o título repetiria
        "interstellar_en": dict(reais["interstellar"], titulo_difere_do_logo=True,
                                logo=dict(reais["interstellar"]["logo"], idioma="en",
                                          titulo="Interstellar")),
        # normalização da busca: caixa, acento, pontuação e artigo inicial
        "normalizado": {"titulo": "O Ódio!", "titulo_difere_do_logo": True,
                        "logo": {"path": "/a.png", "idioma": "en", "classe": "claro",
                                 "titulo": "odio"}},
        "anatomia": reais["anatomy-of-a-fall"],
    }
    out = _node("""const r = {};
        for (const [k, f] of Object.entries(D)) r[k] = [S.tituloNaLinha(f),
            T.linhaDaManchete(f, S.tituloNaLinha(f))];
        console.log(JSON.stringify(r));""", casos)
    assert reais["aftersun"]["logo"]["titulo"] == "Aftersun"
    assert out["aftersun"] == [False, "Charlotte Wells · Reino Unido, Estados Unidos · 2022"]
    assert reais["interstellar"]["logo"]["idioma"] == "pt-BR"
    assert out["interstellar"][0] is False
    assert out["interstellar_en"][0] is True
    assert out["interstellar_en"][1].startswith("Interestelar · ")
    assert out["normalizado"][0] is False
    assert out["anatomia"][0] is True
    assert out["anatomia"][1].startswith("Anatomia de uma Queda · ")


@precisa_node
def test_titulo_do_logo_publicado_em_todo_logo():
    out = _node("console.log(JSON.stringify(D.filter(f => f.logo).map(f => [f.slug, f.logo.idioma, f.logo.titulo, f.titulo])));",
                FILMES_REAIS)
    assert len(out) == 97
    for slug, idioma, titulo_logo, titulo in out:
        assert titulo_logo, slug
        if idioma == "pt-BR":
            assert titulo_logo == titulo, slug


@precisa_node
def test_linha_em_partes_tem_o_mesmo_texto():
    out = _node("""console.log(JSON.stringify(D.map(f => [
        T.partesDaManchete(f, true).map(p => p.texto).join(T.SEPARADOR) === T.linhaDaManchete(f, true),
        T.partesDiretorAno(f).map(p => p.texto).join(T.SEPARADOR) === T.linhaDiretorAno(f),
        T.partesDaManchete(f, false).map(p => p.tipo)])));""", FILMES_REAIS)
    for igual_m, igual_r, tipos in out:
        assert igual_m and igual_r
        assert tipos[0] == "diretor" and tipos[-1] == "ano"


FONTE_JS = (JS / "fonte.js").read_text(encoding="utf-8")


def _rodar_fonte(busca: str) -> dict:
    """Executa js/fonte.js num documento falso, com `?...` = `busca`."""
    script = textwrap.dedent("""
        const links = []; const attrs = {};
        global.location = {search: process.argv[1]};
        global.URLSearchParams = URLSearchParams;
        global.window = {};
        global.document = {
            documentElement: {setAttribute: (k, v) => { attrs[k] = v; }},
            createElement: () => ({}),
            head: {appendChild: l => links.push({rel: l.rel, href: l.href})},
        };
        require(process.argv[2]);
        console.log(JSON.stringify({attrs, links, api: window.ESPECTRO_FONTE}));
    """)
    r = subprocess.run(["node", "-e", script, busca, str(JS / "fonte.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@precisa_node
@pytest.mark.parametrize("busca,fonte,familia", [
    ("", "instrument", "Instrument+Sans"),          # [rodada da fonte] o padrão
    ("?fonte=atual", "atual", None),
    ("?fonte=inter-tight", "inter-tight", "Inter+Tight"),
    ("?fonte=instrument", "instrument", "Instrument+Sans"),
    ("?fonte=comic-sans", "instrument", "Instrument+Sans"),  # desconhecida: o padrão
    ("?dia=2026-10-21&fonte=instrument", "instrument", "Instrument+Sans"),
])
def test_fonte_marca_o_html_e_carrega_so_a_familia_pedida(busca, fonte, familia):
    out = _rodar_fonte(busca)
    assert out["attrs"] == {"data-fonte": fonte}
    folhas = [l["href"] for l in out["links"] if l["rel"] == "stylesheet"]
    if familia is None:
        assert out["links"] == []                    # `atual`: zero rede
    else:
        assert len(folhas) == 1 and "family=" + familia + ":" in folhas[0]
        assert folhas[0].startswith("https://fonts.googleapis.com/css2?")
        outra = "Instrument" if familia.startswith("Inter") else "Inter"
        assert outra not in folhas[0]


def test_padrao_da_fonte_e_uma_linha_e_a_familia_uma_variavel():
    assert len(re.findall(r'var FONTE_PADRAO = "[a-z-]+";', FONTE_JS)) == 1
    assert 'var FONTE_PADRAO = "instrument";' in FONTE_JS   # [rodada da fonte]
    filmes = (FRONT / "filmes" / "index.html").read_text(encoding="utf-8")
    assert filmes.index('src="../js/fonte.js"') < filmes.index("</head>")
    css = _bloco_editorial_css()
    # uma variável só define a família, por opção
    assert re.findall(r':root\[data-fonte="([a-z-]+)"\] \{ --ed-fonte: "([^"]+)"', css) == [
        ("inter-tight", "Inter Tight"), ("instrument", "Instrument Sans")]
    # os elementos da prova leem a variável, com a família de sempre como padrão
    for seletor, padrao in ((".ed-colecao__titulo", "--serif"),
                            (".ed-manchete__titulo-texto", "--serif"),
                            (".ed-cartao__titulo", "--serif"),
                            (".ed-manchete__linha", "--mono"),
                            (".ed-cartao__meta", "--mono"),
                            (".ed-main .section-label", "--mono")):
        corpo = re.search(re.escape(seletor) + r"\s*\{([^}]*)\}", css).group(1)
        assert f"font-family: var(--ed-fonte, var({padrao}))" in corpo, seletor
    html = (FRONT / "index.html").read_text(encoding="utf-8")
    assert html.index('src="js/fonte.js"') < html.index("</head>")


def test_tratamento_das_fontes_novas():
    css = _bloco_editorial_css()
    novo = ':root[data-fonte]:not([data-fonte="atual"])'
    titulos = re.search(re.escape(novo + " .ed-colecao__titulo") + r"[^{]*\{([^}]*)\}", css).group(1)
    assert "text-transform: uppercase" in titulos and "letter-spacing: normal" in titulos
    assert re.search(r"font-weight: (500|600)", titulos)
    rotulo = re.search(re.escape(novo + " .ed-main .section-label") + r"\s*\{([^}]*)\}", css).group(1)
    assert "text-transform: uppercase" in rotulo and "letter-spacing: normal" in rotulo
    assert re.search(r"font-weight: (500|600)", rotulo)
    meta = re.search(re.escape(novo + " .ed-meta") + r"\s*\{([^}]*)\}", css).group(1)
    assert "text-transform: uppercase" in meta and "font-weight: 400" in meta
    assert re.search(re.escape(novo + " .ed-meta__diretor") + r"\s*\{ font-weight: 700; \}", css)
