"""Fase 0 do fine-tuning — (c) poder do teste por tamanho, com o FILME como cluster.

Pergunta: com N filmes de teste (18 bullets cada), qual a MENOR diferença na
taxa de bullets "sem apoio" (juiz v2.2) que se detecta com poder 0,80 e
α = 0,05 bilateral, entre dois lados medidos nos MESMOS filmes (treinado ×
base, ou treinado × publicado)?

Insumos MEDIDOS (checagem-bullets, branch gate-local, juiz v2.2 congelado):
publicado 2/90 sem apoio, qwen3:14b 6/90; por filme (anatomy, incendies,
mother, napoleon, the-substance): publicado 0,1,0,1,0 e local 3,0,2,0,1.

Dois cálculos (os dois são ESTIMATIVA, não medição):
1. Analítico: teste de duas proporções com efeito de desenho
   DEFF = 1 + (m − 1)·ICC, m = 18 bullets por filme. Ignora o pareamento —
   conservador.
2. Simulação: logit-normal por filme, efeito do filme COMPARTILHADO pelos dois
   lados (pareamento), teste = bootstrap por filme da diferença média pareada
   (IC 95% percentil exclui 0). É o teste que a avaliação vai usar.

O ICC vem dos 10 clusters de referência (5 filmes × 2 lados, estimador ANOVA),
com 9 eventos no total — muito incerto; por isso o resultado sai para uma
faixa de ICC.

Saída: `finetune/poder.json` e `finetune/poder.md`.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

import numpy as np  # noqa: E402

M_BULLETS = 18
REF = {"publicado": [0, 1, 0, 1, 0], "local": [3, 0, 2, 0, 1]}
P0 = 2 / 90                     # publicado, MEDIDO
APOIO_GE2 = {"publicado": 0.833, "local": 0.822}
SEG_POR_PAR = 16.0              # dado pelo dono
PARES_POR_BULLET = 5
LADOS_MEDIDOS = 3               # publicado, base, treinado
TAMANHOS = (20, 25, 30)
ICCS = (0.0, 0.023, 0.05, 0.10, 0.20)   # 0,023 = o ICC medido na referência (juntos)
SEMENTE = 20261020


def icc_anova(contagens: list[int], m: int) -> float:
    """Estimador ANOVA do ICC para dados binários em clusters de mesmo tamanho."""
    k = len(contagens)
    p = [c / m for c in contagens]
    pbar = sum(contagens) / (k * m)
    msb = m * sum((pi - pbar) ** 2 for pi in p) / (k - 1)
    msw = sum(c * (1 - c / m) for c in contagens) / (k * (m - 1))
    return (msb - msw) / (msb + (m - 1) * msw)


def mde_analitico(n_filmes: int, icc: float, p0: float = P0, alfa: float = 0.05,
                  poder: float = 0.8) -> float:
    """Menor p1 > p0 detectável (duas proporções, n efetivo pelo DEFF)."""
    from statistics import NormalDist
    z_a, z_b = NormalDist().inv_cdf(1 - alfa / 2), NormalDist().inv_cdf(poder)
    n = n_filmes * M_BULLETS / (1 + (M_BULLETS - 1) * icc)
    lo, hi = p0, 0.99
    for _ in range(60):
        p1 = (lo + hi) / 2
        pb = (p0 + p1) / 2
        lhs = (z_a * math.sqrt(2 * pb * (1 - pb) / n)
               + z_b * math.sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n))
        if p1 - p0 >= lhs:
            hi = p1
        else:
            lo = p1
    return hi - p0


def _tau(icc: float) -> float:
    """Desvio do efeito de filme na escala logit para um ICC latente."""
    return math.sqrt(icc * (math.pi ** 2 / 3) / (1 - icc)) if icc > 0 else 0.0


def poder_simulado(n_filmes: int, icc: float, delta: float, semente: int,
                   r: float = 0.0, p0: float = P0, n_sim: int = 1000,
                   n_boot: int = 1000) -> float:
    """Números aleatórios COMUNS entre deltas (mesma semente): o poder fica
    monótono em delta e a bissecção de `mde_simulado` converge.

    `r` = correlação entre os efeitos de filme dos dois lados. A referência
    NÃO sustenta efeito compartilhado: o publicado erra em incendies e
    napoleon, o local em anatomy, mother e the-substance. r = 0 é o caso
    principal; r = 1 (pareamento perfeito) é o otimista."""
    rng = np.random.default_rng(semente)
    lg = lambda p: math.log(p / (1 - p))  # noqa: E731
    tau = _tau(icc)
    z1 = rng.standard_normal((n_sim, n_filmes))
    z2 = r * z1 + math.sqrt(1 - r * r) * rng.standard_normal((n_sim, n_filmes))
    z, zb = z1 * tau, z2 * tau
    u_a = rng.random((n_sim, n_filmes, M_BULLETS))
    u_b = rng.random((n_sim, n_filmes, M_BULLETS))
    idx = rng.integers(0, n_filmes, size=(n_boot, n_filmes))
    pa = 1 / (1 + np.exp(-(lg(p0) + z)))
    pb = 1 / (1 + np.exp(-(lg(p0 + delta) + zb)))
    a = (u_a < pa[..., None]).mean(axis=2)
    b = (u_b < pb[..., None]).mean(axis=2)
    d = (b - a).astype(np.float32)                    # (n_sim, n_filmes)
    rej = 0
    for ini in range(0, n_sim, 100):
        bloco = d[ini:ini + 100][:, idx].mean(axis=2)  # (100, n_boot)
        lo, hi = np.percentile(bloco, [2.5, 97.5], axis=1)
        rej += int(((lo > 0) | (hi < 0)).sum())
    return rej / n_sim


def mde_simulado(n_filmes: int, icc: float, semente: int, r: float = 0.0,
                 alvo: float = 0.8) -> dict:
    """Bissecção em delta (pp absolutos sobre P0) até 0,25 pp de resolução,
    mais o erro tipo I do mesmo teste (delta = 0): o bootstrap percentil com
    poucos eventos pode rejeitar mais que 5% sob H0, e aí o MDE é otimista."""
    tamanho = poder_simulado(n_filmes, icc, 0.0, semente, r)
    lo, hi = 0.0, 0.40
    if poder_simulado(n_filmes, icc, hi, semente, r) < alvo:
        return {"delta": None, "poder": None, "erro_tipo_1": tamanho}
    while hi - lo > 0.0025:
        mid = (lo + hi) / 2
        if poder_simulado(n_filmes, icc, mid, semente, r) >= alvo:
            hi = mid
        else:
            lo = mid
    return {"delta": hi, "poder": poder_simulado(n_filmes, icc, hi, semente, r),
            "erro_tipo_1": tamanho}


def horas_de_juiz(n_filmes: int, lados: int = LADOS_MEDIDOS,
                  reaproveitar_publicado_5: bool = False) -> float:
    pares = n_filmes * M_BULLETS * PARES_POR_BULLET * lados
    if reaproveitar_publicado_5:
        pares -= 5 * M_BULLETS * PARES_POR_BULLET
    return pares * SEG_POR_PAR / 3600


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR)
    a = ap.parse_args()
    rng = np.random.default_rng(SEMENTE)

    icc_ref = {lado: icc_anova(c, M_BULLETS) for lado, c in REF.items()}
    icc_ref["juntos"] = icc_anova(REF["publicado"] + REF["local"], M_BULLETS)
    linhas = []
    for n in TAMANHOS:
        for icc in ICCS:
            s0 = mde_simulado(n, icc, SEMENTE + n, r=0.0)
            s1 = mde_simulado(n, icc, SEMENTE + n, r=1.0)
            pp = lambda x: None if x["delta"] is None else round(100 * x["delta"], 1)  # noqa: E731
            linhas.append({"n_filmes": n, "icc": icc,
                           "deff": round(1 + (M_BULLETS - 1) * icc, 2),
                           "mde_analitico_pp": round(100 * mde_analitico(n, icc), 1),
                           "mde_simulado_r0_pp": pp(s0),
                           "erro_tipo_1_r0": s0["erro_tipo_1"],
                           "mde_simulado_r1_pp": pp(s1),
                           "erro_tipo_1_r1": s1["erro_tipo_1"]})
    custo = {n: {"horas_3_lados": round(horas_de_juiz(n), 1),
                 "horas_reaproveitando_publicado_dos_5": round(horas_de_juiz(n, reaproveitar_publicado_5=True), 1),
                 "horas_2_lados_novos": round(horas_de_juiz(n, lados=2), 1)}
             for n in TAMANHOS}
    # A referência medida, lida como um teste de 5 filmes: a diferença 6/90 − 2/90
    d_ref = [l - p for l, p in zip(REF["local"], REF["publicado"])]
    boot = np.array([np.mean(rng.choice(d_ref, 5)) for _ in range(10000)]) / M_BULLETS
    saida = {"insumos": {"p0_publicado": P0, "ref_por_filme": REF, "m_bullets": M_BULLETS,
                         "apoio_ge2": APOIO_GE2, "seg_por_par": SEG_POR_PAR,
                         "pares_por_bullet": PARES_POR_BULLET, "lados": LADOS_MEDIDOS,
                         "semente": SEMENTE},
             "icc_referencia": {k: round(v, 3) for k, v in icc_ref.items()},
             "referencia_5_filmes": {"dif_local_menos_publicado_pp": round(100 * 4 / 90, 1),
                                     "ic95_bootstrap_por_filme_pp": [
                                         round(100 * float(np.percentile(boot, 2.5)), 1),
                                         round(100 * float(np.percentile(boot, 97.5)), 1)]},
             "mde": linhas, "custo_juiz": custo}
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "poder.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    (a.saida / "poder.md").write_text(md(saida), encoding="utf-8")
    print(md(saida))


def md(s: dict) -> str:
    i = s["insumos"]
    L = ["# Poder do teste por tamanho (ESTIMADO)", "",
         f"Base: publicado {round(100 * i['p0_publicado'], 1)}% sem apoio (2/90, MEDIDO), "
         f"{i['m_bullets']} bullets por filme, α = 0,05 bilateral, poder 0,80. "
         f"ICC na referência (ANOVA, 5 filmes × 2 lados, 9 eventos): {s['icc_referencia']}. "
         f"A referência como teste de 5 filmes: local − publicado = "
         f"{s['referencia_5_filmes']['dif_local_menos_publicado_pp']} pp, IC 95% bootstrap por "
         f"filme {s['referencia_5_filmes']['ic95_bootstrap_por_filme_pp']} pp.", "",
         "Menor aumento detectável na taxa de \"sem apoio\" (pontos percentuais, sobre 2,2%):", "",
         "| filmes | ICC | DEFF | analítico (2 proporções + DEFF) | simulado r=0 (erro tipo I) | simulado r=1 (erro tipo I) |",
         "|---|---|---|---|---|---|"]
    f = lambda v: "> 40 pp" if v is None else f"+{v} pp"  # noqa: E731
    for x in s["mde"]:
        L.append(f"| {x['n_filmes']} | {x['icc']} | {x['deff']} | +{x['mde_analitico_pp']} pp | "
                 f"{f(x['mde_simulado_r0_pp'])} ({x['erro_tipo_1_r0']:.3f}) | "
                 f"{f(x['mde_simulado_r1_pp'])} ({x['erro_tipo_1_r1']:.3f}) |")
    L += ["", "r = correlação do efeito de filme entre os dois lados (r = 0 é o que a "
          "referência sugere; r = 1 é pareamento perfeito). Teste simulado = IC 95% "
          "percentil do bootstrap por filme da diferença média; 1.000 simulações × 1.000 "
          "reamostras por ponto."]
    L += ["", f"Custo do juiz: {i['seg_por_par']:.0f} s/par × {i['pares_por_bullet']} pares/bullet "
          f"× {i['m_bullets']} bullets/filme:", "",
          "| filmes | 3 lados | reaproveitando o publicado dos 5 | só base + treinado |",
          "|---|---|---|---|"]
    for n, c in s["custo_juiz"].items():
        L.append(f"| {n} | {c['horas_3_lados']} h | {c['horas_reaproveitando_publicado_dos_5']} h | "
                 f"{c['horas_2_lados_novos']} h |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
