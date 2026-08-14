# Régua de anotação do gabarito humano

**Fixada em:** 2026-08-13 · **Vale para:** toda anotação humana futura de
`leitura.md` e para qualquer reanotação das 100 já feitas.

Este arquivo existe porque a primeira anotação das 100 reviews ficou
internamente inconsistente num eixo, e a inconsistência só apareceu por
acaso — ao investigar falsos positivos de uma variante de prompt. Régua
escrita, aplicada igual nas duas direções, é o que impede a repetição.

O gabarito é PERMANENTE: ele valida toda variante de prompt futura. Uma
inconsistência nele não é ruído que se dilui — é viés que entra em toda
medição daqui para frente, e que penaliza sistematicamente qualquer prompt
que discorde do anotador no ponto inconsistente.

---

## `impacto_emocional` — a régua

**`impacto_emocional` exige que a review descreva o EFEITO que o filme
causou em quem assistiu (ou na plateia).**

Marque quando a review diz **o que o filme fez com quem assistiu**:

> "me fez chorar" · "dormi no meio" · "saí exausto" · "fiquei
> desconfortável" · "me deu dor de cabeça" · "pausei de tédio" · "ri alto"
> · "passei mal" · "me cagué de miedo" · "metade da sala saiu"

**NÃO marque quando a review só diz que o filme é bom ou ruim.** Veredicto
seco de aprovação ou reprovação não é `impacto_emocional` — **nem positivo
nem negativo**:

> "gostei" · "não gostei" · "é ruim" · "é ótimo" · "odiei" · "amei" ·
> "obra-prima" · "5 estrelas" · "peak cinema" · "mid" · "waste of money"

### A fronteira, em uma linha

> Se a review diz apenas que o filme **é** bom ou ruim → não marca.
> Se diz o que o filme **fez** com quem assistiu → marca.

### A simetria é obrigatória

A regra vale **igual nos dois polos**. Este é o ponto exato em que a
primeira anotação falhou: `impacto_emocional` foi marcado para veredicto
seco NEGATIVO ("não gostei", "I did not enjoy", "odiei") e deixado em
branco para veredicto seco POSITIVO ("I really liked it", "I really enjoyed
it"). Não foi decisão — foi descuido ao longo de 100 reviews.

Por que importa além da coerência: qualquer classificador que marque os
positivos é penalizado na PRECISÃO por um gabarito que só aceita os
negativos. Foi o que aconteceu com a variante `A_regra` — precisão de
`impacto_emocional` medida em 0,792 contra um gabarito que contava como
falso positivo exatamente o comportamento simétrico ao que ele premiava do
outro lado.

### Casos de fronteira, resolvidos

| caso | decisão | por quê |
|---|---|---|
| "decepcionou", "deixou a desejar", "un peu déçu" | **não marca** | decepção é veredicto contra expectativa, não efeito descrito (e `expectativa` já cobre a parte de expectativa) |
| "faltou emoção", "no emotional bonding", "prevented dread from forming" | **não marca** | descreve o que o FILME não entrega, não o que aconteceu com quem assistiu |
| "hearts are broken", "a angústia anda lado a lado nesse filme" | **não marca** | descreve o conteúdo ou o tom da obra — isso é `roteiro_estrutura` ou `tom_atmosfera` |
| "me fez pensar", "fica na sua cabeça", "made me wanna read X" | **marca** | efeito cognitivo declarado sobre quem assistiu conta como efeito |
| "dá sono", "é chato de acompanhar", "me entediei" | **marca** | tédio experimentado é efeito (distinto de "o filme é lento", que é `ritmo`) |
| "a plateia saiu no meio", "gente chorando junto" | **marca** | a definição do eixo inclui explicitamente reação de PLATEIA |
| "nightmare fuel", "cringe" | **caso a caso** | se descreve o que causou em quem assistiu, marca; se qualifica a cena, não |
| review em língua que o anotador não domina | **anotar mesmo assim, e registrar a dúvida** | pular enviesa o gabarito para as línguas que o anotador lê |

### Casos de fronteira difíceis — a rodada de 11 (2026-08-14)

A correção do gabarito levantou 28 casos que não cabiam nas linhas acima.
17 foram resolvidos por analogia direta às linhas existentes. Os 11 abaixo
são os que exigiram a régua entrar em detalhe novo — o registro de cada um
existe para que o próximo caso parecido não precise ser decidido de novo.

**REMOVER — não é efeito, é outra coisa:**

| id | frase que decidiu | por quê |
|---|---|---|
| `viewing:310070546` | "No emotional bonding, no eroticism, zero intensity" | descreve o que o FILME não entrega (a história não convence), não o que aconteceu com quem assistiu — mesma linha de "faltou emoção" |
| `viewing:1439459822` | "there are too many wow moments" | "wow moments" sem dizer QUAL efeito (chorou? riu?) é intensificador genérico, primo de "obra-prima" — entusiasmo sem efeito descrito |
| `viewing:415968879` | "…and all the kids cheered! but i didn't cheer. i stood right up and started shouting" | **caso limite decidido pela AUSÊNCIA de detalhe, não pela presença**: "started shouting" é comportamento, mas o gatilho é indignação com o roteiro (fim do filme), não uma reação visceral ao filme como obra — mais perto de `critica_social`/`roteiro_estrutura` que de efeito emocional puro |
| `viewing:1431368105` | "The sex scene was a bit cringe i wont lie" | "cringe" aqui qualifica UMA CENA específica (avaliação de conteúdo), não descreve o que aconteceu com quem assistiu — companheiro do `nightmare fuel` do lado "não marca" |
| `viewing:1438967239` | "que manera de detestar a los personajes... odiooo" | o alvo do ódio são os PERSONAGENS ("los personajes"), não o filme como experiência — isso é crítica de `roteiro_estrutura` com intensidade emocional na escrita, não `impacto_emocional` sobre quem assistiu |
| `viewing:1416457627` | "The uncanny cgi human cat morphs are nightmare fuel" | resolve o caso "nightmare fuel" da linha acima: aqui qualifica a QUALIDADE VISUAL da cena (é sobre o CGI, `direcao_imagem`), não descreve pesadelo/medo que o espectador teve |
| `viewing:1437855983` | "ماقدر الفلم انه يخليني أتعلق بالشخصيات و اتأثر معهم" ("o filme não conseguiu me fazer apegar aos personagens e me afetar") | mesma família de "faltou emoção" — descreve o que o filme NÃO conseguiu fazer, negação explícita de efeito, não efeito ocorrido |

**MANTÉM — é efeito, mesmo sem vocabulário óbvio de emoção:**

| id | frase que decidiu | por quê |
|---|---|---|
| `viewing:1424202073` | "A stirring and baffling work. I love it so much." | "stirring" (comovente) e "baffling" (intrigante/desconcertante) são adjetivos de EFEITO, não de qualidade — descrevem o que a obra fez com quem assistiu, distinto de "obra-prima" que não descreve nada |
| `viewing:1418805746` | "it takes you out of it" | "tira você da experiência" é efeito descrito (quebra de imersão), ainda que dito de forma indireta — mantido apesar de o resto da review ser predominantemente técnico |
| `viewing:1433154456` | "certain parts were difficult to watch" | "difícil de assistir" é reação declarada (desconforto), companheira direta de "uncomfortable the whole time" da lista principal — decide a favor de marcar mesmo sendo mais brando |
| `viewing:1431008461` | "Am I losing my mind? Have I lost my whimsy? Or am I being gaslit…" | a sequência de perguntas retóricas É a descrição do efeito — confusão/desorientação genuína causada pelo filme, não avaliação fria; distinto de "is this movie just genuinely terrible" (a última frase, que sozinha NÃO marcaria) |

A linha que separa REMOVER de MANTÉM nesta rodada, resumida: **o alvo da
frase.** Se o alvo é o FILME, a CENA ou os PERSONAGENS ("essa cena é
nightmare fuel", "os personagens são idiotas", "o filme não conseguiu me
fazer sentir algo"), não marca — é avaliação de conteúdo, ainda que com
palavras emocionais. Se o alvo é O QUE ACONTECEU COM QUEM ASSISTIU
("fiquei com medo daquela cena", "aquilo me tirou da experiência", "fiquei
confuso o filme todo"), marca — mesmo com vocabulário indireto ou frase em
forma de pergunta.

---

## Regras gerais (valem para todos os eixos)

1. **Anote o que a review MENCIONA, não o que o filme é.** Um filme com
   trilha marcante cuja review não fala de som não recebe `som_trilha`.
2. **Não olhe o veredito do modelo antes de anotar.** É por isso que
   `gabarito_modelo.json` fica em arquivo separado de `leitura.md`.
3. **Zero eixos numa review é julgamento legítimo** (a review pode não
   falar do filme). Zero eixos no arquivo INTEIRO é erro de parsing — há
   guard-rail para isso em `auditoria_acuracia.ler_anotacoes_humanas`.
4. **`livre` é sobre ASSUNTO, não sobre tamanho.** Use quando a review fala
   de outra coisa que não o filme (logística da sessão, a vida de quem
   escreveu, recado para outra pessoa). Review curta que fala pouco do
   filme ainda fala DO FILME — é eixo, não `livre`. (Mesma régua que o
   prompt de produção passou a usar em `A_regra`.)
5. **`livre` convive com eixos.** A parte que fala do filme vira eixo, a
   parte que não fala vira `livre`.
6. **Marcador de checkbox:** `- [x]` ou `* [x]`, ambos aceitos pelo parser.
   Qualquer outro marcador faz o parser falhar com erro explícito.

---

## Formato do checkbox

```
- [x] impacto_emocional
- [ ] ritmo
- [x] livre — temas: logística da sessão, recado ao diretor
```

`temas` só é lido quando `livre` está marcado.

---

## Procedimento para corrigir o gabarito

Correção de gabarito **nunca é automática**. O procedimento:

1. Levantar TODOS os casos afetados nas duas direções (marcado onde a régua
   diz que não; não marcado onde a régua diz que sim). Levantar só uma
   direção troca uma assimetria por outra.
2. Apresentar cada caso com id, texto completo, eixos atuais e sugestão,
   ordenado por confiança.
3. **O dono do projeto decide caso a caso.** Uma correção automática errada
   contamina o gabarito de forma pior que a inconsistência original, porque
   passa a ter aparência de régua aplicada.
4. Só então aplicar, com backup e contagem de checkboxes antes/depois.
