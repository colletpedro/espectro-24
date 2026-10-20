# Limpeza do treino com o juiz v2.2 congelado (ESTIMADO)

Juiz `config_sha256` 44606cf1…; 16 s/par.

Posição do 1º par com apoio, na ordem de similaridade (referência, MEDIDO):

- publicado: {'1': 64, '3': 5, '2': 17, 'None': 2, '4': 2} → 131 de 450 pares (1.456 por bullet); parando no 2º sim (preserva o "apoio ≥ 2"): 288
- local: {'None': 6, '1': 70, '3': 2, '2': 10, '5': 1, '4': 1} → 135 de 450 pares (1.5 por bullet); parando no 2º sim (preserva o "apoio ≥ 2"): 265

Treino: 60 filmes, 1079 bullets, 180 exemplos (buckets). Economia de parar no 1º sim: 71% (lado publicado da referência).

Bucket com algum bullet sem apoio, na referência publicada: 0.133 (IC95 Wilson [0.037, 0.379]; pela taxa por bullet, 1−(1−2/90)^6 = 0.126).

| opção | horas de juiz | exemplos removidos (estimado) |
|---|---|---|
| filtrar tudo (60 filmes) | 7.0 h parando no 1º sim (24.0 h completo) | 24.0 de 180 |
| filtrar parte: só V4-Flash (20 filmes) | 2.3 h (8.0 h completo) | 8.0 |
| não filtrar | 0 h | 0 (≈ 24.0 bullets sem apoio ficam no alvo) |
