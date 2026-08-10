"""[v1.9.5, Entregas 4-5] Recoleta sob a âncora nova + medição antes/depois.

O número que valida (ou reprova) a sessão é o **gap raso-vs-profundo em dias**.
Ele era mediana de 3 dias sob a âncora da v1.9.2. Se continuar em ~3, o desenho
falhou — e é para reportar como falha, não maquiar.

Uso:
    python scripts/recoleta_v195.py antes     # fotografa, sem tocar a rede
    python scripts/recoleta_v195.py recoletar
    python scripts/recoleta_v195.py depois    # fotografa e compara
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import carregar, percentil  # noqa: E402
from espectro24.buckets import FRONTEIRAS, mapa_de_niveis  # noqa: E402
from espectro24.alocacao import dividir_raso_profundo  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.lote import rodar_lote  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

SAIDA = RAIZ / "resultado" / "v195-recoleta"
ARQ_ANTES = SAIDA / "antes.json"
ARQ_DEPOIS = SAIDA / "depois.json"
ARQ_CUSTO = SAIDA / "custo.json"


def _dia(s):
    return s[:10] if s and len(s) >= 10 else None


def _data(s):
    s = _dia(s)
    if not s:
        return None
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return date(y, m, d)
    except ValueError:
        return None


def _med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def _n_raso(nivel, orc):
    o = orc.get(nivel)
    return dividir_raso_profundo(o)[0] if o else 0


def _perfil(reviews, orc):
    if not reviews:
        return None
    pg = sorted(r.pagina_origem for r in reviews)
    prof = sum(1 for r in reviews if r.pagina_origem > _n_raso(r.nivel, orc))
    ds = sorted(d for d in (_dia(r.data) for r in reviews) if d)
    dias = None
    if ds:
        a, b = _data(percentil(ds, 0.05)), _data(percentil(ds, 0.95))
        dias = (b - a).days if a and b else None
    return {"n": len(reviews), "pagina_min": pg[0], "pagina_max": pg[-1],
            "pagina_p50": percentil(pg, 0.50), "pagina_p95": percentil(pg, 0.95),
            "n_profundas": prof, "fracao_profunda": prof / len(reviews),
            "dias_p5_p95": dias,
            "data_min": ds[0] if ds else None, "data_max": ds[-1] if ds else None}


def _gap_raso_profundo(todas, orc):
    """O número que valida a sessão: mediana(data do raso) − mediana(data do
    profundo), em dias. Era 3 sob a âncora da v1.9.2."""
    r_ds, p_ds = [], []
    for r in todas:
        dt = _data(r.data)
        if not dt:
            continue
        nr = _n_raso(r.nivel, orc)
        (p_ds if (nr and r.pagina_origem > nr) else r_ds).append(dt)
    if not r_ds or not p_ds:
        return None
    return {"gap_dias": (_med(r_ds) - _med(p_ds)).days,
            "n_raso": len(r_ds), "n_profundo": len(p_ds),
            "mais_antiga_profunda": str(min(p_ds)),
            "mais_antiga_rasa": str(min(r_ds))}


def dias_por_100_paginas(todas, ) -> dict | None:
    """Quanto TEMPO cada 100 páginas da listagem cobre.

    É o diagnóstico decisivo desta versão, e é uma propriedade da LISTAGEM,
    não da amostra: mede a mediana de `data` da página mais rasa contra a da
    mais profunda presentes no bruto. Um valor baixo significa que paginar
    fundo não alcança o passado — não importa a âncora nem o orçamento.
    """
    por_pag: dict[int, list] = {}
    for r in todas:
        dt = _data(r.data)
        if dt:
            por_pag.setdefault(r.pagina_origem, []).append(dt)
    if len(por_pag) < 2:
        return None
    p_min, p_max = min(por_pag), max(por_pag)
    dias = (_med(por_pag[p_min]) - _med(por_pag[p_max])).days
    return {"pagina_min": p_min, "pagina_max": p_max, "dias": dias,
            "dias_por_100_paginas": 100 * dias / max(1, p_max - p_min),
            # Quantas páginas seriam necessárias para cobrir 1 ano — contra o
            # teto de plataforma de 256.
            "paginas_para_1_ano": (round(365 * max(1, p_max - p_min) / dias)
                                   if dias > 0 else None)}


def foto() -> dict:
    filmes = {}
    for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
        if not (d / "meta.json").exists():
            continue
        slug = d.name
        meta, todas = carregar(slug)
        hist = {float(k): v for k, v in (meta or {}).get("histograma_bruto", {}).items()}
        orc = {float(k): v for k, v in
               (meta or {}).get("orcamento_paginas_por_nivel", {}).items()}
        if not hist:
            continue
        sel = selecionar(todas, hist, orcamento_paginas_por_nivel=orc or None)
        buckets = {}
        for nome, niveis in mapa_de_niveis().items():
            escolhidas = [r for n in sel[nome].niveis
                          for r in sel[nome].niveis[n].validas]
            buckets[nome] = {
                "n_final": sel[nome].n_final,
                "estado_piso": sel[nome].estado_piso,
                "bruto": _perfil([r for r in todas if r.nivel in niveis], orc),
                "amostra": _perfil(escolhidas, orc),
            }
        filmes[slug] = {
            "n_bruto": len(todas), "buckets": buckets,
            "gap": _gap_raso_profundo(todas, orc),
            "dias_por_100_paginas": dias_por_100_paginas(todas),
            "profundidade_sondagem": (meta or {}).get("profundidade_sondagem"),
            "profundidade_estimada_por_nivel":
                (meta or {}).get("profundidade_estimada_por_nivel"),
            "paginas_gastas_por_nivel": (meta or {}).get("paginas_gastas_por_nivel"),
        }
    return {"filmes": filmes, "n_filmes": len(filmes)}


def _resumo(f: dict) -> None:
    gaps = [d["gap"]["gap_dias"] for d in f["filmes"].values() if d["gap"]]
    n40 = sum(1 for d in f["filmes"].values()
              for b in d["buckets"].values() if b["n_final"] >= 40)
    prof = [b["amostra"]["fracao_profunda"] for d in f["filmes"].values()
            for b in d["buckets"].values() if b["amostra"]]
    pg = [b["amostra"]["pagina_p95"] for d in f["filmes"].values()
          for b in d["buckets"].values() if b["amostra"]]
    dias = [b["amostra"]["dias_p5_p95"] for d in f["filmes"].values()
            for b in d["buckets"].values()
            if b["amostra"] and b["amostra"]["dias_p5_p95"] is not None]
    print(f"  filmes {f['n_filmes']} · buckets a 40: {n40}/105")
    print(f"  GAP raso-profundo (dias): mediana {_med(gaps)} · media {st.mean(gaps):.0f} "
          f"· <=7d em {sum(1 for g in gaps if g <= 7)}/{len(gaps)} filmes")
    print(f"  amostra: fração profunda {100*st.mean(prof):.1f}% · "
          f"página p95 mediana {_med(pg)} · janela mediana {_med(dias)}d")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["antes", "recoletar", "depois"])
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.etapa in ("antes", "depois"):
        f = foto()
        alvo = ARQ_ANTES if args.etapa == "antes" else ARQ_DEPOIS
        alvo.write_text(json.dumps(f, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        print(f"[{args.etapa}] → {alvo.relative_to(RAIZ)}")
        _resumo(f)
        return

    slugs = sorted(d.name for d in (RAIZ / "dados" / "bruto").iterdir()
                   if (d / "meta.json").exists())
    fetchers: dict[str, Fetcher] = {}

    def fabrica(slug: str) -> Fetcher:
        f = Fetcher(cache_dir="resultado/cache")
        fetchers[slug] = f
        return f

    t0 = time.time()
    rel = rodar_lote(
        slugs, dados_dir=str(RAIZ / "dados" / "bruto"),
        estado_path=SAIDA / "estado.json", fabrica_fetcher=fabrica,
        on_progress=lambda s, st_, m: print(
            f"  [{st_}] {s}" + (f" — {m}" if m else ""), flush=True))
    dt = time.time() - t0

    custo = {
        "segundos": round(dt, 1), "n_concluidos": rel.n_concluidos,
        "n_pulados": rel.n_pulados, "n_falhas": rel.n_falhas,
        "falhas": rel.falhas,
        "rede_por_filme": {s: f.n_network for s, f in fetchers.items()},
        "cache_por_filme": {s: f.n_cache for s, f in fetchers.items()},
        "rede_total": sum(f.n_network for f in fetchers.values()),
        "projecao": {"requisicoes": 1400, "horas": 1.5},
    }
    ARQ_CUSTO.write_text(json.dumps(custo, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\n{custo['rede_total']} requisições · {dt/3600:.2f}h · "
          f"{rel.n_concluidos} ok / {rel.n_falhas} falhas")


if __name__ == "__main__":
    main()
