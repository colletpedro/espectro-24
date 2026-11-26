"""Acrescenta filme(s) NOVO(s) a `dados/legibilidade_manchete.json` pelo MESMO método dos 29 de 08/11
(`preparar_legibilidade_29.py`): caixa = imagem inteira, contraste >= 4,5 do texto da justificativa
com o véu `alfa` JÁ publicado, medido sobre o `backdrop_path` em w300 (e, por construção, contra branco
puro). Não muda `alfa`, nem as caixas dos outros filmes, nem o CSS: se o contraste não passar, FALHA.

    venv/bin/python scripts/acrescentar_legibilidade.py boogie-nights
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import medir_legibilidade as M  # noqa: E402
from espectro24.still_hash import baixar  # noqa: E402

ARQ = ROOT / "dados" / "legibilidade_manchete.json"


def acrescentar(slugs):
    d = json.loads(ARQ.read_text(encoding="utf-8"))
    alfa = d["alfa"]
    for slug in slugs:
        assert slug not in d["filmes"], f"{slug} já está na medição"
        path = json.loads((ROOT / "frontend" / "data" / f"{slug}.json").read_text(encoding="utf-8"))["ficha"]["backdrop_path"]
        with Image.open(baixar(path)) as im:
            img = np.asarray(im.convert("RGB"), dtype=np.float64) / 255
        caixas = {str(w): [0, 0, 1, 1] for w in M.LARGURAS}
        r = dict(backdrop_path=path, caixas=caixas, luminancia_sem_veu={}, contraste_com_veu={},
                 caixas_metodo="limite conservador: imagem inteira; garantia adicional contra branco puro para qualquer caixa")
        for w, c in caixas.items():
            pixels = M.regiao(img, c)
            l0 = M.luminancia_do_fundo(pixels, 0)
            contraste = M.contraste(M.luminancia_do_fundo(pixels, alfa))
            assert contraste >= 4.5, f"{slug} {w}: contraste {contraste:.3f} < 4,5 com o véu publicado {alfa}"
            r["luminancia_sem_veu"][w] = round(l0, 4)
            r["contraste_com_veu"][w] = round(contraste, 3)
        d["filmes"][slug] = r
        d["garantia_novos"]["filmes"] += 1
    ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    acrescentar(sys.argv[1:])
