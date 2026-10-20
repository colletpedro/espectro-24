"""Guarda da fase 0 do fine-tuning: nenhuma chamada paga, nenhuma rede.

Importar este módulo ANTES de qualquer `espectro24.*`:

1. recusa rodar se alguma chave de API que o código lê estiver no ambiente
   (`PROVIDER_ENV_KEYS` de `config.py`, mais as variantes que existem no
   `.env` do dono e a do TMDB) — falha alta, não aviso;
2. troca `dotenv.load_dotenv` por uma função que levanta: o `.env` da raiz
   tem as chaves, e `cli.main` o carrega sozinho;
3. bloqueia toda conexão de socket que não seja loopback. Um caminho que
   tente chamar DeepSeek, Gemini, Anthropic ou TMDB morre com
   `RedeBloqueada` na primeira conexão.

Nada aqui muda o comportamento do pacote: só impede o que esta rodada proíbe.
"""
from __future__ import annotations

import os
import socket
import sys

CHAVES = ("DEEPSEEK_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEY_PROD",
          "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "TMDB_API_KEY",
          "OPENAI_API_KEY")


class RedeBloqueada(RuntimeError):
    pass


class ChaveNoAmbiente(RuntimeError):
    pass


def _loopback(endereco) -> bool:
    host = endereco[0] if isinstance(endereco, tuple) else endereco
    return isinstance(host, str) and (host in ("localhost", "::1")
                                      or host.startswith("127."))


def instalar() -> None:
    presentes = [k for k in CHAVES if os.environ.get(k)]
    if presentes:
        raise ChaveNoAmbiente(
            f"chave(s) de API no ambiente: {presentes}. Esta rodada não chama "
            f"API paga; rode com `env -u {' -u '.join(presentes)} ...`.")

    try:
        import dotenv

        def _proibido(*_a, **_k):
            raise ChaveNoAmbiente("load_dotenv chamado: o .env tem as chaves")
        dotenv.load_dotenv = _proibido
    except ImportError:
        pass

    connect_original = socket.socket.connect

    def connect(self, endereco):
        if not _loopback(endereco):
            raise RedeBloqueada(f"conexão para {endereco!r} bloqueada pela guarda")
        return connect_original(self, endereco)

    create_original = socket.create_connection

    def create_connection(endereco, *a, **k):
        if not _loopback(endereco):
            raise RedeBloqueada(f"create_connection para {endereco!r} bloqueada pela guarda")
        return create_original(endereco, *a, **k)

    socket.socket.connect = connect
    socket.create_connection = create_connection


def checar() -> list[str]:
    """Autoteste: devolve as falhas da guarda (vazio = guarda de pé)."""
    falhas = []
    try:
        socket.create_connection(("api.deepseek.com", 443), timeout=2)
        falhas.append("create_connection passou")
    except RedeBloqueada:
        pass
    s = socket.socket()
    try:
        s.connect(("8.8.8.8", 443))
        falhas.append("socket.connect passou")
    except RedeBloqueada:
        pass
    finally:
        s.close()
    return falhas


instalar()
if "--sem-autoteste" not in sys.argv and checar():
    raise RuntimeError(f"guarda de rede não está de pé: {checar()}")
