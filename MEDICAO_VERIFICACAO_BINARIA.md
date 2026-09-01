# Medição — a verificação binária reprova, e o gabarito que a reprovou está torto

**Três entregas. A primeira é a que decide, e ela REPROVA** no critério
registrado antes de rodar — em duas execuções independentes. Reporto e paro,
como combinado; não reescrevi o critério para o desenho passar no próprio teste.

**Mas a reprovação veio acompanhada de um achado que vale mais que ela:** o
"gabarito humano" contra o qual C1 foi fixado **subconta**, e eu medi por quanto.
Numa releitura à mão das 40 reviews do pior caso, a contagem verdadeira é 16 —
contra 8 no gabarito, 10 em `mencoes_aproximadas` e 22 na verificação binária.
Os três números estão errados; o gabarito e o número publicado erram para
**menos**, o instrumento novo erra para **mais**, e por magnitudes parecidas.

Nada em `resultado/` foi escrito. Nenhum filme regerado. `taxonomia.py` intacto
(md5 `bf41c993142ee0ed20be16a6901ebff5`), `taxonomia_id` segue `ebab2667de74`
(conferido no fim). Suíte: **1.525 testes passando**, o mesmo número da sessão
anterior. Nenhuma review nova raspada — a Entrega 2 usa só o que já está em
`dados/bruto/`. Única escrita em arquivo do repositório: o registro da Entrega 3
em `SPEC.md` §2.6, que foi o que o briefing pediu.

**Chamadas de LLM:** **1.763**, todas sobre a amostra registrada
(1.571 do passe + 192 da repetição de reprodutibilidade), `deepseek-v4-flash`,
`thinking: disabled`. Custo total **US$ 0,065**.

**Convenção:** **MEDIDO** traz número e fonte; **VISTO** é leitura à mão sobre
amostra nomeada; **NÃO VERIFICADO** é premissa que continua sem conferência.

---

# ACHADO 0 — a população de teste das sessões anteriores estava errada

Isto vem antes das três entregas porque todas dependem dele, e porque corrige
uma premissa que as duas sessões anteriores usaram.

`resultado/votacao-3/amostra.json` é descrito no próprio arquivo como *"a
população que a síntese veria"*. **Ele não é.**

**MEDIDO.** A reconstrução determinística da seleção a partir do bruto em disco
— `selecao.selecionar()` com os parâmetros de produção, zero rede — reproduz:

| conferência independente | resultado |
|---|---|
| `buckets[].n_validas` de cada JSON publicado | **105 de 105 buckets** |
| `eixos.fonte_classificacao.por_bucket[].sobreposicao_com_analisadas` | **93 de 93 buckets que têm o campo** |

Duas conferências independentes, das quais a segunda é forte: ela reproduz
números como 20, 14, 19 (aftersun) e 26, 27, 20 (napoleon) que só batem se o
conjunto de ids for exatamente o mesmo. **A reconstrução é a população que a
síntese publicada leu.**

O `amostra.json`, por sua vez, sobrepõe essa população em **67,6%** dos ids
(2.487 de 3.677), e só **2 de 93** buckets têm sobreposição total. Ele veio de
um snapshot do bruto anterior ao que gerou os filmes publicados.

**Consequência.** Esta sessão testa cada bullet contra as reviews que a síntese
**daquele bullet** de fato leu. Sem isso, a comparação com o gabarito à mão —
levantado sobre "todas as reviews da seleção de produção daquele bucket" — não
seria comparação nenhuma. Isso está registrado em `CRITERIO_REGISTRADO.md` §0,
antes de qualquer chamada.

**Registro para as sessões anteriores:** a Entrega 1 de `MEDICAO_SPLIT_E_FONTES.md`
amostrou 260 reviews do `amostra.json`. Aquele resultado não é invalidado — ele
mede frequência e emaranhamento sobre reviews reais dos mesmos filmes e buckets,
e não depende de serem as mesmas que a síntese viu. Mas qualquer medição futura
que precise casar com um bullet publicado tem de reconstruir, não ler o
`amostra.json`.

---
---

# ENTREGA 1 — a verificação binária por (review, tema)

## Parte A — o desenho

Registrado por inteiro em `CRITERIO_REGISTRADO.md` (scratchpad da sessão),
md5 `ccdae9d622c1582b47e5e71ff633131f`, **14:44:25Z**, com zero chamadas de LLM
feitas. Um adendo às 14:45:09Z corrige um defeito de implementação do sorteio
(detalhado em §A.4); nenhum critério de aprovação foi tocado por ele.

### A.1 — Unidade e schema

**Unidade: o par (review, tema).** Uma chamada por par. A review inteira entra;
o tema entra como uma frase.

**A pergunta é sobre o TEMA, não sobre o exemplo.** `mencoes_aproximadas` é
declarado por tema e a barra do frontend é por tema
([filme.js:1370](frontend/js/filme.js:1370)); o `exemplo_parafraseado` entra no
prompt como **desambiguação**, marcado como tal, não como texto a casar palavra
por palavra.

Schema de saída, JSON mode, objeto único, **nesta ordem de campos**:

```json
{"frase": "<trecho literal da review, ou vazio>",
 "tocou_assunto": true,
 "veredito": "sustenta"}
```

A ordem é deliberada e copia o padrão do verificador `V2_alvo` que funcionou
(§2.5 da SPEC): **o compromisso com a evidência vem antes do veredito**, para
fechar o atalho de decidir primeiro e justificar depois.

### A.2 — Os três valores, e a regra de abstenção

| valor | quando |
|---|---|
| `sustenta` | a review **afirma** o que o tema afirma, com frase literal citável |
| `nao_sustenta` | a review não afirma aquilo — cobre "não fala do assunto" e "fala do assunto sem fazer a afirmação" |
| `contradiz` | a review afirma o **oposto** sobre o mesmo assunto |

O caso "toca de leve" **não** ganhou um quarto valor do enum. Ele é resolvido
por regra (R2) e fica registrado no campo diagnóstico `tocou_assunto`. Razão:
alargar o enum de três para quatro é o mesmo movimento — mais decisões numa
chamada só — que a sessão anterior identificou como a causa da perda de
resolução. O enum é a decisão difícil; o diagnóstico anda de carona sem
disputar espaço com ela.

**Regras de abstenção, em ordem de precedência, escritas no prompt:**

- **R1 — na dúvida, `nao_sustenta`.** Default assimétrico deliberado: o erro que
  este passe existe para pegar é o de **inflação** (o achado `wonka`: 1 review
  vira 6). Um instrumento que empata para SIM não pega inflação.
- **R2 — menção de passagem não é sustentação.**
- **R3 — o quantificador do tema não é testado.** Se o tema diz "muitos acham
  X", pergunta-se se **esta** review afirma X.
- **R4 — assunto certo com juízo oposto é `contradiz`**, não `nao_sustenta`.
  Existe para não esconder o modo de falha que gerou o achado `wonka` e a
  contracorrente do `cats-2019`.
- **R5 — sem frase literal, não há `sustenta`.**

**MEDIDO: R5 foi obedecida em 472 de 472 `sustenta`** — nenhum veredito
positivo veio sem trecho citado (média 104 caracteres).

### A.3 — Isto é auditoria, não substituição

O passe roda **depois** de a síntese ter escolhido os 6 temas do bucket. A
síntese continua decidindo **o quê**; o código passa a contar **quantas**
reviews sustentam cada escolha. O que ele substituiria é
`mencoes_aproximadas` — não o bloco de temas, não a rotulagem [D3], não a
classificação por eixo.

### A.4 — Amostra

Regras A0–A6 registradas antes do sorteio. O primeiro sorteio devolveu 35
bullets concentrados em **9 filmes**, todos no início do alfabeto: o balanceio
por bucket reordenava os candidatos por `slug` **depois** do embaralhamento,
anulando o PRNG. Corrigido no adendo (A3b: máximo 3 bullets por filme; A4b: a
ordem embaralhada manda). **Registrado como correção de implementação, com a
declaração de que nenhum resultado de amostra havia sido visto.**

Obtido: **40 bullets** — 5 do gabarito por construção + 35 sorteados — em
**26 filmes**, buckets 12/10/13, cotas por eixo cumpridas exatamente
(`roteiro_estrutura` 9, `atuacao` 5, `critica_social` 4, `direcao_imagem` 4,
`ritmo` 4, `tom_atmosfera` 3, `impacto_emocional` 2, `som_trilha` 2,
`comparacoes` 1, `expectativa` 1). **1.571 pares.**

### A.5 — Custo projetado sobre 300 filmes

**MEDIDO sobre as 1.763 chamadas reais:** entrada **813 tokens/chamada**
(78% de cache hit, porque o `system` é idêntico em todas), saída **37
tokens/chamada**, **US$ 0,000037 por chamada**.

| cenário | chamadas | custo |
|---|---:|---:|
| 35 filmes, 1 voto | 25.200 | **US$ 0,93** |
| **300 filmes, 1 voto** | **216.000** | **US$ 7,94** |
| **300 filmes, 3 votos** | **648.000** | **US$ 23,82** |

**Comparado ao que já se paga:**

| | custo | fonte |
|---|---:|---|
| classificação por eixo, 3 votos, 36.000 reviews | US$ 9,86 | medido, sessão anterior |
| lista de índices na síntese (300 filmes) | +US$ 0,03 | projetado, sessão anterior |
| **passe por review, 300 filmes, 3 votos** | **US$ 23,82** | **medido aqui** |

**Correção à projeção da sessão anterior.** `MEDICAO_SPLIT_E_FONTES.md` §Entrega
4.5 projetou US$ 1,25 (1 voto) e US$ 3,74 (3 votos), e concluiu que o passe
custaria *"menos de metade"* da classificação por eixo. **O custo real é 6,4×
maior**, porque a projeção assumiu um contexto muito menor que o real: o
`system` deste passe sozinho tem ~600 tokens, e a review média acrescenta ~200.
Com 3 votos, o passe custa **2,4× a classificação por eixo inteira**, não
metade dela. Continua barato em termos absolutos; **deixa de ser desprezível**,
e o argumento "o custo não existe" não sobrevive à medição.

---

## Parte B — os critérios, fixados antes de rodar

| | condição | limiar | de onde veio o limiar |
|---|---|---|---|
| **C1a** | erro absoluto médio contra o gabarito | **< 2,80** | é o MAE de `mencoes_aproximadas` contra o mesmo gabarito |
| **C1b** | vitórias individuais contra o gabarito | **≥ 3 de 5** | com n=5, "melhor na média" pode ser carregado por um acerto só |
| **C2** | mediana da razão `binário / mencoes` na amostra sorteada | **[0,75 , 1,35]** | intervalo observado (0,78–1,33) na calibração manual registrada de 8 bullets, `ESTUDO_CATALOGO_35.md` §6b |
| **C3** | razão agregada (soma / n) por bucket | **[0,8 , 2,9]** | a razão real do catálogo hoje: média 1,67, mediana 1,55, max 2,83 |
| **C4** | `contradiz` funciona em `cats-2019`/neg | ≥ 1 | diagnóstico declarado, **não reprova** |

**Veredito registrado:** APROVA só se C1a, C1b, C2 e C3 passarem. **Zona
cinzenta: nenhuma.**

Imprecisão do gabarito **registrada antes de rodar**: o estudo conta `wonka` no
nível do *exemplo* (1) e `napoleon` no nível do *tema* (13). Como o passe
pergunta pelo tema, adotei **2** para `wonka` — o número que **desfavorece** o
instrumento novo — e reporto os dois.

---

## Parte C — o resultado

### C1 — REPROVA

| caso | gabarito | `mencoes` | **binário** | `contradiz` | erro `mencoes` | **erro binário** |
|---|---:|---:|---:|---:|---:|---:|
| `wonka` neg — *Fotografia e efeitos visuais criticados* | 2 | 6 | **4** | 0 | 4 | **2** ✅ |
| `talk-to-me-2022` neg — *Diálogos e tom juvenil artificiais* | 2 | 5 | **4** | 0 | 3 | **2** ✅ |
| `napoleon-2023` med — *Batalhas visualmente impressionantes* | 13 | 15 | **12** | 2 | 2 | **1** ✅ |
| `interstellar` pos — *Fotografia e efeitos visuais deslumbrantes* | 8 | 11 | **14** | 0 | 3 | **6** ❌ |
| `cats-2019` neg — *Experiência de visualização desconfortável* | 8 | 10 | **22** | 1 | 2 | **14** ❌ |

| | `mencoes` | binário |
|---|---:|---:|
| **MAE** | **2,80** | **5,00** |
| vitórias individuais | — | 3/5 |

- **C1a: REPROVA.** 5,00 contra o limiar de 2,80.
- **C1b: passa.** 3 de 5.
- Com `wonka` = 1 (leitura de exemplo): MAE `mencoes` 3,00, binário 5,20 —
  **reprova igual**.

**A segunda execução (A6), mesma amostra, mesmo prompt, mesmo modelo:** MAE
binário **3,80**, vitórias 3/5. **C1a REPROVA também.** Não é sorte de execução.

### C2 — passa

**MEDIDO** sobre os 35 bullets sorteados (fora do gabarito):

| | valor |
|---|---:|
| mediana da razão `binário / mencoes` | **1,125** |
| média | 1,180 |
| p25 · p75 | 0,833 · 1,300 |
| min · max | 0,67 · 2,14 |

**PASSA** — dentro de [0,75 , 1,35], e no mesmo lugar em que a calibração
manual de 8 bullets pôs a razão `à mão / mencoes` (mediana 1,02). Delta médio
+1,31 menção por bullet; binário maior em 23, igual em 1, menor em 11.

### C3 — passa

Fração `sustenta` por bullet: média **0,300**, mediana 0,275. Projetada para os
6 bullets de um bucket: razão agregada **1,80**, contra **1,61** pela mesma
projeção com `mencoes_aproximadas` e **1,67** medida no catálogo real.
**PASSA** — o passe não colapsa nem para SIM nem para NÃO.

### C4 — passa formalmente, falha na prática

`cats-2019`/negativas devolveu **1** `contradiz`. Formalmente ≥1, então C4
passa. **Mas ele deveria ter devolvido 5.** Na minha releitura das 40
(§Parte D), as reviews que afirmam o oposto do tema são cinco:

> *"my friends and i have seen this film like 3 times and its been the most fun ive had"* · *"This is not a movie to watch, it's a movie to point and laugh at with friends… I have watched it several times with a smile on my face"* · *"This movie made us laugh so hard for the entire run time"* · *"As a drinking game — this movie is phenomenal"* · *"I was overcome by what I can only describe as a psychedelic euphoria"*

O modelo achou **uma** delas. Pior: das quatro que perdeu, uma foi classificada
como **`sustenta`** — a que diz *"it's a movie to point and laugh at… with a
smile on my face"* virou evidência de "experiência desconfortável".
**Recall de `contradiz` medido: 1 de 5.** No corpus inteiro, `contradiz`
aparece em 37 de 1.571 pares (2,4%), em 21 dos 40 bullets.

O terceiro valor não é decorativo — mas está perto disso, e **R4 é a regra menos
obedecida do prompt**.

### Veredito da Entrega 1

| condição | resultado |
|---|---|
| C1a — erro contra o gabarito | **REPROVA** (5,00 vs 2,80; 3,80 na 2ª execução) |
| C1b — vitórias individuais | passa (3/5) |
| C2 — sem viés sistemático | passa (mediana 1,125) |
| C3 — plausibilidade agregada | passa (1,80) |
| C4 — `contradiz` (diagnóstico) | passa formalmente, recall 1/5 |
| **conjunto** | **NÃO APROVADO** |

**A verificação binária, como desenhada e medida aqui, não deve ser
implementada.**

---

## Parte D — o diagnóstico, e é aqui que a reprovação vira informação

A reprovação inteira vem de dois casos, os dois na mesma direção: o binário
conta **a mais**. Fui ler as reviews para saber de quem é o erro.

### D.1 — `interstellar`: o gabarito está errado, o instrumento está certo

**VISTO — li as 14 frases que o passe citou como `sustenta`.** Todas as 14 são
afirmações explícitas de que o visual é deslumbrante:

> *"The cinematography is breathtaking"* · *"The visuals are unmatched"* ·
> *"wizualnie jest jednym z piękniejszych tworów ostatnich lat"* ·
> *"Christopher Nolan created a visual marvel"* · *"Visualmente te vuela la
> cabeza"* · *"how gorgeous space looked… top 2 or 3 best cinematography I've
> seen of all time"*

**Zero falsos positivos.** E do outro lado: só **1** das 25 restantes foi marcada
`nao_sustenta` com `tocou_assunto: true` — a candidata única a falso negativo, e
ela é um veredito genérico (*"It's simply a beautifull movie"*), corretamente
recusado.

**A contagem verdadeira é ~14. O binário acertou. O gabarito de 8 é que erra por
−6, e `mencoes` (11) erra por −3.**

E o gabarito de 8 é o mais frágil dos cinco: **NÃO VERIFICADO** — o
`ESTUDO_CATALOGO_35.md` nunca declara uma contagem para este bullet. Ele discute
o *exemplo* (a cláusula sobre buracos negros, que de fato não se sustenta) e diz
que o **tema** é *"impecavelmente sustentado"*. O número 8 aparece pela primeira
vez na tabela de `MEDICAO_CONTAGEM_E_AB.md`, sem derivação visível.

### D.2 — `cats-2019`: os dois estão errados, em direções opostas

**VISTO — li as 40 reviews inteiras do bucket**, não só as que o modelo marcou.
É a única forma de saber se a diferença é falso positivo do instrumento ou falso
negativo do gabarito. Minha contagem independente para *"Experiência de
visualização desconfortável"*: **16 reviews** (banda 16–18 com dois casos
limítrofes).

| | contagem | erro contra 16 |
|---|---:|---:|
| gabarito do estudo | 8 | **−8** |
| `mencoes_aproximadas` (publicado) | 10 | **−6** |
| **verificação binária** | 22 | **+6** |
| minha releitura das 40 | **16** | — |

**Os 6 falsos positivos do binário têm um padrão só, e é conhecido:** veredito
seco contado como experiência.

> *"baffling, pathetic and truly rotten"* · *"This movie sucks in genuinely
> every way possible"* · *"The human-cat-looking characters look weird"* ·
> *"wtf is a jellicle cat I still don't know"*

Nenhuma dessas diz o que o filme **fez com quem assistiu** — dizem o que o filme
**é**. É exatamente a confusão que derrubou a precisão de `impacto_emocional`
para 0,486 e que o passe `V2_alvo` existe para corrigir. **O eixo deste bullet é
`impacto_emocional`.** O passe binário reproduz o mesmo erro, no mesmo eixo, com
prompt novo — o que confirma que a falha é da distribuição do material, não da
redação (SPEC §3[D]: *"instrução não remove o que a distribuição do material
impõe"*).

Os 16 verdadeiros, por contraste, não deixam dúvida — e nenhum deles seria
achado por varredura de palavra-chave em português:

> *"I just felt like gouging my eyes out"* · *"I'm genuinely scarred for having
> seen it all the way through"* · *"JFC that was rough"* · *"Die digitalen
> Fellkörper… erzeugen einen Zustand, den man nicht mehr los wird"* ·
> *"The scale makes my brain hurt"*

### D.3 — Por que o gabarito subconta, e é estrutural

O protocolo do estudo está declarado em `ESTUDO_CATALOGO_35.md` §12: para cada
bullet, ler **até 12** reviews que carregam o eixo do bullet, mais **até 6** que
casam por palavra de conteúdo. **Até 18 de 40**, e a segunda metade por
*matching* de palavra.

Isso não acha *"gouging my eyes out"*, *"JFC that was rough"*, *"einen Zustand,
den man nicht mehr los wird"* nem *"my brain hurt"* — nenhum casa com palavra de
conteúdo de "experiência de visualização desconfortável", e o corpus é
multilíngue. O estudo declarou o viés do protocolo, mas o declarou na direção
errada: escreveu que *"o viés favorece o produto"* porque procura suporte onde
ele é mais provável. **Isso vale para o veredito qualitativo (achar suporte),
não para a contagem** — para contar, ler 18 de 40 e casar por palavra só pode
subestimar.

**Nos dois casos que reprovaram C1, o gabarito subconta: −8 em `cats-2019`, −6
em `interstellar`.** Nos três que passaram, os números batem.

**Isto NÃO reabilita a verificação binária.** C1 foi fixado antes de rodar,
contra o gabarito que existia, e contra ele o instrumento perde 5,00 a 2,80 em
duas execuções. A reprovação está de pé. O que muda é o que se aprende com ela:
**a régua estava torta, e ela é a mesma régua que `MEDICAO_CONTAGEM_E_AB.md`
usou para reprovar a contagem por eixo.** Aquela decisão foi tomada com estes
mesmos cinco números.

### D.4 — A reprodutibilidade é o problema mais duro, e ninguém tinha medido

**MEDIDO (A6)** — duas execuções idênticas, mesmo prompt, mesmo modelo, mesmos
192 pares do gabarito:

| | valor |
|---|---:|
| concordância par a par | **88,0%** |
| **Jaccard do conjunto `sustenta`** | **0,70** |

E o que isso faz com a contagem publicável:

| bullet | execução A | execução B | Δ |
|---|---:|---:|---:|
| `wonka` neg | 4 | **1** | **−75%** |
| `cats-2019` neg | 22 | 18 | −18% |
| `talk-to-me` neg | 4 | 3 | −25% |
| `interstellar` pos | 14 | 13 | −7% |
| `napoleon` med | 12 | 11 | −8% |

**`wonka` cai de 4 para 1 entre duas execuções da mesma coisa.** Num bullet de
32 reviews, isso é a barra indo de 13% para 3%.

Isto é o argumento mais forte contra adotar o desenho em passada única, e é
independente da acurácia: **um número que muda 75% entre execuções não é
autoridade sobre nada.** A saída conhecida é votação de 3 — mas ela custa
US$ 23,82 em 300 filmes (§A.5) e **não foi medida aqui**; se ela estabiliza o
suficiente é pergunta em aberto, não resultado.

*(Nota de honestidade: na execução B, `wonka` = 1 bate exatamente com a leitura
estrita do gabarito. Escolher a execução B tornaria o resultado melhor. Não é
uma escolha disponível — a execução A foi a registrada como o passe.)*

## Limites da Entrega 1

- **N = 40 bullets, 1.571 pares, um modelo, passada única.** O piso de variância
  deste instrumento é grande (Jaccard 0,70) e C1a reprova por margem de 2,2
  pontos de MAE; na execução B, por 1,0. As duas reprovam.
- **A releitura à mão de §D.1 e §D.2 é minha, sobre 40 + 40 reviews, e é uma só
  pessoa sem segunda opinião.** É gabarito melhor que o do estudo para estes dois
  bullets — li todas as reviews, não 18 — e não é gabarito auditado.
- **Nos 35 bullets sorteados não há gabarito nenhum.** C2 e C3 medem
  plausibilidade e ausência de viés, **não acurácia**. Nada aqui diz que as 472
  marcações `sustenta` da amostra maior estão certas.
- **A votação de 3 não foi medida.** Todo número desta entrega é de passada
  única.
- **O modo de falha `padding`** que a sessão anterior antecipou para a lista de
  índices não se aplica aqui (não há lista a preencher), mas o modo de falha
  **veredito-seco-como-experiência** (§D.2) é o análogo e está medido.

## O que fazer com a reprovação

Em ordem do que o dado sustenta:

1. **Refazer o gabarito antes de qualquer outra decisão de contagem.** É a ação
   mais barata e a de maior retorno: os cinco casos são a régua de duas decisões
   já tomadas (`MEDICAO_CONTAGEM_E_AB.md` reprovou a contagem por eixo com eles)
   e de uma terceira (esta). Custa ler 5 buckets × 40 reviews = 200 reviews à
   mão. **Dois dos cinco já estão refeitos aqui.**
2. **Não adotar o passe binário em passada única.** Jaccard 0,70 basta sozinho.
3. **Se o passe for reconsiderado, medir a votação de 3 primeiro** — é a única
   intervenção conhecida contra a instabilidade, e custa US$ 23,82 em 300 filmes,
   não os US$ 3,74 projetados antes.
4. **`contradiz` precisa de passe próprio ou não existe.** Recall 1/5 dentro de
   uma pergunta de três valores. É o mesmo diagnóstico da sessão anterior por
   outro caminho: a decisão que divide atenção com outra é a que se perde.

---
---

# ENTREGA 2 — curva de retorno marginal por número de reviews

**EXPLORATÓRIA, e a dependência declarada no briefing NÃO se materializou.** A
Entrega 1 reprovou, então a contagem binária **não** desloca a contagem
publicada — a base do bootstrap não muda. A curva abaixo vale como está. O que
a torna exploratória é outra coisa, e é maior (§2.2).

## 2.1 — O superset existe, e é bem menor do que o bruto sugere

O briefing pedia conferir em ≥10 filmes. Conferi nos **35**.

**MEDIDO — reviews brutas por filme:** 634 a 1.088 em 34 dos 35 (a exceção é
`obsession-2026`, com 69). `aftersun`: 908, como a sessão anterior registrou.

**Mas review bruta não é review utilizável.** Sob os filtros de produção —
`texto_completo`, sem spoiler, ≥150 caracteres — o pool elegível **por bucket**:

| | @ `min_chars` 150 (produção) | @ `min_chars` 50 |
|---|---:|---:|
| mediana | **66** | 145 |
| média | 65,7 | 146,4 |
| máximo | **112** | 216 |
| buckets com pool ≥ 50 | **87/105 (83%)** | 102/105 (97%) |
| buckets com pool ≥ 65 | 54/105 (51%) | 102/105 (97%) |
| buckets com pool ≥ 94 | 12/105 (11%) | 101/105 (96%) |
| buckets com pool ≥ 147 | **0/105 (0%)** | 50/105 (48%) |

`aftersun`, o caso citado: 908 brutas → **95 / 107 / 84** elegíveis por bucket,
40 usadas. **Folga real de 2,4×, não de 22×.**

**A premissa do briefing se confirma em direção e não em magnitude:** dá para
simular por reamostragem sem raspar nada, e o teto do que seria *coletável* hoje
é ~66 por bucket na mediana, não centenas.

## 2.2 — O limite estrutural que muda o significado da curva

**As reviews do superset não têm rótulo.** A classificação por eixo existe para
as ~40 por bucket que foram classificadas; as outras ~26 nunca passaram por
classificador nenhum. Classificá-las é chamada de LLM sobre material fora da
amostra autorizada — proibido nesta sessão, e corretamente.

**Consequência, declarada antes de rodar** (em `curva_n.py`): reamostrar com
m > 40 **não acrescenta informação**. Ele congela a distribuição empírica das 40
rotuladas e reduz só o termo de variância amostral. **n = 50 aqui significa "e
se eu tivesse sorteado 50 da MESMA distribuição", não "e se eu tivesse
classificado 10 reviews a mais".** Para n ≤ 40 a leitura é limpa (subamostragem);
para n = 50 é extrapolação com o ponto fixo congelado.

## 2.3 — Método

Idêntico ao bootstrap de `ESTUDO_CATALOGO_35.md` §8: **B = 2.000** reamostragens
com reposição por filme, **semente 24**, dentro de cada bucket,
`lift = freq − max(freq nos outros dois)`, comparação com a margem de 20pp em
`Fraction` exato como `espectro24.eixos`. População rotulada:
`consenso_verificado.jsonl` (~40/bucket).

**Sobre quantos filmes: os 35.** O briefing dizia que não precisava ser os 35 —
mas o custo é computacional (13 segundos, zero LLM), então subamostrar só
perderia poder sem economizar nada.

## 2.4 — A curva

**MEDIDO:**

| n por bucket | P(filme mantém contraste) | largura do IC95 do lift dominante | ganho por review adicional |
|---:|---:|---:|---:|
| 10 | 0,993 | 76,0 pp | — |
| 20 | 0,918 | 54,3 pp | 2,17 pp |
| 30 | 0,836 | 44,2 pp | 1,01 pp |
| **40 (atual)** | **0,769** | **38,4 pp** | 0,58 pp |
| 50 | 0,718 | 34,5 pp | **0,39 pp** |

**Dois achados, e o primeiro é contraintuitivo.**

### P(manter contraste) CAI com mais reviews

Não é erro: é o artefato que o estudo dos 35 já nomeava e que aqui fica
quantificado. `tematico` é *"algum das 30 células passa de 20pp"* — um **máximo
sobre 30 células ruidosas**. Com n pequeno o ruído é enorme, o máximo quase
sempre estoura a margem, e 99,3% dos filmes saem `tematico` com n=10. Conforme n
cresce, o ruído encolhe e o máximo converge para o valor verdadeiro.

| n | filmes com P(tematico) ≥ 0,9 |
|---:|---:|
| 10 | **35/35** |
| 20 | 27/35 |
| 30 | 12/35 |
| 40 | **10/35** |
| 50 | 9/35 |

**O rótulo `tematico` é, em boa parte, fabricado por ruído amostral. Coletar
mais reviews não o estabiliza — ele o remove.** Por grupo publicado:

| | n=10 | n=20 | n=30 | n=40 | n=50 |
|---|---:|---:|---:|---:|---:|
| publicados `tematico` (18) | 0,995 | 0,955 | 0,917 | 0,884 | 0,857 |
| publicados `valorativo` (17) | 0,990 | 0,879 | 0,750 | 0,648 | 0,572 |

Os filmes com lift observado alto ficam **mais** estáveis com n
(`obsession-2026` 42,5pp: 1,000 → 1,000; `cats-2019` 30,0pp: 0,932 → 0,940);
os de lift baixo, menos (`cidade-de-deus` 5,4pp: 0,385 → 0,242). É o esperado —
n afia na direção da verdade, seja ela qual for.

### A largura do IC é exatamente 1/√n — não há cotovelo

| n | IC95 medido | previsto por 1/√n (ancorado em n=40) |
|---:|---:|---:|
| 10 | 76,0 | 76,7 |
| 20 | 54,3 | 54,2 |
| 30 | 44,2 | 44,3 |
| 40 | 38,4 | 38,4 |
| 50 | 34,5 | 34,3 |

Erro máximo do ajuste: **0,7pp**. **A curva de retorno marginal é o 1/√n do
livro-texto e não achata em lugar nenhum** — ela só fica lenta. O ganho cai de
2,17pp por review (10→20) para **0,39pp por review** (40→50).

**A pergunta "onde ela achata" tem resposta e é: em lugar nenhum, mas ela deixa
de valer a pena bem antes do que se gostaria.** O IC95 do lift dominante é
**38,4pp** com n=40 — quase o dobro da margem de 20pp que ele tem de decidir.
Para o intervalo caber dentro da própria margem:

| IC95 alvo | n necessário por bucket | buckets com pool suficiente hoje |
|---:|---:|---|
| 30 pp | 65 | 54/105 (51%) |
| 25 pp | 94 | 12/105 (11%) |
| **20 pp** | **147** | **0/105 (0%)** |
| 15 pp | 262 | 0/105 |

**Não é caro. É impossível com a coleta atual.** Chegar a um IC do tamanho da
margem exigiria 147 reviews elegíveis por bucket, e o melhor bucket do catálogo
tem 112. Baixar `min_chars` de 150 para 50 levaria 48% dos buckets a 147 — mas
isso troca a composição do que se analisa por reviews curtas, o que é outra
intervenção com outros custos, e não foi medida.

## 2.5 — O que esta entrega NÃO responde

- **O ganho de ir de 35 filmes para mais.** Não é simulável a partir do que está
  coletado, por construção: reamostrar reviews de 35 filmes não cria o 36º. Só se
  mede coletando uma amostra pequena de filmes novos — decisão e sessão à parte.
- **O ganho de classificar mais reviews de verdade.** Os pontos de n=50 são
  extrapolação com o ponto estimado congelado (§2.2). Eles dizem quanto a
  **variância amostral** encolheria; não dizem se a frequência observada se
  moveria, e ela pode se mover.
- **A estabilidade da classificação em si.** Como no estudo original: cada review
  carrega o mesmo conjunto de eixos em todas as reamostragens. Se o classificador
  mudasse de ideia, este bootstrap não veria. Essa pergunta tem medição própria
  em `ESTABILIDADE_AGREGADA.md`.
- **Se a margem de 20pp é o número certo.** A curva mostra que ela é fina demais
  para o n disponível. Se a resposta é mais n, margem maior, ou outro estado que
  não seja binário, é decisão de produto que esta medição não toma.

---
---

# ENTREGA 3 — feelings em espera, dividido por fonte

**Aplicada** em `SPEC.md`, seção nova **§2.6**. Registro de decisão; nenhum
comportamento mudou, nenhum arquivo de `resultado/` foi tocado, nada de feelings
foi construído.

O que ficou registrado:

- **Feelings não é descartado por causa da colisão de vocabulário com o TMDB.**
  A colisão medida em `MEDICAO_SPLIT_E_FONTES.md` (Entrega 3) — o TMDB emite
  `moody`, `bitter`, `playful`, `so bad it's good` em 17 de 35 filmes — é
  argumento para **não misturar** as duas fontes, não para descartar uma delas.
- **Review-derived** (`mood`, `experiencia`, `narrativa`) e **work-derived**
  (`tema`, `contexto`) continuam como **entidades internas separadas**, com
  listas próprias e sem precedência de uma sobre a outra, porque `mood` do TMDB
  é catalogação editorial e `mood` de review é relato de leitor. Fundi-las
  produziria uma etiqueta cuja procedência o produto não saberia declarar.
- **A dependência de ordem, explícita:** feelings é uma **segunda** camada sobre
  o mesmo material, e adicioná-la enquanto a **primeira** ainda erra aumenta o
  espaço de erro sem isolar a causa. Feelings aguarda o veredito da verificação
  binária — que é esta sessão, e **reprovou**. As cinco perguntas bloqueantes já
  listadas em `DESENHO_CLASSIFICACAO_V2.md`, entre elas o gabarito humano de
  ~100 reviews para feelings, continuam valendo e são **posteriores** a esta.

---

# Resumo

**A verificação binária por (review, tema) REPROVA** no critério registrado —
erro absoluto médio de 5,00 contra o gabarito, com o limiar em 2,80, e 3,80 numa
segunda execução idêntica. Passa em C2 (mediana da razão 1,125), em C3 (razão
agregada 1,80) e formalmente em C4, mas o `contradiz` tem **recall de 1 em 5** e
uma das quatro contradições perdidas foi contada como `sustenta`. E a
reprodutibilidade entre duas execuções idênticas é **Jaccard 0,70**, com `wonka`
saindo de 4 para 1 menções — um número que muda 75% entre execuções não é
autoridade sobre nada. **Não implementar em passada única.**

**Mas a régua que reprovou está torta, e isso importa mais.** Lendo as 40 reviews
inteiras do pior caso: a contagem verdadeira de `cats-2019` é **16** — o
gabarito diz 8, o número publicado diz 10, o binário diz 22. Em `interstellar`,
as 14 marcações do binário são **todas corretas** e o gabarito de 8 nunca teve
derivação registrada. A causa é estrutural: o protocolo do estudo lia até 18 de
40 reviews e casava por palavra-chave, num corpus multilíngue. **Os mesmos cinco
números foram a régua que reprovou a contagem por eixo na sessão passada.**
Refazer o gabarito custa 200 reviews lidas e é a ação de maior retorno em fila.

**O superset existe, mas é 2,4× e não 22×.** As 908 reviews brutas de `aftersun`
viram **95/107/84** elegíveis por bucket sob os filtros de produção; a mediana do
catálogo é **66 por bucket**, o máximo é 112, e n=50 é alcançável em 83% dos
buckets.

**A curva de retorno é 1/√n exata, sem cotovelo, e a conclusão é dura:** o IC95
do lift dominante é **38,4pp com n=40**, quase o dobro da margem de 20pp que ele
decide; fechá-lo até a margem exigiria **147 reviews elegíveis por bucket**, e o
melhor bucket do catálogo tem 112. Pior: **P(manter contraste) CAI com mais
reviews** — de 0,993 em n=10 para 0,718 em n=50 —, porque `tematico` é um máximo
sobre 30 células ruidosas e n só afia na direção da verdade. Coletar mais reviews
não estabiliza o rótulo `tematico`; ele o **remove**. Com n=10, 35 de 35 filmes
teriam contraste "estável"; com n=40, dez.

**Feelings fica em espera, com as duas fontes preservadas como entidades
separadas** e a dependência de ordem registrada em `SPEC.md` §2.6.
