#!/usr/bin/env python3
"""[v1.9.21, §3[V]] Regera o VEREDITO sobre `resultado/*.json` já publicados.

**Isto NÃO é republicar o filme.** Nenhum estágio a montante roda: sem
coleta, sem seleção, sem síntese, sem [D3], sem narrativa, sem TMDB, sem
histograma. O harness lê o JSON que já está em disco, monta o briefing do
veredito (código puro), chama o LLM pelo adaptador, e grava **uma única
chave**: `veredito`.

**Por que harness PRÓPRIO, e não `publicar_catalogo.py`.** Aquele script tem
o checkpoint por `spec_version` e a guarda de lote da v1.9.21 — os dois
existem porque republicar faz REDE e é caro. Regerar veredito não faz nada
disso, então herdar a guarda seria cerimônia sem risco. A contrapartida é a
lição do próprio footgun que a v1.9.21 fechou: *harness novo com "cuidado
diferente" é exatamente como se abre o próximo*. O risco aqui é menor —
sobrescrever 35 JSONs — e não é zero. Por isso o escopo deste arquivo é
travado por TESTE, não por disciplina:

  - `tests/test_gerar_veredito.py` substitui os pontos de entrada de coleta,
    seleção, síntese, [D3] e narrativa por `pytest.fail` e roda o harness;
  - o mesmo arquivo prova que nenhuma chamada de rede sai daqui fora do
    adaptador de LLM;
  - e compara o JSON campo a campo antes/depois, exigindo que só `veredito`
    mude.

Uso:
    python scripts/gerar_veredito.py --slug the-godfather
    python scripts/gerar_veredito.py --todos
    python scripts/gerar_veredito.py --todos --modelo gemini-3.7-flash \\
        --saida resultado/veredito-ab/flash --so-veredito
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24 import veredito as V  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"

# A ÚNICA chave que este harness escreve. Literal, e conferida contra o
# documento antes de gravar: se o estágio um dia passar a mexer em outra
# coisa, o teste de campo a campo quebra, e este nome é onde o leitor
# descobre qual era o contrato.
CHAVE = "veredito"


def slugs_publicados() -> list[str]:
    """Todo `resultado/<slug>.json` com bloco `eixos` — a população sobre a
    qual o estágio [V] tem o que dizer. Filme sem `eixos` é pulado, não é
    erro (mesma política aditiva de ficha e distribuição)."""
    saida = []
    for caminho in sorted(RESULTADO_DIR.glob("*.json")):
        try:
            d = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if (d.get("eixos") or {}).get("linhas"):
            saida.append(caminho.stem)
    return saida


def _campos_fora_da_chave(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != CHAVE}


def gerar_um(slug: str, *, modelo: str | None = None,
             provider: str | None = None, saida: Path | None = None,
             so_veredito: bool = False) -> dict:
    """Regera o veredito de UM filme e grava. Devolve a telemetria.

    `saida` grava noutro diretório (é o que o A/B de modelo usa, para os dois
    braços não sobrescreverem um ao outro). `so_veredito` grava um documento
    contendo apenas slug + o bloco — para comparação, nunca para publicar.
    """
    origem = RESULTADO_DIR / f"{slug}.json"
    documento = json.loads(origem.read_text(encoding="utf-8"))
    antes = _campos_fora_da_chave(documento)

    t0 = time.time()
    bloco = V.gerar(documento, model=modelo, provider=provider)
    if bloco is None:
        return {"slug": slug, "ok": False, "motivo": "sem_bloco_eixos"}

    documento[CHAVE] = bloco

    # A guarda que o teste de campo a campo trava, aqui também em produção:
    # nada além da chave pode ter mudado.
    depois = _campos_fora_da_chave(documento)
    if depois != antes:
        divergentes = sorted(k for k in set(antes) | set(depois)
                             if antes.get(k) != depois.get(k))
        raise SystemExit(
            f"ABORTADO em {slug}: o estágio de veredito alterou campos fora "
            f"de `{CHAVE}`: {divergentes}. Nada foi gravado.")

    destino_dir = Path(saida) if saida else RESULTADO_DIR
    destino_dir.mkdir(parents=True, exist_ok=True)
    a_gravar = ({"slug": slug, CHAVE: bloco} if so_veredito else documento)
    (destino_dir / f"{slug}.json").write_text(
        json.dumps(a_gravar, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"slug": slug, "ok": True, "origem": bloco["origem"],
            "modelo": bloco["modelo"], "flags": bloco["flags"],
            "motivo": bloco["motivo"], "n_palavras": len(bloco["texto"].split()),
            "texto": bloco["texto"], "elapsed_s": round(time.time() - t0, 1)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", action="append", help="slug (repetível)")
    ap.add_argument("--todos", action="store_true",
                    help="todos os filmes com bloco `eixos`")
    ap.add_argument("--modelo", help="override do modelo (default: "
                                     "MODELO_POR_ESTAGIO['veredito'])")
    ap.add_argument("--provider", help="override do provider")
    ap.add_argument("--saida", help="diretório alternativo (A/B de modelo)")
    ap.add_argument("--so-veredito", action="store_true",
                    help="grava só slug + bloco (comparação, não publicação)")
    ap.add_argument("--log", help="jsonl com a telemetria de cada filme")
    args = ap.parse_args()

    load_dotenv(RAIZ / ".env")
    slugs = args.slug or (slugs_publicados() if args.todos else [])
    if not slugs:
        raise SystemExit("nada a fazer: use --slug X ou --todos.")

    log = Path(args.log) if args.log else None
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)

    n_llm = n_fallback = 0
    for slug in slugs:
        r = gerar_um(slug, modelo=args.modelo, provider=args.provider,
                     saida=Path(args.saida) if args.saida else None,
                     so_veredito=args.so_veredito)
        if log:
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if not r["ok"]:
            print(f"  [·] {slug}: {r['motivo']}")
            continue
        marca = "✓" if r["origem"] == "llm" else "!"
        n_llm += r["origem"] == "llm"
        n_fallback += r["origem"] == "template_fallback"
        print(f"  [{marca}] {slug}: {r['texto']}")
        if r["flags"]:
            print(f"        flags: {', '.join(r['flags'])}")

    print(f"\n{n_llm} por LLM · {n_fallback} em template_fallback")


if __name__ == "__main__":
    main()
