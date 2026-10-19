# Rodar o gate no Windows (Ollama local)

Passo a passo para um **clone limpo** no notebook Windows rodar o gate de
qualidade da classificação com um modelo local servido pelo Ollama. Custo:
**zero** — nenhuma chave de API é necessária e nenhuma chamada sai da máquina.

O gate mede o modelo local contra o gabarito humano de 100 reviews, tendo o
DeepSeek (já em disco, no repositório) como referência. Critério de parada,
igual ao do Gemini: **PARAR** se, em qualquer eixo ou no micro geral, o IC95 de
ΔF1 ficar inteiro abaixo de zero, **ou** ΔF1 ≤ −0,10, **ou** a falha na 1ª
tentativa passar de 2%.

Os comandos abaixo são do **PowerShell**.

## 1. Pré-requisitos

| O quê | Versão | Instalar |
|---|---|---|
| Git | qualquer recente | `winget install Git.Git` |
| Python | **3.10 ou mais novo** | `winget install Python.Python.3.12` |
| Ollama | recente | `winget install Ollama.Ollama` (ou ollama.com/download) |

Feche e reabra o PowerShell depois de instalar, para o `PATH` valer. Confira:

```powershell
git --version
python --version
ollama --version
```

## 2. Clonar

`core.autocrlf=false` mantém os arquivos de dados com as quebras de linha do
repositório (o gate compara resultados contra arquivos versionados).

```powershell
git clone -c core.autocrlf=false https://github.com/colletpedro/espectro-24.git
cd espectro-24
```

## 3. Python: venv e dependências

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # só neste terminal
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

`pip install -e .` traz o que o gate precisa (`requests`, `beautifulsoup4`,
`python-dotenv`). **Não** são necessários `google-genai`, `openai` nem
`anthropic` para rodar o gate com `--provider local`.

Para rodar também a suíte de testes (seção 8):

```powershell
pip install -e ".[llm,stills,test]"
```

## 4. Variáveis de ambiente

O gate local **não precisa de `.env` nem de chave**. Não crie nem copie `.env`.

Recomendadas (valem para o terminal atual):

```powershell
$env:PYTHONUTF8 = "1"          # o relatório imprime Δ, ≤, — e acentos; sem isso o console cp1252 quebra
chcp 65001 | Out-Null          # console em UTF-8
```

Opcionais — o padrão já serve para o Ollama no próprio Windows:

| Variável | Padrão | Para quê |
|---|---|---|
| `ESPECTRO24_OLLAMA_URL` | `http://localhost:11434` | endereço do Ollama (outra máquina da rede, p.ex. `http://192.168.0.7:11434`) |
| `ESPECTRO24_OLLAMA_PRAZO_S` | `600` | prazo por chamada, em segundos. Na CPU uma review longa leva 1–2 min e a 1ª chamada soma a carga do modelo; suba para `900` ou mais com modelo grande |
| `ESPECTRO24_OLLAMA_NUM_CTX` | `8192` | janela de contexto (prefixo de ~929 tokens + a review) |
| `ESPECTRO24_OLLAMA_NUM_PREDICT` | `2000` | teto de tokens de saída |
| `ESPECTRO24_OLLAMA_THINK` | `false` | nível de raciocínio: `false`, `low`, `medium` ou `high`. **`gpt-oss` não desliga com `false`** — use `low` (ou mais). qwen3/mistral: deixe `false`. O nível usado vai em cada registro e no `gate.json`. Com raciocínio ligado, os tokens pensados contam no teto de saída: suba `ESPECTRO24_OLLAMA_NUM_PREDICT` (ex.: `4000`) se aparecer `finish_reason: length` |
| `ESPECTRO24_OLLAMA_TEMPERATURE` | (padrão do modelo) | só se quiser fixar |

**Uma variável é do servidor, não do gate:** `OLLAMA_NUM_PARALLEL=1`. O Ollama
reaproveita o prefixo fixo de 929 tokens (o system prompt) entre chamadas
consecutivas; com mais de um slot, esse reaproveitamento pode se perder. No
Windows o Ollama sobe como app da bandeja, então:

```powershell
setx OLLAMA_NUM_PARALLEL 1
```

Depois **saia do Ollama pela bandeja (Quit) e abra de novo**. Ou, sem app:

```powershell
$env:OLLAMA_NUM_PARALLEL = "1"; ollama serve
```

## 5. Baixar o modelo e conferir o servidor

```powershell
ollama pull <modelo>          # ex.: ollama pull qwen3:8b
ollama list                   # o modelo precisa aparecer aqui
Invoke-RestMethod http://localhost:11434/api/tags | ConvertTo-Json -Depth 3
```

O nome passado ao gate (`--modelo`) é **exatamente** o de `ollama list`.

## 6. Rodar o gate

Três etapas, **nesta ordem** (o verificador roda sobre o consenso dos passes).
Substitua `<modelo>`. As chamadas são sequenciais, na ordem do gabarito; é
normal demorar (CPU). **Pode interromper e reexecutar**: só as reviews sem
`ok: true` são refeitas.

```powershell
python scripts/gate_gemini_classificacao.py --provider local --modelo <modelo> passes
python scripts/gate_gemini_classificacao.py --provider local --modelo <modelo> verificar
python scripts/gate_gemini_classificacao.py --provider local --modelo <modelo> comparar
```

- `passes`: 100 reviews × 3 passes de classificação (300 chamadas).
- `verificar`: o verificador `V2_alvo` × 3 passes, só nas reviews em que o
  consenso do modelo marcou `impacto_emocional`.
- `comparar`: sem chamada nenhuma — calcula as métricas, o bootstrap, o
  critério de parada e o resumo de tempo. Termina imprimindo **PARAR** ou
  **PASSA** e os motivos.

O comando falha cedo, com mensagem, se o Ollama estiver fora do ar ou o
modelo não estiver baixado.

### Onde ficam os resultados

`resultado\auditoria-acuracia\local\<modelo>\` (no nome da pasta, `:` vira `-`
e `/` vira `_`: `qwen3:8b` → `qwen3-8b`):

- `classificacao_passe_{1,2,3}.jsonl` e `V2_alvo_passe_{1,2,3}.jsonl` — um
  registro por chamada, com `provider: "local"`, `modelo`, `modelo_efetivo`,
  `custo_usd: 0.0`, e o tempo: `latencia_s` (parede), `leitura_prompt_s`,
  `geracao_s`, `carga_s`, `total_s`, `prompt_eval_count`, `eval_count`.
  Chamada que falha também grava provider, modelo e `latencia_s`.
- `gate.json` — o relatório (`gate.parar`, `gate.motivos`, `gate_por_eixo`,
  `custo.tempo_local` com média/p50/p95/máximo de cada tempo).

O sinal de que o prefixo foi reaproveitado é o **tempo de leitura do prompt
cair**: `leitura_prompt_s` alto na primeira chamada (~23 s medidos) e baixo nas
seguintes (~1,2 s). Está resumido em `custo.tempo_local.reaproveitamento_do_prefixo`
do `gate.json`. **Não** use `prompt_eval_count` como sinal: o Ollama o reporta
com o prompt inteiro, reaproveitado ou não.
Se `total_s` máximo chegar perto do prazo, suba `ESPECTRO24_OLLAMA_PRAZO_S`.

### Devolver o resultado ao GitHub

Só a pasta do modelo — nunca `.env`, `dados\bruto\` nem `resultado\votacao-3\`:

```powershell
git add resultado/auditoria-acuracia/local/<pasta-do-modelo>
git commit -m "gate local: <modelo>"
git push
```

## 7. Problemas comuns

| Sintoma | Causa / saída |
|---|---|
| `Ollama inacessível em http://localhost:11434` | servidor parado: abra o app Ollama ou rode `ollama serve`; ou ajuste `ESPECTRO24_OLLAMA_URL` |
| `modelo '...' não está no Ollama` | `ollama pull <modelo>` e confira o nome em `ollama list` |
| muitas falhas `prazo de 600s estourado` | CPU lenta ou modelo grande: `$env:ESPECTRO24_OLLAMA_PRAZO_S = "1200"`; falha por prazo conta na taxa de falha do gate |
| `UnicodeEncodeError` ao imprimir | falta `$env:PYTHONUTF8 = "1"` (seção 4) |
| `ModuleNotFoundError: bs4` / `espectro24` | venv não ativado, ou falta `pip install -e .` dentro dele |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `comparar` diz "nenhum passe de classificação" | rode `passes` e `verificar` antes (com o mesmo `--modelo`) |

## 8. Conferir a instalação sem o Ollama

Os testes do provider usam um servidor falso e não precisam do Ollama:

```powershell
pytest tests/test_provider_local.py -q
```

A suíte inteira (`pytest -q`, com `pip install -e ".[llm,stills,test]"`) tem
**4 falhas conhecidas, anteriores ao provider local**, todas de testes que
leem o catálogo publicado (`test_aplicar_lei_margem`, `test_condicoes`,
`test_hero_faixa_frontend`, `test_veredito_briefing`). Não são do Windows nem
do gate; qualquer falha *além* dessas merece atenção.

## 9. Gerar a prosa local dos 5 filmes (gpt-oss:20b) — comparação cega

Roda **síntese, rotulagem, narrativa, veredito e condições** com o modelo local
sobre 5 filmes **já publicados**, para o dono comparar, às cegas, com o texto
publicado. É uma exceção escopada (`espectro24.prosa_local`): não escreve em
`resultado/`, não toca nos 99 publicados, recusa o lote C22 e custa **zero**.
Os 5 filmes (`FILMES_COMPARACAO`): `anatomy-of-a-fall` (arthouse, contraste
temático), `mother-2017` (divisivo, valorativo), `napoleon-2023` (invertido,
valorativo), `the-substance` (aclamado, temático), `incendies` (aclamado,
valorativo) — os cinco com condições publicadas.

**Antes:** `git pull` (traz o código desta seção), venv ativado, e o mesmo
cuidado de memória do gate: feche o que puder (navegador, apps), confira
RAM+VRAM livres e acompanhe o pagefile — a janela de contexto da prosa é maior
(24.576 tokens) que a do gate (8.192).

```powershell
$env:PYTHONUTF8 = "1"
$env:ESPECTRO24_OLLAMA_THINK = "low"          # gpt-oss não desliga o raciocínio; low é o do gate
ollama pull gpt-oss:20b                       # se ainda não estiver
python scripts/gerar_prosa_local.py --modelo gpt-oss:20b --saida prosa-local --filmes-padrao
```

- **Pode interromper e reexecutar:** filme com `prosa-local\<slug>.json` pronto
  é pulado. O filme em andamento recomeça do zero (não há checkpoint por
  estágio).
- **Seguir como está em produção:** best-of-3 por estágio (`--n` só para teste).
  São ~15–19 chamadas por filme.
- **Variáveis da prosa (opcionais):** `ESPECTRO24_OLLAMA_PRAZO_PROSA_S` (padrão
  1800 s por chamada), `ESPECTRO24_OLLAMA_NUM_CTX_PROSA` (24576),
  `ESPECTRO24_OLLAMA_NUM_PREDICT_PROSA` (6000 na síntese/rotulagem, 12000 na
  prosa; **inclui os tokens de raciocínio**).
- **O que olhar:** `prosa-local\<slug>.telemetria.json` — `falhas` por estágio
  (vazio = sem falha), `estagios.<estágio>.finish_reason` (`length` = o teto de
  saída cortou: suba `NUM_PREDICT_PROSA`), tempos por chamada, `think` e
  `modelo_efetivo` em cada chamada.

**Tempo estimado: ~25 min por filme, ~2h15 para os cinco** (faixa 1h30–3h30).
Estimativa, não medida: sai das velocidades do gate do gpt-oss (leitura do
prompt ~40–80 tokens/s, geração ~14 tokens/s) e dos tamanhos reais dos prompts
dos 5 filmes — síntese 3 × ~6 mil tokens de entrada (~11 min), rotulagem
(~2 min), narrativa (~5,5 min; as 3 amostras repetem o mesmo prompt, então só a
1ª paga a leitura), veredito (~2 min), condições (~4 min; o prompt de sistema
tem 11 mil caracteres). O primeiro filme dá o número real: se passar de 40 min,
a faixa pessimista vale.

**Depois:** levar `prosa-local\` para o Mac. O jeito mais simples é um commit no
branch `gate-local` (NUNCA em `main`):

```powershell
git switch gate-local
git add prosa-local
git commit -m "prosa local: 5 filmes, gpt-oss:20b think=low"
git push
```

No Mac, `scripts/comparacao_cega_prosa.py` monta o documento de leitura cega
(A/B sorteado por filme, sem dizer qual é qual), o mapeamento com hash em
arquivo separado e as métricas dos validadores.

## 10. Juiz dos bullets (qwen3:14b) — checagem de apoio

Para cada bullet da síntese dos 5 filmes (lado publicado, do DeepSeek, e lado
local, do qwen3:14b), o juiz recebe o bullet e **uma** review recuperada por
vez e responde `{"menciona": true}` ou `{"menciona": false}`. A entrada já vem
pronta do Mac (`checagem-bullets\juiz_entrada.jsonl`, no branch `gate-local`,
com o texto das reviews dentro): aqui só se roda o juiz. Custo **zero**; não
escreve em `resultado/`.

**Antes — as mesmas guardas de memória do gate:**

- feche o que puder (navegador, apps), confira RAM+VRAM livres e acompanhe o
  pagefile;
- `OLLAMA_NUM_PARALLEL=1` no servidor (§4): as chamadas são uma por vez e o
  system prompt fica no KV entre elas;
- só o qwen3:14b carregado: `ollama ps`; se outro modelo aparecer (p.ex. o
  gpt-oss da §9), `ollama stop <modelo>`;
- a janela é a do gate (`ESPECTRO24_OLLAMA_NUM_CTX`, padrão 8192) — a maior
  review da entrada tem ~5 mil caracteres, folga de sobra. Não use as
  variáveis `_PROSA` da §9, que não valem aqui;
- raciocínio desligado: `ESPECTRO24_OLLAMA_THINK=false` (o padrão).

```powershell
git fetch
git switch gate-local
git pull
.\venv\Scripts\Activate.ps1
pip install -e .                               # só se o venv for novo
$env:PYTHONUTF8 = "1"
$env:ESPECTRO24_OLLAMA_THINK = "false"
ollama list                                    # qwen3:14b precisa aparecer
python scripts/checagem_bullets.py juiz --modelo qwen3:14b --dir checagem-bullets
```

- **900 chamadas.** Tempo estimado: **~1h30** (faixa ~1h10–3h), em
  `checagem-bullets\juiz_estimativa.md`. Estimativa, não medição: sai das
  velocidades do qwen3:14b medidas no gate deste notebook. O progresso sai a
  cada 25 chamadas, com o tempo que falta; se as primeiras 25 passarem de
  ~5 min, a ponta pessimista vale.
- **Pode interromper e reexecutar:** par com `ok: true` em
  `checagem-bullets\juiz_saida.jsonl` não é refeito; o que falhou é refeito.
- **No fim** a última linha diz `pares sem veredito: 0 — completo`. Se não
  disser, rode o mesmo comando de novo.
- **O que olhar** em `juiz_saida.jsonl`: `finish_reason` (`length` = o teto
  de 64 tokens cortou — não deveria acontecer com uma resposta de ~8 tokens),
  `modelo_efetivo` e `think` em cada registro.

**Depois:**

```powershell
git add checagem-bullets/juiz_saida.jsonl
git commit -m "checagem bullets: juiz qwen3:14b nos 900 pares"
git push
```

**A rotulagem do dono (Parte 3) não depende do juiz** e pode ser feita antes,
no Mac: `checagem-bullets\rotulagem\rotulagem_dono.md`, respostas em
`rotulos_dono.csv`. Quem rotula não deve abrir `juiz_saida.jsonl` antes de
terminar. Com os dois prontos, no Mac:

```bash
python scripts/checagem_bullets.py validar-juiz --dir checagem-bullets
python scripts/checagem_bullets.py relatorio --dir checagem-bullets
```

## 11. Juiz v2 dos bullets (gpt-oss:20b) — calibração nos 40 pares

O juiz v1 (§10) reprovou contra o rótulo do dono (precisão 0,727). O v2 troca o
modelo (gpt-oss:20b, que não escreveu nenhum dos lados), exige uma **frase de
prova** literal da review — conferida pelo código, não pelo modelo — e usa o
mesmo guia que o dono usou para rotular. Código: `scripts/juiz_bullets_v2.py`.
Custo **zero**; não escreve em `resultado/`.

Aqui roda só a **calibração**: o v2 nos mesmos 40 pares que o dono já rotulou.
Ela serve para ajustar o prompt, não para validar o juiz (a validação é numa
amostra nova, depois de a versão ser congelada).

**A configuração inteira está no código** e entra num hash (`config_sha256`,
gravado em cada registro): modelo, `think=low`, `num_ctx` 3584, `num_predict`
1024, `seed` 20261019, temperatura do modelo. As variáveis
`ESPECTRO24_OLLAMA_THINK`, `_NUM_CTX` e `_NUM_PREDICT` **não valem** para este
juiz; `ESPECTRO24_OLLAMA_TEMPERATURE` definida faz o juiz se recusar a rodar.

**Antes — as mesmas guardas de memória do gate do gpt-oss:** feche o que puder,
confira RAM+VRAM livres (o gate rodou com ≥ 13,0 GB) e acompanhe o pagefile;
`OLLAMA_NUM_PARALLEL=1`; só o gpt-oss carregado (`ollama ps`; `ollama stop
qwen3:14b` se ele aparecer).

Dois passos, na ordem:

1. `medir-contexto` — os 10 prompts mais longos dos 900, com janela folgada
   (8192) e 1 token de saída, para o servidor contar os tokens exatos. Grava
   `checagem-bullets\juiz_v2\contexto_medido_v2.0.json` e diz `CABE` ou `NÃO
   CABE` em 3584. Sem `CABE`, o juiz se recusa a rodar. Poucos minutos.
2. `juiz --calibracao` — os 40 pares. **~10 min (p95 ~19 min)**, estimativa a
   partir das velocidades do gate do gpt-oss neste notebook
   (`checagem-bullets\juiz_v2\preparo_v2.0.md`). Retomável: par já feito com a
   mesma configuração não é refeito.

```powershell
git fetch
git switch gate-local
git pull
.\venv\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
Remove-Item Env:ESPECTRO24_OLLAMA_TEMPERATURE -ErrorAction SilentlyContinue
ollama list                                    # gpt-oss:20b precisa aparecer
python scripts/juiz_bullets_v2.py medir-contexto --dir checagem-bullets
python scripts/juiz_bullets_v2.py juiz --calibracao --dir checagem-bullets
```

- **No fim** a última linha diz `pares sem veredito: 0 — completo`. Se não
  disser, rode o último comando de novo.
- **O que olhar** em `checagem-bullets\juiz_v2\calibracao_v2.0_saida.jsonl`:
  `finish_reason` (falha com `length` = o raciocínio passou de 1024 tokens),
  `erro` com `contexto` (o prompt encostou na janela), `think` = `low` e
  `modelo_efetivo` = `gpt-oss:20b`. O `pensamento` de cada par fica gravado.
- Se o seu `ollama ps` tiver a coluna `CONTEXT`, ela deve mostrar 3584 durante o
  passo 2 (8192 no passo 1).

**Depois:**

```powershell
git add checagem-bullets/juiz_v2
git commit -m "checagem bullets: juiz v2.0 (gpt-oss:20b) na calibração dos 40 pares"
git push
```

No Mac, a calibração contra o rótulo do dono:

```bash
python scripts/juiz_bullets_v2.py calibrar --dir checagem-bullets
```
