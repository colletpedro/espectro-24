# Parte 3 — o juiz contra o rótulo do dono

**O JUIZ FALHOU — o resultado da Parte 2 NÃO VALE**: precisão 0.727 < 0.8

Critério (fixado antes do rótulo): precisão ≥ 0.8 e recall ≥ 0.8. Positivo = "menciona".

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] | acurácia |
|---|---|---|---|---|---|---|---|---|
| todos | 40 | 24 | 9 | 1 | 6 | 0.727 [0.558, 0.849] | 0.96 [0.805, 0.993] | 0.75 |
| publicado | 20 | 13 | 3 | 1 | 3 | 0.812 [0.57, 0.934] | 0.929 [0.685, 0.987] | 0.8 |
| local | 20 | 11 | 6 | 0 | 3 | 0.647 [0.413, 0.827] | 1.0 [0.741, 1.0] | 0.7 |

Com 40 pares os intervalos são largos; a diferença entre os lados importa porque um juiz que erra mais num lado enviesa a comparação.

## Erros do juiz

- P03 (local, the-substance/positivas): dono não, juiz sim — tema "dualidade entre personagens e identidade"
- P04 (local, mother-2017/medianas): dono não, juiz sim — tema "confusão e falta de clareza"
- P11 (publicado, the-substance/positivas): dono sim, juiz não — tema "Body horror extremo e efeitos práticos"
- P13 (local, napoleon-2023/medianas): dono não, juiz sim — tema "Interpretação do personagem insatisfatória"
- P15 (local, napoleon-2023/positivas): dono não, juiz sim — tema "Abordagem do personagem Napoleão"
- P31 (local, anatomy-of-a-fall/negativas): dono não, juiz sim — tema "diálogos longos e repetitivos"
- P32 (local, the-substance/positivas): dono não, juiz sim — tema "horror corporal e efeitos visuais extremos"
- P34 (publicado, anatomy-of-a-fall/negativas): dono não, juiz sim — tema "História sem profundidade"
- P36 (publicado, incendies/medianas): dono não, juiz sim — tema "Ritmo lento e momentos arrastados"
- P39 (publicado, the-substance/positivas): dono não, juiz sim — tema "Direção e estilo visual marcantes"
