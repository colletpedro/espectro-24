"""Orquestração do pipeline (SPEC §3): [A]→[B]→[C]→[C']→[D]→[E]."""
from __future__ import annotations

from .collector import assemble_buckets, collect_distribuicao, collect_level
from .config import COTA_POR_NIVEL, NIVEIS_ORDENADOS, TETO_PAGINAS
from .fetcher import Fetcher
from .models import LevelResult, SearchResult
from .parser import parse_search_results
from .synthesize import synthesize_bucket
from .urls import search_cache_key, search_url


def resolve_slug(fetcher: Fetcher, query: str) -> list[SearchResult]:
    """[A] Busca de slug via endpoint AJAX. Retorna candidatos (top primeiro)."""
    html = fetcher.get(search_url(query), search_cache_key(query))
    return parse_search_results(html)


def collect_all_levels(fetcher: Fetcher, slug: str, cota: int = COTA_POR_NIVEL,
                       max_pages: int = TETO_PAGINAS,
                       on_level=None) -> dict[float, LevelResult]:
    niveis: dict[float, LevelResult] = {}
    for n in NIVEIS_ORDENADOS:
        lvl = collect_level(fetcher, slug, n, cota, max_pages)
        niveis[n] = lvl
        if on_level:
            on_level(lvl)
    return niveis


def run_pipeline(fetcher: Fetcher, slug: str, data_coleta: str,
                 client_call=None, model=None, provider=None, synth: bool = True,
                 cota: int = COTA_POR_NIVEL, max_pages: int = TETO_PAGINAS,
                 on_level=None, distribuicao: bool = True):
    """Executa coleta→distribuição→cascata→completamento→síntese.
    Retorna (buckets, niveis, distrib).

    `model`/`provider` propagam para `synthesize_bucket` sem forçar um default
    aqui (v1.1.1): o default de modelo depende do provider resolvido lá —
    forçar MODEL_DEFAULT (Anthropic) neste nível quebraria o default
    provider-específico do Gemini quando nenhum --model é passado.

    v1.4.0: `distribuicao` controla a busca do histograma (+1 requisição
    cacheada). Falha vira None sem interromper nada (§3b).
    """
    niveis = collect_all_levels(fetcher, slug, cota, max_pages, on_level=on_level)
    buckets = assemble_buckets(niveis)
    distrib = collect_distribuicao(fetcher, slug) if distribuicao else None

    if synth:
        for b in buckets:
            synthesize_bucket(b, client_call=client_call, model=model, provider=provider)
    return buckets, niveis, distrib


def total_observado(niveis: dict[float, LevelResult]) -> int:
    return sum(l.n_brutas for l in niveis.values())
