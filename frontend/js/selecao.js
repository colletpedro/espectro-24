/* Espectro 24 — selecao.js
   O QUE a home mostra em cada dia: a manchete (o filme do dia), a coleção
   do dia e os recém-chegados. Funções puras sobre o índice (`js/indice.js`), sem DOM e
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
   6. [rodada 4] O ANIVERSÁRIO VENCE A PERMUTAÇÃO. Se algum elegível faz
      aniversário de estreia no dia (`fazAniversario`: mesmo dia e mês de
      `estreia`, ano posterior, 29/02 só em ano bissexto, 01/01 NUNCA), ele
      é o filme do dia. Com mais de um aniversariante, vence o que vem
      PRIMEIRO NA PERMUTAÇÃO da lista atual — a mesma ordem do item 3, sem
      critério novo. A permutação NÃO é deslocada: no dia seguinte o índice
      continua sendo `dias mod N`, como se o aniversário não tivesse
      acontecido. Consequências aceitas (decisão do dono): o aniversariante
      pode aparecer de novo pela permutação no mesmo ciclo, e o filme que a
      permutação mostraria no dia do aniversário perde a vez naquele ciclo.
      Substitui a regra da rodada 2 ("o aniversário não altera a seleção"),
      com a qual o gancho não aparecia nenhuma vez em 3 anos.
      `filmeDaPermutacao` continua expondo a regra antiga (itens 3–5) sozinha.

   ANIVERSÁRIO EM 01/01: não conta. O `release_date` 01/01 no TMDB é, na
   prática, data genérica ("só o ano"), não estreia — `the-gentlemen`
   (2020-01-01) é o caso no catálogo de 2026-10-19. A data fica gravada; o
   gancho e a seleção a ignoram.

   ---------------------------------------------------------------------
   COLEÇÕES (rodada editorial: as prateleiras saíram da home e a lógica
   delas virou a das coleções)
   ---------------------------------------------------------------------
   · DE DIVISÃO ("Onde X divide"): uma por eixo da taxonomia, com os
     filmes em que AQUELE eixo passa a margem de lift (`eixos_acima`).
   · VALORATIVAS ("Todos falam de X, ninguém concorda"): uma por eixo, com
     os filmes `contraste: valorativo` cujo assunto comum dominante
     (`assunto_comum`, `build_indice.py`) é aquele eixo.
   · Piso: só existe coleção com >= PISO_PRATELEIRA filmes elegíveis.
   · Dentro da coleção: ordem ALFABÉTICA pelo título exibido normalizado
     (artigo inicial ignorado), empate pelo slug.
   · ORDEM FIXA DAS COLEÇÕES (`ordemDasColecoes`): divisão (D) e valorativa
     (V), cada uma na ordem da taxonomia, INTERCALADAS de forma
     PROPORCIONAL a partir de D: a cada posição entra o tipo mais ATRASADO
     na sua própria lista (fração já usada menor; empate, D). Com 4 de
     divisão e 10 valorativas, nenhuma sequência de um tipo só passa de
     ceil(maior / menor) seguidas — a mesma intercalação das prateleiras
     da rodada 2, agora sem rotação por dia (a rotação é a da coleção do
     dia, abaixo).

   COLEÇÃO DO DIA (`colecaoDoDia`): no dia d (o mesmo contador do filme do
   dia), a coleção de posição (d mod N) na ordem fixa, N = nº de coleções.
   Se ela contém o filme da MANCHETE, a busca SALTA MEIO CICLO: tenta as
   posições (d mod N) + floor(N/2), + floor(N/2) + 1, ... (circular) até a
   primeira que não contém o filme; se todas contêm, fica a de posição
   (d mod N). O salto existe porque avançar uma posição escolheria a
   coleção de amanhã, e a mesma coleção apareceria em dois dias seguidos.
   Em N dias seguidos sem manchete a evitar, cada coleção aparece uma vez.
   FILMES MOSTRADOS: até LIMITE_COLECAO (4). Com mais que isso, uma janela
   circular de 4 sobre a lista alfabética, começando em (d mod tamanho), e
   reordenada alfabeticamente; o "primeiro filme" (o still grande) é o
   primeiro dessa seleção.

   RECÉM-CHEGADOS (`recemChegados`): os filmes da data de entrada mais
   recente do registro (`entrada`); se essa leva tiver menos que o piso,
   entram as levas anteriores até alcançá-lo. Em ordem alfabética, inteira.
   A HOME mostra LIMITE_RECEM (3) por dia (`recemDoDia`): janela circular
   de 3 sobre a leva, começando em (d mod tamanho), em ordem alfabética.
   Antes da janela saem os filmes que já estão na página (manchete e
   coleção), DESDE QUE sobrem pelo menos 3; senão, nada sai.

   LOGO DA MANCHETE (`modoDoLogo`): a classe de contraste FINAL do logo
   (`logo.classe`, build_data.py) decide: `claro` → o logo como está;
   `escuro_mono` → o logo embranquecido por filtro; qualquer outra
   (`escuro_cor`, `desligado`) ou sem logo → o título em texto. E o título
   brasileiro abre a linha de metadado só com logo exibido que não é pt-BR
   e cujo texto, normalizado como na busca, difere dele (`tituloNaLinha`). */
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

  // [rodada editorial] quantos filmes a home mostra da coleção do dia e dos
  // recém-chegados
  var LIMITE_COLECAO = 4;
  var LIMITE_RECEM = 3;

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

  var DATA_RE = /^\d{4}-\d{2}-\d{2}$/;

  // Aniversário de estreia em `dia` (AAAA-MM-DD, São Paulo): mesmo dia e
  // mês, ano posterior ao da estreia. 29/02 só casa com 29/02 (não há
  // aniversário adiado), e 01/01 nunca conta (ver o cabeçalho).
  function fazAniversario(estreia, dia) {
    if (!estreia || !dia || !DATA_RE.test(estreia) || !DATA_RE.test(dia)) return false;
    if (estreia.slice(5) === "01-01") return false;
    return estreia.slice(5) === dia.slice(5) && estreia.slice(0, 4) < dia.slice(0, 4);
  }

  // A regra dos itens 3–5, sozinha: o filme que a permutação dá ao dia.
  function filmeDaPermutacao(filmes, dia) {
    var lista = permutacao(elegiveis(filmes));
    if (!lista.length) return null;
    return lista[modulo(diasDesdeEpoca(dia), lista.length)];
  }

  /* [rodada 4b] CARÊNCIA: o aniversariante só vence a permutação se NÃO
     for o filme da PERMUTAÇÃO em nenhum dia de [dia − C, dia + C] (o
     próprio dia incluso). Calculada sobre `filmeDaPermutacao`, nunca sobre
     `escolhaDoDia` — sem recursão. Aplicada a cada aniversariante ANTES do
     desempate pela ordem da permutação; se nenhum passar, vale a
     permutação. Evita o mesmo filme duas vezes em poucos dias (caso
     medido: Napoleão em 20/11 pela permutação e 22/11 pelo aniversário). */
  var CARENCIA_ANIVERSARIO_DIAS = 14;

  function emCarencia(slug, lista, dia) {
    var d = diasDesdeEpoca(dia);
    for (var k = -CARENCIA_ANIVERSARIO_DIAS; k <= CARENCIA_ANIVERSARIO_DIAS; k++) {
      if (lista[modulo(d + k, lista.length)].slug === slug) return true;
    }
    return false;
  }

  // → { filme, motivo: "aniversario" | "permutacao" }
  function escolhaDoDia(filmes, dia) {
    var lista = permutacao(elegiveis(filmes));
    if (!lista.length) return null;
    for (var i = 0; i < lista.length; i++) {
      if (fazAniversario(lista[i].estreia, dia) && !emCarencia(lista[i].slug, lista, dia)) {
        return { filme: lista[i], motivo: "aniversario" };
      }
    }
    return { filme: lista[modulo(diasDesdeEpoca(dia), lista.length)], motivo: "permutacao" };
  }

  // `dia` é AAAA-MM-DD já em São Paulo; `filmeDoDiaEm` aceita um instante.
  function filmeDoDia(filmes, dia) {
    var e = escolhaDoDia(filmes, dia);
    return e && e.filme;
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

  // Todas as coleções que passam o piso, sem rotação: divisão, depois
  // valorativas, cada grupo na ordem da taxonomia. (O nome é o das
  // prateleiras, de onde a lógica veio; `colecoes` é o mesmo.)
  function prateleirasBase(filmes) {
    return doTipo("divisao", filmes).concat(doTipo("valorativa", filmes));
  }

  // Intercalação PROPORCIONAL de A e Z, começando por A (ver o cabeçalho).
  function intercalar(A, Z) {
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

  function ordemDasColecoes(filmes) {
    return intercalar(doTipo("divisao", filmes), doTipo("valorativa", filmes));
  }

  // Janela circular de `n` itens começando em (d mod tamanho), devolvida na
  // ordem original da lista (que é a alfabética).
  function janelaDoDia(lista, n, d) {
    if (lista.length <= n) return lista.slice();
    var k = modulo(d, lista.length);
    var idx = [];
    for (var i = 0; i < n; i++) idx.push((k + i) % lista.length);
    return idx.sort(function (a, b) { return a - b; })
      .map(function (i) { return lista[i]; });
  }

  function contem(colecao, slug) {
    return colecao.filmes.some(function (f) { return f.slug === slug; });
  }

  // → { colecao, filmes (até LIMITE_COLECAO), total, evitou } ou null.
  // `mancheteSlug` é opcional: sem ele, é o filme do dia de `escolhaDoDia`.
  function colecaoDoDia(filmes, dia, mancheteSlug) {
    var ordem = ordemDasColecoes(filmes);
    if (!ordem.length) return null;
    if (mancheteSlug === undefined) {
      var e = escolhaDoDia(filmes, dia);
      mancheteSlug = e && e.filme.slug;
    }
    var d = diasDesdeEpoca(dia);
    var n = ordem.length;
    var k0 = modulo(d, n);
    var escolhida = ordem[k0];
    if (mancheteSlug && contem(escolhida, mancheteSlug)) {
      var salto = Math.floor(n / 2);
      for (var j = 0; j < n; j++) {
        var c = ordem[(k0 + salto + j) % n];
        if (c !== ordem[k0] && !contem(c, mancheteSlug)) { escolhida = c; break; }
      }
    }
    return { colecao: escolhida, filmes: janelaDoDia(escolhida.filmes, LIMITE_COLECAO, d),
             total: escolhida.filmes.length, evitou: escolhida !== ordem[k0] };
  }

  function modoDoLogo(filme) {
    var logo = filme && filme.logo;
    if (!logo || !logo.path) return "texto";
    if (logo.classe === "claro") return "logo";
    if (logo.classe === "escuro_mono") return "logo_branco";
    return "texto";
  }

  // O título brasileiro abre a linha de metadado da manchete só quando o
  // LOGO EXIBIDO não é o pt-BR (`modoDoLogo` != "texto" e
  // `titulo_difere_do_logo`) E [rodada editorial 2] o que o logo escreve
  // (`logo.titulo`), normalizado como na busca (`B.normalizar`: caixa,
  // acentos, pontuação, artigos iniciais), é DIFERENTE do título
  // brasileiro — "Aftersun" no logo e "Aftersun" no título não se repetem.
  // Sem `logo.titulo`, conta como diferente (o título aparece). Com o
  // título em texto, ele já está na tela.
  function tituloNaLinha(filme) {
    if (modoDoLogo(filme) === "texto" || !filme.titulo_difere_do_logo) return false;
    return B.normalizar(filme.titulo || "") !== B.normalizar(filme.logo.titulo || "");
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
             filmes: B.ordenarAlfabetico(escolhidos) };
  }

  // Os LIMITE_RECEM do dia (ver o cabeçalho). `evitar`: slugs já na página.
  function recemDoDia(filmes, dia, evitar) {
    var r = recemChegados(filmes);
    if (!r) return null;
    var fora = {};
    (evitar || []).forEach(function (s) { fora[s] = true; });
    var resto = r.filmes.filter(function (f) { return !fora[f.slug]; });
    var pool = resto.length >= LIMITE_RECEM ? resto : r.filmes;
    return { desde: r.desde, ate: r.ate, total: r.total,
             filmes: janelaDoDia(pool, LIMITE_RECEM, diasDesdeEpoca(dia)) };
  }

  var api = {
    SEMENTE: SEMENTE, EPOCA: EPOCA, FUSO: FUSO, EXCLUIDOS: EXCLUIDOS,
    PISO_PRATELEIRA: PISO_PRATELEIRA, LIMITE_RECEM: LIMITE_RECEM,
    LIMITE_COLECAO: LIMITE_COLECAO,
    ORDEM_EIXOS: ORDEM_EIXOS, PREFIXO_VALORATIVA: PREFIXO_VALORATIVA,
    diaEmSaoPaulo: diaEmSaoPaulo, diasDesdeEpoca: diasDesdeEpoca,
    fnv1a: fnv1a, elegiveis: elegiveis, permutacao: permutacao,
    filmeDoDia: filmeDoDia, filmeDoDiaEm: filmeDoDiaEm,
    fazAniversario: fazAniversario, filmeDaPermutacao: filmeDaPermutacao,
    escolhaDoDia: escolhaDoDia, emCarencia: emCarencia,
    CARENCIA_ANIVERSARIO_DIAS: CARENCIA_ANIVERSARIO_DIAS,
    prateleirasBase: prateleirasBase, colecoes: prateleirasBase,
    ordemDasColecoes: ordemDasColecoes, intercalar: intercalar,
    janelaDoDia: janelaDoDia, colecaoDoDia: colecaoDoDia,
    recemChegados: recemChegados, recemDoDia: recemDoDia,
    modoDoLogo: modoDoLogo, tituloNaLinha: tituloNaLinha,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ESPECTRO_SELECAO = api;
})(this);
