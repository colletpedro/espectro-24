# Calibração do juiz v2 — versão v2.0

> **CALIBRAÇÃO, NÃO VALIDAÇÃO.** Estes 40 pares são os mesmos usados para ajustar o prompt; o número aqui é otimista por construção. O juiz só vale depois de congelado e medido numa amostra NOVA.

Configuração `a42f48932713ff322535116cb17538bc51a14bdb5e49c9c8389c35b687461c22` · gpt-oss:20b think=low · num_ctx 3584 · num_predict 1024 · seed 20261019

No critério proposto (a pré-registrar antes da amostra nova), esta calibração REPROVARIA: recall 0.68 < 0.8 — precisão e recall ≥ 0,8; diferença de precisão entre os lados ≤ 0.15; diferença medida: 0.131.

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |
|---|---|---|---|---|---|---|---|
| v2 · todos | 40 | 17 | 3 | 8 | 12 | 0.85 [0.64, 0.948] | 0.68 [0.484, 0.828] |
| v2 · publicado | 20 | 10 | 1 | 4 | 5 | 0.909 [0.623, 0.984] | 0.714 [0.454, 0.883] |
| v2 · local | 20 | 7 | 2 | 4 | 7 | 0.778 [0.453, 0.937] | 0.636 [0.354, 0.848] |
| v1 · todos | 40 | 24 | 9 | 1 | 6 | 0.727 [0.558, 0.849] | 0.96 [0.805, 0.993] |
| v1 · publicado | 20 | 13 | 3 | 1 | 3 | 0.812 [0.57, 0.934] | 0.929 [0.685, 0.987] |
| v1 · local | 20 | 11 | 6 | 0 | 3 | 0.647 [0.413, 0.827] | 1.0 [0.741, 1.0] |

**Derrubados pelo trecho** (o modelo disse que apoia, mas o trecho é nulo, tem menos de 4 palavras ou não está na review): P08 (trecho não encontrado na review), P13 (trecho não encontrado na review), P28 (trecho não encontrado na review).

## Erros do v2

### P01 — local, mother-2017/positivas

- tema: "Crítica à figura masculina e ao ego"
- dono sim · v2 não (modelo disse não apoia; trecho encontrado, 33 palavras; motivo: modelo disse que não apoia) · v1 sim
- trecho: "Miam miam on aime ce qui montre le vrai : quand l’homme est un connard, la femme, seule personne cohérente du film, ne se fait pas écouter donc forcément ça part en sucette."
- raciocínio: "Need to see if review supports bullet: bullet claims behavior of male character interpreted as metaphor for ego, lack of empathy, domination over woman. Review says: \"Miam miam on aime ce qui montre le vrai : quand l’homme est un connard, la femme, seule personne cohérente du film, ne se fait pas écouter donc forcément ça part en sucette.\" So mentions when the man is a bastard, woman not heard. Also \"boucle, details ... scene final transgressing moral constructions\". Doesn't explicitly say it's metaphor for ego. It's just criticism of male as connard. So supports idea of domination? Possibly b"

### P04 — local, mother-2017/medianas

- tema: "confusão e falta de clareza"
- dono não · v2 sim (modelo disse apoia; trecho encontrado, 12 palavras; motivo: —) · v1 sim
- trecho: "The early narrative drags so much that it completely lost my interest."
- raciocínio: "Need to see if review supports claim of confusion and lack of clarity. Review says early narrative drags and lost interest, chaotic final act. That supports confusion. So answer yes, trecho providing proof. Provide sentence: \"When it works, it’s dynamic and overwhelming. But all that madness in the final act couldn't rescue the fuuucking slow burn of the first half. The early narrative drags so much that it completely lost my interest.\" That contains lack of clarity. Provide that full sentence."

### P08 — local, anatomy-of-a-fall/negativas

- tema: "final aberto e frustrante"
- dono sim · v2 não (modelo disse apoia; trecho não encontrado, 31 palavras; motivo: trecho não encontrado na review) · v1 sim
- trecho: "je détesté la fin, pcq tout le long on s’attend à une réponse concrète mais le but du film c’est justement de ne donner aucune réponse, du coup c’est super frustrant."
- raciocínio: "Need to see if review supports title \"final aberto e frustrante\". Review says: \"je détesté la fin... c’est super frustrant... le film répond à rien... fin ouverte...\". That supports. So apoia true. Provide trecho exact sentence. Use full sentence from review. For example: \"c’est super frustrant.\" but need 4+ words. Full sentence: \"c’est super frustrant.\" Only 3 words. Not enough. Another: \"c’est super frustrant.\" not. Maybe earlier: \"je détesté la fin, pcq tout le long on s’attend à une réponse concrète mais le but du film c’est justement de ne donner aucune réponse, du coup c’est super frustr"

### P11 (duvidoso) — publicado, the-substance/positivas

- tema: "Body horror extremo e efeitos práticos"
- dono sim · v2 não (modelo disse não apoia; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v1 não
- trecho: null
- raciocínio: "Need to see if review supports title: \"Body horror extremo e efeitos práticos\". Review talks about body horror goes crazy, great job representing horrors of being a woman. No mention of practical effects or gore. So does not support. Return false."

### P15 (duvidoso) — local, napoleon-2023/positivas

- tema: "Abordagem do personagem Napoleão"
- dono não · v2 sim (modelo disse apoia; trecho encontrado, 22 palavras; motivo: —) · v1 sim
- trecho: "Le personnage de Napoléon est incomplet certes, mais loin d'être inintéressant. C'est simplement pas la face de lui qu'on s'attendait à voir."
- raciocínio: "Need to see if review supports that bullet: claim about approach to character: more human, complex, vulnerable, contradictory. Review says: \"Le personnage de Napoléon est incomplet certes, mais loin d'être inintéressant. C'est simplement pas la face de lui qu'on s'attendait à voir.\" This suggests the film shows a different face of him, not as expected, not incomplete? The bullet says film shows more human and complex. The review: says character incomplete but not uninteresting; simply not the expected face. This supports more complex? It's ambiguous. The bullet says attempt to show more human "

### P17 — publicado, mother-2017/positivas

- tema: "Desempenho de Jennifer Lawrence"
- dono sim · v2 não (modelo disse não apoia; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v1 sim
- trecho: null
- raciocínio: "Need to see if review supports. Review says \"she's really that MOTHER! Jennifer Lawrence THE WOMAN THAT YOU ARE!!!!\" It's praising her. But doesn't mention performance or acting quality. So not support. Output {\"trecho\": null, \"apoia\": false}"

### P28 (duvidoso) — local, the-substance/negativas

- tema: "abordagem excessiva de gore e nus"
- dono sim · v2 não (modelo disse apoia; trecho não encontrado, 9 palavras; motivo: trecho não encontrado na review) · v1 sim
- trecho: "the fake‑ahh body horror really started to annoy me."
- raciocínio: "Need to see if review supports claim of excessive gore and nudity. Review says \"fake-ahh body horror really started to annoy me\", \"visuals got exhausting\". It mentions gore and body horror but not explicitly nudity. It supports excessive gore. It's in same sense. So answer SIM. Provide trecho literal: the sentence containing \"fake-ahh body horror\" etc. Let's extract: \"the fake-ahh body horror really started to annoy me.\" That is the evidence. Must be entire sentence. It has >4 words. So trecho is that."

### P29 — publicado, incendies/positivas

- tema: "Reviravolta e revelações"
- dono sim · v2 não (modelo disse não apoia; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v1 sim
- trecho: null
- raciocínio: "We need to check if review supports bullet. Bullet says reviravolta (plot twist) is frequently cited as shocking and brutal, some consider unnecessary, most describe as blow that reconfigures narrative. Review says: \"en sondaki plot twist pornosu bence çok gereksizdi, hikayenin geri kalanı zaten halihazırda içimizi ezen - ama gerçekleşmiş olması kuvvetle muhtemel - olaylar bütünüyken, sondaki o meşhur sahnenin varlığı sadece midemi kaldırdı.\" So says plot twist is unnecessary, just made stomach upset. Does not mention shocking or reconfiguring. So does not support bullet. So apoia false, trech"

### P33 — local, napoleon-2023/medianas

- tema: "Tempo de duração e ritmo narrativo criticados"
- dono sim · v2 não (modelo disse não apoia; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v1 sim
- trecho: null
- raciocínio: "We need to decide if the review supports the bullet. Bullet: title \"Tempo de duração e ritmo narrativo criticados\" (Duration time and narrative pace criticized). Description says long duration seen as problem, especially rhythm cannot maintain interest.\n\nReview says: \"Now ask yourself: Which film is longer? ... After a rewatch the film decidedly conveys its points a lot better, and it’s a decent biopic that separates the man from the myth. That being said, decent is the word for it, because half of the time either Joaquin’s acting is meandering and aimless or Napoleon’s mood is being written t"

### P34 (duvidoso) — publicado, anatomy-of-a-fall/negativas

- tema: "História sem profundidade"
- dono não · v2 sim (modelo disse apoia; trecho encontrado, 36 palavras; motivo: —) · v1 sim
- trecho: "O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado"
- raciocínio: "Need to decide. Review says film is a suspense but ends simply, ending removes suspense. It implies shallow story? It says \"entirely a suspense about if she killed husband or not, but simply arrives at end is just playing answer in simple way ending all suspense.\" So indicates lack of depth. Supports bullet: yes. Provide phrase. Need full sentence: \"O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com todo suspense que foi criado\". Use as is."

### P40 — publicado, napoleon-2023/medianas

- tema: "Foco excessivo no relacionamento com Josefina"
- dono sim · v2 não (modelo disse não apoia; trecho não encontrado, 0 palavras; motivo: modelo disse que não apoia) · v1 sim
- trecho: null
- raciocínio: "Need to see if review supports title: \"Foco excessivo no relacionamento com Josefina\". Review says: \"Saw director's cut and it was a bit boring with a few good scenes, this movie just focus so much in the personal life of Napoleon instead of showing one of the greatest generals in history.\" That mentions focus on personal life, not specifically Josefina, but personal life. Title mentions relationship with Josefina. Review does not mention Josefina, just personal life. So doesn't support. Thus apoia false. trecho null."

