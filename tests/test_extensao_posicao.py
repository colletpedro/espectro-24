"""[v1.9.4] Onde caem as páginas de EXTENSÃO, posicionalmente — SPEC §3[B].

A extensão NÃO recalcula a divisão raso/profundo: se recalculasse, as posições
geométricas mudariam e a coleta base deixaria de ser prefixo exato da coleta
estendida. As extras são ANEXADAS — primeiro nos buracos dentro do intervalo
já confirmado (conteúdo garantido por monotonicidade), depois além dele.
"""
from conftest import FakeFetcher

from espectro24.collector import estender_nivel, raspar_nivel
from espectro24.urls import level_page_cache_key
from test_posicionamento import _pagina


def _fetcher(slug: str, nivel: float, profundidade: int,
             ordenacao: str = "by/added") -> FakeFetcher:
    resp = {}
    for p in range(1, profundidade + 1):
        resp[level_page_cache_key(slug, nivel, p, ordenacao)] = _pagina(
            1, base_id=p * 1000)
    return FakeFetcher(resp)


def test_base_registra_as_posicoes_buscadas_e_a_maior_confirmada():
    """Sem essa contabilidade a extensão não saberia onde continuar."""
    ff = _fetcher("f", 4.0, 40)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    # orçamento 10 → raso 1..8, profundo 8+2=10 e 8+4=12
    assert nb.posicoes_buscadas == {1, 2, 3, 4, 5, 6, 7, 8, 10, 12}
    assert nb.maior_confirmada == 12
    assert nb.paginas_gastas == 10


def test_primeira_extra_preenche_o_buraco_dentro_do_intervalo_confirmado():
    """Posição 9 está entre confirmadas (8 e 10) — tem conteúdo garantido."""
    ff = _fetcher("f", 4.0, 40)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    antes = len(nb.reviews)
    teve = estender_nivel(ff, "f", nb)
    assert teve is True
    assert 9 in nb.posicoes_buscadas
    assert len(nb.reviews) > antes


def test_extras_seguintes_esgotam_os_buracos_antes_de_ir_alem():
    ff = _fetcher("f", 4.0, 40)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    novas = [estender_nivel(ff, "f", nb) or True for _ in range(4)]
    assert all(novas)
    # buracos 9 e 11 primeiro, depois 13 e 14 (além do confirmado)
    assert {9, 11, 13, 14} <= nb.posicoes_buscadas
    assert nb.maior_confirmada == 14


def test_extra_nunca_rebusca_posicao_ja_buscada():
    ff = _fetcher("f", 4.0, 40)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    antes = set(nb.posicoes_buscadas)
    for _ in range(6):
        estender_nivel(ff, "f", nb)
    assert len(nb.posicoes_buscadas) == len(antes) + 6


def test_extra_alem_da_profundidade_real_devolve_falso_e_marca_esgotado():
    """Nível com 12 páginas de conteúdo: o buraco em 9 e 11 rende, a 13 não."""
    ff = _fetcher("f", 4.0, 12)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    assert estender_nivel(ff, "f", nb) is True     # 9
    assert estender_nivel(ff, "f", nb) is True     # 11
    assert estender_nivel(ff, "f", nb) is False    # 13 — vazia
    assert nb.motivo_parada == "material_esgotado"


def test_nivel_raso_estende_consecutivo_a_partir_do_fim():
    """Orçamento 1 → só a posição 1 na base; a extra vai para 2, 3, …"""
    ff = _fetcher("f", 4.0, 40)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=1)
    assert nb.posicoes_buscadas == {1}
    estender_nivel(ff, "f", nb)
    estender_nivel(ff, "f", nb)
    assert nb.posicoes_buscadas == {1, 2, 3}


def test_extra_nao_recalcula_raso_profundo_a_base_continua_prefixo():
    """A garantia central: as posições da base são as MESMAS com e sem
    extensão. Se a extensão recalculasse o orçamento, as geométricas
    mudariam de lugar e a base deixaria de ser prefixo."""
    ff1 = _fetcher("f", 4.0, 40)
    base_sozinha = raspar_nivel(ff1, "f", 4.0, alvo=0, teto_paginas=10)

    ff2 = _fetcher("f", 4.0, 40)
    com_extensao = raspar_nivel(ff2, "f", 4.0, alvo=0, teto_paginas=10)
    for _ in range(8):
        estender_nivel(ff2, "f", com_extensao)

    assert base_sozinha.posicoes_buscadas <= com_extensao.posicoes_buscadas


def test_extra_em_nivel_ja_esgotado_nao_faz_requisicao():
    """Defensivo: nível morto não gasta requisição, mesmo se chamado."""
    ff = _fetcher("f", 4.0, 3)
    nb = raspar_nivel(ff, "f", 4.0, alvo=0, teto_paginas=10)
    assert nb.motivo_parada == "material_esgotado"
    antes = len(ff.calls)
    assert estender_nivel(ff, "f", nb) is False
    assert len(ff.calls) == antes
