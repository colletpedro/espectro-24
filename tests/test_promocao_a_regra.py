"""Trava a promoção de A_regra a `classificar_10.SYSTEM` (sessão 2026-08-13).

A auditoria achou recall 0,35 em review ≤200 chars; a variante A_regra
corrigiu isso mexendo SÓ no bloco REGRAS (ver docstring de
`classificar_10.py` e `TAXONOMIA_10.md`, seção "Correção de recall em review
curta"). Estes testes travam que a promoção fez exatamente isso — regras
novas, cabeçalho (eixos) intocado — e que o `taxonomia_id` resultante é o
mesmo que a auditoria previu antes de qualquer chamada de LLM.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

# O id previsto pela Entrega 2 da tarefa de variantes, ANTES de qualquer
# reclassificação — hash de SYSTEM_A + EIXOS, calculado e conferido na sessão
# que promoveu A_regra. Se este teste começar a falhar, ou a promoção foi
# desfeita, ou REGRAS/EIXOS mudaram de novo sem atualizar a expectativa.
TAXONOMIA_ID_A_REGRA = "ebab2667de74"
TAXONOMIA_ID_ANTIGA = "11871105c0d3"


@pytest.fixture(scope="module")
def c10():
    import classificar_10
    return classificar_10


@pytest.fixture(scope="module")
def vp():
    import variantes_prompt_curtas
    return variantes_prompt_curtas


def test_producao_e_a_regra_byte_a_byte(c10, vp):
    """`classificar_10.SYSTEM` é EXATAMENTE `SYSTEM_A` da variante vencedora."""
    assert c10.SYSTEM == vp.SYSTEM_A


def test_taxonomia_id_e_o_previsto_pela_auditoria(c10):
    id_atual = c10.taxonomia_id()
    assert id_atual == TAXONOMIA_ID_A_REGRA
    assert id_atual != TAXONOMIA_ID_ANTIGA


def test_cabecalho_de_eixos_nao_mudou(c10, vp):
    """Só REGRAS mudou — preâmbulo + definições dos 10 eixos, intocados."""
    cabecalho_novo = c10.SYSTEM.split("REGRAS:")[0]
    cabecalho_antigo = vp.SYSTEM_BASELINE.split("REGRAS:")[0]
    assert cabecalho_novo == cabecalho_antigo


def test_regras_de_producao_sao_diferentes_das_antigas(c10, vp):
    """A promoção teve efeito real: as REGRAS mudaram."""
    regras_novas = c10.SYSTEM.split("REGRAS:")[1]
    regras_antigas = vp.SYSTEM_BASELINE.split("REGRAS:")[1]
    assert regras_novas != regras_antigas


def test_lista_de_eixos_nao_mudou(c10):
    assert c10.EIXOS == (
        "ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura",
        "som_trilha", "tom_atmosfera", "impacto_emocional", "comparacoes",
        "expectativa", "critica_social",
    )


def test_regras_de_producao_atacam_o_defeito_medido(c10):
    """As três mudanças que a auditoria motivou estão de fato em produção —
    mesma checagem que valida a variante, agora sobre o SYSTEM real."""
    r = c10.SYSTEM
    assert "Brevidade não é ausência" in r
    assert "ASSUNTO" in r
    assert "elogio sem eixo" in r


def test_variantes_prompt_curtas_fica_congelado_e_nao_referencia_producao(vp):
    """O módulo arquivado não deve mais importar SYSTEM ao vivo de
    `classificar_10` — senão 'baseline' colapsaria sobre produção a cada
    mudança futura de prompt, e o registro do experimento deixaria de valer
    algo (ver nota no topo de `variantes_prompt_curtas.py`)."""
    fonte = (RAIZ / "scripts" / "variantes_prompt_curtas.py").read_text(
        encoding="utf-8")
    assert "SYSTEM as SYSTEM_BASELINE" not in fonte
    assert 'SYSTEM_BASELINE = """' in fonte
