"""Guarda de LATÊNCIA para os scripts que chamam o juiz (gpt-oss:20b no Ollama).

Substitui a guarda de RAM livre: com o gpt-oss:20b carregado a RAM livre fica
perto de 0,3 GB por construção (MEDIDO na limpeza de 20–21/10: 1.863 chamadas
a 14,7 s de mediana, sem paginação), então "RAM livre baixa" não distingue o
normal do problema. O sintoma de paginação é outro: a chamada demora muito
mais que as vizinhas.

Regra (do dono): pausa e avisa se UMA chamada passar de `fator` (4×) a mediana
das últimas `janela` (20) chamadas. A chamada lenta termina e é gravada pelo
chamador (nada se perde); a PRÓXIMA não sai: levanta `LatenciaAnomala`, que é
`BaseException` de propósito — o `J.rodar` do juiz captura `Exception` e
registraria a pausa como falha de par.

Detalhes que mudam o resultado:
- só vale com `minimo` (10) chamadas na janela (antes disso não há mediana);
- a chamada anômala NÃO entra na janela (uma fase lenta não vira o "normal");
- `ignorar_proxima()` — depois de reiniciar o Ollama a 1ª chamada paga a
  carga do modelo (~24 s): ela não é medida nem entra na janela.
"""
from __future__ import annotations

import collections
import statistics
import time


class LatenciaAnomala(BaseException):
    def __init__(self, latencia_s: float, mediana_s: float, fator: float, n_janela: int):
        self.latencia_s, self.mediana_s, self.fator, self.n_janela = (
            latencia_s, mediana_s, fator, n_janela)
        super().__init__(
            f"chamada de {latencia_s:.1f} s > {fator:g}× a mediana de {mediana_s:.1f} s "
            f"das últimas {n_janela} chamadas")


class GuardaDeLatencia:
    def __init__(self, janela: int = 20, fator: float = 4.0, minimo: int = 10):
        self.janela, self.fator, self.minimo = janela, fator, minimo
        self.recentes: collections.deque[float] = collections.deque(maxlen=janela)
        self.pendente: LatenciaAnomala | None = None
        self._pular = False

    def mediana(self) -> float | None:
        return statistics.median(self.recentes) if len(self.recentes) >= self.minimo else None

    def ignorar_proxima(self) -> None:
        self._pular = True

    def registrar(self, latencia_s: float) -> None:
        """Mede UMA chamada concluída; marca a pausa se ela for anômala."""
        if self._pular:
            self._pular = False
            return
        med = self.mediana()
        if med is not None and latencia_s > self.fator * med:
            self.pendente = LatenciaAnomala(latencia_s, med, self.fator, len(self.recentes))
            return
        self.recentes.append(latencia_s)

    def envolver(self, chamar):
        """`chamar(system, user) -> dict` com a guarda. Uma chamada que levanta
        também é medida (rede pendurada é o caso que mais interessa)."""
        def com_guarda(*args, **kw):
            if self.pendente is not None:
                raise self.pendente
            t0 = time.monotonic()
            try:
                return chamar(*args, **kw)
            finally:
                self.registrar(time.monotonic() - t0)
        return com_guarda
