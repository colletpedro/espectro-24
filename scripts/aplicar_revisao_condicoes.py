#!/usr/bin/env python3
"""[piloto de expansão] APLICA a revisão do dono a um lote de condições.

**O fluxo.** `relatorio_revisao_condicoes.py` numera o lote (`C001`…) e o
identifica por impressão digital; a revisão volta com a linha EXATA que o
dono escreveu para cada item que ele corrigiu:

    C010 — Vale a pena se você se interessa por vínculos entre personagens…
    C024 — SEM CONDIÇÃO PUBLICÁVEL — R6 — o tema usa exclusivamente…

Este script reconstrói a numeração a partir do INSUMO (e recusa se a
impressão digital não bater), e escreve o lote corrigido:

  · texto do dono → substitui a frase, **verbatim**, recortada só da abertura
    da coluna (que o código renderiza), e ganha `origem: "leitura_humana"` —
    a marca que muda a régua da trava (`condicoes.FLAGS_LEXICAS`). Se o item
    era uma DESCARTADA, ele volta para a coluna, na posição da seleção;
  · "SEM CONDIÇÃO PUBLICÁVEL" → o item sai da coluna e entra em
    `sem_condicao_publicavel`, com a regra e o motivo do dono;
  · depois, `condicoes.consolidar_recusas` aplica a regra do par (marca
    `par_recusado`, move para `par_desfeito`) e recalcula `temas_saltados`.

O insumo fica intacto: é ele que a impressão digital identifica.

Não chama LLM, não toca rede, não escreve em `resultado/`.

Uso:
    python scripts/aplicar_revisao_condicoes.py --insumo DIR --correcoes JSON --saida DIR
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import condicoes as C  # noqa: E402
import relatorio_revisao_condicoes as RR  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"

_RE_LINHA = re.compile(r"^(?P<numero>C\d{3}) — (?P<resto>.+)$", re.S)
_RE_RECUSA = re.compile(
    r"^SEM CONDIÇÃO PUBLICÁVEL — (?P<regra>\S+) — (?P<motivo>.+)$", re.S)


class RevisaoInvalida(Exception):
    """A revisão não se aplica ao lote como ele está — nada é escrito."""


def interpretar(linha: str, item: dict) -> dict:
    """A linha do dono → `{tipo: "texto", texto}` ou `{tipo: "recusa",
    regra, motivo}`. Confere o número e a abertura da coluna."""
    m = _RE_LINHA.match(linha or "")
    if not m or m["numero"] != item["numero"]:
        raise RevisaoInvalida(f"{item['numero']}: linha não começa pelo "
                              f"número do item: {linha!r}")
    r = _RE_RECUSA.match(m["resto"])
    if r:
        return {"tipo": "recusa", "regra": r["regra"],
                "motivo": r["motivo"].strip()}
    abertura = RR.ABERTURA[item["lado"]] + " "
    if not m["resto"].startswith(abertura):
        raise RevisaoInvalida(
            f"{item['numero']}: a abertura não bate com a coluna "
            f"`{item['lado']}` do item: {linha!r}")
    return {"tipo": "texto", "texto": m["resto"][len(abertura):]}


def _achar(bloco: dict, item: dict) -> tuple[str, dict]:
    """Onde a frase original do item está: `("coluna"|"descartadas", c)`."""
    for c in bloco.get(item["lado"]) or []:
        if c.get("tema_origem") == item["tema_origem"] \
                and c.get("texto") == item["texto"]:
            return "coluna", c
    for c in bloco.get("descartadas") or []:
        if c.get("lado") == item["lado"] \
                and c.get("tema_origem") == item["tema_origem"] \
                and c.get("texto") == item["texto"]:
            return "descartadas", c
    raise RevisaoInvalida(f"{item['numero']}: a frase do item não está no "
                          "lote")


def aplicar(lote, correcoes: dict, resultado_dir: Path = RESULTADO_DIR
            ) -> dict[str, dict]:
    """`{slug: bloco corrigido}` para TODOS os filmes do lote."""
    itens = RR.montar_itens(lote, resultado_dir)
    fp = RR.impressao_digital(itens)
    if fp != correcoes.get("impressao_digital"):
        raise RevisaoInvalida(f"impressão digital do insumo é {fp}; a "
                              f"revisão é do lote "
                              f"{correcoes.get('impressao_digital')}")
    por_numero = {it["numero"]: it for it in itens}
    blocos = {slug: copy.deepcopy(b) for slug, b in lote}
    tocados = set()
    for cor in correcoes["itens"]:
        it = por_numero.get(cor["numero"])
        if it is None:
            raise RevisaoInvalida(f"{cor['numero']}: não existe no lote")
        d = interpretar(cor["linha_do_dono"], it)
        bloco = blocos[it["slug"]]
        onde, c = _achar(bloco, it)
        tocados.add(it["slug"])
        if d["tipo"] == "recusa":
            (bloco[it["lado"]] if onde == "coluna"
             else bloco["descartadas"]).remove(c)
            bloco.setdefault("sem_condicao_publicavel", []).append({
                "tema_origem": it["tema_origem"], "lado": it["lado"],
                "regra": d["regra"], "motivo": d["motivo"],
                "origem": C.ORIGEM_HUMANA})
            continue
        if onde == "coluna":
            c["texto"] = d["texto"]
            c["origem"] = C.ORIGEM_HUMANA
            continue
        # Descartada pelo validador, e o dono escreveu a frase: volta para a
        # coluna com o mesmo formato das outras, na posição da seleção.
        bloco["descartadas"].remove(c)
        t = C.indexar(json.loads((Path(resultado_dir) / f"{it['slug']}.json")
                                 .read_text(encoding="utf-8")))[it["tema_origem"]]
        bloco[it["lado"]].append({
            "texto": d["texto"], "tema_origem": t["id"],
            "bucket_origem": t["bucket"], "tema_texto": t["tema"],
            "rotulo_forca": t["rotulo_forca"], "origem": C.ORIGEM_HUMANA})
        pos = (bloco.get("temas_pedidos") or {}).get(it["lado"]) or []
        bloco[it["lado"]].sort(key=lambda x: pos.index(x["tema_origem"])
                               if x["tema_origem"] in pos else len(pos))
    for slug in tocados:
        idx = C.indexar(json.loads((Path(resultado_dir) / f"{slug}.json")
                                   .read_text(encoding="utf-8")))
        blocos[slug] = C.consolidar_recusas(blocos[slug], idx)
    return blocos


def _checar_saida(destino: Path) -> None:
    alvo = destino.resolve()
    proibido = RESULTADO_DIR.resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise SystemExit(f"RECUSADO: --saida aponta para dentro de {proibido}. "
                         "Publicar é com `publicar_condicoes.py`.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--insumo", required=True,
                    help="o lote que o relatório numerou (fica intacto)")
    ap.add_argument("--correcoes", required=True,
                    help="JSON com `impressao_digital` e `itens`")
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()

    destino = Path(args.saida)
    _checar_saida(destino)
    correcoes = json.loads(Path(args.correcoes).read_text(encoding="utf-8"))
    lote = RR.carregar_lote(Path(args.insumo))
    blocos = aplicar(lote, correcoes)
    destino.mkdir(parents=True, exist_ok=True)
    for slug, bloco in sorted(blocos.items()):
        (destino / f"{slug}.json").write_text(
            json.dumps({"slug": slug, "condicoes": bloco},
                       ensure_ascii=False, indent=1), encoding="utf-8")
    n_txt = sum(1 for b in blocos.values() for l in C.LADOS
                for c in b.get(l) or [] if c.get("origem") == C.ORIGEM_HUMANA)
    n_rec = sum(len(b.get("sem_condicao_publicavel") or [])
                for b in blocos.values())
    print(f"lote {correcoes['impressao_digital']} → {destino}: {n_txt} frases "
          f"do dono, {n_rec} sem condição publicável")


if __name__ == "__main__":
    main()
