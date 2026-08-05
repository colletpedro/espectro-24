# Espectro 24 — Comparação: síntese local (Ollama) vs. gabarito Gemini

Gerado em 2026-07-27. **Experimento, não bump de versão** — `SPEC_VERSION` inalterado, `resultado/cure.json` (o gabarito) não foi tocado. Comparação lê `resultado/experimento_local/cure__ollama.json` (gerado por `scripts/comparar_sintese_local.py`) contra o gabarito já existente.

**Zero chamadas Gemini, zero requisições Letterboxd, zero requisições TMDB.** As reviews do `cure` vieram inteiramente do cache em disco (`Fetcher(offline=True)`, confirmado `n_network == 0`); os prompts (`build_system_prompt`/`build_user_message`) são os MESMOS objetos de código que o pipeline de produção usa — a única variável entre os dois resultados é o provider (Ollama local vs. Gemini).

**Ambiente:** Ollama em `localhost:11434`, modelo `qwen3-espectro` (Qwen3.5-9B, Q4_K_M, `num_ctx=32768`), `think: false`, `format: "json"`.

**Nenhum veredito de qualidade é emitido aqui.** A comparação semântica dos temas é humana — o que segue são números e textos, lado a lado.

---

## Tarefa 0 — checagem de contexto (antes de qualquer chamada)

| Bucket | Reviews | user_msg (chars) | system (chars) | ~tokens (chars/3.5) |
|---|---|---|---|---|
| `negativas` | 50 | 44.375 | 2.197 | ~13.306 |
| `medianas` | 20 | 37.307 | 2.193 | ~11.286 |
| `positivas` | 30 | 39.452 | 2.193 | ~11.899 |

Pior caso (`negativas`) + teto de saída (`LLM_MAX_TOKENS=3000`) ≈ 16,3k tokens — bem dentro dos 32.768 de `num_ctx`. **Sem risco de truncamento por contexto insuficiente.** Prosseguiu sem ajuste.

---

## Bucket `negativas` (50 reviews)

**JSON válido de primeira?** Sim, nas duas versões. **Retentativa?** Nenhuma nas duas. **Tempo Ollama:** 126,1s (1 chamada). **Temas:** gabarito 6, Ollama 6 (ambos dentro do teto de 6 da spec).

| # | Gabarito (Gemini) | menções/n | Ollama (local) | menções/n |
|---|---|---|---|---|
| 1 | Ritmo lento e tedioso | 35/50 | Ritmo excessivamente lento e estagnação da narrativa | 48/50 |
| 2 | Falta de tensão/mistério/terror | 25/50 | Personagens desprovidos de profundidade e interesse | 35/50 |
| 3 | Enredo e roteiro fracos/repetitivos | 18/50 | Narrativa previsível sem tensão dramática | 32/50 |
| 4 | Personagens desinteressantes/planos | 15/50 | Atmosfera clínica e excessivamente limpa | 18/50 |
| 5 | Filme superestimado/pretensioso | 12/50 | Tratamento superficial dos temas de hipnose e psicologia | 15/50 |
| 6 | Final insatisfatório/abrupto | 8/50 | Atores entregando performances impessoais ou robóticas | 12/50 |

**Denominador (`n_reviews_analisadas`) bate com o `n_validas` real do bucket (50)?** Sim, nas duas versões, em todos os temas. **Numerador > denominador?** Não, em nenhum tema de nenhuma versão. **`mencoes_clampadas`:** false em todos.

**Idioma:** pt-BR em 100% dos campos, nas duas versões. **Aspas de citação:** gabarito teve 1 tema com `aspas_removidas: true` ("Final insatisfatório/abrupto") — o Gemini havia citado uma review entre aspas, removida mecanicamente; Ollama não gerou nenhuma aspas em nenhum exemplo deste bucket.

**Anti-spoiler:** nenhuma menção a evento de trama, nome de personagem ou desfecho específico em nenhuma das duas versões neste bucket. Os exemplos do Ollama ficam tão abstratos quanto os do gabarito ("resultando em uma falta total de conexão emocional com as figuras centrais da história" — sem nomear ninguém nem descrever nenhuma cena).

---

## Bucket `medianas` (20 reviews)

**JSON válido de primeira?** Sim, nas duas. **Retentativa?** Nenhuma. **Tempo Ollama:** 131,1s (1 chamada). **Temas:** gabarito 5, Ollama 6 (ambos ≤ 6).

| # | Gabarito (Gemini) | menções/n | Ollama (local) | menções/n |
|---|---|---|---|---|
| 1 | Ritmo lento e confusão narrativa | 10/20 | Atmosfera lenta e ambígua que divide a audiência | 12/20 |
| 2 | Final insatisfatório/ambíguo | 8/20 | Problemas na resolução dos mistérios | 9/20 |
| 3 | Ideias intrigantes, mas execução falha | 7/20 | Conceitos abstratos de identidade e mal | 8/20 |
| 4 | Atmosfera e estilo visual eficazes | 6/20 | Distância emocional entre espectador e personagens | 6/20 |
| 5 | Necessidade de revisitação para compreensão | 6/20 | Confusão narrativa sobre motivações | 5/20 |
| 6 | *(gabarito tem só 5 temas)* | — | Realismo perturbador versus elementos sobrenaturais | 4/20 |

**Denominador bate com `n_validas` (20)?** Sim, nas duas, todos os temas. **Numerador > denominador?** Não. **`mencoes_clampadas`:** false em todos.

**Idioma:** pt-BR em 100%. **Aspas:** nenhuma nas duas versões neste bucket.

**Anti-spoiler — ACHADO A DESTACAR:** o exemplo do tema "Confusão narrativa sobre motivações" (Ollama) diz: *"Há uma crítica recorrente quanto à falta de clareza sobre as razões por trás dos atos violentos e a transição entre o personagem amnésico e outras vítimas."* Isso nomeia uma característica específica de um personagem ("amnésico") e uma dinâmica de trama ("transição... entre... outras vítimas") — mais concreto do que qualquer exemplo do gabarito Gemini, que se mantém inteiramente no nível temático/abstrato em todo o `cure` (nunca descreve mecânica de enredo ou traço de personagem específico). Não chega a revelar o desfecho, mas é o único ponto, nos dois conjuntos, onde a checagem anti-spoiler merece atenção humana antes de publicar.

---

## Bucket `positivas` (30 reviews)

**JSON válido de primeira?** Sim, nas duas. **Retentativa?** Nenhuma. **Tempo Ollama:** 133,1s (1 chamada). **Temas:** gabarito 5, Ollama 6.

| # | Gabarito (Gemini) | menções/n | Ollama (local) | menções/n |
|---|---|---|---|---|
| 1 | Atmosfera e Tom Perturbador/Hipnótico | 15/30 | Atmosfera de opressão e paranoia | 15/30 |
| 2 | Pacing Lento e Deliberado | 10/30 | Atuação contida dos atores | 12/30 |
| 3 | Temas Psicológicos e Existenciais | 9/30 | Estética visual minimalista | 10/30 |
| 4 | Atuação do Antagonista | 6/30 | Tema da identidade perdida | 9/30 |
| 5 | Design de Som e Cinematografia | 6/30 | Psicologia do mal oculto | 8/30 |
| 6 | *(gabarito tem só 5 temas)* | — | Tratamento lento e deliberado | 7/30 |

**Denominador bate com `n_validas` (30)?** Sim, nas duas. **Numerador > denominador?** Não. **`mencoes_clampadas`:** false em todos.

**Idioma:** pt-BR em 100%. **Aspas:** nenhuma nas duas.

**Anti-spoiler:** limpo nas duas versões — nenhuma menção a evento de trama, personagem nomeado ou desfecho.

---

## Tabela-resumo

| | Gemini (gabarito) | Ollama (local) |
|---|---|---|
| JSON válido de primeira, nos 3 buckets | Sim | Sim |
| Retentativas (dos 3 buckets) | 0 | 0 |
| Total de temas (3 buckets) | 16 (6+5+5) | 18 (6+6+6) |
| Denominador incorreto | 0 ocorrências | 0 ocorrências |
| Numerador > denominador | 0 ocorrências | 0 ocorrências |
| Idioma não-pt-BR | 0 | 0 |
| Aspas de citação (removidas mecanicamente) | 1 (negativas) | 0 |
| Achado anti-spoiler para revisão humana | 0 | 1 (medianas — "personagem amnésico") |
| Tempo total de síntese | não medido nesta sessão (produção) | 390,3s (6m30s) |

## Tempo e extrapolação

| Bucket | Tempo Ollama | Chamadas |
|---|---|---|
| `negativas` (50 reviews) | 126,1s | 1 |
| `medianas` (20 reviews) | 131,1s | 1 |
| `positivas` (30 reviews) | 133,1s | 1 |
| **Total (`cure`, 3 buckets)** | **390,3s ≈ 6,51 min** | 3 |

**Extrapolação** (assumindo o mesmo padrão de 1 chamada/bucket, sem retentativa — o `cure` é só 1 amostra, variação real esperada entre filmes):

| Filmes | Minutos de LLM local | Horas |
|---|---|---|
| 1 | ~6,5 min | 0,11h |
| 50 | ~325 min | **~5,4h** |
| 300 | ~1.952 min | **~32,5h** |

Isso cobre só a etapa de síntese §D (3 chamadas/filme) — não inclui narrador [D2] nem editor [E2], que este experimento não testou.

---

## Observações finais (dados, não veredito)

- As duas versões respeitaram o teto de 6 temas, produziram JSON válido de primeira em todos os 6 buckets combinados (nenhuma retentativa), mantiveram idioma pt-BR em 100% dos campos, e não tiveram nenhum caso de denominador incorreto ou numerador clampado.
- Divergência de contagem de temas: Ollama produziu 6 temas em todos os 3 buckets; o gabarito Gemini produziu 6/5/5 — a spec permite até 6, então ambos estão dentro da regra; a diferença é de quantidade escolhida pelo modelo, não de violação.
- O único ponto que pediria atenção humana antes de publicar é o achado anti-spoiler do bucket `medianas` acima — vale conferir se esse nível de especificidade de trama passaria pela revisão que o `cure` já recebeu no gabarito.
- Custo de tempo: ~6,5 minutos de LLM por filme (só síntese) é o número que dimensiona a viabilidade de um catálogo maior sem a cota do Gemini — a decisão de escala (50 ou 300 filmes) depende de quanto tempo de máquina está disponível, não é uma limitação técnica adicional além da já medida aqui.
