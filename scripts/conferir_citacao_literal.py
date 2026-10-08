"""Citação literal SEM aspas nos bullets da síntese — a lacuna da regra 2.

A regra 2 do prompt de síntese (§D) manda `exemplo_parafraseado` ser
paráfrase, "NUNCA citação literal". A única conferência de código era a
remoção MECÂNICA de aspas (`synthesize._remover_aspas`): um trecho copiado sem
aspas passava. Este script mede o que a remoção de aspas não vê.

**A medida.** Para cada bullet (tema com paráfrase, num bucket), a MAIOR
sequência contínua de palavras que a paráfrase compartilha com alguma review
do MESMO bucket — a amostra que a síntese leu (`pipeline.amostra_do_bruto`,
a mesma seleção de produção, recusadas já fora). Palavras normalizadas:
minúsculas, sem acento, só letras e dígitos. Zero rede, zero LLM.

**Sem limiar chutado.** A saída é a DISTRIBUIÇÃO nos buckets sintetizados
pelo DeepSeek (os 99, menos o bucket de fallback) — a base contra a qual os
bullets em Gemini são lidos: quantos passam do p99 da base, e quais. A
paráfrase é em pt-BR, então só review em português pode casar em sequência
longa; tradução literal de review em outra língua NÃO é detectável por esta
medida — limite declarado, não resolvido.

Uso:
    python scripts/conferir_citacao_literal.py            # base + Gemini
    python scripts/conferir_citacao_literal.py --exemplos 10   # os maiores da base
    python scripts/conferir_citacao_literal.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.pipeline import amostra_do_bruto  # noqa: E402


def tokens(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.findall(r"[a-z0-9]+", t)


def maior_sequencia(a: list[str], b: list[str]) -> tuple[int, int]:
    """(tamanho, início em `a`) da maior sequência contínua comum."""
    melhor, fim = 0, 0
    ant = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = ant[j - 1] + 1
                if cur[j] > melhor:
                    melhor, fim = cur[j], i
        ant = cur
    return melhor, fim - melhor


def bullets_do_filme(d: dict) -> list[dict]:
    slug = d["slug"]
    amostra = amostra_do_bruto(slug, coleta=d.get("coleta"))
    textos = {b: [(r.id, tokens(r.texto)) for r in rs] for b, rs in amostra.items()}
    gemini_filme = bool(d.get("proveniencia_llm"))
    saida = []
    for b in d.get("buckets", []):
        nome = b.get("bucket")
        gemini = gemini_filme or bool(b.get("fallback_conteudo"))
        for t in b.get("temas") or []:
            p = tokens(t.get("exemplo_parafraseado", ""))
            if not p:
                continue
            melhor = (0, None, 0)
            for rid, rt in textos.get(nome, []):
                n, ini = maior_sequencia(p, rt)
                if n > melhor[0]:
                    melhor = (n, rid, ini)
            n, rid, ini = melhor
            saida.append({"slug": slug, "bucket": nome, "tema": t.get("tema"),
                          "gemini": gemini, "maior_sequencia": n, "review": rid,
                          "trecho": " ".join(p[ini:ini + n]) if n else "",
                          "n_palavras_parafrase": len(p)})
    return saida


def medir() -> dict:
    base, gemini = [], []
    for arq in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        if "buckets" not in d or "slug" not in d:
            continue
        for x in bullets_do_filme(d):
            (gemini if x["gemini"] else base).append(x)
    q = sorted(x["maior_sequencia"] for x in base)
    n = len(q)
    ref = {"n": n, "mediana": q[n // 2], "p90": q[int(0.9 * n)],
           "p99": q[int(0.99 * n)], "max": q[-1],
           "contagem": {k: sum(1 for v in q if v >= k) for k in (5, 6, 8, 10)}}
    acima = [x for x in gemini if x["maior_sequencia"] > ref["p99"]]
    return {"base_deepseek": ref, "n_gemini": len(gemini),
            "gemini_acima_do_p99": acima,
            "maiores_da_base": sorted(base, key=lambda x: -x["maior_sequencia"])[:30]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--exemplos", type=int, default=0)
    a = ap.parse_args(argv)
    r = medir()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    b = r["base_deepseek"]
    print(f"base DeepSeek: {b['n']} bullets · maior sequência comum com uma review "
          f"do bucket (palavras): mediana {b['mediana']} · p90 {b['p90']} · "
          f"p99 {b['p99']} · máx {b['max']} · ≥5: {b['contagem'][5]} · "
          f"≥6: {b['contagem'][6]} · ≥8: {b['contagem'][8]} · ≥10: {b['contagem'][10]}")
    for x in r["maiores_da_base"][:a.exemplos]:
        print(f"  [{x['maior_sequencia']:2}] {x['slug']}/{x['bucket']} · {x['trecho']}")
    print(f"Gemini: {r['n_gemini']} bullets · acima do p99 da base: "
          f"{len(r['gemini_acima_do_p99'])}")
    for x in r["gemini_acima_do_p99"]:
        print(f"  [{x['maior_sequencia']:2}] {x['slug']}/{x['bucket']} "
              f"({x['review']}) · {x['trecho']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
