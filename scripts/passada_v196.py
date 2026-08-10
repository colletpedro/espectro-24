"""[v1.9.6] Passada seletiva sob `by/added-earliest` — seleção, execução e medição.

    python scripts/passada_v196.py metrica      # calcula dias_por_100_paginas (offline)
    python scripts/passada_v196.py selecionar   # quem entra no critério, e por quê
    python scripts/passada_v196.py antes        # fotografa o bruto (offline)
    python scripts/passada_v196.py rodar        # a passada (rede, com checkpoint)
    python scripts/passada_v196.py depois       # fotografa e compara
    python scripts/passada_v196.py simular      # Entrega 5 — S1/S2/S3, sem aplicar

Nenhuma etapa aplica mudança de seleção: `simular` mede e reporta.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import (  # noqa: E402
    carregar,
    janela_temporal,
    reviews_da_ordenacao,
)
from espectro24.buckets import mapa_de_niveis  # noqa: E402
from espectro24.config import (  # noqa: E402
    COTA_POR_BUCKET,
    LIMIAR_PASSADA_ANTIGA,
    MIN_CHARS,
    ORDENACAO,
    ORDENACAO_PASSADA,
)
from espectro24.fetcher import Fetcher, PressaoDoSite, SobrecargaError  # noqa: E402
from espectro24.lote import EstadoLote  # noqa: E402
from espectro24.passada import coletar_passada, decidir_lote  # noqa: E402
from espectro24.pipeline import atualizar_dias_por_100_paginas  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

BRUTO = RAIZ / "dados" / "bruto"
SAIDA = RAIZ / "resultado" / "v196-passada"


def slugs_do_catalogo() -> list[str]:
    return sorted(d.name for d in BRUTO.iterdir() if (d / "meta.json").exists())


def _ordenacao_base(meta: dict | None) -> str:
    return (meta or {}).get("ordenacao_usada") or ORDENACAO


def _duas_pontas(slug: str):
    """`(meta, recentes, antigas)` — as reviews de cada ordenação."""
    meta, todas = carregar(slug, raiz=BRUTO)
    base = _ordenacao_base(meta)
    return (meta,
            reviews_da_ordenacao(todas, base, base),
            reviews_da_ordenacao(todas, ORDENACAO_PASSADA, base))


# --- etapa: métrica ---------------------------------------------------------

def etapa_metrica() -> dict:
    """Calcula e GRAVA `dias_por_100_paginas` em todo meta.json. Zero rede."""
    metricas = {}
    for slug in slugs_do_catalogo():
        metricas[slug] = atualizar_dias_por_100_paginas(slug, raiz=BRUTO)
    return metricas


def _metricas_do_disco() -> dict:
    m = {}
    for slug in slugs_do_catalogo():
        meta, _ = carregar(slug, raiz=BRUTO)
        m[slug] = (meta or {}).get("dias_por_100_paginas")
    return m


# --- etapa: seleção ---------------------------------------------------------

def etapa_selecionar(limiar: float = LIMIAR_PASSADA_ANTIGA) -> dict:
    dentro, fora = decidir_lote(_metricas_do_disco(), limiar)
    saida = {
        "limiar": limiar,
        "dentro": [{"slug": d.slug, "dias_por_100_paginas": d.dias_por_100_paginas,
                    "motivo": d.motivo} for d in dentro],
        "fora": [{"slug": d.slug, "dias_por_100_paginas": d.dias_por_100_paginas,
                  "motivo": d.motivo} for d in fora],
    }
    print(f"limiar: dias_por_100_paginas < {limiar:g}")
    print(f"\nDENTRO ({len(dentro)} filmes) — 256 páginas não cobrem 1 ano:")
    for d in sorted(dentro, key=lambda x: x.dias_por_100_paginas):
        print(f"  {d.slug:45s} {d.dias_por_100_paginas:8.1f}")
    print(f"\nFORA ({len(fora)} filmes):")
    for d in sorted(fora, key=lambda x: (x.dias_por_100_paginas is None,
                                         x.dias_por_100_paginas or 0)):
        v = "sem métrica" if d.dias_por_100_paginas is None \
            else f"{d.dias_por_100_paginas:8.1f}"
        print(f"  {d.slug:45s} {v}")
    return saida


# --- fotografia (Entrega 4) -------------------------------------------------

def _perfil(reviews) -> dict | None:
    if not reviews:
        return None
    chars = [r.n_chars for r in reviews]
    return {
        "n": len(reviews),
        "n_chars_medio": round(st.mean(chars), 1),
        "n_chars_mediano": st.median(chars),
        "fracao_abaixo_min_chars": round(
            sum(1 for c in chars if c < MIN_CHARS) / len(chars), 4),
        "fracao_spoiler": round(
            sum(1 for r in reviews if r.spoiler_flag) / len(reviews), 4),
        "fracao_truncada": round(
            sum(1 for r in reviews if r.truncada) / len(reviews), 4),
        "fracao_texto_completo": round(
            sum(1 for r in reviews if r.texto_completo) / len(reviews), 4),
        "janela": janela_temporal(reviews),
        "por_nivel": {str(n): sum(1 for r in reviews if r.nivel == n)
                      for n in sorted({r.nivel for r in reviews})},
    }


def _selecao_do_filme(slug: str, reviews=None):
    meta, todas = carregar(slug, raiz=BRUTO)
    reviews = todas if reviews is None else reviews
    hist = {float(k): v for k, v in (meta or {}).get("histograma_bruto", {}).items()}
    orc = {float(k): v for k, v in
           (meta or {}).get("orcamento_paginas_por_nivel", {}).items()}
    return selecionar(reviews, hist or None, orcamento_paginas_por_nivel=orc or None)


def foto(slugs: list[str]) -> dict:
    filmes = {}
    for slug in slugs:
        meta, recentes, antigas = _duas_pontas(slug)
        todas = recentes + antigas
        sel = _selecao_do_filme(slug, todas)
        buckets = {}
        for nome, niveis in mapa_de_niveis().items():
            escolhidas = [r for ns in sel[nome].niveis.values() for r in ns.validas]
            buckets[nome] = {
                "n_final": sel[nome].n_final,
                "estado_piso": sel[nome].estado_piso,
                "fecha_cota": sel[nome].n_final >= COTA_POR_BUCKET,
                "n_bruto": sum(1 for r in todas if r.nivel in niveis),
                "n_bruto_antigo": sum(1 for r in antigas if r.nivel in niveis),
                "amostra": _perfil(escolhidas),
            }
        filmes[slug] = {
            "n_bruto": len(todas),
            "dias_por_100_paginas": (meta or {}).get("dias_por_100_paginas"),
            "janela_total": janela_temporal(todas),
            "ponta_recente": _perfil(recentes),
            "ponta_antiga": _perfil(antigas),
            "buckets": buckets,
        }
    return {"filmes": filmes, "n_filmes": len(filmes)}


def _anos(janela) -> float | None:
    if not janela:
        return None
    from datetime import date

    def d(s):
        y, m, dd = (int(x) for x in s[:10].split("-"))
        return date(y, m, dd)
    return round((d(janela["max"]) - d(janela["min"])).days / 365.25, 2)


# --- etapa: rodar (rede) ----------------------------------------------------

def etapa_rodar(limiar: float) -> dict:
    dentro, _ = decidir_lote(_metricas_do_disco(), limiar)
    estado = EstadoLote(SAIDA / "estado.json").carregar()
    pressao = PressaoDoSite()      # contador de 503 do LOTE (§2.4)
    custo, t0 = {}, time.time()

    for d in dentro:
        if estado.status(d.slug) == "concluido":
            print(f"  [pulado] {d.slug}", flush=True)
            continue
        f = Fetcher(cache_dir=str(RAIZ / "resultado" / "cache"), pressao=pressao)
        try:
            entrada = coletar_passada(f, d.slug, raiz=BRUTO, motivo=d.motivo)
        except SobrecargaError as e:
            estado.marcar_falhou(d.slug, f"sobrecarga_503: {e}")
            estado.salvar()
            print(f"\nPARADO — {e}", flush=True)
            break
        except Exception as e:      # noqa: BLE001 — falha isolada por filme
            estado.marcar_falhou(d.slug, f"{type(e).__name__}: {e}")
            estado.salvar()
            print(f"  [falhou] {d.slug} — {type(e).__name__}: {e}", flush=True)
            continue
        custo[d.slug] = {"requisicoes": f.n_network, "cache": f.n_cache,
                         "n_novas": entrada["n_novas"],
                         "paginas": sum(entrada["paginas_gastas_por_nivel"].values()),
                         "retentativa": f.telemetria_retentativa()}
        estado.marcar_concluido(d.slug, n_por_bucket={},
                                requisicoes=f.n_network)
        estado.salvar()
        print(f"  [ok] {d.slug} — {f.n_network} req · "
              f"{entrada['n_novas']} novas · "
              f"{f.n_retentativas} retentativas", flush=True)

    total = sum(c["requisicoes"] for c in custo.values())
    rel = {"segundos": round(time.time() - t0, 1), "por_filme": custo,
           "requisicoes_total": total,
           "retentativas_total": sum(c["retentativa"]["n_retentativas"]
                                     for c in custo.values()),
           "n_503": pressao.n_503}
    print(f"\n{total} requisições · {rel['segundos']/3600:.2f}h · "
          f"{rel['retentativas_total']} retentativas · {pressao.n_503} × 503")
    return rel


# --- etapa: simular (Entrega 5) --------------------------------------------

def _selecionar_com_cota(slug, reviews, cota, orcamento):
    meta, _ = carregar(slug, raiz=BRUTO)
    hist = {float(k): v for k, v in (meta or {}).get("histograma_bruto", {}).items()}
    return selecionar(reviews, hist or None, cota_por_bucket=cota,
                      orcamento_paginas_por_nivel=orcamento or None)


def _orc_base(meta):
    return {float(k): v for k, v in
            (meta or {}).get("orcamento_paginas_por_nivel", {}).items()}


def _orc_passada(meta):
    for p in (meta or {}).get("passadas", []):
        if p.get("ordenacao") == ORDENACAO_PASSADA:
            return {float(k): v for k, v in p["orcamento_paginas_por_nivel"].items()}
    return {}


def _resumo_cenario(escolhidas_por_bucket: dict) -> dict:
    saida = {}
    for nome, escolhidas in escolhidas_por_bucket.items():
        antigas = [r for r in escolhidas if r.ordenacao_origem == ORDENACAO_PASSADA]
        saida[nome] = {
            "n_final": len(escolhidas),
            "fecha_cota": len(escolhidas) >= COTA_POR_BUCKET,
            "n_antigas": len(antigas),
            "n_chars_medio": (round(st.mean([r.n_chars for r in escolhidas]), 1)
                              if escolhidas else None),
            "janela": janela_temporal(escolhidas),
        }
    return saida


def _escolhidas(sel) -> dict:
    return {nome: [r for ns in sel[nome].niveis.values() for r in ns.validas]
            for nome in sel}


def simular_filme(slug: str) -> dict:
    meta, recentes, antigas = _duas_pontas(slug)
    orc_b, orc_p = _orc_base(meta), _orc_passada(meta)
    mapa = mapa_de_niveis()

    # S1 — seleção ATUAL: pool inteiro, sem consciência de ordenação.
    s1 = _escolhidas(_selecionar_com_cota(slug, recentes + antigas,
                                          COTA_POR_BUCKET, orc_b))

    def dividida(fracao_antiga_por_bucket):
        saida = {}
        for nome, niveis in mapa.items():
            fa = fracao_antiga_por_bucket[nome]
            cota_antiga = round(COTA_POR_BUCKET * fa)
            cota_recente = COTA_POR_BUCKET - cota_antiga
            esc = []
            if cota_recente:
                esc += _escolhidas(_selecionar_com_cota(
                    slug, recentes, cota_recente, orc_b))[nome]
            if cota_antiga:
                esc += _escolhidas(_selecionar_com_cota(
                    slug, antigas, cota_antiga, orc_p))[nome]
            saida[nome] = esc
        return saida

    s2 = dividida({nome: 0.30 for nome in mapa})

    fracoes = {}
    for nome, niveis in mapa.items():
        n_a = sum(1 for r in antigas if r.nivel in niveis)
        n_r = sum(1 for r in recentes if r.nivel in niveis)
        fracoes[nome] = (n_a / (n_a + n_r)) if (n_a + n_r) else 0.0
    s3 = dividida(fracoes)

    return {
        "fracao_antiga_no_bruto": {k: round(v, 4) for k, v in fracoes.items()},
        "S1": _resumo_cenario(s1),
        "S2": _resumo_cenario(s2),
        "S3": _resumo_cenario(s3),
    }


def etapa_simular(slugs: list[str]) -> dict:
    return {"filmes": {s: simular_filme(s) for s in slugs}}


# --- comparação (Entrega 4) -------------------------------------------------

def comparar(antes: dict, depois: dict) -> dict:
    """Antes × depois, por filme e agregado. Imprime a tabela do relatório."""
    linhas, agregado = {}, {"anos_antes": [], "anos_depois": [],
                            "p5p95_antes": [], "p5p95_depois": []}
    print(f"{'filme':38s} {'n antes':>8s} {'+antigas':>9s} "
          f"{'p5 antes':>10s} {'p5 depois':>10s} {'anos':>6s} {'buckets 40':>11s}")
    for slug, a in antes["filmes"].items():
        d = depois["filmes"].get(slug)
        if not d:
            continue
        ja, jd = a["janela_total"], d["janela_total"]
        antiga = d["ponta_antiga"]
        b_a = sum(1 for b in a["buckets"].values() if b["fecha_cota"])
        b_d = sum(1 for b in d["buckets"].values() if b["fecha_cota"])
        linhas[slug] = {
            "n_bruto_antes": a["n_bruto"], "n_bruto_depois": d["n_bruto"],
            "n_antigas": (antiga or {}).get("n", 0),
            "janela_antes": ja, "janela_depois": jd,
            "anos_antes": _anos(ja), "anos_depois": _anos(jd),
            "p5_p95_antes": _dias_p5_p95(ja), "p5_p95_depois": _dias_p5_p95(jd),
            "buckets_na_cota_antes": b_a, "buckets_na_cota_depois": b_d,
            "perfil_antigo": antiga, "perfil_recente": d["ponta_recente"],
        }
        for k, v in (("anos_antes", _anos(ja)), ("anos_depois", _anos(jd)),
                     ("p5p95_antes", _dias_p5_p95(ja)),
                     ("p5p95_depois", _dias_p5_p95(jd))):
            if v is not None:
                agregado[k].append(v)
        print(f"{slug:38s} {a['n_bruto']:8d} {linhas[slug]['n_antigas']:9d} "
              f"{(ja or {}).get('p5', '—'):>10s} {(jd or {}).get('p5', '—'):>10s} "
              f"{_anos(jd) or 0:6.2f} {b_a:5d} → {b_d:3d}")
    resumo = {k: (round(st.median(v), 2) if v else None)
              for k, v in agregado.items()}
    print(f"\nmediana anos (min-max): {resumo['anos_antes']} → {resumo['anos_depois']}")
    print(f"mediana dias p5-p95:    {resumo['p5p95_antes']} → {resumo['p5p95_depois']}")
    return {"por_filme": linhas, "mediana": resumo}


def _dias_p5_p95(janela) -> int | None:
    """Cobertura ROBUSTA — min/max são dominados por um outlier de data
    assistida (§3[B']); p5-p95 é o que a amostra realmente cobre."""
    if not janela:
        return None
    from datetime import date

    def d(s):
        y, m, dd = (int(x) for x in s[:10].split("-"))
        return date(y, m, dd)
    return (d(janela["p95"]) - d(janela["p5"])).days


# --- CLI --------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["metrica", "selecionar", "antes", "rodar",
                                      "depois", "comparar", "simular"])
    ap.add_argument("--limiar", type=float, default=LIMIAR_PASSADA_ANTIGA)
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    def grava(nome, dado):
        (SAIDA / nome).write_text(json.dumps(dado, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"→ resultado/v196-passada/{nome}")

    if args.etapa == "metrica":
        m = etapa_metrica()
        com = sum(1 for v in m.values() if v)
        grava("metrica.json", m)
        print(f"{com}/{len(m)} filmes com métrica mensurável")
        return

    if args.etapa == "selecionar":
        grava("selecao.json", etapa_selecionar(args.limiar))
        return

    if args.etapa in ("antes", "depois"):
        dentro, _ = decidir_lote(_metricas_do_disco(), args.limiar)
        f = foto([d.slug for d in dentro])
        grava(f"{args.etapa}.json", f)
        n40 = sum(1 for d in f["filmes"].values()
                  for b in d["buckets"].values() if b["fecha_cota"])
        anos = [_anos(d["janela_total"]) for d in f["filmes"].values()]
        anos = [a for a in anos if a is not None]
        print(f"  {f['n_filmes']} filmes · buckets na cota {n40}/{3*f['n_filmes']}")
        print(f"  cobertura do bruto (anos): mediana {st.median(anos):.2f} · "
              f"max {max(anos):.2f}")
        return

    if args.etapa == "comparar":
        a = json.loads((SAIDA / "antes.json").read_text(encoding="utf-8"))
        d = json.loads((SAIDA / "depois.json").read_text(encoding="utf-8"))
        grava("comparacao.json", comparar(a, d))
        return

    if args.etapa == "rodar":
        grava("custo.json", etapa_rodar(args.limiar))
        return

    dentro, _ = decidir_lote(_metricas_do_disco(), args.limiar)
    grava("simulacao.json", etapa_simular([d.slug for d in dentro]))


if __name__ == "__main__":
    main()
