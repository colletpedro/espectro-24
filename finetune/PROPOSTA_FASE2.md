# PROPOSTA — Fase 2 (avaliação no teste): métricas, margens e custo

**Status: PROPOSTA para revisão do tech lead e do dono. NÃO é o pré-registro.**
Nada aqui foi medido no teste. O pré-registro da Fase 2 só é escrito (e
commitado à parte) depois desta revisão e ANTES de qualquer geração nos filmes
de teste. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.

Data: 2026-10-31. Modelo base escolhido: Qwen3-8B (`FINETUNE_REGISTRO.md`,
"Modelo base escolhido").

## Desenho

- **Unidade de reamostragem: o FILME.** 30 filmes de teste (`split.json`,
  semente 20261020), 89 buckets: o `a-brighter-summer-day/positivas` (Gemini)
  fica fora em todos os lados. Em geral 6 bullets por bucket, 18 por filme.
- **Três lados**, pareados por filme: **P** = publicado (DeepSeek, o
  professor); **B** = Qwen3-8B base, exportado pelo kernel
  `kaggle/kernel_base/exportar_base.py` (o mesmo caminho do treinado, sem
  adaptador); **T** = Qwen3-8B treinado. B e T saem de
  `scripts/finetune/gerar_sintese_teste.py`, 1 amostra por bucket, `think`
  false, `num_ctx` pela regra do gate 0.
- **Duas perguntas**, cada uma com seu tipo de critério:
  1. T × P: **não-inferioridade** com margem δ (o treinado não é pior que o
     publicado mais do que δ);
  2. T × B: **superioridade** (o treino melhorou a base: a diferença tem o
     sinal certo e o IC não cruza o zero).
- **IC:** bootstrap POR FILME, 10.000 reamostras, percentil 95% bilateral. Em
  cada reamostra, os mesmos filmes nos três lados (pareado); a taxa é a razão
  das somas (bullets ou buckets com o evento / total) nos filmes sorteados.
- **Regra de decisão PROPOSTA:** o T passa se TODAS as métricas
  confirmatórias passarem (teste de interseção–união: cada uma a 95%, sem
  correção de multiplicidade, porque a decisão exige todas).
- **Margens:** δ = o menor efeito detectável (MDE) com 30 filmes, 18 bullets por
  filme, α = 0,05 bilateral e poder 0,80, pela fórmula de `poder.md`
  (2 proporções, variância não agrupada, DEFF = 1 + 17 × ICC). Com δ = MDE e
  diferença real 0, a não-inferioridade é declarada com probabilidade ≈ 0,80.
  O ICC = 0,023 foi MEDIDO só para "sem apoio" (referência, 5 filmes × 2
  lados, 9 eventos): nas outras métricas ele é uma SUPOSIÇÃO, e a tabela dá
  também o MDE com ICC 0,05.

MDE (pontos percentuais, 30 filmes × 18 bullets; ESTIMADO pela fórmula):

| taxa de referência p | ICC 0,023: aumento | ICC 0,023: queda | ICC 0,05: aumento | ICC 0,05: queda |
|---|---|---|---|---|
| 0,022 | +4,0 | — | +4,8 | — |
| 0,55 | +9,8 | −10,0 | +11,3 | −11,5 |
| 0,80 | +7,4 | −8,6 | — | −10,0 |
| 0,85 | +6,4 | −7,8 | — | −9,1 |
| 0,90 | +5,2 | −6,8 | — | −8,0 |

(A linha de 2,2% reproduz o `poder.md`: +4,0 pp analítico, +3,3 pp simulado.)

## Métricas

### 1. Juiz v2.2 parando no 2º "sim" (confirmatória)

- **Fonte:** juiz congelado `44606cf1…` (gpt-oss:20b no Windows), a mesma
  recuperação e5 e os mesmos 5 pares por bullet da limpeza; parada no 2º "sim"
  (decisão 9 do gate 0). O publicado dos 5 filmes da referência só é
  reaproveitado se o sha256 das 450 linhas de entrada do juiz (lado P) bater.
- **% sem apoio** = bullets com 0 "sim" nos pares julgáveis / bullets julgados
  (indeterminado = nenhum par julgável: contado à parte, fora do denominador,
  e reportado por lado).
  - T × P: não-inferioridade, **δ = +4,0 pp** (p = 2,2% MEDIDO na referência;
    MDE com ICC 0,023 MEDIDO). Passa se o limite superior do IC de (T − P)
    < +4,0 pp.
  - T × B: superioridade, limite superior do IC de (T − B) < 0.
- **% com apoio ≥ 2** = bullets com ≥ 2 "sim" / bullets julgados.
  - T × P: não-inferioridade, **δ PROPOSTO = −8 pp** (MDE de queda para
    p ≈ 0,85 com ICC 0,023; a taxa do P no teste NÃO é conhecida). Regra
    PROPOSTA: medir o lado P primeiro e fixar δ pela mesma fórmula na taxa
    medida do P, ANTES de gerar ou julgar o T. Passa se o limite inferior do
    IC de (T − P) > −δ.
  - T × B: superioridade, limite inferior do IC de (T − B) > 0.

### 2. Especificidade (M-disp), SÓ se a validação da Fase 1 aprovar

- **Fonte:** `scripts/finetune/especificidade_bullet.py` (código `ff71747e…`),
  limiar congelado em `especificidade/limiares_v2.json` (`dbe0b135…`), sobre o
  bullet completo (`tema — exemplo`), referência `referencia_bullets.jsonl`
  (nenhum filme de teste na referência; a medida de cada item exclui o
  próprio filme).
- **% genérico** = bullets com M-disp ≥ limiar / bullets.
  - T × P: não-inferioridade, **δ PROPOSTO = +10 pp** (MDE de aumento para
    p ≈ 0,5–0,6 com ICC 0,023; com ICC 0,05 seria ~+11,4). Passa se o limite
    superior do IC de (T − P) < +10 pp.
  - T × B: superioridade, limite superior do IC de (T − B) < 0.
- Se a validação reprovar (AUC < 0,80, acurácia balanceada < 0,75 ou
  diferença entre subconjuntos > 0,15), esta métrica SAI, e a especificidade
  fica só com a leitura cega (Fase 4). Nada é recalibrado.

### 3. M1 — palavra de quantidade no `exemplo_parafraseado` (confirmatória, de imitação)

- **Fonte:** `scripts/finetune/metricas.py`, lista CONGELADA
  `metricas/palavras_quantidade.txt` (`a7fcd5a5…`). M1 = exemplos com ≥ 1
  expressão / exemplos, por lado. Referência no treino (P): 591/1.079 = 54,8%
  (MEDIDO).
- Não há direção "melhor" (o tratamento das palavras de quantidade é a opção C,
  pendência de produto do dono). Mede se o T imita o professor.
  - T × P: **equivalência**, **±10 pp PROPOSTO** (MDE para p ≈ 0,55). Passa se
    o IC de (T − P) estiver inteiro dentro de (−10, +10) pp.
  - T × B: descritiva (sem critério).

### 4. Validadores mecânicos e JSON válido (confirmatória, por bucket)

- **Fonte:** `_parse_llm_json` (JSON válido) e os validadores atuais da
  síntese, os mesmos do inventário (idioma, escopo, sem aspas, menções em
  [0, n], ≤ 6 temas, ordem decrescente, `n_reviews_analisadas` = n, campos não
  vazios, sem tema de menção única), aplicados à saída CRUA de uma amostra
  (sem a retentativa de produção) e, à parte, depois do pós-processamento de
  produção (`_construir_temas`, com o n do publicado).
- P passa em 293/293 por construção (MEDIDO no inventário). Com 89 buckets o
  IC por filme é largo; PROPOSTO um piso absoluto em vez de margem:
  - T: JSON válido em **≥ 87 de 89** buckets e todos os validadores em
    **≥ 87 de 89** (no máximo 2 falhas: a produção tem 1 retentativa);
  - T × B: descritiva (contagem e IC por filme).

### 5. M2 — concordância de `mencoes_aproximadas` (só T × P, descritiva)

- **Fonte:** `metricas.py` (`parear`, `concordancia_bucket`): pareamento e5
  húngaro com cosseno ≥ τ; por bucket, DAM (|m_T − m_P| / n, média dos pares) e
  τ_b de Kendall (P ≥ 3); agregado = média nos buckets definidos, com a fração
  pareada e IC por filme.
- Mede IMITAÇÃO, não acerto de contagem (o publicado não é gabarito). Não
  existe distribuição de referência para fixar margem: **PROPOSTO descritiva**
  na Fase 2. O τ do pareamento tem de ser fixado antes de medir; sugestão:
  fixá-lo no conjunto de VALIDAÇÃO (8 filmes, B × P), nunca no teste.

### 6. Leitura cega do dono (Fase 4; confirmatória final)

- **Material:** T × P, nos 5 filmes da referência (`fixos_no_teste`:
  anatomy-of-a-fall, incendies, mother-2017, napoleon-2023, the-substance),
  os 3 buckets de cada um, bullet completo (`tema — exemplo`), sem contagens,
  sem nome de modelo.
- **Lados sorteados** por filme (semente PROPOSTA a fixar no pré-registro):
  "A" e "B" trocam ao acaso; o mapa (filme → qual lado é qual) fica em
  `finetune/fase4/mapa_leitura.json`, com o sha256 impresso no fim do
  documento; o documento vai para `docs/arquivo-de-estudos/` (fora do git).
- **Pergunta por filme:** "A síntese A é publicável como está?" e o mesmo para
  B (sim/não), mais a preferência (A, B, empate).
- **Critério de partida (PROPOSTO): o T é publicável em ≥ 4 de 5 filmes.**
  A preferência é descritiva. Limitação: 5 filmes não têm poder para comparar
  preferência; o estilo do T pode denunciar o lado (o mesmo vazamento
  registrado na validação da Fase 1).

## Custo (Windows salvo indicação; ESTIMADO pelos números MEDIDOS hoje)

Números de base: geração base da Fase 1 = 15 buckets em 39,3 min de parede
(mediana 150,7 s; 121–266 s; 4,43 tok/s de geração; prompts de 4,2 a 14,3 mil
tokens); juiz = 16,2 s de parede por par (limpeza, 1.863 pares); export no
Kaggle = 831,5 s (smoke v4).

| etapa | onde | tempo |
|---|---|---|
| exportar a base (carga, provas, export, conferência da fusão, comparação com a biblioteca) | Kaggle (cota de GPU) | ~45–75 min |
| baixar o GGUF (5,03 GB) + `importar-pasta` (create, contagem do template, medição a 18.432, probe) | Windows | ~10–20 min |
| `plano` dos 89 pares (tokens exatos) | Mac | ~2–5 min |
| síntese B: 88 buckets × ~2,5 min + o outlier (~22–25 mil tokens, `num_ctx` ≈ 28.672–31.744: NÃO medido) | Windows | **~3,7–4,5 h** |
| síntese T (idem, depois do treino) | Windows | **~3,7–4,5 h** |
| juiz parando no 2º "sim", por lado: 534 bullets × 2,5–5 pares × 16,2 s (2,5 = suposição; 5 = teto, o `poder.md`) | Windows | **~6–12 h por lado; ~18–36 h nos 3** (−~1 h se o P dos 5 for reaproveitado) |
| M-disp (e5 em numpy), M1, validadores, M2 | Mac | minutos |
| leitura cega (Fase 4) | dono | ~30–60 min (ESTIMADO) |

Pontos abertos para a revisão:
1. o `num_ctx` do outlier pela regra fica ACIMA do probe medido (27.648): ESTIMADO
   28.672–31.744 (tokens do inventário, tokenizer do Qwen3.5, × 1,032–1,147, a razão Qwen3/Qwen3.5 medida nos 15 pares da Fase 1); tempo e memória não medidos;
2. o lado P no teste tem de ser julgado inteiro (só os 5 da referência podem
   ser reaproveitados);
3. a ordem (P → fixa δ do apoio ≥ 2 → B → T) e a semente da leitura cega
   entram no pré-registro.
