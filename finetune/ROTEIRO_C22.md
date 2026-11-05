# Roteiro do C22 — treinado + guarda, 35 filmes (105 buckets)

Pré-requisitos: fluência ≥ 27/30 aprovada pelo dono; `PREREGISTRO_C22.md` commitado.
Cegueira do dono até o C6: não abra `finetune/c22/{sintese_treinado,juiz,cego}`, `c6_*`.
Tempos ESTIMADOS (extrapolados da Fase 4): geração 5–6 h; juiz 8–11 h.

## Bloco 0 (Windows, início de CADA sessão)
```powershell
cd C:\espectro\espectro-24
git restore --staged --worktree scripts/finetune src/espectro24
git pull
git checkout origin/main -- scripts/finetune src/espectro24
Remove-Item Env:GEMINI_API_KEY, Env:GEMINI_API_KEY_PROD, Env:TMDB_API_KEY, Env:DEEPSEEK_API_KEY, Env:GOOGLE_API_KEY, Env:ANTHROPIC_API_KEY, Env:OPENAI_API_KEY, Env:ESPECTRO24_OLLAMA_TEMPERATURE -ErrorAction SilentlyContinue
Test-Path scripts\finetune\c22.py
```
(tem de imprimir `True`). Nunca `ollama list`/`ollama ps`: use `ollama_pronto.py`.

## Bloco 1 — Windows: geração (~5–6 h, retomável)
```powershell
$PY=".\venv\Scripts\python.exe"; $LT="finetune\kaggle\treino_saida_qwen3\treino\qwen3-8b-treinado__12288\log.json"; $LB="finetune\kaggle\base_saida_qwen3\base\qwen3-8b-base__14336\log.json"; & $PY scripts\finetune\c22.py gerar --log-kernel $LT --log-kernel-base $LB
```
Parada: rodar de novo imprime `0 a fazer`. Commit:
```powershell
git add finetune\c22\sintese_treinado finetune\c22\cego
git commit -m "finetune: sintese do treinado no C22" -- finetune\c22\sintese_treinado finetune\c22\cego
git restore --staged --worktree scripts/finetune src/espectro24
git pull --rebase origin finetune
git push origin finetune
```

## Bloco 2 — Mac: preparar (~15 min)
```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/c22.py preparar; rm finetune
```
Parada: `preparado, entrada_meta.json sha256 …`. Commit e push de `finetune/c22/juiz finetune/c22/cego`.

## Bloco 3 — Windows: juiz (~8–11 h, retomável)
```powershell
$PY=".\venv\Scripts\python.exe"; & $PY scripts\finetune\ollama_pronto.py --subir --modelo gpt-oss:20b; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\c22.py medir-contexto }; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\c22.py julgar }
```
Parada: `fim — rode calcular`; saída 3 = PAUSADO (rodar de novo); "NÃO CABE" = PARE. Commit de `finetune\c22\juiz finetune\c22\cego` e o fecho do bloco 1.

## Bloco 4 — Mac: calcular (~5 min)
```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/c22.py calcular; rm finetune
```
Parada: `calculado, c1_c4_c22.json sha256 …`. Commit de `finetune/c22/cego`.

## Bloco 5 — Mac: documento do C6, leitura do dono, avaliação
```bash
cd ~/Downloads/espectro-24 && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/c22.py leitura montar; rm finetune
```
O dono lê `docs/arquivo-de-estudos/finetune-c22/leitura_c6.md` e preenche `leitura_c6_respostas.csv` (S/N).
```bash
cd ~/Downloads/espectro-24 && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/c22.py leitura avaliar --selo SELO; rm finetune
```
**PARE e avise o Claude:** o `RESULTADO_C22.md` é escrito só depois do C6.

## Publicação (PREPARADA, não executada; nada no frontend)
Falta: (1) um comando que, aprovado o C22, monte `resultado/<slug>.json` a partir de
`sintese_treinado` + ficha/TMDB + distribuição + rotulagem de eixos (hoje só o CLI faz isso, com
síntese por LLM); (2) incluir os slugs em `dados/publicados.json`; (3) a rotulagem de eixos
(\[D3\]) e o bloco `eixos` não existem para o treinado; (4) a proveniência (`proveniencia_llm`)
com o modelo local. Sem prosa (narrativa/veredito saíram), o frontend precisa renderizar o filme
só com os bullets: o dono decide se publica primeiro assim, com ou sem bloco de condições.
