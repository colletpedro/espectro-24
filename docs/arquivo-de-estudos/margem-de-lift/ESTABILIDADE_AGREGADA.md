# Estabilidade das frequências agregadas — mede se a instabilidade individual chega ao schema

**Data:** 2026-08-10 · **Natureza:** medição, zero chamada de LLM · **Mudanças de produção:** nenhuma

Sobre as 200 reviews com dupla classificação da Entrega 3 da auditoria de
acurácia (`resultado/auditoria-acuracia/estabilidade_bruto.jsonl`), já em
disco. Nenhuma reclassificação, nenhum parâmetro tocado, nenhum commit de
schema. Script: `scripts/estabilidade_agregada.py`.

---

## O veredito, antes dos números

**Parcialmente estável, com uma exceção que pesa mais do que a média sugere.**

A diferença média absoluta entre as duas execuções é **2,18pp** — dentro da
folga de 2-3pp que o critério original previa como "ruído que não se
propaga". Mas a média esconde o caso que importa: **`impacto_emocional`**,
o eixo que a taxonomia de 10 eixos AFROUXOU (29,2% → 46,1%, o maior salto de
qualquer eixo), se move **5,5pp** entre as duas execuções — e cai **11pp**
quando a frequência é restrita ao núcleo estável. **`livre`** — que É,
literalmente, `fracao_livre`, o primeiro número que a calibração do schema
usa — se move **5pp**, na direção de SUBIR (mais reviews caem em `livre` na
reclassificação).

**Achado que a Entrega 1 sozinha não pega:** `tom_atmosfera` passa limpo no
teste de frequência agregada (28,5% → 30,0%, só +1,5pp) — mas ao restringir
ao núcleo (Entrega 3) a frequência cai **10,5pp**, quase tanto quanto
`impacto_emocional`. Frequência agregada estável não significa atribuição
individual estável: `tom_atmosfera` está ENTRANDO e SAINDO de reviews
diferentes em quantidade parecida, e as duas coisas se cancelam no número
agregado — por acaso, não por desenho. Isso é exatamente o "erro
correlacionado vs. erro que se cancela" que a tarefa pediu para medir, e a
resposta para `tom_atmosfera` é: cancela nesta amostra, mas o mecanismo por
trás (~1 em cada 3 atribuições não repete) não dá garantia de que cancele
sempre.

A margem de lift (20pp) não foi de fato estressada por esta medição: o lift
agregado entre buckets, pooled sobre 200 reviews de 34 filmes, nunca chega
perto de 20pp em nenhuma das duas execuções (máximo observado: 10pp). Zero
eixos mudam de lado da margem — mas porque nenhum chegou perto dela, não
porque a margem resistiu a um teste de verdade. Essa calibração continua
**não testada**, não confirmada.

`tom_atmosfera` vs `impacto_emocional`, a suspeita de confusão registrada
antes da medição, **não se confirma como troca sistemática**: só 2 de 74
casos relevantes (2,7%) mostram o padrão "um aparece onde o outro some". A
instabilidade dos dois é independente, não uma fronteira mal desenhada entre
eles — redesenhar o prompt não resolveria isso.

---

## Entrega 1 — Frequência por eixo, execução A vs execução B

n=200. Execução A = classificação persistida em produção
(`eixos_original`); execução B = reclassificação da auditoria
(`eixos_reclassificado`), mesmo prompt, mesmo modelo, nenhuma temperatura
tocada em nenhum dos dois caminhos.

| eixo | freq A | freq B | diff (pp) |
|---|---:|---:|---:|
| `impacto_emocional` | 48,5% | 43,0% | **-5,5** |
| `livre` | 14,5% | 19,5% | **+5,0** |
| `comparacoes` | 40,0% | 43,5% | **+3,5** |
| `expectativa` | 26,0% | 29,5% | **+3,5** |
| `atuacao` | 26,5% | 28,0% | +1,5 |
| `tom_atmosfera` | 28,5% | 30,0% | +1,5 |
| `roteiro_estrutura` | 47,0% | 45,5% | -1,5 |
| `ritmo` | 26,0% | 25,5% | -0,5 |
| `direcao_imagem` | 28,0% | 27,5% | -0,5 |
| `critica_social` | 23,0% | 22,5% | -0,5 |
| `som_trilha` | 14,0% | 14,5% | +0,5 |

**Diferença média absoluta: 2,18pp.** Sete das onze categorias ficam dentro
de 3pp — o critério do enunciado, cumprido pela maioria. As quatro que
excedem: `impacto_emocional`, `livre`, `comparacoes`, `expectativa` — não
por acaso, são justamente os dois eixos NOVOS (`expectativa`,
`critica_social` — este último dentro da folga) e o eixo AFROUXADO
(`impacto_emocional`), mais o resíduo (`livre`) que os alimenta. Os cinco
eixos herdados do gate de 8 sem alteração de definição (`ritmo`, `atuacao`,
`direcao_imagem`, `roteiro_estrutura`, `som_trilha`) ficam todos dentro de
1,5pp — **por esta métrica**, instabilidade concentrada onde o desenho
mais recentemente mudou a régua.

**Mas `tom_atmosfera` (também herdado, sem alteração) só passa por esta
métrica** — a Entrega 3 mostra que ele tem tanta rotatividade de atribuição
quanto `impacto_emocional`, só que as entradas e saídas se cancelam no
agregado. A leitura correta não é "6 eixos estáveis, 4 instáveis": é
"5 eixos estáveis nas duas medidas; `tom_atmosfera` estável só na
frequência agregada; `impacto_emocional`, `livre`, `comparacoes` e
`expectativa` instáveis nas duas".

---

## Entrega 2 — O efeito no lift

n por bucket na amostra de 200: negativas 66, medianas 57, positivas 77.

**Ressalva que se confirmou na medição, não só declarada a priori:** o
lift aqui é calculado agregando as 200 reviews de 34 filmes DENTRO de cada
bucket — não por filme, como a calibração real do schema (que soma pares
`(filme, eixo)`). Com só 2-13 reviews por filme na amostra de estabilidade,
um lift por filme seria ruído puro (a própria calibração original exige
mínimo de 3 por bucket para entrar no nulo de permutação, e usa até 40).
Agregar por bucket, ignorando o filme, é a única forma de ter `n`
utilizável — mas mede uma coisa MAIS FRACA que "os pares perto da margem
flipariam": mede se a frequência POR BUCKET, somada sobre filmes
heterogêneos, se move.

| eixo | lift A | vencedor A | lift B | vencedor B | mudou de lado (20pp)? |
|---|---:|---|---:|---|---|
| `impacto_emocional` | 10,0pp | positivas | 9,3pp | positivas | não |
| `direcao_imagem` | 9,6pp | medianas | 7,4pp | medianas | não |
| `critica_social` | 9,0pp | negativas | 7,5pp | negativas | não |
| `roteiro_estrutura` | 4,6pp | medianas | 1,1pp | medianas | não |
| `atuacao` | 4,1pp | medianas | 0,5pp | negativas | não |
| `tom_atmosfera` | 2,6pp | medianas | 5,2pp | positivas | não |
| `expectativa` | 2,0pp | negativas | 2,0pp | medianas | não |
| `comparacoes` | 0,6pp | negativas | 1,5pp | positivas | não |
| `som_trilha` | 0,9pp | negativas | 3,9pp | negativas | não |
| `ritmo` | 0,5pp | negativas | 2,0pp | negativas | não |

**0 de 10 eixos mudam de lado da margem de 20pp — mas o número mais
honesto aqui não é esse, é que o lift MÁXIMO observado, nas duas execuções,
é 10,0pp.** Nenhum eixo chegou perto o bastante da margem para que a
pergunta "o lado muda?" fosse sequer colocada à prova. **Esta entrega não
confirma que a margem de 20pp é robusta — ela não conseguiu testar isso.**
O teste que testaria de verdade exigiria dupla classificação POR FILME com
`n` comparável ao de produção (até 40/bucket), o que é reclassificação —
fora do escopo desta tarefa.

O que a Entrega 2 mede de fato, e que É válido: mesmo agregado sobre 34
filmes, nenhum eixo saltou de "baixo" para "alto" contraste entre as duas
execuções — todos os lifts, nas duas execuções, ficam abaixo de 10pp. Mas o
**bucket vencedor** (o de maior frequência, o que decidiria o rótulo de
peso se este fosse um par tratado individualmente) troca em **4 dos 10
eixos**: `atuacao` (medianas → negativas), `tom_atmosfera` (medianas →
positivas), `comparacoes` (negativas → positivas) e `expectativa`
(negativas → medianas) — todos com lift pequeno nos dois lados (0,5 a
5,2pp), então a troca de vencedor é ruído de margem estreita, não um
contraste real virando de lado. **Isto reforça a leitura da Entrega 1, não
a contradiz:** com lift tão baixo em ambas as execuções, qual bucket "ganha"
é instável quase por definição — e é exatamente por isso que a margem de
20pp existe, para não deixar essas diferenças de fração de ponto decidir
qual bucket "vence" um eixo.

---

## Entrega 3 — O núcleo estável

Núcleo = eixos presentes nas duas execuções. Borda = eixos presentes em só
uma (diferença simétrica).

| | valor |
|---|---:|
| tamanho médio do núcleo | **2,57** eixos |
| tamanho médio da borda | **1,38** eixos |

Núcleo maior que borda em média — a maioria da classificação de uma review
sobrevive à reclassificação —, mas a razão (2,57 : 1,38 ≈ 1,9 : 1) está
longe de "borda é ruído desprezível".

**Eixos com mais ocorrências na borda do que no núcleo** (só dois, dos 11):

| eixo | n núcleo | n borda | razão borda/núcleo |
|---|---:|---:|---:|
| `livre` | 13 | 42 | **3,23** |
| `tom_atmosfera` | 36 | 45 | **1,25** |

`livre` é o caso extremo: das 55 vezes que apareceu em alguma das duas
execuções, só 13 apareceram nas DUAS — 76% do tempo que uma review cai em
`livre`, é só numa execução, não nas duas. Isso é o oposto de um resíduo
estável; é o eixo cuja definição (implícita: "nada mais coube") é a menos
reprodutível de todas, por construção — `livre` não tem regra própria, é
o que sobra depois que os outros dez falharam em bater, e reclassificar
muda o que "os outros dez" decidem, o que muda o que sobra.

**Frequência restrita ao núcleo vs. frequência da execução completa**
(a pergunta que decide se a borda é ruído simétrico ou viés):

| eixo | freq completa (A) | freq só-núcleo | queda (pp) |
|---|---:|---:|---:|
| `impacto_emocional` | 48,5% | 37,5% | **-11,0** |
| `tom_atmosfera` | 28,5% | 18,0% | **-10,5** |
| `livre` | 14,5% | 6,5% | **-8,0** |
| `comparacoes` | 40,0% | 32,5% | -7,5 |
| `roteiro_estrutura` | 47,0% | 40,5% | -6,5 |
| `ritmo` | 26,0% | 20,0% | -6,0 |
| `expectativa` | 26,0% | 20,0% | -6,0 |
| `critica_social` | 23,0% | 18,0% | -5,0 |
| `direcao_imagem` | 28,0% | 24,0% | -4,0 |
| `atuacao` | 26,5% | 26,0% | -0,5 |
| `som_trilha` | 14,0% | 13,5% | -0,5 |

Toda linha cai — é aritmeticamente inevitável (núcleo ⊆ execução completa,
sempre). O que importa é o TAMANHO da queda, e ele não é uniforme:
`atuacao` e `som_trilha` perdem quase nada (≤0,5pp) restringindo ao
núcleo — a classificação desses dois É estável, quase toda a frequência
observada sobrevive às duas execuções. `impacto_emocional` e
`tom_atmosfera` perdem mais de 10pp cada — mais de um quinto da frequência
completa de `impacto_emocional` (48,5%) vem de atribuições que NÃO se
repetem numa segunda passada.

---

## Entrega 4 — `tom_atmosfera` vs `impacto_emocional`: troca ou independência?

Das 200 reviews, em 126 nenhum dos dois eixos oscila entre execuções — a
maioria do corpus não toca essa questão. Das **74 restantes** (ao menos um
dos dois oscila):

| padrão | n | fração dos relevantes |
|---|---:|---:|
| **troca sistemática** (um entra, o outro sai, na mesma review) | **2** | **2,7%** |
| ambos oscilam, mesma direção (os dois entram ou os dois saem juntos) | 2 | 2,7% |
| **só um oscila, o outro fica igual nas duas execuções** | **70** | **94,6%** |

**Não é troca sistemática.** A hipótese que motivou a Entrega 4 — que o
afrouxamento de `impacto_emocional` borrou a fronteira com `tom_atmosfera`,
e o modelo hesita entre os dois — não se sustenta: se fosse fronteira mal
desenhada, a maioria das oscilações mostraria o padrão de troca (um some
exatamente onde o outro aparece). Em vez disso, **94,6% das oscilações são
independentes**: cada eixo aparece ou some por conta própria, sem o outro
se mover em compensação.

**Consequência para a ação:** redesenhar a fronteira do prompt entre os
dois eixos NÃO resolveria a instabilidade — ela não está concentrada
naquela fronteira específica, está espalhada como instabilidade geral do
modelo, que por acaso atinge esses dois eixos com frequência mais alta
(são dois dos que mais oscilam em termos absolutos, Entrega 1) sem que a
causa seja confusão MÚTUA entre eles.

---

## O que fica sem resposta

- **A margem de lift de 20pp não foi testada com poder estatístico
  suficiente.** A Entrega 2 mede lift agregado por bucket sobre 34 filmes
  heterogêneos, e nenhum eixo chegou perto da margem nas duas execuções —
  o que impede a pergunta "os pares perto da margem trocam de lado?" de
  ser respondida. Um teste de verdade exige dupla classificação POR FILME
  com `n` de produção, que é reclassificação — fora do escopo aqui.
- **Por que `livre` e `impacto_emocional` são os mais instáveis** não foi
  investigado — só medido. Pode ser ambiguidade genuína no texto das
  reviews que caem nesses casos, viés de amostra da temperatura da API, ou
  a definição do eixo/resíduo ser mesmo mais permeável a leitura variável.
  A auditoria humana (Entregas 1-2 da tarefa anterior, ainda paradas
  aguardando anotação) deveria ajudar a decidir qual.
- **O efeito líquido em `fracao_livre` do schema (4,81%, medido sobre
  3948 reviews) não foi recalculado** — a medição aqui é sobre a
  sub-amostra de 200 reclassificadas, e o `+5pp` observado é o tamanho da
  variância de execução NESSA amostra, não uma correção ao número
  publicado. Extrapolar exigiria mais reclassificação.

## Reprodução

```bash
python scripts/estabilidade_agregada.py
```

Lê `resultado/auditoria-acuracia/estabilidade_bruto.jsonl` (já em disco, da
Entrega 3 da auditoria de acurácia). Zero rede, zero chamada de LLM.
Escreve `resultado/auditoria-acuracia/estabilidade_agregada.json`.
