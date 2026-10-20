# Validação do juiz v2 — versão congelada v2.2

Configuração `44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669` · 40 pares NOVOS (nenhum da calibração) · rótulo do dono · selo do mapa `5fad9a3000cb45c0…`

**O JUIZ PASSOU** no critério pré-registrado — precisão ≥ 0.8, recall ≥ 0.8, diferença de precisão entre os lados ≤ 0.15 (medida: 0.011).

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |
|---|---|---|---|---|---|---|---|
| todos | 40 | 23 | 4 | 2 | 11 | 0.852 [0.675, 0.941] | 0.92 [0.75, 0.978] |
| publicado | 20 | 12 | 2 | 1 | 5 | 0.857 [0.601, 0.96] | 0.923 [0.667, 0.986] |
| local | 20 | 11 | 2 | 1 | 6 | 0.846 [0.578, 0.957] | 0.917 [0.646, 0.985] |

## Erros

### P05 — local, mother-2017/negativas

- tema: "excesso de metáforas e simbolismo"
- dono não · juiz sim (motivo: —)
- trecho: "Entendo a alegoria, os símbolos bíblicos e tudo mais, mas nossa… Não. Simplesmente não dá pra mim."
- raciocínio: "We need to check if review supports bullet \"excesso de metáforas e simbolismo\". Review says: \"Entendo a alegoria, os símbolos bíblicos e tudo mais, mas nossa… Não. Simplesmente não dá pra mim.\" This indicates too much allegory, symbols, etc. So yes supports. Evidência clara? The sentence clearly expresses that. So true. Provide snippet."

### P09 — publicado, mother-2017/negativas

- tema: "Experiência insuportável e desconfortável"
- dono sim · juiz não (motivo: trecho não encontrado na review)
- trecho: "I was miserable, I didn’t feel scared."
- raciocínio: "Need to decide if review supports \"Experiência insuportável e desconfortável\". The review indeed says it was miserable, uncomfortable, irritated, etc. So yes supports. Provide snippet. Choose a sentence that clearly expresses that. For example: \"I was miserable.\" Or \"I felt increasingly irritated at a man who couldn’t respect his wife’s privacy...\". Need full sentence from review. We'll pick: \"I was miserable.\" But that's short (<4 words? It's 2 words). Need at least 4 words. Choose: \"I was miserable.\" still 2. Maybe: \"I was miserable.\" Not enough. Use longer sentence: \"I was miserable.\" No. A"

### P14 — local, napoleon-2023/negativas

- tema: "Falta de ação e ritmo lento"
- dono não · juiz sim (motivo: —)
- trecho: "las batallas son Hollywood goyslop sin cohesión y careciendo de las tácticas que le hicieron tan buen general."
- raciocínio: "We need to check if review supports bullet \"Falta de ação e ritmo lento\" (lack of action and slow pace). Review says: \"las batallas son Hollywood goyslop sin cohesión y careciendo de las tácticas...\" and \"las fechas estan mal puestas\". It criticizes action and cohesion. So supports lack of action and slow pace? Yes, it says lack of cohesive action. So supports. Provide trecho literal: the sentence: \"las batallas son Hollywood goyslop sin cohesión y careciendo de las tácticas que le hicieron tan buen general.\" That's >4 words. So evidence clear. So JSON."

### P20 — publicado, mother-2017/negativas

- tema: "Alta carga alegórica e excesso de simbolismo"
- dono não · juiz sim (motivo: —)
- trecho: "Entendo a alegoria, os símbolos bíblicos e tudo mais, mas nossa… Não. Simplesmente não dá pra mim."
- raciocínio: "We need to check if review supports bullet \"Alta carga alegórica e excesso de simbolismo\". Review says: \"Entendo a alegoria, os símbolos bíblicos e tudo mais, mas nossa… Não. Simplesmente não dá pra mim.\" She acknowledges allegory but says can't handle. It supports idea of high allegory? She says \"Entendo a alegoria, os símbolos bíblicos e tudo mais\" meaning acknowledges but maybe too much? It supports the idea that there is allegory/symbolism, but maybe not necessarily \"excess\"? She says \"Não. Simplesmente não dá pra mim.\" indicates she can't handle it. That supports the idea of high allegory"

### P32 — publicado, napoleon-2023/negativas

- tema: "Batalhas decepcionantes"
- dono não · juiz sim (motivo: —)
- trecho: "Dissapointed. So many great battles could have been included."
- raciocínio: "Need to see if review supports bullet \"Batalhas decepcionantes\" (disappointing battles). Review says disappointed, so many great battles could have been included, so it's disappointed with battles. That supports. It's explicit. So apoia_ideia_principal true. Evidencia clara true. Provide trecho. Use full sentence? The relevant sentence: \"Dissapointed. So many great battles could have been included.\" We need full sentence including start. The exact phrase from review: \"Dissapointed. So many great battles could have been included.\" That's two sentences. The instruction: copy the phrase entire wh"

### P40 — local, mother-2017/negativas

- tema: "trabalho do diretor e intencionalidade artística"
- dono sim · juiz não (motivo: modelo disse que não apoia a ideia principal)
- trecho: null
- raciocínio: "We need to determine if the review supports the bullet \"trabalho do diretor e intencionalidade artística\". The bullet's main idea: director's work and artistic intentionality. The review says: \"el tipo de cosas que pasaban en la casa del papá de la cande película pretenciosa, busca impactar todo el rato, llena de simbolismos para ideas tan simples ... es solo una alegoría a la biblia completamente rebuscada.\" It's criticizing pretentiousness, over-symbolism, over-interpretation, implying lack of clear intentionality? It says it's pretentious, over-symbolic, a rebusculated biblical allegory. Th"

