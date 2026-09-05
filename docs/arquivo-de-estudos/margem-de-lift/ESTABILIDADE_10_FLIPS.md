# Os 10 filmes que mudariam de `contraste` sob cobertura completa

**Zero chamada de LLM. `resultado/<slug>.json` não foi tocado — só lido.**
Confirmação de que os artefatos publicados continuam internamente coerentes:
os 10 arquivos abaixo carregam `taxonomia_id: ebab2667de74` (o mesmo do
consenso estendido) e `fonte_classificacao` presente em todos — cada um é
consistente consigo mesmo, eixos/lift/contraste/veredito concordam dentro do
próprio arquivo. O que existe é defasagem entre o artefato (70,7% de
cobertura) e o consenso em `votacao-3/` (100%), não inconsistência.

---

## A tabela completa

| filme | publicado hoje | sob consenso completo | direção | lift antes | lift depois |
|---|---|---|---|---|---|
| `bones-and-all` | tematico | valorativo | **T → V** | `impacto_emocional`/neg **26,0pp** | `atuacao`/med 17,5pp |
| `everything-everywhere-all-at-once` | tematico | valorativo | **T → V** | `direcao_imagem`/med **28,9pp** | `direcao_imagem`/med 17,5pp |
| `hereditary` | tematico | valorativo | **T → V** | `ritmo`/neg **36,0pp** | `expectativa`/neg 15,0pp |
| `napoleon-2023` | tematico | valorativo | **T → V** | `ritmo`/med **25,0pp** | `impacto_emocional`/neg 12,5pp |
| `perfect-days-2023` | tematico | valorativo | **T → V** | `tom_atmosfera`/pos **28,9pp** | `ritmo`/neg 17,5pp |
| `spider-man-across-the-spider-verse` | tematico | valorativo | **T → V** | `comparacoes`/med **25,0pp** | `expectativa`/med 12,5pp |
| `dune-2021` | valorativo | tematico | V → T | `som_trilha`/pos 19,2pp | `impacto_emocional`/med **20,0pp** |
| `oppenheimer-2023` | valorativo | tematico | V → T | `critica_social`/neg 17,4pp | `critica_social`/neg **25,0pp** |
| `the-substance` | valorativo | tematico | V → T | `tom_atmosfera`/med 19,9pp | `tom_atmosfera`/med **27,5pp** |
| `wicked-2024` | valorativo | tematico | V → T | `ritmo`/neg 14,9pp | `ritmo`/neg **20,0pp** |

**A direção é 6 contra 4, não 5 contra 5.** Seis filmes publicam hoje um
contraste que o consenso completo não sustenta; quatro publicam a afirmação
conservadora quando o consenso completo encontraria contraste.

## O caso que pesa mais: `tematico → valorativo` (6 filmes)

**A razão de isolar este grupo:** um filme `tematico` publica, no veredito, a
frase que NOMEIA o eixo de contraste — uma afirmação específica ("quem não
recomenda rejeita pelo ritmo arrastado", "quem recomenda valoriza X") que o
leitor lê como o que separa os grupos. Se o dado completo não sustenta esse
contraste, a página está fazendo uma afirmação de conteúdo sem lastro — não
um "talvez", uma frase categórica.

Um filme `valorativo → tematico` publica hoje "os grupos falam das mesmas
coisas — discordam sobre se elas funcionam" (ou equivalente), que é a leitura
mais conservadora possível: não nomeia eixo nenhum, não afirma nada
específico sobre do que cada grupo fala. Se o consenso completo encontraria
um contraste ali, o produto está **subafirmando** — deixando de contar algo
verdadeiro, não contando algo falso. É o erro inofensivo dos dois.

**Os 6 vereditos publicados hoje, na íntegra** (campo `veredito.texto` de
cada `resultado/<slug>.json`):

### `bones-and-all`

> *"Cerca de metade de quem recomenda valoriza a narrativa pela trajetória de
> autoconhecimento e aceitação pessoal. Em contrapartida, cerca de metade de
> quem não recomenda expressa forte repulsa ao excesso de sangue e violência
> gráfica, além de considerar a trama previsível."*

Eixo publicado: não nomeado explicitamente no texto, mas o lift dominante
publicado é `impacto_emocional`/negativas. Sob o consenso completo, o maior
lift do filme cai para `atuacao`/medianas 17,5pp — abaixo da margem.

### `everything-everywhere-all-at-once`

> *"Cerca de metade de quem recomenda ressalta o impacto emocional ao abordar
> superação, laços familiares e esperança. Em contrapartida, a maioria dos que
> não recomendam critica o roteiro por alegorias familiares artificiais, além
> de apontar pouca profundidade no teor social e um desfecho previsível."*

Eixo publicado: `direcao_imagem`/medianas 28,9pp. Sob o consenso completo,
17,5pp — abaixo da margem.

### `hereditary`

> *"Entre os que recomendam, muitos centram suas análises em comparações. Em
> contrapartida, cerca de metade dos que não recomendam rejeita a produção
> pelo andamento arrastado e pela sensação de monotonia."*

Eixo publicado: `ritmo`/negativas 36,0pp — o maior lift observado entre os 10.
Sob o consenso completo, o maior lift do filme cai para
`expectativa`/negativas 15,0pp.

### `napoleon-2023`

> *"O meio-termo é o maior grupo da recepção (~45% das notas). Enquanto muitos
> que recomendam baseiam-se em comparações, a maioria dos que reprovam
> questiona a representação de Napoleão e aponta o impacto emocional. No
> meio-termo, cerca de metade aborda a ênfase no relacionamento com Josefina,
> trazendo também ressalvas ao ritmo e à duração extensa."*

Eixo publicado: `ritmo`/medianas 25,0pp. Sob o consenso completo,
`impacto_emocional`/negativas 12,5pp — o novo maior lift, abaixo da margem.

### `perfect-days-2023`

> *"A maioria dos que não recomendam a produção destaca o andamento
> excessivamente vagaroso e entediante. Em contrapartida, a maioria dos que
> recomendam foca na atmosfera, ressaltando o encanto presente na rotina
> simples e nos detalhes do dia a dia."*

Eixo publicado: `tom_atmosfera`/positivas 28,9pp. Sob o consenso completo,
`ritmo`/negativas 17,5pp.

### `spider-man-across-the-spider-verse`

> *"A maioria dos que não recomendam aponta que a narrativa é truncada e
> carece de um desfecho convincente. Em contrapartida, cerca de metade dos que
> recomendam valoriza a construção e a evolução das personagens ao longo da
> trama."*

Eixo publicado: `comparacoes`/medianas 25,0pp. Sob o consenso completo,
`expectativa`/medianas 12,5pp.

## O outro grupo: `valorativo → tematico` (4 filmes), sem texto a citar

`dune-2021`, `oppenheimer-2023`, `the-substance`, `wicked-2024` publicam hoje
o veredito genérico de ausência de contraste — nenhum nomeia eixo, então não
há frase específica em risco de ficar sem lastro. Nos 4, o lift cruzou a
margem de baixo para cima (19,2→20,0 · 17,4→25,0 · 19,9→27,5 · 14,9→20,0),
sempre no mesmo eixo antes e depois — não é um eixo novo aparecendo, é o
mesmo eixo ganhando força com a amostra completa.

## Resumo para a decisão

| | n |
|---|---:|
| `tematico → valorativo` (afirmação específica sem lastro completo) | **6** |
| `valorativo → tematico` (subafirmação, inofensiva) | **4** |
| **total** | **10** |

Maioria (6 de 10) é do tipo que pesa: o produto publica hoje uma frase que
nomeia causa, e o dado completo não sustenta.
