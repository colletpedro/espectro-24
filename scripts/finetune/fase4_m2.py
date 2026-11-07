"""Fase 4 — M2 (concordância de `mencoes_aproximadas` com o publicado), DESCRITIVO.

Pelo `finetune/DESVIO_P03.md` ("Como o M2 é calculado na Fase 4"), sem mudar
nada do que lá está:

- τ = o de `finetune/fase4/tau_m2.json` (`tau_m2.py fixar`, só treino);
- por lado L ∈ {treinado, base} contra o publicado, nos buckets mantidos (os 89
  menos os fora por memória em qualquer lado), só onde os dois lados têm temas:
  `metricas.parear(temas_L, temas_P, e5, τ)` e `metricas.concordancia_bucket`;
- taxa de pareamento = Σ pares / Σ temas do publicado; DAM = Σ |m_L − m_P| /
  Σ pares; DAM relativa = Σ (|m_L − m_P| / n) / Σ pares; tau-b = mediana dos
  buckets com tau-b definido;
- IC 95% por filme da DAM relativa de cada lado e de treinado − base, com as
  reamostras do C1–C3 (`avaliar_c1_c4.reamostras`, semente 20261101).

Cegueira do dono: grava `finetune/fase4/cego/m2_fase4.json` e só imprime o
sha256 (`_cego.py`).

Subcomando:
    calcular   (Mac, depois da síntese do treinado)
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import _cego  # noqa: E402
import avaliar_c1_c4 as A  # noqa: E402
import fase4_especificidade as F  # noqa: E402
import metricas as M  # noqa: E402
import tau_m2 as T  # noqa: E402

ARQ_M2 = _cego.PASTA / "m2_fase4.json"
LADOS_M2 = ("treinado", "base")


def linha_do_bucket(slug: str, bucket: str, temas_l: list[dict], temas_p: list[dict],
                    parear) -> dict:
    """Um bucket: pares acima do τ e as somas que o agregado usa."""
    if not temas_l or not temas_p:
        return {"slug": slug, "bucket": bucket, "comparavel": False,
                "temas_p": len(temas_p), "pares": 0, "abs": 0.0, "abs_rel": 0.0, "tau_b": None}
    pares = parear(temas_l, temas_p)
    c = M.concordancia_bucket(temas_l, temas_p, pares)
    n = temas_p[0].get("n_reviews_analisadas") or 0
    dif = [abs(temas_l[i]["mencoes_aproximadas"] - temas_p[j]["mencoes_aproximadas"])
           for i, j, _ in pares]
    return {"slug": slug, "bucket": bucket, "comparavel": True, "temas_p": len(temas_p),
            "temas_l": len(temas_l), "pares": len(pares), "abs": float(sum(dif)),
            "abs_rel": float(sum(d / n for d in dif)) if n else 0.0, "tau_b": c["tau_b"]}


def por_filme(linhas: list[dict]) -> dict[str, dict]:
    f = collections.defaultdict(collections.Counter)
    for l in linhas:
        if l["comparavel"]:
            c = f[l["slug"]]
            c["temas_p"] += l["temas_p"]
            c["pares"] += l["pares"]
            c["abs"] += l["abs"]
            c["abs_rel"] += l["abs_rel"]
    return {s: dict(c) for s, c in f.items()}


def razao(pf: dict, filmes: list[str], num: str, den: str) -> float | None:
    d = sum(pf.get(s, {}).get(den, 0) for s in filmes)
    return sum(pf.get(s, {}).get(num, 0) for s in filmes) / d if d else None


def _ic(vals: list[float]) -> list[float] | None:
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    q = lambda p: vals[min(len(vals) - 1, int(p * len(vals)))]
    return [q(0.025), q(0.975)]


def resumo(linhas: list[dict], filmes: list[str], boot: list[list[str]]) -> dict:
    pf = por_filme(linhas)
    taus = [l["tau_b"] for l in linhas if l["tau_b"] is not None]
    return {"buckets_comparaveis": sum(l["comparavel"] for l in linhas),
            "buckets_sem_temas": sum(not l["comparavel"] for l in linhas),
            "pares": sum(l["pares"] for l in linhas),
            "temas_publicado": sum(l["temas_p"] for l in linhas if l["comparavel"]),
            "taxa_pareamento": razao(pf, filmes, "pares", "temas_p"),
            "dam": razao(pf, filmes, "abs", "pares"),
            "dam_relativa": razao(pf, filmes, "abs_rel", "pares"),
            "dam_relativa_ic95": _ic([razao(pf, b, "abs_rel", "pares") for b in boot]),
            "tau_b_mediana": statistics.median(taus) if taus else None,
            "buckets_com_tau_b": len(taus)}


def diferenca_dam(lt: list[dict], lb: list[dict], filmes: list[str], boot: list) -> dict:
    pt, pb = por_filme(lt), por_filme(lb)

    def d(fs):
        a, b = razao(pt, fs, "abs_rel", "pares"), razao(pb, fs, "abs_rel", "pares")
        return None if a is None or b is None else a - b
    return {"ponto": d(filmes), "ic95": _ic([d(b) for b in boot])}


def cmd_calcular(a) -> None:
    import encoder_e5 as E5

    if ARQ_M2.exists():
        raise SystemExit(f"{ARQ_M2} já existe: o M2 da Fase 4 é calculado UMA vez")
    tau = T.ler_tau()
    split = K.ler_json(a.split)
    pares_teste = A._pares_de_teste(split)
    regs = A.registros_gerados(pares_teste)
    if "treinado" not in regs:
        raise SystemExit("sem a síntese do treinado (`gerar_sintese_teste.py gerar --lado treinado`)")
    mantidos, fora = A.buckets_mantidos(pares_teste, regs)
    filmes = sorted({s for s, _ in mantidos})
    boot = A.reamostras(filmes)
    enc = E5.Encoder.do_disco()
    parear = lambda tl, tp: M.parear(tl, tp, enc, tau)
    linhas: dict[str, list[dict]] = {}
    with K.entradas_do_commit(sorted({s for s, _ in pares_teste})) as ent:
        docs: dict = {}
        pub = {k: A.bucket_do_lado("publicado", k[0], k[1], regs, docs) for k in mantidos}
        for lado in (l for l in LADOS_M2 if l in regs):
            linhas[lado] = [linha_do_bucket(s, b, A.bucket_do_lado(lado, s, b, regs, docs)
                                            .get("temas") or [], pub[(s, b)].get("temas") or [],
                                            parear) for s, b in mantidos]
    out = {"gerado_por": "scripts/finetune/fase4_m2.py calcular", "tau": tau,
           "tau_m2_sha256": K.sha256_arquivo(T.ARQ_TAU),
           "desvio_sha256": K.sha256_arquivo(T.ARQ_DESVIO),
           "semente_bootstrap": A.SEMENTE_BOOT, "reamostras": A.N_BOOT, "filmes": len(filmes),
           "buckets_mantidos": len(mantidos), "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
           "modelo_e5": E5.MODELO_ID, "e5_snapshot": enc._dir.name,
           "entradas": {k: ent[k] for k in ("commit", "n_arquivos", "sha256")},
           "manifestos": {l: K.sha256_arquivo(F.pasta_sintese(l) / "manifesto.json") for l in linhas},
           "script_sha256": K.sha256_arquivo(Path(__file__)),
           "lados": {l: resumo(ls, filmes, boot) for l, ls in linhas.items()},
           "por_bucket": linhas}
    if "base" in linhas:
        out["treinado_menos_base_dam_relativa"] = diferenca_dam(linhas["treinado"], linhas["base"],
                                                                filmes, boot)
    ARQ_M2.parent.mkdir(parents=True, exist_ok=True)
    ARQ_M2.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    _cego.Saida("treinado", "m2_treinado.log")(
        json.dumps({k: out[k] for k in ("tau", "lados")}, ensure_ascii=False),
        curto=f"calculado, {ARQ_M2.name} sha256 {K.sha256_arquivo(ARQ_M2)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calcular")
    a = ap.parse_args()
    {"calcular": cmd_calcular}[a.cmd](a)


if __name__ == "__main__":
    main()
