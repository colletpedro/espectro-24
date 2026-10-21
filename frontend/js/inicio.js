/* Espectro 24 — inicio.js
   A APRESENTAÇÃO da home editorial. Só monta DOM e liga eventos: o que
   mostrar vem de `selecao.js` (manchete, coleção do dia, recém-chegados,
   modo do logo), a busca vem de `busca.js` e toda a prosa vem de
   `textos_home.js`. A rodada de tipografia e paleta troca este arquivo e o
   CSS sem tocar nos outros três.

   Lê só `window.ESPECTRO_INDICE` (`js/indice.js`), nunca o `data.js` de
   5,6 MB — que continua sendo o dado de /filmes e da página do filme. De
   imagem, o índice só tem backdrop, stills e logo: a home NUNCA mostra
   pôster (`poster.js` entra só pela URL do CDN, `P.url`).

   `?dia=AAAA-MM-DD` fixa a data da seleção (conferência manual de um dia
   específico); sem ele, vale o dia de hoje em America/Sao_Paulo. */
(function () {
  "use strict";

  var IDX = window.ESPECTRO_INDICE || { filmes: [] };
  var B = window.ESPECTRO_BUSCA;
  var S = window.ESPECTRO_SELECAO;
  var T = window.ESPECTRO_TEXTOS;
  var P = window.ESPECTRO_POSTER;
  var FILMES = IDX.filmes || [];

  var paramDia = new URLSearchParams(location.search).get("dia");
  var DIA = /^\d{4}-\d{2}-\d{2}$/.test(paramDia || "")
    ? paramDia : S.diaEmSaoPaulo(new Date());

  function el(tag, classe, texto) {
    var n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texto != null) n.textContent = texto;
    return n;
  }

  function hrefFilme(slug) { return "filme.html?slug=" + encodeURIComponent(slug); }
  var HREF_CATALOGO = "filmes/";

  // --- barra espectral segmentada (marca) — a mesma de /filmes ---
  var brand = document.getElementById("brandBar");
  if (brand) {
    ["#e5484d", "#f5820b", "#f5a623", "#f5c518", "#8bbf3f", "#46a758",
     "#2e9c8e", "#3b82f6"].forEach(function (c) {
      var s = el("span");
      s.style.background = c;
      brand.appendChild(s);
    });
  }

  // --- cabeçalho: nome e links ---
  [["edNome", T.NOME_SITE], ["edLinkFilmes", T.LINK_FILMES],
   ["edLinkMetodo", T.LINK_METODO]].forEach(function (par) {
    var n = document.getElementById(par[0]);
    if (n) n.textContent = par[1];
  });

  // --- busca (no cabeçalho) ---
  (function ligarBusca() {
    var input = document.getElementById("busca");
    var lista = document.getElementById("buscaResultados");
    var vazio = document.getElementById("buscaVazia");
    if (!input || !lista || !vazio) return;
    input.placeholder = T.BUSCA_PLACEHOLDER;

    var motor = B.criar(FILMES);
    var resultados = [];
    var ativo = -1;

    function fechar() {
      lista.hidden = true;
      vazio.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      ativo = -1;
    }

    function marcar(i) {
      ativo = i;
      [].forEach.call(lista.children, function (li, j) {
        li.setAttribute("aria-selected", j === i ? "true" : "false");
        li.classList.toggle("is-ativo", j === i);
      });
      if (i >= 0) {
        input.setAttribute("aria-activedescendant", "busca-op-" + i);
        lista.children[i].scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function render() {
      var q = input.value;
      lista.innerHTML = "";
      ativo = -1;
      input.removeAttribute("aria-activedescendant");
      if (!B.normalizar(q)) { fechar(); return; }
      resultados = motor.buscar(q);
      if (!resultados.length) {
        lista.hidden = true;
        input.setAttribute("aria-expanded", "false");
        vazio.innerHTML = "";
        vazio.appendChild(el("span", null, T.BUSCA_VAZIA + " "));
        var a = el("a", null, T.BUSCA_VAZIA_LINK);
        a.href = HREF_CATALOGO;
        vazio.appendChild(a);
        vazio.hidden = false;
        return;
      }
      vazio.hidden = true;
      resultados.forEach(function (r, i) {
        var li = el("li", "busca__opcao");
        li.id = "busca-op-" + i;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", "false");
        var a = el("a", "busca__link");
        a.href = hrefFilme(r.slug);
        a.tabIndex = -1;
        a.appendChild(el("span", "busca__titulo", r.titulo));
        var extra = [];
        if (r.titulo_nativo) extra.push(r.titulo_nativo);
        if (r.titulo_letterboxd && B.normalizar(r.titulo_letterboxd) !== B.normalizar(r.titulo)) {
          extra.push(r.titulo_letterboxd);
        }
        if (r.ano) extra.push(String(r.ano));
        if (extra.length) a.appendChild(el("span", "busca__meta", extra.join(" · ")));
        li.appendChild(a);
        li.addEventListener("mousemove", function () { if (ativo !== i) marcar(i); });
        lista.appendChild(li);
      });
      lista.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }

    input.addEventListener("input", render);
    input.addEventListener("focus", function () { if (input.value) render(); });
    input.addEventListener("keydown", function (ev) {
      var n = resultados.length;
      if (ev.key === "Escape") {
        if (!lista.hidden || !vazio.hidden) { fechar(); ev.preventDefault(); }
        return;
      }
      // depois de um Esc, a seta para baixo reabre a lista da consulta atual
      if (lista.hidden && ev.key === "ArrowDown" && input.value) {
        render(); n = resultados.length; ev.preventDefault();
        if (lista.hidden) return;
      }
      if (lista.hidden || !n) return;
      if (ev.key === "ArrowDown") { marcar((ativo + 1) % n); ev.preventDefault(); }
      else if (ev.key === "ArrowUp") { marcar(ativo <= 0 ? n - 1 : ativo - 1); ev.preventDefault(); }
      else if (ev.key === "Enter") {
        ev.preventDefault();
        location.href = hrefFilme(resultados[ativo >= 0 ? ativo : 0].slug);
      }
    });
    document.addEventListener("click", function (ev) {
      if (!document.getElementById("buscaCaixa").contains(ev.target)) fechar();
    });
  })();

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

  // ------------------------------------------------------------------
  // 1. MANCHETE (o filme do dia)
  // ------------------------------------------------------------------
  var escolha = S.escolhaDoDia(FILMES, DIA);
  var manchete = escolha && escolha.filme;
  var naPagina = [];

  (function montarManchete() {
    var caixa = document.getElementById("manchete");
    var f = manchete;
    if (!caixa || !f) { if (caixa) caixa.hidden = true; return; }
    naPagina.push(f.slug);
    var j = T.justificar(f, DIA);
    var modo = S.modoDoLogo(f);
    caixa.dataset.slug = f.slug;
    caixa.dataset.gancho = j.gancho;
    caixa.dataset.motivo = escolha.motivo;   // "aniversario" | "permutacao"
    caixa.dataset.modoLogo = modo;           // "logo" | "logo_branco" | "texto"

    var rotulo = el("h2", "visually-hidden", T.ROTULO_FILME_DO_DIA);
    rotulo.id = "mancheteRotulo";
    caixa.appendChild(rotulo);

    var visual = el("a", "ed-manchete__visual");
    visual.href = hrefFilme(f.slug);
    visual.tabIndex = -1;
    visual.setAttribute("aria-hidden", "true");
    visual.appendChild(quadro(f, "ed-manchete__quadro", "100vw", true, true));
    visual.appendChild(faixaDosGrupos(f, "ed-faixa ed-manchete__faixa"));
    caixa.appendChild(visual);

    // O texto vai numa CAIXA com o véu atrás (canto inferior esquerdo do
    // still) — a opacidade `--ed-veu` é MEDIDA para o contraste WCAG >= 4,5
    // da justificativa (scripts/medir_legibilidade.py).
    var texto = el("div", "ed-manchete__texto");
    var caixaTexto = el("div", "ed-manchete__caixa");
    texto.appendChild(caixaTexto);
    var titulo = el("h3", "ed-manchete__titulo");
    var link = el("a");
    link.href = hrefFilme(f.slug);
    function tituloEmTexto() {
      link.innerHTML = "";
      link.className = "ed-manchete__titulo-texto";
      link.textContent = f.titulo;
      caixa.dataset.modoLogo = "texto";
      if (linha) preencherMeta(linha, T.partesDaManchete(f, false));
    }
    var linha = null;
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
    caixaTexto.appendChild(titulo);
    if (f.titulo_nativo) caixaTexto.appendChild(el("p", "ed-manchete__nativo", f.titulo_nativo));
    // o título brasileiro abre a linha só quando o LOGO EXIBIDO escreve
    // outra coisa (`tituloNaLinha`)
    linha = preencherMeta(el("p", "ed-manchete__linha ed-meta"), T.partesDaManchete(f, S.tituloNaLinha(f)));
    caixaTexto.appendChild(linha);
    caixaTexto.appendChild(el("p", "ed-manchete__justificativa", j.texto));
    caixa.appendChild(texto);
  })();

  // ------------------------------------------------------------------
  // 2. COLEÇÃO DO DIA
  // ------------------------------------------------------------------
  function cartao(f, classe, sizes, meta, desloc) {
    var a = el("a", "ed-cartao" + (classe ? " " + classe : ""));
    a.href = hrefFilme(f.slug);
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

  function soAno(f) { return f.ano ? [{ tipo: "ano", texto: String(f.ano) }] : []; }

  (function montarColecao() {
    var caixa = document.getElementById("colecaoDoDia");
    var cd = S.colecaoDoDia(FILMES, DIA, manchete ? manchete.slug : null);
    if (!caixa || !cd || !cd.filmes.length) { if (caixa) caixa.hidden = true; return; }
    var txt = T.textoDaColecao(cd.colecao);
    caixa.dataset.chave = cd.colecao.chave;
    cd.filmes.forEach(function (f) { naPagina.push(f.slug); });

    var topo = el("div", "ed-colecao__topo");
    var bloco = el("div", "ed-colecao__texto");
    bloco.appendChild(el("p", "section-label ed-colecao__rotulo", T.ROTULO_COLECAO));
    var h = el("h2", "ed-colecao__titulo", txt.titulo);
    h.id = "colecaoTitulo";
    bloco.appendChild(h);
    if (txt.descricao) bloco.appendChild(el("p", "ed-colecao__descricao", txt.descricao));
    if (txt.frase) bloco.appendChild(el("p", "ed-colecao__frase", txt.frase));
    if (cd.total > cd.filmes.length) {
      var todos = el("a", "ed-link mono", T.ROTULO_COLECAO_TODOS + " →");
      todos.href = HREF_CATALOGO + "?colecao=" + encodeURIComponent(cd.colecao.chave);
      bloco.appendChild(todos);
    }
    topo.appendChild(bloco);

    var primeiro = cd.filmes[0];
    topo.appendChild(cartao(primeiro, "ed-colecao__destaque",
      "(max-width: 699px) 100vw, 66vw", soAno, 1));
    caixa.appendChild(topo);

    var fileira = el("ul", "ed-colecao__fileira");
    cd.filmes.forEach(function (f) {
      var li = el("li");
      li.appendChild(cartao(f, null, "(max-width: 699px) 40vw, 25vw", soAno));
      fileira.appendChild(li);
    });
    caixa.appendChild(fileira);
  })();

  // ------------------------------------------------------------------
  // 3. RECÉM-CHEGADOS (3 por dia, da leva mais recente)
  // ------------------------------------------------------------------
  (function montarRecem() {
    var caixa = document.getElementById("recemChegados");
    var r = S.recemDoDia(FILMES, DIA, naPagina);
    if (!caixa || !r || !r.filmes.length) { if (caixa) caixa.hidden = true; return; }
    var cab = el("div", "ed-recem__cabeca");
    var h = el("h2", "section-label ed-recem__titulo", T.ROTULO_RECEM);
    h.id = "recemTitulo";
    cab.appendChild(h);
    // "ver todos" abre /filmes FILTRADO pela leva (`?desde=`, lido por
    // catalogo.js) — mesmo critério de data desta seção.
    var todos = el("a", "ed-link mono", T.ROTULO_RECEM_TODOS + " →");
    todos.href = HREF_CATALOGO + "?desde=" + r.desde;
    cab.appendChild(todos);
    caixa.appendChild(cab);
    var grade = el("ul", "ed-recem__grade");
    r.filmes.forEach(function (f) {
      var li = el("li");
      li.appendChild(cartao(f, null, "(max-width: 699px) 100vw, 33vw", T.partesDiretorAno));
      grade.appendChild(li);
    });
    caixa.appendChild(grade);
  })();

  // --- 4. o link para o catálogo inteiro ---
  var verTodos = document.getElementById("verTodos");
  if (verTodos) {
    var a = el("a", "ed-link", T.verOsFilmes(FILMES.length) + " →");
    a.href = HREF_CATALOGO;
    verTodos.appendChild(a);
  }
})();
