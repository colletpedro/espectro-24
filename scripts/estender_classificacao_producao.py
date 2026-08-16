"""[v1.9.15, Entrega 1] Estende a classificação para cobrir a seleção de
PRODUÇÃO inteira, nos filmes indicados.

Fecha o achado da v1.9.14 (§[D3], "Duas populações de 40"): a amostra
CLASSIFICADA (`resultado/votacao-3/amostra.json`, montada sem
`orcamento_paginas_por_nivel`) e a amostra ANALISADA (a que a síntese de
produção de fato lê, via `orcamento_paginas_por_nivel`) são seleções
diferentes do mesmo bucket. Este script não reclassifica nada — acha, por
bucket, as reviews da seleção de produção que ainda faltam à classificação
(`uniao_amostra.reviews_faltantes`), soma-as a `amostra.json` (mesmo
`taxonomia_id`, mesmo formato) e roda as MESMAS três passadas de
`votacao_3.py` só sobre elas.

Uso:
    python scripts/estender_classificacao_producao.py --slug cure \\
        --slug cidade-de-deus --slug the-invite-2026 [--dry-run]

Sem `--slug`, usa o catálogo publicado (`CATALOGO`). `--dry-run` reporta o
que seria classificado sem gastar nenhuma chamada.

Depois de rodar, `python scripts/votacao_3.py consenso` precisa ser chamado
para que `resultado/votacao-3/consenso.jsonl` incorpore as novas linhas —
este script já faz isso ao final, a menos que `--sem-consenso` seja passado.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import perfil_de, taxonomia_id  # noqa: E402
from espectro24.bruto import carregar  # noqa: E402
from espectro24 import eixos as E  # noqa: E402
from espectro24.pipeline import amostra_do_bruto  # noqa: E402
from espectro24.uniao_amostra import reviews_faltantes  # noqa: E402
from votacao_3 import (  # noqa: E402
    ARQ_AMOSTRA,
    ARQ_CONSENSO,
    ARQ_PASSE,
    classificar_passe,
    cmd_consenso,
)

CATALOGO = ["cure", "cidade-de-deus", "the-invite-2026"]
RAIZ_BRUTO = RAIZ / "dados" / "bruto"


def _faltantes_por_slug(slugs: list[str]) -> dict[str, dict[str, list]]:
    """`{slug: {bucket: [ReviewBruta]}}` — o que falta classificar."""
    cat = {}
    consenso_path = RAIZ / E.CONSENSO_PADRAO
    if consenso_path.exists():
        cat = E.carregar_classificacao(consenso_path)

    fora = {}
    for slug in slugs:
        json_path = RAIZ / "resultado" / f"{slug}.json"
        coleta = None
        if json_path.exists():
            coleta = json.loads(json_path.read_text(encoding="utf-8")).get("coleta")
        producao = amostra_do_bruto(slug, coleta=coleta, raiz=str(RAIZ_BRUTO))
        classificadas = {b: set(reviews) for b, reviews in cat.get(slug, {}).items()}
        fora[slug] = reviews_faltantes(producao, classificadas)
    return fora


def _perfil_de_slug(slug: str) -> str:
    meta, _ = carregar(slug, raiz=str(RAIZ_BRUTO))
    hist = {float(k): v for k, v in (meta.get("histograma_bruto") or {}).items()}
    return perfil_de(slug, hist) if hist else "?"


def _acrescentar_a_amostra(faltantes: dict[str, dict[str, list]]) -> int:
    """Soma as reviews faltantes ao `amostra.json` de `votacao_3.py`, no
    MESMO formato que ele já usa. Devolve quantas linhas foram acrescentadas
    (0 se já estavam todas lá, execução idempotente)."""
    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    tid_atual = taxonomia_id()
    if amostra["taxonomia_id"] != tid_atual:
        raise SystemExit(
            f"amostra.json sob taxonomia {amostra['taxonomia_id']!r}, "
            f"prompt atual é {tid_atual!r} — não é seguro estender.")

    ja = {(r["slug"], r["bucket"], r["id"]) for r in amostra["reviews"]}
    perfis = {}
    n_novas = 0
    for slug, por_bucket in faltantes.items():
        if slug not in perfis:
            perfis[slug] = _perfil_de_slug(slug)
        for bucket, reviews in por_bucket.items():
            for r in reviews:
                chave = (slug, bucket, r.id)
                if chave in ja:
                    continue
                amostra["reviews"].append({
                    "slug": slug, "perfil": perfis[slug], "bucket": bucket,
                    "id": r.id, "nivel": r.nivel, "n_chars": r.n_chars,
                    "texto": r.texto,
                })
                ja.add(chave)
                n_novas += 1

    if n_novas:
        ARQ_AMOSTRA.write_text(json.dumps(amostra, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    return n_novas


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slug", action="append",
                   help="slug a estender (repetível); default: os 3 publicados")
    p.add_argument("--dry-run", action="store_true",
                   help="só reporta o que falta, não gasta chamada nenhuma")
    p.add_argument("--sem-consenso", action="store_true",
                   help="não roda `votacao_3.py consenso` ao final")
    args = p.parse_args()

    slugs = args.slug or CATALOGO
    faltantes = _faltantes_por_slug(slugs)

    total = 0
    for slug, por_bucket in faltantes.items():
        n_slug = sum(len(v) for v in por_bucket.values())
        total += n_slug
        print(f"  {slug}: " + ", ".join(f"{b}={len(v)}"
                                        for b, v in por_bucket.items())
              + f" = {n_slug}")
    print(f"\nTotal faltante: {total} reviews -> {total * 3} chamadas "
          f"(votação de 3)")

    if args.dry_run or total == 0:
        if total == 0:
            print("Nada a classificar — a amostra já cobre a produção.")
        return

    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    n_novas = _acrescentar_a_amostra(faltantes)
    print(f"\n{n_novas} linhas novas acrescentadas a "
          f"{ARQ_AMOSTRA.relative_to(RAIZ)}")

    for n_passe in (1, 2, 3):
        print(f"\n--- passe {n_passe} ---")
        classificar_passe(n_passe)

    if not args.sem_consenso:
        print("\n--- consenso ---")
        cmd_consenso()


if __name__ == "__main__":
    main()
