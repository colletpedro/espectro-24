# Parte 1a — o eixo do bullet no consenso da classificação

Para cada bullet, o eixo que a rotulagem do PRÓPRIO lado deu ao tema e quantas reviews do grupo (as mesmas que a síntese leu) têm esse eixo no consenso. **Grosseiro:** o eixo é mais largo que o tema — `atuacao` conta elogio e crítica de atuação juntos — então eixo alto não prova apoio; eixo em 0-1 review é que torna o bullet suspeito. Tema rotulado `livre` não tem eixo e não é medido aqui.

Consenso: `resultado/votacao-3/consenso_verificado.jsonl` (sha256 das linhas dos 5 filmes `21076cf329f81238…`). Contagem conferida contra o bloco `eixos` publicado em 300 células, sem divergência.

| lado | bullets | sem eixo (livre) | suspeitos (eixo ≤ 1) | declarado > eixo |
|---|---|---|---|---|
| publicado | 90 | 3 | 0 | 21 |
| local | 90 | 2 | 0 | 14 |

_declarado > eixo_: a síntese diz que mais reviews citam o tema do que as que têm o eixo inteiro — inflado mesmo pela régua larga (ou erro de recall da classificação).

## Anatomia de uma Queda

### publicado — DeepSeek (síntese publicada)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Ritmo lento e arrastado | 25/40 | ritmo | 27/40 |  |
| negativas | Final em aberto frustrante | 15/40 | roteiro_estrutura | 32/40 |  |
| negativas | História sem profundidade | 10/40 | roteiro_estrutura | 32/40 |  |
| negativas | Personagens pouco cativantes | 7/40 | roteiro_estrutura | 32/40 |  |
| negativas | Mistura de idiomas incomoda | 5/40 | som_trilha | 4/40 | declarado > eixo |
| negativas | Expectativas não correspondidas | 5/40 | expectativa | 10/40 |  |
| medianas | Ritmo lento e duração excessiva | 20/40 | ritmo | 15/40 | declarado > eixo |
| medianas | Final ambíguo e sem respostas definitivas | 13/40 | roteiro_estrutura | 30/40 |  |
| medianas | Atuações fortes (incluindo o cachorro) | 12/40 | atuacao | 13/40 |  |
| medianas | Promotor irritante e processo judicial | 10/40 | roteiro_estrutura | 30/40 |  |
| medianas | Foco nas relações humanas e na subjetividade da verdade | 9/40 | tom_atmosfera | 3/40 | declarado > eixo |
| medianas | Expectativa por um grande acontecimento que não vem | 7/40 | expectativa | 6/40 | declarado > eixo |
| positivas | Atuações excepcionais | 25/40 | atuacao | 18/40 | declarado > eixo |
| positivas | Dissolução e complexidade conjugal | 18/40 | roteiro_estrutura | 29/40 |  |
| positivas | Roteiro inteligente e diálogos afiados | 15/40 | roteiro_estrutura | 29/40 |  |
| positivas | Tensão e suspense no tribunal | 10/40 | ritmo | 14/40 |  |
| positivas | Direção e atmosfera realista | 8/40 | direcao_imagem | 10/40 |  |
| positivas | Reflexões sobre verdade e percepção | 7/40 | tom_atmosfera | 8/40 |  |

### local — qwen3:14b (Ollama)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | ritmo lento e monótono | 25/40 | ritmo | 27/40 |  |
| negativas | final aberto e frustrante | 18/40 | roteiro_estrutura | 32/40 |  |
| negativas | trama pouco envolvente | 15/40 | roteiro_estrutura | 32/40 |  |
| negativas | diálogos longos e repetitivos | 12/40 | roteiro_estrutura | 32/40 |  |
| negativas | atuações insuficientes | 10/40 | atuacao | 14/40 |  |
| negativas | direção e estética visual fraca | 8/40 | direcao_imagem | 7/40 | declarado > eixo |
| medianas | ritmo lento e alongado | 18/40 | ritmo | 15/40 | declarado > eixo |
| medianas | foco no processo judicial e nas relações familiares | 12/40 | roteiro_estrutura | 30/40 |  |
| medianas | interpretação da verdade e ambiguidade | 10/40 | roteiro_estrutura | 30/40 |  |
| medianas | atuações fortes, especialmente de Sandra Hüller | 8/40 | atuacao | 13/40 |  |
| medianas | presença do cachorro como elemento simbólico | 6/40 | direcao_imagem | 4/40 | declarado > eixo |
| medianas | críticas ao sistema judicial francês | 5/40 | critica_social | 5/40 |  |
| positivas | complexidade dos relacionamentos | 15/40 | roteiro_estrutura | 29/40 |  |
| positivas | desempenho atorial | 12/40 | atuacao | 18/40 |  |
| positivas | tensão e suspense no tribunal | 10/40 | ritmo | 14/40 |  |
| positivas | realismo e autenticidade | 8/40 | direcao_imagem | 10/40 |  |
| positivas | interpretação do espectador | 6/40 | impacto_emocional | 16/40 |  |
| positivas | comparação com outras obras | 5/40 | comparacoes | 10/40 |  |

## Incêndios

### publicado — DeepSeek (síntese publicada)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Ritmo lento e tédio | 15/40 | ritmo | 12/40 | declarado > eixo |
| negativas | Twist previsível e decepcionante | 14/40 | roteiro_estrutura | 35/40 |  |
| negativas | Falta de contexto político e covardia | 10/40 | critica_social | 15/40 |  |
| negativas | Atuações fracas e falta de credibilidade | 8/40 | atuacao | 6/40 | declarado > eixo |
| negativas | Exploração de trauma e tabus | 7/40 | tom_atmosfera | 5/40 | declarado > eixo |
| negativas | Problemas de roteiro e lógica | 6/40 | roteiro_estrutura | 35/40 |  |
| medianas | Reviravolta previsível ou que não surpreendeu | 18/40 | roteiro_estrutura | 38/40 |  |
| medianas | Ritmo lento e momentos arrastados | 15/40 | ritmo | 14/40 | declarado > eixo |
| medianas | Direção e atuações elogiadas | 12/40 | atuacao | 8/40 | declarado > eixo |
| medianas | Roteiro excessivamente construído para o choque | 10/40 | roteiro_estrutura | 38/40 |  |
| medianas | Fotografia e aspectos técnicos bem avaliados | 9/40 | direcao_imagem | 11/40 |  |
| medianas | Dificuldade de conexão emocional com os personagens | 8/40 | impacto_emocional | 25/40 |  |
| positivas | Impacto emocional devastador | 28/40 | impacto_emocional | 25/40 | declarado > eixo |
| positivas | Reviravolta e revelações | 22/40 | roteiro_estrutura | 30/40 |  |
| positivas | Direção de Denis Villeneuve | 18/40 | direcao_imagem | 9/40 | declarado > eixo |
| positivas | Atuação de Lubna Azabal | 12/40 | atuacao | 6/40 | declarado > eixo |
| positivas | Fotografia e paisagens | 11/40 | direcao_imagem | 9/40 | declarado > eixo |
| positivas | Roteiro e narrativa não linear | 10/40 | roteiro_estrutura | 30/40 |  |

### local — qwen3:14b (Ollama)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | previsibilidade do enredo | 12/40 | roteiro_estrutura | 35/40 |  |
| negativas | trabalho de atuação insatisfatório | 8/40 | atuacao | 6/40 | declarado > eixo |
| negativas | falta de aprofundamento no contexto político e histórico | 7/40 | critica_social | 15/40 |  |
| negativas | apresentação de temas sensíveis de forma inadequada | 6/40 | critica_social | 15/40 |  |
| negativas | ritmo lento e falta de engajamento | 5/40 | ritmo | 12/40 |  |
| negativas | falta de originalidade e genericalidade | 4/40 | roteiro_estrutura | 35/40 |  |
| medianas | Revelação surpreendente no final | 12/40 | roteiro_estrutura | 38/40 |  |
| medianas | Trabalho de direção e fotografia | 8/40 | direcao_imagem | 11/40 |  |
| medianas | Narrativa lenta e densa | 7/40 | ritmo | 14/40 |  |
| medianas | Foco excessivo no plot twist | 6/40 | roteiro_estrutura | 38/40 |  |
| medianas | Temas de guerra e conflito | 5/40 | critica_social | 13/40 |  |
| medianas | Ausência de conexão emocional com os personagens | 4/40 | impacto_emocional | 25/40 |  |
| positivas | impacto emocional intenso | 18/40 | impacto_emocional | 25/40 |  |
| positivas | revelação surpreendente e impactante | 12/40 | roteiro_estrutura | 30/40 |  |
| positivas | exploração da guerra e seus efeitos | 10/40 | critica_social | 9/40 | declarado > eixo |
| positivas | exploração da maternidade e dos laços familiares | 8/40 | roteiro_estrutura | 30/40 |  |
| positivas | realismo e representação da vida real | 6/40 | direcao_imagem | 9/40 |  |
| positivas | direção e cinematografia impecáveis | 5/40 | direcao_imagem | 9/40 |  |

## mãe!

### publicado — DeepSeek (síntese publicada)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Alta carga alegórica e excesso de simbolismo | 13/40 | tom_atmosfera | 5/40 | declarado > eixo |
| negativas | Experiência insuportável e desconfortável | 11/40 | impacto_emocional | 17/40 |  |
| negativas | Ritmo problemático e sensação de longa duração | 8/40 | ritmo | 6/40 | declarado > eixo |
| negativas | Crítica ao personagem feminino e à dinâmica do casal | 7/40 | critica_social | 12/40 |  |
| negativas | Atuação de Jennifer Lawrence como ponto positivo | 6/40 | atuacao | 9/40 |  |
| negativas | Sensacionalismo gratuito e cenas chocantes | 5/40 | critica_social | 12/40 |  |
| medianas | Simbologia e alegoria | 15/40 | livre | 0/40 | **sem eixo** |
| medianas | Atuação de Jennifer Lawrence | 10/40 | atuacao | 12/40 |  |
| medianas | Experiência estressante e desconfortável | 10/40 | impacto_emocional | 20/40 |  |
| medianas | Ritmo e excessos no ato final | 8/40 | ritmo | 10/40 |  |
| medianas | Premissa interessante, execução confusa | 7/40 | roteiro_estrutura | 25/40 |  |
| medianas | Fotografia e tensão visual | 5/40 | direcao_imagem | 9/40 |  |
| positivas | Símbolos e metáforas religiosas | 18/40 | livre | 0/40 | **sem eixo** |
| positivas | Desempenho de Jennifer Lawrence | 12/40 | atuacao | 13/40 |  |
| positivas | Incompreensão inicial e revelação posterior | 10/40 | expectativa | 6/40 | declarado > eixo |
| positivas | Sensação de desconforto e ansiedade | 10/40 | tom_atmosfera | 6/40 | declarado > eixo |
| positivas | Roteiro e direção intensos | 8/40 | roteiro_estrutura | 25/40 |  |
| positivas | Crítica ao ego masculino e relacionamentos abusivos | 7/40 | critica_social | 10/40 |  |

### local — qwen3:14b (Ollama)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | excesso de metáforas e simbolismo | 15/40 | roteiro_estrutura | 22/40 |  |
| negativas | trabalho de Jennifer Lawrence | 8/40 | atuacao | 9/40 |  |
| negativas | ritmo e desgaste do espectador | 7/40 | ritmo | 6/40 | declarado > eixo |
| negativas | trabalho do diretor e intencionalidade artística | 6/40 | direcao_imagem | 7/40 |  |
| negativas | trabalho de atores secundários e direção de cena | 5/40 | atuacao | 9/40 |  |
| negativas | conteúdo desagradável e impacto emocional | 5/40 | impacto_emocional | 17/40 |  |
| medianas | sensação de desconforto e ansiedade | 15/40 | tom_atmosfera | 7/40 | declarado > eixo |
| medianas | uso de metáforas e simbolismo | 12/40 | direcao_imagem | 9/40 | declarado > eixo |
| medianas | desenvolvimento do enredo | 10/40 | roteiro_estrutura | 25/40 |  |
| medianas | interpretação pessoal e reflexão | 8/40 | livre | 0/40 | **sem eixo** |
| medianas | desempenho de Jennifer Lawrence | 7/40 | atuacao | 12/40 |  |
| medianas | confusão e falta de clareza | 6/40 | roteiro_estrutura | 25/40 |  |
| positivas | Metáforas religiosas e simbolismo bíblico | 15/40 | roteiro_estrutura | 25/40 |  |
| positivas | Performance de Jennifer Lawrence | 12/40 | atuacao | 13/40 |  |
| positivas | Tensão e ansiedade psicológica | 10/40 | tom_atmosfera | 6/40 | declarado > eixo |
| positivas | Confusão inicial e revelação no final | 9/40 | roteiro_estrutura | 25/40 |  |
| positivas | Crítica à figura masculina e ao ego | 7/40 | critica_social | 10/40 |  |
| positivas | Impacto emocional e psicológico | 6/40 | impacto_emocional | 24/40 |  |

## Napoleão

### publicado — DeepSeek (síntese publicada)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Retrato de Napoleão | 20/40 | roteiro_estrutura | 30/40 |  |
| negativas | Imprecisões históricas | 15/40 | critica_social | 15/40 |  |
| negativas | Ritmo e edição | 10/40 | ritmo | 8/40 | declarado > eixo |
| negativas | Foco excessivo no romance | 9/40 | roteiro_estrutura | 30/40 |  |
| negativas | Atuações e elenco | 7/40 | atuacao | 14/40 |  |
| negativas | Batalhas decepcionantes | 6/40 | direcao_imagem | 15/40 |  |
| medianas | Batalhas visualmente impressionantes | 15/40 | direcao_imagem | 20/40 |  |
| medianas | Ritmo irregular e excesso de duração | 12/40 | ritmo | 18/40 |  |
| medianas | Foco excessivo no relacionamento com Josefina | 10/40 | roteiro_estrutura | 27/40 |  |
| medianas | Imprecisões históricas e licenças poéticas | 9/40 | critica_social | 16/40 |  |
| medianas | Atuações de destaque, especialmente de Phoenix e Kirby | 8/40 | atuacao | 11/40 |  |
| medianas | Construção de personagem fraca e falta de profundidade política | 7/40 | roteiro_estrutura | 27/40 |  |
| positivas | Atuações e carisma de Joaquin Phoenix e Vanessa Kirby | 8/40 | atuacao | 14/40 |  |
| positivas | Impacto visual e direção de arte | 8/40 | direcao_imagem | 18/40 |  |
| positivas | Qualidade das cenas de batalha | 7/40 | direcao_imagem | 18/40 |  |
| positivas | Abordagem pessoal e íntima do personagem | 6/40 | roteiro_estrutura | 22/40 |  |
| positivas | Ritmo e edição | 5/40 | ritmo | 13/40 |  |
| positivas | Incentivo à pesquisa histórica | 5/40 | livre | 0/40 | **sem eixo** |

### local — qwen3:14b (Ollama)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Inaccuracy histórica | 20/40 | critica_social | 15/40 | declarado > eixo |
| negativas | Foco excessivo na relação com Joséphine | 15/40 | roteiro_estrutura | 30/40 |  |
| negativas | Interpretação inadequada de Napoleão | 12/40 | atuacao | 14/40 |  |
| negativas | Falta de profundidade e contexto | 10/40 | roteiro_estrutura | 30/40 |  |
| negativas | Falta de ação e ritmo lento | 9/40 | ritmo | 8/40 | declarado > eixo |
| negativas | Falta de coesão e estrutura narrativa | 8/40 | roteiro_estrutura | 30/40 |  |
| medianas | Foco excessivo na vida pessoal de Napoleão | 12/40 | roteiro_estrutura | 27/40 |  |
| medianas | Erros históricos e falta de precisão factual | 10/40 | critica_social | 16/40 |  |
| medianas | Cenas de batalha visualmente impressionantes, mas insuficientes | 8/40 | direcao_imagem | 20/40 |  |
| medianas | Interpretação do personagem insatisfatória | 7/40 | atuacao | 11/40 |  |
| medianas | Estilo visual e cinematografia apreciados, mas não suficientes para compensar falhas narrativas | 6/40 | direcao_imagem | 20/40 |  |
| medianas | Tempo de duração e ritmo narrativo criticados | 5/40 | ritmo | 18/40 |  |
| positivas | Batalhas e cenas de ação | 12/40 | direcao_imagem | 18/40 |  |
| positivas | Interpretação de Joaquin Phoenix | 9/40 | atuacao | 14/40 |  |
| positivas | Trabalho de direção e produção | 7/40 | direcao_imagem | 18/40 |  |
| positivas | Relação entre Napoleão e Josephine | 6/40 | roteiro_estrutura | 22/40 |  |
| positivas | Abordagem do personagem Napoleão | 5/40 | roteiro_estrutura | 22/40 |  |
| positivas | Versão do diretor (Director’s Cut) | 5/40 | livre | 0/40 | **sem eixo** |

## A Substância

### publicado — DeepSeek (síntese publicada)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | Excesso de gore e violência gratuita | 15/40 | tom_atmosfera | 7/40 | declarado > eixo |
| negativas | Exibicionismo e nudez excessiva | 10/40 | tom_atmosfera | 7/40 | declarado > eixo |
| negativas | Roteiro sem desenvolvimento | 10/40 | roteiro_estrutura | 25/40 |  |
| negativas | Mensagem superficial e repetitiva | 8/40 | critica_social | 18/40 |  |
| negativas | Final decepcionante | 7/40 | roteiro_estrutura | 25/40 |  |
| negativas | Duração excessiva e ritmo lento | 6/40 | ritmo | 15/40 |  |
| medianas | Final exagerado e decepcionante | 18/40 | roteiro_estrutura | 25/40 |  |
| medianas | Crítica social e mensagem relevante | 14/40 | critica_social | 20/40 |  |
| medianas | Atuações e elenco elogiados | 10/40 | atuacao | 13/40 |  |
| medianas | Efeitos práticos e direção de arte | 9/40 | direcao_imagem | 16/40 |  |
| medianas | Ritmo irregular e repetição | 9/40 | ritmo | 14/40 |  |
| medianas | Body horror extremo e desconforto | 7/40 | tom_atmosfera | 22/40 |  |
| positivas | Metáfora da autodestruição e padrões de beleza | 12/40 | critica_social | 17/40 |  |
| positivas | Atuações de Demi Moore e Margaret Qualley | 8/40 | atuacao | 9/40 |  |
| positivas | Direção e estilo visual marcantes | 7/40 | direcao_imagem | 12/40 |  |
| positivas | Body horror extremo e efeitos práticos | 7/40 | direcao_imagem | 12/40 |  |
| positivas | Crítica à indústria do entretenimento e ao envelhecimento | 6/40 | critica_social | 17/40 |  |
| positivas | Final controverso e exagerado | 6/40 | roteiro_estrutura | 19/40 |  |

### local — qwen3:14b (Ollama)

| grupo | tema | declarado | eixo | reviews com o eixo | |
|---|---|---|---|---|---|
| negativas | abordagem excessiva de gore e nus | 18/40 | critica_social | 18/40 |  |
| negativas | roteiro fraco e desorganizado | 14/40 | roteiro_estrutura | 25/40 |  |
| negativas | excesso de repetição e previsibilidade | 10/40 | roteiro_estrutura | 25/40 |  |
| negativas | exposição de temas sensíveis de forma inadequada | 8/40 | critica_social | 18/40 |  |
| negativas | longa duração e ritmo lento | 7/40 | ritmo | 15/40 |  |
| negativas | falta de originalidade e influências evidentes | 6/40 | roteiro_estrutura | 25/40 |  |
| medianas | horror corporal e estética grotesca | 20/40 | direcao_imagem | 16/40 | declarado > eixo |
| medianas | crítica à beleza e ao envelhecimento feminino | 12/40 | critica_social | 20/40 |  |
| medianas | narrativa repetitiva e excessiva | 8/40 | roteiro_estrutura | 25/40 |  |
| medianas | atuações e direção | 6/40 | atuacao | 13/40 |  |
| medianas | comentários sobre o final do filme | 5/40 | roteiro_estrutura | 25/40 |  |
| medianas | referências culturais e influências cinematográficas | 4/40 | comparacoes | 14/40 |  |
| positivas | representação do corpo e a pressão por juventude | 20/40 | critica_social | 17/40 | declarado > eixo |
| positivas | horror corporal e efeitos visuais extremos | 15/40 | direcao_imagem | 12/40 | declarado > eixo |
| positivas | crítica ao patriarcado e estereótipos de beleza | 10/40 | critica_social | 17/40 |  |
| positivas | dualidade entre personagens e identidade | 8/40 | roteiro_estrutura | 19/40 |  |
| positivas | uso de metáforas e simbolismo | 6/40 | roteiro_estrutura | 19/40 |  |
| positivas | desempenho dos atores e direção | 5/40 | atuacao | 9/40 |  |
