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

   BACKDROPS NÃO SÃO RENDERIZADOS EM LUGAR NENHUM. O pipeline coleta
   `backdrop_paths[]` (custo marginal zero, mesma chamada) e este arquivo
   deliberadamente não os lê: o TMDB não garante que um backdrop seja livre
   de spoiler, e "0 spoilers para quem ainda não assistiu" é a promessa
   central do produto (§0). Uma imagem legítima do acervo pode ser do
   terceiro ato. Se você veio aqui para "aproveitar" os backdrops, a decisão
   de produto está registrada no changelog da v1.9.29 e depende de uma
   política de curadoria que ainda não existe. */
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
     também o caso em que o CSS não carregou e o em que a imagem não vem. */
  function razaoDe(ficha) {
    var l = ficha && ficha.poster_largura, a = ficha && ficha.poster_altura;
    return (l > 0 && a > 0) ? (l + " / " + a) : RAZAO_PADRAO;
  }

  /* AUSÊNCIA DE PÔSTER É ESTADO DESENHADO, não imagem quebrada. Nenhum dos
     35 filmes publicados está neste caso hoje (medido: 35/35 com pôster),
     mas a expansão trará filmes obscuros com cobertura menor — e o estado
     tem de existir ANTES, senão o primeiro filme sem pôster vira um ícone
     de imagem quebrada em produção. O desenho é a própria caixa do pôster,
     na proporção padrão, com a marca do produto em vez de uma foto: mesma
     silhueta, sem fingir que a imagem está chegando. */
  function vazio(titulo) {
    var el = document.createElement("span");
    el.className = "poster__vazio";
    el.setAttribute("aria-hidden", "true");     // o alt do bloco já diz tudo
    var marca = document.createElement("span");
    marca.className = "poster__vazio-marca";
    marca.textContent = "24";
    var nota = document.createElement("span");
    nota.className = "poster__vazio-nota";
    nota.textContent = "sem pôster";
    el.appendChild(marca);
    el.appendChild(nota);
    return el;
  }

  /* `montar(ficha, opcoes)` → o elemento pronto, com a proporção já
     reservada. `opcoes.uso` é "mosaico" ou "ficha"; `opcoes.titulo` e
     `opcoes.ano` compõem o `alt`; `opcoes.lazy` liga `loading="lazy"`. */
  function montar(ficha, opcoes) {
    opcoes = opcoes || {};
    var uso = opcoes.uso === "ficha" ? "ficha" : "mosaico";
    var caixa = document.createElement("span");
    caixa.className = "poster poster--" + uso;
    caixa.style.aspectRatio = razaoDe(ficha);

    var caminho = ficha && ficha.poster_path;
    if (!caminho) {
      caixa.classList.add("is-vazio");
      caixa.appendChild(vazio(opcoes.titulo));
      return caixa;
    }

    var img = document.createElement("img");
    img.className = "poster__img";
    img.src = url(caminho, TAMANHO[uso]);
    if (ficha.poster_largura) img.width = ficha.poster_largura;
    if (ficha.poster_altura) img.height = ficha.poster_altura;

    // `lazy` na home (35 imagens, a maioria abaixo da dobra) e `eager` na
    // página do filme (UMA imagem, sempre acima da dobra — adiá-la só
    // atrasaria a abertura da página). `decoding="async"` nos dois: nenhum
    // dos dois casos precisa bloquear a pintura do texto.
    img.loading = opcoes.lazy ? "lazy" : "eager";
    img.decoding = "async";

    // ALT: o pôster ilustra um filme que o texto ao lado JÁ nomeia. Descrever
    // a arte seria invenção (não temos a descrição) e repetir o título seria
    // ruído para quem usa leitor de tela. O alt diz o que a imagem É.
    var nome = opcoes.titulo || "";
    img.alt = "Pôster de " + nome + (opcoes.ano ? " (" + opcoes.ano + ")" : "");

    // Falha do CDN (404, rede, `file_path` que envelheceu) cai no MESMO
    // estado desenhado da ausência — nunca no ícone de imagem quebrada.
    img.addEventListener("error", function () {
      if (caixa.classList.contains("is-vazio")) return;
      caixa.classList.add("is-vazio");
      caixa.innerHTML = "";
      caixa.appendChild(vazio(nome));
    });

    caixa.appendChild(img);
    return caixa;
  }

  window.ESPECTRO_POSTER = {
    CDN: CDN, TAMANHO: TAMANHO, RAZAO_PADRAO: RAZAO_PADRAO,
    url: url, razaoDe: razaoDe, montar: montar,
  };
})();
