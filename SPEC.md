# Espectro 24 — Especificação v1.7.2

**Data:** 2026-07-26
**Status:** v1 fechada (aceite em "Status de aceite da v1", fim do documento). v1.2.0 adiciona a etapa **[D2] narrador** (§D2) e a flag `--tom` como **mecanismo de desenvolvimento** para A/B de saída. v1.2.1 corrige uma classe de infidelidade do narrador (cota de amostragem apresentada como distribuição da recepção) — invariante nova no §D2 + telemetria. v1.2.2 adiciona calibração numérica dos quantificadores da narrativa (mapa fração→palavra, faixa mais fraca em caso de dúvida) — verificação por instrução ao LLM. v1.2.3 move a calibração do prompt para o CÓDIGO: os rótulos de quantificador passam a ser pré-computados e o LLM só os usa, não os escolhe (mesmo princípio da v1.1.1 — código como autoridade de número/rótulo). v1.3.0 adiciona uma **ficha técnica do filme via TMDB** (§3a, aditiva — nunca bloqueia o pipeline) e reestrutura §D2 para uma narrativa em **três movimentos** (filme → experiência consensual → contraste entre grupos), com uma emenda pontual à regra de "zero conteúdo de trama" para permitir a sinopse OFICIAL curta como fonte do primeiro movimento (ver §3[D] "Anti-spoiler"). **v1.3.1** corrige um defeito real observado na primeira execução do MOVIMENTO 2 (a narrativa de `the-invite-2026` importou um juízo de QUALIDADE — "atuações marcantes"/"roteiro inteligente" — como se fosse um consenso DESCRITIVO, contradizendo diretamente os temas do grupo negativas): a regra do MOVIMENTO 2 ganha três critérios explícitos (categoria/presença/não-contradição) e telemetria de `consensos_usados` para revisão humana de cada execução (ver §D2). **v1.4.0** é a maior mudança desde a v1: o pipeline passa a coletar a **distribuição real de notas** (histograma público do Letterboxd, §3b) e, com ela, **inverte** a regra de prevalência do §D2 — o que a v1.2.1 proibiu por falta do dado, a v1.4.0 torna obrigatório e ancorado (ver "Princípio norteador" abaixo). **v1.4.1** corrige três defeitos pontuais observados na entrega da v1.4.0, todos no §D2: (1) telemetria de quantificadores **por par declarado** (`quantificadores_usados`), depois da 3ª reincidência do mesmo modo de falha, que a rede de nível de bucket não pega; (2) **omissão autorizada** do MOVIMENTO 2, contra a pressão de preenchimento que produz juízo de qualidade hedgeado; (3) **invariante de vocabulário do peso** — rótulos de peso dizem "das notas", nunca "das reviews"/"do público"/"dos espectadores". **v1.5.0** ataca um defeito de **fluência**, não de honestidade: as narrativas entregues até a v1.4.1 são factualmente corretas, mas soam mecânicas — forma sintática repetida (rótulo de peso + verbo de reporte + complemento, três vezes seguidas), frases quase todas do mesmo comprimento, excesso de verbos de reporte e nominalizações no lugar de verbos. O diagnóstico (registrado no changelog) é que o acúmulo de invariantes de honestidade das versões anteriores empurrou o modelo à única forma que satisfaz todas simultaneamente. A correção prescreve **ritmo** e **registro** com a mesma precisão de código com que já se prescrevem números, adiciona uma **marcação de perspectiva** pré-computada (para que a redução de verbos de reporte não deixe a fala de um grupo minoritário soar como fato do narrador) e duas telemetrias novas (`marcadores_perspectiva`, `metricas_fluencia`) — **sem afrouxar nenhuma invariante de honestidade** das versões anteriores. **v1.6.0** conclui que a v1.5.0 errou no MÉTODO, não no objetivo: empilhar honestidade e fluência num prompt só não funcionou (as regras de ritmo não transferiram entre filmes, as métricas que as fiscalizavam não acompanhavam qualidade, e a configuração de produção chegou a publicar uma frase agramatical). A correção é **separar responsabilidades**: o narrador (§D2) é podado de volta a UMA responsabilidade — dizer a verdade com a estrutura certa — e um estágio novo, o **editor [E2]** (§E2), assume ritmo e leitura sem ter acesso a nenhuma fonte de fato e sem poder alterar número, rótulo ou atribuição (trechos protegidos + verificação mecânica + descarte da edição em caso de violação). **v1.6.1** corrige o defeito 5.2 que a v1.6.0 deixou em aberto: em vez de normalizar a COMPARAÇÃO entre o trecho declarado e o texto (caixa/acento/demonstrativo), passa a verificar a EXISTÊNCIA de uma expressão de atribuição reconhecida no texto realmente escrito — o que fecha também o caso de reordenação de palavras que a normalização não alcançava, e reduz `marcadores_perspectiva` a telemetria pura (auditoria humana, não fonte de validação). **v1.6.2** corrige um bug de substring solta descoberto ao vivo na regeneração de `cidade-de-deus` (shares 1%/8%/91%): `_ancora_de_grupo` e `_ancoragem_de_peso_ok` buscavam o percentual de um grupo com `f"{pct}%" in texto`/`texto.find(...)`, que casa **dentro** de outro número — `"1%"` combinava com o "1" final de `"(~91%)"`, ancorando o grupo `negativas` (1%) numa posição muito anterior à sua menção real, corrompendo o cálculo do span de movimento e produzindo falso positivo em `perspectiva_nao_marcada` mesmo com o texto correto e bem marcado. A busca agora usa `re.search(rf"(?<!\d){pct}%", texto)` (nega dígito imediatamente anterior), então `"1%"` só casa como número isolado, nunca como sufixo de `"91%"`/`"21%"`/etc. Mesmo defeito corrigido nos dois pontos que faziam a busca (âncora de grupo e checagem de ancoragem de peso), com testes de regressão cobrindo o caso real. Nenhuma invariante de honestidade foi afrouxada — o fix é estritamente sobre a CHECAGEM, não sobre o que é permitido no texto. **v1.7.0** corrige dois defeitos reais observados na regeneração das narrativas: (1) **resolução de ficha do filme errado** — `espectro24 --slug cure` sem `--ano` resolvia no TMDB para "The Cure" (2026, dir. Nancy Leopardi) em vez de Cure (1997, Kiyoshi Kurosawa), porque a desambiguação por popularidade sem ano escolhe o candidato errado quando o título é comum; a resolução de ano ganha uma cadeia de fallback confiável (slug → página do Letterboxd → sem ficha) e uma guarda de sanidade que descarta a ficha inteira se o ano devolvido pelo TMDB divergir do esperado em mais de 1 ano (ver §3[A]); (2) **lista de protegidos do editor §E2 enxugada** — protegia até 16 trechos por filme, incluindo quantificadores soltos ("muitos") e expressões de atribuição, o que descartava o editor com frequência (`cure`) ou o levava a inventar frases só para reencaixar um protegido movido ("Essa é a opinião de uma fração mínima das notas.", `cidade-de-deus`), e ainda deixava sobreviver um defeito gramatical real ("destacando a a maioria o estilo visual") porque a frase continha um rótulo protegido; a proteção literal agora cobre só rótulo de peso COM percentual e tokens numéricos — quantificador e atribuição passam a valer SÓ pela checagem semântica que já existia e era mais forte (`conferencia_quantificador` v1.4.1, `_marcadores_validos` v1.6.1), revalidada dentro do próprio `editar_narrativa` (ver §E2). **v1.7.1** corrige três defeitos de acabamento observados no texto PUBLICADO da v1.7.0, nenhum deles de honestidade: (1) **contrabarra residual** — `_remover_aspas` trocava só o caractere de aspas por "", então uma citação escapada (`\"A Cura\"`) virava `\A Cura\` (publicado em `cure` e `the-invite-2026`); a remoção agora consome a contrabarra que precede a aspas junto, como uma unidade. (2) **capitalização de rótulo protegido movido** — o rótulo de peso guarda a caixa de onde apareceu a primeira vez (início de frase, capitalizado); quando o editor o move para o meio de um período, a checagem 100% literal não deixava ajustar só a inicial, e o defeito ("Para A grande maioria...", `cidade-de-deus`) sobrevivia porque corrigir quebraria o protegido; a checagem de trecho perdido agora aceita a primeira letra em qualquer caixa — e SÓ ela, nenhuma outra letra, palavra ou número do trecho. (3) **família "quem gostou/não gostou" ausente do vocabulário de atribuição** — o `cure` escreveu "quem não gostou considerou o ritmo lento e tedioso" para o grupo de 3%, uma atribuição real, mas fora da lista de expressões reconhecidas (`_EXPRESSOES_DE_PERSPECTIVA`), produzindo falso positivo em `perspectiva_nao_marcada`; a família foi acrescentada ("quem gostou", "quem não gostou", "quem amou", "quem ficou no meio", e as formas com "para" na frente), mantendo de fora o "para quem" ISOLADO (pronome relativo comum, motivo do falso negativo original da v1.6.0). Nenhuma invariante de honestidade foi afrouxada nas três correções — são fixes de CHECAGEM e de limpeza mecânica, não mudança do que é permitido no texto. **v1.7.2** corrige um defeito real observado na regeneração do `cidade-de-deus` sob a v1.7.1: o editor devolveu a prosa embrulhada num invólucro `{ text: "..." }`, ignorando a instrução de responder só texto puro — e TODAS as checagens mecânicas de então (protegidos, conjunto numérico, honestidade) passaram, porque rodam sobre SUBSTRING e o protegido/os números continuavam achados DENTRO do invólucro. A edição foi marcada "aplicada"; só a leitura humana antes de publicar pegou o defeito. A correção acrescenta uma **checagem ESTRUTURAL** (`_formato_invalido`, §E2), aplicada ANTES de todas as outras: rejeita o texto se ele começar com `{`/`[`, contiver cerca de código (```), tiver uma das primeiras linhas com cara de campo JSON (`"text":`, `text:`, `"narrativa":`), ou tiver chaves desbalanceadas — mesma política das demais checagens (1 retentativa com reforço explicando o formato exigido; se persistir, descarta com `motivo_descarte: "formato_invalido"` e publica a bruta). Deliberadamente NÃO rejeita uma chave/colchete equilibrado no MEIO da prosa — só o formato de invólucro, não qualquer ocorrência do caractere.

---

## 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO

> Os três grupos recebem **formato idêntico**: mesma profundidade de análise
> (cota 50/20/30), mesma estrutura de temas, mesmo estilo tipográfico, mesmo
> espaço estrutural na interface. **A assimetria vem dos dados, não da
> apresentação.**

**O problema que motivou a versão** (feedback recorrente de usuários reais):
filmes amplamente aclamados *soam divididos* no produto, porque os três grupos
recebem o mesmo peso textual e visual. Um filme com 91% das notas na faixa alta
era apresentado com a mesma proeminência dada ao grupo de 1% — o leitor saía
com a impressão de controvérsia onde havia consenso. Isso é uma **infidelidade
por omissão**: cada frase era verdadeira, mas o conjunto comunicava algo falso.

A v1.2.1 já havia diagnosticado a raiz (as cotas de coleta não são a
distribuição da recepção) e escolhido a única saída disponível na época:
**proibir** qualquer afirmação de prevalência. O changelog daquela versão e a
seção "Candidatos à próxima versão" registraram explicitamente que a correção
de raiz seria coletar o histograma. É o que esta versão faz — e por isso a
regra inverte em vez de ser "afrouxada": não é uma concessão, é o dado que
faltava chegando.

**Duas invariantes que a inversão NÃO toca:**

1. **`share` por faixa NÃO é nota média.** São três números que particionam a
   população de notas, cada um atribuído à sua faixa. A proibição de score
   agregado, nota média ou "X de 10" (§1) permanece **intacta** e está escrita
   dentro da própria regra invertida do prompt. Em nenhum lugar do produto
   existe um número-síntese único do filme.
2. **A perspectiva minoritária continua analisada com o mesmo rigor.** Menos
   espaço na prosa, **mesma seriedade**: sem desdém, sem ironia, sem sugerir
   que quem pensa assim está errado. Quem procura saber se vai gostar precisa
   entender o que incomodou aquela parcela — e um grupo de 1% mantém seus 6
   temas, suas barras e suas paráfrases na interface.

---
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
| **Config LLM da PROSA (v1.6.0)** — narrador §D2 + editor §E2 | `thinking_budget=4096` (FIXO) · `max_output_tokens=16000` |
| **Config LLM da SÍNTESE (§D)** — inalterada | `thinking_budget=0` · `max_output_tokens=3000` |

---

## 3. Pipeline

```
input (nome do filme)
  → [A] resolução de slug
  → [B] coleta por nível de nota (com cache)
  → [C] filtros e cascata de relaxamento (por nível)
  → [C'] completamento de reviews truncadas
  → [G] distribuição real de notas — histograma (aditiva — v1.4.0)
  → [D] síntese LLM por bucket
  → [D2] narrador (opcional, --tom; lê [G] se existir)
  → [E2] editor — passe de fluência sobre a narrativa (v1.6.0; --no-edicao pula)
  → [F] ficha do filme via TMDB (aditiva, independente de D/D2 — v1.3.0)
  → [E] render (JSON + terminal)
```

**[F] e [G] rodam em paralelo conceitual a [D]/[D2]:** não dependem das
reviews coletadas nem são bloqueadas por elas ([F] usa título/ano derivados
do slug — §3[F]; [G] usa só o slug — §3[G]). Uma falha em [F] ou [G] nunca
impede [D]/[D2]/[E] de rodar, e vice-versa: as fontes de dados são
independentes.

**[G] é a única exceção à independência total:** o narrador [D2] *lê* a
distribuição quando ela existe, para escolher a variante da regra (c). Mas a
dependência é **opcional por construção** — ausência de [G] não é erro, é o
caminho de fallback (regras da v1.2.1), e nenhum outro estágio muda.

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
b. **Aspas:** se qualquer `exemplo_parafraseado` contiver aspas de citação (`" ' “ ” ‘ ’ « » ‹ ›`), remove-as **mecanicamente** (não é reescrita — apenas apaga os caracteres e normaliza espaços) e registra `aspas_removidas: true` **no tema**. **Sem retentativa** — correção mecânica basta, não vale gastar uma chamada de LLM. **v1.7.1 — bugfix:** quando a aspas vinha ESCAPADA no texto (`\"A Cura\"`), a remoção trocava só o caractere de aspas, deixando a contrabarra órfã (`\A Cura\`) — publicado ao vivo em `cure` e `the-invite-2026`. A remoção agora consome a contrabarra que precede a aspas junto, como uma unidade (`_remover_aspas`, `synthesize.py`).
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

### [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)

Etapa **PÓS-síntese**, opcional, controlada pela flag `--tom` (ver abaixo). Uma **única chamada LLM para o filme inteiro** (não por bucket), mesmo provider/modelo da síntese.

**Decisão de arquitetura (invariante, inalterada desde v1.2.0):** o narrador recebe **EXCLUSIVAMENTE o JSON validado** — os temas, `mencoes_aproximadas`, `n_reviews_analisadas` e `observacao_geral` dos 3 buckets, o total de reviews, e (v1.3.0) a **ficha técnica** do filme quando existir (§3a). **NUNCA as reviews brutas.** Ele reescreve informação **já validada** como prosa; não tem acesso a nada que as validações (§D) não tenham aprovado, nem a nada que não venha da ficha oficial do TMDB. Isso é garantido **por construção**: a entrada do narrador é o dict de saída de `build_output` (que não serializa texto de review) mais o campo `ficha` (que vem só do TMDB, nunca de reviews).

Por que essa fronteira (justificativa anti-embelezamento / anti-spoiler): dar reviews brutas ao narrador reabriria os dois riscos que o pipeline inteiro existe para conter — (1) **spoiler**, pois texto integral não passou pela camada anti-spoiler do LLM; e (2) **embelezamento/infidelidade**, pois o narrador poderia "florear" com material não contabilizado, quebrando a fidelidade às frequências. Lendo só o relatório validado (+ ficha oficial), o narrador não pode afirmar nada que a camada de baixo não tenha aprovado.

**v1.3.0 — narrativa em três movimentos:** a v1.2.x produzia um único bloco de prosa livre. A v1.3.0 estrutura esse bloco em três movimentos sequenciais, sem subtítulos visíveis no texto final (a divisão organiza o LLM, não aparece como marcação para o leitor) — motivada pela interface em vídeo que consome a narrativa em três passos de review: apresentar o filme, descrever a experiência de assisti-lo, e só então contrastar as reações.

1. **MOVIMENTO 1 — O FILME** (2-3 frases; só existe se houver `ficha` no relatório — sem ficha, a narrativa começa direto no Movimento 2): premissa a partir da `sinopse_oficial` do TMDB (pode condensar, PROIBIDO expandir com conhecimento externo — ver emenda de anti-spoiler em §3[D]), diretor, gênero, ano; duração só se for relevante ao que os movimentos 2/3 dizem.
2. **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): como é assistir ao filme, usando **apenas** propriedades DESCRITIVAS (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade) em que os grupos concordam no **núcleo factual**, mesmo divergindo na avaliação. Tom neutro, sem valência — descreve, não julga; a avaliação fica para o Movimento 3. **v1.3.1 — três critérios obrigatórios** para uma propriedade entrar aqui: **(a) categoria** — só descritiva, PROIBIDO juízo de qualidade (atuação/roteiro/direção boa-ou-ruim, isso é sempre disputa e pertence ao Movimento 3); **(b) presença** — vem de temas de pelo menos DOIS grupos com o mesmo núcleo factual, mesmo com valência diferente ("lento e tedioso" + "lento e deliberado" → núcleo "ritmo lento"); **(c) não-contradição** — se QUALQUER grupo nega o núcleo factual (não só diverge na avaliação), a propriedade é desqualificada. Cada propriedade usada é registrada em `consensos_usados` (telemetria — ver abaixo).
   **v1.4.1 — OMISSÃO AUTORIZADA:** se **menos de duas** propriedades passarem nos três critérios, o MOVIMENTO 2 deve ser **CURTO (1 frase) ou AUSENTE**, e a narrativa passa direto ao MOVIMENTO 3. **Omitir é o comportamento CORRETO, não uma falha** — não há cota de frases a cumprir, e um filme com poucos temas descritivos simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de qualidade suavizado ("estilo visual eficaz", "abordagem arrojada") é **pior** do que não ter o movimento: é a violação do critério (a) disfarçada de descrição por um advérbio de hesitação. Quando omitido, `consensos_usados` vem como **lista vazia** — resultado esperado, e a validação de `_consensos_validos` **não** trata lista vazia como suspeita (válida por vacuidade, regra já vigente desde a v1.3.1).
3. **MOVIMENTO 3 — O CONTRASTE** (enxuto — ~40% menor que a narrativa única da v1.2.x): as perspectivas dos três grupos, priorizando os 2-3 temas **mais fortes** de cada grupo em vez de cobrir todos os até 6 possíveis — decisão motivada pela interface, que já exibe as barras de frequência tema a tema (a narrativa não precisa duplicar essa cobertura completa). Mantém **todas** as invariantes vigentes desde v1.2.x (rótulos de quantificador pré-computados, escopo por grupo, proibição de prevalência entre grupos, sem aspas, anti-spoiler, pt-BR).

Alvo de tamanho total: **250-400 palavras** (ajustado de 200-350 na v1.2.x — o movimento 1 adiciona conteúdo quando há ficha).

#### Diagnóstico de fluência (v1.5.0) — por que as narrativas soavam mecânicas

Leitura adversarial das narrativas entregues até a v1.4.1 (o texto de `the-invite-2026`, ver `resultado/the-invite-2026.json` campo `narrativa`, é o caso citado) revelou um padrão sistemático, não um defeito isolado:

- **Forma sintática repetida:** cada perspectiva era apresentada com a MESMA estrutura — rótulo de peso, seguido de verbo de reporte ("elogia", "reconhece", "classifica"), seguido de complemento — três vezes seguidas, uma por grupo.
- **Comprimento de frase quase constante:** a maioria das frases caía na faixa de 25-35 palavras, sem variação perceptível.
- **Densidade alta de verbos de reporte e nominalizações** no lugar de verbos diretos ("a repetição das situações torna a experiência cansativa" em vez de "as situações se repetem e o filme cansa").

**Causa provável:** o acúmulo de invariantes de honestidade das versões anteriores (peso ancorado com percentual, quantificador pré-computado, escopo por grupo, anti-spoiler, sem aspas, vocabulário "das notas") — cada uma necessária e nenhuma removida nesta versão — levou o modelo à ÚNICA forma sintática que satisfaz todas simultaneamente ao mesmo tempo: relatar, com um verbo, o que cada grupo (identificado pelo rótulo de peso) diz. É previsível: sob restrição suficiente, convergir para uma forma única é o caminho de menor risco para o modelo não violar nenhuma regra. A correção desta versão não afrouxa nenhuma invariante — prescreve **ritmo** e **registro** com a mesma precisão de código com que os números já são prescritos, para que a honestidade não dependa de sacrificar a fluência.

#### RITMO E REGISTRO — MIGRADOS PARA O EDITOR §E2 (v1.6.0)

As regras de ritmo e registro introduzidas na v1.5.0 (variação de comprimento e de abertura, conectivos de fala, limite de verbos de reporte, proibição de advérbios em -mente, tom de "contar para um amigo") **saíram do prompt do narrador** e passaram a viver no **editor (§E2)**. O par few-shot ANTES/DEPOIS foi movido junto — não duplicado.

**Por que a v1.5.0 falhou** (evidência em `DIAGNOSTICO_FLUENCIA.md` e `DIAGNOSTICO_FLUENCIA_V2.md`):
- **as regras não transferiram.** O `the-invite` pareceu obedecer, mas estava **copiando o few-shot** — 58 8-gramas compartilhados, porque o exemplo fora escrito com os dados daquele mesmo filme. `cure` e `cidade-de-deus`, sem nada a copiar, não transferiram estilo nenhum e pioraram em pontos;
- **a fiscalização era cega.** As métricas que disparavam retentativa não acompanham qualidade: no `cure`, o texto qualitativamente melhor pontuou PIOR em `cv_comprimento` (0.35 → 0.28) e em `verbos_reporte` (3 → 6);
- **o custo apareceu na saída publicada.** A configuração de produção (`thinking_budget=0`) gerou uma frase agramatical que foi ao ar.

**O diagnóstico de fundo permanece válido** (ver seção anterior): sob restrição suficiente, o modelo converge para a única forma que satisfaz todas as regras. O erro foi tentar resolver isso **empilhando mais regras no mesmo prompt** — o que aumenta a restrição em vez de aliviá-la. A v1.6.0 tira a carga de estilo do narrador e a entrega a um estágio que só tem essa função, e que é estruturalmente incapaz de comprometer a honestidade (§E2).

**O que o narrador ganhou no lugar:** uma nota curta avisando que existe um estágio de edição depois, que ele não precisa se preocupar com ritmo, e que deve escrever de forma clara e **gramaticalmente correta**. Nada além disso.

#### MARCAÇÃO DE PERSPECTIVA (v1.5.0, regra nova — só existe COM distribuição)

**Motivação:** ao remover os verbos de reporte (regra de REGISTRO, item f), a afirmação de um grupo minoritário pode soar como fato do próprio narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante (o grupo de maior peso, apresentado primeiro pela regra de ABERTURA OBRIGATÓRIA). Sem "eles apontam que", a frase "o humor é previsível" lida isolada parece uma afirmação do produto sobre o filme, não a opinião de uma fatia minoritária das notas.

**Pré-computação em código (`_marcacoes_por_bucket`/`_marcacao_perspectiva`, `synthesize.py`), por grupo, a partir dos `share_real`:**
- `dominante` = maior share entre os três grupos do filme;
- `marcacao_perspectiva = "nenhuma"` se `share > dominante/3`;
- `marcacao_perspectiva = "simples"` se `share <= dominante/3`;
- `marcacao_perspectiva = "antecipada"` se `share <= dominante/10`.

A condição mais restritiva (`antecipada`) é checada primeiro — um share que a satisfaz também satisfaz `simples`. **Só existe quando há distribuição real:** o mesmo motivo pelo qual a COTA de coleta (50/20/30) não pode alimentar este cálculo — usar a cota apresentaria amostragem como se fosse prevalência, o defeito que a v1.2.1 proíbe (§D2, regra (c) sem distribuição). Sem `share_real`, não há "dominante" legítimo a calcular. O valor é passado ao narrador na serialização, junto do `rotulo_peso` de cada grupo — o LLM não calcula nem escolhe.

**Limiares são ponto de partida, calibráveis:** ao contrário das faixas de quantificador (v1.2.2/v1.2.3) e de peso (v1.4.0), que vieram de casos reais observados e comparação de modelos, estes limiares (`dominante/3`, `dominante/10`) não têm evidência empírica prévia — são um primeiro corte razoável, sujeito a ajuste em versões futuras conforme a leitura adversarial das narrativas regeneradas.

**Regra no prompt:**
- TODO trecho que fala de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra exigido).
- `marcacao_perspectiva = "simples"`: além da abertura, ao menos UM marcador de perspectiva dentro do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
- `marcacao_perspectiva = "antecipada"`: o marcador interno deve vir ANTES da primeira afirmação substantiva do trecho sobre aquele grupo — não no fim.
- Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
- PROIBIDO marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito, conforme a v1.4.0 (RESPEITO À MINORIA).

**Telemetria (`marcadores_perspectiva`, mesmo padrão de `consensos_usados`/`quantificadores_usados`):** o narrador declara `{grupo, trecho}` para cada marcador usado, com o trecho copiado literalmente da narrativa. **v1.6.1 — esta declaração é auditoria humana, não fonte de validação** (ver abaixo); ela é persistida no JSON e exibida no render exatamente como antes.

**Validação pós-parsing (`_marcadores_validos`, `synthesize.py`) — v1.6.1, reescrita para verificar o TEXTO, não a declaração:**
(a) para todo grupo com `marcacao_perspectiva != "nenhuma"`, o MOVIMENTO daquele grupo (`_span_de_movimento`: do ponto em que ele é ancorado — rótulo de peso ou percentual — até a âncora do próximo grupo, ou o fim do texto) contém **alguma expressão de atribuição reconhecida** (a mesma lista `_EXPRESSOES_DE_PERSPECTIVA` que `montar_protegidos`, §E2, já usa — fonte única, sem duplicação: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa" e variantes); **v1.7.1** ampliou o vocabulário com a família "quem gostou/não gostou/amou/ficou no meio" (e as formas com "para" na frente) — caso real do `cure`, onde "quem não gostou considerou o ritmo lento e tedioso" cumpria a função de atribuição para o grupo de 3%, mas não estava na lista, produzindo falso positivo em `perspectiva_nao_marcada` num texto honesto. O "para quem" ISOLADO continua de fora — é pronome relativo comum e foi o que causou o falso NEGATIVO original da v1.6.0.)
(b) para `marcacao_perspectiva == "antecipada"`, **PELO MENOS UMA** dessas ocorrências precisa cair na MESMA frase em que o grupo é ancorado ou na frase IMEDIATAMENTE seguinte.

**v1.6.0 — dois bugs corrigidos:** "antecipada" passou a exigir **um** marcador bem posicionado, não todos (o narrador legitimamente declara mais de um ao elaborar o grupo — foi o que aconteceu no `the-invite`); e a comparação do trecho declarado ganhou normalização de caixa/acento/demonstrativo.

**v1.6.1 — a normalização não bastou, e a correção foi trocar O QUE se verifica.** O caso concreto do `cidade-de-deus` sobreviveu à v1.6.0: o narrador declarou *"Para esse grupo, muitos reconhecem a qualidade técnica…"* e escreveu *"Muitos neste grupo reconhecem a qualidade técnica…"* — divergência de **ORDEM DAS PALAVRAS** (similaridade 0.92), que nenhuma normalização de caixa/acento fecha. Fechar por comparação difusa com limiar foi **descartado** (de novo): um limiar de similaridade é uma linha arbitrária, e a checagem existe para confirmar que o marcador de perspectiva **EXISTE no texto** — não que a frase declarada é uma transcrição fiel dele.

A correção pela raiz separa as duas coisas que a v1.6.0 ainda misturava:
- `marcadores_perspectiva` é o que o LLM **diz que fez** — telemetria para revisão humana, exatamente como `consensos_usados`;
- a validação escaneia o que o LLM **realmente escreveu**, procurando qualquer expressão de atribuição reconhecida no trecho de texto associado ao grupo — **igual usa `trecho` declarado**.

Consequência: `_normalizar_trecho`/`_trecho_aparece` (v1.6.0) foram **removidas** — não davam conta do problema real, e a nova checagem não compara mais string contra string. `montar_protegidos` (§E2) e `_marcadores_validos` agora leem a **mesma constante** `_EXPRESSOES_DE_PERSPECTIVA`, então um vocabulário novo de atribuição só precisa ser ensinado num lugar.

Falha em qualquer critério → **1 retentativa** com reforço (`_REFORCO_MARCADORES`); se persistir, aceita e sinaliza `perspectiva_nao_marcada: true` em `narrativa_flags`. Lista vazia é válida por vacuidade quando nenhum grupo exige marcação (dominante ≈ os três grupos, ex. 40/30/30 — nenhum passa nos limiares). Persistido no JSON como campo global `marcadores_perspectiva` e exibido no render de terminal como bloco compacto, mesmo padrão de `consensos_usados`.

#### EXEMPLO DE ESTILO — MIGRADO PARA O EDITOR §E2 (v1.6.0)

O par ANTES/DEPOIS foi **movido** para o prompt do editor (§E2), onde o eixo de ritmo agora vive. Ele permanece **descontaminado** — filme fictício, números inventados (74/19/7) —, e um teste (`test_v160_few_shot_do_editor_segue_descontaminado`) impede a reintrodução de nomes ou shares do catálogo.

> **Registro histórico da descontaminação (sessão de diagnóstico, 2026-07-25):** a primeira versão do par usava os **dados reais do `the-invite-2026`** (79/18/3, o nome da diretora, o apartamento único). Medindo sobreposição de 8-gramas com as construções mandatórias mascaradas: `the-invite` **58**, `cure` **0**, `cidade-de-deus` **0**. Ou seja, o filme que parecia ter aprendido o estilo estava **copiando o exemplo**, e os outros dois não transferiram nada. Um few-shot construído sobre um filme do catálogo contamina a avaliação daquele filme e só daquele — e por isso não mede nada. Dois micro-exemplos que também carregavam dados do `the-invite` (a regra (e) de REGISTRO e a ilustração da ANCORAGEM) foram neutralizados junto.

#### Telemetria de fluência (v1.5.0, NOVO) — métricas calculadas em código, não pelo LLM

Mesma filosofia das demais telemetrias do §D2: o código não reescreve a prosa, só mede e sinaliza. Calculadas por `_metricas_fluencia` (`synthesize.py`) sobre o texto final da narrativa e persistidas em `metricas_fluencia`:

| Métrica | Definição |
|---|---|
| `n_frases` | Frases (divisão heurística por `.`/`!`/`?`, sem tratar abreviações) |
| `media_palavras` | Média de palavras por frase |
| `cv_comprimento` | **Desvio padrão ÷ média** de palavras por frase — mede VARIAÇÃO, não o comprimento em si (a regra de ritmo pede variação, não frases curtas o tempo todo) |
| `frase_mais_curta` | Menor contagem de palavras entre as frases |
| `aberturas_repetidas` | Pares de frases CONSECUTIVAS com a mesma primeira palavra (normalizada, minúscula) — proxy barato para "mesma estrutura de abertura" |
| `verbos_reporte` | Ocorrências dos verbos da regra (f) e flexões (`elogi-`, `destac-`, `apont-`, `relat-`, `consider-`, `classific-`, `mencion-`, `ressalt-`, `reconhec-`, `express-`, `descrev-`) |
| `adverbios_mente` | Ocorrências de advérbios intensificadores de uma lista fechada (intensamente, profundamente, extremamente, excessivamente e sinônimos comuns da mesma família) — deliberadamente NÃO cobre todo advérbio em `-mente` (ex. "praticamente" não é intensificador) |

**v1.6.0 — as métricas viram DIAGNÓSTICO PURO.** Os gatilhos automáticos de retentativa (`cv_comprimento < 0.40` · nenhuma frase ≤ 10 palavras · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`), o reforço `_REFORCO_FLUENCIA` e a flag `fluencia_baixa` foram **REMOVIDOS**.

**Motivo — as métricas não acompanham qualidade.** No `cure` (DIAGNOSTICO_FLUENCIA_V2.md, células A vs. B), o texto qualitativamente MELHOR pontuou PIOR nas duas métricas centrais:

| | A (pior texto) | B (melhor texto) |
|---|---|---|
| `cv_comprimento` | 0.35 | **0.28** |
| `verbos_reporte` | 3 | **6** |

`cv_comprimento` mede **dispersão** de comprimento de frase, não legibilidade: um texto com frases uniformemente boas pontua mal, e um texto truncado no meio pontua bem. Otimizar contra a métrica — que é exatamente o que uma retentativa automática faz — empurra o modelo a **degradar** a prosa para satisfazer um número. É o mesmo erro que o projeto já evitou em outros eixos (o código é autoridade sobre NÚMERO e RÓTULO; não é, e não deve ser, autoridade sobre ESTILO).

`_metricas_fluencia` continua sendo calculada e persistida em `metricas_fluencia`, com o mesmo estatuto de `consensos_usados`: **material de revisão humana**, não critério automático. O eixo de fluência passa a ser responsabilidade do editor (§E2), que trabalha por instrução e exemplo, não por limiar.

Persistida no JSON como campo global `metricas_fluencia` e exibida no render de terminal como linha-resumo, após os blocos de consensos/quantificadores/marcadores.

**Prompt fixo do narrador (SPEC — texto oficial, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`):**

> Você recebe um RELATÓRIO DE RECEPÇÃO já validado de um filme: três grupos de reviews separados por faixa de nota (negativas, medianas, positivas), cada um com seus temas, frequências aproximadas e uma observação; e, quando disponível, uma FICHA TÉCNICA do filme (sinopse oficial, diretor, gênero, ano, duração — fonte: TMDB). Sua tarefa é reescrever esse material como um texto corrido e envolvente, em TRÊS MOVIMENTOS, SEM subtítulos ou marcações entre eles (a divisão é para você se organizar, não para aparecer no texto), NESTA ORDEM:
>
> **MOVIMENTO 1 — O FILME** (2-3 frases; SÓ escreva este movimento SE houver FICHA TÉCNICA no relatório — sem ficha, comece direto no MOVIMENTO 2): apresente a premissa do filme a partir da `sinopse_oficial` da ficha — pode condensá-la, mas é PROIBIDO expandi-la com qualquer conhecimento externo sobre o filme, elenco, direção ou produção que não esteja na ficha fornecida. Se a `sinopse_oficial` parecer revelar algo além da premissa inicial do filme, use só a parte que é premissa e ignore o resto (a ficha NÃO tem passe livre sobre a regra de anti-spoiler abaixo). Mencione diretor, gênero e ano; duração só se for relevante para o que os dois movimentos seguintes vão dizer.
>
> **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): descreva como é assistir ao filme usando APENAS propriedades DESCRITIVAS da experiência (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade) em que os grupos CONCORDAM no NÚCLEO FACTUAL, mesmo divergindo na avaliação. Tom NEUTRO, SEM valência — este movimento descreve, não julga; gostar ou não gostar fica para o MOVIMENTO 3. Uma propriedade só entra neste movimento se passar nos TRÊS critérios abaixo, TODOS obrigatórios (v1.3.1 — reescrito após um defeito real observado):
>
> a. CRITÉRIO DE CATEGORIA: só propriedades DESCRITIVAS. É PROIBIDO qualquer juízo de QUALIDADE (atuações boas/ruins, roteiro inteligente/fraco, direção competente/questionável, elenco talentoso/fraco) — julgamento de qualidade é sempre disputado entre quem gostou e quem não gostou, e pertence ao MOVIMENTO 3, NUNCA a este.
> b. CRITÉRIO DE PRESENÇA: a propriedade precisa derivar de temas de PELO MENOS DOIS grupos, com o mesmo núcleo factual — a valência pode divergir ("lento e tedioso" num grupo + "lento e deliberado" noutro = consenso factual "ritmo lento"; a avaliação de cada grupo sobre esse ritmo é coisa diferente e não entra aqui).
> c. CRITÉRIO DE NÃO-CONTRADIÇÃO: se QUALQUER grupo contradiz o núcleo factual (não só diverge na avaliação, mas nega o fato em si), a propriedade está desqualificada — não entra no MOVIMENTO 2 de jeito nenhum.
>
> EXEMPLO POSITIVO (os três critérios satisfeitos): as reviews negativas chamam o ritmo de "lento e tedioso", as positivas de "lento e deliberado" — ambos descrevem RITMO (categoria descritiva, critério a), os dois grupos concordam no núcleo "lento" (critério b), nenhum grupo nega isso (critério c) → consenso válido para o MOVIMENTO 2: "ritmo lento e contemplativo".
>
> EXEMPLO NEGATIVO (falha real observada, v1.3.0 — caso de "the-invite-2026"): as reviews positivas elogiam "atuações marcantes" e "roteiro inteligente"; as negativas têm os temas "atuações e direção questionáveis" e "roteiro fraco". Isso NÃO é consenso: é uma propriedade AVALIATIVA (qualidade de atuação, qualidade de roteiro — falha o critério a) E os grupos se contradizem diretamente sobre ela (falha o critério c também). O correto é NÃO mencionar qualidade de atuação/roteiro no MOVIMENTO 2 — essa disputa pertence ao MOVIMENTO 3, atribuída a cada grupo separadamente.
>
> É PROIBIDO importar qualquer informação que não venha dos temas validados dos três grupos.
>
> OMISSÃO AUTORIZADA (v1.4.1 — leia isto antes de escrever o movimento): se MENOS DE DUAS propriedades passarem nos três critérios ao mesmo tempo, este movimento deve ser CURTO (1 frase) ou AUSENTE — e a narrativa passa direto ao MOVIMENTO 3. OMITIR É O COMPORTAMENTO CORRETO, não uma falha: não há cota de frases a cumprir aqui, e um filme cujos temas descritivos são poucos simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de qualidade suavizado ("estilo visual eficaz", "abordagem arrojada", "atuações competentes", "roteiro habilidoso") é PIOR do que não ter o movimento — é o defeito que o critério (a) proíbe, disfarçado de descrição por um advérbio de hesitação. Quando o movimento é omitido, `consensos_usados` vem como lista VAZIA (`[]`) — isso é resultado esperado, não erro. Para CADA propriedade usada no MOVIMENTO 2, registre em `consensos_usados` (ver formato de saída) a propriedade, os grupos de onde ela veio e os nomes EXATOS dos temas (copiados literalmente do relatório) que a sustentam — esse registro é o artefato de revisão humana que confirma que o consenso é real, não inventado.
>
> **MOVIMENTO 3 — O CONTRASTE** (enxuto — a interface já exibe as barras de frequência tema a tema, então aqui priorize os 2-3 temas MAIS FORTES de cada grupo, não a cobertura completa dos 6 possíveis): as perspectivas dos três grupos — quem não gostou, quem ficou no meio, quem gostou — sobre o filme. Neste movimento (e em qualquer lugar do texto que fale de grupos) valem as invariantes abaixo, TODAS ainda em vigor:
>
> a. **PAPEL:** o texto inteiro é para alguém que está DECIDINDO se assiste ao filme e que AINDA NÃO ASSISTIU.
> b. **FIDELIDADE:** toda afirmação deve derivar da ficha técnica e/ou dos temas e números recebidos. É PROIBIDO adicionar fatos, opiniões próprias, ou qualquer contexto externo sobre o filme, elenco, direção ou produção que não esteja no relatório. Se não está nos dados, não existe.
> c. **TAMANHO DOS GRUPOS — REGRA CRÍTICA:** os três grupos NÃO têm o tamanho da opinião real do público. O tamanho de cada grupo é fixado pelo MÉTODO DE COLETA (uma cota fixa por faixa de nota), não pela quantidade de pessoas que pensam assim — as medianas, por exemplo, serão sempre o menor grupo por construção, em todo filme. Portanto é PROIBIDO comparar tamanhos entre grupos ou inferir prevalência global: NADA de "a maioria dos espectadores", "a maioria do público", "grupo maior", "grupo menor", "minoria", "igualmente expressivo", "recepção polarizada", "opiniões divididas", "consenso" ou qualquer equivalente. Trate cada grupo como uma PERSPECTIVA, não como uma fatia quantificada do público: apresente-os como "entre quem não gostou...", "já entre quem amou...", "para quem ficou no meio-termo...".
> d. **PROPORÇÕES (só DENTRO de um grupo):** proporções são permitidas APENAS internamente a um grupo e SEMPRE ancoradas ao denominador daquele grupo. NUNCA uma proporção que compare grupos ou fale do público como um todo.
> **QUANTIFICADOR PRÉ-COMPUTADO (obrigatório, v1.2.3):** cada tema do relatório já vem com um `rótulo_quantificador` calculado pelo CÓDIGO a partir da fração real de menções — você NÃO calcula nem escolhe o quantificador sozinho. Ao expressar a frequência de um tema em prosa, USE o `rótulo_quantificador` fornecido para aquele tema (sinônimos de mesma força são permitidos: "a maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma parte"). É PROIBIDO usar um quantificador MAIS FORTE do que o fornecido. Um quantificador MAIS FRACO é permitido se a fluência do texto pedir — nunca o oposto. Escala de força, do mais fraco ao mais forte: poucos < alguns/uma parte < muitos/boa parte < cerca de metade < a maioria/mais da metade < quase todos/praticamente todos.
> **DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES (v1.4.1):** para CADA expressão de frequência que você usar na prosa ao falar de um tema, registre um item em `quantificadores_usados` (ver formato de saída) com o quantificador EXATO que você escreveu e o NOME EXATO do tema (copiado literalmente do relatório) de onde aquela frequência vem — um item por expressão usada. Antes de declarar, confira o par contra o relatório: se o quantificador que você escreveu for mais forte que o `rótulo_quantificador` daquele tema, corrija a PROSA (não o registro). Se você não usar nenhum quantificador de tema, a lista vem vazia.
> e. **ESTRUTURA:** a divisão em três grupos (quem não gostou / quem ficou no meio / quem gostou) deve permanecer legível na prosa do MOVIMENTO 3, em qualquer ordem que sirva à narrativa.
> f. **ESCOPO:** cada afirmação sobre um grupo é atribuída ao SEU grupo ("as reviews negativas apontam...", "quem deu notas altas destaca..."). É PROIBIDO generalizar para "os críticos", "a maioria" (do filme todo) ou "o consenso".
> g. **ANTI-SPOILER:** em QUALQUER movimento (incluindo o 1, com a sinopse oficial), é PROIBIDO mencionar eventos de trama, personagens específicos ou desfechos, mesmo que a sinopse ou algum tema tangencie isso (defesa em profundidade — a camada anterior já filtra os temas, você reforça, e a sinopse oficial é tratada com a mesma cautela).
> h. **FORMA:** português do Brasil, SEM aspas de citação, SEM subtítulos ou rótulos dos movimentos no texto final, entre 250 e 400 palavras ao todo.
>
> **RITMO** (v1.5.0 — aplica-se à narrativa INTEIRA, não só ao MOVIMENTO 3): **a.** alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras); PROIBIDO três períodos consecutivos de comprimento semelhante; ao menos UMA frase de até 10 palavras na narrativa inteira. **b.** PROIBIDO abrir dois períodos consecutivos com a mesma estrutura. **c.** o rótulo de peso pode aparecer em QUALQUER posição do período, não só na abertura. **d.** use conectivos de fala ("só que", "aí", "já", "e", "mas"); pode iniciar período por conjunção.
>
> **REGISTRO** (v1.5.0): **e.** depois de estabelecer QUEM fala, descreva o filme DIRETAMENTE, sem reintroduzir o sujeito a cada frase. **f.** verbos de reporte (elogia, destaca, aponta, relata, considera, classifica, menciona, ressalta, reconhece, expressa, descreve): NO MÁXIMO 1 por movimento. **g.** prefira verbos a nominalizações. **h.** PROIBIDOS advérbios intensificadores em -mente (intensamente, profundamente, extremamente, excessivamente) — NO MÁXIMO 1 em toda a narrativa. **i.** escreva como alguém contando de um filme para um amigo — fluido e leve, SEM gíria, SEM emoji, SEM interpelação direta ao leitor, SEM hipérbole.
>
> Responda APENAS com JSON puro no formato: `{"narrativa": "<seu texto>", "consensos_usados": [{"propriedade": "<nome curto da propriedade descritiva>", "grupos_de_origem": ["<negativas|medianas|positivas>", ...], "temas_de_origem": ["<nome EXATO do tema, copiado do relatório>", ...]}], "quantificadores_usados": [{"quantificador": "<a expressão de frequência EXATA que você escreveu na prosa>", "tema": "<nome EXATO do tema, copiado do relatório, de onde ela vem>"}], "marcadores_perspectiva": [{"grupo": "<negativas|medianas|positivas>", "trecho": "<o trecho EXATO da narrativa, copiado literalmente, onde o marcador de perspectiva desse grupo aparece>"}]}`. `consensos_usados` pode ser `[]` se o MOVIMENTO 2 não usou nenhuma propriedade consensual (ver OMISSÃO AUTORIZADA); `quantificadores_usados` pode ser `[]` se a prosa não quantificou nenhum tema; `marcadores_perspectiva` pode ser `[]` quando nenhum grupo do relatório exige marcação de perspectiva (regra presente só quando há distribuição real — ver abaixo).

#### A regra (c) tem DUAS variantes (v1.4.0) — a escolha é do CÓDIGO, pelo dado

O §D2 passa a ter duas versões da regra (c), e **só ela** muda entre as
variantes: todo o resto do prompt (os três movimentos, os critérios do
MOVIMENTO 2, o quantificador pré-computado, anti-spoiler, forma) é
**byte-idêntico**, para que a comparação A/B isole a mudança.

- **SEM distribuição** → `build_narrator_prompt(False)` devolve o prompt
  histórico (`NARRATOR_SYSTEM_PROMPT`), com a regra (c) restritiva da v1.2.1
  intacta. O fallback não é uma reescrita parecida: é a MESMA constante.
  **Emenda v1.4.1:** até a v1.4.0 esse texto era byte-idêntico ao da v1.3.1;
  a v1.4.1 alterou as partes **compartilhadas** do prompt (omissão do
  MOVIMENTO 2 e declaração de quantificadores), que valem nas duas variantes.
  A invariante que continua de pé — e é a que a comparação A/B precisa — é a
  original: **só a regra (c) difere entre as duas variantes** (verificado em
  teste). **Emenda v1.5.0:** a marcação de perspectiva e o exemplo de estilo
  few-shot (ambos abaixo) foram adicionados **dentro** da regra (c) COM
  distribuição, porque dependem do `share_real` — a marcação usa o
  `dominante` calculado a partir dele, e o exemplo usa vocabulário de peso
  que a variante SEM distribuição proíbe. A invariante "só a regra (c)
  difere" continua válida por construção: é justamente por dependerem do
  mesmo dado que essas duas adições vivem dentro dela, não fora. As regras
  de RITMO e REGISTRO (que não dependem de share), por sua vez, entraram nas
  partes **compartilhadas** do prompt — presentes, idênticas, nas duas
  variantes.
- **COM distribuição** → a regra (c) INVERTE, virando "PESO REAL DE CADA GRUPO":

> c. **PESO REAL DE CADA GRUPO — REGRA CRÍTICA** (a distribuição está disponível neste relatório): você recebeu a DISTRIBUIÇÃO REAL das notas do filme, vinda do histograma público — quantas pessoas deram cada nota. Isso é um dado diferente do tamanho dos grupos de reviews analisadas (50/20/30), que é apenas a COTA DE COLETA e continua NÃO significando prevalência. Regras:
> - **ANCORAGEM OBRIGATÓRIA:** cada grupo DEVE ser apresentado, na primeira vez que aparecer no MOVIMENTO 3, com o `rotulo_peso` que veio no relatório para ele (ex.: "a grande maioria das notas (~79%)"). É PROIBIDO usar um rótulo MAIS FORTE do que o fornecido; um MAIS FRACO é permitido se a fluência pedir — nunca o oposto. Você NÃO calcula nem escolhe esse rótulo: ele é dado.
> - **ABERTURA OBRIGATÓRIA:** o MOVIMENTO 3 começa pela perspectiva de MAIOR peso. Esta regra tem precedência sobre a liberdade de ordem da regra (e).
> - **ÊNFASE PROPORCIONAL:** dê aproximadamente mais espaço ao grupo de maior peso e menos ao de menor peso — um filme amplamente amado não pode soar dividido, e um amplamente rejeitado não pode soar morno.
> - **RESPEITO À MINORIA:** a perspectiva minoritária é apresentada COMO minoritária, mas SEM desdém, ironia ou insinuação de que quem pensa assim está errado. Menos espaço, mesma seriedade analítica: quem procura saber se vai gostar precisa entender o que incomodou essa parcela.
> - **VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS (v1.4.1):** o `rotulo_peso` vem do histograma de NOTAS do Letterboxd, ou seja, de TODO MUNDO que avaliou o filme; os temas vêm das REVIEWS COM TEXTO, um subconjunto bem menor. São duas populações diferentes. Portanto, ao expressar peso, é OBRIGATÓRIO escrever "das notas" ("a grande maioria das notas (~79%)") e é PROIBIDO escrever "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review nem sobre quem assistiu sem avaliar. As frequências de TEMA seguem no vocabulário oposto (regra d): sempre em relação às reviews analisadas daquele grupo. Os dois vocabulários nunca se misturam.
> - Continua PROIBIDO inventar um número-síntese do filme (nota média, score, "X de 10", "nota N"): os shares por faixa são a ÚNICA quantificação permitida, e são três números, nunca um só.
>
> **MARCAÇÃO DE PERSPECTIVA** (v1.5.0 — motivada pela regra de REGISTRO acima): ao reduzir os verbos de reporte, a fala de um grupo minoritário pode soar como fato do narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante. Cada grupo do relatório vem com uma `marcacao_perspectiva` PRÉ-COMPUTADA (nenhuma/simples/antecipada, a partir do `share_real` — você NÃO calcula nem escolhe esse valor):
> - TODO trecho que falar de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra é exigido).
> - `marcacao_perspectiva="simples"`: além da abertura, inclua ao menos UM marcador de perspectiva DENTRO do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
> - `marcacao_perspectiva="antecipada"`: o marcador interno precisa vir ANTES da primeira afirmação substantiva sobre esse grupo, não no fim do trecho.
> - Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
> - É PROIBIDO um marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito (mesma RESPEITO À MINORIA acima).
> Para CADA marcador de perspectiva que você usar, registre em `marcadores_perspectiva` (ver formato de saída) o grupo e o TRECHO EXATO, copiado literalmente da narrativa, onde ele aparece.
>
> EXEMPLO DE RITMO E MARCAÇÃO COM FILME FICTÍCIO — nunca reaproveitar seu conteúdo; os fatos vêm sempre do JSON recebido. O filme abaixo NÃO EXISTE e os números são INVENTADOS: eles servem só para mostrar a FORMA (variação de comprimento, aberturas diferentes, marcadores de perspectiva, ausência de verbos de reporte). Copiar qualquer fato, adjetivo ou número daqui é uma violação da regra de FIDELIDADE.
>
> ANTES (evite este ritmo): "A grande maioria das notas (~74%) elogia intensamente a condução do filme e o trabalho de câmera, destacando a habilidade de sustentar o clima em cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas sente que a indefinição do meio e a duração prolongada tornam a experiência cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo como arrastado e os personagens como estáticos."
>
> DEPOIS (busque este ritmo): "Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra num ponto só: o filme não tem pressa e usa isso a favor, porque cada silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma minoria das notas (~19%) chega até a metade junto. Para esse grupo, o problema aparece quando a história precisa decidir para onde vai, e não decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para eles a lentidão nunca vira método, os personagens não saem do lugar, e o final chega sem ter construído nada."

**`rotulo_peso` é PRÉ-COMPUTADO pelo código** — mesmo princípio da v1.2.3
(quantificador) e da v1.1.1 (denominador): o LLM não escolhe rótulo numérico.
Mapa determinístico sobre o `share_real`, do mais fraco ao mais forte:

| Faixa | Rótulo |
|---|---|
| **< 5%** | **uma fração mínima** *(v1.6.0)* |
| 5–10% | uma pequena minoria |
| 10–25% | uma minoria |
| 25–45% | uma parcela expressiva |
| 45–70% | a maioria |
| ≥ 70% | a grande maioria |

**v1.6.0 — faixa nova no extremo fraco.** Até a v1.5.0, 8% e 1% recebiam ambos "uma pequena minoria", achatando uma diferença de **oito vezes** entre os dois grupos minoritários — observado em `cidade-de-deus` (shares 91/8/1), onde o grupo mediano e o negativo apareciam com o mesmo peso verbal. A faixa `< 5% → "uma fração mínima"` separa o "muito pouco" do "quase nada" sem mexer em nenhuma outra fronteira, e sem tocar na convenção de desempate.

**Bordas resolvidas SEMPRE para o rótulo mais fraco** (itera do mais fraco ao
mais forte, primeiro match vence) — mesma convenção da v1.2.3:
`10 → uma minoria`, `25 → uma minoria`, `45 → uma parcela expressiva`,
`70 → a maioria`. Consequência documentada: "a grande maioria" começa de fato
em **71%**, não em 70% — subestimar o peso é aceitável, inflar não é.

O rótulo é sempre entregue **junto do percentual** (`"a grande maioria das
notas (~79%)"`): o número é o que impede o rótulo de virar retórica solta.

**Validação — a rede de prevalência MUDA DE SINAL:**

| | Sem distribuição | Com distribuição |
|---|---|---|
| Marcadores de prevalência ("minoria", "a maioria do público"…) | **violação** → retentativa → `prevalencia_suspeita` | **desligada** — essas palavras agora são EXIGIDAS pela regra (c); manter o detector ligado flaggaria toda narrativa correta |
| Ancoragem de peso | não se aplica (nada a ancorar) | **exigida** → retentativa (`_REFORCO_ANCORAGEM`) → `peso_nao_ancorado` |
| **(v1.4.1)** Vocabulário do peso ("das notas") | não se aplica (não há rótulo de peso) | **exigida** → retentativa (`_REFORCO_VOCABULARIO_PESO`) → `vocabulario_peso_suspeito` |

A checagem de ancoragem (`_ancoragem_de_peso_ok`) aceita, por grupo: o rótulo
fornecido, **qualquer rótulo mais fraco** (o prompt permite descer de força) ou
o percentual literal. Heurística deliberadamente permissiva — a defesa
principal é a instrução; isto detecta o modo de falha que importa: o narrador
ignorar os pesos e reescrever a narrativa antiga, de grupos equivalentes.

**Fallback (§3[G]):** sem distribuição, tudo isso desaparece sozinho — prompt
histórico, rede de prevalência original ativa, `peso_nao_ancorado` sempre
`False`, render com o disclaimer antigo, frontend sem shares. **Não há flag de
configuração:** a presença do dado é o interruptor.

**Por que a invariante (c) existe (v1.2.1 — defeito corrigido):** os buckets têm tamanhos fixados pela **cota de coleta** (50/20/30 = 10 válidas × nº de níveis de nota do bucket: 5/2/3), que **não** refletem a distribuição real da recepção. A narrativa da v1.2.0, sem a regra (c), inferia prevalência a partir das cotas ("grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada") — as medianas seriam "minoria" em todo filme, para sempre, por construção. A invariante (c) é a **defesa principal**; a telemetria abaixo é a rede de segurança.

**Por que o quantificador virou pré-computado (v1.2.3 — reincidência corrigida pela raiz):** a v1.2.2 tentou corrigir a inflação de quantificadores por INSTRUÇÃO — pedir ao LLM que calculasse a fração e escolhesse o rótulo por uma tabela. Funcionou parcialmente, mas **reincidiu**: na primeira regeneração das 3 narrativas pós-fix, "quase todos"/"praticamente todos" foi aplicado a frações de 65-70% **2 vezes** (a condição de escalada que o próprio changelog da v1.2.2 previa: *"um checador numérico pós-parsing é candidato futuro caso a inflação reincida"*). A correção pela raiz é o **mesmo princípio da v1.1.1** (denominador de `n_reviews_analisadas`): o LLM não decide número nem rótulo numérico — **o código é a autoridade**. `_serialize_output_for_narrator` agora pré-computa `fracao`/`rótulo_quantificador` por tema (`_fracao_e_rotulo`, mapa determinístico em `_rotulo_quantificador` — mesmas faixas da v1.2.2, resolução de sobreposição sempre para o rótulo mais fraco) e os injeta na entrada do narrador; o prompt (d) deixou de pedir cálculo e passou a proibir só usar um rótulo MAIS FORTE que o dado. **Rede de segurança complementar (v1.2.3):** checagem em nível de bucket — se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço; se persistir, `quantificador_suspeito: true`. Deliberadamente restrita a esse quantificador (o único modo de falha observado) — não cobre uso indevido dos demais rótulos.

**Por que o Movimento 1 é condicional à ficha (v1.3.0):** a ficha TMDB é aditiva por design (§3a) — pode faltar (API fora do ar, filme não encontrado, `--no-ficha`). Sem ela não há `sinopse_oficial` para ancorar o Movimento 1, e nada no prompt permite ao narrador inventar uma premissa a partir dos temas de review (violaria (b) FIDELIDADE e a proibição de conhecimento externo). Por isso o prompt instrui explicitamente pular para o Movimento 2 quando a ficha está ausente — mesmo comportamento defensivo do resto do pipeline (buckets `sem_analise` não inventam temas; a ficha ausente não inventa premissa).

O formato de saída `{"narrativa": ..., "consensos_usados": [...]}` reusa os mesmos adaptadores de provider (modo JSON nativo) e o parsing defensivo do §D. Sobre a prosa retornada aplicam-se as **mesmas validações pós-parsing** que fazem sentido para texto livre: **aspas** (remoção mecânica → `aspas_removidas`), **idioma**, **escopo**, **(v1.2.1) prevalência**, **(v1.2.3) quantificador** (ver acima) e **(v1.4.1) vocabulário do peso** — inalteradas pela reestruturação em movimentos da v1.3.0, elas operam sobre o texto final completo, independente de quantos movimentos o compõem. Todas com 1 retentativa combinada (reforço anexado ao prompt); se persistir, aceita e sinaliza a flag correspondente (`idioma_invalido`/`escopo_suspeito`/`prevalencia_suspeita`/`quantificador_suspeito`/`vocabulario_peso_suspeito`). As checagens sobre os campos **declarados** pelo narrador (`consensos_usados`, v1.3.1; `quantificadores_usados`, v1.4.1) entram na MESMA retentativa combinada — o orçamento do narrador continua sendo, no pior caso, 1 chamada + 1 retentativa de JSON + 1 retentativa de validação. Heurísticas **acento-sensíveis** como as demais (rede de segurança; a defesa principal é a invariante/pré-computação do prompt). A narrativa entra no JSON no campo global **`narrativa`** (+ `narrativa_flags` de telemetria).

**Telemetria de `consensos_usados` (v1.3.1, NOVO):** para cada propriedade que o narrador usar no MOVIMENTO 2, o próprio LLM declara `{propriedade, grupos_de_origem, temas_de_origem}` — `grupos_de_origem` restrito a `negativas`/`medianas`/`positivas`, `temas_de_origem` com os nomes de tema EXATOS (copiados do relatório recebido). Esse registro é o **artefato de revisão humana** de cada execução: permite conferir, tema a tema, se o consenso declarado é real (existe nos dados citados) ou inventado — o mesmo tipo de exercício feito manualmente no relatório da v1.3.0 que descobriu o defeito do `the-invite-2026`, agora com o material pronto em vez de precisar recomputar frações à mão.

Validação pós-parsing (código, não substitui a revisão humana): `_consensos_validos` (`synthesize.py`) confere que todo `grupos_de_origem` citado é um dos três nomes válidos E existe no relatório do filme, e que todo `temas_de_origem` citado corresponde a um tema real de algum dos grupos citados naquele item — comparação por igualdade de string com o nome do tema como veio no relatório. Falha em qualquer item → **1 retentativa combinada** com as demais (reforço anexado ao prompt, `_REFORCO_CONSENSOS`); se persistir, aceita a resposta da retentativa e sinaliza `consenso_suspeito: true` em `narrativa_flags` — telemetria visível, não correção silenciosa (mesma política das demais flags do §D2). `consensos_usados: []` é válido por vacuidade (MOVIMENTO 2 pode não ter nenhuma propriedade que passe nos três critérios).

`consensos_usados` é persistido no JSON do filme como campo global (junto de `narrativa`/`narrativa_flags`) e exibido no render de terminal, no tom `narrativo`/`ambos`, como bloco compacto após a prosa ("Consensos do movimento 2: • propriedade — grupos: ... — temas: ...") — visível em toda execução, não só sob demanda.

#### Telemetria de `quantificadores_usados` (v1.4.1, NOVO) — o quantificador declarado junto do seu tema

**O defeito (3ª ocorrência do MESMO modo de falha).** Na v1.4.0, a narrativa de `the-invite-2026` escreveu "Quase todos" para o tema `Atuações e química do elenco` (**20/30 = 67%**), cujo `rotulo_quantificador` pré-computado era **"a maioria"**. As duas defesas vigentes não pegaram:
- a **pré-computação** (v1.2.3) entrega o rótulo certo no relatório, mas não impede o modelo de escrever outra coisa na prosa;
- a **rede de segurança** (v1.2.3) é de **nível de bucket** — ela só pergunta se ALGUM tema do filme tem fração ≥80%. Outro tema do mesmo grupo (`Direção e roteiro (geral)`, 25/30 = 83%) dava lastro, e a checagem passou.

O buraco é estrutural: **nenhuma checagem sobre a prosa consegue saber a QUAL tema um "quase todos" solto se refere.** A correção segue o padrão que já resolveu o problema análogo do MOVIMENTO 2 (`consensos_usados`, v1.3.1): em vez de adivinhar, **o narrador declara**, e o código julga — o LLM continua sem decidir número nem rótulo (princípio da v1.1.1/v1.2.3).

**Formato.** A saída do narrador ganha `quantificadores_usados`: lista de `{quantificador, tema}` — **cada expressão de frequência usada na prosa**, declarada junto do **nome EXATO do tema** de onde ela vem (copiado literalmente do relatório recebido). Lista vazia é válida (a prosa pode não quantificar tema nenhum).

**Validação pós-parsing** (`_quantificadores_validos`, `synthesize.py`), par a par:
1. **Tema inexistente** no relatório (nenhum bucket tem um tema com esse nome exato) → violação.
2. **Quantificador MAIS FORTE** que o `rótulo_quantificador` pré-computado daquele tema → violação. A força da expressão declarada é resolvida por `_forca_declarada` sobre a mesma escala do prompt (`poucos` < `alguns`/`uma parte` < `muitos`/`boa parte` < `cerca de metade` < `a maioria`/`mais da metade` < `quase todos`/`praticamente todos`), casando por substring com a chave mais longa primeiro (`mais da metade` nunca é lido como `metade`). Quantificador **mais fraco** continua permitido (o prompt autoriza descer de força).

Violação em qualquer par → **1 retentativa** combinada com as demais validações de prosa (reforço `_REFORCO_QUANT_DECLARADO`); se persistir, aceita e sinaliza **`quantificador_suspeito: true`** — a flag **já existente** (v1.2.3) passa a ser alimentada por esta checagem **além** da de bucket, que permanece ativa e inalterada. Mesma política de telemetria visível das demais flags.

**Duas limitações deliberadas** (heurística, como as demais redes do §D2; a defesa principal é a instrução + pré-computação):
- **Expressão irreconhecível** (fora da escala, ex. "um punhado disperso") não é comparável e **não** conta como violação — não flaggar prosa possivelmente correta é preferível a flaggar por não entender.
- **Tema homônimo em mais de um grupo** (frações diferentes): o par declarado não diz de qual grupo veio, então a checagem resolve pela força **mais alta** entre os homônimos. Na ambiguidade, não flagga.

`quantificadores_usados` é persistido no JSON como campo global (junto de `narrativa`/`consensos_usados`) e exibido no render de terminal (tom `narrativo`/`ambos`) como bloco compacto, no mesmo padrão do bloco de consensos — e **com a conferência ao lado de cada par** ("• "quase todos" — tema: X (fração real 67% → rótulo: a maioria)"), porque o par sozinho não diria a um leitor humano se está inflado.

#### Invariante de vocabulário do peso (v1.4.1): **notas × reviews**

Duas populações **diferentes** alimentam a narrativa, e confundi-las é uma infidelidade silenciosa:

| | Origem | Denominador | Vocabulário obrigatório |
|---|---|---|---|
| **Rótulo de peso** (`rotulo_peso`, §3[G]) | histograma público de **NOTAS** | todo mundo que **avaliou** o filme | "**das notas**" |
| **Frequência de tema** (`rótulo_quantificador`, v1.2.3) | **REVIEWS COM TEXTO** analisadas (subconjunto) | `n_reviews_analisadas` do grupo | "das **reviews** analisadas" (regra d) |

Regra: ao expressar **peso**, é **OBRIGATÓRIO** dizer "das notas" e **PROIBIDO** dizer "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review, nem sobre quem assistiu sem avaliar. As frequências de tema continuam expressas em relação às **reviews analisadas**. Os dois vocabulários não se misturam. A regra está escrita dentro da própria regra (c) invertida do prompt (variante COM distribuição — sem distribuição não há peso a expressar, e a invariante não existe).

**Checagem barata** (`_vocabulario_peso_ok`, `synthesize.py`), duas passadas literais sobre a prosa, só quando há distribuição:
1. **rótulos inequívocos de peso** (`uma pequena minoria`, `uma minoria`, `uma parcela expressiva`, `a grande maioria`) → inspeciona os ~40 chars seguintes; se aparecer "reviews"/"público"/"espectadores" **antes** de "notas", é violação;
2. **qualquer percentual** (`~79%`) → inspeciona os ~60 chars anteriores, com o mesmo teste.

A passada (2) existe porque **"a maioria" é ambígua**: é rótulo de peso E rótulo de quantificador de tema — e "a maioria das reviews negativas analisadas" é a forma **correta** exigida pela regra (d). Ancorar no percentual (que só acompanha peso, nunca frequência de tema na prosa) desambigua sem flaggar prosa certa. Violação → **1 retentativa** (reforço `_REFORCO_VOCABULARIO_PESO`); se persistir, **`vocabulario_peso_suspeito: true`** em `narrativa_flags`, visível no render.

**Flag `--tom {estruturado,narrativo,ambos}` — MECANISMO DE DESENVOLVIMENTO (não é feature final):** existe para o **teste A/B humano** entre a saída estruturada (atual) e a narrativa durante o desenvolvimento. `estruturado` (default) mantém o comportamento histórico intacto; `narrativo` imprime só a prosa **mas os metadados de coleta e os avisos NUNCA somem** — modo degradado (sem_analise/reduzido) e flags continuam visíveis nos dois tons; `ambos` imprime os dois lado a lado. `narrativo`/`ambos` gastam **+1 chamada LLM** (o narrador). **A v2 consolidará um tom único** após a avaliação humana do A/B; até lá, `--tom` é dev-only. (Atalho de A/B: `--reuse-synthesis` reaproveita a síntese de um JSON já gerado, gastando só a chamada do narrador — para comparar tons sobre a MESMA síntese.)

### [F] Ficha do filme (TMDB) — v1.3.0

Etapa **aditiva e independente** do resto do pipeline (`ficha.py`): dado o título/ano do filme (derivados do slug por default — `titulo_ano_de_slug`, com override via `--titulo`/`--ano` no CLI para os casos em que o slug não carrega ano, ex. `cure`), busca a ficha técnica na API pública do TMDB (`api.themoviedb.org/3`).

**Resolução do ID:** `GET /search/movie?query=<título>&language=pt-BR[&year=<ano>]`. Quando `ano` está disponível, é usado tanto como parâmetro de busca quanto para desambiguação pós-resposta: entre os candidatos com `release_date` no ano pedido, prefere o de maior `popularity` do TMDB — **não** o primeiro da lista. Necessário porque títulos comuns podem devolver mais de um candidato do MESMO ano (ex. "The Invite" tem múltiplas entradas no TMDB; "Cure" 1997 devolve o filme de Kiyoshi Kurosawa E um documentário obscuro do mesmo ano) — a ordem da API não é por relevância quando o filtro de ano está ativo. Medido ao vivo na regeneração da v1.3.0: escolher o primeiro resultado do ano pegou o documentário (`popularity=0.28`, 1 voto) em vez do filme correto (`popularity=3.79`, 820 votos); corrigido para desempate por popularidade antes da entrega.

**Resolução de ano confiável (v1.7.0) — Tarefa 1.** Defeito real: `espectro24 --slug cure` sem `--ano` desambiguava só pelo TÍTULO (nenhum ano para filtrar), e o TMDB devolveu como único candidato "The Cure" (2026, dir. Nancy Leopardi) — um filme completamente diferente — sem nenhum aviso. A cadeia de resolução do ano passa a ter três degraus, nesta ordem, cada um só tentado se o anterior não resolveu: **(a)** sufixo `-YYYY` do slug (`titulo_ano_de_slug`, já existia); **(b)** se ausente, **1 requisição** à página principal do filme no Letterboxd (`resolver_ano_letterboxd`, `ficha.py`) — mesmo `fetcher`/cache/headers/delay do resto do pipeline, extrai o ano do link `/films/year/YYYY/` ou do `<meta property="og:title">` (formato "Título (YYYY)"); falha de rede/ausência de ano → `None`, nunca levanta; **(c)** se AINDA assim indisponível, a ficha **não é buscada** — o pipeline segue sem ela (`output["ficha"] = None`, `output["ficha_indisponivel"] = "ano_desconhecido"`) em vez de arriscar a desambiguação cega que causou o defeito. O campo `ano_fonte` (`"slug" | "letterboxd" | "argumento"`) entra na própria ficha, sempre visível.

**Guarda de sanidade — ano divergente descarta a ficha inteira (v1.7.0, Tarefa 1.2).** Mesmo com ano resolvido, o TMDB pode devolver o candidato errado quando NENHUM resultado da busca tem `release_date` no ano pedido (o código então cai para o primeiro resultado da lista, que pode ser de qualquer ano — o próprio modo de falha do defeito real do `cure`). Depois de montar a ficha, se o ano esperado (nunca o do próprio resultado do TMDB — seria circular) divergir do `ano` da ficha em mais de 1, a ficha inteira é DESCARTADA: `buscar_ficha` retorna `(None, aviso, {"motivo": "ano_divergente", "esperado": X, "recebido": Y})`, e o CLI persiste esse dict em `output["ficha_descartada"]`. Melhor nenhuma ficha do que a ficha de outro filme. A ficha descartada por esse motivo NÃO é cacheada como "não encontrado" — uma nova tentativa (ex. com um título mais preciso) não fica travada numa rejeição antiga.

**Detalhes:** `GET /movie/{id}?language=pt-BR&append_to_response=credits`. Extraídos: título pt-BR (`title`), sinopse oficial (`overview`), gêneros (`genres[].name`), duração (`runtime`), diretor (primeiro `credits.crew[]` com `job == "Director"`), ano (`release_date[:4]`).

**Diretor em escrita latina (v1.6.0):** o TMDB devolve o nome do diretor no **alfabeto nativo** quando a localidade pt-BR não tem tradução — `cure` vinha com `"黒沢清"`, que foi parar na narrativa **publicada** (o narrador só reproduz o que a ficha entrega). Quando o nome pt-BR não está em escrita latina (`_e_escrita_latina`, checagem sobre `unicodedata.name` de cada letra — cobre diacríticos latinos como ç/é/ñ sem lista de exceções), o `credits` de `en-US` é consultado e a transliteração é usada (`"Kiyoshi Kurosawa"`). A ficha carrega `diretor_transliterado: true` — visível, nunca silencioso. **Custo:** no máximo 1 requisição extra, e só para filmes nessa condição; quando o fallback de sinopse já buscou `en-US`, a resposta é **reaproveitada** em vez de refeita. Se o `en-US` também não for latino, mantém o nome original (melhor um nome em alfabeto nativo do que nenhum). Cacheado junto da ficha, como todo o resto.

**Fallback de sinopse:** se `overview` vier vazio na resposta pt-BR (acontece para filmes com localização incompleta no TMDB), uma segunda chamada com `language=en-US` busca o overview em inglês; a ficha carrega esse texto com a flag `sinopse_fallback_en: true` — nunca fica silenciosamente vazia, mas também nunca finge ser pt-BR quando não é.

**Cache em disco** (mesmo padrão do cache do Letterboxd em `fetcher.py`, raiz própria `<cache-dir>/_tmdb/`): chave determinística por `título_normalizado[_ano]`; nunca rebusca filme já buscado, inclusive "não encontrado" (evita reconsultar buscas vazias). Diferente do cache de rede do Letterboxd, falhas transitórias (rede, HTTP não-200) **não são cacheadas** — podem ser passageiras, vale tentar de novo na próxima execução; só resultado de sucesso ou "sem resultado" persistem.

**Falha nunca bloqueia (decisão de design central desta etapa):** chave ausente, erro de rede, HTTP não-200, filme não encontrado, ou ano indisponível/divergente → `buscar_ficha` retorna `(None, aviso, ficha_descartada)` (v1.7.0 — terceiro elemento da tupla, `None` nos casos que não são divergência de ano). O CLI imprime o aviso em stderr, persiste `ficha_descartada` no JSON quando presente, e segue o pipeline inteiro (coleta, síntese, narrador, render) com `output["ficha"] = None`. Nenhuma exceção de `ficha.py` escapa para o `main()` do CLI.

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

### [G] Distribuição real de notas (histograma do Letterboxd) — v1.4.0

Etapa **aditiva e independente**, irmã da ficha TMDB (§F): não depende das
reviews coletadas e não é bloqueada por elas. Detalhes de sondagem, seletores
e armadilhas em **`FASE_HISTOGRAMA.md`**.

**Endpoint:** `letterboxd.com/csi/film/<slug>/rating-histogram/` — fragmento CSI
server-rendered, **1 requisição por filme**, cacheada em
`<cache-dir>/_histograma/<slug>.html`. Preferido à página principal do filme
por ser ~5,8 KB em vez de centenas, expondo exatamente o dado desejado.

**Estrutura (validada ao vivo):** `table.chart tbody tr` × **10** (sempre 10,
um por nível de 0.5 a 5, em ordem crescente). Nível em `th._sr-only` (glifos:
`half-★`, `★`, `★½`, …). **Contagem exata no atributo `title` do `.barcolumn`.**

Três armadilhas, todas tratadas (ver `FASE_HISTOGRAMA.md` §3):
1. **Nível zerado não tem `<a>`** — vira `<span class="barcolumn" title="No ★½ ratings">`.
   Buscar `a.barcolumn` perderia os zeros **em silêncio** e inflaria o total,
   justamente em filmes pequenos (onde o denominador é mais frágil). O seletor
   é `.barcolumn`, qualquer tag.
2. **O `_sr-only` da barra ABREVIA** (`23.4K`, `111K`) — inútil como fonte. O
   `title` traz o número exato.
3. **Singular/plural e "No"** — `456 … ratings`, `1 … rating`, `No … ratings`.

**Agregação (código, não prompt):** `share_real` por bucket =
`soma dos níveis do bucket / total`, em **percentual inteiro**. Cada bucket é
arredondado **independentemente**, para que o número de cada grupo seja a
melhor aproximação inteira do seu próprio share. **Consequência aceita e
documentada:** a soma dos três pode dar 99 ou 101 (ex.: `cure` → 3+17+79=99).
Preferido a redistribuir o resto, o que tornaria algum bucket menos fiel ao
próprio dado — coerente com a política do projeto de não maquiar número. A
interface **nunca exibe a soma**.

**A cota de coleta 50/20/30 NÃO muda** (decisão explícita). Racional: cota e
peso respondem a perguntas diferentes e ambas continuam necessárias.
- A **cota** é *amostragem estratificada*: garante **profundidade igual por
  perspectiva**. Quem quer saber o que incomodou o grupo minoritário precisa de
  ~50 reviews negativas lidas, não de 1 review porque só 1% deu nota baixa.
  Reduzir a amostra do grupo pequeno destruiria a análise temática justamente
  onde ela é mais informativa para a decisão de assistir.
- O **peso** é a prevalência real, e agora está exibido separadamente.

Ou seja: **profundidade igual, peso informado** — que é o princípio norteador
(§0) aplicado à coleta.

**Consequência de vocabulário (v1.4.1) — o histograma conta NOTAS, não
reviews.** O denominador de `share_real` é `n_notas_total`: **todo mundo que
avaliou** o filme. Os temas, por outro lado, saem das **reviews com texto**
que passaram nos filtros (§C) — um subconjunto muito menor da mesma
população. As duas coisas nunca compartilham denominador, e por isso o
produto **nunca** apresenta um rótulo de peso como se fosse sobre reviews,
espectadores ou "o público": um rótulo de peso é sempre "**das notas**". A
regra completa, com a checagem que a defende no narrador, está em §D2
("Invariante de vocabulário do peso"); o render de terminal e o frontend já
seguiam esse vocabulário desde a v1.4.0 (`· ~X% das notas`).

**Falha nunca bloqueia** (idêntico a §F): chave estrutural inesperada, rede,
HTTP, anti-bot ou filme sem nota alguma → `collect_distribuicao` retorna `None`,
o campo sai `null` e **todo o resto do pipeline degrada sozinho** para o
comportamento da v1.3.1 (ver "Fallback" no §D2). Nem `AntiBotError` escapa:
perder a distribuição não justifica abortar uma coleta que já custou dezenas de
requisições.

**Saída** (§4): bloco global `distribuicao` + `share_real` por bucket.
```json
{
  "n_notas_total": 375278,
  "por_nivel": {"0.5": 456, "1.0": 1037, "…": 0, "5.0": 99242},
  "por_bucket": {"negativas": 3, "medianas": 17, "positivas": 79},
  "fonte": "letterboxd_histograma"
}
```
`share_real` é **omitido** (chave ausente, não `0`) quando não há distribuição —
o consumidor distingue "não coletado" de "coletado e deu 0%".

**Flag `--no-distribuicao`** pula a busca (e cai no fallback), para A/B.

### [E2] Editor — passe de EDIÇÃO da narrativa (v1.6.0, NOVO)

Etapa **PÓS-narrador**, ativa junto com `--tom narrativo|ambos`, desligável com `--no-edicao`. **Uma única chamada LLM por filme** (+1 sobre o custo da v1.5.0), mesmo provider/modelo, na configuração de prosa (§2: `thinking_budget=4096`, `max_output_tokens=16000`).

**O princípio: separar o que não devia ter sido empilhado.** Até a v1.5.0, um único prompt respondia por honestidade (números, rótulos, atribuição, anti-spoiler) **e** por fluência (ritmo, registro). Falhou nas três frentes documentadas no §D2. A v1.6.0 separa:

| | Narrador §D2 | Editor §E2 |
|---|---|---|
| Responde por | **verdade** e estrutura | **leitura** e ritmo |
| Recebe | relatório validado + ficha | **só o texto + trechos protegidos** |
| Pode inventar fato? | não (só usa o relatório) | **não tem como** — não recebe fonte de fato |
| Pode alterar número? | não escolhe número (pré-computado) | **não** — verificado mecanicamente |

**Decisão de arquitetura (invariante):** o editor recebe **EXCLUSIVAMENTE** o texto da narrativa validada e a lista de trechos protegidos. **Não recebe** o JSON dos buckets, nem as reviews, nem a ficha, nem os temas. A garantia anti-invenção é **estrutural, não uma instrução**: o que não está na entrada, o editor não tem como saber. É a mesma fronteira que o §D2 estabelece para o narrador, apertada mais um nível.

#### Trechos protegidos (montados em CÓDIGO, `montar_protegidos`) — ENXUGADOS na v1.7.0

O editor nunca escolhe o que é intocável. A lista sai do que o narrador **já declarou**:

1. **Rótulos de peso, SEMPRE com percentual** — a forma canônica e as mais fracas permitidas (`"a grande maioria das notas (~79%)"`); a forma nua sem percentual (`"a grande maioria das notas"`) **saiu** na v1.7.0 — ver abaixo;
2. **Todo token que contenha dígito** (percentuais, anos, durações).

Até a v1.6.2, a lista também incluía (2) as expressões de quantificador declaradas em `quantificadores_usados` e (3) as expressões de atribuição dos `marcadores_perspectiva`. **A v1.7.0 (Tarefa 2) removeu as duas.** Defeito real: com 14-16 protegidos por filme — incluindo palavras soltas como "muitos" —, o editor era descartado com frequência (`cure`, 2 protegidos perdidos mesmo após retentativa) ou inventava frases penduradas só para reencaixar um protegido que mudou de lugar (`cidade-de-deus`: *"Essa é a opinião de uma fração mínima das notas."*, sem função nenhuma além de conter a string exigida). Pior: um defeito gramatical real da narrativa bruta — *"destacando a a maioria o estilo visual"* — **sobreviveu à edição** porque "a maioria" estava na lista de protegidos, e o editor não ousou tocar na frase.

A remoção é segura porque as duas coisas removidas **já tinham verificação semântica melhor do que a comparação literal**, preexistente e mais forte:
- **Quantificador** — `conferencia_quantificador` (v1.4.1) confere o PAR declarado (`{quantificador, tema}`) contra o rótulo pré-computado da fração real; não exige que a STRING sobreviva, só que a afirmação continue certa.
- **Atribuição de perspectiva** — `_marcadores_validos` (v1.6.1) varre o MOVIMENTO de cada grupo em busca de qualquer expressão de atribuição reconhecida; não exige que a string DECLARADA sobreviva, só que alguma expressão válida exista onde precisa. **v1.7.0 estende essa checagem para dentro do próprio `editar_narrativa`**: o estado de `_marcadores_validos` sobre o texto bruto é comparado ao mesmo sobre o texto editado, e uma regressão (válido → inválido) entra no mesmo mecanismo de regressão de honestidade que já existia para idioma/escopo/prevalência/vocabulário/ancoragem — motivo `"perspectiva_nao_marcada"` no descarte.

Proteger a STRING era redundante com uma checagem melhor, e engessava a reescrita sem ganhar nada em honestidade — a checagem semântica já cobria o que importa.

Dois cuidados de implementação, ambos motivados por comportamento real (continuam valendo para o que ainda é protegido):
- **Só entram candidatos que REALMENTE ocorrem no texto do narrador.** Proteger uma string ausente tornaria a checagem impossível de satisfazer — o editor seria punido por algo que o narrador não escreveu. Em `cidade-de-deus` (v1.5.0) o narrador declarou um marcador que ele mesmo não reproduziu literalmente.
- **O protegido é a forma COMO APARECE no texto**, não a canônica: o narrador capitaliza no início de frase ("A grande maioria das notas (~79%)") enquanto o rótulo canônico é minúsculo. A busca casa ignorando caixa e guarda a fatia real.
- **Tokens numéricos entram SEM a pontuação em volta** (`~3%`, não `(~3%),`): blindar parêntese e vírgula impediria o editor de repontuar, que é metade do trabalho de ritmo.

##### Exceção de capitalização na checagem de trecho perdido (v1.7.1)

Defeito real: o rótulo protegido guarda a caixa de onde apareceu a **primeira vez** — em início de frase, capitalizado ("A grande maioria das notas (~91%)"). Quando o editor move o rótulo para o **meio** de um período reescrito ("Para a grande maioria das notas (~91%), ..."), a letra inicial deveria virar minúscula — mas a checagem, sendo 100% literal, tratava isso como perda do protegido. Publicado ao vivo em `cidade-de-deus` (v1.7.0): "Para A grande maioria...", "Já Uma pequena minoria...", maiúscula incorreta no meio da frase, porque o editor não ousou ajustar por medo do descarte.

`_protegido_presente` (`synthesize.py`) agora aceita o trecho tanto na forma literal quanto com **só a primeira letra** em caixa alternada (`_variante_primeira_letra`) — nenhuma outra letra, palavra, número ou pontuação ganha essa folga. O prompt do editor (regra INVIOLÁVEL — TRECHOS PROTEGIDOS) ganhou uma exceção explícita autorizando esse ajuste específico. Testado nos dois sentidos: caixa ajustada é aceito; qualquer outra palavra alterada (mesmo pequena) continua sendo perda; número alterado continua descartando mesmo com a caixa "corrigida" no processo.

##### Conflito histórico (v1.6.0, superado pela v1.7.0): proteger marcadores × corrigir gramática

Descoberto num ensaio ponta a ponta sobre o `cure` **publicado**, antes de qualquer chamada real: o narrador havia declarado, como `trecho` do marcador de `negativas`, **o próprio período agramatical** — *"Uma pequena minoria das notas (~3%), para quem o filme é superestimado e pretensioso, a maioria considerou o ritmo…"*. Proteger o período inteiro (ou mesmo só a expressão de atribuição dentro dele, solução da v1.6.0) tornava as regras do §E2 tensas: o editor que reescrevesse em volta de um protegido corria o risco de ter de inventar contexto para reencaixá-lo. A v1.7.0 resolve pela raiz: a atribuição não é mais protegida por STRING nenhuma — só pela checagem semântica (`_marcadores_validos`, ver acima), que valida a EXISTÊNCIA da atribuição, não a sobrevivência de uma redação específica. **A regra de gramática obrigatória (§E2, "GRAMÁTICA") ganhou uma frase explícita (Tarefa 2.4):** corrigir "a a"/"de de"/artigo repetido é obrigatório mesmo quando o defeito encosta num trecho protegido, desde que o protegido em si (o rótulo de peso ou o número) permaneça intacto por dentro.

#### Prompt do editor (SPEC — texto oficial, `_EDITOR_SYSTEM_PROMPT` em `synthesize.py`)

> Você é um EDITOR de texto. Recebe um texto pronto sobre a recepção de um filme e o reescreve para que ele SOE MELHOR — sem mudar nada do que ele diz.
>
> Você NÃO tem acesso aos dados de origem. Tudo o que você pode afirmar já está no texto recebido; não há nada a acrescentar, e você não teria como verificar nada que inventasse.
>
> **REGRA INVIOLÁVEL — TRECHOS PROTEGIDOS:** junto do texto você recebe uma lista de TRECHOS PROTEGIDOS. Cada um deles precisa aparecer no seu texto final EXATAMENTE como foi entregue — mesmos caracteres, mesma pontuação, mesmos números, sem reformulação, sem sinônimo, sem reordenar as palavras dentro do trecho. Você pode mover um trecho protegido para outro ponto da frase ou do parágrafo, e pode reescrever tudo em volta dele; o que não pode é alterar o trecho por dentro. Se uma melhoria de ritmo exigir quebrar um trecho protegido, NÃO faça a melhoria — o trecho vence. EXCEÇÃO ÚNICA (v1.7.1): se mover um trecho protegido para o meio de uma frase deixar a letra inicial dele com a caixa errada (maiúscula que devia virar minúscula, ou o contrário), você PODE ajustar só essa primeira letra — nenhuma outra letra, palavra, número ou pontuação do trecho.
>
> **TAMBÉM PROIBIDO:** adicionar, remover ou alterar QUALQUER número ou percentual, mesmo fora dos trechos protegidos; adicionar, remover ou alterar nome próprio (de pessoa, filme, lugar); adicionar, remover ou alterar qualquer afirmação factual — se o texto diz que um grupo achou o ritmo lento, o seu texto diz a mesma coisa; acrescentar informação que não esteja no texto recebido, inclusive conhecimento seu sobre o filme; trocar a quem uma opinião é atribuída.
>
> **RITMO:** alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras); o texto final precisa ter pelo menos UMA frase de até 10 palavras; não abra dois períodos seguidos com a mesma estrutura; use conectivos de fala ("só que", "aí", "já", "e", "mas"), podendo iniciar período por conjunção.
>
> **REGISTRO:** prefira verbos a nominalizações ("as situações se repetem e o filme cansa", não "a repetição das situações torna a experiência cansativa"); no máximo UM advérbio terminado em -mente no texto inteiro; reduza verbos de reporte (elogia, destaca, aponta, relata, considera, classifica, menciona, ressalta, reconhece) quando já estiver claro de quem é a opinião — MAS nunca à custa de um trecho protegido, e nunca apagando a atribuição de quem pensa o quê.
>
> **TOM:** alguém contando de um filme para um amigo. Fluido e leve, mas SEM gíria, SEM emoji, SEM interpelação direta ao leitor ("você vai adorar"), SEM hipérbole, SEM aspas de citação.
>
> **GRAMÁTICA (obrigatório):** cada período do texto final precisa ser uma frase completa e correta em português do Brasil — sujeito e predicado coerentes, concordância certa, sem anacoluto. Se o texto recebido contiver um período quebrado ou truncado, CORRIGI-LO É OBRIGATÓRIO; essa é a única situação em que você reescreve a estrutura de uma frase por necessidade, e mesmo assim preservando o que ela afirma e os trechos protegidos que ela contém.
>
> **TAMANHO:** entre 220 e 400 palavras.
>
> **EXEMPLO DE RITMO COM FILME FICTÍCIO** — nunca reaproveitar seu conteúdo. O filme abaixo NÃO EXISTE e os números são INVENTADOS: servem só para mostrar a FORMA. Copiar qualquer fato, adjetivo ou número daqui seria inventar informação.
>
> ANTES (ritmo monótono): "A grande maioria das notas (~74%) elogia intensamente a condução do filme e o trabalho de câmera, destacando a habilidade de sustentar o clima em cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas sente que a indefinição do meio e a duração prolongada tornam a experiência cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo como arrastado e os personagens como estáticos."
>
> DEPOIS (ritmo desejado — mesmos fatos, mesmos números, mesma atribuição): "Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra num ponto só: o filme não tem pressa e usa isso a favor, porque cada silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma minoria das notas (~19%) chega até a metade junto. Para esse grupo, o problema aparece quando a história precisa decidir para onde vai, e não decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para eles a lentidão nunca vira método, os personagens não saem do lugar, e o final chega sem ter construído nada."
>
> Responda APENAS com o texto final editado. Sem preâmbulo, sem explicação, sem JSON, sem aspas envolvendo o texto.

**A regra de gramática não é decorativa:** a v1.5.0 publicou, na configuração de produção, a frase *"Muitos para eles, há uma falta de tensão ou mistério…"* (`cure`, célula flash/thinking-off do diagnóstico) e um anacoluto no `cure` publicado (*"Uma pequena minoria das notas (~3%), para quem o filme é superestimado e pretensioso, a maioria considerou o ritmo…"*). Corrigir período quebrado é a única reescrita estrutural que o editor tem **obrigação** de fazer.

#### Verificação mecânica da saída do editor (código, não prompt)

Sobre o texto editado, nesta ordem:

**(a) Trechos protegidos** — cada um precisa aparecer **literalmente**. Aqui a comparação é literal de propósito (ao contrário da checagem de marcadores do §D2): o ponto é justamente que o editor não reformule.
**(b) Conjunto numérico** — o multiconjunto ordenado de tokens numéricos (`_tokens_numericos`) do texto editado deve ser **idêntico** ao do original. Nenhum número novo, nenhum removido, nenhum alterado. Como todo token com dígito também é protegido por (a), esta checagem é a **segunda rede**: pega sobretudo número **inventado**, que (a) não veria.
**(c) Honestidade reexecutada** — as validações do §D2 que fazem sentido sobre texto livre (idioma, aspas, escopo, prevalência, vocabulário de peso, ancoragem de peso) rodam de novo sobre o texto editado. A comparação é **contra o estado do texto original**: a edição não pode **regredir** (e não é obrigada a consertar o que já vinha marcado do narrador).

Falha em qualquer uma → **1 retentativa** com reforço (listando os trechos perdidos e/ou cobrando o conjunto numérico). Se persistir, a edição é **DESCARTADA** e a narrativa original do narrador prevalece, com `edicao_descartada: true` e `motivo_descarte` em `edicao_flags`.

> **A garantia que isso compra:** o editor **pode não melhorar** o texto — pode ser descartado e não entregar ganho nenhum. O que ele não pode, em hipótese alguma, é **piorá-lo**. Toda propriedade de honestidade conquistada da v1.1.1 à v1.5.0 sobrevive ao estágio novo por construção, não por confiança no modelo.

**Persistência (§4):** `narrativa` passa a ser o texto **final** (editado); `narrativa_bruta` guarda a saída do narrador para auditoria; `metricas_fluencia` passa a ser calculada sobre o texto final; `edicao_flags` carrega o resultado das checagens. O render de terminal exibe uma linha de status da edição (aplicada / descartada com motivo e trechos perdidos).

### [E] Render
1. `resultado/<slug>.json` — objeto completo: 3 buckets + metadados por nível e globais.
2. Terminal — por bucket: título, `n_validas/alvo` (com decomposição por nível quando houver nível degradado), filtro aplicado, temas com frequência relativa ("mencionado em ~14 de 50 reviews"), observação geral. Avisos de modo reduzido/degradado sempre visíveis e concretos ("análise negativa baseada em apenas 7 de 50 reviews-alvo — interprete com cautela").
3. Rodapé: contagem total de reviews observada, para distinguir "bucket vazio porque ninguém odeia" de "bucket vazio porque ninguém assistiu".
4. **(v1.4.0)** Header do grupo ganha `· ~X% das notas` quando há distribuição — **formato e estilo idênticos nos três grupos** (§0: a assimetria vem do dado, não da apresentação). O disclaimer da seção tema-a-tema tem duas variantes, escolhidas pela presença do dado (constantes `DISCLAIMER_*` em `render.py`, mantidas em sincronia com o frontend):
   - **sem** distribuição: *"grupos de 50 · 20 · 30 reviews são cotas de coleta — não a proporção real das opiniões"*
   - **com** distribuição: *"análise em profundidade igual por grupo (50·20·30 reviews); o peso real de cada faixa está indicado em cada grupo"*

   O frontend (`frontend/`) aplica exatamente o mesmo tratamento e **tolera JSONs sem `distribuicao`** (filmes antigos/fallback) sem quebrar: omite os shares e usa o disclaimer antigo. Ordem visual dos grupos permanece negativas → medianas → positivas em qualquer caso — **a ordem não é reordenada por peso**; quem muda de ordem é só a prosa do MOVIMENTO 3.

---

## 4. Metadados obrigatórios no output

Por nível: `n_validas`, `n_brutas`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_descartadas_truncamento`, `paginas_buscadas`.
Por bucket: agregados dos níveis + `modo` (completo/reduzido/sem_analise) + **(v1.1.2)** `idioma_invalido`, `escopo_suspeito`.
Por tema: **(v1.1.2)** `aspas_removidas`, além de `mencoes_clampadas`/`mencoes_valor_original` (v1.1.1).
Globais: `slug`, `data_coleta`, `origem` (cache/rede por página), versão da spec, **(v1.1.4)** `reviews_url`, **(v1.2.0)** `narrativa` + `narrativa_flags` (só quando `--tom narrativo|ambos`), **(v1.3.0)** `ficha` (objeto TMDB ou `null` — §3a), **(v1.3.1)** `consensos_usados` (lista de `{propriedade, grupos_de_origem, temas_de_origem}` do MOVIMENTO 2 — só quando `--tom narrativo|ambos`) + `narrativa_flags.consenso_suspeito`, **(v1.4.0)** `distribuicao` (bloco do histograma ou `null` — §3[G]) + `narrativa_flags.peso_nao_ancorado`, **(v1.4.1)** `quantificadores_usados` (lista de `{quantificador, tema}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.vocabulario_peso_suspeito`, **(v1.5.0)** `marcadores_perspectiva` (lista de `{grupo, trecho}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.perspectiva_nao_marcada`, `metricas_fluencia` (`{n_frases, media_palavras, cv_comprimento, frase_mais_curta, aberturas_repetidas, verbos_reporte, adverbios_mente}` — só quando `--tom narrativo|ambos`), **(v1.6.0)** `narrativa_bruta` (saída do narrador antes da edição, para auditoria) + `edicao_flags` (`{edicao_descartada, motivo_descarte, protegidos_perdidos, numeros_alterados, houve_retentativa, falhou, n_protegidos}` — só quando `--tom narrativo|ambos` e sem `--no-edicao`). **A flag `narrativa_flags.fluencia_baixa` foi REMOVIDA na v1.6.0** (ver §D2, "Telemetria de fluência"). Na ficha: **(v1.6.0)** `diretor_transliterado` (bool), **(v1.7.0)** `ano_fonte` (`"slug" | "letterboxd" | "argumento"`). Globais **(v1.7.0)**: `ficha_indisponivel` (`"ano_desconhecido"` — presente só quando a ficha não foi buscada por falta de ano confiável, §3[F]) e `ficha_descartada` (`{motivo, esperado, recebido}` — presente só quando o TMDB resolveu para um filme de ano divergente e a ficha inteira foi rejeitada, §3[F]); ambos ausentes do JSON no caminho normal (ficha resolvida com sucesso ou `--no-ficha`).
Por bucket: **(v1.4.0)** `share_real` (percentual inteiro), **omitido** quando não há distribuição.

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
- **v1.6.1** (2026-07-25): conclui a Tarefa 10 da v1.6.0 (regeneração, bloqueada por cota naquela sessão) e corrige a pendência registrada como "decisão deixada em aberto" — a correção 5.2 do validador de marcadores.
  - **A correção 5.2, revisitada.** A v1.6.0 já tinha corrigido dois defeitos do validador de `marcadores_perspectiva` (§D2): bastar UM marcador bem posicionado por grupo (5.1), e normalizar caixa/acento/demonstrativo na comparação entre o `trecho` declarado e o texto (5.2 original). Mas o caso real que motivou 5.2 — `cidade-de-deus`, narrador declarou *"Para esse grupo, muitos reconhecem…"* e escreveu *"Muitos neste grupo reconhecem…"* — **sobreviveu** à normalização: a diferença é de ORDEM DAS PALAVRAS, não de grafia, e nenhuma normalização de caixa/acento fecha isso. Comparação difusa com limiar foi cogitada e **descartada de novo** (um limiar é uma linha arbitrária).
  - **A correção pela raiz muda O QUE se verifica, não COMO se compara.** `_marcadores_validos` deixou de comparar o `trecho` declarado contra o texto. Em vez disso, escaneia o MOVIMENTO de cada grupo que exige marcação (`_span_de_movimento`: da âncora do grupo — rótulo de peso/percentual — até a âncora do próximo grupo, ou o fim do texto) em busca de qualquer expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`) — a MESMA constante que `montar_protegidos` (§E2) já usava, unificada num só lugar. Para `marcacao_perspectiva == "antecipada"`, a exigência de posição (mesma frase da âncora ou a seguinte) passa a valer sobre QUALQUER ocorrência encontrada no movimento, não sobre o `trecho` declarado. `marcadores_perspectiva` (a declaração do LLM) vira **telemetria pura** — persistida e exibida como sempre, mas não mais fonte da validação. Confirmado sobre o `cidade-de-deus` PUBLICADO (dado real, não sintético): o validador agora aceita tanto a declaração original quanto uma lista vazia — o que importa é que o texto realmente contém "neste grupo" e "Para eles" nos movimentos certos.
  - **`_normalizar_trecho`/`_trecho_aparece` (v1.6.0) foram REMOVIDAS** — a normalização de caixa/acento/demonstrativo deixou de ser necessária porque a checagem não compara mais string contra string.
  - **Regeneração (Tarefa 2/3 desta sessão):** ver bloco abaixo, dentro do changelog da v1.6.0, para o resultado exato (filmes concluídos, chamadas gastas, e o que ficou pendente se a cota ou uma chave inválida interromperam a sessão).
- **v1.6.0** (2026-07-25): **separação de responsabilidades** — o narrador volta a responder só por verdade, e um estágio novo (**editor [E2]**) assume ritmo e leitura. Fecha, junto, quatro pendentes acumulados. Nenhum parâmetro congelado de §2 mudou (a config de LLM da prosa é adição, não alteração da síntese).
  - **O diagnóstico acumulado que motiva a versão** (duas sessões, `DIAGNOSTICO_FLUENCIA.md` e `DIAGNOSTICO_FLUENCIA_V2.md`):
    **(a) O few-shot da v1.5.0 usava dados de um filme do catálogo.** O `the-invite` copiou **58 8-gramas** do exemplo (medidos com as construções mandatórias mascaradas), enquanto `cure` e `cidade-de-deus` — sem nada a copiar — ficaram em **0**. A "melhora" daquele filme na v1.5.0 era **artefato de cópia**, não transferência de estilo. Corrigido na sessão de diagnóstico (exemplo passou a ser de filme fictício); registrado aqui porque invalidou a leitura original da v1.5.0.
    **(b) As regras de ritmo no prompt do narrador não transferiram** para os outros dois filmes, e pioraram ambos (períodos emendados, um trecho agramatical no `cure`, "muitos" como sujeito repetido no `cidade-de-deus`).
    **(c) As métricas de fluência não acompanham qualidade.** No `cure`, o texto qualitativamente MELHOR pontuou PIOR em `cv_comprimento` (0.35 → 0.28) e em `verbos_reporte` (3 → 6). Fiscalizar estilo por limiar empurra o modelo a degradar a prosa para satisfazer um número.
    **(d) A configuração de produção gerou uma frase agramatical publicada** — `thinking_budget=0` no `cure`: *"Muitos para eles, há uma falta de tensão ou mistério…"*.
    **Conclusão:** acumular regras num único prompt falhou. A correção não é mais uma regra — é separar as duas responsabilidades em dois estágios, cada um com uma função e com fronteiras estruturais.
  - **(1) Config de produção da PROSA** (`config.py`, §2.1): `thinking_budget=4096` **FIXO** e `max_output_tokens=16000` para narrador e editor, revertendo o `thinking_budget=0` da v1.2.x. Base empírica: com thinking DINÂMICO sob teto de 8000, o raciocínio consumiu até 7676 tokens (96% do orçamento) e truncou 1 chamada em CADA célula testada; com budget FIXO e teto de 16000, **4/4 chamadas terminaram em STOP**. O problema nunca foi "thinking", foi thinking **sem teto** competindo com a resposta pelo mesmo orçamento. A **síntese por bucket (§D) não muda** — é extração estruturada, e nada no diagnóstico apontou problema lá.
  - **(2) Narrador podado** (§D2): saíram todas as regras de RITMO e REGISTRO da v1.5.0 e o par few-shot. Ficaram intactas as invariantes de honestidade — três movimentos, anti-spoiler e risco aceito, critérios do MOVIMENTO 2 + `consensos_usados`, rótulos de peso com percentual e vocabulário "das notas", quantificadores pré-computados + `quantificadores_usados`, marcação de perspectiva + `marcadores_perspectiva`, escopo por grupo, sem aspas, pt-BR, JSON puro. No lugar das regras de estilo, uma nota curta avisando que existe um estágio de edição depois e que ele deve escrever de forma clara e **gramaticalmente correta**.
  - **(3) Estágio [E2] — editor** (§E2, NOVO): 1 chamada LLM por filme, após o narrador. Recebe **exclusivamente** o texto validado e a lista de **trechos protegidos** — não recebe buckets, reviews nem ficha. A garantia anti-invenção é **estrutural**: o que não está na entrada, o editor não tem como saber. A lista de protegidos é montada **em código** a partir do que o narrador já declarou (rótulos de peso com percentual, quantificadores declarados, trechos de marcadores, todo token com dígito), incluindo só o que realmente ocorre no texto e na forma **como aparece** (o narrador capitaliza no início de frase). O prompt traz o par few-shot **movido** da v1.5.0, e uma regra de **gramática obrigatória**: corrigir período quebrado é a única reescrita estrutural que o editor tem obrigação de fazer.
  - **(4) Verificação mecânica da edição** (§E2): **(0, v1.7.2) checagem ESTRUTURAL, aplicada ANTES das demais** — rejeita se o texto começar com `{`/`[`, contiver cerca de código (```), tiver campo estilo JSON nas primeiras linhas (`"text":`, `text:`, `"narrativa":`), ou tiver chaves desbalanceadas (`_formato_invalido`); sem essa checagem, um invólucro `{ text: "..." }` passa pelas checagens (a)-(c) porque elas rodam sobre substring e continuam achando protegidos/números DENTRO do invólucro — foi exatamente o defeito real do `cidade-de-deus` sob a v1.7.1. (a) todo trecho protegido aparece **literalmente** (com a exceção de capitalização inicial, v1.7.1); (b) o multiconjunto de tokens numéricos é **idêntico** ao do original (segunda rede — pega sobretudo número inventado); (c) as validações de honestidade do §D2 são **reexecutadas** e nenhuma pode **regredir** em relação ao texto original. Falha em qualquer uma → 1 retentativa com reforço; se persistir, a edição é **DESCARTADA** e a narrativa do narrador prevalece (`edicao_descartada: true`, `motivo_descarte: "formato_invalido"` no caso da checagem estrutural). **A garantia:** o editor pode não melhorar o texto, mas não pode piorá-lo — toda propriedade conquistada da v1.1.1 à v1.5.0 sobrevive por construção, não por confiança no modelo. Persistidos `narrativa` (final), `narrativa_bruta` (auditoria) e `edicao_flags`.
  - **(5) Dois bugs do validador de marcadores** (§D2): **(5.1)** "antecipada" exigia que **TODOS** os marcadores declarados de um grupo respeitassem a posição — mas o narrador legitimamente declara mais de um ao elaborar o grupo, e foi assim que o `the-invite` disparou `perspectiva_nao_marcada` com os **dois** marcadores válidos em conteúdo. Passou a bastar **PELO MENOS UM** bem posicionado. **(5.2)** a comparação do trecho declarado passou a ser **normalizada** (minúsculas, sem acentos, série `esse/este` equivalente), com os demonstrativos mapeados **antes** da remoção de acento para não confundir "esta" (demonstrativo) com "está" (verbo). **Limitação registrada:** a normalização não cobre **reordenação** — no caso concreto do `cidade-de-deus` ("Para esse grupo, muitos reconhecem…" declarado vs. "Muitos neste grupo reconhecem…" escrito, similaridade 0.92), o falso positivo **persiste**; fechá-lo exigiria comparação difusa com limiar, o que enfraqueceria a garantia de que o marcador declarado é o que está no texto. Decisão deixada em aberto.
  - **(6) Métricas de fluência viram DIAGNÓSTICO PURO** (§D2): removidos os gatilhos automáticos de retentativa, o reforço `_REFORCO_FLUENCIA` e a flag `fluencia_baixa`. O cálculo e a persistência de `metricas_fluencia` continuam, com o mesmo estatuto de `consensos_usados` — material de revisão humana. Motivo em (c) acima: as métricas medem **dispersão**, não legibilidade.
  - **(7) Granularidade do rótulo de peso** (§D2): faixa nova `< 5% → "uma fração mínima"`. Antes, 8% e 1% recebiam ambos "uma pequena minoria", achatando uma diferença de **oito vezes** — observado em `cidade-de-deus` (91/8/1). Demais faixas e a convenção de desempate (sempre o rótulo mais fraco) inalteradas.
  - **(7b) Timeout nas chamadas LLM** (`LLM_TIMEOUT_MS = 180_000`, `config.py`): o SDK do Gemini bloqueia **indefinidamente** sem timeout explícito. Observado ao vivo durante a regeneração desta versão — um processo ficou **67 minutos** parado, 0% de CPU, dormindo num socket, sem voltar nem falhar (era o retry interno do SDK batendo em 429 sucessivos). Um timeout converte "trava para sempre" em erro que o chamador vê. 180s cobre com folga o pior caso medido (~110s numa chamada com thinking).
  - **PENDÊNCIA DESTA VERSÃO — as 3 narrativas NÃO foram regeneradas.** O código, a SPEC e os testes da v1.6.0 estão completos, mas a regeneração ao vivo esbarrou na **cota diária do free tier** do `gemini-2.5-flash` (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `limit: 20`), esgotada pelas sessões de diagnóstico do mesmo dia. Seis tentativas com backoff ao longo de 10 minutos devolveram 429 — não é janela curta, é o teto diário. **Consequência:** `resultado/*.json` e `frontend/js/data.js` seguem com as narrativas da **v1.5.0** (portanto sem `narrativa_bruta`/`edicao_flags`, com o rótulo antigo "uma pequena minoria" para 1%/3%, e com o diretor do `cure` ainda em `"黒沢清"`). O caminho foi validado ponta a ponta com LLM mockado sobre os dados reais dos três filmes (editor identidade ACEITO, editor que infla número DESCARTADO em 3/3). **Para concluir:** com cota disponível, `--slug <slug> --reuse-synthesis --tom narrativo --offline` nos três filmes (6 chamadas Gemini) + `python frontend/build_data.py`. O cache TMDB do `cure` foi propositalmente invalidado para que a correção do diretor seja aplicada na próxima execução (custa 3 requisições TMDB, só nesse filme).
  - **(8) Diretor em escrita latina** (§3[F]): o TMDB devolve o nome no alfabeto nativo quando pt-BR não tem tradução — `cure` publicou `"黒沢清"` na narrativa. Quando o nome pt-BR não é latino, o `credits` de `en-US` é consultado e a transliteração usada, com `diretor_transliterado: true` na ficha. No máximo 1 requisição extra, só para filmes nessa condição, reaproveitando a resposta `en-US` quando o fallback de sinopse já a buscou.
- **v1.5.0** (2026-07-25): fluência da narrativa (ritmo/registro) + marcação de perspectiva — a primeira mudança do §D2 motivada por QUALIDADE de prosa, não por uma infidelidade factual. Nenhum parâmetro congelado (§2) mudou; nenhuma invariante de honestidade das versões anteriores foi afrouxada.
  - **Diagnóstico (registrado por extenso na SPEC, §D2):** as narrativas entregues até a v1.4.1 são factualmente corretas mas soam mecânicas — forma sintática repetida (rótulo de peso + verbo de reporte + complemento, três vezes seguidas), comprimento de frase quase constante (25-35 palavras), densidade alta de verbos de reporte e nominalizações no lugar de verbos. **Causa provável:** o acúmulo de invariantes de honestidade das versões anteriores (peso ancorado, quantificador pré-computado, escopo por grupo, anti-spoiler, vocabulário "das notas") levou o modelo à ÚNICA forma sintática que satisfaz todas simultaneamente — relatar, com um verbo, o que cada grupo diz. **A correção:** prescrever ritmo, registro e marcação de perspectiva com a mesma precisão de código com que já se prescrevem os números, sem tocar em nenhuma regra de honestidade existente.
  - **(a) Regras de RITMO** (§D2, prompt): variação de comprimento de período (30-50 palavras alternadas com 3-10), pelo menos uma frase curta obrigatória, proibição de três períodos consecutivos de comprimento semelhante, proibição de repetir a estrutura de abertura entre períodos consecutivos, liberdade de posição para o rótulo de peso (não mais preso à abertura), conectivos de fala. Regras compartilhadas — presentes nas DUAS variantes da regra (c), pois não dependem do `share_real`.
  - **(b) Regras de REGISTRO** (§D2, prompt): descrever o filme diretamente após estabelecer quem fala (em vez de reintroduzir o sujeito a cada frase); verbos de reporte (elogia/destaca/aponta/relata/considera/classifica/menciona/ressalta/reconhece/expressa/descreve) limitados a 1 por movimento; preferência por verbos sobre nominalizações; advérbios intensificadores em -mente limitados a 1 em toda a narrativa; registro de "alguém contando de um filme para um amigo" — sem gíria, emoji, interpelação direta ou hipérbole. Também compartilhadas entre as duas variantes.
  - **(c) MARCAÇÃO DE PERSPECTIVA (regra nova, pedida pelo usuário) — só existe COM distribuição.** Motivação: ao remover os verbos de reporte (b), a fala de um grupo minoritário pode soar como fato do narrador, porque chega depois de o texto já ter estabelecido a leitura dominante. Pré-computação em CÓDIGO (`_marcacoes_por_bucket`/`_marcacao_perspectiva`, `synthesize.py`), por grupo, a partir do `share_real`: `dominante` = maior share do filme; `marcacao_perspectiva` = "nenhuma" se `share > dominante/3`, "simples" se `share <= dominante/3`, "antecipada" se `share <= dominante/10` (condição mais restritiva checada primeiro). Só existe com distribuição pelo MESMO motivo pelo qual a cota de coleta não pode alimentar esse cálculo (usar a cota apresentaria amostragem como prevalência, o defeito que a v1.2.1 proíbe). **Limiares são ponto de partida, calibráveis** — ao contrário das faixas de quantificador/peso, não vieram de evidência empírica prévia. O prompt exige ancoragem em todo trecho que fale de um grupo (o rótulo de peso já cumpre esse papel para o grupo dominante); `"simples"` exige um marcador em algum lugar do trecho ("para eles", "nessa leitura"); `"antecipada"` exige o marcador ANTES da primeira afirmação substantiva. Marcador de perspectiva é explicitamente distinguido de verbo de reporte no prompt (não conta para o limite da regra f) e é proibida carga depreciativa.
  - **(d) Telemetria `marcadores_perspectiva` (NOVO campo, mesmo padrão de `consensos_usados`/`quantificadores_usados`):** o narrador declara `{grupo, trecho}` por marcador usado. Validação pós-parsing (`_marcadores_validos`): grupo com marcação exigida precisa ter marcador declarado; trecho precisa aparecer literalmente no texto final; para "antecipada", o trecho precisa estar na MESMA frase da âncora do grupo (rótulo de peso/percentual) ou na frase IMEDIATAMENTE seguinte — aproximação por frase, já que os movimentos não têm marcação estrutural no texto final. Falha → 1 retentativa combinada (`_REFORCO_MARCADORES`); se persistir, `perspectiva_nao_marcada: true`. Lista vazia é válida por vacuidade quando nenhum grupo exige marcação (ex. 40/30/30 — nenhum passa nos limiares).
  - **(e) Exemplo few-shot ANTES/DEPOIS** embutido literalmente no prompt (só na variante COM distribuição, porque usa vocabulário de peso que a variante SEM distribuição proíbe) — descrito na SPEC como "o lever mais forte" contra a monotonia observada, por mostrar a forma desejada em vez de só descrevê-la. Marcado explicitamente como exemplo de ESTILO, não de conteúdo: os fatos e números de cada filme vêm sempre do relatório recebido.
  - **(f) Telemetria de fluência `metricas_fluencia` (NOVO campo, calculado em CÓDIGO, não pelo LLM):** `n_frases`, `media_palavras`, `cv_comprimento` (desvio padrão ÷ média de palavras por frase — mede variação, não comprimento em si), `frase_mais_curta`, `aberturas_repetidas` (frases consecutivas com a mesma primeira palavra), `verbos_reporte`, `adverbios_mente` (lista fechada de intensificadores, não todo advérbio em -mente). Gatilhos de 1 retentativa (`_REFORCO_FLUENCIA`), NUNCA bloqueiam: `cv_comprimento < 0.40` · nenhuma frase ≤10 palavras · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`. Se persistir, `fluencia_baixa: true`. Mesma ressalva de calibração da marcação de perspectiva: limiares são ponto de partida.
  - **(g) Render/CLI:** blocos compactos de `marcadores_perspectiva` (mesmo padrão do bloco de consensos) e resumo numérico de `metricas_fluencia`, exibidos no tom `narrativo`/`ambos`, após os blocos existentes; duas flags novas no aviso de terminal.
  - **(h) Emenda à invariante "só a regra (c) difere entre as variantes"** (v1.4.0, reafirmada com ressalva na v1.4.1): a marcação de perspectiva e o exemplo few-shot foram adicionados DENTRO da regra (c) COM distribuição — dependem do `share_real`, então pertencem a ela por construção. As regras de RITMO e REGISTRO, que não dependem de share, entraram nas partes compartilhadas do prompt, presentes e idênticas nas duas variantes. A invariante segue válida: o que muda é exatamente o que depende do dado.
- **v1.4.1** (2026-07-24): três correções pontuais no §D2, todas motivadas por defeitos reais na entrega da v1.4.0. Nenhum parâmetro congelado (§2) mudou; nenhuma etapa nova de pipeline.
  - **(a) Telemetria de quantificadores POR PAR — `quantificadores_usados` (NOVO campo na saída do narrador).** **A motivação é a reincidência:** é a **3ª ocorrência** do mesmo modo de falha (v1.2.2 por instrução → v1.2.3 por pré-computação → agora). Na v1.4.0, `the-invite-2026` usou "Quase todos" para `Atuações e química do elenco` (**20/30 = 67%**, rótulo pré-computado "a maioria"), e **a rede de segurança da v1.2.3 não pega**, porque ela é de **nível de bucket**: outro tema do mesmo grupo (`Direção e roteiro (geral)`, 25/30 = **83%**) dava lastro para "quase todos" existir em algum lugar do relatório. O buraco é estrutural — nenhuma checagem sobre a prosa sabe a QUAL tema um "quase todos" solto se refere. **A correção repete o padrão que funcionou no MOVIMENTO 2** (`consensos_usados`, v1.3.1): o narrador **declara** cada expressão de frequência junto do nome EXATO do tema de onde ela vem, e o CÓDIGO confere par a par contra o `rótulo_quantificador` pré-computado (`_quantificadores_validos`/`_forca_declarada`). Quantificador mais forte que o rótulo, ou tema inexistente → 1 retentativa combinada (`_REFORCO_QUANT_DECLARADO`); se persistir, alimenta a flag **já existente** `quantificador_suspeito`, agora com **duas** fontes (bucket + par), ambas ativas. Persistido no JSON e exibido no render como bloco compacto **com a conferência ao lado** (fração real → rótulo). Limitações deliberadas e documentadas: expressão fora da escala não é comparável (não flagga) e tema homônimo em dois grupos resolve pela força mais alta (não flagga na ambiguidade).
  - **(b) MOVIMENTO 2 pode ser OMITIDO — omissão autorizada explicitamente no prompt.** **O defeito:** na v1.4.0, o MOVIMENTO 2 do `the-invite-2026` trouxe juízos de qualidade **hedgeados** ("estilo visual eficaz", "abordagem arrojada"), violando o critério (a) de categoria — que a v1.3.1 escreveu justamente para esse filme. **Diagnóstico: pressão de preenchimento.** O filme tem poucos temas descritivos, o prompt pedia "3-5 frases" e só admitia encolher ("pode ser curto"); o modelo completou o espaço com avaliação suavizada, que é a violação disfarçada de descrição. **A correção não é mais uma proibição — é uma AUTORIZAÇÃO:** com menos de duas propriedades aprovadas nos três critérios, o movimento deve ser CURTO (1 frase) ou **AUSENTE**, passando direto ao MOVIMENTO 3. Omitir é o comportamento **correto**, não falha; preencher com juízo hedgeado é **pior** que não ter o movimento. `consensos_usados: []` é o resultado esperado nesse caso — e a validação da v1.3.1 **já** tratava lista vazia como válida por vacuidade (comportamento confirmado por teste, não alterado).
  - **(c) Invariante de vocabulário: NOTAS × REVIEWS.** **A distinção que faltava explicitar:** os rótulos de peso derivam do histograma de **notas** (todo mundo que avaliou); os temas derivam das **reviews com texto** (subconjunto). São populações diferentes e não compartilham denominador. Registrada em §D2 (tabela + regra) e em §3[G] (onde a distribuição é documentada), e reforçada dentro da regra (c) invertida do prompt: **OBRIGATÓRIO** "das notas", **PROIBIDO** "das reviews"/"dos espectadores"/"do público" ao expressar peso; frequência de tema continua em relação às reviews analisadas. **Checagem barata** (`_vocabulario_peso_ok`): rótulos inequívocos de peso → janela seguinte; qualquer percentual → janela anterior. A segunda passada existe porque **"a maioria" é ambígua** (também é rótulo de quantificador de tema, e "a maioria das reviews negativas analisadas" é a forma CORRETA da regra (d)) — ancorar no percentual desambigua sem flaggar prosa certa. Violação → 1 retentativa (`_REFORCO_VOCABULARIO_PESO`); se persistir, flag nova `vocabulario_peso_suspeito`.
  - **(d) Emenda ao "byte a byte" da v1.4.0:** a v1.4.0 registrava que `build_narrator_prompt(False)` devolvia o prompt da v1.3.1 byte a byte. As correções (a) e (b) vivem nas partes **compartilhadas** do prompt e valem nas duas variantes, então essa igualdade histórica deixou de existir. A invariante que a comparação A/B realmente precisa — **só a regra (c) difere entre as variantes** — continua de pé e verificada em teste.
- **v1.4.0** (2026-07-21): **distribuição real de notas** coletada e a regra de prevalência do §D2 **invertida** — a maior mudança desde a v1.
  - **A motivação (feedback de usuários reais, não hipótese):** filmes amplamente aclamados *soavam divididos*, porque os três grupos recebiam o mesmo peso textual e visual. `cidade-de-deus` tem **91%** das notas na faixa alta e era apresentado com a mesma proeminência dada ao grupo de **1%**. Infidelidade **por omissão**: cada frase verdadeira, o conjunto comunicando controvérsia onde havia consenso.
  - **A v1.2.1 previu esta correção.** Ela proibiu prevalência *porque o dado não existia*, e registrou em "Candidatos à próxima versão" que a correção de raiz seria coletar o histograma (inclusive o custo: 1 requisição cacheável — confirmado exato). A regra não foi afrouxada; o dado que faltava chegou.
  - **(a) Princípio norteador registrado (§0):** *neutralidade de TRATAMENTO, não de fato* — formato idêntico para os três grupos; a assimetria vem dos dados. Com duas invariantes intocadas: **share por faixa NÃO é nota média** (são três números que particionam a população; a proibição de score agregado segue escrita dentro da própria regra invertida) e **a minoria mantém o mesmo rigor analítico** (menos espaço na prosa, mesma seriedade; na interface, um grupo de 1% mantém seus 6 temas e barras).
  - **(b) Coleta (§3[G], `FASE_HISTOGRAMA.md`):** endpoint CSI `/csi/film/<slug>/rating-histogram/`, 1 requisição cacheada por filme. Três armadilhas reais tratadas — nível zerado troca `<a>` por `<span>` (buscar `a.barcolumn` perderia os zeros **em silêncio** e inflaria o total justo em filmes pequenos); o `_sr-only` da barra **abrevia** (`23.4K`) e é imprestável como fonte, o `title` é exato; singular/plural/"No" no `title`. Validação estrutural exige os 10 níveis canônicos, senão `None`.
  - **(c) Agregação em código:** `share_real` por bucket, percentual inteiro, cada bucket arredondado **independentemente** — a soma pode dar 99 ou 101 (`cure`: 3+17+79=99), aceito e documentado em vez de redistribuir o resto e tornar algum bucket menos fiel ao próprio dado. A interface nunca exibe a soma.
  - **(d) Cota 50/20/30 MANTIDA, com racional explícito:** cota é *amostragem estratificada* (profundidade igual por perspectiva — entender o que incomodou o grupo de 1% exige ~50 reviews lidas, não 1); peso é prevalência, agora exibida à parte. **Profundidade igual, peso informado.**
  - **(e) Regra (c) do §D2 em duas variantes, escolhidas pelo CÓDIGO:** sem distribuição, `build_narrator_prompt(False)` devolve o prompt da v1.3.1 **byte a byte** (verificado em teste) — o fallback é o texto anterior, não uma reescrita parecida. Com distribuição: ancoragem obrigatória no `rotulo_peso`, abertura do MOVIMENTO 3 pela perspectiva de maior peso, ênfase proporcional e respeito explícito à minoria. **Só a regra (c) difere** entre as variantes, para a comparação A/B isolar a mudança.
  - **(f) `rotulo_peso` pré-computado** (mesmo princípio da v1.2.3/v1.1.1): mapa determinístico com bordas sempre para o rótulo **mais fraco** (`70% → "a maioria"`, não "a grande maioria" — que começa de fato em 71%). Sempre entregue junto do percentual, que é o que impede o rótulo de virar retórica.
  - **(g) A rede de prevalência muda de sinal:** com distribuição, o detector da v1.2.1 é **desligado** (as palavras que ele caça passaram a ser exigidas) e quem cobre o eixo é a nova checagem de **ancoragem** (`peso_nao_ancorado`, 1 retentativa com `_REFORCO_ANCORAGEM`). Sem distribuição, o detector original continua ativo. **Não há flag de configuração — a presença do dado é o interruptor.**
  - **(h) Render e frontend:** `· ~X% das notas` no header, formato idêntico nos três; disclaimer com duas variantes; frontend tolera JSON sem `distribuicao`. Ordem visual dos grupos **não** é reordenada por peso — só a prosa do MOVIMENTO 3 abre pelo dominante.
  - **Resultado medido nas 3 demos:** ancoragem 3/3 filmes, abertura pelo grupo dominante 3/3, zero `peso_nao_ancorado`. Shares reais: `the-invite-2026` 3/18/79, `cure` 3/17/79, `cidade-de-deus` 1/8/91.
- **v1.3.1** (2026-07-20): regra do MOVIMENTO 2 reescrita (categoria/presença/não-contradição) + telemetria `consensos_usados` (§D2).
  - **O defeito real:** na primeira execução da narrativa em três movimentos (v1.3.0), o MOVIMENTO 2 de `the-invite-2026` afirmou "elenco com atuações marcantes" e "roteiro elogiado por sua inteligência" como fatos neutros de experiência — mas o grupo negativas tem literalmente os temas "Atuações e direção questionáveis" (~15/50) e "Humor e roteiro fracos/entediantes" (~27/50), uma contradição direta, não um consenso. **Diagnóstico:** erro de CATEGORIA — o narrador importou um juízo AVALIATIVO (qualidade de atuação/roteiro, que é sempre disputado) como se fosse uma propriedade DESCRITIVA (ritmo/tom/atmosfera, sobre a qual pode haver consenso factual mesmo com valência diferente). A regra da v1.3.0 pedia "características em que os grupos concordam factualmente" mas não distinguia essas duas categorias nem dava um exemplo do modo de falha.
  - **(a) Regra reescrita com três critérios obrigatórios** (§D2, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`): **(i) CRITÉRIO DE CATEGORIA** — só propriedades descritivas (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade); PROIBIDO qualquer juízo de qualidade, que pertence sempre ao MOVIMENTO 3. **(ii) CRITÉRIO DE PRESENÇA** — a propriedade precisa vir de temas de PELO MENOS DOIS grupos com o mesmo núcleo factual (valência pode divergir). **(iii) CRITÉRIO DE NÃO-CONTRADIÇÃO** — se qualquer grupo nega o núcleo factual (não só diverge na avaliação), a propriedade é desqualificada. O prompt inclui os dois exemplos pedidos: o POSITIVO (ritmo lento/tedioso vs lento/deliberado → consenso válido) e o NEGATIVO — o caso real das atuações do `the-invite-2026`, documentado por extenso como o modo de falha a evitar.
  - **(b) Telemetria `consensos_usados` (NOVO campo na saída do narrador):** o LLM agora declara, para cada propriedade usada no MOVIMENTO 2, `{propriedade, grupos_de_origem, temas_de_origem}` — grupos restritos a negativas/medianas/positivas, temas com o nome EXATO como aparece no relatório. É o artefato de revisão humana que substitui o exercício manual (recalcular frações e comparar com o texto) feito no relatório da v1.3.0 para achar o defeito do `the-invite-2026` — agora fica pronto em toda execução. Persistido no JSON do filme (campo global `consensos_usados`) e exibido no render de terminal (tom `narrativo`/`ambos`) como bloco compacto após a prosa.
  - **(c) Validação pós-parsing** (`_consensos_validos`, `synthesize.py`): confere que todo grupo citado é um dos três nomes válidos e existe no relatório, e que todo tema citado corresponde, por igualdade exata de string, a um tema real de algum dos grupos citados naquele item. Falha → 1 retentativa combinada com as demais validações de prosa (reforço `_REFORCO_CONSENSOS`); se persistir, aceita e sinaliza `consenso_suspeito: true` em `narrativa_flags` — telemetria visível, mesma política das demais flags do §D2. Lista vazia (`[]`) é válida — o MOVIMENTO 2 pode não ter nenhuma propriedade que passe nos três critérios.
  - **(d) Correção retroativa documentada em §3a:** durante a regeneração das narrativas da v1.3.0, a desambiguação por ano do TMDB (§3a) mostrou um bug real — escolher o primeiro resultado do ano certo, em vez de desempatar por popularidade, pegava o filme errado para "Cure" 1997 (um documentário obscuro em vez do filme de Kiyoshi Kurosawa). Corrigido antes da entrega da v1.3.0; texto de §3a atualizado nesta versão para refletir o comportamento real do código.
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

- ~~**Histograma de distribuição real de notas (torna prevalência legítima em vez de proibida).**~~ **ENTREGUE na v1.4.0** (§0, §3[G], §D2) — o texto original do candidato fica abaixo como registro de que a v1.2.1 já previa esta correção de raiz, inclusive o custo estimado (1 requisição extra, cacheável), que se confirmou exato.
- *(candidato original, cumprido)* **Histograma de distribuição real de notas.** A v1.2.1 **proíbe** afirmações de prevalência entre grupos porque as cotas de coleta (50/20/30) não são a distribuição da recepção. A correção de raiz — em vez da proibição — é **coletar o histograma de notas da página do filme no Letterboxd** (a barra de distribuição de ratings; **1 requisição extra** por filme, cacheável). Com a distribuição real disponível, o narrador **e** o render estruturado poderiam fazer afirmações de prevalência **legítimas e ancoradas nos dados** ("a maior parte das avaliações fica na faixa alta"), e o `--tom` narrativo deixaria de ter uma invariante puramente restritiva. Enquanto o histograma não existe no pipeline, a proibição da v1.2.1 é o comportamento correto. *(Também destrava a distinção "bucket vazio porque ninguém odiou" vs "porque ninguém assistiu" com número real, não só o total observado do rodapé.)*
- **Validador pós-parsing por tema (não só o quantificador mais forte).** A v1.2.3 pré-computa o rótulo (código como autoridade) e adiciona uma rede de segurança em nível de BUCKET restrita a "quase todos"/"praticamente todos" — deliberadamente não cobre uso indevido dos demais rótulos (ex.: "poucos" aplicado a um tema de 40%). Candidato futuro: correspondência por `tema` no texto da narrativa, recalcular a fração daquele tema específico e conferir contra QUALQUER rótulo usado, não só o mais forte — mesma mecânica de retentativa + flag das demais validações de prosa. Só vale a pena se o padrão de uso indevido de rótulos mais fracos aparecer na prática; nenhuma evidência disso até a v1.2.3.
- **Cache em `cache/`/`.cache/` na raiz** (desacoplar de `resultado/`, ver §3[B]) e **backfill barato de cota** (§3[C'].5) — candidatos herdados da v1.1.x.