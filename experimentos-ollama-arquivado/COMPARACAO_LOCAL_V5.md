# Espectro 24 — Experimento 5: refinamento do pipeline de dois estágios + validação em 2 filmes

Gerado a partir de `scripts/comparar_sintese_local_v5.py`. **Chamadas Gemini: 0. Requisições Letterboxd: 0. Requisições TMDB: 0.** Reviews 100% do cache (`Fetcher(offline=True)`, `n_network=0` confirmado por filme). think=false em todas as chamadas.

**Sessão de EXPERIMENTO, não bump de versão.** `SPEC.md` e `build_system_prompt` (produção) não foram tocados. `resultado/*.json` de produção e os resultados dos experimentos 1-4 não foram tocados.

> **Nenhum veredito de qualidade literária é emitido aqui.** Números e textos; avaliação semântica é humana.

## O que mudou desde o experimento 4

| Tarefa | Mudança |
|---|---|
| 1 — nomenclatura | Prompt do estágio 1 ganhou regra explícita (2-6 palavras, português natural) + 3 exemplos bons + 3 ruins (usando os nomes malformados reais do exp.4: "Ritmo e Pacingo Abstrato", "Ambiente Opressivo Somente Visual e Sonoro", "Estética do Banal Sobrenatural") |
| 2 — anti-spoiler | Reforço explícito: descrever o EFEITO no espectador, nunca o MECANISMO da trama; exemplo negativo real do exp.4 incluído no prompt |
| 3 — sub-classificação | Estágio 2 passou a pedir correspondência SEMÂNTICA (não literal); "não marcar" virou exceção explícita, não resposta padrão |
| 4 — custo de tempo | Lotes de 25 reviews (era 10) |
| 5 — validação | Rodado em `cure` E `cidade-de-deus` |

## Execução — resumo

| Filme | Bucket | Reviews | Lotes (tam. 25) | Estágio 1 | Estágio 2 | Total |
|---|---|---|---|---|---|---|
| `cure` | negativas | 50 | 2 | 116,1s | 144,2s | 260,3s |
| `cure` | medianas | 20 | 1 | 125,1s | 120,3s | 245,5s |
| `cure` | positivas | 30 | 2 | 134,1s | 161,3s | 295,4s |
| `cidade-de-deus` | negativas | 50 | 2 | 266,6s | 285,7s | 552,3s |
| `cidade-de-deus` | medianas | 20 | 1 | 99,5s | 73,4s | 172,9s |
| `cidade-de-deus` | positivas | 30 | 2 | 103,7s | 106,1s | 209,8s |

**Todas as chamadas (3+5 estágio-2 lotes por filme = 8 chamadas/filme, 16 no total) produziram JSON válido na primeira tentativa** — 0 retentativas, 0 lotes com falha em nenhum dos 2 filmes.

---

## Tarefa 4 — o lote maior NÃO reduziu o tempo total

**Hipótese testada:** prefill é barato (~1s/14k tokens), saída do estágio 2 é minúscula, então lotes maiores deveriam custar quase o mesmo por chamada — reduzindo o total pelo menor número de chamadas.

**Resultado: a hipótese não se sustentou.** Comparando `cure` diretamente contra o experimento 4 (mesmo filme, mesmos prompts-base, só o tamanho do lote muda):

| | Exp.4 (lote=10) | Exp.5 (lote=25) |
|---|---|---|
| Chamadas de estágio 2 (`cure`, total) | 10 (5+2+3) | 5 (2+1+2) |
| Tempo de estágio 2 (`cure`, total) | 172,0+114,9+137,7 = 424,6s | 144,2+120,3+161,3 = 425,8s |
| Tempo TOTAL (`cure`, 3 buckets) | **806,1s ≈ 13,43 min** | **801,2s ≈ 13,35 min** |

O tempo total ficou **essencialmente IDÊNTICO** (diferença de 0,6%) apesar de reduzir de 10 para 5 chamadas de estágio 2. Olhando por chamada: em `negativas`, o exp.4 fazia 5 lotes de 10 a ~34,4s/lote; o exp.5 faz 2 lotes de 25 a ~72,1s/lote — o tempo por chamada **mais que dobrou** quando o lote 2,5x maior, quase proporcionalmente ao tamanho do lote, não ficou fixo como a hipótese previa. Ou seja: o custo NÃO é dominado por um overhead fixo por chamada — cresce com o tamanho da entrada+saída de forma aproximadamente linear, cancelando o ganho de ter menos chamadas.

---

## Bucket `negativas` — `cure` (50 reviews)

| | Gabarito | Exp.4 (lote=10) | Exp.5 (lote=25) |
|---|---|---|---|
| **Temas (frequência)** | Ritmo lento e tedioso (35); Falta de tensão/mistério/terror (25); Enredo e roteiro fracos/repetitivos (18); Personagens desinteressantes/planos (15); Filme superestimado/pretensioso (12); Final insatisfatório/abrupto (8) | Ausência de Tensão Atmosférica (26); Ritmo e Pacingo Abstrato (20); Caracterização Plana e Falta de Ganchos Emocionais (18); Conceito Central Tratado Superficialmente (18); Roteiro Confuso e Falta de Progressão Dramática (13); Atuações Indiferentes ou Inautênticas (9) | Ritmo excessivamente lento e estático (23); Narrativa sem evolução dramática (22); Diálogos artificiais e repetitivos (18); Personagens planos e sem profundidade emocional (15); Conceito de hipnose questionado logicamente (15); Atmosfera clínica fria demais (14) |
| **Razão soma/n_reviews** | 2,26 | 2,08 | **2,14** |
| **Maior menção / fração** | 35/50 (70%) | 26/50 (52%) | **23/50 (46%)** |
| **Reviews sem tema** | — | 11/50 (22%) | **13/50 (26%)** |
| **Média temas/review classificada** | — | 2,08 | 2,14 |
| **Ids inválidos (estágio 2)** | — | 0 | **2** |
| **Nomes malformados** | — | — | 0/6 |

## Bucket `medianas` — `cure` (20 reviews)

| | Gabarito | Exp.4 | Exp.5 |
|---|---|---|---|
| **Temas (frequência)** | Ritmo lento e confusão narrativa (10); Final insatisfatório/ambíguo (8); Ideias intrigantes, mas execução falha (7); Atmosfera e estilo visual eficazes (6); Necessidade de revisitação (6) | Ritmo lento e deliberado (10); Atmosfera densa e minimalista visual (7); Elipses narrativas e ambiguidade resolvente (6); Nihilismo ético e moralidade ambígua (5); Dissolução da identidade individual (1) | Ritmo lento e hipnótico (9); Mistério elíptico abstrato (9); Ambiente opressivo vazio (8); Resolução confusa narrativa (8); Desconexão emocional distante (8); Vilania intangível interior (5) |
| **Razão soma/n_reviews** | 1,85 | 1,45 | **2,35** |
| **Maior menção / fração** | 10/20 (50%) | 10/20 (50%) | **9/20 (45%)** |
| **Reviews sem tema** | — | 5/20 (25%) | **4/20 (20%)** |
| **Média temas/review classificada** | — | 1,45 | 2,35 |
| **Ids inválidos** | — | 0 | 0 |
| **Nomes malformados** | — | — | 0/6 |

## Bucket `positivas` — `cure` (30 reviews)

| | Gabarito | Exp.4 | Exp.5 |
|---|---|---|---|
| **Temas (frequência)** | Atmosfera e Tom Perturbador/Hipnótico (15); Pacing Lento e Deliberado (10); Temas Psicológicos e Existenciais (9); Atuação do Antagonista (6); Design de Som e Cinematografia (6); Ausência de Respostas e Ambiguidade (5) | Ambiente Opressivo Somente Visual e Sonoro (11); Psicologia da Identidade e Vazio Interior (8); Manipulação Mental e Hipnotismo (8); Estética do Banal Sobrenatural (7); Edição Elíptica para Desorientação (5); Atuação Contida e Monótona (4) | Estilo visual minimalista e clínico (15); Atmosfera opressiva e onírica (13); Vazio interior dos personagens (10); Som ambiente perturbador (7); Violência mecânica e banal (4) |
| **Razão soma/n_reviews** | 1,70 | 1,433 | **1,633** |
| **Maior menção / fração** | 15/30 (50%) | 11/30 (36,7%) | **15/30 (50%)** |
| **Reviews sem tema** | — | 7/30 (23,3%) | **10/30 (33,3%)** |
| **Média temas/review classificada** | — | 1,433 | 1,633 |
| **Ids inválidos** | — | 0 | **3** |
| **Nomes malformados** | — | — | 0/5 |

**`cure` — resumo:** razão bateu o gabarito quase exatamente em `positivas` (1,633 vs 1,70) e `negativas` (2,14 vs 2,26); `medianas` passou do gabarito para cima (2,35 vs 1,85) — nenhum bucket voltou ao nível de inflação extrema das rodadas 1-3 (84-96% de maior fração). **A taxa de reviews sem tema NÃO caiu de forma consistente** apesar do reforço de correspondência semântica: subiu em `negativas` (22%→26%) e `positivas` (23,3%→33,3%), caiu só em `medianas` (25%→20%) — resultado misto, não a melhoria uniforme esperada da Tarefa 3.

---

## Bucket `negativas` — `cidade-de-deus` (50 reviews) — só gabarito (exp.4 não rodou este filme)

| | Gabarito | Exp.5 |
|---|---|---|
| **Temas (frequência)** | Estetização e espetacularização da violência/miséria (25); Representação estereotipada e deturpada da favela (18); Violência excessiva e gratuita (15); Falta de autenticidade/Crítica à perspectiva dos diretores (10); Personagens pouco desenvolvidos (8); Roteiro confuso/repetitivo (7) | Violência como espetáculo frenético (27); Falta de agência dos moradores reais (26); Estética do colonialismo favela-ficção (20); Personagens como arquétipos vazios (19); Voz em off que distancia do humano (12) |
| **Razão soma/n_reviews** | 1,66 | **2,08** |
| **Maior menção / fração** | 25/50 (50%) | **27/50 (54%)** |
| **Reviews sem tema** | — | 15/50 (30%) |
| **Ids inválidos** | — | 0 |
| **Nomes malformados** | — | **1/5 — "Estética do colonialismo favela-ficção"** (construção academicista/neologismo hifenizado, não claramente uma palavra inventada mas foge do "como um crítico escreveria") |

## Bucket `medianas` — `cidade-de-deus` (20 reviews)

| | Gabarito | Exp.5 |
|---|---|---|
| **Temas (frequência)** | Retrato da violência e realidade social (11); Qualidade técnica e estilística (9); Entretenimento vs. profundidade/conexão emocional (7); Ritmo e engajamento (4); Caracterização dos personagens (3) | Ritmo frenético e cinematográfico (8); Violência crua e hipnótica (6); Falta de conexão com os personagens (5); Narrativa fragmentada e esquemática (4); Trilha sonora pop desconectada (3); Estilização artificial e excessiva (2) |
| **Razão soma/n_reviews** | 1,70 | **1,40** |
| **Maior menção / fração** | 11/20 (55%) | **8/20 (40%)** |
| **Reviews sem tema** | — | 4/20 (20%) |
| **Ids inválidos** | — | 0 |
| **Nomes malformados** | — | 0/6 |

## Bucket `positivas` — `cidade-de-deus` (30 reviews)

| | Gabarito | Exp.5 |
|---|---|---|
| **Temas (frequência)** | Estilo visual e edição dinâmicos (21); Narrativa envolvente e abrangente (15); Brutalidade e realismo da violência (14); Atuações marcantes (10); Contexto social e histórico (9); Mistura de gêneros (3) | Depictão despojado das favelas (16); Edição frenética e ritmo acelerado (11); Enorme número de personagens complexos (11); Atuações cruas sem filtro artístico (10); Paleta de cores vibrante marcadora da época (6) |
| **Razão soma/n_reviews** | 2,4 | **1,80** |
| **Maior menção / fração** | 21/30 (70%) | **16/30 (53,3%)** |
| **Reviews sem tema** | — | 5/30 (16,7%) |
| **Ids inválidos** | — | 0 |
| **Nomes malformados** | — | **1/5 — "Depictão despojado das favelas"** ("Depictão" NÃO é palavra em português — mistura do inglês "depiction" com sufixo "-ção") |

**`cidade-de-deus` — resumo (validação no 2º filme):** o padrão de razão moderada se repete (1,40-2,08, nunca os 3,x+ das rodadas antigas) e a maior fração fica entre 40-54% — mesma faixa observada em `cure`. **2 dos 16 nomes de tema** deste filme violam a regra de nomenclatura (12,5%) — pior que `cure` (0/17), indicando que o reforço do prompt reduziu mas não eliminou o defeito.

---

## Tarefa 2 — checagem anti-spoiler nas descrições (transcrição das violações)

| Filme/bucket | Descrição (tema) | O que expõe | Equivalente no gabarito |
|---|---|---|---|
| `cidade-de-deus`/negativas | *"Transforma **mortes de crianças** e atrocidades em ritmo acelerado, criando excitação visual ao invés de reflexão ou pesar."* (Violência como espetáculo frenético) | Nomeia conteúdo específico ("mortes de crianças") em vez de só o efeito | Gabarito: "Estetização e espetacularização da violência/miséria" — sem nomear vítimas |
| `cidade-de-deus`/medianas | *"a brutalidade dos **assassinatos** atordoa o espectador com a falta de senso comum em meio à pobreza extrema"* (Violência crua e hipnótica) | Nomeia "assassinatos" como conteúdo, mais brando que o exemplo acima | Gabarito: "Retrato da violência e realidade social" — mais abstrato |
| `cure`/negativas | *"premissa que soa simplória ou pseudo-científica"* (Conceito de hipnose questionado logicamente) | Rotula o CONCEITO da trama (hipnose) por nome, mas não explica o mecanismo | Gabarito: "Filme superestimado/pretensioso" — não nomeia o conceito |

Comparado ao experimento 4 (onde 2 descrições explicavam abertamente COMO o mecanismo da trama funciona — "a perda de memória... permitem que forças ocultas assumam controle"), o experimento 5 não repetiu esse padrão de explicação mecanicista; o que sobrou é nomear CONTEÚDO/conceito específico (mortes, assassinatos, hipnose) em vez de só o efeito — uma violação mais branda, mas ainda presente. Reportado para julgamento humano.

---

## Amostra para conferência humana

### `cure` / bucket `medianas` (mapa: t1=Ritmo lento e hipnótico, t2=Ambiente opressivo vazio, t3=Resolução confusa narrativa, t4=Desconexão emocional distante, t5=Vilania intangível interior, t6=Mistério elíptico abstrato)

**Índice 0 (3,0★) — atribuída a t2, t3, t4, t5, t6 (5 temas, o máximo observado):**
> 55/100 Second viewing, last seen 20 years ago. [...] Unlike everybody else on Earth, it seems, I didn't think this movie was all that hot. Kurosawa's films call to mind the trajectory of Twin Peaks, except with the slow slide from eerily gripping premise to irritatingly "enigmatic" conclusion compressed into a mere two hours. [...] Not only does the narrative prove unsatisfying in each case, but thematically the films are so vague that it's possible to read pretty much anything you want into them. [...] There's something being said here, however, about "the evil that lurks within men's souls" [...] Given that the film has no satisfying narrative conclusion (which even its champions must admit), it had better damn well boast a fascinating subtext. [...] *(review muito longa — trecho representativo; discute extensamente vaguidão temática, falta de resolução, e o "mal" abstrato do filme)*

*Leitura para conferência:* review longa e multifacetada — de fato toca em resolução insatisfatória (t3), vaguidão temática/mal abstrato (t5, t6), e alguma desconexão emocional pelo tom sarcástico (t4). 5 temas simultâneos é o valor mais alto observado; a review é excepcionalmente longa e cobre muito terreno, então pode ser defensável, mas é o caso mais "generoso" da amostra e vale atenção humana.

**Índice 1 (3,0★) — SEM tema atribuído:**
> This is my second Kyoshi Kurosawa film after last week's Sweet Home. Cure is a gritty cat and mouse psychological thriller [...] Cure, on the other hand, goes for the subdued approach, and while I certainly felt plenty of suspense amidst the lackadaisical yet gripping conversations, I feel a huge suppression of actual horror. [...] The process of the antagonist's questioning comes across vastly superior in the reasoning behind the plot points, but the writing doesn't take the ideas far enough. [...] It just didn't hit the high notes as well as it could have, particularly with the writing. The directorial skill is there but not tuned or well adjusted to the themes at hand.

*Leitura para conferência:* mesma review do experimento 4 (mesmo bucket, mesmo índice) — CONTINUA sem tema mesmo com a instrução de correspondência semântica mais frouxa. "subdued approach" e "huge suppression of actual horror" tocam em tom/atmosfera sem usar as palavras dos temas listados; permanece um caso limítrofe para julgamento humano — a mudança de prompt não foi suficiente para capturá-la.

**Índice 2 (3,0★) — atribuída a t1 (Ritmo lento e hipnótico):**
> It frustrates me because I feel like I didn't connect with this film in the same way most people seem to have. [...] I found it somewhat slow and even boring for most of its runtime. [...] there remains an intangible barrier preventing me from fully surrendering to its atmosphere and emotional rhythm.

*Leitura para conferência:* "slow and even boring" bate diretamente com t1 — classificação parece precisa.

**Índice 3 (3,0★) — atribuída a t1, t3, t6:**
> [...] Kiyoshi Kurosawa is better at creating mysteries than he's at resolving them [...] which drew me in with it's Se7en-esque atmosphere and detective vs. enigmatic antagonist dynamics, without ever giving me the same satisfying resolution. Why the things happen that happen in act three beats me. [...] It's well-made, but Cure eludes me too much to love it. *(seguido de uma lista de desafio pessoal de watchlist, sem relação com o filme)*

*Leitura para conferência:* "better at creating mysteries than resolving them" e "without... satisfying resolution" batem com t3 (resolução confusa) e t6 (mistério elíptico); t1 (ritmo) não é mencionado diretamente — possível falso positivo a checar.

**Índice 5 (3,0★) — atribuída a t3, t4, t6:**
> [...] Cure is at its best when our amnesiac pushes that question into his prey's faces [...] I get Mayima as an unstable young loner who takes his field of study much too far [...] But how to explain the detective apparently taking over the mantle of hypno-murder-inciter? Why on Earth would he do that, I asked myself. I didn't have an answer. [...] we're left to toss a coin about whether those are real or imagined [...] a shortcut to explain what you want explained.

*Leitura para conferência:* "I didn't have an answer" e "toss a coin about whether... real or imagined" batem bem com t3 (resolução confusa) e t6 (mistério elíptico); t4 (desconexão emocional) é menos óbvio nesta review, que é mais sobre confusão de trama do que distância emocional — outro possível falso positivo.

### `cidade-de-deus` / bucket `medianas` (mapa: t1=Violência crua e hipnótica, t2=Ritmo frenético e cinematográfico, t3=Falta de conexão com os personagens, t4=Estilização artificial e excessiva, t5=Trilha sonora pop desconectada, t6=Narrativa fragmentada e esquemática)

**Índice 0 (3,0★, em árabe) — atribuída a t3, t2:**
> [árabe] *"Achei que seria como La Haine, e depois de algumas cenas confirmei — o ritmo alto que tem é incrível... mas literalmente o filme é entediante ao extremo, não vou exagerar se disser que nenhuma cena do filme me agradou ou me marcou, não me afetei com nada durante o filme todo... o melhor nele é que é realista em tudo, especialmente a atuação, mas o clima de tumulto, tiros e as muitas armas não combinaram comigo de jeito nenhum."* (tradução aproximada, não gerada pelo modelo)

*Leitura para conferência:* "ritmo alto... incrível" bate com t2; "nenhuma cena me agradou/marcou" e "não me afetei com nada" batem com t3 (falta de conexão) — classificação em língua não-inglesa/não-portuguesa funcionou, sinal de que a classificação semântica atravessa idioma.

**Índice 1 (3,0★, em árabe) — SEM tema atribuído:**
> [árabe] *"O filme é sincero e realista de um jeito que te faz sentir que está vivendo entre eles a pobreza, o medo e a perdição que não poupa ninguém... apesar do filme ser bom na narrativa, a quantidade de palavrões foi incômoda mesmo que o objetivo fosse retratar a realidade, e senti que o filme era mais documentário do que cinematográfico e qualquer filme com armas e tiros não me agrada."* (tradução aproximada)

*Leitura para conferência:* fala de realismo/pobreza (fora dos 6 temas listados, que são sobre ritmo/violência/personagens/estilização/trilha/narrativa) e linguagem chula — não bate claramente com nenhum tema listado; ausência parece defensável.

**Índice 2 — atribuída a t2 (Ritmo frenético e cinematográfico):**
> Hoods don't love, they desire. Hoods don't talk, they smooth-talk. Hoods don't stop, they take a break. Hi-octane. Hyper-kinetic. Adrenaline. Top 500 Narrative Features: #127

*Leitura para conferência:* "Hi-octane. Hyper-kinetic. Adrenaline." bate diretamente com t2 — classificação precisa apesar do texto ser extremamente curto e estilizado.

**Índice 3 — atribuída a t6 (Narrativa fragmentada e esquemática):**
> Why remain in the City of God when God has forgotten you? [...] In the City of God — that was the name of the housing project the brazilian government created in the 60's — were we meet all these characters and their evolution over the decades. The violence in this slum is brutal. [...] The editing of this movie was superb and the fantastic movements of the handheld camera added a lot to the suspense and tension [...]

*Leitura para conferência:* a review elogia a edição e a tensão, não critica fragmentação narrativa de forma clara — t6 parece um possível falso positivo (a review é mais sobre "personagens e evolução ao longo de décadas" do que sobre a narrativa ser confusa/esquemática).

**Índice 5 (em turco) — SEM tema atribuído:**
> [turco] *"Segue de forma adequada ao seu tema, mas mesmo sabendo que não tenho prazer nenhum assistindo esse tipo de filme, quis assistir por ser um filme popular. Por isso, para mim foi um filme mediano."* (tradução aproximada)

*Leitura para conferência:* review muito curta e genérica ("filme mediano", sem crítica específica a nenhum dos 6 temas) — ausência de tema é claramente correta aqui.

---

## Tabela-resumo final

| Filme/bucket | Gabarito (razão/maior%) | Exp.4 (razão/maior%) | **Exp.5 (razão/maior%)** | Nomes malformados |
|---|---|---|---|---|
| `cure`/negativas | 2,26 / 70% | 2,08 / 52% | **2,14 / 46%** | 0/6 |
| `cure`/medianas | 1,85 / 50% | 1,45 / 50% | **2,35 / 45%** | 0/6 |
| `cure`/positivas | 1,70 / 50% | 1,433 / 36,7% | **1,633 / 50%** | 0/5 |
| `cidade-de-deus`/negativas | 1,66 / 50% | — | **2,08 / 54%** | 1/5 |
| `cidade-de-deus`/medianas | 1,70 / 55% | — | **1,40 / 40%** | 0/6 |
| `cidade-de-deus`/positivas | 2,4 / 70% | — | **1,80 / 53,3%** | 1/5 |

**Validação em 2 filmes confirma o padrão central do experimento 4:** em nenhum dos 6 buckets (2 filmes × 3 buckets) a razão passou de 2,35 nem a maior fração passou de 54% — bem distante dos 84-96% das rodadas 1-3. O padrão se sustenta fora da amostra original.

**Nomenclatura:** 2 de 33 nomes de tema (6%) ainda violam a regra, ambos em `cidade-de-deus` — o reforço do prompt reduziu drasticamente a frequência (de quase todo bucket ter um nome malformado no exp.4 para 2 casos isolados), mas não eliminou o defeito.

**Sub-classificação:** a taxa de reviews sem tema não melhorou de forma consistente (subiu em 2 buckets de `cure`, caiu em 1) — a instrução de correspondência semântica não produziu o efeito uniforme esperado.

## Tempo e extrapolação final

| | `cure` | `cidade-de-deus` | Média |
|---|---|---|---|
| Tempo total (3 buckets) | 801,2s ≈ 13,35 min | 935,0s ≈ 15,58 min | **14,47 min/filme** |

| Filmes | Minutos de LLM local | Horas |
|---|---|---|
| 1 | ~14,5 min | 0,24h |
| 50 | ~723,4 min | **~12,06h** |
| 300 | ~4.340,5 min | **~72,34h** |

O lote maior (25) não reduziu o tempo por filme em relação ao experimento 4 (13,4 min) — ficou estatisticamente no mesmo patamar (13,35-15,58 min, com a variação entre filmes maior que o efeito do tamanho do lote).
