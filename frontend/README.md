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
  index.html        Home (catálogo dos 3 filmes)
  filme.html        Tela do filme (lê ?slug=<slug>)
  css/styles.css    Design system (dark, gradiente, 3 famílias de fonte)
  js/data.js        DADOS EMBUTIDOS (gerado — não editar à mão)
  js/home.js        Monta cards + busca estética
  js/filme.js       Renderiza ficha, narrativa, grupos, temas, modo degradado
  js/survey.js      Micro-pesquisa A/B (localStorage + copiar feedback)
  data/*.json       Cópia crua dos JSONs (referência; o site usa data.js)
  build_data.py     Gera js/data.js e data/*.json a partir de resultado/
```

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

Isso reescreve `js/data.js` e `data/*.json` a partir de
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
- **Busca** é estética nesta versão: ao focar/digitar mostra "busca em breve",
  sem lógica de filtro.
- **Micro-pesquisa (A/B):** voto salvo em `localStorage` por filme; botão
  "copiar meu feedback" gera texto simples para envio manual. Sem backend,
  sem analytics, sem cookies de terceiros.
- **Acessibilidade:** navegação por teclado nos expansíveis (botões com
  `aria-expanded`/`aria-controls`) e no formulário; `aria-live` nos status;
  foco visível; respeita `prefers-reduced-motion`.

## Teste manual

Ver [`TESTE_MANUAL.md`](TESTE_MANUAL.md) para o roteiro executado e resultados.
