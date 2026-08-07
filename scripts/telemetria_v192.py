"""Telemetria MEDIDA da recoleta v1.9.2 (SPEC §3[B], §3[B'], §5.6).

Lê os JSONs de coleta e o `meta.json` do bruto persistido e imprime a tabela
que a v1.9.2 se obrigou a reportar: n final por bucket (esperado 40/40/40 —
incluindo `cidade-de-deus`, que ficou em 37/40 na v1.9.1), requisições
contra a v1.9.1, motivo de parada por nível (determinístico, entrega 1),
páginas profundas efetivamente alcançadas (entrega 2), distribuição de
`pagina_origem` da amostra selecionada (entrega 4, primária) e janela por
`data` para comparação (secundária, proxy contaminado).

Uso:
    python scripts/telemetria_v192.py [--out-dir resultado/v192-coleta]
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
MEDIA_REQ_V191 = 21   # execução incremental — ver ressalva no relatório


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
    print(f"\nREQUISIÇÕES (execução incremental sobre o bruto já persistido): "
          f"{rede} de rede · {cache} de cache · {rede + cache} no total")
    print(f"  ordenação: {coleta.get('ordenacao_usada')} · "
          f"coletor v{coleta.get('versao_coletor')} · "
          f"{coleta.get('n_reviews_bruto')} reviews no bruto (acumulado)")

    # --- motivo de parada DETERMINÍSTICO por nível (entrega 1) ---
    print("\nMOTIVO DE PARADA por nível — determinístico (entrega 1)")
    motivo_nivel = coleta.get("motivo_parada_por_nivel", {})
    orc_nivel = coleta.get("orcamento_paginas_por_nivel", {})
    pag_nivel = coleta.get("paginas_gastas_por_nivel", {})
    contagem_motivos = Counter(motivo_nivel.values())
    print(f"  distribuição: {dict(contagem_motivos)}")
    for nome in BUCKETS:
        niveis = sorted((str(n) for n in MAPA[nome]), key=float)
        orc_b = sum(orc_nivel.get(n, 0) for n in niveis)
        gasto_b = sum(pag_nivel.get(n, 0) for n in niveis)
        pct = f"{100*gasto_b/orc_b:.0f}%" if orc_b else "—"
        print(f"  {nome:<10} orçamento={orc_b:>3}  gasto={gasto_b:>3}  ({pct} usado)")
        for n in niveis:
            print(f"      {_n(float(n)):>4}★  orçamento={orc_nivel.get(n, 0):>3}  "
                  f"gasto={pag_nivel.get(n, 0):>3}  motivo={motivo_nivel.get(n, '?')}")

    # --- n final por bucket (esperado 40/40/40, incl. cidade-de-deus) ---
    print("\nN FINAL POR BUCKET (esperado 40/40/40 — cidade-de-deus ficou 37/40 na v1.9.1)")
    for b in out["buckets"]:
        print(f"  {b['bucket']:<10} n={b['n_validas']:>3}/{b['alvo']:<3} "
              f"modo={b['modo']:<10} estado_piso={b['estado_piso']:<16} "
              f"déficit_redistribuído={b.get('deficit_redistribuido', 0)}")

    # --- pagina_origem: instrumento temporal PRIMÁRIO (entrega 4) ---
    print("\nDISTRIBUIÇÃO DE pagina_origem — PRIMÁRIA (entrega 4)")
    for b in out["buckets"]:
        d = b.get("distribuicao_pagina_origem")
        if not d:
            print(f"  {b['bucket']:<10} (sem dado)")
            continue
        fp = d.get("fracao_profunda")
        fp_txt = f"{fp:.2f}" if fp is not None else "?"
        print(f"  {b['bucket']:<10} n={d['n']:<3} min={d['min']:<4} p5={d['p5']:<4} "
              f"p50={d['p50']:<4} p95={d['p95']:<4} max={d['max']:<4} "
              f"fracao_profunda={fp_txt}")

    # --- janela temporal por data: SECUNDÁRIA, proxy contaminado ---
    print("\nJANELA TEMPORAL por `data` — SECUNDÁRIA, proxy contaminado (v1.9.1)")
    jt = (meta or {}).get("janela_temporal") or {}
    total_jt = jt.get("total")
    if total_jt:
        print(f"  {'total':<10} n={total_jt['n']:<5} min={total_jt['min']} "
              f"p50={total_jt['p50']} max={total_jt['max']}")
    for nome, bloco in (jt.get("por_bucket") or {}).items():
        if bloco is None:
            print(f"  {nome:<10} (sem review com data)")
            continue
        print(f"  {nome:<10} n={bloco['n']:<5} min={bloco['min']} "
              f"p50={bloco['p50']} max={bloco['max']}")

    return {"slug": slug, "rede": rede,
           "n_por_bucket": {b["bucket"]: b["n_validas"] for b in out["buckets"]}}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="resultado/v192-coleta")
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
    print(f"\nmédia de requisições de rede: {media:.1f} "
          f"(v1.9.1 incremental: ~{MEDIA_REQ_V191})")
    todos_40 = all(v == 40 for r in resumo for v in r["n_por_bucket"].values())
    print(f"todos os buckets em 40/40 (incl. cidade-de-deus/medianas)? "
          f"{'SIM' if todos_40 else 'NÃO'}")


if __name__ == "__main__":
    main()
