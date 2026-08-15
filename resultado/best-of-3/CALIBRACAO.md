# Calibração dos proxies contra leitura humana (§D2, v1.9.9, Entrega 5)

> **ATUALIZAÇÃO (sessão de fechamento, v1.9.9).** O achado (2) abaixo — o
> falso negativo sistemático da cobertura em paráfrase — foi CONSERTADO
> antes desta calibração valer. A seção "Correção aplicada" logo depois dos
> dois achados originais explica o quê e por quê, e as tabelas do achado
> (1) foram deixadas como estavam (histórico), com os números NOVOS ao
> lado. Duas consequências mecânicas da correção, sem nenhuma leitura
> humana envolvida:
>
> - a escolha automática de `cidade-de-deus` MUDOU, de B para A — não por
>   causa da cobertura, e sim porque a MESMA sessão também fechou a
>   Entrega 2 (parágrafo por grupo no movimento 3), e o candidato B tinha o
>   defeito que essa checagem existe para pegar (movimento 3 com dois
>   grupos dividindo o mesmo parágrafo). B passou de 0 para 1 flag e saiu
>   da disputa;
> - com as duas correções, a cobertura das 9 narrativas do best-of-3 é
>   **1,00 em todas** — o proxy segue nunca decidindo nada (mesmo fato do
>   achado 1), mas agora pela razão OPOSTA: não porque ele estava cego para
>   conteúdo real, e sim porque, medido corretamente, os 9 candidatos
>   realmente cobrem os temas do briefing.

## O que está sendo calibrado, e o que uma calibração destas pode provar

A seleção do best-of-3 é feita POR CÓDIGO. Dois dos seus critérios são
medida direta de defeito já observado (clichê da blocklist, repetição de
construção quantificadora) e não precisam de calibração: eles contam
exatamente a coisa que nomeiam.

Os outros dois são PROXIES, e é deles que este documento trata:

- **ritmo** — desvio-padrão do comprimento de frase, em palavras inteiras.
  A hipótese é que texto com todas as frases do mesmo tamanho lê como
  lista. O número não sabe nada sobre prosa; ele mede dispersão.
- **cobertura** — fração dos temas do briefing que o texto cobre,
  aproximada por ESTRUTURA (nº de cláusulas no span de cada grupo, contra
  o nº de temas atribuídos a ele — ver "Correção aplicada" abaixo). Já foi
  léxica (casamento de termos com o rótulo do tema) e tinha falso negativo
  sistemático em paráfrase; corrigida nesta sessão. É proxy porque
  verificar que uma cláusula específica é REALMENTE sobre um tema
  específico exigiria casamento semântico — um segundo LLM julgando, que
  este projeto não faz.

**O que poucos casos podem provar:** nada sobre correção. Se a preferência
humana coincidir com a escolha automática, o resultado é apenas "os proxies
não estão obviamente errados" — não "os proxies medem qualidade". Se
divergir, o resultado é mais forte e mais útil: significa que o proxy mede
outra coisa que não o que um leitor vê, e a divergência é registrada aqui
com o motivo dado pelo leitor.

## Procedimento

1. `python scripts/best_of_3.py calibracao --slug <filme>` imprime as três
   narrativas como CANDIDATO A/B/C, na ordem de geração, **sem dizer qual o
   código escolheu**.
2. A leitura humana escolhe e o motivo é anotado ANTES do passo 3.
3. `python scripts/best_of_3.py veredito --slug <filme>` revela a escolha
   automática e a tabela de métricas de cada candidato.

A ordem não é embaralhada de propósito: o que precisa ficar oculto é o
veredito, não a identidade do candidato — assim a leitura é reproduzível e
a anotação abaixo pode ser conferida depois.

## Registro

| filme | preferência humana | escolha do código | acordo? | motivo dado pelo leitor |
|---|---|---|---|---|
| `cure` | _(a preencher)_ | _(revelar só depois)_ | | |

| `cidade-de-deus` | _(a preencher)_ | _(revelar só depois)_ | | |
| `the-invite-2026` | _(a preencher)_ | _(revelar só depois)_ | | |

_(Uma linha por filme lido. Desacordo NÃO é erro a corrigir na tabela — é
achado, e a decisão do que fazer com o proxy vem depois dele.)_

## Dois achados que a rodada já produziu, ANTES de qualquer leitura

Ambos são sobre o COMPORTAMENTO dos critérios, não sobre qual texto é
melhor — por isso podem ser registrados sem a leitura humana, e nenhum
deles a substitui.

### (1) O ritmo decidiu nos 3 filmes; a cobertura não votou em nenhum

As 9 narrativas (3 filmes × 3) passaram limpas nas flags. Entre limpas, os
dois primeiros critérios EMPATARAM em todos os casos — clichê ficou em 0
nas nove, e a repetição máxima ficou constante dentro de cada filme (2, 2 e
1). Com clichê e repetição empatados, o ritmo passa a ser o primeiro
critério capaz de separar, e como é numérico e quase nunca empata, ele
decide sozinho: **3 de 3**. A cobertura, último da ordem, nunca chegou a
ser consultada.

Isso não é bug — é a consequência aritmética da ordem pedida. Mas registra
um fato que a ordem escondia: na prática, entre candidatos limpos, o
best-of-3 é hoje uma seleção **por dispersão de comprimento de frase**. Se
a leitura humana concordar com as três escolhas, essa dispersão está
correlacionada com o que um leitor prefere e a ordem está boa. Se
discordar, o conserto não é mexer no cálculo do ritmo: é mover a cobertura
para antes dele.

**O caso mais informativo é `cure`**, onde os dois proxies apontam para
lados opostos:

| cand | flags | clichês | rep.máx | ritmo | cobertura |
|---|---|---|---|---|---|
| A | 0 | 0 | 2 | 5 | 0,67 |
| **B (escolhido)** | 0 | 0 | 2 | **8** | **0,44** |
| C | 0 | 0 | 2 | 5 | **0,78** |

O código escolheu o candidato de MENOR cobertura porque ele tem o maior
ritmo. `cidade-de-deus` repete o padrão (B: ritmo 11, cobertura 0,78,
contra A e C com ritmo 5 e cobertura 1,00). Se a preferência humana em
`cure` for A ou C, o desacordo tem causa localizada e conserto conhecido.

### (2) A cobertura tem falso negativo em PARÁFRASE — e ele é sistemático

Inspecionando os temas que a cobertura não detectou no candidato B de
`cure`, os cinco "ausentes" estão todos no texto, parafraseados:

| tema do briefing | o que o texto escreveu |
|---|---|
| Pacing Lento e Deliberado | "o andamento metódico intensifica o suspense" |
| Final insatisfatório/ambíguo | "um desfecho considerado excessivamente ambíguo" |
| Temas Psicológicos e Existenciais | "a fragilidade da identidade, a manipulação mental" |
| Ritmo lento e tedioso | "a experiência como excessivamente tediosa" |
| Enredo e roteiro fracos/repetitivos | "a trama se torna repetitiva… roteiro pouco substancial" |

A cobertura de B não é 0,44: é 1,00. O proxy mede **sobreposição lexical
com o rótulo do tema**, não cobertura — e o viés tem direção: pune
justamente o texto que evita copiar o rótulo, isto é, a prosa melhor.

Estava registrado como **não corrigido** na versão anterior deste
documento, com o racional de que o conserto óbvio (casar sinônimo) exigiria
casamento semântico — um segundo LLM julgando, que este projeto não põe no
caminho.

### Correção aplicada (sessão de fechamento)

`cobertura` deixou de perguntar "este tema específico foi mencionado"
(léxico, com o falso negativo acima) e passou a perguntar algo mais fraco e
puramente ESTRUTURAL: "o span do GRUPO CERTO — ancorado pela primeira
ocorrência LITERAL do `rotulo_peso`, a mesma âncora que
`qualidade.ordem_dos_grupos_ok` já usava — tem tantas cláusulas distintas
quanto o briefing atribuiu a ele, na ORDEM em que os grupos aparecem?" A
primeira cláusula de cada span é descartada da contagem (é tipicamente a
frase de abertura que só retoma o rótulo de peso, sem tema próprio).

GRUPO é garantido pelo span (conteúdo do grupo errado nunca soma para o
grupo certo); ORDEM, por percorrer os grupos na ordem do briefing. O que
isto **declaradamente não verifica**: que a cláusula N seja REALMENTE sobre
o tema N — só que existem cláusulas suficientes. Uma ideia repetida três
vezes com sinônimos conta como três. É uma troca deliberada: extinguir o
falso negativo sistemático (grave e medido, tabela acima) custa a
capacidade de pegar a omissão de UM tema específico dentro de um grupo bem
escrito em volume — mais rara, e sem exemplo medido até agora.

Sob a métrica nova, o candidato B de `cure` mede **1,00** de cobertura, não
0,44 — as cinco paráfrases da tabela acima agora contam. As 9 narrativas do
best-of-3 medem 1,00 nas duas métricas onde antes divergiam; a única
mudança real de comportamento observada foi em `cidade-de-deus`, e por um
motivo diferente (parágrafo por grupo, achado da Entrega 2 desta sessão,
não a cobertura em si).

**O que segue sem resposta:** nenhum dos 9 candidatos, nas duas rodadas,
teve cobertura abaixo de 1,00 sob a métrica nova — o que significa que esta
calibração específica não teve chance de testar o proxy CORRIGIDO contra
um caso de omissão real. Se a leitura humana notar um tema do briefing
ausente de algum texto que a métrica marcou como 1,00, é esse o caso que
prova (ou derruba) a troca declarada acima — vale registrar explicitamente
se acontecer.
