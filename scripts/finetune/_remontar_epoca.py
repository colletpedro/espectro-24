"""Remonta os prompts da síntese com o CÓDIGO DE UMA ÉPOCA (subprocesso).

Chamado por `reconstruir_sintese.py` com `PYTHONPATH` apontando para o `src/`
exportado de um commit antigo (`git archive`). Usa só o que existia no pacote
naquele commit: `bruto.carregar`, `selecao.selecionar`, `pipeline.montar_buckets`,
`synthesize.build_system_prompt` / `build_user_message`. Os parâmetros de
`selecionar` são os que a assinatura daquele commit aceita (o `excluir_ids` das
recusas só existe desde 2026-10-08 e é vazio para os publicados).

Entrada: `--src`, `--bruto`, `--coletas` (JSON {slug: coleta}). Saída (stdout):
JSON {slug: {bucket: {"system_sha256", "user_sha256", "n"}}}.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  — nenhuma rede, nenhuma chave


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--bruto", required=True)
    ap.add_argument("--coletas", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.src)
    import espectro24
    from espectro24.bruto import carregar
    from espectro24.config import COTA_POR_BUCKET
    from espectro24.pipeline import montar_buckets
    from espectro24.selecao import selecionar
    from espectro24.synthesize import build_system_prompt, build_user_message

    origem = Path(espectro24.__file__).resolve()
    if Path(a.src).resolve() not in origem.parents:
        raise SystemExit(f"espectro24 veio de {origem}, não de {a.src}")
    aceitos = set(inspect.signature(selecionar).parameters)
    fora = {}
    for slug, coleta in json.loads(Path(a.coletas).read_text(encoding="utf-8")).items():
        _, todas = carregar(slug, raiz=a.bruto)
        hist = {float(k): v for k, v in (coleta.get("histograma_bruto") or {}).items()}
        kw = {"cota_por_bucket": COTA_POR_BUCKET}
        if "orcamento_paginas_por_nivel" in aceitos:
            kw["orcamento_paginas_por_nivel"] = {
                float(k): v for k, v in (coleta.get("orcamento_paginas_por_nivel") or {}).items()}
        sel = selecionar(todas, hist or None, **kw)
        fora[slug] = {}
        for b in montar_buckets(sel, None):
            s, u = build_system_prompt(b.nome), build_user_message(b)
            fora[slug][b.nome] = {
                "system_sha256": hashlib.sha256(s.encode()).hexdigest(),
                "user_sha256": hashlib.sha256(u.encode()).hexdigest(),
                "n": len(b.reviews_analisadas)}
    json.dump(fora, sys.stdout)


if __name__ == "__main__":
    main()
