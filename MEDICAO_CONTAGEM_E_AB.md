# Medição — a contagem por eixo como número publicável, e o A/B da passada única

**Entregas 1 e 3.** Sessão de desenho e medição. Nenhum arquivo de `resultado/`
foi escrito, nenhum filme regerado, nenhum estágio do pipeline executado, a
taxonomia de produção e o `taxonomia_id` intactos, frontend intocado. A única
chamada de LLM desta sessão é a da Entrega 3, sobre 120 reviews de amostra
registrada. O desenho da classificação nova está no documento irmão,
`DESENHO_CLASSIFICACAO_V2.md`.

**Data:** 2026-08-28 · **`taxonomia_id`:** `ebab2667de74` ·
**classificação de referência:** `resultado/votacao-3/consenso_verificado.jsonl`
· **modelo:** `deepseek-v4-flash` (o mesmo da classificação de produção).

---

# ENTREGA 1 — a contagem por eixo serve como número publicável?

## O que está sendo perguntado

Hoje a largura da barra de cada bullet é
`mencoes_aproximadas / n_reviews_analisadas`
([frontend/js/filme.js:1370](frontend/js/filme.js:1370)), e
`mencoes_aproximadas` é **decidido pelo LLM** — está no schema pedido ao modelo
em [synthesize.py:116](src/espectro24/synthesize.py:116), e
[`_construir_temas`](src/espectro24/synthesize.py:962) só aplica
`max(0, min(bruto, n))`, que é clamp de sanidade e não medição. Isso contradiz
o princípio que a spec repete desde a v1.1.1 — *"o LLM não decide número nem
rótulo numérico; o código é a autoridade"* (§3[D2], §7208 do changelog).

*(Registro: a própria SPEC já listava isto como pendência em aberto — "ground
truth manual das contagens de `mencoes_aproximadas` — na fila do usuário",
seção "Pendência de verificação contínua". O estudo dos 35 filmes é essa
aferição, e esta entrega é a avaliação da correção candidata.)*

A candidata: trocar por `mencoes / de_n` do eixo correspondente, que vem de
`consenso_verificado.jsonl`, é somado em `Counter` por
[eixos.py](src/espectro24/eixos.py), é auditável e já é o número que decide o
lift e o estado `contraste`.

**Dois cenários foram medidos**, porque a troca mexe no numerador *e* no
denominador:

| | numerador | denominador |
|---|---|---|
| **hoje** | `mencoes_aproximadas` (LLM) | `n_reviews_analisadas` (~40) |
| **cenário A** | `mencoes` do eixo (código) | `de_n`, reviews **classificadas** (~27) |
| **cenário B** | `mencoes` do eixo (código) | `n_reviews_analisadas` (~40) |

O cenário B é listado só para ser descartado: contar sobre a população
classificada e dividir pela analisada é exatamente o defeito de "dois quarentas
diferentes" que a v1.9.15 corrigiu (§[D3]). **Todo número abaixo é do cenário A.**

**Limiares registrados antes de olhar o resultado:** barra "alterada de forma
visível" = |Δ| ≥ 10pp; "muito alterada" = |Δ| ≥ 25pp. Razão: a barra é uma
largura percentual, e 10pp é a menor mudança perceptível num elemento desse
tamanho.

Universo: **629 bullets**, dos quais 619 têm eixo com linha em `eixos.linhas[]`
(os 10 restantes são `livre`, que não tem linha e portanto não tem contagem —
já é um caso sem número, e continuaria sem).

---

## 1. A diferença entre os dois numeradores

| | valor |
|---|---|
| Δ (contagem de eixo − `mencoes_aproximadas`) | média **+0,3** · mediana **0** |
| amplitude | −25 a +27 |
| eixo **maior** que o LLM | 287 bullets (46%) |
| **iguais** | 39 (6%) |
| eixo **menor** que o LLM | 293 (47%) |

Histograma do Δ (bins de 5): `−25:3 · −20:9 · −15:25 · −10:70 · −5:186 · 0:175 · +5:82 · +10:40 · +15:23 · +20:4 · +25:2`

**Leitura.** Não há viés sistemático: o LLM não infla nem desinfla em relação à
contagem de eixo — a mediana da diferença é exatamente zero e os dois lados são
quase simétricos (46% contra 47%). Isso pode parecer um endosso ao número
atual, e não é: **os dois números não medem a mesma coisa**, e a simetria é
coincidência de duas medidas diferentes sobre populações diferentes. O tema é
um **subconjunto** do eixo ("Ritmo arrastado e tédio" é um dos assuntos dentro
de `ritmo`), então a contagem de eixo deveria ser sempre ≥ à do tema se as duas
contassem a mesma população. Ela é menor em 47% dos casos porque a população
dela é menor (~27 contra ~40).

## 2. Quantos bullets teriam a barra alterada, e em que direção

| limiar | bullets | % | sobem | descem |
|---|---:|---:|---:|---:|
| ≥ 10pp (visível) | **411** | 66,4% | 334 | 77 |
| ≥ 25pp (muito) | **182** | 29,4% | 162 | 20 |
| ≥ 40pp | 73 | 11,8% | 66 | 7 |

Δ da barra: **média +12,4pp · mediana +11,8pp · min −51,2pp · max +71,7pp.**

A distribuição inteira desloca para cima, porque o denominador encolhe:

| | média | mediana | p10 | p90 |
|---|---:|---:|---:|---:|
| hoje | 27,9% | 25,0% | 15,0% | 45,0% |
| cenário A | **40,3%** | **39,3%** | 16,7% | **68,4%** |

Efeitos colaterais na leitura da barra:
- barras ≥ 80% ("quase todo o grupo"): **2 → 10** bullets;
- barras ≤ 10%: 8 → 20;
- amplitude das barras **dentro** de um mesmo bucket: mediana **28pp → 42pp**;
- **a ordem dos bullets mudaria em 103 dos 105 buckets (98%)** — §D.3 ordena
  os temas por `mencoes_aproximadas` decrescente, e trocar o número reordena
  quase tudo.

**As maiores subidas** (todas em `roteiro_estrutura`, o eixo saturado):

| filme / bucket | tema | hoje | cenário A |
|---|---|---:|---:|
| `shutter-island` neg | *Excesso de flashbacks e simbolismo* | 12% (5/40) | **84%** (32/38) |
| `joker-folie-a-deux` med | *Desconstrução do personagem* | 15% (6/40) | **85%** (22/26) |
| `shutter-island` neg | *Confuso e difícil de acompanhar* | 18% (7/40) | **84%** (32/38) |
| `eighth-grade` pos | *Final emocionante e esperançoso* | 15% (6/40) | 81% (22/27) |
| `anatomy-of-a-fall` neg | *Personagens pouco cativantes* | 18% (7/40) | 82% (28/34) |

**As maiores quedas** (todas em `tom_atmosfera` e `som_trilha`):

| filme / bucket | tema | hoje | cenário A |
|---|---|---:|---:|
| `friday-the-13th-2009` pos | *Jason mais assustador e brutal* | 75% (30/40) | 24% (5/21) |
| `obsession-2026` med | *Potencial promissor do cineasta* | 67% (4/6) | 17% (1/6) |
| `joker-folie-a-deux` neg | *Números musicais deslocados* | 75% (30/40) | 28% (9/32) |
| `avengers-endgame` pos | *Batalha final épica e fan service* | 45% (18/40) | **0%** (0/18) |

## 3. A colisão — bullets que perdem barra própria

| | valor |
|---|---|
| bullets que passariam a repetir a barra de um vizinho | **175 de 629 (28%)** |
| buckets afetados | **70 de 105 (67%)** |
| pares (eixo × bucket) em colisão | 79 |

Distribuição: `roteiro_estrutura` ×2 em 34 buckets, ×3 em 12, **×4 em 2**;
`critica_social` ×2 em 11 e ×3 em 1; `direcao_imagem` ×2 em 6;
`impacto_emocional` ×2 em 5; `tom_atmosfera` e `ritmo` ×2 em 3 cada;
`atuacao` e `livre` ×2 em 1 cada.

**O pior caso — quatro bullets, uma barra:**

`joker-folie-a-deux` / negativas, todos `roteiro_estrutura`, **todos com barra
de 53% (17/32)**:
- *Roteiro fraco e sem desenvolvimento*
- *Descaracterização do Arthur Fleck*
- *Personagem Harley Quinn subutilizada*
- *Desfecho insatisfatório*

`cure` / negativas, todos `roteiro_estrutura`, **todos com barra de 68% (27/40)**:
- *Falta de clímax ou recompensa*
- *Personagens pouco cativantes*
- *Enredo confuso e sem objetividade*
- *Diálogos fracos e repetitivos*

Mais 13 buckets com três bullets numa barra só, entre eles `shutter-island`/neg
(três a 84%) e `anatomy-of-a-fall`/neg (três a 82%).

**Leitura.** Quatro barras idênticas empilhadas dizem ao leitor que os quatro
assuntos têm o mesmo peso, e não têm — o que têm em comum é o rótulo de eixo
que [D3] lhes deu. Isso é pior que o número errado de hoje: hoje a barra erra a
quantidade; no cenário A ela **afirma uma equivalência que o dado não sustenta**,
e afirma isso em 28% dos bullets do catálogo.

## 4. A contradição dos 5% desaparece? **Sim — e cria uma pior**

| | hoje | cenário A |
|---|---:|---:|
| bullets com frequência do tema acima da do próprio eixo em >20pp | **30 (4,8%)** | **0 (0%)** |

**Confirmado, e por construção**: no cenário A a barra *é* a frequência do
eixo, então a diferença entre as duas é zero em 100% dos bullets. O caso que o
estudo destacou — `avengers-endgame`/positivas, *"Batalha final épica e fan
service"*, barra de 45% num eixo (`tom_atmosfera`) de contagem zero — deixa de
ser contraditório.

**Mas o que ele vira é um bullet com barra de 0%.** São dois no catálogo:

| filme / bucket | tema | eixo | cenário A |
|---|---|---|---|
| `avengers-endgame` pos | *Batalha final épica e fan service* | `tom_atmosfera` | **0/18** |
| `obsession-2026` neg | *Potencial não realizado* | `expectativa` | **0/5** |

Um bullet publicado com barra vazia é uma afirmação nova e falsa: *"nenhuma
review deste grupo mencionou isto"* — quando o que aconteceu foi [D3] pôr o
tema numa linha cuja contagem é zero. A contradição não some; ela troca de
lugar, de "dois números que se desmentem" para "um número que desmente o texto
ao lado dele".

## 5. O denominador, e o que ele faz com a barra

| | valor |
|---|---|
| soma `n_analisadas` | 4.056 |
| soma `n_classificadas` | 2.866 |
| **cobertura** | **70,7%** |
| denominador por bucket (classificadas) | média 27,4 · mediana 28 · **min 5** · max 40 |
| quantum da barra (1 review) | 2,5pp hoje → **3,6pp** (mediana) no cenário A |

**Qual denominador seria publicado: o das classificadas.** Não há alternativa
honesta — o numerador é contado sobre elas, e publicar `de_n` ao lado é a
mesma regra de "frequência sempre com denominador visível" que a v1.9.15
impôs. O cenário B (contar sobre 27, dividir por 40) reintroduz literalmente o
defeito dos "dois quarentas".

**O que isso custa:**

1. **A cobertura é desigual, e a desigualdade vira ruído visual entre filmes.**
   8 dos 35 estão abaixo de 50%: `perfect-days-2023` 39%, `hereditary` 42%,
   `the-substance` 42%, `everything-everywhere-all-at-once` 43%, `aftersun` 44%,
   `dune-2021` 44%, `bones-and-all` 48%, `avengers-endgame` 48%. Só quatro estão
   em 100% (`cure`, `cidade-de-deus`, `the-invite-2026` — os três estendidos na
   v1.9.15 — e `obsession-2026`, que tem 19 reviews no total). Dois filmes lado a
   lado no catálogo teriam barras calculadas sobre populações de tamanhos muito
   diferentes, sem nada na tela dizendo isso.
2. **O quantum cresce, e em alguns buckets explode.** 8 buckets ficariam com
   denominador abaixo de 15 — `obsession-2026`/negativas com **n=5, quantum de
   20pp**: uma review muda a barra em um quinto da largura. `obsession-2026`
   medianas n=6 (16,7pp), positivas n=8 (12,5pp), `perfect-days-2023`/medianas
   n=12, `hereditary`/medianas n=13, `dune-2021`/medianas n=13 e positivas n=14,
   `aftersun`/medianas n=14.

---

## A verificação que decide: a contagem de eixo conserta os casos ruins?

O estudo dos 35 achou 5 bullets de generalização excessiva e mediu a contagem à
mão em cada um. Confrontando as três contagens:

| filme / bucket / tema | eixo | **à mão** | hoje (LLM) | cenário A |
|---|---|---:|---:|---:|
| `wonka` neg — *Fotografia e efeitos visuais criticados* | `direcao_imagem` | **1**/32 | 6/32 | 3/32 |
| `talk-to-me-2022` neg — *Diálogos e tom juvenil artificiais* | `tom_atmosfera` | **2**/40 | 5/40 | **8**/33 |
| `napoleon-2023` med — *Batalhas visualmente impressionantes* | `direcao_imagem` | **13**/40 | 15/40 | 13/26 |
| `interstellar` pos — *Fotografia e efeitos visuais deslumbrantes* | `direcao_imagem` | **8**/40 | 11/40 | 9/29 |
| `cats-2019` neg — *Experiência de visualização desconfortável* | `impacto_emocional` | **8**/40 | 10/40 | **17**/34 |

**Em 2 dos 5 a contagem de eixo é PIOR que a do LLM.** `talk-to-me` sai de 2,5×
para 4× o valor real; `cats-2019` sai de 1,25× para 2,1×. E no único caso em que
melhora muito (`wonka`, de 6× para 3×), continua três vezes acima. Em
`napoleon` a contagem fica exata (13 = 13) mas a **fração** infla de 37,5% para
50%, porque o denominador caiu de 40 para 26 — o que agrava exatamente o
problema que o estudo apontou naquele bullet (o exemplo publicado diz "para a
maioria dos espectadores deste grupo").

**A causa é conceitual, não de calibração: o eixo é um superconjunto do tema.**
`tom_atmosfera` conta as 8 reviews que falam de clima em `talk-to-me`; o bullet
fala de *diálogos e gírias juvenis*, que são 2 delas. Substituir o número do
tema pelo número do eixo troca uma **estimativa mole** por um **erro de
categoria duro** — e o erro duro tem a propriedade ruim de parecer confiável,
porque é somado em código.

---

## Recomendação da Entrega 1

**Não adotar a contagem de eixo como número da barra.** Ela resolve o problema
de governança (o número passa a ser do código) e resolve a contradição dos 5%,
mas cobra três preços que somados são maiores que o problema que corrige:

1. muda a barra de forma visível em **66% dos bullets** e a ordem de leitura em
   **98% dos buckets**, sem que exista evidência de que a barra nova esteja mais
   perto da verdade — e nos 5 casos em que existe medição à mão, ela está mais
   longe em 2;
2. faz **28% dos bullets** perderem barra própria, publicando uma equivalência
   falsa entre até quatro assuntos distintos;
3. publica dois bullets com barra **zero** e passa a depender de um denominador
   que hoje cobre 70,7% da amostra, desigualmente, com 8 buckets abaixo de 15
   reviews.

**O que o dado sustenta.** O problema real não é *qual das duas contagens usar*
— é que **nenhuma das duas conta o tema**. A contagem de eixo conta o eixo; a
do LLM conta o tema mas não é auditável. A saída que fecha o princípio do §0 sem
os três preços acima é **contar o tema em código**, o que exige que a
classificação carregue granularidade de tema — que é precisamente o que a
Entrega 2 desenha. Isto é uma dependência, não um adiamento: a barra fiel é um
subproduto da classificação nova, não uma entrega separada.

**Duas correções que independem dessa decisão e são baratas:**

- **Publicar a contagem de eixo AO LADO, não no lugar.** Ela é o número que
  decide o contraste e hoje é invisível ao leitor. A linha do eixo já existe no
  JSON (`eixos.linhas[].por_bucket[].mencoes/de_n`).
- **Tratar os 30 bullets da contradição dos 5% como sintoma de rotulagem [D3],
  não de contagem.** `avengers-endgame`/positivas com tema de 45% num eixo de
  0% não é erro do LLM da síntese — é o tema estar na linha errada.

---
---

# ENTREGA 3 — o A/B da passada única

## Hipótese

*"Uma única passada multi-label sobre a review mantém qualidade comparável a
classificações independentes?"* — a preocupação é que pedir muitas decisões
simultâneas faça o modelo sacrificar precisão em alguma delas, **em silêncio**.

## Desenho

**Braço A** — 1 chamada por review, devolvendo eixo + polaridade por eixo +
feelings.
**Braço B** — 3 chamadas por review, uma decisão cada: (B1) eixo, (B2)
polaridade recebendo os eixos de B1, (B3) feelings.

**Controle central: as definições de eixo são byte-idênticas nos dois braços.**
`SYSTEM_B1` é literalmente `espectro24.taxonomia.SYSTEM`, o prompt de produção
(verificado por asserção no build dos prompts); o braço A é esse mesmo texto com
o rodapé de formato substituído. A única variável do experimento é a estrutura
de passada. As definições de polaridade e de feelings também são as mesmas
strings nos dois braços.

Modelo `deepseek-v4-flash` nos dois (o de `MODELO_POR_ESTAGIO["classificacao"]`),
`thinking: disabled`, `json_mode`, mesma concorrência.

**Passada ÚNICA nos dois braços — sem votação de 3.** O A/B testa estrutura de
passada, não votação; ligar a votação mediria as duas coisas somadas.
Consequência a carregar na leitura: a referência (`consenso_verificado`) é
produto de 3 votos + verificador, então o valor **absoluto** de concordância de
qualquer braço é deprimido por construção. **A comparação que vale é A-contra-
referência versus B-contra-referência.**

### Critério de amostragem — registrado antes de qualquer chamada

Universo: as 2.866 reviews que estão ao mesmo tempo na seleção de produção e no
`consenso_verificado.jsonl` (as únicas com referência de eixo).

- **R1.** N = 120.
- **R2.** Estratificação por **bucket** (40/40/40) × **faixa de comprimento**
  (≤200 / 201–500 / 501–1200 / >1200 chars), 10 por célula. Razão: o
  comprimento é a variável com efeito medido mais forte sobre o erro de
  classificação (recall 0,35 em ≤200 chars contra 0,87–0,93 acima —
  `CLASSIFICACAO_CONSOLIDADO.md` §3). Estratificar por ele é o que impede o A/B
  de medir comprimento em vez de estrutura.
- **R3.** No máximo 6 reviews por filme.
- **R4.** Empate por PRNG semente 24 sobre a lista ordenada por
  `(slug, bucket, id)`. Nada escolhido a dedo.
- **R5.** Célula sem candidatos cede a vaga, com registro. **Não foi acionada.**

Amostra obtida: 120 reviews · 40/40/40 por bucket · 30 por faixa · **32 filmes
distintos**, máximo 6 por filme · comprimento mediano 505 chars (152 a 6.999) ·
3,65 eixos de referência por review.

Execução: 480 chamadas, 60 s de relógio, **0 falhas** nos dois braços.

---

## Resultado principal — EIXO

Contra `consenso_verificado`:

| braço | precisão | recall | F1 | conjunto exato | tp/fp/fn |
|---|---:|---:|---:|---:|---|
| **A** (1 chamada) | **0,791** | 0,845 | **0,817** | 21,7% | 370/98/68 |
| **B** (3 chamadas) | 0,762 | **0,872** | 0,814 | **23,3%** | 382/119/56 |
| Δ (A−B) | +0,028 | −0,027 | **+0,003** | −1,7pp | |

**Bootstrap pareado sobre o F1 por review (A−B, B=5000, semente 24): média
−0,0114, IC95 [−0,0465, +0,0221] — CRUZA ZERO.**

**A hipótese não se confirma no eixo.** A passada única não perde qualidade de
eixo de forma distinguível de ruído. O que ela faz é deslocar o erro: A é
levemente mais **precisa** e B levemente mais **sensível**, e o F1 empata.

### Onde a passada única cobra o preço: reviews curtas

| faixa | n | F1 braço A | F1 braço B | Δ |
|---|---:|---:|---:|---:|
| ≤200 chars | 30 | 0,621 | **0,650** | −0,029 |
| 201–500 | 30 | 0,769 | **0,794** | −0,025 |
| 501–1200 | 30 | **0,825** | 0,823 | +0,001 |
| >1200 | 30 | **0,844** | 0,837 | +0,007 |

O sinal é consistente e vai na direção que a hipótese previa — **a perda da
passada única se concentra nas reviews curtas**, exatamente a população que já
é o ponto fraco medido da classificação (§3 do consolidado). Em textos longos
A empata ou ganha. Com n=30 por faixa, um Δ de 0,03 não é conclusivo
isoladamente; o que vale é a monotonicidade dos quatro pontos.

### Por eixo

| eixo | n ref | A: P / R | B: P / R |
|---|---:|---|---|
| `ritmo` | 46 | 0,91 / **0,91** | 0,88 / 0,76 |
| `atuacao` | 50 | **1,00** / 0,92 | 0,94 / **0,98** |
| `direcao_imagem` | 52 | 0,94 / 0,98 | 0,94 / 0,98 |
| `roteiro_estrutura` | 79 | 0,94 / 0,84 | 0,93 / **0,90** |
| `som_trilha` | 25 | 0,88 / **0,92** | 0,91 / 0,84 |
| `tom_atmosfera` | 32 | 0,69 / 0,56 | **0,81 / 0,69** |
| `impacto_emocional` | 42 | **0,46** / 0,93 | **0,41** / 0,95 |
| `comparacoes` | 49 | **0,80 / 0,80** | 0,72 / 0,73 |
| `expectativa` | 26 | **0,58 / 0,58** | **0,73 / 0,85** |
| `critica_social` | 28 | **0,89** / 0,86 | 0,74 / **1,00** |

Dois achados que não estavam na pergunta:

- **`expectativa` é onde a passada única perde de verdade** (P 0,58 vs 0,73; R
  0,58 vs 0,85). É o eixo cuja definição depende mais de contexto ("o que a
  pessoa esperava ANTES de assistir e por quê") e o primeiro a ser sacrificado
  quando o prompt cresce. `tom_atmosfera` perde na mesma direção.
- **`impacto_emocional` tem precisão de 0,46 (A) e 0,41 (B) contra a
  referência** — mas isso **não** é o problema de saturação da spec, é o
  contrário. A referência é o consenso **verificado**, em que o passe `V2_alvo`
  já removeu as marcações fracas; um braço de passada única sem esse passe volta
  a marcar demais. Confirma, por um caminho independente, que o verificador é
  quem sustenta a precisão desse eixo.

### A vs B, sem referência

Jaccard médio **0,671**; conjunto **idêntico em 21 de 120 reviews (18%)**.
Eixos por review: referência 3,65 · A 3,90 · B 4,17.

Os dois braços concordam bem menos entre si do que cada um concorda com a
referência — o que é o resultado esperado de duas passadas únicas com a mesma
variância individual (26,5% de reprodutibilidade em passada única, medida em
`ESTABILIDADE_AGREGADA.md`) e é a justificativa da votação de 3, não uma
crítica a nenhum dos braços.

### Disciplina de lista fechada — medida ao vivo

| braço | rótulos fora da taxonomia | quais |
|---|---:|---|
| A | 6 em 480 eixos | `atracao`, `sombrio`, `ton_atmosfera`, `atucao`, `experiencia`, `liberdade` |
| B | 5 | `impato_emocional`, `comparações`, `rotativo`, `comparecoes`, `atencao` |

Onze rótulos inválidos em 240 chamadas de eixo (~4,6% das reviews), em três
famílias: **erro de digitação** (`atucao`, `impato_emocional`, `comparecoes`,
`ton_atmosfera`), **acento/plural** (`comparações`) e **invenção** (`sombrio`,
`liberdade`, `atracao`). É a validação empírica direta do requisito de
normalização rígida da Entrega 2 — e `comparações` é o mesmo modo de falha que o
estudo dos 35 achou em produção (`crítica_social` caindo para `livre` por causa
do acento).

---

## Secundário — POLARIDADE (sem referência)

| | valor |
|---|---|
| pares (review, eixo) com polaridade nos dois braços | 380 |
| **concordância A/B** | **81,3%** |
| valores fora da lista fechada | **nenhum** |
| cobertura (eixos atribuídos que receberam polaridade) | A 99% · B 97% |

| valor | braço A | braço B |
|---|---:|---:|
| `positivo` | 218 | 221 |
| `negativo` | **169** | 156 |
| `neutro` | **39** | **69** |
| `misto` | 36 | 42 |

**Leitura à mão de 8 discordâncias** (critério registrado: PRNG semente 24 sobre
os 71 pares em desacordo, ordenados por id):

| # | caso | A | B | quem acerta |
|---|---|---|---|---|
| 1 | `dune-2021` pos, `roteiro` — *"still just feels like a build up for the next two movies… Naming him Paul just seems wrong"* | negativo | neutro | **A** |
| 2 | `joker` med, `roteiro` — *"The idea is so good. They just don't execute… I actually love the ending. Very very good."* | misto | negativo | **A** |
| 3 | `shutter-island` neg, `impacto` — *"Dicap proves once again he just cannot make a good one sad to see"* | misto | negativo | **B** |
| 4 | `perfect-days` pos, `ritmo` — *"very little conflict. And yet it's a very captivating film"* | neutro | negativo | **nenhum** (é `misto`) |
| 5 | `barbie` pos, `critica_social` — *"le féminisme est mis en avant par contradiction ce qui n'est pas… le plus judicieux mais bon merci à ce film"* | misto | positivo | **A** |
| 6 | `parasite` med, `roteiro` — *"achei que faltou tensão, e é muito ilógico toda a trama, mas… num geral eu gostei"* | misto | negativo | **A** |
| 7 | `napoleon` pos, `comparacoes` | misto | neutro | **B** |
| 8 | `im-still-here` med, `direcao_imagem` — *"cortes bruscos que encerram o plano… De qualquer forma, a fotografia tá bem bonita"* | positivo | misto | **B** |

Placar 4 A / 3 B / 1 nenhum. O padrão é mais informativo que o placar: **B usa
`neutro` como abstenção** (69 contra 39), e nos casos 1, 2, 5 e 6 o `neutro`/
`negativo` de B apaga uma concessão explícita que A capturou como `misto`. Faz
sentido estruturalmente: em B a chamada de polaridade recebe só o texto e uma
lista de eixos, sem ter decidido os eixos; em A o modelo acabou de decidir por
que atribuiu cada eixo e compromete-se com a polaridade.

**Na polaridade, a passada única é a melhor das duas** — resultado oposto ao que
a hipótese previa.

---

## Secundário — FEELINGS (sem referência)

| categoria | Jaccard A/B | etiquetas/review A | etiquetas/review B | fora da lista |
|---|---:|---:|---:|---:|
| `mood` | 0,360 | 0,75 | **1,57** | 14 |
| `experiencia` | 0,344 | 0,62 | **1,34** | 2 |
| `narrativa` | 0,456 | 0,21 | **0,88** | 3 |

**O braço B produz duas a quatro vezes mais etiquetas.** Lido isoladamente, esse
número diz "a passada única perde metade dos feelings" — que era exatamente a
degradação silenciosa que a hipótese temia. **A leitura à mão inverte o sinal.**

Critério registrado: as 4 maiores lacunas B−A, 1 caso mediano, 2 casos em que A
rendeu mais. Seleção deliberadamente adversarial contra o braço A.

- **`napoleon-2023`** (italiano, sobre encenação e a filmografia de Scott).
  A = 0 etiquetas. B = **8**: `melancolico`, `contemplativo`, `esperancoso`,
  `de_ver_acompanhado`, `de_sair_pensando`, `amadurecimento`,
  `ascensao_e_queda`, `final_aberto`. **Nenhuma sustentada pelo texto.** A está
  certo ao abster-se.
- **`the-invite-2026`**, 160 chars: *"I came to AMC Theater to laugh, to cry,
  for that indescribable feeling when the lights begin to dim… and that's
  exactly what The Invite gave me."* A = 0 (perde `de_chorar`/`de_rir`, que o
  texto sustenta). B = **7**, incluindo `aconchegante`, `catartico` e
  `amadurecimento`. Os dois erram; B erra inventando.
- **`cidade-de-deus`** (6.999 chars, negativa). B acrescenta `camara_fechada`
  — *huis clos* — a um épico de favela.
- **`dune-part-two`**: B acrescenta `final_aberto` e `melancolico`, nenhum
  sustentado.
- **`mother-2017`** (o caso em que A rende mais): A = 6 etiquetas
  (`perturbador`, `angustiante`, `caotico`, `desconfortavel`, `exaustivo`,
  `narrativa_outro`), B = 2. A review fala de raiva, estresse e taquicardia —
  **A está certo e B subrotula**.

Nas 4 maiores lacunas, as etiquetas extras de B eram infundadas em 3.

**Evidência quantitativa do mesmo padrão:**

| | braço A | braço B |
|---|---:|---:|
| etiquetas/review em ≤200 chars | 0,53 | **2,20** |
| etiquetas/review em >1200 chars | 2,83 | 5,70 |
| correlação etiquetas × comprimento | +0,295 | +0,473 |
| reviews ≤300 chars com **≥5** etiquetas | 0 (0%) | 4 (9%) |
| reviews com **zero** etiquetas (abstenção) | 44 (**37%**) | 8 (**7%**) |

As duas curvas crescem com o texto, então B não é puro ruído. Mas B atribui
**2,2 etiquetas a reviews de até 200 caracteres** e se abstém em apenas 7% do
corpus — contra 37% de A.

**Conclusão sobre feelings: os dois braços falham, em direções opostas.** A
subrotula (37% de abstenção, perde etiquetas que o texto sustenta); B
superrotula (7% de abstenção, inventa etiquetas em reviews curtas). **Nenhum
dos dois está pronto para virar filtro público**, porque um filtro é uma
promessa: `de_chorar` devolvendo `napoleon-2023` quebra a promessa de forma
visível ao usuário. Feelings precisa da mesma calibração contra gabarito humano
que o eixo teve — está detalhado na Entrega 2.

---

## Custo

Medido sobre as 120 reviews, projetado para **300 filmes × 120 reviews =
36.000 reviews**:

| chamada | US$ / passada sobre 36.000 |
|---|---:|
| A (eixo + polaridade + feelings, 1 chamada) | **4,72** |
| B1 (só eixo — prompt de produção) | 3,29 |
| B2 (só polaridade) | 2,89 |
| B3 (só feelings) | 2,57 |
| B (as três) | **8,75** |

| cenário | US$ |
|---|---:|
| hoje (só eixo, votação de 3) | 9,86 |
| **A com votação de 3 em tudo** | **14,15** |
| **B com votação de 3 em tudo** | **26,24** |
| híbrido: 3 votos no eixo + 1× A | 14,57 |
| híbrido: 3 votos no eixo + 1× polaridade + 1× feelings | 15,32 |

| | A | B |
|---|---:|---:|
| chamadas por review | 1 | 3 |
| tokens de prompt por review | 1.895 | 2.524 (+33%) |
| **aproveitamento de cache de prefixo** | **77%** | 51% |
| latência mediana por review | **1,6 s** | 4,1 s |

**A diferença entre os dois braços, com votação de 3 e sobre um catálogo de 300
filmes, é de US$ 12.** Esse é o número mais decisivo do experimento e ele age
contra a economia: **não existe argumento de custo para adotar a passada única.**
A diferença real é de latência (2,6× ) e de acoplamento — o braço A refaz as
três decisões quando qualquer uma precisa mudar, e o braço B permite trocar a
lista de feelings sem reclassificar eixo nenhum.

*(O aproveitamento de cache de 77% em A vem de o prompt longo ser prefixo
constante entre reviews; em B ele se dilui entre três prompts diferentes. Isso
já está embutido nos custos acima.)*

---

## Recomendação da Entrega 3

**Resultado negativo registrado como tal: a hipótese não se confirmou no eixo.**
A passada única não degrada a classificação de eixo de forma distinguível de
ruído (ΔF1 +0,003; IC95 do bootstrap pareado cruza zero). Se a decisão dependesse
só do eixo, o braço A passaria.

**Mas a recomendação é o braço B, por três razões que a medição produziu e que
não estavam na hipótese:**

1. **A perda existe e é seletiva, não difusa.** Ela se concentra em `expectativa`
   (P/R 0,58/0,58 contra 0,73/0,85) e `tom_atmosfera`, e nas reviews curtas
   (F1 0,621 contra 0,650 em ≤200 chars) — a população que já é o ponto fraco
   conhecido da classificação. Uma perda concentrada é pior que uma perda média
   equivalente, porque some na métrica agregada.
2. **Não há economia que a pague.** US$ 12 sobre 300 filmes.
3. **O acoplamento é o custo escondido.** A lista de feelings vai mudar — a
   Entrega 2 desenha o gatilho de crescimento dela por frequência de catch-all.
   No braço A, cada mudança na lista invalida a classificação de eixo do corpus
   inteiro, porque muda o prompt e portanto o `taxonomia_id`. No braço B, B1
   fica intocado e só B3 roda de novo. Esta é a razão de arquitetura, e é a mais
   forte das três.

**Com uma exceção medida: a POLARIDADE deve ficar junto do eixo.** Na leitura à
mão, o `neutro` de B apagou concessões explícitas em 4 dos 8 casos, e o
mecanismo é claro — quem decide a polaridade precisa saber por que o eixo foi
atribuído. A recomendação concreta é **duas chamadas, não três**:

- **chamada 1** — eixo **+ polaridade por eixo** (prompt de produção acrescido
  só da definição de polaridade), sob votação de 3, como hoje;
- **chamada 2** — feelings, isolada, com sua própria lista fechada e seu próprio
  identificador de versão.

Custo projetado desse desenho sobre 36.000 reviews, com 3 votos na chamada 1 e
1 passada na 2: **≈ US$ 12,50** — abaixo do braço B completo e ~US$ 2,60 acima do
que a classificação de eixo já custa hoje.

**Limite desta entrega.** N = 120 (4,2% das 2.866 com referência), passada única
nos dois braços, um único modelo, uma única execução — sem repetição, então a
variância entre execuções do *mesmo* braço não foi medida e pode ser da ordem
do Δ observado. Os números de polaridade e feelings **não têm referência
nenhuma**: são concordância entre braços mais 15 casos lidos à mão, e a seleção
desses casos foi adversarial de propósito. Nada aqui estima a acurácia de
polaridade ou de feelings — só mostra que os dois braços discordam bastante
(81,3% na polaridade, Jaccard 0,34–0,46 nos feelings) e como cada um erra.
