"""[v1.9.24, §3[D]; consolidado na v1.9.25] Retentativa de TRANSPORTE do
adaptador de LLM.

Precedente: `tests/test_*` de `fetcher.py` (§2.4, v1.9.6) — mesmo desenho,
mesma classe de teste: retenta erro de transporte, não retenta erro de
conteúdo/autenticação/cota, respeita o teto, aplica backoff sem depender de
tempo real de parede.

**v1.9.25** move a retentativa de `resposta()` para o TRANSPORTE
(`deepseek_resposta`/`_gemini_resposta`), porque `resposta()` era só uma das
DUAS portas de entrada do adaptador e a síntese de bucket (§D) entra pela
outra (`client_call`). Os testes acompanham: contam chamadas ao SDK falso,
não à camada intermediária — espiar a camada intermediária removeria o
mecanismo sob teste.
"""
from __future__ import annotations

import httpx
import openai
import pytest
from google.genai import errors as genai_errors

from espectro24 import synthesize as S
from espectro24.config import LLM_MAX_TENTATIVAS
from espectro24.models import BucketResult, LevelResult, Review


@pytest.fixture(autouse=True)
def _telemetria_limpa():
    S.resetar_telemetria_retentativa_llm()
    yield
    S.resetar_telemetria_retentativa_llm()


def _sem_sleep_real(monkeypatch):
    """Espia `time.sleep` sem esperar de verdade — devolve a lista de
    durações pedidas, na ordem."""
    chamadas = []
    monkeypatch.setattr(S.time, "sleep", lambda s: chamadas.append(s))
    return chamadas


# --- fábricas de resposta HTTP para as exceções tipadas dos SDKs -----------

def _resp_httpx(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "http://x"))


def _openai_erro(cls, status: int, msg: str = "erro"):
    return cls(msg, response=_resp_httpx(status), body=None)


class _FakeChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _FakeDeepseekResp:
    def __init__(self, content="ok"):
        self.choices = [_FakeChoice(content)]
        self.usage = None


class _FakeDeepseekClient:
    """Injetável via `client=` em `deepseek_resposta` — a mesma porta que a
    produção usa para reaproveitar conexão (v1.9.4)."""

    def __init__(self, efeitos):
        self._efeitos = list(efeitos)
        self.n_chamadas = 0

        class _Completions:
            def create(inner_self, **kwargs):
                self.n_chamadas += 1
                efeito = self._efeitos.pop(0)
                if isinstance(efeito, BaseException):
                    raise efeito
                return efeito

        self.chat = type("Chat", (), {"completions": _Completions()})()


def _resposta_deepseek(monkeypatch, efeitos, **kw):
    client = _FakeDeepseekClient(efeitos)
    resp = S.resposta("sys", "user", "modelo-x", provider="deepseek",
                      max_tokens=100, json_mode=True, client=client, **kw)
    return resp, client


class _ContadorGemini:
    """Estado COMPARTILHADO entre retentativas: `_gemini_resposta` cria um
    `genai.Client(...)` NOVO a cada chamada (não reaproveita client entre
    tentativas, ao contrário do caminho DeepSeek injetável) — a fila de
    efeitos e a contagem precisam viver FORA do client fabricado, senão cada
    retentativa recomeçaria vendo o 1º efeito de novo."""

    def __init__(self, efeitos):
        self._efeitos = list(efeitos)
        self.n_chamadas = 0

    def gerar(self):
        self.n_chamadas += 1
        efeito = self._efeitos.pop(0)
        if isinstance(efeito, BaseException):
            raise efeito
        return efeito


def _resposta_gemini(monkeypatch, efeitos):
    import google.genai as genai_mod

    contador = _ContadorGemini(efeitos)

    class _FakeGeminiClient:
        def __init__(self, *a, **kw):
            self.models = self

        def generate_content(self, **kwargs):
            return contador.gerar()

    monkeypatch.setattr(genai_mod, "Client", _FakeGeminiClient)
    monkeypatch.setenv("GEMINI_API_KEY", "chave-fake")
    resp = S.resposta("sys", "user", "gemini-2.5-flash", provider="gemini",
                      max_tokens=100, json_mode=True)
    return resp, contador


# --- 5xx / timeout retenta e a segunda tentativa passa ----------------------

def test_deepseek_5xx_retenta_e_sucede_na_segunda_tentativa(monkeypatch):
    sleeps = _sem_sleep_real(monkeypatch)
    ok = _FakeDeepseekResp("conteúdo bom")
    resp, client = _resposta_deepseek(
        monkeypatch, [_openai_erro(openai.InternalServerError, 500), ok])
    assert resp is ok
    assert client.n_chamadas == 2
    assert len(sleeps) == 1
    tel = S.telemetria_retentativa_llm()
    assert tel["n_retentativas"] == 1
    assert tel["por_tipo"] == {"InternalServerError": 1}


def test_deepseek_connection_error_retenta_e_sucede(monkeypatch):
    _sem_sleep_real(monkeypatch)
    ok = _FakeDeepseekResp("ok")
    req = httpx.Request("POST", "http://x")
    erro_conexao = openai.APIConnectionError(request=req)
    resp, client = _resposta_deepseek(monkeypatch, [erro_conexao, ok])
    assert resp is ok
    assert client.n_chamadas == 2


def test_gemini_servererror_retenta_e_sucede(monkeypatch):
    _sem_sleep_real(monkeypatch)
    ok = object()
    erro = genai_errors.ServerError(503, {"message": "overloaded",
                                          "status": "UNAVAILABLE"})
    resp, cliente = _resposta_gemini(monkeypatch, [erro, ok])
    assert resp is ok
    assert cliente.n_chamadas == 2
    tel = S.telemetria_retentativa_llm()
    assert tel["por_tipo"] == {"ServerError": 1}


def test_gemini_timeout_httpx_retenta_e_sucede(monkeypatch):
    """Ponto ambíguo investigado (ver `_erros_transporte_llm`): sem
    `HttpRetryOptions`, o SDK deixa a exceção crua do httpx subir — e ela
    tem de ser tratada como transporte, não descartada por não ser
    `ServerError`."""
    _sem_sleep_real(monkeypatch)
    ok = object()
    resp, cliente = _resposta_gemini(
        monkeypatch, [httpx.ConnectTimeout("timeout"), ok])
    assert resp is ok
    assert cliente.n_chamadas == 2


# --- erro de conteúdo/autenticação/cota NUNCA retenta -----------------------

@pytest.mark.parametrize("cls,status", [
    (openai.RateLimitError, 429),        # cota
    (openai.AuthenticationError, 401),   # autenticação
    (openai.PermissionDeniedError, 403), # autenticação
    (openai.BadRequestError, 400),       # parâmetro inválido
    (openai.NotFoundError, 404),
    (openai.UnprocessableEntityError, 422),
])
def test_deepseek_erro_de_conteudo_ou_autenticacao_nao_retenta(monkeypatch, cls, status):
    sleeps = _sem_sleep_real(monkeypatch)
    erro = _openai_erro(cls, status)
    with pytest.raises(cls):
        _resposta_deepseek(monkeypatch, [erro])
    assert sleeps == []
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 0


def test_gemini_clienterror_4xx_nao_retenta(monkeypatch):
    """`ClientError` cobre 400/401/403 E 429 — cota do Gemini é 4xx, mesma
    classe, e não pode retentar."""
    sleeps = _sem_sleep_real(monkeypatch)
    erro = genai_errors.ClientError(429, {"message": "quota",
                                          "status": "RESOURCE_EXHAUSTED"})
    with pytest.raises(genai_errors.ClientError):
        _resposta_gemini(monkeypatch, [erro])
    assert sleeps == []
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 0


def test_erro_generico_de_conteudo_nao_retenta(monkeypatch):
    """Uma exceção qualquer (ex.: bug de parsing local, `ValueError`) não
    está na lista de transporte — sobe na hora, sem retentar."""
    sleeps = _sem_sleep_real(monkeypatch)
    with pytest.raises(ValueError):
        _resposta_deepseek(monkeypatch, [ValueError("json malformado")])
    assert sleeps == []


# --- teto respeitado ---------------------------------------------------------

def test_deepseek_teto_de_tentativas_e_respeitado(monkeypatch):
    sleeps = _sem_sleep_real(monkeypatch)
    efeitos = [_openai_erro(openai.InternalServerError, 500)
               for _ in range(LLM_MAX_TENTATIVAS)]
    with pytest.raises(S.LLMTransportError) as exc:
        _resposta_deepseek(monkeypatch, efeitos)
    assert f"após {LLM_MAX_TENTATIVAS} tentativas" in str(exc.value)
    assert isinstance(exc.value.__cause__, openai.InternalServerError)
    # N tentativas -> N-1 esperas de backoff (a última falha não espera).
    assert len(sleeps) == LLM_MAX_TENTATIVAS - 1
    tel = S.telemetria_retentativa_llm()
    assert tel["n_retentativas"] == LLM_MAX_TENTATIVAS
    assert tel["por_tipo"] == {"InternalServerError": LLM_MAX_TENTATIVAS}


def test_gemini_teto_de_tentativas_e_respeitado(monkeypatch):
    sleeps = _sem_sleep_real(monkeypatch)
    efeitos = [genai_errors.ServerError(500, {"message": "boom"})
               for _ in range(LLM_MAX_TENTATIVAS)]
    with pytest.raises(S.LLMTransportError):
        _resposta_gemini(monkeypatch, efeitos)
    assert len(sleeps) == LLM_MAX_TENTATIVAS - 1


# --- backoff efetivamente aplicado, sem depender de tempo real -------------

def test_backoff_e_exponencial_com_jitter_dentro_da_faixa(monkeypatch):
    sleeps = _sem_sleep_real(monkeypatch)
    monkeypatch.setattr(S.random, "uniform", lambda lo, hi: 1.0)  # jitter neutro
    efeitos = [_openai_erro(openai.InternalServerError, 500)
               for _ in range(LLM_MAX_TENTATIVAS)]
    with pytest.raises(S.LLMTransportError):
        _resposta_deepseek(monkeypatch, efeitos)
    # Jitter neutralizado -> backoff puro: 2s, 4s (base=2.0, dobra a cada
    # tentativa), igual à fórmula do Fetcher (§2.4).
    assert sleeps == [2.0, 4.0]


# --- a retentativa é herdada pelas camadas de cima, contando chamadas ao SDK
# FALSO (mesma técnica de `test_a_guarda_roda_dentro_de_cmd_publicar`,
# tests/test_publicar_catalogo.py: exercitar o caminho REAL e contar o efeito
# no nível de baixo, em vez de confiar que a função certa foi chamada) ------
#
# v1.9.25: a contagem passou de `deepseek_resposta` para o SDK. Espiar
# `deepseek_resposta` era o certo quando a retentativa vivia em `resposta()`;
# agora ela vive DENTRO de `deepseek_resposta`, e substituí-la por um dublê
# removeria justamente o mecanismo sob teste.

def test_resposta_herda_a_retentativa_do_transporte(monkeypatch):
    """`resposta()` — caminho de narrador (§D2) e veredito (§V) — continua
    retentando, agora por HERANÇA e não por implementação própria."""
    _sem_sleep_real(monkeypatch)
    client = _FakeDeepseekClient([_openai_erro(openai.InternalServerError, 500),
                                  _FakeDeepseekResp("ok")])
    resp = S.resposta("sys", "user", "modelo-x", provider="deepseek",
                      max_tokens=100, json_mode=True, client=client)
    assert resp.choices[0].message.content == "ok"
    assert client.n_chamadas == 2


def test_chamar_deepseek_resposta_direto_TAMBEM_retenta(monkeypatch):
    """**Premissa INVERTIDA na v1.9.25, de propósito.** A v1.9.24 tinha aqui
    o teste espelhado (`..._continua_sem_retentativa`), afirmando que quem
    chamasse `deepseek_resposta` direto não ganhava retentativa — verdade
    quando ela morava em `resposta()`, e exatamente a lacuna que deixava a
    síntese de bucket (§D) descoberta, já que ela entra por `client_call`.

    Com a retentativa movida para o transporte, o caminho direto passa a ser
    coberto também. O teste antigo não foi apagado: foi reescrito para
    afirmar o contrário, que é o objetivo da versão."""
    _sem_sleep_real(monkeypatch)
    client = _FakeDeepseekClient([_openai_erro(openai.InternalServerError, 500),
                                  _FakeDeepseekResp("ok")])
    resp = S.deepseek_resposta("sys", "user", "modelo-x", max_tokens=100,
                               json_mode=True, client=client)
    assert resp.choices[0].message.content == "ok"
    assert client.n_chamadas == 2


# ===========================================================================
# v1.9.25 — a retentativa cobre as DUAS portas de entrada, uma vez só
# ===========================================================================

def _bucket_com_reviews(n=5):
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [
        Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i} completa",
               truncated=False, full_text_url=None, spoiler=False,
               full_text=f"review {i} completa")
        for i in range(n)
    ]
    return BucketResult(nome="positivas", alvo=30, modo="reduzido", niveis=[lvl])


_JSON_OK = ('{"bucket":"positivas","temas":[{"tema":"fotografia",'
            '"mencoes_aproximadas":3,"n_reviews_analisadas":5,'
            '"exemplo_parafraseado":"elogios a fotografia"}],'
            '"observacao_geral":"bem recebido"}')


# --- AUSÊNCIA DE ANINHAMENTO ------------------------------------------------
# O risco concreto de "mover" mal: deixar a retentativa nos DOIS níveis produz
# LLM_MAX_TENTATIVAS² chamadas. Estes testes atravessam as duas camadas e
# contam o SDK falso — o único lugar onde o aninhamento seria visível.

def test_sem_aninhamento_no_caminho_client_call_do_deepseek(monkeypatch):
    """`deepseek_client_call` -> `_deepseek_call` -> `deepseek_resposta` ->
    SDK. Duas camadas acima do transporte: se alguma delas retentasse
    também, seriam 9 chamadas em vez de 3."""
    _sem_sleep_real(monkeypatch)
    client = _FakeDeepseekClient(
        [_openai_erro(openai.InternalServerError, 500)] * 20)
    monkeypatch.setattr(S, "deepseek_client", lambda *a, **kw: client)
    with pytest.raises(S.LLMTransportError):
        S.deepseek_client_call("sys", "user", "modelo-x")
    assert client.n_chamadas == LLM_MAX_TENTATIVAS


def test_sem_aninhamento_no_caminho_resposta_do_deepseek(monkeypatch):
    """A outra porta de entrada, mesmo transporte, mesmo teto."""
    _sem_sleep_real(monkeypatch)
    client = _FakeDeepseekClient(
        [_openai_erro(openai.InternalServerError, 500)] * 20)
    with pytest.raises(S.LLMTransportError):
        S.resposta("sys", "user", "modelo-x", provider="deepseek",
                   max_tokens=100, json_mode=True, client=client)
    assert client.n_chamadas == LLM_MAX_TENTATIVAS


def test_sem_aninhamento_no_caminho_client_call_do_gemini(monkeypatch):
    """`gemini_client_call` -> `_gemini_call` -> `_gemini_resposta` -> SDK.
    Este é o caminho que a v1.9.24 NÃO cobria de forma alguma, porque
    `_gemini_call` tinha transporte próprio."""
    _sem_sleep_real(monkeypatch)
    erro = genai_errors.ServerError(503, {"message": "overloaded"})
    with pytest.raises(S.LLMTransportError):
        _resposta_gemini_via(monkeypatch, [erro] * 20,
                             lambda: S.gemini_client_call("s", "u",
                                                          "gemini-2.5-flash"))
    assert _CONTADOR["obj"].n_chamadas == LLM_MAX_TENTATIVAS


_CONTADOR = {"obj": None}


def _resposta_gemini_via(monkeypatch, efeitos, acao):
    """Instala o SDK falso do Gemini e roda `acao()`. O contador vive fora do
    client porque `_gemini_resposta` fabrica um `genai.Client` NOVO a cada
    tentativa."""
    import google.genai as genai_mod

    contador = _ContadorGemini(efeitos)
    _CONTADOR["obj"] = contador

    class _FakeGeminiClient:
        def __init__(self, *a, **kw):
            self.models = self

        def generate_content(self, **kwargs):
            contador.ultimo_config = kwargs.get("config")
            return contador.gerar()

    monkeypatch.setattr(genai_mod, "Client", _FakeGeminiClient)
    monkeypatch.setenv("GEMINI_API_KEY", "chave-fake")
    return acao()


# --- SÍNTESE DE BUCKET (§D) COBERTA — o objetivo inteiro da Entrega 1 ------

def test_sintese_de_bucket_passa_a_ter_retentativa_deepseek(monkeypatch):
    """§D em produção usa DeepSeek (`PROVIDER_POR_ESTAGIO['classificacao']`).
    `synthesize_bucket` sem `client_call` injetado percorre o caminho REAL:
    `deepseek_client_call` -> `_deepseek_call` -> `deepseek_resposta`.
    Um 5xx na primeira chamada tem de ser absorvido, não derrubar o lote."""
    _sem_sleep_real(monkeypatch)
    client = _FakeDeepseekClient([_openai_erro(openai.InternalServerError, 500),
                                  _FakeDeepseekResp(_JSON_OK)])
    monkeypatch.setattr(S, "deepseek_client", lambda *a, **kw: client)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "chave-fake")

    b = S.synthesize_bucket(_bucket_com_reviews(), provider="deepseek")

    assert client.n_chamadas == 2                  # retentou e sucedeu
    assert b.temas[0].tema == "fotografia"         # e produziu síntese real
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 1


def test_sintese_de_bucket_passa_a_ter_retentativa_gemini(monkeypatch):
    """A mesma etapa sob `--provider gemini`, que é o caminho literalmente
    descoberto pela v1.9.24."""
    _sem_sleep_real(monkeypatch)

    class _RespGemini:
        text = _JSON_OK

    erro = genai_errors.ServerError(503, {"message": "overloaded"})
    b = _resposta_gemini_via(
        monkeypatch, [erro, _RespGemini()],
        lambda: S.synthesize_bucket(_bucket_com_reviews(), provider="gemini"))
    assert _CONTADOR["obj"].n_chamadas == 2
    assert b.temas[0].tema == "fotografia"


# --- CONDIÇÕES DA DELEGAÇÃO DO GEMINI (v1.9.25) ---------------------------

def test_gemini_call_delega_e_devolve_apenas_o_texto(monkeypatch):
    """`_gemini_call` passa a ser `_gemini_resposta(...).text`."""
    class _RespGemini:
        text = "prosa pura"

    out = _resposta_gemini_via(
        monkeypatch, [_RespGemini()],
        lambda: S._gemini_call("s", "u", "gemini-2.5-flash",
                               max_output_tokens=99, thinking_budget=7,
                               json_mode=False))
    assert out == "prosa pura"


def test_thinking_budget_chega_inalterado_ao_sdk(monkeypatch):
    """CONDIÇÃO 2 da delegação: `_gemini_call` exige `thinking_budget` como
    keyword, `_gemini_resposta` tem default `PROSA_THINKING_BUDGET`. A
    delegação repassa EXPLICITAMENTE — se caísse no default, este teste
    pegaria, porque 7 não é o default."""
    class _RespGemini:
        text = "x"

    _resposta_gemini_via(
        monkeypatch, [_RespGemini()],
        lambda: S._gemini_call("s", "u", "gemini-2.5-flash",
                               max_output_tokens=99, thinking_budget=7,
                               json_mode=False))
    cfg = _CONTADOR["obj"].ultimo_config
    assert cfg.thinking_config.thinking_budget == 7
    assert cfg.max_output_tokens == 99
    assert cfg.response_mime_type is None          # json_mode=False preservado


def test_json_mode_e_max_tokens_do_client_call_chegam_ao_sdk(monkeypatch):
    """A outra metade: o adaptador JSON (§D) continua fixando o modo JSON e
    `thinking_budget=0` depois da delegação."""
    class _RespGemini:
        text = "{}"

    _resposta_gemini_via(
        monkeypatch, [_RespGemini()],
        lambda: S.gemini_client_call("s", "u", "gemini-2.5-flash"))
    cfg = _CONTADOR["obj"].ultimo_config
    assert cfg.response_mime_type == "application/json"
    assert cfg.thinking_config.thinking_budget == 0


def test_chave_ausente_levanta_igual_nos_dois_caminhos(monkeypatch):
    """CONDIÇÃO 1 da delegação: `_gemini_call` fazia a checagem de chave
    inline; `_gemini_resposta` usa `_exigir_chave`. Verificado em runtime que
    as duas levantam `LLMError` com mensagem byte-idêntica — este teste
    congela isso, porque é caminho que só se exercita em produção sem a
    variável definida, e a delegação o troca em silêncio."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def _capturar(fn):
        with pytest.raises(S.LLMError) as exc:
            fn()
        return str(exc.value)

    via_call = _capturar(lambda: S._gemini_call(
        "s", "u", "gemini-2.5-flash", max_output_tokens=10,
        thinking_budget=0, json_mode=True))
    via_resposta = _capturar(lambda: S._gemini_resposta(
        "s", "u", "gemini-2.5-flash", max_output_tokens=10, json_mode=True))

    assert via_call == via_resposta
    assert "GEMINI_API_KEY" in via_call
    # E a chave ausente NÃO é transporte: falha na 1ª, sem retentar.
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 0


def test_o_transporte_do_gemini_existe_em_um_lugar_so():
    """Guard-rail estrutural da consolidação: se alguém reintroduzir um
    `generate_content` em `_gemini_call` (ou em qualquer outra função),
    a duplicata volta e a retentativa volta a cobrir só metade dos
    caminhos — exatamente o defeito que a v1.9.25 corrige."""
    import ast
    import inspect

    fonte = inspect.getsource(S)
    tree = ast.parse(fonte)
    tocam = [fn.name for fn in ast.walk(tree)
             if isinstance(fn, ast.FunctionDef)
             and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                     and c.func.attr == "generate_content"
                     for c in ast.walk(fn))]
    assert tocam == ["_gemini_resposta"], tocam


# ===========================================================================
# O TERCEIRO ponto de contato com o SDK — anthropic — REGISTRADO sem
# retentativa (v1.9.25). Não é código morto: alcançável por `--provider
# anthropic` e por `detect_provider` com só `ANTHROPIC_API_KEY` no ambiente.
# Fica assim de propósito — mas não só em prosa: se um dia "anthropic" virar
# provider DE ESTÁGIO (produção), este teste falha e aponta para a lacuna
# em vez de ela entrar em produção em silêncio.
# ===========================================================================

def test_anthropic_nao_e_provider_de_estagio_enquanto_ficar_sem_retentativa():
    """`anthropic_client_call` é o único ponto de contato com o SDK que NÃO
    passa por `_com_retentativa` (§3[D], v1.9.25) — `resposta()` nem aceita
    `provider="anthropic"`. Isso é seguro enquanto anthropic for só um
    provider AVULSO (`--provider anthropic` ou única chave no ambiente,
    nunca em produção sem pedir explicitamente).

    Se um dia alguém adicionar uma entrada `"...": "anthropic"` em
    `PROVIDER_POR_ESTAGIO` (config.py) — promovendo-o a provider de ALGUM
    estágio de produção —, este teste FALHA. A retentativa de transporte é
    PRÉ-REQUISITO para essa promoção (mesmo motivo desta sessão inteira: um
    5xx sem retentativa custa o lote todo), então a falha aqui deve ser lida
    como "implemente a retentativa do anthropic ANTES de promovê-lo", não
    como "atualize o teste"."""
    from espectro24.config import PROVIDER_POR_ESTAGIO

    assert "anthropic" not in PROVIDER_POR_ESTAGIO.values(), (
        "anthropic virou provider de estágio de produção, mas "
        "anthropic_client_call ainda não tem retentativa de transporte "
        "(§3[D], v1.9.25) — um 5xx nesse estágio vai descartar o lote "
        "inteiro, exatamente o defeito que esta sessão corrigiu para "
        "deepseek/gemini. Implemente a retentativa (ver `_com_retentativa` "
        "e como `deepseek_resposta`/`_gemini_resposta` a usam) antes de "
        "promover — não relaxe este teste.")


def test_resposta_rejeita_provider_anthropic_hoje():
    """Metade viva da mesma garantia: `resposta()` (o ponto que os
    chamadores de PRODUÇÃO usam — narrador, veredito) recusa `anthropic`
    explicitamente, então mesmo um chamador de produção que tentasse não
    conseguiria contornar a ausência de retentativa por acidente."""
    with pytest.raises(S.ProviderError):
        S.resposta("s", "u", "m", provider="anthropic", max_tokens=10,
                  json_mode=True)
