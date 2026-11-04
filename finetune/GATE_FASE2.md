# GATE DA FASE 2 — publicado e base no teste

Gerado por `scripts/finetune/gate_fase2.py` a partir de `finetune/fase2/` (`c1_c4_fase2.json`, `delta2.json`, juiz e síntese da base). Pré-registro: `PREREGISTRO_AVALIACAO.md`. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.

Conjunto (MEDIDO): 30 filmes, 89 buckets mantidos. Entradas do commit `742cfe3` (162 arquivos, sha256 `f2a7a0ba…`). Bootstrap por filme: 10.000 reamostras, semente 20261101. Juiz `44606cf1…`, parada no 2º sim.

**Fase 2 é descritiva.** Nada aqui decide o treinado; o que se fixa é o δ₂. O treinado só é gerado depois deste arquivo commitado (`gerar_sintese_teste.py` recusa).

## 1. C1–C4 do publicado e da base (MEDIDO)

Taxa de cada lado com IC 95% do bootstrap por filme.

| métrica | publicado | base |
|---|---|---|
| C1 · % sem apoio (bullets) | 19/534 = 3,6% [1,9; 5,4] | 36/526 = 6,8% [4,3; 9,7] |
| C2 · % apoio ≥ 2 (bullets) | 457/534 = 85,6% [82,2; 89,0] | 436/526 = 82,9% [78,5; 87,0] |
| C3 · M1, % exemplos com palavra de quantidade | 303/534 = 56,7% [51,7; 62,0] | 242/526 = 46,0% [41,1; 50,8] |
| C4 · % buckets válidos | 89/89 = 100,0% [100,0; 100,0] | 89/89 = 100,0% [100,0; 100,0] |

Indeterminados (sem par julgável; fora do denominador de C1/C2): publicado 0; base 0.
C4 da base na 1ª tentativa, sem retentativa (descrição): 89/89.

### Base − publicado (descritivo, com os limiares do treinado)

| critério | base − publicado | IC 95% | limiar | satisfaz |
|---|---|---|---|---|
| C1 | +3,3 pp | [+0,4; +6,5] | sup. < +4,0 e pontual ≤ +2,0 pp | não |
| C2 | -2,7 pp | [-7,8; +2,1] | inf. > −7,8 pp (δ₂ fixado) | não |
| C3 | -10,7 pp | [-18,3; -3,4] | sup. < +10,0 pp | sim |
| C4 | 89/89 buckets | — | ≥ 87 | sim |

A base NÃO satisfaz C1 a C4 juntos (descritivo).

## 2. δ₂ fixado (MEDIDO p₀; fórmula pré-registrada)

- p₀ = taxa de apoio ≥ 2 do publicado = 85,6% (534 bullets julgados, buckets mantidos);
- **δ₂ = 7,8 pp** (substitui os 8 pp); poder.mde_analitico no sentido da queda; n = 30·18/(1 + 17·0,023);
- `delta2.json` sha256 `688a9d3f8d77b1f8685a3cf3e8bc90fd98a5874d70a5d2063c63231235c44528`.

## 3. Buckets fora e por quê (MEDIDO)

- `a-brighter-summer-day/positivas`: fallback_conteudo: síntese deste bucket feita pelo Gemini (fora do treino e de toda avaliação, em todos os lados).
- Fora por memória (saem dos dois lados, inclusive do publicado): nenhum.
- Derrubados uma vez pela guarda de RAM e refeitos com sucesso: `django-unchained/positivas`, `incendies/negativas`, `mother-2017/negativas`, `mother-2017/positivas`, `spider-man-across-the-spider-verse/medianas`, `the-second-mother/negativas`, `the-substance/medianas`.
- Outlier `500-days-of-summer/positivas` (num_ctx 31744): ok True, abortos por memória 0, fora por memória False, 495.4 s.

## 4. Tempos (MEDIDO)

- Síntese da base: 89 buckets, 4,0 h somadas (mediana 154 s, de 88 a 495 s); chamadas por bucket {1: 89}.
- Juiz, publicado: 1600 chamadas (1600 ok, 0 reaproveitadas), 6,9 h de latência somada (mediana 14,1 s); de 2026-11-03T12:41:51+00:00 a 2026-11-03T19:34:52+00:00 (UTC). `preparar` (Mac): 788 s.
- Juiz, base: 1627 chamadas (1627 ok, 0 reaproveitadas), 7,1 h de latência somada (mediana 14,2 s); de 2026-11-03T22:17:16+00:00 a 2026-11-04T05:39:10+00:00 (UTC). `preparar` (Mac): 814 s.

## 5. Comparação com a medição antiga dos 5 de referência (descritiva)

- Antes (MEDIDO, `poder.md`, gate-local): publicado 2/90 sem apoio.
- Agora (MEDIDO): publicado nos mesmos 5 filmes, 2/90 sem apoio (0 indeterminados).
- **As entradas diferem:** o sha256 das 450 linhas do publicado dos 5 foi `059f3825…`, o esperado era `a68a6c9b…` (bate: False). Por isso nada foi reaproveitado e o publicado foi julgado inteiro. A medição antiga julgou todos os pares; esta para no 2º sim (o "sem apoio" não muda pela parada, mas o conjunto de pares e de bullets pode mudar). Não é réplica: é só uma conferência de ordem de grandeza.

## 6. O que NÃO foi medido

- O TREINADO: nem gerado nem julgado no teste (Fase 4, depois deste commit).
- C5 e C6 (rotulagem e leitura cega do dono): Fase 4.
- M2 (`mencoes_aproximadas`): o τ ainda depende de um DESVIO.
- Os parâmetros de amostragem efetivos do Ollama além dos passados em cada chamada (DESVIO_P01): não lidos do servidor.
- C4 do publicado na 1ª tentativa: o publicado não tem tentativas gravadas.
- Os bullets indeterminados (sem par julgável na janela do juiz): fora de C1/C2.
- Variação entre execuções da base (uma geração, seed fixa): não estimada.

<!-- gate_fase2 {"c1_c4_fase2_sha256": "37bd704053b5aa3d54ab3b9d4210725b32f1c76d3015357be0c1c5062d0a974e", "delta2_sha256": "688a9d3f8d77b1f8685a3cf3e8bc90fd98a5874d70a5d2063c63231235c44528", "manifesto_sintese_base_sha256": "698c3e4072102dfd1a241b1e7bee43774b9aad79d4715d2ac82cd836b52ab7c5", "saida_juiz_base_sha256": "46645f5db446e66ab74866f762090b14953de1151893630e1b067a9f40c88860", "saida_juiz_publicado_sha256": "7a319df612aa86fd70a27a5cee9cbf1db1d480aa0104dd9bea385a1bf5e3074f", "script_sha256": "37b51a1fd2344a97adfc304b14bc0782178821c5475e9b9f842c31886174abc1"} -->
