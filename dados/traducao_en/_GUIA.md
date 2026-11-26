> Para levar o inglês ao pipeline (geração automática), ver `docs/I18N_PIPELINE.md`; este guia continua sendo a fonte das regras.

# Guia do tradutor PT -> EN do conteúdo gerado

Para os agentes (sem chamada de API de LLM) que preenchem os `null` de
`dados/traducao_en/<slug>.json` e `_vocabulario.json`. Cada arquivo é um mapa
`"<string PT exata>": "<tradução EN>"`. **A chave nunca muda** (é a string PT
byte a byte; o site procura a tradução por ela). Só o valor é preenchido.

Fluxo: `python3 scripts/i18n_extrair_en.py` (cria/atualiza, preserva o já
traduzido) -> preencher -> `python3 frontend/build_traducao_en.py` (gera
`frontend/js/data_en.js`) -> `pytest tests/test_traducao_en.py`.

## 1. O que há em cada arquivo

| Campo | Conteúdo |
|---|---|
| `titulo_en` | Título em inglês do filme. Já vem preenchido em 95 filmes (título do Letterboxd); nos 33 sem identidade guardada vem `null`: preencha com o título de lançamento em inglês (ex. "Hereditary", "The Godfather"). Título que não é inglês (ex. "Cidade de Deus"): use o título internacional em inglês ("City of God"). |
| `textos` | strings PT -> EN, sem duplicata, na ordem em que aparecem na página: veredito, temas e exemplos de cada grupo, condições, parágrafos da narrativa. |
| `_orfaos` | traduções cuja string PT sumiu depois de uma regeneração. Ignore (o extrator as devolve se a string voltar). |
| `_vocabulario.json` | gêneros e temas que se repetem em 2+ filmes. Traduza uma vez, vale em todos. |

## 2. Inventário: o que chega à tela (e por isso é traduzido)

Linhas de `frontend/js/filme.js` na data deste guia.

| Campo do dado | Onde renderiza | No arquivo |
|---|---|---|
| `veredito.texto` | `veredictoBlock` (l. ~1588, `el.textContent = texto`) | `textos` |
| `buckets[].temas[].tema` | `themeRow` (l. ~1936, `nm.textContent = t.tema`) | `textos` ou vocabulário (se repete em 2+ filmes) |
| `buckets[].temas[].exemplo_parafraseado` | `themeRow` (l. ~1993, `inner.textContent`) | `textos` |
| `condicoes.vale_a_pena[].texto`, `talvez_evite[].texto` | `colunaDeCondicoes` (l. ~1522, `txt.textContent = cond.texto`) | `textos` |
| `narrativa` | `narrativaCollapsedBlock` (l. ~622: `split(/\n{2,}/)`, um `<p>` por parágrafo) | `textos`, **um parágrafo por chave** |
| `ficha.generos[]` | `T.partesDaFicha` (`textos_home.js` ~l. 399, até 2 gêneros) e filtros/prateleiras de gênero (`explorar.js` ~l. 116, `semanal.js` ~l. 74), via `indice.js` | vocabulário |
| `ficha.titulo` (título PT exibido) | `titleOf`, manchete, cartões, busca | `titulo_en` |

Não renderizam e **não** estão nos arquivos: `observacao_geral`, `niveis`,
`eixos.*` (só servem de chave de ordenação, em PT, antes da tradução),
`tema_texto`, `rotulo_forca`, `sinopse_oficial` (a página não mostra sinopse),
`exemplo_antes_da_guarda`, `descartadas`, metadados. Textos de peso
(`peso_texto`, `peso_meio.texto`, `nota_de_amostra`) são refeitos pela
interface a partir do número (`filme.peso_texto` etc.); não traduza.
Países são códigos ISO (a interface traduz os nomes).

## 3. Regras de tradução

**Registro.** Inglês natural e editorial, registro de crítica de cinema:
conciso, direto, sem coloquialismo e sem pompa. Frases que um editor de
revista de cinema publicaria. Evite decalque do português (falsos cognatos:
"atuações" = "performances", não "actuations"; "elenco" = "cast"; "trama" =
"plot"; "roteiro" = "script"/"screenplay"; "ritmo" = "pacing"; "desfecho" =
"ending"/"resolution"). Inglês americano. Não aumente nem encurte além do
necessário: o comprimento deve ser parecido com o do PT.

**Fidelidade total ao sentido.** Não acrescente nem remova afirmações. Não
suavize nem intensifique ("cansativo" não vira "slightly tiring" nem
"exhausting" sem que o PT diga isso). Preserve a ordem lógica, as ressalvas
e os conectivos de contraste ("mas", "enquanto", "embora").

**Neutralidade (SPEC.md §0, §3[V], §3[CD]).** O produto trata os três grupos
com o mesmo formato e o mesmo respeito: a assimetria vem dos dados, não do
texto. Na tradução isso significa:

- Mesmo tom para os três grupos. Sem desdém, ironia ou sarcasmo com a
  minoria; sem entusiasmo extra com quem elogia. Se o PT é seco, o EN é seco.
- Nenhum score, nota média ou "X out of 10"; nenhum número-síntese novo.
- **Quantificadores são um vocabulário fechado e calibrado por faixa;
  traduza sempre pelo equivalente da mesma força** (nunca mais forte, nunca
  mais fraco; o SPEC proíbe tanto inflar quanto deflacionar):
  `poucos` -> *few*; `alguns` -> *some*; `muitos` -> *many*; `cerca de
  metade` -> *about half*; `a maioria` -> *most* / *the majority*; `quase
  todos` -> *nearly all*. "Uma parcela expressiva", "um número considerável",
  "boa parte", "vários" etc. mantêm a posição relativa na escala: não troque
  por palavra de outra faixa ("muitos" não vira "a lot of people" se isso
  mudar a força; "alguns" nunca vira "a handful" ou "a few"). Se uma frase
  repete o mesmo quantificador em PT, repita o equivalente.
- **Notas x reviews**: "notas" = *ratings*; "reviews"/"críticas"/
  "comentários" = *reviews*. Não troque um pelo outro (SPEC §3[D2], invariante
  de vocabulário do peso). "A maioria das notas" é peso; "a maioria das
  reviews analisadas" é frequência de tema.
- Os grupos: `negativas`/`medianas`/`positivas` como adjetivo -> *negative* /
  *mixed* (ou *middling* quando o PT diz "medianas") / *positive*. Os
  rótulos de interface HATERS / MIXED / FANS não aparecem nas sínteses;
  não os introduza no texto.
- Sem spoilers adicionais: traduza só o que está; não explique, não
  complete, não identifique cena, reviravolta ou desfecho que o PT não nomeie.

**Números.** Preserve todos, idênticos: "~96%", "~1%", anos, durações. O
texto gerado não usa contagem de reviews; se aparecer "~X de N" em dado
futuro, escreva "~X of N". Nunca converta fração em porcentagem nem
porcentagem em fração, e nunca crie um "%" onde o PT não tinha (os
testes comparam os números e os "%" do PT com os do EN). "~" e parênteses
ficam como no PT.

**Nomes próprios e títulos.** Nomes de pessoas, personagens, lugares e
instituições como no original. Títulos de filmes citados no texto: use o
título original/inglês do filme (Letterboxd), não o brasileiro; em dúvida,
mantenha o que está no PT. Não traduza nome próprio nem o ponha entre
aspas. Não adicione aspas onde o PT não tem (o pipeline as remove de
propósito).

**Estrutura.** Uma chave = uma saída; não una nem divida strings. Preserve
quebras de linha e a divisão em frases/parágrafos. A narrativa já está
quebrada em um parágrafo por chave: traduza cada um isoladamente, sem
referências "como dito acima" que dependam de outro parágrafo que o PT não
tenha. Não traduza placeholders nem marcação (`{...}`, `%s`, `<...>`,
tags HTML, `~`).

**Sem sentido adicional.** Não "melhore" o PT: erros ou obscuridades do
original se traduzem como são (e vale avisar o orquestrador à parte).

## 4. As condições: a frase que elas completam

A interface monta a condição como a continuação de uma abertura fixa, em
colunas separadas (`ABERTURA_DA_COLUNA` em `filme.js`; o `aria-label` da
lista também lê a abertura + o item):

- `vale_a_pena`: **Worth it if you…**
- `talvez_evite`: **Maybe skip it if you…**

O PT já é um verbo/oração em 3ª pessoa que completa "Vale a pena se você…"
(ex. "aprecia um roteiro preciso", "se cansa com narrativas arrastadas").
**Forma decidida para o EN:** sintagma verbal no **presente, na forma base
(concorda com "you")**, **começando com letra minúscula**, **sem sujeito
("you") repetido e sem ponto final**:

| PT (continuação de "Vale a pena se você…") | EN (continuação de "Worth it if you…") |
|---|---|
| aprecia um roteiro preciso que constrói tensão contínua unicamente por meio de diálogos | appreciate a precise script that builds sustained tension through dialogue alone |
| procura uma atmosfera opressiva | are after an oppressive atmosphere |
| procura um ritmo ágil e envolvente | want a brisk, engaging pace |

| PT (continuação de "Talvez evite se você…") | EN (continuação de "Maybe skip it if you…") |
|---|---|
| se cansa com narrativas de andamento arrastado | get tired of slow-moving narratives |
| se incomoda com cenários restritos a um único cômodo | are bothered by settings confined to a single room |
| se frustra com discussões repetitivas | get frustrated by repetitive arguments |

Regras: (a) verifique em voz alta "Worth it if you appreciate…" / "Maybe skip
it if you get tired of…"; a frase inteira tem de ser gramatical.
(b) "procura/busca/quer/espera" -> *want* / *are after* / *look for* /
*expect*, conforme o PT; ocorre concordância com *you* ("are", "have", "get"),
nunca "is"/"gets". (c) Mantenha a polaridade e a intensidade do verbo
("se incomoda" != "se irrita" != "sofre"). (d) Não comece com "you",
"if" nem "who". (e) Sem ponto final nem maiúscula inicial (exceto nome
próprio ou "I"). (f) Uma condição por chave: não una.

O **veredito** é uma frase independente (ex. "As opiniões convergem sobre
o foco no texto…" -> "Opinions converge on the focus on the text…"):
com maiúscula e ponto final, como no PT.

Temas (`tema`) são rótulos curtos, sem ponto final, em estilo título
da frase (só a primeira palavra maiúscula, como no PT): "Ritmo lento e tédio"
-> "Slow pacing and boredom".

Exemplos parafraseados (`exemplo_parafraseado`) são uma ou duas frases com
ponto final, na voz de síntese do pipeline ("Muitas reviews descrevem..." ->
"Many reviews describe...").

## 5. Checklist antes de gravar

1. Nenhum `null` sobrando no arquivo (inclusive `titulo_en`).
2. Valor != chave (exceto nome próprio curto ou rótulo idêntico nas duas
   línguas, p.ex. "Drama", "Thriller").
3. Números, "~" e "%" idênticos aos do PT.
4. Condições minúsculas, sem ponto, completam a abertura.
5. Nenhum acréscimo de fato, nome ou cena; nenhum quantificador mais forte
   ou mais fraco.
6. `python3 frontend/build_traducao_en.py` e `pytest tests/test_traducao_en.py`.

## 6. Tabela canônica de quantificadores (passada de consistência)

Uma forma EN por termo PT, na ordem crescente de força. Princípio: cada
substantivo PT tem um substantivo EN fixo (parcela = *share*, parte =
*portion*, fatia = *slice*, fração = *fraction*, número = *number*), e o
adjetivo preserva o grau. O verbo concorda como já estava (não se mexeu na
concordância; só se trocou o sintagma do quantificador).

| PT | EN canônico |
|---|---|
| poucos | few |
| alguns | some |
| uma fatia menor | a smaller slice |
| uma parte / parte deles / parte do grupo / parte do público | a portion (of them / of the group / of the audience) |
| vários / diversos | several |
| muitos | many |
| um número considerável | a considerable number |
| boa parte | a good portion |
| uma parcela expressiva / significativa | a significant share |
| perto da metade | close to half |
| quase metade | nearly half |
| cerca de metade / aproximadamente metade | about half |
| metade (sem modificador) | half |
| grande parte | a large portion |
| a maior parcela | the largest share |
| a maioria / a maior parte | most (most of, quando "dos que…") |
| grande maioria (das notas) | the vast majority (of ratings) |
| quase todos / praticamente todos / a quase totalidade | nearly all |

Rótulos de peso do grupo ("Numa … das notas (~N%)"): `parcela das notas` ->
*a share of the ratings*; `parte (menor) das notas` -> *a (smaller) portion of
the ratings*; `fração mínima` -> *a minimal fraction*; `fração ainda menor` ->
*an even smaller fraction*; `parcela menor` -> *a smaller share*.

Ressalva: "boa parte/grande parte do filme, da projeção, do tempo" (parte
de uma coisa, não de pessoas) pode ficar *a good part of* / *a large part of*;
a tabela vale para quantificadores de gente.

Grupos de review: `negativas` -> *negative*; `positivas` -> *positive*;
`medianas` -> ***middling*** (nunca *mixed*); *mixed* fica só para PT
"mistas/misto".

Condições de `talvez_evite` que em PT começam com "evita": *steer clear of …*
(não "avoid …", que lê contraditório depois de "Maybe skip it if you…").
Títulos de filmes citados: título em inglês do Letterboxd (*Obsession*, *Woman of Fire*, *Triangle of Sadness*). Exceção: "Seven" (título do PT sem dígito) fica
*Seven* no texto, porque o teste de números compara dígitos PT x EN.
