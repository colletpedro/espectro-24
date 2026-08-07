"""[C2] Seleção downstream — cota 40/40/40 sobre o bruto persistido (§3[C2]).

Este é o lado "ANÁLISE" da linha que a v1.9.0 traçou. Tudo o que até a v1.8.2
era decisão de coleta — fronteira de bucket, cota, filtro de comprimento,
exclusão de spoiler, cascata de relaxamento, piso — chega aqui como
**parâmetro de chamada**, e é aplicado sobre reviews que já estão em disco.

**Zero requisições de rede.** A garantia é estrutural: `selecionar` não
recebe um `Fetcher`. Mudar qualquer parâmetro acima custa re-rodar esta
função, não recoletar o filme.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .alocacao import alocar_bucket, redistribuir_deficit
from .bruto import ReviewBruta
from .buckets import FRONTEIRAS, mapa_de_niveis
from .collector import estado_do_piso
from .config import (
    CASCATA_CHARS,
    COTA_POR_BUCKET,
    MIN_CHARS,
    PISO_ALOCACAO_POR_NIVEL,
)


@dataclass
class NivelSelecionado:
    nivel: float
    n_alvo: int
    filtro_aplicado: int
    validas: list[ReviewBruta] = field(default_factory=list)
    n_brutas: int = 0
    n_sem_nota: int = 0
    n_descartadas_spoiler: int = 0
    n_descartadas_curtas: int = 0
    n_descartadas_truncamento: int = 0
    n_indisponivel_truncamento: int = 0

    @property
    def n_validas(self) -> int:
        return len(self.validas)


@dataclass
class BucketSelecionado:
    nome: str
    niveis: dict[float, NivelSelecionado] = field(default_factory=dict)
    composicao_alvo: dict[float, int] = field(default_factory=dict)
    composicao_atingida: dict[float, int] = field(default_factory=dict)
    cascata_por_degrau: dict[int, int] = field(default_factory=dict)
    deficit_redistribuido: int = 0

    @property
    def n_final(self) -> int:
        return sum(n.n_validas for n in self.niveis.values())

    @property
    def estado_piso(self) -> str:
        return estado_do_piso(self.n_final)


def _escada(min_chars: int, cascata: list[int]) -> list[int]:
    """Degraus efetivos da cascata: `min_chars` primeiro, depois os menores.

    Mantém `min_chars` e `cascata` como parâmetros independentes (é o que a
    spec pede) sem deixar uma combinação incoerente passar: pedir
    `min_chars=200` com a cascata padrão dá `[200, 150, 50, 0]`, não
    `[150, 50, 0]` com um 200 ignorado.
    """
    return [min_chars] + [c for c in cascata if c < min_chars]


def _cascade_pool(reviews: list[ReviewBruta], min_chars: int,
                  cascata: list[int], excluir_spoiler: bool
                  ) -> tuple[list[ReviewBruta], int]:
    """Aplica a cascata a UM nível. Devolve `(pool, filtro_que_vigorou)`.

    A cascata **só desce quando o degrau atual daria ZERO** — nunca para
    completar cota (regra da v1.1.0, §C, preservada). Um nível com 1 review
    longa e 30 curtas fecha com 1, não relaxa para 31.
    """
    elegiveis = [r for r in reviews
                 if r.texto_completo and not (excluir_spoiler and r.spoiler_flag)]
    degraus = _escada(min_chars, cascata)
    for thr in degraus:
        pool = [r for r in elegiveis if r.n_chars >= thr]
        if pool:
            return pool, thr
    return [], degraus[-1]


def selecionar(reviews: list[ReviewBruta],
               histograma: dict[float, int] | None,
               *,
               fronteiras: dict[str, tuple[float, float]] | None = None,
               cota_por_bucket: int = COTA_POR_BUCKET,
               min_chars: int = MIN_CHARS,
               excluir_spoiler: bool = True,
               cascata: list[int] | None = None,
               piso_nivel: int = PISO_ALOCACAO_POR_NIVEL,
               ) -> dict[str, BucketSelecionado]:
    """Escolhe até `cota_por_bucket` reviews por bucket, a partir do bruto.

    Passos por bucket (§3[C2]):

    1. **Elegíveis** — reviews dos níveis do bucket (pelas `fronteiras`
       recebidas) com `texto_completo` e, se `excluir_spoiler`, sem
       `spoiler_flag`. Truncada não resolvida fica de fora e é contada em
       `n_indisponivel_truncamento`: a invariante de v1.1.0 "texto truncado
       nunca chega ao LLM" sobrevive ao superset.
    2. **Alvo por nível** — a alocação de §3[C1], recomputada sobre o mesmo
       histograma (que está no `meta.json` do bruto, logo disponível offline).
    3. **Cascata por nível** — `min_chars` → degraus menores, disparando só em
       zero.
    4. **Redistribuição de déficit** — restrita ao mesmo bucket.
    5. **Ordem de escolha** — `(pagina_origem, ordem no jsonl)`, que é a ordem
       de amostragem da ordenação usada na coleta (§2.3). Determinística e
       reproduzível: a mesma entrada dá sempre a mesma saída.
    """
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    cascata = CASCATA_CHARS if cascata is None else cascata
    mapa = mapa_de_niveis(fr)
    hist = histograma or {}

    # A ordem de aparição no jsonl é a ordem de amostragem — guardá-la aqui
    # evita depender da estabilidade de `sorted` sobre objetos iguais.
    posicao = {id(r): i for i, r in enumerate(reviews)}
    por_nivel: dict[float, list[ReviewBruta]] = {}
    for r in reviews:
        por_nivel.setdefault(r.nivel, []).append(r)

    resultado: dict[str, BucketSelecionado] = {}
    for nome, niveis in mapa.items():
        alocacao = alocar_bucket(
            cota_por_bucket, {n: hist.get(n, 0) for n in niveis}, niveis, piso_nivel)

        pools: dict[float, list[ReviewBruta]] = {}
        filtros: dict[float, int] = {}
        for n in niveis:
            pool, thr = _cascade_pool(por_nivel.get(n, []), min_chars, cascata,
                                      excluir_spoiler)
            pool.sort(key=lambda r: (r.pagina_origem, posicao[id(r)]))
            pools[n], filtros[n] = pool, thr

        final = redistribuir_deficit(alocacao, {n: len(pools[n]) for n in niveis})

        bucket = BucketSelecionado(nome=nome)
        bucket.composicao_alvo = dict(alocacao)
        for n in niveis:
            brutas_do_nivel = por_nivel.get(n, [])
            escolhidas = pools[n][:final[n]]
            com_texto = [r for r in brutas_do_nivel if r.texto_completo]
            bucket.niveis[n] = NivelSelecionado(
                nivel=n,
                n_alvo=alocacao[n],
                filtro_aplicado=filtros[n],
                validas=escolhidas,
                n_brutas=len(brutas_do_nivel),
                n_sem_nota=0,   # a URL de coleta já é por nível (§3[B])
                n_descartadas_spoiler=sum(1 for r in com_texto if r.spoiler_flag),
                n_descartadas_curtas=sum(
                    1 for r in com_texto
                    if not r.spoiler_flag and r.n_chars < filtros[n]),
                n_indisponivel_truncamento=sum(
                    1 for r in brutas_do_nivel if not r.texto_completo),
            )
            bucket.cascata_por_degrau[filtros[n]] = (
                bucket.cascata_por_degrau.get(filtros[n], 0) + len(escolhidas))
        bucket.composicao_atingida = {n: bucket.niveis[n].n_validas for n in niveis}
        bucket.deficit_redistribuido = sum(
            max(0, final[n] - alocacao[n]) for n in niveis)
        resultado[nome] = bucket

    return resultado
