"""[v1.9.0] Alocação proporcional ao histograma — SPEC §3[C1].

Distribui as `N_bucket` vagas de análise entre os níveis de estrela **daquele
bucket**, segundo o histograma real do filme:

    n(nível L) = max(piso_nivel, round(N_bucket × contagem(L) / contagem_bucket))

Substitui a cota igual por nível (10 por nível, v1.1.0), que
**super-representava os extremos**: no `cure`, 0,5★ tem 456 notas e 2,0★ tem
4.251, e ambos entravam com 10 reviews — 0,5★ com ~9× o peso relativo que tem
na população, fazendo o grupo negativo soar mais raivoso do que é.

**Custo: zero requisições.** O histograma já era buscado uma vez por filme
desde a v1.4.0 (§3[G]); a v1.9.0 só o usa antes da coleta em vez de depois.

**A fronteira que este módulo NÃO cruza:** o peso informa a composição
*dentro* do grupo; nunca o tamanho *entre* grupos (§3[G]). `N_bucket` chega
como parâmetro e é igual nos três (40/40/40) — a profundidade por perspectiva
continua sendo decisão de design, não do histograma.

Duas ressalvas declaradas em §3[C1], que este módulo não pode resolver
sozinho e por isso a spec obriga a telemetria:
1. o histograma mede **NOTAS**, a alocação distribui **REVIEWS COM TEXTO** —
   populações diferentes, logo a alocação é uma **aproximação por proxy**;
2. a redistribuição de déficit muda a composição **silenciosamente** — daí a
   obrigação de publicar composição ALVO vs. ATINGIDA lado a lado (§4).
"""
from __future__ import annotations

from .buckets import FRONTEIRAS, mapa_de_niveis
from .config import (
    ORCAMENTO_PAGINAS_POR_BUCKET,
    PISO_ALOCACAO_POR_NIVEL,
    PISO_PAGINAS_POR_NIVEL,
    TETO_SEGURANCA_PAGINAS_NIVEL,
)


def _maior_resto(n_total: int, pesos: dict[float, float]) -> dict[float, int]:
    """Distribui `n_total` inteiros proporcionalmente a `pesos`, somando exato.

    Método do maior resto: piso de cada quota, e os `n_total - Σpiso` votos
    restantes vão para os maiores restos. Desempate determinístico pelo nível
    mais ALTO — arbitrário, mas fixo, para que a mesma entrada dê sempre a
    mesma saída (a seleção downstream precisa ser reproduzível).
    """
    if n_total <= 0 or not pesos:
        return {n: 0 for n in pesos}
    soma = sum(pesos.values())
    if soma <= 0:
        return {n: 0 for n in pesos}

    exatos = {n: n_total * p / soma for n, p in pesos.items()}
    base = {n: int(v) for n, v in exatos.items()}
    sobra = n_total - sum(base.values())
    ordem = sorted(exatos, key=lambda n: (-(exatos[n] - base[n]), -n))
    for n in ordem[:sobra]:
        base[n] += 1
    return base


def alocar_bucket(n_bucket: int, contagens: dict[float, int],
                  niveis: list[float],
                  piso_nivel: int = PISO_ALOCACAO_POR_NIVEL) -> dict[float, int]:
    """Aloca `n_bucket` vagas entre `niveis`, proporcional a `contagens`.

    Garantias (todas cobertas em `tests/test_alocacao.py`):
    - `sum(resultado.values()) == n_bucket`, **sempre**;
    - todo nível com `contagens[L] > 0` recebe ao menos `piso_nivel`, exceto
      no caso degenerate abaixo;
    - nível com contagem zero (ou ausente do dict) recebe **0** e não quebra.

    Dois caminhos degenerados, ambos explícitos:
    - **bucket inteiro zerado no histograma** (ou histograma ausente): sem
      nenhuma informação de forma, o palpite honesto é dividir igual — é o
      mesmo caminho do fallback sem histograma de §3[C1];
    - **piso impossível** (`nº de níveis com material × piso > n_bucket`):
      honrá-lo estouraria a cota, então o piso é **RELAXADO** e a alocação
      distribui `n_bucket` o mais uniformemente possível. Relaxar
      explicitamente é melhor que violar em silêncio ou que devolver uma
      soma errada.
    """
    if n_bucket <= 0:
        return {n: 0 for n in niveis}

    com_material = [n for n in niveis if contagens.get(n, 0) > 0]

    # Sem forma nenhuma: divide igual (fallback de §3[C1]).
    if not com_material:
        return _maior_resto(n_bucket, {n: 1.0 for n in niveis})

    # Piso impossível de honrar: relaxa, mas mantém a soma exata.
    if piso_nivel > 0 and len(com_material) * piso_nivel > n_bucket:
        alocado = _maior_resto(n_bucket, {n: 1.0 for n in com_material})
        return {n: alocado.get(n, 0) for n in niveis}

    alocado = _maior_resto(n_bucket, {n: float(contagens.get(n, 0))
                                      for n in com_material})

    # Aplica o piso e devolve o excedente cortando de quem tem mais acima do
    # piso — decrementando de um em um, do maior para o menor, com desempate
    # pelo nível mais alto. Um corte proporcional seria mais elegante mas
    # reabriria o problema de arredondamento que o maior resto acabou de
    # fechar; `n_bucket` é da ordem de dezenas, então iterar é barato.
    for n in com_material:
        if alocado[n] < piso_nivel:
            alocado[n] = piso_nivel
    excedente = sum(alocado.values()) - n_bucket
    while excedente > 0:
        candidatos = [n for n in com_material if alocado[n] > piso_nivel]
        if not candidatos:
            break
        alvo = max(candidatos, key=lambda n: (alocado[n], n))
        alocado[alvo] -= 1
        excedente -= 1

    return {n: alocado.get(n, 0) for n in niveis}


def alocar(n_por_bucket: dict[str, int],
           histograma: dict[float, int] | None,
           fronteiras: dict[str, tuple[float, float]] | None = None,
           piso_nivel: int = PISO_ALOCACAO_POR_NIVEL) -> dict[str, dict[float, int]]:
    """Alocação do filme inteiro: `{bucket: {nível: n}}`.

    `histograma=None` (endpoint fora do ar, `--no-distribuicao`, filme sem
    nota) cai para **uniforme** dentro de cada bucket — a coleta segue igual
    e nada bloqueia, que é a política de §3[G] desde a v1.4.0.

    As fronteiras entram como PARÂMETRO: é o que permite reavaliar a alocação
    sob outra configuração sem tocar em nenhuma outra linha.
    """
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    mapa = mapa_de_niveis(fr)
    hist = histograma or {}
    return {
        nome: alocar_bucket(n_por_bucket.get(nome, 0), hist, mapa[nome], piso_nivel)
        for nome in mapa
    }


def redistribuir_deficit(alocacao: dict[float, int],
                         disponivel: dict[float, int]) -> dict[float, int]:
    """Realoca, DENTRO do bucket, as vagas que um nível não consegue preencher.

    Quando um nível não completa a alocação (esgotou material ou bateu o teto
    de páginas), a sobra vai para os níveis do **mesmo bucket** com mais
    material disponível.

    Duas garantias:
    - **nunca estoura** `N_bucket` — o total devolvido é no máximo o total
      alocado;
    - **nunca sai do bucket** — estruturalmente, a função só vê os níveis que
      recebeu; não há caminho pelo qual uma vaga de `negativas` acabe em
      `positivas`.

    E uma não-garantia deliberada: se o bucket inteiro não tiver material, ele
    **fecha abaixo do alvo**. Isso é resultado honesto — quem trata a
    consequência é o piso escalonado (§3[C3]), não a alocação inventando
    reviews nem afrouxando filtro (relaxamento é decisão de seleção e só
    dispara em zero, §3[C2]).
    """
    final = {n: min(alocacao.get(n, 0), disponivel.get(n, 0)) for n in alocacao}
    deficit = sum(alocacao.values()) - sum(final.values())

    while deficit > 0:
        candidatos = [n for n in final if disponivel.get(n, 0) - final[n] > 0]
        if not candidatos:
            break   # material esgotado no bucket inteiro — fecha curto
        alvo = max(candidatos, key=lambda n: (disponivel.get(n, 0) - final[n], n))
        final[alvo] += 1
        deficit -= 1

    return final


def orcamento_paginas_bucket(orcamento_bucket: int, contagens: dict[float, int],
                             niveis: list[float],
                             piso: int = PISO_PAGINAS_POR_NIVEL,
                             teto_nivel: int = TETO_SEGURANCA_PAGINAS_NIVEL
                             ) -> dict[float, int]:
    """Orçamento de PÁGINAS por nível dentro de um bucket (v1.9.1, §3[B]).

    Corrige o defeito estrutural registrado na v1.9.0: o teto de páginas era
    por NÍVEL (flat) enquanto a cota de análise é por BUCKET — um bucket com
    menos níveis tinha um teto agregado menor sem nenhuma razão de conteúdo,
    só de aritmética. Aqui o orçamento é definido **por bucket** e distribuído
    entre os níveis, então dois buckets com o mesmo `orcamento_bucket` sempre
    têm o mesmo teto agregado, não importa quantos níveis cada um tem.

    **Não é uma segunda fórmula de distribuição.** A distribuição proporcional
    é literalmente `alocar_bucket` — a MESMA função que já aloca reviews
    (§3[C1]) — chamada com o orçamento de páginas no lugar da cota de
    reviews. O teto de segurança por nível (nenhum nível consome o orçamento
    do bucket sozinho) é aplicado chamando `redistribuir_deficit` de novo,
    com o teto como "disponibilidade" — não um mecanismo de redistribuição
    novo, o mesmo já usado para o déficit de reviews (§3[C1]), só com um
    `disponivel` diferente.

    Garantias: soma nunca excede `orcamento_bucket`; fica ABAIXO dele só no
    caso degenerado de um bucket com um único nível capado pelo teto de
    segurança (nada para receber o excedente redistribuído).
    """
    base = alocar_bucket(orcamento_bucket, contagens, niveis, piso_nivel=piso)
    return redistribuir_deficit(base, {n: teto_nivel for n in niveis})


def orcamento_paginas(
    orcamento_por_bucket: dict[str, int],
    histograma: dict[float, int] | None,
    fronteiras: dict[str, tuple[float, float]] | None = None,
    piso: int = PISO_PAGINAS_POR_NIVEL,
    teto_nivel: int = TETO_SEGURANCA_PAGINAS_NIVEL,
) -> dict[str, dict[float, int]]:
    """Orçamento de páginas do filme inteiro: `{bucket: {nível: páginas}}`.

    Espelha `alocar()` (§3[C1]): mesmo fallback sem histograma (uniforme),
    mesmas fronteiras como parâmetro. `orcamento_por_bucket` tipicamente é o
    mesmo valor (`ORCAMENTO_PAGINAS_POR_BUCKET`) para os três nomes — é
    exatamente essa igualdade, independente do número de níveis de cada
    bucket, que fecha o defeito estrutural da v1.9.0.
    """
    fr = FRONTEIRAS if fronteiras is None else fronteiras
    mapa = mapa_de_niveis(fr)
    hist = histograma or {}
    return {
        nome: orcamento_paginas_bucket(
            orcamento_por_bucket.get(nome, ORCAMENTO_PAGINAS_POR_BUCKET),
            hist, mapa[nome], piso, teto_nivel)
        for nome in mapa
    }
