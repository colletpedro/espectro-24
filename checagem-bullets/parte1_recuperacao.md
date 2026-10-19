# Parte 1b — as 5 reviews do grupo mais parecidas com cada bullet

Modelo: `intfloat/multilingual-e5-base` (snapshot `d128750597153bb5987e10b1c3493a34e5a4502a`, pesos sha256 `a18a44fad1d0b46d…`), local, em numpy (`scripts/encoder_e5.py`). Query = `query: <tema>. <descrição>`; review = `passage: <texto>`, em janelas de até 900 caracteres, e a similaridade da review é a do seu melhor trecho. 691 pedaços para 600 reviews; 0 truncados pelo teto de 512 tokens.

**A ordem é por `score` = `sim` − o deslocamento da review** (a média do `sim` dela contra os 1690 bullets publicados do resto do catálogo). Sem centrar, poucas reviews genéricas, na língua das queries, dominavam o top-5 de quase todo bullet; a escolha foi medida pelo eixo e está em `checagem_bullets.recuperar`.

**Como ler os números:** o e5 concentra os cossenos entre ~0,7 e 1,0 (FAQ do modelo); o que informa é a ORDEM dentro do grupo, não o valor absoluto. Ser parecida não é apoiar — quem decide apoio é o juiz (Parte 2). `eixo` ✓ = a review tem o eixo do bullet no consenso.

| lado | bullets | `sim` médio do top-1 | `score` médio do top-5 | reviews do top-5 com o eixo do bullet |
|---|---|---|---|---|
| publicado | 90 | 0.816 | +0.024 | 296/435 |
| local | 90 | 0.810 | +0.022 | 285/440 |

## Anatomia de uma Queda

### publicado — DeepSeek (síntese publicada)

**[negativas] Ritmo lento e arrastado** — eixo `ritmo`, declarado 25/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.848 | ✓ | (2.0★) c’est un film très lent, avec une atmosphère étrange et de très très très très longs dialogues. c’est un infini procès, avec une embrouille interminable, qui ré… |
| 2 | +0.027 | 0.792 | ✓ | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |
| 3 | +0.024 | 0.828 | ✓ | (1.5★) aunque la película no me haya gustado la verdad es que admito que es bastante entretenida, sus dialogos te mantienen fija en el televisor esperando a ver cuál e… |
| 4 | +0.023 | 0.792 | ✓ | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |
| 5 | +0.022 | 0.831 | ✓ | (1.5★) Siento que es innecesariamente larga y los puntos que tocan tampoco se profundiza mucho, lo que hace que sea bastante superficial 1. Historia y Guion: 3/10 El g… |

**[negativas] Final em aberto frustrante** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.024 | 0.843 | ✓ | (2.0★) nao da pra negar o altissimo nivel das atuacoes e da ambientação, mas desse final em aberto? 2 horas vendo essa merda pra nao saber se ela matou ou nao aquele o… |
| 2 | +0.020 | 0.836 | ✓ | (1.5★) Esperaba más, como un plot twis o al menos saber que paso realmente. Pero no, es muy lenta, y hasta a veces aburrida, si es interesante el método de investigaci… |
| 3 | +0.016 | 0.793 | ✓ | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 4 | +0.016 | 0.807 | ✓ | (2.0★) PALLOOOOSO, troppo lento e il finale scontato siccome non è stato mostrato nulla che potesse far pensare ad altre ipotesi. povero quel dolce cagnolino, ha inger… |
| 5 | +0.015 | 0.778 | ✓ | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |

**[negativas] História sem profundidade** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.838 | ✓ | (1.5★) Esperaba más, como un plot twis o al menos saber que paso realmente. Pero no, es muy lenta, y hasta a veces aburrida, si es interesante el método de investigaci… |
| 2 | +0.018 | 0.810 | ✓ | (2.0★) its interesting but boring its understandable but confusing tf?? anyways i read a review from the LB crew and realized the story behind it was even more boring … |
| 3 | +0.015 | 0.778 | ✓ | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 4 | +0.013 | 0.836 | ✓ | (2.0★) O filme é inteiro um suspense sobre se ela matou o marido ou não pra simplesmente chegar no final é só jogar a resposta de um jeito muito simples acabando com t… |
| 5 | +0.013 | 0.839 | ✓ | (2.0★) Por não ser um filme tão envolvente e ter um enredo que enrole um pouco, não me pegou tanto. Mas envolve assuntos interessantes e a relação da mãe com o filho é… |

**[negativas] Personagens pouco cativantes** — eixo `roteiro_estrutura`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.020 | 0.782 | ✓ | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 2 | +0.014 | 0.808 | ✓ | (0.5★) Ana olayın yaşanmasından önce karakterlerle bağ kurmamız için bize hiçbir neden verilmediği için yaşanan trajedi de artık pek umrumda olmadı. İzleyiciyi duygusa… |
| 3 | +0.013 | 0.778 | ✓ | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |
| 4 | +0.013 | 0.784 | ✓ | (2.0★) Just didn't enjoy it for some reason- might have been my mood on the day. Found the case and intricacies of the French legal system to be dull. I'll give it a r… |
| 5 | +0.011 | 0.788 | ✓ | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |

**[negativas] Mistura de idiomas incomoda** — eixo `som_trilha`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.039 | 0.840 |  | (1.5★) Yes, in the end there is a space for uncertainty for the memory, especially given the lost of sight, the involvement of emotions, the version that the superego … |
| 2 | +0.019 | 0.789 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |
| 3 | +0.019 | 0.784 |  | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |
| 4 | +0.018 | 0.795 |  | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 5 | +0.017 | 0.818 |  | (2.0★) C'est un grand non pour ma part. Le mélange anglais français pour m'abattre, c'est mou, c'est chiant. Oscar 2024, César et Palme d'or 2023, bah non hein. Chiant… |

**[negativas] Expectativas não correspondidas** — eixo `expectativa`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.026 | 0.836 | ✓ | (2.0★) Afirmaría que mis expectativas fueron muy altas, basadas en comentarios positivos que vi por internet y el hype. No me parece una película mala, pero tampoco me… |
| 2 | +0.025 | 0.799 | ✓ | (1.0★) I've seen a few movies that bummed me out because of all the hype, but this one, I just don't get why people like it. Is there a prevalent fascination with film… |
| 3 | +0.016 | 0.790 | ✓ | (1.0★) I don’t get why this is so hyped. Like, it’s litteraly feeling like watching an unfinished episode of a French cop serie… and the tracks have bothered my ADHD |
| 4 | +0.015 | 0.791 |  | (2.0★) Acting was top tier the story was alright the ending was fucking horrible. This is the most drawn out unsatisfying movie of all time. I’ve seen human centipede … |
| 5 | +0.013 | 0.782 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |

**[medianas] Ritmo lento e duração excessiva** — eixo `ritmo`, declarado 20/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.855 | ✓ | (2.5★) é um filme muito bom, mas pelo amor de deus que filme longo véi. desnecessariamente longo. meu cérebro de brainrot 24/7 quase colapsou assistindo isso |
| 2 | +0.028 | 0.819 | ✓ | (3.0★) I can appreciate the acting and camera work here but not really much else? I was waiting the whole movie for a turn that will knock me off my shoes but that jus… |
| 3 | +0.027 | 0.787 | ✓ | (2.5★) Idk why but felt too long for me. Still a visually interesting film but I was left yearning for something a little more. Dog was ⭐️⭐️⭐️⭐️⭐️ actor shout out my b… |
| 4 | +0.025 | 0.793 | ✓ | (3.0★) Langatmiger Gerichtsfilm, der im Gegensatz zu bekannten Vertretern des Genres auf Twists und Spannung verzichtet. Vielmehr stellt er die Beziehungskrise zwische… |
| 5 | +0.024 | 0.836 | ✓ | (3.0★) L'histoire n'est pas quelque chose d'extraordinaire, les acteurs sont bien mais je n'ai pas été transporté quoi. Je trouve que le film s'étire trop en longueur … |

**[medianas] Final ambíguo e sem respostas definitivas** — eixo `roteiro_estrutura`, declarado 13/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.020 | 0.797 |  | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 2 | +0.018 | 0.842 | ✓ | (3.0★) je sais pas j'ai aimé sans aimer pour moi elle est innocente, mais idkw le fils est trop bizarre ??? et y'a pas de fin ça m'agace moi il m'a fait grv peur mais … |
| 3 | +0.015 | 0.824 | ✓ | (3.0★) Siento que fue un capítulo extendido de la ley y el orden, tengo que ponerme a investigar cual fue la intención del director con la película porque me pareció u… |
| 4 | +0.014 | 0.825 | ✓ | (3.0★) L'AVOCAT CHAUVE 🫯 Jcomprends pas pourquoi ils ont fait tout un procès alors qu'on sait tous que C'EST ÉMILE, émile, c'est émile le tueur 🪤💥 bien joué cara, et d… |
| 5 | +0.013 | 0.807 | ✓ | (3.0★) i mean it was very interesting and complicated at the same time, i just don't know if it was worth That long... what really captured my attention was the dog an… |

**[medianas] Atuações fortes (incluindo o cachorro)** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.027 | 0.787 | ✓ | (2.5★) Idk why but felt too long for me. Still a visually interesting film but I was left yearning for something a little more. Dog was ⭐️⭐️⭐️⭐️⭐️ actor shout out my b… |
| 2 | +0.021 | 0.797 | ✓ | (3.0★) I rarely rate a movie above 2 stars but anatomy of a fall really does deserve it - this movie grabbed my attention throughout - very thought provoking - elite a… |
| 3 | +0.021 | 0.792 |  | (3.0★) ain’t no way that kid didn’t lie his ass off to save his mom once he believed in her innocence, he gave it his all to shut that rude ass judge up. we saw he can… |
| 4 | +0.021 | 0.834 | ✓ | (3.0★) Casi la quito porque se me estaba haciendo lenta pero los juicios han acabado dándomelo todo y la actuación del perro CINE Al final me quedé esperando una revel… |
| 5 | +0.021 | 0.814 |  | (3.0★) i mean it was very interesting and complicated at the same time, i just don't know if it was worth That long... what really captured my attention was the dog an… |

**[medianas] Promotor irritante e processo judicial** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.819 |  | (3.0★) França reveja seu sistema judiciário pra ontem!! Eu seriamente pensei durante o final que o Daniel era o culpado 😝 EN: I'm sure the French judicial system must … |
| 2 | +0.019 | 0.819 | ✓ | (2.5★) J’aime pas la réalisation ? y’avait tellement mieux à faire j’ai l’impression… Plusieurs choses m’empêchent de réellement passer un bon moment - Le côté médiati… |
| 3 | +0.016 | 0.793 |  | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 4 | +0.015 | 0.841 | ✓ | (3.0★) eu acho que ele planejou se matar pra culpa cair na esposa pq ele realmente tinha muita inveja e raiva dela #sóacho mas falando sério, nunca senti tanto ódio de… |
| 5 | +0.015 | 0.819 |  | (3.0★) L'avocat général est DÉTESTABLE, on a envie de lui foutre 2-3 claques plus d'une fois. Mais plus sérieusement, c'est un très beau film. Peut-être un peu long et… |

**[medianas] Foco nas relações humanas e na subjetividade da verdade** — eixo `tom_atmosfera`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.798 |  | (3.0★) I liked the sharp development of the plot but was a bit disappointed because we don't get to see the truth, but that made it deeper in a way where it represents… |
| 2 | +0.025 | 0.796 |  | (3.0★) ain’t no way that kid didn’t lie his ass off to save his mom once he believed in her innocence, he gave it his all to shut that rude ass judge up. we saw he can… |
| 3 | +0.022 | 0.800 |  | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 4 | +0.022 | 0.816 |  | (3.0★) i mean it was very interesting and complicated at the same time, i just don't know if it was worth That long... what really captured my attention was the dog an… |
| 5 | +0.022 | 0.832 |  | (3.0★) L'AVOCAT CHAUVE 🫯 Jcomprends pas pourquoi ils ont fait tout un procès alors qu'on sait tous que C'EST ÉMILE, émile, c'est émile le tueur 🪤💥 bien joué cara, et d… |

**[medianas] Expectativa por um grande acontecimento que não vem** — eixo `expectativa`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.831 | ✓ | (3.0★) Me gusto auque esperaba otra cosa. No se si me habré perdido algunos detalles pero al final no quedó muy claro lo que realmente paso. Me gustaron las partes don… |
| 2 | +0.026 | 0.794 |  | (3.0★) I liked the sharp development of the plot but was a bit disappointed because we don't get to see the truth, but that made it deeper in a way where it represents… |
| 3 | +0.021 | 0.834 |  | (3.0★) Casi la quito porque se me estaba haciendo lenta pero los juicios han acabado dándomelo todo y la actuación del perro CINE Al final me quedé esperando una revel… |
| 4 | +0.021 | 0.822 |  | (3.0★) me esperaba un giro de guion pero entiendo que la gracia es que no haya ningún giro: sino el proceso judicial y como atar los cabos para incriminar o salvar y e… |
| 5 | +0.020 | 0.809 | ✓ | (3.0★) i was feeling really sick watching this so that mght be why i didnt think it was so great but it didnt work for me and there was not enough to make me invest in… |

**[positivas] Atuações excepcionais** — eixo `atuacao`, declarado 25/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.048 | 0.810 | ✓ | (4.5★) GOD THIS IS GOOD. Still sits easily in one of my favorite releases of the past few years. The performances are outstanding, and despite its length, the entire f… |
| 2 | +0.023 | 0.796 | ✓ | (4.0★) Gets better on a rewatch but still the pacing was definitely a bit off. But what a beautiful screenplay and that argument scene is some of the best writing and … |
| 3 | +0.023 | 0.807 | ✓ | (3.5★) Palme d’or 2023 et couronné de nombreuses récompenses, Anatomie d’une chute de Justine Triet mérite largement sa réputation. Derrière son apparence de film judi… |
| 4 | +0.021 | 0.810 | ✓ | (4.5★) This was awesome. Might be a higher score on rewatch. I’m gonna sleep and give my full thoughts tomorrow. Best Criterion purchase I made since Memories of Murde… |
| 5 | +0.019 | 0.824 | ✓ | (3.5★) Mettez du respect et de la lumière sur le cinéma féminin. Un film de procès qui ne cherche jamais vraiment le verdict, mais la faille. Triet construit son récit… |

**[positivas] Dissolução e complexidade conjugal** — eixo `roteiro_estrutura`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.037 | 0.819 | ✓ | (4.5★) La muerte del marido es una excusa para desmenuzar la propia anatomía de la pareja y sus propias repercusiones con la excusa del juicio. Película muy inteligent… |
| 2 | +0.028 | 0.797 | ✓ | (4.5★) Incredible performances from the mother and son. I got goosebumps during the couple’s argument presented during the trial and the final testimony from Daniel. I… |
| 3 | +0.026 | 0.817 |  | (4.0★) The movie asks an important question: can you feel the depth and the strain of learning to find yourself in the complicated context of a long-term relationship … |
| 4 | +0.023 | 0.809 | ✓ | (5.0★) How does love fade, how do you pick whose dream to prioritize in life, and who do you blame for problems? You get to reflect on these questions when watching th… |
| 5 | +0.022 | 0.838 | ✓ | (4.0★) buf que fuerte, me ha encantado, es un juicio en resumen pero es tan profunda hay diálogos que me han hecho sentir que me entrometía en la pareja, he sentido ta… |

**[positivas] Roteiro inteligente e diálogos afiados** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.807 | ✓ | (4.0★) Really well crafted take on the importance of nuances. Egregious vibes from the guy in the red robe compared to the amazing vibes from the handsome fella on Hül… |
| 2 | +0.014 | 0.830 | ✓ | (4.0★) buf que fuerte, me ha encantado, es un juicio en resumen pero es tan profunda hay diálogos que me han hecho sentir que me entrometía en la pareja, he sentido ta… |
| 3 | +0.012 | 0.783 | ✓ | (4.0★) I was expecting more of a follow through with the plot but it turned out to be so meaningful. I was rooting for her, not because I liked her but for her son’s s… |
| 4 | +0.012 | 0.797 | ✓ | (4.0★) Ein spannendes Gerichtsdrama, das Fragen nach Wahrheit, Schuld und Wahrnehmung aufwirft. Die vielschichtigen Figuren und die dichte Atmosphäre regen zum Nachden… |
| 5 | +0.010 | 0.811 | ✓ | (4.5★) Preciosa. No podía parar de pensar en la hostilidad de esa sociedad. Impresionante la construcción de los personajes y el como se mantuvo el misterio y a la vez… |

**[positivas] Tensão e suspense no tribunal** — eixo `ritmo`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.032 | 0.817 |  | (4.0★) Ein spannendes Gerichtsdrama, das Fragen nach Wahrheit, Schuld und Wahrnehmung aufwirft. Die vielschichtigen Figuren und die dichte Atmosphäre regen zum Nachden… |
| 2 | +0.028 | 0.830 | ✓ | (4.0★) iki bucuk saat olsa da beni icine hemen aldi. sahnelerin en guzel yani gercek hissetirmesiydi. boyle filmlere bayiliyorum. ozellikle mahkeme sahneleri muazzamdi… |
| 3 | +0.025 | 0.797 | ✓ | (4.0★) I’m reminded again how lawyers can twist your words so fast, it’s impressive. Surprisingly to me the court scenes felt faster than the first hour or so, Daniel … |
| 4 | +0.024 | 0.814 |  | (5.0★) From the stellar performances to the polaroids, dialogue and the kitchen, everything felt so authentic. It made the camera work feel so intrusive. But the ruthl… |
| 5 | +0.021 | 0.790 |  | (4.5★) Incredible performances from the mother and son. I got goosebumps during the couple’s argument presented during the trial and the final testimony from Daniel. I… |

**[positivas] Direção e atmosfera realista** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.015 | 0.777 | ✓ | (4.5★) GOD THIS IS GOOD. Still sits easily in one of my favorite releases of the past few years. The performances are outstanding, and despite its length, the entire f… |
| 2 | +0.014 | 0.804 | ✓ | (5.0★) From the stellar performances to the polaroids, dialogue and the kitchen, everything felt so authentic. It made the camera work feel so intrusive. But the ruthl… |
| 3 | +0.012 | 0.800 |  | (4.5★) This was awesome. Might be a higher score on rewatch. I’m gonna sleep and give my full thoughts tomorrow. Best Criterion purchase I made since Memories of Murde… |
| 4 | +0.012 | 0.792 |  | (4.5★) In awe of just how much tension this film is able produce with essentially no score outside of Daniel’s piano and 50’s P.I.M.P. instrumental. Incredible work fr… |
| 5 | +0.010 | 0.794 | ✓ | (3.5★) Palme d’or 2023 et couronné de nombreuses récompenses, Anatomie d’une chute de Justine Triet mérite largement sa réputation. Derrière son apparence de film judi… |

**[positivas] Reflexões sobre verdade e percepção** — eixo `tom_atmosfera`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.033 | 0.819 |  | (5.0★) How does love fade, how do you pick whose dream to prioritize in life, and who do you blame for problems? You get to reflect on these questions when watching th… |
| 2 | +0.023 | 0.814 | ✓ | (4.0★) The movie asks an important question: can you feel the depth and the strain of learning to find yourself in the complicated context of a long-term relationship … |
| 3 | +0.022 | 0.807 | ✓ | (4.0★) Ein spannendes Gerichtsdrama, das Fragen nach Wahrheit, Schuld und Wahrnehmung aufwirft. Die vielschichtigen Figuren und die dichte Atmosphäre regen zum Nachden… |
| 4 | +0.017 | 0.786 |  | (4.5★) Incredible performances from the mother and son. I got goosebumps during the couple’s argument presented during the trial and the final testimony from Daniel. I… |
| 5 | +0.016 | 0.798 |  | (4.5★) I had extensive thoughts about this movie, but i forgot them I think it'd be more impactful if i cared more for family dynamics Good movie very engaging |

### local — qwen3:14b (Ollama)

**[negativas] ritmo lento e monótono** — eixo `ritmo`, declarado 25/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.794 | ✓ | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |
| 2 | +0.028 | 0.797 | ✓ | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |
| 3 | +0.028 | 0.848 | ✓ | (2.0★) c’est un film très lent, avec une atmosphère étrange et de très très très très longs dialogues. c’est un infini procès, avec une embrouille interminable, qui ré… |
| 4 | +0.027 | 0.830 | ✓ | (2.0★) DE // ENG Ein Film für Fans von Kriminalfällen. Man kann schön mitraten, interpretieren und Hypothesen aufstellen. Man bekommt auch genügend Zeit dafür. Denn ma… |
| 5 | +0.027 | 0.837 | ✓ | (1.5★) Siento que es innecesariamente larga y los puntos que tocan tampoco se profundiza mucho, lo que hace que sea bastante superficial 1. Historia y Guion: 3/10 El g… |

**[negativas] final aberto e frustrante** — eixo `roteiro_estrutura`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.812 | ✓ | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 2 | +0.029 | 0.848 | ✓ | (2.0★) c’est un film très lent, avec une atmosphère étrange et de très très très très longs dialogues. c’est un infini procès, avec une embrouille interminable, qui ré… |
| 3 | +0.026 | 0.795 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |
| 4 | +0.025 | 0.844 | ✓ | (2.0★) nao da pra negar o altissimo nivel das atuacoes e da ambientação, mas desse final em aberto? 2 horas vendo essa merda pra nao saber se ela matou ou nao aquele o… |
| 5 | +0.023 | 0.848 | ✓ | (2.0★) gosto de filmes de tribunal assim, mas odeio filme que deixa o "final" em aberto, tipo apenas conte o que aconteceu no final logo ao invés de deixar pra imagina… |

**[negativas] trama pouco envolvente** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.791 | ✓ | (2.0★) Just didn't enjoy it for some reason- might have been my mood on the day. Found the case and intricacies of the French legal system to be dull. I'll give it a r… |
| 2 | +0.018 | 0.795 | ✓ | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 3 | +0.016 | 0.779 | ✓ | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 4 | +0.014 | 0.831 | ✓ | (1.5★) Esperaba más, como un plot twis o al menos saber que paso realmente. Pero no, es muy lenta, y hasta a veces aburrida, si es interesante el método de investigaci… |
| 5 | +0.014 | 0.806 | ✓ | (1.0★) A good insight/deep dive/illustration into the lived experience of a court case and its impact and life long implications. I felt its purpose was cognitive and … |

**[negativas] diálogos longos e repetitivos** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.790 | ✓ | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 2 | +0.022 | 0.791 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |
| 3 | +0.020 | 0.837 | ✓ | (1.5★) Esperaba más, como un plot twis o al menos saber que paso realmente. Pero no, es muy lenta, y hasta a veces aburrida, si es interesante el método de investigaci… |
| 4 | +0.019 | 0.796 | ✓ | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 5 | +0.019 | 0.784 | ✓ | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |

**[negativas] atuações insuficientes** — eixo `atuacao`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.781 | ✓ | (2.0★) Surprised this movie has such high reviews. Felt super slow. Great acting but the plot just was not there. Also, I hate French they should just speak English th… |
| 2 | +0.015 | 0.786 | ✓ | (1.0★) Music was cool, acting was decent. Story sucked ass. Am I too stupid to understand this movie? Am I really left to guess wtf was the result of the movie? If I’m… |
| 3 | +0.014 | 0.776 |  | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 4 | +0.011 | 0.788 |  | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 5 | +0.011 | 0.780 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |

**[negativas] direção e estética visual fraca** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.807 |  | (2.0★) 2.4 < Too high DAY 13 OF MY CRITERION CHALLENGE 2026 TODAY'S CATEGORY IS: "2020'S" To be clear, I don't believe that Anatomy of a Fall is a terrible film, it ju… |
| 2 | +0.012 | 0.789 |  | (2.0★) (2023) France- French, English. I don't really understand this film. The ambiguous ending left me feeling like "what was the purpose of this film?" It was also … |
| 3 | +0.010 | 0.810 |  | (2.0★) C'est un grand non pour ma part. Le mélange anglais français pour m'abattre, c'est mou, c'est chiant. Oscar 2024, César et Palme d'or 2023, bah non hein. Chiant… |
| 4 | +0.009 | 0.772 |  | (2.0★) So terribly boring. The courtroom procedures, including the judge, really irritated me. Still unable to see the point of it all. Only highlight was the marital … |
| 5 | +0.009 | 0.779 |  | (1.0★) I don’t know why I thought I would’ve enjoyed this movie. Everyone was speaking French. The last 30 mins was the best part. It took way to long and it was rathe… |

**[medianas] ritmo lento e alongado** — eixo `ritmo`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.015 | 0.839 |  | (3.0★) je sais pas j'ai aimé sans aimer pour moi elle est innocente, mais idkw le fils est trop bizarre ??? et y'a pas de fin ça m'agace moi il m'a fait grv peur mais … |
| 2 | +0.012 | 0.791 | ✓ | (3.0★) french tom scott it was alright! not that revelatory. fairly restrained which did make it drag a teensy bit. i liked the kid’s final testimony, i thought it was… |
| 3 | +0.011 | 0.823 | ✓ | (3.0★) L'histoire n'est pas quelque chose d'extraordinaire, les acteurs sont bien mais je n'ai pas été transporté quoi. Je trouve que le film s'étire trop en longueur … |
| 4 | +0.010 | 0.800 |  | (2.5★) ummmm yeah. i don't really have any thoughts at all about this movie. wasn't very good and wasn't very bad. it was exactly what it was with no fluff and no deep… |
| 5 | +0.010 | 0.801 | ✓ | (3.0★) I can appreciate the acting and camera work here but not really much else? I was waiting the whole movie for a turn that will knock me off my shoes but that jus… |

**[medianas] foco no processo judicial e nas relações familiares** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.027 | 0.805 |  | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 2 | +0.020 | 0.814 | ✓ | (3.0★) i mean it was very interesting and complicated at the same time, i just don't know if it was worth That long... what really captured my attention was the dog an… |
| 3 | +0.018 | 0.788 | ✓ | (3.0★) ain’t no way that kid didn’t lie his ass off to save his mom once he believed in her innocence, he gave it his all to shut that rude ass judge up. we saw he can… |
| 4 | +0.015 | 0.816 | ✓ | (3.0★) me esperaba un giro de guion pero entiendo que la gracia es que no haya ningún giro: sino el proceso judicial y como atar los cabos para incriminar o salvar y e… |
| 5 | +0.013 | 0.837 | ✓ | (3.0★) je sais pas j'ai aimé sans aimer pour moi elle est innocente, mais idkw le fils est trop bizarre ??? et y'a pas de fin ça m'agace moi il m'a fait grv peur mais … |

**[medianas] interpretação da verdade e ambiguidade** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.020 | 0.830 | ✓ | (3.0★) L'AVOCAT CHAUVE 🫯 Jcomprends pas pourquoi ils ont fait tout un procès alors qu'on sait tous que C'EST ÉMILE, émile, c'est émile le tueur 🪤💥 bien joué cara, et d… |
| 2 | +0.013 | 0.790 |  | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 3 | +0.012 | 0.814 | ✓ | (3.0★) me esperaba un giro de guion pero entiendo que la gracia es que no haya ningún giro: sino el proceso judicial y como atar los cabos para incriminar o salvar y e… |
| 4 | +0.012 | 0.782 | ✓ | (3.0★) ain’t no way that kid didn’t lie his ass off to save his mom once he believed in her innocence, he gave it his all to shut that rude ass judge up. we saw he can… |
| 5 | +0.011 | 0.780 | ✓ | (3.0★) I liked the sharp development of the plot but was a bit disappointed because we don't get to see the truth, but that made it deeper in a way where it represents… |

**[medianas] atuações fortes, especialmente de Sandra Hüller** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.026 | 0.820 | ✓ | (3.0★) Me pareció una película muy interesante. Desde el principio logró mantener mi atención, pero lo que más me gustó fue la actuación de Sandra Hüller. El hecho de … |
| 2 | +0.008 | 0.779 |  | (3.0★) ain’t no way that kid didn’t lie his ass off to save his mom once he believed in her innocence, he gave it his all to shut that rude ass judge up. we saw he can… |
| 3 | +0.008 | 0.831 |  | (3.0★) je sais pas j'ai aimé sans aimer pour moi elle est innocente, mais idkw le fils est trop bizarre ??? et y'a pas de fin ça m'agace moi il m'a fait grv peur mais … |
| 4 | +0.006 | 0.783 | ✓ | (3.0★) I rarely rate a movie above 2 stars but anatomy of a fall really does deserve it - this movie grabbed my attention throughout - very thought provoking - elite a… |
| 5 | +0.005 | 0.785 | ✓ | (3.0★) i tried giving this another chance because i genuinely do like sandra and think she's great but i'm bored and it just doesn't hold my attention like it should :… |

**[medianas] presença do cachorro como elemento simbólico** — eixo `direcao_imagem`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.789 | ✓ | (2.5★) Idk why but felt too long for me. Still a visually interesting film but I was left yearning for something a little more. Dog was ⭐️⭐️⭐️⭐️⭐️ actor shout out my b… |
| 2 | +0.015 | 0.804 |  | (3.0★) i was feeling really sick watching this so that mght be why i didnt think it was so great but it didnt work for me and there was not enough to make me invest in… |
| 3 | +0.014 | 0.827 |  | (3.0★) Casi la quito porque se me estaba haciendo lenta pero los juicios han acabado dándomelo todo y la actuación del perro CINE Al final me quedé esperando una revel… |
| 4 | +0.013 | 0.806 |  | (3.0★) i mean it was very interesting and complicated at the same time, i just don't know if it was worth That long... what really captured my attention was the dog an… |
| 5 | +0.007 | 0.780 |  | (3.0★) I was upset during the whole movie when I was hearing the original music for a song that 50 cent sampled to make a song I love in P.I.M.P. And here I thought 50… |

**[medianas] críticas ao sistema judicial francês** — eixo `critica_social`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.046 | 0.823 | ✓ | (3.0★) My only conclusion is that the French court system seems as stable as a house made of dry spaghetti and marshmallows Kid be lying, mom be lying, dad be bumping … |
| 2 | +0.036 | 0.833 | ✓ | (3.0★) França reveja seu sistema judiciário pra ontem!! Eu seriamente pensei durante o final que o Daniel era o culpado 😝 EN: I'm sure the French judicial system must … |
| 3 | +0.024 | 0.834 |  | (3.0★) L'AVOCAT CHAUVE 🫯 Jcomprends pas pourquoi ils ont fait tout un procès alors qu'on sait tous que C'EST ÉMILE, émile, c'est émile le tueur 🪤💥 bien joué cara, et d… |
| 4 | +0.018 | 0.842 |  | (3.0★) je sais pas j'ai aimé sans aimer pour moi elle est innocente, mais idkw le fils est trop bizarre ??? et y'a pas de fin ça m'agace moi il m'a fait grv peur mais … |
| 5 | +0.016 | 0.795 |  | (3.0★) french tom scott it was alright! not that revelatory. fairly restrained which did make it drag a teensy bit. i liked the kid’s final testimony, i thought it was… |

**[positivas] complexidade dos relacionamentos** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.034 | 0.824 |  | (4.0★) The movie asks an important question: can you feel the depth and the strain of learning to find yourself in the complicated context of a long-term relationship … |
| 2 | +0.021 | 0.807 | ✓ | (5.0★) How does love fade, how do you pick whose dream to prioritize in life, and who do you blame for problems? You get to reflect on these questions when watching th… |
| 3 | +0.021 | 0.790 | ✓ | (4.5★) Incredible performances from the mother and son. I got goosebumps during the couple’s argument presented during the trial and the final testimony from Daniel. I… |
| 4 | +0.018 | 0.834 | ✓ | (4.0★) buf que fuerte, me ha encantado, es un juicio en resumen pero es tan profunda hay diálogos que me han hecho sentir que me entrometía en la pareja, he sentido ta… |
| 5 | +0.018 | 0.800 | ✓ | (4.5★) La muerte del marido es una excusa para desmenuzar la propia anatomía de la pareja y sus propias repercusiones con la excusa del juicio. Película muy inteligent… |

**[positivas] desempenho atorial** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.061 | 0.823 | ✓ | (4.5★) GOD THIS IS GOOD. Still sits easily in one of my favorite releases of the past few years. The performances are outstanding, and despite its length, the entire f… |
| 2 | +0.038 | 0.827 | ✓ | (4.5★) This was awesome. Might be a higher score on rewatch. I’m gonna sleep and give my full thoughts tomorrow. Best Criterion purchase I made since Memories of Murde… |
| 3 | +0.037 | 0.821 | ✓ | (3.5★) Palme d’or 2023 et couronné de nombreuses récompenses, Anatomie d’une chute de Justine Triet mérite largement sa réputation. Derrière son apparence de film judi… |
| 4 | +0.030 | 0.809 | ✓ | (4.0★) I really liked the character portrayals, those were certainly my favorite part! The characters felt so very real, and nuanced, and alive; I looked at Sandra Hül… |
| 5 | +0.027 | 0.832 | ✓ | (3.5★) Mettez du respect et de la lumière sur le cinéma féminin. Un film de procès qui ne cherche jamais vraiment le verdict, mais la faille. Triet construit son récit… |

**[positivas] tensão e suspense no tribunal** — eixo `ritmo`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.810 |  | (4.0★) Ein spannendes Gerichtsdrama, das Fragen nach Wahrheit, Schuld und Wahrnehmung aufwirft. Die vielschichtigen Figuren und die dichte Atmosphäre regen zum Nachden… |
| 2 | +0.022 | 0.794 | ✓ | (4.0★) I’m reminded again how lawyers can twist your words so fast, it’s impressive. Surprisingly to me the court scenes felt faster than the first hour or so, Daniel … |
| 3 | +0.017 | 0.814 |  | (4.5★) Une claque pour tous ceux qui se reconnaissent dans l’over ambition mais la difficulté et la peur de les accomplir J’ai adoré le jeu de la dame qui défend la de… |
| 4 | +0.017 | 0.793 | ✓ | (3.5★) معرف هل هو النظام القضائي الفرنسي او ان المحامين اغبيا او المشكله بل كتابه يعني جتني لحظات اتكلم مع نفسي واقول يا حمار ايش ما تقول زي كذا ولا اشلون ذا المحامي ي… |
| 5 | +0.016 | 0.803 |  | (4.0★) Really well crafted take on the importance of nuances. Egregious vibes from the guy in the red robe compared to the amazing vibes from the handsome fella on Hül… |

**[positivas] realismo e autenticidade** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.818 |  | (4.5★) This was awesome. Might be a higher score on rewatch. I’m gonna sleep and give my full thoughts tomorrow. Best Criterion purchase I made since Memories of Murde… |
| 2 | +0.021 | 0.800 | ✓ | (4.0★) I really liked the character portrayals, those were certainly my favorite part! The characters felt so very real, and nuanced, and alive; I looked at Sandra Hül… |
| 3 | +0.020 | 0.810 | ✓ | (5.0★) From the stellar performances to the polaroids, dialogue and the kitchen, everything felt so authentic. It made the camera work feel so intrusive. But the ruthl… |
| 4 | +0.015 | 0.789 | ✓ | (5.0★) I love movies like this, especially the legal aspect. It’s even better when a film manages to make it feel tense and gripping. The various camera angles and sho… |
| 5 | +0.014 | 0.784 |  | (4.0★) Just finished the movie and at the end, it strikes me there seems to be some connections to the movie the Shining. The son’s red turtleneck and hair and look…. … |

**[positivas] interpretação do espectador** — eixo `impacto_emocional`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.820 |  | (4.0★) Ein spannendes Gerichtsdrama, das Fragen nach Wahrheit, Schuld und Wahrnehmung aufwirft. Die vielschichtigen Figuren und die dichte Atmosphäre regen zum Nachden… |
| 2 | +0.028 | 0.833 |  | (5.0★) gran película, gran juicio, una film que te retiene y te hace interpretar. Desde mi postura como estudiante , lo analicé basándome en mis habilidades de observa… |
| 3 | +0.019 | 0.795 | ✓ | (3.5★) معرف هل هو النظام القضائي الفرنسي او ان المحامين اغبيا او المشكله بل كتابه يعني جتني لحظات اتكلم مع نفسي واقول يا حمار ايش ما تقول زي كذا ولا اشلون ذا المحامي ي… |
| 4 | +0.018 | 0.809 |  | (4.0★) The movie asks an important question: can you feel the depth and the strain of learning to find yourself in the complicated context of a long-term relationship … |
| 5 | +0.017 | 0.788 | ✓ | (4.0★) I was expecting more of a follow through with the plot but it turned out to be so meaningful. I was rooting for her, not because I liked her but for her son’s s… |

**[positivas] comparação com outras obras** — eixo `comparacoes`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.063 | 0.834 | ✓ | (4.0★) Just finished the movie and at the end, it strikes me there seems to be some connections to the movie the Shining. The son’s red turtleneck and hair and look…. … |
| 2 | +0.036 | 0.818 |  | (4.5★) I had extensive thoughts about this movie, but i forgot them I think it'd be more impactful if i cared more for family dynamics Good movie very engaging |
| 3 | +0.036 | 0.805 | ✓ | (4.5★) Incredible performances from the mother and son. I got goosebumps during the couple’s argument presented during the trial and the final testimony from Daniel. I… |
| 4 | +0.030 | 0.801 |  | (3.5★) Just rewatched for the 2nd time without realized I already rated it and would’ve given the same rating. Features one of my favourite tracks (P.I.M.P by 50 Cent)… |
| 5 | +0.028 | 0.803 | ✓ | (5.0★) I love movies like this, especially the legal aspect. It’s even better when a film manages to make it feel tense and gripping. The various camera angles and sho… |

## Incêndios

### publicado — DeepSeek (síntese publicada)

**[negativas] Ritmo lento e tédio** — eixo `ritmo`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.034 | 0.856 | ✓ | (2.0★) muy lenta, el plot twist me ha molao, el cast me falla. Quizá no era para mí, he sentido que no pasaba nada durante toda la peli hasta el final, pero me ha dece… |
| 2 | +0.028 | 0.807 | ✓ | (1.0★) Could not finish. predicted the twist and found myself correct later. Skipped and tried to pace but still could not finish. I then realised its rated so high wh… |
| 3 | +0.023 | 0.807 | ✓ | (1.0★) one of my hb recommended me this and now i have to fucking kill him, this was the worst shit i’ve ever seen, can’t believe i wasted a saturday night watching th… |
| 4 | +0.021 | 0.780 |  | (1.0★) Really bad. I couldn’t even finish it. The story and characters just didn’t do anything for me, and I found it incredibly difficult to get through. Maybe I need… |
| 5 | +0.020 | 0.809 |  | (0.5★) Sterile, cynical, cowardly, 'apolitical' (racist), not just uninterested in, but brutal towards the real-world Lebanese history it uses as wanking material, Wes… |

**[negativas] Twist previsível e decepcionante** — eixo `roteiro_estrutura`, declarado 14/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.850 | ✓ | (2.0★) muy lenta, el plot twist me ha molao, el cast me falla. Quizá no era para mí, he sentido que no pasaba nada durante toda la peli hasta el final, pero me ha dece… |
| 2 | +0.027 | 0.829 | ✓ | (2.0★) overrated AS FUCK. No es NI DE CO-ÑA el mejor plot twist de la historia como te venden, de hecho Adriana se ha catao 5-10 minutos antes de que te lo presenten. … |
| 3 | +0.027 | 0.826 | ✓ | (1.0★) on te sort une révélation finale tellement grosse et statistiquement impossible que j’ai plus de chances de signer au Real Madrid que de voir cette fin se réali… |
| 4 | +0.025 | 0.804 | ✓ | (1.0★) Could not finish. predicted the twist and found myself correct later. Skipped and tried to pace but still could not finish. I then realised its rated so high wh… |
| 5 | +0.022 | 0.823 | ✓ | (0.5★) El final se veía venir desde menos de mitad de la película. Muy predecible, muy normalita y muy muy sobrevalorada, que pena que en el mundo el mundo del cine se… |

**[negativas] Falta de contexto político e covardia** — eixo `critica_social`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.818 | ✓ | (2.0★) I am so very split on this movie. On the one hand, it brought me to tears, it is empathetic, it is beautifully shot. On the other, it is exploitative, ignorant,… |
| 2 | +0.019 | 0.825 | ✓ | (2.0★) Jour 12 pour voir le top 100 Letterboxd Dans un pays imaginaire, après une guerre de religion, les enfant d'une mère ayant vécu ce fameux conflit tente de retro… |
| 3 | +0.017 | 0.820 | ✓ | (2.0★) Je me suis senti vraiment en empathie avec le peuple qui a subi cette guerre dans le pays du nom de …. Ah non ce serait chiant d’assumer un contexte politique d… |
| 4 | +0.017 | 0.822 | ✓ | (1.5★) Basé un film sur les conflits du moyen orient qui se passe dans un pays imaginaire sans expliquer les contextes sociaux sans parler un peu de politique, tout ça… |
| 5 | +0.013 | 0.800 | ✓ | (1.0★) Worse dialogs in cinema’s history. They try to be emotional and deep but it just ends up looking like a marvel movie. I challenge anyone to find more than 70 se… |

**[negativas] Atuações fracas e falta de credibilidade** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.020 | 0.779 |  | (1.0★) Really bad. I couldn’t even finish it. The story and characters just didn’t do anything for me, and I found it incredibly difficult to get through. Maybe I need… |
| 2 | +0.019 | 0.805 |  | (1.0★) Butchered arabic, dialects that have nothing to do with the region (the militia chief is Moroccan, they couldn’t go furthest than that). Plus it doesn’t make se… |
| 3 | +0.015 | 0.799 |  | (1.0★) one of my hb recommended me this and now i have to fucking kill him, this was the worst shit i’ve ever seen, can’t believe i wasted a saturday night watching th… |
| 4 | +0.014 | 0.803 | ✓ | (2.0★) ????????? The “gotchya” here being incestuous rape is so insane when the viewer would literally have NO WAY of putting it together because they used the same ac… |
| 5 | +0.013 | 0.812 |  | (1.0★) on te sort une révélation finale tellement grosse et statistiquement impossible que j’ai plus de chances de signer au Real Madrid que de voir cette fin se réali… |

**[negativas] Exploração de trauma e tabus** — eixo `tom_atmosfera`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.026 | 0.807 |  | (2.0★) I watched Prisoners and I liked it so much So I told my self let s see another Villeneuve movie I heard a lot about Incendies and to be honest I had an idea abo… |
| 2 | +0.026 | 0.818 |  | (1.0★) 1 star for radio head . This movie was nice but lokwey a bit spineless for not mentioning the acctual war that took place also it basically follows the old boys… |
| 3 | +0.020 | 0.814 |  | (2.0★) Yet another film that has mystified me with its high rating. Why do people like to just hand out 5 stars when there's rape in a movie?? Maybe instead of being b… |
| 4 | +0.017 | 0.822 |  | (2.0★) Jour 12 pour voir le top 100 Letterboxd Dans un pays imaginaire, après une guerre de religion, les enfant d'une mère ayant vécu ce fameux conflit tente de retro… |
| 5 | +0.015 | 0.802 |  | (2.0★) It's like Wild Bill from the Green Mile where you don't understand until you get the deus ex machina to tell you what the context is. For a movie about oedipal … |

**[negativas] Problemas de roteiro e lógica** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.808 | ✓ | (1.0★) Butchered arabic, dialects that have nothing to do with the region (the militia chief is Moroccan, they couldn’t go furthest than that). Plus it doesn’t make se… |
| 2 | +0.018 | 0.822 | ✓ | (1.5★) Basé un film sur les conflits du moyen orient qui se passe dans un pays imaginaire sans expliquer les contextes sociaux sans parler un peu de politique, tout ça… |
| 3 | +0.018 | 0.804 | ✓ | (1.0★) Worse dialogs in cinema’s history. They try to be emotional and deep but it just ends up looking like a marvel movie. I challenge anyone to find more than 70 se… |
| 4 | +0.014 | 0.808 | ✓ | (2.0★) + An opening scene, just F**ing brilliant! - Everything it’s just hard to swallow, even though the story is genial! Room for improvement: It’s just hard to watc… |
| 5 | +0.012 | 0.794 | ✓ | (2.0★) La chose intéressante avec les acteurs québécois est qu'ils ne sont pas des bons acteurs, pourquoi ils s'expriment comme la première lecture expressive d'une pi… |

**[medianas] Reviravolta previsível ou que não surpreendeu** — eixo `roteiro_estrutura`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.855 | ✓ | (3.0★) Fui assistir esse filme pq sempre aparecia pra mim em recomendações de filmes com os plot twists mais absurdos. So que eu mesmo estraguei a experiência desse fi… |
| 2 | +0.030 | 0.820 | ✓ | (3.0★) Villeneuve es un monstruo dirigiendo, sabe construir personajes complejos con un transfondo oscuro pero muy humanos. Técnicamente la película es impecable de pr… |
| 3 | +0.026 | 0.812 | ✓ | (2.5★) genel itibariyle yavaş akan ama bi o kadar da sonunda ne olacağını merak ettirten bi filmdi bence film ikiz kardeşlerin annelerinden vasiyet yoluyla kalan mektu… |
| 4 | +0.024 | 0.820 | ✓ | (2.5★) Donacak kan kalmadı, midem bulandı, elim ayağım titredi ben bu kadar ağır filmleri kaldıramıyorum bence. Gece 3 olmasa bir romcom izleyip yatardım ama uykum var… |
| 5 | +0.020 | 0.795 | ✓ | (3.0★) Finally got around to checking out Incendies and it was exactly what I thought it was going to be, a very brutal and horrifying look at how war can affect someo… |

**[medianas] Ritmo lento e momentos arrastados** — eixo `ritmo`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.832 | ✓ | (3.0★) Az once izledim son 20 dakikada herseyi anlatiyor ama oldboy gibi merak ettirip sarmak yerine cok bunaltti kaotikti sonunu iyi ve garip bagladilar ve eksik gibi… |
| 2 | +0.018 | 0.788 | ✓ | (2.5★) Ikke fan, meget god historie, godt plottwist og et gisp der fik mig til at tisse i bukserne. Men glædede mig til at den sluttede, virkelig kedelig. Måske jeg en… |
| 3 | +0.016 | 0.820 |  | (2.5★) For me, distasteful and rubbing your nose in it. The only savings graces were Villeneuve's camera casts its usual effectively cold gaze, and the humanistic clos… |
| 4 | +0.014 | 0.802 | ✓ | (3.0★) By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story. You will now… |
| 5 | +0.013 | 0.799 | ✓ | (2.5★) genel itibariyle yavaş akan ama bi o kadar da sonunda ne olacağını merak ettirten bi filmdi bence film ikiz kardeşlerin annelerinden vasiyet yoluyla kalan mektu… |

**[medianas] Direção e atuações elogiadas** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.011 | 0.789 | ✓ | (3.0★) GAG!!!!! Oh my God i know people have been talking about the twist and that pool scene but DAMN!!! Understanding it while watching it for the first time really … |
| 2 | +0.002 | 0.779 | ✓ | (3.0★) I wasn’t a huge fan of this one. There were too many plot points that just didn’t make sense to me, so I personally think it’s pretty overrated. That being said… |
| 3 | +0.001 | 0.773 |  | (3.0★) Can 1+1 = 1 The ending and twist were amazing and my favorite part of this movie but there was part of the first and second act I felt bored. I applaud Villeneu… |
| 4 | +0.001 | 0.774 |  | (3.0★) Found it such a cop out to set the war in a fictional Middle Eastern country instead of Lebanon. wah wah universality of the human condition wah wah Greek trage… |
| 5 | +0.001 | 0.785 | ✓ | (3.0★) Doesn’t help that I’ve heard of this twist a long time ago- so this review is biased But ultimately, this movie doesn’t work for me bc the faces/appearance of t… |

**[medianas] Roteiro excessivamente construído para o choque** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.023 | 0.804 | ✓ | (3.0★) This movie felt like a stage play. And, lo and behold, a quick Google search and Wiki skim revealed to me that it was indeed a stage play. All I was waiting for… |
| 2 | +0.020 | 0.793 | ✓ | (3.0★) Found it such a cop out to set the war in a fictional Middle Eastern country instead of Lebanon. wah wah universality of the human condition wah wah Greek trage… |
| 3 | +0.020 | 0.817 | ✓ | (3.0★) franchement sympathique, mais pas pour moi. Villeneuve est un très bon réalisateur donc il pond une histoire correct avec cette aspect contemplatif qui définie … |
| 4 | +0.019 | 0.798 | ✓ | (2.5★) Incredibly overrated, boring, don’t care about the characters, tries to be traumatic but I just don’t care, if it was in English it would be way lower later, fe… |
| 5 | +0.018 | 0.793 | ✓ | (3.0★) I obviously can’t help but compare this to Oldboy. But besides the end it was boring and sad and a devastating movie doesn’t mean it’s good. I get it was artist… |

**[medianas] Fotografia e aspectos técnicos bem avaliados** — eixo `direcao_imagem`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.002 | 0.807 | ✓ | (2.5★) For me, distasteful and rubbing your nose in it. The only savings graces were Villeneuve's camera casts its usual effectively cold gaze, and the humanistic clos… |
| 2 | +0.001 | 0.779 | ✓ | (3.0★) GAG!!!!! Oh my God i know people have been talking about the twist and that pool scene but DAMN!!! Understanding it while watching it for the first time really … |
| 3 | -0.001 | 0.779 |  | (3.0★) الفيلم كان ممل في اول ساعة بس بشكل بيخدم القصة عشان تيجي تاني ساعة ويبقي فيها بلوت تويست عظيم ممكن يكون predictable بس بردو Worth the wait and worth watching |
| 4 | -0.002 | 0.810 |  | (3.0★) una historia desgarradora y cruel con un enfoque especial en la guerra y la maternidad, una madre que cría con amor y perdona lo imperdonable. esperaba otro plo… |
| 5 | -0.003 | 0.819 |  | (3.0★) Se eu não tivesse tomado um spoiller, teria sido um filmaço. Porém, que ÓDIO desses irmãos que não tiveram UMA reação ao descobrir a verdade. É um sangue de bar… |

**[medianas] Dificuldade de conexão emocional com os personagens** — eixo `impacto_emocional`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.802 | ✓ | (3.0★) Doesn’t help that I’ve heard of this twist a long time ago- so this review is biased But ultimately, this movie doesn’t work for me bc the faces/appearance of t… |
| 2 | +0.014 | 0.798 |  | (3.0★) I rly like the idea of laying out a mystery in a will and then solving it throughout a movie, but the way it’s done here is pretty slow and could be done better… |
| 3 | +0.012 | 0.798 | ✓ | (3.0★) 該怎麼說呢，火燒車與結局確實震撼，但整體敘事卻感覺綁手綁腳，沒能更好地用鏡頭傳達，但也確實讓我很好奇原劇作的呈現，應該會比電影精彩很多吧？ 本片多次在觀眾試圖解讀影像之前率先透過某人講出媽媽發生什麼事，忽然失去探索影像的主導權，身為電影觀眾不免對此有些反感，且講完了還要再給你看事發當下的鏡頭，感到多餘的同時馬上瞭然不過… |
| 4 | +0.011 | 0.834 |  | (3.0★) Se eu não tivesse tomado um spoiller, teria sido um filmaço. Porém, que ÓDIO desses irmãos que não tiveram UMA reação ao descobrir a verdade. É um sangue de bar… |
| 5 | +0.011 | 0.796 | ✓ | (2.5★) Cuando te encierras en una burbuja y te detienes a ver el mundo real te caes de cara y te das cuenta de que hasta lo poquito que tienes es un privilegio. Eso me… |

**[positivas] Impacto emocional devastador** — eixo `impacto_emocional`, declarado 28/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.036 | 0.837 | ✓ | (5.0★) Es demoledor, increíble y bello que un simple suspiro sea más horroroso que cualquier crimen inimaginable. Amo esta película porque me afecta en las sensaciones… |
| 2 | +0.035 | 0.824 |  | (4.0★) Mientras veía la película, mi amigo se cuestionaba por qué la madre arriesgaría tanto y convertiría radicalmente su vida por un niño que nunca conoció realmente… |
| 3 | +0.032 | 0.809 | ✓ | (5.0★) this movie is really heavy and i was thinking about it for three days after watching, It’s one of those things you kind of like, but wouldn’t recommend to anyon… |
| 4 | +0.028 | 0.806 | ✓ | (4.0★) Un film d’une violence émotionnelle incroyable. Denis Villeneuve construit son histoire petit à petit avant de nous mettre une énorme claque avec ses révélation… |
| 5 | +0.027 | 0.858 | ✓ | (5.0★) eu terminei esse filme tentando entender como alguém conseguiu transformar uma história em uma experiência de sofrimento psicológico, n foi um filme, foi uma ag… |

**[positivas] Reviravolta e revelações** — eixo `roteiro_estrutura`, declarado 22/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.799 | ✓ | (4.0★) Un film d’une violence émotionnelle incroyable. Denis Villeneuve construit son histoire petit à petit avant de nous mettre une énorme claque avec ses révélation… |
| 2 | +0.015 | 0.810 | ✓ | (4.5★) i mean, devastating. unbelievable storytelling. denis villeneuve is an incredibly good director haunting, actually, maybe more just fucked. didn’t see a twist c… |
| 3 | +0.013 | 0.817 | ✓ | (4.5★) içeriği ve duygu yoğunluğu itibariyle birkaç yıldır ertelediğim bir filmdi, ve sonunda izledim denis villeneuve her zaman yaptığı gibi alternatif bir mekansal e… |
| 4 | +0.010 | 0.835 | ✓ | (4.0★) A guerra leva consigo tantas perdas, tantas memórias... E no final resta uma casca vazia, deixando-nos a opção de escolher entre se ferir com a verdade e preenc… |
| 5 | +0.009 | 0.812 | ✓ | (5.0★) beh, diciamo uno dei racconti più emozionanti, profondi e meglio riusciti di sempre? si potrebbe. questo film racconta semplicemente come da trama, la storia di… |

**[positivas] Direção de Denis Villeneuve** — eixo `direcao_imagem`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.066 | 0.828 |  | (4.0★) Really good and powerful movie with a very depressing twist. But definitely my least favourite of Denis filmography. Because I don’t really feel, that I get des… |
| 2 | +0.054 | 0.831 |  | (5.0★) Watching this feels like your heart has been torn and it's such a masterpiece. My heart breaks for every character, the love of a mother is insane. It'll take a… |
| 3 | +0.047 | 0.854 |  | (4.5★) Um dos dramas mais poderosos deste século, e com certeza, a obra-prima de Denis Villeneuve. Num mundo onde a identidade é negada a todo o momento, não existe es… |
| 4 | +0.044 | 0.822 | ✓ | (4.0★) Un film d’une violence émotionnelle incroyable. Denis Villeneuve construit son histoire petit à petit avant de nous mettre une énorme claque avec ses révélation… |
| 5 | +0.036 | 0.805 |  | (4.0★) This film was heavily pushed on me by two former colleagues of mine, whose recommendations usually need to be taken with a large grain of salt. Unsurprisingly (… |

**[positivas] Atuação de Lubna Azabal** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.048 | 0.855 | ✓ | (4.5★) Um dos dramas mais poderosos deste século, e com certeza, a obra-prima de Denis Villeneuve. Num mundo onde a identidade é negada a todo o momento, não existe es… |
| 2 | +0.047 | 0.842 | ✓ | (4.5★) i mean, devastating. unbelievable storytelling. denis villeneuve is an incredibly good director haunting, actually, maybe more just fucked. didn’t see a twist c… |
| 3 | +0.031 | 0.807 |  | (5.0★) FUCK. That gasp is probably one of the most terrifying scenes I've ever seen, which is insane because it is just 1 second of a character reacting. Best use of n… |
| 4 | +0.017 | 0.809 | ✓ | (4.5★) Stunning script in the way it coils and unravels with devastating force. Extraordinary lead performances. The mood is bleak and unrelenting, barely lets you bre… |
| 5 | +0.013 | 0.838 | ✓ | (5.0★) La hòstia, quina peli. Fotografia excel·lent. Guió increïble. Actuacions brutals. Direcció acollonant. Ambientació supèrflua. Conclusió asfixiant. 5 de 5 fàcil. |

**[positivas] Fotografia e paisagens** — eixo `direcao_imagem`, declarado 11/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.027 | 0.830 | ✓ | (5.0★) beh, diciamo uno dei racconti più emozionanti, profondi e meglio riusciti di sempre? si potrebbe. questo film racconta semplicemente come da trama, la storia di… |
| 2 | +0.014 | 0.840 | ✓ | (5.0★) La hòstia, quina peli. Fotografia excel·lent. Guió increïble. Actuacions brutals. Direcció acollonant. Ambientació supèrflua. Conclusió asfixiant. 5 de 5 fàcil. |
| 3 | +0.013 | 0.777 |  | (5.0★) Эмоционально безумно тяжелая работа. Прекрасная актерская игра. Абсолютный мастхэв для любителей фильмов связанных с Ближним Востоком. Хорошая сюжетная линия. |
| 4 | +0.009 | 0.838 |  | (4.0★) A cena da piscina é um choque absurdo. Esse filme é excessivamente melancólico, então tem que estar em um mood ótimo pra aguentar. A parte "documental" da polít… |
| 5 | +0.006 | 0.807 |  | (5.0★) Es demoledor, increíble y bello que un simple suspiro sea más horroroso que cualquier crimen inimaginable. Amo esta película porque me afecta en las sensaciones… |

**[positivas] Roteiro e narrativa não linear** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.801 | ✓ | (4.0★) Wow, I really don’t know what to say. Villeneuve is easily one of my favorite directors, and he creates such an expertly crafted story of family, war, and grief… |
| 2 | +0.008 | 0.786 | ✓ | (3.5★) Wish I didn’t know it how ended beforehand!! But still quite moving at times and also quite slow. Sheer chance and odds being a BIT too high on this one two tim… |
| 3 | +0.006 | 0.835 | ✓ | (4.0★) من قوه لبلوت تويست عضيت ريام ونكتلت هههههههههههههههه هو واولد بوي نفس الخرا يعني صارلي سنتين ثلاث من شفت اولد بوي ولليوم هذا ما تخطيته وجاء الازرب منه دمرلي نفس… |
| 4 | +0.006 | 0.808 | ✓ | (5.0★) beh, diciamo uno dei racconti più emozionanti, profondi e meglio riusciti di sempre? si potrebbe. questo film racconta semplicemente come da trama, la storia di… |
| 5 | +0.006 | 0.810 | ✓ | (4.5★) içeriği ve duygu yoğunluğu itibariyle birkaç yıldır ertelediğim bir filmdi, ve sonunda izledim denis villeneuve her zaman yaptığı gibi alternatif bir mekansal e… |

### local — qwen3:14b (Ollama)

**[negativas] previsibilidade do enredo** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.026 | 0.806 | ✓ | (1.0★) Could not finish. predicted the twist and found myself correct later. Skipped and tried to pace but still could not finish. I then realised its rated so high wh… |
| 2 | +0.026 | 0.806 | ✓ | (2.0★) I watched Prisoners and I liked it so much So I told my self let s see another Villeneuve movie I heard a lot about Incendies and to be honest I had an idea abo… |
| 3 | +0.025 | 0.826 | ✓ | (0.5★) El final se veía venir desde menos de mitad de la película. Muy predecible, muy normalita y muy muy sobrevalorada, que pena que en el mundo el mundo del cine se… |
| 4 | +0.019 | 0.841 | ✓ | (2.0★) muy lenta, el plot twist me ha molao, el cast me falla. Quizá no era para mí, he sentido que no pasaba nada durante toda la peli hasta el final, pero me ha dece… |
| 5 | +0.018 | 0.820 | ✓ | (2.0★) overrated AS FUCK. No es NI DE CO-ÑA el mejor plot twist de la historia como te venden, de hecho Adriana se ha catao 5-10 minutos antes de que te lo presenten. … |

**[negativas] trabalho de atuação insatisfatório** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.017 | 0.798 | ✓ | (2.0★) La chose intéressante avec les acteurs québécois est qu'ils ne sont pas des bons acteurs, pourquoi ils s'expriment comme la première lecture expressive d'une pi… |
| 2 | +0.011 | 0.810 |  | (1.0★) on te sort une révélation finale tellement grosse et statistiquement impossible que j’ai plus de chances de signer au Real Madrid que de voir cette fin se réali… |
| 3 | +0.010 | 0.770 |  | (1.0★) Really bad. I couldn’t even finish it. The story and characters just didn’t do anything for me, and I found it incredibly difficult to get through. Maybe I need… |
| 4 | +0.009 | 0.793 |  | (1.0★) one of my hb recommended me this and now i have to fucking kill him, this was the worst shit i’ve ever seen, can’t believe i wasted a saturday night watching th… |
| 5 | +0.006 | 0.794 |  | (0.5★) Sterile, cynical, cowardly, 'apolitical' (racist), not just uninterested in, but brutal towards the real-world Lebanese history it uses as wanking material, Wes… |

**[negativas] falta de aprofundamento no contexto político e histórico** — eixo `critica_social`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.823 | ✓ | (2.0★) I am so very split on this movie. On the one hand, it brought me to tears, it is empathetic, it is beautifully shot. On the other, it is exploitative, ignorant,… |
| 2 | +0.023 | 0.826 | ✓ | (2.0★) Je me suis senti vraiment en empathie avec le peuple qui a subi cette guerre dans le pays du nom de …. Ah non ce serait chiant d’assumer un contexte politique d… |
| 3 | +0.020 | 0.825 | ✓ | (2.0★) Jour 12 pour voir le top 100 Letterboxd Dans un pays imaginaire, après une guerre de religion, les enfant d'une mère ayant vécu ce fameux conflit tente de retro… |
| 4 | +0.018 | 0.823 | ✓ | (1.5★) Basé un film sur les conflits du moyen orient qui se passe dans un pays imaginaire sans expliquer les contextes sociaux sans parler un peu de politique, tout ça… |
| 5 | +0.017 | 0.803 | ✓ | (1.0★) Butchered arabic, dialects that have nothing to do with the region (the militia chief is Moroccan, they couldn’t go furthest than that). Plus it doesn’t make se… |

**[negativas] apresentação de temas sensíveis de forma inadequada** — eixo `critica_social`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.015 | 0.803 | ✓ | (0.5★) Sterile, cynical, cowardly, 'apolitical' (racist), not just uninterested in, but brutal towards the real-world Lebanese history it uses as wanking material, Wes… |
| 2 | +0.014 | 0.816 | ✓ | (2.0★) Je me suis senti vraiment en empathie avec le peuple qui a subi cette guerre dans le pays du nom de …. Ah non ce serait chiant d’assumer un contexte politique d… |
| 3 | +0.013 | 0.801 |  | (2.0★) It's like Wild Bill from the Green Mile where you don't understand until you get the deus ex machina to tell you what the context is. For a movie about oedipal … |
| 4 | +0.011 | 0.803 | ✓ | (1.0★) 1 star for radio head . This movie was nice but lokwey a bit spineless for not mentioning the acctual war that took place also it basically follows the old boys… |
| 5 | +0.011 | 0.795 |  | (1.0★) one of my hb recommended me this and now i have to fucking kill him, this was the worst shit i’ve ever seen, can’t believe i wasted a saturday night watching th… |

**[negativas] ritmo lento e falta de engajamento** — eixo `ritmo`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.851 | ✓ | (2.0★) muy lenta, el plot twist me ha molao, el cast me falla. Quizá no era para mí, he sentido que no pasaba nada durante toda la peli hasta el final, pero me ha dece… |
| 2 | +0.023 | 0.807 | ✓ | (1.0★) one of my hb recommended me this and now i have to fucking kill him, this was the worst shit i’ve ever seen, can’t believe i wasted a saturday night watching th… |
| 3 | +0.022 | 0.802 | ✓ | (2.0★) اقل من المتوقع رغم أني ماشعرت ابداّ بالمل وكنت منسجم مع الفيلم ولكن العمل بارد وسطحي بشكل غير طبيعي ، السرد ثقيل جداّ والأحداث بطيئه بدون أي تعقيد أو غموض نهاية… |
| 4 | +0.022 | 0.782 |  | (1.0★) Really bad. I couldn’t even finish it. The story and characters just didn’t do anything for me, and I found it incredibly difficult to get through. Maybe I need… |
| 5 | +0.022 | 0.803 |  | (2.0★) Just didn't hit for me. So much in fact I forgot to long it and the next 2 movies I watched on different days. I'm pretty sure thats connected with this movie |

**[negativas] falta de originalidade e genericalidade** — eixo `roteiro_estrutura`, declarado 4/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.803 | ✓ | (1.0★) Worse dialogs in cinema’s history. They try to be emotional and deep but it just ends up looking like a marvel movie. I challenge anyone to find more than 70 se… |
| 2 | +0.015 | 0.854 | ✓ | (1.5★) Um filme COVARDE Na sua busca do choque pelo choque, é o que Villeneuve se propôs aqui. Sua visão estéril sobre um filme, que por escolha própria, quis se ambie… |
| 3 | +0.014 | 0.807 | ✓ | (2.0★) I am so very split on this movie. On the one hand, it brought me to tears, it is empathetic, it is beautifully shot. On the other, it is exploitative, ignorant,… |
| 4 | +0.014 | 0.774 | ✓ | (1.0★) Really bad. I couldn’t even finish it. The story and characters just didn’t do anything for me, and I found it incredibly difficult to get through. Maybe I need… |
| 5 | +0.013 | 0.814 | ✓ | (0.5★) El final se veía venir desde menos de mitad de la película. Muy predecible, muy normalita y muy muy sobrevalorada, que pena que en el mundo el mundo del cine se… |

**[medianas] Revelação surpreendente no final** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.793 | ✓ | (3.0★) Finally got around to checking out Incendies and it was exactly what I thought it was going to be, a very brutal and horrifying look at how war can affect someo… |
| 2 | +0.012 | 0.835 | ✓ | (3.0★) Se eu não tivesse tomado um spoiller, teria sido um filmaço. Porém, que ÓDIO desses irmãos que não tiveram UMA reação ao descobrir a verdade. É um sangue de bar… |
| 3 | +0.008 | 0.820 | ✓ | (3.0★) una historia desgarradora y cruel con un enfoque especial en la guerra y la maternidad, una madre que cría con amor y perdona lo imperdonable. esperaba otro plo… |
| 4 | +0.008 | 0.798 | ✓ | (3.0★) Korkunc Saat 05.19 yatakta dogruldum dusunuyorum cok uzucu cidden etik olmayışı ve bir filmde bunun gözler önüne serilmesi hos degil. açıkçası beklemiyodum bu k… |
| 5 | +0.008 | 0.794 | ✓ | (2.5★) genel itibariyle yavaş akan ama bi o kadar da sonunda ne olacağını merak ettirten bi filmdi bence film ikiz kardeşlerin annelerinden vasiyet yoluyla kalan mektu… |

**[medianas] Trabalho de direção e fotografia** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.011 | 0.789 | ✓ | (3.0★) GAG!!!!! Oh my God i know people have been talking about the twist and that pool scene but DAMN!!! Understanding it while watching it for the first time really … |
| 2 | +0.005 | 0.790 |  | (2.5★) Cuando te encierras en una burbuja y te detienes a ver el mundo real te caes de cara y te das cuenta de que hasta lo poquito que tienes es un privilegio. Eso me… |
| 3 | +0.003 | 0.807 | ✓ | (2.5★) For me, distasteful and rubbing your nose in it. The only savings graces were Villeneuve's camera casts its usual effectively cold gaze, and the humanistic clos… |
| 4 | +0.001 | 0.776 |  | (3.0★) Finally got around to checking out Incendies and it was exactly what I thought it was going to be, a very brutal and horrifying look at how war can affect someo… |
| 5 | +0.001 | 0.787 | ✓ | (3.0★) 該怎麼說呢，火燒車與結局確實震撼，但整體敘事卻感覺綁手綁腳，沒能更好地用鏡頭傳達，但也確實讓我很好奇原劇作的呈現，應該會比電影精彩很多吧？ 本片多次在觀眾試圖解讀影像之前率先透過某人講出媽媽發生什麼事，忽然失去探索影像的主導權，身為電影觀眾不免對此有些反感，且講完了還要再給你看事發當下的鏡頭，感到多餘的同時馬上瞭然不過… |

**[medianas] Narrativa lenta e densa** — eixo `ritmo`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.805 | ✓ | (3.0★) By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story. You will now… |
| 2 | +0.015 | 0.794 | ✓ | (2.5★) Incredibly overrated, boring, don’t care about the characters, tries to be traumatic but I just don’t care, if it was in English it would be way lower later, fe… |
| 3 | +0.014 | 0.785 | ✓ | (2.5★) Ikke fan, meget god historie, godt plottwist og et gisp der fik mig til at tisse i bukserne. Men glædede mig til at den sluttede, virkelig kedelig. Måske jeg en… |
| 4 | +0.014 | 0.818 |  | (2.5★) For me, distasteful and rubbing your nose in it. The only savings graces were Villeneuve's camera casts its usual effectively cold gaze, and the humanistic clos… |
| 5 | +0.013 | 0.794 |  | (3.0★) This movie felt like a stage play. And, lo and behold, a quick Google search and Wiki skim revealed to me that it was indeed a stage play. All I was waiting for… |

**[medianas] Foco excessivo no plot twist** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.024 | 0.814 | ✓ | (3.0★) Villeneuve es un monstruo dirigiendo, sabe construir personajes complejos con un transfondo oscuro pero muy humanos. Técnicamente la película es impecable de pr… |
| 2 | +0.022 | 0.846 | ✓ | (3.0★) Fui assistir esse filme pq sempre aparecia pra mim em recomendações de filmes com os plot twists mais absurdos. So que eu mesmo estraguei a experiência desse fi… |
| 3 | +0.019 | 0.803 | ✓ | (3.0★) Doesn’t help that I’ve heard of this twist a long time ago- so this review is biased But ultimately, this movie doesn’t work for me bc the faces/appearance of t… |
| 4 | +0.017 | 0.789 | ✓ | (3.0★) Can 1+1 = 1 The ending and twist were amazing and my favorite part of this movie but there was part of the first and second act I felt bored. I applaud Villeneu… |
| 5 | +0.016 | 0.787 | ✓ | (3.0★) ياشبية سيتي اوف قاد فالاجواء يعيال الفلم عادي ولا انا مهبول ولا هو غبي بالحيل ولا انا اللي فيني بلاء قسم بالله مايستاهل تقييمه ياهوه وش اللي 4,5 ؟!؟!😳يعني طول ا… |

**[medianas] Temas de guerra e conflito** — eixo `critica_social`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.790 |  | (3.0★) Finally got around to checking out Incendies and it was exactly what I thought it was going to be, a very brutal and horrifying look at how war can affect someo… |
| 2 | +0.014 | 0.802 |  | (3.0★) By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story. You will now… |
| 3 | +0.011 | 0.824 |  | (3.0★) una historia desgarradora y cruel con un enfoque especial en la guerra y la maternidad, una madre que cría con amor y perdona lo imperdonable. esperaba otro plo… |
| 4 | +0.006 | 0.830 | ✓ | (3.0★) 1+1 pode ser um? sei nem como expressar o que eu senti com essa película, ao mesmo tempo que gostei muito também não gostei. até então, temos um oriente médio q… |
| 5 | +0.004 | 0.778 | ✓ | (3.0★) Found it such a cop out to set the war in a fictional Middle Eastern country instead of Lebanon. wah wah universality of the human condition wah wah Greek trage… |

**[medianas] Ausência de conexão emocional com os personagens** — eixo `impacto_emocional`, declarado 4/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.014 | 0.793 | ✓ | (2.5★) Incredibly overrated, boring, don’t care about the characters, tries to be traumatic but I just don’t care, if it was in English it would be way lower later, fe… |
| 2 | +0.010 | 0.786 |  | (3.0★) I obviously can’t help but compare this to Oldboy. But besides the end it was boring and sad and a devastating movie doesn’t mean it’s good. I get it was artist… |
| 3 | +0.009 | 0.792 | ✓ | (3.0★) كنت مستني من الفلم انه يغير شي فيا ، يغير نظرتي للحياه ، يخلني اراجع نفسي بس ما صار ولا شي. اللي شفته فعلا صادم وبس ، لا اكثر ولا اقل. ممكن انا حطيت توقعات عالي… |
| 4 | +0.009 | 0.816 |  | (3.0★) Esthétisation permanente des scènes de violence qui désamorce leur portée dramatique ; dépolitisation complète de la situation à tel point qu'on galère à savoir… |
| 5 | +0.009 | 0.796 | ✓ | (3.0★) By the time this slow sad family and war drama becomes disturbingly devastating, it’s become too late to back out and you’re invested in the story. You will now… |

**[positivas] impacto emocional intenso** — eixo `impacto_emocional`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.831 | ✓ | (5.0★) Es demoledor, increíble y bello que un simple suspiro sea más horroroso que cualquier crimen inimaginable. Amo esta película porque me afecta en las sensaciones… |
| 2 | +0.029 | 0.808 | ✓ | (5.0★) An ending that left me completely speechless A story that left me deeply stunned and sad One of the toughest films I have seen in my life I knew before I watche… |
| 3 | +0.028 | 0.805 | ✓ | (5.0★) Watching this feels like your heart has been torn and it's such a masterpiece. My heart breaks for every character, the love of a mother is insane. It'll take a… |
| 4 | +0.028 | 0.806 | ✓ | (4.0★) Un film d’une violence émotionnelle incroyable. Denis Villeneuve construit son histoire petit à petit avant de nous mettre une énorme claque avec ses révélation… |
| 5 | +0.027 | 0.819 |  | (4.5★) Stunning script in the way it coils and unravels with devastating force. Extraordinary lead performances. The mood is bleak and unrelenting, barely lets you bre… |

**[positivas] revelação surpreendente e impactante** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.027 | 0.796 | ✓ | (3.5★) i figured out the plot twist within the first hour, but i neither expect nor was prepared for how horrifying the truth would be. i kept telling myself it couldn… |
| 2 | +0.024 | 0.802 | ✓ | (4.5★) peak soundtrack, acting, plot. saw the twist coming but it still hit. liked that i didn’t recognize any of the actors but they were still great. denis really do… |
| 3 | +0.024 | 0.801 | ✓ | (5.0★) Watching this feels like your heart has been torn and it's such a masterpiece. My heart breaks for every character, the love of a mother is insane. It'll take a… |
| 4 | +0.024 | 0.799 | ✓ | (5.0★) FUCK. That gasp is probably one of the most terrifying scenes I've ever seen, which is insane because it is just 1 second of a character reacting. Best use of n… |
| 5 | +0.022 | 0.800 | ✓ | (4.0★) Un film d’une violence émotionnelle incroyable. Denis Villeneuve construit son histoire petit à petit avant de nous mettre une énorme claque avec ses révélation… |

**[positivas] exploração da guerra e seus efeitos** — eixo `critica_social`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.828 | ✓ | (4.0★) Esta película muestra la perspectiva de una víctima que se ve afectada simplemente por ser ella misma, por buscar la verdad y no dejarse llevar por el odio aunq… |
| 2 | +0.026 | 0.816 | ✓ | (4.5★) ~IS THIS WHAT WE LIVE TO EXPERIENCE~ War has always given us stories where we forget to draw a line between being human and being an inhumane body who doesn't d… |
| 3 | +0.022 | 0.847 |  | (4.0★) A guerra leva consigo tantas perdas, tantas memórias... E no final resta uma casca vazia, deixando-nos a opção de escolher entre se ferir com a verdade e preenc… |
| 4 | +0.020 | 0.800 |  | (5.0★) An ending that left me completely speechless A story that left me deeply stunned and sad One of the toughest films I have seen in my life I knew before I watche… |
| 5 | +0.018 | 0.821 | ✓ | (3.5★) C'est un beau film dans un contexte de guerre qui fait prendre conscience de certaines choses comme les contexte politique, les religions et conflit à cette épo… |

**[positivas] exploração da maternidade e dos laços familiares** — eixo `roteiro_estrutura`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.794 | ✓ | (4.5★) على رأي يوسف وهبي يا للهول مظنش اني شفت في حياتي معلومة ممكن تكون بهذه الصعوبة وهذه الفاجعه، تأكدت إن الفيلم Not based on true story عشان لو كان قصة حقيقية مكنت… |
| 2 | +0.019 | 0.808 | ✓ | (4.0★) Mientras veía la película, mi amigo se cuestionaba por qué la madre arriesgaría tanto y convertiría radicalmente su vida por un niño que nunca conoció realmente… |
| 3 | +0.016 | 0.848 | ✓ | (4.0★) Que final brutal, esse filme é um quebra cabeça insano, começa com uma investigação dos irmãos tentando descobrir o passado da mãe e localizar o pai e o irmão q… |
| 4 | +0.016 | 0.819 | ✓ | (5.0★) beh, diciamo uno dei racconti più emozionanti, profondi e meglio riusciti di sempre? si potrebbe. questo film racconta semplicemente come da trama, la storia di… |
| 5 | +0.016 | 0.784 | ✓ | (3.5★) i figured out the plot twist within the first hour, but i neither expect nor was prepared for how horrifying the truth would be. i kept telling myself it couldn… |

**[positivas] realismo e representação da vida real** — eixo `direcao_imagem`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.792 |  | (4.5★) على رأي يوسف وهبي يا للهول مظنش اني شفت في حياتي معلومة ممكن تكون بهذه الصعوبة وهذه الفاجعه، تأكدت إن الفيلم Not based on true story عشان لو كان قصة حقيقية مكنت… |
| 2 | +0.017 | 0.795 |  | (5.0★) كنت مأجل اني اتفرج علي الفيلم دا من زمان لان اتحرقتلي التويست بتاعته قولت اجرب اشوفه حقيقي مفيش كلام يقال هنا فيلم رائع بكل المقاييس بس في نفس الوقت صعب جدا انك… |
| 3 | +0.014 | 0.792 |  | (4.5★) peak soundtrack, acting, plot. saw the twist coming but it still hit. liked that i didn’t recognize any of the actors but they were still great. denis really do… |
| 4 | +0.013 | 0.799 |  | (4.5★) ينهار أبيض بجد 1+1=1 أنا جالي ضيق تنفس وقت المشاهده من أقسى الافلام اللي شوفتها بجد متكامل ، لكنه صعب أوي ، كنت بفكر مكملهوش بس تحس بحاجه بتشدك انك تكملة للنهاي… |
| 5 | +0.011 | 0.814 |  | (3.5★) C'est un beau film dans un contexte de guerre qui fait prendre conscience de certaines choses comme les contexte politique, les religions et conflit à cette épo… |

**[positivas] direção e cinematografia impecáveis** — eixo `direcao_imagem`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.799 |  | (5.0★) Watching this feels like your heart has been torn and it's such a masterpiece. My heart breaks for every character, the love of a mother is insane. It'll take a… |
| 2 | +0.019 | 0.781 |  | (4.0★) Really good and powerful movie with a very depressing twist. But definitely my least favourite of Denis filmography. Because I don’t really feel, that I get des… |
| 3 | +0.019 | 0.845 | ✓ | (5.0★) La hòstia, quina peli. Fotografia excel·lent. Guió increïble. Actuacions brutals. Direcció acollonant. Ambientació supèrflua. Conclusió asfixiant. 5 de 5 fàcil. |
| 4 | +0.015 | 0.810 |  | (5.0★) Tout simplement merci à Denis Villeneuve pour ce chef d’œuvre. J’avais plus été aussi marqué par un film depuis requiem for a dream et quel « bonheur » de retro… |
| 5 | +0.014 | 0.793 |  | (4.5★) peak soundtrack, acting, plot. saw the twist coming but it still hit. liked that i didn’t recognize any of the actors but they were still great. denis really do… |

## mãe!

### publicado — DeepSeek (síntese publicada)

**[negativas] Alta carga alegórica e excesso de simbolismo** — eixo `tom_atmosfera`, declarado 13/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.044 | 0.828 |  | (2.0★) went in blind, and maybe it’s because I’m deeply unreligious, but a lot of the symbolism went over my head. Even the parts I did get, I was just like, “Ok…” I c… |
| 2 | +0.036 | 0.859 | ✓ | (1.0★) Uma experiência, definitivamente. Uma experiência ruim, mas mesmo assim… uma experiência. Simplesmente horrível e agoniante assistir. Entendo a alegoria, os sím… |
| 3 | +0.036 | 0.815 |  | (2.0★) i have never been so bewildered and gagged at once. it was supposed to be a metaphor for nature but maybe the literacy crisis is real bc i didn’t catch that. if… |
| 4 | +0.031 | 0.850 |  | (2.0★) Acho que os filmes perfeitos são 50/50. 50% do filme é oque você vê e 50% do filme é oque você entende, as metáforas e os significados. Odeio filmes como "Mãe!"… |
| 5 | +0.029 | 0.813 |  | (2.0★) This entire film is metaphor after metaphor after metaphor. And most of the time it's the exact. same. metaphor. I understand that is the point but just because… |

**[negativas] Experiência insuportável e desconfortável** — eixo `impacto_emocional`, declarado 11/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.049 | 0.872 | ✓ | (1.0★) Uma experiência, definitivamente. Uma experiência ruim, mas mesmo assim… uma experiência. Simplesmente horrível e agoniante assistir. Entendo a alegoria, os sím… |
| 2 | +0.029 | 0.821 | ✓ | (0.5★) Day 1 of surviving my bsf favorite movies @ruyaarchive… I understand what this movie is trying to say. I understand the biblical allegory, the symbolism of Moth… |
| 3 | +0.024 | 0.808 | ✓ | (2.0★) went in blind, and maybe it’s because I’m deeply unreligious, but a lot of the symbolism went over my head. Even the parts I did get, I was just like, “Ok…” I c… |
| 4 | +0.023 | 0.795 |  | (1.0★) Most infuriating shit ever Would’ve been 3 stars but it’s a stupid fucking time loop movie This was fucking nonsense. I guess that’s the point but why. What the… |
| 5 | +0.023 | 0.793 | ✓ | (1.0★) The last 40mins are so gruesome. This is how a selfish man with no moral compass ruins your life. J law's acting was terrific tho. I'm never watching this again… |

**[negativas] Ritmo problemático e sensação de longa duração** — eixo `ritmo`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.783 |  | (1.5★) Took me way too long to realize my tv glitched and started playing the Albert Brooks film, Mother . Not sure how or why, but I thought Jennifer Lawrence was jus… |
| 2 | +0.016 | 0.842 | ✓ | (1.0★) 2 horas e caceta de filme que parecem ser 6 horas. Esse diretor nao sabe oq eh bom senso nao? Eu em. As únicas coisas que salvam nesse filme são a ambientação e… |
| 3 | +0.014 | 0.792 |  | (2.0★) Annoying. If this movie had just been Domhnall Gleeson murdering everybody I would have been happy. But you can't always get what you want. Menacing chair movem… |
| 4 | +0.014 | 0.791 | ✓ | (2.0★) Overlooking the egregious religious themes, this film felt very mean-spirited. “What’s mine is yours” taken to cult-level of extremes by NPCs who act so bizarre… |
| 5 | +0.013 | 0.830 |  | (1.0★) ver esta peli es mas estresante que cortar el cable rojo verde o azul de una bomba a contratiempo y con tu suegra llamándote porque le debés plata y su hija se … |

**[negativas] Crítica ao personagem feminino e à dinâmica do casal** — eixo `critica_social`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.810 | ✓ | (2.0★) ERKEK GOTU GORMEK ISTEMIYORUM ARTIK IMDAT basrol adam o kadar mal ki erkeklere olan nefrerim katlanarak artti yemin ederim cok sinirim bozuldu nys kadinin yerin… |
| 2 | +0.024 | 0.816 | ✓ | (0.5★) Day 1 of surviving my bsf favorite movies @ruyaarchive… I understand what this movie is trying to say. I understand the biblical allegory, the symbolism of Moth… |
| 3 | +0.018 | 0.854 |  | (0.5★) so me fez passar raiva essa bosta, nunca senti tanto odio de visitas indesejadas, esse marido dela é um bundão, tudo nesse filme me irritou do começo ao fim, e … |
| 4 | +0.015 | 0.787 |  | (1.5★) What the actual fuck was the point of this movie “What hurts the most is that I’m not enough” Get the fuck out of my house, why do you think you can come into M… |
| 5 | +0.009 | 0.791 |  | (2.0★) Hey, so, what the fuck was that? Forreal tho, my beef with this one is that it’s way too shocking for what feels like absolutely no reason. I can understand how… |

**[negativas] Atuação de Jennifer Lawrence como ponto positivo** — eixo `atuacao`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.797 |  | (1.5★) Took me way too long to realize my tv glitched and started playing the Albert Brooks film, Mother . Not sure how or why, but I thought Jennifer Lawrence was jus… |
| 2 | +0.021 | 0.848 | ✓ | (1.0★) 2 horas e caceta de filme que parecem ser 6 horas. Esse diretor nao sabe oq eh bom senso nao? Eu em. As únicas coisas que salvam nesse filme são a ambientação e… |
| 3 | +0.021 | 0.798 |  | (2.0★) First hour engaging, but then its just jennifer lawrence torture without anything redeeming Feels like he had one idea and decided to make a whole film of it no… |
| 4 | +0.019 | 0.811 | ✓ | (1.5★) nie znam dobrze biblii wiec niestety nie zrozumiałam metafory dopóki nie przeczytałam interpretacji… overall bardzo nieprzyjemny film do oglądania, jennifer law… |
| 5 | +0.019 | 0.829 |  | (1.5★) MEU DEUS QUE AGONIA ELES QUEBRANDO A CASA DA JENNIFER LAWRENCE PQP. A pessoa que pensou nessa coisa que chamamos de filme é a mesma que crucificou Jesus. |

**[negativas] Sensacionalismo gratuito e cenas chocantes** — eixo `critica_social`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.802 |  | (2.0★) Hey, so, what the fuck was that? Forreal tho, my beef with this one is that it’s way too shocking for what feels like absolutely no reason. I can understand how… |
| 2 | +0.021 | 0.805 |  | (2.0★) went in blind, and maybe it’s because I’m deeply unreligious, but a lot of the symbolism went over my head. Even the parts I did get, I was just like, “Ok…” I c… |
| 3 | +0.019 | 0.802 |  | (2.0★) This entire film is metaphor after metaphor after metaphor. And most of the time it's the exact. same. metaphor. I understand that is the point but just because… |
| 4 | +0.016 | 0.793 | ✓ | (2.0★) Overlooking the egregious religious themes, this film felt very mean-spirited. “What’s mine is yours” taken to cult-level of extremes by NPCs who act so bizarre… |
| 5 | +0.016 | 0.787 |  | (1.5★) i didn’t even want to finish watching this movie and i thoroughly regret having done so. what a bland, banal, stupid thing omg. the only redeeming quality of th… |

**[medianas] Simbologia e alegoria** — eixo `livre`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.034 | 0.809 |  | (3.0★) A film I respect intellectually but no fucking clue if I like this or not. All I’ll say is that believing in a higher power doesn’t automatically make you a goo… |
| 2 | +0.032 | 0.812 |  | (3.0★) Was annoyed the whole time like girl ur too pretty for that, but then i found out abt its symbolism like OH! As a spiritual girly and also a catholic … well uh |
| 3 | +0.027 | 0.797 |  | (3.0★) An interesting allegorical metaphor, but the deliberate sensory assault made it one of the most uncomfortable and anxiety enducing films i've watched. |
| 4 | +0.025 | 0.792 |  | (3.0★) this movie was so crazy highly fucked up but the symbolism was cool ig and it was a very unique movie that frustrated me SO FUCKING BAD . Watched it with my par… |
| 5 | +0.025 | 0.811 |  | (3.0★) glaringly obvious metaphor for religion and mother nature from the start. very unsettling visuals with talented acting. it was good, but not enjoyable. more uns… |

**[medianas] Atuação de Jennifer Lawrence** — eixo `atuacao`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.060 | 0.823 | ✓ | (3.0★) There’s a lot going on in the movie. I understand that the story is allegorical but at times I felt like it was getting a little lost in the sauce. I liked it b… |
| 2 | +0.049 | 0.817 | ✓ | (3.0★) Abit of a difficult movie to review because half the time i didn't know what the fuck was going on 😂 but overall great performances from Jennifer Lawrence and J… |
| 3 | +0.048 | 0.813 | ✓ | (3.0★) Great family film. The script demands a lot from Jennifer Lawrence and whilst she’s not perfect she manages to do a great job at being the central performance i… |
| 4 | +0.035 | 0.812 | ✓ | (2.5★) Two stars for Jennifer’s acting and overall spooky vibe. It did the psychological thriller genre justice in the first two acts. The third act however completely… |
| 5 | +0.033 | 0.794 | ✓ | (3.0★) Rewatched this one today. First time watching it I turned it off because it was not something I wanted to watch at that time but I made sure that I will watch i… |

**[medianas] Experiência estressante e desconfortável** — eixo `impacto_emocional`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.049 | 0.815 | ✓ | (2.5★) This film is so stressful and anxiety-inducing that I will never willingly watch it again. The singular viewing I had of this film has stuck with me all of thes… |
| 2 | +0.037 | 0.814 | ✓ | (3.0★) what the fuck! i had to pause it and leave it a day cus it stressed me out so much i have never been so stressed by a film before. i now want to live on my own … |
| 3 | +0.032 | 0.833 | ✓ | (3.0★) je crois que ce film m’a donnée une crise de panique j’ai envie de brûler ma maison maintenant à la place de jennifer lawrence j’aurai crié SORTEZ SORTEZ DE MA … |
| 4 | +0.028 | 0.799 | ✓ | (3.0★) An interesting allegorical metaphor, but the deliberate sensory assault made it one of the most uncomfortable and anxiety enducing films i've watched. |
| 5 | +0.028 | 0.797 | ✓ | (3.0★) Honestly, had to look up what this movie meant and was surprised to find it has heavily biblical subtext, would never guess… it sure was an experience and made … |

**[medianas] Ritmo e excessos no ato final** — eixo `ritmo`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.834 | ✓ | (3.0★) okey no tengo mucho que decir.. me pareció un poco lenta, pero se ve que me estaba guardando para los ultimos 30 minutos que fueron desesperantes. la ira de una… |
| 2 | +0.027 | 0.801 |  | (3.0★) Watched by someone who didn’t get a lick of the bible stuff. I thought this was the Giving Tree! The first half I was intrigued and loving it. Weird happenings,… |
| 3 | +0.025 | 0.812 | ✓ | (3.0★) What? The tension building was great but what the hell does this even mean? It's entertaining but completely crazy and I think it lost its head in the second ho… |
| 4 | +0.023 | 0.805 | ✓ | (3.0★) This is genuinely what it feels like when ur roommate is hosting a pregame. Holy shit this escalated so fast and I got left in the fucking dust. Act 3 is probab… |
| 5 | +0.023 | 0.808 | ✓ | (2.5★) Aronofsky’s signature blend of terrifying, pretentious, and heavy symbolism gets me every time but this.... To give credit where it’s due, the allegories are so… |

**[medianas] Premissa interessante, execução confusa** — eixo `roteiro_estrutura`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.024 | 0.800 | ✓ | (3.0★) Like some other Aronofsky films it may take an viewing to understand it better, though I will not do a second viewing, will read up on that ending especially, i… |
| 2 | +0.024 | 0.846 | ✓ | (2.5★) O filme tem uma premissa muito interessante, porém o diretor não consegue desenvolver a ideia ao longo do enredo, gostaria de falar que é culpa do elenco, porém… |
| 3 | +0.023 | 0.812 | ✓ | (2.5★) darren aronofsky is a brilliant director, but he’s far from a great writer. he’s at his absolute best when he’s adapting another’s work. Black Swan, The Wrestle… |
| 4 | +0.021 | 0.794 |  | (2.5★) Brother I don’t even know, I remember this fucking HOOKED me but the part with the baby and the crowd was the wildest stomach turn I’ve ever seen ever. I think … |
| 5 | +0.020 | 0.790 |  | (3.0★) Honestly, had to look up what this movie meant and was surprised to find it has heavily biblical subtext, would never guess… it sure was an experience and made … |

**[medianas] Fotografia e tensão visual** — eixo `direcao_imagem`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.004 | 0.835 | ✓ | (3.0★) Tive que assistir mais umas duas vezes pra entender tudo, mas a fotografia é impecável de linda, bem filme pra se pensar mesmo, prestar atencao nos detalhes |
| 2 | +0.003 | 0.772 | ✓ | (3.0★) L'horror è il genere cinematografico che più si adatta allo stile di questo regista, amante del rapporto tra primi piani e campi lunghi. Un bell'omaggio a rosem… |
| 3 | +0.001 | 0.781 |  | (3.0★) Was annoyed the whole time like girl ur too pretty for that, but then i found out abt its symbolism like OH! As a spiritual girly and also a catholic … well uh |
| 4 | -0.002 | 0.763 | ✓ | (3.0★) метафоры отсылочки такие простые легко понятные что может быть как минус, но мне в принципе зашла картинка в целом но так на разок дженифер лоуренс своей игрой … |
| 5 | -0.004 | 0.810 | ✓ | (3.0★) Je trouve ça dommage de faire un huis clos pour y mettre tous les éléments de l'extérieur tels qu'ils sont. Par exemple une manif, la guerre, la police ? Dans u… |

**[positivas] Símbolos e metáforas religiosas** — eixo `livre`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.033 | 0.838 |  | (4.0★) Definitivamente no es para todos. Es una película llena de simbolismos y referencias de la biblia. Sin duda incomoda lo cruda que es pero podría hablar del sign… |
| 2 | +0.033 | 0.813 |  | (3.5★) Very disturbing introduction to Aronofsky. This had a really strong first hour, that for me tapered off as it progressed. The atmosphere was well done, sort of … |
| 3 | +0.031 | 0.798 |  | (3.5★) I was lost all the movie and then I realise it was about the bible and the origin of the life and all this story since Adam and Eve This shit blow my mind |
| 4 | +0.026 | 0.803 |  | (4.5★) The real hunger games. But actually the last ten minutes had me shocked and the religious-ness of it all hadn't clocked until after the movie and It just all ma… |
| 5 | +0.022 | 0.811 |  | (4.0★) i just saw someone said that the mother is the earth and the writer is the god The guests are Adam and Eve and their sons Abel and Cain "who literally one of th… |

**[positivas] Desempenho de Jennifer Lawrence** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.049 | 0.841 |  | (5.0★) kahit ako ehh kung ganyan mga bisita ko baka sunugin ko nalang din bahay namin. anyway, she's really that MOTHER! Jennifer Lawrence THE WOMAN THAT YOU ARE!!!! |
| 2 | +0.041 | 0.859 | ✓ | (5.0★) Darren Aronofsky as vezes acerta muito! Esse filme é uma obra de arte. praticamente deu a impressão de estar em primeira pessoa junto à personagem de Jennifer L… |
| 3 | +0.041 | 0.809 | ✓ | (4.0★) Breathtaking performance by the astonishing Jennifer Lawrence One of the most controversial works of modern time for a reason, the biblical story within the fil… |
| 4 | +0.041 | 0.852 | ✓ | (4.0★) Que filme insano! Essa mulher passou pelos meus maiores pesadelos dentro de 2 horas de filme. É loucura se eu disser que essa foi a maior performance da carreir… |
| 5 | +0.040 | 0.833 | ✓ | (5.0★) it just got worse and worse and worse ive never been so frustrated for a character that it made me cry in anger its like eraserhead from a mothers perspective i… |

**[positivas] Incompreensão inicial e revelação posterior** — eixo `expectativa`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.798 | ✓ | (3.5★) not gonna lie i was confused for most of it, but the ending recontextualized everything and honestly made me appreciate it way more, jennifer lawrence’s charact… |
| 2 | +0.019 | 0.825 |  | (3.5★) Non mentirò: ho capito cos'avessi visto solo dopo aver letto la spiegazione nel relativo forum di IMDB (sezione di cui non sentirò mai abbastanza la mancanza). |
| 3 | +0.019 | 0.785 |  | (3.5★) I was lost all the movie and then I realise it was about the bible and the origin of the life and all this story since Adam and Eve This shit blow my mind |
| 4 | +0.013 | 0.790 |  | (4.5★) The real hunger games. But actually the last ten minutes had me shocked and the religious-ness of it all hadn't clocked until after the movie and It just all ma… |
| 5 | +0.012 | 0.820 | ✓ | (4.0★) No me esperaba para nada esta película, toda la peli pensando en qué cojones está pasando, te deja enganchado, te frustras viendo la peli, luego al final lo ent… |

**[positivas] Sensação de desconforto e ansiedade** — eixo `tom_atmosfera`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.826 |  | (4.0★) Esta pelicula me sigue atormentando con sus manifestaciones semanales en sueños. Hay peores por supuesto, pero esta lo tiene todo para conseguir meterse en mi c… |
| 2 | +0.016 | 0.798 |  | (4.5★) “You never loved me." “You just loved how much I loved you." This is a average day of hosting a house party. This one had me go through many emotions and at the… |
| 3 | +0.015 | 0.780 |  | (5.0★) This was a 2 hour long mega nightmare and I mean that as a compliment. Firstly Jennifer Lawrence is such an amazing actress and she is slowly rising up my list … |
| 4 | +0.015 | 0.810 |  | (5.0★) sumpah benci bgt sama lakinya ajg😭😭 bro just listen to your wife for once. egois, haus validasi, empatinya nol. manusia-manusianya juga gatau diri bgst😔 |
| 5 | +0.014 | 0.807 |  | (5.0★) it just got worse and worse and worse ive never been so frustrated for a character that it made me cry in anger its like eraserhead from a mothers perspective i… |

**[positivas] Roteiro e direção intensos** — eixo `roteiro_estrutura`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.023 | 0.794 | ✓ | (5.0★) Hard-pressed to think of another movie that so masterfully and grievously captures the brutal, unrelenting chaos and arrogance of humans. An insanely good scrip… |
| 2 | +0.011 | 0.793 |  | (4.5★) “You never loved me." “You just loved how much I loved you." This is a average day of hosting a house party. This one had me go through many emotions and at the… |
| 3 | +0.011 | 0.804 |  | (5.0★) it just got worse and worse and worse ive never been so frustrated for a character that it made me cry in anger its like eraserhead from a mothers perspective i… |
| 4 | +0.011 | 0.775 |  | (5.0★) This was a 2 hour long mega nightmare and I mean that as a compliment. Firstly Jennifer Lawrence is such an amazing actress and she is slowly rising up my list … |
| 5 | +0.011 | 0.793 |  | (4.0★) i love the way aronofsky directs. on the one hand, this film was maybe the most stressed i’ve ever been in my life as a hater of crowds. it felt like a weird an… |

**[positivas] Crítica ao ego masculino e relacionamentos abusivos** — eixo `critica_social`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.830 |  | (5.0★) sumpah benci bgt sama lakinya ajg😭😭 bro just listen to your wife for once. egois, haus validasi, empatinya nol. manusia-manusianya juga gatau diri bgst😔 |
| 2 | +0.023 | 0.791 |  | (3.5★) not gonna lie i was confused for most of it, but the ending recontextualized everything and honestly made me appreciate it way more, jennifer lawrence’s charact… |
| 3 | +0.020 | 0.802 | ✓ | (4.5★) “You never loved me." “You just loved how much I loved you." This is a average day of hosting a house party. This one had me go through many emotions and at the… |
| 4 | +0.018 | 0.820 | ✓ | (4.0★) Recordé mucho el cuento Casa Tomada de Julio Cortázar , intrusos que entran a tu casa sin invitación y mi interpretación es que e todos estos entes son los mons… |
| 5 | +0.017 | 0.798 |  | (3.5★) Very disturbing introduction to Aronofsky. This had a really strong first hour, that for me tapered off as it progressed. The atmosphere was well done, sort of … |

### local — qwen3:14b (Ollama)

**[negativas] excesso de metáforas e simbolismo** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.806 |  | (2.0★) went in blind, and maybe it’s because I’m deeply unreligious, but a lot of the symbolism went over my head. Even the parts I did get, I was just like, “Ok…” I c… |
| 2 | +0.021 | 0.825 |  | (2.0★) Básicamente es todo una referencia a la biblia. No me gustan las películas ultra metafóricas, que tienes que estar tú comiendote el coco para entender de que va… |
| 3 | +0.021 | 0.800 |  | (2.0★) i have never been so bewildered and gagged at once. it was supposed to be a metaphor for nature but maybe the literacy crisis is real bc i didn’t catch that. if… |
| 4 | +0.021 | 0.843 |  | (1.0★) Uma experiência, definitivamente. Uma experiência ruim, mas mesmo assim… uma experiência. Simplesmente horrível e agoniante assistir. Entendo a alegoria, os sím… |
| 5 | +0.015 | 0.797 |  | (1.0★) Trying Too Hard: The Motion Picture It's the theatre equivalent of Aronofsky jerking off for 2 hours. At a macro level, it's nakedly transparent; a micro level,… |

**[negativas] trabalho de Jennifer Lawrence** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.792 |  | (1.5★) Took me way too long to realize my tv glitched and started playing the Albert Brooks film, Mother . Not sure how or why, but I thought Jennifer Lawrence was jus… |
| 2 | +0.015 | 0.819 |  | (0.5★) ragebait continuo. non ho mai visto un film che mi abbia fatto ARRABBIARE cosi tanto. Non ha nemmeno senso. Fastidio, collera, stress, per guardare sto film mi … |
| 3 | +0.015 | 0.786 |  | (1.0★) Most infuriating shit ever Would’ve been 3 stars but it’s a stupid fucking time loop movie This was fucking nonsense. I guess that’s the point but why. What the… |
| 4 | +0.014 | 0.825 |  | (1.5★) MEU DEUS QUE AGONIA ELES QUEBRANDO A CASA DA JENNIFER LAWRENCE PQP. A pessoa que pensou nessa coisa que chamamos de filme é a mesma que crucificou Jesus. |
| 5 | +0.012 | 0.790 |  | (2.0★) First hour engaging, but then its just jennifer lawrence torture without anything redeeming Feels like he had one idea and decided to make a whole film of it no… |

**[negativas] ritmo e desgaste do espectador** — eixo `ritmo`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.015 | 0.792 | ✓ | (2.0★) First hour engaging, but then its just jennifer lawrence torture without anything redeeming Feels like he had one idea and decided to make a whole film of it no… |
| 2 | +0.013 | 0.792 |  | (2.0★) Annoying. If this movie had just been Domhnall Gleeson murdering everybody I would have been happy. But you can't always get what you want. Menacing chair movem… |
| 3 | +0.013 | 0.798 |  | (2.0★) Without reading an explanation, it's very confusing and seems pointless. After hearing the explanation, its definitely a unique movie, but it's just not an ente… |
| 4 | +0.013 | 0.784 |  | (1.0★) Most infuriating shit ever Would’ve been 3 stars but it’s a stupid fucking time loop movie This was fucking nonsense. I guess that’s the point but why. What the… |
| 5 | +0.012 | 0.784 |  | (1.5★) What the actual fuck was the point of this movie “What hurts the most is that I’m not enough” Get the fuck out of my house, why do you think you can come into M… |

**[negativas] trabalho do diretor e intencionalidade artística** — eixo `direcao_imagem`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.017 | 0.799 |  | (1.0★) Trying Too Hard: The Motion Picture It's the theatre equivalent of Aronofsky jerking off for 2 hours. At a macro level, it's nakedly transparent; a micro level,… |
| 2 | +0.013 | 0.792 |  | (2.0★) Annoying. If this movie had just been Domhnall Gleeson murdering everybody I would have been happy. But you can't always get what you want. Menacing chair movem… |
| 3 | +0.010 | 0.823 | ✓ | (2.0★) De todas sus cintas de su director, está esta es la que me parece pierde el rumbo y se embrolla en metáforas y delirios absurdos. Aquí Aranovski busca decididam… |
| 4 | +0.009 | 0.794 |  | (2.0★) went in blind, and maybe it’s because I’m deeply unreligious, but a lot of the symbolism went over my head. Even the parts I did get, I was just like, “Ok…” I c… |
| 5 | +0.009 | 0.823 |  | (2.0★) el tipo de cosas que pasaban en la casa del papá de la cande película pretenciosa, busca impactar todo el rato, llena de simbolismos para ideas tan simples (ooh… |

**[negativas] trabalho de atores secundários e direção de cena** — eixo `atuacao`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.003 | 0.807 |  | (0.5★) ragebait continuo. non ho mai visto un film che mi abbia fatto ARRABBIARE cosi tanto. Non ha nemmeno senso. Fastidio, collera, stress, per guardare sto film mi … |
| 2 | +0.003 | 0.827 |  | (1.0★) Horrível. Pessimo posicionamento de camera, edição e iluminação, eu e minha família odiamos muito, não é contagiante quanto o hit borboletas de Vitor e Leo, mes… |
| 3 | +0.002 | 0.792 |  | (0.5★) Non. Ça m'apprendra à ne pas regarder les BA. Que Aronofsky se tienne loin de nous, et s'abstienne de retranscrire sur grand écran ce qui sort de son imaginatio… |
| 4 | +0.001 | 0.773 |  | (2.0★) imma b real i think the movie would have been better if they were meaner to J Law the whole time it gets real gnarly right at the end but ultimately the movie f… |
| 5 | +0.001 | 0.792 | ✓ | (2.0★) ok this movie is extremely well acted/written/filmed/etc but i don’t think i enjoyed a second of watching it and that’s moreso what the rating reflects |

**[negativas] conteúdo desagradável e impacto emocional** — eixo `impacto_emocional`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.036 | 0.807 | ✓ | (1.5★) What the actual fuck was the point of this movie “What hurts the most is that I’m not enough” Get the fuck out of my house, why do you think you can come into M… |
| 2 | +0.030 | 0.802 |  | (1.0★) Most infuriating shit ever Would’ve been 3 stars but it’s a stupid fucking time loop movie This was fucking nonsense. I guess that’s the point but why. What the… |
| 3 | +0.027 | 0.799 |  | (1.0★) This is Aronofsky’s hate letter to Christians after letting him down for Noah. This film is the best representation of a nightmare that I’ve ever seen. |
| 4 | +0.026 | 0.849 | ✓ | (1.0★) Uma experiência, definitivamente. Uma experiência ruim, mas mesmo assim… uma experiência. Simplesmente horrível e agoniante assistir. Entendo a alegoria, os sím… |
| 5 | +0.025 | 0.849 | ✓ | (1.0★) Horrível. Pessimo posicionamento de camera, edição e iluminação, eu e minha família odiamos muito, não é contagiante quanto o hit borboletas de Vitor e Leo, mes… |

**[medianas] sensação de desconforto e ansiedade** — eixo `tom_atmosfera`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.037 | 0.803 |  | (2.5★) This film is so stressful and anxiety-inducing that I will never willingly watch it again. The singular viewing I had of this film has stuck with me all of thes… |
| 2 | +0.028 | 0.801 |  | (2.5★) Brother I don’t even know, I remember this fucking HOOKED me but the part with the baby and the crowd was the wildest stomach turn I’ve ever seen ever. I think … |
| 3 | +0.028 | 0.810 |  | (3.0★) This is genuinely what it feels like when ur roommate is hosting a pregame. Holy shit this escalated so fast and I got left in the fucking dust. Act 3 is probab… |
| 4 | +0.026 | 0.814 |  | (3.0★) 121 minutes with what the fuck is going on?!?!? Ej va så stressa og ukomfortabel gjennom heile filmen so it made me feel what i was supposed to feel. Ej e distu… |
| 5 | +0.025 | 0.826 |  | (3.0★) je crois que ce film m’a donnée une crise de panique j’ai envie de brûler ma maison maintenant à la place de jennifer lawrence j’aurai crié SORTEZ SORTEZ DE MA … |

**[medianas] uso de metáforas e simbolismo** — eixo `direcao_imagem`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.805 |  | (3.0★) Was annoyed the whole time like girl ur too pretty for that, but then i found out abt its symbolism like OH! As a spiritual girly and also a catholic … well uh |
| 2 | +0.025 | 0.800 |  | (3.0★) A film I respect intellectually but no fucking clue if I like this or not. All I’ll say is that believing in a higher power doesn’t automatically make you a goo… |
| 3 | +0.012 | 0.800 |  | (2.5★) will make you force yourself to finish it because you just keep saying “wtf” out loud. After googling what this possibly could’ve been a metaphor for I did writ… |
| 4 | +0.010 | 0.824 | ✓ | (3.0★) Je trouve ça dommage de faire un huis clos pour y mettre tous les éléments de l'extérieur tels qu'ils sont. Par exemple une manif, la guerre, la police ? Dans u… |
| 5 | +0.007 | 0.831 |  | (3.0★) que filme doidjo é esse. Ainda bem que eu soube da metáfora e assisti pensando nela... mas tipo se deu errado tantas vezes pq ele tenta de novo e de novo, achei… |

**[medianas] desenvolvimento do enredo** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.013 | 0.802 | ✓ | (2.5★) darren aronofsky is a brilliant director, but he’s far from a great writer. he’s at his absolute best when he’s adapting another’s work. Black Swan, The Wrestle… |
| 2 | +0.010 | 0.785 | ✓ | (3.0★) A film I respect intellectually but no fucking clue if I like this or not. All I’ll say is that believing in a higher power doesn’t automatically make you a goo… |
| 3 | +0.009 | 0.794 | ✓ | (2.5★) Aronofsky’s signature blend of terrifying, pretentious, and heavy symbolism gets me every time but this.... To give credit where it’s due, the allegories are so… |
| 4 | +0.007 | 0.780 | ✓ | (2.5★) Michelle Pfeiffer so good The back half gets so heavy handed that you forget she was ever in it My big issue with Eddington was the I felt a genuinely engaging … |
| 5 | +0.007 | 0.783 | ✓ | (3.0★) Like some other Aronofsky films it may take an viewing to understand it better, though I will not do a second viewing, will read up on that ending especially, i… |

**[medianas] interpretação pessoal e reflexão** — eixo `livre`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.794 |  | (3.0★) A film I respect intellectually but no fucking clue if I like this or not. All I’ll say is that believing in a higher power doesn’t automatically make you a goo… |
| 2 | +0.015 | 0.816 |  | (3.0★) je crois que ce film m’a donnée une crise de panique j’ai envie de brûler ma maison maintenant à la place de jennifer lawrence j’aurai crié SORTEZ SORTEZ DE MA … |
| 3 | +0.015 | 0.804 |  | (3.0★) Film ne razumem Dženifer Lorens razumem ona je MAMA! kako glumačka tako i u stvarnom životu. 🍻 A razumem i zašto je ovo svrstano u žanr horora, Bože kako mrzim … |
| 4 | +0.015 | 0.783 |  | (3.0★) Abit of a difficult movie to review because half the time i didn't know what the fuck was going on 😂 but overall great performances from Jennifer Lawrence and J… |
| 5 | +0.014 | 0.779 |  | (3.0★) Great family film. The script demands a lot from Jennifer Lawrence and whilst she’s not perfect she manages to do a great job at being the central performance i… |

**[medianas] desempenho de Jennifer Lawrence** — eixo `atuacao`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.060 | 0.823 | ✓ | (3.0★) There’s a lot going on in the movie. I understand that the story is allegorical but at times I felt like it was getting a little lost in the sauce. I liked it b… |
| 2 | +0.047 | 0.812 | ✓ | (3.0★) Great family film. The script demands a lot from Jennifer Lawrence and whilst she’s not perfect she manages to do a great job at being the central performance i… |
| 3 | +0.039 | 0.807 | ✓ | (3.0★) Abit of a difficult movie to review because half the time i didn't know what the fuck was going on 😂 but overall great performances from Jennifer Lawrence and J… |
| 4 | +0.033 | 0.838 |  | (3.0★) il concept è anche ok, però mi è sembrato troppo lungo. mi sono piaciute però le inquadrature e credo che, insieme alla colonna sonora, regalino al film la gius… |
| 5 | +0.026 | 0.803 | ✓ | (2.5★) Two stars for Jennifer’s acting and overall spooky vibe. It did the psychological thriller genre justice in the first two acts. The third act however completely… |

**[medianas] confusão e falta de clareza** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.012 | 0.802 | ✓ | (3.0★) I give ⭐️⭐️⭐️ but I have to see it again as soon as possible because I think it will increase the rating. But at the first viewing it is complicated to understa… |
| 2 | +0.011 | 0.800 | ✓ | (2.5★) darren aronofsky is a brilliant director, but he’s far from a great writer. he’s at his absolute best when he’s adapting another’s work. Black Swan, The Wrestle… |
| 3 | +0.010 | 0.795 | ✓ | (2.5★) Aronofsky’s signature blend of terrifying, pretentious, and heavy symbolism gets me every time but this.... To give credit where it’s due, the allegories are so… |
| 4 | +0.009 | 0.777 | ✓ | (3.0★) had to look up the meaning but i understand it now. need a rewatch with the religious connotations in mind. not a huge fan of the portrayal of “eve” but it’s ne… |
| 5 | +0.009 | 0.781 |  | (2.5★) Brother I don’t even know, I remember this fucking HOOKED me but the part with the baby and the crowd was the wildest stomach turn I’ve ever seen ever. I think … |

**[positivas] Metáforas religiosas e simbolismo bíblico** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.807 |  | (4.0★) i just saw someone said that the mother is the earth and the writer is the god The guests are Adam and Eve and their sons Abel and Cain "who literally one of th… |
| 2 | +0.013 | 0.780 | ✓ | (3.5★) I was lost all the movie and then I realise it was about the bible and the origin of the life and all this story since Adam and Eve This shit blow my mind |
| 3 | +0.012 | 0.793 | ✓ | (3.5★) Very disturbing introduction to Aronofsky. This had a really strong first hour, that for me tapered off as it progressed. The atmosphere was well done, sort of … |
| 4 | +0.011 | 0.817 | ✓ | (4.0★) Definitivamente no es para todos. Es una película llena de simbolismos y referencias de la biblia. Sin duda incomoda lo cruda que es pero podría hablar del sign… |
| 5 | +0.008 | 0.820 | ✓ | (4.0★) Que filme insano! Essa mulher passou pelos meus maiores pesadelos dentro de 2 horas de filme. É loucura se eu disser que essa foi a maior performance da carreir… |

**[positivas] Performance de Jennifer Lawrence** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.053 | 0.845 |  | (5.0★) kahit ako ehh kung ganyan mga bisita ko baka sunugin ko nalang din bahay namin. anyway, she's really that MOTHER! Jennifer Lawrence THE WOMAN THAT YOU ARE!!!! |
| 2 | +0.052 | 0.820 | ✓ | (4.0★) Breathtaking performance by the astonishing Jennifer Lawrence One of the most controversial works of modern time for a reason, the biblical story within the fil… |
| 3 | +0.050 | 0.868 | ✓ | (5.0★) Darren Aronofsky as vezes acerta muito! Esse filme é uma obra de arte. praticamente deu a impressão de estar em primeira pessoa junto à personagem de Jennifer L… |
| 4 | +0.048 | 0.859 | ✓ | (4.0★) Que filme insano! Essa mulher passou pelos meus maiores pesadelos dentro de 2 horas de filme. É loucura se eu disser que essa foi a maior performance da carreir… |
| 5 | +0.045 | 0.809 | ✓ | (5.0★) This was a 2 hour long mega nightmare and I mean that as a compliment. Firstly Jennifer Lawrence is such an amazing actress and she is slowly rising up my list … |

**[positivas] Tensão e ansiedade psicológica** — eixo `tom_atmosfera`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.855 | ✓ | (3.5★) Bizarro, nojento, traumático, a primeira hora do filme é tão chata que eu quase desisti de ver o resto. Mas eu gostei das metáforas e mesmo sendo nojento a segu… |
| 2 | +0.023 | 0.787 |  | (5.0★) This was a 2 hour long mega nightmare and I mean that as a compliment. Firstly Jennifer Lawrence is such an amazing actress and she is slowly rising up my list … |
| 3 | +0.019 | 0.828 |  | (4.0★) Esta pelicula me sigue atormentando con sus manifestaciones semanales en sueños. Hay peores por supuesto, pero esta lo tiene todo para conseguir meterse en mi c… |
| 4 | +0.019 | 0.779 |  | (4.0★) This movie is my worst nightmare. All the people just showing up, touching shit, and fucking up the house. The third act was insane! Some of the symbolism was a… |
| 5 | +0.018 | 0.800 | ✓ | (3.5★) Watched with my own mother(!) A neat uncomfortable first and second act until it goes completely off the rails for the third. In fact I preferred the slow, unea… |

**[positivas] Confusão inicial e revelação no final** — eixo `roteiro_estrutura`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.031 | 0.798 | ✓ | (3.5★) not gonna lie i was confused for most of it, but the ending recontextualized everything and honestly made me appreciate it way more, jennifer lawrence’s charact… |
| 2 | +0.019 | 0.825 | ✓ | (3.5★) Non mentirò: ho capito cos'avessi visto solo dopo aver letto la spiegazione nel relativo forum di IMDB (sezione di cui non sentirò mai abbastanza la mancanza). |
| 3 | +0.017 | 0.823 | ✓ | (3.5★) Le parallèle de la religion est super intéressant et le développement des scènes d’autant plus, la BO est plutôt bonne, le dernier tiers du film était incompréh… |
| 4 | +0.017 | 0.797 | ✓ | (3.5★) Very disturbing introduction to Aronofsky. This had a really strong first hour, that for me tapered off as it progressed. The atmosphere was well done, sort of … |
| 5 | +0.016 | 0.783 | ✓ | (3.5★) I was lost all the movie and then I realise it was about the bible and the origin of the life and all this story since Adam and Eve This shit blow my mind |

**[positivas] Crítica à figura masculina e ao ego** — eixo `critica_social`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.041 | 0.869 |  | (5.0★) Uma das obras mais densas que eu já vi. Tal qual experimentar um prato que de tão spicy deixa a sua boca adormecida, e mesmo assim você curte a experiência, Mot… |
| 2 | +0.030 | 0.825 |  | (5.0★) sumpah benci bgt sama lakinya ajg😭😭 bro just listen to your wife for once. egois, haus validasi, empatinya nol. manusia-manusianya juga gatau diri bgst😔 |
| 3 | +0.016 | 0.757 |  | (4.0★) Что за мясо я сейчас посмотрел! Во-первых, что курили люди, когда решили наградить Дженифер Лоуренс и Хавьера Бардема за эти перфомансы номинацией на золотую ма… |
| 4 | +0.012 | 0.797 | ✓ | (4.5★) Miam miam on aime ce qui montre le vrai : quand l’homme est un connard, la femme, seule personne cohérente du film, ne se fait pas écouter donc forcément ça par… |
| 5 | +0.012 | 0.767 |  | (4.0★) المفروض لو كرهت الزوج ابقى كده كفرت ولا ايه ؟ بعيداً عن كل الرمزيات واختلافنا عليها الفيلم كان عبقري أنه يوصلي الشعور بالاستفزاز والتوتر من الأحداث الي بتحصل وك… |

**[positivas] Impacto emocional e psicológico** — eixo `impacto_emocional`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.810 | ✓ | (4.5★) “You never loved me." “You just loved how much I loved you." This is a average day of hosting a house party. This one had me go through many emotions and at the… |
| 2 | +0.021 | 0.782 | ✓ | (4.0★) This movie is my worst nightmare. All the people just showing up, touching shit, and fucking up the house. The third act was insane! Some of the symbolism was a… |
| 3 | +0.020 | 0.813 | ✓ | (5.0★) it just got worse and worse and worse ive never been so frustrated for a character that it made me cry in anger its like eraserhead from a mothers perspective i… |
| 4 | +0.019 | 0.820 | ✓ | (3.5★) Le film était bien ou en tout cas le message qu’il voulait faire passer était incroyable. Mais en même temps le film était tellement dérangeant. Spoiler: quand … |
| 5 | +0.018 | 0.830 | ✓ | (4.0★) Que filme insano! Essa mulher passou pelos meus maiores pesadelos dentro de 2 horas de filme. É loucura se eu disser que essa foi a maior performance da carreir… |

## Napoleão

### publicado — DeepSeek (síntese publicada)

**[negativas] Retrato de Napoleão** — eixo `roteiro_estrutura`, declarado 20/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.075 | 0.821 | ✓ | (1.5★) An emperor reduced to a punchline. Napoleon strips one of history’s most fascinating figures of his political and military brilliance, replacing him with a stra… |
| 2 | +0.056 | 0.821 |  | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 3 | +0.054 | 0.815 | ✓ | (1.0★) Worst portrayal of Napoleon I’ve ever seen they made him look like a cuck for Christ sake some of the lines they made him saw are awful some of the battle views… |
| 4 | +0.042 | 0.839 | ✓ | (1.5★) Cómo vas a poder arruinar una de las historias más conocidas, de uno de los conquistadores militares como reyes más conocidis de la historia y importantes. y co… |
| 5 | +0.041 | 0.796 | ✓ | (1.0★) They butchered Napoleon's portrayal. There are just so many things wrong with the film. First off, the casting for Napoleon is bad. He should have been way youn… |

**[negativas] Imprecisões históricas** — eixo `critica_social`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.057 | 0.822 | ✓ | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 2 | +0.043 | 0.799 |  | (1.0★) They butchered Napoleon's portrayal. There are just so many things wrong with the film. First off, the casting for Napoleon is bad. He should have been way youn… |
| 3 | +0.041 | 0.796 |  | (2.0★) The movie focuses too much on Napoleon's relationship with Joséphine, and some of the battles weren't shown as much as I had hoped. But overall, if you want to … |
| 4 | +0.041 | 0.811 | ✓ | (2.0★) I watched a two hour video detailing all of the historical inaccuracies of this movie last night so I figured I'd actually watch this (the standard version bc i… |
| 5 | +0.040 | 0.827 | ✓ | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |

**[negativas] Ritmo e edição** — eixo `ritmo`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.023 | 0.804 | ✓ | (0.5★) I can't do this. I've tried to get through this movie like 6 times and only make it 20 minutes before turning it off. Why is it so boring, I hate everything abo… |
| 2 | +0.019 | 0.824 |  | (1.0★) to się ogląda jak ekranizacje najgorszej, bezdusznej i nudnej książki historycznej, której autor już ma lekką demencję nie byłem przygotowany na aż taki chaos i… |
| 3 | +0.017 | 0.799 | ✓ | (2.0★) It wasn’t good 48 minutes in, it wasn’t good 48 minutes later, it wasn’t good 48 minutes before the end, I doubt watching 48 minutes more minutes will make it a… |
| 4 | +0.015 | 0.781 |  | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 5 | +0.015 | 0.815 |  | (2.0★) très bon visuellement, mais mauvais narrativement parlant. trop de faux raccord et le film donne plus l’impression de vouloir humilier Napoléon que le glorifier… |

**[negativas] Foco excessivo no romance** — eixo `roteiro_estrutura`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.052 | 0.839 | ✓ | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 2 | +0.049 | 0.804 | ✓ | (2.0★) The movie focuses too much on Napoleon's relationship with Joséphine, and some of the battles weren't shown as much as I had hoped. But overall, if you want to … |
| 3 | +0.045 | 0.840 | ✓ | (2.0★) Qué decepción. Esperaba ver una peli de guerra, principalmente porque el protagonista es de los mayores conquistadores y estrategas militares de la historia, as… |
| 4 | +0.045 | 0.808 | ✓ | (2.0★) Dissapointed. So many great battles could have been included. His conquest of Italy and creation of french sister republics could have been included. Shows his … |
| 5 | +0.042 | 0.807 | ✓ | (2.0★) I'd find this bullshit amazing if I was a 19th century brit. Horrible cast choice, a 60 year old man playing the role of a man who was in his 20s for a lot of t… |

**[negativas] Atuações e elenco** — eixo `atuacao`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.033 | 0.823 | ✓ | (1.0★) Juste pas bon. Je suis officiellement fkg tanné de voir Joaquin Phoenix à l'écran, il est pas superbe franchement. Overall super méga décevant pour un film de R… |
| 2 | +0.026 | 0.781 | ✓ | (2.0★) The Napoleon movie was very different from what I was expecting. It's a masterpiece, with great production values. The direction, actings, and costumes didn’t g… |
| 3 | +0.026 | 0.800 | ✓ | (2.0★) Długo wzbraniałem się przed nadrobieniem "Napoleona". Najlepsze lata Ridleya Scotta już dawno przeminęły, a w międzyczasie trudno było uniknąć opinii, że nie do… |
| 4 | +0.025 | 0.794 | ✓ | (1.0★) I’d give anything to go back in time and not watch this garbage. Joaquin Phoenix with the mail-it-in job of the century. They made Napoleon lame. Was that the w… |
| 5 | +0.024 | 0.805 | ✓ | (2.0★) Ridley Scott in his vintage years has become less reliable as a master filmmaker and this is just another example of his decline. Visually well made and well ac… |

**[negativas] Batalhas decepcionantes** — eixo `direcao_imagem`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.061 | 0.849 |  | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 2 | +0.056 | 0.819 |  | (2.0★) Dissapointed. So many great battles could have been included. His conquest of Italy and creation of french sister republics could have been included. Shows his … |
| 3 | +0.055 | 0.836 |  | (2.0★) the track ‘dawn’ from pride and prejudice is played over the scene where josephine flashes napoleon so that was quite an experience for me i’m quite disappointe… |
| 4 | +0.054 | 0.800 | ✓ | (1.5★) An emperor reduced to a punchline. Napoleon strips one of history’s most fascinating figures of his political and military brilliance, replacing him with a stra… |
| 5 | +0.054 | 0.850 |  | (2.0★) Qué decepción. Esperaba ver una peli de guerra, principalmente porque el protagonista es de los mayores conquistadores y estrategas militares de la historia, as… |

**[medianas] Batalhas visualmente impressionantes** — eixo `direcao_imagem`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.034 | 0.802 | ✓ | (3.0★) Ridley Scott still knows how to direct great battle sequences. About halfway through, I actually thought critics had been way too harsh on this, but by the end,… |
| 2 | +0.026 | 0.801 | ✓ | (3.0★) Napoleón destaca para mí por su gran calidad visual, las batallas y la ambientación, aunque se toma demasiadas libertades con la historia real. Presenta a Napol… |
| 3 | +0.018 | 0.787 | ✓ | (3.0★) Ridley Scott ensevelit ses batailles dans une lumière somptueuse, mais le Napoléon qui en ressort manque de feu intérieur. Phoenix reste trop énigmatique pour q… |
| 4 | +0.017 | 0.784 |  | (3.0★) It's entertaining for those who watch is as a pop history film, and quite disfavorable for those acquainted with the history and context of the time period, whi… |
| 5 | +0.015 | 0.826 | ✓ | (2.5★) Al ser una pelicula sobre la historia de Nápoleon le tenía una gran expectativa pero me decepcionó un montón por las carencias que tuvo por todos lados. Para em… |

**[medianas] Ritmo irregular e excesso de duração** — eixo `ritmo`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.028 | 0.798 | ✓ | (3.0★) Re-logging for the director’s cut. The 45 additional minutes of footage definitely improve the flow, letting the film breathe a bit more. But it doesn’t change … |
| 2 | +0.022 | 0.830 |  | (3.0★) Je ne sais quoi penser, c'est à la fois très beau et parfois très bon, mais le film laisse un arrière-goût un peu étrange, même avec la version longue j'ai l'im… |
| 3 | +0.020 | 0.796 | ✓ | (2.5★) Watched the Director’s Cut (all 3+ hours of it) in hopes that it would better than the theatrical release. Which it was, slightly, raising my rating from 2 star… |
| 4 | +0.019 | 0.845 | ✓ | (2.5★) Começa bem mas tem uma barriga chata demais no meio do filme. Depois que o Napoleão se separa da Josefina perde o encanto do filme. Dito isso as primeiras cenas… |
| 5 | +0.017 | 0.800 | ✓ | (3.0★) you would think that the director's cut of a ridley scott epic would be some revelatory experience, fundamentally improving a flawed original version. you would… |

**[medianas] Foco excessivo no relacionamento com Josefina** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.042 | 0.816 | ✓ | (3.0★) J’ai vu le directors cut de Napoleon et je trouve le fait que Joséphine et la relation que Napoleon et elle entreprennent fassent 50/60 % du film est très osé d… |
| 2 | +0.042 | 0.796 | ✓ | (3.0★) Saw director's cut and it was a bit boring with a few good scenes, this movie just focus so much in the personal life of Napoleon instead of showing one of the … |
| 3 | +0.038 | 0.811 | ✓ | (3.0★) An epic tale that was boring as hell. The movie was a lot of talky that didn't really drive anything forward. You almost really needed a history degree to under… |
| 4 | +0.037 | 0.817 | ✓ | (2.5★) Movie sure has its peaks, but it's too far away from being impressive. In the movie Napoleon's personality is mainly linked to his love story with Josephine, ma… |
| 5 | +0.036 | 0.791 | ✓ | (3.0★) One of the worst napoleon movies. they cant even use the real flags bro.. holy hollywood movie has to be. but the interpretation was good including the battles.… |

**[medianas] Imprecisões históricas e licenças poéticas** — eixo `critica_social`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.020 | 0.796 | ✓ | (3.0★) Napoleón destaca para mí por su gran calidad visual, las batallas y la ambientación, aunque se toma demasiadas libertades con la historia real. Presenta a Napol… |
| 2 | +0.020 | 0.807 | ✓ | (3.0★) Si fuese un personaje ficticio y no Napoleon hubiera sido mejor película porque menuda vergüenza hacer esto con lo interesante que es la historia de Napoleon. |
| 3 | +0.020 | 0.786 |  | (3.0★) Pen, men blir ganske lang må jeg si. Lite forkludrende på hva som gjorde Napoleon, Napoleon. Er en spesifikk historie som skal fortelles, og det blir litt tydel… |
| 4 | +0.018 | 0.802 |  | (3.0★) you would think that the director's cut of a ridley scott epic would be some revelatory experience, fundamentally improving a flawed original version. you would… |
| 5 | +0.017 | 0.828 | ✓ | (2.5★) Al ser una pelicula sobre la historia de Nápoleon le tenía una gran expectativa pero me decepcionó un montón por las carencias que tuvo por todos lados. Para em… |

**[medianas] Atuações de destaque, especialmente de Phoenix e Kirby** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.046 | 0.831 | ✓ | (2.5★) Une bande annonce qui promettait un Ridley Scott au plus haut de sa forme avec un nouveau film historique mémorable et c’est assez décevant. Dans les points pos… |
| 2 | +0.034 | 0.833 | ✓ | (3.0★) Como diría el grandísimo PEPO FANTASY: “en plan… se centran demasiado en lo que es el amor con la jamba”. Me da realmente pena no haber caído de pie viendo ‘Nap… |
| 3 | +0.033 | 0.802 | ✓ | (3.0★) Ridley Scott ensevelit ses batailles dans une lumière somptueuse, mais le Napoléon qui en ressort manque de feu intérieur. Phoenix reste trop énigmatique pour q… |
| 4 | +0.030 | 0.828 | ✓ | (2.5★) Hay algo neurodivergente en la interpretación de Joaquín Phoenix que me hace pensar en el presidente Javier Gerardo Milei. Mucho CG, por momentos era como ver u… |
| 5 | +0.023 | 0.785 | ✓ | (3.0★) Not a bad film but definitely had some flaws. First of all I thought pheonix’s performance was great as napoleon but found the main characters were written a li… |

**[medianas] Construção de personagem fraca e falta de profundidade política** — eixo `roteiro_estrutura`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.046 | 0.800 | ✓ | (3.0★) Saw director's cut and it was a bit boring with a few good scenes, this movie just focus so much in the personal life of Napoleon instead of showing one of the … |
| 2 | +0.042 | 0.817 | ✓ | (3.0★) Napoleón destaca para mí por su gran calidad visual, las batallas y la ambientación, aunque se toma demasiadas libertades con la historia real. Presenta a Napol… |
| 3 | +0.041 | 0.796 | ✓ | (3.0★) One of the worst napoleon movies. they cant even use the real flags bro.. holy hollywood movie has to be. but the interpretation was good including the battles.… |
| 4 | +0.038 | 0.825 | ✓ | (3.0★) Si fuese un personaje ficticio y no Napoleon hubiera sido mejor película porque menuda vergüenza hacer esto con lo interesante que es la historia de Napoleon. |
| 5 | +0.035 | 0.815 | ✓ | (2.5★) Movie sure has its peaks, but it's too far away from being impressive. In the movie Napoleon's personality is mainly linked to his love story with Josephine, ma… |

**[positivas] Atuações e carisma de Joaquin Phoenix e Vanessa Kirby** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.793 | ✓ | (5.0★) Joaquin Phoenix is absolutely amazing in this role! The pacing is fantastic. How faithful this is to history and the man as he was is spectacular! Each piece of… |
| 2 | +0.022 | 0.781 | ✓ | (3.5★) “There is just no stopping this man, Run!” I was disappointed this movie didn’t receive the best ratings, but I found it a fine biopic. This movie shows how utt… |
| 3 | +0.020 | 0.796 | ✓ | (3.5★) I've always thought that making a film about a great historical figure is one of the hardest things a director can do. Unless it's a TV series or a whole film s… |
| 4 | +0.019 | 0.803 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 5 | +0.013 | 0.791 |  | (4.0★) Phoenix and Scott decide to demystify Napoleon and show him as “just another guy” that happens to be good at war, but not good at love Worked for me, felt like … |

**[positivas] Impacto visual e direção de arte** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.802 |  | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |
| 2 | +0.015 | 0.813 | ✓ | (4.5★) la réalisation n’est pas parfaite mais juste pour l’histoire du plus grand chef de guerre de tout les temps en plus français et corse obliger de le mettre dans … |
| 3 | +0.013 | 0.798 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 4 | +0.012 | 0.815 | ✓ | (3.5★) Et bien j'ai bien aimé. Le choix d'avoir plutôt orienté la vie de Napoléon sur son aspect sentimental est un choix qu'il faut respecter. Oui il y a des errances… |
| 5 | +0.012 | 0.795 |  | (4.0★) ‘’ Tell them to make the rain stop” the man you were Napoleon. The performance is phenomenal. God damn it i love France, Paris and this little Corsican man And … |

**[positivas] Qualidade das cenas de batalha** — eixo `direcao_imagem`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.788 | ✓ | (3.5★) “There is just no stopping this man, Run!” I was disappointed this movie didn’t receive the best ratings, but I found it a fine biopic. This movie shows how utt… |
| 2 | +0.028 | 0.792 |  | (4.0★) La storia la scrivono i vincitori. La vera storia la scrivono i sopravvissuti. Le sceneggiature dei film di Ridley Scott le scrivono Sal Da Vinci e Il Giaguaro_… |
| 3 | +0.024 | 0.814 | ✓ | (3.5★) Un bon petit film à la Ridley Scott, le film est sympa mais pas exceptionnel non plus et puis je suis pas sur que le film colle à la réalité parce que je pense … |
| 4 | +0.023 | 0.806 |  | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |
| 5 | +0.021 | 0.795 | ✓ | (3.5★) I’ll preface by saying i only watched the director’s cut. That said, god, i hate that i liked this. Do i think it’s a good portrayal of how Napoleon was perceiv… |

**[positivas] Abordagem pessoal e íntima do personagem** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.040 | 0.798 | ✓ | (4.0★) I think this movie did a great job at portraying who Napoleon really was as a person. It had amazing scenes of his triumphs as well as his mistakes and what I t… |
| 2 | +0.037 | 0.809 | ✓ | (3.5★) It was a decent napoleon’s film and interpretation. Guy wasn’t the cleanest man out there if real history you know. People expected more because they don’t know… |
| 3 | +0.035 | 0.811 | ✓ | (3.5★) I've always thought that making a film about a great historical figure is one of the hardest things a director can do. Unless it's a TV series or a whole film s… |
| 4 | +0.035 | 0.834 | ✓ | (3.5★) Bah j'aime vraiment bien ce film. Chaque scène, chaque décor est une fresque, c'est somptueux. Le personnage de Napoléon est incomplet certes, mais loin d'être … |
| 5 | +0.034 | 0.837 | ✓ | (3.5★) Et bien j'ai bien aimé. Le choix d'avoir plutôt orienté la vie de Napoléon sur son aspect sentimental est un choix qu'il faut respecter. Oui il y a des errances… |

**[positivas] Ritmo e edição** — eixo `ritmo`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.790 |  | (4.0★) I did Napoleon youth life podcast part 1 ➡️ part two (French revolution) ➡️ napoleon extended edition➡️ napoleon egypt podcast ➡️ catching Napoleon podcast and … |
| 2 | +0.023 | 0.806 | ✓ | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |
| 3 | +0.007 | 0.801 | ✓ | (4.0★) La messa in scena è meravigliosa per tutta la durata di 3:20 (ho visto la director's cut), Joaquin è sempre Dio e Scott si riconferma un regista che rimpiangere… |
| 4 | +0.006 | 0.758 | ✓ | (3.5★) Прекрасная игра Феникса, которая ломается об очень короткий хрон, для такого человека, как Наполеон 2,5 часа очень мало для раскрытия всей величины его жизни |
| 5 | +0.005 | 0.777 |  | (3.5★) It was a decent napoleon’s film and interpretation. Guy wasn’t the cleanest man out there if real history you know. People expected more because they don’t know… |

**[positivas] Incentivo à pesquisa histórica** — eixo `livre`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.038 | 0.796 |  | (4.0★) I think this movie did a great job at portraying who Napoleon really was as a person. It had amazing scenes of his triumphs as well as his mistakes and what I t… |
| 2 | +0.037 | 0.802 |  | (4.0★) I did Napoleon youth life podcast part 1 ➡️ part two (French revolution) ➡️ napoleon extended edition➡️ napoleon egypt podcast ➡️ catching Napoleon podcast and … |
| 3 | +0.036 | 0.838 |  | (3.5★) Et bien j'ai bien aimé. Le choix d'avoir plutôt orienté la vie de Napoléon sur son aspect sentimental est un choix qu'il faut respecter. Oui il y a des errances… |
| 4 | +0.033 | 0.818 |  | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 5 | +0.032 | 0.804 |  | (3.5★) It was a decent napoleon’s film and interpretation. Guy wasn’t the cleanest man out there if real history you know. People expected more because they don’t know… |

### local — qwen3:14b (Ollama)

**[negativas] Inaccuracy histórica** — eixo `critica_social`, declarado 20/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.032 | 0.791 |  | (1.5★) Just changed too many things. What about the Italian Campaign? He didn’t use cannons to win the Battle of the Pyramids. crossing of the Alps, Peninsular War, Tr… |
| 2 | +0.031 | 0.796 | ✓ | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 3 | +0.023 | 0.793 | ✓ | (2.0★) I watched a two hour video detailing all of the historical inaccuracies of this movie last night so I figured I'd actually watch this (the standard version bc i… |
| 4 | +0.021 | 0.785 |  | (2.0★) Dissapointed. So many great battles could have been included. His conquest of Italy and creation of french sister republics could have been included. Shows his … |
| 5 | +0.018 | 0.780 |  | (1.0★) Worst portrayal of Napoleon I’ve ever seen they made him look like a cuck for Christ sake some of the lines they made him saw are awful some of the battle views… |

**[negativas] Foco excessivo na relação com Joséphine** — eixo `roteiro_estrutura`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.051 | 0.806 | ✓ | (2.0★) The movie focuses too much on Napoleon's relationship with Joséphine, and some of the battles weren't shown as much as I had hoped. But overall, if you want to … |
| 2 | +0.045 | 0.833 | ✓ | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 3 | +0.040 | 0.806 | ✓ | (2.0★) I'd find this bullshit amazing if I was a 19th century brit. Horrible cast choice, a 60 year old man playing the role of a man who was in his 20s for a lot of t… |
| 4 | +0.039 | 0.830 | ✓ | (2.0★) Ce film aurait pu traiter des sujets passionnants : les stratégies de combat de Napoléon, sa manière d'être et de commander durant la guerre, ce qu'il cherchait… |
| 5 | +0.036 | 0.831 | ✓ | (2.0★) Qué decepción. Esperaba ver una peli de guerra, principalmente porque el protagonista es de los mayores conquistadores y estrategas militares de la historia, as… |

**[negativas] Interpretação inadequada de Napoleão** — eixo `atuacao`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.066 | 0.811 |  | (1.5★) An emperor reduced to a punchline. Napoleon strips one of history’s most fascinating figures of his political and military brilliance, replacing him with a stra… |
| 2 | +0.060 | 0.841 | ✓ | (2.0★) Ridley Scott in his vintage years has become less reliable as a master filmmaker and this is just another example of his decline. Visually well made and well ac… |
| 3 | +0.059 | 0.825 |  | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 4 | +0.055 | 0.846 | ✓ | (1.0★) Un navet sans nom. Les inexactitudes historiques ne sont pas si dérangeantes étant donné que le film est centré sur la personne de Napoléon, presque de manière … |
| 5 | +0.051 | 0.821 | ✓ | (1.0★) I’d give anything to go back in time and not watch this garbage. Joaquin Phoenix with the mail-it-in job of the century. They made Napoleon lame. Was that the w… |

**[negativas] Falta de profundidade e contexto** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.036 | 0.801 |  | (2.0★) Not only is it historically inaccurate and portrays Napoleon as a living caricature, but it turned one of the most famously colorful and bright periods of histo… |
| 2 | +0.033 | 0.788 | ✓ | (2.0★) The movie focuses too much on Napoleon's relationship with Joséphine, and some of the battles weren't shown as much as I had hoped. But overall, if you want to … |
| 3 | +0.032 | 0.787 | ✓ | (1.0★) They butchered Napoleon's portrayal. There are just so many things wrong with the film. First off, the casting for Napoleon is bad. He should have been way youn… |
| 4 | +0.028 | 0.815 | ✓ | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 5 | +0.026 | 0.797 |  | (2.0★) I watched a two hour video detailing all of the historical inaccuracies of this movie last night so I figured I'd actually watch this (the standard version bc i… |

**[negativas] Falta de ação e ritmo lento** — eixo `ritmo`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.778 |  | (1.0★) They butchered Napoleon's portrayal. There are just so many things wrong with the film. First off, the casting for Napoleon is bad. He should have been way youn… |
| 2 | +0.022 | 0.803 | ✓ | (2.0★) the track ‘dawn’ from pride and prejudice is played over the scene where josephine flashes napoleon so that was quite an experience for me i’m quite disappointe… |
| 3 | +0.022 | 0.803 | ✓ | (0.5★) I can't do this. I've tried to get through this movie like 6 times and only make it 20 minutes before turning it off. Why is it so boring, I hate everything abo… |
| 4 | +0.019 | 0.806 |  | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 5 | +0.019 | 0.773 |  | (2.0★) The movie focuses too much on Napoleon's relationship with Joséphine, and some of the battles weren't shown as much as I had hoped. But overall, if you want to … |

**[negativas] Falta de coesão e estrutura narrativa** — eixo `roteiro_estrutura`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.017 | 0.804 | ✓ | (2.0★) La vida de Napoleón no es interesante por su relación con josefina si no por su carrera militar y política, las fechas estan mal puestas, las batallas son Holly… |
| 2 | +0.016 | 0.787 |  | (2.0★) I watched a two hour video detailing all of the historical inaccuracies of this movie last night so I figured I'd actually watch this (the standard version bc i… |
| 3 | +0.016 | 0.771 | ✓ | (1.0★) They butchered Napoleon's portrayal. There are just so many things wrong with the film. First off, the casting for Napoleon is bad. He should have been way youn… |
| 4 | +0.015 | 0.820 |  | (1.0★) to się ogląda jak ekranizacje najgorszej, bezdusznej i nudnej książki historycznej, której autor już ma lekką demencję nie byłem przygotowany na aż taki chaos i… |
| 5 | +0.014 | 0.797 |  | (2.0★) It wasn’t good 48 minutes in, it wasn’t good 48 minutes later, it wasn’t good 48 minutes before the end, I doubt watching 48 minutes more minutes will make it a… |

**[medianas] Foco excessivo na vida pessoal de Napoleão** — eixo `roteiro_estrutura`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.045 | 0.819 | ✓ | (3.0★) J’ai vu le directors cut de Napoleon et je trouve le fait que Joséphine et la relation que Napoleon et elle entreprennent fassent 50/60 % du film est très osé d… |
| 2 | +0.043 | 0.798 | ✓ | (3.0★) Saw director's cut and it was a bit boring with a few good scenes, this movie just focus so much in the personal life of Napoleon instead of showing one of the … |
| 3 | +0.042 | 0.823 | ✓ | (2.5★) Movie sure has its peaks, but it's too far away from being impressive. In the movie Napoleon's personality is mainly linked to his love story with Josephine, ma… |
| 4 | +0.040 | 0.802 | ✓ | (3.0★) Not a bad film but definitely had some flaws. First of all I thought pheonix’s performance was great as napoleon but found the main characters were written a li… |
| 5 | +0.036 | 0.821 | ✓ | (2.5★) Une bande annonce qui promettait un Ridley Scott au plus haut de sa forme avec un nouveau film historique mémorable et c’est assez décevant. Dans les points pos… |

**[medianas] Erros históricos e falta de precisão factual** — eixo `critica_social`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.821 | ✓ | (2.5★) terribly inaccurate, josephines death, thomas-alexandre dumas’ involvement when the portrait of the crowning cermony, the meeting between arthur and napoleon, a… |
| 2 | +0.024 | 0.779 | ✓ | (3.0★) One of the worst napoleon movies. they cant even use the real flags bro.. holy hollywood movie has to be. but the interpretation was good including the battles.… |
| 3 | +0.018 | 0.798 |  | (2.5★) Movie sure has its peaks, but it's too far away from being impressive. In the movie Napoleon's personality is mainly linked to his love story with Josephine, ma… |
| 4 | +0.018 | 0.804 | ✓ | (3.0★) Si fuese un personaje ficticio y no Napoleon hubiera sido mejor película porque menuda vergüenza hacer esto con lo interesante que es la historia de Napoleon. |
| 5 | +0.016 | 0.815 | ✓ | (3.0★) Plutôt bien réalisé mais ils se sont perdus, c’est-à-dire qu’ils ont passés beaucoup de détails qui font que finalement le personnage de Bonaparte n’est pas tel… |

**[medianas] Cenas de batalha visualmente impressionantes, mas insuficientes** — eixo `direcao_imagem`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.810 | ✓ | (3.0★) Napoleón destaca para mí por su gran calidad visual, las batallas y la ambientación, aunque se toma demasiadas libertades con la historia real. Presenta a Napol… |
| 2 | +0.035 | 0.804 | ✓ | (3.0★) Ridley Scott still knows how to direct great battle sequences. About halfway through, I actually thought critics had been way too harsh on this, but by the end,… |
| 3 | +0.032 | 0.843 | ✓ | (2.5★) Al ser una pelicula sobre la historia de Nápoleon le tenía una gran expectativa pero me decepcionó un montón por las carencias que tuvo por todos lados. Para em… |
| 4 | +0.031 | 0.827 |  | (2.5★) Da una imagen de Napoleón más de meme que de aura y lo de que los franceses hablen en inglés le resta mucho. Por lo demás no está tan mal... aunque se me ha hec… |
| 5 | +0.031 | 0.786 |  | (3.0★) One of the worst napoleon movies. they cant even use the real flags bro.. holy hollywood movie has to be. but the interpretation was good including the battles.… |

**[medianas] Interpretação do personagem insatisfatória** — eixo `atuacao`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.053 | 0.822 | ✓ | (3.0★) Ridley Scott ensevelit ses batailles dans une lumière somptueuse, mais le Napoléon qui en ressort manque de feu intérieur. Phoenix reste trop énigmatique pour q… |
| 2 | +0.043 | 0.841 | ✓ | (2.5★) Hay algo neurodivergente en la interpretación de Joaquín Phoenix que me hace pensar en el presidente Javier Gerardo Milei. Mucho CG, por momentos era como ver u… |
| 3 | +0.043 | 0.854 | ✓ | (2.5★) Al ser una pelicula sobre la historia de Nápoleon le tenía una gran expectativa pero me decepcionó un montón por las carencias que tuvo por todos lados. Para em… |
| 4 | +0.040 | 0.816 |  | (3.0★) Napoleón destaca para mí por su gran calidad visual, las batallas y la ambientación, aunque se toma demasiadas libertades con la historia real. Presenta a Napol… |
| 5 | +0.037 | 0.816 | ✓ | (3.0★) Pro: • Kulissen und Kostüme sind gewaltig • Joaquin Phoenix • der Director Cut ist besser als die Kinofassung • unglaublich detailverliebt Contra: • über 200 Mi… |

**[medianas] Estilo visual e cinematografia apreciados, mas não suficientes para compensar falhas narrativas** — eixo `direcao_imagem`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.852 | ✓ | (2.5★) É um filme visualmente muito bonito. Mas a construção do personagem é péssima. Anacronismo semântico, com pretensão pacifista e de condenação póstuma. |
| 2 | +0.020 | 0.782 | ✓ | (3.0★) Not a bad film but definitely had some flaws. First of all I thought pheonix’s performance was great as napoleon but found the main characters were written a li… |
| 3 | +0.019 | 0.830 | ✓ | (2.5★) Al ser una pelicula sobre la historia de Nápoleon le tenía una gran expectativa pero me decepcionó un montón por las carencias que tuvo por todos lados. Para em… |
| 4 | +0.018 | 0.787 | ✓ | (3.0★) Ridley Scott ensevelit ses batailles dans une lumière somptueuse, mais le Napoléon qui en ressort manque de feu intérieur. Phoenix reste trop énigmatique pour q… |
| 5 | +0.016 | 0.739 |  | (2.5★) ريدلي سكوت كان بيده ما يكفي لصناعة فيلم للتاريخ، يمتلك قصة مو أي قصة وانما حياة أحد أعظم القادة نابليون ، ويمتلك خواكين فينيكس لبطولة الدور، ويمتلك الإمكانيات م… |

**[medianas] Tempo de duração e ritmo narrativo criticados** — eixo `ritmo`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.805 | ✓ | (2.5★) Watched the Director’s Cut (all 3+ hours of it) in hopes that it would better than the theatrical release. Which it was, slightly, raising my rating from 2 star… |
| 2 | +0.025 | 0.794 | ✓ | (3.0★) Ridley Scott still knows how to direct great battle sequences. About halfway through, I actually thought critics had been way too harsh on this, but by the end,… |
| 3 | +0.025 | 0.803 | ✓ | (3.0★) Pro: • Kulissen und Kostüme sind gewaltig • Joaquin Phoenix • der Director Cut ist besser als die Kinofassung • unglaublich detailverliebt Contra: • über 200 Mi… |
| 4 | +0.022 | 0.789 |  | (3.0★) It's entertaining for those who watch is as a pop history film, and quite disfavorable for those acquainted with the history and context of the time period, whi… |
| 5 | +0.022 | 0.807 | ✓ | (3.0★) The year is 2023, and two new biopics have been released about some of the most destructive men known to our world. One of those films is named Oppenheimer, and… |

**[positivas] Batalhas e cenas de ação** — eixo `direcao_imagem`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.018 | 0.803 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 2 | +0.018 | 0.805 |  | (3.5★) i know this film get criticised A LOT, but tbh i enjoyed it. oh men with their ambitions, ‘status’, and ‘HONOR’, acting big with their pride, feeling dominant, … |
| 3 | +0.014 | 0.840 | ✓ | (3.5★) ​"Não vejo na religião o mistério da Encarnação, mas o mistério da ordem social. A religião associa ao Céu uma ideia de igualdade que impede que os ricos sejam … |
| 4 | +0.014 | 0.812 | ✓ | (4.5★) la réalisation n’est pas parfaite mais juste pour l’histoire du plus grand chef de guerre de tout les temps en plus français et corse obliger de le mettre dans … |
| 5 | +0.011 | 0.770 | ✓ | (3.5★) “There is just no stopping this man, Run!” I was disappointed this movie didn’t receive the best ratings, but I found it a fine biopic. This movie shows how utt… |

**[positivas] Interpretação de Joaquin Phoenix** — eixo `atuacao`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.076 | 0.860 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 2 | +0.074 | 0.833 | ✓ | (3.5★) “There is just no stopping this man, Run!” I was disappointed this movie didn’t receive the best ratings, but I found it a fine biopic. This movie shows how utt… |
| 3 | +0.060 | 0.820 | ✓ | (5.0★) Joaquin Phoenix is absolutely amazing in this role! The pacing is fantastic. How faithful this is to history and the man as he was is spectacular! Each piece of… |
| 4 | +0.051 | 0.863 | ✓ | (3.5★) Un deuxième visionnage bien rentable, cette fois-ci vu en version intégrale qui rajoute 48 minutes environ. Je me rappelle que la version cinéma de 2h40 donnait… |
| 5 | +0.046 | 0.822 | ✓ | (3.5★) I've always thought that making a film about a great historical figure is one of the hardest things a director can do. Unless it's a TV series or a whole film s… |

**[positivas] Trabalho de direção e produção** — eixo `direcao_imagem`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.008 | 0.808 |  | (3.5★) Adaptación histórica del carajo. Realmente emocionante como se abarca la trama de Josefina. Es una de las mejores representaciones fílmicas sobre uno de los pro… |
| 2 | +0.008 | 0.806 | ✓ | (4.5★) la réalisation n’est pas parfaite mais juste pour l’histoire du plus grand chef de guerre de tout les temps en plus français et corse obliger de le mettre dans … |
| 3 | +0.008 | 0.763 | ✓ | (4.0★) I happened to like this movie obviously not that historically accurate all tho technically he did burn down Moscow with the help of the Russians because they kn… |
| 4 | +0.006 | 0.825 |  | (4.0★) Une claque du cinéma, un film qui narre l'histoire de Napoléon avec justesse et clarté, il y a même des petits détailles auquel ils ont pensé, le fait qu'il soi… |
| 5 | +0.004 | 0.787 |  | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |

**[positivas] Relação entre Napoleão e Josephine** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.056 | 0.832 | ✓ | (3.5★) I've always thought that making a film about a great historical figure is one of the hardest things a director can do. Unless it's a TV series or a whole film s… |
| 2 | +0.046 | 0.829 | ✓ | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |
| 3 | +0.045 | 0.847 | ✓ | (3.5★) Et bien j'ai bien aimé. Le choix d'avoir plutôt orienté la vie de Napoléon sur son aspect sentimental est un choix qu'il faut respecter. Oui il y a des errances… |
| 4 | +0.040 | 0.797 | ✓ | (4.0★) I think this movie did a great job at portraying who Napoleon really was as a person. It had amazing scenes of his triumphs as well as his mistakes and what I t… |
| 5 | +0.037 | 0.822 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |

**[positivas] Abordagem do personagem Napoleão** — eixo `roteiro_estrutura`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.047 | 0.804 | ✓ | (4.0★) I think this movie did a great job at portraying who Napoleon really was as a person. It had amazing scenes of his triumphs as well as his mistakes and what I t… |
| 2 | +0.047 | 0.846 | ✓ | (3.5★) Bah j'aime vraiment bien ce film. Chaque scène, chaque décor est une fresque, c'est somptueux. Le personnage de Napoléon est incomplet certes, mais loin d'être … |
| 3 | +0.046 | 0.822 | ✓ | (3.5★) I've always thought that making a film about a great historical figure is one of the hardest things a director can do. Unless it's a TV series or a whole film s… |
| 4 | +0.045 | 0.830 | ✓ | (4.0★) ★★★★☆ (8/10) Napoléon est un film que j'ai beaucoup apprécié. Les scènes de bataille sont spectaculaires, la mise en scène est magnifique et les décors donnent … |
| 5 | +0.043 | 0.836 |  | (3.5★) En la película hacen todo lo posible para evitar mencionar a España ni una sola maldita vez. Está guapa pero me parece bastante feo ni mencionar que Napoleón tu… |

**[positivas] Versão do diretor (Director’s Cut)** — eixo `livre`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.051 | 0.834 |  | (4.0★) This cut is so much better than the original. While I was planning to save Ridley Scott’s Napoleon until I reached the next chapter of my director deep dive, th… |
| 2 | +0.026 | 0.811 |  | (3.5★) Director’s Cut I have really mixed feelings on this. While I have to say this is an outstanding production with stellar cinematography, amazing set and costume … |
| 3 | +0.021 | 0.816 |  | (4.0★) La messa in scena è meravigliosa per tutta la durata di 3:20 (ho visto la director's cut), Joaquin è sempre Dio e Scott si riconferma un regista che rimpiangere… |
| 4 | +0.020 | 0.794 |  | (3.5★) This film is aesthetically great but the plot is a bit too rushed, the focus is often in the wrong places and the characters just don’t feel right. The director… |
| 5 | +0.017 | 0.781 |  | (4.0★) La storia la scrivono i vincitori. La vera storia la scrivono i sopravvissuti. Le sceneggiature dei film di Ridley Scott le scrivono Sal Da Vinci e Il Giaguaro_… |

## A Substância

### publicado — DeepSeek (síntese publicada)

**[negativas] Excesso de gore e violência gratuita** — eixo `tom_atmosfera`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.032 | 0.799 |  | (0.5★) Coralie Fargeat hat so gesagt „hey was ist wenn wir einen Film machen der wie Alien ist aber in noch ekliger und scheiße“ und sie hatte noch nie mehr Unrecht. N… |
| 2 | +0.028 | 0.808 |  | (2.0★) This sucked ass :D Niin paska kässäri mitä helvettiä nyt ja joo kehollinen kauhu puhuttelee jonkun verran mut ei näin paljoo! Tykkäsin Demi Mooresta :) ja lavas… |
| 3 | +0.027 | 0.808 | ✓ | (2.0★) An extreme movie that really goes all the way and beyond in terms of violence and gore which you seldomly see with a female filmmaker (Titane‘s extremity looks … |
| 4 | +0.026 | 0.834 | ✓ | (2.0★) Diría que es interesante pero la verdad que no va a ningún lado. Gore y porno suave con la intención de mandar un mensaje pero lo único que estás haciendo es ve… |
| 5 | +0.024 | 0.789 |  | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |

**[negativas] Exibicionismo e nudez excessiva** — eixo `tom_atmosfera`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.790 |  | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |
| 2 | +0.021 | 0.822 |  | (1.0★) Abberant. Le message est super intéressant, une belle morale... TOUTEFOIS : Je savais pas que j'avais lancé un porno 💀 j'ai vu plus de cul et de seins que dans … |
| 3 | +0.020 | 0.814 |  | (2.0★) Quelle déception ce film. Le début est vraiment un chef d’œuvre mais la fin est tellement bâclé on croirait une caméra cachée. Entre les scènes de nudité et le … |
| 4 | +0.020 | 0.833 |  | (2.0★) Entiendo perfectamente la crítica que genera está película sobre la industria de la actuación pero para mí gusto es innecesario usar todas escenas explícitas qu… |
| 5 | +0.018 | 0.799 | ✓ | (2.0★) An extreme movie that really goes all the way and beyond in terms of violence and gore which you seldomly see with a female filmmaker (Titane‘s extremity looks … |

**[negativas] Roteiro sem desenvolvimento** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.024 | 0.816 |  | (1.5★) La peor película que vi en el año. La única razón por la que no le pongo un 1, es pq el trabajo artístico está 10/10, pero es grotésca sin sentido, aburrida y e… |
| 2 | +0.023 | 0.790 | ✓ | (1.0★) Interesting concept and mostly entertaining throughout but the ending is so idiotic it completely ruins the entire film, zero respect for the director/screenwri… |
| 3 | +0.023 | 0.809 |  | (2.0★) You get the point in the first 20 mins max and it just keeps saying the same thing for way too long when it could elaborate or delve further into it and it just… |
| 4 | +0.022 | 0.813 | ✓ | (1.0★) I hate that. This movie has no final plot, or even if you call thin end the plot, it doesn’t have any sense at all. Everything is totally random and unnecessary… |
| 5 | +0.022 | 0.793 | ✓ | (1.5★) Felt too long, very boring, nothing happening for most of the film. Main character was annoying and someone I just couldn't root for. This movie is basically ha… |

**[negativas] Mensagem superficial e repetitiva** — eixo `critica_social`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.841 | ✓ | (1.5★) Les 5 premières minutes on se dit wow ça va être quelque chose puis au bout de 15 on se dit ah ouais ok ça va être quelque chose de sacrément long. Les gros pla… |
| 2 | +0.021 | 0.790 | ✓ | (2.0★) The Substance has some genuinely interesting things to say about the way women are treated and seen in everyday life, but everything else felt so overdone to me… |
| 3 | +0.019 | 0.851 | ✓ | (2.0★) importante a lição de moral e tal sobre não se cobrar pela opinião da sociedade se você é bonita ou não ou velha ou não mas um dos piores filmes que já vi, nada… |
| 4 | +0.019 | 0.815 | ✓ | (2.0★) gereksiz uzatmışlar bir yerden sonra fena sıktı en sonda kadın fil adama benzediği için puan kırdım güncel puan iki maalesef güzellik algısı insanı buralara kad… |
| 5 | +0.018 | 0.791 | ✓ | (1.0★) A level of unsubtley prokaryote bacteria could understand. Insultingly stupid writing and editing yet not interesting enough to convincingly describe itself as … |

**[negativas] Final decepcionante** — eixo `roteiro_estrutura`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.040 | 0.807 | ✓ | (1.0★) Interesting concept and mostly entertaining throughout but the ending is so idiotic it completely ruins the entire film, zero respect for the director/screenwri… |
| 2 | +0.035 | 0.830 | ✓ | (1.5★) Cometí el gran error de verla comiendo, no lo hagan. La trama está buena pero merecía un mejor final, con las últimas escenas solo se vuelve una película palome… |
| 3 | +0.035 | 0.831 | ✓ | (1.0★) WTF, WTF, WTF Ver esta peli en Cannes ha sido una experiencia cinematográfica que no voy a olvidar nunca. Una fucking locura. Es una película que amas u odias. … |
| 4 | +0.034 | 0.825 | ✓ | (1.0★) I hate that. This movie has no final plot, or even if you call thin end the plot, it doesn’t have any sense at all. Everything is totally random and unnecessary… |
| 5 | +0.033 | 0.799 | ✓ | (2.0★) Huh? The special effects were amazing because they actually did gross me out but honestly speaking this was a pretty stupid kinda movie like there was alot of l… |

**[negativas] Duração excessiva e ritmo lento** — eixo `ritmo`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.029 | 0.801 | ✓ | (1.5★) Felt too long, very boring, nothing happening for most of the film. Main character was annoying and someone I just couldn't root for. This movie is basically ha… |
| 2 | +0.020 | 0.786 | ✓ | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |
| 3 | +0.019 | 0.806 | ✓ | (2.0★) You get the point in the first 20 mins max and it just keeps saying the same thing for way too long when it could elaborate or delve further into it and it just… |
| 4 | +0.017 | 0.808 |  | (1.0★) I hate that. This movie has no final plot, or even if you call thin end the plot, it doesn’t have any sense at all. Everything is totally random and unnecessary… |
| 5 | +0.017 | 0.785 |  | (2.0★) The Substance has some genuinely interesting things to say about the way women are treated and seen in everyday life, but everything else felt so overdone to me… |

**[medianas] Final exagerado e decepcionante** — eixo `roteiro_estrutura`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.043 | 0.848 | ✓ | (3.0★) me gusta la crítica social que hace, pero el final ya me parece excesivo, entiendo que en general ese es el punto que todo sea "extra" pero es que me parece que… |
| 2 | +0.034 | 0.821 | ✓ | (3.0★) Filmin ilk bir saatinde yakın planda çekilmiş sahnelerle çıplaklık sahneleri benim için rahatsız ediciydi. Hikâye uzun süre aynı rutinde döndü durdu. İkinci yar… |
| 3 | +0.033 | 0.842 | ✓ | (2.5★) ça montre bien la peur de vieillir pour une actrice d’hollywood ou juste « l’addiction» qu’on a à tout faire pour se plaire physiquement. j’me suis imaginé 1mil… |
| 4 | +0.032 | 0.834 | ✓ | (2.5★) at times infuriatingly incompetent and edited as if the audience is an 8 month old with no object permanence, interspersed with the best practical effects and s… |
| 5 | +0.030 | 0.840 |  | (2.5★) Se me ha hecho un poco pesada hasta que en la segunda mitad manda todo a la mierda y se marca un tributo a las pelis de serie Z. Desde luego prefiero eso a esce… |

**[medianas] Crítica social e mensagem relevante** — eixo `critica_social`, declarado 14/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.011 | 0.812 | ✓ | (3.0★) Un horror "asqueroso" pero vale la pena. Una satira totalmente impredecible, con dos personajes que hicieron un gran trabajo. No se me hizo aburrida, y refleja … |
| 2 | +0.009 | 0.812 | ✓ | (3.0★) To put things briefly, The Substance is a relatively sound film, although, it still comes with a fair share of issues. As films of this more thematic nature, an… |
| 3 | +0.008 | 0.783 | ✓ | (3.0★) I think it was a cool commentary how women destroy themselves from the inside to stay relevant but idk how well it was executed well. Super cool concept. Great … |
| 4 | +0.007 | 0.783 | ✓ | (3.0★) Most bearable margaret qualley performance imo and love french people hating Americans with the subtlety of Americans hating the French. A Patricia Piccinini sc… |
| 5 | +0.007 | 0.812 | ✓ | (3.0★) me gusta la crítica social que hace, pero el final ya me parece excesivo, entiendo que en general ese es el punto que todo sea "extra" pero es que me parece que… |

**[medianas] Atuações e elenco elogiados** — eixo `atuacao`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.006 | 0.793 | ✓ | (3.0★) I've rarely felt so distant from the rest of the audience, honestly quite an incomprehensible sensation. I felt this movie as an (interesting) dramatic approach… |
| 2 | -0.001 | 0.775 | ✓ | (3.0★) Most bearable margaret qualley performance imo and love french people hating Americans with the subtlety of Americans hating the French. A Patricia Piccinini sc… |
| 3 | -0.001 | 0.799 | ✓ | (3.0★) Un horror "asqueroso" pero vale la pena. Una satira totalmente impredecible, con dos personajes que hicieron un gran trabajo. No se me hizo aburrida, y refleja … |
| 4 | -0.001 | 0.803 |  | (2.5★) od połowy to ja nie wiem co za kongo tu sie odpierdala..... To chyba znak ze jeżeli kiedykolwiek takie coś by było to nigdy bym nie użyła i trzeba kochać ciało … |
| 5 | -0.003 | 0.769 |  | (3.0★) Love It that it's not a potion, some magic or a curse that does the trick. It's not even a machine. It's an Amazon-like minimalistic assembly yourself kit that … |

**[medianas] Efeitos práticos e direção de arte** — eixo `direcao_imagem`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.798 | ✓ | (3.0★) Dug it. Great practical effects and camp. Feels like it’ll be a timeless rewatch. Very consistent though and through. The superficial LA aesthetic is so good he… |
| 2 | +0.013 | 0.815 | ✓ | (2.5★) at times infuriatingly incompetent and edited as if the audience is an 8 month old with no object permanence, interspersed with the best practical effects and s… |
| 3 | +0.011 | 0.775 | ✓ | (3.0★) Australian Premiere: Sydney Film Festival 2024 Closing Night Gala “There is no she. You are one. Remember that.” This visually stunning horror film blends body … |
| 4 | +0.010 | 0.797 | ✓ | (3.0★) I've rarely felt so distant from the rest of the audience, honestly quite an incomprehensible sensation. I felt this movie as an (interesting) dramatic approach… |
| 5 | +0.009 | 0.802 | ✓ | (3.0★) "remember there's no she and you, you're one person." i quite liked this, very beautiful cinematography, design, acting, editing- very nice body horror too. mad… |

**[medianas] Ritmo irregular e repetição** — eixo `ritmo`, declarado 9/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.806 | ✓ | (3.0★) SFF2024 #7 (Closing Night Film) Spends a surprising amount of its third act riffing on extremely specific images from a not very well-regarded Doctor Who episod… |
| 2 | +0.021 | 0.808 | ✓ | (3.0★) Filmin ilk bir saatinde yakın planda çekilmiş sahnelerle çıplaklık sahneleri benim için rahatsız ediciydi. Hikâye uzun süre aynı rutinde döndü durdu. İkinci yar… |
| 3 | +0.021 | 0.798 | ✓ | (2.5★) Oohhhhh ok this is camp, no one told me! I thought it was cool. 20 minutes too long. Upset my whole party but I blame their media literacy and lack of connectio… |
| 4 | +0.017 | 0.838 |  | (3.0★) edit: j’attends de le revoir parce que ma note de cannes est hardcore mdr — c’est une prouesse technique, de jeu, d’invention et de mise en scène, mais je pense… |
| 5 | +0.016 | 0.823 | ✓ | (3.0★) Un peu tiraillée pour le coup, il y a beaucoup de choses que j'ai aimé mais aussi beaucoup de points qui m'ont dérangé Dans le positif, j'applaudis le cast que … |

**[medianas] Body horror extremo e desconforto** — eixo `tom_atmosfera`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.046 | 0.831 | ✓ | (3.0★) Horrifying, stylish and clearly true to its intentions, The Substance is probably not for most, but you can’t deny it does what it does well. Unapologetically o… |
| 2 | +0.044 | 0.839 | ✓ | (3.0★) Fuerte. Película muy bien hecha, pero tenés que ser fuerte para verla. Básicamente: body horror. No es recomendada para cualquiera que sea sensible a este tipo … |
| 3 | +0.031 | 0.825 | ✓ | (3.0★) "remember there's no she and you, you're one person." i quite liked this, very beautiful cinematography, design, acting, editing- very nice body horror too. mad… |
| 4 | +0.027 | 0.810 | ✓ | (3.0★) SFF2024 #7 (Closing Night Film) Spends a surprising amount of its third act riffing on extremely specific images from a not very well-regarded Doctor Who episod… |
| 5 | +0.026 | 0.801 |  | (3.0★) A very disturbing movie, but I like very disturbing movies. Definitely a really cool and original concept, so that was nice to see. This movie pretty much sums … |

**[positivas] Metáfora da autodestruição e padrões de beleza** — eixo `critica_social`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.051 | 0.827 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 2 | +0.045 | 0.848 | ✓ | (4.0★) La película te deja un mensaje, esta película tiene muchísimas metáforas hacia dismorfia corporal, el odio a uno mismo y la adición, de como los comentarios de … |
| 3 | +0.044 | 0.838 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 4 | +0.038 | 0.804 | ✓ | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 5 | +0.031 | 0.794 |  | (5.0★) This movie was great freaky and weird af. Great storyline and really sucks you in like dang what would I do???? Would my young self kill my old self??? Costumes… |

**[positivas] Atuações de Demi Moore e Margaret Qualley** — eixo `atuacao`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.054 | 0.831 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 2 | +0.045 | 0.831 | ✓ | (4.5★) at the end of the day she’s just a girl. hella gore tho like some of that was unnecessary but demi moore played tf out of that character my god. oh and margaret… |
| 3 | +0.038 | 0.804 | ✓ | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 4 | +0.035 | 0.798 | ✓ | (5.0★) This movie was great freaky and weird af. Great storyline and really sucks you in like dang what would I do???? Would my young self kill my old self??? Costumes… |
| 5 | +0.031 | 0.812 | ✓ | (4.0★) honestly loved how everything is shoved into your face via visual presentation and cues. some might criticize how this film exaggerates the message, slapping it… |

**[positivas] Direção e estilo visual marcantes** — eixo `direcao_imagem`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.035 | 0.805 |  | (4.0★) This film is gonna be a huge divider. All I know is: I won't forget that screening in a hurry. Every Cannes has one: a love it or hate it title that becomes a w… |
| 2 | +0.033 | 0.806 | ✓ | (4.0★) Whoa!! This is awesome. Totally insane body horror of the highest order. Filled with the most gratuitously sexual shots of female bodies AND also the most disgu… |
| 3 | +0.016 | 0.782 |  | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 4 | +0.015 | 0.790 | ✓ | (4.5★) holy shit this was so peak the concept was perfect ending was aight i loved the directing and cinematography such a well made movie i was so engaged great time … |
| 5 | +0.011 | 0.791 | ✓ | (4.0★) utterly disgusting but done in the most beautiful way possible. probably one of the best body horrors of all time. really cool cinematography and set designs. t… |

**[positivas] Body horror extremo e efeitos práticos** — eixo `direcao_imagem`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.056 | 0.835 | ✓ | (4.0★) utterly disgusting but done in the most beautiful way possible. probably one of the best body horrors of all time. really cool cinematography and set designs. t… |
| 2 | +0.043 | 0.809 |  | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 3 | +0.039 | 0.815 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 4 | +0.038 | 0.811 |  | (4.5★) this was so disgusting and i loved it. the idea of the ideal version of you and the real you becoming separate, blurring so you don’t even know who you are anym… |
| 5 | +0.036 | 0.837 | ✓ | (4.0★) Aris: This movie was really....... good...? This movie was really... evocative... Totle: Oh wow, this movie was really intense. I really loved to see everything… |

**[positivas] Crítica à indústria do entretenimento e ao envelhecimento** — eixo `critica_social`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.791 | ✓ | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 2 | +0.023 | 0.817 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 3 | +0.023 | 0.817 | ✓ | (4.0★) Un film qui retrace correctement la société et ses attentes envers les femmes. Je pense que ce film fait sens pour beaucoup de femme qui ont du mal avec le temp… |
| 4 | +0.020 | 0.791 | ✓ | (4.0★) I mean I had seen the poster for the movie, but I had no idea it would be so much body horror. Def some scenes that were really hard for me to watch lol I reall… |
| 5 | +0.020 | 0.800 | ✓ | (5.0★) been reflecting a lot on womanhood, feminism, and where i see myself within society. this film is masterfully made. i’m in a different space than i was when i s… |

**[positivas] Final controverso e exagerado** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.040 | 0.848 | ✓ | (3.5★) Me encantó; pero ese final; aún admirandolo debido a que la directora hizo lo que creyó mejor y apeteció; se desvío demasiado a un derroche de body horror sin s… |
| 2 | +0.025 | 0.826 |  | (4.0★) Aris: This movie was really....... good...? This movie was really... evocative... Totle: Oh wow, this movie was really intense. I really loved to see everything… |
| 3 | +0.024 | 0.852 | ✓ | (4.0★) gebre que porra eh essa crítica muito interessante, mas que final foi esse puta que pariu esse filme ter perdido pra Anora tambem foi foda, só comprova a crític… |
| 4 | +0.022 | 0.796 | ✓ | (4.5★) this was so disgusting and i loved it. the idea of the ideal version of you and the real you becoming separate, blurring so you don’t even know who you are anym… |
| 5 | +0.022 | 0.806 | ✓ | (3.5★) margaret qualley i owe you an apology. i wasn't familiar with your game. what a strange apartment. what a strange universe. everybody only drives a mustang and … |

### local — qwen3:14b (Ollama)

**[negativas] abordagem excessiva de gore e nus** — eixo `critica_social`, declarado 18/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.030 | 0.798 | ✓ | (0.5★) Coralie Fargeat hat so gesagt „hey was ist wenn wir einen Film machen der wie Alien ist aber in noch ekliger und scheiße“ und sie hatte noch nie mehr Unrecht. N… |
| 2 | +0.028 | 0.793 | ✓ | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |
| 3 | +0.026 | 0.807 |  | (2.0★) An extreme movie that really goes all the way and beyond in terms of violence and gore which you seldomly see with a female filmmaker (Titane‘s extremity looks … |
| 4 | +0.025 | 0.834 | ✓ | (2.0★) Diría que es interesante pero la verdad que no va a ningún lado. Gore y porno suave con la intención de mandar un mensaje pero lo único que estás haciendo es ve… |
| 5 | +0.025 | 0.793 | ✓ | (2.0★) The Substance has some genuinely interesting things to say about the way women are treated and seen in everyday life, but everything else felt so overdone to me… |

**[negativas] roteiro fraco e desorganizado** — eixo `roteiro_estrutura`, declarado 14/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.014 | 0.806 |  | (1.5★) La peor película que vi en el año. La única razón por la que no le pongo un 1, es pq el trabajo artístico está 10/10, pero es grotésca sin sentido, aburrida y e… |
| 2 | +0.014 | 0.850 | ✓ | (2.0★) Vamos lá Quero começar dizendo que o filme tem uma ideia muito boa, diga se por passagem, mas que se perde muito por conta do roteiro, o roteiro parece que não … |
| 3 | +0.013 | 0.785 | ✓ | (1.5★) Felt too long, very boring, nothing happening for most of the film. Main character was annoying and someone I just couldn't root for. This movie is basically ha… |
| 4 | +0.012 | 0.803 | ✓ | (1.0★) I hate that. This movie has no final plot, or even if you call thin end the plot, it doesn’t have any sense at all. Everything is totally random and unnecessary… |
| 5 | +0.012 | 0.798 |  | (2.0★) You get the point in the first 20 mins max and it just keeps saying the same thing for way too long when it could elaborate or delve further into it and it just… |

**[negativas] excesso de repetição e previsibilidade** — eixo `roteiro_estrutura`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.016 | 0.802 |  | (2.0★) You get the point in the first 20 mins max and it just keeps saying the same thing for way too long when it could elaborate or delve further into it and it just… |
| 2 | +0.015 | 0.852 | ✓ | (2.0★) eu literalmente me forcei a terminar esse filme. eu entendo completamente a proposta e reconheço que ele tem uma crítica interessante sobre padrões de beleza, e… |
| 3 | +0.014 | 0.792 |  | (2.0★) Requiem for a dream puis La mouche puis Revenge (!) puis Éléphant Man puis Carrie puis Braindead puis Society. Forcément du coup c’est trop long… Est à peu près… |
| 4 | +0.013 | 0.787 | ✓ | (2.0★) More needles and ASMR sounds than dialogue in this movie. I found it pretty heavy-handed in it's themes, at one point explicitly stating one of the themes of th… |
| 5 | +0.012 | 0.780 |  | (0.5★) Coralie Fargeat hat so gesagt „hey was ist wenn wir einen Film machen der wie Alien ist aber in noch ekliger und scheiße“ und sie hatte noch nie mehr Unrecht. N… |

**[negativas] exposição de temas sensíveis de forma inadequada** — eixo `critica_social`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.027 | 0.796 | ✓ | (2.0★) The Substance has some genuinely interesting things to say about the way women are treated and seen in everyday life, but everything else felt so overdone to me… |
| 2 | +0.027 | 0.807 | ✓ | (2.0★) Me when I built a secret room in my bathroom that doesn't have a handle, so how the hell do you shut that shit? --I understand what they were trying to do. Movi… |
| 3 | +0.026 | 0.791 | ✓ | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |
| 4 | +0.024 | 0.808 | ✓ | (1.0★) Lancer un concept tout simple et développer presque rien. Chez Cronenberg, on voit tjs l'ouverture et la créativité dans n’importe quelle condition cruelle. Mai… |
| 5 | +0.024 | 0.837 | ✓ | (2.0★) Entiendo perfectamente la crítica que genera está película sobre la industria de la actuación pero para mí gusto es innecesario usar todas escenas explícitas qu… |

**[negativas] longa duração e ritmo lento** — eixo `ritmo`, declarado 7/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.797 | ✓ | (1.5★) Felt too long, very boring, nothing happening for most of the film. Main character was annoying and someone I just couldn't root for. This movie is basically ha… |
| 2 | +0.018 | 0.793 | ✓ | (0.5★) تحملت اول ساعة من الفيلم بالعافية .. الشيء الوحيد الي خلاني اكمل بسكبات للنهاية هو الفضول المحض اني اشوف وين بيوصل هالقرف . تجربة تجيب الغثيان وبس .. المحزن بال… |
| 3 | +0.016 | 0.799 |  | (1.0★) Lancer un concept tout simple et développer presque rien. Chez Cronenberg, on voit tjs l'ouverture et la créativité dans n’importe quelle condition cruelle. Mai… |
| 4 | +0.015 | 0.806 |  | (1.0★) I hate that. This movie has no final plot, or even if you call thin end the plot, it doesn’t have any sense at all. Everything is totally random and unnecessary… |
| 5 | +0.015 | 0.852 |  | (2.0★) Vamos lá Quero começar dizendo que o filme tem uma ideia muito boa, diga se por passagem, mas que se perde muito por conta do roteiro, o roteiro parece que não … |

**[negativas] falta de originalidade e influências evidentes** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.025 | 0.797 | ✓ | (1.5★) Felt too long, very boring, nothing happening for most of the film. Main character was annoying and someone I just couldn't root for. This movie is basically ha… |
| 2 | +0.021 | 0.802 | ✓ | (2.0★) An extreme movie that really goes all the way and beyond in terms of violence and gore which you seldomly see with a female filmmaker (Titane‘s extremity looks … |
| 3 | +0.020 | 0.828 | ✓ | (2.0★) Diría que es interesante pero la verdad que no va a ningún lado. Gore y porno suave con la intención de mandar un mensaje pero lo único que estás haciendo es ve… |
| 4 | +0.019 | 0.799 |  | (2.0★) Me when I built a secret room in my bathroom that doesn't have a handle, so how the hell do you shut that shit? --I understand what they were trying to do. Movi… |
| 5 | +0.019 | 0.784 | ✓ | (0.5★) Genuinely one of the worst movies I have ever seen. This movie took an insanely cool concept, built a god awful story around it, and then devolved the entire fi… |

**[medianas] horror corporal e estética grotesca** — eixo `direcao_imagem`, declarado 20/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.032 | 0.827 |  | (3.0★) Fuerte. Película muy bien hecha, pero tenés que ser fuerte para verla. Básicamente: body horror. No es recomendada para cualquiera que sea sensible a este tipo … |
| 2 | +0.029 | 0.814 | ✓ | (3.0★) Horrifying, stylish and clearly true to its intentions, The Substance is probably not for most, but you can’t deny it does what it does well. Unapologetically o… |
| 3 | +0.025 | 0.788 | ✓ | (3.0★) Australian Premiere: Sydney Film Festival 2024 Closing Night Gala “There is no she. You are one. Remember that.” This visually stunning horror film blends body … |
| 4 | +0.023 | 0.806 | ✓ | (3.0★) 5 stars for the cinematic experience that came with this movie. Without an audience I would have turned this off at the first transitioning scene. Filled with g… |
| 5 | +0.021 | 0.804 | ✓ | (3.0★) SFF2024 #7 (Closing Night Film) Spends a surprising amount of its third act riffing on extremely specific images from a not very well-regarded Doctor Who episod… |

**[medianas] crítica à beleza e ao envelhecimento feminino** — eixo `critica_social`, declarado 12/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.022 | 0.798 | ✓ | (3.0★) Most bearable margaret qualley performance imo and love french people hating Americans with the subtlety of Americans hating the French. A Patricia Piccinini sc… |
| 2 | +0.018 | 0.822 |  | (2.5★) od połowy to ja nie wiem co za kongo tu sie odpierdala..... To chyba znak ze jeżeli kiedykolwiek takie coś by było to nigdy bym nie użyła i trzeba kochać ciało … |
| 3 | +0.016 | 0.780 | ✓ | (3.0★) This is one CREEPY movie. However, the lesson the director (Caroline Fargeat) is trying to show is actually real and many people struggle accepting their own id… |
| 4 | +0.015 | 0.798 | ✓ | (3.0★) SFF2024 #7 (Closing Night Film) Spends a surprising amount of its third act riffing on extremely specific images from a not very well-regarded Doctor Who episod… |
| 5 | +0.014 | 0.811 |  | (2.5★) —“ CONTROL YOURSELF! ” Now that my head cleared up after the panic attack I had, I can finally talk about it. The ending is so dragged. It’s so unnecessary long… |

**[medianas] narrativa repetitiva e excessiva** — eixo `roteiro_estrutura`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.806 | ✓ | (2.5★) Demi Moore es buenísima, buenísima, lamentablemente la película es mala; o más que mala se cae en el segundo acto y el tercero solo tira por la borda la sutilez… |
| 2 | +0.018 | 0.823 | ✓ | (3.0★) me gusta la crítica social que hace, pero el final ya me parece excesivo, entiendo que en general ese es el punto que todo sea "extra" pero es que me parece que… |
| 3 | +0.018 | 0.781 | ✓ | (3.0★) Australian Premiere: Sydney Film Festival 2024 Closing Night Gala “There is no she. You are one. Remember that.” This visually stunning horror film blends body … |
| 4 | +0.017 | 0.807 |  | (3.0★) Nuts. Starts off as a satire on aging and self-loathing, and then goes to places you cannot imagine, but they are befitting the director of the bloodsoaked Reve… |
| 5 | +0.016 | 0.794 | ✓ | (3.0★) very theatrical? i enjoyed it a lot but it's definitely not a movie where you can try and use logic to explain the reactions or actions of people in it. big fat… |

**[medianas] atuações e direção** — eixo `atuacao`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.042 | 0.827 | ✓ | (2.5★) Demi Moore es buenísima, buenísima, lamentablemente la película es mala; o más que mala se cae en el segundo acto y el tercero solo tira por la borda la sutilez… |
| 2 | +0.042 | 0.829 | ✓ | (3.0★) I've rarely felt so distant from the rest of the audience, honestly quite an incomprehensible sensation. I felt this movie as an (interesting) dramatic approach… |
| 3 | +0.030 | 0.814 | ✓ | (3.0★) SFF2024 #7 (Closing Night Film) Spends a surprising amount of its third act riffing on extremely specific images from a not very well-regarded Doctor Who episod… |
| 4 | +0.025 | 0.815 | ✓ | (3.0★) Nuts. Starts off as a satire on aging and self-loathing, and then goes to places you cannot imagine, but they are befitting the director of the bloodsoaked Reve… |
| 5 | +0.011 | 0.787 | ✓ | (3.0★) I think it was a cool commentary how women destroy themselves from the inside to stay relevant but idk how well it was executed well. Super cool concept. Great … |

**[medianas] comentários sobre o final do filme** — eixo `roteiro_estrutura`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.033 | 0.839 | ✓ | (3.0★) me gusta la crítica social que hace, pero el final ya me parece excesivo, entiendo que en general ese es el punto que todo sea "extra" pero es que me parece que… |
| 2 | +0.030 | 0.805 | ✓ | (3.0★) I think it was a cool commentary how women destroy themselves from the inside to stay relevant but idk how well it was executed well. Super cool concept. Great … |
| 3 | +0.026 | 0.836 | ✓ | (2.5★) ça montre bien la peur de vieillir pour une actrice d’hollywood ou juste « l’addiction» qu’on a à tout faire pour se plaire physiquement. j’me suis imaginé 1mil… |
| 4 | +0.024 | 0.802 | ✓ | (3.0★) very theatrical? i enjoyed it a lot but it's definitely not a movie where you can try and use logic to explain the reactions or actions of people in it. big fat… |
| 5 | +0.023 | 0.810 | ✓ | (3.0★) Filmin ilk bir saatinde yakın planda çekilmiş sahnelerle çıplaklık sahneleri benim için rahatsız ediciydi. Hikâye uzun süre aynı rutinde döndü durdu. İkinci yar… |

**[medianas] referências culturais e influências cinematográficas** — eixo `comparacoes`, declarado 4/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.019 | 0.782 | ✓ | (3.0★) Australian Premiere: Sydney Film Festival 2024 Closing Night Gala “There is no she. You are one. Remember that.” This visually stunning horror film blends body … |
| 2 | +0.013 | 0.800 | ✓ | (3.0★) I've rarely felt so distant from the rest of the audience, honestly quite an incomprehensible sensation. I felt this movie as an (interesting) dramatic approach… |
| 3 | +0.011 | 0.801 | ✓ | (3.0★) La serie Z que rezuma. Sobre pinchazos y borbotones. Ya lo escribió Baruch Spinoza en su momento: nadie sabe lo que puede un cuerpo. Transcurrida una hora, me p… |
| 4 | +0.011 | 0.817 |  | (3.0★) Un peu tiraillée pour le coup, il y a beaucoup de choses que j'ai aimé mais aussi beaucoup de points qui m'ont dérangé Dans le positif, j'applaudis le cast que … |
| 5 | +0.010 | 0.800 | ✓ | (3.0★) Nuts. Starts off as a satire on aging and self-loathing, and then goes to places you cannot imagine, but they are befitting the director of the bloodsoaked Reve… |

**[positivas] representação do corpo e a pressão por juventude** — eixo `critica_social`, declarado 20/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.033 | 0.799 | ✓ | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 2 | +0.029 | 0.805 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 3 | +0.027 | 0.821 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 4 | +0.022 | 0.794 |  | (4.0★) Whoa!! This is awesome. Totally insane body horror of the highest order. Filled with the most gratuitously sexual shots of female bodies AND also the most disgu… |
| 5 | +0.021 | 0.814 | ✓ | (4.5★) Writing this review at midnight so… I tried following along with Pump It Up as I watched it and dislocated my leg, this is ridiculous, I want a refund. 0/10. A … |

**[positivas] horror corporal e efeitos visuais extremos** — eixo `direcao_imagem`, declarado 15/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.038 | 0.818 | ✓ | (4.0★) utterly disgusting but done in the most beautiful way possible. probably one of the best body horrors of all time. really cool cinematography and set designs. t… |
| 2 | +0.031 | 0.807 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 3 | +0.030 | 0.796 |  | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 4 | +0.029 | 0.789 |  | (5.0★) nothing says “it feels so scary getting old” like watching your younger self crawl out of your body and slowly turn you into something unrecognizable. so fuckin… |
| 5 | +0.029 | 0.791 | ✓ | (5.0★) This movie was great freaky and weird af. Great storyline and really sucks you in like dang what would I do???? Would my young self kill my old self??? Costumes… |

**[positivas] crítica ao patriarcado e estereótipos de beleza** — eixo `critica_social`, declarado 10/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.037 | 0.814 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 2 | +0.032 | 0.797 | ✓ | (4.5★) Body horror goes crazyyyy! This movie does a great job representing the horrors of being a woman in Hollywood. The misogynistic urge to devalue a woman who ages… |
| 3 | +0.031 | 0.825 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 4 | +0.025 | 0.805 | ✓ | (5.0★) been reflecting a lot on womanhood, feminism, and where i see myself within society. this film is masterfully made. i’m in a different space than i was when i s… |
| 5 | +0.023 | 0.816 | ✓ | (4.5★) Writing this review at midnight so… I tried following along with Pump It Up as I watched it and dislocated my leg, this is ridiculous, I want a refund. 0/10. A … |

**[positivas] dualidade entre personagens e identidade** — eixo `roteiro_estrutura`, declarado 8/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.021 | 0.797 |  | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 2 | +0.014 | 0.807 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 3 | +0.013 | 0.799 |  | (4.5★) at the end of the day she’s just a girl. hella gore tho like some of that was unnecessary but demi moore played tf out of that character my god. oh and margaret… |
| 4 | +0.012 | 0.782 |  | (4.0★) This film is gonna be a huge divider. All I know is: I won't forget that screening in a hurry. Every Cannes has one: a love it or hate it title that becomes a w… |
| 5 | +0.011 | 0.774 | ✓ | (5.0★) This movie was great freaky and weird af. Great storyline and really sucks you in like dang what would I do???? Would my young self kill my old self??? Costumes… |

**[positivas] uso de metáforas e simbolismo** — eixo `roteiro_estrutura`, declarado 6/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.023 | 0.800 |  | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 2 | +0.015 | 0.809 | ✓ | (5.0★) ahhh, yes, the awfulness and sacrifice of being pretty in an industry that can just replace you whenever they want, and put it on a concept that's absolutely ho… |
| 3 | +0.012 | 0.815 | ✓ | (4.0★) La película te deja un mensaje, esta película tiene muchísimas metáforas hacia dismorfia corporal, el odio a uno mismo y la adición, de como los comentarios de … |
| 4 | +0.009 | 0.814 |  | (3.5★) Ohhhh red lovers would like this movie yeah everything started out normal and what the heck just happened? what and yeah pump it out I guess? I clearly understa… |
| 5 | +0.007 | 0.791 | ✓ | (3.5★) margaret qualley i owe you an apology. i wasn't familiar with your game. what a strange apartment. what a strange universe. everybody only drives a mustang and … |

**[positivas] desempenho dos atores e direção** — eixo `atuacao`, declarado 5/40

| # | score | sim | eixo | review |
|---|---|---|---|---|
| 1 | +0.013 | 0.793 | ✓ | (4.0★) honestly loved how everything is shoved into your face via visual presentation and cues. some might criticize how this film exaggerates the message, slapping it… |
| 2 | +0.011 | 0.787 | ✓ | (5.0★) a metaphor of the self destructive nature of self hatred that is enforced by patriarchal societal norms wrapped up in a perfect body horror package with breatht… |
| 3 | +0.008 | 0.802 | ✓ | (4.0★) Un film qui retrace correctement la société et ses attentes envers les femmes. Je pense que ce film fait sens pour beaucoup de femme qui ont du mal avec le temp… |
| 4 | +0.007 | 0.794 | ✓ | (4.5★) at the end of the day she’s just a girl. hella gore tho like some of that was unnecessary but demi moore played tf out of that character my god. oh and margaret… |
| 5 | +0.005 | 0.797 |  | (4.0★) went in blind, pleasantly surprised the haunting depths a person can go may it be a part of the entertainment industry or a person part of the norm just to atta… |
