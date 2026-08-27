"""[NOVO v1.3.0] Ficha técnica via TMDB — mock, zero rede.

Cobre: resolução de ID com desambiguação por ano, cache em disco (nunca
rebusca filme já buscado), falha da API não quebra o pipeline (retorna
None + aviso), fallback de sinopse en quando pt-BR vem vazio.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from espectro24.ficha import (
    buscar_ficha,
    resolver_ano_letterboxd,
    titulo_ano_de_slug,
)


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


def _detalhes(overview="Um filme sobre algo.", title="Título PT",
              release_date="1997-06-01"):
    return {
        "id": 42,
        "title": title,
        "original_title": "Original Title",
        "overview": overview,
        "genres": [{"name": "Drama"}, {"name": "Suspense"}],
        "runtime": 111,
        "release_date": release_date,
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
        ("movie", "pt-BR"): _detalhes(title="The Invite", release_date="2026-05-01"),
    })
    ficha, aviso, _ = buscar_ficha("The Invite", 2026, tmp_path, api_key="k", session=session)
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
    f1, a1, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    n_chamadas_1 = len(session.calls)
    assert a1 is None

    f2, a2, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert a2 is None
    assert f2 == f1
    assert len(session.calls) == n_chamadas_1  # nenhuma chamada nova


# --- falha da API é aditiva: nunca levanta, retorna (None, aviso) ---

def test_chave_ausente_retorna_none_com_aviso(tmp_path, monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    ficha, aviso, _ = buscar_ficha("Cure", 1997, tmp_path, api_key=None)
    assert ficha is None
    assert "TMDB_API_KEY" in aviso


def test_http_erro_retorna_none_com_aviso_sem_levantar(tmp_path):
    class SessionErro:
        def get(self, url, params=None, timeout=None):
            return SimpleNamespace(status_code=500, json=lambda: {})

    ficha, aviso, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=SessionErro())
    assert ficha is None
    assert "TMDB" in aviso


def test_sem_resultado_retorna_none_e_cacheia_nao_encontrado(tmp_path):
    session = FakeTmdbSession({("search", "Filme Inexistente", None): {"results": []}})
    ficha, aviso, _ = buscar_ficha("Filme Inexistente", None, tmp_path, api_key="k", session=session)
    assert ficha is None
    assert "nenhum resultado" in aviso

    # segunda chamada: usa o cache de "não encontrado", não rebusca
    ficha2, aviso2, _ = buscar_ficha("Filme Inexistente", None, tmp_path, api_key="k", session=session)
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
    ficha, aviso, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert aviso is None
    assert ficha["sinopse_oficial"] == "A movie about something."
    assert ficha["sinopse_fallback_en"] is True


def test_overview_pt_br_presente_nao_dispara_fallback(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(overview="Sinopse em português."),
    })
    ficha, aviso, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert ficha["sinopse_oficial"] == "Sinopse em português."
    assert ficha["sinopse_fallback_en"] is False


# --- ficha entra no dict com o formato esperado (§1.4) ---

def test_ficha_tem_os_campos_da_spec(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(),
    })
    ficha, _, _desc = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    for campo in ("titulo", "sinopse_oficial", "generos", "duracao_min", "diretor", "ano", "fonte"):
        assert campo in ficha
    assert ficha["fonte"] == "tmdb"
    assert ficha["diretor"] == "Kiyoshi Kurosawa"
    assert ficha["generos"] == ["Drama", "Suspense"]

    # persistido em disco (cache), JSON válido
    cached_files = list(tmp_path.glob("*.json"))
    assert len(cached_files) == 1
    assert json.loads(cached_files[0].read_text(encoding="utf-8"))["titulo"] == "Título PT"


# =====================================================================
# v1.6.0 — diretor em escrita latina (Tarefa 8)
# =====================================================================

def _detalhes_diretor(nome, overview="Um filme sobre algo.", release_date="1997-06-01"):
    d = _detalhes(overview=overview, release_date=release_date)
    d["credits"] = {"crew": [{"job": "Director", "name": nome}]}
    return d


def test_diretor_nao_latino_e_substituido_pelo_credits_en(tmp_path):
    """O TMDB devolve o nome no alfabeto nativo quando pt-BR não tem
    tradução: `cure` vinha "黒沢清", que foi parar na narrativa publicada.
    O credits en-US traz a transliteração."""
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [
            {"id": 42, "release_date": "1997-06-01", "popularity": 3.79}]},
        ("movie", "pt-BR"): _detalhes_diretor("黒沢清"),
        ("movie", "en-US"): _detalhes_diretor("Kiyoshi Kurosawa"),
    })
    ficha, aviso, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    assert aviso is None
    assert ficha["diretor"] == "Kiyoshi Kurosawa"
    assert ficha["diretor_transliterado"] is True


def test_diretor_ja_latino_nao_dispara_busca_extra(tmp_path):
    """Só filmes nessa condição pagam a requisição extra."""
    session = FakeTmdbSession({
        ("search", "Cidade de Deus", 2002): {"results": [
            {"id": 42, "release_date": "2002-01-01", "popularity": 9.0}]},
        ("movie", "pt-BR"): _detalhes_diretor("Fernando Meirelles", release_date="2002-01-01"),
        ("movie", "en-US"): _detalhes_diretor("NAO_DEVIA_SER_USADO", release_date="2002-01-01"),
    })
    ficha, _, _desc = buscar_ficha("Cidade de Deus", 2002, tmp_path, api_key="k",
                            session=session)
    assert ficha["diretor"] == "Fernando Meirelles"
    assert ficha["diretor_transliterado"] is False
    idiomas = [p.get("language") for url, p in session.calls if "search" not in url]
    assert "en-US" not in idiomas          # nenhuma requisição extra


def test_diretor_com_acento_latino_conta_como_latino(tmp_path):
    session = FakeTmdbSession({
        ("search", "Filme", 2000): {"results": [
            {"id": 42, "release_date": "2000-01-01", "popularity": 1.0}]},
        ("movie", "pt-BR"): _detalhes_diretor("José Padilha", release_date="2000-01-01"),
        ("movie", "en-US"): _detalhes_diretor("NAO_DEVIA_SER_USADO", release_date="2000-01-01"),
    })
    ficha, _, _desc = buscar_ficha("Filme", 2000, tmp_path, api_key="k", session=session)
    assert ficha["diretor"] == "José Padilha"
    assert ficha["diretor_transliterado"] is False


def test_diretor_nao_latino_sem_alternativa_latina_mantem_o_original(tmp_path):
    """Se o en-US também não for latino, mantém o que havia — melhor um nome
    em alfabeto nativo do que nenhum."""
    session = FakeTmdbSession({
        ("search", "Filme", 2000): {"results": [
            {"id": 42, "release_date": "2000-01-01", "popularity": 1.0}]},
        ("movie", "pt-BR"): _detalhes_diretor("黒沢清", release_date="2000-01-01"),
        ("movie", "en-US"): _detalhes_diretor("黒沢清", release_date="2000-01-01"),
    })
    ficha, _, _desc = buscar_ficha("Filme", 2000, tmp_path, api_key="k", session=session)
    assert ficha["diretor"] == "黒沢清"
    assert ficha["diretor_transliterado"] is False


def test_fallback_de_sinopse_reaproveita_a_resposta_en(tmp_path):
    """Quando o overview pt-BR está vazio, a resposta en-US já foi buscada —
    o diretor não-latino reusa essa resposta em vez de pedir de novo."""
    session = FakeTmdbSession({
        ("search", "Filme", 2000): {"results": [
            {"id": 42, "release_date": "2000-01-01", "popularity": 1.0}]},
        ("movie", "pt-BR"): _detalhes_diretor("黒沢清", overview="", release_date="2000-01-01"),
        ("movie", "en-US"): _detalhes_diretor("Kiyoshi Kurosawa",
                                              overview="A film about something.",
                                              release_date="2000-01-01"),
    })
    ficha, _, _desc = buscar_ficha("Filme", 2000, tmp_path, api_key="k", session=session)
    assert ficha["sinopse_fallback_en"] is True
    assert ficha["diretor"] == "Kiyoshi Kurosawa"
    n_en = sum(1 for url, p in session.calls
               if "search" not in url and p.get("language") == "en-US")
    assert n_en == 1        # UMA requisição en-US, não duas


# =====================================================================
# v1.7.0 (Tarefa 1) — resolução de ano confiável e guarda de sanidade
# =====================================================================
# Defeito real corrigido: `espectro24 --slug cure` sem --ano resolveu no
# TMDB para "The Cure" (2026, dir. Nancy Leopardi) em vez de Cure (1997,
# Kiyoshi Kurosawa) — a desambiguação por popularidade, sem ano, escolheu o
# filme errado, e a ficha completa dele foi parar na narrativa publicada
# sem nenhum aviso.

class FakeFetcherPaginaFilme:
    """Fake mínimo do `Fetcher` para `resolver_ano_letterboxd` — só precisa
    do método `get(url, cache_key) -> html`."""

    def __init__(self, html: str | None = None, excecao: Exception | None = None):
        self.html = html
        self.excecao = excecao
        self.chamadas = 0

    def get(self, url, cache_key):
        self.chamadas += 1
        if self.excecao:
            raise self.excecao
        return self.html


def test_resolver_ano_letterboxd_extrai_do_link_de_ano():
    html = '<a href="/films/year/1997/">1997</a>'
    fetcher = FakeFetcherPaginaFilme(html=html)
    assert resolver_ano_letterboxd(fetcher, "cure") == 1997
    assert fetcher.chamadas == 1


def test_resolver_ano_letterboxd_cai_para_og_title_quando_sem_link():
    html = '<meta property="og:title" content="Cure (1997)">'
    fetcher = FakeFetcherPaginaFilme(html=html)
    assert resolver_ano_letterboxd(fetcher, "cure") == 1997


def test_resolver_ano_letterboxd_sem_ano_em_lugar_nenhum_retorna_none():
    fetcher = FakeFetcherPaginaFilme(html="<html>nada aqui</html>")
    assert resolver_ano_letterboxd(fetcher, "cure") is None


def test_resolver_ano_letterboxd_falha_de_rede_retorna_none_sem_levantar():
    from espectro24.fetcher import FetchError
    fetcher = FakeFetcherPaginaFilme(excecao=FetchError("boom"))
    assert resolver_ano_letterboxd(fetcher, "cure") is None


# --- guarda de sanidade: ano divergente descarta a ficha inteira ---

def test_ano_divergente_descarta_a_ficha(tmp_path):
    """Caso real: 'cure' sem ano resolveria para 'The Cure' 2026 (o TMDB
    devolve isso como único resultado quando não se filtra por ano) — se o
    ano ESPERADO (vindo do slug/Letterboxd/--ano) for 1997, a divergência de
    quase 30 anos precisa descartar a ficha inteira, nunca publicá-la."""
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [
            {"id": 999, "release_date": "2026-01-01", "popularity": 5.0}]},
        ("movie", "pt-BR"): _detalhes(title="The Cure", overview="Outro filme.",
                                      release_date="2026-01-01"),
    })
    ficha, aviso, descarte = buscar_ficha(
        "Cure", 1997, tmp_path, api_key="k", session=session)
    assert ficha is None
    assert descarte == {"motivo": "ano_divergente", "esperado": 1997, "recebido": 2026}
    assert "divergente" in aviso.lower()
    # a ficha descartada não é cacheada — uma nova tentativa (ex. com um
    # título mais preciso) não fica travada numa rejeição antiga
    assert list(tmp_path.glob("*.json")) == []


def test_ano_divergente_em_1_ano_nao_descarta(tmp_path):
    """A guarda tolera 1 ano de folga (arredondamento de virada de ano/fuso
    do release_date) — só descarta acima disso."""
    session = FakeTmdbSession({
        ("search", "Filme", 1997): {"results": [
            {"id": 5, "release_date": "1998-01-01", "popularity": 1.0}]},
        ("movie", "pt-BR"): _detalhes(),
    })
    ficha, aviso, descarte = buscar_ficha(
        "Filme", 1997, tmp_path, api_key="k", session=session)
    assert ficha is not None
    assert descarte is None
    assert aviso is None


def test_ano_fonte_e_persistido_na_ficha(tmp_path):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes(title="Cure"),
    })
    ficha, _, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k",
                              session=session, ano_fonte="letterboxd")
    assert ficha["ano_fonte"] == "letterboxd"


# =====================================================================
# v1.9.29 — IMAGENS e RASTREABILIDADE (§3[F])
# =====================================================================

from espectro24.ficha import TETO_BACKDROPS, TMDB_IMAGE_LANGS  # noqa: E402


def _detalhes_com_imagens(poster_path="/poster.jpg", n_backdrops=3,
                          poster_nas_imagens=True, **kw):
    d = _detalhes(**kw)
    d["poster_path"] = poster_path
    d["images"] = {
        "posters": ([{"file_path": poster_path, "width": 1000,
                      "height": 1500, "iso_639_1": "pt"}]
                    if poster_nas_imagens and poster_path else []) + [
            {"file_path": "/outro.jpg", "width": 500, "height": 750,
             "iso_639_1": None}],
        "backdrops": [{"file_path": f"/bd{i}.jpg", "width": 1920,
                       "height": 1080} for i in range(n_backdrops)],
    }
    return d


def _ficha_com_imagens(tmp_path, **kw):
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes_com_imagens(**kw),
    })
    ficha, _, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    return ficha, session


def test_a_chamada_de_detalhes_e_UNICA_e_pede_credits_e_images(tmp_path):
    """Custo marginal de rede ZERO: `images` entra no mesmo
    `append_to_response` que já trazia `credits` — nenhuma requisição nova."""
    _ficha, session = _ficha_com_imagens(tmp_path)
    detalhes = [(u, p) for u, p in session.calls if "movie/" in u]
    assert len(detalhes) == 1, "houve mais de uma chamada de detalhes"
    params = detalhes[0][1]
    assert params["append_to_response"] == "credits,images"
    assert params["include_image_language"] == TMDB_IMAGE_LANGS


def test_include_image_language_esta_presente_e_e_o_da_constante(tmp_path):
    """A razão está medida no comentário de `TMDB_IMAGE_LANGS`: sem este
    parâmetro, `language=pt-BR` filtra o bloco de imagens e `backdrops` volta
    VAZIO para filmes com pouca cobertura pt-BR — o sintoma parece "este
    filme não tem imagens". O teste trava o parâmetro, não a medição.

    E o valor é `pt`, NÃO `pt-BR`: o parâmetro aceita ISO-639-1, e um código
    de localidade é ignorado em silêncio (7 dos 9 filmes sondados perdiam as
    dimensões do pôster com `pt-BR,null`). Uma regressão para `pt-BR` aqui
    voltaria a produzir um dado faltando sem nenhum erro — daí o teste."""
    assert TMDB_IMAGE_LANGS == "pt,null"


def test_o_poster_e_o_poster_path_do_proprio_tmdb(tmp_path):
    """A cascata (pt-BR → sem idioma → original → melhor avaliado) já é o que
    o campo `poster_path` da resposta de detalhes entrega, porque ele é
    sensível a `language`. Medido antes de decidir; não reimplementado."""
    ficha, _ = _ficha_com_imagens(tmp_path, poster_path="/escolhido.jpg")
    assert ficha["poster_path"] == "/escolhido.jpg"


def test_as_dimensoes_vem_de_images_posters_e_nao_sao_presumidas(tmp_path):
    """O `poster_path` não traz dimensões, e elas são OBRIGATÓRIAS para o
    frontend reservar a proporção antes de carregar (§3[E]). São procuradas
    na entrada correspondente de `images.posters`."""
    ficha, _ = _ficha_com_imagens(tmp_path)
    assert (ficha["poster_largura"], ficha["poster_altura"]) == (1000, 1500)


def test_poster_ausente_de_images_posters_deixa_dimensoes_nulas(tmp_path):
    """Ausência é estado válido: o frontend cai na proporção padrão."""
    ficha, _ = _ficha_com_imagens(tmp_path, poster_nas_imagens=False)
    assert ficha["poster_path"] == "/poster.jpg"
    assert ficha["poster_largura"] is None
    assert ficha["poster_altura"] is None


def test_filme_sem_poster_nenhum_e_estado_valido_nao_erro(tmp_path):
    ficha, _ = _ficha_com_imagens(tmp_path, poster_path=None, n_backdrops=0)
    assert ficha is not None and ficha["titulo"] == "Título PT"
    assert ficha["poster_path"] is None
    assert ficha["backdrop_paths"] == []


def test_backdrops_sao_coletados_e_respeitam_o_teto(tmp_path):
    ficha, _ = _ficha_com_imagens(tmp_path, n_backdrops=TETO_BACKDROPS + 7)
    assert len(ficha["backdrop_paths"]) == TETO_BACKDROPS
    assert ficha["backdrop_paths"][0] == "/bd0.jpg"


def test_tmdb_id_e_carimbo_de_obtencao_entram_na_ficha(tmp_path):
    """RASTREABILIDADE (§3[F]): o carimbo vale para a ficha INTEIRA — todos
    os campos vêm da mesma resposta, no mesmo instante. Ele existe porque os
    termos da API proíbem cachear por mais de 6 meses; a política de
    revalidação NÃO é construída aqui, só a data que a torna possível."""
    ficha, _ = _ficha_com_imagens(tmp_path)
    assert ficha["tmdb_id"] == 5
    assert ficha["tmdb_fetched_at"].endswith("+00:00")


def test_ficha_cacheada_sem_carimbo_e_refeita_e_nao_devolvida_capenga(tmp_path):
    """Ficha gravada ANTES da v1.9.29 não tem imagens. Devolvê-la como está
    produziria "este filme não tem pôster" para um filme que tem, em
    silêncio. A ausência do carimbo conta como MISS."""
    from espectro24.ficha import _cache_key
    antiga = {"titulo": "Título PT", "fonte": "tmdb", "ano": 1997}
    (tmp_path / f"{_cache_key('Cure', 1997)}.json").write_text(
        json.dumps(antiga), encoding="utf-8")

    ficha, _ = _ficha_com_imagens(tmp_path)
    assert ficha["poster_path"] == "/poster.jpg"
    assert ficha["tmdb_fetched_at"]


def test_fallback_en_us_nao_rebaixa_imagens(tmp_path):
    """Os fallbacks en-US (sinopse vazia / diretor não-latino) só querem
    `overview`/`credits`; o bloco de imagens é grande e não deve ser baixado
    duas vezes."""
    session = FakeTmdbSession({
        ("search", "Cure", 1997): {"results": [{"id": 5, "release_date": "1997-01-01"}]},
        ("movie", "pt-BR"): _detalhes_com_imagens(overview=""),
        ("movie", "en-US"): _detalhes(overview="An english overview."),
    })
    ficha, _, _ = buscar_ficha("Cure", 1997, tmp_path, api_key="k", session=session)
    en = [p for u, p in session.calls if p.get("language") == "en-US"]
    assert len(en) == 1
    assert en[0]["append_to_response"] == "credits"
    assert "include_image_language" not in en[0]
    # e as imagens da resposta pt-BR seguem intactas
    assert ficha["poster_path"] == "/poster.jpg"
    assert ficha["sinopse_fallback_en"] is True
