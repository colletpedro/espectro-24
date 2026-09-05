# A margem de 20pp — estudo estatístico e de produto

**Estatística sobre dado que já existe. Zero chamada de LLM. Nenhum arquivo de
`resultado/` foi escrito** (`git status resultado/` sem diff além dos dois
`.bak` que já estavam lá antes desta sessão). **Nenhum filme regerado, nenhum
veredito reescrito, `margem_lift_pp` intocado em todo lugar, taxonomia e
`taxonomia_id` intocados, frontend intocado.** Suíte: **1.524 passaram**, o
mesmo número de §2.8.

**O desenho da simulação foi registrado ANTES de rodar**, em
[DESENHO_NULO_DO_MAXIMO.md](DESENHO_NULO_DO_MAXIMO.md), com as previsões
escritas para poderem falhar — **uma delas falhou e está reportada como falha**
(§2.7 abaixo).

**Convenção deste relatório:** **MEDIDO** = número que saiu de código rodado
nesta sessão ou de documento anterior citado com a fonte. **VISTO** = leitura,
julgamento, argumento. Onde as duas se misturam, a frase diz qual é qual.

**Nenhuma decisão foi tomada.** O entregável é a recomendação da Entrega 6,
para o dono aprovar ou recusar.

---

## Validação do instrumento, antes de qualquer resultado

A população reconstruída aqui (`amostra_do_bruto(slug) ∩
consenso_verificado.jsonl`, cobertura 100% de §2.8) reproduz, sem ajuste:

- **16 `tematico` / 19 `valorativo`** — o número de §2.8;
- **exatamente os 10 filmes** de `ESTABILIDADE_10_FLIPS.md`, com os mesmos
  valores de lift depois (17,5 · 20,0 · 17,5 · 15,0 · 12,5 · 25,0 · 17,5 ·
  12,5 · 27,5 · 20,0);
- **o estado publicado de todos os 35**, reconstruído independentemente a
  partir do campo `lift_pp` de cada `resultado/<slug>.json` — **zero
  divergências**.

Se algum desses três tivesse falhado, nada abaixo valeria.

---
---

# ENTREGA 1 — as cinco evidências numa figura só

## A tabela

| # | evidência | o que mede | população | número | o que ela **NÃO** diz |
|---|---|---|---|---|---|
| 1 | **Nulo de permutação** (SPEC §2.5) | fração dos **pares (eixo, bucket)** acima de 20pp no catálogo inteiro que apareceria por acaso | `consenso.jsonl` **CRU**, 35 filmes, todas as células | **34%** a 20pp (61% a 15pp, 27% a 25pp) | nada sobre um filme específico; nada sobre o **máximo** por filme, que é a estatística que o produto usa; e **não é a população publicada** |
| 2 | **Bootstrap por célula** (ESTUDO §8, recomputado em §2.8) | com que probabilidade uma marcação publicada sobreviveria a outra amostra da MESMA população | produção ∩ verificado, cobertura 100% | das **23** células acima da margem: **1** com p≥90%, **10** entre 60–90%, **12** abaixo de 60% | não mede se a marcação é real — mede se ela é **repetível**. Uma marcação pode ser estável e falsa |
| 3 | **Curva de retorno por n** (MEDICAO, Entrega 2) | como P(filme mantém contraste) e o IC95 do lift dominante se movem com n | os 35, reamostragem | P cai **0,993 → 0,718** de n=10 a n=50; IC95 = **38,4pp** em n=40, quase o dobro da margem; o ajuste é exatamente 1/√n | n=50 é extrapolação com a distribuição empírica congelada; não diz se a frequência observada se moveria |
| 4 | **Observação direta** (SPEC §2.8 / ESTABILIDADE_10_FLIPS) | quantos filmes trocam de estado quando a cobertura vai de 70,7% para 100% | os 35, dado real | **10 de 35**, sendo **6** perdendo um contraste que o veredito nomeia por extenso | é UM evento, não uma distribuição; não isola a causa sozinho |
| 5 | **Calibração de gabarito** (RELATORIO_GABARITO §D) | concordância entre a leitura do MODELO e a leitura do dono, por tipo de tema | 28 reviews (`napoleon`/med) e 14 (`talk-to-me`/neg) | **96,4%** em tema visual, **71,4%** em tema de registro de fala | **não é uma medida de instabilidade da classificação por eixo**, e não é leitura humana discordando de si mesma — ver a correção abaixo |

## Onde elas concordam, e é o ponto

**MEDIDO nesta sessão, e é a costura que faltava:** as quatro primeiras não são
quatro achados. São **quatro sintomas de um mecanismo só**, que a Entrega 2
mede diretamente pela primeira vez — o estado `contraste` é o **máximo de 30
células ruidosas** comparado a um número fixo, e o máximo de um conjunto
ruidoso é enviesado para cima, com o viés crescendo quando n encolhe.

Isso explica cada uma:

- (1) é o viés visto **por célula agregada** — 34% dos pares são ruído;
- (2) é o viés visto **por reamostragem** — metade das marcações não se repete;
- (3) é o viés visto **por n** — P(tematico) cai com mais dado porque o ruído
  que inflava o máximo encolhe (não é paradoxo, é a definição de máximo);
- (4) é o viés visto **acontecendo**, com dado real, uma vez.

**Não há discordância entre as quatro.** Onde os números parecem discordar
(34% de ruído por par vs. 92,5% de "o filme mantém contraste"), eles estão
medindo coisas diferentes: um é a taxa por **célula**, o outro é a
probabilidade do **máximo sobre 30 células** — e a diferença entre os dois **é
o efeito** que este estudo mede.

## Três correções às evidências, e uma delas é a que o dono vem citando como firme

### Correção 1 — a evidência 5 não é o que o briefing desta sessão diz que é

**MEDIDO.** O briefing desta sessão descreve a evidência 5 como *"mesmo leitura
humana cuidadosa discorda de si mesma conforme o tipo de tema"*. Ela não é
isso. Lendo `RELATORIO_GABARITO_E_COBERTURA.md` §Etapa C/D:

- os 96,4% e 71,4% são **concordância entre o MODELO e o dono**, não do dono
  consigo mesmo — não há releitura do mesmo humano em nenhum dos dois casos;
- a tarefa medida é **"esta review sustenta este TEMA?"** (verificação binária
  de bullet), **não** "esta review carrega este EIXO?" (classificação por
  eixo). São instrumentos diferentes, com prompts diferentes, e a segunda é a
  que alimenta o lift;
- os denominadores são **28** e **14** reviews.

**MEDIDO nesta sessão** — a diferença entre as duas concordâncias é real mas
imprecisa: Fisher exato bilateral **p = 0,035** (27/28 contra 10/14), e os
IC95 de Wilson são **[82,3%; 99,4%]** e **[45,4%; 88,3%]**. A direção do achado
("tema de registro de fala é mais difícil que tema visual") **sobrevive**; a
magnitude não deve ser citada com essas duas casas decimais.

**VISTO — o que a evidência 5 sustenta e o que não sustenta.** Ela sustenta:
*"a confiabilidade da leitura por modelo depende do tipo de julgamento, e não
existe fator de correção fixo"* — que é exatamente o que o relatório original
escreveu, e continua correto. Ela **não** sustenta: *"nenhum instrumento
entrega a precisão que uma fronteira fina exigiria"*. Essa frase é
provavelmente verdadeira, mas o suporte dela vem das evidências 1–4 e da
reprodutibilidade individual de 26,5% de `ESTABILIDADE_AGREGADA.md`, **não**
desta calibração. A evidência 5 deve sair da lista de suportes da margem, ou
entrar rebaixada ao que ela mede.

### Correção 2 — o 34% de §2.5 está medido na população errada, e o número certo é pior

**MEDIDO nesta sessão.** §2.5 declara que a tabela de margem usa *"a amostra
classificada bruta por decisão metodológica de longa data"* — `consenso.jsonl`
cru, que acumula a seleção antiga e a nova lado a lado (§[D3], "duas populações
de 40") e que **não** é a população que o bloco `eixos` publicado conta.
Recalculando a mesma estatística na população publicada, com cobertura 100%:

| margem | pares acima (observado) | esperado sob o nulo | fração de ruído |
|---|---:|---:|---:|
| 15pp | 56 | 28,9 | **51,6%** |
| **20pp** | **23** | **9,9** | **42,8%** |
| 25pp | 11 | 3,7 | **33,3%** |

**A margem de 20pp entrega 42,8% de ruído por célula na população que o produto
de fato publica, não 34%.** O número da spec não está errado para o que ele
mede; está medindo outra população. `CLASSIFICACAO_CONSOLIDADO.md` §6 já
registrava 41,1% num terceiro corpus, e o valor recomputado aqui fica em cima
dele.

### Correção 3 — a evidência 4 tem uma causa mais específica do que "a margem é porosa"

**MEDIDO nesta sessão, e é a descoberta que mais muda a leitura do caso.**
§2.8 e §2.9 explicam os 10 flips dizendo que "a margem já era conhecida como
porosa nesse regime de n". O regime de n é **muito pior do que "≈40"**.

Reconstruindo o `de_n` de cada célula direto dos 35 `resultado/<slug>.json`
publicados:

| `n` por bucket **no catálogo publicado** | valor |
|---|---:|
| mínimo | **5** |
| mediana | **28** |
| média | **27,3** |
| máximo | 40 |
| buckets com n < 30 | **56 de 105** |
| buckets com n < 20 | **24 de 105** |

Os filmes cujo veredito hoje nomeia uma causa que o dado completo não sustenta
foram decididos com `n` de **12 a 27** por bucket, não 40. `perfect-days-2023`
publica com **[18, 12, 17]**; `hereditary` com **[22, 13, 16]**;
`everything-everywhere-all-at-once` com **[19, 16, 17]**.

**A frase "n≈40 é insuficiente para a margem de 20pp" é verdadeira, mas o
catálogo publicado nunca esteve em n=40.** Ele está em n≈28, e a Entrega 2
mostra que a diferença entre os dois regimes é enorme.

---
---

# ENTREGA 2 — o problema de comparações múltiplas, medido

## 2.1 O que foi construído

O nulo do **máximo**, por permutação do rótulo de bucket dentro de cada filme,
**B = 10.000** por filme, semente 24, aritmética exata em inteiros escalados
(reproduz `Fraction` do código de produção sem ponto flutuante em decisão
nenhuma). O embaralhamento preserva o conjunto de eixos de cada review intacto
— logo **toda a dependência entre eixos da mesma review sobrevive** — mais a
frequência global de cada eixo e o tamanho de cada bucket. Destrói só a
associação eixo↔grupo. Desenho completo, incluindo a alternativa recusada e por
quê, em [DESENHO_NULO_DO_MAXIMO.md](DESENHO_NULO_DO_MAXIMO.md) §3.

**Nenhuma decisão de desenho ficou em aberto** — o briefing especificou o
embaralhamento com precisão suficiente ("embaralhar o rótulo de bucket das
reviews dentro de cada filme, preservando os tamanhos de bucket e a estrutura
de eixos por review"), e é exatamente o que rodou. Não houve motivo para parar.

## 2.2 O nulo, por filme

**MEDIDO.** `n` é a faixa dos três buckets sob cobertura 100%. `T` é o lift
máximo observado sobre as 30 células. `med₀` e `p95₀` são a mediana e o
percentil 95 do máximo **sob o nulo**. `pct(20)` é em que percentil do nulo o
limiar de 20pp cai. `P(falso)` é P(T_nulo ≥ 20pp) — a probabilidade de um filme
**sem contraste nenhum** sair publicado como `tematico`.

| filme | n | T (pp) | med₀ | p95₀ | pct(20) | P(falso) | p-valor | publ. | @100% |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `obsession-2026` | 5–8 | 42,5 | **40,0** | 62,5 | **2** | **0,976** | 0,4034 | tema | temat |
| `cats-2019` | 40 | 35,0 | 15,0 | 22,5 | 83 | 0,173 | **0,0009** | tema | temat |
| `anatomy-of-a-fall` | 40 | 30,0 | 12,5 | 22,5 | 86 | 0,141 | **0,0051** | tema | temat |
| `barbie` | 40 | 27,5 | 15,0 | 22,5 | 85 | 0,150 | **0,0133** | tema | temat |
| `cure` | 40 | 27,5 | 15,0 | 22,5 | 81 | 0,191 | **0,0188** | tema | temat |
| `the-substance` | 40 | 27,5 | 15,0 | 22,5 | 80 | 0,195 | **0,0185** | valo | temat |
| `oppenheimer-2023` | 40 | 25,0 | 15,0 | 22,5 | 81 | 0,193 | **0,0477** | valo | temat |
| `wonka` | 32–40 | 22,8 | 15,1 | 25,0 | 81 | 0,193 | 0,0866 | tema | temat |
| `dune-part-two` | 40 | 22,5 | 15,0 | 22,5 | 80 | 0,202 | 0,0992 | tema | temat |
| `joker-folie-a-deux` | 40 | 22,5 | 15,0 | 22,5 | 81 | 0,194 | 0,0981 | tema | temat |
| `the-invite-2026` | 40 | 22,5 | 15,0 | 22,5 | 79 | 0,206 | 0,1015 | tema | temat |
| `dune-2021` | 40 | 20,0 | 15,0 | 22,5 | 80 | 0,203 | 0,2036 | valo | temat |
| `eighth-grade` | 40 | 20,0 | 12,5 | 22,5 | 88 | 0,119 | 0,1191 | tema | temat |
| `interstellar` | 40 | 20,0 | 15,0 | 22,5 | 83 | 0,172 | 0,1716 | tema | temat |
| `the-hateful-eight` | 40 | 20,0 | 15,0 | 22,5 | 81 | 0,190 | 0,1896 | tema | temat |
| `wicked-2024` | 37–40 | 20,0 | 14,7 | 23,9 | 83 | 0,168 | 0,1682 | valo | temat |
| `talk-to-me-2022` | 39–40 | 18,5 | 13,4 | 22,2 | 89 | 0,112 | 0,1650 | valo | valor |
| `bones-and-all` | 40 | 17,5 | 15,0 | 22,5 | 84 | 0,157 | 0,2780 | tema | valor |
| `everything-everywhere-all-at-once` | 40 | 17,5 | 15,0 | 22,5 | 82 | 0,183 | 0,3092 | tema | valor |
| `im-still-here-2024` | 40 | 17,5 | 15,0 | 22,5 | 82 | 0,178 | 0,3148 | valo | valor |
| `longlegs` | 40 | 17,5 | 15,0 | 22,5 | 81 | 0,194 | 0,3384 | valo | valor |
| `perfect-days-2023` | 40 | 17,5 | 15,0 | 22,5 | 81 | 0,191 | 0,3409 | tema | valor |
| `aftersun` | 40 | 15,0 | 12,5 | 22,5 | 84 | 0,156 | 0,4997 | valo | valor |
| `hereditary` | 40 | 15,0 | 15,0 | 22,5 | 82 | 0,184 | 0,5504 | tema | valor |
| `shutter-island` | 40 | 15,0 | 12,5 | 22,5 | 86 | 0,140 | 0,4675 | valo | valor |
| `friday-the-13th-2009` | 40 | 12,5 | 12,5 | 22,5 | 86 | 0,140 | 0,7211 | valo | valor |
| `napoleon-2023` | 40 | 12,5 | 15,0 | 22,5 | 82 | 0,179 | 0,7558 | tema | valor |
| `parasite-2019` | 40 | 12,5 | 12,5 | 22,5 | 85 | 0,151 | 0,7315 | valo | valor |
| `spider-man-across-the-spider-verse` | 40 | 12,5 | 15,0 | 22,5 | 83 | 0,170 | 0,7461 | tema | valor |
| `the-godfather` | 30–40 | 12,5 | 15,0 | 24,2 | 79 | 0,207 | 0,7606 | valo | valor |
| `avengers-endgame` | 40 | 10,0 | 12,5 | 22,5 | 87 | 0,132 | 0,9024 | valo | valor |
| `cidade-de-deus` | 40 | 10,0 | 15,0 | 22,5 | 82 | 0,179 | 0,9361 | valo | valor |
| `mother-2017` | 40 | 10,0 | 12,5 | 22,5 | 86 | 0,141 | 0,9045 | valo | valor |
| `pearl-2022` | 27–40 | 10,0 | 15,0 | 24,5 | 81 | 0,194 | 0,9048 | valo | valor |
| `the-northman` | 40 | 10,0 | 15,0 | 22,5 | 82 | 0,178 | 0,9402 | valo | valor |

## 2.3 Onde 20pp cai no nulo (item 2 do briefing)

**MEDIDO.**

- **Percentil mediano de 20pp no nulo: 82.** Isto é: em metade dos filmes, um
  filme **sem contraste nenhum** produziria um máximo abaixo de 20pp em ~82%
  das permutações — e **acima** em ~18%.
- **Em 1 dos 35 filmes 20pp está abaixo da mediana do nulo**, e é
  `obsession-2026` (n = 5, 6, 8): a mediana do máximo sob o nulo é **40,0pp**,
  o dobro do limiar, e **97,6%** das permutações cruzariam a margem.
  `ESTUDO_CATALOGO_35.md` §8 já dizia *"não é um filme com contraste forte; é um
  filme sem denominador"*; aqui isso vira número: o estado `tematico` de
  `obsession-2026` não carrega **nenhuma** informação sobre o filme.
- **Taxa média de falso contraste a 20pp: 0,195** sobre os 35 · **0,172**
  restrito aos 29 filmes com 40/40/40 nos três buckets.

**MEDIDO — e no `n` em que o catálogo foi de fato publicado (mediana 28), a
mesma taxa é 0,373.** Por filme:

| filme | n médio publicado | P(falso contraste @ 20pp) |
|---|---:|---:|
| `obsession-2026` | 6 | **0,894** |
| `perfect-days-2023` | 15 | **0,858** |
| `spider-man-across-the-spider-verse` | 20 | 0,658 |
| `barbie` | 20 | 0,638 |
| `bones-and-all` | 19 | 0,615 |
| `dune-2021` | 17 | 0,612 |
| `hereditary` | 17 | 0,604 |
| `the-substance` | 17 | 0,589 |
| `everything-everywhere-all-at-once` | 17 | 0,588 |
| `avengers-endgame` | 19 | 0,581 |

**O número que resume o problema inteiro:** nos **6 filmes que hoje publicam um
veredito nomeando a causa que separa os grupos e que o dado completo não
sustenta**, a probabilidade média de aquele contraste ter aparecido **puramente
por ruído** era de **0,633**.

Não é "a margem é porosa". É: **essas seis páginas nomeiam uma causa que, na
amostra em que foram decididas, tinha ~63% de chance de ser sorteio.**

## 2.4 A taxa de falso contraste do catálogo (item 3 do briefing)

**MEDIDO — significância bruta, por filme (nulo do próprio filme):**

| nível | filmes distinguíveis do nulo |
|---|---:|
| α = 0,10 | **9 de 35** |
| α = 0,05 | **6 de 35** |
| α = 0,01 | **2 de 35** |

Os 6 a α = 0,05: `cats-2019`, `anatomy-of-a-fall`, `barbie`, `the-substance`,
`cure`, `oppenheimer-2023`. Note que **dois deles (`the-substance`,
`oppenheimer-2023`) estão publicados hoje como `valorativo`** — são
justamente parte dos 4 flips inofensivos de §2.9.

**MEDIDO — com correção para a multiplicidade ENTRE os 35 filmes** (o segundo
nível de multiplicidade, acima das 30 células):

| nível | bruto | Holm–Bonferroni | Benjamini–Hochberg |
|---|---:|---:|---:|
| α = 0,10 | 9 | **1** | **2** |
| α = 0,05 | 6 | **1** | **1** |
| α = 0,01 | 2 | 0 | 0 |

**Sobrevive a Holm a 5%: um filme, `cats-2019`.** Sobrevive a BH a 10%: dois,
`cats-2019` e `anatomy-of-a-fall`.

**MEDIDO — taxa de falsa descoberta entre os `tematico`.** Com π₀ estimado por
Storey (λ = 0,5) em **0,629** — ou seja, ~22 dos 35 filmes provavelmente não
têm contraste real nenhum:

| limiar (n=40) | P(falso) por filme | `tematico` | FDR (π₀=0,63) | FDR (π₀=1) |
|---|---:|---:|---:|---:|
| **20,0pp (hoje)** | 0,173 | **16** | **23,8%** | **37,9%** |
| 22,5pp | 0,083 | 11 | 16,7% | 26,5% |
| 25,0pp | 0,037 | 7 | 11,7% | 18,7% |
| 27,5pp | 0,016 | 6 | 5,8% | 9,2% |
| 30,0pp | 0,006 | 3 | 4,3% | 6,9% |

**Entre 4 e 6 dos 16 filmes `tematico` do catálogo a 100% de cobertura são
ruído puro** — uma taxa de falso contraste de **24% a 38%**.

**VISTO — qual das duas leituras de multiplicidade vale.** Holm/BH e a
estimativa por π₀ discordam (1–2 filmes contra 7–11), e a discordância é
legítima, não erro: elas controlam coisas diferentes. Holm controla a chance de
**qualquer** afirmação errada no catálogo inteiro — a pergunta certa se o
produto fizesse uma afirmação sobre o catálogo. BH e o π₀ controlam a
**proporção** de erradas entre as publicadas — a pergunta certa quando cada
página faz sua própria afirmação, lida isoladamente. **O produto é o segundo
caso**, e por isso a tabela de FDR é a que deve guiar o limiar. Isso precisa
ficar registrado como decisão, porque é uma escolha, não um fato: quem
argumentar que o leitor navega o catálogo inteiro e forma uma impressão
agregada estará pedindo Holm, e não estará errado — estará pedindo um catálogo
de 1 ou 2 filmes `tematico`.

## 2.5 A dependência de `n` (item 4a)

**MEDIDO.** Procedimento único: sob o nulo o bucket não carrega informação, logo
sortear 3n reviews do pool do filme e fatiá-las em três buckets de tamanho n
**é** a permutação quando 3n = N, subamostragem quando 3n < N, e reamostragem
com reposição quando 3n > N (a mesma extrapolação declarada em MEDICAO §2.2:
congela a distribuição empírica, mexe só na variância amostral). Conjunto fixo
de 29 filmes com 40/40/40, B = 4.000.

**Taxa de falso contraste, por limiar × n:**

| n | 12,5pp | 15pp | 17,5pp | 20pp | 22,5pp | 25pp | 27,5pp | 30pp | 35pp |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0,974 | 0,974 | 0,974 | **0,974** | 0,669 | 0,669 | 0,669 | 0,669 | 0,256 |
| 20 | 0,922 | 0,922 | 0,662 | **0,662** | 0,352 | 0,352 | 0,147 | 0,147 | 0,051 |
| 30 | 0,845 | 0,597 | 0,347 | **0,347** | 0,172 | 0,074 | 0,029 | 0,029 | 0,003 |
| **40** | 0,752 | 0,526 | 0,316 | **0,173** | 0,083 | 0,037 | 0,016 | 0,006 | 0,001 |
| 50 | 0,443 | 0,273 | 0,153 | **0,081** | 0,018 | 0,008 | 0,003 | 0,001 | 0,000 |
| 100 | 0,123 | 0,048 | 0,009 | **0,002** | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |

*(As colunas repetidas nas linhas de n pequeno não são erro: com n=10 o lift só
assume múltiplos de 10pp, então 12,5 · 15 · 17,5 · 20pp são **o mesmo corte**.
A tabela na grade atingível de cada n está em §3.2.)*

**Percentis do nulo do máximo, e a lei:**

| n | mediana₀ | p95₀ medido | p95₀ previsto por 1/√n (ancorado em n=40) |
|---:|---:|---:|---:|
| 10 | 30,00 | 47,95 | 45,17 |
| 20 | 20,00 | 32,76 | 31,94 |
| 30 | 16,55 | 26,55 | 26,08 |
| **40** | **14,40** | **22,59** | 22,59 |
| 50 | 12,00 | 20,07 | 20,20 |
| 100 | 8,78 | 14,52 | 14,28 |

**Erro máximo do ajuste: 2,8pp, e só em n=10.** O nulo do máximo obedece a
mesma lei 1/√n que MEDICAO Entrega 2 encontrou para a largura do IC — o que é o
esperado, e é a confirmação independente de que os dois estudos estão medindo o
mesmo mecanismo por caminhos diferentes.

**A leitura decisiva: em n = 20, a mediana do nulo do máximo é exatamente
20,0pp.** Um filme decidido com 20 reviews por bucket cruza a margem de 20pp em
**66% das permutações sem contraste nenhum**. **24 dos 105 buckets publicados
estão abaixo de n = 20.**

## 2.6 A dependência da carga de eixos (item 4b)

**MEDIDO**, n fixo em 40, 29 filmes:

- eixos por review: **2,12** (`eighth-grade`) a **3,67** (`the-hateful-eight`),
  média 2,95;
- **corr(carga, mediana do nulo) = +0,55**;
- **corr(carga, P(falso contraste @ 20pp)) = +0,74**.

O efeito é real mas de segunda ordem: a taxa de falso contraste vai de **0,119**
no filme com menos eixos por review a **0,206** no filme com mais — um fator
1,7×, contra o fator ~5,6× que a variação de n de 40 para 20 produz.

**VISTO.** A carga de eixos é um segundo parâmetro do nulo, e ela **não** é
constante entre filmes — o que significa que mesmo entre filmes com n idêntico
o limiar fixo não representa a mesma exigência probatória. Mas o desvio é
pequeno o bastante para que uma tabela por n, sem correção por carga, já capture
a maior parte do problema (§Entrega 4). Registrar como limitação conhecida, não
como parâmetro.

## 2.7 A previsão que FALHOU

Registrada em [DESENHO_NULO_DO_MAXIMO.md](DESENHO_NULO_DO_MAXIMO.md) §7,
previsão 3: *"o limiar necessário para taxa de falso contraste de 5% em n = 40
ficará acima de 30pp"*.

**MEDIDO: 25,0pp.** A previsão errou por ~5pp e na direção pessimista — eu
esperava que o viés de máximo sobre 30 células fosse mais violento do que é. A
segunda metade da mesma previsão (*"deixaria menos de 8 dos 35 tematico"*)
**acertou**: a 25pp são 7. As previsões 1, 2 e 4 se confirmaram.

**Consequência para a leitura de todo o resto:** o problema é **menos grave do
que eu previa em n=40**, e continua **muito mais grave do que o registro do
projeto supõe em n≈28**, que é onde o catálogo publicado de fato está.

---
---

# ENTREGA 3 — qual limiar produz taxa aceitável

## 3.1 O passo, e por que ele não é livre

**MEDIDO.** O lift é uma diferença entre frações de denominador `n`, logo ele só
assume **múltiplos de 100/n pontos percentuais**. Em n = 40 isso é **2,5pp**; em
n = 30, 3,33pp; em n = 20, **5pp**; em n = 10, **10pp**.

Consequências que governam toda esta entrega:

- **Qualquer limiar em (22,5 ; 25,0] produz exatamente o mesmo catálogo** entre
  os filmes de n=40. Um limiar de "22,8pp" não é mais fino que 25pp — é o
  **mesmo corte**, escrito de um jeito que sugere precisão que não existe.
- **O passo de varredura correto é o próprio 100/n, e ele muda com n.** A
  primeira versão desta varredura usou uma grade fixa de 2,5pp para todos os n,
  e isso produz limiares **inatingíveis** em n pequeno (não existe lift de
  32,5pp com n=20). A tabela abaixo está na grade própria de cada n.

## 3.2 Limiar necessário por n, para taxa convencional

**MEDIDO** — o menor valor **atingível** de lift cuja taxa de falso contraste
fica no alvo, sobre o nulo dos 29 filmes cheios:

| taxa alvo | n=10 | n=20 | n=30 | **n=40** | n=50 | n=100 |
|---|---:|---:|---:|---:|---:|---:|
| **10%** | 50,0pp | 35,0pp | 26,7pp | **22,5pp** | 20,0pp | 14,0pp |
| **5%** | 60,0pp | 40,0pp | 30,0pp | **25,0pp** | 22,0pp | 15,0pp |
| 1% | 70,0pp | 45,0pp | 36,7pp | 30,0pp | 26,0pp | 18,0pp |

A curva completa em n = 40, que é onde a decisão mora:

| limiar | 12,5 | 15,0 | 17,5 | **20,0** | 22,5 | 25,0 | 27,5 | 30,0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| taxa de falso contraste | 0,752 | 0,526 | 0,316 | **0,173** | 0,083 | 0,037 | 0,016 | 0,006 |

**As respostas diretas às perguntas da Entrega 3, no n atual (40):**

- **taxa de falso contraste de 10% exige limiar de 22,5pp** → catálogo vai de
  16 para **11 `tematico`**;
- **taxa de 5% exige 25,0pp** → catálogo vai para **7 `tematico`**;
- **20pp, o limiar de hoje, entrega 17,3%** — nem perto de qualquer nível
  convencional, e isso **no melhor n que o catálogo tem**. No n mediano em que
  ele foi publicado (28), entrega **37,3%**.
- **Em n = 20, o menor limiar que atinge 10% é 35pp** — e 35pp com n=20 exige
  que 11 das 20 reviews de um grupo carreguem um eixo que no máximo 4 das 20 de
  outro grupo carreguem. É um critério que quase nada satisfaz, e isso **não é
  defeito do critério**: é a medição dizendo que 20 reviews por bucket não
  sustentam a afirmação que o produto quer fazer.

## 3.3 O que isso faz com o catálogo

**MEDIDO**, sob cobertura 100%:

| limiar | `tematico` | `valorativo` | filmes `tematico` |
|---|---:|---:|---|
| 17,5pp | 22 | 13 | — |
| **20,0pp (hoje)** | **16** | **19** | anatomy · barbie · cats · cure · dune-2021 · dune-part-two · eighth-grade · interstellar · joker · obsession · oppenheimer · hateful-eight · the-invite · the-substance · wicked · wonka |
| 22,5pp | 11 | 24 | anatomy · barbie · cats · cure · dune-part-two · joker · obsession · oppenheimer · the-invite · the-substance · wonka |
| 25,0pp | 7 | 28 | anatomy · barbie · cats · cure · obsession · oppenheimer · the-substance |
| 27,5pp | 6 | 29 | anatomy · barbie · cats · cure · obsession · the-substance |
| 30,0pp | 3 | 32 | cats · obsession · the-substance ⚠️ |

⚠️ **`obsession-2026` sobrevive a TODOS os limiares fixos até 40pp**, e é o
filme cujo estado carrega menos informação de todo o catálogo (P(falso) =
0,976). **Nenhum limiar fixo resolve `obsession-2026`.** Só um critério que
olhe para n resolve. Isso sozinho já é o argumento da Entrega 4.

---
---

# ENTREGA 4 — fixo vs dependente de n vs critério estatístico

## 4.0 O achado que reorganiza a pergunta

**MEDIDO — e ele mostra que as três opções não são três.** Calculando o valor
crítico do nulo de cada filme separadamente:

| | nos 29 filmes com 40/40/40 |
|---|---|
| c(α=0,10) | mín **20,00** · mediana **20,00** · máx **22,50** (amplitude 2,50pp = **um** passo da grade) |
| c(α=0,05) | mín **22,50** · mediana **22,50** · máx **22,62** (amplitude **0,12pp**) |

**A opção (c) — critério estatístico — É a opção (a) — limiar fixo — para 29
dos 35 filmes.** Em α = 0,05, o valor crítico varia 0,12pp entre 29 filmes com
carga de eixos de 2,12 a 3,67 por review. Um número.

Onde (c) difere de (a) é exatamente nos **6 filmes com bucket abaixo de 40**:

| filme | n | c(α=0,10) | c(α=0,05) |
|---|---|---:|---:|
| `obsession-2026` | 5, 6, 8 | **57,9** | **64,6** |
| `pearl-2022` | 27, 40, 40 | 24,9 | 27,8 |
| `the-godfather` | 30, 40, 40 | 23,6 | 26,4 |
| `wonka` | 32, 34, 40 | 22,9 | 25,5 |
| `wicked-2024` | 37, 40, 37 | 21,3 | 23,7 |
| `talk-to-me-2022` | 39, 40, 40 | 20,7 | 23,1 |

E "diferir por n" **é** a opção (b).

> **A conclusão estrutural: (a), (b) e (c) não são três alternativas. São um
> mesmo critério em três graus de adaptação, e no catálogo atual (b) e (c) são a
> mesma regra escrita de dois jeitos.** A decisão real do dono é binária: **o
> limiar olha para `n` ou não?** Se olhar, a forma barata e exata de
> implementá-lo é uma **tabela congelada por n** — que é (b) na implementação e
> (c) na origem do número.

## 4.1 Custo de neutralidade (§0) — a pergunta obrigatória

**A resposta curta: não é violação do §0. É a aplicação do §0 a uma dimensão
onde ele estava sendo ignorado — e o próprio §0 já contém o precedente, escrito
por extenso, na regra de ordenação da v1.9.30.**

**Primeiro, o escopo.** O §0 governa a **neutralidade entre os três GRUPOS
dentro de um filme**: mesma cota 40/40/40, mesma estrutura, mesmo espaço, mesma
margem para os dois lados. Ele nunca falou sobre neutralidade **entre filmes**.
Um limiar por n **não toca em nada que o §0 governa**: dentro de cada filme, os
três buckets continuam sendo julgados pelo mesmo número, pela mesma métrica, com
o mesmo denominador. Não existe caminho pelo qual `negativas` receba um limiar e
`positivas` outro.

**Segundo, e é o ponto que vai para a spec: o limiar fixo NÃO é a mesma régua.
É o mesmo NÚMERO, que é outra coisa.** MEDIDO nesta sessão:

| o mesmo 20pp, em... | é o percentil ... do ruído | exigência probatória |
|---|---:|---|
| n = 10 | ~3 | praticamente nenhuma |
| n = 20 | ~34 | abaixo do acaso |
| n = 30 | ~65 | fraca |
| **n = 40** | **~83** | moderada |
| n = 100 | ~99,8 | forte |

**Um número constante aplicado a amostras de tamanhos diferentes exige provas
sistematicamente diferentes.** O filme com amostra pequena é julgado por uma
régua **mais frouxa** — ele passa mais fácil, e o que ele publica tem mais
chance de ser ruído. Chamar isso de neutralidade é chamar de neutro o resultado
de não olhar.

**Terceiro, o precedente já está dentro do §0, e a formulação é do próprio
dono** (v1.9.30, ordenação dos blocos por peso):

> *"E A ORDEM ANTIGA NÃO ERA NEUTRA — ERA CONSTANTE, que é outra coisa. Isto
> precisa ficar escrito porque a intuição diz o oposto (uma ordem que nunca muda
> parece a opção neutra)."*

O argumento é **estruturalmente idêntico**. Trocando "ordem" por "limiar" e
"peso" por "tamanho de amostra", o parágrafo se lê sem uma emenda. E o teste que
a v1.9.30 usou para se autorizar — *"a regra é função do DADO, não do
sentimento… não existe caminho pelo qual esta regra favoreça um lado"* —
**passa aqui também, e por construção**: `n` é quantas reviews com texto ≥150
caracteres o Letterboxd tem naquele bucket. É contagem, não juízo. Não existe
mecanismo pelo qual um limiar em função de n favoreça o grupo negativo ou o
positivo.

**Quarto, e é a metade honesta: o que se PERDE.** Duas coisas reais.

1. **Comparabilidade entre páginas.** O leitor que vê `tematico` em
   `cats-2019` e `valorativo` em `the-godfather` não tem como saber que o
   segundo foi julgado sob um limiar mais alto. A afirmação "estes dois filmes
   são diferentes" fica um grau mais fraca do que parece. **Mitigação medida:**
   isso afeta **6 de 35 filmes** hoje, e em 4 deles a diferença de limiar é de
   menos de um passo da grade. O caso extremo é um só (`obsession-2026`) e é
   exatamente o caso em que o produto **deveria** estar dizendo outra coisa.
2. **Uma regra a mais para explicar.** §4.2.

**Veredito da pergunta obrigatória: REFINAMENTO do §0, não violação.** A
formulação sugerida para a spec, se o dono aprovar:

> Neutralidade de tratamento é **mesma exigência probatória**, não mesmo
> número. Quando o tamanho da amostra difere entre filmes, o mesmo número é uma
> exigência diferente — mais frouxa exatamente onde o dado é mais fraco. Um
> limiar em função de `n` é a forma de manter a exigência constante, e ele é
> função do DADO (quantas reviews com texto existem), nunca do sentimento do
> grupo. Dentro de cada filme, a margem continua **idêntica para os três
> buckets**, e nada nesta regra pode favorecer um lado.

**O que a opção (a) — fixo recalibrado — custa ao §0:** nada explicitamente, e
é justamente por isso que ela é a mais fácil de defender e a mais fácil de
defender **errado**. Ela mantém a aparência de neutralidade e mantém a
desigualdade de exigência que a tabela acima mede.

## 4.2 Legibilidade

**VISTO.**

| opção | como se explica ao leitor | veredito |
|---|---|---|
| **(a) fixo** | *"um assunto entra como contraste quando um grupo o cita ao menos 25 pontos percentuais mais que os outros dois."* Uma frase. É o que o produto já diz. | **melhor** |
| **(b) dependente de n** | a frase acima + *"em filmes com menos reviews analisadas, a diferença exigida é maior — amostra menor produz diferenças grandes por acaso."* Duas frases, e a segunda é uma intuição que o leitor leigo **tem** (todo mundo entende que 3 de 5 é menos convincente que 30 de 50). | **aceitável** |
| **(c) critério estatístico** | precisa de "p-valor" ou "distinguível do acaso" e de uma nota sobre permutação. E precisaria explicar por que o mesmo lift dá resultados diferentes em filmes que parecem iguais. | **pior** |

**E (c) tem um custo que não é de legibilidade e que é decisivo:** a permutação
é **Monte Carlo**. §2.5 gastou uma versão inteira (v1.9.15) e um bloco de
documentação para garantir que *"nenhuma decisão de estado depende de
arredondamento de float"* — `Fraction` exato, comparação `>=` exata. Um
p-valor por permutação faz o estado `contraste` **depender de uma semente**. Um
filme na fronteira poderia sair `tematico` numa execução e `valorativo` na
seguinte. **Isso é uma regressão no compromisso central do §2.5**, e é o
argumento que sozinho elimina (c) na forma "recalcular o nulo em produção".

A saída — congelar o valor crítico numa tabela — recupera a exatidão **e**
transforma (c) em (b).

## 4.3 Estabilidade

Duas medições, e a segunda é a que vale.

**MEDIDO — bootstrap da amostra (B = 2.000 por filme), P(o estado troca):**

| regra | P(troca) média | mediana |
|---|---:|---:|
| (a₀) fixo 20pp (hoje) | 0,416 | 0,511 |
| (a) fixo 22,5pp | 0,430 | 0,419 |
| (a) fixo 25pp | **0,384** | 0,376 |
| (b) dependente de n @10% | 0,450 | 0,430 |
| (b) dependente de n @5% | 0,392 | 0,381 |
| (c) estatístico α=0,10 | 0,453 | 0,521 |
| (c) estatístico α=0,05 | 0,438 | 0,481 |

**Esta tabela não distingue nada, e o motivo é conhecido.** Todas as regras
ficam em 0,38–0,45, e o bootstrap do **máximo** é enviesado para cima
exatamente na direção que infla a instabilidade dos filmes `valorativo` —
`ESTUDO_CATALOGO_35.md` §8 registra o mesmo viés ("a comparação `tematico` vs
`valorativo` [é] a menos [confiável] deste estudo"). Como elevar o limiar move
filmes para `valorativo`, o bootstrap penaliza precisamente a intervenção que
está sendo avaliada. **Descartada como critério de decisão.**

**MEDIDO — o evento REAL: quantos dos 35 trocam de estado quando a cobertura vai
de 70,7% para 100%.** Sem simulação: dado observado, duas vezes.

| regra | antes | depois | **trocam** | acordo |
|---|---|---|---:|---:|
| fixo 20pp (hoje) | 18T / 17V | 16T / 19V | **10** | 71% |
| fixo 22,5pp | 15T / 20V | 11T / 24V | 12 | 66% |
| fixo 25pp | 12T / 23V | 7T / 28V | 11 | 69% |
| fixo 27,5pp | 8T / 27V | 6T / 29V | 6 | 83% |
| dep. de n, α=0,10 | 7T / 28V | 9T / 26V | **8** | 77% |
| dep. de n, α=0,05 | 4T / 31V | 6T / 29V | **4** | **89%** |

**Comparação de composição casada** — a única justa, porque uma regra que
classifica menos filmes como `tematico` tem menos a trocar:

| `tematico` sob cobertura 100% | regra | trocas no evento real |
|---:|---|---:|
| 9 | dep. de n, k=130/√n | 8 |
| 9 | dep. de n, k=140/√n | **6** |
| 7 | fixo 25,0pp | 11 |
| 6 | dep. de n, k=144/√n | **4** |
| 6 | fixo 27,5pp | 6 |
| 11 | fixo 22,5pp | 12 |

**VISTO — a leitura, com a ressalva.** O limiar dependente de n é
**consistentemente mais estável em composição casada** (6 trocas contra 11 na
faixa de 7–9 `tematico`), e o mecanismo é claro e não é sorte: o limiar por n
exigia **mais** exatamente nos filmes cujo `n` publicado era pequeno — que são
os que trocaram. **Mas 4 contra 6 contra 11, em 35 filmes e UM evento, não é
uma diferença estatisticamente distinguível.** O que se pode afirmar: a
direção é a esperada pelo mecanismo, e nenhuma medição contradiz. O que **não**
se pode afirmar: que (b) é comprovadamente mais estável que (a).

## 4.4 Complexidade de implementação

**MEDIDO — o que lê `contraste` e o que quebra**, por leitura do código:

- `src/espectro24/eixos.py` — `acima_da_margem(lift, margem_pp)`, `contraste()`,
  `bullets()`, `montar_bloco()`. **A assinatura não conhece `n`.** Ela recebe
  um `Fraction` e um int.
- `src/espectro24/config.py` — `MARGEM_LIFT_PP`.
- `src/espectro24/briefing.py:442-464,587` — `_contraste_do_output`, e o ramo
  `valorativo` do briefing.
- `src/espectro24/veredito.py:341` — **o template ramifica em
  `tematico`/`valorativo`**, com dois blocos de instrução diferentes ao LLM.
- `src/espectro24/render.py`, `cli.py` — exibição e ordem de pipeline.
- `margem_lift_pp` é **carimbado dentro de cada `resultado/<slug>.json`**.

| opção | mudança de código | o que quebra |
|---|---|---|
| **(a) fixo** | uma constante em `config.py` | nada estrutural. Testes que fixam contagens (18/17, os 5 filmes em 20,0pp — este já foi retirado em §2.8) precisam de atualização. **Baixo.** |
| **(b) dep. de n** | `acima_da_margem` passa a receber `n` (ou uma `margem` já resolvida por filme); ripple em `contraste()`, `bullets()`, `montar_bloco()` e nos testes que chamam essas funções direto | assinaturas públicas do módulo. **Médio.** Requer **uma decisão de desenho a mais: qual `n`** — o do bucket da célula, o mínimo dos três, ou a média. (Recomendo o **mínimo**: o lift é uma diferença entre buckets, e a precisão da diferença é governada pelo menor dos denominadores.) |
| **(c) estatístico** | tudo de (b), **mais** um estágio de permutação por filme no pipeline, **mais** semente como parâmetro publicado, **mais** o p-valor no schema | o compromisso de aritmética exata do §2.5 (§4.2 acima). **Alto**, e com regressão conceitual. |

**O que NENHUMA das três quebra:** o template do veredito **não muda de forma**
— ele continua ramificando em `tematico`/`valorativo`, com os mesmos dois
blocos. A interface **não muda de forma** — ela continua tendo dois
comportamentos. **Todas as três opções só mudam QUAIS filmes caem em cada
ramo.** Isso é importante e reduz muito o custo estimado: o trabalho é
**republicação**, não reescrita de estágio.

---
---

# ENTREGA 5 — a consequência de produto, medida

## 5.1 O catálogo sob cada opção viável

**MEDIDO**, sob cobertura 100% (a base sobre a qual qualquer mudança seria
aplicada):

| opção | `tematico` | `valorativo` | muda vs. **base 100%** | muda vs. **publicado hoje** |
|---|---:|---:|---:|---:|
| **nada (20pp, base 100%)** | 16 | 19 | 0 | **10** |
| (a) fixo 22,5pp | 11 | 24 | 5 | 11 |
| (a) fixo 25,0pp | 7 | 28 | 9 | 15 |
| (b) dep. de n, α=0,10 | **9** | 26 | 7 | 13 |
| **(b) dep. de n, α=0,05** | **6** | **29** | 10 | **16** |
| (c) estatístico α=0,05 (≡ (b) nos 29 cheios) | 8 | 27 | 8 | 14 |

**Os filmes `tematico` sob (b) α=0,05 — seis:** `anatomy-of-a-fall`, `barbie`,
`cats-2019`, `cure`, `oppenheimer-2023`, `the-substance`.

**Sob (b) α=0,10 — nove:** os seis acima + `dune-part-two`,
`joker-folie-a-deux`, `the-invite-2026`.

**Quem muda vs. o publicado, sob (b) α=0,05 — 16 filmes:**

| direção | filmes |
|---|---|
| **`tematico` → `valorativo`** (retira uma afirmação nomeada) | `bones-and-all`, `dune-part-two`, `eighth-grade`, `everything-everywhere-all-at-once`, `hereditary`, `interstellar`, `joker-folie-a-deux`, `napoleon-2023`, `perfect-days-2023`, `spider-man-across-the-spider-verse`, `the-hateful-eight`, `the-invite-2026`, `wonka` (13) |
| **`tematico` → sem estado publicado** (piso de `n`) | `obsession-2026` (1) |
| **`valorativo` → `tematico`** (passa a afirmar) | `oppenheimer-2023`, `the-substance` (2) |

**14 das 16 mudanças retiram uma afirmação (13 para `valorativo`, 1 para
"sem estado"); 2 acrescentam.** Os 6 filmes de
`ESTABILIDADE_10_FLIPS.md` que hoje publicam uma causa sem lastro estão **todos**
no primeiro grupo. `obsession-2026` também — e é o único caminho pelo qual ele
sai.

**Os limiares por filme sob (b) α=0,05**, para os 6 que não têm 40/40/40:
`obsession-2026` 64,6pp · `pearl-2022` 27,8pp · `the-godfather` 26,4pp ·
`wonka` 25,5pp · `wicked-2024` 23,7pp · `talk-to-me-2022` 23,1pp. Todos os
outros 29: **22,8pp**, que na grade de 2,5pp é operacionalmente **25,0pp**.

## 5.2 Um catálogo majoritariamente `valorativo` ainda é problema de produto?

**Esta é a pergunta que muda o peso de tudo, e ela tem resposta MEDIDA.**

### O defeito histórico, e se ele voltaria

O defeito que motivou a reescrita das v1.9.21–v1.9.23 era a **mesma frase em 20
de 35 filmes**. Elevar o limiar aumenta o número de `valorativo` — e portanto o
número de filmes que caem no ramo do veredito que tinha o defeito.

**MEDIDO nesta sessão, nos 17 `valorativo` publicados hoje:**

- **17 textos distintos de 17.**
- **Zero frases de mais de 25 caracteres repetidas entre dois filmes
  quaisquer.** Nenhuma.

**O defeito está morto.** A reescrita da v1.9.21 (veredito por LLM sobre
briefing determinístico) e o ataque estrutural da v1.9.22 (padrão sintático de
abertura como desempate na seleção, não no prompt) o neutralizaram. Os textos:

> `avengers-endgame` — *"A divergência central está no paralelo traçado com
> Guerra Infinita, tema mais abordado por ambos os lados…"*
> `im-still-here-2024` — *"O debate gira em torno da crítica social do filme:
> a maioria dos que recomendam exalta a reconstituição da ditadura militar…"*
> `cidade-de-deus` — *"A divisão sobre o filme gira em torno de como a
> narrativa e as questões sociais são trabalhadas…"*

### E há um argumento mais forte, que ainda não estava escrito

**MEDIDO — o veredito `valorativo` não é a afirmação vazia que
`ESTABILIDADE_10_FLIPS.md` descreve.** Lendo `veredito.py:178-188` e o prompt em
`veredito.py:1125`: o ramo `valorativo` **nomeia o `assunto_compartilhado`** — o
eixo que maximiza `min(freq_negativas, freq_positivas)` com piso de 25% dos dois
lados. É uma afirmação de conteúdo, e ela vem de **FREQUÊNCIA**, não de lift.

E frequência é a estatística **estável** do sistema. MEDIDO, no mesmo evento
real (cobertura 70,7% → 100%), nos mesmos 35 filmes:

| o que o ramo do veredito nomeia | estatística | quantos filmes mudam o eixo nomeado |
|---|---|---:|
| ramo `tematico` → o eixo de maior **lift** | máximo sobre 30 células | **16 de 35** |
| ramo `valorativo` → o `assunto_compartilhado` | mínimo entre duas frequências | **8 de 35** |

**Mover um filme de `tematico` para `valorativo` move a afirmação publicada da
estatística MENOS estável do sistema para a MAIS estável — o dobro de
estabilidade, medido no mesmo evento.** (E §2.8 já havia medido que nenhuma
frequência por eixo se move mais que 1,2pp sob 30% mais dado, enquanto 10 filmes
trocam de estado.)

### Veredito da pergunta

**VISTO, com base medida.** Um catálogo majoritariamente `valorativo` **não é
mais um problema de produto** — é o oposto. Três razões:

1. o defeito de repetição está medido como morto (17/17 distintos, zero frases
   compartilhadas);
2. o ramo `valorativo` faz uma afirmação de conteúdo real, e ela repousa sobre a
   estatística mais estável do sistema (8/35 contra 16/35 de instabilidade);
3. o erro que ele produz quando erra é o **inofensivo** — subafirmar —,
   enquanto o erro do ramo `tematico` é publicar uma causa que não existe. É a
   assimetria que `ESTABILIDADE_10_FLIPS.md` já isolou.

**Consequência para a decisão: o preço de elevar o limiar caiu muito desde que a
margem de 20pp foi escolhida.** O trade-off registrado em §2.5 é *"pureza de
lista contra cobertura"*, e ele foi escolhido quando `valorativo` era o estado
fraco. Ele não é mais. **A cobertura vale menos do que valia, e a pureza vale o
mesmo.** O ponto de equilíbrio se move para cima, e a frase de §2.5 que fixa
"cerca de um terço do catálogo" como critério de sucesso deve ser **aposentada,
não satisfeita** — ela é um alvo de cobertura de quando cobertura era o bem
escasso.

---
---

# ENTREGA 6 — recomendação

## A recomendação

> **MUDAR. Opção (b): limiar dependente de `n`, calibrado a α = 0,05, congelado
> como LEI — não recalculado em produção.**
>
> **`limiar(n) = 144,4 / √n` pontos percentuais**, com `n` = **o menor dos três
> buckets** do filme, comparado em `Fraction` exato como hoje.
>
> A constante 144,4 é derivada do nulo desta sessão (média de `q95 · √n` sobre
> n ∈ {20, 30, 40, 50, 100}) e vira **um número congelado na spec**, no mesmo
> estatuto do `taxonomia_id`: aritmética exata, zero Monte Carlo em produção,
> zero dependência de semente.
>
> Catálogo resultante: **6 `tematico` / 28 `valorativo` / 1 sem estado**
> (`obsession-2026`, pelo piso). **6 + 28 + 1 = 35.**

**MEDIDO — a taxa de falso contraste que essa lei realiza**, sobre o nulo dos 29
filmes cheios, por `n`:

| n | limiar | taxa realizada |
|---:|---:|---:|
| 10 | 45,7pp | 0,060 |
| 15 | 37,3pp | 0,061 |
| 20 | 32,3pp | 0,049 |
| 25 | 28,9pp | 0,040 |
| 30 | 26,4pp | 0,075 |
| 35 | 24,4pp | 0,053 |
| **40** | **22,8pp** | **0,037** |
| 50 | 20,4pp | 0,040 |
| 100 | 14,4pp | 0,047 |

Entre **3,7% e 7,5%**, média ≈ 5%. A oscilação em torno do alvo é a
**quantização** (§3.1), não erro da lei: em `n = 30` o lift só assume múltiplos
de 3,33pp e nenhum limiar acerta 5% exatamente.

**A leitura prática, que evita uma confusão:** para os 29 filmes com 40/40/40, a
lei dá 22,8pp — e como o lift em n=40 só assume múltiplos de 2,5pp, **o corte
operante nesses filmes é 25,0pp**. A lei não está fazendo nada de mais fino que
um limiar fixo de 25pp ali. Ela existe pelos outros 6 (§4.0), onde os limiares
são `talk-to-me-2022` 23,1 · `wicked-2024` 23,7 · `wonka` 25,5 ·
`the-godfather` 26,4 · `pearl-2022` 27,8 · `obsession-2026` **64,6**.

**E um piso, que é a regra a mais:** `n < 10` no menor bucket → **o estado
`contraste` não é publicado** (abaixo).

### A lei preserva a aritmética exata do §2.5 — e a forma importa

`144,4 / √n` tem uma raiz irracional, e comparar `lift >= 144,4/√n` em ponto
flutuante **jogaria fora** exatamente a garantia que a v1.9.15 comprou a um
custo alto (*"nenhuma decisão de estado depende de arredondamento de float"*).
Cinco filmes já caíram fora da margem uma vez por causa disso.

**A forma equivalente é exata.** Para `lift > 0`:

```
lift  >=  (1444/1000) / √n      ⟺      lift² · n  >=  (1444/1000)²
                                                   =  Fraction(2085136, 1000000)
```

(`lift` é uma fração de 0 a 1, não pontos percentuais — 144,4pp de constante é
1,444 nessa escala, e em n = 40 a lei dá 1,444/√40 = 0,2283, isto é 22,83pp.)

`lift` já é `Fraction`, `n` é `int`: `lift * lift * n >= Fraction(2085136,
1000000)` é uma comparação de racionais **exata**, sem raiz, sem float, sem
tabela de arredondamento. Elevar ao quadrado é monotônico no ramo positivo, e
`lift <= 0` reprova por inspeção antes da conta.

**Este parágrafo é metade do argumento contra a opção (c)** (§4.2): a lei por
`n` é estatística na origem e **exata na operação**; um p-valor por permutação
em produção seria estatístico na origem e **Monte Carlo na operação**.

**Conferido nesta sessão:** a comparação exata em `Fraction` devolve
**exatamente os mesmos 6 filmes** que a versão em ponto flutuante usada nas
tabelas acima. Nenhum filme do catálogo está tão perto da fronteira que a forma
da conta decida por ele — mas isso é uma propriedade do catálogo de hoje, não
uma garantia, e é por isso que a forma exata é a que deve ir para o código.

## Por quê, em quatro razões

1. **É a única opção que resolve `obsession-2026`.** MEDIDO: nenhum limiar fixo
   até 40pp o move, e a probabilidade de o contraste dele ser ruído é **0,976**.
   Um produto que publica `tematico` num filme com 5, 6 e 8 reviews por bucket
   está publicando um sorteio como fato. Qualquer opção que deixe esse caso de
   pé está incompleta, e é um caso real do catálogo, não hipotético.
2. **Ela é a que o §0 pede, pelo argumento que o próprio §0 já usou uma vez.**
   Limiar constante ≠ exigência constante (§4.1, com a tabela de percentis). O
   paralelo com a v1.9.30 é estrutural, não retórico.
3. **O custo dela sobre (a) é quase zero, porque nos 29 filmes cheios ela É
   (a).** MEDIDO: o valor crítico varia 0,12pp entre eles. A complexidade extra
   compra o tratamento correto de 6 filmes e não custa nada nos outros 29.
4. **α = 0,05 e não 0,10 por causa da assimetria de dano**, já estabelecida em
   `ESTABILIDADE_10_FLIPS.md`: `tematico → valorativo` errado é subafirmar
   (inofensivo); `valorativo → tematico` errado é publicar uma causa falsa em
   prosa categórica. Quando os dois erros custam coisas diferentes, o nível se
   escolhe pelo mais caro. E §5.2 mostra que o lado conservador não custa mais
   nada de produto.

**O que a recomendação NÃO afirma.** Ela não afirma que (b) é comprovadamente
mais estável que (a) — §4.3 mediu 4 trocas contra 11 em composição casada, e
essa diferença, em 35 filmes e um evento, **não é estatisticamente
distinguível**. A recomendação repousa nas razões 1–4, não na estabilidade
medida.

## A regra a mais, e ela é obrigatória

**`n < 10` no menor bucket: o estado `contraste` NÃO é publicado.** Não é
`valorativo` — é **ausente**, no mesmo estatuto do bloco `eixos` inteiro quando
não há classificação (`montar_bloco` devolve `None`, e "chave ausente distingue
filme não classificado de classificado e sem eixo"). Publicar `valorativo` em
`obsession-2026` seria trocar uma afirmação sem lastro por outra: a medição
naquele n não distingue os dois estados, e dizer "os grupos falam das mesmas
coisas" seria tão sem base quanto dizer o contrário. **Um filme só entra em
`obsession-2026`** hoje.

## O que precisa acontecer depois, e o custo

| # | ação | escopo | custo |
|---|---|---|---|
| 1 | `config.py` / `eixos.py`: `MARGEM_LIFT_PP` vira a lei por `n`, na forma quadrada que preserva a exatidão (abaixo). `acima_da_margem`, `contraste`, `bullets`, `montar_bloco` passam a receber `n`. | ~5 funções, um módulo | **meio dia**, sem risco de dado |
| 2 | Testes que fixam 18/17 e contagens derivadas | `tests/test_eixos.py` e vizinhos | incluído em (1) |
| 3 | Terceiro caso: `contraste` ausente quando `n < 10`. Briefing e veredito precisam de um caminho para "sem estado" | `briefing.py`, `veredito.py`, `render.py`, frontend | **o item mais caro** — é o único que muda **forma**, não só conteúdo. Afeta 1 filme, mas é um ramo novo em 4 lugares |
| 4 | **Republicar 16 filmes** — regerar o veredito, que é o único estágio que lê `contraste` | 16 × ~4 chamadas de `gemini-3.7-flash`, ~4k tokens de entrada cada | **~64 chamadas, ~270k tokens de entrada**. Menos da metade de uma regeneração completa dos 35, que o projeto já fez três vezes (v1.9.21/22/23). A rotulagem [D3] **não** precisa rodar de novo (não depende da margem) |
| 5 | Spec: §2.5 reescrita (tabela de limiar por n, o nulo do máximo, a aposentadoria do critério "cerca de um terço"); §0 ganha o parágrafo do §4.1 acima; §2.9 fecha | documentação | meio dia |

**O item 3 é o que o dono deve pesar com mais cuidado**, porque é o único que
adiciona um ramo. Se ele for considerado caro demais, existe uma versão reduzida
defensável: manter `obsession-2026` como `valorativo` e **registrar por escrito
na spec que aquele estado específico não é uma medição** — pior que a versão
completa, mas honesto, e adiável.

## Ordem de execução, e ela importa

**Não republicar os 10 filmes de §2.9 antes de decidir o limiar** — mas a razão
registrada em §2.9 é **mais fraca do que parece**, e vale corrigir isso aqui.

§2.9 diz que republicar agora "seria trabalho refeito se a margem mudar". **MEDIDO:
dos 10 filmes de §2.9, apenas 2 (`dune-2021` e `wicked-2024`) teriam estado
diferente sob a recomendação em relação ao que a republicação de §2.9 lhes
daria.** Os outros 8 receberiam, das duas vezes, o mesmo estado.

A contabilidade real dos dois caminhos:

| caminho | regenerações de veredito |
|---|---:|
| republicar os 10 agora, depois adotar (b) | 10 + 10 = **20** |
| decidir o limiar primeiro, republicar uma vez | **16** |

**O argumento de esperar continua válido — 20 contra 16 —, mas é um argumento de
4 regenerações, não do trabalho inteiro.** A razão forte para esperar é outra, e
é a que a Entrega 6 dá: republicar sob 20pp coloca no ar 16 estados com taxa de
falso contraste de 24–38%, e depois teria de tirar. Se o dono decidir **não**
mudar o limiar, a republicação de §2.9 deve acontecer imediatamente — ela é uma
melhora inequívoca sobre o publicado hoje, independentemente da margem.

## Se a decisão for NÃO MUDAR

Então o que passa a ser registrado como limitação conhecida, com estes números:

1. **A taxa de falso contraste do catálogo publicado é de 24% a 38%** — entre 4
   e 6 dos 16 `tematico` são ruído (§2.4).
2. **Só 6 dos 35 filmes têm contraste distinguível do acaso a α = 0,05, e só 1
   sobrevive a correção para as 35 comparações** (§2.4).
3. **O catálogo publicado foi decidido com `n` mediano de 28 por bucket, não
   40**, e nesse regime a taxa de falso contraste a 20pp é **0,373** (§Corr. 3).
4. **Os 6 filmes cujo veredito nomeia uma causa que o dado completo não
   sustenta tinham 63% de probabilidade média de aquele contraste ser ruído**
   (§2.3). Esta é a frase que precisa estar escrita, porque ela é a que o
   produto está publicando.
5. **`obsession-2026` publica `tematico` com P(ruído) = 0,976.** O estado dele
   não carrega informação.

**Como a interface comunicaria isso, se nada mudar** (VISTO): o único lugar
honesto é junto do próprio estado, e a forma mais barata que não reabre o
veredito é uma **linha de base** — não de magnitude. O precedente existe e é
exato: a v1.9.22 proibiu hedge de **magnitude** ("relatos pontuais apontam que a
maioria…") mas manteve explicitamente a exceção para hedge que **ancora na
base** ("analisadas", "disponíveis", "coletadas"), e criou um teste nomeado para
protegê-la. Uma linha como *"medido em N reviews analisadas por grupo"* ao lado
do estado cabe dentro dessa doutrina sem tocar no texto do veredito. **Não
resolve o problema** — as seis páginas continuam nomeando a causa em prosa
categórica —, mas é o máximo que se consegue sem reabrir o estágio fechado.

---
---

# A quarta opção — parar de publicar um binário

O dono pediu leitura, não recomendação. Aqui está.

## É viável sem reabrir o veredito?

**Depende de qual das duas coisas se chama "quarta opção", e elas têm respostas
opostas.**

**Versão A — o veredito passa a expressar a confiança em prosa.** *"Quem não
recomenda talvez rejeite pelo ritmo"*, ou um terceiro ramo para o caso
indeciso. **NÃO é viável sem reabrir o veredito**, por definição: o template
ramifica em `tematico`/`valorativo` (`veredito.py:341`), e um terceiro estado é
um terceiro bloco de instrução, um terceiro conjunto de validações de qualidade
e um terceiro padrão de abertura entrando na métrica anti-repetição da v1.9.22.
**E ela colide com uma decisão já medida:** a v1.9.22 estabeleceu que *"deflação
mente sobre o dado exatamente como inflação"* e proibiu hedge de magnitude. Um
veredito que diz "talvez" sobre um achado que o código decidiu ser verdadeiro é
exatamente esse hedge. Reabrir isso é reabrir uma medição, não uma preferência.

**Versão B — o binário continua governando o veredito; a CONFIANÇA é publicada
ao lado, como dado.** Um campo novo no bloco `eixos` (o percentil no nulo, ou o
`n` efetivo e o limiar aplicado) e uma linha na interface. **É viável sem tocar
no veredito**, e cabe no estatuto aditivo que o projeto já usa três vezes
(ficha §3[F], distribuição §3[G], `fonte_classificacao`): a chave só existe
quando há algo a declarar, e a ausência dela **é** a declaração.

## É melhor ou pior que recalibrar o limiar?

**VISTO: as duas não são alternativas — são camadas diferentes, e recalibrar é a
que não pode ser pulada.**

O argumento é este. A Versão B publica a incerteza **do estado**. Mas o dano
concreto medido nesta sessão não está no estado — está na **prosa**. Os seis
vereditos de `ESTABILIDADE_10_FLIPS.md` dizem *"cerca de metade dos que não
recomendam rejeita a produção pelo andamento arrastado"*. Essa frase nomeia uma
causa. Uma linha ao lado dizendo "confiança baixa" não a desfaz — o leitor
médio lê a frase e retém a causa, e a nota de confiança é a última coisa que ele
processa e a primeira que ele esquece. **Publicar incerteza sobre uma afirmação
que não deveria ter sido feita não é uma correção; é uma nota de rodapé numa
afirmação errada.**

Recalibrar o limiar age no lugar certo: impede que a frase seja escrita.

**Portanto: recalibrar é necessário; publicar a confiança é um bom complemento e
não substitui.** A Versão B **não** é melhor que as três opções, e a Versão A é
pior que todas (custa mais e colide com uma medição existente).

**A recomendação da Entrega 6 não muda.** Mas se o dono quiser as duas, a ordem
é: recalibrar primeiro (o estado passa a ser majoritariamente confiável), e
**depois** avaliar publicar a confiança — que, num catálogo já recalibrado, tem
muito menos trabalho a fazer, e é justamente por isso que é um bom segundo
passo e um péssimo primeiro.

---
---

# O que este estudo NÃO responde

- **Se a classificação por eixo está certa.** O nulo toma o conjunto de eixos de
  cada review como dado. Erro de classificação não aparece aqui —
  `ESTABILIDADE_AGREGADA.md` mede 26,5% de reprodutibilidade individual antes da
  votação de 3, e essa é uma fonte de instabilidade **inteiramente separada** e
  não somada em lugar nenhum deste relatório. **MEDIDO de lado nesta sessão, e é
  um sinal do tamanho dela:** 5 dos 35 filmes trocam de estado apenas em função
  de o passe verificador de `impacto_emocional` ter rodado ou não
  (`dune-2021`, `eighth-grade`, `im-still-here-2024`, `napoleon-2023`,
  `the-godfather`). Isso não é margem — é classificação.
- **Se um contraste significativo é interessante.** Significância não é tamanho
  de efeito nem relevância editorial. Um contraste de 25pp em `livre` não vira
  bullet, e um em `impacto_emocional` pode ser trivialmente verdadeiro.
- **Os pontos de n = 50 e 100.** São extrapolação com a distribuição empírica
  congelada (a mesma declarada em MEDICAO §2.2). Eles dizem quanto a **variância
  amostral** encolheria; não dizem se a frequência observada se moveria.
- **Nada sobre filmes fora dos 35.** A calibração do limiar sobre o mesmo
  catálogo que ele vai julgar é, formalmente, um uso duplo do dado. Com 35 filmes
  não há como separar treino de teste sem perder tudo. **Registrar como
  limitação:** a taxa de falso contraste projetada é uma estimativa in-sample.
- **Se `n` deveria ser o mínimo, a média ou o do bucket da célula.** Recomendei o
  mínimo com um argumento (§4.4), não com uma medição.

---

## Reprodução

Os scripts desta sessão estão no scratchpad da sessão, não no repositório —
nenhum arquivo do projeto foi criado ou alterado além destes dois markdowns.
Semente 24 em toda parte; B = 10.000 no nulo por filme, 4.000 nas curvas por n,
2.000 no bootstrap. A população se reconstrói com
`espectro24.pipeline.amostra_do_bruto(slug, coleta=resultado/<slug>.json[coleta])`
interseccionada com `resultado/votacao-3/consenso_verificado.jsonl`, e a
validação de três pontos do topo deste documento é o teste de que ela está
certa.
