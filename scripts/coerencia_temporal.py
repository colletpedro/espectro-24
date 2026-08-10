"""[Coerência temporal] MEDIÇÃO + SIMULAÇÃO. Zero rede, zero mudança.

O problema, aberto desde a v1.9.0: o histograma que alimenta os rótulos de
peso ("a grande maioria das notas, ~90%") acumula notas desde 2012, enquanto
a amostra de reviews que alimenta as frequências de tema cobre uma janela
muito mais estreita. As duas frases aparecem no mesmo parágrafo da narrativa
como se falassem do mesmo grupo de pessoas.

A causa não é uma decisão que alguém tomou: a seleção consome as reviews em
ordem de `(pagina_origem, ordem no jsonl)` e para ao fechar a cota, então
RECÊNCIA virou critério de seleção implícito. A v1.9.2 resolveu o lado da
COLETA (posicionamento log-espaçado põe material profundo no bruto); falta a
SELEÇÃO usá-lo.

**Este script NÃO altera a seleção.** Ele mede o que está em disco e simula
desenhos alternativos sobre o mesmo bruto. Mudar a seleção agora invalidaria
a classificação de eixos que roda em paralelo — outras reviews no bucket são
outras frequências.

Uso:
    python scripts/coerencia_temporal.py medir      # Entrega 1
    python scripts/coerencia_temporal.py simular    # Entregas 2 e 3
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.alocacao import (  # noqa: E402
    alocar_bucket,
    dividir_raso_profundo,
    redistribuir_deficit,
)
from espectro24.bruto import carregar, percentil  # noqa: E402
from espectro24.buckets import FRONTEIRAS, mapa_de_niveis  # noqa: E402
from espectro24.config import (  # noqa: E402
    CASCATA_CHARS,
    COTA_POR_BUCKET,
    MIN_CHARS,
    PISO_ALOCACAO_POR_NIVEL,
)
from espectro24.selecao import _cascade_pool  # noqa: E402

SAIDA = RAIZ / "resultado" / "coerencia-temporal"
ARQ_MEDICAO = SAIDA / "medicao.json"
ARQ_SIMULACAO = SAIDA / "simulacao.json"

PISO_PROFUNDO = 0.25   # E3: fração da cota reservada ao bloco profundo
DESENHOS = ("atual", "E1_faixas_iguais", "E2_proporcional_ao_volume",
            "E3_piso_de_profundidade")


# ===========================================================================
# Infra comum
# ===========================================================================

def _carregar_filme(slug: str):
    meta, todas = carregar(slug)
    hist = {float(k): v for k, v in (meta or {}).get("histograma_bruto", {}).items()}
    orc = {float(k): v for k, v in
           (meta or {}).get("orcamento_paginas_por_nivel", {}).items()}
    return meta, todas, hist, orc


def _n_raso(nivel: float, orcamento: dict[float, int]) -> int:
    """Fronteira raso/profundo do nível, pela MESMA função da coleta.

    Usa o orçamento BASE (`orcamento_paginas_por_nivel`), não as páginas
    gastas: as extras da v1.9.4 são ANEXADAS além do bloco base e portanto
    caem naturalmente do lado profundo — que é o que se quer contar."""
    orc = orcamento.get(nivel)
    if not orc:
        return 0
    raso, _ = dividir_raso_profundo(orc)
    return raso


def _perfil(reviews: list, orcamento: dict[float, int]) -> dict | None:
    """min/max/percentis de `pagina_origem` + fração profunda + comprimento."""
    if not reviews:
        return None
    paginas = sorted(r.pagina_origem for r in reviews)
    profundas = sum(1 for r in reviews
                    if r.pagina_origem > _n_raso(r.nivel, orcamento))
    chars = [r.n_chars for r in reviews]
    datas = sorted(d for d in (_dia(r.data) for r in reviews) if d)
    return {
        "n": len(reviews),
        "pagina_min": paginas[0], "pagina_max": paginas[-1],
        "pagina_p5": percentil(paginas, 0.05),
        "pagina_p50": percentil(paginas, 0.50),
        "pagina_p95": percentil(paginas, 0.95),
        "n_profundas": profundas,
        "fracao_profunda": profundas / len(reviews),
        "n_chars_medio": sum(chars) / len(chars),
        "n_chars_mediano": st.median(chars),
        # (d) instrumento SECUNDÁRIO — `data` é a data ASSISTIDA, proxy
        # contaminado por quem registra filmes com atraso (§3[B'], v1.9.2).
        "data_min": datas[0] if datas else None,
        "data_max": datas[-1] if datas else None,
        "data_p5": percentil(datas, 0.05) if datas else None,
        "data_p50": percentil(datas, 0.50) if datas else None,
        "dias_p5_p95": _dias(percentil(datas, 0.05), percentil(datas, 0.95))
        if datas else None,
    }


def _dia(s: str | None) -> str | None:
    """Só a parte de DATA. O bruto tem os dois formatos — `2026-08-05` e
    `2026-08-06T01:21:22.456Z` —, herança de páginas com markup diferente;
    comparar strings de 10 chars funciona para os dois e mantém a ordenação
    lexicográfica correta."""
    return s[:10] if s and len(s) >= 10 else None


def _dias(a: str | None, b: str | None) -> int | None:
    from datetime import date
    a, b = _dia(a), _dia(b)
    if not a or not b:
        return None
    try:
        ya, ma, da = (int(x) for x in a.split("-"))
        yb, mb, db = (int(x) for x in b.split("-"))
    except ValueError:
        return None
    return (date(yb, mb, db) - date(ya, ma, da)).days


def _pools_do_bucket(todas: list, niveis: list[float]):
    """Elegíveis por nível — o MESMO `_cascade_pool` da seleção, na MESMA
    ordem `(pagina_origem, ordem no jsonl)`."""
    posicao = {id(r): i for i, r in enumerate(todas)}
    por_nivel: dict[float, list] = {n: [] for n in niveis}
    for r in todas:
        if r.nivel in por_nivel:
            por_nivel[r.nivel].append(r)
    pools, filtros = {}, {}
    for n in niveis:
        pool, thr = _cascade_pool(por_nivel[n], MIN_CHARS, CASCATA_CHARS, True)
        pool.sort(key=lambda r: (r.pagina_origem, posicao[id(r)]))
        pools[n], filtros[n] = pool, thr
    return pools, filtros


# ===========================================================================
# ENTREGA 1 — dimensionar
# ===========================================================================

def medir() -> dict:
    filmes = {}
    for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
        if not (d / "meta.json").exists():
            continue
        slug = d.name
        meta, todas, hist, orc = _carregar_filme(slug)
        if not hist:
            continue
        mapa = mapa_de_niveis()
        buckets = {}
        for nome, niveis in mapa.items():
            do_bucket = [r for r in todas if r.nivel in niveis]
            pools, _ = _pools_do_bucket(todas, niveis)
            elegiveis = [r for n in niveis for r in pools[n]]
            alocacao = alocar_bucket(COTA_POR_BUCKET,
                                     {n: hist.get(n, 0) for n in niveis},
                                     niveis, PISO_ALOCACAO_POR_NIVEL)
            final = redistribuir_deficit(alocacao,
                                         {n: len(pools[n]) for n in niveis})
            selecionadas = [r for n in niveis for r in pools[n][:final[n]]]
            buckets[nome] = {
                "bruto": _perfil(do_bucket, orc),
                "elegiveis": _perfil(elegiveis, orc),
                "selecionadas": _perfil(selecionadas, orc),
                "alocacao_por_nivel": {str(n): final[n] for n in niveis},
            }
        filmes[slug] = {"buckets": buckets,
                        "orcamento_paginas_por_nivel": {str(k): v
                                                        for k, v in orc.items()}}
    return {"filmes": filmes, "n_filmes": len(filmes)}


# ===========================================================================
# ENTREGA 2 — simular estratificação
# ===========================================================================

def _faixas(pool: list, n_raso: int) -> list[list]:
    """As 3 faixas de profundidade de UM nível, na ordem raso→profundo.

    A divisão é ESTRUTURAL, não um tercil arbitrário da distribuição: a
    coleta (§3[B], v1.9.2) já produz dois blocos com naturezas diferentes —
    o RASO é consecutivo e denso (posições 1..n_raso), o PROFUNDO é
    geométrico e esparso (cada página cobre muito mais tempo que a anterior).
    Partir o raso ao meio e manter o profundo inteiro respeita essa
    estrutura; cortar por tercil das posições presentes produziria faixas
    diferentes a cada filme, sem significado comum entre eles.
    """
    meio = max(1, math.ceil(n_raso / 2))
    f1 = [r for r in pool if r.pagina_origem <= meio]
    f2 = [r for r in pool if meio < r.pagina_origem <= n_raso]
    f3 = [r for r in pool if r.pagina_origem > n_raso]
    return [f1, f2, f3]


def _escolher(pool: list, n_alvo: int, n_raso: int, desenho: str) -> list:
    """Escolhe `n_alvo` reviews do pool de UM nível, sob um dos desenhos.

    Em todos eles a ordem DENTRO da faixa continua sendo a de sempre
    (`pagina_origem`, depois ordem no jsonl) — o que muda é quantas vagas
    cada faixa recebe, nunca o critério de desempate dentro dela.
    """
    if n_alvo <= 0 or not pool:
        return []
    if desenho == "atual":
        return pool[:n_alvo]

    faixas = _faixas(pool, n_raso)
    disponivel = {i: len(f) for i, f in enumerate(faixas)}

    if desenho == "E1_faixas_iguais":
        # Cota dividida IGUALMENTE entre as 3 faixas. `alocar_bucket` com
        # pesos iguais faz a divisão inteira; `redistribuir_deficit` devolve
        # às outras faixas o que uma faixa vazia não consegue preencher —
        # QUINTO uso da mesma função (reviews entre níveis, páginas entre
        # níveis, posições dentro de um nível, extras entre níveis, agora
        # vagas entre faixas).
        alvo = alocar_bucket(n_alvo, {i: 1 for i in range(3)}, list(range(3)),
                             piso_nivel=0)
    elif desenho == "E2_proporcional_ao_volume":
        # Proporcional ao VOLUME de elegíveis em cada faixa. Representa o
        # filme na proporção em que as pessoas de fato escreveram sobre ele
        # — o que, na prática, favorece o raso (é lá que está a densidade).
        alvo = alocar_bucket(n_alvo, disponivel, list(range(3)), piso_nivel=0)
    elif desenho == "E3_piso_de_profundidade":
        # Mantém a seleção atual, mas RESERVA um mínimo para o bloco
        # profundo. É o desenho de menor intervenção: só age quando a
        # seleção atual pegaria menos que o piso.
        piso = min(math.ceil(n_alvo * PISO_PROFUNDO), disponivel[2])
        rasos = n_alvo - piso
        alvo = {0: 0, 1: 0, 2: piso}
        # o resto vai para raso na ordem de sempre (faixa 0, depois 1)
        alvo[0] = min(rasos, disponivel[0])
        alvo[1] = min(rasos - alvo[0], disponivel[1])
    else:
        raise ValueError(desenho)

    final = redistribuir_deficit(alvo, disponivel)
    escolhidas = []
    for i in range(3):
        escolhidas.extend(faixas[i][:final.get(i, 0)])
    # Se ainda faltar (todas as faixas curtas), completa na ordem de sempre.
    if len(escolhidas) < n_alvo:
        ja = {id(r) for r in escolhidas}
        for r in pool:
            if id(r) not in ja:
                escolhidas.append(r)
                if len(escolhidas) >= n_alvo:
                    break
    return escolhidas[:n_alvo]


def simular() -> dict:
    resultados = {d: {} for d in DESENHOS}
    competicao = []
    perfil_faixas = {"raso": Counter(), "profundo": Counter()}
    chars_por_faixa = {"raso": [], "profundo": []}
    spoiler_por_faixa = {"raso": [0, 0], "profundo": [0, 0]}   # [spoiler, total]
    nivel_por_faixa = {"raso": Counter(), "profundo": Counter()}

    for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
        if not (d / "meta.json").exists():
            continue
        slug = d.name
        meta, todas, hist, orc = _carregar_filme(slug)
        if not hist:
            continue
        mapa = mapa_de_niveis()

        # --- perfil do material PROFUNDO vs RASO, sobre o BRUTO inteiro ---
        for r in todas:
            nr = _n_raso(r.nivel, orc)
            faixa = "profundo" if (nr and r.pagina_origem > nr) else "raso"
            chars_por_faixa[faixa].append(r.n_chars)
            spoiler_por_faixa[faixa][1] += 1
            spoiler_por_faixa[faixa][0] += bool(r.spoiler_flag)
            nivel_por_faixa[faixa][r.nivel] += 1
            perfil_faixas[faixa][slug] += 1

        for nome, niveis in mapa.items():
            pools, _ = _pools_do_bucket(todas, niveis)
            alocacao = alocar_bucket(COTA_POR_BUCKET,
                                     {n: hist.get(n, 0) for n in niveis},
                                     niveis, PISO_ALOCACAO_POR_NIVEL)
            final = redistribuir_deficit(alocacao,
                                         {n: len(pools[n]) for n in niveis})

            # --- COMPETIÇÃO entre os dois critérios de estratificação ---
            # Um nível com cota 1 ou 2 não tem como preencher 3 faixas. É
            # aqui que "estratificar por profundidade" e "alocação
            # proporcional por nível" disputam o mesmo orçamento de vagas.
            for n in niveis:
                if final[n] > 0:
                    faixas = _faixas(pools[n], _n_raso(n, orc))
                    competicao.append({
                        "slug": slug, "bucket": nome, "nivel": n,
                        "cota_do_nivel": final[n],
                        "faixas_com_material": sum(1 for f in faixas if f),
                        "cabe_em_3_faixas": final[n] >= 3,
                        "tem_profundo": bool(faixas[2]),
                    })

            for desenho in DESENHOS:
                escolhidas = []
                for n in niveis:
                    escolhidas.extend(_escolher(pools[n], final[n],
                                                _n_raso(n, orc), desenho))
                resultados[desenho].setdefault(slug, {})[nome] = _perfil(
                    escolhidas, orc)

    def _resumo_faixa(f):
        chars = chars_por_faixa[f]
        sp, tot = spoiler_por_faixa[f]
        return {
            "n": tot,
            "n_chars_medio": sum(chars) / len(chars) if chars else None,
            "n_chars_mediano": st.median(chars) if chars else None,
            "fracao_abaixo_de_150": (sum(1 for c in chars if c < 150) / len(chars))
            if chars else None,
            "fracao_spoiler": sp / tot if tot else None,
            "por_nivel": {str(k): v for k, v in sorted(nivel_por_faixa[f].items())},
        }

    return {
        "desenhos": {d: resultados[d] for d in DESENHOS},
        "perfil_do_material": {"raso": _resumo_faixa("raso"),
                               "profundo": _resumo_faixa("profundo")},
        "competicao_de_criterios": competicao,
        "piso_profundo_E3": PISO_PROFUNDO,
    }


# ===========================================================================
# CLI
# ===========================================================================

def _cli() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["medir", "simular"])
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.etapa == "medir":
        r = medir()
        ARQ_MEDICAO.write_text(json.dumps(r, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"{r['n_filmes']} filmes → {ARQ_MEDICAO.relative_to(RAIZ)}")
    else:
        r = simular()
        ARQ_SIMULACAO.write_text(json.dumps(r, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(f"→ {ARQ_SIMULACAO.relative_to(RAIZ)}")


if __name__ == "__main__":
    _cli()
