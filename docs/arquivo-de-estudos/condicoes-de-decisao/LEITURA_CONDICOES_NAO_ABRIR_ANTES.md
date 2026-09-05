# Leitura das condições — FECHADA

*(O aviso no nome do arquivo perdeu a função: o portão editorial já
aconteceu. O arquivo fica com o nome original para não quebrar referências.)*

## Estado final

| | |
|---|---:|
| condições na folha | **263** |
| marcadas R pelo dono | 6 |
| marcadas C pelo dono | 0 |
| **reescritas aplicadas** | **6 de 6** |
| pendentes | **0** |

**As seis passaram por `validar()` e pelas seis perguntas do portão antes de
entrar na folha.** Nenhuma toca prompt, regra, validador ou seleção.

---

## O padrão das seis, confirmado

Em **quatro das seis** o defeito era o mesmo que o dono nomeou: **a condição
subia um nível de abstração e saía do filme.** Todas tinham lastro, todas
passavam nos validadores, todas eram verdadeiras — e todas falavam de uma
CATEGORIA em vez daquele filme.

| filme | de | para |
|---|---|---|
| `the-godfather` NEG-B | *obras de grande reputação* | *o filme não merece tanto elogio* |
| `the-godfather` NEG-C | *tramas que parecem desconexas* | *a história não prende e soa desconexa* |
| `friday-the-13th-2009` POS-B | *este tipo de remake* | *este remake* |
| `aftersun` NEG-C | *uma atuação masculina* | *Paul Mescal* |

As outras duas tinham defeito próprio: `cats-2019` atribuía status cult
estabelecido onde a evidência é comparação; `pearl-2022` tinha perdido o
elemento concreto na abstração anti-spoiler.

---

## As seis, uma a uma

### 1. `the-godfather` NEG-B — *Filme superestimado*
> antes: *se frustra quando obras de grande reputação não correspondem a altas expectativas*
> **depois: acha que o filme não merece tanto elogio quanto recebe**

Sai do meta (reputação e hype em geral) e vai ao juízo sobre o filme.
Lastro direto: a paráfrase diz *"é muito elogiado sem merecer tanto"*.

### 2. `the-godfather` NEG-C — *Dificuldade de conexão com a trama*
> antes: *se desinteressa por tramas que parecem desconexas ou difíceis de acompanhar*
> **depois: perde o interesse porque a história não prende e soa desconexa**

O *"quando… tramas"* virou *"porque a história"* — deixa de enunciar uma
regra sobre um tipo de trama e passa a falar desta. Lastro: *"a história não
conseguiu prendê-los, com uma narrativa que parecia desconexa"*.

### 3. `cats-2019` POS-E — *Culto e arte camp*
> antes: *aprecia a estética camp com exageros assumidos e apelo cult*
> **depois: aprecia a estética camp e celebra o exagero desavergonhado como escolha artística**

"Apelo cult" atribuía status; a evidência é que o grupo **compara** o filme a
obras cult. Mantidos camp e exagero, retirada a atribuição. Lastro:
*"celebrando seu exagero e falta de vergonha como qualidades artísticas"*.

### 4. `aftersun` NEG-C — *Atuação de Paul Mescal não convence*
> antes: *se decepciona com uma atuação masculina pouco crível no papel de pai*
> **depois: não se convence com Paul Mescal no papel de pai**

O nome está no tema, então citá-lo é permitido (a invariante proíbe
INTRODUZIR nome ausente do briefing, não repetir o que está). Sai o abstrato
*"atuação masculina"*, entra o ator específico.

### 5. `pearl-2022` POS-B — *Monólogo final*
> antes: *valoriza uma interpretação intensa que expõe momentos de fúria e vulnerabilidade*
> **depois: quer ver a protagonista num monólogo devastador de fúria e vulnerabilidade**

Recupera **monólogo** e **devastador** — os elementos concretos que a
abstração da rodada 4 tinha apagado — e **omite "final"**, que é o único
termo que localizava o momento no desfecho. Nomeia um elemento formal e o
registro emocional; não diz quando acontece nem o que é dito.

**Não precisou de abstenção:** a precedência só se aplicaria se a formulação
sem spoiler perdesse lastro, e esta mantém quatro palavras da paráfrase.

### 6. `friday-the-13th-2009` POS-B — *Remake subestimado*
> antes (rodada 5, minha): *acha que este tipo de remake costuma receber críticas mais duras do que merece*
> **depois: acha este remake superior às sequências originais da franquia**

**A colisão que o dono apontou é real e minha correção anterior estava pela
metade.** Eu tinha consertado a inversão de preferência (*"busca um remake
subestimado"* — ninguém procura um filme subestimado) e criado uma
generalização no lugar (*"este tipo de remake costuma…"* — como remakes são
avaliados em geral). A versão final abandona o eixo reputação e usa a
afirmação de conteúdo que estava na paráfrase o tempo todo: *"é superior a
outros remakes e à maioria das sequências originais"*.

---

## `shutter-island` e `dune-part-two` — mantidos

`shutter-island` POS-B continua saltado. `dune-part-two` POS-C mantém a
formulação restaurada da rodada 4. Nenhum dos dois estava entre os 6 R.
