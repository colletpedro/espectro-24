# CONDIÇÕES DE DECISÃO — fechamento editorial

**Nada publicado.** `git status resultado/` **sem diff**, frontend intocado,
**prompt, regras, validadores e seleção intocados**. Suíte: **1.643**, a mesma
da rodada 5 — esta sessão não alterou código.

Anteriores: [rodada 1](MEDICAO_CONDICOES_DE_DECISAO.md) ·
[2](MEDICAO_CONDICOES_R2.md) · [3](MEDICAO_CONDICOES_R3.md) ·
[4](MEDICAO_CONDICOES_R4.md) · [5](MEDICAO_CONDICOES_R5.md).

---

## O que foi feito

**6 R do dono → 6 reescritas aplicadas. 0 pendentes. 0 cortes.**

Cada uma passou por `validar()` e pelas seis perguntas antes de entrar na
folha. Todas manuais, sobre o texto já gerado — **nenhuma tocou prompt, regra,
validador ou seleção**, pela razão que a própria rodada 5 mediu: `dune-part-two`
deu 4 de 5 e provou que mexer em regra a esta altura tem custo sistêmico.

**Log de auditoria: 16 intervenções** (8 condições × 2 execuções), todas
registradas com texto antes e depois. Nada corrigido em silêncio.

---

## As duas colisões, e a que era minha

**A do `friday-the-13th-2009` era minha, e pela metade.** Eu tinha consertado
a inversão de preferência da rodada 5 (*"busca um remake subestimado"* —
ninguém procura um filme subestimado) e, ao fazê-lo, criei uma generalização
no lugar (*"este tipo de remake costuma receber críticas mais duras do que
merece"* — sobre como remakes são avaliados em geral). **Consertei um defeito
introduzindo o outro**, e o portão editorial pegou.

A do `the-godfather` não é regressão de ninguém: o molde que a rodada 5
recuperou como "honesto" é o que torna a frase genérica. As duas passavam em
todos os validadores.

## O padrão, confirmado em 4 das 6

| filme | de (categoria) | para (o filme) |
|---|---|---|
| `the-godfather` NEG-B | *obras de grande reputação* | *o filme não merece tanto elogio* |
| `the-godfather` NEG-C | *tramas que parecem desconexas* | *a história não prende e soa desconexa* |
| `friday-the-13th-2009` POS-B | *este tipo de remake* | *este remake* |
| `aftersun` NEG-C | *uma atuação masculina* | *Paul Mescal* |

As outras duas tinham defeito próprio: `cats-2019` atribuía status cult
estabelecido onde a evidência é comparação; `pearl-2022` tinha perdido o
elemento concreto na abstração anti-spoiler.

### As seis, antes e depois

| # | filme | antes | depois |
|---|---|---|---|
| 1 | `the-godfather` NEG-B | se frustra quando **obras de grande reputação** não correspondem a altas expectativas | **acha que o filme não merece tanto elogio quanto recebe** |
| 2 | `the-godfather` NEG-C | se desinteressa por **tramas** que parecem desconexas ou difíceis de acompanhar | **perde o interesse porque a história não prende e soa desconexa** |
| 3 | `cats-2019` POS-E | aprecia a estética camp com exageros assumidos e **apelo cult** | **aprecia a estética camp e celebra o exagero desavergonhado como escolha artística** |
| 4 | `aftersun` NEG-C | se decepciona com **uma atuação masculina** pouco crível no papel de pai | **não se convence com Paul Mescal no papel de pai** |
| 5 | `pearl-2022` POS-B | valoriza uma interpretação intensa que expõe momentos de fúria e vulnerabilidade | **quer ver a protagonista num monólogo devastador de fúria e vulnerabilidade** |
| 6 | `friday-the-13th-2009` POS-B | acha que **este tipo de remake costuma** receber críticas mais duras do que merece | **acha este remake superior às sequências originais da franquia** |

**Sobre a 5, porque envolvia a precedência anti-spoiler:** recuperei
*monólogo* e *devastador* — os elementos concretos apagados na rodada 4 — e
**omiti "final"**, que era o único termo localizando o momento no desfecho. A
condição nomeia um elemento formal e o registro emocional; não diz quando
acontece nem o que é dito. **Não precisou de abstenção**: a precedência só se
aplicaria se a formulação segura perdesse lastro, e esta mantém quatro
palavras da paráfrase.

---
---

# Reporte à parte 1 — a categoria expectativa/superestimado

**Pedido:** dizer se a formulação encontrada generaliza, ou se cada filme
exigiu solução própria. Isso decide se a categoria precisa de trabalho futuro.

## Resposta: cada filme exigiu solução própria, e a categoria NÃO está resolvida

Os dois casos que você marcou como R eram os dois que usavam **o mesmo
molde** — o da rodada 5, *"quando obras de grande reputação não correspondem
a altas expectativas"*. As reescritas **divergiram**:

| filme | o que a paráfrase oferecia além da reputação | solução |
|---|---|---|
| `the-godfather` | *"é muito elogiado sem merecer tanto"* — um juízo sobre o mérito | **acha que o filme não merece tanto elogio quanto recebe** |
| `friday-the-13th-2009` | *"é superior a outros remakes e à maioria das sequências originais"* — uma comparação concreta | **acha este remake superior às sequências originais da franquia** |

**Não existe molde comum.** A segunda reescrita **abandona o eixo reputação
por inteiro** e usa uma afirmação de conteúdo (superioridade sobre as
sequências) que estava na paráfrase o tempo todo. A primeira permanece no eixo
reputação porque a paráfrase não oferece outra coisa.

### O que isso revela sobre a categoria

**O eixo `expectativa` é o único da taxonomia cujo objeto não é o filme — é a
relação entre o público e a reputação do filme.** Todos os outros nove eixos
nomeiam algo que está na tela (ritmo, atuação, imagem, som, roteiro…). Este
nomeia algo que está **fora** dela.

Daí a dificuldade estrutural: **um formato que exige ancorar no filme colide
com um eixo cujo assunto não é o filme.** As três saídas observadas em cinco
rodadas foram:

1. **abster** (rodada 4, 6 filmes) — perde informação de decisão real;
2. **subir ao meta** (rodada 5) — o que você marcou como R;
3. **descer ao conteúdo que a paráfrase carrega ao lado da reputação** — só
   funciona quando existe esse conteúdo, e `friday` tinha, `the-godfather`
   quase não tinha.

**Os outros quatro filmes da categoria não foram revistos** e continuam no
molde da rodada 5: `parasite-2019` NEG-C, `hereditary` NEG-B, `interstellar`
NEG-B, `longlegs` NEG-B. Você não os marcou — **mas eles usam a mesma
construção que você reprovou nos dois outros.** Ou a diferença está em algo
que eu não isolei, ou eles passaram por não terem sido lidos com o mesmo
peso. **Vale a sua conferência antes da publicação**, e é a única pendência
que eu deixaria em aberto.

**Recomendação:** a categoria precisa de trabalho futuro, e não é reescrita —
é decidir se `expectativa` deve alimentar condições. Um eixo cujo objeto está
fora do filme talvez pertença ao veredito, que descreve a recepção, e não a
um bloco que recomenda pelo filme.

---

## Reporte à parte 2 — o rótulo do `aftersun`, verificado

Você pediu para conferir se o `alguns` estava errado. **Não está.**

| | |
|---|---|
| `aftersun` NEG-C | 8 de 40 = **20%** |
| banda `alguns` | 10–25% (inclusive) |
| rótulo emitido | **`alguns`** ✓ |

**O código está certo; quem infla é a paráfrase.** E não é caso isolado —
medi o catálogo inteiro:

| | |
|---|---:|
| temas com `rotulo_forca` | 611 |
| **paráfrase usa quantidade FORTE** (*"parcela significativa"*, *"muitos"*, *"vários"*, *"amplamente"*) **enquanto o código diz `poucos`/`alguns`** | **80 (13,1%)** |

Exemplos: `mother-2017` MED-C diz *"a maioria"* com 10 de 40 (25% → `alguns`);
`everything-everywhere` MED-E diz *"amplamente"* com 9 de 40 (22% → `alguns`).

**É o modo de falha que o §10 do `ESTUDO_CATALOGO_35` já tinha medido** — *"os
erros estão nas palavras de quantidade e de escopo, que são justamente as que
nenhuma review individual pode confirmar ou desmentir"*. A novidade é que o
bloco de condições **põe o rótulo do código ao lado da paráfrase da síntese na
mesma tela**, e a discordância, que antes era invisível, agora é legível.

**Nada a corrigir nesta sessão:** a paráfrase é saída de [D], a montante, e o
rótulo — que é a autoridade sobre quantidade — está correto. Fica registrado
como achado, e a folha traz uma nota para que a leitura não confunda os dois.

---
---

# A folha fechada

| | |
|---|---:|
| condições | **263** |
| tempo estimado de releitura | **~132 min** |
| R pendentes | **0** |
| intervenções manuais no log | 16 (8 condições × 2 execuções) |

A contagem não mudou: as seis foram **reescrita de texto**, sem adição nem
remoção. `shutter-island` POS-B continua saltado; `dune-part-two` POS-C mantém
a formulação restaurada da rodada 4.

**O texto está fechado.** O que resta é decisão de publicação, que é sua e não
desta sessão. A única coisa que eu levaria para essa decisão é a conferência
dos quatro filmes de expectativa que não foram revistos.
