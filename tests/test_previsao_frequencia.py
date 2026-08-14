"""Preditor pareado de frequência — o mecanismo que substitui a nota escrita.

Contexto (`src/espectro24/previsao_frequencia.py`): ao promover `A_regra`,
a extrapolação de TETO sobre o prompt antigo errou a direção de
`expectativa` (previu 2,02× de alta, veio 0,75×). A razão PAREADA
recall/precisão entre os dois prompts acertou. Estes testes travam a
aritmética do preditor e o comportamento nas bordas, e reproduzem o caso
histórico contra os números reais em disco.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.previsao_frequencia import (  # noqa: E402
    acuracia_da_previsao,
    fator_pareado,
    prever_frequencias,
)


# ---------------------------------------------------------------- aritmética

def test_prompts_identicos_nao_mudam_nada():
    """Mesma precisão e mesmo recall → fator 1,0, seja qual for o valor."""
    fator, motivo = fator_pareado(0.9, 0.5, 0.9, 0.5)
    assert motivo is None
    assert fator == pytest.approx(1.0)


def test_recall_dobra_com_precisao_estavel_dobra_a_frequencia():
    fator, _ = fator_pareado(0.9, 0.4, 0.9, 0.8)
    assert fator == pytest.approx(2.0)


def test_precisao_cai_com_recall_estavel_aumenta_a_frequencia_observada():
    """Menos precisão = mais falso positivo = MAIS eixo observado.

    É contra-intuitivo e é o motivo de a precisão entrar na conta: um prompt
    que ganha recall perdendo precisão infla a frequência pelos dois lados.
    """
    fator, _ = fator_pareado(0.9, 0.5, 0.45, 0.5)
    assert fator == pytest.approx(2.0)


def test_ganho_de_recall_e_de_precisao_se_compensam():
    # recall ×1,5 e precisão ×1,5 → razão inalterada.
    fator, _ = fator_pareado(0.6, 0.4, 0.9, 0.6)
    assert fator == pytest.approx(1.0)


def test_reproduz_o_caso_expectativa_da_promocao():
    """Os números reais de `A_regra` vs baseline para `expectativa` —
    o eixo em que o preditor de teto errou a direção."""
    fator, _ = fator_pareado(precisao_antiga=0.750, recall_antigo=0.525,
                             precisao_nova=0.909, recall_novo=0.500)
    assert fator < 1.0            # prevê QUEDA (o real foi 0,75×)
    assert fator == pytest.approx(0.786, abs=0.01)


# -------------------------------------------------------------------- bordas

@pytest.mark.parametrize("kwargs", [
    {"precisao_antiga": None, "recall_antigo": 0.5, "precisao_nova": 0.9, "recall_novo": 0.5},
    {"precisao_antiga": 0.9, "recall_antigo": None, "precisao_nova": 0.9, "recall_novo": 0.5},
    {"precisao_antiga": 0.9, "recall_antigo": 0.5, "precisao_nova": None, "recall_novo": 0.5},
    {"precisao_antiga": 0.9, "recall_antigo": 0.5, "precisao_nova": 0.9, "recall_novo": None},
])
def test_medida_ausente_devolve_none_com_motivo(kwargs):
    fator, motivo = fator_pareado(**kwargs)
    assert fator is None
    assert "ausente" in motivo


def test_precisao_zero_e_indefinido_nao_zero():
    fator, motivo = fator_pareado(0.0, 0.5, 0.9, 0.5)
    assert fator is None and "precisão zero" in motivo
    fator, motivo = fator_pareado(0.9, 0.5, 0.0, 0.5)
    assert fator is None and "precisão zero" in motivo


def test_recall_antigo_zero_nao_tem_base_multiplicativa():
    """Eixo que não existia na saída antiga não tem fator — multiplicar
    uma frequência observada de 0 por qualquer coisa continua 0."""
    fator, motivo = fator_pareado(0.9, 0.0, 0.9, 0.5)
    assert fator is None
    assert "recall antigo zero" in motivo


def test_recall_novo_zero_e_definido_e_vale_zero():
    """O eixo sumir sob o prompt novo é previsão legítima, não indefinição."""
    fator, motivo = fator_pareado(0.9, 0.5, 0.9, 0.0)
    assert motivo is None
    assert fator == 0.0


# ------------------------------------------------------------ prever_frequencias

def test_prever_devolve_frequencia_absoluta_quando_recebe_a_observada():
    prev = prever_frequencias(
        {"ritmo": {"precisao": 0.9, "recall": 0.4}},
        {"ritmo": {"precisao": 0.9, "recall": 0.8}},
        {"ritmo": 0.30})
    p = prev["ritmo"]
    assert p.fator == pytest.approx(2.0)
    assert p.freq_prevista == pytest.approx(0.60)


def test_prever_sem_frequencia_observada_devolve_so_o_fator():
    prev = prever_frequencias(
        {"ritmo": {"precisao": 0.9, "recall": 0.4}},
        {"ritmo": {"precisao": 0.9, "recall": 0.8}})
    assert prev["ritmo"].fator == pytest.approx(2.0)
    assert prev["ritmo"].freq_prevista is None


def test_eixo_ausente_de_um_lado_aparece_no_resultado():
    """Taxonomia que ganhou ou perdeu eixo não pode sumir em silêncio."""
    prev = prever_frequencias(
        {"ritmo": {"precisao": 0.9, "recall": 0.5}},
        {"ritmo": {"precisao": 0.9, "recall": 0.5},
         "eixo_novo": {"precisao": 0.8, "recall": 0.5}})
    assert set(prev) == {"ritmo", "eixo_novo"}
    assert prev["eixo_novo"].fator is None
    assert "ausente" in prev["eixo_novo"].motivo_indefinido


# ----------------------------------------------------------- acuracia_da_previsao

def test_acuracia_conta_sinal_e_ordem_de_grandeza():
    prev = prever_frequencias(
        {"a": {"precisao": 0.9, "recall": 0.4}},   # fator previsto 2,0
        {"a": {"precisao": 0.9, "recall": 0.8}})
    ac = acuracia_da_previsao(prev, {"a": 1.9})
    assert ac["n_comparados"] == 1
    assert ac["acertos_de_sinal"] == 1
    assert ac["acertos_de_ordem_de_grandeza"] == 1


def test_faixa_morta_impede_contar_ruido_como_erro_de_sinal():
    """1,00 previsto contra 1,02 real é acerto ('estavel'), não erro."""
    prev = prever_frequencias(
        {"a": {"precisao": 0.9, "recall": 0.5}},
        {"a": {"precisao": 0.9, "recall": 0.5}})     # fator 1,0
    ac = acuracia_da_previsao(prev, {"a": 1.02})
    assert ac["acertos_de_sinal"] == 1


def test_erro_de_sinal_de_verdade_e_contado_como_erro():
    prev = prever_frequencias(
        {"a": {"precisao": 0.9, "recall": 0.4}},
        {"a": {"precisao": 0.9, "recall": 0.8}})     # prevê 2,0 (subiu)
    ac = acuracia_da_previsao(prev, {"a": 0.5})      # real caiu
    assert ac["acertos_de_sinal"] == 0
    assert ac["por_eixo"][0]["sinal_previsto"] == "subiu"
    assert ac["por_eixo"][0]["sinal_real"] == "caiu"


def test_eixo_sem_fator_nao_entra_na_contagem():
    prev = prever_frequencias(
        {"a": {"precisao": 0.9, "recall": 0.0}},     # indefinido
        {"a": {"precisao": 0.9, "recall": 0.5}})
    ac = acuracia_da_previsao(prev, {"a": 1.5})
    assert ac["n_comparados"] == 0
    assert ac["por_eixo"][0]["comparavel"] is False


# ------------------------------------------------------------------ histórico

ARQ_VARIANTES = RAIZ / "resultado" / "auditoria-acuracia" / "variantes" / "comparacao.json"
ARQ_PROMOCAO = RAIZ / "resultado" / "votacao-3" / "comparacao_a_regra.json"


@pytest.mark.skipif(not (ARQ_VARIANTES.exists() and ARQ_PROMOCAO.exists()),
                    reason="dados da promoção de A_regra ausentes")
def test_caso_historico_a_regra_acerta_ordem_de_grandeza_nos_10_eixos():
    """Trava o resultado que justificou promover este preditor a mecanismo.

    Números honestos, medidos por este módulo: **10 de 10** eixos dentro de
    25% do fator real, e **1 erro direcional de consequência**
    (`comparacoes`: previu 1,05×, veio 0,92×). Os dois movimentos grandes —
    `impacto_emocional` para cima e `expectativa` para baixo — foram
    acertados, e é justamente `expectativa` que a extrapolação de teto
    errava (previa 2,02× de ALTA).
    """
    v = json.loads(ARQ_VARIANTES.read_text(encoding="utf-8"))
    comp = json.loads(ARQ_PROMOCAO.read_text(encoding="utf-8"))
    antigas = {e: {"precisao": d["precisao"], "recall": d["recall"]}
               for e, d in v["baseline"]["por_eixo"].items()}
    novas = {e: {"precisao": d["precisao"], "recall": d["recall"]}
             for e, d in v["A_regra"]["por_eixo"].items()}
    real = {r["eixo"]: r["freq_nova"] / r["freq_antiga"]
            for r in comp["entrega2"]["frequencia_por_eixo"] if r["freq_antiga"]}

    ac = acuracia_da_previsao(prever_frequencias(antigas, novas), real)
    assert ac["n_comparados"] == 10
    assert ac["acertos_de_ordem_de_grandeza"] == 10

    por_eixo = {l["eixo"]: l for l in ac["por_eixo"] if l["comparavel"]}
    # os dois movimentos grandes, acertados
    assert por_eixo["impacto_emocional"]["sinal_previsto"] == "subiu"
    assert por_eixo["impacto_emocional"]["sinal_real"] == "subiu"
    assert por_eixo["expectativa"]["sinal_previsto"] == "caiu"
    assert por_eixo["expectativa"]["sinal_real"] == "caiu"
    # o único erro direcional de consequência
    assert por_eixo["comparacoes"]["acertou_sinal"] is False
