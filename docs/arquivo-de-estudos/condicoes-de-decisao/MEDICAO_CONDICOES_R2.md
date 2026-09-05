# CONDIÇÕES DE DECISÃO — rodada 2: as duas correções, medidas

**Estudo de VIABILIDADE. Nada implementado em produção.** `git status` sem
diff em `resultado/`, `src/`, `scripts/`, `tests/`, `frontend/` e `SPEC.md`
durante toda a sessão. Nenhum filme regerado, `taxonomia_id`, lei de margem,
cota e piso intocados. **Suíte: 1.591 passaram antes e 1.591 depois.**

Documentos anteriores: [DESENHO_CONDICOES_DE_DECISAO.md](DESENHO_CONDICOES_DE_DECISAO.md)
(desenho) e [MEDICAO_CONDICOES_DE_DECISAO.md](MEDICAO_CONDICOES_DE_DECISAO.md)
(rodada 1, reprovação por prontidão). Esta rodada executa as três correções
que aquela recomendação nomeou.

**Convenção:** **MEDIDO** = número que saiu de código rodado nesta sessão ou
de documento anterior citado com a fonte. **VISTO** = leitura, julgamento.

**Chamadas de LLM: 33.** Provider `gemini`, modelo `gemini-3.7-flash` — os
do estágio `veredito` em `config.py`, sem override.

**As 48 condições da rodada 1 estão INVALIDADAS como linha de base**, como
aquele relatório previu: a população gerada mudou. Onde a comparação entre
rodadas aparece, ela é feita **re-validando a rodada 1 sob os validadores da
rodada 2** — nunca comparando números medidos com réguas diferentes.

---

## Decisões e critério — REGISTRADOS ANTES DE QUALQUER GERAÇÃO

### A regra de seleção (Correção 1) — a pergunta do briefing tinha uma resposta medível

O briefing pedia para avaliar se ordenar por `mencoes_aproximadas` (número
decidido pelo LLM da síntese, com erro conhecido) é melhor ou pior que usar
a ordem de publicação do bullet.

**MEDIDO, 105 buckets dos 36 JSONs de `resultado/`: a ordem publicada de
`buckets[].temas` é `mencoes_aproximadas` DECRESCENTE em 105 de 105.** Zero
exceções. **40 de 105** buckets têm empate de `mencoes`, e neles a ordem
publicada é o único desempate existente.

**As duas opções não são duas regras — são a mesma seleção**, e a segunda é
um superconjunto da primeira. Escolher "ordem de publicação" não escapa de
`mencoes_aproximadas`: **herda-o em silêncio**.

**REGRA REGISTRADA: os N primeiros de `buckets[].temas`, na ordem publicada.
N = 3 por lado.** Três razões:

1. **Não há fuga.** A objeção do briefing é correta (§10: `wonka` com
   `mencoes` = 6 onde o texto sustenta 1), e nenhuma das duas opções a
   evita.
2. **A alternativa que existe é pior, e está medida.** Ordenar pela
   frequência do EIXO trocaria um número ruim por um número de **outra
   população**: §10 mediu que em 5% dos bullets a frequência do tema excede
   a do próprio eixo em mais de 20pp, com `avengers-endgame` publicando
   barra de 45% num eixo de contagem **zero** naquele bucket.
3. **A razão positiva, e é ela que decide: consistência com a página.** Os
   bullets já saem nessa ordem, logo abaixo, na mesma tela. Uma régua
   diferente poria **duas ordenações divergentes da mesma evidência** na
   mesma página. Entre um ranking imperfeito usado uma vez e dois rankings
   imperfeitos que se contradizem, o primeiro é estritamente melhor.

### O critério (repetido da rodada 1, sem afrouxar)

C1 fabricação: **corte em ZERO**. C2 generalização excessiva: **12,5%** (a
taxa que §10 mediu nos bullets). C3 reprodutibilidade: **0,80**. C5:
validadores **em par**. C6: `napoleon`/batalhas. C7: abstenção.

> **Registrado ANTES, e é a ressalva que impede uma vitória falsa:** com a
> seleção em código, `tema_origem` passa a ser determinístico por
> construção, então **C3 vira quase tautológico**. A métrica que vale nesta
> rodada é a do TEXTO; o Jaccard de id fica só como conferência de que a
> seleção realmente ficou determinística. **Não se declara vitória em C3 com
> um número que a própria correção tornou trivial.**

### A calibração do `exemplo_verbatim` (Correção 3), feita sobre dado da rodada 1

**MEDIDO — maior sequência de palavras de conteúdo copiada do
`exemplo_parafraseado` nas 48 condições da rodada 1:**

| sequência | 1 | 2 | 3 | 4 | 5+ |
|---|---:|---:|---:|---:|---:|
| condições | 8 | 20 | 15 | 5 | 0 |

**Teto escolhido: 4.** Em 3, o validador reprovaria 20 de 48 (41,7%), e a
leitura mostra que a maioria é **enumeração sem sinônimo disponível** —
*"fotografia figurinos cenários"*, *"erros datas eventos"*, *"conquistas
militares políticas"*, *"silêncios planos longos"*. Reprovar isso é o falso
positivo caro que o §3[V] mediu três vezes na primeira geração dos 35.

Em 4 reprova 5 de 48 (10,4%), e os cinco são reconhecivelmente a frase de
outra pessoa. **O que se herda da v1.9.22 é a FORMA do argumento, não o
número:** `tema_verbatim` fixou o corte onde *"não é copiável, é a única
forma de nomeá-lo"* deixa de valer. Num rótulo isso acontece em 3; numa
paráfrase de frase inteira, em 4.

### A amostra — 10 filmes, e o que cada novo cobre

| filme | share | por que entrou |
|---|---|---|
| `the-godfather` | 2/5/93 | adverso da rodada 1 |
| `napoleon-2023` | 22/45/33 | adverso — MIXED dominante, o caso C6 |
| `hereditary` | 6/14/80 | adverso — temas FANS sem valência no rótulo |
| `perfect-days-2023` | 2/7/92 | adverso — a inversão de valor escrita nos temas |
| `cats-2019` | 86/7/7 | **distribuição invertida** e **`tematico`** |
| `anatomy-of-a-fall` | 2/10/88 | **`tematico` em distribuição NORMAL** — separa o efeito do estado do da distribuição |
| `joker-folie-a-deux` | 46/33/21 | o mais equilibrado com HATERS na frente |
| `friday-the-13th-2009` | 33/41/26 | o mais equilibrado do catálogo; 2º MIXED dominante |
| `wonka` | 15/34/50 | **o filme do pior erro de `mencoes` medido** (§10) e dois buckets `reduzido` |
| `im-still-here-2024` | 1/4/96 | o único filme com **algarismo arábico** num `exemplo_parafraseado` de bucket que alimenta condição |

3 `tematico` / 7 `valorativo` · shares de 1% a 93% · 2 com MIXED dominante ·
3 com bucket reduzido · 1 invertido. **Continua sendo 10 de 35.**

### VARIANTE B — o par obrigatório, declarada antes de rodar

**Previsão registrada:** o tema HATERS *Batalhas decepcionantes* é o 6º do
bucket (6/40), **não entra** no top-3, e o tema FANS *Qualidade das cenas de
batalha* é o 3º (7/40) e **entra** — então a Correção 1 **não** conserta C6.

Braço B, também em CÓDIGO: se um tema selecionado tem no bucket oposto um
tema de mesmo assunto não selecionado, esse irmão é **acrescentado** (nunca
substitui — precedente direto do §2.5: *"a lista tem no máximo 5 entradas e
no mínimo 2, e o número de entradas é informação, não defeito de
preenchimento"*). Calculado **uma vez** sobre a seleção A, nunca em cascata:
iterar tornaria a saída dependente da ordem de varredura.

---
---

# RESULTADOS

## 1. Correção 1 — a seleção saiu do modelo

**MEDIDO:** o modelo não escolhe mais nada. Na rodada 1 a escolha divergia
da ordem de frequência em **14 de 16**; agora não há escolha a divergir.

**E a regra dodgeia a maior parte do erro conhecido de `mencoes` — MEDIDO,
não suposto.** Aplicando a regra top-3 aos **5 bullets que §10 classificou
como generalização excessiva**:

| caso §10 | bucket | ordem | menções | seria selecionado? |
|---|---|---:|---:|---|
| `wonka` — *Fotografia e efeitos visuais criticados* | negativas | 3 | 6/32 | **não** |
| `cats-2019` — *Experiência de visualização desconfortável* | negativas | 3 | 10/40 | **não** |
| `talk-to-me-2022` — *Diálogos e tom juvenil artificiais* | negativas | 4 | 5/40 | **não** |
| `napoleon-2023` — *Batalhas visualmente impressionantes* | medianas | 0 | 15/40 | **não** — medianas nunca alimenta condição |
| `interstellar` — *Fotografia e efeitos visuais deslumbrantes* | positivas | 2 | 11/40 | **SIM** |

**4 de 5 ficam de fora, e o mecanismo não é sorte:** a inflação de §10 é uma
contagem PEQUENA que ficou grande demais (*"uma review individual virou tema
de grupo com contagem 6"*), e contagem pequena não entra no top-3. **Mas
`interstellar` mostra que não é garantia** — e o defeito dele mora no
EXEMPLO (a especificidade do buraco negro, *"acrescentada invertendo o sinal
da única evidência disponível"*), que é justamente o que o briefing das
condições precisa carregar.

**Limitação registrada:** a condição herda integralmente o erro de
`mencoes_aproximadas`. A seleção não ficou correta — ficou **auditável**,
que é o que a Correção 1 pede.

## 2. Correção 2 — `rotulo_forca` NÃO resolve o desequilíbrio, e isso está medido

O campo entra no schema, resolvido por
`quantificador.fracao_e_rotulo(mencoes_aproximadas, n_reviews_analisadas)`,
nunca escrito pelo modelo, e **suprimido** nos buckets cujo `estado_piso`
proíbe quantificador (§3[C3]: `sem_numero`, `sem_quantificador`,
`sem_analise`).

### O que ele faz: funciona

Dentro de uma coluna ele distingue o que precisa distinguir. `the-godfather`
sai com *a maioria* (28/40), *cerca de metade* (22/40) e *muitos* (18/40) no
lado FANS; `napoleon` sai com três *alguns* (8, 8, 7 de 40) do lado FANS e
*muitos, muitos, alguns* do lado HATERS.

### O que ele NÃO faz, e é a razão nº 1 da reprovação anterior

**MEDIDO sobre os 35 filmes publicados, antes de rodar qualquer coisa:**

| | |
|---|---:|
| filmes em que o `rotulo_forca` do topo do lado **minoritário** é **igual ou mais forte** que o do majoritário | **18 de 35 (51%)** |
| … entre os 16 filmes com diferença de share ≥ 80pp | **8 de 16** |

| filme | share min / maj | rótulo minoritário | rótulo majoritário |
|---|---|---|---|
| `cidade-de-deus` | 1 / 96 | *muitos* | *muitos* |
| `interstellar` | 2 / 92 | *muitos* | *muitos* |
| `hereditary` | 6 / 80 | *muitos* | *muitos* |
| `aftersun` | 3 / 88 | *muitos* | *muitos* |
| `napoleon-2023` | 22 / 33 | *muitos* | ***alguns*** |

**Isto é estrutural, não amostral.** `rotulo_forca` é `mencoes / n_analisadas`
**DENTRO** do bucket; o desequilíbrio é **ENTRE** buckets. Um denominador
que é sempre ~40 não pode carregar a diferença entre 2% e 93% da recepção —
**a informação não está na razão.** Em `napoleon` o rótulo chega a apontar
para o lado errado: HATERS (22% das notas) recebe *muitos* e FANS (33%)
recebe *alguns*, porque a concordância interna do grupo pequeno é maior.

> **REPROVAÇÃO DA CORREÇÃO 2, como o briefing pediu que fosse reportada:**
> `rotulo_forca` **não resolve** a razão nº 1. Ele é necessário e deve entrar
> — resolve outra coisa, a força **dentro** da coluna —, mas a razão nº 1
> continua **aberta** com ele.

### Item 3 — o que carregaria o peso melhor (considerado, NÃO implementado)

**(a) Prefixo de peso por lado, escrito em CÓDIGO.** Análogo direto do
`prefixo_de_codigo` do §3[V], que já concatena *"O meio-termo é o maior
grupo da recepção (~45% das notas)"* fora da saída do modelo. Custo: uma
função. É o **mínimo** que fecha a razão nº 1, porque põe o número que falta
exatamente onde ele falta.

**(b) Número ASSIMÉTRICO de condições por lado, decidido em código.** É a
solução da v1.4.0 (profundidade proporcional ao peso) aplicada a este
formato. **MEDIDO — regra ilustrativa (3 ao lado de maior share; ao outro,
`round(3 × menor/maior)`, piso 1), nos 35:**

| alocação evite / vale | filmes |
|---|---:|
| 1 / 3 | **31** |
| 2 / 3 | 1 (`napoleon-2023`) |
| 3 / 2 | 1 (`friday-the-13th-2009`) |
| 3 / 1 | 2 (`joker-folie-a-deux`, `cats-2019`) |
| **total** | **35** |

**Nenhum dos 35 sai simétrico**, que é exatamente o ponto. O custo é real e
precisa de decisão do dono: em 31 dos 35 o lado minoritário publicaria **uma
única** condição. Isso NÃO fere a invariante 2 do §0 (*"um grupo de 1%
mantém seus 6 temas, suas barras e suas paráfrases"*) — os bullets não
mudam —, mas é uma assimetria deliberada num bloco novo, da mesma família da
exceção do meio recolhido.

**(c) Ordem por peso (v1.9.30), herdada de graça.** A coluna do grupo de
maior `share_real` vem primeiro. Já é a regra dos blocos de bullets, é
código puro, e não custa nada. **Deveria ser default em qualquer construção.**

**(d) A barra de proporção logo acima já carrega o peso.** VISTO: ela
carrega, e é justamente por isso que o problema é do bloco de condições —
duas colunas simétricas logo abaixo de uma barra 2/5/93 **contradizem a
barra**, e o leitor não tem como saber qual das duas ler.

**Recomendação desta seção: (c) + (a) como mínimo; (b) como decisão de
produto do dono.**

## 3. Correção 3 — `exemplo_verbatim` funciona, e a cópia caiu

**MEDIDO, braço A (118 condições):** `exemplo_verbatim` disparou **7 vezes**
(5,9%). Re-validando a rodada 1 sob a mesma régua, ela dispararia **5 de 48
(10,4%)**. A cópia caiu quase pela metade, com o validador ativo no prompt.

## 4. C5 — os três validadores, cada um com seu par

**MEDIDO, rodado nesta sessão contra os JSONs publicados.**

| validador | caso que REPROVA | flags | caso que PASSA LIMPA | flags |
|---|---|---|---|---|
| **1 ÂNCORA** | *"não se incomoda com licença histórica"* ← `POS-F` *Incentivo à pesquisa histórica* (a condição FABRICADA do mockup) | `ancora_nao_verificavel`, `sem_discriminacao` | *"quer um Napoleão íntimo, não o estadista"* ← `POS-D` (a condição CORRETA do mockup) | **nenhuma** |
| **2a DISCRIMINAÇÃO** | *"quer sequências de batalha impressionantes"* ← `POS-C` | `sem_discriminacao` | *"quer um ritmo contemplativo, quase meditativo"* ← `perfect-days` `POS-D` | **nenhuma** |
| **2b CORROBORAÇÃO** | *"topa longos períodos sem ação e até um pouco de sono"* ← `hereditary` `NEG-A`, lado **vale a pena** | `sinal_sem_corroboracao` (isolado) | *"topa lentidão e ausência de eventos"* ← `perfect-days` `NEG-A`, lado **vale a pena** | **nenhuma** — corroborado por `POS-D` *Ritmo lento e contemplativo* |
| **3 `exemplo_verbatim`** | *"prefere ver as inseguranças e a vida pessoal de Napoleão como homem comum"* (cópia REAL da rodada 1, 4 palavras seguidas) | `exemplo_verbatim` (isolado) | *"quer o Napoleão pessoal e inseguro, não o herói"* — **mesmo tema**, mesmas ideias, palavras reordenadas | **nenhuma** |
| **3 CONTROLE** | — | — | *"valoriza fotografia, figurinos e cenários deslumbrantes"* — enumeração de 3 sem sinônimo | **nenhuma** (é o que o teto 4 protege) |
| **4 `quantidade_escrita`** | *"é como a maioria, que reprova o retrato infantilizado"* | `quantidade_escrita` | — | — |

**C5 PASSA.** Cada validador tem um par, e 2b e 3 têm par **isolado** — um
caso em que só aquele validador dispara, que é o que prova que ele decide
alguma coisa sozinho.

*(Registro de método: a primeira tentativa de par para o validador 3 foi
descartada porque a metade "limpa" reprovava na ÂNCORA — a paráfrase que
escrevi não compartilhava vocabulário com o tema. O par acima é o
corrigido. Um par em que a metade limpa reprova por outro motivo não prova
nada sobre o validador em teste.)*

## 5. C1 e C2 — fabricação e generalização

**Protocolo:** cada uma das 118 condições do braço A lida contra o `tema` E
o `exemplo_parafraseado` do tema que ela cita (P4 REVISADO, §2.7).
**Leitura minha — esta tabela é VISTO**, com os textos ruins colados abaixo.

| categoria | n | % | rodada 1 |
|---|---:|---:|---:|
| suporte direto | **114** | 96,6% | 89,6% |
| extrapolação legítima | 1 | 0,8% | 2,1% |
| generalização excessiva | **3** | **2,5%** | 8,3% |
| **informação não encontrada** | **0** | **0%** | 0% |
| **total** | **118** | **100%** | — |

**C1 PASSA** (zero fabricações). **C2 PASSA com folga** — 2,5% contra o
corte de 12,5%, e contra os 8,3% da rodada 1.

**Leitura estendida** (contracorrente em QUALQUER bucket e ausente do
conjunto gerado): +4 casos ⇒ **7 de 118 = 5,9%**, contra 12,5% na rodada 1.
**Passa nas duas leituras**, e desta vez com margem.

### Os 3 casos de generalização excessiva, com o texto

**1 e 2. `cats-2019` / `POS-C`, nas duas execuções.**
- gerado: *"vale a pena se você **encontra charme na estranheza visual e no
  CGI bizarro das criaturas**"* (exec 2: *"acha graça no visual bizarro"*).
- tema `POS-C` *Visual bizarro e CGI questionável*: *"Muitas reviews
  mencionam a estranheza visual dos gatos, com efeitos digitais considerados
  **perturbadores**, **mas alguns** veem isso como parte do charme."*
- A condição promove a cláusula *"mas alguns"* a condição inteira e cala
  *"perturbadores"*, que está na mesma frase. É a cláusula de §10 — *"apaga
  uma contracorrente visível"* — dentro da própria paráfrase citada.

**3. `perfect-days-2023` / `NEG-B`, execução 1 apenas.**
- gerado: *"talvez evite se você se incomoda com a **romantização do
  desgaste no trabalho** sem crítica estrutural"*.
- a paráfrase diz que a obra *"enobrece a vida de um faxineiro, **ignorando**
  as condições estruturais e o desgaste do trabalho"* — o desgaste é o que o
  filme **apaga**, não o que ele romantiza.
- **É o mesmo defeito da rodada 1, e ele caiu de 2 em 2 para 1 em 2:** a
  execução 2 escreveu *"se incomoda com a romantização do trabalho de
  faxineiro e sua rotina"*, que é correto.

### O caso de extrapolação legítima

`hereditary` exec 1, `NEG-C`: *"busca sustos genuínos **frequentes**"*; a
paráfrase diz que os momentos de choque são *"raros"*. Inferência curta.

## 6. C6 — o caso `napoleon`/batalhas: a previsão se confirmou

**MEDIDO. Braço A, as duas execuções:**

- temas pedidos ao lado HATERS: `NEG-A`, `NEG-B`, `NEG-C`. **`NEG-F`
  *Batalhas decepcionantes* (6/40, ordem 5) NÃO entra.**
- condição gerada: *"vale a pena se você **aprecia sequências de combate
  espetaculares e brutais em grandes batalhas**"* (exec 2: *"…batalha
  brutais com coreografias autênticas…"*). **FLAGS: nenhuma, nas duas.**

**A Correção 1 não conserta C6, exatamente como previsto antes de rodar.** A
página do braço A diria que as batalhas valem o ingresso e em nenhum lugar
diria que o grupo que rejeitou o filme as chama de taticamente vazias.

**MEDIDO. Braço B (par obrigatório):**

- `NEG-F` é forçado para dentro pelo CÓDIGO;
- a condição gerada é ***"talvez evite se você espera combates com rigor
  tático e estratégia militar autêntica"*** — **FLAGS: nenhuma**;
- e a condição `POS-C` continua lá, também limpa.

**Isto é praticamente a correção que a auditoria manual propôs** (*"quer
batalha com tática, não só espetáculo"*), produzida pelo estágio.

> **A distinção que fecha C6 honestamente, e ela importa:** a razão nº 2 foi
> enunciada como *"o validador de discriminação não fecha o caso difícil"*.
> **Estritamente, ele continua não fechando** — `POS-C` passa limpa nos dois
> braços, porque *espetaculares* / *brutais* / *coreografias* são
> lexicalmente exclusivas de `POS-C` embora semanticamente idênticas a
> *visualmente impressionantes* das HATERS. O proxy é lexical e o defeito é
> semântico, como §3.3 do desenho já declarava.
>
> **O que a variante B fecha é o DANO, não o validador:** o leitor passa a
> ver as duas leituras. E o dano era a razão de a razão nº 2 existir — a
> condição enganosa não engana quando a objeção está na mesma tela.

**Custo do braço B, MEDIDO:** as listas crescem de 3/3 para 3/3–5/5, o total
de condições pedidas sobe **+38%** (60 → 83 nos 10 filmes), e o custo por
chamada sobe de US$ 0,00201 para US$ 0,00241 (+20%, briefing maior).

## 7. C7 — abstenção: aconteceu, e o achado real é outro

**MEDIDO:**

| | braço A | braço B |
|---|---:|---:|
| condições pedidas | 120 | 83 |
| condições geradas | 118 | 78 |
| **temas SALTADOS** | **2 (1,7%)** | **5 (6,0%)** |

**A rodada 1 teve ZERO abstenções em 16 lados** (48 condições, seis por
execução, sem exceção). Aqui há 7 saltos em 203 pedidos.
**A mudança não é do modelo — é do desenho:** na rodada 1 o modelo escolhia
os temas, então nunca era confrontado com um tema que não sabia usar. Com a
seleção em código, ele é.

### As sondas

| sonda | o que é | pedido | resultado |
|---|---|---|---|
| **zero temas** | `como-fazer-um-curta-metragem-…`, filme REAL com os três buckets em `sem_analise` e **nenhum tema** | 0 | **listas vazias nos dois lados** — abstenção total |
| **amostra mínima** | `obsession-2026`, n = 5/6/8, `estado_piso` `sem_numero`/`sem_quantificador`, sem `contraste` publicado | 6 | 6 condições, e o `rotulo_forca` das **seis** saiu `null` — a supressão de §3[C3] funciona |
| **um tema só** | `perfect-days` truncado a 1 tema no lado positivo | 1 + 3 | **1 + 3** — não completou cota, não substituiu |

### E o achado que a medição inverteu

Meu primeiro palpite, olhando os 5 saltos do braço B, foi que eles caíam
exatamente nos temas de valência conflitante. **A tabulação desmentiu:**

| tema classificado pelo léxico como de valência OPOSTA ao lado | condição escrita | saltada |
|---|---:|---:|
| sim | **12** | 1 |
| não | 184 | 6 |

Lendo os 13, **12 são erro do LÉXICO, não conflito real:**

- `joker` `POS-B` *Crítica à idolatria do Coringa* — "crítica" dispara o
  marcador negativo, mas aqui o filme **é** a crítica. A condição gerada
  está certa.
- `friday` `POS-B` *Remake subestimado* — *"recebeu críticas injustas"*
  dispara o marcador. A condição está certa.
- `wonka` `NEG-E`, `im-still-here` `NEG-E` — *"carisma"*, *"elogiada como o
  ponto alto"* disparam o marcador positivo dentro de temas negativos.

**MEDIDO: precisão do léxico de valência em "conflito" = 1 de 13 (7,7%).** E
ele produziu **2 flags `sinal_sem_corroboracao` falso-positivas** em 196
condições.

> **Este é o mesmo modo de falha que o §3[V] já mediu e corrigiu removendo
> marcadores:** *"`incomod*` saiu de `impacto_emocional`: incômodo é como se
> descreve qualquer coisa de que não se gostou"*. Palavra avaliativa em uso
> **meta** — o filme critica, os outros criticaram injustamente, a atuação é
> elogiada mas o resto não — quebra o léxico. **Recomendação: 2b entra
> restrito (só quando o tema NÃO tem irmão de mesmo assunto em outro bucket)
> ou não entra.** Como está, ele reprova mais texto correto do que errado.

**O único conflito REAL foi `friday-the-13th-2009` `POS-E` *Críticas ao
excesso de sexo e nudez*** — um tema de queixa dentro do bucket positivo. O
estágio foi mandado escrever *"vale a pena se você…"* a partir dele e
**saltou**. 1 de 1, e n=1 não é uma taxa.

## 8. Reprodutibilidade — C3, com a ressalva que foi registrada antes

**MEDIDO, braço A, duas execuções idênticas por filme:**

| | rodada 1 | rodada 2 |
|---|---:|---:|
| Jaccard sobre `(lado, tema_origem)` | 0,929 | **1,000** (10 de 10 filmes) |
| Jaccard sobre palavras de conteúdo | 0,557 | **0,365** |

**O 1,000 não é uma vitória, e isso ficou registrado antes de rodar:** a
seleção passou a ser determinística em código, então a métrica mede a
correção, não o estágio. Ela serve como conferência de que a Correção 1
realmente foi aplicada — e serve.

**O número que informa é o do TEXTO, e ele PIOROU: 0,365 contra 0,557.**
VISTO: com o tema fixo, o modelo reformula a mesma afirmação livremente a
cada execução (*"aprecia atuações marcantes que transmitem a complexidade de
seus personagens"* × *"aprecia atuações marcantes que revelam com
profundidade a complexidade dos personagens"*). A DECISÃO ficou estável e a
REDAÇÃO ficou menos estável. É o mesmo desacoplamento que o §3[V] aceita
explicitamente para o veredito (*"o que se perde é a reprodutibilidade byte
a byte"*), e não é critério de reprovação — mas o corte de 0,80 **não pode
ser declarado satisfeito**, porque a métrica que o satisfaz é a tautológica.

## 9. Flags e a comparação justa entre as duas rodadas

**MEDIDO, sob a MESMA régua (validadores da rodada 2) nas duas populações:**

| | rodada 1 (48 condições) | rodada 2 braço A (118) | rodada 2 braço B (78) |
|---|---:|---:|---:|
| com ao menos uma flag | **8 (16,7%)** | **17 (14,4%)** | 12 (15,4%) |
| `exemplo_verbatim` | 5 | 7 | 3 |
| `tema_verbatim` | 2 | 5 | 2 |
| `quantidade_escrita` | 1 | 3 | 1 |
| `sem_discriminacao` | 0 | 4 | 5 |
| `sinal_sem_corroboracao` | 0 | 0 | 2 |
| `ancora_nao_verificavel` | 0 | 0 | 1 |

Duas leituras honestas:

- **a taxa não melhorou muito** (16,7% → 14,4%), e a Correção 3 sozinha não
  a derruba;
- **`tema_verbatim` subiu, e parte é falso positivo.** Os 5 do braço A
  incluem 3 em `joker-folie-a-deux` sobre *Descaracterização do Arthur
  Fleck* — nomear a personagem exige o nome dela, e o tema tem exatamente 3
  palavras de conteúdo (`descaracterizacao`, `arthur`, `fleck`), o mínimo
  que aciona a regra. **É a fronteira da v1.9.22 encontrando um tema que é
  substantivamente um nome próprio**, e precisa de exceção antes de
  construir.

## 10. O algarismo — a garantia continua ausente, e a exposição hoje é zero

**MEDIDO, varredura dos 36 JSONs, só os buckets que ALIMENTAM condição
(`negativas` e `positivas`):** existe **1** tema com algarismo arábico —
`im-still-here-2024` / positivas / *Primeira parte memorável* (*"Os
primeiros **30** minutos…"*). Ele está em **ordem 3**, fora do top-3.

| | |
|---|---:|
| temas com algarismo em bucket que alimenta condição | 1 |
| … que entrariam no briefing sob N = 3 | **0** |
| algarismo em **qualquer** briefing serializado desta rodada (30 briefings) | **nenhum** |
| algarismo em qualquer das **206** condições geradas (2 braços + 3 sondas) | **nenhum** |

**A leitura correta é a estreita:** a garantia "zero dígitos por construção"
do §3[V] **continua perdida** — o desenho precisa da paráfrase e a paráfrase
não é limpa. O que a medição diz é que **a exposição HOJE é zero**, e ela é
zero porque um único tema num único filme está em quarto lugar. Um filme
novo, ou uma regeneração que reordene aquele bucket, reabre o buraco sem
aviso. A validação `digito` continua sendo a defesa primária.

## 11. Custo — MEDIDO

Preços de `scripts/comparar_narrador.py` (`gemini-3.7-flash`, US$ 0,75
entrada / 3,75 saída por 1M, **promocional até 31/12/2026**).

| | valor |
|---|---:|
| chamadas | 33 |
| tokens entrada / saída | 42.710 / 9.755 |
| custo total da sessão | **US$ 0,0686** |
| por chamada, braço A | US$ 0,00201 |
| por chamada, braço B | US$ 0,00241 |
| latência mediana | 5,3 s |

| projeção, `BEST_OF_N` = 3 | 35 filmes | 300 filmes |
|---|---:|---:|
| braço A | US$ 0,21 | **US$ 1,81** |
| braço B | US$ 0,25 | **US$ 2,17** |
| … com o preço pós-promoção (2×) | — | US$ 3,6 – 4,3 |

Referência do mesmo instrumento: a verificação binária foi reprovada, entre
outros motivos, por **US$ 23,82 em 300 filmes**. **O custo não decide nada
aqui, e isso precisa estar escrito para que um eventual "não" não seja
confundido com um "não" por preço.**

---
---

# As duas razões da reprovação anterior — fechadas ou abertas?

## Razão nº 1 — o formato apaga o PESO: **CONTINUA ABERTA**

`rotulo_forca` foi implementado e **está medido como incapaz de fechá-la**:
em 18 de 35 filmes o rótulo do lado minoritário é igual ou mais forte que o
do majoritário, e em `napoleon` ele aponta para o lado errado. A informação
de peso não está na razão `mencoes/n_analisadas`, e nenhuma escolha de
redação a põe lá.

**O que fecharia, e não foi construído nem medido:** (c) ordenar as colunas
por `share_real` — de graça, código puro, já é a regra dos bullets — mais
(a) um prefixo de peso por lado escrito em código, análogo ao
`prefixo_de_codigo` que o §3[V] já usa. **A razão nº 1 só fecha quando isso
existir e for lido.** `rotulo_forca` entra junto, porque resolve outra coisa
que também precisa ser resolvida.

## Razão nº 2 — o validador não fecha o caso difícil: **PARCIALMENTE FECHADA**

- **O validador continua não fechando.** `napoleon`/`POS-C` passa limpa nos
  dois braços. O proxy é lexical, o defeito é semântico, e isso é fronteira
  declarada, não pendência.
- **O dano fecha, pela variante B.** Com o par obrigatório em CÓDIGO, o tema
  HATERS *Batalhas decepcionantes* entra e produz *"talvez evite se você
  espera combates com rigor tático e estratégia militar autêntica"*. O
  leitor vê as duas leituras. Custo medido: +38% de condições, +20% de custo
  por chamada.
- **Preço de admissão da variante B:** ela sobe `sem_discriminacao` de 4/118
  para 5/78 e é onde os 2 falsos positivos de 2b apareceram. Precisa das
  correções de léxico da §7 antes de ser default.

## O que melhorou de fato, com número

| | rodada 1 | rodada 2 (braço A) |
|---|---:|---:|
| seleção de tema feita pelo MODELO | 14 de 16 | **0 — é do código** |
| generalização excessiva (estrita) | 8,3% | **2,5%** |
| generalização excessiva (estendida) | 12,5% | **5,9%** |
| fabricação | 0% | **0%** |
| abstenções | **0 em 16 lados** | **7 em 203 pedidos, e as 3 sondas passaram** |
| cópia da paráfrase (mesma régua) | 10,4% | **5,9%** |
| custo, 300 filmes, best-of-3 | US$ 2,03 | US$ 1,81 |

## Recomendação

**Não é decisão desta sessão construir, e a questão de produto — RECOMENDAR
em vez de RELATAR — continua pendente do dono, intocada.**

O que a rodada 2 estabelece: **das duas razões que reprovaram a rodada 1,
uma fechou pela metade e a outra não fechou, mas as duas têm agora um
conserto NOMEADO, barato e em CÓDIGO** — ordenação por peso mais prefixo de
peso (razão nº 1), e par obrigatório (razão nº 2). Nenhum dos dois é
pesquisa; os dois são função pura sobre dado que já existe.

**A ordem para uma eventual rodada 3, se o dono quiser:** (0) a decisão de
produto do §0; (1) prefixo de peso e ordenação por peso, com leitura do
`the-godfather` e do `cats-2019` para ver se a impressão muda; (2) restringir
ou remover o validador 2b, que hoje reprova mais texto correto do que errado;
(3) exceção de nome próprio no `tema_verbatim`; (4) rodar nos 35 com leitura
humana — **US$ 0,25 de LLM** e o tempo de ler ~210 condições.

## Limite da amostra

**10 filmes de 35, 33 chamadas, 196 condições, e a classificação de
fidelidade é uma leitura minha.** Com 0 fabricações em 118 do braço A, o
limite superior de 95% é **~2,5%** — melhor que os ~6% da rodada 1, e ainda
não é "zero fabricação no catálogo". A amostra desta rodada foi montada para
**cobrir**, não para quebrar, o que torna os achados POSITIVOS mais
generalizáveis que os da rodada 1 e os NEGATIVOS menos extremos. Os quatro
filmes adversos continuam dentro, então a comparação com a rodada 1 é
válida para eles.

**E um limite específico:** o braço B rodou **uma execução por filme**, não
duas. Nada do que se diz sobre ele tem medida de reprodutibilidade.

## Reprodução

`condicoes2.py`, `rodar2.py`, `rodada2.json`, `rodada.json` e
`CRITERIO_REGISTRADO_R2.md` vivem no scratchpad da sessão, não no
repositório — mesma política de `ESTUDO_MARGEM_20PP.md`. Nenhum arquivo do
projeto foi criado ou alterado além deste markdown. O protótipo importa
`espectro24.veredito`, `espectro24.quantificador`, `espectro24.briefing` e
`espectro24.qualidade` sem modificá-los.
