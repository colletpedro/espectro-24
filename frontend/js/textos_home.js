/* Espectro 24 — textos_home.js
   TODA a prosa da home num arquivo só: os títulos das coleções (que eram
   os das prateleiras), as descrições fixas de eixo e de tipo da coleção do
   dia, a linha de metadado da manchete, a mensagem de busca vazia e os
   TEMPLATES da justificativa do filme do dia. A premissa e o aviso de
   catálogo saíram da home editorial e ficam aqui, sem uso na home, porque
   o teste "sem nota" de toda a prosa continua cobrindo-os. Nada aqui chama LLM, em build
   ou em runtime; a prosa vai ser substituída por modelo próprio depois, e é
   por isso que mora isolada — reescrever este arquivo não toca a lógica.

   REGRAS QUE ESTES TEXTOS SEGUEM (e que `tests/test_home_nova.py` cobra):
   · Sem nota, estrela, média ou escore — nem implícito.
   · Sem proporção de grupo e sem vocabulário de veredito. A lista proibida
     vive no teste (`VOCABULARIO_PROIBIDO`) e é, por extenso: amou, amaram,
     adorou, adoraram, odiou, odiaram, detestou, detestaram, gostou,
     gostaram, maioria, minoria, unanime/unanimidade, consenso, aclamado,
     obra-prima, imperdivel, melhor, pior, excelente, otimo, bom, boa, ruim,
     genial, fracasso, sucesso, decepcion*, recomend*, vale a pena, nota,
     notas, estrela(s), media, score, rating, ranking — além de qualquer
     algarismo e do sinal "%" fora do título do filme.
   · Neutralidade: quando um texto nomeia um grupo, nomeia os TRÊS, uma vez
     cada, na ordem de leitura do site (HATERS, MIXED, FANS).
     Nenhum template diz qual grupo fala mais de um assunto.
   · Anti-spoiler: a justificativa só usa o TÍTULO e o NOME do eixo. O
     índice que a alimenta não tem texto de review nenhum.

   GANCHOS DA JUSTIFICATIVA, em prioridade fixa (o primeiro que se aplica):
     1) `aniversario` — o dia e o mês de HOJE (America/Sao_Paulo) coincidem
                        com a data de estreia (`estreia`, AAAA-MM-DD) e o
                        ano de hoje é posterior ao da estreia. Uma frase de
                        aniversário SEM o número de anos (algarismo seria
                        quantidade fora do título), seguida do gancho de
                        conteúdo do filme (2 a 4, abaixo). Estreia em 29/02
                        só faz aniversário em ano bissexto.
                        [rodada 4] O aniversário passou a DEFINIR o
                        filme do dia (selecao.js); 01/01 não conta. Depois
                        da frase de aniversário, o gancho de conteúdo abre
                        com "Nele"/"Está" em vez de repetir o título.
     2) `eixo`        — o filme tem eixo acima da margem de lift: usa o de
                        maior lift_pp (empate: o primeiro na ordem da
                        taxonomia).
     3) `valorativo`  — `contraste: valorativo` E um assunto comum
                        dominante (`assunto_comum`, calculado em
                        `build_indice.py`): o eixo de que os três grupos,
                        somados, falam MAIS DO QUE O HABITUAL no catálogo
                        — não o mais falado em termos absolutos, que seria
                        roteiro em quase todo filme. O texto diz isso, e
                        não "falam sobretudo de".
     4) `generico`    — nenhum dos anteriores (hoje: `woman-of-fire`, abaixo
                        do piso do estado de contraste). */
(function (root) {
  "use strict";

  // A regra do aniversário mora em selecao.js (ela decide o filme do dia);
  // o texto usa a MESMA função, para não haver duas regras.
  var S = (typeof module !== "undefined" && module.exports)
    ? require("./selecao.js") : root.ESPECTRO_SELECAO;
  // [i18n] a prosa mora nos dicionários `pt`/`en` abaixo; o resto do arquivo
  // monta as mesmas constantes de antes a partir de I18N.t (I18N já está
  // carregado — é o primeiro script da página).
  var I = (typeof module !== "undefined" && module.exports)
    ? require("./i18n.js") : root.I18N;
  var t = I.t;

  I.registrar({
    pt: {
      "home.tres_grupos": "HATERS, MIXED e FANS",
      "home.premissa": "Como {grupos} veem cada filme — cada grupo com as próprias palavras, lado a lado, sem nota e sem spoiler.",
      "home.aviso_catalogo": "O catálogo cresce com o tempo: novos filmes são adicionados aos poucos.",
      "home.aviso_link": "Ver todos os filmes",
      "home.busca_placeholder": "Buscar filme por título ou ano",
      "home.busca_vazia": "Esse filme ainda não está no catálogo. Novos filmes chegam com o tempo.",
      "home.busca_vazia_link": "Ver o catálogo completo",
      "home.rotulo_filme_do_dia": "Filme do dia",
      "home.rotulo_abrir": "Abrir a análise",
      "home.rotulo_recem": "Recém-chegados",
      "home.rotulo_recem_todos": "Ver todos os recém-chegados",
      "home.nome_site": "Espectro 24",
      "home.link_filmes": "Filmes",
      "home.link_metodo": "Método",
      "home.rotulo_colecao": "Coleção do dia",
      "home.rotulo_colecao_todos": "Ver todos",
      "home.titulo_explorar": "Explorar",
      "home.grupo_explorar.assunto": "Por assunto",
      "home.grupo_explorar.decada": "Por década",
      "home.grupo_explorar.genero": "Por gênero",
      "home.grupo_explorar.pais": "Por país",
      "home.resumo_explorar": "Explorar por assunto, década, gênero e país",
      "home.link_indice": "Índice A–Z",
      "home.vista_grade": "Grade",
      "home.vista_indice": "Índice A–Z",
      "home.mostrar_mais": "Mostrar mais",
      "home.filtro_vazio": "Nenhum filme com esses filtros.",
      "home.limpar_filtros": "Limpar os filtros",
      "home.remover_filtro": "Remover filtro",
      "home.qualquer.colecao": "Qualquer assunto",
      "home.qualquer.decada": "Qualquer década",
      "home.qualquer.genero": "Qualquer gênero",
      "home.qualquer.pais": "Qualquer país",
      "home.contador": "{mostrados} de {total}",
      "home.chip_desde": function (v) {
        return "Recém-chegados desde " + v.d + "/" + v.m + "/" + v.a;
      },
      "home.titulo_decada": function (v) {
        return "Seleção anos " + String(v.decada % 100).padStart(2, "0");
      },
      "home.descricao_decada": "Filmes do catálogo lançados entre {ini} e {fim}.",
      "home.min": "{n} min",
      "home.titulo_pagina": "Espectro 24 — a recepção completa de um filme, sem spoilers",
      "home.descricao_pagina": "A recepção completa de um filme — o que quem odiou, quem amou e quem ficou no meio diz — sem nota média e sem spoilers.",
      "home.rodape.sintese": "Síntese automática a partir de reviews públicas do Letterboxd. Sem nota média, sem spoilers.",
      "home.rodape.tmdb": "Este produto usa a API do TMDB, mas não é endossado nem certificado pelo TMDB.",
      "home.rodape.creditos": "créditos e fontes",

      "home.descricao_eixo.ritmo": "Ritmo é a sensação de tempo do filme: se ele se arrasta, respira ou corre.",
      "home.descricao_eixo.atuacao": "Atuação é o que o elenco entrega: presença, voz, gesto, a credibilidade de cada personagem.",
      "home.descricao_eixo.direcao_imagem": "Direção e imagem é o filme como coisa vista: enquadramento, fotografia, cor, a mão de quem dirige.",
      "home.descricao_eixo.roteiro_estrutura": "Roteiro e estrutura é como a história é montada: diálogos, viradas, a ordem em que as coisas acontecem.",
      "home.descricao_eixo.som_trilha": "Som e trilha é tudo o que se ouve: a música, o silêncio, o desenho de som.",
      "home.descricao_eixo.tom_atmosfera": "Tom e atmosfera é o clima que o filme sustenta: o desconforto, a leveza, a estranheza que fica no ar.",
      "home.descricao_eixo.impacto_emocional": "Impacto emocional é o que o filme faz com quem assiste: se comove, perturba ou deixa frio.",
      "home.descricao_eixo.comparacoes": "Comparações é quando o filme é medido contra outro: o original, a sequência, a obra anterior de quem dirige.",
      "home.descricao_eixo.expectativa": "Expectativa é a distância entre o que se esperava e o que se encontrou.",
      "home.descricao_eixo.critica_social": "Crítica social é o que o filme diz sobre o mundo fora dele: classe, poder, história.",

      "home.frase_tipo.divisao": "Nestes filmes, é desse assunto que um grupo fala muito mais que os outros.",
      "home.frase_tipo.valorativa": "Nestes filmes, os três grupos falam disso mais do que o habitual e chegam a vereditos diferentes.",

      "home.eixo_nome.ritmo": "ritmo",
      "home.eixo_nome.atuacao": "atuação",
      "home.eixo_nome.direcao_imagem": "direção e imagem",
      "home.eixo_nome.roteiro_estrutura": "roteiro e estrutura",
      "home.eixo_nome.som_trilha": "som e trilha",
      "home.eixo_nome.tom_atmosfera": "tom e atmosfera",
      "home.eixo_nome.impacto_emocional": "impacto emocional",
      "home.eixo_nome.comparacoes": "comparações com outros filmes",
      "home.eixo_nome.expectativa": "expectativa",
      "home.eixo_nome.critica_social": "crítica social",

      "home.prateleira.ritmo": "Onde o ritmo divide",
      "home.prateleira.atuacao": "Onde a atuação divide",
      "home.prateleira.direcao_imagem": "Onde a direção e a imagem dividem",
      "home.prateleira.roteiro_estrutura": "Onde o roteiro divide",
      "home.prateleira.som_trilha": "Onde o som e a trilha dividem",
      "home.prateleira.tom_atmosfera": "Onde o tom e a atmosfera dividem",
      "home.prateleira.impacto_emocional": "Onde o impacto emocional divide",
      "home.prateleira.comparacoes": "Onde as comparações dividem",
      "home.prateleira.expectativa": "Onde a expectativa divide",
      "home.prateleira.critica_social": "Onde a crítica social divide",
      "home.prateleira.valorativo:ritmo": "Todos falam do ritmo, ninguém concorda",
      "home.prateleira.valorativo:atuacao": "Todos falam da atuação, ninguém concorda",
      "home.prateleira.valorativo:direcao_imagem": "Todos falam da direção e da imagem, ninguém concorda",
      "home.prateleira.valorativo:roteiro_estrutura": "Todos falam do roteiro, ninguém concorda",
      "home.prateleira.valorativo:som_trilha": "Todos falam do som e da trilha, ninguém concorda",
      "home.prateleira.valorativo:tom_atmosfera": "Todos falam do tom e da atmosfera, ninguém concorda",
      "home.prateleira.valorativo:impacto_emocional": "Todos falam do impacto emocional, ninguém concorda",
      "home.prateleira.valorativo:comparacoes": "Todos fazem comparações, ninguém concorda",
      "home.prateleira.valorativo:expectativa": "Todos falam da expectativa, ninguém concorda",
      "home.prateleira.valorativo:critica_social": "Todos falam da crítica social, ninguém concorda",

      "home.tpl.aniversario": "{t} faz aniversário de estreia hoje.",
      "home.tpl.eixo": "{abre} assunto em que {grupos} mais se afastam é {eixo}. Um dos grupos fala disso bem mais que os outros dois — a página mostra qual, e com que palavras.",
      "home.tpl.eixo_abre": "{t}: o",
      "home.tpl.eixo_abre_sem": "Nele, o",
      "home.tpl.valorativo": "{abre} assunto que aparece mais do que o habitual no catálogo, somando {grupos}, é {eixo}. Os três grupos falam dele e chegam a vereditos diferentes — o que muda é o valor que cada um dá ao filme, não o tema da conversa.",
      "home.tpl.generico": "{abre} no catálogo com o que {grupos} dizem sobre ele. A página mostra os assuntos de cada grupo lado a lado, cada um com as próprias palavras.",
      "home.tpl.generico_abre": "{t} está",
      "home.tpl.generico_abre_sem": "Está",
    },
    en: {
      "home.tres_grupos": "HATERS, MIXED and FANS",
      "home.premissa": "How {grupos} see each film — each group in its own words, side by side, with no score and no spoilers.",
      "home.aviso_catalogo": "The catalog grows over time: new films are added a few at a time.",
      "home.aviso_link": "See all films",
      "home.busca_placeholder": "Search films by title or year",
      "home.busca_vazia": "That film isn't in the catalog yet. New films arrive over time.",
      "home.busca_vazia_link": "See the full catalog",
      "home.rotulo_filme_do_dia": "Film of the day",
      "home.rotulo_abrir": "Open the analysis",
      "home.rotulo_recem": "New arrivals",
      "home.rotulo_recem_todos": "See all new arrivals",
      "home.nome_site": "Espectro 24",
      "home.link_filmes": "Films",
      "home.link_metodo": "Method",
      "home.rotulo_colecao": "Collection of the day",
      "home.rotulo_colecao_todos": "See all",
      "home.titulo_explorar": "Explore",
      "home.grupo_explorar.assunto": "By topic",
      "home.grupo_explorar.decada": "By decade",
      "home.grupo_explorar.genero": "By genre",
      "home.grupo_explorar.pais": "By country",
      "home.resumo_explorar": "Explore by topic, decade, genre and country",
      "home.link_indice": "A–Z index",
      "home.vista_grade": "Grid",
      "home.vista_indice": "A–Z index",
      "home.mostrar_mais": "Show more",
      "home.filtro_vazio": "No films match these filters.",
      "home.limpar_filtros": "Clear filters",
      "home.remover_filtro": "Remove filter",
      "home.qualquer.colecao": "Any topic",
      "home.qualquer.decada": "Any decade",
      "home.qualquer.genero": "Any genre",
      "home.qualquer.pais": "Any country",
      "home.contador": "{mostrados} of {total}",
      "home.chip_desde": function (v) {
        var meses = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                     "Sep", "Oct", "Nov", "Dec"];
        return "New arrivals since " + meses[Number(v.m) - 1] + " " + Number(v.d) + ", " + v.a;
      },
      "home.titulo_decada": function (v) { return "The " + v.decada + "s selection"; },
      "home.descricao_decada": "Films in the catalog released between {ini} and {fim}.",
      "home.min": "{n} min",
      "home.titulo_pagina": "Espectro 24 — the full reception of a film, spoiler-free",
      "home.descricao_pagina": "The full reception of a film — what those who hated it, those who loved it and those in the middle say — with no average score and no spoilers.",
      "home.rodape.sintese": "Automatic synthesis of public Letterboxd reviews. No average score, no spoilers.",
      "home.rodape.tmdb": "This product uses the TMDB API but is not endorsed or certified by TMDB.",
      "home.rodape.creditos": "credits and sources",

      "home.descricao_eixo.ritmo": "Pacing is the film's sense of time: whether it drags, breathes or runs.",
      "home.descricao_eixo.atuacao": "Acting is what the cast delivers: presence, voice, gesture, the credibility of each character.",
      "home.descricao_eixo.direcao_imagem": "Direction and imagery is the film as something seen: framing, cinematography, color, the hand of whoever directs.",
      "home.descricao_eixo.roteiro_estrutura": "Script and structure is how the story is built: dialogue, turns, the order in which things happen.",
      "home.descricao_eixo.som_trilha": "Sound and score is everything you hear: the music, the silence, the sound design.",
      "home.descricao_eixo.tom_atmosfera": "Tone and atmosphere is the mood the film sustains: the unease, the lightness, the strangeness left hanging in the air.",
      "home.descricao_eixo.impacto_emocional": "Emotional impact is what the film does to whoever watches it: whether it moves, unsettles or leaves them cold.",
      "home.descricao_eixo.comparacoes": "Comparisons is when the film is measured against another: the original, the sequel, the director's earlier work.",
      "home.descricao_eixo.expectativa": "Expectations is the distance between what was expected and what was found.",
      "home.descricao_eixo.critica_social": "Social commentary is what the film says about the world outside it: class, power, history.",

      "home.frase_tipo.divisao": "In these films, this is the topic one group talks about far more than the others.",
      "home.frase_tipo.valorativa": "In these films, all three groups talk about this more than usual and reach different verdicts.",

      "home.eixo_nome.ritmo": "pacing",
      "home.eixo_nome.atuacao": "acting",
      "home.eixo_nome.direcao_imagem": "direction and imagery",
      "home.eixo_nome.roteiro_estrutura": "script and structure",
      "home.eixo_nome.som_trilha": "sound and score",
      "home.eixo_nome.tom_atmosfera": "tone and atmosphere",
      "home.eixo_nome.impacto_emocional": "emotional impact",
      "home.eixo_nome.comparacoes": "comparisons with other films",
      "home.eixo_nome.expectativa": "expectations",
      "home.eixo_nome.critica_social": "social commentary",

      "home.prateleira.ritmo": "Where pacing divides",
      "home.prateleira.atuacao": "Where acting divides",
      "home.prateleira.direcao_imagem": "Where direction and imagery divide",
      "home.prateleira.roteiro_estrutura": "Where the script divides",
      "home.prateleira.som_trilha": "Where sound and score divide",
      "home.prateleira.tom_atmosfera": "Where tone and atmosphere divide",
      "home.prateleira.impacto_emocional": "Where emotional impact divides",
      "home.prateleira.comparacoes": "Where comparisons divide",
      "home.prateleira.expectativa": "Where expectations divide",
      "home.prateleira.critica_social": "Where social commentary divides",
      "home.prateleira.valorativo:ritmo": "Everyone talks about the pacing, no one agrees",
      "home.prateleira.valorativo:atuacao": "Everyone talks about the acting, no one agrees",
      "home.prateleira.valorativo:direcao_imagem": "Everyone talks about direction and imagery, no one agrees",
      "home.prateleira.valorativo:roteiro_estrutura": "Everyone talks about the script, no one agrees",
      "home.prateleira.valorativo:som_trilha": "Everyone talks about sound and score, no one agrees",
      "home.prateleira.valorativo:tom_atmosfera": "Everyone talks about tone and atmosphere, no one agrees",
      "home.prateleira.valorativo:impacto_emocional": "Everyone talks about emotional impact, no one agrees",
      "home.prateleira.valorativo:comparacoes": "Everyone makes comparisons, no one agrees",
      "home.prateleira.valorativo:expectativa": "Everyone talks about expectations, no one agrees",
      "home.prateleira.valorativo:critica_social": "Everyone talks about social commentary, no one agrees",

      "home.tpl.aniversario": "{t} has its release anniversary today.",
      "home.tpl.eixo": "{abre} topic on which {grupos} differ most is {eixo}. One of the groups talks about it far more than the other two — the page shows which, and in what words.",
      "home.tpl.eixo_abre": "{t}: the",
      "home.tpl.eixo_abre_sem": "Here, the",
      "home.tpl.valorativo": "{abre} topic that comes up more than usual in the catalog, across {grupos} combined, is {eixo}. All three groups talk about it and reach different verdicts — what changes is the value each gives the film, not the subject of the conversation.",
      "home.tpl.generico": "{abre} in the catalog with what {grupos} say about it. The page lays out each group's topics side by side, each in its own words.",
      "home.tpl.generico_abre": "{t} is",
      "home.tpl.generico_abre_sem": "It is",
    },
  });

  var EIXOS = ["ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura",
    "som_trilha", "tom_atmosfera", "impacto_emocional", "comparacoes",
    "expectativa", "critica_social"];

  function porEixo(prefixo) {
    var o = {};
    EIXOS.forEach(function (e) { o[e] = t(prefixo + e); });
    return o;
  }

  // Os rótulos que o site já usa (`GRUPO_LABEL` em filme.js), na ordem
  // de leitura dele.
  var GRUPOS = ["HATERS", "MIXED", "FANS"];
  var TRES_GRUPOS = t("home.tres_grupos");

  var PREMISSA = t("home.premissa", { grupos: TRES_GRUPOS });

  var AVISO_CATALOGO = t("home.aviso_catalogo");
  var AVISO_LINK = t("home.aviso_link");

  var BUSCA_PLACEHOLDER = t("home.busca_placeholder");
  var BUSCA_VAZIA = t("home.busca_vazia");
  var BUSCA_VAZIA_LINK = t("home.busca_vazia_link");

  var ROTULO_FILME_DO_DIA = t("home.rotulo_filme_do_dia");
  var ROTULO_ABRIR = t("home.rotulo_abrir");
  var ROTULO_RECEM = t("home.rotulo_recem");
  var ROTULO_RECEM_TODOS = t("home.rotulo_recem_todos");

  // [rodada editorial] cabeçalho, coleção do dia e o link final
  var NOME_SITE = t("home.nome_site");
  var LINK_FILMES = t("home.link_filmes");
  var LINK_METODO = t("home.link_metodo");
  var ROTULO_COLECAO = t("home.rotulo_colecao");
  var ROTULO_COLECAO_TODOS = t("home.rotulo_colecao_todos");

  // [rodada Explorar] o bloco Explorar da home e a página /filmes
  var TITULO_EXPLORAR = t("home.titulo_explorar");
  var ROTULO_GRUPO_EXPLORAR = {
    assunto: t("home.grupo_explorar.assunto"), decada: t("home.grupo_explorar.decada"),
    genero: t("home.grupo_explorar.genero"), pais: t("home.grupo_explorar.pais"),
  };
  var RESUMO_EXPLORAR = t("home.resumo_explorar");
  var LINK_INDICE = t("home.link_indice");
  var VISTA_GRADE = t("home.vista_grade");
  var VISTA_INDICE = t("home.vista_indice");
  var MOSTRAR_MAIS = t("home.mostrar_mais");
  var FILTRO_VAZIO = t("home.filtro_vazio");
  var LIMPAR_FILTROS = t("home.limpar_filtros");
  var REMOVER_FILTRO = t("home.remover_filtro");
  var QUALQUER = {
    colecao: t("home.qualquer.colecao"), decada: t("home.qualquer.decada"),
    genero: t("home.qualquer.genero"), pais: t("home.qualquer.pais"),
  };
  function contadorDaPagina(mostrados, total) {
    return t("home.contador", { mostrados: mostrados, total: total });
  }
  function chipDesde(dia) {
    var p = dia.split("-");
    return t("home.chip_desde", { a: p[0], m: p[1], d: p[2] });
  }

  // [home semanal] A seleção da década: título e linha FIXOS. Os únicos
  // algarismos são os da própria década (o dado do bloco, como o ano no
  // título de um filme); `decada` é o primeiro ano (1990).
  function tituloDaDecada(decada) { return t("home.titulo_decada", { decada: decada }); }
  function descricaoDaDecada(decada) {
    return t("home.descricao_decada", { ini: decada, fim: decada + 9 });
  }

  // Descrição FIXA de cada eixo, para o bloco de texto da coleção do dia.
  // Diz o que o assunto É, nunca como os grupos o julgam.
  var DESCRICAO_EIXO = porEixo("home.descricao_eixo.");

  // Frase FIXA de cada tipo de coleção (selecao.js: "divisao" | "valorativa").
  var FRASE_TIPO = {
    divisao: t("home.frase_tipo.divisao"),
    valorativa: t("home.frase_tipo.valorativa"),
  };

  // Países (ISO 3166-1) pelo nome no idioma da página, no máximo
  // MAX_PAISES, na ordem do TMDB. Sem `Intl.DisplayNames`, fica o código.
  var MAX_PAISES = 2;
  var nomesDeRegiao = null;
  try {
    nomesDeRegiao = new Intl.DisplayNames([I.idioma === "en" ? "en" : "pt-BR"], { type: "region" });
  } catch (e) { nomesDeRegiao = null; }

  function nomeDoPais(c) {
    var nome = null;
    try { nome = nomesDeRegiao && nomesDeRegiao.of(c); } catch (e) { nome = null; }
    return nome || c;
  }

  function nomesDosPaises(codigos) {
    return (codigos || []).slice(0, MAX_PAISES).map(nomeDoPais);
  }

  // A linha de metadado da manchete, em PARTES ({tipo, texto}): título
  // brasileiro (quando `comTitulo` — ver `tituloNaLinha`, selecao.js),
  // diretor, país(es) e ano. As partes deixam a apresentação marcar o
  // diretor (negrito no formato MUBI da prova de fontes) sem refazer a
  // regra; o texto corrido é `linhaDaManchete`.
  var SEPARADOR = " · ";

  function partesDaManchete(filme, comTitulo) {
    var partes = [];
    if (comTitulo && filme.titulo) partes.push({ tipo: "titulo", texto: filme.titulo });
    if (filme.diretor) partes.push({ tipo: "diretor", texto: filme.diretor });
    var paises = nomesDosPaises(filme.paises);
    if (paises.length) partes.push({ tipo: "paises", texto: paises.join(", ") });
    if (filme.ano) partes.push({ tipo: "ano", texto: String(filme.ano) });
    return partes;
  }

  // [página do filme] A linha de metadado do TOPO da página do filme, no
  // formato MUBI: as partes da manchete (título brasileiro quando
  // `comTitulo`, diretor, país(es), ano) e mais gênero(s) (até MAX_GENEROS)
  // e duração. A duração não está no índice: vem da ficha (`duracaoMin`).
  var MAX_GENEROS = 2;

  function partesDaFicha(filme, duracaoMin, comTitulo) {
    var partes = partesDaManchete(filme, comTitulo);
    var generos = (filme.generos || []).slice(0, MAX_GENEROS);
    if (generos.length) partes.push({ tipo: "generos", texto: generos.map(function (g) {
      var h = root.ESPECTRO_EN_HOME;
      return (h && h.vocabulario_generos && h.vocabulario_generos[g]) || g;
    }).join(", ") });
    if (duracaoMin) partes.push({ tipo: "duracao", texto: t("home.min", { n: duracaoMin }) });
    return partes;
  }

  function juntar(partes) {
    return partes.map(function (p) { return p.texto; }).join(SEPARADOR);
  }

  // "Diretor · País(es) · Ano", com o título brasileiro no início quando
  // `comTitulo`.
  function linhaDaManchete(filme, comTitulo) { return juntar(partesDaManchete(filme, comTitulo)); }

  // "Diretor · Ano", sob o still dos recém-chegados.
  function partesDiretorAno(filme) {
    var partes = [];
    if (filme.diretor) partes.push({ tipo: "diretor", texto: filme.diretor });
    if (filme.ano) partes.push({ tipo: "ano", texto: String(filme.ano) });
    return partes;
  }

  function linhaDiretorAno(filme) { return juntar(partesDiretorAno(filme)); }

  // O eixo em português legível, SEM artigo — os templates o usam depois de
  // dois-pontos, o que dispensa concordância de gênero e número.
  var EIXO_NOME = porEixo("home.eixo_nome.");

  // Títulos das prateleiras: fixos, neutros, um por chave de prateleira
  // (selecao.js). As de DIVISÃO têm a chave do eixo; as VALORATIVAS,
  // "valorativo:" + o eixo do assunto comum. Nenhum título diz quem fala
  // mais, nem quem gosta mais.
  var TITULO_PRATELEIRA = {};
  EIXOS.forEach(function (e) {
    TITULO_PRATELEIRA[e] = t("home.prateleira." + e);
    TITULO_PRATELEIRA["valorativo:" + e] = t("home.prateleira.valorativo:" + e);
  });

  var ORDEM_EIXOS = EIXOS;

  function eixoQueMaisDivide(filme) {
    var melhor = null;
    (filme.eixos_acima || []).forEach(function (e) {
      if (!Object.prototype.hasOwnProperty.call(EIXO_NOME, e.eixo)) return;
      if (!melhor || e.lift_pp > melhor.lift_pp
          || (e.lift_pp === melhor.lift_pp
              && ORDEM_EIXOS.indexOf(e.eixo) < ORDEM_EIXOS.indexOf(melhor.eixo))) {
        melhor = e;
      }
    });
    return melhor;
  }

  // `semTitulo`: [rodada 4] quando o gancho de conteúdo vem DEPOIS da
  // frase de aniversário, que já nomeou o filme, a abertura troca o título
  // por "Nele" / "Está" (os ganchos abrem com "{título}:", sem preposição
  // antes do título — "Em" + "Em Chamas" dava "Em Em Chamas") — o resto do texto é idêntico. Sem aniversário, os
  // textos são exatamente os da rodada 3.
  var TEMPLATES = {
    aniversario: function (titulo) {
      return t("home.tpl.aniversario", { t: titulo });
    },
    eixo: function (titulo, eixo, semTitulo) {
      return t("home.tpl.eixo", {
        abre: t(semTitulo ? "home.tpl.eixo_abre_sem" : "home.tpl.eixo_abre", { t: titulo }),
        grupos: TRES_GRUPOS, eixo: EIXO_NOME[eixo] });
    },
    valorativo: function (titulo, eixo, semTitulo) {
      return t("home.tpl.valorativo", {
        abre: t(semTitulo ? "home.tpl.eixo_abre_sem" : "home.tpl.eixo_abre", { t: titulo }),
        grupos: TRES_GRUPOS, eixo: EIXO_NOME[eixo] });
    },
    generico: function (titulo, semTitulo) {
      return t("home.tpl.generico", {
        abre: t(semTitulo ? "home.tpl.generico_abre_sem" : "home.tpl.generico_abre", { t: titulo }),
        grupos: TRES_GRUPOS });
    },
  };

  // Ganchos 2 a 4: o que o filme TEM, independente da data.
  function ganchoDeConteudo(filme, semTitulo) {
    var tit = filme.titulo || filme.slug;
    var e = eixoQueMaisDivide(filme);
    if (e) return { gancho: "eixo", eixo: e.eixo, texto: TEMPLATES.eixo(tit, e.eixo, semTitulo) };
    var a = filme.assunto_comum;
    if (filme.contraste === "valorativo"
        && Object.prototype.hasOwnProperty.call(EIXO_NOME, a)) {
      return { gancho: "valorativo", eixo: a, texto: TEMPLATES.valorativo(tit, a, semTitulo) };
    }
    return { gancho: "generico", eixo: null, texto: TEMPLATES.generico(tit, semTitulo) };
  }

  // A regra (dia e mês, ano posterior, 29/02, 01/01 nunca) é a de
  // selecao.js; reexportada aqui por compatibilidade.
  var fazAniversario = S.fazAniversario;

  // → { gancho, gancho_conteudo, eixo, texto }. Sem `dia`, só conteúdo.
  function justificar(filme, dia) {
    var aniv = fazAniversario(filme.estreia, dia);
    var c = ganchoDeConteudo(filme, aniv);
    var r = { gancho: c.gancho, gancho_conteudo: c.gancho, eixo: c.eixo, texto: c.texto };
    if (aniv) {
      r.gancho = "aniversario";
      r.texto = TEMPLATES.aniversario(filme.titulo || filme.slug) + " " + c.texto;
    }
    return r;
  }

  function tituloDaPrateleira(chave) { return TITULO_PRATELEIRA[chave] || chave; }

  // O texto da coleção do dia: título (o da prateleira, já aprovado),
  // descrição fixa do eixo e frase fixa do tipo.
  function textoDaColecao(colecao) {
    return { titulo: tituloDaPrateleira(colecao.chave),
             descricao: DESCRICAO_EIXO[colecao.eixo] || "",
             frase: FRASE_TIPO[colecao.tipo] || "" };
  }

  var api = {
    GRUPOS: GRUPOS, PREMISSA: PREMISSA, AVISO_CATALOGO: AVISO_CATALOGO,
    AVISO_LINK: AVISO_LINK, BUSCA_PLACEHOLDER: BUSCA_PLACEHOLDER,
    BUSCA_VAZIA: BUSCA_VAZIA, BUSCA_VAZIA_LINK: BUSCA_VAZIA_LINK,
    ROTULO_FILME_DO_DIA: ROTULO_FILME_DO_DIA, ROTULO_ABRIR: ROTULO_ABRIR,
    ROTULO_RECEM: ROTULO_RECEM, ROTULO_RECEM_TODOS: ROTULO_RECEM_TODOS, EIXO_NOME: EIXO_NOME,
    TITULO_PRATELEIRA: TITULO_PRATELEIRA, eixoQueMaisDivide: eixoQueMaisDivide,
    fazAniversario: fazAniversario, justificar: justificar, tituloDaPrateleira: tituloDaPrateleira,
    NOME_SITE: NOME_SITE, LINK_FILMES: LINK_FILMES, LINK_METODO: LINK_METODO,
    ROTULO_COLECAO: ROTULO_COLECAO, ROTULO_COLECAO_TODOS: ROTULO_COLECAO_TODOS,
    DESCRICAO_EIXO: DESCRICAO_EIXO, FRASE_TIPO: FRASE_TIPO,
    MAX_PAISES: MAX_PAISES, nomesDosPaises: nomesDosPaises, nomeDoPais: nomeDoPais,
    TITULO_EXPLORAR: TITULO_EXPLORAR, RESUMO_EXPLORAR: RESUMO_EXPLORAR,
    tituloDaDecada: tituloDaDecada, descricaoDaDecada: descricaoDaDecada, ROTULO_GRUPO_EXPLORAR: ROTULO_GRUPO_EXPLORAR,
    LINK_INDICE: LINK_INDICE, VISTA_GRADE: VISTA_GRADE, VISTA_INDICE: VISTA_INDICE,
    MOSTRAR_MAIS: MOSTRAR_MAIS, FILTRO_VAZIO: FILTRO_VAZIO, LIMPAR_FILTROS: LIMPAR_FILTROS,
    REMOVER_FILTRO: REMOVER_FILTRO, QUALQUER: QUALQUER,
    contadorDaPagina: contadorDaPagina, chipDesde: chipDesde,
    linhaDaManchete: linhaDaManchete, linhaDiretorAno: linhaDiretorAno,
    partesDaManchete: partesDaManchete, partesDiretorAno: partesDiretorAno,
    partesDaFicha: partesDaFicha, MAX_GENEROS: MAX_GENEROS,
    SEPARADOR: SEPARADOR,
    textoDaColecao: textoDaColecao,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_TEXTOS = api;
})(this);
