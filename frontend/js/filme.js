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

  var params = new URLSearchParams(location.search);
  var slug = params.get("slug") || "";
  // [v1.9.19, Entrega 7] tint de fundo por sentimento — atrás de FLAG,
  // nunca ligado por padrão. `?tint=1` na URL liga só nesta visita, pra o
  // dono do projeto comparar com/sem sem precisar de deploy. Ver `.is-tinted`
  // em styles.css — 2-3% de opacidade, mesmos tokens de cor de sempre.
  var TINT = params.get("tint") === "1";
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
  // [v1.9.19] REORDENAÇÃO DA PÁGINA — dados primeiro.
  //
  // Ordem anterior (até v1.9.16): header → ficha → narrativa completa →
  // "eixo a eixo" (tabela de 3 colunas) → listas por grupo → pesquisa.
  // Feedback de usuários reais: a parede de texto aparecia ANTES dos
  // bullets e ninguém lia; havia redundância entre o resumo narrativo no
  // topo e a observação por grupo no fim; a tabela "eixo a eixo" não
  // funcionava na prática.
  //
  // Ordem nova: header → ficha → VEREDITO (código, zero LLM, Entrega 2) →
  // bullets agrupados por SENTIMENTO (Entrega 3) → narrativa completa
  // COLAPSADA (existe, só deixa de ser a primeira coisa) → pesquisa.
  //
  // A tabela "eixo a eixo" SAI da tela (Entrega 5) — decisão de produto,
  // não técnica. O bloco `eixos` do JSON continua existindo, continua
  // sendo calculado do mesmo jeito, e passa a alimentar DUAS coisas que
  // não existiam antes: o veredito (Entrega 2) e a ORDEM dos bullets
  // dentro de cada grupo (temas com papel de contraste sobem — ver
  // `ordenarTemasPorEixo`). Ver `veredictoBlock`/`sentimentGroupsBlock`
  // para onde `f.eixos` é lido agora.
  // =====================================================================
  function render(f) {
    app.appendChild(header(f));
    if (f.ficha) app.appendChild(fichaBlock(f.ficha));

    var veredito = veredictoBlock(f);
    if (veredito) app.appendChild(veredito);

    app.appendChild(detailDivider(f));
    app.appendChild(sentimentGroupsBlock(f));

    if (f.narrativa) app.appendChild(narrativaCollapsedBlock(f.narrativa));

    // micro-pesquisa (A/B) — módulo separado
    if (window.mountSurvey) window.mountSurvey(app, f);
  }

  // --- header ---
  function header(f) {
    var el = document.createElement("header");
    el.className = "film-header";

    // [v1.9.20, Entrega 2] "N reviews observadas" saiu — nenhuma contagem
    // de review no texto. O ano sozinho já cumpria o papel de metadado
    // rápido; sem contagem ao lado, o `<span class="dot">` (que separava
    // os dois) também sai.
    var ano = f.ficha && f.ficha.ano ? String(f.ficha.ano) : "";
    var meta = null;
    if (ano) {
      meta = document.createElement("p");
      meta.className = "film-header__meta";
      meta.textContent = ano;
    }

    var h1 = document.createElement("h1");
    h1.className = "film-header__title";
    h1.textContent = titleOf(f);

    if (meta) el.appendChild(meta);
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

  // --- narrativa completa (v1.9.19: COLAPSADA, no fim da página — Entrega 1) ---
  // A narrativa continua existindo e continua no produto — só deixa de ser a
  // primeira coisa. Fechada por padrão (`<details>` sem `open`), com um
  // controle claro pra expandir (`.disclosure`, mesmo padrão visual do
  // grupo-do-meio recolhido, ver `meioColapsadoBlock`).
  function narrativaCollapsedBlock(texto) {
    var det = document.createElement("details");
    det.className = "disclosure disclosure--narrativa";

    var sum = document.createElement("summary");
    sum.innerHTML =
      '<span class="disclosure__label">Ler a análise completa</span>' + chevronSvg();
    det.appendChild(sum);

    var body = document.createElement("div");
    body.className = "disclosure__body narrativa";
    texto.split(/\n{2,}/).forEach(function (par) {
      var p = par.trim();
      if (!p) return;
      var node = document.createElement("p");
      node.textContent = p;
      body.appendChild(node);
    });
    det.appendChild(body);
    return det;
  }

  function chevronSvg() {
    return '<span class="chevron" aria-hidden="true">' +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="m6 9 6 6 6-6"/></svg></span>';
  }

  // --- divisor EM DETALHE + disclaimer ---
  // v1.4.0: o disclaimer depende do dado disponível. Sem distribuição real,
  // avisa que os tamanhos NÃO são prevalência (regra v1.2.1). Com ela, o peso
  // real está exibido em cada grupo e o texto passa a explicar o método.
  // Mantidos em sincronia com render.py (DISCLAIMER_*).
  // [v1.9.20, Entrega 2] A cota ("40 · 40 · 40 reviews") saiu do texto —
  // decisão do dono do projeto, nenhuma contagem de review em texto. As
  // cotas continuam iguais entre os grupos (`f.buckets[i].alvo` no JSON,
  // intacto) — só deixaram de ser citadas em algarismo aqui.
  function detailDivider(f) {
    var temDistribuicao = !!f.distribuicao;
    var texto = temDistribuicao
      ? "Análise em profundidade igual por grupo; o peso real de cada "
        + "faixa está indicado em cada grupo."
      : "Os grupos são cotas de coleta — não a proporção real das opiniões.";
    var el = document.createElement("div");
    el.className = "detail-divider";
    el.innerHTML =
      '<div class="spectrum-line" aria-hidden="true"></div>' +
      '<p class="detail-divider__label">Em detalhe · tema a tema</p>' +
      '<p class="disclaimer">' + texto + "</p>";
    return el;
  }


  // =====================================================================
  // v1.9.19 — a tabela "EIXO A EIXO" SAI DA TELA (Entrega 5, decisão de
  // produto — feedback de uso: "não funciona na prática"). O que existia
  // em `eixosBlock`/`contrasteBox`/`gradeCabecalho`/`linhaEixo`/`celula`/
  // `denominadorNota` foi REMOVIDO daqui — não escondido atrás de um flag,
  // removido mesmo. O bloco `eixos` do JSON não muda em nada: continua
  // sendo calculado pelo mesmo código de sempre (`eixos.py`, zero LLM), e
  // passa a alimentar DUAS coisas que a view antiga não fazia:
  //   1. o VEREDITO (`veredito`, abaixo) — a leitura de UMA frase que a
  //      tabela de 3 colunas pedia ao leitor pra fazer de cabeça;
  //   2. a ORDEM dos temas dentro de cada grupo (`ordenarTemasPorEixo`,
  //      perto de `groupBlock`) — o tema cujo eixo é "só este grupo" sobe
  //      pro topo, porque é exatamente o que o veredito está apontando.
  // Se um dia a tabela precisar voltar, o dado que ela lia está intacto.
  // =====================================================================

  // --- VEREDITO (Entrega 2) — TEMPLATE sobre lift já computado. ZERO
  // chamada de LLM: é derivação, não geração. A regra: o eixo de maior
  // lift em cada bucket é o que aquele grupo tem de PRÓPRIO; o veredito
  // contrasta os dois extremos (negativas/positivas — o meio nunca é um
  // dos dois lados do contraste, só ganha menção quando é o grupo
  // DOMINANTE da recepção, Entrega 4).
  //
  // RESTRIÇÃO DE PRODUTO: nenhuma nota média/score/estrela agregada aqui —
  // só nomes de eixo e `share_real` (uma PROPORÇÃO, a mesma métrica que
  // "~90% das notas" já usa em todo o resto da tela, nunca um número-síntese
  // único do filme). E o veredito não afirma o que o dado não sustenta: um
  // bucket sem eixo acima da margem de contraste não empresta seu "melhor"
  // eixo pro veredito — cai no ramo "os grupos falam das mesmas coisas".
  // [v1.9.21] O veredito passa a ser GERADO NA PUBLICAÇÃO (§3[V]) e vem
  // pronto no JSON, em `f.veredito.texto`. O render aqui é render: não
  // decide nada, não calcula nada, não formata número nenhum — inclusive o
  // percentual do meio dominante já vem concatenado pelo código Python.
  //
  // `veredito()` abaixo NÃO foi deletada: ela é o FALLBACK DE RENDER para
  // JSON publicado antes desta versão (compatibilidade), e é a mesma lógica
  // que `veredito.veredito_template` reproduz em Python como rede do
  // estágio. As duas precisam concordar; se divergirem, o sintoma é um
  // filme antigo e um filme novo em `template_fallback` dizendo coisas
  // diferentes sobre dados equivalentes.
  //
  // A TELEMETRIA do bloco (`origem`, `modelo`, `flags`, `candidatos`) é
  // diagnóstico de produção e NÃO aparece na tela — mesma decisão já tomada
  // para `verificacao_narrativa` e `narrativa_selecao`.
  function veredictoBlock(f) {
    var pronto = f.veredito && f.veredito.texto;
    var texto = pronto ? f.veredito.texto : veredito(f);
    if (!texto) return null;
    var el = document.createElement("p");
    el.className = "verdict";
    el.textContent = texto;
    return el;
  }

  function veredito(f) {
    var e = f.eixos;
    if (!e || !e.linhas || !e.linhas.length) return null;
    var buckets = f.buckets || [];
    var margem = e.margem_lift_pp || 20;

    var dominante = bucketDominante(buckets);
    var meioDominante = !!(dominante && dominante.bucket === "medianas");

    var pos = eixoDeMaiorLift(e, "positivas", buckets);
    var neg = eixoDeMaiorLift(e, "negativas", buckets);
    var posOk = !!pos && pos.lift_pp >= margem;
    var negOk = !!neg && neg.lift_pp >= margem;

    var frase;
    if (posOk && negOk) {
      frase = "Quem recomenda destaca " + eixoEmFrase(pos.eixo) + "; quem não "
        + "recomenda aponta " + eixoEmFrase(neg.eixo) + ".";
    } else if (posOk || negOk) {
      // [v1.9.20, Entrega 1] Achado real em `anatomy-of-a-fall` (88%
      // positivas): "nenhum assunto se destaca" mentia por omissão — o lado
      // sem lift não estava mudo, estava falando de um tema MUITO citado
      // que também aparece nos outros grupos (então o CONTRASTE é baixo
      // mesmo com a FREQUÊNCIA alta). O leitor lia "os positivos não
      // elogiaram nada"; o dado dizia "elogiaram o que todo mundo cita".
      // Cai pro eixo de maior FREQUÊNCIA do lado sem lift — nunca fingindo
      // que é exclusivo (a redação distingue "aponta/destaca" de "fala
      // sobretudo de..."). [v1.9.21] O fecho dessa segunda oração era uma
      // frase FIXA que afirmava "todos"; ver a Entrega 6 logo abaixo.
      var comLift = posOk ? pos : neg;
      var ladoSemLift = posOk ? "negativas" : "positivas";
      var freqDoOutro = eixoDeMaiorFrequencia(e, ladoSemLift, buckets);
      var bucketSemLift = (buckets || []).filter(function (x) {
        return x.bucket === ladoSemLift;
      })[0] || {};
      var verbo = posOk ? "Quem recomenda destaca " : "Quem não recomenda aponta ";
      var verboOutro = ladoSemLift === "positivas"
        ? "quem recomenda fala sobretudo de "
        : "quem não recomenda fala sobretudo de ";

      // [v1.9.21, Entrega 6] BUG REAL, medido em produção e corrigido aqui.
      //
      // Este ramo terminava com a frase FIXA "— um assunto que todos os
      // grupos citam", disparada sempre que existisse qualquer eixo com
      // `mencoes > 0`, SEM checar se a frequência sustenta "todos":
      //   · `obsession-2026` afirmava isso a partir de 2 de 5 reviews (40%),
      //     num grupo que o próprio site rotula "modo reduzido";
      //   · `eighth-grade`, com amostra completa, a partir de 13 de 34 (38%).
      // É a mesma classe de inflação retórica que as v1.2.2/v1.2.3 já tinham
      // resolvido para a narrativa, reintroduzida num lugar novo.
      //
      // O quantificador agora vem do MESMO mapa determinístico do pipeline
      // (`src/espectro24/quantificador.py`, faixas da v1.2.3), e amostra
      // reduzida é caso à parte: cautela explícita, nunca generalização.
      if (!freqDoOutro) {
        frase = verbo + eixoEmFrase(comLift.eixo) + " — do outro lado, nenhum "
          + "assunto se destaca tanto assim.";
      } else if (amostraReduzida(bucketSemLift)) {
        frase = verbo + eixoEmFrase(comLift.eixo) + "; " + verboOutro
          + eixoEmFrase(freqDoOutro.eixo)
          + " — amostra pequena demais para dizer mais que isso.";
      } else {
        var rot = rotuloQuantificador(freqDoOutro.freqPct);
        frase = verbo + eixoEmFrase(comLift.eixo) + "; " + verboOutro
          + eixoEmFrase(freqDoOutro.eixo) + " — um assunto que " + rot
          + " naquele grupo também " + (PLURAL[rot] ? "mencionam" : "menciona")
          + ".";
      }
    } else {
      // `contraste: valorativo` (nenhum bucket acima da margem) cai aqui —
      // mas também qualquer `tematico` em que o contraste mora só no meio,
      // caso em que negativas/positivas de fato não têm nada de próprio.
      frase = "Os grupos falam das mesmas coisas — discordam sobre se elas "
        + "funcionam.";
    }

    // Entrega 4: quando o meio é o MAIOR grupo, a frase original mentiria
    // por omissão (descreveria o filme só pelos dois grupos minoritários).
    // A menção vem ANTES, como contexto que muda a leitura do resto.
    if (meioDominante && typeof dominante.share_real === "number") {
      frase = "O meio-termo é o maior grupo da recepção (~"
        + dominante.share_real + "% das notas). " + frase;
    }
    return frase;
  }

  // O grupo com maior `share_real` — usado tanto no veredito quanto na
  // decisão de promover o meio a destaque (Entrega 4). `null` sem
  // distribuição real (nenhum `share_real` no JSON).
  function bucketDominante(buckets) {
    var comShare = (buckets || []).filter(function (b) {
      return typeof b.share_real === "number";
    });
    if (!comShare.length) return null;
    return comShare.reduce(function (a, b) {
      return b.share_real > a.share_real ? b : a;
    });
  }

  // O eixo de maior lift de UM bucket — "o que aquele grupo tem de
  // próprio". `null` quando o bucket não sustenta nada: piso `sem_analise`
  // (não há análise temática pra esse grupo, então não há lift confiável
  // pra citar) ou nenhum eixo mencionado.
  function eixoDeMaiorLift(e, bucket, buckets) {
    var b = (buckets || []).filter(function (x) { return x.bucket === bucket; })[0];
    if (b && b.estado_piso === "sem_analise") return null;
    var candidatos = (e.linhas || []).filter(function (l) {
      var d = (l.por_bucket || {})[bucket];
      return d && d.mencoes > 0 && typeof d.lift_pp === "number";
    });
    if (!candidatos.length) return null;
    var melhor = candidatos.reduce(function (a, l) {
      return l.por_bucket[bucket].lift_pp > a.por_bucket[bucket].lift_pp ? l : a;
    });
    return { eixo: melhor.eixo, lift_pp: melhor.por_bucket[bucket].lift_pp };
  }

  // [v1.9.20] O eixo de maior FREQUÊNCIA de um bucket — "do que aquele
  // grupo mais fala", sem exigir que seja EXCLUSIVO dele (ao contrário de
  // `eixoDeMaiorLift`, aqui um lift negativo não desqualifica: o tema pode
  // ser ainda mais comum nos outros grupos e mesmo assim ser o que este
  // grupo mais cita). Mesma guarda de piso `sem_analise` que `eixoDeMaiorLift`.
  function eixoDeMaiorFrequencia(e, bucket, buckets) {
    var b = (buckets || []).filter(function (x) { return x.bucket === bucket; })[0];
    if (b && b.estado_piso === "sem_analise") return null;
    var candidatos = (e.linhas || []).filter(function (l) {
      var d = (l.por_bucket || {})[bucket];
      return d && d.mencoes > 0 && d.de_n > 0;
    });
    if (!candidatos.length) return null;
    var melhor = candidatos.reduce(function (a, l) {
      var da = a.por_bucket[bucket], dl = l.por_bucket[bucket];
      return (dl.mencoes / dl.de_n) > (da.mencoes / da.de_n) ? l : a;
    });
    var d = melhor.por_bucket[bucket];
    // [v1.9.21] A FREQUÊNCIA volta junto com o eixo — sem ela, quem chama
    // não tem como escolher o quantificador honesto, que foi exatamente o
    // buraco por onde entrou o "todos os grupos citam" a partir de 38%.
    return { eixo: melhor.eixo, freqPct: Math.round(100 * d.mencoes / d.de_n) };
  }

  // [v1.9.21] O mapa fração→palavra da v1.2.3, PORTADO de
  // `src/espectro24/quantificador.py`. Duplicação ENTRE LINGUAGENS, que
  // nenhuma extração resolve: o Python é a autoridade e é onde vive o
  // racional; esta cópia existe só para o fallback de render de JSON
  // publicado antes da v1.9.21. Ordem do mais FRACO ao mais FORTE, primeiro
  // match vence — é isso que resolve toda fronteira compartilhada para o
  // rótulo mais fraco ("50%" vira "muitos", não "a maioria").
  var BANDAS_QUANTIFICADOR = [
    ["poucos", 0, 10, false], ["alguns", 10, 25, true],
    ["muitos", 25, 50, true], ["cerca de metade", 40, 60, true],
    ["a maioria", 50, 80, true], ["quase todos", 80, 100, true],
  ];
  var PLURAL = { "poucos": 1, "alguns": 1, "muitos": 1, "quase todos": 1 };

  function rotuloQuantificador(pct) {
    pct = Math.max(0, Math.min(100, pct));
    for (var i = 0; i < BANDAS_QUANTIFICADOR.length; i++) {
      var b = BANDAS_QUANTIFICADOR[i];
      if (pct < b[1]) continue;
      if (b[3] ? pct <= b[2] : pct < b[2]) return b[0];
    }
    return "quase todos";
  }

  // Amostra pequena: o site já rotula esses grupos como degradados na tela;
  // um veredito que generalize a partir deles contradiria o próprio aviso
  // que aparece dois blocos abaixo.
  function amostraReduzida(b) {
    return !!b && (b.modo === "reduzido" || (b.estado_piso
      && b.estado_piso !== "completa"));
  }

  // Rótulo do eixo em minúscula, pra encaixar em "destaca <eixo>" — os
  // valores de `EIXO_LABEL` são pensados pra cabeçalho (inicial maiúscula).
  function eixoEmFrase(id) {
    var label = EIXO_LABEL[id] || id;
    return label.charAt(0).toLowerCase() + label.slice(1);
  }

  // =====================================================================
  // BULLETS AGRUPADOS POR SENTIMENTO (Entrega 3) + O MEIO REBAIXADO
  // (Entrega 4, decisão do dono do projeto).
  //
  // Formato: dois blocos em destaque, negativas e positivas, MESMO leiaute
  // entre os dois (a neutralidade de TRATAMENTO do §0 da SPEC continua
  // valendo AQUI — é só o meio que sai do meio-a-meio). O grupo medianas
  // vira uma linha discreta e colapsada abaixo dos dois, com controle pra
  // expandir — ele é minoritário em 33 dos 35 filmes do catálogo, e o
  // feedback de uso apontou que em destaque ele "polui sem informar".
  //
  // EXCEÇÃO AUTOMÁTICA, e é o que impede a decisão virar distorção: quando
  // medianas é o grupo DOMINANTE (maior `share_real` dos três — 45% em
  // `napoleon-2023`, 41% em `friday-the-13th-2009`), ele sobe pro destaque
  // junto dos outros dois. Descrever esses dois filmes só pelos grupos que,
  // somados, são METADE da recepção seria mentir sobre a distribuição —
  // exatamente o defeito que o §0 (neutralidade de tratamento) existe pra
  // evitar. Isto quebra a promessa de "três grupos, formato idêntico"
  // DELIBERADAMENTE; a razão está registrada em SPEC.md §0.
  // =====================================================================
  function sentimentGroupsBlock(f) {
    var porNome = {};
    (f.buckets || []).forEach(function (b) { porNome[b.bucket] = b; });
    var dominante = bucketDominante(f.buckets || []);
    var meioDominante = !!(dominante && dominante.bucket === "medianas");

    var wrap = document.createElement("div");
    wrap.className = "sentiment-wrap";

    var destaque = document.createElement("div");
    destaque.className = "sentiment-groups"
      + (meioDominante ? " sentiment-groups--3" : " sentiment-groups--2");
    var ordem = meioDominante
      ? ["negativas", "medianas", "positivas"]
      : ["negativas", "positivas"];
    ordem.forEach(function (nome) {
      if (porNome[nome]) destaque.appendChild(groupBlock(porNome[nome], f));
    });
    wrap.appendChild(destaque);

    if (!meioDominante && porNome.medianas) {
      wrap.appendChild(meioColapsadoBlock(porNome.medianas, f));
    }
    return wrap;
  }

  function meioColapsadoBlock(b, f) {
    var det = document.createElement("details");
    det.className = "disclosure disclosure--meio";

    var rotuloPct = typeof b.share_real === "number"
      ? "~" + b.share_real + "% ficaram no meio-termo"
      : "uma parte ficou no meio-termo";
    var sum = document.createElement("summary");
    sum.innerHTML = '<span class="disclosure__label">' + esc(rotuloPct)
      + "</span>" + chevronSvg();
    det.appendChild(sum);

    var body = document.createElement("div");
    body.className = "disclosure__body";
    body.appendChild(groupBlock(b, f));
    det.appendChild(body);
    return det;
  }

  // O bloco `eixos` alimenta a ORDEM dos temas dentro do grupo (Entrega 5):
  // o tema cujo eixo tem papel de bullet "não-frequência" (contraste ou
  // frequência+contraste) sobe pro topo — é o mesmo eixo que o veredito, lá
  // em cima, está apontando como o que aquele grupo tem de próprio.
  function papelPorTema(e, bucket) {
    var mapa = {};
    if (!e) return mapa;
    (e.linhas || []).forEach(function (l) {
      var d = (l.por_bucket || {})[bucket];
      if (d && d.tema) mapa[d.tema] = (l.bullet_de || {})[bucket] || null;
    });
    return mapa;
  }
  function ordenarTemasPorEixo(temas, papelMap) {
    return temas
      .map(function (t, i) { return { t: t, i: i }; })
      .sort(function (a, b) {
        var pa = papelMap[a.t.tema], pb = papelMap[b.t.tema];
        var wa = pa && pa !== "frequencia" ? 0 : 1;
        var wb = pb && pb !== "frequencia" ? 0 : 1;
        return wa !== wb ? wa - wb : a.i - b.i;   // estável no empate
      })
      .map(function (x) { return x.t; });
  }

  // --- grupo ---
  function groupBlock(b, f) {
    var meta = GRUPO_META[b.bucket] || { label: b.bucket, color: "var(--text)" };
    var el = document.createElement("section");
    el.className = "group" + (TINT ? " is-tinted" : "");
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
    head.appendChild(dot);
    head.appendChild(name);
    head.appendChild(stars);
    // v1.4.0: share real do grupo — mono, discreto, MESMO estilo e MESMO
    // formato nos três (neutralidade de TRATAMENTO; a assimetria vem do
    // dado). Omitido por completo quando o filme não tem distribuição.
    // [v1.9.20, Entrega 2] É o ÚNICO número que fica no header — "N de M
    // analisadas" saiu (decisão do dono do projeto: nenhuma contagem de
    // review em texto). O percentual de peso continua porque é a única
    // forma que o produto tem de dizer qual grupo domina a recepção.
    if (typeof b.share_real === "number") {
      var share = document.createElement("span");
      share.className = "group__share";
      share.textContent = "~" + b.share_real + "% das notas";
      head.appendChild(share);
    }
    el.appendChild(head);

    // v1.9.14 (Entrega 6): a JANELA da amostra vem logo abaixo do header —
    // até a v1.9.19 vinha colada ao denominador ("40 de 40 analisadas"),
    // que saiu na v1.9.20; a janela continua tendo linha própria, nunca ao
    // lado do "~X% das notas". O peso vem do histograma de NOTAS, que
    // acumula desde 2012; carimbar nele uma janela de semanas diria que as
    // notas todas são recentes. São duas populações, e a linha separada é
    // o que impede a leitura errada.
    var janela = janelaTexto(b.janela_amostra);
    if (janela) {
      var jl = document.createElement("p");
      jl.className = "group__janela";
      jl.textContent = janela;
      el.appendChild(jl);
    }

    // avisos de modo degradado — SEMPRE visíveis. [v1.9.20, Entrega 3] Sem
    // a contagem no bullet, um grupo de amostra pequena não pode mais
    // apoiar essa cautela num número visível na barra — o aviso é onde ela
    // mora agora, e por isso continua sem nenhum algarismo de review
    // (`n_validas`/`alvo` seguem no JSON, só não em texto).
    if (b.modo === "reduzido") {
      el.appendChild(warnBox(
        "Modo reduzido: amostra pequena para este grupo. "
        + "Interprete com cautela."));
    }
    if (b.modo === "sem_analise") {
      var w = warnBox("Sem análise temática: amostra insuficiente neste grupo.");
      var link = document.createElement("a");
      link.className = "sem-analise-link";
      link.href = f.reviews_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.innerHTML = "→ reviews disponíveis no Letterboxd&nbsp;↗";
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

    // temas — ordenados pelo papel de bullet do eixo (ver `ordenarTemasPorEixo`)
    if (b.temas && b.temas.length) {
      var themes = document.createElement("div");
      themes.className = "themes";
      var ordenados = ordenarTemasPorEixo(b.temas, papelPorTema(f.eixos, b.bucket));
      ordenados.forEach(function (t, i) {
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

    // [v1.9.20, Entrega 2] Decisão do dono do projeto: nenhum algarismo de
    // contagem de review no TEXTO — a BARRA (abaixo) continua proporcional
    // e é quem comunica visualmente o peso do tema; o "~X de N" ao lado do
    // nome saiu. O `aria-label` da barra mantém o número (não é texto
    // visível, é a alternativa textual da barra pra leitor de tela — sem
    // ele a barra vira um `role="img"` mudo).
    var top = document.createElement("div");
    top.className = "theme__top";
    var nm = document.createElement("span");
    nm.className = "theme__name";
    nm.textContent = t.tema;
    top.appendChild(nm);
    row.appendChild(top);

    var bar = document.createElement("div");
    bar.className = "theme__bar";
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", "Mencionado em cerca de " + x + " de " + n + " reviews");
    var fill = document.createElement("span");
    fill.style.width = pct.toFixed(1) + "%";           // largura = X/N
    bar.appendChild(fill);
    row.appendChild(bar);

    // exemplo parafraseado expansível — [Entrega 6, v1.9.19] o "+" parecia
    // rótulo estático (achado de uso: ninguém percebia que era clicável).
    // Chevron no padrão de ícone do resto do site (mesmo stroke/round-cap
    // do back-link e da narrativa colapsada), dentro de um pill na cor do
    // grupo com opacidade baixa (`--neg-soft`/`--med-soft`/`--pos-soft`,
    // já usadas — nenhuma cor nova) em vez de texto solto.
    if (t.exemplo_parafraseado) {
      var id = "ex-" + bucket + "-" + idx;
      var btn = document.createElement("button");
      btn.className = "theme__toggle";
      btn.type = "button";
      btn.setAttribute("aria-expanded", "false");
      btn.setAttribute("aria-controls", id);
      btn.innerHTML = '<span class="theme__toggle-label">Exemplo parafraseado</span>' + chevronSvg();

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
})();
