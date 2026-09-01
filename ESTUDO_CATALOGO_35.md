# Estudo analítico do catálogo publicado — 35 filmes

**Sessão de leitura, não de implementação.** Nada em `resultado/`, `frontend/`,
`dados/` ou `src/` foi escrito ou alterado. Nenhum estágio do pipeline rodou.
Nenhuma chamada de LLM foi feita. Os estudos 8 e 10 usam os métodos alternativos
especificados no pedido, e a distinção entre o que eles medem e o que pareceriam
medir está declarada em cada seção.

**Data:** 2026-08-27 · **Catálogo:** 35 filmes com bloco `eixos`
(`resultado/*.json`; o 36º arquivo,
`como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual.json`, não
tem bloco `eixos` nem bruto persistido e fica fora de tudo) ·
**`taxonomia_id`:** `ebab2667de74` · **margem:** 20pp, `>=` exato ·
**classificação de produção:** `resultado/votacao-3/consenso_verificado.jsonl`.

---

## Definições e reconstruções usadas em todo o relatório

Três decisões de método valem para os dez estudos e ficam aqui para não se
repetirem:

**(a) "Bullet publicado" = todo `tema` de `buckets[].temas[]`.** Foi verificado
no render, não presumido: `groupBlock()` em
[frontend/js/filme.js:1325](frontend/js/filme.js:1325) itera sobre **todos** os
temas do bucket; `bullet_de` (`"frequencia"` | `"contraste"` |
`"frequencia_e_contraste"` | `null`) só decide a **ordem** dentro do grupo
(`ordenarTemasPorEixo`, [filme.js:1215](frontend/js/filme.js:1215)). Isso dá
**629 bullets** (18 por filme; 17 em `the-hateful-eight`). Os 210 bullets que
`bullet_de` marca como `frequencia` e os 29 que marca como contraste são um
sub-rótulo dentro desses 629, não o conjunto publicado.

**(b) Mapa `tema → eixo`.** Vem de `eixos.linhas[].por_bucket[bucket].tema` e de
`temas_no_mesmo_eixo[]`. Cobre 619 dos 629 bullets. Os 10 restantes são os que
[D3] rotulou `livre` — eixo que não tem linha em `linhas[]` — e são tratados
como `livre` aqui. Dois deles são um achado de instrumentação: em
`im-still-here-2024`/positivas e `mother-2017`/medianas o rótulo devolvido foi
`crítica_social`, **com acento**, caiu fora da lista fechada e virou `livre`
(`rotulagem.fora_da_taxonomia` registra os dois). Não é erro de conceito, é
normalização de string.

**(c) A população classificada foi reconstruída, não estimada.** Os estudos 6 e
8 precisam saber **quais** reviews o bloco `eixos` conta. Reusei
`pipeline.ids_analisados_do_bruto(slug)` (leitura de disco, zero rede, zero LLM)
para re-derivar a seleção de produção e cruzei com `consenso_verificado.jsonl`.
A reconstrução foi conferida contra o publicado antes de ser usada: em `barbie`,
`ritmo` sai 1/18 · 5/26 · 1/17 pelos três buckets, byte a byte igual ao que
`resultado/barbie.json` publica. A partir daí ela é tratada como fiel.

---

# BLOCO A — Estrutura do produto

## 1. Eixo por gênero

**Método.** Para cada eixo, conto (i) em quantos filmes ele aparece como bullet
em pelo menos um dos três grupos e (ii) que fração dos bullets daquele gênero
ele ocupa. Um filme multi-gênero conta em todos os seus gêneros
(`ficha.generos`, TMDB); nenhum filme está sem gênero; 17 filmes têm 3 gêneros,
12 têm 2, 4 têm 1, 2 têm 4. Gêneros com n ≤ 3 (`História` 3, `Romance` 2,
`Guerra`/`Animação`/`Faroeste`/`Família` 1) ficam fora das tabelas — com n=1 a
"frequência" é a leitura de um filme só.

**Números — presença (o eixo aparece no filme?).**

| eixo | catálogo (35) | Drama (19) | Terror (9) | Thriller (8) | Aventura (8) | F. científica (7) | Mistério (6) | Crime (6) | Comédia (6) | Fantasia (5) | Ação (4) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ritmo` | 31 (89%) | 18 (95%) | 7 (78%) | 6 (75%) | 8 (100%) | 7 (100%) | 6 (100%) | 6 (100%) | 4 (67%) | 3 (60%) | 4 (100%) |
| `atuacao` | 34 (97%) | 19 (100%) | 9 (100%) | 8 (100%) | 7 (88%) | 6 (86%) | 6 (100%) | 6 (100%) | 6 (100%) | 5 (100%) | 3 (75%) |
| `direcao_imagem` | 34 (97%) | 18 (95%) | 9 (100%) | 8 (100%) | 8 (100%) | 7 (100%) | 6 (100%) | 6 (100%) | 5 (83%) | 5 (100%) | 4 (100%) |
| `roteiro_estrutura` | **35 (100%)** | 19 (100%) | 9 (100%) | 8 (100%) | 8 (100%) | 7 (100%) | 6 (100%) | 6 (100%) | 6 (100%) | 5 (100%) | 4 (100%) |
| `som_trilha` | 16 (46%) | 7 (37%) | 3 (33%) | 4 (50%) | 5 (62%) | 4 (57%) | 2 (33%) | 3 (50%) | 3 (50%) | 4 (80%) | 2 (50%) |
| `tom_atmosfera` | 28 (80%) | 14 (74%) | 8 (89%) | 8 (100%) | 6 (75%) | 5 (71%) | 6 (100%) | 5 (83%) | 6 (100%) | 4 (80%) | 3 (75%) |
| `impacto_emocional` | 18 (51%) | 12 (63%) | 3 (33%) | 2 (25%) | 6 (75%) | 4 (57%) | 2 (33%) | 2 (33%) | 4 (67%) | 3 (60%) | 3 (75%) |
| `comparacoes` | 12 (34%) | 6 (32%) | 4 (44%) | 3 (38%) | 2 (25%) | 1 (14%) | 1 (17%) | 3 (50%) | 2 (33%) | 2 (40%) | 2 (50%) |
| `expectativa` | 19 (54%) | 8 (42%) | 6 (67%) | 6 (75%) | 6 (75%) | 5 (71%) | 5 (83%) | 5 (83%) | 2 (33%) | 1 (20%) | 3 (75%) |
| `critica_social` | 27 (77%) | 16 (84%) | 8 (89%) | 7 (88%) | 5 (62%) | 4 (57%) | 4 (67%) | 4 (67%) | 4 (67%) | 3 (60%) | 3 (75%) |
| `livre` | 7 (20%) | 5 (26%) | 2 (22%) | 2 (25%) | 2 (25%) | 2 (29%) | 0 (0%) | 1 (17%) | 0 (0%) | 0 (0%) | 1 (25%) |

**Números — peso (que fração dos bullets do gênero cada eixo ocupa).** Esta é a
tabela que discrimina; a de presença satura.

| eixo | catálogo | Drama | Terror | Thriller | Aventura | F. científica | Mistério | Crime | Comédia | Fantasia | Ação |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ritmo` | 12% | 12% | 9% | 10% | 15% | 16% | 14% | 13% | 8% | 9% | 17% |
| `atuacao` | 14% | 14% | 13% | 11% | 12% | 11% | 14% | 12% | 17% | 18% | 10% |
| `direcao_imagem` | 13% | 12% | 15% | 13% | 11% | 11% | 10% | 11% | 13% | 17% | 11% |
| `roteiro_estrutura` | **25%** | 23% | 27% | **32%** | 25% | 27% | **32%** | **32%** | 19% | 16% | 28% |
| `som_trilha` | 5% | 4% | 2% | 4% | 6% | 6% | 2% | 4% | 7% | **11%** | 4% |
| `tom_atmosfera` | 7% | 6% | 9% | 8% | 6% | 7% | 9% | 7% | 8% | 9% | 8% |
| `impacto_emocional` | 7% | 10% | 4% | 3% | 7% | 6% | 4% | 4% | **11%** | 7% | 6% |
| `comparacoes` | 2% | 2% | 3% | 3% | 1% | 1% | 1% | 4% | 3% | 3% | 3% |
| `expectativa` | 4% | 3% | 5% | 6% | 5% | 5% | 7% | 7% | 3% | 1% | 4% |
| `critica_social` | 10% | 10% | 10% | 7% | 9% | 8% | 7% | 5% | 11% | 10% | 8% |
| `livre` | 2% | 2% | 3% | 3% | 1% | 2% | 0% | 1% | 0% | 0% | 1% |

(Bullets contados por gênero: Drama 341, Terror 162, Thriller 144, Aventura 144,
F. científica 126, Crime 108, Comédia 108, Mistério 107, Fantasia 90, Ação 72.
Um bullet de filme multi-gênero é contado em cada gênero, então a soma das
colunas passa de 629 — é uma tabela de perfil por gênero, não uma partição.)

**Leitura.** Três coisas.

1. **`roteiro_estrutura` é um ralo, não um eixo.** Um quarto de todos os bullets
   do catálogo cai nele — 158 de 629, mais que o dobro do segundo colocado
   (`atuacao`, 86). Ele aparece em **35 de 35 filmes** e em **todos** os
   dez gêneros com n ≥ 4, em 100% dos filmes de cada um. Um eixo que nunca
   discrimina nada não separa nada: por construção, ele nunca vai ser o eixo de
   contraste de ninguém, porque está saturado nos três grupos de todos os
   filmes. É o mesmo modo de falha que a SPEC §2.5 documenta para
   `impacto_emocional` (75,5% do corpus, precisão medida 0,486), só que
   `roteiro_estrutura` chegou lá pelo lado dos bullets em vez do lado da
   classificação.
2. **O sinal de gênero existe, mas é fraco e mora na cauda.** As diferenças
   grandes o suficiente para se notar são: `som_trilha` em Fantasia (11% dos
   bullets contra 5% do catálogo — são os musicais: `wicked-2024`, `wonka`),
   `impacto_emocional` em Comédia (11% contra 7% — `barbie` e
   `everything-everywhere-all-at-once` puxam), `expectativa` em Mistério/Crime
   (7% contra 4% — filmes de reputação consolidada colhendo "superestimado"),
   e a ausência quase completa de `impacto_emocional` em Thriller (3%) e Terror
   (4%). O resto é ruído de amostra.
3. **A hipótese "gênero de fórmula fala de fórmula" não aparece aqui.** Comédia
   e Terror não concentram em eixos diferentes dos outros; Comédia é, na
   verdade, o gênero **menos** concentrado em `roteiro_estrutura` (19%).

**Limite da amostra.** Com 35 filmes e multi-gênero, cada célula da tabela de
peso repousa em 4 a 19 filmes. Uma diferença de 3-4pp entre gêneros pode ser um
filme. Nada aqui além do item 1 (`roteiro_estrutura`, que é uma saturação de
100%, não uma diferença) deve ser tratado como conclusão fechada — são hipóteses
para reteste com o catálogo expandido.

---

## 2. Concentração por filme

**Método.** Para cada filme, quantos eixos **distintos** aparecem entre seus 18
bullets. Reporto com e sem `livre`, e acrescento um índice de concentração
(HHI = soma dos quadrados das frações de bullets por eixo; 0,100 seria os 18
bullets perfeitamente espalhados nos 10 eixos, 1,000 seria tudo num eixo só) —
porque "quantos eixos distintos" não distingue um filme com 2+2+2+2+2+2+2+2+2 de
um com 8+2+2+2+1+1+1+1.

**Números.** Nenhum filme tem 0 eixos; nenhum tem menos de 5.

| eixos distintos (sem `livre`) | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|
| filmes | 2 | 7 | 11 | 11 | 3 | 1 |

- **Média 7,26 · mediana 7,0 · min 5 · max 10.** Com `livre`: mediana 7, min 6.
- **HHI: média 0,177 · mediana 0,173.** Todos os filmes ficam entre 0,123 e
  0,278 — um intervalo estreito.

**Extremos.**

| mais DISPERSO (HHI baixo) | HHI | eixos | maior eixo |
|---|---|---|---|
| `mother-2017` | 0,123 | 9 | `critica_social` 3/18 |
| `hereditary` | 0,136 | 9 | `roteiro_estrutura` 4/18 |
| `the-godfather` | 0,136 | 8 | `ritmo` 3/18 |
| `dune-2021` | 0,142 | 8 | `ritmo` 3/18 |

| mais CONCENTRADO (HHI alto) | HHI | eixos | maior eixo |
|---|---|---|---|
| `spider-man-across-the-spider-verse` | 0,278 | 6 | `roteiro_estrutura` **8/18** |
| `friday-the-13th-2009` | 0,272 | 6 | `roteiro_estrutura` **8/18** |
| `longlegs` / `talk-to-me-2022` / `cure` / `anatomy-of-a-fall` | 0,228 | 6–7 | `roteiro_estrutura` 7/18 |

Por contagem simples de eixos distintos, os extremos são `napoleon-2023` e
`spider-man-across-the-spider-verse` (5 eixos) de um lado e `cidade-de-deus`
(10 eixos, o único filme do catálogo que toca todos) do outro.

**Leitura.** A dispersão é **quase constante em todo o catálogo** — mediana 7 de
10, HHI numa faixa de 0,12 a 0,28. Isso não é uma propriedade dos filmes; é uma
propriedade do desenho. Como todo filme entrega exatamente 18 bullets (6 por
bucket, número fixo de §[D]) e a taxonomia tem 10 eixos, o resultado
matematicamente esperado é "7 ou 8 eixos por filme, com o excedente empilhado no
eixo mais elástico". E é exatamente isso que acontece: **em todos os 6 filmes
mais concentrados, o eixo que absorve o excedente é `roteiro_estrutura`.** A
concentração alta não diz "este filme é sobre roteiro"; diz "os 18 temas deste
filme não couberam nos outros 9 eixos". `roteiro_estrutura` está funcionando
como o `livre` de facto da taxonomia.

Na outra ponta, `cidade-de-deus` com 10 de 10 é o caso oposto e é informativo: é
um filme com share 1/3/96 e ainda assim `contraste: valorativo` — dispersão
máxima e contraste nenhum, que é a assinatura de "os três grupos falam de tudo,
e de tudo do mesmo jeito".

**Limite da amostra.** 35 pontos, num intervalo estreito. A leitura estrutural
(o teto de 18 bullets forçando 7±1 eixos) é sólida porque é aritmética; o
ranking de filmes específicos dentro dessa faixa não é.

---

## 3. Contraste valorativo por gênero

**Hipótese a testar (não a presumir):** gêneros "de fórmula" — comédia, terror —
concordariam mais no tema e divergiriam só no valor, produzindo mais
`contraste: valorativo`.

**Método.** Proporção de filmes com `eixos.contraste == "tematico"` vs
`"valorativo"` por gênero. O catálogo é 18 `tematico` / 17 `valorativo`, o que
confere com a SPEC §2.5 sob `>=` exato.

**Números.**

| gênero | n | `tematico` | `valorativo` |
|---|---:|---:|---:|
| Comédia | 6 | 5 (83%) | 1 |
| Mistério | 6 | 4 (67%) | 2 |
| Thriller | 8 | 5 (62%) | 3 |
| Aventura | 8 | 5 (62%) | 3 |
| Fantasia | 5 | 3 (60%) | 2 |
| Ficção científica | 7 | 4 (57%) | 3 |
| Crime | 6 | 3 (50%) | 3 |
| Ação | 4 | 2 (50%) | 2 |
| **Drama** | **19** | **9 (47%)** | **10** |
| **Terror** | **9** | **4 (44%)** | **5** |
| *(catálogo)* | *35* | *18 (51%)* | *17* |

Gêneros com n ≤ 3 omitidos: História 1/3, Romance 1/2, Guerra/Animação/Faroeste/
Família 1/1 cada.

**Leitura. A hipótese não se sustenta — e falha de modos opostos nos dois
gêneros que ela previa juntos.** Comédia é o gênero **mais** temático do
catálogo (83%), o contrário do previsto; Terror é o menos (44%), como previsto.
Se "fórmula" explicasse contraste valorativo, os dois deveriam andar juntos, e
não andam.

Uma leitura alternativa que os dados **permitem** (e não confirmam): o que
separa os dois grupos não é fórmula, é **em que dimensão a fórmula falha**. Nas
6 comédias, o contraste temático mora em eixos onde a comédia pode dar errado de
um jeito visível e específico (`barbie` → `critica_social`, `wonka` →
`atuacao`/`direcao_imagem`, `everything-everywhere-all-at-once` →
`critica_social`/`direcao_imagem`). Nos 9 filmes de terror, o desacordo é sobre
se o filme **funcionou**, o que é justamente o que o estado `valorativo`
descreve. Isso é uma hipótese, e o n de 6 e 9 não a testa.

**Limite da amostra — este é o estudo mais frágil do bloco A.** Comédia n=6: um
filme mudando de estado leva os 83% para 67%. Com n=6 e p real de 50%, obter 5/6
por acaso tem probabilidade de ~11% — não é raro o suficiente para virar
conclusão. A diferença Comédia (83%) vs Terror (44%) não é distinguível de ruído
com estas amostras. **Tratar como hipótese a confirmar na expansão de catálogo.**

---

## 4. Vida útil de tema × eixo

**Método.** Para cada eixo, quantas strings `tema` **distintas** ele hospeda no
catálogo inteiro, e qual fração desses temas tem pelo menos um quase-sinônimo no
mesmo eixo. "Quase-sinônimo" = sobreposição Dice ≥ 0,55 sobre sacos de palavras
de conteúdo normalizadas (acentos removidos, stopwords pt-BR removidas, sufixos
de plural/gênero cortados). O limiar 0,55 foi fixado antes de olhar os pares.

**Números.**

| eixo | bullets | temas distintos | reuso literal | temas com quase-sinônimo no mesmo eixo |
|---|---:|---:|---:|---:|
| `roteiro_estrutura` | 158 | 148 | 1,07× | 74 (50%) |
| `atuacao` | 86 | 73 | 1,18× | 48 (66%) |
| `direcao_imagem` | 80 | 74 | 1,08× | 41 (55%) |
| `ritmo` | 76 | **48** | **1,58×** | **37 (77%)** |
| `critica_social` | 60 | 60 | 1,00× | 16 (27%) |
| `tom_atmosfera` | 47 | 46 | 1,02× | 8 (17%) |
| `impacto_emocional` | 41 | 38 | 1,08× | 19 (50%) |
| `som_trilha` | 31 | 24 | 1,29× | 16 (67%) |
| `expectativa` | 25 | 24 | 1,04× | 14 (58%) |
| `comparacoes` | 15 | 15 | 1,00× | 3 (20%) |
| `livre` | 10 | 10 | 1,00× | 0 (0%) |

**Três exemplos concretos de temas redundantes dentro do mesmo eixo.**

1. **`ritmo` — a família "lento".** Quatro strings literalmente repetidas em
   filmes diferentes: *"Ritmo lento e tédio"* (10×), *"Ritmo lento e arrastado"*
   (8×), *"Ritmo lento e duração excessiva"* (4×), *"Ritmo arrastado e duração
   excessiva"* (4×). São 26 dos 76 bullets de `ritmo` em quatro rótulos que
   dizem a mesma coisa. Dice entre os dois últimos: **0,75**. O eixo tem a menor
   variedade lexical do catálogo (48 temas para 76 bullets) e 77% de seus temas
   têm vizinho.
2. **`roteiro_estrutura` — a família "final".** *"Final decepcionante"*,
   *"Final decepcionante e ilógico"*, *"Final decepcionante ou confuso"*,
   *"Final confuso e insatisfatório"*, *"Final ambíguo e insatisfatório"*,
   *"Final ambíguo e sem respostas definitivas"*, *"Final controverso e
   exagerado"* — 10 temas mutuamente vizinhos. E a família "desenvolvimento de
   personagens": *"Desenvolvimento de personagem"*, *"…de personagens"*,
   *"…fraco"*, *"…superficial"*, *"…decepcionante"*, *"…fraco ou irritante"*.
3. **`expectativa` — o eixo quase inteiro é uma paráfrase de si mesmo.**
   *"Expectativa alta frustrada"*, *"Expectativa alta não correspondida"*,
   *"Expectativa alta, decepção"*, *"Expectativa não correspondida"*,
   *"Expectativas altas não correspondidas"*, *"Expectativas não
   correspondidas"*, *"Expectativa versus realidade"*, *"Expectativa vs.
   realidade (hype)"*, *"Expectativa vs. realidade (superestimado)"*. Nove das
   24 strings distintas do eixo dizem literalmente a mesma frase com
   pontuação diferente.

**Um achado colateral: 6 filmes têm o MESMO tema, string idêntica, em dois
buckets diferentes.** `barbie` medianas e positivas: *"Atuações de Margot Robbie
e Ryan Gosling"*. `the-northman` negativas e medianas: *"Ritmo lento e
arrastado"*. Também `eighth-grade` (*"Ritmo lento e tédio"*, neg+med),
`the-godfather` (*"Ritmo lento e longa duração"*, med+pos), `pearl-2022`
(*"Atuação de Mia Goth"*, med+pos) e `napoleon-2023` (*"Ritmo e edição"*,
neg+pos). Na interface, o leitor vê a mesma frase em duas colunas do mesmo
filme — a diferença entre os grupos está inteiramente na barra e no
`exemplo_parafraseado`, não no rótulo.

**Leitura.** A granularidade não é uniformemente fina demais; ela é fina demais
em **dois eixos específicos**, e por motivos diferentes.

- `ritmo` e `expectativa` são **eixos de baixa dimensionalidade semântica**: o
  público só tem umas poucas coisas a dizer sobre ritmo ("lento", "arrastado",
  "longo", "compensa no fim") e sobre expectativa ("não correspondeu"). Pedir
  ao [D] seis temas distintos por bucket força a produção de sinônimos. A
  solução não é mudar o eixo, é aceitar que 2 bullets nesses eixos já esgotam o
  que há para dizer.
- `roteiro_estrutura` é o oposto: é um eixo de **altíssima** dimensionalidade
  que virou o depósito de tudo que não coube. Os 148 temas distintos não são
  redundância — é que "roteiro/estrutura" cobre enredo, personagens, diálogo,
  final, ritmo narrativo, coerência interna e lore. Metade deles tem vizinho
  porque o eixo é grande, não porque seja repetitivo.
- `critica_social`, `tom_atmosfera` e `comparacoes` têm **zero ou quase zero
  redundância** (27%, 17%, 20%) e reuso literal 1,00×. Esses eixos estão na
  granularidade certa.

**Limite.** A medida é lexical, não semântica. *"Personagem principal
irritante"* e *"Falta de desenvolvimento dos personagens"* (`pearl-2022`,
negativas, mesmo eixo) dão Dice 0,333 e não entram como redundantes, mas um
leitor humano os lê como o mesmo bullet. A redundância medida aqui é um piso, não
um teto.

---

## 5. Peso do grupo × eixo

**Método.** Duas comparações. **(5a)** por filme: "unânimes" = filmes cujo maior
`share_real` de bucket passa de 80% (18 filmes) contra "equilibrados" (17
filmes). **(5b)** por bucket, que é onde o efeito de fato deve aparecer: os 23
buckets com `share_real ≤ 5%` (o grupo minoritário de um filme muito unânime)
contra os 19 buckets com `share_real ≥ 80%` (o grupo dominante).

**Números — 5a, por filme.** Nada.

| | unânimes (n=18) | equilibrados (n=17) |
|---|---|---|
| eixos distintos por filme (média) | 7,28 | 7,24 |
| `contraste: tematico` | 10/18 (56%) | 8/17 (47%) |
| `impacto_emocional` presente | 61% | 41% |
| `comparacoes` presente | 22% | 47% |

**Números — 5b, por bucket.** Aqui há sinal, e é forte.

| eixo | bucket minoritário (≤5%, 138 bullets) | bucket dominante (≥80%, 114 bullets) | diferença |
|---|---:|---:|---:|
| `roteiro_estrutura` | **32,6%** | 18,4% | **+14,2pp** |
| `critica_social` | 14,5% | 3,5% | **+11,0pp** |
| `ritmo` | 17,4% | 8,8% | +8,6pp |
| `expectativa` | 7,2% | 0,9% | +6,4pp |
| `comparacoes` | 2,2% | 1,8% | +0,4pp |
| `som_trilha` | 3,6% | 6,1% | −2,5pp |
| `impacto_emocional` | 5,1% | 11,4% | −6,3pp |
| `atuacao` | 8,7% | 15,8% | −7,1pp |
| `direcao_imagem` | 6,5% | 17,5% | **−11,0pp** |
| `tom_atmosfera` | 1,4% | 14,0% | **−12,6pp** |

E o mesmo padrão aparece na visão por bucket do catálogo inteiro (todos os 105
buckets, sem filtro de share):

| eixo | negativas | medianas | positivas |
|---|---:|---:|---:|
| `roteiro_estrutura` | **33%** | 24% | 18% |
| `ritmo` | 16% | 14% | 7% |
| `critica_social` | 11% | 9% | 9% |
| `expectativa` | 6% | 5% | 1% |
| `tom_atmosfera` | 5% | 4% | **13%** |
| `direcao_imagem` | 7% | 14% | **17%** |
| `atuacao` | 11% | 14% | 16% |
| `impacto_emocional` | 5% | 6% | 9% |

**Leitura.** A pergunta como formulada ("filmes unânimes usam eixos diferentes?")
responde **não** — 5a é plano. Mas a pergunta reformulada por bucket responde
**sim, e de forma muito clara**: o vocabulário do desagrado e o vocabulário do
elogio são estruturalmente diferentes.

**Quem não gostou fala de mecanismo; quem gostou fala de efeito.** Os buckets
minoritários (as poucas vozes discordantes num filme quase unânime) gastam um
terço dos bullets em `roteiro_estrutura`, mais `ritmo` e `expectativa` —
ou seja, apontam **onde o filme quebrou** e **o que prometeu e não entregou**.
Os buckets dominantes gastam nos eixos sensoriais e afetivos: `direcao_imagem`,
`tom_atmosfera`, `impacto_emocional`, `atuacao` — **como o filme foi**. `ritmo`
cai de 16% no negativo para 7% no positivo; `tom_atmosfera` sobe de 5% para 13%;
`direcao_imagem` de 7% para 17%.

Isso tem uma consequência de produto direta: o alinhamento por linha, que é a
promessa estrutural do Ponto 2, **está estruturalmente enviesado contra os
grupos minoritários**. Um eixo como `tom_atmosfera` quase nunca vai ter célula
preenchida no lado negativo (1,4% dos bullets), então a linha "Tom e atmosfera"
tende a sair com dois lados cheios e um vazio — e célula vazia lê-se como "este
grupo não falou disso", quando o mais provável é que este grupo tenha falado
disso em `roteiro_estrutura`.

**Limite.** 138 e 114 bullets são amostras razoáveis para essa comparação —
esta é a medição mais robusta do Bloco A. O que fica frágil é a atribuição
causal: não sei se o padrão vem do público (as pessoas realmente criticam
mecanismo e elogiam efeito) ou do prompt de síntese (§[D]). Os dois são
plausíveis e os dados aqui não separam.

---

# BLOCO B — Qualidade da síntese

## 6. Cobertura das reviews

**Método.** Três medições distintas, porque o pedido junta duas perguntas
diferentes.

**(6a) Sanidade agregada de `mencoes_aproximadas`** sobre os 629 bullets.

**(6b) Calibração manual contra o texto bruto.** Sub-amostra **registrada
antes**: os bullets de índice 5, 10, 15, 20, 25, 30, 35 e 40 da amostra
estratificada do estudo 10 (regra determinística: um a cada cinco). Para cada
um, varri **todas** as reviews da seleção de produção daquele bucket por
palavras-chave do tema e contei à mão quantas de fato afirmam aquilo.

**(6c) Reviews órfãs — proxy declarado.** *Não há dado que diga qual review
sustenta qual bullet.* O que existe é o eixo de cada review
(`consenso_verificado.jsonl`). Então: uma review é **órfã** quando nenhum dos
eixos que ela carrega é o eixo de nenhum bullet publicado no seu bucket. Isso é
um **limite superior de representação** (a review pode carregar o eixo certo e
mesmo assim falar de outra coisa) e um piso frouxo de orfandade. Está declarado
como proxy, não como medição direta.

### 6a — os números agregados

- **629 bullets · 0 clampados** (`mencoes_clampadas` é `false` em todos).
- **Menções por bullet:** média 10,7 · mediana 10 · min 1 · max 35.
- **Soma das menções por bucket:** média 64,0 sobre `n_validas ≈ 40` →
  razão média **1,67**, mediana 1,55, max 2,83. Ou seja: cada review analisada
  é contada, em média, em 1,7 bullets do seu bucket. Isso é esperado (uma review
  fala de várias coisas) e não é sinal de inflação por si só.

### 6b — calibração manual (8 bullets, sub-amostra registrada)

| # | filme / bucket / tema | `mencoes` | contagem à mão | razão |
|---|---|---:|---:|---:|
| 5 | `longlegs` neg — *Atuações e personagens fracos* | 7 | 7 | **1,00** |
| 10 | `napoleon-2023` med — *Batalhas visualmente impressionantes* | 15 | ~13 | 1,15 |
| 15 | `wonka` med — *Roteiro previsível e sem profundidade* | 7 | ~7 | 1,05 |
| 20 | `interstellar` pos — *Trilha sonora marcante* | 12 | ~9 | 1,33 |
| 25 | `cats-2019` neg — *Experiência de visualização desconfortável* | 10 | ~8 | 1,25 |
| 30 | `joker-folie-a-deux` med — *Comparação desfavorável com o primeiro filme* | 18 | 18 | **1,00** |
| 35 | `spider-man…` pos — *Cliffhanger e expectativa pela continuação* | 7 | ~9 | 0,78 |
| 40 | `pearl-2022` pos — *Crítica à repressão social* | 7 | ~8 | 0,88 |

**Razão média 1,06 · mediana 1,02 · intervalo 0,78–1,33.**

Fora da sub-amostra registrada, fiz mais 7 verificações **dirigidas por
suspeita** durante o estudo 10 (viesadas por construção — servem para achar o
pior caso, não para estimar a taxa). A pior:

- **`wonka` / negativas / *"Fotografia e efeitos visuais criticados"*, `mencoes`
  = 6 de 32.** Varredura completa do bucket por `cgi|visual|ugly|colou?r|
  greenscreen|efeito|feio|cenográf`: **2 reviews** casam, e só **1** sustenta o
  bullet (a que diz *"I am absolutely astonished at how ugly this movie is…
  bad greenscreen and CGI… this gross filter that takes all the color out"*).
  A outra faz uma queixa diferente (visuais "childlike"). Razão real ≈ **3–6×**.
- **`talk-to-me-2022` / negativas / *"Diálogos e tom juvenil artificiais"*,
  `mencoes` = 5 de 40.** Duas reviews sustentam. Razão ≈ 2,5×.

**Leitura de 6a+6b.** `mencoes_aproximadas` é **bem calibrado na mediana**
(1,02) e sem viés sistemático de inflação — nas 8 verificações registradas ele
erra para menos duas vezes e para mais seis, todas dentro de ±33%. O problema
não é o centro da distribuição, é a **cauda direita**: existe pelo menos um caso
no catálogo em que um número visível ao leitor (a barra do bullet, cuja largura
é `mencoes_aproximadas / n_reviews_analisadas`,
[filme.js:1370](frontend/js/filme.js:1370)) está 3 a 6 vezes acima do que o
texto bruto sustenta. Com 8 amostras registradas e 0 casos ruins entre elas, o
que posso dizer é: casos assim existem e não são a norma; não sei a taxa.

### 6c — órfãs por proxy de eixo

Universo: **2.866 reviews** que estão simultaneamente na seleção de produção e
no consenso classificado (de 4.056 analisadas — ver a nota de cobertura abaixo).

- **Órfãs: 332 de 2.866 = 11,6%.**
- Reviews com **nenhum eixo atribuído**: 57 = 2,0% (subconjunto das órfãs).
- Por bucket: negativas **12,5%** (126/1005) · medianas 9,6% (91/946) ·
  positivas **12,6%** (115/915).

**Por filme (extremos):**

| pior | órfãs | | melhor | órfãs |
|---|---:|---|---|---:|
| `spider-man-across-the-spider-verse` | 23% (14/62) | | `aftersun` | 4% (2/53) |
| `dune-part-two` | 21% (20/95) | | `hereditary` | 4% (2/51) |
| `dune-2021` | 19% (10/53) | | `perfect-days-2023` | 4% (2/47) |
| `the-invite-2026` | 18% (22/120) | | `the-hateful-eight` | 6% (5/90) |
| `wicked-2024` / `wonka` | 18% | | `the-substance` | 6% (3/51) |

**Piores buckets:** `obsession-2026`/negativas 40% (2 de 5 — bucket degradado),
`wonka`/positivas 33% (11/33), `spider-man…`/negativas 32% (7/22),
`the-invite-2026`/medianas 30% (12/40), `wicked-2024`/positivas 29% (7/24).

**Nota de cobertura, que limita tudo em 6c.** A classificação por eixo cobre
**2.866 de 4.056 reviews analisadas = 70,7%**. Só 4 filmes estão em 100%
(`cure`, `cidade-de-deus`, `the-invite-2026` — os três da extensão da v1.9.15 —
e `obsession-2026`, que tem só 19 reviews analisadas no total). Sete filmes
estão abaixo de 50%: `perfect-days-2023` 39%, `hereditary` 42%, `the-substance`
42%, `everything-everywhere-all-at-once` 43%, `aftersun` 44%, `dune-2021` 44%,
`bones-and-all` 48%. **Isso inverte a leitura ingênua da tabela acima:**
`aftersun` e `hereditary` aparecem como "melhores" em orfandade porque sua
população classificada é menor e mais enviesada, não porque estejam melhor
cobertos.

**Leitura.** Cerca de **1 review em 9** da seleção de produção não fala de
nenhum assunto que virou bullet no seu grupo, mesmo sob a medida mais
generosa possível (basta compartilhar um eixo, não o tema). O número é
razoável para um produto que publica 6 temas por grupo — mas ele **não é
uniforme**: nos buckets minoritários e nos filmes de recepção mais fragmentada
(`spider-man`, `dune-part-two`, `wonka`, `wicked`) chega a 1 em 3. E porque é um
limite superior de representação, a orfandade real (review que não sustenta
nenhum bullet **específico**) é necessariamente maior que 11,6%.

**Limite.** O proxy de eixo é frouxo, a cobertura da classificação é de 70,7% e
desigual entre filmes, e a calibração manual repousa em 8 casos registrados.
Nenhum dos três números deste estudo deve ser citado sem essas três ressalvas
juntas.

---

## 7. Redundância entre bullets

**Método.** Pares de `tema` do **mesmo filme e mesmo bucket** (1.570 pares em
105 buckets). Similaridade = Dice sobre sacos de palavras de conteúdo
normalizadas (mesma normalização do estudo 4). **Limiar de "redundante" fixado
em Dice ≥ 0,50 antes de olhar os resultados** — nível em que metade do
vocabulário de conteúdo é compartilhado.

**Números.**

| | valor |
|---|---|
| pares avaliados | 1.570 |
| Dice médio | 0,002 |
| Dice mediano | **0,000** |
| Dice p90 / p99 | 0,000 / 0,000 |
| Dice **máximo do catálogo** | **0,333** |
| pares ≥ 0,50 (limiar registrado) | **0** |
| pares ≥ 0,30 | 3 (0,2%) — em 3 filmes |

**Os 5 pares mais redundantes do catálogo** (nenhum atinge o limiar; listados
porque o pedido pede os cinco mais próximos):

| Dice | filme / bucket | eixos | A | B |
|---:|---|---|---|---|
| **0,333** | `pearl-2022` / negativas | `roteiro_estrutura` × `roteiro_estrutura` | *Personagem principal irritante* | *Falta de desenvolvimento dos personagens* |
| **0,333** | `parasite-2019` / positivas | `direcao_imagem` × `direcao_imagem` | *Direção e simbolismo visual* | *Fotografia e direção de arte* |
| **0,333** | `dune-2021` / positivas | `tom_atmosfera` × `ritmo` | *Construção de mundo imersiva* | *Ritmo lento, mas com construção* |
| 0,286 | `the-substance` / negativas | `tom_atmosfera` × `ritmo` | *Exibicionismo e nudez excessiva* | *Duração excessiva e ritmo lento* |
| 0,286 | `avengers-endgame` / negativas | `roteiro_estrutura` × `critica_social` | *Desenvolvimento de personagens decepcionante* | *Tratamento injusto de personagens femininas* |

Apenas **2 pares** de todo o catálogo têm Dice ≥ 0,30 **e** o mesmo eixo (os
dois primeiros da tabela).

**Mas a redundância existe — só não é lexical.** Trocando a lente de "duas
frases parecidas" para "dois bullets no mesmo eixo":

- **79 dos 105 buckets (75%) publicam dois ou mais temas no mesmo eixo.**
- Distribuição: `roteiro_estrutura` ×2 em 34 buckets, ×3 em 12, ×4 em 2;
  `critica_social` ×2 em 11 e ×3 em 1; `direcao_imagem` ×2 em 6;
  `impacto_emocional` ×2 em 5; `tom_atmosfera` e `ritmo` ×2 em 3 cada;
  `atuacao` e `livre` ×2 em 1 cada.

**Leitura.** O prompt de síntese (§[D]) **não repete palavras dentro de um
bucket** — mediana de sobreposição zero, máximo 0,333, nenhum par acima do
limiar. Isso é um resultado positivo e vale registrar como tal: a lista de 6
temas de um grupo é lexicalmente limpa.

O que ele repete é **assunto**. Em 3 de cada 4 buckets do catálogo, dois ou mais
bullets caem no mesmo eixo — e em `roteiro_estrutura` isso chega a quatro
bullets do mesmo eixo no mesmo grupo. O caso mais grave que o pedido antecipava
("dois bullets do mesmo eixo que dizem quase a mesma coisa") existe, mas escapa
da medida de palavras: *"Personagem principal irritante"* e *"Falta de
desenvolvimento dos personagens"* (`pearl-2022`/negativas) compartilham só a
palavra "personagem" e são, para o leitor, a mesma queixa duas vezes.

Consequência de desenho: enquanto [D] escolhe 6 temas por bucket sem ver os
eixos, e [D3] rotula depois sem poder mudar a lista, essa colisão é
**estrutural**, não acidental. Fechar isso exigiria [D] conhecer o eixo no
momento da escolha — o que é uma mudança de arquitetura, não um ajuste de
prompt.

**Limite.** Dice sobre palavras de conteúdo é a medida barata que o pedido
autoriza e ela mede o que sabe medir. Ela produz um **piso** de redundância
(0 pares), não um teto. A medida de colisão de eixo (75% dos buckets) é o teto
grosseiro do lado oposto: nem todo par no mesmo eixo é redundante.

---

## 8. Estabilidade da margem — bootstrap sobre rótulos já classificados

**O que este estudo mede, e o que ele NÃO mede.** Ele reamostra, com reposição,
as **reviews já rotuladas** de cada bucket e recalcula lift e margem. Portanto
mede a **sensibilidade do corte de 20pp à variação de amostra** — "se eu tivesse
sorteado outras 40 pessoas do mesmo grupo, este eixo continuaria passando?".
Ele **não** mede a estabilidade da classificação em si: cada review carrega
exatamente o mesmo conjunto de eixos em todas as reamostragens. Se o classificador
mudasse de ideia sobre uma review, este estudo não veria. Essa segunda pergunta
já tem medição própria em `ESTABILIDADE_AGREGADA.md` (26,5% de reprodutibilidade
individual antes da votação de 3) e não é o que está aqui.

**Método.** B = 2.000 reamostragens por filme, semente 24. Dentro de cada bucket,
sorteio com reposição preservando o n (a população é exatamente a que o bloco
publicado conta: seleção de produção ∩ consenso verificado). Recalculo
`freq(eixo, bucket)`, `lift = freq − max(freq nos outros dois)` e comparo com
20pp em **`Fraction` exato**, como o código de produção
([src/espectro24/eixos.py](src/espectro24/eixos.py)). Registro, por eixo e por
filme, em que fração das reamostragens ele passaria.

**Números — visão geral.**

- Das 1.050 células (35 filmes × 10 eixos × 3 buckets), **31 passam a margem no
  observado** — 3,0%.
- Dessas 31 marcações publicadas: **1** sobrevive a ≥90% das reamostragens,
  **17** ficam entre 60% e 90%, e **13** ficam **abaixo de 60%**.
  Média 64%, mediana 62%.
- **A única marcação robusta do catálogo inteiro** é
  `eighth-grade` / `impacto_emocional` / positivas, com **p = 92%**.

**Números — probabilidade de o filme continuar com ≥1 eixo acima da margem.**

| | n | média | mediana | extremo |
|---|---:|---:|---:|---|
| filmes publicados `tematico` | 18 | **92,5%** | 93,5% | mín. 82,5% (`the-invite-2026`) |
| filmes publicados `valorativo` | 17 | **71,9%** | 75,3% | máx. 92,0% (`the-substance`) |

Ou seja: um filme `valorativo` médio **viraria `tematico` em ~72% das
reamostragens**. A assimetria é em parte artefato conhecido — o "melhor lift" é
um **máximo sobre 30 células**, e o máximo de um conjunto ruidoso é
enviesado para cima sob bootstrap. Mas a ordem de grandeza é a mesma que a SPEC
§2.5 já registra por outro caminho (nulo de permutação: **34% dos pares acima de
20pp cruzariam por acaso**), e as duas medições independentes concordam que
20pp, com n≈30 por bucket, é uma fronteira porosa.

**Números — os eixos na fronteira (passam no observado, p entre 60% e 90%).**

| filme | eixo | bucket | p |
|---|---|---|---:|
| `obsession-2026` | `atuacao` | positivas | 87% |
| `cats-2019` | `tom_atmosfera` | positivas | 85% |
| `hereditary` | `ritmo` | negativas | 85% |
| `obsession-2026` | `som_trilha` | medianas | 83% |
| `hereditary` | `atuacao` | medianas | 78% |
| `obsession-2026` | `tom_atmosfera` | positivas | 76% |
| `cure` | `tom_atmosfera` | positivas | 75% |
| `obsession-2026` | `direcao_imagem` | positivas | 75% |
| `anatomy-of-a-fall` | `ritmo` | negativas | 72% |
| `perfect-days-2023` | `tom_atmosfera` | positivas | 68% |
| `obsession-2026` | `impacto_emocional` | positivas | 67% |
| `everything-everywhere-all-at-once` | `direcao_imagem` | medianas | 66% |
| `spider-man-across-the-spider-verse` | `comparacoes` | medianas | 65% |
| `interstellar` | `atuacao` | negativas | 63% |
| `obsession-2026` | `comparacoes` | positivas | 62% |
| `wonka` | `direcao_imagem` | medianas | 61% |
| `hereditary` | `direcao_imagem` | medianas | 60% |

**E os 13 mais frágeis ainda (p < 60%) — estes são publicados como contraste e
não sobreviveriam a metade das reamostragens:**

| filme | eixo | bucket | p |
|---|---|---|---:|
| `spider-man-across-the-spider-verse` | `direcao_imagem` | medianas | **38%** |
| `wonka` | `atuacao` | medianas | **42%** |
| `bones-and-all` | `atuacao` | medianas | 47% |
| `the-invite-2026` | `tom_atmosfera` | positivas | 48% |
| `joker-folie-a-deux` | `roteiro_estrutura` | medianas | 50% |
| `dune-part-two` | `ritmo` | negativas | 52% |
| `barbie` | `comparacoes` | negativas | 53% |
| `bones-and-all` | `impacto_emocional` | negativas | 53% |
| `the-hateful-eight` | `tom_atmosfera` | positivas | 54% |
| `everything-everywhere-all-at-once` | `critica_social` | negativas | 55% |
| `napoleon-2023` | `impacto_emocional` | negativas | 55% |
| `perfect-days-2023` | `impacto_emocional` | positivas | 56% |
| `napoleon-2023` | `ritmo` | medianas | 58% |

**O simétrico, que é igualmente informativo:** 45 combinações filme-eixo que
**não** passam no observado passariam em ≥25% das reamostragens. Os casos mais
próximos de entrar: `obsession-2026`/`roteiro_estrutura` 55%,
`the-substance`/`tom_atmosfera` 45%, `the-godfather`/`ritmo` 45%,
`im-still-here-2024`/`impacto_emocional` 44%, `the-substance`/`atuacao` 43%,
`dune-part-two`/`impacto_emocional` 42%,
`im-still-here-2024`/`roteiro_estrutura` 42%,
`joker-folie-a-deux`/`impacto_emocional` 42%.

**Leitura.** O estado `contraste` é razoavelmente robusto **numa direção só**: um
filme publicado como `tematico` continua tendo algum contraste em 92,5% das
reamostragens. O que é frágil é (i) **qual** eixo é o contraste — metade das
marcações publicadas cai abaixo de 60%, e a mais fraca (`spider-man`,
`direcao_imagem`, medianas) sobrevive a 38% —, e (ii) o rótulo `valorativo`,
que é o mais comum do catálogo e o menos estável dos dois.

Isso reordena a prioridade de risco do produto. A frase "os três grupos falam
das mesmas coisas e discordam só no valor" é uma afirmação forte sobre o filme,
e é a que o dado sustenta menos. A frase "este grupo fala de X e os outros não"
é sustentada com mais firmeza no agregado, mas quase nunca no eixo específico
que a interface nomeia.

`obsession-2026` merece nota à parte: seus buckets têm n = 5, 6 e 8. Com esse
denominador o quantum do lift é de 12 a 20pp — um único voto atravessa a margem.
Ele aparece com p = 100% de "ter contraste" e seis eixos na fronteira porque
praticamente qualquer sorteio produz algum lift de 20pp. Não é um filme com
contraste forte; é um filme sem denominador.

**Limite.** Bootstrap não fabrica informação: ele descreve a variabilidade
**da amostra que existe**, não a da população. Além disso, o viés de
máximo-sobre-30-células infla o p a nível de filme e não o p a nível de célula —
por isso a leitura por célula (as duas tabelas de fronteira) é a mais confiável
deste estudo, e a comparação `tematico` vs `valorativo` a menos.

---

## 9. Concordância / força do bullet

**Resposta curta: o dado não existe. Isto é uma limitação de instrumentação, e
não vou inventar um proxy para ela.**

**Método de verificação.** Inspecionei o schema de todas as fontes de
classificação por review:

| arquivo | campos por review |
|---|---|
| `passe_1/2/3/4.jsonl` (8.171 linhas cada) | `ok`, `taxonomia_id`, `passe`, `slug`, `perfil`, `bucket`, `id`, `nivel`, `n_chars`, `eixos`, `temas_livres`, `eixos_invalidos`, `uso`, `tentativas` |
| `consenso.jsonl` / `consenso_verificado.jsonl` (4.181) | + `votos`, `eixos_por_passe` |
| `verificador_producao.jsonl` (3.162) | `confirma`, `frase`, `alvo` — **só para `impacto_emocional`**, e `alvo` é filme/espectador, não polaridade |

**Nenhum campo carrega polaridade.** `eixos` é um conjunto de assuntos; nada diz
se a review falou bem ou mal daquele assunto. `nivel` é a nota da review inteira
(e é o que define o bucket), não a valência por eixo. `verificador_producao`
distingue se `impacto_emocional` fala do filme ou do espectador — uma dimensão
diferente. Portanto **a proporção pedida — menções positivas vs negativas do
mesmo eixo dentro do mesmo bucket — não é computável a partir do que está em
disco.**

**Por que isso importa mais do que parece.** A célula publicada diz *"Atuação —
`atuacao`, 3 de 18"* no grupo negativo. Ela não diz, e não pode dizer, se essas
3 reviews criticam a atuação ou se são reviews de nota 1,5 que **elogiam** a
atuação enquanto detonam o resto. Durante o estudo 10 encontrei os dois casos
lado a lado no mesmo bucket:

- `longlegs` / **negativas** / eixo `atuacao`: uma review diz *"Die Schauspieler
  wirken uninspiriert und hölzern"* e outra, no mesmo bucket, *"Two stars for
  the acting as it's all the film has going for it"* e uma terceira *"Maika
  Monroe was great though"*. O bullet publicado é *"Atuações e personagens
  fracos"*.
- `aftersun` / **medianas** / eixo `atuacao`: uma review chama a química
  pai-filha de *"perfect chemistry between Frankie Corio and Paul Mescal"* e
  outra diz que Mescal *"just doesn't have the chops"*. O bullet publicado é
  *"Atuações convincentes"*, com exemplo citando *"uma atuação notável de Paul
  Mescal"*.

Isto é divergência interna dentro do bucket **e dentro do eixo**, e o schema não
tem onde registrá-la.

**O que é mensurável hoje, declarado como o que é.** Não é polaridade por
review; é uma medida sobre o **texto da síntese**: com que frequência o próprio
bullet admite a divergência, via marcador concessivo (`mas`, `porém`, `embora`,
`apesar`, `enquanto outros`, `divide opiniões`, `alguns … outros`) no `tema` ou
no `exemplo_parafraseado`.

- **153 de 629 bullets (24,3%)** carregam marcador — 15 no `tema` (2,4%) e 152
  no `exemplo` (24,2%).
- Por bucket: **medianas 33%**, positivas 20%, negativas 19%.
- Por eixo: `expectativa` **64%**, `som_trilha` 35%, `ritmo` 30%, `atuacao` 28%,
  `direcao_imagem` 28%, `comparacoes` 27%, `critica_social` 18%,
  `impacto_emocional` 17%, `roteiro_estrutura` 16%, `tom_atmosfera` 15%.

Exemplos: *"Fotografia bonita, mas execução fraca"* (`aftersun`/neg),
*"Atuações boas, mas personagens sem profundidade"* (`cure`/med),
*"Atuação boa apesar dos problemas"* (`pearl-2022`/neg),
*"Ritmo lento no início, mas que compensa"* (`the-hateful-eight`/pos),
*"O desempenho de alguns atores… é elogiado, enquanto outros são criticados"*
(`avengers-endgame`/med, no exemplo).

**Leitura.** A síntese **sabe** que há divergência interna e a expressa em cerca
de um quarto dos bullets, com pico no grupo do meio (33%) — que é exatamente
onde ela deve estar. Mas essa admissão é **editorial e não instrumentada**: mora
na prosa do `exemplo_parafraseado`, não num campo, e por isso não pode ser
verificada, contada por eixo pelo pipeline, nem usada pela interface para
qualificar a barra. O número que a interface exibe (a barra do bullet) é
silenciosamente unipolar.

**Limite.** A contagem de marcadores mede como a síntese escreve, não como as
reviews se distribuem. Um bullet sem "mas" pode estar cobrindo um bucket
perfeitamente unânime ou apagando uma divisão de 50/50 — os dois casos ficam
indistinguíveis. **Não trate os 24,3% como estimativa da taxa de divergência
interna.**

---

## 10. Faithfulness dos bullets — amostra estratificada

### Critério de amostragem, registrado ANTES da leitura

Universo: os 629 bullets publicados, cada um com o eixo que [D3] lhe atribuiu.
Regras aplicadas nesta ordem, por
`scripts` ad-hoc de amostragem (scratchpad da sessão):

- **R1.** 4 bullets por eixo da taxonomia fechada (10 eixos) → **N = 40**.
- **R2.** Dentro do eixo, cobrir os 3 buckets; a 4ª vaga vai para o bucket
  `índice_do_eixo mod 3`, para que a folga circule entre os buckets.
- **R3.** Nenhum filme repetido dentro de um eixo; no máximo 2 bullets por filme
  no total.
- **R4.** Empates resolvidos por PRNG com **semente 24** sobre a lista de
  candidatos ordenada por `(slug, bucket, índice_do_tema)`. Nada escolhido a
  dedo.
- **R5.** Célula (eixo, bucket) sem candidato elegível passa a vaga ao bucket
  seguinte, com registro. **Não foi acionada** — todas as células tinham
  candidato.

Amostra resultante: **40 pares · 14 negativas / 13 medianas / 13 positivas ·
4 por eixo em todos os 10 eixos · 31 filmes distintos** (9 filmes com 2 bullets).

### Protocolo de leitura, também registrado

Para cada bullet, li: **(a)** as reviews da seleção de produção daquele bucket
classificadas no eixo do bullet (até 12, por tamanho decrescente) — o conjunto de
**melhor caso**; **(b)** até 6 reviews do mesmo bucket que casam por palavra de
conteúdo do tema e não entraram em (a). Nenhuma review de fora do bucket. Em 7
casos rodei também uma varredura de palavra-chave sobre **todo** o bucket
(registradas na seção 6b e nos comentários abaixo).

**O viés deste protocolo é conhecido e favorece o produto:** ao começar pelas
reviews que já carregam o eixo do bullet, procuro suporte onde ele é mais
provável. Isso torna um veredito de "não encontrado" muito forte e um veredito
de "suporte direto" mais fácil de obter que numa leitura cega.

### Categorias

- **suporte direto** — ≥2 reviews do bucket afirmam explicitamente o que o
  bullet (tema + exemplo) afirma.
- **extrapolação legítima** — as reviews sustentam o núcleo; o bullet o formula
  num nível de abstração acima, e a inferência é curta e segura.
- **generalização excessiva** — há algum suporte, mas o bullet excede em
  **escopo**, **quantificador** ou **especificidade**; ou `mencoes_aproximadas`
  está muito acima do que o texto sustenta; ou o bullet apaga uma contracorrente
  visível do mesmo bucket.
- **informação não encontrada** — nenhuma review lida sustenta a afirmação.

### Distribuição

| categoria | n | % |
|---|---:|---:|
| suporte direto | **31** | 77,5% |
| extrapolação legítima | 4 | 10,0% |
| generalização excessiva | 5 | 12,5% |
| **informação não encontrada** | **0** | **0%** |

### Exemplos — generalização excessiva (todos os 5)

**1. `wonka` / negativas / `direcao_imagem` — *"Fotografia e efeitos visuais
criticados"*, `mencoes` = 6 de 32.**
Exemplo publicado: *"A estética visual foi duramente criticada, com uso excessivo
de CGI, cenários artificiais e uma paleta de cores desbotada, tornando o filme
feio aos olhos."*
Varredura completa do bucket: **2 de 32** reviews tocam visual, e **uma só**
sustenta o exemplo — e o sustenta inteiro, quase palavra por palavra:
> *"I am absolutely astonished at how ugly this movie is… bad CG… wayyyy more of
> it just constantly… Amidst all the bad greenscreen and CGI is the occasional
> physical prop or set, which look so cheap… the whole movie has this gross
> filter that takes all the color out"*

A outra review faz uma queixa diferente (*"the visuals seemed very childlike"*).
**Uma review individual virou tema de grupo com contagem 6.** Este é o pior caso
que encontrei no catálogo.

**2. `interstellar` / positivas / `direcao_imagem` — *"Fotografia e efeitos
visuais deslumbrantes"*, `mencoes` = 11 de 40.**
O tema é impecavelmente sustentado (*"The cinematography is breathtaking"*,
*"a visual marvel"*, *"This movie is just stunning"*, *"the shots in the movie
are amazing"*). O **exemplo** não é: *"…especialmente das paisagens espaciais e
dos buracos negros, que são considerados alguns dos melhores já vistos no
cinema."* Varredura de `black hole|buraco negro|czarn|planet|landscape` em todas
as 40: **3 matches**, e o único que fala do buraco negro fala **mal** —
> *"sam film wydaje się myśleć że jest inteligentniejszy niż faktycznie jest
> (i to strasznie widać podczas sekwencji w czarnej dziurze)"*
> [o filme parece se achar mais inteligente do que é — e isso é gritante na
> sequência do buraco negro]

A especificidade foi acrescentada pela síntese, e acrescentada invertendo o sinal
da única evidência disponível.

**3. `napoleon-2023` / medianas / `direcao_imagem` — *"Batalhas visualmente
impressionantes"*, `mencoes` = 15 de 40.**
O tema tem suporte abundante (*"Ridley Scott still knows how to direct great
battle sequences"*, *"ensevelit ses batailles dans une lumière somptueuse"*,
*"truly spectacular action set pieces"*, *"as primeiras cenas de lutas são
lindas"*, *"the battle scenes were well made"*). O **quantificador** do exemplo
não: *"…sendo o ponto alto do filme **para a maioria dos espectadores deste
grupo**."* Com `mencoes` = 15 de 40, isso é 37,5%. Não é maioria, pelo próprio
número que o produto publica ao lado.

**4. `cats-2019` / negativas / `impacto_emocional` — *"Experiência de
visualização desconfortável"*, `mencoes` = 10 de 40.**
O exemplo é sustentado quase literalmente por uma review (*"Es tan incómoda de
ver que ni siquiera da risa, solo da ganas de pausarla a los diez minutos"* vs.
*"a vontade é de interromper a exibição logo no início"*), e ~8 reviews
descrevem desconforto. Mas o bucket tem uma **contracorrente grande e explícita**
que o bullet apaga: *"this movie is so awful that it's funny and weirdly good"*,
*"my friends and i have seen this film like 3 times and its been the most fun
ive had"*, *"As a drinking game- this movie is phenomenal"*, *"I would never
recommend it, but I have watched it several times with a smile on my face"*.
Dizer que *"o filme gera um mal-estar constante"* como característica do grupo,
quando parte substantiva do grupo relata prazer irônico, é escopo excessivo.

**5. `talk-to-me-2022` / negativas / `tom_atmosfera` — *"Diálogos e tom juvenil
artificiais"*, `mencoes` = 5 de 40.**
O exemplo é uma paráfrase próxima de **uma** review:
> *"esses elementos minimamente interessantes são sufocados por várias piadas sem
> graça e gírias ultrapassadas. Parece que o roteirista passou cinco minutos na
> internet e pensou: 'Ah, então é assim que os jovens se comunicam'"*

vs. o publicado: *"As piadas e gírias usadas parecem forçadas, como se o
roteirista tentasse imitar a linguagem jovem sem naturalidade."* Uma segunda
review apoia de longe (*"parecer que foi um adolescente estranho no ensino médio
… que escreveu o roteiro"*). Varredura completa: **2 de 40**, contra `mencoes`
= 5. *(Nota lateral: o bullet está no eixo `tom_atmosfera`, mas a review fala de
roteiro e diálogo — um caso de rótulo [D3] deslocado.)*

### Exemplos — extrapolação legítima (todos os 4)

**1. `dune-2021` / medianas / `ritmo` — *"Ritmo lento e falta de ação"***
(`mencoes` = 15/40). "Lento" está por toda parte (*"The pacing is soooo slow"*,
*"it moves slowly"*, *"so much exposition, and it feels so stiff"*). "Falta de
ação" não é dito por ninguém — o mais próximo é *"tiene mucho silencio"*. A
inferência é curta e defensável.

**2. `the-northman` / negativas / `roteiro_estrutura` — *"Roteiro fraco e
previsível"*** (21/40). Amplamente sustentado (*"Hikaye klişe"*, *"Generic
Hamlet imitation"*, *"one drawn-out plot… no attempt at subtlety"*, *"lazy
writing"*). Mas o exemplo afirma *"tornando o desfecho óbvio desde o início"*, e
nenhuma review diz isso; a que fala do final diz o oposto — *"very anticlimactic
to have your arch-nemesis be a sheep farmer"*. Clichê ⇒ previsível é uma
inferência aceitável, mas é inferência.

**3. `dune-part-two` / positivas / `tom_atmosfera` — *"Escala épica e construção
de mundo"*** (12/40). "Épico" e "efeitos visuais" estão nas reviews (*"o
suprassumo do épico"*, *"los efectos visuales… Absolutamente todo funciona"*);
"construção de mundo" e "imersão completa no universo de Duna" são a moldura da
síntese, não a palavra do público. *(Este bullet tem também o pior descolamento
número/rótulo do catálogo — ver a seção de achados estruturais abaixo.)*

**4. `bones-and-all` / positivas / `impacto_emocional` — *"Final impactante e
emocional"*** (11/40). "Devastador e memorável" está lá (*"o final me traz uma
angústia tão grande"*, *"si le puse 4 estrellas fue prácticamente por ese final
porque wow"*). A cláusula *"redefinir a compreensão de toda a narrativa"* é
inferida de uma leitura só.

### Exemplos — suporte direto (5 dos 31, os mais exatos)

**1. `interstellar` / positivas / `som_trilha` — *"Trilha sonora marcante"*.**
Exemplo: *"…um dos melhores trabalhos do compositor, com destaque para o
órgão."* Reviews: *"Every single time Hans Zimmer's organ music swells in
Interstellar, I get chills"* · *"the score is probably hans zimmer's best work
imo"* · *"Hans Zimmer's score is unforgettable"* · *"The best score"*. Cada
elemento do exemplo tem uma frase atrás.

**2. `joker-folie-a-deux` / medianas / `som_trilha` — *"Musical deslocado"*.**
Exemplo: *"…desnecessária e desconectada, não contribuindo para o avanço da
trama… apenas arrastando o ritmo."* Review: *"the musical numbers feel
completely unnecessary since they don't add anything and only slow the movie
down even more"*. Praticamente uma tradução, com mais 4 reviews concordando.

**3. `im-still-here-2024` / medianas / `impacto_emocional` — *"Falta de conexão
emocional"*.** Exemplo: *"…não conseguiram se conectar afetivamente com a
história, apesar de reconhecerem sua importância."* Review: *"exige una conexión
emocional con ese contexto que, al menos en mi caso, nunca terminó de aparecer.
Entiendo perfectamente la importancia que tiene para Brasil…"*. Mais três:
*"I respect what it's trying to do but I honestly struggled to stay fully
engaged"*, *"A temática é extremamente importante, mas a forma como foi montada
não me causou muito impacto"*.

**4. `avengers-endgame` / positivas / `comparacoes` — *"Comparação com Infinity
War"*.** Exemplo: *"Parte dos fãs debateram se este filme é superior ou inferior
ao anterior, com alguns preferindo a abordagem mais focada nos heróis e outros
achando que a narrativa do filme anterior era mais coesa."* Os dois lados do
debate estão literalmente no bucket: *"I like this better than Infinity War and
I'll explain why: Infinity War kinda glosses over characters… I just prefer the
heroes with multiple movies of growth"* contra *"Infinity war is still the more
beautiful twin… so many odd plot holes in place that just make it the weaker of
the two films"* e *"Not as good as infinity war"*. O bullet reproduz uma
estrutura de desacordo, não uma média.

**5. `everything-everywhere-all-at-once` / negativas / `expectativa` —
*"Superestimado e prêmios injustificados"*.** Exemplo: *"…aspectos como montagem
são elogiados, mas o conjunto não justifica o reconhecimento."* Review:
*"Eu realmente acredito que a campanha desse filme no Oscar foi um delírio
coletivo… não consigo enxergar uma obra digna de sete estatuetas aqui. Para mim,
o único prêmio realmente justificável é o de **Melhor Montagem**."* A ressalva
sobre montagem — que parecia a parte mais arriscada do bullet — é a mais
rastreável. Varredura completa do bucket: 11 de 40 reviews falam de hype/prêmios,
contra `mencoes` = 8. Aqui o produto **subconta**.

### Um achado estrutural que este estudo produziu de lado

A frequência que a interface **mostra** (largura da barra =
`mencoes_aproximadas / n_reviews_analisadas`, sobre as ~40 analisadas) e a
frequência que o produto **usa para decidir contraste** (`mencoes / de_n` do
eixo, sobre as ~23 classificadas) são dois instrumentos diferentes sobre duas
populações diferentes. Medindo os 619 pares tema↔eixo do catálogo:

- diferença mediana: a frequência do tema fica **11,8pp abaixo** da do seu eixo
  (esperado — um eixo agrega vários temas);
- mas em **30 bullets (5%)** a frequência do tema **excede** a do próprio eixo em
  mais de 20pp, o que seria aritmeticamente impossível se as duas medissem a
  mesma coisa sobre as mesmas pessoas.

Os piores:

| filme / bucket | tema | freq do TEMA | freq do EIXO |
|---|---|---:|---:|
| `avengers-endgame` / positivas | *Batalha final épica e fan service* (`tom_atmosfera`) | 45% (18/40) | **0%** (0/18) |
| `parasite-2019` / positivas | *Crítica social e desigualdade de classes* (`critica_social`) | 87,5% (35/40) | 55,3% |
| `friday-the-13th-2009` / positivas | *Jason mais assustador e brutal* (`tom_atmosfera`) | 75% | 23,8% |
| `joker-folie-a-deux` / negativas | *Números musicais deslocados* (`som_trilha`) | 75% | 28,1% |
| `shutter-island` / positivas | *Atmosfera imersiva* (`tom_atmosfera`) | 70% | 25,7% |
| `dune-2021` / positivas | *Construção de mundo imersiva* (`tom_atmosfera`) | 50% | 7,1% |
| `dune-part-two` / positivas | *Escala épica e construção de mundo* (`tom_atmosfera`) | 30% (12/40) | **2,9%** (1/35) |

`avengers-endgame` é o caso limite: um bullet exibido com barra de 45% num eixo
cuja contagem naquele bucket é **zero**. A SPEC §[D3] antecipa exatamente esse
modo de falha ("o modo de falha é de legenda, nunca de aritmética") e ele está
confirmado aqui em escala: 5% dos bullets do catálogo.

### Leitura do estudo 10

**Nada foi fabricado.** Zero de 40 bullets afirmam algo que nenhuma review do
seu bucket sustenta. Para um produto que resume 40 textos livres em 6 frases,
esse é o resultado mais importante do relatório, e vale enunciá-lo sem
qualificações extras: nas 40 amostras lidas, **toda afirmação publicada tinha
alguém no bucket dizendo aquilo**.

**O modo de falha real não é invenção; é promoção.** Os 5 casos de generalização
excessiva têm todos a mesma forma: uma observação verdadeira, feita por uma ou
duas pessoas, é **promovida à condição de característica do grupo** — por um
quantificador ("a maioria"), por uma contagem inflada (`mencoes` 6 quando o texto
sustenta 1), ou pelo silêncio sobre uma contracorrente do mesmo tamanho. Em três
dos cinco (`wonka`, `talk-to-me`, `interstellar`) o exemplo parafraseado é uma
tradução próxima de **uma única review** — o que é ótimo para fidelidade
literal e enganoso para representatividade.

**A síntese acerta mais nos detalhes específicos do que nos quantificadores.**
"Melhor Montagem" em EEAAO, o órgão de Zimmer em `interstellar`, os dois lados
do debate Endgame×Infinity War, os nomes *Lady Bird* e *The Edge of Seventeen*
em `eighth-grade` — todos rastreáveis a frases exatas. Os erros estão nas
palavras de quantidade e de escopo, que são justamente as que nenhuma review
individual pode confirmar ou desmentir.

**Limite da amostra.** N = 40 de 629 (6,4%). Com 0 fabricações observadas em 40,
o limite superior de 95% para a taxa real é ≈ **7,5%** (regra de três) — ou seja,
o dado é compatível com até 1 em 13 bullets do catálogo sendo fabricado, e não
com "zero fabricação no catálogo". Some a isso o viés do protocolo (comecei
pelas reviews que carregam o eixo do bullet) e a leitura correta é: **a
fabricação não é o modo de falha dominante deste produto; a inflação de escopo
é.**

---

# Resumo

**Bloco A — a estrutura.** O produto tem uma taxonomia de 10 eixos, mas publica
como se tivesse 6 ou 7: `roteiro_estrutura` absorve 25% de todos os bullets,
está em 35 de 35 filmes e em 100% dos filmes de todos os gêneros, e é o eixo que
recebe o excedente em todos os filmes mais concentrados — virou o `livre` de
facto. A dispersão por filme é constante (mediana 7 eixos de 10, HHI 0,12–0,28)
porque o teto de 18 bullets a determina, não porque os filmes se pareçam. O
gênero quase não prevê nada, e a hipótese de que comédia e terror seriam mais
`valorativo` se quebrou nos dois sentidos ao mesmo tempo (comédia é a mais
temática, 83%; terror a menos, 44%) com n de 6 e 9 — hipótese, não conclusão.
O sinal estrutural mais forte do bloco não é por gênero, é por **grupo**: quem
não gostou fala de mecanismo (`roteiro_estrutura` 33%, `ritmo` 16%), quem gostou
fala de efeito (`tom_atmosfera` 13%, `direcao_imagem` 17%), e isso enviesa o
alinhamento por linha contra os grupos minoritários.

**Bloco B — a qualidade.** A síntese não inventa: 0 de 40 bullets auditados
afirmam algo sem lastro no bucket, e os detalhes específicos são rastreáveis a
frases exatas. O que ela faz é **promover** — uma observação de uma pessoa vira
característica do grupo, por quantificador ("a maioria", com 37,5%), por
contagem (`mencoes` 6 onde o texto sustenta 1, em `wonka`) ou por omissão da
contracorrente (o prazer irônico em `cats-2019`). Duas fragilidades de
instrumentação sustentam isso: não há polaridade por review, então "3 de 18 em
`atuacao`" não distingue elogio de crítica dentro do mesmo grupo; e o número que
o leitor vê (barra, sobre 40 analisadas) e o número que decide o contraste
(lift, sobre ~23 classificadas) vêm de populações diferentes — em 5% dos bullets
eles se contradizem, com o caso extremo de uma barra de 45% num eixo de contagem
zero. O bootstrap fecha o quadro: das 31 marcações de contraste publicadas, **1**
sobrevive a 90% das reamostragens e 13 ficam abaixo de 60%; o rótulo
`valorativo`, o mais comum do catálogo, é o menos estável dos dois.

---

# Não medido aqui, e recomendado como próximo passo

**Este relatório mede frequência, cobertura e fidelidade. Ele não mede
utilidade — e não pode.** Frequência ≠ relevância ≠ utilidade é uma distinção
real, mas hoje não existe telemetria de leitura nem pesquisa coletada no
produto, e a micro-pesquisa A/B nunca colheu voto real. Qualquer número sobre
"o leitor achou útil" seria inventado, e por isso não há uma seção 11.

O que a leitura destes dez estudos sugere como próxima fase é **instrumentação
antes de mais medição de conteúdo**, em três peças, na ordem em que se pagam:

1. **Telemetria de interação por bullet.** Quais bullets abrem o disclosure
   "Aprofundar", em que ordem, quanto tempo cada grupo fica aberto. É o dado
   mais barato de coletar e o único que separa "o público falou muito disso"
   (o que o produto mede hoje) de "o leitor quis saber mais disso". A hipótese
   testável mais óbvia sai do estudo 5: se o vocabulário do grupo minoritário é
   estruturalmente diferente, o leitor lê o grupo minoritário mais ou menos que
   o dominante?
2. **Voto de utilidade por bullet, não por filme.** Um sinal binário por bullet
   ("isso me ajudou?"), agregado por **eixo**. É o que decidiria a pergunta que
   o estudo 1 levanta e não resolve: `roteiro_estrutura` ocupa 25% dos bullets
   porque é o assunto do público, ou porque é onde a síntese despeja o que não
   coube? Utilidade por eixo separa as duas.
3. **Polaridade por review dentro do eixo** — a lacuna do estudo 9. Não é
   pesquisa com usuário, é um campo a mais na classificação; mas é pré-requisito
   para qualquer leitura honesta de utilidade, porque enquanto "3 de 18 em
   `atuacao`" puder significar tanto elogio quanto crítica, nem o leitor nem a
   medição sabem o que está sendo julgado útil.

Nenhuma dessas três é uma decisão que este relatório possa tomar. As três
custam coleta e mudança de schema, e ficam registradas como recomendação de
produto, não como conclusão de medição.
