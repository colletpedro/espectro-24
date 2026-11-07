"""τ do pareamento do M2, pelo `finetune/DESVIO_P03.md` — só dados de TREINO.

Lê a geração base da Fase 1 (`finetune/especificidade/geracao_base/`, 5 filmes
de TREINO × 3 buckets, conferida contra o manifesto, bullets `completo`) e os
publicados desses 5 do commit fixo (`comum.entradas_do_commit`). Com o
pareamento de `metricas.parear` (e5, húngaro) SEM limiar:

- D₀ (nula): base (x, b) × publicado (y, b), x ≠ y, os 60 pares ordenados de
  filmes × 3 buckets; todos os cossenos atribuídos;
- τ = percentil 95 de D₀ pelo posto mais próximo, arredondado PARA CIMA na 3ª
  casa; sem alternativa;
- D₁ (só descrição): base (x, b) × publicado (x, b), 15 atribuições.

Subcomando:
    fixar   (Mac) grava `finetune/fase4/tau_m2.json` UMA vez
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import especificidade_validacao as V  # noqa: E402
import metricas as M  # noqa: E402

ARQ_DESVIO = K.FINETUNE_DIR / "DESVIO_P03.md"
ARQ_TAU = K.FINETUNE_DIR / "fase4" / "tau_m2.json"
PASTA_SINTESE_T = K.FINETUNE_DIR / "fase2" / "sintese_treinado"
PERCENTIL = 0.95
CASAS = 3


def percentil_posto(vals: list[float], p: float = PERCENTIL) -> float:
    """O valor na posição ⌈p·N⌉ da lista crescente (1-indexada)."""
    xs = sorted(vals)
    return xs[max(1, math.ceil(p * len(xs))) - 1]


def arredondar_para_cima(x: float, casas: int = CASAS) -> float:
    f = 10 ** casas
    return math.ceil(round(x * f, 9)) / f


def temas_base(split: dict) -> dict[tuple[str, str], list[dict]]:
    """(slug, bucket) → temas da geração base, na forma de `metricas.parear`."""
    out: dict[tuple[str, str], list[dict]] = {}
    for b in V.bullets_base(split):          # confere treino, manifesto, `completo`
        out.setdefault((b["slug"], b["bucket"]), []).append(
            {"tema": b["tema"], "exemplo_parafraseado": b["exemplo"]})
    return out


def temas_publicado(slugs: list[str]) -> dict[tuple[str, str], list[dict]]:
    out = {}
    for slug in slugs:
        for b in K.ler_json(K.RESULTADO_DIR / f"{slug}.json")["buckets"]:
            out[(slug, b["bucket"])] = list(b.get("temas") or [])
    return out


def distribuicoes(base: dict, pub: dict, slugs: list[str], parear) -> tuple[list[float], list[float]]:
    """(D₀, D₁): cossenos atribuídos entre filmes diferentes e no mesmo filme.
    `parear(temas_a, temas_b)` devolve [(i, j, cos)] sem limiar."""
    d0, d1 = [], []
    for bucket in K.BUCKETS:
        for x in slugs:
            for y in slugs:
                cos = [c for _, _, c in parear(base[(x, bucket)], pub[(y, bucket)])]
                (d1 if x == y else d0).extend(cos)
    return d0, d1


def quantis(vals: list[float]) -> dict:
    return {f"p{int(q * 100):02d}": round(percentil_posto(vals, q), 4)
            for q in (0.05, 0.25, 0.50, 0.75, 0.95)} if vals else {}


def cmd_fixar(a) -> None:
    import encoder_e5 as E5

    if not V._versionado_e_limpo(ARQ_DESVIO):
        raise SystemExit(f"{ARQ_DESVIO.name} não está commitado (ou mudou): o critério vem antes")
    if ARQ_TAU.exists():
        raise SystemExit(f"{ARQ_TAU} já existe: o τ é fixado UMA vez")
    if (PASTA_SINTESE_T / "manifesto.json").exists():
        raise SystemExit("a síntese do treinado já existe: o τ tinha de ser fixado ANTES")
    split = K.ler_json(a.split)
    base = temas_base(split)
    slugs = sorted({s for s, _ in base})
    if len(slugs) != 5 or set(base) != {(s, b) for s in slugs for b in K.BUCKETS}:
        raise SystemExit(f"geração base com {len(slugs)} filmes / {len(base)} buckets (esperados 5 × 3)")
    enc = E5.Encoder.do_disco()
    with K.entradas_do_commit(slugs) as ent:
        pub = temas_publicado(slugs)
    d0, d1 = distribuicoes(base, pub, slugs,
                           lambda ta, tb: M.parear(ta, tb, enc, float("-inf")))
    tau = arredondar_para_cima(percentil_posto(d0))
    out = {"gerado_por": "scripts/finetune/tau_m2.py fixar",
           "criterio": "percentil 95 (posto mais próximo) de D₀, arredondado para cima na 3ª casa",
           "tau": tau, "percentil_95_bruto": percentil_posto(d0),
           "D0": {"n": len(d0), "atribuicoes": 3 * len(slugs) * (len(slugs) - 1), **quantis(d0)},
           "D1": {"n": len(d1), "atribuicoes": 3 * len(slugs), **quantis(d1),
                  "fracao_ge_tau": round(sum(c >= tau for c in d1) / len(d1), 4) if d1 else None},
           "filmes": slugs, "modelo_e5": E5.MODELO_ID, "e5_snapshot": enc._dir.name,
           "desvio_sha256": K.sha256_arquivo(ARQ_DESVIO),
           "manifesto_geracao_base_sha256": K.sha256_arquivo(V.ARQ_MANIFESTO_BASE),
           "split_sha256": K.sha256_arquivo(a.split),
           "entradas": {k: ent[k] for k in ("commit", "n_arquivos", "sha256")},
           "script_sha256": K.sha256_arquivo(Path(__file__))}
    ARQ_TAU.parent.mkdir(parents=True, exist_ok=True)
    ARQ_TAU.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def ler_tau() -> float:
    """O τ fixado (para o M2 da Fase 4); recusa sem o arquivo do DESVIO_P03."""
    if not ARQ_TAU.exists():
        raise SystemExit(f"sem {ARQ_TAU}: rode `tau_m2.py fixar` (DESVIO_P03) antes do M2")
    return float(K.ler_json(ARQ_TAU)["tau"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fixar")
    a = ap.parse_args()
    {"fixar": cmd_fixar}[a.cmd](a)


if __name__ == "__main__":
    main()
