# Espectro 24 — Especificação v1.3.0

**Data:** 2026-07-20
**Status:** v1 fechada (aceite em "Status de aceite da v1", fim do documento). v1.2.0 adiciona a etapa **[D2] narrador** (§D2) e a flag `--tom` como **mecanismo de desenvolvimento** para A/B de saída. v1.2.1 corrige uma classe de infidelidade do narrador (cota de amostragem apresentada como distribuição da recepção) — invariante nova no §D2 + telemetria. v1.2.2 adiciona calibração numérica dos quantificadores da narrativa (mapa fração→palavra, faixa mais fraca em caso de dúvida) — verificação por instrução ao LLM. v1.2.3 move a calibração do prompt para o CÓDIGO: os rótulos de quantificador passam a ser pré-computados e o LLM só os usa, não os escolhe (mesmo princípio da v1.1.1 — código como autoridade de número/rótulo). v1.3.0 adiciona uma **ficha técnica do filme via TMDB** (§3a, aditiva — nunca bloqueia o pipeline) e reestrutura §D2 para uma narrativa em **três movimentos** (filme → experiência consensual → contraste entre grupos), com uma emenda pontual à regra de "zero conteúdo de trama" para permitir a sinopse OFICIAL curta como fonte do primeiro movimento (ver §3[D] "Anti-spoiler").
**Objetivo:** dado o nome de um filme, agregar reviews de usuários do Letterboxd em três buckets por nota e produzir, via LLM, uma síntese temática de cada bucket — pontos recorrentes com frequência — permitindo entender a recepção do filme sem viés de leitura seletiva e sem spoilers.

**Público-alvo:** pessoa que ainda NÃO assistiu ao filme. Toda decisão de design que envolva trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler.

---

## 1. Escopo v1

**Dentro:** CLI/script local; fonte única Letterboxd; três buckets com cota por nível de nota; busca de texto completo de reviews truncadas; cache em disco; saída estruturada JSON + render em texto no terminal.

**Fora (explicitamente):** UI web, FastAPI, deploy, IMDB como fallback, reviews sem nota, múltiplos idiomas de saída (saída em pt-BR, reviews de entrada em qualquer idioma).

---

## 2. Parâmetros congelados

| Parâmetro | Valor | Origem |
|---|---|---|
| Buckets | Negativas 0.5–2.5 · Medianas 3–3.5 · Positivas 4–5 | Decisão de design |
| **Cota de reviews válidas POR NÍVEL de nota** | **10** | **v1.1.0 — decisão do usuário** |
| Tamanho-alvo resultante por bucket | Negativas 50 · Medianas 20 · Positivas 30 | Derivado (5/2/3 níveis × 10) |
| Piso mínimo por bucket para análise temática | 3 válidas no bucket | Análogo ao piso de predições do card-guy |
| Filtro de comprimento (padrão) | ≥ 150 chars | Decisão de design |
| Relaxamento em cascata (por nível) | 150 → 50 → sem filtro | Decisão de design |
| Teto de paginação por nível de nota | 6 páginas (~72 reviews brutas) | Fase 0: pior caso 33% de aproveitamento |
| **Texto truncado enviado ao LLM** | **PROIBIDO — texto completo obrigatório ou descarte** | **v1.1.0 — decisão do usuário** |
| Delay entre requisições | ≥ 2s, sem paralelismo | Fase 0: anti-bot presente |
| Ordenação da coleta | `by/activity` | Fase 0 (mitiga viés de "popularity" e review-piada) |
| Reviews sem nota | Descartadas | Decisão de design |
| Reviews com flag de spoiler | Descartadas na coleta | Decisão de design |

### 2.1 Parâmetros técnicos congelados (Fase 0)

| Item | Valor |
|---|---|
| URL de coleta | `letterboxd.com/film/<slug>/reviews/rated/<N>/by/activity/[page/<n>/]` |
| Formato de nota na URL | **Decimal**: `0.5, 1, 1.5 … 5` (nunca o glifo `½`) |
| **Página além da última** | **Validado (Fase 1):** retorna **200 com lista de reviews vazia** — esse é o sinal de parada da paginação, não erro/redirect |
| Endpoint de texto completo | **Validado (Fase 1):** `letterboxd.com/s/full-text/viewing:<id>/`, retorna fragmento HTML (`<p>` sem wrapper) |
| **Endpoint de busca de slug** | **Validado (Fase 1):** `letterboxd.com/s/search/films/<query>/` (AJAX, server-rendered). A URL humana `letterboxd.com/search/films/<query>/` é só um shell React — resultados vêm vazios no HTML estático dela |
| **Dedup / cache por review** | **Validado (Fase 1):** `p[data-likeable-identifier]` → JSON `uid` = `viewing:<id>`. Universal (presente em toda review); NÃO usar `data-full-text-url` para isso — ele falta em alguns casos |
| Container de review | `article.production-viewing` (fallback: `li.film-detail`) |
| Corpo do texto | `.body-text` / `.js-review-body` |
| Nota | `span.inline-rating`, parsing `count("★") + (0.5 se "½")` (fallback: `span.rating` classe `rated-N`, N = estrelas×2) |
| Spoiler | **Corrigido (Fase 1 / v1.1.1):** placeholder de texto **exato** `"This review may contain spoilers. I can handle the truth."` no corpo. Não usar substring genérica ("may contain spoilers" sozinho tem falso positivo em prosa legítima). **Ressalva:** se o Letterboxd localizar essa string para outros idiomas, o detector quebra silenciosamente — nenhum teste automatizado cobre esse cenário (ver `FASE1_INCOGNITAS.md`) |
| Headers | User-Agent de navegador + `Accept`, `Referer`, `Upgrade-Insecure-Requests`, `Sec-Fetch-*`, `Sec-Ch-Ua` |
| `Accept-Encoding` | **`gzip, deflate` apenas** (nunca `br` sem lib brotli instalada) |
| Plano B anti-bot (não ativar sem necessidade) | `curl_cffi` com `impersonate="chrome"`, mesmo delay |

---

## 3. Pipeline

```
input (nome do filme)
  → [A] resolução de slug
  → [B] coleta por nível de nota (com cache)
  → [C] filtros e cascata de relaxamento (por nível)
  → [C'] completamento de reviews truncadas
  → [D] síntese LLM por bucket
  → [D2] narrador (opcional, --tom)
  → [F] ficha do filme via TMDB (aditiva, independente de D/D2 — v1.3.0)
  → [E] render (JSON + terminal)
```

**[F] roda em paralelo conceitual a [D]/[D2]:** não depende de reviews do
Letterboxd nem é bloqueada por elas (usa só título/ano do filme, derivados
do slug — ver §3a). Uma falha em [F] nunca impede [D]/[D2]/[E] de rodar, e
vice-versa: as duas fontes de dados são independentes.

### [A] Resolução de slug
Busca via o endpoint AJAX `letterboxd.com/s/search/films/<query>/` (**corrigido na Fase 1** — a URL humana `letterboxd.com/search/films/<query>/` é um shell React vazio no HTML estático; ver §2.1); apresentar os top resultados (título + ano) e pedir confirmação do usuário quando houver ambiguidade. Se o usuário passar o slug diretamente (flag `--slug`), pular a busca.

### [B] Coleta por nível de nota
Para cada um dos 10 níveis (`rated/0.5/` … `rated/5/`), paginar até: **10 reviews válidas no nível** OU **nível esgotado** OU **teto de 6 páginas** — o que vier primeiro. A cota por nível garante que cada bucket represente todo o seu intervalo (negativas não viram só "0.5 com raiva").

Registrar por nível: `n_paginas_buscadas`, `n_brutas`, `n_validas`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_sem_nota`, `filtro_aplicado`.

**Cache:** por filme+nível+página (e por texto completo, ver C'), em disco (SQLite ou JSON por filme). Nunca rebuscar página cacheada. Cache não expira na v1.

**Caminho do cache — PROVISÓRIO (v1.1.1):** implementado em `resultado/cache/<slug>/` em vez de `cache/<slug>/` na raiz. Consequência direta da restrição de arquivos da Fase 1 (que não permitia criar `cache/` fora de `resultado/`), não uma decisão de design. Ratificado para v1.1.1 — mudar agora seria churn sem ganho. **Candidato a v1.2:** desacoplar para `cache/` ou `.cache/` na raiz — `resultado/` é semanticamente a **entrega** (descartável/versionável), enquanto o cache é **estado reconstruível caro** (dezenas a centenas de páginas HTML); misturar os dois acopla ciclos de vida opostos (ex.: limpar `resultado/` hoje também apaga o cache e força recoleta completa).

### [C] Filtros e cascata (por nível)
Ordem por review: (1) tem nota → (2) sem flag de spoiler → (3) comprimento.

Cascata avaliada por nível, após esgotar a paginação do nível:
1. Filtro padrão (≥150 chars). Se `n_validas ≥ 10`: nível completo.
2. Se `n_validas < 10`: nível em modo reduzido — segue com o que tem.
3. Se `n_validas == 0` no nível: relaxar para ≥50 chars sobre as brutas já coletadas; se ainda 0, remover filtro. Nível pode terminar vazio.

O piso de análise continua **por bucket**: se a soma de válidas dos níveis do bucket < 3, o bucket fica **sem análise temática** — exibir a **contagem** e a **URL da página de reviews do filme** (`https://letterboxd.com/film/<slug>/reviews/`), no formato `→ N review(s) disponíveis em <url>`, tanto no terminal quanto no JSON (campo global `reviews_url`). **NÃO exibir os textos brutos das reviews.**

> **Por que não exibir texto bruto (v1.1.4):** a cláusula anterior ("se houver 1–2 reviews, exibir os textos brutos com aviso") contradizia o princípio de design do cabeçalho da spec — *todo trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler*. Texto integral de review **sem** passar pela camada anti-spoiler do LLM (§D) é o caminho de **maior** risco de spoiler do produto; e a flag de spoiler do Letterboxd é **autodeclarada** (não confiável como garantia). Apontar para a página de reviews transfere a decisão de risco para o usuário, de forma consciente, em vez de o produto imprimir o texto por ele.

**Nota sobre comprimento e truncamento:** o filtro de comprimento usa o texto visível. Review truncada que já passa dos 150 chars no trecho visível é válida; o texto completo é resolvido em C'.

### [C'] Completamento de reviews truncadas — regra "nunca pela metade"
Aplicado somente a reviews que **já passaram todos os filtros** (não gastar requisição com review descartável):

1. **Detecção de truncamento — corrigido (Fase 1 / v1.1.1):** o detector é **exclusivamente o marcador de colapso `.collapsed-text`** no corpo (equivalente observável: texto visível terminando em `…`). `data-full-text-url` está presente em **quase toda review** (truncada ou não) e por isso **NÃO discrimina** — usá-lo como sinal de truncamento daria falsos positivos em massa. Validado com 2 casos positivos + 2 negativos, zero erros (ver `FASE1_INCOGNITAS.md` §A3). `data-full-text-url` continua sendo a **fonte da URL de completamento**, só não é mais o detector.
2. Para cada review truncada válida: buscar `data-full-text-url` (delay 2s, cache por id de viewing — chave via `p[data-likeable-identifier].uid`, ver §2.1).
3. Falha na busca → **uma** retentativa. Falha persistente → **descartar a review** e registrar em `n_descartadas_truncamento`. Nunca enviar texto parcial ao LLM.
4. O texto completo substitui o visível para todos os fins (inclusive re-checagem de spoiler: se o texto completo revelar o placeholder de spoiler, descartar).
5. **Sem backfill de cota na v1.1.1:** se o completamento descartar uma review (passo 3), a cota do nível fecha com o que sobrou (ex. 9/10) — **não há reposição** buscando outra bruta para substituir a descartada. Razões: (i) o shortfall fica **visível** via `n_descartadas_truncamento`, não é silencioso; (ii) o piso de 3 por bucket (§2) + modo `sem_analise` já tratam o caso degenerado sem inventar dados; (iii) backfill ingênuo tem custo de requisição **não limitado** — cada reposição pode ela mesma vir truncada e falhar, encadeando. **Candidato a v1.2**, com uma distinção que deve orientar o design: **backfill barato** (repor a partir da lista de brutas já paginadas no nível — custo = 1 requisição de full-text por reposição) é razoável; **backfill caro** (repaginar o nível para buscar mais brutas) não é — só o barato deve entrar em v1.2.
6. **SUPOSIÇÃO ABERTA — não verificada ao vivo:** o comportamento do endpoint `/s/full-text/` para uma review **simultaneamente truncada e com spoiler** é *assumido* (devolver o placeholder de spoiler, permitindo o descarte no passo 4), não confirmado com um caso real — nenhuma review nessa condição apareceu nas amostras da Fase 1. Coberto por teste com fixture sintética (caminho de código exercitado), mas **não** por um caso ao vivo. Se o endpoint devolver o texto real em vez do placeholder, o spoiler vazaria ao LLM. **Instrução operacional:** se um viewing id truncado+spoiler aparecer numa coleta futura, gastar 1 requisição para confirmar o comportamento antes de confiar cegamente nesta suposição.

Custo estimado: no pior caso ~100 requisições extras por filme novo (uma por review válida truncada), ~3 min adicionais a 2s/req. Aceitável para ferramenta pessoal com cache.

### [D] Síntese LLM
- **Uma chamada por bucket** (máx. 3 por filme), modelo configurável.
- **Provider-agnóstico (v1.1.1):** a interface de cliente injetável (`client_call(system, user, model) -> str`) é o **contrato formal**. Providers suportados: **Gemini** (chave `GEMINI_API_KEY`, modo JSON nativo) e **Anthropic** (chave `ANTHROPIC_API_KEY`). Seleção via `--provider {gemini,anthropic}`; sem a flag, auto-detecta pela chave presente no ambiente; se ambas as chaves estiverem presentes, ou nenhuma, é erro — exige decisão explícita.
- **Default de modelo Gemini — `gemini-2.5-flash` (v1.1.2, ratificado com evidência):** a comparação de modelos (`resultado/comparacao/COMPARACAO.md`) rodou o MESMO prompt sobre o MESMO corpus (`oppenheimer-2023`) em `gemini-2.5-flash-lite` e `gemini-2.5-flash`. O flash-lite cometeu **3 violações de instrução** documentadas: (1) bucket `negativas` inteiro em inglês, violando "saída sempre em pt-BR"; (2)-(3) `observacao_geral` generalizando o recorte filtrado do bucket para "a maioria dos críticos considera o filme um fracasso" — o próprio erro de enquadramento que motivou o preâmbulo de papel abaixo. O `gemini-2.5-flash`, no mesmo teste, não repetiu nenhuma das três. Default Anthropic: `claude-sonnet-4-6`.
- **Prompt PARAMETRIZADO POR BUCKET (v1.1.2)** — não mais uma string única. A parametrização é **por bucket** (nome + intervalo de notas), nunca por provider/modelo: o texto para um dado bucket é **byte-idêntico** entre Gemini e Anthropic; só o transporte (SDK, formato de chamada) muda por adaptador.
- Entrada: todas as reviews válidas do bucket (texto COMPLETO + nota), instruções fixas.
- Buckets têm tamanhos-alvo diferentes (50/20/30): frequências sempre relativas a `n_reviews_analisadas`, nunca absolutas soltas.
- **Denominador e clamp — regra de código, não de prompt (v1.1.1):**
  - `n_reviews_analisadas` é **sempre carimbado pelo código**, a partir da contagem real de reviews enviadas ao LLM naquele bucket. Qualquer valor que o LLM devolva nesse campo do JSON é **ignorado** — nunca usado, nem como fallback. (Correção de bug: a v1.1.0 fazia o inverso — confiava no valor do LLM e só usava o real como fallback.) Em modo degradado essa distinção é a diferença entre honestidade e maquiagem estatística.
  - `mencoes_aproximadas` é **clampado** para o intervalo `[0, n_reviews_analisadas]` (o código nunca aceita um numerador maior que o total de reviews do bucket, nem negativo). Quando o clamp atua, é sinal de alucinação do modelo e **fica visível, não silencioso**: o tema carrega `mencoes_clampadas: true` + `mencoes_valor_original` (o valor cru que o LLM devolveu), exibido também no render do terminal.
- Saída obrigatória em JSON:

```json
{
  "bucket": "negativas",
  "temas": [
    {
      "tema": "ritmo lento",
      "mencoes_aproximadas": 14,
      "n_reviews_analisadas": 50,
      "exemplo_parafraseado": "vários reviewers acham o segundo ato arrastado",
      "mencoes_clampadas": false,
      "mencoes_valor_original": null,
      "aspas_removidas": false
    }
  ],
  "observacao_geral": "1-2 frases de síntese do bucket",
  "idioma_invalido": false,
  "escopo_suspeito": false
}
```

(`mencoes_clampadas`/`mencoes_valor_original`/`aspas_removidas`/`idioma_invalido`/`escopo_suspeito` são carimbados pelo código pós-parsing — não fazem parte do que se pede ao LLM no prompt; ver regras abaixo.)

#### Template do prompt (SPEC — texto oficial, `build_system_prompt(bucket_nome)` em `synthesize.py`)

**a. Preâmbulo de papel — NOVO (v1.1.2), parametrizado por `{bucket_nome}` e `{intervalo}` (ex.: `negativas` / `0.5–2.5 estrelas`):**

> Você é uma etapa de um pipeline que agrega reviews de usuários de um filme do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES desta etapa (negativas, medianas, positivas); você está recebendo EXCLUSIVAMENTE a faixa "`{bucket_nome}`" (`{intervalo}`) — um recorte enviesado POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.
>
> Sua função é descrever o que ESTE grupo específico de reviews diz. Outros módulos do pipeline cuidam das outras faixas de nota; o usuário final verá as três análises lado a lado, cada uma rotulada com sua faixa.
>
> Consequência explícita: é PROIBIDO generalizar para "os críticos", "a maioria", "o consenso" ou "a recepção do filme". A `observacao_geral` deve se referir sempre a ESTE grupo (ex.: "as reviews `{bucket_nome}` apontam...", "este grupo destaca..."), nunca ao filme em termos absolutos.

**Motivação (evidência empírica):** rodando o prompt v1.1.1 (sem preâmbulo) sobre o bucket `negativas` de `oppenheimer-2023`, o flash-lite escreveu `observacao_geral: "a maioria dos críticos considera o filme um fracasso"` — generalizando um recorte filtrado por construção (só notas ≤2.5) para a opinião geral do filme. O preâmbulo ataca esse erro de enquadramento na raiz, antes de qualquer instrução de formato.

**b. Instruções fixas (invariáveis) — as 5 anteriores + 2 novas (v1.1.2):**
  1. Anti-spoiler: descrever críticas em nível temático (ritmo, atuações, fotografia, roteiro em termos abstratos); **proibido mencionar eventos da trama, destinos de personagens, reviravoltas ou o final**, mesmo que as reviews os mencionem.
  2. `exemplo_parafraseado` é paráfrase, nunca citação literal de review.
  3. Temas ordenados por `mencoes_aproximadas` decrescente; máximo 6 temas por bucket; não inventar temas com menção única salvo se o bucket tiver < 5 reviews.
  4. Reviews em qualquer idioma; saída sempre em pt-BR.
  5. Responder apenas o JSON, sem preâmbulo.
  6. **NOVO:** proibido usar aspas (simples, duplas ou angulares) dentro de `exemplo_parafraseado` — nunca citar nem reproduzir um trecho entre aspas, mesmo traduzido; reescrever sempre em terceira pessoa, com palavras próprias. **Motivação:** o `gemini-2.5-flash`, na mesma comparação, usou frases entre aspas em `exemplo_parafraseado`, violando a regra de paráfrase (citação literal, ainda que traduzida).
  7. **NOVO:** reforço de idioma — TODOS os campos de texto em pt-BR, incluindo os NOMES DOS TEMAS, independentemente do idioma das reviews de origem.
- Parsing defensivo (strip de fences, try/except) e uma única retentativa em caso de JSON inválido (inalterado, v1.1.1).

#### Validações pós-parsing (código, não prompt) — v1.1.2

Rede de segurança/telemetria — o preâmbulo de papel (acima) é a **defesa principal** contra vazamento de escopo; estas checagens são baratas e propositalmente imperfeitas (heurísticas), não substituem revisão humana.

a. **Idioma:** heurística de contagem de stopwords pt-BR vs. inglês sobre a concatenação de `temas` + `exemplos` + `observacao_geral`. Ausência de stopwords de qualquer idioma (texto curto/indeterminado) **não** conta como violação — só conta quando há evidência de maioria em outro idioma. Se detectar não-pt-BR: **uma retentativa**, com instrução de idioma reforçada anexada ao FIM do prompt (não substitui o preâmbulo/instruções). Se persistir: aceita o resultado da retentativa e registra `idioma_invalido: true` no bucket (visível no render).
b. **Aspas:** se qualquer `exemplo_parafraseado` contiver aspas de citação (`" ' “ ” ‘ ’ « » ‹ ›`), remove-as **mecanicamente** (não é reescrita — apenas apaga os caracteres e normaliza espaços) e registra `aspas_removidas: true` **no tema**. **Sem retentativa** — correção mecânica basta, não vale gastar uma chamada de LLM.
c. **Escopo:** checagem barata na `observacao_geral` por marcadores literais de generalização ("a maioria dos críticos", "o consenso", "os críticos consideram", "amplamente aclamado", "amplamente rejeitado"). Se encontrar: **uma retentativa**; se persistir, aceita e registra `escopo_suspeito: true` no bucket. Heurística imperfeita por design (lista curta e literal, não NLP) — o preâmbulo de papel é a defesa principal; isto é rede de segurança e telemetria.

**Retentativa combinada:** se idioma **e** escopo falharem na mesma resposta, é feita **UMA única chamada extra** que reforça os dois ao mesmo tempo (não duas retentativas separadas) — mantém o orçamento de chamadas por bucket previsível (no máximo 1 retentativa de JSON + 1 retentativa de validação = 3 chamadas no pior caso por bucket).

#### Anti-spoiler: escopo da proteção e risco aceito (v1.1.3)

> **RISCO ACEITO** (decisão do usuário, 2026-07-19, validada com juiz humano que conhecia o filme — *Cure*, 1997): a proteção anti-spoiler cobre eventos da trama, desfechos e destinos de personagens. A zona cinzenta "mecanismo/dispositivo central da trama" (ex: nomear a técnica que conecta os eventos) é **risco aceito e NÃO deve ser endurecida**: instruções mais restritivas degradariam a especificidade dos temas em todos os filmes para evitar um falso negativo raro e tolerável. Saídas nessa zona são comportamento dentro do risco aceito, não bug.

> **EMENDA — sinopse oficial curta como fonte do MOVIMENTO 1 (v1.3.0, decisão do usuário, 2026-07-20):** a regra de "zero conteúdo de trama" continua valendo para reviews e para o conhecimento próprio do modelo, mas ganha uma exceção estreita e explícita: a **sinopse OFICIAL** de um filme (campo `overview` do TMDB — material de divulgação curado pelo próprio estúdio/distribuidor, categoria equivalente à sinopse de contracapa/poster) pode ser usada, condensada, como fonte do MOVIMENTO 1 da narrativa (§D2). Justificativa: esse texto é escrito para ser lido por quem ainda não assistiu — é a mesma informação que o usuário veria no pôster ou na página do filme antes de decidir assistir; não é "conteúdo de trama" no sentido que a regra original protege (revelações extraídas de reviews de quem já assistiu, ou conhecimento factual do modelo sobre o filme). O que **continua proibido**, sem exceção:
> - sinopses de **terceiros** (não oficiais — resenhas, wikis, sinopses de outros catálogos) como fonte de premissa;
> - **expansão** da sinopse oficial com qualquer conhecimento externo do modelo sobre o filme, elenco, direção ou produção;
> - usar a sinopse oficial para justificar relaxar o anti-spoiler dos MOVIMENTOS 2/3 (temas dos buckets) — a fronteira entre síntese validada e reviews brutas (§D2, "Decisão de arquitetura") não muda.
>
> Ressalva operacional: a sinopse oficial do TMDB é, na prática observada, quase sempre limitada à premissa (é material de marketing) — mas não há garantia formal disso. Por isso o prompt do narrador (§D2) instrui explicitamente: se a `sinopse_oficial` parecer revelar algo além da premissa inicial, usar só a parte que é premissa. Essa é uma instrução ao LLM (julgamento, não checagem mecânica) — no mesmo espírito de risco aceito do parágrafo acima, não um novo validador de código.

### [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0)

Etapa **PÓS-síntese**, opcional, controlada pela flag `--tom` (ver abaixo). Uma **única chamada LLM para o filme inteiro** (não por bucket), mesmo provider/modelo da síntese.

**Decisão de arquitetura (invariante, inalterada desde v1.2.0):** o narrador recebe **EXCLUSIVAMENTE o JSON validado** — os temas, `mencoes_aproximadas`, `n_reviews_analisadas` e `observacao_geral` dos 3 buckets, o total de reviews, e (v1.3.0) a **ficha técnica** do filme quando existir (§3a). **NUNCA as reviews brutas.** Ele reescreve informação **já validada** como prosa; não tem acesso a nada que as validações (§D) não tenham aprovado, nem a nada que não venha da ficha oficial do TMDB. Isso é garantido **por construção**: a entrada do narrador é o dict de saída de `build_output` (que não serializa texto de review) mais o campo `ficha` (que vem só do TMDB, nunca de reviews).

Por que essa fronteira (justificativa anti-embelezamento / anti-spoiler): dar reviews brutas ao narrador reabriria os dois riscos que o pipeline inteiro existe para conter — (1) **spoiler**, pois texto integral não passou pela camada anti-spoiler do LLM; e (2) **embelezamento/infidelidade**, pois o narrador poderia "florear" com material não contabilizado, quebrando a fidelidade às frequências. Lendo só o relatório validado (+ ficha oficial), o narrador não pode afirmar nada que a camada de baixo não tenha aprovado.

**v1.3.0 — narrativa em três movimentos:** a v1.2.x produzia um único bloco de prosa livre. A v1.3.0 estrutura esse bloco em três movimentos sequenciais, sem subtítulos visíveis no texto final (a divisão organiza o LLM, não aparece como marcação para o leitor) — motivada pela interface em vídeo que consome a narrativa em três passos de review: apresentar o filme, descrever a experiência de assisti-lo, e só então contrastar as reações.

1. **MOVIMENTO 1 — O FILME** (2-3 frases; só existe se houver `ficha` no relatório — sem ficha, a narrativa começa direto no Movimento 2): premissa a partir da `sinopse_oficial` do TMDB (pode condensar, PROIBIDO expandir com conhecimento externo — ver emenda de anti-spoiler em §3[D]), diretor, gênero, ano; duração só se for relevante ao que os movimentos 2/3 dizem.
2. **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): como é assistir ao filme, usando **apenas** características em que os grupos **concordam factualmente mesmo divergindo na avaliação** (ex.: negativas dizem "lento e tedioso", positivas dizem "lento e deliberado" → fato consensual: "ritmo lento e contemplativo"). Tom neutro, sem valência — descreve, não julga; a avaliação fica para o Movimento 3. Sem consensos claros o suficiente, o movimento pode ser curto (1-2 frases), nunca forçando um consenso que os dados não sustentam.
3. **MOVIMENTO 3 — O CONTRASTE** (enxuto — ~40% menor que a narrativa única da v1.2.x): as perspectivas dos três grupos, priorizando os 2-3 temas **mais fortes** de cada grupo em vez de cobrir todos os até 6 possíveis — decisão motivada pela interface, que já exibe as barras de frequência tema a tema (a narrativa não precisa duplicar essa cobertura completa). Mantém **todas** as invariantes vigentes desde v1.2.x (rótulos de quantificador pré-computados, escopo por grupo, proibição de prevalência entre grupos, sem aspas, anti-spoiler, pt-BR).

Alvo de tamanho total: **250-400 palavras** (ajustado de 200-350 na v1.2.x — o movimento 1 adiciona conteúdo quando há ficha).

**Prompt fixo do narrador (SPEC — texto oficial, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`):**

> Você recebe um RELATÓRIO DE RECEPÇÃO já validado de um filme: três grupos de reviews separados por faixa de nota (negativas, medianas, positivas), cada um com seus temas, frequências aproximadas e uma observação; e, quando disponível, uma FICHA TÉCNICA do filme (sinopse oficial, diretor, gênero, ano, duração — fonte: TMDB). Sua tarefa é reescrever esse material como um texto corrido e envolvente, em TRÊS MOVIMENTOS, SEM subtítulos ou marcações entre eles (a divisão é para você se organizar, não para aparecer no texto), NESTA ORDEM:
>
> **MOVIMENTO 1 — O FILME** (2-3 frases; SÓ escreva este movimento SE houver FICHA TÉCNICA no relatório — sem ficha, comece direto no MOVIMENTO 2): apresente a premissa do filme a partir da `sinopse_oficial` da ficha — pode condensá-la, mas é PROIBIDO expandi-la com qualquer conhecimento externo sobre o filme, elenco, direção ou produção que não esteja na ficha fornecida. Se a `sinopse_oficial` parecer revelar algo além da premissa inicial do filme, use só a parte que é premissa e ignore o resto (a ficha NÃO tem passe livre sobre a regra de anti-spoiler abaixo). Mencione diretor, gênero e ano; duração só se for relevante para o que os dois movimentos seguintes vão dizer.
>
> **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): descreva como é assistir ao filme usando APENAS características em que os grupos CONCORDAM factualmente, mesmo divergindo na avaliação — ex.: se as reviews negativas chamam o ritmo de "lento e tedioso" e as positivas de "lento e deliberado", o fato consensual compartilhado por trás da divergência é "ritmo lento e contemplativo". Tom NEUTRO, SEM valência — este movimento descreve, não julga; gostar ou não gostar fica para o MOVIMENTO 3. É PROIBIDO importar qualquer informação que não venha dos temas validados dos três grupos. Se não houver consensos claros o bastante entre os grupos, este movimento pode ser curto (1-2 frases sobre o que os dados permitem dizer, sem forçar um consenso que os dados não sustentam).
>
> **MOVIMENTO 3 — O CONTRASTE** (enxuto — a interface já exibe as barras de frequência tema a tema, então aqui priorize os 2-3 temas MAIS FORTES de cada grupo, não a cobertura completa dos 6 possíveis): as perspectivas dos três grupos — quem não gostou, quem ficou no meio, quem gostou — sobre o filme. Neste movimento (e em qualquer lugar do texto que fale de grupos) valem as invariantes abaixo, TODAS ainda em vigor:
>
> a. **PAPEL:** o texto inteiro é para alguém que está DECIDINDO se assiste ao filme e que AINDA NÃO ASSISTIU.
> b. **FIDELIDADE:** toda afirmação deve derivar da ficha técnica e/ou dos temas e números recebidos. É PROIBIDO adicionar fatos, opiniões próprias, ou qualquer contexto externo sobre o filme, elenco, direção ou produção que não esteja no relatório. Se não está nos dados, não existe.
> c. **TAMANHO DOS GRUPOS — REGRA CRÍTICA:** os três grupos NÃO têm o tamanho da opinião real do público. O tamanho de cada grupo é fixado pelo MÉTODO DE COLETA (uma cota fixa por faixa de nota), não pela quantidade de pessoas que pensam assim — as medianas, por exemplo, serão sempre o menor grupo por construção, em todo filme. Portanto é PROIBIDO comparar tamanhos entre grupos ou inferir prevalência global: NADA de "a maioria dos espectadores", "a maioria do público", "grupo maior", "grupo menor", "minoria", "igualmente expressivo", "recepção polarizada", "opiniões divididas", "consenso" ou qualquer equivalente. Trate cada grupo como uma PERSPECTIVA, não como uma fatia quantificada do público: apresente-os como "entre quem não gostou...", "já entre quem amou...", "para quem ficou no meio-termo...".
> d. **PROPORÇÕES (só DENTRO de um grupo):** proporções são permitidas APENAS internamente a um grupo e SEMPRE ancoradas ao denominador daquele grupo. NUNCA uma proporção que compare grupos ou fale do público como um todo.
> **QUANTIFICADOR PRÉ-COMPUTADO (obrigatório, v1.2.3):** cada tema do relatório já vem com um `rótulo_quantificador` calculado pelo CÓDIGO a partir da fração real de menções — você NÃO calcula nem escolhe o quantificador sozinho. Ao expressar a frequência de um tema em prosa, USE o `rótulo_quantificador` fornecido para aquele tema (sinônimos de mesma força são permitidos: "a maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma parte"). É PROIBIDO usar um quantificador MAIS FORTE do que o fornecido. Um quantificador MAIS FRACO é permitido se a fluência do texto pedir — nunca o oposto. Escala de força, do mais fraco ao mais forte: poucos < alguns/uma parte < muitos/boa parte < cerca de metade < a maioria/mais da metade < quase todos/praticamente todos.
> e. **ESTRUTURA:** a divisão em três grupos (quem não gostou / quem ficou no meio / quem gostou) deve permanecer legível na prosa do MOVIMENTO 3, em qualquer ordem que sirva à narrativa.
> f. **ESCOPO:** cada afirmação sobre um grupo é atribuída ao SEU grupo ("as reviews negativas apontam...", "quem deu notas altas destaca..."). É PROIBIDO generalizar para "os críticos", "a maioria" (do filme todo) ou "o consenso".
> g. **ANTI-SPOILER:** em QUALQUER movimento (incluindo o 1, com a sinopse oficial), é PROIBIDO mencionar eventos de trama, personagens específicos ou desfechos, mesmo que a sinopse ou algum tema tangencie isso (defesa em profundidade — a camada anterior já filtra os temas, você reforça, e a sinopse oficial é tratada com a mesma cautela).
> h. **FORMA:** português do Brasil, SEM aspas de citação, SEM subtítulos ou rótulos dos movimentos no texto final, entre 250 e 400 palavras ao todo.
>
> Responda APENAS com JSON puro no formato: `{"narrativa": "<seu texto>"}`

**Por que a invariante (c) existe (v1.2.1 — defeito corrigido):** os buckets têm tamanhos fixados pela **cota de coleta** (50/20/30 = 10 válidas × nº de níveis de nota do bucket: 5/2/3), que **não** refletem a distribuição real da recepção. A narrativa da v1.2.0, sem a regra (c), inferia prevalência a partir das cotas ("grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada") — as medianas seriam "minoria" em todo filme, para sempre, por construção. A invariante (c) é a **defesa principal**; a telemetria abaixo é a rede de segurança.

**Por que o quantificador virou pré-computado (v1.2.3 — reincidência corrigida pela raiz):** a v1.2.2 tentou corrigir a inflação de quantificadores por INSTRUÇÃO — pedir ao LLM que calculasse a fração e escolhesse o rótulo por uma tabela. Funcionou parcialmente, mas **reincidiu**: na primeira regeneração das 3 narrativas pós-fix, "quase todos"/"praticamente todos" foi aplicado a frações de 65-70% **2 vezes** (a condição de escalada que o próprio changelog da v1.2.2 previa: *"um checador numérico pós-parsing é candidato futuro caso a inflação reincida"*). A correção pela raiz é o **mesmo princípio da v1.1.1** (denominador de `n_reviews_analisadas`): o LLM não decide número nem rótulo numérico — **o código é a autoridade**. `_serialize_output_for_narrator` agora pré-computa `fracao`/`rótulo_quantificador` por tema (`_fracao_e_rotulo`, mapa determinístico em `_rotulo_quantificador` — mesmas faixas da v1.2.2, resolução de sobreposição sempre para o rótulo mais fraco) e os injeta na entrada do narrador; o prompt (d) deixou de pedir cálculo e passou a proibir só usar um rótulo MAIS FORTE que o dado. **Rede de segurança complementar (v1.2.3):** checagem em nível de bucket — se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço; se persistir, `quantificador_suspeito: true`. Deliberadamente restrita a esse quantificador (o único modo de falha observado) — não cobre uso indevido dos demais rótulos.

**Por que o Movimento 1 é condicional à ficha (v1.3.0):** a ficha TMDB é aditiva por design (§3a) — pode faltar (API fora do ar, filme não encontrado, `--no-ficha`). Sem ela não há `sinopse_oficial` para ancorar o Movimento 1, e nada no prompt permite ao narrador inventar uma premissa a partir dos temas de review (violaria (b) FIDELIDADE e a proibição de conhecimento externo). Por isso o prompt instrui explicitamente pular para o Movimento 2 quando a ficha está ausente — mesmo comportamento defensivo do resto do pipeline (buckets `sem_analise` não inventam temas; a ficha ausente não inventa premissa).

O formato de saída `{"narrativa": ...}` reusa os mesmos adaptadores de provider (modo JSON nativo) e o parsing defensivo do §D. Sobre a prosa retornada aplicam-se as **mesmas validações pós-parsing** que fazem sentido para texto livre: **aspas** (remoção mecânica → `aspas_removidas`), **idioma**, **escopo**, **(v1.2.1) prevalência** e **(v1.2.3) quantificador** (ver acima) — inalteradas pela reestruturação em movimentos da v1.3.0, elas operam sobre o texto final completo, independente de quantos movimentos o compõem. Todas com 1 retentativa combinada (reforço anexado ao prompt); se persistir, aceita e sinaliza a flag correspondente (`idioma_invalido`/`escopo_suspeito`/`prevalencia_suspeita`/`quantificador_suspeito`). Heurísticas **acento-sensíveis** como as demais (rede de segurança; a defesa principal é a invariante/pré-computação do prompt). A narrativa entra no JSON no campo global **`narrativa`** (+ `narrativa_flags` de telemetria).

**Flag `--tom {estruturado,narrativo,ambos}` — MECANISMO DE DESENVOLVIMENTO (não é feature final):** existe para o **teste A/B humano** entre a saída estruturada (atual) e a narrativa durante o desenvolvimento. `estruturado` (default) mantém o comportamento histórico intacto; `narrativo` imprime só a prosa **mas os metadados de coleta e os avisos NUNCA somem** — modo degradado (sem_analise/reduzido) e flags continuam visíveis nos dois tons; `ambos` imprime os dois lado a lado. `narrativo`/`ambos` gastam **+1 chamada LLM** (o narrador). **A v2 consolidará um tom único** após a avaliação humana do A/B; até lá, `--tom` é dev-only. (Atalho de A/B: `--reuse-synthesis` reaproveita a síntese de um JSON já gerado, gastando só a chamada do narrador — para comparar tons sobre a MESMA síntese.)

### [F] Ficha do filme (TMDB) — v1.3.0

Etapa **aditiva e independente** do resto do pipeline (`ficha.py`): dado o título/ano do filme (derivados do slug por default — `titulo_ano_de_slug`, com override via `--titulo`/`--ano` no CLI para os casos em que o slug não carrega ano, ex. `cure`), busca a ficha técnica na API pública do TMDB (`api.themoviedb.org/3`).

**Resolução do ID:** `GET /search/movie?query=<título>&language=pt-BR[&year=<ano>]`. Quando `ano` está disponível, é usado tanto como parâmetro de busca quanto para desambiguação pós-resposta: entre os candidatos com `release_date` no ano pedido, prefere o de maior `popularity` do TMDB — **não** o primeiro da lista. Necessário porque títulos comuns podem devolver mais de um candidato do MESMO ano (ex. "The Invite" tem múltiplas entradas no TMDB; "Cure" 1997 devolve o filme de Kiyoshi Kurosawa E um documentário obscuro do mesmo ano) — a ordem da API não é por relevância quando o filtro de ano está ativo. Medido ao vivo na regeneração da v1.3.0: escolher o primeiro resultado do ano pegou o documentário (`popularity=0.28`, 1 voto) em vez do filme correto (`popularity=3.79`, 820 votos); corrigido para desempate por popularidade antes da entrega.

**Detalhes:** `GET /movie/{id}?language=pt-BR&append_to_response=credits`. Extraídos: título pt-BR (`title`), sinopse oficial (`overview`), gêneros (`genres[].name`), duração (`runtime`), diretor (primeiro `credits.crew[]` com `job == "Director"`), ano (`release_date[:4]`).

**Fallback de sinopse:** se `overview` vier vazio na resposta pt-BR (acontece para filmes com localização incompleta no TMDB), uma segunda chamada com `language=en-US` busca o overview em inglês; a ficha carrega esse texto com a flag `sinopse_fallback_en: true` — nunca fica silenciosamente vazia, mas também nunca finge ser pt-BR quando não é.

**Cache em disco** (mesmo padrão do cache do Letterboxd em `fetcher.py`, raiz própria `<cache-dir>/_tmdb/`): chave determinística por `título_normalizado[_ano]`; nunca rebusca filme já buscado, inclusive "não encontrado" (evita reconsultar buscas vazias). Diferente do cache de rede do Letterboxd, falhas transitórias (rede, HTTP não-200) **não são cacheadas** — podem ser passageiras, vale tentar de novo na próxima execução; só resultado de sucesso ou "sem resultado" persistem.

**Falha nunca bloqueia (decisão de design central desta etapa):** chave ausente, erro de rede, HTTP não-200, ou filme não encontrado → `buscar_ficha` retorna `(None, aviso)`. O CLI imprime o aviso em stderr e segue o pipeline inteiro (coleta, síntese, narrador, render) com `output["ficha"] = None`. Nenhuma exceção de `ficha.py` escapa para o `main()` do CLI.

**Saída:** campo global `ficha` no JSON (§4), formato:
```json
{
  "titulo": "Cure", "sinopse_oficial": "...", "sinopse_fallback_en": false,
  "generos": ["Suspense", "Terror"], "duracao_min": 111,
  "diretor": "Kiyoshi Kurosawa", "ano": 1997, "fonte": "tmdb"
}
```
`null` quando a ficha não foi obtida (busca falhou, `--no-ficha`, ou filme não encontrado).

**Consumo:** a ficha (quando presente) é serializada para o narrador (§D2) como fonte exclusiva do MOVIMENTO 1; fora do modo narrativo, o render estruturado/terminal também exibe um resumo de uma linha da ficha, quando existe (título/ano/diretor/gênero/duração), separado dos buckets e sem interferir nos avisos existentes.

### [E] Render
1. `resultado/<slug>.json` — objeto completo: 3 buckets + metadados por nível e globais.
2. Terminal — por bucket: título, `n_validas/alvo` (com decomposição por nível quando houver nível degradado), filtro aplicado, temas com frequência relativa ("mencionado em ~14 de 50 reviews"), observação geral. Avisos de modo reduzido/degradado sempre visíveis e concretos ("análise negativa baseada em apenas 7 de 50 reviews-alvo — interprete com cautela").
3. Rodapé: contagem total de reviews observada, para distinguir "bucket vazio porque ninguém odeia" de "bucket vazio porque ninguém assistiu".

---

## 4. Metadados obrigatórios no output

Por nível: `n_validas`, `n_brutas`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_descartadas_truncamento`, `paginas_buscadas`.
Por bucket: agregados dos níveis + `modo` (completo/reduzido/sem_analise) + **(v1.1.2)** `idioma_invalido`, `escopo_suspeito`.
Por tema: **(v1.1.2)** `aspas_removidas`, além de `mencoes_clampadas`/`mencoes_valor_original` (v1.1.1).
Globais: `slug`, `data_coleta`, `origem` (cache/rede por página), versão da spec, **(v1.1.4)** `reviews_url`, **(v1.2.0)** `narrativa` + `narrativa_flags` (só quando `--tom narrativo|ambos`), **(v1.3.0)** `ficha` (objeto TMDB ou `null` — §3a).

---

## 5. Critérios de aceite da v1

1. Filme popular (ex: `oppenheimer-2023`): 10 níveis completos (10 válidas cada), temas coerentes, zero spoilers na saída (verificação manual).
2. Filme de fanbase "review curta" (ex: `cidade-de-deus`): o filtro de comprimento descarta reviews curtas em volume, a coleta fecha os níveis dentro do teto de paginação, e a análise permanece útil com observações corretamente escopadas. *(Reescrito em v1.1.4 — ver nota abaixo; o critério original presumia cascata de relaxamento/modo degradado, que `cidade-de-deus` não aciona por ser coberto demais por nível. A demonstração da cascata e do modo degradado é atribuída ao critério 3, onde ocorre de fato.)*
3. Filme obscuro (a escolher): modo degradado severo — piso de 3 por bucket respeitado, bucket sem análise renderiza aviso (contagem + `reviews_url`) e não inventa temas; a cascata de relaxamento por nível (`filtro_aplicado` assumindo 50/0) é exercitada aqui.
4. **Nenhum texto truncado chega ao LLM:** teste com filme contendo reviews longas colapsadas; verificar que todas as reviews enviadas ao LLM têm texto completo ou foram descartadas com registro.
5. Segunda execução de qualquer filme: **zero requisições de rede** (100% cache).
6. Orçamento de requisições por filme novo: típico ≤ ~80; teto absoluto = 60 (10 níveis × 6 páginas) + válidas truncadas (≤ 100) + busca de slug.

---

## 6. Incógnitas de Fase 1 — RESOLVIDAS (ver `FASE1_INCOGNITAS.md`)

As três incógnitas abaixo foram resolvidas na Fase 1; os achados já estão incorporados em §2.1 e §3 [A]/[C'] acima. Mantidas aqui só como registro histórico.

1. ~~**Paginação** `.../rated/N/by/activity/page/2/`: confirmar que funciona e não repete conteúdo.~~ **Resolvido:** funciona, não repete (dedup por viewing id), página além da última = 200 com lista vazia.
2. ~~**Página de busca** de slug: estrutura não verificada.~~ **Resolvido:** endpoint real é `/s/search/films/<query>/` (AJAX), não a URL humana (shell React vazio).
3. ~~**Endpoint de texto completo** (`/s/full-text/viewing:<id>/`): validar formato da resposta, e validar o **detector de truncamento** com casos positivos e negativos conhecidos (crítico — ver C'.1).~~ **Resolvido:** endpoint validado; detector corrigido para `.collapsed-text` (não `data-full-text-url`, que não discrimina) — 2 positivos + 2 negativos, zero erros.

---

## Changelog
- **v1.3.0** (2026-07-20): ficha técnica via TMDB (§3a/[F], NOVO) + narrativa do narrador reestruturada em TRÊS MOVIMENTOS (§D2 reescrito).
  - **(a) Ficha do filme — TMDB** (`ficha.py`, NOVO módulo): dado título/ano do filme (derivados do slug por default, `titulo_ano_de_slug`; override via `--titulo`/`--ano`), busca `/search/movie` (com desambiguação por ano — necessária para títulos comuns como "The Invite", que têm múltiplas entradas no TMDB) e depois `/movie/{id}?language=pt-BR&append_to_response=credits`. Extrai título pt-BR, sinopse oficial, gêneros, duração, diretor e ano. Cache em disco no mesmo padrão do cache do Letterboxd (`<cache-dir>/_tmdb/`), chave por título normalizado + ano, nunca rebusca filme já buscado (inclusive "não encontrado"). **Aditiva por design:** qualquer falha (chave ausente, rede, HTTP, sem resultado) retorna `(None, aviso)` — NUNCA levanta; o pipeline (coleta, síntese, narrador, render) segue normalmente com `ficha: null` no JSON, e o CLI só imprime o aviso em stderr. Campo global `ficha` no output (§4). Fallback de sinopse: overview pt-BR vazio → busca `en-US`, sinalizado com `sinopse_fallback_en: true` (nunca some silenciosamente, nunca finge ser pt-BR).
  - **(b) Emenda de anti-spoiler — sinopse oficial como fonte do Movimento 1** (§3[D], "Anti-spoiler: escopo da proteção e risco aceito"): a regra de "zero conteúdo de trama" ganha uma exceção estreita — a sinopse OFICIAL do TMDB (material de divulgação curado, categoria equivalente ao texto de pôster/contracapa) pode ser usada, condensada, como fonte do novo Movimento 1 da narrativa. Sinopses de terceiros e qualquer expansão com conhecimento externo do modelo continuam PROIBIDAS. O prompt instrui o narrador a usar só a parte de premissa da sinopse caso ela pareça revelar algo além disso — julgamento do LLM, não checagem mecânica (mesmo espírito de risco aceito da v1.1.3).
  - **(c) Narrador em três movimentos** (§D2, `NARRATOR_SYSTEM_PROMPT`/`_serialize_output_for_narrator` em `synthesize.py`): a prosa única da v1.2.x vira MOVIMENTO 1 — O FILME (premissa da ficha, condicional à existência de ficha; sem ficha, pula direto pro Movimento 2), MOVIMENTO 2 — A EXPERIÊNCIA (consensos factuais entre grupos, tom neutro sem valência, avaliação fica pro Movimento 3), MOVIMENTO 3 — O CONTRASTE (perspectivas dos 3 grupos, enxuto — prioriza os 2-3 temas mais fortes de cada grupo em vez de cobrir todos os 6 possíveis, já que a interface exibe as barras tema a tema). Nenhum subtítulo aparece no texto final. Todas as invariantes de v1.2.0–v1.2.3 permanecem em vigor (tamanho de grupo/anti-prevalência, quantificador pré-computado, escopo por grupo, anti-spoiler, forma) — a reestruturação organiza a prosa em torno delas, não as substitui. Alvo de tamanho ajustado de 200–350 para **250–400 palavras** (o Movimento 1 adiciona conteúdo quando há ficha).
  - **(d) Validações pós-parsing inalteradas:** aspas/idioma/escopo/prevalência/quantificador continuam operando sobre o texto final completo, independente de quantos movimentos o compõem — nenhuma mudança de mecânica, só de conteúdo do prompt.
  - **(e) Render/CLI:** novo campo `ficha` no JSON (`null` quando ausente); resumo de uma linha da ficha no render de terminal (título/ano/diretor/gênero/duração) quando presente, sem interferir nos avisos e metadados existentes; flags `--titulo`, `--ano`, `--no-ficha` no CLI.
- **v1.2.3** (2026-07-19): quantificadores pré-computados pelo CÓDIGO — o LLM deixa de escolher (§D2, regra "d. PROPORÇÕES").
  - **A reincidência:** a calibração por instrução (v1.2.2 — o LLM calculava a fração e escolhia o rótulo por uma tabela dada no prompt) reduziu mas não eliminou o modo de falha. Na primeira regeneração das 3 narrativas pós-fix v1.2.2, "quase todos"/"praticamente todos" foi aplicado a frações de 65–70% **2 vezes** — exatamente a condição de escalada que o próprio changelog da v1.2.2 previu ("um checador numérico pós-parsing é candidato futuro caso a inflação reincida").
  - **O princípio da correção:** mesmo da v1.1.1 (denominador de `n_reviews_analisadas`) — o LLM não decide número nem rótulo numérico; **o código é a autoridade**.
  - **(a) Pré-computação** (`synthesize.py`): `_serialize_output_for_narrator` agora injeta, por tema, `fracao` (percentual arredondado) e `rótulo_quantificador` — resolvidos por `_fracao_e_rotulo`/`_rotulo_quantificador`, mapa determinístico com as MESMAS faixas da v1.2.2. Sobreposições nas fronteiras (40–50%, 50–60%, e os pontos exatos 25/50/80%) resolvidas SEMPRE para o rótulo mais fraco, por construção do algoritmo (itera do mais fraco pro mais forte, retorna o primeiro match) — documentado por extenso no código-fonte. O prompt (d) mudou de "calcule e escolha pela tabela" para "use o `rótulo_quantificador` fornecido; PROIBIDO um mais forte; mais fraco é permitido".
  - **(b) Rede de segurança complementar** (validação pós-parsing, nível de bucket, não por tema): se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço (`_REFORCO_QUANTIFICADOR`); se persistir, `quantificador_suspeito: true` em `narrativa_flags`. Deliberadamente restrita a esse quantificador — é o único modo de falha observado; não cobre uso indevido dos demais rótulos (limitação documentada).
  - **Resultado esperado:** zero violações na regeneração das 3 narrativas — qualquer quantificador fora da faixa pré-computada agora é bug de implementação, não variância do modelo (ver `ACEITE_FINAL.md`/relatório da sessão para a conferência).
- **v1.2.2** (2026-07-19): calibração numérica dos quantificadores da narrativa (§D2, regra "d. PROPORÇÕES").
  - **O defeito:** na narrativa do filme *Cure*, o narrador escreveu "quase todos os elogios neste grupo destacam a atmosfera" para um tema de ~15 de 30 (50%) — inflação retórica. Nos outros dois filmes testados os quantificadores saíram honestos; defeito de **variância**, não sistemático, mas incompatível com a promessa central de frequência honesta do produto.
  - **A correção:** mapa explícito quantificador → faixa percentual, calculado sobre `mencoes_aproximadas / n_reviews_analisadas` do grupo: "quase todos"/"praticamente todos" só ≥80%; "a maioria"/"mais da metade" 50–80%; "cerca de metade" 40–60%; "muitos"/"boa parte" 25–50%; "alguns"/"uma parte" 10–25%; "poucos" <10%. Em caso de fronteira ambígua entre duas faixas, instrução explícita de usar sempre a mais **fraca** — subestimar é aceitável, inflar não é.
  - **Verificação:** permanece **humana** (leitura adversarial, quantificador contra número real) nesta versão — sem validador pós-parsing automático. Candidato futuro se a inflação reincidir (ver "Candidatos à próxima versão").
- **v1.2.1** (2026-07-19): corrige uma classe de infidelidade do modo narrativo — **cota de amostragem apresentada como distribuição da recepção**.
  - **O defeito:** os buckets têm tamanhos fixados pela cota de coleta (50/20/30 = 10 válidas × nº de níveis do bucket), que **não** refletem a distribuição real da recepção. A narrativa da v1.2.0 tirava inferências de prevalência das cotas — "grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada". As medianas serão "minoria" em todo filme, para sempre, por construção (2 níveis vs 5/3) — logo qualquer afirmação de prevalência entre grupos é infiel.
  - **(a) Invariante nova no prompt §D2** (regra "c. TAMANHO DOS GRUPOS — REGRA CRÍTICA"): os tamanhos vêm do método de coleta, não da recepção; PROIBIDO comparar tamanhos entre grupos ou inferir prevalência global (maioria/minoria/grupo maior ou menor/igualmente expressivo/polarizada/dividida/consenso). Proporções só DENTRO de um grupo, sempre ancoradas ("mais da metade das reviews negativas analisadas"). Grupos apresentados como PERSPECTIVAS ("entre quem não gostou...", "já entre quem amou..."), nunca como fatias quantificadas do público. A antiga regra de proporções (que dava "uma minoria mediana" como exemplo) foi reescrita.
  - **(b) Telemetria** (validação pós-parsing da narrativa): checagem de marcadores de prevalência entre grupos, mesma mecânica das demais (1 retentativa combinada; flag `prevalencia_suspeita: true` em `narrativa_flags` se persistir; visível no render). Heurística acento-sensível como as outras — rede de segurança; a defesa principal é a invariante (a) do prompt.
- **v1.2.0** (2026-07-19): etapa **[D2] narrador** + flag `--tom` (mecanismo de desenvolvimento para A/B de saída).
  - **(a) Narrador pós-síntese** (§D2): `narrate_output(output)` faz UMA chamada LLM para o filme inteiro e reescreve o relatório validado como prosa (200–350 palavras, pt-BR). **Decisão de arquitetura:** o narrador lê **exclusivamente o JSON validado** (temas/números/observacoes dos 3 buckets + total), **nunca as reviews brutas** — garantido por construção (a entrada é o dict de `build_output`, que não serializa texto de review). Justificativa anti-embelezamento/anti-spoiler registrada em §D2. Prompt fixo do narrador documentado na íntegra (invariantes a–g: papel, fidelidade, proporções, estrutura dos 3 grupos, escopo, anti-spoiler em profundidade, forma).
  - **(b) Validações de prosa reaproveitadas** (§D): sobre a narrativa aplicam-se aspas (remoção mecânica → `aspas_removidas`), idioma e escopo (1 retentativa combinada; `idioma_invalido`/`escopo_suspeito`), com as mesmas flags/telemetria da síntese. Saída via JSON `{"narrativa": ...}` reusa os adaptadores em modo JSON e o parsing defensivo do §D.
  - **(c) Flag `--tom {estruturado,narrativo,ambos}`** (default `estruturado` — comportamento histórico intacto): **MECANISMO DE DESENVOLVIMENTO** para o A/B humano entre saída estruturada e narrativa; a v2 consolidará um tom único após avaliação. `narrativo`/`ambos` não escondem metadados nem avisos — modo degradado permanece visível nos dois tons. Campo `narrativa` (+ `narrativa_flags`) no JSON. Atalho `--reuse-synthesis` compara tons sobre a MESMA síntese gastando só a chamada do narrador.
- **v1.1.4** (2026-07-19): fechamento da v1 — resolve os dois gaps do `ACEITE_FINAL.md` por emenda de spec + mudança mínima de render.
  - **(a) §3[C] — texto bruto removido, URL no lugar.** Removida a cláusula "se houver 1–2 reviews, exibir os textos brutos com aviso" de buckets `sem_analise`. **Motivo:** contradizia o princípio do cabeçalho da spec (trade-offs resolvem a favor de evitar spoiler) — texto integral sem a camada anti-spoiler do LLM é o caminho de maior risco de spoiler do produto, e a flag de spoiler do Letterboxd é autodeclarada. **Substituto (código, `render.py`):** bucket `sem_analise` passa a exibir, além da contagem, `→ N review(s) disponíveis em https://letterboxd.com/film/<slug>/reviews/`, no terminal e no JSON (campo global novo `reviews_url`). Resolve o gap 1 do aceite (o render não exibia texto bruto — agora, por decisão de design, não deve mesmo, e aponta para a fonte).
  - **(b) §5.2 — critério reescrito para o comportamento real.** O critério original presumia cascata de relaxamento/modo degradado em `cidade-de-deus`; o aceite mostrou que o filme é **coberto demais por nível** (10 válidas ≥150 chars em cada um dos 10 níveis, `filtro_aplicado=150` em todos, zero relaxação — ver `ACEITE_FINAL.md`). Novo texto: o filtro de comprimento descarta as curtas em volume, os níveis fecham dentro do teto de paginação, e a análise permanece útil e corretamente escopada. A demonstração da **cascata de relaxamento** e do **modo degradado** é atribuída ao **critério 3** (filme minúsculo), onde ocorreu de fato (`filtro_aplicado` 50/0). Previsão empírica da spec corrigida com dado real.
  - **(c) Selo de aceite.** Nova seção "Status de aceite da v1" (fim do documento) com o veredito por critério e a evidência.
- **v1.1.3** (2026-07-19): registro de risco aceito na proteção anti-spoiler (§3 [D], subseção "Anti-spoiler: escopo da proteção e risco aceito"). A zona cinzenta "mecanismo/dispositivo central da trama" é risco aceito e não deve ser endurecida — endurecer degradaria a especificidade dos temas em todos os filmes para evitar um falso negativo raro e tolerável. Decisão do usuário, validada com juiz humano que conhecia o filme (*Cure*, 1997). Nenhuma mudança de código ou de parâmetro — apenas documentação da fronteira de decisão. (Bateria de aceite §5 dos critérios 2 e 3 executada nesta data — ver `ACEITE_FINAL.md`.)
- **v1.1.2** (2026-07-19): reengenharia do prompt §D + validações pós-parsing, motivadas por evidência empírica da comparação de modelos (`resultado/comparacao/COMPARACAO.md`).
  - **(a) Preâmbulo de papel por bucket** (§3 [D]): NOVO texto antes das instruções invariantes, parametrizado por bucket (nome + intervalo de notas) — não por provider/modelo, que continuam recebendo prompt byte-idêntico para o mesmo bucket. **Motivação:** o flash-lite, com o prompt v1.1.1 (sem preâmbulo), gerou `observacao_geral: "a maioria dos críticos considera o filme um fracasso"` a partir do bucket NEGATIVAS — generalizando um recorte filtrado por construção (só notas ≤2.5) para a recepção geral do filme. O preâmbulo explica ao modelo que ele só vê uma faixa de nota, que esse recorte é enviesado por construção, e proíbe explicitamente generalizações como "os críticos"/"a maioria"/"o consenso"/"a recepção do filme" — ataca o erro na raiz do enquadramento, antes de qualquer instrução de formato.
  - **(b) Regras de aspas e idioma como invariantes §D** (item 6 e 7 da lista de instruções fixas, novos): proibido usar aspas de citação em `exemplo_parafraseado` (motivado pelo 2.5-flash ter citado reviews entre aspas, violando a regra de paráfrase); reforço explícito de que TODOS os campos de texto — incluindo nomes de temas — devem estar em pt-BR.
  - **(c) Validações pós-parsing como camada de código** (não fazem parte do prompt): idioma (heurística de stopwords, 1 retentativa, `idioma_invalido` se persistir), aspas (remoção mecânica, sem retentativa, `aspas_removidas` por tema), escopo (marcadores literais de generalização, 1 retentativa, `escopo_suspeito` se persistir). Idioma e escopo compartilham UMA retentativa combinada quando ambos falham na mesma resposta (não duas separadas) — mantém o orçamento de chamadas por bucket previsível (máx. 3 chamadas no pior caso: 1 + retentativa de JSON + retentativa de validação). Todas as flags são telemetria visível (JSON + terminal), não correção silenciosa — a defesa principal contra vazamento de escopo é o preâmbulo (a), estas são rede de segurança.
  - **(d) Default `gemini-2.5-flash` ratificado com evidência** (§3 [D]): a comparação de modelos rodou o MESMO prompt sobre o MESMO corpus em `gemini-2.5-flash-lite` e `gemini-2.5-flash`; o flash-lite cometeu as 3 violações de instrução que motivaram (a) e (b) acima, o 2.5-flash não repetiu nenhuma. O valor do default não mudou (já era `gemini-2.5-flash` desde v1.1.1), mas agora está documentado com a evidência que o justifica, não só como escolha arbitrária.
- **v1.1.1** (2026-07-18): correções e clarificações da Fase 1, sem alterar nenhum parâmetro congelado de §2.
  - **(a) Correções factuais de Fase 1** (§2.1, §3 [A]/[C'], §6): detector de truncamento = **marcador de colapso `.collapsed-text`** (não `data-full-text-url`, que é quase universal e não discrimina); endpoint de busca real = `/s/search/films/<query>/` (AJAX; a URL de página humana é um shell React vazio); dedup/cache de review por **viewing id via `p[data-likeable-identifier]`**; página além da última retorna **200 com lista vazia** (sinal de parada, não erro).
  - **(b) Cache em `resultado/cache/`** (§3 [B]): registrado como **caminho provisório** — consequência da restrição de arquivos da Fase 1, não decisão de design. Ratificado para v1.1.1 (mudar agora é churn sem ganho); candidato a desacoplar para `cache/` ou `.cache/` na v1.2, já que `resultado/` (entrega descartável/versionável) e o cache (estado reconstruível caro) têm ciclos de vida opostos.
  - **(c) Sem backfill de cota na v1.1.1** (§3 [C'].5): se o completamento de uma truncada falhar e ela for descartada, o nível fecha com a cota reduzida (ex. 9/10), sem repor — shortfall fica visível via `n_descartadas_truncamento`, e o piso-de-3 + modo `sem_analise` já cobrem o caso degenerado. Anotada para v1.2 a distinção entre backfill barato (repor da lista de brutas já paginadas, 1 requisição por reposição — candidato) e backfill caro (repaginar o nível — não é candidato).
  - **(d) Detector de spoiler apertado** (§2.1): ancorado na frase-placeholder **exata** do Letterboxd, substituindo o match por substring solta ("may contain spoilers") que tinha falso positivo em prosa legítima. Ressalva explícita mantida: localização da interface do Letterboxd quebraria o detector em silêncio; nenhum teste automatizado cobre esse cenário.
  - **(e) Suposição aberta registrada, não como coberta** (§3 [C'].6): o comportamento do endpoint `/s/full-text/` para review truncada+spoiler é assumido (devolver o placeholder), não verificado ao vivo — só coberto por fixture sintética. Instrução operacional adicionada: confirmar com 1 requisição se o caso aparecer numa coleta futura.
  - **(f) Denominador e clamp como regra de spec** (§3 [D]): corrigido bug onde o código confiava no `n_reviews_analisadas` devolvido pelo LLM (usando a contagem real só como fallback) — invertido: o código é **sempre** a autoridade do denominador, valor do LLM é ignorado. Adicionado clamp do numerador `mencoes_aproximadas` a `[0, n_reviews_analisadas]`, com o valor original preservado em `mencoes_valor_original` e sinalizado em `mencoes_clampadas` quando o clamp atua — visibilidade de alucinação, não correção silenciosa.
  - **(g) Síntese provider-agnóstica** (§3 [D]): interface de cliente injetável formalizada como contrato (`client_call(system, user, model) -> str`). Providers suportados: **Gemini** (default operacional desta versão) e **Anthropic**; seleção via `--provider` ou auto-detecção pela chave de API presente no ambiente (erro claro se ambas ou nenhuma). Instruções fixas do prompt continuam byte-idênticas entre providers.
- **v1.1.0** (2026-07-18): (1) cota de 10 reviews válidas POR NÍVEL de nota substitui alvo de 20 por bucket — buckets resultantes 50/20/30, cascata movida para o nível, coleta intercalada removida por desnecessária; (2) regra "nunca pela metade": texto completo obrigatório para reviews truncadas via `data-full-text-url`, com detector de truncamento como item de teste crítico e descarte registrado em caso de falha — promovido de incógnita (era seção 6.3) para requisito (C').
- **v1.0.0** (2026-07-18): spec inicial, incorporando resultados da Fase 0 (`RESULTADO.md`).

---

## Status de aceite da v1

**v1 fechada sob v1.1.4** (2026-07-19). Vereditos mecânicos verificados pelo pipeline; qualidade dos temas e ausência de spoiler nos exemplos são de juízo **humano** (aplicado onde indicado).

| # | Critério (§5) | Veredito | Evidência |
|---|---|---|---|
| 1 | Filme popular: 10 níveis completos, temas coerentes, zero spoilers | ✅ | `resultado/oppenheimer-2023.json` (10 níveis × 10 válidas, smoke test); `resultado/cure.json` (juiz humano conhecia o filme — ver risco aceito §3[D]) |
| 2 | Fanbase "review curta": filtro descarta curtas em volume, níveis fecham no teto, análise útil e escopada | ✅ | `ACEITE_FINAL.md` §5.2; `resultado/cidade-de-deus.json` (~76 curtas descartadas, 3 buckets `completo`, observações escopadas) |
| 3 | Filme obscuro: modo degradado severo, piso de 3 respeitado, `sem_analise` avisa (contagem + `reviews_url`) e não inventa temas; cascata de relaxamento exercitada | ✅ | `ACEITE_FINAL.md` §5.3; `resultado/como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual.json` (3 buckets `sem_analise` 1/2/2, `filtro_aplicado` 0/50/150, 0 chamadas Gemini) |
| 4 | Nenhum texto truncado chega ao LLM | ✅ | Smoke `oppenheimer` (100 reviews ao LLM, 0 parcial, 59 truncadas completadas); `cure.json`/`cidade-de-deus.json` (`n_descartadas_truncamento=0`) |
| 5 | Segunda execução: zero requisições de rede (100% cache) | ✅ | Verificado em execução `--offline` do `oppenheimer` (0 rede, 78 cache hits); `tests/test_cache.py` |

§5.6 (orçamento de requisições por filme novo) respeitado em todas as execuções: `cure` 83, `cidade-de-deus` 68, minúsculo 15 — todas dentro do teto.

Evidência transversal de qualidade de instrução: `resultado/comparacao/COMPARACAO.md` (comparação de modelos que motivou o preâmbulo de papel e o default `gemini-2.5-flash` da v1.1.2).

**Pendência de verificação contínua (NÃO bloqueante):** *ground truth* manual das contagens de menções (`mencoes_aproximadas`) — na fila do usuário. As frequências são estimativas do LLM, clampadas a `[0, n_reviews_analisadas]` pelo código (v1.1.1); a aferição da sua acurácia contra contagem manual real é acompanhamento pós-v1, não requisito de fechamento.

---

## Candidatos à próxima versão (pós-v1.2)

- **Histograma de distribuição real de notas (torna prevalência legítima em vez de proibida).** A v1.2.1 **proíbe** afirmações de prevalência entre grupos porque as cotas de coleta (50/20/30) não são a distribuição da recepção. A correção de raiz — em vez da proibição — é **coletar o histograma de notas da página do filme no Letterboxd** (a barra de distribuição de ratings; **1 requisição extra** por filme, cacheável). Com a distribuição real disponível, o narrador **e** o render estruturado poderiam fazer afirmações de prevalência **legítimas e ancoradas nos dados** ("a maior parte das avaliações fica na faixa alta"), e o `--tom` narrativo deixaria de ter uma invariante puramente restritiva. Enquanto o histograma não existe no pipeline, a proibição da v1.2.1 é o comportamento correto. *(Também destrava a distinção "bucket vazio porque ninguém odiou" vs "porque ninguém assistiu" com número real, não só o total observado do rodapé.)*
- **Validador pós-parsing por tema (não só o quantificador mais forte).** A v1.2.3 pré-computa o rótulo (código como autoridade) e adiciona uma rede de segurança em nível de BUCKET restrita a "quase todos"/"praticamente todos" — deliberadamente não cobre uso indevido dos demais rótulos (ex.: "poucos" aplicado a um tema de 40%). Candidato futuro: correspondência por `tema` no texto da narrativa, recalcular a fração daquele tema específico e conferir contra QUALQUER rótulo usado, não só o mais forte — mesma mecânica de retentativa + flag das demais validações de prosa. Só vale a pena se o padrão de uso indevido de rótulos mais fracos aparecer na prática; nenhuma evidência disso até a v1.2.3.
- **Cache em `cache/`/`.cache/` na raiz** (desacoplar de `resultado/`, ver §3[B]) e **backfill barato de cota** (§3[C'].5) — candidatos herdados da v1.1.x.