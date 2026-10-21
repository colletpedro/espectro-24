/* Espectro 24 — cartoes.js  [rodada Explorar]
   O CARTÃO de filme da home e de /filmes: still 16:9 (backdrop e galeria,
   nunca pôster), título e linha de metadado ABAIXO da imagem, e a troca de
   still no hover. Saiu de inicio.js sem mudança de comportamento, para a
   grade de /filmes ser "igual aos recém-chegados da home, incluindo o
   hover".

   `window.ESPECTRO_CARTOES`: quadro, cartao, preencherMeta, faixaDosGrupos,
   fontes, sequencia e TAMANHO_LOGO. `cartao` recebe a RAIZ do site (vazia
   na home, "../" em /filmes) para o link da página do filme. */
(function () {
  "use strict";

  var T = window.ESPECTRO_TEXTOS;
  var P = window.ESPECTRO_POSTER;

  function el(tag, classe, texto) {
    var n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texto != null) n.textContent = texto;
    return n;
  }

  // ------------------------------------------------------------------
  // IMAGENS: só backdrop e stills 16:9 (CDN do TMDB, larguras de backdrop
  // w300 · w780 · w1280) e o logo (w500). Cantos retos e sem sombra são CSS.
  // ------------------------------------------------------------------
  var LARGURAS_STILL = ["w300", "w780", "w1280"];
  var PX_LARGURA = { w300: 300, w780: 780, w1280: 1280 };
  var TAMANHO_LOGO = "w500";

  function fontes(path) {
    return {
      src: P.url(path, "w780"),
      srcset: LARGURAS_STILL.map(function (w) {
        return P.url(path, w) + " " + PX_LARGURA[w] + "w";
      }).join(", "),
    };
  }

  // A sequência de quadros do filme: o backdrop publicado primeiro (o mesmo
  // quadro de sempre) e depois a galeria SEM o primeiro item, que é o grupo
  // do próprio backdrop (ele ou um gêmeo perceptual, `stills_da_galeria`).
  function sequencia(f) {
    var hero = f.imagens && f.imagens.backdrop_path;
    var resto = (f.stills || []).slice(hero ? 1 : 0).filter(function (p) { return p !== hero; });
    return (hero ? [hero] : []).concat(resto);
  }

  // `fixo`: sem troca no hover (a manchete; a troca é da coleção e dos
  // recém-chegados). `desloc`: abre no quadro de posição `desloc` da
  // sequência (o still grande da coleção abre no segundo quadro, para não
  // repetir a imagem do mesmo filme na fileira logo abaixo).
  function quadro(f, classe, sizes, eager, fixo, desloc) {
    var seq = sequencia(f);
    var k = desloc && seq.length > desloc ? desloc : 0;
    seq = seq.slice(k).concat(seq.slice(0, k));
    var caixa = el("span", "ed-quadro" + (classe ? " " + classe : ""));
    if (!seq.length) return caixa;
    var img = el("img", "ed-quadro__img");
    var fo = fontes(seq[0]);
    img.src = fo.src;
    img.srcset = fo.srcset;
    img.sizes = sizes;
    img.alt = "";
    img.width = 16;
    img.height = 9;
    img.decoding = "async";
    if (!eager) img.loading = "lazy";
    img.dataset.path = seq[0];
    caixa.appendChild(img);
    if (!fixo) ligarTroca(caixa, img, seq);
    return caixa;
  }

  // HOVER (desktop): troca pelo próximo still da galeria a cada INTERVALO_HOVER
  // e volta ao primeiro ao sair. Sem troca automática com movimento reduzido
  // e em aparelho sem hover de verdade (toque).
  var INTERVALO_HOVER = 1200;
  var reduzMovimento = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var temHover = window.matchMedia && window.matchMedia("(hover: hover)").matches;

  function mostrar(img, path) {
    var fo = fontes(path);
    img.srcset = fo.srcset;
    img.src = fo.src;
    img.dataset.path = path;
  }

  function ligarTroca(alvo, img, seq) {
    if (reduzMovimento || !temHover || seq.length < 2) return;
    var timer = null, i = 0;
    function sobre() {
      if (timer) return;
      // pré-carrega o próximo, para a troca não piscar
      new Image().src = fontes(seq[1 % seq.length]).src;
      timer = setInterval(function () {
        i = (i + 1) % seq.length;
        mostrar(img, seq[i]);
        new Image().src = fontes(seq[(i + 1) % seq.length]).src;
      }, INTERVALO_HOVER);
    }
    function fora() {
      clearInterval(timer);
      timer = null;
      if (i !== 0) { i = 0; mostrar(img, seq[0]); }
    }
    alvo.addEventListener("mouseenter", sobre);
    alvo.addEventListener("mouseleave", fora);
  }

  // Linha de metadado em partes: cada uma num `span.ed-meta__<tipo>`,
  // separadas por `span.ed-meta__sep` — o texto corrido é o mesmo de
  // `T.linhaDaManchete`; o CSS da prova de fontes põe o diretor em negrito.
  function preencherMeta(alvo, partes) {
    alvo.innerHTML = "";
    partes.forEach(function (p, i) {
      if (i) alvo.appendChild(el("span", "ed-meta__sep", T.SEPARADOR));
      alvo.appendChild(el("span", "ed-meta__" + p.tipo, p.texto));
    });
    return alvo;
  }

  // A faixa fina dos três grupos (a mesma semântica e paleta do mosaico).
  var GRUPOS = ["negativas", "medianas", "positivas"];
  var COR_GRUPO_HOME = {
    negativas: "var(--neg-home)", medianas: "var(--med-home)", positivas: "var(--pos-home)",
  };

  function faixaDosGrupos(f, classe) {
    var strip = el("span", classe);
    strip.setAttribute("aria-hidden", "true");
    var d = f.distribuicao;
    var total = d ? GRUPOS.reduce(function (s, g) { return s + (d[g] || 0); }, 0) : 0;
    if (!total) { strip.classList.add("is-vazia"); return strip; }
    GRUPOS.forEach(function (g) {
      if (!(d[g] > 0)) return;
      var seg = el("span", "ed-faixa__seg");
      seg.style.background = COR_GRUPO_HOME[g];
      seg.style.width = (d[g] / total) * 100 + "%";
      strip.appendChild(seg);
    });
    return strip;
  }

  function cartao(f, classe, sizes, meta, desloc, raiz) {
    var a = el("a", "ed-cartao" + (classe ? " " + classe : ""));
    a.href = (raiz || "") + "filme.html?slug=" + encodeURIComponent(f.slug);
    a.dataset.slug = f.slug;
    a.appendChild(quadro(f, null, sizes, false, false, desloc));
    var corpo = el("span", "ed-cartao__corpo");
    corpo.appendChild(el("span", "ed-cartao__titulo", f.titulo));
    if (f.titulo_nativo) corpo.appendChild(el("span", "ed-cartao__nativo", f.titulo_nativo));
    var partes = meta(f);
    if (partes.length) corpo.appendChild(preencherMeta(el("span", "ed-cartao__meta ed-meta"), partes));
    a.appendChild(corpo);
    return a;
  }


  window.ESPECTRO_CARTOES = {
    TAMANHO_LOGO: TAMANHO_LOGO, INTERVALO_HOVER: INTERVALO_HOVER,
    fontes: fontes, sequencia: sequencia, quadro: quadro, cartao: cartao,
    preencherMeta: preencherMeta, faixaDosGrupos: faixaDosGrupos, el: el,
  };
})();
