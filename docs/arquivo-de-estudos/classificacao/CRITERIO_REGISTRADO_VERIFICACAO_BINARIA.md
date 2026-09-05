# CRITÉRIO REGISTRADO — verificação binária por (review, tema)

**Escrito ANTES de qualquer chamada de LLM desta sessão.** Nenhum resultado da
amostra foi visto. Data: 2026-08-29. `taxonomia_id` em vigor: `ebab2667de74`
(conferido). Modelo: `deepseek-v4-flash`, o mesmo de
`MODELO_POR_ESTAGIO["classificacao"]`.

---

## 0. População de teste — o que mudou em relação à sessão anterior

A sessão anterior usou `resultado/votacao-3/amostra.json` como "a população que
a síntese veria". **Ela não é.** A reconstrução determinística da seleção a
partir do bruto em disco (`selecao.selecionar()` com os parâmetros de produção)
reproduz, em **105 de 105 buckets**, o campo `buckets[].n_validas` do JSON
publicado, e reproduz, em **93 de 93 buckets que têm o campo**, o
`eixos.fonte_classificacao.por_bucket[].sobreposicao_com_analisadas`. O
`amostra.json` sobrepõe essa população em apenas **67,6%** dos ids.

**Consequência registrada antes de rodar:** esta sessão testa cada bullet
contra as reviews que a síntese daquele bullet **de fato leu**, reconstruídas do
bruto, não contra o `amostra.json`. Isso é um pré-requisito para comparar com o
gabarito à mão, que foi levantado sobre "todas as reviews da seleção de
produção daquele bucket".

---

## 1. Unidade e schema da chamada

**Unidade de decisão: o par (review, tema).** Uma chamada por par. A review
inteira entra; o tema entra como uma frase.

**Sobre o que a pergunta é feita: o TEMA, não o exemplo.** `mencoes_aproximadas`
é declarado por tema e a barra do frontend é por tema
([filme.js:1370](frontend/js/filme.js:1370)); o `exemplo_parafraseado` entra no
prompt como **desambiguação** do tema, não como texto a ser casado palavra por
palavra. Isso está registrado aqui porque o gabarito à mão dos 5 casos **mistura
os dois níveis** (ver §4) e a leitura do resultado depende de qual nível foi
perguntado.

**Schema de saída** (JSON mode, objeto único):

```json
{"frase": "<trecho literal da review, ou string vazia>",
 "tocou_assunto": true,
 "veredito": "sustenta"}
```

Ordem dos campos é deliberada e segue o padrão do verificador `V2_alvo` que
funcionou (§2.5 da SPEC): **o compromisso com a evidência vem antes do
veredito**, para fechar o atalho de decidir primeiro e justificar depois.

- `frase` — trecho **literal** da review em que a decisão se apoia. String
  vazia quando a review não toca o assunto.
- `tocou_assunto` — booleano **diagnóstico**, não decisório: a review fala do
  assunto do tema (ainda que sem afirmar o que o tema afirma)?
- `veredito` — enum de **três** valores.

## 2. Os três valores, e a regra de abstenção

O enum de decisão tem exatamente três valores, como o briefing pede. O caso
"toca de leve" **não** ganha um quarto valor: ele é resolvido por regra
explícita no prompt e fica registrado no campo diagnóstico `tocou_assunto`.
Motivo: o enum é a decisão difícil, e alargá-lo de três para quatro é
exatamente o movimento — mais decisões numa chamada só — que a Entrega 1 da
sessão anterior mostrou ser a causa da perda de resolução.

| valor | quando |
|---|---|
| `sustenta` | a review **afirma** o que o tema afirma. Precisa de uma frase literal. |
| `nao_sustenta` | a review não afirma aquilo. Cobre dois casos, separados por `tocou_assunto`: **(a)** não fala do assunto (`tocou_assunto: false`); **(b)** fala do assunto mas não faz a afirmação do tema — menção de passagem, ressalva, assunto tratado com outro juízo (`tocou_assunto: true`). |
| `contradiz` | a review afirma o **oposto** do tema sobre o mesmo assunto. Tema diz "ritmo lento", review diz "ritmo ágil". |

**Regras de abstenção declaradas no prompt, nesta ordem de precedência:**

- **R1 — na dúvida, `nao_sustenta`.** O default assimétrico existe porque o
  erro que este passe tem de pegar é o de **inflação** (o achado `wonka`: 1
  review vira 6). Um instrumento que empata para SIM não pega inflação.
- **R2 — menção de passagem não é sustentação.** Uma cláusula subordinada que
  toca o assunto sem afirmar a tese do tema é `nao_sustenta` com
  `tocou_assunto: true`.
- **R3 — o quantificador do tema não é testado.** Se o tema diz "muitos acham
  X", a pergunta é se **esta** review afirma X, não se ela afirma que muitos
  acham. Um tema é sustentado por uma review que diz a coisa, não que diz a
  frequência da coisa.
- **R4 — assunto certo com juízo oposto é `contradiz`, não `nao_sustenta`.**
  Esta é a regra que existe para não esconder o modo de falha do `wonka` e da
  contracorrente do `cats-2019`.
- **R5 — sem frase literal, não há `sustenta`.** Se o modelo não consegue citar
  a review, a decisão é `nao_sustenta`.

**O que o passe NÃO é.** Não é substituto da síntese. A síntese continua
escolhendo **quais** 6 temas o bucket publica; este passe só conta **quantas**
reviews sustentam cada escolha já feita. Ele roda depois, sobre a saída, e é
`mencoes_aproximadas` que ele substituiria — não o bloco de temas.

## 3. Amostra — regras fixadas antes do sorteio

- **A0 — universo.** Os 629 bullets publicados nos 35 filmes, menos os **10**
  sem eixo (`livre`, sem linha em `eixos.linhas[]`) → 619. Menos os bullets dos
  **3 buckets de `obsession-2026`** (n = 5, 6 e 8 reviews; um bucket degradado
  não mede o instrumento, mede o bucket).
- **A1 — os 5 casos de gabarito entram por construção**, não por sorteio:
  `wonka`/neg, `talk-to-me-2022`/neg, `napoleon-2023`/med, `interstellar`/pos,
  `cats-2019`/neg. São **teste de sanidade obrigatório** e ficam **fora** das
  estatísticas da amostra maior, para não usar o mesmo dado duas vezes.
- **A2 — 35 bullets sorteados** do universo restante, estratificados por
  **eixo** (proporcional à distribuição dos 10 eixos entre os bullets elegíveis)
  e balanceados por **bucket** como segunda chave.
- **A3 — no máximo 2 bullets por (filme, bucket)**, para que um bucket rico não
  domine a amostra.
- **A4 — PRNG semente 24**, sorteio sobre a lista ordenada por
  `(slug, bucket, tema)`. Mesma semente das sessões anteriores.
- **A5 — cada bullet sorteado é testado contra TODAS as reviews do seu bucket**
  (mediana 40). Isso é o que dá a contagem completa e o que torna a comparação
  com `mencoes_aproximadas` justa: os dois números passam a ter o mesmo
  denominador.
- **A6 — reprodutibilidade.** Os 5 bullets do gabarito são rodados **duas
  vezes**, com o mesmo prompt e o mesmo modelo, para medir o piso de variância
  entre execuções deste instrumento. É diagnóstico declarado, não condição de
  aprovação.

**N esperado de chamadas:** ~192 (gabarito) + ~1.330 (35 bullets) + ~192
(repetição) ≈ **1.700**.

## 4. O gabarito humano, e a sua imprecisão declarada

Os 5 casos de generalização excessiva de `ESTUDO_CATALOGO_35.md` §12, com a
contagem à mão consolidada em `MEDICAO_CONTAGEM_E_AB.md`:

| filme / bucket / tema | eixo | à mão | `mencoes` | n |
|---|---|---:|---:|---:|
| `wonka` neg — *Fotografia e efeitos visuais criticados* | `direcao_imagem` | **1** | 6 | 32 |
| `talk-to-me-2022` neg — *Diálogos e tom juvenil artificiais* | `tom_atmosfera` | **2** | 5 | 40 |
| `napoleon-2023` med — *Batalhas visualmente impressionantes* | `direcao_imagem` | **13** | 15 | 40 |
| `interstellar` pos — *Fotografia e efeitos visuais deslumbrantes* | `direcao_imagem` | **8** | 11 | 40 |
| `cats-2019` neg — *Experiência de visualização desconfortável* | `impacto_emocional` | **8** | 10 | 40 |

**Imprecisão registrada antes de rodar, e é do gabarito, não do instrumento:**
o `ESTUDO_CATALOGO_35.md` conta `wonka` no nível do **exemplo** ("*2 de 32
reviews tocam visual, e uma só sustenta o exemplo*") e conta `napoleon` no nível
do **tema** ("*o tema tem suporte abundante… o quantificador do exemplo não*").
Como este passe pergunta pelo **tema** (§1), o alvo de `wonka` é ambíguo entre
**1** (exemplo) e **2** (tema). **Adoto 2 como alvo de `wonka` e reporto o
resultado contra os dois**, porque adotar 1 seria escolher o número que
favorece o instrumento novo.

**Erro absoluto médio de `mencoes_aproximadas` contra este gabarito: 3,0**
(desvios 5, 3, 2, 3, 2 com `wonka` = 1; desvios 4, 3, 2, 3, 2 → **2,8** com
`wonka` = 2).

## 5. Critérios de aprovação — fixados agora, antes de qualquer resultado

### C1 — sanidade contra o gabarito humano (obrigatório)

Sobre os 5 casos, a contagem binária (`sustenta`) tem de:

- **C1a** — erro absoluto médio **menor** que o de `mencoes_aproximadas`:
  **< 2,8** (alvo de `wonka` = 2). Reporto também contra 3,0 (alvo = 1).
- **C1b** — ficar mais perto do gabarito, ou empatar, em **pelo menos 3 dos 5**
  casos individualmente.

*Justificativa de C1b:* com n = 5, "melhor na média" pode ser carregado por um
único acerto grande num instrumento pior no resto. Exigir maioria de vitórias
individuais fecha essa porta.

### C2 — sem erro sistemático novo na amostra maior (obrigatório)

Sobre os 35 bullets sorteados, a **mediana da razão** `binário / mencoes` tem de
ficar em **[0,75 , 1,35]**.

*Justificativa, medida antes de fixar o limiar:* a calibração manual registrada
do `ESTUDO_CATALOGO_35.md` §6b — 8 bullets, sub-amostra declarada antes — achou
a razão `à mão / mencoes` com **média 1,06, mediana 1,02, intervalo
0,78–1,33**. Ou seja: o que já se sabe é que `mencoes_aproximadas` **acerta o
centro** da distribuição e erra na cauda. Um instrumento correto deve, portanto,
**concordar com `mencoes` perto da mediana** e discordar nos casos ruins. Uma
mediana de razão abaixo de 0,75 é viés sistemático para NÃO; acima de 1,35 é
viés sistemático para SIM. O limiar é o intervalo observado naquela calibração,
arredondado para fora.

### C3 — plausibilidade agregada (obrigatório)

A soma das contagens binárias por bucket, dividida por `n`, tem de ficar em
**[0,8 , 2,9]**.

*Justificativa, medida antes de fixar:* essa razão hoje, sobre os 105 buckets
publicados, é **média 1,67 · mediana 1,55 · min 0,97 · max 2,83**. Um passe que
devolva razão acima de 2,9 está dizendo que quase toda review sustenta quase
todo tema (colapso para SIM); abaixo de 0,8, que a maioria das reviews não
sustenta bullet nenhum (colapso para NÃO). Este critério pega o colapso que C2
não pegaria se ele fosse uniforme.

### C4 — o valor `contradiz` funciona (diagnóstico declarado, não reprova)

`cats-2019`/negativas tem contracorrente grande e explícita, lida à mão e citada
no estudo (*"so awful that it's funny"*, *"the most fun i've had"*, *"As a
drinking game — phenomenal"*), contra o tema *"Experiência de visualização
desconfortável"*. **Se o passe devolver 0 `contradiz` nesse bullet, o terceiro
valor é decorativo** e isso é reportado como tal — mas não reprova o desenho
sozinho, porque a contagem que C1/C2/C3 medem é a de `sustenta`.

### Veredito

**APROVA** se C1a, C1b, C2 e C3 passarem. **REPROVA** se qualquer um falhar.
Zona cinzenta: **nenhuma**. Se reprovar, reporto como reprovação e não
redesenho o teste.

---

## ADENDO — 2026-08-29, ainda com ZERO chamadas de LLM feitas

O primeiro sorteio sob A2–A4 devolveu 35 bullets concentrados em **9 filmes**,
todos no início da ordem alfabética. A causa é defeito de implementação, não de
desenho: o balanceio por bucket reordenava os candidatos por `slug` **depois**
do embaralhamento, o que anulava o PRNG. Corrigido:

- **A3b (acrescentado)** — no máximo **3 bullets por filme**, além do limite de
  2 por (filme, bucket) que A3 já impunha. Existe porque A0–A5 não continham
  nenhuma restrição de concentração por filme, e uma amostra de 35 bullets
  vinda de 9 filmes mede 9 sínteses, não 35.
- **A4b (corrigido)** — a escolha passa a ser feita **na ordem embaralhada**,
  com as restrições A3/A3b aplicadas como filtro, sem reordenação posterior.

**Nenhum critério de aprovação (C1–C4) foi tocado.** Nenhum resultado de
amostra havia sido visto quando este adendo foi escrito — a única saída
observada até aqui é a composição da própria amostra.
