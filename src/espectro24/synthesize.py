"""[D] Síntese temática por bucket via LLM (SPEC §D).

Prompt fixo reproduz §D LITERALMENTE e é BYTE-IDÊNTICO entre providers — só o
transporte (client_call) muda. v1.1.2: o prompt passou a ser PARAMETRIZADO
POR BUCKET (preâmbulo de papel com nome + intervalo de notas), não mais uma
string única — a parametrização é por bucket, nunca por modelo/provider.

Contrato formal do cliente injetável (v1.1.1):
    client_call(system: str, user: str, model: str) -> str
Qualquer implementação (Anthropic, Gemini, mock de teste) deve respeitar essa
assinatura. `synthesize_bucket` faz parsing defensivo (strip de fences,
try/except) com 1 retentativa sobre o texto devolvido, independente do
provider.

v1.1.2 — motivação das validações pós-parsing (ver `resultado/comparacao/
COMPARACAO.md`): rodando o MESMO prompt sobre o MESMO corpus, o flash-lite (a)
gerou uma `observacao_geral` do bucket NEGATIVAS dizendo "a maioria dos
críticos considera o filme um fracasso" — generalizando um recorte filtrado
por construção (só as notas baixas) para a opinião geral do filme; e o
2.5-flash (b) usou frases entre aspas em `exemplo_parafraseado`, violando a
regra de paráfrase (citação literal, ainda que traduzida). O preâmbulo de
papel ataca (a) na raiz (o modelo agora sabe que só vê um recorte enviesado);
as validações pós-parsing abaixo são rede de segurança/telemetria para os dois
problemas, não a defesa principal.
"""
from __future__ import annotations

import difflib
import json
import os
import re

from .config import (
    BUCKETS,
    BUCKET_ALVO,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_MS,
    MAX_TEMAS,
    MODELO_POR_ESTAGIO,
    MODEL_DEFAULT,
    PROSA_MAX_TOKENS,
    PROSA_THINKING_BUDGET,
    PROVIDER_DEFAULT_MODELS,
    PROVIDER_ENV_KEYS,
    PROVIDER_POR_ESTAGIO,
    nota_para_url,
)
from .models import BucketResult, Tema


def _intervalo_bucket(bucket_nome: str) -> str:
    """Ex.: 'negativas' -> '0.5–2.5 estrelas'."""
    niveis = BUCKETS[bucket_nome]
    lo, hi = min(niveis), max(niveis)
    return f"{nota_para_url(lo)}–{nota_para_url(hi)} estrelas"


def build_system_prompt(bucket_nome: str) -> str:
    """Monta o prompt fixo (SPEC §D). Parametrizado por BUCKET (preâmbulo de
    papel: nome + intervalo de notas) — NÃO por provider/modelo, que
    continuam recebendo texto byte-idêntico para o mesmo bucket.

    v1.1.2: preâmbulo novo antes das instruções invariantes, atacando na raiz
    o erro de enquadramento observado na comparação de modelos (ver docstring
    do módulo) — o modelo precisa saber que só está vendo um recorte
    enviesado por construção, não a recepção geral do filme.
    """
    intervalo = _intervalo_bucket(bucket_nome)
    return f"""\
Você é uma etapa de um pipeline que agrega reviews de usuários de um filme \
do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES \
desta etapa (negativas, medianas, positivas); você está recebendo \
EXCLUSIVAMENTE a faixa "{bucket_nome}" ({intervalo}) — um recorte enviesado \
POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.

Sua função é descrever o que ESTE grupo específico de reviews diz. Outros \
módulos do pipeline cuidam das outras faixas de nota; o usuário final verá \
as três análises lado a lado, cada uma rotulada com sua faixa.

Consequência explícita: é PROIBIDO generalizar para "os críticos", "a \
maioria", "o consenso" ou "a recepção do filme". A `observacao_geral` deve \
se referir sempre a ESTE grupo (ex.: "as reviews {bucket_nome} apontam...", \
"este grupo destaca..."), nunca ao filme em termos absolutos.

Instruções fixas (invariáveis):
1. Anti-spoiler: descreva as críticas em nível temático (ritmo, atuações, \
fotografia, roteiro em termos abstratos). É PROIBIDO mencionar eventos da \
trama, destinos de personagens, reviravoltas ou o final, mesmo que as reviews \
os mencionem.
2. `exemplo_parafraseado` é paráfrase, NUNCA citação literal de nenhuma review.
3. Temas ordenados por `mencoes_aproximadas` decrescente; no máximo {MAX_TEMAS} \
temas por bucket; não invente temas de menção única, salvo se o bucket tiver \
menos de 5 reviews.
4. As reviews podem estar em qualquer idioma; sua saída é SEMPRE em pt-BR.
5. Responda APENAS o JSON, sem preâmbulo, sem cercas de código.
6. É PROIBIDO usar aspas (simples, duplas ou angulares) dentro de \
`exemplo_parafraseado` — nunca cite nem reproduza um trecho entre aspas, \
mesmo traduzido; reescreva sempre em terceira pessoa, com suas próprias \
palavras.
7. Reforço de idioma: TODOS os campos de texto da saída devem estar em \
pt-BR, incluindo os NOMES DOS TEMAS — nunca deixe um tema em inglês ou \
outro idioma, mesmo que a review de origem esteja nesse idioma.

Formato de saída (JSON puro):
{{
  "bucket": "<nome>",
  "temas": [
    {{
      "tema": "<curto>",
      "mencoes_aproximadas": <int>,
      "n_reviews_analisadas": <int>,
      "exemplo_parafraseado": "<paráfrase>"
    }}
  ],
  "observacao_geral": "<1-2 frases>"
}}"""


# Reforço anexado ao prompt SOMENTE na retentativa de validação (idioma
# e/ou escopo) — v1.1.2 §D.
_REFORCO_VALIDACAO = """

REFORÇO CRÍTICO — sua resposta anterior violou uma regra fixa; corrija AGORA:
- Se usou qualquer palavra/frase fora de pt-BR (inclusive nos nomes dos \
temas): reescreva TUDO em português do Brasil.
- Se a `observacao_geral` generalizou para "os críticos", "a maioria", "o \
consenso" ou "a recepção do filme": reescreva se referindo apenas a ESTE \
grupo de reviews (a faixa de nota analisada), nunca ao filme como um todo."""
















class LLMError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    """Erro na seleção/resolução de provider (chave ausente/ambígua, nome inválido)."""


# --- Adaptadores de provider (contrato: (system, user, model) -> str) ---

def anthropic_client_call(system: str, user: str, model: str,
                          max_tokens: int = LLM_MAX_TOKENS) -> str:
    import anthropic

    key = os.environ.get(PROVIDER_ENV_KEYS["anthropic"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['anthropic']} não definida no ambiente.")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def anthropic_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§D2 narrador / §E2 editor) — v1.6.0: só o teto de
    saída muda (`PROSA_MAX_TOKENS`). O Anthropic não compartilha orçamento
    entre raciocínio e resposta como o Gemini, então não há budget a fixar."""
    return anthropic_client_call(system, user, model, max_tokens=PROSA_MAX_TOKENS)


def gemini_supports_thinking(model: str) -> bool:
    """Família gemini-2.5+ suporta `ThinkingConfig`; gemini-2.0 e anteriores
    não têm o mecanismo de thinking e podem rejeitar o parâmetro.

    Heurística: extrai a versão major.minor do nome do modelo
    (`gemini-2.5-flash` -> (2,5), `gemini-2.0-flash` -> (2,0)) e compara com
    (2,5). Nome sem versão reconhecível (formato inesperado/futuro) ->
    conservador, assume que NÃO suporta (não arrisca passar um parâmetro que
    pode ser rejeitado por um modelo desconhecido).
    """
    m = re.match(r"gemini-(\d+)\.(\d+)", model)
    if not m:
        return False
    major, minor = int(m.group(1)), int(m.group(2))
    return (major, minor) >= (2, 5)


def gemini_client_call(system: str, user: str, model: str) -> str:
    """Adaptador Gemini via google-genai, usando modo JSON nativo.

    O parsing defensivo (fences/try-except) e a retentativa continuam vivendo
    em `synthesize_bucket` — response_mime_type="application/json" reduz a
    chance de precisar deles, mas não os torna dispensáveis (o modelo ainda
    pode devolver um JSON sintaticamente inválido ou fora do schema).

    thinking_budget=0 — CONDICIONAL ao modelo (v1.1.1, comparação de
    modelos): modelos gemini-2.5-* gastam tokens de "thinking" do MESMO
    orçamento de max_output_tokens, ANTES de gerar a resposta visível.
    Medido ao vivo: no bucket real "negativas" (50 reviews, maior do
    sistema), thinking sozinho consumiu 7679/8000 tokens, cortando o JSON no
    meio (finish_reason=MAX_TOKENS) mesmo com um teto generoso — o consumo
    escala com o tamanho do prompt e não é previsível de antemão. Para uma
    tarefa de extração estruturada como esta (não raciocínio livre), desligar
    thinking resolve a causa raiz em vez de perseguir um teto de tokens
    maior. MAS `ThinkingConfig` é específico da família 2.5+ — passá-lo para
    gemini-2.0-flash (sem mecanismo de thinking) pode ser rejeitado pela API;
    por isso o parâmetro só é incluído quando `gemini_supports_thinking(model)`.
    """
    return _gemini_call(system, user, model, max_output_tokens=LLM_MAX_TOKENS,
                        thinking_budget=0, json_mode=True)


def gemini_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§D2 narrador / §E2 editor) — v1.6.0.

    Reverte o `thinking_budget=0` da v1.2.x para um budget FIXO
    (`PROSA_THINKING_BUDGET`) com teto de saída folgado
    (`PROSA_MAX_TOKENS`). O diagnóstico v2 mostrou que o truncamento que
    motivou desligar thinking vinha do raciocínio SEM TETO competindo com a
    resposta pelo mesmo orçamento — com budget fixo, 4/4 chamadas
    terminaram em STOP (ver comentário em `config.py`).
    """
    return _gemini_call(system, user, model,
                        max_output_tokens=PROSA_MAX_TOKENS,
                        thinking_budget=PROSA_THINKING_BUDGET, json_mode=True)


def _gemini_resposta(system: str, user: str, model: str, *,
                     max_output_tokens: int, json_mode: bool,
                     thinking_budget: int = PROSA_THINKING_BUDGET):
    """Resposta INTEIRA do Gemini (com `usage_metadata`), não só o texto.

    Espelho de `deepseek_resposta` — existe pela mesma razão registrada na
    v1.9.4: sem acesso aos contadores, um chamador que precise de custo
    reimplementa o transporte e perde os parâmetros que o adaptador fixa.
    """
    from google import genai
    from google.genai import types

    _exigir_chave("gemini")
    client = genai.Client(
        api_key=os.environ[PROVIDER_ENV_KEYS["gemini"]],
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )
    config_kwargs = dict(system_instruction=system,
                         max_output_tokens=max_output_tokens)
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if gemini_supports_thinking(model):
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget)
    return client.models.generate_content(
        model=model, contents=user,
        config=types.GenerateContentConfig(**config_kwargs))


def _gemini_call(system: str, user: str, model: str, *, max_output_tokens: int,
                 thinking_budget: int, json_mode: bool) -> str:
    """Transporte comum do Gemini. `thinking_budget` só é enviado quando o
    modelo suporta (`gemini_supports_thinking`) — passá-lo a um gemini-2.0
    pode ser rejeitado pela API. `json_mode=False` desliga
    `response_mime_type` para etapas cuja saída é texto puro (§E2 editor)."""
    from google import genai
    from google.genai import types

    key = os.environ.get(PROVIDER_ENV_KEYS["gemini"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['gemini']} não definida no ambiente.")
    # TIMEOUT (v1.6.0): sem ele o SDK bloqueia INDEFINIDAMENTE. Observado ao
    # vivo durante a regeneração desta versão — um processo ficou 67 minutos
    # parado, 0% de CPU, dormindo num socket, sem nunca voltar nem falhar.
    # Um timeout transforma "trava para sempre" em "erro que o chamador vê".
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )
    config_kwargs = dict(
        system_instruction=system,
        max_output_tokens=max_output_tokens,
    )
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if gemini_supports_thinking(model):
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget)
    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return resp.text


def deepseek_client_call(system: str, user: str, model: str) -> str:
    """Adaptador DeepSeek (v1.8.0) via SDK da OpenAI (compatível — só
    `base_url`/`api_key` mudam), usando MODO JSON explícito.

    Provider ADICIONAL, não default de produção (ver PROVIDER_CLIENTS
    abaixo) — decisão registrada após o encerramento dos experimentos de LLM
    local (`experimentos-ollama-arquivado/`): o free tier do Gemini (20
    req/dia) inviabiliza construir catálogo, e o modelo local não sustentou
    as ~18 invariantes do narrador numa única chamada.

    NON-THINKING explícito (`extra_body={"thinking": {"type": "disabled"}}`)
    — MESMO motivo documentado para o Gemini (`gemini_client_call`) e
    observado também no experimento local: tokens de raciocínio competem
    pelo MESMO orçamento de `max_tokens` que a resposta visível, e já
    causaram truncamento de JSON em dois providers diferentes. deepseek-v4-*
    tem thinking LIGADO por padrão (esforço "high") — desligar não é
    cosmético, é a causa raiz que este adaptador evita de saída.

    `response_format={"type": "json_object"}` — a API exige que a palavra
    "json" apareça em algum lugar do prompt quando esse modo é usado; os
    prompts fixos do §D/§D2 já pedem "Responda APENAS o JSON" (byte-idênticos
    entre providers), então nenhum ajuste de prompt foi necessário.
    """
    return _deepseek_call(system, user, model, max_tokens=LLM_MAX_TOKENS,
                          json_mode=True)


def deepseek_client_call_prosa(system: str, user: str, model: str) -> str:
    """Variante de PROSA (§E2 editor) — v1.8.0.

    DIFERENÇA DELIBERADA da variante JSON: `json_mode=False` (sem
    `response_format`). O editor espera e devolve TEXTO PURO
    (`editar_narrativa`/`_uma_chamada` fazem só um strip de fences
    defensivo) — forçar `response_format=json_object` aqui faria a API
    rejeitar a chamada (ela exige a palavra "json" no prompt quando o modo
    está ligado, e o prompt do editor não promete JSON) ou, na melhor das
    hipóteses, embrulhar a prosa num objeto que `_formato_invalido` (§E2,
    v1.7.2) já rejeitaria. Esse foi exatamente o defeito que invalidou o
    teste do editor no experimento local com Ollama — aqui a diferenciação
    é estrutural desde o primeiro commit, não um fix posterior.
    """
    return _deepseek_call(system, user, model, max_tokens=PROSA_MAX_TOKENS,
                          json_mode=False)


def deepseek_client(timeout_ms: int = LLM_TIMEOUT_MS):
    """Cliente DeepSeek reutilizável — a ÚNICA fábrica autorizada (v1.9.4).

    Existe para que um chamador de fora do pacote (script de medição, com
    centenas de chamadas concorrentes) possa reaproveitar a conexão sem
    instanciar o SDK por conta própria. Instanciar por conta própria é
    exatamente o caminho que o guard-rail de §3[D] fecha — e é o caminho pelo
    qual `thinking: disabled` se perde.
    """
    from openai import OpenAI

    key = os.environ.get(PROVIDER_ENV_KEYS["deepseek"])
    if not key:
        raise LLMError(f"{PROVIDER_ENV_KEYS['deepseek']} não definida no ambiente.")
    return OpenAI(api_key=key, base_url="https://api.deepseek.com",
                  timeout=timeout_ms / 1000)


def deepseek_resposta(system: str, user: str, model: str, *, max_tokens: int,
                      json_mode: bool, client=None):
    """A chamada crua, com a resposta INTEIRA — inclusive `usage`.

    Adicionada na v1.9.4 junto do guard-rail (§3[D]): scripts de medição
    precisam dos contadores de token para reportar custo real, e era essa
    necessidade — que `_deepseek_call` não atendia, por devolver só o texto —
    que empurrava cada script novo a reimplementar o transporte e, no caminho,
    esquecer `thinking: disabled`. Fechar o buraco é o que torna o guard-rail
    aplicável em vez de apenas restritivo.
    """
    client = deepseek_client() if client is None else client
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        # NON-THINKING explícito — ver docstring de deepseek_client_call.
        extra_body={"thinking": {"type": "disabled"}},
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs)


def deepseek_uso(resp) -> dict:
    """Contadores de token de uma resposta, no formato que os relatórios de
    custo usam. Os dois campos de cache são específicos do DeepSeek e vêm
    ausentes em provider que não os expõe — daí o `getattr` com default."""
    u = resp.usage
    return {
        "prompt_tokens": u.prompt_tokens,
        "completion_tokens": u.completion_tokens,
        "cache_hit_tokens": getattr(u, "prompt_cache_hit_tokens", 0) or 0,
        "cache_miss_tokens": getattr(u, "prompt_cache_miss_tokens", 0) or 0,
    }


def _deepseek_call(system: str, user: str, model: str, *, max_tokens: int,
                   json_mode: bool) -> str:
    """Transporte comum do DeepSeek. Timeout convertido de ms (`LLM_TIMEOUT_MS`,
    ver `config.py`) para segundos, unidade que o SDK da OpenAI espera."""
    resp = deepseek_resposta(system, user, model, max_tokens=max_tokens,
                             json_mode=json_mode)
    return resp.choices[0].message.content or ""


# ===========================================================================
# Camada GENÉRICA de provider (v1.9.8, §3[D] "Provider por estágio")
# ===========================================================================
# `deepseek_resposta`/`deepseek_uso` foram criados na v1.9.4 para fechar o
# buraco que empurrava cada script novo a reimplementar o transporte (e, no
# caminho, perder `thinking: disabled`). Eram específicos de um provider —
# então o mesmo buraco reabriria no Gemini na primeira vez que alguém
# precisasse de `usage` dele. Estas funções fecham o buraco para os DOIS
# antes que ele apareça: mesma assinatura, mesmas chaves de retorno.


def cliente(provider: str, timeout_ms: int = LLM_TIMEOUT_MS):
    """Fábrica de cliente reutilizável por provider — a ÚNICA autorizada.

    Instanciar o SDK por conta própria é exatamente o caminho que o
    guard-rail de §3[D] fecha. Gemini não expõe um cliente reaproveitável
    da mesma forma (o SDK cria um por chamada dentro de `_gemini_call`), e
    devolver `None` aqui é deliberado: o chamador passa isso adiante e
    `resposta` trata, em vez de cada script inventar seu próprio caminho.
    """
    if provider == "deepseek":
        return deepseek_client(timeout_ms)
    if provider == "gemini":
        _exigir_chave("gemini")
        return None
    if provider == "anthropic":
        _exigir_chave("anthropic")
        return None
    raise ProviderError(f"provider {provider!r} desconhecido — use um de "
                        f"{sorted(PROVIDER_CLIENTS)}.")


def _exigir_chave(provider: str) -> None:
    env = PROVIDER_ENV_KEYS[provider]
    if not os.environ.get(env):
        raise LLMError(f"{env} não definida no ambiente.")


def resposta(system: str, user: str, model: str, *, provider: str,
             max_tokens: int, json_mode: bool, client=None):
    """A chamada crua, com a resposta INTEIRA — inclusive contadores de token.

    Despacha por provider mantendo a assinatura de `deepseek_resposta`, para
    que um chamador troque de provider mudando um argumento, não o caminho.
    """
    if provider == "deepseek":
        return deepseek_resposta(system, user, model, max_tokens=max_tokens,
                                 json_mode=json_mode, client=client)
    if provider == "gemini":
        return _gemini_resposta(system, user, model, max_output_tokens=max_tokens,
                                json_mode=json_mode)
    raise ProviderError(f"provider {provider!r} desconhecido — use um de "
                        f"{sorted(PROVIDER_CLIENTS)}.")


def uso(resp, provider: str) -> dict:
    """Contadores de token no MESMO formato para todo provider.

    As quatro chaves são as que os relatórios de custo do projeto já
    consomem. `cache_miss` do Gemini é DERIVADO (prompt − cacheado) porque a
    API expõe só o cacheado — derivar aqui evita que cada chamador invente a
    própria conta e que dois relatórios discordem sobre o mesmo número.
    Resposta sem contadores devolve zeros em vez de estourar: um provider
    que não expõe `usage` não pode derrubar o pipeline.
    """
    vazio = {"prompt_tokens": 0, "completion_tokens": 0,
             "cache_hit_tokens": 0, "cache_miss_tokens": 0}
    if provider == "deepseek":
        u = getattr(resp, "usage", None)
        if u is None:
            return vazio
        return {
            "prompt_tokens": int(getattr(u, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(u, "completion_tokens", 0) or 0),
            "cache_hit_tokens": int(getattr(u, "prompt_cache_hit_tokens", 0) or 0),
            "cache_miss_tokens": int(getattr(u, "prompt_cache_miss_tokens", 0) or 0),
        }
    if provider == "gemini":
        u = getattr(resp, "usage_metadata", None)
        if u is None:
            return vazio
        entrada = int(getattr(u, "prompt_token_count", 0) or 0)
        cacheado = int(getattr(u, "cached_content_token_count", 0) or 0)
        return {
            "prompt_tokens": entrada,
            "completion_tokens": int(getattr(u, "candidates_token_count", 0) or 0),
            "cache_hit_tokens": cacheado,
            "cache_miss_tokens": max(0, entrada - cacheado),
        }
    return vazio


def provider_do_estagio(estagio: str, explicit: str | None = None) -> str:
    """Resolve o provider de um ESTÁGIO do pipeline (v1.9.8).

    `explicit` (`--provider`) força todos os estágios — é o override manual.
    Sem ele, vale `PROVIDER_POR_ESTAGIO`. A chave correspondente precisa
    estar no ambiente, e o erro nomeia o ESTÁGIO junto da chave: saber que
    falta `GEMINI_API_KEY` sem saber que é a narrativa que não vai rodar
    manda o leitor caçar a resposta no código.
    """
    if estagio not in PROVIDER_POR_ESTAGIO:
        raise ProviderError(
            f"estágio {estagio!r} desconhecido — use um de "
            f"{sorted(PROVIDER_POR_ESTAGIO)}.")
    if explicit is not None:
        return detect_provider(explicit)
    provider = PROVIDER_POR_ESTAGIO[estagio]
    env = PROVIDER_ENV_KEYS[provider]
    if not os.environ.get(env):
        raise ProviderError(
            f"estágio {estagio!r} usa o provider {provider!r}, mas {env} não "
            f"está definida no ambiente (ver PROVIDER_POR_ESTAGIO em "
            f"config.py; --provider força outro).")
    return provider


def modelo_do_estagio(estagio: str, provider: str | None = None) -> str:
    """Modelo default do estágio; com `provider` explícito, o default dele."""
    if provider and provider != PROVIDER_POR_ESTAGIO.get(estagio):
        return PROVIDER_DEFAULT_MODELS[provider]
    return MODELO_POR_ESTAGIO[estagio]


PROVIDER_CLIENTS = {
    "anthropic": anthropic_client_call,
    "gemini": gemini_client_call,
    "deepseek": deepseek_client_call,
}

# v1.6.0: adaptadores das etapas de PROSA (§D2 narrador, §E2 editor) — thinking
# fixo + teto folgado. A síntese por bucket (§D) continua em PROVIDER_CLIENTS.
PROVIDER_CLIENTS_PROSA = {
    "anthropic": anthropic_client_call_prosa,
    "gemini": gemini_client_call_prosa,
    "deepseek": deepseek_client_call_prosa,
}


def detect_provider(explicit: str | None = None) -> str:
    """Resolve qual provider usar (CLI §B2/Tarefa 2).

    Prioridade: `explicit` (--provider) > chave única presente no ambiente.
    Ambas as chaves presentes sem --provider, ou nenhuma chave presente,
    são erro — a spec exige decisão explícita nesses casos, não um default
    silencioso. Mesmo com `explicit`, a chave correspondente precisa estar
    presente — falha aqui em vez de só na hora da chamada real, para que o
    CLI possa recusar antes de gastar qualquer requisição de coleta.
    """
    if explicit is not None:
        if explicit not in PROVIDER_CLIENTS:
            raise ProviderError(
                f"provider {explicit!r} desconhecido — use um de "
                f"{sorted(PROVIDER_CLIENTS)}."
            )
        if not os.environ.get(PROVIDER_ENV_KEYS[explicit]):
            raise ProviderError(
                f"--provider {explicit} escolhido, mas "
                f"{PROVIDER_ENV_KEYS[explicit]} não está definida no ambiente."
            )
        return explicit

    presentes = [p for p, env in PROVIDER_ENV_KEYS.items() if os.environ.get(env)]
    if len(presentes) == 1:
        return presentes[0]
    if not presentes:
        chaves = " ou ".join(PROVIDER_ENV_KEYS.values())
        raise ProviderError(
            f"nenhuma chave de API encontrada ({chaves}) — defina uma delas "
            f"ou passe --provider explicitamente."
        )
    raise ProviderError(
        f"múltiplas chaves de API presentes ({', '.join(presentes)}) — "
        f"especifique --provider {{{','.join(sorted(PROVIDER_CLIENTS))}}}."
    )


def _resolve_call_and_model(client_call, model, provider, prosa: bool = False):
    """Resolve (call, model) para uma etapa LLM — compartilhado por
    `synthesize_bucket` [D], `narrate_output` [D2] e `editar_narrativa` [E2].
    Client custom sem provider conhecido cai no default histórico
    (`MODEL_DEFAULT`); caso contrário o default de modelo segue o provider
    resolvido.

    v1.6.0: `prosa=True` seleciona os adaptadores de PROSA (thinking fixo +
    teto folgado, ver `config.py`). Um `client_call` injetado (testes) é
    respeitado como sempre — a escolha de adaptador só vale quando o cliente
    não foi fornecido."""
    if client_call is not None:
        return client_call, (model or MODEL_DEFAULT)
    resolved_provider = detect_provider(provider)
    clients = PROVIDER_CLIENTS_PROSA if prosa else PROVIDER_CLIENTS
    return clients[resolved_provider], (model or PROVIDER_DEFAULT_MODELS[resolved_provider])


def build_user_message(bucket: BucketResult) -> str:
    reviews = bucket.reviews_analisadas
    linhas = [
        f"Bucket: {bucket.nome}",
        f"Total de reviews analisadas neste bucket: {len(reviews)}",
        "",
        "Reviews (nota em estrelas + texto completo):",
    ]
    for i, r in enumerate(reviews, 1):
        linhas.append(f"[{i}] nota={r.rating} estrelas:")
        linhas.append(r.effective_text)
        linhas.append("")
    return "\n".join(linhas)


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -3]
        # remove possível "json" na primeira linha
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    return t.strip()


def _parse_llm_json(raw: str) -> dict:
    return json.loads(_strip_fences(raw))


# --- Validações pós-parsing (código, não prompt) — SPEC §D, v1.1.2 ---
# Rede de segurança/telemetria: o preâmbulo de papel (build_system_prompt) é
# a defesa principal contra vazamento de escopo; estas checagens são baratas
# e propositalmente imperfeitas (heurísticas), não substituem revisão humana.

_ASPAS_CHARS = "\"'“”‘’«»‹›"


_ASPAS_RE = re.compile(r"\\?[" + re.escape(_ASPAS_CHARS) + r"]")


def _remover_aspas(texto: str) -> tuple[str, bool]:
    """Remoção MECÂNICA (não reescrita) de aspas de citação. Retorna
    (texto_limpo, houve_remocao).

    v1.7.1 — bugfix: a remoção trocava só o CARACTERE de aspas por "", então
    uma citação escapada (`\\"A Cura\\"`, do jeito que o texto às vezes sai
    de dentro de um valor JSON) virava `\\A Cura\\` — a aspas sumia, a
    contrabarra de escape ficava, publicada ao vivo em `cure` e
    `the-invite-2026` (v1.7.0). Agora a contrabarra que precede a aspas é
    removida junto, como uma unidade — nunca uma contrabarra sozinha em
    outro lugar do texto, só a que está imediatamente antes de uma aspas.
    """
    if not any(c in texto for c in _ASPAS_CHARS):
        return texto, False
    limpo = _ASPAS_RE.sub("", texto)
    limpo = re.sub(r"[ \t]{2,}", " ", limpo).strip()
    return limpo, True


# Heurística de stopwords — mesma família da usada em scripts/compare_models.py
# (checagem factual de idioma), agora promovida a validação de produção.
_STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "que", "para", "com", "uma", "um", "e",
    "os", "as", "não", "mais", "como", "por", "sobre", "são", "foi", "ao",
    "à", "às", "seu", "sua", "entre", "também", "muito", "há", "este",
    "esta", "esse", "essa", "mas", "ou", "já", "só", "sem", "pelo", "pela",
}
_STOPWORDS_EN = {
    "the", "and", "of", "to", "in", "is", "for", "with", "on", "are", "as",
    "this", "that", "by", "from", "or", "an", "its", "be", "was", "were",
    "but", "not", "at", "it", "his", "her", "their", "than", "into",
}


def _idioma_e_pt_br(texto: str) -> bool:
    """True se pt-BR OU indeterminado (sem stopwords de nenhum idioma) — a
    ausência de evidência não vira falso positivo de violação."""
    palavras = [w.strip(".,;:!?()\"'").lower() for w in texto.split()]
    n_pt = sum(1 for w in palavras if w in _STOPWORDS_PT)
    n_en = sum(1 for w in palavras if w in _STOPWORDS_EN)
    if n_pt == 0 and n_en == 0:
        return True
    return n_pt >= n_en


def _texto_para_checagem_idioma(temas: list[Tema], observacao_geral: str) -> str:
    partes = [t.tema for t in temas] + [t.exemplo_parafraseado for t in temas]
    partes.append(observacao_geral)
    return " ".join(partes)










# Marcadores de vazamento de escopo (generalização do bucket p/ o filme
# inteiro) — lista propositalmente pequena e literal, não é NLP.
_MARCADORES_ESCOPO = [
    "a maioria dos críticos", "o consenso", "os críticos consideram",
    "amplamente aclamado", "amplamente rejeitado",
]

def _tem_marcador_de_escopo(observacao_geral: str) -> bool:
    texto = observacao_geral.lower()
    return any(m in texto for m in _MARCADORES_ESCOPO)

# Marcadores de PREVALÊNCIA entre grupos (v1.2.1) — a prosa narrativa
# apresentando a cota de amostragem como distribuição da recepção (comparar
# tamanhos de grupo / inferir prevalência global). Heurística acento-sensível
# como as demais: rede de segurança/telemetria; a defesa principal é a
# invariante (c) do prompt §D2. Lista mínima, literal, não é NLP.
_MARCADORES_PREVALENCIA = [
    "maioria dos espectadores", "maioria do público", "minoria",
    "grupo maior", "grupo menor", "igualmente expressivo",
    "polarizada", "dividida", "consenso",
]

def _tem_marcador_de_prevalencia(texto: str) -> bool:
    t = texto.lower()
    return any(m in t for m in _MARCADORES_PREVALENCIA)


def _construir_temas(data: dict, n_analisadas: int) -> list[Tema]:
    """Constrói a lista de Tema a partir do JSON parseado: clamp do
    numerador (v1.1.1) + remoção mecânica de aspas (v1.1.2)."""
    temas = []
    for t in (data.get("temas") or [])[:MAX_TEMAS]:
        try:
            bruto = int(t.get("mencoes_aproximadas", 0))
        except (TypeError, ValueError):
            bruto = 0
        clampado = max(0, min(bruto, n_analisadas))
        foi_clampado = clampado != bruto

        exemplo_bruto = str(t.get("exemplo_parafraseado", ""))
        exemplo_limpo, aspas_removidas = _remover_aspas(exemplo_bruto)

        temas.append(Tema(
            tema=str(t.get("tema", "")),
            mencoes_aproximadas=clampado,
            n_reviews_analisadas=n_analisadas,
            exemplo_parafraseado=exemplo_limpo,
            mencoes_clampadas=foi_clampado,
            mencoes_valor_original=bruto if foi_clampado else None,
            aspas_removidas=aspas_removidas,
        ))
    temas.sort(key=lambda x: x.mencoes_aproximadas, reverse=True)  # §D.3
    return temas


def synthesize_bucket(bucket: BucketResult, client_call=None,
                      model: str | None = None,
                      provider: str | None = None) -> BucketResult:
    """Preenche `bucket.temas` e `bucket.observacao_geral`.

    Buckets sem análise (§C piso) NÃO chamam o LLM. Reviews enviadas usam
    SEMPRE texto completo (garantido por C'). Uma retentativa em JSON inválido.

    Provider (v1.1.1): se `client_call` for omitido, resolve o adaptador via
    `provider` (--provider) ou auto-detecção pela chave de API presente no
    ambiente (`detect_provider`) — ver GATE de ambiguidade lá. O modelo
    default também passa a depender do provider resolvido
    (`PROVIDER_DEFAULT_MODELS`), a menos que `model` seja passado explicitamente.

    Validações pós-parsing (v1.1.2, código não-prompt):
    - Aspas em `exemplo_parafraseado`: removidas mecanicamente, SEM
      retentativa (correção barata, não precisa de nova chamada). Flag
      `aspas_removidas` por tema.
    - Idioma e escopo: verificados juntos; se qualquer um falhar, UMA
      retentativa COMBINADA (mesma chamada cobre os dois — mantém o
      orçamento de chamadas previsível). Se persistir, aceita o resultado da
      retentativa e sinaliza `idioma_invalido`/`escopo_suspeito` no bucket
      (visível no render) em vez de insistir indefinidamente.
    """
    if bucket.modo == "sem_analise":
        bucket.observacao_geral = (
            f"Bucket sem análise temática: apenas {bucket.n_validas} review(s) "
            f"válida(s) (piso é 3)."
        )
        return bucket

    call, model = _resolve_call_and_model(client_call, model, provider)

    system = build_system_prompt(bucket.nome)
    user = build_user_message(bucket)
    n_analisadas = len(bucket.reviews_analisadas)

    data = None
    for tentativa in range(2):  # chamada + 1 retentativa de JSON inválido (§D)
        raw = call(system, user, model)
        try:
            data = _parse_llm_json(raw)
            break
        except (ValueError, json.JSONDecodeError):
            if tentativa == 1:
                bucket.observacao_geral = "Falha ao obter JSON válido do LLM."
                return bucket

    temas = _construir_temas(data, n_analisadas)
    observacao_geral = str(data.get("observacao_geral", ""))

    idioma_ok = _idioma_e_pt_br(_texto_para_checagem_idioma(temas, observacao_geral))
    escopo_ok = not _tem_marcador_de_escopo(observacao_geral)

    if not idioma_ok or not escopo_ok:
        raw_retry = call(system + _REFORCO_VALIDACAO, user, model)
        try:
            data_retry = _parse_llm_json(raw_retry)
            temas = _construir_temas(data_retry, n_analisadas)
            observacao_geral = str(data_retry.get("observacao_geral", ""))
            idioma_ok = _idioma_e_pt_br(
                _texto_para_checagem_idioma(temas, observacao_geral))
            escopo_ok = not _tem_marcador_de_escopo(observacao_geral)
        except (ValueError, json.JSONDecodeError):
            pass  # retentativa não parseou -> mantém o resultado original

    bucket.temas = temas
    bucket.observacao_geral = observacao_geral
    bucket.idioma_invalido = not idioma_ok
    bucket.escopo_suspeito = not escopo_ok
    return bucket


# =====================================================================
# [D2] Narrador — etapa PÓS-síntese (SPEC §D2, v1.2.0)
# =====================================================================
# Recebe EXCLUSIVAMENTE o JSON validado (dict de saída de build_output —
# temas/números/observacoes, NUNCA reviews brutas) e reescreve como prosa.
# A saída volta como JSON {"narrativa": "<texto>"} para reusar os mesmos
# adaptadores (modo JSON nativo) e o parsing defensivo do §D.



# --- Regra (c): as DUAS variantes (v1.4.0) ---
# Sem distribuição real de notas, vale a proibição total da v1.2.1 (o dado
# que justificaria falar de prevalência não existe). Com distribuição, a
# regra INVERTE: o peso passa a ser obrigatório e ancorado no share real.
# Só esta regra muda entre as variantes — todo o resto do prompt é
# byte-idêntico, para que a comparação A/B isole a mudança.













# --- Quantificador pré-computado (v1.2.3) ---
# Correção pela raiz do mesmo tipo da v1.1.1 (denominador): o LLM não decide
# mais número nem rótulo numérico — o código é a autoridade. Motivação: a
# calibração por INSTRUÇÃO (v1.2.2, o LLM calculava a fração e escolhia o
# quantificador sozinho) reduziu mas não eliminou o modo de falha "quase
# todos"/"praticamente todos" aplicado a frações de 65-70% — reincidiu 2x na
# primeira regeneração pós-fix (ver changelog v1.2.3).
#
# Faixas idênticas às da v1.2.2, na ordem do mais FRACO ao mais FORTE.
# Cada faixa é (rótulo, limite_inferior_inclusive, limite_superior,
# superior_inclusive). "poucos" é a ÚNICA faixa com superior EXCLUSIVO
# ("abaixo de 10%", i.e. pct < 10); todas as demais são inclusivas nos dois
# extremos, exatamente como escritas na v1.2.2 ("25%-50%" inclui 25 e 50).
#
# Resolução determinística de sobreposição (regra: "sempre o rótulo mais
# fraco"): iterando as faixas do mais fraco pro mais forte e retornando o
# PRIMEIRO match, cada fronteira compartilhada resolve assim:
#   pct == 10  -> só "alguns" bate ("poucos" exige pct < 10, exclusivo)
#   pct == 25  -> "alguns" (10-25) e "muitos" (25-50) empatam -> "alguns"
#   pct == 50  -> "muitos" (25-50), "cerca de metade" (40-60) e "a maioria"
#                 (50-80) empatam -> "muitos" (o mais fraco dos três)
#   pct == 80  -> "a maioria" (50-80) e "quase todos" (≥80) empatam -> "a maioria"
_BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE = [
    ("poucos", 0, 10, False),
    ("alguns", 10, 25, True),
    ("muitos", 25, 50, True),
    ("cerca de metade", 40, 60, True),
    ("a maioria", 50, 80, True),
    ("quase todos", 80, 100, True),
]


def _fracao_percentual(mencoes: int, n_analisadas: int) -> int:
    """Fração mencoes/n_analisadas do grupo, em percentual arredondado
    (inteiro 0-100). n_analisadas <= 0 -> 0 (sem denominador válido)."""
    if not n_analisadas or n_analisadas <= 0:
        return 0
    return round(100 * mencoes / n_analisadas)


def _rotulo_quantificador(pct: int) -> str:
    """Resolve o rótulo determinístico para uma fração percentual (0-100).
    Ver bloco de comentário acima para a tabela de faixas e a resolução
    exata das fronteiras compartilhadas (sempre o rótulo mais fraco)."""
    for rotulo, lo, hi, hi_inclusive in _BANDAS_QUANTIFICADOR_FRACA_PARA_FORTE:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return rotulo
    return "quase todos"  # pct > 100 não deveria ocorrer; fallback seguro


def _fracao_e_rotulo(tema: dict) -> tuple[int, str]:
    """(fração%, rótulo) pré-computados para um tema (dict com as chaves
    mencoes_aproximadas/n_reviews_analisadas, como em output['buckets'][i]['temas'])."""
    pct = _fracao_percentual(
        tema.get("mencoes_aproximadas", 0) or 0,
        tema.get("n_reviews_analisadas", 0) or 0,
    )
    return pct, _rotulo_quantificador(pct)






# --- v1.4.1: telemetria POR PAR {quantificador, tema} ---
# Motivação (3ª ocorrência do mesmo modo de falha): na v1.4.0 a narrativa de
# `the-invite-2026` escreveu "Quase todos" para o tema "Atuações e química do
# elenco" (20/30 = 67%, rótulo pré-computado "a maioria"). A rede de
# segurança da v1.2.3 é de nível de BUCKET — ela só pergunta se ALGUM tema do
# filme tem fração >=80% — e outro tema do mesmo grupo tinha 83%, dando
# lastro. Nenhuma checagem via prosa consegue saber a QUAL tema um "quase
# todos" solto se refere; por isso o próprio narrador passa a DECLARAR o par,
# no mesmo padrão de `consensos_usados` (v1.3.1), e o código confere par a par
# contra o rótulo pré-computado. O LLM continua sem decidir número ou rótulo:
# ele só declara o que usou, e o código julga.












def conferencia_quantificador(output: dict, tema_nome: str) -> tuple[int, str] | None:
    """(fração%, rótulo pré-computado) do tema com esse nome exato, ou None se
    ele não existir no relatório. Usada pelo render para exibir, ao lado de
    cada par declarado, o número real contra o qual ele foi conferido —
    telemetria legível, não só um booleano de flag."""
    for b in output.get("buckets", []):
        for t in b.get("temas") or []:
            if str(t.get("tema", "")) == tema_nome:
                return _fracao_e_rotulo(t)
    return None


# --- Peso pré-computado por grupo (v1.4.0) ---
# MESMO princípio da v1.2.3 (quantificador) e da v1.1.1 (denominador): o LLM
# não escolhe o rótulo, o CÓDIGO escolhe. Aqui o insumo é o `share_real` do
# bucket (percentual inteiro vindo do histograma real), não a cota de coleta.
#
# Faixas na ordem do mais FRACO ao mais FORTE; cada uma é
# (rótulo, limite_inferior_inclusive, limite_superior, superior_inclusive).
# "uma pequena minoria" é a única com superior EXCLUSIVO (pct < 10).
#
# Resolução de fronteira (itera do mais fraco pro mais forte, primeiro match
# vence) — MESMA convenção da v1.2.3, "na dúvida, o rótulo mais fraco":
#   pct == 10 -> "uma minoria"            (pequena minoria exige pct < 10)
#   pct == 25 -> "uma minoria"            (empata com parcela expressiva)
#   pct == 45 -> "uma parcela expressiva" (empata com a maioria)
#   pct == 70 -> "a maioria"              (empata com a grande maioria)
# Nota: por isso "a grande maioria" começa de fato em 71%, não em 70% —
# subestimar o peso é aceitável, inflar não é.
# v1.6.0 — faixa NOVA no extremo fraco: "uma fração mínima" (<5%). Motivo
# (observado em `cidade-de-deus`, shares 91/8/1): 8% e 1% recebiam ambos
# "uma pequena minoria", achatando uma diferença de OITO VEZES entre os dois
# grupos minoritários. A faixa nova separa o "muito pouco" do "quase nada"
# sem tocar nas demais fronteiras. Convenção de desempate inalterada (itera
# do mais fraco ao mais forte, primeiro match vence => `pct == 5` resolve
# para "uma pequena minoria", o mais fraco dos dois que batem).
_BANDAS_PESO_FRACA_PARA_FORTE = [
    ("uma fração mínima", 0, 5, False),
    ("uma pequena minoria", 5, 10, False),
    ("uma minoria", 10, 25, True),
    ("uma parcela expressiva", 25, 45, True),
    ("a maioria", 45, 70, True),
    ("a grande maioria", 70, 100, True),
]


def _rotulo_peso(pct: int) -> str:
    """Rótulo determinístico para um share real (0-100)."""
    for rotulo, lo, hi, hi_inclusive in _BANDAS_PESO_FRACA_PARA_FORTE:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return rotulo
    return "a grande maioria"  # pct > 100 não deveria ocorrer; fallback seguro


def _rotulo_peso_completo(pct: int) -> str:
    """Forma como o narrador deve escrever: rótulo + percentual, sempre
    juntos — o percentual é o que impede o rótulo de virar retórica solta."""
    return f"{_rotulo_peso(pct)} das notas (~{pct}%)"


def _rotulos_ate(rotulo: str) -> list[str]:
    """O rótulo dado + todos os MAIS FRACOS que ele.

    O prompt permite descer de força ("a grande maioria" -> "a maioria") mas
    nunca subir; a checagem de ancoragem aceita exatamente esse conjunto.
    """
    ordem = [r for r, _, _, _ in _BANDAS_PESO_FRACA_PARA_FORTE]
    return ordem[: ordem.index(rotulo) + 1] if rotulo in ordem else [rotulo]


# --- Marcação de perspectiva pré-computada (v1.5.0) ---
# Motivação: a regra de REGISTRO (v1.5.0) reduz os verbos de reporte a no
# máximo 1 por movimento — mas isso tem um efeito colateral: a fala de um
# grupo minoritário, sem "eles apontam que", pode soar como fato do narrador,
# porque chega depois de o texto já ter estabelecido a leitura dominante. A
# marcação é pré-computada a partir do share_real (MESMO princípio das demais
# pré-computações do §D2: o LLM não decide o valor, só o usa) — depende do
# dado real, por isso só existe quando há distribuição (o mesmo motivo pelo
# qual não dá para usar a COTA de coleta aqui: usar 50/20/30 apresentaria a
# cota como se fosse prevalência, o exato defeito que a v1.2.1 proíbe).
#
# Limiares (ponto de partida, calibráveis — não há evidência empírica ainda
# que os justifique com precisão, ao contrário das faixas de quantificador/
# peso, que vieram de casos reais observados):
#   share > dominante/3   -> "nenhuma"     (grupo grande o bastante por si)
#   share <= dominante/3  -> "simples"     (1 marcador em algum lugar do trecho)
#   share <= dominante/10 -> "antecipada"  (marcador ANTES da 1ª afirmação)
# A condição mais restritiva (antecipada) é checada primeiro: um share que
# satisfaz dominante/10 também satisfaz dominante/3, e "antecipada" implica
# "simples" (o marcador continua lá, só que mais cedo).
def _dominante_share(pesos: dict[str, tuple[int, str]]) -> int | None:
    """Maior share_real entre os grupos com peso, ou None se `pesos` vazio
    (sem distribuição — não há o que ser dominante)."""
    if not pesos:
        return None
    return max(pct for pct, _rot in pesos.values())


def _marcacao_perspectiva(pct: int, dominante: int | None) -> str:
    """Classifica um grupo (nenhuma/simples/antecipada) a partir do seu
    share_real e do share_real do grupo dominante do filme."""
    if not dominante:  # None ou 0 -> nada é dominante o bastante para exigir
        return "nenhuma"
    if pct <= dominante / 10:
        return "antecipada"
    if pct <= dominante / 3:
        return "simples"
    return "nenhuma"


def _marcacoes_por_bucket(pesos: dict[str, tuple[int, str]]) -> dict[str, str]:
    """{bucket: marcacao_perspectiva} para os buckets que TÊM share real.
    Vazio quando `pesos` é vazio (sem distribuição) — mesmo padrão de
    `_pesos_por_bucket`: o vazio é o próprio fallback, sem flag extra."""
    dominante = _dominante_share(pesos)
    return {nome: _marcacao_perspectiva(pct, dominante)
            for nome, (pct, _rot) in pesos.items()}


def _pesos_por_bucket(output: dict) -> dict[str, tuple[int, str]]:
    """{bucket: (share_real, rótulo)} para os buckets que TÊM share real.

    Vazio quando a distribuição não foi coletada — e é esse vazio que faz o
    pipeline inteiro (prompt + validação + render) voltar ao comportamento
    da v1.2.1, sem nenhuma flag extra para checar.
    """
    pesos: dict[str, tuple[int, str]] = {}
    for b in output.get("buckets", []):
        share = b.get("share_real")
        if isinstance(share, int):
            pesos[b.get("bucket", "?")] = (share, _rotulo_peso(share))
    return pesos


def _ancoragem_de_peso_ok(texto: str, pesos: dict[str, tuple[int, str]]) -> bool:
    """True se TODO grupo com peso foi ancorado na prosa.

    Aceita, por grupo: o rótulo fornecido, qualquer rótulo mais fraco (o
    prompt permite), ou o percentual literal. Heurística deliberadamente
    permissiva — a defesa principal é a instrução; isto é rede de segurança
    para o caso de o narrador simplesmente ignorar os pesos e escrever a
    narrativa antiga, que é o modo de falha que importa detectar.

    v1.6.1 — bugfix: `f"{pct}%" in t` era substring solta, então "1%" batia
    DENTRO de "91%" — um grupo de 1% podia ser dado como ancorado só por
    coincidência com o percentual de outro grupo (91%), mascarando um
    `peso_nao_ancorado` real. Mesma causa raiz de `_ancora_de_grupo` (ver
    ali); agora exige que o dígito não seja precedido por outro dígito.
    """
    t = texto.lower()
    for pct, rotulo in pesos.values():
        if any(r in t for r in _rotulos_ate(rotulo)):
            continue
        if re.search(rf"(?<!\d){pct}%", t):
            continue
        return False
    return True


# --- v1.4.1: invariante de vocabulário do peso (notas × reviews) ---
# O rotulo_peso deriva do histograma de NOTAS (todos que avaliaram); os temas
# derivam das REVIEWS COM TEXTO (subconjunto). Dizer "a grande maioria das
# reviews" atribui ao peso um denominador que ele não tem — e é uma
# infidelidade barata de detectar.
_PESO_SUBSTANTIVOS_PROIBIDOS = ("reviews", "público", "publico", "espectadores")

# Rótulos que só podem ser peso. "a maioria" fica DE FORA porque também é um
# rótulo de quantificador de tema, e "a maioria das reviews negativas
# analisadas" é a forma CORRETA exigida pela regra (d) — flaggá-la marcaria
# prosa certa. O caso de "a maioria" usado como peso é coberto pela segunda
# passada, ancorada no percentual (que só acompanha peso).
_ROTULOS_PESO_INEQUIVOCOS = ("uma fração mínima", "uma pequena minoria",
                             "uma minoria", "uma parcela expressiva",
                             "a grande maioria")


def _janela_troca_notas_por_outro(janela: str) -> bool:
    """True se a janela usa um substantivo proibido ANTES de "notas" (ou sem
    "notas" nenhuma) — isto é, o peso foi atribuído a reviews/público/
    espectadores em vez de à população de notas."""
    pos_notas = janela.find("notas")
    for termo in _PESO_SUBSTANTIVOS_PROIBIDOS:
        pos = janela.find(termo)
        if pos != -1 and (pos_notas == -1 or pos < pos_notas):
            return True
    return False


def _vocabulario_peso_ok(texto: str, pesos: dict[str, tuple[int, str]]) -> bool:
    """True se todo rótulo de peso na prosa está acompanhado de "notas".

    Duas passadas complementares, ambas baratas e literais (não é NLP):
    1. rótulos INEQUÍVOCOS de peso -> olha os 40 chars seguintes;
    2. qualquer percentual (`~79%`) -> olha os 60 chars anteriores, o que pega
       "a maioria", ambígua com o quantificador de tema, sem falso positivo:
       frequência de tema nunca vem com percentual na prosa.
    Sem distribuição não há peso a expressar — vacuamente OK.
    """
    if not pesos:
        return True
    t = texto.lower()
    for rotulo in _ROTULOS_PESO_INEQUIVOCOS:
        for m in re.finditer(re.escape(rotulo), t):
            if _janela_troca_notas_por_outro(t[m.end():m.end() + 40]):
                return False
    for m in re.finditer(r"~?\d{1,3}\s?%", t):
        if _janela_troca_notas_por_outro(t[max(0, m.start() - 60):m.start()]):
            return False
    return True




# --- v1.3.1: telemetria/validação de consensos_usados (MOVIMENTO 2) ---









# --- v1.5.0: telemetria/validação de marcadores_perspectiva ---
# "Antecipada" na SPEC significa "antes da PRIMEIRA AFIRMAÇÃO SUBSTANTIVA
# sobre aquele grupo" — não antes do movimento inteiro. No exemplo de estilo
# do prompt, o marcador da minoria ("Para eles...") vem DEPOIS da frase que
# ANCORA o grupo ("Já uma pequena minoria (~3%) não entra na brincadeira"),
# só que na frase SEGUINTE — antes de qualquer afirmação de conteúdo sobre
# esse grupo. A checagem aproxima isso por FRASE (não por parágrafo): acha a
# frase onde o grupo é ancorado (rótulo de peso ou percentual) e exige que o
# marcador apareça naquela mesma frase ou na imediatamente seguinte.

def _ancora_de_grupo(texto: str, pct: int, rotulo: str) -> int | None:
    """Índice (char, minúsculas) da primeira menção ao rótulo de peso do
    grupo (ou um mais fraco — mesmo critério de `_ancoragem_de_peso_ok`) ou
    ao seu percentual. None se nada for encontrado.

    v1.6.1 — bugfix: a busca pelo percentual usava substring solta
    (`t.find(f"{pct}%")`), que casa "1%" DENTRO de "91%" — descoberto ao
    vivo no `cidade-de-deus` real (shares 1/8/91): a âncora de `negativas`
    (1%) "encontrava" o "1" final de "(~91%)" de `positivas`, muito antes
    da menção real, corrompendo o MOVIMENTO inteiro e produzindo falso
    positivo em `perspectiva_nao_marcada`. A busca agora exige que o
    percentual não seja precedido por outro dígito (`(?<!\\d)`), então "1%"
    só casa como número de fato, nunca como sufixo de "91%"/"21%"/etc.
    """
    t = texto.lower()
    candidatos = [t.find(r) for r in _rotulos_ate(rotulo) if t.find(r) != -1]
    m_pct = re.search(rf"(?<!\d){pct}%", t)
    if m_pct:
        candidatos.append(m_pct.start())
    return min(candidatos) if candidatos else None


def _indice_frase_de(frases: list[str], texto: str, idx_char: int) -> int | None:
    """Índice (0-based) da frase de `frases` (saída de `_dividir_frases`)
    que contém o caractere de posição `idx_char` no `texto` original —
    reconstrói offsets por busca sequencial, já que as frases preservam a
    ordem de aparição."""
    if idx_char is None:
        return None
    cursor = 0
    for i, f in enumerate(frases):
        pos = texto.find(f, cursor)
        if pos == -1:
            continue
        fim = pos + len(f)
        if pos <= idx_char <= fim:
            return i
        cursor = fim
    return None


def _span_de_movimento(texto: str, grupo: str,
                       pesos: dict[str, tuple[int, str]]) -> tuple[int, int] | None:
    """(início, fim) do trecho de `texto` associado a `grupo` (v1.6.1) — do
    ponto em que o grupo é ANCORADO (rótulo de peso ou percentual) até a
    âncora do PRÓXIMO grupo que aparece depois dele, ou o fim do texto.

    Aproximação do "movimento daquele grupo", no mesmo espírito de
    `_indice_frase_de`: os movimentos não têm marcação estrutural no texto
    final (o prompt proíbe subtítulos), então a fronteira é inferida pela
    ORDEM em que os grupos são ancorados — coerente com a regra do §D2 de
    que o MOVIMENTO 3 segue a ordem de peso. None se o grupo não tiver peso
    ou não estiver ancorado no texto (nesse caso `_ancoragem_de_peso_ok`,
    checagem separada, já cobre o defeito)."""
    if grupo not in pesos:
        return None
    pct, rotulo = pesos[grupo]
    inicio = _ancora_de_grupo(texto, pct, rotulo)
    if inicio is None:
        return None
    seguintes = [
        idx for g, (p, r) in pesos.items() if g != grupo
        for idx in [_ancora_de_grupo(texto, p, r)]
        if idx is not None and idx > inicio
    ]
    fim = min(seguintes) if seguintes else len(texto)
    return inicio, fim


# Expressões de atribuição de perspectiva (§D2). São elas que carregam o
# sentido "isto é a leitura DAQUELE grupo" — o resto do período declarado é
# conteúdo comum, que o editor precisa poder reescrever.
_EXPRESSOES_DE_PERSPECTIVA = (
    "quem está nessa faixa", "quem está nesta faixa",
    "para esse grupo", "para este grupo", "neste grupo", "nesse grupo",
    "para esse público", "para este público", "esse público", "este público",
    "nessa leitura", "nesta leitura", "para esses", "para estes",
    "para eles", "para elas",
    # v1.7.1 (Tarefa 3) — família "quem gostou/não gostou/amou/...": caso
    # real do `cure`, grupo de 3% ("quem não gostou considerou o ritmo
    # lento e tedioso") — a construção CUMPRE a função de atribuição, só
    # não estava na lista, e produzia falso positivo em
    # `perspectiva_nao_marcada` mesmo com o texto honesto e bem marcado.
    "quem gostou", "quem não gostou", "quem amou", "quem ficou no meio",
    "para quem gostou", "para quem não gostou",
    # "para quem" ISOLADO ficou DE FORA de propósito: é pronome relativo
    # comum ("para quem o filme é superestimado…") e casava dentro da
    # própria frase agramatical do `cure`, blindando o defeito que o editor
    # tem de consertar. Todo item acima exige uma palavra a mais depois de
    # "quem" — nunca casa com esse uso solto.
)


def _ocorrencias_de_atribuicao(texto: str, inicio: int, fim: int) -> list[int]:
    """Índices ABSOLUTOS (no `texto` completo) de toda ocorrência de uma
    expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`)
    dentro de `texto[inicio:fim]`, busca case-insensitive."""
    janela = texto[inicio:fim].lower()
    ocorrencias = []
    for e in _EXPRESSOES_DE_PERSPECTIVA:
        pos = 0
        while True:
            i = janela.find(e, pos)
            if i == -1:
                break
            ocorrencias.append(inicio + i)
            pos = i + len(e)
    return sorted(ocorrencias)


def _marcadores_validos(marcadores: list, texto: str,
                        marcacoes: dict[str, str],
                        pesos: dict[str, tuple[int, str]]) -> bool:
    """True se, para TODO grupo com `marcacao_perspectiva != "nenhuma"`: (a)
    o MOVIMENTO daquele grupo (§`_span_de_movimento`) contém alguma
    expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`); (b)
    para `marcacao_perspectiva == "antecipada"`, PELO MENOS UMA dessas
    ocorrências aparece na mesma frase em que o grupo é ancorado (rótulo de
    peso/percentual) ou na imediatamente seguinte. Vacuamente válido quando
    `marcacoes` é vazio (sem distribuição) ou nenhum grupo exige marcação.

    `marcadores` (o que o LLM DECLAROU em `marcadores_perspectiva`) não
    participa mais desta checagem — ver `_normalizar_marcadores`, que
    continua persistindo a declaração como TELEMETRIA de auditoria humana,
    e o changelog v1.6.1 para o porquê.

    **v1.6.1 — por que a checagem passou a escanear o TEXTO, não o
    `trecho` declarado:** a v1.6.0 já tinha corrigido dois defeitos aqui
    (bastar UM marcador bem posicionado por grupo; normalizar caixa/acento/
    demonstrativo antes de comparar), mas um caso real do `cidade-de-deus`
    continuou dando falso positivo mesmo depois: o narrador declarou
    *"Para esse grupo, muitos reconhecem…"* e escreveu na prosa *"Muitos
    NESTE grupo reconhecem…"* — divergência de ORDEM DAS PALAVRAS, não de
    grafia, que nenhuma normalização de caixa/acento fecha. Fechar por
    comparação difusa (similaridade com limiar) foi descartado: um limiar é
    uma linha arbitrária, e a checagem existe para confirmar que o marcador
    de perspectiva EXISTE no texto — não que a frase declarada é uma
    transcrição fiel dele. A correção pela raiz é verificar exatamente essa
    existência: procurar, no trecho de texto associado ao grupo, qualquer
    expressão da MESMA lista que `montar_protegidos` já usa para reconhecer
    atribuição (`_EXPRESSOES_DE_PERSPECTIVA`) — fonte única, sem duplicação.
    """
    frases = _dividir_frases(texto)
    for grupo, marcacao in marcacoes.items():
        if marcacao == "nenhuma":
            continue
        span = _span_de_movimento(texto, grupo, pesos)
        if span is None:
            return False
        ocorrencias = _ocorrencias_de_atribuicao(texto, *span)
        if not ocorrencias:
            return False
        if marcacao == "antecipada":
            pct, rotulo = pesos[grupo]
            si_ancora = _indice_frase_de(
                frases, texto, _ancora_de_grupo(texto, pct, rotulo))
            cedo = any(
                si_ancora is not None
                and _indice_frase_de(frases, texto, idx) in (si_ancora, si_ancora + 1)
                for idx in ocorrencias
            )
            if not cedo:
                return False
    return True




# --- v1.5.0: telemetria de fluência (pós-parsing, código) ---
# Diagnóstico (registrado no changelog): o acúmulo de invariantes de
# honestidade (peso ancorado, quantificador pré-computado, escopo por
# grupo...) levou o modelo à ÚNICA forma sintática que satisfaz todas
# simultaneamente — rótulo de peso + verbo de reporte + complemento,
# repetida três vezes, frases de 25-35 palavras quase sem variação. As
# métricas abaixo tornam esse padrão MENSURÁVEL: o código não reescreve a
# prosa, só mede e sinaliza — mesma filosofia das demais telemetrias do §D2.

_VERBOS_REPORTE_STEMS = (
    "elogi", "destac", "apont", "relat", "consider", "classific",
    "mencion", "ressalt", "reconhec", "express", "descrev",
)
_RE_VERBO_REPORTE = re.compile(
    r"\b(?:" + "|".join(_VERBOS_REPORTE_STEMS) + r")\w*", re.IGNORECASE)

# Lista fechada e literal (não é NLP) — os quatro exemplos da regra (h) mais
# sinônimos comuns da mesma família de intensificador. Deliberadamente NÃO
# cobre todo advérbio em -mente (ex. "praticamente"/"geralmente" não são
# intensificadores) — heurística restrita, como as demais do módulo.
_ADVERBIOS_INTENSIFICADORES = {
    "intensamente", "profundamente", "extremamente", "excessivamente",
    "totalmente", "completamente", "absolutamente", "imensamente",
    "tremendamente", "surpreendentemente", "extraordinariamente",
    "impressionantemente", "brutalmente", "fortemente",
}

_RE_FRASE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
_RE_PALAVRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def _dividir_frases(texto: str) -> list[str]:
    """Divisão simples por pontuação de fim de frase (.!?) — heurística, não
    trata abreviações; suficiente para telemetria de estilo, propositalmente
    imperfeita como o resto do módulo."""
    return [f.strip() for f in _RE_FRASE.findall(texto) if f.strip()]


def _n_palavras(frase: str) -> int:
    return len(_RE_PALAVRA.findall(frase))


def _primeira_palavra(frase: str) -> str:
    m = _RE_PALAVRA.search(frase)
    return m.group(0).lower() if m else ""


def _metricas_fluencia(texto: str) -> dict:
    """Calcula as métricas de ritmo sobre o texto final da narrativa.

    `cv_comprimento` = desvio padrão ÷ média de palavras por frase — mede
    VARIAÇÃO de comprimento (a regra de ritmo pede variação, não frases
    curtas o tempo todo). `aberturas_repetidas` conta pares de frases
    CONSECUTIVAS que começam pela mesma primeira palavra (normalizada,
    minúscula) — proxy barato para "mesma estrutura de abertura" (regra b),
    não uma análise sintática real.
    """
    frases = _dividir_frases(texto)
    n_frases = len(frases)
    if n_frases == 0:
        return {
            "n_frases": 0, "media_palavras": 0.0, "cv_comprimento": 0.0,
            "frase_mais_curta": 0, "aberturas_repetidas": 0,
            "verbos_reporte": 0, "adverbios_mente": 0,
        }
    comprimentos = [_n_palavras(f) for f in frases]
    media = sum(comprimentos) / n_frases
    variancia = sum((c - media) ** 2 for c in comprimentos) / n_frases
    desvio = variancia ** 0.5
    cv = (desvio / media) if media > 0 else 0.0

    aberturas = [_primeira_palavra(f) for f in frases]
    aberturas_repetidas = sum(
        1 for i in range(1, n_frases)
        if aberturas[i] and aberturas[i] == aberturas[i - 1]
    )

    palavras_lower = [w.lower() for w in _RE_PALAVRA.findall(texto)]
    adverbios_mente = sum(1 for w in palavras_lower
                          if w in _ADVERBIOS_INTENSIFICADORES)
    verbos_reporte = len(_RE_VERBO_REPORTE.findall(texto))

    return {
        "n_frases": n_frases,
        "media_palavras": round(media, 1),
        "cv_comprimento": round(cv, 2),
        "frase_mais_curta": min(comprimentos),
        "aberturas_repetidas": aberturas_repetidas,
        "verbos_reporte": verbos_reporte,
        "adverbios_mente": adverbios_mente,
    }


# v1.6.0 — `_fluencia_ok` REMOVIDA, e com ela os gatilhos automáticos de
# retentativa por métrica e a flag `fluencia_baixa`.
#
# Motivo (DIAGNOSTICO_FLUENCIA_V2.md): as métricas NÃO acompanham qualidade.
# No `cure`, o texto qualitativamente melhor (thinking on) pontuou PIOR em
# `cv_comprimento` (0.35 -> 0.28) e em `verbos_reporte` (3 -> 6) que o texto
# pior. `cv_comprimento` mede DISPERSÃO de comprimento de frase, não
# legibilidade: um texto com frases uniformemente boas pontua mal, e um texto
# truncado no meio pontua bem. Otimizar contra elas — que é o que uma
# retentativa automática faz — empurra o modelo a degradar a prosa para
# satisfazer um número.
#
# `_metricas_fluencia` continua sendo calculada e persistida em
# `metricas_fluencia`: vira telemetria de DIAGNÓSTICO para leitura humana,
# no mesmo estatuto de `consensos_usados` — material de revisão, não critério
# automático. O eixo de fluência passa a ser responsabilidade do editor (§E2).


def _validar_prosa(texto: str, com_distribuicao: bool = False
                   ) -> tuple[str, bool, bool, bool, bool]:
    """Aplica as validações do §D que fazem sentido para prosa livre:
    remoção mecânica de aspas + checagem de idioma, escopo e prevalência (v1.2.1).
    Retorna (texto_limpo, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas).

    v1.4.0 — a checagem de PREVALÊNCIA muda de sinal conforme o dado:
    - SEM distribuição: como na v1.2.1, palavras como "minoria"/"a maioria do
      público" são violação (o dado que as justificaria não existe).
    - COM distribuição: essas mesmas palavras passam a ser EXIGIDAS pela
      regra (c) invertida — manter o detector ligado geraria flag em toda
      narrativa correta. Ele é desligado, e quem cobre este eixo passa a ser
      a checagem de ANCORAGEM (`_ancoragem_de_peso_ok`), aplicada em
      `narrate_output`.
    """
    limpo, aspas_removidas = _remover_aspas(texto)
    idioma_ok = _idioma_e_pt_br(limpo)
    escopo_ok = not _tem_marcador_de_escopo(limpo)
    prevalencia_ok = (True if com_distribuicao
                      else not _tem_marcador_de_prevalencia(limpo))
    return limpo, idioma_ok, escopo_ok, prevalencia_ok, aspas_removidas




# =====================================================================
# [E2] Editor — APOSENTADO na v1.9.10, ver SPEC.md
# =====================================================================
# Rodou de v1.6.0 até v1.9.9 como o passe de EDIÇÃO pós-narrador. Aposentado
# depois de o dono do projeto ler as narrativas do best-of-3 (v1.9.9) sem
# editor e concluir que o ritmo se sustenta sem o estágio: deletar o estágio
# deleta de uma vez as suas três classes de falha (4 tentativas descartadas
# em `cure`, v1.7.1; parágrafo de opinião inventado em `the-invite-2026`,
# v1.8.0; inversão de movimentos, v1.8.0).
#
# Código movido para `experimentos-editor-e2-arquivado/editor.py` — arquivado,
# não deletado, no padrão de `experimentos-ollama-arquivado/`. `EdicaoResult`
# saiu de `models.py`; as constantes `EDITOR_*` saíram de `config.py`. O
# módulo arquivado ainda importa um punhado de funções PRIVADAS deste arquivo
# (`_resolve_call_and_model`, `_pesos_por_bucket`, `_marcadores_validos`,
# `_validar_prosa`, `_dividir_frases`, `_metricas_fluencia`, entre outras) —
# deliberado: são a maquinaria de honestidade do narrador ANTIGO, ainda em
# uso aqui, e duplicá-la no arquivo criaria duas fontes de verdade para a
# MESMA checagem.
