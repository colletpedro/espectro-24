"""Roda a PROSA (síntese, rotulagem, narrativa, veredito, condições) com o
provider `local` (Ollama) sobre filmes JÁ PUBLICADOS — para a comparação cega.

Exceção escopada (`espectro24.prosa_local`): não toca `PROVIDER_POR_ESTAGIO`,
não escreve em `resultado/`, recusa o lote C22 e filme não publicado. Custo
zero. Retoma: filme com `<slug>.json` já na saída é pulado.

Uso (PowerShell, no Windows; ver docs/SETUP_WINDOWS.md §9):
    $env:ESPECTRO24_OLLAMA_THINK = "low"
    python scripts/gerar_prosa_local.py --modelo gpt-oss:20b `
        --saida prosa-local --slug anatomy-of-a-fall --slug mother-2017 `
        --slug napoleon-2023 --slug the-substance --slug incendies

`--filmes-padrao` usa os 5 filmes da comparação (`FILMES_COMPARACAO`).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import local_ollama, prosa_local  # noqa: E402

# Perfis diferentes (arthouse, divisivo, invertido, aclamado x2), contraste
# TEMÁTICO em dois, VALORATIVO em três, e os cinco com condições publicadas.
# Entre os publicados completos (os 4 blocos de prosa), nenhum é `obscuro`.
# `mother-2017` e não `500-days-of-summer`: mesmo perfil, 1/3 do texto de
# síntese (menos tempo de CPU).
FILMES_COMPARACAO = ("anatomy-of-a-fall", "mother-2017", "napoleon-2023",
                     "the-substance", "incendies")


def _exigir_modelo(modelo: str) -> None:
    try:
        nomes = local_ollama.modelos_instalados()
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"Ollama inacessível em {local_ollama.url_base()} "
                         f"({type(e).__name__}: {e})")
    if modelo not in nomes and (modelo + ":latest") not in nomes:
        raise SystemExit(f"modelo {modelo!r} não está no Ollama. "
                         f"Instalados: {nomes}. Rode `ollama pull {modelo}`")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--modelo", required=True, help="ex.: gpt-oss:20b")
    ap.add_argument("--saida", required=True, type=Path,
                    help="diretório de saída (NUNCA dentro de resultado/)")
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--filmes-padrao", action="store_true")
    ap.add_argument("--n", type=int, default=None,
                    help="best-of-N (padrão: config.BEST_OF_N, como em produção)")
    a = ap.parse_args()

    slugs = list(a.slug) + (list(FILMES_COMPARACAO) if a.filmes_padrao else [])
    if not slugs:
        raise SystemExit("nada a fazer: use --slug X ou --filmes-padrao")
    local_ollama.nivel_think()  # ValueError cedo se ESPECTRO24_OLLAMA_THINK for inválido
    for s in slugs:
        try:
            prosa_local.exigir_escopo(s, a.saida)
        except prosa_local.ForaDoEscopo as e:
            raise SystemExit(f"RECUSADO: {e}")
    _exigir_modelo(a.modelo)

    import gerar_veredito as GV
    snapshot = GV.snapshot_de_aberturas()
    a.saida.mkdir(parents=True, exist_ok=True)
    t_total = time.time()
    for s in slugs:
        if (a.saida / f"{s}.json").exists():
            print(f"[·] {s}: já gerado, pulando", flush=True)
            continue
        print(f"[…] {s}", flush=True)
        tele = prosa_local.regenerar_filme(
            s, modelo=a.modelo, saida=a.saida, n=a.n,
            aberturas=GV.historico_para(snapshot, s))
        n_chamadas = sum(r["n_chamadas"] for r in tele["estagios"].values())
        print(f"[✓] {s}: {n_chamadas} chamadas · {tele['elapsed_s']:.0f}s · "
              f"falhas={tele['falhas'] or 'nenhuma'} · "
              f"seleção reproduz={tele['selecao_reproduz_publicada']}", flush=True)
    print(f"\n{len(slugs)} filme(s) em {time.time() - t_total:.0f}s -> {a.saida}")


if __name__ == "__main__":
    main()
