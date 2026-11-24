#!/usr/bin/env python3
"""Documento de leitura do dono dos filmes do C22 a publicar: só os bullets, "publico? S/N", em lotes de 10.

Pré-requisitos (nesta ordem): `c22_fallback.py aplicar` (saída de produção, com o fallback aceito no lugar)
e `conferir_tmdb_c22.py` (identidade). Os 5 do C6 já foram aprovados pelo dono (S nos 5, pelo chat em
2026-11-24): não entram nos lotes, exceto se o fallback trocou o texto de um bucket deles (aí o bucket novo
vai numa seção de RE-LEITURA, porque o que o dono aprovou foi o texto antigo). Filme com divergência no TMDB
ou com bucket sem síntese válida sai e vai para a lista à parte.

    lotes   (Mac)   -> docs/arquivo-de-estudos/finetune-c22/leitura_lote_{1,2,3}.md, leitura_lotes_respostas.csv,
                       leitura_fora.json (quem saiu e por quê)
    avaliar (Mac)   lê leitura_lotes_respostas.csv (filme,publico S/N) -> finetune/c22/aprovados.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum as K  # noqa: E402
import c22 as X  # noqa: E402
import c22_fallback as FB  # noqa: E402

DOC_DIR = X.DOC_DIR
TAMANHO_LOTE = 10
N_LOTES = 3
ARQ_RESPOSTAS = DOC_DIR / "leitura_lotes_respostas.csv"
ARQ_FORA = DOC_DIR / "leitura_fora.json"
ARQ_APROVADOS = X.PASTA / "aprovados.json"
ARQ_TMDB_PADRAO = K.RAIZ.parent / "espectro-24" / "resultado" / "c22-publicacao" / "tmdb_conferencia.json"
ROTULO = {"negativas": "Negativas", "medianas": "Medianas", "positivas": "Positivas"}


def carregar_producao(dir_producao: Path) -> dict[tuple[str, str], dict]:
    return {(r["slug"], r["bucket"]): r
            for r in (json.loads(p.read_text(encoding="utf-8"))
                      for p in sorted(dir_producao.glob("*__*.json")))}


def motivo_de_saida(slug: str, producao: dict, tmdb_ok: set[str]) -> str | None:
    if slug not in tmdb_ok:
        return "tmdb_divergente_ou_indisponivel"
    for b in K.BUCKETS:
        r = producao.get((slug, b))
        if r is None or not r.get("ok") or not (r.get("bucket_final") or {}).get("temas"):
            return f"bucket_{b}_sem_sintese_valida"
    return None


def bloco(r: dict) -> list[str]:
    temas = r["bucket_final"]["temas"]
    out = [f"- **{t['tema']}** — {t['exemplo_parafraseado']}" for t in temas]
    pend = [t["tema"] for t in temas if t.get("quantidade_pendente")]
    if pend:
        out.append(f"  - ⚠ palavra de quantidade ainda presente em: {'; '.join(pend)}")
    return out + [""]


def documento(titulo_lote: str, slugs: list[str], titulos: dict, producao: dict, extra: list[str] | None = None) -> str:
    L_ = [f"# Leitura do dono — {titulo_lote}", "",
          f"Para cada filme, leia os bullets dos três grupos e responda na coluna `publico` de "
          f"`{ARQ_RESPOSTAS.name}`:", "", "> **publico? S ou N**", "",
          "`S` = você publica esta síntese como está. `N` = há algo que impede. Se hesitar, é `N`.", "",
          "---", ""]
    for slug in slugs:
        L_ += [f"## {titulos[slug]}  ·  `{slug}`", ""]
        for b in K.BUCKETS:
            L_ += [f"**{ROTULO[b]}**", ""] + bloco(producao[(slug, b)])
        L_ += ["---", ""]
    return "\n".join(L_ + (extra or [])) + "\n"


def montar(escopo: dict, producao: dict, tmdb_ok: set[str], c6_aprovados: list[str]) -> dict:
    titulos = {f["slug"]: f"{f['titulo']} ({f['ano']})" for f in escopo["incluidos"]}
    fora = {s: m for s in titulos if s not in c6_aprovados and (m := motivo_de_saida(s, producao, tmdb_ok))}
    fora_c6 = {s: m for s in c6_aprovados if (m := motivo_de_saida(s, producao, tmdb_ok))}
    candidatos = sorted(s for s in titulos if s not in c6_aprovados and s not in fora)
    lotes = [candidatos[i * TAMANHO_LOTE:(i + 1) * TAMANHO_LOTE] for i in range(N_LOTES)]
    sobra = candidatos[N_LOTES * TAMANHO_LOTE:]
    # os 5 do C6: o bucket que o fallback trocou precisa de nova leitura (o dono aprovou o texto antigo)
    reler = [(s, b) for s in c6_aprovados if s not in fora_c6 for b in K.BUCKETS
             if producao[(s, b)]["origem"] == "c22_fallback_aceito"]
    return {"titulos": titulos, "lotes": lotes, "sobra": sobra, "fora": fora, "fora_c6": fora_c6, "reler": reler}


def cmd_lotes(a) -> None:
    escopo = K.ler_json(X.ARQ_ESCOPO)
    producao = carregar_producao(FB.DIR_PRODUCAO)
    if len(producao) != 105:
        raise SystemExit(f"a saída de produção tem {len(producao)} buckets (esperado 105): rode `c22_fallback.py aplicar`")
    tmdb = json.loads(Path(a.tmdb).read_text(encoding="utf-8"))
    c6 = [r["slug"] for r in K.ler_json(X.ARQ_C6_RESULTADO)["por_filme"] if r["publicavel"]]
    m = montar(escopo, producao, set(tmdb["publicaveis"]), c6)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    for n, lote in enumerate(m["lotes"], 1):
        extra = None
        if n == 1 and m["reler"]:
            extra = ["## RE-LEITURA — buckets dos 5 filmes do C6 que o fallback trocou", "",
                     "O que você aprovou no C6 foi o texto ANTIGO destes buckets. O texto abaixo é o novo.", ""]
            for s, b in m["reler"]:
                extra += [f"### {m['titulos'][s]} — {ROTULO[b]}", ""] + bloco(producao[(s, b)])
            extra += ["Responda no CSV, linha `<slug>:<bucket>`.", ""]
        (DOC_DIR / f"leitura_lote_{n}.md").write_text(
            documento(f"lote {n} de {N_LOTES}", lote, m["titulos"], producao, extra), encoding="utf-8")
    with open(ARQ_RESPOSTAS, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["filme", "publico"])
        for lote in m["lotes"]:
            for s in lote:
                w.writerow([s, ""])
        for s, b in m["reler"]:
            w.writerow([f"{s}:{b}", ""])
    ARQ_FORA.write_text(json.dumps({"fora": m["fora"], "fora_c6": m["fora_c6"], "sobra_sem_lote": m["sobra"],
                                    "releitura_c6": [f"{s}:{b}" for s, b in m["reler"]]},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"lotes": [len(x) for x in m["lotes"]], "fora": m["fora"], "fora_c6": m["fora_c6"],
                      "sobra_sem_lote": m["sobra"], "releitura_c6": len(m["reler"])}, ensure_ascii=False))


def cmd_avaliar(a) -> None:
    rows = list(csv.DictReader(open(ARQ_RESPOSTAS, encoding="utf-8")))
    val = {r["filme"]: r["publico"].strip().upper() for r in rows}
    if any(v not in ("S", "N") for v in val.values()):
        raise SystemExit("há linha sem S/N no CSV")
    c6 = [r["slug"] for r in K.ler_json(X.ARQ_C6_RESULTADO)["por_filme"] if r["publicavel"]]
    trocados = {k.split(":")[0] for k in val if ":" in k and val[k] == "N"}
    aprovados = sorted([s for s, v in val.items() if ":" not in s and v == "S"] +
                       [s for s in c6 if s not in trocados])
    out = {"gerado_por": "scripts/finetune/c22_leitura.py avaliar", "aprovados": aprovados,
           "reprovados": sorted(s for s, v in val.items() if v == "N"),
           "c6_pendentes_de_releitura_reprovados": sorted(trocados),
           "respostas_sha256": K.sha256_arquivo(ARQ_RESPOSTAS)}
    ARQ_APROVADOS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(aprovados)} aprovados, {len(out['reprovados'])} reprovados")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("lotes")
    l.add_argument("--tmdb", default=str(ARQ_TMDB_PADRAO))
    sub.add_parser("avaliar")
    a = ap.parse_args()
    {"lotes": cmd_lotes, "avaliar": cmd_avaliar}[a.cmd](a)


if __name__ == "__main__":
    main()
