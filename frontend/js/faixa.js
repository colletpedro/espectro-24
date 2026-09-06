/* [v1.9.41] FAIXA DE ROLAGEM CONTÍNUA da galeria de stills.

   Substitui a grade estática de 4 colunas (v1.9.39) por uma faixa
   horizontal que anda sozinha, devagar, da direita para a esquerda.
   Mudança de escopo AUTORIZADA pelo dono do produto; a sensação alvo é
   "o filme está passando diante de mim". Mesma posição na página, mesma
   proporção 16:9 por item, mesmo risco de spoiler assumido (`ficha.py`).

   POR QUE SCROLL NATIVO E NÃO `transform` ANIMADO POR CSS — a escolha é
   deliberada e não deve ser "simplificada" depois. Uma animação de
   `translateX` roda fora da thread principal e é mais barata, mas o
   elemento animado não tem posição de scroll: arrastar, deslizar com o
   dedo ou usar o trackpad deixam de funcionar, e recuperá-los exigiria
   reimplementar inércia à mão. Aqui o contêiner tem `overflow-x: auto` e
   o movimento automático é só `scrollLeft += v·dt` — arrasto, swipe,
   trackpad e roda horizontal continuam sendo o scroll nativo do
   navegador, de graça, com a inércia da plataforma.

   O LOOP não é `scrollLeft = 0` ao chegar no fim (isso pisca). A trilha
   carrega a sequência DUPLICADA, e ao cruzar a largura de UMA cópia
   subtrai-se exatamente essa largura: como o pixel na posição `x` e o
   pixel em `x + largura_de_uma_copia` são a mesma imagem, o salto é
   invisível. As duplicatas reusam as mesmas URLs (cache do navegador,
   zero download novo) e são `aria-hidden` — ninguém deve ouvir 32
   stills onde existem 16.

   As funções PURAS abaixo (`passoDoQuadro`, `normalizarScroll`,
   `velocidadeComRampa`, `deveRolar`) não tocam o DOM de propósito: são o
   que os testes executam de verdade sob node, em vez de checar o texto
   do arquivo (ver `test_faixa_stills.py`). */
(function () {
  "use strict";

  /* [v1.9.42] A velocidade passou a ser declarada em SEGUNDOS POR QUADRO
     DA FAIXA, e não mais em pixels por segundo.

     O motivo é a mudança de escopo: a faixa virou o HERO, e o item deixou
     de ter largura fixa de 172px para ocupar a coluna inteira — MEDIDO,
     720px no desktop e 375px no mobile. Um px/s fixo daria, nesses dois
     tamanhos, ritmos completamente diferentes: os 28 px/s calibrados para
     a miniatura levariam **25,7s** para trocar um quadro no desktop e
     13,4s no mobile. O mesmo movimento, tempos diferentes, sem nenhuma
     razão de produto para isso.

     Declarado em tempo, o ritmo é o MESMO nos dois: 12s por quadro dão
     60 px/s no desktop e 31 px/s no mobile, e um quadro leva 12 segundos
     para atravessar a tela em qualquer aparelho. A conversão para px/s
     acontece uma vez, na medição (`ligar`), a partir da largura real —
     nada no núcleo do movimento mudou.

     [v1.9.43] **12s → 18s**, por decisão do dono depois de ver a faixa
     rodando. Com a faixa full-bleed, o que se percebe não é mais o tempo
     de um quadro isolado e sim o tempo de a TELA INTEIRA se renovar — e
     essa grandeza cresceu junto com a largura. MEDIDO (item de 720px):

         s/quadro | px/s | tela cheia em 1440 | em 2560
               12 |   60 |               24 s |    43 s
               16 |   45 |               32 s |    57 s
               18 |   40 |               36 s |    64 s   <- ESCOLHIDO
               20 |   36 |               40 s |    71 s
               24 |   30 |               48 s |    85 s

     18s/quadro = 40 px/s: um terço mais lento que antes, com a tela de
     1440 levando 36 s para se renovar por inteiro e a de 2560, mais de um
     minuto. Com `TETO_STILLS = 12`, a volta inteira leva 3min36. */
  var SEGUNDOS_POR_QUADRO = 18;

  /* Piso de segurança, em px/s. Uma faixa medida antes do layout poderia
     produzir uma largura minúscula e, com ela, uma velocidade que na
     prática é zero — parada, sem nada dizer que parou. */
  var VELOCIDADE_MIN_PX_S = 4;

  /* A velocidade em px/s para um item desta largura. Pura: os testes
     verificam com ela que desktop e mobile levam o MESMO tempo por
     quadro. */
  function velocidadeParaItem(larguraItem) {
    if (!(larguraItem > 0)) return VELOCIDADE_MIN_PX_S;
    return Math.max(VELOCIDADE_MIN_PX_S, larguraItem / SEGUNDOS_POR_QUADRO);
  }

  /* Rampa de retomada, em segundos. Voltar de 0 para 28 px/s num quadro
     só dá um solavanco visível justamente no momento em que o leitor
     acabou de soltar o dedo. Com a rampa, a faixa "reencontra" a
     velocidade em ~0,45s. Só a RETOMADA é suavizada: a PAUSA é
     instantânea, porque quem toca a faixa quer que ela pare agora. */
  var RAMPA_S = 0.45;

  /* Teto de delta entre dois quadros. Sem ele, uma aba que ficou em
     segundo plano por 30s voltaria com `dt = 30s` e daria um salto de
     840px de uma vez. `requestAnimationFrame` não roda em aba oculta, e
     esse é o caso normal, não um caso raro. */
  var DT_MAX_S = 0.05;

  // ---------------------------------------------------------------
  // Núcleo PURO — sem DOM, sem relógio próprio, sem estado global.
  // ---------------------------------------------------------------

  /* Quantos pixels a faixa anda entre dois instantes, e o instante novo.
     `dtMs` é derivado dos timestamps que o rAF entrega, NUNCA um
     incremento fixo — é isto que torna a velocidade independente da taxa
     de quadros. O primeiro quadro (sem `ultimoMs`) anda ZERO: não há
     intervalo medido ainda, e chutar um daria um salto inicial. */
  function passoDoQuadro(ultimoMs, agoraMs, velocidade) {
    if (ultimoMs == null || !(agoraMs > ultimoMs)) return 0;
    var dt = (agoraMs - ultimoMs) / 1000;
    if (dt > DT_MAX_S) dt = DT_MAX_S;
    return velocidade * dt;
  }

  /* Reposiciona o scroll dentro da PRIMEIRA cópia da sequência.
     `larguraCiclo` é a largura de UMA cópia. Devolve sempre um valor em
     [0, larguraCiclo), e a subtração é exata — não é `% larguraCiclo` com
     ponto flutuante acumulando erro, é o mesmo número que o navegador
     tem. Vale para os dois sentidos: arrastar para trás do zero cai no
     fim da primeira cópia, também sem piscar. */
  function normalizarScroll(pos, larguraCiclo) {
    if (!(larguraCiclo > 0)) return pos;
    while (pos >= larguraCiclo) pos -= larguraCiclo;
    while (pos < 0) pos += larguraCiclo;
    return pos;
  }

  /* Velocidade efetiva do quadro, subindo em rampa até `alvo`. Pausa
     (alvo 0) é imediata; retomada sobe linearmente em `RAMPA_S`.

     [v1.9.42] A inclinação da rampa deriva do `alvo`, e não mais de uma
     constante global de velocidade — que deixou de existir quando a
     velocidade passou a sair da largura medida do item. Com `alvo` na
     fórmula, a rampa leva `RAMPA_S` para completar em qualquer aparelho,
     que é o que ela sempre prometeu; com a constante, ela levaria tempos
     diferentes no desktop e no mobile. */
  function velocidadeComRampa(atual, alvo, dtMs) {
    if (alvo <= 0) return 0;
    var passo = (alvo / RAMPA_S) * (Math.max(0, dtMs) / 1000);
    return Math.min(alvo, atual + passo);
  }

  /* O PERÍODO da repetição, dado o `offsetLeft` de cada item da trilha
     duplicada. **Não é `scrollWidth / 2`**, e a diferença não é teórica:
     uma trilha com `2n` itens tem `2n − 1` intervalos, não `2n`, porque
     não há gap depois do último. Metade da largura total fica meio gap
     curta — medido ao vivo em `wonka` (16 itens de 172px, gap de 10px):
     `scrollWidth / 2` = 2907px contra o período verdadeiro de 2912px.

     Cinco pixels, uma vez por volta, sempre no mesmo sentido: é
     exatamente o "salto visível" que o loop existe para não ter. O
     período certo é a distância entre um item e a sua própria cópia, que
     não depende de contar gaps. */
  function periodoDaTrilha(offsets, n) {
    if (!offsets || offsets.length < 2 * n || n <= 0) return 0;
    return offsets[n] - offsets[0];
  }

  /* Quantos quadros de cada lado do CENTRO já devem ter `src`. A janela
     carregada é `2 × raio + 1` quadros, então o raio é METADE do que
     cabe na tela, mais 1 de margem — a margem é o que faz o quadro
     entrar já carregado em vez de aparecer em branco e preencher depois.

     Dividir por 2 não é detalhe: com o raio igual ao número de quadros
     visíveis, a 2560 a janela seria de 11 imagens (1,52 MB) e o
     carregamento sob demanda não teria servido para nada. Com metade,
     são 7 (0,97 MB) a 2560 e 5 (0,69 MB) a 1440. */
  function raioDeCarga(larguraVisivel, larguraItem) {
    if (!(larguraItem > 0)) return 1;
    return Math.ceil(larguraVisivel / larguraItem / 2) + 1;
  }

  /* A faixa só anda se houver material para andar. Com poucos itens
     (perto de `PISO_STILLS = 3`) a trilha não enche a largura visível, e
     rolar significaria abrir um vão vazio e trazê-lo de volta ciclicamente
     — pior que não rolar. Aqui a resposta é renderizar ESTÁTICO.
     `reduzMovimento` é a segunda porta: `prefers-reduced-motion: reduce`
     desliga a rolagem automática SEM desligar a faixa, que continua
     rolável à mão e com todos os itens alcançáveis. */
  function deveRolar(larguraCiclo, larguraVisivel, reduzMovimento) {
    if (reduzMovimento) return false;
    return larguraCiclo > larguraVisivel;
  }

  // ---------------------------------------------------------------
  // Camada com DOM.
  // ---------------------------------------------------------------

  function prefereMenosMovimento() {
    try {
      return !!(window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (e) { return false; }
  }

  /* Liga a faixa: `trilha` já contém os itens (uma cópia). Duplica a
     sequência, mede, e só então decide se anima.

     A medição é feita DEPOIS do layout e é refeita no `resize` — a
     largura de uma cópia depende da largura do contêiner, que muda ao
     girar o aparelho. */
  function montarFaixa(viewport, trilha) {
    var estado = {
      pos: 0,             // acumulador em float; `scrollLeft` arredonda
      ultimoMs: null,
      velocidade: 0,      // efetiva, com rampa
      alvo: 0,            // 0 = pausado
      alvoCheio: 0,       // px/s derivado da largura MEDIDA do item
      larguraCiclo: 0,
      rodando: false,
      duplicado: false,
      ultimoEscrito: 0,
      motivos: {},        // pausas ativas, por nome — ver `pausar`
      retomada: null,
    };

    function medir() {
      /* [v1.9.42] A velocidade sai daqui, da largura REAL do primeiro
         item, e não de uma constante — ver `velocidadeParaItem`. Refeita a
         cada medição, então girar o aparelho reajusta o ritmo sozinho. */
      var primeiro = trilha.children[0];
      estado.alvoCheio = velocidadeParaItem(
        primeiro ? primeiro.getBoundingClientRect().width : 0);
      if (estado.alvo > 0) estado.alvo = estado.alvoCheio;
      if (!estado.duplicado) {
        // Antes de duplicar, a pergunta é só "isto transborda?" — e para
        // isso a largura do conteúdo serve.
        estado.larguraCiclo = trilha.scrollWidth;
        return;
      }
      var filhos = trilha.children;
      var n = filhos.length / 2;
      var offsets = [];
      for (var i = 0; i < filhos.length; i++) offsets.push(filhos[i].offsetLeft);
      estado.larguraCiclo = periodoDaTrilha(offsets, n);
    }

    function duplicar() {
      if (estado.duplicado) return;
      var originais = Array.prototype.slice.call(trilha.children);
      originais.forEach(function (no) {
        var copia = no.cloneNode(true);
        // A cópia é pixel, não conteúdo: leitor de tela e teclado
        // enxergam só a primeira sequência.
        copia.setAttribute("aria-hidden", "true");
        trilha.appendChild(copia);
      });
      estado.duplicado = true;
    }

    /* Pausa por MOTIVO, e não por booleano — o mecanismo fica; o que
       mudou na v1.9.43 foi a LISTA de motivos.

       Sobrou UM: `scroll`. Passar o mouse por cima NÃO pausa mais, e
       receber foco também não (decisão do dono: a faixa não deve parar só
       porque o cursor cruzou o topo da página, que é por onde o cursor
       passa o tempo todo). Pausa apenas quando o usuário AGE sobre a
       faixa — roda, trackpad, arrasto, swipe —, e todos esses chegam aqui
       como evento de scroll do contêiner.

       O mecanismo continua sendo um conjunto porque o custo dele é uma
       linha e o benefício aparece na primeira vez que um segundo motivo
       voltar: com um booleano, dois motivos simultâneos fazem o primeiro
       a terminar religar a faixa por baixo do outro. */
    /* CARREGAMENTO SOB DEMANDA da faixa. Os quadros nascem com o endereço
       em `data-src` (`caixaDeImagem`, `poster.js`) e só ganham `src`
       quando entram no raio — sem isso a abertura da página buscaria as
       12 imagens de uma vez, 1,62 MB, MEDIDO. Percorre só a primeira
       cópia: a segunda é clone e reusa as mesmas URLs do cache. */
    function carregarVizinhanca() {
      var filhos = trilha.children;
      var n = estado.duplicado ? filhos.length / 2 : filhos.length;
      if (!n) return;
      var largura = filhos[0].getBoundingClientRect().width;
      var centro = largura > 0
        ? Math.floor((viewport.scrollLeft + viewport.clientWidth / 2) / largura)
        : 0;
      var raio = raioDeCarga(viewport.clientWidth, largura);
      for (var k = centro - raio; k <= centro + raio; k++) {
        // o índice circula: a faixa é um loop, e o vizinho do último é o
        // primeiro (que a segunda cópia mostra em seguida)
        var i = ((k % n) + n) % n;
        var img = filhos[i].querySelector("img");
        if (!img || img.getAttribute("src") || !img.dataset.src) continue;
        if (img.dataset.srcset) img.srcset = img.dataset.srcset;
        img.src = img.dataset.src;
        // a cópia do loop aponta para a mesma URL: preenche junto para
        // não piscar quando a trilha der a volta
        if (estado.duplicado) {
          var gemea = filhos[i + n] && filhos[i + n].querySelector("img");
          if (gemea && !gemea.getAttribute("src") && gemea.dataset.src) {
            if (gemea.dataset.srcset) gemea.srcset = gemea.dataset.srcset;
            gemea.src = gemea.dataset.src;
          }
        }
      }
    }

    function pausar(motivo) {
      estado.motivos[motivo] = true;
      estado.alvo = 0;
      estado.velocidade = 0;
    }
    function retomar(motivo) {
      delete estado.motivos[motivo];
      if (!estado.rodando) return;
      for (var k in estado.motivos) { if (estado.motivos[k]) return; }
      estado.alvo = estado.alvoCheio;
    }

    function quadro(agoraMs) {
      if (!estado.rodando) return;
      var dtMs = estado.ultimoMs == null ? 0 : agoraMs - estado.ultimoMs;
      estado.velocidade = velocidadeComRampa(estado.velocidade, estado.alvo, dtMs);
      var passo = passoDoQuadro(estado.ultimoMs, agoraMs, estado.velocidade);
      estado.ultimoMs = agoraMs;
      if (passo > 0) {
        estado.pos = normalizarScroll(estado.pos + passo, estado.larguraCiclo);
        viewport.scrollLeft = estado.pos;
        estado.ultimoEscrito = viewport.scrollLeft;
        carregarVizinhanca();
      }
      window.requestAnimationFrame(quadro);
    }

    /* Distinguir o scroll NOSSO do scroll do usuário: comparar a posição
       lida com a última que escrevemos, em vez de um sinalizador de
       "acabei de escrever". O evento de scroll é assíncrono e pode
       chegar depois de dois quadros nossos — com sinalizador, um gesto
       real do usuário no meio disso seria engolido. A folga de 2px cobre
       o arredondamento que o navegador faz ao guardar `scrollLeft`. */
    viewport.addEventListener("scroll", function () {
      if (Math.abs(viewport.scrollLeft - estado.ultimoEscrito) < 2) return;
      estado.pos = normalizarScroll(viewport.scrollLeft, estado.larguraCiclo);
      carregarVizinhanca();
      pausar("scroll");
      clearTimeout(estado.retomada);
      // Retomada só depois que o gesto claramente acabou. Sem a espera, a
      // faixa brigaria com a inércia do trackpad quadro a quadro.
      estado.retomada = setTimeout(function () { retomar("scroll"); }, 900);
    }, { passive: true });

    // [v1.9.43] NÃO há mais escuta de `pointerenter`/`pointerleave` (hover)
    // nem de `focusin`/`focusout`. Arrasto e swipe continuam pausando —
    // não por `pointerdown`, mas porque arrastar um contêiner rolável
    // DISPARA scroll, e o listener acima trata isso. Um toque sem
    // movimento não pausa, e é o comportamento pedido: só ação de scroll
    // pausa.

    function ligar() {
      medir();
      if (estado.rodando) {
        // já rodando: só reancorar a posição na largura nova
        estado.pos = normalizarScroll(estado.pos, estado.larguraCiclo);
        return;
      }
      if (!deveRolar(estado.larguraCiclo, viewport.clientWidth,
                     prefereMenosMovimento())) {
        // faixa que não anda (poucos itens, ou movimento reduzido) ainda
        // precisa das imagens do que está à vista — senão fica em branco
        carregarVizinhanca();
        return;
      }
      duplicar();
      medir();
      carregarVizinhanca();
      estado.rodando = true;
      estado.ultimoMs = null;
      estado.alvo = estado.alvoCheio;
      window.requestAnimationFrame(quadro);
    }

    /* QUANDO medir — e por que são DOIS mecanismos, não um.

       Não dá para medir aqui e agora: `galeriaBlock` monta a seção e só
       depois `render()` a anexa ao documento, e elemento fora do
       documento tem `clientWidth` e `scrollWidth` iguais a ZERO —
       `deveRolar` responderia "não role" para toda galeria, sempre. Foi
       exatamente o que aconteceu na primeira verificação ao vivo desta
       versão: 16 itens no DOM, nenhuma cópia, faixa parada.

       O ARRANQUE é um `requestAnimationFrame`: ele roda depois que a
       tarefa atual termina, ou seja, depois de `render()` ter anexado
       tudo, e antes da primeira pintura. Chegou a estar em
       `ResizeObserver` sozinho, e a segunda verificação ao vivo mostrou
       por que isso não basta — no navegador embutido usado para conferir,
       o observer não disparou NENHUMA vez, nem para um elemento com
       tamanho. Arranque que depende de um observador disparar é arranque
       que pode simplesmente não acontecer.

       O RESIZE é o observer (quando existe): pega a virada do aparelho e
       a mudança de largura da coluna, que o rAF único não veria.
       `ligar()` é idempotente de propósito, então os dois caminhos podem
       chamá-lo à vontade. */
    window.requestAnimationFrame(ligar);
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(ligar).observe(viewport);
    } else {
      window.addEventListener("resize", ligar);
    }
    return estado;
  }

  var api = {
    SEGUNDOS_POR_QUADRO: SEGUNDOS_POR_QUADRO,
    VELOCIDADE_MIN_PX_S: VELOCIDADE_MIN_PX_S,
    velocidadeParaItem: velocidadeParaItem,
    RAMPA_S: RAMPA_S,
    DT_MAX_S: DT_MAX_S,
    passoDoQuadro: passoDoQuadro,
    normalizarScroll: normalizarScroll,
    velocidadeComRampa: velocidadeComRampa,
    deveRolar: deveRolar,
    raioDeCarga: raioDeCarga,
    periodoDaTrilha: periodoDaTrilha,
    montarFaixa: montarFaixa,
  };

  if (typeof window !== "undefined") window.ESPECTRO_FAIXA = api;

  // Exportação para o teste sob node, que não tem `window` — é assim que
  // as funções puras acima são EXECUTADAS pelo teste, e não só lidas como
  // texto (a convenção anterior do projeto, ver `test_galeria_frontend.py`).
  // No navegador esta linha não faz nada: `module` não existe lá.
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
