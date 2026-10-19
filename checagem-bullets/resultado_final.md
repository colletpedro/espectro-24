# Resultado final — apoio dos bullets nas reviews do próprio grupo

> **ESTE RESULTADO NÃO VALE.** O juiz falhou na validação contra o rótulo do dono (precisão 0.727 < 0.8). Os números abaixo estão aqui só para auditoria; nenhuma conclusão sobre os bullets pode sair deles.

Apoio = o juiz disse "menciona" para a review. Cada bullet foi julgado contra as 5 reviews do grupo mais parecidas com ele, então o apoio vai de 0 a 5: **o teto é 5**, e um bullet que declara 25 menções não tem como mostrar mais que 5 aqui.

| lado | bullets | apoio ≥ 1 | apoio ≥ 2 | sem apoio |
|---|---|---|---|---|
| publicado | 90 | 90 (100%) | 85 (94%) | 0 |
| local | 90 | 88 (98%) | 82 (91%) | 2 |

## Por filme

| filme | lado | bullets | apoio ≥ 1 | apoio ≥ 2 | sem apoio |
|---|---|---|---|---|---|
| Anatomia de uma Queda | publicado | 18 | 100% | 94% | 0 |
| Anatomia de uma Queda | local | 18 | 89% | 78% | 2 |
| Incêndios | publicado | 18 | 100% | 83% | 0 |
| Incêndios | local | 18 | 100% | 94% | 0 |
| mãe! | publicado | 18 | 100% | 100% | 0 |
| mãe! | local | 18 | 100% | 94% | 0 |
| Napoleão | publicado | 18 | 100% | 94% | 0 |
| Napoleão | local | 18 | 100% | 100% | 0 |
| A Substância | publicado | 18 | 100% | 100% | 0 |
| A Substância | local | 18 | 100% | 89% | 0 |

## Bullets sem apoio nenhum

### publicado — DeepSeek (síntese publicada)

_(nenhum)_

### local — qwen3:14b (Ollama)

- **Anatomia de uma Queda / negativas: atuações insuficientes** — "Alguns espectadores consideraram as atuações pouco convincentes, com destaque apenas para alguns personagens secundários." (declarado 10/40; eixo `atuacao` em 14 reviews)
- **Anatomia de uma Queda / negativas: direção e estética visual fraca** — "Críticas mencionaram a falta de coesão visual e a sensação de que a direção não conseguiu transmitir uma estética envolvente ou clara." (declarado 8/40; eixo `direcao_imagem` em 7 reviews)

## Quantificador do bullet × reviews que o sustentam

`texto`: o primeiro quantificador da descrição ("muitas", "várias"…) e a faixa do site em que ele cai; `barra`: a faixa que a contagem declarada comunica na tela. `apoio`: reviews que o juiz confirmou, de 5. `eixo`: reviews com o eixo do bullet (Parte 1a).

### publicado

| filme | grupo | tema | texto | declarado (barra) | apoio | eixo |
|---|---|---|---|---|---|---|
| Anatomia de uma Queda | negativas | Ritmo lento e arrastado | muitas → muitos | 25/40 (a maioria) | 4/5 | 27 |
| Anatomia de uma Queda | negativas | Final em aberto frustrante | — | 15/40 (muitos) | 4/5 | 32 |
| Anatomia de uma Queda | negativas | História sem profundidade | parte das → alguns | 10/40 (alguns) | 5/5 | 32 |
| Anatomia de uma Queda | negativas | Personagens pouco cativantes | alguns → alguns | 7/40 (alguns) | 1/5 | 32 |
| Anatomia de uma Queda | negativas | Mistura de idiomas incomoda | alguns → alguns | 5/40 (alguns) | 4/5 | 4 |
| Anatomia de uma Queda | negativas | Expectativas não correspondidas | muitos → muitos | 5/40 (alguns) | 5/5 | 10 |
| Anatomia de uma Queda | medianas | Ritmo lento e duração excessiva | — | 20/40 (muitos) | 5/5 | 15 |
| Anatomia de uma Queda | medianas | Final ambíguo e sem respostas definitivas | — | 13/40 (muitos) | 2/5 | 30 |
| Anatomia de uma Queda | medianas | Atuações fortes (incluindo o cachorro) | — | 12/40 (muitos) | 4/5 | 13 |
| Anatomia de uma Queda | medianas | Promotor irritante e processo judicial | — | 10/40 (alguns) | 5/5 | 30 |
| Anatomia de uma Queda | medianas | Foco nas relações humanas e na subjetividade da verdade | — | 9/40 (alguns) | 2/5 | 3 |
| Anatomia de uma Queda | medianas | Expectativa por um grande acontecimento que não vem | — | 7/40 (alguns) | 5/5 | 6 |
| Anatomia de uma Queda | positivas | Atuações excepcionais | — | 25/40 (a maioria) | 5/5 | 18 |
| Anatomia de uma Queda | positivas | Dissolução e complexidade conjugal | — | 18/40 (muitos) | 5/5 | 29 |
| Anatomia de uma Queda | positivas | Roteiro inteligente e diálogos afiados | — | 15/40 (muitos) | 2/5 | 29 |
| Anatomia de uma Queda | positivas | Tensão e suspense no tribunal | — | 10/40 (alguns) | 5/5 | 14 |
| Anatomia de uma Queda | positivas | Direção e atmosfera realista | — | 8/40 (alguns) | 5/5 | 10 |
| Anatomia de uma Queda | positivas | Reflexões sobre verdade e percepção | — | 7/40 (alguns) | 2/5 | 8 |
| Incêndios | negativas | Ritmo lento e tédio | varias → muitos | 15/40 (muitos) | 4/5 | 12 |
| Incêndios | negativas | Twist previsível e decepcionante | muitas → muitos | 14/40 (muitos) | 5/5 | 35 |
| Incêndios | negativas | Falta de contexto político e covardia | algumas → alguns | 10/40 (alguns) | 4/5 | 15 |
| Incêndios | negativas | Atuações fracas e falta de credibilidade | — | 8/40 (alguns) | 1/5 | 6 |
| Incêndios | negativas | Exploração de trauma e tabus | algumas → alguns | 7/40 (alguns) | 4/5 | 5 |
| Incêndios | negativas | Problemas de roteiro e lógica | — | 6/40 (alguns) | 4/5 | 35 |
| Incêndios | medianas | Reviravolta previsível ou que não surpreendeu | varios → muitos | 18/40 (muitos) | 4/5 | 38 |
| Incêndios | medianas | Ritmo lento e momentos arrastados | — | 15/40 (muitos) | 3/5 | 14 |
| Incêndios | medianas | Direção e atuações elogiadas | muitos → muitos | 12/40 (muitos) | 4/5 | 8 |
| Incêndios | medianas | Roteiro excessivamente construído para o choque | algumas → alguns | 10/40 (alguns) | 5/5 | 38 |
| Incêndios | medianas | Fotografia e aspectos técnicos bem avaliados | — | 9/40 (alguns) | 2/5 | 11 |
| Incêndios | medianas | Dificuldade de conexão emocional com os personagens | — | 8/40 (alguns) | 3/5 | 25 |
| Incêndios | positivas | Impacto emocional devastador | muitos → muitos | 28/40 (a maioria) | 4/5 | 25 |
| Incêndios | positivas | Reviravolta e revelações | alguns → alguns | 22/40 (cerca de metade) | 4/5 | 30 |
| Incêndios | positivas | Direção de Denis Villeneuve | varios → muitos | 18/40 (muitos) | 5/5 | 9 |
| Incêndios | positivas | Atuação de Lubna Azabal | — | 12/40 (muitos) | 3/5 | 6 |
| Incêndios | positivas | Fotografia e paisagens | — | 11/40 (muitos) | 1/5 | 9 |
| Incêndios | positivas | Roteiro e narrativa não linear | alguns → alguns | 10/40 (alguns) | 1/5 | 30 |
| mãe! | negativas | Alta carga alegórica e excesso de simbolismo | muitas → muitos | 13/40 (muitos) | 5/5 | 5 |
| mãe! | negativas | Experiência insuportável e desconfortável | uma parcela → alguns | 11/40 (muitos) | 5/5 | 17 |
| mãe! | negativas | Ritmo problemático e sensação de longa duração | varias → muitos | 8/40 (alguns) | 2/5 | 6 |
| mãe! | negativas | Crítica ao personagem feminino e à dinâmica do casal | — | 7/40 (alguns) | 5/5 | 12 |
| mãe! | negativas | Atuação de Jennifer Lawrence como ponto positivo | muitos → muitos | 6/40 (alguns) | 2/5 | 9 |
| mãe! | negativas | Sensacionalismo gratuito e cenas chocantes | alguns → alguns | 5/40 (alguns) | 4/5 | 12 |
| mãe! | medianas | Simbologia e alegoria | muitos → muitos | 15/40 (muitos) | 5/5 | livre |
| mãe! | medianas | Atuação de Jennifer Lawrence | muitos → muitos | 10/40 (alguns) | 5/5 | 12 |
| mãe! | medianas | Experiência estressante e desconfortável | a maioria → a maioria | 10/40 (alguns) | 5/5 | 20 |
| mãe! | medianas | Ritmo e excessos no ato final | muitos → muitos | 8/40 (alguns) | 5/5 | 10 |
| mãe! | medianas | Premissa interessante, execução confusa | muitos → muitos | 7/40 (alguns) | 5/5 | 25 |
| mãe! | medianas | Fotografia e tensão visual | — | 5/40 (alguns) | 3/5 | 9 |
| mãe! | positivas | Símbolos e metáforas religiosas | — | 18/40 (muitos) | 5/5 | livre |
| mãe! | positivas | Desempenho de Jennifer Lawrence | — | 12/40 (muitos) | 5/5 | 13 |
| mãe! | positivas | Incompreensão inicial e revelação posterior | muitos → muitos | 10/40 (alguns) | 5/5 | 6 |
| mãe! | positivas | Sensação de desconforto e ansiedade | — | 10/40 (alguns) | 3/5 | 6 |
| mãe! | positivas | Roteiro e direção intensos | — | 8/40 (alguns) | 3/5 | 25 |
| mãe! | positivas | Crítica ao ego masculino e relacionamentos abusivos | — | 7/40 (alguns) | 5/5 | 10 |
| Napoleão | negativas | Retrato de Napoleão | — | 20/40 (muitos) | 5/5 | 30 |
| Napoleão | negativas | Imprecisões históricas | muitos → muitos | 15/40 (muitos) | 5/5 | 15 |
| Napoleão | negativas | Ritmo e edição | — | 10/40 (alguns) | 4/5 | 8 |
| Napoleão | negativas | Foco excessivo no romance | — | 9/40 (alguns) | 5/5 | 30 |
| Napoleão | negativas | Atuações e elenco | alguns → alguns | 7/40 (alguns) | 5/5 | 14 |
| Napoleão | negativas | Batalhas decepcionantes | muitas → muitos | 6/40 (alguns) | 4/5 | 15 |
| Napoleão | medianas | Batalhas visualmente impressionantes | a maioria → a maioria | 15/40 (muitos) | 4/5 | 20 |
| Napoleão | medianas | Ritmo irregular e excesso de duração | varias → muitos | 12/40 (muitos) | 5/5 | 18 |
| Napoleão | medianas | Foco excessivo no relacionamento com Josefina | uma parcela → alguns | 10/40 (alguns) | 4/5 | 27 |
| Napoleão | medianas | Imprecisões históricas e licenças poéticas | varias → muitos | 9/40 (alguns) | 4/5 | 16 |
| Napoleão | medianas | Atuações de destaque, especialmente de Phoenix e Kirby | alguns → alguns | 8/40 (alguns) | 3/5 | 11 |
| Napoleão | medianas | Construção de personagem fraca e falta de profundidade política | — | 7/40 (alguns) | 3/5 | 27 |
| Napoleão | positivas | Atuações e carisma de Joaquin Phoenix e Vanessa Kirby | — | 8/40 (alguns) | 4/5 | 14 |
| Napoleão | positivas | Impacto visual e direção de arte | — | 8/40 (alguns) | 2/5 | 18 |
| Napoleão | positivas | Qualidade das cenas de batalha | — | 7/40 (alguns) | 2/5 | 18 |
| Napoleão | positivas | Abordagem pessoal e íntima do personagem | — | 6/40 (alguns) | 3/5 | 22 |
| Napoleão | positivas | Ritmo e edição | alguns → alguns | 5/40 (alguns) | 2/5 | 13 |
| Napoleão | positivas | Incentivo à pesquisa histórica | — | 5/40 (alguns) | 1/5 | livre |
| A Substância | negativas | Excesso de gore e violência gratuita | — | 15/40 (muitos) | 5/5 | 7 |
| A Substância | negativas | Exibicionismo e nudez excessiva | — | 10/40 (alguns) | 4/5 | 7 |
| A Substância | negativas | Roteiro sem desenvolvimento | — | 10/40 (alguns) | 5/5 | 25 |
| A Substância | negativas | Mensagem superficial e repetitiva | — | 8/40 (alguns) | 5/5 | 18 |
| A Substância | negativas | Final decepcionante | varios → muitos | 7/40 (alguns) | 5/5 | 25 |
| A Substância | negativas | Duração excessiva e ritmo lento | — | 6/40 (alguns) | 4/5 | 15 |
| A Substância | medianas | Final exagerado e decepcionante | muitas → muitos | 18/40 (muitos) | 5/5 | 25 |
| A Substância | medianas | Crítica social e mensagem relevante | alguns → alguns | 14/40 (muitos) | 4/5 | 20 |
| A Substância | medianas | Atuações e elenco elogiados | — | 10/40 (alguns) | 3/5 | 13 |
| A Substância | medianas | Efeitos práticos e direção de arte | — | 9/40 (alguns) | 4/5 | 16 |
| A Substância | medianas | Ritmo irregular e repetição | varios → muitos | 9/40 (alguns) | 4/5 | 14 |
| A Substância | medianas | Body horror extremo e desconforto | alguns → alguns | 7/40 (alguns) | 5/5 | 22 |
| A Substância | positivas | Metáfora da autodestruição e padrões de beleza | — | 12/40 (muitos) | 4/5 | 17 |
| A Substância | positivas | Atuações de Demi Moore e Margaret Qualley | — | 8/40 (alguns) | 5/5 | 9 |
| A Substância | positivas | Direção e estilo visual marcantes | — | 7/40 (alguns) | 3/5 | 12 |
| A Substância | positivas | Body horror extremo e efeitos práticos | — | 7/40 (alguns) | 4/5 | 12 |
| A Substância | positivas | Crítica à indústria do entretenimento e ao envelhecimento | — | 6/40 (alguns) | 3/5 | 17 |
| A Substância | positivas | Final controverso e exagerado | alguns → alguns | 6/40 (alguns) | 5/5 | 19 |

### local

| filme | grupo | tema | texto | declarado (barra) | apoio | eixo |
|---|---|---|---|---|---|---|
| Anatomia de uma Queda | negativas | ritmo lento e monótono | varias → muitos | 25/40 (a maioria) | 5/5 | 27 |
| Anatomia de uma Queda | negativas | final aberto e frustrante | muitos → muitos | 18/40 (muitos) | 4/5 | 32 |
| Anatomia de uma Queda | negativas | trama pouco envolvente | varias → muitos | 15/40 (muitos) | 5/5 | 32 |
| Anatomia de uma Queda | negativas | diálogos longos e repetitivos | muitas → muitos | 12/40 (muitos) | 1/5 | 32 |
| Anatomia de uma Queda | negativas | atuações insuficientes | alguns → alguns | 10/40 (alguns) | 0/5 | 14 |
| Anatomia de uma Queda | negativas | direção e estética visual fraca | — | 8/40 (alguns) | 0/5 | 7 |
| Anatomia de uma Queda | medianas | ritmo lento e alongado | varias → muitos | 18/40 (muitos) | 4/5 | 15 |
| Anatomia de uma Queda | medianas | foco no processo judicial e nas relações familiares | muitas → muitos | 12/40 (muitos) | 4/5 | 30 |
| Anatomia de uma Queda | medianas | interpretação da verdade e ambiguidade | alguns → alguns | 10/40 (alguns) | 2/5 | 30 |
| Anatomia de uma Queda | medianas | atuações fortes, especialmente de Sandra Hüller | diversas → muitos | 8/40 (alguns) | 3/5 | 13 |
| Anatomia de uma Queda | medianas | presença do cachorro como elemento simbólico | alguns → alguns | 6/40 (alguns) | 4/5 | 4 |
| Anatomia de uma Queda | medianas | críticas ao sistema judicial francês | algumas → alguns | 5/40 (alguns) | 2/5 | 5 |
| Anatomia de uma Queda | positivas | complexidade dos relacionamentos | muitas → muitos | 15/40 (muitos) | 5/5 | 29 |
| Anatomia de uma Queda | positivas | desempenho atorial | — | 12/40 (muitos) | 5/5 | 18 |
| Anatomia de uma Queda | positivas | tensão e suspense no tribunal | varias → muitos | 10/40 (alguns) | 2/5 | 14 |
| Anatomia de uma Queda | positivas | realismo e autenticidade | — | 8/40 (alguns) | 3/5 | 10 |
| Anatomia de uma Queda | positivas | interpretação do espectador | muitos → muitos | 6/40 (alguns) | 4/5 | 16 |
| Anatomia de uma Queda | positivas | comparação com outras obras | alguns → alguns | 5/40 (alguns) | 1/5 | 10 |
| Incêndios | negativas | previsibilidade do enredo | varios → muitos | 12/40 (muitos) | 5/5 | 35 |
| Incêndios | negativas | trabalho de atuação insatisfatório | — | 8/40 (alguns) | 1/5 | 6 |
| Incêndios | negativas | falta de aprofundamento no contexto político e histórico | varias → muitos | 7/40 (alguns) | 4/5 | 15 |
| Incêndios | negativas | apresentação de temas sensíveis de forma inadequada | alguns → alguns | 6/40 (alguns) | 4/5 | 15 |
| Incêndios | negativas | ritmo lento e falta de engajamento | muitos → muitos | 5/40 (alguns) | 5/5 | 12 |
| Incêndios | negativas | falta de originalidade e genericalidade | alguns → alguns | 4/40 (alguns) | 3/5 | 35 |
| Incêndios | medianas | Revelação surpreendente no final | varias → muitos | 12/40 (muitos) | 4/5 | 38 |
| Incêndios | medianas | Trabalho de direção e fotografia | — | 8/40 (alguns) | 3/5 | 11 |
| Incêndios | medianas | Narrativa lenta e densa | alguns → alguns | 7/40 (alguns) | 2/5 | 14 |
| Incêndios | medianas | Foco excessivo no plot twist | — | 6/40 (alguns) | 5/5 | 38 |
| Incêndios | medianas | Temas de guerra e conflito | algumas → alguns | 5/40 (alguns) | 5/5 | 13 |
| Incêndios | medianas | Ausência de conexão emocional com os personagens | diversas → muitos | 4/40 (alguns) | 3/5 | 25 |
| Incêndios | positivas | impacto emocional intenso | muitas → muitos | 18/40 (muitos) | 5/5 | 25 |
| Incêndios | positivas | revelação surpreendente e impactante | varias → muitos | 12/40 (muitos) | 4/5 | 30 |
| Incêndios | positivas | exploração da guerra e seus efeitos | varios → muitos | 10/40 (alguns) | 5/5 | 9 |
| Incêndios | positivas | exploração da maternidade e dos laços familiares | — | 8/40 (alguns) | 4/5 | 30 |
| Incêndios | positivas | realismo e representação da vida real | diversas → muitos | 6/40 (alguns) | 3/5 | 9 |
| Incêndios | positivas | direção e cinematografia impecáveis | varias → muitos | 5/40 (alguns) | 4/5 | 9 |
| mãe! | negativas | excesso de metáforas e simbolismo | muitas → muitos | 15/40 (muitos) | 5/5 | 22 |
| mãe! | negativas | trabalho de Jennifer Lawrence | — | 8/40 (alguns) | 4/5 | 9 |
| mãe! | negativas | ritmo e desgaste do espectador | varias → muitos | 7/40 (alguns) | 5/5 | 6 |
| mãe! | negativas | trabalho do diretor e intencionalidade artística | alguns → alguns | 6/40 (alguns) | 4/5 | 7 |
| mãe! | negativas | trabalho de atores secundários e direção de cena | algumas → alguns | 5/40 (alguns) | 1/5 | 9 |
| mãe! | negativas | conteúdo desagradável e impacto emocional | varias → muitos | 5/40 (alguns) | 5/5 | 17 |
| mãe! | medianas | sensação de desconforto e ansiedade | varias → muitos | 15/40 (muitos) | 5/5 | 7 |
| mãe! | medianas | uso de metáforas e simbolismo | muitas → muitos | 12/40 (muitos) | 5/5 | 9 |
| mãe! | medianas | desenvolvimento do enredo | algumas → alguns | 10/40 (alguns) | 4/5 | 25 |
| mãe! | medianas | interpretação pessoal e reflexão | varias → muitos | 8/40 (alguns) | 4/5 | livre |
| mãe! | medianas | desempenho de Jennifer Lawrence | — | 7/40 (alguns) | 5/5 | 12 |
| mãe! | medianas | confusão e falta de clareza | muitos → muitos | 6/40 (alguns) | 5/5 | 25 |
| mãe! | positivas | Metáforas religiosas e simbolismo bíblico | varios → muitos | 15/40 (muitos) | 5/5 | 25 |
| mãe! | positivas | Performance de Jennifer Lawrence | muitas → muitos | 12/40 (muitos) | 5/5 | 13 |
| mãe! | positivas | Tensão e ansiedade psicológica | muitos → muitos | 10/40 (alguns) | 4/5 | 6 |
| mãe! | positivas | Confusão inicial e revelação no final | varias → muitos | 9/40 (alguns) | 5/5 | 25 |
| mãe! | positivas | Crítica à figura masculina e ao ego | — | 7/40 (alguns) | 3/5 | 10 |
| mãe! | positivas | Impacto emocional e psicológico | muitos → muitos | 6/40 (alguns) | 5/5 | 24 |
| Napoleão | negativas | Inaccuracy histórica | varias → muitos | 20/40 (muitos) | 4/5 | 15 |
| Napoleão | negativas | Foco excessivo na relação com Joséphine | muitas → muitos | 15/40 (muitos) | 5/5 | 30 |
| Napoleão | negativas | Interpretação inadequada de Napoleão | varios → muitos | 12/40 (muitos) | 5/5 | 14 |
| Napoleão | negativas | Falta de profundidade e contexto | — | 10/40 (alguns) | 3/5 | 30 |
| Napoleão | negativas | Falta de ação e ritmo lento | varias → muitos | 9/40 (alguns) | 3/5 | 8 |
| Napoleão | negativas | Falta de coesão e estrutura narrativa | alguns → alguns | 8/40 (alguns) | 2/5 | 30 |
| Napoleão | medianas | Foco excessivo na vida pessoal de Napoleão | varias → muitos | 12/40 (muitos) | 4/5 | 27 |
| Napoleão | medianas | Erros históricos e falta de precisão factual | muitas → muitos | 10/40 (alguns) | 5/5 | 16 |
| Napoleão | medianas | Cenas de batalha visualmente impressionantes, mas insuficientes | — | 8/40 (alguns) | 4/5 | 20 |
| Napoleão | medianas | Interpretação do personagem insatisfatória | alguns → alguns | 7/40 (alguns) | 4/5 | 11 |
| Napoleão | medianas | Estilo visual e cinematografia apreciados, mas não suficientes para compensar falhas narrativas | — | 6/40 (alguns) | 4/5 | 20 |
| Napoleão | medianas | Tempo de duração e ritmo narrativo criticados | — | 5/40 (alguns) | 4/5 | 18 |
| Napoleão | positivas | Batalhas e cenas de ação | varias → muitos | 12/40 (muitos) | 3/5 | 18 |
| Napoleão | positivas | Interpretação de Joaquin Phoenix | — | 9/40 (alguns) | 5/5 | 14 |
| Napoleão | positivas | Trabalho de direção e produção | — | 7/40 (alguns) | 2/5 | 18 |
| Napoleão | positivas | Relação entre Napoleão e Josephine | algumas → alguns | 6/40 (alguns) | 3/5 | 22 |
| Napoleão | positivas | Abordagem do personagem Napoleão | — | 5/40 (alguns) | 4/5 | 22 |
| Napoleão | positivas | Versão do diretor (Director’s Cut) | varias → muitos | 5/40 (alguns) | 4/5 | livre |
| A Substância | negativas | abordagem excessiva de gore e nus | muitas → muitos | 18/40 (muitos) | 5/5 | 18 |
| A Substância | negativas | roteiro fraco e desorganizado | varias → muitos | 14/40 (muitos) | 5/5 | 25 |
| A Substância | negativas | excesso de repetição e previsibilidade | muitos → muitos | 10/40 (alguns) | 4/5 | 25 |
| A Substância | negativas | exposição de temas sensíveis de forma inadequada | alguns → alguns | 8/40 (alguns) | 5/5 | 18 |
| A Substância | negativas | longa duração e ritmo lento | varias → muitos | 7/40 (alguns) | 1/5 | 15 |
| A Substância | negativas | falta de originalidade e influências evidentes | alguns → alguns | 6/40 (alguns) | 1/5 | 25 |
| A Substância | medianas | horror corporal e estética grotesca | varias → muitos | 20/40 (muitos) | 5/5 | 16 |
| A Substância | medianas | crítica à beleza e ao envelhecimento feminino | muitas → muitos | 12/40 (muitos) | 3/5 | 20 |
| A Substância | medianas | narrativa repetitiva e excessiva | alguns → alguns | 8/40 (alguns) | 3/5 | 25 |
| A Substância | medianas | atuações e direção | alguns → alguns | 6/40 (alguns) | 5/5 | 13 |
| A Substância | medianas | comentários sobre o final do filme | algumas → alguns | 5/40 (alguns) | 3/5 | 25 |
| A Substância | medianas | referências culturais e influências cinematográficas | alguns → alguns | 4/40 (alguns) | 2/5 | 14 |
| A Substância | positivas | representação do corpo e a pressão por juventude | varias → muitos | 20/40 (muitos) | 4/5 | 17 |
| A Substância | positivas | horror corporal e efeitos visuais extremos | muitas → muitos | 15/40 (muitos) | 4/5 | 12 |
| A Substância | positivas | crítica ao patriarcado e estereótipos de beleza | diversas → muitos | 10/40 (alguns) | 4/5 | 17 |
| A Substância | positivas | dualidade entre personagens e identidade | algumas → alguns | 8/40 (alguns) | 3/5 | 19 |
| A Substância | positivas | uso de metáforas e simbolismo | alguns → alguns | 6/40 (alguns) | 3/5 | 19 |
| A Substância | positivas | desempenho dos atores e direção | algumas → alguns | 5/40 (alguns) | 4/5 | 9 |

## Comparação com a medida grosseira (Parte 1a)

| lado | Parte 1a / juiz | bullets |
|---|---|---|
| publicado | eixo_ok/com_apoio | 87 |
| publicado | sem_eixo/com_apoio | 3 |
| local | eixo_ok/com_apoio | 86 |
| local | eixo_ok/sem_apoio | 2 |
| local | sem_eixo/com_apoio | 2 |

`suspeito/sem_apoio`: as duas medidas concordam que falta apoio; `eixo_ok/sem_apoio`: o eixo é frequente mas nenhuma das reviews mais parecidas diz o tema — o caso que a régua larga não pega.
