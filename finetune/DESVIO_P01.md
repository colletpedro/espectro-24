# DESVIO_P01 — parâmetros de amostragem da geração (base e treinado)

Data: 2026-10-31. Desvia do `PREREGISTRO_AVALIACAO.md` (commit
`8339a6787140d9a3b83940e29e205d193de2e818`, sha256 `4e9d61b6…`), seção 2.
Commitado em commit PRÓPRIO, ANTES de qualquer geração nos filmes de teste.
**Nada foi gerado, julgado ou medido no teste até aqui.**

## O que muda

Na geração da síntese, BASE e TREINADO passam a usar, em CADA chamada e
EXPLÍCITOS na requisição ao Ollama:

| parâmetro | pré-registro (antes) | DESVIO_P01 (vale) |
|---|---|---|
| temperature | 0,8 (padrão do Ollama, passado explícito) | **0,7** |
| top_p | padrão do Ollama (não passado) | **0,8** |
| top_k | padrão do Ollama (não passado) | **20** |
| min_p | padrão do Ollama (não passado) | **0** |
| repeat_penalty | padrão do Ollama (não passado) | **1,0** |
| seed | 20261019 | **20261019** (sem mudança) |

Tudo o mais da seção 2 do pré-registro continua: `think` false, `num_predict`
3.000, `num_ctx` pela regra, retentativa de produção, regra de memória, e a
proibição de `ESPECTRO24_OLLAMA_TEMPERATURE` no ambiente.

## Fonte (consultada em 2026-10-31)

Model card oficial do Qwen3-8B, `huggingface.co/Qwen/Qwen3-8B`, revisão
`b968826d9c46dd6066d109eabc6255188de91218` (lastModified 2025-07-26),
`README.md` (sha256 `0f36caaf…`), linha 328, seção "Best Practices":

> For non-thinking mode (`enable_thinking=False`), we suggest using
> `Temperature=0.7`, `TopP=0.8`, `TopK=20`, and `MinP=0`.

- A linha 327 dá os do modo COM raciocínio: 0,6 / 0,95 / 20 / 0 (os mesmos do
  `generation_config.json` do repositório e do Modelfile do Unsloth).
- **repeat_penalty: o card não fala nele.** O `generation_config.json` do
  repositório não define `repetition_penalty`, então vale o padrão do
  transformers, 1,0 (nenhuma penalidade). O 1,0 explícito é decisão do dono e
  não contradiz o card. A linha 329 permite subir o `presence_penalty` (0 a 2)
  contra repetição sem fim; ele fica no padrão do Ollama (0), sem ajuste.

## Motivos

- O padrão do Ollama traz `repeat_penalty` 1,1, que penaliza tokens repetidos,
  e JSON repete chaves e aspas por construção.
- Os valores do Modelfile do Unsloth (0,6 / 0,95) são os do modo COM
  raciocínio, e o `think` está desligado.
- Os valores vêm do fabricante, sem ajuste nos nossos dados.
- Nada foi gerado no teste: o desvio não foi escolhido olhando resultado.

## O que já foi feito com outros parâmetros

- A geração da **Fase 1** (Qwen3-8B base, 5 filmes de TREINO, só para a
  rotulagem da validação da especificidade, já encerrada e NEGATIVA) usou o
  padrão do Ollama: o Modelfile corrigido não tem parâmetro de amostragem, e
  nenhum foi passado na chamada. Isso não afeta nenhum critério: a validação
  só decidiu que a M-disp sai, e nenhum número dela entra em C1–C6.
- O PUBLICADO (DeepSeek) não muda: foi gerado sem `temperature` explícita.

## Conferências

- Os seis parâmetros chegam à requisição: teste
  `tests/test_finetune_preregistro_geracao.py` (corpo da requisição de
  `resposta_json_local`).
- O juiz não muda: `config_sha256` continua
  `44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669`
  (MEDIDO antes e depois da mudança no `local_ollama`; o juiz não passa os
  novos parâmetros e o hash não lê o fonte do adaptador).
