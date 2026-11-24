#!/usr/bin/env python3
"""Conferência de identidade contra o TMDB dos filmes do C22 (gratuita; sem LLM, sem Letterboxd).

Repete o caminho de identidade do CLI (`cli.py`, bloco "ficha técnica via TMDB"): identidade do
Letterboxd persistida no `dados/bruto/<slug>/meta.json` -> `ficha.buscar_ficha(..., identidade=...)`, que
exige igualdade normalizada do título, o id vindo do Letterboxd e a segunda checagem de duração. Sem
prova, a ficha inteira é recusada. NÃO há dispensa (decisão do dono, 2026-11-24): filme com divergência
sai da publicação e vai para a lista `divergentes`.

Só lê UMA variável do `.env`: `TMDB_API_KEY` (as chaves pagas nunca entram no processo).

Uso:
    venv/bin/python scripts/conferir_tmdb_c22.py                      # os 35 do escopo do C22
    venv/bin/python scripts/conferir_tmdb_c22.py --slug perfect-blue  # um só
Saída: resultado/c22-publicacao/tmdb_conferencia.json (MEDIDO) e o cache em resultado/c22-publicacao/cache_tmdb.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import ficha as F  # noqa: E402

SAIDA = RAIZ / "resultado" / "c22-publicacao"
ARQ_SAIDA = SAIDA / "tmdb_conferencia.json"
CACHE = SAIDA / "cache_tmdb"
BRUTO = RAIZ / "dados" / "bruto"


def chave_do_env(nome: str = F.TMDB_ENV_KEY) -> str | None:
    """Lê SÓ `nome` do `.env` (ou do ambiente); nenhuma outra chave é carregada."""
    if os.environ.get(nome):
        return os.environ[nome]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith(f"{nome}="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def slugs_do_escopo() -> list[str]:
    """Os 35 do C22: `finetune/c22/escopo.json` (árvore irmã do finetune ou a branch `finetune`)."""
    irma = RAIZ.parent / "espectro-24-finetune" / "finetune" / "c22" / "escopo.json"
    if irma.exists():
        esc = json.loads(irma.read_text(encoding="utf-8"))
    else:
        esc = json.loads(subprocess.check_output(
            ["git", "-C", str(RAIZ), "show", "finetune:finetune/c22/escopo.json"], text=True))
    return [r["slug"] for r in esc["incluidos"]]


def conferir(slug: str, api_key: str, cache: Path = CACHE, session=None) -> dict:
    """Um filme. Estados: `validada` | `divergente` | `sem_identidade` | `ano_desconhecido` | `tmdb_indisponivel`."""
    meta = json.loads((BRUTO / slug / "meta.json").read_text(encoding="utf-8"))
    identidade = F.resolver_identidade(None, slug, meta_bruto=meta)
    base = {"slug": slug}
    if identidade is None:
        return {**base, "estado": "sem_identidade"}
    ano = identidade.get("ano")
    if ano is None:
        return {**base, "estado": "ano_desconhecido", "titulo_letterboxd": identidade.get("titulo"),
                "tmdb_id_letterboxd": identidade.get("tmdb_id_letterboxd")}
    ficha, aviso, descartada = F.buscar_ficha(
        identidade["titulo"], ano, cache_dir=cache, api_key=api_key, session=session,
        ano_fonte="letterboxd", identidade=identidade)
    r = {**base, "titulo_letterboxd": identidade["titulo"], "ano_letterboxd": ano,
         "tmdb_id_letterboxd": identidade.get("tmdb_id_letterboxd")}
    if descartada:
        return {**r, "estado": "divergente", "motivo": descartada.get("motivo"), "aviso": aviso,
                "detalhe": descartada}
    if ficha is None:
        return {**r, "estado": "tmdb_indisponivel", "aviso": aviso}
    ident = ficha.get("identidade") or {}
    return {**r, "estado": "validada", "tmdb_id": ficha.get("tmdb_id"), "ano_tmdb": ident.get("ano_tmdb"),
            "ano_divergente": bool(ident.get("ano_divergente")),
            "titulo_tmdb": ident.get("titulo_tmdb_correspondente"),
            "campo_titulo": ident.get("titulo_tmdb_campo")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", help="só estes (repetível)")
    ap.add_argument("--saida", type=Path, default=ARQ_SAIDA)
    a = ap.parse_args()
    key = chave_do_env()
    if not key:
        raise SystemExit(f"{F.TMDB_ENV_KEY} ausente (ambiente ou .env): nada foi consultado")
    slugs = a.slug or slugs_do_escopo()
    CACHE.mkdir(parents=True, exist_ok=True)
    linhas = [conferir(s, key) for s in slugs]
    contagem: dict[str, int] = {}
    for r in linhas:
        contagem[r["estado"]] = contagem.get(r["estado"], 0) + 1
    out = {"gerado_por": "scripts/conferir_tmdb_c22.py", "utc": datetime.now(timezone.utc).isoformat(),
           "custo_usd": 0.0, "contagem": contagem,
           "publicaveis": [r["slug"] for r in linhas if r["estado"] == "validada"],
           "divergentes": [r for r in linhas if r["estado"] != "validada"],
           "filmes": linhas}
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"contagem": contagem, "divergentes": [r["slug"] for r in out["divergentes"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
