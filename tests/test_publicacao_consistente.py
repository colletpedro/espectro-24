"""Guarda: o que o site serve tem de estar INTEIRO no git.

Em 12/11 um push reconstruiu o site só com o que estava versionado e apagou
29 filmes cujos `frontend/data/*.json` (e a atualização de data.js/indice.js)
existiam apenas no working tree. Estes testes comparam `dados/publicados.json`,
`frontend/data/`, `js/indice.js` e `js/data.js` entre si, e os arquivos de
dados contra o que o git VERSIONA (não contra o disco), para que uma
publicação fora do git quebre a suíte antes de chegar ao site.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FRONT = RAIZ / "frontend"


def _json_do_js(caminho: Path) -> dict:
    t = caminho.read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def _publicados() -> set[str]:
    return set(json.loads((RAIZ / "dados" / "publicados.json").read_text())["slugs"])


def _data_no_disco() -> set[str]:
    """Os JSONs servidos, menos o(s) filme(s) de teste marcado(s) como ocultos
    do catálogo (`_oculto_do_catalogo`, ex.: teste-degradado)."""
    return {p.stem for p in (FRONT / "data").glob("*.json")
            if not json.loads(p.read_text(encoding="utf-8")).get("_oculto_do_catalogo")}


def _indice() -> set[str]:
    return {f["slug"] for f in _json_do_js(FRONT / "js" / "indice.js")["filmes"]}


def test_publicados_data_e_indice_concordam():
    pub, data, ind = _publicados(), _data_no_disco(), _indice()
    assert len(pub) == len(data) == len(ind), (len(pub), len(data), len(ind))
    assert pub == data == ind, (sorted(pub ^ data), sorted(pub ^ ind))


def test_data_js_cobre_os_mesmos_filmes():
    d = _json_do_js(FRONT / "js" / "data.js")
    assert set(d["catalogo"]) == _publicados()
    assert _publicados() <= set(d["filmes"])
    assert set(d["filmes"]) - _publicados() <= {"teste-degradado"}


def _git(*args):
    return subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True)


@pytest.mark.skipif(shutil.which("git") is None or _git("rev-parse").returncode != 0,
                    reason="sem repositório git")
def test_tudo_o_que_o_site_serve_esta_versionado():
    """Arquivo servido que só existe no disco some do site no próximo push."""
    servidos = [f"frontend/data/{s}.json" for s in _publicados()] + [
        "frontend/js/data.js", "frontend/js/indice.js",
        "frontend/entrada_no_catalogo.json", "dados/publicados.json"]
    fora = [p for p in servidos if _git("ls-files", "--error-unmatch", p).returncode != 0]
    assert not fora, f"não versionados (o deploy não os terá): {fora[:5]} ({len(fora)})"
    sujos = _git("status", "--porcelain", "--", *servidos).stdout.strip()
    # `??` já foi coberto acima; aqui, modificados e ainda não commitados
    modificados = [l for l in sujos.splitlines() if not l.startswith("??")]
    assert not modificados, f"modificados e não commitados: {modificados[:5]}"
