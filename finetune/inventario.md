# Inventário — fase 0 do fine-tuning da síntese

Gerado por `scripts/finetune/inventario.py` (zero rede, zero LLM). Números de contagem e de tokens são **MEDIDOS** com os tokenizers reais (revisões abaixo); a saída da síntese é o publicado reserializado em JSON indent=2 (**formato PROPOSTO**); a saída de condições é **ESTIMADA** (montada do publicado, que passou por leitura humana). Contexto = maior total × 1,10 (**PROPOSTO**), em múltiplo de 512 (treino) ou entrada máxima + teto de saída de produção × 1,10, em múltiplo de 1024 (inferência).

| candidato | repo@revisão | sha256 do tokenizer.json |
|---|---|---|
| Qwen3.5-9B | `Qwen/Qwen3.5-9B@c202236235` | `5f9e4d4901a92b99…` |
| Gemma-4-E4B | `google/gemma-4-E4B-it@ee0ef60236` | `cc8d3a0ce36466cc…` |
| Gemma-4-12B | `google/gemma-4-12B-it@707f0a3b8a` | `cc8d3a0ce36466cc…` |

## Exemplos e tokens por estágio

### sintese — 293 exemplos utilizáveis em 98 filmes (3 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 5820 / 7771 / 12437 / 21733 | 674 / 731 / 780 / 922 | 22482 | 25088 | 27648 |
| Gemma-4-E4B | 5855 / 7817 / 12585 / 21976 | 687 / 743 / 793 / 929 | 22744 | 25088 | 27648 |
| Gemma-4-12B | 5855 / 7817 / 12585 / 21976 | 687 / 743 / 793 / 929 | 22744 | 25088 | 27648 |

### narrativa — 98 exemplos utilizáveis em 98 filmes (1 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 3334 / 3453 / 3648 / 3648 | 380 / 418 / 457 / 457 | 4043 | 4608 | — |
| Gemma-4-E4B | 3358 / 3478 / 3682 / 3682 | 382 / 422 / 456 / 456 | 4080 | 4608 | — |
| Gemma-4-12B | 3358 / 3478 / 3682 / 3682 | 382 / 422 / 456 / 456 | 4080 | 4608 | — |

### veredito — 79 exemplos utilizáveis em 79 filmes (1 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 1221 / 1237 / 1347 / 1347 | 66 / 76 / 78 / 78 | 1425 | 2048 | — |
| Gemma-4-E4B | 1227 / 1244 / 1353 / 1353 | 66 / 76 / 79 / 79 | 1431 | 2048 | — |
| Gemma-4-12B | 1227 / 1244 / 1353 / 1353 | 66 / 76 / 79 / 79 | 1431 | 2048 | — |

### condicoes — 96 exemplos utilizáveis em 96 filmes (1 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 3810 / 4051 / 4524 / 4524 | 278 / 328 / 397 / 397 | 4836 | 5632 | — |
| Gemma-4-E4B | 3858 / 4111 / 4564 / 4564 | 289 / 342 / 409 / 409 | 4901 | 5632 | — |
| Gemma-4-12B | 3858 / 4111 / 4564 / 4564 | 289 / 342 / 409 / 409 | 4901 | 5632 | — |

### classificacao_consenso — 12976 exemplos utilizáveis em 98 filmes (136 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 1034 / 1211 / 1756 / 14509 | 31 / 43 / 56 / 66 | 14567 | 16384 | 16384 |
| Gemma-4-E4B | 1031 / 1208 / 1756 / 14700 | 31 / 45 / 57 / 69 | 14761 | 16384 | 17408 |
| Gemma-4-12B | 1031 / 1208 / 1756 / 14700 | 31 / 45 / 57 / 69 | 14761 | 16384 | 17408 |

### classificacao_gabarito — 94 exemplos utilizáveis em 32 filmes (6 de filmes excluídos)

| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |
|---|---|---|---|---|---|
| Qwen3.5-9B | 1017 / 1329 / 2213 / 2213 | 29 / 56 / 66 / 66 | 2264 | 2560 | 3072 |
| Gemma-4-E4B | 1012 / 1331 / 2149 / 2149 | 29 / 57 / 69 / 69 | 2214 | 2560 | 3072 |
| Gemma-4-12B | 1012 / 1331 / 2149 / 2149 | 29 / 57 / 69 / 69 | 2214 | 2560 | 3072 |

## Filmes sem o estágio (fora os excluídos)

- **sintese** (0): —
- **narrativa** (0): —
- **veredito** (19): burning-2018, drive-my-car, force-majeure-2014, get-out-2017, guillermo-del-toros-pinocchio, happy-hour-2015-1, hard-to-be-a-god, memories-of-murder, neighboring-sounds, pinocchio-2022, satantango, speak-no-evil-2022, the-cloud-capped-star, the-second-mother, the-turin-horse, the-wailing, whiplash-2014, woman-of-fire, zama
- **condicoes** (2): a-brighter-summer-day, woman-of-fire
- **classificacao_consenso** (0): —

## Bullets (temas) por bucket

- Teto `MAX_TEMAS = 6` — **não é fixo**: é máximo. Fixado em `src/espectro24/config.py:562`, pedido no prompt em `src/espectro24/synthesize.py:113` ("no máximo") e cortado no código em `src/espectro24/synthesize.py:2098`.
- Por bucket utilizável (n temas → n buckets): {5: 1, 6: 292}
- Por filme (soma dos buckets utilizáveis → n filmes): {12: 1, 17: 1, 18: 96}

## Lote e época do professor

| lote | época do professor | filmes |
|---|---|---|
| catalogo-35 | V4-Flash | 31 |
| demo-v1.1.3 | None | 1 |
| expansao-53 | V4.1-Flash | 19 |
| expansao-99 | V4.1-Flash | 44 |
| fallback-conteudo | V4.1-Flash | 1 |
| obsession-migracao | V4-Flash | 1 |
| republicacao-3 | V4-Flash | 3 |

## Pendências de identidade e corpus

- **excluir de todos os conjuntos (PROPOSTO): `obsession-2025`** — família obsession-*: o corpus publicado começou como o do curta (obsession-2026) e foi migrado para o do longa em v1.9.50 (ABERTO C13); o gabarito humano ainda tem 6 reviews do curta
- **excluir de todos os conjuntos (PROPOSTO): `como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual`** — JSON de v1.1.3 (2026-07-20): os 3 buckets são sem_analise (0 chamadas de síntese) e não há eixos, narrativa, veredito nem condições — nenhum estágio utilizável
- `talk-to-me-2022`: identidade `validada` (tmdb 1008042); síntese de 2026-08-22; sinais no corpus analisado: 44/119 com termo do longa de 2022, 0 com termo do filme de 2007.
- gabarito humano com reviews de obsession-*: 6
- sem bloco `identidade` (guarda v1.9.49 nunca rodou no artefato): 33 — aftersun, anatomy-of-a-fall, avengers-endgame, barbie, bones-and-all, cats-2019, cidade-de-deus, cure, dune-2021, dune-part-two, eighth-grade, everything-everywhere-all-at-once, friday-the-13th-2009, hereditary, im-still-here-2024, interstellar, joker-folie-a-deux, longlegs, mother-2017, napoleon-2023, oppenheimer-2023, parasite-2019, pearl-2022, perfect-days-2023, shutter-island, spider-man-across-the-spider-verse, the-godfather, the-hateful-eight, the-invite-2026, the-northman, the-substance, wicked-2024, wonka
- 55 filmes do lote C22 (excecao_c22.SLUGS) não têm resultado/*.json: nenhum exemplo de síntese
