"""Configuração de testes — tudo roda contra fixtures/, ZERO rede."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FIXTURES = ROOT / "fixtures"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def fx(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def histograma_de_contagens(**por_bucket: int) -> dict[float, int]:
    """[v1.9.0] Histograma sintético com contagens conhecidas por BUCKET.

    Espalha a contagem de cada bucket pelos níveis daquele bucket **sob as
    fronteiras em vigor** (`buckets.mapa_de_niveis`).

    Existe para desacoplar os testes de NARRADOR/EDITOR das fronteiras: eles
    não têm opinião nenhuma sobre onde fica o corte entre `negativas` e
    `medianas` — só precisam de um `output` cujos `share_real` sejam números
    conhecidos, para conferir rótulo de peso, marcação de perspectiva e
    ancoragem. Montar esses fixtures a partir do histograma REAL do `cure`
    (como era até a v1.8.2) acoplava dezenas de asserções de prosa à opção C,
    e qualquer mudança de fronteira quebrava testes que não falam de
    fronteira.

    Ex.: `histograma_de_contagens(negativas=345, medianas=1725, positivas=7930)`
    → shares 3/17/79 sob qualquer configuração de fronteira.
    """
    from espectro24.buckets import NIVEIS, mapa_de_niveis

    mapa = mapa_de_niveis()
    h: dict[float, int] = {n: 0 for n in NIVEIS}
    for nome, total in por_bucket.items():
        niveis = mapa[nome]
        base, resto = divmod(total, len(niveis))
        for i, n in enumerate(niveis):
            h[n] = base + (1 if i < resto else 0)
    return h


# Contagens que produzem os shares 3/17/79 do `cure` — os números com que a
# maior parte das asserções de prosa (rótulo de peso "~79%", marcação
# "antecipada" para 3%) foi escrita ao longo das versões v1.4.0–v1.8.2.
CONTAGENS_3_17_79 = {"negativas": 345, "medianas": 1725, "positivas": 7930}


class FakeFetcher:
    """Fetcher de mentira para testar collector/fulltext sem tocar a rede.

    `responses` mapeia cache_key -> html. Chaves ausentes retornam HTML vazio
    (0 reviews → sinal de fim de paginação). Registra as chamadas.
    """

    def __init__(self, responses: dict[str, str] | None = None,
                 raise_on: set[str] | None = None):
        self.responses = responses or {}
        self.raise_on = raise_on or set()
        self.calls: list[tuple[str, str]] = []
        self.n_network = 0
        self.n_cache = 0
        self.origins: dict[str, str] = {}

    def get(self, url: str, cache_key: str) -> str:
        self.calls.append((url, cache_key))
        if cache_key in self.raise_on:
            from espectro24.fetcher import FetchError
            raise FetchError(f"forced failure for {cache_key}")
        self.n_network += 1
        self.origins[cache_key] = "network"
        return self.responses.get(cache_key, "<html><body></body></html>")


class FakeSession:
    """Session de mentira para testar o cache do Fetcher real."""

    def __init__(self, text: str, status: int = 200):
        self._text = text
        self._status = status
        self.n_calls = 0

    def get(self, url, headers=None, timeout=None):
        self.n_calls += 1
        return SimpleNamespace(status_code=self._status, text=self._text)
