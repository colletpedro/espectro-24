"""[v1.9.1, Entrega 3] MEDIÇÃO da profundidade de paginação — SPEC §3[B].

Responde, com dado real e sem alterar o coletor de produção, às quatro
perguntas do gate:

  (a) a profundidade total é conhecível a partir da página 1 (ou de outra
      forma barata)?
  (b) páginas profundas rendem reviews normais (rendimento pós-filtro,
      comprimento médio) comparadas às rasas?
  (c) qual a janela temporal coberta por uma amostra de passo largo, contra
      a janela atual de ~7 semanas?
  (d) o custo em requisições muda?

Método: para o nível 4.0★ (populoso, bateu o teto nos 3 filmes na recoleta de
v1.9.0) de cada filme, uma sonda exponencial encontra um limite inferior
confiável de profundidade (última página não-vazia conhecida), sem tentar
localizar a última página exata — não é necessário para responder as
perguntas acima, e cada página tem custo de rede real.

Este script é DESCARTÁVEL — não integra o coletor de produção. Usa o mesmo
Fetcher/cache de sempre, então é reexecutável sem custo (tudo fica cacheado).
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.parser import parse_reviews  # noqa: E402
from espectro24.urls import level_page_cache_key, level_page_url  # noqa: E402

NIVEL = 4.0
ORDENACAO = "by/added"
CAP_PAGINAS = 4096   # segurança contra runaway — nenhum filme chegou perto
FILMES = ["cure", "cidade-de-deus", "the-invite-2026"]


def _pagina(fetcher: Fetcher, slug: str, pagina: int):
    html = fetcher.get(level_page_url(slug, NIVEL, pagina, ORDENACAO),
                       level_page_cache_key(slug, NIVEL, pagina, ORDENACAO))
    return html, parse_reviews(html)


def _total_reviews_filme(html: str) -> int | None:
    """[(a), forma alternativa] Total de reviews (TODAS as notas) — já vem em
    toda página fetchada, zero custo extra. Serve de insumo a uma estimativa
    por proxy (proporcional ao histograma), avaliada abaixo."""
    m = re.search(r'js-route-reviews.*?title="([\d,]+)&nbsp;reviews"', html, re.S)
    return int(m.group(1).replace(",", "")) if m else None


def sonda_exponencial(fetcher: Fetcher, slug: str) -> tuple[int, int, int]:
    """Dobra a página até achar uma vazia. Devolve (ultima_nao_vazia,
    primeira_vazia, n_requisicoes_desta_sonda)."""
    lo, n_req = 1, 0
    pagina = 1
    while pagina <= CAP_PAGINAS:
        _, revs = _pagina(fetcher, slug, pagina)
        n_req += 1
        if not revs:
            return lo, pagina, n_req
        lo = pagina
        pagina *= 2
    return lo, pagina, n_req   # não achou o fim até o cap — reporta o que tem


def rendimento(revs, min_chars: int = 150) -> tuple[int, float]:
    """(n válidas pós-filtro heurístico, comprimento médio das válidas)."""
    validos = [r for r in revs if not r.spoiler and len(r.text) >= min_chars]
    comp = st.mean(len(r.text) for r in validos) if validos else 0.0
    return len(validos), comp


def janela(revs) -> tuple[str | None, str | None]:
    datas = sorted((r.data or "")[:10] for r in revs if r.data)
    return (datas[0], datas[-1]) if datas else (None, None)


def medir(slug: str, cache_dir: str) -> dict:
    fetcher = Fetcher(cache_dir=cache_dir, delay=2.0)
    req_antes = fetcher.n_network

    # --- (a) profundidade a partir da pág. 1? ---
    html1, revs1 = _pagina(fetcher, slug, 1)
    total_reviews_filme = _total_reviews_filme(html1)
    tem_contagem_por_nivel = bool(
        re.search(r'rated/4[^"]*"[^>]*title="[\d,]+', html1))  # nunca visto, checa mesmo assim
    tem_numeracao_paginas = "paginate-page" in html1 or re.search(
        r'page/\d+/">\d+</a>', html1) is not None

    # --- sonda exponencial: limite inferior de profundidade ---
    lo, hi, n_sonda = sonda_exponencial(fetcher, slug)

    # --- (b) rendimento em páginas rasas vs. profundas ---
    rasas = {}
    for p in (1, 2, 3, 4):
        _, revs = _pagina(fetcher, slug, p)
        rasas[p] = rendimento(revs)

    profundas = {}
    for frac in (0.5, 0.75, 0.95):
        alvo = max(1, round(lo * frac))
        _, revs = _pagina(fetcher, slug, alvo)
        profundas[frac] = {"pagina": alvo, **dict(zip(("n_validas", "comp_media"),
                                                       rendimento(revs)))}

    # --- (c) janela temporal: atual (pág 1-4) vs. passo largo (amostra
    #     hipotética nas mesmas 4 posições, mas espalhadas até `lo`) ---
    revs_rasas_todas = []
    for p in (1, 2, 3, 4):
        _, revs = _pagina(fetcher, slug, p)
        revs_rasas_todas.extend(revs)
    janela_atual = janela(revs_rasas_todas)

    passo_largo_paginas = sorted({max(1, round(lo * f)) for f in (0.0, 0.33, 0.66, 1.0)})
    revs_passo_largo = []
    for p in passo_largo_paginas:
        _, revs = _pagina(fetcher, slug, p)
        revs_passo_largo.extend(revs)
    janela_passo_largo = janela(revs_passo_largo)

    # --- estimativa por proxy (histograma), avaliada contra o achado real ---
    meta = json.loads(Path(f"dados/bruto/{slug}/meta.json").read_text(encoding="utf-8"))
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    total_notas = sum(hist.values())
    est_paginas_proxy = None
    if total_reviews_filme and total_notas:
        est_reviews_nivel = total_reviews_filme * hist.get(NIVEL, 0) / total_notas
        est_paginas_proxy = round(est_reviews_nivel / 12)

    req_depois = fetcher.n_network
    return {
        "slug": slug,
        "tem_numeracao_paginas": tem_numeracao_paginas,
        "total_reviews_filme_nav": total_reviews_filme,
        "estimativa_proxy_paginas": est_paginas_proxy,
        "sonda_ultima_nao_vazia": lo,
        "sonda_primeira_vazia": hi,
        "sonda_requisicoes": n_sonda,
        "rasas": rasas,
        "profundas": profundas,
        "janela_atual_pag1_4": janela_atual,
        "passo_largo_paginas_amostradas": passo_largo_paginas,
        "janela_passo_largo": janela_passo_largo,
        "requisicoes_desta_medicao": req_depois - req_antes,
    }


def main():
    cache_dir = "resultado/cache"
    for slug in FILMES:
        r = medir(slug, cache_dir)
        print(f"\n{'=' * 78}\n{slug} — nível {NIVEL}★, ordenação {ORDENACAO}\n{'=' * 78}")
        print(f"(a) numeração de páginas no HTML? {r['tem_numeracao_paginas']}")
        print(f"    total 'reviews' (nav, todas as notas): "
              f"{r['total_reviews_filme_nav']}")
        print(f"    estimativa por PROXY (histograma): "
              f"~{r['estimativa_proxy_paginas']} páginas")
        print(f"    sonda exponencial: última não-vazia={r['sonda_ultima_nao_vazia']} "
              f"· primeira vazia={r['sonda_primeira_vazia']} "
              f"({r['sonda_requisicoes']} requisições)")
        razao = (r['estimativa_proxy_paginas'] / r['sonda_ultima_nao_vazia']
                if r['estimativa_proxy_paginas'] and r['sonda_ultima_nao_vazia'] else None)
        if razao:
            print(f"    proxy / real: {razao:.1f}x "
                  f"({'SUPERESTIMA' if razao > 1 else 'subestima'} muito)")

        print("\n(b) rendimento — rasas (1-4):")
        for p, (n, comp) in r["rasas"].items():
            print(f"    pág {p:>4}: {n:>2} válidas (≥150c) · comp. média {comp:>5.0f}c")
        print("    profundas (frações da sonda):")
        for frac, d in r["profundas"].items():
            print(f"    {int(frac*100)}% (pág {d['pagina']:>4}): "
                  f"{d['n_validas']:>2} válidas · comp. média {d['comp_media']:>5.0f}c")

        print("\n(c) janela temporal:")
        print(f"    atual (pág 1-4) ......... {r['janela_atual_pag1_4']}")
        print(f"    passo largo (pág {r['passo_largo_paginas_amostradas']}) "
              f".. {r['janela_passo_largo']}")

        print(f"\n(d) requisições gastas NESTA MEDIÇÃO: "
              f"{r['requisicoes_desta_medicao']} "
              f"(sonda {r['sonda_requisicoes']} + 4 rasas + 3 profundas + "
              f"{len(r['passo_largo_paginas_amostradas'])} passo-largo, com sobreposição em cache)")


if __name__ == "__main__":
    main()
