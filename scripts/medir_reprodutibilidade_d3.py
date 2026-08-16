"""[v1.9.15, Entrega 4] Reprodutibilidade da rotulagem [D3] — o rótulo de
tema por eixo é ESTÁVEL entre duas rodadas independentes, ou tem o mesmo
problema que a classificação por review tinha antes da votação de 3?

Achado a investigar (conferência de `resultado/v1914/ROTULAGEM_CONFERENCIA.md`):
em `cidade-de-deus`, "Excesso de violência e ritmo exaustivo" (negativas) foi
rotulado `ritmo` e "Excesso de violência" (medianas) foi rotulado
`tom_atmosfera` — mesmo núcleo, eixos diferentes, no mesmo filme.

Método: roda `rotular_bucket` DUAS VEZES, sobre os MESMOS temas publicados
dos 3 filmes (`resultado/{slug}.json`), e mede a fração de temas cujo eixo
mudou entre as duas rodadas. NÃO decide nada sozinho — reporta a medição.

Uso:
    python scripts/medir_reprodutibilidade_d3.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24.rotulagem import rotular_bucket  # noqa: E402

CATALOGO = ["cure", "cidade-de-deus", "the-invite-2026"]
SAIDA = RAIZ / "resultado" / "v1915"


def _rodada(n: int) -> dict[str, dict[str, list[dict]]]:
    """`{slug: {bucket: rotulos}}` de uma rodada completa sobre os 3 filmes."""
    fora = {}
    for slug in CATALOGO:
        output = json.loads((RAIZ / "resultado" / f"{slug}.json")
                            .read_text(encoding="utf-8"))
        fora[slug] = {}
        for b in output["buckets"]:
            temas = list(b.get("temas") or [])
            if not temas:
                continue
            r = rotular_bucket(b["bucket"], temas)
            fora[slug][b["bucket"]] = r["rotulos"]
            print(f"  rodada {n} · {slug}/{b['bucket']}: "
                  f"{len(r['rotulos'])} temas rotulados")
    return fora


def main() -> None:
    load_dotenv(RAIZ / ".env")

    print("=== Rodada 1 ===")
    r1 = _rodada(1)
    print("\n=== Rodada 2 ===")
    r2 = _rodada(2)

    print("\n=== Comparação ===")
    total, mudou = 0, 0
    divergencias = []
    for slug in CATALOGO:
        for bucket in r1.get(slug, {}):
            m1 = {x["tema"]: x["eixo"] for x in r1[slug][bucket]}
            m2 = {x["tema"]: x["eixo"] for x in r2[slug].get(bucket, [])}
            for tema, eixo1 in m1.items():
                total += 1
                eixo2 = m2.get(tema)
                if eixo1 != eixo2:
                    mudou += 1
                    divergencias.append({
                        "slug": slug, "bucket": bucket, "tema": tema,
                        "rodada_1": eixo1, "rodada_2": eixo2,
                    })

    fracao = mudou / total if total else None
    print(f"\n{total} temas comparados, {mudou} mudaram de eixo entre as "
          f"duas rodadas ({fracao:.1%} se não None)" if total else "sem dado")
    if fracao is not None:
        print(f"fração que MANTEVE o eixo: {1 - fracao:.1%}")

    for d in divergencias:
        print(f"  [{d['slug']}/{d['bucket']}] {d['tema']!r}: "
              f"{d['rodada_1']} -> {d['rodada_2']}")

    if fracao is not None and fracao >= 0.20:
        leitura = ("REPRODUTIBILIDADE BAIXA — mesma classe de problema que a "
                  "classificação por review tinha antes da votação de 3 "
                  "(26,5% de reprodutibilidade individual medida em "
                  "ESTABILIDADE_AGREGADA.md). A solução conhecida é a mesma "
                  "(votação), mas é custo recorrente por filme e a decisão "
                  "não é deste script.")
    elif fracao is not None:
        leitura = ("Reprodutibilidade razoável — divergência pontual, não "
                  "padrão sistemático. Não indica necessidade de votação.")
    else:
        leitura = "sem dado suficiente"
    print(f"\nLEITURA: {leitura}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "reprodutibilidade_d3.json").write_text(json.dumps({
        "total_temas": total, "n_mudou": mudou, "fracao_mudou": fracao,
        "divergencias": divergencias, "leitura": leitura,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {(SAIDA / 'reprodutibilidade_d3.json').relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
