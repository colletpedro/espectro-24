"""[2026-10-31] Fase 4, C6 (`fase4_leitura.py`), com dados SINTÉTICOS.

- os lados saem da semente do pré-registro, um sorteio por filme;
- o documento segue o bloco "1. Bullets da síntese" da leitura anterior, sem
  contagens nem nome de origem, e marca bucket fora por memória e bucket sem JSON;
- o veredito traduz A/B pelo mapa: o treinado precisa ser publicável em ≥ 4 de 5."""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import fase4_leitura as L  # noqa: E402

FILMES = ["anatomy-of-a-fall", "incendies", "mother-2017", "napoleon-2023", "the-substance"]


def test_lados_reprodutiveis():
    a = L.sortear_lados(FILMES, random.Random(L.SEMENTE))
    assert a == L.sortear_lados(list(reversed(FILMES)), random.Random(L.SEMENTE))
    assert set(a.values()) <= {"treinado", "publicado"} and list(a) == FILMES


def test_documento_no_formato_da_leitura_anterior(tmp_path):
    bucket = {"temas": [{"tema": "ritmo lento", "exemplo_parafraseado": "Muitos citam o ritmo.",
                         "mencoes_aproximadas": 9, "n_reviews_analisadas": 40}],
              "observacao_geral": "O grupo reclama do ritmo."}
    f = {"slug": "incendies", "titulo": "Incêndios",
         "treinado": {"negativas": bucket, "medianas": {"temas": []}, "positivas": None},
         "publicado": {"negativas": bucket, "medianas": bucket, "positivas": None}}
    txt = L.documento([f], {"incendies": "treinado"}, "abc", tmp_path / "r.csv")
    assert "## Filme 1 — Incêndios" in txt and "### 1. Bullets da síntese" in txt
    assert "- **ritmo lento** — Muitos citam o ritmo." in txt
    assert "_O grupo reclama do ritmo._" in txt
    assert "sem síntese" in txt and "fora da comparação" in txt
    assert "treinado" not in txt and "publicado" not in txt and "40" not in txt
    assert txt.rstrip().endswith("`abc`_")


def test_veredito_pelo_mapa():
    a_e = {f: ("treinado" if k % 2 == 0 else "publicado") for k, f in enumerate(FILMES)}
    # treinado é A nos filmes 1, 3, 5 e B nos 2, 4
    resp = [{"filme": "1", "publicaria": "A", "melhor": "A"},
            {"filme": "2", "publicaria": "B", "melhor": "empate"},
            {"filme": "3", "publicaria": "ambos", "melhor": "B"},
            {"filme": "4", "publicaria": "A", "melhor": "A"},
            {"filme": "5", "publicaria": "A", "melhor": "B"}]
    r = L.avaliar(a_e, FILMES, resp)
    assert r["treinado_publicavel"] == 4 and r["C6_passa"]
    assert r["por_filme"][3]["treinado_publicavel"] is False
    assert r["por_filme"][2]["melhor"] == "publicado"
    with pytest.raises(SystemExit):
        L.avaliar(a_e, FILMES, resp[:4])
