"""[C'] Completamento de reviews truncadas — regra "nunca pela metade" (SPEC §C').

Aplicado SOMENTE a reviews que já passaram todos os filtros.
"""
from __future__ import annotations

from .fetcher import AntiBotError, FetchError, Fetcher
from .models import Review
from .parser import is_spoiler_text, parse_full_text
from .urls import full_text_cache_key, full_text_url


def complete_review(fetcher: Fetcher, slug: str, review: Review) -> bool:
    """Resolve o texto completo de uma review truncada.

    Retorna True se a review deve ser MANTIDA (texto completo obtido e sem
    spoiler revelado); False se deve ser DESCARTADA. Nunca deixa texto parcial.
    Faz 1 retentativa em caso de falha de rede (§C'.3).
    """
    if not review.truncated:
        review.full_text = review.text  # já completo
        return True
    if not review.full_text_url:
        # truncada mas sem URL de completamento → não dá pra completar → descartar
        return False

    url = full_text_url(review.full_text_url)
    key = full_text_cache_key(slug, review.viewing_id or review.full_text_url)

    last_err: Exception | None = None
    for _ in range(2):  # tentativa + 1 retentativa
        try:
            html = fetcher.get(url, key)
            full = parse_full_text(html)
            if is_spoiler_text(full):  # §C'.4 — spoiler revelado no texto completo
                review.spoiler = True
                return False
            review.full_text = full
            return True
        except AntiBotError:
            raise  # anti-bot: propaga e PARA
        except FetchError as e:
            last_err = e
            continue
    return False  # falha persistente → descartar


def complete_truncated(fetcher: Fetcher, slug: str, reviews: list[Review]):
    """Completa a lista in-place. Retorna (mantidas, n_descartadas_truncamento)."""
    mantidas: list[Review] = []
    descartadas = 0
    for r in reviews:
        if complete_review(fetcher, slug, r):
            mantidas.append(r)
        else:
            descartadas += 1
    return mantidas, descartadas
