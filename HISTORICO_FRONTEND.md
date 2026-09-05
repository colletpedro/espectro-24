# Histórico — a INTERFACE

Este arquivo responde *"por que a interface é assim, e o que foi rejeitado?"*.

Cobre: as exceções deliberadas ao §0 na interface (HATERS/MIXED/FANS, a ordem
por peso), as variantes de barra recusadas, o callout de percentual, a animação
de entrada, o pôster, o backdrop, o topo editorial e a tipografia da ficha.

---

<!-- SPEC.md linhas 109–122 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **O trade-off, escrito por extenso, porque é ele que a exceção custa.**
> Este §0 exige neutralidade de tratamento entre o grupo negativo e o
> positivo, e **"Fans/Haters" não é um par simétrico**: "hater" imputa
> MÁ-FÉ a quem não gostou — descreve alguém movido por hostilidade, não
> alguém que assistiu e achou ruim —, enquanto "fã" imputa entusiasmo,
> que é uma disposição favorável e não uma acusação. O produto passa,
> portanto, a nomear um dos dois lados com uma palavra que carrega juízo
> sobre a MOTIVAÇÃO de quem escreveu, e o outro não. Isso contradiz a
> invariante 2 ("a perspectiva minoritária continua analisada com o mesmo
> rigor... sem desdém, sem ironia, sem sugerir que quem pensa assim está
> errado") no plano do vocabulário. Não há como registrar isto de outro
> jeito: é uma perda de neutralidade, aceita conscientemente em troca de
> alcance, e não uma equivalência que o documento possa fingir.
>

<!-- SPEC.md linhas 165–202 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **REVERSÃO BARATA, DE PROPÓSITO.** O rename é de UM PONTO SÓ porque a
> hipótese ainda não foi testada em público: se o ganho de conexão não se
> confirmar, voltar aos rótulos antigos é **uma edição de uma linha**, e
> não uma varredura por um produto inteiro. O custo de errar foi
> desenhado para ser baixo antes de a aposta ser feita.
>
> **ANOTADO, NÃO IMPLEMENTADO:** "MID" é mais idiomático que "MIXED" em
> português brasileiro, e era o termo da versão originalmente arquivada.
>
> **O CASO DE FRONTEIRA QUE FECHOU O CRITÉRIO: a legenda do mosaico da
> home vira GLOSSÁRIO (v1.9.26).** A varredura da Entrega 3 encontrou um
> caso que não caía limpo dos dois lados do critério, e ele foi escalado em
> vez de decidido por conta própria. A legenda da faixa da home dizia *"a
> faixa na base de cada quadro é a distribuição real do filme: quem não
> gostou, quem ficou no meio, quem gostou"*, com as três expressões nas
> cores dos grupos. Ela tem **função de rótulo** (é a legenda que explica a
> faixa, paralela exata da legenda da barra de proporção, que TROCA) escrita
> em **forma de prosa** (enumeração dentro de uma frase corrida, e sem
> nenhuma das três palavras-chave, que MANTERIA).
>
> **Decisão do dono do projeto: nem manter, nem trocar — virar glossário.**
> Passa a ser **"HATERS (quem não gostou), MIXED (quem ficou no meio), FANS
> (quem gostou)"**, com as cores de grupo preservadas.
>
> **O raciocínio, porque ele generaliza para o próximo caso de fronteira.**
> As duas saídas puras eram ruins por motivos opostos. Trocar seco
> produziria "…a distribuição real do filme: HATERS, MIXED, FANS" e
> **destruiria a única função que a legenda tem** — ela existe para
> explicar a faixa a quem acabou de chegar, e três palavras em inglês sem
> glosa explicam menos que as expressões que estavam lá. Manter como
> estava criaria **descompasso**: o leitor sairia da home com um
> vocabulário e encontraria outro em toda página de filme, sem nada
> ligando os dois. O glossário resolve as duas coisas de uma vez, porque a
> legenda é exatamente **onde o vocabulário novo se ensina**: o rótulo vem
> primeiro, a glosa entre parênteses logo atrás, e o leitor sai dali
> sabendo ler as páginas de filme. É a única posição do produto em que as
> duas formas convivem de propósito.


<!-- SPEC.md linhas 207–214 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **O defeito.** Os dois blocos em destaque saíam em ordem FIXA — negativas
> antes de positivas — qualquer que fosse o peso de cada grupo.
> `the-godfather` é 2 / 5 / 93: a leitura abria por **HATERS, 2% das
> notas**, e o grupo que responde por 93% da recepção só chegava depois. É a
> mesma **infidelidade por omissão** que motivou a v1.4.0, num canal que a
> v1.4.0 não tinha olhado: cada bloco era verdadeiro, e a ordem em que eles
> chegavam comunicava outra coisa.
>

<!-- SPEC.md linhas 219–247 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **POR QUE ELA É COMPATÍVEL COM ESTE §0, e a frase é a inteira: a regra é
> função do DADO, não do sentimento.** Ela nunca privilegia o negativo nem o
> positivo — privilegia **quem é maior**, e quem é maior sai do
> `share_real`, que é o histograma do Letterboxd, não um juízo do produto.
> Não existe caminho pelo qual esta regra favoreça um lado: o lado que ela
> favorece é escolhido pelas notas de quem assistiu.
>
> **E A ORDEM ANTIGA NÃO ERA NEUTRA — ERA CONSTANTE, que é outra coisa.**
> Isto precisa ficar escrito porque a intuição diz o oposto (uma ordem que
> nunca muda *parece* a opção neutra). Liderar sempre pelo negativo é uma
> **escolha editorial fixa**, tomada uma vez e repetida 35 vezes sem que o
> dado fosse consultado nenhuma delas. Neutralidade de tratamento é dar
> **formato idêntico** aos grupos; nunca foi dar posição idêntica, que é
> impossível — alguém tem de vir primeiro. Quando duas posições são
> desiguais por construção, a única regra defensável é a que decide entre
> elas **pelo dado**.
>
> **A NEUTRALIDADE DE TRATAMENTO CONTINUA INTEGRALMENTE EM VIGOR, e a
> mudança foi desenhada para não tocar em nada dela:** mesmo leiaute, mesmo
> peso tipográfico, **mesma quantidade de bullets** (6 e 6 nos 35, conferido
> depois da mudança), mesmas cores, mesmo espaço estrutural. **Só a POSIÇÃO
> muda.** Nenhum número, nenhum bullet, nenhum pixel de estrutura se move.
>
> **A POLÍTICA DO MEIO NÃO MUDA.** `medianas` continua rebaixado por padrão,
> com a mesma exceção automática de quando é o grupo dominante (o parágrafo
> acima). A ordenação só ordena o que já está em destaque: quando o meio
> está lá, ele entra na mesma conta — `napoleon-2023` (22 / 45 / 33) abre
> por MIXED, `friday-the-13th-2009` (33 / 41 / 26) também.
>

<!-- SPEC.md linhas 7405–7460 · origem: A ORDEM DOS BLOCOS EM DESTAQUE — POR PESO (v1.9.30) -->

   **RESULTADO MEDIDO nos 35: a ordem MUDOU em 33.** Os dois que ficaram
   iguais são os dois filmes de recepção negativa dominante —
   `cats-2019` (86 / 7 / 7) e `joker-folie-a-deux` (46 / 33 / 21) —, e é
   exatamente a prova de que a regra não é "positivas primeiro" com outro
   nome: nesses dois, HATERS continua abrindo a leitura, porque HATERS é o
   maior grupo. Dos 33 que mudaram, 31 passaram de `NEG→POS` para
   `POS→NEG`, e os 2 de meio dominante viraram `MED→NEG→POS`
   (`friday-the-13th-2009`) e `MED→POS→NEG` (`napoleon-2023`).

   **A BARRA DE PROPORÇÃO NÃO É REORDENADA — e isso não é uma inconsistência
   por esquecimento, é a diferença entre dois tipos de ordem.** A ordem da
   barra é **SEMÂNTICA**: ela é um eixo ordinal de 0,5★ a 5★, e HATERS à
   esquerda / MIXED no meio / FANS à direita é o que faz a barra ler como
   **uma população particionada** em vez de três medições justapostas.
   Ordenar por peso ali destruiria o eixo — o meio deixaria de estar no
   meio, e a diagonal entre duas faixas deixaria de separar níveis de nota
   vizinhos. **Continuam todos em negativas → medianas → positivas:** a
   barra da página do filme, a faixa do mosaico da home, a legenda e o
   `aria-label`. Conferido depois da mudança em `the-godfather`
   (*"HATERS, cerca de 2%…; MIXED, cerca de 5%…; FANS, cerca de 93%…"*) e em
   `cats-2019`.

   **A DESSINCRONIA ENTRE A BARRA E OS BULLETS — observada na tela, e é
   pequena.** Sim, a página passa a ter dois objetos com ordens diferentes:
   a barra em ordem de estrela e os bullets em ordem de peso. Na tela isso
   quase não se nota, por dois motivos concretos: eles estão a uma rolagem
   um do outro (barra no topo, bullets depois da linha arco-íris), e o
   **callout de percentual** ancora cada número na sua fatia, então o leitor
   chega aos bullets já sabendo qual grupo é o grande — encontrar esse grupo
   primeiro **confirma** a barra em vez de contradizê-la. O caso em que a
   diferença é mais visível é `cats-2019`, onde a fatia esquerda é 86% e o
   primeiro bloco é justamente HATERS: ali as duas ordens **coincidem**.
   Onde elas divergem (`the-godfather`), a fatia grande é a da direita e o
   bloco grande é o de cima — eixos diferentes, sem confronto direto.

   **O VEREDITO PODE FICAR EM DESCOMPASSO, e isto é RESSALVA REGISTRADA, não
   defeito corrigido.** O veredito (§3[V]) é **estágio fechado**: escrito por
   LLM sobre briefing determinístico, com a sua própria ordem de
   apresentação dos grupos, e **não foi regenerado nem alterado** por esta
   versão. Ele pode, portanto, abrir por um grupo diferente do primeiro
   bloco de bullets.

   **MEDIDO nos 35, e o número surpreende na direção boa:** o descompasso
   (primeiro grupo citado no veredito ≠ primeiro bloco de bullets) aparece
   em **6 de 35** DEPOIS desta mudança, contra **31 de 35** ANTES dela. A
   ordem fixa era a que estava fora de sincronia com o veredito quase
   sempre — o texto do LLM tende a abrir pelo grupo dominante, e a tela
   abria pelo negativo. Os 6 remanescentes: `cats-2019` e
   `joker-folie-a-deux` (bullets em HATERS, veredito abre pelos que
   recomendam) e `cure`, `pearl-2022`, `perfect-days-2023`,
   `spider-man-across-the-spider-verse` (bullets em FANS, veredito abre
   pelos que não recomendam). Medição por detecção de vocabulário no texto
   publicado (`recomendam`/`não recomendam`/`aprovam`/`reprovam`/
   `meio-termo`), sobre `veredito.texto` incluindo o prefixo determinístico
   de meio dominante.


<!-- SPEC.md linhas 7501–7566 · origem: O CALLOUT DE PERCENTUAL abaixo da barra (v1.9.27) -->

   **Por que esta regra e não as outras duas consideradas:**
   - **Omissão abaixo de um limiar** foi descartada de saída: sumir com o
     `~2%` é apagar exatamente o número que o leitor não esperava, e a
     exigência de acessibilidade desta versão é que os três estejam
     legíveis e no DOM desde o primeiro frame.
   - **Empilhamento vertical** resolve a colisão, mas cobra altura, desfaz
     a leitura em linha única e **não evita o problema**: um número na
     segunda linha continua precisando de um indicador inclinado para achar
     a sua fatia. Paga o custo do deslocamento sem se livrar dele.

   **Por que ela vale para QUALQUER distribuição futura, e não só para as
   35 de hoje.** É uma passada de empacotamento, não uma exceção por filme:
   sempre tem solução enquanto `3L + 2g` couber na barra — **147,7px contra
   335px** de barra a 375px de viewport (com `g` = 14px), folga de 2,3×. Qualquer trinca que
   some 100 é acomodada, inclusive 0/0/100 e 33/33/34; abaixo de ~180px de
   barra (viewport que não existe) os números encostariam.

   **ONDE A CONTA MORA: no CSS**, pela mesma razão de `--diag`. Ela mistura
   três grandezas que vivem em lugares diferentes — o centro da fatia é
   **dado** (percentual, sai do JSON e nunca muda), a largura da caixa do
   número é **tipografia** (`ch` da mono, que o CSS conhece e o JS só
   saberia medindo) e a largura da barra é **layout** (muda a cada resize).
   `min()`/`max()` misturam porcentagem e `ch` sem problema, então a conta
   inteira reage a resize e a zoom de fonte sozinha: **sem
   `ResizeObserver`, sem ouvinte de `resize`, sem um único recálculo em
   JS**. O JS grava só `--c1..--cn` e `--n`.

   **O INDICADOR tem duas metades porque o CSS não tem sinal.** A que
   aponta para a direita mede `max(0, rótulo − centro)`; a que aponta para
   a esquerda, `max(0, centro − rótulo)`. Só uma tem largura de verdade; a
   outra colapsa para a espessura mínima (1px) e, por estar ancorada NO
   CENTRO VERDADEIRO, vira a marquinha vertical em cima dele — que é
   exatamente o que se quer ali. Sem deslocamento nenhum as duas colapsam e
   o indicador é uma marca vertical de 2px, que é o caso da maioria do
   catálogo.

   **MEDIDO em `the-godfather`, os dois tamanhos** (posição em px a partir
   da borda esquerda da barra; `centro` é o centro do rótulo, `fatia` o
   centro verdadeiro da fatia):

   | | rótulo | esquerda | centro | fatia | desloc. |
   |---|---|---|---|---|---|
   | desktop (barra 720px) | `~2%` | 0,00 | 19,96 | 7,20 | +12,76 |
   | | `~5%` | 53,91 | 73,87 | 32,40 | +41,47 |
   | | `~93%` | 365,23 | 385,19 | 385,20 | −0,01 |
   | 375px (barra 335px) | `~2%` | 0,00 | 19,96 | 3,35 | +16,61 |
   | | `~5%` | 53,91 | 73,87 | 15,07 | +58,80 |
   | | `~93%` | 159,27 | 179,22 | 179,22 | 0,00 |

   Caixa de 39,91px nos dois tamanhos (a fonte não encolhe no mobile);
   nenhuma sobreposição, nenhum overflow horizontal. (Valores da v1.9.28,
   com `--gap` de 14px; na v1.9.27, com 8px, o segundo rótulo ficava 6px
   à esquerda destes.)

   **`aria-hidden="true"` no callout — DIVERGE, de propósito, da decisão
   tomada para a LEGENDA.** A legenda visível não é escondida de leitor de
   tela ("esconder texto visível troca um problema por outro"), e a
   redundância com o `aria-label` é aceita — mas a legenda carrega o **nome
   do grupo**: lida isolada, ela informa. Um `~2%` solto, não. Sem o nome
   ao lado, os três números viram três grandezas órfãs anunciadas logo
   depois de o leitor de tela já ter lido *"HATERS, cerca de 2% das notas;
   MIXED…"* — que é o `aria-label` da barra, com rótulo, na mesma ordem e
   com os mesmos inteiros. O callout **não acrescenta um bit** ao que a
   alternativa textual da barra já diz: é uma re-apresentação VISUAL dela.
   Esconder aqui não perde informação e evita três números sem dono.


<!-- SPEC.md linhas 7623–7736 · origem: A ANIMAÇÃO DE ENTRADA DA BARRA — as FRONTEIRAS DESLIZAM (v1.9.28) -->

   ##### `--diag` durante a interpolação — ACOMPANHA (v1.9.28)

   A diagonal é derivada da fatia mais fina. No estado de terços a mais
   fina é 33,333%; no final pode ser 2%. **Escolhido ACOMPANHAR a
   interpolação**, com as duas variantes construídas e medidas lado a lado.

   `--menor-agora = 33,333 + (menor_final − 33,333) × k`, e a identidade
   `min(lerp(t, f_i, k)) = lerp(t, min(f_i), k)` — todas as fatias partem
   do MESMO 33,333% — é o que permite escrever isso como **uma conta só**,
   sem comparar as três em tempo de execução.

   **Por quê:** a diagonal existe para proteger a fatia estreita, e durante
   o deslize a fatia estreita ainda não é estreita. Fixá-la no valor final
   faz a barra animar inteira com uma diagonal dimensionada para um destino
   que ainda não chegou — e isso é **visível**: em `the-godfather` a 375px,
   no meio da animação, a variante fixa desenha uma fronteira de 3,68px
   entre duas regiões largas, que lê como corte reto e não como a diagonal
   da barra publicada. A variante que acompanha desenha 12px ali, e a barra
   lê como o mesmo objeto do começo ao fim. Os dois estados finais são
   idênticos.

   **O risco levantado (tremor / artefato de subpixel na fatia estreita)
   foi medido e NÃO existe.** Em 131 amostras de 5ms, nas duas variantes:
   **zero reversões** na aresta de cima e na de baixo da diagonal (a de
   baixo é a que corre risco, porque `base = x1 − diag/2` e os dois termos
   encolhem juntos); o ponto mais fino da fatia de 2% nunca desce de
   **4,861px**, o mesmo valor final nas duas variantes.

   **O que ACOMPANHAR de fato custa, registrado:** o `clamp()` prende a
   diagonal no teto de 12px durante a primeira metade e só então a solta,
   então o **valor** é contínuo mas a **taxa** tem um canto no ponto em que
   o clamp deixa de morder (t ≈ 301ms a 375px, t ≈ 470ms em desktop).
   Medido: a diagonal muda no máximo **0,947px por quadro**, contra
   **8,425px por quadro** de deslocamento da própria fronteira — a mudança
   do ângulo é ~9× mais lenta que o movimento em que ela viaja, e fica
   enterrada nele.

   ##### Os rótulos durante a interpolação — AUSENTES (v1.9.28)

   Os rótulos do callout são ancorados aos segmentos, e o empacotamento
   **não depende de `--k`**: as posições são as finais desde o primeiro
   frame. Um `~2%` visível durante o deslize ficaria meio segundo apontando
   para uma região que naquele instante é 33% — ou teria de deslizar junto
   (mostrando número que não bate com a região) ou mudar de valor (animar
   dado, descartado desde a v1.9.27).

   **Rótulos e indicadores AUSENTES durante a interpolação**, acendendo
   depois, já nas posições finais e com os valores finais. A ignição
   continua sendo o momento em que o número aparece. Isso **reverte** o
   `opacity: 0.16` inicial da v1.9.27 (o "tubo apagado"), que só fazia
   sentido enquanto a barra crescia vazia e o número não contradizia nada.
   **O texto continua no DOM com o valor final desde o primeiro frame** — o
   que muda é opacidade, cor e sombra.

   ##### O NEON FICA LIGADO (v1.9.28)

   **Correção da decisão da v1.9.27, pelo dono do projeto:** o brilho NÃO
   decai depois do pico. A ignição continua sendo o EVENTO — apagado →
   flicker → pico → estabiliza —, e o pico continua mais intenso que o
   repouso; o que mudou foi o **destino**: em vez de o halo praticamente
   desaparecer, ele estabiliza num estado **aceso permanente**.

   Calibrado na tela: núcleo branco fechado (2px a 65%), halo na cor do
   grupo (6px) e halo externo na cor a 20% de alfa (**11px, e esse teto é
   requisito de layout — ver abaixo**). O pico vai a 28px, por ~35ms.

   **AS QUATRO CAMADAS DE SOMBRA SÃO AS MESMAS EM TODOS OS QUADROS**, com a
   quarta zerada no repouso. `text-shadow` com número DIFERENTE de camadas
   entre dois quadros **não interpola** — salta. Manter a contagem é o que
   faz o pico descer suavemente até o repouso em vez de piscar para ele.

   ##### A COLISÃO QUE O NEON PERMANENTE CRIA, e como ela foi fechada

   Com o halo aceso o tempo todo, ele passa a **ocupar espaço** o tempo
   todo — e a regra de empacotamento tinha sido calculada sem ele. Em
   `the-godfather` a 375px o segundo número começa a 8px do fim do
   primeiro; um halo de raio grande atravessa essa folga e mistura o brilho
   de dois grupos de **cores diferentes**, que é exatamente o que a paleta
   por grupo existe para não fazer.

   **ESCOLHIDAS AS DUAS SAÍDAS, e não uma.** Limitar o raio (11px) **e**
   fazer o empacotamento contar o halo (`--gap` de 8px para 14px). Cada uma
   sozinha é frágil: só limitar o raio deixaria a garantia dependendo de um
   número que a próxima calibração de brilho pode mexer sem perceber; só
   aumentar a folga deixaria o halo livre para crescer. A conta, com `R` o
   raio do halo e `P` o respiro que a caixa já dá em volta do texto:

   ```
   folga_entre_tintas = --gap + 2P  ≥  2R
   ```

   O pior caso possível é dois rótulos de **4 caracteres** empacotados lado
   a lado (`P` mínimo = 5,46px): `--gap ≥ 2(11) − 2(5,46) = 11,08px`.
   Com 14px sobram 2,92px **no pior caso que a regra admite**, e não só nos
   filmes de hoje. Aumentar a folga **não custa nada** nos filmes em que a
   restrição não morde — o rótulo já cabia no centro da sua fatia —; custa
   ~6px de deslocamento a mais só nos que já estavam deslocados.

   **MEDIDO** (folga entre as TINTAS, medida com `Range`, não entre as
   caixas; precisa de 22px):

   | filme | par | desktop | 375px |
   |---|---|---|---|
   | `the-godfather` | `~2%` · `~5%` | 32,17px | 32,17px |
   | `cidade-de-deus` | `~1%` · `~3%` | 32,17px | 32,17px |
   | `eighth-grade` | `~6%` · `~18%` | 61,91px | **28,55px** |
   | `cats-2019` | `~7%` · `~7%` | 32,17px | 32,18px |

   Nenhuma mistura em nenhum dos dois tamanhos. O par mais apertado do
   catálogo não é o de `the-godfather` e sim o de `eighth-grade` a 375px,
   porque ali um dos dois rótulos tem 4 caracteres e sobra menos respiro
   dentro da caixa.



<!-- SPEC.md linhas 7826–7865 · origem: O PÔSTER (v1.9.29) — na home e na página do filme -->

   **A PROPORÇÃO É RESERVADA ANTES DE CARREGAR**, em dois níveis: um
   `aspect-ratio` inline escrito pelo JS a partir de
   `ficha.poster_largura`/`poster_altura` (segura a caixa mesmo se a imagem
   nunca chegar) **e** `width`/`height` no próprio `<img>` (dá ao navegador
   a razão intrínseca sem depender do CSS). **Medido:** com a reserva, a
   geometria da home é **byte-idêntica** com e sem as 35 imagens no DOM
   (altura de documento 1657px nos dois casos, 0 de 35 células mudando de
   retângulo) e a CLS observada é **0**; na página do filme, o título fica
   em y=425,52 com ou sem o pôster. **Sem a reserva**, a caixa do pôster
   mediria **2px** de altura até a imagem chegar — o título saltaria
   **298px** quando ela chegasse. Esse é o número que a reserva compra.

   **TAMANHOS DO CDN, e o cálculo.** O TMDB serve variantes de largura
   (`w92 · w154 · w185 · w342 · w500 · w780 · original`). A regra é a maior
   largura CSS que o elemento atinge, vezes 2 (telas de densidade 2x/3x),
   arredondada para cima na lista.
   - **mosaico → `w342`.** A célula mede ~142px CSS no desktop (mosaico de
     1080px, 7 colunas) e ~111px no mobile de 375px (3 colunas); 142×2=284,
     111×3=333. **Peso medido dos 35:** `w185` 525 KB (pequeno demais em
     retina), **`w342` 1282 KB** (37 KB de média, 17–66 KB), `w500` 2362 KB
     (+84% por pixels que a célula não usa).
   - **ficha → `w500`.** O pôster mede 200px CSS no desktop; 200×2=400.
     `w342` ficaria abaixo em retina, e é UMA imagem por página.
   `original` (2000px de largura) num card de mosaico é desperdiçar 99% dos
   bytes, e é explicitamente o que não se faz.

   **`loading="lazy"` na home** (35 imagens, a maioria abaixo da dobra) e
   **`eager` na ficha** (UMA imagem, sempre acima da dobra — adiá-la só
   atrasaria a abertura). `alt` diz o que a imagem É ("Pôster de <título>
   (<ano>)"): descrever a arte seria invenção, e o texto ao lado já nomeia o
   filme. **Nada de binário no repositório:** o JSON guarda só `file_path`,
   a imagem vem do CDN do TMDB, sem download, proxy ou cache local.

   **Onde mora.** `frontend/js/poster.js`, compartilhado pelas duas páginas
   — e a exceção à duplicação deliberada do projeto (`EIXO_LABEL` vive em
   home.js E filme.js) é justificada: lá a lista é fechada e divergir seria
   visível no primeiro filme; aqui uma home servindo `w500` e uma ficha
   servindo `w342` não quebrariam nada, não apareceriam em teste nenhum, e a
   única consequência seria peso de rede que ninguém mede.


<!-- SPEC.md linhas 7924–8045 · origem: O BACKDROP no topo da página do filme (v1.9.30) -->

   ##### QUAL backdrop — regra determinística, em código

   A escolha é do **pipeline** (`_ordem_imagem`/`_melhor` em `ficha.py`,
   §3[F]), gravada no JSON como `backdrop_path`, e sai de **dentro dos até
   10 coletados** (`backdrop_paths[]`) — nunca do acervo inteiro. Isso é o
   que mantém "qual imagem esta página mostra" respondível olhando só o JSON
   publicado. **NÃO EXISTE GALERIA:** `backdrop_paths[]` continua sendo lista
   guardada que nenhum arquivo do frontend percorre; o frontend lê **um**
   campo, o do escolhido.

   **A ordem, do degrau mais forte ao mais fraco, e por que cada um:**

   1. **sem texto sobreposto** (`iso_639_1 is None`) antes de arte com
      idioma declarado;
   2. **`vote_average`** decrescente — a resposta a "o mais bem avaliado";
   3. **`vote_count`** decrescente;
   4. **`width`** decrescente;
   5. **`file_path`** crescente — o degrau que fecha a **ordem total**.

   **Por que "mais bem avaliado" e não as outras duas propostas.**
   *Maior resolução* como primeiro critério escolhe o maior arquivo, não o
   melhor quadro: o acervo é cheio de 3840×2160 sem voto nenhum, e a régua
   viraria "quem exportou em 4K". *Primeiro da lista* delega a escolha a uma
   ordenação que a API **não declara**: `images.backdrops` chega por
   `vote_average` decrescente, mas isso não é ordem total — empates são
   comuns e o desempate é indefinido. **MEDIDO nos 35: em 3 filmes**
   (`eighth-grade`, `friday-the-13th-2009`, `wicked-2024`) **o primeiro da
   lista não é o que esta ordem escolhe.** Confiar na posição deixaria a
   imagem de um filme publicado livre para mudar entre duas execuções sem
   que nada no dado tivesse mudado — que é exatamente o que "determinística"
   proíbe. Os degraus 3–5 existem por isso: sem o `file_path` no fim, a
   ordem não é total e o problema volta pela porta dos fundos.

   **O degrau 1 é PREFERÊNCIA, nunca filtro** — um filme cujas imagens sejam
   todas `pt` continua tendo backdrop. Ele existe porque uma imagem
   `iso_639_1='pt'` é **key art de campanha**: título tratado e bloco de
   elenco gravados no pixel, indo logo ACIMA do par ano → título que a
   própria página escreve. **MEDIDO: afeta 2 dos 35** —
   `joker-folie-a-deux` e `longlegs`, os dois com uma peça `pt` de
   `vote_average` 7,542 que venceria sem a regra (a do Joker traz
   *"PHOENIX GAGA / JOKER: LOUCURA A DOIS"* em tipografia de cartaz). É
   também o degrau mais fácil de reverter se o dono preferir a key art:
   é um argumento de `_melhor`.

   ##### FALLBACK, em dois degraus

   1. filme **sem backdrop** usa o **pôster** que já estava ali — contido,
      200px no desktop / 140px no mobile, exatamente como na v1.9.29;
   2. filme **sem os dois** cai no **estado de ausência já desenhado**.

   O backdrop **não cai no pôster por conta própria** dentro de
   `montarBackdrop` (ele devolve `null` e quem chama decide), porque as duas
   caixas têm proporção e tamanho diferentes — um pôster 2:3 esticado na
   largura da coluna seria pior que qualquer um dos dois estados.

   **MEDIDO: 34 dos 35 têm backdrop; 1 não** — `talk-to-me-2022`, e o motivo
   dele **não é escassez de acervo**: a ficha publicada desse slug é a de
   outro filme (ver a ressalva no §3[F]). Uma falha do CDN cai no mesmo
   estado desenhado da ausência, na caixa 16:9.

   ##### PROPORÇÃO RESERVADA — o requisito ficou mais duro, não menos

   Mesma construção em dois níveis do pôster (§3[E], v1.9.29):
   `aspect-ratio` inline vindo de `ficha.backdrop_largura`/`backdrop_altura`
   **e** `width`/`height` no `<img>`. **Aqui a reserva importa MAIS:** sendo
   largo, o backdrop reserva mais altura em pixels que o pôster contido, e
   sem ela o salto seria **pior** que o de antes.

   **MEDIDO** (`the-godfather`, viewport 1280, coluna de 720px):

   | | valor |
   |---|---|
   | caixa reservada | 720 × 405 px |
   | `aspect-ratio` inline | `1920 / 1080` (dimensões reais do TMDB) |
   | y do `<h1>` **com** a imagem carregada | 530,52 px |
   | y do `<h1>` **sem** a imagem (só a reserva) | 530,52 px |
   | y do `<h1>` **sem a reserva** | 125,52 px |
   | **salto que a reserva evita** | **405 px** |
   | **CLS observada** | **0** (0 entradas de `layout-shift`) |

   A CLS foi medida com `PerformanceObserver({type:'layout-shift',
   buffered:true})` sobre um carregamento completo, em desktop (1280px) e a
   375px: **0 nos dois**, com **zero** entradas — não é um total pequeno, é
   a ausência de qualquer deslocamento. A home, que não mudou, foi medida de
   novo para confirmar que não regrediu: **CLS 0**, altura de documento
   **1657px** — o mesmo número da v1.9.29 — nas duas variantes de pôster.

   ##### TAMANHO DE CDN — `w1280`, e a conta

   O TMDB serve backdrops numa lista de larguras **própria**
   (`w300 · w780 · w1280 · original`) — `w500` nem existe para backdrop, e
   por isso ele não entra no mapa de tamanhos do pôster. A coluna de leitura
   é `--maxw` (720px, 760px acima do breakpoint largo) menos 20px de padding
   de cada lado: **680–720px CSS**. A regra do projeto (maior largura CSS ×
   2, arredondando para cima na lista) pediria 1360–1440 — e o degrau
   seguinte é **`original`** (3840×2160, ~1,5 MB), que a regra do projeto
   proíbe servir e que num elemento decorativo seria desperdício de quase
   toda a transferência.

   **`w1280` é a escolha, com o custo declarado:** ela entrega **1,78–1,88×**
   num aparelho de densidade 2, contra os 2,0× ideais — diferença que não se
   vê num quadro fotográfico e que custaria megabytes para fechar. `w780`
   ficaria em **1,08×** no desktop, visivelmente mole em retina.

   ##### `alt`, e a moldura

   `alt` = **"Imagem de &lt;título&gt; (&lt;ano&gt;)"**. Mesma política do
   pôster: diz o que a imagem **É**, sem descrever a arte (não temos a
   descrição, e inventá-la seria mentir para quem depende do `alt`) e sem
   repetir o que o `<h1>` logo abaixo já diz. **Não é chamada de "cena"** de
   propósito: parte do acervo é arte de divulgação, não fotograma, e o `alt`
   afirmaria uma coisa que nem sempre é verdade.

   **Sem borda e sem sombra projetada, ao contrário do pôster** — o pôster é
   um objeto pousado na página e a borda o recorta do fundo; o backdrop é a
   abertura, e uma moldura o transformaria num print. Um degradê na base
   costura a imagem no fundo da página, porque o par ano → título vem logo
   abaixo e uma aresta dura ali cortaria os dois. No mobile ele vai **de
   borda a borda** (recuo negativo de 20px de cada lado): com o padding, um
   quadro 16:9 mediria 335px de largura numa tela de 375 e leria como
   miniatura.


<!-- SPEC.md linhas 8119–8384 · origem: O TOPO EDITORIAL (v1.9.32) — a sinopse sai, o backdrop dissolve, o título invade -->

   | | fade | faixa 100% opaca | recuo do texto | folga |
   |---|---|---|---|---|
   | desktop | 232px | 68px | 58px | 10px |
   | ≤640px | 156px | 58px | 52px | 6px |

   **A CONSEQUÊNCIA é o que torna o requisito verificável: o contraste vira
   INDEPENDENTE DA IMAGEM.** Não é "medimos os 34 e deu bom" — é que a
   imagem **não entra na conta**.

   **Duas diferenças para o mosaico, ambas deliberadas.** (a) Lá a base do
   degradê é **preta** (a célula é um card sobre fundo escuro e o preto some
   nela); aqui é **`--bg`**, porque o degradê tem de casar exatamente com o
   fundo da página — qualquer outra cor deixaria emenda visível onde a
   imagem acaba. (b) As paradas são em **px, não em %**: a faixa chapada
   precisa ter a mesma altura que o recuo, que é em px; em % ela mudaria de
   altura com a proporção do backdrop (de 3840×2160 a 3500×1969 no
   catálogo) e o casamento quebraria sem sintoma.

   **MEDIDO — composição analítica sobre os pixels reais dos 34 backdrops**
   (imagem `w1280` baixada, luminância relativa WCAG, composição
   `img×(1−α) + bg×α` com o α exato de cada parada do degradê, pior pixel
   de cada linha que o texto ocupa):

   | | título (`--text`) | ano (`--text-mute`) |
   |---|---|---|
   | **fade da v1.9.32, nos 34** | **17,15:1** | **4,56:1** |
   | texto sobre o fundo puro `#0b0c10` | 17,15:1 | 4,56:1 |
   | fade da v1.9.30, se o texto invadisse (pior caso) | 4,92:1 | **1,31:1** |

   Em **34 de 34** o fundo sob o texto compõe **exatamente `#0b0c10`** —
   idêntico, dígito a dígito, ao fundo da página. **Nenhum filme fica
   abaixo do piso**, e não há caso a tratar. O ano a 4,56:1 passa o AA de
   texto normal (4,5:1) e **é o mesmo valor que ele já tinha** em qualquer
   outro ponto do site: não há regressão, e o teto dele é uma dívida
   pré-existente da paleta, não desta versão.

   **O PIOR BACKDROP DO CATÁLOGO NÃO É O QUE SE SUPUNHA, e vale registrar.**
   A hipótese de trabalho era `dune-2021` (céu claro embaixo). Medindo a
   luminância média da faixa inferior dos 34, `dune-2021` é o **12º**
   (0,098); os dois piores são **`barbie` (0,370)** e **`the-hateful-eight`
   (0,351)**. Com o fade antigo, `barbie` daria **1,33:1** no ano — texto
   praticamente ilegível. Com o novo, 4,56:1 como todos os outros.

   ##### O ACOPLAMENTO FECHADO POR CONSTRUÇÃO (v1.9.33)

   **A INVARIANTE, em uma frase: o recuo do texto é sempre menor que a
   faixa opaca, e é isso que faz a imagem não entrar no cálculo de
   contraste.**

   Na v1.9.32 essa invariante vivia em DOIS comentários, num arquivo só,
   sobre DOIS números que só concordavam porque alguém fez a conta certo
   uma vez: a faixa chapada do degradê (`68px` em `.backdrop::after`) e o
   recuo do texto (`58px`, `--hero-overlap`). Nada no CSS impedia editar um
   sem lembrar do outro — mudar a faixa sem tocar no recuo teria revertido
   a garantia **em silêncio**, e o sintoma só reapareceria como título
   ilegível no próximo backdrop claro que entrasse no catálogo.

   **A correção segue o mesmo padrão de `--k` na barra de proporção**
   (§3[E]: uma propriedade é a fonte, as fronteiras e a diagonal são
   funções puras dela). Aqui: **`--fade-solid` é a fonte** (a faixa chapada
   — o único número pensado para se ajustar), e **`--hero-overlap` é
   `calc(var(--fade-solid) - var(--fade-folga))`**, com `--fade-folga` uma
   constante **fixa e sempre positiva** (10px no desktop, 6px em ≤640px).

   **Por que isto fecha a desigualdade por ARITMÉTICA, não por disciplina.**
   Subtrair um número positivo de `--fade-solid` produz, por definição de
   subtração, um valor **menor** que `--fade-solid` — não é uma verificação
   que roda, é uma propriedade da própria expressão. Mudar só
   `--fade-solid` (para dar mais ou menos invasão do título) move
   `--hero-overlap` **junto, na mesma direção**, e a desigualdade não pode
   quebrar por essa edição. O único jeito de quebrá-la seria zerar ou
   negativar `--fade-folga` — e ela é declarada como constante justamente
   para não ser o dial que uma entrega futura mexe sem pensar.

   **Os estágios intermediários do degradê também deixaram de ser paradas
   fixas independentes.** `--fade-opaco-em: calc(var(--fade-h) -
   var(--fade-solid))` é o ponto em que a opacidade chega a 100%, e as três
   paradas parciais do gradiente são **frações dessa mesma distância**
   (`× 0.415`, `× 0.756`, `× 0.927`) — editar `--fade-h` ou `--fade-solid`
   redesenha a curva inteira de forma consistente consigo mesma, em vez de
   deixar paradas antigas apontando para uma altura que já não existe.

   **O breakpoint mobile deixou de redeclarar o gradiente inteiro.** Como
   `.backdrop::after` já é 100% `calc()`/`var()`, a media query de `≤640px`
   só sobrescreve as três variáveis-fonte (`--fade-h`, `--fade-solid`,
   `--fade-folga`); `--fade-opaco-em` e `--hero-overlap`, por serem
   `calc()`, recalculam sozinhas quando o navegador resolve as regras que
   as consomem — não precisam ser redeclaradas.

   **VERIFICADO, não só argumentado — em dois sentidos.** (1) *Regressão
   zero:* os valores computados depois da refatoração são **byte-idênticos**
   aos de antes, nos dois breakpoints — desktop `18,1px` de título sobre a
   imagem (o mesmo de `the-invite-2026` na v1.9.32), mobile `12,1px` (o
   mesmo de `the-godfather`/`barbie`). (2) *A invariante segura sob
   tensão:* sobrescrevendo `--fade-solid` para `20px` em runtime, SEM tocar
   em mais nada, `--hero-overlap` recalculou sozinho para `calc(20px -
   6px)` = `14px` — a desigualdade se manteve automaticamente, exatamente o
   comportamento que o design promete.

   **A garantia agora é estrutural: não existe edição de um valor só que a
   viole**, exceto zerar/negativar a folga — e essa é uma ação deliberada
   sobre uma constante nomeada como tal, não um efeito colateral de ajustar
   a faixa.

   ##### O LINK DO LETTERBOXD, secundário

   Deixa de ser pill: **sem caixa, sem borda, sem fundo** — mono pequena,
   na mesma direção do disclosure APROFUNDAR da v1.9.26 (parte do bloco
   editorial, não componente pousado nele). Desce do topo para logo abaixo
   da linha de metadados.

   **O que NÃO foi sacrificado junto com a caixa:** continua `<a>` de
   verdade, `target="_blank"` + `rel="noopener noreferrer"`, **foco visível**
   (`:focus-visible` com contorno de 2px) e **área de toque de 46px medidos
   no mobile** (≥ 44px recomendado) — o padding vertical continua existindo,
   invisível mas clicável. Um link discreto que fica difícil de acertar com
   o polegar seria downgrade de acessibilidade disfarçado de refinamento.

   **O TEXTO CONTINUA "reviews no Letterboxd", e não só "letterboxd".** O
   esboço do dono escreve a forma curta, e ela foi mantida longa de
   propósito: é o **nome acessível** do link, e o que ele promete é a LISTA
   DE REVIEWS daquele filme, não a home do site. Era a única perda de
   informação de uma entrega que pediu tratamento visual — decisão de uma
   palavra, trivial de reverter se o dono quiser a forma curta.

   ##### SEÇÕES NOMEADAS, e o rótulo que VOLTA

   Duas etiquetas, na tipografia mono de rótulo que o projeto já usa
   (mesma família, corpo e tracking; nenhuma família nova entra):

   - **RECEPÇÃO**, antes da barra — que passa a ser o primeiro grande bloco
     **nomeado** da página;
   - **EM DETALHE · TEMA A TEMA**, antes dos bullets.

   **"EM DETALHE · TEMA A TEMA" ESTÁ VOLTANDO, e a reversão é consciente.**
   Ele foi **removido na v1.9.26**, e a razão de lá está registrada acima:
   com o veredito descendo para o rodapé, não havia mais um resumo ANTES
   dos bullets do qual separar "o detalhe", e o rótulo virou promessa sem
   contraparte. **A razão de agora é outra**, e é isso que faz disto
   reversão e não vaivém: (a) a página passou a ter **seções nomeadas**, e
   numa página seccionada o bloco de bullets seria o único anônimo; (b) a
   **sinopse saiu**, e com ela o último texto corrido antes dos bullets — o
   leitor chega ali vindo direto da barra, e o rótulo é o que avisa que a
   régua mudou de "peso de cada grupo" para "o que cada grupo disse".

   A legenda `HATERS · MIXED · FANS` fica **abaixo dos percentuais**, que já
   era a ordem do DOM desde a v1.9.27 — nada mudou nela.

   ##### A REDUNDÂNCIA DE PESO — percorrida, MEDIDA, e MANTIDA por decisão do dono

   A pergunta levantada foi se peso aparece em três lugares (callout,
   legenda, cabeçalhos de grupo). **Medido: são DOIS, não três.** A legenda
   carrega **nome e cor**, nenhum número — ela é chave de leitura, não
   afirmação de peso. Os dois que afirmam peso com número são o **callout**
   (`~2% ~7% ~91%`, ancorado nas fatias) e o **cabeçalho de cada grupo**
   (`~91% DAS NOTAS`).

   **MEDIDO em `the-invite-2026`: 134px** entre o callout e o primeiro
   cabeçalho de grupo, e **os dois cabem na mesma tela** — tanto em
   1280×900 quanto em 375×812. Ou seja: o leitor vê `~91%` e, um terço de
   tela abaixo, `~91% DAS NOTAS`. **Isso lê como repetição**, e a medição
   não maquia isso.

   **DECISÃO DO DONO DO PROJETO: manter os dois, com a razão registrada —
   eles não servem ao mesmo leitor.** O callout serve a quem está **olhando
   a barra**: o número nasce ali, ancorado na fatia, no momento em que a
   proporção é o assunto da tela. O percentual do cabeçalho serve a quem já
   **rolou para dentro dos bullets** e está lendo tema por tema — sobretudo
   no **mobile**, onde os grupos empilham em vez de ficar lado a lado e o
   segundo bloco pode estar uma tela inteira de distância do callout. Ali o
   cabeçalho é o **único sinal de peso co-localizado com as listas** —
   exatamente a função que a v1.9.27 já tinha reconhecido ao **remover** o
   disclaimer da cota e manter o percentual do cabeçalho no lugar dele: *"o
   número no cabeçalho cobre a mesma leitura errada no lugar certo (ao lado
   dos bullets, não a 800px deles)"*. Tirar agora o segundo número
   reabriria exatamente o buraco que aquela remoção fechou.

   **A observação que continua valendo, e não muda a decisão:** a distância
   entre os dois **aumentou**, não diminuiu — na v1.9.31 publicada eram
   **65px** entre a legenda e o primeiro cabeçalho, contra **98px** agora,
   porque a etiqueta EM DETALHE entrou no meio. Isso torna os dois blocos
   mais claramente **duas leituras diferentes** (uma acima da etiqueta, uma
   abaixo dela) em vez de um número ecoando o de cima sem intervalo — o que
   é consistente com a razão de mantê-los, não uma correção adicional.
   **A CONDIÇÃO DA v1.9.27 CONTINUA DE PÉ:** *"se o percentual do cabeçalho
   algum dia sair da tela, [o disclaimer da cota] tem de voltar"* — nada
   nesta versão toca esse número, e a condição segue amarrada a ele.

   ##### ANIMAÇÃO DE ENTRADA DE ANO E TÍTULO — a coreografia, decidida

   Segunda animação de entrada da página, ao lado da sequência da barra
   (v1.9.28). **Decisão: rodam EM PARALELO, as duas a partir de 0ms**, e a
   do título é muito mais curta.

   | animação | início | duração | fim |
   |---|---|---|---|
   | ano (`hero-in`) | 0ms | 430ms | 430ms |
   | título (`hero-in`) | 70ms | 430ms | **500ms** |
   | barra · fronteiras | 0ms | 650ms | 650ms |
   | barra · ignição dos 3 números | 650ms | 260ms × 3, escalonados 55ms | **1020ms** |

   **Total da página: 1020ms — exatamente o da v1.9.28. O título não
   atrasou a barra em um único milissegundo.** Verificado pela Web
   Animations API: 13 animações na página (as **10 da barra, intactas**, as
   2 novas do herói e o `poster-in` de 240ms da imagem, que já existia).

   **POR QUE NÃO ENCADEADAS.** Encadear (título, depois barra) somaria
   ~500ms de tempo morto antes de o conteúdo começar a se mover, e **a
   barra é o conteúdo; o título é a moldura**. A página abriria com meio
   segundo em que nada do que ela veio dizer está acontecendo.

   **POR QUE O TÍTULO AINDA ASSIM "VEM PRIMEIRO".** Ele vem primeiro na
   ordem em que **termina**, não na em que começa: a moldura se assenta e
   fica parada enquanto o conteúdo ainda resolve. O olho pousa no que parou
   de se mexer. O escalonamento ano → título (70ms) é a única sequência
   interna, e é de leitura: o ano é metadado, o título é o assunto.

   **MESMA DISCIPLINA DA BARRA:** `transform` + `opacity` apenas (as duas
   propriedades que compõem sem relayout), **10px** de deslocamento,
   `cubic-bezier(0.22, 0.68, 0.28, 1)` — desaceleração pura, sem bounce,
   sem spring, sem overshoot.

   **`prefers-reduced-motion`: nenhuma das duas roda, estado final
   imediato.** Mesma construção da v1.9.27/v1.9.28 — **o estado base do CSS
   É o final**, e o estado INICIAL (`opacity: 0` + `animation`) vive inteiro
   dentro de `@media (prefers-reduced-motion: no-preference)`. **Verificado
   no CSSOM, não no arquivo:** varrendo `document.styleSheets`, a regra com
   `opacity: 0` para `.film-hero__text` aparece **1 vez dentro** do bloco
   `no-preference` e **0 vezes fora dele**. Se ela morasse fora, `reduce`
   deixaria o título invisível para sempre.

   ##### O FALLBACK SEM BACKDROP não herda a sobreposição

   Filme sem backdrop continua caindo no **pôster contido** (200px), e com
   ele volta a **composição antiga**: texto inteiramente ABAIXO da imagem
   (`.film-hero--poster` zera o recuo negativo). Um pôster 2:3 de 200px não
   tem faixa inferior larga o bastante para um título de 3,6rem, e deixar o
   título subir cobriria o cartaz. Conferido em `talk-to-me-2022`, o único
   do catálogo nessa condição: `margin-top: 0px`, texto começando 18px
   abaixo da base do pôster, estrutura nova (metadados soltos, link
   secundário, RECEPÇÃO, EM DETALHE) toda funcionando.

   #### O PÔSTER SEM TEXTO — DECISÃO FINAL: a arte limpa venceu (v1.9.30, decidido v1.9.31)

   **A queixa do dono:** os pôsteres são poluídos — bloco de créditos,
   tagline, laurel de festival. O TMDB serve **arte-chave sem texto**, que é
   a que declara `iso_639_1: null`, e o pipeline coleta em **campo próprio**
   (§3[F]): `poster_sem_texto_path` e suas dimensões. **Aditivo: não
   substitui `poster_path`**, que continua sendo o do próprio TMDB — o
   fallback abaixo depende de os dois campos coexistirem.

   **A v1.9.30 rodou as duas variantes ATIVAS e alternáveis por query
   param** (`?poster=texto` / `?poster=limpo`), o mesmo mecanismo de
   `?barra=`/`?ficha=` da v1.9.26, para a escolha ser feita **olhando**.

   **O DONO DO PROJETO COMPAROU AS DUAS E ESCOLHEU A ARTE SEM TEXTO
   (v1.9.31).** Seguindo a mesma convenção das duas decisões anteriores (a
   barra contínua venceu a divergente; a pilha de sistema venceu a Inter
   auto-hospedada): a variante vencedora fica como **único caminho**, e o
   mecanismo de escolha — o parâmetro, a leitura de `location.search`, o
   ramo condicional — **sai do JS**, não fica como opção morta atrás de
   flag. `?poster=` não existe mais em nenhum lugar do código; uma URL
   antiga com esse parâmetro não quebra nada, só o ignora, como já é o
   comportamento estabelecido para query params obsoletos de rodadas
   passadas.


<!-- SPEC.md linhas 8448–8471 · origem: A LINHA DE METADADOS DA FICHA — tipografia (v1.9.26) -->

   `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica,
   Arial, sans-serif` — entrega a **SF real** em Mac e iPhone porque usa a
   fonte **já instalada no aparelho do leitor** (o site não distribui
   nada), Segoe UI no Windows, Roboto no Android. Custo zero de
   carregamento; em troca, a página muda de aparência conforme o
   aparelho.

   **A alternativa comparada, e por que não foi a escolhida.** Uma segunda
   variante rodou lado a lado desta: **Inter**, desenhada como equivalente
   aberta da SF, auto-hospedada (SIL Open Font License 1.1, subconjunto
   latin, variável 400–700, 85 KB), idêntica em todo aparelho ao custo de
   85 KB de rede. **O dono do projeto comparou as duas e escolheu a pilha
   de sistema.** O arquivo da fonte, sua licença e o `@font-face` foram
   removidos do repositório junto com a escolha — não ficam sem uso
   ocupando espaço; se precisar voltar, o histórico do git tem o arquivo,
   a licença e a regra completos.

   **CORREÇÃO DE REGISTRO, para a spec não guardar uma frase falsa:** sans
   **não** é família nova no projeto. `--sans` (pilha de sistema) existe
   desde a v1 e é o que `body` e os campos de busca já usam — a paleta
   tipográfica sempre foi serifada + monoespaçada + sans de interface. O
   que é novo é usar **sans na linha editorial da ficha**, que era
   monoespaçada.

