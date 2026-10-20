# Protocolo PRÉ-REGISTRADO — medida de especificidade do título do bullet (Fase 1)

Data: 2026-10-20. Commitado ANTES de gerar o documento de rotulagem e antes de
qualquer rótulo. Nada aqui é revisto depois de ver os rótulos da VALIDAÇÃO.

## Objetivo e definição

Uma medida, calculada por código, que separe bullet GENÉRICO de ESPECÍFICO e
funcione nas saídas de modelo local (a régua de fidelidade não pega bullet
genérico). Unidade: o TÍTULO do bullet (`tema`), como no juiz de fidelidade.

> **GENÉRICO (G)** = o título caberia, sem mudança, em bullets de muitos
> filmes diferentes; **ESPECÍFICO (E)** = só faz sentido para este filme ou
> para poucos.

Classe positiva: G = 1. Nenhum LLM nesta fase.

## Código e referência congelados

- Código: `scripts/finetune/especificidade.py`, sha256
  `7d40e6202ab1821cce0afa02ce2291f6097c430e8f6b590607f1b9881b38f316`
  (`main`, commit `a3807be4ecf582875e7d899e111c724d3df39068`). O sorteio grava
  esse sha256 no mapa; a calibração e a validação rodam com o mesmo arquivo.
- Referência: `finetune/especificidade/referencia.jsonl`, sha256
  `92e4f2f0e98c63ee62c6310338181ec66921fcde6b08112e05bcd190156fcb44` —
  1.223 títulos publicados de 68 filmes (1.079 de TREINO, 144 de VALIDAÇÃO),
  sem o bucket do Gemini e sem os filmes excluídos no gate 0. Nunca contém
  filme de teste nem saída de modelo. Toda medida é calculada contra ela,
  SEMPRE sem o próprio filme do item.

## Medidas (no máximo 3, forma fixa)

**M-disp — dispersão entre filmes (alto = genérico).** Escolhida a forma "média
dos k maiores", não a contagem acima de τ: a contagem exigiria um segundo
parâmetro livre (τ) ajustado nos mesmos 80 rótulos, e é discreta; a média dos
k maiores é contínua e só tem k, fixado aqui.
- e5 `intfloat/multilingual-e5-base` (o snapshot do juiz), prefixo `query: `
  nos DOIS lados (comparação simétrica título × título), vetores normalizados.
- Correção de viés, como no juiz (centrar pelo deslocamento do item de
  referência): s(t,u) = cos(t,u) − d_F(u), com d_F(u) = média de cos(v,u)
  sobre os títulos v da referência fora do filme de u e do filme F do item.
- Para cada filme G ≠ F da referência: s_G = máx_{u ∈ G} s(t,u) (um filme
  conta uma vez, mesmo com vários títulos parecidos).
- **M-disp(t) = média dos k = 10 maiores s_G.** k = 10 ≈ 15% dos 67 outros
  filmes: o "muitos filmes diferentes" da definição, fixado antes dos dados.

**M-anc — ancoragem lexical (alto = específico).**
- Palavras de conteúdo do título: minúsculas, sem acento, sequências de
  letras com ≥ 4 letras, fora da lista de stopwords do código.
- Vocabulário de reviews de cada filme da referência: as reviews ANALISADAS
  (a amostra de 40 por bucket que a síntese leu, `amostra_do_bruto` com a
  `coleta` publicada), minúsculas e sem acento.
- Para o título t do filme F: N = filmes da referência fora de F;
  df(w) = quantos deles têm w; idf(w) = ln((N + 1)/(df(w) + 1));
  presente_F(w) = 1 se w está nas reviews analisadas de F.
- **M-anc(t) = máx_w presente_F(w) · idf(w)** (0 se não há palavra de
  conteúdo). Limitação declarada: títulos em português, reviews em várias
  línguas — o casamento é exato; pegam nomes próprios e termos que se repetem
  entre línguas.

**M-comb.** Regressão logística ponderada (pelos pesos dos estratos), sem
penalização, com exatamente M-disp e M-anc padronizados (média e desvio da
calibração). Score = probabilidade de G.

**Orientação fixa (não se inverte depois de ver dados):** score de G = M-disp;
= −M-anc; = prob. da M-comb. Classifica G quando o score ≥ limiar.

## Calibração (rótulos do dono; aqui se escolhem os limiares)

- 80 títulos publicados de filmes de TREINO, estratificados por quartil de
  M-disp no pool de treino (os 1.079 títulos de treino da referência): 20 por
  quartil, semente **20261021**.
- Mais 10 repetidos, sorteados entre os 80 (mesma semente), cada um inserido a
  ≥ 40 posições do original: medem a consistência do dono e NÃO entram no ROC.
- Pesos dos estratos: w_q = (títulos do quartil q no pool) / 20.
- Limiar de cada medida: Youden (máx TPR − FPR) no ROC ponderado. A M-comb
  é ajustada aqui, nos mesmos 80. Reportados: AUC ponderada de calibração
  (otimista por construção), limiar, TPR, TNR, acurácia balanceada.
- Congelados em `finetune/especificidade/limiares.json`, escrito UMA vez
  (o código recusa reescrever).
- Documento cego: só id e título; nada de filme, bucket, fonte, medida ou
  estrato. Nenhuma medida é calculada nem exibida sobre os itens sorteados
  antes de os rótulos voltarem (o M-disp do pool serve só para o quartil, que
  vai para o mapa, sem os valores).

## Validação (montada numa rodada FUTURA, depois da escolha do modelo base)

- 60 títulos NOVOS, nenhum repetido da calibração, semente **20261022**:
  - 30 publicados: 15 de filmes de VALIDAÇÃO e 15 de títulos de TREINO fora
    da calibração;
  - 30 gerados pelo modelo base ESCOLHIDO, sem treino, nos 5 filmes de
    TREINO de `validacao_filmes.json` (seletor com a semente acima; comando
    `scripts/finetune/gerar_titulos_base.py`), sorteados entre os títulos
    gerados;
  - mais 6 repetidos (consistência).
- Os limiares congelados da calibração são aplicados sem mudança.

**Critério de aceite (a medida passa se cumprir TODOS):**
1. AUC ≥ 0,80 na validação, com IC 95% por bootstrap POR FILME (10.000
   reamostras) reportado;
2. acurácia balanceada ≥ 0,75 no limiar congelado;
3. |acurácia balanceada (publicados) − acurácia balanceada (locais)| ≤ 0,15.

Entre as aprovadas, fica a mais simples: **M-disp < M-anc < M-comb**.

**Teto:** a consistência do dono nos repetidos (calibração e validação) é
reportada. Se < 0,80, o relatório diz que o critério pode estar acima do
alcançável — sem mudar o critério.

**Negativo:** se nenhuma medida passar, o resultado negativo é registrado e a
especificidade fica coberta só pela leitura cega da Fase 4. Um juiz LLM de
especificidade só numa rodada própria, por decisão do dono.

**Proibido:** rever limiar ou fórmula depois de ver os rótulos da validação.
