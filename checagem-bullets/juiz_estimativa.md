# Parte 2 — estimativa de chamadas e tempo do juiz

**900 chamadas** (450 do lado publicado, 450 do lado local): um bullet × uma review por chamada, 5 reviews por bullet.

**Tempo estimado: ~89 min** (faixa 67–179 min), ~5.5 s por chamada na mediana.

**É estimativa, não medição.** Sai das velocidades do qwen3:14b MEDIDAS no notebook, nos 300 registros do gate de classificação (uma review por chamada, JSON curto, system no KV), aplicadas ao tamanho real de cada par:

- leitura do prompt: 2.04 ms por caractere novo (review + tema + descrição; o system fica no KV);
- geração: 0.223 s por token, ~10 tokens por resposta;
- sobra por chamada (parede − leitura − geração): 2.07 s (mediana);
- latência mediana do gate, para comparar: 10.6 s (lá a resposta tinha ~35 tokens).

A faixa vai de 0,75× a 2×: a ponta de cima cobre a gramática do schema custar mais que no gate e o notebook mais quente/ocupado.

Fontes da velocidade: `qwen3-14b/classificacao_passe_1.jsonl`, `qwen3-14b/classificacao_passe_2.jsonl`, `qwen3-14b/classificacao_passe_3.jsonl`
