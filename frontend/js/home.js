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

  // --- mosaico do catálogo (v1.9.17; célula refeita na v1.9.18) ---
  // Ordem de leitura igual à do resto do site: quem não gostou primeiro,
  // quem gostou por último (mesma ordem de `GRUPO_META` em filme.js).
  var GRUPOS = ["negativas", "medianas", "positivas"];
  // [v1.9.18] paleta PARALELA, só para a faixa da home — ver `:root` em
  // styles.css para o porquê (as cores oficiais dos grupos, --neg/--med/
  // --pos, continuam intactas e são as que `filme.html` usa).
  var COR_GRUPO_HOME = {
    negativas: "var(--neg-home)", medianas: "var(--med-home)", positivas: "var(--pos-home)",
  };

  // A faixa é a distribuição REAL do histograma (`distribuicao.por_bucket`,
  // já em percentual, soma ~100) — não a cota de análise, que é sempre
  // 40/40/40 e não diria nada sobre a recepção real. RESTRIÇÃO DE PRODUTO:
  // isto é o único "número" da célula, e ele nunca vira nota, score ou
  // média — é proporção de TRÊS grupos, nunca um valor único agregado.
  function barraDe(f) {
    var pb = f.distribuicao && f.distribuicao.por_bucket;
    if (!pb) return null;
    var total = GRUPOS.reduce(function (s, g) { return s + (pb[g] || 0); }, 0);
    if (!total) return null;
    return GRUPOS.map(function (g) {
      return { grupo: g, pct: ((pb[g] || 0) / total) * 100 };
    });
  }

  var cards = document.getElementById("filmCards");
  DATA.catalogo.forEach(function (slug) {
    var f = DATA.filmes[slug];
    if (!f) return;
    var titulo = (f.ficha && f.ficha.titulo) || slug;
    var ano = (f.ficha && f.ficha.ano) || "";

    var a = document.createElement("a");
    a.className = "mosaic-cell";
    a.href = "filme.html?slug=" + encodeURIComponent(slug);
    a.setAttribute("aria-label", titulo + (ano ? " (" + ano + ")" : "") + " — ver análise");

    // [v1.9.29] O PÔSTER — e isto é REDESENHO da célula, não acréscimo.
    //
    // A célula da v1.9.18 foi desenhada SEM imagem: um card escuro em 4/5,
    // com o texto como protagonista e uma faixa de 5px na base. Encaixar um
    // pôster nela sem mexer no resto daria o pior dos dois — uma miniatura
    // apertada disputando espaço com o título. Então a célula muda de
    // proporção (4/5 → 2/3, a do próprio pôster), o pôster passa a ocupar a
    // célula inteira, e o texto sobe para um degradê na base.
    //
    // O QUE NÃO MUDA, e é o motivo de a faixa continuar existindo: a home
    // não vira um catálogo de capas. A faixa é o único sinal de RECEPÇÃO da
    // célula, e sobre imagem ela precisava de mais presença que os 5px que
    // tinha contra fundo chapado — subiu para 6px e ganhou um fio escuro em
    // cima, que a separa de qualquer pôster (claro ou escuro) sem depender
    // da cor da arte. Cores, ordem e semântica: idênticas.
    //
    // A ANIMAÇÃO DA BARRA NÃO RODA AQUI — decisão registrada (§3[E]).
    // Trinta e cinco sequências simultâneas na entrada viram espetáculo e
    // competem entre si; a home mostra a faixa no ESTADO FINAL, e a
    // animação continua sendo o momento de abrir um filme.
    if (window.ESPECTRO_POSTER) {
      a.appendChild(window.ESPECTRO_POSTER.montar(f.ficha, {
        uso: "mosaico", titulo: titulo, ano: ano, lazy: true,
      }));
    }

    // corpo: título sempre visível (Entrega 1, v1.9.18 — revoga o "só no
    // hover" da v1.9.17), ano abaixo, alinhados na base da célula.
    var body = document.createElement("span");
    body.className = "mosaic-cell__body";
    var h = document.createElement("span");
    h.className = "mosaic-cell__title";
    h.textContent = titulo;
    body.appendChild(h);
    if (ano) {
      var y = document.createElement("span");
      y.className = "mosaic-cell__year";
      y.textContent = String(ano);
      body.appendChild(y);
    }

    // faixa fina colada na base — não mais a célula inteira.
    var strip = document.createElement("span");
    strip.className = "mosaic-cell__strip";
    strip.setAttribute("aria-hidden", "true");
    var partes = barraDe(f);
    if (partes) {
      partes.forEach(function (p) {
        if (p.pct <= 0) return;
        var seg = document.createElement("span");
        seg.className = "mosaic-cell__seg";
        seg.style.background = COR_GRUPO_HOME[p.grupo];
        seg.style.width = p.pct + "%";
        strip.appendChild(seg);
      });
    } else {
      // sem distribuição real (não deveria acontecer no catálogo de
      // produção — todo filme publicado tem histograma; fallback neutro
      // para não deixar a faixa vazia se algum dia acontecer).
      strip.style.background = "var(--border)";
    }

    a.appendChild(body);
    a.appendChild(strip);
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
})();
