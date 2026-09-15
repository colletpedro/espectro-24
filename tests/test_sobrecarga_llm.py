"""[2026-09-14] Sobrecarga do DeepSeek: HTTP 200 com erro no corpo, prazo de
parede e UMA retentativa — nos quatro estágios expostos.

Medido na rodada 3 (ABERTO.md C16): com a fila cheia, o DeepSeek segura a
conexão ~900 s e devolve 200 SEM `choices`, com o corpo de erro. O que está
sob teste:

1. o 200 com erro no corpo vira `LLMSobrecarga`, com a mensagem REAL;
2. o prazo de parede dispara sem esperar os 900 s;
3. uma retentativa, não três, com a espera longa;
4. esgotando, a unidade fica PENDENTE (verificador, classificação) ou o
   filme falha alto (síntese) — nunca em silêncio;
5. a resposta normal não é afetada.

As respostas HTTP passam pelo SDK REAL da OpenAI (`httpx.MockTransport`):
o 200 de erro chega a `deepseek_resposta` exatamente como o SDK o monta.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import synthesize as S  # noqa: E402
from espectro24.config import (  # noqa: E402
    LLM_BACKOFF_INDISPONIVEL_S,
    LLM_BACKOFF_JITTER,
    LLM_MAX_TENTATIVAS,
    LLM_RETENTATIVAS_INDISPONIVEL,
)
from espectro24.models import BucketResult, LevelResult, Review  # noqa: E402

# O corpo EXATO medido em 2026-09-14 (review falha E review de controle).
MSG_FILA = ("We were unable to start processing your request within the "
            "900-second timeout limit. Please try again later.")
CORPO_FILA = {"error": {"message": MSG_FILA}}
CORPO_OUTRO_ERRO = {"error": {"message": "Something else went wrong"}}


def _normal(conteudo: str = '{"ok": 1}') -> dict:
    return {"id": "x", "object": "chat.completion", "created": 0,
            "model": "deepseek-v4-flash",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": conteudo}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3,
                      "total_tokens": 13}}


@pytest.fixture(autouse=True)
def esperas(monkeypatch):
    """Espia `time.sleep` (o backoff) sem esperar de verdade. O prazo de
    parede usa `Event.wait`, então não é afetado."""
    chamadas: list[float] = []
    monkeypatch.setattr(S.time, "sleep", lambda s: chamadas.append(s))
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    S.resetar_telemetria_retentativa_llm()
    S.resetar_telemetria_latencia_llm()
    yield chamadas
    S.resetar_telemetria_retentativa_llm()
    S.resetar_telemetria_latencia_llm()


class ClienteHTTP:
    """O SDK real, sobre um transporte falso. `respostas`: lista consumida em
    ordem, ou um dict/callable devolvido sempre."""

    def __init__(self, respostas):
        self._fila = respostas if isinstance(respostas, list) else None
        self._sempre = None if isinstance(respostas, list) else respostas
        self._lock = threading.Lock()
        self.n = 0

        def handler(req):
            with self._lock:
                self.n += 1
                corpo = self._fila.pop(0) if self._fila is not None else self._sempre
            if callable(corpo):
                corpo = corpo(req)
            return httpx.Response(200, json=corpo)

        self.sdk = openai.OpenAI(
            api_key="fake", base_url="https://api.deepseek.com", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _resposta(cliente, **kw):
    return S.deepseek_resposta("sys", "user", "deepseek-v4-flash",
                               max_tokens=300, json_mode=True,
                               client=cliente.sdk, **kw)


def _espera_longa(s: float) -> bool:
    b = LLM_BACKOFF_INDISPONIVEL_S
    return b * (1 - LLM_BACKOFF_JITTER) <= s <= b * (1 + LLM_BACKOFF_JITTER)


# ===========================================================================
# 1. HTTP 200 com erro no corpo
# ===========================================================================

def test_200_com_erro_de_fila_vira_LLMSobrecarga_com_a_mensagem_real(esperas):
    c = ClienteHTTP(CORPO_FILA)
    with pytest.raises(S.LLMSobrecarga) as exc:
        _resposta(c)
    assert MSG_FILA in str(exc.value)           # o motivo REAL, não TypeError
    assert not isinstance(exc.value, TypeError)


def test_outro_erro_no_corpo_sobe_com_a_mensagem_e_nao_retenta(esperas):
    c = ClienteHTTP(CORPO_OUTRO_ERRO)
    with pytest.raises(S.LLMRespostaComErro, match="Something else went wrong"):
        _resposta(c)
    assert c.n == 1 and esperas == []
    assert not issubclass(S.LLMRespostaComErro, S.LLMIndisponivel)


# ===========================================================================
# 3. UMA retentativa, com espera longa
# ===========================================================================

def test_uma_retentativa_nao_tres(esperas):
    c = ClienteHTTP(CORPO_FILA)
    with pytest.raises(S.LLMSobrecarga, match="desistiu após 2"):
        _resposta(c)
    assert c.n == 1 + LLM_RETENTATIVAS_INDISPONIVEL == 2
    assert len(esperas) == 1 and _espera_longa(esperas[0])
    assert S.telemetria_retentativa_llm()["por_tipo"] == {"LLMSobrecarga": 2}


def test_sobrecarga_seguida_de_resposta_normal_passa(esperas):
    c = ClienteHTTP([CORPO_FILA, _normal()])
    resp = _resposta(c)
    assert resp.choices[0].message.content == '{"ok": 1}'
    assert c.n == 2 and len(esperas) == 1


def test_transporte_continua_com_o_teto_de_antes(esperas):
    """A política nova é SÓ para chamada não processada: 5xx segue com
    `LLM_MAX_TENTATIVAS` e o backoff curto."""
    def cinco_xx(req):
        raise httpx.ConnectError("sem rede", request=req)

    c = ClienteHTTP(cinco_xx)
    with pytest.raises(S.LLMTransportError):
        _resposta(c)
    assert c.n == LLM_MAX_TENTATIVAS
    assert all(s < LLM_BACKOFF_INDISPONIVEL_S / 2 for s in esperas)


# ===========================================================================
# 2. Prazo de parede
# ===========================================================================

def test_prazo_de_parede_dispara_sem_esperar_os_900s(monkeypatch, esperas):
    monkeypatch.setattr(S, "LLM_PRAZO_PAREDE_S", 0.2)
    solta = threading.Event()
    n = {"chamadas": 0}

    def pendurada(**kw):
        n["chamadas"] += 1
        solta.wait(30)            # a fila de 900 s, encurtada
        return SimpleNamespace(choices=None)

    cliente = SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=pendurada)))
    t0 = time.monotonic()
    try:
        with pytest.raises(S.LLMPrazoExcedido, match="prazo de parede") as exc:
            S.deepseek_resposta("sys", "user", "m", max_tokens=300,
                                json_mode=True, client=cliente)
        dt = time.monotonic() - t0
    finally:
        solta.set()               # libera as threads abandonadas
    assert dt < 3                 # 2 × 0,2 s de prazo + backoff espiado
    assert n["chamadas"] == 2     # uma retentativa
    assert "descartada" in str(exc.value)
    assert len(esperas) == 1 and _espera_longa(esperas[0])


def test_thread_abandonada_e_daemon():
    """Sem isto, o CLI ficaria pendurado na saída até a chamada abandonada
    terminar — o `ThreadPoolExecutor` espera suas threads no atexit."""
    solta = threading.Event()
    with pytest.raises(S.LLMPrazoExcedido):
        S._com_prazo_de_parede(lambda: solta.wait(30), 0.05, "deepseek", "m")
    abandonadas = [t for t in threading.enumerate() if t.name == "llm-deepseek"]
    solta.set()
    assert abandonadas and all(t.daemon for t in abandonadas)


# ===========================================================================
# 5. Resposta normal não é afetada
# ===========================================================================

def test_resposta_normal_nao_e_afetada(esperas):
    c = ClienteHTTP(_normal('{"eixos": ["ritmo"]}'))
    resp = _resposta(c)
    assert resp.choices[0].message.content == '{"eixos": ["ritmo"]}'
    assert resp.usage.prompt_tokens == 10
    assert c.n == 1 and esperas == []
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 0


def test_resposta_json_com_fallback_grava_latencia(esperas):
    c = ClienteHTTP(_normal())
    r = S.resposta_json_com_fallback("sys", "user", "m", max_tokens=300,
                                     estagio="verificador", unidade="f/x",
                                     client=c.sdk)
    assert isinstance(r["latencia_s"], float) and r["provider"] == "deepseek"
    tel = S.telemetria_latencia_llm()
    assert tel["verificador"]["n"] == 1
    assert set(tel["verificador"]) == {"n", "p50", "p95", "p99", "max"}


def test_linha_de_latencia_ida_e_volta():
    S._registrar_latencia_llm("sintese", 12.5)
    S._registrar_latencia_llm("sintese", 3.0)
    S._registrar_latencia_llm("rotulagem", 1.1)
    stderr = "x\n" + S.linha_telemetria_latencia() + "\n"
    lida = S.parse_linha_telemetria_latencia(stderr)
    assert lida == S.telemetria_latencia_llm()
    assert lida["sintese"]["max"] == 12.5 and lida["sintese"]["n"] == 2
    assert S.parse_linha_telemetria_latencia("nada") is None


# ===========================================================================
# 4. Esgotando — a unidade fica pendente, não silenciosa
# ===========================================================================

def test_verificador_esgotado_fica_pendente_com_o_motivo_real(monkeypatch, tmp_path):
    import verificador_impacto as vi

    c = ClienteHTTP(CORPO_FILA)
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: c.sdk)
    arq = tmp_path / "v.jsonl"
    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1,
                   [{"id": "r1", "slug": "f", "nivel": 4.0, "n_chars": 10,
                     "texto": "texto"}], arq=arq)
    reg = json.loads(arq.read_text(encoding="utf-8").splitlines()[0])
    assert reg["ok"] is False
    assert reg["erro"].startswith("LLMSobrecarga") and MSG_FILA in reg["erro"]
    assert c.n == 2

    pend = {"r1": vi._motivo_pendencia(reg["erro"])}
    assert pend["r1"]["motivo"] == "erro_LLMSobrecarga"
    linha = vi.gerar_consenso_verificado(
        [{"slug": "f", "bucket": "positivas", "id": "r1",
          "eixos": [vi.EIXO]}], {}, pendencias=pend)[0]
    assert linha["eixos"] == [vi.EIXO]                   # conservador
    assert linha["verificacao_pendente"]["motivo"] == "erro_LLMSobrecarga"
    assert MSG_FILA in linha["verificacao_pendente"]["erro"]


def test_classificacao_esgotada_grava_ok_false_com_o_motivo_real(monkeypatch, tmp_path):
    import classificar_10 as c10
    import votacao_3 as v3

    amostra = {"taxonomia_id": c10.taxonomia_id(), "filmes": [{"slug": "f"}],
               "reviews": [{"slug": "f", "perfil": "misto", "bucket": "negativas",
                            "id": "r1", "nivel": 2.0, "n_chars": 10,
                            "texto": "texto"}]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", {n: tmp_path / f"p{n}.jsonl"
                                          for n in (1, 2, 3, 4)})
    c = ClienteHTTP(CORPO_FILA)
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: c.sdk)

    v3.classificar_passe(1)

    reg = json.loads((tmp_path / "p1.jsonl").read_text(encoding="utf-8"))
    assert reg["ok"] is False and reg["erro"].startswith("LLMSobrecarga")
    assert MSG_FILA in reg["erro"]
    assert "fallback_conteudo" not in reg            # sobrecarga não é recusa


def test_rotulagem_esgotada_nao_empilha_e_grava_o_motivo():
    from espectro24 import rotulagem as R

    n = {"chamadas": 0}

    def call(system, user, model):
        n["chamadas"] += 1
        raise S.LLMSobrecarga(f"deepseek não processou a chamada: {MSG_FILA}")

    saida = R.rotular_bucket("negativas", [{"tema": "Ritmo lento",
                                            "mencoes_aproximadas": 3}],
                             client_call=call)
    assert n["chamadas"] == 1                      # não retenta por cima
    assert saida["falhou"] is True
    assert saida["motivos_falha"][0].startswith("LLMSobrecarga")
    assert MSG_FILA in saida["motivos_falha"][0]


def _bucket():
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i}",
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text=f"review {i}") for i in range(5)]
    return BucketResult(nome="positivas", alvo=30, modo="reduzido", niveis=[lvl])


def test_sintese_esgotada_falha_alto_com_o_motivo_real(monkeypatch):
    """Na síntese a unidade é o bucket e a falha custa o FILME: ela sobe (o
    CLI sai com rc≠0, o harness grava o stderr) em vez de publicar um bucket
    sem temas. Nada é gravado em silêncio."""
    c = ClienteHTTP(CORPO_FILA)
    monkeypatch.setattr(S, "deepseek_client", lambda *a, **kw: c.sdk)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")
    with pytest.raises(S.LLMSobrecarga) as exc:
        S.synthesize_bucket(_bucket(), provider="deepseek")
    assert MSG_FILA in str(exc.value)
    assert c.n == 2                                  # uma retentativa, e para
