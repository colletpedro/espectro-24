"""[rodada Explorar] O bloco Explorar da home e /filmes como página Explorar.

A lógica é EXECUTADA sob node (explorar.js é puro, como selecao.js). Trava:
  1. as contagens do Explorar batem com o catálogo, respeitam os pisos e a
     ordem pedida, e contam só os elegíveis (obsession-2025 fora);
  2. filtros combinados em AND e a URL em ida e volta;
  3. a ordem padrão é determinística e não lê a distribuição dos grupos;
  4. a paginação de 24;
  5. o Índice A–Z respeita os filtros e ignora artigos como a busca;
  6. nenhum pôster em /filmes; links antigos (?desde=, ?colecao=) valem.
"""
from __future__ import annotations

import json
import re
import subprocess
import textwrap
from collections import Counter

import pytest

from test_home_nova import FILMES_REAIS, FRONT, JS, _filme, precisa_node


def _x(corpo: str, dados=None):
    script = textwrap.dedent(f"""
        const B = require({json.dumps(str(JS / "busca.js"))});
        const S = require({json.dumps(str(JS / "selecao.js"))});
        const T = require({json.dumps(str(JS / "textos_home.js"))});
        const X = require({json.dumps(str(JS / "explorar.js"))});
        const D = JSON.parse(require("fs").readFileSync(0, "utf8"));
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], input=json.dumps(dados),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


ELEGIVEIS = [f for f in FILMES_REAIS if f["slug"] != "obsession-2025"]


@pytest.fixture(scope="module")
def grupos_home():
    return _x("console.log(JSON.stringify(X.gruposDoExplorar(D, {elegiveis: true, piso: X.PISO_HOME})));",
              FILMES_REAIS)


# ===========================================================================
# 1. CONTAGENS DO EXPLORAR
# ===========================================================================

@precisa_node
def test_assunto_e_a_ordem_fixa_das_colecoes(grupos_home):
    ordem = _x("console.log(JSON.stringify(S.ordemDasColecoes(D).map(c => [c.chave, c.filmes.length])));",
               FILMES_REAIS)
    assert [[i["chave"], i["n"]] for i in grupos_home["assunto"]] == ordem
    assert all(i["n"] >= 3 for i in grupos_home["assunto"])


@precisa_node
def test_decadas_cronologicas_com_contagem_dos_elegiveis(grupos_home):
    esperado = Counter(f["ano"] // 10 * 10 for f in ELEGIVEIS)
    assert [(i["chave"], i["n"]) for i in grupos_home["decada"]] == sorted(esperado.items())
    nomes = {i["chave"]: i["nome"] for i in grupos_home["decada"]}
    assert nomes[1960] == "Anos 60" and nomes[2020] == "Anos 2020" and nomes[2000] == "Anos 2000"


@precisa_node
def test_generos_com_piso_e_ordem_por_contagem(grupos_home):
    contagem = Counter(g for f in ELEGIVEIS for g in set(f["generos"]))
    itens = grupos_home["genero"]
    assert {i["nome"]: i["n"] for i in itens} == {g: n for g, n in contagem.items() if n >= 3}
    ns = [i["n"] for i in itens]
    assert ns == sorted(ns, reverse=True)
    # nomes em pt-BR, como vêm da ficha (nenhum em inglês no catálogo)
    assert not {"Science Fiction", "Horror", "Comedy", "Mystery", "War", "History"} & {i["nome"] for i in itens}
    assert next(i for i in itens if i["nome"] == "Ficção científica")["chave"] == "ficcao-cientifica"


@precisa_node
def test_paises_contam_todos_os_paises_de_cada_filme(grupos_home):
    contagem = Counter(p for f in ELEGIVEIS for p in set(f["paises"]))
    itens = grupos_home["pais"]
    assert {i["chave"]: i["n"] for i in itens} == {p: n for p, n in contagem.items() if n >= 3}
    assert [(i["n"]) for i in itens] == sorted((i["n"] for i in itens), reverse=True)
    nomes = {i["chave"]: i["nome"] for i in itens}
    assert nomes["US"] == "Estados Unidos" and nomes["JP"] == "Japão"


@precisa_node
def test_desempate_alfabetico_em_genero_e_pais():
    filmes = ([_filme(f"z{i}", f"Z{i}", generos=["Zeta", "Alfa"], paises=["DE", "AT"]) for i in range(3)])
    out = _x("console.log(JSON.stringify(X.gruposDoExplorar(D, {piso: 3})));", filmes)
    assert [i["nome"] for i in out["genero"]] == ["Alfa", "Zeta"]
    assert [i["chave"] for i in out["pais"]] == ["DE", "AT"]   # Alemanha < Áustria


@precisa_node
def test_excluido_da_vitrine_fora_das_contagens_da_home():
    out = _x("""const com = X.gruposDoExplorar(D, {elegiveis: true});
        const sem = X.gruposDoExplorar(D.filter(f => f.slug !== "obsession-2025"), {elegiveis: true});
        const todos = X.gruposDoExplorar(D, {});
        console.log(JSON.stringify({com, sem, todos}));""", FILMES_REAIS)
    assert out["com"] == out["sem"]
    # sem a lista de exclusão, obsession-2025 (Terror, Thriller, 2025, US+GB) contaria
    t = {i["chave"]: i["n"] for i in out["todos"]["genero"]}
    h = {i["chave"]: i["n"] for i in out["com"]["genero"]}
    assert t["terror"] == h["terror"] + 1


def test_home_monta_o_explorar_com_os_elegiveis():
    fonte = (JS / "inicio.js").read_text(encoding="utf-8")
    assert "X.gruposDoExplorar(FILMES, { elegiveis: true, piso: X.PISO_HOME })" in fonte
    assert 'var PARAM = { assunto: "colecao", decada: "decada", genero: "genero", pais: "pais" };' in fonte
    assert 'HREF_CATALOGO + "?vista=indice"' in fonte
    assert 'el("details", "ed-explorar__grupo")' in fonte and 'el("summary"' in fonte


# ===========================================================================
# 2. FILTROS EM AND E URL
# ===========================================================================

@precisa_node
def test_filtros_combinados_sao_and():
    out = _x("""
        const um = X.filtrar(D, {genero: "drama"}).map(f => f.slug);
        const dois = X.filtrar(D, {genero: "drama", pais: "JP"}).map(f => f.slug);
        const tres = X.filtrar(D, {genero: "drama", pais: "JP", decada: 2020}).map(f => f.slug);
        const col = X.filtrar(D, {colecao: "valorativo:critica_social", decada: 1990}).map(f => f.slug);
        const desconhecido = X.filtrar(D, {genero: "nao-existe"}).length;
        console.log(JSON.stringify({um, dois, tres, col, desconhecido}));""", FILMES_REAIS)
    por = {f["slug"]: f for f in FILMES_REAIS}
    assert set(out["um"]) == {f["slug"] for f in FILMES_REAIS if "Drama" in f["generos"]}
    assert set(out["dois"]) == {s for s in out["um"] if "JP" in por[s]["paises"]}
    assert set(out["tres"]) == {s for s in out["dois"] if por[s]["ano"] // 10 * 10 == 2020}
    assert out["dois"] and out["tres"] and set(out["tres"]) < set(out["dois"]) < set(out["um"])
    assert all(por[s]["ano"] // 10 == 199 for s in out["col"]) and out["col"]
    assert out["desconhecido"] == 0


@precisa_node
@pytest.mark.parametrize("busca", [
    "", "?genero=drama", "?decada=1960&pais=JP", "?colecao=valorativo%3Acritica_social",
    "?colecao=ritmo&decada=2010&genero=ficcao-cientifica&pais=US&desde=2026-09-17&vista=indice",
    "?desde=2026-09-17",
])
def test_url_ida_e_volta(busca):
    out = _x("""const a = X.lerFiltros(D);
        const url = X.urlDosFiltros(a.filtros, a.vista);
        console.log(JSON.stringify({a, url, b: X.lerFiltros(url)}));""", busca)
    assert out["a"] == out["b"]
    assert out["url"] == busca


@precisa_node
def test_url_ignora_valores_malformados():
    out = _x("console.log(JSON.stringify(X.lerFiltros(D)));",
             "?decada=60s&pais=EUA&desde=ontem&vista=mosaico&pais=jp")
    assert out == {"filtros": {}, "vista": "grade"}
    out = _x("console.log(JSON.stringify(X.lerFiltros(D)));", "?pais=jp")
    assert out["filtros"] == {"pais": "JP"}


# ===========================================================================
# 3. ORDEM PADRÃO
# ===========================================================================

@precisa_node
def test_ordem_padrao_entrada_desc_e_alfabetica_no_empate():
    out = _x("""console.log(JSON.stringify([X.ordenarPadrao(D).map(f => f.slug),
        X.ordenarPadrao(JSON.parse(JSON.stringify(D)).reverse()).map(f => f.slug)]));""",
             FILMES_REAIS)
    a, b = out
    assert a == b                                      # determinística
    por = {f["slug"]: f for f in FILMES_REAIS}
    entradas = [por[s]["entrada"] for s in a]
    assert entradas == sorted(entradas, reverse=True)
    # no empate de data, alfabética pelo título normalizado (artigos fora)
    norm = _x("console.log(JSON.stringify(D.map(s => B.normalizar(s))))",
              [por[s]["titulo"] for s in a])
    for i in range(len(a) - 1):
        if entradas[i] == entradas[i + 1]:
            assert norm[i] <= norm[i + 1], (a[i], a[i + 1])


@precisa_node
def test_ordem_e_filtros_nao_leem_a_distribuicao():
    trocado = [dict(f, distribuicao={"negativas": 97, "medianas": 2, "positivas": 1} if i % 2 else None)
               for i, f in enumerate(FILMES_REAIS)]
    corpo = """const r = L => [X.ordenarPadrao(L).map(f => f.slug),
        X.filtrar(L, {genero: "drama", pais: "US"}).map(f => f.slug),
        X.gruposDoExplorar(L, {elegiveis: true}), X.indiceAZ(L).map(g => g.letra + g.filmes.length)];
        console.log(JSON.stringify([r(D.a), r(D.b)]));"""
    a, b = _x(corpo, {"a": FILMES_REAIS, "b": trocado})
    assert a == b
    fonte = (JS / "explorar.js").read_text(encoding="utf-8")
    assert "distribuicao" not in re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    assert "distribuicao" not in (JS / "catalogo.js").read_text(encoding="utf-8")


# ===========================================================================
# 4. PAGINAÇÃO
# ===========================================================================

def test_paginacao_de_24_com_mostrar_mais_e_contador():
    cat = (JS / "catalogo.js").read_text(encoding="utf-8")
    exp = (JS / "explorar.js").read_text(encoding="utf-8")
    assert "var PAGINA = 24;" in exp
    assert "recorte.slice(0, mostrados)" in cat and "mostrados += X.PAGINA" in cat
    assert "T.contadorDaPagina(n, recorte.length)" in cat
    # a página não vai para a URL
    assert "pagina" not in exp.split("function urlDosFiltros")[1].split("function filtrar")[0]


@precisa_node
def test_contador_da_pagina():
    out = _x("console.log(JSON.stringify([T.contadorDaPagina(24, 99), T.MOSTRAR_MAIS]))")
    assert out == ["24 de 99", "Mostrar mais"]


# ===========================================================================
# 5. ÍNDICE A–Z
# ===========================================================================

@precisa_node
def test_indice_az_ignora_artigos_e_respeita_filtros():
    out = _x("""const tudo = X.indiceAZ(D);
        const filtrado = X.indiceAZ(X.filtrar(D, {decada: 1990}));
        console.log(JSON.stringify({
            tudo: tudo.map(g => [g.letra, g.filmes.map(f => f.slug)]),
            filtrado: filtrado.flatMap(g => g.filmes.map(f => f.slug)),
            letra: Object.fromEntries(D.map(f => [f.slug, X.letraDe(f)]))}));""", FILMES_REAIS)
    letra = out["letra"]
    assert letra["goodfellas"] == "B"            # "Os Bons Companheiros"
    assert letra["the-godfather"] == "P"         # "O Poderoso Chefão"
    assert letra["12-angry-men"] == "0–9"
    assert letra["la-haine"] == "O"              # "O Ódio": artigo fora, acento fora
    letras = [l for l, _ in out["tudo"]]
    assert letras[0] == "0–9" and letras[1:] == sorted(letras[1:])
    assert sum(len(s) for _, s in out["tudo"]) == len(FILMES_REAIS)
    assert set(out["filtrado"]) == {f["slug"] for f in FILMES_REAIS if f["ano"] // 10 == 199}
    for l, slugs in out["tudo"]:
        assert all(letra[s] == l for s in slugs)


def test_indice_sem_imagem_com_titulo_ano_e_diretor():
    cat = (JS / "catalogo.js").read_text(encoding="utf-8")
    bloco = cat.split("function renderIndice()")[1].split("function render()")[0]
    assert "img" not in bloco and "quadro" not in bloco
    assert "f.titulo" in bloco and "f.ano" in bloco and "f.diretor" in bloco


# ===========================================================================
# 6. NENHUM PÔSTER EM /filmes; LINKS ANTIGOS
# ===========================================================================

def test_filmes_sem_poster_e_sem_data_js():
    html = re.sub(r"<!--.*?-->", "", (FRONT / "filmes" / "index.html").read_text(encoding="utf-8"),
                  flags=re.S)
    assert "data.js" not in html                  # lê só o índice
    assert "mosaic" not in html and "poster" not in html.replace("../js/poster.js", "")
    cat = re.sub(r"/\*.*?\*/|//[^\n]*", "", (JS / "catalogo.js").read_text(encoding="utf-8"), flags=re.S)
    assert "poster" not in cat and "P.montar" not in cat and "ESPECTRO_DATA" not in cat
    assert "C.cartao(" in cat                     # o cartão de still da home


@precisa_node
def test_links_antigos_continuam_validos():
    out = _x("""const r = {};
        for (const q of ["?desde=2026-09-17", "?colecao=valorativo%3Acritica_social",
                         "?colecao=ritmo&desde=2026-09-17"]) {
            const e = X.lerFiltros(q);
            r[q] = X.filtrar(D, e.filtros).map(f => f.slug);
        }
        r.leva = S.recemChegados(D).filmes.map(f => f.slug).concat(
            D.filter(f => f.slug === "obsession-2025" && f.entrada >= "2026-09-17").map(f => f.slug));
        r.colecao = S.prateleirasBase(D).filter(c => c.chave === "valorativo:critica_social")[0].filmes.map(f => f.slug);
        r.ritmo = S.prateleirasBase(D).filter(c => c.chave === "ritmo")[0].filmes.map(f => f.slug);
        console.log(JSON.stringify(r));""", FILMES_REAIS)
    assert set(out["?desde=2026-09-17"]) == set(out["leva"])
    assert set(out["?colecao=valorativo%3Acritica_social"]) == set(out["colecao"])
    assert set(out["?colecao=ritmo&desde=2026-09-17"]) == set(out["ritmo"]) & set(out["leva"])
    home = (JS / "inicio.js").read_text(encoding="utf-8")
    assert '"?desde=" + r.desde' in home
    assert '"?colecao=" + encodeURIComponent(cd.colecao.chave)' in home


def test_textos_do_explorar_sem_vocabulario_proibido():
    from test_home_nova import _proibidos_em, _violacoes_de_nota
    out = _x("""console.log(JSON.stringify([T.TITULO_EXPLORAR, T.LINK_INDICE, T.VISTA_GRADE,
        T.VISTA_INDICE, T.MOSTRAR_MAIS, T.FILTRO_VAZIO, T.LIMPAR_FILTROS, T.REMOVER_FILTRO]
        .concat(Object.values(T.ROTULO_GRUPO_EXPLORAR), Object.values(T.QUALQUER))))""")
    for t in out:
        assert _proibidos_em(t) == [], t
        assert _violacoes_de_nota(t) == [], t
