"""Quais filmes foram classificados em GEMINI — operacional, NÃO produto.

Para o dono escolher o que recoletar em DeepSeek quando houver saldo
(ABERTO.md C22). Lê o DADO, sem reprocessar e sem rede:
`resultado/votacao-3/consenso.jsonl` (a marca `classificacao_excecao` de cada
linha da exceção C22), e o relatório do gate
(`resultado/auditoria-acuracia/gemini/gate.json` e `gate_batch.json`).

Por filme: quantas reviews estão no consenso em Gemini, quantas tiveram o
passe 3 dispensado, as camadas e os modelos EFETIVOS que responderam, e — se
o filme já está publicado — os eixos em que ele declara CONTRASTE (algum
bucket acima da margem), cada um com o F1 do gate em Gemini e a diferença
contra o DeepSeek. Um eixo de contraste com ΔF1 negativo é o primeiro
candidato a recoleta.

Nada disto vai para a página: o JSON publicado não é tocado.

**`--barra` — a conferência que a síntese em Gemini não tinha (2026-09-22).**
A BARRA de cada bullet é `mencoes_aproximadas / n`, e `mencoes_aproximadas` é
a contagem ESTIMADA pela síntese (o LLM), não pela classificação; o único
validador sobre ela é o clamp em [0, n]. O risco histórico registrado do
Gemini é inflar contagem (`config.PROVIDER_POR_ESTAGIO`). Sem gabarito de
síntese, a conferência possível é contra o número de CÓDIGO do mesmo eixo:
para cada célula do bloco `eixos` (tema rotulado num eixo), Δ = fração da
síntese − fração da classificação. A linha de base é a distribuição de Δ nos
buckets sintetizados pelo DeepSeek (1.451 células nos 99, medida em
2026-09-22: mediana −0,075, p10 −0,375, p90 +0,150). Por filme em Gemini:
a mediana do Δ e as células acima do p90 da base.

**`--recusas` — quanto o filtro de conteúdo do Gemini custa em cada filme
(2026-09-23).** Para todo filme com review recusada (`espectro24.recusas`),
o bloco `eixos` é recalculado pela MESMA função de produção
(`eixos.montar_bloco`, zero LLM) em dois cenários, SÓ COMO MEDIDA — o (b)
nunca é publicado nem gravado:
  (a) a amostra publicável — com as substitutas, classificação Gemini;
  (b) a amostra original — as recusadas no lugar das substitutas, com os
      votos DeepSeek ARQUIVADOS (`_arquivo_deepseek_c22/`), consenso 2 de 3
      (com 2 passes só quando concordam; senão, "indeterminado"). O
      verificador DeepSeek nunca rodou nos 55: `impacto_emocional` dessas
      reviews é medido nos dois sentidos (mantido e removido).
Se algum BULLET (papel de algum eixo em algum bucket) ou o ESTADO de
contraste muda entre (a) e (b), o filme é **candidato prioritário à recoleta
em DeepSeek**, com o motivo. Ressalva de desenho: (b) mistura provider (as
recusadas por DeepSeek, o resto por Gemini) — a diferença mede o filtro E o
provider das 1-4 reviews, não o filtro puro; o que o Gemini marcaria nelas é
desconhecido, porque ele as recusou.

Uso:
    python scripts/proveniencia_classificacao.py            # tabela
    python scripts/proveniencia_classificacao.py --recusas  # custo do filtro por filme
    python scripts/proveniencia_classificacao.py --barra    # + conferência da barra
    python scripts/proveniencia_classificacao.py --json     # para outro script
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONSENSO = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"
GATES = {"padrao": RAIZ / "resultado" / "auditoria-acuracia" / "gemini" / "gate.json",
         "batch": RAIZ / "resultado" / "auditoria-acuracia" / "gemini" / "gate_batch.json"}
DECISIVA = "producao_consenso_mais_v2_passe1"


def gate_por_eixo() -> dict[str, dict]:
    """`{modo: {eixo: {f1_gemini, delta_f1, ic95}}}` na configuração de
    produção (consenso + V2 passada única)."""
    saida = {}
    for modo, arq in GATES.items():
        if arq.exists():
            g = json.loads(arq.read_text(encoding="utf-8"))
            saida[modo] = {e: {k: v[k] for k in ("f1_gemini", "f1_deepseek",
                                                 "delta_f1", "ic95")}
                           for e, v in g["gate_por_eixo"].items()}
    return saida


def filmes_em_gemini(consenso: Path = CONSENSO) -> dict[str, dict]:
    por = defaultdict(lambda: {"n_reviews": 0, "n_passe_3_dispensado": 0,
                               "camadas": Counter(), "modelos_efetivos": Counter(),
                               "excecao": set()})
    with consenso.open(encoding="utf-8") as fh:
        for linha in fh:
            if not linha.strip():
                continue
            r = json.loads(linha)
            m = r.get("classificacao_excecao")
            if not m:
                continue
            f = por[r["slug"]]
            f["n_reviews"] += 1
            f["n_passe_3_dispensado"] += bool(r.get("passe_3_dispensado"))
            f["camadas"].update(m.get("camadas") or [])
            f["modelos_efetivos"].update(m.get("modelos_efetivos") or [])
            f["excecao"].add(m.get("excecao"))
    return {s: {**v, "camadas": dict(v["camadas"]),
                "modelos_efetivos": dict(v["modelos_efetivos"]),
                "excecao": sorted(map(str, v["excecao"]))}
            for s, v in sorted(por.items())}


def eixos_de_contraste(slug: str) -> list[str] | None:
    arq = RAIZ / "resultado" / f"{slug}.json"
    if not arq.exists():
        return None
    eixos = (json.loads(arq.read_text(encoding="utf-8")).get("eixos") or {})
    return sorted(l["eixo"] for l in eixos.get("linhas", [])
                  if any((b or {}).get("acima_da_margem")
                         for b in l.get("por_bucket", {}).values()))


def deltas_da_barra(d: dict) -> list[dict]:
    """Por célula do bloco `eixos`: fração da síntese − fração da
    classificação, com o provider que sintetizou o bucket."""
    temas = {b["bucket"]: {t["tema"]: t for t in b.get("temas") or []}
             for b in d.get("buckets", [])}
    gemini_bucket = {b["bucket"]: bool(b.get("fallback_conteudo"))
                     for b in d.get("buckets", [])}
    em_excecao = bool(d.get("proveniencia_llm"))
    saida = []
    for l in (d.get("eixos") or {}).get("linhas", []):
        for bucket, c in (l.get("por_bucket") or {}).items():
            if not c or not c.get("tema") or not c.get("de_n"):
                continue
            t = temas.get(bucket, {}).get(c["tema"])
            if not t or not t.get("n_reviews_analisadas"):
                continue
            fs = t["mencoes_aproximadas"] / t["n_reviews_analisadas"]
            fc = c["mencoes"] / c["de_n"]
            saida.append({"bucket": bucket, "eixo": l["eixo"], "tema": c["tema"],
                          "sintese": round(fs, 3), "classificacao": round(fc, 3),
                          "delta": round(fs - fc, 3),
                          "gemini": em_excecao or gemini_bucket.get(bucket, False)})
    return saida


def conferir_barra() -> dict:
    base, por_filme = [], defaultdict(list)
    for arq in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        for c in deltas_da_barra(d):
            (por_filme[d["slug"]] if c["gemini"] else base).append(c)
    q = sorted(c["delta"] for c in base)
    ref = {"n": len(q), "mediana": q[len(q) // 2], "p10": q[len(q) // 10],
           "p90": q[9 * len(q) // 10]} if q else {}
    filmes = {}
    for slug, cs in por_filme.items():
        ds = sorted(c["delta"] for c in cs)
        filmes[slug] = {"n_celulas": len(cs), "mediana": ds[len(ds) // 2],
                        "acima_do_p90_da_base": [c for c in cs
                                                 if ref and c["delta"] > ref["p90"]]}
    return {"base_deepseek": ref, "filmes_gemini": filmes}


ARQUIVO_DS = RAIZ / "resultado" / "votacao-3" / "_arquivo_deepseek_c22"


def _consenso_arquivado(ids: set[str], slug: str) -> dict[str, list[str] | None]:
    """Consenso DeepSeek das reviews `ids` a partir dos passes ARQUIVADOS.
    `None` = indeterminado (menos de 2 passes, ou 2 passes que divergem)."""
    votos: dict[str, list[set]] = defaultdict(list)
    for n in (1, 2, 3):
        arq = ARQUIVO_DS / f"passe_{n}.jsonl"
        if not arq.exists():
            continue
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            r = json.loads(linha)
            if r.get("slug") == slug and r.get("ok") and r["id"] in ids:
                votos[r["id"]].append(set(r["eixos"]))
    saida: dict[str, list[str] | None] = {}
    for rid in ids:
        vs = votos.get(rid, [])
        if len(vs) >= 3 or (len(vs) == 2 and vs[0] == vs[1]):
            c = Counter(e for v in vs for e in v)
            saida[rid] = sorted(e for e, k in c.items() if k >= 2)
        else:
            saida[rid] = None
    return saida


def _papeis(bloco: dict) -> dict[tuple[str, str], str | None]:
    return {(l["eixo"], b): p for l in bloco["linhas"]
            for b, p in (l.get("bullet_de") or {}).items() if p}


def impacto_das_recusas(slug: str) -> dict:
    """Cenários (a) e (b) do docstring para UM filme. Zero rede, zero LLM."""
    import copy
    sys.path.insert(0, str(RAIZ / "src"))
    from espectro24 import eixos as E
    from espectro24 import recusas as R
    from espectro24.pipeline import ids_analisados_do_bruto

    rs = [r for r in R.recusas() if r["slug"] == slug]
    cat = E.carregar_classificacao(
        RAIZ / "resultado" / "votacao-3" / "consenso_verificado.jsonl").get(slug)
    if not rs or not cat:
        return {"slug": slug, "estado": "sem recusa ou sem classificação"}
    arq_json = RAIZ / "resultado" / f"{slug}.json"
    coleta = (json.loads(arq_json.read_text(encoding="utf-8")).get("coleta")
              if arq_json.exists() else None)
    anal = {b: set(v) for b, v in ids_analisados_do_bruto(slug, coleta=coleta).items()}
    ds = _consenso_arquivado({r["id"] for r in rs}, slug)
    indeterminadas = sorted(i for i, e in ds.items() if e is None)

    def cenario(trocar: bool, sem_ie: bool = False) -> dict:
        c = copy.deepcopy(cat)
        a = {b: set(v) for b, v in anal.items()}
        if trocar:
            for r in rs:
                b, sub = r["bucket"], r.get("substituta")
                if sub and sub in c.get(b, {}):
                    c[b].pop(sub)
                    a[b].discard(sub)
                e = list(ds[r["id"]] or [])
                if sem_ie and "impacto_emocional" in e:
                    e.remove("impacto_emocional")
                c.setdefault(b, {})[r["id"]] = e
                a.setdefault(b, set()).add(r["id"])
        return E.montar_bloco(c, a, {})

    a = cenario(False)
    saida = {"slug": slug, "n_recusadas": len(rs),
             "recusadas": [{k: r[k] for k in ("bucket", "id", "bloqueio", "substituta")}
                           for r in rs],
             "consenso_deepseek_arquivado": ds, "indeterminadas": indeterminadas,
             "contraste_a": a.get("contraste"), "cenarios_b": {}}
    if indeterminadas:
        saida["estado"] = "indeterminado: sem consenso DeepSeek arquivado para " \
                          + ", ".join(indeterminadas)
        return saida
    pa = _papeis(a)
    motivos = []
    for nome, sem_ie in (("b_ie_mantido", False), ("b_ie_removido", True)):
        b = cenario(True, sem_ie)
        pb = _papeis(b)
        mud = sorted({k for k in set(pa) | set(pb) if pa.get(k) != pb.get(k)})
        saida["cenarios_b"][nome] = {
            "contraste": b.get("contraste"),
            "bullets_que_mudam": [{"eixo": e, "bucket": bk, "a": pa.get((e, bk)),
                                   "b": pb.get((e, bk))} for e, bk in mud]}
        if b.get("contraste") != a.get("contraste"):
            motivos.append(f"{nome}: contraste {a.get('contraste')} → {b.get('contraste')}")
        for e, bk in mud:
            motivos.append(f"{nome}: bullet {e}/{bk} {pa.get((e, bk))} → {pb.get((e, bk))}")
    saida["prioritario_recoleta_deepseek"] = bool(motivos)
    saida["motivos"] = motivos
    saida["estado"] = ("PRIORITÁRIO à recoleta em DeepSeek" if motivos
                       else "o filtro não muda bullet nem contraste")
    return saida


def impacto_de_todas_as_recusas() -> list[dict]:
    sys.path.insert(0, str(RAIZ / "src"))
    from espectro24 import recusas as R
    return [impacto_das_recusas(s) for s in sorted({r["slug"] for r in R.recusas()})]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--barra", action="store_true",
                    help="conferência da barra: contagem da síntese contra a "
                         "da classificação, Gemini contra a base DeepSeek")
    ap.add_argument("--recusas", action="store_true",
                    help="custo do filtro de conteúdo do Gemini por filme: "
                         "bullets e contraste com e sem as recusadas")
    a = ap.parse_args(argv)
    if a.recusas:
        rs = impacto_de_todas_as_recusas()
        if a.json:
            print(json.dumps(rs, ensure_ascii=False, indent=1))
            return 0
        for r in rs:
            print(f"{r['slug']:36} {r.get('n_recusadas', 0)} recusada(s) · "
                  f"contraste(a)={r.get('contraste_a')} · {r['estado']}")
            for m in r.get("motivos", []):
                print(f"    {m}")
        return 0
    if a.barra:
        r = conferir_barra()
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
            return 0
        b = r["base_deepseek"]
        print(f"base DeepSeek: {b['n']} células · Δ mediana {b['mediana']:+.3f} · "
              f"p10 {b['p10']:+.3f} · p90 {b['p90']:+.3f}")
        for slug, f in sorted(r["filmes_gemini"].items()):
            print(f"  {slug:40} {f['n_celulas']:3} células · Δ mediana "
                  f"{f['mediana']:+.3f} · acima do p90 da base: "
                  f"{len(f['acima_do_p90_da_base'])}")
            for c in f["acima_do_p90_da_base"]:
                print(f"      {c['bucket']}/{c['eixo']}: síntese {c['sintese']:.2f} "
                      f"× classificação {c['classificacao']:.2f} — {c['tema']}")
        return 0
    gate = gate_por_eixo()
    ref = gate.get("batch") or gate.get("padrao") or {}
    filmes = filmes_em_gemini()
    prioridade = {r["slug"]: r for r in impacto_de_todas_as_recusas()
                  if r.get("prioritario_recoleta_deepseek")}
    for slug, f in filmes.items():
        f["eixos_de_contraste"] = eixos_de_contraste(slug)
        if slug in prioridade:
            f["prioritario_recoleta_deepseek"] = prioridade[slug]["motivos"]
    if a.json:
        print(json.dumps({"gate": gate, "filmes": filmes}, ensure_ascii=False, indent=1))
        return 0
    print(f"{len(filmes)} filme(s) classificado(s) em Gemini (exceção C22)\n")
    print("F1 do gate por eixo (produção: consenso + V2), Gemini vs DeepSeek:")
    for e, v in ref.items():
        print(f"  {e:20} GM {v['f1_gemini']:.3f} · DS {v['f1_deepseek']:.3f} · "
              f"ΔF1 {v['delta_f1']:+.3f} {v['ic95']}")
    print()
    for slug, f in filmes.items():
        cont = f["eixos_de_contraste"]
        cont_txt = ("não publicado" if cont is None else
                    ", ".join(f"{e} (ΔF1 {ref[e]['delta_f1']:+.3f})" if e in ref else e
                              for e in cont) or "sem contraste")
        print(f"{slug:48} {f['n_reviews']:5} reviews · p3 dispensado "
              f"{f['n_passe_3_dispensado']:5} · camadas {f['camadas']} · "
              f"contraste: {cont_txt}")
        if f.get("prioritario_recoleta_deepseek"):
            print(f"    ★ PRIORITÁRIO à recoleta em DeepSeek — o filtro de "
                  f"conteúdo do Gemini muda o que publica: "
                  + "; ".join(f["prioritario_recoleta_deepseek"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
