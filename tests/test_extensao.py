"""[v1.9.4] Extensão de orçamento por DÉFICIT — SPEC §3[B].

Testes da lógica de extensão, escritos ANTES do módulo. Zero rede: a busca de
página é um dublê que devolve `True`/`False` (teve conteúdo / veio vazia), e a
contagem de válidas é um dublê que lê um dicionário controlado pelo teste.
"""
from __future__ import annotations

import pytest

from espectro24.alocacao import alocar_bucket
from espectro24.config import (
    COTA_POR_BUCKET,
    FOLGA_ALVO_COLETA,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    TETO_EXTENSAO_PAGINAS,
)
from espectro24.extensao import (
    escolher_nivel_da_extra,
    estender_bucket,
    meta_com_folga,
)

NIVEIS = [3.5, 4.0, 4.5, 5.0]


def _cenario(validas_por_rodada, alvo=None, vivos=None, paginas_base=16,
             teto_extras=None, meta=None):
    """Monta um `estender_bucket` com dublês.

    `validas_por_rodada` é uma lista de dicts `{nível: válidas}`: o primeiro é
    o estado ao fim do orçamento base, e cada busca de página extra avança
    para o próximo (o último se repete indefinidamente).
    """
    estado = {"i": 0}
    buscas: list[tuple[float, bool]] = []
    vazias = set() if vivos is None else set()

    def contar():
        return dict(validas_por_rodada[min(estado["i"], len(validas_por_rodada) - 1)])

    def buscar(nivel):
        teve = nivel not in vazias
        buscas.append((nivel, teve))
        estado["i"] += 1
        return teve

    res = estender_bucket(
        "positivas", NIVEIS,
        alvo_por_nivel=alvo or alocar_bucket(meta or 50, {n: 100 for n in NIVEIS}, NIVEIS),
        contar_validas=contar,
        buscar_extra=buscar,
        paginas_base=paginas_base,
        vivos=set(NIVEIS) if vivos is None else set(vivos),
        teto_extras=(TETO_EXTENSAO_PAGINAS - ORCAMENTO_PAGINAS_POR_BUCKET
                     if teto_extras is None else teto_extras),
        meta=meta or 50,
    )
    return res, buscas


# --- meta e teto -----------------------------------------------------------

def test_meta_e_a_cota_com_a_folga_ja_existente():
    """A meta reusa FOLGA_ALVO_COLETA — nenhum parâmetro de calibração novo."""
    assert meta_com_folga(COTA_POR_BUCKET) == 50
    assert meta_com_folga(COTA_POR_BUCKET) == round(COTA_POR_BUCKET * FOLGA_ALVO_COLETA)


def test_teto_de_extensao_e_50pct_sobre_a_base():
    assert TETO_EXTENSAO_PAGINAS == 24
    assert TETO_EXTENSAO_PAGINAS - ORCAMENTO_PAGINAS_POR_BUCKET == 8


# --- REGRESSÃO: o bucket que já fechava não muda nada -----------------------

def test_nao_dispara_quando_a_base_ja_atinge_a_meta():
    """O caso que NÃO pode mudar: bucket que fecha a meta no orçamento base
    gasta exatamente as 16 páginas da base, zero extras, zero requisições."""
    res, buscas = _cenario([{3.5: 13, 4.0: 13, 4.5: 12, 5.0: 12}])   # soma 50
    assert res.paginas_extensao == 0
    assert buscas == []
    assert res.motivo_parada == "meta_atingida"
    assert res.paginas_base == 16
    assert res.n_validas_pos_base == res.n_validas_pos_extensao == 50


def test_nao_dispara_quando_a_base_supera_a_meta():
    res, buscas = _cenario([{3.5: 30, 4.0: 30, 4.5: 30, 5.0: 30}])
    assert res.paginas_extensao == 0 and buscas == []
    assert res.motivo_parada == "meta_atingida"


# --- o teto nunca é excedido ----------------------------------------------

def test_extensao_respeita_o_teto_e_nunca_o_excede():
    """Bucket que nunca alcança a meta: para em 8 extras, motivo `teto_extensao`."""
    res, buscas = _cenario([{3.5: 2, 4.0: 2, 4.5: 2, 5.0: 2}])
    assert res.paginas_extensao == 8
    assert len(buscas) == 8
    assert res.paginas_base + res.paginas_extensao == TETO_EXTENSAO_PAGINAS
    assert res.motivo_parada == "teto_extensao"


def test_soma_das_extras_por_nivel_bate_com_o_total():
    res, _ = _cenario([{3.5: 2, 4.0: 2, 4.5: 2, 5.0: 2}])
    assert sum(res.extras_por_nivel.values()) == res.paginas_extensao


# --- só a níveis em déficit ------------------------------------------------

def test_extra_nunca_vai_a_nivel_que_ja_fechou_o_proprio_alvo():
    """4,5★ e 5,0★ já passaram do alvo; toda extra tem de ir aos outros dois."""
    alvo = {3.5: 12, 4.0: 13, 4.5: 12, 5.0: 13}
    res, buscas = _cenario([{3.5: 2, 4.0: 2, 4.5: 30, 5.0: 30}], alvo=alvo)
    assert {n for n, _ in buscas} <= {3.5, 4.0}
    assert 4.5 not in res.extras_por_nivel and 5.0 not in res.extras_por_nivel


def test_extra_nunca_vai_a_nivel_esgotado():
    """Nível morto (página vazia na base) não recebe extra, mesmo em déficit."""
    res, buscas = _cenario([{3.5: 2, 4.0: 2, 4.5: 2, 5.0: 2}],
                           vivos={4.0, 5.0})
    assert {n for n, _ in buscas} <= {4.0, 5.0}


def test_deficit_maior_recebe_mais_extras():
    """A alocação é proporcional ao DÉFICIT medido, não ao histograma."""
    alvo = {3.5: 12, 4.0: 13, 4.5: 12, 5.0: 13}
    #  3,5★ falta 10; os demais faltam 1, 0 e 1
    res, _ = _cenario([{3.5: 2, 4.0: 12, 4.5: 12, 5.0: 12}], alvo=alvo)
    assert res.extras_por_nivel.get(3.5, 0) > sum(
        v for n, v in res.extras_por_nivel.items() if n != 3.5)


# --- reuso obrigatório de redistribuir_deficit ------------------------------

def test_a_escolha_da_extra_passa_por_redistribuir_deficit(monkeypatch):
    """Reuso, não um segundo caminho: a decisão de qual nível recebe a página
    é tomada por `alocar_bucket` + `redistribuir_deficit`. Se alguém trocar
    isso por uma fórmula própria, este teste cai."""
    import espectro24.extensao as ext

    chamadas = {"alocar": 0, "redistribuir": 0}
    alocar_real, redistribuir_real = ext.alocar_bucket, ext.redistribuir_deficit

    def espia_alocar(*a, **k):
        chamadas["alocar"] += 1
        return alocar_real(*a, **k)

    def espia_redistribuir(*a, **k):
        chamadas["redistribuir"] += 1
        return redistribuir_real(*a, **k)

    monkeypatch.setattr(ext, "alocar_bucket", espia_alocar)
    monkeypatch.setattr(ext, "redistribuir_deficit", espia_redistribuir)

    escolher_nivel_da_extra({3.5: 5, 4.0: 5, 4.5: 0, 5.0: 0}, set(NIVEIS), 8)
    assert chamadas["alocar"] >= 1 and chamadas["redistribuir"] >= 1


def test_redistribuir_deficit_move_a_extra_de_nivel_morto_para_vivo():
    """O nível com o MAIOR déficit está morto: a extra vai para o vivo — é
    exatamente o trabalho que `redistribuir_deficit` faz aqui."""
    escolhido = escolher_nivel_da_extra(
        {3.5: 40, 4.0: 3, 4.5: 0, 5.0: 0}, vivos={4.0, 4.5, 5.0}, extras_restantes=8)
    assert escolhido == 4.0


def test_sem_nivel_vivo_em_deficit_nao_ha_escolha():
    assert escolher_nivel_da_extra({3.5: 5, 4.0: 5}, vivos=set(), extras_restantes=8) is None


def test_sem_deficit_nao_ha_escolha():
    assert escolher_nivel_da_extra({3.5: 0, 4.0: 0}, vivos={3.5, 4.0},
                                   extras_restantes=8) is None


def test_sem_extras_restantes_nao_ha_escolha():
    assert escolher_nivel_da_extra({3.5: 5}, vivos={3.5}, extras_restantes=0) is None


# --- os três motivos de parada ---------------------------------------------

def test_motivo_meta_atingida_no_meio_da_extensao():
    res, buscas = _cenario([
        {3.5: 10, 4.0: 10, 4.5: 10, 5.0: 10},    # 40 — abaixo da meta
        {3.5: 14, 4.0: 10, 4.5: 10, 5.0: 10},    # 44
        {3.5: 20, 4.0: 10, 4.5: 10, 5.0: 12},    # 52 — passou
    ])
    assert res.motivo_parada == "meta_atingida"
    assert res.paginas_extensao == 2
    assert res.n_validas_pos_base == 40
    assert res.n_validas_pos_extensao == 52


def test_motivo_teto_extensao():
    res, _ = _cenario([{3.5: 5, 4.0: 5, 4.5: 5, 5.0: 5}])
    assert res.motivo_parada == "teto_extensao" and res.paginas_extensao == 8


def test_motivo_material_esgotado_quando_todo_nivel_morre():
    """Cada página extra volta vazia; o nível morre e, quando todos morrem, a
    extensão para por material — não por teto."""
    estado = {"i": 0}
    buscas = []

    def contar():
        return {3.5: 5, 4.0: 5, 4.5: 5, 5.0: 5}

    def buscar(nivel):
        buscas.append(nivel)
        return False    # sempre vazia

    res = estender_bucket(
        "positivas", NIVEIS,
        alvo_por_nivel={3.5: 12, 4.0: 13, 4.5: 12, 5.0: 13},
        contar_validas=contar, buscar_extra=buscar, paginas_base=16,
        vivos=set(NIVEIS), teto_extras=8, meta=50)
    assert res.motivo_parada == "material_esgotado"
    assert res.paginas_extensao == 4        # uma por nível, todas vazias
    assert sorted(buscas) == sorted(NIVEIS)
    assert estado["i"] == 0


# --- degenerados -----------------------------------------------------------

def test_bucket_com_todos_os_niveis_ja_esgotados_na_base():
    """Nada a buscar: zero extras, motivo material_esgotado, zero requisições."""
    res, buscas = _cenario([{3.5: 1, 4.0: 1, 4.5: 1, 5.0: 1}], vivos=set())
    assert res.paginas_extensao == 0 and buscas == []
    assert res.motivo_parada == "material_esgotado"


def test_meta_atingida_exatamente_na_ultima_extra_permitida():
    """Fronteira: a 8ª extra (a última que o teto autoriza) fecha a meta. O
    motivo tem de ser `meta_atingida`, não `teto_extensao` — o teto só é a
    causa quando a meta NÃO foi alcançada."""
    rodadas = [{3.5: 10, 4.0: 10, 4.5: 10, 5.0: 10}]          # 40, pós-base
    for k in range(1, 8):
        rodadas.append({3.5: 10 + k, 4.0: 10, 4.5: 10, 5.0: 10})   # 41..47
    rodadas.append({3.5: 20, 4.0: 10, 4.5: 10, 5.0: 10})      # 50 — exato
    res, buscas = _cenario(rodadas)
    assert res.paginas_extensao == 8
    assert len(buscas) == 8
    assert res.n_validas_pos_extensao == 50
    assert res.motivo_parada == "meta_atingida"


def test_meta_faltando_uma_na_ultima_extra_para_por_teto():
    """O espelho do anterior: 49 de 50 na 8ª extra → `teto_extensao`."""
    rodadas = [{3.5: 10, 4.0: 10, 4.5: 10, 5.0: 10}]
    for k in range(1, 8):
        rodadas.append({3.5: 10 + k, 4.0: 10, 4.5: 10, 5.0: 10})   # 41..47
    rodadas.append({3.5: 19, 4.0: 10, 4.5: 10, 5.0: 10})           # 49 — falta 1
    res, _ = _cenario(rodadas)
    assert res.paginas_extensao == 8
    assert res.n_validas_pos_extensao == 49
    assert res.motivo_parada == "teto_extensao"


def test_bucket_vazio_nao_quebra():
    res = estender_bucket("medianas", [], alvo_por_nivel={},
                          contar_validas=lambda: {}, buscar_extra=lambda n: True,
                          paginas_base=0, vivos=set(), teto_extras=8, meta=50)
    assert res.paginas_extensao == 0
    assert res.motivo_parada == "material_esgotado"


def test_pagina_extra_vazia_conta_como_gasta():
    """Uma requisição foi feita; ela conta no orçamento de extensão mesmo sem
    render conteúdo — mesma contabilidade da página vazia que revela a
    profundidade na v1.9.2."""
    def buscar(nivel):
        return nivel != 3.5     # só 3,5★ vem vazia

    res = estender_bucket(
        "positivas", NIVEIS, alvo_por_nivel={3.5: 40, 4.0: 4, 4.5: 3, 5.0: 3},
        contar_validas=lambda: {3.5: 0, 4.0: 4, 4.5: 3, 5.0: 3},
        buscar_extra=buscar, paginas_base=16, vivos=set(NIVEIS),
        teto_extras=8, meta=50)
    assert res.extras_por_nivel.get(3.5) == 1        # gastou 1, veio vazia
    assert res.paginas_extensao >= 1


# --- telemetria ------------------------------------------------------------

def test_telemetria_tem_todos_os_campos_obrigatorios():
    res, _ = _cenario([{3.5: 5, 4.0: 5, 4.5: 5, 5.0: 5}])
    d = res.para_meta()
    for campo in ("paginas_base", "paginas_extensao", "extras_por_nivel",
                  "motivo_parada", "n_validas_pos_base", "n_validas_pos_extensao",
                  "meta"):
        assert campo in d, campo
    assert all(isinstance(k, str) for k in d["extras_por_nivel"])


@pytest.mark.parametrize("motivo", ["meta_atingida", "teto_extensao",
                                    "material_esgotado"])
def test_motivo_de_parada_e_sempre_um_dos_tres(motivo):
    assert motivo in {"meta_atingida", "teto_extensao", "material_esgotado"}
