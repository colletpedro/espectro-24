"""[v1.9.15, Entrega 1] Unificar a amostra CLASSIFICADA com a ANALISADA.

O defeito medido na v1.9.14 (§[D3], "Duas populações de 40"): a amostra que
foi classificada por eixo (`resultado/votacao-3/amostra.json`) e a amostra
que a síntese de produção analisa (`pipeline.amostra_do_bruto`) são duas
seleções DIFERENTES do mesmo bucket, porque a primeira foi montada sem
`orcamento_paginas_por_nivel` (a estratificação por profundidade da v1.9.5).

A correção não é reclassificar o corpus — é ESTENDER: achar, por bucket, as
reviews da seleção de PRODUÇÃO que ainda não têm classificação, e classificar
só essas. `reviews_faltantes` é a função pura que decide o que falta; o
resto (rodar as 3 passadas, gravar o consenso) é orquestração em
`scripts/estender_classificacao_producao.py`, fora deste módulo porque
envolve rede/LLM.
"""
from __future__ import annotations

from typing import Iterable

from .bruto import ReviewBruta

__all__ = ["reviews_faltantes"]


def reviews_faltantes(
    amostra_producao: dict[str, list[ReviewBruta]],
    ja_classificadas: dict[str, Iterable[str]],
) -> dict[str, list[ReviewBruta]]:
    """Por bucket, as `ReviewBruta` da amostra de PRODUÇÃO cujo id NÃO está
    entre as já classificadas.

    Só olha buckets presentes em `amostra_producao` — um bucket que só existe
    do lado da classificação antiga (porque a seleção mudou) não gera saída
    aqui; isso é reportado como sobreposição, não como falta. A ordem da
    produção é preservada.
    """
    fora: dict[str, list[ReviewBruta]] = {}
    for bucket, reviews in amostra_producao.items():
        ja = set(ja_classificadas.get(bucket) or ())
        fora[bucket] = [r for r in reviews if r.id not in ja]
    return fora
