# CONDIÇÕES DE DECISÃO — rodada 3: o estágio construído, os 35 gerados, a leitura montada

**Nada foi publicado.** `git status resultado/` **sem diff**, nenhum filme
regerado, veredito e narrativa intocados, frontend intocado, taxonomia,
`taxonomia_id`, lei de margem, cota e piso intocados. **Suíte: 1.591 antes →
1.626 depois** (35 testes novos, nenhum quebrado).

Documentos anteriores: [DESENHO_CONDICOES_DE_DECISAO.md](DESENHO_CONDICOES_DE_DECISAO.md),
[MEDICAO_CONDICOES_DE_DECISAO.md](MEDICAO_CONDICOES_DE_DECISAO.md) (rodada 1)
e [MEDICAO_CONDICOES_R2.md](MEDICAO_CONDICOES_R2.md) (rodada 2).

**Convenção:** **MEDIDO** = número que saiu de código rodado nesta sessão ou
de documento anterior citado com a fonte. **VISTO** = leitura, julgamento.

---
---

# ENTREGA 0 — o delta de §0, aplicado antes do código

**MEDIDO: +83 linhas, 0 linhas alteradas ou removidas.** O parágrafo entra
depois da exceção da lei por `n` e antes de "Objetivo", no mesmo estatuto das
duas exceções deliberadas já registradas. Nenhuma frase existente do §0 foi
editada — a exceção diz o que deixa de valer, sem apagar o texto que passa a
ter escopo reduzido.

O que ele registra, nas cinco partes pedidas:

| parte | o que ficou escrito |
|---|---|
| **o que muda** | a frase do §3[V] — *"não é crítica, não é resenha, **não é recomendação**"* — continua valendo **do veredito** e deixa de valer **do bloco de condições**, que é recomendação condicional por construção. É mudança de NATUREZA, não extensão |
| **a razão** | o público-alvo declarado no próprio §0 é quem ainda não assistiu e está decidindo, e **relato neutro que não ajuda a decidir falha com o público que o parágrafo nomeia**. Mais o argumento medido: em `hereditary` o veredito não menciona *Atuações* (20/40) nem *Atmosfera e tensão* (15/40), os dois temas mais citados do grupo que é 80% da recepção |
| **o que sustenta** | as três garantias, nenhuma opcional: proveniência visível, seleção de tema em CÓDIGO, leitura humana de 100% |
| **o que NÃO muda** | lista fechada: nenhuma nota/score/estrela; zero algarismo escrito pelo modelo; quantidade é do código; anti-spoiler; neutralidade estrutural (cota 40/40/40, margem, bullets, espaço) |
| **reversão** | o veredito continua existindo **e sendo gerado**; reverter é trocar o que a página renderiza, não reprocessar corpus |

E a **FASE 1 — COEXISTÊNCIA** ficou registrada com as duas razões de
arquitetura e a pergunta em aberto (se as condições substituem o veredito, e
sob que critério).

---
---

# ENTREGA 1 — as correções, em código

`src/espectro24/condicoes.py` · `scripts/gerar_condicoes.py` ·
`tests/test_condicoes.py` (35 testes) · registro do estágio em `config.py`.

## 1a · ordenação das colunas por `share_real` — herdada da v1.9.30

`ordem_das_colunas()`, com o desempate pela ordem canônica **explícito** e
não como efeito colateral do `sort`. **MEDIDO nos 35: 32 filmes abrem por
"Vale a pena", 3 por "Talvez evite"** (`cats-2019`, `joker-folie-a-deux`,
`friday-the-13th-2009`).

## 1b · prefixo de peso por lado — o conserto da razão nº 1

Dois elementos, os dois escritos em CÓDIGO, nenhum passando pelo modelo:

- **`peso_texto`** — `~<share_real>% das notas`;
- **`nota_de_amostra`** — `"amostra pequena"` quando o bucket está em
  `modo: reduzido` ou `estado_piso != completa`.

`the-godfather` sai assim:

```
┌─ Vale a pena se você...    [~93% das notas]
┌─ Talvez evite se você...   [~2% das notas · amostra pequena]
```

**Por que o percentual, e não um adjetivo:** é a forma que o §3[V] já usa em
`prefixo_de_codigo`. **Por que ele pode ser publicado mesmo em bucket de
piso:** §3[C3] é explícito — *"o peso vem do histograma de NOTAS e NÃO
depende de haver review com texto… suprimi-lo reintroduziria a infidelidade
por omissão que a v1.4.0 corrigiu"*. O piso suprime o **quantificador**,
nunca o peso. **MEDIDO: `obsession-2026` (n = 5/6/8) publica os dois
percentuais e tem `rotulo_forca` `null` nas seis condições.**

**`nota_de_amostra` aparece em 7 colunas de 5 filmes** — é a ressalva que a
rodada 2 registrou como ausente (*"o veredito carrega o 'numa amostra
pequena' e as condições não"*).

## 1c · par obrigatório como DEFAULT

`selecionar(..., par_obrigatorio=True)`. Calculado **uma vez** sobre a
seleção base, nunca em cascata; **acrescenta, nunca substitui** (precedente
literal do §2.5: *"o número de entradas é informação, não defeito de
preenchimento"*). Teto de 6 por lado.

## 1d · o validador de corroboração por valência foi REMOVIDO

**MEDIDO na rodada 2: precisão de 7,7%** — 12 de 13 "conflitos" eram erro do
léxico, com 2 falsos positivos em 196 condições e **zero** verdadeiros. É o
mesmo modo de falha que o §3[V] corrigiu removendo `incomod*`: palavra
avaliativa em uso META (*"Crítica à idolatria do Coringa"*, onde o filme **é**
a crítica) quebra o léxico.

**No lugar entra `ancora_de_outro_bucket`** — cada lado só cita temas do seu
bucket. Exato, sem léxico, zero falso positivo por construção.

> **Consequência declarada: o validador 2 encolheu.** Ele deixou de ter duas
> metades e é só a DISCRIMINAÇÃO. O resíduo — um tema que é ele próprio uma
> queixa dentro do bucket positivo — continua indetectável por máquina, e
> **apareceu na leitura**: `friday-the-13th-2009` POS-E (§Entrega 3).

## 1e · exceção de nome próprio no `tema_verbatim`

`palavras_copiaveis()` exclui tokens Capitalizados fora da primeira posição.
`Descaracterização do Arthur Fleck` → 1 palavra copiável → regra desligada;
`Ritmo lento e contemplativo` → 3 → **continua ligada**. A fronteira é
tipográfica porque o dado a carrega — mesma família da correção de fronteira
da v1.9.22.

## 1f · `rotulo_forca` entra, com a supressão de §3[C3]

Presente em cada condição, `null` nos estados de piso.

## O guard-rail que reprovou, e devia

`tests/test_provider_por_estagio.py` **falhou** quando o estágio foi
registrado em `config.py` — a lista de estágios é literal de propósito, e o
comentário dela diz que *"um estágio novo aparecendo aqui sem decisão
registrada é exatamente o que este teste existe para expor"*. A decisão
estava registrada (§0 + `config.py`), então a lista foi atualizada citando o
registro. **O teste funcionou como projetado e isso fica anotado, não
escondido.**

## Uma decisão de desenho que vale registro: não existe template de fallback

Um template de condição seria *"vale a pena se você gosta de X"* sobre o
rótulo do eixo — a frase vazia que a v1.9.21 gastou uma versão inteira para
matar. Quando nada limpo sobra, o bloco sai com o que sobreviveu (podendo ser
nada) e `origem: "abstencao"`. **A rede deste estágio é o VEREDITO**, que
continua sendo gerado e renderizado ao lado.

E o harness **recusa** `--saida` dentro de `resultado/`, com mensagem que
cita o §0. Enquanto a fase de leitura estiver aberta, ele **não sabe**
publicar.

---
---

# ENTREGA 2 — os 35, duas execuções

**MEDIDO** (`BEST_OF_N` = 3, `gemini-3.7-flash`):

| | execução 1 | execução 2 |
|---|---:|---:|
| temas pedidos pelo código | 278 | 278 |
| condições publicadas | **266** | 269 |
| condições descartadas por flag | 6 | 3 |
| filmes que precisaram de retry | 10 | 14 |
| filmes em fallback total | **0** | 0 |
| chamadas | 115 | 119 |
| **custo** | **US$ 0,271** | US$ 0,276 |
| latência total | 670 s | 709 s |

**Custo por filme: US$ 0,0077.** Projeção para 300 filmes: **US$ 2,32**.

**Flags das descartadas (exec 1):** `exemplo_verbatim` 5, `sem_discriminacao`
1. Nenhuma `digito`, nenhuma `quantidade_escrita`, nenhuma `ancora_*`.

**Abstenções — 12 temas pedidos sem condição publicada (4,3%).** O estágio
saltou, entre outros: `the-godfather`/*Apreço pela atuação de Al Pacino*,
`hereditary`/*Atuações (elogio a Toni Collette)*, `perfect-days`/*Elogios a
fotografia e trilha sonora* — **três temas de ELOGIO dentro do bucket
negativo**, dos quais nenhuma condição "talvez evite" honesta se deriva.

**Reprodutibilidade:**

| | valor |
|---|---:|
| Jaccard sobre o TEXTO (palavras de conteúdo) | **0,379** |
| Jaccard sobre `(lado, tema_origem)` | 0,965 |
| filmes com seleção idêntica | 28 de 35 |

O 0,965 **não é o critério** — isso ficou registrado antes de gerar, porque a
seleção em código torna a métrica de id quase tautológica. **E o que ela
mede, ela mede:** os 7 filmes abaixo de 1,000 divergem porque a **abstenção**
varia entre execuções, não a seleção. A seleção é determinística; o que o
modelo salta, não é.

---
---

# ENTREGA 3 — a leitura humana de 100%

## A folha, e o número que o briefing pediu antes

**`FOLHA_LEITURA_CONDICOES_35.md` — 266 condições, 35 filmes.**

Cada uma traz: o texto, o `tema` de origem, o `exemplo_parafraseado`
**completo** (P4 REVISADO — a valência mora na paráfrase), o `rotulo_forca`,
e o `~n% das notas` da coluna. Caixa `[ ]` para **A / R / C**.

**Zero indicação da minha opinião, e as flags mecânicas ficam FORA dela.**

**Tempo estimado: ~133 min (30 s por condição, incluindo ler o tema e a
paráfrase). Passa dos ~250 que o briefing fixou como gatilho de corte.**

### O corte que eu tentei, e que NÃO funciona — reportado como falha

Testei o corte por risco: condição cujo tema tem irmão de mesmo assunto em
outro bucket (a família `napoleon`/batalhas), **ou** cuja paráfrase tem
ressalva (*mas*, *embora*, *apesar* — a família `cats`/POS-C), **ou** que está
no lado minoritário de um filme com ≥80pp de desequilíbrio (a família
`the-godfather`).

**MEDIDO: 247 de 266 condições (93%) caem em pelo menos um critério.** O
corte remove 19 condições e economiza 9 minutos. **Ele não serve**, e a razão
é estrutural: **28 dos 35 filmes são `valorativo`**, o que significa, por
definição, que os grupos falam das mesmas coisas — então quase todo tema tem
irmão em outro bucket.

### O corte que eu proponho no lugar: ORDEM DE PRIORIDADE, sem remover nada

A folha está ordenada por prioridade, com o **acumulado no cabeçalho de cada
filme**, para que parar no meio seja uma decisão informada:

| parar em | filmes | condições | tempo | cobertura |
|---|---:|---:|---:|---|
| filme 3 | 3 | 26 | ~13 min | os três **casos de aceite** (`the-godfather`, `cats-2019`, `napoleon-2023`) |
| filme 15 | 15 | 108 | ~54 min | + todos os de **desequilíbrio extremo** (≥85pp) — onde mora a razão nº 1 |
| filme 19 | 19 | 140 | ~70 min | + todos os de **amostra reduzida** |
| filme 27 | 27 | 203 | ~101 min | + todos os de desequilíbrio alto (≥70pp) |
| **filme 35** | **35** | **266** | **~133 min** | **população inteira** |

**A decisão é sua.** O que eu recomendo, e é recomendação e não medição:
**ler até o filme 19 (~70 min) fecha os três casos de aceite e todos os
filmes onde as duas razões da reprovação original vivem.** Os 16 restantes
são os mais equilibrados, que é onde o formato tem menos como errar.

## A minha leitura, e o achado que ela produziu

`LEITURA_CONDICOES_NAO_ABRIR_ANTES.md`, com o aviso no nome.

| veredito | n | % |
|---|---:|---:|
| **A** aprovada | 259 | 97,4% |
| **R** reescrever | **7** | 2,6% |
| **C** cortar | **0** | 0% |

**Zero fabricações.** Em todas as 266 há frase no `exemplo_parafraseado` que
sustenta o que a condição afirma.

### **CINCO DAS SETE SÃO ANTI-SPOILER, e o portão não tinha essa linha**

Este é o achado da sessão, e ele só aparece em leitura de população inteira:
nenhum dos cinco casos estava nos 4 filmes da rodada 1 nem nos 10 da
rodada 2.

**O mecanismo é do FORMATO, não do modelo.** §3[D] filtrou os TEMAS para
spoiler, mas a condição **repondera** o tema:

> um bullet que diz *"Monólogo final"* **descreve o que as pessoas
> comentaram**; uma condição que diz *"vale a pena se você espera um monólogo
> final devastador"* **é uma instrução sobre o que aguardar**. O conteúdo é o
> mesmo; a força ilocucionária não é.

| filme | condição | o problema |
|---|---|---|
| `pearl-2022` | *espera um monólogo final devastador carregado de fúria e vulnerabilidade* | recomenda o filme PELO desfecho |
| `avengers-endgame` | *busca um encerramento marcante com despedidas emocionantes de personagens queridos* | informa que personagens saem |
| `shutter-island` | *gosta de reviravoltas marcantes que transformam a história* | anuncia a reviravolta que recontextualiza — neste filme, o único spoiler que importa |
| `dune-part-two` | *busca acompanhar a transformação épica de Paul até se tornar uma liderança messiânica* | enuncia o ponto de chegada do arco |
| `friday-the-13th-2009` | *busca diversão escrachada, mesmo tolerando o exagero nas cenas de nudez* | tema de QUEIXA no bucket positivo lido como endosso — é o resíduo que a remoção do validador 2b declarou indetectável, e ele apareceu |

As outras duas:

| filme | condição | o problema |
|---|---|---|
| `obsession-2026` | *se frustra com produções que exibem falhas e apenas potencial não realizado* | a paráfrase é **generosa** (*"apesar das falhas, há indícios de talento… considerando a baixa experiência e orçamento"*) e a condição a converte em advertência |
| `interstellar` | *busca a beleza visual de cenários espaciais e recriações de buracos negros* | **previsto e previsível**: é o único dos 5 casos de generalização excessiva do §10 que a regra top-3 seleciona, e §10 mediu que a especificidade do buraco negro *"foi acrescentada invertendo o sinal da única evidência disponível"* |

### O que eu NÃO marquei, declarado para que a comparação seja justa

Todas as condições que carregam **as duas metades** de uma paráfrase com
ressalva ficaram **A**: `wicked-2024` POS-D (*"relevando momentos de
iluminação acinzentada"*), `oppenheimer-2023` POS-E, `the-hateful-eight`
POS-E, `wonka` POS-B, `hereditary` POS-D. Era o defeito da rodada 2 e a
regra 5 nova do prompt o endereçou. **É o ponto mais provável de divergência
entre nós.**

E `cats-2019` POS-C ficou **A** — mudei de opinião em relação à rodada 2,
porque a condição agora carrega *"perturbadores"*, a metade que a versão
anterior calava.

## O comparador

`scripts/comparar_condicoes.py`, no padrão de `comparar_gabarito.py`:
concordância, matriz 3×3, lista de divergências com o motivo do modelo, e a
regra impressa no fim — **onde há divergência, o veredito do dono vale**.

**Caixa em branco é "não lida", nunca "aprovada por omissão"** — mesma regra
do piso de §2.5 (*ausência significa "não medido"*).

Testado ponta a ponta com uma folha simulada: 266 lidas, matriz correta, 3
divergências detectadas e explicadas. Rodado contra a folha real (em branco),
devolve *"nada a comparar ainda"* em vez de inventar concordância.

---
---

# ENTREGA 4 — o portão, contra o resultado

| critério | corte fixado ANTES | medido | veredito |
|---|---|---|---|
| **D1** fabricação | **ZERO** | **0 de 266** | ✅ |
| **D2** generalização excessiva, estrita | ≤ 5% | **0,4%** (1: `interstellar`) | ✅ |
| **D2** estendida | ≤ 8% | **0,8%** (2: + `obsession-2026`) | ✅ |
| **D3** peso: `the-godfather` e `cats-2019` | leitura do dono | **estrutura correta; a impressão é decisão sua** | ⏳ |
| **D4** `napoleon`/batalhas | objeção tática na página | **presente** | ✅ |
| **D5** reprodutibilidade | sem corte, por registro | J(texto) 0,379 | — |
| *(não estava no portão)* | — | **anti-spoiler: 5 de 266 = 1,9%** | ⚠️ |

## D4 — passa, e o texto é quase o que a auditoria manual escreveu à mão

```
┌─ Vale a pena se você...   [~33% das notas]
│  gosta de combates brutais e espetaculares sequências de batalha de Ridley Scott
│      (alguns) ← Qualidade das cenas de batalha
┌─ Talvez evite se você...  [~22% das notas]
│  espera tática e estratégia militar em batalhas, além do puro impacto visual
│      (alguns) ← Batalhas decepcionantes
```

A auditoria manual da rodada 1 propôs *"quer batalha com tática, não só
espetáculo"*. O estágio escreveu *"espera tática e estratégia militar em
batalhas, além do puro impacto visual"*. **O leitor vê as duas leituras.**

E a distinção da rodada 2 continua valendo: **o validador de discriminação
continua não pegando a condição POS-C** — o proxy é lexical e o defeito é
semântico. **O que fecha o caso é o par obrigatório, não um validador.**

## D3 — a estrutura está correta; falta a sua leitura

```
THE-GODFATHER (2/5/93)          CATS-2019 (86/7/7)
┌─ Vale a pena  [~93%]          ┌─ Talvez evite  [~86%]
┌─ Talvez evite [~2% ·          ┌─ Vale a pena   [~7%]
   amostra pequena]
```

A coluna do grupo maior vem primeiro, os dois percentuais estão na tela, e a
coluna minoritária **não foi encolhida** — `the-godfather` publica três
condições de quem não recomenda, com `~2% das notas` ao lado.

### O resíduo de 1b que a medição encontrou, e ele é novo

**MEDIDO: em 9 dos 35 filmes as duas colunas somam menos de 80%**, porque o
meio-termo não tem coluna:

| filme | vale | evite | falta (o meio) |
|---|---:|---:|---:|
| `napoleon-2023` | 33% | 22% | **45%** |
| `friday-the-13th-2009` | 26% | 33% | 41% |
| `wonka` | 50% | 15% | 35% |
| `joker-folie-a-deux` | 21% | 46% | 33% |
| `longlegs` | 57% | 13% | 30% |
| `obsession-2026` | 55% | 16% | 29% |
| `talk-to-me-2022` | 67% | 8% | 25% |
| `barbie` | 70% | 8% | 22% |
| `mother-2017` | 64% | 14% | 22% |

**1b conserta a proporção RELATIVA entre as duas colunas — que era a razão
nº 1 — e deixa a leitura ABSOLUTA incompleta em 9 filmes.** Em 2 deles
(`napoleon`, `friday`) o veredito ao lado cobre, porque o meio é dominante e
o `prefixo_de_codigo` o anuncia. **Nos outros 7, nada cobre.**

**Proposto, NÃO implementado:** um terceiro elemento de código no bloco —
`peso_meio` — dizendo a fatia do meio quando ela passa de um limiar. É uma
função pura sobre `share_real`, e a decisão de forma é sua.

---
---

# A pergunta do briefing: a razão nº 1 fechou?

**PARCIALMENTE. Ela era a única aberta desde a rodada 1, e saiu desta rodada
menor, não morta.**

**O que fechou, e está medido:**

- a **proporção entre as duas colunas** está na tela em 35 de 35 filmes, e a
  ordem por peso põe o grupo maior primeiro em 35 de 35;
- a **ressalva de amostra** que só o veredito carregava aparece em 7 colunas
  de 5 filmes;
- `rotulo_forca` — que a rodada 2 mediu como **incapaz** de fechar isto (18 de
  35 filmes com o rótulo do minoritário igual ou mais forte que o do
  majoritário) — está lá para o que ele **pode** fazer, que é a força dentro
  da coluna;
- e **a coluna minoritária não foi encolhida**, então o conserto não custou a
  invariante 2 do §0.

**O que continua aberto, e são duas coisas:**

1. **A leitura absoluta em 9 de 35 filmes** (o meio sem coluna, acima).
   Medido nesta sessão, não previsto no portão.
2. **A pergunta que nenhum número responde: um leitor sai com a impressão
   certa?** Não existe medida de impressão sem gente. `the-godfather` e
   `cats-2019` estão nos três primeiros filmes da folha, e **13 minutos de
   leitura decidem isso**.

**Se, lendo a folha, você disser que a impressão de proporção continua
errada, a razão nº 1 continua aberta e isso reprova a entrega** — foi assim
que o portão registrou D3 antes de gerar, e é assim que ele vale agora.

---

## O que fica pendente, em ordem

1. **A sua leitura** (~70 min até o filme 19, ~133 min completa) e o
   comparador. Nada é publicado antes disso.
2. **As 7 que eu marquei R** — 5 são anti-spoiler e sugerem uma **regra 13 no
   prompt**: *é proibido apontar o desfecho, a reviravolta ou o final como
   motivo para assistir, mesmo que o tema os nomeie*. Proposta, não escrita.
3. **`peso_meio`** para os 9 filmes de §D3.
4. **O leiaute da FASE 1**, não implementado nesta sessão. Ordem proposta:
   **barra de proporção → condições → veredito → bullets**. As condições
   logo abaixo da barra, porque a barra é o contexto de peso que elas
   pressupõem; o veredito depois, porque ele carrega o quantificador em prosa;
   os bullets por último, como a evidência que sustenta as duas.
5. **A pergunta em aberto do §0:** se as condições substituem o veredito, e
   sob que critério.

## Limite

**35 filmes, 2 execuções, 266 condições, e a classificação de fidelidade é
uma leitura minha — que é exatamente a que a leitura do dono existe para
julgar.** Com 0 fabricações em 266, o limite superior de 95% é **~1,1%**, o
melhor das três rodadas, e ainda não é "zero fabricação". A amostra agora é a
**população** dos 35 publicados, então o que se mede vale para eles; nada
disso vale para filmes fora do catálogo, pela mesma razão que a §2.5 registra
para a lei da margem.

## Reprodução

O estágio está em `src/`, o harness em `scripts/`, os testes em `tests/`. As
duas execuções (`r3/exec1`, `r3/exec2`), o portão registrado
(`PORTAO_R3.md`), o mapa de casamento e a folha simulada de teste do
comparador vivem no scratchpad da sessão. Comando:

```bash
python scripts/gerar_condicoes.py --todos --saida <dir-fora-de-resultado>
```
