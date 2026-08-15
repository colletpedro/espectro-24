# Entrega 4 — pipeline num filme fora do catálogo

**Filme:** `joker-folie-a-deux` — distribuição INVERTIDA (46 / 33 / 21), o
que exercita pela primeira vez em produção a **abertura do movimento 3 pelo
bucket NEGATIVO**. Os 3 filmes do catálogo são todos aclamados (positivas
entre 90% e 96%), então esse caminho nunca tinha rodado fora de teste.

## Resultado mecânico

| | |
|---|---|
| flags | **0** |
| clichês | 0 |
| parágrafos | 4 (1 do movimento 2 + 3 do movimento 3) |
| best-of-3 | candidato #1, `melhor_entre_limpos` / critério `ritmo` |
| chamadas | 3 · `gemini-3.7-flash` |
| rede | 0 (rodou `--offline`) |

**A ordem do movimento 3 saiu certa:** `negativas` (46%) → `medianas` (33%)
→ `positivas` (21%), maior peso primeiro, como o briefing fixa. A
`marcacao_perspectiva` acompanhou (`nenhuma` / `simples` / `antecipada`) e o
texto marcou os grupos menores. Nada quebrou.

---

## Achado A — sem ficha, o texto nunca diz QUE FILME é

A narrativa abre direto no movimento 2 ("A experiência do longa-metragem se
desenvolve a partir da presença contínua de sequências musicais…"). Não há
título, diretor, ano, gênero nem premissa.

**Não é defeito do narrador — ele obedeceu.** `ficha` veio `None` com
`ficha_indisponivel: "ano_desconhecido"`, o orçamento do movimento 1 virou
`(0, 0)` (`ORCAMENTO_SEM_FICHA`) e o briefing mandou pular o movimento.

**A causa é uma interação, e ela é o achado:** o slug `joker-folie-a-deux`
não tem sufixo de ano, então a resolução cai no fallback da v1.7.0 (buscar o
ano na página do Letterboxd) — que **precisa de rede**. Sob `--offline`, o
fallback não roda, o ano fica desconhecido, e a guarda da v1.7.0 (correta)
recusa buscar a ficha sem ano, porque desambiguar por título só já causou o
defeito real do `cure`.

Resultado: **rodar offline um slug sem ano no nome produz, em silêncio, uma
narrativa sem apresentação do filme.** Os 3 filmes do catálogo não expõem
isso — `the-invite-2026` e `cats-2019` têm ano no slug, e `cure`/
`cidade-de-deus` já têm a página cacheada de execuções anteriores.

Quantos filmes do catálogo estão nessa situação: **21 dos 35 slugs não têm
sufixo de ano**. Nenhum deles vai gerar movimento 1 numa execução offline
com cache frio.

**Não corrigido** — é mudança de comportamento (fazer a ficha sobreviver ao
offline, ou avisar em vez de silenciar). Duas direções, nenhuma avaliada:
(a) persistir o ano resolvido no `meta.json` do bruto, junto do resto, na
coleta — ele é dado estável e já foi buscado uma vez;
(b) o CLI avisar explicitamente ("sem ficha: movimento 1 omitido") em vez de
deixar o JSON com um campo `ficha_indisponivel` que ninguém lê.

---

## Achado B — dois grupos, o MESMO rótulo de peso

Os dois primeiros parágrafos do movimento 3 abrem assim:

> **Em boa parte das notas (~46%)**, uma parcela expressiva argumenta que as
> canções surgem totalmente fora de lugar […]
>
> **Em boa parte das notas (~33%)**, a maior parte assinala que a execução
> das faixas musicais soa desconexa […]

46% e 33% caem os dois na faixa `boa parte` (30–50%) de `_rotulo_peso`. O
leitor vê a mesma expressão duas vezes seguidas e só distingue os grupos
pelo número entre parênteses — que é exatamente o que o rótulo verbal existe
para não exigir.

**Não é bug: é a largura das faixas.** E não é raro — medido sobre o
histograma dos **35 filmes** do catálogo:

> **23 de 35 filmes (66%) têm pelo menos dois grupos com o mesmo rótulo de
> peso.**

| padrão | filmes | exemplo |
|---|---|---|
| `negativas` + `medianas` = "uma fração mínima" | 21 | `cure` (2/8/90), `cidade-de-deus` (1/3/96) |
| `negativas` + `medianas` = "boa parte" | 1 | `friday-the-13th-2009` (33/41/26) |
| `medianas` + `positivas` = "uma fração mínima" | 1 | `cats-2019` (86/7/7) |

O caso dominante é o filme aclamado: com `positivas` acima de 80%, os outros
dois grupos caem ambos abaixo de 15% e recebem "uma fração mínima das
notas". **Isso já vale para os 3 filmes do catálogo sob as fronteiras C** —
está no JSON gerado nesta sessão, e vai aparecer no texto publicado.

**Não corrigido** — é mudança de comportamento no rótulo, que é invariante
publicada e literal. Direções possíveis, nenhuma avaliada:
(a) mais faixas (as atuais são 5 para 0–100%, e as duas pontas são largas);
(b) o rótulo do grupo MENOR ganhar um comparativo quando colide com o do
grupo vizinho ("uma fração ainda menor"), o que exige que o código compare
grupos — hoje `_rotulo_peso` só vê um percentual por vez;
(c) aceitar e declarar: o percentual entre parênteses já desambigua.

A opção (c) é a que está valendo hoje, por omissão. Vale uma decisão
explícita antes de republicar.
