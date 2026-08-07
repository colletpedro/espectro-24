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

from .bruto import ReviewBruta, autor_hash, id_estavel, persistir
from .config import (
    DADOS_BRUTO_DIR,
    FOLGA_ALVO_COLETA,
    MIN_CHARS,
    NIVEIS_ORDENADOS,
    ORDENACAO,
    PISO_ESCALONADO,
    PISO_PAGINAS_POR_NIVEL,
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
    parou_por_teto: bool = False
    esgotado: bool = False
    n_sem_nota_no_html: int = 0

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


def _para_bruta(r: Review, nivel: float, pagina: int) -> ReviewBruta:
    """Converte a review raspada no registro persistível (§3[B']).

    `nivel` vem da URL, não do parsing: a URL já filtra por nível, então é a
    fonte autoritativa. O `rating` parseado fica como canário (ver
    `n_sem_nota_no_html`).
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
    )


def raspar_nivel(fetcher: Fetcher, slug: str, nivel: float, alvo: int,
                 ordenacao: str = ORDENACAO,
                 teto_paginas: int = TETO_PAGINAS,
                 piso_paginas: int = PISO_PAGINAS_POR_NIVEL,
                 folga: float = FOLGA_ALVO_COLETA,
                 min_chars: int = MIN_CHARS) -> NivelBruto:
    """Pagina UM nível e devolve tudo o que veio (§3[B]).

    Condição de parada, **nesta ordem de precedência**:

    **(a) PISO** — no mínimo `piso_paginas` página(s), sempre que houver
    material, *mesmo com `alvo == 0`*. É o seguro de reversibilidade da
    fronteira (§2.2, Risco 3): sem ele, um nível fora de todo alvo nunca
    seria raspado, e uma fronteira futura que o incluísse não teria material
    para reavaliar — voltaríamos a pagar recoleta para mudar uma decisão de
    análise.

    **(b) ALVO** — `alvo × folga` válidas pela contagem heurística. Os filtros
    decidem apenas **parar**; tudo continua sendo persistido, inclusive o que
    eles reprovaram.

    **(c) TETO** — `teto_paginas`. Ao bater, PARA e registra
    `parou_por_teto=True`. Superset incompleto é resultado honesto.

    Página vazia (200 com lista vazia, §2.1) encerra o nível como `esgotado`
    — que não é o mesmo que bater no teto, e a telemetria distingue os dois.
    """
    alvo_com_folga = math.ceil(alvo * folga)
    res = NivelBruto(nivel=nivel, paginas_gastas=0)
    vistos: set[str] = set()
    # Pareia cada registro persistível com a `Review` de onde ele veio — o
    # completamento precisa da `full_text_url`, que não existe no registro.
    origem: list[Review] = []

    for pagina in range(1, teto_paginas + 1):
        html = fetcher.get(level_page_url(slug, nivel, pagina, ordenacao),
                           level_page_cache_key(slug, nivel, pagina, ordenacao))
        brutas = parse_reviews(html)
        if not brutas:
            res.esgotado = True
            break
        res.paginas_gastas = pagina

        for r in brutas:
            if r.rating is None:
                res.n_sem_nota_no_html += 1
            reg = _para_bruta(r, nivel, pagina)
            if reg.id in vistos:
                continue
            vistos.add(reg.id)
            res.reviews.append(reg)
            origem.append(r)

        # (a) tem precedência sobre (b): o alvo só pode encerrar depois do piso
        if pagina >= piso_paginas and res.n_estimada_valida >= alvo_com_folga:
            break
    else:
        # esgotou o range sem `break`: bateu no teto
        res.parou_por_teto = res.n_estimada_valida < alvo_com_folga

    _completar_truncadas(fetcher, slug, res, origem, alvo_com_folga, min_chars)
    return res


def _completar_truncadas(fetcher: Fetcher, slug: str, res: NivelBruto,
                         origem: list[Review], orcamento: int,
                         min_chars: int) -> None:
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
        if reg.texto_completo or gastos >= orcamento:
            continue
        # mesma política da v1.1.1: não gastar requisição com review que os
        # filtros já reprovariam pelo texto visível
        if reg.spoiler_flag or reg.n_chars < min_chars:
            continue
        gastos += 1
        if not complete_review(fetcher, slug, r):
            continue   # descartada no completamento → segue marcada, no bruto
        res.reviews[i] = _para_bruta(r, reg.nivel, reg.pagina_origem)


def coletar_superset(fetcher: Fetcher, slug: str,
                     alvo_por_nivel: dict[float, int],
                     histograma: dict[float, int] | None,
                     raiz: str | Path = DADOS_BRUTO_DIR,
                     ordenacao: str = ORDENACAO,
                     teto_paginas: int | dict[float, int] = TETO_PAGINAS,
                     on_level=None) -> SupersetResult:
    """Varre os 10 níveis, persiste o superset e devolve a telemetria (§3[B']).

    A varredura é pela **escala inteira**, na ordem crescente de estrela — o
    coletor não sabe onde ficam as fronteiras, e um nível que hoje não
    pertence a bucket nenhum continuaria sendo raspado.

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
                          ordenacao=ordenacao, teto_paginas=teto)
        res.niveis[nivel] = nb
        if on_level:
            on_level(nb)

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
    }
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
