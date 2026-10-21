# Espectro 24 — Frontend v1

Site estático que apresenta as análises de recepção dos filmes do pipeline
Espectro 24 (o pacote Python na raiz do repo). **Zero backend, zero API,
zero rede em runtime** — os dados vêm embutidos em `js/data.js`, gerado a
partir dos JSONs de `resultado/`.

Estética: dark mode de cinema, gradiente espectral (vermelho→âmbar→verde→azul)
como marca, tipografia serif/mono/sans. Mobile-first.

## Estrutura

```
frontend/
  index.html        Home editorial: cabeçalho (busca, Filmes, Método),
                    manchete (filme do dia), coleção do dia, recém-
                    chegados, link para /filmes (lê só js/indice.js)
  filmes/index.html Catálogo completo — o mosaico que era a home (rota /filmes)
  filme.html        Tela do filme (lê ?slug=<slug>)
  css/styles.css    Design system (dark, gradiente, 3 famílias de fonte)
  js/data.js        DADOS EMBUTIDOS (gerado — não editar à mão)
  js/indice.js      ÍNDICE ENXUTO da home (gerado de data.js — não editar)
  js/busca.js       Motor de busca: consulta → resultados (puro, sem DOM)
  js/selecao.js     Filme do dia, coleções, recém-chegados (puro)
  js/textos_home.js Toda a prosa da home, inclusive os templates
  js/inicio.js      Apresentação da home (só DOM e eventos)
  js/catalogo.js    Mosaico + filtro de /filmes (era js/home.js)
  js/filme.js       Renderiza ficha, narrativa, grupos, temas, modo degradado
  js/survey.js      Micro-pesquisa A/B (localStorage + copiar feedback)
  data/*.json       Cópia crua dos JSONs (referência; o site usa data.js)
  build_data.py     Gera js/data.js e data/*.json a partir de resultado/,
                    e em seguida js/indice.js
  build_indice.py   Gera js/indice.js a partir de js/data.js
  entrada_no_catalogo.json  Data de entrada de cada slug (recém-chegados)
```

`/filmes` é uma pasta com `index.html` para funcionar igual na Vercel e no
`http.server`. Por `file://` o navegador não resolve índice de pasta: abra
`filmes/index.html` diretamente.

## Rodar localmente

**Opção A — abrir direto (file://):** como os dados são embutidos em
`js/data.js`, basta abrir `frontend/index.html` no navegador. Sem servidor,
sem CORS.

**Opção B — servidor estático (recomendado p/ paridade com produção):**

```bash
cd frontend
python3 -m http.server 8000
# abrir http://localhost:8000/index.html
```

## Regenerar os dados

Só é necessário se os JSONs em `resultado/` mudarem (nova coleta/narrativa).
Roda offline, não toca no pacote Python:

```bash
python3 frontend/build_data.py
```

Isso reescreve `js/data.js` e `data/*.json` (e, em seguida, `js/indice.js`)
a partir de
`resultado/{the-invite-2026,cure,cidade-de-deus}.json` e adiciona um filme
sintético `teste-degradado` (usado só para exercitar o modo degradado —
não aparece no catálogo da home).

## Deploy na Vercel

Site 100% estático, sem build. No dashboard da Vercel (ou `vercel` CLI):

1. **Root Directory:** `frontend`
2. **Framework Preset:** `Other` (nenhum framework)
3. **Build Command:** deixar vazio · **Output Directory:** `.` (a própria pasta)

Nada mais a configurar — a Vercel serve os arquivos estáticos direto.

## Comportamentos & regras de produto embutidas

- **Frequências** sempre como `~X de N` (nunca porcentagem solta); a largura
  da barra do tema = X/N.
- **Nenhuma nota média / score / estrela agregada.** A faixa de estrelas por
  grupo (`★ 0,5–2,5` etc.) é a **cota de coleta**, rotulada como tal, não uma
  avaliação.
- **Modo degradado sempre visível:** bucket `reduzido` mostra o aviso com
  números concretos; bucket `sem_analise` mostra contagem + link para as
  reviews no Letterboxd e **não** lista temas. Nunca atrás de tooltip/collapse.
- **Sem conteúdo de trama** além da sinopse oficial da ficha (TMDB); sem
  review bruta individual.
- **Busca da home**: client-side sobre `js/indice.js` (título exibido,
  título do Letterboxd, slug como chave oculta, ano); prefixo antes de
  substring, desempate alfabético. Setas + Enter, Esc fecha. Em `/filmes`
  continua o filtro do mosaico (título ou eixo em destaque); `?desde=AAAA-MM-DD`
  restringe o mosaico aos filmes que entraram no catálogo a partir da data
  (é o "ver todos os recém-chegados" da home).
- **Filme do dia, prateleiras e ganchos**: regras escritas no cabeçalho de
  `js/selecao.js` (seleção) e de `js/textos_home.js` (prioridade dos
  ganchos). `?dia=AAAA-MM-DD` na home fixa a data para conferência.
- **Micro-pesquisa (A/B):** voto salvo em `localStorage` por filme; botão
  "copiar meu feedback" gera texto simples para envio manual. Sem backend,
  sem analytics, sem cookies de terceiros.
- **Acessibilidade:** navegação por teclado nos expansíveis (botões com
  `aria-expanded`/`aria-controls`) e no formulário; `aria-live` nos status;
  foco visível; respeita `prefers-reduced-motion`.

## Teste manual

Ver [`TESTE_MANUAL.md`](TESTE_MANUAL.md) para o roteiro executado e resultados.
