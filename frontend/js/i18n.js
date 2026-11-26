/* Espectro 24 — i18n.js
   Infraestrutura de idioma (pt/en). Carregado como PRIMEIRO script de cada
   página; expõe `window.I18N` (e `module.exports` sob node).

   Ordem de detecção: ?lang=pt|en (grava a preferência) >
   localStorage["espectro_idioma"] > navigator.languages / language (primeira
   entrada pt* → pt, en* → en) > en (visitante estrangeiro). Sob node (sem
   window/navigator) o idioma é pt, para não mudar a saída dos testes.
   Sem analytics, sem cookies: o localStorage guarda só a preferência. */
(function (root) {
  "use strict";

  var CHAVE = "espectro_idioma";
  var IDIOMAS = ["pt", "en"];

  function lerStorage() {
    try { return root.localStorage ? root.localStorage.getItem(CHAVE) : null; }
    catch (e) { return null; }
  }
  function gravarStorage(v) {
    try { if (root.localStorage) root.localStorage.setItem(CHAVE, v); }
    catch (e) { /* sem armazenamento: a escolha vale só para esta visita */ }
  }
  function valido(v) { return IDIOMAS.indexOf(v) >= 0 ? v : null; }

  function doNavegador() {
    var nav = root.navigator;
    if (!nav) return null;
    var lista = (nav.languages && nav.languages.length) ? nav.languages
      : (nav.language ? [nav.language] : []);
    for (var i = 0; i < lista.length; i++) {
      var l = String(lista[i] || "").toLowerCase();
      if (l.indexOf("pt") === 0) return "pt";
      if (l.indexOf("en") === 0) return "en";
    }
    return null;
  }

  function doParametro() {
    try {
      var s = root.location && root.location.search;
      if (!s) return null;
      var m = /[?&]lang=([^&#]*)/.exec(s);
      return m ? valido(decodeURIComponent(m[1]).toLowerCase()) : null;
    } catch (e) { return null; }
  }

  function detectar() {
    var temAmbiente = !!(root.window || root.document || root.navigator);
    if (!temAmbiente) return "pt";
    var p = doParametro();
    if (p) { gravarStorage(p); return p; }
    var s = valido(lerStorage());
    if (s) return s;
    // sem navigator (harness de testes) não há o que detectar: pt
    if (!root.navigator) return "pt";
    return doNavegador() || "en";
  }

  var idioma = detectar();
  if (root.document && root.document.documentElement) {
    root.document.documentElement.lang = idioma === "pt" ? "pt-BR" : "en";
  }

  var DICT = { pt: {}, en: {} };
  var avisadas = {};

  function registrar(d) {
    IDIOMAS.forEach(function (l) {
      var src = d && d[l];
      if (!src) return;
      Object.keys(src).forEach(function (k) { DICT[l][k] = src[k]; });
    });
  }

  function aviso(chave) {
    if (avisadas[chave]) return;
    avisadas[chave] = true;
    if (typeof console !== "undefined" && console.warn) {
      console.warn("[i18n] chave sem tradução: " + chave);
    }
  }

  function t(chave, vars) {
    var v = DICT[idioma][chave];
    if (v === undefined) v = DICT.pt[chave];
    if (v === undefined) { aviso(chave); return chave; }
    if (typeof v === "function") return v(vars || {});
    return String(v).replace(/\{(\w+)\}/g, function (m, nome) {
      return vars && vars[nome] != null ? vars[nome] : m;
    });
  }

  function aplicar(raiz) {
    var r = raiz || root.document;
    if (!r || !r.querySelectorAll) return;
    [].forEach.call(r.querySelectorAll("[data-i18n]"), function (n) {
      n.textContent = t(n.getAttribute("data-i18n"));
    });
    [].forEach.call(r.querySelectorAll("[data-i18n-html]"), function (n) {
      n.innerHTML = t(n.getAttribute("data-i18n-html"));
    });
    [].forEach.call(r.querySelectorAll("[data-i18n-attr]"), function (n) {
      n.getAttribute("data-i18n-attr").split(";").forEach(function (par) {
        var i = par.indexOf(":");
        if (i < 1) return;
        n.setAttribute(par.slice(0, i).trim(), t(par.slice(i + 1).trim()));
      });
    });
  }

  function definirIdioma(lang) {
    var l = valido(lang);
    if (!l) return;
    gravarStorage(l);
    try {
      // tira ?lang= da URL, senão ele sobrepõe a escolha ao recarregar
      var loc = root.location;
      var tinha = /[?&]lang=/.test(loc.search || "");
      if (!tinha) { loc.reload(); return; }
      var busca = loc.search.replace(/([?&])lang=[^&#]*&?/, "$1").replace(/[?&]$/, "");
      loc.replace(loc.pathname + busca + (loc.hash || ""));
    } catch (e) { /* sem DOM */ }
  }

  function numero(n) {
    return Number(n).toLocaleString(idioma === "pt" ? "pt-BR" : "en-US");
  }

  var api = {
    get idioma() { return idioma; },
    registrar: registrar, t: t, aplicar: aplicar,
    definirIdioma: definirIdioma, numero: numero,
    // só para testes
    _detectar: detectar, _dict: DICT,
  };

  if (root.document && root.document.addEventListener) {
    if (root.document.readyState === "loading") {
      root.document.addEventListener("DOMContentLoaded", function () { aplicar(); });
    } else { aplicar(); }
  }

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.I18N = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
