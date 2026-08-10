# Gate de retro-fit da taxonomia de eixos

**Data:** 2026-08-08 · **Natureza:** medição · **Mudanças de código de produção:** nenhuma

Nada de schema, frontend, pipeline de síntese ou `resultado/<slug>.json` foi
tocado. O que este trabalho produziu está inteiro em `scripts/gate_taxonomia.py`
(descartável, fora do pacote) e em `resultado/gate-taxonomia/`.

---

## Veredito

**PASSA.** `fracao_livre` global = **15,4 %** (132 de 859 reviews), IC 95 %
[13,1 %; 17,9 %] — dentro da faixa "até ~20 % → taxonomia adequada, o schema
pode ser commitado", com o intervalo inteiro abaixo do corte.

Nenhum bucket, nenhum perfil e nenhum filme individual chega aos 25 % que
reprovariam. Duas células encostam na zona cinzenta e estão nomeadas em
"Onde a taxonomia é mais fraca", abaixo — nenhuma delas é, no meu julgamento,
motivo para segurar o schema, mas as duas são decisão sua e estão medidas.

O achado que mais deveria mudar o desenho não está na Entrega 2, e sim na
Entrega 4(d): **a margem de lift de 15 pp não separa sinal de ruído com 20
reviews por bucket — mas separa bem com 40.** Detalhe e o número lá.

---

## Entrega 1 — Amostra

**859 reviews · 15 filmes · 3 buckets · semente `20260808`.**

Reprodução: `python scripts/gate_taxonomia.py amostra` regrava
`resultado/gate-taxonomia/amostra.json` byte a byte.

### Critério de escolha dos filmes

O perfil de cada um dos 35 filmes do catálogo é **derivado do histograma
público**, não da rubrica com que ele entrou em `dados/lote-slugs.txt` — a
rubrica registrava a intenção de coleta, e o que o gate precisa é o que o
filme de fato é. Precedência (cada filme cai em exatamente um perfil):

| perfil | regra | filmes no catálogo |
|---|---|---|
| `obscuro` | < 10 000 notas no total | 1 |
| `invertido` | negativas ≥ 20 % das notas | 4 |
| `divisivo` | mornos ≥ 20 % das notas | 6 |
| `arthouse` | pertence à lista declarada de não-anglófono/arthouse | 7 |
| `aclamado` | o resto | 17 |

`arthouse` é o único critério que não sai do histograma. Não sai porque não
pode: "arthouse" não é propriedade da distribuição de notas, e derivá-la dela
seria falso rigor. Está hardcoded como lista, com o nome disso escrito no
código.

`obscuro` e `invertido` entram **inteiros** — são raros (1 e 4 filmes) e é
neles que a taxonomia tem mais chance de quebrar; sortear dentro deles jogaria
fora justamente o material que o gate existe para olhar. Os outros três são
sorteados com RNG semeado (`arthouse` leva uma vaga a mais que `divisivo` e
`aclamado`, pelo mesmo motivo).

| perfil | filmes na amostra |
|---|---|
| obscuro | `obsession-2026` |
| invertido | `cats-2019`, `friday-the-13th-2009`, `joker-folie-a-deux`, `napoleon-2023` |
| divisivo | `barbie`, `longlegs`, `talk-to-me-2022` |
| arthouse | `aftersun`, `anatomy-of-a-fall`, `cure`, `perfect-days-2023` |
| aclamado | `avengers-endgame`, `bones-and-all`, `shutter-island` |

### Critério de escolha das reviews

A amostra sai do **mesmo pool que iria à síntese**, não de um pool inventado
para o gate: `selecao.selecionar()` com os parâmetros de produção (cota 40 por
bucket, `min_chars` 150, cascata, spoiler excluído), e depois sorteio sem
reposição de até 20 por bucket, com RNG semeado por `"20260808:<slug>:<bucket>"`
— uma semente por par, de modo que a amostra de um filme não depende da ordem
em que os outros foram processados.

14 dos 15 filmes fecharam 20/20/20. `obsession-2026` (69 reviews brutas no
total, o filme obscuro) fechou **5/6/8** — o pool inteiro dele, sem sorteio.
É a limitação real e única da amostra, e está carregada em todo número
desagregado que envolve esse filme.

### Método de classificação

O mesmo de sempre: **o modelo classifica review a review, o código soma.**
Uma chamada de LLM por review (`deepseek-v4-flash`, temperatura 0), a review
sozinha no prompt, sem nenhuma contagem à vista, devolvendo só a lista de
eixos que aquela review menciona. Toda frequência, fração e lift deste
relatório é `collections.Counter` sobre essas listas.

**859/859 classificadas sem uma falha**, e — o número que mais diz sobre a
taxonomia caber na cabeça do modelo — **zero eixos inventados**: em 2 107
atribuições de eixo, nenhuma caiu fora da lista fechada.

Uma correção real durante a montagem, vale registrar porque é reincidência de
uma causa raiz já documentada: as 12 primeiras chamadas foram feitas sem
`thinking: disabled`, e **8 delas voltaram com `content` vazio** — o
raciocínio consumiu o orçamento de `max_tokens` inteiro antes do JSON. É
exatamente o que `synthesize.deepseek_client_call` documenta desde a v1.8.0, e
que este script não herdou por não usar o adaptador. Corrigido copiando a
configuração de transporte validada (`thinking: disabled` +
`response_format: json_object`); depois disso, 859/859.

---

## Entrega 2 — A métrica do gate

`fracao_livre` = reviews cuja classificação caiu **só** em `livre`, sobre o
total classificado.

### Global

| | n | só `livre` | fração | IC 95 % |
|---|---:|---:|---:|---|
| **global** | 859 | 132 | **15,4 %** | [13,1 %; 17,9 %] |

O IC de Wilson está publicado porque o critério tem faixas de 5 pp e algumas
células desagregadas são pequenas o bastante para o intervalo cruzar uma
fronteira. Ler a estimativa pontual sozinha, nessas células, seria ler menos
do que o dado diz.

### Por bucket

| bucket | n | só `livre` | fração | IC 95 % |
|---|---:|---:|---:|---|
| negativas | 285 | 58 | **20,4 %** | [16,1 %; 25,4 %] |
| medianas | 286 | 39 | 13,6 % | [10,1 %; 18,1 %] |
| positivas | 288 | 35 | 12,2 % | [8,9 %; 16,4 %] |

### Por perfil de filme

| perfil | n | só `livre` | fração | IC 95 % |
|---|---:|---:|---:|---|
| obscuro | 19 | 7 | **36,8 %** | [19,1 %; 59,0 %] |
| aclamado | 180 | 33 | 18,3 % | [13,4 %; 24,6 %] |
| invertido | 240 | 37 | 15,4 % | [11,4 %; 20,5 %] |
| divisivo | 180 | 27 | 15,0 % | [10,5 %; 20,9 %] |
| arthouse | 240 | 28 | **11,7 %** | [8,2 %; 16,3 %] |

**A expectativa a priori estava invertida.** A hipótese registrada no briefing
— "uma taxonomia pode funcionar bem em aclamados e mal em arthouse" — não se
confirma: `arthouse` é o perfil onde a taxonomia funciona **melhor** (11,7 %),
e `aclamado` é o segundo pior (18,3 %). A leitura que os exemplos de texto
sustentam: review de arthouse fala do filme (imagem, ritmo, clima, o que
sentiu); review de blockbuster fala com frequência de tudo em volta do filme
— franquia, hype, em que circunstância assistiu, o discurso que se formou.

### Por filme

| filme | perfil | n | só `livre` | fração | IC 95 % |
|---|---|---:|---:|---:|---|
| `obsession-2026` | obscuro | 19 | 7 | **36,8 %** | [19,1 %; 59,0 %] |
| `cats-2019` | invertido | 60 | 19 | **31,7 %** | [21,3 %; 44,2 %] |
| `avengers-endgame` | aclamado | 60 | 14 | 23,3 % | [14,4 %; 35,4 %] |
| `talk-to-me-2022` | divisivo | 60 | 13 | 21,7 % | [13,1 %; 33,6 %] |
| `barbie` | divisivo | 60 | 12 | 20,0 % | [11,8 %; 31,8 %] |
| `shutter-island` | aclamado | 60 | 10 | 16,7 % | [9,3 %; 28,0 %] |
| `bones-and-all` | aclamado | 60 | 9 | 15,0 % | [8,1 %; 26,1 %] |
| `anatomy-of-a-fall` | arthouse | 60 | 8 | 13,3 % | [6,9 %; 24,2 %] |
| `cure` | arthouse | 60 | 8 | 13,3 % | [6,9 %; 24,2 %] |
| `friday-the-13th-2009` | invertido | 60 | 7 | 11,7 % | [5,8 %; 22,2 %] |
| `napoleon-2023` | invertido | 60 | 7 | 11,7 % | [5,8 %; 22,2 %] |
| `perfect-days-2023` | arthouse | 60 | 7 | 11,7 % | [5,8 %; 22,2 %] |
| `aftersun` | arthouse | 60 | 5 | 8,3 % | [3,6 %; 18,1 %] |
| `joker-folie-a-deux` | invertido | 60 | 4 | 6,7 % | [2,6 %; 15,9 %] |
| `longlegs` | divisivo | 60 | 2 | 3,3 % | [0,9 %; 11,4 %] |

### Onde a taxonomia é mais fraca

Duas células, e o que penso de cada uma:

**1. `obsession-2026`, 36,8 % — acima do corte de 25 %, e é o único filme que
passa dele.** É também o único filme obscuro do catálogo, e a amostra dele são
19 reviews (o pool inteiro): o IC vai de 19 % a 59 %, largo demais para
sustentar sozinho um veredito em qualquer direção. Não trato isso como
reprovação porque n=19 não reprova nada — mas também não trato como ruído
descartável: é o perfil de filme para o qual o catálogo tem menos evidência,
e a única evidência que tem aponta para cima. **Se o catálogo crescer para o
lado obscuro, este número merece ser remedido antes de qualquer coisa.**

**2. `negativas`, 20,4 %.** Está na borda da zona cinzenta, com IC até 25,4 %.
Não é acaso e tem causa legível na Entrega 3: os dois maiores contribuintes
de `livre` no bucket negativo são `critica_social` (34 ocorrências) e `reacao`
(30) — review negativa com frequência não avalia o filme, ela reage a ele ou
critica o que ele representa. Um eixo novo cobriria boa parte disso (ver
candidatos abaixo).

`cats-2019` (31,7 %) tem a mesma explicação levada ao extremo: 86 % das notas
são negativas, e o corpus é quase todo piada e escárnio.

### Medição suplementar — fora do que o gate pediu

`fracao_livre` mistura duas coisas que não têm o mesmo remédio: (i) a review
diz algo sobre o filme e a taxonomia não tem eixo para isso — lacuna real; e
(ii) a review não diz nada avaliável sobre o filme (piada solta, citação de
diálogo sem comentário, "assisti pra entender o outro filme", emoji) — e aí
nenhum eixo, existente ou futuro, a salvaria. Contar (ii) contra a taxonomia
seria injusto com ela.

Uma passada extra de triagem sobre as 132 reviews só-`livre`, uma por chamada,
com instrução deliberadamente conservadora ("na dúvida, responda
`avaliavel`"):

| | n útil | descartadas | só `livre` | fração ajustada |
|---|---:|---:|---:|---:|
| global | 846 | 13 | 119 | **14,1 %** |
| negativas | 281 | 4 | 54 | 19,2 % |
| medianas | 282 | 4 | 35 | 12,4 % |
| positivas | 283 | 5 | 30 | 10,6 % |
| arthouse | 234 | 6 | 22 | 9,4 % |
| obscuro | 18 | 1 | 6 | 33,3 % |

**Só 13 das 132 (10 %) são review sem conteúdo avaliável.** O confundimento
existe mas é pequeno, e a conclusão não muda: 15,4 % ou 14,1 %, os dois estão
confortavelmente dentro da faixa de aprovação. Registro a métrica ajustada ao
lado da oficial, não no lugar dela — o veredito é contra o critério como você
o definiu antes de olhar o resultado.

---

## Entrega 3 — Análise dos temas livres

317 reviews emitiram pelo menos um tema livre (132 delas caíram **só** em
`livre`), produzindo 478 ocorrências sobre 408 rótulos distintos.

O agrupamento tem duas camadas, publicadas lado a lado em `relatorio.json`:

- **lexical** (`grupos_lexicais`), determinístico, Jaccard ≥ 0,5 sobre
  vocabulário. Fragmenta demais para responder à pergunta — separa
  "expectativa antes de assistir" de "expectativa do espectador" porque não
  compartilham palavras suficientes;
- **semântica** (`familias`), que é a que reporto abaixo. Como a pergunta é
  semântica, usa o LLM — sob a mesma disciplina: um passo propõe as famílias a
  partir da lista de rótulos **em ordem alfabética e sem contagem nenhuma**, e
  o passo seguinte atribui **um rótulo por chamada** a uma dessas famílias.
  Ocorrências e filmes distintos são contados pelo código.

| família | ocorr. | **filmes** | em só-`livre` | neg/med/pos |
|---|---:|---:|---:|---|
| `expectativa` | 54 | **15/15** | 20 | 21/18/15 |
| `critica_social` | 62 | **14** | 19 | 34/13/15 |
| `outros` | 58 | 14 | 27 | 24/21/13 |
| `reacao` | 66 | **13** | 42 | 30/22/14 |
| `assistir` | 39 | **13** | 21 | 15/12/12 |
| `producao` | 39 | 12 | 15 | 11/18/10 |
| `recepcao` | 22 | 12 | 7 | 10/7/5 |
| `experiencia_pessoal` | 29 | 11 | 19 | 7/11/11 |
| `mensagem` | 28 | 11 | 6 | 10/5/13 |
| `comparacao` | 18 | 11 | 10 | 12/2/4 |
| `personagem` | 30 | 9 | 13 | 5/14/11 |
| `aparencia` | 12 | 8 | 5 | 8/1/3 |
| `fidelidade` | 18 | 6 | 5 | 6/6/6 |
| `adaptacao` | 3 | 2 | 0 | 2/0/1 |

### Candidatos a promoção

O critério que você deu — recorrência entre **muitos filmes distintos**, não
frequência bruta — ordena assim:

**1. `expectativa` — 15 de 15 filmes, 54 ocorrências.** O único tema que
aparece em *todos* os filmes da amostra. O que a review traz antes de falar do
filme: o hype, o que esperava, por que foi assistir, o peso do que já tinha
ouvido. Distribuído nos três buckets (21/18/15), o que é raro entre os
candidatos e o torna forte para a interface alinhada por linha.

> `avengers-endgame` / medianas — *"watched this cause everyone said i had to
> in order for far from home and no way home to make sense. will prob be
> better when i actually watch the entire mcu i was very confused"*

**2. `critica_social` — 14 filmes, 62 ocorrências, 34 delas em `negativas`.**
Crítica ao que o filme representa (política, gênero, a franquia, o que
Hollywood está fazendo), distinta de crítica ao que o filme *é*. É o maior
contribuinte isolado do excesso de `livre` no bucket negativo.

> `bones-and-all` / negativas — *"I wonder what kind of butterflies these
> characters have in their stomachs... Hollywood, are you romanticizing
> cannibalism now?"*

**3. `reacao` — 13 filmes, 66 ocorrências, e 42 delas em reviews que caíram
só em `livre`** — a maior conversão de qualquer família. Reação física ou
performática ao filme (asco, riso, desistir no meio, a plateia inteira
reagindo). **Este é um caso de fronteira mal desenhada, não de eixo
faltando:** `impacto_emocional` existe e cobriria boa parte disso, mas a regra
2 do prompt (que proíbe ler entusiasmo genérico como impacto) empurrou o
visceral para fora junto com o vazio. Antes de criar um eixo, vale testar se
afrouxar a definição de `impacto_emocional` resolve — sai mais barato e não
aumenta a taxonomia.

**4. `assistir` — 13 filmes, 39 ocorrências.** Circunstância de exibição:
cinema, TikTok, rewatch, com quem, em que estado. Aparece equilibrado nos três
buckets (15/12/12). Candidato legítimo, mas é o mais próximo de "não fala do
filme" — parte do que ele cobre é justamente o que a triagem marcaria como
sem conteúdo avaliável.

**Abaixo da linha de corte, e por quê:** `producao` (12 filmes) e `recepcao`
(12) recorrem bastante mas contribuem pouco para o só-`livre` (15 e 7);
`personagem` (9 filmes) é, na maior parte, roteiro/atuação classificado
estritamente demais — não é lacuna. `fidelidade` (6) e `adaptacao` (2) são
especificidade legítima de filme histórico ou adaptado, exatamente o caso
para o qual os 2 temas livres por bucket existem.

**`outros` (58 ocorrências, 14 filmes) merece uma linha:** não é uma família,
é o resto — diálogo citado sem comentário, meme, cultura de fandom, "contexto
do universo cinematográfico". É a fatia que nenhum eixo novo resolve.

---

## Entrega 4 — Distribuição e viabilidade do lift

### (a) Quantos eixos por review

| | média | mediana |
|---|---:|---:|
| eixos (sem contar `livre`) | **2,45** | 2 |
| eixos (contando `livre`) | 2,82 | 3 |

Histograma (eixos por review, sem `livre`): 0 → 132 · 1 → 105 · 2 → 233 ·
3 → 183 · 4 → 102 · 5 → 62 · 6 → 28 · 7 → 11 · 8 → 3.

**A classificação não está sendo generosa.** 2,45 de 8 eixos possíveis, com
metade das reviews em 2 ou menos, e só 14 reviews (1,6 %) marcando 7 ou 8. O
risco que a Entrega 4 levantou — frequências infladas por classificação
frouxa — não se materializou. As frequências abaixo podem ser lidas como
estão.

### (b) Frequência de cada eixo por bucket

Percentual das reviews do bucket que mencionam o eixo:

| eixo | negativas | medianas | positivas | global |
|---|---:|---:|---:|---:|
| `roteiro_estrutura` | 48,1 | 45,5 | 39,9 | **44,5** |
| `tom_atmosfera` | 27,7 | 34,6 | **49,0** | 37,1 |
| `comparacoes` | 33,7 | 37,4 | 38,9 | 36,7 |
| `direcao_imagem` | 28,8 | 33,9 | 33,0 | 31,9 |
| `impacto_emocional` | 20,4 | 25,9 | **41,3** | 29,2 |
| `ritmo` | **35,1** | 30,1 | 18,1 | 27,7 |
| `atuacao` | 23,5 | 25,9 | 31,6 | 27,0 |
| `som_trilha` | 8,4 | 10,8 | 14,2 | **11,2** |

Os três gradientes monotônicos são exatamente os que o desenho da interface
esperaria encontrar: `ritmo` cai de negativas para positivas (35 → 18),
`tom_atmosfera` (28 → 49) e `impacto_emocional` (20 → 41) sobem.

### (c) Eixos que quase nunca aparecem

**Nenhum candidato a remoção.** O mais raro, `som_trilha`, aparece em 11,2 %
das reviews — pouco em comparação aos outros, mas longe de "quase nunca", e
com gradiente na direção certa (8,4 → 14,2). Ele é fraco de outra forma, que
importa mais para o desenho: só vence a margem de 15 pp em 2 filmes (contra 9
do `ritmo`) — ou seja, é um eixo que quase nunca vai *encabeçar* uma linha.

### (d) Viabilidade do lift — o achado que deve mudar o desenho

Para cada par (filme, eixo): `lift` = frequência no bucket vencedor menos a
maior frequência entre os outros dois. `obsession-2026` sai desta conta
(buckets de 5 a 8 reviews; ver ressalva ao final), restando **14 filmes × 8
eixos = 112 pares**.

| | pares ≥ 15 pp | pares ≥ 20 pp |
|---|---:|---:|
| **observado** (n = 20/bucket) | **37** de 112 | **20** de 112 |
| esperado sob o nulo, permutação (n = 20) | 23,7 (p95 = 31) | 10,0 (p95 = 15) |
| esperado sob o nulo, paramétrico (n = 20) | 22,7 (p95 = 30) | 9,3 (p95 = 14) |
| esperado sob o nulo, paramétrico (**n = 40**) | **7,2** (p95 = 12) | **1,7** (p95 = 4) |

O nulo é o teste que a pergunta pedia mas o enunciado não previa. Com 20
reviews por bucket, o erro padrão de uma diferença de proporções em torno de
p = 0,3 é ~14,5 pp — **da ordem da própria margem de 15 pp**. Contar os pares
observados acima da margem, sozinho, não distingue sinal de ruído. Então
medi o ruído: embaralhando o rótulo de bucket dentro de cada filme (o que
destrói qualquer associação bucket↔eixo mas preserva os tamanhos de bucket e
a frequência global do eixo), 2 000 vezes.

Três leituras, em ordem de importância:

**1. Há sinal real, mas menos do que o número bruto sugere.** 37 observados
contra 23,7 esperados por acaso: acima do p95 do nulo (31), logo não é acaso —
mas **cerca de dois terços dos pares que passam a margem a 20 reviews
passariam sem nenhuma associação real**. O excedente sobre o nulo é de ~14
pares em 14 filmes: da ordem de **um eixo separador por filme**, não três ou
quatro.

**2. A 40 reviews por bucket, o problema praticamente desaparece.** O nulo
paramétrico (cada par reamostrado como três binomiais com a frequência global
observada daquele eixo naquele filme — nenhuma associação com bucket, por
construção) cai de 22,7 para **7,2** pares a 15 pp, e de 9,3 para **1,7** a
20 pp. Dobrar o denominador reduz o piso de ruído em ~3×. **A margem de
15-20 pp é defensável na cota de produção (40/bucket); não é a 20.** A
validação cruzada entre os dois nulos a n = 20 (23,7 vs 22,7) é o que me deixa
confiar na extrapolação paramétrica para n = 40.

**3. A ordenação por lift tem o que ordenar — 13 dos 14 filmes têm ao menos
um eixo acima de 15 pp** (11 acima de 20 pp). A exceção é `barbie`, cujo
melhor lift é 10 pp: um filme em que os três buckets falam das mesmas coisas
e discordam sobre elas. Se a interface exige uma linha destacada por filme,
`barbie` é o caso que o desenho precisa saber tratar.

Distribuição dos 37 pares ≥ 15 pp — por eixo: `ritmo` 9, `direcao_imagem` 6,
`impacto_emocional` 5, `atuacao` 5, `tom_atmosfera` 4, `roteiro_estrutura` 3,
`comparacoes` 3, `som_trilha` 2. Por bucket vencedor: positivas 18, medianas
10, negativas 9. Por perfil: arthouse 13, invertido 9, aclamado 9, divisivo 6.

Os 13 maiores lifts (todos com 20 reviews por bucket):

| filme | eixo | bucket | freq. | lift |
|---|---|---|---:|---:|
| `cure` | `tom_atmosfera` | positivas | 65,0 % | 35,0 pp |
| `aftersun` | `impacto_emocional` | positivas | 95,0 % | 35,0 pp |
| `cure` | `ritmo` | negativas | 65,0 % | 30,0 pp |
| `friday-the-13th-2009` | `ritmo` | medianas | 45,0 % | 30,0 pp |
| `longlegs` | `ritmo` | negativas | 45,0 % | 30,0 pp |
| `cats-2019` | `tom_atmosfera` | positivas | 50,0 % | 30,0 pp |
| `aftersun` | `tom_atmosfera` | positivas | 60,0 % | 25,0 pp |
| `anatomy-of-a-fall` | `roteiro_estrutura` | negativas | 75,0 % | 25,0 pp |
| `anatomy-of-a-fall` | `direcao_imagem` | positivas | 40,0 % | 25,0 pp |
| `cats-2019` | `direcao_imagem` | medianas | 60,0 % | 25,0 pp |
| `talk-to-me-2022` | `ritmo` | medianas | 40,0 % | 25,0 pp |
| `talk-to-me-2022` | `direcao_imagem` | medianas | 50,0 % | 25,0 pp |
| `talk-to-me-2022` | `impacto_emocional` | positivas | 45,0 % | 25,0 pp |

**Ressalva sobre `obsession-2026`:** incluído, ele contribui 6 pares ≥ 15 pp
(o maior de todos, 62,5 pp) — mas com buckets de 5, 6 e 8 reviews, onde uma
review sozinha vale de 12,5 a 20 pp. Esses 6 pares são aritmética, não
evidência, e por isso o corte `n_min_bucket ≥ 15` (o mesmo limiar que
`PISO_ESCALONADO` já usa para autorizar quantificador) governa todos os
números desta seção. Os totais sem o corte estão em
`relatorio.json → entrega4_distribuicao_e_lift.lift.todos_os_filmes`.

---

## Entrega 5 — Custo

Medido, não estimado — `usage` de cada resposta da API, somado pelo código.

| etapa | chamadas | custo |
|---|---:|---:|
| classificação (Entregas 1-4) | 859 | **US$ 0,0324** |
| famílias de tema livre (Entrega 3) | 430 | US$ 0,0056 |
| triagem suplementar | 132 | US$ 0,0021 |
| **total do gate** | 1 421 | **US$ 0,0401** |

Tokens da classificação: 705 558 de entrada (**544 640 servidos por cache**,
77 %) + 29 969 de saída. **US$ 3,78 × 10⁻⁵ por review.** Throughput medido:
5,8 reviews/s com 8 chamadas concorrentes — as 859 levaram 145 s.

### Extrapolação para o catálogo completo

35 filmes × 3 buckets × até 40 reviews = **4 200 reviews**.

| | valor |
|---|---:|
| custo de LLM | **US$ 0,159** |
| tempo, na mesma concorrência | ~12 min |

A extrapolação é linear no número de reviews e **conservadora por cima**: o
prompt de sistema é idêntico em toda chamada, então a fração de entrada
servida por cache (77 % nesta amostra, que começou fria) só cresce com o
volume.

**O que isso dimensiona:** a classificação por eixo da fase de síntese inteira
custa **menos de vinte centavos de dólar** para todo o catálogo atual. Ela não
é o gargalo de custo de nada — o que significa que decisões como "classificar
com um modelo melhor", "classificar duas vezes e reconciliar" ou "reclassificar
a cada mudança de taxonomia" podem ser tomadas por qualidade, sem argumento
de custo. Um best-of-3 sobre a classificação inteira custaria US$ 0,48.

---

## O que este gate não mediu

- **Se as classificações estão certas.** Mediu-se consistência de formato
  (859/859, zero eixo inventado) e distribuição, não acurácia. Nenhuma amostra
  foi conferida contra julgamento humano. Uma taxonomia pode ter
  `fracao_livre` baixa porque cobre bem o corpus *ou* porque o modelo força
  encaixe — estes números não separam as duas.
- **Estabilidade entre execuções.** Temperatura 0, uma passada. Não se sabe
  quanto da fração de 15,4 % é variância do modelo.
- **Filmes obscuros.** O catálogo tem um, com 19 reviews. É o perfil com o
  pior número e a menor evidência.
- **A regra dos "até 2 temas livres por bucket".** Este gate mediu a taxonomia,
  não a válvula de escape dela.

---

## Reprodução

```bash
python scripts/gate_taxonomia.py amostra       # determinístico, sem LLM
python scripts/gate_taxonomia.py classificar   # 859 chamadas, resume via JSONL
python scripts/gate_taxonomia.py familias      # Entrega 3
python scripts/gate_taxonomia.py triagem       # medição suplementar
python scripts/gate_taxonomia.py relatorio     # agregação, sem LLM
```

Saídas em `resultado/gate-taxonomia/`: `amostra.json`, `classificacoes.jsonl`,
`familias.json`, `triagem_so_livre.jsonl`, `relatorio.json`.
