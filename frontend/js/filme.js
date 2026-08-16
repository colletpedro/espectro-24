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

  // v1.9.14: rótulos dos 10 eixos (§2.5). O JSON carrega o identificador
  // técnico; a tela mostra português. Lista FECHADA — eixo desconhecido cai
  // no próprio identificador em vez de sumir da tabela.
  var EIXO_LABEL = {
    ritmo: "Ritmo", atuacao: "Atuação", direcao_imagem: "Direção e imagem",
    roteiro_estrutura: "Roteiro e estrutura", som_trilha: "Som e trilha",
    tom_atmosfera: "Tom e atmosfera", impacto_emocional: "Impacto emocional",
    comparacoes: "Comparações", expectativa: "Expectativa",
    critica_social: "Crítica social",
  };

  // Permissões do piso escalonado (§3[C3]) — as MESMAS quatro do backend.
  // A linha do eixo acompanha o que cada bucket pode dizer, célula a célula.
  var PISO = {
    completa:          { temas: true,  numero: true },
    sem_quantificador: { temas: true,  numero: true },
    sem_numero:        { temas: true,  numero: false },
    sem_analise:       { temas: false, numero: false },
  };

  var MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
               "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

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
    // v1.9.14: os três grupos ALINHADOS POR EIXO — a promessa estrutural do
    // produto. Vem antes das listas por grupo: é a leitura comparativa, e as
    // listas abaixo seguem servindo o detalhe (exemplo, avisos, observação).
    var eixos = eixosBlock(f);
    if (eixos) app.appendChild(eixos);
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


  // =====================================================================
  // v1.9.14 — OS TRÊS GRUPOS ALINHADOS POR EIXO (§[E])
  //
  // A promessa estrutural do produto: com eixo fixo, os três buckets ficam
  // comparáveis célula a célula, em vez de três listas soltas que o leitor
  // precisa reconciliar de cabeça.
  //
  // Quatro estados, e NENHUM deles é ausência de conteúdo:
  //   1. eixo que um grupo não menciona → célula marcada como vazia;
  //   2. `contraste: valorativo` → o alinhamento existe, nenhuma linha tem
  //      contraste, e a área ganha enunciado próprio (22 dos 35 filmes do
  //      catálogo caem aqui — se parecer bug, o estado não está desenhado);
  //   3. piso escalonado → a linha acompanha o que AQUELE grupo pode dizer;
  //   4. filme sem bloco `eixos` → esta seção não existe e a página cai na
  //      lista de temas de sempre.
  // =====================================================================
  function eixosBlock(f) {
    var e = f.eixos;
    if (!e || !e.linhas || !e.linhas.length) return null;   // estado 4

    var buckets = (f.buckets || []).map(function (b) { return b.bucket; });
    var piso = {};
    (f.buckets || []).forEach(function (b) {
      piso[b.bucket] = PISO[b.estado_piso] || PISO.completa;
    });

    var valorativo = e.contraste === "valorativo";
    var el = document.createElement("section");
    el.className = "section eixos";
    el.setAttribute("data-contraste", e.contraste || "");
    el.setAttribute("aria-labelledby", "eixosLabel");
    el.innerHTML =
      '<h2 class="section-label" id="eixosLabel">Eixo a eixo · os três grupos lado a lado</h2>';

    el.appendChild(contrasteBox(e, valorativo));

    // As linhas exibidas são as que viraram BULLET em algum grupo (§2.5:
    // 2 de frequência + 3 de contraste, por grupo). As demais ficam atrás
    // do "ver todos os eixos" — presentes, não escondidas.
    var destaque = e.linhas.filter(function (l) { return temBullet(l); });
    var resto = e.linhas.filter(function (l) { return !temBullet(l); });

    el.appendChild(gradeCabecalho(buckets));
    destaque.forEach(function (l) { el.appendChild(linhaEixo(l, buckets, piso)); });

    if (resto.length) {
      var det = document.createElement("details");
      det.className = "eixos__resto";
      var sum = document.createElement("summary");
      sum.textContent = "ver os outros " + resto.length + " eixos";
      det.appendChild(sum);
      resto.forEach(function (l) { det.appendChild(linhaEixo(l, buckets, piso)); });
      el.appendChild(det);
    }

    el.appendChild(denominadorNota(e));
    return el;
  }

  function temBullet(linha) {
    var b = linha.bullet_de || {};
    return Object.keys(b).some(function (k) { return !!b[k]; });
  }

  // O enunciado do estado `contraste` — PRIMEIRA CLASSE, nunca uma ausência.
  function contrasteBox(e, valorativo) {
    var el = document.createElement("p");
    el.className = "eixos__contraste";
    el.textContent = valorativo
      ? "Os três grupos falam das mesmas coisas — e discordam sobre se elas "
        + "funcionam. Nenhum assunto separa os grupos aqui: a divergência é "
        + "de veredito, não de tema."
      : "Há assunto que separa os grupos: as linhas marcadas como contraste "
        + "são faladas por um grupo muito mais que pelos outros.";
    return el;
  }

  function gradeCabecalho(buckets) {
    var el = document.createElement("div");
    el.className = "eixos__head";
    el.setAttribute("aria-hidden", "true");
    el.appendChild(document.createElement("span"));   // coluna do rótulo
    buckets.forEach(function (nome) {
      var meta = GRUPO_META[nome] || { label: nome, color: "var(--text)" };
      var c = document.createElement("span");
      c.className = "eixos__head-cell";
      c.style.color = meta.color;
      c.textContent = meta.label.toUpperCase();
      el.appendChild(c);
    });
    return el;
  }

  function linhaEixo(linha, buckets, piso) {
    var el = document.createElement("div");
    el.className = "eixos__row";
    el.setAttribute("data-eixo", linha.eixo);

    var nome = document.createElement("div");
    nome.className = "eixos__axis";
    nome.textContent = EIXO_LABEL[linha.eixo] || linha.eixo;

    // O selo de contraste é por GRUPO, e vai na célula daquele grupo — pôr
    // no rótulo da linha diria que a linha inteira é contraste, quando o
    // contraste é sempre de UM grupo contra os outros dois.
    el.appendChild(nome);

    buckets.forEach(function (bucket) {
      el.appendChild(celula(linha, bucket, piso[bucket] || PISO.completa));
    });
    return el;
  }

  function celula(linha, bucket, permissao) {
    var cel = document.createElement("div");
    cel.className = "eixos__cell";
    cel.setAttribute("data-group", bucket);

    var dados = (linha.por_bucket || {})[bucket];

    // Estado 3 — piso escalonado: grupo sem análise temática não tem célula.
    if (!dados || !permissao.temas) {
      cel.classList.add("is-empty");
      cel.innerHTML = '<span class="eixos__none">sem análise</span>';
      return cel;
    }
    // Estado 1 — o grupo simplesmente não fala deste eixo.
    if (!dados.mencoes) {
      cel.classList.add("is-empty");
      cel.innerHTML = '<span class="eixos__none">não menciona</span>';
      return cel;
    }

    var papel = (linha.bullet_de || {})[bucket];
    if (papel && papel !== "frequencia") {
      var selo = document.createElement("span");
      selo.className = "eixos__badge";
      selo.textContent = "só este grupo";
      selo.title = "Lift de " + fmtPP(dados.lift_pp) + " sobre o grupo "
                 + "seguinte — acima da margem de contraste.";
      cel.appendChild(selo);
    }

    if (dados.tema) {
      var t = document.createElement("span");
      t.className = "eixos__tema";
      t.textContent = dados.tema;
      cel.appendChild(t);
    }

    // O NÚMERO: sempre "X de N", nunca percentual solto — e omitido quando
    // o piso do grupo não permite citar número (§3[C3]).
    if (permissao.numero) {
      var freq = document.createElement("span");
      freq.className = "eixos__freq";
      freq.textContent = dados.mencoes + " de " + dados.de_n;
      cel.appendChild(freq);
      var bar = document.createElement("span");
      bar.className = "eixos__bar";
      bar.setAttribute("role", "img");
      bar.setAttribute("aria-label",
        "Mencionado em " + dados.mencoes + " de " + dados.de_n
        + " reviews classificadas");
      var fill = document.createElement("span");
      fill.style.width = (dados.de_n
        ? Math.max(0, Math.min(100, (dados.mencoes / dados.de_n) * 100)) : 0)
        .toFixed(1) + "%";
      bar.appendChild(fill);
      cel.appendChild(bar);
    } else {
      var av = document.createElement("span");
      av.className = "eixos__freq is-muted";
      av.textContent = "amostra pequena demais para número";
      cel.appendChild(av);
    }

    // Temas do MESMO grupo que caíram neste eixo e não ficaram com a célula
    // (§D3). Aparecem porque a alternativa é o leitor perder tema: com 6
    // temas e 10 eixos a colisão é frequente.
    var outros = dados.temas_no_mesmo_eixo || [];
    if (outros.length) {
      var mais = document.createElement("span");
      mais.className = "eixos__mais";
      mais.textContent = "+ " + outros.join(" · ");
      cel.appendChild(mais);
    }
    return cel;
  }

  // O denominador desta tabela NÃO é o do cabeçalho do grupo. São duas
  // amostras de 40 diferentes (§[D3], "Duas populações de 40"), e apresentá-las
  // com o mesmo rótulo repetiria o defeito que a declaração da janela
  // temporal fecha do outro lado.
  function denominadorNota(e) {
    var el = document.createElement("p");
    el.className = "disclaimer eixos__nota";
    var fonte = (e.fonte_classificacao || {}).por_bucket || {};
    var sobre = Object.keys(fonte).map(function (b) {
      return (GRUPO_META[b] ? GRUPO_META[b].label.toLowerCase() : b) + " "
        + fonte[b].sobreposicao_com_analisadas + "/" + fonte[b].n_classificadas;
    });
    el.textContent =
      "Os números desta tabela contam reviews CLASSIFICADAS por eixo — uma "
      + "amostra do mesmo grupo, do mesmo tamanho, mas não exatamente as "
      + "mesmas reviews que a lista abaixo resume"
      + (sobre.length ? " (em comum: " + sobre.join(", ") + ")" : "")
      + ". Contraste com margem de " + (e.margem_lift_pp || 20)
      + " pontos percentuais.";
    return el;
  }

  function fmtPP(v) {
    return (typeof v === "number" ? v.toFixed(1).replace(".", ",") : "?") + "pp";
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

    // v1.9.14 (Entrega 6): a JANELA da amostra vem logo abaixo do
    // DENOMINADOR ("40 de 40 analisadas"), nunca ao lado do "~X% das notas".
    // O peso vem do histograma de NOTAS, que acumula desde 2012; carimbar
    // nele uma janela de semanas diria que as notas todas são recentes. São
    // duas populações, e a linha separada é o que impede a leitura errada.
    var janela = janelaTexto(b.janela_amostra);
    if (janela) {
      var jl = document.createElement("p");
      jl.className = "group__janela";
      jl.textContent = janela;
      el.appendChild(jl);
    }

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

  // A janela sai dos QUANTIS (p5-p95), nunca de min/max nem de média: `data`
  // é a data ASSISTIDA (diário de quem escreveu), e um único registro
  // atrasado domina os extremos — em `cure`/negativas o `min` é 2024 contra
  // uma p5 de maio de 2026, e há review datada de 1442 no catálogo. A média
  // seria mais lisonjeira (janela "mais ampla") e menos verdadeira.
  function mesAno(iso) {
    var p = String(iso || "").split("-");
    if (p.length < 2) return null;
    var m = MESES[parseInt(p[1], 10) - 1];
    return m ? { mes: m, ano: p[0] } : null;
  }

  function janelaTexto(j) {
    if (!j || !j.p5 || !j.p95) return null;
    var a = mesAno(j.p5), b = mesAno(j.p95);
    if (!a || !b) return null;
    var quando;
    if (a.mes === b.mes && a.ano === b.ano) {
      quando = "em " + a.mes + " de " + a.ano;
    } else if (a.ano === b.ano) {
      quando = "entre " + a.mes + " e " + b.mes + " de " + a.ano;
    } else {
      quando = "entre " + a.mes + " de " + a.ano + " e " + b.mes + " de " + b.ano;
    }
    return "escritas majoritariamente " + quando;
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
