"""Fase 4, critério C6 — leitura cega TREINADO × PUBLICADO nos 5 filmes de referência.

Pelo `finetune/PREREGISTRO_AVALIACAO.md` (seção 3, C6), sem mudar nada do que
lá está:

- só a síntese (os 3 buckets), no formato do bloco "1. Bullets da síntese" de
  `prosa-local-qwen3-leitura/leitura_cega.md` (`gate-local`, `cef0b16`): por
  bucket, os bullets (**tema** — exemplo, sem contagens) e a
  `observacao_geral` em itálico; o texto é o que seria publicado, SEM
  normalização (a publicabilidade se julga no texto real);
- lados sorteados por filme, semente 20261103 (`random.Random`, um sorteio por
  filme na ordem de `fixos_no_teste` ordenado: A = treinado se `random() < 0,5`);
- bucket `fora_por_memoria` em qualquer lado gerado sai dos dois lados, com uma
  nota no lugar;
- mapa com selo em `finetune/fase4/leitura_mapa.json`; documento e respostas em
  `docs/arquivo-de-estudos/finetune-fase4/` (fora do git);
- por filme: "publicaria sem mudança" (A / B / ambos / nenhum) e "melhor"
  (A / B / empate); critério: o TREINADO publicável em ≥ 4 de 5 filmes.

Subcomandos:
    montar    (depois do C5 rotulado) documento, respostas em branco, mapa
    avaliar   (depois das respostas) veredito do C6
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import especificidade_validacao as V  # noqa: E402
import fase4_especificidade as F  # noqa: E402

ARQ_MAPA = F.PASTA / "leitura_mapa.json"
ARQ_RESULTADO = F.PASTA / "leitura_resultado.json"
DOC = "leitura_cega.md"
RESPOSTAS = "leitura_respostas.csv"
SEMENTE = 20261103
N_PUBLICAVEL_MIN = 4
ROTULO_BUCKET = {"negativas": "Negativas", "medianas": "Medianas", "positivas": "Positivas"}
PUBLICARIA = ("A", "B", "ambos", "nenhum")
MELHOR = ("A", "B", "empate")
SEM_JSON = "Falha ao obter JSON válido do LLM."


def sortear_lados(filmes: list[str], rng: random.Random) -> dict[str, str]:
    """filme → o lado que aparece como A."""
    return {f: ("treinado" if rng.random() < 0.5 else "publicado") for f in sorted(filmes)}


def bloco(bucket: dict | None) -> list[str]:
    """Um bucket: bullets e observação; `None` = fora por memória."""
    if bucket is None:
        return ["_(bucket fora da comparação: não coube na memória do notebook)_", ""]
    temas = bucket.get("temas") or []
    if not temas:
        return ["_(sem síntese: o modelo não devolveu JSON válido)_", ""]
    L = [f"- **{t['tema'].strip()}**{F.B.SEP}{t['exemplo_parafraseado'].strip()}" for t in temas]
    obs = (bucket.get("observacao_geral") or "").strip()
    return L + ["", f"_{obs}_", ""] if obs else L + [""]


def documento(filmes: list[dict], a_e: dict[str, str], selo: str, respostas: Path) -> str:
    """`filmes`: [{slug, titulo, treinado: {bucket: dict|None}, publicado: {...}}]."""
    L = ["# Leitura cega — síntese do Espectro 24", "",
         "Para cada filme, duas sínteses, **A** e **B**, de duas origens que não são "
         "reveladas. Leia os três grupos de reviews de cada lado e marque se publicaria "
         "sem mudança (A / B / ambos / nenhum) e qual lê melhor (A / B / empate). "
         f"Responda em `{respostas.name}` (mesma pasta), uma linha por filme.", "", "---", ""]
    for n, f in enumerate(filmes, 1):
        a = a_e[f["slug"]]
        b = "publicado" if a == "treinado" else "treinado"
        L += [f"## Filme {n} — {f['titulo']}", "", "### 1. Bullets da síntese", ""]
        for letra, lado in (("A", a), ("B", b)):
            L += [f"#### {letra}", ""]
            for bucket in K.BUCKETS:
                L += [f"**{ROTULO_BUCKET[bucket]}**"] + bloco(f[lado][bucket])
        L += ["**Sua leitura deste filme:**", "",
              "| bloco | melhor (A / B / empate) | publicaria sem mudança (A / B / ambos / nenhum) |",
              "|---|---|---|", "| bullets | | |", "", "---", ""]
    L += [f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    return "\n".join(L)


def cmd_montar(a) -> None:
    if not V._versionado_e_limpo(F.ARQ_PREREGISTRO):
        raise SystemExit(f"{F.ARQ_PREREGISTRO} não está commitado (ou mudou)")
    if ARQ_MAPA.exists():
        raise SystemExit(f"{ARQ_MAPA} já existe: a leitura é montada UMA vez")
    if not F.ARQ_RESULTADO.exists():
        raise SystemExit("o C5 ainda não foi avaliado: o pré-registro manda rotular o C5 ANTES")
    split = K.ler_json(a.split)
    slugs = sorted(split["fixos_no_teste"])
    if sorted(K.REFERENCIA_5) != slugs or any(s not in set(split["teste"]) for s in slugs):
        raise SystemExit("os 5 de referência não são os do split (ou não são de teste)")
    pares = [k for k in F.pares_de_teste(split) if k[0] in slugs]
    regs_t = F.registros("treinado", pares)
    regs_b = (F.registros("base", pares)
              if (F.pasta_sintese("base") / "manifesto.json").exists() else {})
    fora = F.fora_por_memoria(regs_t, regs_b)
    filmes = []
    for slug in slugs:
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        pb = {b["bucket"]: b for b in pub["buckets"]}
        f = {"slug": slug, "titulo": pub["ficha"]["titulo"], "treinado": {}, "publicado": {}}
        for bucket in K.BUCKETS:
            k = (slug, bucket)
            fica = k in regs_t and k not in fora
            f["treinado"][bucket] = (regs_t[k].get("bucket_final") or {}) if fica else None
            f["publicado"][bucket] = pb[bucket] if fica else None
        filmes.append(f)
    a_e = sortear_lados(slugs, random.Random(SEMENTE))
    mapa = {"gerado_por": "scripts/finetune/fase4_leitura.py montar", "semente": SEMENTE,
            "a_e": a_e, "filmes": slugs, "fora_por_memoria": sorted(f"{s}/{b}" for s, b in fora),
            "preregistro_sha256": K.sha256_arquivo(F.ARQ_PREREGISTRO),
            "manifesto_treinado_sha256": K.sha256_arquivo(
                F.pasta_sintese("treinado") / "manifesto.json"),
            "script_sha256": K.sha256_arquivo(Path(__file__))}
    F.PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA)
    doc_dir = Path(a.doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    texto = documento(filmes, a_e, selo, doc_dir / RESPOSTAS)
    (doc_dir / DOC).write_text(texto, encoding="utf-8")
    with open(doc_dir / RESPOSTAS, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["filme", "publicaria", "melhor"])
        for n in range(1, len(slugs) + 1):
            wr.writerow([n, "", ""])
    print(json.dumps({"documento": str(doc_dir / DOC), "palavras": len(texto.split()),
                      "respostas": str(doc_dir / RESPOSTAS), "mapa": str(ARQ_MAPA),
                      "selo": selo, "fora_por_memoria": mapa["fora_por_memoria"]},
                     ensure_ascii=False, indent=1))


def avaliar(a_e: dict[str, str], filmes: list[str], respostas: list[dict]) -> dict:
    if [int(r["filme"]) for r in respostas] != list(range(1, len(filmes) + 1)):
        raise SystemExit("as respostas não têm uma linha por filme, na ordem")
    por_filme = []
    for slug, r in zip(filmes, respostas):
        pub, mel = r["publicaria"].strip(), r["melhor"].strip()
        if pub not in PUBLICARIA or mel not in MELHOR:
            raise SystemExit(f"{slug}: resposta inválida ({pub!r}, {mel!r})")
        letra_t = "A" if a_e[slug] == "treinado" else "B"
        letra_p = "B" if letra_t == "A" else "A"
        por_filme.append({"slug": slug, "treinado_publicavel": pub in (letra_t, "ambos"),
                          "publicado_publicavel": pub in (letra_p, "ambos"),
                          "melhor": {letra_t: "treinado", letra_p: "publicado"}.get(mel, "empate")})
    n_t = sum(f["treinado_publicavel"] for f in por_filme)
    return {"por_filme": por_filme, "treinado_publicavel": n_t,
            "publicado_publicavel": sum(f["publicado_publicavel"] for f in por_filme),
            "criterio": f"treinado publicável em ≥ {N_PUBLICAVEL_MIN} de {len(filmes)}",
            "C6_passa": n_t >= N_PUBLICAVEL_MIN}


def cmd_avaliar(a) -> None:
    if ARQ_RESULTADO.exists():
        raise SystemExit(f"{ARQ_RESULTADO} já existe: o C6 é avaliado UMA vez")
    mapa = K.ler_json(ARQ_MAPA)
    if a.selo and K.sha256_arquivo(ARQ_MAPA) != a.selo:
        raise SystemExit("o mapa não tem o selo impresso no documento")
    respostas = list(csv.DictReader(open(a.respostas, encoding="utf-8")))
    out = {"gerado_por": "scripts/finetune/fase4_leitura.py avaliar",
           "respostas_sha256": K.sha256_arquivo(Path(a.respostas)),
           "mapa_sha256": K.sha256_arquivo(ARQ_MAPA),
           **avaliar(mapa["a_e"], mapa["filmes"], respostas)}
    ARQ_RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--doc-dir", default=str(F.DOC_DIR), help="pasta do documento (fora do git)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("montar")
    v = sub.add_parser("avaliar")
    v.add_argument("--respostas", default=None)
    v.add_argument("--selo", default="", help="o selo impresso no fim do documento")
    a = ap.parse_args()
    if a.cmd == "avaliar" and a.respostas is None:
        a.respostas = str(Path(a.doc_dir) / RESPOSTAS)
    {"montar": cmd_montar, "avaliar": cmd_avaliar}[a.cmd](a)


if __name__ == "__main__":
    main()
