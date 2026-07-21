/* Espectro 24 — home.js
   Monta os cards do catálogo a partir de window.ESPECTRO_DATA e liga o
   comportamento da busca estética (mensagem suave, sem lógica de filtro). */
(function () {
  "use strict";

  var DATA = window.ESPECTRO_DATA || { catalogo: [], filmes: {} };

  // --- barra espectral segmentada (marca) ---
  var brand = document.getElementById("brandBar");
  if (brand) {
    var stops = ["#e5484d", "#f5820b", "#f5a623", "#f5c518", "#8bbf3f", "#46a758", "#2e9c8e", "#3b82f6"];
    stops.forEach(function (c) {
      var s = document.createElement("span");
      s.style.background = c;
      brand.appendChild(s);
    });
  }

  // --- cards do catálogo ---
  var cards = document.getElementById("filmCards");
  DATA.catalogo.forEach(function (slug) {
    var f = DATA.filmes[slug];
    if (!f) return;
    var titulo = (f.ficha && f.ficha.titulo) || slug;
    var ano = (f.ficha && f.ficha.ano) || "";

    var a = document.createElement("a");
    a.className = "film-card";
    a.href = "filme.html?slug=" + encodeURIComponent(slug);
    a.setAttribute("aria-label", titulo + (ano ? " (" + ano + ")" : "") + " — ver análise");

    var body = document.createElement("div");
    body.className = "film-card__body";

    var h = document.createElement("h3");
    h.className = "film-card__title";
    h.textContent = titulo;

    var meta = document.createElement("p");
    meta.className = "film-card__meta";
    var anoTxt = ano ? String(ano) : "—";
    meta.innerHTML =
      esc(anoTxt) +
      '<span class="dot">·</span>' +
      fmt(f.total_reviews_observadas) + " reviews observadas";

    body.appendChild(h);
    body.appendChild(meta);

    var arrow = document.createElement("span");
    arrow.className = "film-card__arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.innerHTML =
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

    a.appendChild(body);
    a.appendChild(arrow);
    cards.appendChild(a);
  });

  // --- busca estética: nunca parece quebrada ---
  var input = document.getElementById("search");
  var hint = document.getElementById("searchHint");
  var MSG = "Busca em breve — 3 análises disponíveis abaixo";
  function showHint() {
    hint.textContent = MSG;
    hint.classList.add("is-visible");
  }
  function maybeHide() {
    if (!input.value) {
      hint.classList.remove("is-visible");
    }
  }
  input.addEventListener("focus", showHint);
  input.addEventListener("input", showHint);
  input.addEventListener("blur", maybeHide);

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("pt-BR") : "—";
  }
})();
