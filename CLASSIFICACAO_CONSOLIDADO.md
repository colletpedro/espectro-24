# Classificação de 10 eixos — consolidado da fase, para o desenho do schema

**Data:** 2026-08-14 · **Natureza:** consolidação de medição, zero mudança de produção · **`taxonomia_id` corrente:** `ebab2667de74`

Este documento substitui a necessidade de reabrir `TAXONOMIA_10.md`,
`VOTACAO_3.md`, `VOTACAO_3_A_REGRA.md` e os relatórios da auditoria de
acurácia para desenhar o schema. Cada afirmação aqui tem a fonte primária
citada, para quem quiser o detalhe — mas a leitura deste documento sozinho
deve bastar. Nada de schema, lift em produção, estado `contraste` ou
frontend foi implementado nesta fase inteira; `resultado/*.json` de
produção segue intacto.

---

## 1. A taxonomia — 10 eixos, e por que estes

`ritmo` · `atuacao` · `direcao_imagem` · `roteiro_estrutura` · `som_trilha`
· `tom_atmosfera` · `impacto_emocional` · `comparacoes` · `expectativa` ·
`critica_social` (+ `livre`, fallback).

Partiu de um gate com 8 eixos. Dois foram promovidos depois de medição
direta sobre os temas `livre` mais frequentes:

- **`expectativa`** — recorria em 15 de 15 filmes do gate, o único tema
  livre presente em TODOS. Cobre o que a pessoa esperava antes de assistir
  e por quê (hype, recomendação, expectativa frustrada ou superada).
- **`critica_social`** — recorria em 14 de 15 e era o maior contribuinte
  isolado do excesso de `livre` no bucket negativo. Cobre crítica ao que o
  filme REPRESENTA socialmente, distinta de crítica ao que o filme É.

Um terceiro candidato, `assistir` (motivo/circunstância de ter assistido),
foi **rejeitado**: inspeção de 30 exemplos mostrou 26 já cobertos pelos
eixos acima (14 por `expectativa`, 14 por `impacto_emocional`) — não era
eixo faltando, era artefato da taxonomia de 8 eixos.

Fonte: `TAXONOMIA_10.md`.

---

## 2. Votação de 3 — por que consenso em vez de passada única

Uma classificação de passada única mede o modelo contra si mesmo com
**26,5% de reprodutibilidade** — três quartos das vezes que se roda a MESMA
review de novo, o conjunto de eixos muda. Diagnóstico: o modelo não
confunde categoria (94,6% da oscilação é independente entre eixos, não
troca sistemática), ele HESITA perto do limiar em `impacto_emocional`,
`livre` e `tom_atmosfera` — julgamento de grau, não erro de categoria.
Oscilação independente e sem viés é exatamente o que votação por maioria
resolve.

**Arquitetura adotada:** 3 passadas independentes por review, eixo entra no
consenso se aparece em ≥2 de 3. Medido sob o prompt antigo: reprodutibilidade
sobe para **65,0%** (consenso de passadas 1,2,3 vs consenso de 2,3,4).
Reconfirmado sob `A_regra`: **66,5%** — o prompt mais permissivo em review
curta não piorou a estabilidade, hipótese testada e refutada.

Fonte: `VOTACAO_3.md`, `VOTACAO_3_A_REGRA.md` (Entrega 3).

---

## 3. O defeito de recall em review curta — como achado e como corrigido

**Achado.** Auditoria humana de 100 reviews (dono do projeto anotou, sem
ver o veredito do modelo) contra o consenso de votação: recall **0,35** em
reviews ≤200 chars (23,4% do corpus de produção) contra **0,88** acima de
400 chars, com **precisão estável em 0,87–0,93 em toda faixa**. O modelo
não trocava de eixo em texto curto — ele OMITIA eixo. 27 de 100 reviews
tinham recall zero (23 delas ≤200 chars); em 12 as três passadas foram
unânimes em `livre` quando havia eixo real — unanimidade não protegia
contra o defeito.

**Correção — `A_regra`.** Duas variantes de REGRAS testadas contra o mesmo
gabarito (a lista de eixos e as 10 definições nunca mudaram):

| | mudança | resultado |
|---|---|---|
| **A (promovida)** | brevidade não é ausência de conteúdo; `livre` por ASSUNTO, não por tamanho | recall ≤200 chars 0,35→0,61; reviews recall zero 27→5; consensos vazios 8→0 |
| B (rejeitada) | as regras de A + 6 exemplos de review curta | exemplos ANCORARAM o modelo — degradou review longa (recall 401-800: 0,888→0,847) e a concordância exata caiu abaixo do baseline |

`taxonomia_id` mudou de `11871105c0d3` para `ebab2667de74` — só o bloco
REGRAS, lista de eixos e definições byte-idênticas.

Fonte: `resultado/auditoria-acuracia/`, `scripts/variantes_prompt_curtas.py`
(arquivado), seção "Correção de recall em review curta" em `TAXONOMIA_10.md`.

---

## 4. Acurácia final — contra o gabarito FECHADO

O gabarito humano das 100 reviews teve uma inconsistência real: `impacto_emocional`
marcado para veredicto seco NEGATIVO ("não gostei") e deixado em branco para
POSITIVO ("I really liked it"). Corrigida em duas rodadas (2026-08-14, 32
alterações no total: 15 + 17), sob a régua fixada em
`resultado/auditoria-acuracia/REGRA_ANOTACAO.md` — `impacto_emocional`
exige EFEITO descrito, não veredicto, em nenhum dos dois polos. Reviews com
o eixo no gabarito: 66 → **38**.

**Contra este gabarito fechado — a medição vale, as anteriores (feitas
contra o gabarito ainda inconsistente) não:**

| | baseline (prompt antigo) | `A_regra` (produção) |
|---|---:|---:|
| precisão micro geral | 0,858 | 0,821 |
| recall micro geral | 0,715 | 0,763 |
| concordância exata | 0,180 | **0,130** |
| `impacto_emocional` P / R | 0,676 / 0,658 | **0,486** / 0,921 |
| `tom_atmosfera` P / R | 0,900 / 0,730 | 0,880 / 0,595 |
| `atuacao` P / R | 1,000 / 0,909 | 1,000 / 0,818 |
| reviews com recall zero | 25 | 7 |
| consensos vazios | 8 | 0 |

Bootstrap pareado (A_regra − baseline, B=5000): recall geral **+0,048**
(IC95 não cruza zero), recall ≤200 chars **+0,226** (IC95 não cruza zero,
o ganho que motivou a promoção segue sólido) — mas **precisão geral −0,037,
IC95 [−0,072, −0,003], NÃO cruza zero: perda estatisticamente significativa**,
e F1 geral tem IC95 que cruza zero (não dá para chamar de ganho livre).

**Isto CORRIGE uma conclusão anterior.** A validação que promoveu `A_regra`
reportou "sem perda de precisão detectável" — verdadeiro contra o gabarito
de então, que tinha a mesma assimetria que o PROMPT tem: a regra 2 de
`A_regra` lista literalmente `"não gostei"`, `"odiei"` como exemplos de
`impacto_emocional`. Um gabarito com a mesma falha não penalizava o prompt
por repeti-la. Corrigido o gabarito, a perda aparece: `impacto_emocional`
marca quase o dobro do que o gabarito sustenta (tp35/fp37 — 51% dos
positivos de A_regra são falsos).

`tom_atmosfera` (R 0,730→0,595) e `atuacao` (R 0,909→0,818) **persistem
idênticas** contra o gabarito limpo — não eram artefato da inconsistência.

Fonte: `scripts/acuracia_final.py`, `resultado/auditoria-acuracia/acuracia_final.json`.

---

## 5. A saturação de `impacto_emocional` — três hipóteses, três refutações

No corpus de produção (3990 reviews), `impacto_emocional` aparece em
**75,5%** das reviews — o eixo mais frequente, por larga margem. Isso
comprime o espaço de lift disponível: em `barbie`, o eixo ficou 65/70/70%
nos três buckets — **lift 0,000**.

Três correções tentadas, todas por instrução/reponderação, todas refutadas
por medição:

1. **Lift normalizado** (`(freq_top−freq_2o)/(1−freq_2o)`, log-odds). O
   quantum de discretização (1 review de diferença) é AMPLIFICADO pela
   normalização exatamente no regime saturado — 15× mais sensível a ruído
   com o 2º colocado em 95% do que em 25%. Sob o nulo de permutação, a
   normalização faz `impacto_emocional` sozinho responder por 62,6% do
   ruído (contra 13,9% do maior contribuinte sob o lift absoluto atual).
   Nenhuma das três métricas testadas atinge cobertura ≥18/35 filmes com
   ruído ≤35%; a métrica ATUAL (lift absoluto) é a menos ruim das três.
2. **Separar eixo de cobertura de eixo de contraste** (excluir os mais
   frequentes do cálculo de lift). Move o problema: filmes sem nenhum
   bullet de contraste sobem de 17 para 20 de 35 — os 3 que perdem tudo
   dependiam justamente de `impacto_emocional`/`roteiro_estrutura`.
3. **Definição apertada do eixo** (proibir veredicto seco explicitamente,
   nos dois pontos do prompt onde ele aparecia). Testada com votação de 3
   sobre as 100 auditadas: `impacto_emocional` foi de 75,5%→71,3%
   PROJETADO — segue saturado. Nos 13 veredictos secos que o gabarito
   humano desmarcou, a variante deixou de marcar em só **3 de 13**, e
   ADICIONOU marcação errada em 2 onde o prompt original acertava.

**Conclusão:** a saturação medida no corpus não é resolvida por
reponderação nem por instrução — mas a Seção 4 acima muda a leitura do
PORQUÊ. `impacto_emocional` tem precisão de 0,486 contra o gabarito
limpo: **51% das marcações de produção são falsas**. Corrigindo a
frequência observada por essa precisão e pelo recall medido (0,921) —
`freq_verdadeira ≈ freq_observada × precisão / recall` — a estimativa da
frequência REAL do eixo no corpus cai de 75,5% para **≈40%**. Isto é
**PROJEÇÃO, não medição** (n=100, um único ponto de precisão/recall, sem
intervalo de confiança propagado) — mas se a ordem de grandeza se
sustentar, a saturação relatada nas três tentativas acima é em boa parte
um artefato do MODELO over-marcando, não uma propriedade do corpus tão
extrema quanto 75,5% sugere. O terceiro teste (definição apertada) já
mostrou que o modelo não obedece a instrução textual para parar de
over-marcar — o que resolveria isso é matéria aberta (Seção 8).

Fonte: `scripts/metricas_lift.py`, `scripts/variante_impacto_estrito.py`,
`resultado/votacao-3/metricas_lift.json`.

---

## 6. O trade-off de margem — medido, não decidido

Nulo de permutação (2000 rodadas, embaralha bucket dentro de cada filme),
lift absoluto (L1, a métrica que sobreviveu à Seção 5):

| margem | pares acima (observado) | fração de ruído | filmes com ≥1 eixo acima |
|---|---:|---:|---:|
| 15pp | 41 | 62,7% | 22/35 |
| **20pp** | **21** | **41,1%** | **13/35** |
| 25pp | 12 | 29,4% | 9/35 |

A mesma margem de 20pp que era a recomendação (contra o corpus PRÉ-`A_regra`,
onde a fração de ruído era 34%) agora entrega 41,1% de ruído — a saturação
comprimiu o sinal disponível em toda margem. A pureza que 20pp entregava
antes (~34-36%) só volta perto de **25pp** hoje, ao custo de cobertura
(9/35 filmes, contra 13-18/35 antes).

**Não há margem única correta.** É pureza de lista contra cobertura, e o
trade-off ficou mais caro depois da correção de recall porque a frequência
média por eixo subiu. Decisão de produto, não resolvida aqui.

Fonte: `scripts/metricas_lift.py`, `VOTACAO_3_A_REGRA.md` (Entrega 4).

---

## 7. `contraste: valorativo` — frequência sob cada margem

"Sem contraste" = filme sem NENHUM eixo acima da margem.

| margem | sem contraste (de 35) | **`contraste: valorativo`** |
|---|---:|---:|
| 15pp | 13 | 22/35 (63%) |
| **20pp** | **22** | **13/35 (37%)** |
| 25pp | 26 | 9/35 (26%) |

Para referência histórica (pré-correção de recall, classificação de
passada única sobre 3948 reviews, `TAXONOMIA_10.md`): a 20pp, 14/35 (40%)
— o número atual (13/35, 37%) é bem próximo, apesar de toda a mudança de
frequência por eixo entre as duas medições. O estado `contraste: valorativo`
continua sendo o segundo mais comum do catálogo, não um caso de borda, em
qualquer margem testada.

`barbie`, o filme que deu nome ao estado: perdeu contraste em
`impacto_emocional` (22,5pp → 0,0pp, saturado) mas GANHOU em `critica_social`
(20,0pp, gradiente limpo 82,5%→47,5% do bucket negativo ao positivo) — o
contraste não desapareceu, migrou para um eixo mais fiel ao que a crítica do
filme fala.

Fonte: `VOTACAO_3_A_REGRA.md` (Entrega 5).

---

## 8. O que NÃO foi medido — em aberto para o desenho do schema

- **Por que o modelo over-marca `impacto_emocional` mesmo sob instrução
  explícita contra isso, em dois pontos do prompt.** Três tentativas de
  correção por prompt falharam (Seção 5). Se a frequência real for ~40% e
  não 75,5% (Seção 4/5), vale investigar arquitetura em vez de wording —
  ex.: um segundo passe de VERIFICAÇÃO que audite as marcações de
  `impacto_emocional` de um primeiro passe contra a régua de
  `REGRA_ANOTACAO.md`, em vez de pedir para o classificador original ser
  mais rigoroso consigo mesmo.
- **A precisão de `impacto_emocional` medida (0,486) vem de n=100.** Não
  há intervalo de confiança propagado para a projeção de frequência real
  da Seção 5; ela é direcional, não um número para citar com precisão.
- **Os outros 9 eixos não passaram pela mesma auditoria de gabarito.** Só
  `impacto_emocional` teve inconsistência achada e corrigida — não porque
  os outros estejam confirmados limpos, mas porque a busca dirigida que os
  varreu (palavra-gatilho) não achou padrão do mesmo tamanho. Não é prova
  de ausência.
- **Margem de lift**: nenhuma recomendação final foi adotada (Seção 6) —
  é decisão de produto pendente.
- **`fracao_livre` e `eixos_por_review` do corpus inteiro NÃO foram
  recalculados sob o gabarito corrigido** — a correção rodou só sobre as
  100 auditadas. O corpus de 3990 continua classificado sob `A_regra` como
  estava; nenhuma reclassificação foi feita nesta fase.
- **Nenhuma medição de custo de uma eventual arquitetura de verificação**
  (segundo passe) foi feita — é especulação de próximo passo, não plano.

---

## Reprodução

```bash
python scripts/acuracia_final.py               # Seção 4
python scripts/metricas_lift.py                 # Seções 5-6
python scripts/comparacao_a_regra.py             # Seção 7 (dados)
python scripts/variante_impacto_estrito.py comparar   # Seção 5, hipótese 3
```

Testes: `tests/test_promocao_a_regra.py`, `tests/test_variantes_prompt.py`,
`tests/test_variante_impacto_estrito.py`, `tests/test_previsao_frequencia.py`.
