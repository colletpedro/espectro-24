# Critério de escolha do modelo base — PRÉ-REGISTRADO (2026-10-20)

Pré-registrado e commitado ANTES de existir qualquer resultado de Kaggle ou de
Windows. Texto do dono (fechamento da fase 0), sem alteração. A escolha é
aplicada na rodada seguinte, contra este arquivo.

Candidatos: Gemma 4 12B, Gemma 4 E4B e Qwen3-8B (reserva). O Qwen3.5-9B saiu
(o Unsloth desaconselha QLoRA nele e o LoRA em 16 bits não cabe na T4).

## Critérios eliminatórios (um candidato passa só se cumprir todos)

**E1.** No Kaggle, T4 única, QLoRA 4-bit, LoRA r=16 em todas as projeções
lineares, gradient checkpointing "unsloth", fp16, batch 1: pico de
`torch.cuda.max_memory_reserved` ≤ 14,0 GiB no exemplo de treino mais longo,
com `max_seq_length` 14.336, ou 12.288 se o anterior falhar.

**E2.** Perda finita (sem NaN/inf) nos 10 passos do teste de fumaça, em fp16.

**E3.** Tempo projetado de treino ≤ 20 h de GPU, calculado assim:
(s/passo medido no exemplo mediano × nº de exemplos de treino depois da
limpeza estimada × 3 épocas) / 3600.

**E4.** O GGUF Q4_K_M exportado pelo Unsloth no Kaggle importa no Ollama do
notebook Windows e gera texto sem erro.

**E5.** No notebook, o prompt p90 de treino (`do-the-right-thing/negativas`)
com `num_ctx` 18.432 termina em ≤ 20 min.

## Regra de escolha

Entre os aprovados, fica o maior em parâmetros
(Gemma 4 12B > Gemma 4 E4B > Qwen3-8B).

Nesta etapa não há julgamento de qualidade. JSON inválido de modelo não
treinado NÃO é eliminatório; registre só como observação.

Medida não eliminatória: o probe de memória com `num_ctx` 27.648. Se falhar, o
outlier de teste vira tratamento separado, decidido na Fase 2.

Se nenhum candidato passar: reportar o negativo e parar.

## Notas de execução (não mudam o critério)

- "T4 única": o Kaggle CLI só oferece `NvidiaTeslaT4` = T4 ×2
  (`docs/kernels_metadata.md` do kaggle-api, consultado em 2026-10-20). O
  teste de fumaça restringe o processo a UMA GPU com
  `CUDA_VISIBLE_DEVICES=0` antes de importar o torch, e grava
  `torch.cuda.device_count()` no log.
- "Exemplos de treino depois da limpeza estimada" (E3): enquanto a limpeza
  não rodar, 180 − 24 = 156 (`limpeza.md`, ESTIMADO); depois dela, o número
  medido.
- O Qwen3-8B entra no Kaggle só se nenhum Gemma passar.
