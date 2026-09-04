#!/usr/bin/env python3
"""[v1.9.35] Compara a leitura do DONO com a leitura do modelo, condição a
condição.

Mesmo padrão de `comparar_gabarito.py`. **Onde houver divergência, o veredito
do DONO vale** (SPEC §2.7): o gabarito existe para julgar saída de modelo, e
deixá-lo ser decidido por modelo onde há divergência com o humano é a
circularidade que a calibração existe para quebrar.

Entrada:
  --folha   FOLHA_LEITURA_CONDICOES_35.md, já preenchida (A / R / C nas
            caixas `[ ]`)
  --modelo  JSON com {"R": [[slug, tema_id, motivo], ...], "C": [...]}
            (tudo que não estiver listado é lido como A)

Uso:
    python scripts/comparar_condicoes.py --folha FOLHA_LEITURA_CONDICOES_35.md \
        --modelo minha_leitura.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

VEREDITOS = ("A", "R", "C")
RE_FILME = re.compile(r"^## \d+\.\s+.*?`([^`]+)`\s*$")
RE_COND = re.compile(r"^- \*\*\[([^\]]*)\]\*\*\s+(.*)$")
RE_TEMA = re.compile(r"^\s+- tema: \*(.*)\*\s*$")


def ler_folha(caminho: Path) -> list[dict]:
    """As condições da folha, na ordem, com o veredito marcado na caixa.

    Caixa vazia (ou só espaço) significa NÃO LIDA — e isso é distinguido de
    um veredito, nunca tratado como aprovação por omissão. É a mesma regra do
    piso de §2.5: ausência significa "não medido", nunca "medido e sem
    achado".
    """
    itens, slug, pend = [], None, None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = RE_FILME.match(linha)
        if m:
            slug = m.group(1)
            continue
        m = RE_COND.match(linha)
        if m:
            marca = m.group(1).strip().upper()
            pend = {"slug": slug, "texto": m.group(2).strip(),
                    "veredito": marca if marca in VEREDITOS else None,
                    "marca_bruta": m.group(1), "tema": None}
            itens.append(pend)
            continue
        m = RE_TEMA.match(linha)
        if m and pend is not None:
            pend["tema"] = m.group(1)
            pend = None
    return itens


def ler_modelo(caminho: Path) -> dict:
    d = json.loads(caminho.read_text(encoding="utf-8"))
    fora = {}
    for v in ("R", "C"):
        for entrada in d.get(v, []):
            fora[(entrada[0], entrada[1])] = (v, entrada[2] if len(entrada) > 2 else "")
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folha", required=True)
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--mapa", help="JSON slug+texto -> tema_id, para casar as "
                                   "duas leituras (opcional)")
    args = ap.parse_args()

    folha = ler_folha(Path(args.folha))
    modelo = ler_modelo(Path(args.modelo))
    mapa = json.loads(Path(args.mapa).read_text()) if args.mapa else {}

    lidas = [i for i in folha if i["veredito"]]
    print(f"condições na folha: {len(folha)}")
    print(f"lidas (com veredito marcado): {len(lidas)}")
    print(f"em branco: {len(folha) - len(lidas)}")
    if not lidas:
        print("\nNada a comparar ainda — a folha do dono está em branco.")
        print("Este script fica pronto para quando ela voltar preenchida.")
        return

    matriz = Counter()
    divergencias = []
    for item in lidas:
        chave = mapa.get(f"{item['slug']}|{item['texto']}")
        v_modelo = "A"
        motivo = ""
        if chave and (item["slug"], chave) in modelo:
            v_modelo, motivo = modelo[(item["slug"], chave)]
        matriz[(item["veredito"], v_modelo)] += 1
        if item["veredito"] != v_modelo:
            divergencias.append((item, v_modelo, motivo))

    acordo = sum(v for (d, m), v in matriz.items() if d == m)
    print(f"\nconcordância: {acordo}/{len(lidas)} = {100*acordo/len(lidas):.1f}%")
    print(f"\n{'':12}" + "".join(f"{'modelo ' + v:>12}" for v in VEREDITOS))
    for d in VEREDITOS:
        print(f"{'dono ' + d:12}" + "".join(f"{matriz[(d, m)]:>12}"
                                            for m in VEREDITOS))
    print(f"\ndivergências: {len(divergencias)}")
    for item, v_modelo, motivo in divergencias:
        print(f"  {item['slug']:26} dono={item['veredito']} modelo={v_modelo}")
        print(f"      {item['texto'][:88]}")
        if motivo:
            print(f"      motivo do modelo: {motivo}")
    print("\nREGRA DE RESOLUÇÃO: onde há divergência, o veredito do DONO vale.")


if __name__ == "__main__":
    main()
