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
from comum import ARQUIVOS_TOKENIZER, CANDIDATOS, TOKENIZERS_DIR_PADRAO, pasta_do_candidato  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", type=Path, default=TOKENIZERS_DIR_PADRAO)
    a = ap.parse_args()
    for nome, c in CANDIDATOS.items():
        pasta = pasta_do_candidato(a.destino, nome)
        pasta.mkdir(parents=True, exist_ok=True)
        for arq in ARQUIVOS_TOKENIZER:
            url = f"https://huggingface.co/{c['repo']}/resolve/{c['revisao']}/{arq}"
            dados = urllib.request.urlopen(url, timeout=120).read()
            (pasta / arq).write_bytes(dados)
            print(f"{nome:12s} {arq:24s} {hashlib.sha256(dados).hexdigest()}")


if __name__ == "__main__":
    main()
