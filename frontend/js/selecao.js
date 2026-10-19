/* Espectro 24 — selecao.js
   O QUE a home mostra em cada dia: filme do dia, prateleiras e
   recém-chegados. Funções puras sobre o índice (`js/indice.js`), sem DOM e
   sem relógio próprio — a data entra como argumento, e é por isso que os
   testes conseguem fixar o dia (ver `tests/test_home_nova.py`).

   NENHUMA seleção ou ordenação aqui lê a distribuição dos grupos
   (`distribuicao`) — o teste embaralha esse campo e confere que nada muda.

   ---------------------------------------------------------------------
   FILME DO DIA — a regra, por extenso
   ---------------------------------------------------------------------
   1. O DIA é a data civil em America/Sao_Paulo (`diaEmSaoPaulo`): todo
      visitante, em qualquer fuso, vê o mesmo filme no mesmo dia de lá.
   2. ELEGÍVEIS: os filmes do índice menos `EXCLUIDOS`.
   3. A PERMUTAÇÃO é fixa: os elegíveis ordenados por FNV-1a 32 bits de
      `SEMENTE + "|" + slug` (empate, que é improvável, pelo slug). A
      semente é constante e versionada aqui; trocá-la reembaralha tudo.
   4. O ÍNDICE do dia é `dias desde EPOCA, módulo N` (N = nº de elegíveis).
      Em N dias seguidos com a lista parada, cada filme aparece exatamente
      uma vez: nenhum repete antes de o ciclo completo passar.
   5. QUANDO A LISTA MUDA (filme novo, filme excluído): a ordem RELATIVA
      dos que já estavam não muda — ordenar por hash não depende de quem
      mais está na lista; o novo só ocupa a posição do hash dele. Mas N
      mudou, e o índice do dia passa a ser calculado sobre a lista nova a
      partir do dia em que ela é publicada. O ciclo em curso é ABANDONADO
      nesse dia: alguns filmes dele podem reaparecer antes do previsto e
      outros podem ser adiados. Daí em diante vale um ciclo completo novo,
      sem repetição, enquanto a lista não mudar de novo. Continua 100%
      determinístico: mesma lista + mesma data → mesmo filme.

   ---------------------------------------------------------------------
   PRATELEIRAS
   ---------------------------------------------------------------------
   · DE DIVISÃO ("Onde X divide"): uma por eixo da taxonomia, com os
     filmes em que AQUELE eixo passa a margem de lift (`eixos_acima`).
   · VALORATIVAS ("Todos falam de X, ninguém concorda"): uma por eixo, com
     os filmes `contraste: valorativo` cujo assunto comum dominante
     (`assunto_comum`, `build_indice.py`) é aquele eixo. Substituem a
     prateleira valorativa única da rodada 1, que tinha 79 filmes.
   · Piso: só existe prateleira com >= PISO_PRATELEIRA filmes elegíveis.
     Filme de eixo abaixo do piso simplesmente não aparece em prateleira.
   · Dentro da prateleira: ordem ALFABÉTICA pelo título exibido
     normalizado (artigo inicial ignorado), empate pelo slug — a mesma
     regra para todas. Descartado: ordenar pela magnitude do lift (mede
     contraste, não qualidade, mas pede explicação que a prateleira não tem
     onde dar).
   · Ordem das prateleiras no dia d (d = dias desde EPOCA, o mesmo
     contador do filme do dia), com D = as de divisão e V = as valorativas,
     cada lista na ordem da taxonomia:
       1. cada lista é ROTACIONADA sozinha: D começa na posição (d mod |D|)
          e V na posição (d mod |V|);
       2. as duas são INTERCALADAS de forma PROPORCIONAL, começando por D
          em dia par e por V em dia ímpar: a cada posição entra o tipo que
          está mais ATRASADO na sua própria lista (fração já usada menor;
          empate, o tipo que abre o dia). Com tamanhos iguais isso é a
          alternância simples; com 10 valorativas e 4 de divisão, cada
          divisão vem depois de duas ou três valorativas, e nenhuma
          sequência de um tipo só passa de ceil(maior / menor) seguidas.
          Descartado (versão anterior desta rodada): alternar um a um e
          despejar o resto no fim — com 10 contra 4, a home terminava com
          seis valorativas seguidas.
     A home não fica idêntica todo dia, não abre com uma sequência de um
     tipo só, e qualquer um pode reproduzir a ordem de uma data.

   RECÉM-CHEGADOS: os filmes da data de entrada mais recente do registro
   (`entrada`); se essa leva tiver menos que o piso, entram as levas
   anteriores até alcançá-lo. Em ordem alfabética, cortados em
   LIMITE_RECEM (12); `total` diz quantos a leva tem, para o link "ver
   todos" (que abre /filmes?desde=<data>). */
(function (root) {
  "use strict";

  var B = (typeof module !== "undefined" && module.exports)
    ? require("./busca.js") : root.ESPECTRO_BUSCA;

  var SEMENTE = "espectro24/filme-do-dia/v1";
  var EPOCA = "2026-01-01";
  var FUSO = "America/Sao_Paulo";

  /* Fora do filme do dia, das prateleiras e dos recém-chegados — mas
     continuam na busca e em /filmes. Cada entrada com o motivo.
     `obsession-2025` por decisão do dono na aprovação da home nova
     (2026-10-19). O pedido original nomeava `obsession-2026`, que já não
     está no catálogo desde a v1.9.50 (C13: era a página do curta) — com ele
     a lista não excluía filme nenhum. */
  var EXCLUIDOS = {
    "obsession-2025": "corpus contaminado, decisão pendente",
  };

  var PISO_PRATELEIRA = 3;

  var LIMITE_RECEM = 12;

  // A taxonomia fechada, na ordem de `eixos.linhas`.
  var ORDEM_EIXOS = [
    "ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura", "som_trilha",
    "tom_atmosfera", "impacto_emocional", "comparacoes", "expectativa",
    "critica_social",
  ];

  var PREFIXO_VALORATIVA = "valorativo:";

  var MS_DIA = 86400000;

  // A data civil (AAAA-MM-DD) em São Paulo para um instante.
  function diaEmSaoPaulo(instante) {
    var partes = new Intl.DateTimeFormat("en-CA", {
      timeZone: FUSO, year: "numeric", month: "2-digit", day: "2-digit",
    }).formatToParts(instante);
    var v = {};
    partes.forEach(function (p) { v[p.type] = p.value; });
    return v.year + "-" + v.month + "-" + v.day;
  }

  function utcDoDia(dia) {
    var p = dia.split("-").map(Number);
    return Date.UTC(p[0], p[1] - 1, p[2]);
  }

  function diasDesdeEpoca(dia) {
    return Math.round((utcDoDia(dia) - utcDoDia(EPOCA)) / MS_DIA);
  }

  function modulo(a, n) { return ((a % n) + n) % n; }

  // FNV-1a, 32 bits. Escolhido por ser curto, conhecido e idêntico em
  // qualquer motor JS (só usa Math.imul e >>> 0).
  function fnv1a(texto) {
    var h = 0x811c9dc5;
    for (var i = 0; i < texto.length; i++) {
      h ^= texto.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  function elegiveis(filmes) {
    return (filmes || []).filter(function (f) {
      return !Object.prototype.hasOwnProperty.call(EXCLUIDOS, f.slug);
    });
  }

  function permutacao(filmes) {
    return filmes.map(function (f) {
      return { f: f, h: fnv1a(SEMENTE + "|" + f.slug) };
    }).sort(function (a, b) {
      return (a.h - b.h) || B.comparar(a.f.slug, b.f.slug);
    }).map(function (x) { return x.f; });
  }

  // `dia` é AAAA-MM-DD já em São Paulo; `filmeDoDiaEm` aceita um instante.
  function filmeDoDia(filmes, dia) {
    var lista = permutacao(elegiveis(filmes));
    if (!lista.length) return null;
    return lista[modulo(diasDesdeEpoca(dia), lista.length)];
  }

  function filmeDoDiaEm(filmes, instante) {
    return filmeDoDia(filmes, diaEmSaoPaulo(instante));
  }

  function membrosDaDivisao(eixo, filmes) {
    return filmes.filter(function (f) {
      return (f.eixos_acima || []).some(function (e) { return e.eixo === eixo; });
    });
  }

  function membrosDaValorativa(eixo, filmes) {
    return filmes.filter(function (f) {
      return f.contraste === "valorativo" && f.assunto_comum === eixo;
    });
  }

  function doTipo(tipo, filmes) {
    var lista = elegiveis(filmes);
    var saida = [];
    ORDEM_EIXOS.forEach(function (eixo) {
      var membros = tipo === "divisao" ? membrosDaDivisao(eixo, lista)
        : membrosDaValorativa(eixo, lista);
      if (membros.length >= PISO_PRATELEIRA) {
        saida.push({
          chave: tipo === "divisao" ? eixo : PREFIXO_VALORATIVA + eixo,
          tipo: tipo, eixo: eixo, filmes: B.ordenarAlfabetico(membros),
        });
      }
    });
    return saida;
  }

  // Todas as prateleiras que passam o piso, sem rotação: divisão, depois
  // valorativas, cada grupo na ordem da taxonomia.
  function prateleirasBase(filmes) {
    return doTipo("divisao", filmes).concat(doTipo("valorativa", filmes));
  }

  function girar(lista, d) {
    if (!lista.length) return lista;
    var k = modulo(d, lista.length);
    return lista.slice(k).concat(lista.slice(0, k));
  }

  function prateleiras(filmes, dia) {
    var d = diasDesdeEpoca(dia);
    var D = girar(doTipo("divisao", filmes), d);
    var V = girar(doTipo("valorativa", filmes), d);
    var vez = modulo(d, 2) === 0 ? [D, V] : [V, D];
    var A = vez[0], Z = vez[1];
    var saida = [];
    var ia = 0, iz = 0;
    // `ia / |A| <= iz / |Z|`, em inteiros: A entra quando não está à frente.
    while (ia < A.length || iz < Z.length) {
      if (iz >= Z.length || (ia < A.length && ia * Z.length <= iz * A.length)) {
        saida.push(A[ia++]);
      } else {
        saida.push(Z[iz++]);
      }
    }
    return saida;
  }

  function recemChegados(filmes, piso) {
    piso = piso || PISO_PRATELEIRA;
    var lista = elegiveis(filmes).filter(function (f) { return !!f.entrada; });
    var datas = lista.map(function (f) { return f.entrada; })
      .filter(function (d, i, a) { return a.indexOf(d) === i; })
      .sort().reverse();
    var escolhidos = [];
    var ultima = null;
    for (var i = 0; i < datas.length && escolhidos.length < piso; i++) {
      ultima = datas[i];
      escolhidos = escolhidos.concat(lista.filter(function (f) {
        return f.entrada === datas[i];
      }));
    }
    if (escolhidos.length < piso) return null;
    return { desde: ultima, ate: datas[0], total: escolhidos.length,
             filmes: B.ordenarAlfabetico(escolhidos).slice(0, LIMITE_RECEM) };
  }

  var api = {
    SEMENTE: SEMENTE, EPOCA: EPOCA, FUSO: FUSO, EXCLUIDOS: EXCLUIDOS,
    PISO_PRATELEIRA: PISO_PRATELEIRA, LIMITE_RECEM: LIMITE_RECEM,
    ORDEM_EIXOS: ORDEM_EIXOS, PREFIXO_VALORATIVA: PREFIXO_VALORATIVA,
    diaEmSaoPaulo: diaEmSaoPaulo, diasDesdeEpoca: diasDesdeEpoca,
    fnv1a: fnv1a, elegiveis: elegiveis, permutacao: permutacao,
    filmeDoDia: filmeDoDia, filmeDoDiaEm: filmeDoDiaEm,
    prateleirasBase: prateleirasBase, prateleiras: prateleiras,
    recemChegados: recemChegados,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_SELECAO = api;
})(this);
