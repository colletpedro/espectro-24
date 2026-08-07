/* Espectro 24 — filme.js
   Renderiza a tela do filme a partir de window.ESPECTRO_DATA[?slug].
   Regras de produto aplicadas aqui:
   - frequência SEMPRE "~X de N"; largura da barra = X/N.
   - modo degradado (reduzido/sem_analise) sempre visível, nunca escondido.
   - nenhuma nota média/score; a faixa de estrelas é a COTA DE COLETA do
     grupo, rotulada como tal.
   - nenhum texto de review bruto; só temas/paráfrases já validados. */
(function () {
  "use strict";

  var DATA = window.ESPECTRO_DATA || { filmes: {} };
  var app = document.getElementById("app");

  var GRUPO_META = {
    negativas: { label: "Negativas", color: "var(--neg)", cap: "quem não gostou" },
    medianas:  { label: "Medianas",  color: "var(--med)", cap: "quem ficou no meio" },
    positivas: { label: "Positivas", color: "var(--pos)", cap: "quem gostou" },
  };

  var slug = new URLSearchParams(location.search).get("slug") || "";
  var film = DATA.filmes[slug];

  if (!film) {
    app.innerHTML =
      '<div class="section"><h1 class="film-header__title serif">Filme não encontrado</h1>' +
      '<p class="disclaimer">Nenhuma análise para este endereço. ' +
      '<a href="index.html" style="color:var(--pos)">Voltar ao início</a>.</p></div>';
    return;
  }

  document.title = titleOf(film) + " · Espectro 24";
  var footerLink = document.getElementById("footerReviews");
  if (footerLink && film.reviews_url) footerLink.href = film.reviews_url;

  render(film);

  // =====================================================================
  function render(f) {
    app.appendChild(header(f));
    if (f.ficha) app.appendChild(fichaBlock(f.ficha));
    if (f.narrativa) app.appendChild(narrativaBlock(f.narrativa));
    app.appendChild(detailDivider(f));
    (f.buckets || []).forEach(function (b) { app.appendChild(groupBlock(b, f)); });
    // micro-pesquisa (A/B) — módulo separado
    if (window.mountSurvey) window.mountSurvey(app, f);
  }

  // --- header ---
  function header(f) {
    var el = document.createElement("header");
    el.className = "film-header";

    var meta = document.createElement("p");
    meta.className = "film-header__meta";
    var ano = f.ficha && f.ficha.ano ? String(f.ficha.ano) : "";
    meta.innerHTML =
      (ano ? esc(ano) + '<span class="dot">·</span>' : "") +
      fmt(f.total_reviews_observadas) + " reviews observadas";

    var h1 = document.createElement("h1");
    h1.className = "film-header__title";
    h1.textContent = titleOf(f);

    el.appendChild(meta);
    el.appendChild(h1);

    if (f.reviews_url) {
      var chip = document.createElement("a");
      chip.className = "chip";
      chip.href = f.reviews_url;
      chip.target = "_blank";
      chip.rel = "noopener noreferrer";
      chip.innerHTML = "reviews no Letterboxd&nbsp;↗";
      el.appendChild(chip);
    }
    return el;
  }

  // --- ficha (dado novo v1.3.0) ---
  function fichaBlock(ficha) {
    var el = document.createElement("section");
    el.className = "ficha";
    el.setAttribute("aria-label", "Ficha técnica do filme");

    if (ficha.sinopse_oficial) {
      var syn = document.createElement("p");
      syn.className = "ficha__synopsis";
      syn.textContent = ficha.sinopse_oficial;
      el.appendChild(syn);
    }

    var parts = [];
    if (ficha.diretor) parts.push("dir. " + ficha.diretor);
    if (ficha.generos && ficha.generos.length) parts.push(ficha.generos.join(", "));
    if (ficha.duracao_min) parts.push(ficha.duracao_min + " min");
    parts.push("fonte TMDB");

    var line = document.createElement("p");
    line.className = "ficha__line";
    line.innerHTML = parts.map(esc).join('<span class="dot">·</span>');
    el.appendChild(line);

    if (ficha.sinopse_fallback_en) {
      var fb = document.createElement("p");
      fb.className = "ficha__fallback";
      fb.textContent = "⚠ Sinopse oficial em pt-BR indisponível — exibindo a versão em inglês.";
      el.appendChild(fb);
    }
    return el;
  }

  // --- narrativa (A RECEPÇÃO, EM RESUMO) ---
  function narrativaBlock(texto) {
    var el = document.createElement("section");
    el.className = "section narrativa";
    el.setAttribute("aria-labelledby", "resumoLabel");
    el.innerHTML = '<h2 class="section-label" id="resumoLabel">A recepção, em resumo</h2>';
    texto.split(/\n{2,}/).forEach(function (par) {
      var p = par.trim();
      if (!p) return;
      var node = document.createElement("p");
      node.textContent = p;
      el.appendChild(node);
    });
    return el;
  }

  // --- divisor EM DETALHE + disclaimer ---
  // v1.4.0: o disclaimer depende do dado disponível. Sem distribuição real,
  // avisa que os tamanhos NÃO são prevalência (regra v1.2.1). Com ela, o peso
  // real está exibido em cada grupo e o texto passa a explicar o método.
  // Mantidos em sincronia com render.py (DISCLAIMER_*).
  // v1.9.1: as cotas vêm do PRÓPRIO JSON (f.buckets[i].alvo), não de um
  // literal — o frontend não importa config.py, então deriva do dado (mesmo
  // princípio do des-hardcoding já feito em render.py/synthesize.py na
  // v1.9.0). A cota mudou de 50/20/30 para 40/40/40 nessa versão; um
  // literal aqui teria ficado desatualizado sem nenhum erro visível.
  function cotasTexto(f) {
    return (f.buckets || []).map(function (b) { return b.alvo; }).join(" · ");
  }

  function detailDivider(f) {
    var temDistribuicao = !!f.distribuicao;
    var cotas = cotasTexto(f);
    var texto = temDistribuicao
      ? "Análise em profundidade igual por grupo (" + cotas + " reviews); " +
        "o peso real de cada faixa está indicado em cada grupo."
      : "Grupos de " + cotas + " reviews são cotas de coleta — " +
        "não a proporção real das opiniões.";
    var el = document.createElement("div");
    el.className = "detail-divider";
    el.innerHTML =
      '<div class="spectrum-line" aria-hidden="true"></div>' +
      '<p class="detail-divider__label">Em detalhe · tema a tema</p>' +
      '<p class="disclaimer">' + texto + "</p>";
    return el;
  }

  // --- grupo ---
  function groupBlock(b, f) {
    var meta = GRUPO_META[b.bucket] || { label: b.bucket, color: "var(--text)" };
    var el = document.createElement("section");
    el.className = "group";
    el.setAttribute("data-group", b.bucket);
    el.setAttribute("aria-label", "Grupo " + meta.label);

    // header
    var head = document.createElement("div");
    head.className = "group__header";
    var dot = document.createElement("span");
    dot.className = "group__dot";
    dot.style.background = meta.color;
    dot.setAttribute("aria-hidden", "true");
    var name = document.createElement("span");
    name.className = "group__name";
    name.textContent = meta.label.toUpperCase();
    var stars = document.createElement("span");
    stars.className = "group__stars";
    stars.textContent = starBand(b.niveis);
    var count = document.createElement("span");
    count.className = "group__count";
    count.textContent = b.n_validas + " de " + b.alvo + " analisadas";
    head.appendChild(dot);
    head.appendChild(name);
    head.appendChild(stars);
    // v1.4.0: share real do grupo — mono, discreto, MESMO estilo e MESMO
    // formato nos três (neutralidade de TRATAMENTO; a assimetria vem do
    // dado). Omitido por completo quando o filme não tem distribuição.
    if (typeof b.share_real === "number") {
      var share = document.createElement("span");
      share.className = "group__share";
      share.textContent = "~" + b.share_real + "% das notas";
      head.appendChild(share);
    }
    head.appendChild(count);
    el.appendChild(head);

    // avisos de modo degradado — SEMPRE visíveis
    if (b.modo === "reduzido") {
      el.appendChild(warnBox(
        "Modo reduzido: análise baseada em apenas <strong>" + b.n_validas +
        " de " + b.alvo + "</strong> reviews-alvo. Interprete com cautela."));
    }
    if (b.modo === "sem_analise") {
      var w = warnBox(
        "Sem análise temática: apenas <strong>" + b.n_validas +
        "</strong> review(s) válida(s) neste grupo (o piso é 3).");
      var link = document.createElement("a");
      link.className = "sem-analise-link";
      link.href = f.reviews_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.innerHTML = "→ " + b.n_validas + " review(s) disponíveis no Letterboxd&nbsp;↗";
      w.appendChild(link);
      el.appendChild(w);
      // sem_analise não lista temas
      if (b.observacao_geral) el.appendChild(obsBlock(b.observacao_geral));
      return el;
    }

    // flags de idioma/escopo do bucket (telemetria), se houver
    if (b.idioma_invalido) {
      el.appendChild(warnBox("Idioma: saída não confirmadamente em pt-BR — revisão manual pendente."));
    }
    if (b.escopo_suspeito) {
      el.appendChild(warnBox("Escopo: a observação pode generalizar este recorte — revisão manual pendente."));
    }

    // temas
    if (b.temas && b.temas.length) {
      var themes = document.createElement("div");
      themes.className = "themes";
      b.temas.forEach(function (t, i) {
        themes.appendChild(themeRow(t, b.bucket, i));
      });
      el.appendChild(themes);
    }

    if (b.observacao_geral) el.appendChild(obsBlock(b.observacao_geral));
    return el;
  }

  function themeRow(t, bucket, idx) {
    var row = document.createElement("div");
    row.className = "theme";

    var x = t.mencoes_aproximadas, n = t.n_reviews_analisadas;
    var pct = n > 0 ? Math.max(0, Math.min(100, (x / n) * 100)) : 0;

    var top = document.createElement("div");
    top.className = "theme__top";
    var nm = document.createElement("span");
    nm.className = "theme__name";
    nm.textContent = t.tema;
    var freq = document.createElement("span");
    freq.className = "theme__freq";
    freq.textContent = "~" + x + " de " + n;           // regra: sempre ~X de N
    top.appendChild(nm);
    top.appendChild(freq);
    row.appendChild(top);

    var bar = document.createElement("div");
    bar.className = "theme__bar";
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", "Mencionado em cerca de " + x + " de " + n + " reviews");
    var fill = document.createElement("span");
    fill.style.width = pct.toFixed(1) + "%";           // largura = X/N
    bar.appendChild(fill);
    row.appendChild(bar);

    // exemplo parafraseado expansível
    if (t.exemplo_parafraseado) {
      var id = "ex-" + bucket + "-" + idx;
      var btn = document.createElement("button");
      btn.className = "theme__toggle";
      btn.type = "button";
      btn.setAttribute("aria-expanded", "false");
      btn.setAttribute("aria-controls", id);
      btn.innerHTML = 'Exemplo parafraseado <span class="plus" aria-hidden="true">+</span>';

      var ex = document.createElement("div");
      ex.className = "theme__example";
      ex.id = id;
      ex.textContent = t.exemplo_parafraseado;
      if (t.aspas_removidas) {
        var fl = document.createElement("span");
        fl.className = "theme__flag";
        fl.textContent = "aspas de citação removidas mecanicamente";
        ex.appendChild(fl);
      }

      btn.addEventListener("click", function () {
        var open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", String(!open));
        ex.classList.toggle("is-open", !open);
      });

      row.appendChild(btn);
      row.appendChild(ex);
    }
    return row;
  }

  function obsBlock(texto) {
    var p = document.createElement("p");
    p.className = "group__obs";
    p.textContent = texto;
    return p;
  }

  function warnBox(html) {
    var el = document.createElement("div");
    el.className = "mode-warning";
    el.setAttribute("role", "note");
    el.innerHTML =
      '<span class="mode-warning__icon" aria-hidden="true">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>' +
      "</span><div>" + html + "</div>";
    return el;
  }

  // --- helpers ---
  function starBand(niveis) {
    if (!niveis || !niveis.length) return "";
    var vals = niveis.map(function (n) { return n.nivel; });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    return "★ " + starTxt(lo) + "–" + starTxt(hi);
  }
  function starTxt(n) {
    return Number.isInteger(n) ? String(n) : String(n).replace(".", ",");
  }
  function titleOf(f) {
    return (f.ficha && f.ficha.titulo) || f.slug;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("pt-BR") : "—";
  }
})();
