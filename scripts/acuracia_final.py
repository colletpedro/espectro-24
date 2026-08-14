"""[Entrega 2] Acurácia final de A_regra contra o gabarito humano FECHADO.

O gabarito das 100 reviews auditadas passou por duas rodadas de correção
(2026-08-14, ver `resultado/auditoria-acuracia/REGRA_ANOTACAO.md` e
`correcoes_aplicadas.json`): 66 marcações de `impacto_emocional` viraram 38,
sob a régua de que veredicto seco (positivo OU negativo) não é efeito.

Este script recalcula a acurácia de PRODUÇÃO (`A_regra`) e do prompt
ANTIGO (`baseline`) contra esse gabarito fechado — nenhuma chamada de LLM,
as classificações já estão em disco (`resultado/auditoria-acuracia/
variantes/A_regra_passe_*.jsonl`; o baseline usa
`gabarito_modelo.json`, o consenso do prompt antigo sobre as mesmas 100,
gerado antes de qualquer variante existir).

**Por que refazer, e não reusar o relatório anterior:** toda medição de
`impacto_emocional` feita antes desta sessão comparou contra um gabarito
com a assimetria ainda dentro — os números eram números de OUTRO gabarito,
não deste. Reportar o eixo sem refazer a comparação teria comparado maçã
com laranja.

Uso:
    python scripts/acuracia_final.py

Saída em `resultado/auditoria-acuracia/acuracia_final.json`.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import auditoria_acuracia as aa  # noqa: E402
import variante_impacto_estrito as vie  # noqa: E402
from classificar_10 import EIXOS  # noqa: E402

SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "acuracia_final.json"
SEMENTE_BOOTSTRAP = 20260814
N_BOOTSTRAP = 5000


def _reviews_com_recall_zero(anotacoes: dict, gabarito: dict) -> int:
    eixos = set(EIXOS)
    n = 0
    for rid, g in gabarito.items():
        humano = set(anotacoes[rid]["eixos"]) & eixos
        modelo = set(g["eixos"]) & eixos
        if humano and not (humano & modelo):
            n += 1
    return n


def _consensos_vazios(gabarito: dict) -> int:
    return sum(1 for g in gabarito.values() if g.get("confianca") == "vazio")


def _bootstrap(anotacoes: dict, baseline: dict, a_regra: dict, meta: dict) -> dict:
    """Bootstrap pareado (A_regra − baseline), ambos contra o gabarito final.

    Mesma lógica de `variantes_prompt_curtas._bootstrap` — reimplementada
    aqui porque a fonte do baseline mudou (era `A_regra_passe_*` contra
    `SYSTEM_A`; aqui é `gabarito_modelo.json`, o consenso já persistido do
    prompt antigo) e as duas fontes têm formatos de arquivo diferentes.
    """
    eixos = set(EIXOS)
    ids = sorted(anotacoes)

    def pr(sub, g):
        tp = fp = fn = 0
        for rid in sub:
            h = set(anotacoes[rid]["eixos"]) & eixos
            m = set(g[rid]["eixos"]) & eixos
            tp += len(h & m); fp += len(m - h); fn += len(h - m)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return p, r, (2 * p * r / (p + r) if p + r else 0.0)

    rng = random.Random(SEMENTE_BOOTSTRAP)
    acc = {k: [] for k in ("precisao_geral", "recall_geral", "f1_geral",
                           "recall_ate_200")}
    for _ in range(N_BOOTSTRAP):
        amostra = [rng.choice(ids) for _ in ids]
        curtas = [r for r in amostra if meta[r]["n_chars"] <= 200]
        pb, rb, fb = pr(amostra, baseline)
        pa, ra, fa = pr(amostra, a_regra)
        acc["precisao_geral"].append(pa - pb)
        acc["recall_geral"].append(ra - rb)
        acc["f1_geral"].append(fa - fb)
        if curtas:
            acc["recall_ate_200"].append(pr(curtas, a_regra)[1] - pr(curtas, baseline)[1])

    saida = {}
    for k, xs in acc.items():
        xs.sort()
        lo, hi = xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]
        saida[k] = {"delta_mediano": round(xs[len(xs) // 2], 4),
                    "ic95": [round(lo, 4), round(hi, 4)],
                    "cruza_zero": lo <= 0 <= hi}
    return saida


def main() -> None:
    anotacoes = aa.ler_anotacoes_humanas()
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    meta = {r["id"]: r for r in idx["reviews"]}

    baseline = json.loads(aa.ARQ_GABARITO.read_text(encoding="utf-8"))
    a_regra = vie.consenso("A_regra", RAIZ / "resultado" / "auditoria-acuracia" / "variantes")

    m_base = vie._metricas(anotacoes, baseline)
    m_a = vie._metricas(anotacoes, a_regra)
    boot = _bootstrap(anotacoes, baseline, a_regra, meta)

    rel = {
        "gabarito": "final (66->38 marcações de impacto_emocional, "
                    "REGRA_ANOTACAO.md aplicada nas duas rodadas de 2026-08-14)",
        "baseline_vs_gabarito_final": m_base,
        "A_regra_vs_gabarito_final": m_a,
        "por_eixo_lado_a_lado": {
            e: {"baseline": {"precisao": m_base["geral"]["por_eixo"][e]["precisao"],
                             "recall": m_base["geral"]["por_eixo"][e]["recall"]},
                "A_regra": {"precisao": m_a["geral"]["por_eixo"][e]["precisao"],
                           "recall": m_a["geral"]["por_eixo"][e]["recall"]}}
            for e in EIXOS},
        "por_faixa_n_chars_lado_a_lado": {
            f: {"baseline": vie._micro(m_base["por_faixa_n_chars"][f]["por_eixo"]),
                "A_regra": vie._micro(m_a["por_faixa_n_chars"][f]["por_eixo"])}
            for f in m_base["por_faixa_n_chars"]},
        "reviews_com_recall_zero": {
            "baseline": _reviews_com_recall_zero(anotacoes, baseline),
            "A_regra": _reviews_com_recall_zero(anotacoes, a_regra)},
        "consensos_vazios": {
            "baseline": _consensos_vazios(baseline),
            "A_regra": _consensos_vazios(a_regra)},
        "bootstrap_pareado_A_regra_menos_baseline": boot,
    }
    SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"n=100 (0 faltando)")
    print(f"concordância exata: baseline={m_base['geral']['concordancia_exata']:.3f} "
          f"A_regra={m_a['geral']['concordancia_exata']:.3f}")
    print(f"\n{'eixo':<20}{'base P':>8}{'base R':>8}{'A P':>8}{'A R':>8}")
    for e in EIXOS:
        b, a = m_base["geral"]["por_eixo"][e], m_a["geral"]["por_eixo"][e]
        print(f"{e:<20}{b['precisao']:>8.3f}{b['recall']:>8.3f}"
              f"{a['precisao']:>8.3f}{a['recall']:>8.3f}")
    mb = vie._micro(m_base["geral"]["por_eixo"])
    ma = vie._micro(m_a["geral"]["por_eixo"])
    print(f"{'micro geral':<20}{mb['precisao']:>8.3f}{mb['recall']:>8.3f}"
          f"{ma['precisao']:>8.3f}{ma['recall']:>8.3f}")
    print(f"\nreviews com recall zero: baseline={rel['reviews_com_recall_zero']['baseline']} "
          f"A_regra={rel['reviews_com_recall_zero']['A_regra']}")
    print(f"consensos vazios: baseline={rel['consensos_vazios']['baseline']} "
          f"A_regra={rel['consensos_vazios']['A_regra']}")
    print(f"\n=== bootstrap pareado (A_regra - baseline), B={N_BOOTSTRAP} ===")
    for k, d in boot.items():
        lo, hi = d["ic95"]
        marca = "" if d["cruza_zero"] else "   <- IC95 nao cruza 0"
        print(f"  {k:<18}{d['delta_mediano']:+.3f}  IC95 [{lo:+.3f}, {hi:+.3f}]{marca}")
    print(f"\n→ {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
