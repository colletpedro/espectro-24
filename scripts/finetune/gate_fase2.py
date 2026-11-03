"""Gate da Fase 2 — escreve `finetune/GATE_FASE2.md` (PREPARADO, NÃO RODADO; 2026-11-03).

Só roda DEPOIS de:
- `avaliar_c1_c4.py fixar-delta2` (δ₂ pela taxa de apoio ≥ 2 do publicado) e
- `avaliar_c1_c4.py calcular` com o δ₂ já fixado, com publicado E base julgados
  (`c1_c4_fase2.json`, `delta2_fixado` true).

Recusa se o treinado já tiver síntese de teste, se o `GATE_FASE2.md` já
estiver commitado, ou se as contas que ele refaz (taxas por lado) não forem as
do `c1_c4_fase2.json`.

O relatório traz (pré-registro, seções 3–5):
- C1–C4 do publicado e da base, cada taxa com IC 95% do bootstrap POR FILME
  (as MESMAS 10.000 reamostras, semente 20261101, de `avaliar_c1_c4`), e a
  diferença base − publicado já calculada pelo `calcular` (descritiva);
- o δ₂ fixado e o p₀;
- os buckets fora (o do Gemini; fora por memória) e por quê, com o outlier;
- os tempos (síntese da base por bucket; juiz por lado; `preparar`);
- a comparação DESCRITIVA com a medição antiga dos 5 de referência
  (publicado 2/90 sem apoio), avisando que as entradas diferem (o sha256 do
  reaproveitamento não bateu) e que a regra de parada não é a mesma;
- o que NÃO foi medido.

A última linha do arquivo é `<!-- gate_fase2 {…} -->`, com o sha256 do
`c1_c4_fase2.json` e do `delta2.json`: `gerar_sintese_teste.py gerar --lado
treinado` recusa se o arquivo não estiver commitado ou se esses sha256 não
baterem.

Uso: `gate_fase2.py` (sem argumentos; nenhuma chamada a modelo, nenhuma rede).
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  (localhost passa; nenhuma API paga)
import avaliar_c1_c4 as A  # noqa: E402
import comum as K  # noqa: E402
import gerar_sintese_teste as G  # noqa: E402

ARQ_C1C4 = A.DIR / "c1_c4_fase2.json"
LADOS_FASE2 = ("publicado", "base")
ANTIGO_PUBLICADO_5 = (2, 90)               # MEDIDO na referência (poder.md, juiz v2.2)
METRICAS_IC = ("sem_apoio", "apoio_2", "m1", "c4")
NOMES = {"sem_apoio": "C1 · % sem apoio (bullets)", "apoio_2": "C2 · % apoio ≥ 2 (bullets)",
         "m1": "C3 · M1, % exemplos com palavra de quantidade", "c4": "C4 · % buckets válidos"}


# ---------------------------------------------------------------------------
# contas (funções puras)
# ---------------------------------------------------------------------------

def taxa(pf: dict, filmes: list[str], metrica: str) -> float | None:
    if metrica != "c4":
        return A.taxa(pf, filmes, metrica)
    d = sum(pf.get(s, {}).get("buckets", 0) for s in filmes)
    return sum(pf.get(s, {}).get("c4_ok", 0) for s in filmes) / d if d else None


def contagem(pf: dict, filmes: list[str], metrica: str) -> tuple[int, int]:
    num, den = ("c4_ok", "buckets") if metrica == "c4" else A.METRICAS[metrica]
    return (sum(pf.get(s, {}).get(num, 0) for s in filmes),
            sum(pf.get(s, {}).get(den, 0) for s in filmes))


def ic_do_lado(pf: dict, filmes: list[str], boot: list[list[str]], metrica: str) -> dict:
    """Taxa de UM lado (%) com IC 95% percentil do bootstrap por filme."""
    vs = sorted(100 * t for t in (taxa(pf, a, metrica) for a in boot) if t is not None)
    q = lambda p: vs[min(len(vs) - 1, int(p * len(vs)))]
    k, n = contagem(pf, filmes, metrica)
    return {"k": k, "n": n, "pct": 100 * taxa(pf, filmes, metrica),
            "ic95_pct": [q(0.025), q(0.975)], "reamostras_validas": len(vs)}


def referencia_5(pf: dict, estados: dict) -> dict:
    """Publicado nos 5 de referência, medido agora (parada no 2º sim)."""
    k, n = contagem(pf, list(A.REFERENCIA_5), "sem_apoio")
    ind = sum(e["estado"] == "indeterminado" for e in estados.values()
              if e["slug"] in A.REFERENCIA_5)
    return {"sem_apoio": k, "julgados": n, "indeterminados": ind,
            "antigo": {"sem_apoio": ANTIGO_PUBLICADO_5[0], "julgados": ANTIGO_PUBLICADO_5[1]}}


def tempos_sintese(regs: dict) -> dict:
    ps = [r["parede_s"] for r in regs.values() if r.get("parede_s") is not None]
    ch = collections.Counter(r.get("n_chamadas") for r in regs.values())
    return {"buckets": len(ps), "total_h": sum(ps) / 3600, "mediana_s": statistics.median(ps),
            "min_s": min(ps), "max_s": max(ps), "chamadas": dict(sorted(ch.items()))}


def tempos_juiz(saida: list[dict]) -> dict:
    lat = [r["latencia_s"] for r in saida if r.get("latencia_s") is not None]
    ts = sorted(r["ts"] for r in saida if r.get("ts"))
    return {"chamadas": len(saida), "ok": sum(bool(r.get("ok")) for r in saida),
            "reaproveitadas": sum("reaproveitado_de" in r for r in saida),
            "soma_latencia_h": sum(lat) / 3600,
            "mediana_s": statistics.median(lat) if lat else None,
            "primeira": ts[0] if ts else None, "ultima": ts[-1] if ts else None}


# ---------------------------------------------------------------------------
# coleta (lê os arquivos da Fase 2)
# ---------------------------------------------------------------------------

def exigir_ordem(c1c4: dict, delta2: dict) -> None:
    if (G.PASTA / "sintese_treinado" / "manifesto.json").exists():
        raise SystemExit("o treinado já tem síntese de teste: o gate tinha de vir ANTES")
    faltam = [l for l in LADOS_FASE2 if l not in c1c4.get("lados", {})]
    if faltam:
        raise SystemExit(f"c1_c4_fase2.json sem o(s) lado(s) {faltam}: julgue e rode `calcular`")
    if not c1c4.get("delta2_fixado") or c1c4.get("delta2_pp") != delta2.get("delta2_pp"):
        raise SystemExit("c1_c4_fase2.json foi calculado sem o δ₂ fixado: rode `fixar-delta2` "
                         "e depois `calcular` de novo")
    if c1c4.get("decisao") is not None:
        raise SystemExit("c1_c4_fase2.json tem decisão (lado treinado): não é a Fase 2")


def coletar(split_arq: Path) -> dict:
    for f in (A.ARQ_DELTA2, ARQ_C1C4):
        if not f.exists():
            raise SystemExit(f"sem {f.name}: rode `fixar-delta2` e depois `calcular`")
    c1c4, delta2 = K.ler_json(ARQ_C1C4), K.ler_json(A.ARQ_DELTA2)
    exigir_ordem(c1c4, delta2)
    split = K.ler_json(split_arq)
    pares_teste = A._pares_de_teste(split)
    regs = A.registros_gerados(pares_teste)
    mantidos, fora = A.buckets_mantidos(pares_teste, regs)
    filmes = sorted({s for s, _ in mantidos})
    boot = A.reamostras(filmes)
    lados = {}
    with K.entradas_do_commit(sorted({s for s, _ in pares_teste})) as ent:
        for lado in LADOS_FASE2:
            pf, est, _ = A._lado_completo(lado, split, mantidos, regs, ent)
            ics = {m: ic_do_lado(pf, filmes, boot, m) for m in METRICAS_IC}
            for m in A.METRICAS:                     # as mesmas contas do `calcular`
                if abs(ics[m]["pct"] / 100 - c1c4["lados"][lado][m]) > 1e-12:
                    raise SystemExit(f"{lado}/{m}: a taxa refeita difere do c1_c4_fase2.json")
            meta = K.ler_json(A.dir_lado(lado) / "entrada_meta.json")
            lados[lado] = {"ic": ics, "estados": c1c4["lados"][lado]["estados"],
                           "resumo": c1c4["lados"][lado],
                           "juiz": tempos_juiz(A.C._ler_jsonl(A.dir_lado(lado) / "saida.jsonl")),
                           "preparar_s": meta.get("tempo_s"),
                           "reaproveitamento": meta.get("reaproveitamento")}
            if lado == "publicado":
                lados[lado]["referencia_5"] = referencia_5(pf, est)
        entradas = {k: ent[k] for k in ("commit", "n_arquivos", "sha256")}
    rb = regs.get("base", {})
    outlier = ("500-days-of-summer", "positivas")
    return {
        "c1c4": c1c4, "delta2": delta2, "lados": lados, "filmes": len(filmes),
        "buckets_mantidos": len(mantidos), "entradas": entradas,
        "excluidos_split": split["buckets_excluidos"],
        "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
        "abortos_recuperados": sorted(f"{s}/{b}" for (s, b), r in rb.items()
                                      if r.get("abortos_memoria") and not r.get("fora_por_memoria")),
        "outlier": {"par": "/".join(outlier), **{k: (rb.get(outlier) or {}).get(k) for k in (
            "num_ctx", "ok", "abortos_memoria", "fora_por_memoria", "parede_s")}},
        "sintese_base": tempos_sintese(rb),
        "origem_base": next(iter(rb.values()), {}).get("origem"),
        "shas": {"c1_c4_fase2_sha256": K.sha256_arquivo(ARQ_C1C4),
                 "delta2_sha256": K.sha256_arquivo(A.ARQ_DELTA2),
                 "manifesto_sintese_base_sha256": K.sha256_arquivo(
                     G.PASTA / "sintese_base" / "manifesto.json"),
                 **{f"saida_juiz_{l}_sha256": K.sha256_arquivo(A.dir_lado(l) / "saida.jsonl")
                    for l in LADOS_FASE2},
                 "script_sha256": K.sha256_arquivo(Path(__file__))},
    }


# ---------------------------------------------------------------------------
# relatório (função pura)
# ---------------------------------------------------------------------------

def _pp(x: float) -> str:
    return f"{x:+.1f}".replace(".", ",")


def _pct(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def renderizar(d: dict) -> str:
    c, dl = d["c1c4"], d["delta2"]
    bp = c["descritivo"]["base_contra_publicado"]
    L = d["lados"]
    o = ["# GATE DA FASE 2 — publicado e base no teste", "",
         "Gerado por `scripts/finetune/gate_fase2.py` a partir de `finetune/fase2/` "
         "(`c1_c4_fase2.json`, `delta2.json`, juiz e síntese da base). Pré-registro: "
         "`PREREGISTRO_AVALIACAO.md`. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.", "",
         f"Conjunto (MEDIDO): {d['filmes']} filmes, {d['buckets_mantidos']} buckets mantidos. "
         f"Entradas do commit `{d['entradas']['commit'][:7]}` ({d['entradas']['n_arquivos']} "
         f"arquivos, sha256 `{d['entradas']['sha256'][:8]}…`). Bootstrap por filme: "
         f"{str(c['reamostras'])[:-3]}.{str(c['reamostras'])[-3:]} reamostras, semente "
         f"{c['semente_bootstrap']}. Juiz `{c['juiz'][:8]}…`, parada no 2º sim.", "",
         "**Fase 2 é descritiva.** Nada aqui decide o treinado; o que se fixa é o δ₂. "
         "O treinado só é gerado depois deste arquivo commitado (`gerar_sintese_teste.py` recusa).",
         "", "## 1. C1–C4 do publicado e da base (MEDIDO)", "",
         "Taxa de cada lado com IC 95% do bootstrap por filme.", "",
         "| métrica | publicado | base |", "|---|---|---|"]
    for m in METRICAS_IC:
        cel = []
        for l in LADOS_FASE2:
            x = L[l]["ic"][m]
            cel.append(f"{x['k']}/{x['n']} = {_pct(x['pct'])}% [{_pct(x['ic95_pct'][0])}; "
                       f"{_pct(x['ic95_pct'][1])}]")
        o.append(f"| {NOMES[m]} | {cel[0]} | {cel[1]} |")
    o += ["", "Indeterminados (sem par julgável; fora do denominador de C1/C2): " + "; ".join(
        f"{l} {L[l]['estados'].get('indeterminado', 0)}" for l in LADOS_FASE2) + ".",
          f"C4 da base na 1ª tentativa, sem retentativa (descrição): "
          f"{L['base']['resumo'].get('c4_ok_1a_tentativa')}/{d['buckets_mantidos']}.", "",
          "### Base − publicado (descritivo, com os limiares do treinado)", "",
          "| critério | base − publicado | IC 95% | limiar | satisfaz |", "|---|---|---|---|---|"]
    lim = {"C1": f"sup. < +{_pct(A.C1_MARGEM_PP)} e pontual ≤ +{_pct(A.C1_PONTUAL_PP)} pp",
           "C2": f"inf. > −{_pct(dl['delta2_pp'])} pp (δ₂ fixado)",
           "C3": f"sup. < +{_pct(A.C3_MARGEM_PP)} pp"}
    for k in ("C1", "C2", "C3"):
        x = bp[k]
        o.append(f"| {k} | {_pp(x['ponto_pp'])} pp | [{_pp(x['ic95_pp'][0])}; "
                 f"{_pp(x['ic95_pp'][1])}] | {lim[k]} | {'sim' if x['passa'] else 'não'} |")
    x = bp["C4"]
    o += [f"| C4 | {x['ok']}/{x['buckets']} buckets | — | ≥ {x['piso']} | "
          f"{'sim' if x['passa'] else 'não'} |", "",
          ("**Achado (pré-registro, seção 4): a BASE satisfaz C1 a C4.** Usá-la em produção "
           "exigiria uma leitura cega própria, não prevista." if c.get("achado_base_satisfaz_c1_c4")
           else "A base NÃO satisfaz C1 a C4 juntos (descritivo)."), "",
          "## 2. δ₂ fixado (MEDIDO p₀; fórmula pré-registrada)", "",
          f"- p₀ = taxa de apoio ≥ 2 do publicado = {_pct(100 * dl['p0_apoio_2'])}% "
          f"({dl['bullets_julgados']} bullets julgados, buckets mantidos);",
          f"- **δ₂ = {_pct(dl['delta2_pp'])} pp** (substitui os 8 pp); {dl['formula']};",
          f"- `delta2.json` sha256 `{d['shas']['delta2_sha256']}`.", "",
          "## 3. Buckets fora e por quê (MEDIDO)", ""]
    for b in d["excluidos_split"]:
        o.append(f"- `{b['slug']}/{b['bucket']}`: {b['motivo']} ({b['regra']}).")
    ol = d["outlier"]
    o.append(f"- Fora por memória (saem dos dois lados, inclusive do publicado): "
             f"{', '.join(f'`{x}`' for x in d['fora_por_memoria']) or 'nenhum'}.")
    o.append(f"- Derrubados uma vez pela guarda de RAM e refeitos com sucesso: "
             f"{', '.join(f'`{x}`' for x in d['abortos_recuperados']) or 'nenhum'}.")
    o += [f"- Outlier `{ol['par']}` (num_ctx {ol['num_ctx']}): ok {ol['ok']}, abortos por memória "
          f"{ol['abortos_memoria'] or 0}, fora por memória {bool(ol['fora_por_memoria'])}, "
          f"{ol['parede_s']} s.", "", "## 4. Tempos (MEDIDO)", ""]
    sb = d["sintese_base"]
    o.append(f"- Síntese da base: {sb['buckets']} buckets, {_pct(sb['total_h'])} h somadas "
             f"(mediana {sb['mediana_s']:.0f} s, de {sb['min_s']:.0f} a {sb['max_s']:.0f} s); "
             f"chamadas por bucket {sb['chamadas']}.")
    for l in LADOS_FASE2:
        j = L[l]["juiz"]
        med = f"{_pct(j['mediana_s'])} s" if j["mediana_s"] is not None else "—"
        o.append(f"- Juiz, {l}: {j['chamadas']} chamadas ({j['ok']} ok, {j['reaproveitadas']} "
                 f"reaproveitadas), {_pct(j['soma_latencia_h'])} h de latência somada "
                 f"(mediana {med}); de {j['primeira']} a {j['ultima']} (UTC). "
                 f"`preparar` (Mac): {L[l]['preparar_s']:.0f} s.")
    r5 = L["publicado"]["referencia_5"]
    re = L["publicado"]["reaproveitamento"] or {}
    o += ["", "## 5. Comparação com a medição antiga dos 5 de referência (descritiva)", "",
          f"- Antes (MEDIDO, `poder.md`, gate-local): publicado {r5['antigo']['sem_apoio']}/"
          f"{r5['antigo']['julgados']} sem apoio.",
          f"- Agora (MEDIDO): publicado nos mesmos 5 filmes, {r5['sem_apoio']}/{r5['julgados']} "
          f"sem apoio ({r5['indeterminados']} indeterminados).",
          f"- **As entradas diferem:** o sha256 das {re.get('linhas')} linhas do publicado dos 5 "
          f"foi `{(re.get('sha256') or '')[:8]}…`, o esperado era `{A.REUSO_SHA[:8]}…` "
          f"(bate: {re.get('bate')}). Por isso nada foi reaproveitado e o publicado foi julgado "
          "inteiro. A medição antiga julgou todos os pares; esta para no 2º sim (o \"sem apoio\" "
          "não muda pela parada, mas o conjunto de pares e de bullets pode mudar). Não é réplica: "
          "é só uma conferência de ordem de grandeza.", "",
          "## 6. O que NÃO foi medido", "",
          "- O TREINADO: nem gerado nem julgado no teste (Fase 4, depois deste commit).",
          "- C5 e C6 (rotulagem e leitura cega do dono): Fase 4.",
          "- M2 (`mencoes_aproximadas`): o τ ainda depende de um DESVIO.",
          "- Os parâmetros de amostragem efetivos do Ollama além dos passados em cada chamada "
          "(DESVIO_P01): não lidos do servidor.",
          "- C4 do publicado na 1ª tentativa: o publicado não tem tentativas gravadas.",
          "- Os bullets indeterminados (sem par julgável na janela do juiz): fora de C1/C2.",
          "- Variação entre execuções da base (uma geração, seed fixa): não estimada.", "",
          f"{G.MARCA_GATE}{json.dumps(d['shas'], ensure_ascii=False, sort_keys=True)} -->", ""]
    return "\n".join(o)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    a = ap.parse_args()
    if G.ARQ_GATE.exists():
        real = G.ARQ_GATE.resolve()
        if K.rodar_texto(["git", "-C", str(real.parent), "ls-files", "--error-unmatch",
                          real.name]).returncode == 0:
            raise SystemExit(f"{G.ARQ_GATE.name} já está commitado: o gate é escrito UMA vez")
    texto = renderizar(coletar(a.split))
    G.ARQ_GATE.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"gravado: {G.ARQ_GATE} (sha256 {K.sha256_arquivo(G.ARQ_GATE)})")


if __name__ == "__main__":
    main()
