"""Invariantes da variante `impacto_estrito` (hipótese da super-marcação).

A variante testa se a saturação de `impacto_emocional` (75,5% do corpus) é
artefato da DEFINIÇÃO do eixo. Para a medição significar isso, ela precisa
mexer SÓ na definição desse eixo — as regras que compraram o ganho de recall
de `A_regra` (3, 6) e as outras 9 definições têm de ficar intactas. Estes
testes travam exatamente isso.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


@pytest.fixture(scope="module")
def vie():
    import variante_impacto_estrito
    return variante_impacto_estrito


@pytest.fixture(scope="module")
def c10():
    import classificar_10
    return classificar_10


def test_variante_muda_exatamente_duas_linhas(vie):
    """Definição do eixo + exemplos da regra 2. Nada mais."""
    a = vie.SYSTEM_A_REGRA.splitlines()
    b = vie.SYSTEM_ESTRITO.splitlines()
    assert len(a) == len(b)
    difs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(difs) == 2
    assert a[difs[0]].startswith("- impacto_emocional:")
    assert a[difs[1]].startswith("2. ")


def test_as_outras_nove_definicoes_ficam_intactas(vie, c10):
    for eixo in c10.EIXOS:
        if eixo == "impacto_emocional":
            continue
        linha = next(l for l in vie.SYSTEM_A_REGRA.splitlines()
                     if l.startswith(f"- {eixo}:"))
        assert linha in vie.SYSTEM_ESTRITO


@pytest.mark.parametrize("n", [1, 3, 4, 5, 6, 7])
def test_regras_que_compraram_o_recall_ficam_intactas(vie, n):
    """Só a regra 2 muda; 3 (`livre` por ASSUNTO) e 6 (`review curta
    menciona POUCOS eixos`) são as do ganho de recall e não podem mudar."""
    linha = next(l for l in vie.SYSTEM_A_REGRA.splitlines()
                 if l.startswith(f"{n}. "))
    assert linha in vie.SYSTEM_ESTRITO


def test_a_regra_e_o_system_de_producao(vie, c10):
    """A base da variante é o prompt vivo, não uma cópia que pode divergir."""
    assert vie.SYSTEM_A_REGRA == c10.SYSTEM


def test_definicao_nova_barra_veredicto_nos_dois_polos(vie):
    linha = next(l for l in vie.SYSTEM_ESTRITO.splitlines()
                 if l.startswith("- impacto_emocional:"))
    assert "não gostei" in linha and "amei" in linha
    assert "polo positivo quanto no negativo" in linha


def test_regra2_nova_move_veredicto_seco_para_o_lado_de_fora(vie):
    """`não gostei`/`odiei` saem da lista de impacto_emocional e entram na
    de 'avaliação sem eixo' — senão o prompt se contradiz com a definição."""
    r2 = next(l for l in vie.SYSTEM_ESTRITO.splitlines() if l.startswith("2. "))
    fora, dentro = r2.split("Mas um efeito DECLARADO")
    assert '"não gostei"' in fora and '"odiei"' in fora
    assert '"não gostei"' not in dentro and '"odiei"' not in dentro
    # e os efeitos de verdade continuam do lado de dentro
    assert '"chorei"' in dentro and '"passei mal"' in dentro


def test_montar_falha_alto_se_o_prompt_de_producao_mudar(vie, monkeypatch):
    """Se um dos trechos deixar de casar, a variante mediria outra coisa —
    tem de abortar, não seguir em silêncio."""
    monkeypatch.setattr(vie, "SYSTEM_A_REGRA", "prompt completamente outro")
    with pytest.raises(SystemExit, match="variante desatualizada"):
        vie._montar_variante()
