"""[v1.9.4, Entrega 3] Recoleta SELETIVA sob a extensão por déficit — §3[B].

Recoleta só os filmes cujo bucket DOMINANTE ficou abaixo da cota na diagnose
da v1.9.3. `obsession-2026` fica DE FORA de propósito: o déficit dele é
escassez genuína de material (214 notas no total), mecanismo diferente — a
extensão não teria o que buscar.

A recoleta é INCREMENTAL: as páginas do orçamento base já estão no cache de
disco desde o lote da v1.9.3, então não geram requisição. O custo real medido
aqui é o das páginas de EXTENSÃO (e do completamento das truncadas que elas
trazem) — que é exatamente o número que interessa dimensionar.

Uso:
    python scripts/recoleta_v194.py           # roda e grava o relatório
    python scripts/recoleta_v194.py --antes   # só fotografa o estado atual
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import carregar  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.lote import rodar_lote  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

SAIDA = RAIZ / "resultado" / "v194-recoleta"
ARQ_ANTES = SAIDA / "antes.json"
ARQ_RELATORIO = SAIDA / "relatorio.json"

# Os 9 da diagnose (§3[H]) — `obsession-2026` deliberadamente ausente.
FILMES = [
    "wicked-2024", "avengers-endgame", "talk-to-me-2022", "aftersun",
    "pearl-2022", "parasite-2019", "wonka", "hereditary", "shutter-island",
]


def foto(slug: str) -> dict:
    """Estado do filme lido do BRUTO em disco, sem tocar a rede.

    `selecionar` com os parâmetros de produção — a mesma função que a análise
    usa, para que "antes" e "depois" sejam medidos com a mesma régua."""
    meta, todas = carregar(slug)
    hist = {float(k): v for k, v in (meta or {}).get("histograma_bruto", {}).items()}
    sel = selecionar(todas, hist)
    total = sum(hist.values()) or 1
    from espectro24.buckets import FRONTEIRAS
    shares = {nome: round(100 * sum(v for k, v in hist.items() if lo <= k <= hi) / total)
              for nome, (lo, hi) in FRONTEIRAS.items()}
    dominante = max(shares, key=shares.get)
    return {
        "slug": slug,
        "n_bruto": len(todas),
        "shares": shares,
        "bucket_dominante": dominante,
        "n_por_bucket": {nome: b.n_final for nome, b in sel.items()},
        "estado_piso": {nome: b.estado_piso for nome, b in sel.items()},
        "paginas_gastas_por_nivel": (meta or {}).get("paginas_gastas_por_nivel", {}),
        "extensao_por_bucket": (meta or {}).get("extensao_por_bucket"),
    }


def tirar_fotos() -> dict:
    return {slug: foto(slug) for slug in FILMES}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--antes", action="store_true",
                    help="só fotografa o estado atual, sem recoletar")
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.antes or not ARQ_ANTES.exists():
        antes = tirar_fotos()
        ARQ_ANTES.write_text(json.dumps(antes, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"→ {ARQ_ANTES.relative_to(RAIZ)}")
        for slug, f in antes.items():
            d = f["bucket_dominante"]
            print(f"  {slug:22s} dominante={d[:3]} "
                  f"{f['n_por_bucket']['negativas']:2d}/"
                  f"{f['n_por_bucket']['medianas']:2d}/"
                  f"{f['n_por_bucket']['positivas']:2d}")
        if args.antes:
            return
    antes = json.loads(ARQ_ANTES.read_text(encoding="utf-8"))

    # Um Fetcher por filme (mesmo padrão do CLI), guardado para ler os
    # contadores de rede/cache depois.
    fetchers: dict[str, Fetcher] = {}

    def fabrica(slug: str) -> Fetcher:
        f = Fetcher(cache_dir="resultado/cache")
        fetchers[slug] = f
        return f

    t0 = time.time()
    rel = rodar_lote(
        FILMES,
        dados_dir=str(RAIZ / "dados" / "bruto"),
        estado_path=SAIDA / "estado.json",
        fabrica_fetcher=fabrica,
        on_progress=lambda s, st, m: print(
            f"  [{st}] {s}" + (f" — {m}" if m else ""), flush=True),
    )
    dt = time.time() - t0

    depois = tirar_fotos()
    relatorio = {
        "filmes": FILMES,
        "segundos": round(dt, 1),
        "n_concluidos": rel.n_concluidos,
        "n_pulados": rel.n_pulados,
        "n_falhas": rel.n_falhas,
        "falhas": rel.falhas,
        "rede_por_filme": {s: {"network": f.n_network, "cache": f.n_cache}
                           for s, f in fetchers.items()},
        "antes": antes,
        "depois": depois,
    }
    ARQ_RELATORIO.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"\n→ {ARQ_RELATORIO.relative_to(RAIZ)}  ({dt:.0f}s)")


if __name__ == "__main__":
    main()
