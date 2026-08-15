# Calibração dos proxies contra leitura humana (§D2, v1.9.9, Entrega 5)

## O que está sendo calibrado, e o que uma calibração destas pode provar

A seleção do best-of-3 é feita POR CÓDIGO. Dois dos seus critérios são
medida direta de defeito já observado (clichê da blocklist, repetição de
construção quantificadora) e não precisam de calibração: eles contam
exatamente a coisa que nomeiam.

Os outros dois são PROXIES, e é deles que este documento trata:

- **ritmo** — desvio-padrão do comprimento de frase, em palavras inteiras.
  A hipótese é que texto com todas as frases do mesmo tamanho lê como
  lista. O número não sabe nada sobre prosa; ele mede dispersão.
- **cobertura** — fração dos temas do briefing que o texto menciona,
  detectada por casamento de termos de conteúdo. É proxy porque casamento
  semântico exato exigiria um segundo LLM julgando, que é justamente o que
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

Está registrado e **não corrigido nesta versão**, por dois motivos. O
conserto óbvio (casar sinônimo) é casamento semântico, que só um segundo
LLM faz — e LLM julgando prosa é o que este projeto não põe no caminho. E,
enquanto a cobertura for o ÚLTIMO critério e o ritmo decidir sozinho
(achado 1), o falso negativo não mudou nenhuma escolha até agora. Se a
leitura humana mandar a cobertura para antes do ritmo, este defeito passa a
importar imediatamente e tem de ser resolvido antes — provavelmente
mudando o critério para "o tema aparece na MESMA ordem e no MESMO grupo",
que é verificável sem semântica.
