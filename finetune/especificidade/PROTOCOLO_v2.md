> **Genérico = este bullet, como está escrito, poderia aparecer quase sem mudança em muitos filmes diferentes. Específico = diz algo que só vale para este filme ou para poucos.**

# Protocolo PRÉ-REGISTRADO v2 — especificidade do BULLET COMPLETO (Fase 1)

Data: 2026-10-30. Commitado ANTES de gerar o documento de rotulagem e antes de
qualquer rótulo da v2. Vem do `DESVIO_01.md` (commit `2440345`). O protocolo
v1 (`PROTOCOLO.md`, commit `fe7d7a02`) vale em tudo o que não for alterado
aqui. Nada aqui é revisto depois de ver os rótulos da VALIDAÇÃO.

Classe positiva: G = 1. Nenhum LLM nesta fase. Nenhum filme de teste em
estágio nenhum.

## Unidade

**Bullet completo = `tema` + " — " + `exemplo_parafraseado`** (cada um sem
espaços nas pontas), no formato da leitura cega anterior. Campos:

- `tema`: `frontend/js/filme.js:1781`; `src/espectro24/models.py:94`;
- `exemplo_parafraseado`: `frontend/js/filme.js:1819–1837` ("Aprofundar");
  `src/espectro24/models.py:97`.

FORA: `mencoes_aproximadas` e `n_reviews_analisadas`
(`models.py:95–96`), a barra e o "cerca de X de N" (`filme.js:1768`,
`1785–1793`), as marcas do código (`mencoes_clampadas`,
`mencoes_valor_original`, `aspas_removidas`) e o nome do bucket. Nomes próprios
dentro do texto FICAM. Algarismos que estiverem dentro do texto ficam no texto
(não são as contagens); o M-anc já os ignora (só sequências de letras).

## Código e referência congelados

- Código: `scripts/finetune/especificidade_bullet.py`, sha256
  `ff71747ed39830ee7af84f4de6c58ff4a0a04fd2f963cc12a5d472b4545e901f`
  (`main`, commit `50522eb62a72577033ef29d0e609417ab4c0a32f`). Ele importa,
  SEM ALTERAÇÃO, `scripts/finetune/especificidade.py` (sha256 `7d40e620…`, o
  do v1): `Disp`, `m_anc`, `vocabulario_das_reviews`, `palavras_de_conteudo`,
  `auc_ponderada`, `youden`, `logistica`. O mapa grava os dois sha256.
- Referência: `finetune/especificidade/referencia_bullets.jsonl`, sha256
  `da8723a62ebf8de16b8344e1e73a0891cc64bb4c76505a7046ddcd963de54522` — os
  MESMOS 1.223 bullets da referência de títulos (68 filmes; 1.079 de TREINO,
  144 de VALIDAÇÃO; sem o bucket do Gemini; sem os filmes excluídos no gate 0;
  sem teste; sem saída de modelo), agora com o exemplo e o texto completo.
- e5: com o prefixo `query: `, **nenhum** dos 1.223 textos passa de 512
  tokens (máximo 97, mediana 49): **0 truncados**.

## Medidas (mesma forma do v1, sem ajuste)

- **M-disp**: idêntica ao v1, sobre o texto do bullet completo (e5
  `multilingual-e5-base`, `query:` nos dois lados, correção de viés pelo
  deslocamento, máximo por OUTRO filme, média dos k = 10 maiores; alto = G).
- **M-anc**: a mesma fórmula, aplicada às palavras de conteúdo do bullet
  completo (título + exemplo). Consequência declarada, não corrigida: com mais
  palavras, o máximo tende a subir.
- **M-comb**: a mesma logística ponderada, sem penalização, com M-disp e M-anc
  padronizados.
- Orientação fixa: score de G = M-disp; = −M-anc; = prob. da M-comb.

## Calibração

- **Pool elegível**: os 1.079 bullets de TREINO da referência menos qualquer
  bullet cujo título esteve na amostra de títulos arquivada: pelo id (80) ou
  pelo mesmo título normalizado (minúsculas, sem acento, espaços colapsados;
  mais 53). **Pool = 946.** Limitação declarada: a exclusão por texto tira os
  títulos que se repetem entre filmes, que tendem ao genérico; os pesos
  representam o pool elegível, não todo o treino.
- **80 bullets**, 20 por quartil de M-disp no pool elegível (quartil pela
  posição na ordem (valor, id); empates desfeitos pelo id), semente
  **20261030**. Os valores de M-disp não saem do código: o mapa guarda só o
  quartil.
- **10 repetidos**, sorteados entre os 80 (mesma semente), cada um a ≥ 40
  posições do original. Medem a consistência do dono; não entram no ROC.
- Pesos: w_q = (bullets do quartil q no pool elegível) / 20.
- Limiar: Youden (máx TPR − FPR) no ROC ponderado. A M-comb é ajustada nos
  mesmos itens. Congelados em `finetune/especificidade/limiares_v2.json`,
  escrito UMA vez.

### Contingência (pré-registrada)

- Conta-se o número de itens **E distintos** entre os 80 (o rótulo da 1ª
  ocorrência; os repetidos não contam duas vezes). É a ÚNICA conta permitida
  antes dos limiares; nenhuma medida é calculada para ela.
- **Se E < 15**: a calibração é declarada **sem poder**, e um **lote extra de
  40** bullets de TREINO é rotulado ANTES de fixar os limiares:
  - frame: o pool elegível menos os 80 já sorteados;
  - estratos: quartis de M-anc no pool elegível inteiro (posição na ordem
    (valor, id)); quartil 4 = M-anc mais alta = mais específico;
  - alocação **5 / 5 / 10 / 20** (quartis 1 / 2 / 3 / 4: o mais específico
    sobreamostrado), semente **20261031**, sem repetidos;
  - documento cego no mesmo formato, ids `X01…X40`.
- Pesos com o lote extra: w = 1 / P(inclusão), com
  P = π1 + (1 − π1)·π2, π1 = 20 / N_q(M-disp) e π2 = n_q / N'_q(M-anc) no
  frame do lote extra. Aproximação declarada: a condição do lote extra (poucos
  E) não entra na probabilidade. Esses pesos entram no Youden, na AUC e na
  M-comb.
- Se, mesmo com o lote extra, houver < 15 E, a calibração segue com o que há e
  o relatório diz "poder baixo". Não há terceiro lote.

## Documento cego

- `docs/arquivo-de-estudos/finetune-fase1/rotulagem_calibracao_v2.md`, fora do
  git, com `rotulos_calibracao_v2.csv` em branco ao lado.
- Mostra só o id (`B01…`) e o bullet completo (título em negrito + " — " +
  exemplo). Nada de filme, bucket, fonte, medida ou estrato. A definição em uma
  linha fica no topo.
- O mapa id→item fica em `finetune/especificidade/mapa/calibracao_v2_mapa.json`;
  o selo (sha256) é impresso no fim do documento; o mapa não é mostrado ao dono.

## Validação (montada numa rodada FUTURA, depois da escolha do modelo base)

A mesma do v1, com a unidade trocada:

- 60 bullets completos NOVOS, semente **20261022**:
  - 30 publicados: 15 de filmes de VALIDAÇÃO e 15 de TREINO fora da
    calibração v2, fora da amostra de títulos arquivada e fora das exclusões
    por título;
  - 30 gerados pelo modelo base ESCOLHIDO, sem treino, nos 5 filmes de TREINO
    de `validacao_filmes.json`, com título E exemplo
    (`gerar_titulos_base.py` terá de gravar o exemplo: adaptação futura, não
    feita aqui);
  - mais 6 repetidos.
- Os limiares congelados da calibração são aplicados sem mudança.

**Critério de aceite (inalterado):** AUC ≥ 0,80 (IC 95% por bootstrap POR
FILME, 10.000 reamostras); acurácia balanceada ≥ 0,75 no limiar congelado;
|acurácia balanceada (publicados) − acurácia balanceada (locais)| ≤ 0,15. Entre
as aprovadas, a mais simples: **M-disp < M-anc < M-comb**. Teto, resultado
negativo e proibição de rever limiar ou fórmula: como no v1.

## Rótulos de títulos

Os 90 rótulos de títulos (77 G, 13 E) estão arquivados (`DESVIO_01.md`) e não
entram em nada: nem calibração, nem validação, nem consistência.
