/* Espectro 24 — semanal.js
   Os blocos SEMANAIS da home (seleção da década e as duas fileiras de
   gênero) e a MONTAGEM da home inteira sem filme repetido. Funções puras
   sobre o índice, sem DOM e sem relógio — como selecao.js, rodam sob node
   nos testes (`tests/test_home_semanal.py`).

   NENHUMA escolha aqui lê a distribuição dos grupos (`distribuicao`).

   ORDEM E NÃO REPETIÇÃO (`homeDoDia`): manchete → coleção do dia →
   recém-chegados → década → gênero 1 → gênero 2. Cada bloco pula os filmes
   já usados acima. Se o bloco não alcança o mínimo, tenta o próximo
   candidato da rotação; se nenhum serve, o bloco não aparece.

   SEMANA: `S.semanaDe(dia)`, de segunda a domingo em America/Sao_Paulo.

   DÉCADA (`selecaoDaDecada`): candidatas são as décadas ANTERIORES a 2000
   com >= PISO_DECADA (3) elegíveis, em ordem cronológica; a da semana w é
   a de posição (w mod N). 3 filmes (LIMITE_DECADA).

   GÊNEROS (`fileirasDeGenero`): candidatos são os gêneros da ficha com >=
   PISO_GENERO_CANDIDATO (6) elegíveis, numa ordem FIXA embaralhada por
   hash (semente própria) — não por contagem, para a fileira não começar
   sempre pelos maiores. Na semana w entram as posições (2w) e (2w + 1)
   mod N: distintas (N >= 2) e, ao longo de N semanas, a lista inteira
   passa antes de qualquer gênero repetir. 4 filmes (LIMITE_GENERO) por
   fileira, mínimo 4.

   FILMES DENTRO DA DÉCADA OU DO GÊNERO: a lista é alfabética (título
   normalizado) e GIRA k posições por semana (início = (w * k) mod n); a
   semana toma os primeiros k da lista girada que ainda não apareceram na
   página. Sem colisão, a seleção é a mesma de segunda a domingo; a
   colisão com a manchete ou a coleção do dia (que mudam todo dia) troca
   só o filme que colidiu pelo seguinte da lista girada. Os escolhidos são
   mostrados em ordem alfabética. */
(function (root) {
  "use strict";

  var emNode = typeof module !== "undefined" && module.exports;
  var B = emNode ? require("./busca.js") : root.ESPECTRO_BUSCA;
  var S = emNode ? require("./selecao.js") : root.ESPECTRO_SELECAO;
  var X = emNode ? require("./explorar.js") : root.ESPECTRO_EXPLORAR;

  var SEMENTE_GENERO = "espectro24/genero-da-semana/v1";
  var PISO_DECADA = 3;
  var LIMITE_DECADA = 3;
  var PISO_GENERO_CANDIDATO = 6;
  var LIMITE_GENERO = 4;
  var DECADA_MAXIMA = 2000;    // só décadas ANTERIORES a esta

  function agrupar(lista, chavesDe) {
    var m = {};
    lista.forEach(function (f) {
      chavesDe(f).filter(function (v, i, a) { return a.indexOf(v) === i; })
        .forEach(function (k) { (m[k] = m[k] || []).push(f); });
    });
    return m;
  }

  // → [{decada, filmes}] cronológico; filmes em ordem alfabética.
  function decadasCandidatas(filmes) {
    var m = agrupar(S.elegiveis(filmes), function (f) {
      var d = X.decadaDe(f);
      return d == null || d >= DECADA_MAXIMA ? [] : [d];
    });
    return Object.keys(m).map(Number).sort(function (a, b) { return a - b; })
      .filter(function (d) { return m[d].length >= PISO_DECADA; })
      .map(function (d) { return { decada: d, filmes: B.ordenarAlfabetico(m[d]) }; });
  }

  // → [{chave, nome, filmes}] na ordem fixa por hash; filmes alfabéticos.
  function generosCandidatos(filmes) {
    var nomes = {};
    var m = agrupar(S.elegiveis(filmes), function (f) {
      return (f.generos || []).map(function (g) {
        var k = X.chaveDoGenero(g);
        if (!nomes[k]) nomes[k] = g;
        return k;
      });
    });
    return Object.keys(m).filter(function (k) { return m[k].length >= PISO_GENERO_CANDIDATO; })
      .map(function (k) {
        return { chave: k, nome: nomes[k], filmes: B.ordenarAlfabetico(m[k]),
                 h: S.fnv1a(SEMENTE_GENERO + "|" + k) };
      })
      .sort(function (a, b) { return (a.h - b.h) || B.comparar(a.chave, b.chave); })
      .map(function (c) { return { chave: c.chave, nome: c.nome, filmes: c.filmes }; });
  }

  // Os `k` primeiros da lista girada em (semana * k) que ainda não estão em
  // `usados`; em ordem alfabética. null se não houver `k`.
  function girar(lista, semana, k, usados) {
    var n = lista.length;
    var ini = S.modulo(semana * k, n);
    var idx = [];
    for (var j = 0; j < n && idx.length < k; j++) {
      var i = (ini + j) % n;
      if (!usados[lista[i].slug]) idx.push(i);
    }
    if (idx.length < k) return null;
    return idx.sort(function (a, b) { return a - b; }).map(function (i) { return lista[i]; });
  }

  // → {decada, filmes, total} ou null. `usados`: {slug: true}.
  function selecaoDaDecada(filmes, dia, usados) {
    var cand = decadasCandidatas(filmes);
    var w = S.semanaDe(dia);
    for (var j = 0; j < cand.length; j++) {
      var c = cand[S.modulo(w + j, cand.length)];
      var escolhidos = girar(c.filmes, w, LIMITE_DECADA, usados || {});
      if (escolhidos) return { decada: c.decada, filmes: escolhidos, total: c.filmes.length };
    }
    return null;
  }

  // → [{chave, nome, filmes, total}], até 2, gêneros distintos.
  function fileirasDeGenero(filmes, dia, usados) {
    var cand = generosCandidatos(filmes);
    var w = S.semanaDe(dia);
    var n = cand.length;
    var u = {};
    Object.keys(usados || {}).forEach(function (s) { u[s] = true; });
    var saida = [];
    [0, 1].forEach(function (slot) {
      for (var j = 0; j < n; j++) {
        var c = cand[S.modulo(2 * w + slot + j, n)];
        if (saida.some(function (x) { return x.chave === c.chave; })) continue;
        var escolhidos = girar(c.filmes, w, LIMITE_GENERO, u);
        if (!escolhidos) continue;
        escolhidos.forEach(function (f) { u[f.slug] = true; });
        saida.push({ chave: c.chave, nome: c.nome, filmes: escolhidos, total: c.filmes.length });
        return;
      }
    });
    return saida;
  }

  // A home inteira de um dia, sem repetir filme.
  // → {escolha, manchete, colecao, recem, decada, generos, slugs}
  function homeDoDia(filmes, dia) {
    var escolha = S.escolhaDoDia(filmes, dia);
    var manchete = escolha && escolha.filme;
    var usados = {};
    var slugs = [];
    function usar(lista) {
      lista.forEach(function (f) { usados[f.slug] = true; slugs.push(f.slug); });
    }
    if (manchete) usar([manchete]);
    var colecao = S.colecaoDoDia(filmes, dia, manchete ? manchete.slug : null);
    if (colecao) usar(colecao.filmes);
    var recem = S.recemDoDia(filmes, dia, slugs.slice());
    if (recem) usar(recem.filmes);
    var decada = selecaoDaDecada(filmes, dia, usados);
    if (decada) usar(decada.filmes);
    var generos = fileirasDeGenero(filmes, dia, usados);
    generos.forEach(function (g) { usar(g.filmes); });
    return { escolha: escolha, manchete: manchete, colecao: colecao, recem: recem,
             decada: decada, generos: generos, slugs: slugs };
  }

  var api = {
    SEMENTE_GENERO: SEMENTE_GENERO, PISO_DECADA: PISO_DECADA,
    LIMITE_DECADA: LIMITE_DECADA, PISO_GENERO_CANDIDATO: PISO_GENERO_CANDIDATO,
    LIMITE_GENERO: LIMITE_GENERO,
    decadasCandidatas: decadasCandidatas, generosCandidatos: generosCandidatos,
    selecaoDaDecada: selecaoDaDecada, fileirasDeGenero: fileirasDeGenero,
    homeDoDia: homeDoDia,
  };

  if (emNode) module.exports = api;
  else root.ESPECTRO_SEMANAL = api;
})(this);
