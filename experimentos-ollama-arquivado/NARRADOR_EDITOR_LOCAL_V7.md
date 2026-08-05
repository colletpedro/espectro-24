# Experimento 7 — narrador [D2] e editor [E2] no modelo local (Ollama / `qwen3-espectro`)

Experimento exploratório, **não é bump de versão**. Zero Gemini, zero
Letterboxd, zero TMDB — roda inteiramente sobre os JSONs já sintetizados de
`cure` e `cidade-de-deus` (`resultado/cure.json`, `resultado/cidade-de-deus.json`),
que carregam os `buckets` validados (saída de §D) e, como gabarito, a
`narrativa_bruta` (narrador Gemini) e a `narrativa` final (editor Gemini).

Ambiente: Ollama em `localhost:11434`, modelo `qwen3-espectro`
(`qwen3.5:9b`, Q4_K_M, `num_ctx=32768`), `think=false` sempre, timeout
300s — mesmos parâmetros já usados e validados no experimento de síntese.
Prompts de produção **byte-idênticos** (`build_narrator_prompt`,
`_EDITOR_SYSTEM_PROMPT`, `montar_protegidos`, `build_editor_user_message`,
importados diretamente de `src/espectro24/synthesize.py`, nunca copiados).

Script do experimento: `scripts/experimento_narrador_editor_local_v7.py`
(novo arquivo, não faz parte do pipeline de produção).

## Orçamento de chamadas Ollama — como foi usado

Orçamento-teto: 12 chamadas. **Usadas: 12/12**, todas com resposta (nenhuma
pulada por estouro de orçamento, nenhum erro de rede/timeout).

| Etapa | Chamadas | Observação |
|---|---:|---|
| Narrador `cure` | 2 | 1 chamada + 1 retentativa (validação de honestidade falhou na 1ª) |
| Narrador `cidade-de-deus` | 2 | 1 chamada + 1 retentativa (idem) |
| Editor `cure` / B1 (sobre bruta do gabarito Gemini) | 2 | 1 chamada + 1 retentativa — **descartada** |
| Editor `cure` / B2 (sobre narrador local) | 2 | 1 chamada + 1 retentativa — **descartada** |
| Editor `cidade-de-deus` / B1 | 2 | 1 chamada + 1 retentativa — **descartada** |
| Editor `cidade-de-deus` / B2 | 2 | 1 chamada + 1 retentativa — **descartada** |
| **Total** | **12** | |

**Decisão de orçamento documentada:** em produção o editor pode fazer até
`1 + EDITOR_MAX_TENTATIVAS` chamadas (`EDITOR_MAX_TENTATIVAS = 3`, i.e. até
4 chamadas por invocação). Com 4 invocações de editor planejadas (2
filmes × 2 condições), o pior caso de produção sozinho já estouraria os 12
disponíveis (até 16). Para caber no teto sem abrir mão de testar a
retentativa pelo menos uma vez, `EDITOR_MAX_TENTATIVAS` foi reduzido para
**1 só neste processo**, via `synthesize.EDITOR_MAX_TENTATIVAS = 1` em
runtime (monkeypatch de módulo dentro do script do experimento) — **não**
foi editado `config.py`, nem qualquer arquivo de produção. Com isso, o pior
caso passou a ser exatamente 2×2 (narrador) + 4×2 (editor) = 12, que foi o
que de fato aconteceu: todas as 6 invocações (2 narrador + 4 editor)
esgotaram sua única retentativa.

## TESTE A — narrador [D2] local

Saída completa em `resultado/experimento_local/v7/narrador/{cure,cidade-de-deus}.json`.

### `cure`

- **Chamadas:** 2 (houve retentativa). Tempos: 178.3s + 172.6s = **350.9s** (~5.8 min).
- **Narrativa gerada (íntegra):** `"A Cura"` — só o título, nada além disso.
- **Narrativa_bruta do gabarito Gemini** (para comparação, início):
  `"Em 1997, Kiyoshi Kurosawa nos trouxe A Cura. É um filme que mistura Crime,
  Thriller, Terror e Mistério, onde um detetive investiga mortes misteriosas
  marcadas por um x nos corpos. Essa busca por resp[...]"` (texto completo no
  JSON do experimento e em `resultado/cure.json`).
- **Validações de honestidade** (após a retentativa, já esgotada):

  | Validação | Resultado |
  |---|---|
  | `idioma_invalido` | false |
  | `escopo_suspeito` | false |
  | `prevalencia_suspeita` | false |
  | `quantificador_suspeito` | false |
  | `consenso_suspeito` | false |
  | `peso_nao_ancorado` | **true** |
  | `vocabulario_peso_suspeito` | false |
  | `perspectiva_nao_marcada` | **true** |
  | `aspas_removidas` | false |
  | `falhou` (sem JSON válido) | false |

  As duas flags `true` são consequência direta e esperada de o texto ter
  ficado reduzido a duas palavras: não há como ancorar peso nem marcar
  perspectiva em um texto que não chega a descrever nenhum grupo. As flags
  que checam CONTEÚDO indevido (idioma, escopo, quantificador inflado,
  consenso inventado, vocabulário do peso) deram `false` só porque não há
  conteúdo nenhum para violá-las — **não é evidência de honestidade
  robusta**, é vacuidade.
- **Campos declarados:** `consensos_usados: []`, `quantificadores_usados: []`,
  `marcadores_perspectiva: []` — todos vazios, consistente com o texto vazio
  de conteúdo (nada para bater contra o texto).
- **Retentativa:** sim, 1 vez (2 chamadas no total). A 1ª tentativa já havia
  falhado alguma validação (o código não distingue qual falhou sem
  instrumentação extra — não guardada neste experimento); a resposta pós-
  retentativa é a que ficou registrada, e o problema (texto colapsado a
  "A Cura") **persistiu** mesmo depois do reforço.
- **Três movimentos presentes?** **Não.** Nem o movimento 1 (filme) foi
  completado — só o título. Movimentos 2 e 3 ausentes.
- **Nota sobre a causa provável:** a resposta bruta do Ollama (medida pelo
  wrapper de chamada) tinha **3321 e 3305 caracteres** nas duas tentativas —
  não é um caso de resposta vazia ou cortada por timeout. Como o adaptador
  usado (`ollama_client_call` → `ollama_chat_bruto`) envia sempre
  `"format": "json"` ao Ollama (o mesmo parâmetro usado para a síntese §D,
  que de fato precisa de JSON estruturado), o JSON retornado provavelmente
  contém outras chaves grandes (ou repetição/ruído) além do campo
  `"narrativa"`, e é só o valor desse campo que o parser extrai — o
  conteúdo bruto completo **não foi salvo neste experimento** (só o
  comprimento), então essa é uma hipótese plausível a partir dos dados
  disponíveis, não uma causa confirmada por inspeção direta do JSON cru.

### `cidade-de-deus`

- **Chamadas:** 2 (houve retentativa). Tempos: 162.9s + 174.2s = **337.1s** (~5.6 min).
- **Narrativa gerada (íntegra):**
  > Em Cidade de Deus (2002), dirigida por Fernando Meirelles no gênero Drama
  > e Crime, um jovem morador da periferia busca uma vida digna através da
  > fotografia para fugir do destino violento que o cerca. A obra se destaca
  > pelo estilo visual dinâmico, cinematografia marcante e edição ágil criam
  > imersão intensa enquanto a montagem rápida estrutura uma narrativa que
  > abrange décadas de história local com ritmo variável. O filme apresenta
  > violência brutal e realista ao lado de um retrato crueiro da miséria e
  > das condições sociais nas favelas, construindo uma atmosfera densa onde
  > personagens carismáticos enfrentam um ambiente hostil sem perder o foco
  > na realidade social complexa que permeia a trama.

  (nota: "retrato crueiro" no texto gerado é um defeito ortográfico do
  modelo — provavelmente "cruel" — reportado aqui como está, sem correção.)
- **Narrativa_bruta do gabarito Gemini** (para comparação, início):
  `"Dirigido por Fernando Meirelles em 2002, Cidade de Deus é um drama
  criminal que segue Buscapé, um jovem morador da Cidade de Deus que,
  crescendo em meio à violência, busca na fotografia uma saída para uma vida
  digna. [...]"` (completa no JSON do experimento e em `resultado/cidade-de-deus.json`).
- **Validações de honestidade:**

  | Validação | Resultado |
  |---|---|
  | `idioma_invalido` | false |
  | `escopo_suspeito` | false |
  | `prevalencia_suspeita` | false |
  | `quantificador_suspeito` | false |
  | `consenso_suspeito` | false |
  | `peso_nao_ancorado` | **true** |
  | `vocabulario_peso_suspeito` | false |
  | `perspectiva_nao_marcada` | **true** |
  | `aspas_removidas` | false |
  | `falhou` | false |

- **Campos declarados vs. o texto:**
  - `consensos_usados`: 3 itens declarados (estilo visual, narrativa
    histórica, violência), todos citando grupos/temas que **existem** no
    relatório (por isso `consenso_suspeito: false`) — mas o texto gerado só
    usa, de fato, o primeiro (estilo visual/edição). Os outros dois
    ("narrativa de ambientação histórica...", "violência brutal...") **têm
    lastro real no texto** (o parágrafo final fala de "narrativa que abrange
    décadas" e de "violência brutal e realista"), então a declaração bate
    com o texto, mesmo que resumida.
  - `quantificadores_usados`: 2 itens declarados, mas os valores no campo
    `quantificador` **não são quantificadores** — são frases inteiras
    ("alguns espectadores acharam o filme monótono ou entediante em certas
    partes, com um ritmo inconstante"), não uma palavra do vocabulário
    esperado ("muitos"/"alguns"/"a maioria"/etc). Isso é uma violação de
    formato do campo que a checagem de código (`_quantificadores_validos`)
    não pegou como erro fatal (ela audita a EXISTÊNCIA do tema e a força do
    rótulo, não a forma da string), mas é visivelmente uma resposta mal
    formada do modelo.
  - `marcadores_perspectiva`: 2 itens declarados, cada um com um `trecho`
    que cita percentuais (`~1%`, `~8%`) — só que **esses percentuais e
    esses trechos não aparecem em lugar nenhum do texto final gerado**. É
    exatamente essa incoerência entre o que o narrador *declara* ter
    escrito e o que ele *de fato* escreveu que a checagem `_marcadores_validos`
    detecta, resultando (corretamente) em `perspectiva_nao_marcada: true`
    — a rede de segurança funcionou como desenhado.
- **Retentativa:** sim, 1 vez (2 chamadas). O problema de ancoragem/marcação
  persistiu depois da retentativa.
- **Três movimentos presentes?** **Parcialmente.** Movimento 1 (filme) está
  completo e correto. Movimento 2 (consenso) está presente, ainda que
  resumido a uma frase. Movimento 3 (contraste `~91%`/`~8%`/`~1%` entre os
  três grupos) está **ausente** — o texto nunca menciona um percentual,
  apesar de o narrador ter declarado marcadores com percentuais que não
  chegaram a ser escritos.

**Síntese do Teste A:** o narrador local passou nas checagens de
CONTEÚDO INDEVIDO (idioma, escopo, quantificador inflado, consenso
inventado, vocabulário do peso) nos dois filmes, mas falhou nas duas
checagens de COMPLETUDE ESTRUTURAL (ancoragem de peso, marcação de
perspectiva) nos dois filmes, mesmo após a única retentativa disponível. Em
`cure` o problema é extremo (texto reduzido a duas palavras); em
`cidade-de-deus` é parcial (falta só o terceiro movimento). Em nenhum dos
dois casos o narrador chegou a produzir os três movimentos completos que a
spec pede.

## TESTE B — editor [E2] local

Saída completa em
`resultado/experimento_local/v7/editor/{cure,cidade-de-deus}__{B1,B2}.json`.

**Resultado idêntico nas 4 combinações: edição DESCARTADA, motivo
`formato_invalido`, nas duas tentativas de cada uma (8/8 chamadas de
editor reprovadas pela mesma checagem).**

| Filme | Condição | Chamadas | `n_tentativas` | `motivos_por_tentativa` | `edicao_descartada` | `similaridade` | Tempo total |
|---|---|---:|---:|---|---|---:|---:|
| cure | B1 (sobre bruta do gabarito Gemini) | 2 | 2 | formato_invalido, formato_invalido | **true** | 0.348 | 141.3s |
| cure | B2 (sobre narrador local) | 2 | 2 | formato_invalido, formato_invalido | **true** | 0.034 | 33.1s |
| cidade-de-deus | B1 | 2 | 2 | formato_invalido, formato_invalido | **true** | 0.056 | 35.8s |
| cidade-de-deus | B2 | 2 | 2 | formato_invalido, formato_invalido | **true** | 0.000 | 35.4s |

Como toda edição foi descartada, o **fail-safe do §E2 funcionou
exatamente como projetado**: `texto` final = `texto_bruto` (a entrada,
intocada) em todos os 4 casos — nenhum conteúdo foi perdido ou corrompido,
a garantia "o editor pode não melhorar, mas não pode piorar" se sustentou.
`protegidos_perdidos: []` e `numeros_alterados: false` em todos os casos
(nunca chegaram a ser avaliados de fato, porque a checagem estrutural (0),
que roda ANTES de todas as outras, já reprovou a resposta bruta antes de
comparar protegidos/números/honestidade).

**Causa técnica identificada com alta confiança:** o adaptador
`ollama_chat_bruto` (usado por `ollama_client_call`, único client_call
disponível para Ollama) envia **sempre** `"format": "json"` na chamada
`/api/chat` — parâmetro correto e necessário para o narrador e para a
síntese §D (que precisam de um objeto JSON), mas que **força o Ollama a
sempre envolver a resposta num objeto JSON**, mesmo quando o prompt do
editor pede explicitamente "responda APENAS com o texto final editado, em
PROSA CORRIDA [...] sem envolver a resposta num objeto ou campo". A
checagem `_formato_invalido` (§E2, v1.7.2) foi desenhada exatamente para
pegar esse tipo de invólucro — e pegou, nas 8 chamadas de editor, porque a
própria infraestrutura do provider local está estruturalmente incompatível
com a exigência de "prosa pura" do editor. Não há registro do texto bruto
retornado por cada chamada de editor neste experimento (só o comprimento em
caracteres foi medido pelo wrapper de contagem), então a hipótese não foi
confirmada por inspeção literal do payload — mas é consistente com: (a) o
código confirmado de `ollama_chat_bruto` (`"format": "json"` incondicional);
(b) a ausência de `"ollama"` em `PROVIDER_CLIENTS_PROSA` (o dicionário de
adaptadores da etapa de prosa em produção só tem `anthropic` e `gemini` —
ou seja, produção **nunca tentou usar Ollama nesta etapa**, e este
experimento só conseguiu testar porque passou `client_call=ollama_client_call`
explicitamente, contornando essa ausência); e (c) o motivo de descarte ser
`formato_invalido` — não `regressão de honestidade`, não
`trecho perdido`, não `número alterado` — nas 8 chamadas, sem exceção.

**Métricas de fluência (diagnóstico, não critério):** como toda edição foi
descartada, entrada e saída são idênticas — `metricas_fluencia_entrada` ==
`metricas_fluencia_saida` nos 4 casos (ver JSONs individuais). Não há
sinal de fluência do editor local para reportar, porque nenhum texto
editado sobreviveu às checagens mecânicas.

## Tabela-resumo

| Pergunta | Resposta |
|---|---|
| Narrador local passou nas validações de honestidade (conteúdo indevido)? | Sim, nos dois filmes: `idioma_invalido`, `escopo_suspeito`, `quantificador_suspeito`, `consenso_suspeito`, `vocabulario_peso_suspeito`, `aspas_removidas` deram `false` (ou `true` só por remoção mecânica de aspas, não por falha) |
| Narrador local passou nas validações de completude estrutural? | **Não**, nos dois filmes: `peso_nao_ancorado` e `perspectiva_nao_marcada` deram `true` mesmo após retentativa |
| Narrador produziu os três movimentos? | `cure`: não (só o título). `cidade-de-deus`: parcialmente (movimentos 1-2, movimento 3 ausente) |
| Editor local foi aceito em alguma condição? | **Não, em nenhuma das 4** (cure/B1, cure/B2, cidade-de-deus/B1, cidade-de-deus/B2) — todas descartadas por `formato_invalido` |
| Causa identificada do descarte do editor | Adaptador Ollama força `"format": "json"` em toda chamada — incompatível com a exigência de prosa pura do prompt do editor; produção nunca usou Ollama nesta etapa (`PROVIDER_CLIENTS_PROSA` não tem entrada `ollama`) |

### Extrapolação de custo (tempo, não qualidade)

| Etapa | `cure` | `cidade-de-deus` | Média |
|---|---:|---:|---:|
| Narrador (com 1 retentativa) | 350.9s | 337.1s | 344.0s |
| Editor, condição B2 (pipeline 100% local ponta a ponta) | 33.1s | 35.4s | 34.3s |
| **Narrador + editor (pipeline local completo)** | **384.0s (6.4 min)** | **372.5s (6.2 min)** | **378.3s (6.3 min)** |

Somando aos ~14,5 min/filme já medidos para a síntese §D (experimento
anterior, v6): **~14,5 + ~6,3 ≈ 20,8 min/filme** para o pipeline local
completo (síntese + narrador + editor), **considerando que a edição é
sempre descartada e cai no fail-safe** (se o editor algum dia passar a
funcionar de fato — ex. com um adaptador que não force JSON —, o tempo do
editor por filme tende a ser semelhante ou um pouco maior, já que hoje ele
só está sendo medido até a 1ª reprovação estrutural, sem chegar a produzir
uma edição avaliável de verdade).

Para **50 filmes**: 50 × 20,8 min ≈ **1040 min ≈ 17,3 horas** só de
tempo de chamada LLM (sem contar coleta de reviews/distribuição/ficha, que
são passos de rede separados e não fizeram parte deste experimento).

## O que NÃO está neste relatório

Nenhum veredito de qualidade literária da prosa — nem do narrador, nem do
que teria sido a edição (que nunca chegou a existir de fato, por ser
sempre descartada). Os textos estão reproduzidos integralmente acima e nos
JSONs para leitura humana.

## Arquivos gerados

- `scripts/experimento_narrador_editor_local_v7.py` — script do experimento (novo)
- `resultado/experimento_local/v7/narrador/cure.json`
- `resultado/experimento_local/v7/narrador/cidade-de-deus.json`
- `resultado/experimento_local/v7/editor/cure__B1.json`
- `resultado/experimento_local/v7/editor/cure__B2.json`
- `resultado/experimento_local/v7/editor/cidade-de-deus__B1.json`
- `resultado/experimento_local/v7/editor/cidade-de-deus__B2.json`
- `resultado/experimento_local/v7/log_chamadas.json` — log bruto das 12 chamadas (tempo por chamada, erros)
- `NARRADOR_EDITOR_LOCAL_V7.md` — este relatório

Nenhum arquivo de `SPEC.md`, `resultado/*.json` de produção, ou dos
experimentos anteriores (`v5`, `v6`, `RECALL_V6.md`,
`AUDITORIA_RECALL_V6_V3.md`) foi alterado. Nenhuma mudança de teste; a
suíte (`pytest -q`, raiz do projeto) permanece verde: **384 passed**, igual
ao baseline medido antes do experimento.
