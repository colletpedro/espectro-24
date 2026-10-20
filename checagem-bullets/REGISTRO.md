# Checagem de apoio dos bullets — publicado (DeepSeek) × local (qwen3:14b)

**Pergunta.** Cada bullet da síntese afirma que um tema aparece nas reviews de
um grupo. Ele tem apoio nas reviews DAQUELE grupo (as mesmas 40 que alimentaram
a síntese) ou foi inventado/inflado? Só os bullets: no publicado são do
DeepSeek. Nenhuma chamada paga. Código: `scripts/checagem_bullets.py` e
`scripts/encoder_e5.py` (em `main`, `bec03e4`).

5 filmes: anatomy-of-a-fall, incendies, mother-2017, napoleon-2023,
the-substance. 90 bullets por lado, 600 reviews (40 × 3 grupos × 5), a mesma
seleção nos dois lados.

## Estado (2026-10-19)

| parte | estado | arquivos |
|---|---|---|
| 1a — eixo no consenso (sem modelo) | **feita** | `parte1_eixo.{json,md}` |
| 1b — recuperação por embedding local | **feita** | `parte1_recuperacao.{json,md}` |
| 2 — juiz qwen3:14b | **entrada pronta; falta rodar no Windows** (`docs/SETUP_WINDOWS.md` §10) | `juiz_entrada.jsonl`, `juiz_estimativa.md` → `juiz_saida.jsonl` |
| 3 — validação do juiz | **documento pronto; falta o rótulo do dono** | `rotulagem/rotulagem_dono.md`, `rotulagem/rotulos_dono.csv`, `mapa/rotulagem_mapa.json` |
| resultado final | depois de 2 e 3 | `validar-juiz` → `relatorio` |

## Parte 1a — o que saiu

| lado | bullets | sem eixo (livre) | suspeitos (eixo em ≤ 1 review) | declarado > reviews com o eixo |
|---|---|---|---|---|
| publicado | 90 | 3 | **0** | 21 |
| local | 90 | 2 | **0** | 14 |

A contagem foi refeita do consenso (`consenso_verificado.jsonl`, restrito à
amostra analisada) e conferida contra o bloco `eixos` publicado em 300 células,
sem divergência.

**A medida grosseira não separa os lados e não pega os bullets que a leitura
humana apontou.** "atuações insuficientes" (local, negativas de Anatomia) cai
em `atuacao`, que aparece em 14/40 reviews; "direção e estética visual fraca"
cai em `direcao_imagem`, 7/40. O eixo junta elogio e crítica do mesmo assunto,
então "tem o eixo" não diz "diz o tema". É o resultado esperado de uma régua
larga, registrado como tal: ela só flagraria um bullet sobre assunto que
ninguém no grupo menciona, e nenhum dos 180 é assim.

## Parte 1b — o que saiu

Modelo: `intfloat/multilingual-e5-base`, local, forward em numpy; justificativa
em `scripts/encoder_e5.py` (recuperação assimétrica, translíngue, já no disco).
Reviews em janelas de até 900 caracteres (691 pedaços, nenhum truncado).

**Centralização, medida antes de adotada.** Sem centrar, poucas reviews
genéricas na língua das queries dominavam o top-5 (156 reviews distintas em
435 posições do lado publicado). Sinal independente do embedding: a fração do
top-5 que tem o eixo do bullet, contra a fração do grupo (o acaso):

| variante | publicado | local |
|---|---|---|
| sem centrar, query = tema + descrição | 54,7% (lift 1,27) | 57,3% (1,24) |
| sem centrar, query = só o tema | 54,5% (1,26) | 58,2% (1,26) |
| centrado nos 180 bullets dos dois lados | 69,2% (1,61) | 67,7% (1,47) |
| **centrado nos 1.780 bullets publicados do catálogo (adotada)** | **68,0% (1,58)** | **64,8% (1,40)** |
| acaso | 43,1% | 46,1% |

Ficou a referência do catálogo: quase o mesmo ganho, e não muda quando o modelo
avaliado muda (é a régua do fine-tuning). O eixo é polaridade-cego, então isto
compara variantes; não diz que a recuperação acerta. Exemplo do efeito: em
"Mistura de idiomas incomoda" (publicado), o top-5 passou de reviews genéricas
em português para quatro reclamações reais da mistura francês/inglês.

O que a recuperação já mostra, sem juiz: para "atuações insuficientes" as
reviews mais parecidas dizem *"Great acting"* e *"acting was decent"* — o
assunto certo, com o juízo oposto. É o caso que o critério do juiz manda
responder **não**.

## Parte 2 — preparada

900 chamadas (450 por lado), uma por par bullet × review, resposta
`{"menciona": bool}` forçada por schema, `think=false`, sequencial e retomável.
**~89 min estimados (faixa 67–179)**, a partir das velocidades do qwen3:14b
medidas no gate deste notebook — estimativa, não medição.

## Parte 3 — preparada

40 pares sorteados (semente 20261019): 20 por lado, 4 por filme por lado,
metade dos ranks 1-2 e metade dos 3-5, no máximo um par por bullet, ordem
embaralhada. O documento não mostra lado, modelo, similaridade, rank nem
resposta do juiz; o mapa fica em `mapa/` com selo sha256 impresso no rodapé
do documento (`bc592ee9…`).

**Critério para o juiz valer, fixado antes do rótulo** (proposta do código,
`CRITERIO_JUIZ`): precisão ≥ 0,8 **e** recall ≥ 0,8 nos 40 pares. Se o dono
quiser outro, trocar ANTES de rotular. Reprovado o juiz, `relatorio` gera os
números com o aviso "ESTE RESULTADO NÃO VALE" no topo.

## Limites conhecidos

- O apoio do juiz tem **teto de 5** (5 reviews por bullet): um bullet que
  declara 25 menções não pode mostrar mais que 5. O quantificador ("muitas",
  "várias") é comparado contra esse teto, não contra a contagem real.
- O juiz é o mesmo modelo que escreveu um dos lados (qwen3:14b). A validação da
  Parte 3 mede o erro dele nos dois lados separadamente para isso aparecer.
- A recuperação pode deixar de fora a review que sustenta o bullet; "sem apoio"
  quer dizer "sem apoio nas 5 mais parecidas".

## Rotulagem do dono (2026-10-19)

40 pares rotulados em `rotulagem/rotulos_dono.csv`: 25 `sim`, 15 `não`.

**Pares que o dono considerou duvidosos** (o rótulo não muda; registro para
ler a validação com cuidado): P03, P09, P11, P13, P15, P22, P28, P34, P36, P39.

## Validação do juiz e resultado (2026-10-19)

**O juiz REPROVOU: o resultado da Parte 2 NÃO VALE.** Precisão 0,727
[IC95 0,558–0,849], recall 0,96 [0,805–0,993] nos 40 pares (critério: ambos
≥ 0,8). Por lado: publicado P 0,812 / R 0,929; local P 0,647 / R 1,0. O erro
é de um lado só — o juiz diz "menciona" demais (9 falsos positivos, 1 falso
negativo), e mais no lado local (6 FP) que no publicado (3 FP).

7 dos 10 erros caem em pares que o dono marcou como duvidosos; isso não muda
o veredito, que foi fixado antes do rótulo.

O juiz rodou 900/900 pares, todos `finish_reason: stop`, ~65 min de parede
(latência mediana 4,2 s), dentro da faixa estimada (67–179 min).

Os números de apoio em `resultado_final.md` existem só para auditoria. Com o
juiz complacente, eles são um TETO: os 2 bullets sem apoio nenhum (os dois do
lado local, ambos nas negativas de Anatomia, os mesmos apontados na leitura
humana) seguem sem apoio mesmo com um juiz que tende a dizer sim.

## Juiz v2 (2026-10-19) — calibrado; **v2.2 CONGELADA** (2026-10-20)

Código: `scripts/juiz_bullets_v2.py` (em `main`, `e04937e` + `c9bb711`). O v1 e a saída
dele ficam como estão (verificáveis pelo hash do prompt).

**O que muda.**
- **Modelo:** `gpt-oss:20b`, think=low — não escreveu nenhum dos lados. Seed
  fixa (20261019), temperatura do modelo, `num_predict` 1024 (no gate do
  gpt-oss o máximo de saída foi 696).
- **Contexto: `num_ctx` 3584.** O maior par dos 900
  (`local|the-substance|positivas|0|viewing:1439489161`, review de 4.990
  caracteres, prompt inteiro de 7.100) dá no máximo 2.485 tokens pela cota
  conservadora de 0,35 token/caractere (no gate do gpt-oss a razão nunca passou
  de 0,343 em 417 prompts); + 1024 de saída = 3.509 → o menor múltiplo de 512
  que cabe é 3584. **É cota, não medição:** `medir-contexto` conta no servidor
  os 10 prompts mais longos antes de o juiz rodar, e o juiz se recusa sem essa
  medição dizer que cabe. Cada chamada ainda tem uma guarda de estouro.
- **Frase de prova:** o modelo devolve `{"trecho": a frase inteira | null,
  "apoia": bool}` — o prompt pede a FRASE INTEIRA da review onde está a prova,
  não um fragmento. O código decide: apoio = apoia E trecho não-nulo E trecho
  com **ao menos 4 palavras** E trecho achado na review (normalizando só
  espaços, caixa e forma Unicode — sem tirar acento nem trocar aspas).
  Recalculado na leitura, não confiado ao registro; sem apoio, o motivo fica
  gravado (modelo disse que não / trecho nulo / trecho curto / não encontrado).
- **Por que o mínimo de 4 palavras** (decisão do dono, 2026-10-19, antes de
  qualquer dado do v2 — por isso é a própria v2.0, não um ajuste): uma palavra
  só esvazia a prova. "acting" existe em "Great acting", e o código aceitaria
  como apoio a "atuações insuficientes".
- **Critério = o guia do dono** (`CRITERIO_DONO`, no prompt inteiro).

**Configuração v2.0:** `config_sha256` =
`a42f48932713ff322535116cb17538bc51a14bdb5e49c9c8389c35b687461c22`
(substitui o `30f966ae…` do primeiro preparo, anterior à regra das 4
palavras; nenhum dado rodou com ele)
(prompt, modelo, parâmetros e o fonte da regra; detalhe em
`juiz_v2/config_v2.0.json`). Este hash é da versão em calibração, **não** o da
versão congelada.

**Calibração (a).** Os 40 pares do rótulo antigo, só para ajustar o prompt —
no máximo 2 ajustes (v2.1, v2.2), cada versão com o seu arquivo e o seu
resultado aqui. O relatório (`juiz_v2/calibracao_<versão>.md`) se declara
CALIBRAÇÃO, NÃO VALIDAÇÃO. Estimativa: ~10 min (p95 ~19) para os 40,
`juiz_v2/preparo_v2.0.md`. Comando: `docs/SETUP_WINDOWS.md` §11.

**Ainda NÃO feitos** (próximas sessões, nesta ordem): (b) congelar a versão e
gravar o hash dela aqui; (c) pré-registrar aqui o critério — precisão ≥ 0,8 e
recall ≥ 0,8, e diferença de precisão entre os lados ≤ 0,15 (é o que
`CRITERIO_V2` já aplica na calibração, como proposta); (d) amostra nova de 40
pares sem sobreposição com os antigos; (e) os 900 pares (o código recusa sem a
versão congelada); (f) validação só na amostra nova.

| versão | config_sha256 | calibração (40 pares antigos) |
|---|---|---|
| v2.0 | `a42f4893…` | P 0,85 [0,64–0,95] · R 0,68 [0,48–0,83] · dif. lados 0,131 — reprovaria no recall (`juiz_v2/calibracao_v2.0.md`) |
| v2.1 | `75b5533f…` | P 0,909 [0,72–0,98] · R 0,80 [0,61–0,91] · dif. lados 0,167 — reprovaria na diferença entre os lados (`juiz_v2/calibracao_v2.1.md`) |
| v2.2 | `44606cf1…` | P 0,821 [0,64–0,92] · R 0,92 [0,75–0,98] · dif. lados 0,046 — passaria; **congelada** (`juiz_v2/calibracao_v2.2.md`) |

### v2.0 — resultado da calibração

17 VP, 3 FP, 8 FN, 12 VN (v1: 24, 9, 1, 6). Por lado: publicado P 0,909 /
R 0,714; local P 0,778 / R 0,636. A v2.0 trocou falso positivo por falso
negativo. O código derrubou 3 "sim" do modelo, todos por trecho não
encontrado: P08 (cópia com "j’ai carrément" omitido — derrubada certa pela
regra, mas custou um VP), P13 (partes distantes coladas com "…" — acerto do
código, evitou um FP) e P28 (cópia fiel com hífen U+2011 no lugar de "-" —
erro da normalização).

### v2.1 — o 1º ajuste (2026-10-19), uma correção por causa de erro

**Configuração v2.1:** `config_sha256` =
`75b5533f685bc37549a9c7751b7cb5ed3d777bc742dc5d832b6728be995b86b2`
(`juiz_v2/config_v2.1.json`; código em `main`, `9b84104`). Hash da versão em
calibração, **não** o da versão congelada.

1. **Literalidade (prompt).** 5 dos 8 FN da v2.0 (P01, P11, P17, P29, P40;
   talvez P33) foram o modelo exigindo menção explícita ou a parte lateral do
   bullet, contra o critério do dono. O prompt passa a dizer, com destaque: o
   NÚCLEO é o título, a descrição é contexto e não exigência; apoio implícito
   conta se inequívoco (elogiar a protagonista é elogiar a atuação; reclamar do
   excesso de vida pessoal sustenta "foco excessivo no relacionamento"); título
   com duas ideias: basta apoiar a principal. Os exemplos são de filmes FORA
   dos 40 pares (um teste confere que nenhum nome dos 5 filmes da calibração
   aparece no prompt). O `CRITERIO_DONO` segue inteiro e sem mudança.
2. **Normalização do trecho (código, não é ajuste de critério).** P28 caiu por
   um hífen U+2011 numa cópia fiel. A comparação da v2.1 usa NFKC e une
   hífens e travessões ("-"), aspas ('"'), apóstrofos ("'") e espaços
   especiais (os de largura zero somem). Continua NÃO contando: trecho com "…"
   ou partes distantes coladas (P13), cópia com palavra omitida (P08), sem
   acento. O prompt reforça: copiar sem omitir nem alterar nada, sem
   reticências. Com a regra nova, dos trechos da v2.0 só o de P28 muda (passa a
   ser encontrado).
3. **"Na dúvida, não" imposto pelo código.** P15: o raciocínio dizia
   "ambíguo" e o modelo respondeu sim. O JSON do juiz ganha o booleano
   `"ambiguo"`; apoio = apoia E não ambíguo E trecho válido (≥ 4 palavras,
   encontrado). Sem apoio por isso, o motivo é "modelo disse que é ambíguo".

**Janela:** o prompt da v2.1 é mais longo (maior par: 8.737 caracteres, cota
3.058 + 1024 = 4.082) → `num_ctx` 4096 (a v2.0 segue 3584). `medir-contexto`
roda de novo para a v2.1 antes do juiz.

**A v2.0 continua verificável:** prompt, schema, janela e regra são por versão
no código, a v2.0 mantém o hash `a42f4893…` (um teste fixa) e a calibração da
v2.1 sai ao lado do v1 e da v2.0.

Depois da v2.1 sobra **um** ajuste (v2.2). Se a v2.1 ficar boa o bastante,
congelar em vez de gastá-lo.

### v2.1 — resultado da calibração

20 VP, 2 FP, 5 FN, 13 VN. Por lado: publicado P 0,833 / **R 0,714**; local
P 1,0 / R 0,909. Corrigiu da v2.0: P01, P08, P33 (FN) e P04, P15 (FP). Erro
novo: P09 (FP, publicado, duvidoso). Sobraram: P09, P34 (FP, publicado,
ambos duvidosos), P11, P17, P29, P40 (FN, publicado) e P28 (FN, local).
O código não derrubou nenhum "sim"; `ambiguo` foi false nos 40, inclusive em
P17 e P28, cujo raciocínio diz "it's ambiguous". Em P11, P28 e P40 o
raciocínio contraria o prompt (exige as duas ideias do título, ou a menção
explícita a Josefina).

### v2.2 — o 2º e último ajuste (2026-10-19): estrutural

**Configuração v2.2:** `config_sha256` =
`44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669`
(`juiz_v2/config_v2.2.json`; código em `main`, `f95d7fa`). Hash da versão em
calibração, **não** o da versão congelada.

**Por quê.** A v2.1 erra quase só no lado PUBLICADO (recall 0,714 × 0,909 no
local). Um juiz que nega apoio a bullets bons do publicado favorece o modelo
local — o defeito que mais importa numa régua para avaliar o fine-tuning. Os
erros vêm do modelo não obedecer a instruções em texto; por isso as mudanças
são estruturais, não mais prosa:

1. **O juiz vê só o TÍTULO do bullet**, sem a descrição (a v2.1 seguiu
   cobrando a descrição, P29). O `CRITERIO_DONO` segue no prompt, inteiro.
2. **O campo de decisão é `"apoia_ideia_principal"`**: a review sustenta a
   ideia principal do título — em título com duas ideias, a primeira? Sai o
   `"apoia"` genérico.
3. **Polaridade invertida:** sai `"ambiguo"`, entra `"evidencia_clara"`, que
   precisa ser AFIRMADA verdadeira. Apoio = `apoia_ideia_principal` E
   `evidencia_clara` E trecho válido (≥ 4 palavras, encontrado com a
   normalização da v2.1).

O resto é o da v2.1: modelo, frase inteira, normalização, exemplos de filmes
fora dos 40 pares, contexto medido antes (maior par: 8.424 caracteres, cota
2.949 + 1024 = 3.973 → `num_ctx` 4096).

### Regra de escolha entre v2.1 e v2.2 — PRÉ-REGISTRADA (2026-10-19, antes de a v2.2 rodar)

- Se a v2.2 passar nos **três** critérios na calibração (precisão ≥ 0,8,
  recall ≥ 0,8, diferença de precisão entre os lados ≤ 0,15) → **congela a
  v2.2**.
- Senão → congela a versão (v2.1 ou v2.2) com o **maior "recall no pior
  lado"** (o menor dos dois recalls por lado) — o critério que mede justamente
  o defeito atual. Referência da v2.1: **0,714** (publicado).
- **Empate → v2.1.**

A versão congelada é a que vai para os 40 pares novos e para os 900. Os 40
pares novos não são tocados por nenhuma das duas versões antes da escolha.
A regra está no código (`escolha_pre_registrada`, com teste) e o relatório
da v2.2 diz qual versão ela escolhe. Não há ajuste depois da v2.2.

### v2.2 — resultado da calibração (2026-10-20)

23 VP, 5 FP, 2 FN, 10 VN. Por lado: publicado P **0,80** / R 0,857; local
P 0,846 / R 1,0. Diferença de precisão entre os lados 0,046. Corrigiu da
v2.1: P11, P17, P28 (FN). Erros novos: P04, P15 (FP que a v2.0 já tinha e a
v2.1 corrigira) e P36 (FP). Sobraram: P04, P09, P15, P34, P36 (FP) e P29, P40
(FN). O código não derrubou nenhum "sim". Em P28 a cópia trouxe de novo o
hífen U+2011 e a normalização da v2.1 a encontrou (a da v2.0 não).

## CONGELAMENTO — juiz v2.2 (2026-10-20, antes de qualquer rotulagem nova)

**Versão congelada: v2.2.** `config_sha256` =
**`44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669`**
(`CONGELADA = "v2.2"` em `main`, `c489630`; um teste fixa o hash).

**Por quê:** a regra pré-registrada acima — a v2.2 passou nos três critérios
da calibração (precisão 0,821 ≥ 0,8; recall 0,92 ≥ 0,8; diferença de precisão
entre os lados 0,046 ≤ 0,15). Não houve escolha pelo resultado: a regra foi
gravada antes de a v2.2 rodar, e não há ajuste depois dela.

**Registrado junto do congelamento, para ler a validação:**
- **`evidencia_clara` é DECORATIVO, não é uma segunda trava.** Nos 40 pares
  ele nunca divergiu de `apoia_ideia_principal` (28 vezes os dois
  verdadeiros, 12 os dois falsos); em P17 o raciocínio diz "unclear… Could
  support" e o campo veio verdadeiro — a mesma falha do `ambiguo` da v2.1. A
  melhora da v2.2 veio de mostrar só o título e de perguntar pela ideia
  principal. Na prática o juiz decide por `apoia_ideia_principal` e pela
  frase de prova (≥ 4 palavras, achada na review).
- **A precisão do lado publicado ficou em 0,80 exato** na calibração, e 4 dos
  5 FP (P09, P15, P34, P36) estão em pares que o dono marcou como duvidosos.
  O resultado da validação vale qualquer que seja.
- **O viés restante aponta para o mesmo lado:** recall do local 1,0 contra
  0,857 no publicado — o juiz ainda nega mais apoio a bullets bons do
  publicado, o que favorece o modelo local.
- Calibração não é validação: os 40 pares acima ajustaram o prompt e o
  número deles é otimista por construção.

**Critério da validação — o pré-registrado, sem nenhuma mudança:** precisão
≥ 0,8, recall ≥ 0,8 e diferença de precisão entre os lados ≤ 0,15
(`CRITERIO_V2`), nos 40 pares NOVOS, contra o rótulo novo do dono. Reprovado,
a validação e o relatório de fidelidade dizem "ESTE RESULTADO NÃO VALE" na
primeira linha.

**O que vem, nesta ordem:** (1) amostra nova de 40 pares, sorteada depois
deste registro; (2) o dono rotula; (3) o Windows roda a v2.2 nos 900
(`docs/SETUP_WINDOWS.md` §12); (4) `validar`, SÓ nos 40 novos; (5)
`relatorio` (`juiz_v2/fidelidade_v2.2.md`).

## Amostra nova da validação (2026-10-20, depois do congelamento)

40 pares sorteados dos 900 por `amostra-validacao`, semente 20261020 (a da
calibração foi 20261019): **nenhum** dos 40 da calibração, 20 por lado, 4 por
filme em cada lado, metade dos ranks 1-2 e metade dos 3-5, um par por bullet.
Documento cego para o dono: `rotulagem_validacao/rotulagem_dono.md` (sem lado,
modelo, similaridade, rank nem resposta de juiz; o critério impresso é o guia
do dono, `CRITERIO_DONO`), respostas em `rotulagem_validacao/rotulos_dono.csv`.
O mapa (que diz o lado) fica em `mapa/validacao_mapa.json`, selo
`5fad9a3000cb45c053f33958199b2bfc74826deb730a5dbf32925aa9ec0edfca`.

## Rotulagem do dono — validação (2026-10-20)

40 pares rotulados em `rotulagem_validacao/rotulos_dono.csv`: 25 `sim`, 15
`não`. Rotulagem cega, feita no chat a partir do documento
`rotulagem_validacao/rotulagem_dono.md`, sem acesso ao mapa nem à saída do
juiz (a saída dos 900 já estava no branch, mas não foi aberta antes do rótulo
gravado).

**Pares que o dono considerou duvidosos** (o rótulo não muda; registro para
ler a validação com cuidado): P01, P04, P08, P18, P33, P36.

## VALIDAÇÃO do juiz v2.2 congelado (2026-10-20) — **PASSOU**

Os 900 pares rodaram no Windows com a v2.2 congelada (`juiz_v2/saida_v2.2.jsonl`,
900/900 `ok`, todos com `config_sha256` `44606cf1…`). Validação SÓ nos 40 pares
novos, contra o rótulo do dono, com o critério pré-registrado sem mudança
(`juiz_v2/validacao_v2.2.md`):

| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] |
|---|---|---|---|---|---|---|---|
| todos | 40 | 23 | 4 | 2 | 11 | 0,852 [0,675–0,941] | 0,92 [0,75–0,978] |
| publicado | 20 | 12 | 2 | 1 | 5 | 0,857 [0,601–0,96] | 0,923 [0,667–0,986] |
| local | 20 | 11 | 2 | 1 | 6 | 0,846 [0,578–0,957] | 0,917 [0,646–0,985] |

Diferença de precisão entre os lados: **0,011** (≤ 0,15). Erros: P05, P14, P20,
P32 (FP) e P09, P40 (FN); P09 caiu pelo código (a cópia colou duas frases da
review com vírgula — trecho não encontrado). Os 6 duvidosos do dono (P01, P04,
P08, P18, P33, P36): o juiz concordou com o rótulo nos 6.

**Sensibilidade** (`juiz_v2/sensibilidade_v2.2.md`), pedida depois do rótulo e
**sem mudar o veredito**: sem os 3 pares cuja review já estava na calibração
(P18, P26, P30), P 0,833 / R 0,909 (n = 37), diferença entre os lados 0,057;
bootstrap por review (34 reviews, 10 mil reamostras) P [0,677–1,0], R
[0,792–1,0]; 6 reviews aparecem em 2 pares da validação e 3 em pares das duas
amostras — rótulo e juiz coerentes em todas, exceto a review de P05/P20, em
que o juiz diz sim às duas e o dono não.

**Fidelidade dos bullets** com o juiz validado (`juiz_v2/fidelidade_v2.2.md`):
apoio ≥ 1 em 98% dos bullets do publicado e 93% do local; apoio ≥ 2 em 83% e
82%; sem apoio nenhum: 2 bullets do publicado, 6 do local (3 deles nas
negativas de Anatomia).
