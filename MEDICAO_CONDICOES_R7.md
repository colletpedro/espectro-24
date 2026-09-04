# CONDIÇÕES — pendência do eixo `expectativa` + leiaute da FASE 1

**Parte 1: `resultado/` sem diff, nada publicado.** **Parte 2:** o leiaute
entra em `frontend/`; `frontend/js/data.js` foi patcheado temporariamente
para a verificação e **restaurado** (`git status` limpo nele). Suíte:
**1.643**, intacta — nenhuma alteração de Python nesta sessão.

---
---

# PARTE 1 — o eixo `expectativa`

## Registrado na spec (§0, terceira exceção)

O conflito estrutural, as ocorrências com o texto atual, o `friday` como
exceção, o dado medido e a pergunta em aberto. **+226 linhas acumuladas, 0
removidas.**

## Correção 1 — as ocorrências são SEIS, não cinco

A varredura foi feita **por eixo**, não pela memória da leitura, e encontrou
uma que a lista não continha:

| filme | tema | texto atual |
|---|---|---|
| `the-godfather` NEG-B | Filme superestimado | *acha que o filme não merece tanto elogio quanto recebe* |
| `hereditary` NEG-B | Expectativa vs. realidade (hype) | *se decepciona quando filmes de grande repercussão não correspondem a altas expectativas* |
| `interstellar` NEG-B | Filme superestimado | *se frustra quando um filme muito elogiado parece superestimado* |
| `longlegs` NEG-B | Expectativa alta, decepção | *se frustra quando obras cercadas de grande expectativa não correspondem à forte repercussão* |
| `parasite-2019` NEG-C | Expectativa não correspondida | *se frustra quando obras premiadas e consagradas não correspondem a altas expectativas* |
| **`everything-everywhere-all-at-once` NEG-F** | Superestimado e prêmios injustificados | *se decepciona quando obras muito aclamadas aparentam profundidade sem substância real* |

A paráfrase dela confirma o mesmo conflito: *"A aclamação crítica e a vitória
no Oscar parecem desproporcionais à qualidade do filme"* — objeto fora da
tela, mesmo molde *"quando obras…"*.

**Duas condições do eixo NÃO entram na pendência**, e a razão é a que define
o conflito — nelas o objeto **é o filme**:

- `spider-man-across-the-spider-verse` POS-E — *Cliffhanger e expectativa
  pela continuação*: fala do final aberto da própria obra;
- `talk-to-me-2022` NEG-C — *Subaproveitamento do potencial da premissa*:
  fala do potencial da própria premissa.

## Correção 2 — `expectativa` NÃO é a segunda maior assimetria

Os dois números do briefing **confirmam-se**; o ranking, não.

| | reviews | bullets | razão |
|---|---:|---:|---:|
| `expectativa` | **20,6%** | **4,0%** | 5,2× |

*(5.371 reviews em `consenso_verificado.jsonl`; 629 bullets publicados. O
briefing dizia ~19,9% e ~4% — batem.)*

**Mas a posição está errada nas duas métricas possíveis:**

| eixo | reviews | bullets | delta | razão |
|---|---:|---:|---:|---:|
| `comparacoes` | 39,0% | 2,4% | +36,6pp | **16,3×** |
| `roteiro_estrutura` | 56,0% | 25,1% | +30,9pp | 2,2× |
| `impacto_emocional` | 36,3% | 6,5% | +29,8pp | **5,6×** |
| `direcao_imagem` | 32,3% | 12,7% | +19,6pp | 2,5× |
| `ritmo` | 30,5% | 12,1% | +18,4pp | 2,5× |
| **`expectativa`** | **20,6%** | **4,0%** | **+16,6pp** | **5,2×** |

**Por razão é a TERCEIRA; por diferença em pontos percentuais é a SEXTA.**

**O que a medição sustenta é a conclusão, não a posição:** com 20,6% das
reviews carregando o eixo e 4,0% dos bullets publicando-o, **o problema nunca
foi de volume de informação.** Esse argumento fica de pé; a frase "segunda
maior assimetria" não.

## Consequência operacional — a proposta

**Confirmado antes de propor: nenhum filme fica com lado vazio.** Removendo a
condição do eixo, os seis ficam assim:

| filme | vale / evite hoje | se sair |
|---|---|---|
| `the-godfather` | 4 / 3 | 4 / **2** |
| `hereditary` | 5 / 3 | 5 / **2** |
| `interstellar` | 3 / 3 | 3 / **2** |
| `longlegs` | 4 / 4 | 4 / 3 |
| `parasite-2019` | 3 / 4 | 3 / 3 |
| `everything-everywhere` | 5 / 5 | 5 / 4 |

**Menor lado resultante: 2. Nenhum zero.**

### PROPOSTA: as seis SAEM da publicação da fase 1

**A razão decisiva é a terceira garantia do §0.** O que autoriza este produto
a recomendar é a leitura humana de 100% antes de publicar. Essa leitura
aconteceu e disse **R** nestas condições. **Publicar texto que o portão
editorial reprovou esvazia a garantia que autoriza o bloco a existir** — e a
garantia é do §0, não uma preferência de processo.

**E o custo é menor do que parece, porque a informação NÃO sai da página.**
Verifiquei: os bullets continuam publicando o tema com a paráfrase completa e
a barra de frequência ao lado (*Filme superestimado*, *Expectativa vs.
realidade (hype)*…). O que sai é a **recomendação** construída sobre ele; o
**relato** permanece.

**Isso é a arquitetura certa, e não um consolo:** um eixo cujo objeto está
fora do filme fica no bloco que **RELATA** e sai do bloco que **RECOMENDA**.
É a mesma fronteira que a pergunta em aberto do §0 formula.

> **A ressalva honesta, medida:** verifiquei os seis vereditos e **nenhum
> menciona expectativa** — todos nomeiam `roteiro_estrutura` ou
> `comparacoes`, porque o veredito nomeia o `assunto_compartilhado`, que é
> outro. Então a informação **não migra para o veredito** na fase 1. Ela fica
> só nos bullets. Quem quiser que ela apareça em prosa terá de mexer no
> veredito, e isso é a decisão futura, não esta.

**Alternativa que eu NÃO recomendo:** manter as seis marcadas como pendentes
na folha. Marcação de pendência é para quem lê a folha, não para quem lê o
site — o leitor final veria seis condições que o portão reprovou, sem
nenhuma marca.

---
---

# PARTE 2 — o leiaute da FASE 1

## A ordem proposta foi CONTESTADA num ponto

A ordem do estudo era `barra → CONDIÇÕES → veredito → bullets`. **Isso
moveria o veredito de volta para ANTES dos bullets, desfazendo a decisão da
v1.9.26**, que o desceu para o fecho com razão explícita e registrada no
changelog: *"conclusão lida ANTES da evidência é asserção, lida DEPOIS é
fecho"*. A proposta não citava essa decisão.

**Ordem implementada:**

```
backdrop → ficha → barra de proporção → CONDIÇÕES
        → divisor → bullets → veredito → narrativa → pesquisa
```

- as **condições coladas na barra**, que é o contexto de peso que elas
  pressupõem — o `~93% das notas` no cabeçalho de cada coluna só se lê contra
  a barra logo acima. O requisito da proposta é atendido;
- o **veredito fica onde a v1.9.26 o pôs**, intacto;
- os **bullets entre os dois**, como a evidência que sustenta a recomendação
  acima e o fecho abaixo — que é exatamente a razão de arquitetura da
  COEXISTÊNCIA registrada no §0.

**E é a mudança menor:** um bloco entra, **nenhum bloco existente se move**.
O diff em `filme.js` remove três linhas, e as três são as mesmas linhas
renumeradas. A restrição era acrescentar sem redesenhar, e mover o veredito
seria redesenhar uma decisão registrada.

## A linha de proveniência — decisão: HÍBRIDA, sempre visível

- o **TEMA de origem fica sempre visível**, ao lado do rótulo de força, em
  mono pequena: *"muitos · Expectativa vs. realidade (hype)"*;
- a **PARÁFRASE completa não se repete** — ela já está na mesma tela, nos
  bullets logo abaixo, com a barra de frequência ao lado.

**Esconder atrás de disclosure foi descartado:** a proveniência é uma das três
garantias que autorizam o produto a recomendar (§0), e **uma garantia que
exige um clique para existir é decorativa**. Foi ela que permitiu auditar a
feature em cinco rodadas.

## Identidade visual — nenhuma família nem cor nova

| elemento | tratamento | por quê |
|---|---|---|
| texto da condição | **serifa** | é a voz editorial do produto, a mesma do veredito e da narrativa |
| cabeçalho, peso, proveniência | **mono** | é o sistema falando, o registro de `.section-label` e `.proportion__note` |
| cor de cada coluna | `--pos` azul / `--neg` âmbar-avermelhado | a paleta oficial dos três grupos. **Nunca verde-vermelho** — "vale a pena / talvez evite" é exatamente onde a leitura semafórica tentaria entrar |
| marcação da coluna | barra de 2px à esquerda | mesmo vocabulário discreto de `.verdict-absent`, sem caixa nem fundo |

**As duas colunas têm largura e peso visual iguais** (`1fr 1fr`). O peso é
dito pelo NÚMERO, nunca por encolher a coluna.

## Verificação manual — 6 filmes, desktop e mobile

Registrada em `frontend/TESTE_MANUAL.md`. Todos os seis casos ✅:
`the-godfather`, `cats-2019`, `napoleon-2023`, `obsession-2026`,
`perfect-days-2023`, `hereditary`.

- **Zero erro de console** nos seis, conferido em aba limpa;
- **sem transbordo horizontal a 375px**: `scrollWidth === innerWidth === 375`
  nos seis; o grid colapsa para uma coluna;
- **ordem por peso preservada no empilhamento mobile** — a coluna maior vem
  primeiro no DOM (ordenada em Python), então empilhar mantém a ordem sem
  regra de ordem no CSS. `the-godfather` empilha *Vale a pena* primeiro;
  `cats-2019`, *Talvez evite*.

### Um defeito achado NA verificação, e corrigido

`var ABERTURA_DA_COLUNA` estava declarada junto de `condicoesBlock`,
**depois** da chamada `render(film)` (linha ~110). `var` hoista a declaração
mas **não a atribuição** — a tabela chegava `undefined` e o bloco inteiro
estourava com `Cannot read properties of undefined (reading 'vale_a_pena')`.
As funções sobreviviam por serem declarações; a tabela não. Movida para as
constantes de módulo. **É o tipo de erro que só a tela mostra**, e é por isso
que a verificação manual é o aceite em frontend.

## A pergunta que só a tela responde

> **Vendo `the-godfather` como PÁGINA, com as duas colunas e os dois
> percentuais, a proporção fica clara?**

**A minha leitura: fica — e o que a torna clara não é o bloco sozinho, é a
adjacência.**

```
RECEPÇÃO
▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮
~2%  ~5%                            ~93%
■ HATERS   ■ MIXED   ■ FANS

PARA DECIDIR
│ VALE A PENA SE VOCÊ…      │ TALVEZ EVITE SE VOCÊ…
│ ~93% das notas            │ ~2% das notas · amostra pequena
```

O número da coluna **repete** o número da barra a três linhas de distância, e
a barra é uma imagem enquanto a coluna é um rótulo — o leitor encontra a
mesma proporção em duas codificações diferentes, uma dimensional e uma
verbal. Era isso que faltava: a razão nº 1 do estudo era que o formato
**apagava** o peso, e o peso agora está escrito dentro do próprio bloco.

**VISTO, não medido.** É a minha leitura de uma página, não pesquisa com
leitor. O que eu **não** consigo responder é se um leitor apressado lê as
duas colunas como equivalentes **apesar** dos números — simetria visual é um
sinal forte, e a assimetria está só no texto. **Se você quiser fechar essa
dúvida de verdade, é feedback de uso real, que é exatamente o que a fase 1
existe para colher.**

---

## Estado

| | |
|---|---|
| `resultado/` | sem diff |
| `frontend/js/data.js` | patcheado para verificar, **restaurado** |
| Python | inalterado; suíte **1.643** |
| frontend | `filme.js` +168/−3 (as 3 são renumeração), `styles.css` +107, `TESTE_MANUAL.md` +52 |
| SPEC | +226 acumuladas, 0 removidas |

**Pendente de decisão sua:** se as seis condições de `expectativa` saem da
publicação da fase 1 (minha proposta) ou ficam.
