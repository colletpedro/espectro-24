"""[2026-09-14] Fallback de CONTEÚDO: o DeepSeek recusa (`400 Content Exists
Risk`), o Gemini processa — SÓ nesse caso, e visível no dado.

O que está sob teste, na ordem do pedido:

1. o fallback dispara na recusa por conteúdo — classificação (review a
   review) e síntese (bucket a bucket);
2. o fallback NÃO dispara em JSON inválido, timeout, 5xx, rate limit, nem em
   nenhum outro 400 — o critério é a mensagem exata, e o tipo da exceção;
3. a marca de provider fica gravada no dado (registro de passe, consenso,
   bloco de eixos, bucket do resultado) e sobrevive à publicação;
4. um corpus de provider misto não muda nada a jusante (briefings, render,
   cálculo de eixos).

O erro de recusa é construído PELO SDK (`OpenAI._make_status_error`) a
partir do corpo exato que a API devolveu em `a-brighter-summer-day` — o
teste de detecção passa pelo mesmo desembrulho de `body` que a produção.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest
from google.genai import errors as genai_errors

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import synthesize as S  # noqa: E402
from espectro24.config import (  # noqa: E402
    FALLBACK_CONTEUDO_MAX_TOKENS_JSON,
    FALLBACK_CONTEUDO_MODELO,
    LLM_MAX_TENTATIVAS,
)
from espectro24.models import BucketResult, LevelResult, Review  # noqa: E402
from espectro24.render import build_output  # noqa: E402

# O corpo EXATO de `resultado/votacao-3/passe_1.jsonl` (a-brighter-summer-day,
# viewing:1343536508) e do log de publicação da síntese.
CORPO_RECUSA = {"message": "Content Exists Risk", "type": "invalid_request_error",
                "param": None, "code": "invalid_request_error"}
MARCA = {"de": "deepseek", "para": "gemini", "modelo": FALLBACK_CONTEUDO_MODELO,
         "motivo": "Content Exists Risk"}

JSON_CLS = '{"eixos": ["ritmo"], "temas_livres": []}'
JSON_SINTESE = ('{"bucket":"positivas","temas":[{"tema":"fotografia",'
                '"mencoes_aproximadas":3,"n_reviews_analisadas":5,'
                '"exemplo_parafraseado":"elogios a fotografia"}],'
                '"observacao_geral":"bem recebido"}')


@pytest.fixture(autouse=True)
def _isolamento(monkeypatch):
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    # Mesmo motivo de `test_contrato_falha_lote_classificacao.py`: os
    # scripts chamam `load_dotenv` no corpo da função, e o `.env` real tem
    # chaves que vazariam para o resto da suíte.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    S.resetar_telemetria_retentativa_llm()
    S.resetar_telemetria_fallback_conteudo()
    yield
    S.resetar_telemetria_retentativa_llm()
    S.resetar_telemetria_fallback_conteudo()


# --- erros, construídos como o SDK constrói ---------------------------------

def _resp_httpx(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request(
        "POST", "https://api.deepseek.com/chat/completions"))


def _erro_do_sdk(status: int, erro: dict):
    cli = openai.OpenAI(api_key="fake", base_url="https://api.deepseek.com")
    return cli._make_status_error(f"Error code: {status} - {{'error': {erro}}}",
                                  body={"error": erro},
                                  response=_resp_httpx(status))


def _recusa():
    return _erro_do_sdk(400, dict(CORPO_RECUSA))


def _outro_400():
    return _erro_do_sdk(400, {"message": "Invalid max_tokens value, the valid "
                                         "range of max_tokens is [1, 8192]",
                              "type": "invalid_request_error", "param": None,
                              "code": "invalid_request_error"})


def _rate_limit_com_a_mesma_mensagem():
    # O tipo também decide: a mensagem sozinha não basta.
    return _erro_do_sdk(429, dict(CORPO_RECUSA))


def _rate_limit():
    return _erro_do_sdk(429, {"message": "Rate limit reached", "type": "rate_limit",
                              "param": None, "code": "rate_limit"})


def _timeout():
    return openai.APITimeoutError(request=httpx.Request("POST", "http://x"))


def _5xx():
    return _erro_do_sdk(500, {"message": "internal", "type": "server_error",
                              "param": None, "code": None})


# --- dublês ------------------------------------------------------------------

class _Usage:
    prompt_tokens = 10
    completion_tokens = 5
    prompt_cache_hit_tokens = 0
    prompt_cache_miss_tokens = 10


def _resp_deepseek(texto):
    msg = SimpleNamespace(content=texto)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=_Usage())


class FakeDeepseek:
    """`client.chat.completions.create` — efeitos por MARCADOR no conteúdo
    do usuário (ordem entre threads não é garantida nos scripts), ou uma fila
    única quando o marcador é `None`. Cada efeito é uma fábrica: exceção nova
    por tentativa, como na vida real."""

    def __init__(self, efeitos):
        self._efeitos = ({None: list(efeitos)} if isinstance(efeitos, list)
                         else {m: list(e) for m, e in efeitos.items()})
        self._lock = threading.Lock()
        self.chamadas = []
        outer = self

        class _Completions:
            def create(inner, **kw):
                conteudo = kw["messages"][-1]["content"]
                with outer._lock:
                    outer.chamadas.append(conteudo)
                    chave = next((m for m in outer._efeitos
                                  if m is not None and m in conteudo), None)
                    efeito = outer._efeitos[chave].pop(0)
                resultado = efeito() if callable(efeito) else efeito
                if isinstance(resultado, BaseException):
                    raise resultado
                return _resp_deepseek(resultado)

        self.chat = SimpleNamespace(completions=_Completions())


def _gem(texto):
    return SimpleNamespace(text=texto, usage_metadata=None,
                           prompt_feedback=None, candidates=[])


class FakeGemini:
    """`genai.Client(...).models.generate_content` — `_gemini_resposta` cria
    um client por chamada, então a fila e o registro vivem aqui fora."""

    def __init__(self, efeitos=None):
        self._efeitos = list(efeitos) if efeitos is not None else None
        self._lock = threading.Lock()
        self.chamadas = []

    def instalar(self, monkeypatch):
        import google.genai as genai_mod

        outer = self

        class _Client:
            def __init__(self, *a, **kw):
                self.models = self

            def generate_content(self, **kw):
                with outer._lock:
                    outer.chamadas.append(kw)
                    efeito = (outer._efeitos.pop(0) if outer._efeitos is not None
                              else _gem(JSON_CLS))
                if isinstance(efeito, BaseException):
                    raise efeito
                return efeito

        monkeypatch.setattr(genai_mod, "Client", _Client)
        monkeypatch.setenv("GEMINI_API_KEY", "chave-fake")
        return self


def _bucket(nome="positivas", n=5):
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [
        Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i} completa",
               truncated=False, full_text_url=None, spoiler=False,
               full_text=f"review {i} completa")
        for i in range(n)
    ]
    return BucketResult(nome=nome, alvo=30, modo="reduzido", niveis=[lvl])


# ===========================================================================
# 1. DETECÇÃO — só a recusa exata
# ===========================================================================

def test_detecta_a_recusa_exata_como_o_sdk_a_constroi():
    erro = _recusa()
    assert isinstance(erro, openai.BadRequestError)
    assert erro.body == CORPO_RECUSA          # o SDK já desembrulhou `error`
    assert S.recusa_de_conteudo(erro)


@pytest.mark.parametrize("fabrica", [
    _outro_400,
    _rate_limit_com_a_mesma_mensagem,
    _rate_limit,
    _timeout,
    _5xx,
    lambda: openai.BadRequestError("Content Exists Risk", response=_resp_httpx(400),
                                   body=None),
    lambda: _erro_do_sdk(400, {**CORPO_RECUSA,
                               "message": "Content Exists Risk detected"}),
    lambda: json.JSONDecodeError("Expecting value", "x", 0),
    lambda: genai_errors.ClientError(400, {"message": "Content Exists Risk"}),
    lambda: ValueError("Content Exists Risk"),
], ids=["outro-400", "429-mesma-mensagem", "429", "timeout", "5xx",
        "400-sem-corpo", "mensagem-parecida", "json", "gemini-400", "valueerror"])
def test_nenhum_outro_erro_e_recusa_de_conteudo(fabrica):
    assert not S.recusa_de_conteudo(fabrica())


# ===========================================================================
# 2. CLASSIFICAÇÃO — review a review
# ===========================================================================

def test_classificacao_cai_no_gemini_na_recusa(monkeypatch):
    ds = FakeDeepseek([_recusa])
    gm = FakeGemini([_gem(JSON_CLS)]).instalar(monkeypatch)
    r = S.resposta_classificacao("SYS", "USER", "deepseek-v4-flash",
                                 max_tokens=300, client=ds,
                                 unidade="filme-x/positivas/v1/passe1")

    assert len(ds.chamadas) == 1      # a recusa não é retentada no DeepSeek
    assert len(gm.chamadas) == 1
    kw = gm.chamadas[0]
    cfg = kw["config"]
    # mesmo prompt, byte a byte — só o transporte muda
    assert (kw["contents"], cfg.system_instruction) == ("USER", "SYS")
    assert kw["model"] == FALLBACK_CONTEUDO_MODELO
    assert cfg.max_output_tokens == FALLBACK_CONTEUDO_MAX_TOKENS_JSON
    assert cfg.thinking_config.thinking_budget == 0
    assert cfg.response_mime_type == "application/json"

    assert r["texto"] == JSON_CLS
    assert (r["provider"], r["modelo"]) == ("gemini", FALLBACK_CONTEUDO_MODELO)
    assert r["fallback_conteudo"] == MARCA
    assert S.telemetria_fallback_conteudo() == [
        {"estagio": "classificacao", "unidade": "filme-x/positivas/v1/passe1",
         **MARCA}]


def test_classificacao_sem_recusa_nao_toca_o_gemini(monkeypatch):
    ds = FakeDeepseek([JSON_CLS])
    gm = FakeGemini([]).instalar(monkeypatch)
    r = S.resposta_classificacao("SYS", "USER", "deepseek-v4-flash",
                                 max_tokens=300, client=ds, unidade="u")
    assert (r["provider"], r["fallback_conteudo"]) == ("deepseek", None)
    assert gm.chamadas == []
    assert S.telemetria_fallback_conteudo() == []


@pytest.mark.parametrize("fabrica, esperado, n_deepseek", [
    (_rate_limit, openai.RateLimitError, 1),
    (_outro_400, openai.BadRequestError, 1),
    (_timeout, S.LLMTransportError, LLM_MAX_TENTATIVAS),
    (_5xx, S.LLMTransportError, LLM_MAX_TENTATIVAS),
], ids=["rate-limit", "outro-400", "timeout", "5xx"])
def test_classificacao_nao_troca_de_provider_em_outro_erro(
        monkeypatch, fabrica, esperado, n_deepseek):
    """O tratamento de antes, intacto: 4xx sobe na hora, transporte é
    retentado pelo adaptador até o teto e sobe como `LLMTransportError`."""
    ds = FakeDeepseek([fabrica] * LLM_MAX_TENTATIVAS)
    gm = FakeGemini([]).instalar(monkeypatch)
    with pytest.raises(esperado):
        S.resposta_classificacao("SYS", "USER", "m", max_tokens=300,
                                 client=ds, unidade="u")
    assert len(ds.chamadas) == n_deepseek
    assert gm.chamadas == []
    assert S.telemetria_fallback_conteudo() == []


@pytest.mark.parametrize("efeito_gemini, trecho", [
    (_gem(None), "resposta vazia"),
    (genai_errors.ClientError(400, {"message": "blocked"}), "ClientError"),
], ids=["vazio", "erro"])
def test_falha_do_fallback_de_classificacao_carrega_a_marca(
        monkeypatch, efeito_gemini, trecho):
    FakeGemini([efeito_gemini]).instalar(monkeypatch)
    with pytest.raises(S.FallbackDeConteudoFalhou, match=trecho) as exc:
        S.resposta_classificacao("SYS", "USER", "m", max_tokens=300,
                                 client=FakeDeepseek([_recusa]), unidade="u")
    assert exc.value.marca == MARCA
    assert "Content Exists Risk" in str(exc.value)


# --- o lote de produção (`votacao_3`), de ponta a ponta -----------------------

REVIEWS = [("rev-recusa", "MARCA-RECUSA"), ("rev-ok", "MARCA-OK"),
           ("rev-json-ruim", "MARCA-JSON-RUIM")]


def _preparar_votacao(monkeypatch, tmp_path, efeitos_gemini=None):
    import classificar_10 as c10
    import votacao_3 as v3

    tid = c10.taxonomia_id()
    amostra = {"taxonomia_id": tid, "filmes": [{"slug": "filme-x"}],
               "reviews": [{"slug": "filme-x", "perfil": "misto",
                            "bucket": "negativas", "id": rid, "nivel": 2.0,
                            "n_chars": 200,
                            "texto": f"{m} — review de teste completa."}
                           for rid, m in REVIEWS]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", {n: tmp_path / f"passe_{n}.jsonl"
                                          for n in (1, 2, 3, 4)})
    monkeypatch.setattr(v3, "ARQ_CONSENSO", tmp_path / "consenso.jsonl")
    monkeypatch.setattr(v3, "SAIDA", tmp_path)
    monkeypatch.setattr(v3, "RAIZ", tmp_path)   # `cmd_consenso` imprime relativo
    ds = FakeDeepseek({"MARCA-RECUSA": [_recusa] * 3, "MARCA-OK": [JSON_CLS] * 3,
                       "MARCA-JSON-RUIM": ["isto não é um JSON"] * 3})
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: ds)
    gm = FakeGemini(efeitos_gemini).instalar(monkeypatch)
    return v3, ds, gm


def _ler(arq: Path) -> dict[str, dict]:
    return {json.loads(l)["id"]: json.loads(l)
            for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()}


def test_votacao_3_marca_review_a_review_e_o_consenso_carrega(
        monkeypatch, tmp_path, capsys):
    v3, ds, gm = _preparar_votacao(monkeypatch, tmp_path)
    for n in (1, 2, 3):
        v3.classificar_passe(n)

    # Gemini só para a review recusada, uma vez por passe.
    assert len(gm.chamadas) == 3
    assert all("MARCA-RECUSA" in kw["contents"] for kw in gm.chamadas)

    p1 = _ler(tmp_path / "passe_1.jsonl")
    recusa, ok, ruim = p1["rev-recusa"], p1["rev-ok"], p1["rev-json-ruim"]
    assert recusa["ok"] is True and recusa["eixos"] == ["ritmo"]
    assert (recusa["provider"], recusa["modelo"]) == ("gemini",
                                                      FALLBACK_CONTEUDO_MODELO)
    assert recusa["fallback_conteudo"] == MARCA
    assert (ok["provider"], ok["modelo"]) == ("deepseek", v3.MODELO)
    assert "fallback_conteudo" not in ok
    # JSON inválido do DeepSeek: o `ok: False` de sempre, SEM fallback.
    assert ruim["ok"] is False and "JSONDecodeError" in ruim["erro"]
    assert "fallback_conteudo" not in ruim

    saida = capsys.readouterr().out
    assert ("passe 1: fallbacks de conteúdo (deepseek → gemini) 1: "
            "filme-x/negativas/rev-recusa/passe1") in saida

    v3.cmd_consenso()
    cons = _ler(tmp_path / "consenso.jsonl")
    assert cons["rev-recusa"]["fallback_conteudo"] == [
        {"passe": n, **MARCA} for n in (1, 2, 3)]
    assert cons["rev-recusa"]["eixos"] == ["ritmo"]
    assert "fallback_conteudo" not in cons["rev-ok"]
    assert "rev-json-ruim" not in cons      # incompleta, fora — como antes


def test_votacao_3_falha_do_fallback_fica_registrada_com_a_marca(
        monkeypatch, tmp_path):
    v3, ds, gm = _preparar_votacao(
        monkeypatch, tmp_path,
        efeitos_gemini=[genai_errors.ClientError(400, {"message": "blocked"})])
    v3.classificar_passe(1)
    reg = _ler(tmp_path / "passe_1.jsonl")["rev-recusa"]
    assert reg["ok"] is False
    assert reg["fallback_conteudo"] == MARCA
    assert reg["erro"].startswith("FallbackDeConteudoFalhou")
    # e o resume retenta o item, como qualquer `ok: False`
    gm._efeitos = [_gem(JSON_CLS)]
    ds._efeitos["MARCA-RECUSA"] = [_recusa]
    v3.classificar_passe(1)
    linhas = [json.loads(l) for l in (tmp_path / "passe_1.jsonl")
              .read_text(encoding="utf-8").splitlines()]
    assert [l["ok"] for l in linhas if l["id"] == "rev-recusa"] == [False, True]


# ===========================================================================
# 3. SÍNTESE — bucket a bucket
# ===========================================================================

def _sintese(monkeypatch, efeitos_deepseek, efeitos_gemini):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "chave-fake")
    ds = FakeDeepseek(efeitos_deepseek)
    monkeypatch.setattr(S, "deepseek_client", lambda *a, **kw: ds)
    gm = FakeGemini(efeitos_gemini).instalar(monkeypatch)
    return ds, gm


def test_sintese_cai_no_gemini_e_marca_o_bucket(monkeypatch):
    ds, gm = _sintese(monkeypatch, [_recusa], [_gem(JSON_SINTESE)])
    b = _bucket()
    S.synthesize_bucket(b, provider="deepseek")

    assert len(ds.chamadas) == 1 and len(gm.chamadas) == 1
    kw = gm.chamadas[0]
    assert kw["contents"] == S.build_user_message(b)      # o mesmo bucket
    assert kw["config"].system_instruction == S.build_system_prompt("positivas")
    assert kw["model"] == FALLBACK_CONTEUDO_MODELO
    assert kw["config"].thinking_config.thinking_budget == 0  # adaptador §D
    assert b.temas[0].tema == "fotografia"
    assert b.fallback_conteudo == MARCA
    assert S.telemetria_fallback_conteudo() == [
        {"estagio": "sintese", "unidade": "positivas", **MARCA}]


def test_sintese_fica_no_gemini_nas_retentativas_do_bucket(monkeypatch):
    """A retentativa de JSON do bucket manda o MESMO texto: voltar ao
    DeepSeek seria pagar uma recusa certa e misturar providers no bucket."""
    ds, gm = _sintese(monkeypatch, [_recusa],
                      [_gem("isto não é json"), _gem(JSON_SINTESE)])
    b = S.synthesize_bucket(_bucket(), provider="deepseek")
    assert len(ds.chamadas) == 1 and len(gm.chamadas) == 2
    assert b.temas[0].tema == "fotografia" and b.fallback_conteudo == MARCA
    assert len(S.telemetria_fallback_conteudo()) == 1


def test_sintese_sem_recusa_nao_marca(monkeypatch):
    ds, gm = _sintese(monkeypatch, [JSON_SINTESE], [])
    b = S.synthesize_bucket(_bucket(), provider="deepseek")
    assert b.fallback_conteudo is None and gm.chamadas == []
    out = build_output("filme-x", [b], "2026-09-14", {}, 5)
    assert "fallback_conteudo" not in out["buckets"][0]


def test_sintese_json_invalido_do_deepseek_nao_troca_de_provider(monkeypatch):
    ds, gm = _sintese(monkeypatch, ["não é json", "também não"], [])
    b = S.synthesize_bucket(_bucket(), provider="deepseek")
    assert b.observacao_geral == "Falha ao obter JSON válido do LLM."
    assert len(ds.chamadas) == 2 and gm.chamadas == []
    assert b.fallback_conteudo is None


@pytest.mark.parametrize("fabrica, esperado, n_deepseek", [
    (_rate_limit, openai.RateLimitError, 1),
    (_outro_400, openai.BadRequestError, 1),
    (_timeout, S.LLMTransportError, LLM_MAX_TENTATIVAS),
    (_5xx, S.LLMTransportError, LLM_MAX_TENTATIVAS),
], ids=["rate-limit", "outro-400", "timeout", "5xx"])
def test_sintese_nao_troca_de_provider_em_outro_erro(
        monkeypatch, fabrica, esperado, n_deepseek):
    ds, gm = _sintese(monkeypatch, [fabrica] * LLM_MAX_TENTATIVAS, [])
    with pytest.raises(esperado):
        S.synthesize_bucket(_bucket(), provider="deepseek")
    assert len(ds.chamadas) == n_deepseek and gm.chamadas == []
    assert S.telemetria_fallback_conteudo() == []


def test_client_injetado_nao_ganha_fallback(monkeypatch):
    """Fallback só no caminho de produção. Um client injetado (teste, script
    de comparação) que levante a recusa a vê subir, como antes."""
    gm = FakeGemini([]).instalar(monkeypatch)

    def call(system, user, model):
        raise _recusa()

    with pytest.raises(openai.BadRequestError):
        S.synthesize_bucket(_bucket(), client_call=call)
    assert gm.chamadas == []


def test_falha_do_gemini_no_fallback_de_sintese_sobe_com_a_marca(monkeypatch):
    erro = genai_errors.ServerError(503, {"message": "overloaded"})
    ds, gm = _sintese(monkeypatch, [_recusa], [erro] * LLM_MAX_TENTATIVAS)
    with pytest.raises(S.FallbackDeConteudoFalhou) as exc:
        S.synthesize_bucket(_bucket(), provider="deepseek")
    assert exc.value.marca == MARCA
    assert "positivas" in str(exc.value)
    assert len(gm.chamadas) == LLM_MAX_TENTATIVAS   # transporte do Gemini retentado


# ===========================================================================
# 4. A MARCA NO DADO — resultado, bloco de eixos, publicação
# ===========================================================================

def test_build_output_so_marca_o_bucket_que_trocou():
    trocou, nao = _bucket("positivas"), _bucket("negativas")
    trocou.fallback_conteudo = dict(MARCA)
    out = build_output("filme-x", [trocou, nao], "2026-09-14", {}, 10)
    assert out["buckets"][0]["fallback_conteudo"] == MARCA
    assert "fallback_conteudo" not in out["buckets"][1]


def _consenso_em_disco(tmp_path, marcas: dict[str, list[dict] | dict]):
    """`marcas[id]`: lista = passes de classificação (`fallback_conteudo`);
    dict = chaves extras gravadas direto na linha."""
    from espectro24 import eixos as E

    linhas = [{"slug": "filme-x", "bucket": "negativas", "id": f"v{i}",
               "eixos": ["ritmo"] if i < 30 else []} for i in range(40)]
    linhas += [{"slug": "filme-x", "bucket": "positivas", "id": f"p{i}",
                "eixos": ["ritmo"] if i < 4 else []} for i in range(40)]
    # classificada e NÃO analisada (acúmulo legítimo de §[D3]): a marca dela
    # não pode aparecer no bloco, porque ela não entra no `n`.
    linhas.append({"slug": "filme-x", "bucket": "positivas", "id": "p-orfa",
                   "eixos": []})
    for l in linhas:
        m = marcas.get(l["id"])
        if isinstance(m, list):
            l["fallback_conteudo"] = m
        elif m:
            l.update(m)
    arq = tmp_path / "consenso.jsonl"
    arq.write_text("".join(json.dumps(l) + "\n" for l in linhas), encoding="utf-8")
    (tmp_path / "amostra.json").write_text(
        json.dumps({"taxonomia_id": E.TAXONOMIA_ID}), encoding="utf-8")
    return arq


def _bloco(monkeypatch, tmp_path, marcas):
    from espectro24 import eixos as E
    from espectro24 import pipeline as P

    arq = _consenso_em_disco(tmp_path, marcas)
    monkeypatch.setattr(E, "CONSENSO_PADRAO", str(arq))
    monkeypatch.setattr(E, "CONSENSO_VERIFICADO", str(tmp_path / "nao-existe.jsonl"))
    output = {"buckets": [
        {"bucket": b, "n_validas": 40,
         "temas": [{"tema": "Ritmo", "mencoes_aproximadas": 20,
                    "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"}]}
        for b in ("negativas", "positivas")]}
    analisadas = {"negativas": {f"v{i}" for i in range(40)},
                  "positivas": {f"p{i}" for i in range(40)}}

    def rotulagem(system, user, model):
        tema = user.split("1. ")[1].splitlines()[0]
        return json.dumps({"rotulos": [{"tema": tema, "eixo": "ritmo"}]})

    return P.montar_eixos("filme-x", output, analisadas, client_call=rotulagem)


def test_bloco_de_eixos_lista_as_reviews_contadas_que_trocaram(monkeypatch, tmp_path):
    passes = [{"passe": n, **MARCA} for n in (1, 2, 3)]
    bloco = _bloco(monkeypatch, tmp_path, {"p3": passes, "p-orfa": passes})
    assert bloco["fallback_conteudo"] == [
        {"bucket": "positivas", "id": "p3", "passes": passes}]


def test_corpus_misto_nao_muda_o_calculo_de_eixos(monkeypatch, tmp_path):
    passes = [{"passe": 2, **MARCA}]
    com = _bloco(monkeypatch, tmp_path, {"p3": passes})
    sem = _bloco(monkeypatch, tmp_path, {})
    assert "fallback_conteudo" not in sem
    com.pop("fallback_conteudo")
    assert com == sem                      # n, frequências, lift, contraste


def _build_data():
    spec = importlib.util.spec_from_file_location(
        "build_data_teste", RAIZ / "frontend" / "build_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_marca_sobrevive_a_publicacao(tmp_path):
    """`write_json` → `resultado/<slug>.json` → `frontend/build_data.py`, que
    só tira `origem_paginas` e o motivo das recusas de condição — e o
    relatório do harness lê a marca de volta do dado."""
    import publicar_catalogo as pc
    from espectro24.render import write_json

    trocou = _bucket("positivas")
    trocou.fallback_conteudo = dict(MARCA)
    out = build_output("filme-x", [trocou, _bucket("negativas")], "2026-09-14",
                       {"u": "cache"}, 10)
    out["eixos"] = {"fallback_conteudo": [
        {"bucket": "positivas", "id": "v1", "passes": [{"passe": 1, **MARCA}]}]}
    caminho = write_json(out, str(tmp_path))
    publicado = json.loads(Path(caminho).read_text(encoding="utf-8"))

    bd = _build_data()
    publicado.pop("origem_paginas", None)      # o que `build_data.main` faz
    frontend = bd.sem_motivo_de_recusa(publicado)
    assert frontend["buckets"][0]["fallback_conteudo"] == MARCA
    assert frontend["eixos"]["fallback_conteudo"][0]["passes"][0] == {
        "passe": 1, **MARCA}
    assert pc.fallbacks_publicados(frontend) == [
        "sintese:positivas", "classificacao:positivas/v1"]


# ===========================================================================
# 5. A JUSANTE — provider misto não muda nada
# ===========================================================================

def _publicado_real(slug="cure"):
    p = RAIZ / "resultado" / f"{slug}.json"
    if not p.exists():
        pytest.skip(f"resultado/{slug}.json indisponível")
    return json.loads(p.read_text(encoding="utf-8"))


def test_briefings_e_render_ignoram_a_marca():
    """Narrativa, veredito e condições leem o `output`; nenhum deles pode
    mudar de comportamento porque um bucket foi sintetizado pelo Gemini."""
    from espectro24 import briefing, condicoes, veredito
    from espectro24.render import render_terminal

    real = _publicado_real()
    marcado = copy.deepcopy(real)
    for b in marcado["buckets"]:
        b["fallback_conteudo"] = dict(MARCA)
    marcado["eixos"]["fallback_conteudo"] = [
        {"bucket": "positivas", "id": "x", "passes": [{"passe": 1, **MARCA}]}]

    for mod in (briefing, veredito, condicoes):
        a, b = mod.montar_briefing(real), mod.montar_briefing(marcado)
        assert (mod.serializar_briefing(a) if a else a) == (
            mod.serializar_briefing(b) if b else b), mod.__name__
    assert render_terminal(real, tom="ambos") == render_terminal(marcado, tom="ambos")


# ===========================================================================
# 6. TELEMETRIA — a linha que atravessa o limite de processo
# ===========================================================================

def test_linha_de_telemetria_ida_e_volta():
    S._registrar_fallback_conteudo("classificacao", "f/positivas/v1/passe1", MARCA)
    S._registrar_fallback_conteudo("sintese", "positivas", MARCA)
    stderr = "outra coisa\n" + S.linha_telemetria_fallback() + "\nfim\n"
    lida = S.parse_linha_telemetria_fallback(stderr)
    assert lida == {"n": 2, "unidades": S.telemetria_fallback_conteudo()}
    assert lida["unidades"][1]["motivo"] == "Content Exists Risk"


def test_sem_linha_e_nao_sei_e_zero_e_zero():
    assert S.parse_linha_telemetria_fallback("nada aqui") is None
    assert S.parse_linha_telemetria_fallback(S.linha_telemetria_fallback()) == {
        "n": 0, "unidades": []}


# ===========================================================================
# 7. O VERIFICADOR NA REPUBLICAÇÃO — só as candidatas do filme são chamadas
# ===========================================================================

def test_verificador_restrito_por_slug_nao_retenta_falhas_de_outros_filmes(
        monkeypatch, tmp_path):
    import verificador_impacto as vi

    consenso = [{"slug": s, "bucket": "positivas", "id": rid,
                 "eixos": ["impacto_emocional"]}
                for s, rid in (("filme-a", "a1"), ("filme-b", "b1"))]
    (tmp_path / "consenso.jsonl").write_text(
        "".join(json.dumps(l) + "\n" for l in consenso), encoding="utf-8")
    (tmp_path / "amostra.json").write_text(json.dumps({"reviews": [
        {"id": rid, "nivel": 4.0, "n_chars": 100, "texto": "t"}
        for rid in ("a1", "b1")]}), encoding="utf-8")
    (tmp_path / "producao.jsonl").write_text("", encoding="utf-8")
    for nome, arq in (("ARQ_CONSENSO_PRODUCAO", "consenso.jsonl"),
                      ("ARQ_AMOSTRA_PRODUCAO", "amostra.json"),
                      ("ARQ_PRODUCAO", "producao.jsonl"),
                      ("ARQ_CONSENSO_VERIFICADO", "verificado.jsonl"),
                      ("ARQ_MANIFESTO_VERIFICADOR", "manifesto.json")):
        monkeypatch.setattr(vi, nome, tmp_path / arq)
    # o manifesto grava `fonte` relativa à raiz do repositório
    monkeypatch.setattr(vi, "RAIZ", tmp_path)
    chamadas = []
    monkeypatch.setattr(vi, "rodar_passe", lambda v, n, reviews, arq=None:
                        chamadas.append(sorted(r["id"] for r in reviews)))

    vi.cmd_aplicar_producao(["filme-a"])

    assert chamadas == [["a1"]]
    manifesto = json.loads((tmp_path / "manifesto.json").read_text())
    # a escrita continua cobrindo o consenso inteiro
    assert manifesto["fonte_n_linhas"] == 2 and manifesto["n_candidatas"] == 2


# ===========================================================================
# 8. VERIFICADOR — fallback por review, e o estado "sem verificação" visível
# ===========================================================================

JSON_VEREDITO = '{"confirma": false, "frase": "chorei no final", "alvo": "espectador"}'


def test_verificador_cai_no_gemini_na_recusa_e_grava_a_marca(monkeypatch, tmp_path):
    import verificador_impacto as vi

    ds = FakeDeepseek({"MARCA-RECUSA": [_recusa], "MARCA-OK": [JSON_VEREDITO],
                       "MARCA-JSON-RUIM": ["não é json"]})
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: ds)
    gm = FakeGemini([_gem(JSON_VEREDITO)]).instalar(monkeypatch)
    reviews = [{"id": rid, "slug": "filme-x", "nivel": 4.0, "n_chars": 100,
                "texto": f"{m} — texto da review"} for rid, m in REVIEWS]
    arq = tmp_path / "verificador.jsonl"

    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, reviews, arq=arq)

    regs = _ler(arq)
    assert len(gm.chamadas) == 1 and "MARCA-RECUSA" in gm.chamadas[0]["contents"]
    cfg = gm.chamadas[0]["config"]
    assert cfg.max_output_tokens == FALLBACK_CONTEUDO_MAX_TOKENS_JSON
    assert cfg.thinking_config.thinking_budget == 0
    recusa = regs["rev-recusa"]
    assert recusa["ok"] is True and recusa["confirma"] is False
    assert (recusa["provider"], recusa["fallback_conteudo"]) == ("gemini", MARCA)
    assert regs["rev-ok"]["provider"] == "deepseek"
    assert "fallback_conteudo" not in regs["rev-ok"]
    # JSON inválido do DeepSeek: sem troca de provider, como na classificação
    assert regs["rev-json-ruim"]["ok"] is False
    assert "fallback_conteudo" not in regs["rev-json-ruim"]
    assert S.telemetria_fallback_conteudo() == [
        {"estagio": "verificador", "unidade": "filme-x/rev-recusa", **MARCA}]


def test_verificador_nao_troca_de_provider_em_outro_erro(monkeypatch, tmp_path):
    import verificador_impacto as vi

    ds = FakeDeepseek({"MARCA-OK": [_rate_limit]})
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: ds)
    gm = FakeGemini([]).instalar(monkeypatch)
    arq = tmp_path / "v.jsonl"
    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1,
                   [{"id": "r", "slug": "f", "nivel": 4.0, "n_chars": 1,
                     "texto": "MARCA-OK"}], arq=arq)
    reg = _ler(arq)["r"]
    assert reg["ok"] is False and reg["erro"].startswith("RateLimitError")
    assert gm.chamadas == [] and "fallback_conteudo" not in reg


def test_consenso_verificado_marca_veredito_do_gemini_e_pendencia():
    import verificador_impacto as vi

    E_ = vi.EIXO
    linhas = [{"slug": "x", "bucket": "positivas", "id": i, "eixos": e}
              for i, e in (("a", [E_, "ritmo"]), ("b", [E_]), ("c", [E_]),
                           ("d", [E_]), ("e", ["ritmo"]))]
    pend = {"c": {"motivo": "recusa_de_conteudo", "erro": "BadRequestError: …"}}
    saida = {r["id"]: r for r in vi.gerar_consenso_verificado(
        linhas, {"a": False, "b": True}, pendencias=pend, fallbacks={"a": MARCA})}

    assert saida["a"]["eixos"] == ["ritmo"]
    assert saida["a"]["verificador_fallback_conteudo"] == MARCA
    assert "verificacao_pendente" not in saida["a"]
    assert saida["b"] == linhas[1]                         # verificado, sem marca
    assert saida["c"]["eixos"] == [E_]                     # conservador: fica
    assert saida["c"]["verificacao_pendente"] == {"eixo": E_, **pend["c"]}
    assert saida["d"]["verificacao_pendente"] == {"eixo": E_,
                                                  "motivo": "sem_chamada"}
    assert saida["e"] == linhas[4]                         # sem o eixo: idêntica


@pytest.mark.parametrize("erro, motivo", [
    ("BadRequestError: Error code: 400 - {'error': {'message': "
     "'Content Exists Risk', 'type': 'invalid_request_error'}}",
     "recusa_de_conteudo"),
    ("FallbackDeConteudoFalhou: deepseek recusou (Content Exists Risk); …",
     "recusa_de_conteudo_e_fallback_falhou"),
    ("JSONDecodeError: Extra data: line 3 column 1 (char 214)",
     "erro_JSONDecodeError"),
])
def test_motivo_da_pendencia(erro, motivo):
    import verificador_impacto as vi
    assert vi._motivo_pendencia(erro)["motivo"] == motivo


def test_aplicar_producao_marca_pendencia_e_fallback_no_arquivo(monkeypatch, tmp_path):
    import verificador_impacto as vi

    consenso = [{"slug": "filme-a", "bucket": "positivas", "id": rid,
                 "eixos": ["impacto_emocional"]} for rid in ("a1", "a2", "a3")]
    (tmp_path / "consenso.jsonl").write_text(
        "".join(json.dumps(l) + "\n" for l in consenso), encoding="utf-8")
    (tmp_path / "amostra.json").write_text(json.dumps({"reviews": [
        {"id": rid, "nivel": 4.0, "n_chars": 100, "texto": "t"}
        for rid in ("a1", "a2", "a3")]}), encoding="utf-8")
    registros = [
        {"ok": False, "id": "a1", "erro": "BadRequestError: Error code: 400 - "
                                          "{'error': {'message': 'Content Exists Risk'}}"},
        {"ok": True, "id": "a2", "confirma": False, "provider": "gemini",
         "fallback_conteudo": MARCA, "uso": {"prompt_tokens": 10}},
        {"ok": False, "id": "a3", "erro": "JSONDecodeError: Extra data"},
    ]
    (tmp_path / "producao.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in registros), encoding="utf-8")
    for nome, arq in (("ARQ_CONSENSO_PRODUCAO", "consenso.jsonl"),
                      ("ARQ_AMOSTRA_PRODUCAO", "amostra.json"),
                      ("ARQ_PRODUCAO", "producao.jsonl"),
                      ("ARQ_CONSENSO_VERIFICADO", "verificado.jsonl"),
                      ("ARQ_MANIFESTO_VERIFICADOR", "manifesto.json")):
        monkeypatch.setattr(vi, nome, tmp_path / arq)
    monkeypatch.setattr(vi, "RAIZ", tmp_path)
    monkeypatch.setattr(vi, "rodar_passe", lambda *a, **kw: None)

    vi.cmd_aplicar_producao(["filme-a"])

    ver = _ler(tmp_path / "verificado.jsonl")
    assert ver["a1"]["verificacao_pendente"]["motivo"] == "recusa_de_conteudo"
    assert ver["a1"]["eixos"] == ["impacto_emocional"]
    assert ver["a2"]["eixos"] == [] and ver["a2"]["verificador_fallback_conteudo"] == MARCA
    assert ver["a3"]["verificacao_pendente"]["motivo"] == "erro_JSONDecodeError"
    manifesto = json.loads((tmp_path / "manifesto.json").read_text())
    assert manifesto["pendentes_por_motivo"] == {"erro_JSONDecodeError": 1,
                                                 "recusa_de_conteudo": 1}
    assert manifesto["n_fallback_conteudo"] == 1
    assert manifesto["uso"] == {}          # a chamada do Gemini não entra no custo DeepSeek


def test_bloco_publica_veredito_do_gemini_e_verificacao_pendente(monkeypatch, tmp_path):
    pendente = {"eixo": "impacto_emocional", "motivo": "recusa_de_conteudo"}
    bloco = _bloco(monkeypatch, tmp_path, {
        "p1": {"verificador_fallback_conteudo": MARCA},
        "p2": {"verificacao_pendente": pendente},
        "p-orfa": {"verificacao_pendente": pendente},   # não contada: fora
    })
    assert bloco["fallback_conteudo"] == [
        {"bucket": "positivas", "id": "p1", "verificador": MARCA}]
    assert bloco["verificacao_pendente"] == [
        {"bucket": "positivas", "id": "p2", **pendente}]


def test_relatorio_le_verificador_e_pendencia_do_dado():
    import publicar_catalogo as pc

    dados = {"buckets": [], "eixos": {
        "fallback_conteudo": [{"bucket": "positivas", "id": "p1",
                               "passes": [{"passe": 1, **MARCA}],
                               "verificador": MARCA}],
        "verificacao_pendente": [{"bucket": "negativas", "id": "n9",
                                  "eixo": "impacto_emocional",
                                  "motivo": "erro_JSONDecodeError"}]}}
    assert pc.fallbacks_publicados(dados) == [
        "classificacao:positivas/p1", "verificador:positivas/p1"]
    assert pc.pendentes_publicados(dados) == ["negativas/n9 (erro_JSONDecodeError)"]


# ===========================================================================
# 9. ROTULAGEM — sem fallback, mas nunca "falhou sem motivo"
# ===========================================================================

def _output_rotulagem():
    return {"buckets": [{"bucket": "negativas", "n_validas": 40, "temas": [
        {"tema": "Ritmo lento", "mencoes_aproximadas": 3,
         "exemplo_parafraseado": "ex"}]}]}


def test_rotulagem_grava_a_recusa_como_recusa():
    from espectro24 import rotulagem as R

    def call(system, user, model):
        raise _recusa()

    tabela, tel = R.rotular_output(_output_rotulagem(), client_call=call)
    assert tel["falharam"] == ["negativas"]
    assert tel["motivos_falha"] == {
        "negativas": ["recusa_de_conteudo: Content Exists Risk"] * 2}


def test_rotulagem_grava_json_invalido_e_transporte():
    from espectro24 import rotulagem as R

    respostas = iter(["não é json", RuntimeError("timeout")])

    def call(system, user, model):
        r = next(respostas)
        if isinstance(r, BaseException):
            raise r
        return r

    _, tel = R.rotular_output(_output_rotulagem(), client_call=call)
    assert tel["motivos_falha"] == {
        "negativas": ["json_invalido", "RuntimeError: timeout"]}


def test_rotulagem_sem_falha_nao_tem_a_chave():
    from espectro24 import rotulagem as R

    def call(system, user, model):
        return json.dumps({"rotulos": [{"tema": "Ritmo lento", "eixo": "ritmo"}]})

    _, tel = R.rotular_output(_output_rotulagem(), client_call=call)
    assert "motivos_falha" not in tel and tel["falharam"] == []
