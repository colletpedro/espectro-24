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

import math

from .alocacao import alocar_bucket, dividir_raso_profundo, redistribuir_deficit
from .bruto import ReviewBruta
from .buckets import FRONTEIRAS, mapa_de_niveis
from .collector import estado_do_piso
from .config import (
    CASCATA_CHARS,
    COTA_POR_BUCKET,
    MIN_CHARS,
    PISO_ALOCACAO_POR_NIVEL,
)


# Ordem de precedência da discriminação de descarte (v1.9.1, §3[C2]) — cada
# review cai em EXATAMENTE uma categoria, nesta ordem. `duplicata`/`outros`
# são defensivos: esperados sempre zero (o dedupe real acontece na
# persistência do bruto, §3[B']); existirem e não serem zero é sinal de bug
# na camada de baixo, não desta camada.
_MOTIVOS_DESCARTE = ("truncada_sem_texto", "spoiler", "abaixo_min_chars",
                    "excedente_cota", "duplicata", "outros")


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
    # v1.9.1: dict motivo→n — ver `_discriminar_descartes`. Os quatro campos
    # acima continuam existindo (consumidores antigos), mas são DERIVADOS
    # deste dict, não computados de novo — uma fonte de verdade.
    motivos_descarte: dict = field(default_factory=dict)

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


def _discriminar_descartes(brutas_do_nivel: list[ReviewBruta],
                           selecionadas_ids: set[str],
                           filtro_aplicado: int,
                           excluir_spoiler: bool) -> dict[str, int]:
    """Classifica cada review do bruto de um nível em EXATAMENTE uma categoria
    — `selecionada` (não contada) ou um dos motivos de `_MOTIVOS_DESCARTE` —
    numa ordem de precedência fixa (v1.9.1, §3[C2]):

    0. `duplicata` — id já visto nesta mesma passagem (defensivo; o dedupe
       real acontece na persistência do bruto, §3[B'] — esperado sempre 0);
    1. selecionada — está em `selecionadas_ids` (não conta como descarte);
    2. `truncada_sem_texto` — `texto_completo == false`;
    3. `spoiler` — marcada spoiler E `excluir_spoiler=True` (não conta quando
       o parâmetro é `False`: a review É elegível nesse caso);
    4. `abaixo_min_chars` — mais curta que `filtro_aplicado` (o degrau da
       cascata que vigorou NAQUELE nível, não o `min_chars` nominal);
    5. `excedente_cota` — passou em tudo, mas ficou além do que a
       alocação/redistribuição permitiu;
    6. `outros` — catch-all; esperado sempre 0, canário de classificação
       incompleta.

    Garantia: `sum(resultado.values()) == len(brutas_do_nivel) - len(selecionadas_ids)`,
    sempre — todo review classificado numa categoria e só uma.
    """
    motivos = {m: 0 for m in _MOTIVOS_DESCARTE}
    vistos: set[str] = set()
    for r in brutas_do_nivel:
        if r.id in vistos:
            motivos["duplicata"] += 1
            continue
        vistos.add(r.id)
        if r.id in selecionadas_ids:
            continue
        if not r.texto_completo:
            motivos["truncada_sem_texto"] += 1
        elif excluir_spoiler and r.spoiler_flag:
            motivos["spoiler"] += 1
        elif r.n_chars < filtro_aplicado:
            motivos["abaixo_min_chars"] += 1
        else:
            # Passou em texto/spoiler/comprimento — a única razão de não
            # estar em `selecionadas_ids` é ter ficado além do que a
            # alocação/redistribuição permitiu. `outros` fica de fora deste
            # ramo por construção: não há categoria "desconhecida" alcançável
            # daqui — a chave existe no dict só para o schema ser estável e
            # para acusar, se algum dia deixar de ser 0, que a classificação
            # ficou incompleta.
            motivos["excedente_cota"] += 1
    return motivos


def faixas_de_profundidade(pool: list[ReviewBruta],
                           n_raso: int) -> tuple[list, list, list]:
    """As 3 faixas de profundidade de UM nível (v1.9.5, §3[C2]).

    A divisão é **estrutural, não um tercil da distribuição observada**: a
    coleta (§3[B]) já produz dois blocos de naturezas diferentes — o RASO é
    consecutivo e denso (posições `1..n_raso`), o PROFUNDO é esparso e cada
    página cobre muito mais tempo. Partir o raso ao meio e manter o profundo
    inteiro respeita essa estrutura; cortar por tercil das posições presentes
    daria faixas diferentes em cada filme, sem significado comum entre eles.
    """
    meio = max(1, math.ceil(n_raso / 2))
    return ([r for r in pool if r.pagina_origem <= meio],
            [r for r in pool if meio < r.pagina_origem <= n_raso],
            [r for r in pool if r.pagina_origem > n_raso])


def _escolher_estratificado(pool: list[ReviewBruta], n_alvo: int,
                            n_raso: int) -> list[ReviewBruta]:
    """Escolhe `n_alvo` reviews do pool de UM nível, com cota por faixa (E1).

    A ordem DENTRO da faixa continua sendo `(pagina_origem, ordem no jsonl)` —
    muda quantas vagas cada faixa recebe, nunca o desempate dentro dela.

    A alocação entre faixas é `alocar_bucket` com pesos iguais seguida de
    `redistribuir_deficit` com a contagem de cada faixa como disponibilidade —
    **quinto uso da mesma função** (reviews entre níveis, páginas entre
    níveis, posições dentro de um nível, extras da v1.9.4 entre níveis, agora
    vagas entre faixas). Faixa vazia devolve suas vagas às outras.

    **Quando os dois critérios de estratificação competem, este cede.** Com
    `n_alvo < 3` não há como preencher três faixas; a função devolve o prefixo
    do pool, que é exatamente o comportamento anterior à v1.9.5. A precedência
    não é arbitrária: a alocação proporcional por nível (§3[C1]) carrega uma
    garantia de representatividade que o histograma sustenta, enquanto a
    estratificação por profundidade é preferência de cobertura.
    """
    if n_alvo <= 0 or not pool:
        return []
    if n_alvo < 3 or n_raso <= 0:
        return pool[:n_alvo]

    faixas = faixas_de_profundidade(pool, n_raso)
    disponivel = {i: len(f) for i, f in enumerate(faixas)}
    alvo = alocar_bucket(n_alvo, {i: 1 for i in range(3)}, list(range(3)),
                         piso_nivel=0)
    final = redistribuir_deficit(alvo, disponivel)

    escolhidas: list[ReviewBruta] = []
    for i in range(3):
        escolhidas.extend(faixas[i][:final.get(i, 0)])
    # Todas as faixas curtas ao mesmo tempo: completa na ordem de sempre, para
    # que a estratificação nunca CUSTE uma review que a seleção antiga teria.
    if len(escolhidas) < n_alvo:
        ja = {r.id for r in escolhidas}
        for r in pool:
            if r.id not in ja:
                escolhidas.append(r)
                if len(escolhidas) >= n_alvo:
                    break
    return escolhidas[:n_alvo]


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
               orcamento_paginas_por_nivel: dict[float, int] | None = None,
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
    5. **Estratificação por profundidade (v1.9.5, §3[C2])** — a cota de cada
       nível é alocada entre 3 faixas de `pagina_origem`; dentro da faixa, a
       ordem continua sendo `(pagina_origem, ordem no jsonl)`. Determinística
       e reproduzível: a mesma entrada dá sempre a mesma saída.

    `orcamento_paginas_por_nivel` (v1.9.5) é o que define onde fica a
    fronteira raso/profundo de cada nível — vem do `meta.json` do bruto.
    **Omiti-lo devolve o comportamento byte-idêntico ao da v1.9.4**, o que
    mantém válidos o caminho offline e todo teste anterior: a estratificação é
    uma adição, não uma substituição.
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
            n_raso = 0
            if orcamento_paginas_por_nivel:
                orc = orcamento_paginas_por_nivel.get(n)
                if orc:
                    n_raso, _ = dividir_raso_profundo(orc)
            escolhidas = (_escolher_estratificado(pools[n], final[n], n_raso)
                          if n_raso else pools[n][:final[n]])
            # v1.9.1: classificação única de descarte (§3[C2]) — os quatro
            # campos antigos abaixo são DERIVADOS deste dict, não uma segunda
            # contagem que pode divergir dele.
            motivos = _discriminar_descartes(
                brutas_do_nivel, {r.id for r in escolhidas}, filtros[n], excluir_spoiler)
            bucket.niveis[n] = NivelSelecionado(
                nivel=n,
                n_alvo=alocacao[n],
                filtro_aplicado=filtros[n],
                validas=escolhidas,
                n_brutas=len(brutas_do_nivel),
                n_sem_nota=0,   # a URL de coleta já é por nível (§3[B])
                n_descartadas_spoiler=motivos["spoiler"],
                n_descartadas_curtas=motivos["abaixo_min_chars"],
                n_indisponivel_truncamento=motivos["truncada_sem_texto"],
                motivos_descarte=motivos,
            )
            bucket.cascata_por_degrau[filtros[n]] = (
                bucket.cascata_por_degrau.get(filtros[n], 0) + len(escolhidas))
        bucket.composicao_atingida = {n: bucket.niveis[n].n_validas for n in niveis}
        bucket.deficit_redistribuido = sum(
            max(0, final[n] - alocacao[n]) for n in niveis)
        resultado[nome] = bucket

    return resultado
