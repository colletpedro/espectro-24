/* Espectro 24 — textos_home.js
   TODA a prosa da home num arquivo só: a premissa, os títulos das
   prateleiras, o aviso de catálogo, a mensagem de busca vazia e os
   TEMPLATES da justificativa do filme do dia. Nada aqui chama LLM, em build
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

  // Os rótulos que o site já usa (`GRUPO_LABEL` em filme.js), na ordem
  // de leitura dele.
  var GRUPOS = ["HATERS", "MIXED", "FANS"];
  var TRES_GRUPOS = "HATERS, MIXED e FANS";

  var PREMISSA = "Como " + TRES_GRUPOS + " veem cada filme — cada grupo "
    + "com as próprias palavras, lado a lado, sem nota e sem spoiler.";

  var AVISO_CATALOGO = "O catálogo cresce com o tempo: novos filmes são "
    + "adicionados aos poucos.";
  var AVISO_LINK = "Ver todos os filmes";

  var BUSCA_PLACEHOLDER = "Buscar filme por título ou ano";
  var BUSCA_VAZIA = "Esse filme ainda não está no catálogo. Novos filmes "
    + "chegam com o tempo.";
  var BUSCA_VAZIA_LINK = "Ver o catálogo completo";

  var ROTULO_FILME_DO_DIA = "Filme do dia";
  var ROTULO_ABRIR = "Abrir a análise";
  var ROTULO_RECEM = "Recém-chegados";
  var ROTULO_RECEM_TODOS = "Ver todos os recém-chegados";

  // O eixo em português legível, SEM artigo — os templates o usam depois de
  // dois-pontos, o que dispensa concordância de gênero e número.
  var EIXO_NOME = {
    ritmo: "ritmo",
    atuacao: "atuação",
    direcao_imagem: "direção e imagem",
    roteiro_estrutura: "roteiro e estrutura",
    som_trilha: "som e trilha",
    tom_atmosfera: "tom e atmosfera",
    impacto_emocional: "impacto emocional",
    comparacoes: "comparações com outros filmes",
    expectativa: "expectativa",
    critica_social: "crítica social",
  };

  // Títulos das prateleiras: fixos, neutros, um por chave de prateleira
  // (selecao.js). As de DIVISÃO têm a chave do eixo; as VALORATIVAS,
  // "valorativo:" + o eixo do assunto comum. Nenhum título diz quem fala
  // mais, nem quem gosta mais.
  var TITULO_PRATELEIRA = {
    ritmo: "Onde o ritmo divide",
    atuacao: "Onde a atuação divide",
    direcao_imagem: "Onde a direção e a imagem dividem",
    roteiro_estrutura: "Onde o roteiro divide",
    som_trilha: "Onde o som e a trilha dividem",
    tom_atmosfera: "Onde o tom e a atmosfera dividem",
    impacto_emocional: "Onde o impacto emocional divide",
    comparacoes: "Onde as comparações dividem",
    expectativa: "Onde a expectativa divide",
    critica_social: "Onde a crítica social divide",
    "valorativo:ritmo": "Todos falam do ritmo, ninguém concorda",
    "valorativo:atuacao": "Todos falam da atuação, ninguém concorda",
    "valorativo:direcao_imagem": "Todos falam da direção e da imagem, ninguém concorda",
    "valorativo:roteiro_estrutura": "Todos falam do roteiro, ninguém concorda",
    "valorativo:som_trilha": "Todos falam do som e da trilha, ninguém concorda",
    "valorativo:tom_atmosfera": "Todos falam do tom e da atmosfera, ninguém concorda",
    "valorativo:impacto_emocional": "Todos falam do impacto emocional, ninguém concorda",
    "valorativo:comparacoes": "Todos fazem comparações, ninguém concorda",
    "valorativo:expectativa": "Todos falam da expectativa, ninguém concorda",
    "valorativo:critica_social": "Todos falam da crítica social, ninguém concorda",
  };

  var ORDEM_EIXOS = [
    "ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura", "som_trilha",
    "tom_atmosfera", "impacto_emocional", "comparacoes", "expectativa",
    "critica_social",
  ];

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
  // por "Nele" / "Está" — o resto do texto é idêntico. Sem aniversário, os
  // textos são exatamente os da rodada 3.
  var TEMPLATES = {
    aniversario: function (t) {
      return t + " faz aniversário de estreia hoje.";
    },
    eixo: function (t, eixo, semTitulo) {
      return (semTitulo ? "Nele" : "Em " + t) + ", " + TRES_GRUPOS
        + " se afastam sobretudo num "
        + "assunto: " + EIXO_NOME[eixo] + ". Um dos grupos fala disso bem "
        + "mais que os outros dois — a página mostra qual, e com que palavras.";
    },
    valorativo: function (t, eixo, semTitulo) {
      return (semTitulo ? "Nele" : "Em " + t)
        + ", um assunto aparece mais do que o habitual no "
        + "catálogo, somando " + TRES_GRUPOS + ": " + EIXO_NOME[eixo] + ". Os "
        + "três grupos falam dele e chegam a vereditos diferentes — o que muda "
        + "é o valor que cada um dá ao filme, não o tema da conversa.";
    },
    generico: function (t, semTitulo) {
      return (semTitulo ? "Está" : t + " está") + " no catálogo com o que "
        + TRES_GRUPOS + " dizem "
        + "sobre ele. A página mostra os assuntos de cada grupo lado a lado, "
        + "cada um com as próprias palavras.";
    },
  };

  // Ganchos 2 a 4: o que o filme TEM, independente da data.
  function ganchoDeConteudo(filme, semTitulo) {
    var t = filme.titulo || filme.slug;
    var e = eixoQueMaisDivide(filme);
    if (e) return { gancho: "eixo", eixo: e.eixo, texto: TEMPLATES.eixo(t, e.eixo, semTitulo) };
    var a = filme.assunto_comum;
    if (filme.contraste === "valorativo"
        && Object.prototype.hasOwnProperty.call(EIXO_NOME, a)) {
      return { gancho: "valorativo", eixo: a, texto: TEMPLATES.valorativo(t, a, semTitulo) };
    }
    return { gancho: "generico", eixo: null, texto: TEMPLATES.generico(t, semTitulo) };
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

  var api = {
    GRUPOS: GRUPOS, PREMISSA: PREMISSA, AVISO_CATALOGO: AVISO_CATALOGO,
    AVISO_LINK: AVISO_LINK, BUSCA_PLACEHOLDER: BUSCA_PLACEHOLDER,
    BUSCA_VAZIA: BUSCA_VAZIA, BUSCA_VAZIA_LINK: BUSCA_VAZIA_LINK,
    ROTULO_FILME_DO_DIA: ROTULO_FILME_DO_DIA, ROTULO_ABRIR: ROTULO_ABRIR,
    ROTULO_RECEM: ROTULO_RECEM, ROTULO_RECEM_TODOS: ROTULO_RECEM_TODOS, EIXO_NOME: EIXO_NOME,
    TITULO_PRATELEIRA: TITULO_PRATELEIRA, eixoQueMaisDivide: eixoQueMaisDivide,
    fazAniversario: fazAniversario, justificar: justificar, tituloDaPrateleira: tituloDaPrateleira,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_TEXTOS = api;
})(this);
