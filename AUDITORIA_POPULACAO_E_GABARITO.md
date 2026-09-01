# Auditoria — duas contaminações, rastreadas separadamente

**Sessão de leitura e medição sobre dado existente. Zero chamada de LLM, zero
escrita em `resultado/`, nenhum filme regerado, `taxonomia_id` intacto
(`ebab2667de74`), suíte 1.525 passando.** Única escrita no repositório: o aviso
obrigatório em `SPEC.md` §2.7, e a ressalva em §2.6 que ele obriga.

**O veredito curto, e ele inverte a expectativa do briefing:**

> **Contaminação A (população errada) quase não existe.** O estudo principal
> declarou ter reconstruído a população de produção, e a declaração é
> **verdadeira** — verifiquei reproduzindo cada número publicado sob as duas
> populações candidatas, e todos batem com a certa, alguns ao dígito. Um único
> estudo periférico está contaminado, e o efeito nele é de ~1pp.
>
> **Contaminação B (gabarito errado) é grave e confirmada.** Ela derruba as
> **duas** reprovações que sustentava. Recomputando com apenas 2 dos 5 casos
> corrigidos, o erro do gabarito inverte os dois vereditos.

**Convenção:** **MEDIDO** traz número e fonte; **VISTO** é leitura à mão sobre
amostra nomeada; **NÃO VERIFICADO** é premissa que continua sem conferência.

---

# ACHADO 0 — a "descoberta" da sessão anterior já estava na spec, e o defeito tem nome

Antes do inventário, porque muda como ler tudo abaixo.

A sessão anterior reportou como achado que `amostra.json` não é a população da
síntese. **O defeito já estava medido, nomeado e parcialmente corrigido desde a
v1.9.14**, em `SPEC.md` §[D3], sob o título *"Duas populações de 40"* — com a
frase *"'40 de 40 analisadas' no cabeçalho do grupo e '24 de 40' na linha do
eixo são **dois quarentas diferentes**"*.

**A causa raiz, localizada agora no código:**
[`scripts/classificar_10.py:152`](scripts/classificar_10.py:152) chama
`selecionar(todas, hist)` **sem** `orcamento_paginas_por_nivel` — o parâmetro
que liga a estratificação por profundidade da v1.9.5. É exatamente o defeito
contra o qual a docstring de
[`pipeline.ids_analisados_do_bruto`](src/espectro24/pipeline.py:429) avisa:

> *"Omiti-lo é exatamente o defeito que produziu as duas amostras divergentes
> (§[D3]) — aqui ele é passado, e é por isso que este caminho reproduz a seleção
> de produção em vez de uma parecida com ela."*

O projeto tem **um módulo inteiro** para reconciliar as duas
([`uniao_amostra.py`](src/espectro24/uniao_amostra.py), v1.9.15) e um script de
orquestração ([`estender_classificacao_producao.py`](scripts/estender_classificacao_producao.py)).
A correção estrutural — estender a classificação até cobrir a seleção de
produção — **foi aplicada a 3 dos 35 filmes** (`cure`, `cidade-de-deus`,
`the-invite-2026`); os outros 32 seguem divergentes por decisão registrada.

**O que a sessão anterior de fato acrescentou, e é real:** a quantificação da
sobreposição em **67,6%** no catálogo inteiro, e a confirmação de fidelidade da
reconstrução em 105/105 buckets. Isso não estava medido. O que não é novo é a
existência da divergência.

**Consequência para esta auditoria:** o campo
`eixos.fonte_classificacao.por_bucket[]` **já declara** a divergência em cada
filme publicado. Um estudo que leu esse campo estava avisado.

---
---

# ENTREGA 1 — o inventário

## Método: verificação por reprodução, não por leitura de descrição

O scratchpad das sessões que produziram `ESTUDO_CATALOGO_35.md`,
`MEDICAO_CONTAGEM_E_AB.md` e `MEDICAO_SPLIT_E_FONTES.md` **não foi persistido**
— varri os 62 diretórios de sessão em disco. Sem o código, a alternativa a
acreditar na descrição é **reproduzir cada número publicado sob as duas
populações e ver qual bate**. É o que fiz, e é um teste mais forte que ler o
código, porque testa o artefato.

As duas populações candidatas:

| | definição | n |
|---|---|---:|
| **P_prod** | seleção de produção reconstruída do bruto (`pipeline.amostra_do_bruto`) | 4.056 |
| **P_amostra** | `resultado/votacao-3/amostra.json` ≡ `consenso_verificado.jsonl` | 4.181 |
| **P_prod ∩ consenso** | a intersecção — o que o bloco `eixos` publicado conta | **2.866** |

## A distinção que organiza tudo, e que o briefing não separava

**`amostra.json` não é "a população errada" em geral. Ela é a população
CERTA para perguntas sobre o CLASSIFICADOR** — é, por construção, o conjunto que
o classificador processou. Precisão, recall, reprodutibilidade e comparação de
prompts são propriedades do classificador sobre o texto que ele viu.

Ela só é a população **errada** quando o estudo **cruza com um artefato
publicado** — um bullet, uma barra, um lift, uma órfã, uma cobertura. Aí a
pergunta deixa de ser sobre o classificador e passa a ser sobre o produto, e o
produto foi construído sobre P_prod.

Contaminação A só morde nessa segunda classe. Isso reduz muito o alcance dela,
e é o motivo de o inventário abaixo ter tantas linhas limpas.

## A tabela

| estudo / seção | usou `amostra.json`? | usou o gabarito dos 5? | população afetada | números dependentes | precisa rerodar? |
|---|---|---|---|---|---|
| **ESTUDO §1–5** — eixo por gênero, redundância, cobertura de bullets | **não** — só `resultado/*.json` | não | nenhuma | 629 bullets, 619 com eixo, 158 `roteiro_estrutura` (25%) | **Intacto** |
| **ESTUDO §6a** — menções por bullet | **não** | não | nenhuma | média 10,7 · razão soma/n 1,67 | **Intacto** |
| **ESTUDO §6b** — calibração manual de 8 bullets | não | **é a origem** | — | razão à mão/`mencoes` 1,02 | **Rerodar** (contaminação B) |
| **ESTUDO §6c** — órfãs e cobertura | **não — P_prod ∩ consenso** ✅ | não | — | **11,6% órfãs · 70,7% cobertura · 2,0% sem eixo** | **Intacto** |
| **ESTUDO §7** — frequência por eixo no corpus | **não — P_prod ∩ consenso** ✅ | não | — | **`roteiro_estrutura` 55,5% · `comparacoes` 36,4%** e os 9 outros | **Intacto** |
| **ESTUDO §8** — bootstrap da margem | **não — P_prod ∩ consenso** ✅ | não | — | **31 células · 13 abaixo de 60% · 92,5%/71,9%** | **Intacto** |
| **ESTUDO §12** — 5 casos de generalização excessiva | não | **é a origem** | — | contagens 1/2/13/8/8 | **Rerodar** (contaminação B) |
| **CONTAGEM E AB — Entrega 1** (contagem por eixo) | **não — P_prod ∩ consenso** ✅ | **sim, na tabela decisiva** | — | Δ barra 66% dos bullets · colisão 28% · **"eixo pior em 2 dos 5"** | **Rerodar** (só a tabela dos 5) |
| **CONTAGEM E AB — Entrega 3** (A/B passada única) | **não** — universo declarado é P_prod ∩ consenso | não | — | F1 A 0,817 vs B 0,814 · IC95 cruza zero | **Intacto** |
| **SPLIT E FONTES — Entrega 1** (split de `roteiro_estrutura`) | frame não documentado | não | **nenhuma — imune** | C1 51,3% · C2 8,1pp · **C3 50,3%** · controle ±5,3pp | **Intacto** (ver nota) |
| **SPLIT E FONTES — Entrega 2** (`comparacoes`) | idem | não | nenhuma — imune | −2,3pp · 3,90 vs 2,50 eixos | **Intacto** |
| **SPLIT E FONTES — Entrega 3** (keywords TMDB) | não — TMDB | não | nenhuma | 589 distintas · 83% singleton | **Intacto** |
| **SPLIT E FONTES — Entrega 4** (lista de ids) | não | não | nenhuma | +14% saída · **US$ 0,03 / US$ 3,74** | **Nota** (custo refutado por medição, não por população) |
| **VERIFICAÇÃO BINÁRIA — Entrega 1** | **não — P_prod reconstruída** ✅ | **sim, é o critério C1a** | — | **MAE 5,00 → REPROVA** | **Rerodar** (contaminação B) |
| **VERIFICAÇÃO BINÁRIA — Entrega 2** (curva 1/√n) | **não — consenso, por bucket** | não | — | IC95 38,4pp · P(temático) 0,769→0,718 | **Intacto** |
| **ESTABILIDADE_AGREGADA** (200 reviews) | **sim** — 56% na intersecção | não | classificador | 2,18pp · núcleo 2,57 · `livre` 3,23 | **Intacto** (frame correto p/ classificador) |
| **auditoria de acurácia** (gabarito de 100) | **sim** — `_carregar_universo` lê `amostra.json` | não | classificador | **precisão `impacto_emocional` 0,486** · recall 0,35 em curtas | **Intacto** (frame correto p/ classificador) |
| **TAXONOMIA_10 / GATE / VOTAÇÃO_3 / verificador `V2_alvo`** | **sim** | não | classificador | precisão 0,486→0,794 · 1.654 removidas | **Intacto** (frame correto) |
| **`vies_recall_curtas.py`** | **sim, e chama de "as 3990 que `selecionar()` entrega à síntese"** | não | **projeta sobre "frequência publicada"** | `share_publicado` por eixo | **Nota/correção** — efeito medido: **1,1pp** |
| **testes** (`test_eixos`, `test_pipeline_eixos`, `test_uniao_amostra`, `test_contrato_falha_lote`) | só como nome de fixture em `tmp_path` | não | nenhuma | — | **Intacto** |

**Nota sobre SPLIT E FONTES Entrega 1:** o documento não registra de qual
arquivo a amostra de 260 foi sorteada, e isso é uma lacuna de registro real.
Mas o teste é **estruturalmente imune** a A: ele classifica texto de review sob
duas taxonomias e compara os dois braços **na mesma amostra**. Nunca cruza com
um bullet publicado. Qualquer amostra justa de review do catálogo serve, e as
duas populações são isso. O peso de corpus 0,555 que ele usa na extrapolação de
C1 é o número de P_prod ∩ consenso, ou seja, o certo.

## As reproduções que sustentam as linhas ✅

**MEDIDO — frequência por eixo no corpus.** Todo número publicado bate com
`P_prod ∩ consenso`, e nenhum bate com `P_amostra`:

| eixo | **P_prod ∩ cons** | P_amostra | publicado |
|---|---:|---:|---|
| `roteiro_estrutura` | **55,5%** | 55,9% | **55,5%** ✅ |
| `comparacoes` | **36,4%** | 39,3% | **36,4%** ✅ |
| `direcao_imagem` | **30,4%** | 33,1% | 30,4% ✅ |
| `ritmo` | **29,1%** | 31,3% | 29,1% ✅ |
| `atuacao` | **27,9%** | 28,5% | 27,9% ✅ |
| `critica_social` | **23,1%** | 23,8% | 23,1% ✅ |
| `tom_atmosfera` | **22,0%** | 23,8% | 22,0% ✅ |
| `expectativa` | **19,9%** | 20,8% | 19,9% ✅ |
| `som_trilha` | **12,7%** | 13,7% | 12,7% ✅ |
| `impacto_emocional` | **34,6%** | 36,1% | as duas, rotuladas ✅ |
| `livre` | **9,1%** | 8,9% | 9,1% ✅ |
| n | **2.866** | 4.181 | **2.866** ✅ |

Onze de onze. A spec §2.5 publica `impacto_emocional` nas **duas** populações,
cada uma rotulada com o seu `n` — registro correto.

**MEDIDO — cobertura e órfãs (§6c).** P_prod = **4.056**, intersecção =
**2.866**, cobertura **70,7%** — os três ao dígito. Órfãs: minha
reimplementação dá 337/2.866 = 11,8% contra os 332 = 11,6% publicados; o
denominador bate exato e `sem eixo` bate exato (**57 = 2,0%**). A diferença de 5
reviews é detalhe de definição da minha reimplementação (tratamento dos 10
bullets `livre`, que não têm linha em `linhas[]`), **não** diferença de
população: sob `P_amostra` o denominador seria 4.181 e o resultado 11,0%.

**MEDIDO — bootstrap da margem (§8).** Sob `P_prod ∩ consenso`: **31 células
acima da margem**, exatamente o publicado; sob `P_amostra`, 30. A distribuição
publicada (1 acima de 90% · 17 entre 60–90% · 13 abaixo de 60%) reproduz o
compartimento do meio ao número (**17**); a divisão entre os outros dois sai
0/17/14 na minha execução contra 1/17/13 na publicada. **É uma célula só,
oscilando na fronteira dos 90%** — a "única marcação robusta" do catálogo
(`eighth-grade`/`impacto_emocional`/positivas, p = 92%) cai para ~89% sob outra
sequência de PRNG. Ruído de reamostragem, não população.

## As linhas que dão problema

**`vies_recall_curtas.py` — Contaminação A, efeito medido em 1,1pp.** O
docstring afirma que `amostra.json` são *"as 3990 reviews que `selecionar()`
entrega à síntese"*. É falso duas vezes: não é a seleção de produção, e o 3.990
é a versão pré-extensão da v1.9.15. E ele computa `share_publicado` por eixo a
partir dela. **MEDIDO — a variável que move o resultado (fração de reviews
curtas) quase não muda entre as duas populações:**

| faixa | P_amostra | P_prod | Δ |
|---|---:|---:|---:|
| 150–200 chars | 23,4% | 24,5% | **+1,1pp** |
| 201–300 | 25,0% | 26,9% | +1,9pp |
| 301–400 | 14,9% | 14,0% | −0,9pp |
| 401+ | 36,7% | 34,7% | −2,0pp |
| mediana | 309 | 293 | −16 |

O viés projetado escala com a fração de curtas, que se move 1,1pp. **Correção de
registro, não rerrodada.**

---
---

# ENTREGA 2 — as conclusões de produto

Esta é a tabela para ler sozinha.

| conclusão de produto | contaminação | veredito | razão |
|---|---|---|---|
| **"11,6% de reviews órfãs"** | nenhuma | **SOBREVIVE** | reproduz sob P_prod ∩ consenso com denominador exato (2.866) e `sem eixo` exato (57). O proxy de eixo declarado no estudo continua sendo a limitação real, não a população |
| **"a classificação cobre 70,7% das analisadas, desigualmente"** | nenhuma | **SOBREVIVE** | 2.866/4.056 reproduz ao dígito. E ela **não é defeito de medição — é o defeito real**, o §[D3] da spec, corrigido em 3 de 35 filmes |
| **"13 das 31 marcações sobrevivem a menos de 60%"** | nenhuma | **SOBREVIVE, com 1 célula de folga** | as 31 células reproduzem exatamente sob a população certa (30 sob a errada); a partição 13/17/1 sai 14/17/0 sob outro PRNG. A leitura — "o contraste é poroso" — é robusta; o "13" tem ±1 de ruído de bootstrap |
| **"`roteiro_estrutura` está em 55,5% das reviews"** e a tabela por eixo | nenhuma | **SOBREVIVE** | 11 de 11 eixos reproduzem ao dígito sob P_prod ∩ consenso. **O braço de controle da sessão seguinte não é o que blinda o número** — ele mede variância entre execuções do classificador, não população; o que blinda é a reprodução direta acima |
| **"`comparacoes`: 36,4% das reviews contra 2,4% dos bullets, razão 0,07"** | nenhuma | **SOBREVIVE** | 36,4% reproduz sob a população certa; 15/629 = 2,4% vem só de `resultado/*.json`; razão 0,066 |
| **"o `mood` do TMDB colide com o `mood` de review"** | nenhuma | **SOBREVIVE** | vem de 35 requisições ao TMDB, sem review nenhuma |
| **"a curva de retorno é 1/√n, IC95 38,4pp com n=40, sem cotovelo"** | nenhuma | **SOBREVIVE** | calculada por bucket sobre o consenso; não cruza bullet publicado |
| **"o pool elegível é ~66/bucket, não centenas"** | nenhuma | **SOBREVIVE** | derivado do bruto direto |
| **A rejeição do SPLIT de `roteiro_estrutura`** | nenhuma | **SOBREVIVE** | C1/C2/C3 comparam dois braços na mesma amostra e nunca tocam bullet publicado. C3 (50,3% com ≥2 sub-eixos, contra o teto de 46,4%) é imune por construção. O diagnóstico que ela gerou — *a unidade errada é a review, não o eixo* — também |
| **A rejeição do estreitamento de `comparacoes`** | nenhuma | **SOBREVIVE** | −2,3pp dentro do ruído; a hipótese alternativa (3,90 vs 2,50 eixos) roda sobre P_prod ∩ consenso |
| **A rejeição da CONTAGEM POR EIXO** | **B, na tabela decisiva** | **RECALCULAR — e o argumento que sobra muda de dono** | ver abaixo |
| **A rejeição da VERIFICAÇÃO BINÁRIA** | **B, é o critério C1a** | **CAI como estava; INDETERMINADO agora** | ver abaixo |
| **"`mencoes_aproximadas` é bem calibrado na mediana (razão 1,02)"** | **B** | **CAI** | os 8 bullets de §6b saíram do mesmo protocolo. Se ele subconta, a razão à mão/`mencoes` está sistematicamente **baixa**, e "bem calibrado" pode ser "subestimado por igual dos dois lados" |
| **"o modo de falha real não é invenção, é promoção"** (0 casos de "informação não encontrada") | **B, parcialmente** | **SOBREVIVE** | o veredito *qualitativo* (achar suporte) é onde o viés declarado do protocolo de fato favorece o produto. Ler 18 de 40 procurando suporte e não achar nenhum é evidência forte de ausência; é a **contagem** que o protocolo estraga, não a busca |
| **"precisão de `impacto_emocional` 0,486 → 0,794 com `V2_alvo`"** | nenhuma (frame de classificador) | **SOBREVIVE** | gabarito de 100 reviews anotadas à mão, sobre o conjunto que o classificador processou — a população certa para a pergunta |
| **"recall 0,35 em reviews ≤200 chars"** | nenhuma | **SOBREVIVE** | idem |
| **"o passe por review custa US$ 3,74 em 300 filmes"** | nenhuma | **JÁ CAIU** | refutado por medição direta na sessão anterior: **US$ 23,82**. Erro de projeção de contexto, não de população |

## A rejeição da contagem por eixo — o que sobra

**MEDIDO — recomputando a tabela decisiva com os 2 casos relidos:**

| caso | gab. §12 | gab. revisado | `mencoes` | contagem de eixo |
|---|---:|---:|---:|---:|
| `wonka` neg | 1 | 1 *(não relido)* | 6 | 3 |
| `talk-to-me` neg | 2 | 2 *(não relido)* | 5 | 8 |
| `napoleon` med | 13 | 13 *(não relido)* | 15 | 13 |
| `interstellar` pos | 8 | **14** | 11 | 9 |
| `cats-2019` neg | 8 | **16** | 10 | 17 |
| **erro absoluto médio** | | | **3,00 → 3,80** | **3,60 → 2,80** |

Sob o gabarito de §12, a contagem de eixo era **pior** que o LLM na média (3,60
contra 3,00). Sob a correção parcial, ela é **melhor** (2,80 contra 3,80). A
frase publicada *"em 2 dos 5 a contagem de eixo é PIOR que a do LLM"* continua
literalmente verdadeira nas duas versões — mas os dois casos em que ela é pior
mudam de identidade, e a média inverte.

**A rejeição continua sustentada, e agora por argumentos melhores:**

1. **O argumento conceitual, e ele é o principal:** o eixo é **superconjunto**
   do tema. `tom_atmosfera` conta as reviews que falam de clima; o bullet fala
   de *diálogos juvenis*, que são um subconjunto delas. Trocar o número do tema
   pelo do eixo é **erro de categoria**, não de calibração — e um erro de
   categoria não melhora quando o gabarito melhora. **Independente de B.**
2. **A colisão de barras:** 175 de 629 bullets (28%), em 70 de 105 buckets,
   passariam a repetir a barra de um vizinho — até **quatro bullets com a mesma
   barra** em `joker-folie-a-deux`/negativas e `cure`/negativas. Publica uma
   equivalência que o dado não sustenta. **Independente de B.**
3. **Dois bullets com barra zero**, afirmando ao leitor "nenhuma review deste
   grupo mencionou isto" ao lado de um texto que diz o contrário. **Independente
   de B.**

**O que CAI da justificativa original:** o argumento numérico de que a contagem
de eixo está *mais longe da verdade*. Sob o gabarito corrigido ela está **mais
perto**. A rejeição deve ser reapresentada como *"resolve o número e quebra a
leitura"*, não como *"o número novo é pior"*.

## A rejeição da verificação binária — considerando SÓ os motivos independentes

**MEDIDO — C1a sob os dois gabaritos:**

| | gab. §12 | gab. com 2 de 5 corrigidos |
|---|---:|---:|
| MAE `mencoes_aproximadas` (o limiar) | 2,80 / 3,00 | **3,80** |
| MAE verificação binária, execução A | **5,20** | **2,40** |
| MAE verificação binária, execução B | 3,60 | **1,20** |
| **C1a** | **REPROVA** | **PASSARIA** |

**C1a inverte.** E a direção do erro residual é conhecida: os três casos não
relidos vêm do mesmo protocolo que subconta, então corrigi-los tende a
**subir** os alvos — o que favorece ainda mais o instrumento que conta alto. O
sinal parcial existe: a sessão anterior leu à mão as 4 frases que o passe citou
em `wonka` e julgou **3 genuínas**, contra o gabarito de 1.

**Considerando SÓ os motivos independentes do gabarito, o veredito é: NÃO
IMPLEMENTAR EM PASSADA ÚNICA — e a razão principal deixa de ser a acurácia.**

| motivo | depende do gabarito? | número |
|---|---|---|
| reprodutibilidade entre execuções idênticas | **não** | **Jaccard 0,70**; `wonka` de 4 para 1 menções (−75%) |
| recall de `contradiz` | **não** — veio de releitura integral de `cats-2019` | **1 em 5**, e uma das perdidas foi contada como `sustenta` |
| falso positivo "veredito seco como experiência" | **não** — releitura integral | 6 em 22 no bucket relido |
| custo real | **não** | **US$ 23,82** em 300 filmes com 3 votos = 2,4× a classificação por eixo inteira |
| C1a (acurácia contra gabarito) | **SIM** | inverte |

Um número que muda 75% entre duas execuções idênticas do mesmo prompt não é
autoridade sobre nada, e isso basta sozinho contra a passada única. **Mas a
reprovação registrada não estava fundada nisso — estava fundada em C1a, que
não sobrevive.** O estado honesto é: *a acurácia é indeterminada; a
estabilidade reprova a passada única; a votação de 3 não foi medida e é a
única intervenção conhecida contra a instabilidade.*

---
---

# ENTREGA 3 — o que foi recalculado nesta sessão

Tudo que segue foi refeito **sem chamada de LLM**, só com dado em disco e
código.

| item | número antigo | número novo | fonte |
|---|---|---|---|
| frequência dos 11 eixos no corpus | 55,5% · 36,4% · … | **idênticos** | reprodução sob P_prod ∩ consenso |
| cobertura da classificação | 70,7% (2.866/4.056) | **idêntico** | idem |
| reviews sem nenhum eixo | 2,0% (57) | **idêntico** | idem |
| órfãs | 11,6% (332/2.866) | **11,8% (337/2.866)** | reimplementação; Δ = tratamento dos 10 bullets `livre` |
| células acima da margem | 31 de 1.050 | **idêntico (31)** | bootstrap B=2.000 |
| partição do bootstrap | 1 / 17 / 13 | **0 / 17 / 14** | ±1 célula na fronteira dos 90%, ruído de PRNG |
| MAE de `mencoes` contra o gabarito | 3,00 | **3,80** | gabarito com 2 de 5 corrigidos |
| MAE da contagem de eixo | 3,60 | **2,80** | idem |
| MAE da verificação binária (exec. A) | 5,20 | **2,40** | idem |
| distribuição de comprimento (viés de curtas) | 23,4% ≤200 | **24,5% ≤200** | P_prod vs P_amostra, Δ 1,1pp |
| `pipeline.ids_analisados_do_bruto` ≡ reconstrução da sessão anterior | — | **21/21 buckets idênticos** | conferência cruzada |

## O que exige LLM ou releitura humana — NÃO executado

| item | por quê | custo estimado |
|---|---|---|
| **refazer o gabarito dos 3 casos restantes** (`wonka` 32, `talk-to-me` 40, `napoleon` 40 reviews) | leitura humana integral; é o item de maior retorno da fila | **112 reviews**, ~2–3 h de leitura atenta |
| **refazer §6b** (8 bullets da calibração manual) | mesmo protocolo antigo | ~**320 reviews**, ~6–8 h |
| **votação de 3 na verificação binária** | 3× as chamadas do passe | **US$ 23,82** em 300 filmes · **US$ 2,79** só nos 35 |
| **medir se `contradiz` funciona em passe próprio** | prompt novo, amostra nova | ~US$ 0,05 numa amostra do tamanho da anterior |
| **estender a classificação aos 32 filmes** (fechar o §[D3]) | classificar ~1.190 reviews × 3 votos | ~US$ 0,03, **e fecharia a cobertura de 70,7% para 100%** |

**Nota sobre o último:** ele é barato e resolve o defeito estrutural que 3 de 35
filmes já resolveram. Não é escopo desta sessão, mas é a intervenção de melhor
razão custo/benefício que este inventário encontrou.

---
---

# ENTREGA 4 — o gabarito dos 5: refazer, não aposentar

## A decisão

**Refazer. Não aposentar.** Três razões, em ordem de peso.

1. **Sem gabarito não há como decidir nada sobre contagem.** Duas abordagens já
   foram reprovadas contra ele e as duas reprovações caem. Aposentar a régua sem
   substituto deixa o projeto sem critério para a próxima proposta — e a
   próxima proposta virá, porque `mencoes_aproximadas` continua sendo um número
   escolhido pelo LLM contra o princípio do §0.
2. **O defeito é do protocolo, não dos casos.** Os cinco buckets são bons alvos:
   são os que a leitura qualitativa já sinalizou como problemáticos, cobrem
   quatro eixos diferentes (`direcao_imagem` ×3, `tom_atmosfera`,
   `impacto_emocional`) e três buckets. Trocá-los por outros cinco perderia essa
   curadoria e não consertaria nada.
3. **O custo é pequeno e já foi 40% pago.** Faltam **112 reviews** —
   `wonka`/negativas (32), `talk-to-me-2022`/negativas (40),
   `napoleon-2023`/medianas (40). `cats-2019` e `interstellar` já foram relidos
   por inteiro.

**O que muda de status:** os cinco deixam de ser "gabarito" e passam a ser
**"gabarito de 2, suspeita de 3"** até a releitura. Nenhum critério de aceite
deve citá-los como régua enquanto isso.

## O protocolo exigido

**P1 — Leitura integral do bucket.** Todas as 32–40 reviews da seleção de
produção daquele bucket, reconstruída por `pipeline.amostra_do_bruto(slug)`
(105/105 buckets conferidos contra o publicado). **Sem** amostragem, **sem**
teto de 12 ou 18, **sem** ordenar por tamanho.

**P2 — Proibido casamento por palavra-chave.** É a causa raiz. O corpus é
multilíngue e as evidências reais que o protocolo antigo perdeu são paráfrases:
*"JFC that was rough"*, *"I just felt like gouging my eyes out"*, *"einen
Zustand, den man nicht mehr los wird"*, *"The scale makes my brain hurt"* —
nenhuma casa com palavra de conteúdo de *"experiência de visualização
desconfortável"*.

**P3 — Julgar no idioma original.** Não traduzir antes de decidir. Duas das
evidências perdidas em `talk-to-me` estão em russo e português.

**P4 — Contar no nível do TEMA, não do exemplo.** `mencoes_aproximadas` é
declarado por tema e a barra do frontend é por tema. O gabarito antigo **mistura
os dois níveis** — conta `wonka` pelo exemplo (1) e `napoleon` pelo tema (13) —
e essa mistura sozinha já invalida comparações entre casos. O `exemplo_
parafraseado` serve para desambiguar o que o tema quer dizer, nunca como texto a
casar.

**P5 — Registrar a frase literal de cada review contada.** É o que torna o
gabarito novo **auditável** — a falha do antigo é justamente que 8 dos 5
números não têm derivação registrada (`interstellar` não tem nenhuma). Sem a
frase, o gabarito novo herda o defeito do velho.

**P6 — Três valores, não dois.** `sustenta` / `não sustenta` / `contradiz`. A
releitura de `cats-2019` achou **5 contradições explícitas** contra o tema
publicado, e um gabarito binário as esconderia — que é exatamente o erro que
gerou o achado `wonka`.

**P7 — Registrar o protocolo e o resultado ANTES de comparar com qualquer
método.** O gabarito é a régua; medi-la depois de ver o que se quer aprovar é
como reescrever o critério.

## O custo em esforço

| | valor |
|---|---|
| reviews a ler | **112** (32 + 40 + 40) |
| comprimento mediano | ~293 caracteres |
| tempo estimado | **2–3 h** de leitura atenta, com a frase literal anotada |
| chamadas de LLM | **zero** — é leitura humana por definição; um LLM lendo é o instrumento sob teste, não a régua |
| pré-requisito | nenhum; os três buckets estão em disco e reconstruíveis |

**Uma segunda opinião independente em pelo menos um dos três buckets** é
desejável e não foi feita em nenhum dos dois já relidos — a releitura de
`cats-2019` e `interstellar` é de uma pessoa só, e está declarada como tal.

## Registro na SPEC — aplicado

Escrito em **`SPEC.md` §2.7**, seção nova, com título em caixa alta para ser
encontrado por quem grep: *"AVISO — o gabarito de contagem à mão dos 5 casos
SUBESTIMA"*. Contém a causa (o protocolo de até 18 de 40 com casamento por
palavra), os dois casos medidos como evidência (`cats-2019` 8 → 16,
`interstellar` 8 → 14), a tabela de MAE que mostra as duas reprovações
invertendo, a lista do que continua de pé sem o gabarito, e o protocolo P1–P7.

Acrescentei também uma ressalva em **§2.6** (feelings), porque aquele parágrafo
citava a reprovação da verificação binária como estabelecida — ela não está.
A dependência de ordem para feelings **não muda**: a primeira camada passa de
*reprovada* para *indeterminada*, o que é motivo igual para não empilhar a
segunda.

---

# Resumo

**Contaminação A é quase inexistente, e a apuração é o resultado.** O
`ESTUDO_CATALOGO_35.md` afirmou ter reconstruído a população de produção, e a
afirmação é verdadeira: **11 de 11 frequências por eixo, a cobertura de 70,7%,
o denominador de 2.866 e as 31 células do bootstrap reproduzem sob `P_prod ∩
consenso` e não reproduzem sob `amostra.json`**. O A/B da passada única declara
o universo certo. O teste do split é estruturalmente imune. Os estudos de
classificador (auditoria de acurácia, estabilidade, taxonomia, verificador)
usam `amostra.json` e **é a população certa para eles** — é o conjunto que o
classificador processou. **Um único script está contaminado**
(`vies_recall_curtas.py`, que chama `amostra.json` de "as 3990 que `selecionar()`
entrega à síntese"), e o efeito medido é de **1,1pp** na variável que move o
resultado: correção de registro, não rerrodada.

**Contaminação B é grave e derruba as duas reprovações que sustentava.** Com
apenas 2 dos 5 casos relidos, o erro absoluto médio de `mencoes_aproximadas`
contra o gabarito sobe de 3,00 para **3,80**, o da contagem por eixo cai de 3,60
para **2,80**, e o da verificação binária cai de 5,20 para **2,40** — **C1a
passaria**. A rejeição da contagem por eixo **continua de pé pelos argumentos
estruturais** (o eixo é superconjunto do tema; 28% dos bullets perderiam barra
própria; dois bullets publicariam barra zero), mas deve ser reapresentada como
*"resolve o número e quebra a leitura"* e não como *"o número novo é pior"*. A
rejeição da verificação binária **cai como estava** e vira **indeterminada**:
o que sobra contra ela é a instabilidade entre execuções (Jaccard 0,70), o
recall de `contradiz` de 1 em 5 e o custo de US$ 23,82 — suficiente contra a
passada única, insuficiente contra o desenho.

**E o defeito de população não era novo.** Ele está na spec desde a v1.9.14 como
§[D3] *"Duas populações de 40"*, com causa localizada agora em
[`classificar_10.py:152`](scripts/classificar_10.py:152) (`selecionar()` chamado
sem `orcamento_paginas_por_nivel`), um módulo dedicado a reconciliá-lo
(`uniao_amostra.py`) e a correção estrutural **aplicada a 3 dos 35 filmes**.
Estendê-la aos outros 32 custa ~US$ 0,03 e fecharia a cobertura de 70,7% para
100% — a melhor razão custo/benefício que este inventário encontrou.

**O gabarito deve ser refeito, não aposentado:** faltam 112 reviews, ~2–3 h,
zero LLM, sob o protocolo P1–P7 registrado em `SPEC.md` §2.7.
