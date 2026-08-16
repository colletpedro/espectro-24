"""Orquestração do pipeline (SPEC §3).

**v1.9.0 — a ordem mudou, e a mudança é a arquitetura.**

    [G] histograma → [C1] alocação → [B] superset → [B'] persistência
    ─────────────────── COLETA ───────────────────
    ─────────────────── ANÁLISE ──────────────────
    [C2] seleção 40/40/40 → [C3] piso escalonado → [D] síntese

Acima da linha nada sabe onde ficam as fronteiras, qual é a cota ou qual
filtro vale. Abaixo, tudo é parâmetro aplicado sobre o material em disco.
[G] foi promovido para o começo porque a alocação precisa do histograma —
continua custando 1 requisição cacheada e continua não bloqueando (sem ele,
a alocação cai para uniforme).
"""
from __future__ import annotations

from pathlib import Path

from .alocacao import alocar, alocar_bucket, orcamento_paginas
from .bruto import (
    atualizar_meta,
    carregar,
    dias_por_100_paginas,
    dias_por_100_paginas_por_nivel,
    janela_temporal,
    reviews_da_ordenacao,
)
from .buckets import FRONTEIRAS, mapa_de_niveis
from .collector import coletar_superset, collect_distribuicao, estender_nivel
from .config import (
    BUCKETS,
    SPEC_VERSION,
    CASCATA_CHARS,
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    MIN_CHARS,
    NIVEIS_ORDENADOS,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    ORDENACAO,
    TETO_EXTENSAO_PAGINAS,
)
from .extensao import estender_bucket, meta_com_folga
from .profundidade import (
    escalar_por_histograma,
    nivel_mais_populoso,
    sondar_profundidade,
)
from .fetcher import Fetcher
from .ficha import meta_com_ano
from .models import BucketResult, LevelResult, SearchResult
from .parser import parse_search_results
from .selecao import selecionar
from .synthesize import synthesize_bucket
from .urls import search_cache_key, search_url


def atualizar_janela_temporal(slug: str,
                              fronteiras: dict[str, tuple[float, float]] | None = None,
                              raiz: str | Path = DADOS_BRUTO_DIR) -> dict | None:
    """[v1.9.1, §3[B']] Grava `janela_temporal` no `meta.json` do bruto.

    A única peça bucket-AWARE desta operação: agrupa o bruto persistido pelas
    fronteiras (§2.2) e chama a função pura `bruto.janela_temporal` uma vez
    por bucket + uma vez no total, depois mescla o resultado via
    `bruto.atualizar_meta` (sem reescrever `reviews.jsonl`). Mesmo padrão de
    `montar_buckets`: é o único lugar que já enxerga as duas camadas.

    Devolve o bloco `{"total": ..., "por_bucket": {...}}` gravado (também
    útil para quem quiser inspecionar sem reler o arquivo).
    """
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    _, todas = carregar(slug, raiz=raiz)
    mapa = mapa_de_niveis(fr)
    por_bucket = {}
    for nome, niveis in mapa.items():
        subset = [r for r in todas if r.nivel in niveis]
        por_bucket[nome] = janela_temporal(subset)
    bloco = {"total": janela_temporal(todas), "por_bucket": por_bucket}
    atualizar_meta(slug, {"janela_temporal": bloco}, raiz=raiz)
    return bloco


def atualizar_dias_por_100_paginas(slug: str,
                                   raiz: str | Path = DADOS_BRUTO_DIR) -> dict | None:
    """[v1.9.6, §3[B']] Grava `dias_por_100_paginas` no `meta.json` do bruto.

    **Calculada sobre UMA ordenação de cada vez** — a da coleta base
    (`meta["ordenacao_usada"]`). Misturar as duas ordenações somaria posições
    que não significam a mesma coisa: página 3 sob `by/added` é a 3ª adição
    mais recente; sob `by/added-earliest`, a 3ª mais antiga.

    Reaproveita a mesma resolução de `ordenacao_origem is None` que todo
    consumidor usa (`bruto.reviews_da_ordenacao`) — não uma segunda regra que
    possa divergir dela. Zero rede: lê o bruto que a coleta acabou de
    persistir, como `atualizar_janela_temporal`.
    """
    meta, todas = carregar(slug, raiz=raiz)
    base = (meta or {}).get("ordenacao_usada") or ORDENACAO
    da_base = reviews_da_ordenacao(todas, base, base)
    bloco = dias_por_100_paginas(da_base)
    atualizacoes = {
        "dias_por_100_paginas": bloco,
        "dias_por_100_paginas_por_nivel": dias_por_100_paginas_por_nivel(da_base),
    }
    atualizar_meta(slug, atualizacoes, raiz=raiz)
    return bloco


def resolve_slug(fetcher: Fetcher, query: str) -> list[SearchResult]:
    """[A] Busca de slug via endpoint AJAX. Retorna candidatos (top primeiro)."""
    html = fetcher.get(search_url(query), search_cache_key(query))
    return parse_search_results(html)


def montar_buckets(selecao, superset=None) -> list[BucketResult]:
    """Converte o resultado da SELEÇÃO nos `BucketResult` que §D e §E esperam.

    Junta as duas metades da telemetria: o que veio da **coleta**
    (`paginas_buscadas`, por nível) e o que veio da **análise** (n_validas,
    alvo, filtro aplicado, descartes). `modo` continua sendo calculado como
    sempre — render e frontend o consomem e estão fora do escopo desta
    versão; `estado_piso` entra ao lado, não no lugar.
    """
    from .bruto import distribuicao_pagina_origem
    from .config import BUCKET_ALVO, PISO_POR_BUCKET

    paginas = {}
    orcamento_por_nivel = None
    if superset is not None:
        paginas = {n: nb.paginas_gastas for n, nb in superset.niveis.items()}
        # v1.9.2 (§3[B']): orçamento por nível, para classificar a amostra
        # selecionada em rasa/profunda (`distribuicao_pagina_origem`) com a
        # MESMA divisão usada na coleta — chaves do meta.json são string.
        orc_meta = superset.meta.get("orcamento_paginas_por_nivel")
        if orc_meta:
            orcamento_por_nivel = {float(k): v for k, v in orc_meta.items()}

    buckets: list[BucketResult] = []
    for nome in BUCKETS:
        sel = selecao[nome]
        lvls = []
        for nivel, ns in sel.niveis.items():
            lvls.append(LevelResult(
                nivel=nivel,
                filtro_aplicado=ns.filtro_aplicado,
                paginas_buscadas=paginas.get(nivel, 0),
                n_brutas=ns.n_brutas,
                n_sem_nota=ns.n_sem_nota,
                n_descartadas_spoiler=ns.n_descartadas_spoiler,
                n_descartadas_curtas=ns.n_descartadas_curtas,
                n_descartadas_truncamento=ns.n_descartadas_truncamento,
                n_indisponivel_truncamento=ns.n_indisponivel_truncamento,
                motivos_descarte=ns.motivos_descarte,
                n_alvo=ns.n_alvo,
                validas=[r.para_review() for r in ns.validas],
            ))
        n_validas = sel.n_final
        alvo = BUCKET_ALVO[nome]
        if n_validas < PISO_POR_BUCKET:
            modo = "sem_analise"
        elif n_validas >= alvo:
            modo = "completo"
        else:
            modo = "reduzido"
        amostra = [r for ns in sel.niveis.values() for r in ns.validas]
        buckets.append(BucketResult(
            nome=nome, alvo=alvo, modo=modo, estado_piso=sel.estado_piso,
            niveis=lvls,
            composicao_alvo={str(k): v for k, v in sel.composicao_alvo.items()},
            composicao_atingida={str(k): v for k, v in sel.composicao_atingida.items()},
            cascata_por_degrau={str(k): v for k, v in sel.cascata_por_degrau.items()},
            deficit_redistribuido=sel.deficit_redistribuido,
            distribuicao_pagina_origem=distribuicao_pagina_origem(
                amostra, orcamento_por_nivel),
            # v1.9.14 (Entrega 6): a MESMA função pura que já calcula a janela
            # do bruto (§3[B']), aplicada à amostra SELECIONADA. Uma função,
            # duas populações declaradas — nunca duas fórmulas de janela.
            janela_amostra=janela_temporal(amostra),
        ))
    return buckets


def _pool_validas_por_nivel(reviews, niveis, min_chars=MIN_CHARS,
                            cascata=None, excluir_spoiler=True) -> dict[float, int]:
    """Quantas VÁLIDAS cada nível tem AGORA — a contagem que a extensão lê.

    Reusa `selecao._cascade_pool`, a MESMA função que a seleção downstream
    usa para decidir o que é elegível. Se a extensão contasse "válida" por um
    critério próprio, ela poderia parar satisfeita com material que a seleção
    depois descarta — que é exatamente o modo de falha da parada por ALVO
    removida na v1.9.2 (contagem heurística otimista decidindo paginação).
    """
    from .selecao import _cascade_pool

    cascata = CASCATA_CHARS if cascata is None else cascata
    por_nivel: dict[float, list] = {n: [] for n in niveis}
    for r in reviews:
        if r.nivel in por_nivel:
            por_nivel[r.nivel].append(r)
    return {n: len(_cascade_pool(por_nivel[n], min_chars, cascata,
                                 excluir_spoiler)[0])
            for n in niveis}


def _gancho_de_extensao(fetcher: Fetcher, slug: str, hist, *,
                        cota_por_bucket: int,
                        orcamento_base: int,
                        teto_extensao: int,
                        ordenacao: str,
                        dados_dir,
                        fronteiras=None):
    """[v1.9.4, §3[B]] Monta o gancho que `coletar_superset` chama entre o
    orçamento base e a persistência.

    Esta é a única camada que sabe o que é um bucket — o coletor continua
    varrendo a escala de estrelas sem saber onde ficam as fronteiras. O que o
    gancho faz por bucket: conta as válidas sobre o material acumulado
    (bruto em disco ∪ o que esta execução acabou de raspar), e delega a regra
    inteira a `extensao.estender_bucket`.
    """
    mapa = mapa_de_niveis(FRONTEIRAS if fronteiras is None else fronteiras)
    meta = meta_com_folga(cota_por_bucket)
    teto_extras = max(0, teto_extensao - orcamento_base)

    def gancho(superset) -> dict | None:
        # REEXECUÇÃO 100% CACHE (`--offline`, README): a extensão não pode
        # buscar página nenhuma, e a garantia de "zero rede, nunca falha" é
        # anterior a esta versão. Sem esta guarda, todo filme coletado ANTES
        # da v1.9.4 quebrava em `--offline` — a extensão pedia uma página que
        # nunca esteve no cache e o `FetchError` subia pelo pipeline inteiro
        # (verificado ao vivo em `longlegs`, página 9 do nível 2,0★).
        # Devolve a telemetria da coleta que de fato aconteceu, lida do disco:
        # `persistir` SOBRESCREVE o meta, então não devolver nada apagaria o
        # registro, e devolver zeros inventaria uma extensão que não houve.
        if getattr(fetcher, "offline", False):
            meta_disco, _ = carregar(slug, raiz=dados_dir)
            return (meta_disco or {}).get("extensao_por_bucket")

        # O bruto de execuções anteriores ainda não foi mesclado (a
        # persistência roda depois deste gancho), então a contagem tem de ver
        # as duas metades. `id` é a chave de dedupe do §3[B'] — o material
        # recém-raspado prevalece, por ser o mais atual.
        _, do_disco = carregar(slug, raiz=dados_dir)
        acumulado = {r.id: r for r in do_disco}

        def todas():
            atual = dict(acumulado)
            for nb in superset.niveis.values():
                for r in nb.reviews:
                    atual[r.id] = r
            return list(atual.values())

        telemetria = {}
        for nome, niveis in mapa.items():
            paginas_base = sum(superset.niveis[n].paginas_gastas
                               for n in niveis if n in superset.niveis)
            res = estender_bucket(
                nome, niveis,
                # Alvo por nível da META COM FOLGA (não da cota): é contra ele
                # que o déficit de cada nível é medido, e a soma dos alvos é
                # exatamente a meta.
                alvo_por_nivel=alocar_bucket(
                    meta, {n: (hist or {}).get(n, 0) for n in niveis}, niveis),
                contar_validas=lambda ns=niveis: _pool_validas_por_nivel(todas(), ns),
                buscar_extra=lambda nivel: estender_nivel(
                    fetcher, slug, superset.niveis[nivel], ordenacao),
                paginas_base=paginas_base,
                vivos={n for n in niveis
                       if superset.niveis[n].motivo_parada != "material_esgotado"},
                teto_extras=teto_extras,
                meta=meta,
            )
            telemetria[nome] = res.para_meta()
        return telemetria

    return gancho


def collect_all_levels(fetcher: Fetcher, slug: str,
                       cota_por_bucket: int = COTA_POR_BUCKET,
                       orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
                       teto_extensao: int = TETO_EXTENSAO_PAGINAS,
                       ordenacao: str = ORDENACAO,
                       dados_dir: str | Path = DADOS_BRUTO_DIR,
                       distribuicao: bool = True,
                       on_level=None):
    """[G] → [C1] → [B] → [B']: a metade de COLETA, isolada.

    Devolve `(superset, distrib)`. Não seleciona nada — quem faz isso é
    `selecionar`, sobre o que este passo deixou em disco.

    `orcamento_paginas_bucket` (v1.9.1, §3[B]) é o orçamento de páginas POR
    BUCKET — igual para os três nomes, não importa quantos níveis cada um
    tem, o que fecha o defeito estrutural da v1.9.0 (teto por NÍVEL misturava
    unidades com cota por BUCKET). Distribuído entre os níveis de cada
    bucket via `alocacao.orcamento_paginas` (reusa `alocar_bucket`) e
    entregue a `coletar_superset` como um teto POR NÍVEL — o coletor em si
    continua sem saber o que é um bucket.
    """
    distrib = collect_distribuicao(fetcher, slug) if distribuicao else None
    hist = distrib.por_nivel if distrib else None

    alocacao = alocar({nome: cota_por_bucket for nome in BUCKETS}, hist)
    alvo_por_nivel = {n: 0 for n in NIVEIS_ORDENADOS}
    for por_nivel in alocacao.values():
        alvo_por_nivel.update(por_nivel)

    orc = orcamento_paginas(
        {nome: orcamento_paginas_bucket for nome in BUCKETS}, hist)
    teto_por_nivel = {n: orcamento_paginas_bucket for n in NIVEIS_ORDENADOS}
    for por_nivel in orc.values():
        teto_por_nivel.update(por_nivel)

    # v1.9.5 (§3[B]): sondagem de profundidade POR FILME, ~4 requisições, ANTES
    # de gastar o orçamento de páginas — é ela que dá a âncora do bloco
    # profundo. Aditiva: falha devolve None e a coleta segue com o
    # comportamento da v1.9.2.
    nivel_sonda = nivel_mais_populoso(hist)
    sondagem = None
    profundidade_por_nivel: dict[float, int] = {}
    if nivel_sonda is not None:
        s = sondar_profundidade(fetcher, slug, nivel_sonda, ordenacao)
        sondagem = s.para_meta()
        profundidade_por_nivel = escalar_por_histograma(
            s.profundidade, nivel_sonda, hist)

    superset = coletar_superset(
        fetcher, slug, alvo_por_nivel, hist, raiz=dados_dir,
        ordenacao=ordenacao, teto_paginas=teto_por_nivel, on_level=on_level,
        profundidade_por_nivel=profundidade_por_nivel, sondagem=sondagem,
        extensao=_gancho_de_extensao(
            fetcher, slug, hist, cota_por_bucket=cota_por_bucket,
            orcamento_base=orcamento_paginas_bucket,
            teto_extensao=teto_extensao, ordenacao=ordenacao,
            dados_dir=dados_dir))
    # v1.9.1 (§3[B']): janela temporal sobre o bruto ACUMULADO (não só o
    # lote desta execução) — mesmo espírito de `selecionar` ler o bruto
    # persistido em vez do que acabou de ser raspado. Espelhada também em
    # `superset.meta` (em memória) para que `output["coleta"]` (cli.py, que
    # espalha `superset.meta`) continue batendo com o `meta.json` em disco.
    superset.meta["janela_temporal"] = atualizar_janela_temporal(slug, raiz=dados_dir)
    # v1.9.6 (§3[B']): o discriminador que decide qual estratégia cada filme
    # precisa (§2.3) passa a ser calculado NA COLETA, não em análise ad-hoc.
    superset.meta["dias_por_100_paginas"] = atualizar_dias_por_100_paginas(
        slug, raiz=dados_dir)
    # v1.9.12 (§3[B']): o ANO do filme passa a ser dado do superset. Sem
    # ele, um slug sem sufixo de ano só resolve a ficha COM REDE — e uma
    # execução offline perde o movimento 1 em silêncio (medido em
    # `joker-folie-a-deux`; 21 dos 35 slugs do catálogo estão nessa
    # situação). Idempotente: já gravado, não custa requisição.
    superset.meta = meta_com_ano(superset.meta, fetcher, slug)
    # `atualizar_meta` (e não `persistir`) pelo mesmo motivo de
    # `janela_temporal` logo acima: isto é um passo POSTERIOR à persistência
    # do lote e não tem por que reescrever `reviews.jsonl`.
    if superset.meta.get("ano_lancamento"):
        atualizar_meta(slug, {
            "ano_lancamento": superset.meta["ano_lancamento"],
            "ano_fonte": superset.meta["ano_fonte"]}, raiz=dados_dir)
    return superset, distrib


def run_pipeline(fetcher: Fetcher, slug: str, data_coleta: str,
                 client_call=None, model=None, provider=None, synth: bool = True,
                 cota_por_bucket: int = COTA_POR_BUCKET,
                 orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_POR_BUCKET,
                 teto_extensao: int = TETO_EXTENSAO_PAGINAS,
                 on_level=None, distribuicao: bool = True,
                 ordenacao: str = ORDENACAO,
                 dados_dir: str | Path = DADOS_BRUTO_DIR):
    """Executa coleta do superset → seleção → síntese.

    Retorna `(buckets, superset, distrib)`.

    `model`/`provider` propagam para `synthesize_bucket` sem forçar um default
    aqui (v1.1.1): o default de modelo depende do provider resolvido lá.

    `orcamento_paginas_bucket` (v1.9.1) substitui o antigo `max_pages` (teto
    POR NÍVEL) — ver `collect_all_levels`.
    """
    superset, distrib = collect_all_levels(
        fetcher, slug, cota_por_bucket, orcamento_paginas_bucket, teto_extensao,
        ordenacao, dados_dir, distribuicao, on_level)

    # A seleção lê o BRUTO PERSISTIDO, não o que acabou de ser raspado: assim
    # ela enxerga o material acumulado de todas as coletas anteriores, e o
    # caminho de re-seleção offline é literalmente o mesmo código.
    _, todas = carregar(slug, raiz=dados_dir)
    # v1.9.5 (§3[C2]): o orçamento por nível é o que define a fronteira
    # raso/profundo de cada nível, e portanto as faixas da estratificação.
    # Vem do superset desta execução; ausente, a seleção cai no comportamento
    # da v1.9.4.
    orc_meta = superset.meta.get("orcamento_paginas_por_nivel") or {}
    sel = selecionar(todas, distrib.por_nivel if distrib else None,
                     cota_por_bucket=cota_por_bucket,
                     orcamento_paginas_por_nivel={float(k): v
                                                  for k, v in orc_meta.items()})
    buckets = montar_buckets(sel, superset)

    if synth:
        for b in buckets:
            synthesize_bucket(b, client_call=client_call, model=model, provider=provider)
    return buckets, superset, distrib


def total_observado(superset) -> int:
    """Total de reviews BRUTAS observadas na coleta (§E, rodapé)."""
    return sum(nb.n_bruta for nb in superset.niveis.values())


def ids_analisados(buckets) -> dict[str, set[str]]:
    """[v1.9.14] Os ids das reviews que a SÍNTESE leu, por bucket.

    Existe para medir a sobreposição com a amostra CLASSIFICADA, que não é a
    mesma (§[D3], "Duas populações de 40"). Sem este número o JSON diria "24
    de 40" sem que ninguém pudesse saber que aquele 40 não é o 40 do
    cabeçalho do grupo.
    """
    return {b.nome: {r.id for r in b.reviews_analisadas} for b in buckets}


def ids_analisados_do_bruto(slug: str, coleta: dict | None = None,
                            raiz: str | Path = DADOS_BRUTO_DIR,
                            cota_por_bucket: int = COTA_POR_BUCKET
                            ) -> dict[str, set[str]]:
    """O mesmo conjunto, re-derivado do bruto — para quem não tem os
    `BucketResult` em mãos (enriquecimento de um JSON já publicado).

    **Reusa `selecionar` com os MESMOS parâmetros do pipeline**, incluindo o
    `orcamento_paginas_por_nivel` que liga a estratificação por profundidade
    (v1.9.5). Omiti-lo é exatamente o defeito que produziu as duas amostras
    divergentes (§[D3]) — aqui ele é passado, e é por isso que este caminho
    reproduz a seleção de produção em vez de uma parecida com ela.

    Zero rede: lê o bruto persistido, como toda re-seleção offline.
    """
    return {nome: {r.id for r in reviews}
            for nome, reviews in amostra_do_bruto(
                slug, coleta=coleta, raiz=raiz,
                cota_por_bucket=cota_por_bucket).items()}


def amostra_do_bruto(slug: str, coleta: dict | None = None,
                     raiz: str | Path = DADOS_BRUTO_DIR,
                     cota_por_bucket: int = COTA_POR_BUCKET
                     ) -> dict[str, list]:
    """`{bucket: [ReviewBruta]}` — a amostra que a síntese leria, do disco.

    Reusa `selecionar` com os MESMOS parâmetros do pipeline, `orcamento_
    paginas_por_nivel` incluído. Zero rede.
    """
    meta, todas = carregar(slug, raiz=raiz)
    meta = meta or {}
    coleta = coleta or meta
    hist = {float(k): v for k, v in (coleta.get("histograma_bruto") or {}).items()}
    orc = {float(k): v
           for k, v in (coleta.get("orcamento_paginas_por_nivel") or {}).items()}
    sel = selecionar(todas, hist or None, cota_por_bucket=cota_por_bucket,
                     orcamento_paginas_por_nivel=orc)
    return {nome: [r for ns in b.niveis.values() for r in ns.validas]
            for nome, b in sel.items()}


def montar_eixos(slug: str, output: dict, analisadas: dict[str, set[str]],
                 consenso=None, client_call=None, provider=None,
                 model=None) -> dict | None:
    """[v1.9.14, §2.5 + §D3] O bloco `eixos` de um filme — ou `None`.

    ADITIVO por construção, no mesmo estatuto da ficha (§3[F]) e da
    distribuição (§3[G]): filme sem classificação, arquivo ausente ou
    taxonomia divergente devolvem `None` e o pipeline segue. O que NUNCA
    acontece é o bloco sair pela metade — sem classificação não há
    denominador, e sem denominador não há frequência que se possa publicar.

    A ordem importa: [D3] roda ANTES de `montar_bloco` porque é ele que dá a
    FRASE de cada célula; e o bloco inteiro roda antes da narrativa, porque o
    briefing lê `contraste` daqui (Entrega 4).
    """
    from . import eixos as E
    from .rotulagem import rotular_output

    if consenso is None:
        caminho = Path(E.CONSENSO_PADRAO)
        if not caminho.exists():
            return None
        try:
            catalogo = E.carregar_classificacao(caminho)
        except (ValueError, OSError):
            return None
    else:
        catalogo = consenso
    do_filme = catalogo.get(slug)
    if not do_filme:
        return None

    tabela, telemetria = rotular_output(output, client_call=client_call,
                                        provider=provider, model=model)
    bloco = E.montar_bloco(do_filme, analisadas, tabela)
    if bloco is not None:
        bloco["rotulagem"] = telemetria
        # v1.9.14: o bloco carrega a PRÓPRIA versão, e não a do arquivo que o
        # hospeda. Numa execução completa os dois carimbos coincidem; num
        # enriquecimento de JSON já publicado eles DIVERGEM — a narrativa veio
        # de uma versão, o schema de eixos de outra —, e essa divergência é a
        # verdade sobre o artefato, não um defeito a esconder atrás de um
        # carimbo único reescrito depois do fato (política de `VERSAO_COLETOR`).
        bloco["spec_version"] = SPEC_VERSION
    return bloco
