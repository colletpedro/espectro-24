# Coerência temporal da amostra — medição e proposta

**Data:** 2026-08-09 · **Natureza:** medição + simulação · **Mudanças:** nenhuma

Zero requisições de rede. A seleção não foi alterada, nenhum parâmetro foi
tocado, `resultado/*.json` está intacto. Tudo aqui roda sobre o bruto
persistido (`scripts/coerencia_temporal.py`, saídas em
`resultado/coerencia-temporal/`).

---

## O veredito, antes dos números

**Estratificar a seleção é grátis e deve ser feito — mas não resolve o
problema que motivou esta tarefa, e nenhum desenho de seleção resolveria.**

A medição encontrou uma causa que a formulação original não previa: **o bloco
profundo da v1.9.2 é praticamente a mesma coorte temporal que o raso.** A
mediana de `data` do material profundo está **3 dias** antes da do raso. Em 26
dos 34 filmes com material nos dois blocos, o gap é de 7 dias ou menos.

A seleção não está descartando um passado que está em disco. O passado nunca
foi coletado — o orçamento de 16-24 páginas por bucket cai nas primeiras ~28
posições de níveis que vão a ~256, e sob `by/added` isso é uma janela de
semanas para um filme popular.

Logo: adotar E1 **e** declarar a janela. Não um ou outro.

---

## Entrega 1 — O tamanho do problema

### (a)-(c) `pagina_origem`: bruto, elegível, selecionado

| | reviews | profundas | fração profunda |
|---|---:|---:|---:|
| elegíveis (pós-filtro, o que a seleção poderia pegar) | 4906 | 1316 | 26,8% |
| **selecionadas** (o que vai à síntese) | 3948 | **716** | **18,1%** |

**Das 1316 reviews profundas que sobreviveram ao filtro, 716 entram na amostra
— 54,4%. As outras 600 estão em disco e nunca chegam ao produto.**

Por bucket, o padrão é o mesmo (elegível → selecionado): negativas 24,7% →
17,9%, medianas 28,0% → 18,4%, positivas 27,6% → 18,1%. A seleção derruba a
fração profunda em ~9 pontos em todos os três, o que é a assinatura de um
critério implícito e uniforme, não de escassez pontual.

**13 dos 105 buckets têm material profundo disponível e selecionam ZERO dele**
— entre eles `cats-2019`/medianas (17 profundas ignoradas),
`napoleon-2023`/medianas (16), `joker-folie-a-deux`/positivas (15),
`im-still-here-2024`/medianas (14).

### (d) `data` — instrumento secundário, proxy contaminado

Janela p5-p95 da amostra, em dias:

| | mediana | média |
|---|---:|---:|
| elegíveis | 52 | 268 |
| **selecionadas** | **26** | 221 |

**41 dos 105 buckets têm amostra que cabe em 14 dias; 61 em 60 dias.** Contra
um histograma que acumula notas desde 2012.

A ressalva de §3[B'] vale integralmente: `data` é a data ASSISTIDA, contaminada
por quem registra filmes com atraso. A média de 221 dias contra mediana de 26
é exatamente essa contaminação — alguns registros antigos puxam a média sem
descrever a coorte.

### O achado que muda a pergunta

Comparando, dentro de cada filme, a mediana de `data` do material **profundo**
contra a do **raso**:

| gap (raso − profundo) | filmes |
|---|---|
| ≤ 7 dias | **26 de 34** |
| ≤ 30 dias | 32 de 34 |
| mediana | **3 dias** |
| média | 10 dias |
| máximo | 97 dias (`cats-2019`) |

**O bloco profundo compra 3 dias.** Ele é "profundo" em posição de página
(14, 16, 20, 28), não em tempo: para um filme que recebe centenas de reviews
por semana, a página 28 ainda é deste mês.

Duas exceções reais e instrutivas — `cats-2019` (97 dias) e
`im-still-here-2024` (80 dias) — são filmes cujo fluxo de reviews é baixo o
bastante para que 28 páginas atravessem meses. É o mesmo mecanismo,
não uma classe diferente: quanto menos reviews por dia, mais tempo cada página
cobre.

**A v1.9.2 não pagou por páginas inúteis** — elas trazem material real e a
seleção descarta metade dele, o que é desperdício mensurável e corrigível. Mas
o que elas compram é **volume e diversidade de amostra**, não profundidade
temporal.

---

## Entrega 2 — Simulação dos três desenhos

Faixas definidas pela ESTRUTURA que a coleta já produz, não por tercil
arbitrário: a v1.9.2 gera um bloco raso consecutivo e denso (posições
`1..n_raso`) e um profundo geométrico e esparso. As três faixas são
`1..⌈n_raso/2⌉`, `⌈n_raso/2⌉+1..n_raso`, e `> n_raso`. Um tercil das posições
presentes produziria faixas diferentes em cada filme, sem significado comum.

Em todos os desenhos, a ordem DENTRO da faixa continua sendo
`(pagina_origem, ordem no jsonl)` — muda quantas vagas cada faixa recebe,
nunca o desempate dentro dela. A alocação das vagas entre faixas reusa
`alocar_bucket` + `redistribuir_deficit` (**quinto uso** da mesma função).

| desenho | n médio | buckets < 40 | fração profunda | uso do profundo disponível | janela mediana |
|---|---:|---:|---:|---:|---:|
| **atual** | 37,6 | 25 | 18,2% | 54,4% | 26 d |
| **E1** faixas iguais | 37,6 | **25** | **28,1%** | **86,2%** | 44 d |
| **E2** proporcional ao volume | 37,6 | 25 | 26,4% | 80,5% | 31 d |
| **E3** piso de 25% profundo | 37,6 | 25 | 25,9% | 79,0% | 30 d |

Comprimento médio da amostra: 469 (atual) contra 472 / 471 / 475. Sem efeito.

---

## Entrega 3 — O custo do desenho

### Buckets que deixam de fechar a cota: **zero, nos três desenhos**

Medido bucket a bucket: **0 de 105 perdem uma única review** sob E1, E2 ou E3.
A razão é estrutural — o pool elegível (4906) é 24% maior que a cota consumida
(3948), então redistribuir vagas entre faixas encontra material em quase todo
lugar, e onde não encontra o `redistribuir_deficit` devolve a vaga à faixa que
tem.

**Estratificar não custa profundidade de amostra. Esse era o risco esperado, e
ele não se materializa.**

### O material profundo tem perfil diferente do raso? Não

| | n | chars (média) | chars (mediana) | < 150 chars | spoiler |
|---|---:|---:|---:|---:|---:|
| raso | 15 129 | 153 | 58 | 76,3% | 2,5% |
| profundo | 6 139 | 147 | 57 | 78,5% | 2,6% |

Diferenças de 2 pontos percentuais em rendimento pós-`min_chars` e de 0,1 ponto
em spoiler. **Não há interação com `min_chars` a temer**, e nenhum risco de a
estratificação mudar o perfil da amostra por uma porta lateral.

### Os dois critérios competem? Pouco, e o conflito é nomeável

350 pares (bucket, nível) recebem cota > 0.

- **30 deles (9%) têm cota menor que 3** e portanto não conseguem preencher
  três faixas. Nesses, a estratificação por profundidade **cede** para a
  alocação proporcional por nível: o `redistribuir_deficit` concentra as
  poucas vagas onde há material, e o nível se comporta como hoje.
- **114 dos 350 níveis não têm material profundo nenhum** — a faixa 3 é vazia
  e as vagas voltam ao raso automaticamente.

Quem cede é a estratificação, e isso é a escolha certa: a alocação
proporcional por nível carrega uma garantia de representatividade
(§3[C1]) que o histograma sustenta, enquanto a estratificação por
profundidade é uma preferência de cobertura. **Custo do conflito: nos 9% de
níveis com cota < 3, o desenho novo é indistinguível do atual.**

---

## Entrega 4 — Recomendação

### **E1 (faixas iguais), adotado JUNTO com a declaração da janela — não no lugar dela.**

**O número que sustenta E1 entre os três:** ele leva o uso do material
profundo de 54,4% para **86,2%** — contra 80,5% (E2) e 79,0% (E3) — **sem
custar uma única review em nenhum dos 105 buckets.** É o desenho que mais
aproveita o que a v1.9.2 já pagou, ao mesmo custo de todos os outros: zero.

E2 e E3 são estritamente dominados aqui. E2 pesa pelo volume, e volume é
justamente onde o raso já é forte — ele reproduz parcialmente o viés que se
quer corrigir. E3 é o de menor intervenção e o de menor ganho.

**O número que sustenta "e declare a janela":** pelo instrumento secundário,
a mediana do ganho de janela sob E1 é **0 dias**. 63 dos 105 buckets não
mudam, 32 ganham, 10 perdem. Depois de E1, **57 dos 105 buckets ainda cabem em
60 dias** (eram 61) e 38 em 14 dias (eram 41).

Onde E1 muda tudo, muda mesmo: `cats-2019`/positivas vai de 129 para 1882
dias, `spider-man-across-the-spider-verse`/negativas de 31 para 1092,
`oppenheimer-2023`/positivas de 23 para 638. São os filmes de fluxo baixo, em
que a página profunda de fato atravessa anos. Para o blockbuster recente, não
muda nada — e é lá que o problema é pior.

**Sobre os 10 buckets que "perdem" janela sob E1** (`napoleon-2023`/medianas
979 → 209 dias, `hereditary`/medianas 172 → 4): é ruído do proxy. `data` é a
data ASSISTIDA, então uma review recente de alguém registrando uma sessão de
2015 aparece como "material antigo" no bloco raso, e trocá-la por material
genuinamente mais profundo encurta a janela MEDIDA enquanto melhora a amostra
REAL. Pelo instrumento primário (`pagina_origem`), E1 melhora todos os
buckets ou os deixa iguais, nunca piora. Esta divergência entre os dois
instrumentos é a melhor ilustração de por que §3[B'] rebaixou `data` a
secundária.

### A quarta opção que a medição sugere, e que está fora deste escopo

O problema de coerência temporal **não é da seleção; é da coleta**. Se o
objetivo for uma amostra que cubra a vida do filme, o caminho é posicionar o
bloco profundo muito mais fundo — a progressão geométrica atual para em
`n_raso+16` (~posição 28) num nível que vai a ~256. Isso é mudança de
parâmetro de coleta e exigiria recoleta; está registrado aqui como achado,
não como proposta desta sessão.

Enquanto isso não acontecer, **nenhum desenho de seleção fecha a distância
entre "notas desde 2012" e "reviews de ~6 semanas"**, e a declaração é
obrigatória, não opcional.

### O que a narrativa precisa dizer

O defeito é o mesmo que a spec já protege entre NOTAS e REVIEWS COM TEXTO
(§3[G], invariante de vocabulário do peso, v1.4.1): duas populações no mesmo
parágrafo, escritas como se fossem uma. Agora elas também têm bases temporais
diferentes.

**Com E1 adotado, a narrativa precisaria:**

1. **manter a separação de vocabulário que já existe** — rótulo de peso diz
   "das notas", frequência de tema diz "das reviews analisadas". A v1.4.1 já
   obriga isso e continua suficiente para a parte de população;
2. **acrescentar a base temporal ao lado do denominador da amostra**, não ao
   lado do peso. Algo da forma "entre as 40 reviews analisadas, escritas
   majoritariamente em <janela>" — o número da janela vindo de
   `distribuicao_pagina_origem`/`janela_temporal`, que já são calculados e
   persistidos;
3. **nunca escrever a janela como se fosse do peso.** "90% das notas" é sobre
   2012-2026; "a maioria das reviews analisadas" é sobre semanas. A frase que
   junta as duas sem marcar a diferença é exatamente o defeito.

**Se a decisão for NÃO estratificar,** as três exigências acima são idênticas —
com um agravante: a janela declarada seria mais estreita (26 dias medianos
contra 44), e 600 reviews profundas continuariam em disco sem uso. Não há
cenário em que a declaração seja dispensável; há um em que ela precisa
declarar uma amostra pior.

**Uma consequência de honestidade que vale registrar:** se a janela passar a
ser exibida, ela deve vir do dado, não de um texto fixo. `data` é proxy
contaminado e, em alguns buckets, exagera a cobertura (média 221 dias contra
mediana 26). Exibir a média seria mais lisonjeiro e menos verdadeiro.

---

## O que esta medição não fez

- **Não alterou a seleção.** Mudar agora invalidaria a classificação de eixos
  que roda em paralelo — outras reviews no bucket são outras frequências. A
  mudança, se aprovada, se aplica junto do schema.
- **Não mediu a percepção do leitor.** Se a janela declarada muda a confiança
  de quem lê, isso não está medido.
- **Não testou posicionamento mais profundo na coleta** — a quarta opção
  acima. Exigiria rede e recoleta, ambos fora de escopo.

## Reprodução

```bash
python scripts/coerencia_temporal.py medir
python scripts/coerencia_temporal.py simular
```
