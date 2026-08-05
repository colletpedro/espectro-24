# Espectro 24 — Experimento 3: duas hipóteses contra a inflação de frequências

Gerado a partir de `scripts/comparar_sintese_local_v3.py`. **Chamadas Gemini: 0. Requisições Letterboxd: 0. Requisições TMDB: 0.** Reviews 100% do cache (`Fetcher(offline=True)`, `n_network=0` confirmado antes de qualquer chamada).

**Esta é uma sessão de EXPERIMENTO, não um bump de versão.** `SPEC.md` e o prompt de produção (`build_system_prompt`) não foram tocados — os blocos de teste foram anexados por cima do prompt de produção em tempo de execução, via monkeypatch escopado e restaurado logo após cada chamada. `resultado/cure.json` e os resultados dos experimentos 1 e 2 não foram tocados.

> **Nenhum veredito de qualidade literária é emitido aqui.** Este documento reporta números e textos; a avaliação semântica dos temas é humana.

## O experimento

**Hipótese A** — o prompt pede `mencoes_aproximadas` e o modelo ESTIMA; uma instrução explícita de CONTAGEM corrigiria.
**Hipótese B** — raciocínio CURTO E LIMITADO ajuda (ao contrário do raciocínio livre do experimento 2, que divergiu sem produzir resultado utilizável em 2 de 3 buckets).

| Variante | Blocos anexados | think | num_predict |
|---|---|---|---|
| **A** | CONTAGEM DAS MENÇÕES | `false` | 3000 |
| **B** | CONTAGEM DAS MENÇÕES + RACIOCÍNIO BREVE | `true` | 6000 |

Texto exato dos blocos (anexados ao final do prompt de produção, nunca editando-o):

> **CONTAGEM DAS MENÇÕES**
> Para cada tema identificado, percorra as reviews recebidas uma a uma e conte quantas delas mencionam aquele tema. O valor de mencoes_aproximadas deve ser o resultado dessa contagem, não uma impressão geral. Um tema mencionado por quase todas as reviews é raro: se você chegar a um número próximo do total, releia e confirme antes de registrá-lo.

> Antes de responder, raciocine de forma breve e objetiva: liste os temas candidatos e faça a contagem de cada um. Não rascunhe a resposta várias vezes nem reescreva formulações alternativas — poucas linhas de raciocínio bastam.

## Resultado de execução — resumo

| Variante | negativas | medianas | positivas |
|---|---|---|---|
| **A** | ✅ 134,8s, 1 chamada | ✅ 140,0s, 1 chamada | ✅ 146,7s, 1 chamada |
| **B** | ❌ timeout em 600,0s, 0 chamadas concluídas | ❌ timeout em 600,0s, 0 chamadas concluídas | ❌ timeout em 600,0s, 0 chamadas concluídas |

**Variante B falhou nos 3 buckets, sem exceção.** O timeout de 600s por chamada (quase o dobro do maior tempo já observado no experimento 2 completo, 483s) esgotou sem que o servidor devolvesse resposta alguma — nem conteúdo, nem thinking, nem contagem de tokens. Não há dado de variante B para comparar: a hipótese B permanece **NÃO TESTADA** por limite de infraestrutura, não refutada por conteúdo. A robustez pedida (gravar por bucket, timeout por chamada, seguir em caso de falha) funcionou como projetado — o experimento completou os 6 buckets programados (3 sucesso + 3 falha registrada) em vez de travar inteiro como no experimento 2.

---

## Bucket `negativas` (50 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Variante A | (4) Variante B |
|---|---|---|---|---|
| **Temas (ordem de frequência)** | Ritmo lento e tedioso (35); Falta de tensão/mistério/terror (25); Enredo e roteiro fracos/repetitivos (18); Personagens desinteressantes/planos (15); Filme superestimado/pretensioso (12); Final insatisfatório/abrupto (8) | Ritmo excessivamente lento e estagnação da narrativa (48); Personagens desprovidos de profundidade e interesse (35); Narrativa previsível sem tensão dramática (32); Atmosfera clínica e excessivamente limpa (18); Tratamento superficial de hipnose/psicologia (15); Atores impessoais/robóticos (12) | Aburrimento e ritmo excessivamente lento (42); Narrativa repetitiva sem evolução (35); Personagens planos e pouco envolventes (28); Incredibilidade dos elementos centrais (18); Falta realista da atmosfera de terror (12) | *(sem dado — timeout)* |
| **N° de temas** | 6 | 6 | 5 | — |
| **SOMA das menções** | 113 | 160 | 135 | — |
| **Razão soma/n_reviews** | **2,26** | **3,20** | **2,70** | — |
| **Maior menção individual** | 35/50 (70%) | 48/50 (96%) | 42/50 (84%) | — |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 | — |
| **Denominador correto** | — | sim | sim | — |
| **Numerador clampado** | — | não | não | — |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas | — |

A variante A reduziu a inflação em relação ao experimento 1 (2,70 vs. 3,20), mas ainda bem acima do gabarito (2,26). O caso extremo também recuou (42/50 vs. 48/50), mas continua sendo o tema mais frequente do bucket com quase 5x a magnitude relativa do topo do gabarito (84% vs. 70% das reviews).

---

## Bucket `medianas` (20 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Variante A | (4) Variante B |
|---|---|---|---|---|
| **Temas (ordem de frequência)** | Ritmo lento e confusão narrativa (10); Final insatisfatório/ambíguo (8); Ideias intrigantes, mas execução falha (7); Atmosfera e estilo visual eficazes (6); Necessidade de revisitação para compreensão (6) | Atmosfera lenta e ambígua que divide a audiência (12); Problemas na resolução dos mistérios (9); Conceitos abstratos de identidade e mal (8); Distância emocional espectador-personagens (6); Confusão narrativa sobre motivações (5); Realismo perturbador vs. sobrenatural (4) | Narrativa elíptica e ambiguidade da resolução do mistério (18); Ritmo lento, atmosfera opressora e tom surrealista (16); Desconexão emocional do público com os temas filosóficos (12); Atuações contidas e presença marcante de silêncios (10); Incerteza sobre a natureza do mal: sobrenatural versus psicológico (8); Insatisfação com a falta de respostas concretas ao final (6) | *(sem dado — timeout)* |
| **N° de temas** | 5 | 6 | 6 | — |
| **SOMA das menções** | 37 | 44 | 70 | — |
| **Razão soma/n_reviews** | **1,85** | **2,20** | **3,50** | — |
| **Maior menção individual** | 10/20 (50%) | 12/20 (60%) | 18/20 (90%) | — |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 | — |
| **Denominador correto** | — | sim | sim | — |
| **Numerador clampado** | — | não | não | — |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas | — |

**Achado contrário à hipótese A neste bucket:** a instrução explícita de contagem NÃO reduziu a inflação — piorou. Razão soma/n_reviews subiu de 2,20 (exp.1) para **3,50** (variante A), e o maior tema isolado saltou de 12/20 (60%) para 18/20 (90%) — o valor relativo mais extremo de todo o experimento (mais alto até que o 48/50=96% do exp.1 em termos absolutos, mas 90% é a maior FRAÇÃO do bucket já observada).

**Checagem anti-spoiler:** o exp.1 trouxe "personagem amnésico" e "transição entre outras vítimas" (achados sinalizados naquele relatório). Na variante A, o tema mais próximo é "Narrativa elíptica e ambiguidade da resolução do mistério" e "Incerteza sobre a natureza do mal: sobrenatural versus psicológico" — referenciam uma AMBIGUIDADE temática (mesmo nível de abstração do gabarito, que também tem "Ideias intrigantes, mas execução falha"), sem citar mecânica de trama específica, traço de personagem nomeado ou evento de desfecho. Não encontrei o padrão do exp.1 reaparecendo nesta variante — reportado para revisão humana, não como veredito.

---

## Bucket `positivas` (30 reviews)

| | (1) Gabarito Gemini | (2) Exp.1 sem thinking | (3) Variante A | (4) Variante B |
|---|---|---|---|---|
| **Temas (ordem de frequência)** | Atmosfera e Tom Perturbador/Hipnótico (15); Pacing Lento e Deliberado (10); Temas Psicológicos e Existenciais (9); Atuação do Antagonista (6); Design de Som e Cinematografia (6); Ausência de Respostas e Ambiguidade (5) | Atmosfera de opressão e paranoia (15); Atuação contida dos atores (12); Estética visual minimalista (10); Tema da identidade perdida (9); Psicologia do mal oculto (8); Tratamento lento e deliberado (7) | Atmosfera de vazio e paranoia onipresente (28); Manipulação psicológica através do vazio interior (18); Estética naturalista e estética sóbria (15); Som design e ruído ambiente como ferramenta narrativa (12); Desconstrução da identidade humana (10); Violência banalizada sem drama (8) | *(sem dado — timeout)* |
| **N° de temas** | 6 | 6 | 6 | — |
| **SOMA das menções** | 51 | 61 | 91 | — |
| **Razão soma/n_reviews** | **1,70** | **2,03** | **3,03** | — |
| **Maior menção individual** | 15/30 (50%) | 15/30 (50%) | 28/30 (93%) | — |
| **JSON válido de 1ª / retentativas** | — | sim / 0 | sim / 0 | — |
| **Denominador correto** | — | sim | sim | — |
| **Numerador clampado** | — | não | não | — |
| **Idioma / aspas** | — | pt-BR / sem aspas | pt-BR / sem aspas | — |

Mesmo padrão do bucket `medianas`: a razão soma/n_reviews piora com a instrução de contagem (2,03 → 3,03), e o tema mais frequente salta para 93% do bucket (28/30) — o maior valor relativo do experimento inteiro depois do 90% de `medianas`.

**Checagem anti-spoiler:** "Violência banalizada sem drama" é o tema mais próximo de uma referência a conteúdo/mecânica — descreve um EFEITO estilístico (como a violência é tratada), não um evento de trama específico. Sem menção a personagem nomeado ou desfecho.

---

## Tabela-resumo final

| Bucket | Gabarito (razão) | Exp.1 sem thinking (razão) | Variante A — CONTAGEM (razão) | Variante B — CONTAGEM+raciocínio breve |
|---|---|---|---|---|
| `negativas` | 2,26 | 3,20 | **2,70** (melhora parcial) | sem dado |
| `medianas` | 1,85 | 2,20 | **3,50** (piora) | sem dado |
| `positivas` | 1,70 | 2,03 | **3,03** (piora) | sem dado |

**Padrão observado:** a variante A melhorou o bucket mais numeroso (`negativas`, 50 reviews) mas piorou visivelmente os dois buckets menores (`medianas` 20, `positivas` 30) — em ambos, a razão soma/n_reviews da variante A é a PIOR das três colunas com dado, e o tema mais mencionado passou a cobrir 90%+ do bucket. Reportado como dado, não como conclusão — comparação semântica e julgamento sobre causa (ex.: buckets menores dão menos "textura" para a contagem se ancorar, e a instrução pode ter empurrado o modelo para contagens redondas e extremas) fica para leitura humana.

## Tempo e extrapolação

### Variante A (única com dado completo)

| Bucket | Tempo Ollama | Chamadas |
|---|---|---|
| `negativas` (50 reviews) | 134,8s | 1 |
| `medianas` (20 reviews) | 140,0s | 1 |
| `positivas` (30 reviews) | 146,7s | 1 |
| **Total (`cure`, 3 buckets)** | **421,5s ≈ 7,03 min** | 3 |

**Extrapolação** (mesma ressalva do experimento 1 — amostra de 1 filme, variação real esperada):

| Filmes | Minutos de LLM local | Horas |
|---|---|---|
| 1 | ~7,0 min | 0,12h |
| 50 | ~351,5 min | **~5,86h** |
| 300 | ~2.109 min | **~35,15h** |

Comparado ao experimento 1 (sem thinking, sem bloco de contagem): 390,3s totais no `cure` (~6,51 min) — a variante A é **~8% mais lenta** (o bloco de contagem adiciona texto ao prompt e parece puxar respostas um pouco mais longas), sem melhorar a inflação de forma consistente.

### Variante B — sem extrapolação possível

Nenhuma chamada completou dentro de 600s em nenhum dos 3 buckets. Não há piso nem teto confiável para extrapolar tempo por filme — o único fato mensurável é que **>600s por chamada, 3 chamadas por filme, no mínimo >1.800s (30 min) por filme só de tempo de espera sem garantia de sucesso**, o que já torna a variante B inviável para uso em lote nesta configuração de hardware/modelo, independentemente do resultado semântico que produziria se completasse.

## Conclusão dos dados (sem veredito de qualidade)

- **Hipótese A (contagem explícita corrige a inflação):** parcialmente e inconsistentemente suportada — melhora em 1 de 3 buckets (`negativas`), piora nos outros 2. Não é uma correção confiável na forma testada.
- **Hipótese B (raciocínio breve e limitado evita a divergência do experimento 2):** não testável nesta rodada — timeout de infraestrutura em 100% das tentativas, sem nenhum dado de conteúdo capturado.
- A robustez de execução pedida (gravação por bucket, timeout por chamada, continuar após falha) funcionou como projetado: o experimento completo (6 tentativas de bucket) terminou em vez de travar como o experimento 2.
