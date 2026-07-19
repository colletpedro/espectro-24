# Espectro 24 — Bateria de aceite final da v1 (§5)

**Data:** 2026-07-19 · **Spec:** v1.1.3 · **Runner:** `scripts/run_acceptance.py` (pipeline de produção + wrapper de contagem/espaçamento no cliente Gemini).

Este relatório é **factual**: verifica mecânica do pipeline contra a §5. **Não** avalia qualidade dos temas, plausibilidade das frequências nem vazamento de spoiler — esse juízo é humano (fora deste documento).

## Orçamento consumido (sessão)

| Recurso | Gasto | Teto | Detalhe |
|---|---|---|---|
| Letterboxd | **90** | 160 | cidade-de-deus 68 · buscas 3 · sondagens 4 · filme minúsculo 15 |
| Gemini | **3** | 12 | cidade-de-deus 3 (1/bucket, sem retentativa) · minúsculo 0 (todos sem_analise) |

Delay ≥2s e sem paralelismo em toda coleta Letterboxd. Nenhum 403. `.env` nunca lido/impresso. Suíte de testes: **74/74 passando** após o bump v1.1.3.

---

## Critério §5.2 — cidade-de-deus (fanbase "review curta")

**Slug:** `cidade-de-deus` · coleta 100% de rede (68 req, 0 cache) · 3 buckets todos `modo=completo` (50/20/30).

### Metadados de coleta por nível

| Nível | n_validas | n_brutas | filtro_aplicado | curtas-desc | páginas |
|---|---|---|---|---|---|
| 0.5★ | 10 | 24 | 150 | 10 | 2 |
| 1.0★ | 10 | 12 | 150 | 0 | 1 |
| 1.5★ | 10 | 24 | 150 | 10 | 2 |
| 2.0★ | 10 | 24 | 150 | 5 | 2 |
| 2.5★ | 10 | 24 | 150 | 7 | 2 |
| 3.0★ | 10 | 24 | 150 | 11 | 2 |
| 3.5★ | 10 | 24 | 150 | 7 | 2 |
| 4.0★ | 10 | 24 | 150 | 11 | 2 |
| 4.5★ | 10 | 24 | 150 | 4 | 2 |
| 5.0★ | 10 | 24 | 150 | 11 | 2 |

### Veredito por item (§5.2 / Tarefa 1.2)

**a. Cascata de relaxamento POR NÍVEL — ⚠️ NÃO ATIVOU (achado).** Todos os 10 níveis fecharam com **10 válidas no filtro padrão (150 chars)**; **zero níveis abaixo de 10 válidas**; `filtro_aplicado=150` em todos. A **relaxação** (150→50→0) só dispara quando um nível teria **0** válidas em 150 (§C.3) — nunca ocorreu. O fenômeno "review curta" É real e visível: **~76 reviews curtas descartadas** no total (coluna curtas-desc), mas o filme é popular o suficiente para ter ≥10 reviews acima de 150 chars em cada nível, dentro de ≤2 páginas. **Conclusão:** `cidade-de-deus` exercita o *filtro de comprimento* fortemente, mas **não** a *cascata de relaxamento* nem o *modo reduzido* — é coberto demais por nível para degradar. (A relaxação é, na prática, exercitada pelo filme minúsculo do §5.3 abaixo, onde `filtro_aplicado` assume 50 e 0.)

**b. Avisos de modo reduzido — não apareceram (consequência de (a)).** Como todos os buckets ficaram `completo`, nenhum aviso de "modo reduzido" foi renderizado — não havia degradação a avisar. O render de modo reduzido está implementado (`render.py`), mas este filme não o aciona.

**c. Síntese rodou e a `observacao_geral` respeita o escopo — ✅.** 3 chamadas Gemini (1/bucket, sem retentativa de validação). Flags `idioma_invalido=false`, `escopo_suspeito=false`, `aspas_removidas=0` em todos os buckets. As três `observacao_geral` referem-se ao **grupo**, não ao filme em termos absolutos: *"As reviews negativas apontam..."*, *"As reviews medianas de 3 a 3.5 estrelas apontam..."*, *"As reviews positivas apontam..."* — o preâmbulo de papel (v1.1.2) fez efeito.

**Veredito §5.2:** análise útil e escopo correto ✅; porém a *cascata de relaxamento* e os *avisos de modo reduzido* **não foram demonstrados por este filme** (coberto demais). O mecanismo em si é exercitado no §5.3.

### Output literal do terminal (cidade-de-deus)

```
═══ Espectro 24 — cidade-de-deus (spec v1.1.3) ═══

▸ NEGATIVAS  50/50 válidas [0.5★: 10 · 1.0★: 10 · 1.5★: 10 · 2.0★: 10 · 2.5★: 10]  modo=completo
  filtro aplicado (chars): [150]
    • Estetização e espetacularização da violência/miséria — mencionado em ~25 de 50 reviews
        ex.: Muitos consideram que o filme transforma a violência e a miséria da favela em um espetáculo...
    • Representação estereotipada e deturpada da favela — mencionado em ~18 de 50 reviews
    • Violência excessiva e gratuita — mencionado em ~15 de 50 reviews
    • Falta de autenticidade/Crítica à perspectiva dos diretores — mencionado em ~10 de 50 reviews
    • Personagens pouco desenvolvidos e falta de conexão emocional — mencionado em ~8 de 50 reviews
    • Roteiro confuso/repetitivo e montagem frenética — mencionado em ~7 de 50 reviews
  » As reviews negativas apontam que o filme, apesar de seus méritos técnicos, falha eticamente ao
    estetizar a violência e a miséria [...]. Este grupo de espectadores sentiu-se incomodado [...]

▸ MEDIANAS  20/20 válidas [3.0★: 10 · 3.5★: 10]  modo=completo
  filtro aplicado (chars): [150]
    • Retrato da violência e realidade social — mencionado em ~11 de 20 reviews
    • Qualidade técnica e estilística — mencionado em ~9 de 20 reviews
    • Entretenimento versus profundidade/conexão emocional — mencionado em ~7 de 20 reviews
    • Ritmo e engajamento — mencionado em ~4 de 20 reviews
    • Caracterização dos personagens — mencionado em ~3 de 20 reviews
  » As reviews medianas de 3 a 3.5 estrelas apontam que o filme é tecnicamente impressionante [...]

▸ POSITIVAS  30/30 válidas [4.0★: 10 · 4.5★: 10 · 5.0★: 10]  modo=completo
  filtro aplicado (chars): [150]
    • Estilo visual e edição dinâmicos — mencionado em ~21 de 30 reviews
    • Narrativa envolvente e abrangente — mencionado em ~15 de 30 reviews
    • Brutalidade e realismo da violência — mencionado em ~14 de 30 reviews
    • Atuações marcantes — mencionado em ~10 de 30 reviews
    • Contexto social e histórico — mencionado em ~9 de 30 reviews
    • Mistura de gêneros — mencionado em ~3 de 30 reviews
  » As reviews positivas apontam o filme como uma obra-prima do cinema mundial [...]. Este grupo destaca [...]

Total de reviews observadas na coleta: 228
```

(Temas truncados aqui para leitura; o JSON completo com os `exemplo_parafraseado` está em `resultado/cidade-de-deus.json`.)

---

## Critério §5.3 — filme minúsculo (modo degradado severo)

### Sondagem de candidatos (Tarefa 2.1)

Busca via o endpoint de slug com queries de nicho (`curta-metragem`, `experimental brasil`, `documentário recife`) → candidatos das caudas (mais obscuros). 4 sondados com **1 requisição cada** à página base `/reviews/`:

| Candidato | Reviews na pág. 1 | Reviews c/ nota, s/ spoiler, ≥150 ch |
|---|---|---|
| `como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual` (2008) | 9 | 1 |
| `pessegos-em-calda-curta-metragem` | 0 | 0 |
| `light-curta-metragem-experimental` (2020) | 0 | 0 |
| `documentario-sobre-o-ciclo-do-recife` (2002) | 0 | 0 |

**Escolhido: `como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual`.** Interpretação registrada: os 3 candidatos com **0 reviews** são estritamente "mais escassos", mas produziriam um teste **vacuoso** — todos os buckets `sem_analise` com 0 válidas, sem caso "1-2 reviews" para exercitar a cláusula de textos brutos do §3[C], e sem coleta relevante. O escolhido é o **filme mais escasso que ainda produz um caso não-vacuoso**: 9 reviews totais, das quais poucas sobrevivem aos filtros — degrada de fato **e** gera buckets com 1-2 válidas. (Se o desejado for o estritamente-mais-escasso, a escolha volta ao usuário.)

### Metadados de coleta por nível (minúsculo)

| Nível | n_validas | n_brutas | filtro_aplicado | páginas |
|---|---|---|---|---|
| 0.5★ | 0 | 0 | 0 | 0 |
| 1.0★ | 0 | 0 | 0 | 0 |
| 1.5★ | 0 | 0 | 0 | 0 |
| 2.0★ | 1 | 1 | **0** | 1 |
| 2.5★ | 0 | 0 | 0 | 0 |
| 3.0★ | 1 | 1 | **50** | 1 |
| 3.5★ | 1 | 1 | **0** | 1 |
| 4.0★ | 1 | 1 | **0** | 1 |
| 4.5★ | 0 | 0 | 0 | 0 |
| 5.0★ | 1 | 5 | **150** | 1 |

**Bônus factual:** aqui a **cascata de relaxamento SIM ativou** — `filtro_aplicado` assume 50 (nível 3.0) e 0 (níveis 2.0/3.5/4.0) onde não havia review ≥150 chars, exatamente o mecanismo §C.3 que `cidade-de-deus` não chegou a exercitar. O nível 5.0 teve 5 brutas mas 4 curtas descartadas, fechando 1 válida em 150.

### Veredito por item (§5.3 / Tarefa 2.3)

**a. Piso de 3 por bucket respeitado — ✅.** Buckets: negativas 1 válida, medianas 2, positivas 2 — **todos < 3 → `modo=sem_analise`**. Nenhum bucket com <3 recebeu análise.

**b. `sem_analise` não inventou temas — ✅; textos brutos das 1-2 reviews — ⚠️ NÃO renderizados (GAP).** `n_temas=0` nos três buckets, nenhum tema inventado. **Porém:** os três buckets têm 1-2 válidas e, pelo §3[C] ("se houver 1–2 reviews, os textos brutos com aviso — spoiler não garantido"), deveriam exibir os **textos brutos** com o aviso de spoiler-não-garantido. O render mostra **apenas** a mensagem de contagem (`⚠️ Bucket sem análise temática: apenas N review(s) válida(s)`). Os textos brutos **não aparecem** — e nem estão serializados no JSON (`build_output` não guarda o texto das reviews de buckets `sem_analise`). **Discrepância spec↔implementação**, detalhada em "Comportamentos inesperados" abaixo.

**c. Render exibe avisos + rodapé com contagem total — ✅ (parcial).** Cada bucket `sem_analise` renderiza o aviso; o rodapé mostra `Total de reviews observadas na coleta: 9`, distinguindo "vazio por ninguém ter escrito" (é o caso) de "vazio por bucket". O aviso concreto de contagem aparece; o único faltante é o texto-bruto do item (b).

**d. NENHUMA chamada Gemini para bucket `sem_analise` — ✅ VERIFICADO.** O runner instrumentado registrou **0 chamadas Gemini** para cada um dos 3 buckets (e 0 no total do filme). `synthesize_bucket` retorna antes de tocar o LLM quando `modo==sem_analise` — confirmado empiricamente, não só por leitura de código.

### Output literal do terminal (minúsculo)

```
═══ Espectro 24 — como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual (spec v1.1.3) ═══

▸ NEGATIVAS  1/50 válidas [0.5★: 0 · 1.0★: 0 · 1.5★: 0 · 2.0★: 1 · 2.5★: 0]  modo=sem_analise
  filtro aplicado (chars): [0]
  ⚠️  Bucket sem análise temática: apenas 1 review(s) válida(s) (piso é 3).

▸ MEDIANAS  2/20 válidas [3.0★: 1 · 3.5★: 1]  modo=sem_analise
  filtro aplicado (chars): [0, 50]
  ⚠️  Bucket sem análise temática: apenas 2 review(s) válida(s) (piso é 3).

▸ POSITIVAS  2/30 válidas [4.0★: 1 · 4.5★: 0 · 5.0★: 1]  modo=sem_analise
  filtro aplicado (chars): [0, 150]
  ⚠️  Bucket sem análise temática: apenas 2 review(s) válida(s) (piso é 3).

Total de reviews observadas na coleta: 9
```

---

## Comportamentos inesperados / discrepâncias (para decisão do usuário)

1. **[GAP §3[C] ↔ implementação] Textos brutos de buckets `sem_analise` com 1-2 reviews não são exibidos.** O §3[C] diz: "se houver 1–2 reviews, os textos brutos com aviso (spoiler não garantido em reviews sem flag)". Hoje: (i) `build_output` (render.py) não serializa o texto das reviews de buckets `sem_analise` — só a contagem; (ii) `render_terminal` no ramo `sem_analise` imprime apenas a mensagem de contagem e faz `continue`. Resultado: o filme minúsculo, que tem exatamente o caso "1-2 reviews" nos 3 buckets, **não** mostra os textos brutos nem o aviso de spoiler-não-garantido. **Não corrigido** (fora do escopo desta sessão, que é rodar+verificar+reportar) — sinalizado para o usuário decidir se vira correção de código ou ajuste de spec. Note que o §5.3 *núcleo* (piso respeitado, `sem_analise` renderiza aviso, não inventa temas) **passa**; o que falha é o sub-requisito de textos brutos do §3[C].

2. **[Descasamento de exemplo na spec] `cidade-de-deus` não exercita a cascata de relaxamento.** A §5.2 nomeia `cidade-de-deus` como o exemplo de "fanbase review curta / cascata". Na prática o filme é coberto demais por nível (10 válidas ≥150 chars em cada nível) e **nunca** aciona a relaxação nem o modo reduzido — só o filtro de comprimento (que descarta ~76 curtas). O mecanismo de relaxação (`filtro_aplicado` 50/0) só apareceu no filme minúsculo do §5.3. Sugestão factual (não aplicada): a §5.2 poderia ou (a) trocar o exemplo por um filme de cobertura intermediária que realmente relaxe, ou (b) reescrever o critério para "o filtro de comprimento descarta as curtas corretamente e a análise permanece útil" — que é o que `cidade-de-deus` de fato demonstra.

3. **Nenhum outro comportamento inesperado.** Sem 403, sem truncamento descartado (`trunc-desc=0` em ambos), sem clamp de menções, sem flag de idioma/escopo/aspas em `cidade-de-deus`. Contagens de requisição dentro dos tetos.

## Artefatos

- `resultado/cidade-de-deus.json` — 3 buckets `completo`, 68 req Letterboxd.
- `resultado/como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual.json` — 3 buckets `sem_analise`, 15 req Letterboxd, 0 Gemini.
- `SPEC.md` v1.1.3 (nota de risco aceito anti-spoiler + changelog).
- `scripts/run_acceptance.py` — runner instrumentado (novo).
