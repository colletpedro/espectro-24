#!/usr/bin/env python3
"""[v1.9.37] PUBLICA o bloco `condicoes` em `resultado/<slug>.json`.

**A diferença para `gerar_condicoes.py`, e ela é o ponto deste arquivo.**
Aquele é o harness de ESTUDO: ele **recusa** `--saida` dentro de
`resultado/`, porque o §0 exige leitura humana de 100% antes de publicar e um
harness capaz de gravar por default tornaria trivial pular essa etapa.

A leitura aconteceu. Este harness publica — então **a trava muda de lugar,
não desaparece**:

  · lá, a trava era o destino (`resultado/` proibido);
  · aqui, a trava é o CONTEÚDO: nenhuma condição é escrita sem passar por
    `condicoes.validar()`, e nenhum bloco é escrito se alguma condição dele
    falhar. O harness **recusa o filme inteiro** e diz qual condição e qual
    flag.

**[piloto de expansão] Texto de AUTORIA HUMANA** (`origem: "leitura_humana"`
na condição) passa só pelos validadores EXATOS; os LÉXICOS viram AVISO,
gravado na própria condição (`avisos`) e impresso. A régua e a razão estão
em `condicoes.FLAGS_LEXICAS`. Texto do modelo continua sob a trava inteira.

**[piloto de expansão] "Sem condição publicável"** (`sem_condicao_publicavel`)
é conferido pela mesma trava: tema do lado certo, regra do conjunto fechado,
motivo curto, par consolidado (`condicoes.inconsistencias_de_recusa`). E
**coluna vazia é BLOQUEIO do filme** — decisão humana, nunca preenchida por
código.

**Isto NÃO é republicar o filme.** Nenhum estágio a montante roda: sem
coleta, sem seleção, sem síntese, sem [D3], sem rotulagem, sem veredito, sem
narrativa, sem TMDB, sem histograma. O harness lê o JSON que já está em
disco, lê o bloco `condicoes` já gerado e conferido, valida, e escreve **uma
única chave**. Travado por `tests/test_publicar_condicoes.py`, com a mesma
técnica que pegou o footgun de republicação: envenenar os pontos de entrada
com `pytest.fail` e rodar de verdade.

**AS CONDIÇÕES DO EIXO `expectativa` NÃO SÃO PUBLICADAS** (§0, pendência
editorial nomeada; R13 do relatório de revisão). A lista é literal aqui, e
não uma regra derivada do eixo, de propósito: é uma decisão editorial sobre
frases específicas, tomada por uma leitura humana, e derivá-la de um eixo
faria o conjunto mudar sozinho quando o catálogo mudasse. **Essa escolha
está sob revisão** (`ABERTO.md`, C14.16): com 300 filmes a lista mantida à
mão diverge em silêncio, e o modo de falha é publicar o que a R13 proíbe.

Uso:
    python scripts/publicar_condicoes.py --de /tmp/cond --todos --dry-run
    python scripts/publicar_condicoes.py --de /tmp/cond --todos
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import condicoes as C  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
CHAVE = "condicoes"

# §0 — as retiradas pela leitura humana (R13). Literal, e o comentário do
# topo diz por que não é derivado do eixo — e que isso está sob revisão.
RETIRADAS = {
    # as seis da FASE 1, catálogo de 35
    ("the-godfather", "NEG-B"),
    ("hereditary", "NEG-B"),
    ("interstellar", "NEG-B"),
    ("longlegs", "NEG-B"),
    ("parasite-2019", "NEG-C"),
    ("everything-everywhere-all-at-once", "NEG-F"),
    # as duas do piloto-18 (C030 e C134 do lote `0ec05ad3e326`)
    ("get-out-2017", "NEG-C"),
    ("whiplash-2014", "NEG-F"),
}


class CondicaoInvalida(Exception):
    """Uma condição que não passa em `validar()`. Reprova o FILME inteiro —
    publicar as boas e calar as ruins deixaria o bloco incompleto sem que
    nada na página dissesse isso."""


def aplicar_retiradas(slug: str, bloco: dict) -> tuple[dict, int]:
    """Tira do bloco as condições retiradas, sem tocar em mais nada."""
    bloco = json.loads(json.dumps(bloco))          # cópia, não muta a origem
    n = 0
    for lado in C.LADOS:
        antes = bloco.get(lado) or []
        depois = [c for c in antes if (slug, c.get("tema_origem")) not in RETIRADAS]
        n += len(antes) - len(depois)
        bloco[lado] = depois
    return bloco, n


def validar_bloco(slug: str, bloco: dict, idx: dict) -> dict[str, list[str]]:
    """A trava de conteúdo. Levanta na primeira condição inválida.

    Devolve os AVISOS por tema (`{tema_origem: [flag léxica]}`) — só existem
    em texto de autoria humana; em texto do modelo a flag léxica é trava.
    """
    avisos: dict[str, list[str]] = {}
    for lado in C.LADOS:
        for c in bloco.get(lado) or []:
            cond = {"lado": lado, "texto": c.get("texto"),
                    "tema_origem": c.get("tema_origem"),
                    "origem": c.get("origem")}
            flags, av = C.validar_com_avisos(cond, idx)
            if flags:
                raise CondicaoInvalida(
                    f"{slug} [{c.get('tema_origem')}] {flags}: "
                    f"{c.get('texto')!r}")
            if av:
                avisos[c.get("tema_origem")] = av
    problemas = C.inconsistencias_de_recusa(bloco, idx)
    if problemas:
        raise CondicaoInvalida(f"{slug}: " + "; ".join(problemas))
    if not any(bloco.get(l) for l in C.LADOS):
        raise CondicaoInvalida(f"{slug}: bloco sem nenhuma condição")
    for lado in C.LADOS:
        if not bloco.get(lado):
            raise CondicaoInvalida(
                f"{slug}: coluna `{lado}` VAZIA — bloqueio do filme, decisão "
                "humana (o código não completa a coluna com outro tema)")
    return avisos


def publicar_um(slug: str, origem: Path, *, dry_run: bool) -> dict:
    alvo = RESULTADO_DIR / f"{slug}.json"
    doc = json.loads(alvo.read_text(encoding="utf-8"))
    bruto = json.loads((origem / f"{slug}.json").read_text(encoding="utf-8"))
    bloco, n_retiradas = aplicar_retiradas(slug, bruto[CHAVE])

    avisos = validar_bloco(slug, bloco, C.indexar(doc))
    # O aviso fica REGISTRADO na condição publicada: é a trilha de que a
    # frase passou por decisão humana contra uma régua léxica.
    for lado in C.LADOS:
        for c in bloco.get(lado) or []:
            if c.get("tema_origem") in avisos:
                c["avisos"] = avisos[c["tema_origem"]]

    n = sum(len(bloco.get(l) or []) for l in C.LADOS)
    if not dry_run:
        # A chave entra no FIM, estatuto aditivo (ficha §3[F], distribuição
        # §3[G]) — a ordem das chaves de topo existentes não se mexe.
        doc[CHAVE] = bloco
        alvo.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return {"slug": slug, "n": n, "retiradas": n_retiradas, "avisos": avisos,
            "sem_condicao": len(bloco.get("sem_condicao_publicavel") or [])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", required=True,
                    help="diretório com os JSONs já gerados e conferidos")
    ap.add_argument("--slug", action="append")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    origem = Path(args.de)
    slugs = args.slug or []
    if args.todos:
        slugs = sorted(f.stem for f in origem.glob("*.json")
                       if f.name != "_resumo.json")
    if not slugs:
        raise SystemExit("nada a fazer: use --todos ou --slug")

    total = retiradas = 0
    for slug in slugs:
        r = publicar_um(slug, origem, dry_run=args.dry_run)
        total += r["n"]
        retiradas += r["retiradas"]
        marca = "  (-%d retirada)" % r["retiradas"] if r["retiradas"] else ""
        if r["sem_condicao"]:
            marca += f"  ({r['sem_condicao']} sem condição publicável)"
        print(f"{slug:40} {r['n']:2} condições{marca}", flush=True)
        for tema, av in sorted(r["avisos"].items()):
            print(f"{'':40}    AVISO léxico, texto humano [{tema}]: {av}")
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}"
          f"{len(slugs)} filmes · {total} condições publicadas · "
          f"{retiradas} retiradas")


if __name__ == "__main__":
    main()
