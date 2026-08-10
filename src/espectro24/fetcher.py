"""Camada de rede + cache em disco (SPEC §B, §2.1, §2.4).

- Delay ≥2s entre requisições reais, sem paralelismo (§2).
- Cache por chave em disco: nunca rebusca chave cacheada (§B, critério §5.5).
- 403 / challenge Cloudflare → AntiBotError (o CLI PARA e reporta; §restrições).
- **v1.9.6 (§2.4): retentativa para erro de TRANSPORTE, e só para ele.**
  Bloqueio (403/challenge) e sobrecarga repetida (2º 503 do lote) continuam
  parando na hora — retentar bloqueio é evasão, e a spec proíbe.
"""
from __future__ import annotations

import random
import time
from pathlib import Path

import requests

from .config import (
    BACKOFF_BASE_SEGUNDOS,
    BACKOFF_JITTER,
    DELAY_SECONDS,
    ESPERA_503,
    HEADERS,
    LIMITE_503_LOTE,
    MAX_TENTATIVAS,
)


class AntiBotError(RuntimeError):
    """Bloqueio anti-bot (403 ou challenge). Por decisão do usuário: PARAR."""


class FetchError(RuntimeError):
    pass


class SobrecargaError(RuntimeError):
    """[v1.9.6, §2.4] 503 repetido no MESMO lote — PARA o lote e reporta.

    **NÃO herda de `FetchError`, deliberadamente.** As etapas ADITIVAS do
    pipeline (histograma §3[G], ficha §3[F]) capturam `FetchError` para não
    derrubar uma coleta cara por causa de um dado opcional; se esta exceção
    fosse um `FetchError`, elas engoliriam em silêncio exatamente a parada que
    esta regra existe para garantir.
    """


# Erros de TRANSPORTE — a requisição não produziu resposta HTTP nenhuma. Só
# estes retentam (§2.4). Note que `requests.exceptions.RequestException` NÃO
# entra inteira: `HTTPError`/`TooManyRedirects` são respostas do servidor, não
# falha de transporte, e retentá-las seria insistir contra uma decisão dele.
ERROS_DE_TRANSPORTE: tuple[type[BaseException], ...] = (
    ConnectionResetError,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


class PressaoDoSite:
    """[v1.9.6, §2.4] Contador de 503 do LOTE — não da requisição, não do filme.

    O harness (§3[H]) cria um `Fetcher` por filme. Sem um objeto compartilhado,
    "o segundo 503 do lote" seria inexprimível: cada filme recomeçaria a
    contagem e a regra viraria "retenta 503 para sempre, uma vez por filme".

    `limite` é quantos 503 podem ser ABSORVIDOS com retentativa; o seguinte
    levanta `SobrecargaError`.
    """

    def __init__(self, limite: int = LIMITE_503_LOTE):
        self.limite = limite
        self.n_503 = 0

    def registrar_503(self, url: str) -> None:
        self.n_503 += 1
        if self.n_503 > self.limite:
            raise SobrecargaError(
                f"HTTP 503 pela {self.n_503}ª vez neste lote ({url}). "
                "Parando conforme §2.4 — o site está sinalizando sobrecarga e "
                "insistir seria pressão, não retentativa. Retomar depois custa "
                "só o que faltou (checkpoint do harness, §3[H])."
            )


class Fetcher:
    def __init__(
        self,
        cache_dir: str | Path,
        delay: float = DELAY_SECONDS,
        session: requests.Session | None = None,
        offline: bool = False,
        pressao: PressaoDoSite | None = None,
        max_tentativas: int = MAX_TENTATIVAS,
    ):
        self.cache_dir = Path(cache_dir)
        self.delay = delay
        self.offline = offline
        self._session = session
        self.n_network = 0
        self.n_cache = 0
        # origem por chave de cache: "cache" | "network"
        self.origins: dict[str, str] = {}
        # v1.9.6 (§2.4): telemetria de retentativa. Taxa alta é sinal de
        # pressão no site e precisa ser VISÍVEL — o modo de falha desta versão
        # seria absorver em silêncio a degradação que a v1.9.5 conseguiu ver
        # justamente porque o Fetcher quebrava.
        self.n_retentativas = 0
        self.retentativas_por_tipo: dict[str, int] = {}
        self.max_tentativas = max_tentativas
        self.pressao = pressao if pressao is not None else PressaoDoSite()

    @property
    def n_503(self) -> int:
        return self.pressao.n_503

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / cache_key

    def telemetria_retentativa(self) -> dict:
        """[§2.4] O bloco que a coleta grava por filme."""
        return {
            "n_retentativas": self.n_retentativas,
            "por_tipo": dict(self.retentativas_por_tipo),
            "n_503": self.n_503,
            "n_network": self.n_network,
        }

    def _registrar_retentativa(self, tipo: str) -> None:
        self.n_retentativas += 1
        self.retentativas_por_tipo[tipo] = self.retentativas_por_tipo.get(tipo, 0) + 1

    def _backoff(self, tentativa: int) -> float:
        """`2s · 4s · 8s` com jitter de ±25% (§2.4).

        O jitter não é decoração: sem ele, um lote que tropece no mesmo
        instante volta em uníssono, que é a forma mais rápida de transformar
        uma falha transitória em pressão real sobre o site.
        """
        base = BACKOFF_BASE_SEGUNDOS * (2 ** (tentativa - 1))
        return base * random.uniform(1 - BACKOFF_JITTER, 1 + BACKOFF_JITTER)

    def get(self, url: str, cache_key: str) -> str:
        """Retorna o HTML de `url`, servindo do cache quando `cache_key` existe.

        **Política de retentativa (§2.4):** só erro de TRANSPORTE retenta (até
        `max_tentativas`, com backoff exponencial + jitter). O delay de
        educação vale entre TODAS as tentativas — a retentativa SOMA a ele.
        403/challenge, 404 e demais status ≠ 200 falham na primeira; 503 tem
        uma única absorção por LOTE (`PressaoDoSite`), e a segunda ocorrência
        levanta `SobrecargaError`.
        """
        path = self._cache_path(cache_key)
        if path.exists():
            self.n_cache += 1
            self.origins[cache_key] = "cache"
            return path.read_text(encoding="utf-8")

        if self.offline:
            raise FetchError(f"offline e sem cache para {cache_key} ({url})")

        ultimo_erro: BaseException | None = None
        for tentativa in range(1, self.max_tentativas + 1):
            time.sleep(self.delay)
            try:
                resp = self.session.get(url, headers=HEADERS, timeout=15)
            except ERROS_DE_TRANSPORTE as e:
                # Nenhuma resposta HTTP chegou: é rede, não decisão do site.
                self._registrar_retentativa(type(e).__name__)
                ultimo_erro = e
                if tentativa == self.max_tentativas:
                    break
                time.sleep(self._backoff(tentativa))
                continue

            self.n_network += 1

            if resp.status_code == 403 or "just a moment" in resp.text.lower() \
                    or "cf-challenge" in resp.text.lower():
                raise AntiBotError(
                    f"Bloqueio anti-bot em {url} (status {resp.status_code}). "
                    "Parando conforme restrição — não escalar sem autorização."
                )

            if resp.status_code == 503:
                # Levanta SobrecargaError na 2ª ocorrência do LOTE, ANTES de
                # qualquer espera: a decisão é parar, não esperar melhor.
                self.pressao.registrar_503(url)
                self._registrar_retentativa("http_503")
                ultimo_erro = FetchError(f"{url} -> HTTP 503")
                if tentativa == self.max_tentativas:
                    break
                time.sleep(ESPERA_503)
                continue

            if resp.status_code != 200:
                raise FetchError(f"{url} -> HTTP {resp.status_code}")

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(resp.text, encoding="utf-8")
            self.origins[cache_key] = "network"
            return resp.text

        raise FetchError(
            f"{url} -> falhou após {self.max_tentativas} tentativas: "
            f"{type(ultimo_erro).__name__}: {ultimo_erro}"
        )
