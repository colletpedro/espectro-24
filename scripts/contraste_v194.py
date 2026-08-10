"""[v1.9.4, Entrega 5] Frequência do estado "SEM CONTRASTE TEMÁTICO".

MEDIÇÃO APENAS — nenhum schema, nenhum frontend, nenhuma reclassificação.
Roda sobre as classificações que o gate de taxonomia já deixou em disco
(`resultado/gate-taxonomia/classificacoes.jsonl`, 8 eixos, 859 reviews).

A pergunta: quantos filmes têm **ZERO** eixos acima da margem de 15 pp, ou
seja, nenhum eixo que separe um bucket dos outros dois? Esses são os filmes
em que os três grupos falam das MESMAS coisas e discordam só no veredito —
`contraste: valorativo` em vez de `contraste: tematico`.

Além da contagem observada, o script mede quantos filmes ficariam com zero
**sob o nulo** (bucket embaralhado dentro de cada filme). Sem isso a contagem
observada não é interpretável: o gate já mostrou que, com 20 reviews por
bucket, ~2/3 dos pares que cruzam 15 pp cruzam por acaso — logo "tem pelo
menos um eixo acima da margem" é um sinal fraco de contraste real, e a
contagem observada de filmes sem contraste é um **piso**, não uma estimativa.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.buckets import FRONTEIRAS  # noqa: E402

GATE = RAIZ / "resultado" / "gate-taxonomia"
SAIDA = RAIZ / "resultado" / "v194-recoleta" / "contraste.json"
EIXOS = ("ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura",
         "som_trilha", "tom_atmosfera", "impacto_emocional", "comparacoes")
MARGENS = (0.15, 0.20)
N_MIN_BUCKET = 15       # mesmo limiar do estado `completa` do piso escalonado
SEMENTE = 20260808
N_RODADAS = 2000


def _carregar() -> dict[str, list[dict]]:
    por_filme: dict[str, list[dict]] = defaultdict(list)
    vistos = set()
    for linha in (GATE / "classificacoes.jsonl").read_text(
            encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok"):
            continue
        chave = (r["slug"], r["bucket"], r["id"])
        if chave in vistos:
            continue
        vistos.add(chave)
        por_filme[r["slug"]].append(r)
    return por_filme


def _lifts(regs: list[dict]) -> dict[str, float]:
    porb = {b: [r for r in regs if r["bucket"] == b] for b in FRONTEIRAS}
    saida = {}
    for e in EIXOS:
        f = sorted(sum(1 for r in v if e in r["eixos"]) / len(v)
                   for v in porb.values())
        saida[e] = f[-1] - f[-2]
    return saida


def main() -> None:
    por_filme = _carregar()
    elegiveis = {
        s: regs for s, regs in por_filme.items()
        if min(sum(1 for r in regs if r["bucket"] == b) for b in FRONTEIRAS)
        >= N_MIN_BUCKET}

    observado = {}
    for slug, regs in sorted(elegiveis.items()):
        lf = _lifts(regs)
        melhor = max(lf, key=lf.get)
        observado[slug] = {
            "perfil": regs[0]["perfil"],
            "melhor_eixo": melhor,
            "melhor_lift": lf[melhor],
            "n_acima": {str(m): sum(1 for v in lf.values() if v >= m)
                        for m in MARGENS},
            "lift_por_eixo": lf,
        }

    sem_contraste = {
        str(m): sorted(s for s, d in observado.items() if d["n_acima"][str(m)] == 0)
        for m in MARGENS}

    # --- nulo: quantos filmes ficariam sem contraste SEM nenhum sinal real ---
    rng = random.Random(f"{SEMENTE}:contraste")
    marcas = {s: [[e in r["eixos"] for e in EIXOS] for r in regs]
              for s, regs in elegiveis.items()}
    tamanhos = {s: [sum(1 for r in regs if r["bucket"] == b) for b in FRONTEIRAS]
                for s, regs in elegiveis.items()}
    contagens = {str(m): [] for m in MARGENS}
    for _ in range(N_RODADAS):
        zeros = {str(m): 0 for m in MARGENS}
        for s, mk in marcas.items():
            ordem = list(range(len(mk)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos[s]:
                fatias.append(ordem[ini:ini + t])
                ini += t
            melhores = []
            for i in range(len(EIXOS)):
                fs = sorted(sum(mk[j][i] for j in fat) / len(fat) for fat in fatias)
                melhores.append(fs[-1] - fs[-2])
            for m in MARGENS:
                if not any(v >= m for v in melhores):
                    zeros[str(m)] += 1
        for m in MARGENS:
            contagens[str(m)].append(zeros[str(m)])

    def resumo(xs):
        xo = sorted(xs)
        return {"media": sum(xs) / len(xs), "p5": xo[int(0.05 * len(xo))],
                "p95": xo[int(0.95 * len(xo))]}

    rel = {
        "fonte": "resultado/gate-taxonomia/classificacoes.jsonl (8 eixos, sem reclassificar)",
        "n_filmes_elegiveis": len(elegiveis),
        "n_min_bucket": N_MIN_BUCKET,
        "n_reviews_por_bucket_na_amostra": 20,
        "observado": observado,
        "sem_contraste_tematico": {
            str(m): {"n": len(sem_contraste[str(m)]), "filmes": sem_contraste[str(m)]}
            for m in MARGENS},
        "nulo_de_permutacao": {
            "n_rodadas": N_RODADAS,
            "filmes_sem_contraste_sob_o_nulo": {
                str(m): resumo(contagens[str(m)]) for m in MARGENS},
        },
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(elegiveis)} filmes elegíveis (n_min >= {N_MIN_BUCKET})\n")
    for m in MARGENS:
        k = str(m)
        n = rel["sem_contraste_tematico"][k]["n"]
        nulo = rel["nulo_de_permutacao"]["filmes_sem_contraste_sob_o_nulo"][k]
        print(f"margem {100*m:.0f}pp → SEM CONTRASTE em {n} de {len(elegiveis)}"
              f"  ({', '.join(sem_contraste[k]) or '—'})")
        print(f"           sob o nulo: {nulo['media']:.1f} filmes "
              f"(p5={nulo['p5']}, p95={nulo['p95']})")
    print(f"\n→ {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
