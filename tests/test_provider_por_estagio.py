"""Camada de provider POR ESTÁGIO (§3[D], v1.9.8).

O provider deixa de ser global: `classificacao` e `narrativa` resolvem
independentemente. A classificação NÃO migra — está auditada contra gabarito
humano e o `taxonomia_id` não hasheia o modelo, então uma troca ali seria
silenciosa e invalidaria oito sessões de medição.

Estes testes travam a resolução, a uniformidade de `uso` entre providers (a
lacuna que na v1.9.4 fez um script reimplementar o transporte) e o fato de a
chave vir sempre do ambiente.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import config, synthesize as S  # noqa: E402


# ------------------------------------------------------------- configuração

def test_existe_provider_para_cada_estagio():
    assert set(config.PROVIDER_POR_ESTAGIO) == {"classificacao", "narrativa"}
    for p in config.PROVIDER_POR_ESTAGIO.values():
        assert p in config.PROVIDER_ENV_KEYS


def test_a_classificacao_continua_em_deepseek():
    """Trocar o provider da classificação invalidaria a auditoria contra
    gabarito humano SEM mudar o taxonomia_id — silenciosamente."""
    assert config.PROVIDER_POR_ESTAGIO["classificacao"] == "deepseek"


def test_a_narrativa_usa_gemini():
    assert config.PROVIDER_POR_ESTAGIO["narrativa"] == "gemini"


def test_cada_estagio_tem_modelo_default():
    for estagio in config.PROVIDER_POR_ESTAGIO:
        assert config.MODELO_POR_ESTAGIO[estagio]


# ------------------------------------------------------------- resolução

def test_provider_do_estagio_le_a_config(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "y")
    assert S.provider_do_estagio("narrativa") == "gemini"
    assert S.provider_do_estagio("classificacao") == "deepseek"


def test_explicit_forca_todos_os_estagios(monkeypatch):
    """`--provider` continua existindo como override manual."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert S.provider_do_estagio("narrativa", "anthropic") == "anthropic"
    assert S.provider_do_estagio("classificacao", "anthropic") == "anthropic"


def test_estagio_desconhecido_e_erro(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "y")
    with pytest.raises(S.ProviderError, match="estágio"):
        S.provider_do_estagio("inexistente")


def test_chave_ausente_para_o_estagio_e_erro_explicito(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "y")
    with pytest.raises(S.ProviderError, match="GEMINI_API_KEY"):
        S.provider_do_estagio("narrativa")


def test_a_mensagem_de_erro_nomeia_o_estagio(monkeypatch):
    """Para o erro dizer QUAL etapa não pode rodar, não só qual chave falta."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "y")
    with pytest.raises(S.ProviderError, match="narrativa"):
        S.provider_do_estagio("narrativa")


# --------------------------------------------------- `uso` uniforme

def _resp_deepseek():
    return SimpleNamespace(usage=SimpleNamespace(
        prompt_tokens=100, completion_tokens=20,
        prompt_cache_hit_tokens=80, prompt_cache_miss_tokens=20))


def _resp_gemini():
    return SimpleNamespace(usage_metadata=SimpleNamespace(
        prompt_token_count=100, candidates_token_count=20,
        cached_content_token_count=80, total_token_count=120))


@pytest.mark.parametrize("provider,resp", [
    ("deepseek", _resp_deepseek()), ("gemini", _resp_gemini()),
])
def test_uso_tem_as_mesmas_chaves_nos_dois_providers(provider, resp):
    """A lacuna que a v1.9.4 registrou: sem `usage` uniforme, cada script
    novo reimplementa o transporte e perde os parâmetros do adaptador."""
    u = S.uso(resp, provider)
    assert set(u) == {"prompt_tokens", "completion_tokens",
                      "cache_hit_tokens", "cache_miss_tokens"}
    assert all(isinstance(v, int) for v in u.values())


def test_uso_do_deepseek_le_os_campos_de_cache():
    u = S.uso(_resp_deepseek(), "deepseek")
    assert u == {"prompt_tokens": 100, "completion_tokens": 20,
                 "cache_hit_tokens": 80, "cache_miss_tokens": 20}


def test_uso_do_gemini_deriva_o_miss_do_total_menos_o_hit():
    """Gemini expõe só o cacheado; o miss é o complemento — derivar aqui
    evita que cada chamador invente a sua própria conta."""
    u = S.uso(_resp_gemini(), "gemini")
    assert u["prompt_tokens"] == 100
    assert u["completion_tokens"] == 20
    assert u["cache_hit_tokens"] == 80
    assert u["cache_miss_tokens"] == 20


def test_uso_tolera_resposta_sem_contadores():
    """Provider que não expõe usage não pode derrubar o pipeline."""
    u = S.uso(SimpleNamespace(), "gemini")
    assert u == {"prompt_tokens": 0, "completion_tokens": 0,
                 "cache_hit_tokens": 0, "cache_miss_tokens": 0}


def test_deepseek_uso_continua_funcionando():
    """Compatibilidade: 8 scripts chamam `deepseek_uso` diretamente."""
    assert S.deepseek_uso(_resp_deepseek()) == S.uso(_resp_deepseek(), "deepseek")


# ------------------------------------------------------------ chave no env

@pytest.mark.parametrize("provider", ["gemini", "deepseek", "anthropic"])
def test_a_chave_vem_do_ambiente_nunca_do_codigo(provider):
    env = config.PROVIDER_ENV_KEYS[provider]
    fonte = (RAIZ / "src" / "espectro24" / "synthesize.py").read_text("utf-8")
    # a variável é LIDA do ambiente
    assert f'PROVIDER_ENV_KEYS["{provider}"]' in fonte or env in fonte


def test_nenhuma_chave_hardcoded_no_pacote():
    """Varre o pacote por algo com cara de chave de API literal."""
    import re
    padrao = re.compile(r'["\'](sk-|AIza)[A-Za-z0-9_\-]{10,}["\']')
    for arq in (RAIZ / "src").rglob("*.py"):
        assert not padrao.search(arq.read_text("utf-8")), f"chave literal em {arq}"


def test_cliente_falha_claro_sem_chave(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(S.LLMError, match="DEEPSEEK_API_KEY"):
        S.cliente("deepseek")


# ------------------------------------------------------- despacho de resposta

def test_resposta_despacha_por_provider(monkeypatch):
    chamado = {}

    def falso(system, user, model, *, max_tokens, json_mode, client=None):
        chamado["provider"] = "deepseek"
        return "resp-ds"

    monkeypatch.setattr(S, "deepseek_resposta", falso)
    out = S.resposta("s", "u", "m", provider="deepseek",
                     max_tokens=10, json_mode=True)
    assert out == "resp-ds"
    assert chamado["provider"] == "deepseek"


def test_resposta_recusa_provider_desconhecido():
    with pytest.raises(S.ProviderError, match="desconhecido"):
        S.resposta("s", "u", "m", provider="nao_existe",
                   max_tokens=10, json_mode=True)


def test_o_transporte_do_gemini_vive_no_adaptador():
    """Espelho do teste que guarda `thinking: disabled` no DeepSeek: se o
    transporte do Gemini sair de `synthesize.py`, o guard-rail passaria a
    vigiar um lugar que já não corrige nada."""
    fonte = (RAIZ / "src" / "espectro24" / "synthesize.py").read_text("utf-8")
    assert "def _gemini_resposta(" in fonte
    assert "generate_content(" in fonte


def test_gemini_resposta_devolve_o_objeto_nao_o_texto():
    """É o que permite a `uso` ler os contadores — devolver só o texto foi
    exatamente a lacuna que a v1.9.4 registrou como causa de scripts
    reimplementarem o transporte."""
    import inspect
    src = inspect.getsource(S._gemini_resposta)
    assert "return client.models.generate_content(" in src
    assert ".text" not in src.split("return")[-1]


def test_cliente_do_gemini_nao_quebra_com_chave_presente(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert S.cliente("gemini") is None      # SDK cria por chamada, por desenho


def test_cliente_recusa_provider_desconhecido():
    with pytest.raises(S.ProviderError, match="desconhecido"):
        S.cliente("nao_existe")


def test_modelo_do_estagio_segue_a_config():
    assert S.modelo_do_estagio("narrativa") == config.MODELO_POR_ESTAGIO["narrativa"]
    assert S.modelo_do_estagio("classificacao") == config.MODELO_POR_ESTAGIO["classificacao"]


def test_modelo_do_estagio_com_provider_forcado_usa_o_default_dele():
    assert (S.modelo_do_estagio("narrativa", "anthropic")
            == config.PROVIDER_DEFAULT_MODELS["anthropic"])
