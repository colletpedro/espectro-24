# Juiz v2 — versão v2.0

`config_sha256`: `a42f48932713ff322535116cb17538bc51a14bdb5e49c9c8389c35b687461c22`

- modelo `gpt-oss:20b`, think `low`, seed 20261019, temperatura do modelo
- num_predict 1024, num_ctx **3584**

## Contexto

Maior par dos 900: `local|the-substance|positivas|0|viewing:1439489161` — review de 4990 caracteres, prompt inteiro de 7100.

Cota conservadora: 0.35 token/caractere (no gate do gpt-oss o máximo foi 0,343 em 417 prompts) → ≤ 2485 tokens de prompt + 1024 de saída = 3509 → menor múltiplo de 512: **3584**. É cota, não medição: `medir-contexto` conta os 10 maiores prompts no servidor antes de o juiz rodar.

## Tempo (estimativa, não medição)

Das velocidades do gate do gpt-oss:20b neste notebook; a saída é a do gate (mediana 130 tokens, p95 311 — o raciocínio domina).

| execução | chamadas | mediana | p95 |
|---|---|---|---|
| calibração (40 pares) | 40 | ~10 min | ~19 min |
| todos (900 pares, só com a versão congelada) | 900 | ~200 min | ~398 min |

`medir-contexto`: 10 chamadas com num_ctx 8192 e 1 token de saída, mais a recarga do modelo ao trocar de janela — poucos minutos.
