"""[NOVO v1.3.0] Ficha técnica via TMDB — mock, zero rede.

Cobre: resolução de ID com desambiguação por ano, cache em disco (nunca
rebusca filme já buscado), falha da API não quebra o pipeline (retorna
None + aviso), fallback de sinopse en quando pt-BR vem vazio.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from espectro24.ficha import buscar_ficha, titulo_ano_de_slug


class FakeTmdbSession:
    """Mapeia (url, ano do param 'year') -> corpo JSON. `calls` registra
    cada requisição feita, na ordem, para asserções de contagem/params."""

    def __init__(self, respostas: dict[str, dict]):
        self.respostas = respostas
        self.calls: list[tuple[str, dict]] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        key = self._match(url, params or {})
        body = self.respostas.get(key, {})
        return SimpleNamespace(status_code=200, json=lambda: body)

    def _match(self, url, params):
        if "search/movie" in url:
            return ("search", params.get("query"), params.get("year"))
        return ("movie", params.get("language"))


def _detalhes(overview="Um filme sobre algo.", title="Título PT"):
    return {
        "id": 42,
        "title": title,
        "original_title": "Original Title",
        "overview": overview,
        "genres": [{"name": "Drama"}, {"name": "Suspense"}],
        "runtime": 111,
        "release_date": "1997-06-01",
        "credits": {"crew": [
            {"job": "Writer", "name": "Fulano"},
            {"job": "Director", "name": "Kiyoshi Kurosawa"},
        ]},
    }


# --- desambiguação por ano ---

def test_resolucao_de_id_desambigua_por_ano(tmp_path):
    session = FakeTmdbSession({
        ("search", "The Invite", 2026): {"results": [
            {"id": 1, "release_date": "2003-01-01"},
            {"id": 2, "release_date": "2026-05-01"},
        ]},
        ("movie", "pt-BR"): _detalhes(title="The Invite"),
    })
    ficha, aviso = buscar_ficha("The Invite", 2026, tmp_path, api_key="k", session=session)
    assert aviso is None
    assert ficha["titulo"] == "The Invite"
    # o segundo resultado da busca (release_date 2026) foi escolhido, não o
    # primeiro (2003) — confirmado pela URL /movie/2 chamada em seguida.
    movie_calls = [url for url, _ in session.calls if "search/movie" not in url]
    assert any(url.endswith("/movie/2") for url in movie_calls)


def test_titulo_ano_de_slug_extrai_sufixo_de_ano():
    assert titulo_ano_de_slug("the-invite-2026") == ("the invite", 2026)
    assert titulo_ano_de_slug("cure") == ("cure", None)
    assert titulo_ano_de_slug("cidade-de-deus") == ("cidade de deus", None)


# --- cache: nunca rebusca filme já buscado ---

def test_segunda_busca_usa_cache_sem_tocar_a_rede(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(title="Cure"),
    })
    f1, a1 = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    n_chamadas_1 = len(session.calls)
    assert a1 is None

    f2, a2 = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert a2 is None
    assert f2 == f1
    assert len(session.calls) == n_chamadas_1  # nenhuma chamada nova


# --- falha da API é aditiva: nunca levanta, retorna (None, aviso) ---

def test_chave_ausente_retorna_none_com_aviso(tmp_path, monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    ficha, aviso = buscar_ficha("Cure", 1997, tmp_path, api_key=None)
    assert ficha is None
    assert "TMDB_API_KEY" in aviso


def test_http_erro_retorna_none_com_aviso_sem_levantar(tmp_path):
    class SessionErro:
        def get(self, url, params=None, timeout=None):
            return SimpleNamespace(status_code=500, json=lambda: {})

    ficha, aviso = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=SessionErro())
    assert ficha is None
    assert "TMDB" in aviso


def test_sem_resultado_retorna_none_e_cacheia_nao_encontrado(tmp_path):
    session = FakeTmdbSession({("search", "Filme Inexistente", None): {"results": []}})
    ficha, aviso = buscar_ficha("Filme Inexistente", None, tmp_path, api_key="k", session=session)
    assert ficha is None
    assert "nenhum resultado" in aviso

    # segunda chamada: usa o cache de "não encontrado", não rebusca
    ficha2, aviso2 = buscar_ficha("Filme Inexistente", None, tmp_path, api_key="k", session=session)
    assert ficha2 is None
    assert "cache" in aviso2
    assert len(session.calls) == 1  # só a primeira buscou de fato


# --- fallback de sinopse en quando pt-BR vem vazio ---

def test_overview_vazio_cai_para_ingles_com_flag(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(overview=""),
        ("movie", "en-US"): _detalhes(overview="A movie about something."),
    })
    ficha, aviso = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert aviso is None
    assert ficha["sinopse_oficial"] == "A movie about something."
    assert ficha["sinopse_fallback_en"] is True


def test_overview_pt_br_presente_nao_dispara_fallback(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(overview="Sinopse em português."),
    })
    ficha, aviso = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert ficha["sinopse_oficial"] == "Sinopse em português."
    assert ficha["sinopse_fallback_en"] is False


# --- ficha entra no dict com o formato esperado (§1.4) ---

def test_ficha_tem_os_campos_da_spec(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(),
    })
    ficha, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    for campo in ("titulo", "sinopse_oficial", "generos", "duracao_min", "diretor", "ano", "fonte"):
        assert campo in ficha
    assert ficha["fonte"] == "tmdb"
    assert ficha["diretor"] == "Kiyoshi Kurosawa"
    assert ficha["generos"] == ["Drama", "Suspense"]

    # persistido em disco (cache), JSON válido
    cached_files = list(tmp_path.glob("*.json"))
    assert len(cached_files) == 1
    assert json.loads(cached_files[0].read_text(encoding="utf-8"))["titulo"] == "Título PT"
