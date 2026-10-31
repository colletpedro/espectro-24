# TREINO_CONFIG — Qwen3-8B, Fase 3

Data: 2026-10-31. Commitado em commit PRÓPRIO, ANTES do push do kernel de
treino. Vale junto com o `PREREGISTRO_AVALIACAO.md` (commit `8339a678…`) e o
`DESVIO_P01.md` (commit `fb9ec740…`). Etiquetas: **MEDIDO**, **ESTIMADO**,
**PROPOSTO**.

**O treino não olha o teste.** O gate da Fase 2 está fechado para o treino
(decisão do dono): os critérios estão commitados, o dataset só tem filmes de
TREINO e de VALIDAÇÃO, e o treinado só é medido na Fase 4.

## Dados

- **140 exemplos de TREINO e 19 de VALIDAÇÃO** do conjunto LIMPO
  (`limpeza/conjunto_limpo.json`, `sha256_ids`
  `ecdd5558b5881f4104ce922c1ba3dd8775184b0d5c997f5af72a60f503395438`): o que
  sobrou da limpeza com o juiz v2.2, menos o `satantango/positivas` (fora por
  comprimento, decisão de 2026-10-22).
- Cada exemplo: prompt atual da síntese sobre o bucket remontado do bruto, alvo
  = a síntese publicada (`comum.serializar_alvo`), `chat_esperado` pelo
  `comum.chat` CORRIGIDO (sem aparar; commit `7e2ace9`).
- Montado por `scripts/finetune/kaggle/montar_dataset_treino.py` (MEDIDO hoje,
  só filmes de treino e validação):
  - **sha256 do dataset (`treino.jsonl`):
    `36f81ac1a48d11bdc1b7f1fc27e71fb3dd54ca063b29caa862ff4459ee45e53d`**;
  - tokens (Qwen3-8B, total por exemplo): mediana 6.866, p90 9.156, máximo
    **12.014** (treino); validação: mediana 7.461, máximo 10.029. Nenhum
    acima de 12.288;
  - split `3232b2ad…`.
- O `meta.json` do dataset recebe depois, com `--log-kernel-base`, o commit do
  llama.cpp e o sha256 do GGUF da BASE (e o `tensores.json` dela). O
  `treino.jsonl` não muda com isso (o sha acima continua).
- **Dataset PRIVADO no Kaggle** (`USUARIO/espectro24-finetune-treino-qwen3-dados`).
- **O kernel aborta**, antes de instalar ou treinar, se:
  - o sha256 do `treino.jsonl` lido ≠ o do `meta.json` ≠ o desta página
    (constante `DATASET_SHA256` no kernel);
  - o `meta.json` não tiver o commit do llama.cpp da base;
  - algum exemplo for de filme fora do seu conjunto, ou de teste;
  - não forem exatamente 140 + 19.
  E, depois de carregar o modelo, se `template_confere` for falso em QUALQUER
  exemplo, ou se algum passar de 12.288 tokens (não há truncamento).

## Configuração (idêntica ao smoke v4 onde se aplica)

| item | valor | de onde |
|---|---|---|
| repositório | `unsloth/Qwen3-8B-unsloth-bnb-4bit`, revisão `62efd7f9d748e394734a7adae2adf96e13a2abc8` (aborta se o HF mudar) | smoke v4, base |
| carga | 4-bit, `dtype` fp16 | smoke v4 |
| LoRA | r 16, alpha 16, dropout 0, bias none, as 7 projeções (q, k, v, o, gate, up, down) | smoke v4 |
| gradient checkpointing | `"unsloth"` | smoke v4 |
| precisão | fp16 (T4 sem bf16) | smoke v4 |
| seed | 3407 (`random_state`, `seed`, `data_seed`) | smoke v4 |
| template | `get_chat_template(tok, "qwen3")`, `enable_thinking=False` | smoke v4 |
| perda | só na resposta (`train_on_responses_only`; parte da resposta = `<|im_start|>assistant\n<think>\n\n</think>\n\n`); a máscara é conferida no treino e na validação | smoke v4 |
| `max_seq_length` | **12.288** (o maior exemplo tem 12.014) | decisão do dono |
| otimizador | lr 2e-4, cosine, warmup 5% (`warmup_ratio` 0,05), adamw_8bit, weight decay 0 | lr, otimizador e weight decay do smoke; cosine e warmup, decisão do dono |
| épocas, lote | 3 épocas, batch 1 × acumulação 4 (35 passos por época, 105 no total) | decisão do dono |
| packing | não | smoke v4 |
| GPU | T4 única (`CUDA_VISIBLE_DEVICES=0`) | smoke v4 |

- **Versões fixadas:** `unsloth==2026.10.7` e `unsloth_zoo==2026.10.7`, as
  mesmas da exportação da base. O resto (torch, transformers, trl, peft,
  bitsandbytes) vem da imagem do Kaggle do dia e é GRAVADO no `log.json`; no
  smoke v4 (MEDIDO): torch 2.11.0+cu128, transformers 5.16.1, trl 1.15.0, peft
  0.20.0, bitsandbytes 0.50.2. Limitação: a imagem do Kaggle não é fixável pela
  API; a comparação com a base sai dos dois `log.json`.
- **llama.cpp:** o MESMO commit da exportação da base, lido do `meta.json`. O
  kernel clona e compila o llama.cpp nesse commit ANTES da exportação; depois,
  confere o commit usado. Se não for o da base, o GGUF NÃO é copiado para a
  saída (o adaptador fica), e o `gerar_sintese_teste.py` também recusa.
- A carga da base foi com `max_seq_length` 14.336 e a do treino é com 12.288:
  isso muda o comprimento que o treino aceita, não os pesos exportados
  (ESTIMADO pelo código: o `max_seq_length` não entra na fusão).

## Avaliação durante o treino e escolha

- **Perda na VALIDAÇÃO ao fim de cada época** (os 19 exemplos, só os tokens da
  resposta, batch 1).
- **Checkpoint de cada época** em `/kaggle/working/treino/checkpoints`
  (adaptador e estado do otimizador). Uma execução interrompida retoma do
  último checkpoint, inclusive de uma saída anterior anexada como entrada.
- **Regra de escolha:** a época com a MENOR perda na validação, comparada
  arredondada na 4ª casa decimal. Em empate, a de MENOS épocas. A curva
  completa (perda de treino por passo, perda de validação por época) vai para
  `curva.json` e para o `log.json`.
- O adaptador escolhido é carregado de novo e a perda na validação é refeita;
  ela tem de bater com a da curva (tolerância 1e-3), senão o kernel aborta.
- **Busca de hiperparâmetros: nenhuma**, por decisão registrada: com 19
  exemplos de validação, escolher entre configurações seria ajustar ao ruído
  da validação. O único grau de liberdade é a época (≤ 3).

## Exportação

- SÓ o checkpoint escolhido → `save_pretrained_gguf(..., quantization_method=
  "q4_k_m")`, a MESMA função e o mesmo caminho da base (fusão nos shards
  16-bit originais), com o llama.cpp no commit da base. O adaptador escolhido
  também é salvo (`adaptador_escolhido/`, com o sha256 de cada arquivo).
- `tensores.json` (tipo e sha256 de cada tensor do GGUF). Com o
  `tensores_base.json` do dataset, o kernel confere que só os tensores das 7
  projeções mudaram (`comparacao_com_base`).
- Saída: `/kaggle/working/treino/qwen3-8b-treinado__12288/`. O `modelo` do
  `log.json` é `qwen3-8b-treinado`, e o `importar-pasta` o importa como
  **`espectro-qwen3-8b-treinado`**, nome distinto da base
  (`espectro-qwen3-8b-base`). O `gerar_sintese_teste.py` escolhe o modelo pelo
  sha256 do GGUF do `log.json` do kernel, não pelo nome.

## Custo (ESTIMADO pelos números MEDIDOS no smoke v4)

- Treino: 27,06 s por passo de 1 exemplo (mediana, exemplos medianos) × 140 × 3
  = **3,16 h**, mais a validação (19 × 3 só com forward, ~0,1–0,2 h).
- llama.cpp (clone e compilação): ~5–15 min. Fusão e GGUF: 831,5 s no smoke v4
  (~14 min). Carga e instalação: ~10 min.
- **Total: ~3,7–4,5 h de GPU** numa sessão (o limite do Kaggle é 12 h; o
  orquestrador corta em 11 h e os checkpoints por época permitem retomar).
