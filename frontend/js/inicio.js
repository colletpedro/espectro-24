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
  var X = window.ESPECTRO_EXPLORAR;
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

  // O cabeçalho (barra, nome, links, busca) é de js/cabecalho.js; o cartão
  // de filme (still, título, metadado, hover), de js/cartoes.js.
  var C = window.ESPECTRO_CARTOES;
  var quadro = C.quadro, preencherMeta = C.preencherMeta,
      faixaDosGrupos = C.faixaDosGrupos, TAMANHO_LOGO = C.TAMANHO_LOGO;

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
    return C.cartao(f, classe, sizes, meta, desloc, "");
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

  // ------------------------------------------------------------------
  // 4. EXPLORAR — as portas de entrada de /filmes, só texto. Conta só os
  // ELEGÍVEIS (fora a lista de exclusão da vitrine). No desktop os quatro
  // grupos ficam abertos lado a lado; abaixo de 700px cada um é um
  // <details> fechado, com o número de itens no <summary>.
  // ------------------------------------------------------------------
  (function montarExplorar() {
    var caixa = document.getElementById("explorar");
    if (!caixa) return;
    var g = X.gruposDoExplorar(FILMES, { elegiveis: true, piso: X.PISO_HOME });
    var h = el("h2", "section-label ed-explorar__titulo", T.TITULO_EXPLORAR);
    h.id = "explorarTitulo";
    caixa.appendChild(h);
    var colunas = el("div", "ed-explorar__grupos");
    var PARAM = { assunto: "colecao", decada: "decada", genero: "genero", pais: "pais" };
    var grupos = [];
    ["assunto", "decada", "genero", "pais"].forEach(function (k) {
      if (!g[k].length) return;
      var d = el("details", "ed-explorar__grupo");
      d.dataset.grupo = k;
      var s = el("summary", "ed-explorar__nome");
      s.appendChild(el("span", null, T.ROTULO_GRUPO_EXPLORAR[k]));
      s.appendChild(el("span", "ed-explorar__quantos", " (" + g[k].length + ")"));
      d.appendChild(s);
      var ul = el("ul", "ed-explorar__lista");
      g[k].forEach(function (it) {
        var li = el("li");
        var a = el("a", "ed-explorar__item");
        a.href = HREF_CATALOGO + "?" + PARAM[k] + "=" + encodeURIComponent(String(it.chave));
        a.dataset.n = it.n;
        a.appendChild(el("span", null, it.nome));
        a.appendChild(el("span", "ed-explorar__n", " (" + it.n + ")"));
        li.appendChild(a);
        ul.appendChild(li);
      });
      d.appendChild(ul);
      colunas.appendChild(d);
      grupos.push(d);
    });
    caixa.appendChild(colunas);
    var indice = el("p", "ed-explorar__indice");
    var ai = el("a", "ed-link mono", T.LINK_INDICE + " →");
    ai.href = HREF_CATALOGO + "?vista=indice";
    indice.appendChild(ai);
    caixa.appendChild(indice);

    // abertos no desktop, fechados no mobile; no desktop o <summary> não
    // fecha o grupo (é só o título da coluna)
    var largo = window.matchMedia ? window.matchMedia("(min-width: 700px)") : null;
    function ajustar() {
      var aberto = !largo || largo.matches;
      grupos.forEach(function (d) { d.open = aberto; });
      caixa.classList.toggle("is-colunas", aberto);
    }
    grupos.forEach(function (d) {
      d.querySelector("summary").addEventListener("click", function (ev) {
        if (!largo || largo.matches) ev.preventDefault();
      });
    });
    if (largo && largo.addEventListener) largo.addEventListener("change", ajustar);
    ajustar();
  })();
})();
