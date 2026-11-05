# Guarda de quantidade — desenho, medição e critério de fluência

Data: 2026-11-05. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.

## O que é
Reescrita DETERMINÍSTICA das expressões da lista congelada do M1
(`palavras_quantidade.txt`, sha256 `a7fcd5a5…`) em `exemplo_parafraseado`, dentro de
`_construir_temas` (vale para qualquer fonte). Código: `src/espectro24/guarda_quantidade.py`
(`main`, commit `55704e2`). Remove o quantificador ou troca por forma não quantitativa
("alguns momentos" → "certos momentos"; "muitos acham" → "espectadores acham"); nunca
introduz número; nunca remove, junta ou reordena bullet. Texto sem regra segura fica
INTACTO e marcado `quantidade_pendente`. Nenhum fallback foi decidido (PROPOSTO, abaixo).

Conflito registrado: "há quem" e "parte do público" estão NA lista congelada; a guarda não
os emite (usa plurais nus), senão contariam no M1.

## Dados de desenvolvimento (decisão do dono)
Saídas da Fase 4 (treinado, base, publicado dos 30 filmes de teste, teste consumido) e o
publicado dos 60 filmes de treino. As regras foram ajustadas NESTES dados; a avaliação real
é o C22, em filmes nunca vistos.

## Medição (MEDIDO, `dev_medicao.json`)
| fonte | bullets | M1 antes | M1 depois | alterados | sem reescrita |
|---|---|---|---|---|---|
| treinado | 534 | 82,4% | 2,1% | 81,3% | 11 |
| base | 526 | 46,0% | 0,9% | 45,3% | 5 |
| publicado teste | 534 | 56,7% | 5,8% | 53,0% | 31 |
| publicado treino | 1079 | 54,8% | 3,6% | 52,8% | 39 |

Temas (`tema`): 1 ocorrência em ~2.700 — não têm o problema. `observacao_geral` tem palavra
da lista em 52–62% dos buckets (descritivo; fora do M1; decisão do dono).
Invariantes violados: 0.

## Fallback (PROPOSTO, não decidido)
Para texto pendente: nova chamada SÓ daquele bucket com reforço, aceita apenas se mantiver o
mesmo número de bullets; senão fica o texto pendente. Nenhum fallback remove bullet.

## Checagem de fluência — critério fixado ANTES de mostrar
- 30 pares antes/depois, semente **20261106**, sorteio sem reposição entre os pares
  (antes, depois) distintos que a guarda alterou nos dados de desenvolvimento;
- documento cego: só os dois textos; sem fonte, filme nem regra;
- pergunta: "o texto reescrito está correto em português e diz a mesma coisa? S/N";
- **passa com ≥ 27 de 30 `S`. Se reprovar, PARA**: nenhum ajuste da guarda sobre o mesmo
  conjunto; novo conjunto exigiria novo sorteio e novo registro.
- Limite: sorteio uniforme sobre textos, então regras raras ficam sub-representadas.
