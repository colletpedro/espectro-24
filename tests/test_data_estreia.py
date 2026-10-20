"""[home nova, rodada 3] Data de estreia completa na ficha.

Quatro travas:
  1. `ficha.py` persiste `data_estreia` (o `release_date` do TMDB) SEM mexer
     no `ano` publicado — inclusive quando o Letterboxd ganha (talk-to-me);
  2. entrada de cache sem `data_estreia` é MISS (senão uma republicação
     devolveria a ficha antiga e apagaria a data em silêncio);
  3. o harness `scripts/backfill_data_estreia.py` grava UMA linha por arquivo
     e aborta antes de gravar qualquer outra diferença;
  4. DIFF contra o commit anterior ao backfill (`f5ec6db`): nos JSONs
     publicados e no `data.js`, a única mudança é `ficha.data_estreia`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from espectro24.ficha import _cache_key, buscar_ficha
from test_ficha import FakeTmdbSession, _detalhes, _identidade

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

BASE = "f5ec6db"     # último commit ANTES do backfill da data de estreia


# ---------------------------------------------------------------------------
# 1-2. ficha.py
# ---------------------------------------------------------------------------

def _talk_to_me(tmp_path, session=None):
    session = session or FakeTmdbSession({
        ("movie", "pt-BR"): _detalhes(title="Fale Comigo", release_date="2023-07-26"),
        ("movie", "en-US"): _detalhes(title="Talk to Me", release_date="2023-07-26"),
    })
    session.respostas[("movie", "pt-BR")]["original_title"] = "Talk to Me"
    return buscar_ficha(
        "Talk to Me", 2022, tmp_path, api_key="k", session=session,
        ano_fonte="letterboxd",
        identidade=_identidade("talk-to-me-2022", "Talk to Me", 2022, 1008042))


def test_ficha_persiste_a_data_completa_sem_tocar_o_ano(tmp_path):
    ficha, aviso, descarte = _talk_to_me(tmp_path)
    assert aviso is None and descarte is None
    assert ficha["data_estreia"] == "2023-07-26"
    assert ficha["ano"] == 2022                      # o do Letterboxd continua
    chaves = list(ficha)
    assert chaves.index("data_estreia") == chaves.index("ano") + 1


@pytest.mark.parametrize("bruto", ["", None, "2023", "2023-07"])
def test_data_vazia_ou_parcial_vira_null(tmp_path, bruto):
    session = FakeTmdbSession({
        ("movie", "pt-BR"): _detalhes(title="Fale Comigo", release_date=bruto),
        ("movie", "en-US"): _detalhes(title="Talk to Me", release_date=bruto),
    })
    ficha, _a, _d = _talk_to_me(tmp_path, session)
    assert "data_estreia" in ficha and ficha["data_estreia"] is None


def _de_novo(tmp_path, session):
    return buscar_ficha(
        "Talk to Me", 2022, tmp_path, api_key="k", session=session,
        ano_fonte="letterboxd",
        identidade=_identidade("talk-to-me-2022", "Talk to Me", 2022, 1008042))


def test_cache_sem_data_estreia_e_miss_e_com_ela_e_hit(tmp_path):
    _talk_to_me(tmp_path)                            # grava o cache
    caminho = tmp_path / f"{_cache_key('Talk to Me', 2022)}.json"
    cache = json.loads(caminho.read_text(encoding="utf-8"))
    assert cache["data_estreia"] == "2023-07-26"

    sem_rede = FakeTmdbSession({})
    ficha, _a, _d = _de_novo(tmp_path, sem_rede)
    assert sem_rede.calls == [] and ficha["data_estreia"] == "2023-07-26"

    cache.pop("data_estreia")                        # entrada de antes da rodada 3
    caminho.write_text(json.dumps(cache), encoding="utf-8")
    sem_rede = FakeTmdbSession({})
    _de_novo(tmp_path, sem_rede)
    assert sem_rede.calls, "entrada sem data_estreia deveria ter ido à rede"


# ---------------------------------------------------------------------------
# 3. o harness de backfill
# ---------------------------------------------------------------------------

class SessaoId:
    """GET /movie/{id} → {id, release_date}; registra as URLs."""

    def __init__(self, datas: dict[int, str], id_trocado: dict[int, int] | None = None):
        self.datas, self.trocado, self.urls = datas, id_trocado or {}, []

    def get(self, url, params=None, timeout=None):
        self.urls.append(url)
        tid = int(url.rsplit("/", 1)[1])
        corpo = {"id": self.trocado.get(tid, tid), "release_date": self.datas.get(tid, "")}
        return SimpleNamespace(status_code=200, json=lambda: corpo)


def _doc(slug, tid, ano, **extra):
    return {"slug": slug, "data_coleta": "2026-01-01", "ficha": {
        "titulo": "T", "sinopse_oficial": "s", "ano": ano, "fonte": "tmdb",
        "tmdb_id": tid, "tmdb_fetched_at": "2026-01-01T00:00:00+00:00"},
        "eixos": {"contraste": "valorativo"}, **extra}


def _preparar(tmp_path, docs, fim=""):
    res, cache = tmp_path / "resultado", tmp_path / "cache"
    res.mkdir(); cache.mkdir()
    for d in docs:
        (res / f"{d['slug']}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2) + fim, encoding="utf-8")
    return res, cache


def test_backfill_grava_uma_linha_e_nada_mais(tmp_path):
    import backfill_data_estreia as bf
    res, cache = _preparar(tmp_path, [_doc("a", 1, 2022), _doc("b", 2, 1997)], fim="\n")
    (cache / "a_2022.json").write_text(json.dumps(
        {"titulo": "T", "ano": 2022, "fonte": "tmdb", "tmdb_id": 1},
        ensure_ascii=False, indent=2), encoding="utf-8")
    antes = {p.name: p.read_text(encoding="utf-8") for p in res.iterdir()}
    rel = bf.processar(["a", "b"], SessaoId({1: "2023-07-26", 2: ""}), "k",
                       gravar=True, resultado_dir=res, cache_dir=cache)
    assert [r["ok"] for r in rel] == [True, True]
    assert rel[0]["diverge"] is True and rel[1]["diverge"] is False
    for nome, original in antes.items():
        novo = (res / nome).read_text(encoding="utf-8")
        a, b = original.splitlines(), novo.splitlines()
        assert len(b) == len(a) + 1 and novo.endswith("\n")
        extra = [l for l in b if l not in a]
        assert len(extra) == 1 and '"data_estreia"' in extra[0]
    a = json.loads((res / "a.json").read_text(encoding="utf-8"))
    assert a["ficha"]["data_estreia"] == "2023-07-26" and a["ficha"]["ano"] == 2022
    assert json.loads((res / "b.json").read_text(encoding="utf-8"))["ficha"]["data_estreia"] is None
    c = json.loads((cache / "a_2022.json").read_text(encoding="utf-8"))
    assert c["data_estreia"] == "2023-07-26" and rel[0]["cache"] == ["a_2022.json"]


def test_backfill_simulacao_nao_grava(tmp_path):
    import backfill_data_estreia as bf
    res, cache = _preparar(tmp_path, [_doc("a", 1, 2022)])
    antes = (res / "a.json").read_text(encoding="utf-8")
    rel = bf.processar(["a"], SessaoId({1: "2022-01-01"}), "k", gravar=False,
                       resultado_dir=res, cache_dir=cache)
    assert rel[0]["gravou"] is True        # "gravaria"
    assert (res / "a.json").read_text(encoding="utf-8") == antes


def test_backfill_aborta_id_trocado_e_arquivo_fora_do_formato(tmp_path):
    import backfill_data_estreia as bf
    res, cache = _preparar(tmp_path, [_doc("a", 1, 2022), _doc("b", 2, 2000)])
    (res / "b.json").write_text(json.dumps(_doc("b", 2, 2000)), encoding="utf-8")  # sem indent
    antes = {p.name: p.read_text(encoding="utf-8") for p in res.iterdir()}
    rel = bf.processar(["a", "b"], SessaoId({1: "2022-01-01", 2: "2000-01-01"}, {1: 99}),
                       "k", gravar=True, resultado_dir=res, cache_dir=cache)
    assert [r["ok"] for r in rel] == [False, False]
    assert {p.name: p.read_text(encoding="utf-8") for p in res.iterdir()} == antes


def test_backfill_so_conversa_com_o_tmdb(tmp_path):
    import backfill_data_estreia as bf
    res, cache = _preparar(tmp_path, [_doc("a", 7, 2022)])
    s = SessaoId({7: "2022-03-01"})
    bf.processar(["a"], s, "k", gravar=True, resultado_dir=res, cache_dir=cache)
    assert s.urls == ["https://api.themoviedb.org/3/movie/7"]


# ---------------------------------------------------------------------------
# 4. DIFF contra o commit anterior ao backfill
# ---------------------------------------------------------------------------

def _git_show(caminho: str) -> str | None:
    if shutil.which("git") is None:
        return None
    r = subprocess.run(["git", "show", f"{BASE}:{caminho}"], cwd=RAIZ,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _sem_data(doc: dict) -> dict:
    d = json.loads(json.dumps(doc))
    if isinstance(d.get("ficha"), dict):
        d["ficha"].pop("data_estreia", None)
    return d


def _republicado(base: dict, atual: dict) -> bool:
    """Filme republicado DEPOIS do backfill não é comparável com a base."""
    return any(base.get(k) != atual.get(k) for k in ("data_coleta", "spec_version"))


def _data_js(texto: str) -> dict:
    return json.loads(texto[texto.index("=") + 1:].strip().rstrip(";"))


def test_diff_resultado_so_mudou_data_estreia():
    import backfill_data_estreia as bf
    if _git_show("frontend/js/data.js") is None:
        pytest.skip(f"git ou o commit {BASE} indisponível")
    comparados, pulados = 0, []
    for slug in bf.catalogo_publicado():
        base_txt = _git_show(f"resultado/{slug}.json")
        if base_txt is None:
            pulados.append(slug)
            continue
        base = json.loads(base_txt)
        atual = json.loads((RAIZ / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
        if _republicado(base, atual):
            pulados.append(slug)
            continue
        assert "data_estreia" not in (base.get("ficha") or {}), slug
        assert _sem_data(atual) == base, f"{slug}: mudou algo além de data_estreia"
        comparados += 1
    assert comparados >= 90, (comparados, pulados)


def test_diff_data_js_so_mudou_data_estreia():
    base_txt = _git_show("frontend/js/data.js")
    if base_txt is None:
        pytest.skip(f"git ou o commit {BASE} indisponível")
    base = _data_js(base_txt)
    atual = _data_js((RAIZ / "frontend" / "js" / "data.js").read_text(encoding="utf-8"))
    assert atual["catalogo"] == base["catalogo"]
    assert set(atual["filmes"]) == set(base["filmes"])
    com_data = 0
    for slug, filme in atual["filmes"].items():
        if _republicado(base["filmes"][slug], filme):
            continue
        assert _sem_data(filme) == base["filmes"][slug], slug
        com_data += bool((filme.get("ficha") or {}).get("data_estreia"))
    assert com_data >= 90


def test_ano_publicado_de_talk_to_me_nao_foi_sobrescrito():
    doc = json.loads((RAIZ / "resultado" / "talk-to-me-2022.json").read_text(encoding="utf-8"))
    assert doc["ficha"]["ano"] == 2022
    assert doc["ficha"]["data_estreia"] == "2023-07-26"
