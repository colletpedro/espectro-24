"""Guarda de quantidade — checagem de fluência pelo dono (2026-11-05).

Critério fixado ANTES de mostrar (`finetune/guarda/GUARDA_QUANTIDADE.md`, commitado):
- 30 pares antes/depois sorteados (semente 20261106) entre os textos que a guarda
  ALTEROU nos dados de desenvolvimento (`dev_pares.json`, textos distintos);
- documento cego: só os dois textos, sem fonte, regra nem filme;
- pergunta, por par: "o texto reescrito está correto em português e diz a mesma
  coisa que o original? S/N";
- passa com ≥ 27 de 30 "S". Se reprovar, PARA (nenhum ajuste da guarda para
  "passar" no mesmo conjunto: um conjunto novo exigiria novo sorteio e novo registro).

    montar    documento, respostas em branco e mapa (id → fonte, filme, regras)
    avaliar   veredito (UMA vez), com o selo impresso no fim do documento
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
from espectro24 import guarda_quantidade as G  # noqa: E402

PASTA = K.FINETUNE_DIR / "guarda"
ARQ_PARES = PASTA / "dev_pares.json"
ARQ_MAPA = PASTA / "fluencia_mapa.json"
ARQ_RESULTADO = PASTA / "fluencia_resultado.json"
ARQ_CRITERIO = PASTA / "GUARDA_QUANTIDADE.md"
DOC_DIR = K.RAIZ / "docs" / "arquivo-de-estudos" / "finetune-guarda"
DOC = "fluencia.md"
RESPOSTAS = "fluencia_respostas.csv"
SEMENTE = 20261106
N = 30
MIN_S = 27


def sortear(pares: list[dict]) -> tuple[list[dict], int]:
    """Textos distintos (antes, depois), em ordem determinística, sorteio sem reposição."""
    vistos, distintos = set(), []
    for p in sorted(pares, key=lambda p: (p["antes"], p["depois"])):
        if (p["antes"], p["depois"]) not in vistos:
            vistos.add((p["antes"], p["depois"]))
            distintos.append(p)
    return random.Random(SEMENTE).sample(distintos, N), len(distintos)


def exigir_criterio_commitado() -> None:
    real = ARQ_CRITERIO.resolve()
    repo, nome = real.parent, real.name
    if K.rodar_texto(["git", "-C", str(repo), "ls-files", "--error-unmatch", nome]).returncode:
        raise SystemExit(f"{nome} não está commitado: o critério é fixado ANTES de mostrar")
    if K.rodar_texto(["git", "-C", str(repo), "diff", "--quiet", "HEAD", "--", nome]).returncode:
        raise SystemExit(f"{nome} difere do commitado")


def cmd_montar(a) -> None:
    exigir_criterio_commitado()
    if ARQ_MAPA.exists():
        raise SystemExit(f"{ARQ_MAPA.name} já existe: o sorteio é feito UMA vez")
    dados = K.ler_json(ARQ_PARES)
    if dados["guarda_sha256"] != K.sha256_arquivo(Path(G.__file__)):
        raise SystemExit("a guarda mudou desde a medição (dev_pares.json): rode `medir_guarda.py medir`")
    escolhidos, n_pop = sortear(dados["pares"])
    mapa = {"gerado_por": "scripts/finetune/fluencia_guarda.py montar", "semente": SEMENTE,
            "n": N, "min_s": MIN_S, "populacao_textos_distintos": n_pop,
            "guarda_sha256": dados["guarda_sha256"], "criterio_sha256": K.sha256_arquivo(ARQ_CRITERIO),
            "script_sha256": K.sha256_arquivo(Path(__file__)),
            "itens": [{"id": i, "fonte": p["fonte"], "slug": p["slug"], "bucket": p["bucket"],
                       "regras": p["regras"], "antes": p["antes"], "depois": p["depois"]}
                      for i, p in enumerate(escolhidos, 1)]}
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA)
    L = ["# Checagem de fluência — guarda de quantidade", "",
         "Cada item traz um texto **original** e a sua **reescrita** automática (só foram "
         "trocadas expressões de quantidade como \"muitos\", \"algumas\", \"frequentemente\").", "",
         "Para cada item, responda na coluna `resposta` de `" + RESPOSTAS + "`:", "",
         "> **o texto reescrito está correto em português e diz a mesma coisa que o original? S ou N**", "",
         "- `S`: gramática e leitura corretas **e** o mesmo conteúdo (sem perder nem inverter "
         "uma avaliação); a única diferença aceitável é a expressão de quantidade ter saído "
         "ou ter virado uma forma sem quantidade.",
         "- `N`: erro de português (concordância, pontuação, frase estranha) **ou** o sentido mudou.",
         "- Se hesitar, é `N`.", "", f"{N} itens. Passa com {MIN_S} ou mais `S`.", "", "---", ""]
    for it in mapa["itens"]:
        L += [f"## {it['id']}", "", f"**Original:** {it['antes']}", "", f"**Reescrito:** {it['depois']}", ""]
    L += ["---", "", f"Selo: `{selo}`"]
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    (DOC_DIR / DOC).write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(DOC_DIR / RESPOSTAS, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "resposta"])
        for i in range(1, N + 1):
            w.writerow([i, ""])
    print(json.dumps({"documento": str(DOC_DIR / DOC), "respostas": str(DOC_DIR / RESPOSTAS),
                      "itens": N, "populacao": n_pop, "selo": selo}, ensure_ascii=False, indent=1))


def avaliar(respostas: list[dict]) -> dict:
    if [int(r["id"]) for r in respostas] != list(range(1, N + 1)):
        raise SystemExit("as respostas não têm uma linha por item, na ordem")
    val = [r["resposta"].strip().upper() for r in respostas]
    if any(v not in ("S", "N") for v in val):
        raise SystemExit("resposta inválida: só S ou N, em todos os itens")
    n_s = sum(v == "S" for v in val)
    return {"S": n_s, "N": N - n_s, "criterio": f"≥ {MIN_S} de {N} S", "passa": n_s >= MIN_S,
            "ids_N": [i for i, v in enumerate(val, 1) if v == "N"]}


def cmd_avaliar(a) -> None:
    if ARQ_RESULTADO.exists():
        raise SystemExit(f"{ARQ_RESULTADO.name} já existe: a fluência é avaliada UMA vez")
    if a.selo and K.sha256_arquivo(ARQ_MAPA) != a.selo:
        raise SystemExit("o mapa não tem o selo impresso no documento")
    resp = list(csv.DictReader(open(a.respostas, encoding="utf-8")))
    out = {"gerado_por": "scripts/finetune/fluencia_guarda.py avaliar",
           "respostas_sha256": K.sha256_arquivo(Path(a.respostas)),
           "mapa_sha256": K.sha256_arquivo(ARQ_MAPA), **avaliar(resp)}
    mapa = K.ler_json(ARQ_MAPA)
    out["itens_N"] = [{k: it[k] for k in ("id", "fonte", "regras", "antes", "depois")}
                      for it in mapa["itens"] if it["id"] in out["ids_N"]]
    ARQ_RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"S {out['S']}/{N} — {'PASSA' if out['passa'] else 'REPROVA (pare)'} · "
          f"{ARQ_RESULTADO.name} sha256 {K.sha256_arquivo(ARQ_RESULTADO)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("montar")
    v = sub.add_parser("avaliar")
    v.add_argument("--respostas", default=str(DOC_DIR / RESPOSTAS))
    v.add_argument("--selo", default="", help="o selo impresso no fim do documento")
    a = ap.parse_args()
    {"montar": cmd_montar, "avaliar": cmd_avaliar}[a.cmd](a)


if __name__ == "__main__":
    main()
