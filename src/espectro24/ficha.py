"""[NOVO v1.3.0] Ficha técnica do filme via TMDB — dado aditivo, opcional.

Busca `/search/movie` (query + year) para resolver o ID, depois
`/movie/{id}` com `language=pt-BR` e `append_to_response=credits,images` para
extrair título pt-BR, sinopse oficial, gêneros, duração, diretor e ano — e,
desde a v1.9.29, `tmdb_id`, o carimbo de obtenção, o `poster_path` com suas
dimensões, e a lista de `backdrop_paths` (COLETADA e NÃO renderizada).

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .fetcher import AntiBotError, FetchError
from .urls import film_page_cache_key, film_page_url

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_ENV_KEY = "TMDB_API_KEY"

# [v1.9.29] Imagens — ver SPEC §3[F], "Imagens (v1.9.29)".
#
# `include_image_language` é OBRIGATÓRIO, e a razão foi MEDIDA ao vivo contra
# a API antes de fixar: `language=pt-BR` filtra também o bloco `images`, e a
# esmagadora maioria dos backdrops não tem idioma declarado. Sem o parâmetro,
# `images.backdrops` volta VAZIO para filmes com pouca cobertura pt-BR e o
# sintoma parece "este filme não tem imagens". Medido em 2026-08-27:
#
#   eighth-grade (489925)          sem: 1 pôster,  0 backdrops | com: 2,  18
#   the-invite-2026 (950028)       sem: 4 pôsteres, 0 backdrops | com: 10, 21
#   o curta experimental (1079736) sem: 0 e 0                   | com: 1,  0
#   the-godfather (238)            sem: 6 pôsteres, 4 backdrops | com: 21, 102
#
# **O VALOR É `pt`, NÃO `pt-BR` — e isto é uma correção medida, não um
# detalhe de estilo.** O parâmetro aceita códigos ISO-639-1, e um código de
# LOCALIDADE é ignorado em SILÊNCIO: com `pt-BR,null` só o degrau `null`
# sobrevive, e o `pt` some. O sintoma não é um erro — é pior, é um dado que
# falta sem avisar. Medido em 9 filmes do catálogo: com `pt-BR,null`, 7 deles
# (aftersun, anatomy-of-a-fall, cats-2019, cure, hereditary, the-northman,
# wonka) ficaram SEM as dimensões do pôster, porque o `poster_path` escolhido
# pelo TMDB é uma arte `iso_639_1='pt'` que o filtro tinha descartado; com
# `pt,null`, nenhum ficou. Os backdrops também sobem um pouco (a diferença é
# pequena porque quase todos são `null` mesmo).
TMDB_IMAGE_LANGS = "pt,null"

# Teto de backdrops guardados por filme. COLETADOS E NÃO RENDERIZADOS (§3[F]):
# a galeria não existe na v1 porque o TMDB não garante que um backdrop seja
# livre de spoiler, e "0 spoilers" é a promessa central (§0). 10 é folga
# confortável para qualquer curadoria futura (o teto real do TMDB passa de
# 100 num filme popular) sem inchar os `resultado/*.json` — a lista é de
# strings curtas, e 10 × ~32 bytes é ruído no documento.
TETO_BACKDROPS = 10

_ANO_RE_CANDIDATOS = (
    re.compile(r"/films/year/(\d{4})/"),
    re.compile(r'og:title"\s+content="[^"]*\((\d{4})\)'),
)


def _agora_utc() -> str:
    """Carimbo de obtenção, ISO-8601 UTC com segundos.

    Função própria (em vez de `datetime.now()` inline) para que o teste possa
    substituí-la e comparar fichas byte a byte sem que o relógio entre na
    comparação.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _ano_do_bruto(meta_bruto: dict | None) -> int | None:
    """O ano gravado no `meta.json` do superset, se houver e for utilizável.

    Tolerante de propósito: bruto coletado ANTES da v1.9.12 não tem a chave,
    e um valor inválido (0, "", None, texto) tem de degradar para o caminho
    antigo em vez de estourar — o ano é aditivo, como toda a ficha.
    """
    if not meta_bruto:
        return None
    try:
        ano = int(meta_bruto.get("ano_lancamento") or 0)
    except (TypeError, ValueError):
        return None
    return ano or None


def resolver_ano(fetcher, slug: str, *, ano_explicito: int | None = None,
                 meta_bruto: dict | None = None) -> tuple[int | None, str | None]:
    """`(ano, fonte)` do filme, na ordem de precedência da v1.9.12.

    `--ano` explícito → **bruto** → sufixo do slug → Letterboxd (rede) →
    `(None, None)`.

    **O degrau do BRUTO é a correção desta versão.** Defeito medido em
    `joker-folie-a-deux`: slug sem ano + `--offline` ⇒ o fallback de rede
    não roda ⇒ a guarda da v1.7.0 recusa a ficha sem ano (corretamente) ⇒ o
    movimento 1 é omitido e a narrativa nunca diz que filme é — em
    silêncio. 21 dos 35 slugs do catálogo não têm ano no nome.

    O ano é dado ESTÁVEL, buscado uma vez; guardá-lo no superset é a mesma
    lógica que já vale para o histograma (§3[B']: "qualquer reprocessamento
    custa zero rede"). `fetcher=None` é aceito — a rede é o ÚLTIMO recurso,
    não um pré-requisito para os degraus anteriores.
    """
    if ano_explicito is not None:
        return ano_explicito, "argumento"
    do_bruto = _ano_do_bruto(meta_bruto)
    if do_bruto is not None:
        return do_bruto, "bruto"
    _, do_slug = titulo_ano_de_slug(slug)
    if do_slug is not None:
        return do_slug, "slug"
    if fetcher is None:
        return None, None
    da_rede = resolver_ano_letterboxd(fetcher, slug)
    return (da_rede, "letterboxd") if da_rede is not None else (None, None)


def meta_com_ano(meta: dict, fetcher, slug: str) -> dict:
    """`meta` do superset com `ano_lancamento`/`ano_fonte` gravados.

    Gancho de coleta (§3[B']). IDEMPOTENTE: recoletar um filme que já tem o
    ano não gasta requisição nenhuma.

    **Ausência não é gravada.** Um `ano_lancamento: null` no meta seria lido
    pela próxima execução como "já tentei, não existe", e ela não tentaria
    de novo — a chave simplesmente não entra quando não resolve, e a
    execução seguinte COM rede completa o dado.
    """
    if _ano_do_bruto(meta) is not None:
        return meta
    ano, fonte = resolver_ano(fetcher, slug, meta_bruto=meta)
    if ano is None:
        return meta
    return {**meta, "ano_lancamento": ano, "ano_fonte": fonte}


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
                     language: str = "pt-BR",
                     com_imagens: bool = True) -> dict[str, Any]:
    """Detalhes do filme numa CHAMADA ÚNICA.

    [v1.9.29] `images` entra no MESMO `append_to_response` que já trazia
    `credits` — custo marginal de rede zero, nenhuma requisição nova. O
    `include_image_language` acompanha e é o que faz o bloco vir preenchido
    (ver `TMDB_IMAGE_LANGS`).

    `com_imagens=False` existe para os fallbacks en-US (sinopse vazia,
    diretor não-latino): eles só querem `overview`/`credits`, e o bloco de
    imagens é grande — não há por que baixá-lo duas vezes.
    """
    params = {"api_key": api_key, "language": language,
              "append_to_response": "credits,images" if com_imagens else "credits"}
    if com_imagens:
        params["include_image_language"] = TMDB_IMAGE_LANGS
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


def _imagens(detalhes: dict) -> dict[str, Any]:
    """Os campos de imagem da ficha, derivados da resposta de detalhes.

    **O PÔSTER É O DO PRÓPRIO TMDB, e isso foi medido antes de decidir.** A
    cascata pedida (pt-BR → arte sem idioma → idioma original → melhor
    avaliado) já é o que o campo `poster_path` da resposta de detalhes
    entrega: ele é sensível a `language`, então com `language=pt-BR` devolve
    o pôster pt-BR quando existe e cai sozinho para a arte sem idioma quando
    não existe. Medido em 2026-08-27: `napoleon-2023` devolve
    `/2UY2xfk…` (iso_639_1='pt') em pt-BR e `/ytFOXyg…` em en-US — a
    localidade está sendo respeitada; o curta experimental (1079736), que só
    tem uma arte SEM idioma, devolve a mesma imagem nas duas localidades.
    Reimplementar a cascata seria reescrever, com menos informação, uma
    escolha que a API já faz — e divergir dela em silêncio no dia em que ela
    mudasse de critério.

    **As DIMENSÕES, essas, o campo não traz** — e elas são obrigatórias para
    o frontend reservar a proporção antes de carregar (§3[E]). Por isso o
    `poster_path` escolhido é procurado dentro de `images.posters`, que traz
    `width`/`height` reais. Não são sempre 2:3: o curta experimental mede
    505×750 (razão 0,673), não 2000×3000. Quando o caminho não aparece na
    lista (não observado nos 5 filmes sondados, mas possível), as dimensões
    ficam ausentes e o frontend cai na proporção padrão — ausência é estado
    válido, nunca erro.
    """
    imagens = detalhes.get("images") or {}
    poster_path = detalhes.get("poster_path") or None

    largura = altura = None
    if poster_path:
        for p in imagens.get("posters") or []:
            if p.get("file_path") == poster_path:
                largura = p.get("width")
                altura = p.get("height")
                break

    # COLETADOS E NÃO RENDERIZADOS — ver `TETO_BACKDROPS`. A ordem é a que a
    # API devolve (ela já ordena por avaliação); o corte é no fim.
    backdrops = [
        b["file_path"] for b in (imagens.get("backdrops") or [])
        if b.get("file_path")
    ][:TETO_BACKDROPS]

    return {
        "poster_path": poster_path,
        "poster_largura": largura,
        "poster_altura": altura,
        "backdrop_paths": backdrops,
    }


def _montar_ficha(session, api_key: str, movie_id: int, detalhes: dict) -> dict[str, Any]:
    overview = detalhes.get("overview") or ""
    fallback_en = False
    detalhes_en: dict[str, Any] | None = None
    if not overview:
        # §1.3: overview vazio em pt-BR -> fallback para en, sinalizado
        # (nunca silencioso) em vez de deixar a sinopse vazia.
        detalhes_en = _buscar_detalhes(session, api_key, movie_id, language="en-US",
                                       com_imagens=False)
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
                                           language="en-US", com_imagens=False)
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
        # [v1.9.29] Identidade e RASTREABILIDADE. `tmdb_fetched_at` vale para
        # a ficha INTEIRA — título, sinopse, diretor, gêneros, duração,
        # pôster e backdrops vêm todos da mesma resposta, no mesmo instante,
        # e um carimbo por campo seria a mesma data repetida sete vezes.
        #
        # POR QUE ELE EXISTE (§3[F], "Rastreabilidade e o teto de 6 meses"):
        # os termos da API do TMDB proíbem cachear por mais de 6 meses
        # qualquer informação obtida através dela, e o projeto guarda ficha
        # indefinidamente em `resultado/*.json` desde a v1.3.0. A limitação é
        # PRÉ-EXISTENTE — os pôsteres só a tornam visível. Esta versão NÃO
        # constrói cache, revalidação, expiração nem coleta de lixo: entrega
        # só a data, que é o que torna uma política de revalidação possível
        # depois. Sem ela não há nem como saber o que está vencido.
        "tmdb_id": movie_id,
        "tmdb_fetched_at": _agora_utc(),
        **_imagens(detalhes),
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
        # [v1.9.29] Ficha cacheada ANTES desta versão não tem os campos de
        # imagem nem o carimbo de obtenção. Devolvê-la como está produziria o
        # pior sintoma possível — "este filme não tem pôster" para um filme
        # que tem —, e sem nenhum aviso. `tmdb_fetched_at` é o marcador: sua
        # ausência conta como MISS e a entrada é refeita por cima. Não é
        # expiração (que esta versão não constrói, por decisão); é só uma
        # entrada de formato antigo sendo reconhecida como incompleta.
        if cached.get("tmdb_fetched_at"):
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
