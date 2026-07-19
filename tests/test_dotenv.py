"""Carregamento de .env (suporte ao CLI): entra no ambiente, mas não
sobrescreve variáveis já exportadas. Usa uma chave FAKE, nunca a real.

IMPORTANTE (isolamento): `load_dotenv()` sem argumentos localiza o `.env` via
`find_dotenv()`, que busca a partir da localização do arquivo que chama
(inspeção de stack) — NÃO do `cwd`. Por isso `monkeypatch.chdir()` sozinho
NÃO isola esses testes do `.env` real do projeto (ele seria encontrado subindo
os diretórios a partir deste arquivo de teste). Todos os testes aqui passam
`dotenv_path` explícito para um arquivo em `tmp_path`, garantindo que o `.env`
real da raiz do projeto nunca é tocado, lido ou tem seu conteúdo exposto.
"""
import os

from dotenv import load_dotenv


def test_dotenv_carrega_variavel_no_ambiente(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=FAKE-de-teste-nao-real\n")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    load_dotenv(dotenv_path=env_file)

    assert os.environ.get("GEMINI_API_KEY") == "FAKE-de-teste-nao-real"


def test_dotenv_nao_sobrescreve_variavel_ja_exportada(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=valor-do-arquivo-env\n")
    monkeypatch.setenv("GEMINI_API_KEY", "valor-ja-exportado-no-ambiente")

    load_dotenv(dotenv_path=env_file)  # default: override=False

    assert os.environ.get("GEMINI_API_KEY") == "valor-ja-exportado-no-ambiente"


def test_dotenv_arquivo_inexistente_e_noop_silencioso(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"  # nunca criado
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = load_dotenv(dotenv_path=env_file)  # não deve levantar exceção

    assert result is False  # python-dotenv sinaliza "nada carregado"
    assert os.environ.get("GEMINI_API_KEY") is None
