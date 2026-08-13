"""Invariantes das variantes de prompt da correção de recall em review curta.

A correção mexe SÓ no bloco REGRAS. Estes testes travam isso: se uma sessão
futura mexer na lista de eixos ou na definição de um eixo por dentro de uma
variante, o A/B deixa de medir o que diz medir (a mudança de regra) e passa a
medir uma taxonomia diferente — e o resultado da Entrega 3 vira incomparável
com o baseline.

Travam também a higiene do few-shot: nenhum exemplo pode sair das 100
auditadas, que são o conjunto de teste.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


@pytest.fixture(scope="module")
def vp():
    import variantes_prompt_curtas
    return variantes_prompt_curtas


@pytest.fixture(scope="module")
def base():
    import classificar_10
    return classificar_10


@pytest.mark.parametrize("nome", ["A_regra", "B_fewshot"])
def test_variante_preserva_o_cabecalho_do_baseline(vp, nome):
    """Preâmbulo + definições dos 10 eixos, byte a byte iguais ao de produção."""
    cabecalho = vp.SYSTEM_BASELINE.split("REGRAS:")[0]
    assert vp.VARIANTES[nome].startswith(cabecalho)


@pytest.mark.parametrize("nome", ["A_regra", "B_fewshot"])
def test_variante_nao_mexe_na_lista_de_eixos(vp, base, nome):
    """Os 10 eixos aparecem, e nenhum eixo novo é inventado."""
    system = vp.VARIANTES[nome]
    for eixo in base.EIXOS:
        assert f"- {eixo}:" in system, f"{eixo} sumiu da variante {nome}"
    # A definição de cada eixo é a linha do baseline, inalterada.
    for linha in vp.SYSTEM_BASELINE.splitlines():
        if linha.startswith("- ") and ":" in linha:
            assert linha in system


@pytest.mark.parametrize("nome", ["A_regra", "B_fewshot"])
def test_variante_termina_no_mesmo_contrato_de_saida(vp, nome):
    """O formato JSON pedido é o mesmo — senão `_normalizar` não casa."""
    assert vp.VARIANTES[nome].rstrip().endswith(
        '{"eixos": ["..."], "temas_livres": ["..."]}')


def test_as_duas_variantes_diferem_apenas_pelo_fewshot(vp):
    """A e B compartilham as MESMAS regras; B só acrescenta exemplos.

    É o que torna o A/B interpretável: a diferença medida entre as duas é
    atribuível ao few-shot, e a nada mais.
    """
    assert vp._REGRAS_NOVAS in vp.SYSTEM_A
    assert vp._REGRAS_NOVAS in vp.SYSTEM_B
    assert vp.SYSTEM_B == vp.SYSTEM_A.replace(
        vp._FORMATO, vp._FEWSHOT + vp._FORMATO)


def test_apenas_B_tem_fewshot(vp):
    assert "EXEMPLOS RESOLVIDOS" not in vp.SYSTEM_A
    assert "EXEMPLOS RESOLVIDOS" in vp.SYSTEM_B


def test_regras_novas_atacam_o_defeito_medido(vp):
    """As três mudanças que a auditoria motivou estão de fato no texto."""
    r = vp._REGRAS_NOVAS
    assert "Brevidade não é ausência" in r      # omissão em texto curto
    assert "ASSUNTO" in r                       # `livre` por assunto
    assert "elogio sem eixo" in r               # precisão preservada


def test_fewshot_vem_de_fora_das_100_auditadas(vp):
    """O guard-rail que já pegou dois exemplos contaminados na escrita."""
    vp._conferir_fewshot_fora_da_auditoria()


def test_consenso_da_variante_usa_a_regra_de_2_de_3(vp, monkeypatch):
    """Mesma regra de `votacao_3._consensuar`, e a confiança derivada dela."""
    # passe -> {id: eixos}. Três reviews, uma por caso de confiança.
    passes = {
        1: {"r_unanime": ["ritmo"], "r_maioria": ["ritmo"], "r_vazio": ["ritmo"]},
        2: {"r_unanime": ["ritmo"], "r_maioria": ["ritmo"], "r_vazio": ["atuacao"]},
        3: {"r_unanime": ["ritmo"], "r_maioria": ["atuacao"], "r_vazio": ["som_trilha"]},
    }
    monkeypatch.setattr(vp, "_ler_passe", lambda variante, n: passes[n])
    g = vp.consenso_da_variante("A_regra")

    assert g["r_unanime"]["eixos"] == ["ritmo"]
    assert g["r_unanime"]["confianca"] == "unanime"

    # ritmo 2/3 entra; atuacao 1/3 fica de fora.
    assert g["r_maioria"]["eixos"] == ["ritmo"]
    assert g["r_maioria"]["confianca"] == "maioria"

    # três eixos distintos, nenhum alcança 2 votos.
    assert g["r_vazio"]["eixos"] == []
    assert g["r_vazio"]["confianca"] == "vazio"


def test_consenso_exige_as_tres_passadas(vp, monkeypatch):
    """Review que falhou numa passada fica FORA — não se vota com voto
    faltando (mesma decisão de `votacao_3._consensuar`)."""
    passes = {
        1: {"completa": ["ritmo"], "faltando": ["ritmo"]},
        2: {"completa": ["ritmo"], "faltando": ["ritmo"]},
        3: {"completa": ["ritmo"]},
    }
    monkeypatch.setattr(vp, "_ler_passe", lambda variante, n: passes[n])
    g = vp.consenso_da_variante("A_regra")
    assert set(g) == {"completa"}


def test_micro_soma_tp_fp_fn_antes_de_dividir(vp):
    """Micro, não macro: eixo raro não pesa igual a eixo frequente."""
    bloco = {"a": {"tp": 9, "fp": 1, "fn": 0}, "b": {"tp": 0, "fp": 0, "fn": 1}}
    m = vp._micro(bloco)
    assert (m["tp"], m["fp"], m["fn"]) == (9, 1, 1)
    assert m["precisao"] == pytest.approx(0.9)
    assert m["recall"] == pytest.approx(0.9)


def test_micro_devolve_none_em_denominador_zero(vp):
    m = vp._micro({"a": {"tp": 0, "fp": 0, "fn": 0}})
    assert m["precisao"] is None and m["recall"] is None
