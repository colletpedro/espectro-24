# RESULTADO DO C22 — avaliação de produção do treinado (35 filmes, 105 buckets)

Data: 2026-11-24. Pré-registro: `PREREGISTRO_C22.md` (commit `82136d7`, escopo `23cc978c…`, plano `1701d085…`,
guarda `61da0b7d…`). Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**.
Os números vêm de `finetune/c22/cego/c1_c4_c22.json` (sha256 `6f84a0a9…`, commit `496384e`, `c22.py` sha
`342d2926…`) e de `finetune/c22/c6_resultado.json` (sha256 `cde09539…`). Eles foram abertos **depois** da
resposta do dono ao C6, como o pré-registro manda. Nada foi regerado nem recalculado nesta rodada.

## Veredito

**Os cinco critérios pré-registrados passam (C1, C2, C3, C4, C6).** Pelo pré-registro, as sínteses geradas
nesta rodada são a saída de produção, sem nova geração. O veredito da Fase 4 (`RESULTADO_FASE4.md`: não
publicável por C1 e C3) **não muda**: são avaliações diferentes (outro conjunto de filmes e a guarda de
quantidade em código), e este resultado não o reabre. A publicação segue a política de produto de
2026-11-23 (validadores + guarda + leitura do dono); o veredito do C22 é registro de portfólio e não é um
degrau do gate.

## Critérios contra os limiares pré-registrados (MEDIDO)

IC95 por bootstrap por filme, 10.000 reamostras, semente 20261108, percentil 2,5/97,5, razão das somas
(35 filmes, 629 bullets julgados).

| Critério | O que mede | Limiar pré-registrado | Resultado (IC95) | Passa |
|---|---|---|---|---|
| C1 | bullets sem apoio nas reviews (juiz v2.2 `44606cf1…`, parada no 2º sim) | estimativa ≤ 5,6% e limite superior < 7,6% | **4,45%** (2,54–6,68%) — 28/629 | sim |
| C2 | bullets com apoio ≥ 2 | limite inferior > 77,8% | **83,15%** (80,16–86,01%) — 523/629 | sim |
| C3 | M1 (palavra de quantidade) depois da guarda | estimativa ≤ 10% e limite superior < 15% | **3,02%** (1,75–4,30%) — 19/629 | sim |
| C4 | buckets válidos (JSON + validadores, com a retentativa de produção) | ≥ 97% (≥ 102/105) | **104/105 = 99,05%** | sim |
| C6 | leitura cega do dono, 5 filmes sorteados, "publicável? S/N" | ≥ 4 de 5 | **5 de 5 S** | sim |

Margens: C1 tem 1,15 pp de folga no ponto e 0,92 pp no limite superior, a mais apertada das três
estatísticas; C2 tem 2,4 pp de folga no limite inferior; C3 tem 6,98 pp no ponto.

### C6 (MEDIDO)

Sorteio com semente 20261109 sobre os 35 filmes elegíveis (todos com os 3 buckets): full-metal-jacket,
american-sniper, the-simpsons-movie, perfect-blue, eyes-wide-shut. O mapa foi commitado antes da leitura
(`00392cc`). O documento tinha só os bullets, sem nenhum número do C22.
**A resposta do dono veio pelo chat** (S nos 5), e foi o Claude quem preencheu `leitura_c6_respostas.csv`
(commit `6158c8d`, origem em `docs/arquivo-de-estudos/finetune-c22/leitura_c6_origem.md`). Isto difere do
procedimento previsto (o dono preencher o CSV); o conteúdo da resposta não está em dúvida.

## Descritivos (MEDIDO, sem limiar)

- **M1 antes e depois da guarda:** 494/629 bullets (78,5%) tinham palavra da lista congelada antes; 19/629
  (3,0%) depois. A guarda alterou 487 textos (77,4%). Os 19 restantes são exatamente os `quantidade_pendente`
  (sem regra segura de reescrita). Referência do desenvolvimento (Fase 4, teste): treinado 82,4% → 2,1%.
- **Buckets com `quantidade_pendente`: 16 de 105 (15,2%)**, com 19 bullets, 1 a 2 por bucket (seis temas por
  bucket): 1917 medianas, a-fistful-of-dollars medianas, american-sniper positivas, detachment medianas (2),
  harry-potter-and-the-deathly-hallows-part-1 medianas, how-to-train-your-dragon medianas (2), kill-bill-vol-2
  medianas e positivas, men-in-black medianas, poor-things-2023 medianas, rango positivas, saving-private-ryan
  positivas (2), the-dark-knight medianas, the-good-the-bad-and-the-ugly positivas, the-simpsons-movie
  positivas, toy-story-3 negativas. Nove são `medianas`, seis `positivas` e uma `negativas`.
  O ESTIMADO de 23/11 era "até 12%" (11/89 no desenvolvimento); a taxa medida aqui (15,2%) ficou acima.
- **Estados do juiz:** apoio 2: 523 (83,1%); apoio 1: 78 (12,4%); sem apoio: 28 (4,5%).
- **Retentativa de produção:** 104 buckets ficaram na 1ª chamada, 1 usou a 2ª; 103 estavam válidos já na 1ª
  tentativa. Sem fallback da guarda neste regime (`quantidade_fallback` ausente em todos).
- **O bucket reprovado no C4:** o de `harry-potter-and-the-deathly-hallows-part-1` (3 buckets, 2 válidos).
  O motivo exato por validador não foi aberto nesta rodada.
- **Por filme:** nenhum filme passou de 5 bullets sem apoio (toy-story-3: 5/18, o pior); M1 residual de 0 a 2
  bullets por filme.
- **Tempo de geração (Windows, Ollama):** 105 chamadas, mediana 168,5 s, média 175,4 s, mín. 132,5 s, máx.
  390,7 s; total 5,12 h. É a duração por bucket, não por filme (3 buckets).

## O que NÃO foi medido

- **Comparação direta com o publicado nos mesmos filmes.** Os 35 não têm síntese do DeepSeek; os limiares são
  absolutos, ancorados no publicado da Fase 2 (3,6% sem apoio, 85,6% apoio ≥ 2). O treinado fica 0,9 pp
  acima no sem apoio e 2,5 pp abaixo no apoio ≥ 2 em relação a essas âncoras, dentro das folgas, mas isso
  compara filmes diferentes.
- **Os 30 filmes restantes não foram lidos por humano.** O C6 amostra 5 de 35. A decisão de publicação de
  cada um depende da leitura do dono.
- **Bullets pendentes depois do fallback.** O fallback não rodou no C22 (regime pré-registrado). O que ele
  resolve nesses 16 buckets é desconhecido até rodar.
- **Os 2 buckets pendentes entre os filmes do C6** (american-sniper e the-simpsons-movie, ambos
  `positivas`): o dono leu e aprovou o texto **com** a palavra de quantidade ainda presente. Se o fallback
  regerar esses buckets, o texto aprovado muda por inteiro (nova chamada, não edição de um bullet).
- **Identidade (TMDB)**: não conferida nos 35 (`sem_ficha_persistida`); roda na publicação e é gratuita.
- **Os 15 filmes sem classificação e os 5 com pendência de corpus** ficaram fora do escopo.
- **Juiz como gate:** a taxa do juiz (`gpt-oss:20b` v2.2) é registro, fora do gate de publicação (decisão
  de 08/11). A concordância do juiz com leitura humana nestes filmes não foi medida.
- **Fluência fora da guarda:** o 28/30 foi medido em 30 pares do desenvolvimento, não nos 629 bullets do C22;
  só 5 filmes tiveram leitura humana.
- **Causa do viés de quantidade** do treinado (amplifica o padrão do alvo, +27,6 pp): segue não investigada;
  a guarda o mascara no texto, não o remove da geração.
- **Reprodutibilidade em outra máquina/Ollama:** as sínteses são da execução de 2026-11-05 no Windows; não
  há garantia de saída idêntica ao regerar.
