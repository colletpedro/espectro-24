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
     a) `eixo`       — o filme tem eixo acima da margem de lift: usa o de
                       maior lift_pp (empate: o primeiro na ordem da
                       taxonomia).
     b) `valorativo` — `contraste: valorativo`: os grupos falam dos mesmos
                       assuntos e discordam do valor.
     c) `generico`   — nenhum dos dois (hoje: filme abaixo do piso do
                       estado de contraste). */
(function (root) {
  "use strict";

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

  // Títulos das prateleiras: fixos, neutros, um por chave de
  // `ORDEM_PRATELEIRAS` (selecao.js). Nenhum diz quem fala mais.
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
    valorativo: "Mesmos assuntos, vereditos diferentes",
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

  var TEMPLATES = {
    eixo: function (t, eixo) {
      return "Em " + t + ", " + TRES_GRUPOS + " se afastam sobretudo num "
        + "assunto: " + EIXO_NOME[eixo] + ". Um dos grupos fala disso bem "
        + "mais que os outros dois — a página mostra qual, e com que palavras.";
    },
    valorativo: function (t) {
      return "Em " + t + ", nenhum assunto separa " + TRES_GRUPOS + ": os "
        + "três grupos falam das mesmas coisas. A diferença está no valor que "
        + "cada um dá ao filme, não num aspecto específico.";
    },
    generico: function (t) {
      return t + " está no catálogo com o que " + TRES_GRUPOS + " dizem "
        + "sobre ele. A página mostra os assuntos de cada grupo lado a lado, "
        + "cada um com as próprias palavras.";
    },
  };

  // → { gancho: "eixo"|"valorativo"|"generico", eixo: string|null, texto }
  function justificar(filme) {
    var t = filme.titulo || filme.slug;
    var e = eixoQueMaisDivide(filme);
    if (e) return { gancho: "eixo", eixo: e.eixo, texto: TEMPLATES.eixo(t, e.eixo) };
    if (filme.contraste === "valorativo") {
      return { gancho: "valorativo", eixo: null, texto: TEMPLATES.valorativo(t) };
    }
    return { gancho: "generico", eixo: null, texto: TEMPLATES.generico(t) };
  }

  function tituloDaPrateleira(chave) { return TITULO_PRATELEIRA[chave] || chave; }

  var api = {
    GRUPOS: GRUPOS, PREMISSA: PREMISSA, AVISO_CATALOGO: AVISO_CATALOGO,
    AVISO_LINK: AVISO_LINK, BUSCA_PLACEHOLDER: BUSCA_PLACEHOLDER,
    BUSCA_VAZIA: BUSCA_VAZIA, BUSCA_VAZIA_LINK: BUSCA_VAZIA_LINK,
    ROTULO_FILME_DO_DIA: ROTULO_FILME_DO_DIA, ROTULO_ABRIR: ROTULO_ABRIR,
    ROTULO_RECEM: ROTULO_RECEM, EIXO_NOME: EIXO_NOME,
    TITULO_PRATELEIRA: TITULO_PRATELEIRA, eixoQueMaisDivide: eixoQueMaisDivide,
    justificar: justificar, tituloDaPrateleira: tituloDaPrateleira,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_TEXTOS = api;
})(this);
