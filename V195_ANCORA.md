# v1.9.5 — Âncora de profundidade e estratificação da seleção

**Data:** 2026-08-09 · **Spec:** [SPEC.md](SPEC.md) v1.9.5 (delta escrito ANTES do código)

**Última sessão da camada de COLETA.** Depois desta versão, todo parâmetro
restante do projeto é de ANÁLISE, aplicável sobre o bruto sem uma requisição.

Não tocados: fronteiras, cota, `min_chars`, cascata, orçamento base, teto de
extensão, ordenação, `RESERVA_PROFUNDIDADE`, schema de eixos, lift, estado
`contraste`, `taxonomia_id`, narrador, editor. `resultado/*.json` intacto.

---

## O defeito, e por que ele é o quarto do mesmo tipo

O bloco profundo da v1.9.2 comprava uma mediana de **3 dias** sobre o raso —
26 de 34 filmes abaixo de 7 dias. A causa não era a reserva (25% do orçamento,
que segue igual): era a **âncora**. A progressão partia do fim do bloco raso
(`n_raso+2, +4, +8, +16`), o que com `n_raso ≈ 12` punha as posições
"profundas" em **14, 16, 20 e 28** — de níveis que vão a ~256. **Profundo em
posição de página, raso em tempo.**

É o quarto caso do mesmo padrão no projeto: o `50/20/30` era o número de
degraus de estrela vezes 10; o teto por nível contra a cota por bucket era
mistura de unidades; a ordem de consumo da seleção virou critério de coorte
sem ninguém escolher; agora a âncora. Nos quatro, o valor não estava errado —
**ele nunca tinha sido decidido**.

### Por que não bastava declarar a recência

A saída barata seria não recoletar e declarar ("a análise cobre as reviews mais
recentes"). Ela não alinha os dois canais, e a razão é uma propriedade do dado:
**o histograma não é recortável no tempo.** O endpoint devolve o acumulado da
vida do filme e não existe versão temporal dele. Declarar congelaria
permanentemente um parágrafo em que o rótulo de peso fala de 2012-2026 e a
frequência de tema fala de 6 semanas — não corrigido, só confessado. Como a
única metade ajustável é a da amostra, é ela que se move.

---

## Entrega 1 — Sondagem de profundidade por filme

`src/espectro24/profundidade.py`. Escada geométrica `4 · 16 · 64 · 256` no
nível mais populoso do histograma, seguida de refinamento binário de até 3
passos. Os demais níveis são escalados pela proporção do histograma.

**O passo de escala é um PROXY, e entra na spec com esse rótulo.** O histograma
conta NOTAS; a paginação conta REVIEWS COM TEXTO — a mesma aproximação que
§3[C1] já usa para alocar vagas. A defesa não é que o proxy acerte, e sim que
**errar sai barato**: posição estimada que volta vazia cai no mecanismo de
descoberta da v1.9.2, que revela a profundidade real por monotonicidade e
redistribui o orçamento com `redistribuir_deficit`. Nenhum segundo caminho de
código foi escrito.

Custo por construção: `len(SONDA_ESCADA) + SONDA_MAX_REFINAMENTO` = 7 no pior
caso, **4 no caso dominante** (filme popular: os quatro degraus voltam cheios,
a profundidade é o teto de plataforma, o refinamento nem roda).

Aditiva como a ficha do TMDB e o histograma: falha de rede devolve
`profundidade=None`, o posicionamento degrada para o comportamento v1.9.2, e
a coleta segue. Uma sondagem que não deu certo nunca derruba uma coleta que
vai custar dezenas de requisições.

**Nunca superestima.** O valor devolvido é sempre uma página confirmada com
conteúdo — subestimar é um limite inferior real, superestimar faria a âncora
mirar em página vazia. Há teste paramétrico em 11 profundidades reais.

---

## Entrega 2 — Reancoragem

```
posições profundas = frações da profundidade REAL do nível
FRACOES_PROFUNDIDADE = (0,25 · 0,50 · 0,75 · 0,95)
```

**0,95 em vez de 1,0 é deliberado:** a profundidade vem de um proxy que erra, e
mirar no último ponto exato converteria todo erro para cima numa página vazia.
5% de folga é barato e evita a maior parte desse desperdício.

Degenerados, todos com comportamento nomeado e testado:

| caso | comportamento |
|---|---|
| profundidade ≤ `n_raso` | nenhuma posição profunda — o bloco se fundiria ao raso. Correto para filme obscuro |
| profundidade < nº de posições pedidas | frações colidem, deduplicam, o orçamento restante volta ao raso |
| profundidade desconhecida | progressão geométrica da v1.9.2, byte-idêntica |
| nível zerado no histograma | piso de 1 na escala; na prática não recebe orçamento de página |

### O teste que prova a premissa

`test_numero_de_paginas_por_nivel_nao_muda_com_a_ancora`, paramétrico em 6
orçamentos: o mesmo nível com material de sobra, buscado sob a âncora velha e
sob a nova, tem de gastar **exatamente o mesmo número de páginas** — e as
posições têm de ser diferentes. Se ele cair, a mudança de âncora alterou o
custo da coleta sem ninguém ter decidido isso.

Confirmado também em dado real no primeiro filme recoletado (`aftersun`):
`paginas_gastas_por_nivel` idêntico a `orcamento_paginas_por_nivel`, nível a
nível, e as posições profundas saltando de ≤28 para **52, 64, 128**.

---

## Entrega 3 — Estratificação E1 da seleção

A cota de cada nível passa a ser alocada entre três faixas de `pagina_origem`:

```
faixa 1 = 1 .. ⌈n_raso/2⌉ · faixa 2 = ⌈n_raso/2⌉+1 .. n_raso · faixa 3 = > n_raso
```

A divisão é **estrutural, não um tercil da distribuição observada** — a coleta
já produz dois blocos de naturezas diferentes, e um tercil daria faixas
diferentes em cada filme, sem significado comum. A alocação entre faixas é
`alocar_bucket` + `redistribuir_deficit` (**quinto uso** da mesma função).

**Quem cede quando os dois critérios competem:** com cota de nível < 3 não há
como preencher três faixas, e a estratificação devolve o prefixo do pool — o
comportamento anterior à v1.9.5. A precedência não é arbitrária: a alocação
proporcional por nível carrega uma garantia de representatividade que o
histograma sustenta; a estratificação é preferência de cobertura.

**A estratificação é ADIÇÃO, não substituição.** `selecionar` sem
`orcamento_paginas_por_nivel` é byte-idêntica à v1.9.4 — é isso que mantém o
caminho offline e todo teste anterior válidos, e há teste que o exige.

---
## Achado durante a execução — só duas das quatro frações são alcançáveis

`FRACOES_PROFUNDIDADE` declara quatro posições (25/50/75/95%), mas em produção
**nunca mais que duas são usadas**, e a razão é uma interação entre dois
parâmetros que já existiam:

`TETO_SEGURANCA_PAGINAS_NIVEL = 10` (v1.9.1) limita o orçamento de um nível a
10 páginas; `dividir_raso_profundo(10)` devolve `(8, 2)`. Varrendo todos os
orçamentos possíveis de 1 a 10, o **`n_profundo` máximo é 2**:

| orçamento do nível | 1-2 | 3-5 | 6-10 |
|---|---|---|---|
| `n_profundo` | 0 | 1 | 2 |

Logo, a âncora efetiva desta versão é **25% e 50% da profundidade**, e as
entradas 0,75 e 0,95 são latentes: só passam a existir se o teto por nível
subir. Confirmado no dado real — a página mais profunda alcançada em
`aftersun`, `anatomy-of-a-fall` e `avengers-endgame` é **128**, exatamente 50%
dos 256 sondados.

**Isto é o mesmo padrão que a versão existe para corrigir**, e por isso é
reportado em vez de silenciado: eu escolhi quatro frações, mas quem escolheu
as duas que valem foi a interação entre `TETO_SEGURANCA_PAGINAS_NIVEL` e
`RESERVA_PROFUNDIDADE` — nenhuma das duas classificada como decisão sobre
profundidade.

**Não corrigido nesta sessão, por três razões, nesta ordem:** o lote já estava
em execução e mudar as frações no meio produziria um catálogo coletado sob
duas regras diferentes; `RESERVA_PROFUNDIDADE` e o teto de segurança estão
explicitamente fora de escopo; e a melhora medida de 28 → 128 (4,5×) pode já
bastar — a Entrega 5 abaixo decide isso com o gap em dias.

Se a Entrega 5 mostrar que 50% não basta, a correção é de uma linha (espalhar
as frações pelas posições realmente disponíveis, em vez de tomar as primeiras
da lista) mais uma recoleta.

---
## Achado que refuta a hipótese da sessão — medido durante a recoleta

A âncora nova faz exatamente o que prometeu: as posições profundas saltaram de
≤28 para **128** (metade da profundidade sondada), com o mesmo número de
páginas. **E o gap raso-vs-profundo praticamente não se moveu.**

Nos quatro primeiros filmes recoletados:

| filme | gap antes | gap depois |
|---|---:|---:|
| `aftersun` | 2 d | 3 d |
| `anatomy-of-a-fall` | 7 d | 12 d |
| `avengers-endgame` | 0 d | 0 d |
| `barbie` | 1 d | 3 d |

A causa aparece ao olhar a mediana de `data` **página a página**:

| filme | página mais profunda | mediana na pág. 1 | mediana no fundo | dias | **dias por 100 páginas** |
|---|---:|---|---|---:|---:|
| `avengers-endgame` | 128 | 2026-08-07 | 2026-08-06 | 1 | **0,8** |
| `barbie` | 128 | 2026-08-07 | 2026-07-31 | 7 | **5,5** |
| `aftersun` | 128 | 2026-08-07 | 2026-07-30 | 8 | **6,3** |
| `anatomy-of-a-fall` | 128 | 2026-08-07 | 2026-07-12 | 26 | **20,5** |

**A listagem inteira é rasa em tempo, não só o começo dela.** Para cobrir um
ano de história seriam necessárias ~45 000 páginas em `avengers-endgame`,
~6 600 em `barbie`, ~5 800 em `aftersun` e ~1 780 em `anatomy-of-a-fall`. O
teto de plataforma é **256**.

**Conclusão, reportada como falha e não maquiada:** a âncora estava mesmo no
lugar errado e foi corrigida, mas corrigi-la não alcança o objetivo, porque o
passado do filme **não é alcançável por este endpoint sob `by/added`**. As 256
páginas que a plataforma expõe são as ~3000 adições mais recentes, e para um
filme popular isso é questão de semanas. Nenhum orçamento, nenhuma âncora e
nenhum desenho de seleção muda isso.

### O lever que funcionaria, e por que não foi puxado aqui

A §2.3 já mediu a resposta: `by/added-earliest` devolve a listagem
**estritamente crescente a partir de 2012**. Uma fatia coletada sob essa
ordenação poria material genuinamente antigo no bruto — e a persistência é
incremental, então ela SOMA ao que já existe em vez de substituir.

**Ordenação está explicitamente fora do escopo desta sessão**, e por isso não
foi tocada. Fica registrado como o achado que a medição produziu: o parâmetro
que controla a cobertura temporal é a ORDENAÇÃO, não a posição.

### A nuance que o número agregado esconde

`anatomy-of-a-fall` cobre 20,5 dias por 100 páginas contra 0,8 de
`avengers-endgame` — 25× mais. É o mesmo mecanismo da medição anterior: quanto
menor o fluxo de reviews por dia, mais tempo cada página cobre. Para filmes de
fluxo baixo a reancoragem compra tempo real; para blockbusters não compra
quase nada. O relatório final reporta os dois grupos separados em vez de uma
mediana só.

---
## Achado operacional — o `Fetcher` não tem retentativa

A recoleta expôs uma fragilidade que as coletas anteriores não tinham
provocado: `Fetcher.get` faz **uma** tentativa por requisição e qualquer
`ConnectionResetError`/`ReadTimeout` propaga. Com ~48 requisições de rede por
filme, um único reset transitório em qualquer ponto **aborta o filme inteiro**.

Medido durante esta sessão: 4 falhas nos 15 primeiros filmes
(`dune-2021` por timeout de leitura; `dune-part-two`, `eighth-grade` e
`im-still-here-2024` por reset), todas transitórias — o lote voltou a
funcionar logo depois em cada caso, sem nenhum 403 e sem nenhum
`AntiBotError`. Não é bloqueio: é rede.

**Nenhuma review foi perdida.** É exatamente o caso que o harness de lote
(§3[H]) foi desenhado para absorver: falha isolada por filme, checkpoint em
arquivo, e resume que reprocessa todo slug que não está `concluido`. Como as
páginas já buscadas estão em cache, a retomada custa só o que faltava.

Registrado como candidato a próxima sessão, **não implementado aqui**:
retentativa com backoff em `Fetcher.get` para erros de transporte
(distinta do tratamento de 403, que deve continuar parando o lote sem
escalar). É mudança na camada de coleta, que esta sessão fecha — mas é de
robustez, não de amostragem, e portanto não altera nenhum dado coletado.

---
## Entrega 4 — Recoleta: interrompida por decisão, aos 18 de 35

**O lote foi parado por mim, não por falha do harness.** Aos 28 filmes
processados havia **10 falhas de rede** (36%), incluindo um **HTTP 503** —
`shutter-island`, nível 1,0★, página 4. 503 é o servidor dizendo que está
sobrecarregado. A política da spec para pressão do site é parar e reportar,
não insistir (§restrições, "não escala para evasão"), e o achado central já
estava estabelecido com os filmes medidos.

Falharam por rede: `dune-2021`, `dune-part-two`, `eighth-grade`,
`im-still-here-2024`, `interstellar`, `napoleon-2023`, `oppenheimer-2023`,
`pearl-2022`, `shutter-island`, `talk-to-me-2022`. Nenhuma delas é falha de
código — o harness isolou todas e o checkpoint permite retomar.

**Custo real, muito abaixo da projeção:** 271 requisições em 18 filmes =
**15,1/filme**, contra os ~44/filme projetados (~40 páginas novas + 4 de
sondagem). A sondagem custou 69 requisições (25% do total), **3 a 4 por
filme**, exatamente o previsto. A diferença está nas páginas novas: muito
menos que 40, porque `n_profundo ≤ 2` por nível e vários níveis nem emitem
posição profunda (profundidade estimada ≤ `n_raso`).

**Nada foi perdido na recoleta incremental:** o bruto dos 18 filmes foi de
10 472 para 11 989 reviews (+1517), e nenhum filme perdeu uma única review.

---

## Entrega 5 — O que a correção comprou

### O número que valida a sessão: **não comprou tempo**

| | antes | depois |
|---|---:|---:|
| **gap raso-vs-profundo, mediana** | **3 d** | **5 d** |
| gap, média | 12 d | 12 d |
| filmes com gap ≤ 7 dias | 13 de 17 | 10 de 17 |

**O desenho falhou no seu objetivo declarado, e é assim que fica registrado.**
A âncora foi corrigida — as posições profundas saltaram de ≤14 para 128 em 11
dos 18 filmes, com o mesmo número de páginas — e o tempo não veio junto.

### Por que: a listagem inteira é rasa em tempo

| filme | dias por 100 páginas | páginas para cobrir 1 ano |
|---|---:|---:|
| `spider-man-across-the-spider-verse` | 0,0 | — |
| `avengers-endgame` | 0,8 | 46 355 |
| `cidade-de-deus` | 2,4 | 15 452 |
| `everything-everywhere-all-at-once` | 3,1 | 11 589 |
| `barbie` | 5,5 | 6 622 |
| … | | |
| `parasite-2019` | 93,8 | 389 |
| `cats-2019` | 117,3 | 311 |
| `friday-the-13th-2009` | 163,6 | 223 |
| `obsession-2026` | 6 100 | 6 |

Mediana: **1783 páginas para cobrir um ano. O teto de plataforma é 256.**
**Em apenas 2 dos 17 filmes** 256 páginas cobririam um ano de história.

O passado do filme não está "coletado no lugar errado" — ele **não é
alcançável por este endpoint sob `by/added`**. As 256 páginas que a plataforma
expõe são as ~3000 adições mais recentes.

### A ironia que a medição expõe

A reancoragem vai fundo exatamente onde profundidade não vale nada, e fica
rasa exatamente onde valeria:

- os filmes que alcançaram a página 128 (`avengers-endgame`, `barbie`,
  `spider-man`) cobrem **0,0 a 5,5 dias por 100 páginas**;
- os filmes de melhor cobertura temporal (`friday-the-13th-2009` 163,6;
  `cats-2019` 117,3; `parasite-2019` 93,8) **não saíram da página ~9-14**,
  porque a profundidade estimada dos níveis deles fica ≤ `n_raso` e o bloco
  profundo, corretamente, não emite posição.

Não é um bug: é o degenerado nomeado na Entrega 2 funcionando. Mas significa
que a correção entrega profundidade na razão inversa da sua utilidade.

### O que a correção COMPROU de verdade

Três ganhos reais, todos colaterais ao objetivo declarado:

| | antes | depois |
|---|---:|---:|
| buckets a 40 (catálogo) | 80/105 | **85/105** |
| buckets a 40 (só recoletados) | 46/54 | **51/54** |
| fração profunda da amostra | 26,1% | **32,6%** |
| bruto dos 18 filmes | 10 472 | **11 989** |

`bones-and-all` (30/34/40 → 40/40/40), `barbie` (40/35/40 → 40/40/40) e
`hereditary` (36/40/39 → 40/40/40) passaram a fechar a cota nos três buckets.
Mais material bruto, mais diversidade de posição, mais buckets fechando — só
não mais tempo.

A janela da amostra em `data` até **encurtou** (68 → 60 dias medianos), o que é
coerente: material profundo que não é mais antigo, entrando no lugar de
material raso que ocasionalmente carregava um registro atrasado.

---

## Recomendação

**A cobertura temporal não é alcançável por posição. O parâmetro que a
controla é a ORDENAÇÃO.**

A §2.3 já mediu a resposta em 2026-08-07: `by/added-earliest` devolve a
listagem **estritamente crescente a partir de 2012**. Uma fatia coletada sob
essa ordenação poria material genuinamente antigo no bruto, e a persistência é
incremental — ela SOMA ao que já existe. A chave de cache inclui a ordenação
(§3[B]), então não há risco de servir a amostra errada.

Ordenação está explicitamente fora do escopo desta sessão e **não foi tocada**.

Enquanto isso não for decidido, a conclusão da sessão anterior continua
valendo sem alteração: **a declaração da janela na interface é obrigatória,
não opcional**, porque nenhuma mudança da camada de coleta alinha os dois
canais.

### Duas pendências que esta sessão criou

1. **Só 2 das 4 frações são alcançáveis** (`TETO_SEGURANCA_PAGINAS_NIVEL = 10`
   limita `n_profundo` a 2). A âncora efetiva é 25%/50%. Correção: uma linha,
   espalhando as frações pelas posições disponíveis em vez de tomar as
   primeiras da lista — mas só vale a pena junto de uma decisão sobre
   ordenação, porque sozinha ela aprofunda onde profundidade não paga.
2. **17 filmes seguem com o bruto da v1.9.4**, 10 deles por falha de rede. O
   catálogo está em estado MISTO — e como a mudança é aditiva (o bruto só
   cresce), isso não corrompe nada, mas a `profundidade_sondagem` no
   `meta.json` diz quais filmes passaram pela âncora nova.

---

## Testes

**815 passando** (eram 765). Os obrigatórios do briefing:

| exigência | teste |
|---|---|
| posições nas frações da profundidade, não incrementos do raso | `test_posicoes_sao_fracoes_da_profundidade_nao_incrementos_do_raso` |
| **nº de páginas inalterado pela âncora** | `test_numero_de_paginas_por_nivel_nao_muda_com_a_ancora` (6 orçamentos) |
| sondagem com custo limitado | `test_custo_da_sondagem_e_limitado`, `test_filme_popular_custa_4_requisicoes_e_devolve_o_teto` |
| falha de sondagem degrada para v1.9.2 | `test_falha_de_rede_degrada_sem_quebrar`, `test_profundidade_desconhecida_cai_no_comportamento_v192` |
| proxy que erra redistribui pelo mecanismo existente | `test_estimativa_errada_redistribui_pelo_mecanismo_existente` |
| degenerados (prof. 1, menor que as posições, nível zerado) | `test_profundidade_1`, `test_profundidade_curta_deduplica_posicoes_colididas`, `test_escala_com_nivel_zerado_no_histograma` |
| E1: cota respeitada | `test_cota_do_bucket_nao_muda_com_estratificacao` |
| E1: conflito resolve a favor da alocação | `test_cota_de_nivel_menor_que_3_cede_para_a_alocacao` |
| E1: buckets que fecham continuam fechando | `test_bucket_que_fecha_hoje_continua_fechando` |
| regressão: recoleta incremental não perde review | verificado em dado real (18 filmes, +1517 reviews, zero perdas) |

## Reprodução

```bash
python scripts/recoleta_v195.py antes
python scripts/recoleta_v195.py recoletar
python scripts/recoleta_v195.py depois
```
