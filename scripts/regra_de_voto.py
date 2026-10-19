"""Recalcula o F1 do gate sob outras regras de voto — ZERO chamadas.

**Pergunta (2026-10-12).** Os modelos locais reprovaram no gate com a regra de
produção (2 de 3), e o gpt-oss tem precisão 0,90 e recall 0,55: acerta quando
marca, marca pouco. Marcar com 1 de 3 (qualquer passe) deveria trocar recall
por precisão. Aqui se mede quanto, a partir dos registros JÁ GRAVADOS.

**Regras.** `k` = número mínimo de passes (de 3) que precisam marcar o eixo:
k=1 (qualquer passe), k=2 (a de produção), k=3 (unânime). A MESMA regra é
aplicada ao DeepSeek, com os passes dele em disco (`variantes/A_regra_passe_*`
e `verificador/V2_alvo_passe_*`) — a comparação só vale contra o DeepSeek na
mesma regra.

**Verificador como em produção:** `V2_alvo`, passe 1, remove
`impacto_emocional` de quem o verificador reprovou. Só existe veredito para as
reviews que estavam no consenso 2-de-3 DO PRÓPRIO MODELO quando o verificador
rodou. Sob k=1 há candidatas a mais, SEM veredito: ficam como estão (a política
conservadora de `verificador_impacto.aplicar`: sem veredito, não remove). O
relatório conta quantas são, por modelo e regra, e traz também a variante sem
o verificador.

**AVISO (consta do relatório).** Escolher a regra olhando o mesmo gabarito que
a avalia infla o resultado — foi assim que a variante da régua do par passou no
piloto e morreu fora da amostra. O resultado é PISTA, não aprovação: n=100,
uma regra escolhida a posteriori entre três, sem amostra de teste separada.

Bootstrap por review (B=5000, semente 20261012, fixada ANTES de rodar); o
mesmo sorteio de reviews vale para o DeepSeek e para o modelo (pareado), então
o IC de ΔF1 é o da diferença na MESMA regra.

Uso:
    python scripts/regra_de_voto.py --local-dir <pasta com gpt-oss-20b/ e qwen3-14b/> \\
        --modelos gpt-oss-20b qwen3-14b --saida <pasta>
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import auditoria_acuracia as aa  # noqa: E402
import variante_impacto_estrito as vie  # noqa: E402
from classificar_10 import EIXOS  # noqa: E402

DIR_DS_CLASS = RAIZ / "resultado" / "auditoria-acuracia" / "variantes"
DIR_DS_VERIF = RAIZ / "resultado" / "auditoria-acuracia" / "verificador"
EIXO_V = "impacto_emocional"
REGRAS = (1, 2, 3)
SEMENTE = 20261012
N_BOOTSTRAP = 5000
AVISO = ("Escolher a regra olhando o mesmo gabarito que a avalia infla o "
         "resultado (foi assim que a variante da régua do par passou no "
         "piloto e morreu fora da amostra). Trate como pista, não como "
         "aprovação.")


def consenso_k(base: Path, prefixo: str, k: int) -> dict[str, list[str]]:
    """Eixos com pelo menos `k` votos entre os 3 passes. A leitura do passe é
    a de `vie._ler_passe` (eixo inválido recuperado), a mesma do gate."""
    passes = [vie._ler_passe(prefixo, n, base) for n in (1, 2, 3)]
    ids = set(passes[0]) & set(passes[1]) & set(passes[2])
    saida = {}
    for rid in sorted(ids):
        votos = Counter(e for p in passes for e in p[rid])
        saida[rid] = sorted(e for e, v in votos.items() if v >= k)
    return saida


def veredito_passe1(arq: Path) -> dict[str, bool]:
    out = {}
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok"):
                    out[r["id"]] = r["confirma"]
    return out


def com_verificador(eixos_por_id: dict[str, list[str]], vered: dict[str, bool]
                    ) -> tuple[dict[str, list[str]], dict]:
    """`verificador_impacto.aplicar` + a contagem de candidatas sem veredito."""
    saida, sem_veredito, removidas = {}, 0, 0
    for rid, eixos in eixos_por_id.items():
        e = list(eixos)
        if EIXO_V in e:
            if rid not in vered:
                sem_veredito += 1
            elif vered[rid] is False:
                e.remove(EIXO_V)
                removidas += 1
        saida[rid] = e
    return saida, {"candidatas_sem_veredito": sem_veredito, "removidas": removidas}


def _prf(tp: int, fp: int, fn: int) -> dict:
    return {"precisao": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def _contagens(anot: dict, pred: dict[str, list[str]], ids: list[str]) -> dict:
    ev = set(EIXOS)
    c = {e: [0, 0, 0] for e in list(EIXOS) + ["_micro"]}
    for rid in ids:
        h = set(anot[rid]["eixos"]) & ev
        m = set(pred[rid]) & ev
        for e in EIXOS:
            c[e][0] += e in h and e in m
            c[e][1] += e in m and e not in h
            c[e][2] += e in h and e not in m
        c["_micro"][0] += len(h & m)
        c["_micro"][1] += len(m - h)
        c["_micro"][2] += len(h - m)
    return {k: tuple(v) for k, v in c.items()}


def _ic(xs: list[float]) -> list[float]:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return [None, None]
    return [round(xs[int(0.025 * len(xs))], 4), round(xs[int(0.975 * len(xs))], 4)]


def tabela_com_ic(anot: dict, ds: dict, md: dict) -> dict:
    """P/R/F1 por eixo e micro dos dois lados, cada um com IC95, e ΔF1
    (modelo − DeepSeek) com IC95 pareado. Mesmo sorteio nos dois lados."""
    ids = sorted(set(ds) & set(md) & set(anot))
    rng = random.Random(SEMENTE)
    chaves = list(EIXOS) + ["_micro"]
    acc = {k: {"ds": [], "md": [], "delta": []} for k in chaves}
    for _ in range(N_BOOTSTRAP):
        am = [rng.choice(ids) for _ in ids]
        cd, cm = _contagens(anot, ds, am), _contagens(anot, md, am)
        for k in chaves:
            pd, pm = _prf(*cd[k]), _prf(*cm[k])
            acc[k]["ds"].append(pd)
            acc[k]["md"].append(pm)
            acc[k]["delta"].append((pm["f1"] or 0.0) - (pd["f1"] or 0.0))
    pontual_d, pontual_m = _contagens(anot, ds, ids), _contagens(anot, md, ids)
    positivos = {e: sum(e in anot[r]["eixos"] for r in ids) for e in EIXOS}
    saida = {"n": len(ids), "positivos": positivos}
    for k in chaves:
        linha = {}
        for lado, pont in (("deepseek", pontual_d[k]), ("modelo", pontual_m[k])):
            p = _prf(*pont)
            bs = acc[k]["ds" if lado == "deepseek" else "md"]
            linha[lado] = {m: {"valor": None if p[m] is None else round(p[m], 4),
                               "ic95": _ic([b[m] for b in bs])}
                           for m in ("precisao", "recall", "f1")}
        d = (_prf(*pontual_m[k])["f1"] or 0.0) - (_prf(*pontual_d[k])["f1"] or 0.0)
        linha["delta_f1"] = {"valor": round(d, 4), "ic95": _ic(acc[k]["delta"])}
        saida[k] = linha
    return saida


def rodar(local_dir: Path, modelos: list[str]) -> dict:
    anot = aa.ler_anotacoes_humanas()
    vered_ds = veredito_passe1(DIR_DS_VERIF / "V2_alvo_passe_1.jsonl")
    rel = {"aviso": AVISO, "semente": SEMENTE, "B": N_BOOTSTRAP,
           "verificador": "V2_alvo, passe 1, remove impacto_emocional; sem "
                          "veredito = mantém", "regras": {}}
    for k in REGRAS:
        bruto_ds = consenso_k(DIR_DS_CLASS, "A_regra", k)
        ds_v, info_ds = com_verificador(bruto_ds, vered_ds)
        bloco = {"deepseek": {"verificador": info_ds}, "modelos": {}}
        for nome in modelos:
            base = local_dir / nome
            bruto_m = consenso_k(base, "classificacao", k)
            vered_m = veredito_passe1(base / "V2_alvo_passe_1.jsonl")
            md_v, info_m = com_verificador(bruto_m, vered_m)
            bloco["modelos"][nome] = {
                "verificador": info_m,
                "com_v2": tabela_com_ic(anot, ds_v, md_v),
                "sem_v2": tabela_com_ic(anot, bruto_ds, bruto_m)}
        rel["regras"][f"{k}_de_3"] = bloco
    return rel


def _f(x) -> str:
    return "  —  " if x is None else f"{x:.3f}"


def markdown(rel: dict) -> str:
    L = [f"# Regra de voto — recálculo sem chamadas\n", f"> **AVISO.** {rel['aviso']}\n",
         f"Bootstrap por review, B={rel['B']}, semente {rel['semente']} (fixada "
         f"antes de rodar). IC95 entre colchetes. DeepSeek e modelo na MESMA regra "
         f"e MESMO sorteio. Verificador: {rel['verificador']}.\n"]
    for regra, bloco in rel["regras"].items():
        for nome, m in bloco["modelos"].items():
            for variante, titulo in (("com_v2", "com V2 (produção)"), ("sem_v2", "sem V2")):
                t = m[variante]
                L.append(f"\n## {nome} · {regra.replace('_', ' ')} · {titulo} (n={t['n']})\n")
                if variante == "com_v2":
                    L.append(f"V2: DeepSeek {bloco['deepseek']['verificador']} · "
                             f"{nome} {m['verificador']}\n")
                L.append("| eixo | pos | DS P | DS R | DS F1 | modelo P | modelo R | "
                         "modelo F1 [IC95] | ΔF1 [IC95] |")
                L.append("|---|---|---|---|---|---|---|---|---|")
                for e in list(EIXOS) + ["_micro"]:
                    x = t[e]
                    d, g = x["deepseek"], x["modelo"]
                    L.append(
                        f"| {'**micro**' if e == '_micro' else e} | "
                        f"{t['positivos'].get(e, '')} | "
                        f"{_f(d['precisao']['valor'])} | {_f(d['recall']['valor'])} | "
                        f"{_f(d['f1']['valor'])} | {_f(g['precisao']['valor'])} "
                        f"[{_f(g['precisao']['ic95'][0])}; {_f(g['precisao']['ic95'][1])}] | "
                        f"{_f(g['recall']['valor'])} "
                        f"[{_f(g['recall']['ic95'][0])}; {_f(g['recall']['ic95'][1])}] | "
                        f"{_f(g['f1']['valor'])} "
                        f"[{_f(g['f1']['ic95'][0])}; {_f(g['f1']['ic95'][1])}] | "
                        f"{x['delta_f1']['valor']:+.3f} "
                        f"[{x['delta_f1']['ic95'][0]:+.3f}; {x['delta_f1']['ic95'][1]:+.3f}] |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-dir", type=Path, required=True)
    ap.add_argument("--modelos", nargs="+", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args()
    rel = rodar(a.local_dir, a.modelos)
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "regra_de_voto.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    (a.saida / "regra_de_voto.md").write_text(markdown(rel), encoding="utf-8")
    print(markdown(rel))


if __name__ == "__main__":
    main()
