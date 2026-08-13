"""[Entrega 1] Quanto o recall baixo em review curta enviesa a frequência publicada.

A auditoria humana de 100 reviews (`resultado/auditoria-acuracia/`) achou
recall de 0,35 em reviews ≤200 chars contra 0,88 acima de 400 — com precisão
estável (0,87–0,93) em toda faixa. O modelo não troca de eixo em texto curto:
ele OMITE eixo.

Mas a auditoria sobreamostrou reviews curtas de propósito (42 de 100), então
o número dela não é o número do corpus. Este script mede o corpus de produção
de verdade — `votacao-3/amostra.json`, as 3990 reviews que `selecionar()`
entrega à síntese — e projeta o viés que a omissão deixa nas frequências.

**A correção aplicada**, por (faixa de comprimento × eixo):

    estimado_real = observado × precisão / recall

`× precisão` remove os falsos positivos que o observado carrega; `÷ recall`
repõe os falsos negativos que ele não viu. Ambos os fatores vêm da auditoria,
na MESMA faixa de comprimento — é o que torna a correção sensível ao defeito
que se quer medir, em vez de aplicar uma taxa média que o esconderia.

**O que este número NÃO é.** Cada célula (faixa × eixo) da auditoria tem
poucas dezenas de eventos; a razão 1/recall explode quando o recall é baixo,
então o IC95 (Wilson sobre tp/(tp+fn)) é largo — reportado junto, e largo de
propósito. O ponto defensável não é o valor absoluto de nenhum eixo: é que o
fator de correção NÃO É UNIFORME entre eixos (≈2,0x em `impacto_emocional`,
`roteiro_estrutura` e `expectativa` contra 1,12x em `direcao_imagem`). Viés
uniforme preservaria o lift; viés diferencial reordena o ranking, que é o que
o schema consome.

Uso:
    python scripts/vies_recall_curtas.py

Saída em `resultado/auditoria-acuracia/vies_recall_curtas.json`.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_AMOSTRA = RAIZ / "resultado" / "votacao-3" / "amostra.json"
ARQ_CONSENSO = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"
ARQ_METRICAS = RAIZ / "resultado" / "auditoria-acuracia" / "metricas_relatorio.json"
ARQ_SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "vies_recall_curtas.json"

EIXOS = (
    "ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura", "som_trilha",
    "tom_atmosfera", "impacto_emocional", "comparacoes", "expectativa",
    "critica_social",
)

# As faixas da AUDITORIA (é nelas que existe recall medido). As faixas finas
# pedidas no relatório de distribuição são outras — ver `faixa_fina`.
BANDAS_AUDITORIA = ("<=200 (piso)", "201-400", "401-800", "801+")


def faixa_auditoria(n: int) -> str:
    if n <= 200:
        return "<=200 (piso)"
    if n <= 400:
        return "201-400"
    if n <= 800:
        return "401-800"
    return "801+"


def faixa_fina(n: int) -> str:
    if n <= 200:
        return "150-200"
    if n <= 300:
        return "201-300"
    if n <= 400:
        return "301-400"
    return "401+"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson — comporta-se em n pequeno e em p colado em 0/1, que é
    exatamente o regime das células desta auditoria."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centro - meia), min(1.0, centro + meia))


def distribuicao_producao(reviews: list[dict]) -> dict:
    """Onde o corpus REAL cai, por faixa de comprimento e por bucket."""
    n = len(reviews)
    por_faixa = Counter(faixa_fina(r["n_chars"]) for r in reviews)
    curtas_por_bucket: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in reviews:
        alvo = curtas_por_bucket[r["bucket"]]
        alvo[1] += 1
        if r["n_chars"] <= 200:
            alvo[0] += 1
    abaixo_do_piso = [r for r in reviews if r["n_chars"] < 150]
    return {
        "n_reviews": n,
        "por_faixa": {
            f: {"n": por_faixa[f], "fracao": por_faixa[f] / n}
            for f in ("150-200", "201-300", "301-400", "401+")
        },
        "ate_200_por_bucket": {
            b: {"curtas": v[0], "total": v[1], "fracao": v[0] / v[1]}
            for b, v in sorted(curtas_por_bucket.items())
        },
        "abaixo_de_min_chars_150": {
            "n": len(abaixo_do_piso),
            "fracao": len(abaixo_do_piso) / n,
            "nota": "cascata de fallback quando o bucket seca; min_chars=150 "
                    "vale para o caminho normal da seleção",
        },
    }


def projetar_vies(consenso: list[dict], metricas: dict) -> dict:
    recall, precisao, celulas = {}, {}, {}
    for banda, bloco in metricas["por_faixa_n_chars"].items():
        for eixo, v in bloco["por_eixo"].items():
            recall[(banda, eixo)] = v["recall"]
            precisao[(banda, eixo)] = v["precisao"]
            celulas[(banda, eixo)] = (v["tp"], v["fp"], v["fn"])

    observado: dict[tuple[str, str], int] = defaultdict(int)
    for r in consenso:
        banda = faixa_auditoria(r["n_chars"])
        for eixo in r["eixos"]:
            if eixo in EIXOS:
                observado[(banda, eixo)] += 1

    por_eixo = {}
    for eixo in EIXOS:
        obs_total = est_total = lo_total = hi_total = 0.0
        detalhe = {}
        for banda in BANDAS_AUDITORIA:
            obs = observado[(banda, eixo)]
            rec = recall[(banda, eixo)]
            pre = precisao[(banda, eixo)]
            tp, fp, fn = celulas[(banda, eixo)]
            obs_total += obs
            if rec:
                p = pre if pre is not None else 1.0
                est = obs * p / rec
                rlo, rhi = wilson(tp, tp + fn)
                # recall alto → estimativa baixa, e vice-versa.
                lo = obs * p / rhi if rhi else est
                hi = obs * p / rlo if rlo else float("inf")
            else:
                # recall nulo ou indefinido na célula: sem base para corrigir.
                est = lo = hi = float(obs)
            est_total += est
            lo_total += lo
            hi_total += hi
            detalhe[banda] = {
                "observado": obs,
                "recall_auditado": rec,
                "precisao_auditada": pre,
                "auditoria_tp_fn": [tp, fn],
                "estimado": round(est, 1),
                "nao_vistas": round(est - obs, 1),
            }
        por_eixo[eixo] = {
            "observado": int(obs_total),
            "estimado": round(est_total, 1),
            "ic95_estimado": [round(lo_total, 1), round(hi_total, 1)],
            "fator": round(est_total / obs_total, 3) if obs_total else None,
            "por_faixa": detalhe,
        }

    tot_obs = sum(v["observado"] for v in por_eixo.values())
    tot_est = sum(v["estimado"] for v in por_eixo.values())
    rank_obs = sorted(por_eixo, key=lambda e: -por_eixo[e]["observado"])
    rank_est = sorted(por_eixo, key=lambda e: -por_eixo[e]["estimado"])
    ranking = []
    for pos, eixo in enumerate(rank_est, start=1):
        antes = rank_obs.index(eixo) + 1
        ranking.append({
            "eixo": eixo,
            "posicao_publicada": antes,
            "posicao_corrigida": pos,
            "movimento": antes - pos,
            "share_publicado": round(100 * por_eixo[eixo]["observado"] / tot_obs, 1),
            "share_corrigido": round(100 * por_eixo[eixo]["estimado"] / tot_est, 1),
        })
    return {"por_eixo": por_eixo, "ranking": ranking}


def main() -> None:
    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    consenso = [json.loads(l) for l in
                ARQ_CONSENSO.read_text(encoding="utf-8").splitlines() if l.strip()]
    metricas = json.loads(ARQ_METRICAS.read_text(encoding="utf-8"))

    rel = {
        "fonte": {
            "amostra_producao": str(ARQ_AMOSTRA.relative_to(RAIZ)),
            "consenso": str(ARQ_CONSENSO.relative_to(RAIZ)),
            "metricas_auditoria": str(ARQ_METRICAS.relative_to(RAIZ)),
            "n_auditadas": metricas["n_pares"],
        },
        "distribuicao": distribuicao_producao(amostra["reviews"]),
        "vies": projetar_vies(consenso, metricas),
        "ressalva": "IC95 largo: as celulas (faixa x eixo) da auditoria tem "
                    "poucas dezenas de eventos e 1/recall explode em recall "
                    "baixo. O achado defensavel e o fator NAO ser uniforme "
                    "entre eixos, nao o valor absoluto de cada um.",
    }
    ARQ_SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    d = rel["distribuicao"]
    print(f"=== DISTRIBUICAO DE PRODUCAO (n={d['n_reviews']}) ===")
    for f, v in d["por_faixa"].items():
        print(f"  {f:>8}: {v['n']:5d}  ({v['fracao']:6.1%})")
    print(f"\n  <=200 chars por bucket:")
    for b, v in d["ate_200_por_bucket"].items():
        print(f"    {b:>10}: {v['curtas']:4d}/{v['total']:4d}  ({v['fracao']:.1%})")

    print(f"\n=== VIES PROJETADO (obs x precisao / recall) ===")
    print(f"  {'eixo':<20}{'obs':>7}{'estim':>8}{'IC95':>20}{'fator':>8}")
    ordenado = sorted(rel["vies"]["por_eixo"].items(),
                      key=lambda kv: -(kv[1]["fator"] or 0))
    for eixo, v in ordenado:
        lo, hi = v["ic95_estimado"]
        print(f"  {eixo:<20}{v['observado']:>7}{v['estimado']:>8.0f}"
              f"{f'[{lo:.0f}, {hi:.0f}]':>20}{v['fator']:>7.2f}x")

    print(f"\n=== RANKING (o que o lift enxerga) ===")
    for r in rel["vies"]["ranking"]:
        mv = r["movimento"]
        seta = f"+{mv}" if mv > 0 else (str(mv) if mv else "=")
        print(f"  {r['posicao_corrigida']:>2}. {r['eixo']:<20}"
              f"publicado {r['share_publicado']:>5.1f}%  →  "
              f"corrigido {r['share_corrigido']:>5.1f}%   {seta}")
    print(f"\n→ {ARQ_SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
