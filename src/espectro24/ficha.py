"""[NOVO v1.3.0] Ficha técnica do filme via TMDB — dado aditivo, opcional.

Busca `/search/movie` (query + year) para resolver o ID, depois
`/movie/{id}` com `language=pt-BR` e `append_to_response=credits` para
extrair título pt-BR, sinopse oficial, gêneros, duração, diretor e ano.

Cache em disco (mesmo padrão do cache do Letterboxd em `fetcher.py`: chave
determinística, nunca rebusca filme já buscado). Falha da API (chave
ausente, rede, HTTP, sem resultado) NUNCA levanta para o chamador — a ficha
é aditiva por decisão de design (SPEC §1.2): o pipeline segue sem ela, com
um aviso.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import requests

from .fetcher import AntiBotError, FetchError
from .urls import film_page_cache_key, film_page_url

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_ENV_KEY = "TMDB_API_KEY"

_ANO_RE_CANDIDATOS = (
    re.compile(r"/films/year/(\d{4})/"),
    re.compile(r'og:title"\s+content="[^"]*\((\d{4})\)'),
)


class FichaError(RuntimeError):
    """Falha ao consultar a API do TMDB — sempre capturada internamente por
    `buscar_ficha`; nunca deve escapar para o pipeline (a ficha é aditiva)."""


def titulo_ano_de_slug(slug: str) -> tuple[str, int | None]:
    """Deriva (título, ano) a partir do slug do Letterboxd, quando não há
    título/ano mais preciso disponível (ex.: `--reuse-synthesis`, `--slug`
    direto sem busca prévia).

    Slug com sufixo `-YYYY` (ex. 'the-invite-2026') -> ano extraído do
    próprio slug, título é o resto com hífens virando espaços. Slug sem
    sufixo de ano (ex. 'cure', 'cidade-de-deus') -> ano None; a
    desambiguação nesse caso depende só do título (risco documentado —
    ver SPEC §1.3/§1.4 e `--titulo`/`--ano` no CLI como escape hatch)."""
    m = re.match(r"^(.*)-(\d{4})$", slug)
    if m:
        return m.group(1).replace("-", " "), int(m.group(2))
    return slug.replace("-", " "), None


def resolver_ano_letterboxd(fetcher, slug: str) -> int | None:
    """[v1.7.0] Fallback de ano quando o slug não o carrega (ex. 'cure').

    Busca a página principal do filme no Letterboxd (mesmo `fetcher`, mesmo
    cache/delay/headers já usados pelo resto do pipeline — 1 requisição,
    cacheada depois) e extrai o ano de lançamento por regex, sem depender de
    nenhum parser HTML dedicado: primeiro tenta o link `/films/year/YYYY/`
    (presente na ficha técnica da página, aponta pro catálogo daquele ano),
    e cai para o `<meta property="og:title">` (formato "Título (YYYY)") se o
    primeiro não bater. Falha de rede/HTTP/ausência de ano -> None (nunca
    levanta; a resolução de ano é best-effort, igual à ficha em si).
    """
    try:
        html = fetcher.get(film_page_url(slug), film_page_cache_key(slug))
    except (AntiBotError, FetchError, requests.RequestException):
        return None
    for padrao in _ANO_RE_CANDIDATOS:
        m = padrao.search(html)
        if m:
            return int(m.group(1))
    return None


def _cache_key(titulo: str, ano: int | None) -> str:
    chave = re.sub(r"[^a-z0-9]+", "_", titulo.lower()).strip("_")
    return f"{chave}_{ano}" if ano else chave


def _get_json(session, url: str, params: dict) -> dict:
    resp = session.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise FichaError(f"{url} -> HTTP {resp.status_code}")
    return resp.json()


def _resolver_id(session, api_key: str, titulo: str, ano: int | None) -> int | None:
    params = {"api_key": api_key, "query": titulo, "language": "pt-BR"}
    if ano:
        params["year"] = ano
    data = _get_json(session, f"{TMDB_BASE}/search/movie", params)
    resultados = data.get("results") or []
    if not resultados:
        return None
    if ano:
        # Desambiguação por ano (§1.3): entre os candidatos com release_date
        # no ano pedido — o parâmetro `year` da API já filtra a maioria dos
        # casos, mas devolve mais de um candidato do MESMO ano quando o
        # título é comum (ex.: "Cure" 1997 devolve o filme de Kiyoshi
        # Kurosawa E um documentário obscuro de mesmo ano). Entre esses,
        # prefere o de maior `popularity` (proxy de relevância do TMDB) em
        # vez do primeiro da lista — a ordem da API não é por relevância
        # quando o filtro de ano está ativo; medido ao vivo: o documentário
        # tinha popularity=0.28/votes=1 contra popularity=3.79/votes=820 do
        # filme correto.
        candidatos_do_ano = [
            r for r in resultados if (r.get("release_date") or "")[:4] == str(ano)
        ]
        if candidatos_do_ano:
            melhor = max(candidatos_do_ano, key=lambda r: r.get("popularity") or 0)
            return melhor["id"]
    return resultados[0]["id"]


def _buscar_detalhes(session, api_key: str, movie_id: int,
                     language: str = "pt-BR") -> dict[str, Any]:
    params = {"api_key": api_key, "language": language,
              "append_to_response": "credits"}
    return _get_json(session, f"{TMDB_BASE}/movie/{movie_id}", params)


def _diretor(detalhes: dict) -> str | None:
    crew = (detalhes.get("credits") or {}).get("crew") or []
    for c in crew:
        if c.get("job") == "Director":
            return c.get("name")
    return None


def _e_escrita_latina(nome: str) -> bool:
    """True se o nome usa escrita latina (v1.6.0).

    Checa só as LETRAS: espaços, hífens e pontos não dizem nada sobre o
    alfabeto. Um nome sem letra alguma conta como não-latino (não há o que
    exibir). Implementado sobre `unicodedata.name`, que traz o nome Unicode
    do caractere ("LATIN SMALL LETTER A" vs "CJK UNIFIED IDEOGRAPH-9ED2") —
    mais robusto que uma faixa de code points escrita à mão, e cobre
    diacríticos latinos (ç, é, ñ) sem lista de exceções.
    """
    letras = [c for c in nome if c.isalpha()]
    if not letras:
        return False
    for c in letras:
        try:
            if not unicodedata.name(c).startswith("LATIN"):
                return False
        except ValueError:      # caractere sem nome Unicode: conservador
            return False
    return True


def _montar_ficha(session, api_key: str, movie_id: int, detalhes: dict) -> dict[str, Any]:
    overview = detalhes.get("overview") or ""
    fallback_en = False
    detalhes_en: dict[str, Any] | None = None
    if not overview:
        # §1.3: overview vazio em pt-BR -> fallback para en, sinalizado
        # (nunca silencioso) em vez de deixar a sinopse vazia.
        detalhes_en = _buscar_detalhes(session, api_key, movie_id, language="en-US")
        overview = detalhes_en.get("overview") or ""
        fallback_en = True

    # v1.6.0 — diretor em escrita latina. O TMDB devolve o nome no alfabeto
    # nativo quando a localidade pt-BR não tem tradução: `cure` vinha com
    # "黒沢清", que foi parar na narrativa publicada. O `credits` de en-US
    # traz a transliteração ("Kiyoshi Kurosawa"). Só busca en-US se o nome
    # pt-BR não for latino E ainda não tivermos os detalhes en (reaproveita
    # a resposta do fallback de sinopse quando ela já existe) — no pior caso
    # é 1 requisição extra, e só para filmes nessa condição.
    diretor = _diretor(detalhes)
    diretor_transliterado = False
    if diretor and not _e_escrita_latina(diretor):
        if detalhes_en is None:
            detalhes_en = _buscar_detalhes(session, api_key, movie_id,
                                           language="en-US")
        diretor_en = _diretor(detalhes_en)
        if diretor_en and _e_escrita_latina(diretor_en):
            diretor = diretor_en
            diretor_transliterado = True

    data = detalhes.get("release_date") or ""
    ano = int(data[:4]) if data[:4].isdigit() else None
    return {
        "titulo": detalhes.get("title") or detalhes.get("original_title") or "",
        "sinopse_oficial": overview,
        "sinopse_fallback_en": fallback_en,
        "generos": [g["name"] for g in detalhes.get("genres") or []],
        "duracao_min": detalhes.get("runtime"),
        "diretor": diretor,
        # telemetria: o nome exibido veio do credits en-US porque o pt-BR
        # não estava em escrita latina (visível, nunca silencioso)
        "diretor_transliterado": diretor_transliterado,
        "ano": ano,
        "fonte": "tmdb",
    }


def buscar_ficha(titulo: str, ano: int | None, cache_dir: str | Path,
                 api_key: str | None = None,
                 session=None,
                 ano_fonte: str | None = None,
                 ) -> tuple[dict[str, Any] | None, str | None, dict[str, Any] | None]:
    """Ponto de entrada. Retorna `(ficha, aviso, ficha_descartada)`:
    - sucesso: `(dict, None, None)` — `dict` carrega `ano_fonte` (v1.7.0).
    - filme não encontrado / API indisponível / chave ausente:
      `(None, texto_do_aviso, None)`.
    - resolvido no TMDB mas com ano divergente do esperado (v1.7.0, guarda
      de sanidade — §1.2): `(None, texto_do_aviso, {"motivo": ...})`.

    NUNCA levanta — falha de ficha é sempre reportada como aviso, o
    pipeline segue sem ela (§1.2). "Não encontrado" também é cacheado (para
    não regastar a mesma busca vazia), mas falhas de rede/HTTP não são —
    podem ser transitórias e vale tentar de novo na próxima execução. A
    ficha descartada por divergência de ano também NÃO é cacheada — melhor
    tentar de novo (ex. com um `titulo`/`ano` mais preciso) do que travar
    numa rejeição antiga.
    """
    cache_dir = Path(cache_dir)
    path = cache_dir / f"{_cache_key(titulo, ano)}.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("nao_encontrado"):
            return None, f"TMDB: nenhum resultado para {titulo!r} ({ano}) [cache].", None
        return cached, None, None

    key = api_key or os.environ.get(TMDB_ENV_KEY)
    if not key:
        return None, f"{TMDB_ENV_KEY} não definida no ambiente — ficha pulada.", None

    sess = session or requests

    try:
        movie_id = _resolver_id(sess, key, titulo, ano)
        if movie_id is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"nao_encontrado": True}), encoding="utf-8")
            return None, f"TMDB: nenhum resultado para {titulo!r} ({ano}).", None
        detalhes = _buscar_detalhes(sess, key, movie_id)
        ficha = _montar_ficha(sess, key, movie_id, detalhes)

        # v1.7.0 — guarda de sanidade (§1.2): o ano é o sinal mais barato e
        # confiável de que o TMDB resolveu para o filme certo. Se o `ano`
        # esperado (derivado do slug/Letterboxd/--ano, NUNCA do próprio
        # resultado do TMDB) divergir em mais de 1 do ano que o TMDB
        # devolveu, é sinal de desambiguação errada (caso real: "cure" sem
        # ano resolveu para "The Cure" 2026 em vez de "Cure" 1997, uma
        # divergência de quase 30 anos). Descarta a ficha inteira — melhor
        # nenhuma ficha do que a ficha de outro filme.
        if ano is not None and ficha.get("ano") is not None \
                and abs(ficha["ano"] - ano) > 1:
            descarte = {
                "motivo": "ano_divergente",
                "esperado": ano,
                "recebido": ficha["ano"],
            }
            aviso = (f"TMDB: ficha descartada para {titulo!r} — ano divergente "
                    f"(esperado {ano}, TMDB devolveu {ficha['ano']}).")
            return None, aviso, descarte

        ficha["ano_fonte"] = ano_fonte
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        return ficha, None, None
    except (requests.RequestException, FichaError) as e:
        return None, f"TMDB indisponível ({e}) — ficha pulada.", None
