# v1.9.6 — Retentativa no Fetcher e passada `by/added-earliest`

**Data:** 2026-08-09 · **Spec:** [SPEC.md](SPEC.md) v1.9.6 (delta escrito ANTES do código)

Não tocados: fronteiras, cota, `min_chars`, cascata, orçamento base, teto de
extensão, `RESERVA_PROFUNDIDADE`, `FRACOES_PROFUNDIDADE`, schema de eixos,
lift, estado `contraste`, `taxonomia_id`, narrador, editor. Nenhuma mudança de
SELEÇÃO aplicada. `resultado/*.json` intacto.

---

## O que a v1.9.5 deixou provado, e o que esta sessão faz com isso

A v1.9.5 corrigiu a âncora do bloco profundo — as posições saltaram de ≤28
para 128 com o mesmo número de páginas — e **mediu que isso não compra tempo**:

| | |
|---|---|
| mediana do catálogo para cobrir 1 ano | **1783 páginas** |
| teto de paginação da plataforma | **256** |

As 256 páginas expostas sob `by/added` são as ~3000 adições mais recentes.
Nenhum orçamento, nenhuma âncora e nenhum desenho de seleção alcança o passado
por POSIÇÃO. O parâmetro que controla cobertura temporal é a **ORDENAÇÃO**, e
a §2.3 já tinha medido que `by/added-earliest` devolve a listagem crescente
desde 2012.

Esta sessão puxa esse lever — seletivamente, porque a mesma medição mostrou
que **metade do catálogo não precisa dele**.

---

## Entrega 1 — Retentativa que distingue transporte de bloqueio

`Fetcher.get` (§2.4). Até aqui: uma tentativa, e qualquer `ConnectionResetError`
abortava o filme inteiro. Medido na v1.9.5: **10 falhas em 28 filmes (36%)**,
todas transitórias.

**O que retenta:** erro de TRANSPORTE — a requisição não produziu resposta HTTP
nenhuma. Até 3 tentativas, backoff `2s · 4s` com jitter de ±25%. O delay de
educação (§2.1) continua valendo entre todas as tentativas: a retentativa
**soma** a ele, não substitui.

**O que NÃO retenta — a metade que importa:**

| condição | comportamento |
|---|---|
| 403 / challenge Cloudflare | para na hora, sem retentar, sem escalar |
| 503, 1ª ocorrência **do lote** | 1 retentativa, espera longa (30s) |
| 503, 2ª ocorrência **do lote** | `SobrecargaError` → **para o lote** |
| 404 e demais status ≠ 200 | falha na hora — é resposta, não erro de transporte |

Duas decisões de desenho que os testes fixam:

- **O contador de 503 é do LOTE.** O harness cria um `Fetcher` por filme; sem
  um `PressaoDoSite` compartilhado, "o segundo 503 do lote" seria
  inexprimível — cada filme recomeçaria a contagem, e a política viraria
  "insistir uma vez por filme, para sempre". Há teste que dispara o segundo
  503 num `Fetcher` DIFERENTE e exige a parada.
- **`SobrecargaError` não herda de `FetchError`.** As etapas aditivas
  (histograma §3[G], ficha §3[F]) capturam `FetchError` de propósito, para não
  derrubar uma coleta cara por um dado opcional. Se a parada de lote fosse um
  `FetchError`, elas a engoliriam em silêncio.

`tests/test_retentativa.py` (18 casos): 5 tipos de erro de transporte retentando
e sucedendo na 2ª; teto de 3 tentativas; a sequência exata de `sleep`
(`2, 2, 2, 4, 2` — educação e backoff intercalados); jitter dentro da faixa;
403, challenge e 404 parando na primeira; 503 cruzando `Fetcher`; e o cache
continuando a não pagar nem o delay.

---

## Entrega 2 — `dias_por_100_paginas` como métrica persistida

Calculada na COLETA e gravada em `meta.json`, por filme e por nível (§3[B']).
A v1.9.5 a calculou em análise, num script de sessão; ela sobe para o material
persistido porque é **o discriminador de qual estratégia cada filme precisa**.

```
dias = mediana(data na página mais RASA) − mediana(data na mais FUNDA)
dias_por_100_paginas = 100 × dias / (pagina_max − pagina_min)
```

A **mediana por página**, não a data de uma review: `data` é a data ASSISTIDA
(§3[B'], proxy contaminado) e um único outlier domina min/max.

**A ressalva, e por que ela não invalida este uso:** o que se mede é a TAXA ao
longo das páginas, não a data absoluta. A contaminação (quem registra hoje uma
sessão de anos atrás) é ruído aproximadamente uniforme sobre as posições —
alarga a dispersão dentro de cada página sem inclinar sistematicamente a
diferença ENTRE páginas distantes. O uso proibido continua proibido.

Bordas nomeadas e testadas: menos de 2 páginas com data → `None`; todas as
datas iguais → `dias = 0` e `paginas_para_1_ano = None` (não há resposta
finita, e `0` mentiria); taxa NEGATIVA é reportada como medida, não zerada.

**Limitação declarada:** a precisão é limitada pelo alcance do bruto. Um filme
cujo bruto vai só até a página 12 estima a taxa sobre um vão de 12 páginas, e
o campo carrega `pagina_min`/`pagina_max` para que isso seja lido em vez de
suposto. Dos 35 filmes do catálogo, **12 têm vão de 127 páginas** (recoletados sob a
âncora da v1.9.5), 1 tem 63, e **22 têm vão de 1-17 páginas** — coletas
anteriores à âncora, ou interrompidas pelo 503 que parou a v1.9.5. Para esses
22, a taxa é medida sobre um vão curto e **extrapolá-la para 256 páginas é
extrapolação**, não medição. Isso afeta a FRONTEIRA do critério, e há casos
reais nela: `talk-to-me-2022` e `wicked-2024` ficaram de fora com 23,5 —
apenas 18% acima do corte, medidos sobre 17 páginas. Se a taxa deles cair sob
um vão maior, entram. O miolo não muda: os 12 selecionados vão de 0,0 a 11,8,
e os 8 mais altos de fora começam em 20,5.

---

## Entrega 3 — Passada seletiva sob `by/added-earliest`

### Quem entra no critério

`dias_por_100_paginas < 20` — o corte que responde "as 256 páginas que a
plataforma expõe cobrem pelo menos um ano?". **12 de 35 filmes.**

| DENTRO (12) | dias/100 pág | | FORA (23), os 8 primeiros | dias/100 pág |
|---|---:|---|---|---:|
| `spider-man-across-the-spider-verse` | 0,0 | | `anatomy-of-a-fall` | 20,5 |
| `the-invite-2026` | 0,0 | | `talk-to-me-2022` | 23,5 |
| `avengers-endgame` | 0,8 | | `wicked-2024` | 23,5 |
| `cidade-de-deus` | 2,4 | | `cure` | 25,4 |
| `everything-everywhere-all-at-once` | 3,1 | | `longlegs` | 27,6 |
| `barbie` | 5,5 | | `wonka` | 29,4 |
| `aftersun` | 6,3 | | `interstellar` | 45,5 |
| `bones-and-all` | 7,9 | | `oppenheimer-2023` | 45,5 |
| `dune-2021` | 9,1 | | … até `obsession-2026` | 6100,0 |
| `the-substance` | 9,1 | | | |
| `perfect-days-2023` | 10,2 | | | |
| `hereditary` | 11,8 | | | |

Lista completa dos 23 de fora em `resultado/v196-passada/selecao.json`.
`anatomy-of-a-fall` (20,5) fica de fora por 0,5 — o limiar é arbitrário e está
rotulado como tal; o filme está na fronteira e é o primeiro candidato se o
corte se mover.

### O que a passada NÃO faz, e por quê

- **Sem sondagem de profundidade.** Ela existe para ancorar o bloco PROFUNDO, e
  sob ordenação CRESCENTE o fundo da listagem é o material mais RECENTE —
  exatamente o que a coleta base já tem. Economia: 4 requisições por filme,
  gastas em duplicata.
- **Sem extensão por déficit.** A extensão (v1.9.4) mede déficit contra a cota
  de análise, que a passada não está tentando fechar.
- **Sem requisição de histograma.** É o acumulado da vida do filme e não muda
  por ordenação — vem do `meta.json` da coleta base.

### As duas assimetrias que duas ordenações no mesmo bruto obrigaram a resolver

**(1) `pagina_origem` deixou de ter significado único.** `reviews.jsonl` ganhou
`ordenacao_origem`. Sem ele, a página 1 significaria "mais recente" e "mais
antiga" no mesmo arquivo, e a estratificação da seleção (§3[C2]) trataria
review de 2012 como a faixa mais rasa — silenciosamente, com o número parecendo
certo. Compatibilidade: default `None` = "coletada antes do campo existir",
resolvido no CONSUMO por `meta["ordenacao_usada"]`, **sem reescrever dado
histórico com uma inferência**.

**(2) `meta.json` deixou de ser "a última execução".** Uma passada de 6 páginas
por bucket sobrescreveria `orcamento_paginas_por_nivel` — que a seleção LÊ para
achar a fronteira raso/profundo — e junto com ele `paginas_gastas_por_nivel`,
`profundidade_sondagem` e `janela_temporal` da coleta que produziu 95% do
material. O corpo do meta passa a descrever a coleta BASE, e cada passada entra
na lista `passadas`. Repetir a mesma ordenação SUBSTITUI o item dela: a lista
descreve ordenações presentes no bruto, não um log de execuções.

### Custo real

| | |
|---|---|
| filmes | **12/12 concluídos**, 0 falhas |
| requisições | **610** (mediana 48/filme, faixa 39-82) |
| páginas | **18 por filme**, exatamente o orçamento — `orcamento_esgotado` em todos os níveis de todos os filmes, `material_esgotado` em nenhum |
| completamentos [C'] | **32,8 por filme** (o resto das 50,8 requisições medianas) |
| tempo | **0,62 h** (37 min) |
| reviews novas | **2592** (216 por filme; `the-substance` 215) |
| retentativas | **1** (`barbie`) — absorvida, filme concluído |
| HTTP 503 | **0** |

A Entrega 1 pagou na primeira execução: a única retentativa foi um erro de
transporte no meio de `barbie`, que sob a v1.9.5 teria abortado o filme e
custado uma retomada.

**O completamento é 65% do custo**, não a paginação. Ele usa o MESMO
`alvo_por_nivel` da coleta base de propósito — sob orçamento menor, o material
antigo pareceria mais curto por artefato de medição, e o perfil comparado
abaixo é o achado principal da sessão.

---

## Entrega 4 — O que a passada comprou

### Janela temporal do bruto

`p5` do bruto, antes e depois. **`min`/`max` são inutilizáveis** e a passada
mostrou por quê: `barbie` tem uma review datada de **1442-07-09** (data
assistida é campo livre de diário, §3[B']), o que produz uma "cobertura" de
584 anos. Os percentis são o que se pode ler.

| filme | p5 antes | p5 depois | p5-p95 antes | p5-p95 depois |
|---|---|---|---:|---:|
| `aftersun` | 2026-06-25 | 2022-05-22 | 44 d | **1539 d** |
| `avengers-endgame` | 2026-07-21 | 2019-04-23 | 18 d | **2664 d** |
| `barbie` | 2023-07-25 | 2023-07-09 | 1110 d | **1126 d** |
| `bones-and-all` | 2026-07-25 | 2022-09-02 | 14 d | **1436 d** |
| `cidade-de-deus` | 2026-03-22 | 2012-08-30 | 137 d | **5089 d** |
| `dune-2021` | 2026-07-05 | 2021-09-03 | 34 d | **1800 d** |
| `everything-everywhere-all-at-once` | 2024-08-07 | 2022-03-11 | 730 d | **1610 d** |
| `hereditary` | 2026-07-05 | 2018-03-12 | 34 d | **3071 d** |
| `perfect-days-2023` | 2026-06-19 | 2023-05-25 | 50 d | **1170 d** |
| `spider-man-across-the-spider-verse` | 2026-01-20 | 2023-05-29 | 200 d | **1167 d** |
| `the-invite-2026` | 2026-07-26 | 2026-01-24 | 12 d | **195 d** |
| `the-substance` | 2025-12-30 | 2024-05-19 | 221 d | **811 d** |

**Mediana do catálogo selecionado: 47 dias → 1487 dias (4,1 anos).** Em
`cidade-de-deus` (2002) o `p5` do bruto passa a **2012-08-30** — o ano em que
a listagem começa (§2.3, medido ao vivo em `cure`), ou seja, praticamente toda
a vida do filme no site.

**No CATÁLOGO inteiro** (35 filmes — os 23 de fora entram inalterados, é assim
que uma passada seletiva deve ser contada):

| cobertura `p5-p95` do bruto | antes | depois |
|---|---:|---:|
| mediana | 116 d | **582 d** |
| média | 447 d | **992 d** |
| filmes cobrindo ≥ 1 ano | 11/35 | **20/35** |

Os números exatos por filme estão em `resultado/v196-passada/comparacao.json`
(`janela_antes`/`janela_depois` com os cinco campos de §3[B']).

### As duas pontas, e o material antigo

Cada filme ganhou **216 reviews** de `by/added-earliest` (18 páginas × 12),
contra 576-791 já em disco — **21% a 27% do bruto por filme** (18% a 28%
quando medido por bucket, mediana 24%).

**PERFIL DO MATERIAL ANTIGO — o achado que decide o desenho da seleção:**

| | ponta recente (`by/added`) | ponta antiga (`by/added-earliest`) |
|---|---:|---:|
| comprimento médio | **151 chars** | **361 chars** (2,4×) |
| fração abaixo de `min_chars` (150) | **76,5%** | **55,2%** |
| fração com `spoiler_flag` | 2,6% | **4,9%** (1,9×) |
| fração truncada na listagem | 6,0% | **16,4%** |
| fração com texto completo resolvido | 98,9% | 99,1% |

O material antigo é **sistematicamente mais longo**, e a diferença é grande:
onde a ponta recente entrega ~23 reviews acima de `min_chars` por 100
coletadas, a antiga entrega ~45. A taxa de truncamento (2,7×) é consequência
da mesma coisa — review longa vem colapsada na listagem.

**Não é artefato de medição.** As duas pontas passaram pela MESMA política de
completamento e terminam com 99% de texto resolvido nas duas — foi para isso
que a passada usou o `alvo_por_nivel` da coleta base em vez de um menor.

**O que a diferença NÃO permite concluir:** que reviews antigas *sejam* mais
longas. `by/added-earliest` amostra uma COORTE (quem escreveu primeiro:
público de festival, primeiros adeptos, base inicial do Letterboxd), e coorte
e época estão confundidas por construção — a §2.3 já registrava esse recorte
como o motivo de a ordenação ter sido rejeitada como amostragem única em
v1.9.0. O que está medido é: **o material que esta ordenação traz tem esse
perfil**. Separar época de coorte exigiria uma amostragem que este endpoint
não oferece.

**Distribuição de nível** (agregada nos 12 filmes) — semelhante o bastante
para não distorcer bucket nenhum: a ponta antiga tem +7,1 pp em 3,0★ e
−5,9 pp em 2,5★; os outros oito níveis ficam dentro de ±3 pp.

### Buckets

**34/36 → 36/36 na cota de 40.** Os dois que faltavam fecharam:

| filme | bucket | n antes | n depois |
|---|---|---:|---:|
| `dune-2021` | negativas | 33 | **40** |
| `the-substance` | medianas | 31 | **40** |

Os dois estavam em `estado_piso=completa` mesmo abaixo da cota, então o ganho
não é de estado — é de precisão. É também um efeito direto do perfil acima: o
que faltava era material acima de `min_chars`, e a ponta antiga o entrega ao
dobro da taxa.

**Ressalva de escopo:** esses são os 2 buckets sub-40 DOS 12 FILMES
selecionados. O catálogo inteiro tinha outros — nos 23 filmes de fora, que
não receberam passada e continuam como estavam.

---

## Entrega 5 — Proposta de seleção temporal (medida, NÃO aplicada)

Simulação sobre os 12 filmes que receberam a passada — 36 buckets. Nenhuma
alteração de código de seleção; os três cenários chamam a MESMA
`selecao.selecionar`, com cotas diferentes.

| | S1 (atual) | S2 (70/30) | S3 (proporcional) |
|---|---:|---:|---:|
| n final por bucket | 40 | 40 | 40 |
| buckets que fecham a cota | **36/36** | **36/36** | **36/36** |
| buckets que deixariam de fechar | **0** | **0** | **0** |
| antigas por bucket — mediana | 8,0 | 12,0 | 10,0 |
| antigas por bucket — **faixa** | **1 a 19** | 12 a 12 | 7 a 11 |
| antigas por bucket — **desvio** | **4,6** | 0,0 | **1,0** |
| comprimento médio da amostra | 528 | 553 | 532 |
| `p5` mediano da amostra | 2022-09-02 | 2022-09-02 | 2022-09-02 |
| `p50` mediano da amostra | 2026-08-04 | 2026-08-05 | 2026-08-06 |

**Os três produzem praticamente a mesma amostra em agregado.** É por isso que
a recomendação não pode se apoiar em cobertura: ela se apoia em QUEM ESCOLHE.

### S1 não é o caso neutro — é o caso não decidido

A seleção atual ordena o pool por `pagina_origem` e aloca entre três faixas de
profundidade (§3[C2]). Sob `by/added-earliest`, `pagina_origem = 1` é o
material mais ANTIGO, então as 216 reviews da passada entram nas faixas
"rasas" — as que a estratificação da v1.9.5 criou para significar *recente*.

O resultado é uma mistura temporal que ninguém escolheu, e ela **varia por
bucket dentro do mesmo filme**:

| filme | antigas por bucket sob S1 (neg/med/pos) | sob S3 |
|---|---|---|
| `cidade-de-deus` | **5 / 14 / 1** | 10 / 10 / 9 |
| `the-substance` | **13 / 19 / 2** | 11 / 11 / 11 |
| `spider-man-across-the-spider-verse` | **4 / 17 / 5** | 10 / 10 / 9 |
| `perfect-days-2023` | **8 / 4 / 3** | 11 / 10 / 9 |

Em `the-substance`, o bucket `medianas` fica com 47,5% de material de 2024 e o
`positivas` com 5% — no MESMO filme, no MESMO parágrafo de saída. Isso é o
quinto caso do padrão que o projeto vem catalogando (50/20/30 pelo número de
degraus; teto por nível contra cota por bucket; a ordem de consumo virando
critério de coorte; a âncora): **o valor não está errado, ele nunca foi
decidido**.

### Recomendação: S2, com a fração declarada como parâmetro

**S2 (70% recente / 30% antigo).** O que sustenta:

1. **Custo zero contra S1** — 36/36 buckets fecham, `n` idêntico, comprimento
   médio 4,9% maior. Não se troca precisão por cobertura.
2. **Desvio 4,6 → 0,0.** A mistura passa a ser a mesma em todo bucket de todo
   filme, e passa a ser legível no JSON de saída em vez de emergente.
3. **A fração é insensível ao orçamento da coleta.** É aqui que S3 perde,
   apesar de ser o candidato mais elegante: a "proporção do bruto" que ele
   segue (18-28%, mediana 24%) **não é uma propriedade do filme** — é
   consequência de eu ter coletado 18 páginas antigas contra 48 recentes.
   Dobrar o orçamento da passada mudaria a composição da ANÁLISE sem ninguém
   decidir nada, que é exatamente a classe de defeito que S2 evita e que esta
   versão existe para não repetir.
4. **`70/30` é ARBITRÁRIO, e entra rotulado como tal** — mesma política dos
   limiares do piso escalonado (§3[C3]) e de `LIMIAR_PASSADA_ANTIGA`. A defesa
   é a ordem de grandeza: a recepção recente é o objeto principal do produto,
   e a antiga entra como contexto, não como metade.

**Ressalva medida, não hipotética:** em S2 e S3 as duas pontas são
selecionadas independentemente e **não há redistribuição entre elas** — se o
pool antigo de um bucket for menor que sua cota, o bucket não completa pela
ponta recente. Aqui isso nunca aconteceu, e o número que explica: cada filme
tem 216 antigas, das quais ~45% passam `min_chars` (~97 elegíveis) contra uma
cota de 12. **Mas os 12 filmes medidos são os que receberam o orçamento
inteiro de 18 páginas.** Para um filme que esgote material antes disso, a
redistribuição entre pontas é uma peça que S2 ainda não tem, e implementá-la é
parte de aplicar a proposta — não algo que a simulação já validou.

**NÃO APLICADA nesta versão, por decisão explícita:** a mudança de seleção
entra junto do schema, para não invalidar a classificação de eixos que roda em
paralelo. Nada em `selecao.py` mudou; `resultado/*.json` não foi
republicado.

---

## O que fica aberto

- **Aplicar S2** (com redistribuição entre pontas), junto do schema.
- **`ordenacao_origem` ainda não é lido pela seleção.** Enquanto não for, o
  comportamento em vigor é S1 — a mistura não decidida acima. Está registrado
  em §3[C2] e é a razão principal para a próxima sessão pegar isso.
- **Os 23 filmes de fora não têm ponta antiga**, por desenho. Se a proposta de
  seleção passar a exigir as duas pontas em todo filme, o critério de §2.3
  precisa ser reaberto — hoje ele responde "quem PRECISA", não "quem PODE".
- **`talk-to-me-2022` e `wicked-2024`** (23,5, medidos sobre 17 páginas) são
  os primeiros candidatos se o limiar ou a precisão da métrica mudarem.
- **`VERSAO_COLETOR` subiu para 1.9.6** (o `reviews.jsonl` ganhou campo), mas
  as 12 entradas de `passadas` desta sessão gravaram `1.9.0`: o processo do
  lote já tinha importado o valor antigo quando o bump foi feito. Não
  reescrito à mão — um carimbo corrigido depois do fato não é evidência de
  nada.
