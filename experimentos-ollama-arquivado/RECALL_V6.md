# Experimento 6 — recall do classificador de temas (`cure` / `negativas`)

Instrumento de dados. Sem veredito de qualidade — só números, listas de índices e
textos, para leitura humana.

**Escopo:** bucket `cure`/`negativas`, 50 reviews (mesmo corpus do experimento 5).
Estágio 1 (identificação de temas) **reusado** de
`resultado/experimento_local/v5/cure/negativas.json` — não foi executado de novo.
Só o estágio 2 (classificação) mudou entre variantes.

**Confirmação de execução offline:** `n_network=0` (Fetcher offline, 0 requisições de
rede) e paridade índice-a-índice confirmada entre as reviews carregadas agora e
`amostra_completa` de `resultado/experimento_local/v5/cure/negativas.json` antes de
qualquer chamada ao modelo. Todas as chamadas usaram `qwen3-espectro`, `think=false`,
timeout de 300s; nenhuma chamada precisou de retentativa (JSON válido na 1ª tentativa
em todos os lotes de todas as variantes); nenhum lote falhou.

**Temas reusados do estágio 1 (exp.5):**

| id | tema |
|---|---|
| t1 | Ritmo excessivamente lento e estático |
| t2 | Personagens planos e sem profundidade emocional |
| t3 | Atmosfera clínica fria demais |
| t4 | Diálogos artificiais e repetitivos |
| t5 | Conceito de hipnose questionado logicamente |
| t6 | Narrativa sem evolução dramática |

**Variantes:**

| variante | bloco RECALL | lote |
|---|---|---|
| V1 | sim | 25 |
| V2 | sim | 10 |
| V3 | não (controle) | 10 |

---

## 1. Tabela por variante — menções por tema

| variante | t1 | t2 | t3 | t4 | t5 | t6 | soma | soma/50 | sem nenhum tema |
|---|---|---|---|---|---|---|---|---|---|
| exp.5 (referência, lote 25, sem bloco) | 23 | — | — | — | — | — | — | — | 13 |
| V1 (bloco, lote 25) | 13 | 11 | 11 | 9 | 11 | 17 | 72 | 1.44 | 19 |
| V2 (bloco, lote 10) | 15 | 12 | 12 | 13 | 10 | 16 | 78 | 1.56 | 13 |
| V3 (sem bloco, lote 10) | 21 | 14 | 11 | 8 | 13 | 18 | 85 | 1.70 | 10 |

(A linha "exp.5" traz só o dado já conhecido de `negativas.json` para referência de
t1 e de `n_reviews_sem_tema`; os demais temas do exp.5 não fazem parte do escopo desta
tabela porque o objeto de comparação desta rodada é o recall, auditado via t1/t4.)

---

## 2. Tema t1 por variante — contagem e índices marcados

| variante | n marcadas com t1 | índices |
|---|---|---|
| V1 | 13 | 25, 27, 28, 29, 30, 31, 36, 37, 38, 43, 44, 45, 48 |
| V2 | 15 | 4, 14, 17, 18, 19, 23, 24, 25, 31, 32, 36, 37, 45, 48, 49 |
| V3 | 21 | 2, 3, 4, 8, 13, 14, 16, 17, 18, 23, 25, 26, 31, 32, 36, 37, 38, 45, 46, 48, 49 |

Referência — exp.5 (sem bloco, lote 25) marcou 23: 1, 2, 3, 4, 5, 7, 8, 9, 10, 14, 16,
17, 22, 29, 31, 32, 36, 38, 40, 41, 45, 46, 48.

---

## 3. Cruzamento com o gabarito humano

Gabarito (`AUDITORIA_PRECISAO.md`): 8 índices deveriam ter recebido tema no exp.5 e
não receberam — 6, 21, 23, 24, 26, 34, 49 para **t1**; 11 para **t4**.

### t1 — dos 7 índices-alvo (6, 21, 23, 24, 26, 34, 49)

| variante | capturados | perdidos | n capturados |
|---|---|---|---|
| V1 | — | 6, 21, 23, 24, 26, 34, 49 | 0/7 |
| V2 | 23, 24, 49 | 6, 21, 26, 34 | 3/7 |
| V3 | 23, 26, 49 | 6, 21, 24, 34 | 3/7 |

### t4 — do índice-alvo (11)

| variante | capturado? |
|---|---|
| V1 | sim (11) |
| V2 | sim (11) |
| V3 | sim (11) |

### total dos 8 índices-alvo (7 de t1 + 1 de t4)

| variante | capturados | total |
|---|---|---|
| V1 | 11 | 1/8 |
| V2 | 11, 23, 24, 49 | 4/8 |
| V3 | 11, 23, 26, 49 | 4/8 |

V2 e V3 empatam em contagem bruta (4/8), com conjuntos diferentes de índices
capturados (V2 pega 24 e perde 26; V3 pega 26 e perde 24 — 23 e 49 e o 11 de t4 são
comuns às duas). Nenhuma variante captura 6, 21 ou 34 para t1.

Critérios adicionais registrados (sem juízo de qualidade, só números já
apresentados acima, para desempate):
- t1 mais próximo da contagem-alvo humana (~30): V3 (21) > V2 (15) > V1 (13).
- Menos reviews sem nenhum tema: V3 (10) < V2 (13) < V1 (19).

Por esses dois critérios adicionais, V3 fica à frente de V2; por isso o item 7
(arquivo de auditoria) foi gerado para **V3**.

---

## 4. Checagem de negação — índice 9

Review do índice 9 diz explicitamente que o ritmo pausado NÃO é o problema dela.

| variante | marcado com t1? |
|---|---|
| exp.5 (referência) | sim (marcado — o caso que motivou este experimento) |
| V1 | não |
| V2 | não |
| V3 | não |

Nas três variantes desta rodada, o índice 9 não recebeu t1.

---

## 5. Checagem de super-marcação — quantos temas o índice 9 recebeu

| variante | temas atribuídos ao índice 9 | n temas |
|---|---|---|
| exp.5 (referência) | t1, t2, t3, t4, t5, t6 | 6 |
| V1 | t2, t3, t4, t6 | 4 |
| V2 | (nenhum) | 0 |
| V3 | t2, t3 | 2 |

---

## 6. Tempo por variante e por chamada

| variante | lotes | chamadas | tempo total (s) | tempo médio/chamada (s) |
|---|---|---|---|---|
| V1 (lote 25) | 2 | 2 | 158.15 | 79.07 |
| V2 (lote 10) | 5 | 5 | 215.98 | 43.20 |
| V3 (lote 10) | 5 | 5 | 232.22 | 46.44 |

Tempo por chamada individual:

| variante | offset 0 | offset 10 | offset 20 | offset 25 | offset 30 | offset 40 |
|---|---|---|---|---|---|---|
| V1 | 79.83s | — | — | 78.32s | — | — |
| V2 | 34.08s | 34.37s | 46.16s | — | 43.62s | 57.75s |
| V3 | 42.51s | 37.21s | 43.89s | — | 48.18s | 60.42s |

Todas as chamadas produziram JSON válido na primeira tentativa (0 retentativas, 0
ids inválidos, 0 lotes falhos) em todas as variantes.

---

## 7. Arquivo de auditoria da melhor variante

Critério do item 3: V3 (sem bloco, lote 10) — empata com V2 em índices-alvo
capturados (4/8) e vence nos dois critérios adicionais registrados (t1 mais perto do
alvo humano, menos reviews sem tema).

Arquivo gerado: `AUDITORIA_RECALL_V6_V3.md` (raiz do projeto), no mesmo formato de
`AUDITORIA_PRECISAO.md` — texto integral das 21 reviews marcadas com t1 e das 10
reviews que ficaram sem nenhum tema em V3, cada uma com um marcador de conferência
para nova leitura humana.
