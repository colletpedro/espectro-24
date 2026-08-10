"""[v1.9.5] Sondagem de profundidade + reancoragem do bloco profundo — §3[B].

Escritos ANTES dos módulos. Zero rede: `FakeFetcher` com um nível de
profundidade conhecida.

O teste que carrega o desenho inteiro é
`test_numero_de_paginas_por_nivel_nao_muda_com_a_ancora`: a premissa da v1.9.5
é que muda ONDE as páginas caem, não QUANTAS. Se esse cair, o custo da coleta
mudou sem ninguém decidir.
"""
from __future__ import annotations

import pytest

from conftest import FakeFetcher

from espectro24.alocacao import dividir_raso_profundo
from espectro24.config import (
    FRACOES_PROFUNDIDADE,
    SONDA_ESCADA,
    SONDA_MAX_REFINAMENTO,
    TETO_PLATAFORMA_PAGINAS,
)
from espectro24.collector import raspar_nivel
from espectro24.profundidade import (
    escalar_por_histograma,
    posicoes_profundas,
    sondar_profundidade,
)
from espectro24.urls import level_page_cache_key
from test_posicionamento import _pagina


def _ff(slug: str, nivel: float, profundidade: int,
        ordenacao: str = "by/added") -> FakeFetcher:
    resp = {}
    for p in range(1, profundidade + 1):
        resp[level_page_cache_key(slug, nivel, p, ordenacao)] = _pagina(
            1, base_id=p * 1000)
    return FakeFetcher(resp)


# ===========================================================================
# Sondagem
# ===========================================================================

def test_filme_popular_custa_4_requisicoes_e_devolve_o_teto():
    """O caso DOMINANTE: os quatro degraus da escada voltam cheios, então a
    profundidade é o teto de plataforma e não há refinamento a fazer."""
    ff = _ff("pop", 4.0, TETO_PLATAFORMA_PAGINAS)
    r = sondar_profundidade(ff, "pop", 4.0)
    assert r.profundidade == TETO_PLATAFORMA_PAGINAS
    assert r.requisicoes == len(SONDA_ESCADA) == 4
    assert r.motivo == "teto_plataforma"
    assert len(ff.calls) == 4


def test_filme_obscuro_encontra_a_profundidade_real_barato():
    ff = _ff("obs", 4.0, 3)
    r = sondar_profundidade(ff, "obs", 4.0)
    assert r.profundidade == 3
    assert r.exata is True
    assert r.requisicoes <= len(SONDA_ESCADA) + SONDA_MAX_REFINAMENTO


@pytest.mark.parametrize("real", [1, 2, 3, 4, 5, 15, 16, 17, 63, 64, 65])
def test_sondagem_nunca_superestima(real):
    """Nunca devolver profundidade MAIOR que a real — superestimar faria a
    âncora mirar em página vazia. Subestimar é aceitável (é um limite
    inferior confirmado)."""
    ff = _ff("x", 4.0, real)
    r = sondar_profundidade(ff, "x", 4.0)
    assert r.profundidade is None or r.profundidade <= real


def test_custo_da_sondagem_e_limitado():
    """Teto duro de requisições: escada + refinamento, nunca mais."""
    for real in (1, 7, 33, 100, 200, 255, 256):
        ff = _ff("x", 4.0, real)
        r = sondar_profundidade(ff, "x", 4.0)
        assert r.requisicoes <= len(SONDA_ESCADA) + SONDA_MAX_REFINAMENTO, real


def test_nivel_sem_nenhuma_pagina_devolve_none():
    r = sondar_profundidade(FakeFetcher({}), "vazio", 4.0)
    assert r.profundidade is None
    assert r.motivo == "sem_material"


def test_falha_de_rede_degrada_sem_quebrar():
    """Sondagem é ADITIVA: erro de rede não pode derrubar a coleta."""
    class Explode(FakeFetcher):
        def get(self, url, cache_key):
            from espectro24.fetcher import FetchError
            raise FetchError("boom")

    r = sondar_profundidade(Explode({}), "x", 4.0)
    assert r.profundidade is None
    assert r.motivo == "falha"


# ===========================================================================
# Escala por histograma — PROXY declarado
# ===========================================================================

def test_escala_proporcional_ao_histograma():
    hist = {4.0: 1000, 3.0: 500, 0.5: 100}
    est = escalar_por_histograma(200, 4.0, hist)
    assert est[4.0] == 200
    assert est[3.0] == 100
    assert est[0.5] == 20


def test_escala_respeita_piso_de_1_e_teto_de_plataforma():
    hist = {4.0: 1_000_000, 0.5: 1}
    est = escalar_por_histograma(TETO_PLATAFORMA_PAGINAS, 4.0, hist)
    assert est[0.5] == 1
    assert max(est.values()) <= TETO_PLATAFORMA_PAGINAS


def test_escala_com_nivel_zerado_no_histograma():
    est = escalar_por_histograma(100, 4.0, {4.0: 1000, 1.0: 0})
    assert est[1.0] == 1          # piso, não zero nem erro


def test_escala_sem_profundidade_devolve_vazio():
    assert escalar_por_histograma(None, 4.0, {4.0: 10}) == {}


# ===========================================================================
# Reancoragem
# ===========================================================================

def test_posicoes_sao_fracoes_da_profundidade_nao_incrementos_do_raso():
    """O coração da v1.9.5. Com profundidade 200 e bloco raso de 12, as
    posições têm de ir a 50/100/150/190 — não a 14/16/20/28."""
    pos = posicoes_profundas(n_raso=12, n_profundo=4, profundidade=200)
    assert pos == [50, 100, 150, 190]
    assert min(pos) > 40


def test_posicoes_respeitam_as_fracoes_declaradas():
    pos = posicoes_profundas(n_raso=4, n_profundo=4, profundidade=100)
    assert pos == [round(f * 100) for f in FRACOES_PROFUNDIDADE]


def test_so_o_numero_pedido_de_posicoes():
    assert len(posicoes_profundas(12, 2, 200)) == 2
    assert len(posicoes_profundas(12, 1, 200)) == 1
    assert posicoes_profundas(12, 0, 200) == []


def test_posicoes_sempre_alem_do_bloco_raso():
    pos = posicoes_profundas(n_raso=30, n_profundo=4, profundidade=40)
    assert all(p > 30 for p in pos)


def test_profundidade_menor_que_o_raso_nao_emite_posicao():
    """Degenerado nomeado: o bloco profundo se fundiria ao raso. Filme
    obscuro — não há profundidade a alcançar, degrada para consecutivo."""
    assert posicoes_profundas(n_raso=12, n_profundo=4, profundidade=8) == []
    assert posicoes_profundas(n_raso=12, n_profundo=4, profundidade=12) == []


def test_profundidade_1():
    assert posicoes_profundas(n_raso=1, n_profundo=1, profundidade=1) == []


def test_profundidade_curta_deduplica_posicoes_colididas():
    """Frações que colidem em profundidade pequena não repetem página."""
    pos = posicoes_profundas(n_raso=1, n_profundo=4, profundidade=4)
    assert len(pos) == len(set(pos))
    assert all(1 < p <= 4 for p in pos)


def test_profundidade_desconhecida_cai_no_comportamento_v192():
    """Sem sondagem, a progressão geométrica da v1.9.2 — nem erro nem
    posição inventada."""
    pos = posicoes_profundas(n_raso=12, n_profundo=4, profundidade=None)
    assert pos == [12 + 2 ** k for k in range(1, 5)]


# ===========================================================================
# A PREMISSA: muda ONDE, não QUANTAS
# ===========================================================================

@pytest.mark.parametrize("orcamento", [1, 2, 4, 8, 10, 16])
def test_numero_de_paginas_por_nivel_nao_muda_com_a_ancora(orcamento):
    """O teste que prova a premissa da v1.9.5.

    O mesmo nível, com material de sobra, buscado sob a âncora antiga
    (`profundidade=None` → v1.9.2) e sob a nova: o NÚMERO de páginas tem de
    ser idêntico. Se este cair, a mudança de âncora alterou o custo da coleta
    sem ninguém ter decidido isso."""
    ff_velho = _ff("v", 4.0, 300)
    velho = raspar_nivel(ff_velho, "v", 4.0, alvo=0, teto_paginas=orcamento)

    ff_novo = _ff("n", 4.0, 300)
    novo = raspar_nivel(ff_novo, "n", 4.0, alvo=0, teto_paginas=orcamento,
                        profundidade=256)

    assert novo.paginas_gastas == velho.paginas_gastas
    assert len(ff_novo.calls) == len(ff_velho.calls)
    n_raso, n_prof = dividir_raso_profundo(orcamento)
    if n_prof:
        # ... e as posições MUDARAM: é o ponto da versão.
        assert max(novo.posicoes_buscadas) > max(velho.posicoes_buscadas)


def test_ancora_nova_alcanca_muito_mais_fundo():
    ff_v = _ff("v", 4.0, 300)
    velho = raspar_nivel(ff_v, "v", 4.0, alvo=0, teto_paginas=16)
    ff_n = _ff("n", 4.0, 300)
    novo = raspar_nivel(ff_n, "n", 4.0, alvo=0, teto_paginas=16,
                        profundidade=256)
    assert max(velho.posicoes_buscadas) <= 32
    assert max(novo.posicoes_buscadas) >= 200


def test_orcamento_nunca_excedido_sob_a_ancora_nova():
    for orcamento in (1, 3, 8, 16):
        ff = _ff("x", 4.0, 300)
        nb = raspar_nivel(ff, "x", 4.0, alvo=0, teto_paginas=orcamento,
                          profundidade=256)
        assert nb.paginas_gastas <= orcamento


def test_estimativa_errada_redistribui_pelo_mecanismo_existente():
    """PROXY que erra: a profundidade estimada é 200 mas o nível real tem 60.
    A primeira posição estimada vazia revela a profundidade e o orçamento
    sobrante volta ao intervalo confirmado — o MESMO `redistribuir_deficit`
    da v1.9.2, sem segundo caminho."""
    ff = _ff("erra", 4.0, 60)
    nb = raspar_nivel(ff, "erra", 4.0, alvo=0, teto_paginas=16,
                      profundidade=200)
    assert nb.motivo_parada == "material_esgotado"
    assert nb.paginas_gastas <= 16
    # no máximo 1 página desperdiçada — a que revelou a profundidade
    vazias = [p for p in nb.posicoes_buscadas if p > 60]
    assert len(vazias) <= 1


def test_nivel_raso_degrada_para_consecutivo():
    ff = _ff("raso", 4.0, 5)
    nb = raspar_nivel(ff, "raso", 4.0, alvo=0, teto_paginas=16,
                      profundidade=256)
    assert nb.motivo_parada == "material_esgotado"
    assert nb.posicoes_buscadas <= {1, 2, 3, 4, 5, 6}
