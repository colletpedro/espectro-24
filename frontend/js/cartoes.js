/* Espectro 24 — cartoes.js  [rodada Explorar]
   O CARTÃO de filme da home e de /filmes: still 16:9 (backdrop e galeria,
   nunca pôster), título e linha de metadado ABAIXO da imagem, e a troca de
   still no hover. Saiu de inicio.js sem mudança de comportamento, para a
   grade de /filmes ser "igual aos recém-chegados da home, incluindo o
   hover".

   `window.ESPECTRO_CARTOES`: quadro, cartao, preencherMeta, faixaDosGrupos,
   fontes, sequencia, TAMANHO_LOGO e a MANCHETE (`montarManchete`, com o
   bloco do título `blocoDoTitulo`: home e página do filme). `cartao` recebe a RAIZ do site (vazia
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
  var COR_GRUPO = {
    negativas: "var(--grupo-neg)", medianas: "var(--grupo-med)", positivas: "var(--grupo-pos)",
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
      seg.style.background = COR_GRUPO[g];
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


  // ------------------------------------------------------------------
  // A MANCHETE: o still 16:9 com o bloco do título sobre o véu (canto
  // inferior esquerdo) — componente ÚNICO da home e da página do filme
  // (`?topo=estatico`). A regra do logo (`modoDoLogo`: claro, escuro_mono
  // com filtro, o resto em texto) e a do título brasileiro na linha
  // (`tituloNaLinha`) moram em selecao.js e são chamadas AQUI, uma vez só.
  //
  // `opcoes`:
  //   nivel          "h3" (home) | "h1" (página do filme)
  //   href           link do título e do still; ausente = sem link
  //   partes         function (comTitulo) → partes da linha de metadado
  //   justificativa  texto sob a linha (só a home)
  //   faixa          true = a faixa fina dos grupos na base do still
  //   visual         elemento já pronto no lugar do still (página do filme)
  // ------------------------------------------------------------------
  function blocoDoTitulo(caixa, alvo, f, opcoes) {
    var S = window.ESPECTRO_SELECAO;
    var modo = S.modoDoLogo(f);
    caixa.dataset.modoLogo = modo;           // "logo" | "logo_branco" | "texto"
    var titulo = el(opcoes.nivel || "h3", "ed-manchete__titulo");
    var link = el(opcoes.href ? "a" : "span");
    if (opcoes.href) link.href = opcoes.href;
    var linha = null;
    function tituloEmTexto() {
      link.innerHTML = "";
      link.className = "ed-manchete__titulo-texto";
      link.textContent = f.titulo;
      caixa.dataset.modoLogo = "texto";
      if (linha) preencherMeta(linha, opcoes.partes(false));
    }
    if (modo === "logo" || modo === "logo_branco") {
      var logo = el("img", "ed-manchete__logo" + (modo === "logo_branco" ? " is-branco" : ""));
      logo.src = P.url(f.logo.path, TAMANHO_LOGO);
      logo.alt = f.titulo;
      logo.decoding = "async";
      // logo que não carrega cai no título em texto
      logo.addEventListener("error", tituloEmTexto);
      link.appendChild(logo);
    } else {
      link.className = "ed-manchete__titulo-texto";
      link.textContent = f.titulo;
    }
    titulo.appendChild(link);
    alvo.appendChild(titulo);
    if (f.titulo_nativo) alvo.appendChild(el("p", "ed-manchete__nativo", f.titulo_nativo));
    // o título brasileiro abre a linha só quando o LOGO EXIBIDO escreve
    // outra coisa (`tituloNaLinha`)
    linha = preencherMeta(el("p", "ed-manchete__linha ed-meta"), opcoes.partes(S.tituloNaLinha(f)));
    alvo.appendChild(linha);
    return linha;
  }

  function montarManchete(caixa, f, opcoes) {
    if (opcoes.visual) {
      // a página do filme traz o seu (a faixa animada ou o still do topo)
      caixa.appendChild(opcoes.visual);
    } else {
      var visual = el(opcoes.href ? "a" : "div", "ed-manchete__visual");
      if (opcoes.href) { visual.href = opcoes.href; visual.tabIndex = -1; }
      visual.setAttribute("aria-hidden", "true");
      visual.appendChild(quadro(f, "ed-manchete__quadro", "100vw", true, true));
      if (opcoes.faixa) visual.appendChild(faixaDosGrupos(f, "ed-faixa ed-manchete__faixa"));
      caixa.appendChild(visual);
    }

    // O texto vai numa CAIXA com o véu atrás (canto inferior esquerdo do
    // still) — a opacidade `--ed-veu` é MEDIDA para o contraste WCAG >= 4,5
    // da justificativa (scripts/medir_legibilidade.py).
    var texto = el("div", "ed-manchete__texto");
    var caixaTexto = el("div", "ed-manchete__caixa");
    texto.appendChild(caixaTexto);
    blocoDoTitulo(caixa, caixaTexto, f, opcoes);
    if (opcoes.justificativa) {
      caixaTexto.appendChild(el("p", "ed-manchete__justificativa", opcoes.justificativa));
    }
    caixa.appendChild(texto);
    return caixa;
  }

  window.ESPECTRO_CARTOES = {
    TAMANHO_LOGO: TAMANHO_LOGO, INTERVALO_HOVER: INTERVALO_HOVER,
    fontes: fontes, sequencia: sequencia, quadro: quadro, cartao: cartao,
    preencherMeta: preencherMeta, faixaDosGrupos: faixaDosGrupos, el: el,
    blocoDoTitulo: blocoDoTitulo, montarManchete: montarManchete,
  };
})();
