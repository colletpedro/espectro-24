#!/usr/bin/env python3
"""[piloto de expansão] Material de ROTULAGEM MANUAL dos pares obrigatórios.

**Por que existe.** O par obrigatório (`condicoes.selecionar`) força para o
outro lado o tema do grupo oposto que fala do "mesmo assunto" — régua
`condicoes.mesmo_assunto`, dois prefixos de conteúdo em comum. A mesma régua
define os irmãos de `sem_discriminacao`. Antes de mexer nela (lista de
palavras de discurso, limiar, qualquer coisa), o dono rotula os pares à mão:
"estes dois temas falam do mesmo assunto?". Qualquer mudança vem DEPOIS do
rótulo, e é medida contra ele.

**O que este script NÃO faz:** não classifica, não sugere, não ordena por
suspeita. Apresenta cada par com o que o formou — os dois temas, as duas
paráfrases, os prefixos em comum e as palavras de onde cada prefixo veio — e
a pergunta. Os pares vêm de `condicoes.pares_obrigatorios`, a MESMA
computação da seleção, não uma reimplementação.

Não chama LLM, não toca rede, não escreve em `resultado/`.

Uso:
    python scripts/pares_para_rotulagem.py --de DIR --lote NOME
      DIR: um `<slug>.json` por filme (só os slugs são lidos; os temas vêm
      de `resultado/<slug>.json`)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import condicoes as C  # noqa: E402
from espectro24 import veredito as V  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
SAIDA_DIR = RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"
GRUPO = {"positivas": "quem RECOMENDA", "negativas": "quem NÃO recomenda"}


def palavras_do_prefixo(texto: str, prefixo: str) -> list[str]:
    """As palavras do texto ORIGINAL (com acento) cujo prefixo de conteúdo é
    `prefixo` — para o dono ver de onde o prefixo veio."""
    achadas = []
    for tok in re.findall(r"[^\W\d_]+", texto or "", flags=re.UNICODE):
        norm = V.palavras_de_conteudo(tok)
        if norm and norm[0][:V.PREFIXO_PALAVRA] == prefixo \
                and tok not in achadas:
            achadas.append(tok)
    return achadas


def montar_pares(slugs: list[str], resultado_dir: Path = RESULTADO_DIR
                 ) -> list[dict]:
    pares = []
    for slug in sorted(slugs):
        doc = json.loads((Path(resultado_dir) / f"{slug}.json").read_text(
            encoding="utf-8"))
        idx = C.indexar(doc)
        for p in C.pares_obrigatorios(idx):
            b, f = idx[p["base"]], idx[p["forcado"]]
            comuns = sorted(C._prefixos_do_tema(b) & C._prefixos_do_tema(f))
            pares.append({
                "slug": slug,
                "base": {"id": b["id"], "grupo": GRUPO[b["bucket"]],
                         "tema": b["tema"], "parafrase": b["exemplo"]},
                "forcado": {"id": f["id"], "grupo": GRUPO[f["bucket"]],
                            "tema": f["tema"], "parafrase": f["exemplo"]},
                "prefixos": [{
                    "prefixo": px,
                    "no_base": palavras_do_prefixo(
                        b["tema"] + " " + b["exemplo"], px),
                    "no_forcado": palavras_do_prefixo(
                        f["tema"] + " " + f["exemplo"], px)}
                    for px in comuns],
            })
    for i, p in enumerate(pares, 1):
        p["id"] = f"P{i:02d}"
    return pares


def impressao_digital(pares: list[dict]) -> str:
    base = [[p["id"], p["slug"], p["base"]["id"], p["forcado"]["id"]]
            for p in pares]
    return hashlib.sha256(json.dumps(base).encode("utf-8")).hexdigest()[:12]


def renderizar(pares: list[dict], *, nome_lote: str) -> str:
    fp = impressao_digital(pares)
    n_filmes = len({p["slug"] for p in pares})
    L = [f"# Rotulagem dos pares obrigatórios — lote `{nome_lote}`",
         "",
         f"**Impressão digital dos pares: `{fp}`** · {len(pares)} pares · "
         f"{n_filmes} filmes com par",
         "",
         "## Como ler",
         "",
         "Cada coluna de condições parte dos três temas mais citados de um "
         "grupo. O **par obrigatório** acrescenta ao OUTRO lado um tema do "
         "grupo oposto quando o código julga que os dois falam do mesmo "
         "assunto — para a página não recomendar um traço sem mostrar a "
         "objeção que o outro grupo faz a ele.",
         "",
         "A régua do código: os dois temas compartilham **pelo menos dois "
         "prefixos** (as primeiras cinco letras, sem acento) entre as "
         "palavras de conteúdo do nome do tema e da paráfrase. Abaixo de cada "
         "par estão os prefixos em comum e as palavras de onde cada um veio, "
         "em cada tema.",
         "",
         "- **tema de base** — entrou por estar entre os mais citados; é ele "
         "que puxou o outro.",
         "- **tema forçado** — entrou pelo par.",
         "",
         "## A pergunta",
         "",
         "Para cada par: **estes dois temas falam do mesmo assunto?**",
         "",
         "    P01: SIM",
         "    P02: NÃO",
         "",
         "Uma resposta por par, citando o número. Este documento não traz "
         "classificação prévia; o julgamento é seu.",
         "",
         "## Pares",
         ""]
    for p in pares:
        b, f = p["base"], p["forcado"]
        L += [f"### {p['id']} · `{p['slug']}`",
              "",
              f"- **tema de base** — `{b['id']}` ({b['grupo']}): "
              f"*{b['tema']}*",
              f"    - o que o grupo diz: {b['parafrase']}",
              f"- **tema forçado** — `{f['id']}` ({f['grupo']}): "
              f"*{f['tema']}*",
              f"    - o que o grupo diz: {f['parafrase']}",
              "- **prefixos que os uniram:**"]
        for px in p["prefixos"]:
            L.append(f"    - `{px['prefixo']}` — no de base: "
                     f"{', '.join(px['no_base'])} · no forçado: "
                     f"{', '.join(px['no_forcado'])}")
        L += ["",
              f"**{p['id']} — estes dois temas falam do mesmo assunto?** "
              "SIM / NÃO",
              ""]
    return "\n".join(L).rstrip() + "\n"


def gabarito_vazio(pares: list[dict], *, nome_lote: str) -> dict:
    return {"lote": nome_lote, "impressao_digital": impressao_digital(pares),
            "pergunta": "estes dois temas falam do mesmo assunto?",
            "respostas_validas": ["SIM", "NÃO"],
            "pares": [{"id": p["id"], "slug": p["slug"],
                       "base": p["base"]["id"], "forcado": p["forcado"]["id"],
                       "prefixos": [x["prefixo"] for x in p["prefixos"]],
                       "resposta": None} for p in pares]}


def _checar_saida(destino: Path) -> None:
    alvo = destino.resolve()
    proibido = RESULTADO_DIR.resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise SystemExit(f"RECUSADO: --saida aponta para dentro de {proibido}.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--de", default=None,
                    help="diretório com um <slug>.json por filme do lote")
    ap.add_argument("--slug", action="append", default=[],
                    help="slug do lote (repetível), alternativa a --de")
    ap.add_argument("--lote", required=True)
    ap.add_argument("--saida", default=None, help="arquivo .md")
    args = ap.parse_args()

    destino = (Path(args.saida) if args.saida
               else SAIDA_DIR / f"ROTULAGEM_PARES_{args.lote}.md")
    _checar_saida(destino)
    slugs = sorted(set(args.slug) | ({p.stem for p in Path(args.de).glob(
        "*.json") if not p.name.startswith("_")} if args.de else set()))
    if not slugs:
        raise SystemExit("nada a fazer: use --de ou --slug")
    pares = montar_pares(slugs)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(renderizar(pares, nome_lote=args.lote), encoding="utf-8")
    destino.with_suffix(".json").write_text(
        json.dumps(gabarito_vazio(pares, nome_lote=args.lote),
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(pares)} pares · {impressao_digital(pares)} → {destino}")


if __name__ == "__main__":
    main()
