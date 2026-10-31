"""[2026-10-31] Fase 1: a avaliação da validação (`especificidade_validacao avaliar`).

- a matriz de confusão classifica G quando o score ≥ limiar e deixa a
  acurácia balanceada indefinida num subconjunto sem uma das classes (o
  critério da diferença não pode passar sem as duas);
- o bootstrap reamostra FILMES, não itens, e conta as reamostras sem as duas
  classes em vez de inventar uma AUC para elas."""
from __future__ import annotations

import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import especificidade_validacao as V  # noqa: E402


def test_confusao_no_limiar_e_subconjunto_sem_E():
    c = V._confusao([0.9, 0.1, 0.5, 0.2], [1, 1, 0, 0], 0.5)
    assert (c["GG"], c["GE"], c["EG"], c["EE"]) == (1, 1, 1, 1)
    assert c["acuracia_balanceada"] == 0.5
    so_g = V._confusao([0.9, 0.1], [1, 1], 0.5)
    assert so_g["tnr"] is None and so_g["acuracia_balanceada"] is None


def test_bootstrap_reamostra_filmes_e_conta_os_sem_as_duas_classes():
    # um filme só com G e outro só com E: metade das reamostras não tem as duas classes
    score, y, filmes = [0.9, 0.8, 0.1], [1, 1, 0], ["a", "a", "b"]
    r = V.bootstrap_auc(score, y, filmes, random.Random(1), n=2000)
    assert r["filmes"] == 2
    assert r["validas"] + r["sem_as_duas_classes"] == 2000
    assert 800 < r["sem_as_duas_classes"] < 1200
    assert r["ic95"] == [1.0, 1.0]
