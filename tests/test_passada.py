"""[v1.9.6, §2.3] Passada seletiva sob `by/added-earliest`.

Três garantias, e as três são sobre NÃO estragar o que já existe: filme acima
do limiar não recebe passada; a passada SOMA ao bruto sem perder review; e o
`meta.json` da coleta base sobrevive intacto (é dele que a seleção lê a
fronteira raso/profundo).
"""
from __future__ import annotations

import json

import pytest

from conftest import FakeFetcher
from test_coletor import _pagina

from espectro24 import passada as mod
from espectro24.bruto import ReviewBruta, carregar, persistir
from espectro24.config import ORDENACOES
from espectro24.passada import coletar_passada, decidir, decidir_lote
from espectro24.urls import level_page_cache_key

EARLIEST = ORDENACOES["mais_antigas"]
RECENTES = ORDENACOES["mais_recentes"]


# --- quem entra no critério (§2.3) ------------------------------------------

def test_filme_abaixo_do_limiar_recebe_passada():
    d = decidir("barbie", {"dias_por_100_paginas": 5.5}, limiar=20.0)
    assert d.recebe is True
    assert "5.5" in d.motivo and "20" in d.motivo


def test_filme_acima_do_limiar_nao_recebe_passada():
    """Ele já é bem servido pela profundidade sob `by/added` — gastar
    requisição nele duplicaria cobertura existente."""
    d = decidir("friday-the-13th-2009", {"dias_por_100_paginas": 163.6}, limiar=20.0)
    assert d.recebe is False
    assert "163.6" in d.motivo


def test_limiar_e_estritamente_menor():
    assert decidir("x", {"dias_por_100_paginas": 20.0}, limiar=20.0).recebe is False
    assert decidir("x", {"dias_por_100_paginas": 19.9}, limiar=20.0).recebe is True


def test_filme_sem_metrica_fica_de_fora_com_motivo():
    """Sem métrica não há critério; incluir por precaução gastaria requisição
    numa aposta, e a passada não é pré-requisito de nada."""
    d = decidir("obscuro", None, limiar=20.0)
    assert d.recebe is False
    assert "sem_metrica" in d.motivo


def test_taxa_negativa_entra_no_criterio():
    """Taxa negativa é ainda mais rasa em tempo que zero."""
    assert decidir("x", {"dias_por_100_paginas": -3.0}, limiar=20.0).recebe is True


def test_decidir_lote_separa_dentro_e_fora():
    dentro, fora = decidir_lote(
        {"a": {"dias_por_100_paginas": 1.0},
         "b": {"dias_por_100_paginas": 99.0},
         "c": None},
        limiar=20.0)
    assert [d.slug for d in dentro] == ["a"]
    assert sorted(d.slug for d in fora) == ["b", "c"]


# --- a passada em si --------------------------------------------------------

def _bruto_base(tmp_path, slug="filme", niveis=(4.0,)):
    """Bruto pré-existente, como se viesse de uma coleta `by/added`."""
    reviews = [
        ReviewBruta(id=f"viewing:{int(n*10)}{i}", nivel=n, texto="y" * 300,
                    n_chars=300, spoiler_flag=False, pagina_origem=i + 1,
                    url="", autor_hash="h", truncada=False, texto_completo=True,
                    data="2026-08-07", ordenacao_origem=None)
        for n in niveis for i in range(3)
    ]
    meta = {
        "slug": slug,
        "ordenacao_usada": RECENTES,
        "versao_coletor": "1.9.5",
        "histograma_bruto": {str(n): 1000 for n in niveis},
        "orcamento_paginas_por_nivel": {str(n): 10 for n in niveis},
        "paginas_gastas_por_nivel": {str(n): 10 for n in niveis},
        "profundidade_sondagem": {"profundidade": 256},
    }
    persistir(slug, meta, reviews, raiz=tmp_path)
    return meta, reviews


def _fetcher_earliest(slug, niveis=(4.0,), n_paginas=3):
    """Páginas sob a ordenação da passada. Chave de cache ausente devolve HTML
    vazio (fim da paginação) — inclusive TODA chave sob `by/added`, o que
    torna qualquer vazamento de ordenação visível como coleta vazia."""
    resp = {}
    base = 900
    for n in niveis:
        for p in range(1, n_paginas + 1):
            resp[level_page_cache_key(slug, n, p, EARLIEST)] = _pagina(
                4, base_id=base, data="2012-11-10")
            base += 10
    return FakeFetcher(resp)


def test_passada_soma_ao_bruto_sem_perder_review(tmp_path):
    _, antes = _bruto_base(tmp_path)
    f = _fetcher_earliest("filme")
    coletar_passada(f, "filme", raiz=tmp_path)

    _, depois = carregar("filme", raiz=tmp_path)
    ids_antes = {r.id for r in antes}
    ids_depois = {r.id for r in depois}
    assert ids_antes <= ids_depois           # nenhuma review existente perdida
    assert len(ids_depois) > len(ids_antes)  # e material novo entrou


def test_passada_deduplica_por_id(tmp_path):
    _bruto_base(tmp_path)
    f = _fetcher_earliest("filme")
    coletar_passada(f, "filme", raiz=tmp_path)
    _, uma = carregar("filme", raiz=tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path)
    _, duas = carregar("filme", raiz=tmp_path)
    assert len(uma) == len(duas)
    assert len({r.id for r in duas}) == len(duas)


def test_reviews_da_passada_carregam_a_ordenacao_de_origem(tmp_path):
    _bruto_base(tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path)
    _, todas = carregar("filme", raiz=tmp_path)
    novas = [r for r in todas if r.ordenacao_origem == EARLIEST]
    antigas = [r for r in todas if r.ordenacao_origem is None]
    assert novas and antigas          # as duas pontas, distinguíveis
    assert all(r.data == "2012-11-10" for r in novas)


def test_passada_usa_a_url_e_o_cache_da_ordenacao_certa(tmp_path):
    _bruto_base(tmp_path)
    f = _fetcher_earliest("filme")
    coletar_passada(f, "filme", raiz=tmp_path)
    chaves = [k for _, k in f.calls]
    assert any("by_added-earliest" in k for k in chaves)
    assert not any("/by_added/" in k for k in chaves)
    assert all("added-earliest" in u for u, k in f.calls if "/reviews/" in u)


def test_meta_base_sobrevive_a_passada(tmp_path):
    """`orcamento_paginas_por_nivel` é o que a seleção lê para achar a
    fronteira raso/profundo (§3[C2]); sobrescrevê-lo com o orçamento de uma
    passada de 6 páginas mudaria a estratificação do bruto inteiro."""
    base, _ = _bruto_base(tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path)
    meta, _ = carregar("filme", raiz=tmp_path)
    assert meta["ordenacao_usada"] == RECENTES
    assert meta["orcamento_paginas_por_nivel"] == base["orcamento_paginas_por_nivel"]
    assert meta["paginas_gastas_por_nivel"] == base["paginas_gastas_por_nivel"]
    assert meta["profundidade_sondagem"] == base["profundidade_sondagem"]


def test_meta_registra_a_passada_na_lista(tmp_path):
    _bruto_base(tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path,
                    motivo="dias_por_100_paginas=5.5 < 20")
    meta, _ = carregar("filme", raiz=tmp_path)
    assert len(meta["passadas"]) == 1
    p = meta["passadas"][0]
    assert p["ordenacao"] == EARLIEST
    assert p["motivo"] == "dias_por_100_paginas=5.5 < 20"
    assert p["n_novas"] > 0
    assert p["requisicoes"] > 0
    assert "retentativa" in p
    assert p["orcamento_paginas_por_bucket"] == mod.ORCAMENTO_PAGINAS_PASSADA


def test_passada_repetida_substitui_o_item_da_mesma_ordenacao(tmp_path):
    """A lista descreve ORDENAÇÕES PRESENTES no bruto, não um log de execuções."""
    _bruto_base(tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path)
    coletar_passada(_fetcher_earliest("filme"), "filme", raiz=tmp_path)
    meta, _ = carregar("filme", raiz=tmp_path)
    assert len(meta["passadas"]) == 1


def test_passada_nao_estende_orcamento_nem_sonda_profundidade(tmp_path):
    """§2.3: sem extensão (mede déficit de cota, que a passada não persegue) e
    sem sondagem (ancora o bloco PROFUNDO, que sob ordenação CRESCENTE aponta
    para o material mais RECENTE — duplicata do que a base já tem)."""
    _bruto_base(tmp_path)
    f = _fetcher_earliest("filme", n_paginas=20)
    coletar_passada(f, "filme", raiz=tmp_path)
    meta, _ = carregar("filme", raiz=tmp_path)
    p = meta["passadas"][0]
    assert sum(p["paginas_gastas_por_nivel"].values()) <= mod.ORCAMENTO_PAGINAS_PASSADA * 3
    assert "profundidade_sondagem" not in p
    assert not any("csi/film" in u for u, _ in f.calls)   # nem histograma novo


def test_passada_exige_coleta_base(tmp_path):
    with pytest.raises(ValueError, match="coleta base"):
        coletar_passada(_fetcher_earliest("novo"), "novo", raiz=tmp_path)


def test_jsonl_continua_carregavel_por_quem_nao_conhece_o_campo(tmp_path):
    """Compatibilidade: linha sem `ordenacao_origem` carrega com `None`, e não
    é descartada como corrompida (o `except TypeError` de `carregar`)."""
    _bruto_base(tmp_path)
    linhas = (tmp_path / "filme" / "reviews.jsonl").read_text().splitlines()
    assert all("ordenacao_origem" in json.loads(x) for x in linhas)
    sem_campo = [json.dumps({k: v for k, v in json.loads(x).items()
                             if k != "ordenacao_origem"}) for x in linhas]
    (tmp_path / "filme" / "reviews.jsonl").write_text("\n".join(sem_campo) + "\n")
    _, todas = carregar("filme", raiz=tmp_path)
    assert len(todas) == len(linhas)
    assert all(r.ordenacao_origem is None for r in todas)
