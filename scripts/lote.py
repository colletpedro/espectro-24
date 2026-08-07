"""[v1.9.3] CLI do harness de lote — SPEC §3[H].

Coleta o bruto (§3[B']) de uma lista de filmes, um por linha, com
checkpoint/resume, validação de slug e falha isolada. Não sintetiza nada.

Uso:
    python scripts/lote.py lista.txt [--dados-dir dados/bruto]
                                     [--estado dados/lote/estado.json]
                                     [--cache-dir resultado/cache]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from espectro24.config import (  # noqa: E402
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    ORCAMENTO_PAGINAS_POR_BUCKET,
    ORDENACAO_DEFAULT,
    ORDENACOES,
)
from espectro24.lote import ler_lista_slugs, rodar_lote  # noqa: E402


def _on_progress(slug, status, motivo):
    marca = {"concluido": "✓", "falhou": "✗", "pulado": "·"}.get(status, "?")
    extra = f" ({motivo})" if motivo else ""
    print(f"[{marca}] {slug}: {status}{extra}", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("lista", help="arquivo de slugs, um por linha (# comenta)")
    p.add_argument("--dados-dir", default=DADOS_BRUTO_DIR)
    p.add_argument("--estado", default="dados/lote/estado.json")
    p.add_argument("--cache-dir", default="resultado/cache")
    p.add_argument("--cota", type=int, default=COTA_POR_BUCKET)
    p.add_argument("--orcamento-paginas", type=int, default=ORCAMENTO_PAGINAS_POR_BUCKET)
    p.add_argument("--ordenacao", choices=sorted(ORDENACOES), default=ORDENACAO_DEFAULT)
    a = p.parse_args(argv)

    slugs = ler_lista_slugs(a.lista)
    print(f"Lote: {len(slugs)} slugs de {a.lista}", file=sys.stderr)

    rel = rodar_lote(
        slugs, cache_dir=a.cache_dir, dados_dir=a.dados_dir, estado_path=a.estado,
        cota_por_bucket=a.cota, orcamento_paginas_bucket=a.orcamento_paginas,
        ordenacao=ORDENACOES[a.ordenacao], on_progress=_on_progress,
    )

    print(f"\nConcluídos: {rel.n_concluidos} · Pulados (resume): {rel.n_pulados} · "
          f"Falhas: {rel.n_falhas}", file=sys.stderr)
    if rel.falhas:
        print("\nFalhas:", file=sys.stderr)
        for slug, motivo in rel.falhas.items():
            print(f"  {slug}: {motivo}", file=sys.stderr)


if __name__ == "__main__":
    main()
