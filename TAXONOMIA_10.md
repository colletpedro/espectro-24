# Taxonomia ampliada — 10 eixos, 35 filmes

**Data:** 2026-08-08 · **Natureza:** medição · **Mudanças de produção:** nenhuma

Nada de schema, frontend, pipeline de síntese, lift ou estado `contraste` foi
implementado. `resultado/*.json` intacto. Todas as chamadas de LLM passam pelo
adaptador (§3[D]) — o guard-rail da v1.9.4 segue verde.

A taxonomia sob teste, e o que mudou desde o gate de 8 eixos:

| eixo | estado |
|---|---|
| `ritmo`, `atuacao`, `direcao_imagem`, `roteiro_estrutura`, `som_trilha`, `tom_atmosfera`, `comparacoes` | inalterados |
| `impacto_emocional` | **definição AFROUXADA** — passa a cobrir reação física/visceral e reação de plateia; só o elogio genérico sem efeito descrito continua fora |
| `expectativa` | **NOVO** (recorria em 15/15 filmes) |
| `critica_social` | **NOVO** (14/15, maior contribuinte de `livre` no bucket negativo) |
| `livre` | fallback, como antes |

---

## Entrega 1 — Inspeção de `assistir`

39 ocorrências no gate, em 13 filmes, 20 delas em reviews que caíram só em
`livre`. 30 sorteadas com semente (`scripts/inspecao_assistir.py`), cada uma
julgada isoladamente pelo LLM, com o texto completo à vista.

### A resposta não é (a) nem (b)

| categoria | n de 30 |
|---|---|
| **já coberto pelos 10 eixos** | **26** |
| logística pura | 3 |
| conteúdo real que a taxonomia não alcança | 1 |

**`assistir` não era um eixo faltando nem um filtro esperando para nascer: era
um ARTEFATO da taxonomia de 8 eixos.** Os dois eixos que a decisão já promoveu
o dissolvem — de 30 exemplos, **14 seriam cobertos por `expectativa`** e **14
por `impacto_emocional`** (a contagem soma mais que 30 porque uma review pode
ser coberta por ambos).

O que a família continha, lido de perto:

- **motivo de ter ido ver** — "assisti por causa de Supernatural", "foi
  recomendação do ChatGPT", "meu amigo insistiu que a gente visse no cinema".
  Isso é `expectativa`, e só caía em `livre` porque `expectativa` não existia;
- **reação da plateia e reação visceral** — "metade da sala saiu no meio",
  "a plateia gritava KILL HIM toda vez que o Corden aparecia", "dormi 70% do
  filme". Isso é `impacto_emocional` sob a definição afrouxada, e caía fora
  pela regra estrita antiga;
- **circunstância pura** — 3 casos, todos em reviews só-`livre`: "vi metade
  num perfil de TikTok às 5 da manhã", "vi no avião sem legenda em holandês",
  "assisti duas vezes e nunca presto atenção, deixo de fundo".

### Sobre o filtro de seleção: candidato fraco, e a medição diz por quê

A pergunta do filtro só se aplica às reviews que caíram **só** em `livre` —
uma review com 5 eixos e um tema `assistir` de brinde entraria na síntese sob
qualquer filtro razoável. Dessas, na amostra inspecionada: **3 de 15 são
logística pura (20%)**, as outras 11 já estariam cobertas e 1 é conteúdo novo.

Sobre o total do gate, 3 casos de logística pura em 859 reviews classificadas
é **0,35%**. Não é uma classe que justifique um mecanismo de filtro com modo
de falha próprio. **Reportado e parado aqui, como pedido — nenhum filtro
implementado.**

### Concentração num filme só

8 dos 30 exemplos são de `cats-2019`, e descrevem o mesmo fenômeno: a sessão
participativa de meia-noite (o "Jellicle Ball"), onde a plateia canta, grita e
se fantasia. Pelo critério que o próprio gate fixou — tema que recorre em
muitos filmes é candidato a eixo, tema concentrado num filme é especificidade
legítima — isso pertence aos temas livres, não a um eixo. É também o caso mais
forte do único item que classifiquei como conteúdo real não coberto.

### Onde minha leitura diverge da do LLM

Li os 30 e discordo em 2, ambos na direção de **mais** cobertura, não menos:

- `friday-the-13th-2009`/neg, marcado logística pura: "assisti por causa de
  Supernatural, obrigada Jared Padalecki… filme de terror teen, não é pra
  mim". O motivo de ter assistido é `expectativa` — eu contaria como coberto;
- `shutter-island`/pos, o único marcado como conteúdo novo: "literalmente
  exercício pro meu cérebro, e se eu assistisse de novo seria um filme
  inteiramente diferente". Isso é sobre o filme recompensar o rewatch, o que
  é `roteiro_estrutura` (a estrutura do twist) — eu contaria como coberto.

Pela minha leitura seria **28 coberto / 2 logística / 0 conteúdo novo**. A
conclusão não muda em nenhuma das duas contagens; registro a divergência
porque o veredito do LLM é o número reproduzível e o meu não é.

---

## Entrega 2 — Classificação dos 35 filmes

**3948 reviews, 35 filmes, 3948/3948 classificadas sem uma falha.** A amostra
é a **população de produção**, não um sorteio: `selecionar()` com os
parâmetros de sempre (cota 40/bucket, `min_chars` 150, cascata, spoiler
excluído) entrega exatamente o que a síntese veria. 22 dos 35 filmes têm os
três buckets a 40; 25 dos 105 buckets estão abaixo (a recoleta da v1.9.4
cobriu 9 filmes, os demais seguem com o déficit anterior).

Persistência versionada por taxonomia: cada linha carrega `taxonomia_id`
(hash do prompt + da lista de eixos). Mudou a definição de um eixo, muda o
id, e a classificação antiga deixa de casar — nenhuma sessão futura reusa em
silêncio classificação feita sob outra régua.

### `fracao_livre`: 15,4% → 4,8%

| | 8 eixos (859 reviews) | **10 eixos (3948)** |
|---|---|---|
| **global** | 15,4% [13,1; 17,9] | **4,81%** [4,19; 5,53] |
| negativas | 20,4% | **5,61%** [4,5; 7,0] |
| medianas | 13,6% | 4,43% [3,4; 5,7] |
| positivas | 12,2% | 4,41% [3,4; 5,6] |

**Os dois eixos promovidos resolveram o problema que motivou a promoção.** O
bucket `negativas` era a célula na borda da zona cinzenta (20,4%, IC até
25,4%) e a causa diagnosticada era `critica_social` — review negativa que
critica o que o filme representa, não o que ele é. Com o eixo, cai para 5,6%.
A assimetria entre buckets some junto: eram 8,2 pontos entre o pior e o
melhor, agora são 1,2.

Por perfil, nenhum acima de 5,1% — exceto `obsession-2026` (21%, n=19, IC
[8,5; 43,3]), o filme obscuro, que continua sendo a única célula sem
evidência suficiente para dizer coisa alguma.

Pior filme fora dele: `mother-2017` com 10,0%. Melhor: `the-hateful-eight`
com 0,83%.

### Eixos por review: 2,45 → 3,08 (mediana 2 → 3)

Histograma: 0→206 · 1→425 · 2→943 · 3→987 · 4→637 · 5→390 · 6→200 · 7→108 ·
8→38 · 9→10 · 10→4.

Subiu 0,63 eixo por review, com 2 eixos novos e 1 afrouxado — ou seja, quase
todo o ganho veio de reviews que ANTES caíam em `livre` e agora têm eixo, não
de generosidade. 52 reviews (1,3%) marcam 7 ou mais dos 10 eixos; a
classificação continua estrita.

### Frequência por bucket

| eixo | neg | med | pos | global |
|---|---:|---:|---:|---:|
| `impacto_emocional` | 40,1 | 42,2 | **55,8** | **46,1** |
| `roteiro_estrutura` | 45,3 | 45,1 | 39,3 | 43,2 |
| `comparacoes` | 39,2 | 37,1 | 41,3 | 39,2 |
| `ritmo` | **39,8** | 35,4 | 23,1 | 32,7 |
| `direcao_imagem` | 25,7 | 31,6 | 32,1 | 29,8 |
| `expectativa` | **31,2** | 29,7 | 21,9 | 27,6 |
| `atuacao` | 22,4 | 27,3 | 28,5 | 26,1 |
| `critica_social` | **29,1** | 25,8 | 21,5 | 25,4 |
| `tom_atmosfera` | 20,4 | 24,1 | 31,4 | 25,3 |
| `som_trilha` | 9,5 | 12,6 | 15,5 | **12,6** |

Os dois eixos novos entram com peso real — `expectativa` em 27,6% e
`critica_social` em 25,4% das reviews, ambos mais frequentes que
`tom_atmosfera`. Os dois são **mais fortes no bucket negativo**, com gradiente
monotônico decrescente: quem não gostou fala mais do que esperava e do que o
filme representa.

`impacto_emocional` saltou de 29,2% para 46,1% — efeito direto do afrouxamento,
e é agora o eixo mais frequente do corpus.

### Eixos raros — candidatos a remoção

**Nenhum.** O mais raro, `som_trilha`, aparece em 12,6% das reviews (era
11,2% com 8 eixos) e mantém gradiente na direção certa (9,5 → 15,5). Ele
continua fraco de outra forma, que importa mais para o desenho: só encabeça
uma linha em 3 filmes.

### Um achado de método: com 10 eixos o modelo erra o NOME do eixo

Com 8 eixos, **zero** nomes inválidos em 2107 atribuições. Com 10, **56
atribuições** vieram com nome malformado. A lista mais longa produz erro de
digitação.

O reparo é mecânico e conservador (sem acento, sem separadores, aceita só se
a semelhança com **um** eixo válido passa de 0,85), aplicado na LEITURA — o
JSONL guarda o que o modelo devolveu de fato. **32 atribuições recuperadas**,
das quais 10 eram `crítica_social` (o acento) e 6 `ton_atmosfera`: sem o
reparo, o eixo NOVO cuja frequência está sendo medida seria o mais penalizado.

As 24 restantes não são erro de digitação e continuam inválidas de propósito:
`atores` (5), `humor` (3), `ator` (2), `elenco`, `dialogos` — o modelo saindo
da taxonomia para nomear o que já tem eixo. Contá-las como acerto seria
inventar cobertura; apagá-las seria esconder o sinal.

---

## Entrega 3 — Recalibração da margem de lift

Mesmo nulo de permutação de antes: 2000 rodadas, embaralhando o rótulo de
bucket **dentro de cada filme** (destrói a associação bucket↔eixo, preserva
os tamanhos de bucket e a frequência global de cada eixo naquele filme).
350 pares (filme, eixo).

| margem | grupo | observado | nulo (média) | p95 | **% que passaria por acaso** |
|---|---|---:|---:|---:|---:|
| 10 pp | todos (35) | 117 | 69,3 | 82 | 59% |
| **15 pp** | **todos (35)** | **56** | **28,0** | **36** | **50%** |
| | 3 buckets a 40 (22) | 36 | 14,8 | 21 | 41% |
| | algum sub-40 (13) | 20 | 13,2 | 19 | **66%** |
| **20 pp** | **todos (35)** | **32** | **9,9** | **15** | **31%** |
| | **3 buckets a 40 (22)** | **20** | **3,7** | **7** | **19%** |
| | algum sub-40 (13) | 12 | 6,2 | 10 | 52% |
| 25 pp | todos (35) | 18 | 4,1 | 7 | 23% |
| | 3 buckets a 40 (22) | 9 | 0,9 | 3 | 10% |
| | algum sub-40 (13) | 9 | 3,2 | 6 | 36% |

### A extrapolação da v1.9.4 se confirma com dado real

A sessão anterior previu, por nulo paramétrico, que dobrar o denominador de
20 para 40 derrubaria o piso de ruído de 20,3% dos pares para **6,4%**. Medido
agora, com dado real e 10 eixos: o grupo com os três buckets a 40 tem nulo de
14,8 em 220 pares = **6,7% dos pares** a 15 pp.

**6,4% previsto contra 6,7% medido.** A previsão que justificou a extensão de
orçamento da v1.9.4 estava certa.

### Os buckets sub-40 precisam de margem maior — quanto

À mesma margem, o grupo com algum bucket sub-40 tem piso de ruído **2,7×
maior** em fração de pares (10,2% contra 3,8% a 20 pp). Traduzido em
proporção do que passa: a 20 pp, 19% do que cruza a margem num filme cheio é
ruído, contra **52%** num filme com bucket curto.

Ressalva que muda a leitura desse grupo: `obsession-2026` sozinho (buckets de
5, 6 e 8 reviews) responde por **7 dos 20** pares acima de 15 pp e **6 dos
12** acima de 20 pp do grupo sub-40. Excluído ele, sobram 13 e 6 — os outros
12 filmes têm buckets entre 24 e 39, e o problema deles é muito menor que o
número agregado sugere. O caso de bucket com menos de 10 reviews é de outra
ordem, e o piso escalonado (§3[C3]) já o trata à parte.

### Margem recomendada: **20 pp**

O número que a sustenta: a 20 pp, **31% dos pares que cruzam a margem
cruzariam por acaso; a 15 pp são 50%.** Ordenar por lift com metade da lista
sendo ruído não é ordenar. A 20 pp o custo é 32 pares em vez de 56 — 21 dos
35 filmes ainda têm ao menos um eixo acima da margem.

Duas ressalvas que acompanham a recomendação:

1. **20 pp vale para filme com os três buckets a 40** (19% de ruído). Para
   filme com bucket abaixo de 40, 20 pp entrega 52% de ruído — pior que os
   15 pp de um filme cheio. Se o desenho quiser uma regra só, ela deveria ser
   **condicionada ao `n` do menor bucket**, não fixa. Uma margem única de
   25 pp igualaria os grupos (10% contra 36%), mas ao custo de deixar 22 dos
   35 filmes sem nenhuma linha.
2. **Isto é uma taxa de descoberta falsa agregada, não um teste por par.** Diz
   quantos pares da lista são ruído, não quais. A ordenação por lift continua
   sendo uma heurística de apresentação, não uma afirmação estatística sobre
   um eixo específico.

Distribuição dos 56 pares ≥ 15 pp — por eixo: `impacto_emocional` 12,
`direcao_imagem` 8, `ritmo` 7, `tom_atmosfera` 6, `comparacoes` 6, `atuacao`
5, `som_trilha` 3, `expectativa` 3, `roteiro_estrutura` 3, `critica_social` 3.
Por bucket vencedor: positivas 33, negativas 15, medianas 8.

Os dois eixos novos raramente **encabeçam** uma linha (3 cada), apesar de
serem frequentes — eles aparecem muito, mas de forma parecida nos três
buckets. São bons para cobertura, fracos para contraste.

---

## Entrega 4 — Medição limpa do estado `contraste`

| margem | filmes sem NENHUM eixo acima | sob o nulo |
|---|---|---|
| 10 pp | 1 de 35 | 4,3 (p95 = 7) |
| **15 pp** | **8 de 35 (23%)** | 16,7 (p95 = 21) |
| **20 pp** | **14 de 35 (40%)** | 28,3 (p95 = 32) |
| 25 pp | 22 de 35 | 32,6 (p95 = 34) |

**Na margem recomendada de 20 pp, `contraste: valorativo` são 14 de 35 filmes
— 40%. Não é caso de borda: é o segundo estado mais comum, e o desenho
precisa tratá-lo como primeira classe desde o início.**

Mesmo na margem antiga de 15 pp são 8 de 35 (23%), contra o "1 em 14" que a
v1.9.4 mediu. A v1.9.4 registrou aquele número como **piso, não estimativa**,
e a medição limpa confirma: o valor real é 5 a 8 vezes maior.

O sinal é real, não artefato: sob o nulo o esperado seria 16,7 filmes a 15 pp
e 28,3 a 20 pp — o observado (8 e 14) fica **muito abaixo**, ou seja, contraste
temático de verdade existe e é mais comum do que o acaso produziria. O que a
medição corrige não é a existência do contraste, é a frequência do seu
oposto.

### A lista, a 15 pp

| grupo | n | filmes |
|---|---|---|
| **3 buckets a 40** | 3 de 22 (14%) | `avengers-endgame`, `longlegs`, `the-northman` |
| **algum bucket sub-40** | 5 de 13 (38%) | `bones-and-all`, `eighth-grade`, `the-godfather`, `the-substance`, `wicked-2024` |

A separação importa: **entre os filmes bem medidos o estado é 14%; entre os
mal medidos, 38%.** Parte do "sem contraste" dos sub-40 é falta de precisão,
não ausência de contraste — o mesmo `n` pequeno que infla o ruído dos pares
que passam também impede pares reais de passarem. Fechar os buckets restantes
(a extensão da v1.9.4 cobriu 9 dos 35 filmes) deve reduzir esse 38%.

A 20 pp, são 7 de 22 entre os cheios e 7 de 13 entre os sub-40.

### Onde caíram os três filmes que a medição anterior apontou

| filme | antes (8 eixos, n=20) | agora (10 eixos, n=40) |
|---|---|---|
| `barbie` | **melhor lift 10,0 pp — o único sem contraste** | **25,4 pp** (`impacto_emocional`), 2 eixos ≥ 15 pp |
| `napoleon-2023` | 15,0 pp, zero acima de 20 pp | **20,0 pp** (`comparacoes`), 2 ≥ 15, 1 ≥ 20 |
| `perfect-days-2023` | 15,0 pp, zero acima de 20 pp | **35,0 pp** (`tom_atmosfera`), 3 ≥ 15, **3 ≥ 20** |

**Os três saíram da lista, e `barbie` — o caso que deu nome ao estado — é
hoje um dos filmes com contraste mais forte do catálogo.** O que faltava não
era contraste: era eixo para enxergá-lo (a separação de `barbie` está em
`impacto_emocional`, que a régua antiga não capturava) e denominador para
medi-lo.

Isso é um alerta de método que vale registrar: um filme classificado como
`contraste: valorativo` sob uma taxonomia pode deixar de sê-lo sob a
seguinte. O estado descreve **o que a régua atual enxerga**, não uma
propriedade do filme — e o schema deveria carregar a `taxonomia_id` junto do
veredito.

### O caso de borda oposto

`obsession-2026` tem 7 eixos acima de 15 pp — o maior número do catálogo — com
buckets de 5, 6 e 8 reviews. É aritmética, não contraste: uma review vale de
12,5 a 20 pp. Qualquer regra de `contraste` precisa de um piso de `n` antes de
olhar o lift, e o piso escalonado (§3[C3]) já fornece o limiar (15).

---

## Entrega 5 — Custo

| | valor |
|---|---|
| reviews classificadas | 3948 |
| tokens de entrada | 4 039 240 (**3 523 200 servidos por cache, 87,2%**) |
| tokens de saída | 138 662 |
| **custo total** | **US$ 0,1209** |
| custo por review | US$ 3,06 × 10⁻⁵ |

**Contra a extrapolação de US$ 0,159 do gate: 24% ABAIXO.** A projeção era
linear a US$ 3,78 × 10⁻⁵ por review sobre 4200 reviews; o custo real por
review caiu para US$ 3,06 × 10⁻⁵.

A causa é exatamente a que o gate registrou como razão para a extrapolação ser
conservadora por cima: **a taxa de cache hit no prefixo subiu de 77,2% para
87,2%**, porque o prompt de sistema é idêntico em toda chamada e o volume
maior mantém o prefixo quente. O prompt de 10 eixos é mais longo que o de 8, e
ainda assim o custo por review caiu — o efeito do cache mais que compensou.

Wall-clock: 3948 chamadas em ~10,7 min a 6,1/s com 8 chamadas concorrentes.

**Dimensionamento:** classificar o catálogo inteiro em toda mudança de
taxonomia custa ~12 centavos e 11 minutos. Um best-of-3 sobre a classificação
inteira custaria US$ 0,36. Nenhuma decisão de qualidade desta fase precisa ser
tomada por argumento de custo.

---

## O que este trabalho não mediu

- **Se as classificações estão certas.** Mediu-se formato (3948/3948, 24
  nomes fora da taxonomia), distribuição e contraste — não acurácia. Nenhuma
  amostra foi conferida contra julgamento humano, exceto os 30 exemplos da
  Entrega 1.
- **Estabilidade entre execuções.** Temperatura 0, uma passada. Não se sabe
  quanto dos 4,8% é variância do modelo.
- **A regra dos "até 2 temas livres por bucket".** Segue sem medição.
- **Se `expectativa` e `critica_social` são úteis para o LEITOR.** Foram
  medidos como cobertura (frequência, redução de `livre`) e como contraste
  (raramente encabeçam linha). Nenhuma das duas coisas diz se o leitor quer
  ler sobre eles.

## Reprodução

```bash
python scripts/inspecao_assistir.py extrair
python scripts/inspecao_assistir.py classificar
python scripts/classificar_10.py amostra
python scripts/classificar_10.py classificar
python scripts/classificar_10.py relatorio
```

Saídas em `resultado/taxonomia-10/`: `assistir_amostra.json`,
`assistir_vereditos.json`, `amostra.json`, `classificacoes.jsonl`,
`relatorio.json`.
