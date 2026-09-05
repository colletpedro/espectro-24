# CONDIÇÕES DE DECISÃO — o desenho do estágio e dos validadores

**Documento de DESENHO, para aprovação. Nada aqui está implementado em
produção.** Nenhum arquivo de `resultado/` foi escrito, nenhum filme
regerado, `taxonomia_id`, lei de margem, cota e piso intocados, frontend
intocado. O protótipo que produziu os números da medição vive no scratchpad
da sessão, não em `src/` nem em `scripts/` — mesma política de
`ESTUDO_MARGEM_20PP.md` §Reprodução.

**A medição está no documento irmão,
[MEDICAO_CONDICOES_DE_DECISAO.md](MEDICAO_CONDICOES_DE_DECISAO.md).** Este
documento descreve o que FOI desenhado; aquele descreve o que aconteceu
quando rodou, e traz a recomendação. **Os dois se leem nesta ordem, e o
critério de sucesso foi registrado antes de qualquer geração.**

**Convenção herdada:** **MEDIDO** = número que saiu de código rodado nesta
sessão ou de documento anterior citado com a fonte. **VISTO** = leitura,
julgamento, argumento.

---

## 0. O que está sendo desenhado, e contra o quê

Uma exploração de design propôs substituir o VEREDITO (§3[V]) por CONDIÇÕES
DE DECISÃO:

```
Vale a pena se você...    quer um Napoleão íntimo, não o estadista
Talvez evite se você...   quer precisão histórica
```

A hipótese: o público-alvo do produto é quem ainda não assistiu e está
decidindo (§0, "Público-alvo"), e a condição serve melhor a essa decisão que
a descrição em terceira pessoa do veredito.

Isso exige um ESTÁGIO NOVO: converter **traço do filme** em **condição do
espectador**. A pergunta desta sessão é anterior à de construir: **ele pode
ser honesto?**

**A razão de a pergunta não ser trivial está medida.** Uma auditoria manual
do mockup do `napoleon-2023`, contra os temas publicados, achou **1 condição
fabricada e 1 imprecisa em 6** — um humano cuidadoso desenhando à mão errou
2 em 6. Os dois casos são reais e estão conferidos contra
`resultado/napoleon-2023.json` nesta sessão:

| defeito | condição do mockup | tema citado | o que o tema de fato diz |
|---|---|---|---|
| **FABRICADA** | *"não se incomoda com licença histórica"* | FANS *"Incentivo à pesquisa histórica"* | *"O filme despertou a curiosidade dos espectadores, levando-os a pesquisar sobre Napoleão e o contexto histórico por conta própria, o que foi um ponto positivo para eles."* — é um **efeito**, não tolerância a imprecisão. Inversão de sinal. |
| **IMPRECISA** | *"veio pelas batalhas e só por elas"* | FANS *"Qualidade das cenas de batalha"* | HATERS *"Batalhas decepcionantes"*: *"visualmente impressionantes, mas carecem de estratégia e tática"*. Os **três** grupos acham as batalhas bonitas. A condição honesta seria *"quer batalha com tática, não só espetáculo"*. |

Um estágio automatizado industrializaria essa taxa sobre 35 filmes hoje e
300 depois. O desenho abaixo existe para que a taxa seja mensurável antes de
ser paga.

---

## 1. O estágio: insumo, saída, schema

### 1.1 Posição no pipeline

```
[D] síntese por bucket ──►  buckets[].temas  ──►  [C] condições ──► resultado/<slug>.json
                                                        ▲
                                            ficha, share_real dos buckets
```

**Roda na PUBLICAÇÃO**, ~35 chamadas por regeneração de catálogo, nunca por
pageview. Mesma economia do §3[V].

**Depende de [D] e de mais nada.** Em particular **NÃO depende de [D3] nem
de `eixos`** — e essa é a diferença de arquitetura que a proposta traz. O
veredito consome `eixos.linhas[].por_bucket[]` (lift, `acima_da_margem`,
`contraste`); as condições consomem `buckets[].temas[]` (`tema`,
`exemplo_parafraseado`, `mencoes_aproximadas`, `n_reviews_analisadas`).
As consequências disso — boas e ruins — estão medidas na Entrega 3 do
documento irmão.

### 1.2 O que o estágio RECEBE — e a decisão que mais importa

**Decisão: o briefing carrega `tema` E `exemplo_parafraseado`, sempre, e
nunca só o rótulo.**

Isto não é preferência: é a aplicação direta de **P4 REVISADO (§2.7,
2026-08-31)**. Aquela revisão foi forçada por um caso real (`wonka`/[11], o
"künstlich" alemão) e estabeleceu que *"o que o leitor vê na tela é o par
tema + `exemplo_parafraseado`, e é a paráfrase que carrega a afirmação
específica. Julgar só contra a formulação curta do tema perde reviews que
sustentam o que o produto de fato afirma."*

O mesmo vale na direção da geração: **derivar condição só do rótulo produz
condição sem lastro**, e o caso `hereditary` prova por que — os temas FANS
são *"Atuações"*, *"Trilha sonora"*, *"Roteiro e história"*, rótulos **sem
valência nenhuma**. Deles, sozinhos, não se deriva "vale a pena se você…"
honestamente. Das paráfrases, sim: *"a performance intensa da atriz
principal, que consegue transmitir uma gama complexa de emoções"*. **A
valência mora na paráfrase, não no rótulo** — e é medido no documento irmão
que é exatamente de lá que o estágio a tira.

**Isso tem um preço, e ele é medido, não estimado — ver §4.1.**

**O briefing NÃO carrega:**

- **`eixos`, `lift`, `contraste`, `margem`** — nada da maquinaria da margem.
  Não por economia: o estágio não tem o que fazer com um estado binário de
  contraste, e recebê-lo só abriria a porta para o modelo insinuar a partir
  dele.
- **o veredito** — pelo mesmo motivo que [V] e [D2] não se leem: dois
  estágios que se leem produzem eco, não confirmação.
- **o TÍTULO do filme** — herdado literal do §3[V]: *"nomear o filme CONVIDA
  o modelo a usar o que ele sabe sobre o filme, e a invariante 1 proíbe
  contexto externo. Um briefing anônimo torna a fidelidade mais fácil de
  obedecer do que de violar."*
- **reviews brutas** — mesma fronteira de §D2 desde a v1.2.0.

### 1.3 Os ids de tema são LETRAS, e a razão é a garantia de dígito

Cada tema entra com um código `NEG-A`…`NEG-F`, `POS-A`…`POS-F`. **Letras, e
não números, exatamente para não introduzir algarismo na serialização** —
o §3[V] comprou caro a garantia "zero dígitos por construção" e um id
`POS-3` a jogaria fora por conveniência de notação.

O id é o que torna a ÂNCORA verificável por máquina (§2 abaixo): a condição
devolve o código do tema de onde saiu, e o código confere.

### 1.4 A serialização do briefing

Determinística, sem algarismo do lado do CÓDIGO, sem título:

```
QUEM RECOMENDA — TEMAS DISPONÍVEIS:
  [POS-D] Abordagem pessoal e íntima do personagem
       o que o grupo diz: O filme foi apreciado por focar nas inseguranças
       e na vida pessoal de Napoleão, apresentando-o como um homem comum
       com defeitos, em vez de um herói mitológico.
       força AUTORIZADA deste tema: alguns
  …
QUEM NÃO RECOMENDA — TEMAS DISPONÍVEIS:
  …
O MEIO-TERMO É O MAIOR GRUPO DA RECEPÇÃO. O peso dele é informado por fora,
pelo sistema — não escreva número.
```

`força AUTORIZADA` vem de `quantificador.fracao_e_rotulo(mencoes,
n_analisadas)` — **calculada em código**, como todo rótulo de quantidade
deste projeto desde a v1.2.3.

**`medianas` não produz condição, e a regra é a do veredito, não uma nova:**
o meio nunca é um dos dois lados. Quando ele é o bucket DOMINANTE, entra um
**prefixo de código** (`prefixo_de_codigo`, §3[V]) informando o peso —
é o único algarismo do bloco e ele nunca passa pelo modelo. `napoleon-2023`
(45% no meio) cai aqui.

### 1.5 O que o estágio DEVOLVE — schema

```json
"condicoes": {
  "vale_a_pena": [
    {"texto": "quer um Napoleão íntimo, não o estadista",
     "tema_origem": "POS-D",
     "bucket_origem": "positivas",
     "tema_texto": "Abordagem pessoal e íntima do personagem",
     "rotulo_forca": "alguns"}
  ],
  "talvez_evite": [ … ],
  "prefixo_codigo": "O meio-termo é o maior grupo da recepção (~45% das notas). ",
  "origem": "llm" | "abstencao" | "template_fallback",
  "provider": "gemini", "modelo": "gemini-3.7-flash",
  "n_candidatos": 3, "n_chamadas": 3, "indice_escolhido": 0,
  "motivo": "melhor_entre_limpos" | "menor_severidade" | "template_fallback",
  "candidatos": [{"indice": 0, "n_flags": 0, "flags": [], "n_condicoes": 6}],
  "flags": [],
  "uso": {"prompt_tokens": 0, "completion_tokens": 0,
          "cache_hit_tokens": 0, "cache_miss_tokens": 0},
  "latencia_s": 0.0,
  "spec_version": "…"
}
```

**`tema_origem` é a LINHA DE PROVENIÊNCIA, e ela é obrigatória e
verificável** — não é telemetria. `tema_texto` e `rotulo_forca` são
preenchidos pelo CÓDIGO a partir do id, nunca pelo modelo: o modelo devolve
o código, o código resolve o resto. Assim a proveniência não pode divergir do
que o produto publica ao lado.

**`rotulo_forca` precisa chegar à TELA.** É a única forma de a condição não
apagar a diferença entre um tema de 28 de 40 e um de 5 de 40 — os dois
renderizam idênticos sem ele. **Medido no documento irmão: o modelo não
escreve quantificador sozinho (1 de 48 condições).** Quem implementar isto e
deixar `rotulo_forca` fora da tela terá desfeito, num estágio novo, a
disciplina de quantificador que as v1.2.2, v1.2.3 e v1.9.22 custaram três
versões para estabelecer.

**Listas VAZIAS são saída válida** (`origem: "abstencao"`). Ver invariante 5.

---

## 2. As invariantes do prompt

Numeradas para casar com as do §3[V] onde a correspondência existe. As que
não têm correspondência estão marcadas **NOVA**.

1. **Papel e público.** Escreve para quem ainda não assistiu e está
   decidindo. A condição descreve o **LEITOR**, não o filme: *"quer um
   retrato íntimo, não o estadista"*, nunca *"o filme é íntimo"*.
2. **Fidelidade absoluta ao briefing.** Só existe o que está nos temas.
   PROIBIDO introduzir assunto, adjetivo avaliativo, nome de pessoa ou
   informação de enredo que não esteja ali. *(= invariante 2 do §3[V].)*
3. **ÂNCORA OBRIGATÓRIA — NOVA.** Toda condição cita um código de tema, e o
   texto tem de nomear o assunto daquele tema. **Condição que não puder ser
   ancorada não deve ser escrita.** Validador em §3.1.
4. **NÃO INVERTER O SINAL — NOVA.** A condição não pode afirmar mais do que
   o tema afirma. Tema que descreve um EFEITO não vira APROVAÇÃO de outra
   coisa; tema que descreve INCÔMODO não vira TOLERÂNCIA; tema que diz
   *"bonito mas sem tática"* não vira *"bonito"*. Validador em §3.2.
5. **ABSTENÇÃO — NOVA, e é a invariante mais importante deste desenho.** Se
   um lado não tiver tema do qual uma condição honesta se derive, a lista
   daquele lado sai **VAZIA**. Lista vazia é resposta válida e preferível a
   condição inventada. **NÃO complete cota.**
   > É a aplicação da política de omissão autorizada da v1.4.1, que §3[V] já
   > invoca para `assunto_compartilhado` sem tema: *"não se inventa texto
   > para tapar o buraco — preencher com genérico é pior do que não
   > preencher"*.
6. **Zero dígitos.** Nenhum algarismo. *(= invariante 5 do §3[V], mas **sem
   a garantia por construção** — ver §4.1.)*
7. **Anti-spoiler.** Nada de reviravolta, final, morte de personagem ou
   mecanismo central. Os temas já passaram pelo filtro de §3[D]; **use-os
   como estão, não os expanda.** *(= invariante 6 do §3[V].)*
8. **Escopo.** PROIBIDO "os críticos", "o consenso", "a recepção do filme",
   "o público". *(= invariante 7 do §3[V], reusada literal.)*
9. **Palavras suas.** PROIBIDO copiar tema ou paráfrase palavra por palavra.
   Sem aspas. *(= regra 7 do §3[V], **estendida à paráfrase** — ver §4.2.)*
10. **Forma.** No máximo **quatorze palavras** por condição, pt-BR, começa em
    minúscula, continua a abertura sem repeti-la, no máximo **três condições
    por lado**.
11. **Quantificador.** O `rotulo_forca` é do CÓDIGO e vai ao lado da
    condição na tela. O modelo **não escreve rótulo de frequência nenhum** —
    nem mais forte, nem mais fraco. É a v1.9.22 aplicada a um formato que
    não tem onde acomodar o rótulo dentro da frase.

**O que NÃO tem equivalente aqui, e precisa ser dito:** a invariante 3 do
§3[V] (anti-fabricação de contraste) **não se traduz**. As condições nunca
afirmam se os grupos falam das mesmas coisas ou de coisas diferentes — o
formato não tem onde dizê-lo. Isso não é uma invariante a menos por
economia: é **um achado do produto que desaparece da página**. Ver Entrega 3
do documento irmão.

---

## 3. Os dois validadores mecânicos — o coração da entrega

Todos rodam em CÓDIGO, sobre a saída já parseada, antes de qualquer critério
de qualidade. **Validação vem antes de seleção**, pela razão do §3[V]: *"um
texto que mente com riqueza continua mentindo"*.

### 3.1 VALIDADOR 1 — ÂNCORA OBRIGATÓRIA

Três sub-regras, todas decidíveis por contagem.

**1a — pertinência de conjunto.** `tema_origem` tem de ser um id da lista de
temas **daquele filme**. Falha ⇒ `ancora_inexistente`. É a parte forte e a
única com zero folga: é teste de pertinência, não proxy.

**1b — casamento lexical com o tema citado.** Sem isto o código é carimbo:
qualquer condição poderia citar qualquer id. A regra de casamento é
**herdada da v1.9.22, não inventada**, e a lição vem escrita junto dela:

> *"Casamento por PALAVRAS DE CONTEÚDO, nunca por substring do `tema`.
> Substring exata recompensaria copiar a string verbatim e a saída
> degeneraria em citação empilhada."* (§3[V], guarda-corpos da chave
> primária)

Concretamente, reusando `veredito.palavras_de_conteudo` sem alteração:
normaliza (NFKD sem diacríticos, minúsculas, quebra em não-letras), descarta
stopwords e tokens com menos de 4 caracteres, compara por **prefixo de 5**.
Uma condição está ancorada quando compartilha `min(2, |palavras da âncora|)`
prefixos com o tema citado.

**A âncora é o conjunto `tema` + `exemplo_parafraseado`**, e isso é P4
REVISADO (§2.7) aplicado à geração, como em §1.2.

Falha ⇒ `ancora_nao_verificavel`.

**1c — cópia literal REPROVA, não premia.** Reuso direto de `tema_verbatim`
(§3[V]): condição cujo texto contenha a sequência completa de palavras de
conteúdo de um `tema` de 3+ palavras é reprovada. **Estendida à paráfrase**
pela invariante 9 — e §4.2 mostra, com número, por que a extensão é
obrigatória e não cosmética.

Falha ⇒ `tema_verbatim` / `exemplo_verbatim`.

#### TESTE EM PAR — os dois casos reais do mockup

| | condição | tema citado | FLAGS |
|---|---|---|---|
| **reprova** | *"não se incomoda com licença histórica"* | `POS-F` *Incentivo à pesquisa histórica* | `ancora_nao_verificavel`, `sem_discriminacao` |
| **passa limpa** | *"quer um Napoleão íntimo, não o estadista"* | `POS-D` *Abordagem pessoal e íntima do personagem* | **nenhuma** |

**MEDIDO, rodado nesta sessão contra `resultado/napoleon-2023.json`.**

**Por que a fabricada cai:** as palavras de conteúdo da condição são
`incomoda`, `licenca`, `historica`. O tema + paráfrase citado tem
`incentivo`, `pesquisa`, `historica`, `despertou`, `curiosidade`,
`espectadores`, `napoleao`, `contexto`, `propria`, `positivo`. **Um prefixo
em comum (`histor`), e a regra exige dois.** A condição fabricada não é
reprovada por alguém ter adivinhado que ela é falsa — é reprovada porque
**não consegue nomear o tema que diz estar citando**, que é a forma
mecânica da mesma coisa.

**Por que a correta passa:** `intimo` e `napoleao` casam; `intim` é
exclusivo do tema `POS-D` no filme inteiro. Nenhuma flag. **Sem esta metade
o validador seria armadilha** — reprovaria tudo e empurraria o filme para o
fallback, que é o custo caro e medido dos falsos positivos no §3[V].

### 3.2 VALIDADOR 2 — INVERSÃO DE SINAL

**A parte honesta primeiro: a inversão de sinal NÃO é decidível por máquina
no caso geral.** Detectá-la exigiria casamento por SIGNIFICADO entre a
condição e o tema, e este projeto já registrou essa fronteira, no mesmo
estágio, com a mesma conclusão:

> *"`tema_ausente` detecta EIXO, não tema. O eixo tem vocabulário fechado e
> um `tema` não tem; checar tema a tema exigiria casamento por SIGNIFICADO,
> que só um segundo LLM faz — e este projeto não põe LLM para julgar saída
> de LLM."* (§3[V], "O que estas validações declaradamente não pegam")

O que É decidível são **duas condições NECESSÁRIAS**. Elas não provam que a
condição está certa; reprovam duas formas concretas de estar errada, e as
duas foram observadas na auditoria manual.

#### 2a — DISCRIMINAÇÃO (pega a imprecisão por compartilhamento)

Quando o assunto da condição também é assunto de outro bucket, a condição
precisa carregar **pelo menos uma palavra que separe a leitura citada da
leitura do outro grupo**.

- "mesmo assunto" = dois temas de buckets diferentes compartilham ≥2
  prefixos de conteúdo — **a mesma régua de 1b, reusada, não um limiar
  novo**;
- "palavra que separa" = prefixo presente no tema citado e **ausente de
  todos** os temas de mesmo assunto dos outros buckets.

Falha ⇒ `sem_discriminacao`.

#### 2b — CORROBORAÇÃO CRUZADA (pega o endosso derivado de queixa)

Uma condição do lado **vale a pena** ancorada num tema de valência lexical
só NEGATIVA passa **apenas** se existir, em outro bucket, um tema do mesmo
assunto com valência POSITIVA ou mista. Simétrico para o outro lado.

É o que torna **legítima** a inversão escrita nos temas de `perfect-days`
(*"Ritmo lento e tédio"* ↔ *"Ritmo lento e contemplativo"*) e **ilegítima** a
inversão inventada. A valência sai de um **léxico fechado e curto**, com a
convenção de marcador do `_MARCADORES_EIXO` da v1.9.22 (`*` = prefixo, sem
`*` = token inteiro — a correção do bug real em que `tom` casava dentro de
"tomam"). Tema com marcadores dos dois lados devolve `mista` e a regra
**abstém-se** em vez de decidir: a maioria das paráfrases deste corpus é
escrita de forma equilibrada, e uma regra que decidisse ali inventaria sinal.

Falha ⇒ `sinal_sem_corroboracao`.

#### TESTE EM PAR

**Par principal — o caso real do mockup, `napoleon-2023`:**

| | condição | tema citado | FLAGS |
|---|---|---|---|
| **reprova** | *"veio pelas batalhas e só por elas"* | `POS-C` *Qualidade das cenas de batalha* | `ancora_nao_verificavel`, `sem_discriminacao` |
| **passa limpa** | *"quer batalha com tática, não apenas espetáculo"* (lado **talvez evite**) | `NEG-F` *Batalhas decepcionantes* | **nenhuma** |

A correção que a auditoria manual propôs passa limpa: `tatica` é exclusiva
de `NEG-F` contra `MED-A` *Batalhas visualmente impressionantes* e `POS-C`.

**Par isolado de 2a** — porque no par acima a âncora também dispara, e um
validador precisa ser exercitado sozinho:

| | condição | tema citado | FLAGS |
|---|---|---|---|
| **reprova** | *"gosta de um ritmo lento"* | `perfect-days` `POS-D` *Ritmo lento e contemplativo* | `sem_discriminacao` |
| **passa limpa** | *"quer um ritmo contemplativo, quase meditativo"* | mesmo `POS-D` | **nenhuma** |

Duas condições sobre o **mesmo tema**, uma reprovada e outra limpa: a
diferença é a única que importa — a primeira usa só as palavras que os dois
grupos compartilham (*"Ritmo lento e tédio"* nas HATERS diz exatamente
"ritmo lento"), a segunda carrega a palavra que decide qual das duas
leituras o leitor está comprando.

**Par isolado de 2b:**

| | condição (lado **vale a pena**, tema NEGATIVO) | filme | FLAGS |
|---|---|---|---|
| **passa limpa** | *"topa lentidão e ausência de eventos"* ← `NEG-A` *Ritmo lento e tédio* | `perfect-days-2023` | **nenhuma** — corroborado por `POS-D` *Ritmo lento e contemplativo* (valência positiva) |
| **reprova** | *"topa que o filme se arraste sem sustos"* ← `NEG-A` *Ritmo lento e tédio* | `hereditary` | `sinal_sem_corroboracao` (+ âncora e discriminação) — o único irmão é `MED-A` *Ritmo lento e longa duração*, também negativo |

**MEDIDO, os seis casos rodados nesta sessão.** A mesma forma de condição,
sobre o mesmo tema nominal, passa num filme e reprova no outro — e o que
decide é o DADO do filme, não a frase.

### 3.3 O que os dois validadores DECLARADAMENTE não pegam

**A condição que empresta palavras suficientes para ancorar E discriminar, e
ainda assim afirma outra proposição.** É a classe do `napoleon`/pesquisa
histórica reescrita com mais cuidado — por exemplo *"não se incomoda que o
filme desperte mais curiosidade histórica do que precisão"*, que ancora
(`curiosidade` + `historica`) e discrimina (`curiosidade` é exclusiva de
`POS-F`), e continua convertendo um efeito em endosso.

Contra ela restam a instrução do prompt e a **leitura humana do aceite** — a
mesma rede, e a mesma admissão, que o §3[V] já faz para `tema_ausente`.
**Isto não é um buraco que uma versão futura fecha por esforço; é a
fronteira do que se decide sem julgar significado.**

E há uma segunda folga, medida e não prevista no desenho: **2a é um proxy
LEXICAL sobre uma propriedade SEMÂNTICA**, e no `napoleon` ele deixou passar
exatamente a condição que a auditoria manual reprovou. Está medido, com o
texto, na Entrega 2 do documento irmão — e é o achado que mais pesa contra
construir.

### 3.4 As validações herdadas sem redecisão

`digito`, `aspas`, `escopo_generalizado` (a lista literal de §3[V]),
`nota_ou_score`, `cliche` (`dados/blocklist_resenha.txt`), `idioma`,
`comprimento`, `formato_invalido`. **Reusadas, não reescritas.**

---

## 4. O que o desenho NÃO consegue herdar — medido, não suposto

### 4.1 A garantia "zero dígitos por CONSTRUÇÃO" cai

O §3[V] a comprou serializando só rótulos: *"o modelo não pode copiar um
número que nunca viu"*. Aqui o briefing **precisa** carregar o
`exemplo_parafraseado` (§1.2, P4), e a paráfrase não é limpa de algarismo.

**MEDIDO — varredura dos 35 `resultado/*.json`, todos os buckets, os campos
`tema` e `exemplo_parafraseado`:** **2 filmes** têm algarismo arábico dentro
da paráfrase.

| filme | bucket | trecho |
|---|---|---|
| `friday-the-13th-2009` | medianas | *"…típica do terror dos anos **2000**, o que chegou a incomodar alguns."* |
| `im-still-here-2024` | positivas | *"Os primeiros **30** minutos foram amplamente elogiados…"* |

A validação `digito` em código continua e passa a ser a **defesa primária**,
não a redundância que o §3[V] a declara ser. Quem implementar isto precisa
saber que trocou uma garantia por uma checagem — e o §3[V] diz por extenso
que a diferença entre as duas não é de grau.

### 4.2 A cópia verbatim MIGRA do tema para a paráfrase

`tema_verbatim` guarda o `tema`. Com a paráfrase no briefing, a cópia se
muda para ela.

**MEDIDO sobre as 48 condições geradas: 20 de 48 copiam 3 ou mais palavras
de conteúdo EM SEQUÊNCIA do `exemplo_parafraseado`**, e o `tema_verbatim`
existente pegou 2.

É literalmente o padrão que o §3[V] v1.9.23 registrou como observação de
método: *"a cada correção, a repetição MIGRA de dimensão, e a métrica
vigente captura exatamente a dimensão que acabou de ser consertada"*. Por
isso a invariante 9 estende a regra à paráfrase **antes** de o estágio
existir, em vez de depois de a leitura achar o defeito.

### 4.3 A disciplina de quantificador não tem onde morar na frase

**MEDIDO: 1 de 48 condições carrega alguma construção do mapa de
quantificador — e essa uma é *"momentos de choque **raros**"*, copiada do
próprio tema, que descreve a frequência dos sustos NO FILME e não o tamanho
do grupo. Na prática, ZERO de 48.** O
formato "Vale a pena se você…" é uma condicional sobre o LEITOR e não tem
slot para "a maioria". O `rotulo_forca` na tela (§1.5) é a compensação
desenhada; ela é uma decisão de INTERFACE que o dono precisa aprovar, não
algo que o estágio resolva sozinho.

### 4.4 A métrica de repetição estrutural precisa ser refeita do zero

`padrao_de_abertura` (v1.9.22) mede o núcleo do primeiro sintagma nominal.
Aqui **100% das condições abrem com a mesma fórmula por construção** — a
métrica devolveria um padrão único e seria inútil. Ela teria de ser
redefinida sobre o CORPO da condição.

**MEDIDO sobre as 48:** 15 padrões distintos no corpo, os três maiores
cobrindo 18 (37,5%) — `busca` 8, `aprec` 5, `valor` 5. Comparável ao 7-em-35
que a v1.9.22 tratou como defeito, mas **não é o mesmo instrumento** e não
deve ser lido como se fosse.

---

## 5. Seleção entre candidatos, retry e fallback

**Best-of-N com a mesma mecânica do §3[V], reproduzida e não reusada** —
`selecao_narrativa` está acoplado a três movimentos e não se aplica.

- **eliminação por flag primeiro**, sempre;
- **chave primária: COBERTURA DE TEMAS distintos citados**, com teto de 3
  por lado — o análogo direto da "informatividade ancorada", e pela mesma
  razão registrada: a primeira ideia natural ("o mais curto") otimiza na
  direção do defeito;
- **secundária: menos palavras**; empate total, primeiro índice.

**Retry direcionado** com as flags explicadas, e **fallback**:

1. nenhum candidato limpo ⇒ retry com as flags nomeadas;
2. esgotado ⇒ **`origem: "abstencao"`, listas vazias, e o VEREDITO
   determinístico atual permanece na posição**.

**Não existe template determinístico de condição, e é decisão de desenho:**
um template de condição seria "Vale a pena se você gosta de X" sobre o eixo,
que é a frase vazia que a v1.9.21 gastou uma versão inteira para matar. **A
rede do estágio de condições é o veredito**, não um template novo.

---

## 6. Custo de desenho, e o que fica pendente do dono

O que este documento **não** decide, e não pode:

1. **As condições fazem o produto RECOMENDAR em vez de RELATAR.** O §0 fecha
   com *"permitindo entender a recepção do filme"*, e o §3[V] abre com *"não
   é crítica, não é resenha, **não é recomendação**"*. "Vale a pena se
   você…" é uma recomendação condicional. Isso é **mudança de natureza**, e
   precisa do mesmo registro explícito que a exceção do backdrop e a do
   vocabulário HATERS/MIXED/FANS receberam — no §0, por extenso, com o
   trade-off escrito, não como efeito colateral de um estágio novo.
2. **`rotulo_forca` na tela** (§1.5, §4.3).
3. **Se o achado `valorativo`/`tematico` sai da página** (§2, nota final).

---

*A medição deste desenho — taxa de fabricação, reprodutibilidade,
`hereditary`, custo, a comparação com o veredito e a recomendação — está em
[MEDICAO_CONDICOES_DE_DECISAO.md](MEDICAO_CONDICOES_DE_DECISAO.md).*
