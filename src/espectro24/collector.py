"""[B] Coleta por nível + [C] filtros e cascata de relaxamento (SPEC §B, §C)."""
from __future__ import annotations

from .config import (
    BUCKET_ALVO,
    BUCKETS,
    CASCATA_CHARS,
    COTA_POR_NIVEL,
    PISO_POR_BUCKET,
    TETO_PAGINAS,
)
from .fetcher import Fetcher
from .fulltext import complete_truncated
from .models import BucketResult, LevelResult, Review
from .parser import parse_reviews
from .urls import level_page_cache_key, level_page_url


def _passes(r: Review, min_chars: int) -> bool:
    """Ordem de filtros (§C): (1) tem nota → (2) sem spoiler → (3) comprimento."""
    return r.rating is not None and not r.spoiler and len(r.text) >= min_chars


def collect_brutas(fetcher: Fetcher, slug: str, nivel: float,
                   cota: int = COTA_POR_NIVEL, max_pages: int = TETO_PAGINAS):
    """Pagina o nível até: `cota` válidas (filtro padrão) OU página vazia OU teto.

    Retorna (brutas_deduplicadas, paginas_buscadas). Dedup por viewing_id.
    """
    brutas: list[Review] = []
    seen: set[str] = set()
    paginas = 0
    for page in range(1, max_pages + 1):
        html = fetcher.get(level_page_url(slug, nivel, page),
                           level_page_cache_key(slug, nivel, page))
        reviews = parse_reviews(html)
        if not reviews:  # página além da última = lista vazia (A1c) → parar
            break
        paginas += 1
        for r in reviews:
            key = r.viewing_id or f"anon:{len(brutas)}"
            if key in seen:
                continue
            seen.add(key)
            brutas.append(r)
        if sum(1 for r in brutas if _passes(r, CASCATA_CHARS[0])) >= cota:
            break
    return brutas, paginas


def _cascade(brutas: list[Review]) -> tuple[list[Review], int]:
    """Relaxa o filtro só quando o nível daria 0 válidas (§C.3): 150 → 50 → 0."""
    for thr in CASCATA_CHARS:
        validas = [r for r in brutas if _passes(r, thr)]
        if validas:
            return validas, thr
    return [], CASCATA_CHARS[-1]


def collect_level(fetcher: Fetcher, slug: str, nivel: float,
                  cota: int = COTA_POR_NIVEL, max_pages: int = TETO_PAGINAS) -> LevelResult:
    brutas, paginas = collect_brutas(fetcher, slug, nivel, cota, max_pages)
    validas_all, filtro = _cascade(brutas)
    validas = validas_all[:cota]  # cota por nível (§2)

    # [C'] completa truncadas entre as válidas — pode descartar (nunca pela metade)
    validas, n_trunc = complete_truncated(fetcher, slug, validas)

    com_nota = [r for r in brutas if r.rating is not None]
    return LevelResult(
        nivel=nivel,
        filtro_aplicado=filtro,
        paginas_buscadas=paginas,
        n_brutas=len(brutas),
        n_sem_nota=sum(1 for r in brutas if r.rating is None),
        n_descartadas_spoiler=sum(1 for r in com_nota if r.spoiler),
        n_descartadas_curtas=sum(
            1 for r in com_nota if not r.spoiler and len(r.text) < filtro
        ),
        n_descartadas_truncamento=n_trunc,
        validas=validas,
    )


def assemble_buckets(niveis: dict[float, LevelResult]) -> list[BucketResult]:
    buckets: list[BucketResult] = []
    for nome, lista_niveis in BUCKETS.items():
        lvls = [niveis[n] for n in lista_niveis if n in niveis]
        n_validas = sum(l.n_validas for l in lvls)
        alvo = BUCKET_ALVO[nome]
        if n_validas < PISO_POR_BUCKET:
            modo = "sem_analise"
        elif n_validas >= alvo:
            modo = "completo"
        else:
            modo = "reduzido"
        buckets.append(BucketResult(nome=nome, alvo=alvo, modo=modo, niveis=lvls))
    return buckets
