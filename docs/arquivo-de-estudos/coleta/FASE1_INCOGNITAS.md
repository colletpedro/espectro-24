# Espectro 24 — Fase 1, Etapa A: resolução das incógnitas (SPEC §6)

**Data:** 2026-07-18
**Requisições ao Letterboxd nesta etapa:** **10** (limite 15). Delay ≥2s, sem paralelismo.
**Veredito do GATE:** ✅ **PASSA — nenhuma incógnita contradiz a spec de forma fatal.** As três foram resolvidas; há **3 refinamentos** que não invalidam a spec mas devem virar clarificações (candidatos a v1.1.1, listados no fim). **Etapa B liberada.**

Fixtures salvos em `fixtures/` (dados de teste da Etapa B) — lista no fim.

---

## A1 — Paginação (SPEC §6.1)

Testado em `oppenheimer-2023`, nível `rated/5/`, `.../by/activity/page/<n>/`.

| Verificação | Resultado |
|---|---|
| (a) `page/2` retorna 200 com conteúdo | ✅ 200, 12 reviews |
| (b) `page/2` não repete `page/1` (comparado por **viewing id**, não texto) | ✅ interseção **vazia** (12 ids distintos em cada) |
| (c) página além da última (`page/9999`) | ✅ **200 com lista vazia** (0 `article.production-viewing`) — sinal limpo de parada |

**Veredito:** paginação confiável. **Regra de parada da coleta:** parar o nível quando uma página retorna **0 reviews** (além de: 10 válidas atingidas OU teto de 6 páginas). Não há erro/redirect a tratar em out-of-range.

**Achado importante (viewing id):** a extração de id **não deve** depender de `data-full-text-url` — em `page/2` um review não o tinha. A fonte robusta e universal é o botão de like:

```
p[data-likeable-identifier]  →  JSON  →  uid = "viewing:<id>"
```

Presente em 12/12 reviews nas duas páginas. É a chave de **deduplicação** e de **cache por review**.

---

## A2 — Busca de slug (SPEC §6.2, pipeline [A])

**Refinamento vs spec:** a URL da spec (`letterboxd.com/search/films/<query>/`) retorna apenas um **shell React** — o container `#search-table-body` vem **vazio** no HTML estático; os resultados são carregados por AJAX. O endpoint real (descoberto no atributo `data-url` do `.paginate-ajax`) é:

```
letterboxd.com/s/search/films/<query>/        (query URL-encoded; espaço = %20)
```

Esse endpoint retorna o **fragmento HTML server-rendered** com os resultados. Testado com query ambígua `city of god` → 20 resultados, incluindo a desambiguação esperada (2002 / 1997 / 2011 / "10 Years Later" 2013 …).

**Seletores de extração (por resultado):**

| Campo | Seletor |
|---|---|
| Linha de resultado | `li.search-result` |
| Slug | `[data-item-slug]` (no `.react-component.figure` da linha) → ex. `city-of-god` |
| Título + ano | atributo `data-item-name` → ex. `"City of God (2002)"` |
| Ano (alternativo) | `small.metadata` (texto `2002`) **ou** regex `\((\d{4})\)` sobre `data-item-name` |
| Link canônico | `data-item-link` → `/film/city-of-god/` |

Nota: alguns resultados não têm ano (ex. `the-city-of-god` → sem `small.metadata`) — tratar ano como opcional.

**Curiosidade útil:** o slug canônico de "City of God (2002)" na busca é `city-of-god`; o slug `cidade-de-deus` (usado na Fase 0) é um **alias que também resolve** para o mesmo filme. Ambos funcionam em `/film/<slug>/`.

**Veredito:** resolução de slug viável via o endpoint `/s/search/films/`. O caminho `--slug` da spec continua sendo o atalho quando o usuário já sabe o slug.

---

## A3 — Texto completo + detector de truncamento (SPEC §6.3 / C'.1 — CRÍTICO)

### Endpoint
```
letterboxd.com/s/full-text/viewing:<id>/      → 200, fragmento HTML (série de <p>, sem wrapper)
```
Existe e funciona. `content-type: text/html`, `Accept-Encoding: gzip` ok. Parse: `BeautifulSoup(...).get_text(" ", strip=True)` ou juntar os `<p>`.

### Detector de truncamento — **corrigido e validado**

⚠️ **`data-full-text-url` NÃO serve como detector** — ele está presente em **quase todos** os reviews (12/12 na página base de Oppenheimer), inclusive em reviews curtos e completos (ex. um review de 98 chars). Usá-lo como sinal → **falsos positivos** em massa (buscaria texto completo de todo review, violando "não gastar requisição com review descartável" e o custo estimado em C'.2).

**Detector correto (o "marcador de colapso" do C'.1):**
> Review é truncada ⟺ o `.body-text` contém um elemento **`.collapsed-text`** (equivalente observável: o texto visível termina com `…`).
> Reviews completos têm `<p>` diretamente sob `.body-text`, sem `.collapsed-text` e sem `…` final.

### Validação (2 positivos + 2 negativos, ground truth via endpoint)

| Caso | Detector diz | Visível | Texto completo | Δ | Correto? |
|---|---|---|---|---|---|
| review 2 (`viewing:1401220676`) | **truncada** | 420 | 3237 | +2817 | ✅ verdadeiro positivo |
| review 4 (`viewing:1401220279`) | **truncada** | 416 | 935 | +519 | ✅ verdadeiro positivo |
| review 3 (`viewing:1401220529`) | completa | 523 | 523 | 0 | ✅ verdadeiro negativo |
| review 5 (`viewing:1401219145`) | completa | 98 | 98 | 0 | ✅ verdadeiro negativo |

**Zero falsos negativos, zero falsos positivos.** O detector `.collapsed-text` distingue perfeitamente truncadas de completas. (O mesmo teste está replicado como unit test na Etapa B, rodando contra os fixtures salvos.)

### Spoiler revelado pelo texto completo? (C'.4)
Nos 4 casos testados, o texto completo **não** revelou placeholder de spoiler ausente no trecho visível. Não foi possível testar a interação **truncada + spoiler** diretamente (nenhum review nessa condição apareceu nas páginas amostradas, e não gastei requisições caçando um). **Mitigação implementada mesmo assim:** o pipeline re-roda a checagem de spoiler sobre o **texto completo** em C', então se o endpoint retornar o placeholder, o review é descartado. Risco residual baixo — na prática o placeholder de spoiler já aparece no trecho visível da listagem (observado na Fase 0).

---

## Seletores consolidados (fonte da verdade para o parser da Etapa B)

| Alvo | Seletor / regra | Fallback |
|---|---|---|
| Container de review | `article.production-viewing` | `li.film-detail` |
| Corpo do texto | `.body-text` / `.js-review-body` | — |
| Nota | `span.inline-rating` → `count("★") + (0.5 se "½")` | `span.rating` classe `rated-N` (N/2) |
| Viewing id (dedup/cache) | `p[data-likeable-identifier]` → JSON `uid` = `viewing:<id>` | `data-full-text-url` → `viewing:<id>` |
| Truncamento | `.body-text .collapsed-text` presente (texto termina em `…`) | — |
| URL de texto completo | `.body-text[data-full-text-url]` | montar de `/s/full-text/viewing:<id>/` |
| Spoiler | placeholder de texto `"…may contain spoilers…"` no corpo | marcador de classe (não observado nesta amostra) |
| Busca | endpoint `/s/search/films/<query>/`; linha `li.search-result`; slug `[data-item-slug]`; nome `data-item-name` | — |

---

## Divergências / interpretações da spec → candidatos a **v1.1.1**

1. **Detector de truncamento (C'.1):** a spec lista `data-full-text-url` como primeiro sinal ("presença de `data-full-text-url` … OU marcador de colapso"). Na prática `data-full-text-url` é quase universal e **não discrimina**; o detector correto é **exclusivamente o marcador de colapso `.collapsed-text` / `…`**. Recomendo reescrever C'.1 para remover `data-full-text-url` como sinal de truncamento (mantendo-o apenas como fonte da URL de completamento). *(Interpretei nesse sentido na implementação.)*
2. **Endpoint de busca (pipeline [A] / §2.1):** a URL de coleta de busca correta é `/s/search/films/<query>/` (AJAX), não `/search/films/<query>/` (shell React vazio). *(Implementei com o endpoint AJAX.)*
3. **Viewing id / chave de cache de review:** a spec fala em "cache por id de viewing" (C'.2) sem fixar a fonte do id. Fixei em `data-likeable-identifier.uid` por ser universal (ver A1). *(Candidato a documentar em §2.1.)*

Nenhum dos três altera parâmetros congelados (§2) nem o comportamento do pipeline — são precisões de seletor/endpoint. Por isso **não** acionaram o GATE.

---

## Fixtures salvos (`fixtures/`)

| Arquivo | Conteúdo | Usado para testar |
|---|---|---|
| `oppenheimer-2023_reviews_base.html` | página base de reviews (12, com truncadas e completas) | parsing, nota, truncamento (pos+neg) |
| `oppenheimer-2023_rated5_page1.html` / `_page2.html` | paginação de um nível | dedup por viewing id, cascata |
| `oppenheimer-2023_rated5_page9999.html` | página além da última (lista vazia) | condição de parada |
| `fulltext_pos_2_viewing1401220676.html` / `fulltext_pos_4_...html` | texto completo de truncadas | detector (positivos), completamento |
| `fulltext_neg_3_...html` / `fulltext_neg_5_...html` | texto completo de completas (== visível) | detector (negativos) |
| `search_city-of-god.html` | página de busca (shell) | documentação do endpoint AJAX |
| `search_ajax_city-of-god.html` | fragmento AJAX de resultados | extração de slug/título/ano |
| `cidade-de-deus_reviews_base.html` | fanbase "review curta" (modo degradado) | cascata, filtro de comprimento |
| `synthetic_cases.html` | fixture sintética (spoiler, ½, sem nota, truncada, curta) | parser, spoiler, cascata |

---

## Etapa B — pontos de interpretação da spec (candidatos a v1.1.1)

Registrados durante a implementação do pipeline. Nenhum contradiz um parâmetro
congelado; são escolhas onde a spec deixou margem.

1. **Caminho do cache:** §B sugere `cache/<slug>/`, mas a restrição de arquivos
   desta fase não lista `cache/` na raiz. Implementei o cache em
   **`resultado/cache/<slug>/`** (dir permitido), configurável por `--cache-dir`.
   *Candidato: fixar o caminho em §2.1.*
2. **Cota × completamento (sem backfill):** seleciono as 10 válidas por nível
   (filtro sobre texto visível) e **depois** completo as truncadas; se o
   completamento descartar alguma (§C'.3/.4), o nível pode terminar com <10 sem
   repor da lista de brutas. No smoke test `trunc-desc=0`, então não afetou. A
   spec não menciona reposição — interpretei como "não repor". *Candidato:
   decidir explicitamente se há backfill pós-C'.*
3. **Detecção de spoiler:** §2.1 cita "placeholder OU marcador de classe". Nas
   amostras só observei o **placeholder de texto** ("…may contain spoilers…");
   nenhum marcador de classe estável apareceu. Implementei detecção por texto.
   *Candidato: confirmar se existe classe de spoiler a cobrir.*
4. **Interação truncada + spoiler:** não foi possível observar uma review
   simultaneamente truncada e com spoiler para testar §C'.4 ao vivo. A lógica
   está implementada (re-checa spoiler no texto completo) e coberta por unit test
   com fixture sintética, mas o caso real permanece não-exercitado.
5. **`n_reviews_analisadas` por tema:** a spec pede frequências relativas ao total
   do bucket; uso `len(reviews_analisadas)` do bucket como denominador e confio no
   valor do LLM por tema, com fallback para esse total. *Candidato: fixar quem é a
   autoridade do denominador (código vs LLM).*
