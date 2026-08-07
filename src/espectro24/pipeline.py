"""Orquestração do pipeline (SPEC §3).

**v1.9.0 — a ordem mudou, e a mudança é a arquitetura.**

    [G] histograma → [C1] alocação → [B] superset → [B'] persistência
    ─────────────────── COLETA ───────────────────
    ─────────────────── ANÁLISE ──────────────────
    [C2] seleção 40/40/40 → [C3] piso escalonado → [D] síntese

Acima da linha nada sabe onde ficam as fronteiras, qual é a cota ou qual
filtro vale. Abaixo, tudo é parâmetro aplicado sobre o material em disco.
[G] foi promovido para o começo porque a alocação precisa do histograma —
continua custando 1 requisição cacheada e continua não bloqueando (sem ele,
a alocação cai para uniforme).
"""
from __future__ import annotations

from pathlib import Path

from .alocacao import alocar, orcamento_paginas
from .bruto import carregar
from .collector import coletar_superset, collect_distribuicao
from .config import (
    BUCKETS,
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    NIVEIS_ORDENADOS,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    ORDENACAO,
)
from .fetcher import Fetcher
from .models import BucketResult, LevelResult, SearchResult
from .parser import parse_search_results
from .selecao import selecionar
from .synthesize import synthesize_bucket
from .urls import search_cache_key, search_url


def resolve_slug(fetcher: Fetcher, query: str) -> list[SearchResult]:
    """[A] Busca de slug via endpoint AJAX. Retorna candidatos (top primeiro)."""
    html = fetcher.get(search_url(query), search_cache_key(query))
    return parse_search_results(html)


def montar_buckets(selecao, superset=None) -> list[BucketResult]:
    """Converte o resultado da SELEÇÃO nos `BucketResult` que §D e §E esperam.

    Junta as duas metades da telemetria: o que veio da **coleta**
    (`paginas_buscadas`, por nível) e o que veio da **análise** (n_validas,
    alvo, filtro aplicado, descartes). `modo` continua sendo calculado como
    sempre — render e frontend o consomem e estão fora do escopo desta
    versão; `estado_piso` entra ao lado, não no lugar.
    """
    from .config import BUCKET_ALVO, PISO_POR_BUCKET

    paginas = {}
    if superset is not None:
        paginas = {n: nb.paginas_gastas for n, nb in superset.niveis.items()}

    buckets: list[BucketResult] = []
    for nome in BUCKETS:
        sel = selecao[nome]
        lvls = []
        for nivel, ns in sel.niveis.items():
            lvls.append(LevelResult(
                nivel=nivel,
                filtro_aplicado=ns.filtro_aplicado,
                paginas_buscadas=paginas.get(nivel, 0),
                n_brutas=ns.n_brutas,
                n_sem_nota=ns.n_sem_nota,
                n_descartadas_spoiler=ns.n_descartadas_spoiler,
                n_descartadas_curtas=ns.n_descartadas_curtas,
                n_descartadas_truncamento=ns.n_descartadas_truncamento,
                n_indisponivel_truncamento=ns.n_indisponivel_truncamento,
                motivos_descarte=ns.motivos_descarte,
                n_alvo=ns.n_alvo,
                validas=[r.para_review() for r in ns.validas],
            ))
        n_validas = sel.n_final
        alvo = BUCKET_ALVO[nome]
        if n_validas < PISO_POR_BUCKET:
            modo = "sem_analise"
        elif n_validas >= alvo:
            modo = "completo"
        else:
            modo = "reduzido"
        buckets.append(BucketResult(
            nome=nome, alvo=alvo, modo=modo, estado_piso=sel.estado_piso,
            niveis=lvls,
            composicao_alvo={str(k): v for k, v in sel.composicao_alvo.items()},
            composicao_atingida={str(k): v for k, v in sel.composicao_atingida.items()},
            cascata_por_degrau={str(k): v for k, v in sel.cascata_por_degrau.items()},
            deficit_redistribuido=sel.deficit_redistribuido,
        ))
    return buckets


def collect_all_levels(fetcher: Fetcher, slug: str,
                       cota_por_bucket: int = COTA_POR_BUCKET,
                       orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
                       ordenacao: str = ORDENACAO,
                       dados_dir: str | Path = DADOS_BRUTO_DIR,
                       distribuicao: bool = True,
                       on_level=None):
    """[G] → [C1] → [B] → [B']: a metade de COLETA, isolada.

    Devolve `(superset, distrib)`. Não seleciona nada — quem faz isso é
    `selecionar`, sobre o que este passo deixou em disco.

    `orcamento_paginas_bucket` (v1.9.1, §3[B]) é o orçamento de páginas POR
    BUCKET — igual para os três nomes, não importa quantos níveis cada um
    tem, o que fecha o defeito estrutural da v1.9.0 (teto por NÍVEL misturava
    unidades com cota por BUCKET). Distribuído entre os níveis de cada
    bucket via `alocacao.orcamento_paginas` (reusa `alocar_bucket`) e
    entregue a `coletar_superset` como um teto POR NÍVEL — o coletor em si
    continua sem saber o que é um bucket.
    """
    distrib = collect_distribuicao(fetcher, slug) if distribuicao else None
    hist = distrib.por_nivel if distrib else None

    alocacao = alocar({nome: cota_por_bucket for nome in BUCKETS}, hist)
    alvo_por_nivel = {n: 0 for n in NIVEIS_ORDENADOS}
    for por_nivel in alocacao.values():
        alvo_por_nivel.update(por_nivel)

    orc = orcamento_paginas(
        {nome: orcamento_paginas_bucket for nome in BUCKETS}, hist)
    teto_por_nivel = {n: orcamento_paginas_bucket for n in NIVEIS_ORDENADOS}
    for por_nivel in orc.values():
        teto_por_nivel.update(por_nivel)

    superset = coletar_superset(
        fetcher, slug, alvo_por_nivel, hist, raiz=dados_dir,
        ordenacao=ordenacao, teto_paginas=teto_por_nivel, on_level=on_level)
    return superset, distrib


def run_pipeline(fetcher: Fetcher, slug: str, data_coleta: str,
                 client_call=None, model=None, provider=None, synth: bool = True,
                 cota_por_bucket: int = COTA_POR_BUCKET,
                 orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
                 on_level=None, distribuicao: bool = True,
                 ordenacao: str = ORDENACAO,
                 dados_dir: str | Path = DADOS_BRUTO_DIR):
    """Executa coleta do superset → seleção → síntese.

    Retorna `(buckets, superset, distrib)`.

    `model`/`provider` propagam para `synthesize_bucket` sem forçar um default
    aqui (v1.1.1): o default de modelo depende do provider resolvido lá.

    `orcamento_paginas_bucket` (v1.9.1) substitui o antigo `max_pages` (teto
    POR NÍVEL) — ver `collect_all_levels`.
    """
    superset, distrib = collect_all_levels(
        fetcher, slug, cota_por_bucket, orcamento_paginas_bucket, ordenacao,
        dados_dir, distribuicao, on_level)

    # A seleção lê o BRUTO PERSISTIDO, não o que acabou de ser raspado: assim
    # ela enxerga o material acumulado de todas as coletas anteriores, e o
    # caminho de re-seleção offline é literalmente o mesmo código.
    _, todas = carregar(slug, raiz=dados_dir)
    sel = selecionar(todas, distrib.por_nivel if distrib else None,
                     cota_por_bucket=cota_por_bucket)
    buckets = montar_buckets(sel, superset)

    if synth:
        for b in buckets:
            synthesize_bucket(b, client_call=client_call, model=model, provider=provider)
    return buckets, superset, distrib


def total_observado(superset) -> int:
    """Total de reviews BRUTAS observadas na coleta (§E, rodapé)."""
    return sum(nb.n_bruta for nb in superset.niveis.values())
