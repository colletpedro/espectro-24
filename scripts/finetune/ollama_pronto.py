"""Sobe (opcional) e confere o Ollama SEM o CLI interativo (2026-11-03).

O `gerar_sintese_teste.py gerar` derruba o Ollama ao terminar (`matar_ollama`),
e o juiz (`avaliar_c1_c4.py medir-contexto` / `julgar`) exige o servidor no ar
com o modelo. `ollama list` / `ollama ps` digitados no PowerShell travaram o
terminal duas vezes no fim de um bloco; aqui tudo é HTTP com timeout.

- `--subir`: derruba o que houver (`viabilidade_ollama.matar_ollama`) e sobe
  `ollama serve` DESACOPLADO do terminal (sem herdar o console; no Windows,
  `DETACHED_PROCESS`), com `OLLAMA_NUM_PARALLEL=1` e `127.0.0.1:11434`, as
  mesmas variáveis do `viabilidade_ollama.subir_ollama`;
- espera até `--espera-s` por `/api/tags` (cada chamada com timeout) e confere
  se `--modelo` está instalado. Saída 0 = pronto; 1 = não.

Uso: `ollama_pronto.py [--subir] --modelo gpt-oss:20b`
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  (só loopback)

URL = "http://127.0.0.1:11434"


def modelo_presente(nomes: list[str], modelo: str) -> bool:
    return modelo in nomes or f"{modelo}:latest" in nomes


def subir_desacoplado() -> int:
    env = {**os.environ, "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_HOST": "127.0.0.1:11434"}
    kw: dict = {"env": env, "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    return subprocess.Popen(["ollama", "serve"], **kw).pid


def modelos(timeout_s: float) -> list[str] | None:
    import requests
    try:
        r = requests.get(f"{URL}/api/tags", timeout=(3, timeout_s))
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except (requests.RequestException, ValueError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--subir", action="store_true")
    ap.add_argument("--espera-s", type=float, default=90.0)
    a = ap.parse_args()
    out: dict = {"modelo": a.modelo}
    if a.subir:
        import viabilidade_ollama as V
        V.matar_ollama()
        out["pid_serve"] = subir_desacoplado()
    t0, nomes = time.time(), None
    while time.time() - t0 < a.espera_s:
        nomes = modelos(timeout_s=10)
        if nomes is not None:
            break
        time.sleep(2)
    out.update({"responde": nomes is not None, "espera_s": round(time.time() - t0, 1),
                "instalado": nomes is not None and modelo_presente(nomes, a.modelo)})
    print(json.dumps(out, ensure_ascii=False))
    if not out["instalado"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
