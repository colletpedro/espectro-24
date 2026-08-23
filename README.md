# Espectro 24

**[espectro-24-eu6z.vercel.app](https://espectro-24-eu6z.vercel.app)**

A nota média mente. Um filme com nota 3,5 pode ser um filme que todo mundo
achou mediano — ou um filme que metade amou e metade odiou. A média não
distingue os dois casos; o Espectro 24 sim.

## O que é

Um agregador de reviews do [Letterboxd](https://letterboxd.com) para quem
**ainda não assistiu** ao filme e quer saber, antes de decidir: o que quem
não gostou disse, o que quem ficou no meio disse, e o que quem gostou disse
— cada grupo com as suas próprias palavras, sem que a média os misture num
número só. Sem spoilers, sem nota, sem "8,5/10 — obra-prima".

## A tese

A média **achata o espectro**. Um filme divisivo e um filme consensualmente
mediano podem ter a mesma nota e são experiências completamente diferentes
para quem vai assistir. O produto mostra a **distribuição** — quanto do
público está em cada faixa — e, dentro de cada faixa, os **temas** que mais
aparecem: o que incomoda quem não gostou, o que convence quem gostou, e se
os grupos concordam sobre do que o filme trata (discordando só no
veredito) ou discordam também sobre o que há para discordar.

## Como funciona, em alto nível

```
coleta por faixa de nota (negativas · medianas · positivas)
        ↓
classificação de cada review numa taxonomia fechada de 10 eixos
(ritmo, atuação, direção e imagem, roteiro, som, tom, impacto emocional,
comparações, expectativa, crítica social) — por votação de 3 passadas
        ↓
bullets por grupo: os de maior frequência (do que esse grupo mais fala)
e os de maior contraste (o que esse grupo fala muito mais que os outros)
        ↓
narrativa em três movimentos: o filme → a experiência que os três grupos
compartilham → onde e como eles discordam
```

Cada número na tela é contagem de código sobre a classificação persistida
— nenhuma frequência é estimada ou lembrada por um LLM. O LLM decide *o
que* dizer sobre um tema (a frase, o parafraseado); o código decide
*quantas* reviews mencionam cada coisa.

## Limitações declaradas

O produto é honesto sobre o que não sabe, de propósito:

- **`impacto_emocional` tem precisão medida de 0,794** contra um gabarito
  humano de 100 reviews (era 0,486 antes de um segundo estágio de
  verificação, que roda depois da classificação e só pode remover marcação
  errada — nunca adicionar). É o único dos 10 eixos com essa fragilidade
  medida; os outros não passaram pelo mesmo escrutínio porque não deram
  sinal de precisar.
- **A margem de contraste (20 pontos percentuais) é uma escolha entre
  pureza e cobertura**, não um número "correto" descoberto. Com ela, 18 dos
  35 filmes do catálogo têm contraste temático de verdade; os outros 17 têm
  os três grupos concordando sobre do que o filme fala e discordando só no
  veredito — e o produto diz isso explicitamente, em vez de forçar um
  contraste que a distribuição real não sustenta.
- **A janela temporal da amostra é um proxy, não uma medida direta de
  recência de opinião.** A data que uma review carrega é quando ela foi
  *escrita*, não necessariamente quando o filme foi assistido, e o material
  mais antigo do catálogo tende a ser sistematicamente mais longo que o
  recente — os dois fatos interagem com qual review a amostra pega.

A [`SPEC.md`](SPEC.md) é a autoridade técnica completa do projeto — toda
decisão, toda medição, todo changelog desde a v1.0.

---

## Para quem quer rodar ou desenvolver

### Instalação

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e ".[llm]"                # empacotado (pyproject.toml, src-layout)

export GEMINI_API_KEY=...              # ou ANTHROPIC_API_KEY / DEEPSEEK_API_KEY
```

Registra o comando `espectro24` no PATH do venv. A chave também pode viver
num `.env` na raiz (carregado automaticamente, não versionado).

### Uso

```bash
espectro24 --slug oppenheimer-2023            # por slug
espectro24 "city of god"                      # por nome (resolve o slug)
espectro24 --slug oppenheimer-2023 --tom ambos  # síntese estruturada + narrativa
espectro24 --slug oppenheimer-2023 --offline    # reexecução 100% cache
```

Sem `--provider`, cada estágio usa o provider configurado para ele
(`PROVIDER_POR_ESTAGIO` em `config.py`) — hoje, classificação e rotulagem
em DeepSeek, narrativa em Gemini. `--provider` força um único provider em
todos os estágios.

Gera `resultado/<slug>.json`. Ver `SPEC.md` §4 para o schema completo.

### Testes

```bash
pip install -e ".[llm,test]"
python -m pytest tests/        # zero rede, zero chamada real de LLM
```

### Publicar o catálogo

```bash
python scripts/verificador_impacto.py aplicar-producao   # verificador sobre o consenso
python scripts/publicar_catalogo.py                       # pipeline completo, checkpoint/resume
python frontend/build_data.py                              # embute os JSONs no frontend
```

### Estrutura

```
pyproject.toml    empacotamento (setuptools, src-layout) + console script "espectro24"
src/espectro24/
  config.py         parâmetros congelados + provider por estágio
  fetcher.py        rede + cache em disco + parada anti-bot
  collector.py       coleta por nível + cascata de relaxamento
  selecao.py          seleção 40/40/40 estratificada por profundidade
  synthesize.py       síntese por bucket + adaptador ÚNICO de LLM (guard-rail no CI)
  narrador.py          narrativa em 3 movimentos, best-of-3
  eixos.py             frequência, lift, margem, contraste — tudo Fraction, zero LLM
  pipeline.py           orquestração coleta → seleção → síntese → eixos → narrativa
  cli.py                 argparse (espectro24 --slug ...)
scripts/           harnesses de classificação, verificação, votação, publicação e auditoria
frontend/          site estático (HTML/CSS/JS puro, sem build step, dados embutidos)
tests/             ~1100 testes contra fixtures/, zero rede, zero LLM real
```
