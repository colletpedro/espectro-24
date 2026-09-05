# Histórico — a camada de COLETA

Este arquivo responde *"por que a coleta é assim, e o que já foi tentado?"*.
Carregue-o quando for **reabrir** uma decisão de coleta, não para implementar
sob as regras vigentes — essas estão em `SPEC.md`.

Cobre: fronteiras de bucket e seus riscos, ordenação e viés de recência,
orçamento de páginas, posicionamento em profundidade, as quatro recoletas
medidas, o gate de profundidade, o teto de 256 páginas, o harness de lote e a
auditoria de `MIN_CHARS`.

---

<!-- SPEC.md linhas 36–45 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **v1.9.0 — a cota igual passou a ser literal.** Até a v1.8.2 o princípio era
> declarado mas não cumprido: 50/20/30 não era uma decisão de profundidade, era
> um **acidente aritmético** (10 reviews × o número de níveis de estrela de cada
> faixa: 5/2/3). O grupo mediano recebia 40% da profundidade do negativo por
> ter dois níveis em vez de cinco — e a diferença não tinha nenhuma
> justificativa de design. A cota 40/40/40 é a mesma frase de sempre, agora
> escrita como número: **profundidade igual por perspectiva, peso informado à
> parte**. O piso escalonado (§3[C3]) é o que trata o caso em que um grupo
> simplesmente não tem 40 reviews com texto — sem fingir que tem.


<!-- SPEC.md linhas 763–812 · origem: Consequência medida — os shares publicados MUDAM -->

### Consequência medida — os shares publicados MUDAM

**APLICADO EM PRODUÇÃO na v1.9.14 (2026-08-16).** A tabela abaixo deixou de
ser projeção: os três `resultado/*.json` foram sobrescritos pelos artefatos
da v1.9.13 e o frontend passou a exibir a coluna "Novas C". Quem tinha lido
"17% ficaram no meio" em `cure` lê agora "8%" — **o dado não mudou, a régua
mudou**, e é este parágrafo que registra o momento em que a troca ficou
visível ao leitor. Ver o changelog da v1.9.14 para as outras três mudanças
visíveis publicadas no mesmo evento.

Recalculados sobre o **mesmo** histograma já coletado (zero requisições):

| Filme | Antigas (neg/med/pos) | **Novas C** | Movimento |
|---|---|---|---|
| `cure` | 3 / 17 / 79 | **2 / 8 / 90** | positivas +11pp, medianas −9pp |
| `the-invite-2026` | 3 / 18 / 79 | **2 / 7 / 91** | positivas +12pp, medianas −11pp |
| `cidade-de-deus` | 1 / 8 / 91 | **1 / 3 / 96** | positivas +5pp, medianas −5pp |

O padrão é o esperado: **positivas crescem com a entrada do 3,5★** (um nível
populoso — 11-12% de todas as notas nos três filmes) e **negativas encolhem
com a saída do 2,5★** (um nível pequeno, daí o movimento de só 1-2pp desse
lado). O grosso do deslocamento vem do bucket do meio, que perde o nível
grande e ganha o pequeno.

### RISCO ACEITO da opção C, e as mitigações

**Risco 1 — saturação do rótulo de peso no extremo forte.** Com positivas
rotineiramente em 90-96%, a faixa mais alta do mapa de `rotulo_peso` (§D2,
`≥ 70% → "a grande maioria"`) satura: filmes de 71% e de 96% recebem o **mesmo
rótulo**. É exatamente o defeito que a v1.6.0 corrigiu no extremo **fraco**
(8% e 1% recebiam ambos "uma pequena minoria"), reaparecendo simétrico no
extremo oposto — e a opção C o torna a regra, não a exceção.
*Mitigação:* registrado como **candidato explícito** (faixa nova acima de ~90%,
ex. `≥ 90% → "praticamente todas as notas"`), **NÃO aplicado nesta versão** —
o mapa de rótulos é do narrador, fora do escopo desta sessão. O percentual
continua sendo entregue junto do rótulo, então o número não mente enquanto o
rótulo estiver achatado; e a telemetria desta versão publica os shares sob as
duas fronteiras lado a lado, para que a decisão de recalibrar seja tomada com
dado, não com estimativa.

**Risco 2 — mudança silenciosa da marcação de perspectiva.** `marcacao_perspectiva`
(§D2) é pré-computada a partir do `share_real` com limiares `dominante/3` e
`dominante/10`. Subir o dominante de 91 para 96 (`cidade-de-deus`) empurra
mais grupos para o degrau mais restritivo (`antecipada`). Nenhuma linha de
código muda; o comportamento do narrador muda porque o **dado** de entrada
mudou.
*Mitigação:* declarado aqui como consequência prevista, e não como bug quando
aparecer na próxima regeneração de narrativa. Os limiares já estão registrados
como "ponto de partida, calibráveis" desde a v1.5.0.


<!-- SPEC.md linhas 872–905 · origem: O tamanho MEDIDO do viés de recência (recoleta de 2026-08-07) -->

#### O tamanho MEDIDO do viés de recência (recoleta de 2026-08-07)

A ressalva acima era qualitativa. Medida sobre o bruto persistido, ela é
maior do que a palavra "recência" sugere:

| Filme | janela dos 2 meses mais densos | concentração |
|---|---|---|
| `the-invite-2026` | 2026-07 + 2026-08 | **100%** das 396 |
| `cure` (1997) | 2026-07 + 2026-08 | **95%** das 384 |
| `cidade-de-deus` (2002) | 2026-07 + 2026-08 | **79%** das 384 |

Para um filme de catálogo com centenas de milhares de notas, **a amostra
inteira vem de ~6 semanas de atividade recente**. Isso não é um detalhe de
ordenação: a análise temática passa a descrever *quem está descobrindo o filme
agora*, não a recepção acumulada. Sob `by/activity` a mesma sondagem devolvia
reviews espalhadas por 2020-2025 (§2.3, tabela do menu).

**Isso não reverte a decisão** — engajamento continua sendo o pior dos dois
vieses, porque correlaciona com o *conteúdo* da review (longa, performática,
promovida), enquanto recência correlaciona só com *quando*. Mas o tamanho do
efeito precisa estar escrito, e agora está. Candidato de próxima versão:
amostragem estratificada por período (N páginas de `by/added` + N de
`by/added-earliest`), que o superset persistido já suporta sem mudança de
arquitetura — coletas com ordenações diferentes **acumulam** no mesmo `jsonl`
(§3[B']).

**Correção sobre o campo `data` (§3[B']):** ele vem do `<time class="timestamp">`
da listagem, que é a data **ASSISTIDA** (entrada de diário), não a data em que
a review foi publicada. Consequência observada: ~16% dos pares consecutivos do
`cure` aparecem "fora de ordem" decrescente, e a amostra tem extremos de 2023
— são reviews **recentes** sobre sessões **antigas**, não falha de ordenação.
O campo continua sendo a melhor evidência disponível sobre a janela da amostra,
mas é evidência **indireta**; a spec não deve tratá-lo como carimbo de ordem.


<!-- SPEC.md linhas 961–969 · origem: 2.4 Retentativa de rede — TRANSPORTE sim, BLOQUEIO nunca (v1.9.6) -->

## 2.4 Retentativa de rede — TRANSPORTE sim, BLOQUEIO nunca (v1.9.6)

Até a v1.9.5, `Fetcher.get` fazia **uma** tentativa por requisição: qualquer
`ConnectionResetError`/`ReadTimeout` propagava e abortava o filme inteiro. Com
~48 requisições de rede por filme, a probabilidade de um reset transitório em
algum ponto é alta — medido na recoleta da v1.9.5: **10 falhas em 28 filmes
processados (36%)**, todas transitórias, nenhuma com 403 e nenhuma com
`AntiBotError`. Não era bloqueio: era rede.


<!-- SPEC.md linhas 2315–2320 · origem: [C1] Alocação proporcional ao histograma (v1.9.0) — define o alvo, não o filtro -->

**Por que substituiu a cota igual por nível.** A cota de 10 por nível fazia
cada nível de estrela pesar o mesmo dentro do bucket, o que **super-representa
os extremos**: num filme com 456 notas de 0,5★ e 4.251 de 2,0★, ambos entravam
com 10 reviews — 0,5★ com 22× mais peso relativo do que tem na população. O
grupo "negativas" saía lido como mais raivoso do que é.


<!-- SPEC.md linhas 2362–2409 · origem: [B] Raspagem do SUPERSET por nível de nota -->

> **v1.9.2 — a parada por ALVO (heurística, cota × folga) foi REMOVIDA.** Até
> a v1.9.1 havia um terceiro motivo, PISO/ALVO: parar cedo quando a contagem
> heurística de válidas (nota + sem spoiler + comprimento) alcançava a cota
> alocada com 25% de folga, mesmo com orçamento de páginas sobrando. Esse
> mecanismo fazia sentido quando o teto era por NÍVEL e o custo total por
> BUCKET não tinha limite (v1.9.0): parar cedo economizava requisição sem
> arriscar o bucket inteiro. Sob o orçamento por BUCKET da v1.9.1, ele virou
> **fonte de não-determinismo**: a heurística é otimista (mede texto visível,
> antes da cascata precisa e da re-checagem de spoiler — §3[B], "Orçamento de
> páginas"), então pode julgar "material suficiente" e parar de paginar
> exatamente no ponto em que, na prática, o rendimento real cairia abaixo da
> cota — foi o mecanismo EXATO por trás do 37/40 residual de `cidade-de-deus`
> na v1.9.1 (nível 2,5★ parou na página 3 por ALVO, com 3 páginas de
> orçamento ainda disponíveis; a página 4 nunca foi buscada). Removê-la
> significa que o orçamento de páginas passa a ser a ÚNICA variável que
> controla quanto se coleta — o resultado de uma coleta com o mesmo orçamento
> é sempre o mesmo, o que é pré-requisito para planejar o custo de um lote de
> 30-50 filmes com confiança.
>
> **Custo aceito e medido:** mais páginas por filme (o orçamento que antes
> podia parar cedo agora é sempre gasto) — ver "Resultado MEDIDO da recoleta
> v1.9.2" abaixo para os números reais. `FOLGA_ALVO_COLETA` (1,25) e a
> heurística de contagem continuam existindo, mas com escopo REDUZIDO: só
> decidem o orçamento do completamento [C'] (quantas truncadas resolver),
> nunca mais quando parar de paginar.
>
> **O piso de páginas por nível (v1.9.0, §2.2 Risco 3) não desaparece — muda
> de mecanismo.** Ele existia para garantir que todo nível com material fosse
> raspado ao menos 1 vez, mesmo com alocação de reviews zero (o seguro de
> reversibilidade da fronteira). Essa garantia já vinha, desde a v1.9.1, do
> PISO DA ALOCAÇÃO DE PÁGINAS (`orcamento_paginas_bucket`, piso=1 por nível
> com material) — não do parâmetro `piso_paginas` que gatilhava o ALVO. Com o
> ALVO removido, esse parâmetro fica sem função e é revogado (§2); a garantia
> de reversibilidade continua de pé, só que por um único caminho em vez de
> dois.

#### Orçamento de páginas POR BUCKET (v1.9.1) — corrige o defeito estrutural da v1.9.0

**O defeito, como a v1.9.0 o deixou registrado:** o teto de páginas era **por
NÍVEL** (4, flat) enquanto a cota de análise é **por BUCKET** (40). Sob a
opção C, `medianas` tem **2 níveis** contra **4** dos outros dois buckets — seu
teto AGREGADO de páginas era `2 × 4 = 8`, metade do teto agregado de
`negativas`/`positivas` (`4 × 4 = 16`). Era uma mistura de unidades, não falta
de material: o bucket nunca tinha orçamento de página suficiente para tentar
chegar a 40, não importa quanto material existisse no Letterboxd. Medido nos
3 filmes da recoleta v1.9.0: `medianas` fechou 35, 23 e 26 — nunca 40;
`negativas`/`positivas` fecharam 40 sempre.


<!-- SPEC.md linhas 2442–2461 · origem: Orçamento de páginas POR BUCKET (v1.9.1) — corrige o defeito estrutural da v1.9.0 -->

**Por que 16, e por que a razão importa mais que o número:** `16 = 4 × 4`, o
mesmo teto agregado que `negativas`/`positivas` já tinham sob a v1.9.0 (4
páginas × 4 níveis). O orçamento não SOBE para os buckets de 4 níveis — ele
**equaliza** o teto agregado que `medianas` (2 níveis) tinha pela metade. É a
correção mínima que fecha a lacuna sem tocar em fronteira, cota ou piso
escalonado, as três decisões que a v1.9.0 já havia congelado e que o registro
do defeito explicitamente preservou para decisão humana separada.

#### Posicionamento estratificado por profundidade (v1.9.2)

**O defeito que corrige:** as páginas de um nível eram sempre as primeiras `N`
consecutivas. Sob `by/added` (cronológica, mais recentes primeiro, §2.3), isso
amostra sistematicamente as reviews MAIS RECENTES — a v1.9.0 mediu 79-100% da
amostra numa janela de ~7 semanas. Para um filme de catálogo como `cure`
(1997), a análise passa a caracterizar a coorte que descobriu o filme
recentemente, não a recepção do filme ao longo da vida dele.

**A correção não muda QUANTAS páginas são buscadas — muda QUAIS.** O
orçamento de páginas por nível é dividido em dois blocos:


<!-- SPEC.md linhas 2538–2577 · origem: Âncora de profundidade — a progressão estava presa ao lugar errado (v1.9.5) -->

#### Âncora de profundidade — a progressão estava presa ao lugar errado (v1.9.5)

**O defeito, medido.** O bloco profundo da v1.9.2 compra uma mediana de **3
dias** sobre o raso. Em **26 de 34** filmes com material nos dois blocos, o
gap é de 7 dias ou menos; a média é 10 dias, o máximo 97.

A causa é a ÂNCORA da progressão geométrica. Ela parte do **fim do bloco
raso** — `n_raso+2, n_raso+4, n_raso+8, n_raso+16` — e com `n_raso ≈ 12` isso
põe as posições "profundas" em **14, 16, 20 e 28**, de níveis que vão até
~256. O bloco cobre ~10% da profundidade real. **Ele é profundo em POSIÇÃO DE
PÁGINA e raso em TEMPO:** para um filme que recebe centenas de reviews por
semana, a página 28 ainda é deste mês.

As duas exceções medidas (`cats-2019`, 97 dias; `im-still-here-2024`, 80)
confirmam o mecanismo em vez de contrariá-lo: são filmes de fluxo baixo, onde
28 páginas atravessam meses porque cada página cobre mais tempo.

**É o quarto caso do mesmo padrão neste projeto** — um parâmetro que ninguém
classificou como parâmetro. O `50/20/30` era o número de degraus de estrela
vezes 10; o teto por NÍVEL contra a cota por BUCKET era mistura de unidades; a
ordem de consumo da seleção virou critério de coorte sem que ninguém a
escolhesse; e agora a âncora da progressão. Nos quatro, o valor não estava
errado: ele nunca tinha sido decidido.

**Por que a alternativa não serve.** A saída barata seria não recoletar e
declarar a recência como escolha ("a análise cobre as reviews mais recentes").
Ela não alinha os dois canais, e a razão é uma propriedade do dado: **o
histograma não é recortável no tempo.** O endpoint do Letterboxd devolve o
acumulado da vida do filme e não existe versão temporal dele. Declarar a
recência congelaria permanentemente um parágrafo em que o rótulo de peso fala
de 2012-2026 e a frequência de tema fala de 6 semanas — não corrigido, só
confessado. Como a única metade ajustável é a da amostra, é ela que tem de se
mover.

**Por que agora, e por que esta é a última sessão da camada de coleta.**
Posicionamento é o último parâmetro que o superset (§3[B']) não torna
reversível — página não baixada não está em disco. A 35 filmes a recoleta
custa ~1,5 h; a 150 filmes, ~6 h. Depois desta versão, toda decisão restante
do projeto é de ANÁLISE, aplicável sobre o bruto sem uma requisição.


<!-- SPEC.md linhas 2647–2673 · origem: Extensão de orçamento por DÉFICIT (v1.9.4) -->

#### Extensão de orçamento por DÉFICIT (v1.9.4)

**O defeito que corrige.** A diagnose da v1.9.3 (registrada em §3[H]) achou
uma classe, não um caso: **10 buckets DOMINANTES abaixo da cota**, dos quais
9 são filmes muito populares (1,4M-5,7M notas) com rendimento pós-filtro de
10-20%. Em **4 deles** (`wicked-2024`, `avengers-endgame`, `talk-to-me-2022`,
`aftersun`) o bucket dominante — o que abre o MOVIMENTO 3 e carrega o rótulo
de peso mais forte — tem `n` **MENOR** que os outros dois buckets do mesmo
filme: a perspectiva majoritária medida com menos precisão que a minoritária.

O mecanismo é uma **interação entre duas decisões válidas isoladamente**: a
alocação proporcional ao histograma (§3[C1]) concentra o orçamento de páginas
nos níveis mais populosos, e `MIN_CHARS` filtra pior justamente esses níveis,
porque reação de massa é curta. A redistribuição de déficit (§3[C1]) não
socorre: ela pressupõe SOBRA em algum nível do bucket, e aqui o bucket inteiro
rende mal ao mesmo tempo (`deficit_redistribuido = 0` no caso medido).

**Por que corrigir agora, e não depois.** O orçamento de páginas é o **único**
parâmetro da camada de coleta que o superset (§3[B']) não torna reversível —
página não baixada não está em disco, e nenhum parâmetro downstream a traz de
volta. Com 35 filmes, corrigir custa ~20 minutos de recoleta incremental;
com mais 100 filmes coletados sob o orçamento antigo, custa horas. E o gate de
taxonomia mediu, por nulo de permutação, que a margem de lift de 15 pp só é
defensável na cota de 40 (a 20 reviews por bucket, ~2/3 dos pares que cruzam a
margem cruzariam por acaso) — déficit no bucket dominante degrada exatamente
a comparação ENTRE buckets, que é a tese do produto.


<!-- SPEC.md linhas 2784–3198 · origem: Correção e declaração são CAMADAS, não alternativas (v1.9.4) -->

#### Correção e declaração são CAMADAS, não alternativas (v1.9.4)

O teto de 24 garante que **alguns buckets ainda não fecharão 40**. Isso é
esperado e **não é falha da extensão** — é a consequência de haver um teto de
custo, que é o que impede a extensão de virar paginação sem limite.

O registro explícito, para que nenhuma versão futura leia uma coisa como
substituta da outra:

- a **extensão** (§3[B], acima) encolhe a CLASSE de buckets sub-40 — ataca os
  casos em que o material existe e o orçamento é que acabou cedo;
- o **piso escalonado** (§3[C3]) e o **denominador visível** na interface
  absorvem o RESÍDUO — os casos em que o material simplesmente não está lá,
  ou está atrás de mais páginas do que o teto autoriza.

A declaração honesta continua sendo o mecanismo **final**, não a alternativa
rejeitada. Nenhuma quantidade de orçamento de páginas torna o piso escalonado
dispensável: sempre existirá filme obscuro (`obsession-2026`, 214 notas no
total) para o qual nenhum orçamento acha material que não existe. A extensão
muda **quantos** buckets caem no resíduo, nunca **se** o resíduo precisa ser
declarado.

#### Resultado MEDIDO da recoleta v1.9.4 (2026-08-08) — extensão por déficit

Recoleta SELETIVA dos 9 filmes da classe identificada pela diagnose
(`obsession-2026` fora: escassez genuína, mecanismo diferente). Incremental —
as páginas da base já estavam no cache do lote da v1.9.3, então o custo de
rede medido é o das páginas de EXTENSÃO e do completamento que elas geram.

| Filme | dom. | antes (n/m/p) | depois | extras (n/m/p) | motivo (n/m/p) | rede |
|---|---|---|---|---|---|---|
| `wicked-2024` | pos | 30/32/**20** | 36/40/**24** | 8/8/8 | teto/teto/teto | 26 |
| `avengers-endgame` | pos | 40/40/**34** | **40/40/40** | 3/3/8 | meta/meta/teto | 20 |
| `talk-to-me-2022` | pos | 28/24/**23** | 40/31/**34** | 8/8/8 | teto/teto/teto | 30 |
| `aftersun` | pos | 40/40/**38** | **40/40/40** | 0/0/8 | meta/meta/teto | 9 |
| `pearl-2022` | pos | 15/24/**30** | 26/33/**35** | 8/8/8 | teto/teto/teto | 27 |
| `parasite-2019` | pos | 28/40/**32** | **40/40/40** | 8/7/8 | teto/meta/teto | 32 |
| `wonka` | pos | 18/23/**32** | 32/25/**38** | 8/8/8 | teto/teto/teto | 25 |
| `hereditary` | pos | 28/31/**34** | 36/40/**39** | 8/8/8 | teto/teto/teto | 24 |
| `shutter-island` | pos | 30/36/**36** | **40/40/40** | 8/7/8 | teto/meta/teto | 29 |

**Agregado:** bucket dominante fechando a cota **0/9 → 4/9**; buckets abaixo
de 40 **22/27 → 12/27**; dominante MENOR que outro bucket do mesmo filme
**5 → 3**. Os 27 buckets em `estado_piso = completa` antes e depois.

**Custo:** 222 requisições nos 9 filmes (**24,7/filme**, contra ~78/filme de
uma coleta do zero), 603 servidas de cache, 551 s (~9 min).

**Rendimento das extras: 188 páginas concedidas → 225 válidas ganhas**, ~10%
do bruto (a ~12 reviews/página) — exatamente a faixa de 10-20% que a diagnose
mediu para esta classe. A extensão não descobriu material melhor; comprou
mais material do mesmo, que é tudo o que um desenho observacional promete.

**Motivos de parada: 21 `teto_extensao`, 6 `meta_atingida`, 0
`material_esgotado`.** Coerente com serem os filmes mais populares do
catálogo: nenhum chega perto de esgotar o Letterboxd.

**A seletividade é o que distingue isto de um aumento de orçamento.**
`aftersun` é o caso limpo: `negativas` e `medianas` fecharam a meta dentro da
base e receberam ZERO extras (9 requisições no filme inteiro); só `positivas`
estendeu. Um aumento de `ORCAMENTO_PAGINAS_POR_BUCKET` teria gasto 24 páginas
nos três.

**O que NÃO fechou, e por quê — resíduo esperado, não falha:**
- `wicked-2024`/positivas (20→24): 8 extras renderam +4 válidas (~4%), pior
  que os 6,9% da diagnose. Fechar 40 exigiria da ordem de 40-50 páginas no
  bucket. É o pior rendimento dos 35 filmes.
- `hereditary` **passou** a ter o dominante menor que outro bucket (39 contra
  40 em `medianas`) — efeito colateral da extensão ter ajudado mais
  `medianas`; diferença de 1 review, irrelevante para precisão (±7,9pp vs.
  ±8,0pp a 1 EP), mas registrada por honestidade.
- `talk-to-me-2022`/medianas (24→31): o bucket morno tem 2 níveis sob a opção
  C, então as extras se espalham por menos níveis e batem antes no material
  de baixo rendimento.

**Consequência de custo, medida:** a regra é POR BUCKET, então um filme
deficitário estende os três — até 24 páginas extras por filme, não 8. Nos 9
filmes: 188 extras, média 20,9/filme.

#### Resultado MEDIDO da primeira recoleta, v1.9.0 (2026-08-07) — o defeito ANTES da correção

Recoleta ao vivo dos 3 filmes do catálogo, sob `by/added`, teto 4, cota 40:

| Filme | requisições | páginas | bruto | níveis no teto | negativas | medianas | positivas |
|---|---|---|---|---|---|---|---|
| `cure` | **65** | 32 | 384 | 3 | 39/40 | **35/40** | 40/40 |
| `cidade-de-deus` | **61** | 32 | 384 | 4 | 40/40 | **23/40** | 40/40 |
| `the-invite-2026` | **58** | 33 | 396 | 4 | 40/40 | **26/40** | 40/40 |

**DEFEITO ESTRUTURAL — `medianas` não consegue fechar a cota, e a causa é
aritmética, não de material.** O bucket do meio tem **2 níveis** sob a opção
C; os outros dois têm 4. Com teto de 4 páginas e ~12 reviews por página, o
material bruto máximo de um bucket é `nº de níveis × 4 × 12`:

| Bucket | níveis | bruto máximo | válidas a 27% (rendimento medido) |
|---|---|---|---|
| `negativas` / `positivas` | 4 | 192 | ~52 |
| **`medianas`** | **2** | **96** | **~26** |

Ou seja: **`medianas` topa em ~26 válidas e a cota de 40 é inalcançável por
construção** — não por falta de reviews no Letterboxd, mas porque o teto de
páginas é POR NÍVEL e o bucket do meio tem metade dos níveis. Foi o que
aconteceu nos 3 filmes (35, 23 e 26), e vai acontecer em todo filme.

Isto é uma **interação não prevista** entre três decisões desta versão que
foram tomadas separadamente: a fronteira 4/2/4 (§2.2), a cota igual 40/40/40
(§0) e o teto de 4 páginas por nível (§3[B]). Cada uma é defensável sozinha;
juntas, tornam um terço da promessa "profundidade igual" impossível de
cumprir.

> ### RESOLVIDO NA v1.9.1 PELA SAÍDA 1 — leia isto antes da lista abaixo
>
> **O defeito descrito acima não existe mais, e a escolha entre as cinco
> saídas já foi feita: venceu a saída 1, o ORÇAMENTO DE PÁGINAS POR BUCKET.**
> Ele tem seção própria (§3[B], "Orçamento de páginas POR BUCKET (v1.9.1)"),
> está em `config.py` como `ORCAMENTO_PAGINAS_POR_BUCKET = 16`, e o resultado
> medido está logo abaixo, em "Resultado MEDIDO da recoleta v1.9.1": `medianas`
> foi de 35→**40**, 26→**40** e 23→**37** nos três filmes, e o resíduo de
> `cidade-de-deus` fechou em 40/40 na v1.9.2 com a remoção da parada por ALVO.
>
> **Nenhuma das outras quatro foi adotada**, e vale saber o destino de cada
> uma: a **2** (teto de volta a 6) e a **4** (fronteira com 3 níveis no meio)
> nunca foram retomadas; a **5** (baixar `min_chars`) foi **auditada com dado
> em 2026-08-08 e REJEITADA por decisão do usuário** — §3[C2], "Auditoria de
> `MIN_CHARS=150`", com `MIN_CHARS` e `CASCATA_CHARS` mantidos em 150 e
> [150, 50, 0].
>
> **A saída 3 NÃO é mais o comportamento em vigor**, e essa é a frase que esta
> nota existe para desmentir. *(Correção de registro, 2026-09-04: o parágrafo
> que fechava esta lista dizia "A opção 3 é o comportamento em vigor, por
> omissão" — verdadeiro quando foi escrito, na v1.9.0, e falso desde a
> v1.9.1. Quem lesse a lista de cima a baixo saía com a impressão de que o
> projeto tinha decidido conviver com o defeito.)*
>
> **A lista abaixo fica como o registro das alternativas consideradas** — é
> ela que documenta por que a saída 1 era a correção mínima, e é isso que
> uma sessão futura precisa se quiser reabrir o assunto.

**[Registro da v1.9.0, quando a decisão ainda estava aberta.] Não corrigido nesta versão** — corrigir exigiria mexer numa das três
decisões que a v1.9.0 acabou de congelar, e a escolha entre elas merece uma
decisão explícita e não uma correção de rodapé. Registrado como o **candidato
número 1 da próxima versão**, com quatro saídas conhecidas:
1. **orçamento de páginas por BUCKET** em vez de por nível (`4 × nº de níveis`,
   redistribuível internamente) — corrige a assimetria na raiz e não muda
   fronteira nem cota; custo: até +8 páginas/filme só no bucket do meio;
2. **teto de volta a 6** globalmente — custo: até +20 páginas/filme, e ainda
   assim `medianas` chegaria a ~39, no limite;
3. **aceitar** e deixar o piso escalonado reportar — hoje `medianas` fecha em
   23-35, que é `completa` (≥15) nos 3 filmes; a precisão em `n=26` é ±9,8pp
   (1 EP) / ±19,2pp (95%), pior que a de 40 mas dentro da mesma ordem;
4. **fronteira com 3 níveis no meio** — reabre §2.2, que acabou de ser
   decidida com base semântica.

5. **baixar `min_chars`** — medido: com `min_chars=50`, os **três** buckets
   fecham 40/40/40 nos **três** filmes, a partir do MESMO bruto e sem nenhuma
   requisição. Ou seja, o material existe; o que não passa é o filtro de
   comprimento. Trocaria profundidade de texto por contagem, o que é uma
   decisão de qualidade de análise e não de coleta — por isso não é a saída
   default, mas é a mais barata de todas.

*(A opção 3 foi o comportamento da v1.9.0, por omissão: nada quebrava, os três
buckets ficavam `completa`, e a telemetria mostrava a diferença em vez de
escondê-la. **Deixou de ser o comportamento em vigor na v1.9.1** — ver o bloco
"RESOLVIDO NA v1.9.1 PELA SAÍDA 1", acima.)*

**Confirmação do diagnóstico (reseleção offline, 0 requisições):** rodando a
seleção sobre o mesmo bruto **sob as fronteiras HISTÓRICAS** (3 níveis em
`positivas`, 2 em `medianas`, 5 em `negativas`), quem passa a ficar curto é
**`positivas`** — 36/40 em `cidade-de-deus` e em `the-invite-2026` —, enquanto
`negativas` (5 níveis) fecha 40 em todos. O déficit acompanha o **número de
níveis do bucket**, exatamente como a aritmética prevê, e não a faixa de nota.
É a prova de que o defeito é do teto-por-nível, não da opção C.

**Orçamento de requisições, MEDIDO:** 58-65 por filme (média 61), dos quais
32-33 de paginação, 24-33 de completamento e 1 de histograma. Para comparação,
sob a v1.8.2 o `cure` custou **83** e o `cidade-de-deus` **68** — a v1.9.0
custa **menos** apesar de coletar ~50% mais material bruto (384 vs. 252 no
`cure`), porque o orçamento de completamento cortou a parte cara. A estimativa
de "~45" feita antes desta medição estava otimista, como se previa.

#### Resultado MEDIDO da recoleta v1.9.1 (2026-08-07) — depois da correção

Recoleta ao vivo (incremental sobre o bruto da v1.9.0), sob o orçamento por
bucket (16 páginas, teto de segurança 10/nível):

| Filme | requisições de rede | negativas | medianas | positivas |
|---|---|---|---|---|
| `cure` | **17** | 40/40 | **40/40** | 40/40 |
| `cidade-de-deus` | **26** | 40/40 | **37/40** | 40/40 |
| `the-invite-2026` | **20** | 40/40 | **40/40** | 40/40 |

**O defeito fecha em 2 dos 3 filmes, melhora substancialmente no terceiro.**
`medianas` foi de 35→**40**, 26→**40**, 23→**37** — de 3/3 buckets abaixo da
cota para 8/9 buckets no total, e 2/3 filmes com os TRÊS buckets em 40/40/40.

**`cidade-de-deus`/`medianas` ficou 3 abaixo — causa identificada, e NÃO é o
mesmo defeito.** O nível 2,5★ recebeu orçamento de 6 páginas mas usou só 3
(confirmado: página 4 nunca foi buscada, `resultado/cache/cidade-de-deus/
pages/by_added/rated_2_5_page_4.html` não existe) — a condição de parada
**ALVO** (§3[B], degrau b: cota alocada × 1,25 de folga, contada por
heurística) foi satisfeita antes de esgotar o orçamento de páginas. O alvo
de reviews para 2,5★ nesse bucket é 6 (com folga, 8); a heurística julgou
ter material suficiente na página 3, mas parte não sobreviveu ao filtro real
(cascata precisa, exclusão de spoiler) — e o nível 3,0★ (que bateu o teto de
10 páginas) não teve material extra para cobrir a diferença via
redistribuição. **Este é o mecanismo de folga da v1.9.0, inalterado nesta
sessão** (fora de escopo — a lista de "não tocar" desta sessão inclui `cota`
mas a folga é parte do coletor, não da cota em si; ajustá-la não foi pedido).
Registrado como achado residual, candidato a próxima sessão se o padrão se
repetir em mais filmes.

**Requisições: 17-26 por filme (execução incremental), média 21** — bem
abaixo da média de 61 da v1.9.0, porque a maior parte do material já estava
persistida da recoleta anterior; só o incremento (páginas novas dentro do
orçamento maior) gerou requisições reais. **Não é comparável 1:1 com os 61
da v1.9.0** (que foi coleta do zero) — é o custo real medido de ALARGAR uma
coleta já existente, que é o caso de uso que a incrementalidade do bruto
(§3[B']) foi desenhada para servir.

**Motivos de descarte, agregados nos 3 filmes:** `abaixo_min_chars` domina
com folga (~65-70% dos descartes em todo bucket) — confirma que `min_chars`
é o filtro que mais custa rendimento, como já indicado pela saída "baixar
min_chars" de §3[B] (não aplicada, apenas registrada). `excedente_cota`
(material que passaria em tudo mas não coube) aparece em quase todo
bucket — sinal de que o bruto tem folga além do que a cota consome.
`spoiler` e `truncada_sem_texto` são marginais (poucas unidades por
bucket). `duplicata`/`outros`: **zero em todos os filmes/buckets/níveis** —
a garantia de dedupe do bruto se sustenta sob dado real.

**Janela temporal, medida (entrega 4) — confirma o achado do gate.** Os
percentis mudam MUITO mais do que os extremos brutos sugerem: `cure`
positivas tem `min=2023-12-06` mas `p5=2026-08-04` — 95% da amostra desse
bucket está dentro de 3 dias, apesar do extremo de quase 3 anos atrás. É a
prova, em dado real e não sintético, do achado do gate (§3[B]): min/max é
dominado por outlier, a mediana e os percentis são a leitura honesta de onde
a amostra realmente está.

#### Resultado MEDIDO da recoleta v1.9.2 (2026-08-07) — parada determinística + posicionamento estratificado

Recoleta incremental (sobre o bruto da v1.9.1), sob a parada determinística
(entrega 1) e o posicionamento estratificado (entrega 2):

| Filme | requisições de rede | negativas | medianas | positivas |
|---|---|---|---|---|
| `cure` | **15** | 40/40 | 40/40 | 40/40 |
| `cidade-de-deus` | **15** | 40/40 | **40/40** | 40/40 |
| `the-invite-2026` | **13** | 40/40 | 40/40 | 40/40 |

**O DÉFICIT RESIDUAL DA v1.9.1 FECHOU.** `cidade-de-deus`/`medianas`, que
tinha ficado em 37/40 (o nível 2,5★ parando cedo por ALVO antes de esgotar
o orçamento), agora fecha **40/40** — exatamente a correção prevista ao
remover a parada heurística. **Os 3 filmes, os 9 buckets, todos em 40/40 —
a primeira vez desde a v1.9.0 que isso acontece nos três simultaneamente.**

**`motivo_parada` por nível: 100% `orcamento_esgotado`, nos 3 filmes, em
todos os 10 níveis de cada um** (30 valores no total, nenhum
`material_esgotado`) — os 3 filmes do catálogo têm material de sobra em
todo nível, então o orçamento (16/bucket) foi o fator limitante em toda
parte, nunca o conteúdo real do Letterboxd. Consistente com o achado da
Entrega 3 (filmes populares raramente esgotam organicamente).

**Requisições: 13-15 por filme, média 14,3** — abaixo da execução incremental
da v1.9.1 (~21), porque grande parte do bloco raso já estava cacheada;
o custo novo concentrou-se nas posições PROFUNDAS (nunca visitadas antes).
Não comparável ao valor esperado de coleta do zero (~85, §5.6) pelo mesmo
motivo já registrado nas sessões anteriores: incremental reaproveita cache.

**Distribuição de `pagina_origem` (entrega 4) — a primeira medição real do
posicionamento estratificado.** `fracao_profunda` variou de **0,00 a 0,23**
entre buckets — no `the-invite-2026`/negativas, **23% da amostra final veio
do bloco profundo**, contribuição real e mensurável à diversidade temporal
da amostra. Em buckets com material abundante (`cure`/positivas), a fração
profunda ficou em 0 — o bloco raso já basta para fechar a cota, e a seleção
(ainda ordenada por `pagina_origem` ascendente, §3[B], "Reversibilidade")
não precisa alcançar o material profundo. **Confirma a hipótese registrada
durante a implementação (Entrega 4, commit [2/6]):** o benefício do
posicionamento estratificado na amostra FINAL depende de quão escasso é o
material raso — não é automático, é condicional à disponibilidade.

**Janela por `data` (secundária)** segue reportada lado a lado — sem
mudança de leitura em relação à v1.9.1 (ainda concentrada nos últimos
meses/dias em todos os buckets), confirmando que `pagina_origem` e `data`
medem coisas relacionadas mas distintas: a amostra ficou mais profunda em
RANK DE ADIÇÃO sem necessariamente recuar em CALENDÁRIO — o que é esperado
sob `by/added`, onde adições recentes concentram-se numa janela curta e
"profundo" ainda significa, na maioria dos casos, "há algumas semanas", não
"há anos".

#### Medição de profundidade de paginação (v1.9.1, GATE — passo largo NÃO implementado)

A v1.9.0 mediu que 79-100% da amostra de cada filme vem de uma janela de ~7
semanas (viés de recência, §2.3) — para um filme de catálogo como `cure`
(1997), a análise passa a descrever quem descobre o filme AGORA. A correção
candidata é **paginação de PASSO LARGO**: em vez das páginas `1..N`
consecutivas, amostrar `N` páginas espalhadas pela profundidade total
disponível — mesmo número de requisições, cobertura temporal inteira.

**Esta subseção é MEDIÇÃO, não implementação.** Nada do coletor de produção
mudou por causa dela. Metodologia e dado completo em
`scripts/medicao_profundidade_v191.py` (nível 4,0★, `by/added`, os 3 filmes);
respostas às quatro perguntas do gate:

**(a) A profundidade é conhecível a partir da página 1 (ou de outra forma
barata)? NÃO.** O HTML de listagem do Letterboxd usa um widget simples
"Newer/Older" — sem contagem total de páginas, sem numeração, sem link para a
última página, confirmado nos 3 filmes. Uma estimativa por PROXY foi testada
(total de reviews do filme, do nav — já presente em toda página, custo zero —
× participação do nível no histograma ÷ 12/página) e **superestimou a
profundidade real em 11,6×–27,2×** — a maioria das notas não vem acompanhada
de texto, e essa proporção não é uniforme por nível nem ao longo do tempo, o
que torna o proxy inútil para planejar índices de página. A única forma
CONFIÁVEL encontrada foi **sonda exponencial** (dobrar a página até achar uma
vazia): ~10 requisições de rede por nível para um limite confiável, medido nos
3 filmes.

**Achado lateral, não pedido mas relevante para a decisão:** a sonda parou
EXATAMENTE no mesmo intervalo (última não-vazia 256, primeira vazia 512) nos
3 filmes — coincidência grande demais para ser orgânica. Uma busca binária
sobre o `cure` fechou o limite exato: **página 256 tem conteúdo, página 257
não tem** (confirmado por contagem real de reviews parseadas, não por
tamanho de arquivo — ver `resultado/cache/*/pages/by_added/rated_4_page_256.html`
vs. `_257.html`). `256 = 2⁸` é suspeito o bastante para ser um **teto
fixo do site**, não exaustão orgânica de conteúdo — hipótese reforçada por
níveis pouco populosos (ex. `cure` 0,5★, 456 notas) esgotarem naturalmente na
1ª página, muito antes de qualquer teto. **Não confirmado para outros
níveis/filmes** — testado só em `cure`/4,0★; registrado como pista, não fato
estabelecido.

**(b) Páginas profundas rendem reviews normais? SIM.** Contagem de válidas
(≥150 chars) e comprimento médio em páginas a 50%/75%/95% da profundidade
sondada ficaram na MESMA ordem de grandeza das páginas rasas (1-4), nos 3
filmes — sem degradação sistemática de rendimento ou de comprimento à medida
que se pagina mais fundo.

**(c) Qual a janela temporal do passo largo, contra a atual de ~7 semanas?
MISTO — mais complexo do que a hipótese previa, e por um motivo já registrado
na v1.9.0.** Comparando a janela `min↔max` das páginas 1-4 (atual) contra uma
amostra de passo largo (páginas 1, ~33%, ~66%, 100% da profundidade sondada):

| Filme | atual (pág. 1-4) | passo largo | resultado |
|---|---|---|---|
| `cure` | 2026-08-05 → 2026-08-07 (2 dias) | 2026-04-01 → 2026-08-07 (~4 meses) | **confirma a hipótese** |
| `cidade-de-deus` | 2025-11-29 → 2026-08-07 (~8 meses) | 2026-05-19 → 2026-08-07 (~2,5 meses) | **janela mais ESTREITA** |
| `the-invite-2026` | 2026-07-08 → 2026-08-07 (~1 mês) | 2026-07-28 → 2026-08-06 (~9 dias) | **janela mais ESTREITA** |

Em 2 dos 3 filmes o passo largo **estreitou** a janela medida por
`min`/`max` — o oposto do esperado. **Causa provável, já registrada na
v1.9.0:** `data` é a data ASSISTIDA (diário), não a de publicação da review;
alguém pode postar HOJE uma review de um rewatch antigo, produzindo um
outlier de data velha em QUALQUER posição da sequência `by/added` — inclusive
nas páginas 1-4. `min`/`max` sobre uma janela pequena é dominado pelo
outlier mais extremo que ela contém, não pela distribuição real. **Esta
medição é evidência a favor da Entrega 4** (percentis p5/50/95 em vez de só
min/max): a métrica certa para avaliar cobertura temporal não é o extremo,
é a distribuição.

**(d) O custo em requisições muda? O briefing previu que não — a medição diz
que SIM, seria mais caro, a menos que o achado do item (a) se confirme.**
Esta MEDIÇÃO gastou ~11 requisições novas de rede por filme (a maior parte já
estava em cache da coleta anterior). Um coletor de PRODUÇÃO com passo largo
precisaria de alguma forma barata de saber a profundidade ANTES de escolher
os índices de página a amostrar — e a única forma confiável encontrada (sonda
exponencial, ~10 req./nível) seria um custo NOVO, pago em TODA coleta, que a
paginação sequencial atual não paga. Isso inverteria o ganho: passo largo
resolveria o viés de recência mas pioraria o orçamento de requisições que a
v1.9.0 acabou de medir e otimizar. **A única saída que preserva "custo não
muda" é o teto fixo do achado lateral (a) se confirmar** — um valor constante
(256) não precisa de sonda, dispensa completamente esse custo. Mas isso
depende de uma verificação mais ampla (mais níveis, mais filmes) que esta
sessão não fez.

**GATE — decisão tomada na v1.9.2, ver abaixo.** O passo largo (amostra
regular por toda a profundidade) continua NÃO implementado — a v1.9.2
implementa **posicionamento estratificado** (acima), que é uma resposta
diferente e mais barata ao mesmo problema: não precisa conhecer a
profundidade a priori (a reserva geométrica descobre e se adapta, custando
no máximo 1 página por nível), então o argumento "custo não muda só se o
teto de 256 se confirmar" deixou de ser bloqueante.

#### Confirmação do teto de 256 páginas (v1.9.2, Entrega 3) — RESULTADO MEDIDO

Medido em `the-room-1993` — **890 notas no total** (`collect_distribuicao`),
um filme genuinamente obscuro (não confundir com o "The Room" de 2003; é um
título homônimo de 1993 quase sem audiência). Nível mais populoso: **3,0★,
249 notas** — o testado, sob `by/added` (mesma ordenação da sondagem v1.9.1).

Sonda exponencial (`1, 2, 4, 8`) + busca binária de refinamento, **6
requisições no total**:

```
página 1: 12 reviews    página 2: 12 reviews    página 4: 2 reviews
página 8: 0 reviews (limite superior)
página 6: 0 reviews     página 5: 0 reviews
→ última página não-vazia = 4; primeira vazia = 5
```

**Resultado: a profundidade foi determinada pelo CONTEÚDO REAL do filme, não
por um teto do site.** A última página com conteúdo é a **4**, muitíssimo
abaixo de 256 — confirma a hipótese: um filme obscuro esgota organicamente
muito antes de qualquer teto de plataforma, enquanto os 3 filmes populares
da v1.9.1 bateram EXATAMENTE no mesmo ponto (256/512) apesar de terem
volumes de notas completamente diferentes entre si (120 mil a 1,2 milhão) —
um padrão que só faz sentido como limite do SITE, não como coincidência de
conteúdo. **O achado lateral da v1.9.1 fica CONFIRMADO** (ainda que só para
os 4 níveis testados até agora, não generalizado para toda a plataforma):
Letterboxd aparenta impor um teto de paginação por volta de 256 páginas para
listagens populosas, e filmes obscuros nunca chegam perto dele.

**Consequência para o posicionamento estratificado:** nenhuma, como previsto
— o algoritmo de descoberta (acima) não assume o valor 256 em nenhum ponto;
funciona igual, e com o mesmo custo, seja a profundidade real do nível 4
páginas (`the-room-1993`) ou 256 (os filmes populares da v1.9.1). Esta
medição completa o registro do achado da v1.9.1; não foi bloqueante para o
posicionamento estratificado, que já estava implementado sem depender dela.


<!-- SPEC.md linhas 3527–3643 · origem: [H] Harness de lote (v1.9.3) -->

**Diagnose do déficit de buckets nos 3 filmes da Entrega 2 (v1.9.3,
2026-08-07, offline sobre o bruto já em disco — zero requisições).** O
relatório da Entrega 2 afirmou "os 3 fecharam 40/40/40" — **errado**,
contradizendo a própria tabela: só 5 dos 9 buckets atingem a cota cheia
de 40 (`parasite-2019` 28/40/32, `eighth-grade` 38/39/40,
`everything-everywhere-all-at-once` 40/40/40); os 9 fecham
`estado_piso=completa` (limiar n≥15, §3[C3]) — as duas afirmações não são
a mesma coisa, e a confusão entre elas foi o erro. Corrigido em §5.6.

Classificação dos 4 déficits (`parasite-2019`/negativas=28,
`parasite-2019`/positivas=32, `eighth-grade`/negativas=38,
`eighth-grade`/medianas=39), via `selecao.selecionar` reexecutado sobre o
bruto persistido:

- **`motivo_parada_por_nivel` = `orcamento_esgotado` em TODOS os 30
  níveis dos 3 filmes** — nenhum esgotou material organicamente;
  `paginas_gastas_por_nivel` == `orcamento_paginas_por_nivel` em todos.
- **Zero sondagem caindo em página vazia dentro do orçamento** — para
  cada nível, o número de `pagina_origem` distintos com review bate
  exatamente com `paginas_gastas`; toda página orçada retornou conteúdo
  real. Não há DESPERDÍCIO em nenhum dos 4 déficits.
- **Descarte dominado por `abaixo_min_chars`**, 63-87% do bruto de cada
  nível deficitário (ex.: `parasite-2019`/negativas nível 2,0★: 101/120;
  `parasite-2019`/positivas nível 5,0★: 78/96) — o filtro `MIN_CHARS=150`
  descarta reviews curtas. `deficit_redistribuido` (§3[C1]) ativou
  corretamente em todos os 4 (puxou excedente de níveis com sobra para os
  com falta, dentro do mesmo bucket) mas não bastou porque o BUCKET
  inteiro carecia de material elegível, não só um nível.
- **Hipótese de spoiler (`parasite-2019`/positivas, suspeita de
  reviravolta) REFUTADA.** Fração de `spoiler_flag=True` sobre o bruto
  por bucket, nos 6 filmes já coletados: 0,5%-4,9%, `parasite-2019` em
  2,1%-2,6% — dentro do mesmo intervalo dos outros 5 filmes (`cure`,
  aliás, tem a fração mais alta, 4,9% em `medianas`/`positivas`, e fechou
  40/40/40). Spoiler não explica um déficit de 20% da cota; a causa é
  `abaixo_min_chars`, não `spoiler`.
- **Comparação com o catálogo (`cure`/`cidade-de-deus`/`the-invite-2026`,
  os 3 fecham 40/40/40 nos 9 buckets):** a diferença não é volume bruto
  (`n_brutas` por nível é da mesma ordem de grandeza nos dois grupos) —
  é a FRAÇÃO que sobrevive ao filtro de 150 caracteres. No nível 2,0★ de
  `negativas`, o pool elegível pós-filtro foi ~12% do bruto em
  `parasite-2019` (14/120) contra ~36% em `cidade-de-deus` (43/120), quase
  3× de diferença. Estrutural, não ruído: filmes muito populares atraem
  um volume desproporcional de reviews curtas de reação rápida
  ("garbage", "meh"), diluindo o pool de texto substantivo (≥150 chars)
  amostrado dentro de um orçamento de páginas FIXO — o histograma de
  notas é enorme, mas isso não garante densidade de review LONGA na
  amostra. **Achado estrutural para o lote (registrado, não corrigido
  nesta sessão):** filmes populares (alto volume no Letterboxd) tendem a
  fechar buckets extremos (`negativas`/`positivas`) abaixo da cota mais
  do que filmes de nicho, mesmo com orçamento de páginas idêntico — o
  piso escalonado absorve isso corretamente (n≥15 ainda dá `completa`),
  mas a narrativa de um filme popular pode ter `n` menor que a de um
  filme obscuro do catálogo, contra a intuição.
- **Achado lateral, fora do escopo desta diagnose:** recolher os MESMOS 3
  filmes do zero duas vezes (a 1ª rodada de dados foi apagada por engano
  e precisou ser refeita, ~2h de intervalo entre as duas coletas) produziu
  `n` finais diferentes por bucket sob os MESMOS parâmetros — ver §5.6,
  "Achado lateral não previsto".

**Resultado do lote (v1.9.3, 2026-08-08) — 29 filmes, 0 falhas, `min_chars`
e cascata mantidos em 150/[150,50,0] (auditoria fechou pela manutenção).**
Custo real: 2254 requisições (média 77,7/filme, 12,6% acima da projeção de
69 medida na Entrega 2), 5363s de parede (~1,49h, 15% acima da projeção de
~1,3h — ainda bem abaixo do teto de ~4h), ~6,95 MB de bruto (quase exato à
projeção de ~7,1 MB). Achados estruturais (REGISTRADOS, não corrigidos):

- **`material_esgotado` disparou pela primeira vez em produção.**
  `obsession-2026` (214 notas no total — o filme mais obscuro já coletado)
  parou por esgotamento real em 9 dos 10 níveis (só 1,5★ parou por
  orçamento, tendo 1 página de orçamento e 3 notas totais no nível).
  Persistência, `montar_buckets` e o JSON se comportaram corretamente —
  produziu os primeiros estados REAIS de piso reduzido:
  `negativas`=5 (`sem_numero`), `medianas`=6 (`sem_numero`),
  `positivas`=8 (`sem_quantificador`). Os 3 outros estados do piso
  escalonado (todos exceto `completa`) agora têm exemplo real, não só
  sintético.
- **Distribuição invertida — 2 de 4 candidatos confirmados, não 4.** A
  lista foi curada esperando `joker-folie-a-deux`, `cats-2019`,
  `napoleon-2023` e `wonka` como negativas-dominantes. Medido sob as
  fronteiras C: só `cats-2019` (85,9%) e `joker-folie-a-deux` (46,2%) têm
  `negativas` como bucket dominante do histograma; `napoleon-2023` é
  dominado por `medianas` (44,8%) e `wonka` por `positivas` (50,2%) — a
  expectativa de reputação/crítica não bate com a distribuição real de
  NOTAS sob a fronteira C. Onde a inversão realmente ocorreu, a montagem
  de buckets e a agregação do histograma funcionaram sem incidente — o
  caminho "bucket dominante = negativas" nunca tinha sido exercitado
  contra dado real e não quebrou nada; o campo que informa a ordem de
  abertura do MOVIMENTO 3 ao narrador (fora de escopo tocar aqui) recebe
  o mesmo dado de sempre, só que agora com `negativas` no topo em 2 casos
  reais.
- **Rendimento pós-filtro NÃO correlaciona com popularidade — corrige o
  sinal direcional da diagnose anterior (n=6).** Com os 35 filmes já
  coletados (105 buckets), Pearson r(total de notas do histograma,
  n_final) = 0,05-0,13 por tipo de bucket — essencialmente ZERO,
  contra a leitura direcional de n=6 que sugeria filmes populares
  rendendo pior. Também r(share do bucket no histograma, n_final) = 0,06
  no agregado dos 105 buckets; buckets com share <10% do histograma
  fecham a cota tanto quanto buckets com share ≥10% (70% vs. 65%, mediana
  40 em ambos os grupos). Caso ilustrativo: `wicked-2024`/`positivas` é
  76,2% do histograma (bucket dominante, filme com 2,8M notas) e ainda
  assim fecha só `n=20` — o rendimento pós-filtro é IDIOSSINCRÁTICO ao
  filme (composição de quem escreve review longa naquele fandom
  específico), não previsível por popularidade nem por share. **A
  correção do sinal de n=6: não há evidência, com n grande, de que
  filmes populares rendam sistematicamente pior.**
- **Fechamento de cota por tipo de bucket é equilibrado, não estrutural.**
  `negativas` fecha 66% (23/35), `medianas` 63% (22/35), `positivas` 71%
  (25/35) — nenhum dos três tipos concentra o déficit. Sob o orçamento
  POR BUCKET (v1.9.1+), o viés histórico contra `medianas` (2 níveis vs.
  4) não reaparece; o déficit, quando ocorre, é por filme e por nível
  específico, não pelo formato do bucket.
- **14/29 filmes fecham a cota 40 nos 3 buckets; 84/87 buckets em
  `estado_piso=completa`.** A maioria dos déficits (todos exceto
  `obsession-2026`) fica acima do limiar `completa` (≥15) — a narrativa
  teria número/quantificador/temas completos mesmo nos buckets abaixo da
  cota cheia.


<!-- SPEC.md linhas 3700–3707 · origem: Estratificação da seleção por profundidade — E1 (v1.9.5) -->

**Custo medido: ZERO.** Simulado sobre os 35 filmes antes de adotar — **0 de
105 buckets perdem uma única review**, porque o pool elegível (4906) é 24%
maior que a cota consumida (3948). O uso do material profundo sobe de 54,4%
para **86,2%**. O comprimento médio da amostra não muda (469 → 472 chars), e
o material profundo não tem perfil diferente do raso (147 contra 153 chars de
média, 78,5% contra 76,3% abaixo de `min_chars`, spoiler 2,6% contra 2,5%) —
não há interação com o filtro de comprimento a temer.


<!-- SPEC.md linhas 3758–3959 · origem: Precisão da amostra — nos DOIS níveis de confiança -->

#### Precisão da amostra — nos DOIS níveis de confiança

Uma frequência de tema medida sobre `n` reviews é uma estimativa, e a régua de
**1 erro padrão sozinha promete mais do que entrega** (cobre ~68%, não a
confiança que um leitor assume ao ver uma barra). Ambas ficam registradas:

| `n` do bucket | ±1 EP | ±95% |
|---|---|---|
| **40** (cota cheia) | **±7,9pp** | **±15,5pp** |
| **30** | **±9,1pp** | **±17,9pp** |
| 15 (fronteira de `completa`) | ±12,9pp | ±25,3pp |
| 8 (fronteira de `sem_quantificador`) | ±17,7pp | ±34,6pp |

Pior caso `p = 0,5` (`EP = √(0,25/n)`), que é o teto para qualquer proporção.
Leitura direta: com `n=40`, um tema em 40% e um tema em 25% **não são
distinguíveis** a 95%. É o que justifica o piso escalonado (§3[C3]) suprimir
número antes de suprimir tema — o tema é observação, o número é estimativa, e
os dois degradam em ritmos diferentes.

**Auditoria de `MIN_CHARS=150` (v1.9.3, 2026-08-08) — MEDIÇÃO, zero
requisições, nenhum parâmetro alterado.** `min_chars=150` nunca tinha sido
validado contra dado (herança da v1.0). Motivada pela diagnose do déficit
de buckets (§3[H]), que atribuiu 63-87% do descarte dos 4 buckets
deficitários a `abaixo_min_chars`. Medido sobre os 6 filmes em
`dados/bruto/` (`selecao.selecionar` reexecutado, sem tocar `config.py`):

- **Distribuição de `n_chars`:** 40,6% do bruto agregado tem 0-49 chars,
  23,8% tem 50-99, 9,9% tem 100-149 — **74,3% do bruto fica abaixo de 150**
  em TODOS os 6 filmes, deficitários ou não (46,2%/26,4%/10,4% nos
  deficitários vs. 39,0%/23,1%/9,7% no resto — a cauda curta não é
  exclusiva dos buckets que faltam cota, é a forma normal da distribuição
  em qualquer filme).
- **Simulação de limiares (18 buckets, 6 filmes):** `min_chars=50` fecha
  18/18 na cota; `100` fecha 17/18; `150` (atual) fecha 14/18; `200` fecha
  9/18. Comprimento médio da amostra selecionada cresce monotonicamente
  com o limiar (270 → 362 → 459 → 564 chars). Composição por nível
  respeitada em todos os casos testados (a alocação proporcional não
  quebra sob nenhum limiar simulado).
- **Cascata com rung intermediária (`150→100→50→0` vs. atual
  `150→50→0`):** **NÃO ajudou — piorou um bucket já deficitário.**
  `parasite-2019`/negativas caiu de 28 para 22. Causa isolada por nível:
  o nível 0,5★ (12 reviews brutas, nenhuma ≥150 chars) tem 6 reviews entre
  50-99 chars e só 1 entre 100-149; sob a cascata atual ele cai direto
  para o degrau 50 e pega as 7 (filtro nunca desce "para completar cota",
  só quando o degrau atual dá ZERO — regra da v1.1.0, preservada); sob a
  cascata testada ele para no degrau 100 (não-zero, 1 review) e NUNCA
  chega ao 50, perdendo as 6 reviews de 50-99 que a cascata atual
  aproveitava. Os buckets que já fecham a 150 não mudaram em nenhum caso
  (mudança é localizada, como esperado), mas o efeito na direção oposta
  à hipótese — a regra "só desce em zero" pode tornar uma rung
  intermediária estritamente PIOR para um nível específico, não neutra.
- **Amostra qualitativa (40 reviews, 50-149 chars, semente `24081900`,
  estratificada pelos 6 filmes × 3 buckets):** dado bruto, sem
  classificação — decisão do usuário. **Ressalva de qualidade:** 4 das 40
  (10%) são o placeholder de spoiler do parser (`SPOILER_PLACEHOLDER`,
  "This review may contain spoilers..."), não texto real — `n_chars`
  mede o placeholder, não a review original redigida.
- **Rendimento vs. popularidade (n=6, sinal direcional, NÃO conclusivo):**
  correlação de Pearson entre total de notas do histograma e fração de
  bruto abaixo de 150 chars — os 2 filmes mais populares (`parasite-2019`
  5,7M notas, `everything-everywhere-all-at-once` 4,1M) têm as maiores
  frações abaixo de 150 (83,3% e 74,8%); os 3 do catálogo, com 0,3-1,2M
  notas, ficam em 67,7-72,5%. Direção consistente com a hipótese da
  diagnose, mas `n=6` não sustenta conclusão estatística.

**Decisão (usuário, pós-leitura da Entrega 2): manter `MIN_CHARS=150` e
`CASCATA_CHARS=[150, 50, 0]`.** Nenhum parâmetro alterado nem commitado
por causa desta auditoria — a simulação em 100 quase não mudou nada
(17/18 vs. 14/18) e a rung intermediária testada na Entrega 4 piorou um
bucket já deficitário; a leitura foi que 150 não é o defeito.

**Diagnose de acompanhamento (v1.9.3, pós-lote de 29 filmes) — bucket
DOMINANTE abaixo da cota, quando popularidade não é a causa.** Motivada
por `wicked-2024`/positivas: 76,2% do histograma, 2,8M notas, mas
`n_final=20` — volume não explica escassez. Diagnose sobre o bruto
persistido (`selecao.selecionar` reexecutado, zero rede):

- **H1 (rendimento extremo) — CONFIRMADA.** Rendimento pós-filtro por
  nível de `wicked-2024`/positivas comparado à mediana dos 35 filmes:
  nível 3,5★ = 8,3% (mediana 20,8%, **pior de 35**); 4,0★ = 6,9%
  (mediana 20,8%, **pior de 35**); 5,0★ = 10,0% (mediana 19,8%, 4º pior
  de 35); só 4,5★ fica perto da mediana (25,0% vs. 20,8%). Não é
  escassez de material — é rendimento pós-filtro anormalmente baixo em
  3 dos 4 níveis, contra o mesmo filtro que os outros 34 filmes
  atravessam melhor.
- **H2 (concentração da alocação) — fator AMPLIFICADOR, não causa
  isolada.** A alocação proporcional ao histograma concentra 35,0% do
  orçamento do bucket no nível 4,0★ e 32,5% no 5,0★ — exatamente os 2
  níveis com pior rendimento (6,9% e 10,0%). `deficit_redistribuido=0`:
  a redistribuição (§3[C1]) não teve de onde puxar excedente porque
  TODOS os níveis do bucket rendem mal ao mesmo tempo — o mecanismo que
  socorre um nível fraco com sobra de outro não tem sobra para dar
  quando o déficit é sistêmico ao bucket inteiro, não pontual a um
  nível.
- **H3 (profundidade insuficiente) — REFUTADA.** Zero páginas vazias:
  `paginas_gastas` == páginas distintas com review em todo nível do
  bucket. O orçamento de 16 páginas foi todo gasto em páginas com
  conteúdo real; a causa não é alcance, é filtro.
- **Distribuição de `n_chars` do bucket:** 52,6% abaixo de 50 chars,
  79,2% abaixo de 150 — mais pesado na cauda curta que a média geral dos
  6 filmes da auditoria anterior (74,3%), consistente com H1.

**Generalização (35 filmes) — não é só `wicked-2024`, é uma CLASSE.** 10
casos de bucket dominante abaixo da cota; excluindo `obsession-2026`
(escassez genuína — só 214 notas totais, mecanismo diferente), os outros
9 são TODOS filmes muito populares (1,4M-5,7M notas) com rendimento
10-20%: `talk-to-me-2022`, `pearl-2022`, `parasite-2019`, `wonka`,
`avengers-endgame`, `hereditary`, `shutter-island`, `aftersun`, além de
`wicked-2024`. **Isso reconcilia com o `r≈0,05-0,13` do relatório
agregado do lote** (que olhou os 105 buckets, dominantes e minoritários
juntos, e por isso diluiu o padrão) — filtrando só para o bucket
DOMINANTE de cada filme, o padrão aparece: filme muito popular tende a
render pior no bucket que concentra a maioria das notas, porque esse é o
bucket que mais atrai reação curta de massa. Share do histograma e
volume total de notas **não predizem** `n_final` olhando todos os
buckets juntos, mas prediz mal especificamente o bucket que mais precisa
de precisão (o dominante).

**Consequência para o produto.** Em **4 dos 35 filmes**
(`wicked-2024`, `avengers-endgame`, `talk-to-me-2022`, `aftersun` — os
mesmos 4 mais extremos da lista acima) **o bucket que abre o MOVIMENTO 3
e carrega o rótulo de peso mais forte tem `n` MENOR que os outros dois
buckets do mesmo filme** — a perspectiva majoritária é medida com MENOS
precisão que a minoritária, o oposto do que a intuição sugeriria. Não é
um defeito de honestidade (o piso escalonado e as invariantes de §D2
continuam corretos com qualquer `n`), mas é uma tensão real entre
"popular" e "bem-medido" que a narrativa não expõe ao leitor.

**Correção possível, NÃO aplicada — decisão do usuário.** O mecanismo
identificado é uma interação entre duas decisões independentes e válidas
isoladamente: alocação proporcional ao histograma (§3[C1], que concentra
orçamento nos níveis com mais notas) e `MIN_CHARS=150` (que filtra pior
justamente os níveis de blockbuster com reação de massa) — juntas,
sistematicamente subalocam páginas para o nível ERRADO quando os dois
efeitos coincidem no MESMO nível popular. Não corrigido nesta sessão,
por instrução explícita.

**CORRIGIDO na v1.9.4** pela extensão de orçamento por déficit (§3[B]) —
a correção é observacional, não preditiva, e não toca nenhuma das duas
decisões acima: `MIN_CHARS` e a alocação proporcional seguem idênticos; o
que muda é que um bucket que fecha o orçamento base abaixo da meta com
folga ganha até 8 páginas extras. Resultado medido em §3[B], "Resultado
MEDIDO da recoleta v1.9.4".

#### Proposta temporal (v1.9.6) — MEDIDA, não aplicada

Com as duas pontas em disco (§2.3), a seleção passa a ter uma escolha que
antes não existia: **quanto da cota vem de cada época**. Até aqui a pergunta
não fazia sentido — só havia uma época no bruto.

Três desenhos, simulados sobre os filmes que receberam a passada, sem aplicar
nenhum:

| | desenho | o que assume |
|---|---|---|
| **S1** | seleção ATUAL — ignora `ordenacao_origem`, consome o pool inteiro por `(pagina_origem, ordem no jsonl)` | que as duas pontas são intercambiáveis. **É o comportamento em vigor**, e a simulação existe para mostrar o que ele faz agora que o pool mudou |
| **S2** | cota dividida entre as pontas — 70% recente / 30% antigo | que a recepção recente é o objeto principal e a antiga é contexto |
| **S3** | proporcional ao volume de cada ponta no bruto | que o bruto já é a melhor evidência disponível sobre o peso de cada época |

**Resultado medido (12 filmes, 36 buckets):** os três fecham **36/36** buckets
na cota de 40, com `p5` mediano idêntico (2022-09-02) e comprimento médio
dentro de 5%. A cobertura NÃO decide entre eles. O que decide é a variação da
mistura por bucket:

| | S1 (atual) | S2 (70/30) | S3 (proporcional) |
|---|---:|---:|---:|
| antigas por bucket — mediana | 8,0 | 12,0 | 10,0 |
| antigas por bucket — faixa | **1 a 19** | 12 a 12 | 7 a 11 |
| antigas por bucket — desvio | **4,6** | 0,0 | 1,0 |
| buckets que deixam de fechar | 0 | 0 | 0 |

**RECOMENDAÇÃO: S2**, com a fração `70/30` entrando como parâmetro
ARBITRÁRIO declarado (o rótulo está definido em §2, "O que 'ARBITRÁRIO'
significa nesta spec").
S3 é mais elegante e perde por um motivo específico: a "proporção do bruto"
que ele segue **não é propriedade do filme**, é consequência do orçamento da
passada (18 páginas antigas contra 48 recentes) — dobrar esse orçamento mudaria
a composição da ANÁLISE sem ninguém decidir nada, que é a classe exata de
defeito que esta versão existe para não repetir.

**Ressalva medida:** em S2/S3 as pontas são selecionadas independentemente e
**não há redistribuição entre elas**; um bucket cujo pool antigo seja menor que
a cota não completa pela ponta recente. Não ocorreu nos 12 filmes (216 antigas
por filme, ~97 acima de `min_chars`, contra cota de 12), mas os 12 receberam o
orçamento inteiro — a redistribuição entre pontas é peça a implementar junto da
aplicação, não algo que a simulação validou.

**S1 não é o caso neutro que o nome sugere, e é o principal achado:**
a estratificação por faixas de profundidade (acima) ordena o pool por
`pagina_origem`, e sob `by/added-earliest` `pagina_origem = 1` é o material
**mais antigo**, não o mais recente. Sem consciência de `ordenacao_origem`, a
seleção atual classifica reviews de 2012 como "faixa 1" — a mais rasa/recente.
É o mesmo modo de falha que §2.3 e §3[B'] descrevem: um número que continua
parecendo certo depois que o significado por baixo dele mudou. **Medido:** sob
S1 a mistura varia de 1 a 19 antigas por bucket, e varia DENTRO do mesmo filme
— `the-substance` fica com 47,5% de material antigo em `medianas` e 5% em
`positivas`, no mesmo parágrafo de saída.

**Não aplicada nesta versão, por decisão explícita:** a mudança de seleção
entra junto do schema, para não invalidar a classificação de eixos que roda em
paralelo. O resultado da medição e a recomendação estão em `docs/arquivo-de-estudos/coleta/V196_ORDENACAO.md`.


<!-- SPEC.md linhas 8692–8701 · origem: 6. Incógnitas de Fase 1 — RESOLVIDAS (ver `docs/arquivo-de-estudos/coleta/FASE1_INCOGNITAS.md`) -->

## 6. Incógnitas de Fase 1 — RESOLVIDAS (ver `docs/arquivo-de-estudos/coleta/FASE1_INCOGNITAS.md`)

As três incógnitas abaixo foram resolvidas na Fase 1; os achados já estão incorporados em §2.1 e §3 [A]/[C'] acima. Mantidas aqui só como registro histórico.

1. ~~**Paginação** `.../rated/N/by/activity/page/2/`: confirmar que funciona e não repete conteúdo.~~ **Resolvido:** funciona, não repete (dedup por viewing id), página além da última = 200 com lista vazia.
2. ~~**Página de busca** de slug: estrutura não verificada.~~ **Resolvido:** endpoint real é `/s/search/films/<query>/` (AJAX), não a URL humana (shell React vazio).
3. ~~**Endpoint de texto completo** (`/s/full-text/viewing:<id>/`): validar formato da resposta, e validar o **detector de truncamento** com casos positivos e negativos conhecidos (crítico — ver C'.1).~~ **Resolvido:** endpoint validado; detector corrigido para `.collapsed-text` (não `data-full-text-url`, que não discrimina) — 2 positivos + 2 negativos, zero erros.

---

