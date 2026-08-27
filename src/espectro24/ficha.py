"""[NOVO v1.3.0] Ficha técnica do filme via TMDB — dado aditivo, opcional.

Busca `/search/movie` (query + year) para resolver o ID, depois
`/movie/{id}` com `language=pt-BR` e `append_to_response=credits,images` para
extrair título pt-BR, sinopse oficial, gêneros, duração, diretor e ano — e,
desde a v1.9.29, `tmdb_id`, o carimbo de obtenção, o `poster_path` com suas
dimensões, e a lista de `backdrop_paths`. Na v1.9.30 entram o BACKDROP
ESCOLHIDO (um só, com dimensões — o topo da página do filme) e o PÔSTER SEM
TEXTO (arte-chave `iso_639_1: null`, campo próprio, variante do frontend).

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

# Teto de backdrops guardados por filme. 10 é folga confortável (o teto real
# do TMDB passa de 100 num filme popular — medido: `wicked-2024` tem 257)
# sem inchar os `resultado/*.json`: a lista é de strings curtas, e
# 10 × ~32 bytes é ruído no documento.
#
# [v1.9.30] A LISTA CONTINUA COLETADA E NÃO RENDERIZADA; o que passou a ser
# renderizado é UM backdrop, o ESCOLHIDO, no topo da página do filme. Não
# existe galeria, e a distinção não é retórica: `backdrop_paths[]` segue
# sendo dado guardado que nenhum arquivo do frontend percorre. **A escolha
# sai de dentro desta lista** (`backdrops[:TETO_BACKDROPS]`), e não do
# acervo inteiro, para que "qual imagem esta página mostra" continue
# respondível olhando só o JSON publicado.
#
# **ISTO É EXCEÇÃO EXPLÍCITA AO PRINCÍPIO ANTI-SPOILER DO §0**, tomada pelo
# dono do projeto com o trade-off na mesa. O TMDB não garante que um
# backdrop seja livre de spoiler — é quadro do filme, e pode ser do terceiro
# ato. O registro por extenso (o que se ganha, o que se perde, por que não
# há como maquiar a tensão) está em SPEC §3[E], "O BACKDROP no topo da
# página do filme".
TETO_BACKDROPS = 10

# [v1.9.30] A ORDEM DE PREFERÊNCIA ENTRE IMAGENS, e por que ela é do CÓDIGO
# e não da API. `images.backdrops` chega ordenada por `vote_average`
# decrescente, mas isso NÃO é uma ordem total: empates são comuns e a API
# não declara critério de desempate. Medido nos 35 (2026-08-27): em 3 filmes
# (`eighth-grade`, `friday-the-13th-2009`, `wicked-2024`) o primeiro da
# lista NÃO é o que esta ordem escolhe. Confiar na posição faria a imagem de
# um filme publicado poder mudar entre duas execuções sem que nada no dado
# tivesse mudado — que é exatamente o que "regra determinística" proíbe.
#
# Os degraus, do mais forte ao mais fraco:
#
#   1. SEM TEXTO SOBREPOSTO (`iso_639_1 is None`) vem antes de arte com
#      idioma declarado. Uma imagem com `iso_639_1='pt'` é key art de
#      campanha: traz o título tratado e o bloco de elenco. Medido: afeta 2
#      dos 35 (`joker-folie-a-deux`, `longlegs`), e nos dois o vencedor sem
#      a regra seria uma peça de marketing com "PHOENIX GAGA / JOKER" gravado
#      — logo ACIMA do par ano→título que a própria página escreve. É
#      PREFERÊNCIA, nunca filtro: um filme cujas imagens sejam todas `pt`
#      continua tendo imagem.
#   2. `vote_average` decrescente — a única curadoria humana que o TMDB
#      expõe sobre imagem. É o degrau que responde "melhor avaliada".
#   3. `vote_count` decrescente — mesma nota, mais gente confirmando. Caso
#      real em `the-godfather`: 4,934 com 30 votos contra 4,934 com 15.
#   4. `width` decrescente — sobrando empate, mais pixels.
#   5. `file_path` crescente — o degrau que fecha a ORDEM TOTAL. Sem ele,
#      duas imagens idênticas nos quatro critérios acima dependeriam de novo
#      da posição na resposta.
#
# Resolução NÃO é o primeiro degrau de propósito: `width` sozinho escolhe o
# maior arquivo, não o melhor quadro, e o acervo é cheio de 3840×2160 sem
# voto nenhum.


def _ordem_imagem(img: dict, *, preferir_sem_texto: bool) -> tuple:
    """Chave de ordenação — ordem TOTAL, ver o comentário acima.

    Tolerante a campo ausente (`vote_average`, `width`): o TMDB sempre os
    manda, mas um `None` aqui viraria TypeError na comparação, e a ficha é
    aditiva — ela nunca derruba o pipeline por causa de uma imagem.
    """
    sem_texto = 0 if img.get("iso_639_1") is None else 1
    return (
        sem_texto if preferir_sem_texto else 0,
        -(img.get("vote_average") or 0),
        -(img.get("vote_count") or 0),
        -(img.get("width") or 0),
        img.get("file_path") or "",
    )


def _melhor(imagens: list[dict], *, preferir_sem_texto: bool = False,
            so_sem_texto: bool = False) -> dict | None:
    """A melhor imagem da lista pela ordem acima, ou `None` se não houver.

    `so_sem_texto=True` FILTRA (arte-chave sem texto, §3[F] v1.9.30);
    `preferir_sem_texto=True` só PRIORIZA.
    """
    candidatas = [i for i in imagens if i.get("file_path")]
    if so_sem_texto:
        candidatas = [i for i in candidatas if i.get("iso_639_1") is None]
    if not candidatas:
        return None
    return min(candidatas, key=lambda i: _ordem_imagem(
        i, preferir_sem_texto=preferir_sem_texto))


# As chaves que uma entrada de cache precisa TER para ser considerada
# completa. Presença, não verdade: `backdrop_path: None` é resposta válida
# (filme sem backdrop) e não deve forçar uma nova requisição a cada execução.
_CHAVES_COMPLETUDE = (
    "tmdb_fetched_at", "poster_path", "backdrop_path", "poster_sem_texto_path",
)


def _entrada_completa(cached: dict) -> bool:
    return bool(cached.get("tmdb_fetched_at")) and all(
        k in cached for k in _CHAVES_COMPLETUDE)

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

    **[v1.9.30] Os DOIS campos novos, e o que os separa do `poster_path`.**
    O `backdrop_path` e o `poster_sem_texto_path` NÃO são escolhas que a API
    já faça por conta — não existe campo de topo para "o melhor backdrop"
    nem para "a arte sem texto" —, então aqui a escolha é do código, por uma
    ordem TOTAL e registrada (`_ordem_imagem`). É a diferença exata para o
    pôster: lá reimplementar a cascata seria refazer pior o que a API já
    faz; aqui não há nada para reaproveitar. Nenhuma requisição nova em
    nenhum dos dois casos — tudo sai do mesmo bloco `images`.
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

    # A LISTA continua coletada e não percorrida pelo frontend — ver
    # `TETO_BACKDROPS`. A ordem é a que a API devolve; o corte é no fim.
    lista_backdrops = (imagens.get("backdrops") or [])[:TETO_BACKDROPS]
    backdrops = [b["file_path"] for b in lista_backdrops if b.get("file_path")]

    # [v1.9.30] O BACKDROP ESCOLHIDO — UM, o do topo da página do filme.
    # Sai de DENTRO dos até 10 coletados (e não do acervo inteiro), pela
    # ordem total de `_ordem_imagem`, para que a pergunta "qual imagem esta
    # página mostra" seja respondível olhando só o JSON publicado: o
    # `backdrop_path` é sempre um dos itens de `backdrop_paths`.
    #
    # As DIMENSÕES vêm junto pelo mesmo motivo do pôster (§3[E]): sem elas o
    # frontend não reserva a proporção antes de carregar, e o ganho de CLS
    # zero da v1.9.29 regride. Ausência é estado válido — filme sem backdrop
    # nenhum cai no pôster, e sem os dois, no estado de ausência desenhado.
    escolhido = _melhor(lista_backdrops, preferir_sem_texto=True)

    # [v1.9.30] O PÔSTER SEM TEXTO — arte-chave sem bloco de créditos, sem
    # tagline e sem laurel de festival, que o TMDB serve com
    # `iso_639_1: null`. CAMPO PRÓPRIO: não substitui `poster_path`, que
    # continua sendo o do próprio TMDB (a cascata sensível a `language`, ver
    # a docstring acima). É variante alternável no frontend, e ausência
    # nunca bloqueia nada — filme sem arte sem texto usa o pôster normal.
    #
    # Aqui o `iso_639_1 is None` é FILTRO, não preferência: uma arte com
    # idioma declarado tem texto sobreposto por definição, e devolvê-la
    # neste campo seria devolver a coisa que ele existe para evitar.
    limpo = _melhor(imagens.get("posters") or [], so_sem_texto=True)

    return {
        "poster_path": poster_path,
        "poster_largura": largura,
        "poster_altura": altura,
        "backdrop_paths": backdrops,
        "backdrop_path": escolhido.get("file_path") if escolhido else None,
        "backdrop_largura": escolhido.get("width") if escolhido else None,
        "backdrop_altura": escolhido.get("height") if escolhido else None,
        "poster_sem_texto_path": limpo.get("file_path") if limpo else None,
        "poster_sem_texto_largura": limpo.get("width") if limpo else None,
        "poster_sem_texto_altura": limpo.get("height") if limpo else None,
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
        # Ficha cacheada por uma versão ANTERIOR não tem os campos de imagem
        # que a versão atual escreve. Devolvê-la como está produziria o pior
        # sintoma possível — "este filme não tem pôster"/"não tem backdrop"
        # para um filme que tem —, e sem nenhum aviso. Uma entrada
        # INCOMPLETA conta como MISS e é refeita por cima. Não é expiração
        # (que esta versão continua não construindo, por decisão); é uma
        # entrada de formato antigo sendo reconhecida como incompleta.
        #
        # [v1.9.30] A checagem deixou de ser o `tmdb_fetched_at` da v1.9.29 e
        # passou a ser a LISTA de chaves que a versão corrente escreve, por um
        # motivo aprendido nesta rodada: o carimbo já existia nas 35 entradas
        # em cache, então os campos novos desta versão teriam voltado
        # ausentes, em silêncio, exatamente o defeito que aquela regra existia
        # para evitar. Ao acrescentar campo de imagem, acrescente aqui.
        if _entrada_completa(cached):
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
