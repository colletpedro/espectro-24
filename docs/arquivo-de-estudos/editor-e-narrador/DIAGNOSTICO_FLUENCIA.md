# Espectro 24 — Diagnóstico de fluência: matriz modelo × thinking

Gerado em 2026-07-25T18:39:04.998635+00:00. **Chamadas Gemini: 16/16.** Zero requisições ao Letterboxd e ao TMDB (a síntese vem dos JSONs de produção já gerados, no mesmo espírito de `--reuse-synthesis`).

**Esta é uma sessão de DIAGNÓSTICO, não um bump de versão.** `SPEC_VERSION` permanece em 1.5.0; os JSONs de produção e o `frontend/js/data.js` não foram tocados. A única mudança permanente é a substituição do few-shot (abaixo), que corrige um defeito metodológico real.

> **Nenhum veredito de qualidade literária é emitido aqui.** Este documento reporta números e textos; a avaliação da prosa é humana e fica fora desta sessão.

## 1. O problema, e o defeito metodológico que ele escondia

A v1.5.0 adicionou regras de ritmo/registro e um par few-shot ANTES/DEPOIS ao §D2. O resultado foi desigual: o `the-invite` aparentou seguir o estilo novo, enquanto `cure` e `cidade-de-deus` não transferiram e pioraram em pontos (períodos emendados, um trecho agramatical no `cure`, "muitos" como sujeito repetido no `cidade-de-deus`).

**A causa da assimetria não era o modelo — era o exemplo.** O par ANTES/DEPOIS da v1.5.0 foi escrito com os **dados reais do `the-invite`** (79%/18%/3%, o nome da diretora, o apartamento único). Medindo sobreposição de 8-gramas de palavras entre cada narrativa da v1.5.0 e aquele few-shot — **com as construções mandatórias mascaradas** (rótulo de peso, marcadores de perspectiva, enquadramento "quem gostou": aparecem por obrigação de regra, não por cópia):

| Filme (narrativa v1.5.0) | 8-gramas compartilhados com o few-shot ANTIGO |
|---|---|
| `the-invite-2026` | **58** |
| `cure` | **0** |
| `cidade-de-deus` | **0** |

O `the-invite` **copiou o exemplo**, não aprendeu a forma dele. Os outros dois, sem nada a copiar, não transferiram estilo nenhum. Um few-shot construído sobre um filme do catálogo contamina a avaliação daquele filme e só daquele — e por isso **não media nada**. Sem substituí-lo, a matriz modelo × thinking mediria o efeito da cópia, não o da condição de execução.

### Few-shot descontaminado (mudança permanente desta sessão)

O par foi reescrito com um **filme fictício e números inventados** (74/19/7), e o prompt agora declara explicitamente que copiar qualquer fato, adjetivo ou número do exemplo viola a regra de FIDELIDADE. Dois micro-exemplos que também carregavam dados do `the-invite` foram neutralizados junto — a regra (e) de REGISTRO (`"~79%"` + "sem sair de um apartamento", que é a ambientação real daquele filme) e a ilustração da ANCORAGEM na marcação de perspectiva. Um teste novo (`test_few_shot_nao_usa_dados_de_nenhum_filme_do_catalogo`) impede a reintrodução de nomes ou shares do catálogo.

**Validação do detector de contaminação** (contra verdade conhecida, antes de gastar qualquer chamada da matriz): `the-invite` v1.5.0 × few-shot ANTIGO → 58 n-gramas (contaminação real detectada); `the-invite` v1.5.0 × few-shot NOVO → 0; `cure` × few-shot ANTIGO → 0; few-shot NOVO contra si mesmo → 73 (o detector dispara quando deve).

## 2. Cobertura da matriz — metade NÃO foi obtida

**As 4 células de `gemini-2.5-pro` (combinações C e D) falharam — o eixo MODELO da matriz não pôde ser testado.** Não é rate limit transitório: a API responde `RESOURCE_EXHAUSTED` com **`limit: 0`** para `gemini-2.5-pro`, tanto em requisições quanto em tokens de entrada, nas cotas por minuto **e** por dia. Ou seja, a chave/plano em uso não tem acesso ao modelo — repetir a tentativa não muda o resultado. Cada célula gastou 2 chamadas (tentativa + 1 backoff de 60s conforme o protocolo) antes de ser pulada.

| Comb. | Filme | Motivo |
|---|---|---|
| C | `the-invite-2026` | 429 RESOURCE_EXHAUSTED — `limit: 0` para gemini-2.5-pro (sem acesso no plano) |
| C | `cure` | 429 RESOURCE_EXHAUSTED — `limit: 0` para gemini-2.5-pro (sem acesso no plano) |
| D | `the-invite-2026` | 429 RESOURCE_EXHAUSTED — `limit: 0` para gemini-2.5-pro (sem acesso no plano) |
| D | `cure` | orçamento de 16 chamadas esgotado (após os 429 das células anteriores) |

**Consequência para o diagnóstico:** a hipótese "o `gemini-2.5-flash` não tem capacidade de prosa suficiente" **permanece não testada**. O que esta sessão mede é exclusivamente o eixo THINKING, dentro do `gemini-2.5-flash` (A vs. B). Concluir qualquer coisa sobre modelo maior a partir daqui seria extrapolação sem dado.

## 3. Tabela-resumo — as combinações executadas

| Comb. | Modelo | Thinking | Filme | n_frases | media_pal | cv_compr | frase_curta | abert_rep | reporte | -mente | fluencia_baixa | retentativa | latência (s) | contaminação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | gemini-2.5-flash | off | `the-invite-2026` | 13 | 20.6 | **0.37** | **10** | 0 | 5 | 1 | True | True | 16.04 | False |
| A | gemini-2.5-flash | off | `cure` | 9 | 25.1 | **0.35** | **13** | 1 | 3 | 1 | True | True | 19.72 | False |
| B | gemini-2.5-flash | on | `the-invite-2026` | 14 | 18.5 | **0.37** | **8** | 1 | 3 | 1 | True | True | 110.63 | False |
| B | gemini-2.5-flash | on | `cure` | 12 | 18.6 | **0.4** | **8** | 1 | 2 | 0 | True | True | 61.68 | False |
| C | gemini-2.5-pro | off | `the-invite-2026` | — | — | — | — | — | — | — | PULADO — 429 `limit: 0` | — | — | — |
| C | gemini-2.5-pro | off | `cure` | — | — | — | — | — | — | — | PULADO — 429 `limit: 0` | — | — | — |
| D | gemini-2.5-pro | on | `the-invite-2026` | — | — | — | — | — | — | — | PULADO — 429 `limit: 0` | — | — | — |
| D | gemini-2.5-pro | on | `cure` | — | — | — | — | — | — | — | PULADO — orçamento esgotado | — | — | — |

Gatilhos de `fluencia_baixa` (§D2): `cv_comprimento < 0.40` · `frase_mais_curta > 10` · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`.

### Delta A → B (thinking off → on), o único eixo testado

| Filme | métrica | A (off) | B (on) | Δ |
|---|---|---|---|---|
| `the-invite-2026` | cv_comprimento | 0.37 | 0.37 | → +0.0 |
| `the-invite-2026` | frase_mais_curta | 10 | 8 | ↓ -2 |
| `the-invite-2026` | verbos_reporte | 5 | 3 | ↓ -2 |
| `the-invite-2026` | adverbios_mente | 1 | 1 | → +0 |
| `the-invite-2026` | aberturas_repetidas | 0 | 1 | ↑ +1 |
| `the-invite-2026` | media_palavras | 20.6 | 18.5 | ↓ -2.1 |
| `the-invite-2026` | n_frases | 13 | 14 | ↑ +1 |
| `the-invite-2026` | latência (s) | 16.04 | 110.63 | ↑ +94.6 |
| `cure` | cv_comprimento | 0.35 | 0.4 | ↑ +0.05 |
| `cure` | frase_mais_curta | 13 | 8 | ↓ -5 |
| `cure` | verbos_reporte | 3 | 2 | ↓ -1 |
| `cure` | adverbios_mente | 1 | 0 | ↓ -1 |
| `cure` | aberturas_repetidas | 1 | 1 | → +0 |
| `cure` | media_palavras | 25.1 | 18.6 | ↓ -6.5 |
| `cure` | n_frases | 9 | 12 | ↑ +3 |
| `cure` | latência (s) | 19.72 | 61.68 | ↑ +42.0 |

**Tokens de thinking efetivamente gastos** (prova de que o parâmetro fez efeito, e não só de que foi aceito):

| Comb. | Filme | thinking_tokens | output_tokens | max_output_tokens | finish_reason |
|---|---|---|---|---|---|
| A | `the-invite-2026` | None | 1093 | 3000 | FinishReason.STOP |
| A | `cure` | None | 970 | 3000 | FinishReason.STOP |
| B | `the-invite-2026` | 6916 | 693 | 8000 | FinishReason.STOP |
| B | `cure` | 7576 | 407 | 8000 | FinishReason.MAX_TOKENS |

O consumo de 5.1k-7.7k tokens de thinking **confirma retroativamente o diagnóstico da v1.2.x**: sob o teto de 3000 da configuração de produção, thinking sozinho estouraria o orçamento e cortaria o JSON no meio — exatamente o motivo de `thinking_budget=0` ter sido fixado.

**Mas 8000 também não bastou.** Detalhe por chamada (cada célula faz 1 chamada + retentativas do §D2):

| Comb. | Filme | # | finish_reason | json_válido | thinking_tok | output_tok |
|---|---|---|---|---|---|---|
| A | `the-invite-2026` | 1 | FinishReason.STOP | True | None | 859 |
| A | `the-invite-2026` | 2 | FinishReason.STOP | True | None | 1093 |
| A | `cure` | 1 | FinishReason.STOP | True | None | 927 |
| A | `cure` | 2 | FinishReason.STOP | True | None | 970 |
| B | `the-invite-2026` | 1 | FinishReason.MAX_TOKENS | False | 7676 | 307 |
| B | `the-invite-2026` | 2 | FinishReason.STOP | True | 6533 | 990 |
| B | `the-invite-2026` | 3 | FinishReason.STOP | True | 6916 | 693 |
| B | `cure` | 1 | FinishReason.STOP | True | 5153 | 932 |
| B | `cure` | 2 | FinishReason.MAX_TOKENS | False | 7576 | 407 |

Nas DUAS células com thinking, ao menos uma chamada morreu em `MAX_TOKENS` com JSON inválido — thinking chegou a **7676 tokens (96% do teto de 8000)**, deixando ~300 para a resposta. As consequências são operacionais, não estéticas:

- **B · `the-invite`**: a 1ª chamada foi truncada, gastando a retentativa-de-JSON do §D2; a célula precisou de **3 chamadas** em vez de 2.
- **B · `cure`**: foi a **retentativa de validação** que morreu truncada. Como `_uma_chamada` devolve `None` em JSON inválido, o pipeline descartou a correção e **manteve a resposta original** (degradação segura, por construção) — mas isso significa que a tentativa de corrigir `perspectiva_nao_marcada` foi perdida em silêncio, e a flag ficou marcada por truncamento, não por teimosia do modelo.

Consequência prática para quem for adotar thinking: o teto precisa ser dimensionado para **thinking + JSON completo** (~7.7k + ~1.1k observados ⇒ folga real a partir de ~12000), e o custo do thinking **cresce na retentativa** (o reforço alonga o prompt: 5153 → 7576 tokens no `cure`) — justamente quando o orçamento já está mais apertado.

## 4. Flags de honestidade sob cada condição

| Comb. | Filme | quantificador_suspeito | peso_nao_ancorado | vocabulario_peso_suspeito | escopo_suspeito | consenso_suspeito | perspectiva_nao_marcada | idioma_invalido | prevalencia_suspeita |
|---|---|---|---|---|---|---|---|---|---|
| A | `the-invite-2026` | False | False | False | False | False | False | False | False |
| A | `cure` | False | False | False | False | False | False | False | False |
| B | `the-invite-2026` | False | False | False | False | False | True | False | False |
| B | `cure` | False | False | False | False | False | True | False | False |

**Flags acionadas:**
- B · `the-invite-2026`: `perspectiva_nao_marcada`
- B · `cure`: `perspectiva_nao_marcada`

**Leitura honesta deste quadro — thinking NÃO saiu neutro.** As invariantes numéricas centrais (quantificador, ancoragem de peso, vocabulário "das notas", escopo, consensos, idioma) ficaram **limpas em todas as 4 células executadas** — nem thinking as degradou. Mas `perspectiva_nao_marcada` **apareceu só com thinking (B), nos dois filmes**, e estava ausente no baseline (A). Antes de atribuir isso ao raciocínio do modelo, vale a causa mecânica documentada acima: no `cure` a retentativa que corrigiria a marcação morreu em `MAX_TOKENS` e foi descartada. Ou seja, parte desse resultado é **efeito do teto de tokens**, não do thinking em si — e separar as duas coisas exige repetir B com um teto folgado (~12000), o que esta sessão não fez.

## 5. As narrativas, na íntegra

### Combinação A — gemini-2.5-flash · thinking off (baseline de produção)

#### `the-invite-2026`

- `n_palavras`: 272 · `max_output_tokens`: 3000 · `finish_reason`: FinishReason.STOP · latência: 16.04s · chamadas LLM: 2
- tokens — prompt: 7041, saída: 1093, thinking: None
- métricas: {"n_frases": 13, "media_palavras": 20.6, "cv_comprimento": 0.37, "frase_mais_curta": 10, "aberturas_repetidas": 0, "verbos_reporte": 5, "adverbios_mente": 1}
- `contaminacao_detectada`: **False**
- **houve retentativa** — flags que persistiram após ela: ['fluencia_baixa']

> Em 2026, a diretora Olivia Wilde traz a público O Convite, um drama com toques de comédia sobre o casamento de Joe e Angela, que, à beira do colapso, decide convidar os vizinhos misteriosos para um jantar que promete reviravoltas. O filme se desenrola em um cenário predominantemente íntimo, com a narrativa equilibrando momentos de riso com tensão crescente. Há uma progressão notável de tom, partindo de uma atmosfera mais cômica para explorar dilemas mais profundos dos relacionamentos. Sua abordagem da intimidade e das relações interpessoais é bastante explícita. A grande maioria das notas (~79%) elogia a direção e o roteiro por equilibrar comédia e drama, criando tensão e explorando temas complexos de relacionamento. Quase todos que gostaram destacam ainda o desempenho excepcional do elenco e a ótima química entre os atores. Para muitos, o filme consegue ser hilário e, ao mesmo tempo, profundamente triste ou tocante. Já uma minoria das notas (~18%) tem uma visão mais matizada. Para eles, o filme é divertido na primeira metade, mas muitos sentiram que a repetição das situações e a duração prolongada tornaram a experiência cansativa no final. Por esse motivo, as atuações são elogiadas, e a direção é vista como confiante, equilibrando os tons, mas a mudança de tom e o final dividem opiniões. Uma pequena minoria das notas (~3%) não se conecta à proposta do filme. Para eles, cerca de metade das reviews classificou o humor do filme como previsível e o roteiro como arrastado, tornando a experiência tediosa. Muitos veem os personagens como caricaturas e superficiais, com diálogos que parecem forçados ou sem profundidade, e consideram as atuações e a direção questionáveis.

Marcadores de perspectiva declarados:
- `medianas` — "Para eles, o filme é divertido na primeira metade, mas muitos sentiram que a repetição das situações e a duração prolongada tornaram a experiência cansativa no final."
- `negativas` — "Para eles, cerca de metade das reviews classificou o humor do filme como previsível e o roteiro como arrastado, tornando a experiência tediosa."

#### `cure`

- `n_palavras`: 230 · `max_output_tokens`: 3000 · `finish_reason`: FinishReason.STOP · latência: 19.72s · chamadas LLM: 2
- tokens — prompt: 7054, saída: 970, thinking: None
- métricas: {"n_frases": 9, "media_palavras": 25.1, "cv_comprimento": 0.35, "frase_mais_curta": 13, "aberturas_repetidas": 1, "verbos_reporte": 3, "adverbios_mente": 1}
- `contaminacao_detectada`: **False**
- **houve retentativa** — flags que persistiram após ela: ['fluencia_baixa']

> Em 1997, o diretor 黒沢清 apresentou A Cura, um suspense de crime e terror que mergulha na busca desesperada de um detetive por respostas, enquanto pessoas são encontradas mortas com uma estranha marca em x e ele tenta ligar os crimes a um rapaz misterioso. O filme se desenrola com um ritmo lento, construindo uma atmosfera densa e um tanto enigmática, que se inclina para o horror psicológico. Essa cadência e o tom perturbador são essenciais para a experiência, que se mantém ambígua, deixando muitas vezes o espectador sem respostas claras. 
> A grande maioria das notas (~79%) elogia a maestria do filme em criar uma atmosfera perturbadora e hipnótica, onde o pacing lento e deliberado intensifica o horror psicológico. Muitos destacam como o filme explora temas psicológicos e existenciais profundos, como a fragilidade da identidade e a natureza do mal, e alguns apreciam a ambiguidade e ausência de respostas, que convidam à reflexão. Já uma minoria das notas (~17%) reconhece as ideias intrigantes e a atmosfera eficaz, mas muitos veem um ritmo lento que leva à confusão narrativa. Para esse grupo, o filme peca na execução e apresenta um final que parece insatisfatório ou ambíguo. Para uma pequena minoria das notas (~3%), o filme é excessivamente lento e tedioso. Muitos para eles, há uma falta de tensão ou mistério e o enredo é repetitivo, com personagens desinteressantes que não cativam.

Marcadores de perspectiva declarados:
- `medianas` — "Para esse grupo"
- `negativas` — "Para uma pequena minoria das notas (~3%), o filme é excessivamente lento e tedioso. Muitos para eles"

### Combinação B — gemini-2.5-flash · thinking on

#### `the-invite-2026`

- `n_palavras`: 263 · `max_output_tokens`: 8000 · `finish_reason`: FinishReason.STOP · latência: 110.63s · chamadas LLM: 3
- tokens — prompt: 6925, saída: 693, thinking: 6916
- métricas: {"n_frases": 14, "media_palavras": 18.5, "cv_comprimento": 0.37, "frase_mais_curta": 8, "aberturas_repetidas": 1, "verbos_reporte": 3, "adverbios_mente": 1}
- `contaminacao_detectada`: **False**
- **houve retentativa** — flags que persistiram após ela: ['fluencia_baixa', 'perspectiva_nao_marcada', 'perspectiva_nao_marcada']

> Olivia Wilde dirige O Convite, um drama e comédia de 2026 que acompanha o casal Joe e Angela em um momento de crise. A premissa se desenrola quando eles convidam seus misteriosos vizinhos para um jantar, e a noite toma um rumo inesperado.
> >
> > A grande maioria das notas (~79%) abraça O Convite. O filme, para eles, possui uma direção e um roteiro que se destacam pela habilidade em equilibrar comédia e drama, criando tensão enquanto explora relações complexas. As atuações excepcionais do elenco e a ótima química entre os atores são um grande ponto. O humor é hilário e, ao mesmo tempo, profundamente tocante, com um equilíbrio perfeito entre os dois tons.
> Uma minoria das notas (~18%) também tem pontos positivos a considerar. O filme, para esse grupo, tem atuações fortes e uma direção confiante que capta a atmosfera íntima do apartamento. Só que muitos acharam que, embora divertido na primeira metade, o ritmo e a repetição das situações o tornaram cansativo no final. O roteiro é visto como inteligente, mas alguns viram as motivações e os temas como um tanto previsíveis ou superficiais, com uma mudança de tom para o drama final que dividiu opiniões.
> Já uma pequena minoria das notas (~3%) não foi conquistada pelo convite. Para eles, cerca de metade das reviews classifica o humor e o roteiro como fracos e entediantes, com piadas que não funcionam e a história se arrastando. Muitos também acharam os personagens superficiais e irritantes, com diálogos forçados. Nessa leitura, atuações e direção são questionáveis, e o foco excessivo na sexualidade parece constrangedor ou gratuito.

Marcadores de perspectiva declarados:
- `medianas` — "Para esse grupo"
- `negativas` — "Para eles"
- `negativas` — "Nessa leitura"

#### `cure`

- `n_palavras`: 227 · `max_output_tokens`: 8000 · `finish_reason`: FinishReason.MAX_TOKENS · latência: 61.68s · chamadas LLM: 2
- tokens — prompt: 7170, saída: 407, thinking: 7576
- métricas: {"n_frases": 12, "media_palavras": 18.6, "cv_comprimento": 0.4, "frase_mais_curta": 8, "aberturas_repetidas": 1, "verbos_reporte": 2, "adverbios_mente": 0}
- `contaminacao_detectada`: **False**
- **houve retentativa** — flags que persistiram após ela: ['fluencia_baixa', 'perspectiva_nao_marcada', 'perspectiva_nao_marcada']

> A Cura, um thriller, terror e mistério dirigido por 黒沢清 em 1997, segue um detetive que investiga uma série de assassinatos bizarros, todos marcados por um enigmático x nos corpos das vítimas, sem qualquer pista óbvia. Um ritmo lento, característica marcante da obra, permeia a experiência. 
> A grande maioria das notas (~79%) abraça a proposta do filme, com muitos descrevendo sua atmosfera e tom como perturbadores e hipnóticos. O ritmo é notado como lento e deliberado, intensificando o suspense psicológico. Há também uma apreciação pelos temas psicológicos e existenciais que a narrativa explora, mergulhando na fragilidade da identidade e na natureza do mal. Para alguns, a ausência de respostas e a ambiguidade são pontos fortes, enriquecendo a reflexão. 
> Uma minoria das notas (~17%) teve uma experiência mista. Para esse grupo, embora o filme apresente ideias intrigantes e uma atmosfera e estilo visual eficazes, muitos sentem que a execução falha no aprofundamento. Para eles, o ritmo é lento e a narrativa gera confusão, e muitos também apontam um final insatisfatório e ambíguo que deixa pontas soltas. 
> Uma pequena minoria das notas (~3%) não se conecta com a obra. Para eles, o ritmo é lento e tedioso para a maioria, não gerando a tensão, mistério ou terror prometidos. Muitos também veem o enredo e o roteiro como fracos e repetitivos, com personagens desinteressantes e planos, resultando numa experiência decepcionante.

Marcadores de perspectiva declarados:
- `medianas` — "Para esse grupo"
- `negativas` — "Para eles"

### Combinação C — gemini-2.5-pro · thinking off

#### `the-invite-2026`

_PULADO: gemini-2.5-pro falhou de novo após backoff: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\nPlease retry in 27.160771047s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-2.5-pro', 'location': 'global'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-2.5-pro', 'location': 'global'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerDay-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '27s'}]}}_

#### `cure`

_PULADO: gemini-2.5-pro falhou de novo após backoff: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\nPlease retry in 16.281835206s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerDay-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '16s'}]}}_

### Combinação D — gemini-2.5-pro · thinking on

#### `the-invite-2026`

_PULADO: gemini-2.5-pro falhou de novo após backoff: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.5-pro\nPlease retry in 4.44944948s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerDay-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', 'quotaId': 'GenerateContentInputTokensPerModelPerMinute-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-2.5-pro'}}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '4s'}]}}_

#### `cure`

_PULADO: gemini-2.5-pro falhou de novo após backoff: orçamento de 16 chamadas Gemini esgotado (tentativa: gemini-2.5-pro/thinking-on)_
