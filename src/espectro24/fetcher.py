"""Camada de rede + cache em disco (SPEC §B, §2.1).

- Delay ≥2s entre requisições reais, sem paralelismo (§2).
- Cache por chave em disco: nunca rebusca chave cacheada (§B, critério §5.5).
- 403 / challenge Cloudflare → AntiBotError (o CLI PARA e reporta; §restrições).
"""
from __future__ import annotations

import time
from pathlib import Path

import requests

from .config import DELAY_SECONDS, HEADERS


class AntiBotError(RuntimeError):
    """Bloqueio anti-bot (403 ou challenge). Por decisão do usuário: PARAR."""


class FetchError(RuntimeError):
    pass


class Fetcher:
    def __init__(
        self,
        cache_dir: str | Path,
        delay: float = DELAY_SECONDS,
        session: requests.Session | None = None,
        offline: bool = False,
    ):
        self.cache_dir = Path(cache_dir)
        self.delay = delay
        self.offline = offline
        self._session = session
        self.n_network = 0
        self.n_cache = 0
        # origem por chave de cache: "cache" | "network"
        self.origins: dict[str, str] = {}

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / cache_key

    def get(self, url: str, cache_key: str) -> str:
        """Retorna o HTML de `url`, servindo do cache quando `cache_key` existe."""
        path = self._cache_path(cache_key)
        if path.exists():
            self.n_cache += 1
            self.origins[cache_key] = "cache"
            return path.read_text(encoding="utf-8")

        if self.offline:
            raise FetchError(f"offline e sem cache para {cache_key} ({url})")

        time.sleep(self.delay)
        resp = self.session.get(url, headers=HEADERS, timeout=15)
        self.n_network += 1

        if resp.status_code == 403 or "just a moment" in resp.text.lower() \
                or "cf-challenge" in resp.text.lower():
            raise AntiBotError(
                f"Bloqueio anti-bot em {url} (status {resp.status_code}). "
                "Parando conforme restrição — não escalar sem autorização."
            )
        if resp.status_code != 200:
            raise FetchError(f"{url} -> HTTP {resp.status_code}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(resp.text, encoding="utf-8")
        self.origins[cache_key] = "network"
        return resp.text
