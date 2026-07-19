"""Cascata de relaxamento por nível + piso por bucket (SPEC §C)."""
from conftest import FakeFetcher, fx

from espectro24 import collector
from espectro24.collector import _cascade, _passes, assemble_buckets, collect_level
from espectro24.models import LevelResult, Review
from espectro24.urls import level_page_cache_key


def _r(rating, chars, spoiler=False, trunc=False, vid="v"):
    return Review(viewing_id=vid, rating=rating, text="x" * chars,
                  truncated=trunc, full_text_url=None, spoiler=spoiler,
                  full_text=("x" * chars if not trunc else None))


def test_passes_ordem_dos_filtros():
    assert _passes(_r(4.0, 200), 150) is True
    assert _passes(_r(None, 200), 150) is False          # sem nota
    assert _passes(_r(4.0, 200, spoiler=True), 150) is False  # spoiler
    assert _passes(_r(4.0, 100), 150) is False           # curta


def test_cascata_usa_padrao_quando_ha_validas():
    brutas = [_r(4.0, 200, vid=f"a{i}") for i in range(3)]
    validas, filtro = _cascade(brutas)
    assert filtro == 150 and len(validas) == 3


def test_cascata_relaxa_para_50_quando_padrao_da_zero():
    brutas = [_r(4.0, 80, vid=f"b{i}") for i in range(4)]  # 50<=80<150
    validas, filtro = _cascade(brutas)
    assert filtro == 50 and len(validas) == 4


def test_cascata_remove_filtro_quando_50_da_zero():
    brutas = [_r(4.0, 20, vid=f"c{i}") for i in range(2)]  # <50
    validas, filtro = _cascade(brutas)
    assert filtro == 0 and len(validas) == 2


def test_cascata_nivel_pode_terminar_vazio():
    brutas = [_r(None, 200), _r(4.0, 200, spoiler=True)]  # nenhuma com nota+sem spoiler
    validas, filtro = _cascade(brutas)
    assert validas == [] and filtro == 0


def test_piso_por_bucket_sem_analise():
    # bucket negativas com só 2 válidas totais → sem_analise
    niveis = {n: LevelResult(n, 150, 1, 0, 0, 0, 0, 0) for n in
              [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]}
    niveis[0.5].validas = [_r(0.5, 200, vid="x1"), _r(0.5, 200, vid="x2")]
    buckets = {b.nome: b for b in assemble_buckets(niveis)}
    assert buckets["negativas"].modo == "sem_analise"
    assert buckets["negativas"].n_validas == 2


def test_piso_por_bucket_reduzido_e_completo():
    niveis = {n: LevelResult(n, 150, 1, 0, 0, 0, 0, 0) for n in
              [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]}
    # medianas: 3 válidas (>=piso 3, <alvo 20) → reduzido
    niveis[3.0].validas = [_r(3.0, 200, vid=f"m{i}") for i in range(3)]
    # positivas: cada nível com 10 → 30 = alvo → completo
    for n in (4.0, 4.5, 5.0):
        niveis[n].validas = [_r(n, 200, vid=f"p{n}{i}") for i in range(10)]
    buckets = {b.nome: b for b in assemble_buckets(niveis)}
    assert buckets["medianas"].modo == "reduzido"
    assert buckets["positivas"].modo == "completo"


def test_collect_level_para_em_pagina_vazia():
    # página 1 = fixture real (12 reviews, 5★ level), página 2 ausente → vazia
    key1 = level_page_cache_key("oppenheimer-2023", 5.0, 1)
    ff = FakeFetcher({key1: fx("oppenheimer-2023_rated5_page1.html")})
    lvl = collect_level(ff, "oppenheimer-2023", 5.0)
    assert lvl.paginas_buscadas == 1          # parou na página vazia seguinte
    assert lvl.n_brutas == 12
    assert lvl.filtro_aplicado == 150
    assert lvl.n_validas >= 1
