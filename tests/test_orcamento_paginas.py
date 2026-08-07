"""[v1.9.1, Entrega 1] Orçamento de páginas POR BUCKET — SPEC §3[B].

Corrige o defeito estrutural registrado na v1.9.0: o teto de páginas era por
NÍVEL (4, flat) enquanto a cota de análise é por BUCKET (40); sob a opção C,
`medianas` (2 níveis) tinha metade do teto agregado de `negativas`/`positivas`
(4 níveis) — 8 contra 16 — e por isso nunca fechava a cota (medido: 35, 23,
26 nos 3 filmes).

Estes testes provam duas coisas centrais: (1) o orçamento por bucket é
CONSTANTE, não depende do número de níveis — é isso que fecha o defeito; (2)
a distribuição entre níveis e a redistribuição do excedente do teto de
segurança REAPROVEITAM `alocar_bucket`/`redistribuir_deficit` — não há uma
segunda fórmula.
"""
import pytest

from espectro24.alocacao import (
    orcamento_paginas,
    orcamento_paginas_bucket,
    redistribuir_deficit,
)
from espectro24.buckets import FRONTEIRAS_C, FRONTEIRAS_V18, mapa_de_niveis

NEG_C = mapa_de_niveis(FRONTEIRAS_C)["negativas"]       # [0.5, 1.0, 1.5, 2.0]
MED_C = mapa_de_niveis(FRONTEIRAS_C)["medianas"]         # [2.5, 3.0]
POS_C = mapa_de_niveis(FRONTEIRAS_C)["positivas"]        # [3.5, 4.0, 4.5, 5.0]

# Histogramas reais (dados/bruto/*/meta.json, histograma_bruto) — usados para
# reproduzir o caso concreto que motivou o teto de segurança.
HIST_MEDIANAS_CIDADE_DE_DEUS = {2.5: 6324, 3.0: 35847}
HIST_NEGATIVAS_CURE = {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251}


# --- a soma nunca excede o orçamento ---

@pytest.mark.parametrize("contagens,niveis", [
    (HIST_NEGATIVAS_CURE, NEG_C),
    (HIST_MEDIANAS_CIDADE_DE_DEUS, MED_C),
    ({n: 100 for n in POS_C}, POS_C),
    ({0.5: 1, 1.0: 1, 1.5: 1, 2.0: 99997}, NEG_C),   # extremo: 1 nível domina
])
@pytest.mark.parametrize("orcamento", [16, 8, 4, 20])
def test_soma_nunca_excede_o_orcamento(contagens, niveis, orcamento):
    a = orcamento_paginas_bucket(orcamento, contagens, niveis, piso=1, teto_nivel=10)
    assert sum(a.values()) <= orcamento
    assert set(a) == set(niveis)
    assert all(v >= 0 for v in a.values())


# --- piso respeitado quando possível ---

def test_piso_de_1_pagina_respeitado_com_material_suficiente():
    a = orcamento_paginas_bucket(16, HIST_NEGATIVAS_CURE, NEG_C, piso=1, teto_nivel=10)
    assert all(v >= 1 for v in a.values())


def test_piso_e_parametro():
    a = orcamento_paginas_bucket(16, HIST_NEGATIVAS_CURE, NEG_C, piso=2, teto_nivel=10)
    assert all(v >= 2 for v in a.values())


# --- teto de segurança respeitado, e o excedente é redistribuído ---

def test_teto_de_seguranca_respeitado():
    a = orcamento_paginas_bucket(16, HIST_MEDIANAS_CIDADE_DE_DEUS, MED_C,
                                 piso=1, teto_nivel=10)
    assert all(v <= 10 for v in a.values())


def test_caso_real_cidade_de_deus_medianas_o_teto_binda():
    """3,0★ tem 85% do histograma de medianas — sem teto de segurança levaria
    ~14 páginas sozinho. Com teto=10, o excedente vai para 2,5★."""
    a = orcamento_paginas_bucket(16, HIST_MEDIANAS_CIDADE_DE_DEUS, MED_C,
                                 piso=1, teto_nivel=10)
    assert a[3.0] == 10
    assert a[2.5] == 6          # 4 páginas redistribuídas de volta para 2.5
    assert sum(a.values()) == 16


def test_orcamento_nao_sobe_para_buckets_de_4_niveis():
    """16 = 4x4: o mesmo teto agregado que negativas/positivas já tinham na
    v1.9.0 (4 páginas x 4 níveis) — o orçamento EQUALIZA, não infla."""
    a = orcamento_paginas_bucket(16, {n: 100 for n in POS_C}, POS_C,
                                 piso=1, teto_nivel=10)
    assert sum(a.values()) == 16


# --- redistribuição REAPROVEITA redistribuir_deficit — não é um mecanismo novo ---

def test_teto_de_seguranca_e_literalmente_redistribuir_deficit():
    """Reproduz manualmente o que orcamento_paginas_bucket faz por dentro:
    alocar (piso, sem teto) -> capar com redistribuir_deficit(disponivel=teto).
    Se os dois caminhos derem o MESMO resultado, é a prova de que não existe
    uma segunda fórmula de redistribuição."""
    from espectro24.alocacao import alocar_bucket

    base = alocar_bucket(16, HIST_MEDIANAS_CIDADE_DE_DEUS, MED_C, piso_nivel=1)
    manual = redistribuir_deficit(base, {n: 10 for n in MED_C})
    direto = orcamento_paginas_bucket(16, HIST_MEDIANAS_CIDADE_DE_DEUS, MED_C,
                                      piso=1, teto_nivel=10)
    assert manual == direto


# --- degenerados ---

def test_bucket_com_1_nivel_so():
    a = orcamento_paginas_bucket(16, {4.0: 500}, [4.0], piso=1, teto_nivel=10)
    assert a == {4.0: 10}                # capado pelo teto; sem sobra, ninguém pra receber
    assert sum(a.values()) <= 16


def test_bucket_com_nivel_sem_material_nenhum():
    a = orcamento_paginas_bucket(16, {0.5: 0, 1.0: 100, 1.5: 0, 2.0: 100}, NEG_C,
                                 piso=1, teto_nivel=10)
    assert a[0.5] == 0 and a[1.5] == 0
    assert sum(a.values()) == 16


def test_bucket_sem_material_nenhum_cai_para_uniforme():
    a = orcamento_paginas_bucket(16, {n: 0 for n in NEG_C}, NEG_C, piso=1, teto_nivel=10)
    assert sum(a.values()) == 16
    assert len(set(a.values())) <= 2     # o mais uniforme possível (maior resto)


def test_orcamento_zero():
    a = orcamento_paginas_bucket(0, HIST_NEGATIVAS_CURE, NEG_C, piso=1, teto_nivel=10)
    assert sum(a.values()) == 0


# --- simetria: o defeito morreu ---

@pytest.mark.parametrize("fronteiras", [FRONTEIRAS_C, FRONTEIRAS_V18])
def test_todo_bucket_recebe_o_MESMO_orcamento_agregado(fronteiras):
    """A prova de que o defeito morreu: o orçamento por bucket é 16 SEMPRE,
    não importa se o bucket tem 2 ou 4 níveis sob a fronteira em vigor."""
    hist = {n: 1000 for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)}
    orc = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16},
                            hist, fronteiras=fronteiras)
    somas = {nome: sum(v.values()) for nome, v in orc.items()}
    assert somas["negativas"] == somas["medianas"] == somas["positivas"] == 16


def test_orcamento_paginas_usa_as_fronteiras_recebidas():
    hist = {n: 1000 for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)}
    sob_c = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16},
                              hist, fronteiras=FRONTEIRAS_C)
    sob_v18 = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16},
                                hist, fronteiras=FRONTEIRAS_V18)
    assert set(sob_c["negativas"]) == {0.5, 1.0, 1.5, 2.0}
    assert set(sob_v18["negativas"]) == {0.5, 1.0, 1.5, 2.0, 2.5}   # prova de parâmetro


def test_orcamento_paginas_sem_histograma_cai_para_uniforme():
    orc = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16}, None)
    assert orc["medianas"] == {2.5: 8, 3.0: 8}
    assert sum(orc["negativas"].values()) == 16


def test_orcamento_paginas_e_deterministico():
    hist = {n: 1000 for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)}
    a = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16}, hist)
    b = orcamento_paginas({"negativas": 16, "medianas": 16, "positivas": 16}, hist)
    assert a == b
