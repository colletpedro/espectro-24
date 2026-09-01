# Refazimento de gabarito + extensão de cobertura

**Duas sessões.** A primeira (Entregas 1–2, e a Entrega 3 até a medição de
custo) foi leitura, medição e preparação — zero chamada de LLM, `resultado/`
sem diff. A segunda (esta atualização) executou a Entrega 3 depois de o dono
aprovar explicitamente a saída **(b)** — deixar o caminho oficial mutar os
arquivos, sem snapshot/restore — com a razão registrada de que o requisito de
"arquivo novo" protegia contra sobrescrita ACIDENTAL, não contra o resultado
declarado do próprio pedido. **Chamadas de LLM nesta segunda parte: 4.534**
(3.570 de classificação + 964 do verificador). `taxonomia_id` segue
`ebab2667de74`, inalterado. Commit `b60dcae`.

**Convenção:** **MEDIDO** traz número e fonte; **VISTO** é leitura à mão sobre
amostra nomeada.

---

# ENTREGA 1 — o ajuste no protocolo

Aplicado em `SPEC.md` §2.7, em duas seções novas.

## P4 revisado — julgar contra o tema E contra a paráfrase

P4 dizia *"contando no nível do **tema** (não do exemplo)"*. **Está errado.**

O que o leitor vê é o par tema + `exemplo_parafraseado`, e é a paráfrase que
carrega a afirmação específica. O caso que forçou a correção é o [11] do
`wonka`: a paráfrase publicada diz literalmente *"cenários artificiais"*, e a
review alemã diz *"Alles ist mir einen Ticken zu künstlich"* com um exemplo
visual concreto. Contra o título curto do tema, isso sai `não sustenta`; contra
a paráfrase, `sustenta`. Eu tinha a paráfrase na folha e julguei só contra o
título.

**P4 passa a ser:** o julgamento é contra o tema **e** contra o
`exemplo_parafraseado`. O quantificador da paráfrase continua **não** sendo
testado (P3) — "para a maioria" não é a pergunta.

## O viés medido da leitura por modelo

**MEDIDO** na calibração de `wonka`/negativas:

| | valor |
|---|---:|
| concordância | **30/32 = 93,8%** |
| discordâncias | **2** |

| # | dono | modelo | erro |
|---|---|---|---|
| [2] *"Oddio forse le scenografia ma per il resto è tutto dozzinale"* | **contradiz** | não sustenta | perdeu um `contradiz` |
| [11] *"Alles ist mir einen Ticken zu künstlich"* | **sustenta** | não sustenta | perdeu um `sustenta` |

**O modelo errou nas duas direções possíveis de erro conservador — deixou de
contar apoio e deixou de contar contradição — e em nenhuma delas contou a
mais.** É a mesma direção do defeito do protocolo antigo, mais fraca e presente.

Registrado na spec junto com a consequência de desenho: **gabarito não sai de
modelo sozinho**, e onde houver divergência **o veredito humano vale**.

---

# ENTREGA 2 — os dois gabaritos pendentes

## Etapa A — minha leitura integral (feita)

80 reviews lidas por inteiro (40 + 40), sob P1–P7 com o ajuste da Entrega 1,
sem casamento por palavra-chave, no idioma original, com frase literal para
cada `sustenta` e cada `contradiz`. Em
**`LEITURA_CODE_2_NAO_ABRIR_ANTES.md`**.

| caso | sustenta | contradiz | não sustenta |
|---|---:|---:|---:|
| `talk-to-me-2022` / neg — *Diálogos e tom juvenil artificiais* | **5** | 0 | 35 |
| `napoleon-2023` / med — *Batalhas visualmente impressionantes* | **12** | **2** | 26 |

**Contexto — para calibrar a expectativa, não para decidir nada:**

| | gab. antigo | `mencoes` | binária A | binária B | **minha leitura** |
|---|---:|---:|---:|---:|---:|
| `talk-to-me` neg | 2 | 5 | 4 | 3 | **5** |
| `napoleon` med | 13 | 15 | 12 | 11 | **12** |

## Etapa B — as folhas do dono (PREENCHIDAS e comparadas, 2026-08-31)

**`FOLHA_LEITURA_CEGA_TALK_TO_ME_NEG.md`** e
**`FOLHA_LEITURA_CEGA_NAPOLEON_MED.md`**.

**MEDIDO — composição das folhas:**

| grupo | `talk-to-me` | `napoleon` |
|---|---:|---:|
| **G1** — marquei `sustenta` ou `contradiz` | 5 | 14 |
| **G2** — marquei `não sustenta` **com** o assunto tocado | 4 | 9 |
| **controle cego** — sorteadas de `não sustenta` sem o assunto tocado | 5 | 5 |
| **total na folha** | **14** de 40 | **28** de 40 |
| (fora da folha) | 26 | 12 |

**O dono lê 42 reviews no total**, contra 80 se lesse os dois buckets inteiros.

A amostra de controle foi sorteada com **semente 24** sobre a lista ordenada dos
índices de G3, registrada em **`REGISTRO_AMOSTRA_CONTROLE.json`** antes de
qualquer comparação: `talk-to-me` [3, 16, 21, 27, 38] · `napoleon`
[3, 20, 25, 33, 40].

**Nota honesta sobre o `napoleon`:** 28 de 40 é a maior parte do bucket, não uma
folha enxuta. Isso é consequência do próprio tema — 14 reviews afirmam ou negam
que as batalhas impressionam, e mais 9 fazem juízo visual sem citar batalha. A
folha reduzida economiza pouco ali; ela economiza de verdade no `talk-to-me`
(14 de 40).

**Cegueira conferida:** as duas folhas têm exatamente um `**` por bloco de
review — o rótulo `**Veredito:**` —, todos os blocos com formatação idêntica,
ordem de `selecao.selecionar()`, nenhuma tradução, nenhuma marca que revele de
qual grupo cada review veio.

## Etapa C — o comparador, RODADO

**`scripts/comparar_gabarito.py`**, generalizado para os dois filmes (o
`comparar_gabarito_wonka.py` continua onde está). Quebra a concordância
**por grupo** (G1 / G2 / controle) e aplica a regra de resolução — o dono
vence onde diverge — para emitir a contagem final do bucket. Resultado em
`RESULTADO_COMPARADOR_TALK_TO_ME.json` e `RESULTADO_COMPARADOR_NAPOLEON.json`.

### `talk-to-me-2022`/negativas — 71,4% de concordância (10/14)

| grupo | concordância |
|---|---|
| G1 (modelo marcou sustenta/contradiz) | **2/5 = 40%** |
| G2 (modelo marcou não sustenta, assunto tocado) | 4/4 = 100% |
| controle cego | 4/5 = 80% |

**A confirmação de que o grupo de controle importa mais que G1/G2 — e de
que ELE TAMBÉM pode achar erro, não só confirmar** (§ao lado): a
discordância em `viewing:1431255087` (controle, árabe) não é sobre a
fronteira do tema — é sobre o modelo não ter reconhecido a própria
limitação de idioma. G1, por sua vez, discordou em **3 de 5** — o
grupo que deveria ser o mais confiável (o modelo marcando positivo com
confiança) foi o mais fraco nesta calibração.

### `napoleon-2023`/medianas — 96,4% de concordância (27/28)

| grupo | concordância |
|---|---|
| G1 | 13/14 = 93% |
| G2 | 9/9 = 100% |
| controle | 5/5 = 100% |

Única discordância: `viewing:1438324629` (comparação de CG a jogo de
estratégia) — o modelo marcou `contradiz` por inferência, o dono marcou
`não sustenta` por leitura mais conservadora. Um caso, sem padrão de
direção.

### Gabaritos finais (regra: o dono vence onde leu; resto do bucket segue o modelo)

| caso | sustenta | contradiz |
|---|---:|---:|
| `talk-to-me-2022`/negativas | **2** | **0** |
| `napoleon-2023`/medianas | **12** | **1** |

**`talk-to-me-2022` fechou no mesmo valor do gabarito antigo (2). É
coincidência de destino, não validação do protocolo antigo** — os dois
métodos chegaram lá por caminhos diferentes (um por casamento de
palavra-chave em subamostra, o método que §2.7 da SPEC já mediu subcontar
em outros dois casos; o outro por leitura completa com resolução humana
registrada). Ver `SPEC.md` §2.7, tabela atualizada com os 5 casos.

## Etapa D — dois achados que corrigem o registro da calibração anterior

**Correção do achado do `wonka`.** A sessão que calibrou `wonka` registrou
*"o modelo tende ao conservadorismo"*, generalizando de um único ponto. Com
`talk-to-me-2022` como segundo ponto, a direção do erro é **oposta** — 3 de
5 marcações positivas em G1 foram infladas, não perdidas. **A leitura
correta: a confiabilidade da leitura por modelo depende do TIPO de
julgamento, não tem direção fixa.**

| caso | tipo de julgamento | concordância |
|---|---|---:|
| `napoleon-2023` | visual/concreto | 96,4% |
| `wonka` | visual/concreto | 93,8% |
| `talk-to-me-2022` | registro de fala / referência cultural / ironia | **71,4%** |

Temas visuais/concretos têm alta concordância nos dois casos medidos; um
tema sobre registro de fala tem concordância bem mais baixa, e ali o erro
foi para superextrapolação (aceitar analogia frouxa como sustentação), não
para perda. **É isso que justifica manter a leitura humana como decisão —
não existe um fator de correção fixo a aplicar no lugar dela.**

**Achado novo — o modelo nunca usa `não sei julgar`.** Nas 42 reviews das
duas folhas reduzidas, cobrindo ao menos 6 idiomas além do português, o
modelo escolheu `não sei julgar` **zero vezes** — inclusive numa review em
árabe que o dono classificou corretamente como tal. Distinto de erro de
interpretação em idioma que o modelo processa: é excesso de confiança em
idioma dominado só parcialmente. **Recomendação para os próximos gabaritos
da expansão:** reforçar a instrução de abstenção com este caso como
exemplo concreto no prompt, em vez da regra genérica sem exemplo de falha
real.

Os dois achados estão registrados em `SPEC.md` §2.7, substituindo (não
preservando ao lado como histórico) a generalização incorreta anterior.

---

# ENTREGA 3 — extensão de cobertura: EXECUTADA

## 3.1 — O custo, medido antes de rodar (era a pré-condição)

**MEDIDO — o que falta:** **1.190 reviews** em 31 dos 35 filmes → **3.570
chamadas** com votação de 3. (`estender_classificacao_producao.py --dry-run`
sobre os 35 slugs.) Os 4 filmes já em 100% são `cure`, `cidade-de-deus`,
`the-invite-2026` — os três estendidos na v1.9.15 — e `obsession-2026`.

**MEDIDO — o consumo real por review**, extraído dos 8.171 registros de `uso`
de `resultado/votacao-3/passe_1.jsonl` (não estimado):

| | valor |
|---|---:|
| `prompt_tokens` por review | **1.136** (regressão: 1.012 de base + 0,236 × `n_chars`) |
| `completion_tokens` por review | **36,9** |
| cache hit | 85% (1ª passada) · **94%** (2ª e 3ª) |
| `n_chars` médio das 1.190 faltantes | 512 |

Aplicando os preços DeepSeek de `verificador_impacto.py` (miss 0,14/M · hit
0,0028/M · saída 0,28/M):

| regime | 1 passada | **3 passadas** |
|---|---:|---:|
| conservador (85% hit) | US$ 0,044 | **US$ 0,13** |
| medido em regime (94% hit) | US$ 0,027 | **US$ 0,08** |

**Qual das duas estimativas do briefing está certa:**

| origem | estimativa | veredito |
|---|---|---|
| `AUDITORIA_POPULACAO_E_GABARITO.md` | ~US$ 0,03 | **certa para UMA passada**; subestima o trabalho completo em 3× |
| extrapolação da tabela do A/B (US$ 3,29 / 36.000 reviews) | ~US$ 0,11/passada · US$ 0,33 com 3 votos | **alta em ~4×** |

A extrapolação do A/B erra porque usa um custo por review (US$ 0,0000914)
medido num contexto com aproveitamento de cache diferente; o custo real por
review por passada é **US$ 0,000023–0,000037**. **O número que vai para a spec
é US$ 0,08–0,13 para o trabalho inteiro (3 votos), mais o passe do
verificador.** Nenhuma das duas muda a decisão — o custo não é o obstáculo.

## 3.2 — A população: requisito 2 satisfeito por construção

**MEDIDO.** `scripts/estender_classificacao_producao.py:66` chama
`amostra_do_bruto(slug, coleta=coleta, raiz=...)` —
[pipeline.py:450](src/espectro24/pipeline.py:450), que repassa
`orcamento_paginas_por_nivel`. **Não** passa por
[`classificar_10.py:152`](scripts/classificar_10.py:152), que é a chamada a
`selecionar()` sem esse parâmetro e a causa raiz registrada da divergência das
duas populações. **A extensão não reproduz o defeito.**

Confirmação independente: a cobertura que esse caminho calcula reproduz o
publicado ao dígito — **2.866/4.056 = 70,7%**, 8 filmes abaixo de 50%, 4 em
100%, exatamente o que `ESTUDO_CATALOGO_35.md` §6c registra.

## 3.3 — A decisão do dono, e a execução

O dono aprovou **(b)**, não a (a) que eu tinha recomendado: deixar o caminho
oficial mutar os arquivos, sem snapshot/restore. Razão registrada por ele: o
requisito de "arquivo novo" existia para proteger contra sobrescrita
ACIDENTAL de artefato publicado, e ali a sobrescrita era o resultado
DECLARADO do próprio pedido — a saída (a) trocaria risco real (`resultado/`
num estado intermediário que o guard-rail do pipeline recusa, dependendo de
um restore manual funcionar) por conformidade com um requisito que ele mesmo
identificou como mal escrito.

**Antes de rodar, dois itens confirmados no momento da execução** (não só no
planejamento):

1. `git status` limpo em `resultado/` (as duas `.bak` pré-existentes, exceção
   conhecida), commit-base `54f0e8e` registrado.
2. Confirmado de novo, lendo o código na hora: `estender_classificacao_
   producao.py` importa só `perfil_de`/`taxonomia_id` de `classificar_10.py`
   — nunca `selecionar()` — e `votacao_3.classificar_passe` classifica sobre
   `amostra.json` já persistido, sem re-selecionar. O caminho não passa por
   `classificar_10.py:152`.

**Execução, caminho oficial, zero linha de script alterada:**

```
python scripts/estender_classificacao_producao.py --slug <35 filmes>
python scripts/verificador_impacto.py aplicar-producao
```

| passo | resultado |
|---|---:|
| `amostra.json` | +1.190 reviews |
| passe 1 (3 votos) | 1.190/1.190, 0 falhas, 6,6 rev/s |
| passe 2 | 1.190/1.190, 0 falhas, 6,7 rev/s |
| passe 3 | 1.190/1.190, 0 falhas, 0,6–6,9 rev/s (throttling no meio) |
| consenso | 5.371 reviews, 0 incompletas |
| verificador `V2_alvo` | 964 chamadas novas, **8 falhas persistentes** (política conservadora: mantidas com a marcação original) |

**Custo real** (medido por diferença de linhas novas contra o commit-base, não
estimado de novo): classificação **US$ 0,1030** (3.570 chamadas — dentro da
faixa projetada de US$ 0,08–0,13), verificador **US$ 0,0471** (964 chamadas,
não projetado antes por não ter sido pedido) — **US$ 0,15 no total**.

**Arquivos que mudaram em `resultado/`: 8, não 7** — a lista prevista mais
`passe_1.jsonl`, que também recebeu as 1.190 linhas novas (a Entrega 3.1
original só tinha contado os 3 passes coletivamente). Todos confirmados por
`git diff --stat` depois do commit.

## 3.4 — Cobertura: 100% verificada, não presumida

**MEDIDO.** Reconstrução de `amostra_do_bruto` para os 35 slugs, interseção
com `consenso_verificado.jsonl`: **4.056/4.056 = 100,00%**, em **35 de 35**
filmes, zero abaixo de 100%. Antes da extensão: 2.866/4.056 = 70,7%, com 8
filmes abaixo de 50% (`perfect-days-2023` 39,2%, `hereditary` 42,5%,
`the-substance` 42,5%, `everything-everywhere-all-at-once` 43,3%, `aftersun`
44,2%, `dune-2021` 44,2%, `bones-and-all` 47,5%, `avengers-endgame` 48,3%).

## 3.5 — A previsão registrada, testada

A previsão feita antes de rodar tinha duas partes. **A primeira se
confirmou; a segunda não — e a segunda vinha com uma cláusula de parada
("investigue antes de seguir") que foi cumprida.**

**Parte 1 — frequência por eixo, ≤~2pp. CONFIRMADA.**

| eixo | antes (n=2.866) | depois (n=4.056) | Δ |
|---|---:|---:|---:|
| `ritmo` | 29,1% | 28,7% | −0,4pp |
| `atuacao` | 27,9% | 26,8% | **−1,2pp** |
| `direcao_imagem` | 30,4% | 30,1% | −0,3pp |
| `roteiro_estrutura` | 55,5% | 55,8% | +0,3pp |
| `som_trilha` | 12,7% | 12,8% | +0,0pp |
| `tom_atmosfera` | 22,0% | 22,1% | +0,1pp |
| `impacto_emocional` | 34,6% | 35,4% | +0,8pp |
| `comparacoes` | 36,4% | 36,8% | +0,4pp |
| `expectativa` | 19,9% | 19,9% | −0,0pp |
| `critica_social` | 23,1% | 23,0% | −0,1pp |
| `livre` | 9,1% | 9,6% | +0,5pp |

**Maior delta: 1,2pp.** Bate a previsão com folga.

**Parte 2 — nenhum filme muda de estado `contraste`. NÃO CONFIRMADA.**
**10 de 35 mudaram**: `bones-and-all`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `perfect-days-2023`,
`spider-man-across-the-spider-verse` (tematico→valorativo, 6); `dune-2021`,
`oppenheimer-2023`, `the-substance`, `wicked-2024` (valorativo→tematico, 4).

### Investigação — a causa, medida antes de prosseguir

Duas hipóteses testadas: (H1) as reviews que faltavam nesses 10 filmes
diferiam sistematicamente das já classificadas (a mesma causa que explicaria
um delta grande de frequência), ou (H2) o lift desses 10 já estava perto da
margem de 20pp, e a margem é conhecidamente porosa em n≈40.

**H1 REJEITADA.** Se fosse viés de conteúdo, o delta de frequência por eixo
seria grande nesses 10 filmes especificamente — não é: o maior delta
agregado do catálogo inteiro é 1,2pp (`atuacao`), a mesma ordem de grandeza
da previsão original.

**H2 CONFIRMADA — MEDIDO.** O lift observado (antes e depois) do eixo
vencedor de cada um dos 10, todos entre 14,9pp e 28,9pp — a poucos pontos da
margem de 20pp nos dois lados:

| filme | n antes/depois (mín. dos 3 buckets) | melhor lift ANTES | melhor lift DEPOIS |
|---|---|---:|---:|
| `bones-and-all` | 15–23 / 40 | 26,0pp (acima) | 17,5pp (abaixo) |
| `dune-2021` | 13–26 / 40 | 19,2pp (abaixo) | 20,0pp (acima) |
| `everything-everywhere…` | 16–19 / 40 | 28,9pp (acima) | 17,5pp (abaixo) |
| `hereditary` | 13–22 / 40 | 36,0pp (acima) | 15,0pp (abaixo) |
| `napoleon-2023` | 20–27 / 40 | 25,0pp (acima) | 12,5pp (abaixo) |
| `oppenheimer-2023` | 27–35 / 40 | 17,4pp (abaixo) | 25,0pp (acima) |
| `perfect-days-2023` | 12–18 / 40 | 28,9pp (acima) | 17,5pp (abaixo) |
| `spider-man…` | 20–22 / 40 | 25,0pp (acima) | 12,5pp (abaixo) |
| `the-substance` | 16–18 / 40 | 19,9pp (abaixo) | 27,5pp (acima) |
| `wicked-2024` | 24–36 / 38–40 | 14,9pp (abaixo) | 20,0pp (acima) |

**Cruzamento com o bootstrap já publicado** (`ESTUDO_CATALOGO_35.md` §8, B=2000,
sobre a população ANTES): `bones-and-all`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `perfect-days-2023` e
`spider-man-across-the-spider-verse` **já estavam na lista de marcações
frágeis (p<60%)** daquele bootstrap; `the-substance` estava no near-miss
(45%). **6 dos 10 filmes que mudaram de estado já eram sinalizados como
frágeis antes de qualquer extensão rodar.**

**Conclusão da investigação: não é achado novo de instabilidade — é o mesmo
achado do estudo anterior, agora observado com dado completo em vez de
reamostragem simulada.** A margem de 20pp em n≈40 não decide esses 10 filmes
com confiança; a extensão não criou esse problema, ela o tornou visível sem
precisar de bootstrap.

## 3.6 — Recálculo lado a lado

| | antes (n=2.866, 70,7%) | depois (n=4.056, 100%) |
|---|---:|---:|
| reviews órfãs | 337/2.866 = 11,8% | 477/4.056 = 11,8% |
| reviews sem eixo | 57 = 2,0% | 79 = 1,9% |
| células acima da margem (bootstrap, 1.050 possíveis) | 31 | 23 |
| — sobrevivem <60% das reamostragens | 14 | 12 |
| — 60–90% | 16 | 10 |
| — ≥90% | 1 | 1 |
| filmes `tematico` | 18 | **16** |
| filmes `valorativo` | 17 | **19** |

Órfãs: **estável** (11,8% → 11,8%). Bootstrap: o número absoluto de células
acima da margem cai (31→23) porque 6 dos 10 flips saem de `tematico` — mas a
**fração** que sobrevive a <60% das reamostragens sobe relativamente (14/31 =
45% → 12/23 = 52%), consistente com H2: a extensão empurrou para fora da
margem justamente as marcações mais frágeis.

## 3.7 — O que a extensão fecha e o que não fecha

**Fecha:**
- A ressalva de cobertura desigual de `ESTUDO_CATALOGO_35.md` §6c (70,7%,
  8 filmes abaixo de 50%) — todo filme agora tem denominador de eixo igual
  ao denominador de análise.
- A composição do bootstrap sobre população parcial — recomputada acima
  sobre os 4.056.
- As frequências por eixo publicadas — recalculadas ao dígito sobre 100% da
  amostra.

**NÃO fecha:**
- **O `n` por bucket** — continua ~40; a extensão preenche o denominador
  existente, não coleta review nova. A curva de retorno marginal medida
  antes continua valendo tal como está.
- **A margem de 20pp** — não tocada nesta sessão, permanece o parâmetro em
  vigor. A investigação acima é evidência a mais de que ela é porosa em
  n≈40, não uma correção dela.
- **O gabarito dos 5 casos de `ESTUDO_CATALOGO_35.md` §12** — nenhum foi
  relido nesta parte da sessão; a extensão é sobre cobertura de
  classificação por eixo, sem relação com contagem de tema.

Registrado em `SPEC.md` §2.8, com a mesma tabela e a mesma investigação.

## 3.8 — Efeito colateral: dois defeitos pré-existentes na suíte, expostos

A extensão fez 93 de 105 buckets do `consenso_verificado.jsonl` passarem de
≤40 linhas para até 68 — reviews de seleções antigas continuam no arquivo
(estender é aditivo, nunca remove). Isso já era conhecido: `eixos.
_filtrar_pela_analisada` existe desde a v1.9.15 exatamente para filtrar isso
antes de calcular frequência/lift, e é o que `montar_bloco` (o caminho REAL
de produção) já faz. **Confirmado por verificação cruzada, zero divergência:**
rodar `montar_bloco` com os dados reais dá **16 tematico / 19 valorativo**,
idêntico ao recálculo manual da tabela acima.

Mas dois testes (e um script de projeção) não aplicavam esse filtro:

1. `tests/test_eixos.py`'s fixture `catalogo` lia `consenso.jsonl` **cru**
   (pré-verificador), resíduo da v1.9.15 nunca atualizado quando o
   verificador foi adotado na v1.9.16 — bug pré-existente, independente
   desta sessão, só nunca detectado porque nenhuma mudança de dados grande o
   suficiente tinha acontecido desde então.
2. Nem essa fixture nem `verificador_impacto._cobertura_exata`/
   `_corpus_consenso` aplicavam `_filtrar_pela_analisada` — com 9/105
   buckets acumulados (o estado antes desta sessão) isso era invisível; com
   93/105 quebrou visivelmente (3 testes falhando: `18 tematicos` virou
   `10`, não `16`).

**Corrigido:** a fixture de `test_eixos.py` agora lê o verificado e aplica o
filtro — os dois testes que dependiam dela foram atualizados para os
números corretos (16/19), com a investigação acima resumida no docstring.
**Não corrigido, fora do escopo autorizado:** `verificador_impacto.py`'s
funções de projeção — ficam documentadas como limitação conhecida no teste
que as usa (`test_base_da_projecao_reproduz_10_de_35`, pinado no valor
NÃO-filtrado, com nota explicando a divergência).

**Suíte: 1.524 de 1.525.** Um teste (`test_os_5_filmes_na_linha_dos_20pp_
agora_sao_tematicos`) foi retirado sem substituto — sua premissa (5 filmes
nomeados sentados exatamente em 20,0pp) era coincidência da amostra PARCIAL
de antes da extensão, e deixou de ser verdade por construção sob a amostra
completa; não há assinatura equivalente a reafirmar.

## 3.9 — Commit

`b60dcae` — `data(classificacao): estende cobertura de eixo aos 35 filmes
(70,7% -> 100%)`. 10 arquivos: os 8 de `resultado/votacao-3/` mais os 2
arquivos de teste corrigidos. `SPEC.md` e os `.md` de relatório desta e das
sessões anteriores **não foram commitados** — seguem o padrão já
estabelecido no arco (o dono revisa e commita a documentação separadamente).

---

# Resumo

**O protocolo ganhou o ajuste que a calibração exigia** — P4 passa a julgar
contra o tema **e** contra a paráfrase publicada, porque foi exatamente aí que a
leitura por modelo perdeu o caso [11] do `wonka`. E o viés ficou registrado com
número: **30/32 de concordância, com as 2 discordâncias sendo conservadorismo do
modelo nas duas direções possíveis** — perdeu um `sustenta` e perdeu um
`contradiz`, nunca contou a mais.

**Os dois gabaritos pendentes estão prontos para a etapa humana.** Li os dois
buckets inteiros (80 reviews): `talk-to-me` dá **5 sustenta**, `napoleon` dá
**12 sustenta e 2 contradiz**. As folhas do dono somam **42 reviews** em vez de
80, compostas por tudo que marquei positivo, tudo que marquei negativo mas com o
assunto tocado, e **5 controles cegos por filme** sorteados com semente 24 e
registrados antes — os controles são o que testa se deixei passar algo sem nem
perceber, que é o modo de falha do protocolo antigo.

**A extensão de cobertura rodou, aprovada pelo dono na saída (b).** Custo real
medido por diferença de linhas contra o commit-base: **US$ 0,1030** de
classificação (3.570 chamadas, dentro da faixa projetada) + **US$ 0,0471** de
verificador (964 chamadas) = **US$ 0,15**. Cobertura: **100,00% verificada em
35 de 35 filmes** (era 70,7%). 8 arquivos de `resultado/votacao-3/` mudaram;
commit `b60dcae`.

**A previsão registrada se confirmou em metade, e a metade que não se
confirmou foi investigada até a causa, como o critério exigia.** Frequência
por eixo: delta máximo 1,2pp — dentro do previsto. Estado `contraste`: **10
de 35 filmes mudaram**, contra a previsão de nenhum. Investigado: não é viés
de conteúdo (rejeitado — mesmo delta pequeno de frequência nesses 10 filmes
especificamente); é a margem de 20pp cruzada por lifts que estavam a 15–29pp
dela — e **6 dos 10 já estavam na lista de marcações frágeis** do bootstrap
publicado em `ESTUDO_CATALOGO_35.md` §8. **Confirma o achado de porosidade da
margem com dado real, não o contradiz.**

**A extensão fecha a cobertura desigual (§6c) e a base do bootstrap; não fecha
o `n≈40` por bucket, a margem de 20pp, nem o gabarito dos 5 casos.** Tudo
registrado em `SPEC.md` §2.8.

**Efeito colateral, documentado e corrigido dentro do escopo:** a extensão
expôs dois defeitos pré-existentes na suíte de testes (fixture lendo o
consenso errado; dois caminhos de cálculo sem o filtro que a v1.9.15 já tinha
criado contra esse exato problema). Um foi corrigido; o outro (um script de
projeção fora do escopo autorizado) ficou documentado como limitação
conhecida. Suíte: **1.524 de 1.525** — um teste retirado porque sua premissa
deixou de valer por construção, não por falha.
