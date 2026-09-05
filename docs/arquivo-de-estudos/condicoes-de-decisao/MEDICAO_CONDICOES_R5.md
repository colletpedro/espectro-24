# CONDIÇÕES DE DECISÃO — rodada 5: as quatro decisões, e o texto final

**Nada publicado.** `git status resultado/` **sem diff**, frontend intocado,
nenhum filme regerado, **seleção de temas, taxonomia, `taxonomia_id`, lei de
margem, cota e piso intocados**. **Suíte: 1.634 → 1.643** (9 testes novos,
nenhum quebrado).

Anteriores: [rodada 1](MEDICAO_CONDICOES_DE_DECISAO.md) ·
[rodada 2](MEDICAO_CONDICOES_R2.md) · [rodada 3](MEDICAO_CONDICOES_R3.md) ·
[rodada 4](MEDICAO_CONDICOES_R4.md).

**Convenção:** **MEDIDO** = número de código rodado nesta sessão ou de
documento anterior citado com a fonte. **VISTO** = leitura, julgamento.

---
---

# A contradição que a Decisão 2 expôs, e ela explica a rodada 4

A regra 9b, escrita na rodada 4, dava como exemplo **PREFERÍVEL**:

>     RUIM:       gosta da reviravolta final que muda tudo
>     PREFERÍVEL: busca histórias que **recontextualizam o que veio antes**

**A Decisão 2 proíbe exatamente esse "preferível".** "Recontextualiza o que
veio antes" é a descrição do EFEITO da virada — o que a decisão nova torna
proibido.

**Isto explica, sem desculpar, por que `shutter-island` persistiu na rodada
4:** o modelo produziu *"mudança memorável de perspectiva"*, que é a mesma
família do exemplo que o prompt lhe deu como bom. **O par foi invertido**
nesta rodada, e há teste travando que ele não volte
(`test_o_exemplo_contraditorio_da_rodada_4_foi_removido`).

---
---

# As quatro decisões, aplicadas

| decisão | onde entrou |
|---|---|
| **1 · final ambíguo é permitido** | regra 9c nova: *a ESTRUTURA do final é permitida, o CONTEÚDO não*, com par PERMITIDO/PROIBIDO |
| **2 · reviravolta: nomear sim, efeito não** | regra 9d nova, com o teste operacional (*"se diz O QUE PROCURAR, é spoiler; se diz QUE TIPO DE EXPERIÊNCIA, não é"*) e três exemplos, incluindo a formulação da rodada 4 como PROIBIDA |
| **3 · expectativa/superestimado fica** | regra 9g nova: formular pela RELAÇÃO entre reputação e entrega, nunca pelo estado mental do leitor |
| **4 · `peso_meio`** | `peso_do_meio()`, função pura, no bloco publicado |

**A seleção de temas não foi tocada**, como pedido — inclusive o tema de plot
twist do `shutter-island` continua sendo oferecido ao modelo.

## Decisão 4 — a forma e o limiar, registrados antes

```json
"peso_meio": {"pct": 45, "texto": "~45% das notas ficaram no meio-termo"}
```

**LIMIAR: as duas colunas somam menos de 80% das notas** — enunciado como o
defeito foi medido na rodada 3, e não como proxy sobre o share do meio.

> **A régua tem de ser a do defeito, e a diferença é mensurável.** Escrito
> como `share_meio >= 20`, o critério pegaria **10** filmes, incluindo
> `pearl-2022`, cujas colunas somam **81%** — um filme que o defeito medido
> não inclui. Sobre a soma das colunas, dá exatamente os **9** registrados.
>
> **25 foi considerado e recusado**, e o registro fica porque era o mais
> elegante: é a fronteira inferior da faixa `muitos` do mapa de quantificador,
> que o projeto já reusou uma vez para "não é ruído, é fatia real"
> (`PISO_ASSUNTO_COMPARTILHADO_PCT`, §3[V]). Mas ali `barbie` e `mother-2017`
> ficariam de fora, e os dois somam 78% — ainda enganoso.

**MEDIDO: 9 de 35**, exatamente os registrados.

**O pior caso, `napoleon-2023`:**

```
~45% das notas ficaram no meio-termo — o meio-termo não tem coluna.
┌─ Vale a pena se você...    [~33% das notas]
┌─ Talvez evite se você...   [~22% das notas]
```

**Onde ele NÃO aparece, `the-godfather` (2/5/93):** as colunas somam 95%, e uma
terceira linha dizendo "~5% ficaram no meio" acrescentaria ruído sem informar.

`peso_meio` é função pura sobre `share_real`, **nunca passa pelo modelo**, e o
briefing continua sem algarismo — travado por teste.

---
---

# As quatro previsões registradas antes de rodar — as quatro se confirmaram

| previsão | resultado |
|---|---|
| a abstenção CAI dos 7,6% | **5,4%** ✅ |
| os 4 casos de "final ambíguo" passam a ser legítimos | **4 de 4** ✅ |
| `shutter-island` POS-B: nomeia sem efeito **ou** abstém | **abstém** ✅ |
| os 6 saltos de expectativa voltam a converter | **6 de 6** ✅ |

## Decisão 3 — a categoria voltou inteira

**MEDIDO: 6 de 6.** E todas na formulação honesta, pela relação entre
reputação e entrega:

| filme | condição |
|---|---|
| `the-godfather` | *se frustra quando obras de grande reputação não correspondem a altas expectativas* |
| `parasite-2019` | *se frustra quando obras premiadas e consagradas não correspondem a altas expectativas* |
| `hereditary` | *se decepciona quando filmes de grande repercussão não correspondem a altas expectativas* |
| `interstellar` | *se frustra quando um filme muito elogiado parece superestimado* |
| `longlegs` | *se frustra quando obras cercadas de grande expectativa não correspondem à forte repercussão* |
| `friday-the-13th-2009` | *busca um remake subestimado…* ⚠️ (a única que eu marquei R — ver abaixo) |

## `shutter-island` — o caso nomeado de aceite

**O tema POS-B foi SALTADO. Nenhuma condição sobre a virada foi publicada.**

É um dos dois desfechos que a Decisão 2 declarou aceitáveis, e o inaceitável
não ocorreu — não há nenhuma formulação dizendo que a virada transforma,
recontextualiza ou muda a perspectiva.

> **VISTO, e é a ressalva honesta:** a abstenção é o desfecho **mais
> conservador** dos dois. Ela não prova que o modelo saberia *nomear sem
> descrever o efeito* — prova que ele preferiu não tentar. O filme sai com 4
> condições em vez de 5, e o que ele publica é atmosfera, atuação, ritmo e a
> representação de transtornos psiquiátricos.

---
---

# Medições

| | rodada 4 | **rodada 5** |
|---|---:|---:|
| temas pedidos | 278 | 278 |
| condições publicadas | 257 | **263** |
| **abstenções** | 21 (7,6%) | **15 (5,4%)** |
| descartadas por flag | 3 | 4 |
| flags | `sem_discriminacao` 3 | `exemplo_verbatim` 2 · `sem_discriminacao` 2 |
| fallback total | 0 | **0** |
| J(texto) | 0,356 | **0,358** |
| J(id) | 0,967 | **0,971** (28/35 idênticos) |
| **custo, duas execuções** | US$ 0,694 | **US$ 0,789** |

**Fabricação: 0 de 263.** **Generalização excessiva: 0** — `interstellar`
POS-C continua sem os buracos negros (*"fotografia deslumbrante com
representações grandiosas de paisagens espaciais"*).

## Não-regressão nominal — terceira rodada seguida

| filme | rodada 5 |
|---|---|
| `cidade-de-deus` | *aprecia uma direção dinâmica com visual imersivo e fotografia estilisticamente marcante* |
| `im-still-here-2024` | *valoriza atuações comoventes guiadas por expressões sutis e silêncios expressivos* |
| `perfect-days-2023` | *busca uma experiência meditativa e aceita um ritmo vagaroso e imersivo* |

`im-still-here-2024` voltou **à formulação exata da rodada 3**, que é a frase
de referência. Nenhuma virou preferência abstrata; nenhuma descreve o leitor.

---
---

# A classificação cega — e o que ela achou

Critério atualizado pelas Decisões 1 e 2, aplicado às **263 em ordem
alfabética sem marca de origem**, gravado antes do cruzamento, diff por
script. **Limitação declarada:** conheço os casos anteriores e não posso
desconhecê-los; o procedimento garante uniformidade, não cegueira.

**Resultado: 1 flag de spoiler em 263 (0,4%)**, contra 5 em 257 (1,9%) na
rodada 4.

## A única, e é uma REGRESSÃO

`dune-part-two` POS-C:

| | |
|---|---|
| rodada 4 | *se interessa por sagas épicas focadas na **profunda transformação do protagonista*** |
| rodada 5 | *se interessa pela transformação gradual de um jovem relutante em **figura messiânica*** |

Nomeia o **ponto de chegada do arco**. **Nem a Decisão 1 nem a Decisão 2
legalizam isso** — a regra 9 continua listando "ponto de chegada de arco", e a
rodada 4 já tinha resolvido este caso.

> **VISTO, e não consigo distinguir duas hipóteses com uma execução:** ou
> afrouxar três regras de spoiler de uma vez baixou a guarda geral do modelo,
> ou é variação entre execuções. **Registro como o custo plausível das
> decisões 1–3** — liberar categorias é barato de escrever e não é neutro no
> resultado.

## E uma segunda, de formulação, não de spoiler

`friday-the-13th-2009` POS-B: *"busca um **remake subestimado** que se destaca
frente a outras sequências"*. Ninguém procura um filme *subestimado* — procura
um bom filme. A condição adotou o rótulo do tema como se fosse a preferência
do leitor. **A formulação certa existe no mesmo lote** (`the-godfather`), pela
relação entre reputação e entrega.

---
---

# Entregáveis

| arquivo | o que é |
|---|---|
| `FOLHA_LEITURA_CONDICOES_35.md` | **263 condições, texto final**, ordem de prioridade, acumulado por filme, `peso_meio` no cabeçalho dos 9 filmes. Zero opinião minha, zero flags |
| `LEITURA_CONDICOES_NAO_ABRIR_ANTES.md` | a minha leitura: **261 A / 2 R / 0 C** |
| `scripts/comparar_condicoes.py` | concordância, matriz 3×3, divergências com motivo, e a regra impressa: **onde há divergência, o veredito do dono vale** |

O comparador foi testado ponta a ponta contra a folha nova (263 lidas, matriz
correta, 2 divergências simuladas detectadas) e contra a folha real em branco,
onde devolve *"nada a comparar ainda"* em vez de inventar concordância.

**Tempo de leitura estimado: ~132 min** (30 s por condição). Parando no filme
3 são 13 min e cobrem os casos de aceite; no filme 19, ~70 min e cobrem tudo
onde as razões da reprovação original viviam.

---

## Limite, e o que vem depois

**35 filmes, 2 execuções, 263 condições, e a classificação é uma leitura
minha** — a que a sua existe para julgar. Com 0 fabricações em 263, o limite
superior de 95% é **~1,1%**.

**Este foi o último ajuste por regra.** O que mudar daqui em diante muda pela
sua leitura. As duas que eu marquei (`dune-part-two`, `friday-the-13th-2009`)
são candidatas a reescrita pontual, não a regra nova — e regra nova, a esta
altura, tem custo demonstrado: as decisões 1–3 resolveram quatro casos e
plausivelmente causaram um.

**Aprovação de código não é aprovação editorial.** A pergunta do portão
seguinte é a que nenhum número acima responde: *vendo estas condições como
página, a impressão é fiel à recepção e útil para decidir?*

## Reprodução

```bash
python scripts/gerar_condicoes.py --todos --saida <dir-fora-de-resultado>
python scripts/comparar_condicoes.py --folha FOLHA_LEITURA_CONDICOES_35.md \
    --modelo minha_leitura.json --mapa mapa_condicoes.json
```

Estágio em `src/espectro24/condicoes.py`, **51 testes** em
`tests/test_condicoes.py`. Execuções, registro prévio, classificação cega e
mapa no scratchpad da sessão.
