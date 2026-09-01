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

  // =====================================================================
  // [v1.9.26, Entrega 3] O NOME DE EXIBIÇÃO DOS TRÊS GRUPOS — decisão de
  // produto do dono do projeto (conexão geracional / campanha). Registrada
  // em SPEC.md §0 como EXCEÇÃO DE VOCABULÁRIO DE RÓTULO, com o trade-off
  // escrito por extenso: "Fans/Haters" não é um par simétrico ("hater"
  // imputa má-fé, "fã" não), e §0 pede neutralidade de TRATAMENTO.
  //
  // O ESCOPO da exceção, e é ele que a torna aceitável: ela vale só onde o
  // nome do grupo aparece ISOLADO, como rótulo que identifica a coluna —
  // cabeçalho do bloco de bullets, legenda e alternativa textual da barra
  // de proporção, `aria-label` que diz de qual grupo é um elemento. A
  // PROSA do produto (veredito, narrativa, o prefixo do meio dominante
  // gerado em Python, os avisos curtos de piso, o disclaimer da cota)
  // continua neutra, e a neutralidade ESTRUTURAL do §0 continua INTEGRAL:
  // cota 40/40/40, mesma margem de lift dos dois lados, mesmo leiaute e
  // mesma quantidade de bullets entre negativas e positivas.
  //
  // AS CHAVES INTERNAS NÃO MUDAM. `negativas`/`medianas`/`positivas`
  // seguem sendo o vocabulário do JSON, do briefing, dos prompts, dos
  // validadores, da spec e dos testes — nada em `resultado/` foi tocado,
  // nenhum filme foi regerado. Este mapa é a ÚNICA fronteira entre a
  // chave e o nome na tela.
  //
  // REVERSÃO = ESTA LINHA. É de propósito: a mudança vai ser testada em
  // público, e se o ganho não se confirmar o custo de voltar é uma edição
  // de uma linha, não uma varredura. Para reverter:
  //   { negativas: "Negativas", medianas: "Medianas", positivas: "Positivas" }
  //
  // ANOTADO, NÃO IMPLEMENTADO: "MID" é mais idiomático que "MIXED" em
  // português brasileiro, e era o termo da versão originalmente arquivada.
  var GRUPO_LABEL = { negativas: "HATERS", medianas: "MIXED", positivas: "FANS" };

  var GRUPO_META = {
    negativas: { label: GRUPO_LABEL.negativas, color: "var(--neg)", cap: "quem não gostou" },
    medianas:  { label: GRUPO_LABEL.medianas,  color: "var(--med)", cap: "quem ficou no meio" },
    positivas: { label: GRUPO_LABEL.positivas, color: "var(--pos)", cap: "quem gostou" },
  };

  // Ordem de leitura dos três grupos — a mesma do resto do site (quem não
  // gostou primeiro, quem gostou por último) e a mesma da faixa do mosaico
  // da home (`GRUPOS` em home.js).
  var GRUPOS_ORDEM = ["negativas", "medianas", "positivas"];

  // O rótulo de exibição de um grupo. Toda a tela passa por aqui — é o
  // ponto único do rename (ver `GRUPO_LABEL`). Chave desconhecida cai na
  // própria chave, mesma política de lista fechada de `EIXO_LABEL`.
  function rotuloDoGrupo(bucket) {
    return GRUPO_LABEL[bucket] || bucket;
  }

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
  //
  // ---------------------------------------------------------------------
  // [v1.9.26, Entrega 1] REORDENAÇÃO — a BARRA assume o topo, o VEREDITO
  // desce para o rodapé da análise.
  //
  // O que mudou de lugar e por quê: o topo da página passa a ser ocupado
  // pelo sinal DIMENSIONAL da recepção (a barra de proporção, Entrega 2)
  // em vez do sinal VERBAL (o veredito). A barra responde "quanta gente,
  // de cada lado" de relance e sem leitura; o veredito responde "sobre o
  // quê eles discordam", que é uma conclusão — e conclusão lida ANTES da
  // evidência é asserção, lida DEPOIS é fecho. Ele desce para depois dos
  // bullets, intacto: mesmo texto, mesma origem, mesma geração. Nada de
  // §3[V] foi tocado — nem `veredito.py`, nem o briefing, nem o prompt.
  //
  // O cabeçalho "EM DETALHE · TEMA A TEMA" sai (a página não tem mais uma
  // seção "resumo" antes dele — os bullets vêm direto), e o divisor fica
  // sendo só a linha arco-íris. O disclaimer da cota migra para baixo da
  // barra, onde a informação que ele carrega ("profundidade igual ≠ peso
  // igual") fica ancorada no objeto que mostra o peso — ver
  // `proporcaoBlock`.
  //
  // A LÓGICA DO MEIO REBAIXADO (§0, exceção da v1.9.19) NÃO É AFETADA por
  // nada disto: quem decide se `medianas` sobe ao destaque é
  // `sentimentGroupsBlock`, lendo `bucketDominante(f.buckets)` — uma
  // função do DADO, não da posição do bloco na página. `veredictoBlock`
  // não lê nem escreve esse estado (o prefixo do meio dominante já vem
  // concatenado do Python dentro de `f.veredito.texto`). Mover a chamada
  // de `veredictoBlock` de antes para depois de `sentimentGroupsBlock`
  // não passa informação nenhuma entre as duas.
  // ---------------------------------------------------------------------
  function render(f) {
    app.appendChild(header(f));                       // 1 ano+título, 2 chip
    app.appendChild(fichaBlock(f.ficha || {}, f.reviews_url)); // 3 metadados
    app.appendChild(proporcaoBlock(f));               // 4 barra + nota da cota
    app.appendChild(detailDivider());                 // 5 linha arco-íris
    app.appendChild(sentimentGroupsBlock(f));         // 6 bullets por grupo

    var veredito = veredictoBlock(f);                 // 7 veredito (movido)
    if (veredito) app.appendChild(veredito);

    if (f.narrativa) app.appendChild(narrativaCollapsedBlock(f.narrativa)); // 8

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

    // [v1.9.30] O BACKDROP abre a página do filme, no lugar que o pôster
    // vertical ocupava desde a v1.9.29. DECISÃO DO DONO DO PROJETO: o
    // pôster ocupa espaço vertical demais no topo, e um quadro 16:9 lê na
    // horizontal, deixa a barra mais perto da primeira tela e dá uma
    // abertura editorial em vez de uma capa de catálogo.
    //
    // ISTO É EXCEÇÃO EXPLÍCITA AO PRINCÍPIO ANTI-SPOILER DO §0. O TMDB não
    // garante que um backdrop seja livre de spoiler — é quadro do filme, e
    // pode ser do terceiro ato — e ele fica na posição MAIS PROEMINENTE da
    // página, antes até da sinopse. O produto anuncia "0 spoilers" na home
    // e resolve todo trade-off contra o spoiler em todo o resto (bullets
    // filtrados, veredito proibido de citar reviravolta); aqui, e só aqui,
    // essa promessa deixa de valer. Foi decidido com o trade-off na mesa,
    // não por descuido, e o registro por extenso está em SPEC §3[E], "O
    // BACKDROP no topo da página do filme". Não há como escrever isso sem
    // tensão, e o comentário não tenta.
    //
    // O PÔSTER CONTINUA NA HOME. Esta troca é só da página do filme.
    //
    // FALLBACK, em dois degraus: filme sem backdrop usa o pôster que já
    // estava aqui (contido, 200px — nada muda para ele); filme sem os dois
    // cai no estado de ausência já desenhado, que é o que `montar` faz
    // sozinho. Medido no catálogo: 34 dos 35 têm backdrop; o único sem é
    // `talk-to-me-2022`.
    //
    // ORDEM PRESERVADA. A imagem entra ACIMA do par ano → título, exatamente
    // onde o pôster entrava (§3[E], item 1 da ordem publicada), e o par
    // segue como está. A BARRA não é tocada — nem posição, nem geometria,
    // nem animação de entrada (§3[E], v1.9.28).
    // [v1.9.32] O BACKDROP DEIXA DE SER BLOCO FECHADO e passa a se DISSOLVER
    // no fundo, com o par ano → título começando PARCIALMENTE SOBRE a
    // imagem, dentro do fade, e terminando no fundo escuro. A transição
    // entre obra visual e conteúdo editorial vira contínua, não um corte.
    //
    // A ESTRUTURA que isso exige: um contêiner `.film-hero` com a imagem e
    // um bloco de texto que SOBE por cima dela (margem negativa). O texto
    // precisa ser irmão da imagem e vir DEPOIS dela — daí o wrapper, que é a
    // única mudança de árvore aqui. A ordem publicada (§3[E]) não muda: a
    // imagem continua acima do par ano → título.
    //
    // O CONTRASTE É GARANTIDO POR CONSTRUÇÃO, não por sorte com a imagem —
    // ver `.backdrop::after` em styles.css. O fade termina numa FAIXA
    // 100% OPACA na cor do fundo da página, e o recuo do texto é
    // exatamente a altura dessa faixa (`--hero-overlap`): o texto nunca
    // pousa em cima de pixel de imagem, só sobre fundo já chapado. É o
    // mesmo princípio do degradê da célula do mosaico (v1.9.29, título
    // sobre pôster claro), com a diferença de que lá a base é preta e aqui
    // é `--bg`, porque aqui o degradê tem de casar com a página.
    var hero = document.createElement("div");
    hero.className = "film-hero";

    if (window.ESPECTRO_POSTER && f.ficha) {
      var abertura = window.ESPECTRO_POSTER.montarBackdrop(f.ficha, {
        titulo: titleOf(f), ano: ano,
      });
      // FALLBACK sem backdrop: o pôster contido volta, e com ele a
      // composição ANTIGA — pôster fechado, texto INTEIRAMENTE abaixo dele.
      // A sobreposição é do backdrop, não do pôster: um pôster 2:3 de 200px
      // não tem faixa inferior larga onde um título de 3,6rem caiba, e
      // deixar o título subir por cima dele cobriria o rosto do cartaz.
      // `.film-hero--poster` é o que desliga o recuo negativo.
      if (!abertura) {
        hero.classList.add("film-hero--poster");
        abertura = window.ESPECTRO_POSTER.montar(f.ficha, {
          uso: "ficha", titulo: titleOf(f), ano: ano, lazy: false,
        });
      }
      hero.appendChild(abertura);
    }

    var texto = document.createElement("div");
    texto.className = "film-hero__text";
    if (meta) texto.appendChild(meta);
    texto.appendChild(h1);
    hero.appendChild(texto);
    el.appendChild(hero);

    return el;
  }

  // --- ficha (dado novo v1.3.0) ---
  //
  // [v1.9.32] A SINOPSE SAIU, e o card que a continha saiu com ela.
  // DECISÃO FINAL do dono do projeto. Não é ocultar nem colapsar: o bloco
  // não existe mais na página. O que sobrevive é a LINHA DE METADADOS,
  // agora solta — sem fundo, sem borda, sem padding de card.
  //
  // A CONSEQUÊNCIA PREVISTA, registrada aqui e em SPEC §3[E] porque é ela
  // que a decisão custa: o público-alvo é quem AINDA NÃO ASSISTIU, e a
  // sinopse era o único elemento da página que dizia DO QUE O FILME TRATA.
  // Sem ela os bullets chegam sem premissa onde se apoiar — "o ritmo
  // arrasta" pressupõe saber o que arrasta. O custo é baixo nos 35 de hoje
  // (filmes conhecidos, backdrop expressivo) e CRESCENTE na expansão, com
  // filmes obscuros e estrangeiros em que ninguém traz contexto de casa.
  //
  // A ATRIBUIÇÃO AO TMDB NÃO É AFETADA e continua obrigatória: esta linha
  // (diretor, gêneros, duração) vem toda do TMDB, e por isso o "fonte
  // TMDB" continua nela, junto do aviso no rodapé de todas as páginas e da
  // página de créditos (§3[E], "ATRIBUIÇÃO AO TMDB"). Tirar a sinopse
  // reduz o que se usa da API; não reduz em nada o que se deve a ela.
  function fichaBlock(ficha, reviewsUrl) {
    var el = document.createElement("section");
    el.className = "ficha";
    el.setAttribute("aria-label", "Ficha técnica do filme");

    // O DIRETOR EM CAIXA ALTA E SEM O PREFIXO "dir." — o esboço do dono
    // abre a linha pelo nome, e o prefixo era uma muleta que só existia
    // porque o nome vinha em caixa normal no meio de outros dados. A caixa
    // alta é do CSS (`.ficha__dir`), NUNCA do dado: `toUpperCase()` em JS
    // quebraria a busca por texto e o que o leitor de tela anuncia.
    var parts = [];
    if (ficha.generos && ficha.generos.length) parts.push(ficha.generos.join(", "));
    if (ficha.duracao_min) parts.push(ficha.duracao_min + " min");
    // "fonte TMDB" só quando há dado do TMDB na linha. Num filme sem ficha
    // (`teste-degradado`, e qualquer filme cuja busca falhe — §3[F], a
    // ficha é aditiva e a ausência é estado válido) a linha inteira não
    // existe, e creditar uma fonte da qual não veio nada seria falso.
    var temTmdb = !!(ficha.diretor || parts.length);
    if (temTmdb) parts.push("fonte TMDB");

    // [v1.9.26] A linha de metadados é SANS, caixa normal — decisão FINAL
    // do dono do projeto, depois de comparar com a variante "Inter"
    // auto-hospedada. O pedido original era "a fonte que a Apple usa": a
    // pilha de sistema (`--sans-ui`) entrega a San Francisco de verdade em
    // Mac e iPhone porque usa a fonte JÁ INSTALADA no aparelho — o motivo
    // de a SF Pro não poder ser embutida está em `fonts/LEIA-ME.md`.
    //
    // [v1.9.32] Essa decisão CONTINUA VALENDO para gêneros, duração e
    // fonte. A caixa alta nova é só do NOME DO DIRETOR, que abre a linha —
    // não é uma volta ao mono-caixa-alta que a v1.9.26 removeu.
    if (temTmdb) {
      var line = document.createElement("p");
      line.className = "ficha__line";
      var html = "";
      if (ficha.diretor) {
        html += '<span class="ficha__dir">' + esc(ficha.diretor) + "</span>";
        if (parts.length) html += '<span class="dot">·</span>';
      }
      html += parts.map(esc).join('<span class="dot">·</span>');
      line.innerHTML = html;
      el.appendChild(line);
    }

    // [v1.9.32] O AVISO DE SINOPSE EM INGLÊS SAI JUNTO COM A SINOPSE. Ele
    // existia para não deixar o leitor achar que estava lendo pt-BR quando
    // não estava (§3[F], fallback de sinopse); sem sinopse na tela, ele
    // passaria a avisar sobre um texto que não está mais ali. O campo
    // `sinopse_fallback_en` continua no JSON, intocado, e volta a ter uso
    // no dia em que a sinopse voltar.

    // [v1.9.32] O LINK PARA O LETTERBOXD desce do topo para cá e DEIXA DE
    // SER PILL: mono pequena, sem caixa, sem borda, sem fundo — a mesma
    // direção do disclosure APROFUNDAR na v1.9.26 (parte do bloco
    // editorial, não componente externo pousado nele).
    //
    // O QUE NÃO MUDA, porque é semântica e não estilo: continua `<a>` de
    // verdade, com `target="_blank"` + `rel="noopener noreferrer"`, foco
    // visível (`:focus-visible` em styles.css) e área de toque confortável
    // no mobile — o padding vertical existe para isso, mesmo sem caixa
    // desenhada.
    //
    // O TEXTO CONTINUA "reviews no Letterboxd", e não só "letterboxd": é o
    // nome acessível do link, e o que ele promete é a LISTA DE REVIEWS
    // daquele filme, não a home do site. Trocar seria a única perda de
    // informação de uma entrega que só pedia tratamento visual.
    if (reviewsUrl) {
      var link = document.createElement("a");
      link.className = "reviews-link";
      link.href = reviewsUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.innerHTML = "reviews no Letterboxd&nbsp;↗";
      el.appendChild(link);
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

  // =====================================================================
  // [v1.9.26] BARRA DE PROPORÇÃO — o sinal do topo, decisão FINAL do dono
  // do projeto depois de duas rodadas de comparação. A primeira propôs
  // três variantes com respiro escuro entre as faixas ("sólida", "sóbria",
  // "angular"); o veredito sobre a mais forte delas ("sólida"): "tem umas
  // coisas interessantes, mas não dá ideia de continuidade — parece que
  // são três barras separadas, cortadas com vão no meio". O diagnóstico é
  // conceitual, não de ajuste: a recepção de um filme é UMA população
  // particionada em três, não três medições independentes — um vão entre
  // as faixas desenha três objetos onde o dado tem um só. A segunda rodada
  // propôs duas variantes CONTÍNUAS (esta, "contínua", e "divergente", um
  // diverging stacked bar); a escolhida foi a contínua.
  //
  // A BARRA TEM ZERO gap, ZERO fio separador, ZERO respiro escuro.
  //
  //  · A FONTE DO NÚMERO é `b.share_real`, a MESMA que os cabeçalhos de
  //    grupo imprimem ("~75% das notas"). Ler duas fontes para o mesmo
  //    fato é como se cria divergência silenciosa.
  //  · PROPORÇÃO EXATA. Sem vão, não há espaço livre a distribuir: as
  //    larguras são percentuais que somam exatamente 100 (a normalização
  //    pela soma continua necessária porque os três `share_real` são
  //    inteiros ARREDONDADOS e somam 99–101 no catálogo).
  //  · SEM NÚMERO DENTRO DA BARRA — os percentuais continuam nos
  //    cabeçalhos de grupo, um lugar só.
  //  · Paleta OFICIAL (laranja negativo, dourado meio, azul positivo).
  //    Nada de verde/vermelho: semáforo codifica certo/errado, e o produto
  //    se recusa a julgar os grupos.
  //  · `role="img"` + `aria-label` completo. Mesma decisão da v1.9.20
  //    (item 2): o `aria-label` não é texto visível, é a alternativa da
  //    barra para leitor de tela, e PERCENTUAL de peso é número permitido
  //    (o que saiu do produto foi contagem BRUTA de review).
  //
  // A legenda visível NÃO é `aria-hidden`: esconder texto visível de quem
  // usa leitor de tela troca um problema por outro. A redundância com o
  // `aria-label` é conhecida e aceita.
  // =====================================================================
  function proporcaoBlock(f) {
    var el = document.createElement("section");
    el.className = "proportion";

    // [v1.9.32] RECEPÇÃO — a barra passa a ser o primeiro grande bloco
    // NOMEADO da página. O rótulo entra ACIMA da barra; a barra em si não
    // é tocada (geometria, ordem, callout e animação de entrada da v1.9.28
    // ficam exatamente como estão).
    el.appendChild(sectionLabel("RECEPÇÃO"));

    var fatias = fatiasDeProporcao(f);
    if (fatias) {
      el.appendChild(barraContinua(fatias));
      el.appendChild(calloutDePercentual(fatias));
      el.appendChild(legendaDaBarra(fatias));
    } else {
      // [v1.9.27, Entrega 1] SEM distribuição real não há barra — e aí a
      // nota da cota volta INTEIRA, no texto da v1.2.1. Só o ramo COM
      // barra perdeu a frase; este é preservado sem uma vírgula de
      // diferença (ver `notaDaCota`).
      el.appendChild(notaDaCota());
    }
    return el;
  }

  // ---------------------------------------------------------------------
  // A barra: uma faixa só, fronteira em DIAGONAL.
  //
  // A COMPOSIÇÃO, e por que ela é em CAMADAS e não em fatias lado a lado:
  // fatias lado a lado com aresta diagonal deixariam um triângulo vazio em
  // cada fronteira — exatamente o vão que esta variante existe para
  // eliminar. Então as três cores são desenhadas como camadas EMPILHADAS,
  // cada uma começando na borda esquerda da barra e terminando na sua
  // fronteira, com a de baixo (positivas) preenchendo a barra inteira:
  //
  //   z3  negativas  0 ──▶ B1 (aresta direita diagonal)
  //   z2  medianas   0 ──▶ B2 (aresta direita diagonal)
  //   z1  positivas  0 ──▶ 100%  (sem recorte; é o fundo)
  //
  // Assim não existe superfície descoberta em lugar nenhum: cada fronteira
  // é literalmente uma cor TERMINANDO em cima da outra, que é a descrição
  // do efeito pedido. O `clip-path` de cada camada recortada leva a aresta
  // direita de `B + D/2` no topo a `B − D/2` na base, ou seja, a diagonal
  // fica CENTRADA na fronteira verdadeira — a meia altura da barra, o
  // limite está exatamente em B. É isso que preserva a proporção: a
  // diagonal empresta área de um lado e devolve do outro.
  //
  // O ÂNGULO É ADAPTATIVO, e essa é a parte que resolve o risco real.
  // `the-godfather` tem 2% em negativas — 14,4px em desktop e 6,7px a
  // 375px. Uma diagonal de ângulo fixo e generoso comeria a fatia inteira
  // na base e a faria sumir.
  //
  // ONDE O CÁLCULO MORA, e por que não em JS: a diagonal depende da MENOR
  // FATIA em pixels, que é (percentual da menor fatia) × (largura da
  // barra). O primeiro fator é DADO — sai do JSON e nunca muda. O segundo
  // é LAYOUT — muda a cada resize. Então o JS grava só o que é dado
  // (`--menor-pct`, um número sem unidade) e o CSS faz a conversão para
  // pixel com `cqw` (1cqw = 1% da largura do contêiner):
  //
  //     --diag: clamp(3px, calc(var(--menor-pct) * 0.55 * 1cqw), 12px)
  //
  // Assim a diagonal acompanha resize SOZINHA, sem `ResizeObserver`, sem
  // ouvinte de `resize` e sem um único recálculo em JS. A primeira versão
  // desta entrega usava `ResizeObserver`; foi trocada porque media em JS
  // uma coisa que o CSS já sabe — e porque um observador que não dispara
  // (documento oculto, por exemplo) deixaria a barra com o ângulo errado
  // sem nenhum sintoma visível.
  //
  // O fator 0,55 garante que a fatia mais estreita mantenha ~72% da sua
  // largura no ponto mais fino: ela perde D/2 de um lado, e D/2 = 0,275 ×
  // a própria largura. O teto de 12px impede que um filme sem fatia
  // estreita ganhe uma diagonal exagerada; o piso de 3px impede que ela
  // desapareça quando a menor fatia é minúscula.
  //
  // ---------------------------------------------------------------------
  // [v1.9.28] A ANIMAÇÃO DE ENTRADA: AS FRONTEIRAS DESLIZAM. O modelo
  // anterior (bloco neutro crescendo de 0 a 100%, cores nascendo por cima)
  // SAIU inteiro, e com ele a camada de prefill. A barra agora **nasce
  // completa**, particionada em TRÊS PARTES IGUAIS, e as fronteiras
  // deslizam até a distribuição real.
  //
  //   x1: 33,333%  ──▶  h            x2: 66,667%  ──▶  h + m
  //
  // O QUE O JS GRAVA, e é só isto: por camada, `--neutro` (a fronteira do
  // estado de terços) e `--fim` (a fronteira real), os dois em percentual
  // sem unidade. A INTERPOLAÇÃO INTEIRA mora no CSS, num único número
  // animado (`--k`, 0 → 1), e cada fronteira é
  //
  //     x(k) = neutro + (fim − neutro) × k
  //
  // UMA função temporal só, literalmente: `--k` é animado UMA vez, na
  // barra, e as duas fronteiras (mais a diagonal) são funções puras dele.
  // Não são duas animações com temporização igual — é uma animação só,
  // lida por dois lugares. Isso mata na origem o frame em que a soma não
  // fecha 100%.
  //
  // E a arquitetura de CAMADAS EMPILHADAS, preservada, dá a garantia mais
  // forte ainda: a camada de baixo ocupa 100% da barra em TODOS os frames,
  // então a região da terceira fatia é literalmente "o que sobra" e a soma
  // fecha por construção, não por sincronia. Não existe superfície
  // descoberta em frame nenhum, nem durante o deslize — e é por isso que
  // as fatias NÃO viraram três segmentos independentes em flex/grid, que
  // é a forma de fazer isto que deixa buraco.
  function barraContinua(fatias) {
    var bar = document.createElement("div");
    bar.className = "proportion__bar";
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", alternativaTextualDaBarra(fatias));

    var acumulado = 0;
    fatias.forEach(function (s, i) {
      acumulado += s.pct;
      var camada = document.createElement("span");
      camada.className = "proportion__layer";
      camada.setAttribute("data-group", s.grupo);
      // Ordem de pintura: a primeira fatia é a que fica por cima.
      camada.style.zIndex = String(fatias.length - i);
      if (i === fatias.length - 1) {
        // A última preenche a barra inteira e não recebe recorte: é o
        // fundo sobre o qual as outras terminam. Sem ela haveria uma
        // faixa descoberta na direita quando a soma arredondada der 99 —
        // e, com a animação de fronteiras, uma faixa descoberta em todo
        // frame intermediário. Ela não tem fronteira própria e por isso
        // não participa da interpolação.
        camada.className += " proportion__layer--fundo";
      } else {
        // As DUAS pontas da fronteira desta camada. `--neutro` é a
        // partição em partes iguais (i+1 de n), que é onde a barra nasce;
        // `--fim` é a fronteira real acumulada. O CSS interpola entre as
        // duas com o mesmo `--k` que todas as outras leem.
        camada.style.setProperty("--neutro",
          (((i + 1) / fatias.length) * 100).toFixed(3));
        camada.style.setProperty("--fim", acumulado.toFixed(3));
      }
      bar.appendChild(camada);
    });

    // O percentual da menor fatia FINAL, sem unidade. A conversão para
    // pixel é do CSS (ver acima), e a interpolação da diagonal durante o
    // deslize também — no estado de terços a menor fatia é 33,333%, e o
    // CSS deriva o valor de agora do mesmo `--k`.
    var menorPct = fatias.reduce(function (m, x) {
      return Math.min(m, x.pct);
    }, 100);
    bar.style.setProperty("--menor-pct", menorPct.toFixed(3));
    return bar;
  }

  // =====================================================================
  // [v1.9.27, Entrega 3] O CALLOUT DE PERCENTUAL — os três números descem
  // da barra e passam a ficar ANCORADOS na fatia de cada um, abaixo dela,
  // ligados por um indicador fino. Os percentuais dos CABEÇALHOS de grupo
  // continuam onde estavam (Entrega 1): são o mesmo inteiro, e a fonte é a
  // mesma `share_real` de sempre.
  //
  // ---------------------------------------------------------------------
  // A COLISÃO, que é o problema real desta entrega, e a REGRA que a
  // resolve. `the-godfather` é 2% / 5% / 93%: os centros verdadeiros das
  // duas primeiras fatias ficam a 1% e 4,5% da largura da barra — 7,2px e
  // 32,4px em desktop, 3,4px e 15,1px a 375px. A caixa de um número mede
  // ~40px. Três números centrados nos seus centros verdadeiros se
  // sobrepõem, e nenhuma delas cabe dentro da própria fatia.
  //
  // REGRA ESCOLHIDA: EMPACOTAMENTO DA ESQUERDA PARA A DIREITA COM FOLGA
  // MÍNIMA, e o indicador inclinado absorve o deslocamento.
  //
  //   x1 = clamp de (c1 − L/2) entre 0 e (100% − 3L − 2g)
  //   x2 = max(x1 + L + g,  min(c2 − L/2, 100% − 2L − g))
  //   x3 = max(x2 + L + g,  min(c3 − L/2, 100% − L))
  //
  // onde c é o centro VERDADEIRO da fatia (o mesmo número que desenha a
  // barra), L a largura fixa da caixa do número e g a folga mínima. Cada
  // número vai para o centro da sua fatia; quando não cabe, escorrega o
  // mínimo necessário para a direita, e a linha que o liga ao centro
  // verdadeiro inclina. O ponto de ancoragem NUNCA se move: quem se move é
  // o rótulo, e a inclinação é a declaração visível de que ele se moveu.
  //
  // POR QUE ESTA E NÃO AS OUTRAS DUAS:
  //  · OMISSÃO abaixo de um limiar foi descartada de saída — sumir com o
  //    "~2%" é apagar exatamente o número que o leitor não esperava, e a
  //    Entrega 4 exige os três legíveis e no DOM desde o primeiro frame.
  //  · EMPILHAMENTO VERTICAL resolve a colisão mas cobra altura e desfaz a
  //    leitura em linha única; e um número na segunda linha continua
  //    precisando de um indicador inclinado para achar a fatia — ou seja,
  //    paga o custo do deslocamento sem evitar o problema dele.
  //
  // POR QUE ELA VALE PARA QUALQUER DISTRIBUIÇÃO FUTURA, e não só para as
  // 35 de hoje: a regra é uma passada de empacotamento, não uma exceção
  // por filme. Ela SEMPRE tem solução enquanto 3L + 2g couber na barra —
  // ~135px contra 335px de barra a 375px de viewport, com folga de 2,5×.
  // Abaixo disso (viewport de ~180px, que não existe) os números
  // encostariam; acima, qualquer combinação de três percentuais que somem
  // 100 é acomodada, inclusive 0/0/100 e 33/33/34.
  //
  // ONDE A CONTA MORA: NO CSS, pela mesma razão de `--diag` (§3[E]). O
  // centro de cada fatia é DADO (percentual, sai do JSON e nunca muda); a
  // largura da caixa do número é TIPOGRAFIA (`ch` da mono, o CSS sabe e o
  // JS só saberia medindo); a largura da barra é LAYOUT (muda a cada
  // resize). `min()`/`max()` misturam porcentagem e `ch` sem problema, e
  // o resultado reage a resize e a zoom de fonte sozinho — sem
  // `ResizeObserver`, sem ouvinte de `resize`, sem um único recálculo em
  // JS. O JS grava só `--c1..--cn` e `--n`.
  //
  // `aria-hidden` — DIVERGE, de propósito, da decisão tomada para a
  // LEGENDA logo abaixo ("a legenda visível não é aria-hidden: esconder
  // texto visível de quem usa leitor de tela troca um problema por
  // outro"). A legenda carrega o NOME do grupo: lida isolada, ela
  // informa. Um "~2%" solto, não — sem o nome ao lado, os três números
  // viram três grandezas órfãs logo depois de o leitor de tela já ter
  // anunciado "HATERS, cerca de 2% das notas; MIXED...", que é o
  // `aria-label` da barra, com rótulo e na mesma ordem. O callout não
  // acrescenta um bit de informação ao que a alternativa textual da barra
  // já diz; é uma re-apresentação VISUAL dela. Esconder aqui não perde
  // nada e evita três números sem dono.
  // =====================================================================
  function calloutDePercentual(fatias) {
    var el = document.createElement("div");
    el.className = "proportion__callout";
    el.setAttribute("aria-hidden", "true");
    el.style.setProperty("--n", String(fatias.length));

    var acumulado = 0;
    fatias.forEach(function (s, i) {
      // O centro VERDADEIRO da fatia, na mesma escala normalizada que
      // desenha a barra — é a mesma lista `fatias`, então o indicador
      // aponta para a geometria real, e não para uma segunda conta que
      // pudesse divergir dela.
      var centro = acumulado + s.pct / 2;
      acumulado += s.pct;
      el.style.setProperty("--c" + (i + 1), centro.toFixed(3));

      // Um invólucro por fatia, `inset: 0`: ele tem a MESMA largura do
      // callout, então as porcentagens de `left`/`width` dos filhos
      // resolvem contra a largura da barra, que é o sistema de
      // coordenadas em que `--c` está escrito.
      var anc = document.createElement("div");
      anc.className = "proportion__anchor";
      anc.setAttribute("data-group", s.grupo);
      anc.style.setProperty("--ordem", String(i));

      // O indicador tem DUAS metades porque o CSS não tem sinal: a que
      // aponta para a direita mede `max(0, rótulo − centro)` e a que
      // aponta para a esquerda mede `max(0, centro − rótulo)`. Só uma tem
      // largura de verdade; a outra colapsa para a espessura mínima e vira
      // a marquinha vertical em cima do centro verdadeiro da fatia — que é
      // justamente o que se quer ali. Sem deslocamento nenhum, as duas
      // colapsam e o indicador é uma marca vertical de 2px.
      var dir = document.createElement("span");
      dir.className = "proportion__lead proportion__lead--dir";
      var esq = document.createElement("span");
      esq.className = "proportion__lead proportion__lead--esq";

      // O NÚMERO. Mesmo inteiro do cabeçalho do grupo, mesma fonte
      // `share_real`. Está no DOM, com texto de verdade, desde o primeiro
      // frame: a ignição da Fase 3 mexe em opacidade, cor e sombra — nunca
      // em conteúdo (Entrega 4, item 3).
      var num = document.createElement("span");
      num.className = "proportion__pct";
      num.textContent = "~" + s.share + "%";

      anc.appendChild(dir);
      anc.appendChild(esq);
      anc.appendChild(num);
      el.appendChild(anc);
    });
    return el;
  }

  function legendaDaBarra(fatias) {
    var leg = document.createElement("ul");
    leg.className = "proportion__legend";
    fatias.forEach(function (s) {
      var li = document.createElement("li");
      // CHAVE INTERNA no atributo (é o que o CSS casa), rótulo novo no
      // texto — a mesma separação de `.group[data-group]`.
      li.setAttribute("data-group", s.grupo);
      var sw = document.createElement("span");
      sw.className = "proportion__swatch";
      sw.setAttribute("data-group", s.grupo);
      sw.setAttribute("aria-hidden", "true");
      var nm = document.createElement("span");
      nm.className = "proportion__legend-label";
      // RÓTULO ISOLADO — identifica a faixa. Entrega 3 troca aqui.
      nm.textContent = rotuloDoGrupo(s.grupo);
      li.appendChild(sw);
      li.appendChild(nm);
      leg.appendChild(li);
    });
    return leg;
  }

  // As três fatias, na ordem de leitura do site, já normalizadas. `null`
  // quando o filme não tem distribuição real (o degradado sintético) — aí
  // não há barra, e a nota abaixo troca de texto (ver `notaDaCota`).
  function fatiasDeProporcao(f) {
    var porNome = {};
    (f.buckets || []).forEach(function (b) { porNome[b.bucket] = b; });
    var total = 0;
    GRUPOS_ORDEM.forEach(function (g) {
      var b = porNome[g];
      if (b && typeof b.share_real === "number") total += b.share_real;
    });
    if (!total) return null;
    return GRUPOS_ORDEM.map(function (g) {
      var b = porNome[g] || {};
      var share = typeof b.share_real === "number" ? b.share_real : 0;
      return { grupo: g, share: share, pct: (share / total) * 100 };
    }).filter(function (s) { return s.share > 0; });
  }

  // A alternativa textual da barra. Usa o RÓTULO do grupo (é aqui que a
  // barra diz de qual grupo é cada faixa) e o MESMO inteiro que o
  // cabeçalho daquele grupo imprime — nunca um valor recalculado.
  function alternativaTextualDaBarra(fatias) {
    return "Peso real de cada grupo na recepção: "
      + fatias.map(function (s) {
        return rotuloDoGrupo(s.grupo) + ", cerca de " + s.share + "% das notas";
      }).join("; ") + ".";
  }

  // [v1.9.27, Entrega 1] O DISCLAIMER DA COTA SAIU DO RAMO COM BARRA.
  // Esta função existe agora só para o ramo SEM distribuição real.
  //
  // O QUE SAIU, literal: "A barra é o peso real de cada grupo. A análise
  // abaixo tem profundidade igual nos três — o tamanho das listas não
  // indica peso." Ficava sob a barra desde a v1.9.26.
  //
  // POR QUE SAIU, e é DECISÃO, não esquecimento: com o callout de
  // percentual (Entrega 3) o topo da página passou a dizer o peso duas
  // vezes — a barra e os três números ancorados nela —, e a frase virava
  // uma terceira explicação do mesmo fato a 800px de distância das listas
  // que ela existia para desarmar.
  //
  // O QUE A REMOÇÃO CUSTA, escrito porque é ele que a decisão paga: essa
  // era a única frase que dizia, em palavras, que listas de bullets do
  // mesmo tamanho NÃO são grupos do mesmo peso. Sem ela, o único sinal de
  // peso CO-LOCALIZADO com as listas é o "~46% DAS NOTAS" no cabeçalho de
  // cada grupo — e é por isso que ele FICA (a Entrega 1 removeu a frase e
  // preservou o percentual do cabeçalho de propósito). Quem rolar direto
  // para os bullets vê seis marcadores em HATERS e seis em FANS com 2% e
  // 93% impressos ao lado do nome de cada um; o número no cabeçalho é o
  // que impede a leitura "listas iguais, pesos iguais" de fechar. Se o
  // percentual do cabeçalho algum dia sair, esta frase tem de voltar.
  //
  // v1.4.0 / v1.2.1 (PRESERVADO INTACTO): sem distribuição real não há
  // barra nenhuma, não há callout e não há percentual em cabeçalho algum —
  // aí a única coisa na tela sobre tamanho de grupo são as listas, e a
  // regra da v1.2.1 volta a valer inteira. Mesmo texto de sempre, mantido
  // em sincronia com render.py (DISCLAIMER_*).
  // [v1.9.20] Sem algarismo de contagem de review ("40 · 40 · 40" saiu).
  function notaDaCota() {
    var p = document.createElement("p");
    p.className = "proportion__note";
    p.textContent =
      "Os grupos são cotas de coleta — não a proporção real das opiniões.";
    return p;
  }

  // --- divisor ---
  // [v1.9.26, Entrega 1] O cabeçalho "EM DETALHE · TEMA A TEMA" SAI (não
  // há mais nada antes dele que precise ser separado de "o detalhe"; os
  // bullets vêm direto), e o disclaimer migrou para `notaDaCota`, embaixo
  // da barra. Sobra a linha arco-íris, que continua marcando a passagem do
  // topo para a análise — só mudou de posição na página.
  // [v1.9.32] ETIQUETAS DE SEÇÃO — a página ganha estrutura nomeada.
  // Tipografia de rótulo mono já existente no projeto (a mesma família,
  // corpo e tracking que `.film-header__meta` e a legenda da barra usam);
  // nenhuma família nova entra por causa disto.
  function sectionLabel(texto) {
    var el = document.createElement("p");
    el.className = "section-label";
    el.textContent = texto;
    return el;
  }

  // [v1.9.32] "EM DETALHE · TEMA A TEMA" ESTÁ VOLTANDO, e a reversão é
  // consciente — ver SPEC §3[E]. Ele foi REMOVIDO na v1.9.26 com uma razão
  // específica: com o veredito descendo para o rodapé, não havia mais um
  // resumo ANTES dos bullets do qual separar "o detalhe", e o rótulo virou
  // uma promessa sem contraparte. A razão de agora é OUTRA, e é o que
  // torna isto reversão e não vaivém: a página passou a ter seções
  // NOMEADAS (RECEPÇÃO abre o topo), e numa página seccionada o bloco de
  // bullets é o único que ficaria anônimo. Além disso a SINOPSE saiu, e
  // com ela o último texto corrido antes dos bullets — o leitor chega ali
  // vindo direto da barra, e o rótulo é o que diz que a régua mudou de
  // "peso de cada grupo" para "o que cada grupo disse".
  function detailDivider() {
    var el = document.createElement("div");
    el.className = "detail-divider";
    el.innerHTML = '<div class="spectrum-line" aria-hidden="true"></div>';
    el.appendChild(sectionLabel("EM DETALHE · TEMA A TEMA"));
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
  // [v1.9.34] A LINHA DE AUSÊNCIA DE VEREDITO (SPEC §2.5). Determinística,
  // em código, ZERO LLM — ela não é um veredito, é a explicação de por que
  // não há um, e o CSS a distingue de um (`.verdict-absent`, não `.verdict`).
  //
  // As três invariantes que a redação obedece, e nenhuma é decorativa:
  //   · ancorada na BASE, nunca na MAGNITUDE — é exatamente a exceção que a
  //     v1.9.22 preservou ao proibir deflação por hedge;
  //   · zero algarismo (v1.9.20) e zero quantificador (v1.9.22);
  //   · os DOIS estados no MESMO nível, por extenso. "ou apenas discordam"
  //     rebaixaria em prosa o estado que 29 dos 35 filmes publicam — é a
  //     neutralidade do §0 aplicada à frase que explica por que não há estado.
  // FUNÇÃO, e não `var`, de propósito. A primeira versão disto era
  // `var SEM_ESTADO_DE_CONTRASTE = "..."` declarado aqui, ao lado de quem
  // usa — e a página renderizou a linha VAZIA: o render dispara antes desta
  // altura do arquivo, então no momento da chamada o `var` ainda valia
  // `undefined`, e `textContent = undefined` grava STRING VAZIA (não a
  // palavra "undefined"), o que faz o defeito não gritar em lugar nenhum.
  // Declaração de função é hasteada inteira; a ordem deixa de importar.
  // Pego pela verificação no navegador, com a suíte inteira verde.
  function semEstadoDeContraste() {
    return "A amostra analisada deste filme é pequena demais para dizer se " +
      "os grupos falam de coisas diferentes ou se falam das mesmas coisas e " +
      "divergem no julgamento.";
  }

  function veredictoBlock(f) {
    var e = f.eixos;
    // Sem `contraste` no bloco, a medição se RECUSOU a decidir (n < 10,
    // §2.5). O fallback de render NÃO pode rodar aqui: com nenhum eixo acima
    // da margem ele produziria a frase VALORATIVA ("os grupos falam das
    // mesmas coisas e divergem no julgamento"), que é uma das duas
    // afirmações que o piso existe para impedir. O espelho deste defeito no
    // Python punha o ausente no ramo TEMÁTICO — o mesmo buraco, saindo pelos
    // dois lados opostos (§2.5, "o defeito que o piso encontrou").
    if (e && e.linhas && e.linhas.length && !("contraste" in e)) {
      var aviso = document.createElement("p");
      aviso.className = "verdict-absent";
      aviso.textContent = semEstadoDeContraste();
      return aviso;
    }
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

    var dominante = bucketDominante(buckets);
    var meioDominante = !!(dominante && dominante.bucket === "medianas");

    var pos = eixoDeMaiorLift(e, "positivas", buckets);
    var neg = eixoDeMaiorLift(e, "negativas", buckets);
    var posOk = !!pos && pos.acima_da_margem;
    var negOk = !!neg && neg.acima_da_margem;

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
    var cel = melhor.por_bucket[bucket];
    // [v1.9.34] `acima_da_margem` vem do JSON, calculado em Fraction exato
    // por `eixos.py`. NUNCA recalcule `lift_pp >= margem` aqui: `lift_pp` é
    // derivado e arredondado a uma casa, e o limiar da lei (144,4/√n) é
    // IRRACIONAL — o acidente aritmético que tornava o recálculo inofensivo
    // enquanto a margem era o inteiro 20 acabou (SPEC §4).
    return { eixo: melhor.eixo, lift_pp: cel.lift_pp,
             acima_da_margem: cel.acima_da_margem === true };
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
  // =====================================================================
  // [v1.9.30] A ORDEM DE LEITURA DOS BLOCOS EM DESTAQUE — POR PESO.
  //
  // Até aqui os blocos saíam em ordem FIXA (negativas antes de positivas),
  // qualquer que fosse o peso de cada grupo. `the-godfather` é 2/5/93: a
  // leitura abria por HATERS, que é 2% das notas, e o grupo que responde por
  // 93% da recepção chegava depois. Isso não descreve o filme.
  //
  // A REGRA É FUNÇÃO DO DADO, E É ISSO QUE A MANTÉM COMPATÍVEL COM O §0.
  // Ela não privilegia negativo nem positivo: privilegia QUEM É MAIOR, e
  // quem é maior sai do `share_real`, não de um juízo do produto. Em
  // `cats-2019` (86/7/7) o primeiro bloco é HATERS; em `the-godfather`
  // (2/5/93) é FANS. A ordem antiga não era neutra — era CONSTANTE, que é
  // outra coisa: liderar sempre pelo negativo é uma escolha editorial fixa,
  // e ela estava sendo tomada 35 vezes sem que o dado fosse consultado.
  //
  // A NEUTRALIDADE DE TRATAMENTO CONTINUA INTEGRALMENTE EM VIGOR: mesmo
  // leiaute, mesmo peso tipográfico, mesma quantidade de bullets, mesmas
  // cores, mesmo espaço estrutural. Só a POSIÇÃO muda — e a posição é a
  // única coisa da tela que o peso pode legitimamente decidir.
  //
  // VALE NOS DOIS LEIAUTES, e é a mesma linha de código nos dois: o
  // container é grid/flex e a ordem do DOM É a ordem visual. No desktop
  // "primeiro" é a coluna da ESQUERDA; no mobile, empilhado, é o de CIMA —
  // onde a ordem pesa mais, porque lá o segundo bloco só existe depois de
  // uma rolagem.
  //
  // O MEIO NÃO MUDA DE POLÍTICA. Quem decide se `medianas` está em destaque
  // continua sendo `bucketDominante` (a exceção automática do §0), e esta
  // função só ordena o que já foi decidido: se o meio está em destaque, ele
  // entra na mesma ordenação por peso; se está recolhido, ele não é
  // ordenado porque não está aqui.
  //
  // A BARRA DE PROPORÇÃO NÃO É REORDENADA — e isso não é uma omissão. A
  // ordem dela é SEMÂNTICA: é um eixo ordinal de 0,5★ a 5★, e HATERS à
  // esquerda / MIXED no meio / FANS à direita é o que faz a barra ser uma
  // população particionada em vez de três medições. Reordenar por peso ali
  // destruiria o eixo. Barra, faixa do mosaico, legenda e `aria-label`
  // continuam todos em negativas → medianas → positivas.
  //
  // EMPATE: critério determinístico, e é a ordem canônica do produto
  // (negativas → medianas → positivas). `Array.prototype.sort` é estável em
  // todo motor moderno, mas a estabilidade não é o que está sendo usada
  // aqui — o índice canônico entra na comparação EXPLICITAMENTE, para que a
  // regra seja legível no código e não uma propriedade herdada do runtime.
  // Nenhum dos 35 filmes empata hoje entre grupos em destaque; a regra
  // existe para o filme que ainda não foi publicado.
  function ordenarPorPeso(nomes, porNome) {
    function peso(nome) {
      var b = porNome[nome];
      // Sem `share_real` (JSON antigo, sem histograma) não há peso para
      // ordenar, e o filme cai inteiro na ordem canônica — que é o que a
      // página já fazia antes desta versão.
      return (b && typeof b.share_real === "number") ? b.share_real : -1;
    }
    return nomes.slice().sort(function (a, b) {
      return (peso(b) - peso(a))
          || (GRUPOS_ORDEM.indexOf(a) - GRUPOS_ORDEM.indexOf(b));
    });
  }

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
    var ordem = ordenarPorPeso(
      meioDominante ? ["negativas", "medianas", "positivas"]
                    : ["negativas", "positivas"],
      porNome);
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
    // RÓTULO ISOLADO — este `aria-label` existe exatamente para dizer de
    // qual grupo é a seção. Entrega 3 troca aqui (`meta.label` vem de
    // `GRUPO_LABEL`). `data-group` continua com a CHAVE INTERNA, que é o
    // que o CSS casa e o que o JSON usa — a chave nunca muda.
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
    // RÓTULO ISOLADO — o cabeçalho do bloco de bullets. Entrega 3 troca
    // aqui, e com o MESMO destaque visual de antes: mesmo peso, mesma cor
    // de grupo (`.group[data-group=…] .group__name`), mesma posição.
    // `.toUpperCase()` fica: os rótulos novos já são caixa alta, mas a
    // função não pode depender disso para o caso de reversão.
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

    // =================================================================
    // [v1.9.26, Entrega 4] O DISCLOSURE "APROFUNDAR".
    //
    // TEXTO: "Exemplo parafraseado" → "Aprofundar". UM rótulo só, igual
    // nos dois estados — o indicador de estado é o chevron, e dois labels
    // para a mesma coisa é ruído que o `aria-expanded` já cobre.
    //
    // VISUAL: deixa de parecer botão. O pill da v1.9.19 (fundo preenchido
    // na cor do grupo, `border-radius: 999px`, padding de CTA) resolvia um
    // problema real — o "+" da versão anterior não parecia clicável — mas
    // resolveu demais: virou o elemento mais chamativo do bullet,
    // competindo com o próprio tema. A referência agora é disclosure
    // editorial minimalista (GOV.UK Details e afins): fundo transparente,
    // sem borda, sem cápsula, tipografia da monoespaçada que já existe, na
    // cor do grupo com peso visual MENOR que o título e a barra. Ver
    // `.theme__toggle` em styles.css — nenhuma linguagem visual nova.
    //
    // ESTRUTURA (é a animação que a pede): três camadas em vez de uma.
    // O `<div id>` externo é a caixa que ABRE (grid `0fr`→`1fr`), o
    // `-clip` recorta, e o `-inner` é o que DESLIZA de trás do bullet até
    // a posição final. `aria-controls` continua apontando para o elemento
    // externo, o mesmo de sempre. A arquitetura de expansão (botão +
    // `aria-expanded` + classe `is-open` no alvo) é a da v1.9.19, reusada
    // como está — só o alvo tem filhos agora.
    // =================================================================
    if (t.exemplo_parafraseado) {
      var id = "ex-" + bucket + "-" + idx;
      var btn = document.createElement("button");
      btn.className = "theme__toggle";
      btn.type = "button";
      btn.setAttribute("aria-expanded", "false");
      btn.setAttribute("aria-controls", id);
      btn.innerHTML = '<span class="theme__toggle-label">Aprofundar</span>'
        + chevronSvg();

      var ex = document.createElement("div");
      ex.className = "theme__example";
      ex.id = id;

      var clip = document.createElement("div");
      clip.className = "theme__example-clip";
      var inner = document.createElement("div");
      inner.className = "theme__example-inner";
      inner.textContent = t.exemplo_parafraseado;
      if (t.aspas_removidas) {
        var fl = document.createElement("span");
        fl.className = "theme__flag";
        fl.textContent = "aspas de citação removidas mecanicamente";
        inner.appendChild(fl);
      }
      clip.appendChild(inner);
      ex.appendChild(clip);

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
