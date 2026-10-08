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

`prompt_eval_count` pequeno (≈ tamanho da review, não ≈ 929 + review) nas
chamadas depois da primeira é a evidência de que o prefixo foi reaproveitado.
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
