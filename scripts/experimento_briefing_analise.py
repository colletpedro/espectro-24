#!/usr/bin/env python3
"""[experimento de briefing] Análise PRÉ-REGISTRADA — lê os rótulos e decide.

Escrita ANTES de qualquer rótulo existir, e antes de ver as gerações: é o
código da seção 10.4 de `ETAPA_0_DESENHO.md`. Só ela abre o mapeamento selado,
e só depois de conferir o sha256 dele contra o impresso nos relatórios cegos.

Uso:
    python scripts/experimento_briefing_analise.py --rotulos respostas.txt

Formato dos rótulos (o do relatório cego):
    CONFIRMO: X001, X002, X004–X009
    DUVIDOSO: X003 — R2 — motivo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import experimento_briefing as E  # noqa: E402

N_PERMUTACOES = 100_000
ALFA = 0.05
FILMES_DO_PILOTO = {p.stem for p in (
    RAIZ / "docs/arquivo-de-estudos/revisao-condicoes/insumo-piloto-18"
).glob("*.json")}


# ---------------------------------------------------------------------------
# Rótulos
# ---------------------------------------------------------------------------

def _expandir(trecho: str) -> list[str]:
    saida = []
    for parte in re.split(r"[,\s]+", trecho.strip()):
        if not parte:
            continue
        m = re.fullmatch(r"X(\d{3})\s*[–-]\s*X(\d{3})", parte)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            saida += [f"X{i:03d}" for i in range(a, b + 1)]
        elif re.fullmatch(r"X\d{3}", parte):
            saida.append(parte)
        else:
            raise SystemExit(f"rótulo ilegível: {parte!r}")
    return saida


def ler_rotulos(texto: str) -> dict[str, dict]:
    rot: dict[str, dict] = {}

    def pôr(num, valor):
        if num in rot:
            raise SystemExit(f"{num} rotulado duas vezes")
        rot[num] = valor

    for linha in texto.splitlines():
        linha = linha.strip()
        m = re.match(r"CONFIRMO:\s*(.*)$", linha)
        if m:
            for n in _expandir(re.sub(r"\s*[–-]\s*", "–", m.group(1))):
                pôr(n, {"duv": False, "codigos": []})
            continue
        m = re.match(r"DUVIDOSO:\s*(X\d{3})\s*[—–-]\s*(.*)$", linha)
        if m:
            # Separador entre código e motivo: travessão, meia-risca ou hífen
            # CERCADO de espaço (o hífen colado é parte de palavra).
            partes = re.split(r"\s*—\s*|\s*–\s*|\s+-\s+", m.group(2), maxsplit=1)
            codigos = [c.strip().upper() for c in partes[0].split("/")]
            if not all(re.fullmatch(r"R\d{1,2}", c) for c in codigos):
                raise SystemExit(f"{m.group(1)}: código de regra ausente — "
                                 f"{partes[0]!r}")
            pôr(m.group(1), {"duv": True, "codigos": codigos,
                             "motivo": partes[1] if len(partes) > 1 else ""})
    return rot


def grupo_do_codigo(codigos: list[str]) -> set[str]:
    return {c if c in ("R1", "R2", "R6") else "outro" for c in codigos}


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def troca_de_sinal(d: list[int], semente: int) -> float:
    """p bilateral do teste de aleatorização por troca de sinal por tema."""
    d = np.asarray(d, dtype=float)
    s = abs(d.sum())
    if not d.any():
        return 1.0
    rng = np.random.default_rng(semente)
    sinais = rng.choice((-1.0, 1.0), size=(N_PERMUTACOES, d.size))
    extremos = (np.abs(sinais @ d) >= s - 1e-9).sum()
    return (extremos + 1) / (N_PERMUTACOES + 1)


def _semente() -> int:
    return int(hashlib.sha256(E.SEMENTE.encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotulos", required=True)
    args = ap.parse_args()

    reg = E._prereg()
    # 1. O mapeamento só é aberto se bater com o hash impresso nos relatórios.
    impressos = set()
    for p in E.DIR.glob("ROTULAGEM_CEGA_*.md"):
        m = re.search(r"sha256 do mapeamento de cegamento:\*\* `([0-9a-f]{64})`",
                      p.read_text(encoding="utf-8"))
        impressos.add(m.group(1) if m else None)
    bruto_mapa = (E.SELO / "mapa.json").read_bytes()
    h = hashlib.sha256(bruto_mapa).hexdigest()
    if impressos != {h}:
        raise SystemExit(f"mapeamento não confere: arquivo {h}, relatórios "
                         f"{impressos}")
    mapa = json.loads(bruto_mapa)["itens"]

    rot = ler_rotulos(Path(args.rotulos).read_text(encoding="utf-8"))
    faltam = sorted(set(mapa) - set(rot))
    sobram = sorted(set(rot) - set(mapa))
    if faltam or sobram:
        raise SystemExit(f"rótulos incompletos — faltam {faltam}, sobram {sobram}")

    # 2. Rótulo por (slug, tema, braço, réplica).
    por_origem: dict[tuple, dict] = {}
    for num, it in mapa.items():
        for o in it["origens"]:
            por_origem[(it["slug"], it["tema_origem"], o["braco"],
                        o["replica"])] = {**rot[num], "tipo": it["tipo"],
                                          "numero": num}
    ger = E._geracoes()

    def duv(s, t, b, r):
        x = por_origem.get((s, t, b, r))
        return int(bool(x and x["duv"]))

    def conf_escrita(s, lado, t, b, r):
        g = ger[(s, b, r)]["condicoes"]
        x = por_origem.get((s, t, b, r))
        return int(E.situacao(g, lado, t) == "escrita" and x is not None
                   and not x["duv"])

    M, U = reg["M"], reg["U"]
    reps = (1, 2)
    # --- primário
    d_prim = [sum(duv(t["slug"], t["tema_origem"], "controle", r) for r in reps)
              - sum(duv(t["slug"], t["tema_origem"], "variante", r) for r in reps)
              for t in M]
    p_prim = troca_de_sinal(d_prim, _semente())
    tax = {b: sum(duv(t["slug"], t["tema_origem"], b, r) for t in M for r in reps)
           / (2 * len(M)) for b in E.BRACOS}
    # --- G2 rendimento
    d_g2 = [sum(conf_escrita(t["slug"], t["lado"], t["tema_origem"], "controle", r)
                for r in reps)
            - sum(conf_escrita(t["slug"], t["lado"], t["tema_origem"], "variante", r)
                  for r in reps) for t in M]
    p_g2 = troca_de_sinal(d_g2, _semente() + 2)
    rend = {b: sum(conf_escrita(t["slug"], t["lado"], t["tema_origem"], b, r)
                   for t in M for r in reps) for b in E.BRACOS}
    # --- G3 regressão em U
    b3 = sum(1 for t in U if duv(t["slug"], t["tema_origem"], "controle", 1)
             and not duv(t["slug"], t["tema_origem"], "variante", 1))
    c3 = sum(1 for t in U if duv(t["slug"], t["tema_origem"], "variante", 1)
             and not duv(t["slug"], t["tema_origem"], "controle", 1))
    p_g3 = E._mcnemar(b3, c3)
    # --- G1 sobre-recusa (automática, 436)
    rc = rv = 0
    for s, lado, t in reg["analisaveis"]:
        sc = E.situacao(ger[(s, "controle", 1)]["condicoes"], lado, t) == "recusa"
        sv = E.situacao(ger[(s, "variante", 1)]["condicoes"], lado, t) == "recusa"
        rc += sc and not sv
        rv += sv and not sc
    p_g1 = E._mcnemar(rc, rv)

    piora = {
        "G1": rv > rc and p_g1 < ALFA,
        "G2": sum(d_g2) > 0 and p_g2 < ALFA,
        "G3": c3 > b3 and p_g3 < ALFA,
    }
    # Seção 10.4: significativo a favor e nenhuma guarda piora → ADOTAR;
    # significativo contra, ou a favor com guarda piorando → REJEITADO;
    # sem significância → INCONCLUSIVO (a produção fica como está).
    a_favor = sum(d_prim) > 0
    if p_prim >= ALFA:
        decisao = "INCONCLUSIVO"
    elif a_favor and not any(piora.values()):
        decisao = "ADOTAR"
    else:
        decisao = "REJEITADO"

    # --- descritivos
    cod = {b: {} for b in E.BRACOS}
    for (s, t, b, r), x in por_origem.items():
        for g in grupo_do_codigo(x["codigos"]) if x["duv"] else ():
            cod[b][g] = cod[b].get(g, 0) + 1
    M_fora = [i for i, t in enumerate(M) if t["slug"] not in FILMES_DO_PILOTO]
    p_sens = troca_de_sinal([d_prim[i] for i in M_fora], _semente() + 1)

    L = ["# Resultado do experimento de briefing — análise pré-registrada", "",
         f"sha256 do mapeamento conferido: `{h}` · itens rotulados {len(rot)}", "",
         f"## Decisão (regra da seção 10.4): **{decisao}**", "",
         "| desfecho | controle | variante | estatística | p |",
         "|---|---|---|---|---|",
         f"| **primário** — duv em M ({len(M)} temas × 2 réplicas) | "
         f"{100 * tax['controle']:.1f}% | {100 * tax['variante']:.1f}% | "
         f"S = {sum(d_prim)} | {p_prim:.4f} |",
         f"| G1 — recusa, 436 temas, r1 | só controle {rc} | só variante {rv} "
         f"| McNemar | {p_g1:.4f} {'**PIORA**' if piora['G1'] else ''} |",
         f"| G2 — escritas e CONFIRMADAS em M | {rend['controle']} | "
         f"{rend['variante']} | S = {sum(d_g2)} | {p_g2:.4f} "
         f"{'**PIORA**' if piora['G2'] else ''} |",
         f"| G3 — duv em U, r1 | só controle {b3} | só variante {c3} | McNemar "
         f"| {p_g3:.4f} {'**PIORA**' if piora['G3'] else ''} |",
         "",
         "## Descritivos (sem papel na decisão)", "",
         "Duvidosos por código de regra: " + " · ".join(
             f"{b}: " + ", ".join(f"{k} {v}" for k, v in sorted(cod[b].items()))
             for b in E.BRACOS),
         "",
         f"Sensibilidade — primário só nos {len(M_fora)} temas de M fora dos "
         f"filmes do piloto: S = {sum(d_prim[i] for i in M_fora)}, "
         f"p = {p_sens:.4f}."]
    saida = E.DIR / "RESULTADO_EXPERIMENTO.md"
    saida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
