#!/usr/bin/env python3
"""[2026-09-14] Republica SÓ o bloco `eixos` de UM filme já publicado, a partir
da classificação de produção ATUAL — zero LLM, zero rede.

**Para que existe.** A retentativa FILME A FILME do verificador de
`impacto_emocional` (`ABERTO.md` C3/C16): uma review retentada não recupera
um valor — produz um veredito NOVO, que pode confirmar ou remover a marcação.
O bloco publicado precisa refletir esse veredito e, se a review continuar
falhando, a marca `verificacao_pendente`. Nada além disso pode mudar no filme.

**O que NÃO roda:** coleta, seleção, síntese, rotulagem [D3], narrativa,
veredito, condições. As frases das células são RELIDAS do bloco publicado
(`eixos.temas_do_bloco`, o mesmo mecanismo de `aplicar_lei_margem.py`); a
proveniência é anexada por `pipeline.anexar_proveniencia`, a mesma regra de
`montar_eixos`.

**Mede antes de escrever.** Sem `--aplicar`, só mede, antes × depois:
contraste, células que cruzam a margem (`acima_da_margem`), bullets (`n`
incluso), e os briefings de narrativa, veredito e condições — o que o texto
publicado leu. `--aplicar` grava SÓ quando nada disso mudou; se mudou, RECUSA
e diz o quê. Decisão do dono: um filme cujo estado publicado muda para antes
de ser republicado. A única chave escrita é `eixos`, e o documento é conferido
campo a campo antes de gravar.

Uso:
    python scripts/republicar_eixos.py --slug speak-no-evil-2022
    python scripts/republicar_eixos.py --slug speak-no-evil-2022 --aplicar
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import briefing as B  # noqa: E402
from espectro24 import condicoes as C  # noqa: E402
from espectro24 import eixos as E  # noqa: E402
from espectro24 import pipeline as P  # noqa: E402
from espectro24 import veredito as V  # noqa: E402
from espectro24.config import SPEC_VERSION  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
RAIZ_BRUTO = RAIZ / "dados" / "bruto"
CHAVE = "eixos"


def bloco_novo(slug: str, doc: dict) -> dict:
    """O bloco `eixos` sob a classificação de produção atual, montado como
    `pipeline.montar_eixos` o monta — mas com as frases do publicado."""
    with contextlib.chdir(RAIZ):
        catalogo, meta = P._carregar_consenso_producao(E)
        if not catalogo or slug not in catalogo:
            raise SystemExit(f"{slug}: sem classificação de produção.")
        analisadas = P.ids_analisados_do_bruto(
            slug, coleta=doc.get("coleta"), raiz=str(RAIZ_BRUTO))
        bloco = E.montar_bloco(catalogo[slug], analisadas,
                               E.temas_do_bloco(doc[CHAVE]))
        if "rotulagem" in doc[CHAVE]:
            bloco["rotulagem"] = doc[CHAVE]["rotulagem"]   # as mesmas frases
        bloco["spec_version"] = SPEC_VERSION
        caminho = E.CONSENSO_PADRAO
        if meta is not None:
            bloco["verificador"] = meta
            caminho = E.CONSENSO_VERIFICADO
        P.anexar_proveniencia(bloco, slug, analisadas, caminho)
    return bloco


def _celulas(bloco: dict) -> dict[tuple[str, str], dict]:
    return {(l["eixo"], b): c for l in bloco.get("linhas") or []
            for b, c in (l.get("por_bucket") or {}).items()}


def _bullets(bloco: dict) -> dict[str, dict]:
    return {l["eixo"]: l.get("bullet_de") for l in bloco.get("linhas") or []}


def _briefings(doc: dict) -> dict[str, str | None]:
    """O que cada texto publicado LEU — serializado, que é o que o modelo
    recebeu. Filme sem o texto publicado conta mesmo assim: um briefing que
    muda é um texto que, gerado hoje, sairia diferente."""
    fora = {}
    for nome, mod in (("narrativa", B), ("veredito", V), ("condicoes", C)):
        b = mod.montar_briefing(doc)
        fora[nome] = mod.serializar_briefing(b) if b else None
    return fora


def medir(slug: str) -> dict:
    """Antes × depois, sem escrever nada."""
    doc = json.loads((RESULTADO_DIR / f"{slug}.json").read_text(encoding="utf-8"))
    antes = doc[CHAVE]
    novo = bloco_novo(slug, doc)
    doc_novo = copy.deepcopy(doc)
    doc_novo[CHAVE] = novo

    ca, cn = _celulas(antes), _celulas(novo)
    chaves = sorted(set(ca) | set(cn))

    def cel(c, k, campo):
        return (c.get(k) or {}).get(campo)

    margem = [f"{e}/{b}: {cel(ca, (e, b), 'acima_da_margem')} -> "
              f"{cel(cn, (e, b), 'acima_da_margem')}"
              for e, b in chaves
              if cel(ca, (e, b), "acima_da_margem") != cel(cn, (e, b), "acima_da_margem")]
    mencoes = [f"{e}/{b}: {cel(ca, (e, b), 'mencoes')}/{cel(ca, (e, b), 'de_n')} "
               f"-> {cel(cn, (e, b), 'mencoes')}/{cel(cn, (e, b), 'de_n')} "
               f"(lift {cel(ca, (e, b), 'lift_pp')} -> {cel(cn, (e, b), 'lift_pp')}pp)"
               for e, b in chaves
               if (cel(ca, (e, b), "mencoes"), cel(ca, (e, b), "de_n"))
               != (cel(cn, (e, b), "mencoes"), cel(cn, (e, b), "de_n"))]
    # `verificador.n_removidas_no_corpus` é uma contagem GLOBAL, carimbada no
    # bloco na hora da publicação: qualquer remoção em QUALQUER filme a move.
    # Regravá-la num filme cujas contagens não mudaram seria diff sem
    # conteúdo — o carimbo só acompanha o corpus quando o PRÓPRIO filme
    # mudou. Mesmo precedente de `aplicar_lei_margem._bloco_novo`, que
    # preserva o `verificador` do artefato.
    if not mencoes and "verificador" in antes and "verificador" in novo:
        novo["verificador"] = antes["verificador"]
    ba, bn = _bullets(antes), _bullets(novo)
    bullets = [f"{e}: {ba.get(e)} -> {bn.get(e)}"
               for e in sorted(set(ba) | set(bn)) if ba.get(e) != bn.get(e)]
    bra, brn = _briefings(doc), _briefings(doc_novo)
    briefings = sorted(k for k in bra if bra[k] != brn[k])
    contraste = [antes.get("contraste"), novo.get("contraste")]
    n = [(antes.get("margem") or {}).get("n"), (novo.get("margem") or {}).get("n")]
    outras = sorted(k for k in set(antes) | set(novo)
                    if k not in ("linhas", "contraste", "margem")
                    and antes.get(k) != novo.get(k))

    mudou = (contraste[0] != contraste[1] or n[0] != n[1]
             or bool(margem) or bool(bullets) or bool(briefings))
    return {"slug": slug, "estado_publicado_mudou": mudou,
            "contraste": contraste, "n": n,
            "celulas_cruzando_margem": margem, "bullets": bullets,
            "briefings_que_mudam": briefings, "mencoes": mencoes,
            "outras_chaves_do_bloco": outras,
            "bloco_identico": antes == novo, "bloco_novo": novo}


def aplicar(slug: str, medida: dict, *, aceitar_mudanca: bool = False) -> None:
    if medida["estado_publicado_mudou"] and not aceitar_mudanca:
        raise SystemExit(
            f"RECUSADO: {slug} muda de estado publicado — "
            f"contraste {medida['contraste']}, n {medida['n']}, "
            f"margem {medida['celulas_cruzando_margem']}, "
            f"bullets {medida['bullets']}, "
            f"briefings {medida['briefings_que_mudam']}. Nada foi gravado.")
    origem = RESULTADO_DIR / f"{slug}.json"
    bruto = origem.read_text(encoding="utf-8")
    doc = json.loads(bruto)
    fora_da_chave = {k: v for k, v in doc.items() if k != CHAVE}
    doc[CHAVE] = medida["bloco_novo"]
    if {k: v for k, v in doc.items() if k != CHAVE} != fora_da_chave:
        raise SystemExit(f"ABORTADO em {slug}: campos fora de `{CHAVE}` mudaram.")
    # O mesmo formato de `render.write_json` — mas preservando o fim de
    # arquivo do original: os JSONs publicados vêm de harnesses diferentes
    # (CLI sem `\n` final, condições com), e trocar o fim de linha seria um
    # diff sem conteúdo em todo filme republicado.
    fim = "\n" if bruto.endswith("\n") else ""
    origem.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + fim,
                      encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--aceitar-mudanca-de-estado", action="store_true",
                    help="grava mesmo se o estado publicado mudar — SÓ com "
                         "aval explícito do dono para este filme")
    args = ap.parse_args()

    medida = medir(args.slug)
    print(json.dumps({k: v for k, v in medida.items() if k != "bloco_novo"},
                     ensure_ascii=False, indent=1))
    if args.aplicar:
        aplicar(args.slug, medida,
                aceitar_mudanca=args.aceitar_mudanca_de_estado)
        print(f"{args.slug}: bloco `eixos` gravado.", file=sys.stderr)


if __name__ == "__main__":
    main()
