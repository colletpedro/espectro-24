"""Baixa SÓ os arquivos de tokenizer dos candidatos (nenhum peso), na revisão
fixada em `comum.CANDIDATOS`, e imprime o sha256 de cada arquivo.

Rede: só huggingface.co (não usa `_guarda`, que bloqueia rede; não lê chave
nenhuma). Os repositórios são públicos (Apache 2.0, sem gate em 2026-10-20).

    python scripts/finetune/baixar_tokenizers.py --destino ~/.cache/espectro24-finetune/tokenizers
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (ARQUIVOS_TOKENIZER, CANDIDATOS, CANDIDATOS_EXTRA,  # noqa: E402
                   TOKENIZERS_DIR_PADRAO, pasta_do_candidato)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", type=Path, default=TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--candidato", action="append", choices=[*CANDIDATOS, *CANDIDATOS_EXTRA],
                    help="só este(s); sem a opção, os de CANDIDATOS (fase 0)")
    a = ap.parse_args()
    todos = {**CANDIDATOS, **CANDIDATOS_EXTRA}
    escolhidos = a.candidato or list(CANDIDATOS)
    for nome in escolhidos:
        c = todos[nome]
        pasta = pasta_do_candidato(a.destino, nome)
        pasta.mkdir(parents=True, exist_ok=True)
        for arq in ARQUIVOS_TOKENIZER:
            url = f"https://huggingface.co/{c['repo']}/resolve/{c['revisao']}/{arq}"
            dados = urllib.request.urlopen(url, timeout=120).read()
            (pasta / arq).write_bytes(dados)
            print(f"{nome:12s} {arq:24s} {hashlib.sha256(dados).hexdigest()}")


if __name__ == "__main__":
    main()
