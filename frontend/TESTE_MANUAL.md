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

---

# Teste manual — v1.9.27 (2026-08-27)

Executado servindo `frontend/` via `python3 -m http.server`, dirigindo o
navegador em desktop (1280×900, barra de **720px**) e mobile (375×812,
barra de **335px**). Verificação por inspeção do DOM e de geometria
computada (`getBoundingClientRect`, `getComputedStyle`), como na v1.9.14 —
o que importa aqui é POSIÇÃO em pixel, e isso é geometria, não screenshot.

**RESSALVA DE MÉTODO, escrita porque muda o que os números abaixo
significam.** O painel de navegação desta sessão roda em **documento
oculto** (`document.hidden === true`): `document.timeline.currentTime` fica
**congelado** e as animações CSS só avançam quando um frame é forçado. Em
consequência:

- **MEDIDO** (Web Animations API — `getAnimations()`, `delay`, `duration`,
  e `getComputedStyle` com o tempo posicionado à mão via `currentTime`):
  as durações e os atrasos das três fases, o encadeamento, os valores
  intermediários de opacidade/cor e todo o estado final.
- **VISTO** (screenshot, que força frame): o estado final nos dois
  tamanhos, o quadro da Fase 1 a 350ms, o quadro da Fase 2 a 710ms
  (`napoleon-2023`, com as três camadas em estágios diferentes) e o pico da
  ignição a 971ms, este último ampliado 3× para calibrar a intensidade.
- **NÃO VISTO:** a sequência rodando em velocidade real, nem uma vez. É por
  isso que a leitura de cadência ("cansa em navegação repetida?") vai ao
  changelog com ressalva em vez de veredito.

| # | Cenário | Resultado |
|---|---------|-----------|
| 28 | **Disclaimer da cota fora do ramo com barra** — nos 35 filmes, `.proportion__note` não existe; o percentual `~X% DAS NOTAS` continua no cabeçalho dos três grupos | ✅ |
| 29 | **Ramo sem distribuição intacto (`?slug=teste-degradado`)** — sem barra, sem callout, e a nota volta com o texto da v1.2.1: "Os grupos são cotas de coleta — não a proporção real das opiniões." | ✅ |
| 30 | **Conferência barra × cabeçalhos × callout nos 35** — a fronteira medida na MEIA ALTURA de cada camada (borda direita − `--diag`/2) bate com o `share_real` normalizado em todos os 35; zero divergência. Callout, cabeçalhos e `aria-label` imprimem o mesmo inteiro nos 35 | ✅ |
| 31 | **Colisão em `the-godfather` (2/5/93), desktop** — rótulos em x=0,00 / 47,91 / 365,23; centros 19,96 / 67,87 / 385,19; centros de fatia 7,20 / 32,40 / 385,20; deslocamentos +12,76 / +35,47 / −0,01. Sem sobreposição, sem overflow | ✅ |
| 32 | **Colisão em `the-godfather`, 375px** — rótulos em x=0,00 / 47,91 / 159,27; centros 19,96 / 67,87 / 179,22; centros de fatia 3,35 / 15,07 / 179,22; deslocamentos +16,61 / +52,80 / 0,00. Caixa de 39,91px nos dois tamanhos | ✅ |
| 33 | **Pior caso do catálogo — `cidade-de-deus` (1/3/96)** — pior que `the-godfather`: deslocamento de +59,60px a 375px e ainda assim sem sobreposição (3L+2g = 135,7px contra 335px de barra) | ✅ |
| 34 | **O outro lado da regra — `cats-2019` (86/7/7) a 375px** — a borda DIREITA passa a mandar e os dois últimos rótulos são puxados para dentro (deslocamento −33,13 e −8,38): o indicador inclina para a direita, e é a banda `--esq` que carrega a largura | ✅ |
| 35 | **Caso base sem deslocamento** — `eighth-grade`, `napoleon-2023`, `obsession-2026` e `talk-to-me-2022` em desktop: os três rótulos de cada um centram no centro verdadeiro da fatia (\|desloc\| ≤ 0,01px) e o indicador é a marca vertical de 2px | ✅ |
| 36 | **Durações medidas (WAAPI)** — fill `delay 0 / dur 650`; partição `650, 690, 730 / dur 90` (termina em 820); ignição `820, 875, 930 / dur 260` (termina em 1190). **Total 1190ms** | ✅ |
| 37 | **Encadeamento esquerda→direita da partição** — opacidade das 3 camadas amostrada: t=649 `[0,0,0]`; t=660 `[0.18,0,0]`; t=700 `[0.74,0.18,0]`; t=740 `[1,0.74,0.18]`; t=780 `[1,1,0.74]`; t=819 `[1,1,1]` | ✅ |
| 38 | **Fase 1 não revela grupo nenhum** — a 350ms a barra é um bloco único em `#454b5a`, sem divisão e sem nenhuma das três cores; as camadas estão em opacidade 0 | ✅ |
| 39 | **Nenhum vão em nenhum frame** — a partição não introduz gap, gutter nem fio separador: as camadas só variam opacidade e `translateX`; a de baixo ocupa 100% da barra o tempo todo | ✅ |
| 40 | **Expansão presa à diagonal** — `translateX` inicial = `--diag × 0,35`: −2,772px em `the-godfather` desktop (`--diag` 7,92px) e −1,29px a 375px (`--diag` 3,685px) | ✅ |
| 41 | **Ignição encadeada** — opacidade dos 3 números: t=821 `[0.17,0.16,0.16]`; t=900 `[0.68,0.41,0.16]`; t=1000 `[1,0.57,0.43]`; t=1100 `[1,1,1]` | ✅ |
| 42 | **Neon é evento, não estado** — no repouso a sombra é um único `0 0 7px` na cor do grupo a 20% de alfa e a cor é `#e9e7e1`; no pico (t≈971) é `#fff` com 1px + 5px + 13px + 26px. Verificado também por screenshot ampliado 3× | ✅ |
| 43 | **`prefers-reduced-motion`, sentido A** — com o bloco `no-preference` inativo: **0 animações**, bloco neutro em opacidade 0, 3 camadas em 1, 3 números em opacidade 1 / `#e9e7e1` / sombra de repouso, indicadores em 0,5. Estado final, no primeiro frame | ✅ |
| 44 | **`prefers-reduced-motion`, sentido B** — reativando o bloco, as 13 animações voltam e a sequência re-arma do zero (camadas em 0, números em 0,16, indicadores em 0) | ✅ |
| 45 | **Alternativa textual sempre no estado final** — `aria-label` do `role="img"` com os três rótulos e os três pesos, escrito na montagem e nunca tocado pela animação (que só mexe em opacidade, cor, sombra e transform) | ✅ |
| 46 | **Percentuais são conteúdo** — o texto dos três está no DOM em todos os instantes amostrados, inclusive a 0,16 de opacidade antes da ignição; nenhum caractere é criado ou removido pela animação | ✅ |
| 47 | **Sair no meio e voltar** — saída forçada a 400ms (meio da Fase 1) e volta pelo histórico: a página remonta do zero, a sequência recomeça e termina no estado final (`playState: finished`, camadas e números em 1). Nada fica pela metade porque não há estado guardado em lugar nenhum | ✅ |
| 48 | **Sem overflow horizontal** — `the-godfather`, `eighth-grade`, `napoleon-2023`, `obsession-2026`, `talk-to-me-2022`, `cats-2019` e `cidade-de-deus`, nos dois tamanhos: `scrollWidth == clientWidth` em todos | ✅ |
| 49 | **Console limpo** — os filmes percorridos carregam com 0 erro | ✅ |

## O que este teste NÃO cobre

- **Continua não existindo nenhum teste automatizado de frontend.** Esta
  sessão não introduziu um, e a verificação acima precisa ser refeita a
  cada mudança de `filme.js`/`styles.css`. Segue sendo a maior dívida de
  teste do projeto.
- **A sequência em velocidade real.** Ver a ressalva de método acima: o
  documento oculto congela o `document.timeline`, e o que foi verificado
  foram os parâmetros e os quadros, não a experiência.
- **Leitor de tela real.** O `aria-label` e o `aria-hidden` foram
  verificados no DOM, não com VoiceOver/NVDA.

---

# Teste manual — v1.9.28 (2026-08-27)

Mesmo método da v1.9.27: `frontend/` servido por `python3 -m http.server`,
desktop (1280×900, barra de **720px**) e mobile (375×812, barra de
**335px** na janela real; **331px** dentro do iframe usado nas varreduras,
que reserva 4px de barra de rolagem). Verificação por geometria computada,
não por leitura de screenshot.

**RESSALVA DE MÉTODO — a mesma da v1.9.27, e ela vale de novo.** O painel
roda em **documento oculto**: `document.timeline.currentTime` fica
congelado e as animações só avançam quando um frame é forçado.

- **MEDIDO** (Web Animations API — `getAnimations()`, `delay`, `duration`,
  `currentTime` posicionado à mão; `getComputedStyle`; `Range` para a
  extensão da tinta; `elementFromPoint` para as regiões): a linha do
  tempo, as fronteiras em instantes intermediários, a cobertura da barra,
  as folgas entre os halos, o estado sob `prefers-reduced-motion`.
- **VISTO** (screenshot, que força frame): o estado final nos dois
  tamanhos em `the-godfather`, `cidade-de-deus`, `napoleon-2023` e
  `cats-2019`; a Fase A a 260ms nas DUAS variantes de `--diag`, ampliadas
  3× para a comparação; o pico da ignição a 801ms e o repouso aceso, também
  ampliados 3×.
- **NÃO VISTO:** a sequência rodando em velocidade real, nem uma vez.

**A VARREDURA DE COBERTURA é HIT-TEST, não amostragem de pixel.**
`elementFromPoint` a cada 0,25px, em três alturas, registrando qual camada
está por cima. Ela prova que as regiões são contíguas e que a barra nunca
aparece por baixo — não que dois pixels adjacentes tenham a cor esperada.
É a prova mais forte que este ambiente permite, e é isso que ela é.

| # | Cenário | Resultado |
|---|---------|-----------|
| 50 | **Modelo antigo removido** — `.proportion__prefill` não existe no DOM de nenhum filme; a regra e o `@keyframes proportion-fill` saíram do CSS | ✅ |
| 51 | **A barra nasce em terços** — em `k=0`, os 35 filmes exibem exatamente `[33,33 / 33,33 / 33,33]`, independentemente da distribuição | ✅ |
| 52 | **Linha do tempo (WAAPI)** — fronteiras `delay 0 / dur 650`; ignição `650, 705, 760 / dur 260`, terminando em **1020ms**. Uma única animação na barra, três pares (indicador + número) no callout | ✅ |
| 53 | **`--k` interpola de verdade** — 0 → 0,3088 (t=65) → 0,5679 (t=130) → 0,8436 (t=260) → 0,9749 (t=455) → 1 (t=650); monotônico, sem passar de 1 (sem overshoot) | ✅ |
| 54 | **As duas fronteiras vêm do MESMO `k`** — 60 quadros (6 filmes × 2 tamanhos × 5 instantes): erro absoluto máximo entre a fronteira medida e `neutro + (fim − neutro)·k` = **0,070pp** em desktop e **0,151pp** a 375px. O erro escala com `1/largura_da_barra` — assinatura da resolução de 0,25px do hit-test, não da animação | ✅ |
| 55 | **A soma fecha 100% em todo quadro** — `soma = 100,00000` nos 60 quadros. Não por sincronia: a camada de baixo ocupa 100% da barra sempre, e a terceira região é o que sobra | ✅ |
| 56 | **Nenhum pixel transparente entre regiões** — 180 varreduras (60 quadros × 3 alturas): **exatamente 3 regiões contíguas em todas**, zero "buraco" (barra visível por baixo), zero ponto sem elemento | ✅ |
| 57 | **Direção invertida (`cats-2019`, 86/7/7)** — as fronteiras sobem (33,3→86 e 66,7→93) com o mesmo comportamento: soma 100, sem buraco, mesmo `k` | ✅ |
| 58 | **Denominador quase degenerado (`napoleon-2023`)** — a 2ª fronteira anda só 0,333pp (66,667→67). O erro ABSOLUTO continua em 0,07/0,15pp; foi a métrica de razão que estourou, não a animação. Registrado porque a métrica errada dá 0,46 aqui | ✅ |
| 59 | **`--diag` ACOMPANHA — sem tremor** — 131 amostras de 5ms, nas duas variantes: **zero reversões** na aresta de cima e na de baixo da diagonal; o ponto mais fino da fatia de 2% de `the-godfather` a 375px nunca desce de **4,861px** (mesmo valor final nas duas) | ✅ |
| 60 | **`--diag` ACOMPANHA — custo medido** — o `clamp()` segura a diagonal em 12px e a solta em t≈301ms (375px). Maior variação: **0,947px por quadro**, contra **8,425px por quadro** da própria fronteira (~9× mais lento) | ✅ |
| 61 | **Rótulos ausentes durante a interpolação** — em `t ∈ [0, 650)` os três números estão em opacidade 0 e os indicadores em 0; o texto com o valor FINAL está no DOM o tempo todo | ✅ |
| 62 | **Neon permanente** — no repouso: `#fff` + `2px` branco a 65% + `6px` na cor do grupo + `11px` na cor a 20% de alfa. O pico (t≈801) é visivelmente mais intenso (`28px`) | ✅ |
| 63 | **Halos não se misturam** — folga entre as TINTAS (precisa de 22px): `the-godfather` e `cidade-de-deus` **32,17px** nos dois tamanhos; `cats-2019` (`~7%`·`~7%`) 32,17/32,18px; par mais apertado do catálogo, `eighth-grade` a 375px, **28,55px**. Zero misturas | ✅ |
| 64 | **`prefers-reduced-motion`, sentido A** — 0 animações, `--k = 1`, camadas nas larguras finais, números em opacidade 1 com **o `text-shadow` de repouso completo aplicado**: o neon permanente FICA | ✅ |
| 65 | **`prefers-reduced-motion`, sentido B** — reativando, as 10 animações voltam e a sequência re-arma do zero (`--k = 0`, números em 0, indicadores em 0) | ✅ |
| 66 | **`aria-label` e texto** — idênticos nos dois estados, sempre com os valores finais; o estado de terços nunca aparece em texto | ✅ |
| 67 | **Sair no meio e voltar** — saída forçada a 300ms (meio da Fase A, `k = 0,887`) em `cats-2019` e volta pelo histórico: a página remonta, a sequência recomeça e termina no estado final | ✅ |
| 68 | **Conferência barra × cabeçalhos × callout nos 35** — no estado final, a fronteira na meia altura bate com o `share_real` normalizado nos 35; **zero divergência**, igual à v1.9.26/v1.9.27. Cabeçalho, callout e `aria-label` imprimem o mesmo inteiro nos 35 | ✅ |
| 69 | **Ramo sem distribuição (`teste-degradado`)** — sem barra, sem callout, sem animação, e a nota da v1.2.1 no lugar | ✅ |
| 70 | **Sem overflow horizontal** — os 6 filmes do aceite, nos dois tamanhos | ✅ |

## O que este teste NÃO cobre

- **Nenhum teste automatizado de frontend**, como sempre.
- **A sequência em velocidade real** — ver a ressalva de método.
- **Amostragem de pixel** — a cobertura é provada por hit-test (cenário
  56), que é coisa diferente e mais fraca em um aspecto: prova que há
  sempre uma camada opaca sob cada ponto, não que a cor pintada ali seja a
  esperada.
- **Navegador sem `@property`** — a degradação (deslize vira salto no meio
  da duração, estado final correto) está raciocinada em §3[E], não testada:
  não há navegador assim disponível neste ambiente.
- **Leitor de tela real.**
