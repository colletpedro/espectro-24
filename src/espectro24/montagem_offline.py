"""Montagem OFFLINE do `resultado/<slug>.json` (sem Letterboxd, sem recoleta).

É o caminho que gerou os 29 filmes de 08/11 (`scripts/etapa2_featherless.py::gerar_filme`), isolado numa função
testável e com a SÍNTESE injetável: em vez de chamar o modelo, o bucket recebe a síntese já gerada (a saída de
produção do C22). Tudo o mais vem do bruto persistido (`dados/bruto/<slug>`), do consenso verificado e do TMDB:

    buckets  <- selecao offline do bruto (`prosa_local._buckets_do_bruto`; `paginas_buscadas` = 0)
    síntese  <- `aplicar_sintese` (dict `bucket_final` do C22/fallback; NENHUMA chamada ao modelo)
    ficha    <- a que o chamador passa (`ficha.buscar_ficha` com a identidade do bruto)
    distrib. <- `Distribuicao.de_histograma(meta["histograma_bruto"])`
    eixos    <- `pipeline.montar_eixos` sob a classificação VERIFICADA (a rotulagem é a única chamada de LLM)

O que este módulo NÃO faz: condições, retiradas R13 e o build do frontend (etapas seguintes, as mesmas dos 29).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from .models import BucketResult, Tema

CAMPOS_TEMA = {"tema", "mencoes_aproximadas", "n_reviews_analisadas", "exemplo_parafraseado", "mencoes_clampadas",
               "mencoes_valor_original", "aspas_removidas", "quantidade_reescrita", "exemplo_antes_da_guarda",
               "quantidade_pendente"}


def sha256_arquivo(p: str | Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def aplicar_sintese(bucket: BucketResult, registro: dict[str, Any], quantidade_fallback: str | None = None) -> BucketResult:
    """Preenche o bucket com uma síntese pronta (`bucket_final` do C22: temas, observacao_geral, flags).

    Recusa quando a síntese não é deste bucket (n_validas / n_analisadas divergentes): a síntese foi gerada sobre
    uma amostra, e uma amostra diferente invalida o texto.
    """
    if registro.get("n_validas") not in (None, bucket.n_validas):
        raise ValueError(f"{bucket.nome}: síntese com n_validas={registro.get('n_validas')} "
                         f"mas a amostra do bruto tem {bucket.n_validas}")
    if registro.get("n_analisadas") not in (None, len(bucket.reviews_analisadas)):
        raise ValueError(f"{bucket.nome}: síntese com n_analisadas={registro.get('n_analisadas')} "
                         f"mas a amostra do bruto tem {len(bucket.reviews_analisadas)}")
    bucket.temas = [Tema(**{k: v for k, v in t.items() if k in CAMPOS_TEMA}) for t in registro["temas"]]
    bucket.observacao_geral = registro["observacao_geral"]
    bucket.idioma_invalido = bool(registro.get("idioma_invalido"))
    bucket.escopo_suspeito = bool(registro.get("escopo_suspeito"))
    bucket.quantidade_fallback = quantidade_fallback
    return bucket


def montar_documento(slug: str, *, bruto_raiz: str | Path, consenso_path: str | Path,
                     sintese: Callable[[BucketResult], BucketResult] | dict[str, dict],
                     ficha: dict | None, rotular: Callable[[str, str, str], str],
                     modelo_rotulagem: str, provider_rotulagem: str = "featherless",
                     proveniencia_sintese: dict | None = None,
                     fallback_por_bucket: dict[str, str | None] | None = None,
                     fonte_registrada: str | None = None,
                     classificacao_rotulo: str = "existente") -> dict:
    """O documento (o `bullets.json` de `gerar_filme`): coleta + buckets + distribuição + eixos + proveniência.

    `sintese`: `{bucket: bucket_final}` ou uma função `BucketResult -> BucketResult`.
    `rotular(system, user, model) -> str` é a ÚNICA chamada de LLM (rotulagem dos temas por eixo).
    `classificacao_rotulo`: "existente" (consenso já versionado, o caso do C22) ou o modelo que classificou de novo.
    `fonte_registrada`: o caminho que vai para a proveniência (relativo à raiz, sem diretório pessoal); o arquivo
    lido é `consenso_path`.
    Levanta se a amostra do bruto não for a classificada (guarda C14.8) ou se a síntese não casar com a amostra.
    """
    from . import eixos as E
    from . import pipeline as P
    from .models import Distribuicao
    from .prosa_local import _buckets_do_bruto
    from .render import aplicar_distribuicao, build_output

    bruto_raiz = Path(bruto_raiz)
    meta = json.loads((bruto_raiz / slug / "meta.json").read_text(encoding="utf-8"))
    am = P.amostra_do_bruto(slug, raiz=bruto_raiz)
    cat = E.carregar_classificacao(Path(consenso_path))
    E.checar_amostra_classificada(cat[slug], {b: {r.id for r in rs} for b, rs in am.items()})
    buckets = _buckets_do_bruto(slug, meta, bruto_raiz)
    for b in buckets:
        if callable(sintese):
            sintese(b)
        else:
            if b.modo == "sem_analise":
                continue
            aplicar_sintese(b, sintese[b.nome], (fallback_por_bucket or {}).get(b.nome))
    hist = {float(k): v for k, v in (meta.get("histograma_bruto") or {}).items()}
    out = build_output(slug, buckets, data_coleta=meta.get("coletado_em") or "", origens={},
                       total_observado=sum((meta.get("histograma_bruto") or {}).values()),
                       ficha=ficha, coleta=meta)
    dist = Distribuicao.de_histograma(hist)
    if dist:
        aplicar_distribuicao(out, dist)
    out["eixos"] = P.montar_eixos(slug, out, {b: {r.id for r in rs} for b, rs in am.items()}, consenso=cat,
                                  client_call=rotular, model=modelo_rotulagem, provider=provider_rotulagem)
    if out["eixos"] is None:
        raise ValueError(f"{slug}: sem bloco de eixos (classificação ausente ou taxonomia divergente)")
    out["eixos"]["verificador"] = {"aplicado": True, "fonte": fonte_registrada or str(consenso_path), "classificacao": classificacao_rotulo}
    out["proveniencia_llm"] = {
        "sintese": proveniencia_sintese or {},
        "rotulagem": {"provider": provider_rotulagem, "modelo": modelo_rotulagem},
        "classificacao": {"fonte": fonte_registrada or str(consenso_path), "sha256": sha256_arquivo(consenso_path)},
    }
    return out
