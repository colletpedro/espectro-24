# Espectro 24 — Especificação v1.9.50

**Data:** 2026-09-08

> **O título deste documento e a constante `SPEC_VERSION` são duas coisas
> diferentes, e a divergência é DELIBERADA.** O título é a versão do
> DOCUMENTO — a última decisão registrada aqui. `SPEC_VERSION` (`config.py`)
> está em **`1.9.49`** e é o
> carimbo de ARTEFATO DE PIPELINE: ele só sobe quando muda alguma coisa que
> um `resultado/<slug>.json` carrega. As v1.9.26–v1.9.37 foram sessões de
> frontend e de harness de publicação, que não regeram artefato de pipeline —
> por isso o carimbo não subiu. A v1.9.49 volta a subir o carimbo porque muda
> o contrato e o schema da ficha publicada (`ficha.identidade`). Os artefatos
> anteriores não são recarimbados: só uma nova geração pode constituir essa
> evidência. *(Correção de registro: até 2026-09-04 o título dizia
> `v1.9.25` e a data `2026-08-26`, doze versões atrás do próprio conteúdo —
> o título estava copiando o carimbo de artefato em vez de nomear o
> documento.)*


---

## Como este documento foi dividido (2026-09-04)

Este arquivo passou a conter **só LEI**: o que vale agora. Regras que o código
obedece, contratos entre módulos, arquitetura do pipeline, parâmetros e
comportamentos atuais, schema, e os critérios que decidem publicação.

O que saiu, e para onde:

| arquivo | responde |
|---|---|
| `PROTOCOLO.md` | *como eu faço X* — leitura cega, P1–P7, bateria de aceite, regras de teste e ambiente |
| `HISTORICO_COLETA.md` | *por que a coleta é assim* — recoletas, profundidade, orçamento de páginas |
| `HISTORICO_CLASSIFICACAO.md` | *por que a régua é assim* — nulo do máximo, margem de 20pp, gabarito, cobertura |
| `HISTORICO_PROSA.md` | *por que a prosa é assim* — síntese, narrador, veredito, editor aposentado |
| `HISTORICO_FRONTEND.md` | *por que a interface é assim* — barra, pôster, backdrop, topo editorial |
| `CHANGELOG.md` | o registro versão a versão |
| `ABERTO.md` | *o que eu preciso decidir* — um item por decisão pendente |

**Decisão de formato:** toda regra que carregava a justificativa embutida
perdeu a justificativa e ganhou, no lugar dela, **uma linha de ponteiro** para o
arquivo e a seção onde o argumento foi parar. O ponteiro tem a forma
`> *(→ justificativa, medição e histórico desta regra: …)*` e foi **gerado a
partir da própria partição do texto**, não escrito à mão — por isso nenhum
aponta para alvo inexistente.

O texto das regras não foi reescrito: cada linha abaixo é byte a byte a que
estava na spec de 9.128 linhas. Nada foi corrigido nesta passada, inclusive
contradições conhecidas — elas estão listadas em `ABERTO.md`.

> *(→ justificativa, medição e histórico desta regra: `CHANGELOG.md` — "Espectro 24 — Especificação v1.9.37")*

## 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO

> Os três grupos recebem **formato idêntico**: mesma profundidade de análise
> (cota **40/40/40** — v1.9.0; era 50/20/30 até a v1.8.2), mesma estrutura de
> temas, mesmo estilo tipográfico, mesmo espaço estrutural na interface. **A
> assimetria vem dos dados, não da apresentação.**


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO" · `HISTORICO_PROSA.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

**Duas invariantes que a inversão NÃO toca:**

1. **`share` por faixa NÃO é nota média.** São três números que particionam a
   população de notas, cada um atribuído à sua faixa. A proibição de score
   agregado, nota média ou "X de 10" (§1) permanece **intacta** e está escrita
   dentro da própria regra invertida do prompt. Em nenhum lugar do produto
   existe um número-síntese único do filme.
2. **A perspectiva minoritária continua analisada com o mesmo rigor.** Menos
   espaço na prosa, **mesma seriedade**: sem desdém, sem ironia, sem sugerir
   que quem pensa assim está errado. Quem procura saber se vai gostar precisa
   entender o que incomodou aquela parcela — e um grupo de 1% mantém seus 6
   temas, suas barras e suas paráfrases na interface.

> **EXCEÇÃO DELIBERADA na INTERFACE (frontend, sessão "dados primeiro",
> código de UI ~v1.9.19) — o meio sai do meio-a-meio, com uma volta
> automática.** Feedback de uso apontou que o grupo `medianas` — minoritário
> em **33 dos 35** filmes do catálogo — "polui sem informar" quando recebe o
> MESMO destaque visual que negativas/positivas: o leitor decide entre
> recomendar e não recomendar, e o meio raramente é onde a decisão mora.
> `filme.html` passa a mostrar **dois** blocos em destaque (negativas,
> positivas, mesmo formato entre os dois — a neutralidade de TRATAMENTO
> continua valendo AÍ) e recolhe `medianas` numa linha discreta e
> expansível abaixo.
>
> Isto quebra, de propósito, a promessa deste §0 ("três grupos, formato
> idêntico"). **A exceção automática que impede a decisão virar
> distorção:** quando `medianas` é o grupo DOMINANTE (maior `share_real`
> dos três), ele SOBE de volta pro destaque, junto dos outros dois —
> `napoleon-2023` (45% no meio) e `friday-the-13th-2009` (41% no meio) caem
> aqui. Descrever esses dois filmes só pelos dois grupos que, somados, são
> METADE da recepção seria exatamente a infidelidade por omissão que este
> §0 foi escrito para proibir — só que pelo lado oposto do que motivou a
> v1.4.0 (lá, o filme aclamado parecia dividido; aqui, sem a exceção, o
> filme dividido pareceria bipolar quando na verdade é tripolar).
>
> **O que NÃO muda:** o DADO — coleta, classificação, lift, o bloco `eixos`
> do JSON — continua com os três buckets, sem distinção nenhuma. A exceção
> é só de onde o CSS/JS decide desenhar `medianas` em destaque; o grupo
> recolhido mantém os mesmos temas, barras e paráfrases de sempre (a
> invariante 2 acima), só atrás de um `<details>` fechado por padrão.

> **SEGUNDA EXCEÇÃO DELIBERADA na INTERFACE (frontend, v1.9.26) — o
> VOCABULÁRIO DE RÓTULO dos três grupos, e SÓ ele.** Decisão do dono do
> projeto, tomada com objetivo de **conexão geracional e uso em campanha
> de marketing**: onde a tela nomeia um grupo como RÓTULO, ela passa a
> escrever `negativas` → **HATERS**, `medianas` → **MIXED**, `positivas`
> → **FANS**.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> **O ESCOPO é o que delimita a perda, e é a metade obrigatória da
> decisão.** A exceção é de VOCABULÁRIO DE RÓTULO, restrita a onde o nome
> do grupo aparece ISOLADO, identificando a coluna:
>
> - o cabeçalho de cada bloco de bullets;
> - a legenda e a alternativa textual (`aria-label`) da barra de
>   proporção (§3[E], v1.9.26);
> - qualquer `aria-label` cuja função é dizer de qual grupo é o elemento;
> - qualquer lugar da home onde o grupo seja nomeado como rótulo (hoje:
>   nenhum — a home não nomeia grupo nenhum).
>
> **A PROSA do produto permanece NEUTRA, e pelo mesmo motivo.** Quando a
> palavra aparece como adjetivo dentro de uma frase corrida, ela carrega
> o contexto da sentença e não funciona como nome próprio do grupo — e é
> na prosa que mora a afirmação sobre pessoas. Continuam em
> `positivas`/`medianas`/`negativas`, ou em redação neutra:
>
> - o texto do VEREDITO (§3[V]), inclusive o prefixo de bucket dominante
>   montado em CÓDIGO ("O meio-termo é o maior grupo da recepção (~45%
>   das notas)") — este é prosa determinística e é **proibido trocar**;
> - o texto da NARRATIVA e a `observacao_geral` de cada grupo;
> - os avisos curtos dentro do bloco do grupo ("modo reduzido", "sem
>   análise temática") — são frase, não rótulo, e o cabeçalho logo acima
>   já identificou o grupo;
> - o disclaimer da cota.
>
> **A NEUTRALIDADE ESTRUTURAL DESTE §0 NÃO É AFETADA e continua
> integralmente em vigor.** A exceção não toca em nada do que este
> parágrafo governa de verdade: a **cota 40/40/40** continua literal, a
> **mesma margem de lift** (§2.5) vale para os dois lados, e negativas e
> positivas continuam com **o mesmo leiaute, o mesmo espaço estrutural e
> a mesma quantidade de bullets** — 6 e 6 nos 35 filmes do catálogo,
> conferido depois da mudança. Trocar a etiqueta de uma coluna não move
> um único número, um único bullet nem um único pixel de estrutura.
>
> **O DADO não muda em nada.** `negativas`/`medianas`/`positivas`
> continuam sendo as chaves do JSON, do briefing, dos prompts, dos
> validadores, desta spec e dos testes. Nenhum arquivo de `resultado/`
> foi tocado; nenhum filme foi regerado. A troca vive num mapa do
> frontend (`GRUPO_LABEL`, `frontend/js/filme.js`) e em nenhum outro
> lugar.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> **A ORDEM DE LEITURA DOS BLOCOS PASSA A SEGUIR O PESO (v1.9.30) — e isto
> NÃO é uma terceira exceção a este §0.** É o contrário: é o §0 sendo
> aplicado a uma dimensão da tela em que ele estava sendo ignorado.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> **A regra: os blocos em destaque são ordenados por `share_real`, do maior
> para o menor.** Medido no catálogo: em `cats-2019` (86 / 7 / 7) o primeiro
> bloco é HATERS; em `the-godfather` (2 / 5 / 93) é FANS.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> **EMPATE: a ordem canônica do produto** (negativas → medianas →
> positivas), como critério de desempate explícito no código, e não como
> efeito colateral da estabilidade do `sort` do runtime. O mesmo filme
> renderiza sempre na mesma ordem. Nenhum dos 35 empata hoje entre grupos em
> destaque; a regra existe para o filme que ainda não foi publicado.
>
> **A BARRA DE PROPORÇÃO NÃO É REORDENADA**, e a razão é de significado, não
> de esforço: a ordem dela é **semântica**, um eixo ordinal de 0,5★ a 5★.
> Ver §3[E].
>
> **O DADO não muda em nada.** Nenhum arquivo de `resultado/` foi tocado por
> esta regra; nenhum filme foi regerado. Ela vive numa função de
> `frontend/js/filme.js` (`ordenarPorPeso`) e em nenhum outro lugar.

> **A MARGEM DE CONTRASTE PASSA A DEPENDER DE `n` (v1.9.34) — e isto NÃO é uma
> terceira exceção a este §0. É o §0 aplicado a uma dimensão em que ele estava
> sendo ignorado**, exatamente como a ordenação por peso da v1.9.30.
>
> **O ESCOPO, primeiro, porque ele resolve metade da pergunta.** Este §0 governa
> a neutralidade entre os TRÊS GRUPOS **dentro** de um filme: cota 40/40/40,
> mesma estrutura, mesmo espaço, mesma margem para os dois lados. Ele nunca
> falou sobre neutralidade **entre filmes**. A lei por `n` (§2.5) **não toca em
> nada que este parágrafo governa**: dentro de cada filme os três buckets são
> julgados pelo MESMO limiar, com a mesma métrica e o mesmo denominador. Não
> existe caminho pelo qual `negativas` receba um limiar e `positivas` outro — e
> há teste travando isso (`tests/test_eixos.py`).
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO" · `PROTOCOLO.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO" · `ABERTO.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

---
**Objetivo:** dado o nome de um filme, agregar reviews de usuários do Letterboxd em três buckets por nota e produzir, via LLM, uma síntese temática de cada bucket — pontos recorrentes com frequência — permitindo entender a recepção do filme sem viés de leitura seletiva e sem spoilers.

**Público-alvo:** pessoa que ainda NÃO assistiu ao filme. Toda decisão de design que envolva trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler.

---

## 1. Escopo v1

**Dentro:** CLI/script local; fonte única Letterboxd; três buckets com cota por nível de nota; busca de texto completo de reviews truncadas; cache em disco; saída estruturada JSON + render em texto no terminal.

**Fora (explicitamente):** UI web, FastAPI, deploy, IMDB como fallback, reviews sem nota, múltiplos idiomas de saída (saída em pt-BR, reviews de entrada em qualquer idioma).

---

## 2. Parâmetros congelados

> **v1.9.0 — "congelado" deixou de significar "hardcoded".** Metade desta
> tabela descreve decisões de **ANÁLISE** (fronteira, cota, filtro, piso) que
> até a v1.8.2 eram aplicadas **durante a coleta** e ficavam gravadas no
> material coletado. Elas continuam congeladas no sentido de "não se muda sem
> bump de versão", mas passam a ser **parâmetros aplicados downstream**, sobre
> um bruto persistido que não sabe nada sobre elas (§3[B']). A coluna "Camada"
> diz onde cada parâmetro atua: `coleta` (afeta o que é raspado e persistido —
> mudar exige recoletar) ou `análise` (aplicado sobre o bruto — mudar exige só
> re-rodar a seleção).

| Parâmetro | Valor | Camada | Origem |
|---|---|---|---|
| **Fronteiras de bucket** | **Negativas 0,5–2,0 · Mornos 2,5–3,0 · Positivas 3,5–5,0** | análise | **v1.9.0 — opção C (§2.2)** |
| ~~Cota de reviews válidas POR NÍVEL de nota (10)~~ | **REMOVIDA na v1.9.0** — substituída por alocação proporcional (§3[C1]) | — | v1.1.0, revogada v1.9.0 |
| **Cota de análise por bucket** | **40 · 40 · 40** | análise | **v1.9.0 — profundidade igual, literal (§0)** |
| **Alocação dentro do bucket** | proporcional ao histograma, `n(L) = max(piso_nivel, round(N × c_L / C_bucket))` | análise | **v1.9.0 (§3[C1])** |
| **Piso de alocação por nível** | **2** (só para níveis com material no histograma) | análise | **v1.9.0 — ARBITRÁRIO, calibrável** |
| **Piso de análise por bucket** | **escalonado, 4 estados** (≥15 · 8–14 · 3–7 · <3) | análise | **v1.9.0 — limiares ARBITRÁRIOS (§3[C3])** |
| Filtro de comprimento (padrão) | ≥ 150 chars | análise | Decisão de design |
| Relaxamento em cascata (por nível) | 150 → 50 → sem filtro | análise | Decisão de design |
| **Folga do alvo de coleta** | **× 1,25** sobre a cota alocada — usada SÓ para o orçamento de completamento [C'] desde a v1.9.2 (§3[B]) | coleta | **v1.9.0**, escopo reduzido v1.9.2 |
| ~~Piso de páginas por nível (gate do ALVO)~~ | **REVOGADO na v1.9.2** — só existia para condicionar a parada por ALVO, que foi removida; a reversibilidade (§2.2) já é garantida pelo piso da alocação de páginas (`orcamento_paginas_bucket`), não por esta constante | — | v1.9.0, revogado v1.9.2 |
| ~~Parada por ALVO (cota × folga, heurística)~~ | **REMOVIDA na v1.9.2** — causava não-determinismo sob orçamento fixo (foi a causa do 37/40 residual de `cidade-de-deus` na v1.9.1); o orçamento de páginas passa a ser sempre gasto integralmente | coleta | v1.9.0, revogada v1.9.2 (§3[B]) |
| ~~Teto de paginação por nível de nota (4 páginas)~~ | **REVOGADO na v1.9.1** — o teto passou a ser por BUCKET, não por nível (defeito estrutural registrado na v1.9.0) | — | v1.9.0, revogado v1.9.1 |
| **Orçamento de páginas por BUCKET** | **16 páginas** (~192 reviews brutas), distribuídas entre os níveis do bucket proporcional ao histograma | coleta | **v1.9.1 (§3[B])** |
| **Teto de EXTENSÃO por bucket** | **24 páginas** (= base 16 + até 8 extras, +50%) — só é alcançado por bucket que fecha o orçamento base ABAIXO da meta com folga; bucket que fecha a meta na base para em 16, como sempre | coleta | **v1.9.4 (§3[B])** |
| **Teto de segurança por nível** | **10 páginas** — nenhum nível sozinho consome o orçamento inteiro do bucket | coleta | **v1.9.1 (§3[B])** |
| **Reserva de profundidade** | **25%** do orçamento de cada nível — a FRAÇÃO não muda na v1.9.5; muda onde as páginas caem | coleta | **v1.9.2 (§3[B])** |
| **Frações de profundidade** | **25% · 50% · 75% · 95%** da profundidade REAL do nível — a âncora das posições profundas desde a v1.9.5 (era progressão geométrica a partir do fim do bloco raso) | coleta | **v1.9.5 (§3[B])** |
| **Escada da sondagem de profundidade** | **4 · 16 · 64 · 256** páginas, + até 3 passos de refinamento binário | coleta | **v1.9.5 (§3[B])** |
| **Teto de plataforma** | **256 páginas** — medido na v1.9.2 (§3[B]) e usado como teto da profundidade estimada | coleta | **v1.9.5** |
| **Texto truncado enviado ao LLM** | **PROIBIDO — texto completo obrigatório ou descarte** | ambas | **v1.1.0 — decisão do usuário** |
| Delay entre requisições | ≥ 2s, sem paralelismo | coleta | Fase 0: anti-bot presente |
| **Ordenação da listagem** | **`by/added`** (cronológica, mais recentes primeiro) | coleta | **v1.9.0 (§2.3)** — era `by/activity` |
| Reviews sem nota | Não coletadas (a URL já é por nível) | coleta | Decisão de design |
| Reviews com flag de spoiler | **Persistidas no bruto, excluídas na seleção** | análise | **v1.9.0** — era "descartadas na coleta" |

#### O que "ARBITRÁRIO" significa nesta spec — a definição, num lugar só

**Esta é a definição canônica do rótulo. Todo lugar que escreve "limiar
ARBITRÁRIO" aponta para cá, e nenhum outro lugar a redefine.**

Um parâmetro rotulado **ARBITRÁRIO** é aquele em que:

1. **a ORDEM DE GRANDEZA é defensável e o CORTE EXATO não é.** Há razão
   registrada para o valor estar na casa em que está, e nenhuma para ele ser
   aquele número e não o vizinho. `n ≥ 15` para `completa` é defensável porque
   a ±34pp de intervalo a 95% (`n = 8`) um quantificador verbal é indefensável;
   15 contra 14 ou 16 não é;
2. **não existe evidência empírica que o FIXE.** Ele não saiu de calibração
   contra gabarito nem de nulo — se tivesse saído, seria um parâmetro medido, e
   o rótulo não se aplicaria (a lei por `n` de §2.5 é o contraexemplo: a
   constante 144,4 é `média(q95·√n)` do nulo do máximo, e **não** é arbitrária);
3. **ele é CONFIG, nunca constante enterrada** — vive num lugar único e
   nomeado, e mudá-lo é uma edição de uma linha, sem varredura;
4. **ele é CALIBRÁVEL sem mudança de desenho.** Trocá-lo move onde o corte cai,
   nunca o que o mecanismo faz — então recalibrar não exige reabrir a decisão
   que criou o mecanismo.

**A consequência prática, e é ela que o rótulo compra:** um número
ARBITRÁRIO **não é evidência de nada** e não pode ser citado como se fosse.
Quem o encontrar numa medição futura e quiser mexer nele está autorizado pelo
próprio rótulo — o que ele precisa é de dado, não de permissão.

**Os parâmetros que carregam o rótulo hoje:** `piso_nivel = 2` (§3[C1]), os
limiares do piso escalonado `3 · 8 · 15` (§3[C3]), `LIMIAR_PASSADA_ANTIGA = 20`
(§2.3), a fração `70/30` da proposta temporal S2 (§3[C2], não aplicada) e os
limiares de `marcacao_perspectiva` `dominante/3` e `dominante/10` (§D2).

*(Correção de registro, 2026-09-04: até esta data a política era invocada em
três lugares — §2.3, §3[C2] e §3[C3] — que se referiam **uns aos outros** em
círculo, e em nenhum deles ela estava enunciada. Quem seguisse qualquer um dos
três ponteiros chegava a outro ponteiro. O texto acima é o enunciado que
faltava; as três ocorrências passam a apontar para cá.)*

### 2.1 Parâmetros técnicos congelados (Fase 0)

| Item | Valor |
|---|---|
| URL de coleta | `letterboxd.com/film/<slug>/reviews/rated/<N>/<ordenacao>/[page/<n>/]` — `<ordenacao>` é PARÂMETRO (§2.3), default `by/added` |
| Formato de nota na URL | **Decimal**: `0.5, 1, 1.5 … 5` (nunca o glifo `½`) |
| **Página além da última** | **Validado (Fase 1):** retorna **200 com lista de reviews vazia** — esse é o sinal de parada da paginação, não erro/redirect |
| Endpoint de texto completo | **Validado (Fase 1):** `letterboxd.com/s/full-text/viewing:<id>/`, retorna fragmento HTML (`<p>` sem wrapper) |
| **Endpoint de busca de slug** | **Validado (Fase 1):** `letterboxd.com/s/search/films/<query>/` (AJAX, server-rendered). A URL humana `letterboxd.com/search/films/<query>/` é só um shell React — resultados vêm vazios no HTML estático dela |
| **Dedup / cache por review** | **Validado (Fase 1):** `p[data-likeable-identifier]` → JSON `uid` = `viewing:<id>`. Universal (presente em toda review); NÃO usar `data-full-text-url` para isso — ele falta em alguns casos |
| Container de review | `article.production-viewing` (fallback: `li.film-detail`) |
| Corpo do texto | `.body-text` / `.js-review-body` |
| Nota | `span.inline-rating`, parsing `count("★") + (0.5 se "½")` (fallback: `span.rating` classe `rated-N`, N = estrelas×2) |
| Spoiler | **Corrigido (Fase 1 / v1.1.1):** placeholder de texto **exato** `"This review may contain spoilers. I can handle the truth."` no corpo. Não usar substring genérica ("may contain spoilers" sozinho tem falso positivo em prosa legítima). **Ressalva:** se o Letterboxd localizar essa string para outros idiomas, o detector quebra silenciosamente — nenhum teste automatizado cobre esse cenário (ver `docs/arquivo-de-estudos/coleta/FASE1_INCOGNITAS.md`) |
| Headers | User-Agent de navegador + `Accept`, `Referer`, `Upgrade-Insecure-Requests`, `Sec-Fetch-*`, `Sec-Ch-Ua` |
| `Accept-Encoding` | **`gzip, deflate` apenas** (nunca `br` sem lib brotli instalada) |
| Plano B anti-bot (não ativar sem necessidade) | `curl_cffi` com `impersonate="chrome"`, mesmo delay |
| **Config LLM da PROSA (v1.6.0)** — narrador §D2, veredito §3[V], condições §0 *(o editor §E2 também usava esta config até ser **aposentado na v1.9.10**)* | `thinking_budget=4096` (FIXO) · `max_output_tokens=16000` |
| **Config LLM da SÍNTESE (§D)** — inalterada | `thinking_budget=0` · `max_output_tokens=3000` |

---

## 2.2 Fronteiras de bucket — CONFIGURAÇÃO, não constante (v1.9.0)

**A regra estrutural, e ela é a razão de ser desta versão:** as fronteiras
**não podem estar hardcoded em nenhum ponto do código**. Elas vivem num único
lugar (`FRONTEIRAS`, em `buckets.py`), e o mapeamento nível→bucket é uma
**função pura testável** (`bucket_de_nivel`). Todo o resto — a lista de níveis
de cada bucket, os intervalos escritos nos prompts, a agregação do histograma,
a alocação, a seleção — é **derivado** dessa configuração, nunca redigitado.
A prova de que é parâmetro e não constante é um teste que roda o mapeamento
sob fronteiras **alternativas** e confere que tudo acompanha.

**Fronteiras em vigor — opção C.** Semântica: *não recomendam / mornos /
recomendam*.

| Bucket | Faixa | Níveis | Antes (v1.8.2) |
|---|---|---|---|
| `negativas` | **0,5–2,0★** | 4 | 0,5–2,5★ (5) |
| `medianas` (mornos) | **2,5–3,0★** | 2 | 3,0–3,5★ (2) |
| `positivas` | **3,5–5,0★** | 4 | 4,0–5,0★ (3) |

Duas mudanças: **2,5★ sai de negativas e entra em mornos**; **3,5★ sai de
mornos e entra em positivas**. O nome interno do bucket do meio continua
`medianas` (é chave de JSON consumida pelo frontend e pelo narrador — renomear
seria churn fora do escopo desta versão); a **semântica** documentada é
"mornos".

**Por que:** 2,5★ é o ponto médio exato da escala do Letterboxd e ler o meio da
escala como "não recomenda" é uma escolha, não um dado; e 3,5★ é, na prática
observada, uma nota de recomendação com ressalva — tratá-la como morna
subestimava sistematicamente a recepção positiva. A fronteira nova alinha o
corte à pergunta que o produto responde ("vale assistir?"), em vez de à
aritmética da escala.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Consequência medida — os shares publicados MUDAM")*

**Risco 3 — a fronteira pode estar errada.** É uma decisão semântica sem
ground truth. 2,5★ pode ser, para parte do público, uma não-recomendação.
*Mitigação, e é a principal:* **a fronteira deixou de ser cara de trocar.** O
bruto persistido (§3[B']) não sabe onde ficam as fronteiras — guarda reviews
etiquetadas por **nível de estrela**, que é dado do Letterboxd, não decisão
nossa. Trocar a fronteira é editar `FRONTEIRAS` e re-rodar a **seleção**, com
**zero requisições de rede**. O que antes custava uma recoleta completa hoje
custa um re-run offline. Reforçando essa garantia, a condição de parada da
coleta tem um **piso de 1 página por nível sempre que houver material** (§3[B]),
**mesmo para níveis cuja alocação é zero** — é o seguro de reversibilidade:
garante que o bruto sempre contenha material de todos os 10 níveis, para que
qualquer fronteira futura tenha o que reavaliar.

---

## 2.3 Ordenação da listagem — parâmetro de amostragem (v1.9.0)

A ordem em que o Letterboxd lista as reviews de um nível **é um parâmetro de
amostragem**, não um detalhe de URL: só as primeiras `N` páginas são lidas, e a
ordenação decide *quais* reviews caem nessa janela. Até a v1.8.2 ela estava
congelada em `by/activity` e não era registrada em lugar nenhum do material
coletado — não dava para saber, olhando um dado antigo, sob qual amostragem
ele foi obtido. A partir da v1.9.0 é **configuração**, e é **gravada no
`meta.json` do bruto** (`ordenacao_usada`).

**Menu real do Letterboxd** (lido do HTML de `/film/<slug>/reviews/rated/<N>/`,
grupo "Sort by"; três opções, confirmadas ao vivo em `cure`, nível 4★):

| Chave | Segmento de URL | Rótulo no site | Comportamento medido (datas das 6 primeiras reviews) |
|---|---|---|---|
| **`mais_recentes`** | **`by/added`** | Newest First | `2026-08-07 … 2026-08-06` — **estritamente decrescente** |
| `mais_antigas` | `by/added-earliest` | Earliest First | `2012-11-10 … 2014-03-16` — estritamente crescente |
| `atividade` | `by/activity` | Review Activity | `2023-02-15, 2020-10-22, 2024-04-04, 2022-10-23, 2021-10-09, 2025-11-21` — **sem ordem temporal** |

**Default novo: `by/added` (`mais_recentes`).** É a opção mais próxima de
cronológica e a que **não carrega sinal de engajamento**. `by/activity` ordena
por atividade recente na review (curtidas, comentários) — as datas medidas
acima, espalhadas por seis anos sem ordem, são a prova de que o critério é
engajamento e não tempo; e engajamento enviesa para review longa, escrita com
intenção de ser lida, e promovida pela comunidade. Esse é precisamente o viés
que a amostra não deve ter.

**Por que não `by/added-earliest`**, que é igualmente cronológica: para um
filme com centenas de milhares de reviews, as primeiras páginas por
"Earliest First" vêm todas da janela de lançamento (no `cure`, de 2012-2014) —
um recorte de coorte severo (público de festival / primeiros adeptos), pior
como amostra da recepção do que o recorte recente.

**Correção de registro:** a v1.0.0 justificou `by/activity` como quem "mitiga
viés de *popularity* e review-piada" (§2, Fase 0). O menu real do site não
oferece uma ordenação "popularity" separada — as três opções são as da tabela
acima, e `by/activity` **é** a ordenada por engajamento. A justificativa
original não se sustenta contra o HTML observado, e está corrigida aqui.

**Ressalva honesta:** trocar `by/activity` por `by/added` troca um viés
(engajamento) por outro (recência). Não existe amostragem neutra dentro deste
menu — existe amostragem **declarada**. O ganho desta versão é que a escolha
virou parâmetro visível e gravado, não uma constante enterrada numa URL.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "O tamanho MEDIDO do viés de recência (recoleta de 2026-08-07)")*

#### A passada SELETIVA sob `by/added-earliest` (v1.9.6)

O candidato registrado acima ("amostragem estratificada por período") deixa de
ser candidato. A v1.9.5 mediu por que ele é o **único** lever disponível: sob
`by/added`, a mediana do catálogo precisa de **1783 páginas** para cobrir um
ano, contra um teto de plataforma de **256** (§3[B], "Achado que refuta"). As
256 páginas expostas são as ~3000 adições mais recentes — nenhum orçamento,
nenhuma âncora e nenhum desenho de seleção alcança o passado por posição. A
ordenação alcança: `by/added-earliest` devolve a listagem estritamente
crescente desde 2012 (tabela do menu, acima).

**Ela é SELETIVA, e a seletividade é o ponto.** A mesma medição separou duas
populações pelo `dias_por_100_paginas` (§3[B']): `friday-the-13th-2009` cobre
163,6 dias a cada 100 páginas e sequer sai da página ~14; `avengers-endgame`
cobre 0,8. Para o primeiro, a profundidade sob `by/added` **já** entrega anos
de recepção, e uma passada por ordenação gastaria requisição comprando
cobertura que já existe. Para o segundo, 256 páginas são questão de dias.

```
recebe passada  ⇔  dias_por_100_paginas < LIMIAR_PASSADA_ANTIGA (= 20)
```

**Por que 20 e não outro número:** abaixo de 20 dias/100 páginas, o teto de 256
páginas da plataforma não cobre um ano (256 × 20/100 = 51 dias… e o filme
mediano da classe está muito abaixo disso). É o corte que responde à pergunta
"as 256 páginas que existem cobrem pelo menos um ano?" — não um quantil da
distribuição observada, que mudaria a cada filme novo no catálogo. **`LIMIAR_PASSADA_ANTIGA = 20` é um limiar ARBITRÁRIO** no sentido definido em
**§2, "O que 'ARBITRÁRIO' significa nesta spec"** — ordem de grandeza
defensável, corte exato não, config e não constante enterrada, calibrável sem
mudança de desenho.

**Orçamento da passada:** a mesma estrutura por bucket de §3[B], com uma fatia
menor — `ORCAMENTO_PAGINAS_PASSADA = 6` por bucket (~18 páginas por filme,
contra 48 da coleta base). **Sem extensão por déficit e sem sondagem de
profundidade**, e as duas exclusões têm razão: a extensão (§3[B], v1.9.4) mede
déficit contra a cota de análise, que a passada não está tentando fechar; e a
sondagem existe para ancorar o bloco PROFUNDO, que sob ordenação CRESCENTE
aponta para o material mais RECENTE — exatamente o que a coleta base já tem.
Uma passada que gastasse orçamento fundo em `by/added-earliest` compraria
duplicata.

**A passada SOMA, não substitui** — a persistência é incremental e deduplica
por `id` (§3[B']), e a chave de cache inclui a ordenação (`urls.py`, v1.9.0),
então não há risco de servir a amostra errada. As duas assimetrias que a
passada obriga a resolver estão em §3[B'] ("Duas ordenações no mesmo bruto").

**Ressalva que não some com a passada:** o material de `by/added-earliest` é
um recorte de coorte severo (público de festival / primeiros adeptos) — foi
exatamente por isso que a v1.9.0 o rejeitou como ordenação ÚNICA, e essa
rejeição continua de pé. O que muda é que ele deixa de ser *a* amostra para
ser *uma ponta* dela; quanto de cada ponta entra na análise é decisão de
SELEÇÃO (§3[C2], "Proposta temporal"), medida nesta versão e **não aplicada**.

---


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "2.4 Retentativa de rede — TRANSPORTE sim, BLOQUEIO nunca (v1.9.6)")*

**O que RETENTA** — erro de transporte, isto é, a requisição não produziu
resposta HTTP nenhuma: reset de conexão, timeout de leitura/conexão, falha de
DNS/socket. Até **3 tentativas** por requisição, com backoff exponencial
`2s · 4s · 8s` e **jitter de ±25%** (o jitter existe para que um lote inteiro
que tropece no mesmo instante não volte em uníssono). O **delay de educação
(§2.1, ≥2s) continua valendo entre todas as tentativas** — a retentativa
**soma** a ele, nunca o substitui. Custo do pior caso por requisição:
`3×delay + backoffs ≈ 6 + 14 = 20s`.

**O que NÃO retenta, e por quê** — esta é a metade da regra que importa:

| Condição | Comportamento | Razão |
|---|---|---|
| **HTTP 403** / challenge Cloudflare (`AntiBotError`) | **PARA imediatamente**, sem retentar, sem escalar | Retentar bloqueio é evasão, e a spec proíbe (§restrições). O servidor respondeu, e a resposta foi "não" |
| **HTTP 503**, 1ª ocorrência no lote | **1 retentativa**, com backoff LONGO (`ESPERA_503 = 30s`) | Sobrecarga é transitória por definição, e é o servidor pedindo espaço — esperar mais é cooperar, não insistir |
| **HTTP 503**, 2ª ocorrência no lote | **PARA o lote** (`SobrecargaError`) e reporta | A v1.9.5 foi interrompida por um 503 e essa decisão foi correta; automatizar a insistência a desfaria. Duas vezes não é ruído |
| **HTTP 404** e demais status ≠ 200 | `FetchError` na hora, sem retentar | Resposta legítima do servidor, não erro de transporte. Slug inexistente é resultado, não falha a repetir |

**O contador de 503 é do LOTE, não da requisição nem do filme** — o harness
(§3[H]) cria um `Fetcher` por filme, então o estado vive num objeto
compartilhado (`PressaoDoSite`) passado a todos eles. Sem isso, "segundo 503 do
lote" seria inexprimível: cada filme recomeçaria a contagem do zero e a spec
estaria dizendo "retenta 503 para sempre, uma vez por filme".

`SobrecargaError` **não** herda de `FetchError`, deliberadamente: as etapas
ADITIVAS do pipeline (histograma §3[G], ficha §3[F]) engolem `FetchError` para
não derrubar uma coleta cara por causa de um dado opcional, e engolir uma
parada de lote seria o oposto do que esta regra existe para garantir.

**Telemetria obrigatória por filme** (`Fetcher.telemetria_retentativa()`):
tentativas gastas em retentativa, contagem por tipo de erro, e nº de 503.
**Taxa alta de retentativa é sinal de pressão no site e precisa ser VISÍVEL**
— o modo de falha desta versão seria absorver em silêncio a degradação que a
v1.9.5 conseguiu ver justamente porque o `Fetcher` quebrava.

---

## 2.5 Eixos, lift e margem de contraste — a régua do Ponto 2 (v1.9.14)

Fecha o Ponto 2 do projeto: os bullets de cada grupo deixam de ser três
listas livres, independentes entre si, e passam a ser organizados por uma
**taxonomia FECHADA de 10 eixos**. A promessa estrutural é o alinhamento POR
LINHA — com eixo fixo, os três grupos ficam comparáveis célula a célula, em
vez de exigir do leitor a reconciliação mental de três listas soltas.

`ritmo` · `atuacao` · `direcao_imagem` · `roteiro_estrutura` · `som_trilha` ·
`tom_atmosfera` · `impacto_emocional` · `comparacoes` · `expectativa` ·
`critica_social`, mais `livre` para o que não couber.

`taxonomia_id` corrente: **`ebab2667de74`** (hash do prompt de classificação
+ da lista de eixos). A classificação dos 35 filmes está em
`resultado/votacao-3/consenso.jsonl`, por votação de 3 passadas
independentes (eixo entra no consenso se aparece em ≥2 de 3). A fase inteira
de medição que produziu essa régua está consolidada em
`docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md`; esta seção registra só o que virou
PARÂMETRO.

### `taxonomia_id` no veredito não é burocracia

Todo veredito de contraste carrega o `taxonomia_id` sob o qual foi
calculado. **Um filme classificado como sem contraste sob uma taxonomia pode
deixar de sê-lo sob a seguinte** — aconteceu com `barbie`: sob a taxonomia
anterior o contraste vinha de `impacto_emocional` (22,5pp); sob
`ebab2667de74` esse eixo saturou (0,0pp, 65/70/70% nos três grupos) e o
contraste MIGROU para `critica_social` (20,0pp, gradiente limpo 82,5%→47,5%
do bucket negativo ao positivo).

O estado descreve **o que a régua atual enxerga**, não uma propriedade do
filme. Sem o `taxonomia_id` ao lado, `contraste: valorativo` seria lido como
afirmação sobre a obra, e a próxima régua o desmentiria em silêncio.

### Lift — a definição, e por que ABSOLUTO

```
lift(eixo, bucket) = freq(eixo, bucket) − max( freq(eixo, outros dois buckets) )
```

Frequência é sempre `n_reviews_do_bucket_com_o_eixo / n_reviews_classificadas_do_bucket`
— fração com denominador visível, como toda frequência deste projeto.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "Lift — a definição, e por que ABSOLUTO")*

### A MARGEM — a lei por `n` (v1.9.34). **Este é o parâmetro em vigor.**

```
limiar(n) = 144,4 / √n   pontos percentuais       n = o MENOR dos três buckets
```

**A comparação é EXATA, na forma quadrada que elimina a raiz.** `144,4/√n` é
irracional e comparar em float jogaria fora a garantia que a v1.9.15 comprou
caro (*"nenhuma decisão de estado depende de arredondamento de float"* — cinco
filmes já caíram fora da margem uma vez por isso). Para `lift > 0`:

```
lift >= (1444/1000)/√n      ⟺      lift² · n  >=  Fraction(2085136, 1000000)
```

`lift` é `Fraction` de 0 a 1 (não pontos percentuais: 144,4pp de constante é
1,444 nessa escala), `n` é `int`, e `lift² · n >= Fraction(2085136, 1000000)` é
uma comparação de racionais **exata** — sem raiz, sem float, sem tabela de
arredondamento. **Conferido: a forma exata devolve exatamente os mesmos 6 filmes
que a aritmética de alta precisão.**

> **A GUARDA DE SINAL `lift > 0` É PARTE DA LEI, NÃO OTIMIZAÇÃO — e quem for
> "simplificar" a expressão precisa esbarrar nisto.** Elevar ao quadrado
> **apaga o sinal** e só é monotônico no ramo positivo. Sem a guarda, um lift de
> **−0,5** com n = 40 daria `0,25 · 40 = 10 >= 2,085136` — **APROVADO**. E −0,5
> de lift significa que o eixo é 50pp MENOS falado naquele grupo que no
> concorrente: o produto publicaria "este é o assunto próprio deste grupo"
> sobre o assunto que o grupo é o que MENOS toca. Não é um erro de borda, é a
> afirmação exatamente invertida, e ela passaria em qualquer teste que só
> exercitasse lifts positivos.
>
> Isto estava **latente na formulação da lei** quando ela foi aprovada — a
> equivalência `lift >= k/√n ⟺ lift² · n >= k²` só vale sob `lift > 0`, e a
> condição não estava escrita. Fica escrita agora, com teste nomeado
> (`test_lift_nao_positivo_reprova_sempre`).
>
> **A ordem importa:** `lift <= 0` reprova **por inspeção, ANTES** da
> multiplicação. Não é o mesmo que checar depois.

**PISO — `n < 10` no menor bucket: o estado `contraste` NÃO É PUBLICADO.** Não
é `valorativo`: é **ausente**, no mesmo estatuto de `montar_bloco` devolver
`None` sem classificação — **chave ausente distingue "não medido" de "medido e
sem contraste"**. Publicar `valorativo` ali seria trocar uma afirmação sem
lastro por outra: naquele `n` a medição não distingue os dois estados, e dizer
"os grupos falam das mesmas coisas" é tão sem base quanto dizer o contrário.
Afeta **1 filme hoje** (`obsession-2026`, n = 5/6/8, cujo estado tem
**P(ruído) = 0,976**); o piso entra na versão completa, e não como exceção
nomeada, porque a expansão de catálogo trará mais filmes com bucket pequeno.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "A MARGEM — a lei por `n` (v1.9.34). **Este é o parâmetro em vigor.**")*

#### A linha que explica a AUSÊNCIA de veredito (v1.9.34)

Sem `contraste`, a chave `veredito` **some do JSON** — estatuto aditivo de
`ficha` (§3[F]) e `distribuicao` (§3[G]). Mas a página **não fica em silêncio**,
pelo mesmo argumento que este §2.5 já usou para a ausência de bullets de
contraste: *"se ficar como AUSÊNCIA, vai parecer bug ao leitor"*. Na posição do
veredito entra, gerada por **CÓDIGO**, determinística, **zero LLM**:

> **"A amostra analisada deste filme é pequena demais para dizer se os grupos
> falam de coisas diferentes ou se falam das mesmas coisas e divergem no
> julgamento."**

**Ela NÃO é um veredito** — é a explicação de por que não há um —, e o
tratamento visual a distingue de um (classe própria, não `.verdict`).

**Por que esta frase e não outra, em três invariantes:**

1. **Ancorada na BASE, nunca na MAGNITUDE.** É exatamente a exceção que a
   v1.9.22 preservou ao proibir deflação: hedge sobre *"a amostra analisada"* é
   legítimo; hedge que encolhe a quantidade (*"relatos pontuais…"*) é
   falsidade. A frase fala do denominador, não do achado.
2. **Zero algarismo** (v1.9.20) e **zero quantificador de magnitude** (v1.9.22).
3. **Os DOIS estados aparecem no mesmo nível** — "falam de coisas diferentes"
   e "falam das mesmas coisas e divergem no julgamento", por extenso, nenhum
   reduzido a resíduo do outro. **É a neutralidade do §0 aplicada à frase que
   explica por que não há estado:** discordar sobre o mesmo assunto é achado de
   primeira classe neste produto (é o que 29 dos 35 filmes publicam), e uma
   redação como *"ou apenas discordam"* rebaixaria em prosa o estado que o
   resto do produto trata como primeira classe. Protegida por teste nomeado.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "O limiar por `n`, e a taxa que ele realiza" · `PROTOCOLO.md` — "O critério "cerca de um terço do catálogo" está APOSENTADO")*

**O critério que entra no lugar é de ERRO, não de cobertura:** o limiar é o que
mantém a taxa de falso contraste em nível declarado (≈5%), e o número de filmes
`tematico` é **consequência**, não alvo. Sob a lei, o catálogo é **6 `tematico`
/ 28 `valorativo` / 1 sem estado publicado** — e 6/35 não é um defeito a corrigir
afrouxando a lei.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "α = 0,05 e não 0,10 — a razão é assimetria de dano")*

**O cálculo NÃO usa ponto flutuante.** Frequência e lift são frações exatas
(`Fraction`) sobre contagens inteiras, e a margem é `Fraction(20, 100)`,
comparada com `>=` também em `Fraction`. É o mesmo compromisso da v1.9.14
(nenhuma decisão de estado depende de arredondamento de float) com a
fronteira corrigida para a que a medição sempre pretendeu produzir.

### Seleção de bullets — 2 de FREQUÊNCIA + 3 de LIFT

Os bullets de cada bucket deixam de ser "os 6 temas que o LLM devolveu,
ordenados por menção" e passam a ser escolhidos em CÓDIGO, sobre os eixos:

- **2 bullets de maior FREQUÊNCIA** — o que o grupo mais fala. É o eixo de
  CONSENSO, e ele entra mesmo quando os outros grupos falam tanto quanto:
  frequência alta sem lift não é ruído, é o assunto do filme.
- **3 bullets de maior LIFT** — o que **só** esse grupo fala. É o eixo de
  CONTRASTE, e aqui a margem de 20pp vale: eixo com lift abaixo dela **não
  entra**, e a lista fica mais curta em vez de completada com ruído.

Um eixo já escolhido por frequência não é escolhido de novo por lift — a
lista tem no máximo 5 entradas e no mínimo 2, e o número de entradas é
informação, não defeito de preenchimento. Empate é desfeito pela ordem
canônica dos eixos, para que dois filmes com o mesmo perfil não saiam em
ordens diferentes por acidente de iteração.

**Por que os dois critérios, e não só o lift.** Uma lista só de contraste
seria vazia em 22 dos 35 filmes (§2.5) e, nos outros 13, esconderia do
leitor o assunto principal do grupo. Uma lista só de frequência é o que
existia antes, e não responde a pergunta que o produto faz — *no que estes
grupos discordam?*. Os dois lados vêm rotulados como o que são, nunca
misturados numa lista única sem etiqueta.

### Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34)

**Os três casos, e o terceiro é novo:**

| `n` do menor bucket | condição | `contraste` |
|---|---|---|
| ≥ 10 | alguma das 30 células atinge `limiar(n)` | `"tematico"` |
| ≥ 10 | nenhuma atinge | `"valorativo"` |
| **< 10** | — | **chave AUSENTE do bloco `eixos`** |

**Ausente não é um terceiro VALOR; é a ausência da chave**, no mesmo estatuto
do bloco `eixos` inteiro quando não há classificação. Um consumidor que faça
`eixos.get("contraste") == "valorativo"` continua correto; um que faça
`eixos["contraste"]` quebra, e deve quebrar. **A regra para todo consumidor:
ausência significa "não medido", nunca "medido e sem contraste".** O resto do
bloco `eixos` (linhas, frequências, lifts, bullets) **continua sendo publicado
normalmente** — o que falta é só a decisão binária, porque é ela que o `n` não
sustenta.

Contagem atual do catálogo sob a lei da v1.9.34: **6 `tematico`, 28
`valorativo`, 1 sem estado** (`obsession-2026`) — **6 + 28 + 1 = 35**.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34)" · `PROTOCOLO.md` — "Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34)")*

O eixo **entra assim mesmo**, com esta limitação declarada, e não escondido:
removê-lo do schema apagaria um eixo que o público de fato usa, e as três
tentativas de conserto estão medidas e registradas como refutadas — não como
pendências.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "`impacto_emocional` entra no schema COM a limitação registrada"; "Confiabilidade medida da leitura por modelo sob P1–P7 — NÃO tem direção fixa"; … · `PROTOCOLO.md` — "2.7 AVISO — o gabarito de contagem à mão dos 5 casos SUBESTIMA (2026-08-30)"; "Achado novo — o modelo nunca usa "não sei julgar", mesmo devendo"; …)*

## 3. Pipeline

```
input (nome do filme)
  → [A] resolução de slug
  → [G] distribuição real de notas — histograma (v1.4.0; PROMOVIDO na v1.9.0)
  ══ COLETA ══ (não sabe nada de fronteira, cota ou filtro)
  → [C1] alocação proporcional ao histograma (v1.9.0 — define o alvo por nível)
  → [B]  raspagem do SUPERSET por nível de nota (com cache)
  → [C'] completamento de reviews truncadas
  → [B'] PERSISTÊNCIA do bruto em dados/bruto/<slug>/ (v1.9.0)
  ══ ANÁLISE ══ (lê o bruto persistido; zero rede)
  → [C2] seleção 40/40/40: fronteiras + filtros + cascata como PARÂMETROS
  → [C3] piso escalonado (4 estados)
  → [D] síntese LLM por bucket
  → [D3] rotulagem de temas por EIXO (v1.9.14; só com classificação do slug)
  → [D2] narrador (opcional, --tom; lê [G] se existir)
  → [F] ficha do filme via TMDB (aditiva, independente de D/D2 — v1.3.0)
  → [E] render (JSON + terminal)

  ══ PUBLICAÇÃO ══ (harness à parte, NÃO roda dentro do cli — ver abaixo)
  → [V] veredito (v1.9.21, scripts/gerar_veredito.py; depende de [D3])
  → [Cond] condições de decisão (v1.9.35, scripts/gerar_condicoes.py +
           scripts/publicar_condicoes.py; NÃO depende de [D3]/eixos)
```

**Correção de registro (2026-09-04): este diagrama estava desatualizado em
quatro pontos, e foi conferido contra o código antes de ser reescrito.**
Ele listava `[E2] editor — … --no-edicao pula`, um estágio **aposentado na
v1.9.10** cuja flag não existe mais (`grep add_argument src/espectro24/cli.py`:
não há `--no-edicao` nem `--com-editor`; as constantes `EDITOR_*` saíram de
`config.py`; o código está em `experimentos-editor-e2-arquivado/editor.py`); e
**omitia** `[D3]` (v1.9.14), `[V]` (v1.9.21) e o estágio de CONDIÇÕES
(v1.9.35–37), este último com 257 condições publicadas nos 35 filmes.

**A linha `══ PUBLICAÇÃO ══` é uma fronteira real, não um enfeite de
diagrama.** `[V]` e `[Cond]` **não são chamados por `cli.py`** — conferido:
`grep -n condicoes src/espectro24/cli.py src/espectro24/pipeline.py` não
devolve nada, e `condicoes.py` é importado só por `scripts/gerar_condicoes.py`
e `scripts/publicar_condicoes.py`. Os dois rodam por harness próprio, sobre um
`resultado/<slug>.json` já em disco, escrevendo **uma única chave** cada
(`veredito`, `condicoes`) — o mesmo padrão de `scripts/enriquecer_ficha.py`
(§3[F]) e pela mesma razão: regerar a prosa de publicação não deve custar
recoleta, síntese nem classificação. Quem procurar o estágio de condições
dentro do pipeline não vai achar, e isso é o desenho.

**A linha divisória COLETA / ANÁLISE é a mudança central da v1.9.0.** Acima
dela, nada sabe onde ficam as fronteiras de bucket, qual é a cota, ou qual
filtro de comprimento vale: a coleta raspa por **nível de estrela** — que é
dado do Letterboxd — e persiste tudo. Abaixo dela, tudo é parâmetro aplicado
sobre o material já em disco. A consequência prática: **mudar fronteira, cota,
filtro ou piso não custa mais nenhuma requisição de rede.** A única coisa que
atravessa a linha na direção "análise → coleta" é a **alocação** ([C1]), e ela
atravessa apenas como *alvo de quando parar de paginar* — nunca como filtro do
que é gravado.

**[G] foi PROMOVIDO na v1.9.0** de etapa aditiva pós-coleta para **pré-requisito
da coleta**: a alocação proporcional ([C1]) precisa do histograma para calcular
o alvo por nível. **Continua sem custar requisição extra** (é o mesmo 1 request
cacheado de sempre, só que executado antes) e **continua sem bloquear**: sem
histograma, [C1] cai para alocação **uniforme** (`N_bucket ÷ nº de níveis do
bucket`), a coleta segue igual, e o resto do pipeline degrada como já degradava
(§D2 fallback). O que muda é a ordem, não a dependência.

**[F] roda em paralelo conceitual a [D]/[D2]:** não depende das reviews
coletadas nem é bloqueada por elas ([F] usa título/ano derivados do slug —
§3[F]). Uma falha em [F] nunca impede [D]/[D2]/[E] de rodar, e vice-versa: as
fontes de dados são independentes.

**[G] é a única exceção à independência total:** o narrador [D2] *lê* a
distribuição quando ela existe, para escolher a variante da regra (c). Mas a
dependência é **opcional por construção** — ausência de [G] não é erro, é o
caminho de fallback (regras da v1.2.1), e nenhum outro estágio muda.

### [A] Resolução de slug
Busca via o endpoint AJAX `letterboxd.com/s/search/films/<query>/` (**corrigido na Fase 1** — a URL humana `letterboxd.com/search/films/<query>/` é um shell React vazio no HTML estático; ver §2.1); apresentar os top resultados (título + ano) e pedir confirmação do usuário quando houver ambiguidade. Se o usuário passar o slug diretamente (flag `--slug`), pular a busca.

### [C1] Alocação proporcional ao histograma (v1.9.0) — define o alvo, não o filtro

Dentro de cada bucket, as vagas são distribuídas segundo o **histograma real
daquele filme**, em vez de cota igual por nível:

```
n(nível L) = max(piso_nivel, round(N_bucket × contagem(L) / contagem_do_bucket))
```

com `N_bucket = 40` (§2), `piso_nivel = 2` (§2, arbitrário e calibrável), e o
piso aplicado **só a níveis com material** (`contagem(L) > 0`). Níveis ausentes
do histograma recebem 0 e não quebram a conta.

**Reconciliação para somar exatamente `N_bucket`** (o arredondamento e o piso
não fecham sozinhos): distribui-se por *maior resto* e, se o piso empurrar a
soma acima de `N_bucket`, corta-se dos níveis com **maior alocação acima do
piso**, sempre do maior para o menor, com desempate determinístico pelo nível
mais alto. Caso degenerado registrado: se `nº de níveis com material × piso_nivel
> N_bucket`, o piso é impossível de honrar para todos — a alocação então
distribui `N_bucket` o mais uniformemente possível e o piso é **relaxado**, não
violado em silêncio.

**Custo: zero requisições extras.** O endpoint de histograma já é chamado uma
vez por filme desde a v1.4.0 (§3[G]); a v1.9.0 só o executa **antes** da
coleta em vez de depois.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "[C1] Alocação proporcional ao histograma (v1.9.0) — define o alvo, não o filtro")*

#### Duas ressalvas, declaradas

1. **O histograma mede NOTAS; a alocação distribui REVIEWS COM TEXTO.** São
   populações diferentes (a mesma distinção que a v1.4.1 registrou para o
   vocabulário do peso, §D2): nada garante que a proporção de quem *escreve*
   em cada nível seja a proporção de quem *avalia*. A alocação é uma
   **aproximação por proxy**, e está declarada como tal — não como medida.
   O proxy é usado porque é o único dado de forma da distribuição disponível
   sem gastar requisição, e porque é estritamente melhor que a alternativa que
   substituiu (cota igual, que é o proxy "todos os níveis são igualmente
   populosos" — falso em todo filme).
2. **A redistribuição de déficit muda a composição silenciosamente.** Quando um
   nível não completa a alocação (esgotou material ou bateu o teto de páginas),
   a sobra vai para os níveis do **mesmo bucket** com mais material disponível
   — o bucket fecha com `N` certo e composição **diferente da planejada**.
   *Mitigação obrigatória:* a telemetria registra a composição **ALVO** e a
   **ATINGIDA** por nível, **lado a lado** (§4). Um bucket que alcançou 40 por
   redistribuição não pode parecer igual a um que alcançou 40 como planejado.

**A redistribuição NUNCA aciona relaxamento na coleta.** Déficit é resolvido
puxando mais material de **outro nível do mesmo bucket**, jamais afrouxando
filtro ou paginando além do teto. Cascata de relaxamento é decisão de seleção
(§3[C2]), e continua sendo por nível.

### [B] Raspagem do SUPERSET por nível de nota

Para cada um dos 10 níveis (`rated/0.5/` … `rated/5/`), na ordenação do §2.3,
paginar e **persistir tudo o que vier** (§3[B']). Os filtros existem aqui com
uma função só: **decidir quando parar**.

**Condição de parada — dois motivos possíveis, DETERMINÍSTICA desde a v1.9.2:**

**(a) ORÇAMENTO — o orçamento de páginas do nível (derivado do orçamento por
BUCKET, ver abaixo) é sempre gasto INTEGRALMENTE**, salvo esgotamento real de
material. `motivo_parada = "orcamento_esgotado"`: o site provavelmente tem
mais conteúdo, mas o orçamento desta coleta acabou.

**(b) MATERIAL ESGOTADO — página além da última devolve 200 com lista vazia**
(§2.1). `motivo_parada = "material_esgotado"`: o nível está provadamente
completo — não há mais o que coletar ali, com QUALQUER orçamento.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "[B] Raspagem do SUPERSET por nível de nota")*

**A correção:** o teto deixa de ser uma constante fixa por nível e passa a ser
**um orçamento por BUCKET** (`ORCAMENTO_PAGINAS_POR_BUCKET = 16`, igual para os
três — não depende do número de níveis), distribuído entre os níveis daquele
bucket **na mesma proporção do histograma já usada para a alocação de reviews**
(§3[C1]) — não é uma segunda fórmula: é a função `alocar_bucket` reaproveitada,
agora recebendo o orçamento de páginas em vez da cota de reviews como `N`:

```
paginas(nível L) = alocar_bucket(orcamento_bucket=16, histograma, niveis_do_bucket, piso_nivel=1)
```

com dois ajustes sobre o resultado:

- **piso de 1 página por nível com material** — o MESMO seguro de
  reversibilidade da fronteira (§2.2, Risco 3), agora expresso na alocação de
  páginas em vez de numa constante solta;
- **teto de segurança de 10 páginas num único nível** (`TETO_SEGURANCA_PAGINAS_NIVEL
  = 10`) — sem ele, um bucket de 2 níveis muito desbalanceado no histograma
  (ex.: `medianas` de `cidade-de-deus`, onde 3,0★ tem 85% do bucket) daria a
  esse nível sozinho quase o orçamento inteiro, deixando o outro nível do
  bucket com quase nada. O excedente cortado pelo teto é **redistribuído para
  os outros níveis do mesmo bucket** — literalmente `redistribuir_deficit`
  (§3[C1]) chamada de novo, com a "disponibilidade" sendo o teto de segurança
  em vez da contagem de material: **nenhum mecanismo novo de redistribuição
  foi escrito**, o mesmo já existente é reaproveitado com um `disponivel`
  diferente.

**Garantia:** a soma de páginas nunca excede o orçamento do bucket; pode ficar
**abaixo** dele só no caso degenerado de um bucket com um único nível
(nada para redistribuir o excedente do teto de segurança) — caso raro sob a
opção C (nenhum bucket tem 1 nível só), coberto em teste por completude.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Orçamento de páginas POR BUCKET (v1.9.1) — corrige o defeito estrutural da v1.9.0")*

```
n_raso    = orçamento − n_profundo
n_profundo = round(orçamento × RESERVA_PROFUNDIDADE)     # RESERVA_PROFUNDIDADE = 0,25
```

- **bloco raso** — posições `1..n_raso`, consecutivas, igual a antes;
- **bloco profundo** — até `n_profundo` posições em **progressão geométrica**
  a partir do FIM do bloco raso: `n_raso+2, n_raso+4, n_raso+8, n_raso+16, …`
  (dobra a cada termo). Cresce rápido de propósito: com um orçamento pequeno
  de posições profundas, cobrir uma faixa ampla da profundidade real exige
  saltos grandes, não uma amostra densa perto do início do bloco raso.

**Descoberta e redistribuição, sem custo extra.** A profundidade real de um
nível não é conhecida a priori (§3[B], gate da v1.9.1: sem numeração de
página no HTML). As posições profundas são buscadas em ordem CRESCENTE de
offset; a primeira que devolver página vazia revela que a profundidade real
fica **abaixo** dela — e as posições profundas maiores, ainda não tentadas
(agora sabidamente vazias, por monotonicidade da paginação: se a página `K`
está vazia, toda página `> K` também está), NÃO são buscadas. O orçamento
que sobra dessas posições descartadas é redistribuído para dentro do
**intervalo já confirmado como válido** — todo posição `≤` à maior posição
profunda **efetivamente buscada com sucesso** (não à posição vazia, nem a
qualquer coisa além dela: só o que já foi provado ter conteúdo, por
monotonicidade na direção oposta — se a página `P` tem conteúdo, toda
página `< P` também tem). Isso garante **no máximo 1 página desperdiçada por
nível** — a que revelou a profundidade — e nenhuma aposta arriscada em
território desconhecido.

**A redistribuição REAPROVEITA `redistribuir_deficit` — não é um mecanismo
novo.** As posições candidatas (as geométricas originais + posições dentro
do intervalo confirmado ainda não buscadas) entram como o "nível" da função;
`alocacao` é o que se queria originalmente (1 por posição geométrica),
`disponivel` é 1 para toda posição dentro do intervalo confirmado e 0 para
o resto — a mesma função que já redistribui déficit de reviews entre níveis
de um bucket (§3[C1]) e déficit de páginas entre níveis (v1.9.1, acima),
agora aplicada a POSIÇÕES DENTRO de um nível. Três usos, uma implementação.

**Custo: IGUAL ao consecutivo no caso comum; NUNCA maior, em qualquer caso.**
Quando a profundidade real cobre todas as posições tentadas (o caso
DOMINANTE — é justamente o material populoso que justifica gastar reserva
profunda), o total é exatamente `n_raso + n_profundo` = o orçamento, igual
ao esquema consecutivo. **Ressalva honesta, no caso de fronteira exata:** o
backfill só usa posições JÁ CONFIRMADAS (nunca aposta em território
desconhecido, para preservar a garantia de ≤1 desperdício) — se a
profundidade real cai DENTRO de um salto geométrico ainda não coberto por
nenhuma posição confirmada (ex.: confirmado até `n_raso+2`, a profundidade
real é `n_raso+3`, mas a próxima tentativa geométrica é `n_raso+4` e vem
vazia), esse conteúdo real específico fica **fora do backfill** — o
orçamento correspondente simplesmente não é gasto nesse nível, em vez de
arriscar uma segunda página vazia para persegui-lo. **Nunca mais caro que o
consecutivo; igual sempre que há posições confirmadas suficientes para
preencher a reserva (o caso comum); pode ficar levemente ABAIXO do
consecutivo no caso de fronteira, deixando uma fração pequena e real do
conteúdo fora — aceito em troca da garantia de custo previsível.** Testado
explicitamente (`tests/test_posicionamento.py`): igualdade exata no caso
comum (profundidade folgada); nunca excede o orçamento em nenhum caso.

**Degrada para consecutivo quando o nível é raso.** Se a profundidade real
do nível é menor que `n_raso`, o bloco raso já esgota o material (página
vazia dentro dele) e o bloco profundo nunca é tentado — mesmo comportamento
de sempre, sem código especial: a checagem de esgotamento roda ANTES da fase
profunda, e material esgotado na fase rasa pula a fase profunda inteira.

**Reversibilidade — por que esta é a última peça que faltava (v1.9.2).**
Fronteira (§2.2), cota (§0) e filtro (§3[C2]) já eram parâmetros aplicados
DOWNSTREAM sobre o bruto persistido — mudar qualquer um deles não custa
requisição. A profundidade de paginação era a exceção: página não baixada
não está no bruto, e não tem como um parâmetro downstream trazê-la de volta.
Com raso e profundo no MESMO bruto, "analisar só o material recente" ou
"analisar tudo, incluindo o profundo" também vira parâmetro filtrável por
`pagina_origem` na seleção (§3[C2]) — não implementado nesta sessão (fora do
escopo: a seleção continua escolhendo por `(pagina_origem, ordem no jsonl)`,
sem filtro de profundidade), mas agora POSSÍVEL sem recoleta. Sem isto, a
janela temporal ficaria gravada no bruto de forma irreversível, e corrigi-la
exigiria recoletar os 30-50 filmes do lote inteiro depois de já publicados.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Âncora de profundidade — a progressão estava presa ao lugar errado (v1.9.5)")*

##### Sondagem de profundidade — POR FILME, não por nível

A âncora nova exige saber a profundidade real, que o HTML não informa (gate da
v1.9.1: não há numeração de página). A sondagem é **por filme**:

1. **sondar o nível mais populoso** do histograma, por escada geométrica
   (`SONDA_ESCADA = (4, 16, 64, 256)`) seguida de refinamento binário de no
   máximo `SONDA_MAX_REFINAMENTO = 3` passos, dentro do último intervalo
   `(última não-vazia, primeira vazia)`;
2. **escalar os demais níveis pela proporção do histograma** —
   `prof(L) = round(prof_sondada × hist(L) / hist(L_sondado))`, com piso 1 e
   teto `TETO_PLATAFORMA_PAGINAS = 256`.

**O passo 2 é um PROXY, e entra na spec com esse rótulo.** O histograma conta
NOTAS; a paginação conta REVIEWS COM TEXTO. É a mesma aproximação que §3[C1]
já usa para alocar vagas, e o registro é o mesmo: nada garante que a razão
texto/nota seja igual entre níveis. A defesa não é que o proxy acerte — é que
**errar sai barato**, porque o mecanismo de descoberta da v1.9.2 já trata
posição estimada que volta vazia: ela revela a profundidade real por
monotonicidade e o orçamento sobrante é redistribuído para o intervalo
confirmado, **reusando `redistribuir_deficit`**. Nenhum segundo caminho é
escrito.

**Custo:** 4 requisições no caso comum (filme popular, os quatro degraus da
escada não-vazios → profundidade = teto de plataforma, sem refinamento); até
7 no pior caso. A Sessão C já havia estabelecido os dois extremos: 256 é teto
de PLATAFORMA para listagem populosa, e filme obscuro esgota organicamente
muito antes (`the-room-1993`, 890 notas, 4 páginas).

Quando a escada inteira volta vazia — ou a sondagem falha por rede —
`profundidade_sondada` fica `None` e o posicionamento **degrada para o
comportamento da v1.9.2**, registrado em telemetria. Nenhuma coleta é
bloqueada por uma sondagem que não deu certo.

##### Reancoragem: frações da profundidade, não incrementos do bloco raso

```
posições profundas = [round(f × profundidade(L)) para f em FRACOES_PROFUNDIDADE]
FRACOES_PROFUNDIDADE = (0,25 · 0,50 · 0,75 · 0,95)
```

tomadas as `n_profundo` primeiras, deduplicadas, e sempre `> n_raso`.

**`RESERVA_PROFUNDIDADE` (25%) e o orçamento de páginas por bucket não mudam.
O que muda é ONDE as páginas caem, não QUANTAS.** Essa é a premissa central do
desenho e o teste que a prova compara, nível a nível, o número de páginas
buscadas antes e depois — igualdade exata.

Degenerados, todos com comportamento nomeado:

- **profundidade ≤ `n_raso`** — o bloco profundo se fundiria ao raso; nenhuma
  posição profunda é emitida e o nível degrada para consecutivo puro. É o
  resultado correto para filme obscuro: não há profundidade a alcançar;
- **profundidade menor que o número de posições pedidas** — as frações
  colidem, a deduplicação as reduz, e o orçamento restante volta ao bloco raso
  pelo mecanismo já existente;
- **profundidade desconhecida** — comportamento v1.9.2 (progressão geométrica
  a partir do fim do bloco raso);
- **nível zerado no histograma** — recebe profundidade 1 pelo piso; na
  prática não recebe orçamento de página (§3[B], alocação), então a questão
  não chega a se colocar.

##### Telemetria (`meta.json`)

`profundidade_sondagem`: `{nivel_sondado, profundidade, exata, requisicoes,
motivo}` e `profundidade_estimada_por_nivel` — `{nível: páginas}`, o que a
âncora usou. Sem esses dois campos, "por que a página 137 foi buscada" é
irrespondível a partir do bruto.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Extensão de orçamento por DÉFICIT (v1.9.4)")*

**A regra — OBSERVACIONAL, e é isso que a define:**

1. Gastar o orçamento base do bucket (`ORCAMENTO_PAGINAS_POR_BUCKET = 16`),
   **exatamente como hoje**, com o mesmo posicionamento estratificado.
2. Se, ao fim do orçamento base, o total de reviews **VÁLIDAS** do bucket for
   menor que a meta com folga (`cota × FOLGA_ALVO_COLETA` = 40 × 1,25 = 50),
   conceder páginas extras **UMA A UMA**, até `TETO_EXTENSAO_PAGINAS = 24`
   (+8 sobre a base), alocadas aos níveis **em déficit**.
3. Parar no teto ou ao atingir a meta, o que vier primeiro.

O bucket que rende bem para em 16 exatamente como antes — a extensão nunca
dispara para ele, e o custo dos filmes que já fechavam a cota é **zero**. O
bucket que rende mal ganha até 8 páginas extras.

**Por que observacional e NÃO preditivo.** A saída óbvia seria estimar o
rendimento de cada nível pelas páginas já baixadas e comprar páginas onde o
rendimento previsto compensa. Está rejeitada, por duas razões:

- **as páginas não são uma amostra do mesmo regime.** Desde a v1.9.2 elas são
  log-espaçadas em profundidade (bloco raso consecutivo + bloco profundo
  geométrico). O rendimento do bloco raso de um blockbuster mede reação de
  massa em semana de estreia; o do bloco profundo mede outra coorte, outro
  tamanho de texto, outro rendimento. Um estimador ajustado no primeiro não
  descreve o segundo;
- **um preditor ruidoso decidindo orçamento é uma peça nova com modo de falha
  próprio** — e esta spec já pagou esse preço uma vez: a parada por ALVO
  (v1.9.0) era exatamente isso, uma heurística otimista decidindo quando
  parar, e foi removida na v1.9.2 por não-determinismo depois de causar o
  37/40 de `cidade-de-deus`. Reintroduzir estimativa na mesma decisão, dois
  releases depois de tê-la removido dali, seria repetir o erro com outro nome.

A regra acima **não estima nada**. Todo número que ela consulta já foi medido:
quantas válidas o bucket tem AGORA (contadas sobre o bruto em disco, pelo
mesmo `_cascade_pool` da seleção), e quais níveis estão abaixo do próprio
alvo. Nenhum parâmetro de calibração novo é introduzido: `TETO_EXTENSAO_PAGINAS`
é um teto de custo, não um limiar ajustável de qualidade, e a meta com folga
reusa `FOLGA_ALVO_COLETA`, que já existe.

**Alocação das extras — QUARTO uso de `redistribuir_deficit`, nenhum mecanismo
novo.** A cada página concedida, o plano de gasto das extras restantes é
recalculado:

```
deficit(L)   = max(0, alvo_com_folga(L) − válidas_atuais(L))
plano        = alocar_bucket(extras_restantes, deficit, níveis_vivos, piso=0)
plano_final  = redistribuir_deficit(plano, {L: extras_restantes se L vivo senão 0})
```

e a página vai para o nível com maior alocação no plano (desempate pelo nível
mais alto, o mesmo de `_maior_resto`). "Nível vivo" é o que ainda não devolveu
página vazia. São as MESMAS duas funções que já alocam reviews entre níveis
(§3[C1]), páginas entre níveis (v1.9.1) e posições dentro de um nível
(v1.9.2) — agora extras entre níveis. Quatro usos, uma implementação.

**Peso por DÉFICIT, não por histograma — e a escolha é deliberada.** Todos os
outros usos de `alocar_bucket` pesam pelo histograma. Aqui não: pesar as
extras pelo histograma daria todas elas ao mesmo nível populoso de baixo
rendimento que a diagnose identificou como o amplificador do problema —
repetiria a concentração em vez de corrigi-la. O déficit é **medido**, não
estimado, e é o que a extensão existe para fechar.

**Onde as páginas extras caem, posicionalmente.** Não recalculam a divisão
raso/profundo — isso mudaria as posições geométricas e faria a base deixar de
ser um prefixo da coleta estendida. Elas são **anexadas**, nesta ordem:

1. posições ainda não buscadas **dentro do intervalo já confirmado** (`≤` a
   maior posição buscada com sucesso). Por monotonicidade da paginação, essas
   páginas **têm conteúdo garantido** — toda extra gasta ali rende;
2. esgotadas essas, posições consecutivas **além** da mais profunda já
   buscada. Aqui uma página pode vir vazia, e vir vazia marca o nível como
   `material_esgotado` para o resto da extensão.

**O teto é POR EXECUÇÃO, não pela vida do bruto — limitação declarada.** A
contabilidade posicional (`posicoes_buscadas`, `maior_confirmada`) vive no
resultado da raspagem, não no `meta.json`, então uma segunda execução do mesmo
filme reconstrói o estado a partir do orçamento BASE e volta a ter 8 extras
disponíveis. Consequências, ambas benignas mas reais: (a) o bruto de um filme
executado duas vezes pode acumular mais que 24 páginas num bucket; (b) a
segunda execução gasta parte das extras **em posições que a primeira já
buscou** — cacheadas, portanto sem custo de rede, mas também sem material
novo, o que aparece na telemetria como extras concedidas sem ganho de
válidas. Não é corrigido aqui: exigiria um registro posicional persistente, e
o checkpoint do lote (§3[H]) já evita a reexecução acidental. Quem reexecutar
um filme de propósito precisa saber disso.

**`--offline` não estende, e preserva a telemetria da coleta que houve.** A
reexecução 100% cache é uma garantia anterior a esta versão (README: "zero
rede, nunca falha"), e a extensão a quebrou: um filme coletado ANTES da
v1.9.4 pede, em `--offline`, uma página que nunca esteve no cache, e o
`FetchError` sobe pelo pipeline inteiro — observado ao vivo em `longlegs`,
página 9 do nível 2,0★. A guarda é explícita: com `fetcher.offline`, o gancho
devolve o `extensao_por_bucket` já gravado em disco, sem buscar nada. Não
devolver nada apagaria o registro (`persistir` SOBRESCREVE o meta) e devolver
zeros inventaria uma extensão que não aconteceu.

**Telemetria obrigatória, por bucket, em `meta.json` (`extensao_por_bucket`):**

| campo | significado |
|---|---|
| `paginas_base` | páginas com conteúdo gastas no orçamento base |
| `paginas_extensao` | extras efetivamente concedidas (0 quando não disparou) |
| `extras_por_nivel` | `{nível: extras}` — a quem foram |
| `motivo_parada` | `meta_atingida` \| `teto_extensao` \| `material_esgotado` |
| `n_validas_pos_base` | válidas do bucket ao fim da base |
| `n_validas_pos_extensao` | válidas do bucket ao fim da extensão |
| `meta` | a meta com folga usada (cota × 1,25) |

A extensão precisa ser **auditável**: "o bucket X recebeu N páginas de extensão
e parou por Y" tem de ser lido do `meta.json`, não reconstruído.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Correção e declaração são CAMADAS, não alternativas (v1.9.4)")*

**Cache — descrição CANÔNICA (a única; §3[C3] aponta para cá).** Por
filme+nível+página (e por texto completo, ver C'), em **arquivos HTML em
disco** — um por página, sob `resultado/cache/<slug>/pages/<ordenacao>/`, mais
`fulltext/`, `film_page.html` e o histograma; nada de banco. Nunca rebuscar
página cacheada. Cache não expira. **A chave de cache inclui a ordenação**
(v1.9.0, `urls.level_page_cache_key`) — trocar de ordenação é uma amostra
diferente, e servir a antiga do cache seria um erro silencioso.

### [B'] Persistência do bruto (v1.9.0) — o artefato que desacopla

**Layout:**

```
dados/bruto/<slug>/meta.json
dados/bruto/<slug>/reviews.jsonl
```

**`meta.json`:** `slug`, `coletado_em` (ISO 8601), `versao_coletor`,
`ordenacao_usada`, `histograma_bruto` (contagem por nível, os 10 níveis),
`paginas_gastas_por_nivel`, `paradas_por_limite` (lista de níveis que pararam
no teto), `contagem_bruta_por_nivel`, `contagem_estimada_valida_por_nivel`,
**(v1.9.1)** `orcamento_paginas_por_nivel` (o orçamento QUE FOI dado a cada
nível, derivado do orçamento por bucket — §3[B] — distinto de
`paginas_gastas_por_nivel`, que é o QUANTO foi de fato usado; a razão entre os
dois é a mesma composição-alvo-vs-atingida que §3[C1] já exige para reviews,
agora também para páginas) e **(v1.9.1)** `janela_temporal` (§4).

**`reviews.jsonl`**, uma review por linha: `id`, `nivel` (0,5–5,0), `texto`,
`n_chars`, `spoiler_flag`, `pagina_origem`, `url`, `autor_hash`.

**Três campos ADICIONAIS ao formato pedido, e o porquê de cada um** — todos são
**propriedades da review**, nunca decisões de seleção, então respeitam o mesmo
princípio que exclui `passou_por_relaxamento` (abaixo):

- **`truncada`** (bool) — a review veio colapsada na listagem (detector
  `.collapsed-text`, §C'.1). Sem esse campo, a invariante de v1.1.0 **"texto
  truncado nunca chega ao LLM"** ficaria impossível de garantir a partir do
  bruto: `n_chars` de um texto truncado é o do trecho visível, e nada
  distinguiria "review curta" de "review longa cortada".
- **`texto_completo`** (bool) — `texto` é o texto integral (nunca foi truncada,
  ou o completamento resolveu). A seleção (§3[C2]) só considera elegível quem
  tem `texto_completo: true`; o resto entra em `n_indisponivel_truncamento`.
- **`data`** (ISO 8601, do `<time class="timestamp">`) — a data da review. É a
  **evidência** de que a ordenação escolhida (§2.3) é a que se acredita ser:
  sem ela, `ordenacao_usada` seria uma declaração inverificável a partir do
  próprio material coletado.

**O que NÃO é gravado no bruto: `passou_por_relaxamento`.** Relaxamento é uma
**decisão de seleção**, não uma propriedade da review — a mesma review é
"relaxada" ou não conforme o filtro que se aplique depois. Gravá-la no bruto
recolocaria no material coletado exatamente o tipo de decisão que esta versão
tirou de lá. É **derivada** no downstream a partir de `n_chars` e
`spoiler_flag`.

**Idempotente e incremental.** Recoletar um filme já coletado **não duplica
reviews** (dedupe por `id`; a linha nova sobrescreve a antiga do mesmo `id`,
para que um completamento resolvido numa execução posterior seja incorporado) e
**atualiza o `meta.json`**. Consequência desejada: coletas sucessivas
**acumulam** superset — trocar a ordenação e recoletar soma material em vez de
substituí-lo, e o `meta.json` registra a ordenação da execução mais recente.

**`dados/` é versionado** (ao contrário de `resultado/cache/`, que é
`.gitignore`d): o cache é HTML reconstruível e volumoso; o bruto é o **insumo
de análise** — pequeno, textual, e a coisa cuja recoleta esta versão existe
para evitar.

#### Distribuição de `pagina_origem` (v1.9.2) — instrumento temporal PRIMÁRIO

`janela_temporal` (abaixo) mede `data`, e `data` é a data ASSISTIDA (campo
de diário), não a de publicação da review — um usuário pode postar HOJE uma
review de um rewatch de anos atrás, produzindo um outlier de data velha em
QUALQUER posição da amostra. Foi essa contaminação que produziu o resultado
MISTO do gate da v1.9.1 (a janela por `data` ESTREITOU sob amostragem mais
profunda em 2 dos 3 filmes — o oposto do esperado).

`pagina_origem`, sob ordenação cronológica (`by/added`, §2.3), não tem essa
contaminação: é o **rank de adição** — a página 40 foi adicionada ao site
antes da página 1, sempre, por construção da ordenação, independente de
quando o AUTOR diz ter assistido. Não é uma data de calendário, mas é um
proxy de recência **sem o ruído** que compromete `data`.

**Telemetria primária** (`distribuicao_pagina_origem`, por bucket, sobre a
amostra SELECIONADA — não o bruto inteiro): `{n, min, max, p5, p50, p95,
fracao_profunda}`, onde `fracao_profunda` é a fração da amostra cujo
`pagina_origem` cai no BLOCO PROFUNDO do respectivo nível (posicionamento
estratificado, acima) — calculada com a mesma divisão raso/profundo
(`RESERVA_PROFUNDIDADE`) usada na coleta, para que telemetria e coleta nunca
divirjam sobre o que conta como "profundo". Espelhada no bloco `coleta` do
resultado.

#### Janela temporal (v1.9.1) — SECUNDÁRIA desde a v1.9.2, proxy contaminado

**Rebaixada a secundária na v1.9.2** — mantida como telemetria (é dado real e
o problema que motivou §2.3 continua relevante), mas o instrumento PRIMÁRIO
de "onde a amostra está no tempo" passa a ser `pagina_origem` (acima), livre
da contaminação de data assistida vs. data de publicação que produziu o
resultado misto do gate. `janela_temporal` fica no JSON com o rótulo
explícito de proxy contaminado — não removida, porque continua sendo o único
sinal de CALENDÁRIO (ano/mês real) que o pipeline tem; `pagina_origem` diz
"quão fundo", não "quando".

A medição da v1.9.0 (§2.3) achou que 79-100% da amostra de cada filme vem de
uma janela de ~7 semanas; a medição de profundidade desta versão (§3[B], gate)
achou que `min`/`max` sozinhos são enganosos (dominados por outliers de data
assistida antiga). A correção nos dois achados é a mesma: gravar a
**distribuição**, não só os extremos.

`meta.json` ganha o campo `janela_temporal`: `{"total": {...}, "por_bucket":
{"negativas": {...}, "medianas": {...}, "positivas": {...}}}`, cada bloco no
formato `{"n", "min", "max", "p5", "p50", "p95"}` — datas truncadas para
`YYYY-MM-DD` (o campo `data` mistura formatos com e sem hora, §3[B']; a hora
não importa para janela). `p50` é a mediana: uma leitura muito mais honesta de
"quando a amostra realmente está" do que o extremo mais velho. Bordas: 1
review → os 5 campos de data são a mesma data; todas as reviews na mesma data
→ idem.

**A computação é bucket-aware, mas o módulo de persistência não é.** O bruto
(`bruto.py`, `collector.py`) continua sem saber onde ficam as fronteiras — a
função pura que calcula min/max/percentis de uma lista de datas vive em
`bruto.py` (opera sobre qualquer lista de reviews que receba, sem embutir
fronteira nenhuma), mas quem agrupa por bucket antes de chamá-la é o
`pipeline.py`, que já é o único módulo que enxerga as duas camadas — o mesmo
padrão de `montar_buckets` (§3[C2]). O campo é escrito como uma atualização
posterior de `meta.json`, sem reescrever `reviews.jsonl`.

#### `dias_por_100_paginas` (v1.9.6) — métrica de PRIMEIRA CLASSE

Quanto **tempo** cada 100 páginas da listagem cobre. Calculada na COLETA e
gravada em `meta.json`, por filme e por nível — a v1.9.5 a calculou em
análise, ad-hoc, num script de sessão; ela sobe para o material persistido
porque é **o discriminador de qual estratégia cada filme precisa**, consultado
por esta versão (limiar da passada, §2.3) e pelas seguintes.

```
dias = mediana(data na página MAIS RASA) − mediana(data na página MAIS PROFUNDA)
dias_por_100_paginas = 100 × dias / (pagina_max − pagina_min)
paginas_para_1_ano   = 365 × (pagina_max − pagina_min) / dias      (None se dias == 0)
```

A mediana por página, e não a data de uma review, porque uma página tem ~12
reviews e a data de qualquer uma delas é o proxy contaminado de §3[B'] — a
mediana da página é robusta ao outlier que domina min/max.

**Ela usa `data` (data ASSISTIDA, proxy contaminado, §3[B']), e para ESTA
finalidade a contaminação importa pouco.** O que se mede é a **TAXA ao longo
das páginas**, não a data absoluta: a contaminação (usuário que registra hoje
uma sessão de anos atrás) é ruído aproximadamente uniforme sobre as posições,
então ela alarga a dispersão dentro de cada página sem inclinar
sistematicamente a diferença ENTRE páginas distantes. O uso proibido continua
proibido: "esta amostra cobre de X a Y" segue sendo afirmação sobre `data`
absoluta, e segue valendo a ressalva de §3[B'].

**Campos gravados** — `dias_por_100_paginas` (bloco do filme) e
`dias_por_100_paginas_por_nivel` (um bloco por nível, chave string como todo
mapa por nível do meta):
`{pagina_min, pagina_max, dias, dias_por_100_paginas, paginas_para_1_ano, n_paginas}`.

**Calculada sobre UMA ordenação de cada vez** — a da coleta base
(`ordenacao_usada`). Misturar as duas ordenações num só cálculo seria somar
posições que não significam a mesma coisa: página 3 sob `by/added` é a 3ª
adição mais recente, página 3 sob `by/added-earliest` é a 3ª mais antiga.

**Bordas nomeadas e testadas:** menos de 2 páginas distintas com data → `None`
(não há taxa a medir); todas as datas iguais → `dias = 0`,
`dias_por_100_paginas = 0.0` e `paginas_para_1_ano = None` (a taxa é
genuinamente zero, e "quantas páginas para um ano" não tem resposta finita —
`None` diz isso, `0` mentiria).

**Precisão limitada pelo alcance do bruto**, e o campo carrega o próprio
denominador (`pagina_min`, `pagina_max`) para que isso seja lido, não
suposto: um filme cujo bruto vai só até a página 12 estima a taxa sobre um
vão de 12 páginas, e extrapolar dela para 256 é extrapolação — declarada
aqui, não corrigida.

#### Duas ordenações no mesmo bruto (v1.9.6)

A passada de §2.3 é a primeira vez que um mesmo `dados/bruto/<slug>/` guarda
material de duas ordenações. Isso quebra duas coisas que eram implícitas
enquanto havia uma só, e as duas se resolvem no material persistido:

**(1) `pagina_origem` deixa de ter significado único.** Sob `by/added` ela é o
rank de adição decrescente (o instrumento temporal PRIMÁRIO, acima); sob
`by/added-earliest` a mesma página 1 é o material mais ANTIGO que existe. Sem
distinguir, `distribuicao_pagina_origem` e a estratificação da seleção
(§3[C2], faixas de profundidade) passariam a tratar reviews de 2012 como "a
faixa mais rasa/recente" — silenciosamente, e com o número parecendo certo.
Por isso `reviews.jsonl` ganha o campo **`ordenacao_origem`** (segmento de URL
sob o qual AQUELA review foi raspada).

É propriedade da review na mesma acepção de `pagina_origem` — *como ela foi
obtida*, nunca uma decisão de seleção —, então respeita o mesmo princípio que
mantém `passou_por_relaxamento` fora do bruto.

**Compatibilidade:** o campo tem default `None`, e `None` significa "coletada
antes do campo existir". A leitura correta de `None` é `meta["ordenacao_usada"]`
da coleta base — resolvida no consumo, **sem reescrever dado histórico com uma
inferência**. Isso exige que a passada NÃO sobrescreva `ordenacao_usada`, o
que nos leva ao segundo ponto.

**(2) `meta.json` não pode mais ser "a última execução".** A regra da v1.9.0 —
meta sobrescrito pela execução mais recente, reviews acumulando — funcionava
porque toda execução era da mesma natureza. Uma passada de 6 páginas por
bucket sob outra ordenação sobrescreveria `orcamento_paginas_por_nivel`
(que a seleção LÊ para achar a fronteira raso/profundo, §3[C2]),
`paginas_gastas_por_nivel`, `profundidade_sondagem` e `janela_temporal` da
coleta base — apagando a descrição da coleta que produziu 95% do material.

Regra da v1.9.6: **o corpo do `meta.json` continua descrevendo a coleta BASE**
(a de `by/added`), e toda passada entra como um item da lista **`passadas`**:

```json
"passadas": [{"ordenacao": "by/added-earliest", "coletado_em": "...",
              "versao_coletor": "...", "motivo": "dias_por_100_paginas=5.5 < 20",
              "orcamento_paginas_por_bucket": 6,
              "orcamento_paginas_por_nivel": {...}, "paginas_gastas_por_nivel": {...},
              "requisicoes": 71, "n_novas": 183, "n_atualizadas": 0,
              "retentativa": {...}}]
```

Uma passada repetida sob a MESMA ordenação substitui o item daquela ordenação
em vez de anexar um segundo — a lista descreve *ordenações presentes no
bruto*, não um log de execuções, e um log de execuções não é o que qualquer
consumidor precisa saber.

> **A REGRA ACIMA NÃO SE CUMPRE NO DISCO DE HOJE — pendência registrada em
> 2026-09-04, achada ao conferir a spec contra os dados.** Varrendo os 35
> `dados/bruto/*/meta.json`: **`passadas` está VAZIA ou ausente nos 35**,
> apesar de a passada ter de fato rodado. **O material sobreviveu; o registro
> não:** o `reviews.jsonl` tem **2.591 reviews com `ordenacao_origem:
> "by/added-earliest"`, distribuídas em exatamente 12 filmes** — os mesmos 12
> que §2.3 diz terem recebido a passada. (Também há 4.710 com
> `ordenacao_origem: None`, que é "coletada antes do campo existir", como esta
> mesma seção prevê.)
>
> **A causa está diagnosticada e é conhecida:** `persistir()` SOBRESCREVE o
> `meta.json` em vez de mesclar, então republicar um filme sob o pipeline
> fresco apaga o array `passadas` — o mesmo footgun que §3[V] cita ao
> justificar a guarda `LIMITE_LOTE_SEM_CONFIRMACAO`, detalhado em
> `docs/arquivo-de-estudos/coleta/DIAGNOSTICO_OFFLINE.md`, "Achado adicional (v1.9.16): `meta.json` perde
> `passadas`".
>
> **A consequência prática, e é o motivo de isto ficar escrito AQUI, na regra
> que ela quebra:** hoje **não dá para responder "este bruto tem material de
> qual ordenação?" pelo `meta.json`** — só varrendo `ordenacao_origem` no
> `reviews.jsonl`, que é o caminho que esta seção existia para tornar
> desnecessário. Nada em produção lê `passadas` (a seleção lê
> `orcamento_paginas_por_nivel`, que vive na raiz do meta e não foi afetado),
> então isto não corrompe nenhum artefato — é perda de auditabilidade, não de
> dado. **Não corrigido aqui:** a correção é fazer `persistir()`/
> `atualizar_meta` MESCLAREM `passadas`, e é mudança de código.

**Não exposto no frontend nesta sessão.** Como todo campo de `meta.json`, é
espelhado no bloco global `coleta` do JSON de resultado (§4, mesmo mecanismo
de auditoria da v1.9.0) — mas `frontend/js/filme.js` não lê `coleta` hoje, e
esta sessão não adiciona esse consumo. O dado existe para auditoria e para
decisões futuras (ex.: informar o passo largo do gate acima), não para exibir
ao usuário final.

### [H] Harness de lote (v1.9.3)

Infraestrutura para rodar [A]→[B'] (só COLETA, sem síntese) sobre uma lista
de filmes, não um só — o que a v1.9.2 fechou tecnicamente na camada de
coleta ainda exigia uma execução manual por filme. `src/espectro24/lote.py`;
racional curto porque é orquestração, não uma nova regra de negócio.

**Checkpoint em arquivo, não em memória.** Um `estado.json` (`dados/lote/
<nome>/estado.json`) registra, por slug: `status` (`pendente` /
`concluido` / `falhou`), motivo (se falhou) e timestamp. Escrito **após
cada filme**, não em lote ao final — um lote interrompido a qualquer
momento (rede, Ctrl-C, sono da máquina) retoma pulando todo slug já
`concluido`. A persistência do bruto (§3[B']) já era idempotente; o
checkpoint é o que falta para não RECOMEÇAR a decidir o que já foi feito.

**Validação de slug — 1 requisição, antes de gastar orçamento de páginas.**
Busca a listagem de reviews "qualquer nota" (`reviews_qualquer_nota_url`,
`/film/<slug>/reviews/by/activity/`) e reaproveita o `parser.parse_reviews`
já testado: 404/erro de rede → slug inválido, `FetchError`/`AntiBotError`
capturado e reportado como falha isolada, sem derrubar o lote; 200 sem
nenhuma review reconhecida pelo parser → tratado como falha de validação
(`sem_reviews`), pulando a coleta pesada.

**Achado real (v1.9.3, durante a Entrega 2):** a primeira versão desta
função buscava a página PRINCIPAL do filme (`film_page_url`, mesma usada
por `ficha.resolver_ano_letterboxd`) e casava um trecho de markup
(`js-route-reviews`, tooltip de contagem) contra ela — e falhou contra os
3 filmes reais testados (`parasite-2019`, `eighth-grade`,
`everything-everywhere-all-at-once`), todos marcados `sem_reviews`
incorretamente, porque essa tag só existe nas páginas de LISTAGEM de
reviews, não na página raiz do filme. Um detalhe de markup que as
fixtures sintéticas dos testes não capturavam (a fixture reproduzia a
mesma suposição errada). Corrigido para reusar o parser real de reviews
em vez de um regex ad-hoc — existência e presença de review verificadas
juntas, na mesma requisição, pelo mesmo código que a coleta de verdade
usa. Duas funções novas em `urls.py`: `reviews_qualquer_nota_url` e
`reviews_qualquer_nota_cache_key`.
`histograma` ausente **não** é motivo de rejeição aqui — o pipeline já
degrada esse caso graciosamente (alocação uniforme, §3[G]), então
pré-validar duas vezes a mesma coisa seria custo redundante, não segurança.

**Falha isolada.** Cada slug roda dentro de um `try/except` que cerca
TODO o pipeline de coleta daquele filme — qualquer exceção (rede, parsing,
markup inesperado) vira uma entrada `falhou` no checkpoint com o motivo, e
o loop segue para o próximo slug. Nenhuma exceção de um filme escapa para
derrubar o lote inteiro; a única exceção que ainda para tudo é
`AntiBotError` em `--offline=False` sem intenção de escalar (mesma política
de sempre, §restrições) — mas mesmo essa é registrada por slug antes de
propagar, para o resume saber onde parou.

**`material_esgotado` é CASO ESPERADO, não erro (§3[B]).** Um filme
obscuro esgotando material antes do orçamento não é uma falha do harness
— é o comportamento correto e já coberto pela persistência e pelo piso
escalonado (§3[C3]). Os 3 filmes do catálogo, sendo populares, nunca
exercitaram esse caminho em produção (só em teste sintético, §3[B]/§3[C3]):
o lote é a primeira vez que ele roda contra o Letterboxd real em escala, e
por isso os testes desta entrega verificam explicitamente que ele não
quebra nem a persistência, nem `montar_buckets`, nem a serialização do
JSON — um bucket em `sem_analise` é dado válido, não uma falha do harness.

**Log por filme.** Uma linha por nível durante a coleta (reaproveita o
`on_level` que `run_pipeline`/`collect_all_levels` já aceitam) e um
resumo por filme ao final de cada um — o lote roda por horas, e progresso
sem eco é indistinguível de travado.

**Fora do harness, deliberadamente:** paralelismo/concorrência (§2, delay
sequencial ≥2s continua valendo, filme a filme) e qualquer mudança de
parâmetro de coleta — o harness só ORQUESTRA a execução de [A]→[B'] já
existente, não modifica seu comportamento.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "[H] Harness de lote (v1.9.3)")*

### [C2] Seleção downstream — cota 40/40/40 sobre o bruto persistido (v1.9.0)

Lê `dados/bruto/<slug>/` e escolhe **até 40 reviews por bucket**, com tudo o
que era decisão de coleta virando **parâmetro de chamada**: `fronteiras`,
`cota_por_bucket` (40), `min_chars` (150), `excluir_spoiler` (True), `cascata`
(150 → 50 → sem filtro), `piso_nivel` (2). **Zero requisições de rede.**

Por bucket:

1. Elegíveis = reviews dos níveis daquele bucket (pelas `fronteiras` recebidas)
   com `texto_completo: true` e — se `excluir_spoiler` — sem `spoiler_flag`.
2. Alvo por nível = alocação de [C1] recomputada sobre o **mesmo histograma**
   (persistido em `meta.json`, portanto disponível offline).
3. **Cascata por nível**, na ordem: `≥150` → se o nível daria **zero**, `≥50` →
   se ainda zero, **sem filtro**. Idêntica à regra da v1.1.0 (§C): a cascata só
   dispara quando o degrau anterior daria zero naquele nível, nunca para
   "completar cota".
4. **Redistribuição de déficit** ([C1], ressalva 2), restrita ao mesmo bucket.
5. **Estratificação por profundidade dentro do nível (v1.9.5)** — ver abaixo.
   Ordem de escolha DENTRO de cada faixa: `(pagina_origem, ordem de aparição
   no jsonl)`, que é a ordem de amostragem da ordenação escolhida (§2.3).
   Determinística e reproduzível.

**Registrar por bucket** (§4): `n` final, **composição por nível** (alvo vs.
atingida), e **quantas reviews entraram por cada degrau da cascata**.

#### Estratificação da seleção por profundidade — E1 (v1.9.5)

**O defeito que corrige.** A seleção consumia o pool em ordem de
`(pagina_origem, ordem no jsonl)` e parava ao fechar a cota — então **recência
virou critério de seleção implícito**, escolhido por ninguém. Medido sobre os
35 filmes: das 1316 reviews profundas que sobreviviam ao filtro, só **716
(54,4%)** entravam na amostra; **600 ficavam em disco sem chegar ao produto**,
e 13 dos 105 buckets tinham material profundo e selecionavam ZERO dele.

**A regra.** O intervalo de `pagina_origem` de cada nível é dividido em três
faixas e a cota daquele nível é alocada entre elas:

```
faixa 1 = 1 .. ⌈n_raso/2⌉        (raso recente)
faixa 2 = ⌈n_raso/2⌉+1 .. n_raso  (raso)
faixa 3 = > n_raso                (profundo)
```

A divisão é **estrutural, não um tercil da distribuição observada**: a coleta
já produz dois blocos de naturezas diferentes — o raso é consecutivo e denso,
o profundo é esparso e cada página cobre muito mais tempo. Um tercil das
posições presentes daria faixas diferentes em cada filme, sem significado
comum entre eles.

A alocação entre faixas é `alocar_bucket` com pesos iguais seguida de
`redistribuir_deficit` com a contagem de cada faixa como disponibilidade —
**quinto uso da mesma função** (reviews entre níveis, páginas entre níveis,
posições dentro de um nível, extras da v1.9.4 entre níveis, agora vagas entre
faixas). Faixa vazia devolve suas vagas às outras automaticamente.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Estratificação da seleção por profundidade — E1 (v1.9.5)")*

**Quando os dois critérios de estratificação competem, quem cede é este.**
Em 9% dos pares (bucket, nível) a cota do nível é menor que 3 e não cabe em
três faixas. Aí a estratificação por profundidade cede para a **alocação
proporcional por nível** (§3[C1]), e o comportamento é idêntico ao de antes da
v1.9.5. A ordem de precedência não é arbitrária: a alocação por nível carrega
uma garantia de representatividade que o histograma sustenta, enquanto a
estratificação por profundidade é preferência de cobertura.

**A estratificação depende do orçamento de páginas**, que é quem define
`n_raso`. `selecionar` passa a aceitar `orcamento_paginas_por_nivel` (lido do
`meta.json`); **sem ele, o comportamento é byte-idêntico ao da v1.9.4** — o
que mantém offline e testes antigos válidos e torna a estratificação uma
adição, não uma substituição.

#### Motivos de descarte, discriminados (v1.9.1) — telemetria pura

O rendimento medido na v1.9.0 foi ~27% (73% do bruto não entra na seleção), e
até esta versão a telemetria não dizia **por quê** — sem isso não dá para
defender `min_chars=150` como número (§3[B], "Resultado medido", saída 5: com
`min_chars=50` os três buckets fecham 40/40/40), nem para avaliar qualquer
mudança futura de filtro com dado em vez de intuição.

Cada review do bruto de um nível é classificada em **exatamente uma**
categoria — `selecionada` ou um dos motivos abaixo — numa ordem de
precedência fixa, de modo que a soma dos motivos **sempre** fecha com
`n_brutas − n_validas` daquele nível:

1. `truncada_sem_texto` — `texto_completo == false` (a truncada não foi
   resolvida, ou o completamento a descartou — §C');
2. `spoiler` — marcada spoiler e `excluir_spoiler=True` (não conta quando o
   parâmetro é `False`: nesse caso a review é elegível, não descartada);
3. `abaixo_min_chars` — mais curta que o degrau da cascata que vigorou
   NAQUELE nível (não o `min_chars` nominal — se a cascata relaxou para 50,
   o corte real é 50);
4. `excedente_cota` — passou em tudo (texto completo, sem spoiler, comprimento
   suficiente) mas ficou **além** do que a alocação/redistribuição daquele
   nível permitiu — é material real, apenas não coube na cota;
5. `duplicata` — defensivo; o dedupe por `id` já acontece na persistência do
   bruto (§3[B']), então esperado **sempre zero** aqui; existir e não ser zero
   seria sinal de um bug na camada de baixo, não desta camada;
6. `outros` — catch-all; esperado **sempre zero**, canário de classificação
   incompleta.

Persistido por nível (`motivos_descarte`, dict `motivo → n`) e agregados nos
campos já existentes — `n_descartadas_spoiler`/`n_descartadas_curtas`/
`n_indisponivel_truncamento` passam a ser **derivados** do mesmo dict
discriminado (uma fonte de verdade, não duas contagens que podem divergir).
Nenhuma mudança de comportamento: é telemetria sobre decisões que a seleção
já tomava, só que agora nomeadas.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_COLETA.md` — "Precisão da amostra — nos DOIS níveis de confiança")*

### [C3] Piso escalonado — 4 estados (v1.9.0)

Substitui o piso binário de 3 (`sem_analise` ou tudo). Calculado sobre o **`n`
final de cada bucket** depois da seleção:

| `n` final | Estado | O que o bucket entrega |
|---|---|---|
| **≥ 15** | `completa` | temas + frequências + quantificadores |
| **8–14** | `sem_quantificador` | frequências, com marca de amostra pequena; sem quantificador verbal |
| **3–7** | `sem_numero` | temas listados, **sem número e sem quantificador** |
| **< 3** | `sem_analise` | comportamento atual: contagem + `reviews_url`, nenhum tema |

**Os limiares (3, 8, 15) são ARBITRÁRIOS** e entram na spec com esse rótulo
explícito, no sentido definido em **§2, "O que 'ARBITRÁRIO' significa nesta
spec"** — o mesmo que vale para os limiares de `marcacao_perspectiva` (§D2,
v1.5.0) e para `LIMIAR_PASSADA_ANTIGA` (§2.3). Não
há evidência empírica que os fixe; são um primeiro corte com a ordem de
grandeza certa (ver a tabela de precisão acima: em `n=8` o intervalo de 95% já
passa de ±34pp, o que torna um quantificador verbal indefensável).

**Nesta sessão, apenas o CAMPO é exposto.** `estado_piso` entra no JSON de
resultado, consumível pelo frontend e pelo narrador. As **variantes de
narrador** e os **estados de UI** correspondentes **NÃO** são implementados
aqui. O campo `modo` (`completo`/`reduzido`/`sem_analise`) permanece intacto,
para não quebrar frontend e render existentes.

#### Caso de borda — bucket DOMINANTE em modo reduzido

A regra de **ABERTURA OBRIGATÓRIA** do MOVIMENTO 3 (§D2, variante COM
distribuição) manda abrir pelo grupo de **maior peso**. Num filme obscuro, o
bucket dominante pode cair em `sem_numero` ou `sem_analise` — não há narrativa
definida para "abrir por um grupo que não tem temas". Comportamento definido
(documentado agora, **implementado depois**):

> **O peso vem do histograma de NOTAS e NÃO depende de haver review com
> texto.** Portanto a abertura **continua sendo do grupo dominante**, com seu
> `rotulo_peso` e percentual — esse é um fato sobre o filme, e suprimi-lo
> reintroduziria a infidelidade por omissão que a v1.4.0 corrigiu (um filme
> amplamente amado soando dividido porque o grupo grande ficou mudo).
> O que muda é o **conteúdo** da abertura, conforme o estado do grupo
> dominante:
> - `completa` / `sem_quantificador`: comportamento atual.
> - `sem_numero`: abre pelo peso e cita os temas do grupo **sem nenhuma
>   frequência** — nem número, nem quantificador verbal.
> - `sem_analise`: abre pelo peso e diz, explicitamente, que **não há material
>   escrito suficiente desse grupo para descrever o que ele achou** — e só
>   então segue para o grupo de maior peso seguinte, que passa a carregar o
>   corpo do movimento. A ausência é declarada, nunca preenchida com os temas
>   de outro grupo nem disfarçada abrindo por quem tem material.
>
> Invariante que amarra os três casos: **peso e temas são dados diferentes, com
> disponibilidade diferente** — a narrativa pode ter o peso sem ter os temas, e
> nesse caso reporta o peso e declara a falta, em vez de reordenar os grupos
> para esconder o buraco.

Registrar por nível (bruto, §3[B']): `paginas_gastas_por_nivel`,
`contagem_bruta_por_nivel`, `contagem_estimada_valida_por_nivel`,
`paradas_por_limite`. Registrar por nível (análise, §4): `n_validas`,
`n_alvo`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`,
`n_descartadas_truncamento`.

**Cache:** ver §3[B], "Cache" — a descrição canônica está lá, junto da camada
que o produz. *(Correção de registro, 2026-09-04: existiam DUAS descrições do
cache nesta spec, ~800 linhas separadas e **divergentes**. Esta, a segunda,
dizia "(SQLite ou JSON por filme)" — **errado, conferido**: o cache é de
arquivos HTML em disco, um por página, sob `resultado/cache/<slug>/pages/<ordenacao>/`
(`fetcher._cache_path`) — e **omitia a regra da chave de ordenação**, que é a
metade que importa. A descrição de §3[B] estava correta e completa; esta foi
substituída por um ponteiro em vez de mantida como segunda fonte de verdade,
para não voltarem a divergir.)*

**Caminho do cache — PROVISÓRIO (v1.1.1):** implementado em `resultado/cache/<slug>/` em vez de `cache/<slug>/` na raiz. Consequência direta da restrição de arquivos da Fase 1 (que não permitia criar `cache/` fora de `resultado/`), não uma decisão de design. Ratificado para v1.1.1 — mudar agora seria churn sem ganho. **Candidato a v1.2:** desacoplar para `cache/` ou `.cache/` na raiz — `resultado/` é semanticamente a **entrega** (descartável/versionável), enquanto o cache é **estado reconstruível caro** (dezenas a centenas de páginas HTML); misturar os dois acopla ciclos de vida opostos (ex.: limpar `resultado/` hoje também apaga o cache e força recoleta completa).

### [C] Filtros e cascata (por nível)

> **v1.9.0 — esta seção descreve REGRAS, não mais um estágio de coleta.** Os
> filtros e a cascata continuam idênticos no conteúdo, mas passaram a ser
> aplicados **downstream, sobre o bruto persistido** (§3[C2]), com cada valor
> entrando como **parâmetro** em vez de constante. Durante a coleta os mesmos
> filtros são usados **só para decidir parar de paginar** (§3[B], degrau b) —
> nada é descartado por eles.

Ordem por review: (1) tem nota → (2) sem flag de spoiler → (3) comprimento.

Cascata avaliada por nível, sobre o material persistido do nível:
1. Filtro padrão (≥150 chars). Se `n_validas ≥` alvo do nível: nível completo.
2. Se `n_validas <` alvo: nível abaixo do alvo — o déficit vai para a
   redistribuição dentro do bucket (§3[C1]), **nunca** para relaxamento.
3. Se `n_validas == 0` no nível: relaxar para ≥50 chars; se ainda 0, remover
   filtro. Nível pode terminar vazio. **A cascata só dispara em zero** — ela
   nunca é usada para completar cota.

O piso de análise continua **por bucket**, agora **escalonado em 4 estados**
(§3[C3]). No estado mais baixo (`sem_analise`, `n < 3`) o comportamento é o de
sempre: exibir a **contagem** e a **URL da página de reviews do filme**
(`https://letterboxd.com/film/<slug>/reviews/`), no formato `→ N review(s)
disponíveis em <url>`, tanto no terminal quanto no JSON (campo global
`reviews_url`). **NÃO exibir os textos brutos das reviews.**

> **Por que não exibir texto bruto (v1.1.4):** a cláusula anterior ("se houver 1–2 reviews, exibir os textos brutos com aviso") contradizia o princípio de design do cabeçalho da spec — *todo trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler*. Texto integral de review **sem** passar pela camada anti-spoiler do LLM (§D) é o caminho de **maior** risco de spoiler do produto; e a flag de spoiler do Letterboxd é **autodeclarada** (não confiável como garantia). Apontar para a página de reviews transfere a decisão de risco para o usuário, de forma consciente, em vez de o produto imprimir o texto por ele.

**Nota sobre comprimento e truncamento:** o filtro de comprimento usa o texto visível. Review truncada que já passa dos 150 chars no trecho visível é válida; o texto completo é resolvido em C'.

### [C'] Completamento de reviews truncadas — regra "nunca pela metade"
Aplicado somente a reviews que **já passaram todos os filtros** (não gastar requisição com review descartável):

1. **Detecção de truncamento — corrigido (Fase 1 / v1.1.1):** o detector é **exclusivamente o marcador de colapso `.collapsed-text`** no corpo (equivalente observável: texto visível terminando em `…`). `data-full-text-url` está presente em **quase toda review** (truncada ou não) e por isso **NÃO discrimina** — usá-lo como sinal de truncamento daria falsos positivos em massa. Validado com 2 casos positivos + 2 negativos, zero erros (ver `docs/arquivo-de-estudos/coleta/FASE1_INCOGNITAS.md` §A3). `data-full-text-url` continua sendo a **fonte da URL de completamento**, só não é mais o detector.
2. Para cada review truncada válida: buscar `data-full-text-url` (delay 2s, cache por id de viewing — chave via `p[data-likeable-identifier].uid`, ver §2.1).
3. Falha na busca → **uma** retentativa. Falha persistente → **descartar a review** e registrar em `n_descartadas_truncamento`. Nunca enviar texto parcial ao LLM.
4. O texto completo substitui o visível para todos os fins (inclusive re-checagem de spoiler: se o texto completo revelar o placeholder de spoiler, descartar).
5. **Sem backfill de cota na v1.1.1:** se o completamento descartar uma review (passo 3), a cota do nível fecha com o que sobrou (ex. 9/10) — **não há reposição** buscando outra bruta para substituir a descartada. Razões: (i) o shortfall fica **visível** via `n_descartadas_truncamento`, não é silencioso; (ii) o piso de 3 por bucket (§2) + modo `sem_analise` já tratam o caso degenerado sem inventar dados; (iii) backfill ingênuo tem custo de requisição **não limitado** — cada reposição pode ela mesma vir truncada e falhar, encadeando. **Candidato a v1.2**, com uma distinção que deve orientar o design: **backfill barato** (repor a partir da lista de brutas já paginadas no nível — custo = 1 requisição de full-text por reposição) é razoável; **backfill caro** (repaginar o nível para buscar mais brutas) não é — só o barato deve entrar em v1.2.
6. **SUPOSIÇÃO ABERTA — não verificada ao vivo:** o comportamento do endpoint `/s/full-text/` para uma review **simultaneamente truncada e com spoiler** é *assumido* (devolver o placeholder de spoiler, permitindo o descarte no passo 4), não confirmado com um caso real — nenhuma review nessa condição apareceu nas amostras da Fase 1. Coberto por teste com fixture sintética (caminho de código exercitado), mas **não** por um caso ao vivo. Se o endpoint devolver o texto real em vez do placeholder, o spoiler vazaria ao LLM. **Instrução operacional:** se um viewing id truncado+spoiler aparecer numa coleta futura, gastar 1 requisição para confirmar o comportamento antes de confiar cegamente nesta suposição.

Custo estimado: no pior caso ~100 requisições extras por filme novo (uma por review válida truncada), ~3 min adicionais a 2s/req. Aceitável para ferramenta pessoal com cache.



### [D] Síntese LLM

*(A lei deste estágio estava enterrada sob 676 linhas de arqueologia em bloco
de citação. O histórico foi para `HISTORICO_PROSA.md`; o que sobrou aqui é o
que vale — inclusive as fatias de lei que viviam dentro daqueles blocos.)*

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D] Síntese LLM")*

> **A allowlist é explícita e justificada, arquivo por arquivo.** Três scripts
> de diagnóstico anteriores (`diagnostico_fluencia.py`,
> `diagnostico_fluencia_v2.py`, `compare_models.py`) chamam o SDK direto de
> propósito: o `thinking_budget` e o modelo **são o objeto de estudo** deles —
> passar pelo adaptador, que fixa esses parâmetros, tornaria o experimento
> impossível. Eles estão numa constante literal no próprio teste, com o
> motivo escrito ao lado; adicionar um arquivo à allowlist é uma mudança
> deliberada e revisável, não um efeito colateral.
>
> **`tests/` fica FORA da varredura** — os testes importam o SDK para
> construir dublês e nunca fazem chamada real. A única exceção é a fixture do
> próprio guard-rail, que injeta uma violação sintética num arquivo temporário
> e confirma que a varredura a detecta: sem ela, um guard-rail que não
> detecta nada passaria como um que não tem nada a detectar.
>
> **O que o guard-rail NÃO garante.** Ele checa o CAMINHO, não os parâmetros:
> um chamador que use o adaptador está protegido; um que replique o transporte
> com outro nome de variável pode escapar da varredura textual. É uma rede de
> classe de regressão, no mesmo estatuto das checagens mecânicas do §E2 — cobre
> o modo de falha observado, não todo modo de falha concebível.

> #### Retentativa de TRANSPORTE em `resposta()` — o mesmo desenho do `Fetcher`, trazido do scraping para o LLM (v1.9.24)
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D] Síntese LLM")*

> **Onde vive, e por que não é contornável.** Dentro de `resposta()`, no
> mesmo lugar que despacha por provider — não num invólucro por fora que um
> chamador (ou um script futuro) possa contornar chamando `deepseek_resposta`
> /`_gemini_resposta` direto. Esgotadas as tentativas, levanta
> `LLMTransportError` (subclasse de `LLMError`) encadeando o erro original.
> Testado com a mesma técnica de `tests/test_publicar_catalogo.py`
> (`test_a_guarda_roda_dentro_de_cmd_publicar`): chamar `resposta()` — o
> caminho real de produção — e confirmar que o transporte é invocado mais de
> uma vez pela MESMA chamada.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D] Síntese LLM")*

> **A decisão.** O provider deixa de ser global e passa a ser configuração
> **por estágio do pipeline**: `PROVIDER_POR_ESTAGIO` em `config.py`, com
> `classificacao` e `narrativa` resolvidos independentemente. `--provider`
> continua existindo e, quando passado, força TODOS os estágios — é o
> override manual, não o caminho normal.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D] Síntese LLM")*

- **Uma chamada por bucket** (máx. 3 por filme), modelo configurável.
- **Provider-agnóstico (v1.1.1, ampliado na v1.8.0 e na v1.9.8):** a interface de cliente injetável (`client_call(system, user, model) -> str`) é o **contrato formal**. **Providers suportados: TRÊS** — **DeepSeek** (`DEEPSEEK_API_KEY`), **Gemini** (`GEMINI_API_KEY`, modo JSON nativo) e **Anthropic** (`ANTHROPIC_API_KEY`). Seleção via `--provider {anthropic,deepseek,gemini}`; **sem a flag, o provider vem de `PROVIDER_POR_ESTAGIO` (§3[D], v1.9.8), não de auto-detecção** — a auto-detecção por chave presente no ambiente (`detect_provider`) continua existindo como fallback, e ali duas chaves presentes ou nenhuma é erro, exigindo decisão explícita. `DEFAULT_PROVIDER = "deepseek"` desde a v1.8.0.

  > *(Correção de registro, 2026-09-04: esta linha dizia "Providers suportados: **Gemini** e **Anthropic**" e "`--provider {gemini,anthropic}`", omitindo o DeepSeek — que entrou na v1.8.0 e é o **default de produção** desde então. Conferido em `config.py`: `PROVIDER_ENV_KEYS` tem as três chaves e `DEFAULT_PROVIDER = "deepseek"`.)*

  **A configuração em vigor, conferida em `config.py` (2026-09-04):**

  | estágio | `PROVIDER_POR_ESTAGIO` | `MODELO_POR_ESTAGIO` |
  |---|---|---|
  | `classificacao` | `deepseek` | `deepseek-v4-flash` |
  | `rotulagem` (§[D3]) | `deepseek` | `deepseek-v4-flash` |
  | `narrativa` (§D2) | `gemini` | `gemini-3.7-flash` |
  | `veredito` (§3[V]) | `gemini` | `gemini-3.7-flash` |
  | `condicoes` (§0) | `gemini` | `gemini-3.7-flash` |

  **A síntese [D] não tem entrada própria nessas duas tabelas** e cai no
  `DEFAULT_PROVIDER`/`MODEL_DEFAULT` (`deepseek` / `deepseek-v4-flash`).
- **Default de modelo Gemini — `gemini-2.5-flash` (v1.1.2, ratificado com evidência):** a comparação de modelos (`resultado/comparacao/COMPARACAO.md`) rodou o MESMO prompt sobre o MESMO corpus (`oppenheimer-2023`) em `gemini-2.5-flash-lite` e `gemini-2.5-flash`. O flash-lite cometeu **3 violações de instrução** documentadas: (1) bucket `negativas` inteiro em inglês, violando "saída sempre em pt-BR"; (2)-(3) `observacao_geral` generalizando o recorte filtrado do bucket para "a maioria dos críticos considera o filme um fracasso" — o próprio erro de enquadramento que motivou o preâmbulo de papel abaixo. O `gemini-2.5-flash`, no mesmo teste, não repetiu nenhuma das três. Default Anthropic: `claude-sonnet-4-6`. **Estes dois são o `PROVIDER_DEFAULT_MODELS` — o modelo que cada provider usa quando ninguém especifica um. Eles NÃO são o modelo de produção de nenhum estágio**, que vem de `MODELO_POR_ESTAGIO` (tabela acima); conferido em `config.py`, os dois valores seguem exatamente assim.
- **Prompt PARAMETRIZADO POR BUCKET (v1.1.2)** — não mais uma string única. A parametrização é **por bucket** (nome + intervalo de notas), nunca por provider/modelo: o texto para um dado bucket é **byte-idêntico** entre Gemini e Anthropic; só o transporte (SDK, formato de chamada) muda por adaptador.
- Entrada: todas as reviews válidas do bucket (texto COMPLETO + nota), instruções fixas.
- Frequências sempre relativas a `n_reviews_analisadas`, nunca absolutas soltas. *(Até a v1.8.2 esta linha dizia "buckets têm tamanhos-alvo diferentes (50/20/30)"; sob a cota 40/40/40 os alvos são iguais, mas o `n` REAL de cada bucket continua podendo diferir — material insuficiente fecha um bucket curto (§3[C3]) —, então a regra do denominador não muda.)*
- **Denominador e clamp — regra de código, não de prompt (v1.1.1):**
  - `n_reviews_analisadas` é **sempre carimbado pelo código**, a partir da contagem real de reviews enviadas ao LLM naquele bucket. Qualquer valor que o LLM devolva nesse campo do JSON é **ignorado** — nunca usado, nem como fallback. (Correção de bug: a v1.1.0 fazia o inverso — confiava no valor do LLM e só usava o real como fallback.) Em modo degradado essa distinção é a diferença entre honestidade e maquiagem estatística.
  - `mencoes_aproximadas` é **clampado** para o intervalo `[0, n_reviews_analisadas]` (o código nunca aceita um numerador maior que o total de reviews do bucket, nem negativo). Quando o clamp atua, é sinal de alucinação do modelo e **fica visível, não silencioso**: o tema carrega `mencoes_clampadas: true` + `mencoes_valor_original` (o valor cru que o LLM devolveu), exibido também no render do terminal.
- Saída obrigatória em JSON:

```json
{
  "bucket": "negativas",
  "temas": [
    {
      "tema": "ritmo lento",
      "mencoes_aproximadas": 14,
      "n_reviews_analisadas": 40,
      "exemplo_parafraseado": "vários reviewers acham o segundo ato arrastado",
      "mencoes_clampadas": false,
      "mencoes_valor_original": null,
      "aspas_removidas": false
    }
  ],
  "observacao_geral": "1-2 frases de síntese do bucket",
  "idioma_invalido": false,
  "escopo_suspeito": false
}
```

(`mencoes_clampadas`/`mencoes_valor_original`/`aspas_removidas`/`idioma_invalido`/`escopo_suspeito` são carimbados pelo código pós-parsing — não fazem parte do que se pede ao LLM no prompt; ver regras abaixo.)

> *(Correção de registro, 2026-09-04: o exemplo acima trazia
> `"n_reviews_analisadas": 50`, a cota anterior à v1.9.0 — hoje é **40**
> (§0, §2). Como no caso do intervalo, **o defeito era do exemplo, não da
> regra**: o prompt real não traz número nenhum ali (o schema que ele pede usa
> `<int>`), e o valor é sempre carimbado pelo CÓDIGO a partir da contagem real
> de reviews enviadas — qualquer número que o LLM devolva nesse campo é
> ignorado, nem como fallback. Conferido em `build_system_prompt`.)*

#### Template do prompt (SPEC — texto oficial, `build_system_prompt(bucket_nome)` em `synthesize.py`)

**a. Preâmbulo de papel — NOVO (v1.1.2), parametrizado por `{bucket_nome}` e `{intervalo}` (ex.: `negativas` / `0.5–2 estrelas`):**

> *(Correção de registro, 2026-09-04: este exemplo dizia `0.5–2.5 estrelas`, a
> fronteira anterior à v1.9.0. **A regra nunca esteve errada — só a
> ilustração:** `{intervalo}` é derivado de `FRONTEIRAS` em tempo de execução
> por `synthesize._intervalo_bucket` → `buckets.intervalo_de`, nunca
> redigitado. Conferido chamando a função: hoje ela devolve `0.5–2 estrelas`,
> `2.5–3 estrelas` e `3.5–5 estrelas`, e o preâmbulo montado diz literalmente
> `faixa "negativas" (0.5–2 estrelas)`. É exatamente a garantia de §2.2 — "as
> fronteiras não podem estar hardcoded em nenhum ponto do código" —
> funcionando; o que estava hardcoded era o exemplo nesta spec.)*

> Você é uma etapa de um pipeline que agrega reviews de usuários de um filme do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES desta etapa (negativas, medianas, positivas); você está recebendo EXCLUSIVAMENTE a faixa "`{bucket_nome}`" (`{intervalo}`) — um recorte enviesado POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.
>
> Sua função é descrever o que ESTE grupo específico de reviews diz. Outros módulos do pipeline cuidam das outras faixas de nota; o usuário final verá as três análises lado a lado, cada uma rotulada com sua faixa.
>
> Consequência explícita: é PROIBIDO generalizar para "os críticos", "a maioria", "o consenso" ou "a recepção do filme". A `observacao_geral` deve se referir sempre a ESTE grupo (ex.: "as reviews `{bucket_nome}` apontam...", "este grupo destaca..."), nunca ao filme em termos absolutos.

**Motivação (evidência empírica):** rodando o prompt v1.1.1 (sem preâmbulo) sobre o bucket `negativas` de `oppenheimer-2023`, o flash-lite escreveu `observacao_geral: "a maioria dos críticos considera o filme um fracasso"` — generalizando um recorte filtrado por construção (só notas ≤2.5) para a opinião geral do filme. O preâmbulo ataca esse erro de enquadramento na raiz, antes de qualquer instrução de formato.

**b. Instruções fixas (invariáveis) — as 5 anteriores + 2 novas (v1.1.2):**
  1. Anti-spoiler: descrever críticas em nível temático (ritmo, atuações, fotografia, roteiro em termos abstratos); **proibido mencionar eventos da trama, destinos de personagens, reviravoltas ou o final**, mesmo que as reviews os mencionem.
  2. `exemplo_parafraseado` é paráfrase, nunca citação literal de review.
  3. Temas ordenados por `mencoes_aproximadas` decrescente; máximo 6 temas por bucket; não inventar temas com menção única salvo se o bucket tiver < 5 reviews.
  4. Reviews em qualquer idioma; saída sempre em pt-BR.
  5. Responder apenas o JSON, sem preâmbulo.
  6. **NOVO:** proibido usar aspas (simples, duplas ou angulares) dentro de `exemplo_parafraseado` — nunca citar nem reproduzir um trecho entre aspas, mesmo traduzido; reescrever sempre em terceira pessoa, com palavras próprias. **Motivação:** o `gemini-2.5-flash`, na mesma comparação, usou frases entre aspas em `exemplo_parafraseado`, violando a regra de paráfrase (citação literal, ainda que traduzida).
  7. **NOVO:** reforço de idioma — TODOS os campos de texto em pt-BR, incluindo os NOMES DOS TEMAS, independentemente do idioma das reviews de origem.
- Parsing defensivo (strip de fences, try/except) e uma única retentativa em caso de JSON inválido (inalterado, v1.1.1).

#### Validações pós-parsing (código, não prompt) — v1.1.2

Rede de segurança/telemetria — o preâmbulo de papel (acima) é a **defesa principal** contra vazamento de escopo; estas checagens são baratas e propositalmente imperfeitas (heurísticas), não substituem revisão humana.

a. **Idioma:** heurística de contagem de stopwords pt-BR vs. inglês sobre a concatenação de `temas` + `exemplos` + `observacao_geral`. Ausência de stopwords de qualquer idioma (texto curto/indeterminado) **não** conta como violação — só conta quando há evidência de maioria em outro idioma. Se detectar não-pt-BR: **uma retentativa**, com instrução de idioma reforçada anexada ao FIM do prompt (não substitui o preâmbulo/instruções). Se persistir: aceita o resultado da retentativa e registra `idioma_invalido: true` no bucket (visível no render).
b. **Aspas:** se qualquer `exemplo_parafraseado` contiver aspas de citação (`" ' “ ” ‘ ’ « » ‹ ›`), remove-as **mecanicamente** (não é reescrita — apenas apaga os caracteres e normaliza espaços) e registra `aspas_removidas: true` **no tema**. **Sem retentativa** — correção mecânica basta, não vale gastar uma chamada de LLM. **v1.7.1 — bugfix:** quando a aspas vinha ESCAPADA no texto (`\"A Cura\"`), a remoção trocava só o caractere de aspas, deixando a contrabarra órfã (`\A Cura\`) — publicado ao vivo em `cure` e `the-invite-2026`. A remoção agora consome a contrabarra que precede a aspas junto, como uma unidade (`_remover_aspas`, `synthesize.py`).
c. **Escopo:** checagem barata na `observacao_geral` por marcadores literais de generalização ("a maioria dos críticos", "o consenso", "os críticos consideram", "amplamente aclamado", "amplamente rejeitado"). Se encontrar: **uma retentativa**; se persistir, aceita e registra `escopo_suspeito: true` no bucket. Heurística imperfeita por design (lista curta e literal, não NLP) — o preâmbulo de papel é a defesa principal; isto é rede de segurança e telemetria.

**Retentativa combinada:** se idioma **e** escopo falharem na mesma resposta, é feita **UMA única chamada extra** que reforça os dois ao mesmo tempo (não duas retentativas separadas) — mantém o orçamento de chamadas por bucket previsível (no máximo 1 retentativa de JSON + 1 retentativa de validação = 3 chamadas no pior caso por bucket).

#### Anti-spoiler: escopo da proteção e risco aceito (v1.1.3)

> **RISCO ACEITO** (decisão do usuário, 2026-07-19, validada com juiz humano que conhecia o filme — *Cure*, 1997): a proteção anti-spoiler cobre eventos da trama, desfechos e destinos de personagens. A zona cinzenta "mecanismo/dispositivo central da trama" (ex: nomear a técnica que conecta os eventos) é **risco aceito e NÃO deve ser endurecida**: instruções mais restritivas degradariam a especificidade dos temas em todos os filmes para evitar um falso negativo raro e tolerável. Saídas nessa zona são comportamento dentro do risco aceito, não bug.

> **EMENDA — sinopse oficial curta como fonte do MOVIMENTO 1 (v1.3.0, decisão do usuário, 2026-07-20):** a regra de "zero conteúdo de trama" continua valendo para reviews e para o conhecimento próprio do modelo, mas ganha uma exceção estreita e explícita: a **sinopse OFICIAL** de um filme (campo `overview` do TMDB — material de divulgação curado pelo próprio estúdio/distribuidor, categoria equivalente à sinopse de contracapa/poster) pode ser usada, condensada, como fonte do MOVIMENTO 1 da narrativa (§D2). Justificativa: esse texto é escrito para ser lido por quem ainda não assistiu — é a mesma informação que o usuário veria no pôster ou na página do filme antes de decidir assistir; não é "conteúdo de trama" no sentido que a regra original protege (revelações extraídas de reviews de quem já assistiu, ou conhecimento factual do modelo sobre o filme). O que **continua proibido**, sem exceção:
> - sinopses de **terceiros** (não oficiais — resenhas, wikis, sinopses de outros catálogos) como fonte de premissa;
> - **expansão** da sinopse oficial com qualquer conhecimento externo do modelo sobre o filme, elenco, direção ou produção;
> - usar a sinopse oficial para justificar relaxar o anti-spoiler dos MOVIMENTOS 2/3 (temas dos buckets) — a fronteira entre síntese validada e reviews brutas (§D2, "Decisão de arquitetura") não muda.
>
> Ressalva operacional: a sinopse oficial do TMDB é, na prática observada, quase sempre limitada à premissa (é material de marketing) — mas não há garantia formal disso. Por isso o prompt do narrador (§D2) instrui explicitamente: se a `sinopse_oficial` parecer revelar algo além da premissa inicial, usar só a parte que é premissa. Essa é uma instrução ao LLM (julgamento, não checagem mecânica) — no mesmo espírito de risco aceito do parágrafo acima, não um novo validador de código.



### [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS

*(Mesmo padrão do estágio anterior: a lei vinha depois de sete blocos de
citação, e parte do que era apresentado como lei descrevia o narrador
ARQUIVADO na v1.9.11 — esse ficou em `HISTORICO_PROSA.md`.)*

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

> **O que o briefing carrega, tudo pré-computado:**
> - ficha do filme (TMDB: premissa, diretor, gênero, ano, duração);
> - temas por bucket com contagem e fração, **já ordenados** e **já
>   cortados** no número que o movimento 3 deve usar;
> - `rotulo_peso` por bucket, derivado do histograma;
> - **a ordem de apresentação do movimento 3**, como lista explícita —
>   antes era a instrução "comece pela perspectiva de MAIOR peso";
> - o `quantificador` verbal de cada tema, por faixa percentual;
> - o **orçamento de frases** de cada movimento;
> - o `estado_piso` de cada bucket **traduzido em permissão** — o que pode e
>   o que não pode ser dito sobre aquele grupo, em vez de o narrador ter de
>   inferir isso de `modo=sem_analise`;
> - a `marcacao_perspectiva` exigida por grupo.
>
> **O que continua sendo instrução, e por quê.** Nem toda invariante é
> computável. Continuam no prompt: anti-spoiler, proibição de importar fato
> externo, tom neutro do movimento 2, respeito à minoria, e o vocabulário
> "notas, nunca reviews". Essas são regras sobre COMO ESCREVER uma frase
> que o código não tem como pré-decidir sem escrever a frase ele mesmo. A
> medida de sucesso da entrega é quantas SAÍRAM, não zero.
>
> **O que o narrador continua NÃO podendo fazer:** escolher tema, computar
> número, decidir ordem. Toda quantificação que aparece na prosa vem do
> briefing — mesma autoridade do código sobre número que vale desde a
> v1.1.1 (denominador) e v1.2.3 (quantificador).
>
> **Compatibilidade.** O caminho antigo (`_serialize_output_for_narrator` +
> `build_narrator_prompt`) permanece no módulo e continua testado: a
> comparação entre os dois é o que justifica a troca, e apagar o anterior
> tornaria a regressão impossível de medir.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

> Duas checagens mecânicas novas, ambas em `qualidade.py`:
> - `quantificador_fora_de_faixa` — toda construção quantificadora
>   presente no texto tem de pertencer a uma faixa que o briefing
>   REALMENTE atribuiu a algum tema. Substitui a comparação literal por
>   uma comparação de PERTENCIMENTO, que é o que a invariante sempre quis
>   dizer;
> - `quantificador_repetido` — nenhuma construção pode aparecer mais de
>   `QUANT_MAX_REPETICOES` (= 2) vezes no texto. É a checagem que teria
>   pego o defeito, e a razão de ela não existir antes é que a repetição
>   nunca foi violação de nenhuma regra: era obediência.
>
> **Detalhe que a implementação obriga:** o `rotulo_peso` de cada grupo
> (§3[G]) compartilha vocabulário com as construções ("a maioria", "boa
> parte") e é literal obrigatório. Antes de contar construções, as
> ocorrências dos rótulos de peso do briefing são REMOVIDAS do texto —
> senão o texto seria punido por escrever exatamente o que o briefing
> mandou escrever.
>
> **(2) Estrutura de parágrafo.** `gemini-3.1-pro` entregou os 3 filmes
> num bloco único de até 318 palavras, sem uma quebra de linha. Zero
> flags: `formato_invalido` (v1.7.2) checa se a prosa veio embrulhada em
> JSON ou markdown, não se ela é legível.
>
> `paragrafos_insuficientes` e `paragrafo_longo` passam a ser flags. O
> mínimo **não é uma constante**: é o número de movimentos com orçamento
> maior que zero — 3 com ficha, 2 sem ela. Derivar do briefing evita o
> caso em que o narrador é reprovado por obedecer à instrução de pular o
> movimento 1. O teto por parágrafo é `MAX_PALAVRAS_PARAGRAFO` (= 180).
>
> **(3) Orçamento do movimento 2 — DIAGNÓSTICO ANTES DA CORREÇÃO.**
> O movimento 2 encolheu em todos os modelos (em
> `gemini-3.7-flash`/`cure`, uma única frase). Três causas eram possíveis
> — orçamento, material, prompt — e a correção de cada uma é diferente.
> **A medição descarta o orçamento e aponta o material, mas não a
> escassez dele: a truncagem.**
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

> **(4) Best-of-3 com seleção POR CÓDIGO.** Três narrativas independentes
> por filme; escolha mecânica, em `selecao_narrativa.py`. Eliminatório:
> todas as flags limpas. Entre as limpas, ordena por (a) clichê da
> blocklist, (b) repetição de construção quantificadora, (c) variância do
> comprimento de frase — PROXY DECLARADO de ritmo, pela hipótese de que
> texto com frases todas do mesmo tamanho lê como lista, e (d) cobertura
> dos temas do briefing. **Fallback obrigatório:** se nenhuma das 3
> passar limpa, seleciona a de menor severidade e faz retry DIRECIONADO
> só nas frases infratoras — descartar as três seria jogar fora prosa boa
> por causa de uma frase.
>
> **Os proxies são calibrados contra leitura humana antes de valer.** As
> 3 narrativas de um filme são apresentadas ao dono do projeto SEM
> indicação de qual o código escolheu, e a preferência dele é comparada
> com a escolha automática (`resultado/best-of-3/calibracao.md`).
> Registro honesto: poucos casos NÃO provam que os proxies estão certos;
> provam, no máximo, que não estão obviamente errados. Um desacordo é
> resultado publicável — significa que o proxy mede outra coisa.
>
> **(5) Gate do editor [E2] — DECIDIDO NA v1.9.10: APOSENTADO.** O gate
> rodou: as narrativas finais dos 3 filmes foram geradas sob briefing
> determinístico + best-of-3 e **sem passar pelo editor**, e a leitura do
> dono do projeto concluiu que **o ritmo se sustenta sem ele**. O E2 foi
> aposentado — código movido para `experimentos-editor-e2-arquivado/`, no
> padrão de `experimentos-ollama-arquivado/`, com o motivo ao lado.
> **Conferido no código em 2026-09-04:** `cli.py` não chama o editor, as
> flags `--no-edicao`/`--com-editor` não existem, e as constantes `EDITOR_*`
> saíram de `config.py`. O registro do estágio está em §3[E2], marcado como
> histórico.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

> #### FICHA PERSISTIDA E RÓTULO COMPARATIVO — os dois bloqueios da republicação (v1.9.12)
>
> A execução da v1.9.11 num filme fora do catálogo (`joker-folie-a-deux`,
> distribuição invertida) achou dois defeitos que a amostra de 3 filmes
> aclamados escondia. Nenhum é do narrador: os dois são de DADO chegando
> errado — ou não chegando — ao briefing.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

> **O que NÃO muda, e é o que mantém a invariante de pé:** o rótulo continua
> carimbado por CÓDIGO e preservado LITERALMENTE pelo narrador; o número
> entre parênteses é o mesmo; as contrações pré-aprovadas (v1.9.11)
> continuam valendo, porque `variantes_rotulo` opera sobre o primeiro token
> do rótulo, seja ele qual for.
>
> **A verdade do comparativo é condição, não estilo:** a forma "menor" só é
> aplicada quando o grupo é DE FATO menor que o vizinho de mesma faixa.
> Grupos com percentual IGUAL na mesma faixa mantêm o mesmo rótulo — dizer
> "menor" ali seria falso, e a coincidência de rótulo é honesta quando os
> pesos coincidem de verdade.
>

> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)")*

Etapa **PÓS-síntese**, opcional, controlada pela flag `--tom` (ver abaixo). Uma **única chamada LLM para o filme inteiro** (não por bucket); **o provider é escolhido por ESTÁGIO desde a v1.9.8** (ver §3[D], "Provider por estágio") — não mais forçosamente o mesmo da síntese.

**Decisão de arquitetura (invariante, inalterada desde v1.2.0):** o narrador recebe **EXCLUSIVAMENTE o JSON validado** — os temas, `mencoes_aproximadas`, `n_reviews_analisadas` e `observacao_geral` dos 3 buckets, o total de reviews, e (v1.3.0) a **ficha técnica** do filme quando existir (§3a). **NUNCA as reviews brutas.** Ele reescreve informação **já validada** como prosa; não tem acesso a nada que as validações (§D) não tenham aprovado, nem a nada que não venha da ficha oficial do TMDB. Isso é garantido **por construção**: a entrada do narrador é o dict de saída de `build_output` (que não serializa texto de review) mais o campo `ficha` (que vem só do TMDB, nunca de reviews).

Por que essa fronteira (justificativa anti-embelezamento / anti-spoiler): dar reviews brutas ao narrador reabriria os dois riscos que o pipeline inteiro existe para conter — (1) **spoiler**, pois texto integral não passou pela camada anti-spoiler do LLM; e (2) **embelezamento/infidelidade**, pois o narrador poderia "florear" com material não contabilizado, quebrando a fidelidade às frequências. Lendo só o relatório validado (+ ficha oficial), o narrador não pode afirmar nada que a camada de baixo não tenha aprovado.

**v1.3.0 — narrativa em três movimentos:** a v1.2.x produzia um único bloco de prosa livre. A v1.3.0 estrutura esse bloco em três movimentos sequenciais, sem subtítulos visíveis no texto final (a divisão organiza o LLM, não aparece como marcação para o leitor) — motivada pela interface em vídeo que consome a narrativa em três passos de review: apresentar o filme, descrever a experiência de assisti-lo, e só então contrastar as reações.

1. **MOVIMENTO 1 — O FILME** (2-3 frases; só existe se houver `ficha` no relatório — sem ficha, a narrativa começa direto no Movimento 2): premissa a partir da `sinopse_oficial` do TMDB (pode condensar, PROIBIDO expandir com conhecimento externo — ver emenda de anti-spoiler em §3[D]), diretor, gênero, ano; duração só se for relevante ao que os movimentos 2/3 dizem.
2. **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): como é assistir ao filme, usando **apenas** propriedades DESCRITIVAS (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade) em que os grupos concordam no **núcleo factual**, mesmo divergindo na avaliação. Tom neutro, sem valência — descreve, não julga; a avaliação fica para o Movimento 3. **v1.3.1 — três critérios obrigatórios** para uma propriedade entrar aqui: **(a) categoria** — só descritiva, PROIBIDO juízo de qualidade (atuação/roteiro/direção boa-ou-ruim, isso é sempre disputa e pertence ao Movimento 3); **(b) presença** — vem de temas de pelo menos DOIS grupos com o mesmo núcleo factual, mesmo com valência diferente ("lento e tedioso" + "lento e deliberado" → núcleo "ritmo lento"); **(c) não-contradição** — se QUALQUER grupo nega o núcleo factual (não só diverge na avaliação), a propriedade é desqualificada. Cada propriedade usada é registrada em `consensos_usados` (telemetria — ver abaixo).
   **v1.4.1 — OMISSÃO AUTORIZADA:** se **menos de duas** propriedades passarem nos três critérios, o MOVIMENTO 2 deve ser **CURTO (1 frase) ou AUSENTE**, e a narrativa passa direto ao MOVIMENTO 3. **Omitir é o comportamento CORRETO, não uma falha** — não há cota de frases a cumprir, e um filme com poucos temas descritivos simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de qualidade suavizado ("estilo visual eficaz", "abordagem arrojada") é **pior** do que não ter o movimento: é a violação do critério (a) disfarçada de descrição por um advérbio de hesitação. Quando omitido, `consensos_usados` vem como **lista vazia** — resultado esperado, e a validação de `_consensos_validos` **não** trata lista vazia como suspeita (válida por vacuidade, regra já vigente desde a v1.3.1).
3. **MOVIMENTO 3 — O CONTRASTE** (enxuto — ~40% menor que a narrativa única da v1.2.x): as perspectivas dos três grupos, priorizando os 2-3 temas **mais fortes** de cada grupo em vez de cobrir todos os até 6 possíveis — decisão motivada pela interface, que já exibe as barras de frequência tema a tema (a narrativa não precisa duplicar essa cobertura completa). Mantém **todas** as invariantes vigentes desde v1.2.x (rótulos de quantificador pré-computados, escopo por grupo, proibição de prevalência entre grupos, sem aspas, anti-spoiler, pt-BR).

Alvo de tamanho total: **250-400 palavras** (ajustado de 200-350 na v1.2.x — o movimento 1 adiciona conteúdo quando há ficha).


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "Diagnóstico de fluência (v1.5.0) — por que as narrativas soavam mecânicas")*

#### MARCAÇÃO DE PERSPECTIVA (v1.5.0, regra nova — só existe COM distribuição)

**Motivação:** ao remover os verbos de reporte (regra de REGISTRO, item f), a afirmação de um grupo minoritário pode soar como fato do próprio narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante (o grupo de maior peso, apresentado primeiro pela regra de ABERTURA OBRIGATÓRIA). Sem "eles apontam que", a frase "o humor é previsível" lida isolada parece uma afirmação do produto sobre o filme, não a opinião de uma fatia minoritária das notas.

**Pré-computação em código (`_marcacoes_por_bucket`/`_marcacao_perspectiva`, `synthesize.py`), por grupo, a partir dos `share_real`:**
- `dominante` = maior share entre os três grupos do filme;
- `marcacao_perspectiva = "nenhuma"` se `share > dominante/3`;
- `marcacao_perspectiva = "simples"` se `share <= dominante/3`;
- `marcacao_perspectiva = "antecipada"` se `share <= dominante/10`.

A condição mais restritiva (`antecipada`) é checada primeiro — um share que a satisfaz também satisfaz `simples`. **Só existe quando há distribuição real:** o mesmo motivo pelo qual a COTA de coleta (50/20/30) não pode alimentar este cálculo — usar a cota apresentaria amostragem como se fosse prevalência, o defeito que a v1.2.1 proíbe (§D2, regra (c) sem distribuição). Sem `share_real`, não há "dominante" legítimo a calcular. O valor é passado ao narrador na serialização, junto do `rotulo_peso` de cada grupo — o LLM não calcula nem escolhe.

**Limiares são ponto de partida, calibráveis:** ao contrário das faixas de quantificador (v1.2.2/v1.2.3) e de peso (v1.4.0), que vieram de casos reais observados e comparação de modelos, estes limiares (`dominante/3`, `dominante/10`) não têm evidência empírica prévia — são um primeiro corte razoável, sujeito a ajuste em versões futuras conforme a leitura adversarial das narrativas regeneradas.

**Regra no prompt:**
- TODO trecho que fala de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra exigido).
- `marcacao_perspectiva = "simples"`: além da abertura, ao menos UM marcador de perspectiva dentro do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
- `marcacao_perspectiva = "antecipada"`: o marcador interno deve vir ANTES da primeira afirmação substantiva do trecho sobre aquele grupo — não no fim.
- Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
- PROIBIDO marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito, conforme a v1.4.0 (RESPEITO À MINORIA).

**Telemetria (`marcadores_perspectiva`, mesmo padrão de `consensos_usados`/`quantificadores_usados`):** o narrador declara `{grupo, trecho}` para cada marcador usado, com o trecho copiado literalmente da narrativa. **v1.6.1 — esta declaração é auditoria humana, não fonte de validação** (ver abaixo); ela é persistida no JSON e exibida no render exatamente como antes.

**Validação pós-parsing (`_marcadores_validos`, `synthesize.py`) — v1.6.1, reescrita para verificar o TEXTO, não a declaração:**
(a) para todo grupo com `marcacao_perspectiva != "nenhuma"`, o MOVIMENTO daquele grupo (`_span_de_movimento`: do ponto em que ele é ancorado — rótulo de peso ou percentual — até a âncora do próximo grupo, ou o fim do texto) contém **alguma expressão de atribuição reconhecida** (a mesma lista `_EXPRESSOES_DE_PERSPECTIVA` que `montar_protegidos`, §E2, já usa — fonte única, sem duplicação: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa" e variantes); **v1.7.1** ampliou o vocabulário com a família "quem gostou/não gostou/amou/ficou no meio" (e as formas com "para" na frente) — caso real do `cure`, onde "quem não gostou considerou o ritmo lento e tedioso" cumpria a função de atribuição para o grupo de 3%, mas não estava na lista, produzindo falso positivo em `perspectiva_nao_marcada` num texto honesto. O "para quem" ISOLADO continua de fora — é pronome relativo comum e foi o que causou o falso NEGATIVO original da v1.6.0.)
(b) para `marcacao_perspectiva == "antecipada"`, **PELO MENOS UMA** dessas ocorrências precisa cair na MESMA frase em que o grupo é ancorado ou na frase IMEDIATAMENTE seguinte.

**v1.6.0 — dois bugs corrigidos:** "antecipada" passou a exigir **um** marcador bem posicionado, não todos (o narrador legitimamente declara mais de um ao elaborar o grupo — foi o que aconteceu no `the-invite`); e a comparação do trecho declarado ganhou normalização de caixa/acento/demonstrativo.

**v1.6.1 — a normalização não bastou, e a correção foi trocar O QUE se verifica.** O caso concreto do `cidade-de-deus` sobreviveu à v1.6.0: o narrador declarou *"Para esse grupo, muitos reconhecem a qualidade técnica…"* e escreveu *"Muitos neste grupo reconhecem a qualidade técnica…"* — divergência de **ORDEM DAS PALAVRAS** (similaridade 0.92), que nenhuma normalização de caixa/acento fecha. Fechar por comparação difusa com limiar foi **descartado** (de novo): um limiar de similaridade é uma linha arbitrária, e a checagem existe para confirmar que o marcador de perspectiva **EXISTE no texto** — não que a frase declarada é uma transcrição fiel dele.

A correção pela raiz separa as duas coisas que a v1.6.0 ainda misturava:
- `marcadores_perspectiva` é o que o LLM **diz que fez** — telemetria para revisão humana, exatamente como `consensos_usados`;
- a validação escaneia o que o LLM **realmente escreveu**, procurando qualquer expressão de atribuição reconhecida no trecho de texto associado ao grupo — **igual usa `trecho` declarado**.

Consequência: `_normalizar_trecho`/`_trecho_aparece` (v1.6.0) foram **removidas** — não davam conta do problema real, e a nova checagem não compara mais string contra string. `montar_protegidos` (§E2) e `_marcadores_validos` agora leem a **mesma constante** `_EXPRESSOES_DE_PERSPECTIVA`, então um vocabulário novo de atribuição só precisa ser ensinado num lugar.

Falha em qualquer critério → **1 retentativa** com reforço (`_REFORCO_MARCADORES`); se persistir, aceita e sinaliza `perspectiva_nao_marcada: true` em `narrativa_flags`. Lista vazia é válida por vacuidade quando nenhum grupo exige marcação (dominante ≈ os três grupos, ex. 40/30/30 — nenhum passa nos limiares). Persistido no JSON como campo global `marcadores_perspectiva` e exibido no render de terminal como bloco compacto, mesmo padrão de `consensos_usados`.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "EXEMPLO DE ESTILO — MIGRADO PARA O EDITOR §E2 (v1.6.0)")*

#### Telemetria de fluência (v1.5.0, NOVO) — métricas calculadas em código, não pelo LLM

Mesma filosofia das demais telemetrias do §D2: o código não reescreve a prosa, só mede e sinaliza. Calculadas por `_metricas_fluencia` (`synthesize.py`) sobre o texto final da narrativa e persistidas em `metricas_fluencia`:

| Métrica | Definição |
|---|---|
| `n_frases` | Frases (divisão heurística por `.`/`!`/`?`, sem tratar abreviações) |
| `media_palavras` | Média de palavras por frase |
| `cv_comprimento` | **Desvio padrão ÷ média** de palavras por frase — mede VARIAÇÃO, não o comprimento em si (a regra de ritmo pede variação, não frases curtas o tempo todo) |
| `frase_mais_curta` | Menor contagem de palavras entre as frases |
| `aberturas_repetidas` | Pares de frases CONSECUTIVAS com a mesma primeira palavra (normalizada, minúscula) — proxy barato para "mesma estrutura de abertura" |
| `verbos_reporte` | Ocorrências dos verbos da regra (f) e flexões (`elogi-`, `destac-`, `apont-`, `relat-`, `consider-`, `classific-`, `mencion-`, `ressalt-`, `reconhec-`, `express-`, `descrev-`) |
| `adverbios_mente` | Ocorrências de advérbios intensificadores de uma lista fechada (intensamente, profundamente, extremamente, excessivamente e sinônimos comuns da mesma família) — deliberadamente NÃO cobre todo advérbio em `-mente` (ex. "praticamente" não é intensificador) |

**v1.6.0 — as métricas viram DIAGNÓSTICO PURO.** Os gatilhos automáticos de retentativa (`cv_comprimento < 0.40` · nenhuma frase ≤ 10 palavras · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`), o reforço `_REFORCO_FLUENCIA` e a flag `fluencia_baixa` foram **REMOVIDOS**.

**Motivo — as métricas não acompanham qualidade.** No `cure` (`docs/arquivo-de-estudos/editor-e-narrador/DIAGNOSTICO_FLUENCIA_V2.md`, células A vs. B), o texto qualitativamente MELHOR pontuou PIOR nas duas métricas centrais:

| | A (pior texto) | B (melhor texto) |
|---|---|---|
| `cv_comprimento` | 0.35 | **0.28** |
| `verbos_reporte` | 3 | **6** |

`cv_comprimento` mede **dispersão** de comprimento de frase, não legibilidade: um texto com frases uniformemente boas pontua mal, e um texto truncado no meio pontua bem. Otimizar contra a métrica — que é exatamente o que uma retentativa automática faz — empurra o modelo a **degradar** a prosa para satisfazer um número. É o mesmo erro que o projeto já evitou em outros eixos (o código é autoridade sobre NÚMERO e RÓTULO; não é, e não deve ser, autoridade sobre ESTILO).

`_metricas_fluencia` continua sendo calculada e persistida em `metricas_fluencia`, com o mesmo estatuto de `consensos_usados`: **material de revisão humana**, não critério automático. O eixo de fluência passa a ser responsabilidade do editor (§E2), que trabalha por instrução e exemplo, não por limiar.

Persistida no JSON como campo global `metricas_fluencia` e exibida no render de terminal como linha-resumo, após os blocos de consensos/quantificadores/marcadores.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "Telemetria de fluência (v1.5.0, NOVO) — métricas calculadas em código, não pelo LLM")*

- **SEM distribuição** → `build_narrator_prompt(False)` devolve o prompt
  histórico (`NARRATOR_SYSTEM_PROMPT`), com a regra (c) restritiva da v1.2.1
  intacta. O fallback não é uma reescrita parecida: é a MESMA constante.
  **Emenda v1.4.1:** até a v1.4.0 esse texto era byte-idêntico ao da v1.3.1;
  a v1.4.1 alterou as partes **compartilhadas** do prompt (omissão do
  MOVIMENTO 2 e declaração de quantificadores), que valem nas duas variantes.
  A invariante que continua de pé — e é a que a comparação A/B precisa — é a
  original: **só a regra (c) difere entre as duas variantes** (verificado em
  teste). **Emenda v1.5.0:** a marcação de perspectiva e o exemplo de estilo
  few-shot (ambos abaixo) foram adicionados **dentro** da regra (c) COM
  distribuição, porque dependem do `share_real` — a marcação usa o
  `dominante` calculado a partir dele, e o exemplo usa vocabulário de peso
  que a variante SEM distribuição proíbe. A invariante "só a regra (c)
  difere" continua válida por construção: é justamente por dependerem do
  mesmo dado que essas duas adições vivem dentro dela, não fora. As regras
  de RITMO e REGISTRO (que não dependem de share), por sua vez, entraram nas
  partes **compartilhadas** do prompt — presentes, idênticas, nas duas
  variantes.
- **COM distribuição** → a regra (c) INVERTE, virando "PESO REAL DE CADA GRUPO":

> c. **PESO REAL DE CADA GRUPO — REGRA CRÍTICA** (a distribuição está disponível neste relatório): você recebeu a DISTRIBUIÇÃO REAL das notas do filme, vinda do histograma público — quantas pessoas deram cada nota. Isso é um dado diferente do tamanho dos grupos de reviews analisadas (40/40/40), que é apenas a COTA DE COLETA e continua NÃO significando prevalência. Regras:
> - **ANCORAGEM OBRIGATÓRIA:** cada grupo DEVE ser apresentado, na primeira vez que aparecer no MOVIMENTO 3, com o `rotulo_peso` que veio no relatório para ele (ex.: "a grande maioria das notas (~79%)"). É PROIBIDO usar um rótulo MAIS FORTE do que o fornecido; um MAIS FRACO é permitido se a fluência pedir — nunca o oposto. Você NÃO calcula nem escolhe esse rótulo: ele é dado.
> - **ABERTURA OBRIGATÓRIA:** o MOVIMENTO 3 começa pela perspectiva de MAIOR peso. Esta regra tem precedência sobre a liberdade de ordem da regra (e).
> - **ÊNFASE PROPORCIONAL:** dê aproximadamente mais espaço ao grupo de maior peso e menos ao de menor peso — um filme amplamente amado não pode soar dividido, e um amplamente rejeitado não pode soar morno.
> - **RESPEITO À MINORIA:** a perspectiva minoritária é apresentada COMO minoritária, mas SEM desdém, ironia ou insinuação de que quem pensa assim está errado. Menos espaço, mesma seriedade analítica: quem procura saber se vai gostar precisa entender o que incomodou essa parcela.
> - **VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS (v1.4.1):** o `rotulo_peso` vem do histograma de NOTAS do Letterboxd, ou seja, de TODO MUNDO que avaliou o filme; os temas vêm das REVIEWS COM TEXTO, um subconjunto bem menor. São duas populações diferentes. Portanto, ao expressar peso, é OBRIGATÓRIO escrever "das notas" ("a grande maioria das notas (~79%)") e é PROIBIDO escrever "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review nem sobre quem assistiu sem avaliar. As frequências de TEMA seguem no vocabulário oposto (regra d): sempre em relação às reviews analisadas daquele grupo. Os dois vocabulários nunca se misturam.
> - Continua PROIBIDO inventar um número-síntese do filme (nota média, score, "X de 10", "nota N"): os shares por faixa são a ÚNICA quantificação permitida, e são três números, nunca um só.
>
> **MARCAÇÃO DE PERSPECTIVA** (v1.5.0 — motivada pela regra de REGISTRO acima): ao reduzir os verbos de reporte, a fala de um grupo minoritário pode soar como fato do narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante. Cada grupo do relatório vem com uma `marcacao_perspectiva` PRÉ-COMPUTADA (nenhuma/simples/antecipada, a partir do `share_real` — você NÃO calcula nem escolhe esse valor):
> - TODO trecho que falar de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra é exigido).
> - `marcacao_perspectiva="simples"`: além da abertura, inclua ao menos UM marcador de perspectiva DENTRO do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
> - `marcacao_perspectiva="antecipada"`: o marcador interno precisa vir ANTES da primeira afirmação substantiva sobre esse grupo, não no fim do trecho.
> - Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
> - É PROIBIDO um marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito (mesma RESPEITO À MINORIA acima).
> Para CADA marcador de perspectiva que você usar, registre em `marcadores_perspectiva` (ver formato de saída) o grupo e o TRECHO EXATO, copiado literalmente da narrativa, onde ele aparece.
>
> EXEMPLO DE RITMO E MARCAÇÃO COM FILME FICTÍCIO — nunca reaproveitar seu conteúdo; os fatos vêm sempre do JSON recebido. O filme abaixo NÃO EXISTE e os números são INVENTADOS: eles servem só para mostrar a FORMA (variação de comprimento, aberturas diferentes, marcadores de perspectiva, ausência de verbos de reporte). Copiar qualquer fato, adjetivo ou número daqui é uma violação da regra de FIDELIDADE.
>
> ANTES (evite este ritmo): "A grande maioria das notas (~74%) elogia intensamente a condução do filme e o trabalho de câmera, destacando a habilidade de sustentar o clima em cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas sente que a indefinição do meio e a duração prolongada tornam a experiência cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo como arrastado e os personagens como estáticos."
>
> DEPOIS (busque este ritmo): "Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra num ponto só: o filme não tem pressa e usa isso a favor, porque cada silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma minoria das notas (~19%) chega até a metade junto. Para esse grupo, o problema aparece quando a história precisa decidir para onde vai, e não decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para eles a lentidão nunca vira método, os personagens não saem do lugar, e o final chega sem ter construído nada."

**`rotulo_peso` é PRÉ-COMPUTADO pelo código** — mesmo princípio da v1.2.3
(quantificador) e da v1.1.1 (denominador): o LLM não escolhe rótulo numérico.
Mapa determinístico sobre o `share_real`, do mais fraco ao mais forte:

| Faixa | Rótulo |
|---|---|
| **< 5%** | **uma fração mínima** *(v1.6.0)* |
| 5–10% | uma pequena minoria |
| 10–25% | uma minoria |
| 25–45% | uma parcela expressiva |
| 45–70% | a maioria |
| ≥ 70% | a grande maioria |

**v1.6.0 — faixa nova no extremo fraco.** Até a v1.5.0, 8% e 1% recebiam ambos "uma pequena minoria", achatando uma diferença de **oito vezes** entre os dois grupos minoritários — observado em `cidade-de-deus` (shares 91/8/1), onde o grupo mediano e o negativo apareciam com o mesmo peso verbal. A faixa `< 5% → "uma fração mínima"` separa o "muito pouco" do "quase nada" sem mexer em nenhuma outra fronteira, e sem tocar na convenção de desempate.

**Bordas resolvidas SEMPRE para o rótulo mais fraco** (itera do mais fraco ao
mais forte, primeiro match vence) — mesma convenção da v1.2.3:
`10 → uma minoria`, `25 → uma minoria`, `45 → uma parcela expressiva`,
`70 → a maioria`. Consequência documentada: "a grande maioria" começa de fato
em **71%**, não em 70% — subestimar o peso é aceitável, inflar não é.

O rótulo é sempre entregue **junto do percentual** (`"a grande maioria das
notas (~79%)"`): o número é o que impede o rótulo de virar retórica solta.

**Validação — a rede de prevalência MUDA DE SINAL:**

| | Sem distribuição | Com distribuição |
|---|---|---|
| Marcadores de prevalência ("minoria", "a maioria do público"…) | **violação** → retentativa → `prevalencia_suspeita` | **desligada** — essas palavras agora são EXIGIDAS pela regra (c); manter o detector ligado flaggaria toda narrativa correta |
| Ancoragem de peso | não se aplica (nada a ancorar) | **exigida** → retentativa (`_REFORCO_ANCORAGEM`) → `peso_nao_ancorado` |
| **(v1.4.1)** Vocabulário do peso ("das notas") | não se aplica (não há rótulo de peso) | **exigida** → retentativa (`_REFORCO_VOCABULARIO_PESO`) → `vocabulario_peso_suspeito` |

A checagem de ancoragem (`_ancoragem_de_peso_ok`) aceita, por grupo: o rótulo
fornecido, **qualquer rótulo mais fraco** (o prompt permite descer de força) ou
o percentual literal. Heurística deliberadamente permissiva — a defesa
principal é a instrução; isto detecta o modo de falha que importa: o narrador
ignorar os pesos e reescrever a narrativa antiga, de grupos equivalentes.

**Fallback (§3[G]):** sem distribuição, tudo isso desaparece sozinho — prompt
histórico, rede de prevalência original ativa, `peso_nao_ancorado` sempre
`False`, render com o disclaimer antigo, frontend sem shares. **Não há flag de
configuração:** a presença do dado é o interruptor.

**Por que a invariante (c) existe (v1.2.1 — defeito corrigido):** os buckets têm tamanhos fixados pela **cota de coleta** — na época 50/20/30 (= 10 válidas × nº de níveis de nota do bucket: 5/2/3), hoje 40/40/40 (v1.9.0) —, que **não** refletem a distribuição real da recepção. *(A v1.9.0 removeu o acidente aritmético mas NÃO a razão da invariante: uma cota, igual ou desigual, continua sendo amostragem, não prevalência.)* A narrativa da v1.2.0, sem a regra (c), inferia prevalência a partir das cotas ("grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada") — as medianas seriam "minoria" em todo filme, para sempre, por construção. A invariante (c) é a **defesa principal**; a telemetria abaixo é a rede de segurança.

**Por que o quantificador virou pré-computado (v1.2.3 — reincidência corrigida pela raiz):** a v1.2.2 tentou corrigir a inflação de quantificadores por INSTRUÇÃO — pedir ao LLM que calculasse a fração e escolhesse o rótulo por uma tabela. Funcionou parcialmente, mas **reincidiu**: na primeira regeneração das 3 narrativas pós-fix, "quase todos"/"praticamente todos" foi aplicado a frações de 65-70% **2 vezes** (a condição de escalada que o próprio changelog da v1.2.2 previa: *"um checador numérico pós-parsing é candidato futuro caso a inflação reincida"*). A correção pela raiz é o **mesmo princípio da v1.1.1** (denominador de `n_reviews_analisadas`): o LLM não decide número nem rótulo numérico — **o código é a autoridade**. `_serialize_output_for_narrator` agora pré-computa `fracao`/`rótulo_quantificador` por tema (`_fracao_e_rotulo`, mapa determinístico em `_rotulo_quantificador` — mesmas faixas da v1.2.2, resolução de sobreposição sempre para o rótulo mais fraco) e os injeta na entrada do narrador; o prompt (d) deixou de pedir cálculo e passou a proibir só usar um rótulo MAIS FORTE que o dado. **Rede de segurança complementar (v1.2.3):** checagem em nível de bucket — se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço; se persistir, `quantificador_suspeito: true`. Deliberadamente restrita a esse quantificador (o único modo de falha observado) — não cobre uso indevido dos demais rótulos.

**Por que o Movimento 1 é condicional à ficha (v1.3.0):** a ficha TMDB é aditiva por design (§3a) — pode faltar (API fora do ar, filme não encontrado, `--no-ficha`). Sem ela não há `sinopse_oficial` para ancorar o Movimento 1, e nada no prompt permite ao narrador inventar uma premissa a partir dos temas de review (violaria (b) FIDELIDADE e a proibição de conhecimento externo). Por isso o prompt instrui explicitamente pular para o Movimento 2 quando a ficha está ausente — mesmo comportamento defensivo do resto do pipeline (buckets `sem_analise` não inventam temas; a ficha ausente não inventa premissa).

O formato de saída `{"narrativa": ..., "consensos_usados": [...]}` reusa os mesmos adaptadores de provider (modo JSON nativo) e o parsing defensivo do §D. Sobre a prosa retornada aplicam-se as **mesmas validações pós-parsing** que fazem sentido para texto livre: **aspas** (remoção mecânica → `aspas_removidas`), **idioma**, **escopo**, **(v1.2.1) prevalência**, **(v1.2.3) quantificador** (ver acima) e **(v1.4.1) vocabulário do peso** — inalteradas pela reestruturação em movimentos da v1.3.0, elas operam sobre o texto final completo, independente de quantos movimentos o compõem. Todas com 1 retentativa combinada (reforço anexado ao prompt); se persistir, aceita e sinaliza a flag correspondente (`idioma_invalido`/`escopo_suspeito`/`prevalencia_suspeita`/`quantificador_suspeito`/`vocabulario_peso_suspeito`). As checagens sobre os campos **declarados** pelo narrador (`consensos_usados`, v1.3.1; `quantificadores_usados`, v1.4.1) entram na MESMA retentativa combinada — o orçamento do narrador continua sendo, no pior caso, 1 chamada + 1 retentativa de JSON + 1 retentativa de validação. Heurísticas **acento-sensíveis** como as demais (rede de segurança; a defesa principal é a invariante/pré-computação do prompt). A narrativa entra no JSON no campo global **`narrativa`** (+ `narrativa_flags` de telemetria).

**Telemetria de `consensos_usados` (v1.3.1, NOVO):** para cada propriedade que o narrador usar no MOVIMENTO 2, o próprio LLM declara `{propriedade, grupos_de_origem, temas_de_origem}` — `grupos_de_origem` restrito a `negativas`/`medianas`/`positivas`, `temas_de_origem` com os nomes de tema EXATOS (copiados do relatório recebido). Esse registro é o **artefato de revisão humana** de cada execução: permite conferir, tema a tema, se o consenso declarado é real (existe nos dados citados) ou inventado — o mesmo tipo de exercício feito manualmente no relatório da v1.3.0 que descobriu o defeito do `the-invite-2026`, agora com o material pronto em vez de precisar recomputar frações à mão.

Validação pós-parsing (código, não substitui a revisão humana): `_consensos_validos` (`synthesize.py`) confere que todo `grupos_de_origem` citado é um dos três nomes válidos E existe no relatório do filme, e que todo `temas_de_origem` citado corresponde a um tema real de algum dos grupos citados naquele item — comparação por igualdade de string com o nome do tema como veio no relatório. Falha em qualquer item → **1 retentativa combinada** com as demais (reforço anexado ao prompt, `_REFORCO_CONSENSOS`); se persistir, aceita a resposta da retentativa e sinaliza `consenso_suspeito: true` em `narrativa_flags` — telemetria visível, não correção silenciosa (mesma política das demais flags do §D2). `consensos_usados: []` é válido por vacuidade (MOVIMENTO 2 pode não ter nenhuma propriedade que passe nos três critérios).

`consensos_usados` é persistido no JSON do filme como campo global (junto de `narrativa`/`narrativa_flags`) e exibido no render de terminal, no tom `narrativo`/`ambos`, como bloco compacto após a prosa ("Consensos do movimento 2: • propriedade — grupos: ... — temas: ...") — visível em toda execução, não só sob demanda.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "Telemetria de `quantificadores_usados` (v1.4.1, NOVO) — o quantificador declarado junto do seu tema")*

#### Invariante de vocabulário do peso (v1.4.1): **notas × reviews**

Duas populações **diferentes** alimentam a narrativa, e confundi-las é uma infidelidade silenciosa:

| | Origem | Denominador | Vocabulário obrigatório |
|---|---|---|---|
| **Rótulo de peso** (`rotulo_peso`, §3[G]) | histograma público de **NOTAS** | todo mundo que **avaliou** o filme | "**das notas**" |
| **Frequência de tema** (`rótulo_quantificador`, v1.2.3) | **REVIEWS COM TEXTO** analisadas (subconjunto) | `n_reviews_analisadas` do grupo | "das **reviews** analisadas" (regra d) |

Regra: ao expressar **peso**, é **OBRIGATÓRIO** dizer "das notas" e **PROIBIDO** dizer "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review, nem sobre quem assistiu sem avaliar. As frequências de tema continuam expressas em relação às **reviews analisadas**. Os dois vocabulários não se misturam. A regra está escrita dentro da própria regra (c) invertida do prompt (variante COM distribuição — sem distribuição não há peso a expressar, e a invariante não existe).

**Checagem barata** (`_vocabulario_peso_ok`, `synthesize.py`), duas passadas literais sobre a prosa, só quando há distribuição:
1. **rótulos inequívocos de peso** (`uma pequena minoria`, `uma minoria`, `uma parcela expressiva`, `a grande maioria`) → inspeciona os ~40 chars seguintes; se aparecer "reviews"/"público"/"espectadores" **antes** de "notas", é violação;
2. **qualquer percentual** (`~79%`) → inspeciona os ~60 chars anteriores, com o mesmo teste.

A passada (2) existe porque **"a maioria" é ambígua**: é rótulo de peso E rótulo de quantificador de tema — e "a maioria das reviews negativas analisadas" é a forma **correta** exigida pela regra (d). Ancorar no percentual (que só acompanha peso, nunca frequência de tema na prosa) desambigua sem flaggar prosa certa. Violação → **1 retentativa** (reforço `_REFORCO_VOCABULARIO_PESO`); se persistir, **`vocabulario_peso_suspeito: true`** em `narrativa_flags`, visível no render.

**Flag `--tom {estruturado,narrativo,ambos}` — MECANISMO DE DESENVOLVIMENTO (não é feature final):** existe para o **teste A/B humano** entre a saída estruturada (atual) e a narrativa durante o desenvolvimento. `estruturado` (default) mantém o comportamento histórico intacto; `narrativo` imprime só a prosa **mas os metadados de coleta e os avisos NUNCA somem** — modo degradado (sem_analise/reduzido) e flags continuam visíveis nos dois tons; `ambos` imprime os dois lado a lado. `narrativo`/`ambos` gastam **+1 chamada LLM** (o narrador). **A v2 consolidará um tom único** após a avaliação humana do A/B; até lá, `--tom` é dev-only. (Atalho de A/B: `--reuse-synthesis` reaproveita a síntese de um JSON já gerado, gastando só a chamada do narrador — para comparar tons sobre a MESMA síntese.)

### [D3] Rotulagem de temas por EIXO — a metade qualitativa da linha (v1.9.14)

O alinhamento por linha precisa de duas metades que vivem em lugares
diferentes do pipeline:

```
Ritmo — arrasta (24/40) | lento mas justificado (11/40) | hipnótico (19/40)
        └── FRASE:  vem dos `temas` de §[D]        └── NÚMERO: vem da
            (o que ESTE grupo diz do eixo)             classificação por
                                                       review (§2.5), somado
                                                       em CÓDIGO
```

Elas não estavam ligadas: os `temas` são texto livre por bucket, a
classificação é por review, e nada dizia que "Ritmo lento e arrastado" é o
eixo `ritmo`. **[D3] é essa ligação, e só ela.**

**Uma chamada por bucket.** Entrada: a lista FECHADA dos 10 eixos com as
definições byte-idênticas às de `scripts/classificar_10.py`, mais os ≤6
temas daquele bucket. Saída: um eixo por tema. Nenhum número entra no
prompt e nenhum número sai dele — [D3] não vê frequência, não vê
denominador e não vê os outros grupos.

**Validação mecânica, não confiança.** O código confere cada rótulo contra a
lista fechada; **o que não estiver nela vira `livre`**. Um eixo inventado
nunca entra no schema — mesmo padrão de verificação em vez de instrução que
a spec aplica desde a v1.2.3.

#### A assimetria de validação, declarada

A classificação de produção (§2.5) passou por auditoria humana de 100
reviews, votação de 3 passadas, precisão e recall medidos **por eixo**, e
duas variantes de prompt comparadas contra o mesmo gabarito com bootstrap
pareado. **[D3] não passou por nada disso.** É um segundo uso da mesma
taxonomia por um prompt que nunca foi medido contra gabarito humano.

Isto está aqui como **ressalva de primeira classe, não nota de rodapé**: o
número da célula tem oito sessões de medição atrás dele; o rótulo que decide
em qual LINHA a célula aparece não tem nenhuma. As duas coisas convivem no
mesmo pixel e não têm o mesmo estatuto.

**A mitigação adotada** é proporcional ao risco e ao tamanho do problema:
são ~50 células nos 3 filmes publicados, e a tabela `tema → eixo atribuído`
é **conferida à mão pelo dono do projeto** antes de publicar
(`resultado/v1914/ROTULAGEM_CONFERENCIA.md`, atualizada na v1.9.15 em
`resultado/v1915/ROTULAGEM_CONFERENCIA.md`). Não é a auditoria de 100
reviews — é muito melhor que publicar sem validação nenhuma, e o que ela
cobrir fica registrado como conferido, não como presumido.

**Reprodutibilidade medida (v1.9.15, Entrega 4).** A conferência da v1.9.14
achou um caso concreto: em `cidade-de-deus`, "Excesso de violência e ritmo
exaustivo" (negativas) foi rotulado `ritmo` e "Excesso de violência"
(medianas) foi rotulado `tom_atmosfera` — mesmo núcleo, eixos diferentes.
Para saber se é caso isolado ou padrão, [D3] foi rodado DUAS VEZES sobre os
MESMOS 54 temas dos 3 filmes publicados
(`scripts/medir_reprodutibilidade_d3.py`): **98,1% dos temas mantiveram o
mesmo eixo entre as rodadas — 1 de 54 divergiu.** É a mesma tema flagrada na
conferência: "Excesso de violência" (`cidade-de-deus`/medianas) oscilou
entre `livre` e `tom_atmosfera`; contando a execução já publicada como uma
terceira amostra independente, o placar é 2 de 3 para `tom_atmosfera` — o
tema está genuinamente numa fronteira, não é ruído aleatório sem direção.

**Leitura: NÃO é a mesma classe de problema que a classificação por review
tinha antes da votação de 3** (26,5% de reprodutibilidade individual medida
em `docs/arquivo-de-estudos/margem-de-lift/ESTABILIDADE_AGREGADA.md` — [D3] está em 98,1%, quase 4× mais estável).
Um tema por bucket em 54 é o ritmo de divergência esperado numa tarefa de
classificação com fronteiras reais entre categorias (§2.5, os mesmos eixos
que saturam ou colidem na classificação por review têm o mesmo efeito aqui).
**Decisão: NÃO implementar votação em [D3]** — o custo seria recorrente por
filme (hoje 1 chamada/bucket, viraria 3), e a taxa medida não justifica.
Revisitar se a fração de divergência crescer com o catálogo.

**O que [D3] NÃO pode fazer:** mudar o número. Se o rótulo põe um tema na
linha errada, a linha erra a FRASE; a frequência daquele eixo continua sendo
a contagem de reviews classificadas, alheia ao que [D3] decidiu. O modo de
falha é de legenda, nunca de aritmética — e é por isso que uma etapa não
calibrada é tolerável aqui e não seria na classificação.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "DUAS POPULAÇÕES DE 40 — UNIFICADAS na v1.9.15")*

### [V] Veredito — a linha de contraste, escrita por LLM sobre briefing determinístico (v1.9.21)

O **veredito** é a linha de 1–2 frases no topo de `filme.html`, entre a ficha
e os bullets: a leitura de UMA frase que a tabela "eixo a eixo" (removida na
v1.9.19) pedia ao leitor para fazer de cabeça. Ele nasceu na v1.9.19 como
TEMPLATE determinístico sobre o lift já computado, zero LLM, e foi corrigido
na v1.9.20 para não mentir por omissão (`eixoDeMaiorFrequencia`). Esta versão
troca o gerador do texto — **o briefing continua sendo código; a redação passa
a ser LLM** — e mantém o template como rede.

> **AVISO DE LEITURA — as contagens de catálogo desta seção são de v1.9.21/22 e
> NÃO descrevem o catálogo de hoje (nota acrescentada em 2026-09-04).**
>
> Esta seção mede repetição, aberturas, conectivos e anti-fabricação sobre uma
> partição de **18 `tematico` / 17 `valorativo`**, que era o catálogo sob a
> margem fixa de 20pp. **A lei por `n` da v1.9.34 (§2.5) mudou a partição, e os
> artefatos JÁ FORAM republicados sob ela.** Conferido varrendo os 35
> `resultado/*.json` em 2026-09-04:
>
> | | §3[V] mede sobre | catálogo publicado hoje |
> |---|---:|---:|
> | `tematico` | 18 | **6** |
> | `valorativo` | 17 | **28** |
> | sem estado (`contraste` ausente) | 0 | **1** (`obsession-2026`) |
> | total | 35 | 35 |
>
> Os 35 carregam `margem.lei = "lift^2 * n >= 2085136/1000000"`, ou seja, todos
> foram gerados sob a lei nova.
>
> **O que isso invalida e o que NÃO invalida.** Continuam válidos: as regras, o
> schema, o contrato do briefing, as validações, a seleção por âncoras, as
> invariantes do prompt e o fallback — nada disso depende de quantos filmes
> caem em cada ramo. **Ficam datadas as MEDIÇÕES por população**: "os 17
> `valorativo`", "14 dos 17 abriam com fórmula de divergência", "`enquanto`
> 14/17 (82%)", a verificação anti-fabricação "nos 17", e a tabela de aceite
> da v1.9.21. Cada uma delas descreve textos que existiam quando foi feita.
>
> **Elas NÃO foram refeitas, e essa é uma pendência de sincronização real, não
> uma correção que esta nota faça:** a republicação da v1.9.34 regerou 16
> vereditos sob briefings novos, e nenhuma das métricas de repetição do estágio
> foi recomputada depois. **Ninguém sabe hoje qual é o padrão de abertura, o
> Jaccard ou a taxa de conectivo do catálogo em vigor** — o que se sabe é que
> os números abaixo não o descrevem. Refazê-las é trabalho de uma sessão de
> medição, não de uma sessão de correção de texto.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "O defeito medido, e por que ele não é do template")*

#### Posição no pipeline, insumo e saída

O estágio roda **na PUBLICAÇÃO, não a cada pageview** — ~35 chamadas por
regeneração de catálogo, não uma por leitor.

```
[D3]/eixos  ──►  [V] veredito  ──►  resultado/<slug>.json
                      ▲                        │
                      │                        ▼
             buckets + ficha        build_data.py ──► frontend/js/data.js
                                                              │
                                                              ▼
                                                     filme.js (render puro)
```

- **Consome:** o dict `output` já montado — `eixos` (obrigatório: sem ele o
  estágio devolve `None` e a chave não é emitida), `buckets`, `ficha`.
  **Nunca reviews brutas** — a mesma fronteira que §D2 estabelece desde a
  v1.2.0, e ela fica escrita aqui por extenso porque é invariante de
  SEGURANÇA, não ponteiro de conveniência:

  > **A FRONTEIRA DO TEXTO BRUTO (invariante, vale para TODO estágio de prosa
  > deste projeto — §D2, §3[V] e as CONDIÇÕES do §0).** Um estágio que escreve
  > prosa recebe **exclusivamente material já validado** — o dict de saída de
  > `build_output` (temas, contagens, `observacao_geral`, `eixos`) mais a
  > `ficha` oficial do TMDB. **NUNCA o texto de uma review.** A garantia é
  > **por construção, não por instrução**: o texto bruto não é serializado na
  > entrada, então o modelo não tem como usá-lo.
  >
  > **Por que ela existe, e são dois riscos distintos.** (1) **Spoiler:** o
  > texto integral de uma review não passou pela camada anti-spoiler de §3[D],
  > e a flag de spoiler do Letterboxd é autodeclarada. (2)
  > **Embelezamento/infidelidade:** com material não contabilizado à mão, o
  > estágio pode "florear" com o que nenhuma frequência sustenta, quebrando a
  > fidelidade aos números. Lendo só o relatório validado, ele **não pode
  > afirmar nada que a camada de baixo não tenha aprovado**.
  >
  > *(Correção de 2026-09-04: aqui havia só o ponteiro "mesma fronteira de §D2
  > desde a v1.2.0". A regra em si vive em §D2, "Decisão de arquitetura", e
  > quem lesse §3[V] sozinho — ou recuperasse só este trecho — ficava com a
  > referência e sem a invariante.)*
- **Depende de** [D3] ter rodado antes, pela mesma razão que o briefing do
  narrador depende: `contraste` vem de lá.
- **Independe de** [D2]: veredito e narrativa não se leem. Regenerar um não
  obriga a regenerar o outro.
- **Grava:** a chave de topo `veredito` (schema abaixo).

**`veredito.spec_version`, e por que o carimbo do FILME não sobe.** O bloco
carrega a própria versão, como `eixos` já faz desde a v1.9.14. Regenerar só o
veredito sobre um JSON existente **não** re-roda coleta, seleção, síntese,
[D3] nem narrativa — e escrever `1.9.21` no `spec_version` de topo afirmaria
que rodou. Mesma política de `VERSAO_COLETOR` (§3[B']): um carimbo que não
corresponde ao que foi executado não é evidência de nada.

> **Consequência registrada, não corrigida nesta versão:** o checkpoint de
> `scripts/publicar_catalogo.py` considera um filme "publicado sob o pipeline
> corrente" quando `spec_version == SPEC_VERSION`. Com `SPEC_VERSION` em
> `1.9.21` e os 35 JSONs em `1.9.16`, aquele script passa a enxergar os 35
> como pendentes. **Isto é correto** — eles de fato não passaram pelo
> pipeline completo da v1.9.21 — mas significa que rodar
> `publicar_catalogo.py` sem `--slug` republicaria o catálogo inteiro. O
> estágio [V] tem harness PRÓPRIO (`scripts/gerar_veredito.py`), que não usa
> aquele checkpoint e não chama coleta/síntese/narrativa.
>
> **O footgun é FECHADO, não apenas registrado (v1.9.21).** Antes desta
> versão, rodar `publicar_catalogo.py` sem argumento era inócuo: os 32 slugs
> default eram todos pulados por `_ja_publicado`. Com a constante em
> `1.9.21`, nenhum é pulado — um comando de uma linha dispara re-scrape de 32
> filmes a 2s por requisição sem paralelismo, e apaga o histórico `passadas`
> do `meta.json` (dívida conhecida, `docs/arquivo-de-estudos/coleta/DIAGNOSTICO_OFFLINE.md`). Caro e
> irreversível para o histórico. `cmd_publicar` passa a **recusar execução**
> quando mais de `LIMITE_LOTE_SEM_CONFIRMACAO = 5` filmes seriam de fato
> republicados, exigindo `--republicar-tudo`, com mensagem que diz **quantos
> e por quê**. O limiar é decisão de produto: acima de um punhado, o comando
> deixa de ser "conserta um caso" e vira "republica o catálogo", e a
> diferença entre os dois é de horas de rede. A guarda conta quem SERIA
> republicado, não o tamanho da lista — passar os 35 com 32 em dia é um lote
> de 3, e passa. **Escopo estritamente este:** o checkpoint em si não muda, e
> a dívida do `passadas` continua aberta.

#### Schema do bloco `veredito`

```json
"veredito": {
  "texto": "<1–2 frases, pt-BR, sem algarismos>",
  "origem": "llm" | "template_fallback",
  "prefixo_codigo": "<string ou null>",
  "provider": "gemini",
  "modelo": "gemini-3.7-flash",
  "n_candidatos": 3,
  "n_chamadas": 3,
  "indice_escolhido": 0,
  "motivo": "melhor_entre_limpos" | "menor_severidade" | "template_fallback",
  "criterio_decisivo": "flags" | "comprimento" | "unico" | "empate",
  "candidatos": [
    {"indice": 0, "n_flags": 0, "flags": [], "n_palavras": 31, "eliminado": false}
  ],
  "flags": [],
  "uso": {"prompt_tokens": 0, "completion_tokens": 0,
          "cache_hit_tokens": 0, "cache_miss_tokens": 0},
  "latencia_s": 0.0,
  "spec_version": "1.9.21"
}
```

`texto` é o texto FINAL, já com `prefixo_codigo` concatenado quando existe —
o frontend renderiza `texto` e nada mais. `prefixo_codigo` fica ao lado como
telemetria de qual parte não veio do modelo.

> *(Correção de registro, 2026-09-04: o campo `modelo` do exemplo dizia
> `gemini-3.1-pro-preview`, que foi o **braço B do A/B da v1.9.21** e não o
> escolhido. Conferido nos 35 JSONs publicados: **34 têm bloco `veredito` e
> todos os 34 carimbam `gemini-3.7-flash`**, que é o que
> `MODELO_POR_ESTAGIO["veredito"]` configura. `origem` nos 34: 33 `llm`, 1
> `template_fallback`. **O 35º filme não tem o bloco**, e isso é a regra de
> §2.5 funcionando — `obsession-2026` fica sem `contraste` pelo piso de
> `n < 10`, e sem `contraste` a chave `veredito` some do JSON.)*

**Telemetria é DIAGNÓSTICO DE PRODUÇÃO, não informação de leitor.** Nenhum
campo além de `texto` chega à tela — mesma decisão já tomada para
`verificacao_narrativa` e `narrativa_selecao`.

#### O contrato do briefing (`veredito.py`, código puro, zero LLM)

**Regra dura: todo número e todo rótulo quantificador que aparece no briefing
é calculado aqui.** O modelo recebe rótulos prontos e nomes de tema prontos;
nunca calcula, nunca arredonda, nunca escolhe intensidade. Mesmo princípio da
v1.1.1 (denominador), v1.2.3 (quantificador) e v1.4.0 (peso).

**Nível do filme:**

| Campo | Origem | Quem calcula |
|---|---|---|
| `titulo`, `ano` | `ficha` (com fallback para o slug) | código |
| `contraste` | `eixos.contraste` | [D3]/`eixos.py` |
| `margem_lift_pp` | `eixos.margem_lift_pp` | `eixos.limiar_pp(n)`, derivado da lei por `n` — **não** uma constante de `config.py` (ver a nota abaixo da tabela) |
| `bucket_dominante` | maior `share_real` dos `buckets` | código |
| `assunto_compartilhado` | ver critério abaixo | código |
| `grupos` | por bucket, tabela seguinte | código |

**Por bucket** (`negativas` e `positivas` sempre; `medianas` **só quando é o
bucket dominante** — o meio nunca é um dos dois lados do contraste):

| Campo | Origem | Quem calcula |
|---|---|---|
| `eixo_maior_lift` + `lift_pp` + `acima_da_margem` | `eixos.linhas[].por_bucket[]` — o eixo e o `lift_pp` de lá; **e desde a v1.9.34 o `acima_da_margem` também vem de lá, LIDO e não recalculado** (§4). Até a v1.9.33 este campo era `lift_pp >= margem` em float, e com a lei por `n` isso passaria a poder divergir da decisão exata | código |
| `eixo_maior_frequencia` + `tema` + `freq_pct` | `mencoes`/`de_n` e `tema` da mesma linha | código |
| `rotulo_quantificador` | `freq_pct` → mapa de faixas | código (`quantificador.py`) |
| `share_pct` | `buckets[].share_real` | histograma (§3[G]) |
| `modo`, `estado_piso` | `buckets[]` | §3[C3] |

Bucket com `estado_piso: "sem_analise"` não empresta eixo nenhum ao briefing
— mesma guarda que `eixoDeMaiorLift`/`eixoDeMaiorFrequencia` já aplicavam.

> **CORREÇÃO DE REGISTRO (2026-09-04): `config.MARGEM_LIFT_PP` NÃO EXISTE.** A
> tabela de nível do filme, acima, dava essa constante como origem de
> `margem_lift_pp`, e ela foi **removida de `config.py` na v1.9.34, de
> propósito**. O comentário que ficou no lugar dela diz por quê, e vale
> repetir: *"o valor histórico e a razão de ele ter caído estão na spec (§2.5,
> 'A margem de 20pp — REGISTRO HISTÓRICO'), não no código, para que ninguém o
> reimporte por engano achando que é o parâmetro em vigor."*
>
> **O que `margem_lift_pp` é hoje:** `round(eixos.limiar_pp(n), 2)` — o limiar
> da lei por `n` resolvido para o `n` daquele filme, **derivado e para
> exibição**. `veredito.py` o carrega para o briefing como rótulo, e
> **nenhuma decisão o lê**: a decisão por célula é `acima_da_margem`,
> calculado em `Fraction` exato por `eixos.py` (§4). Conferido nos 35 JSONs
> publicados: todos carregam `margem.lei = "lift^2 * n >= 2085136/1000000"`.

#### `assunto_compartilhado` — o critério, o piso e a medição

**Critério:** entre os eixos que os DOIS extremos mencionam, o que maximiza
`min(freq_negativas, freq_positivas)`. Desempate por `freq_negativas +
freq_positivas`; persistindo, pela ordem canônica de `taxonomia.EIXOS`.
**Piso: 25% nos dois lados** — abaixo disso o eixo não é "assunto de ambos os
grupos", é ruído que os dois tocaram de passagem. 25% é a fronteira inferior
da faixa `muitos` do mapa de quantificador (§D2 v1.2.3), reusada aqui em vez
de um número novo.

É esse campo que dá substância ao caso `valorativo`: quando nenhum lado tem
assunto PRÓPRIO, o veredito precisa nomear o assunto COMPARTILHADO e dizer
que a divergência é de julgamento.

**Medição sobre os 35 do catálogo (v1.9.21):** todos os 35 têm assunto
compartilhado sob esse critério; nos 17 filmes `valorativo` o `min` fica
entre **40% e 84%**. Exemplos do que o campo produz:

| Filme | Eixo | Tema nas negativas | Tema nas positivas |
|---|---|---|---|
| `talk-to-me-2022` | `roteiro_estrutura` | Protagonista irritante e decisões idiotas | Personagens exasperantes e decisões irracionais |
| `wicked-2024` | `som_trilha` | Músicas genéricas e esquecíveis | Músicas marcantes e bem integradas |
| `shutter-island` | `roteiro_estrutura` | Plot twist previsível ou decepcionante | Roteiro e construção do mistério |

> **LIMITAÇÃO REGISTRADA, não contornada.** O campo `tema` de uma célula só
> existe quando aquele eixo virou BULLET daquele grupo (§2.5, seleção 2+3).
> Em **2 dos 17** filmes `valorativo` — `dune-2021` (`comparacoes`) e
> `the-substance` (`impacto_emocional`) — o eixo compartilhado não tem tema
> nomeado em NENHUM dos dois lados. Nesses casos o briefing carrega o rótulo
> do eixo sem tema, e a substância vem do top-frequência de cada lado. **Não
> se inventa texto para tapar o buraco** — é a mesma política de omissão
> autorizada da v1.4.1: preencher com genérico é pior do que não preencher.

#### A serialização não contém NENHUM algarismo

`serializar_briefing_veredito()` — o texto que efetivamente vai na mensagem
do usuário — emite **rótulos, nunca números**. O dict do briefing carrega
`freq_pct`, `lift_pp` e `share_pct` (para os testes, para a telemetria e para
o template de fallback); a serialização carrega `rotulo_quantificador` e o
booleano `acima_da_margem`.

Duas coisas caem disso, e as duas são deliberadas:

1. **A invariante "zero dígitos na saída" (§ prompt, regra 5) passa a ser
   garantida por CONSTRUÇÃO.** O modelo não pode copiar um número que nunca
   viu.

   > **As duas defesas são independentes, e é preciso saber disso ao mexer
   > em qualquer uma.** A validação `digito` em código continua existindo
   > como **redundância DELIBERADA** — não é sobra da defesa antiga, e não
   > é a defesa primária. Afrouxar a serialização (deixar um número
   > escapar para a mensagem) **não** fica coberto pela validação, porque
   > um número plausível copiado do briefing passaria a existir na saída
   > exatamente onde ela não sabe distinguir invenção de cópia; e remover
   > a validação achando que a serialização cobre **não** fica coberto
   > pela serialização, porque nada impede o modelo de INVENTAR um
   > algarismo que ninguém lhe deu. Remover qualquer uma das duas é
   > mudança de política, não limpeza.
2. **`lift_pp` não chega ao prompt, então "chegou perto" não existe para o
   modelo.** Ver a invariante do limiar binário, abaixo.
3. **O TÍTULO DO FILME também não entra.** Duas razões, e a segunda é a
   forte: (a) `friday-the-13th-2009` se chama "Sexta-Feira 13" — o título
   CARREGA algarismo, e emiti-lo abriria na serialização exatamente o buraco
   que ela existe para fechar (o mesmo falso positivo que a varredura da
   v1.9.20 já tinha investigado no frontend); (b) nomear o filme CONVIDA o
   modelo a usar o que ele sabe sobre o filme, e a invariante 2 proíbe
   contexto externo — **um briefing anônimo torna a fidelidade mais fácil de
   obedecer do que de violar**. O veredito nunca precisou dizer de que filme
   se trata: é renderizado logo abaixo do título na página.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "O limiar é BINÁRIO — nenhuma noção de "quase passou"")*

> **O exemplo perdeu o que o tornava bom, e vale dizer:** ele existia para
> ilustrar um "quase passou" (0,4pp de folga). Sob a lei, `the-godfather` está
> a **13,9pp** do limiar — não é mais um caso de fronteira. A REGRA abaixo não
> depende do exemplo e continua valendo inteira.
>
> **Dívida conhecida, fora do escopo desta sessão (só spec):** a mesma
> ilustração desatualizada aparece num docstring de `veredito.py`
> (*"`the-godfather` falha a margem por 0,4pp"*). Corrigir código não é escopo
> aqui; fica registrado para quem tocar o arquivo.

A observação é **registrada, e nada mais**. Explicitamente NÃO autoriza:

- **alterar a lei da margem** (§2.5), aqui ou em lugar nenhum. É parâmetro a
  montante que alimenta a seleção de bullets inteira, e a constante `144,4` saiu
  do nulo do máximo com a taxa de erro declarada; mexer nela por esta porta
  mudaria o produto sem decisão de produto. *(Até 2026-09-04 esta linha dizia
  "alterar `MARGEM_LIFT_PP`" — a constante foi removida de `config.py` na
  v1.9.34 e proibir mexer no que não existe não protege nada.)*
- **tratar quase-passou como contraste** no briefing ou no prompt. Se o lift
  não atinge a margem, aquele lado **não tem assunto próprio**, e ponto. O
  briefing pode carregar `lift_pp` como número; o prompt não recebe nenhuma
  noção de proximidade e o modelo não pode insinuar contraste a partir dela.

#### As invariantes do prompt

O projeto documenta prompts por extenso. O texto integral de
`PROMPT_VEREDITO` está em `src/espectro24/veredito.py`; as invariantes que
ele codifica, na íntegra:

1. **Papel e público.** Escreve para quem **ainda não assistiu** ao filme e
   está decidindo se assiste. Não é crítica, não é resenha, não é
   recomendação — é o mapa de ONDE as opiniões divergem.
2. **Fidelidade absoluta ao briefing.** Só pode citar assuntos e temas
   presentes no briefing. É PROIBIDO introduzir tema, adjetivo avaliativo
   sobre o filme, ou informação de enredo que não esteja ali.
3. **Anti-fabricação de contraste.** Quando o briefing marca `valorativo`, é
   PROIBIDO afirmar que os grupos falam de assuntos DIFERENTES. A tarefa é
   nomear o assunto COMPARTILHADO e dizer que a divergência é sobre se ele
   funciona. Concordar sobre o que o filme é e discordar sobre se ele
   funciona é um RESULTADO, não uma falta de resultado.

   > **A remissão desta invariante estava quebrada PARA QUEM LÊ SÓ A SPEC, e a
   > correção é enunciar a regra irmã por extenso (2026-09-04).** O texto
   > dizia *"(Mesma invariante 7b de §D2, aplicada a um estágio novo.)"* — e
   > **§D2, nesta spec, não tem invariante 7b**: as do prompt transcrito ali
   > são alfabéticas (a–h), porque o que §D2 transcreve é o narrador ANTIGO.
   > A invariante 7b **existe de verdade**, mas no prompt que a spec nunca
   > transcreveu: `PROMPT_NARRADOR_BRIEFING`, em `briefing.py`, item `7b.
   > CONTRASTE`. Como não há para onde apontar dentro deste documento, ela
   > fica escrita aqui, literal:
   >
   > > *7b. CONTRASTE: quando o briefing trouxer a seção CONTRASTE ENTRE OS
   > > GRUPOS, ela é obrigatória e vale sobre a sua intuição. Se ela disser
   > > que a discordância é de VEREDITO, o movimento 3 precisa dizer isso
   > > explicitamente uma vez — e é PROIBIDO fabricar diferença de assunto
   > > entre os grupos para preencher o movimento. Concordar sobre o que o
   > > filme é e discordar sobre se ele funciona é um resultado, não uma
   > > falta de resultado.*
   >
   > **As duas são a mesma proibição em dois estágios**, e a diferença é só de
   > alcance: em §D2 ela protege o MOVIMENTO 3 de uma narrativa de 250–400
   > palavras; aqui, um veredito de 1–2 frases. Mudar uma sem a outra é o modo
   > de falha que este bloco existe para impedir.
4. **Quantificadores (corrigida na v1.9.22).** O `rotulo_quantificador`
   fornecido é o **único admissível**. Rótulo mais FORTE é PROIBIDO e mais
   FRACO **também** — e é PROIBIDO envolver o rótulo em algo que o desminta
   ("relatos pontuais apontam que a maioria…").

   > **A v1.9.21 dizia "mais fraco é permitido", e essa metade estava
   > errada.** Foi erro de especificação, não de implementação. **Deflação
   > mente sobre o dado exatamente como inflação**, e o §0 — o código é a
   > autoridade sobre quantidade — não distingue direção. Um grupo de 58%
   > descrito como anedota é tão falso quanto um de 40% descrito como
   > "quase todos".
5. **Zero dígitos.** Nenhum algarismo na saída. Nenhuma contagem de review,
   nenhum percentual, nenhuma nota, score ou estrela. Quando o filme tem o
   meio como grupo dominante, o percentual de peso é **prefixado pelo
   CÓDIGO**, fora do texto do modelo.
6. **Anti-spoiler.** Nada de reviravolta, final, morte de personagem ou
   mecanismo central da trama. Os temas do briefing já passaram por esse
   filtro (§3[D]); não os expanda nem os detalhe.
7. **Escopo.** PROIBIDO generalizar para "os críticos", "o consenso", "a
   recepção do filme". Cada grupo é uma perspectiva, nunca uma fatia
   quantificada do público.
8. **Forma.** 1–2 frases, pt-BR, alvo de ~45 palavras, **teto de 55
   palavras**. Sem aspas de citação. Tom seco e informativo, não
   publicitário.
9. **Cautela com amostra pequena (reescrita na v1.9.22).** Quando o
   briefing indica `modo: "reduzido"`, a redação diz isso — mas **a cautela
   é sobre a AMOSTRA (quantas reviews foram analisadas), nunca sobre a
   FREQUÊNCIA (que fatia daquele grupo disse aquilo)**. PERMITIDO: "numa
   amostra pequena", "entre os poucos relatos analisados", "no material
   disponível". PROIBIDO: "impressões pontuais", "relatos isolados",
   "menções esparsas" — isso afirma um TAMANHO, e o tamanho já veio no
   quantificador. Um grupo com amostra pequena continua recebendo o rótulo
   que o briefing deu, com a ressalva sobre a base ao lado.

9b. **Mesmo tratamento para os dois lados (v1.9.22).** Quando o briefing dá
    o MESMO quantificador a quem recomenda e a quem não recomenda, os dois
    recebem o mesmo tratamento textual. É PROIBIDO nomear a frequência de um
    lado e tratar o outro como anedota. O que separa os dois grupos é o que
    eles dizem, nunca o peso que a redação lhes dá.
10. **Limiar binário.** O prompt não recebe `lift_pp` e não tem nenhuma
    noção de "quase atingiu a margem"; um lado sem assunto próprio é um lado
    sem assunto próprio.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[v1.9.22] Deflação, neutralidade do §0, e o padrão de abertura")*

**Métrica nova e permanente — o PADRÃO SINTÁTICO DE ABERTURA.** É o núcleo
do primeiro sintagma nominal (primeiro token de conteúdo fora da classe
fechada), truncado a 5 caracteres, com os **rótulos de quantificador
colapsados em `QUANT`**. Duas decisões, as duas medidas antes de fixar:

- **Sem o verbo.** A definição "núcleo + verbo principal" foi testada e
  descartada: sem analisador sintático o verbo sai por terminação, "está"
  colide com "esta" ao remover acento, e o primeiro verbo finito costuma
  estar dentro do sujeito ("dos que recomendam"). Ela reporta **22 padrões
  distintos contra 7** da definição sem verbo — **parece melhor porque é mais
  ruidosa**, e uma métrica que melhora o número por imprecisão é pior que não
  ter métrica.
- **Quantificador colapsado.** Qual rótulo abre a frase é decisão do CÓDIGO.
  Contar "A maioria…" e "Cerca de metade…" como aberturas diferentes
  creditaria ao modelo uma variedade que é do dado.

**O desempate por abertura, e a política de estabilidade que o torna
admissível.** A frequência do padrão entra na chave de seleção **antes da
brevidade** — âncoras → abertura menos frequente → menos palavras → primeiro
índice —, sobre os candidatos que o best-of-3 já gera, sem nenhuma chamada
nova. O risco era a saída passar a depender da ordem dos filmes; a política
fecha isso:

> O histórico é um **snapshot** dos padrões PUBLICADOS, tirado **uma vez,
> antes de qualquer escrita**, e o filme em geração sai da própria conta.
> Consequências: o resultado não depende da ordem (todo filme deriva do
> mesmo snapshot), e **regenerar um filme isolado vê o mesmo histórico que a
> regeneração completa veria para ele**. Um histórico atualizado no meio da
> execução seria mais eficaz e INSTÁVEL — o mesmo filme sairia diferente
> conforme fosse o primeiro ou o último da fila.

*Bug real achado ao implementar isso, e invisível para os testes que rodavam
contra um diretório de sandbox: o caminho de PRODUÇÃO grava em `resultado/`,
então recalcular o histórico a cada filme faria o segundo ver o veredito novo
do primeiro. O snapshot único é a correção, e há teste de regressão que
escreve por cima no meio do caminho e exige que o histórico não se mexa.*

##### [v1.9.23] A repetição MIGRA de dimensão — observação de método

**A cada correção, a repetição muda de camada, e a métrica vigente captura
exatamente a camada que acabou de ser consertada.** O histórico do estágio
[V], em três versões:

| Versão | Consertou | Métrica que provou | Para onde a repetição foi |
|---|---|---|---|
| v1.9.21 | texto byte-idêntico (19/35) | Jaccard sobre palavras de conteúdo | **abertura** — e o Jaccard não via |
| v1.9.22 | abertura (6 padrões/35) | padrão sintático de abertura | **molde contrastivo** — e o padrão de abertura não via |
| v1.9.23 | — (só mede) | conectivo contrastivo | ? |

**A regra que fica: estender a métrica ANTES de declarar vitória, não
depois.** Uma dimensão não medida não é uma dimensão sem defeito — é uma
dimensão sem número. Cada versão declarou vitória com o número da dimensão
que tinha acabado de instrumentar, e o defeito seguinte foi encontrado por
LEITURA, não por medição. A leitura continua sendo o aceite final; a métrica
serve para que o achado da leitura vire número e não volte.

##### [v1.9.23] Conectivo contrastivo — a métrica, e o que ela NÃO decide


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[v1.9.22] Deflação, neutralidade do §0, e o padrão de abertura")*

#### Best-of-3, validações e seleção

Mesmo padrão de `narrador.narrar()` (§D2, v1.9.11), **reproduzido, não
reusado**. `selecao_narrativa.selecionar()` está acoplado ao formato de três
movimentos — `spans_por_grupo()` ancora no `rotulo_peso` literal, `cobertura()`
conta cláusulas por span de grupo, `ritmo()` exige ≥2 frases. Num texto de
1–2 frases sem rótulo de peso ancorado, esses três critérios nunca desempatam
nada: seria auditoria de aparência, não de fato. `qualidade.py` é reusado no
que se aplica (`tokens_numericos`, `formato_invalido`, `achar_resenha_speak`
+ `carregar_blocklist`, `_normalizar`).

**Validações pós-parsing — em CÓDIGO, nunca só no prompt:**

| Flag | O que reprova |
|---|---|
| `formato_invalido` | invólucro JSON, cerca de código, chaves desbalanceadas (§E2 v1.7.2) |
| `digito` | qualquer algarismo na saída |
| `quantificador_mais_forte` | rótulo acima do fornecido para aquele grupo |
| `tema_ausente` | tema/eixo que não está no briefing |
| `idioma` | saída fora de pt-BR |
| `comprimento` | acima do teto de palavras, ou mais de 2 frases |
| `escopo_generalizado` | "os críticos", "o consenso", "a recepção do filme", "o público" |
| `nota_ou_score` | marcadores de nota/estrela/score |
| `contraste_fabricado` | em filme `valorativo`, afirmação de que os grupos falam de coisas DIFERENTES |
| `cliche` | blocklist de resenha (`dados/blocklist_resenha.txt`) |

**Seleção:** candidato com `n_flags > 0` é eliminado — validação vem antes
de qualquer critério de qualidade, porque um texto que mente com riqueza
continua mentindo. Entre os limpos, **nenhum LLM julga prosa**, como em todo
o projeto: todo critério é contagem.

**Seleção entre candidatos limpos — chave DUPLA.** A primeira proposta desta
sessão foi "o mais curto", e foi **reprovada**: ela otimiza na direção exata
do defeito que a versão veio corrigir. Os 19 vereditos idênticos não eram
longos, eram **vazios** — entre candidatos que passam em todas as validações,
o mais curto tende a ser o mais genérico. A chave é:

1. **PRIMÁRIA — informatividade ancorada.** Quantas **âncoras substantivas
   distintas** do briefing o texto efetivamente nomeia. Mais âncoras vence.
2. **SECUNDÁRIA — brevidade.** Empate na primária desempata por menos
   palavras; empate total, pelo primeiro índice (arbitrário, determinístico).

**Âncora substantiva** = o `assunto_compartilhado` e o eixo de top-frequência
de cada lado, cada um com o conjunto de palavras de conteúdo do seu `tema` e
do rótulo do seu eixo.

Três guarda-corpos, todos obrigatórios:

- **TETO de 2 na chave primária.** Sem teto, o critério premiaria empilhar
  tema atrás de tema até estourar o limite de palavras — trocaria o defeito
  "vazio" pelo defeito "lista". Duas âncoras é o que um veredito de 1–2
  frases comporta.
- **Casamento por PALAVRAS DE CONTEÚDO, nunca por substring do `tema`.**
  Substring exata recompensaria copiar a string verbatim e a saída
  degeneraria em citação empilhada. A regra: normaliza (NFKD sem
  diacríticos, minúsculas, quebra em não-letras), descarta stopwords e
  tokens com menos de 4 caracteres, e compara por **prefixo de 5
  caracteres** — proxy declarado que absorve flexão (`ritmos`→`ritmo`) e
  **subconta** o que não absorve (`lentidão` não casa com `lento`).
  Subcontar é a direção certa: torna a chave primária mais difícil de
  satisfazer, nunca mais fácil. Uma âncora conta como nomeada quando
  `min(2, |palavras da âncora|)` das suas palavras aparecem no texto.
- **A cópia literal é REPROVADA, não premiada.** A validação
  `tema_verbatim` reprova o candidato cujo texto contenha a sequência
  completa de palavras de conteúdo de um `tema` do briefing (só para temas
  com 3+ palavras de conteúdo — um tema de uma ou duas palavras não é
  copiável, é a única forma de nomeá-lo). O modelo tem de dizer o assunto
  com as palavras dele.

**Verificado nos 35 antes de implementar:** nenhum filme fica com menos de 2
âncoras disponíveis, inclusive os dois sem `tema` no eixo compartilhado
(`dune-2021`, `the-substance`) — cada um deles tem, no top-frequência de
algum lado, uma âncora com tema nomeado de verdade. Se algum ficasse com zero
ou uma, a chave primária seria CONSTANTE naquele filme e a escolha cairia
inteira na brevidade — exatamente o critério reprovado.

> **Se a medição da Entrega 7 mostrar que este critério seleciona texto
> EMPILHADO em vez de fluente, ele é o primeiro parâmetro a revisar.** A
> hipótese sob teste é a informatividade ancorada, não a brevidade.

#### O que estas validações DECLARADAMENTE não pegam

Duas delas são proxies, e registrar o alcance é o que impede que "passou nas
validações" seja lido como "está correto":

> **Três falsos positivos MEDIDOS na primeira geração dos 35, e corrigidos
> antes do A/B valer.** O custo de um falso positivo aqui é caro e concreto:
> ele elimina candidatos bons e empurra o filme para `template_fallback` — ou
> seja, **devolve ao leitor exatamente a frase genérica que esta versão veio
> eliminar**. (1) O marcador `tom` casava como SUBSTRING dentro de "tomam",
> "sintoma" e "átomo", reprovando por `tom_atmosfera` um texto que só dizia
> "decisões que eles tomam" — mesma família do bug de substring da v1.6.2
> (`"1%"` casando dentro de `"91%"`), e mesma correção: fronteira de token
> explícita. Marcadores passam a casar TOKEN INTEIRO por padrão, e por
> PREFIXO só quando escritos com `*` (`arrastad*`). (2) `desenvolvimento` saiu
> de `roteiro_estrutura`: "desenvolvimento arrastado" é RITMO,
> "desenvolvimento dos personagens" é ROTEIRO, e um marcador que casa nos
> dois não discrimina nada — custou `hereditary`. (3) `incomod*` saiu de
> `impacto_emocional`: incômodo é como se descreve qualquer coisa de que não
> se gostou, inclusive uma personagem irritante, que é `roteiro_estrutura` —
> custou `pearl-2022`. Os três viraram teste de regressão.

- **`tema_ausente` detecta EIXO, não tema.** O eixo tem vocabulário fechado
  (10 itens, §2.5) e um `tema` não tem; checar tema a tema exigiria casamento
  por SIGNIFICADO, que só um segundo LLM faz — e este projeto não põe LLM
  para julgar saída de LLM. Consequência: um texto que invente um detalhe
  DENTRO de um eixo que o briefing cita passa. A rede que resta contra isso é
  a fidelidade pedida no prompt e a leitura humana do aceite.
- **`contraste_fabricado` é por MARCADOR DE FRASE.** Ela pega a afirmação
  explícita ("falam de coisas diferentes", "discordam sobre qual é o
  assunto"); não pega uma insinuação construída só pela estrutura da frase.
  O que fecha boa parte da folga é indireto e vale registrar: num filme
  `valorativo` o briefing costuma ter pouquíssimos eixos, então nomear um
  segundo assunto normalmente já trip `tema_ausente`. **A verificação de
  aceite dos 17 `valorativo` NÃO usa esta validação** — usaria a mesma
  checagem para se auto-aprovar. Ela usa uma lista de marcadores
  independente e mais larga, mais leitura humana dos 17 textos.

**Fallback obrigatório, em dois degraus:**

1. Nenhum candidato limpo → o de **menor severidade** entra num retry
   direcionado, com as flags disparadas explicadas (mesma mecânica do retry
   de §D2).
2. Esgotadas as tentativas sem candidato limpo → o filme cai no **TEMPLATE
   DETERMINÍSTICO** da v1.9.19/v1.9.20, que permanece no código, e
   `origem` grava `template_fallback`.

**Nunca fica sem veredito; nunca publica veredito inválido.** O template é a
rede, e é a mesma rede que o frontend usa para JSON antigo (abaixo).

#### Persistência e render

`build_data.py` copia o JSON de resultado inteiro e verbatim (menos
`origem_paginas`), então a chave nova viaja para `frontend/js/data.js` sem
nenhuma edição naquele arquivo.

Em `filme.js`, `veredictoBlock()` passa a preferir `f.veredito.texto` quando
existe. **A função `veredito()` NÃO é deletada** — vira o fallback de render
para filme sem o campo novo (compatibilidade com JSON publicado antes desta
versão) e continua sendo a rede que o estágio [V] usa em `template_fallback`.

> **`teste-degradado` fica DELIBERADAMENTE sem o campo `veredito`.** O filme
> sintético de `build_data.py` existe para exercitar os caminhos que os 35
> reais não têm; a partir desta versão ele exercita também o **fallback de
> render por compatibilidade**. Não é esquecimento — está registrado aqui e
> no comentário do próprio `_filme_degradado()`, porque sem isso a próxima
> pessoa a mexer no arquivo "conserta" a ausência e apaga a cobertura.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "O veredito deixa de ser 100% determinístico — o registro honesto")*

#### Modelo — configurável, nunca hardcoded, nunca alias

Chave `"veredito"` em `PROVIDER_POR_ESTAGIO` e `MODELO_POR_ESTAGIO`
(`config.py`) — único ponto de configuração, resolvido por
`synthesize.provider_do_estagio`/`modelo_do_estagio`, passando pelo adaptador
e pelo guard-rail de §3[D].

**Inventário da chave, consultado na API (não de memória), 2026-08-25:** o
tier `pro` disponível é **`gemini-3.1-pro-preview`** (`version:
3.1-pro-preview-01-2026`) e não existe tier acima dele. O flash mais recente
é `gemini-3.7-flash` (`3.7-flash-08-2026`), **sete meses mais novo que o
único pro disponível**. `gemini-pro-latest` existe e é REJEITADO por política
(v1.9.10: alias é alvo móvel — comparação não reproduzível, preço não
ancorável).

Tensão registrada: a comparação de modelos da v1.9.10 mediu
`gemini-3.1-pro-preview` PIOR que `gemini-3.7-flash` no narrador (2 flags
contra 1, ~10× o custo), em amostra de 3 filmes. Resolvida do jeito que este
projeto resolve as coisas — **por medição**: o A/B da v1.9.21 roda o critério
de aceite INTEIRO nos dois braços (as três métricas de repetição, taxa de
flag, taxa de `template_fallback`, os 20 textos do ramo na íntegra por
modelo, e a verificação anti-fabricação nos 17 por modelo), com briefing,
prompt, best-of-3, validadores e ordem de filmes IDÊNTICOS — a única variável
é o modelo. **Conformidade não decide sozinha:** um modelo pode passar limpo
em todas as validações e ainda produzir 35 vereditos corretos, insossos e
intercambiáveis, que é exatamente a falha que esta versão existe para evitar.
Empate em qualidade legível desempata por custo, e aí o flash vence. O
default efetivo é decisão do dono do projeto lendo os textos, registrada no
changelog.


### [CD] CONDIÇÕES DE DECISÃO — o estágio que o §0 escondia

*(Movido para cá na reestruturação de 2026-09-04. Este texto vivia inteiro
dentro do §0, como um bloco de citação chamado "TERCEIRA EXCEÇÃO DELIBERADA" —
era a especificação inteira de um estágio em produção, 257 condições no ar,
sem seção própria em §3. O texto **não foi reescrito**: é o mesmo do §0.
O contrato do briefing, as validações e o schema do bloco publicado continuam
**não especificados** — pendência registrada em `ABERTO.md`.)*

> **TERCEIRA EXCEÇÃO DELIBERADA — as CONDIÇÕES DE DECISÃO, e o produto passa a
> RECOMENDAR onde antes só RELATAVA (v1.9.35).** Decisão do dono do projeto,
> tomada depois de duas rodadas de estudo de viabilidade
> (`docs/arquivo-de-estudos/condicoes-de-decisao/DESENHO_CONDICOES_DE_DECISAO.md`, `docs/arquivo-de-estudos/condicoes-de-decisao/MEDICAO_CONDICOES_DE_DECISAO.md`,
> `docs/arquivo-de-estudos/condicoes-de-decisao/MEDICAO_CONDICOES_R2.md`) e de feedback de uso real.
>
> **O QUE MUDA, e é uma frase deste documento que deixa de valer.** O §3[V]
> abre dizendo que o veredito *"não é crítica, não é resenha, **não é
> recomendação** — é o mapa de ONDE as opiniões divergem"*. A partir desta
> versão isso continua verdadeiro **do veredito** e **deixa de valer para o
> bloco de CONDIÇÕES**, que é recomendação condicional por construção:
>
>     Vale a pena se você...    quer um retrato íntimo, não o estadista
>     Talvez evite se você...   quer rigor histórico
>
> Não há como registrar isto de outro jeito: o produto passa a dizer ao leitor
> **em que caso assistir**, e não apenas o que as pessoas acharam. É uma
> mudança de NATUREZA, aceita conscientemente, e não uma extensão que o
> documento possa fingir que já estava prevista.
>
> **A RAZÃO, e ela sai deste mesmo §0.** O público-alvo declarado é *"pessoa
> que ainda NÃO assistiu ao filme"*, decidindo se assiste. **Relato
> perfeitamente neutro que não ajuda a decidir falha com o público que este
> parágrafo nomeia** — a neutralidade é um meio para que a decisão seja do
> leitor, nunca um fim que a substitua. E há um segundo argumento, medido:
> em `hereditary` o veredito não menciona *Atuações* (20 de 40) nem *Atmosfera
> e tensão* (15 de 40), os dois temas mais citados do grupo que responde por
> 80% da recepção, porque o veredito nomeia o assunto COMPARTILHADO; as
> condições os nomeiam. O formato novo carrega informação que o antigo
> estruturalmente não alcança.
>
> **O QUE SUSTENTA A EXCEÇÃO — três garantias, e nenhuma é opcional.**
>
> 1. **PROVENIÊNCIA VISÍVEL.** Toda condição carrega o `tema` de origem, e a
>    citação é verificável por máquina contra a lista de temas daquele filme.
>    Condição que não puder ser ancorada não é escrita.
> 2. **SELEÇÃO DE TEMA EM CÓDIGO.** O modelo não escolhe sobre o que falar. A
>    rodada 1 mediu o modelo divergindo da ordem de frequência em **14 de 16**
>    casos e descartando, em `the-godfather`, o terceiro tema mais citado do
>    grupo. A fronteira do §3[V] — *"o código decide O QUÊ; o modelo decide
>    apenas COMO ESCREVER"* — vale aqui **integralmente**.
> 3. **LEITURA HUMANA DE 100% ANTES DE PUBLICAR.** Nenhuma condição vai ao ar
>    sem passar pela leitura do dono, condição a condição, contra o tema e a
>    paráfrase. Não é amostra: é a população. *"Qualidade incontestável"* não
>    sai de validador.
>
> **O QUE NÃO MUDA, e a lista é fechada:**
>
> - **nenhuma nota, score, estrela ou número-síntese** do filme, em lugar
>   nenhum (§1, intocado);
> - **zero algarismo escrito pelo modelo** — todo número do bloco é
>   concatenado pelo CÓDIGO, fora da saída dele;
> - **quantidade é do código.** O modelo é proibido de escrever "a maioria",
>   "alguns", "poucos"; o rótulo vem de `quantificador.fracao_e_rotulo` e é
>   exibido ao lado da frase;
> - **anti-spoiler** (§3[D]): os temas já passaram pelo filtro e não podem ser
>   expandidos;
> - **a neutralidade ESTRUTURAL entre os grupos.** Cota 40/40/40 literal,
>   mesma margem para os dois lados, mesmos bullets, mesmo espaço. O bloco de
>   condições **não** reordena, apaga nem encolhe nada do que já existe.
>
> **A VIA DE REVERSÃO, barata de propósito.** O veredito **continua existindo
> em código e continua sendo gerado** — não é substituído nesta fase (ver
> "FASE 1", abaixo). Reverter a exceção é trocar o que a página **renderiza**,
> não reprocessar corpus: nenhuma coleta, nenhuma síntese, nenhuma
> classificação depende dela. O custo de errar foi desenhado para ser baixo
> antes de a aposta ser feita, exatamente como no rename HATERS/MIXED/FANS.
>
> **FASE 1 — COEXISTÊNCIA, não substituição, e a pergunta fica aberta.**
> Condições, veredito e bullets convivem na mesma página. É decisão de
> produto, e tem duas razões de arquitetura que valem registro:
>
> - **os bullets põem a EVIDÊNCIA na mesma tela da afirmação.** Se uma
>   condição enganar, o bullet logo abaixo a contradiz — e foi assim que o
>   pior caso conhecido (`napoleon`/batalhas) se tornou visível;
> - **o veredito carrega o que as condições não têm.** Ele diz *"numa amostra
>   pequena"* e traz o rótulo de quantificador dentro da prosa. Enquanto o
>   prefixo de peso do bloco de condições não estiver medido em uso, o
>   veredito é a rede.
>

> *(→ justificativa, medição e histórico desta regra: `ABERTO.md` — "0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO")*

> **[v1.9.36] O ANTI-SPOILER PRECISOU SER REAVALIADO, e o achado é sobre ESTE
> parágrafo.** A exceção acima lista o anti-spoiler entre os não-negociáveis e,
> na mesma frase, aprova a mudança de natureza (recomendar em vez de relatar).
> **As duas metades não foram cruzadas** — ninguém perguntou o que a mudança
> de natureza faz com o anti-spoiler. A leitura de população inteira da rodada
> 3 respondeu: **5 das 7 condições marcadas para reescrita eram spoiler**, e
> nenhuma delas expandia o tema.
>
> **O mecanismo é do FORMATO, não do modelo.** O filtro de §3[D] roda sobre os
> TEMAS e continua correto; o que muda é a FORÇA ILOCUCIONÁRIA. O bullet
> *"Monólogo final"* **relata** o que as pessoas comentaram; a condição *"vale
> a pena se você espera um monólogo final devastador"* **instrui** o leitor
> sobre o que aguardar. Mesmo conteúdo, ato de fala diferente — e é o segundo
> que estraga o filme.
>
> **A regra que passa a valer, e a unidade que ela protege é nova:**
>
> > É proibido usar desfecho, reviravolta, ponto de chegada de arco, morte,
> > revelação final ou qualquer informação cujo valor dependa de o espectador
> > ainda não conhecê-la **como motivo para recomendar ou desaconselhar**. A
> > regra vale mesmo quando o tema de origem é válido e mesmo quando a review
> > menciona o elemento. **A unidade a proteger é a CONDIÇÃO PUBLICADA, não o
> > tema.**
>
> **A PRECEDÊNCIA entre as duas regras novas, porque elas se cruzam.** O
> anti-spoiler empurra para ABSTRAIR; o controle de especificidade proíbe
> abstrair além do que a paráfrase sustenta. **O anti-spoiler REBAIXA o teto
> de abstração disponível** — e se a única formulação sem spoiler já não tem
> lastro pleno, a resposta é **ABSTER-SE**, nunca escolher a menos pior.
> Lastro nunca é sacrificado para caber numa regra de forma.
>


### [F] Ficha do filme (TMDB) — v1.3.0

**CONTRATO DE IDENTIDADE — v1.9.49, completado pela correção de corpus da v1.9.50 (prevalece sobre a resolução histórica descrita abaixo).** A página canônica do Letterboxd fornece `production:name`, ano e `data-tmdb-id`; os três passam a ser extraídos juntos e persistidos em `meta.identidade_letterboxd` nas coletas futuras. O título nunca mais é derivado do slug para decidir qual ficha publicar. Sem título canônico ou sem ID direto, o resultado é `ficha: null` com `ficha_indisponivel` explícito — ausência é aceitável, substituição silenciosa não é.

O ID do Letterboxd é a fonte primária e leva diretamente a `GET /movie/{id}`; popularidade não decide identidade. Não existe associação manual em vigor. A exceção criada na v1.9.49 para `obsession-2026` foi removida na v1.9.50: aquela URL é realmente o curta de Jackson Treadway (`1615708`) e não pode fornecer o corpus do longa. O objeto editorial correto vive em `obsession-2025`, cuja própria página declara Curry Barker, 2025 e `1339713`. A guarda de identidade da ficha não substitui uma guarda de identidade da fonte das reviews.

**Retirada auditável de corpus — v1.9.50.** Um bruto comprovadamente associado à obra errada não é apagado: permanece em `dados/bruto/` como evidência do defeito, mas `classificar_10.montar_amostra()` o exclui por uma lista explícita. `votacao_3.cmd_consenso()` cruza os passes append-only com o conjunto de filmes da amostra vigente, impedindo que um filme retirado ressuscite sem apagar extensões de cobertura ainda válidas dos filmes ativos. Para `Obsession`, as 19 reviews analisadas do curta foram substituídas por 136 reviews classificadas do longa (120 da amostra base mais 16 necessárias para cobrir exatamente a seleção de produção); os três buckets publicados têm 40 reviews.

Depois dos detalhes, o título canônico precisa ser IGUAL — após normalizar caixa, pontuação e diacríticos — a pelo menos um membro de `{original_title, title pt-BR, title en-US, alternative_titles}`. Nunca há substring nem pontuação de similaridade. A chamada en-US só acontece se o conjunto já disponível não casar, cobrindo títulos internacionais como `Parasite` contra `기생충`/`Parasita`. `duracao_compativel_com_longa` permanece como uma segunda checagem independente: abaixo de 40 minutos ou sem duração, a ficha inteira é recusada.

**Ano, decisão do dono:** quando o ID direto prova a obra, o ano editorial do Letterboxd prevalece no campo publicado. Divergências não somem: `ficha.identidade` conserva `ano_letterboxd`, `ano_tmdb` e `ano_divergente`. É o caso correto de `talk-to-me-2022`: Letterboxd 2022, TMDB 2023, `tmdb_id=1008042`. A tolerância histórica de ano continua apenas no caminho legado, que não é usado pelo pipeline de produção.

**Cache:** uma ficha só é hit para o caminho de produção se trouxer `identidade.versao=1`, `status=validada`, o mesmo slug, ID escolhido e fonte da decisão. Todas as 35 entradas existentes foram medidas sem esse selo e viram miss automaticamente; uma resposta recusada não é cacheada como ficha válida. A evidência registra ainda qual título TMDB casou e, quando aplicável, o override inteiro.

**Fronteira downstream:** o CLI zera `ficha` antes de narrativa/render e persiste o motivo da recusa. Assim, título, sinopse, imagens e duração reprovados não chegam ao narrador, ao frontend nem ao briefing do veredito. As condições de decisão foram verificadas no código: são derivadas de eixos/buckets e não recebem título, ano ou ficha; por isso uma correção de ficha não autoriza regenerá-las.

*Histórico anterior, mantido para explicar a evolução e os defeitos que levaram ao contrato atual:*

Etapa **aditiva e independente** do resto do pipeline (`ficha.py`): dado o título/ano do filme (derivados do slug por default — `titulo_ano_de_slug`, com override via `--titulo`/`--ano` no CLI para os casos em que o slug não carrega ano, ex. `cure`), busca a ficha técnica na API pública do TMDB (`api.themoviedb.org/3`).

**Resolução do ID:** `GET /search/movie?query=<título>&language=pt-BR[&year=<ano>]`. Quando `ano` está disponível, é usado tanto como parâmetro de busca quanto para desambiguação pós-resposta: entre os candidatos com `release_date` no ano pedido, prefere o de maior `popularity` do TMDB — **não** o primeiro da lista. Necessário porque títulos comuns podem devolver mais de um candidato do MESMO ano (ex. "The Invite" tem múltiplas entradas no TMDB; "Cure" 1997 devolve o filme de Kiyoshi Kurosawa E um documentário obscuro do mesmo ano) — a ordem da API não é por relevância quando o filtro de ano está ativo. Medido ao vivo na regeneração da v1.3.0: escolher o primeiro resultado do ano pegou o documentário (`popularity=0.28`, 1 voto) em vez do filme correto (`popularity=3.79`, 820 votos); corrigido para desempate por popularidade antes da entrega.

**Resolução de ano confiável (v1.7.0) — Tarefa 1.** Defeito real: `espectro24 --slug cure` sem `--ano` desambiguava só pelo TÍTULO (nenhum ano para filtrar), e o TMDB devolveu como único candidato "The Cure" (2026, dir. Nancy Leopardi) — um filme completamente diferente — sem nenhum aviso. A cadeia de resolução do ano passa a ter três degraus, nesta ordem, cada um só tentado se o anterior não resolveu: **(a)** sufixo `-YYYY` do slug (`titulo_ano_de_slug`, já existia); **(b)** se ausente, **1 requisição** à página principal do filme no Letterboxd (`resolver_ano_letterboxd`, `ficha.py`) — mesmo `fetcher`/cache/headers/delay do resto do pipeline, extrai o ano do link `/films/year/YYYY/` ou do `<meta property="og:title">` (formato "Título (YYYY)"); falha de rede/ausência de ano → `None`, nunca levanta; **(c)** se AINDA assim indisponível, a ficha **não é buscada** — o pipeline segue sem ela (`output["ficha"] = None`, `output["ficha_indisponivel"] = "ano_desconhecido"`) em vez de arriscar a desambiguação cega que causou o defeito. O campo `ano_fonte` (`"slug" | "letterboxd" | "argumento"`) entra na própria ficha, sempre visível.

**Guarda de sanidade — ano divergente descarta a ficha inteira (v1.7.0, Tarefa 1.2).** Mesmo com ano resolvido, o TMDB pode devolver o candidato errado quando NENHUM resultado da busca tem `release_date` no ano pedido (o código então cai para o primeiro resultado da lista, que pode ser de qualquer ano — o próprio modo de falha do defeito real do `cure`). Depois de montar a ficha, se o ano esperado (nunca o do próprio resultado do TMDB — seria circular) divergir do `ano` da ficha em mais de 1, a ficha inteira é DESCARTADA: `buscar_ficha` retorna `(None, aviso, {"motivo": "ano_divergente", "esperado": X, "recebido": Y})`, e o CLI persiste esse dict em `output["ficha_descartada"]`. Melhor nenhuma ficha do que a ficha de outro filme. A ficha descartada por esse motivo NÃO é cacheada como "não encontrado" — uma nova tentativa (ex. com um título mais preciso) não fica travada numa rejeição antiga.

**Detalhes:** `GET /movie/{id}?language=pt-BR&append_to_response=credits`. Extraídos: título pt-BR (`title`), sinopse oficial (`overview`), gêneros (`genres[].name`), duração (`runtime`), diretor (primeiro `credits.crew[]` com `job == "Director"`), ano (`release_date[:4]`).

**Imagens — PÔSTER e backdrops (v1.9.29).** A mesma chamada de detalhes passa a pedir `append_to_response=credits,images&include_image_language=pt,null`. **Custo marginal de rede ZERO** — nenhuma requisição nova, `images` entra no `append_to_response` que já trazia `credits`.

**`include_image_language` é obrigatório, e o valor é `pt`, NÃO `pt-BR`.** Duas medições ao vivo (2026-08-27) sustentam as duas metades da frase. (a) *Obrigatório:* `language=pt-BR` filtra também o bloco `images`, e a esmagadora maioria dos backdrops não declara idioma — sem o parâmetro o campo volta VAZIO para filmes com pouca cobertura pt-BR e o sintoma parece "este filme não tem imagens". Medido: `eighth-grade` 1 pôster / **0 backdrops** sem o parâmetro contra 2 / 18 com ele; `the-invite-2026` 4 / **0** contra 10 / 21; o curta experimental (id 1079736) **0 / 0** contra 1 / 0; `the-godfather` 6 / 4 contra 21 / 102. (b) *`pt`, não `pt-BR`:* o parâmetro aceita códigos **ISO-639-1**, e um código de LOCALIDADE é descartado em **silêncio** — com `pt-BR,null` só o degrau `null` sobrevive. O sintoma não é um erro, é um dado faltando sem aviso: dos 9 filmes sondados, **7** (`aftersun`, `anatomy-of-a-fall`, `cats-2019`, `cure`, `hereditary`, `the-northman`, `wonka`) ficaram **sem as dimensões do pôster** com `pt-BR,null`, porque o `poster_path` que o TMDB escolheu é uma arte `iso_639_1='pt'` que o filtro tinha jogado fora; com `pt,null`, nenhum ficou.

**O pôster é o `poster_path` do PRÓPRIO TMDB — a cascata não foi reimplementada, e isso foi MEDIDO antes de decidir.** A política pedida (pt-BR → arte sem idioma → idioma original → melhor avaliado) já é o que aquele campo entrega: ele é sensível a `language`. Medido: `napoleon-2023` devolve `/2UY2xfk…` (`iso_639_1='pt'`) em pt-BR e `/ytFOXyg…` em en-US — a localidade é respeitada; o curta experimental, que só tem arte SEM idioma, devolve a mesma imagem nas duas localidades — o degrau neutro também. Reescrever a cascata em código seria refazer, com menos informação, uma escolha que a API já faz — e divergir dela em silêncio no dia em que ela mudasse de critério.

**As DIMENSÕES, essas, o campo não traz** — e são obrigatórias para o frontend reservar a proporção antes de carregar (§3[E]). O `poster_path` escolhido é procurado dentro de `images.posters`, que traz `width`/`height` reais. Elas **não são sempre 2:3**: medido no catálogo, `aftersun` é 1632×2449 (0,666) e o curta experimental é 505×750 (0,673). Se o caminho não aparecer na lista, as dimensões ficam ausentes e o frontend cai na razão padrão — ausência é estado válido, nunca erro.

**`backdrop_paths[]` — a LISTA continua coletada e não percorrida; o
ESCOLHIDO passa a ser renderizado (v1.9.30).** Teto de **10** por filme
(`TETO_BACKDROPS`), na ordem que a API devolve. **Até a v1.9.29 nenhum
backdrop era renderizado**, e a razão registrada era esta: o TMDB não
garante que um backdrop seja livre de spoiler, e *"0 spoilers para quem
ainda não assistiu"* é a promessa central do produto (§0). **Esse fato
continua verdadeiro; o que mudou foi a decisão sobre ele.** Na v1.9.30 o
dono do projeto decidiu, com o trade-off explicitamente na mesa, abrir a
página do filme com **um** backdrop, sem curadoria de spoiler — **exceção
explícita ao §0**, registrada por extenso em §3[E], "O BACKDROP no topo da
página do filme". **Não existe galeria**, e a distinção não é retórica: a
lista continua sendo dado guardado que arquivo nenhum do frontend percorre;
o frontend lê `backdrop_path`, o campo do escolhido.

**A ESCOLHA É DO CÓDIGO, por uma ORDEM TOTAL (v1.9.30).** Ao contrário do
pôster — onde a cascata pedida já era o que o `poster_path` da API entrega —
aqui não há nada para reaproveitar: o TMDB não expõe campo de topo para "o
melhor backdrop" nem para "a arte sem texto". `_ordem_imagem`/`_melhor`
(`ficha.py`) ordenam por **(1)** sem texto sobreposto (`iso_639_1 is None`,
preferência e não filtro), **(2)** `vote_average` desc, **(3)** `vote_count`
desc, **(4)** `width` desc, **(5)** `file_path` asc. O último degrau é o que
fecha a ordem total. A escolha sai de dentro de `backdrops[:TETO_BACKDROPS]`
— o `backdrop_path` é sempre um dos itens de `backdrop_paths[]`, e isso é
travado por teste. Racional degrau a degrau, com as três medições que o
sustentam, em §3[E].

**O PÔSTER SEM TEXTO (v1.9.30)** — `poster_sem_texto_path` e dimensões: a
melhor arte de `images.posters` com `iso_639_1: null`, pela mesma ordem.
**Aqui o `iso_639_1 is None` é FILTRO, não preferência:** arte com idioma
declarado tem texto sobreposto por definição, e devolvê-la neste campo seria
devolver a coisa que ele existe para evitar. Campo próprio, **aditivo**: não
substitui `poster_path`. Medido nos 35: **todos têm**; em 1
(`talk-to-me-2022`) coincide com o próprio `poster_path`.

**CUSTO MARGINAL DE REDE ZERO, confirmado.** Os dois campos novos saem do
**mesmo bloco `images`** que a v1.9.29 já pedia, com o mesmo
`include_image_language=pt,null` — nenhuma requisição nova, e o teste
`test_os_campos_novos_nao_custam_UMA_requisicao_a_mais` trava isso contando
as chamadas a `/movie/{id}`.

**As DIMENSÕES do backdrop vêm junto**, pelo mesmo motivo das do pôster: sem
elas o frontend não reserva a proporção antes de carregar e o ganho de CLS
zero da v1.9.29 regride — e aqui regrediria **pior**, porque a caixa é mais
alta (§3[E], a tabela de medição). Elas vêm da própria entrada de
`images.backdrops`, que traz `width`/`height`; não são todas 16:9 (medido:
`eighth-grade` é 3500×1969).

**RASTREABILIDADE — `tmdb_fetched_at`, e vale para TODOS os campos derivados do TMDB**, não só as imagens: título, sinopse, diretor, gêneros, duração, pôster e backdrops vêm todos da mesma resposta, no mesmo instante, e um carimbo por campo seria a mesma data repetida sete vezes. **Por que ele existe:** os termos de uso da API do TMDB proíbem **cachear por mais de 6 meses** qualquer informação obtida através dela, e o projeto guarda dados de ficha **indefinidamente** em `resultado/*.json` desde a v1.3.0. **Isto NÃO é problema novo criado pelos pôsteres — é uma limitação PRÉ-EXISTENTE que os pôsteres tornam visível.** Esta versão **não** constrói cache, revalidação, expiração nem coleta de lixo, deliberadamente: a entrega é só a data de obtenção, que é o que torna uma política de revalidação possível depois. Sem ela não há sequer como saber o que está vencido. A intenção fica registrada aqui; a implementação é de outra versão.

**O TMDB não estende nenhum direito sobre as imagens.** O copyright dos pôsteres é dos estúdios e distribuidores; o TMDB apenas hospeda e declara não reivindicar propriedade sobre as imagens da API. Nenhum binário é baixado ou versionado (§3[E]): o JSON guarda só `file_path`, e a imagem vem do CDN.

**Cache de ficha de uma versão anterior — a checagem de COMPLETUDE.** Uma entrada gravada antes de uma versão que acrescenta campo de imagem não tem esse campo. Devolvê-la como está produziria o pior sintoma possível — *"este filme não tem pôster"*, *"não tem backdrop"* — para um filme que tem, sem nenhum aviso. Uma entrada **incompleta** conta como **MISS** e é refeita por cima. Não é expiração (que o projeto continua não construindo, por decisão); é uma entrada de formato antigo sendo reconhecida como incompleta.

**[v1.9.30] A checagem deixou de ser o `tmdb_fetched_at` da v1.9.29 e passou a ser a LISTA de chaves que a versão corrente escreve (`_CHAVES_COMPLETUDE`), e a lição vale registrar porque ela quase mordeu.** A regra da v1.9.29 olhava só o carimbo — e as 35 entradas em cache **já o tinham**. Mantida como estava, esta versão teria devolvido `backdrop_path` e `poster_sem_texto_path` ausentes, em silêncio, para os 35: o defeito exato que aquela regra existia para evitar, repetido um degrau adiante. É **presença de chave**, não valor verdadeiro: `backdrop_path: None` é resposta válida (filme sem backdrop) e não pode forçar uma requisição nova a cada execução. **Ao acrescentar campo de imagem, acrescente à lista.**

**Campos de imagem na ficha:** `tmdb_id`, `tmdb_fetched_at`, `poster_path`, `poster_largura`, `poster_altura`, `backdrop_paths[]` (v1.9.29) e — **v1.9.30** — `backdrop_path`, `backdrop_largura`, `backdrop_altura`, `poster_sem_texto_path`, `poster_sem_texto_largura`, `poster_sem_texto_altura`. **Aditivos por design, como toda a ficha desde a v1.3.0:** qualquer falha (rede, HTTP, filme sem imagem, chave ausente) nunca bloqueia coleta, publicação ou render. **Ausência de pôster é estado válido, não erro.**

**Retrofit dos 35 — `scripts/enriquecer_ficha.py` (v1.9.29).** Os filmes já publicados ganham os campos novos **sem re-rodar o pipeline**: harness próprio, no espírito de `scripts/gerar_veredito.py` (v1.9.21) e da trava por teste da v1.9.25. Ele lê o JSON em disco, faz UMA consulta ao TMDB e grava só as chaves acima dentro do bloco `ficha`. Não chama coleta, seleção, classificação, verificação, síntese, [D3], narrativa nem veredito; **não passa pela guarda de lote de `publicar_catalogo.py` (`LIMITE_LOTE_SEM_CONFIRMACAO = 5`) e não deve — e também não a contorna:** publicar continua inalcançável dali, inclusive por caminho indireto. `tests/test_enriquecer_ficha.py` trava as quatro coisas substituindo os pontos de entrada por `pytest.fail` e comparando o documento campo a campo. Ele carrega ainda uma **guarda de identidade**: reconsultar o TMDB reabre a desambiguação que o pipeline já fez, então se a resposta descrever outro filme (título, ano ou diretor divergentes) o filme é abortado sem gravar — melhor ficar sem pôster do que colar o pôster de outro filme numa página publicada. Ela disparou de verdade em `mother-2017` e apontou uma causa real: buscar pelo `ficha.titulo` (o título pt-BR, `"mãe!"`) em vez do título do slug resolve outro filme ("Perfeita é a Mãe 2"). O harness passou a usar o título do SLUG, como o pipeline usa. **Resultado medido (v1.9.29): 35 de 35 filmes com pôster, 0 sem, 0 falhas.**

**Retrofit da v1.9.30 — mesmo harness, mesmas travas, `CHAVES_NOVAS` maior.** Os seis campos da v1.9.30 entraram pelo mesmo passe, com a guarda de lote continuando inalcançável e a **guarda de identidade** (a que pegou `mother-2017`) em vigor. **Resultado medido: 35 de 35 processados, 0 falhas; 34 com backdrop e 1 sem (`talk-to-me-2022`); 35 com arte sem texto e 0 sem.** Diff dos `resultado/*.json` conferido campo a campo contra o `HEAD` anterior: **nada mudou fora do bloco `ficha`**, e dentro dele mudaram exatamente os seis campos novos mais `tmdb_fetched_at` — que é o carimbo da nova consulta e está em `CHAVES_NOVAS` desde a v1.9.29. `poster_path`, as dimensões do pôster e `backdrop_paths[]` vieram **idênticos** aos de antes, o que é a confirmação independente de que a reconsulta resolveu os mesmos 35 filmes.

**RESSALVA HISTÓRICA DA v1.9.30, CORRIGIDA NA v1.9.49 — `talk-to-me-2022` publicava a ficha de OUTRO FILME.** O slug é o de *Talk to Me* (2022, Danny e Michael Philippou), mas a ficha era **"The Elms Estate: You Can Talk To Me"** (`tmdb_id` 976680), curta de 3 minutos dirigido por George Williams. A v1.9.49 republicou ficha, narrativa e veredito sobre o longa correto (`tmdb_id=1008042`, 95 minutos); o ano editorial 2022 do Letterboxd prevalece e a data TMDB 2023 continua auditável em `ficha.identidade`. O caso deixa de ser o único filme sem backdrop e passa a ter a faixa normal de 12 stills. Reviews, classificação, eixos e condições não foram regenerados.

**Diretor em escrita latina (v1.6.0):** o TMDB devolve o nome do diretor no **alfabeto nativo** quando a localidade pt-BR não tem tradução — `cure` vinha com `"黒沢清"`, que foi parar na narrativa **publicada** (o narrador só reproduz o que a ficha entrega). Quando o nome pt-BR não está em escrita latina (`_e_escrita_latina`, checagem sobre `unicodedata.name` de cada letra — cobre diacríticos latinos como ç/é/ñ sem lista de exceções), o `credits` de `en-US` é consultado e a transliteração é usada (`"Kiyoshi Kurosawa"`). A ficha carrega `diretor_transliterado: true` — visível, nunca silencioso. **Custo:** no máximo 1 requisição extra, e só para filmes nessa condição; quando o fallback de sinopse já buscou `en-US`, a resposta é **reaproveitada** em vez de refeita. Se o `en-US` também não for latino, mantém o nome original (melhor um nome em alfabeto nativo do que nenhum). Cacheado junto da ficha, como todo o resto.

**Fallback de sinopse:** se `overview` vier vazio na resposta pt-BR (acontece para filmes com localização incompleta no TMDB), uma segunda chamada com `language=en-US` busca o overview em inglês; a ficha carrega esse texto com a flag `sinopse_fallback_en: true` — nunca fica silenciosamente vazia, mas também nunca finge ser pt-BR quando não é.

**Cache em disco** (mesmo padrão do cache do Letterboxd em `fetcher.py`, raiz própria `<cache-dir>/_tmdb/`): chave determinística por `título_normalizado[_ano]`; nunca rebusca filme já buscado, inclusive "não encontrado" (evita reconsultar buscas vazias). Diferente do cache de rede do Letterboxd, falhas transitórias (rede, HTTP não-200) **não são cacheadas** — podem ser passageiras, vale tentar de novo na próxima execução; só resultado de sucesso ou "sem resultado" persistem.

**Falha nunca bloqueia (decisão de design central desta etapa):** chave ausente, erro de rede, HTTP não-200, filme não encontrado, ou ano indisponível/divergente → `buscar_ficha` retorna `(None, aviso, ficha_descartada)` (v1.7.0 — terceiro elemento da tupla, `None` nos casos que não são divergência de ano). O CLI imprime o aviso em stderr, persiste `ficha_descartada` no JSON quando presente, e segue o pipeline inteiro (coleta, síntese, narrador, render) com `output["ficha"] = None`. Nenhuma exceção de `ficha.py` escapa para o `main()` do CLI.

**Saída:** campo global `ficha` no JSON (§4), formato:
```json
{
  "titulo": "Cure", "sinopse_oficial": "...", "sinopse_fallback_en": false,
  "generos": ["Suspense", "Terror"], "duracao_min": 111,
  "diretor": "Kiyoshi Kurosawa", "ano": 1997, "fonte": "tmdb"
}
```
`null` quando a ficha não foi obtida (busca falhou, `--no-ficha`, ou filme não encontrado).

**Consumo:** a ficha (quando presente) é serializada para o narrador (§D2) como fonte exclusiva do MOVIMENTO 1; fora do modo narrativo, o render estruturado/terminal também exibe um resumo de uma linha da ficha, quando existe (título/ano/diretor/gênero/duração), separado dos buckets e sem interferir nos avisos existentes.

### [G] Distribuição real de notas (histograma do Letterboxd) — v1.4.0

Etapa **aditiva e independente**, irmã da ficha TMDB (§F): não depende das
reviews coletadas e não é bloqueada por elas. Detalhes de sondagem, seletores
e armadilhas em **`docs/arquivo-de-estudos/coleta/FASE_HISTOGRAMA.md`**.

**Endpoint:** `letterboxd.com/csi/film/<slug>/rating-histogram/` — fragmento CSI
server-rendered, **1 requisição por filme**, cacheada em
`<cache-dir>/_histograma/<slug>.html`. Preferido à página principal do filme
por ser ~5,8 KB em vez de centenas, expondo exatamente o dado desejado.

**Estrutura (validada ao vivo):** `table.chart tbody tr` × **10** (sempre 10,
um por nível de 0.5 a 5, em ordem crescente). Nível em `th._sr-only` (glifos:
`half-★`, `★`, `★½`, …). **Contagem exata no atributo `title` do `.barcolumn`.**

Três armadilhas, todas tratadas (ver `docs/arquivo-de-estudos/coleta/FASE_HISTOGRAMA.md` §3):
1. **Nível zerado não tem `<a>`** — vira `<span class="barcolumn" title="No ★½ ratings">`.
   Buscar `a.barcolumn` perderia os zeros **em silêncio** e inflaria o total,
   justamente em filmes pequenos (onde o denominador é mais frágil). O seletor
   é `.barcolumn`, qualquer tag.
2. **O `_sr-only` da barra ABREVIA** (`23.4K`, `111K`) — inútil como fonte. O
   `title` traz o número exato.
3. **Singular/plural e "No"** — `456 … ratings`, `1 … rating`, `No … ratings`.

**Agregação (código, não prompt):** `share_real` por bucket =
`soma dos níveis do bucket / total`, em **percentual inteiro**. Cada bucket é
arredondado **independentemente**, para que o número de cada grupo seja a
melhor aproximação inteira do seu próprio share. **Consequência aceita e
documentada:** a soma dos três pode dar 99 ou 101 (ex.: `cure` → 3+17+79=99).
Preferido a redistribuir o resto, o que tornaria algum bucket menos fiel ao
próprio dado — coerente com a política do projeto de não maquiar número. A
interface **nunca exibe a soma**.

**A cota NÃO passa a seguir o peso** (decisão explícita, reafirmada na
v1.9.0). Racional: cota e peso respondem a perguntas diferentes e ambas
continuam necessárias.
- A **cota** é *amostragem estratificada*: garante **profundidade igual por
  perspectiva**. Quem quer saber o que incomodou o grupo minoritário precisa de
  ~40 reviews negativas lidas, não de 1 review porque só 1% deu nota baixa.
  Reduzir a amostra do grupo pequeno destruiria a análise temática justamente
  onde ela é mais informativa para a decisão de assistir.
- O **peso** é a prevalência real, e está exibido separadamente.

Ou seja: **profundidade igual, peso informado** — que é o princípio norteador
(§0) aplicado à coleta.

> **v1.9.0 — o que mudou, e o que deliberadamente não mudou.** A cota **entre**
> buckets deixou de ser 50/20/30 e passou a ser **40/40/40** (§0): o desenho
> antigo já pretendia profundidade igual, mas entregava 5/2/3 níveis × 10, que é
> aritmética de escala, não decisão de profundidade. **Dentro** de cada bucket,
> ao contrário, o histograma passa a mandar (§3[C1]) — porque ali a pergunta é
> outra: distribuir 40 vagas entre 4 níveis do MESMO grupo por cota igual
> super-representa os extremos, sem nenhum ganho de perspectiva. Em uma frase:
> **peso informa a composição DENTRO do grupo; nunca o tamanho ENTRE grupos.**
> É a mesma fronteira da v1.4.0, aplicada um nível abaixo.

**Consequência de vocabulário (v1.4.1) — o histograma conta NOTAS, não
reviews.** O denominador de `share_real` é `n_notas_total`: **todo mundo que
avaliou** o filme. Os temas, por outro lado, saem das **reviews com texto**
que passaram nos filtros (§C) — um subconjunto muito menor da mesma
população. As duas coisas nunca compartilham denominador, e por isso o
produto **nunca** apresenta um rótulo de peso como se fosse sobre reviews,
espectadores ou "o público": um rótulo de peso é sempre "**das notas**". A
regra completa, com a checagem que a defende no narrador, está em §D2
("Invariante de vocabulário do peso"); o render de terminal e o frontend já
seguiam esse vocabulário desde a v1.4.0 (`· ~X% das notas`).

**Falha nunca bloqueia** (idêntico a §F): chave estrutural inesperada, rede,
HTTP, anti-bot ou filme sem nota alguma → `collect_distribuicao` retorna `None`,
o campo sai `null` e **todo o resto do pipeline degrada sozinho** para o
comportamento da v1.3.1 (ver "Fallback" no §D2). Nem `AntiBotError` escapa:
perder a distribuição não justifica abortar uma coleta que já custou dezenas de
requisições.

**Saída** (§4): bloco global `distribuicao` + `share_real` por bucket.
```json
{
  "n_notas_total": 375278,
  "por_nivel": {"0.5": 456, "1.0": 1037, "…": 0, "5.0": 99242},
  "por_bucket": {"negativas": 3, "medianas": 17, "positivas": 79},
  "fonte": "letterboxd_histograma"
}
```
`share_real` é **omitido** (chave ausente, não `0`) quando não há distribuição —
o consumidor distingue "não coletado" de "coletado e deu 0%".

**Flag `--no-distribuicao`** pula a busca (e cai no fallback), para A/B.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_PROSA.md` — "[E2] Editor — passe de EDIÇÃO da narrativa (v1.6.0) — **APOSENTADO na v1.9.10, seção mantida como REGISTRO HISTÓRICO**")*

### [E] Render
1. `resultado/<slug>.json` — objeto completo: 3 buckets + metadados por nível e globais.
2. Terminal — por bucket: título, `n_validas/alvo` (com decomposição por nível quando houver nível degradado), filtro aplicado, temas com frequência relativa ("mencionado em ~14 de 50 reviews"), observação geral. Avisos de modo reduzido/degradado sempre visíveis e concretos ("análise negativa baseada em apenas 7 de 50 reviews-alvo — interprete com cautela").
3. Rodapé: contagem total de reviews observada, para distinguir "bucket vazio porque ninguém odeia" de "bucket vazio porque ninguém assistiu".
4. **(v1.4.0)** Header do grupo ganha `· ~X% das notas` quando há distribuição — **formato e estilo idênticos nos três grupos** (§0: a assimetria vem do dado, não da apresentação). O disclaimer da seção tema-a-tema tem duas variantes, escolhidas pela presença do dado (constantes `DISCLAIMER_*` em `render.py`, mantidas em sincronia com o frontend):
   - **sem** distribuição: *"grupos de 40 · 40 · 40 reviews são cotas de coleta — não a proporção real das opiniões"*
   - **com** distribuição: *"análise em profundidade igual por grupo (40 · 40 · 40 reviews); o peso real de cada faixa está indicado em cada grupo"*

   **(v1.9.0)** Os números destes dois textos são **derivados de `BUCKET_ALVO`**, não literais — a v1.9.0 mudou a cota, e um disclaimer com o número antigo seria uma afirmação falsa sobre o método na cara do leitor. **PENDÊNCIA RESOLVIDA NA v1.9.1:** `frontend/js/filme.js` tinha os mesmos dois textos com "50 · 20 · 30" hardcoded — corrigido para ler `f.buckets[i].alvo` do próprio JSON de resultado (o campo já existe desde a v1.1.0; o frontend não tem acesso a `config.py`, então lê do dado, não de uma constante compartilhada) em vez de repetir o número.

   O frontend (`frontend/`) aplica exatamente o mesmo tratamento e **tolera JSONs sem `distribuicao`** (filmes antigos/fallback) sem quebrar: omite os shares e usa o disclaimer antigo. Ordem visual dos grupos permanece negativas → medianas → positivas em qualquer caso — **a ordem não é reordenada por peso**; quem muda de ordem é só a prosa do MOVIMENTO 3.

   **(v1.9.26) A PÁGINA DO FILME, ordem publicada.** O frontend divergiu do
   render de terminal em ORDEM e em ÊNFASE — o terminal continua como
   descrito acima; `filme.html` é o que o leitor vê, e nele a ordem é:

   1. ano + título
   2. botão "reviews no Letterboxd"
   3. ficha (sinopse + linha de metadados)
   4. **BARRA DE PROPORÇÃO** + o disclaimer da cota logo abaixo dela
   5. linha arco-íris
   6. bullets por sentimento (dois blocos, ou três sob a exceção do §0)
   7. **VEREDITO** (§3[V])
   8. narrativa completa, colapsada
   9. micro-pesquisa

   **(v1.9.32) A ORDEM ATUALIZADA.** A lista acima é a da v1.9.26 e fica
   como registro histórico. A publicada hoje:

   1. **BACKDROP** dissolvido no fundo (v1.9.30, refeito na v1.9.32), com
      **ano + título começando SOBRE a imagem**, dentro do fade
   2. linha de metadados — **DIRETOR EM CAIXA ALTA** · gêneros · duração ·
      fonte TMDB, solta, sem card (a **SINOPSE SAIU** na v1.9.32)
   3. "reviews no Letterboxd ↗", **link secundário** (deixou de ser pill)
   4. **RECEPÇÃO** (etiqueta de seção) + **BARRA DE PROPORÇÃO** + callout de
      percentual + legenda HATERS · MIXED · FANS
   5. linha arco-íris + **EM DETALHE · TEMA A TEMA** (etiqueta de seção,
      de volta — ver abaixo)
   6. bullets por sentimento, **ordenados por peso** (v1.9.30)
   7. **VEREDITO** (§3[V]) — inalterado
   8. narrativa completa, colapsada — inalterada
   9. micro-pesquisa — inalterada

   Os itens 7, 8 e 9 não foram tocados pela v1.9.32 e continuam exatamente
   onde estavam; o rodapé com a atribuição ao TMDB também.

   **A BARRA DE PROPORÇÃO** é a divisão dos três grupos numa faixa
   **contínua**, largura proporcional ao peso real, na ordem de leitura de
   sempre. Ela lê `share_real` — a MESMA fonte que os cabeçalhos de grupo
   imprimem, e não `distribuicao.por_bucket`, que carrega os mesmos
   valores: uma fonte só por fato é o que impede a barra e os cabeçalhos de
   divergirem em silêncio. **Nenhum número dentro da barra** (os
   percentuais continuam nos cabeçalhos), e a alternativa textual é o
   `aria-label` com rótulo e peso dos três — número permitido pela v1.9.20,
   que proibiu contagem bruta de review e não proporção.

   **CONTÍNUA quer dizer SEM VÃO, e isso é requisito, não acabamento.** A
   primeira rodada desta versão separava as três faixas com 3px de respiro
   escuro e foi rejeitada pelo dono do projeto com o diagnóstico certo: a
   barra "não dá ideia de continuidade — parece que são três barras
   separadas, cortadas com vão no meio". O erro era conceitual. A recepção
   de um filme é **uma população particionada em três**, não três medições
   independentes; um vão entre as faixas desenha três objetos onde o dado
   tem um só. A barra publicada tem zero gap, zero fio separador e zero
   respiro escuro entre faixas.

   **A fronteira é uma DIAGONAL**: uma cor terminando e a outra começando.
   Desenhada por camadas empilhadas (cada cor começa na borda esquerda e
   termina na sua fronteira, a última preenchendo a barra), porque fatias
   lado a lado com aresta inclinada deixariam um triângulo vazio em cada
   fronteira — o vão de novo. A diagonal fica **centrada** na fronteira
   verdadeira, então ela empresta área de um lado e devolve do outro: na
   meia altura da barra, o limite está exatamente no percentual (medido em
   `napoleon-2023`: 22,000% contra um cabeçalho de 22%).

   **A DIAGONAL É ADAPTATIVA, porque senão ela come a fatia estreita.** A
   pior do catálogo é `the-godfather`, com 2% em negativas. A projeção
   horizontal da diagonal é `clamp(3px, 0,55 × menorFatia, 12px)`, e o
   cálculo mora no **CSS**, não no JS: o percentual da menor fatia é DADO
   (o JS grava `--menor-pct` uma vez), e a conversão para pixel usa `cqw`,
   que reage a resize sozinha. A primeira implementação usou
   `ResizeObserver` e foi trocada — media em JS uma coisa que o CSS já
   sabe, e um observador que não dispara deixaria o ângulo errado sem
   sintoma visível. Medido: a fatia de 2% mede 14,40px de média em desktop
   (720px de barra) e 6,70px em mobile (335px); no ponto mais fino da
   diagonal, 10,91px e 5,07px — a diagonal encolhe sozinha no mobile
   (7,9px → 3,7px) exatamente para a fatia sobreviver.

   **A marca da fronteira, e por que ela não é um vão.** Sem respiro, a
   distinção entre faixas adjacentes passaria a depender só do contraste
   entre as cores. Cada camada recebe um `drop-shadow` de 1px que, por
   acompanhar o `clip-path`, traça **exatamente a diagonal e só ela**. É
   uma dobra, não um corte: as cores continuam encostadas.

   **A VARIANTE ALTERNATIVA, e por que não foi a escolhida.** Uma segunda
   proposta desta rodada foi um **diverging stacked bar** (Heiberger &
   Robbins, *Journal of Statistical Software* 57(5), 2014) — o meio
   ancorado no centro, a cavaleiro sobre um zero, com negativas crescendo
   para a esquerda e positivas para a direita. É a técnica que a
   literatura recomenda como primária para escalas ordenadas de opinião
   com centro neutro, e a ressalva honesta era que parte do valor do
   padrão vem de comparar VÁRIAS linhas contra a mesma linha-base — a
   página do filme tem uma só. **O dono do projeto comparou as duas e
   escolheu a contínua.** A implementação da divergente foi removida do
   JS e do CSS junto com a escolha; se precisar voltar, o histórico do git
   tem a construção completa (fórmula do zero, marca de divergência,
   verificação de honestidade em `napoleon-2023` e `the-godfather`).

   **O DISCLAIMER DA COTA — REMOVIDO DO RAMO COM BARRA na v1.9.27, e isso
   é decisão registrada, não esquecimento.** Na v1.9.26 ele morava debaixo
   da barra, com este texto: *"A barra é o peso real de cada grupo. A
   análise abaixo tem profundidade igual nos três — o tamanho das listas
   não indica peso."* Com o **callout de percentual** (v1.9.27) o topo
   passou a dizer o peso duas vezes — a barra e os três números ancorados
   nela —, e a frase virou uma terceira explicação do mesmo fato, a uma
   rolagem inteira de distância das listas que ela existia para desarmar.

   **O que a remoção custa, escrito porque é ele que a decisão paga.** Era
   a única frase que dizia, em palavras, que listas de bullets do mesmo
   tamanho NÃO são grupos do mesmo peso. Sem ela, o único sinal de peso
   **co-localizado com as listas** é o `~X% DAS NOTAS` no cabeçalho de cada
   grupo — e **é por isso que o percentual do cabeçalho FICA**. As duas
   coisas são uma decisão só: a frase sai porque o número do cabeçalho
   cobre a mesma leitura errada no lugar certo (ao lado dos bullets, não a
   800px deles). Quem rolar direto para a análise encontra seis marcadores
   em HATERS e seis em FANS com `~2%` e `~93%` impressos ao lado do nome de
   cada grupo; é o número no cabeçalho que impede "listas iguais, pesos
   iguais" de fechar. **Se o percentual do cabeçalho algum dia sair da
   tela, esta frase tem de voltar** — e essa é a condição que amarra a
   remoção.

   **O RAMO SEM DISTRIBUIÇÃO REAL fica INTACTO, no texto da v1.2.1** (*"Os
   grupos são cotas de coleta — não a proporção real das opiniões."*).
   Nesse caminho não há barra, não há callout e não há percentual em
   cabeçalho nenhum: a única coisa na tela sobre tamanho de grupo são as
   listas, e a regra da v1.2.1 volta a valer sozinha e inteira. Mantido em
   sincronia com `render.py` (`DISCLAIMER_*`); o render de TERMINAL não
   mudou.

   **O cabeçalho "EM DETALHE · TEMA A TEMA" foi REMOVIDO** — com o veredito
   no rodapé, não há mais um resumo antes dele do qual separar "o detalhe".

   **Os RÓTULOS dos três grupos na tela são HATERS/MIXED/FANS** desde a
   v1.9.26, onde o nome aparece isolado; a prosa continua em
   negativas/medianas/positivas, e as chaves do dado não mudam. Escopo,
   trade-off e política de reversão em **§0, "SEGUNDA EXCEÇÃO DELIBERADA na
   INTERFACE"**.

   #### A ORDEM DOS BLOCOS EM DESTAQUE — POR PESO (v1.9.30)

   O item 6 da ordem publicada acima ("bullets por sentimento") passa a ter
   ordem **interna** definida pelo dado: os blocos em destaque saem
   ordenados por `share_real`, **do maior para o menor**. O racional
   completo — por que a regra é compatível com o §0, e por que a ordem fixa
   anterior não era neutra e sim constante — está em **§0, "A ORDEM DE
   LEITURA DOS BLOCOS PASSA A SEGUIR O PESO"**. Aqui ficam a mecânica e a
   medição.

   **Vale nos DOIS leiautes, e é a mesma linha de código nos dois.** O
   contêiner é grid e **a ordem do DOM é a ordem visual**: no desktop
   "primeiro" é a coluna da ESQUERDA; no mobile, empilhado em coluna única,
   é o de CIMA. Nada de `order:` no CSS, nada de reordenar por
   breakpoint — o mobile é onde a ordem pesa mais, porque lá o segundo bloco
   só existe depois de uma rolagem, e ele é servido pela mesma decisão.
   MEDIDO em `the-godfather` a 375px: FANS em y=1203, HATERS em y=2166.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "A ORDEM DOS BLOCOS EM DESTAQUE — POR PESO (v1.9.30)")*
   #### O CALLOUT DE PERCENTUAL abaixo da barra (v1.9.27)

   Os três percentuais deixam de aparecer **só** nos cabeçalhos de grupo e
   passam a aparecer também **abaixo da barra**, cada um **ancorado na sua
   fatia** por um indicador fino. O percentual do cabeçalho **continua onde
   estava** — ver o parágrafo do disclaimer acima: é ele que carrega a
   informação de peso para o lado das listas de bullets. **A fonte
   continua sendo uma só:** `b.share_real`, o mesmo inteiro que o cabeçalho
   e que o `aria-label` imprimem; o callout não recalcula nada.

   **A COLISÃO é o problema real desta entrega.** `the-godfather` é
   2% / 5% / 93%: os centros verdadeiros das duas primeiras fatias caem a
   1% e 4,5% da largura da barra — **7,2px e 32,4px** em desktop (720px),
   **3,35px e 15,07px** a 375px (barra de 335px). A caixa de um número mede
   **39,91px**. Três números centrados nos seus centros verdadeiros se
   sobrepõem, e nenhum dos dois primeiros cabe dentro da própria fatia. O
   pior caso do catálogo não é nem esse: é `cidade-de-deus`, 1% / 3% / 96%.

   **A REGRA: empacotamento da ESQUERDA para a DIREITA com folga mínima, e
   o indicador inclinado absorve o deslocamento.**

   ```
   x1 = max(0,          min(c1 − L/2,  100% − 3L − 2g))
   x2 = max(x1 + L + g, min(c2 − L/2,  100% − 2L − g))
   x3 = max(x2 + L + g, min(c3 − L/2,  100% − L))
   ```

   `c` é o centro VERDADEIRO da fatia (o mesmo número normalizado que
   desenha a barra), `L` a largura da caixa do número (`5.6ch` da mono) e
   `g` a folga mínima (**14px desde a v1.9.28** — era 8px; a diferença é o
   espaço que o halo do neon permanente passou a ocupar, ver "A COLISÃO QUE
   O NEON PERMANENTE CRIA"). Cada número vai para o centro da sua fatia;
   quando não cabe, escorrega o mínimo necessário e a linha que o liga ao
   centro verdadeiro inclina. **O ponto de ancoragem nunca se move** —
   quem se move é o rótulo, e a inclinação é a declaração visível de que
   ele se moveu. O termo `100% − L` na última linha é o que trata o outro
   lado: uma fatia colada na borda direita puxa o rótulo para DENTRO, e aí
   o indicador inclina para a direita em vez de para a esquerda
   (`cats-2019`, 86/7/7, é o caso).


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "O CALLOUT DE PERCENTUAL abaixo da barra (v1.9.27)")*
   #### A ANIMAÇÃO DE ENTRADA DA BARRA — as FRONTEIRAS DESLIZAM (v1.9.28)

   **O MODELO DA v1.9.27 SAIU INTEIRO.** Lá a barra crescia de 0 a 100%
   como um bloco neutro (`#454b5a`) e só então as cores nasciam por cima,
   em duas fases (fill + partição). A camada de prefill foi **removida do
   JS e do CSS**, não escondida atrás de flag. Decisão do dono do projeto.

   **O MODELO PUBLICADO:** a barra **nasce completa**, particionada em
   **três partes iguais**, e as fronteiras deslizam até a distribuição
   real. Com isso as duas fases viram **uma**.

   ```
   x1: 33,333%  ──▶  h            x2: 66,667%  ──▶  h + m
   x(k) = neutro + (fim − neutro) × k
   ```

   | fase | janela | o quê |
   |---|---|---|
   | A · fronteiras | 0 → 650ms | terços ──▶ distribuição real |
   | B · ignição | 650 → 1020ms | 3 números × 260ms, escalonados 55ms |

   **Total 1020ms** (era 1190ms com o modelo antigo), medido pela Web
   Animations API.

   **UMA FUNÇÃO TEMPORAL SÓ, e ela é literal.** `--k` é um número
   registrado por `@property` e animado **uma vez**, na barra; as duas
   fronteiras e a diagonal são funções puras dele. Não são duas animações
   com temporização igual que *pareceriam* a mesma função — é uma animação,
   lida por dois lugares. Isso mata na origem o frame em que a soma não
   fecha 100%.

   **E A ARQUITETURA DE CAMADAS EMPILHADAS dá a garantia mais forte
   ainda**, e é por isso que ela foi preservada: a camada de baixo ocupa
   **100% da barra em todos os frames**, então a região da terceira fatia é
   literalmente "o que sobra". A soma fecha **por construção**, não por
   sincronia — e não existe superfície descoberta em frame nenhum. Três
   segmentos independentes em flex/grid é a forma de fazer isto que deixa
   buraco; foi recusada.

   **A DURAÇÃO É FIXA (650ms) e independente da distribuição.** A
   DISTÂNCIA percorrida é consequência do dado — `cats-2019` move a
   primeira fronteira 52,7 pontos percentuais e `napoleon-2023` move 11,3 —,
   mas as duas levam os mesmos 650ms. Amarrar a duração à distância faria a
   animação codificar uma segunda variável competindo com a barra.

   **A CURVA — `cubic-bezier(0.22, 0.68, 0.28, 1)`, desaceleração pura.** A
   proibição de overshoot/bounce/spring é **geométrica antes de ser
   estética**: os dois pontos de controle dentro de [0,1] são o que garante
   `k ∈ [0,1]` em todo instante, e `k` fora desse intervalo produziria
   `x1 > x2`, ou seja, uma fatia de largura **negativa**.

   **NENHUM VÃO EM FRAME NENHUM.** Durante o deslize as camadas não mudam
   de opacidade nem de posição — só de **limite** —, e continuam encostadas
   o tempo todo. Zero gutter, zero fio separador, zero margem, zero borda
   como separador, zero pixel transparente.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "A ANIMAÇÃO DE ENTRADA DA BARRA — as FRONTEIRAS DESLIZAM (v1.9.28)")*
   #### ACESSIBILIDADE DA ANIMAÇÃO (v1.9.27, reconfirmada na v1.9.28)

   1. **`prefers-reduced-motion`: nenhuma fase roda.** A construção é a
      única que entrega isso sem depender de regra de desligamento: **o
      estado base do CSS É o estado final**, e tudo que a animação faz —
      inclusive o estado INICIAL (`--k: 0`, número apagado) — vive dentro
      de `@media (prefers-reduced-motion: no-preference)`. O
      `* { animation: none !important }` que já existia sob `reduce`
      continua valendo como segunda linha, mas nada aqui depende dele —
      **e essa é a diferença que importa**: se o estado inicial morasse
      fora do bloco, `reduce` deixaria a barra em terços para sempre.
      Verificado nos dois sentidos: com o bloco `no-preference` inativo, 0
      animações, `--k = 1`, barra na distribuição real e números acesos;
      reativado, as 10 animações voltam e a sequência re-arma do zero.
      **O NEON PERMANENTE NÃO É MOVIMENTO E FICA** — conferido: sob
      `reduce` o `text-shadow` de repouso está aplicado por inteiro.
   2. **A alternativa textual descreve sempre o ESTADO FINAL.** O
      `aria-label` do `role="img"` é escrito na montagem, com os três
      rótulos e os três pesos, e nunca é tocado pela animação. **O estado
      neutro de terços é expressivo e nunca é anunciado**: um leitor de
      tela jamais ouve "33% / 33% / 33%".
   3. **Os percentuais são conteúdo, não aparência.** O texto está no DOM
      com os **valores finais** desde o primeiro frame; a animação não
      cria, remove nem altera um caractere — muda opacidade, cor e sombra.
      Que eles fiquem **invisíveis** durante o deslize é decisão de
      apresentação (ver "Os rótulos durante a interpolação"), não de
      conteúdo.
   4. **Sair da página no meio não deixa nada pela metade.** Não há estado
      guardado em lugar nenhum: a página é remontada do zero a cada visita,
      a sequência é CSS puro com `animation-fill-mode: both`, e o estado
      final coincide com o estado base.

   **CADÊNCIA — DECISÃO EM ABERTO PARA O DONO DO PROJETO.** Implementado
   **SEMPRE** (roda a cada visita a uma página de filme), que é o que a
   intenção "sensação de estar sendo calculado na hora" pede. A alternativa
   é uma vez por sessão (`sessionStorage`), e ela tem um custo próprio: a
   barra passaria a aparecer pronta em algumas visitas e animada em outras,
   sem que o leitor saiba por quê. A leitura sobre cansaço em navegação
   repetida continua não podendo ser dada por experiência — ver a ressalva
   de método em `frontend/TESTE_MANUAL.md`. O total caiu de 1190ms para
   1020ms na v1.9.28, o que reduz o custo por visita em 14%.

   #### O PÔSTER (v1.9.29) — na home e na página do filme

   **Decisão de produto, tomada e não reaberta:** pôster SIM, na home e na
   página do filme; **galeria de backdrops NÃO na v1** (§3[F] — o TMDB não
   garante que um backdrop seja livre de spoiler). O pipeline coleta
   `backdrop_paths[]` e **nenhum arquivo do frontend os lê**.

   **Página do filme — CONTIDO.** O pôster abre a ficha, 200px no desktop e
   140px no mobile. O produto não vira catálogo visual: o pôster representa
   o FILME, a barra logo abaixo representa a RECEPÇÃO, e a composição existe
   para que **nenhum dos dois domine o outro**. Um pôster em largura total
   empurraria a barra para fora da primeira tela e inverteria a hierarquia
   que a v1.9.26 estabeleceu. A composição de referência do dono é
   `[PÔSTER] → TÍTULO → ANO → barra`; o que a página publica desde a v1.9.26
   é **ano → título** (item 1 da ordem publicada acima), e essa micro-ordem
   não é o que esta sessão veio mudar — o pôster entra ACIMA do par e o par
   segue como está. **A BARRA não foi tocada:** nem posição, nem geometria,
   nem a animação de entrada da v1.9.28.

   **Home — REDESENHO da célula, não acréscimo.** A célula da v1.9.18 foi
   desenhada SEM imagem (card escuro em 4/5, texto como protagonista, faixa
   de 5px na base). Encaixar um pôster nela daria o pior dos dois — uma
   miniatura apertada disputando espaço com o título. Então: a célula muda
   de proporção (**4/5 → 2/3**, a do próprio pôster), o pôster ocupa a
   célula inteira, e o texto sobe para um **degradê** na base que chega a
   98% de preto — o título tem de ser legível sobre pôster claro
   (`barbie`, `wonka`) e sobre escuro, e um véu uniforme apagaria a arte.
   A grade fica ~20% mais alta (5 linhas de 213px contra 165px no desktop);
   é o custo de densidade que mostrar pôster cobra. **A faixa de recepção
   continua**, de 5px para **6px** com um fio escuro em cima que a separa de
   qualquer arte sem depender da cor dela — ela é o único sinal de RECEPÇÃO
   da célula, e é o que impede a home de virar um catálogo de capas. Cores,
   ordem e semântica: idênticas.

   **A ANIMAÇÃO DA BARRA NÃO RODA NA HOME — decisão registrada.** Trinta e
   cinco sequências simultâneas na entrada viram espetáculo e competem entre
   si. A home mostra a faixa no **estado final**; a animação continua sendo
   o momento de **abrir um filme**.

   **AUSÊNCIA DE PÔSTER É ESTADO DESENHADO**, nunca imagem quebrada. Nenhum
   dos 35 publicados está nesse caso (medido: 35/35 com pôster), mas a
   expansão trará filmes obscuros com menos cobertura, e o estado precisa
   existir ANTES do primeiro — senão ele vira um ícone de imagem quebrada em
   produção. O desenho mantém a silhueta do pôster, com hachura diagonal
   sutil, a marca do produto e "SEM PÔSTER". Uma falha do CDN (404, rede,
   `file_path` que envelheceu) cai no MESMO estado.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "O PÔSTER (v1.9.29) — na home e na página do filme")*
   #### O BACKDROP no topo da página do filme (v1.9.30)

   **O pôster vertical SAI do topo da página do filme e entra um BACKDROP
   (16:9, horizontal), no mesmo lugar — acima do par ano → título.** Decisão
   do dono do projeto, tomada e **não reaberta**. **O PÔSTER CONTINUA NA
   HOME**, sem nenhuma alteração: esta entrega troca a imagem SÓ na página
   do filme.

   ##### ISTO É EXCEÇÃO EXPLÍCITA AO PRINCÍPIO ANTI-SPOILER DO §0

   Este registro é obrigatório e é a parte da decisão que custa alguma
   coisa. Não há como escrevê-lo sem tensão, e ele não tenta.

   **O que o produto promete.** A home anuncia **"0 SPOILERS"** em caixa
   alta, ao lado de "24 QUADROS" e "3 GRUPOS". O parágrafo de abertura desta
   spec diz, sobre o público-alvo: *"pessoa que ainda NÃO assistiu ao filme.
   Toda decisão de design que envolva trade-off entre completude e risco de
   spoiler resolve a favor de evitar spoiler."* E o produto cumpre isso em
   toda parte: as reviews passam por filtro anti-spoiler na coleta (§3[C]),
   o prompt de síntese proíbe descrever eventos de enredo (§3[D]), o
   veredito é **proibido de citar reviravolta** (§3[V]), e a galeria de
   backdrops foi recusada na v1 **por este exato motivo**.

   **O que o backdrop é.** Um quadro do filme, do acervo do TMDB, **sem
   nenhuma garantia** de que não seja do terceiro ato. Não existe curadoria
   — nem humana, nem automática, nem por metadado: o TMDB não marca imagem
   por posição na narrativa, e não há sinal na API do qual isso se derive.
   **O dono do projeto decidiu prosseguir SEM curadoria de spoiler**, com o
   trade-off explicitamente na mesa.

   **E ele fica na POSIÇÃO MAIS PROEMINENTE DA PÁGINA** — o primeiro
   elemento, acima do título, **antes da sinopse**, em largura total. Não é
   um detalhe periférico onde a exceção seria pequena: é literalmente a
   primeira coisa que o leitor vê, e ele a vê sem ter escolhido vê-la.

   **O QUE SE GANHA:**
   - **Leitura horizontal.** 16:9 é o formato da imagem em movimento, e um
     quadro largo abre a página como abertura editorial em vez de capa de
     catálogo.
   - **Menos espaço vertical no topo.** Medido: o backdrop reserva **405px**
     de altura em desktop (720px de coluna) contra os ~300px do pôster de
     200px de largura — mas ele ocupa a **largura inteira**, então não
     divide a linha com nada e não empurra o par ano → título para o lado.
     No mobile o ganho é o real: de borda a borda, contra uma capa de 140px
     que deixava dois terços da linha vazios.
   - **Abertura editorial.** O pôster é o objeto de marketing do filme; o
     quadro é o filme. Para uma página que existe para descrever recepção, a
     segunda leitura é a que o dono quis.

   **O QUE SE PERDE, sem maquiagem:** **a promessa anti-spoiler deixa de
   valer neste elemento.** Não fica mais fraca, não fica condicionada, não
   fica "mitigada por curadoria": ela **não vale ali**. Um leitor que confia
   no "0 spoilers" da home e abre uma página de filme pode ver, antes de
   qualquer texto, um quadro do desfecho. O produto continua a resolver todo
   o resto contra o spoiler; este elemento, e só ele, é a exceção. Se algum
   dia existir política de curadoria, ela entra aqui — e o pipeline já está
   preparado para isso, porque a lista de candidatos continua guardada.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "O BACKDROP no topo da página do filme (v1.9.30)")*
   #### O TOPO EDITORIAL (v1.9.32) — a sinopse sai, o backdrop dissolve, o título invade

   Cinco mudanças de uma vez no topo da página do filme, todas decisão do
   dono do projeto. A barra de proporção **não foi tocada** — nem
   geometria, nem ordem, nem callout, nem a regra de colisão, nem a
   animação de entrada da v1.9.28.

   ##### A SINOPSE SAI — decisão final, e o que ela custa

   O bloco de sinopse e o **card escuro** que o continha foram **removidos**
   da página. Não é ocultar nem colapsar: não existem mais. A **linha de
   metadados sobrevive**, agora **solta** — sem fundo, sem borda, sem
   padding de caixa —, porque com uma linha só um card desenha uma caixa
   sem conteúdo para conter.

   **A CONSEQUÊNCIA PREVISTA, escrita porque é ela que a decisão paga.** O
   público-alvo declarado do produto (§1) é **quem ainda NÃO assistiu**, e
   a sinopse era **o único elemento da página inteira que dizia do que o
   filme trata**. Sem ela, os bullets chegam **sem premissa onde se
   apoiar**: "o ritmo arrasta" pressupõe saber o que arrasta, "a atuação
   sustenta" pressupõe saber quem atua. O produto passa a assumir que o
   leitor **já sabe qual é o filme** antes de chegar.

   **O custo é BAIXO HOJE e CRESCENTE depois, e essa assimetria é o ponto.**
   Nos 35 do catálogo atual ele quase não morde: são filmes conhecidos, e o
   backdrop faz muito do trabalho de situar (o quadro de `dune-2021` diz
   "deserto, ficção científica" sem uma palavra). Na expansão — filmes
   obscuros, estrangeiros, sem circulação no Brasil — nada disso vale: nem
   o leitor traz contexto de casa, nem o backdrop de um drama iraniano
   comunica premissa. **A dívida cresce com o catálogo, e não aparece
   enquanto o catálogo for o de hoje.** Decisão consciente do dono, tomada
   com isto na mesa.

   **A ATRIBUIÇÃO AO TMDB NÃO É AFETADA e continua integralmente em vigor.**
   Conferido depois da mudança: a linha de metadados (diretor, gêneros,
   duração) **continua vindo do TMDB**, e por isso continua carregando
   **"fonte TMDB"**; o aviso exigido pelos termos segue no **rodapé de
   `index.html`, `filme.html` e `creditos.html`**, e a página de créditos
   segue no ar e linkada. Usar menos da API não reduz em nada o que se deve
   a ela. O que saiu junto com a sinopse foi só o **aviso de sinopse em
   inglês** (`sinopse_fallback_en`) — ele avisava sobre um texto que não
   está mais na tela; o campo continua no JSON, intocado.

   **O DIRETOR EM CAIXA ALTA, sem o prefixo "dir."** — o esboço do dono abre
   a linha pelo nome, e o prefixo era muleta de quando o nome vinha em caixa
   normal no meio de outros dados. **A caixa alta é do CSS
   (`text-transform`), nunca do dado:** `toUpperCase()` em JS mudaria o que
   o leitor de tela anuncia e o que uma busca por texto encontra. **Só o
   nome do diretor** muda de caixa — gêneros, duração e fonte continuam em
   sans caixa normal, como a v1.9.26 decidiu; isto **não** é uma volta ao
   mono-caixa-alta que aquela versão removeu. Conferido com o nome mais
   longo do catálogo (`FRANCIS FORD COPPOLA`, 20 caracteres): cabe em uma
   linha no desktop e quebra limpo no mobile, sem hifenização nem estouro.

   ##### O BACKDROP DISSOLVE, e o título INVADE — com piso de contraste

   O backdrop deixa de ser bloco fechado: **sem `border-radius`, sem margem
   inferior**, terminando dissolvido no fundo da página. O par ano → título
   **começa SOBRE a imagem**, dentro do fade, e **termina no fundo escuro** —
   a passagem de obra visual para conteúdo editorial vira contínua, não um
   corte.

   **O REQUISITO DURO: contraste garantido em QUALQUER backdrop.** Os
   backdrops variam muito no brilho da faixa inferior, e um degradê que só
   "escurece um pouco" entrega contraste diferente por filme — os que
   ficarem bons ficam por sorte.

   **A CONSTRUÇÃO — a mesma ideia do degradê da célula do mosaico (v1.9.29,
   título legível sobre pôster claro), adaptada.** O degradê chega a **100%
   opaco antes do fim da imagem**, formando uma **faixa chapada** na base; o
   recuo negativo do texto é **menor que essa faixa**. O texto, portanto,
   **nunca pousa sobre pixel de imagem** — só sobre `--bg` já chapado.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "O TOPO EDITORIAL (v1.9.32) — a sinopse sai, o backdrop dissolve, o título invade")*
   **VALE NA HOME, e só nela**, porque a página do filme trocou o pôster por
   um backdrop (v1.9.30) — não há pôster lá para variar.

   **O FALLBACK NÃO É RESQUÍCIO DO MECANISMO DE ESCOLHA — é a mesma regra de
   AUSÊNCIA que já rege backdrop e ficha desde a v1.3.0.** Filme sem arte
   sem texto usa o pôster normal (com texto); a lógica em `fonteDoPoster`
   (`poster.js`) é a mesma de antes, só sem o parâmetro decidindo entre as
   duas — agora ela sempre tenta a arte limpa primeiro e cai para a com
   texto quando o campo está ausente.

   **MEDIDO nos 35: os 35 têm arte sem texto — o fallback não é exercitado
   pelo catálogo de hoje, e existe para o filme obscuro que a expansão vai
   trazer.** Em **34** ela é uma imagem diferente do pôster normal; em **1**
   (`talk-to-me-2022`) o `poster_sem_texto_path` é **o mesmo arquivo** do
   `poster_path`, porque aquele registro do TMDB tem uma única arte e ela já
   é sem idioma. A home foi medida com a arte limpa como único caminho em
   **CLS 0** e altura de documento **1657px** — o mesmo número de antes da
   decisão: a variante troca o arquivo servido, não a geometria (a reserva
   usa as dimensões da imagem efetivamente escolhida).

   #### ATRIBUIÇÃO AO TMDB (v1.9.29) — obrigatória, não cosmética

   Até a v1.9.28 o site inteiro dizia apenas "fonte TMDB" numa linha de
   metadados da ficha, e não existia seção "Sobre" ou "Créditos". Os termos
   de uso da API exigem mais. Passa a existir:

   - **O aviso, de forma proeminente, em TODAS as páginas** (rodapé de
     `index.html`, `filme.html` e `creditos.html`) — um aviso escondido
     atrás de um clique não é proeminente. Texto **conferido contra a página
     oficial de atribuição do TMDB** antes de ser escrito, e não contra
     memória: *"This product uses the TMDB API but is not endorsed or
     certified by TMDB."* Ele aparece na página de créditos em inglês,
     LITERAL — é a frase que os termos pedem — com a tradução ao lado, porque
     o produto é em pt-BR e um aviso que o leitor não entende não avisa.
   - **`frontend/creditos.html`**, a seção "Sobre/Créditos" que o site não
     tinha: o que vem do TMDB, o que vem do Letterboxd, e o que o site faz
     com isso.
   - **O copyright das imagens não é do TMDB.** Registrado na spec e na
     página: os pôsteres pertencem aos estúdios e distribuidores; o TMDB
     apenas hospeda e declara não reivindicar propriedade sobre as imagens
     da API.
   - **O LOGO DO TMDB NÃO É USADO — decisão registrada.** Os termos permitem
     usá-lo desde que seja um dos oficiais, sem alterar cor, proporção,
     espelhar ou rotacionar, e menos proeminente que a marca do próprio
     Espectro. Nenhuma condição é difícil, mas o projeto não versiona
     binário nem baixa asset de terceiro (mesma regra dos pôsteres), e a
     atribuição em texto satisfaz a exigência por inteiro. Se o logo entrar,
     entra por decisão de design, não por obrigação.

   #### A LINHA DE METADADOS DA FICHA — tipografia (v1.9.26)

   A linha `DIR. · GÊNEROS · DURAÇÃO · FONTE` era monoespaçada em caixa
   alta com tracking largo, e lia como log de terminal. Passa a ser
   **sans**, em caixa normal, corpo maior e tracking quase nulo. Só a linha
   de metadados; `sinopse_oficial` continua serifada e intocada.

   **O pedido era "a fonte que a Apple usa" — a San Francisco (SF Pro) —, e
   ela NÃO PODE ser embutida.** A licença da Apple restringe o uso da SF
   Pro a mock-ups de interface para iOS/OS X/tvOS; não autoriza
   redistribuição nem uso como webfont em site próprio. **Nenhum arquivo de
   SF Pro é baixado, hospedado ou referenciado neste projeto**, e isso não
   é negociável. A saída legal é a **pilha de fontes de SISTEMA**:


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_FRONTEND.md` — "A LINHA DE METADADOS DA FICHA — tipografia (v1.9.26)")*

#### As TRÊS COLUNAS ALINHADAS POR EIXO (v1.9.14) — a promessa estrutural do produto

Até aqui o frontend exibia três listas de temas empilhadas, cada uma na sua
ordem, e a comparação entre grupos era trabalho mental do leitor. Com eixo
fixo, a mesma informação vira **uma linha por eixo, três células**:

```
Ritmo   |  arrasta (24/40)  |  lento mas justificado (11/40)  |  hipnótico (19/40)
```

A ordem das colunas é **sempre** negativas → medianas → positivas, nunca
reordenada por peso (regra inalterada desde a v1.4.0), e o formato das três
células é idêntico (§0: a assimetria vem do dado, não da apresentação).

**Os quatro estados que a renderização tem de tratar, e nenhum deles é
ausência de conteúdo:**

1. **Eixo presente em só um ou dois buckets.** A célula do bucket que não
   fala daquele eixo fica VAZIA, marcada como vazia — não é zero, não é
   traço solto: é "este grupo não fala disso", que é a informação.
2. **`contraste: valorativo`.** O alinhamento existe e é exibido
   normalmente; o que não existe é linha de contraste. A área ganha
   **enunciado próprio** — os grupos concordam sobre o que o filme é e
   discordam sobre se funciona —, nunca uma lista mais curta sem explicação.
   `cidade-de-deus` (melhor lift 10pp) é o **caso de referência** deste
   estado: se a interface parecer vazia ou quebrada nele, o estado não está
   desenhado como primeira classe.
3. **Bucket em estado reduzido do piso escalonado** (`sem_quantificador`,
   `sem_numero`, `sem_analise`). A linha acompanha o que AQUELE bucket pode
   dizer, célula a célula: sem número quando o piso proíbe número, sem
   célula nenhuma quando proíbe análise. A permissão já existe em código
   (`PERMISSOES_POR_ESTADO`, §D2) e é a mesma consultada aqui — não uma
   segunda regra que possa divergir dela.
4. **Filme sem bloco de eixos** (classificação ausente para aquele slug). O
   frontend cai na lista de temas anterior, sem quebrar. É o caminho de todo
   filme fora dos 35 classificados.

**Denominador: `X de N reviews classificadas`.** Distinto de "N de N
analisadas" no cabeçalho do grupo — não por preciosismo de vocabulário, mas
porque até a v1.9.14 eram duas amostras de 40 DIFERENTES (§[D3], "Duas
populações de 40"), e apresentá-las com o mesmo rótulo seria repetir
exatamente o defeito que a Entrega 6 daquela versão fechou do outro lado.
**Na v1.9.15 (Entrega 1) as duas populações foram unificadas** para os
filmes cuja classificação foi estendida — a nota de rodapé que declarava a
divergência (`denominadorNota`, `frontend/js/filme.js`) passa a exibir um
texto DIFERENTE quando `fonte_classificacao` está ausente do bloco: em vez
do caveat "não exatamente as mesmas reviews", confirma que a amostra é a
mesma. A chave `fonte_classificacao` só volta a aparecer — e o caveat com
ela — para um filme cuja seleção de produção ainda não foi estendida.

#### Busca — de decorativa a filtro real (v1.9.14)

A busca da home nunca filtrou nada: exibia "Busca em breve" e o catálogo
inteiro seguia abaixo. Com eixos, ela passa a ter um critério real —
**filtra por título e por eixo**, sobre o dado já embutido, sem rede. Digitar
`ritmo` devolve os filmes cujo bloco de eixos tem `ritmo`; digitar um título
segue funcionando como se espera. Sem resultado, a mensagem diz o que não
casou, em vez de fingir que a funcionalidade não existe.

#### Janela temporal declarada AO LADO DO DENOMINADOR (v1.9.14)

O defeito: a amostra de reviews cobre uma janela estreita (mediana ~26 dias)
enquanto o histograma de notas acumula desde 2012, e as duas frases apareciam
no mesmo parágrafo como se descrevessem as mesmas pessoas.

**Onde a declaração entra, e onde ela NÃO entra.** Ao lado do **denominador
da amostra** — *"entre as 40 reviews analisadas, escritas majoritariamente
em ⟨janela⟩"* —, **nunca** ao lado do rótulo de peso. O rótulo de peso fala
do histograma de NOTAS, que é a população acumulada da vida do filme;
carimbar nele uma janela de 26 dias inverteria o sentido e diria que 96% das
notas são recentes. É a mesma invariante de vocabulário notas × reviews da
v1.4.1, aplicada ao eixo do tempo.

**O número vem da MEDIANA, nunca da média.** Em `data` a média é ~10× a
mediana, por contaminação conhecida (`data` é a data ASSISTIDA, campo livre
de diário — há review datada de 1442 no catálogo). A média seria mais
lisonjeira (janela "mais ampla") e menos verdadeira; a mediana é robusta ao
outlier que a contaminação produz. Fonte: `janela_temporal` e
`distribuicao_pagina_origem`, ambos já calculados e persistidos desde as
v1.9.1/v1.9.2 — nenhuma coleta nova, nenhum parâmetro de coleta tocado.


---

## 4. Metadados obrigatórios no output

Por nível: `n_validas`, `n_brutas`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_descartadas_truncamento` (**v1.9.0: sempre 0** — uma truncada não resolvida não é mais *descartada*, ela fica no bruto marcada `texto_completo: false`; o número que importa passou a ser `n_indisponivel_truncamento`. O campo permanece para não quebrar consumidores existentes), `paginas_buscadas`, **(v1.9.0)** `n_alvo` (a alocação de §3[C1] para aquele nível — é o "ALVO" da ressalva 2, e sem ele a composição atingida não é interpretável), `n_indisponivel_truncamento` (persistidas mas inelegíveis por texto incompleto), **(v1.9.1)** `motivos_descarte` (dict `motivo→n` — §3[C2]; `n_descartadas_spoiler`/`n_descartadas_curtas`/`n_indisponivel_truncamento` passam a ser derivados dele, uma única fonte de verdade).
Por bucket: agregados dos níveis + `modo` (completo/reduzido/sem_analise) + **(v1.1.2)** `idioma_invalido`, `escopo_suspeito` + **(v1.9.0)** `estado_piso` (`completa`/`sem_quantificador`/`sem_numero`/`sem_analise`, §3[C3]), `composicao_alvo` e `composicao_atingida` (dicts nível→n, lado a lado — a mitigação obrigatória da ressalva 2 de §3[C1]), `cascata_por_degrau` (dict `chars`→n, quantas reviews entraram por cada degrau do relaxamento), `deficit_redistribuido` (int), **(v1.9.2)** `distribuicao_pagina_origem` (`{n, min, max, p5, p50, p95, fracao_profunda}` sobre a amostra SELECIONADA daquele bucket — §3[B'], instrumento temporal primário).
**(v1.9.0, campos ajustados nas v1.9.1/v1.9.2)** Bloco global `coleta`: `{ordenacao_usada, versao_coletor, coletado_em, paginas_gastas_por_nivel, paradas_por_limite, contagem_bruta_por_nivel, contagem_estimada_valida_por_nivel, n_reviews_bruto}` — espelha o `meta.json` do bruto (§3[B']) dentro do resultado, para que um JSON de entrega seja auditável sem abrir `dados/`. **(v1.9.1)** ganha `orcamento_paginas_por_nivel` (o orçamento dado a cada nível, derivado do orçamento por bucket — §3[B]) e `janela_temporal` (`{total, por_bucket}`, cada bloco `{n, min, max, p5, p50, p95}` — §3[B'], SECUNDÁRIA e rotulada como proxy contaminado desde a v1.9.2, não consumida pelo frontend). **(v1.9.2)** ganha `motivo_parada_por_nivel` (dict nível→`"orcamento_esgotado"`\|`"material_esgotado"` — §3[B], substitui `paradas_por_limite` como fonte primária de telemetria de parada; `paradas_por_limite` permanece, derivado, para não quebrar consumidores).
Por tema: **(v1.1.2)** `aspas_removidas`, além de `mencoes_clampadas`/`mencoes_valor_original` (v1.1.1).
Globais: `slug`, `data_coleta`, `origem` (cache/rede por página), versão da spec, **(v1.1.4)** `reviews_url`, **(v1.2.0)** `narrativa` + `narrativa_flags` (só quando `--tom narrativo|ambos`), **(v1.3.0)** `ficha` (objeto TMDB ou `null` — §3a), **(v1.3.1)** `consensos_usados` (lista de `{propriedade, grupos_de_origem, temas_de_origem}` do MOVIMENTO 2 — só quando `--tom narrativo|ambos`) + `narrativa_flags.consenso_suspeito`, **(v1.4.0)** `distribuicao` (bloco do histograma ou `null` — §3[G]) + `narrativa_flags.peso_nao_ancorado`, **(v1.4.1)** `quantificadores_usados` (lista de `{quantificador, tema}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.vocabulario_peso_suspeito`, **(v1.5.0)** `marcadores_perspectiva` (lista de `{grupo, trecho}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.perspectiva_nao_marcada`, `metricas_fluencia` (`{n_frases, media_palavras, cv_comprimento, frase_mais_curta, aberturas_repetidas, verbos_reporte, adverbios_mente}` — só quando `--tom narrativo|ambos`), **(v1.6.0)** `narrativa_bruta` (saída do narrador antes da edição, para auditoria) + `edicao_flags` (`{edicao_descartada, motivo_descarte, protegidos_perdidos, numeros_alterados, houve_retentativa, falhou, n_protegidos}` — só quando `--tom narrativo|ambos` e sem `--no-edicao`; **(v1.7.3)** `n_tentativas` (quantas chamadas o editor fez, 1 a `1 + EDITOR_MAX_TENTATIVAS`) e `motivos_por_tentativa` (lista do motivo de cada falha, na ordem — telemetria de qual checagem mais reprova, não critério de aprovação); **(v1.7.4)** `similaridade` (float 0-1, SEMPRE presente, aceita ou não a edição) e `capitalizacao_ajustada` (bool)). **A flag `narrativa_flags.fluencia_baixa` foi REMOVIDA na v1.6.0** (ver §D2, "Telemetria de fluência"). **`narrativa_bruta` e `edicao_flags` NÃO são mais gravados desde a v1.9.10**, quando o editor [E2] foi aposentado (§3[E2]) — os dois campos, e a condição "sem `--no-edicao`" que os acompanha acima, descrevem JSONs publicados ANTES daquela versão, que continuam válidos e que `render_terminal` continua sabendo ler. *(Carimbo acrescentado em 2026-09-04: a descrição estava em presente vigente e citava uma flag de CLI que não existe mais.)* Na ficha: **(v1.6.0)** `diretor_transliterado` (bool), **(v1.7.0)** `ano_fonte` (`"slug" | "letterboxd" | "argumento"`). Globais **(v1.7.0)**: `ficha_indisponivel` (`"ano_desconhecido"` — presente só quando a ficha não foi buscada por falta de ano confiável, §3[F]) e `ficha_descartada` (`{motivo, esperado, recebido}` — presente só quando o TMDB resolveu para um filme de ano divergente e a ficha inteira foi rejeitada, §3[F]); ambos ausentes do JSON no caminho normal (ficha resolvida com sucesso ou `--no-ficha`).
Por bucket: **(v1.4.0)** `share_real` (percentual inteiro), **omitido** quando não há distribuição.

**(v1.9.14) Bloco global `eixos`** — o schema do Ponto 2 (§2.5). Presente só quando existe classificação para o slug sob o `taxonomia_id` corrente; **ausente por completo** (chave não emitida) quando não existe, para que o consumidor distinga "não classificado" de "classificado e sem eixo". Estrutura:

```json
{
  "eixos": {
    "taxonomia_id": "ebab2667de74",
    "margem_lift_pp": 20,
    "contraste": "valorativo",
    "fonte_classificacao": {
      "arquivo": "resultado/votacao-3/consenso.jsonl",
      "criterio": "votacao_3_consenso_2_de_3",
      "por_bucket": {
        "negativas": {"n_classificadas": 40, "n_analisadas": 40,
                      "sobreposicao_com_analisadas": 13}
      }
    },
    "linhas": [
      {
        "eixo": "ritmo",
        "por_bucket": {
          "negativas": {"mencoes": 24, "de_n": 40, "freq_pct": 60,
                        "lift_pp": 27.5, "tema": "Ritmo lento e arrastado",
                        "exemplo_parafraseado": "…"},
          "medianas":  {"mencoes": 11, "de_n": 40, "freq_pct": 27.5,
                        "lift_pp": -32.5, "tema": null,
                        "exemplo_parafraseado": null}
        },
        "bullet_de": {"negativas": "contraste", "medianas": null}
      }
    ]
  }
}
```

`mencoes`/`de_n` são as contagens INTEIRAS — a fonte da verdade; `freq_pct` e `lift_pp` são derivados e arredondados **para exibição**. `tema`/`exemplo_parafraseado` vêm de §[D3] e são `null` quando aquele bucket não tem tema naquele eixo — célula vazia é estado, não falta de dado. `bullet_de` é `"frequencia"` | `"contraste"` | `null` por bucket, e é o que a interface lê para saber o que exibir como bullet daquele grupo. `contraste` é `"tematico"` | `"valorativo"` (§2.5), sempre acompanhado do `taxonomia_id` sob o qual foi decidido — o veredito descreve a régua atual, não o filme.


> *(→ justificativa, medição e histórico desta regra: `HISTORICO_CLASSIFICACAO.md` — "(v1.9.34) O bloco `margem`, `acima_da_margem` por célula, e um DEFEITO que a lei por `n` expôs")*

```json
{
  "eixos": {
    "taxonomia_id": "ebab2667de74",
    "margem": {
      "lei": "lift^2 * n >= 2085136/1000000",
      "constante_quadrada": [2085136, 1000000],
      "n": 40,
      "limiar_pp": 22.83
    },
    "margem_lift_pp": 22.83,
    "contraste": "valorativo",
    "linhas": [
      {"eixo": "ritmo",
       "por_bucket": {
         "negativas": {"mencoes": 24, "de_n": 40, "freq_pct": 60,
                       "lift_pp": 27.5, "acima_da_margem": true, "…": "…"}}}
    ]
  }
}
```

- **`acima_da_margem`** (bool, por célula) é calculado por `eixos.py` em
  `Fraction` exato e é **a única fonte de verdade sobre "esta célula atinge a
  margem"**. `veredito.py` e `filme.js` passam a LER este campo em vez de
  comparar `lift_pp`. A frase de invariante volta a ser verdadeira, agora por
  construção e com teste que falha se alguém reintroduzir a comparação em float.
- **`margem_lift_pp`** continua existindo e continua significando "o limiar em pp
  que governou ESTE filme" — só que agora é o **limiar resolvido** (float, uma
  casa: 22,83 para n=40) em vez do inteiro 20. É **derivado e para exibição**;
  nenhuma decisão o lê.
- **`margem`** é o bloco novo, e existe por um critério só: **um artefato precisa
  poder ser auditado sozinho, sem consultar a versão do código que o gerou.** Ele
  carrega a lei em forma **exata** (a constante como par de inteiros, e o `n`
  usado), de modo que qualquer terceiro reproduza a decisão de cada célula com
  aritmética racional e sem adivinhar nada. `limiar_pp` fica ao lado, derivado,
  para leitura humana.
- **`contraste` pode estar AUSENTE** quando `n < 10` (§2.5). `margem`,
  `margem_lift_pp` e `acima_da_margem` **continuam presentes** nesse caso — o que
  falta é só a decisão binária do filme, não a medição das células. Um consumidor
  que assuma a chave `contraste` presente quebra, e **deve** quebrar.

---


> *(→ justificativa, medição e histórico desta regra: `PROTOCOLO.md` — "5. Critérios de aceite da v1" · `HISTORICO_COLETA.md` — "6. Incógnitas de Fase 1 — RESOLVIDAS (ver `docs/arquivo-de-estudos/coleta/FASE1_INCOGNITAS.md`)" · `CHANGELOG.md` — "Changelog" · `ABERTO.md` — "Candidatos à próxima versão (pós-v1.2)")*

---

## A regra do gatilho de regeneração

*(Movida para cá na reestruturação de 2026-09-04. Estava enterrada em §2.9,
cujo título — "Defasagem entre os artefatos publicados e o consenso estendido" —
não anunciava que continha uma lei operacional travada por teste.)*

### REGRA: o gatilho de regeneração do veredito é o BRIEFING, não o ESTADO

**Reutilizável, e ela custou uma correção de rota na v1.9.34.** O plano
aprovado era regerar o veredito onde o `contraste` mudasse. **Medido antes de
disparar: o critério de estado é proxy ERRADO**, e deixaria texto publicado
descrevendo um briefing que não existe mais. Os dois casos que o provaram:

- **`anatomy-of-a-fall`** continua `tematico` dos dois lados, e o quantificador
  do grupo negativo cai de **"quase todos"** para **"a maioria"**. O texto no ar
  diz "quase todos" — sob os números novos isso é **inflação de quantificador**,
  exatamente o que a validação `quantificador_divergente` da v1.9.22 reprova.
  Manter seria publicar de propósito o que o próprio validador do projeto
  rejeitaria.
- **`barbie`** continua `tematico`, e o eixo que o veredito NOMEIA para as
  negativas muda de `comparacoes` para `roteiro_estrutura`.

**A regra:** qualquer mudança futura que altere o BRIEFING — eixo nomeado,
`assunto_compartilhado`, rótulo de quantificador, bucket dominante, estado de
piso — exige regeneração do veredito, **mesmo que o estado `contraste` não
mude**. O estado é uma das entradas do briefing, não um resumo dele.
Travado em `tests/test_aplicar_lei_margem.py::test_o_criterio_e_o_BRIEFING_e_
nao_o_estado`.
