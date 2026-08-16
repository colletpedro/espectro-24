# Teste manual — Frontend v1

Executado em 2026-07-20, servindo `frontend/` via `python3 -m http.server`
e dirigindo o navegador (desktop ~1280px + mobile 375×812). Verificação por
screenshot, inspeção do DOM (`get_page_text`) e estilos computados.

## Resultados

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | **Home renderiza** — barra espectral segmentada, título serif com "24" itálico gradiente, tagline, subtítulo, busca, microcopy, 3 cards (O Convite / A Cura / Cidade de Deus) com ano + "N reviews observadas" + seta | ✅ |
| 2 | **Busca estética** — ao focar/digitar aparece "Busca em breve — 3 análises disponíveis abaixo"; sem filtro, nunca quebra | ✅ |
| 3 | **Cura (`?slug=cure`)** — header (ano · reviews observadas · título serif · chip "reviews no Letterboxd ↗"); ficha com sinopse oficial + linha "dir. 黒沢清 · Crime, Thriller, Terror, Mistério · 111 min · fonte TMDB"; narrativa em 3 parágrafos | ✅ |
| 4 | **Divisor "EM DETALHE · TEMA A TEMA"** com linha gradiente + disclaimer "grupos de 50 · 20 · 30 … não a proporção real das opiniões" | ✅ |
| 5 | **3 grupos** com bolinha colorida, faixa de estrelas (`★ 0,5–2,5` / `★ 3–3,5` / `★ 4–5`) e "N de N analisadas" | ✅ |
| 6 | **Cores dos grupos** (estilos computados): negativas `#e0673f` (âmbar-avermelhado), medianas `#e3b23c` (dourado), positivas `#4d90e5` (azul) — em bolinha, nome e barra | ✅ |
| 7 | **Frequência `~X de N`** e **largura da barra = X/N** — 1º tema negativas 35/50 → barra 504px = 70% de 720px | ✅ |
| 8 | **Exemplo parafraseado expansível** — clique alterna `aria-expanded` false→true e revela o texto; `+` gira p/ ×; flag "aspas removidas" aparece quando aplicável | ✅ |
| 9 | **Observação geral** do grupo em itálico serif ao final de cada grupo | ✅ |
| 10 | **Micro-pesquisa** — botão Enviar desabilitado até escolher opção; ao votar salva em `localStorage['espectro24:voto:cure']` (`{escolha:"resumo", …}`), mostra agradecimento e botão "copiar meu feedback" | ✅ |
| 11 | **Copiar feedback** — botão presente; gera texto simples (filme, escolha, comentário, data); usa `navigator.clipboard` com fallback `execCommand` | ✅ (função verificada; clipboard real depende de permissão do navegador) |
| 12 | **Voto persistente** — recarregar o filme já votado mostra direto o estado de agradecimento (lido do localStorage) | ✅ |
| 13 | **Modo degradado (`?slug=teste-degradado`, JSON sintético)** — sem ficha (null) → nenhum bloco de ficha, narrativa direto; **negativas** modo `reduzido` → aviso "análise baseada em apenas 7 de 50 reviews-alvo" + 2 temas; **medianas** `sem_analise` → aviso "apenas 2 review(s) válida(s) (piso é 3)" + link "→ 2 review(s) disponíveis no Letterboxd ↗", **0 temas**; **positivas** `completo` → 2 temas | ✅ |
| 14 | **Avisos de modo degradado sempre visíveis** — renderizados inline, nunca atrás de tooltip/collapse | ✅ |
| 15 | **Mobile (375px)** — layout empilha bem; header, ficha, narrativa, divisor, grupos legíveis | ✅ |
| 16 | **Regras de produto** — nenhuma nota média/score/estrela agregada; nenhum texto de review bruto; sinopse só da ficha oficial | ✅ |

## Como reproduzir

```bash
cd frontend && python3 -m http.server 8000
```

- Home: <http://localhost:8000/index.html>
- Filmes: `filme.html?slug=cure` · `?slug=the-invite-2026` · `?slug=cidade-de-deus`
- Modo degradado: `filme.html?slug=teste-degradado`

## Desvios do design (com justificativa)

1. **Fontes de sistema em vez de webfonts.** O design pede serif display /
   mono / sans. Para manter a promessa de **offline / zero rede / abre por
   file://**, uso stacks de sistema (`Georgia` serif, `ui-monospace` mono,
   `system-ui` sans) em vez de baixar Google Fonts. O caráter (serif de
   cinema para títulos/observações, mono para metadados) é preservado; só a
   fonte-fonte muda. Trocar por webfonts self-hosted é trivial depois
   (adicionar `@font-face` com arquivos locais) sem alterar a estrutura.

2. **Resumo e detalhe em sequência (scroll), sem toggle.** O briefing deixa
   "âncora ou toggle" a critério e pede fidelidade ao mockup — o mockup
   mostra as duas seções em sequência, então mantive assim (mais simples e
   fiel). Se as telas ficarem longas demais em uso real, um sub-nav âncora
   "resumo · detalhe" pode ser adicionado sem refazer o layout.

3. **Filme sintético de teste (`teste-degradado`)** existe só para exercitar
   os modos `reduzido`/`sem_analise` (os 3 filmes reais são todos `completo`).
   Fica **fora** do catálogo da home; acessível só pela URL direta.

---

# Teste manual — v1.9.14 (2026-08-16)

Executado servindo `frontend/` via `python3 -m http.server`, dirigindo o
navegador em desktop (1280px) e mobile (375×812). Verificação por inspeção
do DOM e de **estilos/geometria computados** (`getBoundingClientRect`,
`getComputedStyle`), não por leitura de screenshot: o que importa aqui é se
as três colunas estão de fato ALINHADAS, e isso é geometria.

Os cenários 1-16 acima continuam valendo, com duas correções de registro:
o **nº 2** descreve a busca decorativa, substituída pelo nº 21 abaixo; o
**nº 4** cita "50 · 20 · 30", que hoje lê `b.alvo` do JSON e mostra
"40 · 40 · 40" (o texto do teste envelheceu, o código não — a derivação foi
corrigida na v1.9.1).

| # | Cenário | Resultado |
|---|---------|-----------|
| 17 | **Seção "Eixo a eixo"** aparece nos 3 filmes do catálogo, entre o divisor e as listas por grupo; grade de 4 colunas (`128px repeat(3, 1fr)`), 720px de largura dentro do wrap, **sem overflow horizontal** | ✅ |
| 18 | **Alinhamento real** — numa linha de `cidade-de-deus`, as 3 células ficam lado a lado em x=415/612/809, mesma largura (183px); as células de um mesmo eixo pertencem à mesma linha do grid | ✅ |
| 19 | **`contraste: valorativo` (`cidade-de-deus`, o caso de referência)** — a tabela renderiza completa, **0 selos de contraste**, e a área abre com o enunciado próprio ("os três grupos falam das mesmas coisas — e discordam sobre se elas funcionam"), com borda dourada distinta. Não parece vazia nem quebrada | ✅ |
| 20 | **`contraste: tematico` (`the-invite-2026`)** — 5 linhas em destaque, selo "só este grupo" nas células de `direcao_imagem`/positivas e `tom_atmosfera`/positivas (as duas acima de 20pp), e `<details>` "ver os outros 5 eixos" com o resto | ✅ |
| 21 | **Busca real (home)** — "tom" → 2 filmes, "atuação" → 1, "deus" → 1 (título), "atuacao" sem acento → mesmo resultado, "ritmo" → 0 com a mensagem que diz o que a busca cobre, campo vazio → catálogo inteiro de volta | ✅ |
| 22 | **Estados de célula (`?slug=teste-degradado`)** — `sem_numero` (negativas) mostra o tema e "amostra pequena demais para número"; `sem_analise` (medianas) mostra "sem análise" na coluna inteira; eixo que o grupo não menciona mostra "não menciona"; célula normal (positivas) mostra tema + "9 de 30" + barra | ✅ |
| 23 | **Filme sem bloco `eixos`** — a seção não é criada e a página cai na lista de temas de sempre, sem erro (caminho de todo filme fora dos 35 classificados) | ✅ |
| 24 | **Denominador da tabela é DECLARADO como outro** — a nota ao pé diz que os números contam reviews CLASSIFICADAS, "não exatamente as mesmas reviews que a lista abaixo resume", com a sobreposição medida por grupo (ex. negativas 13/40) | ✅ |
| 25 | **Janela temporal** — linha própria abaixo de "40 de 40 analisadas", NUNCA dentro do `.group__header` (onde vive o "~X% das notas"); em `cure`: "escritas majoritariamente entre maio e agosto de 2026"; em `cidade-de-deus`/medianas: "entre janeiro de 2013 e agosto de 2026" (o filme com material antigo de verdade) | ✅ |
| 26 | **Mobile (375px)** — a grade vira coluna única, o cabeçalho de colunas some, as 3 células de um eixo empilham em y distintos e cada uma exibe o nome do grupo via `::before` na cor do grupo; **sem overflow horizontal** | ✅ |
| 27 | **Console limpo** — home, os 3 filmes e o degradado carregam com 0 erro (verificado em aba nova; uma regressão de `var` içado — `MESES` usado antes da atribuição — foi achada e corrigida por este teste) | ✅ |

## O que este teste NÃO cobre

- **Nenhum teste automatizado de frontend existe.** Não há runner de JS no
  projeto, e esta sessão não introduziu um. A verificação acima é manual e
  precisa ser refeita a cada mudança de `filme.js`/`home.js`. É a maior
  dívida de teste do projeto, e ela cresceu nesta versão: `filme.js` saiu de
  ~330 para ~630 linhas.
- A conferência da rotulagem [D3] (tema → eixo) é do dono do projeto e vive
  em `resultado/v1914/ROTULAGEM_CONFERENCIA.md`, não aqui.
