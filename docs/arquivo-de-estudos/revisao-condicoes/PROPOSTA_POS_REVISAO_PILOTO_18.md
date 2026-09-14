# Lote `piloto-18` depois da revisão — aplicação, "sem condição publicável", padrões dos duvidosos, validador

**Convenção:** **MEDIDO** = saiu de código rodado nesta sessão, sobre o disco.
**VISTO** = leitura minha, e é julgamento, não medida. Zero chamada de LLM e
zero rede nesta sessão. **Nada foi gravado em `resultado/`**, e nenhum
código de produção mudou: a suíte continua em 1861 coletados, 1855 passando,
5 falhando e 1 xfail.

Insumo: lote `0ec05ad3e326` (141 itens), revisão externa (120 confirmados,
21 duvidosos) e o texto do dono (`correcoes-piloto-18.json`, verbatim).

---

## 1. Aplicação das correções (Tarefa 1)

**O que foi feito.** O lote corrigido está em `lote-piloto-18-corrigido/`; o
insumo original ficou intacto, porque é ele que a impressão digital
`0ec05ad3e326` identifica.

- **As 18 correções entraram verbatim.** A única operação foi recortar a
  abertura da coluna ("Vale a pena se você " / "Talvez evite se você "),
  porque o bloco guarda só a continuação da frase — a abertura é renderizada
  pelo código. O script confere que a abertura de cada linha bate com a
  coluna do item, e bateu nas 18.
- **C024, C051 e C089 saíram da coluna.** Os três foram para
  `temas_saltados`, o campo existente cuja definição é "pedido e não
  escrito"; nenhum campo novo foi criado (a representação é a Tarefa 2).
- **C020** vinha de `descartadas`; com o texto do dono, passa para a coluna.

**Colunas depois da remoção — MEDIDO** (sem `expectativa`, que não publica
pela R13):

| | piloto corrigido | catálogo antigo (35) |
|---|---|---|
| filmes com coluna vazia | **0** | 0 |
| menor lado | **2** (`speak-no-evil-2022` 2/3, `the-wailing` 2/4) | 2 (`hereditary` 5/2 e mais 3) |
| distribuição do menor lado | 2→2 · 3→10 · 4→5 · 5→1 | 2→4 · 3→15 · 4→16 |
| distribuição de \|vale−evite\| | 0→5 · 1→10 · 2→3 | 0→15 · 1→16 · 2→3 · 3→1 |

As três remoções tiram um item cada: `force-majeure` evite 4→3, `hard-to-be-a-god`
vale 5→4, `speak-no-evil` vale 3→2.

**Desequilíbrio a ponto de as colunas ficarem incomparáveis? Não, pela
contagem:** a maior diferença é 2, dentro da faixa do catálogo antigo, cujo
máximo é 3. O desequilíbrio que existe é o de PESO (`~94%` contra `~1%`), que
é de construção, vem do histograma e é mostrado pelo código ao lado de cada
coluna; nenhuma remoção o altera. Mesmo se as 7 correções bloqueadas (abaixo)
não publicassem, nenhum lado zeraria: o menor continuaria 2, e a maior
diferença, 2.

**Um par se desfaz — VISTO sobre dado MEDIDO:** em `force-majeure-2014`,
C020 (`POS-F`, "Ritmo lento…") foi FORÇADO pelo `NEG-A` "Ritmo lento e
duração excessiva". Se C020 não publicar, a coluna "talvez evite" fala do
ritmo e a "vale a pena" não traz a leitura positiva dele — o defeito que o
par obrigatório existe para fechar. As outras recusas não quebram par real
(ver 2.3).

### O que impediu a publicação — MEDIDO (dry-run de `publicar_condicoes`, filme a filme)

**11 filmes passam e 7 são RECUSADOS**, todos por texto do dono:

| item | filme | flags do validador |
|---|---|---|
| C010 | drive-my-car | `ancora_nao_verificavel`, `sem_discriminacao` |
| C020 | force-majeure-2014 | `ancora_nao_verificavel`, `sem_discriminacao` |
| C026 | get-out-2017 | `exemplo_verbatim` |
| C058 | memories-of-murder | `ancora_nao_verificavel` |
| C103 | the-second-mother | `ancora_nao_verificavel`, `sem_discriminacao` |
| C127 | whiplash-2014 | `sem_discriminacao` |
| C138 | zama | `exemplo_verbatim` |

A trava de `publicar_condicoes` reprova o filme INTEIRO na primeira condição
inválida; por isso não publiquei nada (seção 4).

**Outro bloqueio, independente dos 7:** `RETIRADAS` em `publicar_condicoes.py`
é uma lista LITERAL com os 6 itens de `expectativa` do catálogo antigo. Os
dois do piloto — **C030** (`get-out-2017` NEG-C, base) e **C134**
(`whiplash-2014` NEG-F, par obrigatório) — seriam publicados. Pela R13 não
podem; é preciso acrescentá-los à lista antes de publicar. Os dois filmes já
estão entre os 7 recusados, e `get-out-2017` ainda tem a amostra contaminada
(n=39, `ABERTO.md` C14.8).

---

## 2. "Sem condição publicável" como estado do pipeline (Tarefa 2) — PROPOSTA, não implementada

### 2.0 O que já existe, MEDIDO

- A regra 6 do prompt (ABSTENÇÃO) já deixa o modelo **saltar** um tema, em
  silêncio: vira `temas_saltados`, sem motivo. Nos 18 filmes o modelo saltou
  **5** temas (fora os descartados pelo validador).
- **Os dois temas de desfecho recusados pelo dono (C024, C089) já saíram do
  briefing marcados:** *"ATENÇÃO — este tema toca desfecho… Sem formulação
  com lastro, SALTE o tema."* O modelo escreveu os dois assim mesmo.
- **O best-of PENALIZA a recusa.** A chave de escolha (`condicoes._chave`) é
  `(-temas_cobertos, n_flags, índice)`. Em `speak-no-evil-2022` os três
  candidatos cobriram **7, 4 e 7** temas; o que cobriu 4 perdeu. Não dá para
  saber quais temas ele deixou de fora (o bloco não guarda os perdedores),
  mas, pela chave, uma amostra que tivesse recusado C089 perderia para uma
  que o escrevesse. O docstring pede "abstenção possível sem ser premiada";
  do jeito que está, ela é punida.

### 2.1 O gerador pode devolver "sem condição publicável" com motivo?

**Proposta.**
- **Saída do modelo:** cada lado ganha uma lista
  `sem_condicao: [{"tema_origem": "NEG-E", "regra": "R6", "motivo": "..."}]`.
  `regra` vem de um conjunto fechado (R1, R2, R6, R12, R13); `motivo` tem até
  20 palavras.
- **`extrair` valida:** o tema tem de ter sido pedido, e a regra tem de estar
  no conjunto. Tema citado nas duas listas vira flag, como `tema_repetido`
  já é.
- **Chave de escolha:** recusa DECLARADA, com regra válida, conta como tema
  resolvido. Silêncio continua não contando.
- **Desempate:** com cobertura e flags iguais, vence quem escreveu mais. Sem
  isso, recusar vira o caminho de menor atrito, porque recusa não tem flag.
- **Bloco publicado:** ganha `sem_condicao_publicavel: [{tema_origem, lado,
  regra, motivo, origem: "modelo" | "leitura_humana"}]`. O motivo nunca vai
  para a página. As três recusas do piloto entram com
  `origem: "leitura_humana"`, com o texto do dono.

**Risco declarado:** o modelo passar a recusar demais. Não há medida disso
antes de gerar; a revisão por lote passa a conferir as recusas (2.4).

### 2.2 O que acontece com a seleção por código quando um tema é recusado: cai para o próximo?

**Recomendação: NÃO cai.**
- **É o princípio vigente em três lugares:** bullets de eixo ("a lista
  encurta em vez de ser completada"), par obrigatório ("ACRESCENTA, nunca
  substitui") e regra 6 ("PROIBIDO completar cota").
- **O próximo tema não é do top-N:** puxá-lo mostraria ao leitor, como um
  dos assuntos principais, um que a contagem não pôs lá.
- **MEDIDO:** com as três recusas, nenhuma coluna ficou vazia. O menor lado
  é 2, o mesmo do catálogo antigo.

**Coluna vazia continua sendo estado de BLOQUEIO do filme**, com decisão
humana, como a Tarefa 1 pediu. Alternativa não recomendada: puxar o tema de
ordem N+1 só quando a coluna zera, marcado `entrou_por_recusa`.

### 2.3 O par obrigatório sobrevive à recusa de um dos lados?

Par = tema de base T, de um lado, que força o irmão S, do outro.

- **S (o forçado) é recusado:** T fica afirmando um traço sem a leitura do
  outro grupo — o defeito `napoleon`. Proposta: T continua publicável e ganha
  a marca exata `par_recusado`, que vira seção própria no relatório; a
  revisora julga se T sozinho achata a recepção. Remover T automaticamente
  não é recomendado: puniria o tema mais citado pela falha do forçado.
  MEDIDO: é o caso `force-majeure` `NEG-A` → C020.
- **T (o de base) é recusado:** S perde a razão de estar ali, porque foi
  forçado para mostrar a objeção a um traço que a página não afirma mais.
  Proposta: o par se desfaz e S sai, registrado como `par_desfeito`.
  Alternativa: S fica, se o dono preferir não perder a informação. MEDIDO:
  nenhuma das três recusas era de base com forçado. C051 e C089 eram base e
  não forçaram ninguém; C024 era forçado.

**Achado que vem antes de qualquer mudança aqui.** A régua do par é
`mesmo_assunto`: dois temas bastam compartilhar 2 prefixos de conteúdo.

- **MEDIDO:** 38 pares nos 18 filmes. Itens que entraram por par
  obrigatório são duvidosos em **26%** (9 de 34), contra **11%** dos de base
  (12 de 107).
- **VISTO:** 12 a 14 dos 38 pares se formam só por palavras de DISCURSO. C024
  entrou por `POS-B` "Crítica aos papéis de gênero" → `NEG-E` "Final
  decepcionante" via `deixa`, `quest`. C134 (`expectativa`) entrou por
  `POS-A` "Atuações marcantes" → `NEG-F` "Excesso de hype" via `consi`,
  `receb`. Os outros formados assim: `burning` NEG-C→POS-D, `drive-my-car`
  POS-B→NEG-E, `happy-hour` POS-A→NEG-D, `hard-to-be-a-god` NEG-A→POS-D,
  `neighboring-sounds` POS-A→NEG-D, `the-second-mother` POS-C→NEG-D,
  `the-turin-horse` POS-C→NEG-F / NEG-A→POS-F / NEG-B→POS-D, `whiplash`
  NEG-A→POS-D; limítrofes: `neighboring` NEG-A→POS-D, `pinocchio-2022`
  NEG-C→POS-D.
- **O mesmo afrouxamento infla os irmãos de `sem_discriminacao`** (seção 4).
  Uma lista de palavras de discurso excluídas da régua é o candidato óbvio,
  mas não foi medida. O primeiro passo seria o dono rotular os 38 pares.

### 2.4 Como aparece no relatório de revisão

- **Seção nova, antes de "descartada":** "Sem condição publicável". Cada
  recusa é um ITEM, numerado na mesma sequência estável (o tema recusado
  ocupa a posição dele na coluna). Traz filme, coluna, tema, paráfrase,
  rótulo, regra, motivo, origem (modelo ou leitura humana) e o efeito sobre
  o par.
- **Pergunta da seção:** *"a recusa procede? DUVIDOSO = existia uma
  condição honesta"*. É o espelho de `descartada`, e é o que impede a
  abstenção de virar atalho sem custo.
- **Categoria exata `par_recusado` / `par_desfeito`** para os itens do lado
  que sobrou.
- **O topo do relatório ganha uma regra:** "sem condição" é resposta válida,
  e publicar menos não é defeito.

---

## 3. Os três padrões dos 21 duvidosos (Tarefa 3)

**Base, MEDIDO:** 21/141 = 14,9%.
- **Por coluna:** "vale a pena" 15/68 (22%), "talvez evite" 6/73 (8%).
- **Por forma de entrada:** par obrigatório 9/34 (26%), base 12/107 (11%).

**Atribuição por grupo — VISTO.** O pedido traz as contagens por grupo, não os
itens; distribuí os 21 pelo diff entre o original e a correção e pela lista de
qualificadores do pedido:

| grupo | itens |
|---|---|
| **R2** omissão de ressalva (8) | C032, C039, C051, C073, C074, C079, C081, C097 |
| **R1** invenção de qualificador (6) | C001 "deliberada", C103 "dramas", C120 "clássicos de mestres autorais", C127 "confronto marcante", C137 "contundentes", C138 "rigor" |
| **R6** spoiler de arco (4) | C024, C089 (desfecho) · C010, C058 (evolução de relação/personagem) |
| fora dos três | C020 (descarte indevido do validador), C026 (inventou "no centro da narrativa"; poderia ser R1), C093 (inventou a oposição "procura um suspense dinâmico"; poderia ser R1/R8) |

### R2 — omissão de ressalva

- **MEDIDO:** 25 das 141 paráfrases têm conector de ressalva explícito
  ("embora", "apesar", "mas", "com exceção"…). A condição tirou todos os
  conectores em **22 das 25**.
- **O detector "conector na paráfrase e nenhum na condição":** dispara em
  22/141 e pega **6 dos 8** R2, com precisão de **27%** (6 de 22).
- **Os dois R2 que o detector não pega:** C051 (a queixa É o tema, dentro do
  grupo que recomenda, e não há conector) e C073 (a condição já tinha
  "apesar", mas minimizou com "ocasionais").
- **VISTO, sobre os 16 disparos que a revisora confirmou:**
  - 8 carregam a ressalva com verbo de concessão, sem conector: "aceita",
    "tolera", "não compensa", "em favor de" (C005, C012, C016, C053, C057,
    C060, C098, C119);
  - 6 têm conector que não contrabalança nada (C041, C069, C108, C110, C120,
    C122);
  - C118 é discutível: a condição tira "contribui para a atmosfera";
  - o último é C020.

**O briefing pode reduzir? Provavelmente, e é o grupo com mais chance.**
- **A regra já existe:** a 5 do prompt ("RESSALVA DO PRÓPRIO TEMA") e foi
  descumprida em 22 de 25 casos. Repetir a regra geral não é o que falta.
- **O que falta é LOCALIZAR a instrução:** uma marca por tema no briefing,
  como a de spoiler, com o mesmo argumento de custo assimétrico. Exemplo:
  *"RESSALVA NESTE TEMA: «…trecho…». Carregue as duas metades — com
  conector ou com verbo de concessão (aceita, tolera, apesar de) — ou
  declare sem condição."*
- **Carga:** 25/141 temas (18%). **Cobertura dos R2 rotulados:** 6/8.
- **C051 não é caso de marca:** é do canal de recusa (seção 2).

### R1 — invenção de qualificador

- **MEDIDO — resultado negativo:** a novidade léxica não separa. 130 dos
  135 itens fora do R1 também têm alguma palavra de conteúdo ausente do
  tema e da paráfrase (mediana 2, contra 3 no R1). A R11 ("palavras
  próprias") OBRIGA palavra nova, e isso tira do input qualquer sinal
  marcável.
- **Tipos, VISTO:** 4 intensificadores/avaliativos (deliberada, contundentes,
  rigor, confronto marcante), 1 rótulo de gênero (dramas), 1 referência
  externa (clássicos de mestres autorais).
- **A regra 2 do prompt já proíbe** "adjetivo avaliativo … que não esteja
  ali".
- **O briefing pode reduzir? É o grupo com menos confiança.** Proposta:
  trocar a regra abstrata por exemplos contrastivos reais, tirados destes 6
  casos ("a paráfrase diz *ambiguidade* → *ambiguidade deliberada* é RUIM").
- **Validador de lista fechada de intensificadores: NÃO recomendado agora.**
  Qualquer lista feita hoje sai destes 6 casos, então o recall medido sobre
  eles seria circular.

### R6 — spoiler de arco

São dois mecanismos diferentes.

- **Desfecho (C024, C089):**
  - **MEDIDO:** os dois já saíram do briefing com a marca "ATENÇÃO — toca
    desfecho… SALTE o tema", e o modelo escreveu mesmo assim.
  - **Instrução a mais não resolve.** O que resolve é o canal de recusa com
    motivo mais a chave do best-of que não pune recusa (seção 2). O dono
    concluiu que os dois não têm condição possível.
- **Arco/evolução (C010, C058):**
  - **MEDIDO:** a marca de spoiler atual pegou 0 de 2.
  - **Acrescentando léxico de arco** (desenvolv*, gradual*, desgast*, "ao
    longo", culmin*…): pega 4/4, mas marca 29/141 (20%), com precisão de
    13,8%.
  - **Ressalva:** a medição é in-sample. O léxico foi montado depois de ver
    C010 e C058, então o recall está inflado por construção. O maior ruído é
    "desenvolv*".
  - **Proposta, independente do léxico:** uma regra 9h no prompt — *"a
    evolução de um personagem ou de uma relação AO LONGO do filme é arco:
    nomeie o traço, não a trajetória"* —, com C010 e C058 como exemplos. A
    regra 9 hoje só fala de "ponto de chegada de arco".

### Quanto isso move a conta dos 300

- **Hoje:** 15% de 2.300 ≈ 345 itens para leitura humana.
- **Teto teórico:** se as três medidas funcionassem 100% sobre o que cobrem
  (R2 6/8, desfecho 2, arco 2), sobrariam 11/141 ≈ 7,8%, cerca de 180 itens.
  Não é previsão.
- **Como medir:**
  - **Experimento:** regerar os 18 filmes com o briefing variante (≈4
    chamadas Gemini por filme, ~US$ 0,45 pelo custo medido de US$
    0,025/filme) e rotular às cegas pelo mesmo protocolo de revisão.
  - **Poder:** com 141 itens, cair de 8 para 4 em R2 NÃO é distinguível do
    acaso (Fisher p≈0,37); só dá direção. Para separar, são necessários os
    53 filmes, ~410 itens, ~US$ 1,3.
  - **Preço:** o do Gemini dobra em 1/1/2027.

---

## 4. C020 e o validador (Tarefa 4)

**A regra que descartou C020 é `sem_discriminacao`** (validador 2,
`condicoes._validar_discriminacao`). Se o tema é "mesmo assunto" que QUALQUER
tema de outro grupo — medianas incluídas —, a condição precisa conter ao menos
um prefixo EXCLUSIVO do seu tema e da sua paráfrase.

**Por que C020 caiu — MEDIDO:**
- **Irmãos:** 6 temas contaram como irmãos (NEG-A, NEG-C, NEG-E, MED-B,
  MED-D, MED-E), três deles só por palavra de discurso (`quest`, `abord`,
  `algum`, `propo`).
- **Exclusivos que sobraram:** `agrad`, `embor` e `recon` — "agradou",
  "embora", "reconheçam", nenhum de conteúdo.
- **Onde caiu:** "a serviço da proposta" é a leitura positiva que o dono
  apontou, e reprova porque "proposta" também aparece na paráfrase do
  `MED-D`.

**No catálogo inteiro — MEDIDO:**
- **Descartes finais:** 3 no total — 2 nos 35 antigos e C020 no piloto.
  - `shutter-island` NEG-B: "…reviravolta final se revela previsível logo no
    início".
  - `the-northman` NEG-A: "…enredos de vingança previsíveis e repletos de
    clichês".
  - São 3 dos 8 descartes finais do catálogo (5 + 3).
- **A montante, a regra dispara muito mais:** aparece em 51 candidatos do
  best-of nos 35 e em 21 no piloto; o retry costuma consertar.
- **Sobre os 2 descartes antigos, VISTO:** `the-northman` parece falso
  positivo; `shutter-island` tinha problema de spoiler de qualquer forma.

**Padrão, não caso único — MEDIDO sobre o único conjunto rotulado que
existe.** Nas 18 correções do dono (aprovadas por definição), os validadores
LÉXICOS reprovam **7 (39%)**:

- **`sem_discriminacao`, 4 (C010, C020, C103, C127)** — mesmo mecanismo de
  C020: irmãos inflados, exclusivos sem conteúdo.
- **`ancora_nao_verificavel`, 4 (C010, C020, C058, C103)** — o dono usou
  sinônimo onde a régua pede prefixo igual: atuações → interpretações,
  personagens → figuras, doméstico → dentro de casa. É exatamente a
  abstração que a R12 pede.
- **`exemplo_verbatim`, 2:**
  - **C026** reprova SÓ pelos 4 nomes ("Daniel Kaluuya e Allison Williams");
    sem nomes, a sequência copiada é 0. A exceção de nome próprio que o
    `tema_verbatim` ganhou na v1.9.35 não existe no `exemplo_verbatim`.
  - **C138** copia de fato 4 palavras da paráfrase ("valoriza os aspectos
    técnicos e temáticos").

O documento de desenho já registrava que "o proxy é LEXICAL e o defeito é
SEMÂNTICO" para o que ele deixa passar. Isto é o espelho: o que ele reprova
indevidamente. **Precisão não calculável:** nenhum descarte do validador tem
rótulo de acerto além de C020.

**Opções para o dono**, sem nada implementado:
- **(a)** Texto de autoria humana (`origem: leitura_humana`) passa só pelos
  validadores EXATOS — âncora 1a/1b, dígito, aspas, comprimento, quantidade,
  escopo, perfil, formato. Os léxicos (1c, 1d, discriminação) viram aviso.
- **(b)** Manter a trava e reescrever as 7 para passar no léxico — na
  prática, o validador redigindo o produto.
- **(c)** Estender ao `exemplo_verbatim` a exceção de nome próprio; resolve
  só C026.
- **(d)** Excluir as palavras de discurso de `mesmo_assunto`; muda também
  os pares (2.3) e precisa de rótulo antes.

Recomendação: (a) com (c); (d) só depois de medir.

---

## 5. Decisões pendentes, em ordem

1. Como os 7 textos do dono passam pela trava (seção 4).
2. C030 e C134 entram em `RETIRADAS` (R13).
3. `get-out-2017` continua com amostra contaminada (C14.8).
4. Aprovar ou recusar a proposta de "sem condição publicável" (seção 2).
5. Aprovar o experimento de briefing (seção 3) antes de gerar condições para
   os 300.
