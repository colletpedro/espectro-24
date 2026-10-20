# Calibração do juiz v2 — versão v2.2

> **CALIBRAÇÃO, NÃO VALIDAÇÃO.** Estes 40 pares são os mesmos usados para ajustar o prompt; o número aqui é otimista por construção. O juiz só vale depois de congelado e medido numa amostra NOVA.

Configuração `44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669` · gpt-oss:20b think=low · num_ctx 4096 · num_predict 1024 · seed 20261019

No critério proposto (a pré-registrar antes da amostra nova), esta calibração passaria — precisão e recall ≥ 0,8; diferença de precisão entre os lados ≤ 0.15; diferença medida: 0.046.

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
| v2.2 · todos | 40 | 23 | 5 | 2 | 10 | 0.821 [0.644, 0.921] | 0.92 [0.75, 0.978] |
| v2.2 · publicado | 20 | 12 | 3 | 2 | 3 | 0.8 [0.548, 0.93] | 0.857 [0.601, 0.96] |
| v2.2 · local | 20 | 11 | 2 | 0 | 7 | 0.846 [0.578, 0.957] | 1.0 [0.741, 1.0] |

| juiz | diferença de precisão entre os lados | no critério proposto |
|---|---|---|
| v1 | 0.165 | reprovaria: precisão 0.727 < 0.8; precisão difere 0.165 entre os lados (> 0.15) |
| v2.0 | 0.131 | reprovaria: recall 0.68 < 0.8 |
| v2.1 | 0.167 | reprovaria: precisão difere 0.167 entre os lados (> 0.15) |
| v2.2 | 0.046 | passaria |

**Escolha pré-registrada (REGISTRO.md): congelar a v2.2** — a v2.2 passa nos três critérios.

**Derrubados pelo código** (o modelo disse que apoia, mas disse que é ambíguo, ou o trecho é nulo, tem menos de 4 palavras ou não está na review): nenhum.

## Pares duvidosos

| par | lado | dono | v1 | v2.0 | v2.1 | v2.2 | motivo do não |
|---|---|---|---|---|---|---|---|
| P03 | local | não | sim | não | não | não | modelo disse que não apoia a ideia principal |
| P09 | publicado | não | não | não | sim | sim | — |
| P11 | publicado | sim | não | não | não | sim | — |
| P13 | local | não | sim | não | não | não | modelo disse que não apoia a ideia principal |
| P15 | local | não | sim | sim | não | sim | — |
| P22 | publicado | não | não | não | não | não | modelo disse que não apoia a ideia principal |
| P28 | local | sim | sim | não | não | sim | — |
| P34 | publicado | não | sim | sim | sim | sim | — |
| P36 | publicado | não | sim | não | não | sim | — |
| P39 | publicado | não | sim | não | não | não | modelo disse que não apoia a ideia principal |

## Erros da v2.2

### P04 — local, mother-2017/medianas

- tema: "confusão e falta de clareza"
- dono não · v2.2 sim (modelo disse apoia, evidência clara; trecho encontrado, 34 palavras; motivo: —) · v2.0 sim · v2.1 não · v1 sim
- trecho: "the frantic descent into chaos leading to the finale throws a harsh spotlight on societal collapse, throwing at thr audience brutal, inexplicable human crimes in rapid flashes without giving you a second to breathe."
- raciocínio: "Need to see if review supports title \"confusão e falta de clareza\". Review says chaotic descent into chaos, frantic, harsh spotlight, but also slow burn. Mentions early narrative drags, lost interest. So review indicates confusion and lack of clarity. So supports. Need clear evidence: phrase that indicates confusion/lack of clarity. For example: \"the frantic descent into chaos\" or \"early narrative drags so much that it completely lost my interest.\" We need entire sentence from review. Let's pick sentence: \"the frantic descent into chaos leading to the finale throws a harsh spotlight on societa"

### P09 (duvidoso) — publicado, napoleon-2023/negativas

- tema: "Batalhas decepcionantes"
- dono não · v2.2 sim (modelo disse apoia, evidência clara; trecho encontrado, 14 palavras; motivo: —) · v2.0 não · v2.1 sim · v1 não
- trecho: "hay más escenas de Napoleón practicando el sexo con Josefina que de propias batallas."
- raciocínio: "We need to check if review supports bullet \"Batalhas decepcionantes\" (Portuguese). Review says: expects war movie but it's porn, few battles. That supports idea of disappointing battles. So yes. Provide full sentence that shows that. The phrase: \"hay más escenas de Napoleón practicando el sexo con Josefina que de propias batallas.\" That's the evidence. It's more than 4 words. So we return.\n\n"

### P15 (duvidoso) — local, napoleon-2023/positivas

- tema: "Abordagem do personagem Napoleão"
- dono não · v2.2 sim (modelo disse apoia, evidência clara; trecho encontrado, 11 palavras; motivo: —) · v2.0 sim · v2.1 não · v1 sim
- trecho: "Le personnage de Napoléon est incomplet certes, mais loin d'être inintéressant."
- raciocínio: "We need to check if review supports bullet \"Abordagem do personagem Napoleão\" (Approach to Napoleon character). Review says: \"Le personnage de Napoléon est incomplet certes, mais loin d'être inintéressant. C'est simplement pas la face de lui qu'on s'attendait à voir.\" That comments on character portrayal. So yes supports. Evidence: the sentence about character. Need full sentence. That's: \"Le personnage de Napoléon est incomplet certes, mais loin d'être inintéressant.\" or also following? The sentence includes \"C'est simplement pas la face de lui qu'on s'attendait à voir.\" That is also about ch"

### P29 — publicado, incendies/positivas

- tema: "Reviravolta e revelações"
- dono sim · v2.2 não (modelo disse não apoia, sem evidência clara afirmada; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia a ideia principal) · v2.0 não · v2.1 não · v1 sim
- trecho: null
- raciocínio: "We need to check if review supports bullet \"Reviravolta e revelações\" (Plot twist and revelations). Review mentions plot twist: \"en sondaki plot twist pornosu bence çok gereksizdi\" => says plot twist is unnecessary. It does not support. So answer NÃO. Provide null, false, false."

### P34 (duvidoso) — publicado, anatomy-of-a-fall/negativas

- tema: "História sem profundidade"
- dono não · v2.2 sim (modelo disse apoia, evidência clara; trecho encontrado, 36 palavras; motivo: —) · v2.0 sim · v2.1 sim · v1 sim
- trecho: "O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado"
- raciocínio: "We need to decide. Title \"História sem profundidade\". Review says film is just suspense about murder, ends simply, kills suspense. That indicates shallow story? The review implies lack of depth. So supports idea. It is clear. Provide trecho. Sentence: \"O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado\". That's whole. That's >4 words. So output."

### P36 (duvidoso) — publicado, incendies/medianas

- tema: "Ritmo lento e momentos arrastados"
- dono não · v2.2 sim (modelo disse apoia, evidência clara; trecho encontrado, 26 palavras; motivo: —) · v2.0 não · v2.1 não · v1 sim
- trecho: "By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story."
- raciocínio: "Need to see if review supports idea \"Ritmo lento e momentos arrastados\". Review says: \"By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story.\" Mentions \"slow sad family and war drama\". So yes supports slow rhythm. Provide trecho. Let's find exact phrase: \"By the time this slow sad family and war drama becomes disturbingly devastating\". That includes \"slow sad\". So yes. Provide trecho entire sentence. It has >4 words. Provide JSON."

### P40 — publicado, napoleon-2023/medianas

- tema: "Foco excessivo no relacionamento com Josefina"
- dono sim · v2.2 não (modelo disse não apoia, sem evidência clara afirmada; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia a ideia principal) · v2.0 não · v2.1 não · v1 sim
- trecho: null
- raciocínio: "We need to decide. Bullet title: \"Foco excessivo no relacionamento com Josefina\" meaning focus excessive on relationship with Josephine. Review says: \"just focus so much in the personal life of Napoleon instead of showing one of the greatest generals\". That's about personal life in general, not specifically Josephine. The bullet specifically about relationship with Josefina. The review does not mention Josephine, only personal life. So does it support? According to rules, if review supports the nucleus of bullet: the nucleus is focus on relationship with Josefina. Review says focus on personal"

