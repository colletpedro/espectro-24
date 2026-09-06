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

  /* [v1.9.42] A FAIXA DE STILLS VIROU O HERO — e com ela a largura do CDN.
     Substitui o `TAMANHO_STILLS = "w300"` da galeria de rodapé (v1.9.39–41),
     que foi REMOVIDA: o item deixou de ser uma miniatura de 172px e passou
     a ocupar a coluna inteira, exatamente como o backdrop estático de antes.

     MEDIDO ao vivo (2026-09-06): o hero mede **720 × 405 CSS no desktop**
     (a coluna de leitura, `--maxw` 760px menos 2 × 20px de padding) e
     **375 × 211 no mobile** (de borda a borda, `width: calc(100% + 40px)`).

     A lista de larguras de backdrop do TMDB é `w300 · w780 · w1280 ·
     original` (não há `w500`). Na convenção do projeto — largura do CDN
     dividida pela largura CSS, ideal 2,0× num aparelho de densidade 2:

         largura CSS      w780     w1280
         720 (desktop)   1,08×     1,78×
         375 (mobile)    2,08×     3,41×

     Daí o PAR, servido por `srcset`/`sizes` em vez de um valor único:

       · desktop → `w1280`, 1,78×. É EXATAMENTE o que o backdrop estático
         já servia (`TAMANHO_BACKDROP`), então a nitidez do topo da página
         não regride um pixel com a troca. `w780` daria 1,08× — visivelmente
         mole numa imagem que ocupa a abertura inteira.
       · mobile → `w780`, 2,08×, praticamente o ideal. Servir `w1280` ali
         seria mandar 3,41× de pixels que a tela não mostra, ao custo de
         138,6 kB por imagem contra 59,0 kB (médias MEDIDAS em 40 stills
         publicados) — 2,3× mais bytes no aparelho que menos tem banda.

     `original` está fora por regra pré-existente do projeto (3840×2160,
     ~1,5 MB numa imagem só). */
  var TAMANHO_STILLS_DESKTOP = "w1280";
  var TAMANHO_STILLS_MOBILE = "w780";

  /* O breakpoint de `sizes` é o MESMO 640px do CSS (`@media (max-width:
     640px)`, onde o backdrop vira de borda a borda). Repetido aqui porque
     `sizes` é atributo de HTML e não enxerga a media query do CSS; se um
     dos dois mudar, o outro tem de mudar junto — e é por isso que o número
     aparece uma vez só nesta constante, e não solto em cada chamada. */
  var STILLS_SIZES = "(max-width: 640px) 100vw, 720px";

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
    /* [v1.9.43] `diferido`: guarda o endereço em `data-src` em vez de
       `src`, para que a imagem NÃO seja buscada até alguém atribuir o
       `src` de verdade (na faixa, `faixa.js` faz isso conforme o quadro
       se aproxima). Existe porque `loading="lazy"` é DICA e não teto: o
       limiar dele depende da conexão e, numa rápida, cobre a trilha
       inteira — MEDIDO, as 12 imagens do hero saíram juntas na abertura
       da página, 1,62 MB de uma vez. */
    if (cfg.diferido) {
      img.dataset.src = url(cfg.path, cfg.tamanho);
    } else {
      img.src = url(cfg.path, cfg.tamanho);
    }
    /* [v1.9.42] `srcset`/`sizes` OPCIONAIS — só a faixa do hero os usa
       (ver `TAMANHO_STILLS_DESKTOP`/`_MOBILE`). Quem não passa `srcset`
       continua com uma URL só, como sempre: o pôster e o backdrop
       estático não mudaram de comportamento. */
    if (cfg.srcset) {
      if (cfg.diferido) img.dataset.srcset = cfg.srcset;
      else img.srcset = cfg.srcset;
      if (cfg.sizes) img.sizes = cfg.sizes;
    }
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

  /* [v1.9.42] `montarHeroFaixa(ficha, opcoes)` → os quadros 16:9 que
     compõem a FAIXA DO HERO, no topo da página do filme. Substitui
     `montarGaleria` (v1.9.39–41), que montava miniaturas de 172px para a
     galeria de rodapé — seção REMOVIDA nesta versão: o mesmo conteúdo em
     dois lugares da mesma página.

     Cada item ocupa a largura inteira da coluna e tem a proporção do
     próprio arquivo reservada, exatamente como o backdrop estático fazia
     — a troca não pode introduzir salto de layout no topo da página, que
     é o pior lugar possível para um.

     **RISCO DE SPOILER ASSUMIDO** (ver docstring de `ficha.py`): nenhum
     filtro de conteúdo, e agora na posição MAIS proeminente da página. O
     backdrop estático já era essa exceção (§3[E]); a faixa não a amplia
     em natureza, mas amplia em quantidade — de um quadro para até
     `TETO_STILLS`.

     Devolve array VAZIO — nunca `null` — quando não há faixa: sem
     `ficha`, `galeria_stills` ausente/vazio (inclui o FILTRO DE DURAÇÃO e
     o PISO, `ficha.py`), ou campo que não é array. Quem chama cai no
     backdrop estático de sempre; o hero NUNCA fica vazio, é o topo da
     página (ver `filme.js`).

     CARREGAMENTO SOB DEMANDA, e é aqui que ele vive: `eager` só nos
     `EAGER_NO_HERO` primeiros itens, `lazy` em todo o resto. Uma volta
     inteira da faixa a `w1280` são ~1,6 MB, acima do teto de ~1,5 MB por
     página — mas ABRIR a página custa só os itens ansiosos, e os demais
     chegam conforme a faixa avança e cada um entra na viewport. Baixar a
     qualidade para caber foi recusado explicitamente pelo dono. */
  var EAGER_NO_HERO = 2;

  function montarHeroFaixa(ficha, opcoes) {
    opcoes = opcoes || {};
    var lista = (ficha && ficha.galeria_stills) || [];
    if (!Array.isArray(lista)) return [];
    var nome = opcoes.titulo || "";
    return lista.filter(function (s) { return s && s.still_path; })
      .map(function (s, i) {
        return caixaDeImagem({
          classe: "hero-still",
          razao: razaoOu(s.still_largura, s.still_altura, RAZAO_BACKDROP),
          path: s.still_path,
          largura: s.still_largura,
          altura: s.still_altura,
          tamanho: TAMANHO_STILLS_DESKTOP,
          srcset: url(s.still_path, TAMANHO_STILLS_MOBILE) + " 780w, " +
                  url(s.still_path, TAMANHO_STILLS_DESKTOP) + " 1280w",
          sizes: STILLS_SIZES,
          // O PRIMEIRO quadro é o backdrop do hero de sempre (`ficha.py`
          // pina-o em 1º) e pinta a abertura da página: adiá-lo deixaria o
          // topo vazio no primeiro instante, que é justamente o que o
          // `eager` do backdrop estático existia para evitar.
          lazy: i >= EAGER_NO_HERO,
          // na FAIXA o `src` é diferido (ver `caixaDeImagem`); na galeria
          // do mobile não, porque lá a coluna é vertical e o `lazy`
          // nativo já segura — MEDIDO: 2 de 12 na abertura.
          diferido: !!opcoes.diferido && i >= EAGER_NO_HERO,
          // ALT numerado: são vários quadros do MESMO filme em sequência, e
          // "Imagem de X" repetido 12 vezes seria ruído idêntico para quem
          // usa leitor de tela — o número os distingue sem descrever a cena
          // (não temos a descrição, e descrevê-la arriscaria spoiler além do
          // que a imagem já arrisca).
          alt: "Still " + (i + 1) + " de " + nome + sufixoAno(opcoes.ano),
          notaVazio: "sem imagem",
        });
      });
  }

  /* [v1.9.43] `montarGaleriaMobile(ficha, opcoes)` → os mesmos stills, na
     GALERIA DO MOBILE (uma coluna, borda a borda). Reusa
     `montarHeroFaixa` inteiro: são os mesmos quadros, a mesma proporção
     reservada, o mesmo `alt` numerado e o mesmo par de larguras de CDN.
     A diferença é toda de layout, e layout é CSS.

     `sizes` é o MESMO: no mobile a expressão já resolve para `100vw`, que
     é exatamente a largura que o item ocupa aqui. Não há segundo
     breakpoint a manter em sincronia. */
  function montarGaleriaMobile(ficha, opcoes) {
    return montarHeroFaixa(ficha, opcoes);
  }

  window.ESPECTRO_POSTER = {
    CDN: CDN, TAMANHO: TAMANHO, TAMANHO_BACKDROP: TAMANHO_BACKDROP,
    TAMANHO_STILLS_DESKTOP: TAMANHO_STILLS_DESKTOP,
    TAMANHO_STILLS_MOBILE: TAMANHO_STILLS_MOBILE,
    STILLS_SIZES: STILLS_SIZES, EAGER_NO_HERO: EAGER_NO_HERO,
    RAZAO_PADRAO: RAZAO_PADRAO, RAZAO_BACKDROP: RAZAO_BACKDROP,
    url: url, razaoDe: razaoDe, montar: montar,
    montarBackdrop: montarBackdrop, montarHeroFaixa: montarHeroFaixa,
    montarGaleriaMobile: montarGaleriaMobile,
  };
})();
