"""Cegueira do dono na Fase 4: nenhum número do TREINADO na tela até o C5 e o C6.

Até as duas avaliações do dono estarem registradas, nada que ele veja mostra
C1–C4, M1, M2, taxa do juiz ou validador do treinado. No lado treinado, o que
os scripts imprimiriam vai, completo, para `finetune/fase4/cego/<log>`; a tela
recebe só o progresso (`curto`). Nos outros lados, nada muda.

    out = Saida(lado, "julgar_treinado.log")
    out(linha_completa, curto="[3/30] filme · 12 min")
    with out.silenciar():          # o stdout de quem é chamado vai para o log
        J.rodar(...)
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone

import comum as K

PASTA = K.FINETUNE_DIR / "fase4" / "cego"
LADO_CEGO = "treinado"


class Saida:
    def __init__(self, lado: str, log: str):
        self.cego = lado == LADO_CEGO
        self.arq = PASTA / log

    def _anexar(self, texto: str) -> None:
        PASTA.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(self.arq, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {texto}\n")

    def __call__(self, completo: str, curto: str | None = None) -> None:
        if not self.cego:
            print(completo, flush=True)
            return
        self._anexar(completo)
        if curto is not None:
            print(curto, flush=True)

    @contextlib.contextmanager
    def silenciar(self):
        if not self.cego:
            yield
            return
        PASTA.mkdir(parents=True, exist_ok=True)
        with open(self.arq, "a", encoding="utf-8") as f, contextlib.redirect_stdout(f):
            yield
