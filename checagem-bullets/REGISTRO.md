# Checagem de apoio dos bullets — publicado (DeepSeek) × local (qwen3:14b)

**Pergunta.** Cada bullet da síntese afirma que um tema aparece nas reviews de
um grupo. Ele tem apoio nas reviews DAQUELE grupo (as mesmas 40 que alimentaram
a síntese) ou foi inventado/inflado? Só os bullets: no publicado são do
DeepSeek. Nenhuma chamada paga. Código: `scripts/checagem_bullets.py` e
`scripts/encoder_e5.py` (em `main`, `bec03e4`).

5 filmes: anatomy-of-a-fall, incendies, mother-2017, napoleon-2023,
the-substance. 90 bullets por lado, 600 reviews (40 × 3 grupos × 5), a mesma
seleção nos dois lados.

## Estado (2026-10-19)

| parte | estado | arquivos |
|---|---|---|
| 1a — eixo no consenso (sem modelo) | **feita** | `parte1_eixo.{json,md}` |
| 1b — recuperação por embedding local | **feita** | `parte1_recuperacao.{json,md}` |
| 2 — juiz qwen3:14b | **entrada pronta; falta rodar no Windows** (`docs/SETUP_WINDOWS.md` §10) | `juiz_entrada.jsonl`, `juiz_estimativa.md` → `juiz_saida.jsonl` |
| 3 — validação do juiz | **documento pronto; falta o rótulo do dono** | `rotulagem/rotulagem_dono.md`, `rotulagem/rotulos_dono.csv`, `mapa/rotulagem_mapa.json` |
| resultado final | depois de 2 e 3 | `validar-juiz` → `relatorio` |

## Parte 1a — o que saiu

| lado | bullets | sem eixo (livre) | suspeitos (eixo em ≤ 1 review) | declarado > reviews com o eixo |
|---|---|---|---|---|
| publicado | 90 | 3 | **0** | 21 |
| local | 90 | 2 | **0** | 14 |

A contagem foi refeita do consenso (`consenso_verificado.jsonl`, restrito à
amostra analisada) e conferida contra o bloco `eixos` publicado em 300 células,
sem divergência.

**A medida grosseira não separa os lados e não pega os bullets que a leitura
humana apontou.** "atuações insuficientes" (local, negativas de Anatomia) cai
em `atuacao`, que aparece em 14/40 reviews; "direção e estética visual fraca"
cai em `direcao_imagem`, 7/40. O eixo junta elogio e crítica do mesmo assunto,
então "tem o eixo" não diz "diz o tema". É o resultado esperado de uma régua
larga, registrado como tal: ela só flagraria um bullet sobre assunto que
ninguém no grupo menciona, e nenhum dos 180 é assim.

## Parte 1b — o que saiu

Modelo: `intfloat/multilingual-e5-base`, local, forward em numpy; justificativa
em `scripts/encoder_e5.py` (recuperação assimétrica, translíngue, já no disco).
Reviews em janelas de até 900 caracteres (691 pedaços, nenhum truncado).

**Centralização, medida antes de adotada.** Sem centrar, poucas reviews
genéricas na língua das queries dominavam o top-5 (156 reviews distintas em
435 posições do lado publicado). Sinal independente do embedding: a fração do
top-5 que tem o eixo do bullet, contra a fração do grupo (o acaso):

| variante | publicado | local |
|---|---|---|
| sem centrar, query = tema + descrição | 54,7% (lift 1,27) | 57,3% (1,24) |
| sem centrar, query = só o tema | 54,5% (1,26) | 58,2% (1,26) |
| centrado nos 180 bullets dos dois lados | 69,2% (1,61) | 67,7% (1,47) |
| **centrado nos 1.780 bullets publicados do catálogo (adotada)** | **68,0% (1,58)** | **64,8% (1,40)** |
| acaso | 43,1% | 46,1% |

Ficou a referência do catálogo: quase o mesmo ganho, e não muda quando o modelo
avaliado muda (é a régua do fine-tuning). O eixo é polaridade-cego, então isto
compara variantes; não diz que a recuperação acerta. Exemplo do efeito: em
"Mistura de idiomas incomoda" (publicado), o top-5 passou de reviews genéricas
em português para quatro reclamações reais da mistura francês/inglês.

O que a recuperação já mostra, sem juiz: para "atuações insuficientes" as
reviews mais parecidas dizem *"Great acting"* e *"acting was decent"* — o
assunto certo, com o juízo oposto. É o caso que o critério do juiz manda
responder **não**.

## Parte 2 — preparada

900 chamadas (450 por lado), uma por par bullet × review, resposta
`{"menciona": bool}` forçada por schema, `think=false`, sequencial e retomável.
**~89 min estimados (faixa 67–179)**, a partir das velocidades do qwen3:14b
medidas no gate deste notebook — estimativa, não medição.

## Parte 3 — preparada

40 pares sorteados (semente 20261019): 20 por lado, 4 por filme por lado,
metade dos ranks 1-2 e metade dos 3-5, no máximo um par por bullet, ordem
embaralhada. O documento não mostra lado, modelo, similaridade, rank nem
resposta do juiz; o mapa fica em `mapa/` com selo sha256 impresso no rodapé
do documento (`bc592ee9…`).

**Critério para o juiz valer, fixado antes do rótulo** (proposta do código,
`CRITERIO_JUIZ`): precisão ≥ 0,8 **e** recall ≥ 0,8 nos 40 pares. Se o dono
quiser outro, trocar ANTES de rotular. Reprovado o juiz, `relatorio` gera os
números com o aviso "ESTE RESULTADO NÃO VALE" no topo.

## Limites conhecidos

- O apoio do juiz tem **teto de 5** (5 reviews por bullet): um bullet que
  declara 25 menções não pode mostrar mais que 5. O quantificador ("muitas",
  "várias") é comparado contra esse teto, não contra a contagem real.
- O juiz é o mesmo modelo que escreveu um dos lados (qwen3:14b). A validação da
  Parte 3 mede o erro dele nos dois lados separadamente para isso aparecer.
- A recuperação pode deixar de fora a review que sustenta o bullet; "sem apoio"
  quer dizer "sem apoio nas 5 mais parecidas".
