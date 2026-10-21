/* Espectro 24 — explorar.js  [rodada Explorar]
   As PORTAS DE ENTRADA do catálogo: o bloco "Explorar" da home e os
   filtros de /filmes. Funções puras sobre o índice (`js/indice.js`), sem
   DOM — como selecao.js, executadas sob node pelos testes.

   NENHUMA contagem, filtro ou ordenação aqui lê a distribuição dos grupos
   (`distribuicao`).

   GRUPOS DO EXPLORAR (`gruposDoExplorar`):
   · assunto — as coleções (selecao.js: `ordemDasColecoes`, a ordem fixa já
     usada na home; piso de 3 elegíveis e lista de exclusão de lá);
   · década  — `floor(ano / 10) * 10`, cronológica;
   · gênero  — os gêneros da ficha (`generos`, pt-BR como vêm do TMDB),
     por contagem decrescente, desempate alfabético (normalizado);
   · país    — TODOS os países de cada filme (`paises`, ISO 3166-1), por
     contagem decrescente, desempate alfabético pelo nome em pt-BR.
   Pisos e universo são parâmetros: a home conta só os ELEGÍVEIS (fora a
   lista de exclusão da vitrine) com piso 3 em gênero e país e 1 em
   década; /filmes oferece nos filtros tudo o que existe (piso 1) no
   catálogo inteiro.

   FILTROS (`filtrar`): colecao, decada, genero, pais e desde, combinados
   em AND. Valor que não corresponde a nada (coleção, gênero ou país
   desconhecido) dá recorte VAZIO — a página diz isso e oferece limpar.
   Todos vivem na URL (`lerFiltros` / `urlDosFiltros`, ida e volta), com a
   vista (`vista=indice`); a página da paginação não vai para a URL.

   ORDEM PADRÃO (`ordenarPadrao`): entrada no catálogo, mais recentes
   primeiro; desempate alfabético pelo título exibido normalizado (artigos
   iniciais ignorados, como na busca); por fim o slug.

   ÍNDICE A–Z (`indiceAZ`): o recorte inteiro em ordem alfabética,
   agrupado pela primeira letra do título exibido NORMALIZADO (sem acento,
   artigo inicial ignorado); título que começa com algarismo vai para
   "0–9", no início. */
(function (root) {
  "use strict";

  var emNode = typeof module !== "undefined" && module.exports;
  var B = emNode ? require("./busca.js") : root.ESPECTRO_BUSCA;
  var S = emNode ? require("./selecao.js") : root.ESPECTRO_SELECAO;
  var T = emNode ? require("./textos_home.js") : root.ESPECTRO_TEXTOS;

  var PISO_HOME = 3;          // gênero e país no bloco da home
  var PAGINA = 24;            // /filmes mostra 24 por vez
  var GRUPO_ALGARISMO = "0–9";
  var DATA_RE = /^\d{4}-\d{2}-\d{2}$/;

  function decadaDe(f) {
    return typeof f.ano === "number" ? Math.floor(f.ano / 10) * 10 : null;
  }

  // "Anos 60" até 1990; "Anos 2000" em diante (como se fala).
  function rotuloDaDecada(d) {
    return "Anos " + (d < 2000 ? String(d % 100).padStart(2, "0") : String(d));
  }

  // A chave de URL de um gênero: o nome normalizado, espaços em hífen
  // ("Ficção científica" → "ficcao-cientifica").
  function chaveDoGenero(nome) {
    return B.normalizar(nome).replace(/ /g, "-");
  }

  function contar(lista, valoresDe) {
    var n = {};
    lista.forEach(function (f) {
      // um filme conta UMA vez por valor, mesmo se repetido na ficha
      valoresDe(f).filter(function (v, i, a) { return a.indexOf(v) === i; })
        .forEach(function (v) { n[v] = (n[v] || 0) + 1; });
    });
    return n;
  }

  function porContagem(itens) {
    return itens.sort(function (a, b) {
      return (b.n - a.n) || B.comparar(B.normalizar(a.nome), B.normalizar(b.nome))
        || B.comparar(String(a.chave), String(b.chave));
    });
  }

  // → {assunto, decada, genero, pais}, cada um uma lista de
  //   {chave, nome, n}. `opcoes`: {elegiveis: bool, piso: n (gênero e país)}.
  function gruposDoExplorar(filmes, opcoes) {
    opcoes = opcoes || {};
    var lista = opcoes.elegiveis ? S.elegiveis(filmes) : (filmes || []).slice();
    var piso = opcoes.piso == null ? PISO_HOME : opcoes.piso;

    var assunto = S.ordemDasColecoes(filmes).map(function (c) {
      return { chave: c.chave, nome: T.tituloDaPrateleira(c.chave), n: c.filmes.length };
    });

    var nd = contar(lista, function (f) { var d = decadaDe(f); return d == null ? [] : [d]; });
    var decada = Object.keys(nd).map(Number).sort(function (a, b) { return a - b; })
      .map(function (d) { return { chave: d, nome: rotuloDaDecada(d), n: nd[d] }; });

    var nomeDoGenero = {};
    var ng = contar(lista, function (f) {
      return (f.generos || []).map(function (g) {
        var k = chaveDoGenero(g);
        if (!nomeDoGenero[k]) nomeDoGenero[k] = g;
        return k;
      });
    });
    var genero = porContagem(Object.keys(ng).filter(function (k) { return ng[k] >= piso; })
      .map(function (k) { return { chave: k, nome: nomeDoGenero[k], n: ng[k] }; }));

    var np = contar(lista, function (f) { return f.paises || []; });
    var pais = porContagem(Object.keys(np).filter(function (k) { return np[k] >= piso; })
      .map(function (k) { return { chave: k, nome: T.nomeDoPais(k), n: np[k] }; }));

    return { assunto: assunto, decada: decada, genero: genero, pais: pais };
  }

  // ------------------------------------------------------------------
  // URL ⇄ filtros
  // ------------------------------------------------------------------
  var CHAVES_URL = ["colecao", "decada", "genero", "pais", "desde"];

  function lerFiltros(busca) {
    var p = new URLSearchParams(busca || "");
    var f = {};
    var colecao = p.get("colecao");
    if (colecao) f.colecao = colecao;
    var decada = p.get("decada");
    if (/^\d{4}$/.test(decada || "")) f.decada = Number(decada);
    var genero = p.get("genero");
    if (genero) f.genero = genero;
    var pais = p.get("pais");
    if (/^[A-Za-z]{2}$/.test(pais || "")) f.pais = pais.toUpperCase();
    var desde = p.get("desde");
    if (DATA_RE.test(desde || "")) f.desde = desde;
    return { filtros: f, vista: p.get("vista") === "indice" ? "indice" : "grade" };
  }

  function urlDosFiltros(filtros, vista) {
    var p = [];
    CHAVES_URL.forEach(function (k) {
      if (filtros && filtros[k] != null && filtros[k] !== "") {
        p.push(k + "=" + encodeURIComponent(String(filtros[k])));
      }
    });
    if (vista === "indice") p.push("vista=indice");
    return p.length ? "?" + p.join("&") : "";
  }

  // ------------------------------------------------------------------
  // filtro, ordem, índice
  // ------------------------------------------------------------------
  function filtrar(filmes, filtros) {
    filtros = filtros || {};
    var membros = null;
    if (filtros.colecao) {
      var c = S.prateleirasBase(filmes).filter(function (x) { return x.chave === filtros.colecao; })[0];
      membros = {};
      (c ? c.filmes : []).forEach(function (f) { membros[f.slug] = true; });
    }
    return (filmes || []).filter(function (f) {
      if (membros && !membros[f.slug]) return false;
      if (filtros.decada != null && decadaDe(f) !== filtros.decada) return false;
      if (filtros.genero && !(f.generos || []).some(function (g) {
        return chaveDoGenero(g) === filtros.genero;
      })) return false;
      if (filtros.pais && (f.paises || []).indexOf(filtros.pais) === -1) return false;
      if (filtros.desde && !(f.entrada && f.entrada >= filtros.desde)) return false;
      return true;
    });
  }

  function ordenarPadrao(filmes) {
    return (filmes || []).slice().sort(function (x, y) {
      var ex = x.entrada || "", ey = y.entrada || "";
      return B.comparar(ey, ex)
        || B.comparar(B.normalizar(x.titulo), B.normalizar(y.titulo))
        || B.comparar(x.slug, y.slug);
    });
  }

  function letraDe(f) {
    var c = B.normalizar(f.titulo || f.slug).charAt(0).toUpperCase();
    return /[0-9]/.test(c) ? GRUPO_ALGARISMO : c;
  }

  // → [{letra, filmes}], letras em ordem, "0–9" primeiro.
  function indiceAZ(filmes) {
    var grupos = {};
    B.ordenarAlfabetico(filmes || []).forEach(function (f) {
      var l = letraDe(f);
      (grupos[l] = grupos[l] || []).push(f);
    });
    return Object.keys(grupos).sort(function (a, b) {
      if (a === GRUPO_ALGARISMO) return -1;
      if (b === GRUPO_ALGARISMO) return 1;
      return B.comparar(a, b);
    }).map(function (l) { return { letra: l, filmes: grupos[l] }; });
  }

  var api = {
    PISO_HOME: PISO_HOME, PAGINA: PAGINA, GRUPO_ALGARISMO: GRUPO_ALGARISMO,
    decadaDe: decadaDe, rotuloDaDecada: rotuloDaDecada, chaveDoGenero: chaveDoGenero,
    gruposDoExplorar: gruposDoExplorar, lerFiltros: lerFiltros,
    urlDosFiltros: urlDosFiltros, filtrar: filtrar, ordenarPadrao: ordenarPadrao,
    letraDe: letraDe, indiceAZ: indiceAZ,
  };

  if (emNode) module.exports = api;
  else root.ESPECTRO_EXPLORAR = api;
})(this);
