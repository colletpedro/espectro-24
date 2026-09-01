# Desenho da classificação v2 — eixos, polaridade e Feelings

**Entrega 2. Este documento é uma PROPOSTA para aprovação, não uma
implementação.** Nenhum classificador foi escrito, nenhum corpus
reclassificado, `taxonomia.py` e o `taxonomia_id` `ebab2667de74` estão
intactos, nada em `resultado/` foi tocado. A medição que sustenta as decisões
está no documento irmão, `MEDICAO_CONTAGEM_E_AB.md`; o insumo é
`ESTUDO_CATALOGO_35.md`.

**Convenção deste documento:** o que está **MEDIDO** traz o número e a fonte;
o que está **PROPOSTO** é decisão de desenho a aprovar; o que está **NÃO
VERIFICADO** é premissa que ainda não foi conferida e está marcada como tal.

---

## Sumário das decisões propostas

| # | decisão | estatuto |
|---|---|---|
| 1 | `roteiro_estrutura` → **3 sub-eixos** (`personagem`, `enredo_desfecho`, `escrita`) | proposto, testado contra 148 temas |
| 2 | **NÃO** dividir `impacto_emocional` — o verificador já resolveu | medido |
| 3 | **NÃO** fundir `ritmo`+`expectativa`, nem `expectativa`+`comparacoes` | medido (fusão refutada) |
| 4 | **Estreitar** `comparacoes`, que é o segundo eixo saturado e ninguém tinha sinalizado | medido |
| 5 | Polaridade **por (review, eixo)**, 4 valores, `misto` de primeira classe | proposto |
| 6 | Feelings: 3 categorias de review + 2 do TMDB, listas fechadas, `feelings_id` próprio | proposto |
| 7 | Sem autoconfiança do modelo; a confiança é a **votação**, com limiar por consumidor | proposto |
| 8 | `plot_twist` entra, como exceção deliberada ao anti-spoiler | decisão do dono, trade-off registrado |

Contagem de eixos: **10 → 12** (+3 do split, −1 pelo `roteiro_estrutura` que
deixa de existir), mais `livre`.

---

# (a) EIXO — resolvendo `roteiro_estrutura`

## O diagnóstico, com o número que decide

O estudo mostrou a saturação no nível dos **bullets** (25% de todos, 35 de 35
filmes). O que fecha o caso é o nível de **review**, que é o que alimenta o
lift — medido sobre as 2.866 reviews classificadas da seleção de produção:

| eixo | % das reviews | negativas | medianas | positivas | **amplitude** |
|---|---:|---:|---:|---:|---:|
| **`roteiro_estrutura`** | **55,5%** | 55,3% | 58,2% | 53,0% | **5,2 pp** |
| `comparacoes` | 36,4% | 35,7% | 34,9% | 38,8% | 3,9 pp |
| `impacto_emocional` | 34,6% | 33,8% | 30,0% | 40,3% | 10,3 pp |
| `direcao_imagem` | 30,4% | 26,8% | 33,7% | 30,8% | 7,0 pp |
| **`ritmo`** | 29,1% | 36,0% | 31,0% | 19,6% | **16,5 pp** |
| `atuacao` | 27,9% | 24,9% | 30,7% | 28,5% | 5,8 pp |
| `critica_social` | 23,1% | 26,4% | 23,2% | 19,6% | 6,8 pp |
| **`tom_atmosfera`** | 22,0% | 15,5% | 21,0% | 30,1% | **14,5 pp** |
| `expectativa` | 19,9% | 22,3% | 20,9% | 16,3% | 6,0 pp |
| `som_trilha` | 12,7% | 10,7% | 12,7% | 15,0% | 4,2 pp |
| `livre` | 9,1% | 8,6% | 9,6% | 9,1% | 1,0 pp |

**`roteiro_estrutura` aparece em 56% das reviews com 5,2pp de amplitude entre
os três grupos.** Está acima de 50% em **63 dos 105 buckets** e acima de 70% em
**21**. Um eixo assim não pode produzir 20pp de lift em lugar nenhum — a
impossibilidade é aritmética, não estatística.

Duas descobertas colaterais que mudam o escopo desta entrega:

**MEDIDO — `impacto_emocional` já foi resolvido, e a spec está desatualizada
nesse ponto.** §2.5 registra 75,5% de saturação e diz que existe *"uma correção
que funcionou e que NÃO foi aplicada"* (o passe `V2_alvo`). **Ela foi
aplicada**, na v1.9.16, e o consenso de produção é o verificado:

| | `consenso.jsonl` (cru) | `consenso_verificado.jsonl` (produção) |
|---|---:|---:|
| `impacto_emocional` no corpus (n=4.181) | **75,6%** | **36,1%** |
| na seleção de produção (n=2.866) | 75,6% | **34,6%** |
| eixos por review | 3,42 | 3,01 |
| reviews sem nenhum eixo | 0,2% | 2,0% |

A projeção de de-saturação registrada no consolidado (75,5% → 35,7%) **acertou
dentro de 1pp**. O texto de §2.5 que trata a correção como pendente descreve um
estado que não é mais o atual — correção de registro, não mudança de
comportamento.

**MEDIDO — `comparacoes` é o segundo eixo saturado, e não estava sinalizado.**
36,4% das reviews, 3,9pp de amplitude, acima de 50% em 20 buckets e de 70% em 7.
E a assimetria mais extrema do catálogo entre o que a classificação vê e o que
a síntese publica:

| eixo | % das reviews | % dos bullets | razão |
|---|---:|---:|---:|
| `comparacoes` | 36,4% | **2,4%** | **0,07** |
| `impacto_emocional` | 34,6% | 6,5% | 0,19 |
| `expectativa` | 19,9% | 4,0% | 0,20 |
| `roteiro_estrutura` | 55,5% | 25,1% | 0,45 |
| `atuacao` | 27,9% | 13,7% | 0,49 |

Um em cada três leitores compara o filme com outra coisa, e isso vira 2% dos
bullets. A causa provável é a definição, que reúne quatro atos diferentes numa
etiqueta só: comparar com outro filme, com o livro, com a franquia e com a obra
anterior do mesmo diretor.

## A divisão proposta — três sub-eixos

**PROPOSTO.** `roteiro_estrutura` sai da taxonomia e é substituído por:

### `personagem`
> As pessoas na tela: quem são, se mudam ao longo do filme, se dá para se
> importar com elas, se as decisões delas fazem sentido, se estão
> desenvolvidas ou subaproveitadas, e o julgamento sobre elas
> (cativantes, irritantes, rasas, complexas). Inclui a relação **entre**
> personagens quando ela é o objeto do comentário. **Não** inclui a
> atuação de quem os interpreta — isso é `atuacao`.

### `enredo_desfecho`
> Se a história se sustenta: lógica interna, furos, se dá para acompanhar,
> confusão, ritmo de entrega da informação, flashback, não-linearidade,
> excesso ou falta de exposição, e **como termina** — desfecho, clímax,
> reviravolta, final aberto ou fechado. **Não** inclui se a ideia de
> partida era boa (isso é `escrita`) nem se o filme é longo demais (isso é
> `ritmo`).

### `escrita`
> O texto e a ideia: os diálogos (naturais ou artificiais, demais ou de
> menos, o estilo de quem escreveu) e a originalidade da premissa
> (previsível, clichê, ambiciosa, "boa ideia mal executada"). **Não**
> inclui a mensagem política ou social do filme — isso é `critica_social`.

### A regra de fronteira, por extenso

Escrita antes do teste e aplicada sem ajuste depois dele:

> **R1 — O OBJETO manda, não o adjetivo.** "Raso", "superficial", "fraco",
> "previsível", "sem profundidade" atacam qualquer coisa e não decidem
> sub-eixo. Decide o **substantivo que o adjetivo modifica**: *"personagens
> rasos"* → `personagem`; *"roteiro raso"* → `escrita`; *"trama rasa"* →
> `enredo_desfecho`.
>
> **R2 — O mais específico ganha do mais geral**, nesta ordem de precedência:
> `personagem` > `escrita` > `enredo_desfecho`. Um tema que toque dois vai
> para o primeiro da lista que ele toca. Razão: `enredo_desfecho` é o
> sub-eixo mais elástico e receberia por padrão tudo que os outros dois
> deixassem passar, reconstruindo a saturação que a divisão existe para
> desfazer.
>
> **R3 — Descrever o ASSUNTO do filme não é eixo.** *"Trama sobre luto e
> solidão"*, *"Família, trauma e aceitação"* dizem do que o filme trata, não
> como ele foi recebido. Vão para **Feelings**, seção (c).
>
> **R4 — Tema que não faz afirmação nenhuma não é problema de taxonomia.**
> *"História"*, *"Roteiro e narrativa"*, *"Vilão"* são bullets vazios, e a
> correção é em §[D], não aqui.
>
> **R5 — Posição do filme numa série é `comparacoes`**, não enredo:
> *"Divisão em duas partes desnecessária"*, *"Filme como mera introdução"*.

## O teste contra os 148 temas reais

Os 148 `tema` distintos que `roteiro_estrutura` produziu no catálogo, passados
por um classificador de palavra-chave que implementa R1–R5. **O classificador é
deliberadamente burro: ele existe para achar onde a fronteira não decide
sozinha, não para ser o classificador de produção.**

**Primeira rodada, sem a regra de precedência** (para medir o que a regra
compra), com uma divisão de cinco sub-eixos:

| | temas |
|---|---:|
| casaram com **uma** regra | 108 (73%) |
| **ambíguos** (mais de uma) | 18 (12%) |
| **órfãos** (nenhuma) | 22 (15%) |

**Segunda rodada, com R1–R5 aplicadas:**

| destino | temas | % |
|---|---:|---:|
| resolvidos num sub-eixo | **125** | 84% |
| → para `comparacoes` (R5) | 4 | 3% |
| → para Feelings (R3) | 6 | 4% |
| → bullets vazios (R4) | 11 | 7% |
| **sem regra (resíduo real)** | **1** | **0,7%** |

*(Uma correção de honestidade: o classificador de palavra-chave mandou
"Trama sobrenatural e final insatisfatório" para R3 porque a expressão "trama
sobre" casou dentro de "trama sobrenatural". É um falso positivo do regex, não
da regra — o tema julga o desfecho e pertence a `enredo_desfecho`. Corrigido à
mão nos números acima; e é a demonstração de por que o classificador de
produção precisa ser um modelo com definições, não uma lista de padrões.)*

**Os 20 temas que tocavam mais de um sub-eixo e foram decididos pela
precedência** (14% do total) são o custo real da divisão, e valem ser vistos:

| tema | toca | R2 decide |
|---|---|---|
| *Personagens rasos e irritantes* | personagem + escrita | `personagem` |
| *Desenvolvimento de personagens superficial* | personagem + escrita | `personagem` |
| *Final confuso e insatisfatório* | enredo + desfecho (mesmo sub-eixo agora) | `enredo_desfecho` |
| *Plot twist previsível ou decepcionante* | enredo_desfecho + escrita | `escrita` |
| *Roteiro inteligente e diálogos afiados* | escrita (duas vezes) | `escrita` |
| *Premissa interessante, execução confusa* | escrita + enredo_desfecho | `escrita` |
| *Narrativa previsível e clichê* | enredo_desfecho + escrita | `escrita` |

Note que a divisão de **três** já absorve 4 das 18 ambiguidades da primeira
rodada só por juntar `desfecho` com `coerencia` — os pares `Final confuso`,
`Final decepcionante e ilógico`, `Final decepcionante ou confuso` e `Narrativa
fragmentada e sem conclusão satisfatória` deixam de ser fronteira.

**Os 11 bullets vazios** merecem registro à parte porque são um achado sobre a
síntese, não sobre a taxonomia: *"História"* (`spider-man`/medianas),
*"Vilão"* (`spider-man`/medianas), *"Roteiro e narrativa"* (2×), *"Roteiro e
história"*, *"Roteiro e mensagem"*, *"Roteiro e mistério"*, *"Roteiro e
desenvolvimento"*, *"Roteiro e direção intensos"*, *"Roteiro e construção do
mistério"*, *"Roteiro sem desenvolvimento"*. Nenhuma divisão de eixo conserta um
bullet que não afirma nada. **7 dos 11 estão no bucket positivo** — 19% de todos
os bullets de `roteiro_estrutura` do grupo positivo são contentless.

## Por que TRÊS e não cinco — a medição que decidiu

A divisão natural dos 148 temas é de cinco (`dialogo`, `desfecho`,
`personagem`, `coerencia`, `premissa`). Medindo o **poder de separação entre
buckets** de cada opção (proxy de tema — ver o limite abaixo):

| divisão de 5 | temas | neg / med / pos | amplitude |
|---|---:|---|---:|
| `coerencia` | 31 | 20% / 27% / 8% | **19 pp** |
| `premissa` | 17 | 16% / 8% / 5% | 10 pp |
| `personagem` | 48 | 33% / 27% / 30% | 5 pp |
| `desfecho` | 22 | 14% / 16% / 11% | 5 pp |
| `dialogo` | 17 | 11% / 10% / 11% | **2 pp** |

| divisão de 3 | temas | neg / med / pos | amplitude |
|---|---:|---|---:|
| `enredo_desfecho` | 47 | 33% / 35% / 16% | **19 pp** |
| `escrita` | 40 | 29% / 25% / 19% | 10 pp |
| `personagem` | 48 | 33% / 27% / 30% | 5 pp |

**A divisão de três preserva integralmente o poder de separação da de cinco
(19pp e 10pp nos dois casos) com dois eixos a menos.** Os dois que somem —
`dialogo` (2pp) e `desfecho` (5pp) — não separavam nada; eles apenas
adicionariam duas linhas finas ao cálculo de lift, num catálogo em que **13 das
31 marcações de contraste publicadas já sobrevivem a menos de 60% das
reamostragens** (`ESTUDO_CATALOGO_35.md` §8). Eixo fino é ruído a mais na
margem de 20pp.

**O que o leitor perde, dito sem maquiagem.** `dialogo` é uma coisa que o leitor
reconhece e que muda decisão de assistir; sob a proposta, *"Diálogos artificiais
e exagerados"* aparece na linha **Escrita** em vez de numa linha **Diálogo**. A
perda é pequena porque **o texto do bullet já diz que é sobre diálogo** — o eixo
existe para alinhar linhas e calcular lift, não para informar o assunto, que o
próprio tema informa. Se, com o catálogo expandido, `escrita` saturar, a divisão
em `dialogo` + `premissa` é o próximo passo natural e não custa nada agora.

**LIMITE DESTE TESTE, e ele é grande.** Tudo acima é nível de **TEMA** (o que a
síntese publicou), não de **REVIEW** (o que a classificação conta e o que
alimenta o lift). O proxy é enviesado para o plano, porque a composição dos 6
temas por bucket é restrita por construção. **O efeito da divisão sobre o lift
real é desconhecido, e há uma razão concreta para esperar que seja menor que o
proxy sugere:** 56% das reviews já carregam `roteiro_estrutura`, e essas reviews
carregam em média **3,58 eixos** contra 2,29 das que não carregam. Reviews que
falam de roteiro são as longas, e uma review longa provavelmente toca
personagem **e** enredo **e** escrita — caso em que a divisão não de-satura
nada, só troca um eixo de 56% por três de 30–40%. **Esta é a incerteza central
da proposta e a primeira coisa a medir antes de implementar** (ver "O que medir
antes de aprovar").

## As outras perguntas do briefing

**`impacto_emocional` precisa do mesmo tratamento? NÃO — MEDIDO.** Está em
34,6% pós-verificador, com 10,3pp de amplitude — perfil normal. O que ele
precisa é de **promoção de arquitetura**: o passe `V2_alvo` roda hoje como
script separado (`scripts/verificador_impacto.py aplicar-producao`) e o
pipeline "prefere o verificado quando existe". Numa taxonomia nova, ele deve ser
parte declarada da classificação, com o `taxonomia_id` cobrindo os dois passes —
senão a precisão de 0,79 depende de alguém lembrar de rodar um script.

**`ritmo` deve ser fundido ou reduzido? NÃO — MEDIDO, e é o oposto.** `ritmo`
tem **16,5pp de amplitude, a maior do catálogo** (36,0% / 31,0% / 19,6%,
gradiente limpo do negativo ao positivo). É o melhor separador que a taxonomia
tem. A redundância que o estudo achou — 48 temas distintos para 76 bullets,
*"Ritmo lento e tédio"* 10×, *"Ritmo lento e arrastado"* 8× — é **redundância de
TEMA, não de EIXO**: o eixo está certo, o que está errado é [D] ser obrigado a
devolver 6 temas por bucket quando o público tem três coisas a dizer sobre
ritmo. A correção é em §[D] (permitir lista mais curta, como §2.5 já permite
para bullets de contraste), não na taxonomia.

**`expectativa` deve ser fundido? A fusão foi TESTADA e REFUTADA.**
Hipótese: `expectativa` (19,9%, 6,0pp, 4% dos bullets) e `comparacoes` (36,4%,
3,9pp, 2,4% dos bullets) são ambos "o quadro de referência que o espectador
trouxe de fora" e poderiam virar um eixo só, pagando parte do custo do split.

| eixo | % reviews | neg | med | pos | amplitude |
|---|---:|---:|---:|---:|---:|
| `expectativa` | 19,9% | 22,3% | 20,9% | 16,3% | 6,0 pp |
| `comparacoes` | 36,4% | 35,7% | 34,9% | 38,8% | 3,9 pp |
| **fusão `referencia_previa`** | **47,6%** | 48,5% | 47,6% | 46,6% | **1,9 pp** |

**A fusão cria um segundo `roteiro_estrutura`:** 47,6% de frequência com 1,9pp
de amplitude — o pior poder de separação de qualquer eixo, atual ou proposto.
(As reviews que carregam os dois hoje são só 8,8% do corpus, então a união quase
soma as duas frequências em vez de absorvê-las.) **Refutada por medição.**

**O que fazer com `comparacoes`, então: estreitar, não fundir.** PROPOSTO —
restringir a definição ao ato que o leitor de fato usa para decidir, e mandar o
resto para onde pertence:

> `comparacoes`: comparação do filme com **outra obra** — outro filme, o
> livro que ele adapta, os outros filmes da mesma franquia, ou o trabalho
> anterior do mesmo diretor. **Não** inclui: o filme ter correspondido ou
> não ao que a pessoa esperava (isso é `expectativa`), nem a posição do
> filme como parte 1 de 2 quando o comentário é sobre a história ficar
> incompleta (isso é `enredo_desfecho`).

Efeito esperado: reduzir a frequência de 36,4% para algo que o bullet-share de
2,4% justifique. **NÃO VERIFICADO** — a definição estreitada não foi testada
contra gabarito; é a segunda coisa a medir antes de implementar.

## A taxonomia proposta, completa

| # | eixo | origem | estatuto |
|---|---|---|---|
| 1 | `ritmo` | inalterado | byte-idêntico |
| 2 | `atuacao` | inalterado | byte-idêntico |
| 3 | `direcao_imagem` | inalterado | byte-idêntico |
| 4 | **`personagem`** | de `roteiro_estrutura` | novo |
| 5 | **`enredo_desfecho`** | de `roteiro_estrutura` | novo |
| 6 | **`escrita`** | de `roteiro_estrutura` | novo |
| 7 | `som_trilha` | inalterado | byte-idêntico |
| 8 | `tom_atmosfera` | inalterado | byte-idêntico |
| 9 | `impacto_emocional` | inalterado + verificador embutido | definição igual, arquitetura muda |
| 10 | `comparacoes` | **estreitado** | definição nova |
| 11 | `expectativa` | inalterado | byte-idêntico |
| 12 | `critica_social` | inalterado | byte-idêntico |
| — | `livre` | inalterado | byte-idêntico |

**O `taxonomia_id` muda**, e isso é a proteção funcionando: nenhuma
classificação sob `ebab2667de74` pode ser reusada sob a taxonomia nova, e
`carregar_classificacao` recusa a mistura sozinho.

**Consequência de custo a decidir junto:** reclassificar os 35 já publicados
custa ~4.200 reviews × 3 votos. Pela medição da Entrega 3 (US$ 3,29 por passada
sobre 36.000 reviews), isso é **≈ US$ 1,15**. Não é um obstáculo.

---

# (b) POLARIDADE

**PROPOSTO.** A polaridade é atribuída **por par (review, eixo)**, nunca por
review. Essa é a decisão que importa: os dois casos que o estudo achou —
`longlegs`/negativas com atuação elogiada e criticada, `aftersun`/medianas com
Mescal elogiado e desmerecido — são divergência **dentro do mesmo eixo, dentro
do mesmo bucket**, e uma polaridade por review não os enxerga.

**Quatro valores:**

| valor | quando |
|---|---|
| `positivo` | a review fala bem daquele aspecto |
| `negativo` | a review fala mal daquele aspecto |
| `misto` | a review fala bem **e** mal **do mesmo aspecto** |
| `neutro` | menciona o aspecto sem julgá-lo |

**A regra para o caso dos dois jeitos: `misto`, e `misto` é valor de primeira
classe, não fallback.** Isto precisa estar escrito no prompt e no schema porque
o modo de falha natural é o modelo usar `neutro` como "não sei" — e a Entrega 3
mediu esse modo de falha acontecendo: o braço com chamada separada de polaridade
devolveu `neutro` 69 vezes contra 39 do braço integrado, e na leitura à mão 4 de
8 discordâncias eram concessões explícitas que o `neutro`/`negativo` apagou
(*"achei que faltou tensão… mas num geral eu gostei"* saiu como `negativo`).

**A polaridade é do EIXO, não da review**, e o prompt precisa dizer isso: uma
review de 1,5★ pode ter `atuacao: positivo`. Sem essa frase o modelo herda a
nota.

**Consequência para o produto (fora do escopo desta entrega, registrada aqui
porque é o motivo de a polaridade existir):** com ela, a célula publicada deixa
de ser *"Atuação — 3 de 18"* e passa a poder dizer de que lado são as 3. É a
lacuna de instrumentação que o estudo nomeou no §9.

**Onde a polaridade é decidida: junto do eixo, na mesma chamada.** Recomendação
que vem da Entrega 3, não do desenho — quem decide a polaridade precisa saber
por que o eixo foi atribuído.

---

# (c) FEELINGS

## O princípio: taxonomia interna estruturada, rótulo público simples

Na interface, uma coisa só: **Feelings**. Internamente, **cinco categorias com
listas separadas**, porque misturá-las produz um espaço de etiquetas em que
"melancólico", "vingança" e "máfia" competem pela mesma posição — e em 300
filmes isso é uma nuvem de tags, não um filtro.

## Divisão de fonte — decidida

| categoria | fonte | razão |
|---|---|---|
| `mood` | **reviews** | é o que fica em quem assistiu; não está em metadado |
| `experiencia` | **reviews** | idem |
| `narrativa` | **reviews** | a forma da história, como percebida |
| `tema` | **TMDB `keywords`** | ninguém escreve "este é um filme de máfia" numa review de *O Poderoso Chefão* — assume-se |
| `contexto` | **TMDB `keywords`** | idem |

O argumento do dono é o correto e vale registrar por extenso: derivar `tema` de
review produziria a etiqueta **só onde alguém achou o assunto digno de
comentário**, que é quase o inverso do que um filtro precisa — um filme de máfia
canônico ficaria sem a etiqueta "máfia" justamente por ser óbvio demais para
comentar.

**MEDIDO, e o dado do catálogo confirma a divisão pelo lado oposto:** dos 148
temas de `roteiro_estrutura`, 6 descrevem o assunto em vez da recepção
(*"Trama sobre luto e solidão"*, *"Temas profundos sobre memória e luto"*,
*"Família, trauma e aceitação"*, *"Elementos sobrenaturais e ocultismo"*,
*"Jornada de autodescoberta e aceitação da própria identidade"*, *"Exploração de
temas familiares e de poder"*). Eles existem hoje como bullets de recepção e não
informam recepção nenhuma. Sob a divisão de fonte, saem dos eixos e viram
`tema`/`contexto` do TMDB.

**NÃO VERIFICADO — a premissa de custo do TMDB.** O código busca hoje
`append_to_response=credits,images`
([ficha.py:341](src/espectro24/ficha.py:341)). Acrescentar `keywords` é a mesma
requisição, sem chamada extra — isso está confirmado pela forma da API. **O que
NÃO foi verificado é a cobertura e a qualidade das `keywords` do TMDB para estes
35 filmes**; o cache em `dados/cache/_tmdb/` não as tem, porque nunca foram
pedidas, e esta sessão não roda coleta. **Primeira verificação antes de
implementar:** buscar `keywords` para os 35, medir quantos filmes vêm com
zero/poucas, e se a granularidade serve (TMDB mistura "based on novel" com
"jazz" e "1970s"). Se a cobertura for ruim, a decisão de fonte precisa ser
revista **antes**, não depois.

## As três listas derivadas de review

**PROPOSTO.** Doze etiquetas por categoria, mais catch-all. Ids em ASCII
minúsculo sem acento, separados por `_` — o modelo **nunca** devolve o rótulo
humano, só o id.

**`mood` — o clima que fica**
`aconchegante` · `angustiante` · `melancolico` · `sombrio` · `caotico` ·
`contemplativo` · `tenso` · `leve` · `nostalgico` · `perturbador` ·
`esperancoso` · `frio` · **`mood_outro`**

**`experiencia` — o que o filme fez com quem assistiu**
`de_chorar` · `de_rir` · `prende_a_respiracao` · `de_sair_pensando` ·
`de_ver_entre_os_dedos` · `da_sono` · `de_rever` · `de_ver_acompanhado` ·
`desconfortavel` · `catartico` · `exaustivo` · `empolgante` ·
**`experiencia_outro`**

**`narrativa` — a forma da história**
`plot_twist` · `investigacao` · `vinganca` · `sobrevivencia` ·
`amadurecimento` · `ascensao_e_queda` · `nao_linear` ·
`narrador_nao_confiavel` · `camara_fechada` · `perseguicao` · `final_aberto` ·
`metalinguagem` · **`narrativa_outro`**

**Correção já aprendida na Entrega 3:** `empolgante` está em `experiencia` e o
modelo o devolveu em `mood` cinco vezes. Categorias que compartilham vocabulário
vazam. A regra de desenho que sai disso: **nenhuma etiqueta pode ser plausível
em duas categorias** — se for, ou muda de nome ou muda de categoria, e a
validação deve rejeitar (não realocar em silêncio) uma etiqueta entregue na
categoria errada.

## A disciplina de lista fechada — herdada, e com o motivo medido

O estudo achou dois rótulos de eixo caindo fora da taxonomia por **acento**
(`crítica_social` → `livre`, em `im-still-here-2024` e `mother-2017`). A Entrega
3 mediu o mesmo modo de falha ao vivo: **11 rótulos inválidos em 240 chamadas de
eixo (~4,6%)** — `comparações` (acento), `atucao`/`impato_emocional`/
`comparecoes`/`ton_atmosfera` (digitação), `sombrio`/`liberdade`/`atracao`
(invenção).

E o `temas_livres` de hoje mostra o que acontece **sem** lista fechada:
**2.321 ocorrências em 1.899 rótulos distintos** — praticamente uma etiqueta
nova por review. Com as colisões de normalização visíveis a olho nu no topo da
lista: `sessão de cinema` (29) e `sessao de cinema` (6); `reação da plateia`
(15) e `reações da plateia` (6); `experiência pessoal` (13) e `experiencia
pessoal` (4). **Este é o argumento inteiro para a normalização rígida, e ele é
medido, não temido.**

**PROPOSTO — a regra de validação, em código, na leitura:**

1. Normalizar: `NFD` → remover marcas combinantes → minúsculas → colapsar
   espaço/hífen em `_` → `strip`.
2. Casar **exato** contra o conjunto fechado da categoria.
3. Não casou → **catch-all da categoria**, e o valor cru vai para
   `fora_da_taxonomia` (mesma disciplina de [D3], §[D3] "validação mecânica, não
   confiança").
4. Etiqueta entregue na categoria errada → rejeitada para catch-all, **nunca**
   realocada em silêncio.
5. **`feelings_id`** = hash das cinco listas + do texto das definições, mesma
   construção de `taxonomia_id()`. Sem ele, crescer uma lista mistura
   silenciosamente corpora classificados sob vocabulários diferentes — e as
   listas **vão** crescer.

**O catch-all é contado e nunca publicado como filtro.** Sua frequência é o
gatilho de crescimento da lista: se `mood_outro` passar de um limiar a definir
(sugestão: 15% das atribuições da categoria), a lista está curta e o que está
caindo nele deve ser lido e promovido — com `feelings_id` novo.

## `plot_twist` — exceção deliberada ao anti-spoiler

**Decisão do dono do projeto: passa.** Registrada aqui como exceção explícita ao
§0 ("Toda decisão de design que envolva trade-off entre completude e risco de
spoiler resolve a favor de evitar spoiler"), no mesmo estatuto das exceções de
interface já registradas lá.

**A razão do dono:** já passa hoje, nas reviews e nos bullets publicados —
`shutter-island`/negativas publica *"Plot twist previsível ou decepcionante"*.

**A ressalva, escrita sem maquiagem, porque é o que a exceção custa.** As duas
situações não são equivalentes:

- **Hoje**, a etiqueta aparece **dentro de um grupo**, ao lado de outros cinco
  temas, para quem já abriu a página daquele filme e está lendo o que o grupo
  negativo achou. É informação encontrada.
- **Como filtro**, ela vira **promessa antecipada**: o leitor que clica em
  `plot_twist` recebe uma lista de filmes e entra em cada um deles **sabendo que
  haverá uma reviravolta**. Isso é destruição de expectativa por construção, e
  atinge exatamente o público-alvo declarado no §0 — *"pessoa que ainda NÃO
  assistiu ao filme"*.

O agravante específico: `plot_twist` é a única etiqueta da lista cuja
**existência** é o spoiler. Saber que um filme é `tenso` ou `de_chorar` não
antecipa nada da trama; saber que tem reviravolta antecipa a estrutura inteira
do terceiro ato. `narrador_nao_confiavel` e `final_aberto` têm o mesmo problema
em grau menor e devem ser decididos junto — não os incluí nem excluí por conta
própria.

**Mitigação disponível, não decidida:** a etiqueta pode existir na
classificação (contável, útil internamente) sem ser exposta como filtro
navegável — o mesmo tipo de separação que §2.5 faz entre o eixo que conta e o
eixo que vira bullet. Isso preserva o dado e não faz a promessa. Fica como opção
para o dono, não como recomendação disfarçada.

---

# (d) CONFIANÇA E AMBIGUIDADE

**PROPOSTO — o classificador NÃO reporta autoconfiança.** Nem escala numérica,
nem "alta/média/baixa". Razão: confiança autorrelatada de LLM não é calibrada, e
este projeto já refutou por medição três tentativas de resolver problema de
classificação pedindo cuidado ao modelo no prompt (§2.5, as três correções de
saturação de `impacto_emocional`). Pedir um número de confiança é a quarta
versão do mesmo erro.

**A confiança é a VOTAÇÃO, que já existe.** `votos` e `eixos_por_passe` estão no
schema de `consenso.jsonl` desde a v1.9.x. O que muda é que os limiares passam a
ser **declarados por consumidor**, em vez de um `≥2 de 3` implícito para tudo:

| dimensão | regra | razão |
|---|---|---|
| **eixo** | ≥ 2 de 3 (**inalterado**) | é o limiar calibrado, com precisão/recall medidos por eixo contra gabarito de 100 reviews |
| **polaridade** | maioria **entre as passadas que atribuíram aquele eixo**; sem maioria → `indefinido` | polaridade só existe onde o eixo existe; o denominador é o número de passadas que viram o eixo, não 3 |
| **feelings — publicado como filtro** | ≥ 2 de 3 | filtro é promessa; 1 de 3 promete errado |
| **feelings — telemetria** | ≥ 1 de 3, contado à parte | é o que alimenta o gatilho de crescimento da lista |

**`indefinido` é um quinto valor de polaridade, e é excluído das contagens
publicadas com o denominador declarado** — mesma regra de "frequência sempre com
denominador visível" que vale no resto do projeto. Ele **não** se confunde com
`neutro`: `neutro` é uma leitura ("a review menciona sem julgar"), `indefinido` é
ausência de leitura ("as passadas discordaram").

**Abstenção.** O prompt instrui devolver lista **vazia** quando a review não
sustenta nada, em vez de escolher o mais próximo — e isso vale para feelings, não
para eixo. A assimetria é deliberada e vem de medição: no eixo, o modo de falha
medido é o **oposto** (recall 0,35 em reviews curtas, 27 reviews com recall
zero), e a regra 6 do prompt de produção — *"Review curta menciona POUCOS eixos,
não ZERO eixos"* — existe para combatê-lo. Instruir abstenção no eixo desfaria a
correção que a promoção de `A_regra` comprou. **Nos feelings a instrução é a
inversa**, e a Entrega 3 mostra por quê: o braço com chamada dedicada atribuiu
2,2 etiquetas a reviews de ≤200 caracteres e se absteve em só 7% do corpus,
inventando `camara_fechada` para `cidade-de-deus` e oito etiquetas para uma
review italiana sobre a filmografia de Ridley Scott.

**Interação com o catch-all.** Três destinos distintos, que não devem ser
confundidos:

| situação | destino |
|---|---|
| a review fala de algo real que a lista não cobre | **catch-all** (`mood_outro`) |
| a review não sustenta nada naquela categoria | **lista vazia** |
| as passadas discordaram | **abaixo do limiar**, não entra |

Catch-all inflado significa lista curta; lista vazia frequente significa que a
categoria não é derivável de review; discordância alta significa definição
ambígua. São três diagnósticos diferentes e o schema precisa poder distingui-los.

---

# O que medir antes de aprovar esta proposta

Em ordem de risco. Nenhum destes é caro; todos são bloqueantes para partes
diferentes.

1. **O split de-satura no nível de REVIEW?** *(bloqueia (a))* — é a incerteza
   central. Reclassificar uma amostra de ~200 reviews que hoje carregam
   `roteiro_estrutura` sob os três sub-eixos e medir a frequência de cada um.
   **Critério de aprovação, a fixar antes de rodar:** nenhum sub-eixo acima de
   ~40% do corpus e amplitude entre buckets ≥10pp em pelo menos um deles. Se os
   três saírem em 30–40% cada, a divisão não resolveu o problema para o qual
   existe, e a resposta certa é revisar — não implementar.
2. **As `keywords` do TMDB existem e servem?** *(bloqueia `tema`/`contexto`)* —
   uma requisição por filme, 35 filmes, sem LLM. Medir cobertura e
   granularidade.
3. **A definição estreitada de `comparacoes` reduz a frequência?** *(bloqueia
   (a) parcialmente)* — mesma amostra do item 1.
4. **Gabarito humano para feelings.** *(bloqueia (c) como produto)* — a Entrega 3
   mostrou os dois braços errando em direções opostas sem nenhuma referência para
   dizer qual está certo. Feelings precisa das ~100 reviews anotadas à mão que o
   eixo teve, **antes** de virar filtro público. Sem isso, `de_chorar` é uma
   promessa não medida.
5. **Reprodutibilidade da polaridade sob votação de 3.** — a Entrega 3 mediu
   concordância entre *braços* (81,3%), não entre *passadas do mesmo braço*, que
   é o número que decide se `≥2 de 3` é limiar adequado.

**O que esta proposta não resolve, e é preciso dizer.** A divisão de eixos
**não conserta o lift**. `CLASSIFICACAO_CONSOLIDADO.md` §8 já registra que
nenhuma das quatro intervenções da fase anterior o resolveu, e o estudo dos 35
mostrou que 13 das 31 marcações publicadas sobrevivem a menos de 60% das
reamostragens. Uma taxonomia melhor é condição necessária e não suficiente: o
limite mais provável não é a taxonomia, é **n≈30 reviews por bucket** contra uma
margem de 20pp. Isso é problema de amostra, e a resposta a ele é coleta, não
classificação.
