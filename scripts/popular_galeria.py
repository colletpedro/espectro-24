#!/usr/bin/env python3
"""[v1.9.38] Backfill único: acrescenta `galeria_posters` à `ficha` dos 35
`resultado/*.json` já publicados — SEM reabrir a desambiguação de
`/search/movie` (docstring de `buscar_ficha`, §1.2: "Reconsultar o TMDB é
reabrir a desambiguação que já ocorreu").

Usa o `tmdb_id` JÁ RESOLVIDO e gravado em cada ficha, chamando só
`/movie/{id}` com o MESMO `include_image_language=pt,null` de sempre — o
mesmo dado que `buscar_ficha` já teria trazido se os 35 fossem buscados de
novo hoje, sem o risco de o `/search/movie` escolher um id diferente numa
segunda chamada.

Aplica o mesmo filtro de duração da lib (`duracao_compativel_com_longa`,
`ficha.py` — NÃO é guarda de identidade, ver a docstring da função) e grava
o resultado tanto em `resultado/{slug}.json` (fonte de verdade) quanto no
cache `dados/cache/_tmdb/*.json` (para que uma reexecução futura de
`buscar_ficha` veja a entrada como completa e não regaste rede à toa).

Uso:
    python scripts/popular_galeria.py                 # os 35
    python scripts/popular_galeria.py --slug talk-to-me-2022
    python scripts/popular_galeria.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.ficha import (  # noqa: E402
    TMDB_BASE,
    TMDB_IMAGE_LANGS,
    _cache_key,
    _galeria,
    duracao_compativel_com_longa,
)

RESULTADO = ROOT / "resultado"
CACHE_TMDB = ROOT / "dados" / "cache" / "_tmdb"


def _api_key() -> str:
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key
    for linha in (ROOT / ".env").read_text().splitlines():
        if linha.startswith("TMDB_API_KEY"):
            return linha.split("=", 1)[1].strip()
    raise SystemExit("TMDB_API_KEY não encontrada (nem no ambiente, nem em .env)")


def _catalogo() -> list[str]:
    with open(RESULTADO / "votacao-3" / "consenso.jsonl") as f:
        return sorted({json.loads(l)["slug"] for l in f if l.strip()})


def _cache_path_para(slug: str, d: dict) -> Path | None:
    """Acha o arquivo de cache correspondente a esta ficha pela mesma
    `_cache_key(titulo, ano)` que `buscar_ficha` usa — sem isso o cache
    ficaria desatualizado (`galeria_posters` ausente) e uma reexecução
    futura da ficha completa reabriria rede à toa achando-o incompleto."""
    ficha = d.get("ficha") or {}
    ano_fonte = ficha.get("ano_fonte")
    # o título usado na busca original é o do PRÓPRIO slug/ano — mesma
    # derivação de `titulo_ano_de_slug`, já que é essa chamada que
    # `publicar_catalogo`/`cli` fazem antes de bater no TMDB.
    import re as _re
    m = _re.match(r"^(.*)-(\d{4})$", slug)
    if m:
        titulo, ano = m.group(1).replace("-", " "), int(m.group(2))
    else:
        titulo, ano = slug.replace("-", " "), ficha.get("ano")
    chave = _cache_key(titulo, ano)
    p = CACHE_TMDB / f"{chave}.json"
    return p if p.exists() else None


def processar(slug: str, key: str, sess: requests.Session, *, dry_run: bool) -> dict:
    p = RESULTADO / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "status": "sem_resultado"}
    d = json.loads(p.read_text(encoding="utf-8"))
    ficha = d.get("ficha")
    if not ficha or not ficha.get("tmdb_id"):
        return {"slug": slug, "status": "sem_ficha_ou_tmdb_id"}

    tmdb_id = ficha["tmdb_id"]
    duracao_min = ficha.get("duracao_min")

    resp = sess.get(f"{TMDB_BASE}/movie/{tmdb_id}", params={
        "api_key": key, "language": "pt-BR",
        "append_to_response": "images",
        "include_image_language": TMDB_IMAGE_LANGS,
    })
    if resp.status_code != 200:
        return {"slug": slug, "status": f"http_{resp.status_code}"}
    detalhes = resp.json()
    imagens = detalhes.get("images") or {}

    galeria = _galeria(imagens, ficha.get("poster_path"))
    compativel = duracao_compativel_com_longa(duracao_min)
    if not compativel:
        galeria = []

    if not dry_run:
        ficha["galeria_posters"] = galeria
        d["ficha"] = ficha
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

        cache_p = _cache_path_para(slug, d)
        if cache_p:
            cached = json.loads(cache_p.read_text(encoding="utf-8"))
            cached["galeria_posters"] = galeria
            cache_p.write_text(json.dumps(cached, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    return {
        "slug": slug, "status": "ok", "tmdb_id": tmdb_id,
        "duracao_min": duracao_min, "duracao_compativel_com_longa": compativel,
        "n_galeria": len(galeria),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = _api_key()
    slugs = args.slug or _catalogo()
    sess = requests.Session()

    resultados = []
    excecoes = []
    for slug in slugs:
        r = processar(slug, key, sess, dry_run=args.dry_run)
        resultados.append(r)
        marca = "✓" if r["status"] == "ok" else "✗"
        if r["status"] == "ok" and not r["duracao_compativel_com_longa"]:
            excecoes.append(r)
            marca = "⚠"
        print(f"  [{marca}] {slug}: {r}")
        time.sleep(0.05)

    print(f"\n{sum(1 for r in resultados if r['status'] == 'ok')}/{len(resultados)} ok")
    if excecoes:
        print("\nEXCEÇÕES — duração fora do território de longa (galeria vazia; "
              "NÃO é confirmação de identidade, ver duracao_compativel_com_longa):")
        for r in excecoes:
            print(f"  - {r['slug']} (tmdb_id={r['tmdb_id']}, "
                  f"duracao_min={r['duracao_min']})")


if __name__ == "__main__":
    main()
