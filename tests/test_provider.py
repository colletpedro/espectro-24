"""Tarefa 2 (v1.1.1): adaptador Gemini + seleção de provider (zero chamadas reais)."""
import pytest

from espectro24.config import PROVIDER_DEFAULT_MODELS, PROVIDER_ENV_KEYS
from espectro24.synthesize import (
    ProviderError,
    detect_provider,
    gemini_client_call,
    gemini_supports_thinking,
    synthesize_bucket,
)
from test_synthesize import _bucket_com_reviews


# --- gemini_supports_thinking: condicional por família de modelo (v1.1.1) ---

@pytest.mark.parametrize("model", [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3.0-flash",   # família futura hipotética >= 2.5
])
def test_gemini_supports_thinking_familia_2_5_mais(model):
    assert gemini_supports_thinking(model) is True


@pytest.mark.parametrize("model", [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
])
def test_gemini_supports_thinking_familia_anterior_a_2_5(model):
    assert gemini_supports_thinking(model) is False


def test_gemini_supports_thinking_nome_desconhecido_e_conservador():
    # formato de nome sem versão reconhecível -> assume que NÃO suporta,
    # em vez de arriscar passar um parâmetro que a API pode rejeitar
    assert gemini_supports_thinking("gemini-flash-latest") is False
    assert gemini_supports_thinking("algum-modelo-futuro") is False


# --- detect_provider: auto-detecção e ambiguidade ---

def test_detect_provider_explicito_vence(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert detect_provider("anthropic") == "anthropic"
    assert detect_provider("gemini") == "gemini"


def test_detect_provider_nome_invalido_levanta(monkeypatch):
    with pytest.raises(ProviderError):
        detect_provider("openai")


def test_detect_provider_auto_deteccao_unica_chave(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert detect_provider(None) == "gemini"


def test_detect_provider_ambas_chaves_exige_flag(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    with pytest.raises(ProviderError, match="[Mm]últiplas"):
        detect_provider(None)


def test_detect_provider_nenhuma_chave_e_erro_claro(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="nenhuma chave"):
        detect_provider(None)


def test_provider_default_models_tem_as_duas_chaves():
    assert set(PROVIDER_DEFAULT_MODELS) == {"anthropic", "gemini"}
    assert PROVIDER_DEFAULT_MODELS["gemini"] == "gemini-2.5-flash"


# --- GeminiClient: mock do SDK, ZERO chamadas reais ---

class _FakeGeminiModels:
    def __init__(self, capture, response_text):
        self._capture = capture
        self._response_text = response_text

    def generate_content(self, model, contents, config):
        self._capture["model"] = model
        self._capture["contents"] = contents
        self._capture["config"] = config
        return type("Resp", (), {"text": self._response_text})()


class _FakeGeminiClient:
    def __init__(self, capture, response_text):
        self.models = _FakeGeminiModels(capture, response_text)


def test_gemini_client_call_usa_modo_json_nativo(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    capture = {}

    import google.genai as genai
    monkeypatch.setattr(
        genai, "Client",
        lambda api_key: _FakeGeminiClient(capture, '{"temas":[],"observacao_geral":"ok"}'),
    )

    out = gemini_client_call("SYSTEM", "USER", "gemini-2.5-flash")

    assert out == '{"temas":[],"observacao_geral":"ok"}'
    assert capture["model"] == "gemini-2.5-flash"
    assert capture["contents"] == "USER"
    assert capture["config"].system_instruction == "SYSTEM"
    assert capture["config"].response_mime_type == "application/json"  # modo JSON nativo
    # Regressão (bug real encontrado em uso ao vivo): thinking_budget precisa
    # ser 0. Sem isso, gemini-2.5-flash gasta tokens de "thinking" do mesmo
    # orçamento de max_output_tokens antes do JSON — em buckets grandes
    # (medido: 7679/8000 tokens só de thinking no bucket de 50 reviews), a
    # resposta visível vem cortada no meio e falha o parsing. Ver config.py.
    assert capture["config"].thinking_config.thinking_budget == 0


def test_gemini_client_call_modelo_2_0_nao_recebe_thinking_config(monkeypatch):
    # gemini-2.0-flash não tem mecanismo de thinking; passar ThinkingConfig
    # pode ser rejeitado pela API. O adaptador precisa OMITIR o parâmetro
    # inteiramente para esse modelo (não só zerar o budget).
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    capture = {}

    import google.genai as genai
    monkeypatch.setattr(
        genai, "Client",
        lambda api_key: _FakeGeminiClient(capture, '{"temas":[],"observacao_geral":"ok"}'),
    )

    out = gemini_client_call("SYSTEM", "USER", "gemini-2.0-flash")

    assert out == '{"temas":[],"observacao_geral":"ok"}'
    assert capture["model"] == "gemini-2.0-flash"
    assert capture["config"].thinking_config is None  # nunca setado p/ essa família


def test_gemini_client_call_sem_chave_levanta(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from espectro24.synthesize import LLMError
    with pytest.raises(LLMError):
        gemini_client_call("s", "u", "gemini-2.5-flash")


def test_gemini_mantem_parsing_defensivo_e_retentativa(monkeypatch):
    # instruções fixas byte-idênticas entre providers: o mesmo SYSTEM_PROMPT
    # é usado; o que muda é só o transporte. Aqui simulamos o transporte
    # Gemini devolvendo lixo na 1ª tentativa e JSON válido na 2ª — o
    # parsing defensivo/retentativa de synthesize_bucket é o mesmo de sempre.
    respostas = ["não é json", '{"temas":[],"observacao_geral":"via gemini"}']

    def fake_gemini(system, user, model):
        assert "PROIBIDO mencionar eventos da trama" in system  # prompt fixo intacto
        return respostas.pop(0)

    b = synthesize_bucket(_bucket_com_reviews(), client_call=fake_gemini)
    assert b.observacao_geral == "via gemini"


# --- synthesize_bucket resolve provider/model corretamente sem client_call ---

def test_synthesize_bucket_resolve_modelo_default_do_provider(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    captured = {}

    def fake(system, user, model):
        captured["model"] = model
        return '{"temas":[],"observacao_geral":"ok"}'

    import espectro24.synthesize as synth_mod
    monkeypatch.setitem(synth_mod.PROVIDER_CLIENTS, "gemini", fake)

    synthesize_bucket(_bucket_com_reviews())  # sem client_call, sem model, sem provider
    assert captured["model"] == PROVIDER_DEFAULT_MODELS["gemini"]


def test_synthesize_bucket_provider_explicito_sem_env_falha_claro(monkeypatch):
    # Mesmo com --provider explícito, a chave correspondente precisa existir
    # — detect_provider falha aqui, não só dentro da chamada real ao SDK.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        synthesize_bucket(_bucket_com_reviews(), provider="gemini")


def test_synthesize_bucket_provider_explicito_resolve_ambiguidade(monkeypatch):
    # Com AMBAS as chaves presentes (ambíguo para auto-detecção), --provider
    # explícito escolhe sem erro — essa é a razão de a flag existir.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    captured = {}

    def fake(system, user, model):
        captured["model"] = model
        return '{"temas":[],"observacao_geral":"ok"}'

    import espectro24.synthesize as synth_mod
    monkeypatch.setitem(synth_mod.PROVIDER_CLIENTS, "gemini", fake)

    synthesize_bucket(_bucket_com_reviews(), provider="gemini")
    assert captured["model"] == PROVIDER_DEFAULT_MODELS["gemini"]
