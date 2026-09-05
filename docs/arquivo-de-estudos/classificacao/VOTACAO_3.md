# Classificação por votação de 3 — medição completa

**Data:** 2026-08-10 · **Natureza:** medição, zero mudança de produção · **Custo real:** US$ 0,39 (4 passadas completas, 3990 reviews cada)

Nenhum parâmetro de coleta, seleção, schema, frontend ou prompt foi tocado.
`resultado/*.json` intacto. A taxonomia é a mesma (`taxonomia_id
11871105c0d3`, idêntica à de `TAXONOMIA_10.md`) — só o MECANISMO de decisão
mudou: de "uma chamada decide" para "três chamadas votam, ≥2/3 vence".
Script: `scripts/votacao_3.py`, reusa `scripts/classificar_10.py` por
import direto (prompt, eixos, amostra, adaptador, nulo de permutação —
nenhuma lógica duplicada).

---

## O veredito, antes dos números

**A votação funciona para o que foi desenhada — estabiliza a classificação
individual, de 26,5% para 65,0% de reprodutibilidade exata — mas a previsão
específica sobre `tom_atmosfera` não se confirmou, e o motivo é instrutivo.**

**Entrega 3 é o resultado mais importante:** rodando uma QUARTA passada
independente e comparando o consenso de (1,2,3) contra o consenso de
(2,3,4), **65,0% das 3990 reviews têm exatamente o mesmo conjunto
consensual** — mais que o dobro dos 26,5% da passada única. A votação não
deslocou o problema, resolveu boa parte dele. Não é 100%: ainda sobra 35%
de instabilidade residual, e isso fica registrado, não escondido atrás da
melhora.

**A previsão de `tom_atmosfera` (Entrega 5) não se confirmou** — a
frequência sob consenso é **26,2%**, não os ~14,5% previstos, e ele
continua encabeçando linha em 4 filmes (não caiu para menos que os 3
originais). A razão é matemática, não um erro de medição: a previsão vinha
da Entrega 3 de `ESTABILIDADE_AGREGADA.md`, que mede o **núcleo = interseção
de exatamente 2 execuções específicas** (A∩B, equivalente a exigir 2 de 2)
— um critério muito mais estrito que **maioria de 2 de 3**, que só precisa
de concordância entre QUAISQUER duas das três chamadas. A estatística
usada para prever não era a mesma que a política de votação aplica, e as
duas divergem o bastante para inverter a conclusão prática sobre este eixo
específico. Registrado como correção de método, não escondido.

**O que a votação de fato mudou, e onde:** o efeito isolado da votação
(controlando por crescimento do corpus) é pequeno para quase todo eixo
individual (a maioria fica dentro de ±1,5pp) — **exceto `livre`, que cai
4,9pp**. A votação limpa principalmente o RESÍDUO, não redesenha a
frequência dos eixos nomeados. `fracao_livre` (definição estrita, `==
["livre"]`) vai de **4,81% → 4,19% (só corpus) → 3,76% (+ votação)**.

**Efeito colateral no schema que pesa contra a votação, não a favor:** a
fração de filmes com bucket cheio que caem em `contraste: valorativo` na
margem de 20pp **sobe** de 31,8% (7/22, medição original) para **40,7%
(11/27)** sob consenso. A votação, ao filtrar contagens individuais
ruidosas, também comprime os lifts MÁXIMOS observados por filme — menos
outliers de eixo único puxado por 1-2 reviews. Menos ruído na classificação
custa alguns pares de contraste genuíno-mas-marginal.

---

## Entrega 1 — Classificação por votação

3990 reviews (a amostra de PRODUÇÃO atual — cresceu de 3948 desde
`TAXONOMIA_10.md`: v1.9.5/v1.9.6 fecharam mais buckets, 87/105 a 40 agora
contra os que geraram a medição original), três passadas independentes,
**0 falhas em 11970 chamadas**.

| | passe 1 | passe 2 | passe 3 |
|---|---:|---:|---:|
| tempo | 643s (10,7 min) | 639s (10,7 min) | 671s (11,2 min) |
| taxa | 6,2/s | 6,2/s | 5,9/s |
| custo | US$ 0,1263 | US$ 0,0889 | US$ 0,0889 |
| cache hit | 86,9% | 93,5% | 93,5% |

Custo Entrega 1: **US$ 0,3041** (contra a estimativa de ~36 centavos — mais
barato, cache de prefixo ficou quente rodando as três sequenciais no mesmo
processo, sem intervalo).

Consenso: eixo entra se ≥2/3 votos. **3990/3990 reviews com os três passes
completos** — nenhuma ficou de fora por falha parcial. Persistido em
`resultado/votacao-3/consenso.jsonl`: conjunto final, contagem de votos por
eixo, as três classificações brutas (`eixos_por_passe`), `taxonomia_id`.

---

## Entrega 2 — O que a votação mudou

Três colunas de comparação: **antiga** (passada única, corpus de 3948 —
`resultado/taxonomia-10/`), **passe1** (uma passada isolada sobre o corpus
ATUAL de 3990 — isola o efeito do crescimento do corpus), **consenso**
(isola o efeito da votação, mesma base do passe1).

| eixo | antiga | passe1 (corpus atual) | consenso | Δ corpus (pp) | Δ votação (pp) |
|---|---:|---:|---:|---:|---:|
| `ritmo` | 32,7% | 35,1% | 33,7% | +2,4 | -1,4 |
| `atuacao` | 26,1% | 29,0% | 29,1% | +2,9 | +0,1 |
| `direcao_imagem` | 29,8% | 32,9% | 32,5% | +3,0 | -0,4 |
| `roteiro_estrutura` | 43,2% | 43,8% | 44,0% | +0,5 | +0,3 |
| `som_trilha` | 12,6% | 13,8% | 13,5% | +1,2 | -0,3 |
| `tom_atmosfera` | 25,3% | 27,6% | 26,2% | +2,2 | **-1,4** |
| `impacto_emocional` | 46,1% | 45,6% | 45,9% | -0,6 | +0,4 |
| `comparacoes` | 39,2% | 44,9% | 43,4% | **+5,7** | -1,5 |
| `expectativa` | 27,6% | 28,9% | 27,6% | +1,4 | -1,3 |
| `critica_social` | 25,4% | 25,5% | 24,5% | +0,1 | -1,0 |
| **`livre`** | **17,8%** | **17,3%** | **12,4%** | -0,5 | **-4,9** |

**A coluna que decide a leitura é "Δ votação"**: com exceção de `livre`,
todo eixo fica dentro de ±1,5pp — a votação não redistribui peso entre
eixos NOMEADOS de forma relevante. O efeito real e grande da votação é
sobre `livre`: -4,9pp, de longe a maior mudança da tabela. `comparacoes`
teve o maior movimento total (+4,2pp antiga→consenso), mas **quase todo
vem do corpus crescer** (+5,7pp), não da votação (-1,5pp) — os dois efeitos
puxam em direções opostas.

**`fracao_livre`** (definição estrita — `eixos == ["livre"]`, a MESMA de
`TAXONOMIA_10.md`, não uma mais frouxa — ver nota de correção abaixo):

| | n | fração |
|---|---:|---:|
| antiga (passada única, corpus 3948) | 190/3948 | **4,81%** |
| passe1 (corpus atual, passada única) | 167/3990 | 4,19% |
| consenso | 150/3990 | **3,76%** |

**Categoria nova, sem equivalente na passada única:** `consenso_vazio`
(nem `livre` nem eixo nenhum alcança 2/3 votos → conjunto final `[]`) —
**27/3990 (0,68%)**. É "abstenção coletiva": as três passadas discordam
tanto entre si que nem "não classificável" reúne maioria. Não é a mesma
coisa que `fracao_livre` e contá-la junto infla o número — nota de
correção: uma versão inicial deste script fazia exatamente essa mistura
(chegou a 5,22%/5,27% de "antiga" contra o 4,81% publicado); corrigido
antes de qualquer número ser reportado adiante.

**Eixos por review:** antiga 3,08 (mediana 3) → passe1 3,27 → consenso
3,20. Sobe com o corpus, cai um pouco com a votação — consistente com
votação removendo atribuições de voto único.

**Mudança de conjunto, nas 3183 reviews com chave em comum entre antiga e
consenso** (a antiga é quase toda um subconjunto do corpus atual, mas nem
toda review sobrevive idêntica à re-seleção sob bruto maior):

| | n | fração |
|---|---:|---:|
| conjunto idêntico | 1294 | 40,7% |
| ganhou eixo (só cresceu) | 583 | 18,3% |
| perdeu eixo (só encolheu) | 752 | 23,6% |
| ganhou E perdeu | 554 | 17,4% |

**Voto único que não sobrevive ao consenso, por eixo** (fração das vezes
que o eixo apareceu em ALGUMA passada que era só 1 de 3 votos — o número
que decide se a frequência publicada estava sustentada por ruído):

| eixo | menções (≥1 voto) | só 1/3 | fração |
|---|---:|---:|---:|
| **`tom_atmosfera`** | 1642 | 598 | **36,4%** |
| `expectativa` | 1614 | 511 | 31,7% |
| `critica_social` | 1394 | 418 | 30,0% |
| `comparacoes` | 2358 | 625 | 26,5% |
| `ritmo` | 1739 | 394 | 22,7% |

`tom_atmosfera` tem a MAIOR fração de voto único de todos os eixos — mais
de 1 em cada 3 vezes que aparece em alguma passada, é só numa. Isso é
consistente com `ESTABILIDADE_AGREGADA.md` (ele era o eixo com maior
rotatividade "invisível" na frequência agregada). Mas alta rotatividade
individual não implica frequência final baixa — ver Entrega 5.

---

## Entrega 3 — Estabilidade da votação

Quarta passada independente, **0 falhas em 3985 chamadas** (5 já feitas no
smoke test antes do lote principal). Consenso A = maioria(1,2,3) — o
oficial da Entrega 1. Consenso B = maioria(2,3,4) — o mesmo mecanismo,
trocando um dos três votos por uma execução nova.

| | valor |
|---|---:|
| reviews comparadas | 3990 |
| **fração com consenso idêntico (A = B)** | **65,0%** |
| fração idêntica, passada única (referência) | 26,5% |

**A votação de 3 é substancialmente mais reprodutível que a passada
única — 2,45× — mas não elimina a instabilidade.** 35% das reviews
mudariam de consenso se um dos três votos fosse trocado por uma execução
nova. Isso é o PISO real da precisão que qualquer decisão de schema
baseada nesta classificação pode ter: mesmo com votação, não é seguro tratar
o consenso como "a" classificação definitiva de uma review individual —
é uma estimativa consideravelmente melhor, não uma correção completa. Para
números AGREGADOS (frequência por bucket, lift), 65% de reprodutibilidade
por review já é suficiente para as médias serem estáveis (ver Entrega 2),
mas para citar o veredito de UMA review específica, o mesmo cuidado que
motivou a auditoria humana continua valendo.

Custo desta entrega: US$ 0,0888 (passe 4 sozinho).

---

## Entrega 4 — Recalibração dos números do schema

Sobre o consenso, 3990 reviews, 35 filmes (27 com os 3 buckets a 40, 8 com
algum bucket abaixo — subiu de 22/13 para 27/8 desde `TAXONOMIA_10.md`,
efeito da passada seletiva v1.9.6, **não** da votação — ver nota de
confusão abaixo).

### `fracao_livre`

| | n | fração | IC95 |
|---|---:|---:|---|
| global | 150/3990 | **3,76%** | [3,22; 4,39] |
| negativas | 63/1322 | 4,77% | [3,74; 6,05] |
| medianas | 41/1329 | 3,09% | [2,28; 4,16] |
| positivas | 46/1339 | 3,44% | [2,59; 4,55] |

Contra 4,81% da medição original — queda de 1,05pp, mas **confundida**
entre corpus (4,19%, a maior parte) e votação (3,76%, o resto) — ver nota
de decomposição.

### Nulo de permutação — recalibração da margem

| margem | observado | nulo (média) | nulo p95 | % que passaria por acaso |
|---|---:|---:|---:|---:|
| 10pp | 111 | 70,4 | 83 | 63% |
| 15pp | 61 | 27,6 | 36 | 45% |
| **20pp** | **28** | **9,6** | **15** | **34%** |
| 25pp | 14 | 3,7 | 7 | 26% |

Contra a medição original (10pp 59%, 15pp 50%, **20pp 31%**, 25pp 23%): a
margem de **20pp continua sendo a recomendação que a lógica do nulo
sustenta** — 34% de ruído sob consenso está na mesma ordem de grandeza dos
31% originais, a mesma folga relativa entre margens se preserva. **A
votação não muda a recomendação de margem por este critério.**

### Contraste — onde a votação de fato pesa

| margem | grupo | sem contraste (medição original) | sem contraste (consenso) |
|---|---|---:|---:|
| 15pp | 3 buckets a 40 | 3/22 (14%) | 3/27 (11%) |
| 15pp | algum sub-40 | 5/13 (38%) | 2/8 (25%) |
| **20pp** | **3 buckets a 40** | **7/22 (32%)** | **11/27 (41%)** |
| 20pp | algum sub-40 | 7/13 (54%) | 6/8 (75%) |
| 25pp | 3 buckets a 40 | — | 20/27 (74%) |
| 25pp | algum sub-40 | — | 6/8 (75%) |

**Na margem recomendada (20pp), a fração de filmes cheios sem contraste
SOBE de 32% para 41% sob votação.** A 15pp ela desce (14%→11%) — melhora.
A leitura: votação reduz atribuições isoladas ruidosas, o que às vezes
elimina o único par que dava a um filme seu lift acima de 20pp — contraste
que passava por causa de UM voto que não sobreviveria a uma segunda
opinião. Não é um defeito da votação: é exatamente o tipo de correção que
ela foi desenhada para fazer, só que o efeito colateral é reduzir a
COBERTURA do schema, não só sua acurácia.

### Nota de confusão — corpus vs. votação, declarada como pedido

O `n_filmes_todos_buckets_40` foi de **22 para 27** entre a medição
original e esta — efeito quase certo da passada seletiva `by/added-earliest`
(v1.9.6) e do fechamento de buckets (v1.9.5), **não da votação**: a votação
não busca review nenhuma, só reclassifica o que já estava selecionado. As
duas causas (corpus maior + votação) afetam o número de filmes com
contraste de formas diferentes e não foi possível separá-las por filme
individual sem reclassificar a passada única sobre o corpus atual inteiro
(o que a Entrega 2 já faz via `passe1`, mas o nulo de permutação e a
margem recomendada não foram recalculados separadamente sobre passe1 —
ficaria como uma quarta rodada de análise, não pedida). **Declarado, não
resolvido**: o número de filmes sem contraste a 20pp mistura as duas
causas.

---

## Entrega 5 — `tom_atmosfera` sob a nova régua

**A previsão não se confirmou.** `ESTABILIDADE_AGREGADA.md` previu queda de
~25% para ~14,5% com base no "núcleo" (interseção de exatamente 2
execuções). Sob consenso de 3 (maioria de 2 de 3, critério mais frouxo):

| | valor |
|---|---:|
| frequência sob consenso | **26,17%** |
| frequência `som_trilha` (referência, eixo mais fraco) | 13,51% |
| diferença | **+12,66pp** — mais do que o DOBRO de `som_trilha`, não perto dele |
| filmes onde encabeça linha (≥20pp, é o eixo de maior lift do filme) | **4** (`cats-2019`, `cure`, `longlegs`, `obsession-2026`) — era 3 |
| distribuição de votos: fração 3/3 (unânime) | **64,2%** |
| fração 2/3 | 35,8% |

**Por que a previsão errou, precisamente:** núcleo (Entrega 3 de
`ESTABILIDADE_AGREGADA.md`) exige que o eixo apareça em AMBAS as duas
execuções específicas comparadas — matematicamente equivalente a "2 de 2".
Maioria de 3 exige "2 de QUAISQUER 3" — um bar mais baixo, porque há três
chances de formar o par vencedor em vez de uma só. Um eixo com oscilação
alta mas SEM viés sistemático (o diagnóstico do achado anterior: 94,6% de
oscilação independente, não troca) tende a formar ALGUM par 2-de-3 com
mais frequência do que forma um par 2-de-2 específico — é aritmética de
combinatória, não uma propriedade nova do eixo. A previsão comparou duas
estatísticas diferentes como se fossem a mesma.

**Conclusão para a decisão futura (não tomada aqui, por instrução):**
`tom_atmosfera` sob votação de 3 se comporta como um eixo ESTABELECIDO,
não como um candidato fraco — frequência alta (26,2%, 4º mais frequente
dos 10), maioria unânime na maior parte de suas ocorrências (64,2%), e
CRESCEU o número de filmes onde encabeça linha (3→4). O caso para removê-lo
enfraqueceu, não fortaleceu, com esta medição. `som_trilha` continua sendo
o eixo estruturalmente mais fraco por qualquer critério medido até aqui.

---

## Custo total

| entrega | passadas | custo | tempo |
|---|---|---:|---:|
| 1 (passadas 1-3) | 3 × 3990 | US$ 0,3041 | 1953s (32,6 min) |
| 3 (passada 4) | 1 × 3990 | US$ 0,0888 | 2641s (44 min — ver nota) |
| **total** | 4 × 3990 = 15960 chamadas | **US$ 0,3929** | ~77 min |

**Nota sobre o tempo da passada 4:** um estol de rede entre os itens 400 e
600 (de 6,1/s para 0,3/s por ~34 min) inflou o tempo total — sem esse
episódio, a passada 4 teria levado os mesmos ~11 min das três primeiras.
Nenhuma chamada falhou (0/3990); o mecanismo de retentativa (3 tentativas,
backoff) absorveu o problema sem intervenção. Custo não foi afetado —
retentativa não gasta token extra além do necessário para completar.

## Reprodução

```bash
python scripts/votacao_3.py amostra
python scripts/votacao_3.py passe 1   # e 2, 3, 4 — resumível, idempotente
python scripts/votacao_3.py consenso
python scripts/votacao_3.py relatorio
python scripts/votacao_3.py estabilidade_consenso
```

Saídas em `resultado/votacao-3/`: `amostra.json`, `passe_{1,2,3,4}.jsonl`,
`consenso.jsonl`, `relatorio.json`, `estabilidade_consenso.json`.
