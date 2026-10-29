/* Espectro 24 — cor.js  [rodada cor]
   `?cor=` escolhe a paleta dos três grupos (HATERS, MIXED, FANS) em TODO o
   site — faixa da home, cartões, RECEPÇÃO, bullets e condições leem os
   mesmos tokens `--grupo-neg/med/pos` (styles.css):

     atual       as cores fortes da página do filme
     apagada     as da faixa da home até a rodada da cor
     editorial   paleta dessaturada (saturação HSL <= 45%), medida em
                 scripts/medir_cores.py

   Roda no <head>, antes de pintar: marca `<html data-cor="...">`. Valor
   desconhecido vale o padrão. Combina com `?fonte=` e `?topo=`.

   TORNAR UMA PADRÃO é trocar uma linha: `COR_PADRAO` abaixo. */
(function () {
  "use strict";

  var COR_PADRAO = "atual";

  var CORES = ["atual", "apagada", "editorial"];

  var pedida = new URLSearchParams(location.search).get("cor");
  var cor = CORES.indexOf(pedida) >= 0 ? pedida : COR_PADRAO;
  document.documentElement.setAttribute("data-cor", cor);

  window.ESPECTRO_COR = { COR_PADRAO: COR_PADRAO, CORES: CORES, cor: cor };
})();
