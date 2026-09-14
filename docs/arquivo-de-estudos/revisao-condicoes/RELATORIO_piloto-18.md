# Revisão de condições — lote `piloto-18`

**Impressão digital do lote: `0ec05ad3e326`** · 141 itens (138 publicáveis + 3 descartados pelo validador) · 18 filmes · insumo: `docs/arquivo-de-estudos/revisao-condicoes/insumo-piloto-18`

*Para o dono:* este arquivo é o insumo da revisora externa — passe-o INTEIRO, sem cortar a seção 1. Ao trazer a resposta de volta, cite o lote pela impressão digital e os itens pelo número.

## 1. Regras — leia antes de julgar qualquer item

Este relatório é para você, revisora, que **não tem acesso ao projeto**. Tudo
o que é preciso para julgar está nesta seção. Julgue pelas regras abaixo, não
pelo senso comum sobre o que seria uma boa recomendação.

### 1.1 O produto

Uma página por filme, para quem **ainda NÃO assistiu** e está decidindo se
assiste. Tudo o que a página diz vem de reviews de usuários do Letterboxd. As
reviews são separadas em três **grupos** pela nota que a pessoa deu: quem
**não recomenda** (notas baixas), o **meio-termo**, e quem **recomenda** (notas
altas). De cada grupo o sistema lê uma amostra de até 40 reviews e extrai
**temas**: o assunto que aparece, com uma paráfrase do que o grupo diz dele.

### 1.2 O bloco sob revisão: as condições

Duas colunas, no topo da página:

    Vale a pena se você...    ← escrita a partir dos temas de quem RECOMENDA
    Talvez evite se você...   ← escrita a partir dos temas de quem NÃO recomenda

Cada **condição** é uma frase curta que completa a abertura. Uma IA escreveu
a frase; **antes** disso, o código escolheu QUAIS temas viram condição, em que
ordem, e com que rótulo de força. A frase só pode dizer, com outras palavras,
o que o tema e a paráfrase já dizem.

**Por que isto exige leitura.** No resto da página o produto só RELATA o que
as pessoas acharam. Aqui ele RECOMENDA — diz ao leitor em que caso assistir.
É uma exceção deliberada, e uma das condições dela é que nenhuma condição vá
ao ar sem leitura.

### 1.3 Os campos de cada item

- **número** (`C017`) e **chave** (`filme · coluna · tema`) — cite o número.
- **condição** — o texto integral, como apareceria na página.
- **tema de origem** — código e nome. `POS-A` é o tema mais citado de quem
  recomenda, `POS-B` o segundo…; `NEG-` o mesmo para quem não recomenda.
- **o que o grupo diz** — a paráfrase de onde a condição tem de sair.
- **rótulo de força (do código)** — quantos do grupo mencionaram o tema:
  menções ÷ reviews lidas, calculado pelo CÓDIGO e mostrado ao lado da
  condição na página. Faixas: `poucos` abaixo de 10%; `alguns` de 10% a 25%; `muitos` de 25% a 50%; `cerca de metade` de 40% a 60%; `a maioria` de 50% a 80%; `quase todos` de 80% em diante. Onde duas faixas se sobrepõem,
  vale a mais fraca. "sem rótulo" = grupo com amostra pequena, onde o
  código não afirma quantidade nenhuma.
- **peso da coluna** — `~X% das notas`: quanto do filme aquele grupo é,
  pelo histograma de notas. Também escrito pelo código.
- **como entrou** — `base` (entre os 3 temas mais citados do grupo) ou
  `par obrigatório` (entrou porque o outro grupo fala do MESMO assunto, para
  que a página não recomende um traço sem mostrar a objeção a ele).
- **eixo do tema** — cada tema é classificado em um de dez assuntos (ritmo,
  atuação, expectativa…). Aqui só importa para a regra R13.
- **situação no validador** — um validador automático já roda sobre toda
  condição; os que ele reprovou aparecem como `DESCARTADA`, com o motivo.
- **categorias de risco** — o que os detectores deste relatório acharam.
  Ver 1.6: eles NÃO são julgamento.

Números aparecem neste relatório (contagens, percentuais) porque ele é para
você. Na página, quem escreve número é só o código.

### 1.4 As regras — toda condição publicada tem de cumprir TODAS

- **R1 — Âncora e fidelidade.** Nomeia o assunto do SEU tema. Não introduz
  assunto, adjetivo avaliativo, nome de pessoa ou fato de enredo que não
  esteja no tema ou na paráfrase.
- **R2 — Sinal.** Não afirma mais do que o tema. Um EFEITO ("despertou
  curiosidade") não vira APROVAÇÃO; um INCÔMODO não vira TOLERÂNCIA; "bonito
  mas sem tática" não vira só "bonito". Se a paráfrase traz ressalva
  ("embora…", "mas alguns…"), a condição carrega as duas metades — ou não
  existe.
- **R3 — Discriminação.** Se o outro grupo fala do mesmo assunto, a condição
  diz QUAL leitura oferece: "ritmo contemplativo", não só "ritmo lento".
- **R4 — Zero algarismo na condição.** Nenhum número, em nenhuma forma. A
  razão: a página já mostra números escritos pelo código ("~34% das notas");
  um número na frase competiria com eles, e o leitor não distingue "1940" de
  "34%". **Exceção nova, e estreita:** um ANO de quatro algarismos pode
  aparecer no NOME DE UM TEMA ("Comparação com o clássico de 1940") — nunca
  na condição, nunca na paráfrase, nunca como quantidade.
- **R5 — Quantidade é do código.** A condição não escreve "a maioria",
  "muitos", "alguns", "poucos", "metade" nem nada sobre QUANTAS pessoas
  disseram aquilo, e não sugere consenso. O rótulo de força aparece ao lado.
  Atenção a um padrão conhecido: a PARÁFRASE às vezes usa quantidade mais
  forte que o rótulo ("uma parcela significativa" ao lado de `alguns`). O
  rótulo está certo — é contagem; quem infla é a paráfrase, que vem de uma
  etapa anterior. A condição não pode herdar a inflação.
- **R6 — Anti-spoiler.** A condição é para quem não viu. Proibido usar
  desfecho, reviravolta, morte, revelação ou ponto de chegada de um arco como
  motivo para assistir ou evitar — mesmo quando o tema fala disso. **O
  teste:** se a frase diz ao leitor O QUE PROCURAR durante o filme, é
  spoiler; se diz QUE TIPO DE EXPERIÊNCIA ele é, não é. Permitido: dizer que
  o final é aberto ou ambíguo; dizer que existe uma virada. Proibido: dizer o
  que o final contém, ou o EFEITO da virada ("reviravoltas que transformam a
  história").
- **R7 — Acionável por quem não viu.** O leitor precisa conseguir reconhecer
  se aquilo lhe interessa ANTES de assistir. Personagem pelo nome, cena
  específica, "aquele momento" — referência que só faz sentido para quem viu
  — falha.
- **R8 — Qualidade da obra, não perfil do leitor.** Proibido "você é o tipo
  de pessoa que", "pessoas que gostam"; também não é crítica ("o filme tem
  ótima fotografia"). Nomeia a qualidade concreta e deixa o leitor se
  reconhecer. Oposição "X em vez de Y" só quando os DOIS lados estão na
  paráfrase.
- **R9 — Escopo.** Não fala de "os críticos", "o consenso", "o público".
- **R10 — Palavras próprias.** Não copia o tema nem a paráfrase palavra por
  palavra; sem aspas.
- **R11 — Forma.** Até 14 palavras, português do Brasil, começa
  em minúscula e continua a abertura sem repeti-la.
- **R12 — Especificidade.** A maior abstração que a paráfrase sustenta
  INTEIRA: um detalhe de passagem não vira critério central, e subir de
  abstração além do que está escrito é inventar.
- **R13 — O eixo `expectativa` não vira condição.** Temas sobre hype,
  reputação, "superestimado": o objeto deles não é o filme, é a relação do
  público com a fama dele. Decisão editorial vigente: não são publicados.

### 1.5 O que devolver

Para cada item, uma de duas respostas, citando o número:

    CONFIRMO: C001, C002, C004–C009
    DUVIDOSO: C003 — R6 — diz ao leitor que o desfecho é cruel

- **CONFIRMO** — você não achou violação de nenhuma regra.
- **DUVIDOSO** — cite a(s) regra(s) e o motivo em uma frase. O item vai para
  a leitura do dono.

Para itens `DESCARTADA` e de `expectativa`, que não serão publicados, a
pergunta é outra (está no topo de cada seção). Não reescreva condições e não
decida publicação: quem decide é o dono. Na dúvida, DUVIDOSO.

### 1.6 O que este relatório NÃO faz

Não aprova, não rejeita, não pontua, não recomenda. As categorias de risco
são o que detectores automáticos acharam — alguns exatos, outros aproximados
com precisão conhecida e baixa, um sem medição nenhuma; cada seção diz qual.
**"Sem categoria" quer dizer que nenhum detector disparou, NÃO que o item não
tem risco.** Leia todos os itens contra as regras.

## 2. Resumo por categoria

Cada item aparece UMA vez, na primeira categoria da tabela que o toca; "tocam" conta também os que estão em outra seção.

| seção | categoria | detector | nesta seção | tocam |
|---|---|---|---:|---:|
| 3.1 | Descartada pelo validador automático | EXATO | 3 | 3 |
| 3.2 | Tema de origem não bate com o filme publicado | EXATO | 0 | 0 |
| 3.3 | Tema do eixo `expectativa` (regra R13 — retido, não publica) | EXATO | 2 | 2 |
| 3.4 | Algarismo no texto (regra R4, com a exceção de ano já aplicada) | EXATO | 0 | 0 |
| 3.5 | Possível spoiler / exige ter visto o filme (regra R6) | HEURÍSTICO MEDIDO | 12 | 14 |
| 3.6 | Paráfrase com quantidade mais forte que o rótulo do código (regra R5) | HEURÍSTICO LÉXICO | 6 | 8 |
| 3.7 | Pode não ser acionável por quem não viu o filme (regra R7) | HEURÍSTICO NÃO MEDIDO | 6 | 7 |
| 3.8 | Sem categoria de risco | nenhum detector disparou | 112 | — |

## 3. Itens, por categoria de risco

### 3.1 Descartada pelo validador automático (3 itens)

*Detector:* EXATO — o validador existente reprovou a frase; ela NÃO seria publicada.

*Pergunta desta seção:* O motivo do descarte procede? DUVIDOSO aqui = a frase parecia boa e o validador errou (condição boa perdida).

#### C012 · `drive-my-car` · Vale a pena · POS-D

> **Vale a pena se você** busca uma experiência imersiva e aceita um ritmo deliberado em longa duração

- **chave:** `drive-my-car · vale_a_pena · POS-D`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-D — *Ritmo lento e duração*
- **o que o grupo diz:** O ritmo deliberado e a longa duração são mencionados tanto como um desafio quanto como um aspecto que contribui para a imersão, com muitos afirmando que o tempo passa rápido apesar das três horas.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** **DESCARTADA** — `exemplo_verbatim`
- **categorias de risco:**
    - `descartada` — `exemplo_verbatim` — copia uma sequência do texto do grupo palavra por palavra — reformule

#### C020 · `force-majeure-2014` · Vale a pena · POS-F

> **Vale a pena se você** aceita um andamento lento e um desfecho divisivo a serviço da proposta

- **chave:** `force-majeure-2014 · vale_a_pena · POS-F`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~80% das notas
- **tema de origem:** POS-F — *Ritmo lento e final questionável*
- **o que o grupo diz:** Algumas reviews mencionam um ritmo lento e um desfecho que não agradou a todos, embora reconheçam que a abordagem funciona para a proposta do filme.
- **rótulo de força (do código):** `alguns` (7 de 40 = 18%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** **DESCARTADA** — `sem_discriminacao`
- **categorias de risco:**
    - `descartada` — `sem_discriminacao` — o outro grupo fala do MESMO assunto e a sua frase não diz qual das duas leituras ela oferece: use a palavra que separa uma da outra
    - `spoiler` — na condição: desfecho; no tema/paráfrase: final, desfecho

#### C092 · `speak-no-evil-2022` · Talvez evite · NEG-C

> **Talvez evite se você** se decepciona com desfechos gratuitos que tentam chocar sem construir significado coerente

- **chave:** `speak-no-evil-2022 · talvez_evite · NEG-C`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-C — *Final insatisfatório e pretensioso*
- **o que o grupo diz:** O desfecho é decepcionante, gratuito e tenta chocar sem construir um significado coerente, deixando uma sensação de vazio.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** **DESCARTADA** — `exemplo_verbatim`
- **categorias de risco:**
    - `descartada` — `exemplo_verbatim` — copia uma sequência do texto do grupo palavra por palavra — reformule
    - `spoiler` — na condição: desfechos; no tema/paráfrase: final, desfecho

### 3.2 Tema de origem não bate com o filme publicado (0 itens)

*Detector:* EXATO — a condição cita um tema cujo texto hoje é outro (o filme foi republicado depois de a condição ser gerada).

*Pergunta desta seção:* Não dá para julgar contra um tema que mudou. Aponte como DUVIDOSO.

*(nenhum item)*

### 3.3 Tema do eixo `expectativa` (regra R13 — retido, não publica) (2 itens)

*Detector:* EXATO — o tema foi classificado no eixo `expectativa`.

*Pergunta desta seção:* Estes itens estão aqui só para registro: pela regra R13 não serão publicados, qualquer que seja o texto.

#### C030 · `get-out-2017` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra quando produções amplamente aclamadas não correspondem ao grande hype

- **chave:** `get-out-2017 · talvez_evite · NEG-C`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-C — *Filme superestimado*
- **o que o grupo diz:** Diversas reviews classificam a obra como superestimada, dizendo que não corresponde ao hype e que não entende o motivo de tanto elogio.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `expectativa`
- **situação no validador:** passou
- **categorias de risco:**
    - `expectativa` — tema classificado no eixo `expectativa`
    - `quantidade` — a paráfrase diz 'diversas' (faixa `muitos`); o código diz `alguns`

#### C134 · `whiplash-2014` · Talvez evite · NEG-F

> **Talvez evite se você** se frustra quando obras de grande aclamação não correspondem a expectativas tão altas

- **chave:** `whiplash-2014 · talvez_evite · NEG-F`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-F — *Excesso de hype e expectativas frustradas*
- **o que o grupo diz:** Diversas pessoas relatam que a obra não corresponde à aclamação que recebeu, sentindo-se decepcionadas após tantos elogios e considerando o resultado superestimado.
- **rótulo de força (do código):** `alguns` (8 de 40 = 20%)
- **como entrou:** par obrigatório
- **eixo do tema:** `expectativa`
- **situação no validador:** passou
- **categorias de risco:**
    - `expectativa` — tema classificado no eixo `expectativa`
    - `quantidade` — a paráfrase diz 'diversas' (faixa `muitos`); o código diz `alguns`

### 3.4 Algarismo no texto (regra R4, com a exceção de ano já aplicada) (0 itens)

*Detector:* EXATO — algarismo na condição, na paráfrase, ou no nome do tema fora da forma de ano admitida.

*Pergunta desta seção:* Confira se o número compete com os números do código.

*(nenhum item)*

### 3.5 Possível spoiler / exige ter visto o filme (regra R6) (12 itens)

*Detector:* HEURÍSTICO MEDIDO — palavras de desfecho/revelação ('final', 'desfecho', 'reviravolta', 'morte', 'revelação'…) no tema, na paráfrase ou na condição. Medido sobre 266 condições: precisão 15,8% (a maioria dos alarmes é falsa) e pegou 3 dos 5 spoilers que a leitura humana marcou — ~2 em 5 spoilers reais NÃO disparam este detector. Fonte conhecida de alarme falso: o marcador de 'clímax' também casa 'clima' ('clima opressivo').

*Pergunta desta seção:* Aplique o teste da R6: a frase diz O QUE PROCURAR, ou QUE TIPO DE EXPERIÊNCIA é?

*Também tocam esta categoria, listados em outra seção:* C020, C092.

#### C024 · `force-majeure-2014` · Talvez evite · NEG-E

> **Talvez evite se você** se frustra com desfechos anticlimáticos e encerramentos que parecem insatisfatórios

- **chave:** `force-majeure-2014 · talvez_evite · NEG-E`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-E — *Final decepcionante e anticlimático*
- **o que o grupo diz:** A conclusão é vista como insatisfatória, confusa ou que contradiz o desenvolvimento anterior, deixando a sensação de que o filme não soube encerrar suas questões.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: desfechos, encerrament; no tema/paráfrase: final, conclusa

#### C027 · `get-out-2017` · Vale a pena · POS-C

> **Vale a pena se você** aprecia um suspense com tensão crescente que mantém o clima apreensivo

- **chave:** `get-out-2017 · vale_a_pena · POS-C`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-C — *Tensão e suspense*
- **o que o grupo diz:** As reviews positivas mencionam que o filme constrói uma tensão crescente desde o início, mantendo o espectador apreensivo e envolvido.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: clim

#### C028 · `get-out-2017` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com tramas previsíveis e reviravoltas fáceis de antecipar

- **chave:** `get-out-2017 · talvez_evite · NEG-A`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-A — *Previsibilidade da trama*
- **o que o grupo diz:** Várias reviews negativas afirmam que a história é totalmente previsível, com uma reviravolta óbvia que pode ser antecipada nos primeiros minutos, o que torna a experiência entediante.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: reviravoltas; no tema/paráfrase: reviravolta

#### C035 · `guillermo-del-toros-pinocchio` · Vale a pena · POS-C

> **Vale a pena se você** procura uma experiência comovente que toca em temas sensíveis de vida e perda

- **chave:** `guillermo-del-toros-pinocchio · vale_a_pena · POS-C`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-C — *Emoção e impacto emocional*
- **o que o grupo diz:** Muitas reviews relatam que o filme comove profundamente, levando às lágrimas e tocando em temas sensíveis sobre vida, morte e perda.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — no tema/paráfrase: morte

#### C042 · `happy-hour-2015-1` · Vale a pena · POS-B

> **Vale a pena se você** busca protagonistas femininas com grande profundidade psicológica, nuances e dilemas de identidade

- **chave:** `happy-hour-2015-1 · vale_a_pena · POS-B`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~91% das notas
- **tema de origem:** POS-B — *Personagens femininas complexas e bem construídas*
- **o que o grupo diz:** As reviews elogiam a profundidade das quatro protagonistas, suas nuances e a forma como cada uma lida de maneira distinta com relacionamentos, crises pessoais e a própria identidade.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: identidade; no tema/paráfrase: identidade

#### C043 · `happy-hour-2015-1` · Vale a pena · POS-C

> **Vale a pena se você** valoriza narrativas centradas no vínculo de afeto e cumplicidade de amizades femininas

- **chave:** `happy-hour-2015-1 · vale_a_pena · POS-C`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~91% das notas
- **tema de origem:** POS-C — *Amizade feminina como eixo emocional*
- **o que o grupo diz:** A amizade entre as mulheres é apontada como o coração do filme, uma forma de amor e apoio que permeia até os momentos em que elas estão separadas, oferecendo um senso de pertencimento e identidade.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — no tema/paráfrase: identidade

#### C063 · `memories-of-murder` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra com narrativas dispersas em subtramas e diálogos com pouca clareza

- **chave:** `memories-of-murder · talvez_evite · NEG-C`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-C — *Roteiro confuso e sem foco*
- **o que o grupo diz:** Algumas reviews apontam que a narrativa se perde em subtramas e reviravoltas sem propósito, com diálogos confusos e falta de clareza sobre o que o filme quer dizer, resultando em uma experiência arrastada e insatisfatória.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — no tema/paráfrase: reviravoltas

#### C087 · `speak-no-evil-2022` · Vale a pena · POS-A

> **Vale a pena se você** busca um suspense com clima opressivo e sensação contínua de angústia

- **chave:** `speak-no-evil-2022 · vale_a_pena · POS-A`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~61% das notas
- **tema de origem:** POS-A — *Desconforto e tensão constantes*
- **o que o grupo diz:** As reviews descrevem uma experiência angustiante do início ao fim, com cenas que causam ansiedade e um clima opressivo que domina todo o filme.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: clim; no tema/paráfrase: clim

#### C089 · `speak-no-evil-2022` · Vale a pena · POS-C

> **Vale a pena se você** busca uma experiência que culmine em um desfecho cruel e impactante

- **chave:** `speak-no-evil-2022 · vale_a_pena · POS-C`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~61% das notas
- **tema de origem:** POS-C — *Final impactante e brutal*
- **o que o grupo diz:** As reviews destacam que o desfecho é chocante, cruel e difícil de esquecer, sendo frequentemente apontado como o ponto mais forte do longa.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: desfecho; no tema/paráfrase: final, desfecho

#### C121 · `the-wailing` · Vale a pena · POS-B

> **Vale a pena se você** gosta de tramas de mistério que desorientam e deixam dúvidas constantes

- **chave:** `the-wailing · vale_a_pena · POS-B`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~83% das notas
- **tema de origem:** POS-B — *Mistério ambíguo e confusão sobre quem confiar*
- **o que o grupo diz:** Este grupo destaca que a trama mantém o espectador em dúvida sobre quem é o verdadeiro vilão e o que é real, com reviravoltas que desorientam e deixam a audiência sem saber em quem acreditar até o fim.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — no tema/paráfrase: reviravoltas

#### C124 · `the-wailing` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com enredos que acumulam pistas contraditórias e carecem de lógica interna

- **chave:** `the-wailing · talvez_evite · NEG-B`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-B — *Roteiro confuso e sem coerência*
- **o que o grupo diz:** Este grupo considera que a trama avança em círculos, acumulando reviravoltas e pistas contraditórias que nunca se encaixam, deixando a sensação de que a história carece de estrutura lógica interna.
- **rótulo de força (do código):** `cerca de metade` (21 de 40 = 52%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — no tema/paráfrase: reviravoltas

#### C126 · `the-wailing` · Talvez evite · NEG-D

> **Talvez evite se você** evita desfechos abertos que deixam perguntas essenciais sem respostas recompensadoras

- **chave:** `the-wailing · talvez_evite · NEG-D`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-D — *Final ambíguo e vazio*
- **o que o grupo diz:** Essas críticas afirmam que o desfecho deixa perguntas sem resposta de forma gratuita, sem a ambiguidade recompensadora de uma obra bem construída, resultando em um gosto de vazio e frustração ao final.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `spoiler` — na condição: desfechos; no tema/paráfrase: final, desfecho

### 3.6 Paráfrase com quantidade mais forte que o rótulo do código (regra R5) (6 itens)

*Detector:* HEURÍSTICO LÉXICO — palavra de quantidade na paráfrase ('a maioria', 'muitos', 'vários', 'amplamente', 'parcela significativa'…) numa faixa ACIMA do rótulo que o código calculou. É padrão conhecido e vem de uma etapa anterior (a síntese). O rótulo do código está certo; quem infla é a paráfrase. Calibração: nos 35 filmes do catálogo antigo este léxico acha 88 de 629 temas (14,0%) com paráfrase `muitos` ou acima e código `poucos`/`alguns`; a medição de referência achou 80 de 611 (13,1%) sobre o catálogo de então. Precisão não medida: 'vários aspectos' dispara e não fala de pessoas.

*Pergunta desta seção:* A CONDIÇÃO herdou a inflação (sugere mais gente, ou consenso, do que o rótulo diz)? Se não herdou, CONFIRMO.

*Também tocam esta categoria, listados em outra seção:* C030, C134.

#### C005 · `burning-2018` · Vale a pena · POS-E

> **Vale a pena se você** aceita um ritmo paciente que desenvolve gradualmente a tensão da narrativa

- **chave:** `burning-2018 · vale_a_pena · POS-E`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~82% das notas
- **tema de origem:** POS-E — *Ritmo lento e narrativa metódica*
- **o que o grupo diz:** Embora alguns considerem o ritmo lento, muitos valorizam a construção gradual da tensão e o desenvolvimento cuidadoso da história, que recompensa a paciência do espectador.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'alguns', 'muitos' (faixa `muitos`); o código diz `alguns`

#### C038 · `guillermo-del-toros-pinocchio` · Talvez evite · NEG-C

> **Talvez evite se você** prefere evitar produções com canções fracas, sem graça e letras infantis

- **chave:** `guillermo-del-toros-pinocchio · talvez_evite · NEG-C`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-C — *Músicas ruins e mal executadas*
- **o que o grupo diz:** As canções são criticadas como fracas, sem graça e desnecessárias, muitas vezes parecendo diálogos com ritmo ou letras infantis.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** base
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'muitas' (faixa `muitos`); o código diz `alguns`

#### C080 · `pinocchio-2022` · Talvez evite · NEG-F

> **Talvez evite se você** espera encontrar a mesma ousadia e emoção da animação clássica

- **chave:** `pinocchio-2022 · talvez_evite · NEG-F`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~60% das notas
- **tema de origem:** NEG-F — *Comparação com o clássico de 1940* (o ano 1940 está no nome do tema e é admitido pela exceção da R4)
- **o que o grupo diz:** Muitos destacam que o remake perde completamente a emoção, o charme e a ousadia do original, resultando em uma versão inferior que não justifica sua existência.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** par obrigatório
- **eixo do tema:** `comparacoes`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'muitos' (faixa `muitos`); o código diz `alguns`
    - `acionavel` — referência a outra obra: classica, classico, comparacao

#### C082 · `satantango` · Vale a pena · POS-B

> **Vale a pena se você** aprecia fotografia em preto e branco com planos-sequência extensos e atmosfera hipnótica

- **chave:** `satantango · vale_a_pena · POS-B`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~88% das notas
- **tema de origem:** POS-B — *Fotografia e planos longos*
- **o que o grupo diz:** A fotografia em preto e branco e os extensos planos-sequência são amplamente elogiados pela beleza e pela capacidade de criar uma atmosfera hipnótica e contemplativa.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'amplamente' (faixa `a maioria`); o código diz `cerca de metade`

#### C097 · `the-cloud-capped-star` · Vale a pena · POS-D

> **Vale a pena se você** se envolve com melodramas intensos de forte carga dramática e apelo comovente

- **chave:** `the-cloud-capped-star · vale_a_pena · POS-D`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-D — *Melodrama e emoção*
- **o que o grupo diz:** O melodrama intenso e a carga emocional são vistos como centrais, com alguns considerando excessivo, mas na maioria das vezes eficaz e comovente.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** par obrigatório
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'alguns', 'maioria' (faixa `a maioria`); o código diz `muitos`

#### C114 · `the-turin-horse` · Vale a pena · POS-F

> **Vale a pena se você** procura uma experiência sensorial meditativa e intensa em uma atmosfera melancólica e hostil

- **chave:** `the-turin-horse · vale_a_pena · POS-F`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-F — *Atmosfera opressiva e experiência sensorial*
- **o que o grupo diz:** O filme é descrito como uma experiência sensorial intensa e opressiva, que envolve o espectador em um ambiente hostil e melancólico, muitas vezes comparado a uma instalação artística ou a um estado meditativo.
- **rótulo de força (do código):** `alguns` (7 de 40 = 18%)
- **como entrou:** par obrigatório
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:**
    - `quantidade` — a paráfrase diz 'muitas' (faixa `muitos`); o código diz `alguns`

### 3.7 Pode não ser acionável por quem não viu o filme (regra R7) (6 itens)

*Detector:* HEURÍSTICO NÃO MEDIDO — dois sinais de forma: nome próprio na condição (quem é?), ou referência a OUTRA obra no tema ou na condição ('clássico', 'original', 'remake', 'releitura', 'versão'…). NÃO pega referência a cena ou personagem sem nome — esse caso só a leitura acha.

*Pergunta desta seção:* Quem nunca viu o filme (nem a obra citada) consegue saber se isto lhe interessa?

*Também tocam esta categoria, listados em outra seção:* C080.

#### C034 · `guillermo-del-toros-pinocchio` · Vale a pena · POS-B

> **Vale a pena se você** busca uma releitura profunda de conto clássico com temas de luto e aceitação

- **chave:** `guillermo-del-toros-pinocchio · vale_a_pena · POS-B`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-B — *História e adaptação do conto clássico*
- **o que o grupo diz:** O grupo considera esta uma releitura ousada e profunda do conto, com desenvolvimento do vínculo entre o pai e o boneco, explorando temas como luto e aceitação.
- **rótulo de força (do código):** `muitos` (17 de 40 = 42%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — referência a outra obra: adaptacao, classico, releitura

#### C072 · `pinocchio-2022` · Vale a pena · POS-A

> **Vale a pena se você** busca reviver a essência e a nostalgia da animação clássica

- **chave:** `pinocchio-2022 · vale_a_pena · POS-A`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~15% das notas
- **tema de origem:** POS-A — *Fidelidade e nostalgia em relação ao clássico*
- **o que o grupo diz:** Muitas reviews positivas destacam que a adaptação mantém a essência da animação original, respeitando seus elementos clássicos e despertando nostalgia nos fãs.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `comparacoes`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — referência a outra obra: classica, classico

#### C075 · `pinocchio-2022` · Vale a pena · POS-D

> **Vale a pena se você** gosta de canções clássicas e trilhas sonoras que reforçam uma atmosfera mágica

- **chave:** `pinocchio-2022 · vale_a_pena · POS-D`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~15% das notas
- **tema de origem:** POS-D — *Trilha sonora e canções*
- **o que o grupo diz:** A trilha sonora e as canções clássicas são lembradas com carinho, contribuindo para a atmosfera mágica e nostálgica do filme.
- **rótulo de força (do código):** `alguns` (7 de 40 = 18%)
- **como entrou:** par obrigatório
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — referência a outra obra: classicas

#### C078 · `pinocchio-2022` · Talvez evite · NEG-C

> **Talvez evite se você** evita remakes que exploram a nostalgia sem acrescentar propósito artístico

- **chave:** `pinocchio-2022 · talvez_evite · NEG-C`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~60% das notas
- **tema de origem:** NEG-C — *Desnecessidade do remake*
- **o que o grupo diz:** Várias pessoas questionam por que refazer um clássico que já funcionava perfeitamente, apontando que a nova versão não acrescenta nada de novo e soa como uma exploração nostálgica sem propósito artístico.
- **rótulo de força (do código):** `muitos` (20 de 40 = 50%)
- **como entrou:** base
- **eixo do tema:** `comparacoes`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — referência a outra obra: remake, remakes

#### C105 · `the-second-mother` · Vale a pena · POS-C

> **Vale a pena se você** valoriza uma interpretação natural e humanizada de Regina Casé junto ao elenco

- **chave:** `the-second-mother · vale_a_pena · POS-C`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-C — *Atuação de Regina Casé e do elenco*
- **o que o grupo diz:** Este grupo elogia de forma recorrente a atuação de Regina Casé, descrita como natural e capaz de dar humanidade à personagem, além de destacar a qualidade do restante do elenco.
- **rótulo de força (do código):** `muitos` (17 de 40 = 42%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — nome próprio na condição: Regina, Casé

#### C120 · `the-turin-horse` · Talvez evite · NEG-F

> **Talvez evite se você** espera a mesma força narrativa e profundidade encontradas em clássicos de mestres autorais

- **chave:** `the-turin-horse · talvez_evite · NEG-F`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-F — *Comparações desfavoráveis com outras obras ou diretores*
- **o que o grupo diz:** Algumas críticas comparam o filme a trabalhos anteriores do próprio diretor ou a cineastas como Tarkovski, Fellini e Bergman, considerando-o inferior em termos de narrativa e profundidade. A obra é por vezes descrita como uma versão menos eficaz de outras produções que também exploram o cotidiano ou o pessimismo, mas conseguem manter o interesse.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `comparacoes`
- **situação no validador:** passou
- **categorias de risco:**
    - `acionavel` — referência a outra obra: classicos, comparacoes

### 3.8 Sem categoria de risco (112 itens)

Nenhum detector disparou nestes itens. **Isso não quer dizer que estão livres de risco** — os detectores de spoiler e de acionabilidade deixam passar casos reais (ver 3.5 e 3.7). Leia contra as regras R1–R13.

#### C001 · `burning-2018` · Vale a pena · POS-A

> **Vale a pena se você** busca tramas com ambiguidade deliberada abertas a múltiplas teorias e leituras

- **chave:** `burning-2018 · vale_a_pena · POS-A`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~82% das notas
- **tema de origem:** POS-A — *Ambiguidade e abertura a interpretações*
- **o que o grupo diz:** Muitas reviews elogiam a ambiguidade do filme, que não entrega respostas prontas e convida o espectador a formar suas próprias teorias, tornando a experiência mais rica e sujeita a múltiplas leituras.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C002 · `burning-2018` · Vale a pena · POS-B

> **Vale a pena se você** aprecia uma atmosfera hipnótica guiada por iluminação natural e belos enquadramentos

- **chave:** `burning-2018 · vale_a_pena · POS-B`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~82% das notas
- **tema de origem:** POS-B — *Fotografia e estética visual*
- **o que o grupo diz:** A fotografia é frequentemente destacada como belíssima, com uso marcante de luz natural e enquadramentos que tornam locações comuns visualmente atraentes, criando uma atmosfera hipnótica.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C003 · `burning-2018` · Vale a pena · POS-C

> **Vale a pena se você** valoriza atuações autênticas capazes de expressar a complexidade psicológica dos personagens

- **chave:** `burning-2018 · vale_a_pena · POS-C`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~82% das notas
- **tema de origem:** POS-C — *Atuações do elenco*
- **o que o grupo diz:** As atuações, especialmente a de Steven Yeun e a de Jeon Jongseo, são muito elogiadas por sua autenticidade e capacidade de transmitir a complexidade dos personagens.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C004 · `burning-2018` · Vale a pena · POS-D

> **Vale a pena se você** se interessa por tensões sobre desigualdade de classe, privilégio e alienação social

- **chave:** `burning-2018 · vale_a_pena · POS-D`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~82% das notas
- **tema de origem:** POS-D — *Crítica social e desigualdade de classe*
- **o que o grupo diz:** O filme é visto como uma crítica contundente às disparidades de classe na Coreia do Sul, explorando a tensão entre um protagonista de origem humilde e um personagem rico e misterioso, com comentários sobre privilégio e alienação.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C006 · `burning-2018` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com narrativas de ritmo arrastado e duração prolongada

- **chave:** `burning-2018 · talvez_evite · NEG-A`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-A — *Ritmo lento e duração excessiva*
- **o que o grupo diz:** Muitos espectadores consideram o ritmo arrastado e a longa duração desnecessária, tornando a experiência cansativa.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C007 · `burning-2018` · Talvez evite · NEG-B

> **Talvez evite se você** se frustra com histórias excessivamente ambíguas e desprovidas de resoluções claras

- **chave:** `burning-2018 · talvez_evite · NEG-B`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-B — *Ambiguidade e falta de respostas*
- **o que o grupo diz:** A ambiguidade excessiva e a ausência de resoluções claras deixam a narrativa vazia e frustrante.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C008 · `burning-2018` · Talvez evite · NEG-C

> **Talvez evite se você** tem dificuldade em criar vínculo emocional com personagens apáticos

- **chave:** `burning-2018 · talvez_evite · NEG-C`
- **filme:** Em Chamas (`burning-2018`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-C — *Personagens apáticos e difíceis de se conectar*
- **o que o grupo diz:** O protagonista sem emoções e outros personagens rasos dificultam a criação de vínculo emocional com a história.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C009 · `drive-my-car` · Vale a pena · POS-A

> **Vale a pena se você** se interessa por narrativas sobre luto, culpa e a busca por aceitação

- **chave:** `drive-my-car · vale_a_pena · POS-A`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-A — *Luto e culpa*
- **o que o grupo diz:** As reviews destacam como o filme explora o luto, a culpa e a dificuldade de seguir em frente após uma perda, mostrando personagens que carregam dores do passado e buscam aceitação.
- **rótulo de força (do código):** `a maioria` (28 de 40 = 70%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C010 · `drive-my-car` · Vale a pena · POS-B

> **Vale a pena se você** aprecia o desenvolvimento gradual de confiança e cura mútua entre personagens feridos

- **chave:** `drive-my-car · vale_a_pena · POS-B`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-B — *Relação entre Kafuku e Misaki*
- **o que o grupo diz:** A conexão que se desenvolve entre o diretor de teatro e sua motorista é frequentemente elogiada, com muitos descrevendo como os dois se reconhecem em suas feridas e criam um espaço de confiança e cura mútua.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C011 · `drive-my-car` · Vale a pena · POS-C

> **Vale a pena se você** valoriza composições visuais simétricas e belas paisagens que refletem a solidão interior

- **chave:** `drive-my-car · vale_a_pena · POS-C`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-C — *Fotografia e estética*
- **o que o grupo diz:** A fotografia e a composição visual do filme são muito elogiadas, com destaque para os planos amplos, a simetria e a beleza das paisagens, que ajudam a transmitir a solidão e a introspecção dos personagens.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C013 · `drive-my-car` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com narrativas muito longas que parecem arrastadas e tediosas

- **chave:** `drive-my-car · talvez_evite · NEG-A`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-A — *Duração excessiva e ritmo lento*
- **o que o grupo diz:** Este grupo reclama que o filme se arrasta por quase três horas e que a duração não se justifica, tornando a experiência tediosa e cansativa.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C014 · `drive-my-car` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com atuações apáticas e excessiva contenção emocional que distanciam a história

- **chave:** `drive-my-car · talvez_evite · NEG-B`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-B — *Falta de emoção e atuações apáticas*
- **o que o grupo diz:** As reviews negativas apontam que os personagens parecem robóticos ou indiferentes, e que a contenção emocional impede qualquer conexão com a história.
- **rótulo de força (do código):** `muitos` (17 de 40 = 42%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C015 · `drive-my-car` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra com diálogos excessivamente extensos e uma estrutura narrativa confusa

- **chave:** `drive-my-car · talvez_evite · NEG-C`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-C — *Roteiro confuso e diálogos prolongados*
- **o que o grupo diz:** Este grupo critica a estrutura narrativa como confusa ou arrastada, com diálogos extensos que não acrescentam e momentos iniciais pouco claros.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C016 · `drive-my-car` · Talvez evite · NEG-E

> **Talvez evite se você** acha que belos visuais e fotografia caprichada não compensam a falta de envolvimento

- **chave:** `drive-my-car · talvez_evite · NEG-E`
- **filme:** Drive My Car (`drive-my-car`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-E — *Aspectos visuais elogiados, mas insuficientes*
- **o que o grupo diz:** As reviews negativas reconhecem a bela fotografia e o capricho visual, mas afirmam que isso não compensa a falta de envolvimento emocional ou de uma narrativa cativante.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C017 · `force-majeure-2014` · Vale a pena · POS-A

> **Vale a pena se você** busca um estudo sobre fragilidade masculina, culpa e vitimização

- **chave:** `force-majeure-2014 · vale_a_pena · POS-A`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~80% das notas
- **tema de origem:** POS-A — *Masculinidade frágil e ego masculino*
- **o que o grupo diz:** Várias reviews destacam como o filme examina a fragilidade masculina e o ego do homem, mostrando um personagem que não consegue assumir seus erros e transforma a própria culpa em vitimização.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C018 · `force-majeure-2014` · Vale a pena · POS-B

> **Vale a pena se você** aprecia reflexões sobre papéis de gênero e dinâmicas de casamento com ambiguidades

- **chave:** `force-majeure-2014 · vale_a_pena · POS-B`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~80% das notas
- **tema de origem:** POS-B — *Crítica aos papéis de gênero e ao casamento*
- **o que o grupo diz:** O grupo aponta que a obra levanta questões sobre papéis de gênero, expectativas sociais e a dinâmica do casamento, deixando o espectador em dúvida sobre quem está certo.
- **rótulo de força (do código):** `muitos` (11 de 40 = 28%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C019 · `force-majeure-2014` · Vale a pena · POS-C

> **Vale a pena se você** gosta de humor desconfortável nascido de situações de constrangimento e tensão

- **chave:** `force-majeure-2014 · vale_a_pena · POS-C`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~80% das notas
- **tema de origem:** POS-C — *Desconforto e humor incômodo*
- **o que o grupo diz:** Muitas reviews descrevem a experiência como desconfortável e ao mesmo tempo engraçada, com situações de constrangimento que geram riso nervoso e tensão.
- **rótulo de força (do código):** `muitos` (11 de 40 = 28%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C021 · `force-majeure-2014` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa de cenas longas, repetitivas e com ritmo arrastado

- **chave:** `force-majeure-2014 · talvez_evite · NEG-A`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-A — *Ritmo lento e duração excessiva*
- **o que o grupo diz:** Muitos espectadores relatam que o filme se arrasta, com cenas longas e repetitivas que tornam a experiência entediante, e que a duração poderia ser reduzida sem prejuízo.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C022 · `force-majeure-2014` · Talvez evite · NEG-B

> **Talvez evite se você** se irrita com personagens unidimensionais e reações infantilizadas no casal protagonista

- **chave:** `force-majeure-2014 · talvez_evite · NEG-B`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-B — *Personagens irritantes e falta de profundidade*
- **o que o grupo diz:** As críticas apontam que os personagens, especialmente o casal protagonista, são unidimensionais e suas reações soam exageradas ou infantilizadas, dificultando a conexão do público.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C023 · `force-majeure-2014` · Talvez evite · NEG-C

> **Talvez evite se você** rejeita discussões de gênero tratadas de modo simplista ou com estereótipos superficiais

- **chave:** `force-majeure-2014 · talvez_evite · NEG-C`
- **filme:** Força Maior (`force-majeure-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-C — *Mensagem sobre papéis de gênero e masculinidade frágil*
- **o que o grupo diz:** Vários comentários consideram que a abordagem das questões de gênero é simplista ou mal desenvolvida, ora acusando o filme de misoginia, ora de reforçar estereótipos de forma superficial.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C025 · `get-out-2017` · Vale a pena · POS-A

> **Vale a pena se você** busca uma abordagem inteligente e desconfortável sobre o racismo velado

- **chave:** `get-out-2017 · vale_a_pena · POS-A`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-A — *Comentário social e racismo*
- **o que o grupo diz:** As reviews positivas destacam que o filme aborda o racismo de forma inteligente, especialmente o racismo velado e disfarçado de elogios, educação e falsa aceitação, tornando a experiência desconfortável e assustadora.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C026 · `get-out-2017` · Vale a pena · POS-B

> **Vale a pena se você** valoriza atuações intensas e críveis no centro da narrativa

- **chave:** `get-out-2017 · vale_a_pena · POS-B`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-B — *Atuações*
- **o que o grupo diz:** Este grupo elogia as atuações, com destaque para Daniel Kaluuya e Allison Williams, que entregam performances intensas e críveis.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C029 · `get-out-2017` · Talvez evite · NEG-B

> **Talvez evite se você** se desaponta com narrativas arrastadas de introdução longa e pouca tensão

- **chave:** `get-out-2017 · talvez_evite · NEG-B`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-B — *Ritmo lento e falta de tensão*
- **o que o grupo diz:** Alguns espectadores consideram o filme excessivamente lento, com uma introdução longa e sem cenas que gerem medo ou tensão real, tornando a narrativa arrastada.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C031 · `get-out-2017` · Talvez evite · NEG-D

> **Talvez evite se você** rejeita roteiros com mensagens pouco sutis e abordagem simplista do racismo

- **chave:** `get-out-2017 · talvez_evite · NEG-D`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-D — *Crítica ao roteiro e à abordagem do racismo*
- **o que o grupo diz:** Algumas reviews criticam o roteiro por ser simplista, maniqueísta ou por não aprofundar bem o tema do racismo, resultando em uma mensagem pouco sutil.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** par obrigatório
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C032 · `get-out-2017` · Talvez evite · NEG-E

> **Talvez evite se você** se incomoda com um elenco irregular marcado por performances fracas ou deslocadas

- **chave:** `get-out-2017 · talvez_evite · NEG-E`
- **filme:** Corra! (`get-out-2017`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-E — *Atuações irregulares*
- **o que o grupo diz:** Há comentários sobre atuações fracas ou deslocadas, com exceção de alguns atores como Daniel Kaluuya, que se destacam em meio a um elenco considerado irregular.
- **rótulo de força (do código):** `alguns` (7 de 40 = 18%)
- **como entrou:** par obrigatório
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C033 · `guillermo-del-toros-pinocchio` · Vale a pena · POS-A

> **Vale a pena se você** admira animação em stop-motion detalhada com cenários criativos e ricos em textura

- **chave:** `guillermo-del-toros-pinocchio · vale_a_pena · POS-A`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-A — *Animação em stop-motion e design visual*
- **o que o grupo diz:** As reviews elogiam a técnica de stop-motion como impressionante e detalhada, com design de personagens e cenários ricos em textura e criatividade, fazendo cada cena parecer uma obra de arte.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C036 · `guillermo-del-toros-pinocchio` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com um ritmo excessivamente lento e uma condução arrastada

- **chave:** `guillermo-del-toros-pinocchio · talvez_evite · NEG-A`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-A — *Ritmo lento e arrastado*
- **o que o grupo diz:** Várias reviews negativas reclamam que o filme é excessivamente lento, com ritmo arrastado e se arrastando, o que torna a experiência cansativa e difícil de terminar.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C037 · `guillermo-del-toros-pinocchio` · Talvez evite · NEG-B

> **Talvez evite se você** se irrita com um protagonista malcriado, egoísta e de tom estridente

- **chave:** `guillermo-del-toros-pinocchio · talvez_evite · NEG-B`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-B — *Pinóquio irritante e personagem desagradável*
- **o que o grupo diz:** O protagonista é descrito como insuportável, egoísta e malcriado, com uma voz estridente que contribui para a antipatia.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C039 · `guillermo-del-toros-pinocchio` · Talvez evite · NEG-E

> **Talvez evite se você** se desagrada com design visual perturbador e personagens de aparência incômoda

- **chave:** `guillermo-del-toros-pinocchio · talvez_evite · NEG-E`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-E — *Design visual e animação feios ou perturbadores*
- **o que o grupo diz:** Apesar da técnica impressionante, o visual é considerado feio, perturbador ou sem vida, com personagens de aparência desagradável.
- **rótulo de força (do código):** `alguns` (8 de 40 = 20%)
- **como entrou:** par obrigatório
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C040 · `guillermo-del-toros-pinocchio` · Talvez evite · NEG-F

> **Talvez evite se você** se frustra com uma história mal construída e subtramas sem foco

- **chave:** `guillermo-del-toros-pinocchio · talvez_evite · NEG-F`
- **filme:** Pinóquio por Guillermo del Toro (`guillermo-del-toros-pinocchio`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-F — *Enredo confuso e mal desenvolvido*
- **o que o grupo diz:** A história é vista como mal construída, com subtramas mal elaboradas e desenvolvimento fraco, resultando em uma narrativa sem foco.
- **rótulo de força (do código):** `alguns` (8 de 40 = 20%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C041 · `happy-hour-2015-1` · Vale a pena · POS-A

> **Vale a pena se você** aprecia uma longa duração contemplativa que proporciona imersão na vida das personagens

- **chave:** `happy-hour-2015-1 · vale_a_pena · POS-A`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~91% das notas
- **tema de origem:** POS-A — *Duração longa e ritmo contemplativo*
- **o que o grupo diz:** Muitas reviews destacam que, apesar das mais de cinco horas, o filme não parece arrastado; a duração é sentida como uma imersão que permite acompanhar a vida das personagens com naturalidade e até deixa vontade de que durasse mais.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C044 · `happy-hour-2015-1` · Vale a pena · POS-D

> **Vale a pena se você** se interessa por diálogos naturais e filosóficos que revelam tensões e significados ocultos

- **chave:** `happy-hour-2015-1 · vale_a_pena · POS-D`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~91% das notas
- **tema de origem:** POS-D — *Diálogos e conversas como motor narrativo*
- **o que o grupo diz:** O texto elogia a escrita dos diálogos, que soam naturais e filosóficos sem perder a mundaneidade, e a maneira como as conversas revelam camadas de significado e tensões não ditas.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C045 · `happy-hour-2015-1` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com filmes muito extensos de andamento lento e cenas arrastadas

- **chave:** `happy-hour-2015-1 · talvez_evite · NEG-A`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-A — *Duração excessiva e ritmo lento*
- **o que o grupo diz:** Muitas reviews criticam a longa duração de mais de cinco horas, considerando-a desnecessária e arrastada, com cenas que poderiam ser encurtadas sem prejuízo.
- **rótulo de força (do código):** `a maioria` (30 de 40 = 75%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C046 · `happy-hour-2015-1` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com figuras apáticas, diálogos pouco naturais e falta de conexão emocional

- **chave:** `happy-hour-2015-1 · talvez_evite · NEG-B`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-B — *Personagens apáticos e sem carisma*
- **o que o grupo diz:** Várias reviews apontam que os personagens são difíceis de se conectar, parecendo vazios, sem emoção e com diálogos pouco naturais.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C047 · `happy-hour-2015-1` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra com narrativas sem foco dispersas em subtramas consideradas desnecessárias

- **chave:** `happy-hour-2015-1 · talvez_evite · NEG-C`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-C — *Roteiro arrastado e falta de substância*
- **o que o grupo diz:** Algumas críticas mencionam que a história se perde em subtramas irrelevantes e não justifica o tempo investido, com uma narrativa sem foco.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C048 · `happy-hour-2015-1` · Talvez evite · NEG-D

> **Talvez evite se você** se desaponta com atuações inexpressivas e desempenhos que parecem desinteressados

- **chave:** `happy-hour-2015-1 · talvez_evite · NEG-D`
- **filme:** Happy Hour (`happy-hour-2015-1`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~2% das notas
- **tema de origem:** NEG-D — *Atuações fracas ou inexpressivas*
- **o que o grupo diz:** Certas reviews destacam que a atuação parece desinteressada e sem expressão, prejudicando a imersão na história.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C049 · `hard-to-be-a-god` · Vale a pena · POS-A

> **Vale a pena se você** busca uma imersão tátil em um universo denso e ricamente detalhado

- **chave:** `hard-to-be-a-god · vale_a_pena · POS-A`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~73% das notas
- **tema de origem:** POS-A — *Imersão sensorial e worldbuilding*
- **o que o grupo diz:** As reviews destacam que o filme cria um mundo tão denso e tátil que o espectador sente como se tivesse sido transportado para dentro dele, com cenários, figurinos e detalhes que transbordam a tela e tornam a experiência quase documental.
- **rótulo de força (do código):** `a maioria` (30 de 40 = 75%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C050 · `hard-to-be-a-god` · Vale a pena · POS-B

> **Vale a pena se você** se interessa por uma estética visceral e crua que provoca fascínio e repulsa

- **chave:** `hard-to-be-a-god · vale_a_pena · POS-B`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~73% das notas
- **tema de origem:** POS-B — *Sujeira, imundície e repulsa*
- **o que o grupo diz:** Muitas reviews enfatizam a presença constante de lama, excrementos, sangue e outras sujeiras, descrevendo o filme como repulsivo e ao mesmo tempo fascinante, com uma estética que provoca desde nojo até necessidade de banho após a sessão.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C051 · `hard-to-be-a-god` · Vale a pena · POS-C

> **Vale a pena se você** aceita o desafio de encarar uma narrativa fragmentada que não oferece facilidades

- **chave:** `hard-to-be-a-god · vale_a_pena · POS-C`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~73% das notas
- **tema de origem:** POS-C — *Narrativa confusa e difícil de acompanhar*
- **o que o grupo diz:** Este grupo aponta que a trama é fragmentada e praticamente incompreensível, exigindo paciência ou pesquisa externa para ser minimamente entendida, e que o filme não se esforça para facilitar o acompanhamento.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C052 · `hard-to-be-a-god` · Vale a pena · POS-D

> **Vale a pena se você** aprecia planos longos e fotografia em preto e branco com câmera intrusiva

- **chave:** `hard-to-be-a-god · vale_a_pena · POS-D`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~73% das notas
- **tema de origem:** POS-D — *Fotografia e direção marcantes*
- **o que o grupo diz:** As reviews elogiam a fotografia em preto e branco, os planos longos e a câmera que se move de forma inquieta e intrusiva, criando uma sensação de claustrofobia e imersão que muitos consideram uma conquista técnica e artística.
- **rótulo de força (do código):** `muitos` (20 de 40 = 50%)
- **como entrou:** par obrigatório
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C053 · `hard-to-be-a-god` · Vale a pena · POS-F

> **Vale a pena se você** tolera uma longa duração e andamento lento em troca de maior imersão

- **chave:** `hard-to-be-a-god · vale_a_pena · POS-F`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~73% das notas
- **tema de origem:** POS-F — *Duração e ritmo desafiadores*
- **o que o grupo diz:** Algumas reviews comentam que as quase três horas de projeção e o ritmo lento tornam a experiência cansativa e exigem esforço, embora esse mesmo aspecto seja visto por outras como parte da imersão proposta pelo filme.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C054 · `hard-to-be-a-god` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com o excesso de sujeira e fluidos corporais de teor repulsivo

- **chave:** `hard-to-be-a-god · talvez_evite · NEG-A`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-A — *Imundície e nojo excessivos*
- **o que o grupo diz:** As reviews negativas reclamam que o filme é dominado por sujeira, excrementos, vômitos e outros fluidos corporais, usados de forma gratuita e repetitiva, tornando a experiência repulsiva em vez de artística.
- **rótulo de força (do código):** `a maioria` (28 de 40 = 70%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C055 · `hard-to-be-a-god` · Talvez evite · NEG-B

> **Talvez evite se você** se cansa com narrativas longas de andamento arrastado e cenas repetitivas

- **chave:** `hard-to-be-a-god · talvez_evite · NEG-B`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-B — *Ritmo lento e duração excessiva*
- **o que o grupo diz:** Muitos espectadores consideram o ritmo arrastado e a longa duração um teste de paciência, sem recompensa narrativa, com cenas que parecem se repetir indefinidamente.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C056 · `hard-to-be-a-god` · Talvez evite · NEG-C

> **Talvez evite se você** rejeita histórias sem fio condutor claro, com diálogos incoerentes e eventos desconexos

- **chave:** `hard-to-be-a-god · talvez_evite · NEG-C`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-C — *Roteiro confuso e sem coesão*
- **o que o grupo diz:** A falta de uma linha narrativa clara e a sensação de que a história não vai a lugar algum são críticas frequentes, com diálogos incoerentes e eventos aleatórios.
- **rótulo de força (do código):** `muitos` (19 de 40 = 48%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C057 · `hard-to-be-a-god` · Talvez evite · NEG-F

> **Talvez evite se você** acha que apuro técnico e visual não compensam uma experiência desagradável e tediosa

- **chave:** `hard-to-be-a-god · talvez_evite · NEG-F`
- **filme:** É Difícil Ser Um Deus (`hard-to-be-a-god`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-F — *Cinematografia e design de produção elogiados, mas não salvam*
- **o que o grupo diz:** Apesar de reconhecerem a qualidade técnica e a construção de mundo, os críticos afirmam que isso não compensa a experiência desagradável e tediosa.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** par obrigatório
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C058 · `memories-of-murder` · Vale a pena · POS-A

> **Vale a pena se você** aprecia atuações fortes e personagens moralmente ambíguos que se desgastam na trama

- **chave:** `memories-of-murder · vale_a_pena · POS-A`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~94% das notas
- **tema de origem:** POS-A — *Atuações e personagens complexos*
- **o que o grupo diz:** As atuações são elogiadas e os detetives são descritos como personagens moralmente ambíguos, cujas personalidades e métodos se desgastam ao longo da trama.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C059 · `memories-of-murder` · Vale a pena · POS-B

> **Vale a pena se você** valoriza uma fotografia expressiva com atmosfera sombria e visual opressivo

- **chave:** `memories-of-murder · vale_a_pena · POS-B`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~94% das notas
- **tema de origem:** POS-B — *Fotografia e atmosfera*
- **o que o grupo diz:** A fotografia, a paleta de cores e a construção de atmosfera sombria e opressiva são frequentemente destacadas como pontos altos.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C060 · `memories-of-murder` · Vale a pena · POS-C

> **Vale a pena se você** aceita um início compassado em favor de uma tensão crescente e bem conduzida

- **chave:** `memories-of-murder · vale_a_pena · POS-C`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~94% das notas
- **tema de origem:** POS-C — *Ritmo e duração*
- **o que o grupo diz:** O ritmo é percebido como lento no início, mas a tensão crescente e a boa condução fazem com que a duração prolongada não seja um problema.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C061 · `memories-of-murder` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com um ritmo excessivamente lento e trechos que parecem não avançar

- **chave:** `memories-of-murder · talvez_evite · NEG-A`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-A — *Ritmo lento e arrastado*
- **o que o grupo diz:** Várias reviews deste grupo reclamam que o filme é excessivamente lento, com longos trechos em que nada parece avançar, tornando a experiência entediante e difícil de acompanhar até o fim.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C062 · `memories-of-murder` · Talvez evite · NEG-B

> **Talvez evite se você** rejeita toques cômicos ou humor físico em meio a uma investigação brutal

- **chave:** `memories-of-murder · talvez_evite · NEG-B`
- **filme:** Memórias de um Assassino (`memories-of-murder`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-B — *Tom de comédia deslocado*
- **o que o grupo diz:** Este grupo critica a mistura de humor com a investigação séria, dizendo que as piadas e momentos cômicos, como quedas e chutes, quebram a tensão e soam inadequadas diante da brutalidade dos crimes.
- **rótulo de força (do código):** `muitos` (11 de 40 = 28%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C064 · `neighboring-sounds` · Vale a pena · POS-A

> **Vale a pena se você** aprecia o desenho de som e ruídos ambientais usados para gerar tensão

- **chave:** `neighboring-sounds · vale_a_pena · POS-A`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~77% das notas
- **tema de origem:** POS-A — *Uso do som e da trilha sonora como elemento narrativo*
- **o que o grupo diz:** As reviews destacam que o som e os ruídos ambientais são usados de forma magistral para criar tensão e desconforto, funcionando quase como um personagem e sendo parte essencial da experiência.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C065 · `neighboring-sounds` · Vale a pena · POS-B

> **Vale a pena se você** busca reflexões contundentes sobre desigualdade social e dinâmicas de classe no cotidiano

- **chave:** `neighboring-sounds · vale_a_pena · POS-B`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~77% das notas
- **tema de origem:** POS-B — *Crítica social e desigualdade de classe*
- **o que o grupo diz:** O filme é elogiado por retratar de maneira sutil e contundente as relações de classe, a desigualdade social e o legado escravocrata, expondo hierarquias e privilégios presentes no cotidiano.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C066 · `neighboring-sounds` · Vale a pena · POS-C

> **Vale a pena se você** valoriza narrativas fragmentadas que retratam a rotina e o cotidiano de moradores

- **chave:** `neighboring-sounds · vale_a_pena · POS-C`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~77% das notas
- **tema de origem:** POS-C — *Retrato do cotidiano e da vida em comunidade*
- **o que o grupo diz:** A narrativa fragmentada que acompanha diversos moradores e suas rotinas é vista como um retrato realista e envolvente da vida em um bairro de classe média, valorizando pequenos momentos do dia a dia.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C067 · `neighboring-sounds` · Vale a pena · POS-D

> **Vale a pena se você** gosta de uma atmosfera de suspense com constante sensação de ameaça iminente

- **chave:** `neighboring-sounds · vale_a_pena · POS-D`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~77% das notas
- **tema de origem:** POS-D — *Construção de tensão e atmosfera de suspense*
- **o que o grupo diz:** As críticas ressaltam a habilidade do diretor em criar uma atmosfera de constante apreensão, com uma sensação de ameaça iminente que percorre todo o filme, mesmo em cenas aparentemente banais.
- **rótulo de força (do código):** `muitos` (11 de 40 = 28%)
- **como entrou:** par obrigatório
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C068 · `neighboring-sounds` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com um ritmo arrastado em que as cenas demoram a avançar

- **chave:** `neighboring-sounds · talvez_evite · NEG-A`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-A — *Ritmo lento e arrastado*
- **o que o grupo diz:** O espectador relata que o filme se estende por duas horas que parecem uma eternidade, com cenas que demoram a avançar e uma sensação constante de que nada acontece, tornando a experiência cansativa e por vezes entediante.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C069 · `neighboring-sounds` · Talvez evite · NEG-B

> **Talvez evite se você** espera um debate social aprofundado e rejeita abordagens excessivamente sutis ou superficiais

- **chave:** `neighboring-sounds · talvez_evite · NEG-B`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-B — *Crítica social superficial*
- **o que o grupo diz:** As reviews apontam que a obra tenta discutir desigualdade de classes e herança escravocrata, mas o faz de forma sutil demais ou rasteira, sem aprofundamento, com os temas ficando apenas nas entrelinhas ou em lampejos superficiais.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C070 · `neighboring-sounds` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra com estruturas fragmentadas que deixam subtramas desconexas e sem resolução

- **chave:** `neighboring-sounds · talvez_evite · NEG-C`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-C — *Narrativa confusa e fragmentada*
- **o que o grupo diz:** Vários comentários mencionam que a história é difícil de acompanhar, com cenas desconexas, subtramas que não se amarram e uma estrutura que parece sugerir sem nunca chegar a um ponto claro.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C071 · `neighboring-sounds` · Talvez evite · NEG-D

> **Talvez evite se você** prioriza figuras carismáticas e se ressente de personagens com pouco desenvolvimento

- **chave:** `neighboring-sounds · talvez_evite · NEG-D`
- **filme:** O Som ao Redor (`neighboring-sounds`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-D — *Personagens rasos e chatos*
- **o que o grupo diz:** Algumas críticas destacam que os personagens são pouco desenvolvidos, sem carisma ou profundidade, o que dificulta a conexão do público e deixa a experiência ainda mais arrastada.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C073 · `pinocchio-2022` · Vale a pena · POS-B

> **Vale a pena se você** aprecia cenários detalhados e efeitos digitais, apesar de ocasionais estranhezas visuais

- **chave:** `pinocchio-2022 · vale_a_pena · POS-B`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~15% das notas
- **tema de origem:** POS-B — *Efeitos visuais e design de produção*
- **o que o grupo diz:** O CGI e o design de produção são elogiados por sua qualidade, com cenários detalhados e personagens visualmente cativantes, embora alguns apontem estranhezas no visual.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C074 · `pinocchio-2022` · Vale a pena · POS-C

> **Vale a pena se você** valoriza atuações carismáticas e emotivas do elenco principal

- **chave:** `pinocchio-2022 · vale_a_pena · POS-C`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~15% das notas
- **tema de origem:** POS-C — *Atuações do elenco*
- **o que o grupo diz:** As atuações, especialmente as de Tom Hanks, Benjamin Evan Ainsworth e Cynthia Erivo, recebem elogios por sua emotividade e carisma, apesar de algumas críticas isoladas.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C076 · `pinocchio-2022` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com produções calculadas que substituem o encanto por frieza digital

- **chave:** `pinocchio-2022 · talvez_evite · NEG-A`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~60% das notas
- **tema de origem:** NEG-A — *Falta de alma e artificialidade*
- **o que o grupo diz:** Muitas reviews descrevem o filme como uma produção sem alma, oca e puramente comercial, que substitui o encanto e a magia do original por uma estética digital fria e calculada.
- **rótulo de força (do código):** `a maioria` (28 de 40 = 70%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C077 · `pinocchio-2022` · Talvez evite · NEG-B

> **Talvez evite se você** rejeita efeitos visuais excessivos e personagens computadorizados sem vida

- **chave:** `pinocchio-2022 · talvez_evite · NEG-B`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~60% das notas
- **tema de origem:** NEG-B — *CGI e efeitos visuais ruins*
- **o que o grupo diz:** Os efeitos gerados por computador são criticados como feios, mal feitos e excessivos, com personagens digitais que parecem deslocados e sem vida, prejudicando a imersão.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C079 · `pinocchio-2022` · Talvez evite · NEG-D

> **Talvez evite se você** se decepciona com atuações afetadas ou desempenhos apáticos do elenco

- **chave:** `pinocchio-2022 · talvez_evite · NEG-D`
- **filme:** Pinóquio (`pinocchio-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~60% das notas
- **tema de origem:** NEG-D — *Atuação de Tom Hanks e elenco*
- **o que o grupo diz:** A atuação de Tom Hanks é vista como esforçada, mas equivocada, com um sotaque instável e exageros que não convencem, enquanto o restante do elenco é considerado apático ou mal utilizado.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** par obrigatório
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C081 · `satantango` · Vale a pena · POS-A

> **Vale a pena se você** aprecia uma imersão profunda construída por um ritmo deliberadamente lento e duração extensa

- **chave:** `satantango · vale_a_pena · POS-A`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~88% das notas
- **tema de origem:** POS-A — *Duração e ritmo lento*
- **o que o grupo diz:** A longa duração de sete horas e meia e o ritmo deliberadamente lento são vistos como essenciais para a experiência imersiva, embora alguns considerem que poderia ser encurtado sem perder o impacto.
- **rótulo de força (do código):** `a maioria` (25 de 40 = 62%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C083 · `satantango` · Vale a pena · POS-C

> **Vale a pena se você** se atrai por ambientações melancólicas que exploram desolação, pobreza e abandono

- **chave:** `satantango · vale_a_pena · POS-C`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~88% das notas
- **tema de origem:** POS-C — *Atmosfera opressiva e miséria*
- **o que o grupo diz:** A ambientação melancólica e a representação da pobreza e do abandono são destacadas como centrais para a obra, transmitindo uma sensação de desolação e estagnação.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C084 · `satantango` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa de narrativas extremamente longas com ritmo arrastado e cenas prolongadas

- **chave:** `satantango · talvez_evite · NEG-A`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-A — *Duração excessiva e ritmo lento*
- **o que o grupo diz:** As reviews negativas criticam a duração de mais de sete horas, considerando-a injustificada e arrastada, com cenas que se estendem sem propósito e poderiam ser reduzidas drasticamente.
- **rótulo de força (do código):** `quase todos` (38 de 40 = 95%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C085 · `satantango` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com histórias de pouco desenvolvimento onde longos trechos parecem vazios

- **chave:** `satantango · talvez_evite · NEG-B`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-B — *Falta de conteúdo narrativo e tédio*
- **o que o grupo diz:** Este grupo destaca que a história é vazia, sem desenvolvimento significativo, e que o tédio predomina, com longos trechos em que nada acontece.
- **rótulo de força (do código):** `a maioria` (30 de 40 = 75%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C086 · `satantango` · Talvez evite · NEG-C

> **Talvez evite se você** tem repulsa a cenas consideradas cruéis envolvendo animais

- **chave:** `satantango · talvez_evite · NEG-C`
- **filme:** O Tango de Satã (`satantango`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-C — *Cena de animal e crueldade*
- **o que o grupo diz:** Várias reviews negativas condenam uma cena envolvendo um animal, considerada cruel e desnecessária, que prejudica a experiência e gera repulsa.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C088 · `speak-no-evil-2022` · Vale a pena · POS-B

> **Vale a pena se você** se interessa por tensões geradas pela excessiva gentileza e passividade dos protagonistas

- **chave:** `speak-no-evil-2022 · vale_a_pena · POS-B`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~61% das notas
- **tema de origem:** POS-B — *Passividade e excesso de gentileza dos protagonistas*
- **o que o grupo diz:** Este grupo critica a dificuldade dos personagens em dizer não e a tendência a ceder para não parecer indelicados, o que os coloca em situações cada vez mais desconfortáveis.
- **rótulo de força (do código):** `muitos` (17 de 40 = 42%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C090 · `speak-no-evil-2022` · Talvez evite · NEG-A

> **Talvez evite se você** se irrita com personagens que tomam decisões absurdas sem instinto de autopreservação

- **chave:** `speak-no-evil-2022 · talvez_evite · NEG-A`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-A — *Personagens burros e sem instinto de sobrevivência*
- **o que o grupo diz:** Os personagens tomam decisões idiotas atrás de idiotas, sem qualquer instinto de autopreservação, o que torna a história inacreditável e irritante.
- **rótulo de força (do código):** `a maioria` (30 de 40 = 75%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C091 · `speak-no-evil-2022` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com tramas dependentes de coincidências e atitudes forçadas para avançar

- **chave:** `speak-no-evil-2022 · talvez_evite · NEG-B`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-B — *Roteiro forçado e ilógico*
- **o que o grupo diz:** A trama depende de coincidências e ações sem sentido para avançar, parecendo que os personagens agem apenas para cumprir as exigências do roteiro.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C093 · `speak-no-evil-2022` · Talvez evite · NEG-E

> **Talvez evite se você** procura um suspense dinâmico e rejeita narrativas de ritmo monótono e previsível

- **chave:** `speak-no-evil-2022 · talvez_evite · NEG-E`
- **filme:** Não Fale o Mal (`speak-no-evil-2022`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~11% das notas
- **tema de origem:** NEG-E — *Ritmo arrastado e falta de tensão*
- **o que o grupo diz:** O filme demora a engrenar e, quando tenta criar suspense, soa monótono e previsível, sem gerar medo ou ansiedade reais.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C094 · `the-cloud-capped-star` · Vale a pena · POS-A

> **Vale a pena se você** busca atuações autênticas comoventes e personagens construídos com grande força emocional

- **chave:** `the-cloud-capped-star · vale_a_pena · POS-A`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-A — *Atuação e personagens*
- **o que o grupo diz:** As reviews elogiam a atuação de Supriya Choudhury como Neeta e a caracterização dos personagens, destacando a força emocional e a autenticidade das performances.
- **rótulo de força (do código):** `muitos` (20 de 40 = 50%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C095 · `the-cloud-capped-star` · Vale a pena · POS-B

> **Vale a pena se você** aprecia efeitos sonoros expressivos e música tradicional integrados à atmosfera da história

- **chave:** `the-cloud-capped-star · vale_a_pena · POS-B`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-B — *Trilha sonora e desenho de som*
- **o que o grupo diz:** O uso da música tradicional e os efeitos sonoros expressivos, como estalos e chicotadas, são frequentemente citados como elementos que amplificam o impacto emocional e a atmosfera do filme.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C096 · `the-cloud-capped-star` · Vale a pena · POS-C

> **Vale a pena se você** valoriza fotografia em preto e branco com uso expressivo de luz e sombra

- **chave:** `the-cloud-capped-star · vale_a_pena · POS-C`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-C — *Fotografia e composição visual*
- **o que o grupo diz:** A fotografia em preto e branco, com enquadramentos cuidadosos e uso expressivo de luz e sombra, é destacada como um dos pontos altos, criando imagens marcantes e simbólicas.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C098 · `the-cloud-capped-star` · Vale a pena · POS-F

> **Vale a pena se você** tolera um andamento vagaroso e desafiador em favor de uma experiência recompensadora

- **chave:** `the-cloud-capped-star · vale_a_pena · POS-F`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~87% das notas
- **tema de origem:** POS-F — *Ritmo e duração*
- **o que o grupo diz:** Algumas reviews mencionam que o ritmo é lento e que a duração pode ser um desafio, embora a experiência compense.
- **rótulo de força (do código):** `alguns` (5 de 40 = 12%)
- **como entrou:** par obrigatório
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C099 · `the-cloud-capped-star` · Talvez evite · NEG-A

> **Talvez evite se você** se desgasta com melodramas focados no acúmulo repetitivo de sofrimento da protagonista

- **chave:** `the-cloud-capped-star · talvez_evite · NEG-A`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-A — *Melodrama excessivo e acúmulo de sofrimento*
- **o que o grupo diz:** As reviews negativas criticam o filme por ser um melodrama que insiste em empilhar desgraças sobre a protagonista, tornando a narrativa repetitiva e arrastada.
- **rótulo de força (do código):** `a maioria` (20 de 27 = 74%)
- **como entrou:** base · amostra do grupo PEQUENA
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C100 · `the-cloud-capped-star` · Talvez evite · NEG-B

> **Talvez evite se você** se frustra com ritmos excessivamente lentos que parecem se arrastar sem avanços

- **chave:** `the-cloud-capped-star · talvez_evite · NEG-B`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-B — *Ritmo lento e duração excessiva*
- **o que o grupo diz:** Muitos espectadores consideram o ritmo extremamente lento e a duração de duas horas excessiva, com momentos que parecem se arrastar sem avanço significativo.
- **rótulo de força (do código):** `cerca de metade` (15 de 27 = 56%)
- **como entrou:** base · amostra do grupo PEQUENA
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C101 · `the-cloud-capped-star` · Talvez evite · NEG-C

> **Talvez evite se você** se incomoda com atuações teatrais exageradas e falta de nuance nas interpretações

- **chave:** `the-cloud-capped-star · talvez_evite · NEG-C`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-C — *Atuações fracas ou exageradas*
- **o que o grupo diz:** As atuações são frequentemente descritas como exageradas, teatrais ou sem nuance, com destaque para críticas à falta de expressividade da protagonista.
- **rótulo de força (do código):** `muitos` (12 de 27 = 44%)
- **como entrou:** base · amostra do grupo PEQUENA
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C102 · `the-cloud-capped-star` · Talvez evite · NEG-E

> **Talvez evite se você** se incomoda com inserções musicais irritantes ou transições sonoras com cortes abruptos

- **chave:** `the-cloud-capped-star · talvez_evite · NEG-E`
- **filme:** Estrela Encoberta de Nuvens (`the-cloud-capped-star`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~3% das notas
- **tema de origem:** NEG-E — *Música e trilha sonora incômodas*
- **o que o grupo diz:** A trilha sonora e as canções são apontadas como irritantes ou mal inseridas, com cortes abruptos que prejudicam a experiência.
- **rótulo de força (do código):** `muitos` (9 de 27 = 33%)
- **como entrou:** par obrigatório · amostra do grupo PEQUENA
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C103 · `the-second-mother` · Vale a pena · POS-A

> **Vale a pena se você** aprecia dramas que retratam hierarquias sociais e barreiras invisíveis no ambiente doméstico

- **chave:** `the-second-mother · vale_a_pena · POS-A`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-A — *Desigualdade social e crítica de classe*
- **o que o grupo diz:** As reviews deste grupo elogiam como o filme expõe a desigualdade brasileira e as barreiras invisíveis entre patrões e empregados, tratando o ambiente doméstico como um retrato das hierarquias sociais do país.
- **rótulo de força (do código):** `a maioria` (28 de 40 = 70%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C104 · `the-second-mother` · Vale a pena · POS-B

> **Vale a pena se você** se interessa por críticas ao paternalismo que mascara a subalternidade nas relações domésticas

- **chave:** `the-second-mother · vale_a_pena · POS-B`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-B — *Classismo e falsa ideia de 'quase da família'*
- **o que o grupo diz:** Várias reviews destacam como o discurso de que a empregada é praticamente da família funciona apenas enquanto ela mantém o lugar subalterno que lhe é reservado, revelando um paternalismo que mascara a exploração.
- **rótulo de força (do código):** `muitos` (19 de 40 = 48%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C106 · `the-second-mother` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com narrativas de andamento excessivamente vagaroso e cenas longas

- **chave:** `the-second-mother · talvez_evite · NEG-A`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-A — *Ritmo lento e arrastado*
- **o que o grupo diz:** Várias pessoas descrevem o filme como excessivamente devagar e entediante, com cenas longas que diluem o conflito e tornam a experiência cansativa, fazendo alguns até cochilarem.
- **rótulo de força (do código):** `muitos` (11 de 40 = 28%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C107 · `the-second-mother` · Talvez evite · NEG-B

> **Talvez evite se você** se incomoda com roteiros de progressão frouxa e situações sem desenvolvimento claro

- **chave:** `the-second-mother · talvez_evite · NEG-B`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-B — *Roteiro fraco e desenvolvimento inconsistente*
- **o que o grupo diz:** O texto é criticado por ser mal construído, sem nexo ou progressão clara, com situações jogadas sem desenvolvimento e uma sensação de que a história não vai a lugar nenhum.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C108 · `the-second-mother` · Talvez evite · NEG-C

> **Talvez evite se você** rejeita comentários sociais abordados de forma didática, maniqueísta ou simplificada

- **chave:** `the-second-mother · talvez_evite · NEG-C`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-C — *Crítica social panfletária e simplista*
- **o que o grupo diz:** Alguns espectadores consideram que a mensagem sobre desigualdade é importante, mas entregue de forma didática e maniqueísta, tratando questões complexas como preto no branco e subestimando a inteligência da plateia.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C109 · `the-second-mother` · Talvez evite · NEG-D

> **Talvez evite se você** se afasta de histórias com figuras caricatas, estereotipadas ou de atitudes irritantes

- **chave:** `the-second-mother · talvez_evite · NEG-D`
- **filme:** Que Horas Ela Volta? (`the-second-mother`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-D — *Personagens irritantes e estereotipados*
- **o que o grupo diz:** A filha da protagonista é frequentemente descrita como insuportável e folgada, enquanto outros personagens soam como caricaturas e estereótipos, o que afasta o envolvimento com a história.
- **rótulo de força (do código):** `alguns` (8 de 40 = 20%)
- **como entrou:** par obrigatório
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C110 · `the-turin-horse` · Vale a pena · POS-A

> **Vale a pena se você** busca uma experiência imersiva e hipnótica construída pelo ritmo lento e rotinas repetitivas

- **chave:** `the-turin-horse · vale_a_pena · POS-A`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-A — *Ritmo lento e repetição intencional*
- **o que o grupo diz:** Várias reviews positivas destacam que a lentidão e a repetição das rotinas não são defeitos, mas escolhas deliberadas que criam uma experiência imersiva e hipnótica, forçando o espectador a sentir o peso da existência.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C111 · `the-turin-horse` · Vale a pena · POS-B

> **Vale a pena se você** aprecia uma fotografia austera em preto e branco com planos-sequência longos e pictóricos

- **chave:** `the-turin-horse · vale_a_pena · POS-B`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-B — *Fotografia em preto e branco e planos longos*
- **o que o grupo diz:** A fotografia em preto e branco de textura rica e os longos planos sequências são frequentemente elogiados como elementos que conferem uma beleza austera e quase pictórica ao filme.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C112 · `the-turin-horse` · Vale a pena · POS-C

> **Vale a pena se você** se interessa por reflexões sobre o niilismo, o vazio existencial e a desesperança

- **chave:** `the-turin-horse · vale_a_pena · POS-C`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-C — *Nihilismo e peso da existência*
- **o que o grupo diz:** Muitas reviews associam o filme a uma profunda reflexão sobre o nihilismo, a falta de sentido e a dureza da vida, descrevendo-o como uma obra que transmite desesperança e vazio existencial.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `tom_atmosfera`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C113 · `the-turin-horse` · Vale a pena · POS-D

> **Vale a pena se você** valoriza uma trilha sonora hipnótica combinada ao som constante do vento opressivo

- **chave:** `the-turin-horse · vale_a_pena · POS-D`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~85% das notas
- **tema de origem:** POS-D — *Trilha sonora marcante e som ambiente*
- **o que o grupo diz:** A trilha sonora hipnótica e o som constante do vento são citados como componentes essenciais que amplificam a atmosfera opressiva e a monotonia da experiência.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** par obrigatório
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C115 · `the-turin-horse` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com narrativas arrastadas e repetições de ações cotidianas sem propósito claro

- **chave:** `the-turin-horse · talvez_evite · NEG-A`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-A — *Ritmo excessivamente lento e tedioso*
- **o que o grupo diz:** As críticas deste grupo descrevem a experiência de assistir ao filme como arrastada e entediante, com cenas que se estendem sem propósito claro, levando alguns a acelerar a reprodução ou até desistir no meio. A repetição de ações cotidianas sem variação significativa é apontada como um fator que torna a obra difícil de suportar.
- **rótulo de força (do código):** `quase todos` (38 de 40 = 95%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C116 · `the-turin-horse` · Talvez evite · NEG-B

> **Talvez evite se você** prefere histórias com arcos narrativos claros, diálogos frequentes e personagens com profundidade emocional

- **chave:** `the-turin-horse · talvez_evite · NEG-B`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-B — *Falta de enredo e desenvolvimento de personagens*
- **o que o grupo diz:** Muitas reviews afirmam que o filme carece de uma história envolvente, com personagens sem profundidade ou motivações que despertem interesse. A ausência de diálogos e de arcos narrativos claros faz com que a experiência pareça vazia e monótona, sem nada para se apegar emocionalmente.
- **rótulo de força (do código):** `a maioria` (28 de 40 = 70%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C117 · `the-turin-horse` · Talvez evite · NEG-C

> **Talvez evite se você** se incomoda com obras que aparentam pretensão artística ao valorizar tédio e dificuldade

- **chave:** `the-turin-horse · talvez_evite · NEG-C`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-C — *Pretensão artística e elitismo percebido*
- **o que o grupo diz:** Este grupo critica o que considera uma postura pretensiosa do diretor e de seus admiradores, sugerindo que a obra valoriza a dificuldade e o tédio como se fossem virtudes artísticas. Alguns expressam frustração com a ideia de que apenas uma audiência específica, supostamente mais culta, seria capaz de apreciar o filme, tratando a incompreensão como falha do espectador.
- **rótulo de força (do código):** `cerca de metade` (22 de 40 = 55%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C118 · `the-turin-horse` · Talvez evite · NEG-D

> **Talvez evite se você** se irrita com temas musicais incessantes e som contínuo de vento que geram desgaste

- **chave:** `the-turin-horse · talvez_evite · NEG-D`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-D — *Uso repetitivo da trilha sonora e som*
- **o que o grupo diz:** A trilha sonora, caracterizada por um refrão de cordas que se repete incessantemente, é mencionada como um elemento que intensifica a sensação de monotonia e desgaste. O som do vento, onipresente, também é citado como fator que contribui para a atmosfera opressiva, mas que se torna cansativo ao longo do tempo.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** par obrigatório
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C119 · `the-turin-horse` · Talvez evite · NEG-E

> **Talvez evite se você** acha que uma bela fotografia em preto e branco não sustenta uma narrativa arrastada

- **chave:** `the-turin-horse · talvez_evite · NEG-E`
- **filme:** O Cavalo de Turim (`the-turin-horse`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~5% das notas
- **tema de origem:** NEG-E — *Fotografia bela mas insuficiente para sustentar o filme*
- **o que o grupo diz:** Várias reviews reconhecem a qualidade da fotografia em preto e branco e a composição visual cuidadosa, mas argumentam que esses aspectos não compensam a falta de envolvimento narrativo ou emocional. A beleza das imagens é vista como um atrativo isolado que não justifica a duração extensa e o ritmo arrastado.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** par obrigatório
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C122 · `the-wailing` · Vale a pena · POS-C

> **Vale a pena se você** aprecia atuações expressivas que equilibram momentos cômicos com drama familiar comovente

- **chave:** `the-wailing · vale_a_pena · POS-C`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~83% das notas
- **tema de origem:** POS-C — *Atuações e personagens marcantes*
- **o que o grupo diz:** As reviews elogiam as atuações, especialmente a performance da criança, e descrevem o protagonista como um policial atrapalhado mas dedicado à família, o que gera tanto humor quanto compaixão.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C123 · `the-wailing` · Talvez evite · NEG-A

> **Talvez evite se você** se cansa com narrativas muito extensas em que o ritmo dilui a tensão

- **chave:** `the-wailing · talvez_evite · NEG-A`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-A — *Duração excessiva e ritmo lento*
- **o que o grupo diz:** Várias pessoas deste grupo reclamam que o filme se arrasta por mais de duas horas e meia, com pausas e repetições que fazem a tensão se dissipar em vez de crescer, tornando a experiência cansativa e sem recompensa.
- **rótulo de força (do código):** `cerca de metade` (24 de 40 = 60%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C125 · `the-wailing` · Talvez evite · NEG-C

> **Talvez evite se você** se frustra com personagens que tomam decisões absurdas e parecem mal desenvolvidos

- **chave:** `the-wailing · talvez_evite · NEG-C`
- **filme:** O Lamento (`the-wailing`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~4% das notas
- **tema de origem:** NEG-C — *Personagens burros e mal construídos*
- **o que o grupo diz:** Para essas reviews, os personagens tomam decisões que beiram o absurdo e parecem existir apenas como peças de um enredo mal montado, o que torna impossível se importar com eles ou levar a história a sério.
- **rótulo de força (do código):** `muitos` (13 de 40 = 32%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C127 · `whiplash-2014` · Vale a pena · POS-A

> **Vale a pena se você** aprecia atuações intensas e realistas que conduzem um confronto marcante

- **chave:** `whiplash-2014 · vale_a_pena · POS-A`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-A — *Atuações marcantes*
- **o que o grupo diz:** As reviews positivas elogiam as atuações, especialmente a de J.K. Simmons, considerada intensa e realista, e a de Miles Teller, que também recebe destaque.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `atuacao`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C128 · `whiplash-2014` · Vale a pena · POS-B

> **Vale a pena se você** se interessa pelo retrato da obsessão e pelas consequências da busca por perfeição

- **chave:** `whiplash-2014 · vale_a_pena · POS-B`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-B — *Obsessão e busca pela perfeição*
- **o que o grupo diz:** O filme é visto como um retrato da obsessão e do desejo de atingir a perfeição, mostrando as consequências desse comportamento na vida do protagonista.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C129 · `whiplash-2014` · Vale a pena · POS-C

> **Vale a pena se você** procura uma narrativa guiada por tensão constante e intensidade do início ao fim

- **chave:** `whiplash-2014 · vale_a_pena · POS-C`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-C — *Tensão e intensidade*
- **o que o grupo diz:** Muitas reviews destacam a tensão constante e a intensidade do filme, que mantém o espectador nervoso e envolvido do início ao fim.
- **rótulo de força (do código):** `muitos` (14 de 40 = 35%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C130 · `whiplash-2014` · Vale a pena · POS-D

> **Vale a pena se você** quer conhecer os bastidores e os desafios exigentes do meio do jazz

- **chave:** `whiplash-2014 · vale_a_pena · POS-D`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~93% das notas
- **tema de origem:** POS-D — *Representação do mundo da música*
- **o que o grupo diz:** As reviews elogiam a forma como o filme retrata o universo do jazz e a indústria musical, incluindo seus bastidores e desafios.
- **rótulo de força (do código):** `alguns` (10 de 40 = 25%)
- **como entrou:** par obrigatório
- **eixo do tema:** `som_trilha`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C131 · `whiplash-2014` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com tramas que retratam humilhação e violência psicológica como algo justificável

- **chave:** `whiplash-2014 · talvez_evite · NEG-A`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-A — *Romantização do abuso e da toxicidade*
- **o que o grupo diz:** Várias reviews criticam a forma como o filme retrata a relação entre professor e aluno como uma apologia à violência psicológica e física, normalizando o sadismo e a humilhação em nome da excelência artística.
- **rótulo de força (do código):** `a maioria` (27 de 40 = 68%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C132 · `whiplash-2014` · Talvez evite · NEG-B

> **Talvez evite se você** rejeita histórias com protagonistas egoístas e figuras irritantes que dificultam a empatia

- **chave:** `whiplash-2014 · talvez_evite · NEG-B`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-B — *Personagens desagradáveis e sem profundidade*
- **o que o grupo diz:** Muitos espectadores consideram o protagonista e o mentor figuras irritantes, egoístas e unidimensionais, cujas motivações soam falsas ou exageradas, dificultando qualquer empatia.
- **rótulo de força (do código):** `muitos` (20 de 40 = 50%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C133 · `whiplash-2014` · Talvez evite · NEG-C

> **Talvez evite se você** se entedia com uma dinâmica monótona e repetitiva centrada em ensaios e sofrimento

- **chave:** `whiplash-2014 · talvez_evite · NEG-C`
- **filme:** Whiplash: Em Busca da Perfeição (`whiplash-2014`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~1% das notas
- **tema de origem:** NEG-C — *Ritmo arrastado e experiência angustiante*
- **o que o grupo diz:** A narrativa é percebida como monótona e repetitiva, focada excessivamente em ensaios e sofrimento, o que gera ansiedade e tédio em vez de envolvimento.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C135 · `zama` · Vale a pena · POS-A

> **Vale a pena se você** aprecia uma cadência lenta e opressiva, mesmo que a experiência se torne cansativa

- **chave:** `zama · vale_a_pena · POS-A`
- **filme:** Zama (`zama`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~66% das notas
- **tema de origem:** POS-A — *Ritmo lento e atmosfera opressiva*
- **o que o grupo diz:** Várias reviews positivas comentam que o ritmo é deliberadamente lento e arrastado, criando uma sensação de agonia e claustrofobia que combina com a experiência do protagonista, embora algumas considerem que isso possa tornar o filme cansativo em certos momentos.
- **rótulo de força (do código):** `muitos` (18 de 40 = 45%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C136 · `zama` · Vale a pena · POS-B

> **Vale a pena se você** busca uma recriação de época meticulosa com fotografia impressionante e som imersivo

- **chave:** `zama · vale_a_pena · POS-B`
- **filme:** Zama (`zama`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~66% das notas
- **tema de origem:** POS-B — *Fotografia, som e direção de arte*
- **o que o grupo diz:** As reviews elogiam a fotografia impressionante, o desenho de som imersivo e a recriação de época meticulosa, que transportam o espectador para o século XVIII e criam uma atmosfera densa e sensorial.
- **rótulo de força (do código):** `muitos` (16 de 40 = 40%)
- **como entrou:** base
- **eixo do tema:** `direcao_imagem`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C137 · `zama` · Vale a pena · POS-C

> **Vale a pena se você** se interessa por críticas contundentes ao colonialismo e à burocracia kafkiana

- **chave:** `zama · vale_a_pena · POS-C`
- **filme:** Zama (`zama`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~66% das notas
- **tema de origem:** POS-C — *Crítica ao colonialismo e à burocracia*
- **o que o grupo diz:** Este grupo destaca como o filme expõe o absurdo e a violência do sistema colonial, retratando a burocracia espanhola como kafkiana e mostrando a hipocrisia dos colonizadores, que tratam os povos originários com desprezo enquanto dependem de um poder central que os ignora.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `critica_social`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C138 · `zama` · Vale a pena · POS-E

> **Vale a pena se você** valoriza o rigor técnico e temático mesmo diante de certo distanciamento emocional

- **chave:** `zama · vale_a_pena · POS-E`
- **filme:** Zama (`zama`)
- **coluna:** Vale a pena se você... — escrita a partir de quem RECOMENDA (notas altas) · ~66% das notas
- **tema de origem:** POS-E — *Dificuldade de envolvimento emocional ou compreensão*
- **o que o grupo diz:** Parte das reviews positivas admite que não conseguiu se conectar emocionalmente com os personagens ou entender completamente a narrativa em uma primeira assistência, sentindo-se desorientada, mas ainda assim valoriza os aspectos técnicos e temáticos.
- **rótulo de força (do código):** `alguns` (9 de 40 = 22%)
- **como entrou:** par obrigatório
- **eixo do tema:** `impacto_emocional`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C139 · `zama` · Talvez evite · NEG-A

> **Talvez evite se você** se incomoda com narrativas arrastadas e cenas excessivamente prolongadas que causam tédio

- **chave:** `zama · talvez_evite · NEG-A`
- **filme:** Zama (`zama`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~9% das notas
- **tema de origem:** NEG-A — *Ritmo lento e tédio*
- **o que o grupo diz:** Muitas reviews descrevem o filme como arrastado e entediante, com cenas que se prolongam excessivamente e uma narrativa que não prende a atenção.
- **rótulo de força (do código):** `a maioria` (25 de 40 = 62%)
- **como entrou:** base
- **eixo do tema:** `ritmo`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C140 · `zama` · Talvez evite · NEG-B

> **Talvez evite se você** se frustra ao se sentir perdido diante de uma história difícil de acompanhar

- **chave:** `zama · talvez_evite · NEG-B`
- **filme:** Zama (`zama`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~9% das notas
- **tema de origem:** NEG-B — *Confusão e falta de compreensão*
- **o que o grupo diz:** Diversos espectadores relatam dificuldade em acompanhar a história, sentindo-se perdidos ou sem entender o que está acontecendo na tela.
- **rótulo de força (do código):** `muitos` (15 de 40 = 38%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

#### C141 · `zama` · Talvez evite · NEG-C

> **Talvez evite se você** rejeita narrativas sem direção definida que deixam a sensação de que nada acontece

- **chave:** `zama · talvez_evite · NEG-C`
- **filme:** Zama (`zama`)
- **coluna:** Talvez evite se você... — escrita a partir de quem NÃO recomenda (notas baixas) · ~9% das notas
- **tema de origem:** NEG-C — *Roteiro e narrativa fracos*
- **o que o grupo diz:** O roteiro é criticado por parecer sem direção, mal adaptado ou por não desenvolver uma trama envolvente, deixando a sensação de que nada acontece.
- **rótulo de força (do código):** `muitos` (12 de 40 = 30%)
- **como entrou:** base
- **eixo do tema:** `roteiro_estrutura`
- **situação no validador:** passou
- **categorias de risco:** nenhum detector disparou

## Apêndice A — temas pedidos que o modelo não escreveu

Informativo: não há frase para julgar. O código pediu uma condição para estes temas e o modelo SALTOU (a regra de abstenção permite — saltar é melhor que forçar).

- `burning-2018` · Talvez evite se você... · NEG-E, NEG-F
- `guillermo-del-toros-pinocchio` · Vale a pena se você... · POS-D
- `satantango` · Vale a pena se você... · POS-E
- `the-wailing` · Vale a pena se você... · POS-A

## Apêndice B — índice por filme

- `burning-2018`: C001–C008 (8 itens)
- `drive-my-car`: C009–C016 (8 itens)
- `force-majeure-2014`: C017–C024 (8 itens)
- `get-out-2017`: C025–C032 (8 itens)
- `guillermo-del-toros-pinocchio`: C033–C040 (8 itens)
- `happy-hour-2015-1`: C041–C048 (8 itens)
- `hard-to-be-a-god`: C049–C057 (9 itens)
- `memories-of-murder`: C058–C063 (6 itens)
- `neighboring-sounds`: C064–C071 (8 itens)
- `pinocchio-2022`: C072–C080 (9 itens)
- `satantango`: C081–C086 (6 itens)
- `speak-no-evil-2022`: C087–C093 (7 itens)
- `the-cloud-capped-star`: C094–C102 (9 itens)
- `the-second-mother`: C103–C109 (7 itens)
- `the-turin-horse`: C110–C120 (11 itens)
- `the-wailing`: C121–C126 (6 itens)
- `whiplash-2014`: C127–C134 (8 itens)
- `zama`: C135–C141 (7 itens)
