"""[v1.9.5] Profundidade real do nível — sondagem e âncora. SPEC §3[B].

Existe por um defeito medido: o bloco profundo da v1.9.2 comprava uma mediana
de **3 dias** sobre o raso. A causa não era a reserva (25% do orçamento, que
segue igual) e sim a ÂNCORA — a progressão geométrica partia do fim do bloco
raso, então "profundo" queria dizer página 14-28 de níveis que vão a ~256.
Profundo em POSIÇÃO DE PÁGINA, raso em TEMPO.

Este módulo dá à coleta o número que faltava (a profundidade real) e converte
esse número nas posições a buscar. Não decide QUANTAS páginas — isso continua
sendo `RESERVA_PROFUNDIDADE` e o orçamento por bucket.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import (
    FRACOES_PROFUNDIDADE,
    SONDA_ESCADA,
    SONDA_MAX_REFINAMENTO,
    TETO_PLATAFORMA_PAGINAS,
)
from .parser import parse_reviews
from .urls import level_page_cache_key, level_page_url


@dataclass
class Sondagem:
    """Resultado da sondagem de UM nível. `profundidade=None` = desconhecida."""
    nivel: float
    profundidade: int | None
    exata: bool
    requisicoes: int
    motivo: str          # "teto_plataforma" | "encontrada" | "sem_material" | "falha"

    def para_meta(self) -> dict:
        return {"nivel_sondado": self.nivel, "profundidade": self.profundidade,
                "exata": self.exata, "requisicoes": self.requisicoes,
                "motivo": self.motivo}


def nivel_mais_populoso(histograma: dict[float, int] | None) -> float | None:
    """O nível a sondar. É o mais populoso porque é o que tem mais chance de
    alcançar o teto de plataforma — sondar um nível raso mediria o conteúdo
    daquele nível, não a profundidade que os outros podem ter."""
    if not histograma:
        return None
    com_material = {n: c for n, c in histograma.items() if c > 0}
    if not com_material:
        return None
    return max(com_material, key=lambda n: (com_material[n], n))


def sondar_profundidade(fetcher, slug: str, nivel: float,
                        ordenacao: str | None = None) -> Sondagem:
    """Última página não-vazia do nível, por escada geométrica + refinamento.

    **Custo limitado por construção:** `len(SONDA_ESCADA)` requisições de
    escada mais `SONDA_MAX_REFINAMENTO` de refinamento binário. No caso
    dominante (filme popular) a escada inteira volta cheia, a profundidade é o
    teto de plataforma e o refinamento nem roda — 4 requisições.

    **Aditiva, como a ficha do TMDB e o histograma (§3[G]):** qualquer falha
    devolve `profundidade=None`, e quem chama degrada para o comportamento da
    v1.9.2. Uma sondagem que não deu certo nunca derruba uma coleta que vai
    custar dezenas de requisições.

    Nunca SUPERESTIMA: o valor devolvido é sempre uma página confirmada com
    conteúdo. Subestimar é aceitável (é um limite inferior real); superestimar
    faria a âncora mirar em página vazia.
    """
    from .config import ORDENACAO
    from .fetcher import AntiBotError, FetchError

    ordenacao = ORDENACAO if ordenacao is None else ordenacao
    req = 0

    def tem_conteudo(pagina: int) -> bool:
        nonlocal req
        req += 1
        html = fetcher.get(level_page_url(slug, nivel, pagina, ordenacao),
                           level_page_cache_key(slug, nivel, pagina, ordenacao))
        return bool(parse_reviews(html))

    try:
        # --- escada: última cheia e primeira vazia ---
        ultima_cheia = 0
        primeira_vazia: int | None = None
        for degrau in SONDA_ESCADA:
            if tem_conteudo(degrau):
                ultima_cheia = degrau
            else:
                primeira_vazia = degrau
                break

        if primeira_vazia is None:
            # Escada inteira cheia → o teto de plataforma (§3[B], v1.9.2).
            return Sondagem(nivel, min(ultima_cheia, TETO_PLATAFORMA_PAGINAS),
                            False, req, "teto_plataforma")

        # --- refinamento binário, com teto de passos ---
        # `ultima_cheia == 0` (nem o primeiro degrau tem conteúdo) entra aqui
        # como qualquer outro intervalo: `lo=0` é o limite inferior trivial, e
        # o refinamento resolve um nível muito raso em 2 passos. Tratá-lo como
        # caso especial custaria precisão de graça no filme obscuro, que é
        # justamente onde a profundidade real importa saber com exatidão.
        lo, hi = ultima_cheia, primeira_vazia   # lo cheia (ou 0), hi vazia
        passos = 0
        while hi - lo > 1 and passos < SONDA_MAX_REFINAMENTO:
            meio = (lo + hi) // 2
            if tem_conteudo(meio):
                lo = meio
            else:
                hi = meio
            passos += 1
        if lo == 0:
            return Sondagem(nivel, None, hi == 1, req, "sem_material")
        return Sondagem(nivel, lo, hi - lo == 1, req, "encontrada")

    except (FetchError, AntiBotError, OSError):
        return Sondagem(nivel, None, False, req, "falha")


def escalar_por_histograma(profundidade: int | None, nivel_sondado: float,
                           histograma: dict[float, int] | None
                           ) -> dict[float, int]:
    """Profundidade estimada dos DEMAIS níveis, pela proporção do histograma.

    **PROXY DECLARADO, e a spec o rotula como tal (§3[B]).** O histograma
    conta NOTAS; a paginação conta REVIEWS COM TEXTO. É a mesma aproximação
    que §3[C1] já usa para alocar vagas, com a mesma ressalva: nada garante
    que a razão texto/nota seja igual entre níveis.

    A defesa do proxy não é que ele acerte, e sim que **errar sai barato**:
    posição estimada que volta vazia cai no mecanismo de descoberta da v1.9.2
    (`collector.raspar_nivel`), que revela a profundidade real por
    monotonicidade e redistribui o orçamento com `redistribuir_deficit`.
    Nenhum segundo caminho de código.

    Piso de 1 e teto de `TETO_PLATAFORMA_PAGINAS`.
    """
    if profundidade is None or not histograma:
        return {}
    base = histograma.get(nivel_sondado, 0)
    if base <= 0:
        return {}
    return {
        n: max(1, min(TETO_PLATAFORMA_PAGINAS,
                      round(profundidade * c / base)))
        for n, c in histograma.items()
    }


def posicoes_profundas(n_raso: int, n_profundo: int,
                       profundidade: int | None) -> list[int]:
    """As posições do bloco PROFUNDO de um nível, em ordem crescente.

    Com `profundidade` conhecida: frações dela (`FRACOES_PROFUNDIDADE`), o que
    faz "profundo" significar profundo no MATERIAL, não a alguns passos do
    bloco raso.

    Com `profundidade=None` (sondagem falhou ou não rodou): a **progressão
    geométrica da v1.9.2**, byte-idêntica. Degradar para o comportamento
    anterior é melhor que não buscar nada, e mantém a versão anterior viva
    como fallback em vez de removê-la.

    Degenerados (§3[B]):
    - profundidade ≤ `n_raso` → lista VAZIA: o bloco profundo se fundiria ao
      raso. Correto para filme obscuro — não há profundidade a alcançar;
    - frações que colidem em profundidade pequena → deduplicadas, e o
      orçamento não gasto volta ao raso pelo mecanismo já existente.
    """
    if n_profundo <= 0:
        return []
    if profundidade is None:
        return [n_raso + 2 ** k for k in range(1, n_profundo + 1)]
    if profundidade <= n_raso:
        return []

    vistas: list[int] = []
    for f in FRACOES_PROFUNDIDADE:
        p = max(n_raso + 1, min(profundidade, round(f * profundidade)))
        if p not in vistas:
            vistas.append(p)
        if len(vistas) == n_profundo:
            break
    return sorted(vistas)
