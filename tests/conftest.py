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
