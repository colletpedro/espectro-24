"""[v1.9.15, Entrega 1] Unificar a amostra CLASSIFICADA com a ANALISADA.

O defeito medido na v1.9.14: `amostra.json` foi montada sem
`orcamento_paginas_por_nivel`, então a seleção que classificou 40 reviews por
bucket não é a mesma que a síntese de produção analisou. A correção não é
reclassificar — é ESTENDER: achar, por bucket, as reviews da seleção de
produção que ainda não têm classificação, e só essas.

Estes testes cobrem a função PURA que decide "o que falta classificar" —
sem rede, sem LLM, determinística sobre dois conjuntos de ids.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import ReviewBruta  # noqa: E402
from espectro24.uniao_amostra import reviews_faltantes  # noqa: E402


def _r(id_, texto="x" * 200):
    return ReviewBruta(id=id_, nivel=2.0, texto=texto, n_chars=len(texto),
                       spoiler_flag=False, pagina_origem=1, url="",
                       autor_hash="", truncada=False, texto_completo=True,
                       data=None)


def test_review_ja_classificada_nao_e_faltante():
    producao = {"negativas": [_r("a"), _r("b")]}
    classificadas = {"negativas": {"a"}}
    fora = reviews_faltantes(producao, classificadas)
    assert [r.id for r in fora["negativas"]] == ["b"]


def test_bucket_totalmente_coberto_fica_vazio():
    producao = {"negativas": [_r("a")]}
    classificadas = {"negativas": {"a"}}
    fora = reviews_faltantes(producao, classificadas)
    assert fora["negativas"] == []


def test_bucket_sem_classificacao_nenhuma_devolve_tudo():
    producao = {"positivas": [_r("a"), _r("b"), _r("c")]}
    classificadas = {}
    fora = reviews_faltantes(producao, classificadas)
    assert {r.id for r in fora["positivas"]} == {"a", "b", "c"}


def test_bucket_ausente_da_producao_nao_aparece_na_saida():
    producao = {"negativas": [_r("a")]}
    classificadas = {"medianas": {"z"}}
    fora = reviews_faltantes(producao, classificadas)
    assert set(fora) == {"negativas"}


def test_ordem_e_preservada_da_producao():
    producao = {"negativas": [_r("c"), _r("a"), _r("b")]}
    fora = reviews_faltantes(producao, {})
    assert [r.id for r in fora["negativas"]] == ["c", "a", "b"]


def test_id_classificado_que_nao_esta_mais_na_producao_e_ignorado():
    """A função só olha o que FALTA à produção — não reporta sobra da
    classificação antiga (isso é a leitura de sobreposição, feita depois)."""
    producao = {"negativas": [_r("a")]}
    classificadas = {"negativas": {"a", "velho-id-que-sumiu"}}
    fora = reviews_faltantes(producao, classificadas)
    assert fora["negativas"] == []
