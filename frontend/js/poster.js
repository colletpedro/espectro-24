/* Espectro 24 — poster.js  [v1.9.29]
   O PÔSTER, nos dois lugares onde ele aparece: a célula do mosaico (home) e
   a abertura da ficha (página do filme).

   POR QUE UM ARQUIVO COMPARTILHADO, quando o projeto duplica de propósito
   (`EIXO_LABEL` vive em home.js E em filme.js). A duplicação lá é aceitável
   porque a lista é FECHADA e versionada — divergir seria visível no primeiro
   filme classificado. Aqui não é: uma home servindo `w500` e uma ficha
   servindo `w342` não quebram nada, não aparecem em teste nenhum, e a única
   consequência é peso de rede que ninguém mede. O que precisa NÃO divergir
   é exatamente o que este arquivo guarda — a escolha de tamanho do CDN, a
   reserva de proporção e o desenho do vazio.

   NADA DE BINÁRIO NO REPOSITÓRIO (requisito): o JSON guarda só `file_path`,
   e a imagem vem do CDN do TMDB. Nenhum download, nenhum proxy, nenhum
   cache local — ver SPEC §3[F].

   [v1.9.30] O BACKDROP passou a ser renderizado — UM, no topo da página do
   filme, no lugar onde o pôster estava. NÃO EXISTE GALERIA e a distinção
   não é retórica: `backdrop_paths[]` continua sendo lista guardada que
   arquivo nenhum do frontend percorre; o que este arquivo lê é o campo
   `backdrop_path`, o ESCOLHIDO, decidido em código no pipeline por uma
   ordem total e registrada (`_ordem_imagem`, `ficha.py`).

   ISTO É EXCEÇÃO EXPLÍCITA AO PRINCÍPIO ANTI-SPOILER DO §0, e o comentário
   anterior deste arquivo — que dizia, com razão, que o TMDB não garante que
   um backdrop seja livre de spoiler — continua VERDADEIRO. O que mudou não
   foi o fato; foi a decisão sobre ele, tomada pelo dono do projeto com o
   trade-off na mesa. O produto anuncia "0 spoilers" na home e resolve todo
   trade-off contra o spoiler (bullets filtrados, veredito proibido de citar
   reviravolta) — e este elemento, e só ele, deixa de valer essa promessa,
   na posição mais proeminente da página. Registro por extenso, com o que se
   ganha e o que se perde, em SPEC §3[E], "O BACKDROP no topo da página do
   filme".

   O PÔSTER CONTINUA NA HOME, e desde a v1.9.31 SEMPRE na variante SEM
   TEXTO (com fallback para a com texto — ver `fonteDoPoster`). */
(function () {
  "use strict";

  var CDN = "https://image.tmdb.org/t/p/";

  // TAMANHOS DO CDN, e o cálculo por trás de cada escolha. O TMDB serve
  // variantes de LARGURA (w92 · w154 · w185 · w342 · w500 · w780 · original)
  // e a regra é a mesma nos dois casos: a maior largura CSS que o elemento
  // atinge, vezes 2 (telas de densidade 2x/3x), arredondada para cima na
  // lista. Servir `original` (2000px de largura, ~1MB) num card de 142px é
  // desperdiçar 99% dos bytes baixados, e é explicitamente o que não se faz.
  //
  //   mosaico → w342. A célula mede ~142px CSS no desktop (mosaico de
  //     1080px, 7 colunas, gap de 8px) e ~111px no mobile de 375px (3
  //     colunas). 142 × 2 = 284; 111 × 3 = 333. `w185` estouraria em tela
  //     retina, `w500` traria 47% mais pixels que o necessário — vezes 35
  //     células.
  //   ficha  → w500. O pôster da página do filme mede 200px CSS no desktop
  //     e 140px no mobile; 200 × 2 = 400. `w342` ficaria abaixo em retina,
  //     e é UMA imagem por página — a folga custa pouco.
  var TAMANHO = { mosaico: "w342", ficha: "w500" };

  // [v1.9.30] BACKDROP — lista de larguras PRÓPRIA no TMDB
  // (w300 · w780 · w1280 · original), e é por isso que ele não entra no mapa
  // acima: `w500` nem existe para backdrop.
  //
  //   ficha → w1280. A coluna de leitura é `--maxw` (720px, 760px acima do
  //     breakpoint largo) menos 20px de padding de cada lado: 680–720px CSS.
  //     680 × 2 = 1360 e 720 × 2 = 1440, e o degrau seguinte da lista é
  //     `original` (3840×2160, ~1,5 MB), que a regra do projeto proíbe
  //     servir. `w1280` cobre 1× com folga e entrega 1,78–1,88× num aparelho
  //     de densidade 2, contra os 2,0× ideais — diferença que não se vê num
  //     quadro fotográfico e que custaria megabytes para fechar. `w780`
  //     ficaria em 1,08× no desktop, visivelmente mole em retina.
  var TAMANHO_BACKDROP = "w1280";

  // [v1.9.38] GALERIA DE PÔSTERES ALTERNATIVOS — lista própria de largura,
  // porque a caixa é uma MINIATURA, bem menor que o pôster de 200px da
  // ficha. Medido: a coluna de leitura cabe ~5 miniaturas de ~100px CSS de
  // largura com gap de 8px (720px / (100+8) ≈ 6, folga para o gap externo).
  // 100 × 2 = 200; `w154` (154px) cobre 1,54× — acima do 1× e abaixo do
  // custo de `w185`/`w342` por imagem, e são até 8 delas na mesma página
  // (`TETO_GALERIA`, `ficha.py`), ao contrário do pôster/backdrop que são
  // UMA imagem só. `w92` ficaria mole em tela retina (0,92×).
  var TAMANHO_GALERIA = "w154";

  // Proporção de reserva do backdrop quando as dimensões não vieram da API.
  // 16:9 é o formato do acervo de backdrops do TMDB (medido nos 34 do
  // catálogo que têm um: 3840×2160, 1920×1080, 2560×1440 — e as exceções,
  // como `eighth-grade` em 3500×1969, ficam perto). Vale a mesma regra do
  // pôster: as dimensões REAIS têm precedência, esta razão só existe para o
  // caso em que elas faltam.
  var RAZAO_BACKDROP = "16 / 9";

  // Proporção de reserva quando as dimensões não vieram da API. 2:3 é o
  // padrão de pôster de cinema e o que a esmagadora maioria do TMDB usa —
  // mas NÃO é universal, e por isso as dimensões reais têm precedência:
  // medido no catálogo, `poster-do-curta-experimental` é 505×750 (0,673) e
  // `aftersun` é 1632×2449 (0,666), nenhum dos dois exatamente 2:3.
  var RAZAO_PADRAO = "2 / 3";

  function url(filePath, tamanho) {
    return CDN + tamanho + filePath;
  }

  /* A PROPORÇÃO, RESERVADA ANTES DE CARREGAR — requisito, não acabamento.
     Sem isto, 35 pôsteres chegando em ordem aleatória empurram a grade para
     baixo enquanto a pessoa lê o primeiro título; é o modo de falha clássico
     de galeria (CLS). A reserva é feita em DOIS níveis, de propósito:

       · `aspect-ratio` no contêiner, que segura a caixa mesmo se a imagem
         nunca chegar (rede caída, 404 do CDN, `file_path` inválido);
       · `width`/`height` no próprio `<img>`, que é o que dá ao navegador a
         razão INTRÍNSECA e o faz reservar sozinho, sem depender do CSS.

     Um só dos dois já resolveria o caso feliz. Os dois juntos resolvem
     também o caso em que o CSS não carregou e o em que a imagem não vem.

     [v1.9.30] O BACKDROP entra pela MESMA porta, e isso é requisito: ele é
     16:9 e ocupa a largura inteira da coluna, então a altura que ele reserva
     é MAIOR em pixels que a do pôster contido de 200px — sem reserva, o
     salto seria pior que o de antes, não menor. O ganho de CLS zero da
     v1.9.29 não pode regredir. */
  function razaoOu(largura, altura, padrao) {
    return (largura > 0 && altura > 0) ? (largura + " / " + altura) : padrao;
  }

  function razaoDe(ficha) {
    return razaoOu(ficha && ficha.poster_largura,
                   ficha && ficha.poster_altura, RAZAO_PADRAO);
  }

  /* [v1.9.30, DECIDIDO na v1.9.31] O PÔSTER SEM TEXTO É O PADRÃO ÚNICO da
     home. O mecanismo `?poster=texto`/`?poster=limpo` foi o jeito de o dono
     do projeto comparar as duas OLHANDO — o mesmo esquema de `?barra=` e
     `?ficha=` nas rodadas anteriores — e ele escolheu a limpa. Seguindo a
     mesma convenção daquelas duas decisões (a barra contínua e a ficha em
     pilha de sistema): a variante vencedora fica, a perdedora e o mecanismo
     de escolha SAEM do código — não como opção morta atrás de flag.

     Uma URL antiga com `?poster=` não quebra nada: o parâmetro
     simplesmente não é mais lido, como já é o comportamento estabelecido
     para query params obsoletos das rodadas passadas.

     O FALLBACK que segue abaixo NÃO é resquício do mecanismo de escolha —
     é a mesma regra de AUSÊNCIA que já rege backdrop (§3[E]) e ficha
     (§3[F]) desde a v1.3.0: dado ausente cai para o próximo degrau, nunca
     para buraco. Filme sem arte sem texto usa o pôster normal (com
     texto). */
  function fonteDoPoster(ficha) {
    if (ficha && ficha.poster_sem_texto_path) {
      return {
        path: ficha.poster_sem_texto_path,
        largura: ficha.poster_sem_texto_largura,
        altura: ficha.poster_sem_texto_altura,
      };
    }
    return {
      path: (ficha && ficha.poster_path) || null,
      largura: ficha && ficha.poster_largura,
      altura: ficha && ficha.poster_altura,
    };
  }

  /* AUSÊNCIA DE IMAGEM É ESTADO DESENHADO, não imagem quebrada. Nenhum dos
     35 filmes publicados está sem pôster (medido: 35/35), e 34 dos 35 têm
     backdrop, mas a expansão trará filmes obscuros com cobertura menor — e o
     estado tem de existir ANTES, senão o primeiro filme sem imagem vira um
     ícone quebrado em produção. O desenho é a própria caixa da imagem, na
     proporção que ela teria, com a marca do produto em vez de uma foto:
     mesma silhueta, sem fingir que a imagem está chegando. */
  function vazio(nota) {
    var el = document.createElement("span");
    el.className = "poster__vazio";
    el.setAttribute("aria-hidden", "true");     // o alt do bloco já diz tudo
    var marca = document.createElement("span");
    marca.className = "poster__vazio-marca";
    marca.textContent = "24";
    var nt = document.createElement("span");
    nt.className = "poster__vazio-nota";
    nt.textContent = nota || "sem pôster";
    el.appendChild(marca);
    el.appendChild(nt);
    return el;
  }

  // A caixa comum de pôster e backdrop: proporção reservada, imagem dentro,
  // e o MESMO estado desenhado para "não veio" e "quebrou no CDN".
  function caixaDeImagem(cfg) {
    var caixa = document.createElement("span");
    caixa.className = cfg.classe;
    caixa.style.aspectRatio = cfg.razao;

    if (!cfg.path) {
      caixa.classList.add("is-vazio");
      caixa.appendChild(vazio(cfg.notaVazio));
      return caixa;
    }

    var img = document.createElement("img");
    img.className = "poster__img";
    img.src = url(cfg.path, cfg.tamanho);
    if (cfg.largura) img.width = cfg.largura;
    if (cfg.altura) img.height = cfg.altura;

    img.loading = cfg.lazy ? "lazy" : "eager";
    img.decoding = "async";
    img.alt = cfg.alt;

    // Falha do CDN (404, rede, `file_path` que envelheceu) cai no MESMO
    // estado desenhado da ausência — nunca no ícone de imagem quebrada.
    img.addEventListener("error", function () {
      if (caixa.classList.contains("is-vazio")) return;
      caixa.classList.add("is-vazio");
      caixa.innerHTML = "";
      caixa.appendChild(vazio(cfg.notaVazio));
    });

    caixa.appendChild(img);
    return caixa;
  }

  function sufixoAno(ano) { return ano ? " (" + ano + ")" : ""; }

  /* `montar(ficha, opcoes)` → o pôster pronto, com a proporção já reservada.
     `opcoes.uso` é "mosaico" ou "ficha"; `opcoes.titulo` e `opcoes.ano`
     compõem o `alt`; `opcoes.lazy` liga `loading="lazy"`. */
  function montar(ficha, opcoes) {
    opcoes = opcoes || {};
    var uso = opcoes.uso === "ficha" ? "ficha" : "mosaico";
    var fonte = fonteDoPoster(ficha);
    var nome = opcoes.titulo || "";
    return caixaDeImagem({
      classe: "poster poster--" + uso,
      razao: razaoOu(fonte.largura, fonte.altura, RAZAO_PADRAO),
      path: fonte.path,
      largura: fonte.largura,
      altura: fonte.altura,
      tamanho: TAMANHO[uso],
      // `lazy` na home (35 imagens, a maioria abaixo da dobra) e `eager` na
      // página do filme (UMA imagem, sempre acima da dobra — adiá-la só
      // atrasaria a abertura da página).
      lazy: !!opcoes.lazy,
      // ALT: o pôster ilustra um filme que o texto ao lado JÁ nomeia.
      // Descrever a arte seria invenção (não temos a descrição) e repetir o
      // título seria ruído para quem usa leitor de tela. O alt diz o que a
      // imagem É. A variante sem texto NÃO muda o alt: para quem não vê a
      // imagem, "o pôster com ou sem o bloco de créditos" não é distinção
      // que informe — é detalhe de tratamento visual.
      alt: "Pôster de " + nome + sufixoAno(opcoes.ano),
      notaVazio: "sem pôster",
    });
  }

  /* [v1.9.30] `montarBackdrop(ficha, opcoes)` → o backdrop do topo da página
     do filme. UMA imagem, nunca carrossel: o `backdrop_path` é o escolhido
     pelo pipeline, e `backdrop_paths[]` continua sem nenhum leitor aqui.

     Devolve `null` quando o filme não tem backdrop — quem chama decide o
     fallback (hoje: `filme.js` cai no pôster, que por sua vez cai no estado
     de ausência). Ele NÃO cai no pôster por conta própria de propósito: a
     caixa é de proporção e tamanho diferentes, e um pôster 2:3 esticado na
     largura da coluna seria pior que qualquer um dos dois estados. */
  function montarBackdrop(ficha, opcoes) {
    opcoes = opcoes || {};
    if (!ficha || !ficha.backdrop_path) return null;
    return caixaDeImagem({
      classe: "backdrop",
      razao: razaoOu(ficha.backdrop_largura, ficha.backdrop_altura,
                     RAZAO_BACKDROP),
      path: ficha.backdrop_path,
      largura: ficha.backdrop_largura,
      altura: ficha.backdrop_altura,
      tamanho: TAMANHO_BACKDROP,
      lazy: false,           // UMA imagem, sempre acima da dobra
      // ALT: mesma política do pôster — diz o que a imagem É, sem descrever
      // a arte (não temos a descrição) e sem chamá-la de "cena", que seria
      // afirmar uma coisa que nem sempre é verdade (parte do acervo é arte
      // de divulgação, não fotograma).
      alt: "Imagem de " + (opcoes.titulo || "") + sufixoAno(opcoes.ano),
      notaVazio: "sem imagem",
    });
  }

  /* [v1.9.38] `montarGaleria(ficha, opcoes)` → array de miniaturas
     (`<span>` na mesma caixa comum de imagem, cada uma com sua própria
     proporção reservada) para a galeria de pôsteres alternativos.

     Devolve array VAZIO — nunca `null` — quando não há galeria: o filme
     está sem `ficha`, `galeria_posters` é ausente/vazio (inclui o caso da
     GUARDA DE IDENTIDADE, `ficha.py`, que zera a lista quando o `tmdb_id`
     resolvido não é confirmado como o longa esperado), ou o campo não é
     array. Quem chama decide o que fazer com array vazio — hoje, não
     renderizar a seção (ver `filme.js`): galeria vazia não é erro, é o
     mesmo "filme sem [dado]" de sempre (§3[F]).

     `lazy: true` sempre — a galeria vem DEPOIS da narrativa, abaixo da
     dobra em qualquer tela, ao contrário do pôster da ficha (acima) e do
     backdrop (topo). */
  function montarGaleria(ficha, opcoes) {
    opcoes = opcoes || {};
    var lista = (ficha && ficha.galeria_posters) || [];
    if (!Array.isArray(lista)) return [];
    var nome = opcoes.titulo || "";
    return lista.filter(function (p) { return p && p.poster_path; })
      .map(function (p, i) {
        return caixaDeImagem({
          classe: "poster poster--galeria",
          razao: razaoOu(p.poster_largura, p.poster_altura, RAZAO_PADRAO),
          path: p.poster_path,
          largura: p.poster_largura,
          altura: p.poster_altura,
          tamanho: TAMANHO_GALERIA,
          lazy: true,
          // ALT numerado: são várias imagens do MESMO filme lado a lado, e
          // "Pôster de X" repetido 8 vezes seria ruído idêntico para quem
          // usa leitor de tela — o número as distingue sem inventar
          // descrição de arte que não temos.
          alt: "Pôster alternativo " + (i + 1) + " de " + nome,
          notaVazio: "sem pôster",
        });
      });
  }

  window.ESPECTRO_POSTER = {
    CDN: CDN, TAMANHO: TAMANHO, TAMANHO_BACKDROP: TAMANHO_BACKDROP,
    TAMANHO_GALERIA: TAMANHO_GALERIA,
    RAZAO_PADRAO: RAZAO_PADRAO, RAZAO_BACKDROP: RAZAO_BACKDROP,
    url: url, razaoDe: razaoDe, montar: montar,
    montarBackdrop: montarBackdrop, montarGaleria: montarGaleria,
  };
})();
