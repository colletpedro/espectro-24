# Roteiro da Fase 2 — PUBLICADO e BASE no teste (depois, Fase 4)

Data: 2026-11-03. Quem roda é o dono. Fase 3 registrada (`7719102`). Pelo
`PREREGISTRO_AVALIACAO.md` (seções 1, 2 e 5), a Fase 2 gera a BASE nos 89
buckets de teste, julga PUBLICADO e BASE, calcula C1–C4 dos dois e fixa δ₂.
**O TREINADO não é gerado nem julgado até o gate da Fase 2 fechar:**
`gerar_sintese_teste.py gerar --lado treinado` recusa enquanto não existir
`finetune/GATE_FASE2.md` COMMITADO, igual ao HEAD, com o sha256 do
`c1_c4_fase2.json` e do `delta2.json` atuais (`main`, guarda nova).

Scripts: `main` `126ed74` (guarda, `gate_fase2.py` e `ollama_pronto.py`; este roteiro cita `gate_fase2.py` e `ollama_pronto.py`, que
chegam ao Windows pelo bloco 0). Entradas da medição: `main`
`742cfe3c7d443decd7cfd395e32dce080011bd45`, conjunto MEDIDO de 162 arquivos,
sha256 `f2a7a0ba4b767516e3c9936b3af4a7877c6cd7074d4a9fc25779284163c97e45`
(`git archive`; os scripts recusam se o conjunto mudar). Etiquetas:
**MEDIDO**, **ESTIMADO**, **PROPOSTO**.

## Visão geral

| bloco | onde | o quê | tempo (ESTIMADO) | parada |
|---|---|---|---|---|
| 1 | Mac | `plano` + `preparar --lado publicado` | ~20 min | plano e entrada do publicado commitados |
| 2 | Windows, noite 1 | síntese da BASE (89) → juiz do PUBLICADO | ~9–17 h | `fim — rode calcular` do juiz |
| 3 | Mac | `fixar-delta2` + `preparar --lado base` | ~20 min | δ₂ e entrada da base commitados |
| 4 | Windows, noite 2 | juiz da BASE | ~5–12 h | `fim — rode calcular` |
| 5 | Mac | `calcular` (com δ₂ fixado) + `gate_fase2.py` | ~5 min | `GATE_FASE2.md` commitado → PARE |

Total de máquina no Windows (ESTIMADO, pelos números MEDIDOS da Fase 1 e da
limpeza): síntese 88 × ~150 s + retentativas + outlier ≈ 3,8–4,6 h; juiz
~534 bullets × ~3,2 pares × 16,2 s ≈ 7,7 h por lado (faixa 5–12 h). A noite
1 passa de uma madrugada se o juiz ficar no alto da faixa: tudo é retomável.

**PROPOSTO (ordem):** o `fixar-delta2` vem ANTES do `calcular` (o
`COMANDOS_FASE2_FASE3.md` tinha o contrário), para o C2 descritivo da base
já sair com o δ₂ fixado; o δ₂ só depende do PUBLICADO e dos buckets fora por
memória (conhecidos ao fim da noite 1), então é fixado antes de a base ser
julgada. Nada do pré-registro muda; o `gate_fase2.py` recusa um
`c1_c4_fase2.json` calculado sem o δ₂ fixado.

## Regras do Windows (todas as sessões)

- PowerShell NOVO, **fora do Claude Code** (`gerar` e `julgar` recusam
  `CLAUDECODE`). Repositório `C:\espectro\espectro-24`, branch `finetune`.
- **Bloco 0 completo no início de CADA sessão**, mesmo para retomar.
- Python e Kaggle só do venv: `.\venv\Scripts\python.exe`,
  `.\venv\Scripts\kaggle.exe` (a Fase 2 não tem passo de Kaggle).
- **Não digite `ollama list` nem `ollama ps`** (o terminal travou duas vezes
  depois deles, no fim de um bloco). Para conferir o servidor:
  `.\venv\Scripts\python.exe scripts\finetune\ollama_pronto.py --modelo gpt-oss:20b`
  (HTTP com timeout; saída 0 = pronto).
- **Retomável:** se cair (latência, memória, queda de luz, Ctrl+C), abra um
  PowerShell novo, rode o bloco 0 e a MESMA linha do bloco. Par já feito não é
  refeito; bullet já julgado não é rejulgado.
- Fecho de todo bloco do Windows (depois do commit):

```powershell
git restore --staged --worktree scripts/finetune src/espectro24/local_ollama.py
git pull --rebase origin finetune
git push origin finetune
```

## Bloco 0 — preparo do Windows (início de CADA sessão)

```powershell
cd C:\espectro\espectro-24
git restore --staged --worktree scripts/finetune src/espectro24/local_ollama.py
git pull
git checkout origin/main -- scripts/finetune src/espectro24/local_ollama.py
Remove-Item Env:GEMINI_API_KEY, Env:GEMINI_API_KEY_PROD, Env:TMDB_API_KEY, Env:DEEPSEEK_API_KEY, Env:GOOGLE_API_KEY, Env:ANTHROPIC_API_KEY, Env:OPENAI_API_KEY, Env:ESPECTRO24_OLLAMA_TEMPERATURE -ErrorAction SilentlyContinue
```

Conferência (tem de imprimir `True`): o `gate_fase2.py` chegou de `main`.

```powershell
Test-Path scripts\finetune\gate_fase2.py
```

## Bloco 1 — Mac: plano e entrada do PUBLICADO (~20 min)

O `plano` conta os tokens exatos dos 89 pares (tokenizer do Qwen3-8B) e
grava o `num_ctx` de cada um; o `preparar` do publicado faz a recuperação e5
e confere o sha dos 5 de referência (MEDIDO em 2026-10-31: NÃO bate,
`059f3825…`; o publicado é julgado inteiro). O `preparar` do publicado não
depende da base, por isso vem já aqui, antes da noite 1.

Uma vez no Mac, se ainda não existir: `mkdir -p ~/.espectro24-pylib && ln -sf
/opt/homebrew/lib/python3.14/site-packages/tokenizers ~/.espectro24-pylib/tokenizers`.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/gerar_sintese_teste.py plano && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/avaliar_c1_c4.py preparar --lado publicado; rm finetune
```

Parada: o `plano` imprime `89 pares` e o sha; o `preparar` imprime o
`entrada_meta.json` com `"bate": false`. Se o `preparar` caiu depois de
gravar `entrada.jsonl` e antes do `entrada_meta.json`, apague só
`finetune/fase2/juiz/publicado/entrada.jsonl` e rode o `preparar` de novo (ele
recusa sobrescrever uma entrada).

```bash
git -C ../espectro-24-finetune add finetune/fase2/plano_teste.json finetune/fase2/juiz/publicado && git -C ../espectro-24-finetune commit -m "finetune: plano da sintese de teste e entrada do juiz do publicado (fase 2)" -- finetune/fase2/plano_teste.json finetune/fase2/juiz/publicado && git -C ../espectro-24-finetune push origin finetune
```

## Bloco 2 — Windows, noite 1: síntese da BASE e juiz do PUBLICADO

Bloco 0 antes. Depois, UMA linha (de madrugada; se cair, a mesma linha
retoma). Ela: gera a base nos 89 buckets (partida limpa, guardas de latência
e de RAM, outlier `500-days-of-summer/positivas` por último); só se a síntese
terminar, sobe o Ollama desacoplado e confere o `gpt-oss:20b`; mede o
contexto do juiz; julga o publicado com parada no 2º sim.

```powershell
$PY=".\venv\Scripts\python.exe"; $LB="finetune\kaggle\base_saida_qwen3\base\qwen3-8b-base__14336\log.json"; & $PY scripts\finetune\gerar_sintese_teste.py gerar --lado base --log-kernel $LB; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\ollama_pronto.py --subir --modelo gpt-oss:20b }; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py medir-contexto --lado publicado }; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py julgar --lado publicado }
```

Leitura das paradas:
- `gerar` com "a guarda de RAM derrubou o servidor": o par ficou gravado; a
  mesma linha tenta UMA vez mais (partida limpa); se cair de novo, o par fica
  `fora_por_memoria` (sai dos dois lados de toda comparação) e a linha segue;
- `gerar` com "PAUSA pela guarda de latência" ou `julgar` com saída 3
  ("PAUSADO"): a chamada lenta foi gravada; rode a mesma linha;
- `ollama_pronto` com `"instalado": false`: o servidor não subiu ou o
  `gpt-oss:20b` não está nele; não julgue, anote e pare;
- `medir-contexto` com "NÃO CABE": PARE (o juiz não roda fora da janela);
- fim normal: `julgar` imprime `fim — rode calcular`.

Commit (também serve para um fim parcial: o que está gravado é retomável):

```powershell
git add finetune\fase2\sintese_base finetune\fase2\juiz\publicado
git commit -m "finetune: sintese da base nos 89 buckets e juiz no publicado (fase 2)" -- finetune\fase2\sintese_base finetune\fase2\juiz\publicado
```

(fecho do Windows). Se a noite acabou antes do `fim`, a próxima sessão é de
novo bloco 0 + a mesma linha + o mesmo commit; a síntese já feita é pulada
(`0 a fazer`) e o juiz retoma.

## Bloco 3 — Mac: δ₂ fixado e entrada da BASE (~20 min)

Só com o bloco 2 completo (`fim — rode calcular` do publicado). O δ₂ sai da
taxa de apoio ≥ 2 do PUBLICADO nos buckets mantidos (pré-registro, C2) e é
gravado UMA vez; o `preparar` da base faz a recuperação e5 dos bullets da
base.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/avaliar_c1_c4.py fixar-delta2 && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/avaliar_c1_c4.py preparar --lado base; rm finetune
```

Parada: `delta2.json` com `p0_apoio_2` e `delta2_pp`; o `entrada_meta.json`
da base. Commit em dois (o δ₂ em commit próprio, antes de qualquer conta da
base):

```bash
git -C ../espectro-24-finetune add finetune/fase2/delta2.json && git -C ../espectro-24-finetune commit -m "finetune: delta2 fixado pela taxa do publicado (fase 2)" -- finetune/fase2/delta2.json && git -C ../espectro-24-finetune add finetune/fase2/juiz/base && git -C ../espectro-24-finetune commit -m "finetune: entrada do juiz da base (fase 2)" -- finetune/fase2/juiz/base && git -C ../espectro-24-finetune push origin finetune
```

## Bloco 4 — Windows, noite 2: juiz da BASE

Bloco 0 antes. UMA linha (retomável):

```powershell
$PY=".\venv\Scripts\python.exe"; & $PY scripts\finetune\ollama_pronto.py --subir --modelo gpt-oss:20b; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py medir-contexto --lado base }; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py julgar --lado base }
```

Paradas: como no bloco 2. Commit:

```powershell
git add finetune\fase2\juiz\base
git commit -m "finetune: juiz na base (fase 2)" -- finetune\fase2\juiz\base
```

(fecho do Windows)

## Bloco 5 — Mac: C1–C4 dos dois lados e o gate (~5 min)

Só com o bloco 4 completo. `calcular` grava `c1_c4_fase2.json` (publicado e
base, base − publicado descritivo, com o δ₂ fixado); `gate_fase2.py` recusa se
o δ₂ não estiver fixado, se faltar um lado, se o treinado já tiver síntese ou
se as taxas que ele refaz não forem as do `calcular`, e grava
`finetune/GATE_FASE2.md` (C1–C4 com IC 95% por filme, δ₂, buckets fora e
por quê, tempos, comparação com os 2/90 antigos, o que não foi medido).

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/avaliar_c1_c4.py calcular > /dev/null && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/gate_fase2.py; rm finetune
```

```bash
git -C ../espectro-24-finetune add finetune/fase2/c1_c4_fase2.json finetune/GATE_FASE2.md && git -C ../espectro-24-finetune commit -m "finetune: C1-C4 da fase 2 (publicado e base) e gate da fase 2" -- finetune/fase2/c1_c4_fase2.json finetune/GATE_FASE2.md && git -C ../espectro-24-finetune push origin finetune
```

**PARE aqui.** O gate é lido antes de qualquer passo da Fase 4.

## Depois do gate: Fase 4 (NÃO faz parte deste roteiro)

Na ordem do pré-registro (seção 5.4), UMA vez: síntese do treinado (a guarda
confere o `GATE_FASE2.md` commitado), `preparar`/juiz do treinado, `calcular`
(decisão C1–C4), C5, C6. Os comandos da Fase 4 vão num roteiro próprio,
escrito depois de lido o gate.

## O que este roteiro NÃO garante (não medido)

- O `ollama_pronto.py --subir` foi conferido só no Mac (sem `--subir`); no
  Windows o servidor desacoplado (`DETACHED_PROCESS`) não foi testado
  (ESTIMADO que sobreviva ao fim do Python, como o `ollama serve` do
  `subir_ollama`).
- Os tempos são ESTIMADOS (Fase 1 e limpeza); o outlier e as retentativas não
  têm medida.
- O `gate_fase2.py` foi testado com dados sintéticos; a coleta real só roda
  com os arquivos da Fase 2.
