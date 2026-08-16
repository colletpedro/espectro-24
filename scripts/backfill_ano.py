"""[v1.9.12, §3[B']] Backfill do `ano_lancamento` no bruto já coletado.

Os 35 filmes do catálogo foram coletados ANTES de o ano virar dado do
superset, então nenhum tem `ano_lancamento` no `meta.json`. Sem ele, um
slug sem sufixo de ano (21 dos 35) só resolve a ficha COM REDE — e uma
execução offline perde o movimento 1 em silêncio (defeito medido em
`joker-folie-a-deux`, v1.9.11).

Custo: 1 requisição por filme SEM ano no slug, e ZERO para os que têm o ano
no nome ou já foram preenchidos. Cacheada, com o delay de educação (§2.1)
do `Fetcher` de sempre — o script não tem caminho de rede próprio.

Uso:
    python scripts/backfill_ano.py            # relata o que falta (0 rede)
    python scripts/backfill_ano.py --aplicar  # resolve e grava
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import atualizar_meta, carregar  # noqa: E402
from espectro24.config import DADOS_BRUTO_DIR  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.ficha import resolver_ano, titulo_ano_de_slug  # noqa: E402


def slugs(raiz: Path) -> list[str]:
    return sorted(p.name for p in raiz.iterdir()
                  if p.is_dir() and (p / "meta.json").exists())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aplicar", action="store_true",
                    help="resolve e GRAVA (sem a flag, só relata)")
    ap.add_argument("--dados-dir", default=DADOS_BRUTO_DIR)
    ap.add_argument("--cache-dir", default="resultado/cache")
    args = ap.parse_args()

    raiz = RAIZ / args.dados_dir
    todos = slugs(raiz)
    fetcher = Fetcher(cache_dir=args.cache_dir) if args.aplicar else None

    ja_tem, do_slug, precisa_rede, resolvidos, falhou = [], [], [], [], []
    t0 = time.time()
    for slug in todos:
        meta, _ = carregar(slug, raiz=raiz)
        meta = meta or {}
        if meta.get("ano_lancamento"):
            ja_tem.append(slug)
            continue
        _, ano_slug = titulo_ano_de_slug(slug)
        (do_slug if ano_slug else precisa_rede).append(slug)
        if not args.aplicar:
            continue
        ano, fonte = resolver_ano(fetcher, slug, meta_bruto=meta)
        if ano is None:
            falhou.append(slug)
            print(f"  {slug}: NÃO resolvido")
            continue
        atualizar_meta(slug, {"ano_lancamento": ano, "ano_fonte": fonte},
                       raiz=raiz)
        resolvidos.append((slug, ano, fonte))
        print(f"  {slug}: {ano} ({fonte})")

    print()
    print(f"filmes no bruto ............ {len(todos)}")
    print(f"  já tinham o ano .......... {len(ja_tem)}")
    print(f"  ano derivável do slug .... {len(do_slug)}  (0 requisições)")
    print(f"  precisam de rede ......... {len(precisa_rede)}")
    if args.aplicar:
        print(f"\nresolvidos ................. {len(resolvidos)}")
        print(f"não resolvidos ............. {len(falhou)}  {falhou}")
        print(f"requisições de REDE ........ {fetcher.n_network}")
        print(f"tempo ...................... {time.time() - t0:.1f}s")
    else:
        print("\n(relatório — rode com --aplicar para gravar)")


if __name__ == "__main__":
    main()
