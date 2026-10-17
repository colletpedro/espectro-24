# Prosa local — registro da execução (sem conteúdo de texto)

## gpt-oss:20b — NÃO CABE COM A PROSA
Parado pela guarda de memória às 2026-10-16 20:39 (RAM livre 0,26 GB, mínimo 0,09 GB;
pagefile 382 → 1168 MB, +786 MB) depois de 3 chamadas de síntese. Nenhum filme gerado.
Config: think=low, ctx 16.384, NUM_PREDICT_PROSA 4000. Registro: `prosa.log` (execução 20:33),
`prosa_gptoss_chamadas.jsonl`. Tentativa anterior (20:26, ctx 24.576) parou em segundos por pagefile
(+1,35 GB). O gate de classificação já tinha dado F1 0,680 contra 0,811 do DeepSeek.

## qwen3:14b — think=false, ctx 16.384, NUM_PREDICT_PROSA=4000
5 de 5 filmes completos, `falhas` vazio e `selecao_reproduz_publicada=True` nos cinco. Nenhum "NAO COUBE".
anatomy-of-a-fall e mother-2017 vieram de execuções anteriores (servidor sem reinício por filme);
napoleon-2023, the-substance e incendies, da execução com reinício do Ollama antes de cada filme.

| filme | total (s) | síntese | rotulagem | narrativa | veredito | condições |
|---|---|---|---|---|---|---|
| anatomy-of-a-fall | 1682,7 | 719,0 | 109,1 | 487,8 | 55,9 | 310,5 |
| mother-2017 | 2085,6 | 827,7 | 117,2 | 762,3 | 77,8 | 300,3 |
| napoleon-2023 | 1898,3 | 849,0 | 120,7 | 511,8 | 70,5 | 345,7 |
| the-substance | 2036,2 | 805,8 | 119,5 | 646,9 | 58,6 | 404,9 |
| incendies | 2071,2 | 773,5 | 115,1 | 736,2 | 42,2 | 403,7 |

Tempos de parede somados das chamadas. Chamadas por estágio: síntese 3, rotulagem 3, narrativa 4,
veredito 3–4, condições 3–4. **Truncamentos: nenhum** (todo `finish_reason` = stop, 0 falhas de chamada).

RAM livre mínima / pagefile (do `prosa.log`): anatomy 1,44 GB / ~373–403 MB (sem crescimento);
mother ~0,8 GB / max 337 MB (execução parada depois no napoleon, ver abaixo); napoleon 0,5 GB / 0 → 309 MB;
the-substance 0,76 GB / 217 → 225 MB; incendies 0,75 GB / 211 → 216 MB. Pagefile base 0 MB no napoleon é
leitura do início do processo. Execuções anteriores pararam por pagefile (+1,03 GB, 22:12) no napoleon
sem reinício do servidor; o reinício por filme resolveu.

Recusas dos validadores mecânicos (contagens do lado local, da telemetria):
| filme | narrativa: candidatos eliminados | veredito: eliminados | condições: descartadas |
|---|---|---|---|
| anatomy-of-a-fall | 3/3 | 2/3 | 0 |
| mother-2017 | 3/3 | 3/3 | 1 |
| napoleon-2023 | 3/3 | 3/3 | 0 |
| the-substance | 3/3 | 3/3 | 1 |
| incendies | 3/3 | 0/3 | 3 |
Narrativa: a amostra escolhida tem 1 flag em todos os filmes; retry de frases infratoras só em incendies (3 frases, não aplicado).
