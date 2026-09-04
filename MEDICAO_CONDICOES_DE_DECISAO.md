# CONDIÇÕES DE DECISÃO — medição, comparação e recomendação

**Estudo de VIABILIDADE. Nada foi implementado em produção.** Nenhum arquivo
de `resultado/` foi escrito (`git status` sem diff em toda a sessão), nenhum
filme regerado, nenhum estágio novo criado em `src/` ou `scripts/`,
`taxonomia_id` / lei de margem / cota / piso intocados, frontend intocado,
nenhuma reclassificação. **Suíte: 1.591 passaram antes e 1.591 depois.**

O desenho medido aqui está em
[DESENHO_CONDICOES_DE_DECISAO.md](DESENHO_CONDICOES_DE_DECISAO.md); os dois
documentos se leem nessa ordem.

**Convenção:** **MEDIDO** = número que saiu de código rodado nesta sessão ou
de documento anterior citado com a fonte. **VISTO** = leitura, julgamento,
argumento. Onde as duas se misturam, a frase diz qual é qual.

**Chamadas de LLM: 8**, todas na Entrega 2, todas nos quatro filmes
declarados. Provider `gemini`, modelo `gemini-3.7-flash` — os do estágio
`veredito` em `config.py`, sem override.

---

## Critério de sucesso — REGISTRADO ANTES DE QUALQUER GERAÇÃO

Reproduzido na íntegra do arquivo escrito antes da primeira chamada de LLM.

> ### C1 — FABRICAÇÃO (desqualificante, corte em ZERO)
> Qualquer condição em "informação não encontrada" (§10 do
> `ESTUDO_CATALOGO_35`) reprova o estágio. As duas populações comparáveis já
> medidas deram zero: bullets 0/40 (§10); veredito, zero contraste fabricado
> nos 17 `valorativo` nos dois braços do A/B (§3[V]). **A condição é um ato
> de fala MAIS FORTE que os dois — ela aconselha em vez de relatar —, então
> o limiar dela não pode ser mais frouxo que o do que ela substitui.**
>
> ### C2 — GENERALIZAÇÃO EXCESSIVA (corte em 12,5%)
> 12,5% é a taxa que §10 mediu nos bullets (5 de 40). O estágio comprime os
> MESMOS temas; se generaliza mais que o bullet de onde tira o material,
> piora o produto na dimensão que §10 identificou como o modo de falha
> DOMINANTE.
>
> ### C3 — REPRODUTIBILIDADE (corte em 0,80 de Jaccard)
> Sobre o conjunto de `(lado, tema_origem)` entre duas execuções idênticas.
> A verificação binária foi reprovada, entre outras razões, por Jaccard 0,70
> entre execuções idênticas (SPEC §2.7). Aquele estágio só ROTULAVA reviews
> internamente; este escreveria a frase mais visível da página — **um
> estágio mais exposto não pode ter barra mais baixa que a de um estágio
> interno já reprovado.**
>
> ### C4 — `hereditary`, o teste de ABSTENÇÃO (desqualificante)
> Abstenção ou ancoragem no `exemplo_parafraseado` ⇒ passa. Condições
> confiantes e não ancoráveis ⇒ reprova por C1.
>
> ### C5 — os dois validadores precisam PASSAR NO PAR
> Reprovar o caso ruim **e** deixar passar limpo o caso correto. Validador
> sem o par não conta como entregue.
>
> ### Regra de decisão
> CONSTRUIR exige C1 ∧ C2 ∧ C3 ∧ C4 ∧ C5. Falha em qualquer um ⇒ NÃO
> CONSTRUIR.
>
> ### Limite da amostra, declarado antes
> Quatro filmes. Com ~24-30 condições geradas, zero fabricações observadas
> dá limite superior de 95% de ~10-12% pela regra de três — ou seja, **mesmo
> um resultado limpo NÃO prova taxa baixa de fabricação no catálogo; prova
> apenas "não pior que os bullets, na amostra lida"**. Nenhuma conclusão
> desta sessão pode ser enunciada sem esta frase ao lado.

*(Nota, depois de rodar: saíram **48** condições e não 24-30 — o estágio
devolveu 3 por lado em todos os 16 lados, e a estimativa registrada supunha
alguma abstenção. Com 48, o limite superior de 95% é ~6%. A previsão
implícita no próprio critério — "vai haver abstenção" — falhou, e isso é o
§2.1.)*

---
---

# ENTREGA 2 — geração e medição sobre a amostra

## 2.0 O que rodou

| filme | share HATERS/MIXED/FANS | por que está na amostra |
|---|---|---|
| `perfect-days-2023` | 2 / 7 / 92 | o caso fácil — a inversão de valor está escrita nos temas |
| `napoleon-2023` | 22 / 45 / 33 | MIXED dominante, e o filme dos dois defeitos conhecidos |
| `hereditary` | 6 / 14 / 80 | o caso duro — temas FANS sem valência no rótulo |
| `the-godfather` | 2 / 5 / 93 | desequilíbrio extremo |

**Duas execuções idênticas por filme**, uma amostra por execução, sem
best-of-N — para que a comparação entre execuções meça a distribuição do
MODELO e não a estabilidade de um seletor. **48 condições geradas**
(4 filmes × 2 execuções × 6 condições).

**MEDIDO — flags mecânicas disparadas nas 48:** `tema_verbatim` **2**;
todas as outras **zero**. Nenhuma condição acima do teto de 14 palavras
(média 11,0, máximo 13).

## 2.1 O resultado que decide a sessão, antes dos outros

**MEDIDO: em 16 de 16 lados (4 filmes × 2 execuções × 2 lados), o modelo
devolveu exatamente 3 condições. ZERO abstenções.** A invariante 5 do
desenho — *"lista vazia é resposta válida e preferível; NÃO complete cota"* —
não foi exercitada uma única vez.

E o mesmo modelo, no mesmo projeto, já tem essa falha medida:

> *"**Achado novo — o modelo nunca usa 'não sei julgar', mesmo devendo.**
> MEDIDO. Nas 42 reviews das duas folhas reduzidas… o modelo escolheu `não
> sei julgar` **zero vezes**… Zero ocorrências em 42 tentativas… é sinal de
> que a instrução de abstenção não está sendo seguida na prática, não só de
> que o modelo raramente precisa dela."* (SPEC §2.7)

**Zero de 42 lá, zero de 16 aqui.** É a mesma instrução, o mesmo tipo de
saída, o mesmo resultado. **VISTO:** não é possível, com esta amostra,
distinguir "sempre houve material" de "o modelo não abstém". Mas a hipótese
"não abstém" tem agora dois pontos independentes e a hipótese contrária tem
zero.

## 2.2 `hereditary` — a previsão FALHOU, e a razão importa

**A previsão registrada era:** os FANS de `hereditary` têm temas sem
valência (*"Atuações"*, *"Trilha sonora"*, *"Roteiro e história"*), então o
estágio não produziria condições honestas do lado "vale a pena"; condições
confiantes ali seriam inventadas.

**MEDIDO: o estágio produziu 3 condições confiantes por execução, e elas NÃO
são inventadas.**

| condição gerada | tema citado | o que o `exemplo_parafraseado` do tema diz |
|---|---|---|
| *"valoriza atuações intensas que transmitem uma gama complexa de emoções"* | `POS-A` *Atuações* | *"…a performance **intensa** da atriz principal, que consegue **transmitir uma gama complexa de emoções**…"* |
| *"gosta de suspense criado por silêncios, planos longos e desconforto persistente"* | `POS-B` *Atmosfera e tensão* | *"…uma sensação de medo e **desconforto** que **persiste** do início ao fim, com uma direção que utiliza **silêncios e planos longos** para gerar **suspense**."* |
| *"prefere histórias com desenvolvimento gradual entre drama familiar e terror psicológico"* | `POS-D` *Roteiro e história* | *"…trama bem construída, com um **desenvolvimento gradual** que mistura **drama familiar e terror psicológico**, embora algumas reviravoltas sejam vistas como previsíveis."* |

**A previsão estava errada porque partia do RÓTULO, e a valência mora na
PARÁFRASE.** É a mesma correção que §2.7 já tinha feito, com um caso real,
ao revisar P4: *"o que o leitor vê na tela é o par tema +
`exemplo_parafraseado`, e é a paráfrase que carrega a afirmação
específica"*. O rótulo *"Atuações"* é mudo; a paráfrase é a frase inteira.

**C4 PASSA** — não por abstenção, mas porque não havia do que abster-se. O
teste de abstenção continua **não exercitado**, e §2.1 é o que sobra.

**VISTO, e é a leitura honesta:** este resultado é bom para o desenho e ruim
para a confiança. Ele mostra que a fonte de valência é suficiente; não
mostra que o estágio sabe reconhecer ausência, porque a ausência nunca
apareceu. O caso desenhado para testar a abstenção testou outra coisa.

## 2.3 Taxa de fabricação — as quatro categorias do §10

**Protocolo:** cada uma das 48 condições lida contra o `tema` E o
`exemplo_parafraseado` do tema que ela cita (P4 REVISADO). **Leitura minha,
não medição automática: esta tabela é VISTO, com os textos colados abaixo
para que qualquer leitor refaça o julgamento.**

| categoria | n | % |
|---|---:|---:|
| suporte direto | **43** | 89,6% |
| extrapolação legítima | 1 | 2,1% |
| generalização excessiva | **4** | **8,3%** |
| **informação não encontrada** | **0** | **0%** |
| **total** | **48** | **100%** |

*(Total conferido contra o N conhecido, como a nota de método do §2.5
exige.)*

### Os 4 casos de generalização excessiva, com o texto

**1 e 2. `perfect-days-2023` / `NEG-B`, nas DUAS execuções.**
- gerado: *"Talvez evite se você **se incomoda com a romantização do
  trabalho e do desgaste na rotina**"* (exec 2: *"…e do desgaste da
  rotina"*).
- tema `NEG-B` *Romantização do trabalho e da rotina*, paráfrase: *"Há uma
  crítica incisiva à forma como a obra enobrece a vida de um faxineiro,
  **ignorando** as condições estruturais e o desgaste do trabalho…"*
- **O defeito é de RELAÇÃO, não de escopo.** A queixa é que o filme
  romantiza o trabalho **omitindo** o desgaste. A condição junta os dois num
  só objeto romantizado — o desgaste passa a ser o que o filme enobrece,
  quando é o que ele apaga. Uma inversão pequena, gerada duas vezes em duas,
  e invisível para todos os validadores.

**3 e 4. `hereditary` / `POS-D`, nas DUAS execuções.**
- gerado: *"Vale a pena se você **prefere histórias com desenvolvimento
  gradual entre drama familiar e terror psicológico**"*.
- a paráfrase termina em *"…**embora algumas reviravoltas sejam vistas como
  previsíveis**"*, e a condição corta a ressalva.
- É exatamente a cláusula de §10: *"o bullet apaga uma contracorrente
  visível"*. Aqui a contracorrente estava dentro da própria paráfrase
  citada, a poucas palavras de distância.

### A categoria que o §10 não tem, e que este formato cria

§10 define generalização excessiva por contracorrente **do mesmo bucket**.
Uma condição não fala de um grupo — fala da DECISÃO do leitor. Então a
contracorrente relevante é a de **qualquer** bucket, e ela precisa de conta
própria.

**MEDIDO — o caso, e é o mais grave da sessão:**

> `napoleon-2023`, **duas execuções em duas**:
> *"Vale a pena se você **busca sequências de batalha espetaculares, brutais
> e com coreografias autênticas**"* ← `POS-C` *Qualidade das cenas de
> batalha*.
> **FLAGS: nenhuma. Passou em todos os validadores mecânicos do desenho,
> inclusive o de discriminação.**

Este é o defeito **IMPRECISO** da auditoria manual, reproduzido pelo estágio
automatizado em 2 de 2 execuções. O leitor sai da página achando que as
batalhas são o argumento a favor do filme. Os outros dois buckets dizem:

- HATERS `NEG-F` *Batalhas decepcionantes*: *"visualmente impressionantes,
  **mas carecem de estratégia e tática**, sendo muitas vezes confusas"*;
- MIXED `MED-A` *Batalhas visualmente impressionantes*: *"amplamente
  elogiadas por sua grandiosidade"*.

**E o `NEG-F` foi DESCARTADO pelo modelo nas duas execuções** (§2.5) — ou
seja, a página inteira diria que as batalhas valem o ingresso e **em nenhum
lugar** diria que o grupo que rejeitou o filme as chama de taticamente
vazias.

**Por que o validador 2a não pegou, e é o limite medido do proxy:**
`espetaculares`, `brutais` e `coreografias` são lexicalmente **exclusivas**
de `POS-C`. Semanticamente são a mesma afirmação que `visualmente
impressionantes` e `grandiosidade`. **O validador testa palavra; o defeito é
de significado.** §3.3 do desenho já declarava essa fronteira; aqui ela está
medida, no caso exato para o qual o validador foi desenhado.

**Contagem sob a leitura estendida (contracorrente em QUALQUER bucket e
ausente do conjunto de condições gerado):** +2 (`napoleon`/`POS-C`, duas
execuções) ⇒ **6 de 48 = 12,5%**, colado no corte de C2 e não abaixo dele.

### O caso de extrapolação legítima (1)

`hereditary` exec 2, `NEG-C`: *"procura sustos genuínos **frequentes** e
momentos de choque eficazes"*; a paráfrase diz *"os momentos de choque são
**raros** e pouco eficazes"*. "Frequentes" é inferido de "raros" — inferência
curta e segura.

### C1 e C2 — veredito

- **C1 PASSA.** Zero "informação não encontrada" em 48. Toda condição tem
  frase de origem rastreável.
- **C2 PASSA na leitura estrita (8,3% < 12,5%) e EMPATA na leitura estendida
  (12,5%).** Não passa com folga em nenhuma das duas.

## 2.4 Reprodutibilidade — C3

**MEDIDO, duas execuções idênticas por filme:**

| filme | J(lado, tema_origem) | J(palavras de conteúdo) | textos idênticos |
|---|---:|---:|---:|
| `perfect-days-2023` | 1,000 | 0,707 | 1 / 6 |
| `napoleon-2023` | 1,000 | 0,720 | 0 / 6 |
| `hereditary` | 1,000 | 0,463 | 0 / 6 |
| `the-godfather` | **0,714** | 0,340 | 0 / 6 |
| **média** | **0,929** | 0,557 | — |

A única divergência de DECISÃO: `the-godfather` trocou `POS-A` *Atuações
marcantes* (28/40) por `POS-E` *Ritmo lento e longa duração* (12/40) entre
uma execução e a outra.

**C3 PASSA** (0,929 ≥ 0,80), e passa com folga confortável. O Jaccard de
palavras (0,557) é a redação variando com a decisão fixa — o mesmo
desacoplamento que o §3[V] já aceita para o veredito, e não é critério.

**VISTO, com a ressalva obrigatória:** 4 filmes, 2 execuções. Uma divergência
observada em 8 execuções não estima taxa nenhuma. O número é bom; a amostra
não sustenta a precisão que ele aparenta.

## 2.5 O achado NÃO previsto: o modelo faz SELEÇÃO EDITORIAL

Nenhum critério do briefing manda escolher **quais** 3 dos 6 temas viram
condição. O modelo escolhe.

**MEDIDO — a escolha do modelo contra a ordem de frequência do código, em
16 pares (filme, bucket, execução):**

| | |
|---|---:|
| escolha = os 3 temas mais citados | **2** |
| escolha ≠ os 3 mais citados | **14** |
| **total** | **16** |

Os temas que o modelo descartou nas **duas** execuções, com a menção que o
produto publica ao lado do bullet:

| filme | tema descartado | menções |
|---|---|---:|
| `the-godfather` / FANS | *Maestria técnica e visual* | **18/40** |
| `the-godfather` / HATERS | *Filme superestimado* | **12/30** |
| `hereditary` / HATERS | *Expectativa vs. realidade (hype)* | **12/40** |
| `perfect-days-2023` / FANS | *Fotografia e estética visual* | 12/40 |
| `hereditary` / FANS | *Cinematografia e direção* | 10/40 |
| `napoleon-2023` / HATERS | *Ritmo e edição* | 10/40 |
| `the-godfather` / FANS | *Cenas icônicas e memoráveis* | 10/40 |
| `perfect-days-2023` / FANS | *Atuação de Koji Yakusho e minimalismo* | 10/40 |
| `napoleon-2023` / HATERS | *Batalhas decepcionantes* | 6/40 |
| *(mais 14 temas de menor frequência)* | | |

`the-godfather`/FANS é o caso limite: o **terceiro tema mais citado do
grupo** (18 de 40) sai da página, e o quinto (12 de 40) entra.

**Por que isto é uma violação de arquitetura e não uma preferência de
redação.** O §3[V] define a fronteira do projeto em uma frase: *"o código
decide O QUÊ (quais fatos, quais números, qual rótulo, qual eixo, qual
grupo); o modelo decide apenas COMO ESCREVER"*, e enumera: *"o modelo não
escolhe **qual** eixo, **qual** tema, **qual** grupo, **qual** rótulo de
intensidade nem **qual** estado de contraste"*. **Aqui ele escolhe qual
tema, em 14 de 16.** Não é um caso de borda do desenho; é o desenho —
enquanto o número de condições por lado for menor que o número de temas
disponíveis, alguém escolhe, e neste desenho é o modelo.

**Isto é consertável, e o conserto é conhecido:** o CÓDIGO seleciona os N
temas (por `mencoes_aproximadas`, com desempate declarado) e o briefing
entrega **só** esses N, sem lista para escolher. Custa uma decisão de
produto — qual regra de seleção — e nenhuma pesquisa. **Não é motivo
suficiente para não construir; é requisito de qualquer construção.**

## 2.6 Custo — MEDIDO, não estimado

Preços de `scripts/comparar_narrador.py` (`gemini-3.7-flash`, tabela paga,
US$ 0,75 entrada / 3,75 saída por 1M — **promocional até 31/12/2026, depois
1,50/7,50**).

| | valor |
|---|---:|
| chamadas | 8 |
| tokens de entrada / saída | 13.180 / 2.167 |
| **custo total da medição** | **US$ 0,0180** |
| custo por chamada | US$ 0,00225 |
| latência mediana por chamada | 5,6 s |

**Projeção, com o custo por chamada medido:**

| | 35 filmes | 300 filmes |
|---|---:|---:|
| `BEST_OF_N` = 1 | US$ 0,079 | US$ 0,68 |
| **`BEST_OF_N` = 3** (o do projeto) | **US$ 0,236** | **US$ 2,03** |
| tempo sequencial, N=3 | ~9 min | ~77 min |
| … com o preço pós-promoção (2×) | US$ 0,47 | US$ 4,05 |

**O custo não é um argumento contra construir.** Para comparação com o
mesmo instrumento: a verificação binária foi reprovada, entre outros
motivos, por **US$ 23,82 em 300 filmes com 3 votos** (SPEC §2.7). Este
estágio custa **~1/12 disso**. Se a decisão for não construir, não é o preço
que a decide — e isso precisa estar escrito, porque um resultado negativo
barato é fácil de confundir com um resultado negativo por custo.

---
---

# ENTREGA 3 — a comparação que decide

## 3.1 O veredito e as condições, lado a lado

Os quatro são `contraste: valorativo` sob a lei por `n` da v1.9.34.

### `perfect-days-2023` (2 / 7 / 92)

> **Veredito publicado:** *"As opiniões divergem sobre o funcionamento do
> roteiro e da estrutura. Enquanto cerca de metade de quem recomenda
> encontra encanto no cotidiano e na simplicidade dos acontecimentos, cerca
> de metade de quem não recomenda considera a condução arrastada e monótona,
> apontando superficialidade no desenvolvimento do enredo e dos
> personagens."*

> **Condições (exec 1).** Vale a pena se você: *aprecia encontrar poesia na
> repetição diária e na simplicidade do cotidiano* · *busca uma experiência
> quase meditativa guiada por um ritmo lento e contemplativo* · *valoriza a
> solidão e a introspecção como caminhos de paz*. Talvez evite se você: *se
> cansa com lentidão e com a ausência de eventos relevantes* · *se incomoda
> com a romantização do trabalho e do desgaste na rotina* · *exige um arco
> dramático bem desenvolvido e rejeita narrativas superficiais*.

**CONCORDAM** no achado central e **as condições dizem mais**: elas nomeiam
a romantização do trabalho — a segunda queixa mais citada das HATERS
(12/40), com carga política — que o veredito não tem espaço para carregar.
**A divergência revela o que o formato compra:** o veredito comprime em um
eixo; a condição enumera em três.

### `napoleon-2023` (22 / 45 / 33)

> **Veredito publicado:** *"O meio-termo é o maior grupo da recepção (~45%
> das notas). O debate gira em torno da condução narrativa e da figura
> central: cerca de metade de quem recomenda valoriza a abordagem íntima do
> protagonista, enquanto a maioria dos que não recomendam reprova esse
> retrato. Para a maioria nas avaliações intermediárias, o incômodo está na
> ênfase exagerada à relação com Josefina."*

> **Condições (exec 1).** Vale a pena se você: *busca sequências de batalha
> espetaculares, brutais e com coreografias autênticas* · *prefere
> acompanhar as inseguranças e a vida pessoal de um homem comum* · *valoriza
> fotografia, figurinos e cenários deslumbrantes*. Talvez evite se você:
> *exige fidelidade histórica estrita e se incomoda com erros em datas e
> eventos* · *espera um estrategista brilhante e rejeita um retrato fraco ou
> infantilizado do líder* · *prioriza conquistas militares e políticas em vez
> da relação amorosa com Josefina*.

**CONCORDAM** no eixo íntimo-versus-retrato e no foco em Josefina.
**DIVERGEM em duas coisas, e as duas contam contra as condições:**

1. o veredito carrega o peso do meio (45%) e três rótulos de quantificador;
   as condições carregam **nenhum**;
2. as condições acrescentam as batalhas — e é exatamente a adição que §2.3
   mostra ser enganosa.

### `hereditary` (6 / 14 / 80)

> **Veredito publicado:** *"As opiniões dividem-se sobre o funcionamento da
> narrativa e de sua estrutura. Enquanto muitos entre os que recomendam
> apreciam o desenvolvimento da história, cerca de metade dos que não
> recomendam acha a condução desordenada e carente de explicações."*

> **Condições.** Vale a pena se você: *valoriza atuações intensas…* · *gosta
> de suspense criado por silêncios, planos longos e desconforto persistente*
> · *prefere histórias com desenvolvimento gradual…*. Talvez evite se você:
> *se incomoda com longos períodos sem ação…* · *busca sustos genuínos…* ·
> *se irrita com histórias com pontas soltas…*.

**DIVERGEM, e aqui as condições vencem claramente.** O veredito fala só de
`roteiro_estrutura`, porque é o `assunto_compartilhado`; e com isso **não
menciona os dois temas mais citados das FANS** — *Atuações* (20/40) e
*Atmosfera e tensão* (15/40), que são 80% da recepção deste filme. Um leitor
decidindo se assiste `hereditary` quer saber que a atuação e o clima são o
que as pessoas elogiam, e **o veredito não conta**. As condições contam.

### `the-godfather` (2 / 5 / 93)

> **Veredito publicado:** *"As visões divergem ao avaliar as comparações com
> outras produções: cerca de metade de quem recomenda valoriza a evolução do
> protagonista na condução da trama, enquanto, **numa amostra pequena**,
> cerca de metade dos que não recomendam considera o andamento narrativo
> excessivamente vagaroso e cansativo."*

> **Condições (exec 1).** Vale a pena se você: *busca atuações marcantes…* ·
> *aprecia a evolução convincente de um jovem a líder implacável* · *se
> interessa por tramas sobre laços de família, lealdade e poder*. Talvez
> evite se você: *se cansa com ritmo arrastado…* · *se incomoda com excesso
> de diálogos longos e falta de ação* · *não se atrai pela temática de máfia*.

**DIVERGEM, e esta divergência é a mais séria do documento.** O veredito diz
**"numa amostra pequena"** sobre as HATERS. As condições dão **três linhas
de mesmo peso visual** a um grupo que é **2% das notas** e cuja análise saiu
de 30 reviews, ao lado de três linhas para os 93%.

Isso é a **infidelidade por omissão** que motivou a v1.4.0 — *"filmes
amplamente aclamados soam divididos no produto, porque os três grupos
recebem o mesmo peso textual e visual… cada frase era verdadeira, mas o
conjunto comunicava algo falso"* — reaparecendo num canal novo, pela terceira
vez. A v1.9.30 já a tinha encontrado na ORDEM dos blocos, com este mesmo
filme como caso: *"a leitura abria por HATERS, 2% das notas"*.

**O formato de condição é simétrico por construção**, e a simetria é o
defeito quando a recepção é 2/5/93. O `rotulo_forca` do desenho (§1.5) é a
correção proposta; ela **não foi testada**, e o modelo, deixado por conta
própria, não escreveu peso nenhum (§2.3 do desenho: 0 de 48).

## 3.2 A substituição desacopla a frase da maquinaria da margem?

**CONFIRMADO EM PARTE, REFUTADO EM PARTE. A tese, como enunciada, é forte
demais nas duas pontas.**

### Onde ela se confirma

**MEDIDO (SPEC §2.5 / `ESTUDO_MARGEM_20PP.md` §4.3):** no evento real de
cobertura 70,7% → 100%, **10 de 35 filmes trocaram de estado `contraste`**, e
o eixo de maior lift — o que o ramo `tematico` nomeia — **mudou em 16 de
35**. O estado é o máximo sobre 30 células ruidosas contra um limiar, e o
máximo de um conjunto ruidoso é enviesado para cima.

O veredito **ramifica** nesse estado: `veredito.py` monta dois blocos de
instrução diferentes conforme `contraste`. As condições **não leem `eixos`**
— nem lift, nem margem, nem `contraste`, nem `taxonomia_id`. Nesse ponto o
desacoplamento é literal e completo: **as 48 condições desta sessão seriam
byte a byte as mesmas se a lei da margem mudasse amanhã.**

### Onde ela se refuta

**Primeiro: o veredito já está mais desacoplado do que a tese supõe.** Sob a
v1.9.34 o catálogo é **6 `tematico` / 28 `valorativo` / 1 sem estado**. Em
todos os 28 `valorativo` — os quatro filmes desta amostra inclusive — o
`acima_da_margem` é falso em todas as células, e o CONTEÚDO do texto vem de
`assunto_compartilhado` e `eixo_maior_frequencia`, **os dois de
FREQUÊNCIA**. A própria §2.5 registra: *"o ramo `valorativo` nomeia o
`assunto_compartilhado`, que é uma afirmação de conteúdo real e vem de
FREQUÊNCIA, não de lift"*, com **8 de 35** mudando o eixo nomeado contra
**16 de 35** do lift. **O lift decide a ramificação nos 34 filmes com veredito,
mas escreve conteúdo em apenas 6.** O ganho da troca é o ramo, não a frase.

**Segundo: o "1,2pp" não é sobre o que as condições consomem.** Aquele
número é o delta máximo da **frequência por EIXO agregada no corpus** entre
n=2.866 e n=4.056 (SPEC §2.8). As condições não consomem frequência por
eixo — consomem o **texto do `tema` e do `exemplo_parafraseado`**, que são
saída do estágio [D], um estágio de LLM. **A estabilidade dessas strings sob
regeneração não está medida em lugar nenhum deste projeto** (o que está
medido é [D3], a rotulagem por eixo: 98,1%). O evento de cobertura que
produziu o 1,2pp **não re-rodou [D]** — estendeu a classificação. Citar 1,2pp
como a estabilidade do insumo das condições é **usar um número medido em
outra população**, que é a mesma falha que a Correção 2 de
`ESTUDO_MARGEM_20PP.md` apontou no "34%" da spec.

**Terceiro, e é o que a medição acrescentou: a troca não remove
instabilidade, ela a MOVE.** O veredito tem uma decisão instável e medida (o
ramo). As condições têm uma decisão instável e **não medida**: qual dos 6
temas vira condição, decidida pelo modelo, divergindo da ordem de frequência
em **14 de 16** e trocando entre execuções idênticas em **1 de 8**.

### A frase que sobrevive

**VISTO, com base medida:** a substituição **desacopla a frase visível do
estado binário de contraste**, que é a estatística menos estável do sistema,
e isso é um ganho real de arquitetura. Ela **não** ancora a frase numa
estatística medida como estável — ancora-a em strings de LLM cuja
estabilidade é desconhecida, e acrescenta uma escolha editorial nova. **O
argumento de arquitetura se sustenta pela metade, e a metade que se sustenta
vale menos hoje do que valeria antes da v1.9.34**, porque 28 dos 35 filmes
já publicam conteúdo derivado de frequência.

## 3.3 O que se perde — as garantias do veredito, uma a uma

| garantia | versão | herda? | o que acontece |
|---|---|---|---|
| `formato_invalido`, `digito`, `aspas`, `idioma`, `comprimento`, `nota_ou_score`, `escopo_generalizado`, `cliche` | v1.9.21 | **SIM, literal** | reuso direto; nenhuma redecisão |
| `tema_verbatim` (contra o `tema`) | v1.9.22 | **SIM** | e disparou 2 vezes em 48 — funcionando |
| **zero dígitos por CONSTRUÇÃO** | v1.9.21 | **NÃO** | a paráfrase precisa entrar no briefing (P4) e **2 dos 35 filmes têm algarismo arábico dentro dela** (MEDIDO). A validação `digito` deixa de ser redundância e vira defesa primária — e o §3[V] diz por extenso que a diferença entre as duas não é de grau |
| **disciplina de quantificador** | v1.2.3 / v1.9.22 | **NÃO** | o formato não tem slot. **MEDIDO: 0 de 48** condições carregam rótulo de frequência. Precisa ser reconstruída **na interface** (`rotulo_forca`), não no prompt |
| **anti-repetição por padrão sintático de abertura** | v1.9.22 | **NÃO** | 100% das condições abrem com a mesma fórmula por construção; a métrica precisa ser redefinida sobre o CORPO. Linha de base MEDIDA: 15 padrões distintos em 48, três maiores = 37,5% |
| **anti-cópia verbatim** | v1.9.22 | **PARCIAL** | a cópia MIGRA para a paráfrase. **MEDIDO: 20 de 48** copiam 3+ palavras de conteúdo em sequência do `exemplo_parafraseado`. Um `exemplo_verbatim` teria de ser construído |
| **anti-fabricação de contraste** | v1.9.21 | **NÃO SE APLICA** | e é uma perda de CONTEÚDO, não de validação: as condições não dizem se os grupos falam das mesmas coisas. O achado que **28 dos 35** filmes publicam some da página |
| **anti-spoiler** | v1.9.21 | **SIM, e mais exposto** | os temas já passaram por §3[D], mas as condições **parafraseiam o exemplo** em vez de nomear o eixo — mais superfície, mesma rede |
| **código decide O QUÊ** | §0 / v1.9.8 | **NÃO, no desenho testado** | MEDIDO: seleção de tema pelo modelo em 14 de 16. **Consertável em código**, e obrigatório antes de qualquer construção (§2.5) |
| **fallback determinístico** | v1.9.19/20 | **N/A** | não existe template de condição que não seja vazio; a rede é o próprio veredito |

**São quatro garantias a reconstruir do zero, uma a estender, e um achado de
produto a perder.**

---
---

# ENTREGA 4 — recomendação

## NÃO CONSTRUIR agora. E a razão não é a taxa de fabricação.

**O critério registrado dá PASSA em C1, C2 (estrito), C3, C4 e C5.** Se a
decisão fosse só o critério, ela seria "construir". **Ela não é**, e a razão
é que a medição encontrou duas coisas que o critério, escrito antes, não
sabia procurar — e uma delas é a mais séria do documento.

### As duas razões, em ordem de peso

**1. O formato apaga o PESO, e o produto já corrigiu essa falha duas vezes.**
`the-godfather` é 2 / 5 / 93 e recebe três condições de cada lado, com o
mesmo peso visual. É a infidelidade por omissão da v1.4.0 num canal novo —
a v1.4.0 a corrigiu na prosa, a v1.9.30 a corrigiu na ordem dos blocos, e o
formato de condição a reintroduz por construção, porque uma condicional
sobre o leitor não tem onde acomodar "a maioria". **O `rotulo_forca` é a
correção proposta e ela NÃO FOI TESTADA.** Enquanto não for, o estágio
troca uma frase que carrega quantificador e ressalva de amostra por seis
frases que não carregam nenhum dos dois. **MEDIDO: 0 de 48.**

**2. O defeito IMPRECISO da auditoria manual sobreviveu ao estágio
automatizado, limpo, nas duas execuções.** `napoleon`/batalhas passou em
todos os validadores mecânicos, inclusive no de discriminação que foi
desenhado para ele, porque o proxy é lexical e o defeito é semântico. E o
tema que o desmentiria foi descartado pelo próprio modelo nas duas rodadas.
**O validador difícil não fecha o caso difícil** — isso estava previsto como
possibilidade em §3.3 do desenho, e a medição confirmou no caso exato.

### O que o resultado NÃO diz, e precisa ficar escrito

Este é um resultado negativo **de prontidão, não de conceito**, e as duas
coisas se confundem com facilidade:

- **a taxa de fabricação é boa** — 0 em 48, e 89,6% de suporte direto;
- **a reprodutibilidade é boa** — 0,929, muito acima do 0,70 que reprovou a
  verificação binária;
- **o custo é irrelevante** — US$ 2,03 em 300 filmes com best-of-3, ~1/12 do
  que reprovou a verificação binária;
- **e as condições ganham do veredito num filme dos quatro**: em
  `hereditary`, o veredito não menciona os dois temas mais citados do grupo
  que é 80% da recepção, e as condições mencionam.

**Nada disso é o problema. O problema é que o formato perde o peso e o
validador difícil não fecha.** Um "não construir" que fosse lido como "a
ideia é ruim" seria uma leitura errada deste documento.

## Se o dono quiser construir mesmo assim: o que precisa acontecer antes

Em ordem, porque a ordem importa e o item 0 é bloqueante.

**0. A DECISÃO DE PRODUTO, e ela é anterior a todo o resto.** As condições
fazem o Espectro **RECOMENDAR** em vez de **RELATAR**. O §0 define o produto
como *"permitindo entender a recepção do filme"*; o §3[V] abre com *"não é
crítica, não é resenha, **não é recomendação** — é o mapa de ONDE as opiniões
divergem"*. *"Vale a pena se você…"* é uma recomendação condicional, e a
proveniência não a desfaz.

Isto é **mudança de natureza**, e precisa do mesmo tratamento que as duas
exceções deliberadas já registradas no §0 — o vocabulário HATERS/MIXED/FANS
e a política do meio: **um parágrafo próprio, com o trade-off escrito por
extenso, o escopo delimitado, e a via de reversão declarada.** Não pode
entrar como efeito colateral de um estágio novo. **Se esta decisão não for
tomada explicitamente, os itens abaixo não devem começar.**

**1. Mover a seleção de tema para o CÓDIGO.** O briefing entrega os N temas
já escolhidos, sem lista. Regra de seleção declarada (`mencoes_aproximadas`
decrescente, desempate pela ordem de publicação do bullet). **Sem isto, o
estágio viola a fronteira do §3[V] em 14 de 16.** Custo: pequeno, e é código
puro.

**2. Levar o `rotulo_forca` à tela e medir se ele resolve `the-godfather`.**
É a única correção proposta para a razão nº 1, e ela é de INTERFACE.
Enquanto não estiver medida, a razão nº 1 continua de pé.

**3. Construir `exemplo_verbatim`** (20 de 48 justificam) e **redefinir a
métrica de repetição sobre o corpo da condição** (linha de base medida: 15
padrões em 48).

**4. Rodar sobre os 35, com leitura humana dos 35 × 6.** Quatro filmes não
sustentam a decisão, e este documento diz isso desde o critério registrado.
A varredura de população inteira é a mesma exigência que o §3[V] se impôs
para a anti-fabricação nos 17 `valorativo`. **Custo medido: US$ 0,24 de LLM
e o tempo de leitura de 210 condições.**

**5. Decidir onde o achado `valorativo`/`tematico` passa a viver.** Ele
descreve 28 dos 35 filmes e as condições não o dizem. Se as condições
SUBSTITUEM o veredito, o produto para de publicar esse achado; se
CONVIVEM, a página ganha duas frases fazendo trabalhos diferentes e a
decisão é de leiaute.

## O caminho que este documento recomenda

**Manter o veredito. Reabrir as condições depois do item 0 e do item 1, e
com o `rotulo_forca` medido.** O desenho está pronto e testado em par; o que
falta não é desenho, é uma decisão de produto e duas correções nomeadas.

Este arco já reprovou a contagem por eixo, a verificação binária e o split
de `roteiro_estrutura`. **Este não é o mesmo tipo de reprovação:** aqueles
três foram reprovados porque a medição mostrou que não funcionavam. Este
funciona melhor do que a hipótese previa — e é reprovado por prontidão, com
a lista do que falta escrita acima e nenhum item dela impossível.

---

## Limite da amostra — a frase que acompanha toda conclusão acima

**Quatro filmes, oito execuções, 48 condições, uma leitura (a minha) para a
classificação de fidelidade.** Isso não estima taxa de catálogo. Com 0
fabricações em 48, o limite superior de 95% é ~6% — o dado é compatível com
até 1 em 17 condições sendo fabricada num catálogo de 35, e não com "zero
fabricação". A escolha dos quatro filmes foi **deliberadamente adversa**
(um MIXED dominante, um sem valência no rótulo, dois com desequilíbrio
extremo), o que torna os achados NEGATIVOS mais fortes e os POSITIVOS menos
generalizáveis — a amostra foi montada para achar defeito, então a ausência
de defeito nela pesa menos que a presença.

**E a taxa de fabricação medida aqui é sobre condições geradas por um
desenho que ainda escolhe temas pelo modelo.** Mover a seleção para o código
(item 1) muda a população de condições geradas e **invalida os 48 desta
sessão como linha de base** — a medição teria de ser refeita.

## Reprodução

Protótipo (`condicoes.py`), runner (`rodar.py`), saída bruta
(`rodada.json`) e o critério registrado vivem no scratchpad da sessão, não
no repositório — mesma política de `ESTUDO_MARGEM_20PP.md`. Nenhum arquivo
do projeto foi criado ou alterado além destes dois markdowns. O protótipo
importa `espectro24.veredito`, `espectro24.quantificador` e
`espectro24.qualidade` sem modificá-los; a régua de casamento por palavra de
conteúdo e prefixo de 5 é a de `veredito.palavras_de_conteudo`, reusada, não
reimplementada.
