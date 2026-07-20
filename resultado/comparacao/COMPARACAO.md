# Espectro 24 — Comparação de modelos Gemini (oppenheimer-2023)

Gerado em 2026-07-19T07:38:59.980167+00:00. Corpus 100% do cache (`resultado/cache/`), zero requisições ao Letterboxd. Prompt §D byte-idêntico entre modelos — a única variável é o modelo.

**Chamadas Gemini gastas nesta sessão: 5/8**

## Modelos pulados

- **gemini-2.0-flash**: sondagem de 1 bucket falhou: modelo gemini-2.0-flash falhou de novo após backoff de 60s: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash\nPlease retry in 59.985624873s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.0-flash'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '59s'}]}} — confirmação de que a alocação zero da sessão anterior persiste após o reset.

## Métricas por modelo × bucket

| Modelo | Bucket | json_valido | houve_retentativa | houve_backoff | finish_reason | n_temas | soma_mencoes | n_clampados | latência (s) |
|---|---|---|---|---|---|---|---|---|---|
| gemini-2.5-flash-lite | negativas | True | False | False | FinishReason.STOP | 6 | 115 | 0 | 5.39 |
| gemini-2.5-flash-lite | medianas | True | False | False | FinishReason.STOP | 6 | 45 | 0 | 5.06 |
| gemini-2.5-flash-lite | positivas | True | False | False | FinishReason.STOP | 6 | 89 | 0 | 3.77 |
| gemini-2.5-flash | negativas | True | False | False | FinishReason.STOP | 6 | 67 | 0 | 6.84 |
| gemini-2.5-flash | medianas | True | False | False | FinishReason.STOP | 6 | 42 | 0 | 4.48 |
| gemini-2.5-flash | positivas | True | False | False | FinishReason.STOP | 6 | 80 | 0 | 5.43 |

## Temas lado a lado (nome + frequência, por bucket)

Apenas dados organizados para inspeção humana — nenhum veredito de qualidade/coerência/spoiler é feito por este script.

### Bucket: negativas

| # | gemini-2.5-flash-lite | gemini-2.5-flash |
|---|---|---|
| 1 | Pacing and Structure (~30) | Visão eurocêntrica e falta de representação das vítimas (~15) |
| 2 | Portrayal of Historical Context and Victims (~25) | Ritmo e edição caóticos/acelerados (~15) |
| 3 | Character Development (especially women) (~20) | Personagens femininas fracas ou estereotipadas (~13) |
| 4 | Dialogue and Exposition (~15) | Sonoplastia e trilha sonora excessivas/distrativas (~9) |
| 5 | Sound and Music (~15) | Roteiro confuso e superficial (~8) |
| 6 | Visuals and Cinematography (~10) | Filme pretensioso ou autoindulgente de Nolan (~7) |

### Bucket: medianas

| # | gemini-2.5-flash-lite | gemini-2.5-flash |
|---|---|---|
| 1 | Dificuldades de ritmo e duração (~10) | Ritmo e duração do filme (~10) |
| 2 | Direção e estilo de Nolan (~9) | Atuações e elenco (~8) |
| 3 | Atuações e elenco (~7) | Estilo e megalomania de Nolan (~7) |
| 4 | Roteiro e diálogos (~7) | Aspectos técnicos (fotografia, som, trilha sonora) (~7) |
| 5 | Aspectos visuais e sonoros (~6) | Roteiro e desenvolvimento de personagens (~6) |
| 6 | Profundidade temática e emocional (~6) | Representação histórica e impacto das bombas (~4) |

### Bucket: positivas

| # | gemini-2.5-flash-lite | gemini-2.5-flash |
|---|---|---|
| 1 | Atuações (~20) | Atuações e elenco (~21) |
| 2 | Som e Trilha Sonora (~18) | Imersão e impacto sensorial (som e trilha sonora) (~17) |
| 3 | Estrutura e Narrativa (~14) | Direção e complexidade narrativa de Nolan (~15) |
| 4 | Cinematografia e Visual (~13) | Exploração temática e profundidade moral (~12) |
| 5 | Temas e Reflexões (~13) | Qualidade cinematográfica e visual (~9) |
| 6 | Direção de Christopher Nolan (~11) | Impacto emocional e psicológico (~6) |


## Checagem factual de idioma por bucket (não é veredito de qualidade)

Contagem mecânica de stopwords pt-BR vs. inglês nos nomes dos temas de cada bucket — checagem de FORMATO (§D.4 da spec exige saída sempre em pt-BR), não avaliação de conteúdo/coerência/spoiler.

| Modelo | Bucket | Idioma detectado |
|---|---|---|
| gemini-2.5-flash-lite | negativas | en ⚠️ |
| gemini-2.5-flash-lite | medianas | pt-BR |
| gemini-2.5-flash-lite | positivas | pt-BR |
| gemini-2.5-flash | negativas | pt-BR |
| gemini-2.5-flash | medianas | pt-BR |
| gemini-2.5-flash | positivas | pt-BR |
