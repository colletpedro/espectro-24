/* Espectro 24 — cabecalho.js  [rodada Explorar]
   O CABEÇALHO comum da home e de /filmes: a barra espectral, o nome, os
   links Filmes e Método e a BUSCA (busca.js sobre o índice, com a lista de
   resultados por teclado). Saiu de inicio.js sem mudança de comportamento,
   para /filmes ter o mesmo cabeçalho.

   `<body data-raiz="../">` diz onde fica a raiz do site a partir da página
   (vazio na home, "../" em /filmes) — os links da busca dependem disso. */
(function () {
  "use strict";

  var IDX = window.ESPECTRO_INDICE || { filmes: [] };
  var B = window.ESPECTRO_BUSCA;
  var T = window.ESPECTRO_TEXTOS;
  var I = window.I18N;
  var FILMES = IDX.filmes || [];
  var RAIZ = (document.body && document.body.dataset.raiz) || "";

  function el(tag, classe, texto) {
    var n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texto != null) n.textContent = texto;
    return n;
  }

  function hrefFilme(slug) { return RAIZ + "filme.html?slug=" + encodeURIComponent(slug); }
  var HREF_CATALOGO = RAIZ + "filmes/";

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

  // --- [i18n] textos do cabeçalho compartilhado e o seletor de idioma ---
  I.registrar({
    pt: {
      "cabecalho.buscar_filme": "Buscar filme",
      "cabecalho.resultados": "Resultados da busca",
      "cabecalho.secoes": "Seções",
      "cabecalho.idioma": "Idioma",
      "cabecalho.idioma_pt": "Português",
      "cabecalho.idioma_en": "English (inglês)",
    },
    en: {
      "cabecalho.buscar_filme": "Search films",
      "cabecalho.resultados": "Search results",
      "cabecalho.secoes": "Sections",
      "cabecalho.idioma": "Language",
      "cabecalho.idioma_pt": "Português (Portuguese)",
      "cabecalho.idioma_en": "English",
    },
  });

  (function traduzirCabecalho() {
    var rotulo = document.querySelector('label[for="busca"]');
    if (rotulo) rotulo.textContent = I.t("cabecalho.buscar_filme");
    var res = document.getElementById("buscaResultados");
    if (res) res.setAttribute("aria-label", I.t("cabecalho.resultados"));
    var nav = document.querySelector(".ed-cabecalho__nav");
    if (nav) nav.setAttribute("aria-label", I.t("cabecalho.secoes"));
  })();

  // Seletor "PT · EN": dois botões reais num grupo; o idioma atual fica
  // marcado (aria-pressed + destaque visual) e o outro troca e recarrega.
  (function ligarIdioma() {
    var linha = document.querySelector(".ed-cabecalho__linha");
    if (!linha || linha.querySelector(".idioma")) return;
    var grupo = el("div", "idioma");
    grupo.setAttribute("role", "group");
    grupo.setAttribute("aria-label", I.t("cabecalho.idioma"));
    [["pt", "PT", "cabecalho.idioma_pt"], ["en", "EN", "cabecalho.idioma_en"]]
      .forEach(function (d, i) {
        if (i) {
          var sep = el("span", "idioma__sep", "·");
          sep.setAttribute("aria-hidden", "true");
          grupo.appendChild(sep);
        }
        var b = el("button", "idioma__botao", d[1]);
        b.type = "button";
        b.lang = d[0] === "pt" ? "pt-BR" : "en";
        b.setAttribute("aria-label", I.t(d[2]));
        var atual = I.idioma === d[0];
        b.setAttribute("aria-pressed", atual ? "true" : "false");
        if (atual) b.classList.add("is-ativo");
        b.addEventListener("click", function () {
          if (!atual) I.definirIdioma(d[0]);
        });
        grupo.appendChild(b);
      });
    linha.appendChild(grupo);
  })();

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

})();
