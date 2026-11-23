"""Síntese de PRODUÇÃO pelo modelo local (`espectro-qwen3-8b-treinado`, via Ollama).

Decisão de produto do dono (2026-11-23, registrada em `finetune/FINETUNE_REGISTRO.md`):
a síntese gerada por este modelo pode ser publicada pelo MESMO gate dos filmes da
Featherless — validadores mecânicos + guarda de quantidade em código + leitura do dono;
o juiz fica FORA do gate. O veredito da Fase 4 ("não publicável pelos critérios
pré-registrados": C1 e C3) continua como está; isto é uma política nova, não uma
aprovação retroativa.

Este módulo é só o ADAPTADOR de síntese (`(system, user, model) -> str`, o contrato de
`synthesize.PROVIDER_CLIENTS`). O prompt, a retentativa de produção, os validadores e a
guarda de quantidade são os de `synthesize_bucket`, sem tocar neles. O que o adaptador fixa:

- **Modelo pelo sha do GGUF** (`GGUF_SHA256`, `e488697e…`), não pelo nome: o nome no Ollama é
  um rótulo que o `ollama create` sobrescreve. O sha vem do `FROM …/blobs/sha256-<hex>` do
  `modelfile` que `/api/show` devolve. Sem modelo com esse sha, a chamada recusa.
- **Amostragem do DESVIO_P01** em CADA chamada (temperature 0,7, top_p 0,8, top_k 20,
  min_p 0, repeat_penalty 1,0), seed 20261019, `think` false, JSON livre (`format: "json"`),
  teto de saída 3.000. `ESPECTRO24_OLLAMA_TEMPERATURE` no ambiente é recusada.
- **`num_ctx` por chamada** pela regra do gate 0: (tokens do prompt + 3.000) × 1,10, arredondado
  para cima em múltiplos de 1.024. Tokens: o tokenizer do Qwen3 se `ESPECTRO24_TOKENIZER_JSON`
  apontar para o `tokenizer.json` e `tokenizers` estiver instalado (exato); senão uma estimativa
  CONSERVADORA de 1 token a cada 2,8 caracteres (MEDIDO: nos 105 prompts do C22 a razão
  caracteres/token foi de 2,96 no mínimo, média 3,79; a estimativa só superestima o `num_ctx`).
  `ESPECTRO24_LOCAL_NUM_CTX` fixa o valor e dispensa a conta.
- **Registro por chamada** em `REGISTRO` (modelo pedido, efetivo, sha conferido, `num_ctx`,
  tempos, tokens, `finish_reason`), para o relatório do piloto.

Não faz: guarda de latência, monitor de RAM nem partida limpa do servidor — essas vivem nos
scripts de `finetune/` (Windows) e ficam com quem roda a rodada.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import threading
from datetime import datetime, timezone

import requests

from . import local_ollama as L

PROVIDER = "local"
MODELO_PADRAO = "espectro-qwen3-8b-treinado"
GGUF_SHA256 = "e488697e7215f12c35c7fdfe9206a5af4438bfe47512a91a8698ad98cdcd6eac"

# DESVIO_P01.md — os valores do model card do Qwen3-8B para o modo sem raciocínio.
AMOSTRAGEM = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
              "repeat_penalty": 1.0}
SEED = 20261019
TETO_SAIDA = 3000
MARGEM = 0.10
PASSO_CTX = 1024
CARACTERES_POR_TOKEN_CONSERVADOR = 2.8
VAR_TEMPERATURA = "ESPECTRO24_OLLAMA_TEMPERATURE"
VAR_NUM_CTX = "ESPECTRO24_LOCAL_NUM_CTX"
VAR_TOKENIZER = "ESPECTRO24_TOKENIZER_JSON"
VAR_GGUF_SHA = "ESPECTRO24_LOCAL_GGUF_SHA256"

REGISTRO: list[dict] = []
_cache_modelo: dict[tuple[str, str], tuple[str, bool]] = {}
_cache_tokenizer: dict[str, object] = {}
_trava = threading.Lock()


class ModeloLocalIndisponivel(L.LLMLocalFalhou):
    """Nenhum modelo do servidor tem o sha esperado (ou a configuração é recusada)."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem, 0.0)


def sha_esperado() -> str:
    sha = (os.environ.get(VAR_GGUF_SHA) or GGUF_SHA256).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ModeloLocalIndisponivel(f"{VAR_GGUF_SHA} não é um sha256 hexadecimal de 64 dígitos")
    return sha


def sha_do_modelfile(modelfile: str) -> str | None:
    """O sha256 do GGUF (blob) no `FROM` de um `modelfile` do Ollama, no Windows ou no Linux."""
    for linha in (modelfile or "").splitlines():
        if linha.strip().upper().startswith("FROM"):
            m = re.search(r"sha256[-:]([0-9a-fA-F]{64})", linha)
            if m:
                return m.group(1).lower()
    return None


def _sha_do_modelo(nome: str) -> str | None:
    r = requests.post(f"{L.url_base()}/api/show", json={"model": nome},
                      timeout=(L.PRAZO_CONEXAO_S, 30))
    if r.status_code != 200:
        return None
    return sha_do_modelfile(r.json().get("modelfile") or "")


def modelo_pelo_sha(sha: str | None = None) -> str:
    """O nome no Ollama do modelo cujo GGUF tem este sha256. Entre vários nomes para o mesmo
    GGUF, vale `MODELO_PADRAO` se estiver entre eles, senão o primeiro por ordem alfabética."""
    sha = sha or sha_esperado()
    try:
        nomes = L.modelos_instalados()
        achados = sorted(n for n in nomes if _sha_do_modelo(n) == sha)
    except (requests.RequestException, ValueError) as e:
        raise L.LLMLocalFalhou(f"não consegui listar os modelos de {L.url_base()}: "
                               f"{type(e).__name__}: {e}", 0.0) from e
    if not achados:
        raise ModeloLocalIndisponivel(
            f"nenhum modelo de {L.url_base()} tem o GGUF {sha[:8]}… "
            f"(instalados: {', '.join(nomes) or 'nenhum'})")
    for n in achados:
        if n.split(":")[0] == MODELO_PADRAO:
            return n
    return achados[0]


def resolver_modelo(pedido: str | None) -> tuple[str, bool]:
    """(nome a chamar, sha conferido). `pedido` igual ao padrão (ou vazio) → o modelo é o do
    sha do GGUF. Outro nome (`--model`) é usado como está e sai marcado `sha conferido = False`."""
    if pedido and pedido.split(":")[0] != MODELO_PADRAO:
        return pedido, False
    chave = (L.url_base(), sha_esperado())
    with _trava:
        if chave not in _cache_modelo:
            _cache_modelo[chave] = (modelo_pelo_sha(chave[1]), True)
        return _cache_modelo[chave]


def _tokenizer():
    caminho = os.environ.get(VAR_TOKENIZER)
    if not caminho:
        return None
    if caminho not in _cache_tokenizer:
        try:
            from tokenizers import Tokenizer
            _cache_tokenizer[caminho] = Tokenizer.from_file(caminho)
        except Exception as e:  # sem `tokenizers` ou arquivo ilegível: cai na estimativa
            raise ModeloLocalIndisponivel(
                f"{VAR_TOKENIZER}={caminho} não carregou: {type(e).__name__}: {e}") from e
    return _cache_tokenizer[caminho]


def _chat_qwen(system: str, user: str) -> str:
    """O texto do turno do usuário como o template do Qwen3 o monta, com o raciocínio
    desligado (o mesmo de `scripts/finetune/comum.chat`)."""
    return (f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n"
            f"<|im_start|>assistant\n<think>\n\n</think>\n\n")


def tokens_do_prompt(system: str, user: str) -> tuple[int, str]:
    """(tokens, método): `exato` com o tokenizer, `estimado` sem ele (conservador)."""
    tok = _tokenizer()
    texto = _chat_qwen(system, user)
    if tok is not None:
        return len(tok.encode(texto, add_special_tokens=False).ids), "exato"
    return math.ceil(len(texto) / CARACTERES_POR_TOKEN_CONSERVADOR), "estimado"


def num_ctx_da_chamada(tokens_prompt: int) -> int:
    bruto = int((tokens_prompt + TETO_SAIDA) * (1 + MARGEM))
    return -(-bruto // PASSO_CTX) * PASSO_CTX


def _num_ctx(system: str, user: str) -> tuple[int, str]:
    fixo = os.environ.get(VAR_NUM_CTX)
    if fixo:
        return int(fixo), "fixo"
    n, metodo = tokens_do_prompt(system, user)
    return num_ctx_da_chamada(n), metodo


def client_call_local(system: str, user: str, model: str | None = None) -> str:
    """O adaptador de síntese: `(system, user, model) -> str`, no contrato de `PROVIDER_CLIENTS`."""
    if VAR_TEMPERATURA in os.environ:
        raise ModeloLocalIndisponivel(
            f"{VAR_TEMPERATURA} está no ambiente: a temperatura é a do DESVIO_P01 "
            f"({AMOSTRAGEM['temperature']}), passada em cada chamada — remova-a")
    nome, sha_conferido = resolver_modelo(model)
    num_ctx, metodo = _num_ctx(system, user)
    r = L.resposta_json_local(system, user, estagio="sintese", modelo=nome, schema="json",
                              prazo=3600, num_predict=TETO_SAIDA, num_ctx=num_ctx,
                              think="false", seed=SEED, amostragem=dict(AMOSTRAGEM))
    REGISTRO.append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo": nome, "modelo_efetivo": r.get("modelo_efetivo"),
        "gguf_sha256": sha_esperado() if sha_conferido else None, "sha_conferido": sha_conferido,
        "system_sha256": hashlib.sha256(system.encode("utf-8")).hexdigest(),
        "num_ctx": num_ctx, "num_ctx_metodo": metodo,
        "amostragem": dict(AMOSTRAGEM), "seed": SEED, "think": r.get("think"),
        **{k: r.get(k) for k in ("finish_reason", "latencia_s", "leitura_prompt_s",
                                 "geracao_s", "carga_s", "prompt_eval_count", "eval_count")}})
    return r["texto"]
