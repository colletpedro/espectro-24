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
from pathlib import Path
from typing import Any

import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_ENV_KEY = "TMDB_API_KEY"


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


def _montar_ficha(session, api_key: str, movie_id: int, detalhes: dict) -> dict[str, Any]:
    overview = detalhes.get("overview") or ""
    fallback_en = False
    if not overview:
        # §1.3: overview vazio em pt-BR -> fallback para en, sinalizado
        # (nunca silencioso) em vez de deixar a sinopse vazia.
        en = _buscar_detalhes(session, api_key, movie_id, language="en-US")
        overview = en.get("overview") or ""
        fallback_en = True
    data = detalhes.get("release_date") or ""
    ano = int(data[:4]) if data[:4].isdigit() else None
    return {
        "titulo": detalhes.get("title") or detalhes.get("original_title") or "",
        "sinopse_oficial": overview,
        "sinopse_fallback_en": fallback_en,
        "generos": [g["name"] for g in detalhes.get("genres") or []],
        "duracao_min": detalhes.get("runtime"),
        "diretor": _diretor(detalhes),
        "ano": ano,
        "fonte": "tmdb",
    }


def buscar_ficha(titulo: str, ano: int | None, cache_dir: str | Path,
                 api_key: str | None = None,
                 session=None) -> tuple[dict[str, Any] | None, str | None]:
    """Ponto de entrada. Retorna `(ficha, aviso)`:
    - sucesso: `(dict, None)`.
    - filme não encontrado / API indisponível / chave ausente: `(None, texto_do_aviso)`.

    NUNCA levanta — falha de ficha é sempre reportada como aviso, o
    pipeline segue sem ela (§1.2). "Não encontrado" também é cacheado (para
    não regastar a mesma busca vazia), mas falhas de rede/HTTP não são —
    podem ser transitórias e vale tentar de novo na próxima execução.
    """
    cache_dir = Path(cache_dir)
    path = cache_dir / f"{_cache_key(titulo, ano)}.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("nao_encontrado"):
            return None, f"TMDB: nenhum resultado para {titulo!r} ({ano}) [cache]."
        return cached, None

    key = api_key or os.environ.get(TMDB_ENV_KEY)
    if not key:
        return None, f"{TMDB_ENV_KEY} não definida no ambiente — ficha pulada."

    sess = session or requests

    try:
        movie_id = _resolver_id(sess, key, titulo, ano)
        if movie_id is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"nao_encontrado": True}), encoding="utf-8")
            return None, f"TMDB: nenhum resultado para {titulo!r} ({ano})."
        detalhes = _buscar_detalhes(sess, key, movie_id)
        ficha = _montar_ficha(sess, key, movie_id, detalhes)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        return ficha, None
    except (requests.RequestException, FichaError) as e:
        return None, f"TMDB indisponível ({e}) — ficha pulada."
