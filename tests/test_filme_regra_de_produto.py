"""[rodada página do filme] A REGRA DE PRODUTO da página do filme não mudou.

A rodada mudou a FORMA da página (topo, veredito, tipografia, galeria,
"na mesma coleção"); as decisões de produto ficam: a ordem dos grupos por
peso, a abertura e o fechamento do Mixed, o layout de 2 ou 3 colunas, 6
bullets por grupo, a ordem e a quantidade das condições, o peso do meio.

O `filme.js` REAL roda, filme a filme, contra um DOM mínimo
(`tests/_filme_harness.js`, o projeto não tem runner de JS com DOM), e o
resultado é comparado com o snapshot `snapshots/filme_regra_de_produto_antes.json`,
tirado do `filme.js` DE ANTES da rodada. Um filme cujo INPUT (share_real,
ordem_colunas, nº de temas e de condições) mudou desde o snapshot — um
republish — sai da comparação: o que se trava é a regra, não os dados.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "frontend" / "js"
FILME_JS = JS / "filme.js"
HARNESS = RAIZ / "tests" / "_filme_harness.js"
SNAPSHOT = RAIZ / "tests" / "snapshots" / "filme_regra_de_produto_antes.json"
DATA = RAIZ / "frontend" / "data"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="sem node")

# a regra de cada coluna de condição → grupo → faixa de notas
FAIXA = {"negativas": "0,5 a 2", "medianas": "2,5 a 3", "positivas": "3,5 a 5"}


def _rodar(env=None, *args):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run(["node", str(HARNESS), str(FILME_JS), *args],
                       capture_output=True, text=True, timeout=300, env=e)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def padrao():
    return _rodar()


@pytest.fixture(scope="module")
def estatico():
    return _rodar({"HARNESS_TOPO": "estatico"})


def _sem_comentarios(fonte):
    fonte = re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    return re.sub(r"//.*", "", fonte)


# --- 1. a regra de produto, antes e depois -------------------------------

CAMPOS_DA_REGRA = ("colunas", "layout", "meio", "bullets", "condicoes", "peso_meio")


def test_a_regra_de_produto_e_identica_antes_e_depois_nos_filmes(padrao):
    antes = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    comparados = 0
    for slug, a in antes.items():
        d = padrao.get(slug)
        assert d is not None, f"{slug} sumiu do data.js"
        assert "erro" not in d, f"{slug}: {d.get('erro', '')[:300]}"
        if a["entrada"] != d["entrada"]:
            continue                      # republish: o input mudou
        comparados += 1
        for campo in CAMPOS_DA_REGRA:
            assert a[campo] == d[campo], f"{slug}: `{campo}` mudou\n{a[campo]}\n{d[campo]}"
    # trava contra trap vazio: se quase tudo foi "republicado", o teste não vigia nada
    assert comparados >= 90, comparados


def test_o_snapshot_cobre_o_catalogo_inteiro():
    antes = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert len(antes) >= 99
    assert any(v["layout"] == "3" for v in antes.values())          # meio dominante
    assert any(v["meio"] for v in antes.values())                   # meio recolhido
    assert any(not v["condicoes"] for v in antes.values())          # sem condições


# --- 2. nada de ★, nada de pesquisa ---------------------------------------

def test_nao_ha_estrela_na_pagina_do_filme(padrao):
    codigo = _sem_comentarios(FILME_JS.read_text(encoding="utf-8"))
    assert "★" not in codigo
    assert "★" not in (RAIZ / "frontend" / "filme.html").read_text(encoding="utf-8")
    for slug, d in padrao.items():
        assert "★" not in d["texto_da_pagina"], slug
        assert all(t.startswith("notas ") for t in d["faixas_de_notas"]), slug


def test_a_pesquisa_ab_saiu_do_html_e_do_filme_js():
    html = (RAIZ / "frontend" / "filme.html").read_text(encoding="utf-8")
    assert "survey" not in html.lower()
    assert "mountSurvey" not in FILME_JS.read_text(encoding="utf-8")
    assert (JS / "survey.js").exists()      # o arquivo pode ficar, sem uso


def test_a_nota_das_aspas_removidas_nao_e_exibida(padrao):
    assert "aspas de citação removidas" not in _sem_comentarios(
        FILME_JS.read_text(encoding="utf-8"))
    assert not any("aspas de citação" in d["texto_da_pagina"] for d in padrao.values())


# --- 3. ?topo=estatico: a mesma página, só o topo muda ----------------------

def test_topo_estatico_e_padrao_so_diferem_no_topo(padrao, estatico):
    assert set(padrao) == set(estatico)
    for slug, p in padrao.items():
        e = estatico[slug]
        if p["topo"] == "solido":
            # sem still nenhum (`teste-degradado`): as duas variantes caem no
            # topo sólido, e a página é a mesma
            assert e["topo"] == "solido", slug
        else:
            assert p["topo"] == "faixa" and e["topo"] == "manchete", slug
        p2 = {k: v for k, v in p.items() if k != "topo"}
        e2 = {k: v for k, v in e.items() if k != "topo"}
        assert p2 == e2, f"{slug}: o resto da página mudou com ?topo=estatico"


# --- 4. o logo e o título na linha: reutilizados, não duplicados -------------

def test_a_regra_do_logo_e_tituloNaLinha_moram_so_no_componente_compartilhado():
    cartoes = _sem_comentarios((JS / "cartoes.js").read_text(encoding="utf-8"))
    filme = _sem_comentarios(FILME_JS.read_text(encoding="utf-8"))
    inicio = _sem_comentarios((JS / "inicio.js").read_text(encoding="utf-8"))
    assert cartoes.count("S.modoDoLogo(") == 1 and cartoes.count("S.tituloNaLinha(") == 1
    for fonte in (filme, inicio):
        for duplicata in ("modoDoLogo", "tituloNaLinha", "is-branco", "logo_branco"):
            assert duplicata not in fonte, duplicata
    # e a página do filme usa o mesmo componente da manchete da home
    assert "C.montarManchete(" in filme and "C.montarManchete(" in inicio


# --- 5. as condições: o grupo de cada coluna vem da ORIGEM nos dados --------

def test_o_rotulo_da_coluna_de_condicao_vem_do_bucket_de_origem(padrao):
    vistos = 0
    for slug, d in padrao.items():
        dados = json.loads((DATA / f"{slug}.json").read_text(encoding="utf-8"))
        c = dados.get("condicoes")
        if not c:
            assert d["rotulos"] == [], slug
            continue
        # as colunas saem na ordem de `ordem_colunas`
        ordem = [l for l in c["ordem_colunas"] if c.get(l)]
        assert [r["lado"] for r in d["rotulos"]] == ["pos" if l == "vale_a_pena" else "neg" for l in ordem], slug
        for lado, r in zip(ordem, d["rotulos"]):
            origens = {x["bucket_origem"] for x in c[lado]}
            assert len(origens) == 1, (slug, lado, origens)
            grupo = origens.pop()
            assert r["grupo"] == grupo, slug
            assert r["texto"].startswith(c["peso"][lado]["peso_texto"] + " · quem deu de " + FAIXA[grupo]), (slug, r["texto"])
            vistos += 1
    assert vistos >= 190


def test_o_rotulo_segue_a_origem_e_nao_o_lado_nem_a_ordem():
    """Caso sintético: as condições de `vale_a_pena` passam a ter origem no
    MEIO e a `ordem_colunas` se inverte. O rótulo acompanha a origem."""
    patch = {"slug": "arrival-2016", "lado": "vale_a_pena", "bucket": "medianas",
             "ordem": ["talvez_evite", "vale_a_pena"]}
    d = _rodar({"HARNESS_PATCH": json.dumps(patch)}, "arrival-2016")["arrival-2016"]
    assert [r["lado"] for r in d["rotulos"]] == ["neg", "pos"]
    assert d["rotulos"][0]["grupo"] == "negativas"
    assert d["rotulos"][0]["texto"].endswith("quem deu de 0,5 a 2")
    assert d["rotulos"][1]["grupo"] == "medianas"
    assert d["rotulos"][1]["texto"].endswith("quem deu de 2,5 a 3")


# --- 6. veredito: a linha fina --------------------------------------------

def test_sem_veredito_a_linha_e_a_justificativa_da_home_e_woman_of_fire_mantem_o_aviso(padrao):
    sem = 0
    for slug, d in padrao.items():
        v = d["veredito"]
        dados = json.loads((DATA / f"{slug}.json").read_text(encoding="utf-8"))
        if v and v["classe"].startswith("verdict-absent"):
            # estado sem contraste: o aviso atual, no mesmo lugar
            assert v["texto"].startswith("A amostra analisada deste filme é pequena demais"), slug
            assert slug in ("woman-of-fire", "teste-degradado"), slug
        elif dados.get("veredito"):
            assert v["origem"] == "veredito"
            assert v["texto"] == dados["veredito"]["texto"], slug
        elif v:
            assert v["origem"] == "justificativa", slug
            assert "HATERS, MIXED e FANS" in v["texto"], slug
            assert "faz aniversário" not in v["texto"]      # sem data: só conteúdo
            sem += 1
    assert sem >= 10


# --- 7. na mesma coleção -------------------------------------------------------

@pytest.fixture(scope="module")
def colecoes():
    return _rodar({"HARNESS_COLECOES": "1"})


def test_na_mesma_colecao_regra_determinismo_exclusao_e_fallback(padrao, colecoes):
    ordem = colecoes["ordem"]
    excluidos = set(colecoes["excluidos"])
    recem = set(colecoes["recem"])
    de_colecao = fallback = 0
    for slug, d in padrao.items():
        c = d["colecao"]
        assert c is not None, slug
        assert slug not in c["slugs"], f"{slug}: o próprio filme apareceu"
        assert not (set(c["slugs"]) & excluidos), slug
        assert len(set(c["slugs"])) == len(c["slugs"]) == 3, slug
        esperada = next((x for x in ordem
                         if len(x["slugs"]) >= 4 and slug in x["slugs"]), None)
        if esperada:
            de_colecao += 1
            assert c["origem"] == "colecao" and c["chave"] == esperada["chave"], slug
            assert set(c["slugs"]) <= set(esperada["slugs"]), slug
            assert c["href"] == "filmes/?colecao=" + esperada["chave"].replace(":", "%3A"), slug
        else:
            fallback += 1
            assert c["origem"] == "recem" and set(c["slugs"]) <= recem, slug
            assert c["href"].startswith("filmes/?desde="), slug
    assert de_colecao > 50 and fallback >= 1


def test_na_mesma_colecao_e_deterministica(padrao):
    outra = _rodar()
    assert {k: v["colecao"] for k, v in padrao.items()} == {k: v["colecao"] for k, v in outra.items()}


def test_o_titulo_da_secao_e_o_titulo_da_colecao(padrao):
    import re as _re
    texto = (JS / "textos_home.js").read_text(encoding="utf-8")
    for slug, d in padrao.items():
        c = d["colecao"]
        if c["origem"] == "colecao":
            assert f'"{c["chave"]}": "{c["titulo"]}"' in texto or f'{c["chave"]}: "{c["titulo"]}"' in texto, slug


# --- 8. a galeria e a linha de metadado -------------------------------------

def test_a_galeria_tem_ate_4_stills_em_todas_as_larguras(padrao):
    assert max(d["galeria"] for d in padrao.values()) == 4
    assert padrao["woman-of-fire"]["galeria"] == 3       # só tem 3 stills
    assert padrao["teste-degradado"]["galeria"] == 0     # sem imagem: sem seção
    assert "fp-galeria" not in padrao["teste-degradado"]["secoes"]


def test_a_ordem_das_secoes_da_pagina(padrao):
    d = padrao["arrival-2016"]
    assert d["secoes"] == ["verdict", "proportion", "grupos", "decide",
                           "disclosure", "fp-galeria", "fp-colecao"]


def test_a_linha_de_metadado_do_topo_diretor_paises_ano_generos_duracao():
    r = subprocess.run(["node", "-e", """
        const T = require(%s);
        const f = {titulo: 'A Chegada', diretor: 'Denis Villeneuve', paises: ['US', 'CA', 'FR'],
                   ano: 2016, generos: ['Drama', 'Ficção científica', 'Mistério']};
        const sem = T.partesDaFicha(f, 116, false).map(p => p.tipo + '=' + p.texto);
        const com = T.partesDaFicha(f, 116, true).map(p => p.tipo);
        const nada = T.partesDaFicha({ano: 2000}, null, false).map(p => p.tipo);
        console.log(JSON.stringify({sem, com, nada}));
    """ % json.dumps(str(JS / "textos_home.js"))], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert [x.split("=")[0] for x in o["sem"]] == ["diretor", "paises", "ano", "generos", "duracao"]
    assert o["sem"][2] == "ano=2016" and o["sem"][4] == "duracao=116 min"
    assert o["sem"][3] == "generos=Drama, Ficção científica"          # até 2
    assert o["com"][0] == "titulo"
    assert o["nada"] == ["ano"]
