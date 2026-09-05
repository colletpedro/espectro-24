# ABERTO — o que ainda é decisão

Este arquivo responde *"o que eu preciso decidir?"*. Antes de 2026-09-04 esta
lista não existia como arquivo: os itens estavam espalhados por doze lugares da
`SPEC.md`, quase sempre dentro da seção que os produziu, e por isso invisíveis
para quem não lia a seção inteira.

**O critério de saída de um item daqui é uma decisão registrada — não uma
versão nova.** É o que impede o padrão que a auditoria estrutural encontrou:
item já fechado continuar escrito como aberto, porque o lugar onde ele estava
escrito não tinha estado.

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

### B2. O eixo `expectativa`: 6 condições retiradas, destino não decidido

As 6 condições do eixo foram lidas no portão editorial, marcadas para retirada
e **não publicadas** — 257 foram ao ar, não 263. A decisão pendente é se
`expectativa` alimenta as CONDIÇÕES ou pertence ao VEREDITO. É o único eixo cuja
polaridade se inverte conforme o grupo, e é isso que cria o conflito.

### B3. Fase 1 → Fase 2: as condições substituem o veredito?

A coexistência (condições + veredito + bullets juntos) é declaradamente **Fase
1**. Sob que critério se decide passar à Fase 2, e o que acontece com o veredito
nela, está em aberto.

### B4. A pergunta de simetria visual que a inspeção não respondeu

Com a barra no ar, os dois lados da decisão ficam visualmente simétricos mesmo
quando o peso é muito assimétrico. A inspeção não respondeu se isso é problema.

---

## C. Pipeline e dados

### C1. `talk-to-me-2022` publica a ficha de outro filme
Defeito conhecido, aberto, no estágio de ficha TMDB.

### C2. Guarda de identidade no pipeline
Não existe uma checagem que impeça um filme de ser publicado com metadados de
outro — o defeito de C1 é o caso concreto que ela pegaria.

### C3. Instabilidade do verificador de `impacto_emocional` (5 filmes)
Registrada, não corrigida.

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

### F3. O changelog para na v1.9.34, o título vai a v1.9.37
As versões **v1.9.35, v1.9.36 e v1.9.37** não têm entrada de changelog na forma
`- **vX.Y.Z**`, apesar de terem posto 257 condições no ar. Decidir se ganham
entrada retroativa ou se a numeração do documento passa a admitir versões sem
changelog.
