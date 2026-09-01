"""Comparador de duas leituras humanas do mesmo bucket — calibração de gabarito.

Generalização de `comparar_gabarito_wonka.py` para qualquer par
(folha cega preenchida, leitura do modelo). A leitura do modelo pode estar em
um arquivo com VÁRIOS buckets (tabelas sob cabeçalhos `## <titulo>`), caso em
que `--secao` escolhe qual.

NÃO RODAR antes de o dono preencher a folha.

Uso:
    python scripts/comparar_gabarito.py \
        --dono FOLHA_LEITURA_CEGA_TALK_TO_ME_NEG.md \
        --code LEITURA_CODE_2_NAO_ABRIR_ANTES.md \
        --secao talk-to-me-2022

    python scripts/comparar_gabarito.py \
        --dono FOLHA_LEITURA_CEGA_NAPOLEON_MED.md \
        --code LEITURA_CODE_2_NAO_ABRIR_ANTES.md \
        --secao napoleon-2023

Reporta: concordância total, matriz de confusão nos quatro valores, a lista de
discordâncias com o texto da review ao lado, e — quando o registro da amostra
de controle está disponível — a concordância separada por GRUPO (G1, G2,
controle), que é o que diz se a amostra cega de controle pegou algo.

Aplica a regra de resolução registrada em `SPEC.md` §2.7: onde há divergência,
o veredito do dono vale. A contagem final sai com essa regra aplicada.

Zero rede, zero LLM.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

VALORES = ("sustenta", "não sustenta", "contradiz", "não sei julgar")

_NORMALIZA = {
    "sustenta": "sustenta",
    "nao sustenta": "não sustenta",
    "não sustenta": "não sustenta",
    "nao_sustenta": "não sustenta",
    "contradiz": "contradiz",
    "nao sei julgar": "não sei julgar",
    "não sei julgar": "não sei julgar",
    "nao sei": "não sei julgar",
    "não sei": "não sei julgar",
}


def _normaliza(txt: str) -> str | None:
    t = re.sub(r"\s+", " ", txt.strip().lower()).strip(" *_.:`")
    return _NORMALIZA.get(t)


def _parse_folha_cega(caminho: Path) -> tuple[dict[int, str], dict[int, str]]:
    """`({numero: veredito}, {numero: texto})` da folha do dono."""
    texto = caminho.read_text(encoding="utf-8")
    blocos = re.split(r"(?=^### \[\d+\])", texto, flags=re.MULTILINE)
    vereditos: dict[int, str] = {}
    textos: dict[int, str] = {}
    for bloco in blocos:
        m = re.match(r"### \[(\d+)\]", bloco)
        if not m:
            continue
        n = int(m.group(1))
        corpo = bloco.split("**Veredito:**")[0]
        textos[n] = "\n".join(l for l in corpo.splitlines()[2:] if l.strip()).strip()
        mv = re.search(r"\*\*Veredito:\*\*\s*(.+)", bloco)
        if mv:
            v = _normaliza(mv.group(1))
            if v:
                vereditos[n] = v
    return vereditos, textos


def _parse_leitura_code(caminho: Path, secao: str | None) -> dict[int, str]:
    """`{numero: veredito}` da tabela do modelo. `secao` filtra por cabeçalho
    `## ...` que contenha a string (necessário quando o arquivo tem vários
    buckets)."""
    texto = caminho.read_text(encoding="utf-8")
    if secao:
        partes = re.split(r"(?=^## )", texto, flags=re.MULTILINE)
        alvo = [p for p in partes if p.startswith("## ") and secao in p.splitlines()[0]]
        if not alvo:
            raise SystemExit(f"ERRO: seção {secao!r} não encontrada em {caminho}. "
                             f"Cabeçalhos: "
                             f"{[p.splitlines()[0] for p in partes if p.startswith('## ')]}")
        texto = alvo[0]
    saida: dict[int, str] = {}
    for linha in texto.splitlines():
        if not linha.startswith("|"):
            continue
        cols = [c.strip() for c in linha.strip("|").split("|")]
        if len(cols) < 3 or not re.match(r"^\d+$", cols[0]):
            continue
        v = _normaliza(cols[2].replace("**", ""))
        if v:
            saida[int(cols[0])] = v
    return saida


def _grupos(registro: Path | None, chave: str | None) -> dict[int, str]:
    """`{numero: 'G1'|'G2'|'controle'}`, do registro da amostra, se existir."""
    if not registro or not registro.exists() or not chave:
        return {}
    d = json.loads(registro.read_text(encoding="utf-8"))
    alvo = next((v for k, v in d.items() if chave in k), None)
    if not alvo:
        return {}
    g = {}
    for n in alvo.get("g1", []):
        g[n] = "G1"
    for n in alvo.get("g2", []):
        g[n] = "G2"
    for n in alvo.get("controle", []):
        g[n] = "controle"
    return g


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dono", type=Path, required=True)
    ap.add_argument("--code", type=Path, required=True)
    ap.add_argument("--secao", default=None,
                    help="filtra a seção da leitura do modelo (ex.: napoleon-2023)")
    ap.add_argument("--registro", type=Path, default=None,
                    help="registro_amostra_controle.json, para a quebra por grupo")
    ap.add_argument("--saida", type=Path, default=None)
    args = ap.parse_args()

    for f in (args.dono, args.code):
        if not f.exists():
            print(f"ERRO: {f} não existe.", file=sys.stderr)
            return 1

    dono, textos = _parse_folha_cega(args.dono)
    code = _parse_leitura_code(args.code, args.secao)
    grupos = _grupos(args.registro, args.secao)

    na_folha = sorted(textos)
    faltando = [n for n in na_folha if n not in dono]
    if faltando:
        print(f"AVISO: {len(faltando)} reviews sem veredito do dono: {faltando}")
        print("Preencha a folha antes da comparação final. "
              "Continuando só com o preenchido.\n")

    comuns = sorted(set(dono) & set(code))
    if not comuns:
        print("Nada em comum entre as duas leituras — nada a comparar.")
        return 0

    concorda = sum(1 for n in comuns if dono[n] == code[n])
    print("=== Concordância ===")
    print(f"  {concorda}/{len(comuns)} = {100 * concorda / len(comuns):.1f}%\n")

    if grupos:
        print("=== Concordância por grupo ===")
        for g in ("G1", "G2", "controle"):
            sel = [n for n in comuns if grupos.get(n) == g]
            if not sel:
                continue
            ok = sum(1 for n in sel if dono[n] == code[n])
            print(f"  {g:9s} {ok}/{len(sel)} = {100 * ok / len(sel):.0f}%")
        print("  (divergência no grupo 'controle' é o sinal mais forte: são as\n"
              "   reviews que o modelo julgou não tocarem sequer o assunto)\n")

    print("=== Matriz de confusão (linha = dono, coluna = modelo) ===")
    print("                 " + "".join(f"{v[:12]:>14s}" for v in VALORES))
    matriz = {a: {b: 0 for b in VALORES} for a in VALORES}
    for n in comuns:
        matriz[dono[n]][code[n]] += 1
    for a in VALORES:
        print(f"{a[:16]:16s} " + "".join(f"{matriz[a][b]:14d}" for b in VALORES))
    print()

    disc = [n for n in comuns if dono[n] != code[n]]
    print(f"=== Discordâncias ({len(disc)} de {len(comuns)}) ===\n")
    for n in disc:
        g = f" grupo={grupos[n]}" if n in grupos else ""
        print(f"--- [{n}] dono={dono[n]!r}  modelo={code[n]!r}{g}")
        print(textos.get(n, "(texto não recuperado)"))
        print()

    # Contagem final sob a regra de resolução: o dono vence onde diverge; nas
    # reviews fora da folha, o veredito do modelo permanece.
    final = dict(code)
    final.update(dono)
    n_sust = sum(1 for v in final.values() if v == "sustenta")
    n_contra = sum(1 for v in final.values() if v == "contradiz")
    n_nsj = sum(1 for v in final.values() if v == "não sei julgar")
    print("=== Contagem final do bucket (regra: o dono vence onde diverge) ===")
    print(f"  sustenta       {n_sust}")
    print(f"  contradiz      {n_contra}")
    print(f"  não sei julgar {n_nsj}")
    print(f"  total julgado  {len(final)}")

    if args.saida:
        args.saida.write_text(json.dumps({
            "concordancia": {"n": concorda, "total": len(comuns),
                             "fracao": concorda / len(comuns)},
            "por_grupo": {g: {"n": sum(1 for n in comuns
                                       if grupos.get(n) == g and dono[n] == code[n]),
                              "total": sum(1 for n in comuns if grupos.get(n) == g)}
                          for g in ("G1", "G2", "controle")} if grupos else {},
            "matriz_confusao": matriz,
            "discordancias": [{"n": n, "dono": dono[n], "modelo": code[n],
                               "grupo": grupos.get(n), "texto": textos.get(n, "")}
                              for n in disc],
            "contagem_final": {"sustenta": n_sust, "contradiz": n_contra,
                               "nao_sei_julgar": n_nsj, "total": len(final)},
            "faltando_dono": faltando,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
