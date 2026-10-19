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
   · Uma por eixo da taxonomia (os filmes em que AQUELE eixo passa a
     margem de lift, `eixos_acima`) e uma para `contraste: valorativo`.
   · Piso: só existe prateleira com >= PISO_PRATELEIRA filmes elegíveis.
   · Dentro da prateleira: ordem ALFABÉTICA pelo título exibido
     normalizado (artigo inicial ignorado), empate pelo slug — a mesma
     regra para todas, inclusive as de eixo. Descartado: ordenar pela
     magnitude do lift (mede contraste, não qualidade, mas pede explicação
     que a prateleira não tem onde dar).
   · Ordem das prateleiras: a ordem da taxonomia (`ORDEM_PRATELEIRAS`),
     ROTACIONADA pelo mesmo contador de dias do filme do dia — no dia d, a
     prateleira de posição (d mod P) abre a lista (P = nº de prateleiras
     que passaram o piso). A home não fica idêntica todo dia, e qualquer
     um pode reproduzir a ordem de uma data.

   RECÉM-CHEGADOS: os filmes da data de entrada mais recente do registro
   (`entrada`), em ordem alfabética; se essa leva tiver menos que o piso,
   entram as levas anteriores até alcançá-lo. */
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

  // A taxonomia fechada, na ordem de `eixos.linhas`, + o estado valorativo.
  var ORDEM_PRATELEIRAS = [
    "ritmo", "atuacao", "direcao_imagem", "roteiro_estrutura", "som_trilha",
    "tom_atmosfera", "impacto_emocional", "comparacoes", "expectativa",
    "critica_social", "valorativo",
  ];

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

  function membrosDa(chave, filmes) {
    return filmes.filter(function (f) {
      if (chave === "valorativo") return f.contraste === "valorativo";
      return (f.eixos_acima || []).some(function (e) { return e.eixo === chave; });
    });
  }

  // Todas as prateleiras que passam o piso, na ordem-base (sem rotação).
  function prateleirasBase(filmes) {
    var lista = elegiveis(filmes);
    var saida = [];
    ORDEM_PRATELEIRAS.forEach(function (chave) {
      var membros = membrosDa(chave, lista);
      if (membros.length >= PISO_PRATELEIRA) {
        saida.push({ chave: chave, filmes: B.ordenarAlfabetico(membros) });
      }
    });
    return saida;
  }

  function prateleiras(filmes, dia) {
    var base = prateleirasBase(filmes);
    if (!base.length) return base;
    var k = modulo(diasDesdeEpoca(dia), base.length);
    return base.slice(k).concat(base.slice(0, k));
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
    return { desde: ultima, ate: datas[0], filmes: B.ordenarAlfabetico(escolhidos) };
  }

  var api = {
    SEMENTE: SEMENTE, EPOCA: EPOCA, FUSO: FUSO, EXCLUIDOS: EXCLUIDOS,
    PISO_PRATELEIRA: PISO_PRATELEIRA, ORDEM_PRATELEIRAS: ORDEM_PRATELEIRAS,
    diaEmSaoPaulo: diaEmSaoPaulo, diasDesdeEpoca: diasDesdeEpoca,
    fnv1a: fnv1a, elegiveis: elegiveis, permutacao: permutacao,
    filmeDoDia: filmeDoDia, filmeDoDiaEm: filmeDoDiaEm,
    prateleirasBase: prateleirasBase, prateleiras: prateleiras,
    recemChegados: recemChegados,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_SELECAO = api;
})(this);
