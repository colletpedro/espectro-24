# Validação DeepSeek (deepseek-v4-flash) — 3 filmes do catálogo

**Data:** 2026-08-04. **Objetivo:** decidir se `deepseek-v4-flash` é candidato a
provider default, comparando lado a lado com as narrativas **publicadas**
(geradas pelo Gemini, em `resultado/<slug>.json` — intocadas por esta sessão)
contra narrativas geradas agora com `--provider deepseek`, sobre os **mesmos
dados** de síntese (`--reuse-synthesis`, 0 chamadas de coleta Letterboxd/TMDB).

**Saídas desta validação:** `resultado/validacao_deepseek/{cure,cidade-de-deus,the-invite-2026}.json`
— diretório isolado, `resultado/*.json` de produção não foram tocados (hashes
MD5 conferidos antes/depois, inalterados).

**Orçamento:** até 24 chamadas DeepSeek. Gastas: 14 — 8 no pipeline real
(narrador + editor dos 3 filmes) + 6 em chamadas instrumentadas equivalentes
(1 narrador + 1 editor por filme, prompts idênticos aos reais) só para expor
`usage` (tokens/cache), que o pipeline de produção não expõe. Nenhum filme
falhou — não foi necessário o plano B do orçamento.

**Nenhum veredito de qualidade literária abaixo** — textos e números lado a
lado; a leitura da prosa é humana.

---

## Tabela de decisão

| Filme | 3 movimentos completos? | Flags de honestidade (8) | Editor | Tempo total (narrador+editor) | Custo estimado |
|---|---|---|---|---|---|
| **cure** | ✅ sim | todas `false` (só `aspas_removidas=true`, mecânico) | ✅ aceito, **2 tentativas** (1ª: "conjunto de números do texto foi alterado") · similaridade 0,853 · 0 protegidos perdidos | 24,4 s (1 narrador + 2 editor) | ≈ US$ 0,00057 |
| **cidade-de-deus** | ✅ sim | todas `false` (só `aspas_removidas=true`) | ✅ aceito, **1 tentativa** · similaridade 0,923 · 0 protegidos perdidos · capitalização residual ajustada | 12,8 s (1 narrador + 1 editor) | ≈ US$ 0,00037 |
| **the-invite-2026** | ✅ sim | `perspectiva_nao_marcada=true` **(única flag acesa nos 3 filmes)**; demais `false` | ✅ aceito, **1 tentativa** · similaridade **0,406** (reescrita pesada) · 0 protegidos perdidos | 23,0 s (2 narrador + 1 editor) | ≈ US$ 0,00057 |
| **Soma (3 filmes)** | 3/3 | 1 flag acesa em 3×8=24 checagens | 4 chamadas de editor no total (2+1+1), todas aceitas | 60,1 s | **≈ US$ 0,00152** |

**Teste decisivo (o ponto em que o Qwen3.5-9B local falhava — colapso num
resumo de filme só, ou omissão do movimento 3): PASSOU nos 3 filmes.**
Nenhuma narrativa colapsou; os três movimentos (filme / experiência /
contraste) e os rótulos de peso ancorados apareceram em todas.

**Extrapolação de custo:** US$ 0,00152 ÷ 3 filmes = US$ 0,000506/filme (médio,
1 narrador + ~1,3 chamada de editor). US$ 5,00 ÷ US$ 0,000506 ≈ **9.887
filmes** ao preço medido — o gargalo de 20 req/dia do Gemini free tier deixa
de ser o fator limitante.

---

## Achado — editor: o padrão do smoke test NÃO se repetiu integralmente

O smoke test isolado (`cure`, sessão anterior) via o editor precisar de **3**
tentativas. Nesta validação com os 3 filmes, o padrão foi mais brando:

| Filme | n_tentativas | Motivos por tentativa (na ordem) |
|---|---|---|
| cure | 2 | `"conjunto de números do texto foi alterado"` |
| cidade-de-deus | 1 | (nenhum — aceito de primeira) |
| the-invite-2026 | 1 | (nenhum — aceito de primeira, mas com similaridade 0,406) |

Só **1 dos 3 filmes** (`cure`) precisou de retentativa — não confirma a
hipótese "2+ tentativas em todos os filmes" levantada a partir do smoke test
isolado; a variância parece ligada ao filme/tamanho do texto, não a um viés
sistemático do editor DeepSeek em alterar números.

**Achado mais concreto, e mais preocupante, é outro:** em `the-invite-2026` o
editor foi **aceito de primeira** (nenhuma checagem mecânica reprovou), mas com
**similaridade 0,406** — a mais baixa das três, bem abaixo da faixa 0,85-0,92
dos outros dois filmes — e o texto cresceu de 246 para 307 palavras (+25%).
Comparando bruto×editado desse filme: o editor (a) **reordenou** o Movimento 1
(a apresentação do filme) para o meio do texto, depois do parágrafo do grupo
positivo — os outros dois filmes preservaram a ordem; e (b) **acrescentou um
parágrafo de fechamento inteiro** ("O saldo geral, no entanto, é positivo...")
sem correspondência direta e localizável no texto bruto — passou pelas
checagens mecânicas (protegidos, números, honestidade) porque nenhuma delas
audita "o editor inventou uma frase nova", só "o editor não perdeu conteúdo
protegido / não mudou um número / não regrediu uma flag". Registrado como
achado para leitura humana e eventual reforço de prompt do editor
(`_EDITOR_SYSTEM_PROMPT`) — **não corrigido nesta sessão**, conforme instrução.

`the-invite-2026` também foi o único com `perspectiva_nao_marcada=true` — o
narrador não conseguiu satisfazer a marcação de perspectiva exigida mesmo após
a retentativa interna do §D2 (2 chamadas de narrador, não 1). As duas
observações do mesmo filme (flag de perspectiva acesa + editor mais agressivo)
podem ou não estar relacionadas — não investigado a fundo aqui.

---

## `cure`

### Narrativa publicada (Gemini) — bruta

> Em 1997, Kiyoshi Kurosawa dirigiu A Cura, um filme de Crime, Thriller, Terror e Mistério que segue um detetive em uma investigação sobre mortes misteriosas marcadas por um x nos corpos, cuja busca por respostas o leva a um rapaz enigmático. A experiência de assistir ao filme é marcada por um ritmo lento e uma atmosfera sombria, utilizando planos longos para criar uma sensação de desconforto e um estilo visual eficaz. Essa ambientação sombria contribui para a experiência geral, que é descrita como sendo bastante ambígua.
>
> A grande maioria das notas (~79%) avalia A Cura de forma positiva, com muitos descrevendo o filme como hipnótico e perturbador, gerando uma sensação constante de apreensão. Para quem está nessa faixa, o ritmo lento e metódico intensifica o horror psicológico, levando o espectador a um estado de transe. Muitos também ressaltam a exploração de temas profundos como a fragilidade da identidade e a natureza do mal, e alguns apreciam o filme por não fornecer respostas definitivas, mantendo uma ambiguidade que força a reflexão. Por outro lado, uma minoria das notas (~17%) teve uma experiência mediana. Para eles, o filme tem ideias intrigantes e uma atmosfera eficaz, mas muitos apontam que o ritmo lento e a confusão narrativa, além de um final insatisfatório e ambíguo, impedem uma conexão plena. Uma fração mínima das notas (~3%) considera o filme decepcionante; para esse grupo, a maioria reclama do ritmo excessivamente lento e tedioso, o que o torna arrastado e chato. Muitos também sentiram uma falta de tensão e mistério, e alguns criticam o enredo e roteiro por serem fracos e repetitivos.

### Narrativa publicada (Gemini) — editada (a que está no ar)

> Em 1997, Kiyoshi Kurosawa nos trouxe A Cura. É um filme que mistura Crime, Thriller, Terror e Mistério, onde um detetive investiga mortes misteriosas marcadas por um x nos corpos. Essa busca por respostas o leva até um rapaz enigmático. A experiência de assistir ao filme é de ritmo lento. A atmosfera é sombria, com planos longos que criam uma sensação de desconforto, e o estilo visual é eficaz. Tudo isso compõe uma ambientação que se descreve como bastante ambígua. A grande maioria das notas (~79%) avalia A Cura de forma positiva. Para esses espectadores, o filme é hipnótico e perturbador, gerando uma sensação constante de apreensão. O ritmo lento e metódico intensifica o horror psicológico, levando a um estado de transe. Muitos também veem a exploração de temas profundos, como a fragilidade da identidade e a natureza do mal. E alguns ainda apreciam que o filme não forneça respostas definitivas, mantendo uma ambiguidade que força a reflexão. Só que uma minoria das notas (~17%) teve uma experiência mediana. Eles reconhecem ideias intrigantes e uma atmosfera eficaz, mas o ritmo lento e a confusão narrativa atrapalham a conexão plena. Um final insatisfatório e ambíguo também é um ponto de crítica para esse grupo. Já Uma fração mínima das notas (~3%) achou o filme decepcionante. Para eles, o ritmo é excessivamente lento e tedioso, tornando a experiência arrastada e chata. Muitos sentiram falta de tensão e mistério, enquanto alguns criticam o enredo e o roteiro por serem fracos e repetitivos.

### Narrativa gerada agora (DeepSeek) — bruta

> Em A Cura (1997), o diretor Kiyoshi Kurosawa conduz um thriller de mistério e terror sobre um detetive obcecado em investigar assassinatos marcados por um estranho x. A premissa de um suspeito tímido e enigmático promete um mergulho psicológico sombrio. A experiência de assistir é marcada por um ritmo deliberadamente lento e contemplativo, sustentado por uma atmosfera perturbadora e hipnótica, que se constrói mais pela sugestão do que por sustos diretos. A narrativa evita respostas fáceis e mantém uma ambiguidade constante, mergulhando em temas sobre a fragilidade da mente e a natureza inexplicável do mal. Entre as notas, a grande maioria das notas (~79%) é positiva, e para esses espectadores, o ritmo lento é uma ferramenta que intensifica a sensação de transe e desconforto, com muitos destacando a maestria em criar uma atmosfera perturbadora e a exploração de temas psicológicos profundos. Alguns também elogiam a atuação do antagonista, descrita como assustadoramente calma. Já uma minoria das notas (~17%) ficou no meio-termo: para eles, as ideias são intrigantes, mas a execução falha em aprofundá-las, e o ritmo lento gera confusão narrativa, com muitos apontando um final ambíguo e insatisfatório. Por fim, uma fração mínima das notas (~3%) rejeita o filme: para esse grupo, antes de qualquer análise, o ritmo é simplesmente tedioso e arrastado, e a falta de tensão ou mistério torna a experiência decepcionante, com muitos considerando o enredo repetitivo e os personagens desinteressantes.

### Narrativa gerada agora (DeepSeek) — editada

> A Cura (1997) começa com Kiyoshi Kurosawa à frente de um thriller de mistério e terror, e a trama acompanha um detetive obcecado em investigar assassinatos marcados por um estranho x. A premissa de um suspeito tímido e enigmático promete um mergulho psicológico sombrio. Só que a experiência de assistir é marcada por um ritmo deliberadamente lento e contemplativo, sustentado por uma atmosfera perturbadora e hipnótica, que se constrói mais pela sugestão do que por sustos diretos. A narrativa evita respostas fáceis e mantém uma ambiguidade constante, mergulhando em temas sobre a fragilidade da mente e a natureza inexplicável do mal. Entre as notas, a grande maioria das notas (~79%) é positiva, e para esses espectadores o ritmo lento funciona como ferramenta que intensifica a sensação de transe e desconforto. Muitos destacam a maestria em criar uma atmosfera perturbadora e a exploração de temas psicológicos profundos, e alguns também elogiam a atuação do antagonista, descrita como assustadoramente calma. Já uma minoria das notas (~17%) ficou no meio-termo: para eles, as ideias são intrigantes, mas a execução falha em aprofundá-las, e o ritmo lento gera confusão narrativa, com muitos apontando um final ambíguo e insatisfatório. Por fim, uma fração mínima das notas (~3%) rejeita o filme. Para esse grupo, antes de qualquer análise, o ritmo é simplesmente tedioso e arrastado. A falta de tensão ou mistério torna a experiência decepcionante, e muitos consideram o enredo repetitivo e os personagens desinteressantes.

### Números — `cure`

- **Flags de honestidade (narrador):** `idioma_invalido=false` · `escopo_suspeito=false` · `prevalencia_suspeita=false` · `quantificador_suspeito=false` · `consenso_suspeito=false` · `peso_nao_ancorado=false` · `vocabulario_peso_suspeito=false` · `perspectiva_nao_marcada=false` · `aspas_removidas=true` (mecânico, sem penalidade) · `falhou=false`.
- **Editor:** `edicao_descartada=false` · `n_tentativas=2` · `motivos_por_tentativa=["conjunto de números do texto foi alterado"]` · `similaridade=0,853` · `protegidos_perdidos=[]` · `numeros_alterados=false` (na versão final aceita) · `capitalizacao_ajustada=false`.
- **Tempo/tokens** (chamada representativa, mesmo prompt real): narrador 9,26 s · 6.592 tokens entrada (**6.528 cache hit / 64 cache miss**) · 1.091 tokens saída. Editor 3,83 s · 1.968 tokens entrada (**1.920 cache hit / 48 cache miss**) · 378 tokens saída.
- **Custo estimado** (1 narrador + 2 chamadas de editor, contagem real desta rodada): **≈ US$ 0,00057**.

---

## `cidade-de-deus`

### Narrativa publicada (Gemini) — bruta = editada

O editor foi **descartado** na produção deste filme (`edicao_descartada=true`,
`motivo_descarte="regressão de honestidade: perspectiva_nao_marcada"` — dado
já existente em `resultado/cidade-de-deus.json`, gerado antes desta sessão).
A narrativa publicada é, portanto, a bruta do narrador, sem passe de edição.

> Dirigido por Fernando Meirelles em 2002, Cidade de Deus é um drama criminal que segue Buscapé, um jovem morador da Cidade de Deus que, crescendo em meio à violência, busca na fotografia uma saída para uma vida digna. O filme apresenta uma narrativa abrangente, com ritmo e edição dinâmicos que contribuem para a intensidade da experiência. Sua abordagem da violência é visceral e focada na realidade social, ambientada em um contexto de extrema pobreza.
>
> A grande maioria das notas (~91%) considera Cidade de Deus uma obra-prima. A maioria dessas reviews positivas elogia o estilo visual e a edição dinâmicos, que conferem um ritmo acelerado e energia contagiante. Muitos também destacam a narrativa envolvente e abrangente, capaz de contar múltiplas histórias ao longo de décadas sem perder a coesão. Para uma fração mínima das notas (~1%), porém, muitos criticam a estetização e espetacularização da violência e miséria, vendo o filme como uma representação estereotipada da favela. Para esses espectadores, a violência é excessiva e gratuita. Já para uma pequena minoria das notas (~8%), que se posiciona de forma mediana, a qualidade técnica e estilística é notável, com a edição ágil e a direção estilizada sendo pontos fortes, mas muitos sentem que o filme não consegue gerar uma conexão emocional profunda, sendo mais entretenimento do que uma experiência marcante.

### Narrativa gerada agora (DeepSeek) — bruta

> Cidade de Deus, dirigido por Fernando Meirelles, é um drama criminal de 2002 que acompanha Buscapé, um jovem que cresce em meio à violência da favela e vê na fotografia uma chance de escapar desse destino. A experiência de assistir ao filme é marcada por um ritmo acelerado e uma montagem frenética, com uma representação crua e realista da violência e da realidade social. O estilo visual é dinâmico e estilizado, criando uma atmosfera intensa que não se aprofunda emocionalmente nos personagens. Essa estetização e a abordagem da violência dividem opiniões. A grande maioria das notas (~91%), as positivas, consideram a obra uma obra-prima, elogiando o estilo visual e a edição dinâmicos, a narrativa envolvente e a brutalidade realista da violência, que para eles é impactante e não glamourizada. Uma pequena minoria das notas (~8%), as medianas, reconhecem a qualidade técnica e o retrato realista, mas sentem falta de conexão emocional e de um ritmo mais constante. Para eles, o filme é tecnicamente impressionante, mas não gera o uau esperado. Uma fração mínima das notas (~1%), as negativas, criticam a estetização e espetacularização da violência, a representação estereotipada da favela e a violência excessiva, vendo-as como um recurso para chocar em vez de gerar reflexão. Para esse grupo, a abordagem é eticamente questionável e a narrativa, superficial.

### Narrativa gerada agora (DeepSeek) — editada

> Uma verdadeira porradaria visual, e Cidade de Deus, dirigido por Fernando Meirelles, é um drama criminal de 2002 que acompanha Buscapé, um jovem que cresce em meio à violência da favela e vê na fotografia uma chance de escapar desse destino. A experiência de assistir ao filme é marcada por um ritmo acelerado e uma montagem frenética. A representação é crua e realista da violência e da realidade social. Já o estilo visual é dinâmico e estilizado, criando uma atmosfera intensa que não se aprofunda emocionalmente nos personagens. É essa estetização que divide opiniões, e a abordagem da violência também.
>
> A grande maioria das notas (~91%) são as positivas, e o grupo considera a obra uma obra-prima, elogiando o estilo visual e a edição dinâmicos, a narrativa envolvente e a brutalidade realista da violência, que para eles é impactante e não glamourizada. Mas há uma pequena minoria das notas (~8%), as medianas, que reconhecem a qualidade técnica e o retrato realista, só que sentem falta de conexão emocional e de um ritmo mais constante. Para eles, o filme é tecnicamente impressionante, mas não gera o uau esperado. E existe ainda uma fração mínima das notas (~1%), as negativas, que criticam a estetização e espetacularização da violência, a representação estereotipada da favela e a violência excessiva, vendo essas escolhas como um recurso para chocar em vez de gerar reflexão. Para esse grupo, a abordagem é eticamente questionável e a narrativa, superficial.

### Números — `cidade-de-deus`

- **Flags de honestidade (narrador):** todas `false`, exceto `aspas_removidas=true` (mecânico).
- **Editor:** `edicao_descartada=false` · `n_tentativas=1` (aceito de primeira) · `motivos_por_tentativa=[]` · `similaridade=0,923` · `protegidos_perdidos=[]` · `capitalizacao_ajustada=true` (o pós-processamento determinístico baixou a caixa de um rótulo de peso movido para o meio da frase).
- **Tempo/tokens:** narrador 7,51 s · 6.600 tokens entrada (**6.528 cache hit / 72 cache miss**) · 776 saída. Editor 4,16 s · 1.920 entrada (**1.792 cache hit / 128 cache miss**) · 378 saída.
- **Custo estimado** (1 narrador + 1 editor): **≈ US$ 0,00037**.

---

## `the-invite-2026`

### Narrativa publicada (Gemini) — bruta

> Em O Convite, de 2026, dirigido por Olivia Wilde, um casal em crise, Joe e Angela, decide convidar seus enigmáticos vizinhos para um jantar, o que rapidamente leva a noite a rumos inesperados, explorando os gêneros de Drama e Comédia.
>
> A experiência de assistir ao filme é marcada por um tom que mistura humor e drama, explorando temas de relacionamento e casamento. A ambientação íntima, muitas vezes restrita a um único espaço, é percebida como eficaz na construção de uma atmosfera envolvente.
>
> A grande maioria das notas (~79%) reflete uma recepção positiva, com quase todos elogiando intensamente a direção de Olivia Wilde e o roteiro, destacando a habilidade em equilibrar comédia e drama e criar tensão. A maioria dessas reviews salienta também o desempenho excepcional do elenco e a ótima química entre os atores. Cerca de metade aponta a capacidade do filme de ser hilário e, ao mesmo tempo, profundamente triste ou tocante. Uma minoria das notas (~18%) aponta uma experiência mais mediana; para esse grupo, as performances foram amplamente elogiadas, mas muitos acharam o filme divertido na primeira metade e sentiram que a repetição das situações tornava a experiência cansativa no final. Para uma fração mínima das notas (~3%), o filme foi uma decepção; para eles, cerca de metade das reviews classificou o humor como previsível e pouco engraçado, com muitos achando os personagens e diálogos superficiais ou irritantes.

### Narrativa publicada (Gemini) — editada (a que está no ar)

> O Convite, de 2026, dirigido por Olivia Wilde, mostra Joe e Angela, um casal em crise. Eles decidem convidar os vizinhos enigmáticos para um jantar, e essa noite logo toma rumos inesperados, misturando Drama e Comédia. A experiência do filme se destaca pela mistura de humor e drama, ao explorar temas de relacionamento e casamento. A ambientação é íntima e, muitas vezes, fica restrita a um único espaço. Isso se mostra eficaz para criar uma atmosfera envolvente. A grande maioria das notas (~79%) teve uma recepção positiva. Praticamente todos elogiam muito a direção de Olivia Wilde e o roteiro, destacando como ela consegue equilibrar comédia e drama e ainda criar tensão. Além disso, a maioria das críticas aponta o desempenho excepcional do elenco e a ótima química entre os atores. Cerca de metade das pessoas também nota a capacidade do filme de ser hilário e, ao mesmo tempo, profundamente triste ou tocante. Já Uma minoria das notas (~18%) viu uma experiência mais mediana. Para esse grupo, as performances receberam muitos elogios, mas muita gente achou o filme divertido apenas na primeira metade. Depois, a repetição das situações tornou a experiência cansativa no final. Mas, para uma fração mínima das notas (~3%), o filme foi uma decepção. Para eles, quase metade das avaliações classificou o humor como previsível e pouco engraçado, e muitos ainda acharam os personagens e diálogos superficiais ou até irritantes.

### Narrativa gerada agora (DeepSeek) — bruta

> O Convite (2026), dirigido por Olivia Wilde, mistura drama e comédia ao apresentar um casal à beira do divórcio que convida os enigmáticos vizinhos do andar de cima para um jantar, transformando a noite em algo inesperado. O filme transita entre o humor e o drama em um cenário íntimo, com um ritmo que se torna mais cansativo na segunda metade, especialmente pela repetição de situações e pela transição tonal percebida como abrupta por parte das análises. A grande maioria das notas (~79%) celebra a produção, destacando quase todos dos textos positivos a direção e o roteiro como pontos fortes, além do equilíbrio entre comédia e drama e das atuações, vistas por cerca de metade como excepcionais e com boa química. Para esses espectadores, o filme é hilário e tocante ao mesmo tempo, com uma abordagem original e visualmente envolvente. Já para a minoria das notas (~18%), que se posiciona no meio, trata-se de uma comédia bem executada, com atuações elogiadas por muitos e um roteiro inteligente, mas que se torna repetitivo e previsível, e cuja mudança de tom no final divide opiniões — enquanto alguns acham o desfecho impactante, outros o veem como abrupto e pouco desenvolvido. Por fim, uma fração mínima das notas (~3%) rejeita a obra: para esse grupo, cerca de metade aponta humor e roteiro fracos e entediantes, muitos criticam personagens e diálogos superficiais, e a abordagem da sexualidade é percebida como forçada e constrangedora, resultando em uma experiência decepcionante e previsível.

### Narrativa gerada agora (DeepSeek) — editada

> A grande maioria das notas (~79%) celebra o filme. Os textos positivos destacam a direção, o roteiro, o equilíbrio entre comédia e drama e as atuações, que cerca de metade considera excepcionais, com boa química. Para esse grupo, o filme é hilário e tocante ao mesmo tempo, com abordagem original e visualmente envolvente. O Convite (2026), de Olivia Wilde, mistura drama e comédia: um casal à beira do divórcio convida os enigmáticos vizinhos do andar de cima para um jantar, e a noite vira algo inesperado. O ritmo, porém, cansa na segunda metade, sobretudo pela repetição de situações e pela transição tonal que algumas análises veem como abrupta.
>
> Já a minoria das notas (~18%) fica no meio. Para ela, é uma comédia bem executada, com atuações elogiadas por muitos e um roteiro inteligente, só que repetitivo e previsível. A mudança de tom no final divide opiniões: uns acham o desfecho impactante, outros o veem como abrupto e pouco desenvolvido. O filme transita entre o humor e o drama num cenário íntimo, e aí está o nó.
>
> Por fim, uma fração mínima das notas (~3%) rejeita a obra. Cerca de metade desse grupo aponta humor e roteiro fracos e entediantes; muitos criticam personagens e diálogos superficiais. A abordagem da sexualidade parece forçada e constrangedora para eles. O resultado é uma experiência decepcionante e previsível. O saldo geral, no entanto, é positivo. O drama se mistura à comédia com originalidade, e mesmo os críticos reconhecem a qualidade técnica da direção. As atuações seguram o filme, e a química do casal principal convence. A segunda metade perde fôlego, mas a ideia central sustenta o interesse até o fim. O desfecho polariza, e é justamente essa divisão que faz o filme render conversa. No conjunto, a recepção majoritária é calorosa, e a minoria que reprova não apaga o brilho do conjunto.

### Números — `the-invite-2026`

- **Flags de honestidade (narrador):** `idioma_invalido=false` · `escopo_suspeito=false` · `prevalencia_suspeita=false` · `quantificador_suspeito=false` · `consenso_suspeito=false` · `peso_nao_ancorado=false` · `vocabulario_peso_suspeito=false` · **`perspectiva_nao_marcada=true`** (única flag acesa nos 3 filmes — o CLI avisou: *"algum grupo com marcação de perspectiva exigida ficou sem marcador... mesmo após retentativa"*) · `aspas_removidas=true` · `falhou=false`. O narrador precisou de **2 chamadas** (a inicial + a retentativa interna do §D2), e mesmo assim não satisfez a checagem.
- **Editor:** `edicao_descartada=false` · `n_tentativas=1` (aceito de primeira pelas checagens mecânicas) · `motivos_por_tentativa=[]` · **`similaridade=0,406`** (a mais baixa dos 3 filmes — reescrita substancial, +25% em palavras, reordenação do Movimento 1 e um parágrafo de fechamento novo — ver "Achado" acima) · `protegidos_perdidos=[]`.
- **Tempo/tokens** (chamada representativa): narrador 6,96 s · 6.430 tokens entrada (**6.400 cache hit / 30 cache miss**) · 721 saída. Editor 4,43 s · 1.947 entrada (**1.920 cache hit / 27 cache miss**) · 418 saída.
- **Custo estimado** (2 narrador + 1 editor, contagem real desta rodada): **≈ US$ 0,00057**.

---

## Conclusão factual (sem juízo de qualidade)

- **3/3 filmes passaram no teste decisivo** (movimentos completos, sem
  colapso) — o defeito estrutural que inviabilizou o Qwen3.5-9B local não
  apareceu em nenhum dos 3 filmes com DeepSeek.
- **23/24 checagens de honestidade passaram** (3 filmes × 8 flags); a única
  falha foi `perspectiva_nao_marcada` em `the-invite-2026`, mesmo após a
  retentativa interna do narrador.
- **Editor aceitou os 3 filmes** — nunca precisou descartar e publicar a
  bruta —, mas com variância real de comportamento: de "aceito de primeira,
  quase sem mudar nada" (`cidade-de-deus`, similaridade 0,923) a "aceito de
  primeira, mas reescreveu quase metade do texto e acrescentou um parágrafo"
  (`the-invite-2026`, similaridade 0,406). Essa faixa (0,406-0,923) é mais
  larga que qualquer coisa vista nos dados de produção do Gemini disponíveis
  para comparação direta.
- **Custo:** ≈ US$ 0,0015 para os 3 filmes (8 chamadas reais) — a US$
  5,00 dariam para regenerar a narrativa de **quase 9.900 filmes** ao preço
  medido, muito acima do teto de 20 req/dia do free tier do Gemini.
- **Cache de prefixo:** eficaz nos 3 filmes — 96-99% do prompt do narrador
  veio como cache hit em todos.

A decisão de trocar (ou não) o provider default fica para leitura humana
deste relatório — nenhuma mudança de default foi aplicada nesta sessão.
