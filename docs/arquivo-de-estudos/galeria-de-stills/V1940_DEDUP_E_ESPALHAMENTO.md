# v1.9.40 — a galeria repetia quadro: o que foi medido antes de mexer

Estudo de 2026-09-05. Cinco filmes de perfis visuais diferentes (`wonka`,
`anatomy-of-a-fall`, `dune-part-two`, `eighth-grade`, `parasite-2019`),
316 candidatas a still. **Os rótulos manuais estão ao lado**
(`pares-rotulados.json`, `arte-promocional-rotulos.json`); tudo abaixo é
derivável deles.

## ETAPA 0 — a hipótese, e o que dela se confirmou

A hipótese era que ordenar por `vote_average` desc causa os DOIS defeitos
reportados (quadro repetido em crops diferentes; arte de campanha na
galeria), porque as duas coisas concentram voto.

**Duplicata: CONFIRMADO, e com folga.** Contando à mão quantas imagens
DISTINTAS há em cada janela de 8 posições:

| janela | imagens distintas em 40 posições |
|---|---:|
| top-8 (o que a v1.9.39 publicava) | **34/40** |
| 8 do meio do pool | 39/40 |
| 8 do fim do pool | 40/40 |

Medido de outro jeito, pela taxa automática (pHash ≤ 14) de pares
duplicados por janela deslizante de 8: o top-8 tem 1 par em 3 dos 5
filmes, contra uma média de 0,00 a 0,15 par por janela no resto do
ranking — 7× a 19× a taxa de fundo. O caso extremo é o `wonka`, cujo
top-8 mostrava **5 imagens distintas em 8 posições**: 3 crops do mesmo
plano da loja e 2 crops da mesma arte de campanha.

**Arte promocional: CONFIRMADO SÓ EM PARTE, e o mecanismo não é o
suposto.** A arte é 14,9% do pool e 17,5% do top-8 — enriquecimento real
mas pequeno, e desigual (`parasite-2019` 10% → 25%; `wonka` 33% → 38%;
`anatomy-of-a-fall` 3% → 0%). A mediana de posição normalizada é 0,462
para arte contra 0,533 para quadro. **A arte não domina o topo: ela está
no acervo inteiro**, e ordenar diferente não a remove. É por isso que a
ETAPA 3 (abaixo) mede em vez de implementar.

## ETAPA 1 — pHash, e o limiar 14

Escolha entre dHash e pHash decidida por medição, não por preferência —
a matriz completa está na docstring de `src/espectro24/still_hash.py`.
Resumo: pHash domina dHash em todo ponto de precisão comparável (com
precisão 1,000, pHash chega a recall 0,660 e dHash a 0,553), porque as
duplicatas do TMDB são o mesmo quadro RE-GRADADO, e o dHash mede o
contraste local que a gradação muda.

`LIMIAR_PHASH = 14` sai da regra "o maior limiar com precisão ≥ 0,95":
P=0,951 R=0,830. O limiar seguinte (16) cai para P=0,880.

**O limite conhecido:** recall 0,830, e o que escapa tem nome — "mesmo
plano, escala e gradação muito diferentes". `wonka` #1 vs #6 (mesma cena,
plano aberto vs fechado) dá pHash=34; `anatomy-of-a-fall` #1 vs #2 dá 38.
Distâncias de par aleatório. Nenhum limiar utilizável separa isso.

## ETAPA 2 — amostragem espalhada

Substitui o top-N por "primeiro item de cada uma das 8 faixas contíguas
do ranking" (`floor(k * n / 8)`). Determinística, mantém o item 0 como o
mais votado do filme, e dá a segunda defesa que a dedup não dá: as
duplicatas que o pHash NÃO reconhece são vizinhas no ranking, e duas
vizinhas nunca caem na mesma faixa quando `n ≥ 16` (verdade nos 34
longas do catálogo).

## ETAPA 3 — arte promocional: três heurísticas, três reprovações

Não foi implementado filtro. Ver `ABERTO.md` §E3 para a tabela de
precisão/recall e a decisão que ficou com o dono. Resultado curto: a
melhor das três (saturação) erra 63% do que marca, no seu MELHOR limiar
escolhido já sabendo o rótulo, e a previsão do dono sobre falso positivo
em paleta saturada confirmou-se (`dune-part-two`: 22 dos 102 quadros
reais marcados como arte).

## Resultado no catálogo

Backfill dos 35, 2026-09-05: 2.948 candidatas, **331 colapsadas**, 2.617
distintas. Os 34 longas continuam com galeria de 8; `talk-to-me-2022`
continua vazio pelo filtro de duração, como deve.
