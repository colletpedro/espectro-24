# DESVIO_P02 — prova de fusão da base FALSA, aceita com exceção exata

Data: 2026-11-02. Desvia da regra da Fase 2a (`exportar_base.py`, passo 5:
"com B = 0 a fusão tem de deixar TODOS [os tensores] iguais"). Commitado em
commit PRÓPRIO, ANTES do import da base. **Nada foi importado, treinado,
gerado ou julgado com este GGUF até aqui.**

## Decisão (do dono)

O GGUF da base do kernel `exportar_base` v2 é ACEITO: `Qwen3-8B.Q4_K_M.gguf`,
sha256 `c9f3c7016b886143f79b8d86e4e8ff26fb55dee7475e674272e211fbf1f23475`,
5.027.784.288 bytes. A `prova_fusao` do log fica `ok: false` e explicada
aqui; ela não é reescrita.

## O que a prova mostrou (MEDIDO, `finetune/kaggle/base_saida_qwen3/.../log.json`)

- comparação exata (`torch.equal`: dtype, forma e bits), sem tolerância, dos
  4 shards fundidos contra os originais de `unsloth/Qwen3-8B`, revisão
  `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`. É a mesma revisão nos 4
  metadados de download da fusão;
- **1 de 399 tensores** diferente: `model.embed_tokens.weight`, bf16 nos dois
  lados, **max_abs 0,029541015625**;
- shard 1 (o da embedding) com sha256 diferente; shards 2, 3 e 4 idênticos
  byte a byte. O `lm_head.weight` está no shard 4, logo não mudou;
- `prova_adaptador`: `B_zero` true; perda e logits com e sem o adaptador
  idênticos (diferença 0,0).

## Causa (lida no código do Unsloth instalado, 2026.10.7)

Wheels do PyPI: `unsloth-2026.10.7` sha256 `3ffd1dc0…`; `unsloth_zoo-2026.10.7`
sha256 `4161df8e…`.

1. `unsloth/models/qwen3.py:414`: `FastQwen3Model.from_pretrained` chama
   `FastLlamaModel.from_pretrained`;
2. `unsloth/models/llama.py:4201–4203`: dentro de `from_pretrained`, chama
   `zero_pad_embedding_rows(model, tokenizer)`;
3. `unsloth/tokenizer_utils.py:173–195`: zera `module.weight[pad_token_id]`
   em todo `nn.Embedding` com `padding_idx == pad_token_id`. Não zera se o pad
   for EOS, se o tokenizer o adicionar a toda entrada ou se a embedding for
   amarrada ao `lm_head`. No repositório da carga
   (`unsloth/Qwen3-8B-unsloth-bnb-4bit` `62efd7f9…`) o pad é
   `<|vision_pad|>`, **id 151654** (`config.json` `pad_token_id`,
   `tokenizer_config.json` `pad_token`). O EOS é 151645 e
   `tie_word_embeddings` é false: nenhuma das exceções vale;
4. `unsloth_zoo/saving_utils.py:1015–1056` (`_untargeted_vocab_modules`,
   `_get_vocab_overrides`, `_apply_vocab_override`), chamados em `:1137` e
   `:1362`: na fusão, a embedding e o `lm_head` sem LoRA são sobrepostos pelo
   peso vivo. `_with_live_vocab_rows` (`:525–541`) grava só as linhas que
   diferem do original convertido ao dtype vivo (fp16). As outras linhas não
   mudam, e a linha zerada sai como zero no shard bf16.

## Números (MEDIDO por conta local, sem Kaggle)

Só leitura, por HTTP Range, de 2 linhas da embedding do shard 1 original
(`model-00001-of-00004.safetensors` de `unsloth/Qwen3-8B` `946bc9ac…`;
cabeçalho de 12.312 bytes; embedding BF16 [151936, 4096] no offset 0 dos
dados):

| linha | token | max_abs | média abs | L2 | zeros de 4.096 |
|---|---|---|---|---|---|
| 151654 | `<\|vision_pad\|>` | **0,029541015625** | 0,00697 | 0,562 | 30 |
| 151643 | `<\|endoftext\|>` (referência) | 0,111328125 | 0,0218 | 1,750 | 0 |

O max_abs da linha 151654 original é IGUAL, bit a bit, ao max_abs da
`prova_fusao`. Com a linha zerada, a divergência é a própria linha: relativa
100%.

## O token não é usado (MEDIDO, busca do texto `<|vision_pad|>`)

- `chat_template.jinja` do repositório da carga: 0 ocorrências;
- `Modelfile` exportado (`base_saida_qwen3/.../Modelfile`): 0;
- `finetune/kaggle/treino_dataset_qwen3/treino.jsonl`, 159 linhas (140 de
  TREINO e 19 de VALIDAÇÃO): 0. O TESTE não foi aberto;
- o template de chat usa `<|im_start|>` 151644, `<|im_end|>` 151645,
  `<think>` 151667, `</think>` 151668 e quebras de linha. Nenhum é 151654;
- o treino usa batch 1 e `packing=False`: o SFT não insere pad. Na geração, o
  Ollama não alimenta o pad.

## Por que base e treinado continuam diferindo SÓ pelo adaptador

- `treino.py` usa a MESMA chamada de carga (mesmo repositório e revisão,
  4-bit, fp16): passa pela mesma `zero_pad_embedding_rows`, pelo mesmo
  `save_pretrained_gguf` e pelo mesmo override de vocabulário (INFERIDO do
  código);
- o SFTTrainer do Unsloth acrescenta `fix_untrained_tokens` e
  `fix_zero_training_loss`. Com `embed_tokens` e `lm_head` congelados,
  `fix_untrained_tokens` só retorna ou levanta erro (ramo
  `bad_not_trainable`, `unsloth_zoo/tokenizer_utils.py:456–740`) e exclui o
  pad explicitamente. `fix_zero_training_loss` só lê os `labels`. Nenhum dos
  dois escreve pesos (INFERIDO do código);
- a igualdade passa a ser MEDIDA, não inferida:
  - (a) o import do treinado (`viabilidade_ollama.py importar-pasta`) e o
    `gerar_sintese_teste.py` abortam se o `token_embd.weight` e o
    `output.weight` do `tensores.json` do treinado não tiverem os sha256 da
    base: `70a40c465d023c8bfb8bddb9bd51377d314fd33583f76cc2da2e6f092f163728`
    e `05d7a76c29a32e067f41ad91df565341b21f4bedeeffbbf9e10957aaa9f78cc1`;
  - (b) o kernel de treino grava no log as linhas do `embed_tokens` fundido
    que diferem do original, com o max_abs de cada uma. É só registro.

## Exceção nas guardas (exata)

Onde um script exigia `prova_fusao.ok`, a condição passa a ser: `ok` true OU
(`n_diferentes` == 1, o único diferente é `model.embed_tokens.weight`,
`max_abs` == 0,029541015625 e as chaves iguais em todos os shards). Qualquer
outro padrão reprova: 2 tensores, outro tensor ou outro max_abs.

## Medido × inferido

- MEDIDO: 1 de 399 tensores; o tensor, o dtype e o max_abs; shards 2–4
  idênticos (inclui `lm_head`); revisão `946bc9ac…` nos 4 shards; max_abs da
  linha 151654 original = o da prova; 0 ocorrências do token no template, no
  Modelfile, no treino e na validação; sha256 do GGUF no Windows.
- INFERIDO (do código do Unsloth 2026.10.7): que só a linha 151654 mudou; o
  log não grava a diferença por linha, e o shard fundido não existe mais.
  Também inferido: que o treinado sai com a mesma linha zerada (passa a ser
  medido pelas conferências (a) e (b) acima).
- NÃO MEDIDO: a linha 151654 do `token_embd.weight` dequantizada do GGUF da
  base. A conferência seria local, com o `gguf-py` do llama.cpp `6d194531`.
