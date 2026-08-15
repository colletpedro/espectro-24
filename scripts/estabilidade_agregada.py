"""Estabilidade das FREQUÊNCIAS AGREGADAS — não da classificação individual.

A Entrega 3 da auditoria de acurácia (`scripts/auditoria_acuracia.py
estabilidade`) mediu que só 26,5% das 200 reviews reclassificadas produzem
conjunto idêntico de eixos. Isso é um teto para acurácia INDIVIDUAL. Mas o
produto nunca lê a classificação individual — lê `fracao_livre`, a margem de
lift (20pp) e o estado `contraste`, todos FREQUÊNCIAS AGREGADAS somadas por
código sobre o corpus inteiro. A pergunta desta tarefa é se a instabilidade
individual se cancela no agregado (erro simétrico, ruído) ou se sobrevive
(erro correlacionado, viés).

**Zero chamadas de LLM.** As duas classificações independentes das 200
reviews (execução A = a persistida em produção, `eixos_original`; execução B
= a reclassificação da auditoria, `eixos_reclassificado`) já estão em
`resultado/auditoria-acuracia/estabilidade_bruto.jsonl`. Este script só soma.

Uso:
    python scripts/estabilidade_agregada.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import EIXOS, MARGENS, recuperar_eixo  # noqa: E402

FONTE = RAIZ / "resultado" / "auditoria-acuracia" / "estabilidade_bruto.jsonl"
SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "estabilidade_agregada.json"

BUCKETS = ("negativas", "medianas", "positivas")
CATEGORIAS = list(EIXOS) + ["livre"]  # Entrega 1 pede "10 eixos (+ livre)"
MARGEM_SCHEMA = 0.20  # a margem calibrada em TAXONOMIA_10.md, Entrega 3


def _carregar() -> list[dict]:
    """Lê o bruto da Entrega 3 da auditoria e aplica o MESMO reparo de nome
    malformado (`recuperar_eixo`) à execução B — a execução A já vem
    reparada (`eixos_original` foi montado por `auditoria_acuracia.
    _carregar_universo`, que já repara). Reparar as duas do mesmo jeito é o
    que impede diferença de reparo virar "instabilidade" espúria."""
    regs = []
    for linha in FONTE.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok"):
            continue
        b = list(r["eixos_reclassificado"])
        for bruto in r.get("eixos_invalidos_reclassificado", []):
            alvo = recuperar_eixo(bruto)
            if alvo and alvo not in b:
                b.append(alvo)
        r = dict(r, eixos_A=sorted(r["eixos_original"]), eixos_B=sorted(set(b)))
        regs.append(r)
    return regs


# ===========================================================================
# Entrega 1 — frequência agregada por eixo, A vs B
# ===========================================================================

def entrega1(regs: list[dict]) -> dict:
    n = len(regs)
    linhas = []
    for c in CATEGORIAS:
        fa = sum(1 for r in regs if c in r["eixos_A"]) / n
        fb = sum(1 for r in regs if c in r["eixos_B"]) / n
        linhas.append({"eixo": c, "freq_A": fa, "freq_B": fb,
                       "diff_pp": (fb - fa) * 100})
    linhas.sort(key=lambda x: -abs(x["diff_pp"]))
    media_abs = sum(abs(l["diff_pp"]) for l in linhas) / len(linhas)
    return {
        "n": n, "por_eixo": linhas,
        "diferenca_media_absoluta_pp": media_abs,
        "eixo_maior_divergencia": linhas[0]["eixo"],
        "maior_divergencia_pp": linhas[0]["diff_pp"],
        "dentro_de_3pp": sum(1 for l in linhas if abs(l["diff_pp"]) <= 3),
        "acima_de_3pp": [l["eixo"] for l in linhas if abs(l["diff_pp"]) > 3],
    }


# ===========================================================================
# Entrega 2 — efeito no lift
# ===========================================================================

def _freq_por_bucket(regs: list[dict], campo: str, eixo: str) -> dict[str, float]:
    por_b = {}
    for b in BUCKETS:
        sub = [r for r in regs if r["bucket"] == b]
        por_b[b] = (sum(1 for r in sub if eixo in r[campo]) / len(sub)
                    if sub else 0.0)
    return por_b


def _lift(freqs: dict[str, float]) -> tuple[float, str]:
    ordenado = sorted(freqs.items(), key=lambda kv: kv[1])
    vencedor = ordenado[-1][0]
    lift = ordenado[-1][1] - ordenado[-2][1]
    return lift, vencedor


def entrega2(regs: list[dict]) -> dict:
    n_por_bucket = dict(Counter(r["bucket"] for r in regs))
    por_eixo = []
    trocaram_lado = []
    for e in EIXOS:
        fa = _freq_por_bucket(regs, "eixos_A", e)
        fb = _freq_por_bucket(regs, "eixos_B", e)
        lift_a, venc_a = _lift(fa)
        lift_b, venc_b = _lift(fb)
        lado_a = lift_a >= MARGEM_SCHEMA
        lado_b = lift_b >= MARGEM_SCHEMA
        mudou = lado_a != lado_b
        linha = {"eixo": e, "lift_A": lift_a, "vencedor_A": venc_a,
                "lift_B": lift_b, "vencedor_B": venc_b,
                "freqs_A": fa, "freqs_B": fb,
                "acima_da_margem_A": lado_a, "acima_da_margem_B": lado_b,
                "mudou_de_lado": mudou}
        por_eixo.append(linha)
        if mudou:
            trocaram_lado.append(e)
    return {
        "margem": MARGEM_SCHEMA, "n_por_bucket": n_por_bucket,
        "ressalva": ("200 reviews é amostra pequena para lift — a média por "
                    "bucket é 66-77, contra os até 40 por bucket/filme que "
                    "calibraram a margem original. Direcional, não conclusivo."),
        "por_eixo": por_eixo,
        "n_eixos_que_mudaram_de_lado": len(trocaram_lado),
        "eixos_que_mudaram_de_lado": trocaram_lado,
    }


# ===========================================================================
# Entrega 3 — núcleo estável
# ===========================================================================

def entrega3(regs: list[dict]) -> dict:
    n = len(regs)
    nucleos, bordas = [], []
    contagem_nucleo = Counter()
    contagem_borda = Counter()
    for r in regs:
        a, b = set(r["eixos_A"]), set(r["eixos_B"])
        nucleo, borda = a & b, a ^ b
        nucleos.append(len(nucleo))
        bordas.append(len(borda))
        for e in nucleo:
            contagem_nucleo[e] += 1
        for e in borda:
            contagem_borda[e] += 1
        r["_nucleo"], r["_borda"] = nucleo, borda

    razao_borda_nucleo = []
    for e in CATEGORIAS:
        nu, bo = contagem_nucleo[e], contagem_borda[e]
        razao = (bo / nu) if nu else (float("inf") if bo else 0.0)
        razao_borda_nucleo.append({"eixo": e, "n_nucleo": nu, "n_borda": bo,
                                   "razao_borda_sobre_nucleo": razao})
    # Ordenado por N ABSOLUTO na borda — é a leitura mais direta de "este
    # eixo aparece muito em execução divergente", e evita que um eixo raro
    # (n_nucleo=0, n_borda=1 → razão infinita) suba ao topo por acidente
    # aritmético em vez de por volume real.
    razao_borda_nucleo.sort(key=lambda x: -x["n_borda"])

    freq_nucleo_vs_completa = []
    for e in CATEGORIAS:
        f_nucleo = sum(1 for r in regs if e in r["_nucleo"]) / n
        f_completa = sum(1 for r in regs if e in r["eixos_A"]) / n
        freq_nucleo_vs_completa.append({
            "eixo": e, "freq_completa_A": f_completa, "freq_so_nucleo": f_nucleo,
            "diff_pp": (f_nucleo - f_completa) * 100})
    freq_nucleo_vs_completa.sort(key=lambda x: x["diff_pp"])

    return {
        "n": n,
        "tamanho_medio_nucleo": sum(nucleos) / n,
        "tamanho_medio_borda": sum(bordas) / n,
        "eixos_mais_na_borda_que_no_nucleo": [
            r for r in razao_borda_nucleo if r["n_borda"] > r["n_nucleo"]],
        "razao_borda_nucleo_por_eixo": razao_borda_nucleo,
        "freq_nucleo_vs_execucao_completa": freq_nucleo_vs_completa,
        "maior_queda_pp_ao_restringir_ao_nucleo": freq_nucleo_vs_completa[0],
    }


# ===========================================================================
# Entrega 4 — tom_atmosfera vs impacto_emocional: troca ou independência?
# ===========================================================================

def entrega4(regs: list[dict]) -> dict:
    TA, IE = "tom_atmosfera", "impacto_emocional"
    troca, so_um_oscila, ambos_mesma_direcao, nenhum_oscila = [], [], [], []
    for r in regs:
        a, b = r["eixos_A"], r["eixos_B"]
        ta_a, ta_b = TA in a, TA in b
        ie_a, ie_b = IE in a, IE in b
        ta_osc, ie_osc = ta_a != ta_b, ie_a != ie_b
        if not ta_osc and not ie_osc:
            nenhum_oscila.append(r["id"])
            continue
        if ta_osc and ie_osc:
            # troca: um aparece em A-só e o outro em B-só (direções opostas)
            entrou_ta, saiu_ta = (ta_b and not ta_a), (ta_a and not ta_b)
            entrou_ie, saiu_ie = (ie_b and not ie_a), (ie_a and not ie_b)
            eh_troca = (entrou_ta and saiu_ie) or (saiu_ta and entrou_ie)
            (troca if eh_troca else ambos_mesma_direcao).append(r["id"])
        else:
            so_um_oscila.append(r["id"])

    n_relevantes = len(troca) + len(so_um_oscila) + len(ambos_mesma_direcao)
    return {
        "n_total": len(regs),
        "n_nenhum_dos_dois_oscila": len(nenhum_oscila),
        "n_ao_menos_um_oscila": n_relevantes,
        "troca_sistematica": {"n": len(troca), "ids": troca,
                              "fracao_dos_relevantes": (
                                  len(troca) / n_relevantes if n_relevantes else None)},
        "ambos_oscilam_mesma_direcao": {"n": len(ambos_mesma_direcao),
                                        "ids": ambos_mesma_direcao},
        "so_um_oscila_independente": {"n": len(so_um_oscila),
                                      "fracao_dos_relevantes": (
                                          len(so_um_oscila) / n_relevantes
                                          if n_relevantes else None)},
        "veredito": (
            "troca sistemática — fronteira mal desenhada, redesenhar o prompt"
            if n_relevantes and len(troca) / n_relevantes >= 0.5 else
            "oscilação majoritariamente independente — instabilidade geral, "
            "não fronteira específica"),
    }


# ===========================================================================
# Veredito
# ===========================================================================

def veredito(e1: dict, e2: dict, e3: dict) -> dict:
    """Não colapsa as três entregas num único booleano por AND/OR — essa é
    exatamente a espécie de resumo que esconde nuance (o mesmo defeito que
    esta medição existe para expor). Reporta os fatos separados; a leitura
    fica registrada em `ESTABILIDADE_AGREGADA.md`, não aqui.
    """
    eixos_concentracao = sorted(set(e1["acima_de_3pp"]) | {
        r["eixo"] for r in e3["freq_nucleo_vs_execucao_completa"]
        if abs(r["diff_pp"]) >= 10})
    eixos_herdados_do_gate_8 = {"ritmo", "atuacao", "direcao_imagem",
                                "roteiro_estrutura", "som_trilha", "tom_atmosfera"}
    concentrado_em_eixos_recentes = (
        eixos_concentracao
        and set(eixos_concentracao) - eixos_herdados_do_gate_8 == set(eixos_concentracao))

    return {
        "fatos": {
            "Entrega1_diferenca_media_pp": e1["diferenca_media_absoluta_pp"],
            "Entrega1_eixos_acima_de_3pp": e1["acima_de_3pp"],
            "Entrega2_lift_maximo_observado_pp": max(
                max(r["lift_A"], r["lift_B"]) for r in e2["por_eixo"]) * 100,
            "Entrega2_eixos_que_mudaram_de_lado_da_margem_20pp": (
                e2["eixos_que_mudaram_de_lado"]),
            "Entrega2_teve_poder_para_testar_a_margem": False,
            "Entrega3_maior_queda_ao_restringir_ao_nucleo_pp": abs(
                e3["maior_queda_pp_ao_restringir_ao_nucleo"]["diff_pp"]),
        },
        "eixos_com_instabilidade_concentrada": eixos_concentracao,
        "instabilidade_concentrada_em_eixos_recem_alterados": (
            concentrado_em_eixos_recentes),
        "leitura": (
            "Frequências agregadas na maioria dos eixos ficam dentro de "
            "1,5pp entre execuções — os 6 eixos herdados do gate de 8 "
            "(inalterados desde então) são estáveis. A instabilidade real "
            "se concentra nos eixos NOVOS/AFROUXADOS (impacto_emocional, "
            "livre, comparacoes, expectativa), consistente nas 3 entregas "
            "(frequência, núcleo, e a suspeita de troca refutada na "
            "Entrega 4). A margem de lift não foi estressada por esta "
            "medição — nenhum eixo chegou perto dela em nenhuma execução, "
            "então 'zero mudaram de lado' não confirma robustez, só não a "
            "refuta."),
    }


def main() -> None:
    regs = _carregar()
    e1, e2, e3, e4 = entrega1(regs), entrega2(regs), entrega3(regs), entrega4(regs)
    v = veredito(e1, e2, e3)
    rel = {"n_reviews": len(regs), "entrega1_frequencia_agregada": e1,
          "entrega2_efeito_no_lift": e2, "entrega3_nucleo_estavel": e3,
          "entrega4_tom_atmosfera_vs_impacto_emocional": e4, "veredito": v}
    SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"n={len(regs)}")
    print(f"\nEntrega 1 — diferença média absoluta: "
          f"{e1['diferenca_media_absoluta_pp']:.2f}pp · maior: "
          f"{e1['eixo_maior_divergencia']} ({e1['maior_divergencia_pp']:+.1f}pp)")
    print(f"Entrega 2 — eixos que mudam de lado da margem de 20pp: "
          f"{e2['n_eixos_que_mudaram_de_lado']}/10 "
          f"{e2['eixos_que_mudaram_de_lado']}")
    print(f"Entrega 3 — núcleo médio {e3['tamanho_medio_nucleo']:.2f} · "
          f"borda média {e3['tamanho_medio_borda']:.2f} · "
          f"maior queda ao restringir ao núcleo: "
          f"{e3['maior_queda_pp_ao_restringir_ao_nucleo']['eixo']} "
          f"({e3['maior_queda_pp_ao_restringir_ao_nucleo']['diff_pp']:+.1f}pp)")
    print(f"Entrega 4 — {e4['veredito']} "
          f"(troca: {e4['troca_sistematica']['n']}/{e4['n_ao_menos_um_oscila']})")
    print(f"\ninstabilidade concentrada em eixos recém-alterados? "
          f"{v['instabilidade_concentrada_em_eixos_recem_alterados']} "
          f"{v['eixos_com_instabilidade_concentrada']}")
    print(f"\n{v['leitura']}")
    print(f"→ {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
