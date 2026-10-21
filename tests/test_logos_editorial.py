"""[rodada editorial] Classe de contraste do logo e a sua publicação.

  1. a classe medida é a razão WCAG contra o fundo de referência (#111111)
     e, abaixo do limiar, o croma decide mono × cor (`medir_editorial.py`);
  2. o build publica `ficha.logo` (caminho, idioma, classe FINAL — override
     vence a medida) e `ficha.titulo_difere_do_logo` (`build_data.py`);
  3. `data.js` e o índice da home carregam esses campos e `paises`.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))


def _modulo(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def medir():
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    return _modulo("medir_editorial_teste", RAIZ / "scripts" / "medir_editorial.py")


@pytest.fixture(scope="module")
def build():
    return _modulo("build_data_teste", RAIZ / "frontend" / "build_data.py")


def _js(caminho: Path) -> dict:
    t = caminho.read_text(encoding="utf-8")
    return json.loads(t[t.index("=") + 1:].strip().rstrip(";"))


# ---------------------------------------------------------------- 1. classe

def test_constantes_nomeadas(medir):
    assert medir.FUNDO_REFERENCIA == "#111111"
    assert medir.LIMIAR_CONTRASTE == 3.0
    assert medir.LIMIAR_CROMA_MONO == 0.15


def test_razao_wcag(medir):
    assert medir.luminancia_relativa_hex("#ffffff") == pytest.approx(1.0)
    assert medir.luminancia_relativa_hex("#000000") == 0.0
    # branco sobre #111111: (1,05)/(0,0056+0,05) ≈ 18,9
    assert medir.razao_contraste(1.0) == pytest.approx(18.88, abs=0.01)
    assert medir.razao_contraste(medir.luminancia_relativa_hex("#111111")) == pytest.approx(1.0)


@pytest.mark.parametrize("lum,croma,esperado", [
    (1.0, 0.0, "claro"),
    (0.2126, 1.0, "claro"),       # vermelho puro: 4,7:1 — a luma Rec.709 o chamava de escuro
    (0.117, 0.0, "claro"),        # logo acima do limiar 3,0
    (0.116, 0.0, "escuro_mono"),  # logo abaixo
    (0.0, 0.149, "escuro_mono"),
    (0.0, 0.15, "escuro_cor"),
    (0.08, 0.6, "escuro_cor"),
])
def test_classe_por_contraste_e_croma(medir, lum, croma, esperado):
    assert medir.classe_medida({"luminancia_relativa_media": lum,
                                "croma_medio": croma}) == esperado


def test_classe_sem_medida_e_none(medir):
    assert medir.classe_medida({"erro": "x"}) is None


def test_logos_json_coerente_com_a_regra(medir):
    logos = json.loads((RAIZ / "dados" / "logos.json").read_text(encoding="utf-8"))["logos"]
    assert len(logos) == 99
    for slug, r in logos.items():
        e = r["logo_escolhido"]
        if not e:
            assert r["classe_medida"] is None and r["idioma_logo"] is None, slug
            continue
        assert e["idioma"] in ("pt-BR", "en", "sem_idioma"), slug   # pt-PT nunca
        assert r["classe_medida"] == medir.classe_medida(e["medida_w500"]), slug


# ------------------------------------------------------------- 2. publicação

_REG = {"logo_escolhido": {"file_path": "/a.png", "idioma": "en"},
        "classe_medida": "claro"}


def test_logo_publicado_usa_a_classe_medida_sem_override(build):
    assert build.logo_da_ficha(_REG, None) == {"path": "/a.png", "idioma": "en",
                                               "classe": "claro"}


def test_override_vence_a_medida(build):
    assert build.logo_da_ficha(_REG, {"classe": "escuro_cor"})["classe"] == "escuro_cor"
    assert build.logo_da_ficha(_REG, {"desligar": True})["classe"] == "desligado"


def test_sem_logo_e_null_e_titulo_nao_difere(build):
    assert build.logo_da_ficha({"logo_escolhido": None}, None) is None
    assert build.logo_da_ficha(None, None) is None
    d = build.com_logo({"ficha": {}}, {"logo_escolhido": None}, None)
    assert d["ficha"]["logo"] is None and d["ficha"]["titulo_difere_do_logo"] is False


def test_titulo_difere_quando_o_logo_nao_e_pt_br(build):
    en = build.com_logo({"ficha": {}}, _REG, None)["ficha"]
    br = build.com_logo({"ficha": {}}, {"logo_escolhido": {"file_path": "/b.png",
                                                           "idioma": "pt-BR"},
                                        "classe_medida": "claro"}, None)["ficha"]
    assert en["titulo_difere_do_logo"] is True and br["titulo_difere_do_logo"] is False


def test_override_versionado_e_valido():
    ov = json.loads((RAIZ / "dados" / "logos_override.json").read_text(encoding="utf-8"))
    assert isinstance(ov["overrides"], dict)
    for slug, o in ov["overrides"].items():
        assert set(o) <= {"classe", "desligar", "motivo"}, slug
        assert o.get("desligar") or o.get("classe") in ("claro", "escuro_mono", "escuro_cor"), slug


# ------------------------------------------------- 3. data.js e índice da home

def test_data_js_e_indice_carregam_logo_e_paises(build):
    logos, overrides = build.ler_logos()
    dados = _js(RAIZ / "frontend" / "js" / "data.js")
    indice = {f["slug"]: f for f in _js(RAIZ / "frontend" / "js" / "indice.js")["filmes"]}
    assert set(indice) == set(dados["catalogo"])
    for slug in dados["catalogo"]:
        ficha = dados["filmes"][slug]["ficha"]
        assert ficha["logo"] == build.logo_da_ficha(logos.get(slug), overrides.get(slug)), slug
        assert ficha["paises"] and all(len(p) == 2 for p in ficha["paises"]), slug
        for campo in ("logo", "paises", "titulo_difere_do_logo"):
            assert indice[slug][campo] == ficha[campo], (slug, campo)
