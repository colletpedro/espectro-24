"""Arquiva os passes DeepSeek dos 55 da exceção C22 (2026-09-22).

Os 55 do lote noturno de 18/09 têm os passes 1 e 2 completos e o passe 3 em
38% em DeepSeek, pagos (~US$1,75, ABERTO.md C19). A decisão do dono é refazer
os TRÊS passes em Gemini — um provider por filme. Os registros DeepSeek não
podem ficar em `passe_*.jsonl`: `_ler_passe` os leria como votos, e a exceção
recusa rodar enquanto eles estiverem lá (`votacao_3.exigir_sem_votos_de_fora`).
Também não são apagados: foram pagos, e são a única classificação V4.1-Flash
com `ts` desses filmes.

O que faz, por arquivo `passe_{1,2,3,4}.jsonl`: move as LINHAS (bytes
originais, sem re-serializar) dos 55 sem a marca `excecao` para
`resultado/votacao-3/_arquivo_deepseek_c22/passe_N.jsonl`, e reescreve o
arquivo de produção só com as demais, na ordem original. Antes de gravar,
confere que as linhas que ficam são byte a byte as linhas de fora dos 55 —
o sha256 do conjunto é impresso antes e depois. Atômico por arquivo.

Por padrão SIMULA (conta e mostra os hashes). `--executar` grava.
Idempotente: rodar de novo não acha mais nada a mover.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import excecao_gemini_c22 as C22  # noqa: E402
from espectro24.atomico import escrever_atomico  # noqa: E402

VOTACAO = RAIZ / "resultado" / "votacao-3"
ARQUIVO = VOTACAO / "_arquivo_deepseek_c22"

MOTIVO = """# Passes DeepSeek arquivados — exceção C22 (2026-09-22)

Registros de classificação DeepSeek (`deepseek-v4-flash`, roteado para o
V4.1-Flash) dos 55 filmes do lote noturno de 2026-09-18
(`dados/lote/lista-noturno-2026-09-18.txt`): passes 1 e 2 completos, passe 3
em 38% quando o saldo DeepSeek acabou. Pagos (~US$1,75, ABERTO.md C19).

**Por que saíram de `passe_*.jsonl`:** o dono decidiu não recarregar o
DeepSeek e refazer os TRÊS passes destes 55 em Gemini (ABERTO.md C22). Não
completar o passe 3 em Gemini sobre os passes 1-2 DeepSeek: a votação de 3
pressupõe três sorteios do MESMO modelo, e misturar provider dentro do voto
quebra a premissa sem volta. Um provider por filme.

**Por que não foram apagados:** foram pagos, e são a única classificação
V4.1-Flash com `ts` destes filmes — servem para recoletar em DeepSeek no
futuro (reaproveitando os passes 1-2) ou para comparar os dois provedores
sobre o mesmo volume.

Linhas copiadas com os bytes originais, na ordem original.
Script: `scripts/arquivar_passes_c22.py`.
"""


def _sha(linhas: list[str]) -> str:
    return hashlib.sha256("".join(linhas).encode("utf-8")).hexdigest()[:16]


def separar(texto: str) -> tuple[list[str], list[str]]:
    """`(ficam, saem)`, cada uma com as linhas ORIGINAIS (com `\\n`)."""
    ficam, saem = [], []
    for linha in texto.splitlines(keepends=True):
        if not linha.strip():
            ficam.append(linha)
            continue
        r = json.loads(linha)
        if r.get("slug") in C22.SLUGS and r.get("excecao") != C22.EXCECAO:
            saem.append(linha)
        else:
            ficam.append(linha)
    return ficam, saem


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--executar", action="store_true")
    a = ap.parse_args(argv)
    total = 0
    for n in (1, 2, 3, 4):
        arq = VOTACAO / f"passe_{n}.jsonl"
        if not arq.exists():
            continue
        texto = arq.read_text(encoding="utf-8")
        ficam, saem = separar(texto)
        fora_dos_55 = [l for l in texto.splitlines(keepends=True)
                       if l.strip() and json.loads(l).get("slug") not in C22.SLUGS]
        assert [l for l in ficam if l.strip()
                and json.loads(l).get("slug") not in C22.SLUGS] == fora_dos_55
        print(f"passe_{n}.jsonl: {len(saem)} linha(s) dos 55 a arquivar · "
              f"{len(fora_dos_55)} de fora dos 55, sha256 {_sha(fora_dos_55)}")
        total += len(saem)
        if not (a.executar and saem):
            continue
        ARQUIVO.mkdir(parents=True, exist_ok=True)
        destino = ARQUIVO / f"passe_{n}.jsonl"
        anterior = destino.read_text(encoding="utf-8") if destino.exists() else ""
        escrever_atomico(destino, anterior + "".join(saem))
        escrever_atomico(arq, "".join(ficam))
        depois = [l for l in arq.read_text(encoding="utf-8").splitlines(keepends=True)
                  if l.strip() and json.loads(l).get("slug") not in C22.SLUGS]
        assert _sha(depois) == _sha(fora_dos_55)
        print(f"  → arquivadas em {destino.relative_to(RAIZ)}; de fora dos 55 "
              f"depois: sha256 {_sha(depois)} (idêntico)")
    if a.executar and total:
        (ARQUIVO / "MOTIVO.md").write_text(MOTIVO, encoding="utf-8")
    print(f"{'ARQUIVADAS' if a.executar else 'SIMULAÇÃO — a arquivar'}: {total} linha(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
