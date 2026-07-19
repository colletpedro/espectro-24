# Espectro 24

Agregador de reviews do [Letterboxd](https://letterboxd.com) que separa opiniões
em três **buckets por nota** — negativas (0.5–2.5), medianas (3–3.5), positivas
(4–5) — e produz, via LLM, uma **síntese temática** de cada bucket, **sem
spoilers**, para quem ainda não assistiu ao filme.

A autoridade do projeto é [`SPEC.md`](SPEC.md) (v1.2.3). As incógnitas técnicas
foram resolvidas na Fase 1 — ver [`FASE1_INCOGNITAS.md`](FASE1_INCOGNITAS.md).

## Instalação

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e ".[llm]"                # empacotado (pyproject.toml, src-layout)
# ou só um provider: pip install -e ".[anthropic]"  /  pip install -e ".[gemini]"

export GEMINI_API_KEY=...              # provider default operacional atual
# ou: export ANTHROPIC_API_KEY=sk-...  # a chave define o provider por auto-detecção
```

A instalação registra o comando `espectro24` no PATH do venv (console script).

### Fornecendo a chave da API

Duas formas equivalentes — o CLI aceita as duas:

1. **Export manual no shell** (acima) — dura só a sessão do terminal.
2. **Arquivo `.env` na raiz do projeto** — persistente entre sessões:
   ```bash
   # .env (na raiz do projeto, ao lado de pyproject.toml)
   GEMINI_API_KEY=sua-chave-aqui
   ```
   O CLI carrega esse arquivo automaticamente no início da execução (via
   `python-dotenv`, dependência base). Se a variável já estiver exportada no
   ambiente, o valor exportado **tem prioridade** — o `.env` não a sobrescreve.

   `.env` já está no `.gitignore` por padrão — não é versionado.

## Uso

```bash
# por slug (pula a busca)
espectro24 --slug oppenheimer-2023

# por nome (resolve o slug; se ambíguo, lista candidatos p/ reexecutar com --slug)
espectro24 "city of god"

# só coleta + metadados, sem chamar o LLM
espectro24 --slug oppenheimer-2023 --no-synth

# reexecução 100% cache (zero rede)
espectro24 --slug oppenheimer-2023 --offline

# provider explícito (necessário se ambas as chaves estiverem no ambiente)
espectro24 --slug oppenheimer-2023 --provider gemini
espectro24 --slug oppenheimer-2023 --provider anthropic --model claude-sonnet-4-6

# tom da saída (mecanismo de A/B em desenvolvimento — SPEC §D2): estruturado
# (default) | narrativo (prosa) | ambos. narrativo/ambos gastam +1 chamada LLM.
espectro24 --slug oppenheimer-2023 --tom ambos
# comparar tons sobre a MESMA síntese já gerada (só a chamada do narrador):
espectro24 --slug oppenheimer-2023 --tom ambos --reuse-synthesis
```

### Tom de saída (v1.2.0 — dev/A/B)
`--tom` alterna entre a saída **estruturada** (temas + frequências, default) e a
**narrativa** (uma prosa de 200–350 palavras gerada por uma etapa pós-síntese que
lê **só o JSON já validado** — nunca as reviews brutas). É um **mecanismo de
desenvolvimento** para o A/B humano; a v2 consolidará um tom único. Nos dois
tons, os metadados de coleta e os avisos de modo degradado **nunca somem**.

### Provider do LLM (v1.1.1)
Sem `--provider`, o CLI auto-detecta pela chave presente no ambiente
(`GEMINI_API_KEY` ou `ANTHROPIC_API_KEY`). Se **ambas** estiverem presentes, ou
se **nenhuma** estiver, o CLI recusa com um erro claro (antes de gastar
qualquer requisição de coleta) pedindo `--provider {gemini,anthropic}`
explícito. O modelo default depende do provider resolvido
(`gemini-2.5-flash` / `claude-sonnet-4-6`) — `--model` sobrescreve.
As instruções fixas do prompt (§D da spec) são **byte-idênticas** entre os
dois providers; só o transporte muda.

Flags úteis: `--provider` (`gemini`|`anthropic`), `--model`, `--cota` (válidas
por nível, default 10), `--max-pages` (teto por nível, default 6),
`--cache-dir` (default `resultado/cache`), `--out-dir` (default `resultado`).

### Comportamento
- **Coleta educada:** delay ≥2s entre requisições, sem paralelismo. Cache em disco
  por filme+nível+página e por texto completo — a 2ª execução não toca a rede.
- **Anti-bot:** apenas os headers validados na Fase 0. Se aparecer 403, o programa
  **para e reporta** (não escala para evasão).
- **Nunca pela metade:** reviews truncadas têm o texto completo resolvido via
  `/s/full-text/viewing:<id>/` antes de ir ao LLM; falha → descarte registrado.

## Saída

Gera `resultado/<slug>.json` (buckets + metadados por nível/bucket/globais) e
imprime um resumo no terminal:

```
═══ Espectro 24 — oppenheimer-2023 (spec v1.2.3) ═══

▸ NEGATIVAS  50/50 válidas [0.5★: 10 · 1.0★: 10 · 1.5★: 10 · 2.0★: 10 · 2.5★: 10]  modo=completo
  filtro aplicado (chars): [150]
    • ritmo — mencionado em ~14 de 50 reviews
        ex.: vários reviewers acham o segundo ato arrastado
    • ...
  » síntese do bucket em 1-2 frases

▸ MEDIANAS  20/20 válidas [...]  modo=completo
▸ POSITIVAS 30/30 válidas [...]  modo=completo

Total de reviews observadas na coleta: 312
```

Cada tema traz **frequência relativa** (`~N de M reviews`), nunca absoluta solta.
`n_reviews_analisadas` é **sempre** a contagem real de reviews enviadas ao LLM
naquele bucket — o código é a autoridade desse número (v1.1.1); um valor que o
LLM eventualmente devolva no JSON é ignorado. Se `mencoes_aproximadas` vier
fora de `[0, n_reviews_analisadas]` (sinal de alucinação), o código clampa e
expõe `mencoes_clampadas: true` + `mencoes_valor_original` no JSON — visível
também no terminal com um aviso.
Buckets abaixo do piso de 3 válidas ficam `sem_analise`: renderizam a contagem
e **não** inventam temas. Em vez de imprimir o texto bruto das reviews (risco de
spoiler — a flag do Letterboxd é autodeclarada), apontam para a página de
reviews do filme: `→ N review(s) disponíveis em https://letterboxd.com/film/<slug>/reviews/`
(também no JSON, campo `reviews_url`).

## Testes

```bash
pip install -e ".[llm,test]"   # já inclui pytest + os dois SDKs de LLM
python -m pytest tests/        # roda 100% contra fixtures/, zero rede/zero LLM real
```

## Estrutura

```
pyproject.toml    empacotamento (setuptools, src-layout) + console script "espectro24"
src/espectro24/
  config.py       parâmetros congelados (§2) + headers da Fase 0 + PROVIDER_DEFAULT_MODELS
  fetcher.py      rede + cache em disco + parada anti-bot
  parser.py       seletores atuais (+ fallbacks antigos); detector de spoiler ancorado (v1.1.1)
  collector.py    coleta por nível [B] + cascata de relaxamento [C]
  fulltext.py     completamento de truncadas [C'] — "nunca pela metade"
  synthesize.py   síntese por bucket [D] + narrador [D2] (v1.2.0); adaptadores Anthropic/Gemini
  render.py       JSON + terminal [E] (tons estruturado/narrativo/ambos)
  pipeline.py     orquestração A→B→C→C'→D→E
  cli.py          argparse (--slug, --provider, --model, --tom, --reuse-synthesis, ...)
tests/            unit tests contra fixtures/, zero rede, zero chamada real de LLM
fixtures/         HTMLs reais da Fase 1 (dados de teste)
```
