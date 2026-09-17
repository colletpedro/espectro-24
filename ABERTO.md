# ABERTO — o que ainda é decisão

Este arquivo responde *"o que eu preciso decidir?"*. Antes de 2026-09-04 esta
lista não existia como arquivo: os itens estavam espalhados por doze lugares da
`SPEC.md`, quase sempre dentro da seção que os produziu, e por isso invisíveis
para quem não lia a seção inteira.

**O critério de saída de um item daqui é uma decisão registrada — não uma
versão nova.** É o que impede o padrão que a auditoria estrutural encontrou:
item já fechado continuar escrito como aberto, porque o lugar onde ele estava
escrito não tinha estado.

**Por onde começar:** os dois itens com número pronto para agir são o **A1**
(o `the-godfather` comparado contra uma margem revogada — o valor certo já está
ao lado do errado) e o **G1** (as 674 linhas de render que ficaram na `SPEC.md`
com medição misturada à lei). Os dois fecham por decisão, sem medição nova.

**Nada nesta lista foi corrigido na sessão que a criou.** A reestruturação moveu
texto e não alterou nenhuma regra; onde ela encontrou contradição ou erro de
fato, registrou aqui.

---

## A. Contradições e erros de fato conhecidos, NÃO corrigidos

Estes são defeitos do documento, não decisões de produto. Estão aqui porque
corrigir cada um exige uma medição ou uma decisão que a sessão de
reestruturação não tinha mandato para tomar.

### A1. `the-godfather`: 19,6pp comparado contra a margem errada — **o mais sério**

`SPEC.md`, no texto vivo do estágio `[V]`, diz que o `the-godfather` tem *"o
melhor lift das negativas em **19,6pp** contra a margem de 20"* e conclui que
falha por 0,4pp.

**A margem de 20 não existe mais.** Sob a lei por `n` (v1.9.34), o limiar
daquele filme é **26,4pp** — e a `SPEC.md` diz isso em outro lugar, na tabela
do limiar por `n`. O veredito final (`valorativo`) não muda; **o número da
comparação está errado por 6,4pp**, e o texto ensina uma régua revogada.

| | valor no texto | valor certo |
|---|---:|---:|
| lift das negativas (eixo `ritmo`) | 19,6pp | 19,6pp *(inalterado)* |
| margem comparada | **20,0pp** | **26,4pp** |
| distância до limiar | "falha por 0,4pp" | falha por **6,8pp** |

**Por que merece destaque:** a sessão de correção de contradições de 2026-09-04
varreu o documento item por item, fechou dez correções de registro e **não pegou
esta**. Quem for corrigir não precisa remedir nada — os dois números acima já
estão na própria spec, em seções diferentes.

### A2. A contagem do catálogo: `17/18` contra `6/28/1`

O estágio `[V]` inteiro opera sobre **17 `valorativo` / 18 `tematico`**, sem
carimbo de que isso mudou — inclusive nas medições de aceite e nas linhas de
base de repetição. Sob a lei por `n` o catálogo é **6 `tematico` / 28
`valorativo` / 1 sem estado**.

**Contagem de ocorrências:** a forma antiga aparece **15 vezes**; a nova, **1**.
Uma sessão que ler só o estágio `[V]` sai com a distribuição errada.

### A3. Critério 1 do aceite da v1: `10 níveis × 10 válidas`

A régua revogada na v1.9.0 sobrevive em **duas linhas** do bloco de status de
aceite, sem a nota de revogação que a seção de critérios tem.

### A4. `impacto_emocional` no corpus: 75,5% ou 75,6%?

Mesma grandeza, mesmo corpus, dois valores, nenhuma nota reconciliando:
**75,5% em 7 ocorrências**, **75,6% em 8**. Os dois estão escritos com uma casa
decimal, o que impede lê-los como arredondamento declarado.

### A5. Quatro denominadores de população, dois deles não reconciliados

| valor | ocorrências | explicado? |
|---|---:|---|
| 4.181 | 5 | **não** |
| 4.056 | 7 | sim — cobertura 100% |
| 5.371 | 5 | **não** |
| 2.866 | 7 | sim — a seleção de produção, cobertura 70,7% |

`4.181 > 4.056`, e a spec declara 4.056 como sendo 100%. Resolver exige abrir
`consenso.jsonl` / `consenso_verificado.jsonl` / `amostra.json` — não dá para
decidir pela leitura do documento.

### A6. Uma especificação que diz "implementado depois", sem versão que a feche

O caso de borda do bucket dominante em modo reduzido está escrito como
*"documentado agora, implementado depois"*. Nenhuma versão posterior diz que
foi. **Não se sabe se é lei vigente ou especificação nunca executada** — e a
diferença decide se o trecho pertence à `SPEC.md` ou ao histórico.

### A7. Três remissões apontam para alvos que não existem

| remissão | problema |
|---|---|
| *"invariante **7b de §D2**"* | §D2 não tem invariante 7b — as dele são alfabéticas. A regra (anti-fabricação de contraste) precisa ser **enunciada por extenso**, não apontada. |
| *"§ correção de recall em review curta"* | Não existe seção com esse nome. `A_regra` aparece 6 vezes e nunca é definida; o alvo real é `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md`. |
| *"§3[D] 'razão PAREADA'"* como fonte da promoção de `A_regra` | A subseção existe, mas trata do preditor de mudança de frequência. Alvo errado. |

---

## B. O estágio de CONDIÇÕES DE DECISÃO

### B1. O contrato do estágio não está especificado em lugar nenhum

O estágio está **em produção** — 257 condições no ar em 35 filmes — e ganhou
seção própria na `SPEC.md` em 2026-09-04 (`[CD]`). Mas o que foi para lá é o
texto que já existia no §0: a exceção ao princípio, as três garantias, a via de
reversão. **O contrato do briefing, as validações e o schema do bloco publicado
continuam sem especificação.**

Inventário levantado do código, como ponto de partida para quem for escrever —
**é inventário, não é a seção**:

- `src/espectro24/condicoes.py`, **1.094 linhas**.
- Superfície pública: `indexar`, `selecionar`, `ordem_das_colunas`,
  `peso_do_lado`, `peso_do_meio`, `mesmo_assunto`, `palavras_copiaveis`,
  `risco_de_spoiler`, `montar_briefing`, `serializar_briefing`, `validar`
  (com `_validar_ancora` e `_validar_discriminacao`), `extrair`, `_medir`,
  `_chave`.
- **Não é chamado por `cli.py` nem por `pipeline.py`** — roda por harness.
- O bloco publicado tem as chaves `vale_a_pena`, `talvez_evite` (cada condição
  com `texto`, `tema_origem`, `bucket_origem`, `tema_texto`, `rotulo_forca`),
  `ordem_colunas`, `peso`, `peso_meio`, `origem`, `temas_pedidos`,
  `temas_saltados`, `descartadas`, `retry`, mais a telemetria de best-of-3.
  **Desde 2026-09-14** (piloto): `sem_condicao_publicavel`, `par_desfeito`,
  `recusas_invalidas`; por condição, `origem` (só `leitura_humana` é
  gravada), `avisos` e `par_recusado`; `temas_saltados` passou a ser só o
  silêncio (sem recusas nem pares desfeitos). Ver C14.13 e C14.15.

### B2. O eixo `expectativa`: 6 condições retiradas, destino não decidido

As 6 condições do eixo foram lidas no portão editorial, marcadas para retirada
e **não publicadas** — 257 foram ao ar, não 263. A decisão pendente é se
`expectativa` alimenta as CONDIÇÕES ou pertence ao VEREDITO. É o único eixo cuja
polaridade se inverte conforme o grupo, e é isso que cria o conflito.

**2026-09-14:** `RETIRADAS` passou de 6 para **8** — entraram C030
(`get-out-2017` NEG-C) e C134 (`whiplash-2014` NEG-F), os dois do piloto. A
lista continua literal; a aplicação por REGRA (eixo de origem) está proposta,
com medição, em C14.16 — e a medição achou 2 itens `expectativa` já no ar.

**2026-09-15:** a lista SAIU do código. A R13 é aplicada por regra (C14.16
FECHADA), e os 2 itens no ar foram retirados. O destino do eixo (condições ou
veredito) continua sendo a decisão aberta deste item.

### B3. Fase 1 → Fase 2: as condições substituem o veredito?

A coexistência (condições + veredito + bullets juntos) é declaradamente **Fase
1**. Sob que critério se decide passar à Fase 2, e o que acontece com o veredito
nela, está em aberto.

### B4. A pergunta de simetria visual que a inspeção não respondeu

Com a barra no ar, os dois lados da decisão ficam visualmente simétricos mesmo
quando o peso é muito assimétrico. A inspeção não respondeu se isso é problema.

### B5. Primeira revisão humana de 100% em volume (44 filmes, lote
`expansao-44-2026-09-16`) — validação independente do experimento de
briefing, e dois achados sobre a R4

**Recusa declarada: 3,0% (11/366)**, contra a única medida anterior — 11%
(1 em 9), de um filme só (`a-brighter-summer-day`, item 5 do log de
2026-09-14). A amostra de 44 filmes é a primeira em volume; a sobre-recusa
não se confirmou nem no experimento de briefing nem aqui.

**Taxa REAL de duvidosos, medida por leitura humana de 100% dos 366 itens:
2,7% (10/366).** Próxima dos ~1,8% projetados pelo experimento de briefing
(C14.18, braço adotado) e muito abaixo dos 14,9% de antes do canal de
recusa. **Registrado como validação independente**, fora da amostra que
produziu a projeção: o resultado do experimento se confirma em volume.

**Achado 1 — a R4 (regra 7 do prompt, flag `digito` de `condicoes.validar`)
governa só o TEXTO PUBLICADO da condição, nunca a paráfrase.** Confirmado
lendo o código: `_todas_as_flags` roda `re.search(r"\d", texto)` só sobre
`cond["texto"]` — a paráfrase (`exemplo_parafraseado`) não entra na trava
que decide publicação. A frase "nunca na paráfrase" que aparece perto da
exceção de ano (linha ~566) é sobre a EXCEÇÃO não se estender à paráfrase,
não sobre a paráfrase estar sob a R4 — a paráfrase nunca esteve sob ela.
Achados reais: C031/C071 (`all-quiet-on-the-western-front-2022`/`chinatown`,
ano na paráfrase) e C320 (`the-spongebob-movie-search-for-squarepants`,
"3D" na paráfrase) — as três condições publicadas estão limpas; a regra
nunca previu bloqueá-las.

**Achado 1b — fração posicional por extenso ("um terço final", "primeira
metade") não é bloqueada por NENHUM validador hoje, e não deveria ser
tratada como se fosse.** `digito` só casa dígito literal (`\d`); as
palavras de quantidade que `quantidade_escrita` proíbe vêm do vocabulário
fechado de `_br.FAIXAS_QUANTIFICADOR` ("a maioria", "alguns"…), que não
inclui frações. Levantamento sobre os 366 do lote + os 55 publicados: só 4
condições usam fração por extenso (`district-9` "um terço final",
`joker-2019` "primeira metade", `the-brutalist` "segunda metade",
`avengers-endgame` "primeira metade" — esta descartada, mas por
`exemplo_verbatim`, sem relação). **As 4 são posicionais** (referem-se a um
trecho do FILME — "final", "primeira", "segunda" — nunca a fração de
review/espectador/nota); nenhuma usa fração para quantidade de amostra.
Amostra pequena (n=4), então "reliável" aqui é "sem contraexemplo
encontrado", não "provado".

**Critério de forma proposto (decisão do dono, 2026-09-16), na mesma lógica
da exceção de ano — por FORMA, não por intenção:** uma fração por extenso
é POSICIONAL (permitida) quando qualifica um trecho da OBRA — segue ou
precede palavra de segmento (`final`, `inicial`, `primeira`, `segunda`,
`último`, `ato`, `metragem`, `duração`, `filme`) — e é DE AMOSTRA
(proibida, seria "quanta gente" competindo com os números do código) quando
se refere a reviews/espectadores/notas/público/pessoas. Nenhum
contraexemplo nos dados atuais; qualquer caso fora dessa forma volta a ser
recusado (mesmo destino do ano fora da forma: reescrever sem a fração). Não
implementado em código — é registro de critério, não um novo validador;
decidir se vale codificar fica para quando (se) o volume justificar.

**Achado 2 — SEPARADO do Achado 1, e ainda ABERTO: existe um segundo
validador, mais estrito, que TRATA a paráfrase como proibida sem exceção, e
ele não roda em produção.** `condicoes.algarismos_proibidos_no_briefing`
verifica o BRIEFING inteiro (o que vai para o modelo, paráfrase incluída)
e não tem NENHUMA exceção de ano fora do nome do tema — é o que
`test_briefing_nao_tem_algarismo_ano_na_parafrase_nao_tem_excecao` prova
deliberadamente. Só é chamado em teste
(`test_briefing_nao_tem_algarismo_proibido_em_nenhum_filme`), não em
`condicoes.gerar()`/`cli.py` — puramente um monitor, não um portão. Esse
teste é uma das 3 falhas conhecidas da suíte (item citado no changelog de
2026-09-15, caso `woman-of-fire`) — **e os 44 pioraram, não abriram
novo**: de 2 filmes falhando (`a-brighter-summer-day` "60",
`woman-of-fire` "1960") para **7** (+ `2001-a-space-odyssey` "1968",
`all-quiet-on-the-western-front-2022` "1930", `chinatown` "1930",
`porco-rosso` "17", `the-spongebob-movie-search-for-squarepants` "3","3").
Um desses (`2001-a-space-odyssey`) mostra que a FORMA do ano também tem
falso negativo real: o tema usa "para 1968", e a preposição admitida é só
`de`/`em` — "para" não está na lista, e um ano genuíno some pela borda da
forma, o mesmo trade-off já aceito e documentado para a exceção original.
**Decisão pendente do dono:** fechar esse buraco (estender a exceção de ano
à paráfrase, do jeito que o item 6 do changelog de 2026-09-13 já cogitou e
não fez) ou aceitar formalmente que este validador é só telemetria e
nunca vai ter 100% verde. Não resolvido aqui — resolver o Achado 1 não
resolve o Achado 2, são dois portões diferentes.

**RESOLVIDO (2026-09-16) — Achado 2 fechado por decisão do dono: "passa
todos menos o porco rosso".** `algarismos_proibidos_no_briefing` passou a
mascarar, além do ano na paráfrase (item acima), duas formas novas — a
mesma regra, "por FORMA, não por intenção":
- **preposição `para`** somada a `de`/`em` (caso `2001-a-space-odyssey`,
  "impressionantes para 1968" — ano genuíno, só a preposição estava fora
  da lista);
- **década** (`"anos NN"`/`"anos NNNN"`, casos `a-brighter-summer-day`
  "anos 60" e `chinatown` "anos 1930") — **reverte** a exclusão deliberada
  anterior (`"Terror dos anos 2000"` saiu do lado FALHA do teste
  parametrizado); a década também ganhou sufixo mais solto que o do ano
  (não precisa fechar a frase, só não colar em outro dígito/`%`/decimal) —
  os dois casos reais não fechavam frase (`"...e os reflexos..."`,
  `"...1930, criando..."`) e o sufixo do ano os teria barrado de novo;
- **formato de tela** (`"3D"`/`"2D"`, caso
  `the-spongebob-movie-search-for-squarepants`) — nova categoria, não é
  ano nem fração, é nome de tecnologia de exibição.

`porco-rosso` ("personagem de **17** anos") ficou de fora por decisão
explícita — é idade de personagem, categoria que não foi pedida para
exemptar, e segue como o único filme que falha o teste hoje. Testes:
6 novos/reescritos em `test_condicoes.py`, nenhuma asserção existente
afrouxada (a que mudou de lado — `"Terror dos anos 2000"` — foi movida,
não apagada, com o motivo registrado ao lado). Suíte: 2083 passam (+5),
as mesmas 3 falhas de sempre mais esta (só `porco-rosso` agora, era 7).

### B6. Piso da barra do bullet: 14px → 12px, remedido sobre 99 filmes
(2026-09-17)

Publicar os 44 quebrou `test_o_piso_nao_alonga_nenhum_item_publicado`:
`goodfellas`/negativas ("Tratamento raso das personagens femininas e visão
masculina"), 7,5% = **11,96px** na coluna mobile (159,5px) — abaixo do
piso de 14px calibrado sobre os 35/633 itens da entrega original
(`v1.9.47`). Remedido do zero sobre 99 filmes/1780 itens, não ajustado ao
caso: distribuição completa em `min=7,5%, p1=12,5%, p5=15%, mediana=27,5%`.

**A distribuição sozinha pediria 10px** — o catálogo tem um outlier
isolado em 11,96px e o resto só recomeça em 15,95px, sem agrupamento
entre os dois; 10px fica abaixo dos dois com folga. **Mas 10px viola
`test_o_piso_ainda_le_como_traco_e_nao_como_ponto`** (`piso >= 2×altura`,
altura do traço = 6px, regra da mesma entrega `v1.9.47`): exige piso
≥ 12px para o traço não ler como ponto. **As duas regras juntas não têm
solução comum** — 11,96 < 12 — e **essa segunda regra é quem decide o
valor publicado agora**, não a distribuição.

**Publicado: 12px.** Contra o real do goodfellas (11,96px), a diferença é
0,0375px — subpixel, nenhum navegador renderiza. A tolerância que isso
exige em `test_o_piso_nao_alonga_nenhum_item_publicado` está documentada
NAQUELE teste (comentário extenso, não só aqui): teto de <1px inteiro,
reconhecendo o limite da unidade de medida — não "o suficiente para
passar o goodfellas". Qualquer item que exceder 1px de diferença real
volta a fazer o teste falhar.

**O piso só morde no mobile (159,5px).** O mesmo item mais fraco do
catálogo já dá 16,0px na coluna desktop de 3 grupos (213,3px, caso
`--3`, meio dominante) e 25,5px na de 2 grupos (340px, caso `--2`, o
comum) — nunca é a restrição lá.

**Duas opções cogitadas e NÃO tomadas nesta rodada** — registradas para
se o piso voltar a ser questão:
- **(B) Baixar a altura do traço** (hoje 6px) para algo como 5px abriria
  espaço para um piso de 10px sem violar `piso >= 2×altura` (2×5=10).
  Não feito: muda a espessura de TODA barra do catálogo, decisão visual
  maior que só o piso, e não foi pedida.
- **(C) Revisitar a proporção 2×altura em si** — é uma regra de
  legibilidade da entrega original (`v1.9.47`), não desta medição; talvez
  o mínimo para "ler como traço" não precise ser exatamente o dobro. Não
  feito: mexeria numa invariante estabelecida sem medição própria para
  justificar outro valor.

**A folga vale para 99 filmes, não é garantia permanente.** Com o
catálogo em ~300, itens abaixo de 10% deixam de ser caso isolado por
volume — remedir a distribuição inteira quando o catálogo crescer, pelo
mesmo método (não reajustar ao próximo outlier sem medir de novo).

---

## C. Pipeline e dados

### C1. `talk-to-me-2022` publicava a ficha de outro filme — FECHADA (v1.9.49)
O JSON agora publica o longa correto (`tmdb_id=1008042`, 95 minutos), com ano
editorial 2022 do Letterboxd e ano TMDB 2023 preservado na evidência. Ficha,
narrativa e veredito foram regenerados; reviews, buckets, classificação, eixos,
condições, coleta e distribuição ficaram byte-idênticos ao artefato anterior.

### C2. Guarda de identidade no pipeline — FECHADA NO CÓDIGO (v1.9.49)
Título canônico + ID direto do Letterboxd, igualdade contra o conjunto de
títulos TMDB, piso de duração independente, ausência explícita e selo de cache
versionado. As 35 entradas antigas viram miss. O fechamento de C1 no artefato
foi conferido separadamente.

### C3. Instabilidade do verificador de `impacto_emocional` (5 filmes)
Registrada, não corrigida.

**[2026-09-15] ABERTA. O trabalho de 14–15/09 NÃO a fechou: ele corrigiu
OUTRO mecanismo, que produz o mesmo sintoma.**

Dois mecanismos distintos deixam uma review CONTADA sem veredito do
verificador (`ok: False`, `impacto_emocional` mantido pela política
conservadora):

| | (A) sobrecarga do DeepSeek | (B) JSON malformado do verificador |
|---|---|---|
| o que acontece | a requisição NÃO É PROCESSADA: HTTP 200 sem `choices`, erro de fila no corpo, depois de ~900 s | a requisição É processada, a resposta chega, mas o conteúdo não parseia (`Extra data`, `Expecting ','`) |
| visto em | 14/09, C16 rodada 3 (6 de 6 chamadas, e uma de controle) | desde o piloto: as 8 falhas da rodada original e as 14 do piloto — a medição que ABRIU esta C3 |
| determinismo | estado da fila do provider, afeta qualquer texto | por review: a mesma falha numa rodada e passa em outra, e a posição do erro muda entre tentativas |
| status | **CORRIGIDO** no adaptador: detecção, prazo de parede, uma retentativa (C16 rodada 5) e disjuntor (rodada 8) | **NÃO corrigido. É esta C3.** |

**Onde isso deixa as 12 reviews que estavam sem veredito em 14/09:**
- **10 com veredito publicado:** 7 confirmam `impacto_emocional`; 3 removem.
  As remoções são `hard-to-be-a-god`/medianas, `the-cloud-capped-star`/positivas
  e `speak-no-evil-2022`/medianas. Esta última foi publicada em 15/09 por
  decisão do dono e mudou dois bullets.
- **2 sem veredito, por (B):** `whiplash-2014`/medianas e `zama`/negativas.
  Falharam de novo com a fila NORMAL (C16 rodada 7), com `JSONDecodeError` em
  posição diferente da tentativa anterior. Seguem pendentes e marcadas
  `verificacao_pendente` no JSON publicado. **Não retentadas, por decisão do
  dono:** sem entender o mecanismo, retentar é rolar o dado — pode passar, e
  o que se aprende com isso é nada.

**Para fechar esta C3 falta entender (B):** por que o modelo devolve texto
além do objeto JSON nessas reviews (segundo objeto? comentário depois do
fechamento? o `alvo` com aspas não escapadas?). Com isso, decidir entre
corrigir o parsing, o prompt, ou aceitar a taxa medida (0,19%–0,87%) com a
marca visível. Ler as respostas cruas dessas 2 reviews — hoje não
persistidas: o registro guarda só a mensagem do `JSONDecodeError` — é o
primeiro passo.

**Medição nova (piloto de expansão, 2026-09-10) — um segundo mecanismo, da
mesma família. Não corrigido.**

- **Causa das falhas:** todas as falhas do verificador são `JSONDecodeError`
  (resposta malformada do modelo: `Extra data`, `Expecting ','`) — as 8 da
  rodada original (35 filmes) e as 14 da rodada do piloto (20 novos). Não é
  filtro de conteúdo.
- **São não determinísticas.** `verificador_impacto.rodar_passe` refaz todo id
  sem registro `ok`; as 8 antigas foram refeitas na rodada do piloto e as 8
  passaram. Uma delas (`spider-man-across-the-spider-verse`, positivas,
  `viewing:1439420676`) voltou `confirma=False` e perdeu `impacto_emocional`.
- **Por que isso é instabilidade:** a política em vigor mantém a marcação
  original quando a chamada falha. A classificação publicada depende, então,
  de a chamada ter falhado naquela rodada — e muda na próxima execução do
  verificador sem mudança de dado nem de código.
- **Taxa:** 8/4.236 (0,19%) na rodada original; 14/1.605 (0,87%) nas reviews
  novas.
- **Efeito medido** (bloco recalculado com `eixos.montar_bloco`; o cálculo sobre
  o snapshot reproduz o bloco publicado exatamente):
  - `spider-man`: estado (`valorativo`), margem e bullets inalterados;
    `impacto_emocional`/positivas 17→16 de 40 (42,5%→40,0%); lifts do eixo
    deslocam 2,5pp (negativas −5,0→−2,5, medianas −20,0→−17,5, positivas
    +5,0→+2,5), todos longe da margem de 22,83pp. O JSON publicado continua
    dizendo 17 até ser republicado.
  - 12 filmes novos com review falha: se a review falha perdesse o eixo,
    nenhum contraste muda e nenhuma célula cruza a margem — **mas em
    `speak-no-evil-2022` os bullets das medianas mudam** (`impacto_emocional`,
    `comparacoes`). Um bullet publicado dependendo de uma falha de parse.
- **Relação com os 5 filmes** (`dune-2021`, `eighth-grade`,
  `im-still-here-2024`, `napoleon-2023`, `the-godfather`, CHANGELOG v1.9.34),
  que trocam de estado conforme o verificador rodou ou não: nenhuma das 8
  reviews reprocessadas é desses 5. Mesma família (a classificação publicada
  depende de um estágio instável), causa diferente (falha de parse + política
  conservadora + retomada que refaz a falha).

### C4. Feelings — em espera, com dependência de ordem
Nada implementado, nada autorizado. A tabela review-derived × work-derived é lei
de uma coisa que não existe.

### C5. Proposta temporal S1/S2/S3 — recomendação S2, não aplicada
E, **dentro dela**, um defeito medido do comportamento **em vigor**: a seleção
não lê `ordenacao_origem`, então classifica material de `by/added-earliest`
como faixa rasa/recente. Medido: a mistura de material antigo varia de 1 a 19
por bucket, e varia dentro do mesmo filme.

### C6. Backfill barato de cota
Registrado, não decidido.

### C7. Backup de `dados/bruto/`
Não existe política. O bruto é o artefato que torna todo reprocessamento
gratuito; perdê-lo custa a coleta inteira.

### C8. Decisão de expansão: mais filmes ou mais reviews por filme?
As duas competem pelo mesmo orçamento e movem métricas diferentes.

### C9. Cache do TMDB acima de 6 meses — dívida contratual, sem política

### C10. `passadas` do `meta.json` são apagadas na republicação
`persistir()` sobrescreve o histórico. Dívida conhecida, registrada, não
resolvida.

### C11. `load_dotenv` dentro de `classificar()`
Dívida registrada: a função de biblioteca altera o ambiente do processo,
contra a regra de ambiente do protocolo.

### C12. `anthropic_client_call` sem retentativa
O terceiro ponto de contato do adaptador, registrado e não consertado.

### C13. FECHADA em v1.9.50 — `obsession-2026` era a página do curta
A página canônica do longa existe em `obsession-2025` e declara diretamente
o `tmdb_id=1339713`. O curta saiu do catálogo, da amostra e do consenso; seu
bruto continua preservado apenas para auditoria e é excluído por código. O
longa foi recoletado e todos os estágios dependentes das reviews foram refeitos.
O link público agora aponta para as reviews do longa. O override de ficha, que
mascarava a divergência entre corpus e ficha, foi removido.

### C14. BLOQUEANTES DA EXPANSÃO (~300 filmes) — medidos no piloto de 20 (2026-09-10)
Registrados pelo piloto da ETAPA 0 (estudo untracked em
`docs/arquivo-de-estudos/piloto-expansao/ETAPA_0_PROPOSTA.md`). Corrigidos
até agora: 1 (descarte silencioso no consenso, 2026-09-15), 6 (crash de
n<10), 8 (recoleta na publicação; `get-out-2017` republicado com n=40 em
2026-09-15) e 16 (R13 por regra, 2026-09-15). Enquanto qualquer um estiver
aberto, os 300 não devem ser disparados.

1. **Filme novo é descartado pelo consenso em silêncio, DEPOIS das chamadas
   pagas.** `scripts/estender_classificacao_producao.py` acrescenta reviews a
   `amostra["reviews"]`, mas não registra o filme em `amostra["filmes"]`; e
   `votacao_3.cmd_consenso` filtra por `amostra["filmes"]` (`votacao_3.py:276`).
   Medido no piloto: 7.068 chamadas classificaram 2.356 reviews dos 20 e o
   consenso saiu com as mesmas 5.488 linhas de antes, sem erro nem aviso.
   Contornado À MÃO: as 20 entradas foram geradas por
   `classificar_10.montar_amostra()` em memória e acrescentadas só por
   apêndice (as 35 entradas conferidas idênticas antes/depois). **Não escala
   para 300.** Achado lateral: 7 das 35 entradas de `amostra["filmes"]` têm
   `n_por_bucket` defasado (`dune-part-two`, `eighth-grade`, `pearl-2022`,
   `talk-to-me-2022`, `the-godfather`, `wicked-2024`, `wonka` — bruto
   recoletado em 22/08, entradas de 10–16/08). Nenhum leitor de produção lê o
   campo (`eixos.carregar_classificacao` lê só `taxonomia_id`).

   **RESOLVIDO (2026-09-15).** Verificado antes de implementar, zero rede:
   - **O contorno manual produziu o que o caminho oficial produz.** As 55
     entradas foram comparadas campo a campo, e na ordem das chaves, com
     `montar_amostra()` rodado hoje sobre o bruto. 48 são idênticas, e **as
     20 do piloto estão entre elas**: nenhum metadado divergente. As 7
     diferentes são as 7 dos 35 nomeadas acima, e só em `n_por_bucket`.
   - **O achado lateral continua verdadeiro depois da correção.** As 7
     seguem defasadas, e registrar não reescreve entrada existente (há teste
     para isso). Quem lê `amostra["filmes"]`: o consenso lê só `slug`, os
     relatórios de `votacao_3`/`gate_taxonomia` leem `perfil`, e o único que
     lê `n_por_bucket` é o relatório de estudo de `classificar_10.py`.
   
   Correção:
   - `classificar_10.entrada_do_filme(slug)` é a entrada de UM filme,
     extraída de `montar_amostra()`; a saída deste é byte a byte idêntica
     (4.677.771 bytes, antes e depois).
   - `estender_classificacao_producao.py` registra o filme por essa função
     ANTES da primeira chamada paga, e registra também quando não falta
     review: é o conserto gratuito do estado do piloto. Em seguida confere o
     registro e recusa pagar se ele faltar.
   - `votacao_3.cmd_consenso` chama `checar_filmes_registrados` antes de
     escrever: filme com review na amostra, ou classificado nos passes, fora
     de `amostra["filmes"]` levanta `FilmeForaDaAmostra`, e o consenso não é
     gravado. O único descarte que continua permitido é o do filme retirado
     de propósito (`SLUGS_BRUTOS_RETIRADOS`; hoje `obsession-2026`, 38
     registros por passe).
   - Testes: `tests/test_registro_filme_amostra.py` (12). Cobrem a falha alta
     (inclusive o estado exato do piloto), o registro com a entrada de
     `montar_amostra()`, o registro antes do primeiro passe, a
     idempotência, o dry-run que não grava, e a recusa de pagar sem
     registro.
   - Primeiro uso real: `get-out-2017` (item 8). A reexecução do dry-run
     depois dele dá 0 faltantes.
2. **`--republicar-tudo` sem `--slug` republica os 32 do catálogo**
   (`publicar_catalogo.filmes_pendentes`), refazendo a coleta de rede e
   apagando `passadas` (C10). A guarda `LIMITE_LOTE_SEM_CONFIRMACAO = 5` exige
   a flag para qualquer lote de filmes NOVOS acima de 5, e a flag não
   distingue "estes N novos" de "o catálogo inteiro". O piloto publicou em 4
   lotes de 5 para nunca passá-la; para 300 seriam 60 lotes.
3. **`synthesize.uso()` ignora `thoughts_token_count` do Gemini.** O `uso`
   gravado em `narrativa_selecao`, `veredito` e `condicoes` conta só
   `candidates_token_count`; o raciocínio (budget fixo na prosa,
   `PROSA_THINKING_BUDGET`) é cobrado como saída e fica fora. Todo relatório
   de custo de Gemini feito a partir dos JSONs publicados subestima a saída.
   **Medido no piloto** (contadores crus instrumentados em 15 publicações):
   por filme, 11.221 tokens de entrada, 1.384 de saída visível e **10.173 de
   raciocínio**. Custo real da narrativa US$ 0,0518/filme contra US$ 0,0136
   sem o raciocínio — **3,8× o que o `uso` gravado permite calcular**. É o
   maior item de custo por filme do pipeline. **Custo real total, medido,
   por filme (classificação + verificador + síntese + rotulagem +
   narrativa; sem veredito, não gerado no piloto): ~US$ 0,10.** O preço do
   Gemini 3.7 Flash usado nesta conta (US$ 0,75/M entrada, 3,75/M saída)
   **dobra em 1/1/2027** (1,50/7,50) — qualquer projeção de custo para os
   300 feita depois dessa data precisa recalcular, não só reescalar.

   **2026-09-15 — a subestimação NÃO é a mesma em todo estágio Gemini.**
   Medida agora em condições (item 18): 2,25×, não 3,8×. As duas ficam
   registradas, com o estágio ao lado — usar a de um estágio no outro erra.
4. **Scraping: 23,7 h medidas para 300, não 16 h.** 284 s/filme (mediana
   256, 177–457), 115,8 req/filme a 2,46 s/req. A projeção anterior usava o
   perfil do lote 1 (77,7 req/filme). Filmes obscuros pedem MAIS requisições
   (`satantango` 187, `hard-to-be-a-god` 174, `zama` 149): a expansão, que é
   de filme obscuro, tende a ser pior que a média do piloto. **Projeção do
   PIPELINE INTEIRO, medida ponta a ponta no piloto:** scraping 284 s +
   classificação ~51 s + verificador ~12 s + publicação 60 s + condições
   ~18 s ≈ 7 min/filme → **~35 h para 300**, e **~US$ 31** pelo custo real
   do item 3 (sem veredito, que não foi gerado no piloto e falta medir).

   **2026-09-15 — custo recalculado no item 18: ≈ US$ 33 hoje, ≈ US$ 58
   depois de 1/1/2027.** A diferença para os ~US$ 31 aqui é o braço de
   condições adotado (0,0324/geração medido, contra 0,025 estimado).
5. **Disco — bloqueante condicional.** Medido **3,2 GiB livres (99%)** em
   2026-09-10, antes da coleta; em 2026-09-13 o volume tem **32 GiB livres
   (84%)**, espaço liberado fora da sessão do piloto. O cache HTML
   (`resultado/cache/`, gitignored, sem cópia) cresceu 133 MB com os 20
   (309→442 MB, ~6,7 MB/filme): **~2,0 GB para 300**. Com 3,2 GiB, bloqueava;
   com 32 GiB, não. Medir o disco imediatamente antes de disparar.
6. **CORRIGIDO (2026-09-13). Filme com bucket n<10 derrubava a publicação.**
   `woman-of-fire` (negativas n=9): a lei omite a chave `contraste` de
   propósito (`eixos.contraste` → `None`, §2.5), mas `cli.py:348` indexava
   `bloco['contraste']` direto e levantava `KeyError` — o filme não
   publicava. Fix: `bloco.get('contraste', 'sem_estado (n<10)')` — a linha
   de telemetria vira aviso explícito em vez de quebrar o processo; nenhum
   outro comportamento muda. Trava por teste:
   `tests/test_cli_tom.py::test_bloco_sem_contraste_nao_quebra_o_cli`
   (confirmado reproduzindo o `KeyError` real antes do fix, revertendo só
   `cli.py` e rodando o teste isolado). **REPUBLICADO em 2026-09-13** (já com
   o `--offline` do item 8): 57,4 s, **0 requisições de rede**, `n = 9`
   (negativas `sem_quantificador`/`reduzido`), limiar 48,13pp, chave
   `contraste` AUSENTE — o estado "não medido" da lei, não `valorativo`;
   `dados/bruto/woman-of-fire/*` byte a byte idêntico ao de antes. **Dois
   testes passaram a apontar o filme, e os dois estão CERTOS — decisão do
   dono, nenhum afrouxado:**
   - `test_aplicar_lei_margem.py::test_o_catalogo_publicado_esta_sob_a_lei`
     (`sem == []`): primeiro filme PUBLICADO sem estado de contraste — o
     docstring do teste diz que "É AQUI que precisa aparecer". Ou o
     catálogo aceita filme sem estado (a asserção vira lista explícita), ou
     `woman-of-fire` sai do ar.
   - `test_condicoes.py::test_briefing_nao_tem_algarismo_proibido_em_nenhum_filme`:
     a síntese nova de POS-A é *"Comparação com a obra original de 1960"* —
     o NOME passa na exceção de ano (item 10), mas a PARÁFRASE repete o ano
     (*"…a versão original de 1960, notando…"*) e a paráfrase não tem
     exceção. Segundo caso real em dois dias; pega ANTES de gerar condições
     do filme. Estender a mesma forma à paráfrase passaria este caso
     (`de 1960` seguido de vírgula) — é decisão de escopo, não foi feita.
7. **Filtro de conteúdo do DeepSeek derruba um filme inteiro.**
   `a-brighter-summer-day`: a síntese de bucket recebe `400 Content Exists
   Risk` e o CLI sai com rc=1. Determinístico — o filme não publica com o
   pipeline atual. A classificação já tinha perdido uma review do mesmo filme
   pelo mesmo erro nos 3 passes (`viewing:1343536508`); não foi verificado se
   é a mesma review que derruba a síntese. 1 de 20 filmes no piloto.
   **Achado de 2026-09-13 (zero rede):** a amostra que a seleção dá hoje
   para as positivas CONTÉM `viewing:1343536508` — a review que a
   classificação não conseguiu classificar. Mesmo que a síntese passasse, a
   guarda do item 8 recusaria o filme no bloco de eixos.
   **Registrado como limitação conhecida por decisão do dono (2026-09-13) —
   nenhum contorno tentado.** Qualquer solução (capturar o erro por bucket e
   seguir sem aquele tema, trocar de provider só para o bucket afetado,
   pré-filtrar o texto) é decisão de produto, não deste piloto.
   **RESOLVIDO (2026-09-14) por decisão do dono: fallback DeepSeek → Gemini
   SÓ na recusa de conteúdo, marcado no dado. Filme republicado com n = 40
   nos três buckets — ver C16.**
8. **CORRIGIDO NA CAUSA (2026-09-13) — `get-out-2017` continua
   contaminado.** A publicação recoletava e deslocava a amostra DEPOIS da
   classificação. Investigado e relatado primeiro; (A) e (B) implementados
   depois, por decisão do dono — ver o fim do item.

   **Causa raiz, confirmada lendo o código:** `publicar_catalogo.publicar_um`
   invoca `python -m espectro24.cli --slug X --tom ambos` — **sem
   `--offline` e sem `--reuse-synthesis`**. `cli.main` sem essas flags chama
   `pipeline.run_pipeline`, que SEMPRE roda `collect_all_levels` (coleta de
   rede, respeitando cache por URL, mas capaz de buscar página nova). O
   Letterboxd é um site VIVO: qualquer intervalo de tempo entre "classificar
   o corpus" (que congela `amostra["reviews"]`/`consenso_verificado.jsonl`
   num instante) e "publicar" (que roda `run_pipeline` de novo, sem
   `--offline`) está exposto a reviews novas chegarem no meio, serem
   raspadas, e serem selecionadas para o JSON publicado sem nunca ter
   passado por classificação.

   **Medido:** `get-out-2017` — bruto cresceu de 826 para 862 reviews
   durante a publicação (3 requisições de rede novas, confirmadas no
   stderr do CLI); uma review nova (`viewing:1493797951`) entrou nas 40
   analisadas do bucket positivas sem ter sido classificada; `eixos.
   _filtrar_pela_analisada` não tem como preencher o buraco (só remove,
   nunca completa) e o denominador publicado caiu de 40 para 39 (limiar
   23,12pp em vez de 22,83pp) — SILENCIOSO: nenhum erro, nenhum aviso,
   só um número um pouco menor. 1 de 18 filmes publicados no piloto. O
   intervalo neste caso foi de minutos (classificação e publicação na
   mesma sessão); num pipeline real de 300 filmes rodado em etapas
   separadas por horas ou dias, a janela de exposição é maior.

   **Duas opções de guarda, como foram registradas (as duas IMPLEMENTADAS
   depois — ver abaixo):**

   - **(A) — estrutural.** Acrescentar `--offline` à chamada do CLI em
     `publicar_catalogo.publicar_um`. Torna a invariante "a amostra não
     muda entre classificação e publicação" verdadeira POR CONSTRUÇÃO: sem
     rede, `run_pipeline` só pode ler o bruto já persistido, e a seleção
     reproduz exatamente o que a classificação já viu. Risco a verificar
     antes de aplicar: todo filme classificado passou antes por `lote.py`
     (coleta completa, cacheada) — nenhum caso hoje deveria precisar de
     rede na publicação; um filme publicado por um caminho que pule
     `lote.py` quebraria com `FetchError` em vez de silenciosamente
     recoletar. Ficha/distribuição já degradam graciosamente sob
     `--offline` (capturam `FetchError`), então não deveriam ser afetadas.
   - **(B) — defensivo, complementar a (A).** Uma asserção em
     `eixos.montar_bloco`/`_filtrar_pela_analisada` (ou em `cli.py`, antes
     de publicar) que FALHA ALTO — não encolhe `n` em silêncio — quando
     `analisadas` contém um id ausente de `classificacao`. Pega a MESMA
     classe de defeito não importa a causa (recoleta, um bug futuro em
     `estender_classificacao_producao.py`, edição manual do corpus), então
     vale mesmo se (A) for aplicado.

   **IMPLEMENTADO (2026-09-13).**
   - (A) `publicar_catalogo.publicar_um` roda o CLI com `--offline`.
   - (B) `eixos.checar_amostra_classificada` levanta `AmostraNaoClassificada`
     quando alguma review ANALISADA está fora da classificação (a direção
     inversa — classificada sem estar analisada — é o acúmulo legítimo de
     §[D3] e continua filtrada). Roda em três pontos: `montar_bloco`
     (qualquer caminho), `pipeline.montar_eixos` ANTES da rotulagem (não paga
     [D3] num filme que vai ser recusado; o CLI sai com código 6 e não grava
     nada), e `publicar_catalogo.checar_amostra_antes_de_publicar`, ANTES do
     subprocesso, com zero rede e zero LLM (recusa vai para o log e o lote
     segue).
   - Medido antes de ligar, zero rede: nos 55 classificados, só
     `get-out-2017` e `a-brighter-summer-day` têm review analisada fora da
     classificação.

   **`get-out-2017` NÃO sai com n=40, e (A) sozinho não resolveria:** o
   bruto já absorveu a contaminação (862 reviews), então a seleção OFFLINE
   de hoje continua escolhendo `viewing:1493797951`. Recusado nas duas
   guardas com o dado real (a do harness e o CLI com `--reuse-synthesis
   --offline`, rc=6; `resultado/` e `dados/bruto/` intocados). Voltar a
   n=40 exige classificar essa uma review (chamadas pagas, e passa pelo
   defeito do item 1), porque aparar o bruto está fora de questão. **Até lá
   o arquivo em disco continua o do piloto, com n=39.**

   **Achado lateral: o checkpoint não enxerga a contaminação.** Rodar
   `publicar_catalogo.py --slug get-out-2017` PULA o filme ("já publicado
   sob 1.9.50"): `_ja_publicado` só olha `spec_version` e
   `verificador.aplicado`, então o JSON com n=39 conta como em dia e nem
   chega à guarda. Não corrigido.

   **Dois testes passaram a falhar, e são a guarda achando `get-out-2017`
   no dado real:** `test_aplicar_lei_margem.py::test_a_selecao_E_chamada_e_
   isso_e_CORRETO` e `::test_o_plano_nao_escreve_nada`. Nos dois,
   `planejar()` percorre o catálogo publicado e recusa ao reconstruir
   `get-out-2017`. Com o filme excluído, `planejar()` passa nos 52 restantes.
   Harness e testes intocados: voltam a passar quando a amostra do filme
   voltar a ser consistente.

   **FECHADO (2026-09-15): `get-out-2017` republicado com n=40, por decisão
   do dono (classificar a review).**
   - **Classificação.** Feita pelo caminho oficial já corrigido (item 1):
     `estender_classificacao_producao.py --slug get-out-2017`. Uma review
     (positivas, `viewing:1493797951`), 3 chamadas DeepSeek, todas `ok`,
     nenhum fallback.
   - **Consenso.** Passou de 7.844 para 7.845 linhas. Pelo hash por filme,
     só `get-out-2017` mudou (120 → 121).
   - **Verificador.** `aplicar-producao --slug get-out-2017`: 1 chamada,
     `confirma=False`. `impacto_emocional` sai da review, que fica com
     `atuacao`, `expectativa`, `roteiro_estrutura` e `tom_atmosfera`. No
     consenso verificado só `get-out-2017` mudou;
     `n_removidas_no_corpus` foi de 2.784 para 2.785. As 2 pendentes da C3
     não foram tocadas.
   - **Medido antes de gravar** (`republicar_eixos.py`, sem `--aplicar`):
     - contraste continua `valorativo`;
     - nenhuma célula cruza a margem;
     - bullets idênticos;
     - briefings de narrativa, veredito e condições idênticos;
     - `n` vai de 39 para 40, e o limiar de 23,12 para 22,83 pp.
   - **O efeito do lift relativo apareceu, sem cruzar.**
     `tom_atmosfera`/negativas é de um bucket que não foi tocado, e o lift
     dela vai de −21,1 para −22,5 pp. `critica_social`/medianas continua em
     −22,5, mas o limiar desce. As duas ficam 0,33 pp abaixo da margem,
     a mesma distância de `speak-no-evil-2022`.
   - **Gravado** com `--aplicar --aceitar-mudanca-de-estado`: a única
     mudança de estado é o `n`, que era o pedido. Só a chave `eixos` mudou.
     `fonte_classificacao` sai, porque só existe quando classificada ≠
     analisada.
   - **Testes.** Os 2 testes de `test_aplicar_lei_margem.py` acima voltaram
     a passar.
   - **Condições publicadas (2026-09-15, aval do dono).** Saíram do lote
     corrigido do piloto com `publicar_condicoes --slug get-out-2017`: 7
     condições (3 em `vale_a_pena`, 4 em `talvez_evite`), com C030 (NEG-C)
     retida pela regra. No arquivo, só `condicoes` entrou, no fim; o resto
     ficou na ordem.
   - **Continua aberto.** O achado lateral do checkpoint (`_ja_publicado`
     não enxerga contaminação) não foi corrigido.
9. **A busca da home não indexa o título do Letterboxd** (complementa E2). Ela
   indexa `ficha.titulo` (pt-BR do TMDB) e o slug; com filme internacional, o
   título que o leitor conhece falha: "memories of murder" e "get out"
   devolvem 0 (só "memorias", "corra" ou o slug com hífen acham). E os eixos
   quase não filtram: "roteiro" devolve 51 de 53 filmes (96%; com 35 eram
   33, 94%), "impacto" 31 de 53.
10. **CORRIGIDO EM PARTE (2026-09-13). A suíte fixava o catálogo em 35.**
    Com os dados do piloto no disco: baseline 1822 coletados, 1813 passam,
    **8 falham**, 1 xfail; os mesmos 8 passavam num worktree limpo do
    `HEAD` — confirmando que a causa era o DADO (catálogo maior), não uma
    asserção errada. **Seis foram desacoplados do número/lista fixa, SEM
    afrouxar o que provam** (ver detalhe de cada asserção, antes/depois, no
    relato da sessão):
    - `test_catalogo_tem_os_35_filmes_classificados` →
      `test_catalogo_tem_todos_os_filmes_do_catalogo_classificados`: em vez
      de `len(catalogo) == 35`, `set(catalogo) == <slugs de
      votacao-3/consenso.jsonl>` — a mesma fonte que `build_data.py`/
      `publicar_catalogo.py` usam, não mais um glob cego.
    - `test_catalogo_reproduz_7_tematicos_e_28_valorativos` →
      `test_catalogo_reproduz_o_contraste_publicado`: em vez de
      `(len(tematicos), len(valorativos), len(sem_estado)) == (7, 28, 0)` +
      lista exata, compara o `contraste` RE-DERIVADO (via `E.contraste`,
      sem passar por `montar_bloco`) contra o PUBLICADO em cada
      `resultado/<slug>.json`, filme a filme — mais estrito, não mais
      frouxo: aponta QUAL filme diverge, não só "o total mudou". Achado no
      caminho: `sem_estado == []` estava incorreto como invariante absoluto
      — `woman-of-fire` (classificado, não publicado) tem n=9 e
      legitimamente fica sem estado; a comparação nova lida com isso sem
      caso especial (`publicado.get("contraste")` é `None` nos dois lados).
    - `test_o_catalogo_publicado_esta_sob_a_lei`: escopo trocado de
      `resultado/*.json` (glob cego) para o catálogo canônico
      (`consenso.jsonl`); `(7, 28, 0)` cai, ficam `"margem" in e` (migração
      completa), `sem == []` (agora corretamente escopado só a filmes
      PUBLICADOS), soma bate com o catálogo, `obsession-2025` em tematico.
    - `test_filmes_padrao_sao_os_32_faltantes` →
      `test_filmes_padrao_sao_o_catalogo_menos_os_ja_publicados`: em vez de
      `len(faltantes) == 32`, `set(faltantes) == <catalogo> -
      JA_PUBLICADOS_ANTES`, lendo `consenso.jsonl` de novo (não via
      `pc.catalogo_completo()`) para provar que a função lê o arquivo
      certo, não só que concorda consigo mesma.
    - `test_base_da_projecao_reproduz_10_de_35`: `corpus` (que cresce com
      a expansão) agora é FILTRADO aos 35 slugs originais, nomeados
      explicitamente (`_SLUGS_35_ORIGINAIS`) — os números (12, 35) não
      mudaram, só pararam de quebrar quando um filme novo é classificado.
      Ampliar o escopo do teste para o catálogo novo é decisão separada.
    - `test_peso_meio_usa_a_regua_do_DEFEITO_e_nao_uma_proxy`: `com_linha
      == alvos` (igualdade) virou `alvos <= com_linha` (subconjunto) — os
      8 filmes conhecidos continuam obrigatórios; um filme A MAIS
      satisfazendo o critério deixou de ser falha, porque um catálogo maior
      ter mais candidatos não é regressão da régua (a prova de que ela não
      é a proxy errada continua sendo `pearl-2022` ficar de fora).

    **Dois ficam abertos — achados reais, não contagem, decisão do dono:**
    - `test_briefing_nao_tem_algarismo_em_nenhum_dos_35` — o tema NEG-F de
      `pinocchio-2022` é *"Comparação com o clássico de 1940"*; a garantia
      "zero dígitos" do briefing de condições reaberta por um filme novo.
      **FECHADO (2026-09-13) com a exceção de ano em nome de tema**, aprovada
      pelo dono e decidida por FORMA (`condicoes.algarismos_proibidos_no_
      briefing`, registrada também em SPEC.md §[CD]). O teste virou
      `test_briefing_nao_tem_algarismo_proibido_em_nenhum_filme`, e mais 25
      casos cobrem os dois lados (4 formas de ano que passam, 18 de
      quantidade ou fora da forma que falham, ano na paráfrase falha, ano no
      texto da condição continua reprovado). Voltou a falhar por OUTRO filme,
      `woman-of-fire` (ano na paráfrase — item 6).
    - `test_o_primeiro_quadro_da_faixa_e_o_backdrop_publicado_ou_gemeo_dele`
      — **achado NOVO desta sessão.** `guillermo-del-toros-pinocchio` junta
      os 7 filmes conhecidos cujo hero (primeiro quadro da faixa de stills)
      colapsa num gêmeo perceptual (pHash) do backdrop publicado em vez de
      SER o backdrop. Este teste é uma ALLOWLIST deliberada — o próprio
      docstring diz que um oitavo caso "precisa ser uma conversa, não uma
      surpresa" — por isso NÃO entra no grupo dos seis: decouplar a lista
      aqui apagaria exatamente o sinal que o teste existe para dar. Fica
      travado no `HEAD` limpo; decisão de incluir `guillermo-del-toros-
      pinocchio` na lista (aceitar o padrão) ou investigar por que o
      colapso acontece é do dono.

    Suíte depois do desacoplamento: **1823 coletados** (+1, o teste novo do
    item 6), **1820 passam**, **2 falham** (os dois acima), 1 xfail.

    **Suíte em 2026-09-13, depois dos itens 6, 8 e 12: 1861 coletados**
    (+38 testes novos), **1855 passam, 5 falham, 1 xfail.** As 5 falhas:
    a do hero, aberta de propósito; as duas de `get-out-2017` (item 8); e as
    duas de `woman-of-fire` (item 6).
11. **~2.300 itens de condição para LEITURA HUMANA nos 300 — gargalo não
    contabilizado.** Medido no piloto: 138 itens de condição gerados em 18
    filmes (7,7/filme, `resultado/votacao-3` não tocado — geração de estudo,
    fora de `resultado/`). O §0 exige leitura humana de 100% antes de
    publicar o bloco `condicoes` (garantia estrutural, não cerimônia — é o
    que sustenta a exceção do estágio). Projetando 7,7/filme para 300:
    **~2.300 itens**, um a um, por uma pessoa. Isto NUNCA apareceu nas
    projeções de tempo/custo desta sessão porque elas só somam trabalho de
    MÁQUINA (scraping, LLM); o item 4 (~35h/~US$31 para 300) é o pipeline
    até a publicação SEM condições — a leitura humana de 2.300 itens é
    tempo adicional, do dono, fora da conta.

    **2026-09-15 — recalculado no item 18 sob o briefing adotado: ≈ 44
    itens para leitura humana em 300 filmes**, não ~345. É a mesma taxa
    medida em 55 filmes aplicada à escala, não medição direta em 300.
12. **Relatório de revisão por lote — contorno do item 11, não solução
    (2026-09-13).** `scripts/relatorio_revisao_condicoes.py` gera, por
    lote, um markdown autocontido para o dono passar À MÃO por uma IA
    revisora, fora do pipeline. A revisora separa os duvidosos e o dono
    continua sendo quem decide. O relatório não aprova, não pontua e não
    recomenda: cada categoria declara se o detector dela é exato, medido ou
    não medido. Primeiro exemplo real, untracked:
    `docs/arquivo-de-estudos/revisao-condicoes/RELATORIO_piloto-18.md`
    (insumo copiado ao lado; o original estava num `/tmp` de outra sessão).
    141 itens (138 + 3 descartados), 112 sem categoria.
    **"Sem categoria" não quer dizer seguro:** o detector de spoiler deixa
    passar ~2 em 5 casos reais (medido, n=5), e o de acionabilidade não tem
    medição. Se a revisora externa merece confiança é algo que ninguém
    mediu: mesmo modo de falha dos validadores deste projeto, só que agora
    fora do código.
    **Resultado da primeira volta (2026-09-13):** 120 confirmados, 21
    duvidosos; o dono corrigiu 18 e recusou 3. O lote corrigido está em
    `docs/arquivo-de-estudos/revisao-condicoes/lote-piloto-18-corrigido/`,
    com as correções verbatim e o insumo original intacto. Não publicado —
    ver item 15. Análise completa:
    `docs/arquivo-de-estudos/revisao-condicoes/PROPOSTA_POS_REVISAO_PILOTO_18.md`.
13. **"Sem condição publicável" — IMPLEMENTADO em 2026-09-14 (estado no fim
    do item); falta medir a taxa de recusa na primeira geração.** O dono recusou C024 e C089 (R6, desfecho) e C051
    (R2, a queixa é o tema), por não terem condição honesta possível; nos
    300, o caso volta. MEDIDO:
    - **Recusa silenciosa já existe, recusa com motivo não.** O modelo pode
      saltar um tema pela regra 6 (5 saltos nos 18), mas não há "recusa com
      motivo".
    - **A marca de spoiler não bastou.** C024 e C089 saíram do briefing com
      "ATENÇÃO — toca desfecho… SALTE o tema", e o modelo escreveu os dois.
    - **O best-of pune a recusa.** A chave é "mais temas cobertos": em
      `speak-no-evil-2022` os candidatos cobriram 7, 4 e 7, e o de 4 perdeu.

    Proposta:
    - lista `sem_condicao` na saída do modelo, com regra de um conjunto
      fechado e motivo curto;
    - recusa declarada conta como tema resolvido na chave do best-of;
    - a seleção NÃO cai para o próximo tema (princípio vigente; nenhuma
      coluna zerou no piloto), e coluna vazia bloqueia o filme;
    - par obrigatório: se o forçado é recusado, o de base fica marcado
      `par_recusado` para revisão; se o de base é recusado, o par se desfaz;
    - seção própria no relatório: "a recusa procede?".

    **Achado lateral, MEDIDO:** itens que entram por par obrigatório são
    duvidosos em 26% (9 de 34), contra 11% dos de base; e, pela leitura
    (VISTO), 12 a 14 dos 38 pares se formam só por palavras de discurso
    ("descreve", "experiência", "considera"). C134, de `expectativa`,
    entrou por um desses.

    **2026-09-14 — IMPLEMENTADO como aprovado pelo dono.** A saída do modelo
    ganhou `sem_condicao: [{tema_origem, regra, motivo}]`; `validar_recusa`
    confere tema pedido, regra do conjunto fechado (R1, R2, R6, R12, R13; mais
    de uma com barra, como o "R6/R12" do dono) e motivo de até 20 palavras;
    tema nas duas listas vira `tema_repetido` nas duas pontas. Chave do
    best-of: `(-resolvidos, flags, -escritos, índice)` — recusa declarada e
    válida conta, silêncio não, e no empate vence quem escreveu. O bloco
    ganhou `sem_condicao_publicavel` (o `motivo` sai em `frontend/build_data`,
    nunca vai à página), `par_desfeito` e `recusas_invalidas`;
    `condicoes.consolidar_recusas` aplica o par (`par_recusado` no base,
    forçado para `par_desfeito`), e `publicar_condicoes` recusa bloco não
    consolidado e **coluna vazia**. Relatório: seção "Sem condição
    publicável" antes de "descartada", categorias `par_desfeito` /
    `par_recusado`, regra de topo "publicar menos não é defeito". As 3
    recusas do dono estão no lote corrigido com `origem: leitura_humana`
    (C024 marca `force-majeure` POS-B como `par_recusado`).

    **Continua aberto:**
    - **taxa de recusa** — só existe na primeira geração sob o canal novo;
      nenhuma geração foi feita nesta sessão. **MEDIDA no item 18
      (2026-09-15): 6,0% no braço sem as três mudanças do item 14, 3,9% no
      braço adotado — o variante recusa MENOS, não mais; a guarda de
      sobre-recusa não disparou.**
    - **exposição da chave, MEDIDA na telemetria existente:** em 12 dos 35
      filmes e 2 dos 18 os três candidatos tinham ao menos uma flag. Nesses,
      "menos flags" decide antes de "quem escreveu mais", e um candidato que
      DECLARE os temas difíceis vence os que os escreveram — mesmo quando o
      retry consertaria a frase. É o risco "recusar demais" com número;
    - **`par_recusado` só marca recusa DECLARADA.** Forçado saltado em
      silêncio ou descartado quebra o par sem marca nenhuma: 6 dos 38 pares
      do insumo (`burning` ×2, `drive-my-car`, `force-majeure`, `guillermo`,
      `satantango`);
    - **R13 no prompt** foi descrita como "o tema fala só de fama ou de hype,
      e a paráfrase não diz nada do que a obra entrega", para não contradizer
      a regra 9g ("expectativa é assunto legítimo"). A R13 do RELATÓRIO é
      mais larga (o eixo inteiro não publica) — os dois códigos iguais não
      cobrem exatamente o mesmo caso.
14. **Os três padrões dos 21 duvidosos (14,9% do lote) — o que decide se a
    expansão é sustentável** (15% de 2.300 ≈ 345 itens de leitura).
    Atribuição dos itens por grupo é VISTO; os números são MEDIDOS.
    - **R2, omissão de ressalva (8):** 25 das 141 paráfrases têm conector
      de ressalva, e a condição o descarta em 22. A regra 5 do prompt já
      manda carregar a ressalva. Uma marca por tema no briefing (mesmo
      estatuto da de spoiler) pegaria 6 dos 8 e marcaria 18% dos temas; é o
      grupo com mais chance.
    - **R1, invenção de qualificador (6):** resultado negativo — nenhum
      sinal no insumo, porque 130 dos 135 itens restantes também usam
      palavra nova (a regra 11 exige). Proposta: exemplos contrastivos reais
      no prompt; um validador de lista fechada seria circular.
    - **R6, spoiler de arco (4):** desfecho (2) já era marcado e não
      adiantou — o que resolve é o item 13. Arco/evolução (2): a marca atual
      pega 0 de 2; uma regra 9h no prompt ("nomeie o traço, não a
      trajetória"); um léxico de arco seria in-sample.
    - **Teto teórico:** cerca de 7,8% de duvidosos, sem previsão. Medir
      exige regerar (18 filmes ≈ US$ 0,45 só dá direção; 53 filmes ≈ US$ 1,3
      para separar do acaso). Briefing NÃO alterado.

    **2026-09-15 — MEDIDO no experimento pareado (item 18): 3,7% nos temas
    com ressalva, contra os 13,3% do braço sem as três mudanças** — melhor
    que o teto teórico de 7,8% estimado aqui, porque aquele teto não
    contava com o canal de recusa (item 13) reduzindo o braço controle
    antes mesmo do briefing novo. Briefing ADOTADO como default.
15. **Os validadores LÉXICOS reprovavam 7 das 18 correções do dono (39%) —
    (a)+(c) implementadas em 2026-09-14; o dry-run passa 18/18, publicação
    espera o aval do dono (estado no fim do item).** O dry-run de
    `publicar_condicoes` passa 11 filmes e recusa 7:
    - `ancora_nao_verificavel`, 4: sinônimos, o que a R12 pede;
    - `sem_discriminacao`, 4;
    - `exemplo_verbatim`, 2: C026 só pelos nomes dos atores, porque a
      exceção de nome próprio de `tema_verbatim` falta aqui; C138 é cópia
      real.

    **C020** (descarte que o dono julgou indevido) caiu em
    `sem_discriminacao`: 6 "irmãos", vários por palavra de discurso, deixam
    como "exclusivos" só "agradou", "embora" e "reconheçam". A regra
    descartou 3 itens em todo o catálogo (`shutter-island` NEG-B e
    `the-northman` NEG-A nos 35, mais C020), mas dispara a montante em 51 +
    21 candidatos do best-of. **Padrão, não caso único.**

    Outro bloqueio: `RETIRADAS` (R13) é literal e não inclui C030 e C134,
    os dois de `expectativa` do piloto.

    Opções, sem nada implementado: texto de autoria humana passa só pelos
    validadores exatos e os léxicos viram aviso; exceção de nome próprio no
    `exemplo_verbatim`; tirar as palavras de discurso de `mesmo_assunto`
    (exige rótulo antes).

    **2026-09-14 — (a) e (c) IMPLEMENTADAS, como aprovado; (b) e (d) não.**
    - **(a)** Condição com `origem: "leitura_humana"` passa só pelas flags
      EXATAS; as LÉXICAS (`condicoes.FLAGS_LEXICAS`: `ancora_nao_verificavel`,
      `tema_verbatim`, `exemplo_verbatim`, `sem_discriminacao`) viram aviso,
      gravado na condição publicada (`avisos`). `vazio`, `nota_ou_score`,
      `idioma` e `cliche` não estavam em nenhuma das duas listas e CONTINUAM
      travando. Texto do modelo sob a trava inteira: `extrair` não propaga
      `origem`. As 18 frases do dono ganharam a marca
      (`scripts/aplicar_revisao_condicoes.py`, que reconstrói o lote
      corrigido a partir do insumo e da revisão, conferindo a impressão
      digital). MEDIDO: zero flag exata nas 18.
    - **(c)** `exemplo_verbatim`: uma sequência copiada feita SÓ de nomes
      próprios não conta. A forma literal ("tirar os nomes e recontar") foi
      medida e recusada: derruba o par de teste da cópia real da rodada 1
      ("…a vida pessoal de Napoleão", 3 < 4 sem o nome). Nos 405 textos em
      disco, regra antiga e nova dão os mesmos 5 disparos.
    - **Os 7, depois:** passam todos. Avisos registrados — C010, C020, C103:
      `ancora_nao_verificavel` + `sem_discriminacao`; C058:
      `ancora_nao_verificavel`; C127: `sem_discriminacao`; **C138:
      `exemplo_verbatim` — cópia REAL de quatro palavras ("valoriza os
      aspectos técnicos e temáticos"), sem nome; passa porque é texto do
      dono e a checagem é léxica, não porque deixou de ser cópia**; C026:
      nenhum aviso (a exceção (c) resolve na régua, para qualquer autor).
    - **Dry-run do lote corrigido: 18 de 18 filmes passam** — 134
      condições, 2 retiradas (C030, C134), 3 sem condição publicável.
      **Nada publicado**: publicar espera o aval do dono.

16. **R13 por REGRA, não por enumeração — FECHADO (2026-09-15), estado no
    fim do item.**
    `RETIRADAS` (`publicar_condicoes.py`) é literal; nesta sessão só ganhou
    C030 e C134. A R13 retém um EIXO e a lista enumera ITENS: com 300
    filmes ela diverge em silêncio, e o modo de falha é publicar o que a
    R13 proíbe. Proposta: reter pelo eixo de origem do tema, lido do bloco
    `eixos` publicado — a mesma função que já dá a categoria `expectativa`
    do relatório (`relatorio_revisao_condicoes._eixos_do_tema`). MEDIDO
    sobre os 35 publicados + os 18 do piloto:
    - as 8 da lista são todas `expectativa` pela regra (ela as reproduz);
    - **a regra reteria 2 itens que estão NO AR hoje**, que a
      classificação [D3] põe em `expectativa` e a leitura da FASE 1
      publicou: `talk-to-me-2022` NEG-C (*Subaproveitamento do potencial da
      premissa*) e `spider-man-across-the-spider-verse` POS-E (*Cliffhanger
      e expectativa pela continuação*). Aplicar a regra os tira na próxima
      publicação desses filmes;
    - um terceiro tema selecionado é `expectativa` e não está no ar
      (`mother-2017` POS-C, *Incompreensão inicial e revelação posterior*);
    - **2 de 426 temas selecionados não têm eixo nenhum** no bloco
      (`im-still-here-2024` POS-E, `mother-2017` POS-A): para eles a regra
      falha ABERTA;
    - a classificação muda com republicação, e o conjunto retido muda
      junto — o argumento da lista literal continua verdadeiro; o que muda
      é que o modo de falha dela (publicar o proibido) é pior que o da
      regra (reter o que a [D3] classificou mal).
    Decisões do dono: (1) aplicar por regra; (2) o destino dos 2 no ar;
    (3) tema sem eixo bloqueia ou passa.

    **2026-09-15 — DECIDIDO E IMPLEMENTADO.**
    - **As decisões.**
      - (a) Os 2 no ar SAEM: foram publicados por lista incompleta, não por
        decisão.
      - (b) Tema sem eixo BLOQUEIA o filme (`CondicaoInvalida`), não passa.
      - (c) A lista literal some depois de validada.
    - **Implementação.** `publicar_condicoes.retidas_pela_r13` retém a
      condição cujo tema está em `EIXO_RETIDO_R13 = "expectativa"`, lido do
      bloco `eixos` do filme. A leitura é por `condicoes.eixos_do_tema`, a
      função que era `relatorio_revisao_condicoes._eixos_do_tema` e que o
      relatório agora reusa. `RETIRADAS` não existe mais.
    - **Validação antes de remover a lista**, zero LLM:
      - a regra retém as 8 (`get-out-2017` pelo lote corrigido);
      - além delas retém exatamente os 3 medidos acima;
      - o dry-run do lote corrigido do piloto é idêntico sob a lista e sob
        a regra: 18 filmes, 134 condições, 2 retiradas.
    - **(a) aplicado**, com `publicar_condicoes --slug` sobre o bloco
      publicado e medido antes:
      - `talk-to-me-2022`: `talvez_evite` passa de 4 para 3 condições;
      - `spider-man-across-the-spider-verse`: `vale_a_pena` passa de 4
        para 3 condições;
      - nenhuma coluna vazia nem abaixo do menor lado do catálogo (2);
      - o diff de cada arquivo é só o item, 7 linhas removidas.
    - **Achado do (a).** `spider-man` POS-E era o tema FORÇADO pelo par
      obrigatório de NEG-A. Saiu sem marcar `par_recusado` no base, como nos
      precedentes: `whiplash-2014` NEG-F e EEAAO NEG-F eram forçados por
      POS-A e também foram retirados sem marca.
    - **(b) atinge 2 filmes com o item NO AR:** `im-still-here-2024` POS-E
      (*Valor histórico e educativo*) e `mother-2017` POS-A (*Símbolos e
      metáforas religiosas*). NÃO foram republicados nesta sessão. A
      próxima publicação de condições desses dois filmes será recusada até
      alguém decidir o tema (reclassificar, retirar à mão ou aceitar).
      **O que se sabe da causa: é INFERÊNCIA, porque a resposta crua da
      rotulagem não é persistida.** A telemetria da rotulagem guarda os
      rótulos descartados por estarem fora da taxonomia, mas não diz de
      qual tema eles eram.
      - `im-still-here-2024`: positivas tem exatamente 1 tema sem eixo
        (POS-E) e exatamente 1 rótulo descartado, `crítica_social` com
        acento — o eixo válido é `critica_social`. O mais provável é que o
        tema tenha perdido o eixo por um erro de grafia do modelo.
      - `mother-2017`: são 2 temas sem eixo, MED-A (*Simbologia e
        alegoria*) e POS-A. O único rótulo descartado (`crítica_social`) é
        das medianas. POS-A não tem rótulo descartado nenhum: o modelo
        simplesmente não lhe deu eixo. MED-A não é tema de condição.
      **Decisão do dono (2026-09-15): deixar como está.** As duas condições
      seguem no ar; nada é rerrotulado agora. O bloqueio só dispara se as
      condições desses filmes forem republicadas, e aí a decisão volta.
      Recomendação registrada, não aprovada: refazer a rotulagem só se um
      dos dois precisar ser republicado, e medir no catálogo inteiro,
      antes dos 300, quantos temas perderam o eixo por rótulo fora da
      taxonomia (como `crítica_social`, com acento).
    - **`publicar_condicoes` preserva o fim de arquivo do original.** A
      republicação trocava o `\n` final do JSON do CLI, um diff sem
      conteúdo; a regra agora é a mesma de `republicar_eixos`.
    - **Testes, nenhuma asserção afrouxada.**
      - O teste da lista literal virou a validação no dado: a regra ⊇ as 8,
        e as extras são exatamente as 3.
      - Novos: o lote do piloto sai igual; os 2 do (a) não publicam e
        nenhuma coluna esvazia; tema sem eixo bloqueia (os 2 casos reais e
        um sintético); `RETIRADAS` não pode voltar; fim de arquivo
        preservado.
    - **Continua aberto.** Os dois códigos "R13" (o do prompt e o do
      relatório) não cobrem o mesmo caso (item 13, último ponto).

    Suíte ao fim de 2026-09-15: **2038 coletados, 2034 passam, 3 falham, 1
    xfail.** Os 2 testes de `get-out-2017` voltaram a passar. As 3 falhas
    restantes são as de `woman-of-fire` (duas, item 6) e a do hero (item
    10).

17. **Rotulagem dos 38 pares obrigatórios — MATERIAL PRONTO, espera o
    dono.** `docs/arquivo-de-estudos/revisao-condicoes/ROTULAGEM_PARES_piloto-18.md`
    (mais o `.json` com `resposta: null` por par), impressão digital
    `09ba67a40e3d`, gerado por `scripts/pares_para_rotulagem.py` a partir de
    `condicoes.pares_obrigatorios` — a MESMA computação da seleção. 38 pares
    em 17 filmes (`memories-of-murder` não forma par). Por par: tema de
    base, tema forçado, as duas paráfrases, os prefixos em comum e as
    palavras de onde cada um veio, e a pergunta SIM/NÃO. Sem classificação
    prévia. A régua `mesmo_assunto` NÃO foi alterada e nenhuma lista de
    palavras de discurso foi implementada: a opção (d) do item 15 e
    qualquer outra mudança vêm depois do rótulo, medidas contra ele.

    **2026-09-14 — ROTULADO pelo dono** (respostas e critério gravados no
    `.json`). MEDIDO:
    - **A régua acerta 22 de 38 pares (58%)**; 16 são falsos: P04, P05,
      P07, P14, P15, P17, P19, P20, P23, P29, P30, P32, P33, P34, P36, P37.
      C024 (P07) e C134 (P36), os dois exemplos citados, são NÃO.
    - **Variantes mais estritas**, só avaliáveis sobre os pares já formados
      (afrouxar não é medível aqui):
      - (d) tirar as palavras de discurso nomeadas antes do rótulo
        (`deixa, quest, consi, receb, abord, algum, propo, descr, exper`):
        pega 6/16 falsos e desfaz 3/22 bons. **Resultado negativo.**
      - exigir 3 prefixos: pega 14/16 e desfaz 10/22 bons. Negativo.
      - **exigir ao menos 1 prefixo em comum nos NOMES dos temas**: pega
        15/16 falsos (fica P30) e desfaz 3/22 bons (P12, P13, P16) — dos
        20 pares que sobram, 19 são SIM (Fisher p≈1e-6). **In-sample:**
        definida depois de o rótulo existir, sobre 38 pares; nos 35 do
        catálogo ela desfaria 36 de 70 pares, sem rótulo que diga quantos
        eram bons. Não implementada. Validar exige rotular os pares dos 35
        (ou dos 53) antes.
      - A mesma régua define os irmãos de `sem_discriminacao`; o efeito de
        qualquer variante ali não foi medido.
    - **Os duvidosos NÃO estão nos pares falsos.** Item forçado duvidoso
      na revisão: 7/18 nos pares SIM, 2/16 nos NÃO (p≈0,13, só direção). O
      custo do par falso não é frase ruim — é um tema fora do top-N na
      coluna, sem objeção nenhuma a mostrar. A premissa "par por
      coincidência gera item fraco em volume" não se sustenta com este
      dado.

    **Validação fora da amostra — MATERIAL PRONTO, espera o dono.**
    `ROTULAGEM_PARES_catalogo-35.md` (+ `.json` vazio), impressão digital
    `146f1e43c94a`: 70 pares de 30 filmes do catálogo publicado (5 não
    formam par: `aftersun`, `anatomy-of-a-fall`, `interstellar`,
    `shutter-island`, `the-invite-2026`). Mesmo formato do piloto, sem
    nenhuma indicação de quais pares a variante desfaria. Com o rótulo, a
    variante "1 prefixo nos nomes" é medida numa amostra que não a inspirou.

    **2026-09-14 — ROTULADO pelo dono; a variante FALHA fora da amostra.**
    MEDIDO sobre os 70 (respostas no `.json`):
    - a régua atual acerta **50 de 70 (71%)** — no piloto, 22/38 (58%);
      somados, 72/108 (67%);
    - **"1 prefixo nos nomes"**: pega 19/20 falsos (fica P10), mas desfaz
      **17 de 50 pares bons (34%)** — no piloto eram 3/22 (14%). Do que ela
      corta, só 19 de 36 (53%) são falsos: quase cara ou coroa. O número
      in-sample estava inflado exatamente onde importa. Desfaz inclusive
      um par bom do `napoleon` (P42, *Retrato de Napoleão* ↔ *Abordagem
      pessoal e íntima do personagem*); o das batalhas (P41) sobrevive;
    - "exigir 3 prefixos": 19/20 falsos, 15/50 bons perdidos (30%) —
      mesmo perfil, também inaceitável;
    - (d) palavras de discurso: 2/20 falsos, 0 bons perdidos — precisa,
      mas quase não pega nada. Negativo de novo;
    - **Nenhuma das três é implementável.** O custo de perder um par bom
      é reabrir o defeito que o par obrigatório fecha (recomendar um traço
      sem mostrar a objeção); o de manter um falso é um tema fora do top-N
      na coluna. Com estes números, a régua atual (29–42% de falsos) é o
      menor dos custos medidos. Os dois gabaritos (108 pares) ficam como
      conjunto de teste para qualquer régua futura — e ela terá de ser
      desenhada sem olhar para eles, ou validada num terceiro lote.

18. **Experimento de briefing — ADOTADO como default de produção
    (2026-09-15).** Resolve os itens 13 e 14: as três mudanças propostas no
    item 14 (marca de ressalva R2, exemplos contrastivos R1, regra global de
    arco R6/9h) foram implementadas como briefing SELECIONÁVEL
    (`condicoes.VARIANTE_EXPERIMENTO`), testadas num experimento pareado
    PRÉ-REGISTRADO antes de qualquer geração
    (`docs/arquivo-de-estudos/experimento-briefing/ETAPA_0_DESENHO.md`) e,
    com o resultado dentro da regra de decisão escrita ANTES da rotulagem,
    viraram o default de `condicoes.gerar` no mesmo dia.

    **Desenho, MEDIDO.** 55 filmes, os dois braços (`controle` = prompt e
    briefing de antes; `variante` = os três acima), best-of-3 + retry iguais
    à produção, 208 gerações. Réplica dupla nos 94 temas com ressalva
    (estrato M) para dar poder ao desfecho principal; réplica única numa
    amostra de 80 temas sem ressalva (estrato U), como guarda de regressão.
    Rotulagem CEGA pelo dono: 506 itens, braço e réplica escondidos por
    numeração embaralhada e hash do mapeamento impresso no relatório
    (`aac57fbf…`), motivo das recusas oculto até o fim.

    **Resultado, MEDIDO — todos os quatro testes pré-registrados:**
    | desfecho | controle | variante | p |
    |---|---|---|---|
    | primário — duvidosos em M (94 temas × 2 réplicas) | 13,3% | 3,7% | **0,0010** |
    | G1 — sobre-recusa, 436 temas | 13 só controle | 4 só variante | 0,049 (direção BOA) |
    | G2 — rendimento confirmado em M | 149 | 168 | 0,0007 (direção BOA) |
    | G3 — regressão em U (80 temas) | 3 só controle | 1 só variante | 0,625 (sem diferença) |

    Significativo a favor e nenhuma guarda piorou → a regra de decisão
    (seção 10.4 do desenho) manda ADOTAR. Sensibilidade nos 69 temas de M
    fora dos filmes já vistos no piloto (dado genuinamente novo): p = 0,016.

    **O que NÃO foi provado, e é para não ser lido como validado
    individualmente.** R1 e a regra de arco (9h) não tinham poder nesta
    escala — o dono marcou DUVIDOSO por R1 só 2 vezes e por R6-arco só 3, no
    braço controle INTEIRO (94×2 + 80 temas). As duas entram porque o
    PACOTE das três passou, não porque cada uma se sustenta isolada.
    Registrado também em `condicoes.gerar`, ao lado do parâmetro.

    **Implementação.** `condicoes.gerar(..., variante=VARIANTE_EXPERIMENTO)`
    é o novo default. `variante=None` continua existindo, byte a byte o
    prompt e o briefing de antes — para reproduzir o braço `controle` ou
    reverter, não para uso corrente. `scripts/gerar_condicoes.py` ganhou
    `--variante legado` para o mesmo fim; sem a flag, usa o default novo.
    Suíte: **2062 coletados** (+24 desde a C14.16: 23 testes do briefing
    variante e mais 1 líquido da correção de default), 2058 passam, as
    mesmas 3 falhas de antes (itens 6 e 10), nenhuma asserção afrouxada.

    **Custo real, MEDIDO pelos contadores crus (raciocínio incluído) —
    corrige o item 3.** A subestimação do `uso` gravado **varia por
    estágio**, e usar a de um estágio no outro erra:
    - **narrativa: 3,8×** (medido no piloto, item 3 — 10.173 tokens de
      raciocínio contra 1.384 visíveis);
    - **condições: 2,25×** (medido aqui — 958.679 de raciocínio contra
      257.116 visíveis, nas 208 gerações do experimento).

    Condições reais no braço adotado (`variante`): **US$ 0,0324/geração**
    (US$ 3,37 em 104 gerações), 30% acima da projeção de 0,025 usada até
    aqui.

    **Projeção dos 300, recalculada** (classificação/verificador/
    síntese/rotulagem em DeepSeek, preço fixo; narrativa e condições em
    Gemini, dobram em 1/1/2027):

    | | por filme, hoje | por filme, depois de 1/1/2027 |
    |---|---:|---:|
    | classificação+verificador+síntese+rotulagem (DeepSeek) | 0,0252 | 0,0252 |
    | narrativa (Gemini) | 0,0518 | 0,1036 |
    | condições (Gemini, braço adotado) | 0,0324 | 0,0648 |
    | **total** (sem veredito) | **≈ US$ 0,110** | **≈ US$ 0,194** |

    Para 300 filmes: **≈ US$ 33 hoje, ≈ US$ 58 depois de 1/1/2027** — contra
    a projeção antiga de ~US$ 31 do item 4, que usava 0,025 nas condições.

    **Carga de revisão humana dos 300, sob a taxa nova — atualiza o item
    11.** Taxa de duvidoso pareada, ponderada pela fração de temas com
    ressalva medida no catálogo (96/444 = 21,6%, item 14):
    - **braço adotado (variante): ≈ 1,8%** (3,7% em M, 1,3% em U);
    - controle (só com o canal de recusa do item 13, sem as três mudanças):
      ≈ 5,8% — já bem abaixo dos 14,9% originais, que são de ANTES do canal
      de recusa e não comparáveis diretamente.

    Com 8,07 temas pedidos/filme (item 14, 444/55) e 300 filmes: **≈ 2.421
    itens gerados**, dos quais **≈ 44 para leitura humana** sob o briefing
    adotado — contra a estimativa antiga de ~345 (14,9% de ~2.300, item 11).
    **Não é medição direta em 300 filmes**, é a mesma taxa medida em 55
    aplicada à escala; o catálogo de 300 é mais obscuro que o de hoje (item
    4), e nada garante que a taxa de duvidoso se comporte igual em filme
    pouco comentado.

    **Achado a acompanhar, não decidido.** O braço variante teve MAIS
    descartes pelo validador automático que o controle (8 contra 4 em 436
    temas, réplica 1 — 1,8% contra 0,9%). Nenhuma das três guardas acusou
    isso (a guarda cobre recusa DECLARADA e regressão de duvidoso, não
    descarte pelo validador léxico), e o volume é pequeno demais para
    testar à parte. Registrado para olhar se vira padrão na primeira
    geração em volume real.

    Material completo, untracked:
    `docs/arquivo-de-estudos/experimento-briefing/` (desenho, pré-registro,
    as duas gerações por filme com contadores crus, os dois relatórios de
    rotulagem cega, o mapeamento selado e o resultado da análise).

### C15. DeepSeek vs. Gemini na classificação/rotulagem — fundamento corrigido, três medições novas

**O motivo histórico da troca (v1.8.0) não vale mais.** `PROVIDER_POR_ESTAGIO`
justificava DeepSeek em `classificacao`/`rotulagem` citando, em primeiro
lugar, o teto de 20 req/dia do Gemini free tier. **A chave do Gemini tem
billing ativo hoje — o teto não existe.** Corrigido em `config.py:320-405` e
`synthesize.py` (`deepseek_client_call`), com nota datada, 2026-09-14: o
argumento deixou de ser BLOQUEIO e virou CUSTO, e a permanência do DeepSeek
passa a se apoiar nos outros dois motivos (tarefa estruturada, volume alto) —
que nunca tinham sido medidos contra o Gemini. `HISTORICO_PROSA.md` já
registrava a resolução; `CHANGELOG.md` e `experimentos-ollama-arquivado/`
ficaram como estavam — são registro datado do que era verdade então, não
justificativa viva.

**(a) CUSTO, MEDIDO — não é competitivo, e por um motivo estrutural.**
Classificação + verificador, 20 filmes do piloto, mesmas chamadas reais
(7.068 + 1.597):

| | DeepSeek (preço do repo, desatualizado) | DeepSeek (preço de hoje) | Gemini (medido) |
|---|---:|---:|---:|
| total | US$ 0,426 | US$ 0,557 | **US$ 9,23** |
| por filme | US$ 0,0213 | US$ 0,0278 | **US$ 0,462** |

Gemini sai **~17× mais caro**, mesmo no cenário que MAIS o favorece (ver
abaixo). A causa não é o preço por token — é que o **DeepSeek cacheia
automaticamente o prefixo do prompt** (89,5% de cache hit medido nos 35.559
chamadas de classificação do catálogo inteiro) e o Gemini, sem cache
explícito configurado (feature separada, com custo e complexidade próprios,
não implementada), paga o prompt inteiro (~1.000-1.500 tokens) a preço cheio
em TODA chamada.

**Achado que muda a pergunta: a telemetria do projeto não só SUBESTIMA o
Gemini — ela pode ESCONDER FALHA.** `synthesize.uso()` não lê
`thoughts_token_count` (confirmado lendo o código: só `candidates_token_count`
vira `completion_tokens`). Medido com chamada crua (fora do adaptador), em
40 reviews reais do piloto, `gemini-3.7-flash` com `thinking_budget=0` E
`max_output_tokens=300` (o mesmo teto que a classificação usa no DeepSeek):
- **`thinking_budget=0` NÃO desliga o thinking neste modelo/tarefa** — 26 de
  40 chamadas geraram tokens de raciocínio mesmo assim (média 140, até 291);
- **20% das chamadas saíram truncadas** (`finish_reason=MAX_TOKENS`, JSON
  inválido) — o orçamento de saída morreu para o pensamento antes de chegar
  na resposta. Sem `thinking_budget` explícito (default do modelo), a taxa
  sobe para 80%.
- Subindo `max_output_tokens` para 2000, 15/15 chamadas de teste saíram
  limpas (0% de falha) — mas cada uma ainda carrega ~50 tokens de thinking
  em média, cobrados como saída. **É esse cenário (2000 tokens, 0% falha)
  que gerou os US$ 0,462/filme da tabela acima — o número JÁ é o mais
  favorável ao Gemini que o dado sustenta.** Ao orçamento real de 300
  tokens, ele teria uma taxa de falha de 20%+ que o DeepSeek não tem.
- Preço usado: US$ 0,75/M entrada, US$ 3,75/M saída (oficial até
  31/12/2026, thinking cobrado como saída).

**(b) BLOQUEIO DE CONTEÚDO — indicativo, Gemini NÃO recusou.** Testadas as
MESMAS duas entradas que travaram o DeepSeek em `a-brighter-summer-day`:
1. a review `viewing:1343536508` (a que falhou nos 3 passes de
   classificação, `400 Content Exists Risk`);
2. o bucket `positivas` inteiro reconstruído OFFLINE do bruto persistido
   (`pipeline.amostra_do_bruto`, mesma seleção de produção, confirmado que
   contém a review acima) — o mesmo texto que a síntese envia e que também
   travou com `400`.

**Os dois passaram limpos no Gemini** (`gemini-3.7-flash`, `thinking_budget=0`,
JSON válido nos dois, sem qualquer sinalização de bloqueio em
`prompt_feedback`). **Amostra de 1 filme, 2 chamadas — indicativo, não
taxa.** Mas é o único bloqueante DETERMINÍSTICO que existe hoje (item 7 acima):
se a taxa de recusa do DeepSeek para este tipo de conteúdo for consistente,
trocar SÓ este estágio problemático (ou ter um fallback de provider quando
`Content Exists Risk` disparar) resolveria um bloqueante real da expansão —
questão de disponibilidade, não de custo.

**(c) QUALIDADE — desenho proposto, ARQUIVADO NÃO RODADO (2026-09-14).**
**Motivo do arquivamento:** a decisão de provider já está tomada por custo e
cache (item a: ~17×, e estrutural — o DeepSeek cacheia o prefixo, o Gemini
paga o prompt inteiro em toda chamada), e um resultado de qualidade não a
mudaria: nem um Gemini melhor justificaria 17× no estágio de volume, nem um
pior desfaria o fallback de C16, que existe por DISPONIBILIDADE, não por
qualidade. Os ~US$ 8,11 não foram gastos. O desenho fica abaixo, intacto,
para o caso de a premissa de custo mudar.

Não comparar custo mais alto = melhor sem medir. Proposta, em duas partes:

1. **Contra gabarito humano.** Rodar os MESMOS 100 exemplos rotulados à mão
   de `CLASSIFICACAO_CONSOLIDADO.md` no Gemini, 3 passes (mesma votação de
   3 já usada em produção), e comparar precisão/recall por eixo contra os
   números já medidos do DeepSeek — sem precisar reclassificar o DeepSeek,
   que já está medido. Custo: 300 chamadas × ~US$ 0,0011 ≈ **US$ 0,33**.
2. **Concordância e reprodutibilidade sobre volume real.** Rodar Gemini 3×
   sobre as 2.356 reviews do piloto (mesmo conjunto que o DeepSeek já
   classificou 3×) e medir (i) concordância DeepSeek×Gemini por eixo
   (interseção/união do voto majoritário de cada um) e (ii) reprodutibilidade
   interna de cada provider (fração de unanimidade nos 3 passes — mesmo
   método de `scripts/medir_reprodutibilidade_d3.py`, aplicado aqui à
   classificação em vez da rotulagem). Custo: 2.356×3 chamadas Gemini ×
   ~US$ 0,0011 ≈ **US$ 7,78** (repetindo a mesma ordem de grandeza do item a,
   porque é o mesmo volume).
   Total do desenho: **~US$ 8,11**, zero chamada DeepSeek nova (reusa o que
   já está classificado). Nenhuma reclassificação; só grava num
   diretório de estudo, fora de `resultado/`.

**Nada foi trocado em produção.** `PROVIDER_POR_ESTAGIO` continua com
`classificacao`/`rotulagem` em DeepSeek. Nenhuma asserção de teste foi
afrouxada; `tests/test_provider_por_estagio.py` (34 testes) continua
passando.

### C16. Fallback de conteúdo DeepSeek → Gemini — implementado, medido, provado em `a-brighter-summer-day` (2026-09-14)

**Decisão do dono:** fallback para o Gemini quando o DeepSeek recusa por
conteúdo. O custo de execução é ~zero (o Gemini só roda na recusa), e o
argumento não depende da taxa: sem fallback, cada recusa é um filme que não
publica. `PROVIDER_POR_ESTAGIO` NÃO mudou.

**Detecção — o critério inteiro** (`synthesize.recusa_de_conteudo`):
`openai.BadRequestError` com `exc.body["message"] == "Content Exists Risk"`,
comparação EXATA. É o que a API devolveu nas três vezes registradas (passes,
log de publicação): HTTP 400, `type`/`code` = `invalid_request_error` — os
mesmos de qualquer 400 (parâmetro inválido, contexto longo); só a mensagem
distingue, e o SDK já desembrulha `error` em `body`. Falso positivo não tem
como acontecer; se o DeepSeek mudar o texto, o fallback para de disparar e o
filme falha ALTO como antes — o modo de falha é o erro visível, nunca o
mascarado. **Não dispara** (um teste para cada): JSON inválido, timeout, 5xx,
429 (nem com a mesma mensagem), outro 400, 400 sem corpo, mensagem parecida,
erro do Gemini.

**Onde.**
- Classificação, POR REVIEW: `votacao_3.classificar_passe` →
  `synthesize.resposta_classificacao`. Gemini `gemini-3.7-flash` com
  `thinking_budget=0` e teto de 2000 tokens (C15.a: a 300, 20% truncava).
- Síntese, POR BUCKET: `synthesize_bucket`, só no caminho de produção
  resolvido para DeepSeek (client injetado não ganha fallback), pelo
  `gemini_client_call` — o adaptador §D do Gemini, de produção até a
  v1.8.0. As retentativas do bucket (JSON, idioma/escopo) ficam no Gemini:
  mandar o mesmo texto de volta ao DeepSeek seria pagar uma recusa certa.
- **O Gemini ser o provider da prosa não resolvia nada:** narrador, veredito
  e condições leem só o `output` validado, nunca review bruta — o texto
  recusado nunca chega a eles. A recusa acontece nos estágios que leem
  review (classificação, síntese, verificador), e os dois primeiros são
  necessários JUNTOS: sem a síntese, o filme não sai; sem a classificação, a
  guarda do item 8 recusa a amostra.

**Marca no dado** — a chave só existe quando houve troca (mesma política do
`verificador`), e por isso as 7.843 linhas antigas de consenso ficaram byte a
byte iguais:
- registro de passe: `provider` e `modelo` (em todo registro novo) +
  `fallback_conteudo: {de, para, modelo, motivo}`;
- linha de consenso e de consenso verificado: `fallback_conteudo:
  [{passe, de, para, modelo, motivo}]`;
- bloco `eixos` do resultado: `fallback_conteudo: [{bucket, id, passes}]` —
  só as reviews contadas no `n`;
- bucket do resultado: `fallback_conteudo: {de, para, modelo, motivo}`;
- sobrevive a `write_json` e a `frontend/build_data.py` (teste).
**Telemetria:** linha `Fallbacks de conteúdo do LLM:` no stderr do CLI (com
aviso legível ao lado), parseada pelo harness para o campo
`fallback_conteudo` de `publicacao_log.jsonl`; resumo por passe em
`votacao_3`; `publicar_catalogo --relatorio` lista onde, lendo do DADO.

**Republicação de `a-brighter-summer-day` — a prova de ponta a ponta.**
1. Classificação: a única review pendente da amostra inteira ×3 passes → 3
   recusas do DeepSeek → 3 respostas do Gemini, `ok`, os mesmos 7 eixos nos
   3 passes (unânime). ~1.529 tokens de entrada e ~57 de saída por chamada.
2. Consenso: 7.843 → 7.844 linhas, 0 incompletas; o diff é a linha nova e
   nenhuma outra.
3. Verificador: `aplicar-producao --slug a-brighter-summer-day` — **flag
   nova**, porque sem ela o resume retentaria as falhas de JSON de OUTROS
   filmes e mudaria `consenso_verificado.jsonl` por baixo de JSONs já
   publicados (o piloto registrou que `speak-no-evil-2022` mudaria). 3
   chamadas: as 2 falhas antigas de JSON do próprio filme passaram; **a
   review nova foi RECUSADA DE NOVO pelo DeepSeek** e ficou com
   `impacto_emocional` sem verificação (política conservadora); `n_falharam`
   14 → 13. `consenso_verificado`: 1 linha nova, 0 alteradas em qualquer
   outro filme.
4. Publicação (`publicar_catalogo --slug`, offline, 0 requisições, 57 s):
   **n = 40 nos três buckets** (margem `n=40`, limiar 22,83pp), contraste
   `tematico`, verificador aplicado, rotulagem em 3 chamadas sem falha,
   narrativa com 0 flags. **Um bucket processado pelo Gemini: `positivas`**
   (5 temas). Veredito gerado pelo LLM (não template).
5. NÃO feito: condições (o §0 exige leitura humana de 100% antes de
   `publicar_condicoes.py`) e `frontend/build_data.py`.

**Rotulagem e verificador têm o mesmo risco?**
- **Verificador: sim, observado AO VIVO** (passo 3). Manda o mesmo texto de
  review que a classificação. A falha é conservadora, mas NÃO é visível por
  filme: o bloco `eixos` carrega só o manifesto global. Em
  `a-brighter-summer-day`/positivas, uma das marcações de
  `impacto_emocional` é de review não verificada — e a variante de produção
  remove 47,7% dessas marcações no corpus. **Recomendação: entrar**, com a
  mesma detecção e um ponto de chamada (`rodar_passe`). Não implementado:
  aguarda aval.
- **Rotulagem: risco baixo.** Recebe só os NOMES dos temas (paráfrase em
  português gerada pelo modelo), nunca texto de review; na republicação, os
  temas de `positivas` — gerados pelo Gemini a partir do texto recusado —
  passaram no DeepSeek. A falha é aditiva (célula sem frase,
  `rotulagem.falharam`). Mas `rotular_bucket` tem `except Exception` largo:
  uma recusa ali viraria `falhou` sem motivo. **Recomendação: não entrar no
  fallback; gravar o motivo da falha** — mudança pequena, não feita.

**Taxa real de bloqueio (dimensionamento, não gate) — custo zero: a medição
já estava no disco.** Os três passes de produção já mandaram ao DeepSeek
toda review da amostra, e a falha fica gravada com o erro.
- Classificação: 7.844 reviews × 3 passes (23.532 chamadas) → **1 review
  recusada** (a mesma, 3/3) = **0,013%**; nas 7.724 reviews dos outros 54
  filmes, **0**. Nenhum outro tipo de erro nos três passes.
- Verificador: 5.851 registros antes desta sessão, 0 recusas (as 14 falhas
  eram JSON); +1 recusa agora, a mesma review.
- Síntese: 162 buckets sintetizados no disco, 0 recusas; +1 recusado
  (`positivas` deste filme, que contém a review).
- **Concentração: total.** Tudo o que o DeepSeek recusou até hoje, em três
  estágios, é UMA entrada de UM filme (1 de 55).
- **Perfil:** *A Brighter Summer Day* (Edward Yang, Taiwan, 1991), o único
  filme sino-falante do catálogo. A review recusada é POSITIVA (5★) e cita
  Taiwan/Taipei. **Não é filtro de palavra:** 18 reviews da amostra citam
  Taiwan (17 passaram), 15 citam China e 12 comunismo, e filmes de violência
  extrema, abuso e ditadura (`im-still-here-2024`, `hard-to-be-a-god`,
  `cidade-de-deus`, `the-substance`, `speak-no-evil-2022`) passaram limpos.
  Hipótese NÃO medida: o filtro reage a tema político sensível para a China
  (o DeepSeek é provider chinês). n = 1 não sustenta mais que hipótese.
- **Projeção para 300:** na taxa de hoje, 1/55 filmes → ~5 filmes; com 1
  evento, o IC 95% (Poisson exato) vai de ~0,1 a ~30. **O perfil empurra
  para cima:** a expansão é de cinema internacional e temas difíceis, e se a
  hipótese valer, filmes sobre China/Taiwan/Hong Kong/Tibete/Revolução
  Cultural batem mais — o catálogo atual tem só um. Custo do fallback por
  filme afetado: ~US$ 0,0014 por review por passe + ~US$ 0,01 por bucket de
  síntese → < US$ 0,05/filme; no teto do IC, < US$ 2 no lote.

**Aberto:**
- `SPEC_VERSION` NÃO foi incrementada: a chave nova é aditiva, e incrementar
  faria `_ja_publicado` recusar o catálogo inteiro (o harness republicaria
  tudo). Decisão do dono no commit.
- O `uso` do Gemini no fallback continua sem `thoughts_token_count` (item 4
  do piloto): custo subestimado.
- A síntese não grava provider quando NÃO há troca: "sem marca = DeepSeek"
  vale para execuções com o provider default; `--provider` explícito não
  deixa rastro no JSON (dívida anterior a esta sessão).
- Fallback no verificador (recomendado) e motivo na rotulagem: aguardam aval.
- Condições de `a-brighter-summer-day`: aguardam geração + leitura humana.

**Testes:** `tests/test_fallback_conteudo.py` (39). Única asserção alterada:
`test_sem_empilhamento_scripts.ALVOS_LLM` ganhou `resposta_classificacao` —
APERTA: sem ela, a varredura de `votacao_3.py` ficaria sem alvo e passaria
por vacuidade. Nenhuma afrouxada. Suíte: 1965 coletados / 1959 passam / 5
falhas conhecidas (as mesmas de antes) / 1 xfail.

**Rodada 2 (2026-09-14), aprovada pelo dono — resolve os itens "Aberto" acima.**
1. **Verificador com fallback.** `resposta_json_com_fallback` (estágio
   `verificador`); `resposta_classificacao` virou atalho dela. Teto de saída
   `FALLBACK_CONTEUDO_MAX_TOKENS_JSON` = 2000, herdado da medição da
   classificação (mesma forma de tarefa; não medido no verificador).
   **Reverificação de `viewing:1343536508`:** o Gemini CONFIRMOU
   `impacto_emocional` (alvo `espectador`) — **o estado não muda**. A linha
   passa a carregar `verificador_fallback_conteudo`, e o bloco publicado
   `eixos.fallback_conteudo` traz `verificador` junto dos `passes`.
2. **O estado "sem verificação" deixou de ser invisível.**
   `gerar_consenso_verificado` marca toda linha com `impacto_emocional` e sem
   veredito com `verificacao_pendente: {eixo, motivo, erro}` (motivos:
   `recusa_de_conteudo`, `recusa_de_conteudo_e_fallback_falhou`,
   `erro_<Tipo>`, `sem_chamada`); o bloco `eixos` publica
   `verificacao_pendente` para as reviews CONTADAS; o manifesto ganhou
   `pendentes_por_motivo` e `n_fallback_conteudo`, e o custo dele passou a
   somar só as chamadas do DeepSeek (os preços são os dele).
   **Estado hoje:** 0 reviews sem verificação por recusa. **12 sem
   verificação por `JSONDecodeError`, em 11 filmes, TODAS contadas no `n`
   publicado e nenhuma marcada no JSON publicado** (os JSONs são anteriores
   à marca): `drive-my-car`/negativas, `force-majeure-2014`/medianas,
   `hard-to-be-a-god`/medianas, `memories-of-murder`/negativas,
   `pinocchio-2022`/positivas, `satantango`/negativas,
   `speak-no-evil-2022`/medianas, `the-cloud-capped-star`/positivas,
   `the-turin-horse`/positivas, `whiplash-2014`/medianas, `zama`/negativas e
   positivas. Em `consenso_verificado.jsonl` essas 12 linhas ganharam só a
   chave — os eixos das 7.844 linhas estão intactos. **Decisão do dono,
   não tomada:** (a) regenerar o bloco `eixos` desses 11 filmes para a marca
   chegar à página; ou (b) retentar as 12 no verificador (falha não
   determinística — no piloto, 8 de 8 passaram na retomada), o que PODE
   mudar contagens publicadas (`speak-no-evil-2022` mudaria bullets).
3. **Rotulagem: sem fallback, com motivo.** `motivos_falha` por tentativa
   (`recusa_de_conteudo: Content Exists Risk`, `json_invalido`,
   `<Tipo>: <mensagem>`), em `eixos.rotulagem.motivos_falha` só quando
   houve falha; o CLI imprime.
4. **`SPEC_VERSION` não sobe** — decisão registrada ao lado da constante
   (`config.py`) e em `SPEC.md` §3[V], junto da política de carimbo.
5. **Condições de `a-brighter-summer-day`: geradas, NÃO publicadas** —
   `docs/arquivo-de-estudos/revisao-condicoes/insumo-proximo-lote/`, para o
   próximo lote de revisão humana. 9 temas pedidos (5 vale a pena, 4 talvez
   evite) → 8 condições (4 + 4), 0 descartadas, **1 recusa declarada pelo
   modelo**: POS-D, regra R6 (spoiler — o tema é o impacto do desfecho).
   Taxa de recusa 1/9 = 11%, a primeira sob o canal de recusa — um filme só.
6. **Bloco `eixos` republicado** por `cli --reuse-synthesis --offline --tom
   estruturado`: só `eixos.fallback_conteudo` e `veredito` (regerado)
   mudaram; contagens, margem (n = 40), contraste, buckets e narrativa
   idênticos. `build_data.py`: catálogo da home 54 → 55, `data.js` só com
   inserções.

Testes da rodada: +12 em `test_fallback_conteudo.py`; `ALVOS_LLM` ganhou
`resposta_json_com_fallback` (aperta, pelo mesmo motivo). Nenhuma asserção
afrouxada. Suíte: 1977 coletados / 1971 passam / 5 falhas conhecidas / 1
xfail.

**Rodada 3 (2026-09-14) — retentativa filme a filme das 12 reviews sem
verificação. PARADA em 6 de 11 filmes: o DeepSeek não processou nenhuma
chamada.**

**Método** (decisão do dono: retentar não restaura um valor — produz um
veredito novo, que pode remover a marcação):
- por filme, na ordem: `verificador_impacto.py aplicar-producao --slug X`;
- conferência de `consenso_verificado.jsonl` contra um snapshot anterior,
  por hash de filme e por linha: só as linhas dos ids retentados podem
  mudar;
- `scripts/republicar_eixos.py` (novo): regrava SÓ o bloco `eixos`, com
  zero LLM e zero rede. As frases das células são relidas do publicado
  (`eixos.temas_do_bloco`, extraído de `aplicar_lei_margem.py`), e a
  proveniência vem de `pipeline.anexar_proveniencia` (extraído de
  `montar_eixos`). Ele mede contraste, células cruzando a margem, bullets,
  `n` e os briefings de narrativa/veredito/condições, e RECUSA gravar se
  qualquer um mudar. Preserva o fim de arquivo do original.
- Sanidade antes da primeira chamada: `burning-2018` e
  `a-brighter-summer-day` remontam byte a byte iguais ao publicado; nos 11
  filmes, a única diferença era a marca nova.

**Resultado** — `drive-my-car`, `force-majeure-2014`, `hard-to-be-a-god`,
`memories-of-murder`, `pinocchio-2022`, `satantango`:
- as 6 retentativas FALHARAM, e nenhuma produziu veredito;
- nenhum estado publicado mudou: contraste, margem, bullets, contagens e os
  três briefings idênticos;
- cada filme foi republicado só com `verificacao_pendente` (10 linhas de
  diff por arquivo);
- consenso verificado: 6 linhas alteradas (só o motivo da pendência, de
  `erro_JSONDecodeError` para `erro_TypeError`); 49 de 55 filmes com hash
  idêntico ao snapshot, e os outros 6 são exatamente os retentados.

**Causa, medida com a resposta crua:** sobrecarga do DeepSeek. A resposta
chega com HTTP 200 depois de ~900 s, sem `choices`, e com o corpo
`{"error": {"message": "We were unable to start processing your request
within the 900-second timeout limit. Please try again later."}}`.
Reproduzido na review que falhou (902 s) e numa review de CONTROLE que já
tinha veredito (`viewing:1437760141`, 901 s) — a mesma resposta. Não é o
texto das reviews; é a fila do provider.

**Três achados do adaptador, NÃO corrigidos nesta rodada (tratados na
rodada 5, abaixo):**
1. A sobrecarga vem como 200, não como 5xx, então `_com_retentativa` não a
   vê como transporte. O acesso a `choices[0]` vira
   `TypeError: 'NoneType' object is not subscriptable` — é o motivo gravado
   nas 6 marcas: verdadeiro, mas não diz a causa.
2. O timeout de 180 s do SDK não protege: a conexão fica aberta ~900 s,
   porque o servidor a mantém viva enquanto a requisição espera na fila.
3. O mesmo vale para classificação e síntese: com o DeepSeek neste estado,
   o pipeline inteiro espera 15 min por chamada antes de falhar.

**NÃO rodados:** `speak-no-evil-2022`, `the-cloud-capped-star`,
`the-turin-horse`, `whiplash-2014` e `zama` (6 reviews).

**Pendência de instabilidade do V2_alvo (C3): NÃO fechada.**

Testes da rodada: +8 em `tests/test_republicar_eixos.py` (LLM e rede
envenenados). Suíte: 1985 coletados / 1979 passam / 5 falhas conhecidas / 1
xfail.

**Rodada 4 (2026-09-14) — decisão do dono: marcar os 5 restantes SEM
retentar.** Com o DeepSeek nesse estado, retentar custaria ~900 s por review
para receber o mesmo erro; a transparência (marca visível) é o que importa
agora, não o resultado da chamada. `consenso_verificado.jsonl` já carregava
`verificacao_pendente` para essas 6 reviews desde a escrita global da rodada
2 (que sempre cobre o consenso inteiro, independente de `--slug`) — só o
JSON PUBLICADO ainda não refletia isso. Rodado `republicar_eixos.py --slug X`
(medir, depois aplicar) nos 5 filmes, ZERO chamada ao verificador:

- os 5 confirmam `estado_publicado_mudou: false` — só a marca entra;
- **`speak-no-evil-2022`, com atenção redobrada:** contraste `valorativo` →
  `valorativo`, n 40 → 40, zero células cruzando margem, zero bullets, zero
  briefing mudando. Correto: SEM retentativa a marcação de
  `impacto_emocional` não muda, então nada que dependa dela pode mudar;
- `zama` carrega as 2 pendências (`negativas`/`viewing:1414135189` e
  `positivas`/`viewing:1487064786`), os outros 4 filmes uma cada.

**Estado final: as 12 reviews (11 filmes) estão marcadas
`verificacao_pendente` no JSON publicado** — 6 com motivo `erro_TypeError`
(retentadas na rodada 3, contra o DeepSeek sobrecarregado) e 6 com
`erro_JSONDecodeError` (marcadas sem retentar, rodada 4). Nenhuma foi
verificada de fato; nenhum estado publicado mudou em nenhuma.

**Rodada 5 (2026-09-14) — o adaptador passa a reconhecer a sobrecarga. Decisão
do dono: detecção implementada como desenhada; prazo de parede MEDIDO antes de
escolhido; UMA retentativa, não três.**

**Medição da latência por estágio — o que existia.** A latência por chamada
NÃO estava gravada em nenhum registro de produção dos quatro estágios
DeepSeek: os registros de passe, do verificador, a telemetria de rotulagem e
os buckets de síntese guardam `uso`, não tempo. O que existe:
- classificação: mediana 1,6 s por review (estudo de 120 reviews,
  `MEDICAO_CONTAGEM_E_AB.md`), sem cauda registrada;
- síntese — o prompt maior, onde um prazo curto cortaria chamada legítima:
  limite DERIVADO do log de publicação. Por filme, tempo total menos a
  latência da narrativa do mesmo run = 3 sínteses + 3 rotulagens + overhead:
  **p50 28,5 s · p95 82,8 s · máximo 89,5 s** em 50 filmes. Nenhuma síntese
  isolada passou de 89,5 s; a típica fica em ~10 s. Não dá p99 por chamada:
  a unidade medida é o filme;
- verificador e rotulagem: nada gravado;
- os outros `latencia_s` do repositório são do Gemini (narrativa, veredito,
  condições, comparações antigas) — não servem para o DeepSeek.

**Prazo de parede: 90 s por tentativa** (`LLM_PRAZO_PAREDE_S`). Critério:
acima da maior latência legítima plausível e 10× abaixo dos 900 s da fila.
Cobre o pior caso derivado da síntese, que é a soma de SEIS chamadas; para os
estágios de JSON curto (mediana ~1,6 s) é folga larga. **Um parâmetro só para
os quatro estágios** — nenhum precisou de valor próprio com o dado que existe.
É ponto de partida, não ótimo: a latência passa a ser gravada por estágio
(`latencia_s` em cada registro de classificação e do verificador; linha
`Latências do LLM:` no stderr do CLI com n/p50/p95/p99/máx de síntese e
rotulagem, gravada pelo harness em `publicacao_log.jsonl` como
`latencia_llm`). Imposto por fora do SDK, numa thread DAEMON: a de
`concurrent.futures` não é daemon, e o CLI ficaria pendurado na saída até a
chamada abandonada terminar. **Custo declarado:** a chamada que estoura
continua rodando em segundo plano e a resposta, se vier, é descartada — numa
chamada paga, é pagar por trabalho jogado fora. Não é impeditivo; é a razão
de o prazo não ser agressivo.

**Detecção.** HTTP 200 sem `choices` é conferido dentro da tentativa
(`_resposta_deepseek_valida`): com a assinatura da fila (prefixo "We were
unable to start processing your request" — o número de segundos é parâmetro
do provider) vira `LLMSobrecarga` com a mensagem real; com outro erro no
corpo, `LLMRespostaComErro`, não retentada. Nenhum dos dois vira mais
`TypeError`.

**Retentativa: UMA, com espera de 30 s ±25%** (`LLM_RETENTATIVAS_INDISPONIVEL`
= 1, `LLM_BACKOFF_INDISPONIVEL_S` = 30), só para chamada NÃO PROCESSADA
(`LLMSobrecarga` ou `LLMPrazoExcedido`). Critério: fila cheia agora tende a
continuar cheia nos segundos seguintes; 30 s é 15× o primeiro backoff de
transporte, o bastante para uma fila que oscila, pouco perto de uma fila
parada. Pior caso por unidade: 90 + 30 + 90 ≈ 3,5 min (antes: ~45 min).
Esgotando, a exceção sobe com o motivo real e as tentativas. O transporte (5xx,
conexão) continua como estava: `LLM_MAX_TENTATIVAS` = 3, backoff 2 s · 4 s.
Efeito colateral a registrar: o timeout de leitura do SDK (180 s) deixa de
ser alcançado no DeepSeek — o prazo de parede dispara antes — e o prazo
também limita as retentativas internas do SDK da OpenAI (`max_retries=2` por
padrão), que antes podiam empilhar sob as nossas.

**Por estágio, esgotando:**
- **verificador:** `ok: False` com o motivo real → `verificacao_pendente`
  com motivo `erro_LLMSobrecarga` / `erro_LLMPrazoExcedido`, visível no
  bloco `eixos` publicado — o mecanismo da rodada 2;
- **classificação:** `ok: False` com o motivo real; a review não entra no
  consenso e a guarda `AmostraNaoClassificada` recusa publicar o filme —
  falha alta;
- **rotulagem:** a célula fica sem frase, com o motivo em
  `rotulagem.motivos_falha`. **Precisou de ajuste próprio:** o laço de 2
  tentativas de `rotular_bucket` empilharia uma segunda rodada de ~3,5 min
  sobre a do adaptador; agora ele NÃO retenta depois de `LLMIndisponivel`;
- **síntese: tratada igual, e o custo é o filme.** A unidade é o bucket, e a
  exceção sobe: o CLI sai com rc≠0 e o harness grava o motivo real no log.
  Publicar um bucket sem temas, marcado, seria decisão de produto — não
  tomada. A consequência medida: as sínteses já pagas dos outros buckets do
  filme são refeitas quando o filme é republicado. Não justifica
  paciência maior para a síntese — com a fila parada, mais espera só
  atrasa a mesma falha.

**Não tratado:** o fallback para o Gemini dentro dos estágios (recusa de
conteúdo) usa o timeout próprio do Gemini (180 s), que funciona — o problema
de conexão viva foi observado só no DeepSeek. **Proposta, não implementada:**
um disjuntor por processo (após N chamadas não processadas seguidas, as
seguintes falham na hora). Com fila parada, a classificação de 300 filmes
ainda gastaria ~3,5 min por unidade até cada uma falhar; o disjuntor é o que
transformaria isso em uma falha só.

Testes: `tests/test_sobrecarga_llm.py` (14), sobre o SDK REAL da OpenAI com
transporte falso (`httpx.MockTransport`) — o 200 de erro chega a
`deepseek_resposta` exatamente como o SDK o monta. Cobre: a exceção nova com a
mensagem real; outro erro no corpo sem retentativa; uma retentativa, não
três, com a espera longa; sobrecarga seguida de resposta normal; o transporte
com o teto de antes; o prazo de parede disparando em 0,2 s (não 900 s) com a
thread abandonada daemon; resposta normal intacta; latência gravada; e,
esgotando, verificador pendente com o motivo real, classificação `ok: False`,
rotulagem sem empilhar e síntese falhando alto. Nenhuma asserção afrouxada.
Suíte: 1999 coletados / 1993 passam / 5 falhas conhecidas / 1 xfail.

**Rodada 6 (2026-09-14) — as 6 retentativas refeitas, com o adaptador novo e a
fila normal.** Sonda antes: uma chamada pelo adaptador novo respondeu em
2,2 s, sem retentativa. Mesmo método da rodada 3: snapshot novo do consenso
verificado com hash por filme; por filme, na ordem,
`aplicar-producao --slug X` → conferência (só a linha da review retentada
pode mudar) → `republicar_eixos.py`, que mede e só grava sem mudança de
estado.

| filme | review | veredito | efeito publicado |
|---|---|---|---|
| `drive-my-car` | negativas `viewing:1311567647` | confirma | só sai a marca |
| `force-majeure-2014` | medianas `viewing:1029424328` | confirma | só sai a marca |
| `hard-to-be-a-god` | medianas `viewing:1024049819` | **remove** | `impacto_emocional`/medianas 18/40 → 17/40 (lift −17,5 → −20,0 pp) |
| `memories-of-murder` | negativas `viewing:1474734368` | confirma | só sai a marca |
| `pinocchio-2022` | positivas `viewing:1364816145` | confirma | só sai a marca |
| `satantango` | negativas `viewing:1205585573` | confirma | só sai a marca |

- **Nenhum estado publicado mudou** em nenhum dos 6: contraste, `n`,
  células na margem, bullets e os briefings de narrativa/veredito/condições
  idênticos. A remoção em `hard-to-be-a-god` muda um NÚMERO publicado (uma
  célula, −1 menção), longe da margem de 22,83 pp.
- Integridade: 49 de 55 filmes com hash idêntico ao snapshot; as 6 linhas
  alteradas são exatamente as 6 reviews, e em nenhuma outro eixo mudou.
- **Efeito colateral achado e CORRIGIDO na mesma rodada:**
  `verificador.n_removidas_no_corpus` é uma contagem GLOBAL carimbada no
  bloco, e a remoção em `hard-to-be-a-god` a levou de 2781 para 2782. O
  harness regravava o valor atual em todo bloco reconstruído, então
  `memories-of-murder`, `pinocchio-2022` e `satantango` ganharam um
  2781 → 2782 sem conteúdo, e 3 testes de `test_republicar_eixos.py`
  passaram a falhar: o filme de controle deixou de reconstruir idêntico.
  A asserção não foi afrouxada; o harness mudou. **Regra: o carimbo só
  acompanha o corpus quando as contagens do PRÓPRIO filme mudam** — mesmo
  precedente de `aplicar_lei_margem._bloco_novo`, que preserva o
  `verificador` do artefato. Os 3 filmes voltaram a 2781 (valor do snapshot
  anterior à rodada, restante do carimbo idêntico); só `hard-to-be-a-god`,
  cuja contagem mudou, diz 2782. Conferido depois: os 6 filmes e o controle
  `burning-2018` reconstroem idênticos ao publicado, e o diff de cada um
  contra o commit é só a marca saindo (mais a célula de `hard-to-be-a-god`).
  +2 testes fixam a regra nos dois sentidos.
- **Estado final das 12:** 6 verificadas de fato (5 confirmam, 1 remove), sem
  marca; 6 pendentes (`erro_JSONDecodeError`, os 5 filmes da rodada 4), com
  `verificacao_pendente` no JSON publicado. Retentá-las agora seria possível
  (a fila está normal) — não feito, por não estar no pedido.
- Suíte ao fim da rodada: 2001 coletados / 1995 passam / 5 falhas
  conhecidas (as mesmas) / 1 xfail. Nenhuma asserção afrouxada.

**Rodada 7 (2026-09-14) — as 6 reviews restantes, com o adaptador de
sobrecarga já no ar.** Sonda antes: 2,2 s, sem retentativa — mesma fila
normal da rodada 6. Mesmo método: por filme, na ordem, `--slug` restrito;
medição ANTES de gravar; PARAR se o estado publicado mudar.

| filme | review | veredito | efeito publicado |
|---|---|---|---|
| `speak-no-evil-2022` | medianas `viewing:1477019671` | **remove** | **`estado_publicado_mudou: true` — NÃO GRAVADO** |
| `the-cloud-capped-star` | positivas `viewing:1255160718` | remove | `impacto_emocional`/positivas 20/40 → 19/40 (lift 20,0 → 17,5 pp) |
| `the-turin-horse` | positivas `viewing:1466699858` | confirma | só sai a marca |
| `whiplash-2014` | medianas `viewing:1478219894` | **FALHOU DE NOVO** | nada muda — bloco reconstruído idêntico ao publicado, sem escrita |
| `zama` | negativas `viewing:1414135189` | **FALHOU DE NOVO**, erro diferente (char 99 → char 97) | review continua pendente |
| `zama` | positivas `viewing:1487064786` | confirma | marca sai; a outra review de `zama` continua pendente |

**`speak-no-evil-2022` — o caso previsto, medido ANTES de gravar, PARADO.**
O DeepSeek confirmou desta vez que o verificador REMOVE
`impacto_emocional` da review (`confirma: false`). Medido, não aplicado:

- `estado_publicado_mudou: true`;
- `mencoes`: `impacto_emocional`/medianas 19/40 → 18/40 (lift −20,0 →
  −22,5 pp);
- **dois bullets mudam:** o bullet de `impacto_emocional` em `medianas`
  SOME (deixa de ser `frequencia`); o bucket `medianas` ganha um bullet
  novo em `comparacoes` (era `None`, vira `frequencia`) — a MESMA
  substituição de bullet que o piloto de 2026-09 tinha previsto;
- contraste, `n`, margem e os três briefings ficam iguais.

**Nada foi gravado.** O JSON publicado de `speak-no-evil-2022` continua
com `impacto_emocional`/medianas em 19/40 e `verificacao_pendente` (o
estado de antes desta rodada). O veredito REAL já está em
`consenso_verificado.jsonl` (a chamada ao verificador não é reversível: ela
já aconteceu e o dado é o dado) — só o bloco `eixos` do JSON publicado, que
`republicar_eixos.py` se recusa a escrever sem `--aceitar-mudanca-de-estado`,
ficou para trás.

**Duas falhas NÃO relacionadas à sobrecarga.** `whiplash-2014` e uma das
duas reviews de `zama` falharam de novo com `JSONDecodeError` — mensagens
DIFERENTES da tentativa anterior (char 95 antes, char 95 de novo em
whiplash; char 99 → char 97 em zama), confirmando o diagnóstico original da
C3: é o modelo produzindo JSON malformado de forma não determinística nessa
review específica, não fila cheia. O adaptador novo (rodada 5) não tem o
que fazer aqui — não é `LLMSobrecarga` nem `LLMPrazoExcedido`, é
`json.JSONDecodeError` no parsing normal, retentada 0 vezes a mais (por
decisão de escopo: o script já não retenta JSON inválido em cima da
retentativa do adaptador, ABERTO.md rodada anterior de C16 "Entrega 2").

**Integridade:** conferido por hash, 51 de 55 filmes idênticos ao snapshot
desta rodada; as 5 linhas que mudam são exatamente as 5 reviews com
veredito novo (a 6ª, `speak-no-evil-2022`, teve o consenso atualizado mas
o JSON publicado preservado, de propósito).

**Status final de C3 — FECHADA PARCIALMENTE, com causa remanescente
IDENTIFICADA, não corrigida.**
- Das 12 reviews originais: **9 têm veredito real** (7 confirmam
  `impacto_emocional`, 2 removem — `hard-to-be-a-god` na rodada 6 e
  `the-cloud-capped-star` nesta). **1 tem veredito real mas NÃO publicado**
  por decisão do dono (`speak-no-evil-2022`, mudaria bullets). **2
  continuam sem veredito** (`whiplash-2014` e uma review de `zama`) — não
  por sobrecarga, mas por JSON malformado recorrente e não determinístico
  do modelo nessa review específica.
- **A causa de origem da instabilidade do V2_alvo — JSON malformado não
  determinístico — NÃO foi corrigida e não tinha como ser por este
  trabalho**: a sobrecarga do DeepSeek (rodada 5) e a instabilidade de
  parsing (C3 original) são dois mecanismos DIFERENTES que produzem o
  mesmo sintoma (`ok: False`, review sem veredito). A rodada 5 resolveu o
  primeiro; o segundo é o que a C3 já descrevia antes desta sessão
  (`JSONDecodeError`, taxa 0,19%–0,87%, sem correção proposta).
- **Consequência prática:** `whiplash-2014` e `zama` continuam publicados
  com `verificacao_pendente`; retentar de novo tem chance de sucesso (é
  não determinístico — 8 de 8 reviews antigas passaram ao serem refeitas,
  no piloto original), mas nenhuma garantia. `speak-no-evil-2022` tem
  veredito pronto, aguardando decisão sobre publicar a mudança de bullet.

Suíte ao fim da rodada: 2001 coletados / 1995 passam / 5 falhas conhecidas
(as mesmas) / 1 xfail. Nenhuma asserção afrouxada; nenhum arquivo novo de
teste (o método reusa `republicar_eixos.py` e
`verificador_impacto.aplicar-producao`, já testados).

**Rodada 8 (2026-09-15) — `speak-no-evil-2022` publicado; disjuntor
implementado.**

**`speak-no-evil-2022`, publicado por decisão do dono.** Manter o JSON antigo
era preservar uma marcação que só sobreviveu porque uma chamada anterior
falhou. Remedido antes de gravar (idêntico à rodada 7) e gravado com
`republicar_eixos.py --aplicar --aceitar-mudanca-de-estado`:
- `impacto_emocional`, `bullet_de`: `medianas` `frequencia` → **nenhum**
  (negativas e positivas seguem `frequencia`);
- `comparacoes`, `bullet_de`: `medianas` nenhum → **`frequencia`**;
- `impacto_emocional`/medianas 19/40 → 18/40 (lift −20,0 → −22,5 pp);
- efeito colateral: `impacto_emocional`/positivas continua 27/40, mas o lift
  vai de 20,0 para 22,5 pp, porque o lift é relativo aos outros buckets. Isso
  deixa a célula **0,33 pp abaixo da margem de 22,83 pp**, e
  `acima_da_margem` segue `False` — a célula mais perto de cruzar entre os
  filmes tocados nesta sessão;
- contraste (`valorativo`), `n` (40) e os briefings de narrativa, veredito e
  condições idênticos — as condições revisadas à mão continuam valendo;
- `verificador.n_removidas_no_corpus` 2781 → 2784, correto pela regra da
  rodada 6: as contagens do filme mudaram;
- conferido por hash: 113 de 114 arquivos publicados (`resultado/*.json`,
  `frontend/data/*.json`, consenso verificado, manifesto) idênticos; só o
  JSON do próprio filme mudou.

**Disjuntor do DeepSeek — implementado com o desenho aprovado.**
- estado em ARQUIVO (`config.CIRCUITO_ARQUIVO` = `dados/lote/circuito_deepseek.json`,
  já no `.gitignore`), porque o lote de publicação roda um subprocesso por
  filme e um disjuntor em memória recomeçaria fechado a cada um;
- abre em 3 `LLMSobrecarga` SEGUIDAS (`CIRCUITO_LIMIAR_SOBRECARGAS`),
  contadas depois da retentativa do adaptador e globalmente, entre threads e
  processos. `LLMPrazoExcedido` NÃO conta; qualquer resposta válida zera a
  contagem;
- escopo global, não por estágio: o portão fica em `deepseek_resposta`, por
  onde passam classificação, rotulagem, verificador e síntese;
- aberto, toda chamada DeepSeek falha na hora com `LLMCircuitoAberto`, sem
  tocar a rede e sem entrar na retentativa;
- reabertura por sonda com prazo FIXO de 5 min (`CIRCUITO_REABERTURA_S`).
  Vencido o prazo, a chamada passa de verdade: se responde, fecha; se volta
  `LLMSobrecarga`, reabre por mais 5 min, mantendo `aberto_desde`. Sem
  exponencial nesta versão: não há dado sobre duração de sobrecarga, e a
  latência só agora é gravada;
- a falha por disjuntor aberto usa o mecanismo que já existia:
  - no verificador vira `ok: False` com motivo `circuito_aberto`
    (`_motivo_pendencia`) e marca `verificacao_pendente`;
  - na classificação vira `ok: False` com o motivo no erro;
  - na rotulagem, a subclasse de `LLMIndisponivel` impede empilhar
    retentativas;
  - na síntese, o filme falha alto, como em qualquer sobrecarga;
  - nada é abortado e nada se perde: a reexecução retenta só o pendente;
- abertura, reabertura e fechamento são avisados no stderr, que o harness
  grava no log de publicação;
- escrita atômica (temporário + `os.replace`) sem lock de arquivo entre
  processos, com `threading.Lock` dentro do processo. O trade-off está
  registrado em comentário no código: corrida rara produz log ruidoso (uma
  sobrecarga não contada, um aviso duplicado), nunca dado incorreto. No lote
  de publicação os filmes rodam em sequência, então a corrida nem acontece
  ali;
- arquivo ausente ou ilegível = FECHADO: defeito no disjuntor nunca barra
  tráfego sozinho; sucesso com estado limpo não escreve no disco.

**Isolamento de teste.** Como o estado é arquivo, ele também valeria entre
TESTES: três testes de sobrecarga seguidos abririam o disjuntor real e
quebrariam todo teste seguinte — e a próxima execução de produção. Um fixture
autouse em `tests/conftest.py` dá a cada teste um arquivo próprio. Conferido:
`dados/lote/circuito_deepseek.json` não existe antes nem depois da suíte
inteira.

Testes: `tests/test_disjuntor_deepseek.py` (16), sobre o SDK real da OpenAI
com transporte falso. Cobrem:
- abre em 3 seguidas, não em 2, e aberto não chama a rede;
- NÃO abre com `LLMPrazoExcedido`;
- sucesso zera a contagem e, com estado limpo, não escreve no disco;
- o estado sobrevive entre processos: abre num subprocesso e barra no outro;
  a contagem soma entre processos;
- antes do prazo segue barrado; a sonda que responde fecha, e a que volta
  sobrecarga reabre por mais um prazo;
- com disjuntor aberto, o verificador marca `circuito_aberto` e a
  reexecução retenta só o pendente; a classificação grava `ok: False`;
- o arquivo mora em `dados/lote/` e o git o ignora; a escrita não deixa
  temporário e um arquivo corrompido vale fechado.

Nenhuma asserção afrouxada. Suíte: 2017 coletados / 2011 passam / 5 falhas
conhecidas (as mesmas) / 1 xfail.

### C17. Referências quebradas após `docs/arquivo-de-estudos/` sair do git (2026-09-14)

O commit que removeu `galeria-de-stills/`, `piloto-expansao/` e
`revisao-condicoes/` do rastreamento (política da sessão: estudo fica
untracked) deixou os arquivos no disco, mas nada no repositório versionado
os garante presentes num clone limpo. **Dívida conhecida, não corrigida —
não é regressão desta sessão**, já existia antes: esses três diretórios só
entraram no git por engano no commit anterior, e as referências abaixo já
apontavam para caminhos untracked antes disso.

**Sete referências em `ABERTO.md`** apontam para arquivos que só existem no
disco de quem rodou a sessão: linhas 252, 541, 551, 554, 716, 755 e 1063
(nesta numeração) — `ETAPA_0_PROPOSTA.md`, `RELATORIO_piloto-18.md`,
`lote-piloto-18-corrigido/`, `PROPOSTA_POS_REVISAO_PILOTO_18.md`,
`ROTULAGEM_PARES_piloto-18.md`, `ROTULAGEM_PARES_catalogo-35.md` e
`insumo-proximo-lote/`. As linhas 252 e 541 já se declaravam "untracked" —
a numeração muda a cada edição do arquivo, o texto não.

**Quatro testes dependem desses arquivos** e, num clone limpo, falham ou são
pulados (o mesmo que já acontecia antes desta sessão tocar o repositório):
`test_aplicar_revisao_condicoes.py`, `test_pares_para_rotulagem.py`,
`test_publicar_condicoes.py`, `test_relatorio_revisao_condicoes.py`.

**Dois scripts gravam nesses diretórios por padrão:**
`pares_para_rotulagem.py` e `relatorio_revisao_condicoes.py`
(`revisao-condicoes/`).

**O `.gitignore` cobre só os três diretórios, de propósito** — um padrão
para `docs/arquivo-de-estudos/` inteiro ignoraria as 7 subpastas já
rastreadas desde `85a8f11` (`aceite-e-mapa`, `classificacao`, `coleta`,
`condicoes-de-decisao`, `editor-e-narrador`, `margem-de-lift` — que inclui
`ESTUDO_MARGEM_20PP.md`, a referência viva — e `spec-estrutura`).

**Não corrigido nesta sessão** — nem os caminhos, nem os testes, nem os
scripts. Decisão do dono: registrar, não consertar.

### C18. O saldo do DeepSeek zerou no meio do lote de 44 (2026-09-16)

**O que aconteceu, medido.** O lote noturno de 44 filmes (coleta →
classificação → verificador, sem publicar) terminou limpo em 3h41, mas o
estágio do verificador registrou **174 reviews sem veredito**. Delas, **139
são `402 Insufficient Balance`**, todas idênticas palavra por palavra, e
concentradas nas **últimas 142 linhas** de `verificador_producao.jsonl`
(índices 9166–9307 de 9308) — o fim absoluto da rodada. Saldo medido em
seguida: **-US$ 0,14, `is_available: false`**.

**Não é (A) nem (B) da C3** — é um terceiro mecanismo. (A) é fila cheia
declarada no corpo com HTTP 200; (B) é JSON malformado numa resposta que
chegou; este é 4xx de BILLING, e a conta não volta sozinha. O disjuntor de
sobrecarga não viu nada porque conta `LLMSobrecarga`, e 402 não é fila.

**O aviso existiu e ninguém viu.** Antes dos 402 vieram **3 `429`** cuja
mensagem já dizia a causa: *"concurrency ... based on your remaining
balance"*. O provider corta a concorrência conforme o crédito cai.

**PENDENTES POR SALDO, NÃO POR JULGAMENTO** — o registro que interessa a
quem for publicar estes dois filmes:
- **`uncut-gems`: 100 de 100 candidatas** sem veredito do verificador;
- **`top-gun-maverick`: 39 de 77.**

As 139 seguem com `impacto_emocional` na marcação ORIGINAL, por política
conservadora, e marcadas `verificacao_pendente` — visíveis, como as da C3.
**Decisão do dono (2026-09-16): publicar assim, e reverificar em DeepSeek
quando houver saldo — NÃO em Gemini.** O custo em Gemini seria irrisório
(~US$ 0,09–0,14), mas exigiria mudar `rodar_passe` e misturaria providers
dentro do mesmo eixo: os **39,9% de remoção medidos nos 44** (1.369 de 3.434)
saíram de DeepSeek/`V2_alvo`, e 139 reviews julgadas por outro modelo não
seriam comparáveis. Custo de reverificar em DeepSeek: **~US$ 0,01**.

**Os outros 30 são a C3(B) de sempre:** `JSONDecodeError` (`Extra data`),
30/3.434 = **0,87%**, idêntica à taxa histórica do piloto, espalhados por ~20
filmes. **Não retentados, por decisão do dono** — mesmo motivo da C3.

**CORRIGIDO: disjuntor de SALDO** (`config.CIRCUITO_SALDO_*`,
`synthesize.py`, `tests/test_disjuntor_saldo.py`). Desenho aprovado
integralmente pelo dono, e deliberadamente DIFERENTE do de sobrecarga:
- **402 abre na PRIMEIRA ocorrência** (`CIRCUITO_SALDO_LIMIAR = 1`) — saldo
  negativo é estado determinístico da conta, não a fila oscilante que exige 3
  confirmações. As 139 falhas foram o custo de confirmar 139 vezes o que a
  primeira resposta provou;
- **exceção própria, `LLMSaldoEsgotado`**, irmã e não sinônimo de
  `LLMCircuitoAberto`: quem trata precisa saber que esta não passa sozinha;
- **sonda por `GET /user/balance`**, grátis e sem consumir crédito (é a única
  sonda possível numa conta sem saldo), a cada **30 min** e não os 5 min
  calibrados para fila. Sonda que falha NÃO fecha o disjuntor;
- **o `429` de concorrência por saldo vira AVISO ALTO** na primeira
  ocorrência, uma vez por processo, e não abre nada;
- **o passe ABORTA** (`SystemExit`) em vez de arrastar a fila contra conta
  morta, e **não grava registro nenhum** das não tentadas — sem registro, a
  reexecução pós-depósito retenta todas. Medido no teste: o dano fica preso a
  UMA onda de concorrência (8 chamadas), não às 139.

**Buraco de cobertura achado no caminho — e ele é o mais grave desta
rodada.** `scripts/gerar_condicoes.py` foi commitado em `18a1196` **sem
compilar** (f-string com literal não terminado), justamente no commit que
adotou o briefing variante como default de produção. `compileall` sobre
`scripts/` + `src/` mostrou que era o ÚNICO arquivo quebrado. Nenhum teste o
abria. Corrigido (2 linhas) e **acrescentado a `SCRIPTS_SEM_LACO`**, cujo
`ast.parse` transforma erro de sintaxe em falha de teste. **Ainda fora de
qualquer teste, no caminho de produção:** `lote.py`,
`relatorio_revisao_condicoes.py`, `aplicar_revisao_condicoes.py`,
`enriquecer_eixos.py`, `backfill_ano.py`, `recalcular_margem_exata.py`.

**A suíte ganhou uma 4ª falha que é da EXPANSÃO, não do código.**
`test_publicar_condicoes::test_a_regra_reproduz_as_oito_da_lista_e_so_retem_as_tres_medidas`
assume **consenso ⊆ publicado**: `_temas_retidos_no_catalogo()` varre os
slugs de `consenso.jsonl` e abre `resultado/<slug>.json` de cada um. Com os
44 no consenso e nenhum publicado, quebra em `FileNotFoundError`. **É a mesma
CLASSE dos 6 testes que fixavam o catálogo em 35, mas o espelho deles:**
aqueles congelavam a CONTAGEM e precisaram derivar da fonte real; este deriva
a POPULAÇÃO da fonte real e congela o RESULTADO (`retidos - OITO_DA_LISTA ==`
três pares literais). **Publicar os 44 não cura** — troca `FileNotFoundError`
por falha na igualdade assim que qualquer um dos 44 tiver tema retido em
`expectativa`. Conserto proposto, NÃO feito (aguarda aval): fixar a população
no catálogo em que a medição foi feita, em vez de "todo slug do consenso" —
o que preserva a asserção inteira em vez de afrouxá-la.

---

## D. Régua e medição

### D1. A limitação in-sample da lei por `n`
A taxa de ~5% de falso contraste é **in-sample e otimista**. A expansão do
catálogo é o primeiro teste out-of-sample: o protocolo manda rodar o nulo do
máximo sobre os filmes **novos** e recalibrar a constante, não os filmes.

### D2. Faixa de `rotulo_peso` acima de ~90%
Candidato não aplicado desde a v1.9.0; o mapa em vigor topa em ≥70%.

### D3. Tautologia de um lado no veredito — diagnosticada, não corrigida

### D4. Conectivo contrastivo a 82% — número medido, decisão do dono

### D5. A inflação de quantidade nas paráfrases — 80 de 611 temas
Dívida a montante que a feature das condições tornou visível.

---

## E. Interface

### E1. Cadência da animação da barra — sempre, ou uma vez por sessão?

### E2. Busca da home
Pendência registrada no handoff, sem decisão.

---

## F. Código morto e resíduo

### F1. `BANDAS_QUANTIFICADOR` — código morto

### F2. Ramo do editor aposentado ainda imprime no render
`src/espectro24/render.py` mantém um ramo que imprime
*"Edição [E2]: DESLIGADA (--no-edicao)"* para uma flag que não existe mais e um
estágio que não roda desde a v1.9.10.

### F3. O changelog tem lacuna entre v1.9.34 e v1.9.49
As versões **v1.9.35–v1.9.48** não têm entrada de changelog na forma
`- **vX.Y.Z**`; a v1.9.49 foi registrada sem preencher retroativamente essa
lacuna. Decidir se as versões ausentes ganham entrada retroativa ou se a
numeração do documento admite versões sem changelog.

---

## G. A próxima passada de corte na documentação

A divisão de 2026-09-04 parou num ponto declarado, não num ponto natural. Os
dois itens abaixo são **o trabalho que ela adiou** — não observação de rodapé.

### G1. O `§3[E]` foi cortado em granularidade de SUBSEÇÃO, não de parágrafo

O render é a maior seção da spec original e a única cujo corte ficou grosso.

| | linhas |
|---|---:|
| `§3[E]` na spec original | **1.362** |
| foi para `HISTORICO_FRONTEND.md` | 688 |
| **ficou na `SPEC.md`** | **674** |
| dessas 674, quanto é lei de verdade | **não medido** |

**O que isso significa na prática:** as outras seções foram cortadas parágrafo
a parágrafo, com o ponto de virada localizado um a um. O `§3[E]` não — nele a
lei e a medição alternam **dentro** do mesmo bloco (a decisão vem primeiro, a
medição que a sustenta vem logo abaixo, e o padrão se repete em cada um dos
sub-blocos de animação, pôster, backdrop e topo editorial). Cortar mais fino
sem uma passada frase a frase produziria erro, e a sessão não tinha mandato
para reescrever.

**A consequência que o leitor sente:** as ~674 linhas de render que estão na
`SPEC.md` ainda carregam medição junto da regra — variantes rejeitadas,
números de CLS, composição analítica de backdrops. É exatamente o defeito que a
divisão existia para corrigir, sobrevivendo numa seção só.

**O que decidir:** se vale uma passada frase a frase no `§3[E]`, ou se render
é uma camada em que lei e medição são inseparáveis na prática e o corte grosso
é o certo. **A decisão fecha o item; não é preciso esperar versão nova.**

### G2. Vinte e um parágrafos de justificativa embutida sobreviveram na `SPEC.md`

A decisão de formato da divisão foi: regra fica, justificativa sai e vira
ponteiro. Ela foi aplicada onde o corte era de bloco inteiro — mas **não** onde
a justificativa está no mesmo parágrafo da regra, ou num parágrafo logo abaixo
dela dentro do mesmo bloco. Varredura da `SPEC.md` final encontrou **21**
sobreviventes. Eles se dividem em três naturezas, e **só a primeira é
claramente para mover**:

**(a) Parágrafo inteiro de justificativa, com cabeçalho que o anuncia — 11
casos.** São os mais fáceis: o cabeçalho já diz que o que vem é *por quê*.

| linha | abre com |
|---:|---|
| 347 | *"**Por que:** 2,5★ é o ponto médio exato da escala…"* (fronteiras de bucket) |
| 399 | *"**Por que não `by/added-earliest`**…"* |
| 441 | *"**Por que 20 e não outro número**…"* (`LIMIAR_PASSADA_ANTIGA`) |
| 678 | *"**Por que os dois critérios, e não só o lift.**"* |
| 1068 | *"**Por que observacional e NÃO preditivo.**"* (extensão por déficit) |
| 1709 | *"**Por que não exibir texto bruto (v1.1.4)**…"* |
| 2210 | *"**Por que a invariante (c) existe (v1.2.1 — defeito corrigido)**…"* |
| 2212 | *"**Por que o quantificador virou pré-computado (v1.2.3…)**…"* |
| 2214 | *"**Por que o Movimento 1 é condicional à ficha (v1.3.0)**…"* |
| 2404 | *"**Por que ela existe, e são dois riscos distintos.**"* |
| 627 | *"**Por que esta frase e não outra, em três invariantes:**"* — **caso de fronteira**: abre como justificativa mas o que vem depois são três invariantes protegidas por teste, que são lei |

**(b) Nota histórica que não é lei nenhuma — 4 casos.** Linhas **405**
(*"Correção de registro: a v1.0.0 justificou `by/activity`…"*), **744** (a
correção do diagrama do pipeline), **1526** (*"O defeito que corrige"*, na
estratificação da seleção) e **2109** (*"Motivo — as métricas não acompanham
qualidade"*). Estas pertencem aos `HISTORICO_*`, não à lei.

**(c) Ressalva declarada — 3 casos, e o argumento é que elas FICAM.** Linhas
**411** (*"trocar `by/activity` por `by/added` troca um viés por outro"*),
**465** (o recorte de coorte da passada seletiva) e **944** (fronteira exata no
posicionamento). Não são justificativa: são **declarações de limitação que o
produto se obriga a carregar**, no mesmo estatuto da ressalva de assimetria de
validação. Mover isso para o histórico esconderia limitação conhecida — que é
o oposto do que este projeto faz.

**Três casos que a varredura por padrão não pega, e que valem a mesma
inspeção:** a coluna **"Razão"** da tabela de retentativa do §2.4 (quatro
linhas de *por quê* dentro de uma tabela de lei); o parágrafo do
`SobrecargaError` que não herda de `FetchError` *"deliberadamente"*, com o
motivo colado; e o caso `barbie` inteiro dentro de *"`taxonomia_id` no veredito
não é burocracia"*.

**O que decidir:** se (a) e (b) saem numa próxima passada — são 15 parágrafos,
trabalho de uma sessão — e se (c) fica onde está. **O critério proposto:** sai
o que responde *por que a regra é essa*; fica o que responde *o que esta regra
não garante*.
