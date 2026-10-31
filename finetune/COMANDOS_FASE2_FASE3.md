# Comandos — Fase 2 (Windows) e Fase 3 (Mac/Kaggle)

Data: 2026-10-31. Quem roda é o dono. Pré-registro `8339a678…`, `DESVIO_P01`
`fb9ec740…`, `TREINO_CONFIG` `ff041237…`. Scripts em `main` `b7c6707`.
Etiquetas: **MEDIDO**, **ESTIMADO**.

No Windows, sempre num PowerShell novo e FORA do Claude Code. Repositório em
`C:\espectro\espectro-24` (branch `finetune`). Kaggle: usuário `pedrocollet1`.

## 0. Preparo do Windows (antes de CADA bloco abaixo)

Traz os scripts de `main` e o `local_ollama.py` (a amostragem do DESVIO_P01) e
tira as chaves do ambiente. O `gerar` aborta se `ESPECTRO24_OLLAMA_TEMPERATURE`
existir.

```powershell
cd C:\espectro\espectro-24
git restore --staged --worktree scripts/finetune src/espectro24/local_ollama.py
git pull
git checkout origin/main -- scripts/finetune src/espectro24/local_ollama.py
Remove-Item Env:GEMINI_API_KEY, Env:GEMINI_API_KEY_PROD, Env:TMDB_API_KEY, Env:DEEPSEEK_API_KEY, Env:GOOGLE_API_KEY, Env:ESPECTRO24_OLLAMA_TEMPERATURE -ErrorAction SilentlyContinue
```

Depois de cada commit no Windows, o fecho é sempre o mesmo:

```powershell
git restore --staged --worktree scripts/finetune src/espectro24/local_ollama.py
git pull --rebase
git push
```

No Mac, os comandos que contam tokens ou usam o e5 precisam do `tokenizers` do
Python do Homebrew (uma vez):

```bash
mkdir -p ~/.espectro24-pylib && ln -sf /opt/homebrew/lib/python3.14/site-packages/tokenizers ~/.espectro24-pylib/tokenizers
```

## FASE 2

### a) Base: exportar no Kaggle e importar no Windows

Mac (cópia em `/tmp`, só os arquivos do kernel; o usuário conferido com grep):

```bash
cd ~/Downloads/espectro-24 && rm -rf /tmp/kbase && mkdir /tmp/kbase && find scripts/finetune/kaggle/kernel_base -maxdepth 1 -type f -exec cp {} /tmp/kbase/ \; && sed -i '' 's/USUARIO/pedrocollet1/g' /tmp/kbase/kernel-metadata.json && grep -n pedrocollet1 /tmp/kbase/kernel-metadata.json && ! grep -n USUARIO /tmp/kbase/kernel-metadata.json && kaggle kernels push -p /tmp/kbase
```

```bash
kaggle kernels status pedrocollet1/espectro24-finetune-base-qwen3
```

Windows (bloco 0 antes). Baixa, importa SÓ a pasta da base (nome
`espectro-qwen3-8b-base`) e guarda os logs sem o GGUF:

```powershell
$B="$HOME\espectro24-kaggle\qwen3\base"; New-Item -ItemType Directory -Force $B | Out-Null
kaggle kernels output pedrocollet1/espectro24-finetune-base-qwen3 -p $B
Get-ChildItem $B -Recurse -Include *.gguf,log.json | Select FullName,Length
.\venv\Scripts\python.exe scripts\finetune\viabilidade_ollama.py importar-pasta --pasta $B\base\qwen3-8b-base__14336
robocopy $B finetune\kaggle\base_saida_qwen3 /E /XF *.gguf *.safetensors *.bin
ollama list | Select-String espectro-qwen3-8b
git add finetune\kaggle\base_saida_qwen3 finetune\viabilidade
git commit -m "finetune: export da base pelo kernel e importacao" -- finetune\kaggle\base_saida_qwen3 finetune\viabilidade
```

(fecho do Windows). Se a base já foi importada, este bloco não se repete: o
`gerar` confere o sha do GGUF no `log.json` e a prova do adaptador e da fusão.

### b) Plano (Mac) e síntese da BASE nos 89 buckets (Windows, retomável)

Mac — tokens exatos e `num_ctx` dos 89 pares:

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/gerar_sintese_teste.py plano; rm finetune
```

```bash
git -C ../espectro-24-finetune add finetune/fase2/plano_teste.json && git -C ../espectro-24-finetune commit -m "finetune: plano da sintese de teste (fase 2)" -- finetune/fase2/plano_teste.json && git -C ../espectro-24-finetune push origin finetune
```

Windows (bloco 0 antes) — **de madrugada**; se parar (latência, memória),
rode o MESMO comando de novo:

```powershell
.\venv\Scripts\python.exe scripts\finetune\gerar_sintese_teste.py gerar --lado base --log-kernel finetune\kaggle\base_saida_qwen3\base\qwen3-8b-base__14336\log.json
git add finetune\fase2\sintese_base
git commit -m "finetune: sintese da base nos 89 buckets de teste (fase 2)" -- finetune\fase2\sintese_base
```

(fecho do Windows)

### c) Juiz: PUBLICADO e BASE (Mac prepara, Windows julga)

Mac — recuperação e5 dos dois lados. No publicado, confere o sha das 450
linhas dos 5 de referência (`a68a6c9b…`) e, se bater, copia os vereditos
antigos; o `entrada_meta.json` diz se bateu:

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && for L in publicado base; do env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/avaliar_c1_c4.py preparar --lado $L || break; done; rm finetune
```

```bash
git -C ../espectro-24-finetune add finetune/fase2/juiz && git -C ../espectro-24-finetune commit -m "finetune: entrada do juiz, publicado e base (fase 2)" -- finetune/fase2/juiz && git -C ../espectro-24-finetune push origin finetune
```

Windows (bloco 0 antes) — **de madrugada**, um lado por noite; `julgar` é
retomável (saída 3 = pausa da guarda de latência: confira o Ollama e rode de
novo):

```powershell
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py medir-contexto --lado publicado
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py julgar --lado publicado
git add finetune\fase2\juiz\publicado
git commit -m "finetune: juiz no publicado (fase 2)" -- finetune\fase2\juiz\publicado
```

```powershell
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py medir-contexto --lado base
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py julgar --lado base
git add finetune\fase2\juiz\base
git commit -m "finetune: juiz na base (fase 2)" -- finetune\fase2\juiz\base
```

(fecho do Windows depois de cada um)

### d) C1–C4 nos dois lados (descritivo) e δ₂

Windows (bloco 0 antes):

```powershell
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py calcular
.\venv\Scripts\python.exe scripts\finetune\avaliar_c1_c4.py fixar-delta2
```

### e) Commit das saídas

```powershell
git add finetune\fase2\c1_c4_fase2.json finetune\fase2\delta2.json
git commit -m "finetune: C1-C4 da fase 2 (descritivo) e delta2" -- finetune\fase2\c1_c4_fase2.json finetune\fase2\delta2.json
```

(fecho do Windows)

### Tempo da Fase 2 (ESTIMADO pelos números MEDIDOS)

| etapa | onde | tempo | madrugada? |
|---|---|---|---|
| export da base (carga, provas, export 831,5 s no smoke v4, conferência da fusão, biblioteca) | Kaggle | ~45–75 min | não precisa |
| download (5,03 GB) + `importar-pasta` | Windows | ~10–20 min | não |
| `plano` | Mac | ~2–5 min | não |
| síntese da base: 88 × ~150 s (mediana MEDIDA na Fase 1: 150,7 s, de 121 a 266 s) + retentativas (0–15%, sem medida) + o outlier (`num_ctx` 28.672–31.744, sem medida) | Windows | **~3,8–4,6 h** | **sim** |
| `preparar` (e5): 1.927,7 s para 68 filmes na limpeza (MEDIDO) → ~28 s por filme | Mac | ~15 min por lado | não |
| juiz no publicado: 444 bullets (534 − 90 reaproveitados) × 3,2 pares × 16,2 s (3,2 = 5 × (1 − 36%), a economia MEDIDA na referência; 16,2 s/par MEDIDO na limpeza) | Windows | **~6,4 h** (sem o reaproveitamento: ~7,7 h; faixa 2,5–5 pares: 5–12 h) | **sim** |
| juiz na base: ~534 bullets × 3,2 × 16,2 s | Windows | **~7,7 h** (5–12 h) | **sim** |
| `calcular`, `fixar-delta2` | Windows | minutos | não |

Total de máquina no Windows: ~18–25 h, em três madrugadas (síntese, juiz P,
juiz B).

## FASE 3 — treino no Kaggle (em paralelo à Fase 2, DEPOIS do bloco a)

O kernel de treino precisa do commit do llama.cpp da base: só depois que os
logs da base estiverem em `finetune/kaggle/base_saida_qwen3`.

Mac — fecha o `meta.json` do dataset com o llama.cpp e o GGUF da base. O
`treino.jsonl` não muda: o sha tem de continuar `36f81ac1…`:

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/kaggle/montar_dataset_treino.py --log-kernel-base finetune/kaggle/base_saida_qwen3/base/qwen3-8b-base__14336/log.json; rm finetune
```

```bash
shasum -a 256 ../espectro-24-finetune/finetune/kaggle/treino_dataset_qwen3/treino.jsonl | grep -q '^36f81ac1a48d11bdc1b7f1fc27e71fb3dd54ca063b29caa862ff4459ee45e53d' && echo SHA_OK && git -C ../espectro-24-finetune add finetune/kaggle/treino_dataset_qwen3 && git -C ../espectro-24-finetune commit -m "finetune: dataset de treino com o llama.cpp da base" -- finetune/kaggle/treino_dataset_qwen3 && git -C ../espectro-24-finetune push origin finetune
```

Mac — dataset PRIVADO (a 1ª vez `create`; se já existir, `version`):

```bash
rm -rf /tmp/dtreino && mkdir /tmp/dtreino && find ../espectro-24-finetune/finetune/kaggle/treino_dataset_qwen3 -maxdepth 1 -type f -exec cp {} /tmp/dtreino/ \; && sed -i '' 's/USUARIO/pedrocollet1/g' /tmp/dtreino/dataset-metadata.json && grep -n pedrocollet1 /tmp/dtreino/dataset-metadata.json && ! grep -n USUARIO /tmp/dtreino/dataset-metadata.json && kaggle datasets create -p /tmp/dtreino
```

```bash
kaggle datasets version -p /tmp/dtreino -m "meta.json com o llama.cpp da base"
```

```bash
kaggle datasets status pedrocollet1/espectro24-finetune-treino-qwen3-dados
```

Mac — kernel (só quando o dataset estiver `ready`):

```bash
rm -rf /tmp/ktreino && mkdir /tmp/ktreino && find scripts/finetune/kaggle/kernel_treino -maxdepth 1 -type f -exec cp {} /tmp/ktreino/ \; && sed -i '' 's/USUARIO/pedrocollet1/g' /tmp/ktreino/kernel-metadata.json && grep -n pedrocollet1 /tmp/ktreino/kernel-metadata.json && ! grep -n USUARIO /tmp/ktreino/kernel-metadata.json && kaggle kernels push -p /tmp/ktreino
```

```bash
kaggle kernels status pedrocollet1/espectro24-finetune-treino-qwen3
```

Se a sessão cair antes do fim (o orquestrador corta em 11 h), anexe a saída
da execução anterior como entrada (`"kernel_sources":
["pedrocollet1/espectro24-finetune-treino-qwen3"]` no `/tmp/ktreino/kernel-metadata.json`)
e rode o `push` de novo: o kernel retoma do último checkpoint de época.
(ESTIMADO: não testado no Kaggle.)

Windows (bloco 0 antes) — baixa, importa SÓ a pasta do treinado (nome
`espectro-qwen3-8b-treinado`, distinto da base) e guarda os logs sem GGUF,
adaptador e checkpoints:

```powershell
$T="$HOME\espectro24-kaggle\qwen3\treino"; New-Item -ItemType Directory -Force $T | Out-Null
kaggle kernels output pedrocollet1/espectro24-finetune-treino-qwen3 -p $T
Get-ChildItem $T -Recurse -Include *.gguf,log.json,curva.json | Select FullName,Length
.\venv\Scripts\python.exe scripts\finetune\viabilidade_ollama.py importar-pasta --pasta $T\treino\qwen3-8b-treinado__12288
robocopy $T finetune\kaggle\treino_saida_qwen3 /E /XF *.gguf *.safetensors *.bin *.pt *.pth /XD checkpoints adaptador_escolhido
ollama list | Select-String espectro-qwen3-8b
git add finetune\kaggle\treino_saida_qwen3 finetune\viabilidade
git commit -m "finetune: treino do Qwen3-8B (fase 3), logs e importacao" -- finetune\kaggle\treino_saida_qwen3 finetune\viabilidade
```

(fecho do Windows). O treinado NÃO é gerado nem medido no teste aqui: isso é
a Fase 4, uma vez, com `--lado treinado --log-kernel
finetune\kaggle\treino_saida_qwen3\treino\qwen3-8b-treinado__12288\log.json
--log-kernel-base finetune\kaggle\base_saida_qwen3\base\qwen3-8b-base__14336\log.json`.

### Tempo da Fase 3 (ESTIMADO pelo smoke v4)

| etapa | onde | tempo |
|---|---|---|
| `montar_dataset_treino` | Mac | ~5 min |
| upload do dataset (~10 MB) | Mac | ~1–3 min |
| treino: 27,06 s/passo (MEDIDO) × 140 × 3 = 3,16 h; + validação por época ~0,1–0,2 h | Kaggle | ~3,3–3,4 h |
| llama.cpp (clone e compilação), fusão e GGUF (831,5 s MEDIDO), carga | Kaggle | ~0,4–0,6 h |
| **total do kernel** | Kaggle | **~3,7–4,5 h de GPU** (cota semanal de 30 h, MEDIDO em 22/10) |
| download + `importar-pasta` | Windows | ~10–20 min |
