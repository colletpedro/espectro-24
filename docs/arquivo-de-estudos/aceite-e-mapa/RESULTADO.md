# Espectro 24 — Resultado do teste de viabilidade (Fase 0)

**Data:** 2026-07-18
**Fonte:** Letterboxd (`letterboxd.com/film/<slug>/reviews/`)
**Filmes testados:** `oppenheimer-2023` (bem coberto) e `cidade-de-deus` (segundo caso, modo degradado)
**Requisições gastas nesta sessão:** 13 (limite ~15), delay de 2s mantido, sem paralelismo.

---

## Veredito por teste

| Teste | oppenheimer-2023 | cidade-de-deus |
|-------|------------------|----------------|
| **[1] Acesso** | ✅ 200 (após ajuste de headers) | ✅ 200 |
| **[2] URL por nota** | ✅ os 3 formatos → 200; `3.5` filtra de fato | ✅ os 3 formatos → 200 |
| **[3] Extração** | ✅ 12/12 após corrigir seletores | ✅ 12/12 (1 spoiler detectado) |
| **[4] Aproveitamento** | ✅ 83% (10/12 válidas) | ⚠️ 33% (4/12 válidas) — modo degradado |

**Conclusão geral:** a coleta é **viável** com `requests` + `beautifulsoup4`, sem necessidade de `curl_cffi`, proxies ou qualquer técnica de evasão. Foram necessários dois ajustes no script (headers e seletores), documentados abaixo.

---

## [1] Acesso / anti-bot

- **Primeira tentativa: 403.** O `User-Agent` sozinho não passa.
- **Correção 5a (headers extras) resolveu.** Adicionar `Accept`, `Referer`, `Upgrade-Insecure-Requests` e a família `Sec-Fetch-*` / `Sec-Ch-Ua` fez o acesso retornar **200**. **Não foi preciso escalar para `curl_cffi`** (passo 5b) nem parar (5c).
- ⚠️ **Armadilha encontrada:** incluir `br` (Brotli) em `Accept-Encoding` fez o servidor responder `content-encoding: br`, que o `requests` **não decodifica** → `resp.text` vinha como bytes ilegíveis, com status 200 "falso-positivo" e a extração encontrando 0 elementos. **Correção:** anunciar apenas `Accept-Encoding: gzip, deflate`. (Alternativa futura: instalar `brotli`/`brotlicffi` se quiser aceitar `br`.)

## [2] Formato da URL de filtro por nota — **CONFIRMADO**

Formato para a spec:

```
https://letterboxd.com/film/<slug>/reviews/rated/<N>/by/activity/
```

- **Use o formato decimal:** `N ∈ {0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5}` — ex.: `rated/3/`, `rated/3.5/`.
- **Verificado que filtra de verdade:** `rated/3.5/` retornou 12 reviews, **todas ★★★½ (3.5)**. Não é apenas 200 vazio — o filtro é real.
- Os três candidatos (`3`, `3.5`, `3½`) retornaram **200**. O glifo `3½` também é aceito (a própria UI do Letterboxd o usa), mas **padronize no decimal** por ser mais limpo em código e não exigir encoding de caractere especial.

## [3] Seletores CSS — **PRECISARAM DE AJUSTE (corrigidos no script)**

A estrutura mudou desde a versão original do script. Layout atual (jul/2026):

| Alvo | Seletor **antigo** (quebrado) | Seletor **atual** (corrigido) |
|------|-------------------------------|-------------------------------|
| Container do review | `li.film-detail` / `div.film-detail-content` | `article.production-viewing` |
| Texto do review | `.body-text` / `.js-review-body` | `.body-text` / `.js-review-body` *(inalterado, ainda funciona)* |
| Nota | `span.rating` com classe `rated-N` (N = estrelas×2) | `span.inline-rating` com **glifos de estrela** |

- **Parsing da nota mudou:** não existe mais a classe `rated-N`. A nota vem como texto de estrelas em `span.inline-rating`, ex. `★★★½`. Regra: `nota = texto.count("★") + (0.5 se "½" in texto)`.
- **Spoiler:** confirmado funcionando. Reviews marcadas como spoiler vêm com o corpo substituído pelo placeholder *"This review may contain spoilers. I can handle the truth."* (~57 chars). A heurística de texto/classe do script detecta corretamente (`spoiler=True`). **Bônus:** como o corpo real fica atrás de `data-full-text-url`, a review de spoiler é filtrada **duas vezes** — pelo flag de spoiler **e** pelo mínimo de 150 chars.
- Os fallbacks para o layout antigo foram mantidos no script, então ele degrada com elegância se a estrutura voltar a mudar.

## [4] Taxa de aproveitamento

Filtros da spec: **nota presente + ≥150 chars + sem spoiler**. Amostra = página base (12 reviews/página, ordenada por atividade).

| Filme | Extraídas | Com nota | Válidas | **Taxa** | Raw p/ 20 válidas @ essa taxa |
|-------|-----------|----------|---------|----------|-------------------------------|
| oppenheimer-2023 | 12 | 12 | 10 | **83%** | ~24 |
| cidade-de-deus | 12 | 12 | 4 | **33%** | ~60 |

**Por que a diferença (modo degradado):** `cidade-de-deus` atrai muitas reviews curtas de uma linha (ex.: *"bené, eu te amava muito"* = 23 chars; *"never seen a movie change from story to story..."* = 59 chars) e uma spoiler. O corte de 150 chars derruba a maioria. Esse é o cenário realista de pior caso para filmes com fanbase que escreve reviews curtas/afetivas.

---

## Recomendação para a spec v1.0.0

**Quantas reviews brutas buscar por bucket para atingir 20 válidas:**

- **Adote o piso de ~33% de aproveitamento** (pior caso observado), não os 83% do caso bom. `20 / 0.33 ≈ 61`.
- **Meta prática: ~72 reviews brutas por bucket** (= 6 páginas de 12), com paginação `.../by/activity/page/<n>/`.
- **Estratégia adaptativa (recomendada):** para cada bucket, paginar dentro dos níveis de nota que o compõem até **atingir 20 válidas OU esgotar o bucket OU bater o teto de ~6 páginas**, o que vier primeiro. Filmes bem cobertos fecham em 2–3 páginas (~24–36 raw); só os degradados precisam das 6.

**Como montar cada bucket via a URL de filtro** (cada bucket agrega vários níveis de nota):

| Bucket | Níveis de nota (`rated/N/`) | Nº de níveis |
|--------|------------------------------|--------------|
| Negativas | 0.5, 1, 1.5, 2, 2.5 | 5 |
| Medianas | 3, 3.5 | 2 |
| Positivas | 4, 4.5, 5 | 3 |

⚠️ **Bucket mais apertado = Medianas** (só 2 níveis de nota alimentando-o). Para filmes menos populares, alguns buckets podem simplesmente **não ter 20 reviews válidas disponíveis** — a spec deve aceitar `< 20` quando o bucket está esgotado, em vez de paginar infinitamente.

### Notas / incógnitas restantes para a spec
- **Paginação (`/page/2/` etc.) não foi exercida nesta sessão** (para respeitar o teto de requisições) — assumida como o padrão do Letterboxd; **confirmar na Fase 1** que a página 2 dos filtros `rated/N/` funciona e não repete conteúdo.
- **Anti-bot:** manter delay ≥2s e os headers de navegador. Se o Letterboxd endurecer, o plano B já validado é `curl_cffi` com `impersonate="chrome"` (não foi necessário agora).
- **Encoding:** fixar `Accept-Encoding: gzip, deflate` no cliente (ou instalar suporte a Brotli) para não cair na armadilha do corpo ilegível.
- **Texto completo de reviews longas/colapsadas:** o corpo às vezes fica atrás de `data-full-text-url` (`/s/full-text/viewing:<id>/`). Para o resumo por LLM pode ser necessário buscar esse endpoint — avaliar na spec se o trecho visível já basta.
