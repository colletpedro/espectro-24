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

### B3. Fase 1 → Fase 2: as condições substituem o veredito?

A coexistência (condições + veredito + bullets juntos) é declaradamente **Fase
1**. Sob que critério se decide passar à Fase 2, e o que acontece com o veredito
nela, está em aberto.

### B4. A pergunta de simetria visual que a inspeção não respondeu

Com a barra no ar, os dois lados da decisão ficam visualmente simétricos mesmo
quando o peso é muito assimétrico. A inspeção não respondeu se isso é problema.

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
até agora: 6 (crash de n<10) e 8 (recoleta na publicação, na causa; o
`get-out-2017` já publicado continua contaminado). Enquanto qualquer um
estiver aberto, os 300 não devem ser disparados.

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
4. **Scraping: 23,7 h medidas para 300, não 16 h.** 284 s/filme (mediana
   256, 177–457), 115,8 req/filme a 2,46 s/req. A projeção anterior usava o
   perfil do lote 1 (77,7 req/filme). Filmes obscuros pedem MAIS requisições
   (`satantango` 187, `hard-to-be-a-god` 174, `zama` 149): a expansão, que é
   de filme obscuro, tende a ser pior que a média do piloto. **Projeção do
   PIPELINE INTEIRO, medida ponta a ponta no piloto:** scraping 284 s +
   classificação ~51 s + verificador ~12 s + publicação 60 s + condições
   ~18 s ≈ 7 min/filme → **~35 h para 300**, e **~US$ 31** pelo custo real
   do item 3 (sem veredito, que não foi gerado no piloto e falta medir).
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
      nenhuma geração foi feita nesta sessão;
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

16. **R13 por REGRA, não por enumeração — PROPOSTO, NÃO IMPLEMENTADO.**
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
