"""Regressões da migração do curta para o longa de Obsession."""
from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_amostra_preserva_bruto_antigo_mas_so_inclui_pagina_canonica():
    import classificar_10 as c10

    amostra = c10.montar_amostra()
    slugs = {f["slug"] for f in amostra["filmes"]}

    assert "obsession-2025" in slugs
    assert "obsession-2026" not in slugs


def test_consenso_nao_ressuscita_registro_fora_da_amostra(
        tmp_path, monkeypatch):
    import votacao_3 as v3

    atual = ("obsession-2025", "positivas", "review-longa")
    estendida = ("obsession-2025", "negativas", "review-extensao-producao")
    retirado = ("obsession-2026", "positivas", "review-curta")
    amostra = tmp_path / "amostra.json"
    amostra.write_text(json.dumps({
        "filmes": [{"slug": atual[0]}],
        "reviews": [{"slug": atual[0], "bucket": atual[1], "id": atual[2]}],
    }), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", amostra)

    tid = v3.taxonomia_id()
    arquivos = {}
    for passe in (1, 2, 3):
        caminho = tmp_path / f"passe_{passe}.jsonl"
        registros = []
        for slug, bucket, review_id in (atual, estendida, retirado):
            registros.append({
                "ok": True, "taxonomia_id": tid, "passe": passe,
                "slug": slug, "perfil": "popular", "bucket": bucket,
                "id": review_id, "nivel": 5.0, "n_chars": 200,
                "eixos": ["atuacao"], "eixos_invalidos": [],
            })
        caminho.write_text(
            "".join(json.dumps(r) + "\n" for r in registros),
            encoding="utf-8",
        )
        arquivos[passe] = caminho
    monkeypatch.setattr(v3, "ARQ_PASSE", arquivos)

    consenso = tmp_path / "consenso.jsonl"
    monkeypatch.setattr(v3, "ARQ_CONSENSO", consenso)
    monkeypatch.setattr(v3, "SAIDA", tmp_path)
    monkeypatch.setattr(v3, "RAIZ", tmp_path)

    v3.cmd_consenso()

    linhas = [json.loads(l) for l in consenso.read_text().splitlines()]
    assert {(r["slug"], r["id"]) for r in linhas} == {
        ("obsession-2025", "review-longa"),
        ("obsession-2025", "review-extensao-producao"),
    }
