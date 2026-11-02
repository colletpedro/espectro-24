/* Espectro 24 — inicio.js
   A APRESENTAÇÃO da home editorial. Só monta DOM e liga eventos: o que
   mostrar vem de `selecao.js` (manchete, coleção do dia, recém-chegados,
   modo do logo), a busca vem de `busca.js` e toda a prosa vem de
   `textos_home.js`. A rodada de tipografia e paleta troca este arquivo e o
   CSS sem tocar nos outros três.

   Lê só `window.ESPECTRO_INDICE` (`js/indice.js`), nunca o `data.js` de
   5,6 MB — que continua sendo o dado de /filmes e da página do filme. De
   imagem, o índice só tem backdrop, stills e logo: a home NUNCA mostra
   pôster (`poster.js` entra só pela URL do CDN, `P.url`).

   `?dia=AAAA-MM-DD` fixa a data da seleção (conferência manual de um dia
   específico); sem ele, vale o dia de hoje em America/Sao_Paulo. */
(function () {
  "use strict";

  var IDX = window.ESPECTRO_INDICE || { filmes: [] };
  var X = window.ESPECTRO_EXPLORAR;
  var W = window.ESPECTRO_SEMANAL;
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

  // O cabeçalho (barra, nome, links, busca) é de js/cabecalho.js; o cartão
  // de filme (still, título, metadado, hover), de js/cartoes.js.
  var C = window.ESPECTRO_CARTOES;
  var quadro = C.quadro, preencherMeta = C.preencherMeta,
      faixaDosGrupos = C.faixaDosGrupos, TAMANHO_LOGO = C.TAMANHO_LOGO;

  // ------------------------------------------------------------------
  // 1. MANCHETE (o filme do dia)
  // ------------------------------------------------------------------
  // A home inteira do dia vem de semanal.js (`homeDoDia`): cada bloco pula
  // os filmes dos anteriores, então nenhum filme aparece duas vezes.
  var HOME = W.homeDoDia(FILMES, DIA);
  var escolha = HOME.escolha;
  var manchete = HOME.manchete;

  (function montarManchete() {
    var caixa = document.getElementById("manchete");
    var f = manchete;
    if (!caixa || !f) { if (caixa) caixa.hidden = true; return; }
    var j = T.justificar(f, DIA);
    caixa.dataset.slug = f.slug;
    caixa.dataset.gancho = j.gancho;
    caixa.dataset.motivo = escolha.motivo;   // "aniversario" | "permutacao"

    var rotulo = el("h2", "visually-hidden", T.ROTULO_FILME_DO_DIA);
    rotulo.id = "mancheteRotulo";
    caixa.appendChild(rotulo);

    // o still, o véu e o bloco do título (logo, nativo, linha) são do
    // componente compartilhado (cartoes.js); a home põe a justificativa
    C.montarManchete(caixa, f, {
      nivel: "h3",
      href: hrefFilme(f.slug),
      partes: function (comTitulo) { return T.partesDaManchete(f, comTitulo); },
      justificativa: j.texto,
      faixa: true,
    });
  })();

  // ------------------------------------------------------------------
  // 2. COLEÇÃO DO DIA
  // ------------------------------------------------------------------
  function cartao(f, classe, sizes, meta, desloc) {
    return C.cartao(f, classe, sizes, meta, desloc, "");
  }

  function soAno(f) { return f.ano ? [{ tipo: "ano", texto: String(f.ano) }] : []; }

  // O bloco "texto em 1/3 e still grande em 2/3, fileira embaixo" — a
  // coleção do dia e a seleção da década. `b`: {chave, titulo, rotulo,
  // descricao, frase, filmes, href (ver todos) ou null}.
  function montarBlocoGrande(caixa, b) {
    var topo = el("div", "ed-colecao__topo");
    var bloco = el("div", "ed-colecao__texto");
    if (b.rotulo) bloco.appendChild(el("p", "section-label ed-colecao__rotulo", b.rotulo));
    var h = el("h2", "ed-colecao__titulo", b.titulo);
    h.id = b.idTitulo;
    bloco.appendChild(h);
    if (b.descricao) bloco.appendChild(el("p", "ed-colecao__descricao", b.descricao));
    if (b.frase) bloco.appendChild(el("p", "ed-colecao__frase", b.frase));
    if (b.href) {
      var todos = el("a", "ed-link mono", T.ROTULO_COLECAO_TODOS + " →");
      todos.href = b.href;
      bloco.appendChild(todos);
    }
    topo.appendChild(bloco);
    // o still grande abre no segundo quadro, para não repetir a imagem do
    // mesmo filme na fileira logo abaixo
    topo.appendChild(cartao(b.filmes[0], "ed-colecao__destaque",
      "(max-width: 699px) 100vw, 66vw", soAno, 1));
    caixa.appendChild(topo);

    var fileira = el("ul", "ed-colecao__fileira");
    b.filmes.forEach(function (f) {
      var li = el("li");
      li.appendChild(cartao(f, null, "(max-width: 699px) 40vw, 25vw", soAno));
      fileira.appendChild(li);
    });
    caixa.appendChild(fileira);
  }

  (function montarColecao() {
    var caixa = document.getElementById("colecaoDoDia");
    var cd = HOME.colecao;
    if (!caixa || !cd || !cd.filmes.length) { if (caixa) caixa.hidden = true; return; }
    var txt = T.textoDaColecao(cd.colecao);
    caixa.dataset.chave = cd.colecao.chave;
    montarBlocoGrande(caixa, {
      idTitulo: "colecaoTitulo", rotulo: T.ROTULO_COLECAO, titulo: txt.titulo,
      descricao: txt.descricao, frase: txt.frase, filmes: cd.filmes,
      href: cd.total > cd.filmes.length
        ? HREF_CATALOGO + "?colecao=" + encodeURIComponent(cd.colecao.chave) : null,
    });
  })();

  // ------------------------------------------------------------------
  // 3. RECÉM-CHEGADOS (3 por dia, da leva mais recente)
  // ------------------------------------------------------------------
  (function montarRecem() {
    var caixa = document.getElementById("recemChegados");
    var r = HOME.recem;
    if (!caixa || !r || !r.filmes.length) { if (caixa) caixa.hidden = true; return; }
    var cab = el("div", "ed-recem__cabeca");
    var h = el("h2", "section-label ed-recem__titulo", T.ROTULO_RECEM);
    h.id = "recemTitulo";
    cab.appendChild(h);
    // "ver todos" abre /filmes FILTRADO pela leva (`?desde=`, lido por
    // catalogo.js) — mesmo critério de data desta seção.
    var todos = el("a", "ed-link mono", T.ROTULO_RECEM_TODOS + " →");
    todos.href = HREF_CATALOGO + "?desde=" + r.desde;
    cab.appendChild(todos);
    caixa.appendChild(cab);
    var grade = el("ul", "ed-recem__grade");
    r.filmes.forEach(function (f) {
      var li = el("li");
      li.appendChild(cartao(f, null, "(max-width: 699px) 100vw, 33vw", T.partesDiretorAno));
      grade.appendChild(li);
    });
    caixa.appendChild(grade);
  })();

  // ------------------------------------------------------------------
  // 4. SELEÇÃO DA DÉCADA (semanal)
  // ------------------------------------------------------------------
  (function montarDecada() {
    var caixa = document.getElementById("selecaoDecada");
    var d = HOME.decada;
    if (!caixa || !d) { if (caixa) caixa.hidden = true; return; }
    caixa.dataset.decada = d.decada;
    montarBlocoGrande(caixa, {
      idTitulo: "decadaTitulo", titulo: T.tituloDaDecada(d.decada),
      descricao: T.descricaoDaDecada(d.decada), filmes: d.filmes,
      href: HREF_CATALOGO + "?decada=" + d.decada,
    });
  })();

  // ------------------------------------------------------------------
  // 5 e 6. FILEIRAS DE GÊNERO (semanais): grade de 4, "Diretor · Ano"
  // ------------------------------------------------------------------
  ["generoUm", "generoDois"].forEach(function (id, i) {
    var caixa = document.getElementById(id);
    var g = HOME.generos[i];
    if (!caixa || !g) { if (caixa) caixa.hidden = true; return; }
    caixa.dataset.genero = g.chave;
    var cab = el("div", "ed-genero__cabeca");
    var h = el("h2", "section-label ed-genero__titulo", g.nome);
    h.id = id + "Titulo";
    cab.appendChild(h);
    var todos = el("a", "ed-link mono", T.ROTULO_COLECAO_TODOS + " →");
    todos.href = HREF_CATALOGO + "?genero=" + encodeURIComponent(g.chave);
    cab.appendChild(todos);
    caixa.appendChild(cab);
    var grade = el("ul", "ed-genero__grade");
    g.filmes.forEach(function (f) {
      var li = el("li");
      li.appendChild(cartao(f, null, "(max-width: 699px) 50vw, 25vw", T.partesDiretorAno));
      grade.appendChild(li);
    });
    caixa.appendChild(grade);
  });

  // ------------------------------------------------------------------
  // 7. EXPLORAR — as portas de entrada de /filmes, só texto, discreto: um
  // único <details> fechado em qualquer largura. Conta só os ELEGÍVEIS
  // (fora a lista de exclusão da vitrine); as contagens aparecem em /filmes.
  // ------------------------------------------------------------------
  (function montarExplorar() {
    var caixa = document.getElementById("explorar");
    if (!caixa) return;
    var g = X.gruposDoExplorar(FILMES, { elegiveis: true, piso: X.PISO_HOME });
    var d = el("details", "ed-explorar__caixa");
    var s = el("summary", "ed-explorar__resumo", T.RESUMO_EXPLORAR);
    s.id = "explorarTitulo";
    d.appendChild(s);
    var colunas = el("div", "ed-explorar__grupos");
    var PARAM = { assunto: "colecao", decada: "decada", genero: "genero", pais: "pais" };
    ["assunto", "decada", "genero", "pais"].forEach(function (k) {
      if (!g[k].length) return;
      var grupo = el("div", "ed-explorar__grupo");
      grupo.dataset.grupo = k;
      grupo.appendChild(el("p", "ed-explorar__nome", T.ROTULO_GRUPO_EXPLORAR[k]));
      var ul = el("ul", "ed-explorar__lista");
      g[k].forEach(function (it) {
        var li = el("li");
        var a = el("a", "ed-explorar__item", it.nome);
        a.href = HREF_CATALOGO + "?" + PARAM[k] + "=" + encodeURIComponent(String(it.chave));
        li.appendChild(a);
        ul.appendChild(li);
      });
      grupo.appendChild(ul);
      colunas.appendChild(grupo);
    });
    d.appendChild(colunas);
    var indice = el("p", "ed-explorar__indice");
    var ai = el("a", "ed-link mono", T.LINK_INDICE + " →");
    ai.href = HREF_CATALOGO + "?vista=indice";
    indice.appendChild(ai);
    d.appendChild(indice);
    caixa.appendChild(d);
  })();
})();
