#!/usr/bin/env python3
"""[v1.9.35, §0 terceira exceção] Gera as CONDIÇÕES DE DECISÃO sobre os
`resultado/*.json` já publicados.

**Isto NÃO é republicar o filme.** Nenhum estágio a montante roda: sem
coleta, sem seleção, sem síntese, sem [D3], sem veredito, sem narrativa, sem
TMDB, sem histograma. O harness lê o JSON que já está em disco, monta o
briefing (código puro), chama o LLM pelo adaptador, e escreve **uma única
chave**: `condicoes`.

**`--saida` é OBRIGATÓRIO, e a razão é de fase.** O §0 exige LEITURA HUMANA
DE 100% antes de publicar — é uma das três garantias que sustentam a
exceção. Um harness capaz de gravar em `resultado/` por default tornaria
trivial pular essa etapa, e a lição registrada na v1.9.21 é exatamente essa:
*"harness novo com 'cuidado diferente' é exatamente como se abre o próximo
footgun"*. Enquanto a fase de leitura estiver aberta, este script **não sabe**
escrever em `resultado/` — e recusa explicitamente se apontarem para lá.

Uso:
    python scripts/gerar_condicoes.py --todos --saida /tmp/cond/exec1
    python scripts/gerar_condicoes.py --slug the-godfather --saida /tmp/x
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24 import condicoes as C  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
CHAVE = "condicoes"


def slugs_publicados() -> list[str]:
    """Todo `resultado/<slug>.json` com tema em algum bucket extremo."""
    saida = []
    for caminho in sorted(RESULTADO_DIR.glob("*.json")):
        try:
            d = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        buckets = {b.get("bucket"): b for b in (d.get("buckets") or [])}
        if any((buckets.get(n) or {}).get("temas")
               for n in ("negativas", "positivas")):
            saida.append(caminho.stem)
    return saida


def _checar_saida(destino: Path) -> None:
    alvo = destino.resolve()
    proibido = RESULTADO_DIR.resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise SystemExit(
            f"RECUSADO: --saida aponta para dentro de {proibido}.\n"
            "O §0 exige leitura humana de 100% antes de publicar; este "
            "harness não escreve em resultado/ enquanto a fase de leitura "
            "estiver aberta.")


def gerar_um(slug: str, destino: Path, *, n: int, modelo: str | None) -> dict:
    origem = RESULTADO_DIR / f"{slug}.json"
    d = json.loads(origem.read_text(encoding="utf-8"))
    t0 = time.time()
    bloco = C.gerar(d, n=n, model=modelo)
    dt = time.time() - t0
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{slug}.json").write_text(
        json.dumps({"slug": slug, CHAVE: bloco}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return {"slug": slug, "bloco": bloco, "latencia_s": round(dt, 2)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--saida", required=True,
                    help="diretório de saída (NUNCA dentro de resultado/)")
    ap.add_argument("--n", type=int, default=None,
                    help="best-of-N (default: config.BEST_OF_N)")
    ap.add_argument("--modelo", default=None)
    args = ap.parse_args()

    destino = Path(args.saida)
    _checar_saida(destino)
    load_dotenv(RAIZ / ".env")

    from espectro24.config import BEST_OF_N
    n = args.n or BEST_OF_N

    slugs = slugs_publicados() if args.todos else (args.slug or [])
    if not slugs:
        raise SystemExit("nada a fazer: use --todos ou --slug")

    resumo = []
    for slug in slugs:
        r = gerar_um(slug, destino, n=n, modelo=args.modelo)
        b = r["bloco"] or {}
        nc = len(b.get("vale_a_pena", [])) + len(b.get("talvez_evite", []))
        ped = sum(len(v) for v in (b.get("temas_pedidos") or {}).values())
        print(f"{slug:40} pediu {ped:2}  publicou {nc:2}  "
              f"descartou {len(b.get('descartadas') or [])}  "
              f"{r['latencia_s']:5.1f}s", flush=True)
        resumo.append(r)
    (destino / "_resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(resumo)} filmes -> {destino}")


if __name__ == "__main__":
    main()
