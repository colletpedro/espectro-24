#!/usr/bin/env python3
"""[rodada cor] MEDE as paletas dos três grupos (?cor=) sobre o fundo escuro.

Fonte ÚNICA das cores: o dicionário `PALETAS` abaixo. O CSS
(`frontend/css/styles.css`, `:root[data-cor=...]`) repete os mesmos hex, e
`tests/test_cores_grupos.py` confere que os dois concordam.

Restrições medidas (as da rodada), para cada paleta:
  · texto colorido (rótulos, "Aprofundar"): contraste WCAG >= 4,5 sobre o fundo;
  · barras e marcadores: contraste >= 3,0;
  · distância entre cada par de cores, CIEDE2000 >= 20 em visão normal e sob
    simulação de deuteranopia e de protanopia (Machado, Oliveira & Fernandes
    2009, severidade 1,0, aplicada em RGB linear);
  · luminância relativa das três dentro de ±25% da média das três.
  · [editorial] saturação HSL <= 45%.

    venv/bin/python scripts/medir_cores.py            # tabela + grava dados/cores_grupos.json
    venv/bin/python scripts/medir_cores.py --buscar   # busca a paleta editorial
"""
from __future__ import annotations

import colorsys
import itertools
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUNDO = "#0b0c10"     # --bg

# neg, med, pos
PALETAS = {
    "atual":     {"neg": "#e0673f", "med": "#e3b23c", "pos": "#4d90e5"},
    "apagada":   {"neg": "#9c5f4e", "med": "#a8874f", "pos": "#5b7a99"},
    "editorial": {"neg": "#c1a85c", "med": "#95c6ba", "pos": "#7e97c8"},
}

MIN_TEXTO, MIN_BARRA, MIN_DE, TOL_LUM, MAX_SAT = 4.5, 3.0, 20.0, 0.25, 0.45

# Machado et al. 2009, severidade 1,0 (RGB linear)
MACHADO = {
    "deuteranopia": [[0.367322, 0.860646, -0.227968],
                     [0.280085, 0.672501, 0.047413],
                     [-0.011820, 0.042940, 0.968881]],
    "protanopia": [[0.152286, 1.052583, -0.204868],
                   [0.114503, 0.786281, 0.099216],
                   [-0.003882, -0.048116, 1.051998]],
}


def rgb(hexa):
    h = hexa.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def linear(c):
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def luminancia(hexa):
    r, g, b = linear(rgb(hexa))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b=FUNDO):
    la, lb = luminancia(a), luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def saturacao_hsl(hexa):
    r, g, b = rgb(hexa)
    return colorsys.rgb_to_hls(r, g, b)[2]


def simular(hexa, modo):
    if modo == "normal":
        return hexa
    m = MACHADO[modo]
    lin = linear(rgb(hexa))
    out = [max(0.0, min(1.0, sum(m[i][j] * lin[j] for j in range(3)))) for i in range(3)]
    srgb = [12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055 for x in out]
    return "#" + "".join(f"{round(max(0, min(1, x)) * 255):02x}" for x in srgb)


def lab(hexa):
    r, g, b = linear(rgb(hexa))
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(c1, c2):
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h = lambda b, a: (math.degrees(math.atan2(b, a)) % 360) if (a or b) else 0.0
    h1p, h2p = h(b1, a1p), h(b2, a2p)
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        d = h2p - h1p
        dhp = d - 360 if d > 180 else d + 360 if d < -180 else d
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpm = (h1p + h2p) / 2
    else:
        hpm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hpm - 30)) + 0.24 * math.cos(math.radians(2 * hpm))
         + 0.32 * math.cos(math.radians(3 * hpm + 6)) - 0.20 * math.cos(math.radians(4 * hpm - 63)))
    dth = 30 * math.exp(-(((hpm - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / math.sqrt(20 + (Lpm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


PARES = [("neg", "med"), ("neg", "pos"), ("med", "pos")]
MODOS = ("normal", "deuteranopia", "protanopia")


def medir(p):
    lums = {g: luminancia(p[g]) for g in p}
    media = sum(lums.values()) / 3
    r = {
        "hex": dict(p),
        "contraste": {g: round(contraste(p[g]), 2) for g in p},
        "saturacao_hsl": {g: round(saturacao_hsl(p[g]), 3) for g in p},
        "luminancia": {g: round(lums[g], 4) for g in p},
        "luminancia_desvio_da_media": {g: round(lums[g] / media - 1, 3) for g in p},
        "de2000": {m: {f"{a}-{b}": round(de2000(simular(p[a], m), simular(p[b], m)), 1)
                       for a, b in PARES} for m in MODOS},
    }
    falhas = []
    for g in p:
        if r["contraste"][g] < MIN_TEXTO:
            falhas.append(f"texto {g} {r['contraste'][g]} < {MIN_TEXTO}")
        if r["contraste"][g] < MIN_BARRA:
            falhas.append(f"barra {g} {r['contraste'][g]} < {MIN_BARRA}")
        if abs(r["luminancia_desvio_da_media"][g]) > TOL_LUM:
            falhas.append(f"luminância {g} {r['luminancia_desvio_da_media'][g]:+.0%} fora de ±25%")
    for m in MODOS:
        for par, v in r["de2000"][m].items():
            if v < MIN_DE:
                falhas.append(f"ΔE {par} em {m}: {v} < {MIN_DE}")
    r["falhas"] = falhas
    r["passa"] = not falhas
    return r


def _passa(p, sat=MAX_SAT):
    return medir(p)["passa"] and all(saturacao_hsl(p[g]) <= sat for g in p)


def buscar():
    """Varre matizes/saturações/claridades e lista as paletas que passam, com
    neg no quadrante quente, pos no frio e med nem cinza (S >= 20%) nem
    vermelho × verde com neg/pos."""
    def hsl(h, s, l):
        r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
        return "#" + "".join(f"{round(x * 255):02x}" for x in (r, g, b))
    achados = []
    quentes = [(h, s, l) for h in range(0, 41, 5) for s in (0.35, 0.45) for l in (0.55, 0.6, 0.65, 0.7)]
    frios = [(h, s, l) for h in range(190, 231, 5) for s in (0.35, 0.45) for l in (0.55, 0.6, 0.65, 0.7)]
    meios = [(h, s, l) for h in range(45, 330, 15) for s in (0.25, 0.35, 0.45) for l in (0.5, 0.55, 0.6, 0.65, 0.7)]
    for n, p, m in itertools.product(quentes, frios, meios):
        pal = {"neg": hsl(*n), "med": hsl(*m), "pos": hsl(*p)}
        if _passa(pal):
            achados.append((pal, n, m, p))
    return achados


def main(argv):
    if "--buscar" in argv:
        achados = buscar()
        print(len(achados), "paletas passam")
        for pal, n, m, p in achados[:40]:
            print(pal, "neg", n, "med", m, "pos", p)
        return 0
    saida = {}
    for nome, p in PALETAS.items():
        r = medir(p)
        saida[nome] = r
        print(f"\n== {nome}  {'PASSA' if r['passa'] else 'FALHA'}")
        for g in p:
            print(f"  {g}  {p[g]}  contraste {r['contraste'][g]:>5}  S_hsl {r['saturacao_hsl'][g]:.2f}  "
                  f"L {r['luminancia'][g]:.4f} ({r['luminancia_desvio_da_media'][g]:+.0%})")
        for m in MODOS:
            print(f"  ΔE2000 {m:13s} " + "  ".join(f"{k} {v}" for k, v in r["de2000"][m].items()))
        for f in r["falhas"]:
            print("  ✗", f)
    (RAIZ / "dados").mkdir(exist_ok=True)
    (RAIZ / "dados" / "cores_grupos.json").write_text(
        json.dumps({"fundo": FUNDO, "limites": {"texto": MIN_TEXTO, "barra": MIN_BARRA, "de2000": MIN_DE,
                                                  "luminancia": TOL_LUM, "saturacao_editorial": MAX_SAT},
                    "paletas": saida}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
