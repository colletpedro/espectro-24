"""[§3[B'], v1.9.13] `coletado_em` só avança quando a execução tocou a rede.

Achado ao regenerar 4 filmes da v1.9.12 `--offline`: o campo avançou ~5h
mesmo com ZERO requisições — `coletar_superset` sempre carimbava "agora",
independente de ter tocado a rede. Segundo sintoma da mesma raiz de
"Reprodutibilidade offline" (§3[B']): `meta.json` não separava O QUE A
COLETA FEZ de QUANDO ALGUÉM RODOU O PIPELINE.

Corrige só o sintoma imediato (contido); a correção estrutural (posições
gravadas) segue diagnosticada, não implementada.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.collector import _coletado_em  # noqa: E402


class _FetcherComContagem:
    def __init__(self, n_network: int):
        self.n_network = n_network


def test_execucao_sem_rede_preserva_o_carimbo_anterior():
    anterior = {"coletado_em": "2026-08-15T21:33:18+00:00"}
    resultado = _coletado_em(anterior, _FetcherComContagem(0), "2026-08-16T02:11:06+00:00")
    assert resultado == "2026-08-15T21:33:18+00:00"


def test_execucao_com_rede_avanca_o_carimbo():
    anterior = {"coletado_em": "2026-08-15T21:33:18+00:00"}
    resultado = _coletado_em(anterior, _FetcherComContagem(3), "2026-08-16T02:11:06+00:00")
    assert resultado == "2026-08-16T02:11:06+00:00"


def test_primeira_coleta_sem_meta_anterior_usa_agora_mesmo_sem_rede():
    """Filme nunca coletado: não há carimbo anterior para preservar — usa
    o momento da execução, mesmo que ela (improvavelmente) não tenha
    tocado a rede."""
    resultado = _coletado_em(None, _FetcherComContagem(0), "2026-08-16T02:11:06+00:00")
    assert resultado == "2026-08-16T02:11:06+00:00"


def test_meta_anterior_sem_o_campo_nao_quebra():
    """Bruto de uma versão anterior a esta correção pode não ter
    `coletado_em` registrado da forma esperada — degrada para 'agora' em
    vez de estourar."""
    resultado = _coletado_em({"slug": "cure"}, _FetcherComContagem(0),
                             "2026-08-16T02:11:06+00:00")
    assert resultado == "2026-08-16T02:11:06+00:00"


def test_fetcher_sem_atributo_n_network_nao_quebra():
    """Dublê de teste sem `n_network` — trata como se tivesse tocado a
    rede (mais conservador: prefere avançar a arriscar carimbo preso)."""
    class _SemContagem:
        pass
    resultado = _coletado_em({"coletado_em": "X"}, _SemContagem(), "AGORA")
    assert resultado == "AGORA"
