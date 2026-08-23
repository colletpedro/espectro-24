/* Espectro 24 — home.js
   Monta os cards do catálogo a partir de window.ESPECTRO_DATA e liga a BUSCA.

   v1.9.14: a busca deixou de ser decorativa. Até aqui ela exibia "Busca em
   breve" e o catálogo inteiro seguia abaixo, sem filtrar nada — não havia
   critério de filtro que não fosse o título. Com a taxonomia fechada de 10
   eixos (§2.5) passa a haver: o leitor procura "ritmo" e recebe os filmes
   cujos grupos falam de ritmo. Filtra por TÍTULO e por EIXO, sobre o dado já
   embutido, sem uma requisição de rede. */
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

  // Rótulos dos eixos — a mesma lista fechada de filme.js. Duplicada aqui
  // (e não importada) porque os dois scripts são independentes e carregados
  // em páginas diferentes; a lista é FECHADA e versionada pelo taxonomia_id,
  // então a divergência seria visível no primeiro filme classificado.
  var EIXO_LABEL = {
    ritmo: "ritmo", atuacao: "atuação", direcao_imagem: "direção e imagem",
    roteiro_estrutura: "roteiro e estrutura", som_trilha: "som e trilha",
    tom_atmosfera: "tom e atmosfera", impacto_emocional: "impacto emocional",
    comparacoes: "comparações", expectativa: "expectativa",
    critica_social: "crítica social",
  };

  // O que cada filme responde na busca: título + os eixos EM DESTAQUE, com
  // acento removido para que "atuacao" e "atuação" achem a mesma coisa.
  //
  // Só os eixos que viraram BULLET (§2.5: 2 de frequência + 3 de contraste
  // por grupo), nunca os 10. Medido nos 3 filmes do catálogo: todos os 10
  // eixos aparecem em todos os 3, então casar com a linha inteira devolveria
  // o catálogo completo para qualquer eixo — um filtro que não filtra é o
  // mesmo defeito da busca decorativa, com outra roupa.
  function chavesDe(f) {
    var termos = [(f.ficha && f.ficha.titulo) || "", f.slug];
    ((f.eixos && f.eixos.linhas) || []).forEach(function (l) {
      var papeis = l.bullet_de || {};
      var destaque = Object.keys(papeis).some(function (b) { return !!papeis[b]; });
      if (destaque) termos.push(l.eixo, EIXO_LABEL[l.eixo] || "");
    });
    return termos.map(norm).filter(Boolean);
  }

  function norm(s) {
    return String(s).toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  // [v1.9.16] A contagem vem do próprio dado embutido, não de um literal —
  // mesmo princípio de v1.9.1 (§3[B1], "50·20·30 remanescente... passa a
  // derivar do próprio JSON"): um catálogo que cresce de 3 para 35 não pode
  // deixar a home dizendo "3" até alguém lembrar de editar o HTML à mão.
  var microcopy = document.getElementById("homeMicrocopy");
  if (microcopy) {
    var n = DATA.catalogo.length;
    microcopy.textContent = n + (n === 1 ? " análise pronta" : " análises prontas")
      + " · busca por título ou eixo";
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
    a.dataset.busca = chavesDe(f).join(" | ");
    cards.appendChild(a);
  });

  // --- busca REAL: título ou eixo ---
  var input = document.getElementById("search");
  var hint = document.getElementById("searchHint");
  var todos = [].slice.call(cards.children);

  function filtrar() {
    var q = norm(input.value.trim());
    if (!q) {
      todos.forEach(function (el) { el.hidden = false; });
      hint.classList.remove("is-visible");
      hint.textContent = "";
      return;
    }
    var n = 0;
    todos.forEach(function (el) {
      var casa = el.dataset.busca.indexOf(q) !== -1;
      el.hidden = !casa;
      if (casa) n++;
    });
    // A mensagem diz o que NÃO casou, em vez de fingir que a funcionalidade
    // não existe — era esse o defeito do "Busca em breve".
    hint.textContent = n
      ? n + (n === 1 ? " filme encontrado" : " filmes encontrados")
      : "Nada com \u201C" + input.value.trim() + "\u201D — a busca cobre o "
        + "título e os eixos em destaque de cada análise.";
    hint.classList.add("is-visible");
  }

  input.addEventListener("input", filtrar);
  input.addEventListener("focus", function () { if (input.value) filtrar(); });

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("pt-BR") : "—";
  }
})();
