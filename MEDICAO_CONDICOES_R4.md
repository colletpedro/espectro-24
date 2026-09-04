# CONDIÇÕES DE DECISÃO — rodada 4: o refinamento, medido

**Nada publicado.** `git status resultado/` **sem diff**, frontend intocado,
nenhum filme regerado, taxonomia / `taxonomia_id` / lei de margem / cota /
piso intocados, **seleção de temas intocada**. **Suíte: 1.626 → 1.634**
(8 testes novos, nenhum quebrado). SPEC.md **+125 linhas, 0 alteradas**.

Anteriores: [DESENHO_CONDICOES_DE_DECISAO.md](DESENHO_CONDICOES_DE_DECISAO.md),
[rodada 1](MEDICAO_CONDICOES_DE_DECISAO.md), [rodada 2](MEDICAO_CONDICOES_R2.md),
[rodada 3](MEDICAO_CONDICOES_R3.md).

**Convenção:** **MEDIDO** = número de código rodado nesta sessão ou de
documento anterior citado com a fonte. **VISTO** = leitura, julgamento.

---
---

# O MAPA — reportado antes do código

## Onde cada regra entrou

| regra | onde | por quê ali |
|---|---|---|
| **anti-spoiler** | prompt (regra 9 reescrita + 9b exemplos + 9c precedência) · marca no briefing · SPEC §0 | a regra antiga dizia *"use os temas como estão, não os expanda"* — e **essa frase autorizava o defeito**: quem introduziu o spoiler não foi a expansão, foi a mudança de ato de fala |
| **qualidade concreta × perfil** | prompt (preâmbulo reescrito) · flag `perfil_de_leitor` | o preâmbulo dizia *"Ela descreve o LEITOR, não o filme"* — **era essa linha que empurrava para o perfil** e produzia o molde *"prioriza X em vez de Y"* |
| **controle de especificidade** | prompt (regra 13, nova) | não existia nada: a regra de fidelidade proíbe introduzir o que não está, e **nada proibia superespecificar o que ESTÁ** — o buraco por onde `interstellar` passou |
| **critério de abstenção** | prompt (regra 6 estendida + 9c) · `prompt_retry` | a precedência precisava estar nos dois lugares, senão a correção de um spoiler vira invenção no retry |

## O que NÃO foi tocado, deliberadamente

`selecionar()` (estável desde a rodada 2, foi o que a corrigiu),
`peso_do_lado()`, `ordem_das_colunas()`, `_validar_ancora`,
`_validar_discriminacao`, `palavras_copiaveis`, `MAX_SEQ_EXEMPLO`, e a
orquestração. **Nenhum validador lexical de valência foi recriado.**

## A decisão de desenho que exigiu medição prévia

O briefing pedia: *se propuser detecção mecânica de spoiler, meça a precisão
antes de adotá-la.* **MEDIDO, sobre as 266 condições da rodada 3:**

| | |
|---|---:|
| o marcador lexical dispara em | 19 de 266 (7,1%) |
| acerta, dos 5 anti-spoiler reais | 3 de 5 |
| **precisão** | **15,8%** |

**DECISÃO: não vira validador.** É pior que os 7,7% do léxico de valência que
a rodada 3 removeu, e o modo de falha é o mesmo e caro — falso positivo aqui
**descarta condição boa**, o custo que o §3[V] mediu três vezes.

**Mas ele entra como MARCA DE BRIEFING, por ASSIMETRIA DE CUSTO.** Como
validador, um falso positivo joga fora uma condição boa; como marca, apenas
faz o modelo escrever com mais cuidado sobre aquele tema. **Um sinal de baixa
precisão é utilizável no lado barato e não no lado caro.** Dispara em 30
temas dos 35 filmes.

E parte dos "falsos positivos" era **subcontagem da minha leitura da rodada
3**, não erro do marcador — *"desfecho explosivo"*, *"pontas soltas no
final"*, *"reviravoltas surpreendentes"* são casos que a regra nova deve
pegar e que eu não tinha marcado. O que a classificação cega abaixo confirmou.

---
---

# O QUE A SUÍTE PEGOU DE MIM, e vale registrar

`test_briefing_nao_tem_algarismo_em_nenhum_dos_35` **reprovou na primeira
escrita da marca de spoiler**: eu tinha escrito *"a regra 9 vale aqui com
força"* na linha de ATENÇÃO, e **"9" é um algarismo no briefing** — a garantia
"zero dígito por construção" do §3[V], quebrada pela minha própria correção.

Corrigido para *"a regra ANTI-SPOILER"*, e a guarda foi **estendida ao
`prompt_retry`**, que também é concatenado à mensagem do usuário e onde eu
tinha escrito *"a regra 9c"*. Teste novo:
`test_briefing_do_retry_tambem_nao_tem_algarismo`.

---
---

# ENTREGA 2 — os 35, duas execuções

| | rodada 3 | **rodada 4** |
|---|---:|---:|
| temas pedidos pelo código | 278 | 278 |
| condições publicadas (exec 1) | 266 | **257** |
| **abstenções** | 12 (4,3%) | **21 (7,6%)** |
| descartadas por flag | 6 | **3** |
| `exemplo_verbatim` | 5 | **0** |
| `sem_discriminacao` | 1 | 3 |
| filmes com retry | 10 | 15 |
| filmes em fallback total | 0 | **0** |
| chamadas (exec 1) | 115 | 120 |
| **custo, duas execuções** | US$ 0,547 | **US$ 0,694** |

**Reprodutibilidade:** J(texto) **0,356** (era 0,379) · J(id) **0,967** (era
0,965) · 26 de 35 filmes com seleção idêntica. O J(id) continua não sendo
critério — é tautológico sob seleção em código, e o que ele varia é a
**abstenção**, não a seleção.

## A abstenção subiu — e a razão é nomeada, como o briefing exigiu

**MEDIDO: 16 saltos novos, 7 saltos que deixaram de acontecer.** Dos 16 novos:

| categoria | n | leitura |
|---|---:|---|
| tema marcado com **risco de spoiler** no briefing | **4** | a precedência funcionando: `spider-man` POS-E *Cliffhanger e expectativa pela continuação* era, na rodada 3, *"tolera pontas soltas no final"* — um spoiler. Agora é saltado |
| tema de **expectativa / superestimado** | **6** | `hereditary` NEG-B, `interstellar` NEG-B, `parasite` NEG-C, `the-godfather` NEG-B, `longlegs` NEG-B, `friday` POS-B. **VISTO:** são temas sobre a REPUTAÇÃO do filme, não sobre o filme — e o enquadramento novo ("nomeie a qualidade concreta") os torna difíceis de converter sem descrever o estado prévio do leitor. É consequência coerente do refinamento, não acidente |
| valência conflitante com o lado | 3 | `pearl` NEG-E *Atuação boa apesar dos problemas*, `obsession` NEG-C — abstenção correta, mesma da rodada 3 |
| outros | 3 | |

**Nenhum filme ficou com um lado vazio.** O menor lado do catálogo é **2**
condições (`hereditary`, `interstellar`, `longlegs`, `obsession-2026`,
`the-godfather`); 5 filmes têm algum lado com ≤ 2.

**VISTO, e é a ressalva honesta:** a categoria "expectativa/superestimado"
sumindo é defensável pelo enquadramento, mas ela **remove informação de
decisão real** — "muita gente achou superestimado" é útil para quem decide.
Se o dono quiser essa categoria de volta, o caminho não é afrouxar o
enquadramento, é decidir se "reputação do filme" é uma qualidade que a
condição pode nomear. **Fica como pergunta, não como conserto.**

---
---

# ENTREGA 3 — a validação cega

## O procedimento, e a sua limitação declarada

A classificação de anti-spoiler foi feita sobre as **257 condições em ordem
alfabética, sem marca de origem**, com o critério escrito antes:

> *A condição informa ao leitor COMO O FILME TERMINA, ou QUE existe uma
> reviravolta/revelação, usando isso como MOTIVO para recomendar ou
> desaconselhar?*

Gravada em `classificacao_cega_r4.json` **antes** do cruzamento, e o
cruzamento com os 7 da rodada 3 foi feito **por script**.

**A limitação, dita sem maquiagem:** eu já tinha lido os 7 e não posso
desconhecê-los. O que o procedimento garante é que o critério foi aplicado
**uniformemente às 257**, não só onde eu suspeitava — e a prova de que isso
funcionou é que ele pegou **4 casos que a rodada 3 não tinha**.

## Os três números que o briefing pediu

| | n | quais |
|---|---:|---|
| **dos 7 antigos, resolvidos** | **6** | `pearl-2022`, `avengers-endgame`, `dune-part-two`, `interstellar`, `friday-the-13th-2009`, `obsession-2026` (tema saltado) |
| **dos 7 antigos, persistem** | **1** | `shutter-island` POS-B |
| **casos NOVOS que a regra pegou** | **4** | `cure` NEG-B, `spider-man` NEG-A, `anatomy-of-a-fall` NEG-B, `longlegs` NEG-A |
| **falsos positivos criados** | **0** | nenhuma condição boa foi descartada pela regra nova; as 3 descartadas por flag foram `sem_discriminacao`, não spoiler |

**Dos 5 que eram especificamente anti-spoiler: 4 resolvidos, 1 persiste.**

### O que persiste, e por quê

`shutter-island` POS-B saiu de *"gosta de **reviravoltas** marcantes que
transformam a história"* para *"aprecia uma **mudança memorável de
perspectiva** na trama"*. **A abstração não resolve** — ela continua
anunciando que existe uma. **Pela regra de precedência que esta rodada
escreveu, a resposta certa era ABSTER-SE**, e o modelo abstraiu em vez de
abster. É a regra 9c não sendo seguida no caso mais difícil do catálogo.

### Os 4 casos novos são UMA categoria, e ela é tensão de produto

Todos os quatro são condições do lado *talvez evite* que revelam **como o
filme termina** ao descrever a queixa do grupo sobre o final:

> *se frustra com narrativas ambíguas que não oferecem uma resolução
> definitiva* — `anatomy-of-a-fall`

**São simultaneamente spoiler e informação legítima de decisão.** Muita gente
evita filme de final ambíguo, e dizer isso é o serviço que a feature promete;
mas dizer isso é dizer que o final é ambíguo.

**Não resolvi sozinho, e as três saídas estão na folha para o dono decidir:**
(a) aceitar, tratando "o tipo de final" como informação de gênero; (b)
proibir, e perder a informação; (c) abstrair para *"prefere histórias que
fecham todas as pontas"*, que preserva parte da utilidade sem descrever este
filme.

---

## Teste de não-regressão nominal — PASSA

| filme | rodada 4 | virou *"X em vez de Y"*? |
|---|---|---|
| `cidade-de-deus` | *aprecia uma fotografia dinâmica e direção marcante com visual imersivo e estilizado* | **não** |
| `im-still-here-2024` | *busca atuações marcantes que transmitem sentimentos profundos através de expressões e silêncios* | **não** |
| `perfect-days-2023` | *aceita um ritmo vagaroso em troca de uma imersão meditativa no personagem* | **não** |

Nenhuma descreve o leitor, nenhuma inventa oposição, todas continuam nomeando
a qualidade concreta. **Travado por dois testes**, incluindo um que compara a
frase concreta com o molde abstrato e exige que o molde **reprove**:

```
concreta:  aprecia uma direção marcante com fotografia dinâmica…   -> limpa
abstrata:  prioriza impacto visual em vez de uma abordagem discreta -> ancora_nao_verificavel
```

A versão abstrata **não consegue ancorar** — ela não nomeia mais o assunto do
tema. O validador de âncora, que já existia, é o que barra a regressão.

---

## Fabricação e generalização excessiva

**MEDIDO — triagem mecânica de conteúdo acrescentado** (palavras de conteúdo
da condição cujo prefixo não aparece em tema+paráfrase): 63 de 257 têm 4 ou
mais. **Li as 14 maiores e nenhuma é fabricação** — são sinônimos e verbos, que
é exatamente o que a regra "palavras suas" exige (*"ficção especulativa"* ←
"ficção científica"; *"agressividade ininterrupta e montagem acelerada"* ←
"violência constante e edição frenética").

| | rodada 3 | rodada 4 |
|---|---:|---:|
| fabricação | 0 / 266 | **0 / 257** |
| generalização excessiva (minha leitura) | 1 (`interstellar`) | **0** |
| anti-spoiler | 5 (1,9%) | **5 (1,9%)** — 1 antigo + 4 categoria nova |

`interstellar` saiu: *"recriações de buracos negros"* virou *"representações
impressionantes de paisagens espaciais"*. **A regra de especificidade
resolveu o único caso do §10 que a seleção top-3 alcançava.**

---
---

# O que fica pendente

1. **A sua leitura das 257** — `FOLHA_LEITURA_CONDICOES_35.md` está regerada
   com o texto novo, na mesma ordem de prioridade (13 min cobrem os três
   casos de aceite; 70 min cobrem tudo onde as duas razões vivem).
2. **A decisão sobre a categoria "final ambíguo"** — as três saídas acima.
3. **`shutter-island` POS-B** — se a precedência deve virar código (o único
   caminho seria uma regra de seleção que exclua temas de plot twist, e isso
   toca a seleção, que esta rodada não move).
4. **A categoria "expectativa/superestimado"**, que a abstenção passou a
   engolir em 6 filmes.
5. **`peso_meio`** para os 9 filmes da rodada 3 em que as duas colunas somam
   menos de 80% — não implementado nesta rodada, que não moveu peso.

## Limite

**35 filmes, 2 execuções, 257 condições, e a classificação é uma leitura
minha** — que é a que a leitura do dono existe para julgar. Com 0 fabricações
em 257, o limite superior de 95% é **~1,2%**. A validação cega mitiga, mas não
elimina, o fato de eu já conhecer os 7 casos anteriores.

**Aprovação de código não é aprovação editorial.** O portão seguinte é a
leitura humana, e a pergunta dela é a que nenhum número acima responde:
*vendo estas condições como página, a impressão é fiel à recepção e útil para
decidir?*

## Reprodução

```bash
python scripts/gerar_condicoes.py --todos --saida <dir-fora-de-resultado>
```

Estágio em `src/espectro24/condicoes.py`, 42 testes em
`tests/test_condicoes.py`. As duas execuções, o mapa, a classificação cega e
a triagem vivem no scratchpad da sessão.
