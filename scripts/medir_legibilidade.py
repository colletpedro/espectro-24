#!/usr/bin/env python3
"""[rodada editorial 2] MEDE a opacidade do véu atrás do texto da manchete.

O texto da manchete (logo/título, linha de metadado, justificativa) fica
numa caixa no canto inferior esquerdo do still, com um véu preto de
opacidade `--ed-veu` (frontend/css/styles.css). Esta medição escolhe a
MENOR opacidade (em centésimos) que garante contraste WCAG >= 4,5 do texto
da justificativa (`--text`, #f2f0ea) sobre o PIOR caso dos filmes elegíveis
da manchete.

O fundo de cada caso é a região do still SOB A CAIXA: o retângulo da caixa
relativo ao still, MEDIDO no navegador (iframe com a home de um dia em que
o filme é a manchete) em quatro larguras de desktop — 700, 1024, 1440 e
1920 px, com a fonte padrão da home (Instrument Sans desde a rodada da
fonte; remedido nela); abaixo de 700 px o texto sai do still e vai para fundo sólido. Em
cada região, o preto com opacidade `a` é composto sobre cada pixel em sRGB
(como o navegador compõe `rgba()`), e a luminância relativa LINEAR média
dos pixels compostos é a luminância do fundo. Contraste = (L_texto + 0,05) /
(L_fundo + 0,05).

Imagem: o `backdrop_path` publicado (o still da manchete) em w300, do
mesmo cache de `still_hash.py` (`dados/cache/_stills_w300/`). Para a média
de uma região, w300 basta.

Grava `dados/legibilidade_manchete.json` (versionado): a opacidade
escolhida, o pior caso, e por filme as caixas medidas, a luminância do
fundo sem véu e o contraste com o véu escolhido. As caixas ficam no arquivo,
então a medição se refaz sem navegador:

    venv/bin/python scripts/medir_legibilidade.py                 # caixas do arquivo
    venv/bin/python scripts/medir_legibilidade.py --caixas X.json # caixas novas
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.still_hash import baixar  # noqa: E402

INDICE_JS = ROOT / "frontend" / "js" / "indice.js"
SAIDA = ROOT / "dados" / "legibilidade_manchete.json"

COR_TEXTO = "#f2f0ea"          # --text, a cor da justificativa
CONTRASTE_MINIMO = 4.5
LARGURAS = (700, 1024, 1440, 1920)
EXCLUIDOS = {"obsession-2025"}  # fora da manchete (selecao.js, EXCLUIDOS)


def _linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def luminancia_hex(cor: str) -> float:
    rgb = np.array([int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return float(_linear(rgb) @ np.array([0.2126, 0.7152, 0.0722]))


L_TEXTO = luminancia_hex(COR_TEXTO)


def luminancia_do_fundo(pixels: np.ndarray, alfa: float) -> float:
    """Média da luminância relativa dos pixels (sRGB 0–1, N×3) depois de
    compor o preto com opacidade `alfa` por cima."""
    return float((_linear(pixels * (1 - alfa)) @ np.array([0.2126, 0.7152, 0.0722])).mean())


def contraste(l_fundo: float) -> float:
    return (L_TEXTO + 0.05) / (l_fundo + 0.05)


def regiao(img: np.ndarray, caixa) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = (min(max(v, 0.0), 1.0) for v in caixa)
    c0, c1 = int(np.floor(x0 * w)), max(int(np.ceil(x1 * w)), int(np.floor(x0 * w)) + 1)
    r0, r1 = int(np.floor(y0 * h)), max(int(np.ceil(y1 * h)), int(np.floor(y0 * h)) + 1)
    return img[r0:r1, c0:c1].reshape(-1, 3)


def _indice() -> dict:
    t = INDICE_JS.read_text(encoding="utf-8")
    return {f["slug"]: f for f in json.loads(t[t.index("=") + 1:].strip().rstrip(";"))["filmes"]}


def ler_caixas(caminho: Path | None) -> dict:
    """slug → {largura: [x0, y0, x1, y1]} (frações do still)."""
    if caminho is None:
        anterior = json.loads(SAIDA.read_text(encoding="utf-8"))
        return {s: {int(w): c for w, c in r["caixas"].items()}
                for s, r in anterior["filmes"].items()}
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    return {s: {w: v[4 * i:4 * i + 4] for i, w in enumerate(LARGURAS)}
            for s, v in bruto.items()}


def menor_alfa(regioes: list[np.ndarray]) -> float:
    """A menor opacidade, em centésimos, com contraste >= mínimo em TODAS as
    regiões (o contraste cresce com a opacidade: busca binária)."""
    def ok(a):
        return all(contraste(luminancia_do_fundo(p, a)) >= CONTRASTE_MINIMO for p in regioes)
    lo, hi = 0, 100
    if ok(0):
        return 0.0
    while hi - lo > 1:
        meio = (lo + hi) // 2
        if ok(meio / 100):
            hi = meio
        else:
            lo = meio
    return hi / 100


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caixas", type=Path)
    args = ap.parse_args()

    indice = _indice()
    caixas = ler_caixas(args.caixas)
    elegiveis = sorted(s for s in indice if s not in EXCLUIDOS)
    faltam = set(elegiveis) - set(caixas)
    if faltam:
        raise SystemExit(f"sem caixa medida para: {', '.join(sorted(faltam))}")

    pixels = {}
    for slug in elegiveis:
        path = indice[slug]["imagens"]["backdrop_path"]
        with Image.open(baixar(path)) as im:
            img = np.asarray(im.convert("RGB"), dtype=np.float64) / 255
        pixels[slug] = {w: regiao(img, caixas[slug][w]) for w in LARGURAS}

    alfa = menor_alfa([p for por_w in pixels.values() for p in por_w.values()])

    filmes, casos = {}, []
    for slug in elegiveis:
        r = {"backdrop_path": indice[slug]["imagens"]["backdrop_path"],
             "caixas": {str(w): caixas[slug][w] for w in LARGURAS},
             "luminancia_sem_veu": {}, "contraste_com_veu": {}}
        for w in LARGURAS:
            l0 = luminancia_do_fundo(pixels[slug][w], 0.0)
            c = contraste(luminancia_do_fundo(pixels[slug][w], alfa))
            r["luminancia_sem_veu"][str(w)] = round(l0, 4)
            r["contraste_com_veu"][str(w)] = round(c, 3)
            casos.append((c, slug, w, l0))
        filmes[slug] = r
    pior = min(casos)
    mais_claro = max(casos, key=lambda x: x[3])

    SAIDA.write_text(json.dumps({
        "_leia": ("Medição do véu atrás do texto da manchete "
                  "(scripts/medir_legibilidade.py). alfa = menor opacidade do "
                  "preto (centésimos) com contraste WCAG >= 4,5 do texto "
                  "#f2f0ea sobre a luminância média da região do still sob a "
                  "caixa de texto, em todos os filmes elegíveis e larguras."),
        "fonte": "Instrument Sans (padrão, js/fonte.js)",
        "cor_texto": COR_TEXTO, "contraste_minimo": CONTRASTE_MINIMO,
        "larguras": list(LARGURAS), "imagem": "backdrop_path em w300",
        "alfa": alfa,
        "pior_caso": {"slug": pior[1], "largura": pior[2],
                      "contraste": round(pior[0], 3),
                      "luminancia_sem_veu": round(pior[3], 4),
                      "contraste_sem_veu": round(contraste(pior[3]), 3)},
        "fundo_mais_claro": {"slug": mais_claro[1], "largura": mais_claro[2],
                             "luminancia_sem_veu": round(mais_claro[3], 4)},
        "filmes": filmes,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"alfa = {alfa}; pior caso {pior[1]} @ {pior[2]}px: contraste {pior[0]:.2f} "
          f"(sem véu {contraste(pior[3]):.2f}); {len(elegiveis)} filmes")


if __name__ == "__main__":
    main()
