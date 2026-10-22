# Limpeza com o juiz v2.2 — resumo

Juiz `44606cf1…`. Pares julgados 1863 de 6115 na entrada (parada no 1º sim). Estados dos bullets: {'com_apoio': 1176, 'sem_apoio': 45, 'indeterminado': 2}. Um bucket sai se tiver bullet em ['indeterminado', 'sem_apoio'].

| conjunto | época | buckets | removidos | pendentes |
|---|---|---|---|---|
| treino | V4-Flash | 60 | 17 | 0 |
| treino | V4.1-Flash | 120 | 22 | 0 |
| validacao | V4-Flash | 9 | 3 | 0 |
| validacao | V4.1-Flash | 15 | 2 | 0 |

## Por filme

| filme | conjunto | época | bucket | estados | sai? |
|---|---|---|---|---|---|
| 12-angry-men | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| 12-angry-men | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| 12-angry-men | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| all-quiet-on-the-western-front-2022 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| all-quiet-on-the-western-front-2022 | treino | V4.1-Flash | negativas | {'sem_apoio': 1, 'com_apoio': 5} | SAI |
| all-quiet-on-the-western-front-2022 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| arrival-2016 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| arrival-2016 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| arrival-2016 | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| avengers-endgame | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| avengers-endgame | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| avengers-endgame | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| barbie | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| barbie | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| barbie | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| bones-and-all | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| bones-and-all | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| bones-and-all | treino | V4-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cars | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cars | treino | V4.1-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cars | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| catch-me-if-you-can-2002 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| catch-me-if-you-can-2002 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| catch-me-if-you-can-2002 | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cats-2019 | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| cats-2019 | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| cats-2019 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| chinatown | validacao | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| chinatown | validacao | V4.1-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| chinatown | validacao | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| cidade-de-deus | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cidade-de-deus | treino | V4-Flash | negativas | {'com_apoio': 5, 'indeterminado': 1} | SAI |
| cidade-de-deus | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| cujo | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cujo | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| cujo | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| cure | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| cure | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| cure | treino | V4-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| district-9 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| district-9 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| district-9 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| do-the-right-thing | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| do-the-right-thing | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| do-the-right-thing | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| drive-my-car | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| drive-my-car | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| drive-my-car | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| dune-part-two | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| dune-part-two | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| dune-part-two | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| eighth-grade | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| eighth-grade | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| eighth-grade | treino | V4-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| everything-everywhere-all-at-once | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| everything-everywhere-all-at-once | treino | V4-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| everything-everywhere-all-at-once | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| fight-club | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| fight-club | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| fight-club | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| get-out-2017 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| get-out-2017 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| get-out-2017 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| goodfellas | validacao | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| goodfellas | validacao | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| goodfellas | validacao | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| happy-hour-2015-1 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| happy-hour-2015-1 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| happy-hour-2015-1 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| hard-to-be-a-god | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| hard-to-be-a-god | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| hard-to-be-a-god | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| hereditary | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| hereditary | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| hereditary | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| im-still-here-2024 | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| im-still-here-2024 | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| im-still-here-2024 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| inception | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| inception | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| inception | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| inglourious-basterds | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| inglourious-basterds | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| inglourious-basterds | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| interstellar | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| interstellar | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| interstellar | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| joker-folie-a-deux | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| joker-folie-a-deux | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| joker-folie-a-deux | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| la-haine | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| la-haine | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| la-haine | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| longlegs | validacao | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| longlegs | validacao | V4-Flash | negativas | {'com_apoio': 6} | fica |
| longlegs | validacao | V4-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| mad-max-fury-road | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| mad-max-fury-road | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| mad-max-fury-road | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| malcolm-x-1992 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| malcolm-x-1992 | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| malcolm-x-1992 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| marty-supreme | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| marty-supreme | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| marty-supreme | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| memories-of-murder | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| memories-of-murder | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| memories-of-murder | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| neighboring-sounds | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| neighboring-sounds | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| neighboring-sounds | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| oppenheimer-2023 | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| oppenheimer-2023 | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| oppenheimer-2023 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| parasite-2019 | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| parasite-2019 | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| parasite-2019 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| pearl-2022 | treino | V4-Flash | medianas | {'com_apoio': 6} | fica |
| pearl-2022 | treino | V4-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| pearl-2022 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| perfect-days-2023 | validacao | V4-Flash | medianas | {'com_apoio': 6} | fica |
| perfect-days-2023 | validacao | V4-Flash | negativas | {'com_apoio': 6} | fica |
| perfect-days-2023 | validacao | V4-Flash | positivas | {'com_apoio': 6} | fica |
| pinocchio-2022 | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| pinocchio-2022 | treino | V4.1-Flash | negativas | {'com_apoio': 5, 'indeterminado': 1} | SAI |
| pinocchio-2022 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| porco-rosso | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| porco-rosso | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| porco-rosso | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| princess-mononoke | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| princess-mononoke | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| princess-mononoke | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| prisoners | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| prisoners | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| prisoners | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| satantango | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| satantango | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| satantango | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| se7en | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| se7en | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| se7en | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| sinners-2025 | validacao | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| sinners-2025 | validacao | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| sinners-2025 | validacao | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| soul-2020 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| soul-2020 | treino | V4.1-Flash | negativas | {'com_apoio': 4, 'sem_apoio': 2} | SAI |
| soul-2020 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| speak-no-evil-2022 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| speak-no-evil-2022 | treino | V4.1-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| speak-no-evil-2022 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| talk-to-me-2022 | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| talk-to-me-2022 | treino | V4-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| talk-to-me-2022 | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| the-brutalist | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-brutalist | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-brutalist | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| the-cloud-capped-star | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-cloud-capped-star | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-cloud-capped-star | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-gentlemen | validacao | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-gentlemen | validacao | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-gentlemen | validacao | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-godfather | validacao | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-godfather | validacao | V4-Flash | negativas | {'com_apoio': 6} | fica |
| the-godfather | validacao | V4-Flash | positivas | {'com_apoio': 6} | fica |
| the-hateful-eight | treino | V4-Flash | medianas | {'com_apoio': 5} | fica |
| the-hateful-eight | treino | V4-Flash | negativas | {'com_apoio': 6} | fica |
| the-hateful-eight | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| the-northman | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-northman | treino | V4-Flash | negativas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-northman | treino | V4-Flash | positivas | {'com_apoio': 6} | fica |
| the-spongebob-movie-search-for-squarepants | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-spongebob-movie-search-for-squarepants | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-spongebob-movie-search-for-squarepants | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| the-swimming-pool | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-swimming-pool | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-swimming-pool | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| the-truman-show | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-truman-show | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-truman-show | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| the-turin-horse | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-turin-horse | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-turin-horse | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-wailing | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-wailing | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-wailing | treino | V4.1-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| the-wolf-of-wall-street | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| the-wolf-of-wall-street | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| the-wolf-of-wall-street | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| top-gun-maverick | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| top-gun-maverick | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| top-gun-maverick | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| uncut-gems | treino | V4.1-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| uncut-gems | treino | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| uncut-gems | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| whiplash-2014 | treino | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| whiplash-2014 | treino | V4.1-Flash | negativas | {'sem_apoio': 2, 'com_apoio': 4} | SAI |
| whiplash-2014 | treino | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
| wonka | treino | V4-Flash | medianas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| wonka | treino | V4-Flash | negativas | {'com_apoio': 4, 'sem_apoio': 2} | SAI |
| wonka | treino | V4-Flash | positivas | {'com_apoio': 5, 'sem_apoio': 1} | SAI |
| zama | validacao | V4.1-Flash | medianas | {'com_apoio': 6} | fica |
| zama | validacao | V4.1-Flash | negativas | {'com_apoio': 6} | fica |
| zama | validacao | V4.1-Flash | positivas | {'com_apoio': 6} | fica |
