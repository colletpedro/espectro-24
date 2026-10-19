"""Comparação CEGA da prosa: texto publicado × texto do modelo local.

Para cada filme, o documento que o dono LÊ mostra os bullets da síntese, a
narrativa, o veredito e as condições de dois lados, `A` e `B`, SEM dizer qual
é o publicado e qual é o local. A atribuição é sorteada por filme (semente
registrada) e o MAPEAMENTO fica num arquivo FORA do documento de leitura, com
o sha256 impresso no rodapé do documento — quem abrir o mapeamento depois
confere que ele é o mesmo que existia antes da leitura.

Os números dos validadores mecânicos e a barra dos bullets (que identificam o
lado) vão num SEGUNDO documento, com os lados nomeados, para abrir DEPOIS de
ler.

**A barra dos bullets.** A barra de cada célula de eixo é a frequência da
CLASSIFICAÇÃO (`mencoes` de `eixos.linhas`); o bullet ao lado é o tema da
SÍNTESE, com a sua própria contagem (`mencoes_aproximadas`). Para cada célula
com bullet, razão = contagem da síntese / contagem da classificação e
diferença em pontos percentuais de `n`. A FAIXA DO DEEPSEEK é medida aqui, nos
filmes publicados (p5–p95 das duas medidas); o lado local é conferido contra
ela. Como a classificação é a MESMA nos dois lados (vem do consenso), a
diferença está só na contagem que o modelo declara na síntese.

Uso:
    python scripts/comparacao_cega_prosa.py --local-dir prosa-local \\
        --leitura <dir da leitura> --mapa <dir FORA da leitura> \\
        --slug ... (ou --filmes-padrao)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

RESULTADO_DIR = RAIZ / "resultado"
SEMENTE = 20261012
LADOS = ("publicado", "local")
FALHA_JSON_SINTESE = "Falha ao obter JSON válido do LLM."


# ---------------------------------------------------------------------------
# Barra dos bullets: síntese × classificação
# ---------------------------------------------------------------------------

def celulas_barra(doc: dict) -> list[dict]:
    """Uma entrada por (bucket, eixo) que tem bullet E contagem de síntese:
    `{bucket, eixo, tema, sintese, classificacao, n, razao, dif_pp}`."""
    saida = []
    temas = {b["bucket"]: {t["tema"]: t for t in b.get("temas") or []}
             for b in doc.get("buckets", [])}
    for linha in (doc.get("eixos") or {}).get("linhas", []):
        for bucket, c in linha["por_bucket"].items():
            tema = c.get("tema")
            t = temas.get(bucket, {}).get(tema) if tema else None
            if not t or not c.get("de_n") or not c.get("mencoes"):
                continue
            s, k, n = t["mencoes_aproximadas"], c["mencoes"], c["de_n"]
            saida.append({"bucket": bucket, "eixo": linha["eixo"], "tema": tema,
                          "sintese": s, "classificacao": k, "n": n,
                          "razao": s / k, "dif_pp": 100 * (s - k) / n})
    return saida


def _q(xs: list[float], p: float) -> float:
    v = sorted(xs)
    i = p * (len(v) - 1)
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def faixa_deepseek(docs: list[dict]) -> dict:
    """p5/p50/p95 da razão e da diferença em pp, sobre as células dos
    publicados (DeepSeek) — a régua do lado local."""
    cel = [c for d in docs for c in celulas_barra(d)]
    if not cel:
        return {}
    r, d = [c["razao"] for c in cel], [c["dif_pp"] for c in cel]
    return {"n_celulas": len(cel), "n_filmes": len(docs),
            "razao": {"p5": round(_q(r, .05), 3), "p50": round(_q(r, .5), 3),
                      "p95": round(_q(r, .95), 3)},
            "dif_pp": {"p5": round(_q(d, .05), 2), "p50": round(_q(d, .5), 2),
                       "p95": round(_q(d, .95), 2)}}


def barra_do_filme(doc: dict, faixa: dict) -> dict:
    cel = celulas_barra(doc)
    if not cel:
        return {"n_celulas": 0}
    dentro = [c for c in cel
              if faixa["razao"]["p5"] <= c["razao"] <= faixa["razao"]["p95"]
              and faixa["dif_pp"]["p5"] <= c["dif_pp"] <= faixa["dif_pp"]["p95"]]
    return {"n_celulas": len(cel), "dentro_da_faixa": len(dentro),
            "razao_mediana": round(statistics.median(c["razao"] for c in cel), 3),
            "dif_pp_mediana": round(statistics.median(c["dif_pp"] for c in cel), 2),
            "maior_dif_pp": round(max(c["dif_pp"] for c in cel), 1),
            "menor_dif_pp": round(min(c["dif_pp"] for c in cel), 1)}


# ---------------------------------------------------------------------------
# Validadores mecânicos
# ---------------------------------------------------------------------------

def validadores(doc: dict) -> dict:
    """Os sinais mecânicos que os estágios já gravam no documento — os mesmos
    nos dois lados. Chave ausente conta como 0/None, nunca como erro."""
    bks = doc.get("buckets", [])
    temas = [t for b in bks for t in (b.get("temas") or [])]
    rot = (doc.get("eixos") or {}).get("rotulagem") or {}
    nar = doc.get("verificacao_narrativa") or {}
    sel = doc.get("narrativa_selecao") or {}
    ver = doc.get("veredito") or {}
    con = doc.get("condicoes") or {}
    n_cond = len(con.get("vale_a_pena") or []) + len(con.get("talvez_evite") or [])
    return {
        "sintese": {
            "buckets": len(bks),
            "buckets_com_falha_json": sum(b.get("observacao_geral") == FALHA_JSON_SINTESE
                                          for b in bks),
            "buckets_idioma_invalido": sum(bool(b.get("idioma_invalido")) for b in bks),
            "buckets_escopo_suspeito": sum(bool(b.get("escopo_suspeito")) for b in bks),
            "temas": len(temas),
            "temas_aspas_removidas": sum(bool(t.get("aspas_removidas")) for t in temas),
            "temas_mencoes_clampadas": sum(bool(t.get("mencoes_clampadas")) for t in temas)},
        "rotulagem": {
            "chamadas": rot.get("n_chamadas"),
            "buckets_que_falharam": len(rot.get("falharam") or []),
            "eixos_fora_da_taxonomia": sum(len(v) if hasattr(v, "__len__") else 1
                                           for v in (rot.get("fora_da_taxonomia") or {}).values()),
            "retentativas": len(rot.get("houve_retentativa") or [])},
        "narrativa": {
            "palavras": len((doc.get("narrativa") or "").split()),
            "n_flags": nar.get("n_flags"),
            "n_resenha_speak": nar.get("n_resenha_speak"),
            "retry_aplicado": bool((sel.get("retry") or {}).get("aplicado"))
            if isinstance(sel.get("retry"), dict) else None},
        "veredito": {
            "origem": ver.get("origem"), "flags": ver.get("flags") or [],
            "n_flags": len(ver.get("flags") or []),
            "retry": bool(ver.get("retry"))},
        "condicoes": {
            "origem": con.get("origem"), "publicadas": n_cond,
            "descartadas": len(con.get("descartadas") or []),
            "sem_condicao_publicavel": len(con.get("sem_condicao_publicavel") or []),
            "recusas_invalidas": len(con.get("recusas_invalidas") or []),
            "retry": bool(con.get("retry"))},
    }


def taxas(por_filme: list[dict]) -> dict:
    """Agrega os validadores de um lado em taxas sobre os filmes."""
    n = len(por_filme)
    if not n:
        return {}
    soma = lambda f: sum(f(v) for v in por_filme)  # noqa: E731
    return {
        "filmes": n,
        "sintese_buckets_com_falha_json": f"{soma(lambda v: v['sintese']['buckets_com_falha_json'])}/{soma(lambda v: v['sintese']['buckets'])}",
        "sintese_buckets_idioma_ou_escopo": f"{soma(lambda v: v['sintese']['buckets_idioma_invalido'] + v['sintese']['buckets_escopo_suspeito'])}/{soma(lambda v: v['sintese']['buckets'])}",
        "sintese_temas_aspas_removidas": f"{soma(lambda v: v['sintese']['temas_aspas_removidas'])}/{soma(lambda v: v['sintese']['temas'])}",
        "sintese_temas_mencoes_clampadas": f"{soma(lambda v: v['sintese']['temas_mencoes_clampadas'])}/{soma(lambda v: v['sintese']['temas'])}",
        "rotulagem_buckets_que_falharam": f"{soma(lambda v: v['rotulagem']['buckets_que_falharam'])}/{soma(lambda v: v['sintese']['buckets'])}",
        "rotulagem_eixos_fora_da_taxonomia": soma(lambda v: v['rotulagem']['eixos_fora_da_taxonomia']),
        "narrativa_flags_medias": round(soma(lambda v: v['narrativa']['n_flags'] or 0) / n, 2),
        "narrativa_resenha_speak_media": round(soma(lambda v: v['narrativa']['n_resenha_speak'] or 0) / n, 2),
        "narrativa_palavras_media": round(soma(lambda v: v['narrativa']['palavras']) / n),
        "veredito_em_template_fallback": f"{soma(lambda v: v['veredito']['origem'] == 'template_fallback')}/{n}",
        "veredito_flags_medias": round(soma(lambda v: v['veredito']['n_flags']) / n, 2),
        "condicoes_em_abstencao": f"{soma(lambda v: v['condicoes']['origem'] == 'abstencao')}/{n}",
        "condicoes_publicadas_media": round(soma(lambda v: v['condicoes']['publicadas']) / n, 1),
        "condicoes_descartadas_media": round(soma(lambda v: v['condicoes']['descartadas']) / n, 1),
        "condicoes_recusas_media": round(soma(lambda v: v['condicoes']['sem_condicao_publicavel']) / n, 1),
    }


# ---------------------------------------------------------------------------
# Documento de leitura (cego)
# ---------------------------------------------------------------------------

def _bullets(doc: dict) -> list[str]:
    L = []
    for b in doc.get("buckets", []):
        L.append(f"**{b['bucket'].capitalize()}**")
        temas = b.get("temas") or []
        if not temas:
            L.append("- _(sem bullets)_")
        for t in temas:
            L.append(f"- **{t['tema']}** — {t.get('exemplo_parafraseado', '')}")
        if b.get("observacao_geral"):
            L.append(f"\n_{b['observacao_geral']}_")
        L.append("")
    return L


def _condicoes(doc: dict) -> list[str]:
    c = doc.get("condicoes") or {}
    L = []
    for lado, rotulo in (("vale_a_pena", "Vale a pena se…"),
                         ("talvez_evite", "Talvez evite se…")):
        L.append(f"**{rotulo}**")
        for x in c.get(lado) or []:
            L.append(f"- {x['texto']}")
        if not c.get(lado):
            L.append("- _(nenhuma)_")
        L.append("")
    return L


def _veredito(doc: dict) -> str:
    v = doc.get("veredito") or {}
    return v.get("texto") or "_(sem veredito)_"


def _titulo(doc: dict) -> str:
    f = doc.get("ficha") or {}
    return f.get("titulo") or doc["slug"]


def sortear(slugs: list[str], semente: int = SEMENTE) -> dict[str, str]:
    """`{slug: lado que vai para A}` — um sorteio por filme, ordem estável."""
    rng = random.Random(semente)
    return {s: rng.choice(LADOS) for s in sorted(slugs)}


def montar_leitura(slugs: list[str], docs: dict[str, dict[str, dict]],
                   a_e: dict[str, str]) -> str:
    """O texto cego. `docs[slug][lado]`. Nada aqui nomeia o lado, o modelo ou o
    provider."""
    L = ["# Leitura cega — prosa do Espectro 24", "",
         "Para cada filme, dois textos, **A** e **B**, de duas origens que "
         "não são reveladas. Leia os quatro blocos de cada filme e marque, "
         "por bloco, qual lê melhor (ou *empate*) e se algum dos dois "
         "**publicaria sem mudança**. Os números e a identificação ficam "
         "para depois.", ""]
    for i, slug in enumerate(sorted(slugs), 1):
        lado_a = a_e[slug]
        lado_b = [x for x in LADOS if x != lado_a][0]
        A, B = docs[slug][lado_a], docs[slug][lado_b]
        L += [f"---", "", f"## Filme {i} — {_titulo(A)}", ""]
        L += ["### 1. Bullets da síntese", "", "#### A", ""] + _bullets(A) + \
             ["#### B", ""] + _bullets(B)
        L += ["### 2. Narrativa", "", "#### A", "", A.get("narrativa") or "_(vazia)_",
              "", "#### B", "", B.get("narrativa") or "_(vazia)_", ""]
        L += ["### 3. Veredito", "", "#### A", "", _veredito(A), "",
              "#### B", "", _veredito(B), ""]
        L += ["### 4. Condições", "", "#### A", ""] + _condicoes(A) + \
             ["#### B", ""] + _condicoes(B)
        L += ["**Sua leitura deste filme:**", "",
              "| bloco | melhor (A / B / empate) | publicaria sem mudança (A / B / ambos / nenhum) |",
              "|---|---|---|", "| bullets | | |", "| narrativa | | |",
              "| veredito | | |", "| condições | | |", ""]
    return "\n".join(L)


def montar_metricas(slugs: list[str], docs: dict[str, dict[str, dict]],
                    a_e: dict[str, str], faixa: dict, tele: dict[str, dict]) -> str:
    """O segundo documento: lados NOMEADOS. Abrir depois da leitura."""
    L = ["# Métricas mecânicas e barra dos bullets — ABRIR DEPOIS DA LEITURA", "",
         "Este documento nomeia os lados (`publicado` × `local`).", ""]
    por_lado = {lado: [] for lado in LADOS}
    for s in sorted(slugs):
        for lado in LADOS:
            por_lado[lado].append(validadores(docs[s][lado]))
    ta = {lado: taxas(por_lado[lado]) for lado in LADOS}
    L += ["## Taxas dos validadores mecânicos (sobre os filmes comparados)", "",
          "| validador | publicado | local |", "|---|---|---|"]
    for k in ta["publicado"]:
        L.append(f"| {k} | {ta['publicado'][k]} | {ta['local'][k]} |")
    L += ["", "## Barra dos bullets: contagem da síntese × contagem da classificação", "",
          f"Faixa medida no DeepSeek (publicados): {faixa['n_celulas']} células em "
          f"{faixa['n_filmes']} filmes. Razão síntese/classificação p5–p95: "
          f"{faixa['razao']['p5']}–{faixa['razao']['p95']} (mediana "
          f"{faixa['razao']['p50']}); diferença em pp de n, p5–p95: "
          f"{faixa['dif_pp']['p5']} a {faixa['dif_pp']['p95']} (mediana "
          f"{faixa['dif_pp']['p50']}). \"Dentro\" = razão E diferença dentro da faixa.", "",
          "| filme | lado | células | dentro da faixa | razão mediana | dif. mediana (pp) | menor / maior dif. (pp) |",
          "|---|---|---|---|---|---|---|"]
    tot = {lado: [0, 0] for lado in LADOS}
    for s in sorted(slugs):
        for lado in LADOS:
            b = barra_do_filme(docs[s][lado], faixa)
            if not b["n_celulas"]:
                L.append(f"| {s} | {lado} | 0 | — | — | — | — |")
                continue
            tot[lado][0] += b["dentro_da_faixa"]
            tot[lado][1] += b["n_celulas"]
            L.append(f"| {s} | {lado} | {b['n_celulas']} | {b['dentro_da_faixa']} | "
                     f"{b['razao_mediana']} | {b['dif_pp_mediana']:+} | "
                     f"{b['menor_dif_pp']:+} / {b['maior_dif_pp']:+} |")
    L += ["", "| lado | células dentro da faixa do DeepSeek |", "|---|---|"]
    for lado in LADOS:
        d, n = tot[lado]
        L.append(f"| {lado} | {d}/{n} ({100 * d / n:.0f}%) |" if n else f"| {lado} | — |")
    L += ["", "## Mapeamento (qual lado foi A em cada filme)", "",
          "| filme | A | B |", "|---|---|---|"]
    for s in sorted(slugs):
        a = a_e[s]
        L.append(f"| {s} | {a} | {[x for x in LADOS if x != a][0]} |")
    if tele:
        L += ["", "## Tempo e raciocínio do lado local", "",
              "| filme | chamadas | tempo (s) | think | falhas |", "|---|---|---|---|---|"]
        for s in sorted(tele):
            t = tele[s]
            n = sum(r["n_chamadas"] for r in t["estagios"].values())
            L.append(f"| {s} | {n} | {t['elapsed_s']} | {t['think']} | "
                     f"{t['falhas'] or 'nenhuma'} |")
    return "\n".join(L) + "\n"


def hash_do_mapa(mapa: dict) -> str:
    return hashlib.sha256(json.dumps(mapa, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> None:
    from gerar_prosa_local import FILMES_COMPARACAO

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--local-dir", required=True, type=Path)
    ap.add_argument("--leitura", required=True, type=Path,
                    help="onde o documento cego é escrito")
    ap.add_argument("--mapa", required=True, type=Path,
                    help="onde o mapeamento e as métricas ficam (FORA de --leitura)")
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--filmes-padrao", action="store_true")
    a = ap.parse_args()

    slugs = a.slug + (list(FILMES_COMPARACAO) if a.filmes_padrao else [])
    if not slugs:
        raise SystemExit("use --slug ou --filmes-padrao")
    if a.mapa.resolve() == a.leitura.resolve() or a.leitura.resolve() in a.mapa.resolve().parents:
        raise SystemExit("--mapa não pode ficar dentro de --leitura")

    docs, tele = {}, {}
    for s in slugs:
        docs[s] = {"publicado": json.loads((RESULTADO_DIR / f"{s}.json").read_text(encoding="utf-8")),
                   "local": json.loads((a.local_dir / f"{s}.json").read_text(encoding="utf-8"))}
        t = a.local_dir / f"{s}.telemetria.json"
        if t.exists():
            tele[s] = json.loads(t.read_text(encoding="utf-8"))
    from espectro24.excecao_c22 import SLUGS as C22
    todos = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RESULTADO_DIR.glob("*.json"))]
    todos = [d for d in todos if d["slug"] not in C22 and d.get("eixos")]
    faixa = faixa_deepseek(todos)

    a_e = sortear(slugs)
    mapa = {"semente": SEMENTE, "a_e": a_e, "filmes": sorted(slugs)}
    h = hash_do_mapa(mapa)
    a.leitura.mkdir(parents=True, exist_ok=True)
    a.mapa.mkdir(parents=True, exist_ok=True)
    (a.mapa / "mapeamento.json").write_text(
        json.dumps({**mapa, "sha256": h}, ensure_ascii=False, indent=2), encoding="utf-8")
    (a.mapa / "metricas_e_identificacao.md").write_text(
        montar_metricas(slugs, docs, a_e, faixa, tele), encoding="utf-8")
    texto = montar_leitura(slugs, docs, a_e) + \
        f"\n---\n\n_Selo do mapeamento (sha256): `{h}`_\n"
    (a.leitura / "leitura_cega.md").write_text(texto, encoding="utf-8")
    print(f"leitura: {a.leitura / 'leitura_cega.md'}\nmapa e métricas: {a.mapa}\nsha256 {h}")


if __name__ == "__main__":
    main()
