"""[2026-09-23] A medida de citação literal sem aspas (lacuna da regra 2)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import conferir_citacao_literal as C  # noqa: E402


def test_normaliza_acento_caixa_e_pontuacao():
    assert C.tokens("Família, CLASSE média-alta!") == ["familia", "classe",
                                                       "media", "alta"]


def test_maior_sequencia_continua():
    a = C.tokens("o filme se arrasta demais em cenas longas")
    b = C.tokens("Achei que o filme se arrasta demais, sério")
    assert C.maior_sequencia(a, b) == (5, 0)
    assert C.maior_sequencia(C.tokens("nada em comum"), C.tokens("zero")) == (0, 0)


def test_palavras_iguais_fora_de_ordem_nao_contam_como_sequencia():
    n, _ = C.maior_sequencia(C.tokens("ritmo lento e arrastado"),
                             C.tokens("arrastado e lento ritmo"))
    assert n == 1
