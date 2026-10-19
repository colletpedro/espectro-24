/* Espectro 24 — inicio.js
   A APRESENTAÇÃO da home nova. Só monta DOM e liga eventos: o que mostrar
   vem de `selecao.js` (filme do dia, prateleiras, recém-chegados), a busca
   vem de `busca.js` (consulta → resultados) e toda a prosa vem de
   `textos_home.js`. A rodada de identidade visual troca este arquivo e o
   CSS sem tocar nos outros três.

   Lê só `window.ESPECTRO_INDICE` (`js/indice.js`, ~70 KB), nunca o
   `data.js` de 5,6 MB — que continua sendo o dado de /filmes e da página
   do filme.

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

  // --- 1. premissa ---
  var premissa = document.getElementById("homePremissa");
  if (premissa) premissa.textContent = T.PREMISSA;

  // --- 2. busca ---
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

  // --- célula de filme: a MESMA do mosaico de /filmes (pôster, título, ano
  // e a faixa fina dos três grupos, no estado final, sem animação) ---
  var GRUPOS = ["negativas", "medianas", "positivas"];
  var COR_GRUPO_HOME = {
    negativas: "var(--neg-home)", medianas: "var(--med-home)", positivas: "var(--pos-home)",
  };

  function celula(f) {
    var a = el("a", "mosaic-cell");
    a.href = hrefFilme(f.slug);
    a.setAttribute("aria-label", f.titulo + (f.ano ? " (" + f.ano + ")" : "") + " — ver análise");
    if (P) {
      a.appendChild(P.montar(f.imagens, { uso: "mosaico", titulo: f.titulo, ano: f.ano, lazy: true }));
    }
    var body = el("span", "mosaic-cell__body");
    body.appendChild(el("span", "mosaic-cell__title", f.titulo));
    if (f.ano) body.appendChild(el("span", "mosaic-cell__year", String(f.ano)));
    var strip = el("span", "mosaic-cell__strip");
    strip.setAttribute("aria-hidden", "true");
    var d = f.distribuicao;
    var total = d ? GRUPOS.reduce(function (s, g) { return s + (d[g] || 0); }, 0) : 0;
    if (total) {
      GRUPOS.forEach(function (g) {
        if (!(d[g] > 0)) return;
        var seg = el("span", "mosaic-cell__seg");
        seg.style.background = COR_GRUPO_HOME[g];
        seg.style.width = (d[g] / total) * 100 + "%";
        strip.appendChild(seg);
      });
    } else {
      strip.style.background = "var(--border)";
    }
    a.appendChild(body);
    a.appendChild(strip);
    return a;
  }

  // --- 3. filme do dia ---
  (function filmeDoDia() {
    var caixa = document.getElementById("filmeDoDia");
    var f = S.filmeDoDia(FILMES, DIA);
    if (!caixa || !f) { if (caixa) caixa.hidden = true; return; }
    var j = T.justificar(f);
    caixa.dataset.slug = f.slug;
    caixa.dataset.gancho = j.gancho;

    caixa.appendChild(el("p", "section-label", T.ROTULO_FILME_DO_DIA));
    var visual = el("a", "filme-do-dia__visual");
    visual.href = hrefFilme(f.slug);
    visual.tabIndex = -1;
    visual.setAttribute("aria-hidden", "true");
    var img = P && (P.montarBackdrop(f.imagens, { titulo: f.titulo, ano: f.ano })
      || P.montar(f.imagens, { uso: "ficha", titulo: f.titulo, ano: f.ano }));
    if (img) visual.appendChild(img);
    caixa.appendChild(visual);

    var h = el("h2", "filme-do-dia__titulo");
    h.id = "filmeDoDiaTitulo";
    var link = el("a", null, f.titulo);
    link.href = hrefFilme(f.slug);
    h.appendChild(link);
    caixa.appendChild(h);
    if (f.ano) caixa.appendChild(el("p", "filme-do-dia__ano mono", String(f.ano)));
    caixa.appendChild(el("p", "filme-do-dia__texto", j.texto));
    var abrir = el("a", "filme-do-dia__abrir mono", T.ROTULO_ABRIR + " →");
    abrir.href = hrefFilme(f.slug);
    caixa.appendChild(abrir);
  })();

  // --- prateleira: rolagem horizontal NATIVA (touch e trackpad de graça),
  // foco por teclado na trilha (setas) e botões para quem usa mouse ---
  var reduzMovimento = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function prateleira(id, titulo, filmes, nota) {
    var sec = el("section", "prateleira");
    sec.dataset.chave = id;
    var cab = el("div", "prateleira__cabeca");
    var h = el("h2", "section-label prateleira__titulo", titulo);
    h.id = "prat-" + id;
    cab.appendChild(h);
    var nav = el("div", "prateleira__nav");
    var trilha = el("ul", "prateleira__trilha");
    trilha.tabIndex = 0;
    trilha.setAttribute("aria-labelledby", h.id);
    [["‹", -1, "Rolar para a esquerda"], ["›", 1, "Rolar para a direita"]].forEach(function (b) {
      var btn = el("button", "prateleira__botao", b[0]);
      btn.type = "button";
      btn.setAttribute("aria-label", b[2] + ": " + titulo);
      btn.addEventListener("click", function () {
        trilha.scrollBy({ left: b[1] * trilha.clientWidth * 0.85,
                          behavior: reduzMovimento ? "auto" : "smooth" });
      });
      nav.appendChild(btn);
    });
    cab.appendChild(nav);
    sec.appendChild(cab);
    if (nota) sec.appendChild(el("p", "prateleira__nota mono", nota));
    filmes.forEach(function (f) {
      var li = el("li", "prateleira__item");
      li.appendChild(celula(f));
      trilha.appendChild(li);
    });
    sec.appendChild(trilha);

    function atualizarBotoes() {
      var max = trilha.scrollWidth - trilha.clientWidth;
      nav.children[0].disabled = trilha.scrollLeft <= 1;
      nav.children[1].disabled = trilha.scrollLeft >= max - 1;
      nav.hidden = max <= 1;
    }
    trilha.addEventListener("scroll", atualizarBotoes, { passive: true });
    // Medir só depois de a seção estar no DOM (`montarPrateleira`). Vários
    // gatilhos de propósito, como em `faixa.js`: no navegador embutido usado
    // para conferir, nem o rAF nem o ResizeObserver dispararam sempre.
    atualizaveis.push(atualizarBotoes);
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(atualizarBotoes).observe(trilha);
    }
    return sec;
  }

  var atualizaveis = [];
  function atualizarTodas() { atualizaveis.forEach(function (fn) { fn(); }); }
  window.addEventListener("resize", atualizarTodas);
  window.addEventListener("load", atualizarTodas);

  // --- 4. prateleiras ---
  var areaPrat = document.getElementById("prateleiras");
  if (areaPrat) {
    S.prateleiras(FILMES, DIA).forEach(function (p) {
      areaPrat.appendChild(prateleira(p.chave, T.tituloDaPrateleira(p.chave), p.filmes));
    });
  }

  // --- 5. recém-chegados (a data vem do registro de entrada no catálogo) ---
  var areaRecem = document.getElementById("recemChegados");
  if (areaRecem) {
    var r = S.recemChegados(FILMES);
    if (r) {
      var fmt = function (d) { var p = d.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; };
      var nota = r.desde === r.ate ? "entraram no catálogo em " + fmt(r.ate)
        : "entraram no catálogo entre " + fmt(r.desde) + " e " + fmt(r.ate);
      areaRecem.appendChild(prateleira("recem", T.ROTULO_RECEM, r.filmes, nota));
    } else {
      areaRecem.hidden = true;
    }
  }

  atualizarTodas();

  // --- 6. aviso fixo ---
  var aviso = document.getElementById("homeAviso");
  if (aviso) {
    aviso.appendChild(el("span", null, T.AVISO_CATALOGO + " "));
    var a = el("a", null, T.AVISO_LINK + " →");
    a.href = HREF_CATALOGO;
    aviso.appendChild(a);
  }
})();
