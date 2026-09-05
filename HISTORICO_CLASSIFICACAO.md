# Histórico — a RÉGUA (eixos, lift, margem, gabarito)

Este arquivo responde *"por que a régua é assim, e o que já foi medido?"*.

Cobre: o nulo do máximo, a margem de 20pp como registro histórico, α = 0,05, a
comparação exata, `impacto_emocional`, Feelings em espera, o aviso do gabarito
dos 5 casos, a extensão de cobertura a 100%, a defasagem entre artefatos e
consenso, e as duas populações de 40.

---

<!-- SPEC.md linhas 275–315 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **NEUTRALIDADE DE TRATAMENTO É MESMA EXIGÊNCIA PROBATÓRIA, NÃO MESMO NÚMERO.**
> É a frase que esta versão acrescenta ao princípio, e ela precisa estar escrita
> porque a intuição diz o oposto (um número igual para todos *parece* a opção
> neutra). **MEDIDO** (`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_MARGEM_20PP.md` §4.1): o mesmo limiar de 20pp é o
> percentil **3** do ruído com n=10, **34** com n=20, **65** com n=30, **83**
> com n=40 e **99,8** com n=100. Um número constante aplicado a amostras de
> tamanhos diferentes exige provas **sistematicamente diferentes**, e a régua é
> mais FROUXA exatamente onde o dado é mais fraco — o filme com amostra pequena
> passa mais fácil, e o que ele publica tem mais chance de ser ruído. Chamar
> isso de neutralidade é chamar de neutro o resultado de não olhar.
>
> **O PRECEDENTE JÁ ESTAVA AQUI DENTRO, e o argumento é o mesmo trocando duas
> palavras.** A v1.9.30 escreveu, sobre a ordem dos blocos: *"a ordem antiga não
> era neutra — era CONSTANTE, que é outra coisa… quando duas posições são
> desiguais por construção, a única regra defensável é a que decide entre elas
> pelo DADO."* Troque "ordem" por "limiar" e "peso" por "tamanho de amostra" e o
> parágrafo se lê sem uma emenda.
>
> **E O TESTE QUE A v1.9.30 USOU PARA SE AUTORIZAR PASSA AQUI TAMBÉM, POR
> CONSTRUÇÃO:** a regra é função do DADO, não do sentimento. `n` é quantas
> reviews com texto ≥150 caracteres o Letterboxd tem naquele bucket — contagem,
> não juízo. **Não existe mecanismo pelo qual um limiar em função de `n`
> favoreça o grupo negativo ou o positivo**, porque `n` é o mesmo para os três
> dentro de um filme (é o MENOR dos três, §2.5) e entra uma vez só.
>
> **O QUE SE PERDE, escrito por extenso porque é a metade honesta.**
> **Comparabilidade entre páginas.** O leitor que vê `tematico` em `cats-2019` e
> `valorativo` em `the-godfather` não tem como saber que o segundo foi julgado
> sob um limiar mais alto (26,4pp contra 22,8pp). A afirmação implícita "estes
> dois filmes são diferentes" fica um grau mais fraca do que parece. **MEDIDO:
> isso afeta 6 dos 35 filmes hoje** (os que têm algum bucket abaixo de 40), e em
> 4 deles a diferença de limiar é menor que um passo do quantum. O caso extremo
> é um só (`obsession-2026`, n = 5/6/8) e é exatamente aquele em que o produto
> **deveria** estar dizendo outra coisa — e passa a dizer: ele sai sem estado
> publicado (§2.5, piso de `n`).
>
> **O DADO por filme não muda de forma.** A cota 40/40/40 continua literal, os
> três buckets continuam com o mesmo leiaute, o mesmo espaço estrutural e a
> mesma quantidade de bullets. O que muda é **quais filmes** caem em cada ramo
> do veredito — não como um filme trata seus três grupos.


<!-- SPEC.md linhas 1050–1059 · origem: Lift — a definição, e por que ABSOLUTO -->

**Lift NORMALIZADO foi testado e REFUTADO** (`scripts/metricas_lift.py`).
`(freq_top − freq_2o)/(1 − freq_2o)` e log-odds amplificam o quantum de
discretização (1 review de diferença) exatamente no regime saturado: 15×
mais sensível a ruído com o segundo colocado em 95% do que em 25%. Sob o
nulo de permutação, a normalização faz `impacto_emocional` sozinho responder
por **62,6%** do ruído, contra 13,9% do maior contribuinte sob o lift
absoluto. Nenhuma das três métricas atinge cobertura ≥18/35 filmes com ruído
≤35%; **a métrica atual é a menos ruim das três**, e é assim que ela deve
ser lida.


<!-- SPEC.md linhas 1109–1131 · origem: A MARGEM — a lei por `n` (v1.9.34). **Este é o parâmetro em vigor.** -->

> **O DEFEITO QUE O PISO ENCONTROU, e ele se manifesta de dois jeitos OPOSTOS
> nos dois lados do produto.** Antes desta versão o estado nunca podia faltar,
> então os dois consumidores tratavam a ausência por omissão — e cada um caía
> num ramo diferente, os dois publicando exatamente o que o piso existe para
> não afirmar:
>
> - **Python** (`veredito.py`, montagem do briefing): `if estado ==
>   "valorativo": … else: <ramo temático>`. Estado ausente cai no **ramo
>   TEMÁTICO**, e o briefing manda o modelo escrever *"a medição encontrou
>   assunto próprio de pelo menos um grupo"* — sobre o filme cuja medição se
>   RECUSOU a decidir.
> - **Frontend** (`frontend/js/filme.js`, `veredictoBlock`): sem
>   `veredito.texto` cai no fallback de render, que com nenhum eixo acima da
>   margem produz a frase **VALORATIVA** — *"os grupos falam das mesmas coisas
>   e divergem no julgamento"*, que é a outra afirmação proibida ali.
>
> **Um defeito que produz as duas afirmações contrárias, por caminhos
> diferentes, merece estar escrito** — porque a lição não é "faltou um `elif`".
> É que **ausência tratada por omissão vira a asserção que o código já tinha à
> mão**, e qual delas é acidente da estrutura do `if`. Correção: os dois
> caminhos passam a ter tratamento EXPLÍCITO de estado ausente (`montar_briefing`
> devolve `None`, e o fallback de render é bloqueado), nunca um ramo padrão.


<!-- SPEC.md linhas 1162–1244 · origem: O limiar por `n`, e a taxa que ele realiza -->

#### O limiar por `n`, e a taxa que ele realiza

| n | limiar | taxa de falso contraste realizada |
|---:|---:|---:|
| 10 | 45,7pp | 0,060 |
| 15 | 37,3pp | 0,061 |
| 20 | 32,3pp | 0,049 |
| 25 | 28,9pp | 0,040 |
| 30 | 26,4pp | 0,075 |
| 35 | 24,4pp | 0,053 |
| **40** | **22,8pp** | **0,037** |
| 50 | 20,4pp | 0,040 |
| 100 | 14,4pp | 0,047 |

Entre **3,7% e 7,5%**, média ≈ 5%. A oscilação em torno do alvo é a
**quantização** — o lift só assume múltiplos de `100/n`, e em n=30 nenhum limiar
acerta 5% exatamente. **Leitura prática:** nos 29 filmes com 40/40/40 a lei dá
22,8pp e o corte operante é **25,0pp** (o próximo múltiplo de 2,5pp). A lei não
faz nada de mais fino que um limiar fixo de 25pp ali — **ela existe pelos outros
6**, cujos limiares são `talk-to-me-2022` 23,1 · `wicked-2024` 23,7 · `wonka`
25,5 · `the-godfather` 26,4 · `pearl-2022` 27,8 · `obsession-2026` 64,6.

#### O que mediu isso: o NULO DO MÁXIMO, que é novo

Três medições de nulo/reamostragem já existiam no projeto e **nenhuma era
esta**. O nulo de permutação da tabela histórica abaixo conta **pares (eixo,
bucket) agregados sobre o catálogo**; os bootstraps de
`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §8 e `docs/arquivo-de-estudos/classificacao/MEDICAO_VERIFICACAO_BINARIA.md` Entrega 2
reamostram em torno do **observado**. Faltava a distribuição do **máximo sobre
as 30 células sob a hipótese de que não há contraste nenhum** — que é a
estatística que o estado `contraste` de fato usa, porque `tematico` é
*"alguma das 30 células passa do limiar"*.

Desenho registrado ANTES de rodar em `docs/arquivo-de-estudos/margem-de-lift/DESENHO_NULO_DO_MAXIMO.md`; resultados em
`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_MARGEM_20PP.md`. **B = 10.000 permutações por filme, semente 24**,
embaralhando o rótulo de bucket dentro de cada filme — preserva o conjunto de
eixos de cada review intacto (logo toda a **dependência entre eixos da mesma
review**), a frequência global de cada eixo e o tamanho de cada bucket.

**O que ele mediu, e é o diagnóstico que fecha o caso da margem de 20pp:**

| | |
|---|---|
| percentil de 20pp no nulo (mediana dos 35) | **82** |
| taxa de falso contraste a 20pp, n=40 | **17,3%** |
| taxa de falso contraste a 20pp, no `n` MEDIANO em que o catálogo foi publicado (28) | **37,3%** |
| filmes distinguíveis do nulo a α=0,05, sem correção | **6 de 35** |
| … com Holm–Bonferroni sobre os 35 | **1 de 35** |
| FDR entre os 16 `tematico` sob cobertura 100% | **24% a 38%** |
| nos 6 filmes cujo veredito nomeia causa que o dado completo não sustenta: P(ruído) média | **0,633** |

O último número é o que justifica a mudança: **essas seis páginas nomeavam uma
causa que, na amostra em que foram decididas, tinha ~63% de chance de ser
sorteio.**

**E o `n` publicado nunca foi 40.** Reconstruído do campo `de_n` dos 35
`resultado/<slug>.json`: mediana **28**, média 27,3, mínimo **5**, com **56 dos
105 buckets abaixo de 30** e **24 abaixo de 20**. A frase "n≈40 é insuficiente
para a margem de 20pp" era verdadeira e otimista.

#### ⚠️ LIMITAÇÃO IN-SAMPLE — leia isto ANTES de expandir o catálogo

**A lei foi calibrada sobre exatamente os mesmos 35 filmes que ela julga.** Com
35 não existe como separar treino de teste sem perder todo o poder, e não foi
feito. Consequências, sem maquiagem:

- **A taxa de 5% é uma estimativa in-sample, e portanto OTIMISTA.** O valor
  out-of-sample é desconhecido e quase certamente maior. Não cite "5%" como
  propriedade da regra; cite como "5% medido nos 35 que a calibraram".
- **A constante 144,4 é `média(q95 · √n)` sobre n ∈ {20, 30, 40, 50, 100}** do
  nulo desses 35. Ela carrega a estrutura de co-ocorrência de eixos DESTE
  corpus (2,95 eixos por review em média, faixa 2,12–3,67). Um catálogo com
  carga de eixos diferente terá nulo diferente — **MEDIDO: corr(carga,
  P(falso)) = +0,74**, com a taxa indo de 0,119 a 0,206 entre os extremos do
  catálogo atual. É efeito de segunda ordem contra `n`, mas não é zero.
- **A expansão de catálogo é o PRIMEIRO teste out-of-sample desta lei, e deve
  ser tratada como teste.** Ao acrescentar filmes: rode o nulo do máximo sobre
  os filmes NOVOS, sozinhos, e compare a taxa realizada com a tabela acima. Se
  divergir materialmente, **é a constante que precisa ser recalibrada — não os
  filmes novos que estão errados.**
- **Nada aqui vale para filmes fora dos 35.** Nem a constante, nem a tabela, nem
  o piso de `n < 10` como "afeta 1 filme".


<!-- SPEC.md linhas 1275–1404 · origem: α = 0,05 e não 0,10 — a razão é assimetria de dano -->

#### α = 0,05 e não 0,10 — a razão é assimetria de dano

`docs/arquivo-de-estudos/margem-de-lift/ESTABILIDADE_10_FLIPS.md` isolou os dois erros e eles não custam o mesmo. Um
filme que deveria ser `valorativo` e sai `tematico` publica, em prosa
categórica, uma causa que não existe ("quem não recomenda rejeita pelo ritmo
arrastado"). Um filme que deveria ser `tematico` e sai `valorativo`
**subafirma** — deixa de contar algo verdadeiro, sem afirmar nada falso.
**Quando os dois erros custam coisas diferentes, o nível se escolhe pelo mais
caro.** α = 0,10 daria 9 `tematico` com FDR de ~24–39%; α = 0,05 dá 6 com FDR
de ~15–23%.

**Registrado como escolha, não como fato:** a multiplicidade entre os 35 filmes
NÃO é corrigida. Corrigir (Holm) responde *"existe alguma afirmação errada no
catálogo?"* — a pergunta certa se o produto fizesse uma afirmação sobre o
catálogo. Cada página faz sua própria afirmação, lida isoladamente, então o
controle certo é o de **proporção** (FDR), não o de família. Quem argumentar
que o leitor navega o catálogo inteiro e forma impressão agregada estará
pedindo Holm, e **não estará errado** — estará pedindo um catálogo com 1
`tematico`.

#### O que MUDA e o que NÃO MUDA de forma

**NÃO muda de forma:** o template do veredito continua ramificando em
`tematico`/`valorativo` com os mesmos dois blocos de instrução (§3[V]); a
interface continua com os mesmos comportamentos por ramo; a métrica de lift, a
seleção 2+3 de bullets, a taxonomia, o `taxonomia_id`, a cota 40/40/40, o
`assunto_compartilhado`, o piso de 25% e `min_chars` estão **intocados**.
**Só muda QUAIS filmes caem em cada ramo** — mais o caminho novo de estado
ausente, que é a única adição de forma da versão.

---

### A margem de 20pp — REGISTRO HISTÓRICO (v1.9.14 a v1.9.33)

**Esta seção descreve o parâmetro que vigorou até a v1.9.33 e não está mais em
vigor.** Fica porque o raciocínio dela é o que a lei acima substitui, e porque
a tabela de nulo por par continua sendo a medição correta de *outra* coisa (a
taxa de ruído por célula agregada).

Medida por **nulo de permutação** (2000 rodadas, embaralhando o rótulo de
bucket DENTRO de cada filme — preserva a frequência global de cada eixo e
destrói só a associação com o grupo). **Tabela original da v1.9.14, sob a
comparação `>` estrita que se revelou o mesmo bug de arredondamento da
medição de referência** (ver seção anterior) — mantida como registro
histórico:

| margem | pares acima | fração que cruzaria por acaso | filmes com ≥1 eixo acima |
|---|---:|---:|---:|
| 15pp | 41 | 63% | 22/35 |
| 20pp | 21 | 41% | 13/35 |
| 25pp | 12 | 29% | 9/35 |

**Recalculada na v1.9.15 sob `>=` exato** (a comparação corrigida, mesma
seção anterior) — os números que valem a partir desta versão:

| margem | pares acima | fração que cruzaria por acaso | filmes com ≥1 eixo acima |
|---|---:|---:|---:|
| 15pp | 44 | 61% | 24/35 |
| **20pp** | **27** | **34%** | **18/35** |
| 25pp | 13 | 27% | 10/35 |

(`scripts/recalcular_margem_exata.py`, rodado DEPOIS da unificação da
Entrega 1 — mesma metodologia da medição original de
`classificar_10.py`/`votacao_3.py`: 2000 rodadas de permutação, mesma
semente, embaralhando o rótulo de bucket dentro de cada filme; só a
aritmética do lift e da comparação muda de `float` para `Fraction`. Os
números de `pares`/`ruído` mudam por 1-2 unidades em relação à primeira
rodada desta versão — os 3 filmes estendidos pela Entrega 1 têm, na
classificação BRUTA que esta tabela usa, buckets de tamanho ligeiramente
diferente de 40 agora, porque `consenso.jsonl` acumula a seleção antiga e a
nova lado a lado; a contagem `filmes com ≥1 eixo acima` — o que a margem de
20pp de fato decide — não mudou. Esta tabela mede a REGRA sobre o catálogo
inteiro e usa a amostra classificada bruta por decisão metodológica de
longa data (não a analisada — essa é a base do bloco `eixos` publicado por
filme, §[D3]); a ordem de execução desta versão é RECALCULAR a tabela
DEPOIS de qualquer mudança na classificação, nunca antes.)

**Decisão do dono do projeto: 20pp.** Não há margem correta — é pureza de
lista contra cobertura, e o trade-off ficou mais caro depois da correção de
recall em review curta, porque a frequência média por eixo subiu. 20pp
segue sendo o ponto escolhido entre os dois extremos, com os números
recalculados aqui para que a escolha continue revisável com dado, não com
memória.

**CORREÇÃO DE REGISTRO (v1.9.34): o "34% que cruzaria por acaso" está medido na
população ERRADA, e o número na população certa é PIOR.** A tabela acima usa,
por decisão metodológica declarada logo abaixo, a amostra classificada **bruta**
(`consenso.jsonl`), que acumula a seleção antiga e a nova lado a lado (§[D3],
"duas populações de 40") e **não** é a população que o bloco `eixos` publicado
conta. Recalculada na população publicada (produção ∩ `consenso_verificado`,
cobertura 100% de §2.8), com o mesmo método:

| margem | pares acima (observado) | esperado sob o nulo | fração de ruído |
|---|---:|---:|---:|
| 15pp | 56 | 28,9 | **51,6%** |
| **20pp** | **23** | **9,9** | **42,8%** |
| 25pp | 11 | 3,7 | **33,3%** |

**A margem de 20pp entregava 42,8% de ruído por célula na população que o
produto de fato publicava, não 34%.** O número antigo não está errado para o
que mede; está medindo outra população. `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §6 já
registrava 41,1% num terceiro corpus, e o valor recomputado cai em cima dele.

### A comparação é `>=`, EXATA — revertida na v1.9.15

Cinco dos 35 filmes têm o melhor lift em **exatamente 20,0pp**: `barbie`,
`bones-and-all`, `hereditary`, `im-still-here-2024` e
`spider-man-across-the-spider-verse` (com cota 40, o quantum do lift é
2,5pp, e 20,0pp = 8 reviews de diferença — cair na linha não é raro, é
esperado).

A medição de referência (`resultado/votacao-3/metricas_lift.json`), a que
fundamentou a escolha original de margem, comparou com `>=` em ponto
flutuante — e `0,2` binário é ligeiramente MENOR que a fração exata: os
cinco caíram fora por acidente de representação, não por decisão, e é daí
que veio o número **13/35** que a v1.9.14 registrou como escolhido.

**A v1.9.14 tentou fechar essa falha trocando a comparação para ESTRITA
(`lift > margem`)** — errado: isso reproduzia o número 13/35 por construir
a MESMA fronteira que o bug produzia por acidente, em vez de corrigir o
bug e aceitar a fronteira real que a medição sempre mediu. Sob aritmética
exata **sempre foram 18/35** — o `>=` que a medição de referência pretendia
usar. **Decisão do dono do projeto (v1.9.15): manter a margem em 20pp, com
`>=` exato.** Contraste temático passa de 13 para **18 de 35 filmes**. O
critério original — "20pp entrega contraste em cerca de um terço dos filmes
sem publicar listas majoritariamente ruidosas" — **melhora** sob 18/35
(mais perto de um terço do catálogo que 13/35 estava), e `>=` é a semântica
natural de "margem mínima": um eixo com exatamente 20pp de lift ATINGE a
margem, não fica fora dela por uma fração de ponto percentual.


<!-- SPEC.md linhas 1458–1462 · origem: Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34) -->

*(Correção de registro, feita ao implementar: a primeira redação desta seção
dizia "6 / 29 / 1", que soma 36. `obsession-2026` estava contado duas vezes —
como `valorativo` sob a lei e como sem-estado sob o piso. Ele é UM filme, e o
piso o tira de `valorativo`, não o acrescenta.)*


<!-- SPEC.md linhas 1476–1526 · origem: Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34) -->

---

*A partir daqui, esta subseção é o registro da v1.9.14/v1.9.15, sob a margem
fixa de 20pp. As contagens abaixo (13/22, 18/17) são históricas.*

Filme sem NENHUM eixo acima da margem recebe `contraste: valorativo`. **São
22 de 35 filmes (63%) — quase dois terços do catálogo.** O estado não é caso
de borda; é o mais comum.

Isso **não é falha do produto**. Significa que os três grupos falam das
mesmas coisas e discordam apenas no veredito — informação honesta e
interessante sobre o filme. A consequência de desenho é obrigatória: o
estado precisa de tratamento de **primeira classe** (campo explícito no
JSON, o movimento 3 sabendo dizê-lo, e área visual própria na interface). Se
ficar como AUSÊNCIA de bullets de contraste, vai parecer bug ao leitor.

*(Nota de registro: a tabela da seção 7 de `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md`
rotula a coluna de 13/9/22 como `contraste: valorativo`; a coluna é, na
verdade, a de filmes COM contraste temático. A leitura correta é a desta
seção: a 20pp, 13 com contraste temático e 22 valorativos.)*

**Atualização da contagem (v1.9.15, `>=` exato; confirmada na v1.9.21):** sob
a comparação exata o catálogo é **18 `tematico` / 17 `valorativo`** de 35 — o
"22 de 35" acima é a contagem da v1.9.14, sob o `>` estrito que reproduzia o
bug de ponto flutuante. Fica no texto porque o raciocínio de desenho que ele
sustenta não muda: o estado não é caso de borda, é quase metade do catálogo.

**Achado da v1.9.21 — os 17 `valorativo` são EXATAMENTE os 17 filmes que
caem no ramo "os grupos falam das mesmas coisas" do veredito (§3[V]).**
Nenhum filme `valorativo` escapa do ramo. Os outros 3 filmes do ramo
(`joker-folie-a-deux`, `spider-man-across-the-spider-verse`, `wonka`) são
`tematico` com o contraste morando SÓ no bucket do meio — que nunca é um dos
dois lados do veredito. A consequência prática é de método, não de produto: a
verificação anti-fabricação de contraste do §3[V] é uma varredura de
**população inteira**, não de amostra.

### `impacto_emocional` entra no schema COM a limitação registrada

O eixo aparece em **75,5%** do corpus — o mais frequente por larga margem —
e tem **precisão medida de 0,486** contra o gabarito humano fechado de 100
reviews: **51% das marcações de produção são falsas**. Recall 0,921.

**Três tentativas de corrigir a saturação foram testadas e REFUTADAS por
medição** (detalhe em `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §5): lift normalizado
(amplifica o ruído, acima); separar eixo de cobertura de eixo de contraste
(move o problema — filmes sem nenhum bullet de contraste sobem de 17 para
20 de 35); e definição apertada no prompt (75,5%→71,3% projetado, segue
saturado; nos 13 veredictos secos que o gabarito humano desmarcou, a
variante deixou de marcar em só 3, e ADICIONOU marcação errada em 2 onde o
prompt original acertava).


<!-- SPEC.md linhas 1532–1704 · origem: `impacto_emocional` entra no schema COM a limitação registrada -->

Existe uma correção que **funcionou** — o passe de verificação separado
(V2 `alvo`), que leva a precisão de 0,486 para 0,794 em passada única, com
projeção de de-saturação de 75,5% para 35,7% no corpus.

**CORREÇÃO DE REGISTRO (v1.9.31): ela FOI aplicada, na v1.9.16, e este
parágrafo a descrevia como pendente desde então.** O texto anterior — *"uma
correção que funcionou e que NÃO foi aplicada… é decisão pendente do dono do
projeto"* — descrevia o estado de quando foi escrito, e não foi atualizado
quando a adoção aconteceu (changelog da v1.9.16, item 1). O passe roda como
estágio à parte após o consenso de votação
(`scripts/verificador_impacto.py aplicar-producao`), produz
`resultado/votacao-3/consenso_verificado.jsonl` + manifesto, e
`pipeline._carregar_consenso_producao` **prefere o verificado** quando ele
existe e está em dia — com erro explícito, não fallback silencioso, se
`consenso.jsonl` cresceu depois da verificação. A aplicação é declarada no
bloco publicado, em `eixos.verificador`.

**O estado do eixo MEDIDO NA APLICAÇÃO DO VERIFICADOR (v1.9.16, 2026-08-22) —
não é uma medição de "agora", ver a nota de reconciliação abaixo:**

| | `consenso.jsonl` (cru) | `consenso_verificado.jsonl` (**produção**) |
|---|---:|---:|
| `impacto_emocional` no corpus (n=4.181 **naquela data**) | 75,6% | **36,1%** |
| na seleção de produção (n=2.866) | 75,6% | **34,6%** |
| eixos por review | 3,42 | 3,01 |
| reviews sem nenhum eixo | 0,2% | 2,0% |

A projeção de 35,7% acertou dentro de 1pp. **O eixo não está mais saturado**;
`n_removidas_no_corpus` é 1.654 e está carimbado em cada filme publicado.

> ### RECONCILIAÇÃO DOS DENOMINADORES E DAS DUAS FRAÇÕES (2026-09-04)
>
> Esta spec cita **quatro** tamanhos diferentes para o que ela chama de "o
> corpus dos 35 filmes" — **2.866**, **4.056**, **4.181** e **5.371** — e
> **duas** frações para a mesma grandeza, **75,5%** e **75,6%**. Nenhum dos
> seis está errado; o que faltava era dizer a qual população e a qual momento
> cada um pertence. Conferido contra os arquivos em 2026-09-04.
>
> | número | o que é | fonte, verificável |
> |---:|---|---|
> | **2.866** | a seleção de produção ∩ o que estava classificado **antes** da extensão de cobertura — os 70,7% de §2.8 | histórico (§2.8) |
> | **4.056** | **a população de análise publicada**: a soma de `de_n` sobre os 35 `resultado/*.json`. É o denominador que o leitor vê | **conferido: soma = 4.056**, exatamente o "100%" de §2.8 |
> | **4.181** | o tamanho de `consenso.jsonl` **no momento em que o verificador rodou** (v1.9.16) | `resultado/votacao-3/relatorio_aplicacao.json`, campo `manifesto.fonte_n_linhas = 4181` |
> | **5.371** | o tamanho de `consenso.jsonl` / `consenso_verificado.jsonl` **hoje** | `wc -l`: 5.371 linhas, 5.371 ids únicos, 35 slugs, nos dois arquivos |
>
> **Por que 5.371 > 4.056, e por que isso é o desenho e não um erro:**
> `consenso.jsonl` **acumula a seleção antiga e a nova lado a lado** — é o
> "dois quarentas" registrado em §[D3] — enquanto a população publicada é só a
> seleção de produção corrente, filtrada por `eixos._filtrar_pela_analisada`.
> Exemplo conferido: `the-godfather` tem **129** linhas em
> `consenso_verificado.jsonl` e publica **110** (`de_n` 30 + 40 + 40). O
> arquivo de consenso é um superset por construção; **citá-lo como
> denominador de frequência publicada é o erro que `_filtrar_pela_analisada`
> existe para impedir.**
>
> **E as duas frações são de populações diferentes, então unificá-las num
> valor só seria introduzir um erro, não corrigir um:**
>
> - **75,5%** é a frequência medida no **estudo de classificação**
>   (`docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §5) — é o número que justifica o
>   verificador existir, e é a base das projeções registradas nesta seção
>   (75,5%→71,3% da definição apertada; 75,5%→35,7% do verificador);
> - **75,6%** (0,7563, exato) é a frequência medida **na aplicação em
>   produção**, sobre as 4.181 linhas de `consenso.jsonl` daquele dia —
>   `relatorio_aplicacao.json`, `freq_impacto_emocional.antes = 0.7563`, com
>   `depois = 0.3607` (os 36,1% da tabela acima).
>
> **A regra que fica:** toda frequência citada nesta seção vem acompanhada da
> população e da data. Um número sem denominador aqui é um defeito de
> registro, não uma abreviação.
>
> **PENDÊNCIA DE SINCRONIZAÇÃO, registrada e NÃO resolvida aqui:** o corpus
> classificado cresceu de 4.181 para 5.371 linhas depois da medição acima, e
> **as frequências desta tabela não foram recomputadas** sobre ele. Uma
> contagem direta hoje dá 76,97% no cru e 36,32% no verificado — próximo, mas
> **não é o mesmo evento**, e trocar os números da tabela por esses misturaria
> uma medição auditada (com manifesto, custo e telemetria) por uma contagem
> avulsa. Recomputar com o caminho oficial é trabalho de uma sessão de
> medição.

**O que NÃO mudou, e continua valendo:** a precisão de 0,486 é a do prompt de
classificação **sem** o passe, e é ela que justifica o passe existir; as três
tentativas de conserto pelo prompt seguem **refutadas** (parágrafos acima); o
ganho de margem é pequeno (15/35 filmes a 20pp contra 13/35 sem o passe, na
contagem da v1.9.14) — a de-saturação corrigiu a precisão do eixo, não o
problema do lift. E a dependência de arquitetura fica registrada como
limitação: a precisão de 0,79 depende de um **script separado** ter sido
rodado, e não de uma etapa do pipeline; o `taxonomia_id` cobre o prompt de
classificação, não o passe de verificação.

---

## 2.6 Feelings — EM ESPERA, com dependência de ordem registrada (2026-08-29)

Registro de decisão do dono do projeto. **Nada aqui está implementado, e nada
aqui autoriza implementar.**

**Feelings NÃO é descartado.** A medição de `docs/arquivo-de-estudos/classificacao/MEDICAO_SPLIT_E_FONTES.md`
(Entrega 3) achou que o TMDB emite `mood` editorial junto com as `keywords` —
`moody`, `bitter`, `playful`, `so bad it's good`, presentes em 17 de 35 filmes
— colidindo com a categoria que `docs/arquivo-de-estudos/classificacao/DESENHO_CLASSIFICACAO_V2.md` atribuiu à
review. **Essa colisão é argumento para NÃO misturar as duas fontes, não para
descartar uma delas.** As duas semânticas são diferentes e ambas são reais:

| fonte | o que a etiqueta significa | quem atribuiu |
|---|---|---|
| **review-derived** (`mood`, `experiencia`, `narrativa`) | o que ficou em quem assistiu | o público |
| **work-derived** (`tema`, `contexto`) | do que a obra trata — máfia, família, guerra | quem cataloga |

Elas continuam como **entidades internas SEPARADAS**, com listas próprias e
sem precedência de uma sobre a outra, exatamente porque `mood` do TMDB é
catalogação editorial e `mood` de review é relato de leitor. Fundi-las
produziria uma etiqueta cuja procedência o produto não saberia declarar.

**Feelings não avança até a granularidade/faithfulness dos TEMAS estar
resolvida.** A razão é de ordem, não de mérito: feelings é uma **segunda**
camada de classificação sobre o mesmo material, e adicioná-la a um sistema cuja
**primeira** camada ainda erra — `roteiro_estrutura` em 55,5% do corpus, a
contagem por tema sem gabarito confiável, o `contradiz` com recall medido em
~1 de 5 — aumenta o espaço de erro sem isolar a causa. Um filtro público errado
não seria distinguível de uma classificação de tema errada por baixo dele.

**A dependência, explícita:** feelings aguarda o veredito da verificação
binária por (review, tema) — a Entrega 1 de `docs/arquivo-de-estudos/classificacao/MEDICAO_VERIFICACAO_BINARIA.md`,
que **reprovou** no critério registrado. Enquanto a primeira camada não tiver
um número de menções que o código possa defender, a segunda não começa. As
cinco perguntas bloqueantes já listadas em `docs/arquivo-de-estudos/classificacao/DESENHO_CLASSIFICACAO_V2.md`
(entre elas o gabarito humano de ~100 reviews para feelings) continuam
valendo e são posteriores a esta.

**Ressalva acrescentada em 2026-08-30:** a reprovação da verificação binária
citada acima **não está estabelecida** — o critério que a produziu (C1a) foi
medido contra o gabarito dos 5 casos, que §2.7 mostra subestimar. Isso não
libera feelings: a dependência de ordem continua valendo, agora com a primeira
camada em estado *indeterminado* em vez de *reprovado*, o que é motivo igual
para não empilhar a segunda.

---

## 2.7 AVISO — o gabarito de contagem à mão dos 5 casos SUBESTIMA (2026-08-30)

**Quem for usar os cinco números de contagem à mão do `docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md`
§12 (`wonka`, `talk-to-me-2022`, `napoleon-2023`, `interstellar`, `cats-2019`)
precisa ler isto antes.** Eles já foram a régua de **duas** reprovações — a da
contagem por eixo (`docs/arquivo-de-estudos/classificacao/MEDICAO_CONTAGEM_E_AB.md`, Entrega 1) e a da verificação
binária (`docs/arquivo-de-estudos/classificacao/MEDICAO_VERIFICACAO_BINARIA.md`, critério C1a) — e **subestimam de
forma sistemática, não aleatória.**

**A causa é o protocolo, e está declarada no próprio estudo** (§12, "Protocolo
de leitura"): para cada bullet, ler **até 12** reviews que já carregam o eixo do
bullet, mais **até 6** que casam por palavra de conteúdo do tema. **Até 18 de
40**, e a segunda metade por casamento de palavra, num corpus multilíngue. Isso
não pode achar paráfrase, e não pode achar nada nos idiomas em que a palavra de
busca não foi escrita.

O estudo declarou um viés, mas na direção errada: escreveu que *"o viés deste
protocolo favorece o produto"* porque procura suporte onde ele é mais provável.
**Isso vale para o veredito qualitativo — achar suporte —, não para a
CONTAGEM:** ler 18 de 40 e casar por palavra só pode contar **a menos**.

**Os dois casos relidos por inteiro em texto corrido (as 40 reviews de cada
bucket, sem casamento por palavra):**

| caso | gabarito §12 | releitura integral | erro do gabarito |
|---|---:|---:|---:|
| `cats-2019` neg — *Experiência de visualização desconfortável* | 8 | **16** | **−8** |
| `interstellar` pos — *Fotografia e efeitos visuais deslumbrantes* | 8 | **14** | **−6** |

Em `interstellar` o número 8 **nunca teve derivação registrada**: o estudo
discute o *exemplo* do bullet e diz que o *tema* é "impecavelmente sustentado",
sem contar; o 8 aparece pela primeira vez na tabela de
`docs/arquivo-de-estudos/classificacao/MEDICAO_CONTAGEM_E_AB.md`.


<!-- SPEC.md linhas 1778–1844 · origem: Confiabilidade medida da leitura por modelo sob P1–P7 — NÃO tem direção fixa -->

### Confiabilidade medida da leitura por modelo sob P1–P7 — NÃO tem direção fixa

**CORREÇÃO DE REGISTRO (2026-08-31): a frase original aqui dizia que o
viés do modelo "tende ao conservadorismo", generalizando a partir de um
único ponto de calibração (`wonka`). Um segundo ponto (`talk-to-me-2022`)
mostrou o viés na direção OPOSTA. A generalização estava errada e o texto
abaixo a substitui — não a preserva como histórico, porque manteria uma
conclusão falsa disponível para leitura.**

**MEDIDO, três calibrações (leitura integral independente do dono e do
modelo, comparadas depois — `wonka`/negativas 32 reviews completas;
`talk-to-me-2022`/negativas e `napoleon-2023`/medianas com a folha reduzida
de duas etapas, §Consequência de desenho abaixo):**

| caso | tipo de julgamento | concordância |
|---|---|---:|
| `napoleon-2023`/med — *"Batalhas visualmente impressionantes"* | visual/concreto | **27/28 = 96,4%** |
| `wonka`/neg — *"Fotografia e efeitos visuais criticados"* | visual/concreto | **30/32 = 93,8%** |
| `talk-to-me-2022`/neg — *"Diálogos e tom juvenil artificiais"* | registro de fala, referência cultural, ironia | **10/14 = 71,4%** |

**A leitura correta não é "o modelo erra numa direção" — é que a
confiabilidade depende do TIPO de julgamento.** Temas visuais/concretos
("a fotografia é bonita/feia", "a batalha impressiona") têm alta
concordância nos dois casos medidos. Um tema de registro de fala — se a
gíria soa forçada, se uma referência cultural é a mesma coisa que o tema
afirma — tem concordância bem mais baixa, e a direção do erro nesse caso
foi para SUPERCONTAGEM, não subcontagem:

Em `talk-to-me-2022`, dos 5 casos que o modelo marcou `sustenta` (grupo G1),
**3 foram derrubados pelo dono** — o modelo aceitou como sustentação coisas
adjacentes ao tema (comparar o filme a um vídeo de conscientização escolar;
criticar o uso de memes num filme de terror; qualificar o diálogo de
"estilo Tarantino") sem que nenhuma delas afirme especificamente que a
gíria/diálogo *soa artificial/forçado*, que é o que o tema e a paráfrase
publicada afirmam. Em `wonka` e `napoleon-2023`, o padrão foi o oposto ou
ausente: em `wonka` o modelo perdeu um `sustenta` e um `contradiz`
(subcontagem, os dois casos do texto anterior); em `napoleon-2023` houve
só 1 discordância em 28, sem padrão de direção.

**Isso é o que justifica manter a leitura humana como DECISÃO, não como
fator de correção fixo.** Não existe um ajuste único ("some 1 sustenta",
"desconte 10%") que corrija a leitura do modelo em qualquer tema — o
próprio tipo de julgamento decide se o modelo tende a perder ou a
inflar, e isso só se sabe calibrando cada tema, não aplicando uma
constante.

### Achado novo — o modelo nunca usa "não sei julgar", mesmo devendo

**MEDIDO.** Nas 42 reviews das duas folhas reduzidas (`talk-to-me-2022` +
`napoleon-2023`), cobrindo pelo menos 6 idiomas além do português (inglês,
espanhol, francês, alemão, sueco, holandês, árabe, russo — a mistura variou
por bucket), **o modelo escolheu `não sei julgar` zero vezes**. Isso inclui
`viewing:1431255087` (árabe, `talk-to-me-2022`), que o dono marcou
corretamente como `não sei julgar` e o modelo respondeu `não sustenta` com
confiança implícita — sem sinalizar a limitação.

**A distinção que importa:** isto não é o mesmo erro que uma leitura errada
num idioma que o modelo de fato processa (esse é erro de interpretação,
esperado e mensurável pela concordância). É **excesso de confiança em
idioma dominado só parcialmente** — o modelo produziu um veredito com a
mesma aparência de certeza de qualquer outro, em vez de declarar a
limitação que a regra do prompt explicitamente autoriza ("é preferível a
chutar"). Zero ocorrências em 42 tentativas, num corpus que sabidamente
tem reviews em idiomas raros (ver a distribuição de idiomas do `wonka`,
§2.7 acima), é sinal de que a instrução de abstenção não está sendo
seguida na prática, não só de que o modelo raramente precisa dela.


<!-- SPEC.md linhas 1865–2043 · origem: Gabaritos fechados nesta calibração -->

### Gabaritos fechados nesta calibração

| caso | sustenta | contradiz | não sustenta | não sei julgar |
|---|---:|---:|---:|---:|
| `talk-to-me-2022`/negativas — *"Diálogos e tom juvenil artificiais"* | **2** | **0** | 11 | 1 |
| `napoleon-2023`/medianas — *"Batalhas visualmente impressionantes"* | **12** | **1** | 15 | 0 |

**`talk-to-me-2022` fechou em 2 — o mesmo número do gabarito antigo de
`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §12. Isto é COINCIDÊNCIA DE DESTINO, não validação
do protocolo antigo.** Os dois métodos chegaram ao mesmo número por
caminhos diferentes e por razões diferentes: o protocolo antigo leu uma
subamostra do bucket e casou por palavra-chave — o mesmo método que
§2.7 mediu subcontar em `cats-2019` (−8) e `interstellar` (−6), e que aqui
não tem nenhuma garantia de ter acertado por método, só por sorte de
amostra. O número desta sessão vem de leitura completa das 40 reviews com
resolução humana nos pontos de discordância — um processo auditável, com
frase literal registrada para cada veredito. Concordarem no valor final não
torna o protocolo antigo confiável; ele continua sem crédito.

---

## 2.8 Cobertura de classificação estendida a 100% (2026-08-30)

**Aplicado.** `1.190` reviews que faltavam classificar foram classificadas sob
a MESMA taxonomia (`ebab2667de74`), a mesma votação de 3 passadas, e o mesmo
verificador `V2_alvo`, pelo caminho oficial
(`scripts/estender_classificacao_producao.py` + `verificador_impacto.py
aplicar-producao`) — nenhum desenho novo. `pipeline.amostra_do_bruto` foi o
caminho usado (não `classificar_10.py:152`, que tem o defeito registrado em
§[D3]), então a extensão **não** reproduz o "dois quarentas". Custo medido por
diferença de linhas novas contra o commit-base: classificação US$ 0,1030
(3.570 chamadas), verificador US$ 0,0471 (964 chamadas) — **US$ 0,15 no
total**, não os US$ 0,03 nem os US$ 0,33 que duas projeções anteriores
estimaram.

**Cobertura: 100% verificada** (4.056/4.056, 35/35 filmes), não presumida —
conferida reconstruindo `amostra_do_bruto` para os 35 slugs e checando
interseção com `consenso_verificado.jsonl`.

### O que fecha

- **A ressalva de cobertura desigual de `docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §6c**
  (70,7%, 8 filmes abaixo de 50%) — fechada. Todo filme agora tem denominador
  de eixo igual ao denominador de análise.
- **A composição do bootstrap da margem** (§8 daquele estudo) — recomputada
  sobre a população completa; ver números abaixo.
- **As frequências por eixo publicadas** — recalculadas ao dígito sobre 100%
  da amostra; nenhuma se move mais que 1,2pp (tabela abaixo).

### O que NÃO fecha

- **O `n` por bucket** continua ~40 — a extensão preenche o denominador
  existente, não coleta review nova.
- **A margem de 20pp** não foi tocada nesta sessão — permanecia o parâmetro em
  vigor. **[v1.9.34] Deixou de ser: a margem fixa deu lugar à lei por `n`
  (§2.5), e a investigação que os 10 flips desta seção motivaram é exatamente
  a que a produziu.**
- **O gabarito dos 5 casos de `docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §12** — nenhum dos
  cinco foi relido; a extensão não tem relação com contagem de tema, só com
  cobertura de classificação por eixo.

### Achado principal — a margem porosa, confirmada com dado real

**MEDIDO.** Frequência por eixo: delta máximo **1,2pp** entre antes (n=2.866)
e depois (n=4.056) — a previsão registrada antes de rodar ("nenhuma
frequência se move mais que ~2pp") **se confirmou**.

A previsão sobre o estado `contraste` **não se confirmou**: **10 de 35 filmes
mudaram de estado** (6 tematico→valorativo, 4 valorativo→tematico) —
`bones-and-all`, `dune-2021`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `oppenheimer-2023`, `perfect-days-2023`,
`spider-man-across-the-spider-verse`, `the-substance`, `wicked-2024`.

**Investigado antes de prosseguir, como o critério desta sessão exigia.** A
causa **não é viés de conteúdo** das reviews que faltavam (a mesma medição que
sustentou a previsão original — comprimento e nota das 1.190 faltantes contra
as 2.866 já classificadas — permanece válida, e a frequência por eixo confirma
isso: delta máximo 1,2pp). A causa é que os 10 filmes tinham o lift observado
**a poucos pontos percentuais da margem de 20pp** (entre 14,9pp e 28,9pp nos
dois lados), e a margem já era conhecida como porosa nesse regime de n:
`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §8 mediu, por bootstrap, que 13 das 31 marcações de
contraste sobrevivem a **menos de 60%** das reamostragens. Seis dos dez filmes
que mudaram de estado — `bones-and-all`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `perfect-days-2023`,
`spider-man-across-the-spider-verse` — já estavam nomeados naquela lista de
marcações frágeis (p<60%), e `the-substance` no near-miss. **Isto não é um
achado novo de instabilidade — é o mesmo achado, agora observado com dado
completo em vez de reamostragem simulada**, e reforça (não contradiz) a leitura
de que n≈40 é insuficiente para a margem de 20pp decidir com confiança.

### Recálculo lado a lado

| | antes (n=2.866, 70,7%) | depois (n=4.056, 100%) |
|---|---:|---:|
| reviews órfãs | 337/2.866 = 11,8% | 477/4.056 = 11,8% |
| reviews sem eixo | 57 = 2,0% | 79 = 1,9% |
| células acima da margem (bootstrap) | 31 | 23 |
| — p < 60% | 14 | 12 |
| — 60–90% | 16 | 10 |
| — ≥ 90% | 1 | 1 |
| filmes `tematico` | 18 | **16** |
| filmes `valorativo` | 17 | **19** |

Frequência por eixo (maior delta): `impacto_emocional` +0,8pp · `livre`
+0,5pp · `roteiro_estrutura` +0,3pp · `comparacoes` +0,4pp · `atuacao` −1,2pp —
todos os 11 eixos dentro de ±1,2pp.

**Nota de honestidade sobre a suíte de testes.** A extensão expôs dois
defeitos pré-existentes na suíte, nenhum deles novo nesta sessão: (1) a
fixture `catalogo` de `tests/test_eixos.py` lia `consenso.jsonl` (cru,
pré-verificador) em vez de `consenso_verificado.jsonl` — resíduo de quando o
teste foi escrito na v1.9.15, nunca atualizado quando o verificador foi
adotado na v1.9.16; (2) nem essa fixture nem `verificador_impacto.py
_cobertura_exata`/`_corpus_consenso` aplicavam `eixos._filtrar_pela_analisada`
— o mesmo "dois quarentas" que a v1.9.15 corrigiu em `montar_bloco`, nunca
replicado nesses dois caminhos de teste/projeção. Com 9 de 105 buckets
acumulados (o estado antes desta sessão) os dois defeitos eram invisíveis;
com 93 de 105 (o estado depois de estender 32 filmes) eles quebraram os
testes visivelmente. (1) foi corrigido nesta sessão (fixture agora lê o
verificado). (2) foi corrigido na fixture de `test_eixos.py` (que agora
filtra), mas **não** em `verificador_impacto.py` — fora do escopo autorizado;
fica registrado como limitação conhecida em
`tests/test_verificador_impacto.py::test_base_da_projecao_reproduz_10_de_35`.
Suíte: **1.524 de 1.525** — um teste (`test_os_5_filmes_na_linha_dos_20pp_
agora_sao_tematicos`) foi retirado, não substituído: a sua premissa (5 filmes
nomeados sentados exatamente em 20,0pp) era uma coincidência da amostra
PARCIAL de antes da extensão e deixou de ser verdade por construção — não há
assinatura equivalente a reafirmar sob a amostra completa.

---

## 2.9 Defasagem entre os artefatos publicados e o consenso estendido (2026-08-31)

**Para quem chegar aqui sem contexto:** os arquivos `resultado/<slug>.json`
**não foram tocados** por §2.8 e **continuam internamente coerentes** — eixos,
lift, `contraste` e `veredito` concordam entre si dentro de cada arquivo
publicado. Não há inconsistência dentro do produto. O que existe é
**defasagem**: cada `resultado/<slug>.json` foi gerado sob a cobertura de
classificação vigente na hora em que rodou (para a maioria dos 35, 70,7% —
ver §2.5, "duas populações de 40"), e `resultado/votacao-3/consenso_
verificado.jsonl` agora tem cobertura 100% (§2.8). Os dois nunca foram
reconciliados por regeneração.

**Medido, sem regenerar nada:** sob o consenso completo, **10 de 35 filmes
teriam estado `contraste` diferente do publicado** — detalhado em
`docs/arquivo-de-estudos/margem-de-lift/ESTABILIDADE_10_FLIPS.md`, com o lift antes/depois de cada um e, para os 6
que virariam `tematico → valorativo`, o texto do veredito publicado hoje na
íntegra:

| filme | publicado | sob consenso completo |
|---|---|---|
| `bones-and-all` | tematico | valorativo |
| `everything-everywhere-all-at-once` | tematico | valorativo |
| `hereditary` | tematico | valorativo |
| `napoleon-2023` | tematico | valorativo |
| `perfect-days-2023` | tematico | valorativo |
| `spider-man-across-the-spider-verse` | tematico | valorativo |
| `dune-2021` | valorativo | tematico |
| `oppenheimer-2023` | valorativo | tematico |
| `the-substance` | valorativo | tematico |
| `wicked-2024` | valorativo | tematico |

**Decisão do dono: NÃO republicar por ora.** Razão registrada: o estado de
contraste desses 10 filmes está instável **perto da margem de 20pp**, e três
medições independentes concordam nisso — o bootstrap de
`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_CATALOGO_35.md` §8 (13/31 marcações sobrevivem a <60% das
reamostragens), a curva de retorno marginal por `n` (`MEDICAO_VERIFICACAO_
BINARIA.md`, Entrega 2: IC95 do lift dominante em 38,4pp com n=40, quase o
dobro da própria margem), e esta observação direta (§2.8, 6 dos 10 flips já
estavam na lista de marcações frágeis do bootstrap). **O estudo da margem —
a próxima sessão — pode reformular o limiar de 20pp, o que mudaria a lista
de filmes afetados.** Republicar agora, sob a margem atual, seria trabalho
refeito se a margem mudar.

**Esta defasagem é insumo do estudo da margem, não pendência esquecida.**
Qualquer sessão que reabra a margem de lift deve ler `ESTABILIDADE_10_
FLIPS.md` antes de decidir o novo limiar — ele é o conjunto de casos reais
que o novo limiar precisa resolver, não hipotéticos de bootstrap.


<!-- SPEC.md linhas 2067–2110 · origem: FECHADA na v1.9.34 — a republicação aconteceu, sob a lei nova -->

### FECHADA na v1.9.34 — a republicação aconteceu, sob a lei nova

**A defasagem descrita acima não existe mais.** O estudo da margem rodou
(`docs/arquivo-de-estudos/margem-de-lift/ESTUDO_MARGEM_20PP.md`), o dono aprovou a lei por `n` (§2.5), e os filmes
afetados foram republicados sob ela — **16 filmes**, não os 10 desta seção,
porque a lei muda mais estados que a extensão de cobertura sozinha. Os
`resultado/<slug>.json` e o consenso verificado voltam a estar reconciliados.

**A decisão de esperar se confirmou, mas por uma razão diferente da registrada
acima, e vale corrigir.** Esta seção disse que republicar sob 20pp "seria
trabalho refeito se a margem mudar". **MEDIDO: dos 10 filmes acima, apenas 2
(`dune-2021` e `wicked-2024`) teriam estado diferente sob a lei em relação ao
que a republicação sob 20pp lhes daria** — os outros 8 receberiam o mesmo
estado das duas vezes. A contabilidade real era 20 regenerações (10 agora + 10
depois) contra 16 (uma vez só): um argumento de **4 regenerações**, não do
trabalho inteiro. A razão FORTE para esperar era outra, e é a que valeu:
republicar sob 20pp colocaria no ar 16 estados com taxa de falso contraste de
24–38%, para tirar depois.

#### E a decomposição do custo confirma a espera por um argumento MAIOR

**MEDIDO ao planejar a republicação.** Sob o critério de BRIEFING (a regra
acima), 27 dos 35 filmes precisam de veredito novo. A causa de cada um:

| por que o briefing mudou | filmes |
|---|---:|
| **só a ressincronização de cobertura desta §2.9** (70,7% → 100%) | **19** |
| só a LEI nova de §2.5 | 3 (`obsession-2026`, `the-invite-2026`, `wonka`) |
| as duas | 7 |
| as duas, **cancelando-se** (não regera) | 1 (`wicked-2024`) |

**A maior parte deste custo não é o preço da lei nova — é o preço acumulado de
não ter republicado quando a cobertura foi a 100%.** Dezenove filmes carregam
briefing defasado por §2.8, e só três pela mudança de margem.

**Isto confirma a decisão de esperar retroativamente, e com um argumento mais
forte do que o que a fundamentou.** Ela foi tomada sobre "20 regenerações
contra 16" — 4 de diferença. O que se confirmou é que as duas correções, a de
cobertura e a de margem, **entram numa republicação só em vez de duas**, e que
a de cobertura era a maior das duas em volume. Republicar em §2.8 e de novo
agora teria custado 19 regenerações a mais, não 4.

---


<!-- SPEC.md linhas 5925–6006 · origem: DUAS POPULAÇÕES DE 40 — UNIFICADAS na v1.9.15 -->

#### DUAS POPULAÇÕES DE 40 — UNIFICADAS na v1.9.15

**Achado da v1.9.14, corrigido na v1.9.15.** Esta seção documenta o defeito
como foi medido e por que a correção era necessária; a tabela de
sobreposição abaixo é HISTÓRICA — depois da unificação, a sobreposição é
100% por construção em todo bucket dos 3 filmes publicados (verificado, não
presumido — número em `ROTULAGEM_CONFERENCIA.md`/changelog da v1.9.15).

**Por que a declaração não bastou.** A v1.9.14 tratou a divergência como
limitação aceitável, declarada em `fonte_classificacao` e no rótulo
"reviews classificadas" da interface. Isso viola o princípio central da
spec — frequência sempre com denominador visível — porque o denominador só
é verificável se aponta para a MESMA população que o texto ao lado resume.
"Estética e estilo vazios — 21/40" ao lado de "40 de 40 analisadas" com 67%
de sobreposição real é um denominador que aponta para outra população; é
pior que não ter denominador, porque parece verificável e não é. Uma nota
de rodapé não resolve — o leitor lê "21 de 40" e associa às 40 da amostra
ao lado, não às 40 que a nota descreve em abstrato.

`resultado/votacao-3/amostra.json` se declara "a população que a síntese
veria". **Não é.** Ela foi montada com `selecao.selecionar(todas, hist)` —
sem o argumento `orcamento_paginas_por_nivel`, que é o que liga a
**estratificação por profundidade** da v1.9.5 (§3[C2]). O pipeline de
produção passa esse argumento. Resultado: os dois lados selecionam 40
reviews do mesmo bucket, sob os mesmos filtros, e **não são as mesmas 40**.

Sobreposição medida (seleção de produção ∩ amostra classificada), 105
buckets do catálogo: **mediana 75%, mínimo 30%, máximo 100%**. Os 3 filmes
publicados estão entre os PIORES casos, e por um motivo estrutural — são os
que mais recoletas acumularam, logo os de bruto mais profundo, e é
exatamente onde a estratificação mais desloca a escolha:

| filme | negativas | medianas | positivas |
|---|---:|---:|---:|
| `cure` | 27/40 | 25/40 | 23/40 |
| `cidade-de-deus` | **13/40** | 19/40 | 15/40 |
| `the-invite-2026` | 17/40 | 13/40 | 17/40 |

**Por que isto importa tanto neste projeto.** É a mesma classe de defeito
que a spec já protege entre NOTAS e REVIEWS COM TEXTO (§D2, invariante de
vocabulário) e que a Entrega 6 desta versão fecha entre a janela da amostra
e a janela do histograma: duas populações diferentes que o texto não pode
apresentar como se fossem as mesmas pessoas. "40 de 40 analisadas" no
cabeçalho do grupo e "24 de 40" na linha do eixo são **dois quarentas
diferentes**.

**O que a v1.9.14 fez, mantido como registro histórico (a mitigação da
época, substituída pela correção estrutural abaixo):**

1. A frequência por eixo era calculada sobre a amostra CLASSIFICADA, não
   sobre a intersecção — preservava a calibração de 20pp, medida com `n=40`
   por bucket, às custas de um denominador que apontava para a população
   errada.
2. A divergência era declarada em `fonte_classificacao`
   (`n_classificadas`/`n_analisadas`/`sobreposicao_com_analisadas`).
3. A interface rotulava o denominador do eixo como *reviews classificadas*,
   distinto de *analisadas* no cabeçalho do grupo.

**A correção aplicada na v1.9.15: ESTENDER a classificação até cobrir a
seleção de produção inteira, sob o MESMO `taxonomia_id` e a MESMA votação de
3 passadas.** Não é reclassificar o corpus — o que já está classificado é
reusado, como o versionamento por `taxonomia_id` foi desenhado para
permitir. As reviews da seleção de produção que nunca passaram pela
classificação são as ÚNICAS que geram chamada nova.

Consequência aceita e verificada: `n=40` continua sendo `n=40` — a
calibração de 20pp não muda de unidade, só passa a contar as 40 reviews
certas. Os 3 filmes publicados são medidos sobre uma amostra que os outros
32 do catálogo não têm (ainda) — cada um deles segue com a amostra
CLASSIFICADA original até passar pela mesma extensão. O lift de cada eixo
nos 3 filmes foi recomputado antes/depois (changelog da v1.9.15) e o estado
`contraste` de cada um foi conferido explicitamente.

**Correção de registro, agora fechada:** o campo `criterio` de
`amostra.json` afirmava "a amostra é a população que a síntese veria" desde
a v1.9.5 sem que isso fosse verdade. Com a extensão da v1.9.15, para os 3
filmes publicados **volta a ser verdade por construção** — a divergência
`fonte_classificacao`/nota de rodapé perde objeto para esses 3 e é removida
do bloco (`sobreposicao_com_analisadas == n_classificadas == n_analisadas`
em todo bucket). Continua valendo para o resto do catálogo até a mesma
extensão ser aplicada lá.


<!-- SPEC.md linhas 8601–8636 · origem: (v1.9.34) O bloco `margem`, `acima_da_margem` por célula, e um DEFEITO que a lei por `n` expôs -->

### (v1.9.34) O bloco `margem`, `acima_da_margem` por célula, e um DEFEITO que a lei por `n` expôs

**O defeito, primeiro, porque ele desmente uma frase que estava escrita aqui.**
Esta seção afirmava que *"nenhuma decisão do código lê os derivados (a comparação
com a margem é exata)"*. **Isso era falso desde a v1.9.20.** Dois consumidores a
jusante decidem lendo `lift_pp`, que é o float **arredondado a uma casa**:

- `veredito.py:_maior_lift` → o campo `acima_da_margem` do briefing, que é o que
  decide se o veredito diz "ASSUNTO PRÓPRIO deste grupo";
- `frontend/js/filme.js:veredito()` → a frase de veredito montada em código.

Com a margem fixa **inteira** de 20pp o defeito era inofensivo por acidente
aritmético: `lift_pp` vinha de múltiplos de `100/n` e nenhum arredondamento podia
cruzar um inteiro. **`limiar(n) = 144,4/√n` é irracional, e o acidente acaba.**
Uma célula a menos de 0,05pp do limiar decidiria diferente no código exato e no
consumidor arredondado. **MEDIDO nas 35 × 30 células sob a lei: 0 divergências, e
nenhuma célula a menos de 0,15pp da fronteira** — mas o mecanismo já está vivo
(`wicked-2024` tem buckets 37/40/37, logo quantum de lift de **0,068pp**), e a
expansão de catálogo o aciona.

**O ALCANCE do defeito, e ele é menor do que parece — a varredura completa
achou um TERCEIRO canal, e é ele que explica por que nada nunca apareceu na
tela.** `bullet_de` (§4, acima) é computado por `eixos.bullets()` **com a mesma
comparação exata** de `contraste`, e é o que `briefing.py`, `frontend/js/
filme.js` (grade e ordenação de temas) e `frontend/js/home.js` leem para saber o
que é bullet de contraste. **Os BULLETS sempre estiveram certos.** O defeito
estava **confinado ao VEREDITO** — a frase que nomeia o assunto próprio de um
grupo —, em dois pontos (`veredito.py:_maior_lift` e o template de fallback de
`filme.js`), e não distribuído pela interface. Isto precisa ficar registrado
porque as duas coisas têm consequências diferentes: um defeito confinado a um
consumidor se conserta num lugar e não deixa rastro em dado publicado antigo;
um distribuído pela interface exigiria auditar tudo que já foi renderizado.
Aqui é o primeiro caso.

**A correção: `eixos.py` publica a decisão, e ninguém a recalcula.**

