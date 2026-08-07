"""Telemetria MEDIDA da recoleta v1.9.1 (SPEC §3[B], §3[C2], §3[B'], §5.6).

Lê os JSONs de coleta e o `meta.json` do bruto persistido e imprime a tabela
que a v1.9.1 se obrigou a reportar: n final por bucket (esperado 40/40/40),
orçamento de páginas vs. gasto (por nível e por bucket), motivos de descarte
discriminados, janela temporal por bucket, requisições contra a média de 61
da v1.9.0.

Uso:
    python scripts/telemetria_v191.py [--out-dir resultado/v191-coleta]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from espectro24.bruto import carregar  # noqa: E402
from espectro24.buckets import FRONTEIRAS_C, mapa_de_niveis  # noqa: E402

FILMES = ["cure", "cidade-de-deus", "the-invite-2026"]
BUCKETS = ["negativas", "medianas", "positivas"]
MAPA = mapa_de_niveis(FRONTEIRAS_C)
MEDIA_REQ_V190 = 61


def _n(v: float) -> str:
    return f"{v:g}"


def relatorio(slug: str, out_dir: Path, dados_dir: Path) -> dict:
    out = json.loads((out_dir / f"{slug}.json").read_text(encoding="utf-8"))
    meta, brutas = carregar(slug, raiz=dados_dir)
    coleta = out.get("coleta") or {}

    print(f"\n{'=' * 78}\n{slug}\n{'=' * 78}")

    # --- requisições ---
    origens = out.get("origem_paginas") or {}
    rede = sum(1 for v in origens.values() if v == "network")
    cache = sum(1 for v in origens.values() if v == "cache")
    total_req = rede + cache
    print(f"\nREQUISIÇÕES (execução mais recente, incremental sobre o bruto "
          f"já persistido): {rede} de rede · {cache} de cache · {total_req} no total")
    print(f"  ordenação: {coleta.get('ordenacao_usada')} · "
          f"coletor v{coleta.get('versao_coletor')} · "
          f"{coleta.get('n_reviews_bruto')} reviews no bruto (acumulado)")
    delta = rede - MEDIA_REQ_V190
    print(f"  vs. média v1.9.0 ({MEDIA_REQ_V190}): {rede} de rede "
          f"({'+' if delta >= 0 else ''}{delta})")

    # --- orçamento de páginas: dado vs. gasto (§3[B], entrega 1) ---
    print("\nORÇAMENTO DE PÁGINAS — dado vs. gasto, por nível e por bucket (entrega 1)")
    orc_nivel = coleta.get("orcamento_paginas_por_nivel", {})
    pag_nivel = coleta.get("paginas_gastas_por_nivel", {})
    paradas = set(coleta.get("paradas_por_limite") or [])
    for nome in BUCKETS:
        niveis = [str(n) for n in MAPA[nome]]
        orc_b = sum(orc_nivel.get(n, 0) for n in niveis)
        gasto_b = sum(pag_nivel.get(n, 0) for n in niveis)
        print(f"  {nome:<10} orçamento={orc_b:>3}  gasto={gasto_b:>3}"
              f"  ({100*gasto_b/orc_b:.0f}% usado)" if orc_b else f"  {nome:<10} orçamento=0")
        for n in sorted(niveis, key=float):
            marca = " TETO" if n in paradas else ""
            print(f"      {_n(float(n)):>4}★  orçamento={orc_nivel.get(n, 0):>3}  "
                  f"gasto={pag_nivel.get(n, 0):>3}{marca}")

    # --- n final por bucket (esperado 40/40/40) ---
    print("\nN FINAL POR BUCKET (esperado 40/40/40)")
    for b in out["buckets"]:
        print(f"  {b['bucket']:<10} n={b['n_validas']:>3}/{b['alvo']:<3} "
              f"modo={b['modo']:<10} estado_piso={b['estado_piso']:<16} "
              f"déficit_redistribuído={b.get('deficit_redistribuido', 0)}")

    # --- motivos de descarte discriminados (entrega 2) ---
    print("\nMOTIVOS DE DESCARTE, discriminados por bucket (entrega 2)")
    for b in out["buckets"]:
        agregado = Counter()
        for lvl in b["niveis"]:
            for motivo, n in (lvl.get("motivos_descarte") or {}).items():
                agregado[motivo] += n
        n_brutas_bucket = sum(lvl["n_brutas"] for lvl in b["niveis"])
        soma_motivos = sum(agregado.values())
        ok = "✓" if soma_motivos == n_brutas_bucket - b["n_validas"] else "✗ DIVERGE"
        print(f"  {b['bucket']:<10} " + " · ".join(f"{k}={v}" for k, v in agregado.items())
              + f"   [soma={soma_motivos} vs. brutas-válidas="
              f"{n_brutas_bucket - b['n_validas']} {ok}]")

    # --- janela temporal por bucket (entrega 4) ---
    print("\nJANELA TEMPORAL POR BUCKET (min/max/p5/p50/p95 — entrega 4)")
    jt = (meta or {}).get("janela_temporal") or {}
    total_jt = jt.get("total")
    if total_jt:
        print(f"  {'total':<10} n={total_jt['n']:<5} min={total_jt['min']} "
              f"p5={total_jt['p5']} p50={total_jt['p50']} p95={total_jt['p95']} "
              f"max={total_jt['max']}")
    for nome, bloco in (jt.get("por_bucket") or {}).items():
        if bloco is None:
            print(f"  {nome:<10} (sem review com data)")
            continue
        print(f"  {nome:<10} n={bloco['n']:<5} min={bloco['min']} "
              f"p5={bloco['p5']} p50={bloco['p50']} p95={bloco['p95']} "
              f"max={bloco['max']}")

    return {"slug": slug, "rede": rede, "total_req": total_req,
           "n_por_bucket": {b["bucket"]: b["n_validas"] for b in out["buckets"]},
           "estado_por_bucket": {b["bucket"]: b["estado_piso"] for b in out["buckets"]}}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="resultado/v191-coleta")
    p.add_argument("--dados-dir", default="dados/bruto")
    p.add_argument("--filmes", nargs="*", default=FILMES)
    a = p.parse_args(argv)
    resumo = [relatorio(slug, Path(a.out_dir), Path(a.dados_dir)) for slug in a.filmes]

    print(f"\n{'=' * 78}\nRESUMO\n{'=' * 78}")
    print(f"{'filme':<18} {'req(rede)':>10} {'negativas':>10} {'medianas':>10} {'positivas':>10}")
    for r in resumo:
        n = r["n_por_bucket"]
        print(f"{r['slug']:<18} {r['rede']:>10} "
              f"{n.get('negativas', 0):>10} {n.get('medianas', 0):>10} "
              f"{n.get('positivas', 0):>10}")
    media = sum(r["rede"] for r in resumo) / len(resumo)
    print(f"\nmédia de requisições de rede: {media:.1f} (v1.9.0 media: {MEDIA_REQ_V190})")
    todos_40 = all(v == 40 for r in resumo for v in r["n_por_bucket"].values())
    print(f"todos os buckets em 40/40? {'SIM' if todos_40 else 'NÃO'}")


if __name__ == "__main__":
    main()
