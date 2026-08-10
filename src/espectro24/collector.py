"""[B] Raspagem do SUPERSET por nível + [G] histograma (SPEC §3[B], §3[G]).

**v1.9.0 — este módulo deixou de decidir análise.** Até a v1.8.2 ele
aplicava fronteira, cota e filtro durante a coleta, e o resultado saía já
separado em buckets: mudar qualquer uma dessas decisões custava recoletar
tudo. Agora ele raspa por **nível de estrela** (dado do Letterboxd), persiste
**tudo** (§3[B']), e os filtros existem aqui com uma função só: **decidir
quando parar de paginar**.

Quem aplica fronteira, cota, filtro e cascata é `selecao.py`, sobre o
material já em disco e sem tocar a rede.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .alocacao import dividir_raso_profundo, redistribuir_deficit
from .profundidade import posicoes_profundas
from .bruto import ReviewBruta, autor_hash, id_estavel, persistir
from .config import (
    DADOS_BRUTO_DIR,
    FOLGA_ALVO_COLETA,
    MIN_CHARS,
    NIVEIS_ORDENADOS,
    ORDENACAO,
    PISO_ESCALONADO,
    RESERVA_PROFUNDIDADE,
    TETO_PAGINAS,
    VERSAO_COLETOR,
)
from .fetcher import Fetcher
from .fulltext import complete_review
from .models import Distribuicao, Review
from .parser import parse_rating_histogram, parse_reviews
from .urls import (
    histogram_cache_key,
    histogram_url,
    level_page_cache_key,
    level_page_url,
)


@dataclass
class NivelBruto:
    """Resultado da raspagem de UM nível — telemetria + material persistível."""
    nivel: float
    paginas_gastas: int
    reviews: list[ReviewBruta] = field(default_factory=list)
    # v1.9.2 (§3[B]): motivo de parada DETERMINÍSTICO — exatamente dois
    # valores possíveis. Substitui os booleans `parou_por_teto`/`esgotado`
    # da v1.9.0/v1.9.1 (mantidos abaixo como propriedades DERIVADAS, para
    # não quebrar consumidores existentes — cli.py, `paradas_por_limite`).
    motivo_parada: str = "orcamento_esgotado"
    n_sem_nota_no_html: int = 0
    # v1.9.4 (§3[B]): contabilidade posicional, para que a EXTENSÃO saiba onde
    # continuar sem recalcular a divisão raso/profundo — se recalculasse, as
    # posições geométricas mudariam e a coleta base deixaria de ser prefixo
    # exato da coleta estendida. `posicoes_buscadas` inclui a posição vazia
    # que revelou a profundidade (a requisição foi feita); `maior_confirmada`
    # é a maior posição buscada COM conteúdo — por monotonicidade da
    # paginação, todo buraco abaixo dela tem conteúdo garantido.
    posicoes_buscadas: set = field(default_factory=set)
    maior_confirmada: int = 0
    # As `Review` de onde cada registro veio, alinhadas por índice com
    # `reviews`. Só o completamento [C'] precisa delas (a `full_text_url` não
    # existe no registro persistível). Vive aqui, e não numa variável local de
    # `raspar_nivel`, porque a extensão (v1.9.4) completa as truncadas que ela
    # mesma trouxe — página extra cujo texto fica truncado é página que a
    # seleção descarta, o que faria a extensão girar sem render nada.
    origem: list = field(default_factory=list)

    @property
    def parou_por_teto(self) -> bool:
        return self.motivo_parada == "orcamento_esgotado"

    @property
    def esgotado(self) -> bool:
        return self.motivo_parada == "material_esgotado"

    @property
    def n_bruta(self) -> int:
        return len(self.reviews)

    @property
    def n_estimada_valida(self) -> int:
        """Contagem HEURÍSTICA de válidas — a que decidiu a parada.

        Otimista por construção: mede o texto que estava visível na listagem,
        antes do completamento [C'] e da re-checagem de spoiler. É por isso
        que o alvo de parada leva a folga de 25% (§3[B]).
        """
        # Ordem dos filtros (§C): (1) tem nota — garantida pela URL, que já é
        # por nível → (2) sem spoiler → (3) comprimento.
        return sum(1 for r in self.reviews
                   if not r.spoiler_flag and r.n_chars >= MIN_CHARS)


@dataclass
class SupersetResult:
    """Resultado da coleta do filme inteiro."""
    slug: str
    ordenacao: str
    niveis: dict[float, NivelBruto] = field(default_factory=dict)
    n_reviews: int = 0
    n_novas: int = 0
    n_atualizadas: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def paradas_por_limite(self) -> list[float]:
        return [n for n, r in self.niveis.items() if r.parou_por_teto]


def _para_bruta(r: Review, nivel: float, pagina: int,
                ordenacao: str | None = None) -> ReviewBruta:
    """Converte a review raspada no registro persistível (§3[B']).

    `nivel` vem da URL, não do parsing: a URL já filtra por nível, então é a
    fonte autoritativa. O `rating` parseado fica como canário (ver
    `n_sem_nota_no_html`).

    `ordenacao` (v1.9.6, §3[B']) vem da URL pelo mesmo motivo, e é o que torna
    `pagina_origem` interpretável quando o bruto guarda duas ordenações: sem
    ele, a página 1 significaria "mais recente" e "mais antiga" no mesmo
    arquivo.
    """
    texto = r.effective_text
    completo = (not r.truncated) or (r.full_text is not None)
    return ReviewBruta(
        id=r.viewing_id or id_estavel(nivel, r.text),
        nivel=nivel,
        texto=texto,
        n_chars=len(texto),
        spoiler_flag=r.spoiler,
        pagina_origem=pagina,
        url=r.permalink or "",
        autor_hash=autor_hash(r.autor),
        truncada=r.truncated,
        texto_completo=completo,
        data=r.data,
        ordenacao_origem=ordenacao,
    )


def raspar_nivel(fetcher: Fetcher, slug: str, nivel: float, alvo: int,
                 ordenacao: str = ORDENACAO,
                 teto_paginas: int = TETO_PAGINAS,
                 folga: float = FOLGA_ALVO_COLETA,
                 min_chars: int = MIN_CHARS,
                 reserva_profundidade: float = RESERVA_PROFUNDIDADE,
                 profundidade: int | None = None) -> NivelBruto:
    """Pagina UM nível e devolve tudo o que veio (§3[B]).

    **v1.9.2 — condição de parada DETERMINÍSTICA, dois motivos possíveis:**
    o orçamento (`teto_paginas`) é sempre gasto INTEGRALMENTE, salvo
    esgotamento REAL de material (página vazia, §2.1). A parada por ALVO
    (heurística, cota × folga) da v1.9.0/v1.9.1 foi REMOVIDA — sob orçamento
    fixo por bucket (v1.9.1), ela só introduzia não-determinismo (foi a causa
    exata do 37/40 residual de `cidade-de-deus` na v1.9.1). `alvo`/`folga`
    continuam existindo, mas com escopo REDUZIDO: só decidem o orçamento do
    completamento [C'] (quantas truncadas resolver), nunca mais quando parar
    de paginar.

    **v1.9.5 — a ÂNCORA do bloco profundo muda (§3[B]).** `profundidade` é a
    profundidade REAL estimada deste nível (`profundidade.sondar_profundidade`
    + escala por histograma). Com ela, as posições profundas passam a ser
    FRAÇÕES dessa profundidade em vez de incrementos geométricos a partir do
    fim do bloco raso — o defeito medido era que a âncora antiga punha
    "profundo" na página 14-28 de níveis que vão a ~256, comprando mediana de
    3 dias sobre o raso. `profundidade=None` degrada para o comportamento
    v1.9.2, byte-idêntico. **O NÚMERO de páginas buscadas não muda em nenhum
    dos dois casos** — só onde elas caem (`tests/test_profundidade.py`).

    **v1.9.2 — posicionamento ESTRATIFICADO por profundidade (§3[B]).** O
    orçamento do nível se divide em bloco RASO (posições `1..n_raso`,
    consecutivas) e bloco PROFUNDO (até `n_profundo` posições em progressão
    geométrica a partir do fim do bloco raso — `dividir_raso_profundo`,
    `alocacao.py`). O bloco profundo só é tentado se o raso não esgotar
    primeiro (degrada para puramente consecutivo em níveis rasos). A primeira
    posição profunda vazia revela a profundidade real (por monotonicidade da
    paginação); o orçamento não gasto é redistribuído — **reaproveitando
    `redistribuir_deficit`** — só para posições JÁ CONFIRMADAS como válidas
    (nunca além da maior posição buscada com sucesso), garantindo no máximo 1
    página desperdiçada por nível.
    """
    res = NivelBruto(nivel=nivel, paginas_gastas=0)
    vistos: set[str] = set()
    origem = res.origem

    def _buscar(pagina: int) -> list:
        html = fetcher.get(level_page_url(slug, nivel, pagina, ordenacao),
                           level_page_cache_key(slug, nivel, pagina, ordenacao))
        res.posicoes_buscadas.add(pagina)
        brutas = parse_reviews(html)
        if brutas:
            res.maior_confirmada = max(res.maior_confirmada, pagina)
        return brutas

    def _registrar(brutas: list, pagina: int) -> None:
        for r in brutas:
            if r.rating is None:
                res.n_sem_nota_no_html += 1
            reg = _para_bruta(r, nivel, pagina, ordenacao)
            if reg.id in vistos:
                continue
            vistos.add(reg.id)
            res.reviews.append(reg)
            origem.append(r)

    if teto_paginas > 0:
        n_raso, n_profundo = dividir_raso_profundo(teto_paginas, reserva_profundidade)
        paginas_com_conteudo = 0
        esgotou = False

        # --- bloco raso: consecutivo, 1..n_raso ---
        for pagina in range(1, n_raso + 1):
            brutas = _buscar(pagina)
            if not brutas:
                esgotou = True
                break
            _registrar(brutas, pagina)
            paginas_com_conteudo += 1

        # --- bloco profundo: só se o raso não esgotou ---
        if not esgotou and n_profundo > 0:
            # v1.9.5: as posições vêm de `posicoes_profundas`, que devolve
            # frações da profundidade real quando ela é conhecida e a
            # progressão geométrica da v1.9.2 quando não é. O resto deste
            # bloco — descoberta por página vazia, backfill dentro do
            # intervalo confirmado, `redistribuir_deficit` — é o mesmo de
            # antes e não sabe de onde as posições vieram.
            geometricas = posicoes_profundas(n_raso, n_profundo, profundidade)
            tentadas: list[int] = []
            k_vazio: int | None = None
            maior_confirmada = n_raso
            for pos in geometricas:
                brutas = _buscar(pos)
                if not brutas:
                    k_vazio = pos
                    break
                _registrar(brutas, pos)
                paginas_com_conteudo += 1
                tentadas.append(pos)
                maior_confirmada = pos

            if k_vazio is not None:
                esgotou = True
                # A posição vazia (k_vazio) JÁ consumiu 1 unidade real de
                # orçamento (a requisição foi feita, só não trouxe conteúdo)
                # — não entra de novo como "deficit" a redistribuir, senão
                # seria contada duas vezes. Só a CAUDA nunca tentada da
                # progressão geométrica (depois de k_vazio — sabidamente
                # vazia por monotonicidade, nunca requisitada) representa
                # orçamento genuinamente sobrando.
                cauda_nao_tentada = geometricas[len(tentadas) + 1:]
                if cauda_nao_tentada:
                    # Candidatas SEGURAS: posições dentro do intervalo já
                    # confirmado (<= maior_confirmada), ainda não buscadas.
                    # Nunca além — por isso o desperdício fica em no máximo
                    # 1 página por nível (a que revelou k_vazio).
                    candidatas = [p for p in range(n_raso + 1, maior_confirmada + 1)
                                 if p not in tentadas]
                    if candidatas:
                        universo = sorted(set(cauda_nao_tentada) | set(candidatas))
                        alocacao_pos = {p: (1 if p in cauda_nao_tentada else 0)
                                        for p in universo}
                        disponivel_pos = {p: (1 if p <= maior_confirmada else 0)
                                          for p in universo}
                        final_pos = redistribuir_deficit(alocacao_pos, disponivel_pos)
                        extras = sorted(p for p in candidatas if final_pos.get(p, 0) == 1)
                        for pos in extras:
                            brutas = _buscar(pos)
                            if brutas:   # garantido pela monotonicidade; defensivo
                                _registrar(brutas, pos)
                                paginas_com_conteudo += 1

        res.paginas_gastas = paginas_com_conteudo
        res.motivo_parada = "material_esgotado" if esgotou else "orcamento_esgotado"

    orcamento_completar = math.ceil(alvo * folga)
    _completar_truncadas(fetcher, slug, res, origem, orcamento_completar, min_chars)
    return res


def estender_nivel(fetcher: Fetcher, slug: str, nb: NivelBruto,
                   ordenacao: str = ORDENACAO,
                   min_chars: int = MIN_CHARS) -> bool:
    """[v1.9.4, §3[B]] Busca UMA página extra neste nível. Devolve se ela veio
    com conteúdo.

    **Não recalcula a divisão raso/profundo** — a base continua sendo prefixo
    exato da coleta estendida (`tests/test_extensao_posicao.py`). A posição
    escolhida é, nesta ordem:

    1. o menor **buraco** dentro do intervalo já confirmado (`≤
       maior_confirmada`) ainda não buscado. Por monotonicidade da paginação,
       essas páginas têm conteúdo garantido: toda extra gasta ali rende;
    2. esgotados os buracos, a posição consecutiva seguinte à mais profunda
       já buscada. Aqui a página PODE vir vazia — e vir vazia marca o nível
       `material_esgotado`, tirando-o do jogo pelo resto da extensão.

    Nível já esgotado não gasta requisição (guarda defensiva: quem chama já
    deveria tê-lo tirado de `vivos`).

    As truncadas trazidas pela página extra são completadas na mesma chamada:
    review sem texto completo é descartada pela seleção (§3[C2]), então
    deixá-las pela metade faria a extensão gastar página sem render válida.
    """
    if nb.motivo_parada == "material_esgotado":
        return False

    buracos = [p for p in range(1, nb.maior_confirmada + 1)
               if p not in nb.posicoes_buscadas]
    pagina = buracos[0] if buracos else (max(nb.posicoes_buscadas, default=0) + 1)

    html = fetcher.get(level_page_url(slug, nb.nivel, pagina, ordenacao),
                       level_page_cache_key(slug, nb.nivel, pagina, ordenacao))
    nb.posicoes_buscadas.add(pagina)
    brutas = parse_reviews(html)
    if not brutas:
        nb.motivo_parada = "material_esgotado"
        return False

    nb.maior_confirmada = max(nb.maior_confirmada, pagina)
    nb.paginas_gastas += 1
    inicio = len(nb.reviews)
    vistos = {r.id for r in nb.reviews}
    for r in brutas:
        if r.rating is None:
            nb.n_sem_nota_no_html += 1
        reg = _para_bruta(r, nb.nivel, pagina, ordenacao)
        if reg.id in vistos:
            continue
        vistos.add(reg.id)
        nb.reviews.append(reg)
        nb.origem.append(r)

    _completar_truncadas(fetcher, slug, nb, nb.origem,
                         len(nb.reviews) - inicio, min_chars, inicio=inicio)
    return True


def _completar_truncadas(fetcher: Fetcher, slug: str, res: NivelBruto,
                         origem: list[Review], orcamento: int,
                         min_chars: int, inicio: int = 0) -> None:
    """[C'] Resolve o texto completo das truncadas — com ORÇAMENTO (v1.9.0).

    O completamento custa 1 requisição por review. Sob o superset, completar
    toda truncada raspada multiplicaria o custo sem ganho: só interessa o
    material que a seleção pode escolher. O orçamento é o MESMO alvo com
    folga que encerrou a paginação — quem ficar de fora permanece no bruto
    com `texto_completo=False`, e uma execução futura o resolve se uma
    fronteira nova o tornar relevante (a persistência é incremental e
    atualiza a linha no lugar, §3[B']).

    Reviews não truncadas já entram com `texto_completo=True` — não gastam
    requisição nenhuma.
    """
    gastos = 0
    for i, (reg, r) in enumerate(zip(res.reviews, origem)):
        if i < inicio:
            continue   # v1.9.4: a extensão completa só o que ELA trouxe
        if reg.texto_completo or gastos >= orcamento:
            continue
        # mesma política da v1.1.1: não gastar requisição com review que os
        # filtros já reprovariam pelo texto visível
        if reg.spoiler_flag or reg.n_chars < min_chars:
            continue
        gastos += 1
        if not complete_review(fetcher, slug, r):
            continue   # descartada no completamento → segue marcada, no bruto
        res.reviews[i] = _para_bruta(r, reg.nivel, reg.pagina_origem,
                                     reg.ordenacao_origem)


def coletar_superset(fetcher: Fetcher, slug: str,
                     alvo_por_nivel: dict[float, int],
                     histograma: dict[float, int] | None,
                     raiz: str | Path = DADOS_BRUTO_DIR,
                     ordenacao: str = ORDENACAO,
                     teto_paginas: int | dict[float, int] = TETO_PAGINAS,
                     on_level=None, extensao=None,
                     profundidade_por_nivel: dict[float, int] | None = None,
                     sondagem: dict | None = None,
                     meta_hook=None) -> SupersetResult:
    """Varre os 10 níveis, persiste o superset e devolve a telemetria (§3[B']).

    A varredura é pela **escala inteira**, na ordem crescente de estrela — o
    coletor não sabe onde ficam as fronteiras, e um nível que hoje não
    pertence a bucket nenhum continuaria sendo raspado.

    `extensao` (v1.9.4, §3[B]) é um gancho `(SupersetResult) -> dict | None`,
    chamado DEPOIS do orçamento base de todos os níveis e ANTES da
    persistência. Existe para que a extensão por déficit — que é uma decisão
    por BUCKET — possa rodar sem que este módulo aprenda o que é um bucket:
    quem passa o gancho é o `pipeline`, a única camada que já sabe disso. O
    dict devolvido vira `meta["extensao_por_bucket"]`.

    `meta_hook` (v1.9.6, §3[B']) é um gancho `(meta_desta_execucao) -> meta`
    aplicado ANTES da persistência. Existe porque `persistir` SOBRESCREVE o
    `meta.json`, e a passada por ordenação (§2.3) precisa preservar o meta da
    coleta BASE — sem que este módulo aprenda o que é uma passada. Ausente, o
    comportamento é o de sempre (o meta desta execução é o que vai a disco).

    `teto_paginas` aceita **int** (mesmo teto para todo nível — uso direto/
    testes de unidade) ou **dict `{nível: teto}`** (v1.9.1: o orçamento POR
    NÍVEL que `alocacao.orcamento_paginas` calculou a partir do orçamento POR
    BUCKET, §3[B] — é assim que `pipeline.py` corrige o defeito estrutural da
    v1.9.0 sem que este módulo precise saber o que é um bucket). Nível
    ausente do dict usa `TETO_PAGINAS` como fallback.
    """
    res = SupersetResult(slug=slug, ordenacao=ordenacao)
    orcamento_por_nivel: dict[float, int] = {}
    for nivel in NIVEIS_ORDENADOS:
        teto = (teto_paginas.get(nivel, TETO_PAGINAS) if isinstance(teto_paginas, dict)
               else teto_paginas)
        orcamento_por_nivel[nivel] = teto
        nb = raspar_nivel(fetcher, slug, nivel, alvo_por_nivel.get(nivel, 0),
                          ordenacao=ordenacao, teto_paginas=teto,
                          profundidade=(profundidade_por_nivel or {}).get(nivel))
        res.niveis[nivel] = nb
        if on_level:
            on_level(nb)

    # v1.9.4 (§3[B]): páginas do orçamento BASE, congeladas antes da extensão
    # — `paginas_gastas` passa a incluir as extras, e a telemetria precisa
    # conseguir separar as duas coisas.
    base_por_nivel = {n: r.paginas_gastas for n, r in res.niveis.items()}
    telemetria_extensao = extensao(res) if extensao else None

    res.meta = {
        "slug": slug,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "versao_coletor": VERSAO_COLETOR,
        "ordenacao_usada": ordenacao,
        "histograma_bruto": {str(k): v for k, v in sorted((histograma or {}).items())},
        # v1.9.1: o orçamento QUE FOI DADO a cada nível — distinto de
        # `paginas_gastas_por_nivel` (o QUANTO foi de fato usado). A razão
        # entre os dois é a composição-alvo-vs-atingida de §3[C1], agora
        # também para páginas.
        "orcamento_paginas_por_nivel": {str(n): v for n, v in orcamento_por_nivel.items()},
        "paginas_gastas_por_nivel": {str(n): r.paginas_gastas
                                     for n, r in res.niveis.items()},
        "paradas_por_limite": [str(n) for n in res.paradas_por_limite],
        "contagem_bruta_por_nivel": {str(n): r.n_bruta for n, r in res.niveis.items()},
        "contagem_estimada_valida_por_nivel": {str(n): r.n_estimada_valida
                                               for n, r in res.niveis.items()},
        # v1.9.2 (§3[B]): motivo de parada DETERMINÍSTICO por nível — fonte
        # primária de telemetria de parada; `paradas_por_limite` permanece,
        # derivado, para não quebrar consumidores existentes.
        "motivo_parada_por_nivel": {str(n): r.motivo_parada
                                    for n, r in res.niveis.items()},
        # v1.9.4 (§3[B]): base e extensão separadas por nível. A soma das
        # duas é `paginas_gastas_por_nivel`, sempre.
        "paginas_base_por_nivel": {str(n): v for n, v in base_por_nivel.items()},
        "paginas_extensao_por_nivel": {
            str(n): r.paginas_gastas - base_por_nivel[n]
            for n, r in res.niveis.items()},
    }
    if telemetria_extensao is not None:
        res.meta["extensao_por_bucket"] = telemetria_extensao
    # v1.9.5 (§3[B]): sem estes dois campos, "por que a página 137 foi
    # buscada" é irrespondível a partir do bruto.
    if sondagem is not None:
        res.meta["profundidade_sondagem"] = sondagem
    if profundidade_por_nivel:
        res.meta["profundidade_estimada_por_nivel"] = {
            str(n): v for n, v in sorted(profundidade_por_nivel.items())}
    if meta_hook is not None:
        # `res.meta` passa a ser o que foi de fato a disco — a invariante de
        # que memória e `meta.json` batem (de que `cli.py` depende ao espalhar
        # `superset.meta` em `output["coleta"]`) vale também aqui.
        res.meta = meta_hook(res.meta)
    todas = [rev for nb in res.niveis.values() for rev in nb.reviews]
    persistido = persistir(slug, res.meta, todas, raiz=raiz)
    res.n_reviews = persistido.n_total
    res.n_novas = persistido.n_novas
    res.n_atualizadas = persistido.n_atualizadas
    return res


def collect_distribuicao(fetcher: Fetcher, slug: str) -> Distribuicao | None:
    """[v1.4.0] Distribuição real de notas: 1 requisição por filme, cacheada.

    ADITIVA POR DESIGN, como a ficha TMDB (§3a): qualquer falha (rede, HTTP,
    anti-bot, layout inesperado) retorna None e o pipeline segue sem o dado
    — o narrador cai automaticamente nas regras da v1.2.1 (proibição de
    prevalência) e o render volta ao disclaimer antigo. Nenhuma exceção
    escapa daqui, EXCETO nada: até AntiBotError é contida, porque perder a
    distribuição não justifica abortar uma coleta que já custou dezenas de
    requisições.

    v1.9.0: PROMOVIDA para antes da coleta — a alocação proporcional
    (§3[C1]) precisa do histograma para calcular o alvo por nível. Continua
    sendo 1 requisição cacheada e continua sem bloquear: sem histograma, a
    alocação cai para uniforme e a coleta segue igual.
    """
    from .fetcher import AntiBotError, FetchError

    try:
        html = fetcher.get(histogram_url(slug), histogram_cache_key(slug))
    except (FetchError, AntiBotError, OSError):
        return None
    por_nivel = parse_rating_histogram(html)
    if por_nivel is None:
        return None
    return Distribuicao.de_histograma(por_nivel)


def estado_do_piso(n_validas: int) -> str:
    """[v1.9.0, §3[C3]] Piso ESCALONADO — 4 estados a partir do n final.

    Substitui o piso binário de 3, que só distinguia "tem análise" de "não
    tem". Os limiares (3, 8, 15) são **ARBITRÁRIOS** e estão registrados com
    esse rótulo na spec: a ordem de grandeza é defensável pela tabela de
    precisão de §3[C2] (em n=8 o intervalo de 95% já passa de ±34pp, o que
    torna um quantificador verbal indefensável), mas os cortes exatos não.
    """
    for limiar, estado in PISO_ESCALONADO:
        if n_validas >= limiar:
            return estado
    return PISO_ESCALONADO[-1][1]
