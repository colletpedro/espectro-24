"""[2026-10-31] Fase 4, C5 (`fase4_especificidade.py`), com dados SINTÉTICOS.

- o sorteio tira 20 por bucket em cada lado, é reprodutível pela semente do
  pré-registro e insere 3 repetidos de cada lado a ≥ 40 posições;
- bucket fora por memória em qualquer lado sai dos dois;
- o critério usa só os distintos (rótulo da 1ª ocorrência), com Wilson."""
from __future__ import annotations

import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import fase4_especificidade as F  # noqa: E402


def _frame(lado: str, n_filmes: int = 10, por_bucket: int = 6) -> list[dict]:
    return [F._bullet(lado, f"f{k}", b, i, f"tema {lado} {k} {b} {i}", f"exemplo {i}")
            for k in range(n_filmes) for b in F.K.BUCKETS for i in range(por_bucket)]


def test_sorteio_estratificado_reprodutivel_e_repetidos():
    t, p = _frame("treinado"), _frame("publicado")
    seq = F.sortear(t, p, random.Random(F.SEMENTE))
    assert seq == F.sortear(t, p, random.Random(F.SEMENTE))
    distintos = [x for x in seq if not x.get("repete")]
    assert len(seq) == 126 and len(distintos) == 120
    for lado in F.LADOS:
        for b in F.K.BUCKETS:
            assert sum(1 for x in distintos if x["lado"] == lado and x["bucket"] == b) == 20
    itens = F.numerar(seq)
    rep = [i for i in itens if i["repete"]]
    assert sorted(i["lado"] for i in rep) == ["publicado"] * 3 + ["treinado"] * 3
    assert all(abs(int(i["id"][1:]) - int(i["repete_de"][1:])) >= F.DIST_MIN_REPETIDO for i in rep)
    assert itens[0]["tema_exibido"][0].isupper()


def test_fora_por_memoria_em_qualquer_lado():
    t = {("a", "positivas"): {"ok": True}, ("b", "negativas"): {"fora_por_memoria": True}}
    b = {("a", "positivas"): {"fora_por_memoria": True}, ("b", "negativas"): {"ok": True}}
    assert F.fora_por_memoria(t, b) == {("a", "positivas"), ("b", "negativas")}


def test_criterio_conta_so_os_distintos():
    itens = [{"id": f"F{k:03d}", "lado": lado, "bucket": "positivas", "repete": False}
             for k, lado in enumerate(["treinado"] * 10 + ["publicado"] * 10)]
    itens.append({"id": "F999", "lado": "treinado", "bucket": "positivas", "repete": True,
                  "repete_de": "F000"})
    rot = {i["id"]: 1 for i in itens}
    rot["F000"] = 0                                   # 1 E em 10 no treinado: 10%
    rot["F999"] = 1                                   # o repetido discorda: não conta no C5
    r = F.avaliar(itens, rot)
    assert r["por_lado"]["treinado"]["E"] == 1 and r["C5_passa"]
    assert r["consistencia_dono"]["iguais"] == 0
    lo, hi = r["por_lado"]["treinado"]["wilson95"]
    assert 0.0 < lo < 0.1 < hi < 0.5
