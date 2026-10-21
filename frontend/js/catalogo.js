/* Espectro 24 — catalogo.js  [rodada Explorar]
   /filmes como página EXPLORAR. Substitui o mosaico de pôsteres (v1.9.17–
   rodada editorial) e a busca por título ou eixo sobre data.js: a página
   agora lê só `js/indice.js` (o cabeçalho, com a busca por título, é de
   cabecalho.js).

   O que mostrar vem de explorar.js (filtros em AND, ordem padrão, Índice
   A–Z, URL ⇄ filtros); o cartão de filme, de cartoes.js (o mesmo dos
   recém-chegados da home, com o hover); a prosa, de textos_home.js.
   Nenhuma ordenação nem filtro lê a distribuição dos grupos.

   ESTADO = os filtros e a vista, sempre na URL (`?colecao=`, `?decada=`,
   `?genero=`, `?pais=`, `?desde=` e `?vista=indice`): qualquer estado é um
   link. A paginação (24 por vez, "Mostrar mais") NÃO vai para a URL.
   `?desde=` (o "ver todos os recém-chegados" da home) e `?colecao=` (o
   "ver todos" da coleção do dia) continuam valendo, agora combináveis com
   os outros filtros. */
(function () {
  "use strict";

  var IDX = window.ESPECTRO_INDICE || { filmes: [] };
  var X = window.ESPECTRO_EXPLORAR;
  var T = window.ESPECTRO_TEXTOS;
  var C = window.ESPECTRO_CARTOES;
  var FILMES = IDX.filmes || [];
  var RAIZ = "../";

  var el = C.el;

  var estado = X.lerFiltros(location.search);
  var mostrados = X.PAGINA;

  // As opções dos filtros: tudo o que existe no catálogo inteiro (piso 1).
  var OPCOES = X.gruposDoExplorar(FILMES, { piso: 1 });
  var FILTROS = [
    { chave: "colecao", grupo: "assunto" },
    { chave: "decada", grupo: "decada" },
    { chave: "genero", grupo: "genero" },
    { chave: "pais", grupo: "pais" },
  ];

  function nomeDoFiltro(chave, valor) {
    if (chave === "desde") return T.chipDesde(valor);
    if (chave === "colecao") return T.tituloDaPrateleira(valor);
    if (chave === "decada") return X.rotuloDaDecada(valor);
    if (chave === "pais") return T.nomeDoPais(valor);
    var g = OPCOES.genero.filter(function (o) { return o.chave === valor; })[0];
    return g ? g.nome : valor;
  }

  function irPara(filtros, vista) {
    estado = { filtros: filtros, vista: vista };
    mostrados = X.PAGINA;
    var url = location.pathname + X.urlDosFiltros(filtros, vista);
    if (url !== location.pathname + location.search) history.pushState(null, "", url);
    render();
  }

  function semFiltro(chave) {
    var f = {};
    Object.keys(estado.filtros).forEach(function (k) { if (k !== chave) f[k] = estado.filtros[k]; });
    return f;
  }

  // --- título ---
  var titulo = document.getElementById("exTitulo");
  if (titulo) titulo.textContent = T.TITULO_EXPLORAR;

  // --- seletor de vista: Grade | Índice A–Z ---
  var vistas = document.getElementById("exVistas");
  var botoesVista = {};
  [["grade", T.VISTA_GRADE], ["indice", T.VISTA_INDICE]].forEach(function (v) {
    var a = el("a", "ex-vista", v[1]);
    a.dataset.vista = v[0];
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      irPara(estado.filtros, v[0]);
    });
    botoesVista[v[0]] = a;
    vistas.appendChild(a);
  });

  // --- filtros: um <select> por grupo ---
  var form = document.getElementById("exFiltros");
  var selects = {};
  FILTROS.forEach(function (fi) {
    var rotulo = el("label", "ex-filtro");
    rotulo.appendChild(el("span", "ex-filtro__nome", T.ROTULO_GRUPO_EXPLORAR[fi.grupo]));
    var sel = el("select", "ex-filtro__select");
    sel.name = fi.chave;
    var qualquer = el("option", null, T.QUALQUER[fi.chave]);
    qualquer.value = "";
    sel.appendChild(qualquer);
    OPCOES[fi.grupo].forEach(function (o) {
      var op = el("option", null, o.nome + " (" + o.n + ")");
      op.value = String(o.chave);
      sel.appendChild(op);
    });
    sel.addEventListener("change", function () {
      var f = semFiltro(fi.chave);
      if (sel.value) f[fi.chave] = fi.chave === "decada" ? Number(sel.value) : sel.value;
      irPara(f, estado.vista);
    });
    selects[fi.chave] = sel;
    rotulo.appendChild(sel);
    form.appendChild(rotulo);
  });

  var chips = document.getElementById("exChips");
  var contador = document.getElementById("exContador");
  var grade = document.getElementById("exGrade");
  var indice = document.getElementById("exIndice");
  var vazio = document.getElementById("exVazio");
  var mais = document.getElementById("exMais");
  mais.textContent = T.MOSTRAR_MAIS;

  function linkLimpar() {
    var a = el("a", "ex-limpar", T.LIMPAR_FILTROS);
    a.href = "./" + (estado.vista === "indice" ? "?vista=indice" : "");
    a.addEventListener("click", function (ev) { ev.preventDefault(); irPara({}, estado.vista); });
    return a;
  }

  function cartao(f) {
    var li = el("li");
    li.appendChild(C.cartao(f, null, "(max-width: 699px) 100vw, 33vw",
                            T.partesDiretorAno, 0, RAIZ));
    return li;
  }

  var recorte = [];

  function atualizarPaginacao() {
    var n = Math.min(mostrados, recorte.length);
    contador.textContent = T.contadorDaPagina(n, recorte.length);
    mais.hidden = n >= recorte.length;
  }

  function renderGrade() {
    grade.innerHTML = "";
    recorte.slice(0, mostrados).forEach(function (f) { grade.appendChild(cartao(f)); });
    atualizarPaginacao();
  }

  function renderIndice() {
    indice.innerHTML = "";
    X.indiceAZ(recorte).forEach(function (g) {
      var sec = el("section", "ex-indice__grupo");
      sec.appendChild(el("h2", "ex-indice__letra", g.letra));
      var ul = el("ul", "ex-indice__lista");
      g.filmes.forEach(function (f) {
        var li = el("li", "ex-indice__linha");
        li.dataset.slug = f.slug;
        var a = el("a", "ex-indice__titulo", f.titulo);
        a.href = RAIZ + "filme.html?slug=" + encodeURIComponent(f.slug);
        li.appendChild(a);
        var meta = [f.ano ? String(f.ano) : null, f.diretor].filter(Boolean).join(T.SEPARADOR);
        if (meta) li.appendChild(el("span", "ex-indice__meta", meta));
        ul.appendChild(li);
      });
      sec.appendChild(ul);
      indice.appendChild(sec);
    });
    contador.textContent = T.contadorDaPagina(recorte.length, recorte.length);
    mais.hidden = true;
  }

  function render() {
    var f = estado.filtros;
    recorte = X.ordenarPadrao(X.filtrar(FILMES, f));

    FILTROS.forEach(function (fi) {
      var v = f[fi.chave] == null ? "" : String(f[fi.chave]);
      var sel = selects[fi.chave];
      // valor da URL fora das opções: o chip mostra; o select fica em "qualquer"
      sel.value = [].some.call(sel.options, function (o) { return o.value === v; }) ? v : "";
    });

    chips.innerHTML = "";
    var ativos = ["colecao", "decada", "genero", "pais", "desde"].filter(function (k) {
      return f[k] != null;
    });
    ativos.forEach(function (k) {
      var chip = el("span", "ex-chip");
      chip.dataset.filtro = k;
      var nome = nomeDoFiltro(k, f[k]);
      chip.appendChild(el("span", "ex-chip__nome", nome));
      var x = el("button", "ex-chip__remover", "×");
      x.type = "button";
      x.setAttribute("aria-label", T.REMOVER_FILTRO + ": " + nome);
      x.addEventListener("click", function () { irPara(semFiltro(k), estado.vista); });
      chip.appendChild(x);
      chips.appendChild(chip);
    });
    if (ativos.length > 1) chips.appendChild(linkLimpar());
    chips.hidden = !ativos.length;

    Object.keys(botoesVista).forEach(function (v) {
      var b = botoesVista[v];
      b.href = "./" + X.urlDosFiltros(f, v);
      b.setAttribute("aria-current", v === estado.vista ? "true" : "false");
      b.classList.toggle("is-ativa", v === estado.vista);
    });

    vazio.innerHTML = "";
    vazio.hidden = recorte.length > 0;
    if (!recorte.length) {
      vazio.appendChild(el("span", null, T.FILTRO_VAZIO + " "));
      vazio.appendChild(linkLimpar());
    }

    var emIndice = estado.vista === "indice";
    grade.hidden = emIndice || !recorte.length;
    indice.hidden = !emIndice || !recorte.length;
    contador.hidden = !recorte.length;
    if (emIndice) { grade.innerHTML = ""; renderIndice(); }
    else { indice.innerHTML = ""; renderGrade(); }
    if (!recorte.length) mais.hidden = true;
  }

  mais.addEventListener("click", function () {
    var antes = Math.min(mostrados, recorte.length);
    mostrados += X.PAGINA;
    recorte.slice(antes, mostrados).forEach(function (f) { grade.appendChild(cartao(f)); });
    atualizarPaginacao();
  });

  window.addEventListener("popstate", function () {
    estado = X.lerFiltros(location.search);
    mostrados = X.PAGINA;
    render();
  });

  render();
})();
