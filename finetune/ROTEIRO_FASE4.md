# Roteiro da Fase 4 — TREINADO no teste (UMA vez), C5 e C6

Data: 2026-11-04. Quem roda é o dono. Gate da Fase 2 (`GATE_FASE2.md`,
`275ca16`) **aprovado pelo dono em 04/11/2026** (`FINETUNE_REGISTRO.md`). τ do
M2 fixado só com treino (`DESVIO_P03.md`, `a8b849f`; `fase4/tau_m2.json`,
`b278172`). Pelo `PREREGISTRO_AVALIACAO.md` (seção 5.4), o treinado é gerado e
medido **UMA vez**: síntese, juiz, C1–C4, C5, C6, nesta ordem. Sem segunda
geração do treinado no teste.

Scripts: `main` `13c970e` (modo cego, `fase4_m2.py`, C6 com a pergunta por
lado; `tau_m2.py` em `6d0212c`). Entradas da medição: as mesmas da Fase 2
(`main` `742cfe3`, conjunto MEDIDO de 162 arquivos, sha256 `f2a7a0ba…`; os
scripts recusam se mudar). Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.

## CEGUEIRA DO DONO (vale até o `RESULTADO_FASE4.md`)

O dono ainda faz C5 e C6. Até os dois estarem registrados, nenhum número de
C1–C4, M1, M2, taxa do juiz ou validador do TREINADO aparece na tela:

- no lado treinado, `gerar`, `preparar`, `julgar`, `calcular` e `fase4_m2`
  mostram só progresso, caminho e sha256; o que imprimiriam vai completo para
  `finetune/fase4/cego/*.log` (`_cego.py`);
- C5 e C6 (`avaliar`) também só mostram o sha256 do resultado;
- **NÃO abra** (no editor, no Finder, no GitHub, em diff de commit):
  `finetune/fase4/cego/`, `finetune/fase2/sintese_treinado/`,
  `finetune/fase2/juiz/treinado/`, `finetune/fase4/especificidade_mapa.json`,
  `finetune/fase4/leitura_mapa.json`, `finetune/fase4/*_resultado.json`;
- os únicos arquivos do treinado que o dono abre são os dois documentos cegos
  em `docs/arquivo-de-estudos/finetune-fase4/` (fora do git) e os CSVs de
  resposta ao lado deles;
- o resultado só é revelado no `finetune/RESULTADO_FASE4.md`, escrito depois
  do C6 avaliado.

## Visão geral

| bloco | onde | o quê | tempo (ESTIMADO) | parada |
|---|---|---|---|---|
| 1 | Windows, noite 1 | síntese do TREINADO (89) | ~4–5 h | `0 a fazer` ao rodar de novo |
| 2 | Mac | `preparar --lado treinado` + documento do C5 | ~20 min | entrada e mapa do C5 commitados |
| 3 | Windows, noite 2 | juiz do TREINADO (o dono rotula o C5 em paralelo) | ~5–12 h | `fim — rode calcular` |
| 4 | Mac | `calcular` (C1–C4) + `fase4_m2.py` | ~10 min | "calculado, sha …" dos dois |
| 5 | Mac | C5 avaliado (depois dos 126 rótulos) | ~1 min | "avaliado, sha …" |
| 6 | Mac | documento do C6 → leitura do dono → C6 avaliado | ~1 h do dono | "avaliado, sha …" → avisar o Claude |

Tempos ESTIMADOS pelos MEDIDOS da base na Fase 2: síntese 4,0 h somadas
(mediana 154 s por bucket); juiz da base 7,1 h de latência somada.

## Regras do Windows (todas as sessões)

- PowerShell NOVO, **fora do Claude Code** (`gerar` e `julgar` recusam
  `CLAUDECODE`). Repositório `C:\espectro\espectro-24`, branch `finetune`.
- **Bloco 0 completo no início de CADA sessão**, mesmo para retomar.
- Python só do venv: `.\venv\Scripts\python.exe`.
- **Não digite `ollama list` nem `ollama ps`.** Para conferir o servidor:
  `.\venv\Scripts\python.exe scripts\finetune\ollama_pronto.py --modelo gpt-oss:20b`
  (HTTP com timeout; saída 0 = pronto).
- **Retomável:** se cair (latência, memória, queda de luz, Ctrl+C), abra um
  PowerShell novo, rode o bloco 0 e a MESMA linha do bloco. Par já feito não é
  refeito; bullet já julgado não é rejulgado. Retomar não é "segunda geração":
  só completa os pares que faltam.
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

Conferência (tem de imprimir `True`): o modo cego chegou de `main`.

```powershell
Test-Path scripts\finetune\_cego.py
```

## Bloco 1 — Windows, noite 1: síntese do TREINADO

Bloco 0 antes. UMA linha (se cair, a mesma linha retoma). A guarda recusa se
o `GATE_FASE2.md` não for o commitado (com os sha256 do `c1_c4_fase2.json` e
do `delta2.json`), se o llama.cpp do treinado não for o da base, se o
`token_embd`/`output` do treinado não forem os da base (`tensores.json`,
DESVIO_P02) ou se o nome no Ollama não for o do GGUF do log
(`espectro-qwen3-8b-treinado`, MEDIDO no Mac em 04/11: as três guardas passam
com estes arquivos). Partida limpa, guardas de latência e de RAM, outlier
`500-days-of-summer/positivas` por último, como na base.

```powershell
$PY=".\venv\Scripts\python.exe"; $LT="finetune\kaggle\treino_saida_qwen3\treino\qwen3-8b-treinado__12288\log.json"; $LB="finetune\kaggle\base_saida_qwen3\base\qwen3-8b-base__14336\log.json"; & $PY scripts\finetune\gerar_sintese_teste.py gerar --lado treinado --log-kernel $LT --log-kernel-base $LB
```

O que aparece na tela: `[k/N] filme/bucket: gravado` (sem ok, JSON,
chamadas nem tempo). Leitura das paradas:
- "a guarda de RAM derrubou o servidor": o par ficou gravado; a mesma linha
  tenta UMA vez mais; se cair de novo, o par fica fora por memória (sai dos
  dois lados de toda comparação, inclusive do publicado e da base);
- "PAUSA pela guarda de latência": rode a mesma linha;
- "(erro do servidor: refeito ao rodar de novo)": rode a mesma linha;
- fim: rode a mesma linha de novo; tem de imprimir `0 a fazer`.

Commit (também serve para um fim parcial):

```powershell
git add finetune\fase2\sintese_treinado finetune\fase4\cego
git commit -m "finetune: sintese do treinado nos 89 buckets (fase 4)" -- finetune\fase2\sintese_treinado finetune\fase4\cego
```

(fecho do Windows)

## Bloco 2 — Mac: entrada do juiz do TREINADO e documento do C5 (~20 min)

Só com o bloco 1 completo (`0 a fazer`). O `preparar` faz a recuperação e5
dos bullets do treinado; o `amostrar` sorteia o C5 (semente 20261102, 60 do
treinado + 60 do publicado, 20 por bucket, + 6 repetidos a ≥ 40 posições,
`exibir` igual nas duas fontes, definição de G/E da Fase 1 no topo) e grava o
mapa com o selo fora do documento.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/avaliar_c1_c4.py preparar --lado treinado && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/fase4_especificidade.py amostrar; rm finetune
```

Parada: `preparado, entrada_meta.json sha256 …` e o JSON do `amostrar` com
`"itens": 126`, o caminho do documento e o selo. Se o `preparar` caiu depois
de gravar `entrada.jsonl` e antes do `entrada_meta.json`, apague só
`finetune/fase2/juiz/treinado/entrada.jsonl` e rode de novo.

```bash
git -C ../espectro-24-finetune add finetune/fase2/juiz/treinado finetune/fase4/especificidade_mapa.json finetune/fase4/cego && git -C ../espectro-24-finetune commit -m "finetune: entrada do juiz do treinado e sorteio do C5 (fase 4)" -- finetune/fase2/juiz/treinado finetune/fase4/especificidade_mapa.json finetune/fase4/cego && git -C ../espectro-24-finetune push origin finetune
```

**Rotulagem do C5 (o dono, enquanto o juiz roda):** abra
`docs/arquivo-de-estudos/finetune-fase4/rotulagem_especificidade.md` e
preencha `rotulos_especificidade.csv` (mesma pasta), `G` ou `E` em cada um
dos 126 ids. Não abra o mapa.

## Bloco 3 — Windows, noite 2: juiz do TREINADO

Bloco 0 antes. UMA linha (retomável):

```powershell
$PY=".\venv\Scripts\python.exe"; & $PY scripts\finetune\ollama_pronto.py --subir --modelo gpt-oss:20b; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py medir-contexto --lado treinado }; if ($LASTEXITCODE -eq 0) { & $PY scripts\finetune\avaliar_c1_c4.py julgar --lado treinado }
```

Na tela: `[n/30] filme · X min` (sem contagem de estados nem de pendentes).
Paradas: `ollama_pronto` com `"instalado": false` → não julgue, anote e pare;
`medir-contexto` com "NÃO CABE" → PARE; `julgar` com saída 3 ("PAUSADO") →
rode a mesma linha; fim normal: `fim — rode calcular`.

```powershell
git add finetune\fase2\juiz\treinado finetune\fase4\cego
git commit -m "finetune: juiz no treinado (fase 4)" -- finetune\fase2\juiz\treinado finetune\fase4\cego
```

(fecho do Windows)

## Bloco 4 — Mac: C1–C4 e M2 do TREINADO (~10 min)

Só com o bloco 3 completo. `calcular` grava
`finetune/fase4/cego/c1_c4_fase4.json` (decisão C1–C4 do treinado contra o
publicado, com o δ₂ fixado de 7,8 pp; base contra publicado e treinado contra
base como descrição) e recusa se já existir; `fase4_m2.py` grava
`finetune/fase4/cego/m2_fase4.json` com o τ do DESVIO_P03. Os dois só
imprimem o sha256.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/avaliar_c1_c4.py calcular && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY PYTHONPATH=$HOME/.espectro24-pylib ./venv/bin/python scripts/finetune/fase4_m2.py calcular; rm finetune
```

Parada: `calculado, c1_c4_fase4.json sha256 …` e `calculado, m2_fase4.json
sha256 …`.

```bash
git -C ../espectro-24-finetune add finetune/fase4/cego && git -C ../espectro-24-finetune commit -m "finetune: C1-C4 e M2 do treinado (fase 4, cego)" -- finetune/fase4/cego && git -C ../espectro-24-finetune push origin finetune
```

## Bloco 5 — Mac: C5 avaliado (depois dos 126 rótulos)

Critério pré-registrado: proporção de E do treinado entre os 60 distintos
(rótulo da 1ª ocorrência) **≥ 10%**, IC de Wilson 95% nos dois lados,
consistência dos 6 repetidos. `SELO` = o sha256 impresso no fim do documento.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/fase4_especificidade.py avaliar --selo SELO && cp docs/arquivo-de-estudos/finetune-fase4/rotulos_especificidade.csv ../espectro-24-finetune/finetune/fase4/; rm finetune
```

Parada: `avaliado, especificidade_resultado.json sha256 …`.

```bash
git -C ../espectro-24-finetune add finetune/fase4/especificidade_resultado.json finetune/fase4/rotulos_especificidade.csv && git -C ../espectro-24-finetune commit -m "finetune: C5 avaliado (rotulos do dono, fase 4)" -- finetune/fase4/especificidade_resultado.json finetune/fase4/rotulos_especificidade.csv && git -C ../espectro-24-finetune push origin finetune
```

## Bloco 6 — Mac: C6, leitura cega da síntese

Só com o C5 avaliado (o `montar` recusa antes). Treinado × publicado nos 5
filmes de referência, só os bullets e a observação de cada bucket (formato do
bloco "1. Bullets da síntese" de `prosa-local-qwen3-leitura/`), lados
sorteados por filme com a semente 20261103, mapa com selo fora do documento.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/fase4_leitura.py montar; rm finetune
```

```bash
git -C ../espectro-24-finetune add finetune/fase4/leitura_mapa.json && git -C ../espectro-24-finetune commit -m "finetune: documento do C6 montado (fase 4)" -- finetune/fase4/leitura_mapa.json && git -C ../espectro-24-finetune push origin finetune
```

**Leitura (o dono):** `docs/arquivo-de-estudos/finetune-fase4/leitura_cega.md`.
Por filme: **o lado A é publicável? o lado B é publicável?** — na coluna
`publicaria` de `leitura_respostas.csv`, `A`, `B`, `ambos` ou `nenhum`; na
coluna `melhor`, `A`, `B` ou `empate`. Critério pré-registrado: treinado
publicável em **≥ 4 de 5**; a preferência é descritiva.

```bash
cd ~/Downloads/espectro-24 && git -C ../espectro-24-finetune pull --ff-only && ln -s ../espectro-24-finetune/finetune finetune && env -u DEEPSEEK_API_KEY -u GEMINI_API_KEY ./venv/bin/python scripts/finetune/fase4_leitura.py avaliar --selo SELO && cp docs/arquivo-de-estudos/finetune-fase4/leitura_respostas.csv ../espectro-24-finetune/finetune/fase4/; rm finetune
```

```bash
git -C ../espectro-24-finetune add finetune/fase4/leitura_resultado.json finetune/fase4/leitura_respostas.csv && git -C ../espectro-24-finetune commit -m "finetune: C6 avaliado (leitura do dono, fase 4)" -- finetune/fase4/leitura_resultado.json finetune/fase4/leitura_respostas.csv && git -C ../espectro-24-finetune push origin finetune
```

**PARE aqui e avise o Claude.** O `finetune/RESULTADO_FASE4.md` (C1–C6 com
IC e veredito de cada um; "publicável" só se todos passam, senão qual falhou;
treinado × base em C1–C4, M2, validade na 1ª tentativa, tempos; o que não
foi medido) é escrito a partir dos arquivos de `fase4/`, e só então os
números aparecem. Resultado negativo se reporta igual.

## O que este roteiro NÃO garante (não medido)

- O modo cego foi testado com dados sintéticos (`tests/test_finetune_fase4_cego.py`);
  nas rodadas reais, só se confere pela tela.
- Mensagens de parada (memória, latência) vão para a tela e nomeiam o par:
  dizem que o par caiu, não como ele saiu.
- Se um bucket do treinado não tiver síntese, o documento do C6 mostra
  "_(sem síntese …)_" naquele bucket (formato pré-registrado): é a única
  informação de validade que o dono pode ver antes do relatório.
- Os tempos são ESTIMADOS pelos da base; o treinado pode gerar saídas de
  tamanho diferente.
- O `ollama_pronto.py --subir` no Windows rodou na Fase 2 (MEDIDO pelos commits
  `92632e8` e `1f685f6`), não nesta máquina hoje.
