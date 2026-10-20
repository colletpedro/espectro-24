/* Espectro 24 — busca.js
   O MOTOR DE BUSCA da home: consulta → lista de resultados. Sem DOM.

   A INTERFACE É O CONTRATO, não a implementação. A UI (`inicio.js`) só
   conhece isto:

       var motor = ESPECTRO_BUSCA.criar(filmesDoIndice);
       motor.buscar("cidade")  →  [{ slug, titulo, titulo_letterboxd, ano }, ...]

   Uma "busca profunda" futura (por sentimento, por eixo) troca o que
   `criar` devolve, desde que `buscar(q)` continue devolvendo essa lista na
   ordem de exibição — a UI não muda.

   O QUE ESTA VERSÃO PROCURA: o título exibido (pt-BR, da ficha TMDB; em
   alfabeto latino — ver `titulos_de_exibicao` em build_indice.py), o
   título nativo quando ele foi trocado na exibição ("화녀"), o título
   canônico do Letterboxd quando a ficha o tem, o slug como chave oculta
   (33 filmes não têm o título do Letterboxd persistido) e o ANO.

   ORDEM: (0) prefixo de algum título; (1) substring de algum título; (2) o
   ano, quando a consulta é exatamente um ano. Desempate alfabético pelo
   título exibido normalizado, depois pelo slug. NENHUM critério de
   popularidade ou de distribuição de grupos entra na conta — o índice nem
   é consultado por esses campos aqui.

   Funções puras, exportadas também para `node` (ver `tests/test_home_nova.py`). */
(function (root) {
  "use strict";

  // Artigos iniciais ignorados — no título e na consulta, dos dois lados,
  // para que "poderoso chefao" ache "O Poderoso Chefão" como PREFIXO.
  var ARTIGOS = ["o", "a", "os", "as", "the"];

  var LIMITE_RESULTADOS = 10;

  /* Normalização: caixa, diacríticos (NFD + remoção das marcas
     combinantes), pontuação vira espaço, espaços colapsados, e o artigo
     inicial sai — só se houver mais alguma palavra depois dele ("A Cura"
     vira "cura", mas a consulta "a" continua "a"). */
  function normalizar(s) {
    var t = String(s == null ? "" : s).toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .trim().replace(/\s+/g, " ");
    var partes = t.split(" ");
    if (partes.length > 1 && ARTIGOS.indexOf(partes[0]) !== -1) {
      t = partes.slice(1).join(" ");
    }
    return t;
  }

  // Comparação por unidade de código, não `localeCompare`: o resultado não
  // pode depender da localidade do navegador de quem visita.
  function comparar(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

  function chaveDeOrdem(filme) { return normalizar(filme.titulo); }

  function ordenarAlfabetico(filmes) {
    return filmes.slice().sort(function (x, y) {
      return comparar(chaveDeOrdem(x), chaveDeOrdem(y)) || comparar(x.slug, y.slug);
    });
  }

  function chavesDeTitulo(f) {
    var ks = [f.titulo, f.titulo_nativo, f.titulo_letterboxd, f.chave_slug]
      .filter(Boolean).map(normalizar).filter(Boolean);
    // "titulo ano" também é chave: "coringa 2019" casa como PREFIXO.
    if (f.ano) {
      ks = ks.concat(ks.map(function (k) { return k + " " + f.ano; }));
    }
    return ks.filter(function (k, i) { return ks.indexOf(k) === i; });
  }

  // 0 = prefixo, 1 = substring, 2 = ano exato, -1 = não casa.
  function nivelDeCasamento(chaves, ano, q) {
    var melhor = -1;
    for (var i = 0; i < chaves.length; i++) {
      var k = chaves[i];
      if (k.indexOf(q) === 0) return 0;
      if (k.indexOf(q) !== -1) melhor = 1;
    }
    if (melhor === -1 && ano && /^\d{4}$/.test(q) && String(ano) === q) melhor = 2;
    return melhor;
  }

  function criar(filmes, opcoes) {
    opcoes = opcoes || {};
    var limite = opcoes.limite || LIMITE_RESULTADOS;
    var entradas = (filmes || []).map(function (f) {
      return { filme: f, chaves: chavesDeTitulo(f), ordem: chaveDeOrdem(f) };
    });

    function buscar(consulta) {
      var q = normalizar(consulta);
      if (!q) return [];
      var achados = [];
      entradas.forEach(function (e) {
        var nivel = nivelDeCasamento(e.chaves, e.filme.ano, q);
        if (nivel >= 0) achados.push({ nivel: nivel, e: e });
      });
      achados.sort(function (x, y) {
        return (x.nivel - y.nivel) || comparar(x.e.ordem, y.e.ordem)
          || comparar(x.e.filme.slug, y.e.filme.slug);
      });
      return achados.slice(0, limite).map(function (a) {
        var f = a.e.filme;
        return {
          slug: f.slug, titulo: f.titulo, titulo_nativo: f.titulo_nativo || null,
          titulo_letterboxd: f.titulo_letterboxd || null, ano: f.ano || null,
        };
      });
    }

    return { buscar: buscar };
  }

  var api = {
    chavesDeTitulo: chavesDeTitulo,
    ARTIGOS: ARTIGOS, LIMITE_RESULTADOS: LIMITE_RESULTADOS,
    normalizar: normalizar, comparar: comparar,
    ordenarAlfabetico: ordenarAlfabetico, criar: criar,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_BUSCA = api;
})(this);
