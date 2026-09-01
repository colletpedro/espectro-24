"""Comparador de duas leituras humanas do mesmo bucket — calibração de gabarito.

NÃO RODAR ainda: espera o dono preencher `FOLHA_LEITURA_CEGA_WONKA_NEG.md`.

Uso:
    python scripts/comparar_gabarito_wonka.py \
        --dono FOLHA_LEITURA_CEGA_WONKA_NEG.md \
        --code LEITURA_CODE_NAO_ABRIR_ANTES.md

Lê os dois arquivos Markdown, casa por número de review `[N]`, e reporta:
concordância total, matriz de confusão nos quatro valores (os três de P1-P7
mais "não sei julgar"), e a lista de discordâncias com o texto da review ao
lado para leitura conjunta.

Zero rede, zero LLM. Só parsing de Markdown e comparação.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

VALORES = ("sustenta", "não sustenta", "contradiz", "não sei julgar")

# Aceita variações de digitação razoáveis (acento, maiúscula, espaço extra).
_NORMALIZA = {
    "sustenta": "sustenta",
    "nao sustenta": "não sustenta",
    "não sustenta": "não sustenta",
    "nãosustenta": "não sustenta",
    "contradiz": "contradiz",
    "nao sei julgar": "não sei julgar",
    "não sei julgar": "não sei julgar",
    "nao sei": "não sei julgar",
    "não sei": "não sei julgar",
}


def _normaliza_veredito(txt: str) -> str | None:
    t = txt.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" *_.:")
    return _NORMALIZA.get(t)


def _parse_folha_cega(caminho: Path) -> dict[int, str]:
    """Extrai `{numero: veredito}` de `FOLHA_LEITURA_CEGA_WONKA_NEG.md` —
    o padrão é `### [N] ...` seguido, em algum ponto antes do próximo `###`,
    de uma linha `**Veredito:** <algo>`."""
    texto = caminho.read_text(encoding="utf-8")
    blocos = re.split(r"(?=^### \[\d+\])", texto, flags=re.MULTILINE)
    saida: dict[int, str] = {}
    for bloco in blocos:
        m = re.match(r"### \[(\d+)\]", bloco)
        if not m:
            continue
        n = int(m.group(1))
        mv = re.search(r"\*\*Veredito:\*\*\s*(.+)", bloco)
        if not mv:
            continue
        v = _normaliza_veredito(mv.group(1))
        if v:
            saida[n] = v
    return saida


def _parse_tabela_code(caminho: Path) -> dict[int, str]:
    """Extrai `{numero: veredito}` da tabela Markdown de
    `LEITURA_CODE_NAO_ABRIR_ANTES.md` — colunas `| # | id | veredito | ... |`."""
    texto = caminho.read_text(encoding="utf-8")
    saida: dict[int, str] = {}
    for linha in texto.splitlines():
        if not linha.startswith("|"):
            continue
        cols = [c.strip() for c in linha.strip("|").split("|")]
        if len(cols) < 3:
            continue
        if not re.match(r"^\d+$", cols[0]):
            continue
        n = int(cols[0])
        v = _normaliza_veredito(cols[2].replace("**", ""))
        if v:
            saida[n] = v
    return saida


def _textos_das_reviews(caminho_folha: Path) -> dict[int, str]:
    """Reaproveita a folha cega para recuperar o texto de cada review, para
    exibir ao lado das discordâncias."""
    texto = caminho_folha.read_text(encoding="utf-8")
    blocos = re.split(r"(?=^### \[\d+\])", texto, flags=re.MULTILINE)
    saida: dict[int, str] = {}
    for bloco in blocos:
        m = re.match(r"### \[(\d+)\]", bloco)
        if not m:
            continue
        n = int(m.group(1))
        # o texto da review fica entre a linha de cabeçalho e a linha do
        # veredito, sem a marca "**Veredito:**"
        corpo = bloco.split("**Veredito:**")[0]
        linhas = corpo.splitlines()[2:]  # pula "### [N]..." e a linha em branco
        txt = "\n".join(l for l in linhas if l.strip()).strip()
        saida[n] = txt
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dono", type=Path, default=RAIZ / "FOLHA_LEITURA_CEGA_WONKA_NEG.md",
                    help="folha preenchida pelo dono")
    ap.add_argument("--code", type=Path, default=RAIZ / "LEITURA_CODE_NAO_ABRIR_ANTES.md",
                    help="leitura própria (código)")
    ap.add_argument("--saida", type=Path, default=None,
                     help="se dado, também grava um JSON com o resultado completo")
    args = ap.parse_args()

    if not args.dono.exists():
        print(f"ERRO: {args.dono} não existe.", file=sys.stderr)
        return 1
    if not args.code.exists():
        print(f"ERRO: {args.code} não existe.", file=sys.stderr)
        return 1

    dono = _parse_folha_cega(args.dono)
    code = _parse_tabela_code(args.code)
    textos = _textos_das_reviews(args.dono)

    faltando_dono = sorted(set(range(1, 33)) - set(dono))
    if faltando_dono:
        print(f"AVISO: {len(faltando_dono)} reviews sem veredito do dono ainda: "
              f"{faltando_dono}")
        print("Preencha a folha antes de rodar a comparação final. Continuando "
              "só com o que já foi preenchido.\n")

    comuns = sorted(set(dono) & set(code))
    if not comuns:
        print("Nada em comum entre as duas leituras ainda — nada a comparar.")
        return 0

    concorda = sum(1 for n in comuns if dono[n] == code[n])
    print(f"=== Concordância ===")
    print(f"  {concorda}/{len(comuns)} = {100*concorda/len(comuns):.1f}%\n")

    print("=== Matriz de confusão (linha = dono, coluna = code) ===")
    header = "                 " + "".join(f"{v[:12]:>14s}" for v in VALORES)
    print(header)
    matriz = {a: {b: 0 for b in VALORES} for a in VALORES}
    for n in comuns:
        matriz[dono[n]][code[n]] += 1
    for a in VALORES:
        linha = f"{a[:16]:16s} " + "".join(f"{matriz[a][b]:14d}" for b in VALORES)
        print(linha)
    print()

    disc = [n for n in comuns if dono[n] != code[n]]
    print(f"=== Discordâncias ({len(disc)} de {len(comuns)}) ===\n")
    for n in disc:
        print(f"--- [{n}] dono={dono[n]!r}  code={code[n]!r}")
        print(textos.get(n, "(texto não recuperado)"))
        print()

    if args.saida:
        resultado = {
            "concordancia": {"n": concorda, "total": len(comuns),
                             "fracao": concorda / len(comuns)},
            "matriz_confusao": matriz,
            "discordancias": [
                {"n": n, "dono": dono[n], "code": code[n], "texto": textos.get(n, "")}
                for n in disc
            ],
            "faltando_dono": faltando_dono,
        }
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2))
        print(f"Gravado em {args.saida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
