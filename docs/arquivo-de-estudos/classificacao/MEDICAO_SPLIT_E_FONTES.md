# Medição — o split reprova, e o que isso ensina

**Cinco entregas. A primeira é a que importa: o split proposto para
`roteiro_estrutura` REPROVA nas três condições do critério registrado antes de
rodar.** Reporto e paro, como combinado; não reescrevi definição para o teste
caber no desenho.

Nada em `resultado/` foi escrito. Nenhum filme regerado. `taxonomia.py`
intacto, `taxonomia_id` segue `ebab2667de74` (conferido). Suíte: 1.525 testes
passando. Única escrita em arquivo do repositório: a correção de registro da
Entrega 5 em `SPEC.md`, que foi o que o briefing pediu.

**Chamadas de LLM:** 1.560 (780 do braço proposta + 780 do braço controle),
sobre a amostra registrada de 260 reviews, `deepseek-v4-flash`. Custo ≈ US$
0,09. Mais 35 requisições ao TMDB, sem LLM.

**Convenção:** **MEDIDO** traz número e fonte; **VISTO** é leitura à mão sobre
amostra nomeada; **NÃO VERIFICADO** é premissa que continua sem conferência.

---

# ENTREGA 1 — o split de-satura no nível de REVIEW?

## Critério de aprovação, fixado antes de rodar

Registrado em `CRITERIO_REGISTRADO.md` (scratchpad da sessão) **antes de
qualquer chamada**, com nenhum resultado da amostra visto. Reproduzido aqui na
íntegra.

A proposta original trazia duas condições. **Adotei as duas e acrescentei uma
terceira, com justificativa**, porque as duas primeiras juntas têm um buraco:
três sub-eixos a 35% cada satisfazem C1, e um deles com gradiente satisfaz C2,
**mesmo que sejam as mesmas reviews recebendo os três rótulos**. Nesse caso a
divisão não separou — replicou. C3 é a condição que testa isso, e é a pergunta
que o briefing nomeia como decisiva.

**C1 — Teto de frequência.** Nenhum sub-eixo acima de **40%** do corpus.
*Justificativa:* o eixo saudável mais frequente hoje é `comparacoes`, 36,4%;
40% dá margem acima dele.

**C2 — Poder de separação.** Pelo menos um sub-eixo com amplitude entre
buckets **≥ 10pp**. *Justificativa:* hoje `ritmo` 16,5pp, `tom_atmosfera`
14,5pp, `impacto_emocional` 10,3pp — 10pp é "pelo menos tão bom quanto o
terceiro melhor separador que existe".

**C3 — Não-replicação.** Entre as reviews que recebem **pelo menos um**
sub-eixo, no máximo **37,7%** recebem dois ou mais, e no máximo **14,1%**
recebem os três. *Justificativa, medida antes de fixar o limiar:* sobre os
**120 trios possíveis de eixos existentes** (n≥200), a fração que carrega ≥2
do trio tem mediana 32,7%, p25 28,1%, **p75 37,7%**, máximo 46,4%; a que
carrega os três tem mediana 4,7% e **máximo 14,1%**. Os limiares são o p75 e o
máximo observados: se os três sub-eixos forem mais emaranhados que o trio mais
emaranhado que já existe, a divisão replicou. *Zona cinzenta declarada:* ≥2
entre 37,7% e 46,4% = reprovação parcial, decisão do dono.

## Amostragem, também registrada antes

- **A1 — estrato PORTADOR** (carrega `roteiro_estrutura` hoje): **N = 200**,
  por bucket (67/67/66) × faixa de comprimento (≤200 / 201–500 / 501–1200 /
  >1200), ~17 por célula.
- **A2 — estrato CONTROLE** (NÃO carrega): **N = 60**, 20 por bucket.
  *Por que existe:* sem ele a frequência de corpus de um sub-eixo novo é só um
  limite inferior — uma review que hoje recebe só `atuacao` pode receber
  `personagem` sob a taxonomia nova, e esse vazamento é invisível numa amostra
  só de portadores. **C1 depende deste estrato.**
- **A3** máximo 8 reviews por filme · **A4** PRNG semente 24 sobre
  `(slug, bucket, id)` · **A5** célula sem candidatos cede a vaga — **não foi
  acionada**.

Obtido: 260 reviews · 35 filmes · portadores 67/67/66 por bucket e 48/50/51/51
por faixa · mediana 507 chars.

## Método

**3 passadas independentes, consenso ≥2 de 3** — idêntico à produção.
Necessário para comparabilidade: as frequências de referência (55,5%, 36,4%)
são de CONSENSO, e passada única produz número sistematicamente maior.

Prompt: os 12 eixos da proposta, definições e regras R1–R5 **copiadas de
`DESENHO_CLASSIFICACAO_V2.md` sem alteração**, não ajustadas durante a rodada.
As 7 definições herdadas de eixos inalterados foram conferidas **byte a byte**
contra `taxonomia.SYSTEM` por asserção.

**Braço de controle, acrescentado depois de ver o resultado e antes de
reportá-lo:** a MESMA amostra, o MESMO método, sob a taxonomia de **produção**
(10 eixos, prompt byte-idêntico). Existe porque sem ele o resultado negativo
seria atacável por dois confundidores — a ausência do verificador de
`impacto_emocional` nesta sessão, e a variância entre execuções. Custou mais
780 chamadas e vale cada uma.

---

## Resultado — C1

| sub-eixo | portadores | controle | **CORPUS estimado** | C1 (≤40%) |
|---|---:|---:|---:|---|
| `personagem` | 46,0% | 6,7% | **28,5%** | PASSA |
| `enredo_desfecho` | 83,0% | 11,7% | **51,3%** | **REPROVA** |
| `escrita` | 26,5% | 1,7% | **15,5%** | PASSA |

*(Corpus estimado = 0,555 × portadores + 0,445 × controle, com o peso vindo da
fração medida de reviews que hoje carregam `roteiro_estrutura`.)*

**`enredo_desfecho` absorveu o eixo saturado quase inteiro.** A comparação
justa vem do braço de controle, rodado na mesma amostra com o mesmo método:

| | controle (10 eixos) | proposta (12 eixos) |
|---|---:|---:|
| `roteiro_estrutura` | **60,8%** | — (extinto) |
| `enredo_desfecho` | — | **51,3%** |
| `personagem` | — | 28,5% |
| `escrita` | — | 15,5% |

**O split moveu o eixo saturado de 60,8% para 51,3% — 9,5pp.** Não é
de-saturação; é um eixo saturado com nome novo. **C1 REPROVA.**

## Resultado — C2

| sub-eixo | negativas | medianas | positivas | amplitude | C2 (≥10pp) |
|---|---:|---:|---:|---:|---|
| `personagem` | 23,1% | 31,1% | 31,2% | **8,1 pp** | — |
| `enredo_desfecho` | 48,2% | 55,1% | 51,2% | 6,9 pp | — |
| `escrita` | 17,3% | 15,1% | 13,7% | 3,7 pp | — |

Referência: `ritmo` 16,5pp · `tom_atmosfera` 14,5pp · `roteiro_estrutura`
5,2pp (produção) / 6,5pp (controle).

**Maior amplitude 8,1pp, abaixo do piso de 10pp.** O ganho sobre o eixo que a
divisão substitui é de 6,5pp para 8,1pp — 1,6pp. **C2 REPROVA.**

## Resultado — C3, e é a reprovação mais dura

Entre os **191 portadores** que recebem ao menos um sub-eixo:

| | n | % |
|---|---:|---:|
| exatamente **1** sub-eixo | 95 | 49,7% |
| **2** sub-eixos | 72 | 37,7% |
| **3** sub-eixos | 24 | 12,6% |
| **≥2 (limite 37,7%)** | **96** | **50,3%** |

**50,3% > 46,4%** — pior que o trio **mais emaranhado** que existe hoje na
taxonomia (`direcao_imagem`+`roteiro_estrutura`+`comparacoes`), e muito acima
da mediana de 32,7%. Não é zona cinzenta. **C3 REPROVA.**

Par a par: `personagem`+`enredo_desfecho` **40,8%** · `enredo_desfecho`+
`escrita` 19,9% · `personagem`+`escrita` 14,7%.

## VEREDITO

| condição | resultado |
|---|---|
| C1 teto de frequência | **REPROVA** (`enredo_desfecho` 51,3%) |
| C2 poder de separação | **REPROVA** (máx. 8,1pp) |
| C3 não-replicação | **REPROVA** (50,3% ≥2) |
| **conjunto** | **NÃO APROVADO** |

**O split de três, como desenhado, não deve ser implementado.**

---

## O diagnóstico — e é aqui que a reprovação vira informação útil

O emaranhamento não é uniforme. Ele é **função do comprimento da review**:

| faixa | n com ≥1 sub-eixo | 1 sub | 2 sub | 3 sub | **≥2** |
|---|---:|---:|---:|---:|---:|
| ≤200 chars | 45 | 71% | 29% | 0% | **28,9%** ✅ |
| 201–500 | 48 | 73% | 25% | 2% | **27,1%** ✅ |
| 501–1200 | 47 | 40% | 45% | 15% | **59,6%** ❌ |
| >1200 | 51 | 18% | 51% | 31% | **82,4%** ❌ |

**Nas duas faixas curtas o split PASSA em C3 com folga. Nas duas longas ele
colapsa.** As 24 reviews que recebem os três sub-eixos têm comprimento mediano
de **2.124 chars**, contra 507 da amostra portadora.

**VISTO** — as quatro primeiras reviews que receberam os três, lidas à mão,
mostram por quê. Esta, de `bones-and-all`/negativas (596 chars), é
representativa:

> *"Everything it's too predictable: every scene, every line of dialogue,
> every narrative choice. Timothée Chalamet plays an edgy boy that says
> cliches for 2 hours straight, Taylor Russell plays an impersonal shy girl
> that falls in love with said edgy boy just because they are the
> protagonists and rom-com rules say that they must love each other even if we
> don't see the reason for that."*

Ela fala de previsibilidade (`escrita`), de diálogo (`escrita`), das duas
protagonistas e da relação entre elas (`personagem`), e de escolha narrativa
(`enredo_desfecho`). **Os três rótulos estão corretos.** A divisão não errou;
a review realmente cobre os três.

**A conclusão que isso força, e que a proposta não tinha:** o problema não é a
taxonomia, é a **unidade de classificação**. Uma review de 2.000 caracteres
sobre um filme toca quase tudo que 12 eixos sabem nomear — subdividir um eixo
não a torna mais específica, só multiplica os rótulos que ela recebe. Isso é
consistente com o resto do dado: reviews com `roteiro_estrutura` carregam
**3,83** eixos, contra 2,29 das que não carregam (produção); no braço proposta,
portadores subiram de 4,33 (controle) para **4,46** eixos por review — a
taxonomia cresceu 20% e a densidade por review acompanhou.

**Enquanto a unidade for a review inteira, dividir eixos redistribui rótulos
sem aumentar resolução.** É a mesma conclusão a que a Entrega 4 chega por outro
caminho.

## Validação do instrumento — o braço de controle

O controle reproduz a produção dentro de ±5,3pp em 10 dos 11 eixos:

| eixo | controle | produção | Δ |
|---|---:|---:|---:|
| `ritmo` | 28,4% | 29,1% | −0,7 |
| `direcao_imagem` | 31,5% | 30,4% | +1,1 |
| `expectativa` | 20,2% | 19,9% | +0,3 |
| `livre` | 9,0% | 9,1% | −0,1 |
| `som_trilha` | 13,4% | 12,7% | +0,7 |
| `comparacoes` | 39,0% | 36,4% | +2,6 |
| `tom_atmosfera` | 18,1% | 22,0% | −3,9 |
| `critica_social` | 27,4% | 23,1% | +4,3 |
| `atuacao` | 33,2% | 27,9% | +5,3 |
| `roteiro_estrutura` | 60,8% | 55,5% | +5,3 |
| **`impacto_emocional`** | **80,9%** | **34,6%** | **+46,3** |

O único desvio grande é `impacto_emocional`, e ele é **esperado e
diagnóstico**: esta sessão não roda o passe verificador `V2_alvo`, que em
produção remove 1.654 marcações. 80,9% aqui contra 75,6% no consenso cru
confirma que o instrumento está medindo o que deveria. **Isso é o piso de
variância entre execuções: ~±5pp.** O ganho de 1,6pp em C2 está dentro dele; a
queda de 9,5pp em C1 está fora, mas é pequena demais para salvar a proposta.

Reprodutibilidade entre as 3 passadas: **19,7% (proposta) contra 18,8%
(controle)** — as três passadas devolvem conjunto idêntico com a mesma
frequência. **A divisão não custa estabilidade**, e esse é o único indicador em
que ela não piora.

Disciplina de lista fechada: 23 rótulos fora da taxonomia em 779 chamadas
(proposta) contra 15 em 780 (controle). O mais frequente na proposta é
`atracao` (5×), inventado. E `crítica_social` **com acento** aparece nos dois
braços — o mesmo modo de falha que o estudo achou em produção, agora medido
uma terceira vez.

## Limites desta entrega

- **N=260, uma execução, um modelo.** O piso de variância medido é ~±5pp, e
  C1/C3 reprovam por margens de 11pp e 12,6pp — acima do ruído. C2 reprova por
  1,9pp, **dentro** do ruído: sozinho, C2 seria inconclusivo.
- **O prompt de 12 eixos não foi otimizado.** É a redação do documento de
  desenho, sem ajuste, e é 60% mais longo que o de produção. Um prompt melhor
  escrito poderia melhorar as margens — mas não plausivelmente o modo de
  falha, que é estrutural: as reviews longas cobrem os três assuntos de fato, e
  isso está na leitura à mão, não na redação do prompt.
- **`enredo_desfecho` não foi decomposto.** Não sei quanto dos 51,3% é
  "coerência" e quanto é "desfecho" — precisaria de outra rodada.
- Este teste mede **frequência e emaranhamento**, não **acurácia**. Não há
  gabarito humano para os três sub-eixos; nada aqui diz se `personagem` foi
  atribuído corretamente.

## O que fazer com a reprovação

Três caminhos, em ordem do que o dado sustenta:

1. **Não dividir, e atacar a unidade.** É o que o diagnóstico aponta. Com
   classificação por unidade menor (frase, ou "afirmação"), `roteiro_estrutura`
   deixa de ser um rótulo que 56% das reviews recebem e passa a ser um rótulo
   que N frases recebem — e aí a subdivisão pode fazer sentido, porque a
   unidade é específica o bastante para pertencer a um sub-eixo só. É também o
   que a Entrega 4 recomenda por conta própria.
2. **Dividir em DOIS, não três.** `personagem` (28,5%, o único sub-eixo que
   passou C1 com folga e o mais legível para o leitor) e o resto continuando
   como `roteiro_estrutura`. Não testado; a co-atribuição
   `personagem`+`enredo_desfecho` de 40,8% sugere que também falharia C3, mas
   com dois rótulos o teto de emaranhamento é outro e o critério teria de ser
   refixado. **Não recomendo sem medir.**
3. **Aceitar `roteiro_estrutura` como está e parar de tentar consertá-lo pela
   taxonomia.** É o que `CLASSIFICACAO_CONSOLIDADO.md` §8 já registra sobre o
   lift: quatro intervenções, nenhuma resolveu. Esta é a quinta.

---
---

# ENTREGA 2 — a definição estreitada de `comparacoes`

Mesma amostra, mesma rodada, mesmo método. A comparação é contra a
classificação **atual na mesma amostra**, não contra os 36,4% do corpus — a
amostra tem composição diferente (43,5% de `comparacoes` na classificação de
produção, porque é enviesada para portadores de `roteiro_estrutura`).

## Efeito sobre a FREQUÊNCIA

| | n | % da amostra |
|---|---:|---:|
| definição **atual** (braço controle) | 107 | **41,2%** |
| definição **estreitada** (braço proposta) | 101 | **38,8%** |
| **delta** | | **−2,3 pp** |

Composição do delta: **26 reviews saíram, 20 entraram.** O saldo de −6 é
resultado de 46 trocas.

**MEDIDO: a definição estreitada não reduz a frequência.** −2,3pp está bem
dentro do piso de variância entre execuções medido nesta mesma sessão (~±5pp,
com `atuacao` variando +5,3pp e `critica_social` +4,3pp sem que nada tenha
mudado na definição delas). E o churn de 46 trocas para um saldo de 6 indica
que o estreitamento não está *filtrando* — está *mexendo*.

**VISTO** — o que saiu não deveria ter saído. Duas das seis primeiras
exclusões:

- `the-hateful-eight`/negativas: *"Те же бешенные псы, только в разы дороже"*
  — "os mesmos Cães de Aluguel, só que muito mais caros". É uma comparação com
  outro filme do mesmo diretor, exatamente o caso que a definição estreitada
  diz **incluir**.
- `dune-part-two`/negativas: *"In the first film, Paul Atreides was treated
  like a legendary figure before I ever understood why I should care about
  him"* — comparação com o filme anterior da franquia, também dentro da
  definição estreitada.

## Efeito sobre o BULLET-SHARE

**Não medido, e não mensurável nesta sessão** — exigiria rodar síntese, que
está proibido. O que posso reportar é a inferência e a evidência que a
sustenta.

## A hipótese alternativa que o briefing levantou, testada

*"A razão 0,07 pode não significar 'definição larga demais', e sim que
comparar é comum na review e pouco útil como bullet."*

**MEDIDO, sobre o corpus de produção (n=2.866):**

| | reviews COM `comparacoes` | reviews SEM |
|---|---:|---:|
| n | 1.044 (36,4%) | 1.822 |
| **eixos por review** | **3,90** | **2,50** |
| `comparacoes` é o único eixo | 43 (4,1%) | — |

Com que eixo `comparacoes` aparece acompanhada: `roteiro_estrutura` 58% ·
`direcao_imagem` 39% · `atuacao` 33% · `ritmo` 31% · `impacto_emocional` 30%.

**Em 95,9% das vezes a comparação convive com outro eixo, e a review que
compara é sistematicamente mais rica (3,90 eixos contra 2,50).** Comparar não é
o assunto da review — é uma cláusula dentro de uma review cujo assunto está em
outro lugar. *(Contexto: estar sozinho é raro para quase todo eixo — `ritmo`
2,4%, `atuacao` 2,2%, `critica_social` 10,0%. O que distingue `comparacoes` não
é a solidão, é a companhia: ela marca review longa.)*

**A hipótese alternativa é a mais bem sustentada pelos dados.** A razão 0,07
descreve uma síntese que está **certa** em raramente promover a comparação a
tema: em ~96% dos casos a comparação é acessória à afirmação principal.
Estreitar a definição mexeria no denominador do lift e não no bullet-share.

## Recomendação da Entrega 2

**Retirar a proposta de estreitamento de `comparacoes`.** Ela foi motivada pela
razão 0,07 lida como "definição larga demais", e essa leitura não se sustenta:
o estreitamento não reduz a frequência (−2,3pp, dentro do ruído), exclui casos
que ele mesmo diz incluir, e a assimetria que o motivou tem explicação melhor.

**O que fica em aberto e é a pergunta certa:** `comparacoes` a 36,4% com 3,9pp
de amplitude é um eixo que quase não separa grupos. Se ele deve continuar sendo
um eixo de contraste, ou virar metadado de review (útil para saber que a review
é rica, inútil para saber no que os grupos discordam), é decisão de produto que
esta medição não resolve — mas ela agora tem número dos dois lados.

---
---

# ENTREGA 3 — as `keywords` do TMDB existem e servem?

35 requisições a `/movie/{tmdb_id}` com
`append_to_response=credits,images,keywords`, reusando o `tmdb_id` já gravado
em cada ficha. Sem LLM. Gravado só no scratchpad.

**Premissa de custo CONFIRMADA:** `credits` e `images` continuaram vindo
preenchidos na mesma resposta em 35 de 35. **Nenhuma requisição nova** —
`keywords` é literalmente um item a mais no `append_to_response` que
[ficha.py:341](src/espectro24/ficha.py:341) já monta.

## Cobertura

| | valor |
|---|---|
| keywords por filme | média 20,7 · **mediana 21** · min **0** · max 44 |
| filmes com **zero** | **1** — `talk-to-me-2022` |
| filmes com ≤10 | **7 (20%)** |

Os sete magros: `talk-to-me-2022` (0), `friday-the-13th-2009` (6),
`eighth-grade` (8), `the-invite-2026` (9), `wonka` (9),
`joker-folie-a-deux` (10), `napoleon-2023` (10).

## Granularidade — o problema real

| | valor |
|---|---|
| ocorrências totais | 726 |
| **keywords distintas** | **589** |
| reuso médio | 1,23 |
| **aparecem em 1 filme só** | **491 (83%)** |
| aparecem em ≥3 filmes | 25 |

**83% do vocabulário seleciona exatamente um filme.** Como filtro, isso não é
filtro — é nuvem de tags por filme. É o mesmo modo de falha que o
`temas_livres` de hoje (1.899 rótulos distintos para 2.321 ocorrências) e o
motivo pelo qual o desenho exige lista fechada.

Viabilidade de um filtro curado, no catálogo atual:

| corte | etiquetas | filmes cobertos |
|---|---:|---:|
| aparece em ≥2 filmes | 98 | 34 de 35 (97%) |
| aparece em ≥3 filmes | 25 | 31 de 35 (89%) |
| aparece em ≥4 filmes | 8 | 24 de 35 (69%) |

## O TMDB mistura categorias — inclusive as que o desenho atribuiu à review

O briefing antecipou a mistura ("based on novel" com "jazz" e "1970s") e ela
está lá. Mas há uma sobreposição que o desenho **não** previu:

| tipo | ocorrências | exemplos |
|---|---:|---|
| assunto / tema | — | `mafia`, `revenge`, `coming of age`, `mother daughter relationship` |
| contexto | — | `italy`, `tokyo`, `1980s`, `space`, `desert` |
| **produção / metadado** | **41 (6%)** | `based on novel or book`, `sequel`, `woman director`, `female protagonist`, `independent film` |
| **humor / tom** | **31 (4%)**, em **17 de 35 filmes (49%)** | `moody`, `bitter`, `baffled`, `bold`, `disapproving`, `disheartening`, `playful`, `lighthearted`, `introspective`, `so bad it's good` |

`cats-2019` traz `so bad it's good, bitter, baffled, bold, disapproving,
disheartening`. `perfect-days-2023` traz `playful, lighthearted`.

**Isso colide de frente com a divisão de fonte.** O desenho atribui `mood` às
REVIEWS e `tema`/`contexto` ao TMDB. Mas o TMDB emite `mood` também — e emite
**editorialmente**, atribuído por quem cataloga, não derivado de quem assistiu.
Duas fontes para a mesma categoria, com semânticas diferentes, e nenhuma regra
no desenho dizendo quem ganha.

## Verdicto da Entrega 3

**A divisão de fonte sobrevive; a premissa de que `tema`/`contexto` saem das
keywords "sem invenção" NÃO sobrevive.**

- Custo zero: **confirmado**.
- Cobertura: usável na mediana, **com um filme a zero e 20% abaixo de 10** — o
  produto precisa de uma regra para filme sem keyword, e ela não pode ser
  "deriva da review", que é justamente o que a divisão de fonte proíbe.
- Granularidade: **inutilizável em cru**. Entre a lista de 589 termos e uma
  lista fechada navegável existe uma camada de curadoria e mapeamento — que é
  um artefato de desenho que alguém precisa escrever, versionar e manter
  crescendo com o catálogo. Não é derivação; é tradução.
- Sobreposição com `mood`: **precisa de regra explícita** antes de implementar.

**Recomendação:** manter a fonte TMDB para `tema`/`contexto`, e acrescentar ao
desenho (i) a camada de mapeamento `keyword → etiqueta fechada`, com seu
próprio identificador de versão, (ii) a regra para o filme sem keywords, e
(iii) a regra de precedência quando TMDB e review discordam sobre `mood` — com
a recomendação de **ignorar o `mood` do TMDB**, porque ele é catalogação
editorial e o produto inteiro é sobre o que o público disse.

**LIMITE:** 35 filmes. A cauda de 83% de singletons deve encolher com o
catálogo (mais filmes, mais reuso), mas isso é hipótese — a curadoria precisa
ser refeita a cada expansão, e o custo dela cresce, não some.

---
---

# ENTREGA 4 — a contagem de tema por lista de ids

Avaliação sem implementação.

## 1. O prompt de síntese já expõe os ids? **Já expõe um índice, e é melhor que o id**

[`build_user_message`](src/espectro24/synthesize.py:834) monta o bloco de
reviews numerando cada uma:

```
[1] nota=4.0 estrelas:
<texto completo>

[2] nota=3.5 estrelas:
...
```

**O modelo já vê um identificador estável por review, `[1]`…`[n]`, e ele custa
zero tokens adicionais** — já está no prompt. O código mapeia índice →
`viewing_id` deterministicamente, porque `bucket.reviews_analisadas` é lista
ordenada.

**Consequência: o custo de "expor os ids" é ZERO.** Pedir `viewing:1438768547`
em vez de `[7]` seria mais caro (≈8 tokens contra ≈2 por referência) e mais
frágil, sem ganho nenhum. **A proposta deve pedir o ÍNDICE, não o id.**

## 2. Impacto em tokens de saída e em cache

| | valor |
|---|---|
| soma de menções por bucket | média 64,0 · **mediana 62** · p90 95 · max 113 |
| tokens por índice (2 dígitos + vírgula) | ≈2 |
| acréscimo pelos índices | **+124 tokens** (mediana) · +190 (p90) |
| economia do inteiro removido (6 temas) | −24 tokens |
| **delta líquido de SAÍDA por bucket** | **≈ +100 tokens** |
| base medida (§3[D]: 6 temas ≈700 tokens no pior caso) | **≈ +14%** |

Custo do delta, `deepseek-v4-flash` a US$ 0,28/M de saída:
**+US$ 0,003 nos 35 filmes · +US$ 0,025 em 300 filmes.**

**Cache de prefixo: impacto nulo.** O `system` e o `user` não mudam — só o
formato da saída. Saída não é cacheada em nenhum dos providers, então o
aproveitamento de prefixo (77% medido na sessão anterior) fica intacto.

Risco real, e não é o custo: `LLM_MAX_TOKENS = 3000`, com ~700 usados no pior
caso — folga de sobra. Mas o `max_tokens` da retentativa e o comportamento em
buckets com muitas menções (p90 = 95 índices, max 113) devem ser conferidos no
piloto.

## 3. Validações mecânicas que o código passa a poder fazer

As que o briefing lista:

| validação | o que detecta |
|---|---|
| índice fora de `[1, n]` | referência inexistente — hoje invisível |
| índice repetido no mesmo tema | inflação por duplicata |
| `len(lista) > n` | impossível por construção — substitui o clamp por detecção |
| lista vazia | tema sem lastro nenhum — hoje seria `mencoes: 0`, indistinguível de omissão |

E quatro que ela **também** habilita e que valem mais:

5. **Sobreposição real entre temas.** Hoje a razão soma-de-menções / n é 1,67
   em média (medida no estudo), e ninguém sabe se são as mesmas reviews em
   todos os temas ou reviews diferentes. Com listas, vira contagem.
6. **Orfandade EXATA.** Hoje "reviews que não sustentam nenhum bullet" é um
   proxy de eixo (11,6%, com o viés declarado). Com listas é o complemento da
   união — medição, não estimativa.
7. **Verificação cruzada entre estágios independentes.** A review `[7]` é
   listada como sustentando um tema que [D3] rotulou `ritmo`; a classificação
   por eixo diz que `[7]` carrega `ritmo`? Discordância aponta erro de um dos
   dois — e hoje os dois estágios não se tocam.
8. **Reprodução do caso `wonka`.** *"Fotografia e efeitos visuais criticados"*,
   `mencoes` = 6 de 32, com **1** review sustentando na leitura à mão. Com
   lista, as 6 referências ficam nomeadas e a auditoria à mão custa ler 6
   reviews em vez de 32.

## 4. O limite honesto

**O modelo continua escolhendo QUAIS índices.** Isto troca *"inteiro sem
lastro"* por *"lista verificável"* — é **auditabilidade, não verdade**. Um
modelo que hoje devolve `mencoes: 6` para um tema sustentado por 1 review pode
amanhã devolver seis índices plausíveis para o mesmo tema, e as validações
mecânicas da seção 3 **não pegam nenhum deles**: são seis índices existentes,
não repetidos, dentro do bucket.

O que muda é que a afirmação vira **falsificável**: dá para abrir a review `[7]`
e ver se ela diz aquilo. Hoje não dá — não há o que abrir.

**Modo de falha novo, que a proposta cria e que precisa entrar no piloto:**
*padding*. Com um inteiro, inflar custa nada; com uma lista, inflar exige
escolher índices — e o caminho mais barato para o modelo é pegar os primeiros,
ou os mais longos, ou os que já citou. É detectável em agregado (viés de
posição na distribuição dos índices escolhidos, correlação com a ordem do
prompt), não caso a caso, e **não foi medido** porque exigiria rodar síntese.

**Isto NÃO fecha o §0.** "O código é a autoridade sobre números" continua
violado em espírito: o código passa a contar, mas conta uma lista que o modelo
escolheu. É melhor que hoje e não é o conserto completo — e o registro deve
dizer isso, não vender o contrário.

## 5. Existe saída melhor?

**Sim, e custa menos do que parece.**

O problema estrutural das duas versões (inteiro ou lista) é o mesmo: **uma
chamada olha 40 reviews e decide sobre 6 temas de uma vez.** É a mesma diluição
de atenção que a Entrega 3 da sessão anterior mediu nos feelings, onde a
dimensão colocada por último no prompt rendeu metade das etiquetas.

**Alternativa D — inverter a direção.** Em vez de perguntar à síntese *"quais
reviews sustentam este tema?"* (1 chamada, 40 reviews no contexto), perguntar
a um passe seguinte, review a review: *"esta review sustenta algum destes 6
temas?"* — 40 chamadas por bucket, cada uma com **uma** review e **seis** frases
curtas.

| | lista de índices | passe por review |
|---|---|---|
| quem conta | código | código |
| chamadas / filme | 3 (nenhuma nova) | 120 |
| contexto por decisão | 40 reviews | 1 review |
| decisões independentes | não | **sim** |
| aceita votação de 3 | não (é a mesma chamada da síntese) | **sim** |
| orfandade | exata | exata |
| **custo 300 filmes** | **+US$ 0,03** | **US$ 1,25** (1 voto) · **US$ 3,74** (3 votos) |
| custo 35 filmes | +US$ 0,003 | US$ 0,15 · US$ 0,44 |

*(Referência para calibrar: a classificação por eixo com 3 votos sobre 36.000
reviews custa US$ 9,86, medido na sessão anterior. O passe por review é
**menos de metade disso**.)*

O passe por review é a mesma arquitetura que **já funcionou** neste projeto: o
verificador `V2_alvo` levou a precisão de `impacto_emocional` de 0,486 para
0,794 justamente por isolar uma decisão pequena numa chamada própria (§2.5, e a
Entrega 5 abaixo).

**Recomendação:** adotar a lista de índices **como piso** — custa US$ 0,03,
não muda nenhuma chamada, e já habilita as oito validações. E tratar o passe
por review como o desenho-alvo, porque é o único que torna o número um **soma
de decisões independentes e votáveis** em vez da estimativa de um modelo. O
argumento de custo que favoreceria a versão barata **não existe**: US$ 3,74
para o catálogo inteiro.

Ele também é a resposta da Entrega 1: com a unidade reduzida de "40 reviews de
uma vez" para "uma review contra 6 frases", a granularidade que o split tentou
comprar dividindo eixos aparece de graça — e sem inventar eixo nenhum.

---
---

# ENTREGA 5 — correção de registro na SPEC

**Aplicada** em `SPEC.md` §2.5, no parágrafo que começava *"Existe uma correção
que **funcionou** e que NÃO foi aplicada"*.

O texto antigo descrevia o passe `V2_alvo` como medido mas não adotado, e como
"decisão pendente do dono do projeto". **Ele foi adotado na v1.9.16** (item 1
do changelog daquela versão), e o consenso de produção é o verificado desde
então. O parágrafo ficou desatualizado por 15 versões.

O que o texto novo registra, preservando o histórico:

- a adoção, com o caminho (`scripts/verificador_impacto.py aplicar-producao`),
  o artefato (`consenso_verificado.jsonl` + manifesto), a preferência com
  guarda de atualidade em `pipeline._carregar_consenso_producao`, e a
  declaração em `eixos.verificador`;
- **o estado atual medido**: `impacto_emocional` em **36,1%** no corpus e
  **34,6%** na seleção de produção, contra 75,6% no consenso cru; eixos por
  review 3,42 → 3,01; reviews sem eixo 0,2% → 2,0%. A projeção de 35,7%
  registrada na v1.9.14 **acertou dentro de 1pp**;
- o que **não** mudou: a precisão de 0,486 é a do prompt sem o passe e é o que
  justifica o passe existir; as três tentativas de conserto pelo prompt seguem
  refutadas; o ganho de margem continua pequeno (15/35 contra 13/35) — **a
  de-saturação corrigiu a precisão do eixo, não o problema do lift**;
- uma limitação que o texto antigo não tinha: a precisão de 0,79 depende de um
  **script separado** ter sido rodado, não de uma etapa do pipeline, e o
  `taxonomia_id` cobre o prompt de classificação mas **não** o passe de
  verificação. Um corpus classificado sob `ebab2667de74` sem o passe e outro
  com o passe têm o mesmo `taxonomia_id` e frequências que diferem em 46pp —
  medido nesta sessão, no braço de controle (80,9% contra 34,6%).

Correção de registro apenas: nenhum comportamento mudou, nenhum arquivo de
`resultado/` foi tocado, `taxonomia.py` intacto.

---

# Resumo

**O split reprova nas três condições** — `enredo_desfecho` a 51,3% contra os
60,8% que `roteiro_estrutura` tem no mesmo braço de controle (moveu 9,5pp, não
de-saturou), amplitude máxima de 8,1pp contra o piso de 10pp, e 50,3% das
reviews recebendo dois ou mais sub-eixos, pior que o trio mais emaranhado que
já existe. **Mas a reprovação é informativa:** o split passa em C3 nas reviews
curtas (28,9% em ≤200 chars) e colapsa nas longas (82,4% em >1200), e as
reviews que recebem os três de fato falam dos três. **O problema é a unidade de
classificação, não a taxonomia** — enquanto a unidade for a review inteira,
dividir eixos redistribui rótulos sem ganhar resolução.

**O estreitamento de `comparacoes` não faz nada** (−2,3pp, dentro do ruído de
±5pp, com 26 saindo e 20 entrando), e exclui casos que a própria definição diz
incluir. A hipótese alternativa do briefing é a bem sustentada: reviews que
comparam carregam 3,90 eixos contra 2,50, e em 95,9% das vezes a comparação
acompanha outro eixo — a síntese está certa em raramente promovê-la a tema.
**Retirar a proposta.**

**As `keywords` do TMDB vêm de graça e são ricas na mediana (21), mas 83% do
vocabulário aparece em um filme só**, um filme vem com zero e 20% vêm com ≤10 —
e o TMDB emite `mood` editorial (`bitter`, `playful`, `so bad it's good`) que
colide com a categoria que o desenho atribuiu à review. A fonte serve; a
premissa de derivar "sem invenção" não.

**A contagem por lista de ids é barata e boa, e há uma melhor.** O prompt já
numera as reviews `[1]…[n]`, então expor referências custa zero; o delta é
+14% de saída e US$ 0,03 em 300 filmes, com oito validações mecânicas
habilitadas — mas continua sendo auditabilidade, não verdade, porque o modelo
ainda escolhe os índices. O passe por review (40 chamadas por bucket, uma
review contra seis temas) transforma o número numa soma de decisões
independentes e votáveis por **US$ 3,74 no catálogo de 300 filmes** — e é o
mesmo movimento que já funcionou no verificador de `impacto_emocional`.

**A correção de registro está aplicada:** o passe `V2_alvo` foi adotado na
v1.9.16 e `impacto_emocional` está em 34,6%, não nos 75,5% que a spec ainda
descrevia.
