"""[2026-09-16] Disjuntor de SALDO — `402 Insufficient Balance` abre na
PRIMEIRA ocorrência, sonda por leitura grátis de saldo, e o lote PARA.

O que está sob teste, na ordem do pedido (ABERTO.md C18):

1. um 402 abre — sem esperar N, porque saldo negativo é estado
   DETERMINÍSTICO da conta, não a fila oscilante de `LLMSobrecarga`;
2. a exceção é PRÓPRIA (`LLMSaldoEsgotado`), distinta de `LLMCircuitoAberto`:
   quem trata precisa saber que esta não passa sozinha;
3. o 402 não contamina o contador de sobrecarga, e vice-versa;
4. a reabertura é por `GET /user/balance` — grátis, e a única sonda possível
   numa conta cujo crédito acabou (uma chamada paga falharia por definição);
5. o `429` de concorrência reduzida por saldo AVISA alto e NÃO abre;
6. o passe ABORTA em vez de marcar centenas de reviews como pendentes — e
   não grava registro nenhum, para a reexecução pós-depósito retentar todas.

O arquivo de estado é isolado por `tests/conftest.py`
(`_disjuntor_deepseek_isolado`), igual ao teste do disjuntor de sobrecarga.
Nenhum teste aqui toca a rede: a sonda de saldo é sempre monkeypatchada.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import openai
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import config  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402

# As mensagens REAIS do lote de 2026-09-16, palavra por palavra.
MSG_402 = "Insufficient Balance"
CORPO_402 = {"error": {"message": MSG_402, "type": "unknown_error",
                       "param": None, "code": "invalid_request_error"}}
MSG_429_SALDO = ("Too many requests. Your current concurrency is 5, which "
                 "exceeds your concurrency limit of 5 based on your remaining "
                 "balance. Please top up your account.")
MSG_429_COTA = "Rate limit reached for requests per minute."
NORMAL = {"id": "x", "object": "chat.completion", "created": 0,
          "model": "deepseek-v4-flash",
          "choices": [{"index": 0, "finish_reason": "stop",
                       "message": {"role": "assistant",
                                   "content": '{"confirma": true, "frase": "f", '
                                              '"alvo": "espectador"}'}}],
          "usage": {"prompt_tokens": 10, "completion_tokens": 3,
                    "total_tokens": 13}}


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    # Nenhum teste deste arquivo pode tocar a rede: a sonda real só roda em
    # produção. Quem precisar dela monkeypatcha de novo, explicitamente.
    monkeypatch.setattr(S, "saldo_deepseek", lambda *a, **kw: None)
    S.limpar_parada_por_saldo()
    S._avisou_concorrencia_por_saldo.clear()
    S.resetar_telemetria_retentativa_llm()
    yield
    S.limpar_parada_por_saldo()
    S._avisou_concorrencia_por_saldo.clear()
    S.resetar_telemetria_retentativa_llm()


class Cliente:
    """O SDK REAL da OpenAI sobre transporte falso, com STATUS controlado —
    é o status que faz o SDK levantar `APIStatusError`/`RateLimitError`."""

    def __init__(self, status: int = 200, corpo=None):
        self._status = status
        self._corpo = corpo if corpo is not None else NORMAL
        self._lock = threading.Lock()
        self.n = 0

        def handler(req):
            with self._lock:
                self.n += 1
            return httpx.Response(self._status, json=self._corpo)

        self.sdk = openai.OpenAI(
            api_key="fake", base_url="https://api.deepseek.com", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _chamar(cliente):
    return S.deepseek_resposta("sys", "user", "deepseek-v4-flash",
                               max_tokens=300, json_mode=True, client=cliente.sdk)


def _sem_saldo() -> Cliente:
    return Cliente(402, CORPO_402)


def _estado() -> dict:
    return S.estado_circuito()


# ===========================================================================
# 1. Um 402 abre — limiar 1, não 3
# ===========================================================================

def test_um_unico_402_abre_o_disjuntor_de_saldo():
    """O contraste com a sobrecarga é o ponto: lá são 3 seguidas, aqui é 1.
    As 139 falhas de 2026-09-16 foram o custo de confirmar 139 vezes o que a
    primeira resposta já tinha provado."""
    c = _sem_saldo()
    with pytest.raises(S.LLMSaldoEsgotado, match="saldo_esgotado"):
        _chamar(c)
    e = _estado()
    assert e["aberto"] is True
    assert e["classe"] == "saldo"
    assert config.CIRCUITO_SALDO_LIMIAR == 1
    assert MSG_402 in e["ultimo_motivo"]


def test_depois_de_aberto_a_chamada_nem_sai():
    c = _sem_saldo()
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(c)
    antes = c.n
    outro = Cliente(200, NORMAL)
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(outro)
    assert outro.n == 0          # nenhuma requisição saiu
    assert c.n == antes


def test_402_nao_e_retentado():
    """4xx não entra em `_erros_transporte_llm`: uma chamada, uma falha."""
    c = _sem_saldo()
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(c)
    assert c.n == 1


# ===========================================================================
# 2. Exceção própria, distinta da de sobrecarga
# ===========================================================================

def test_saldo_esgotado_e_indisponivel_mas_nao_e_circuito_aberto():
    """As duas barram tráfego; só uma passa sozinha. Quem trata precisa
    distinguir — é essa distinção que manda o lote parar em vez de esperar."""
    assert issubclass(S.LLMSaldoEsgotado, S.LLMIndisponivel)
    assert not issubclass(S.LLMSaldoEsgotado, S.LLMCircuitoAberto)
    assert not issubclass(S.LLMCircuitoAberto, S.LLMSaldoEsgotado)


def test_a_mensagem_diz_que_nao_passa_sozinho(capsys):
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    err = capsys.readouterr().err
    assert "DISJUNTOR DE SALDO ABERTO" in err
    assert "depósito" in err


# ===========================================================================
# 3. Os dois contadores não se misturam
# ===========================================================================

def test_402_nao_conta_como_sobrecarga():
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    e = _estado()
    assert e["classe"] == "saldo"
    # não virou contagem de fila: `seguidas` de sobrecarga nunca chegou a 3
    assert e["seguidas"] == 1


def test_sobrecarga_continua_abrindo_so_em_tres_e_sem_classe_de_saldo():
    """Regressão do disjuntor antigo: o caminho de fila não pode ter mudado."""
    corpo_fila = {"error": {"message": (
        "We were unable to start processing your request within the "
        "900-second timeout limit. Please try again later.")}}
    c = Cliente(200, corpo_fila)
    for _ in range(config.CIRCUITO_LIMIAR_SOBRECARGAS):
        with pytest.raises(S.LLMSobrecarga):
            _chamar(c)
    e = _estado()
    assert e["aberto"] is True and e["seguidas"] == 3
    assert e.get("classe") != "saldo"
    with pytest.raises(S.LLMCircuitoAberto):
        _chamar(Cliente(200, NORMAL))


# ===========================================================================
# 4. Sonda por leitura de saldo — grátis, e longa
# ===========================================================================

def _abrir_vencido_saldo():
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    e = _estado()
    e["reabre_em_epoch"] = time.time() - 1          # os 30 min passaram
    Path(S.CIRCUITO_ARQUIVO).write_text(json.dumps(e), encoding="utf-8")


def test_a_sonda_e_mais_longa_que_a_de_fila():
    """Fila esvazia em minutos; saldo espera um humano depositar."""
    assert config.CIRCUITO_SALDO_REABERTURA_S == 1800
    assert config.CIRCUITO_SALDO_REABERTURA_S > config.CIRCUITO_REABERTURA_S
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    falta = _estado()["reabre_em_epoch"] - time.time()
    assert 0 < falta <= config.CIRCUITO_SALDO_REABERTURA_S


def test_antes_do_prazo_nao_sonda_nem_chama_a_rede(monkeypatch):
    sondas = []
    monkeypatch.setattr(S, "saldo_deepseek",
                        lambda *a, **kw: sondas.append(1) or {"is_available": True})
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    c = Cliente(200, NORMAL)
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(c)
    assert sondas == [] and c.n == 0


def test_sonda_que_ve_credito_fecha_o_disjuntor_e_o_trafego_volta(monkeypatch, capsys):
    _abrir_vencido_saldo()
    monkeypatch.setattr(S, "saldo_deepseek", lambda *a, **kw: {
        "is_available": True,
        "balance_infos": [{"currency": "USD", "total_balance": "5.00"}]})
    c = Cliente(200, NORMAL)
    resp = _chamar(c)                               # a chamada passa
    assert c.n == 1 and resp.choices
    e = _estado()
    assert e["aberto"] is False and e["fechado_por"] == "sonda_de_saldo"
    assert S.parada_por_saldo() is False
    assert "FECHADO" in capsys.readouterr().err


def test_sonda_sem_credito_mantem_aberto_e_empurra_o_prazo(monkeypatch):
    _abrir_vencido_saldo()
    monkeypatch.setattr(S, "saldo_deepseek", lambda *a, **kw: {
        "is_available": False,
        "balance_infos": [{"currency": "USD", "total_balance": "-0.14"}]})
    c = Cliente(200, NORMAL)
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(c)
    assert c.n == 0                                 # a rede nem foi tocada
    e = _estado()
    assert e["aberto"] is True
    assert e["reabre_em_epoch"] - time.time() > config.CIRCUITO_SALDO_REABERTURA_S - 5


def test_sonda_que_falha_nao_fecha_o_disjuntor(monkeypatch):
    """Rede fora não é prova de crédito: `None` mantém tudo como está."""
    _abrir_vencido_saldo()
    monkeypatch.setattr(S, "saldo_deepseek", lambda *a, **kw: None)
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(Cliente(200, NORMAL))
    assert _estado()["aberto"] is True


# ===========================================================================
# 5. O 429 de concorrência por saldo AVISA e não abre
# ===========================================================================

def test_429_por_saldo_avisa_alto_e_nao_abre(capsys):
    """O sinal que existiu 3 vezes em 2026-09-16 e ninguém viu."""
    c = Cliente(429, {"error": {"message": MSG_429_SALDO}})
    with pytest.raises(openai.RateLimitError):
        _chamar(c)
    err = capsys.readouterr().err
    assert "SALDO BAIXO" in err
    assert not _estado().get("aberto")
    assert S.parada_por_saldo() is False


def test_429_de_cota_comum_nao_vira_aviso_de_saldo(capsys):
    """Discriminador: sem esta asserção, um aviso que dispara em TODO 429
    passaria igual a um que lê a mensagem."""
    c = Cliente(429, {"error": {"message": MSG_429_COTA}})
    with pytest.raises(openai.RateLimitError):
        _chamar(c)
    assert "SALDO BAIXO" not in capsys.readouterr().err


def test_o_aviso_sai_uma_vez_por_processo(capsys):
    c = Cliente(429, {"error": {"message": MSG_429_SALDO}})
    for _ in range(3):
        with pytest.raises(openai.RateLimitError):
            _chamar(c)
    assert capsys.readouterr().err.count("SALDO BAIXO") == 1


# ===========================================================================
# 6. O lote PARA — e não deixa rastro de julgamento que não houve
# ===========================================================================

def test_verificador_aborta_e_nao_marca_nenhuma_pendente(tmp_path, monkeypatch):
    """O comportamento que faltou: em vez de 139 registros `ok: False` por
    motivo administrativo, zero registros e uma parada explícita."""
    import verificador_impacto as vi

    c = _sem_saldo()
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: c.sdk)
    arq = tmp_path / "v.jsonl"
    reviews = [{"id": f"r{i}", "slug": "f", "nivel": 4.0, "n_chars": 10,
                "texto": "t"} for i in range(20)]

    with pytest.raises(SystemExit, match="sem crédito"):
        vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, reviews, arq=arq)

    gravadas = [l for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert gravadas == []                   # nenhuma vira `verificacao_pendente`
    # O dano fica preso a UMA onda de concorrência: as `CONCORRENCIA` chamadas
    # já em voo quando o 402 chegou saem, e a fila inteira NÃO drena. É a
    # diferença entre 8 chamadas perdidas e as 139 de 2026-09-16.
    assert c.n <= vi.CONCORRENCIA
    assert c.n < len(reviews)


def test_verificador_retoma_tudo_depois_do_deposito(tmp_path, monkeypatch):
    import verificador_impacto as vi

    ruim = _sem_saldo()
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: ruim.sdk)
    arq = tmp_path / "v.jsonl"
    reviews = [{"id": f"r{i}", "slug": "f", "nivel": 4.0, "n_chars": 10,
                "texto": "t"} for i in range(5)]
    with pytest.raises(SystemExit):
        vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, reviews, arq=arq)

    Path(S.CIRCUITO_ARQUIVO).unlink()        # o depósito aconteceu
    S.limpar_parada_por_saldo()
    bom = Cliente(200, NORMAL)
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: bom.sdk)
    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, reviews, arq=arq)

    linhas = [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()
              if l.strip()]
    assert len(linhas) == 5 and all(l["ok"] for l in linhas)


def test_classificacao_aborta_sem_gravar_registro(tmp_path, monkeypatch):
    import classificar_10 as c10
    import votacao_3 as v3

    amostra = {"taxonomia_id": c10.taxonomia_id(), "filmes": [{"slug": "f"}],
               "reviews": [{"slug": "f", "perfil": "misto",
                            "bucket": "negativas", "id": f"r{i}", "nivel": 2.0,
                            "n_chars": 10, "texto": "t"} for i in range(10)]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", {n: tmp_path / f"p{n}.jsonl"
                                          for n in (1, 2, 3, 4)})
    c = _sem_saldo()
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: c.sdk)

    with pytest.raises(SystemExit, match="sem crédito"):
        v3.classificar_passe(1)

    gravadas = [l for l in (tmp_path / "p1.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    assert gravadas == []


# ===========================================================================
# O estado atravessa processos, como o de sobrecarga
# ===========================================================================

def _em_outro_processo(codigo: str) -> subprocess.CompletedProcess:
    prelude = (
        "import sys; from pathlib import Path\n"
        f"sys.path.insert(0, {str(RAIZ / 'src')!r})\n"
        "from espectro24 import synthesize as S\n"
        f"S.CIRCUITO_ARQUIVO = Path({str(S.CIRCUITO_ARQUIVO)!r})\n")
    return subprocess.run([sys.executable, "-c", prelude + codigo],
                          capture_output=True, text=True, timeout=60)


def test_saldo_aberto_por_um_processo_barra_o_proximo_filme():
    """O lote de publicação roda um subprocesso por filme: sem isto, cada
    filme redescobriria o saldo zerado por conta própria."""
    with pytest.raises(S.LLMSaldoEsgotado):
        _chamar(_sem_saldo())
    r = _em_outro_processo(
        "S.saldo_deepseek = lambda *a, **k: None\n"
        "try:\n    S._circuito_barrar('m')\nexcept Exception as e:\n"
        "    print(type(e).__name__)\n"
        "print(S.parada_por_saldo())\n")
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["LLMSaldoEsgotado", "True"]
