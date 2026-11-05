# RESULTADO DA FASE 4 — avaliação final do TREINADO

Data: 2026-11-05. Pré-registro: `PREREGISTRO_AVALIACAO.md` (sha256 `4e9d61b6…`), com
`DESVIO_P01` (amostragem), `DESVIO_P02` (prova de fusão da base), `DESVIO_P03` (τ do M2) e
`DESVIO_P04` (estrutura impossível de `temas` = JSON inválido). Gate da Fase 2: `275ca16`,
aprovado pelo dono em 04/11/2026. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.

## Resumo para o tech lead

- **O que foi testado:** um Qwen3-8B com LoRA (fine-tune da SÍNTESE: os temas e exemplos de cada
  bucket de reviews), contra a síntese publicada (DeepSeek) e contra o mesmo Qwen3-8B sem treino
  (base), em 30 filmes de teste e 89 buckets, uma única vez, com critérios e limiares
  pré-registrados antes de qualquer medição no teste.
- **Resultado:** o treinado **não passa**. Em qualidade percebida e especificidade ele
  fica no nível do publicado (C5, C6) e valida o formato (C4). Reprova no excesso de
  palavras de quantidade (C3, +25,7 pp) e, por 0,26 pp no IC, na taxa de bullets sem apoio nas
  reviews (C1).
- **A base também não passa** C1 a C4. Nenhum dos dois modelos locais substitui o publicado como
  está.
- **Causa do C3 (MEDIDO):** os alvos de treino têm 54,8% de exemplos com palavra de quantidade
  (591/1.079, publicado dos filmes de treino); o treinado gerou 82,4% no teste. Ele **amplificou**
  o padrão (+27,6 pp sobre o alvo), não o copiou. O porquê não foi investigado.
- **Próxima fase:** ver "Opções para a próxima fase" no fim (PROPOSTO, não decidido).

## Contexto (do `FINETUNE_REGISTRO.md`)

- Base: `unsloth/Qwen3-8B` (bnb-4bit para o treino), Unsloth 2026.10.7, T4 no Kaggle.
- Treino (Fase 3, MEDIDO): LoRA r 16, alpha 16, nas 7 projeções; **140 exemplos de treino e 19
  de validação**; 3 épocas, 105 passos, 3,66 h; checkpoint da época 2 (eval_loss 0,5492; a
  época 3 deu 0,5567, diferença pequena numa amostra de 19). GGUF Q4_K_M de 5,03 GB; só as 252
  projeções diferem da base (conferido nos tensores).
- Avaliação: Windows com Ollama (geração e juiz `gpt-oss:20b` v2.2 congelado); contas no Mac.
  Entradas de um commit fixo de `main` (`742cfe3`, 162 arquivos).
- Fase 1 (especificidade): a medida automática (M-disp) foi **negativa** e saiu; no lugar entrou a
  rotulagem cega do dono (C5).
- Fase 2 (gate): publicado e base medidos no teste antes de gerar o treinado; δ₂ fixado em
  7,8 pp. Aprovado pelo dono em 04/11/2026.

## Decisão

**NÃO PUBLICÁVEL (MEDIDO).** A decisão exigia C1 a C6 todos passando. **C1 e C3 falham.**
C2, C4, C5 e C6 passam.

| critério | resultado | limiar pré-registrado | veredito |
|---|---|---|---|
| C1 sem apoio | T − P = +1,3 pp, IC 95% [−1,5; +4,3] | sup. < +4,0 **e** pontual ≤ +2,0 | **FALHA** (sup. 4,26 ≥ 4,0; o pontual passa) |
| C2 apoio ≥ 2 | +0,2 pp, IC [−3,2; +3,7] | inf. > −7,8 (δ₂) | passa |
| C3 M1, palavras de quantidade | **+25,7 pp**, IC [+19,1; +32,2] | sup. < +10,0 | **FALHA** |
| C4 JSON e validadores | 89/89 buckets | ≥ 87 | passa |
| C5 especificidade (dono) | E do treinado 18/60 = 30%, Wilson [19,9; 42,5] | ≥ 10% | passa |
| C6 leitura cega (dono) | treinado publicável em 5/5 | ≥ 4 de 5 | passa |

Conjunto: 30 filmes, **89 buckets**, nenhum fora por memória. Bootstrap por filme, 10.000
reamostras, semente 20261101; juiz `44606cf1…`, parada no 2º sim; δ₂ = 7,8 pp.

### Por que cada falha
- **C3 (clara):** o treinado usa palavra de quantidade em 82,4% dos exemplos
  (`exemplo_parafraseado`), contra 56,7% do publicado e 46,0% da base. O extremo inferior do IC
  (+19,1 pp) já está duas vezes acima do limite de +10 pp. Não é questão de poder estatístico.
- **C1 (por pouco):** o treinado tem 26/534 bullets sem apoio (4,9%), contra 19/534 (3,6%) do
  publicado. A estimativa pontual (+1,3 pp) passa o teto de +2,0 pp, mas o limite superior do
  IC (+4,26 pp) passa 0,26 pp do limite de +4,0. O IC inclui zero. A margem de 4,0 pp é um
  limite de poder, não uma tolerância de produto (pré-registro, C1). O critério é binário e
  não foi relaxado.

## C1 a C4 — números (MEDIDO)

| métrica | publicado | base | treinado |
|---|---|---|---|
| C1 sem apoio | 19/534 = 3,6% | 36/526 = 6,8% | 26/534 = 4,9% |
| C2 apoio ≥ 2 | 457/534 = 85,6% | 436/526 = 82,9% | 458/534 = 85,8% |
| C3 M1 | 56,7% | 46,0% | 82,4% |
| C4 final (com retentativa) | 89/89 | 89/89 | 89/89 |
| C4 na 1ª tentativa | n/d | 89/89 | **86/89** |

Os 3 buckets do treinado que precisaram de 2 chamadas (de 89; 1 chamada em 86) são os que a
1ª tentativa reprovou. Indeterminados no juiz: 0 nos três lados.

## C5 — especificidade (MEDIDO, rótulos do dono)

| lado | E | n | proporção | Wilson 95% |
|---|---|---|---|---|
| treinado | 18 | 60 | 30,0% | [19,9; 42,5] |
| publicado | 24 | 60 | 40,0% | [28,6; 52,6] |

- Por bucket (negativas/medianas/positivas): treinado 6/5/7; publicado 4/9/11.
- Consistência dos 6 repetidos: **6 de 6 iguais**.
- O dono resolveu a única divergência entre suas notas e o arquivo (F070) como E antes da
  avaliação. Rótulos em `fase4/rotulos_especificidade.csv`.
- Limitações (pré-registro): o Wilson trata os bullets como independentes (ignora o
  agrupamento por filme); o estilo pode denunciar o lado.

## C6 — leitura cega (MEDIDO, dono)

- Treinado publicável em **5/5** filmes; o publicado também em 5/5.
- "Melhor" (descritivo): publicado em 2 (Anatomia de uma Queda, A Substância), empate em 3
  (Incêndios, mãe!, Napoleão); o treinado não foi preferido em nenhum.
- Na coluna `publicaria`, o dono disse que publicaria A e B em todos os filmes, e foi registrado
  `ambos` nos 5. A frase seguinte ("considere melhor como publicaria") era ambígua; foi lida
  como "mantenha a coluna melhor como está". Como o critério é ≥ 4 de 5 e o dono declarou os
  dois lados publicáveis em todos, o C6 passa nessa leitura; a outra leitura (só o vencedor)
  não foi aplicada.
- O critério não discrimina aqui: os dois lados passam em tudo. A leitura mostra paridade de
  qualidade percebida, não vantagem.

## Descritivos (não decidem)

**Treinado × base (T − B):** C1 sem apoio −2,0 pp [−5,2; +1,2]; C2 apoio ≥ 2 +2,9 pp
[−1,9; +8,1]; M1 **+36,4 pp** [+30,8; +42,2]. Nenhum IC de C1/C2 exclui zero.

**Base × publicado (achado pré-registrado):** a base NÃO satisfaz C1 a C4 (C1 +3,3 pp
[+0,4; +6,5] reprova; C2 −2,7 pp [−7,8; +2,1] reprova por 0,03 pp; C3 e C4 passam).

**M2 (τ = 0,963, DESVIO_P03, `mencoes_aproximadas` × publicado, 89 buckets):**

| | treinado | base |
|---|---|---|
| temas do publicado pareados | 174/534 = 32,6% | 114/534 = 21,3% |
| DAM em reviews | 4,85 | 5,47 |
| DAM relativa (fração de n) | 12,4% [10,9; 14,0] | 14,0% [11,8; 16,5] |
| tau-b, mediana (buckets com tau-b) | 0,667 (31) | 0,333 (15) |

Treinado − base na DAM relativa: −1,6 pp [−4,4; +1,1]. Poucos temas pareiam (o e5 comprime os
cossenos; ver `DESVIO_P03`).

**Tempos (MEDIDO, por bucket, em segundos de parede):** treinado soma 4,83 h, mediana 176 s
(118 a 1.017); base soma 3,96 h, mediana 154 s (88 a 495). Geração do treinado: 5 paradas da
guarda de RAM, todas refeitas na rodada seguinte; nenhum bucket fora por memória. Juiz do
treinado: 1 pausa pela guarda de latência, retomada.

## Desvios e incidentes desta fase

- `DESVIO_P03` (τ = 0,963, só treino); `DESVIO_P04`: o treinado devolveu uma vez JSON válido
  com `temas` de inteiros (`anatomy-of-a-murder/medianas`), que estourava o código de produção
  e parou a série. A resposta crua se perdeu. A regra passou a ser "estrutura impossível =
  JSON inválido" (1 nova chamada; senão falha), em `gerar_sintese_teste.py` e na descrição da
  1ª tentativa; a base não muda (0 diferenças em 89 tentativas). Duas correções minhas no
  caminho (recursão no parse estrito; cópia da regra faltando em `bucket_da_1a_tentativa`).
- **Quebra parcial da cegueira antes dos critérios do dono:** a saída do `git pull` de 04/11
  listou as linhas de cada arquivo da síntese do treinado (quase todos 136; 3 com 149 e 1 com
  137; eu disse "cinco e um" ao dono na hora, por engano). Indicava buckets com 2ª chamada, que é a validade na 1ª tentativa (descritiva). Não
  mostrou C1–C4, M1, M2 nem taxa do juiz. Os rótulos do C5 e a leitura do C6 foram feitos sobre
  documentos que só trazem id e texto.
- A leitura do C6 e os "melhor" foram ditos ao Claude pelo chat em vez de preenchidos no CSV.

## O que NÃO foi medido

- Qualquer efeito do treino fora dos 89 buckets de teste e dos 30 filmes.
- **Por que** o treinado amplifica as palavras de quantidade. MEDIDO: alvo 54,8% → treinado
  82,4% (a diferença não vem de os alvos terem muita quantidade). Não se testou nenhuma
  hipótese (poucos exemplos, 3 épocas, temperatura 0,7, algo no prompt).
- Variação entre gerações do treinado: uma geração por bucket, seed fixa (o pré-registro proíbe
  uma 2ª no teste).
- Se o C1 reprovaria com outra amostra de filmes: o IC cobre o limite por 0,26 pp.
- A resposta crua da 1ª ocorrência da estrutura impossível (perdida).
- Qualquer leitura de publicabilidade além dos 5 filmes de referência.
- A estabilidade do rótulo do dono além dos 6 repetidos (todos consistentes).
- O desempenho em produção: tempo, custo e comportamento no servidor.
- A prosa (narrativa e veredito): saiu do produto por decisão do dono e nunca foi avaliada.

## Arquivos (sha256)

- `fase4/cego/c1_c4_fase4.json` `b23ac199…`; `fase4/cego/m2_fase4.json` `b9d1df89…`
- `fase4/especificidade_resultado.json` `0b1be275…`; `fase4/leitura_resultado.json` `7c96b990…`
- Scripts em `main` até `33db25d`.

## Opções para a próxima fase (PROPOSTO, nada decidido)

O conjunto de teste foi consumido: o pré-registro proíbe uma 2ª geração do treinado nele.
Qualquer nova rodada é um experimento novo, com pré-registro novo e filmes que ainda não
tenham sido vistos.

1. **Atacar o C3 no treino.** Hipóteses a medir ANTES de retreinar (cada uma barata, em
   treino/validação): filtrar ou rebalancear exemplos com palavra de quantidade; menos épocas;
   mais dados (hoje 140 exemplos). O C1 passaria a ser o próximo ponto fraco (26/534 contra
   19/534).
2. **Mudar o critério de produto, não o modelo:** se palavras de quantidade são tolerável, o C3
   deixa de decidir; isso é decisão do dono e exigiria reabrir o pré-registro (não deste teste).
3. **Parar a frente local** e manter o DeepSeek: o treinado empata em qualidade percebida e não
   a supera; custo e latência locais não foram medidos como ganho.

Recomendação do assistente (sem peso de decisão): 1, começando pela medida do porquê do C3,
porque é a única falha clara e é barata de diagnosticar no treino.
