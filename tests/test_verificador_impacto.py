"""Invariantes do passe de verificação de `impacto_emocional`.

O passe roda DEPOIS do consenso e só pode REMOVER marcações — é essa
assimetria que define o critério de sucesso (precisão sobe, recall só pode
cair) e ela precisa ser estrutural, não uma promessa da prosa do prompt.
Estes testes travam isso, mais o comportamento nas bordas de parsing (onde
a política é conservadora: na dúvida, não mexe na classificação original).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


@pytest.fixture(scope="module")
def vi():
    import verificador_impacto
    return verificador_impacto


# ------------------------------------------------------- parsing do veredito

@pytest.mark.parametrize("bruto,esperado", [
    (True, True), (False, False),
    ("true", True), ("false", False),
    ("False", False), ("nao", False), ("não", False), ("no", False), ("0", False),
    ("sim", True), ("yes", True),
])
def test_confirma_tolera_bool_e_string(vi, bruto, esperado):
    confirma, _, _ = vi._normalizar_veredito({"confirma": bruto})
    assert confirma is esperado


def test_confirma_ausente_e_conservador_nao_remove(vi):
    """Falha de parsing NÃO pode remover — um verificador que apaga marcação
    por JSON malformado seria pior que não ter verificador."""
    confirma, _, _ = vi._normalizar_veredito({"frase": "algo"})
    assert confirma is True


def test_frase_e_alvo_sao_extraidos(vi):
    _, frase, alvo = vi._normalizar_veredito(
        {"confirma": False, "frase": "  não gostei  ", "alvo": "Filme"})
    assert frase == "não gostei"
    assert alvo == "filme"


def test_alvo_ausente_vira_none(vi):
    """V1 não pede `alvo`; o campo é opcional por desenho."""
    _, _, alvo = vi._normalizar_veredito({"confirma": True})
    assert alvo is None


# ----------------------------------------------------------------- aplicar()

def _consenso(**por_id):
    return {rid: {"eixos": list(eixos), "confianca": "maioria"}
            for rid, eixos in por_id.items()}


def test_aplicar_so_remove_nunca_acrescenta(vi):
    base = _consenso(a=["ritmo"], b=["impacto_emocional", "ritmo"])
    # veredito manda "confirmar" em a (que nem tem o eixo) e remover em b
    saida = vi.aplicar(base, {"a": True, "b": False})
    assert saida["a"]["eixos"] == ["ritmo"]           # inalterada
    assert saida["b"]["eixos"] == ["ritmo"]           # só o eixo saiu


def test_aplicar_nao_toca_outros_eixos(vi):
    base = _consenso(a=["atuacao", "impacto_emocional", "som_trilha", "livre"])
    saida = vi.aplicar(base, {"a": False})
    assert saida["a"]["eixos"] == ["atuacao", "som_trilha", "livre"]


def test_aplicar_preserva_campos_do_consenso(vi):
    base = {"a": {"eixos": ["impacto_emocional"], "confianca": "unanime",
                  "votos": {"impacto_emocional": 3}}}
    saida = vi.aplicar(base, {"a": False})
    assert saida["a"]["confianca"] == "unanime"
    assert saida["a"]["votos"] == {"impacto_emocional": 3}


def test_review_sem_veredito_fica_intacta(vi):
    """Review que o passe não visitou (o eixo não estava marcado) não muda."""
    base = _consenso(a=["impacto_emocional"], b=["ritmo"])
    saida = vi.aplicar(base, {})            # nenhum veredito
    assert saida["a"]["eixos"] == ["impacto_emocional"]
    assert saida["b"]["eixos"] == ["ritmo"]


def test_confirmar_mantem_a_marcacao(vi):
    base = _consenso(a=["impacto_emocional"])
    assert vi.aplicar(base, {"a": True})["a"]["eixos"] == ["impacto_emocional"]


# ------------------------------------------------------- consenso de 3 votos

def test_consenso3_e_maioria_de_2_de_3(vi, monkeypatch):
    passes = {
        1: {"x": {"confirma": True}, "y": {"confirma": False}, "z": {"confirma": True}},
        2: {"x": {"confirma": True}, "y": {"confirma": True}, "z": {"confirma": False}},
        3: {"x": {"confirma": False}, "y": {"confirma": False}, "z": {"confirma": False}},
    }
    monkeypatch.setattr(vi, "_ler", lambda variante, n: passes[n])
    v = vi.vereditos("V2_alvo", "consenso3")
    assert v["x"] is True      # 2 de 3 confirmam
    assert v["y"] is False     # 2 de 3 removem
    assert v["z"] is False     # 1 de 3 confirma


def test_passe1_usa_so_a_primeira_passada(vi, monkeypatch):
    passes = {1: {"x": {"confirma": False}},
              2: {"x": {"confirma": True}},
              3: {"x": {"confirma": True}}}
    monkeypatch.setattr(vi, "_ler", lambda variante, n: passes[n])
    assert vi.vereditos("V2_alvo", "passe1")["x"] is False


# ------------------------------------------------------------------- prompts

@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_e_curto_e_sobre_uma_decisao(vi, nome):
    """O passe existe porque verificar é pergunta MAIS FÁCIL que classificar.
    Reapresentar a taxonomia recriaria a tarefa difícil."""
    p = vi.VARIANTES[nome]
    assert len(p) < 2000
    for eixo in ("roteiro_estrutura", "tom_atmosfera", "comparacoes",
                 "direcao_imagem", "som_trilha"):
        assert f"- {eixo}:" not in p       # nenhuma definição de eixo inteira


@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_trata_os_dois_polos(vi, nome):
    """A assimetria positivo/negativo foi o defeito original — o prompt do
    verificador tem de barrar veredicto nos DOIS polos."""
    p = vi.VARIANTES[nome]
    assert "não gostei" in p and "amei" in p


@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_pede_a_frase_justificadora(vi, nome):
    """Telemetria declarada: é o que permite auditar o verificador depois."""
    assert '"frase"' in vi.VARIANTES[nome]


def test_apenas_v2_pede_o_alvo(vi):
    """A diferença estrutural entre as variantes: V2 força o compromisso
    com o ALVO antes do veredito."""
    assert '"alvo"' not in vi.SYSTEM_V1_REGUA
    assert '"alvo"' in vi.SYSTEM_V2_ALVO


def test_o_eixo_verificado_e_apenas_impacto_emocional(vi):
    assert vi.EIXO == "impacto_emocional"
