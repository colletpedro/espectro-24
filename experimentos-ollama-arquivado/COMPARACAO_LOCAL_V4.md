# Espectro 24 — Experimento 4: síntese local em dois estágios (contagem em código)

Gerado a partir de `scripts/comparar_sintese_local_v4.py`. **Chamadas Gemini: 0. Requisições Letterboxd: 0. Requisições TMDB: 0.** Reviews 100% do cache (`Fetcher(offline=True)`, `n_network=0` confirmado antes de qualquer chamada). think=false em todas as 13 chamadas do experimento.

**Sessão de EXPERIMENTO, não bump de versão.** `SPEC.md` e `build_system_prompt` (produção) não foram tocados — os prompts dos dois estágios são NOVOS, escritos só neste script, preservando as mesmas invariantes de papel/anti-spoiler/pt-BR/sem-aspas do prompt de produção. `resultado/cure.json` e os resultados dos experimentos 1, 2 e 3 não foram tocados.

> **Nenhum veredito de qualidade literária é emitido aqui.** Números e textos; avaliação semântica é humana.

## Diagnóstico que motivou o experimento

Nas três rodadas locais anteriores, a razão soma_de_menções/n_reviews oscilou entre 2,03 e 3,50 sem relação com o tamanho do bucket, e o tema mais citado ficou sempre entre 84% e 93% do bucket, independentemente de haver 20, 30 ou 50 reviews. **Hipótese:** o modelo é bom em identificar temas e ruim em contar ocorrências — separar as duas tarefas e deixar a contagem para o código deveria produzir frequência exata.

## Desenho do experimento

- **Estágio 1** (1 chamada/bucket): identifica de 4 a 6 temas, SEM pedir nenhum número — schema `{id, tema, descricao_curta}`.
- **Estágio 2** (1 chamada/lote de 10 reviews): recebe os temas do estágio 1 e as reviews numeradas; para cada review, decide quais ids de tema ela aborda (nenhum, um, ou vários). Schema `{"1": [ids], "2": [ids], ...}`.
- **O código** soma as ocorrências de cada id e produz `mencoes_aproximadas` — o LLM nunca vê nem escreve esse número.
- Ids inexistentes na resposta do estágio 2 são descartados e contados (`ids_invalidos`).

## Execução — resumo

| Bucket | Estágio 1 | Estágio 2 | Total | Lotes | Falhas |
|---|---|---|---|---|---|
| `negativas` (50) | 119,5s | 172,0s | **291,5s** | 5 | 0 |
| `medianas` (20) | 123,7s | 114,9s | **238,6s** | 2 | 0 |
| `positivas` (30) | 138,3s | 137,7s | **276,0s** | 3 | 0 |

**Todas as 13 chamadas (3 de estágio 1 + 10 lotes de estágio 2) produziram JSON válido na primeira tentativa** — 0 retentativas, 0 lotes com falha, **0 ids inválidos** devolvidos em qualquer lote, em nenhum bucket.

---

## Bucket `negativas` (50 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Exp.4 dois estágios |
|---|---|---|---|
| **Temas (ordem de frequência)** | Ritmo lento e tedioso (35); Falta de tensão/mistério/terror (25); Enredo e roteiro fracos/repetitivos (18); Personagens desinteressantes/planos (15); Filme superestimado/pretensioso (12); Final insatisfatório/abrupto (8) | Ritmo excessivamente lento e estagnação da narrativa (48); Personagens desprovidos de profundidade e interesse (35); Narrativa previsível sem tensão dramática (32); Atmosfera clínica e excessivamente limpa (18); Tratamento superficial de hipnose/psicologia (15); Atores impessoais/robóticos (12) | Ausência de Tensão Atmosférica (26); Ritmo e Pacingo Abstrato (20); Caracterização Plana e Falta de Ganchos Emocionais (18); Conceito Central Tratado Superficialmente (18); Roteiro Confuso e Falta de Progressão Dramática (13); Atuações Indiferentes ou Inautênticas (9) |
| **N° de temas** | 6 | 6 | 6 |
| **SOMA das menções** | 113 | 160 | **104** |
| **Razão soma/n_reviews** | **2,26** | **3,20** | **2,08** |
| **Maior menção individual** | 35/50 (70%) | 48/50 (96%) | **26/50 (52%)** |
| **Reviews sem nenhum tema** | — | — | 11/50 (22%) |
| **Média de temas por review classificada** | — | — | 2,08 |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 (6 chamadas: 1 estágio1 + 5 lotes) |
| **Ids inválidos (estágio 2)** | — | — | 0 |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas nas descrições |

Pela primeira vez nas quatro rodadas, a razão fica ABAIXO do gabarito (2,08 vs. 2,26), e o tema mais frequente cai para 52% do bucket — bem longe dos 70-96% observados até aqui.

---

## Bucket `medianas` (20 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Exp.4 dois estágios |
|---|---|---|---|
| **Temas (ordem de frequência)** | Ritmo lento e confusão narrativa (10); Final insatisfatório/ambíguo (8); Ideias intrigantes, mas execução falha (7); Atmosfera e estilo visual eficazes (6); Necessidade de revisitação para compreensão (6) | Atmosfera lenta e ambígua que divide a audiência (12); Problemas na resolução dos mistérios (9); Conceitos abstratos de identidade e mal (8); Distância emocional espectador-personagens (6); Confusão narrativa sobre motivações (5); Realismo perturbador vs. sobrenatural (4) | Ritmo lento e deliberado (10); Atmosfera densa e minimalista visual (7); Elipses narrativas e ambiguidade resolvente (6); Nihilismo ético e moralidade ambígua (5); Dissolução da identidade individual (1) |
| **N° de temas** | 5 | 6 | 5 |
| **SOMA das menções** | 37 | 44 | **29** |
| **Razão soma/n_reviews** | **1,85** | **2,20** | **1,45** |
| **Maior menção individual** | 10/20 (50%) | 12/20 (60%) | **10/20 (50%)** |
| **Reviews sem nenhum tema** | — | — | 5/20 (25%) |
| **Média de temas por review classificada** | — | — | 1,45 |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 (3 chamadas: 1 estágio1 + 2 lotes) |
| **Ids inválidos (estágio 2)** | — | — | 0 |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas nas descrições |

O maior tema (`Ritmo lento e deliberado`, 10/20 = 50%) empata exatamente com o gabarito em fração relativa. A razão fica abaixo do gabarito desta vez (1,45 vs. 1,85) — ao contrário da variante A do experimento 3, que tinha inflado este mesmo bucket para 3,50.

**Checagem anti-spoiler nas descrições do estágio 1:** o tema `t1` ("Elipses narrativas e ambiguidade resolvente") tem a descrição *"a narrativa avança com lacunas intencionais, onde o enigma só se desfaz de forma insatisfatória no final"* — referencia a resolução do enigma de forma um pouco mais específica que o gabarito equivalente ("Final insatisfatório/ambíguo"), mas sem citar mecânica de trama, nome de personagem ou evento concreto. Não encontrei o padrão "personagem amnésico"/"transição entre outras vítimas" do experimento 1 reaparecendo aqui.

---

## Bucket `positivas` (30 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Exp.4 dois estágios |
|---|---|---|---|
| **Temas (ordem de frequência)** | Atmosfera e Tom Perturbador/Hipnótico (15); Pacing Lento e Deliberado (10); Temas Psicológicos e Existenciais (9); Atuação do Antagonista (6); Design de Som e Cinematografia (6); Ausência de Respostas e Ambiguidade (5) | Atmosfera de opressão e paranoia (15); Atuação contida dos atores (12); Estética visual minimalista (10); Tema da identidade perdida (9); Psicologia do mal oculto (8); Tratamento lento e deliberado (7) | Ambiente Opressivo Somente Visual e Sonoro (11); Psicologia da Identidade e Vazio Interior (8); Manipulação Mental e Hipnotismo (8); Estética do Banal Sobrenatural (7); Edição Elíptica para Desorientação (5); Atuação Contida e Monótona (4) |
| **N° de temas** | 6 | 6 | 6 |
| **SOMA das menções** | 51 | 61 | **43** |
| **Razão soma/n_reviews** | **1,70** | **2,03** | **1,433** |
| **Maior menção individual** | 15/30 (50%) | 15/30 (50%) | **11/30 (36,7%)** |
| **Reviews sem nenhum tema** | — | — | 7/30 (23,3%) |
| **Média de temas por review classificada** | — | — | 1,433 |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 (4 chamadas: 1 estágio1 + 3 lotes) |
| **Ids inválidos (estágio 2)** | — | — | 0 |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas nas descrições |

Menor razão e menor fração de maior tema entre as quatro colunas neste bucket.

**Checagem anti-spoiler nas descrições do estágio 1:** dois temas nomeiam a mecânica central do filme de forma mais explícita que o gabarito — `t1` ("Psicologia da Identidade e Vazio Interior") descreve *"a perda de memória e o vazio interior das vítimas permitem que forças ocultas assumam controle"*, e `t3` ("Manipulação Mental e Hipnotismo") descreve *"a capacidade de influenciar mentes através da sugestão"*. O gabarito usa "hipnótico" como adjetivo de tom/atmosfera; aqui "hipnotismo" e "perda de memória" aparecem como descrição do MECANISMO da trama (o filme trata de um hipnotizador que induz amnésia/violência). Não há nome de personagem nem evento de desfecho, mas é uma exposição de mecânica mais direta que as outras três colunas — sinalizado para revisão humana.

---

## Amostra para conferência humana — bucket `medianas`

Três reviews completas do bucket `medianas`, com os temas que o estágio 2 atribuiu a cada uma (mapa de ids: `t1`=Elipses narrativas e ambiguidade resolvente, `t2`=Atmosfera densa e minimalista visual, `t3`=Dissolução da identidade individual, `t4`=Nihilismo ético e moralidade ambígua, `t5`=Ritmo lento e deliberado).

### Review índice 0 (nota 3,0★) — atribuída a `t5` (Ritmo lento e deliberado) + `t4` (Nihilismo ético e moralidade ambígua)

> 55/100 Second viewing, last seen 20 years ago. That happened to be two months before Pulse scared the living shit out of me at TIFF '01, so my Time Out New York review—fully half of which just complains that Kurosawa's reputation had somehow gotten out ahead of his demonstrable talent—has gained an ironic aftertaste. [...] Unlike everybody else on Earth, it seems, I didn't think this movie was all that hot. Kurosawa's films call to mind the trajectory of Twin Peaks, except with the slow slide from eerily gripping premise to irritatingly "enigmatic" conclusion compressed into a mere two hours. License to Live, Seance, Cure—they all go nowhere, as far as I can tell. Not only does the narrative prove unsatisfying in each case, but thematically the films are so vague that it's possible to read pretty much anything you want into them. [...] There's something being said here, however, about "the evil that lurks within men's souls" This is precisely what I mean when I complain that the movie is ridiculously vague. Any film featuring motiveless killings will automatically be perceived as saying something about the evil that lurks within men's souls. [...] Almost entirely devoid of music and chillingly detached in its presentation of violence, Cure follows a police detective (Kurosawa regular Kōji Yakusho) as he hunts down an amnesiac serial killer (Masato Hagiwara) who hypnotizes others into committing murder, usually with the aid of a cigarette lighter. [...] Kurosawa fails to make any kind of cogent statement about the nature of apparently motiveless crimes or the inherent unknowability of the human heart. *(review completa e bem mais longa no cache — trecho representativo acima; a review integral discute extensamente o roteiro compartilhado da crítica original do usuário no Time Out New York)*

**Leitura para conferência:** a review de fato passa boa parte do texto questionando o "mal sem motivo" e a vagueza temática do filme (`t4` parece razoável) e reclama do ritmo/estrutura ("the slow slide", filmes que "go nowhere") — `t5` também parece defensável. Nenhum tema espúrio óbvio.

### Review índice 2 (nota 3,0★) — atribuída só a `t5` (Ritmo lento e deliberado)

> It frustrates me because I feel like I didn't connect with this film in the same way most people seem to have. I've read so many glowing reviews praising it, and yet I have to admit that I found it somewhat slow and even boring for most of its runtime. The premise is incredibly interesting, and after reading more online about the story and the ending, I can absolutely see and understand what the film is trying to convey. Still, there remains an intangible barrier preventing me from fully surrendering to its atmosphere and emotional rhythm.… maybe I should revisit it in a few months and see if it resonates differently. As of now, however, it has left me feeling strangely indifferent.

**Leitura para conferência:** review curta, cujo conteúdo central é "achei lento e entediante" ("slow and even boring") — `t5` bate exatamente. Não menciona nihilismo, identidade, ou atmosfera visual especificamente — classificação parece precisa e conservadora (não forçou outros temas).

### Review índice 1 (nota 3,0★) — sem nenhum tema atribuído

> This is my second Kyoshi Kurosawa film after last week's Sweet Home. Cure is a gritty cat and mouse psychological thriller that is suspenseful and dabbles in horror (as the genre is KK's great staple). The mise-en-scene and plain atmosphere is a solid foundation for where the film's themes further extrapolate. [...] More than Kurosawa's obvious statement of the influence of Fincher's Se7en (which I see), I feel there is an even greater similarity to Michael Mann's Manhunter [...] Cure, on the other hand, goes for the subdued approach, and while I certainly felt plenty of suspense amidst the lackadaisical yet gripping conversations, I feel a huge suppression of actual horror. [...] The process of the antagonist's questioning comes across vastly superior in the reasoning behind the plot points, but the writing doesn't take the ideas far enough. All of it feels just barely scratched upon the surface. [...] It just didn't hit the high notes as well as it could have, particularly with the writing. The directorial skill is there but not tuned or well adjusted to the themes at hand.

**Leitura para conferência:** review sobre comparações com outros filmes (Se7en, Manhunter, Sátántangó) e uma crítica de que "the writing doesn't take the ideas far enough" — não menciona explicitamente ritmo lento, nihilismo, identidade ou atmosfera visual da forma como os 5 temas do bucket os descrevem; a ausência de atribuição é defensável (a review fala mais de comparações de gênero do que dos temas específicos listados) — mas é uma zona cinzenta: "goes for the subdued approach" e "huge suppression of actual horror" tocam tangencialmente em atmosfera/ritmo sem usar essas palavras. Caso limítrofe para julgamento humano.

---

## Tabela-resumo final

| Bucket | Gabarito (razão / maior%) | Exp.1 sem thinking (razão / maior%) | Exp.3-A contagem (razão / maior%) | **Exp.4 dois estágios (razão / maior%)** |
|---|---|---|---|---|
| `negativas` | 2,26 / 70% | 3,20 / 96% | 2,70 / 84% | **2,08 / 52%** |
| `medianas` | 1,85 / 50% | 2,20 / 60% | 3,50 / 90% | **1,45 / 50%** |
| `positivas` | 1,70 / 50% | 2,03 / 50% | 3,03 / 93% | **1,433 / 36,7%** |

Nas três colunas anteriores a razão sempre superou o gabarito (às vezes bastante); no experimento 4 ela fica ABAIXO do gabarito nos três buckets, e a fração do maior tema nunca passa de 52% — a primeira rodada em que o "quase-todo-mundo-menciona-isso" desaparece por completo.

## Tempo e extrapolação

| Filmes | Minutos de LLM local (dois estágios) | Horas |
|---|---|---|
| 1 (`cure`, 13 chamadas) | ~13,4 min | 0,22h |
| 50 | ~671,7 min | **~11,19h** |
| 300 | ~4.030 min | **~67,17h** |

Comparado à variante A do experimento 3 (~7,0 min/filme): o dois-estágios é **~1,9x mais lento** (13 chamadas contra 3 por filme — o custo de trocar 1 chamada "confie na contagem do modelo" por N chamadas "o código conta de verdade"). A razão soma/n_reviews, em troca, deixou de estar sistematicamente inflada nas três rodadas anteriores.
