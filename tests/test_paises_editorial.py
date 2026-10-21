"""[rodada editorial, etapa 0] `ficha.paises` entra em `resultado/*.json`
como campo NOVO e é a ÚNICA mudança desses arquivos.

DIFF entre o commit anterior à rodada (`BASE`, o HEAD em que ela começou) e
a árvore de trabalho: tirando `ficha.paises`, cada `resultado/*.json` é
idêntico ao da base, e `paises` não existia na base. O valor é a lista de
códigos ISO 3166-1 de `production_countries`, na ordem do TMDB, sem nomes.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
BASE = "a3807be"     # HEAD em que a rodada editorial começou


def _git(*args: str) -> str | None:
    if shutil.which("git") is None:
        return None
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _sem_paises(doc: dict) -> dict:
    d = json.loads(json.dumps(doc))
    if isinstance(d.get("ficha"), dict):
        d["ficha"].pop("paises", None)
    return d


def test_diff_resultado_so_incluiu_ficha_paises():
    listagem = _git("ls-tree", "--name-only", f"{BASE}:resultado")
    if listagem is None:
        pytest.skip(f"git ou o commit {BASE} indisponível")
    na_base = {n for n in listagem.split() if n.endswith(".json")}
    na_arvore = {p.name for p in (RAIZ / "resultado").glob("*.json")}
    assert na_arvore == na_base, "arquivo de resultado/ criado ou apagado"

    com_paises = 0
    for nome in sorted(na_base):
        base = json.loads(_git("show", f"{BASE}:resultado/{nome}"))
        atual = json.loads((RAIZ / "resultado" / nome).read_text(encoding="utf-8"))
        assert "paises" not in (base.get("ficha") or {}), nome
        assert _sem_paises(atual) == base, f"{nome}: mudou algo além de ficha.paises"
        paises = (atual.get("ficha") or {}).get("paises")
        if paises is None:
            continue
        assert isinstance(paises, list), nome
        assert all(isinstance(p, str) and re.fullmatch(r"[A-Z]{2}", p)
                   for p in paises), (nome, paises)
        assert len(set(paises)) == len(paises), (nome, paises)
        com_paises += 1
    assert com_paises >= 99, com_paises


def test_paises_seguem_a_ordem_do_tmdb():
    """Onde o detalhe do TMDB está em cache, `paises` é exatamente a
    sequência de `production_countries` — mesma ordem, nada a mais."""
    cache = RAIZ / "dados" / "cache" / "_tmdb_detalhe"
    if not cache.exists():
        pytest.skip("cache do detalhe do TMDB ausente (dados/cache/ não é versionado)")
    conferidos = 0
    for p in sorted((RAIZ / "resultado").glob("*.json")):
        ficha = json.loads(p.read_text(encoding="utf-8")).get("ficha") or {}
        det = cache / f"{ficha.get('tmdb_id')}.json"
        if "paises" not in ficha or not det.exists():
            continue
        esperado = [c["iso_3166_1"] for c in
                    json.loads(det.read_text(encoding="utf-8"))["production_countries"]]
        assert ficha["paises"] == esperado, p.name
        conferidos += 1
    assert conferidos >= 1
