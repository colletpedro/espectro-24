# Diagnóstico estrutural da SPEC.md — LEI / HISTÓRICO / PROTOCOLO

**Data:** 2026-09-04
**Escopo:** investigação, não reestruturação. Nenhuma linha da SPEC.md foi
editada, movida ou apagada; nada em `resultado/` foi tocado; nenhum arquivo
novo dos propostos na Entrega 4 foi criado.
**Base:** SPEC.md, 8.625 linhas / 832 KB, lida integralmente. Limites do que
esta leitura pode afirmar estão declarados na **Entrega 5** — leia-a antes de
agir sobre a Entrega 1.

**Numeração usada:** os `§` reais do documento quando existem; quando a
subseção não tem número (a maioria), o **título literal do cabeçalho** mais o
intervalo de linhas.

---

## Sumário do que a investigação encontrou

1. A hipótese se confirma, e o tamanho dela é maior do que "mistura de três
   tipos": **cerca de 66% do documento é HISTÓRICO DE DECISÃO**, ~30% é LEI e
   ~4% é PROTOCOLO — e nenhum dos três está marcado como tal em lugar nenhum.
2. O padrão dominante não é seção-mista-por-descuido. É **um padrão de
   escrita recorrente**: cada estágio grande (`[D]`, `[D2]`, `[V]`, `[E]`) abre
   com centenas de linhas de arqueologia em bloco de citação e só depois
   enuncia a regra vigente. Em `[D]`, são **676 linhas de histórico antes de 33
   linhas de lei**. O ponto de virada é sempre localizável e sempre o mesmo
   tipo de linha.
3. Há **quatro seções redigidas em presente vigente que descrevem coisas que
   não estão mais em vigor** — o estágio `[E2] Editor`, o prompt do narrador
   antigo, o diagrama do pipeline em §3, e a `MARGEM_LIFT_PP` do §3[V]. Um RAG
   que recuperar qualquer uma delas devolve uma regra revogada com cara de
   regra atual.
4. Há **um estágio em produção sem seção própria**: as CONDIÇÕES DE DECISÃO
   (v1.9.35–37, 257 condições no ar) vivem inteiramente dentro do §0, como um
   bloco de citação chamado "TERCEIRA EXCEÇÃO DELIBERADA".
5. **Duas remissões apontam para alvos que não existem** no documento
   ("invariante 7b de §D2", "§ correção de recall em review curta").

---

# Entrega 1 — Classificação seção por seção

Legenda: **LEI** = invariante vigente · **HIST** = histórico de decisão ·
**PROT** = protocolo de processo · **MISTO** = mais de um tipo sem separação.
Para todo MISTO, a coluna final dá **a linha exata onde o tipo muda**.

## Cabeçalho (1–11) — 11 linhas

| Tipo | Onde muda |
|---|---|
| **MISTO** | Linha 4, no ponto `"**Status:** v1 fechada (aceite em ...)."` — daí em diante, até o fim da linha 4, são ~9.000 palavras de resumo cumulativo de 40 versões, num único parágrafo físico. As linhas 6, 8 (v1.9.21, v1.9.22) são HIST puro. |

Observação estrutural: **o título diz `v1.9.25` e a data diz `2026-08-26`**,
enquanto o conteúdo vai até v1.9.37 / 2026-09-04. Ver Entrega 3, item C1.

## §0 Princípio norteador (12–577) — 566 linhas

A seção mais misturada do documento. Sete blocos distintos, todos empilhados
sob um cabeçalho que promete um princípio.

| Bloco | Linhas | Tipo | Onde muda / observação |
|---|---|---|---|
| Núcleo do princípio + cota 40/40/40 | 12–18 | **LEI** | — |
| "v1.9.0 — a cota igual passou a ser literal" | 19–27 | **HIST** | inserto histórico dentro da lei |
| "O problema que motivou a versão" | 29–43 | **HIST** | — |
| Duas invariantes que a inversão não toca | 44–56 | **LEI** | — |
| Exceção `medianas` na interface | 57–84 | **LEI** | regra + exceção automática do dominante |
| HATERS/MIXED/FANS | 85–184 | **MISTO** | **Muda na linha 92**: de 85–91 (LEI: qual palavra em qual lugar) para 92–104 (HIST: o trade-off por extenso). Volta a LEI em 106–146 (escopo e o que não muda), volta a HIST em 148–184 (reversão barata, "ANOTADO NÃO IMPLEMENTADO", o caso de fronteira do glossário). |
| Ordem dos blocos por peso (v1.9.30) | 186–243 | **MISTO** | **Muda na linha 198** (`"A regra: os blocos em destaque são ordenados por share_real"` = LEI) e de novo na **202** (`"POR QUE ELA É COMPATÍVEL…"` = HIST). LEI de novo em 231–239 (empate, barra não reordenada). |
| Margem por `n` e o §0 (v1.9.34) | 245–297 | **MISTO** | **Muda na linha 258**: 249–257 é LEI de escopo ("a lei por n não toca o que este § governa"); 258–297 é HIST (a medição do percentil, o precedente da v1.9.30, o que se perde). |
| CONDIÇÕES DE DECISÃO (v1.9.35) | 299–423 | **MISTO** | **Muda na linha 330**: 299–328 é HIST (o que muda, a razão); 330–358 é **LEI** (três garantias + lista fechada do que não muda); 360–422 volta a HIST, com uma **LEI enterrada em 399–413** (a regra anti-spoiler das condições e a precedência sobre o controle de especificidade). |
| "[v1.9.37] ACHADO DE MÉTODO" | 424–447 | **MISTO** | **Muda na linha 444**: 424–443 é HIST; 444–447 (`"A regra prática que fica"`) é **PROT**. |
| Pendência editorial `expectativa` | 451–523 | **HIST** + estado aberto | a tabela de 6 ocorrências é dado operacional, não lei |
| "[v1.9.37] NO AR — e o que fica ABERTO" | 527–569 | **HIST** + estado aberto | é o único lugar do documento que consolida pendências |
| Objetivo / Público-alvo | 571–576 | **LEI** | as duas frases mais fundamentais do produto estão no fim de uma seção de 566 linhas |

> **O achado estrutural desta seção:** o §0 é hoje o depósito de toda decisão
> que "toca um princípio". O estágio de CONDIÇÕES — que está no ar, tem
> `src/espectro24/condicoes.py`, harness próprio e teste — **não tem seção em
> §3**. Sua especificação inteira é o bloco 299–423.

## §1 Escopo v1 (578–585) — 8 linhas
**LEI.**

## §2 Parâmetros congelados (586–624) — 39 linhas
**MISTO.** A tabela é LEI. As linhas **601, 609, 610, 611** são entradas
riscadas (`~~…~~ REVOGADO/REMOVIDA`) — HIST embutido na tabela de lei. O
preâmbulo 588–596 (o que "congelado" passou a significar) é LEI de leitura.

## §2.1 Parâmetros técnicos (625–646) — 22 linhas
**LEI.** Exceção: linha 642 nomeia `editor §E2` como consumidor da config de
prosa (estágio aposentado — Entrega 3, item C5).

## §2.2 Fronteiras de bucket (647–744) — 98 linhas

| Bloco | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Regra estrutural + tabela de fronteiras + "por quê" | 647–679 | **LEI** | — |
| "Consequência medida — os shares publicados MUDAM" | 680–703 | **HIST** | — |
| "RISCO ACEITO da opção C" | 704–744 | **MISTO** | **Muda na linha 732**: Riscos 1 e 2 (706–729) são HIST/declaração; a mitigação do Risco 3 a partir de `"Mitigação, e é a principal"` (732–741) é **LEI** — é onde vive o piso de 1 página por nível, o seguro de reversibilidade. |

## §2.3 Ordenação da listagem (745–877) — 133 linhas

| Bloco | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Parâmetro + menu real + default `by/added` | 745–777 | **LEI** | — |
| "Correção de registro" + "Ressalva honesta" | 778–788 | **HIST** | **muda na linha 778** |
| "O tamanho MEDIDO do viés de recência" | 789–822 | **HIST** | contém um "Candidato de próxima versão" já revogado 12 linhas adiante (Entrega 2, item 2.1) |
| "A passada SELETIVA sob `by/added-earliest`" | 823–877 | **MISTO** | **Muda na linha 841**: 825–840 é HIST (por que é o único lever); 841–843 + 854–868 é **LEI** (a condição da passada, o orçamento, o "soma não substitui"); 845–852 e 869–874 voltam a HIST. |

## §2.4 Retentativa de rede (878–923) — 46 linhas
**MISTO.** **Muda na linha 887**: 880–885 é HIST (a medição de 10 falhas em 28
filmes); de 887 até o fim é **LEI** (o que retenta, a tabela do que não
retenta, o contador de lote, a telemetria obrigatória). Das quatro seções §2.x
grandes, é a mais limpa.

## §2.5 Eixos, lift e margem (924–1489) — 566 linhas

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Abertura + taxonomia de 10 eixos + `taxonomia_id` corrente | 924–943 | **LEI** | — |
| "`taxonomia_id` no veredito não é burocracia" | 944–957 | **MISTO** | **Muda na linha 948**: 946–947 é LEI (todo veredito carrega o id); 948–952 é HIST (o caso `barbie`); 954–956 volta a LEI (o que o estado significa). |
| "Lift — a definição, e por que ABSOLUTO" | 958–976 | **MISTO** | **Muda na linha 967**: 960–965 é LEI (a fórmula); 967–975 é HIST (lift normalizado testado e refutado). |
| **"A MARGEM — a lei por `n`"** | 977–1048 | **MISTO** | **É o núcleo de LEI do documento** (979–1024: a fórmula, a forma exata, a guarda de sinal, o piso de `n<10`). **Muda na linha 1026**: o bloco `"O DEFEITO QUE O PISO ENCONTROU"` (1026–1047) é HIST. |
| "A linha que explica a AUSÊNCIA de veredito" | 1049–1078 | **LEI** | a frase determinística + as três invariantes que a protegem |
| "O limiar por `n`, e a taxa que ele realiza" | 1079–1100 | **HIST** | tabela de medição |
| "O que mediu isso: o NULO DO MÁXIMO" | 1101–1138 | **HIST** | — |
| "⚠️ LIMITAÇÃO IN-SAMPLE" | 1139–1161 | **MISTO** | **Muda na linha 1154**: 1141–1153 é HIST; o terceiro bullet (1154–1158, *"A expansão é o PRIMEIRO teste out-of-sample… rode o nulo do máximo sobre os filmes NOVOS"*) é **PROT** — é uma instrução operacional para uma sessão futura. |
| "O critério 'cerca de um terço' está APOSENTADO" | 1162–1191 | **MISTO** | **Muda na linha 1186**: 1164–1184 é HIST (por que sai); 1186–1190 (`"O critério que entra no lugar é de ERRO"`) é **LEI**. |
| "α = 0,05 e não 0,10" | 1192–1211 | **HIST** | — |
| "O que MUDA e o que NÃO MUDA de forma" | 1212–1223 | **HIST** | — |
| **"A margem de 20pp — REGISTRO HISTÓRICO"** | 1224–1294 | **HIST** | auto-declarado, e é o modelo do que a reestruturação deveria fazer em toda parte |
| "A comparação é `>=`, EXATA" | 1295–1327 | **MISTO** | **Muda na linha 1322**: 1297–1320 é HIST (o bug de float, os 5 filmes, a decisão da v1.9.15 sobre 20pp — revogada); 1322–1326 (`"O cálculo NÃO usa ponto flutuante"`) é **LEI** e sobrevive à lei por `n`. O cabeçalho não avisa que o parâmetro que a seção decide não está mais em vigor. |
| "Seleção de bullets — 2 de FREQUÊNCIA + 3 de LIFT" | 1328–1352 | **LEI** | — |
| "Estado `contraste`" | 1353–1428 | **MISTO** | **Muda três vezes.** 1355–1373 é **LEI** (tabela dos três casos, "ausência = não medido"). **1375–1391**: a correção de registro do 6/29/1 é HIST, e a "Regra prática" das linhas 1389–1391 (*"partição de população vai em TABELA com linha de total"*) é **PROT**. **1393–1428** é HIST auto-declarado (contagens 13/22 e 18/17). |
| "`impacto_emocional` entra no schema" | 1429–1489 | **MISTO** | **Muda na linha 1444**: 1431–1442 é HIST; 1444–1447 é **LEI** (o eixo entra com a limitação declarada); 1449–1489 volta a HIST — e contém o caso da Entrega 2, item 2.2. |

## §2.6 Feelings — EM ESPERA (1490–1536) — 47 linhas
**HIST** + **estado aberto**. Nada implementado, nada autorizado. A tabela
review-derived × work-derived (1502–1506) é a única LEI potencial, e é lei de
uma coisa que não existe.

## §2.7 AVISO — o gabarito dos 5 casos SUBESTIMA (1537–1751) — 215 linhas

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| O AVISO + a causa + as tabelas | 1537–1613 | **MISTO** | **Muda na linha 1614**: 1539–1613 é HIST (a medição do erro do gabarito); 1614–1619 (`"Protocolo exigido para qualquer refação (P1–P7)"`) é **PROT**, e é a única linha da seção que uma sessão futura precisa obedecer. |
| "P4 REVISADO" | 1621–1643 | **MISTO** | **Muda na linha 1638**: 1623–1636 é HIST (o caso `wonka`); 1638–1642 (`"P4 passa a ser…"`) é **PROT**. |
| "Confiabilidade medida da leitura por modelo" | 1644–1689 | **HIST** | — |
| "Achado novo — o modelo nunca usa 'não sei julgar'" | 1690–1730 | **MISTO** | **Muda na linha 1711**: 1692–1709 é HIST; 1711–1716 (`"Recomendação para os próximos gabaritos"`) e 1718–1729 (`"Consequência de desenho"`: o desenho de duas etapas, o veredito humano prevalecendo) são **PROT**. |
| "Gabaritos fechados nesta calibração" | 1731–1751 | **HIST** | — |

## §2.8 Cobertura estendida a 100% (1752–1861) — 110 linhas
**HIST** em toda a extensão, incluindo "O que fecha" / "O que NÃO fecha", que
são estado de projeto, não regra. Único inserto de outro tipo: a linha 1785–1787
(`"[v1.9.34] Deixou de ser…"`) é uma emenda de LEI dentro de um bullet de estado.

## §2.9 Defasagem entre artefatos e consenso (1862–1976) — 115 linhas

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| A defasagem, a tabela dos 10 flips, "NÃO republicar por ora" | 1862–1909 | **HIST** | — (e é o caso da Entrega 2, item 2.3) |
| **"REGRA: o gatilho de regeneração do veredito é o BRIEFING"** | 1910–1932 | **MISTO** | **Muda na linha 1926**: 1912–1924 é HIST (os dois casos que provaram); 1926–1931 (`"A regra:"`) é **LEI** — e é uma lei operacional forte, travada por teste, enterrada dentro de uma seção cujo título é "Defasagem". |
| "FECHADA na v1.9.34" + decomposição do custo | 1933–1976 | **HIST** | — |

## §2.10 Regras de TESTE e de AMBIENTE (1977–2072) — 96 linhas
**PROT** quase integral, e é a seção mais bem-comportada do documento: título
anuncia o tipo, conteúdo entrega o tipo.

- "Traps de escopo — as três regras" (1984–2009): **PROT**.
- "Ambiente — função de biblioteca não altera o ambiente" (2010–2028): **LEI**
  de projeto (2012–2013) + HIST (2015–2027).
- "[v1.9.37] Frontend — constante de módulo no TOPO" (2029–2072): **LEI**
  (2031–2033) + HIST (2035–2054) + **PROT** (2056–2064, o escopo da trava e a
  guarda de trap vazio) + estado aberto (2066–2069, `BANDAS_QUANTIFICADOR`
  morta).

## §3 Pipeline — preâmbulo (2073–2121) — 49 linhas
**LEI**, e **desatualizada**: o diagrama (2075–2092) lista `[E2] editor` com a
flag `--no-edicao` (estágio aposentado na v1.9.10, flag removida), **não lista
`[D3]`, não lista `[V]`, não lista o estágio de CONDIÇÕES**. Ver Entrega 3,
item C4.

## §3[A] Resolução de slug (2122–2124) — 3 linhas
**LEI.**

## §3[C1] Alocação proporcional (2125–2180) — 56 linhas
**MISTO.** **Muda na linha 2151**: 2127–2149 é LEI (fórmula, reconciliação,
caso degenerado, custo); 2151–2155 (`"Por que substituiu a cota igual"`) é
HIST; 2157–2179 ("Duas ressalvas, declaradas") volta a ser **LEI** — as duas
ressalvas são declarações obrigatórias com mitigação obrigatória, não
comentário.

## §3[B] Raspagem do superset (2181–3010) — 830 linhas

O maior bloco do documento depois de `[E]`, e o mais desequilibrado: ~230
linhas de lei e ~600 de arqueologia de coleta.

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Condição de parada | 2181–2233 | **MISTO** | **Muda na linha 2198**: 2183–2196 é LEI; o bloco de citação 2198–2232 (a remoção da parada por ALVO) é HIST. |
| "Orçamento de páginas POR BUCKET" | 2234–2285 | **MISTO** | **Muda na linha 2246**: 2236–2244 é HIST (o defeito medido); 2246–2276 é **LEI** (fórmula, dois ajustes, garantia); 2278–2284 (`"Por que 16"`) volta a HIST. |
| "Posicionamento estratificado" | 2286–2373 | **MISTO** | **Muda na linha 2295**: 2288–2293 é HIST; 2295–2334 é **LEI**; 2335–2372 ("Ressalva honesta", "Degrada para consecutivo", "Reversibilidade") é MISTO — a ressalva de custo é LEI declarada, o parágrafo de reversibilidade é HIST. |
| "Âncora de profundidade" | 2374–2482 | **MISTO** | **Muda na linha 2414**: 2376–2412 é HIST ("O defeito, medido", "É o quarto caso do mesmo padrão", "Por que a alternativa não serve", "Por que agora"); 2414–2481 (sondagem, reancoragem, degenerados, telemetria) é **LEI**. |
| "Extensão de orçamento por DÉFICIT" | 2483–2619 | **MISTO** | **Muda na linha 2510**: 2485–2508 é HIST; 2510–2522 (`"A regra — OBSERVACIONAL"`) é **LEI**; 2524–2539 (`"Por que observacional e NÃO preditivo"`) é HIST; 2541–2618 (alocação das extras, onde caem, teto por execução, `--offline`, telemetria obrigatória) volta a **LEI**. |
| "Correção e declaração são CAMADAS" | 2620–2641 | **HIST** | princípio de projeto, não regra executável |
| Os quatro "Resultado MEDIDO da recoleta v1.9.x" | 2642–2878 | **HIST** | 237 linhas de tabelas de recoleta |
| "Medição de profundidade (GATE)" | 2879–2969 | **HIST** | 91 linhas |
| "Confirmação do teto de 256 páginas" | 2970–3010 | **MISTO** | **Muda na linha 3006**: 2972–3004 é HIST; **3006–3009 é LEI** (a política de cache e "a chave de cache inclui a ordenação") — um parágrafo de lei órfão, alojado no fim de uma seção de medição, sem cabeçalho próprio e sem relação com o assunto dela. |

## §3[B'] Persistência do bruto (3011–3233) — 223 linhas
**LEI quase integral**, e a seção mais bem escrita do documento nesse sentido.
Subseções `pagina_origem` (3069–3092), `janela_temporal` (3093–3127),
`dias_por_100_paginas` (3128–3176) e "Duas ordenações no mesmo bruto"
(3177–3233) são todas LEI de schema e de semântica de campo. Insertos HIST
curtos: 3104–3108, 3095–3102.

## §3[H] Harness de lote (3234–3420) — 187 linhas
**MISTO, com ponto de virada nítido.** **Muda na linha 3304.**
- 3236–3302: **LEI** (checkpoint em arquivo, validação de slug, falha isolada,
  `material_esgotado` como caso esperado, log, o que fica fora do harness).
- 3304–3420: **HIST** puro — "Diagnose do déficit de buckets" (117 linhas) e
  "Resultado do lote (29 filmes)". Nada aqui é regra; é o relatório de uma
  rodada, colado dentro da seção que define o harness.

## §3[C2] Seleção downstream (3421–3735) — 315 linhas

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| A seleção, 5 passos | 3421–3446 | **LEI** | — |
| "Estratificação da seleção — E1" | 3447–3498 | **MISTO** | **Muda na linha 3456**: 3449–3454 é HIST; 3456–3475 é **LEI**; 3477–3483 ("Custo medido: ZERO") é HIST; 3485–3497 (precedência quando os dois critérios competem) volta a **LEI**. |
| "Motivos de descarte, discriminados" | 3499–3534 | **LEI** | — |
| **"Precisão da amostra — nos DOIS níveis de confiança"** | 3535–3678 | **MISTO** | **Muda na linha 3554.** 3537–3552 é **LEI/referência** (a tabela de precisão por `n`, que justifica o piso escalonado). De 3554 a 3678 são **124 linhas de HIST** — a auditoria de `MIN_CHARS`, a diagnose de `wicked-2024`, a generalização para 35 filmes, a consequência para o produto. **O cabeçalho não anuncia nada disso.** É o caso mais grave de conteúdo enterrado sob um título que não o descreve. |
| "Proposta temporal — MEDIDA, não aplicada" | 3679–3735 | **HIST** | ver Entrega 2, item 2.7 |

## §3[C3] Piso escalonado (3736–3798) — 63 linhas
**MISTO.** 3738–3758 é **LEI** (a tabela de 4 estados, os limiares declarados
arbitrários). 3760–3787 ("Caso de borda — bucket dominante em modo reduzido") é
**LEI** de comportamento com a ressalva *"documentado agora, implementado
depois"* — ver Entrega 5, item INDET-3. 3789–3793 é **LEI** de metadados.
3795 é uma **duplicata divergente** do parágrafo de cache da linha 3006
(Entrega 3, item D2). 3797 é **HIST**.

## §3[C] Filtros e cascata (3799–3828) — 30 linhas
**LEI.** O bloco de citação 3825 (por que não exibir texto bruto) é HIST com
função de lei declarada.

## §3[C'] Completamento de truncadas (3829–3840) — 12 linhas
**MISTO.** Itens 1–5 são **LEI**. O item 6 (3837, "SUPOSIÇÃO ABERTA") é
**PROT** — traz uma instrução operacional literal (*"gastar 1 requisição para
confirmar o comportamento antes de confiar cegamente"*).

## §3[D] Síntese LLM (3841–4594) — 754 linhas

**O caso extremo do padrão.** A seção abre com **676 linhas de blocos de
citação** e só então enuncia o que o estágio é.

**Muda na linha 4519** (`"- **Uma chamada por bucket** (máx. 3 por filme)"`).

- **3843–4518 — HIST**, em nove blocos de citação:
  guard-rail do SDK (3843–3891), retentativa em `resposta()` (3892–3958),
  retentativa desce para o transporte (3959–4014), retentativa dos scripts de
  classificação (4015–4125), `load_dotenv` como dívida (4126–4173), telemetria
  de retentativa (4174–4201), razão pareada (4202–4265), provider por estágio
  (4266–4312), "instrução não remove o que a distribuição impõe" (4313–4407),
  correção da projeção de lift (4408–4518).
- **LEI enterrada dentro desse histórico**, e é lei que vale hoje:
  **3862–3884** (o guard-rail de SDK e sua allowlist), **3939–3947** (onde a
  retentativa vive e por que não é contornável), **3973–3980** (a implementação
  única `_com_retentativa`), **4266–4312** (`PROVIDER_POR_ESTAGIO` — a decisão
  DeepSeek classifica / Gemini narra), **4467–4492** (a integração do
  verificador ao pipeline e a guarda de atualidade).
- **4519–4551 — LEI** (o contrato do estágio, o denominador carimbado pelo
  código, o clamp, o schema de saída).
- **4552–4573 — LEI** (o template do prompt, texto oficial) — com o defeito da
  Entrega 3, item C6.
- **4574–4583 — LEI** (validações pós-parsing).
- **4584–4594 — LEI** (anti-spoiler: risco aceito + emenda da sinopse oficial).

## §3[D2] Narrador (4595–5508) — 914 linhas

**Mesmo padrão, e com um agravante:** parte do que é apresentado como lei
descreve o narrador **arquivado** na v1.9.11.

**Muda na linha 5211** (`"Etapa **PÓS-síntese**, opcional, controlada pela flag --tom"`).

- **4597–5208 — HIST**, em sete blocos de citação (briefing determinístico
  v1.9.8, tiques de prosa v1.9.9, fechamento do narrador v1.9.10, integração
  v1.9.11, ficha persistida v1.9.12, fechamento de prosa v1.9.13).
- **LEI enterrada nesse histórico**: **4617–4641** (o que o briefing carrega e
  o que continua sendo instrução), **4665–4695** (faixas de quantificador +
  `quantificador_fora_de_faixa` / `quantificador_repetido`), **4757–4767**
  (best-of-3 e a seleção por código), **5029–5044** (contrações pré-aprovadas
  do rótulo de peso), **5102–5121** (rótulo comparativo na colisão).
- **5211–5225 — LEI** (decisão de arquitetura: o narrador nunca vê review
  bruta; os três movimentos).
- **5226–5235 — HIST** (diagnóstico de fluência).
- **5236–5248 e 5288–5293 — HIST**, e apontam para o §E2 aposentado
  ("MIGRADOS PARA O EDITOR §E2").
- **5249–5287 — LEI** (marcação de perspectiva: pré-computação, regra,
  validação).
- **5294–5361 — MISTO.** **Muda na linha 5308**: 5296–5307 (a tabela de
  métricas) é LEI de telemetria; 5308–5321 é HIST. E **5323–5360 é o "Prompt
  fixo do narrador (SPEC — texto oficial)"** — apresentado como LEI, mas é o
  prompt do narrador **arquivado**. Ver Entrega 3, item C3.
- **5362–5467 — MISTO.** A "regra (c) em duas variantes" descreve o mesmo
  narrador arquivado; mas **5411–5434** (o mapa de faixas de `rotulo_peso`) é
  **LEI vigente** e é consumida pelo veredito e pelo frontend hoje.
- **5468–5489 — HIST** (telemetria `quantificadores_usados` do narrador antigo).
- **5490–5508 — LEI** (invariante de vocabulário do peso: notas × reviews).

## §3[D3] Rotulagem por eixo (5509–5668) — 160 linhas
**MISTO.** 5511–5535 é **LEI** (uma chamada por bucket, validação mecânica,
o que não estiver na lista vira `livre`). 5537–5556 ("A assimetria de
validação") é **LEI de declaração** — a ressalva de primeira classe e a
mitigação obrigatória. 5558–5585 é HIST. **5587–5668 ("DUAS POPULAÇÕES DE 40")
é HIST auto-declarado**, 82 linhas.

## §3[V] Veredito (5669–6467) — 799 linhas

| Subseção | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Abertura | 5669–5678 | **LEI** | — |
| "O defeito medido" | 5679–5700 | **HIST** | — |
| "Posição no pipeline, insumo e saída" | 5701–5757 | **MISTO** | 5703–5730 é **LEI**; o bloco 5732–5756 é MISTO — a guarda `LIMITE_LOTE_SEM_CONFIRMACAO` (5748–5756) é **LEI**, o resto é HIST. |
| "Schema do bloco `veredito`" | 5758–5790 | **LEI** | — |
| "O contrato do briefing" | 5791–5822 | **LEI** | com a linha 5804 desatualizada (Entrega 3, C7) |
| "`assunto_compartilhado`" | 5823–5855 | **MISTO** | **Muda na linha 5837**: 5825–5835 é LEI (critério, desempate, piso de 25%); 5837–5854 é HIST + limitação declarada. |
| "A serialização não contém NENHUM algarismo" | 5856–5892 | **LEI** | — |
| "O limiar é BINÁRIO" | 5893–5909 | **MISTO** | **Muda na linha 5899**: 5895–5897 é HIST desatualizado (o exemplo `the-godfather` 19,6pp contra margem 20); 5899–5908 é **LEI** (a proibição de tratar quase-passou como contraste) — mas proíbe alterar um parâmetro que já foi revogado. |
| "As invariantes do prompt" | 5910–5970 | **LEI** | as 10 invariantes; a única do documento com numeração estável |
| "[v1.9.22] Deflação, neutralidade, padrão de abertura" | 5971–6203 | **MISTO** | 233 linhas, quase todas **HIST**. **A LEI está em 6035–6070** (a métrica do padrão sintático de abertura, o desempate e a política de snapshot). Os blocos `[v1.9.23]` (6072–6196) são HIST e diagnóstico aberto. |
| "Best-of-3, validações e seleção" | 6204–6283 | **LEI** | tabela de flags, chave dupla, três guarda-corpos |
| "O que estas validações não pegam" | 6284–6333 | **LEI de limitação** + fallback | o bloco de citação 6290–6304 (os três falsos positivos) é HIST |
| "Persistência e render" | 6334–6351 | **LEI** | — |
| "O veredito deixa de ser 100% determinístico" | 6352–6381 | **HIST** | — |
| "O risco central desta mudança" | 6382–6397 | **HIST** | — |
| "Critério de aceite (v1.9.21)" | 6398–6437 | **HIST** | — |
| "Modelo — configurável, nunca hardcoded" | 6438–6467 | **MISTO** | **Muda na linha 6445**: 6440–6443 é LEI; 6445–6466 é HIST (inventário da chave, tensão do A/B). |

## §3[F] Ficha do filme TMDB (6468–6570) — 103 linhas
**MISTO, alternando a cada parágrafo.** LEI: 6470, 6472–6478 (resolução de ID e
de ano, guarda de sanidade), 6535 (rastreabilidade), 6539–6543 (checagem de
completude, campos), 6551–6557 (diretor latino, fallback de sinopse, cache,
falha nunca bloqueia), 6559–6569 (saída). HIST: 6480–6534 (as medições de
`include_image_language`, a ordem `_melhor`, o custo zero), 6545–6547 (os dois
retrofits). **6549 é um defeito conhecido aberto** (`talk-to-me-2022` publica a
ficha de outro filme).

## §3[G] Distribuição de notas (6571–6658) — 88 linhas
**LEI** quase integral (endpoint, estrutura, três armadilhas, agregação, a cota
não segue o peso, falha nunca bloqueia, saída). HIST: 6617–6625.

## §3[E2] Editor (6659–6747) — 89 linhas
**HIST na prática, LEI na redação.** O estágio foi **aposentado na v1.9.10**
(registrado em 4859–4916), mas esta seção abre com *"Etapa PÓS-narrador, ativa
junto com `--tom narrativo|ambos`, desligável com `--no-edicao`"* — presente do
indicativo, flag que não existe mais. É a seção de maior risco de RAG do
documento inteiro: 89 linhas de prompt e de regras de verificação para um
estágio que não roda.

## §3[E] Render (6748–7980) — 1.233 linhas

A maior seção do documento, e a mais fragmentada. Estrutura em blocos
indentados (`   ####`), invisíveis a uma varredura por `^#`.

| Bloco | Linhas | Tipo | Onde muda |
|---|---|---|---|
| Render de terminal (itens 1–4) | 6749–6759 | **LEI** | — |
| Ordem publicada v1.9.26 | 6760–6773 | **HIST** | auto-declarado como registro histórico na linha 6774 |
| Ordem publicada v1.9.32 | 6774–6793 | **LEI** | — |
| Barra de proporção | 6794–6855 | **MISTO** | **Muda na linha 6804**: 6794–6802 é LEI; 6804–6841 é MISTO (o requisito "sem vão" é LEI, a rodada rejeitada é HIST); 6842–6854 (a variante divergente recusada) é HIST puro. |
| Disclaimer da cota | 6856–6885 | **MISTO** | **Muda na linha 6876**: 6858–6874 é HIST; 6875–6877 (*"Se o percentual do cabeçalho algum dia sair da tela, esta frase tem de voltar"*) é **LEI condicional**; 6879–6885 é LEI (o ramo sem distribuição). |
| "A ORDEM DOS BLOCOS EM DESTAQUE — POR PESO" | 6896–6969 | **MISTO** | **Muda na linha 6914**: 6898–6912 é LEI (mecânica); 6914–6968 é HIST (resultado medido, dessincronia, descompasso do veredito). |
| "O CALLOUT DE PERCENTUAL" | 6970–7075 | **MISTO** | **Muda na linha 7010**: 6972–7008 é **LEI** (a regra de empacotamento, a fórmula); 7010–7018 (as duas alternativas rejeitadas) é HIST; 7020–7044 volta a LEI (por que vale para qualquer distribuição, onde a conta mora, o indicador); 7046–7074 é HIST (medições) com LEI em 7064–7074 (`aria-hidden`). |
| "A ANIMAÇÃO DE ENTRADA DA BARRA" + 4 sub-blocos | 7076–7245 | **MISTO** | **Muda na linha 7078**: 7078–7081 é HIST (o modelo que saiu); 7083–7131 é LEI; os quatro `#####` (7132–7245) são MISTO — cada um abre com a decisão (LEI) e fecha com a medição que a sustenta (HIST). |
| "ACESSIBILIDADE DA ANIMAÇÃO" | 7246–7287 | **LEI** (4 requisitos) | 7278–7286 ("CADÊNCIA — DECISÃO EM ABERTO") é **estado aberto** |
| "O PÔSTER" | 7288–7374 | **MISTO** | **Muda na linha 7335**: 7290–7334 é LEI + HIST alternando; 7335–7373 (proporção reservada, tamanhos de CDN, lazy/eager, onde mora) é LEI com medições HIST intercaladas. |
| "O BACKDROP no topo" + 6 sub-blocos | 7375–7554 | **MISTO** | **Muda na linha 7383**: 7377–7381 é LEI; 7383–7431 (a exceção ao anti-spoiler) é **LEI de exceção declarada**, escrita como ensaio; 7433–7476 é LEI (a ordem determinística) + HIST (por que não as outras); 7477–7554 alterna LEI (fallback, proporção, `alt`) e HIST (medições de CLS). |
| "O TOPO EDITORIAL (v1.9.32)" + 8 sub-blocos | 7555–7869 | **MISTO** | O bloco mais denso de decisões de UI. **LEI**: 7564–7568 (a sinopse saiu), 7598–7607 (diretor em caixa alta, via CSS), 7626–7644 (a construção do fade), 7673–7730 (o acoplamento `--fade-solid`/`--hero-overlap` — **é a melhor lei do documento**: uma invariante fechada por aritmética), 7739–7751 (o que não foi sacrificado no link), 7816–7857 (a coreografia), 7859–7869 (o fallback). **HIST**: 7570–7586 (o que a remoção da sinopse custa), 7646–7669 (a composição analítica dos 34 backdrops), 7776–7814 (a redundância de peso, medida e mantida). |
| "O PÔSTER SEM TEXTO" | 7870–7913 | **MISTO** | **Muda na linha 7897**: 7872–7895 é HIST (a decisão e o mecanismo removido); 7897–7912 é LEI (o fallback). |
| "ATRIBUIÇÃO AO TMDB" | 7914–7942 | **LEI** | obrigação contratual |
| "A LINHA DE METADADOS — tipografia" | 7943–7980 | **MISTO** | **Muda na linha 7950**: 7945–7948 é LEI; 7950–7979 é HIST (a licença da SF Pro, a alternativa Inter, a correção de registro). |
| "As TRÊS COLUNAS ALINHADAS POR EIXO" | 7981–8030 | **LEI** | os quatro estados de renderização |
| "Busca" | 8031–8039 | **LEI** | — |
| "Janela temporal ao lado do denominador" | 8040–8064 | **LEI** | — |

## §4 Metadados obrigatórios (8065–8189) — 125 linhas
8067–8108 é **LEI** (schema completo). 8110–8189 ("O bloco `margem`") é
**MISTO**: **muda na linha 8144** — 8112–8142 é HIST (o defeito e seu alcance),
8144–8187 é **LEI** (o schema novo, `acima_da_margem` como fonte única).

## §5 Critérios de aceite (8190–8199) — 11 linhas
**MISTO.** Os critérios 1–5 são **PROT** (bateria de aceite). **O critério 6
(linha 8197) é um único item de lista com ~2.500 palavras de HIST** — cinco
versões de medição de orçamento de requisições, um achado lateral não previsto,
e uma correção de registro, tudo numa linha física.

## §6 Incógnitas de Fase 1 (8201–8210) — 10 linhas
**HIST**, auto-declarado.

## Changelog (8211–8600) — 390 linhas
**HIST.** É a única seção do documento cujo tipo é evidente pelo título.

## Status de aceite da v1 (8601–8620) — 20 linhas
**HIST.** O critério 1 da tabela (linha 8607) cita *"10 níveis × 10 válidas"* —
a cota revogada na v1.9.0.

## Candidatos à próxima versão (8621–8625) — 5 linhas
**HIST** + 1 candidato genuinamente aberto (validador pós-parsing por tema).

---

## Contagem agregada da Entrega 1

| Tipo | Linhas (estimativa) | % |
|---|---:|---:|
| **HISTÓRICO** | ~5.650 | ~66% |
| **LEI** | ~2.600 | ~30% |
| **PROTOCOLO** | ~375 | ~4% |
| **Total** | 8.625 | 100% |

**A estimativa de LEI é generosa de propósito.** Ela conta a linha inteira
onde a lei está enunciada *junto* da justificativa. Se a justificativa embutida
for movida para o HISTÓRICO junto com o resto, a LEI cabe em **1.200–1.500
linhas**. A diferença entre os dois números é exatamente o que a Entrega 4
precisa decidir: um arquivo de lei enxuto (bom para RAG, ruim para quem quer
entender) ou um arquivo de lei justificado (o oposto).

---

# Entrega 2 — Decisões fechadas redigidas como debate

Critério: a decisão tem correção numerada, tem "MEDIDO", ou tem resultado de
auditoria — **e mesmo assim a seção continua no tempo verbal da deliberação**,
com o veredito aparecendo em outro lugar ou não aparecendo.

Sete ocorrências. Não reescrevi a SPEC — o "depois" abaixo é ilustração.

### 2.1 — §2.3, linha 809: candidato revogado 16 linhas adiante

**Antes (linhas 809–813):**
> *Candidato de próxima versão: amostragem estratificada por período (N páginas
> de `by/added` + N de `by/added-earliest`), que o superset persistido já
> suporta sem mudança de arquitetura.*

**O que fechou:** a linha 825 diz literalmente *"O candidato registrado acima
… deixa de ser candidato"*, e a passada seletiva foi implementada na v1.9.6,
com limiar, orçamento e telemetria.

**Por que importa:** um leitor (ou um RAG) que recupere o trecho 789–822
recebe "isto é uma ideia futura" sobre uma coisa que está em produção. As duas
frases estão na mesma seção, mas em subseções diferentes.

**Depois, em tom de veredito:**
> *Regra vigente (v1.9.6): a amostragem estratificada por período existe e é a
> passada seletiva sob `by/added-earliest`, condicionada a
> `dias_por_100_paginas < 20`. Ver "A passada SELETIVA", abaixo. Este parágrafo
> registra o estado anterior à decisão.*

### 2.2 — §2.5, linha 1449: a opção anunciada antes do veredito

**Antes (linhas 1449–1451):**
> *Existe uma correção que **funcionou** — o passe de verificação separado
> (V2 `alvo`), que leva a precisão de 0,486 para 0,794 em passada única, com
> projeção de de-saturação de 75,5% para 35,7% no corpus.*

**O que fechou:** o parágrafo imediatamente seguinte (1453) é uma **CORREÇÃO DE
REGISTRO (v1.9.31)** dizendo que ela *foi* aplicada, na v1.9.16, e que o texto
anterior a descrevia como pendente. A correção está lá; a frase de abertura
não foi ajustada.

**Por que importa:** é o único caso do documento em que a correção admite
explicitamente que o parágrafo acima dela está no tempo verbal errado, e mesmo
assim o parágrafo permaneceu. A ordem de leitura entrega a opção antes do fato.

**Depois:**
> *Regra vigente: o passe de verificação separado (`V2_alvo`, passada única)
> roda em produção desde a v1.9.16, como estágio à parte após o consenso de
> votação. Ele leva a precisão de `impacto_emocional` de 0,486 para 0,794. A
> aplicação é declarada em `eixos.verificador`.*

### 2.3 — §2.9, linha 1893: decisão de esperar, já superada

**Antes (linhas 1893–1903):**
> *Decisão do dono: NÃO republicar por ora. … O estudo da margem — a próxima
> sessão — pode reformular o limiar de 20pp … Republicar agora, sob a margem
> atual, seria trabalho refeito se a margem mudar.*

**O que fechou:** a subseção "FECHADA na v1.9.34" (1933–1950) — a republicação
aconteceu, 16 filmes, sob a lei por `n`. E a própria subseção corrige o
argumento: *"a decisão de esperar se confirmou, mas por uma razão diferente da
registrada acima"*.

**Por que importa:** 40 linhas separam a deliberação do veredito, e o
argumento registrado na deliberação está medido como errado. Quem citar 1893
como razão vigente cita um argumento que a própria SPEC refutou.

**Depois:**
> *Fechado (v1.9.34): a republicação aconteceu, 16 filmes, sob a lei por `n`.
> A decisão de esperar se justificou — mas não pelo argumento de "trabalho
> refeito" (MEDIDO: valia 4 regenerações, não o trabalho inteiro), e sim porque
> republicar sob 20pp poria no ar 16 estados com 24–38% de taxa de falso
> contraste, para tirar depois.*

### 2.4 — §3[B], linha 2730: menu de cinco saídas para um problema resolvido

**Antes (linhas 2730–2750):**
> *Não corrigido nesta versão … Registrado como o **candidato número 1 da
> próxima versão**, com quatro saídas conhecidas: 1. orçamento de páginas por
> BUCKET … 2. teto de volta a 6 … 3. aceitar e deixar o piso escalonado
> reportar … 4. fronteira com 3 níveis no meio … 5. baixar `min_chars` …*
> *A opção 3 é o comportamento em vigor, por omissão.*

**O que fechou:** a saída 1 foi implementada na v1.9.1, tem seção própria
("Orçamento de páginas POR BUCKET", 2234) e resultado medido (2771). A frase
*"A opção 3 é o comportamento em vigor"* é falsa desde a v1.9.1.

**Por que importa:** são 21 linhas de menu de opções onde a resposta já é
conhecida, e a última linha afirma um estado revogado.

**Depois:**
> *Resolvido na v1.9.1 pela saída 1 (orçamento por BUCKET, §3[B]). As outras
> quatro saídas ficam registradas como as alternativas consideradas e
> descartadas; nenhuma delas descreve o comportamento em vigor.*

### 2.5 — §3[D2], linha 4776: gate do editor, já decidido

**Antes (linhas 4776–4786):**
> *(5) Gate do editor [E2] — PREPARADO, não decidido. … Se o ritmo se sustentar
> sem ele, o E2 é aposentado … Se faltar ritmo, a alternativa já decidida é
> reescopar o editor por MOVIMENTO … Esta versão **não** aposenta nem reescopa
> nada: só produz o material da decisão.*

**O que fechou:** o bloco imediatamente seguinte, "FECHAMENTO DO NARRADOR …
editor aposentado (v1.9.10)" (4787), item (3): *"Editor [E2] APOSENTADO.
Decisão do dono do projeto"*.

**Por que importa:** a condicional fica de pé, e §3[E2] (6659) continua
descrevendo o estágio como ativo. São três lugares do documento em desacordo.

**Depois:**
> *Decidido na v1.9.10: o editor [E2] foi APOSENTADO — o ritmo se sustenta sem
> ele. Código em `experimentos-editor-e2-arquivado/`; chamada removida de
> `cli.py`; flags `--no-edicao`/`--com-editor` removidas. §3[E2] descreve o
> estágio como registro histórico.*

### 2.6 — §3[V], linha 6280: condicional cuja medição já saiu

**Antes (linhas 6280–6282):**
> *Se a medição da Entrega 7 mostrar que este critério seleciona texto
> EMPILHADO em vez de fluente, ele é o primeiro parâmetro a revisar. A hipótese
> sob teste é a informatividade ancorada, não a brevidade.*

**O que fechou:** "Critério de aceite (v1.9.21)", linha 6419: *"O critério de
âncoras NÃO produziu texto empilhado, que era a hipótese sob teste … a média
de palavras ficou em 41,4 contra um teto de 55 … O teto de 2 âncoras cumpriu o
papel."*

**Por que importa:** a hipótese foi testada e sobreviveu, mas o texto continua
convidando a revisar o parâmetro. É a forma mais barata de correção deste
relatório: uma frase.

**Depois:**
> *MEDIDO na v1.9.21: o critério de âncoras não produz texto empilhado — a
> chave primária decidiu 11 de 35, a média ficou em 41,4 palavras contra teto
> de 55, e o teto de 2 âncoras cumpriu o papel. A hipótese da informatividade
> ancorada está confirmada; o parâmetro fica.*

### 2.7 — §3[C2], linha 3679: um achado fechado dentro de uma proposta aberta

**Antes:** a subseção inteira se chama *"Proposta temporal (v1.9.6) — MEDIDA,
não aplicada"* e termina em *"RECOMENDAÇÃO: S2"*.

**Este caso é diferente dos seis anteriores** — a proposta é genuinamente
aberta e está corretamente rotulada. O problema é que **um achado fechado está
dentro dela**, nas linhas 3721–3730:

> *S1 não é o caso neutro que o nome sugere, e é o principal achado: … sob
> `by/added-earliest` `pagina_origem = 1` é o material mais antigo … a seleção
> atual classifica reviews de 2012 como "faixa 1" — a mais rasa/recente.
> **Medido:** sob S1 a mistura varia de 1 a 19 antigas por bucket, e varia
> DENTRO do mesmo filme.*

Isso é um **defeito medido do comportamento em vigor**, não uma propriedade de
uma proposta. Ele está sepultado num bloco cujo cabeçalho diz "não aplicada",
que é o rótulo que faz um leitor pular a seção.

**Depois** (como item próprio, fora da proposta):
> *DEFEITO MEDIDO NO COMPORTAMENTO EM VIGOR (v1.9.6, não corrigido): a seleção
> não lê `ordenacao_origem`, então classifica material de `by/added-earliest`
> como faixa rasa/recente. Consequência medida: a mistura de material antigo
> varia de 1 a 19 por bucket e varia dentro do mesmo filme
> (`the-substance`: 47,5% em `medianas`, 5% em `positivas`). A correção entra
> junto da proposta temporal, abaixo.*

---

# Entrega 3 — Redundância e remissão cruzada frágil

## A. Remissões que apontam para alvos inexistentes

| # | Onde | Remissão | Diagnóstico |
|---|---|---|---|
| A1 | 5927 | *"(Mesma invariante **7b de §D2**, aplicada a um estágio novo.)"* | **§D2 não tem invariante 7b.** As invariantes de §D2 são alfabéticas (a–h no prompt, a–d em RITMO, e–i em REGISTRO). A única ocorrência de "7b" no documento é um item de changelog sobre timeout de LLM. **PRECISA-REPETIR-A-REGRA** — a invariante em questão (anti-fabricação de contraste) tem de ser enunciada por extenso em §3[V], porque não há para onde apontar. |
| A2 | 4401 | *"as 7 regras de `A_regra` (**§ correção de recall em review curta**) SÃO instrução"* | **Não existe seção com esse nome na SPEC.** `A_regra` aparece 6 vezes e nunca é definida. **PRECISA-REPETIR-A-REGRA** ou apontar para `CLASSIFICACAO_CONSOLIDADO.md`. |
| A3 | 4118 | *"alimentaram a promoção da regra `A_regra`, §3[D] 'razão PAREADA'"* | A subseção "razão PAREADA" existe (4202), mas trata do **preditor de mudança de frequência**, não da promoção de `A_regra`. **RESOLVE-SE-COM-LINK**, corrigindo o alvo. |

## B. Remissões por "mesma política / mesmo princípio" sem a regra ao lado

O documento tem ~30 construções do tipo *"mesma política de X"*. A maioria é
inofensiva porque a regra está a poucas linhas. Estas não são:

| # | Onde | Remissão | Classificação |
|---|---|---|---|
| B1 | 850, 3707, 3749 | *"Limiar ARBITRÁRIO na mesma acepção dos limiares do piso escalonado (§3[C3])"* / *"mesma política de §3[C3] e de `LIMIAR_PASSADA_ANTIGA`"* / *"mesma política dos limiares de `marcacao_perspectiva` (v1.5.0)"* | **PRECISA-REPETIR-A-REGRA.** As três ocorrências se referem umas às outras em círculo e **nenhuma delas enuncia a política**. O mais próximo de um enunciado está em 3748–3752, e é uma descrição do caso, não da regra. A política é: *"limiar declarado ARBITRÁRIO = a ordem de grandeza é defensável, o corte exato não; vive em config, nunca como constante enterrada; é calibrável sem bump de comportamento."* Uma frase, e ela não existe em lugar nenhum. |
| B2 | 5718 | *"**Nunca reviews brutas** — mesma fronteira de §D2 desde a v1.2.0"* | **PRECISA-REPETIR-A-REGRA.** É a invariante anti-spoiler / anti-embelezamento mais forte do produto, e um arquivo (ou chunk de RAG) que descreva §3[V] sozinho fica com um ponteiro em vez da regra. A regra completa está em 5213–5215 e cabe em duas linhas. |
| B3 | 3193 | *"respeita o mesmo princípio que mantém `passou_por_relaxamento` fora do bruto"* | **RESOLVE-SE-COM-LINK.** O princípio está enunciado na mesma seção, 140 linhas acima (3050–3055). Falta só o ponteiro explícito — hoje diz "acima". |
| B4 | 1053 | *"pelo mesmo argumento que este §2.5 já usou para a ausência de bullets de contraste"* | **RESOLVE-SE-COM-LINK.** O argumento é citado literalmente na sequência (*"se ficar como AUSÊNCIA, vai parecer bug ao leitor"*), então a regra está repetida — mas o alvo original (1407) está numa subseção marcada como histórica. |
| B5 | 2062 | *"Ela tem guarda de TRAP VAZIO (**lição da v1.9.25**)"* | **RESOLVE-SE-COM-LINK, e o link está errado.** A regra de trap vazio está na própria §2.10, regra 1 (1991), atribuída à **v1.9.34**. Duas versões diferentes para a mesma lição, na mesma seção, com 71 linhas de distância. |
| B6 | 6206 | *"Mesmo padrão de `narrador.narrar()` (§D2, v1.9.11), **reproduzido, não reusado**"* | **RESOLVE-SE-COM-LINK.** As três razões de não reusar estão enunciadas logo abaixo. Bom exemplo do que fazer. |
| B7 | 7622 | *"a mesma ideia do degradê da célula do mosaico (v1.9.29 …), adaptada"* | **RESOLVE-SE-COM-LINK.** As duas diferenças estão enunciadas; a ideia base, não. |
| B8 | 5853 | *"é a mesma política de omissão autorizada da v1.4.1: preencher com genérico é pior do que não preencher"* | **RESOLVE-SE-COM-LINK** — a regra vem depois dos dois-pontos. Modelo do que fazer nos casos B1 e B2. |

## C. Regras vigentes contraditas por texto vigente

Estes não são "duas populações diferentes explicadas". São afirmações que se
contradizem sem nenhuma nota reconciliando.

| # | O quê | Onde diz A | Onde diz B |
|---|---|---|---|
| **C1** | **Versão do documento** | Linha 1: `# Espectro 24 — Especificação v1.9.25`, linha 3: `Data: 2026-08-26` | Conteúdo vai até v1.9.37 / 2026-09-04 (linhas 424, 527, 2029). O título mente sobre 12 versões. |
| **C2** | **Estágio [E2] Editor** | 6661: *"Etapa PÓS-narrador, ativa junto com `--tom`, desligável com `--no-edicao`"* — 89 linhas em presente vigente | 4859: *"Editor [E2] APOSENTADO"*; 4911: *"As flags `--no-edicao`/`--com-editor` foram removidas"*. Também 642 (§2.1) e 2089 (diagrama) tratam o editor como vivo. |
| **C3** | **Prompt do narrador** | 5323: *"Prompt fixo do narrador (SPEC — texto oficial, `NARRATOR_SYSTEM_PROMPT`)"* — 38 linhas apresentadas como lei | 4997–5011: o narrador antigo foi arquivado em `experimentos-narrador-antigo-arquivado/`, e `NARRATOR_SYSTEM_PROMPT*` está nomeadamente entre o que saiu. |
| **C4** | **Diagrama do pipeline** (2075–2092) | Lista `[E2] editor … --no-edicao pula` | Não lista `[D3]` (v1.9.14), não lista `[V]` (v1.9.21), não lista o estágio de CONDIÇÕES (v1.9.35–37, em produção). O diagrama é a primeira coisa que qualquer leitura de §3 encontra. |
| **C5** | **`MARGEM_LIFT_PP`** | 5804 (§3[V], tabela do contrato do briefing): `margem_lift_pp` ← `config.MARGEM_LIFT_PP`; 5901: *"alterar `MARGEM_LIFT_PP`, aqui ou em lugar nenhum"* | 8174 (§4): `margem_lift_pp` *"agora é o limiar resolvido (float, uma casa: 22,83 para n=40) em vez do inteiro 20 … é derivado e para exibição; nenhuma decisão o lê"*. |
| **C6** | **Fronteira de bucket no prompt oficial de §3[D]** | 4554: *"parametrizado por `{bucket_nome}` e `{intervalo}` (ex.: `negativas` / **`0.5–2.5 estrelas`**)"* | 663 (§2.2, tabela vigente): `negativas` = **0,5–2,0★**; 0,5–2,5★ é a fronteira **anterior à v1.9.0**. |
| **C7** | **Cota no exemplo de schema de §3[D]** | 4537: `"n_reviews_analisadas": 50` no JSON de saída obrigatória | 602 (§2): cota de análise por bucket = **40 · 40 · 40**. |
| **C8** | **Providers e modelos default** | 4520: *"Providers suportados: **Gemini** e **Anthropic**"*; 4521: *"Default de modelo Gemini — `gemini-2.5-flash`… Default Anthropic: `claude-sonnet-4-6`"* | 4266–4312: `PROVIDER_POR_ESTAGIO` — **DeepSeek** classifica, **Gemini** narra; 4917: narrativa fixada em `gemini-3.7-flash`; 6446: veredito em `gemini-3.1-pro-preview`; changelog v1.8.0: `DEFAULT_PROVIDER = "deepseek"`. |
| **C9** | **`the-godfather` contra a margem** | 5895: *"melhor lift das negativas em 19,6pp contra a margem de 20 … Falha por 0,4pp"* | 1099: sob a lei por `n`, o limiar de `the-godfather` é **26,4pp**. A conclusão (`valorativo`) não muda; o número da comparação está errado por 6,4pp. |
| **C10** | **Contagem `tematico`/`valorativo`** | §3[V] inteiro (5669–6467, 799 linhas) opera sobre **17 `valorativo` / 18 `tematico`**, sem nenhum carimbo de que isso mudou — inclusive nas medições de aceite e nas linhas de base de repetição | 1372 (§2.5): sob a lei da v1.9.34 o catálogo é **6 `tematico` / 28 `valorativo` / 1 sem estado**. Uma sessão que ler só §3[V] sai com a distribuição errada do catálogo. |
| **C11** | **Critério 1 do aceite da v1** | 8192 (§5): *"os três buckets em `estado_piso: completa` com os 40 preenchidos (v1.9.0; era '10 níveis completos, 10 válidas cada')"* | 8607 (Status de aceite): a evidência do mesmo critério 1 diz *"10 níveis × 10 válidas"* — a régua revogada, sem a nota que §5 tem. |

## D. Números e frases repetidos com valores diferentes

| # | Grandeza | Valores encontrados | Diagnóstico |
|---|---|---|---|
| **D1** | **`impacto_emocional` no corpus, antes do verificador** | **75,5%** (1431, 1439, 1451, 4351) e **75,6%** (1470, 1471, 4449, 4495, 4499) | Mesma grandeza, mesmo corpus, dois valores, nenhuma nota reconciliando. É exatamente o caso "5,9% em um lugar, cerca de 6% em outro" — só que aqui os dois estão escritos com uma casa decimal, o que impede lê-los como arredondamento declarado. |
| **D2** | **Tamanho do corpus classificado dos 35 filmes** | **4.181** (1470, 4495) · **4.056** (1766, 1795, 1825) · **5.371** (502) · **2.866** (1471, 1794, 1823) | Dois são explicados (2.866 = cobertura 70,7%; 4.056 = 100%). **4.181 e 5.371 não são reconciliados em lugar nenhum do documento.** O 4.181 aparece como denominador de "reviews classificadas dos 35 filmes" na mesma tabela em que 2.866 é "a seleção de produção" — e 4.181 > 4.056, que §2.8 declara ser 100%. |
| **D3** | **Fração de ruído a 20pp** | **41%** (1241) · **34%** (1250) · **42,8%** (1287) · **41,1%** (1293, citando outro corpus) | Este está bem tratado: cada valor tem população e método declarados, e há uma correção de registro explícita (1276). Registro aqui como **o modelo de como fazer**, não como defeito. |
| **D4** | **Parágrafo de cache** | 3006–3009 e 3795 | Duas versões do mesmo parágrafo, ~800 linhas separadas, **divergentes**: a primeira acrescenta *"A chave de cache inclui a ordenação (v1.9.0) — trocar de ordenação é uma amostra diferente"* (regra importante); a segunda diz *"(SQLite ou JSON por filme)"* e *"Cache não expira na v1"*, e omite a ordenação. Nenhuma das duas cita a outra. |
| **D5** | **Lição do trap vazio** | v1.9.34 (§2.10, cabeçalho e regra 1) vs v1.9.25 (2062) | Ver B5. |
| **D6** | **Taxa de falso contraste da lei** | *"Entre 3,7% e 7,5%, média ≈ 5%"* (1093) · *"≈5%"* (1187) · *"a taxa de 5% é in-sample e OTIMISTA … não cite '5%' como propriedade da regra"* (1145) | Coerente, mas com uma tensão real: 1187 usa "≈5%" como o critério vigente, e 1145 proíbe citar 5% como propriedade da regra. As duas frases estão a 42 linhas uma da outra. **Vale um enunciado único.** |
| **D7** | **Slugs default de `publicar_catalogo.py`** | *"os 32 slugs default"* (5745) vs catálogo de **35** filmes em toda parte | Provavelmente correto (32 + os 3 do catálogo original), mas não é explicado em lugar nenhum. |

---

# Entrega 4 — Proposta de corte por arquivo (não executada)

## Critério de desenho

Cada arquivo tem de **responder um tipo de pergunta sozinho**, sem que o RAG
precise carregar os outros. As perguntas são:

- **LEI** → *"o que vale agora?"* — é o arquivo que uma sessão de implementação
  carrega inteiro e que um validador consulta.
- **PROTOCOLO** → *"como eu faço X?"* — carregado sob demanda, quando a sessão
  vai medir, testar ou publicar.
- **HISTÓRICO** → *"por que essa regra é assim, e o que já foi tentado?"* —
  carregado só quando alguém vai **reabrir** uma decisão.
- **ABERTO** → *"o que eu preciso decidir?"* — hoje espalhado por 12 lugares.

## Os quatro arquivos

### 1. `SPEC_LEI.md` — invariantes vigentes
**Estimativa: 1.200–1.600 linhas** (ou 2.400–2.700 se a justificativa embutida
for junto — ver a nota da Entrega 1). *Estimativa, não contagem.*

Contém, na ordem do pipeline:

- **Princípio e escopo** — o núcleo do §0 (12–18, 44–56), as três exceções de
  interface enunciadas como regra sem o ensaio (57–84, 106–146, 198–200 +
  231–239, 330–358 + 399–413), Objetivo/Público-alvo (571–576), §1.
- **Parâmetros** — §2 (tabela sem as linhas riscadas), §2.1, §2.2 (regra +
  fronteiras + o piso de reversibilidade de 732–741), §2.3 (regra + passada
  seletiva), §2.4.
- **A régua** — §2.5 núcleo: taxonomia, `taxonomia_id`, lift, **a lei por `n`
  inteira** (979–1024), a frase de ausência (1049–1078), seleção 2+3, estado
  `contraste` (1355–1373), o critério de erro (1186–1190).
- **O pipeline** — o diagrama **corrigido** (com `[D3]`, `[V]` e o estágio de
  CONDIÇÕES), e a lei de cada estágio: `[A]`, `[C1]`, `[B]` (as partes de lei
  identificadas na Entrega 1), `[B']` quase inteiro, `[H]` 3236–3302, `[C2]`,
  `[C3]`, `[C]`, `[C']`, `[D]` 4519–4594 + a lei enterrada (guard-rail,
  `PROVIDER_POR_ESTAGIO`, integração do verificador), `[D2]` 5211–5225 +
  marcação de perspectiva + `rotulo_peso` + vocabulário do peso + a lei
  enterrada do briefing determinístico, `[D3]` 5511–5556, `[V]` (schema,
  contrato do briefing, serialização sem algarismo, as 10 invariantes,
  best-of-3, validações, fallback), `[F]`, `[G]`, `[E]` (as ~250 linhas de lei
  identificadas), `[E2]` **não entra** (estágio aposentado).
- **Schema** — §4 inteiro + o bloco `margem`.
- **A regra do gatilho de regeneração** (1926–1931) — hoje enterrada em §2.9.

**Três consertos que a extração obriga** (e que não são reestruturação, são
correção de fato): C4 (o diagrama), C5/C9 (`MARGEM_LIFT_PP` e o exemplo do
`the-godfather`), C6/C7 (o intervalo e a cota no prompt oficial de §3[D]).

### 2. `SPEC_PROTOCOLO.md` — como fazer
**Estimativa: 350–450 linhas.**

- **§2.10 inteira** (traps de escopo, ambiente, constante hoisted) — 96 linhas.
- **P1–P7 e P4 revisado** (1614–1643) + o desenho de gabarito em duas etapas
  (1718–1729) + a recomendação de abstenção (1711–1716) — ~110 linhas.
- **A leitura cega / folha reduzida** — o que hoje está espalhado em §2.7 e nos
  arquivos `FOLHA_LEITURA_*`.
- **O que fazer ao expandir o catálogo** (1154–1158: rodar o nulo do máximo nos
  filmes novos e recalibrar a constante, não os filmes).
- **Regras de registro de medição**: partição em tabela com total (1389–1391),
  "estender a métrica ANTES de declarar vitória" (6084–6089), "um exemplo dentro
  do prompt tem força de regra" (444–447).
- **§5, critérios 1–5** (bateria de aceite) + a leitura humana de 100% antes de
  publicar (340–343).
- **A guarda de lote** (`LIMITE_LOTE_SEM_CONFIRMACAO`) e o que cada harness
  (`gerar_veredito.py`, `enriquecer_ficha.py`, `publicar_condicoes.py`) pode e
  não pode alcançar.

### 3. `SPEC_HISTORICO.md` — por que
**Estimativa: 5.500–5.900 linhas.** *Estimativa.*

**Recomendação: não é um arquivo, são quatro.** Um único arquivo de 5.700
linhas recupera mal em RAG — o histórico de uma decisão de CSS e o de uma
decisão de amostragem competiriam pelo mesmo chunk. Divisão por arco:

| Arquivo | Conteúdo | Estimativa |
|---|---|---|
| `HISTORICO_COLETA.md` | §2.2 (consequências e riscos), §2.3 (viés de recência), §3[B] arqueologia inteira (as quatro recoletas, o gate de profundidade, o teto de 256), §3[H] 3304–3420, §3[C2] 3554–3735 | ~1.500 |
| `HISTORICO_CLASSIFICACAO.md` | §2.5 (nulo do máximo, α, margem de 20pp histórica, comparação `>=`, `impacto_emocional`), §2.6, §2.7, §2.8, §2.9, §3[D3] "duas populações de 40" | ~1.100 |
| `HISTORICO_PROSA.md` | §3[D] (os nove blocos de citação), §3[D2] (os sete blocos), §3[E2] inteiro, §3[V] (defeito medido, v1.9.22/23, aceite, modelo) | ~1.800 |
| `HISTORICO_FRONTEND.md` | §3[E] (as ~980 linhas de histórico de UI: variantes rejeitadas, medições de CLS, contraste, tipografia) | ~1.000 |
| `CHANGELOG.md` | 8211–8620, extraído como arquivo próprio | ~410 |

### 4. `SPEC_ABERTO.md` — o que ainda é decisão
**Estimativa: 150–250 linhas.** *É o arquivo que não existe hoje e o que uma
sessão nova mais precisa.*

O §0 já tem um embrião disto ("[v1.9.37] NO AR — e o que fica ABERTO", 527–569,
quatro itens). O arquivo consolidaria, com um item por decisão:

1. `expectativa` alimenta CONDIÇÕES ou pertence ao VEREDITO? (451–523)
2. As condições substituem o veredito? Sob que critério? (367–380)
3. Feelings — em espera, com dependência de ordem (§2.6)
4. Faixa de `rotulo_peso` acima de ~90% (712–718)
5. Proposta temporal S1/S2/S3 — recomendação S2, não aplicada (3679–3735)
6. Tautologia de um lado no veredito — diagnosticada, não corrigida (6158–6195)
7. Conectivo contrastivo a 82% — número medido, decisão do dono (6091–6118)
8. Cadência da animação da barra — sempre vs. uma vez por sessão (7278–7286)
9. Cache TMDB > 6 meses — dívida contratual, sem política (6535)
10. `talk-to-me-2022` publica a ficha de outro filme (6549)
11. Backfill barato de cota (3836, item 5)
12. `load_dotenv` em `classificar()` — dívida registrada, não corrigida (2015–2017, 4126–4173)
13. `anthropic_client_call` sem retentativa (4007–4013)
14. `BANDAS_QUANTIFICADOR` — código morto (2066–2069)
15. A inflação de quantidade nas paráfrases de [D] — 80 de 611 temas (559–569)

**O critério de saída de um item deste arquivo é uma decisão registrada, não
uma versão nova.** É o que impede o padrão da Entrega 2 de se repetir: hoje um
item fechado continua escrito como aberto porque o lugar onde ele está escrito
não tem estado.

## O que a divisão NÃO resolve, e vale saber antes

- **A LEI vai ficar com muito ponteiro para o HISTÓRICO.** Metade das regras
  vigentes tem a forma *"vale X, e a razão é o defeito Y"*. Cortar a razão
  deixa a lei mais recuperável e menos defensável. A saída provável é uma linha
  de ponteiro por regra (`ver HISTORICO_X.md §…`), o que é barato e não quebra
  o RAG.
- **Os casos B1 e B2 da Entrega 3 pioram com a divisão**, não melhoram: uma
  remissão do tipo "mesma política de X" que hoje atravessa 900 linhas passaria
  a atravessar um arquivo. Esses dois são pré-requisito do corte, não
  consequência dele.
- **O estágio de CONDIÇÕES precisa de uma seção `§3[?]` antes de qualquer
  divisão**, senão ele cai inteiro no `HISTORICO_*` errado ou no `SPEC_LEI`
  como um bloco de "exceção ao §0" — que é a forma que hoje o esconde.

---

# Entrega 5 — O que esta investigação NÃO consegue avaliar

## O que foi lido

SPEC.md, integral. **Nada mais foi lido.** Não abri código, não abri testes, não
abri nenhum dos ~50 relatórios de rodada citados pela SPEC
(`ESTUDO_MARGEM_20PP.md`, `CLASSIFICACAO_CONSOLIDADO.md`, `ESTABILIDADE_10_FLIPS.md`,
`MEDICAO_*`, etc.), não abri `resultado/`, não rodei nada.

**Uma exceção, declarada:** listei os nomes de arquivo de `src/espectro24/` e da
raiz do repositório (só `ls`, sem abrir nada), para confirmar que
`condicoes.py` existe — o que sustenta a afirmação de que o estágio de
CONDIÇÕES está em código e não tem seção em §3. Isso é a única afirmação deste
relatório que não sai da SPEC sozinha, e está isolada aqui.

## Consequências diretas

**Todo número "MEDIDO" citado neste relatório foi tomado da SPEC ao pé da
letra.** Não verifiquei nenhum contra a sua fonte. Isso vale inclusive para as
inconsistências da Entrega 3, seção D: eu sei que a SPEC diz 75,5% num lugar e
75,6% em outro; **não sei qual dos dois está certo.**

## INDETERMINADO PELA SPEC SOZINHA

Classificações que dependem de saber se a regra ainda é aplicada no código, e
que **não** decidi:

| # | Item | Por que é indeterminado |
|---|---|---|
| **INDET-1** | **§3[E2] Editor** — classifiquei como HIST | A SPEC diz em 4859 que foi aposentado e em 6661 que está ativo. Classifiquei pela data (v1.9.10 > v1.6.0) e pela existência do diretório `experimentos-editor-e2-arquivado/`, que vi no `ls`. **Não confirmei em `cli.py` que a chamada saiu.** Se o editor voltou em alguma versão sem entrada de changelog, minha classificação está errada. |
| **INDET-2** | **§3[D2] "Prompt fixo do narrador (texto oficial)"** (5323–5360) — classifiquei como HIST | Depende de `NARRATOR_SYSTEM_PROMPT` ter de fato saído para `experimentos-narrador-antigo-arquivado/`, como 5008 afirma. Não verifiquei. |
| **INDET-3** | **§3[C3] "Caso de borda — bucket dominante em modo reduzido"** (3760–3787) | O texto diz *"documentado agora, **implementado depois**"*. Nenhuma versão posterior diz que foi implementado. **Não sei se é LEI vigente ou especificação nunca executada.** |
| **INDET-4** | **§3[C2] "Proposta temporal"** — classifiquei como HIST/aberta | *"Não aplicada nesta versão"* é de v1.9.6. Onze versões depois, não sei se S2 foi aplicada. Se foi, o achado da Entrega 2, item 2.7, muda de natureza. |
| **INDET-5** | **§2.2 Risco 1** — faixa de `rotulo_peso` acima de ~90% | Registrada como candidato não aplicado na v1.9.0; o mapa em 5415–5422 topa em ≥70%. Se o mapa foi estendido em `quantificador.py` sem atualizar a SPEC, o item 4 do `SPEC_ABERTO` proposto está errado. |
| **INDET-6** | **`MARGEM_LIFT_PP`** | Não sei se a constante ainda existe em `config.py`. A contradição C5 é interna à SPEC e é real; **qual dos dois lados descreve o código é indeterminado**. |
| **INDET-7** | **O estágio de CONDIÇÕES** | Sei que `condicoes.py` existe (nome do arquivo). **Não sei** se ele roda dentro do pipeline, se é só um harness de publicação, qual é o contrato do briefing, quais são as validações em código, nem o schema do bloco publicado. **Nada disso está na SPEC** — que é o achado, não a limitação. |
| **INDET-8** | **Denominador do corpus (D2)** | 4.181 vs 4.056 vs 5.371 vs 2.866. Sem abrir `consenso.jsonl` / `consenso_verificado.jsonl` / `amostra.json` não há como dizer qual é o denominador correto hoje, nem se os quatro descrevem populações genuinamente diferentes. |
| **INDET-9** | **Providers e modelos (C8)** | A SPEC se contradiz. Qual configuração está em `config.py` hoje é indeterminado. |
| **INDET-10** | **A passada seletiva de §2.3** | Executada em 12 de 35 filmes na v1.9.6. Se o catálogo foi recoletado depois, o número mudou. A SPEC não diz. |
| **INDET-11** | **A distribuição do catálogo em §3[V]** (C10) | Sei que §2.5 diz 6/28/1 e §3[V] diz 17/18. **Não sei se os `resultado/*.json` no ar hoje refletem a lei por `n`** — §2.9 diz que 16 filmes foram republicados na v1.9.34, mas as medições de repetição de §3[V] (Jaccard, padrões de abertura, conectivos) foram feitas sobre os textos da v1.9.22 e não foram refeitas. |

## Duas coisas que a leitura pode ter errado por método

1. **Os pontos de virada das seções MISTAS são minha leitura, não um marcador
   do documento.** Onde a SPEC alterna lei e justificativa dentro de um mesmo
   parágrafo (comum em §0 e §3[E]), escolhi o início do parágrafo. Um corte
   real vai precisar de decisão frase a frase nesses casos.
2. **As estimativas de linha da Entrega 4 são aritmética sobre a Entrega 1**,
   não uma extração de teste. O erro provável é de ±15% em cada arquivo, e
   maior no `SPEC_LEI.md`, porque é o que mais depende da decisão
   "justificativa vai junto ou não".

## O que esta investigação deliberadamente não fez

Não decidi a reestruturação. Não propus o texto de nenhum arquivo novo. Não
apontei qual das leituras conflitantes da Entrega 3 é a correta — em todos os
casos apontei **onde as duas estão**, porque escolher entre elas é uma decisão
sobre o produto, não sobre o documento.

---

**SPEC.md sem diff.** Confirmado: nenhuma escrita nesta sessão fora deste
arquivo.
