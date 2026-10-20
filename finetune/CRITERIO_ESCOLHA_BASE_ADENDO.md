# Adendo ao critério de escolha do modelo base — PRÉ-REGISTRADO (2026-10-20)

Escrito e commitado ANTES de qualquer resultado de Kaggle ou de Windows. Não
altera E1–E5 nem a regra de escolha de `CRITERIO_ESCOLHA_BASE.md`
(commit `0466cead8e9d138ef071ca9da682ba9caff050b8`).

## Texto do dono

"Se a exportação GGUF falhar no Kaggle por limite de RAM ou disco da
plataforma (e não por erro do modelo ou do treino), o E4 é avaliado pelo
caminho alternativo: adaptador salvo no Kaggle, fusão e conversão para Q4_K_M
no Mac com llama.cpp, mesma quantização, Modelfile conferido. A causa da
falha tem que estar demonstrada no log."

## Onde a causa fica demonstrada (`smoke_treino.py`)

- `log.json` → `gguf_ok`, `gguf_erro`, `gguf_causa` (memória / disco /
  outra), `gguf_disco_livre_no_erro_gib`, `exportacao_disco` (estimativa ×
  livre, só registro: a exportação é sempre tentada) e `df_por_fase`;
- `linha_do_tempo.jsonl` → RAM usada/disponível e disco livre a cada 2 s,
  por fase (`exportacao_fusao`, `exportacao_conversao`), sincronizada no disco
  a cada amostra, para sobreviver a um processo morto pelo sistema;
- `resumo.json` → `rc` do subprocesso (`morto_pelo_so` quando rc = −9, o
  OOM-kill do sistema) e as últimas amostras da linha do tempo;
- o adaptador LoRA é salvo em /kaggle/working ANTES da fusão.

## O Mac aguenta a fusão do 12B em 16 bits? — NÃO, hoje (MEDIDO em 2026-10-20)

| | medido | necessário (ESTIMADO) |
|---|---|---|
| RAM | 16,0 GiB (Apple M4) | fusão em memória: ≥ ~24 GB só de pesos do 12B em 16 bits (23,92 GB de safetensors em `unsloth/gemma-4-12b-it`); E4B ~16 GB |
| disco livre | **5,5 GiB** (`/System/Volumes/Data`, 98% usado) | ~60 GB (16-bit fundido + GGUF 16-bit intermediário + Q4_K_M, 12B); ~40 GB (E4B) |
| llama.cpp | não instalado (`llama-quantize`, `llama-export-lora` ausentes) | instalado |

Leitura:
- **Fusão em memória (PEFT `merge_and_unload` em 16 bits): não cabe no Mac**,
  nem para o 12B (24 GB > 16 GiB), nem com folga para o E4B (~16 GB ≈ toda a
  RAM).
- **Fusão tensor a tensor pelo llama.cpp** (adaptador → GGUF com
  `convert_lora_to_gguf.py`; base em GGUF 16-bit; `llama-export-lora`, que lê
  por mmap; `llama-quantize` para Q4_K_M) pede pouca RAM (NÃO MEDIDO), mas
  ~60 GB de disco. Com 5,5 GiB livres, **o caminho alternativo é inviável no
  Mac até liberar ~60 GB**. O suporte do `llama-export-lora` à arquitetura
  Gemma 4 também NÃO foi verificado.
- Consequência registrada antes do resultado: se a exportação no Kaggle cair
  por limite da plataforma, o E4 do candidato fica PENDENTE até o caminho
  alternativo ser viável (disco liberado no Mac). Usar outra máquina é decisão
  do dono, não deste adendo.
