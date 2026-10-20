# Calibração do juiz v2 — versão v2.1

> **CALIBRAÇÃO, NÃO VALIDAÇÃO.** Estes 40 pares são os mesmos usados para ajustar o prompt; o número aqui é otimista por construção. O juiz só vale depois de congelado e medido numa amostra NOVA.

Configuração `75b5533f685bc37549a9c7751b7cb5ed3d777bc742dc5d832b6728be995b86b2` · gpt-oss:20b think=low · num_ctx 4096 · num_predict 1024 · seed 20261019

No critério proposto (a pré-registrar antes da amostra nova), esta calibração REPROVARIA: precisão difere 0.167 entre os lados (> 0.15) — precisão e recall ≥ 0,8; diferença de precisão entre os lados ≤ 0.15; diferença medida: 0.167.

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |
|---|---|---|---|---|---|---|---|
| v1 · todos | 40 | 24 | 9 | 1 | 6 | 0.727 [0.558, 0.849] | 0.96 [0.805, 0.993] |
| v1 · publicado | 20 | 13 | 3 | 1 | 3 | 0.812 [0.57, 0.934] | 0.929 [0.685, 0.987] |
| v1 · local | 20 | 11 | 6 | 0 | 3 | 0.647 [0.413, 0.827] | 1.0 [0.741, 1.0] |
| v2.0 · todos | 40 | 17 | 3 | 8 | 12 | 0.85 [0.64, 0.948] | 0.68 [0.484, 0.828] |
| v2.0 · publicado | 20 | 10 | 1 | 4 | 5 | 0.909 [0.623, 0.984] | 0.714 [0.454, 0.883] |
| v2.0 · local | 20 | 7 | 2 | 4 | 7 | 0.778 [0.453, 0.937] | 0.636 [0.354, 0.848] |
| v2.1 · todos | 40 | 20 | 2 | 5 | 13 | 0.909 [0.722, 0.975] | 0.8 [0.609, 0.911] |
| v2.1 · publicado | 20 | 10 | 2 | 4 | 4 | 0.833 [0.552, 0.953] | 0.714 [0.454, 0.883] |
| v2.1 · local | 20 | 10 | 0 | 1 | 9 | 1.0 [0.722, 1.0] | 0.909 [0.623, 0.984] |

| juiz | diferença de precisão entre os lados | no critério proposto |
|---|---|---|
| v1 | 0.165 | reprovaria: precisão 0.727 < 0.8; precisão difere 0.165 entre os lados (> 0.15) |
| v2.0 | 0.131 | reprovaria: recall 0.68 < 0.8 |
| v2.1 | 0.167 | reprovaria: precisão difere 0.167 entre os lados (> 0.15) |

**Derrubados pelo código** (o modelo disse que apoia, mas disse que é ambíguo, ou o trecho é nulo, tem menos de 4 palavras ou não está na review): nenhum.

## Pares duvidosos

| par | lado | dono | v1 | v2.0 | v2.1 | motivo do não |
|---|---|---|---|---|---|---|
| P03 | local | não | sim | não | não | modelo disse que não apoia |
| P09 | publicado | não | não | não | sim | — |
| P11 | publicado | sim | não | não | não | modelo disse que não apoia |
| P13 | local | não | sim | não | não | modelo disse que não apoia |
| P15 | local | não | sim | sim | não | modelo disse que não apoia |
| P22 | publicado | não | não | não | não | modelo disse que não apoia |
| P28 | local | sim | sim | não | não | modelo disse que não apoia |
| P34 | publicado | não | sim | sim | sim | — |
| P36 | publicado | não | sim | não | não | modelo disse que não apoia |
| P39 | publicado | não | sim | não | não | modelo disse que não apoia |

## Erros da v2.1

### P09 (duvidoso) — publicado, napoleon-2023/negativas

- tema: "Batalhas decepcionantes"
- dono não · v2.1 sim (modelo disse apoia, não ambíguo; trecho encontrado, 14 palavras; motivo: —) · v2.0 não · v1 não
- trecho: "hay más escenas de Napoleón practicando el sexo con Josefina que de propias batallas"
- raciocínio: "We need to decide if the review supports the bullet's title \"Batalhas decepcionantes\". Review says: expects war movie, but finds porn scenes, says there are more scenes of Napoleon having sex than battles. It says \"no war\" and implies battles are disappointing? It doesn't mention battles being visually impressive, just says not many battles. It criticizes battles? It says there are fewer battle scenes. That supports \"batalhas decepcionantes\" yes. So apoia true. Provide trecho: the phrase that indicates disappointing battles. Likely \"sin embargo, me encuentro con una peli porno\" or \"hay más esc"

### P11 (duvidoso) — publicado, the-substance/positivas

- tema: "Body horror extremo e efeitos práticos"
- dono sim · v2.1 não (modelo disse não apoia, não ambíguo; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v2.0 não · v1 não
- trecho: null
- raciocínio: "We need to check if review supports bullet title \"Body horror extremo e efeitos práticos\". The review says \"Body horror goes crazyyyy!\" and mentions gore and realism. But doesn't mention effects práticos. However supports body horror extreme. Title includes both body horror extremo e efeitos práticos. Review doesn't mention practical effects. So does it support title? The title requires both ideas. If it only supports part, it's NO. So apoia false. trecho null. ambiguo false."

### P17 — publicado, mother-2017/positivas

- tema: "Desempenho de Jennifer Lawrence"
- dono sim · v2.1 não (modelo disse não apoia, não ambíguo; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v2.0 não · v1 sim
- trecho: null
- raciocínio: "We need to check if review supports bullet title \"Desempenho de Jennifer Lawrence\". The review is in Filipino/Tagalog, but contains \"Jennifer Lawrence\". It says \"she's really that MOTHER! Jennifer Lawrence THE WOMAN THAT YOU ARE!!!!\". Not explicitly about performance. It's ambiguous. It's not clearly praising her performance. So likely NÃO. Provide trecho null."

### P28 (duvidoso) — local, the-substance/negativas

- tema: "abordagem excessiva de gore e nus"
- dono sim · v2.1 não (modelo disse não apoia, não ambíguo; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v2.0 não · v1 sim
- trecho: null
- raciocínio: "Need to see if review supports bullet title: \"abordagem excessiva de gore e nus\". Review says: \"The visuals got exhausting, and the fake‑ahh body horror really started to annoy me.\" Also says \"overdone\". No mention of gore or nudity explicitly. It complains about body horror visuals. Could be considered gore? Body horror might imply gore. But the review does not mention nudity. The bullet requires gore and nudity. Review supports excess gore? It says body horror experiment, exhausting visuals. It's ambiguous. It doesn't say gore or nudity. So likely not supporting. So apoia false, trecho null,"

### P29 — publicado, incendies/positivas

- tema: "Reviravolta e revelações"
- dono sim · v2.1 não (modelo disse não apoia, não ambíguo; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v2.0 não · v1 sim
- trecho: null
- raciocínio: "We need to check if the review supports the bullet titled \"Reviravolta e revelações\". Bullet title is about twist and revelations. The review mentions \"en sondaki plot twist pornosu bence çok gereksizdi\" meaning \"the ending plot twist scene was very unnecessary\". So review is about twist, negative. It says twist is unnecessary. Does that support bullet? The bullet says: twist is frequently cited as shocking and brutal, some consider unnecessary, but majority describe it as a blow that reconfigures narrative. Review says twist unnecessary, no mention of shock or reconfiguring. It does not suppo"

### P34 (duvidoso) — publicado, anatomy-of-a-fall/negativas

- tema: "História sem profundidade"
- dono não · v2.1 sim (modelo disse apoia, não ambíguo; trecho encontrado, 36 palavras; motivo: —) · v2.0 sim · v1 sim
- trecho: "O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado"
- raciocínio: "Need to see if review supports bullet title \"História sem profundidade\". Review says film is just a suspense about whether she killed husband, ends simply, ending cheap, kills suspense. That's saying lack of depth. So yes supports. Provide trecho literal. Ambiguo? no. Provide trecho entire sentence. Let's choose sentence: \"O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado\". That's long; but it's whole review text. Use that."

### P40 — publicado, napoleon-2023/medianas

- tema: "Foco excessivo no relacionamento com Josefina"
- dono sim · v2.1 não (modelo disse não apoia, não ambíguo; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v2.0 não · v1 sim
- trecho: null
- raciocínio: "Need to see if review supports bullet title: \"Foco excessivo no relacionamento com Josefina\". Review says: \"movie just focus so much in the personal life of Napoleon instead of showing one of the greatest generals\". That's about personal life, not specifically Josefina. Ambiguity? It says personal life, not specifying relationship. Not explicit about Josefina. Therefore does not support bullet. So output false. Provide trecho? Need to include literal phrase from review that supports. Since doesn't support, trecho null. ambiguo false."

