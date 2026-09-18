"""Escrita atômica: gravar em temporário e renomear.

`open(path, "w")` trunca o arquivo ANTES de escrever. Uma queda no meio deixa o
arquivo pela metade — e `consenso.jsonl`/`consenso_verificado.jsonl` são lidos
por `pipeline.montar_eixos` para os filmes publicados. `os.replace` é atômico
no mesmo filesystem: quem lê vê o arquivo antigo INTEIRO ou o novo INTEIRO.
O temporário fica no MESMO diretório do destino justamente por isso.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def escrever_atomico(destino: str | Path, conteudo: str,
                     encoding: str = "utf-8") -> None:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # `mkstemp` cria 0600; o destino existente mantém o modo que tinha.
    try:
        modo = destino.stat().st_mode & 0o777
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        modo = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=destino.parent,
                               prefix=f".{destino.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(conteudo)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, modo)
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
