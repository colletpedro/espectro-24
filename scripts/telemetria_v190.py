"""Telemetria MEDIDA da recoleta v1.9.0 (SPEC §2.2, §3[B], §3[C1], §3[C3]).

Lê os JSONs de coleta e o `meta.json` do bruto persistido e imprime a tabela
que a v1.9.0 se obrigou a reportar. Nenhum número aqui é estimado: tudo sai
de um arquivo produzido por uma execução real.

Uso:
    python scripts/telemetria_v190.py [--out-dir resultado/v190-coleta]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from espectro24.bruto import carregar  # noqa: E402
from espectro24.buckets import (  # noqa: E402
    FRONTEIRAS_C,
    FRONTEIRAS_V18,
    NIVEIS,
    shares_por_bucket,
)

FILMES = ["cure", "cidade-de-deus", "the-invite-2026"]
BUCKETS = ["negativas", "medianas", "positivas"]


def _n(v: float) -> str:
    return f"{v:g}"


def relatorio(slug: str, out_dir: Path, dados_dir: Path) -> None:
    out = json.loads((out_dir / f"{slug}.json").read_text(encoding="utf-8"))
    meta, brutas = carregar(slug, raiz=dados_dir)
    coleta = out.get("coleta") or {}

    print(f"\n{'=' * 78}\n{slug}\n{'=' * 78}")

    # --- requisições e páginas ---
    origens = out.get("origem_paginas") or {}
    rede = sum(1 for v in origens.values() if v == "network")
    cache = sum(1 for v in origens.values() if v == "cache")
    pag = coleta.get("paginas_gastas_por_nivel", {})
    print(f"\nREQUISIÇÕES: {rede} de rede · {cache} de cache · "
          f"{rede + cache} chaves no total")
    print(f"  ordenação: {coleta.get('ordenacao_usada')} · "
          f"coletor v{coleta.get('versao_coletor')} · "
          f"{coleta.get('n_reviews_bruto')} reviews no bruto")

    print("\nPOR NÍVEL — páginas, bruta persistida, válida heurística, parada")
    print(f"  {'nível':>6} {'pág':>4} {'bruta':>6} {'válida(h)':>10} {'parada':>9}")
    paradas = set(coleta.get("paradas_por_limite") or [])
    bruta_n = coleta.get("contagem_bruta_por_nivel", {})
    val_n = coleta.get("contagem_estimada_valida_por_nivel", {})
    for nv in NIVEIS:
        k = str(nv)
        marca = "TETO" if k in paradas else ""
        print(f"  {_n(nv):>6} {pag.get(k, 0):>4} {bruta_n.get(k, 0):>6} "
              f"{val_n.get(k, 0):>10} {marca:>9}")
    print(f"  {'TOTAL':>6} {sum(pag.values()):>4} {sum(bruta_n.values()):>6} "
          f"{sum(val_n.values()):>10}")
    if paradas:
        print(f"  níveis que pararam por TETO: {sorted(paradas, key=float)}")
    else:
        print("  níveis que pararam por TETO: nenhum")

    # --- composição alvo vs atingida ---
    print("\nCOMPOSIÇÃO — alvo vs. atingida (§3[C1], ressalva 2)")
    for b in out["buckets"]:
        alvo = b.get("composicao_alvo") or {}
        ating = b.get("composicao_atingida") or {}
        niveis = sorted(alvo, key=float)
        print(f"  {b['bucket']:<10} n={b['n_validas']:>3}/{b['alvo']:<3} "
              f"modo={b['modo']:<10} estado_piso={b['estado_piso']}")
        print("             nível : " + " ".join(f"{_n(float(n)):>5}" for n in niveis))
        print("             alvo  : " + " ".join(f"{alvo[n]:>5}" for n in niveis))
        print("             ating.: " + " ".join(f"{ating.get(n, 0):>5}" for n in niveis))
        deficit = b.get("deficit_redistribuido", 0)
        print(f"             déficit redistribuído: {deficit} · "
              f"cascata por degrau: {b.get('cascata_por_degrau')}")

    # --- bruta persistida vs válida pós-filtro ---
    print("\nBRUTA PERSISTIDA vs. VÁLIDA PÓS-FILTRO")
    total_bruto = len(brutas)
    completas = sum(1 for r in brutas if r.texto_completo)
    spoilers = sum(1 for r in brutas if r.spoiler_flag)
    curtas = sum(1 for r in brutas if r.n_chars < 150)
    selecionadas = sum(b["n_validas"] for b in out["buckets"])
    print(f"  persistidas no bruto ............ {total_bruto}")
    print(f"    com texto completo ............ {completas}")
    print(f"    marcadas spoiler .............. {spoilers}")
    print(f"    abaixo de 150 chars ........... {curtas}")
    print(f"  selecionadas para análise ....... {selecionadas} "
          f"({100 * selecionadas / total_bruto:.1f}% do bruto)")

    # --- janela temporal da amostra (evidência da ordenação, §2.3) ---
    datas = sorted((r.data or "")[:10] for r in brutas if r.data)
    if datas:
        from collections import Counter
        meses = Counter(d[:7] for d in datas)
        top2 = meses.most_common(2)
        concentracao = sum(v for _, v in top2) / len(datas)
        print("\nJANELA TEMPORAL DA AMOSTRA (§2.3 — consequência da ordenação)")
        print(f"  extremos ....................... {datas[0]} → {datas[-1]}")
        print(f"  2 meses mais densos ............ "
              f"{', '.join(f'{m} ({v})' for m, v in top2)}")
        print(f"  concentração nesses 2 meses .... {100 * concentracao:.0f}% "
              f"das {len(datas)} reviews com data")
        print("  ATENÇÃO: `data` é a data ASSISTIDA (diário), não a de publicação "
              "da review;\n           os extremos antigos são reviews recentes "
              "sobre sessões antigas.")

    # --- shares sob as duas fronteiras ---
    hist = {float(k): v for k, v in (coleta.get("histograma_bruto") or {}).items()}
    if hist:
        velho = shares_por_bucket(hist, FRONTEIRAS_V18)
        novo = shares_por_bucket(hist, FRONTEIRAS_C)
        print("\nSHARES DO HISTOGRAMA — fronteiras antigas vs. opção C (§2.2)")
        print(f"  {'bucket':<12} {'antigas':>8} {'novas C':>8} {'Δ':>6}")
        for nome in BUCKETS:
            d = novo[nome] - velho[nome]
            print(f"  {nome:<12} {velho[nome]:>7}% {novo[nome]:>7}% {d:>+5}pp")
        print(f"  (soma antiga {sum(velho.values())} · soma nova "
              f"{sum(novo.values())} — arredondamento independente, §3[G])")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="resultado/v190-coleta")
    p.add_argument("--dados-dir", default="dados/bruto")
    p.add_argument("--filmes", nargs="*", default=FILMES)
    a = p.parse_args(argv)
    for slug in a.filmes:
        relatorio(slug, Path(a.out_dir), Path(a.dados_dir))


if __name__ == "__main__":
    main()
