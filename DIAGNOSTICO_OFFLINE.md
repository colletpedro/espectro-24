# Reprodutibilidade offline — diagnóstico (Entrega 3, v1.9.12)

**Sem implementação.** A correção toca a camada de coleta e/ou a de seleção;
o pedido foi diagnosticar, recomendar, e parar se for mudança de
comportamento. É.

## A promessa que está sendo furada

§3[B'] existe para que "qualquer reprocessamento custe zero rede" — o
superset é persistido justamente para que mudar análise não custe recoleta.
A arquitetura de quatro sessões de coleta se apoia nisso.

Medido na v1.9.11: `the-invite-2026` **não rodou** `--offline`. Pediu
`rated_2_5_page_5.html`, que nunca tinha sido buscada.

## A causa, em uma frase

**O bruto guarda as REVIEWS, mas não guarda quais POSIÇÕES foram buscadas —
e a escolha de posições é recomputada, do zero, a cada execução.**

O `meta.json` grava **quantas** páginas cada nível gastou
(`paginas_gastas_por_nivel`, `paginas_base_por_nivel`), nunca **quais**. A
cada execução, `collect_all_levels` recalcula o conjunto a partir de três
entradas, e nenhuma delas está fixada pelo bruto:

| entrada | de onde vem | por que muda |
|---|---|---|
| orçamento por nível | alocação sobre o **histograma** | o histograma muda: são notas novas todo dia |
| profundidade estimada | **sondagem** de rede (~4 req.) | o filme ganha páginas com o tempo |
| posições dentro do orçamento | `posicoes_profundas` | **mudou de estratégia**: v1.9.2 geométrica → v1.9.5 frações da profundidade real |

Para `the-invite-2026`/2.5★, a estratégia de hoje pede `[1,2,3,4,5,8]`; o
cache tinha `[1,2,3,4,6,8]` — construído sob a estratégia anterior. Uma
posição de diferença basta para abortar o filme inteiro.

## Quantos filmes têm o problema hoje

Simulação sobre os 35 filmes do catálogo: para cada nível, computei o
conjunto de posições que o código ATUAL pediria (usando o orçamento e a
profundidade **gravados** no `meta.json`) e conferi contra o cache em disco.

> **34 de 35 rodariam offline hoje. 1 falharia: `obsession-2026`** (14
> posições ausentes, ex. `1.0★p3`, `2.0★p3-p6`, `2.5★p3`).

**Este número está viciado para baixo, e o viés é meu:** `the-invite-2026`
falhava no início desta sessão e passou a constar como "rodaria" porque a
execução online da v1.9.11 **cicatrizou o cache dele**. O número honesto é
"1 falha conhecida hoje, mais as que a próxima mudança de estratégia
criar" — a taxa observada de falha é **2 filmes em 2 mudanças de
estratégia**, não 1 em 35.

E há um viés estrutural que a simulação não alcança: ela usa o orçamento
GRAVADO. Uma execução real recomputa o orçamento a partir do histograma
que estiver no cache naquele momento — se alguém rodar online e o
histograma tiver mudado, o conjunto de posições muda junto, sem nenhuma
alteração de código.

## O dado necessário JÁ EXISTE — no lugar errado

`reviews.jsonl` grava `pagina_origem` por review. Para `the-invite-2026`/
2.5★, o conjunto de páginas presente no bruto é `[1,2,3,4,5,6,8]` — que é
exatamente o conjunto em cache. **O bruto já sabe quais posições foram
buscadas**; só não sabe de forma direta (é preciso reduzir sobre as
reviews) e perde as páginas que voltaram vazias.

## As duas direções, avaliadas

### (i) A seleção consome o bruto sem recomputar posição

*"Posicionamento é decisão de COLETA, não de seleção."* Correto como
princípio — e a seleção **já** faz isso: `run_pipeline` chama
`carregar(slug)` e seleciona sobre o bruto inteiro. **Não é a seleção que
pede páginas; é a coleta, que roda antes dela em todo caminho.**

O que falta é um modo "só análise" que pule a coleta inteira quando o bruto
já basta. Hoje não existe: `--offline` faz a coleta rodar servindo do
cache, não deixar de rodar.

**Custo:** baixo e contido — é um caminho novo no `cli.py`/`pipeline.py`,
sem tocar em nada existente. **Não corrige** o caso de quem quer recoletar
de fato; só separa "analisar de novo" de "coletar de novo", que hoje estão
grudados.

### (ii) O bruto registra as posições buscadas, e o offline as honra

Gravar `posicoes_por_nivel` no `meta.json` (o conjunto efetivamente
buscado, incluindo as que voltaram vazias) e, em modo offline, **usar esse
conjunto em vez de recomputar**.

**Custo:** um campo novo no meta + um ramo em `raspar_nivel`. **Corrige a
causa raiz** — o conjunto deixa de ser derivado de entradas voláteis e
passa a ser dado do superset, exatamente como `ordenacao_usada`
(v1.9.0) já é. Precisa de backfill (recuperável de `pagina_origem`, com a
ressalva das páginas vazias).

## Recomendação

**As duas, nesta ordem — mas (ii) é a que fecha o buraco.**

(ii) primeiro, porque é a que restaura a promessa de §3[B'] e porque o
precedente já existe no projeto: a v1.9.0 tornou a ORDENAÇÃO um dado
gravado exatamente porque servir cache de outra amostragem seria "um erro
silencioso, do tipo que só apareceria como 'a coleta nova saiu igual à
velha'". Posição é a mesma classe de coisa que ordenação: parâmetro de
amostragem que precisa viajar com o material.

(i) depois, como conveniência — um `--so-analise` que nem tenta coletar
torna o reprocessamento explícito em vez de dependente de o cache estar
completo.

**Ressalva para (ii), a registrar antes de implementar:** honrar as
posições gravadas congela a amostra. Um filme coletado com orçamento 6 nunca
mais aproveitaria orçamento 16 sem uma recoleta explícita — o que é o
comportamento CORRETO para reprocessar, e o errado para estender. Os dois
precisam de nomes diferentes na CLI, e essa é a decisão de desenho que falta.

**Não implementado nesta sessão.** (ii) muda o que a coleta grava e como o
modo offline se comporta; (i) acrescenta um modo de execução. Ambos são
mudança de comportamento.
