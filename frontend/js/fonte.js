/* Espectro 24 — fonte.js  [rodada editorial 2: prova de fontes]
   `?fonte=` troca a família tipográfica da home (títulos de coleção,
   títulos em texto, metadados e rótulos de seção):

     atual        as famílias de sistema de sempre (zero rede)
     inter-tight  Inter Tight (Google Fonts)
     instrument   Instrument Sans (Google Fonts) — PADRÃO desde a rodada
                  da fonte; vale na home e em /filmes

   Roda no <head>, antes de pintar: marca `<html data-fonte="...">` — o CSS
   põe a família numa variável ÚNICA (`--ed-fonte`) e aplica o tratamento
   das novas (caixa alta, peso 500–600, espaçamento normal, metadado MUBI) —
   e carrega SÓ a família pedida. Valor desconhecido vale o padrão.

   TORNAR UMA PADRÃO é trocar uma linha: `FONTE_PADRAO` abaixo. */
(function () {
  "use strict";

  var FONTE_PADRAO = "instrument";

  var GOOGLE = "https://fonts.googleapis.com/css2?family=";
  var FONTES = {
    atual: null,
    "inter-tight": "Inter+Tight:wght@400;500;600;700",
    instrument: "Instrument+Sans:wght@400;500;600;700",
  };

  var pedida = new URLSearchParams(location.search).get("fonte");
  var fonte = Object.prototype.hasOwnProperty.call(FONTES, pedida) ? pedida : FONTE_PADRAO;
  document.documentElement.setAttribute("data-fonte", fonte);

  if (FONTES[fonte]) {
    var pre = document.createElement("link");
    pre.rel = "preconnect";
    pre.href = "https://fonts.gstatic.com";
    pre.crossOrigin = "";
    document.head.appendChild(pre);
    var css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = GOOGLE + FONTES[fonte] + "&display=swap";
    document.head.appendChild(css);
  }

  window.ESPECTRO_FONTE = { FONTE_PADRAO: FONTE_PADRAO, FONTES: FONTES, fonte: fonte };
})();
