"""[v1.9.4] Extensão de orçamento por DÉFICIT — SPEC §3[B].

Fecha a classe que a diagnose da v1.9.3 identificou: filmes muito populares
cujo bucket DOMINANTE fecha abaixo da cota, por interação entre a alocação
proporcional ao histograma (§3[C1], que concentra orçamento nos níveis mais
populosos) e `MIN_CHARS` (que filtra pior justamente esses níveis, porque
reação de massa é curta). A redistribuição de déficit não socorre esse caso
porque pressupõe SOBRA em algum nível, e ali o bucket inteiro rende mal ao
mesmo tempo.

**A regra é OBSERVACIONAL — nenhum rendimento é estimado.** Gasta-se o
orçamento base como sempre; se o bucket fecha abaixo da meta com folga,
páginas extras são concedidas UMA A UMA até o teto, aos níveis em déficit
MEDIDO. O desenho preditivo (estimar rendimento das páginas rasas para
comprar profundidade onde compensa) está rejeitado com racional em §3[B]: as
páginas são log-espaçadas desde a v1.9.2 e não amostram o mesmo regime, e a
parada por ALVO — removida na v1.9.2 — já era uma heurística otimista
decidindo orçamento.

**Este módulo não conhece rede nem disco.** As duas operações que dependem
disso chegam como callables (`contar_validas`, `buscar_extra`), o que torna a
regra inteira testável sem uma requisição — e é o `pipeline` (a única camada
que sabe o que é um bucket) quem as fornece.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .alocacao import alocar_bucket, redistribuir_deficit
from .config import COTA_POR_BUCKET, FOLGA_ALVO_COLETA

MOTIVOS_PARADA = ("meta_atingida", "teto_extensao", "material_esgotado")


def meta_com_folga(cota_por_bucket: int = COTA_POR_BUCKET,
                   folga: float = FOLGA_ALVO_COLETA) -> int:
    """A meta que dispara (e encerra) a extensão: cota × folga.

    **Nenhum parâmetro de calibração novo:** `FOLGA_ALVO_COLETA` já existe
    desde a v1.9.0 e já significa exatamente isto — quanto material a mais
    que a cota é preciso ter em mãos para que a cota se feche depois do
    filtro real. A v1.9.2 reduziu o escopo dela ao completamento [C']; aqui
    ela volta a valer também para a decisão de parar de paginar, que é o uso
    original — mas agora sobre uma contagem MEDIDA (o pool pós-filtro), não
    sobre a heurística otimista que a parada por ALVO usava.
    """
    return math.ceil(cota_por_bucket * folga)


@dataclass
class ResultadoExtensao:
    """Telemetria auditável de UM bucket (§3[B], `extensao_por_bucket`).

    O contrato que a spec pede é poder ler, do `meta.json`, a frase "o bucket
    X recebeu N páginas de extensão e parou por Y" — sem reconstruir nada.
    """
    bucket: str
    paginas_base: int
    meta: int
    n_validas_pos_base: int
    n_validas_pos_extensao: int
    paginas_extensao: int = 0
    extras_por_nivel: dict[float, int] = field(default_factory=dict)
    motivo_parada: str = "meta_atingida"

    def para_meta(self) -> dict:
        return {
            "paginas_base": self.paginas_base,
            "paginas_extensao": self.paginas_extensao,
            "extras_por_nivel": {str(n): v
                                 for n, v in sorted(self.extras_por_nivel.items())},
            "motivo_parada": self.motivo_parada,
            "n_validas_pos_base": self.n_validas_pos_base,
            "n_validas_pos_extensao": self.n_validas_pos_extensao,
            "meta": self.meta,
        }


def escolher_nivel_da_extra(deficit: dict[float, int], vivos: set[float],
                            extras_restantes: int) -> float | None:
    """A quem vai a PRÓXIMA página extra. `None` quando não há a quem dar.

    **Quarto uso de `redistribuir_deficit`, não um mecanismo novo** (§3[B]).
    O plano das extras restantes é montado por `alocar_bucket` sobre os níveis
    em déficit e depois passado por `redistribuir_deficit` com a
    "disponibilidade" sendo a liveness do nível — é essa segunda chamada que
    move a cota de um nível ESGOTADO para um que ainda pode render. A página
    vai para o nível com maior alocação no plano final (desempate pelo nível
    mais alto, o mesmo de `_maior_resto`).

    **Peso por DÉFICIT, não por histograma — deliberado.** Todos os outros
    usos de `alocar_bucket` pesam pelo histograma; aqui isso daria as extras
    ao mesmo nível populoso de baixo rendimento que a diagnose apontou como
    o AMPLIFICADOR do problema, repetindo a concentração em vez de corrigi-la.
    O déficit é medido, não estimado.
    """
    if extras_restantes <= 0:
        return None
    em_deficit = [n for n in sorted(deficit) if deficit.get(n, 0) > 0]
    if not em_deficit:
        return None

    plano = alocar_bucket(extras_restantes,
                          {n: deficit[n] for n in em_deficit},
                          em_deficit, piso_nivel=0)
    final = redistribuir_deficit(
        plano, {n: (extras_restantes if n in vivos else 0) for n in em_deficit})

    candidatos = [n for n in em_deficit if final.get(n, 0) > 0]
    if not candidatos:
        return None
    return max(candidatos, key=lambda n: (final[n], n))


def estender_bucket(nome: str, niveis: list[float], *,
                    alvo_por_nivel: dict[float, int],
                    contar_validas,
                    buscar_extra,
                    paginas_base: int,
                    vivos: set[float],
                    teto_extras: int,
                    meta: int) -> ResultadoExtensao:
    """Concede páginas extras a UM bucket, uma a uma, até meta/teto/material.

    - `contar_validas() -> {nível: n}` — o pool pós-filtro do bucket AGORA,
      contado sobre o material já em mãos. Medido, nunca estimado.
    - `buscar_extra(nível) -> bool` — busca UMA página extra naquele nível;
      devolve se ela trouxe conteúdo. Uma página vazia **conta como gasta**
      (a requisição foi feita) e mata o nível para o resto da extensão —
      mesma contabilidade da página vazia que revela a profundidade (v1.9.2).

    Precedência dos motivos de parada: **meta antes de teto**. Se a última
    extra autorizada fecha a meta, o motivo é `meta_atingida` — o teto só é a
    causa quando a meta NÃO foi alcançada.
    """
    validas = contar_validas()
    n_base = sum(validas.values())
    res = ResultadoExtensao(bucket=nome, paginas_base=paginas_base, meta=meta,
                            n_validas_pos_base=n_base,
                            n_validas_pos_extensao=n_base)
    vivos = set(vivos)

    while True:
        total = sum(validas.values())
        res.n_validas_pos_extensao = total
        if total >= meta:
            res.motivo_parada = "meta_atingida"
            return res
        if res.paginas_extensao >= teto_extras:
            res.motivo_parada = "teto_extensao"
            return res

        deficit = {n: max(0, alvo_por_nivel.get(n, 0) - validas.get(n, 0))
                   for n in niveis}
        escolhido = escolher_nivel_da_extra(
            deficit, vivos, teto_extras - res.paginas_extensao)
        if escolhido is None:
            res.motivo_parada = "material_esgotado"
            return res

        teve_conteudo = buscar_extra(escolhido)
        res.paginas_extensao += 1
        res.extras_por_nivel[escolhido] = res.extras_por_nivel.get(escolhido, 0) + 1
        if not teve_conteudo:
            vivos.discard(escolhido)
        validas = contar_validas()
