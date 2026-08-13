# Reclassificação sob A_regra — recalibração do schema e efeito no ranking

**Data:** 2026-08-13 · **Natureza:** medição, zero mudança de produção (schema, lift, `contraste` e frontend seguem NÃO implementados) · **`taxonomia_id`:** `11871105c0d3` → `ebab2667de74`

Continuação de `TAXONOMIA_10.md` (seção "Atualização — Correção de recall
em review curta") e de `VOTACAO_3.md`. Aquele registrou a promoção de
A_regra e o mecanismo do defeito corrigido; este documenta o que a
reclassificação completa do corpus de produção (3990 reviews, votação de 3,
consenso 2/3) muda nos números que calibram o schema — nulo de permutação,
margem de lift, estado `contraste` — e no ranking de frequência dos 10
eixos. Scripts: `scripts/votacao_3.py` (reclassificação, Entregas 2/4/5 na
numeração dele) e `scripts/comparacao_a_regra.py` (comparação isolada
antigo↔novo, criado nesta sessão porque a comparação embutida em
`votacao_3.py` usa como baseline a passada única do gate original — variável
demais para isolar "só o prompt mudou").

Arquivo do consenso antigo: `resultado/votacao-3/_arquivo_taxonomia-11871105c0d3/`.

---

## O veredito, antes dos números

**A correção funcionou exatamente onde foi desenhada para funcionar — e
teve um efeito colateral real e mensurável em outro lugar do schema, que
precisa de decisão, não de silêncio.**

`fracao_livre` em reviews ≤200 chars caiu de 9,76% para 2,58% (queda de
3,8×) e ficou **inalterada** acima de 800 chars (0,32% → 0,32%): o alvo foi
atingido com cirurgia, não com generosidade difusa. A estabilidade do
consenso não piorou (65,0% → 66,5%). Mas `impacto_emocional` saturou —
passou de 45,9% para 75,5% das reviews — e isso **comprime o espaço que
sobra para ele discriminar bucket**, a ponto de deixar de encabeçar a linha
em 6 filmes, incluindo `barbie`, o caso que deu nome ao estado
`contraste: valorativo` em `TAXONOMIA_10.md`. O contraste de `barbie` não
sumiu — moveu de `impacto_emocional` (22,5pp sob o prompt antigo) para
`critica_social` (20,0pp sob o novo), um eixo mais coerente com do que o
filme é sobre. Mas o efeito é sistêmico, não isolado nele: a fração de
pares que cruzam cada margem que é ruído estatístico (nulo de permutação)
**subiu em toda margem testada**, e a margem recomendada de 20pp precisa
ser revisitada.

---

## Entrega 4 — Recalibração dos números do schema

### `fracao_livre` e consenso vazio

| | antigo (`11871105c0d3`) | novo (`ebab2667de74`) |
|---|---:|---:|
| `fracao_livre` global | 3,76% | **1,33%** |
| consenso vazio (abstenção coletiva) | 0,68% | **0,23%** |

### Nulo de permutação — a mesma margem ficou mais ruidosa

2000 rodadas, embaralhando bucket dentro de cada filme, MESMO método de
`TAXONOMIA_10.md`. 35 filmes avaliados nas duas rodadas (27 com os três
buckets a 40, 8 com algum sub-40 — **idêntico ao antigo**, a seleção não
mudou, só a classificação).

| margem | pares acima (antigo → novo) | filmes com ≥1 (antigo → novo) | sem contraste (antigo → novo) | **fração ruído (antigo → novo)** |
|---|---:|---:|---:|---:|
| 10pp | 111 → 86 | 34 → 33 | 1 → 2 | 63% → 77% |
| 15pp | 61 → 41 | 30 → 22 | 5 → 13 | 45% → 63% |
| **20pp** | **28 → 21** | **18 → 13** | **17 → 22** | **34% → 41%** |
| 25pp | 14 → 12 | 9 → 9 | 26 → 26 | 26% → 29% |

**Em toda margem, menos pares reais cruzam o limiar E uma fração maior do
que cruza é ruído.** O nulo em si caiu em termos absolutos (a 20pp, a média
do nulo foi de 9,6 para 8,5 pares) — não é que o embaralhamento aleatório
ficou mais forte, é que o SINAL ficou mais fraco relativo a ele. A causa é
mecânica, não um problema de qualidade: quando um eixo passa a aparecer em
70-80% das reviews de TODO bucket (o caso de `impacto_emocional`), o teto
de 100% comprime o intervalo em que a diferença entre buckets pode crescer
— um eixo que já está perto do teto na pior categoria não tem para onde
subir nas outras.

### Margem recomendada — dado que a margem fixa antiga (20pp) não serve mais como estava calibrada

Medi 2 margens adicionais (30pp, 35pp) para achar onde a fração de ruído do
corpus NOVO volta a bater com o que 20pp entregava no corpus ANTIGO (34%,
o número que justificou a recomendação em `TAXONOMIA_10.md`):

| margem | fração ruído (novo) |
|---|---:|
| 20pp | 41% |
| **25pp** | **29%** |
| 30pp | 24% |
| 35pp | 22% |

**25pp no corpus novo entrega pureza de lista equivalente (ligeiramente
melhor) que 20pp entregava no corpus antigo** (29% contra 34%). Mas o custo
de cobertura é real: a 25pp, só **9 de 35 filmes** têm ao menos um eixo
acima da margem, contra 21 de 35 que 20pp dava no corpus antigo — e o
próprio 20pp no corpus NOVO já caiu de 18 para 13 filmes com sinal.

**Recomendação, com a mesma ressalva dupla de `TAXONOMIA_10.md`:** não há
uma margem única correta — é uma escolha entre pureza de lista e cobertura,
e ela ficou mais cara depois da correção porque o denominador (frequência
média por eixo) subiu. Se o critério é "mesmo risco de ruído que a
recomendação anterior", a margem correta agora é **25pp**, aceitando que
menos de um terço dos filmes (9/35) mostra contraste. Se o critério é
"mesma cobertura que antes" (≥18 filmes com sinal), a margem tem que ficar
em **15pp ou abaixo**, aceitando fração de ruído de 45-63%. **Esta é uma
decisão de produto, não uma conclusão que a medição resolve sozinha** — os
dois números estão aqui para quem decidir.

---

## Entrega 5 — Efeito no ranking dos 10 eixos

### O ranking de frequência quase não mudeu de POSIÇÃO — mas mudou de FORMA

| # novo | eixo | freq. antiga | freq. nova | posição antiga | movimento |
|---|---|---:|---:|---:|---:|
| 1 | `impacto_emocional` | 45,9% | **75,5%** | 1 | = |
| 2 | `roteiro_estrutura` | 44,0% | 55,9% | 2 | = |
| 3 | `comparacoes` | 43,4% | 39,7% | 3 | = |
| 4 | `direcao_imagem` | 32,5% | 33,4% | 5 | +1 |
| 5 | `ritmo` | 33,7% | 31,4% | 4 | −1 |
| 6 | `atuacao` | 29,1% | 28,6% | 6 | = |
| 7 | `critica_social` | 24,5% | 23,5% | 9 | **+2** |
| 8 | `tom_atmosfera` | 26,2% | 23,4% | 8 | = |
| 9 | `expectativa` | 27,6% | **20,7%** | 7 | **−2** |
| 10 | `som_trilha` | 13,5% | 13,9% | 10 | = |

**A previsão de `TAXONOMIA_10.md`/da auditoria de que `expectativa` subiria
de 7º para 4º NÃO se confirmou — ela caiu, de 7º para 9º**, o oposto do
previsto. `critica_social` sobe 2 posições, não `expectativa`. A ordem
GERAL do ranking mudou pouco (a maioria dos eixos manteve posição ou moveu
1), mas as FREQUÊNCIAS absolutas mudaram muito — `impacto_emocional` quase
dobrou, o que é uma mudança de escala do produto (o eixo mais comum passa a
cobrir 3 em cada 4 reviews) mesmo sem mover de posição.

### O mecanismo por trás da queda de `expectativa`: competição, não perda de sinal

371 reviews perderam `expectativa` entre o consenso antigo e o novo
(92 ganharam, saldo líquido −279). **40% das que perderam ganharam
`impacto_emocional` no mesmo review** — a regra 2 ampliada ("um efeito
declarado é eixo mesmo dito em três palavras") está reclassificando
frustração/decepção que antes só cabia em `expectativa` como
`impacto_emocional`, porque "não era o que eu esperava" também é um efeito
declarado. Não é perda de sinal: é o sinal migrando para um eixo mais
específico quando os dois competem pela mesma frase.

### O preditor certo já existia — e não era o da Entrega 1

A extrapolação de viés original (`scripts/vies_recall_curtas.py`) comparava
o observado contra um TETO hipotético de recall=1,0 sob o prompt ANTIGO —
uma pergunta diferente de "o que A_regra vai produzir". Um preditor melhor,
disponível na própria validação de variantes
(`resultado/auditoria-acuracia/variantes/comparacao.json`), usa a razão
recall/precisão medida entre A_regra e o baseline nas 100 reviews
auditadas:

| eixo | fator previsto (recall/precisão) | fator real medido | erro |
|---|---:|---:|---:|
| `direcao_imagem` | 1,00× | 1,03× | 0,03 |
| `som_trilha` | 1,00× | 1,03× | 0,03 |
| `ritmo` | 1,00× | 0,93× | 0,07 |
| `critica_social` | 0,93× | 0,96× | 0,04 |
| **`expectativa`** | **0,79×** | **0,75×** | 0,04 |
| `tom_atmosfera` | 0,83× | 0,89× | 0,06 |
| `atuacao` | 0,90× | 0,98× | 0,08 |
| `roteiro_estrutura` | 1,38× | 1,27× | 0,10 |
| `comparacoes` | 1,05× | 0,91× | 0,14 |
| `impacto_emocional` | 1,95× | 1,64× | 0,30 |

**Acerta o sinal em 9 dos 10 eixos, e a ordem de grandeza em 8** — incluindo
a queda de `expectativa`, que o preditor da Entrega 1 errou na direção. A
lição de método: quando existe uma comparação PAREADA de precisão/recall
entre o prompt novo e o antigo (a validação de variantes já mede isso), ela
prediz frequência de produção melhor que uma extrapolação de teto sobre o
prompt antigo sozinho — porque incorpora o que o prompt novo REALMENTE faz
de diferente, eixo a eixo, e não só quanto ele deveria recuperar.

### Trocas de eixo que encabeça a linha, por margem

"Encabeça" = maior lift do filme, entre os que passam a margem.

| margem | manteve o mesmo eixo | deixou de encabeçar | passou a encabeçar diferente | filmes com algum sinal |
|---|---:|---:|---:|---:|
| 10pp | 11 | 23 | 22 | 35 |
| 15pp | 7 | 23 | 15 | 32 |
| **20pp** | **5** | **13** | **8** | **22** |
| 25pp | 2 | 7 | 7 | 14 |

A 20pp: **13 filmes deixaram de ter um eixo acima da margem ou trocaram**
(`aftersun`, `avengers-endgame`, `barbie`, `bones-and-all`, `interstellar`,
`longlegs`, `shutter-island`, `spider-man-across-the-spider-verse`,
`talk-to-me-2022` perderam contraste; `everything-everywhere-all-at-once`,
`obsession-2026`, `perfect-days-2023`, `the-invite-2026` trocaram de eixo),
e **8 ganharam um eixo novo que não tinham antes**
(`anatomy-of-a-fall` → `ritmo`, `napoleon-2023` → `impacto_emocional`,
`the-hateful-eight` → `tom_atmosfera`, `wonka` → `atuacao`, entre outros).
Só **5 filmes mantiveram exatamente o mesmo eixo na frente.**

### O caso `barbie`: contraste não desapareceu, mudou de eixo

| | antigo | novo |
|---|---|---|
| melhor eixo | `impacto_emocional` | `critica_social` |
| lift | **22,5pp** | **20,0pp** |
| frequência por bucket | negativas 27,5% · medianas 32,5% · **positivas 55,0%** | negativas **82,5%** · medianas 62,5% · positivas 47,5% |
| `impacto_emocional` sob o novo | — | negativas 65% · medianas **70%** · positivas **70%** (lift = **0,0pp**) |

`impacto_emocional` para `barbie` foi de discriminador limpo (gradiente
27,5→55,0%) a **saturado e sem poder de separação nenhum** — 70% em dois
dos três buckets, empatados. Mas o filme não perdeu contraste: ele migrou
para `critica_social`, que sobe de forma monotônica do bucket negativo
(82,5%) ao positivo (47,5%) — e que é, plausivelmente, um eixo mais
verdadeiro sobre do que a crítica a `barbie` realmente fala (a mensagem
feminista/patriarcado do filme, não só "o efeito que causou"). O caso que
deu nome ao estado `contraste: valorativo` continua tendo contraste — só
que agora por um motivo temático mais correto, bem na borda da margem de
20pp.

---

## Reprodução

```bash
python scripts/votacao_3.py relatorio              # entrega4/5 do lado novo
python scripts/comparacao_a_regra.py                # comparação isolada antigo↔novo
```

Saídas: `resultado/votacao-3/relatorio.json`,
`resultado/votacao-3/comparacao_a_regra.json`. Consenso antigo arquivado em
`resultado/votacao-3/_arquivo_taxonomia-11871105c0d3/`.

## O que este documento não decide

- **Qual margem adotar** (15/20/25pp) — a Entrega 4 mede o trade-off,
  não escolhe por quem for desenhar o schema.
- **Se a saturação de `impacto_emocional` (75,5%) é aceitável** para um
  eixo que o schema vai exibir — um eixo presente em 3 de cada 4 reviews
  ainda é informativo para o LEITOR, mas é um sinal fraco para RANQUEAR
  filmes entre si, que é o que o lift mede.
- Schema, lift em produção, estado `contraste`, frontend — **nada disso foi
  implementado**, como pedido.
