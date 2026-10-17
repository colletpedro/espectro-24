# Métricas mecânicas e barra dos bullets — ABRIR DEPOIS DA LEITURA

Este documento nomeia os lados (`publicado` × `local`).

## Taxas dos validadores mecânicos (sobre os filmes comparados)

| validador | publicado | local |
|---|---|---|
| filmes | 5 | 5 |
| sintese_buckets_com_falha_json | 0/15 | 0/15 |
| sintese_buckets_idioma_ou_escopo | 0/15 | 0/15 |
| sintese_temas_aspas_removidas | 0/90 | 0/90 |
| sintese_temas_mencoes_clampadas | 0/90 | 0/90 |
| rotulagem_buckets_que_falharam | 0/15 | 0/15 |
| rotulagem_eixos_fora_da_taxonomia | 1 | 0 |
| narrativa_flags_medias | 0.6 | 1.0 |
| narrativa_resenha_speak_media | 0.0 | 0.0 |
| narrativa_palavras_media | 256 | 285 |
| veredito_em_template_fallback | 0/5 | 0/5 |
| veredito_flags_medias | 0.0 | 0.0 |
| condicoes_em_abstencao | 0/5 | 0/5 |
| condicoes_publicadas_media | 6.8 | 7.8 |
| condicoes_descartadas_media | 0.0 | 1.0 |
| condicoes_recusas_media | 0.2 | 0.0 |

## Barra dos bullets: contagem da síntese × contagem da classificação

Faixa medida no DeepSeek (publicados): 1455 células em 99 filmes. Razão síntese/classificação p5–p95: 0.333–2.079 (mediana 0.8); diferença em pp de n, p5–p95: -45.0 a 20.0 (mediana -7.5). "Dentro" = razão E diferença dentro da faixa.

| filme | lado | células | dentro da faixa | razão mediana | dif. mediana (pp) | menor / maior dif. (pp) |
|---|---|---|---|---|---|---|
| anatomy-of-a-fall | publicado | 14 | 13 | 0.899 | -3.75 | -42.5 / +17.5 |
| anatomy-of-a-fall | local | 15 | 15 | 0.714 | -10.0 | -45.0 / +7.5 |
| incendies | publicado | 14 | 10 | 1.096 | +3.75 | -52.5 / +22.5 |
| incendies | local | 13 | 10 | 0.467 | -17.5 | -65.0 / +5.0 |
| mother-2017 | publicado | 15 | 12 | 0.7 | -7.5 | -45.0 / +20.0 |
| mother-2017 | local | 14 | 11 | 0.779 | -5.0 | -45.0 / +20.0 |
| napoleon-2023 | publicado | 14 | 13 | 0.567 | -17.5 | -42.5 / +5.0 |
| napoleon-2023 | local | 12 | 10 | 0.631 | -15.0 | -40.0 / +12.5 |
| the-substance | publicado | 14 | 11 | 0.613 | -16.25 | -37.5 / +20.0 |
| the-substance | local | 12 | 10 | 0.558 | -18.75 | -42.5 / +10.0 |

| lado | células dentro da faixa do DeepSeek |
|---|---|
| publicado | 59/71 (83%) |
| local | 56/66 (85%) |

## Mapeamento (qual lado foi A em cada filme)

| filme | A | B |
|---|---|---|
| anatomy-of-a-fall | local | publicado |
| incendies | publicado | local |
| mother-2017 | publicado | local |
| napoleon-2023 | publicado | local |
| the-substance | publicado | local |

## Tempo e raciocínio do lado local

| filme | chamadas | tempo (s) | think | falhas |
|---|---|---|---|---|
| anatomy-of-a-fall | 16 | 1682.7 | false | nenhuma |
| incendies | 17 | 2071.2 | false | nenhuma |
| mother-2017 | 18 | 2085.6 | false | nenhuma |
| napoleon-2023 | 17 | 1898.3 | false | nenhuma |
| the-substance | 18 | 2036.2 | false | nenhuma |
