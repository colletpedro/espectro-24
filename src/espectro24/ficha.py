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

[v1.9.39] `galeria_stills` — mudança de escopo AUTORIZADA pelo dono do
produto: a galeria da página do filme mostra STILLS (backdrops 16:9), não
mais pôsteres alternativos (`galeria_posters`, v1.9.38, removido — não
convive com o campo novo). **Risco de spoiler ASSUMIDO explicitamente**:
nenhum filtro anti-spoiler é aplicado aqui, ao contrário de todo o resto do
produto (bullets filtrados, veredito proibido de citar reviravolta) — a
mesma exceção que já valia para o backdrop ESCOLHIDO do topo da página
(§3[E]), agora estendida a uma galeria inteira, com o mesmo trade-off
registrado e a mesma decisão: do dono, não do código.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from html import unescape
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .fetcher import AntiBotError, FetchError
from .identidade import VERSAO_CONTRATO_IDENTIDADE, tmdb_id_escolhido
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

# [v1.9.39] Teto da GALERIA DE STILLS (§3[F] — decisão registrada em ETAPA
# 0 antes de qualquer implementação, não palpite; mudança de escopo
# AUTORIZADA pelo dono: stills 16:9, não pôsteres — ver docstring do
# módulo).
#
# Medido ao vivo em 2026-09-04, os 35 filmes publicados, `/movie/{id}/images`
# SEM `include_image_language` (para pegar o TOTAL de verdade) e filtrado em
# código (`iso_639_1 is None` E aspect_ratio em [1.70, 1.85]): mediana de
# **69** stills por filme, mínimo histórico **0** (`talk-to-me-2022` ainda
# apontava para o curta errado de 3 min), máximo 257 (`wicked-2024`). Excluindo o
# curta, o PISO real do catálogo é 18 (`eighth-grade`) — bem acima de
# qualquer teto razoável; N não é limitado pela distribuição aqui, ao
# contrário da galeria de pôsteres (v1.9.38), onde `eighth-grade`/
# `cats-2019` raspavam o fundo do poço. **TETO_STILLS=8 mantido igual ao
# teto de pôsteres por decisão explícita do dono do produto**, apesar de o
# still 16:9 ser ~2,3× mais largo por item que o pôster 2:3 (proposta
# alternativa de N=6, por layout, foi feita e recusada).
#
# [v1.9.41] **8 → 16**, porque a galeria deixou de ser grade estática e
# virou FAIXA DE ROLAGEM CONTÍNUA (`faixa.js`), e numa faixa o teto deixa
# de ser uma pergunta de layout ("quantos cabem em duas linhas") e vira
# uma pergunta de PERÍODO: com poucos itens o ciclo fecha depressa e a
# repetição vira o efeito dominante, no lugar do movimento.
#
# A grandeza que decide é **quantas TELAS de material distinto a faixa
# guarda** — N dividido pelo número de itens visíveis de uma vez. Medido
# ao vivo (2026-09-06, coluna de leitura de 720px no desktop, item de
# 172px + 10px de gap → 3,96 itens visíveis):
#
#     teto | telas distintas | ciclo a 28px/s | sustentam | espalhamento
#        8 |            2,0  |           52 s |     34/34 |        33/34
#       12 |            3,0  |           78 s |     34/34 |        31/34
#       16 |            4,0  |          104 s |     33/34 |        30/34
#       20 |            5,1  |          130 s |     32/34 |        27/34
#       24 |            6,1  |          156 s |     31/34 |        24/34
#
# ("sustentam" = filmes cujo pool JÁ DEDUPLICADO tem ao menos `teto`
# itens; "espalhamento" = filmes com n ≥ 2·teto, o limiar em que
# `_amostra_espalhada` ainda garante que duas vizinhas do ranking não
# caem na mesma faixa.)
#
# **O critério, declarado: o maior teto que ainda entrega ≥ 4 telas de
# material distinto no desktop E preserva a garantia de espalhamento em
# ≥ 85% do catálogo.** 16 fecha os dois (4,0 telas; 30/34 = 88%); 20 já
# cai para 79% de espalhamento. O teto de 8 falha o primeiro critério com
# folga (2,0 telas) — é exatamente o sintoma que motivou a mudança.
#
# Custo aceito, medido: `eighth-grade` (pool deduplicado de 15) é o ÚNICO
# filme que não enche 16 — renderiza 15, e o piso continua em 3. Quatro
# filmes (`eighth-grade` 15, `cats-2019` 19, `the-invite-2026` 20,
# `anatomy-of-a-fall` 28) ficam abaixo de n ≥ 32 e perdem a garantia de
# espalhamento: neles, uma duplicata que o pHash não reconheceu (recall
# 0,830, ver `still_hash.py`) pode aparecer em posições vizinhas.
#
# O PESO não é o limite aqui: 16 × 13,3 kB (média medida de 40 stills
# publicados em `w300`) = 213 kB, bem abaixo do teto de ~1,5 MB por
# página. A duplicação da sequência que o loop da faixa faz NÃO dobra
# isso — as cópias reusam a mesma URL, servida do cache do navegador.
#
# [v1.9.42] **16 → 12**, porque a faixa MUDOU DE LUGAR: deixou de ser uma
# tira de miniaturas no rodapé e passou a ser o HERO, no topo da página
# (correção de escopo do dono). O item deixou de medir 172px e passou a
# medir a largura inteira da coluna — MEDIDO ao vivo em 2026-09-06:
# **720 × 405 no desktop, 375 × 211 no mobile**. Cabe ~1 por tela, não
# ~4, e as duas contas que fixavam o teto viraram outras.
#
# 1. TELAS DE MATERIAL DISTINTO. Com 1 item por tela, N telas = N itens.
#    O critério declarado na v1.9.41 (≥ 4 telas no desktop) passa a ser
#    atendido por qualquer teto ≥ 4 — ele deixa de ser o gargalo.
#
# 2. DURAÇÃO DA VOLTA. É esta que decide agora. A velocidade passou a ser
#    declarada em SEGUNDOS POR STILL (`faixa.js`), não em px/s, porque o
#    item mudou de tamanho e um px/s fixo daria ritmos diferentes em
#    desktop e mobile. A 12 s por still:
#
#        teto |  volta  | peso do ciclo (w1280) | peso (w780, mobile)
#           8 |  1min36 |               1,08 MB |             0,46 MB
#          10 |  2min00 |               1,35 MB |             0,58 MB
#          12 |  2min24 |               1,62 MB |             0,69 MB
#          16 |  3min12 |               2,17 MB |             0,92 MB
#
# **12 é o maior teto cujo peso de ciclo fica próximo do teto de ~1,5 MB
# por página em vez de 45% acima dele**, e entrega 12 telas distintas —
# o triplo do piso de 4 que a v1.9.41 declarou. 16 continuaria
# funcionando, mas custaria 2,17 MB por volta sem comprar nada que o
# critério de telas distintas peça.
#
# O peso NÃO é resolvido baixando a qualidade (decisão do dono: a
# nitidez do hero não regride) — é resolvido por CARREGAMENTO SOB
# DEMANDA: só os primeiros itens são buscados no carregamento da página e
# os seguintes chegam conforme a faixa avança, ver `montarHeroFaixa` em
# `poster.js`. Os números acima são o total de UMA VOLTA INTEIRA (2min24),
# não o custo de abrir a página.
TETO_STILLS = 12

# [v1.9.39] PISO da galeria — mesma lógica de `n < 10` na lei de margem
# (`config.py`, §2.5) e o mesmo valor da geração anterior (pôsteres,
# v1.9.38): abaixo de um mínimo, o dado não sustenta a coisa que ele
# estaria ali para mostrar, e a ausência é mais honesta que uma versão
# raquítica dela. `PISO_STILLS=3` é o piso ÓBVIO (menos que isso não enche
# nem uma linha da grade) e reaproveita o vocabulário que o projeto já usa
# para "dado de menos": abaixo dele a lista final (depois de ordenar,
# excluir o backdrop do hero e aplicar `TETO_STILLS`) é zerada, não
# truncada — a seção inteira desaparece (ver `galeriaBlock`, `filme.js`).
#
# Na medição original, nenhum longa caiu neste piso por escassez de still; o
# menor real (`eighth-grade`, 18) ficou bem acima de 3. O antigo vazio de
# `talk-to-me-2022` era consequência da ficha do curta errado, corrigida pela
# guarda de identidade da v1.9.49.
PISO_STILLS = 3

# [v1.9.49] Segunda checagem, independente do contrato de identidade.
#
# O ID declarado pelo Letterboxd (ou um override manual auditável) e a
# igualdade de título são a PROVA; duração não é. Mesmo assim, uma ficha com
# menos de 40 minutos é recusada inteira: o piso pega a coincidência rara em
# que ID/título parecem coerentes mas o objeto retornado é um curta. O caso
# histórico que motivou a redundância foi o match errado de 3 minutos de
# `talk-to-me-2022`. Nos outros 34 filmes medidos, a duração ia de 94 a 181.
GALERIA_DURACAO_MIN_FEATURE = 40

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


# [v1.9.40] O limiar e a distância vêm de `still_hash` (onde a matriz de
# acerto que os justifica está registrada). Só a GERAÇÃO de hash precisa de
# Pillow/imagehash; `distancia_phash` é aritmética de inteiro, então a dedup
# e os testes dela rodam num ambiente sem as libs de imagem.
from espectro24.still_hash import LIMIAR_PHASH, distancia as distancia_phash


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


def duracao_compativel_com_longa(duracao_min: int | None) -> bool:
    """`True` se `duracao_min` está no território de longa-metragem (§3[F]
    v1.9.38) — ver `GALERIA_DURACAO_MIN_FEATURE` para o porquê do piso.

    **NÃO CONFIRMA IDENTIDADE.** É a segunda checagem independente aplicada
    depois da prova Letterboxd→TMDB. ``False`` é o caminho seguro: a ficha
    inteira fica indisponível, em vez de publicar metadados plausíveis de um
    curta homônimo.
    """
    return duracao_min is not None and duracao_min >= GALERIA_DURACAO_MIN_FEATURE


def _still_16_9(b: dict) -> bool:
    """`True` se `b` (um item de `images.backdrops`) é 16:9 DE FATO — não
    só "está na lista de backdrops". Medido nos 35 (2026-09-04): o acervo
    de backdrop do TMDB tem exceções reais (ex. crops mais quadrados),
    então a proporção NOMINAL (é backdrop) não é garantia da proporção
    REAL, do mesmo jeito que o pôster não é sempre exatamente 2:3
    (`RAZAO_PADRAO`, `poster.js`). `[1.70, 1.85]` cobre 16:9 (1,778) com
    folga para arredondamento de pixel, sem aceitar um crop nitidamente
    diferente (21:9 = 2,33, 4:3 = 1,33).
    """
    w, h = b.get("width"), b.get("height")
    return bool(w and h and 1.70 <= (w / h) <= 1.85)


def _hashes_dos_candidatos(detalhes: dict, *, session=None) -> dict[str, str]:
    """`{file_path: phash}` das candidatas a still deste filme, ou `{}`.

    Hasheia SÓ o que já passou pelos filtros baratos de `_stills`
    (`iso_639_1 is None` e 16:9): metade do acervo de backdrop do TMDB cai
    aí, e baixar uma imagem para descobrir depois que ela não era
    candidata seria banda jogada fora. O hero NÃO é excluído aqui porque
    `_imagens` só o conhece depois — hashear um arquivo a mais é barato,
    e ele sai na filtragem de `_stills` do mesmo jeito.

    **Faz REDE** (uma imagem w300, ~20 kB, por candidata) — pela MESMA
    `session` que `buscar_ficha` já usa, e não por uma conexão própria: é
    isso que mantém o teste da ficha offline, já que a sessão dublê que
    ele injeta também atende estas requisições. É a única parte da ficha
    que faz rede além da própria chamada ao TMDB — todo o resto sai da resposta que
    `buscar_ficha` já tinha. É a conta pela dedup, e ela é paga UMA vez:
    o cache em disco (`still_hash.hashes_de`) sobrevive entre execuções.
    Qualquer falha (sem rede, sem Pillow, imagem corrompida) volta como
    ausência, e ausência só desliga a dedup — nunca derruba a ficha.
    """
    candidatas = [b.get("file_path") for b in
                  ((detalhes.get("images") or {}).get("backdrops") or [])
                  if b.get("file_path") and b.get("iso_639_1") is None
                  and _still_16_9(b)]
    if not candidatas:
        return {}
    try:
        from espectro24.still_hash import hashes_de
        raiz = Path(__file__).resolve().parents[2]
        return hashes_de(candidatas, session=session,
                         memo=raiz / "dados" / "cache" / "_stills_phash.json")
    except Exception:
        return {}


def _deduplicar(candidatos: list[dict], hashes: dict[str, str] | None,
                *, limiar: int = LIMIAR_PHASH) -> list[dict]:
    """Colapsa em UM item cada grupo de candidatas que leem como a mesma
    imagem, pelo pHash (§3[F] v1.9.40 — o critério e o limiar são MEDIDOS,
    ver a docstring de `still_hash.py`).

    `hashes` é `{file_path: phash_hex}` INJETADO — a função é pura e não
    baixa nada. Sem `hashes` (ou com uma candidata fora dele) a dedup é
    pulada para aquela candidata: ausência de hash é "não sei comparar",
    e a candidata sobrevive. Nunca o contrário — nada é descartado por
    falta de dado.

    DETERMINÍSTICA, nos dois eixos que poderiam variar:

      * O AGRUPAMENTO é uma partição por união de pares abaixo do limiar
        (fecho transitivo), e uma partição não depende da ordem em que os
        pares são unidos.
      * O REPRESENTANTE de cada grupo é a candidata de MAIOR RESOLUÇÃO
        (`width * height`), com desempate estável por `file_path` — a
        mesma regra que fecha `_ordem_imagem`. Duas execuções sobre a
        mesma resposta do TMDB devolvem byte a byte a mesma lista.

    A POSIÇÃO do grupo na lista é a do seu membro MELHOR COLOCADO — o
    representante herda o lugar da candidata mais votada do grupo, não o
    seu próprio. Sem isso, colapsar um grupo poderia empurrar para o topo
    da galeria uma imagem que o `vote_average` tinha deixado no fim.

    **O fecho transitivo é deliberado e tem custo conhecido:** se A~B e
    B~C sem A~C, os três colapsam. Com precisão medida de 0.951 por par o
    encadeamento errado é raro, e o custo dele (perder uma candidata
    distinta de um pool de dezenas) continua menor que o de repetir um
    quadro na página.
    """
    if not hashes:
        return list(candidatos)

    pai = {b["file_path"]: b["file_path"] for b in candidatos}

    def raiz(x: str) -> str:
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    comparaveis = [b for b in candidatos if b["file_path"] in hashes]
    for i, a in enumerate(comparaveis):
        for b in comparaveis[i + 1:]:
            if distancia_phash(hashes[a["file_path"]],
                               hashes[b["file_path"]]) <= limiar:
                pai[raiz(a["file_path"])] = raiz(b["file_path"])

    melhor_do_grupo: dict[str, dict] = {}
    for b in candidatos:
        g = raiz(b["file_path"])
        atual = melhor_do_grupo.get(g)
        chave = lambda x: (-((x.get("width") or 0) * (x.get("height") or 0)),
                           x.get("file_path") or "")
        if atual is None or chave(b) < chave(atual):
            melhor_do_grupo[g] = b

    saida, vistos = [], set()
    for b in candidatos:            # a ordem de entrada JÁ é a do ranking
        g = raiz(b["file_path"])
        if g in vistos:
            continue
        vistos.add(g)
        saida.append(melhor_do_grupo[g])
    return saida


def _amostra_espalhada(itens: list[dict], teto: int) -> list[dict]:
    """Até `teto` itens ESPALHADOS pelo ranking, em vez dos `teto`
    primeiros (§3[F] v1.9.40).

    A regra: o ranking é cortado em `teto` faixas contíguas de tamanho
    igual e cada faixa contribui com o seu PRIMEIRO item — o índice
    escolhido da faixa `k` é `floor(k * n / teto)`. Com `n <= teto` isso
    devolve a lista inteira, na ordem em que veio.

    Por que "primeiro de cada faixa" e não "de N em N a partir do fim",
    nem sorteio: é a única regra que espalha SEM abrir mão da curadoria.
    O item 0 continua sendo o mais votado do filme (a galeria não fica
    pior no primeiro quadro, que é o que mais gente vê), e cada uma das
    outras 7 posições é a melhor colocada da sua faixa, não uma imagem
    qualquer do fim do acervo — que, MEDIDO nos 5 filmes do estudo, é
    onde moram os quadros escuros e os recortes de 1280x720.

    O que ela conserta, e que a dedup sozinha não conserta: as duplicatas
    que o pHash NÃO reconhece (mesmo plano em escala e gradação muito
    diferentes — ver `still_hash.py`) são quase sempre VIZINHAS no
    ranking, porque é o mesmo quadro popular concentrando voto. Duas
    vizinhas nunca caem na mesma faixa quando `n >= 2 * teto`.

    [v1.9.41] **Essa cobertura DEIXOU DE SER TOTAL quando o teto foi de 8
    para 16.** Com teto=8, 33 dos 34 longas tinham `n >= 16`; com teto=16,
    o alvo virou `n >= 32` e quatro filmes ficam abaixo —
    `eighth-grade` (15), `cats-2019` (19), `the-invite-2026` (20) e
    `anatomy-of-a-fall` (28). Neles a amostragem escolhe índices quase
    consecutivos, e uma duplicata que o pHash não reconheceu (recall
    0,830, ver `still_hash.py`) PODE aparecer em posições vizinhas da
    faixa. É o custo medido e aceito do teto novo (30/34 = 88% do
    catálogo mantém a garantia, acima do piso de 85% que o critério
    de `TETO_STILLS` declara); não é um defeito silencioso.

    DETERMINÍSTICA: só divisão inteira sobre o tamanho da lista.
    """
    n = len(itens)
    if n <= teto:
        return list(itens)
    return [itens[(k * n) // teto] for k in range(teto)]


def _stills(imagens: dict, hero_backdrop_path: str | None, *,
            teto: int = TETO_STILLS, piso: int = PISO_STILLS,
            hashes: dict[str, str] | None = None) -> list[dict]:
    """Os até `teto` STILLS do filme, na ORDEM DE CÓDIGO exigida (§3[F]
    v1.9.39 — não é a mesma ordem de `_ordem_imagem`, que é para o
    BACKDROP escolhido/pôster sem texto):

        1. `vote_average` decrescente — única curadoria humana do TMDB.
        2. `file_path` crescente — fecha a ordem total (desempate estável),
           mesmo raciocínio do degrau final de `_ordem_imagem`.

    Nenhuma preferência estética por filme: a ordem é sempre esta.

    **Filtro, não preferência** (diferença do §3[E] original, onde
    `iso_639_1 is None` era só PRIORIDADE sobre o backdrop escolhido): um
    still com `iso_639_1` declarado é arte promocional com texto
    sobreposto, não um quadro do filme — fica de fora. `_still_16_9`
    filtra a proporção pela mesma razão: um crop fora de 16:9 não serve à
    grade da galeria (ver CSS, `styles.css`).

    **[v1.9.42] O `hero_backdrop_path` INVERTEU DE PAPEL: era EXCLUÍDO,
    agora é PINADO EM PRIMEIRO.**

    Até a v1.9.41 a galeria ficava no rodapé da página e o backdrop do
    hero ficava no topo; mostrar o mesmo quadro nos dois lugares repetia
    a imagem, e por isso o hero saía do pool. Nesta versão **a faixa É o
    hero** (a galeria de rodapé foi removida por inteiro, não há mais dois
    lugares), então excluir o backdrop escolhido faria a página abrir com
    um quadro que não é o que a ficha publica em `backdrop_path` — e o
    filme sem faixa, que cai no hero estático, mostraria uma imagem
    diferente da que a faixa mostraria. O hero passa a ser o PRIMEIRO
    item da sequência, e a página abre exatamente no mesmo quadro de
    sempre.

    COMO ele fica em primeiro: entra na chave de ordenação como degrau
    ZERO, antes do `vote_average`. Não é um `insert(0, ...)` depois da
    dedup, e a diferença importa — `_deduplicar` emite cada grupo na
    posição do seu membro melhor colocado, então pinar ANTES faz o GRUPO
    do hero sair em primeiro mesmo quando o representante escolhido é um
    gêmeo de resolução maior. MEDIDO nos 34 longas (2026-09-06): o hero
    sobrevive à dedup como item próprio em 28 deles (+1 no pool); nos
    outros 6 (`anatomy-of-a-fall`, `cats-2019`, `dune-part-two`,
    `everything-everywhere-all-at-once`, `friday-the-13th-2009`,
    `the-substance`) ele colapsa num gêmeo perceptual e quem abre a faixa
    é esse gêmeo — o MESMO quadro, em outro arquivo. Nenhum hero do
    catálogo é barrado pelos filtros (todos são `iso_639_1 is None` e
    16:9 exatos).

    **RISCO DE SPOILER ASSUMIDO** (ver docstring do módulo): nenhuma outra
    filtragem de conteúdo é aplicada — um still pode ser de qualquer ponto
    do filme, terceiro ato incluído.

    **PISO, depois do teto:** se o resultado (já ordenado, já deduplicado,
    já cortado em `teto`) tem menos de `piso` itens, a lista volta VAZIA — ver `PISO_STILLS`. Mesma lógica de `n < 10` na lei
    de margem: abaixo do piso, ausência é mais honesta que uma versão
    raquítica da coisa.
    """
    candidatos = [b for b in (imagens.get("backdrops") or [])
                  if b.get("file_path")
                  and b.get("iso_639_1") is None and _still_16_9(b)]
    # degrau ZERO: o backdrop do hero primeiro; o resto pela ordem de sempre
    candidatos.sort(key=lambda b: (0 if b.get("file_path") == hero_backdrop_path else 1,
                                   -(b.get("vote_average") or 0),
                                   b.get("file_path") or ""))
    candidatos = _deduplicar(candidatos, hashes)
    # A amostragem espalhada vale para o RESTO: a posição 0 é do hero, por
    # decisão, e não pode ser sorteada pela faixa do ranking.
    escolhidos = (candidatos[:1] + _amostra_espalhada(candidatos[1:], teto - 1)
                  if candidatos else [])
    stills = [
        {"still_path": b["file_path"], "still_largura": b.get("width"),
         "still_altura": b.get("height")}
        for b in escolhidos
    ]
    return stills if len(stills) >= piso else []


# As chaves que uma entrada de cache precisa TER para ser considerada
# completa. Presença, não verdade: `backdrop_path: None` é resposta válida
# (filme sem backdrop) e não deve forçar uma nova requisição a cada execução.
_CHAVES_COMPLETUDE = (
    "tmdb_fetched_at", "poster_path", "backdrop_path", "poster_sem_texto_path",
    "galeria_stills",
)


def _entrada_completa(cached: dict, identidade: dict | None = None) -> bool:
    completa = bool(cached.get("tmdb_fetched_at")) and all(
        k in cached for k in _CHAVES_COMPLETUDE)
    if not completa or identidade is None:
        return completa
    evidencia = cached.get("identidade") or {}
    esperado, fonte, _manual = tmdb_id_escolhido(identidade)
    return (
        evidencia.get("versao") == VERSAO_CONTRATO_IDENTIDADE
        and evidencia.get("status") == "validada"
        and evidencia.get("slug") == identidade.get("slug")
        and evidencia.get("tmdb_id_escolhido") == esperado
        and evidencia.get("fonte_id") == fonte
    )

_ANO_RE_CANDIDATOS = (
    re.compile(r"/films/year/(\d{4})/"),
    re.compile(r'og:title"\s+content="[^"]*\((\d{4})\)'),
)
_TITULO_CANONICO_RE = re.compile(
    r'<meta\s+name="production:name"\s+content="([^"]*)"', re.I)
_TMDB_ID_LETTERBOXD_RE = re.compile(r'data-tmdb-id="(\d+)"', re.I)


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


def extrair_identidade_letterboxd(html: str, slug: str) -> dict | None:
    """Extrai título canônico, ano e ID TMDB declarados pela página.

    Sem título ou sem ID não há prova suficiente: devolve ``None``. O ano
    pode faltar; nesse caso a cadeia já existente de resolução de ano ainda
    pode completá-lo, sem inventar o título a partir do slug.
    """
    titulo = _TITULO_CANONICO_RE.search(html)
    tmdb_id = _TMDB_ID_LETTERBOXD_RE.search(html)
    if not titulo or not tmdb_id:
        return None
    ano = None
    for padrao in _ANO_RE_CANDIDATOS:
        achado = padrao.search(html)
        if achado:
            ano = int(achado.group(1))
            break
    return {
        "slug": slug,
        "titulo": unescape(titulo.group(1)).strip(),
        "ano": ano,
        "tmdb_id_letterboxd": int(tmdb_id.group(1)),
        "fonte": "pagina_letterboxd",
    }


def resolver_identidade_letterboxd(fetcher, slug: str) -> dict | None:
    """Obtém a identidade canônica com o mesmo cache/anti-bot da coleta."""
    if fetcher is None:
        return None
    try:
        html = fetcher.get(film_page_url(slug), film_page_cache_key(slug))
    except (AntiBotError, FetchError, requests.RequestException):
        return None
    return extrair_identidade_letterboxd(html, slug)


def identidade_do_meta(meta: dict | None) -> dict | None:
    bloco = (meta or {}).get("identidade_letterboxd")
    if not isinstance(bloco, dict):
        return None
    if not bloco.get("titulo") or not bloco.get("tmdb_id_letterboxd"):
        return None
    return dict(bloco)


def resolver_identidade(fetcher, slug: str, *, meta_bruto: dict | None = None,
                        ano_explicito: int | None = None) -> dict | None:
    """Identidade persistida primeiro; página do Letterboxd depois."""
    identidade = identidade_do_meta(meta_bruto)
    if identidade is None:
        identidade = resolver_identidade_letterboxd(fetcher, slug)
    if identidade is None:
        return None
    identidade["slug"] = slug
    if identidade.get("ano") is None and ano_explicito is not None:
        identidade["ano"] = ano_explicito
    return identidade


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


def meta_com_identidade(meta: dict, fetcher, slug: str) -> dict:
    """Persiste a prova canônica sem reescrever reviews do bruto."""
    existente = identidade_do_meta(meta)
    identidade = existente or resolver_identidade_letterboxd(fetcher, slug)
    if identidade is None:
        return meta_com_ano(meta, fetcher, slug)
    saida = {**meta, "identidade_letterboxd": identidade}
    if _ano_do_bruto(saida) is None and identidade.get("ano") is not None:
        saida["ano_lancamento"] = identidade["ano"]
        saida["ano_fonte"] = "letterboxd"
    return saida


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
              "append_to_response": (
                  "credits,images,alternative_titles" if com_imagens else "credits")}
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


def _imagens(detalhes: dict, *, hashes: dict[str, str] | None = None) -> dict[str, Any]:
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

    # [v1.9.39] A GALERIA DE STILLS — computada aqui (mesmo bloco `images`,
    # zero requisição nova; busca no acervo INTEIRO de `backdrops`, não só
    # nos `TETO_BACKDROPS` capturados para `backdrop_paths` acima — a
    # galeria e a lista de backdrop do hero são coisas diferentes,
    # coincidem só em fonte), mas ainda SEM o filtro de duração: `_imagens`
    # não tem a `duracao_min` de que ele precisa (`_montar_ficha` monta os
    # dois a partir da mesma resposta). `_montar_ficha` zera esta lista
    # quando a duração não bate com longa — ver `duracao_compativel_com_longa`.
    hero_path = escolhido.get("file_path") if escolhido else None
    galeria = _stills(imagens, hero_path, hashes=hashes)

    return {
        "poster_path": poster_path,
        "poster_largura": largura,
        "poster_altura": altura,
        "backdrop_paths": backdrops,
        "backdrop_path": hero_path,
        "backdrop_largura": escolhido.get("width") if escolhido else None,
        "backdrop_altura": escolhido.get("height") if escolhido else None,
        "poster_sem_texto_path": limpo.get("file_path") if limpo else None,
        "poster_sem_texto_largura": limpo.get("width") if limpo else None,
        "poster_sem_texto_altura": limpo.get("height") if limpo else None,
        "galeria_stills": galeria,
    }


def _montar_ficha(session, api_key: str, movie_id: int, detalhes: dict,
                  *, hashes: dict[str, str] | None = None,
                  detalhes_en: dict[str, Any] | None = None) -> dict[str, Any]:
    overview = detalhes.get("overview") or ""
    fallback_en = False
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
    duracao_min = detalhes.get("runtime")
    ficha = {
        "titulo": detalhes.get("title") or detalhes.get("original_title") or "",
        "sinopse_oficial": overview,
        "sinopse_fallback_en": fallback_en,
        "generos": [g["name"] for g in detalhes.get("genres") or []],
        "duracao_min": duracao_min,
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
        **_imagens(detalhes, hashes=hashes),
    }

    # Mantido aqui para consumidores legados de `_montar_ficha`; no caminho
    # identificado, `buscar_ficha` aplica o mesmo piso à ficha INTEIRA.
    if not duracao_compativel_com_longa(duracao_min):
        ficha["galeria_stills"] = []
    return ficha


def normalizar_titulo_identidade(titulo: str) -> str:
    """Normalização conservadora: caixa, diacríticos e pontuação apenas."""
    sem_diacriticos = "".join(
        c for c in unicodedata.normalize("NFKD", titulo or "")
        if not unicodedata.combining(c)
    )
    # `isalnum` preserva scripts não latinos. Uma regex ASCII reduziria
    # títulos coreanos/japoneses/chineses à string vazia e faria duas obras
    # diferentes parecerem iguais — o oposto exato desta guarda.
    plano = "".join(c if c.isalnum() else " " for c in sem_diacriticos.casefold())
    return unicodedata.normalize("NFC", " ".join(plano.split()))


def _titulos_dos_detalhes(detalhes: dict) -> list[tuple[str, str]]:
    titulos: list[tuple[str, str]] = []
    for campo in ("original_title", "title"):
        if detalhes.get(campo):
            titulos.append((campo, detalhes[campo]))
    alternativas = (detalhes.get("alternative_titles") or {}).get("titles") or []
    for item in alternativas:
        if item.get("title"):
            titulos.append(("alternative_title", item["title"]))
    return titulos


def _titulo_correspondente(titulo_letterboxd: str,
                           *respostas: dict | None) -> tuple[str, str] | None:
    esperado = normalizar_titulo_identidade(titulo_letterboxd)
    for detalhes in respostas:
        for campo, titulo in _titulos_dos_detalhes(detalhes or {}):
            if normalizar_titulo_identidade(titulo) == esperado:
                return campo, titulo
    return None


def _evidencia_identidade(identidade: dict, ficha: dict,
                          correspondencia: tuple[str, str], fonte_id: str,
                          manual: dict | None) -> dict:
    evidencia = {
        "versao": VERSAO_CONTRATO_IDENTIDADE,
        "status": "validada",
        "slug": identidade.get("slug"),
        "titulo_letterboxd": identidade.get("titulo"),
        "ano_letterboxd": identidade.get("ano"),
        "tmdb_id_letterboxd": identidade.get("tmdb_id_letterboxd"),
        "tmdb_id_escolhido": ficha.get("tmdb_id"),
        "fonte_id": fonte_id,
        "titulo_tmdb_campo": correspondencia[0],
        "titulo_tmdb_correspondente": correspondencia[1],
        "ano_tmdb": ficha.get("ano"),
        "ano_divergente": (
            identidade.get("ano") is not None and ficha.get("ano") is not None
            and identidade["ano"] != ficha["ano"]
        ),
    }
    if manual:
        evidencia["override_manual"] = manual
    return evidencia


def buscar_ficha(titulo: str, ano: int | None, cache_dir: str | Path,
                 api_key: str | None = None,
                 session=None,
                 ano_fonte: str | None = None,
                 identidade: dict | None = None,
                 ) -> tuple[dict[str, Any] | None, str | None, dict[str, Any] | None]:
    """Ponto de entrada. Retorna `(ficha, aviso, ficha_descartada)`.

    O caminho de produção passa ``identidade``: o ID vem diretamente do
    Letterboxd (ou do mapa manual), o título precisa ser igualdade
    normalizada com ``original_title``, ``title`` ou um título alternativo,
    e a duração passa por uma segunda checagem. Sem prova, a ficha inteira é
    recusada. Chamadas sem ``identidade`` existem só para compatibilidade com
    ferramentas anteriores e conservam a resolução histórica por busca.

    - sucesso: `(dict, None, None)` — `dict` carrega `ano_fonte` (v1.7.0).
    - filme não encontrado / API indisponível / chave ausente:
      `(None, texto_do_aviso, None)`.
    - identidade não comprovada: `(None, texto_do_aviso, {"motivo": ...})`.

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
        if cached.get("nao_encontrado") and identidade is None:
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
        if _entrada_completa(cached, identidade):
            return cached, None, None

    key = api_key or os.environ.get(TMDB_ENV_KEY)
    if not key:
        return None, f"{TMDB_ENV_KEY} não definida no ambiente — ficha pulada.", None

    sess = session or requests

    try:
        fonte_id = "busca_legada"
        manual = None
        if identidade is not None:
            movie_id, fonte_id, manual = tmdb_id_escolhido(identidade)
        else:
            # Compatibilidade para consumidores antigos. O pipeline de
            # produção nunca entra aqui: ele exige a identidade extraída da
            # página do Letterboxd antes de consultar o TMDB.
            movie_id = _resolver_id(sess, key, titulo, ano)
        if movie_id is None:
            if identidade is None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"nao_encontrado": True}), encoding="utf-8")
            motivo = (fonte_id if identidade and fonte_id ==
                      "override_manual_desatualizado" else
                      "tmdb_id_letterboxd_ausente" if identidade else
                      "nao_encontrado")
            mensagem = (f"TMDB: identidade indisponível para {titulo!r} ({ano})."
                        if identidade else
                        f"TMDB: nenhum resultado para {titulo!r} ({ano}).")
            return None, mensagem, {"motivo": motivo} if identidade else None
        detalhes = _buscar_detalhes(sess, key, movie_id)
        detalhes_en = None
        correspondencia = None
        if identidade is not None:
            correspondencia = _titulo_correspondente(identidade["titulo"], detalhes)
            if correspondencia is None:
                detalhes_en = _buscar_detalhes(
                    sess, key, movie_id, language="en-US", com_imagens=False)
                correspondencia = _titulo_correspondente(
                    identidade["titulo"], detalhes, detalhes_en)
            if correspondencia is None:
                descarte = {
                    "motivo": "titulo_divergente",
                    "titulo_letterboxd": identidade["titulo"],
                    "tmdb_id": movie_id,
                    "titulos_tmdb": [t for _campo, t in (
                        _titulos_dos_detalhes(detalhes)
                        + _titulos_dos_detalhes(detalhes_en or {}))],
                }
                return None, (f"TMDB: ficha descartada para {titulo!r} — "
                              "título não comprova a identidade."), descarte
        ficha = _montar_ficha(sess, key, movie_id, detalhes,
                              hashes=_hashes_dos_candidatos(detalhes, session=sess),
                              detalhes_en=detalhes_en)

        if identidade is not None and not duracao_compativel_com_longa(
                ficha.get("duracao_min")):
            descarte = {
                "motivo": "duracao_incompativel_com_longa",
                "tmdb_id": movie_id,
                "duracao_min": ficha.get("duracao_min"),
            }
            return None, (f"TMDB: ficha descartada para {titulo!r} — duração "
                          "incompatível com longa-metragem."), descarte

        # v1.7.0 — guarda de sanidade (§1.2): o ano é o sinal mais barato e
        # confiável de que o TMDB resolveu para o filme certo. Se o `ano`
        # esperado (derivado do slug/Letterboxd/--ano, NUNCA do próprio
        # resultado do TMDB) divergir em mais de 1 do ano que o TMDB
        # devolveu, é sinal de desambiguação errada (caso real: "cure" sem
        # ano resolveu para "The Cure" 2026 em vez de "Cure" 1997, uma
        # divergência de quase 30 anos). Descarta a ficha inteira — melhor
        # nenhuma ficha do que a ficha de outro filme.
        if identidade is None and ano is not None and ficha.get("ano") is not None \
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
        if identidade is not None:
            ficha["identidade"] = _evidencia_identidade(
                identidade, ficha, correspondencia, fonte_id, manual)
            # A data do Letterboxd é a data editorial do catálogo. Divergência
            # (como a estreia em festival de Talk to Me em 2022 versus o
            # lançamento TMDB em 2023) permanece visível na evidência, mas o
            # valor publicado obedece à fonte escolhida pelo dono.
            if identidade.get("ano") is not None:
                ficha["ano"] = identidade["ano"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        return ficha, None, None
    except (requests.RequestException, FichaError) as e:
        return None, f"TMDB indisponível ({e}) — ficha pulada.", None
