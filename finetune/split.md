# Divisão por filme (PROPOSTA)

Semente 20261020. Estratos: época do professor × tercil de tokens de entrada da síntese × perfil (aclamado/outros). Teste 30 (os 5 da referência + 25 sorteados), validação 8, treino o resto.

| conjunto | filmes | exemplos de síntese (buckets) | bullets |
|---|---|---|---|
| treino | 60 | 180 | 1079 |
| validacao | 8 | 24 | 144 |
| teste | 30 | 89 | 534 |

**Teste:** 2001-a-space-odyssey, 500-days-of-summer, a-brighter-summer-day, aftersun, anatomy-of-a-fall, anatomy-of-a-murder, burning-2018, django-unchained, dr-strangelove-or-how-i-learned-to-stop-worrying-and-love-the-bomb, dune-2021, force-majeure-2014, friday-the-13th-2009, gladiator-2000, guillermo-del-toros-pinocchio, incendies, joker-2019, memento, mother-2017, napoleon-2023, portrait-of-a-lady-on-fire, shutter-island, spider-man-across-the-spider-verse, the-battle-of-algiers, the-invite-2026, the-prestige, the-revenant-2015, the-second-mother, the-substance, wicked-2024, woman-of-fire

**Validação:** chinatown, goodfellas, longlegs, perfect-days-2023, sinners-2025, the-gentlemen, the-godfather, zama

**Treino:** 12-angry-men, all-quiet-on-the-western-front-2022, arrival-2016, avengers-endgame, barbie, bones-and-all, cars, catch-me-if-you-can-2002, cats-2019, cidade-de-deus, cujo, cure, district-9, do-the-right-thing, drive-my-car, dune-part-two, eighth-grade, everything-everywhere-all-at-once, fight-club, get-out-2017, happy-hour-2015-1, hard-to-be-a-god, hereditary, im-still-here-2024, inception, inglourious-basterds, interstellar, joker-folie-a-deux, la-haine, mad-max-fury-road, malcolm-x-1992, marty-supreme, memories-of-murder, neighboring-sounds, oppenheimer-2023, parasite-2019, pearl-2022, pinocchio-2022, porco-rosso, princess-mononoke, prisoners, satantango, se7en, soul-2020, speak-no-evil-2022, talk-to-me-2022, the-brutalist, the-cloud-capped-star, the-hateful-eight, the-northman, the-spongebob-movie-search-for-squarepants, the-swimming-pool, the-truman-show, the-turin-horse, the-wailing, the-wolf-of-wall-street, top-gun-maverick, uncut-gems, whiplash-2014, wonka

## Balanço

- **epoca_professor**: V4-Flash → treino 20 / val 3 / teste 11; V4.1-Flash → treino 40 / val 5 / teste 19
- **tercil_tamanho**: 1 → treino 21 / val 3 / teste 9; 2 → treino 20 / val 2 / teste 11; 3 → treino 19 / val 3 / teste 10
- **perfil_grupo**: aclamado → treino 45 / val 5 / teste 23; outros → treino 15 / val 3 / teste 7
- **perfil**: aclamado → treino 45 / val 5 / teste 23; arthouse → treino 4 / val 1 / teste 2; divisivo → treino 6 / val 2 / teste 2; invertido → treino 4 / val 0 / teste 2; obscuro → treino 1 / val 0 / teste 1
- **lote**: catalogo-35 → treino 18 / val 3 / teste 10; expansao-53 → treino 13 / val 1 / teste 5; expansao-99 → treino 27 / val 4 / teste 13; fallback-conteudo → treino 0 / val 0 / teste 1; republicacao-3 → treino 2 / val 0 / teste 1
- **algum_bucket_reduzido**: False → treino 53 / val 7 / teste 28; True → treino 7 / val 1 / teste 2

**Buckets excluídos** (fora do treino e de toda avaliação, em todos os lados): `a-brighter-summer-day/positivas` (teste) — fallback_conteudo: síntese deste bucket feita pelo Gemini

Reviews do gabarito humano em filmes de teste (nunca treinar classificação nelas): 30
