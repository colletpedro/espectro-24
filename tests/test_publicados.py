"""[rodada editorial 2] TRAVA DE PUBLICAÇÃO — `dados/publicados.json`.

`frontend/build_data.py` publica SÓ os slugs da lista explícita e
versionada (não mais todo slug do consenso que tenha `resultado/*.json`):
  · o catálogo gerado é exatamente o conjunto da lista;
  · um resultado novo fora da lista não entra (e é contado);
  · slug da lista sem resultado faz o build FALHAR.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def bd():
    spec = importlib.util.spec_from_file_location(
        "build_data_publicados", RAIZ / "frontend" / "build_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resultados(tmp_path: Path, slugs) -> Path:
    for s in slugs:
        (tmp_path / f"{s}.json").write_text(json.dumps({"slug": s}), encoding="utf-8")
    return tmp_path


def _data_js() -> dict:
    t = (RAIZ / "frontend" / "js" / "data.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("=") + 1:].strip().rstrip(";"))


def test_lista_versionada_sem_repeticao(bd):
    slugs = bd.ler_publicados()
    assert len(slugs) == len(set(slugs)) == 99
    assert slugs == sorted(slugs)


def test_catalogo_publicado_e_exatamente_a_lista(bd):
    dados = _data_js()
    assert set(dados["catalogo"]) == set(bd.ler_publicados())
    assert len(dados["catalogo"]) == len(set(dados["catalogo"]))
    assert set(dados["filmes"]) == set(bd.ler_publicados()) | {"teste-degradado"}
    t = (RAIZ / "frontend" / "js" / "indice.js").read_text(encoding="utf-8")
    indice = json.loads(t[t.index("=") + 1:].strip().rstrip(";"))
    assert {f["slug"] for f in indice["filmes"]} == set(bd.ler_publicados())


def test_resultado_novo_fora_da_lista_nao_entra(bd, tmp_path):
    res = _resultados(tmp_path, ["a-filme", "b-filme", "filme-novo"])
    catalogo, ignorados = bd.catalogo_para_build(["b-filme", "a-filme"], res)
    assert catalogo == ["a-filme", "b-filme"]
    assert ignorados == ["filme-novo"]


def test_destaque_continua_primeiro(bd, tmp_path):
    res = _resultados(tmp_path, ["the-invite-2026", "a-filme"])
    assert bd.catalogo_para_build(["a-filme", "the-invite-2026"], res)[0] == [
        "the-invite-2026", "a-filme"]


def test_slug_da_lista_sem_resultado_faz_o_build_falhar(bd, tmp_path):
    res = _resultados(tmp_path, ["a-filme"])
    with pytest.raises(SystemExit) as e:
        bd.catalogo_para_build(["a-filme", "sem-resultado"], res)
    assert "sem-resultado" in str(e.value)


def test_lista_com_slug_repetido_falha(bd, tmp_path):
    p = tmp_path / "publicados.json"
    p.write_text(json.dumps({"slugs": ["a", "a"]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        bd.ler_publicados(p)


def test_o_build_nao_le_mais_o_consenso():
    fonte = (RAIZ / "frontend" / "build_data.py").read_text(encoding="utf-8")
    assert 'RESULTADO / "votacao-3" / "consenso.jsonl"' not in fonte
    assert "catalogo_para_build(ler_publicados())" in fonte


def test_resultados_reais_fora_da_lista_sao_ignorados(bd):
    """Hoje há 1 — `como-fazer-um-curta-...`, resultado de demonstração de
    2026-07 que nunca foi publicado. Resultados novos de filmes em
    classificação também caem aqui até entrarem na lista."""
    publicados = set(bd.ler_publicados())
    _, ignorados = bd.catalogo_para_build(sorted(publicados))
    assert "como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual" in ignorados
    assert not set(ignorados) & publicados
    assert set(ignorados) == {p.stem for p in (RAIZ / "resultado").glob("*.json")} - publicados
