/* [v1.9.43] MODO TELA CHEIA da galeria do mobile.

   Tocar um quadro da galeria (`filme.js`, `galeriaMobileBlock`) abre o
   still ocupando a tela inteira. Fecha por swipe para baixo, por botão
   visível e por Esc; navega entre os stills por swipe lateral e pelas
   setas do teclado.

   SEM indicador, SEM pontinho, SEM seta e SEM contador — a mesma
   proibição que vale para a faixa vale aqui. O botão de fechar é a
   ÚNICA affordance visível, e ele é exigido explicitamente: um modo que
   só fecha por gesto é um modo do qual parte das pessoas não sai.

   A NAVEGAÇÃO LATERAL É SCROLL NATIVO com `scroll-snap`, pelo mesmo
   motivo da faixa: swipe, inércia e encaixe são da plataforma, e
   reimplementá-los à mão sairia pior. O único gesto tratado em código é
   o de FECHAR (arrastar para baixo), que não tem equivalente nativo.

   O FOCO é devolvido ao item de origem ao fechar. Sem isso, quem navega
   por teclado ou leitor de tela volta para o começo do documento a cada
   imagem aberta — o modo tela cheia viraria uma armadilha em vez de um
   detalhe. */
(function () {
  "use strict";

  /* Quantos pixels de arrasto vertical fecham. Abaixo disso o gesto é
     ruído (a mão treme, o dedo desliza ao tocar); muito acima, o gesto
     vira um esforço. 90px é ~11% de um iPhone padrão em altura. */
  var FECHAR_PX = 90;

  /* Proporção mínima entre o movimento vertical e o horizontal para o
     gesto contar como "para baixo". Sem isso, um swipe lateral levemente
     torto fecharia o modo em vez de navegar — e navegar é o gesto que
     mais se usa aqui. */
  var RAZAO_VERTICAL = 1.4;

  /* Decide o que um gesto quer dizer. PURA — é ela que o teste executa,
     com pares de deltas, em vez de simular toque. */
  function gestoFecha(dx, dy) {
    if (dy <= 0) return false;                       // para cima não fecha
    if (dy < FECHAR_PX) return false;                // curto demais
    return dy >= Math.abs(dx) * RAZAO_VERTICAL;      // e claramente vertical
  }

  /* Índice do quadro depois de andar `passo` a partir de `atual`, com
     `n` quadros. NÃO circula: no primeiro, esquerda não faz nada; no
     último, direita não faz nada. É o comportamento da rolagem nativa
     que o teclado precisa imitar — se as setas circulassem e o swipe
     não, os dois entrariam em desacordo sobre onde a pessoa está. */
  function proximoIndice(atual, passo, n) {
    var i = atual + passo;
    if (i < 0) return 0;
    if (i > n - 1) return n - 1;
    return i;
  }

  /* Qual quadro está em foco, dada a posição de rolagem. O trilho tem
     encaixe, então o quadro visível é sempre `scrollLeft / largura`
     arredondado. */
  function indiceVisivel(scrollLeft, largura, n) {
    if (!(largura > 0)) return 0;
    var i = Math.round(scrollLeft / largura);
    return Math.max(0, Math.min(n - 1, i));
  }

  /* Abre o modo tela cheia em `indice`.

     `itens` é `[{src, srcset, sizes, alt}]` — dados, não nós: o lightbox
     monta os seus próprios `<img>` em vez de mover os da galeria, para
     que fechar não precise desfazer nada na página de trás.

     `origem` é o elemento que recebeu o toque; é para ele que o foco
     volta. */
  function abrir(itens, indice, origem) {
    if (!itens || !itens.length) return null;

    var anterior = origem || document.activeElement;

    var caixa = document.createElement("div");
    caixa.className = "lightbox";
    caixa.setAttribute("role", "dialog");
    caixa.setAttribute("aria-modal", "true");
    caixa.setAttribute("aria-label", "Imagem em tela cheia");
    caixa.tabIndex = -1;

    /* CARREGAMENTO SOB DEMANDA, e por que ele é feito À MÃO aqui.
       A primeira versão marcava `loading="lazy"` nos quadros distantes e
       confiava no navegador. MEDIDO ao vivo: abrir o modo tela cheia
       disparou as 12 imagens mesmo assim. O motivo é que o limiar do
       `lazy` nativo depende da conexão, e numa rápida ele chega a alguns
       milhares de pixels — o trilho inteiro tem 12 × a largura da tela
       (4500px num aparelho de 375), e cabe todo dentro do limiar.

       `lazy` não é um teto, é uma dica. Quando o teto precisa existir, o
       `src` é que tem de ser adiado: quadro sem `src` não busca nada, e
       `garantirVizinhanca` atribui os que entram no raio conforme o dedo
       anda. O `loading="lazy"` fica junto como segunda linha, não como a
       primeira. */
    var imgs = [];
    itens.forEach(function (it, i) {
      var quadro = document.createElement("div");
      quadro.className = "lightbox__quadro";
      var img = document.createElement("img");
      img.alt = it.alt || "";
      img.decoding = "async";
      img.loading = "lazy";
      img.dataset.src = it.src;
      if (it.srcset) img.dataset.srcset = it.srcset;
      if (it.sizes) img.sizes = it.sizes;
      imgs.push(img);
      quadro.appendChild(img);
      caixa.appendChild(quadro);
    });

    /* Raio de 1: o quadro aberto e um de cada lado. É o mínimo que faz o
       primeiro swipe (em qualquer direção) já encontrar a imagem pronta,
       e mantém o custo em 3 imagens em vez de 12. */
    var RAIO = 1;

    function garantirVizinhanca(centro) {
      for (var i = Math.max(0, centro - RAIO);
           i <= Math.min(imgs.length - 1, centro + RAIO); i++) {
        var img = imgs[i];
        if (img.getAttribute("src")) continue;
        if (img.dataset.srcset) img.srcset = img.dataset.srcset;
        img.src = img.dataset.src;
      }
    }

    var fechar = document.createElement("button");
    fechar.type = "button";
    fechar.className = "lightbox__fechar";
    fechar.setAttribute("aria-label", "Fechar");
    fechar.textContent = "×";
    caixa.appendChild(fechar);

    // TRAVA DO SCROLL DE TRÁS. `overflow: hidden` no body basta nos
    // navegadores atuais; a classe é o que o CSS lê e o que o teste
    // consegue verificar.
    document.body.classList.add("lightbox-aberto");
    document.body.appendChild(caixa);

    // posiciona sem animação: abrir já é a transição
    caixa.scrollLeft = indice * caixa.clientWidth;
    garantirVizinhanca(indice);
    caixa.focus();

    // conforme o dedo anda, os quadros que entram no raio ganham `src`
    caixa.addEventListener("scroll", function () {
      garantirVizinhanca(
        indiceVisivel(caixa.scrollLeft, caixa.clientWidth, itens.length));
    }, { passive: true });

    var vivo = true;

    function encerrar() {
      if (!vivo) return;
      vivo = false;
      document.removeEventListener("keydown", aoTeclado, true);
      document.body.classList.remove("lightbox-aberto");
      caixa.remove();
      // DEVOLVE O FOCO ao item de origem — não ao topo do documento.
      if (anterior && anterior.focus) anterior.focus();
    }

    function aoTeclado(e) {
      if (e.key === "Escape") { e.preventDefault(); encerrar(); return; }
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        var n = itens.length;
        var atual = indiceVisivel(caixa.scrollLeft, caixa.clientWidth, n);
        var alvo = proximoIndice(atual, e.key === "ArrowRight" ? 1 : -1, n);
        garantirVizinhanca(alvo);
        caixa.scrollLeft = alvo * caixa.clientWidth;
      }
    }

    fechar.addEventListener("click", encerrar);
    document.addEventListener("keydown", aoTeclado, true);

    // GESTO DE FECHAR. Só o eixo vertical é tratado; o horizontal fica
    // inteiramente com o scroll nativo (por isso nada de `preventDefault`
    // no caminho lateral, que mataria o swipe de navegação).
    var y0 = null, x0 = null;
    caixa.addEventListener("touchstart", function (e) {
      if (e.touches.length !== 1) { y0 = null; return; }
      y0 = e.touches[0].clientY;
      x0 = e.touches[0].clientX;
    }, { passive: true });
    caixa.addEventListener("touchend", function (e) {
      if (y0 == null) return;
      var t = (e.changedTouches && e.changedTouches[0]) || null;
      if (t && gestoFecha(t.clientX - x0, t.clientY - y0)) encerrar();
      y0 = x0 = null;
    }, { passive: true });

    return { fechar: encerrar, elemento: caixa };
  }

  var api = {
    FECHAR_PX: FECHAR_PX,
    RAZAO_VERTICAL: RAZAO_VERTICAL,
    gestoFecha: gestoFecha,
    proximoIndice: proximoIndice,
    indiceVisivel: indiceVisivel,
    abrir: abrir,
  };
  if (typeof window !== "undefined") window.ESPECTRO_LIGHTBOX = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
