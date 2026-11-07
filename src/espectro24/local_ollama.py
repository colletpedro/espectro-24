"""Provider `local`: um modelo servido pelo Ollama (API nativa `/api/chat`).

**Por que existe (2026-10-08).** Os créditos de DeepSeek e Gemini acabaram. Um
notebook Windows serve um modelo local e roda as rodadas longas. Este módulo é
SÓ o adaptador — como `resposta_json_gemini`, é uma exceção ESCOPADA:
`config.PROVIDER_POR_ESTAGIO` não é tocado, e nada de produção chama `local`
sem pedir (hoje, só `scripts/gate_gemini_classificacao.py --provider local`).

**O que o adaptador garante.**
- Saída FORÇADA por JSON schema (`format` do Ollama): a gramática restringe a
  geração, então JSON inválido deixa de ser um modo de falha — o que sobra é
  prazo estourado e servidor fora do ar. `schema_classificacao` e
  `SCHEMA_VERIFICADOR` são os dois formatos que o projeto pede.
- Custo SEMPRE zero (`custo_usd == 0.0`), gravado — para a tabela de custo
  dos relatórios continuar somando sem caso especial.
- Tempo gravado por chamada, com leitura do prompt separada da geração
  (`leitura_prompt_s`, `geracao_s`, mais `carga_s` do modelo e `total_s`), lido
  dos campos em nanossegundos que a API nativa devolve. Chamada que FALHA
  também leva a latência de parede (`LLMLocalFalhou.latencia_s`).
- `provider` e `modelo_efetivo` (o `model` devolvido pelo servidor, não o
  pedido) em cada registro — a lição da C21.
- `leitura_prompt_s` é o SINAL do reaproveitamento do prefixo: com o prefixo
  fixo (o system prompt, 929 tokens) no cache de KV, o tempo de leitura do
  prompt cai (medido no notebook: ~23 s na 1ª chamada, ~1,2 s nas seguintes).
  `prompt_eval_count` NÃO serve de sinal — o Ollama o reporta com o prompt
  inteiro, reaproveitado ou não.

**Reaproveitamento de prefixo.** O Ollama guarda o KV da última requisição e
reaproveita o prefixo idêntico da seguinte. Por isso o chamador deve fazer
chamadas EM SEQUÊNCIA (uma por vez) e agrupar por system prompt: todas as
classificações, depois todos os verificadores. Com `OLLAMA_NUM_PARALLEL=1` no
servidor, não há outro slot para desfazer o prefixo.

**Configuração (variáveis de ambiente).**
- `ESPECTRO24_OLLAMA_URL` — padrão `http://localhost:11434` (o Ollama no
  próprio notebook). Aceita também `OLLAMA_HOST` (a variável do próprio
  Ollama, com ou sem `http://`) se a primeira não existir.
- `ESPECTRO24_OLLAMA_PRAZO_S` — prazo por chamada, padrão 600 s (ver
  `PRAZO_PADRAO_S`).
- `ESPECTRO24_OLLAMA_NUM_CTX` — janela de contexto, padrão 8192 (o padrão do
  Ollama, 2048, truncaria prefixo + review longa em silêncio).
- `ESPECTRO24_OLLAMA_TEMPERATURE` — opcional; ausente = padrão do modelo
  (os outros providers também não fixam temperatura).
- `ESPECTRO24_OLLAMA_THINK` — nível de raciocínio: `false` (padrão), `low`,
  `medium` ou `high`. Ver `nivel_think`.
- `ESPECTRO24_OLLAMA_NUM_PREDICT` — teto de saída, padrão 2000 (o mesmo do
  Gemini, `FALLBACK_CONTEUDO_MAX_TOKENS_JSON`).
"""
from __future__ import annotations

import os
import time

import requests

from .config import FALLBACK_CONTEUDO_MAX_TOKENS_JSON
from .synthesize import LLMError, _registrar_latencia_llm

PROVIDER = "local"
URL_PADRAO = "http://localhost:11434"

# Prazo por chamada. A nuvem usa 90 s (`LLM_TIMEOUT_MS`); na CPU de um
# notebook, um modelo de 7-8 B lê o prompt a ~20-50 tokens/s e gera a ~3-8
# tokens/s, então uma review longa (~1.500 tokens) leva de 1 a 2 minutos e a
# PRIMEIRA chamada soma a carga do modelo e a leitura inicial dos 929 tokens
# do prefixo. Um modelo de 14 B dobra ou triplica isso. 600 s dá ~5x de folga
# sobre o pior caso estimado e ainda corta uma chamada travada em 10 minutos
# (contra 2% de falha como critério de parada do gate: prazo curto demais
# viraria "falha" que é do hardware, não do modelo). A primeira rodada deve
# conferir `total_s` máximo nos registros e ajustar.
PRAZO_PADRAO_S = 600.0
PRAZO_CONEXAO_S = 10.0
NUM_CTX_PADRAO = 8192
KEEP_ALIVE = "30m"


class LLMLocalFalhou(LLMError):
    """A chamada ao Ollama não devolveu uma resposta aproveitável (servidor
    fora do ar, prazo estourado, HTTP de erro, corpo ilegível). Carrega a
    latência de parede até a falha: tempo se grava SEMPRE."""

    def __init__(self, mensagem: str, latencia_s: float):
        super().__init__(mensagem)
        self.latencia_s = round(latencia_s, 2)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

def schema_classificacao(eixos_validos) -> dict:
    """`{"eixos": [...], "temas_livres": [...]}` — o formato do prompt de
    classificação (`classificar_10.SYSTEM`). `eixos_validos` é o conjunto de
    `classificar_10.EIXOS_VALIDOS` (eixos + `livre`): com `enum`, o servidor
    não consegue emitir um eixo fora da taxonomia. A ordem é determinística
    (o schema entra na chave de cache do prompt)."""
    return {
        "type": "object",
        "properties": {
            "eixos": {"type": "array",
                      "items": {"type": "string", "enum": sorted(eixos_validos)}},
            "temas_livres": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["eixos", "temas_livres"],
    }


# `{"alvo": ..., "confirma": ..., "frase": ...}` — o formato de
# `verificador_impacto.SYSTEM_V2_ALVO`, na ordem em que o prompt o escreve.
SCHEMA_VERIFICADOR = {
    "type": "object",
    "properties": {
        "alvo": {"type": "string", "enum": ["espectador", "filme"]},
        "confirma": {"type": "boolean"},
        "frase": {"type": "string"},
    },
    "required": ["alvo", "confirma", "frase"],
}


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

def url_base() -> str:
    url = (os.environ.get("ESPECTRO24_OLLAMA_URL")
           or os.environ.get("OLLAMA_HOST") or URL_PADRAO).strip()
    if "://" not in url:
        url = "http://" + url
    return url.rstrip("/")


def prazo_s() -> float:
    bruto = os.environ.get("ESPECTRO24_OLLAMA_PRAZO_S")
    return float(bruto) if bruto else PRAZO_PADRAO_S


NIVEIS_THINK = ("false", "low", "medium", "high")


def nivel_think() -> str:
    """O nível de `think` pedido, de `ESPECTRO24_OLLAMA_THINK` (padrão
    `false`). Documentação do Ollama (docs.ollama.com/capabilities/thinking,
    conferida em 2026-10-10): `think` aceita booleano ou, nos modelos que
    declaram níveis, "low"/"medium"/"high". O `gpt-oss` NÃO tem como ser
    desligado — `false` não o desliga, ele espera um dos três níveis — e
    qwen3/mistral seguem com `false`. Valor fora da lista é erro, não
    fallback silencioso."""
    bruto = (os.environ.get("ESPECTRO24_OLLAMA_THINK") or "false").strip().lower()
    if bruto not in NIVEIS_THINK:
        raise ValueError(f"ESPECTRO24_OLLAMA_THINK={bruto!r} inválido — "
                         f"use um de {', '.join(NIVEIS_THINK)}")
    return bruto


def _opcoes(num_predict: int | None = None, num_ctx: int | None = None,
            seed: int | None = None, amostragem: dict | None = None) -> dict:
    """`amostragem` (temperature, top_p, top_k, min_p, repeat_penalty...) vai
    inteira para `options` e sobrepõe o ambiente."""
    op = {"num_ctx": num_ctx or int(os.environ.get("ESPECTRO24_OLLAMA_NUM_CTX")
                                    or NUM_CTX_PADRAO),
          "num_predict": num_predict or int(
              os.environ.get("ESPECTRO24_OLLAMA_NUM_PREDICT")
              or FALLBACK_CONTEUDO_MAX_TOKENS_JSON)}
    temp = os.environ.get("ESPECTRO24_OLLAMA_TEMPERATURE")
    if temp:
        op["temperature"] = float(temp)
    op.update(amostragem or {})
    if seed is not None:
        op["seed"] = int(seed)
    return op


def _s(ns) -> float:
    return round((ns or 0) / 1e9, 3)


# ---------------------------------------------------------------------------
# Chamada
# ---------------------------------------------------------------------------

def resposta_json_local(system: str, user: str, *, estagio: str, modelo: str,
                        schema: dict | str, prazo: float | None = None,
                        num_predict: int | None = None,
                        num_ctx: int | None = None, think: str | None = None,
                        seed: int | None = None, amostragem: dict | None = None) -> dict:
    """Uma chamada de JSON CURTO sobre UMA review no Ollama.

    Devolve o mesmo formato de `resposta_json_gemini` (`texto`, `provider`,
    `modelo`, `modelo_efetivo`, `uso`, `thinking_tokens`, `finish_reason`,
    `camada`, `motivo_camada`, `traffic_type`, `latencia_s`), mais
    `custo_usd`, `leitura_prompt_s`, `geracao_s`, `carga_s`, `total_s`,
    `prompt_eval_count` e `eval_count`. Levanta `LLMLocalFalhou` (com a
    latência) se não houver resposta.

    `schema` é um JSON schema (classificação, verificador) ou a string
    `"json"` (modo JSON livre do Ollama — as etapas de PROSA, cuja forma é
    validada pelos extratores de sempre, não por gramática). `num_predict` e
    `num_ctx` sobrepõem o ambiente (a prosa precisa de teto e janela maiores).

    `think`: `false` por padrão (ver `nivel_think` para os outros níveis; o
    nível usado vai em `think` no retorno, `"omitido"` se o servidor recusou
    o campo). `think`, `seed` e `amostragem` explícitos sobrepõem o ambiente — para quem
    precisa fixar a configuração no código (o juiz v2 dos bullets, cuja
    configuração inteira entra num hash). Com `false`, um modelo com "raciocínio" (família qwen3, deepseek-r1)
    gastaria o teto de saída pensando — na CPU, minutos por chamada — e a
    saída forçada por schema nem o deixa escrever o pensamento. Modelo sem
    esse recurso ignora o campo; se o servidor o recusar (400), a chamada é
    refeita uma vez sem ele."""
    if think is None:
        nivel = nivel_think()
    elif think in NIVEIS_THINK:
        nivel = think
    else:
        raise ValueError(f"think={think!r} inválido — use um de {', '.join(NIVEIS_THINK)}")
    corpo = {"model": modelo, "stream": False, "keep_alive": KEEP_ALIVE,
             "format": schema, "think": False if nivel == "false" else nivel,
             "options": _opcoes(num_predict, num_ctx, seed, amostragem),
             "messages": [{"role": "system", "content": system},
                          {"role": "user", "content": user}]}
    limite = prazo if prazo is not None else prazo_s()
    url = f"{url_base()}/api/chat"
    t0 = time.monotonic()

    def post(c: dict) -> requests.Response:
        return requests.post(url, json=c, timeout=(PRAZO_CONEXAO_S, limite))

    try:
        r = post(corpo)
        if r.status_code == 400 and "think" in r.text.lower():
            corpo.pop("think")
            nivel = "omitido"
            r = post(corpo)
        if r.status_code != 200:
            raise LLMLocalFalhou(
                f"HTTP {r.status_code} de {url}: {r.text[:300]}",
                time.monotonic() - t0)
        dados = r.json()
        if not isinstance(dados, dict) or "message" not in dados:
            raise ValueError(f"corpo sem 'message': {str(dados)[:200]}")
    except LLMLocalFalhou:
        raise
    except requests.Timeout as e:
        raise LLMLocalFalhou(
            f"prazo de {limite:.0f}s estourado ({type(e).__name__})",
            time.monotonic() - t0) from e
    except (requests.RequestException, ValueError) as e:
        raise LLMLocalFalhou(f"{type(e).__name__}: {e}",
                             time.monotonic() - t0) from e

    dt = time.monotonic() - t0
    _registrar_latencia_llm(estagio, dt)
    n_in = int(dados.get("prompt_eval_count") or 0)
    n_out = int(dados.get("eval_count") or 0)
    return {
        "texto": (dados.get("message") or {}).get("content") or "",
        "provider": PROVIDER, "modelo": modelo,
        "modelo_efetivo": dados.get("model"),
        "uso": {"prompt_tokens": n_in, "completion_tokens": n_out},
        "thinking_tokens": 0,
        "finish_reason": dados.get("done_reason"),
        "camada": "local", "motivo_camada": None, "traffic_type": None,
        "latencia_s": round(dt, 2),
        "custo_usd": 0.0, "think": nivel,
        "leitura_prompt_s": _s(dados.get("prompt_eval_duration")),
        "geracao_s": _s(dados.get("eval_duration")),
        "carga_s": _s(dados.get("load_duration")),
        "total_s": _s(dados.get("total_duration")),
        "prompt_eval_count": n_in, "eval_count": n_out,
        # O raciocínio que o servidor devolve à parte (`message.thinking`,
        # gpt-oss com think ligado); `None` quando não há.
        "pensamento": (dados.get("message") or {}).get("thinking") or None,
    }


def modelos_instalados() -> list[str]:
    """Nomes que o servidor tem (`/api/tags`) — para o gate falhar CEDO e com
    mensagem clara quando o modelo pedido não foi baixado."""
    r = requests.get(f"{url_base()}/api/tags", timeout=(PRAZO_CONEXAO_S, 30))
    r.raise_for_status()
    return [m["name"] for m in r.json().get("models", [])]
