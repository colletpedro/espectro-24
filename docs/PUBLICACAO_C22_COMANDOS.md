# Publicação dos filmes do C22 — lista única de comandos (PREPARADA, nada publicado)

Data: 2026-11-24. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**. Nada aqui publica: o último passo (push) é do dono.
Política: validadores mecânicos + guarda de quantidade em código + leitura do dono (decisão de 2026-11-23). O
veredito do C22 (`finetune/RESULTADO_C22.md`: C1–C4 e C6 passam) é registro de portfólio e não é degrau do gate.

## Onde estamos (MEDIDO)

| Peça | Estado |
|---|---|
| 5 filmes do C6 (full-metal-jacket, american-sniper, the-simpsons-movie, perfect-blue, eyes-wide-shut) | aprovados pelo dono (S nos 5, pelo chat) |
| 30 filmes restantes | **dependem da leitura do dono** (passos 6–7) |
| Buckets do C22 com `quantidade_pendente` | **16 de 105** (19 bullets). Dois são dos filmes do C6: `american-sniper/positivas` e `the-simpsons-movie/positivas` |
| Bucket reprovado no C4 | 1 (`harry-potter-and-the-deathly-hallows-part-1`, 2 de 3 buckets válidos) |
| Conferência TMDB dos 35 | **feita (MEDIDO): 35 validados, 0 divergentes, custo US$ 0** (`resultado/c22-publicacao/tmdb_conferencia.json`; só Perfect Blue tem ano 1997 no Letterboxd e 1998 no TMDB, evidência e não reprovação) |
| Fallback só nos 16 pendentes | `scripts/finetune/c22_fallback.py` (listar / rodar / aplicar), testado com cliente falso; **nenhuma chamada real foi feita** |
| Documento de leitura em 3 lotes | `scripts/finetune/c22_leitura.py lotes` (precisa do passo 4) |
| **Montagem do `resultado/<slug>.json` dos filmes C22** | **NÃO CONSTRUÍDA** (ver "Decisão em aberto"); sem ela não há condições nem publicação |

## ⚠ Atenção antes de começar

1. **Os 2 buckets pendentes dos filmes do C6.** O dono aprovou o texto de `american-sniper/positivas` e
   `the-simpsons-movie/positivas` COM uma palavra de quantidade ainda presente. Se o fallback for aceito, o bucket é
   regerado por inteiro (nova chamada, não edição de um bullet). O documento de leitura traz esses buckets numa
   seção **RE-LEITURA**; se o dono responder N, o filme sai da lista dos aprovados.
2. **O fallback é uma nova geração do bucket**, com a mesma amostragem e seed, mas prompt + reforço. Só é aceito se
   mantiver o mesmo número de bullets, não piorar idioma/escopo e reduzir os pendentes (as regras de produção).
3. **Custo.** Fallback e TMDB: US$ 0. Rotulagem e condições (Featherless, `deepseek-ai/DeepSeek-V4.1-Flash-1017`,
   teto autorizado US$ 0,50 no total): ESTIMADO ≤ US$ 0,0139 por filme com os três estágios pagos
   (mediana US$ 0,0117, 49 filmes de 08/11, sem desconto de cache) ⇒ **≤ US$ 0,49 para os 35 no pior caso**; como
   a síntese é local, o esperado é bem menor. O custo real fica em `resultado/c22-publicacao/custo.json` (a ser
   gravado pelo passo 9); parar se a soma passar de US$ 0,50.

## Comandos (Mac = `~/Downloads/espectro-24`; Windows = a árvore do `finetune` em que o C22 rodou)

**0. (Mac) Estado de partida**
```bash
cd ~/Downloads/espectro-24 && git pull && git log --oneline -1 && venv/bin/python -m pytest -q tests/test_fallback_quantidade.py tests/test_sintese_local.py
cd ~/Downloads/espectro-24-finetune && git pull && git log --oneline -1
```
Esperado: `main` em `e7c3ed1` ou depois e `finetune` em `bf82d6e` ou depois; testes verdes.

**1. (Windows) Preparar** — Ollama no ar com o GGUF `e488697e…` (o adaptador escolhe pelo sha, não pelo nome); sem
`ESPECTRO24_OLLAMA_TEMPERATURE` no ambiente; fora do Claude Code (o script recusa).
```powershell
cd <pasta do finetune>
git pull
python scripts\finetune\c22_fallback.py listar
```
Esperado: `16 de 105 buckets com quantidade_pendente (19 bullets)`.

**2. (Windows) Fumaça: UM bucket**
```powershell
python scripts\finetune\c22_fallback.py rodar --limite 1
```
**⏸ PARE** — veja a linha `[1/1] <filme>/<bucket>: <desfecho> · pendentes N→M`. Se der erro de modelo
(`ModeloLocalIndisponivel`), o GGUF não está no Ollama: não prossiga.

**3. (Windows) Os 15 restantes** (retoma sozinho; um bucket por vez; ESTIMADO ~45 min = 16 × 168,5 s, a mediana
MEDIDA da geração do C22)
```powershell
python scripts\finetune\c22_fallback.py rodar
git add finetune\c22\fallback
git commit -m "c22: fallback da guarda nos 16 buckets pendentes (resultado real)"
git push origin finetune
```
**⏸ PARE** — avise o Claude: ele continua no Mac.

**4. (Mac) Saída de produção do C22** (C22 como está, com o fallback aceito no lugar)
```bash
cd ~/Downloads/espectro-24-finetune && git pull
../espectro-24/venv/bin/python scripts/finetune/c22_fallback.py aplicar
```
Grava `finetune/c22/producao/<slug>__<bucket>.json` (105) e o manifesto com sha256. Mostra quantos fallbacks foram
aceitos/recusados e quantos bullets seguem pendentes.

**5. (Mac) Identidade TMDB — JÁ FEITA** (35/35 validados; para refazer:)
```bash
cd ~/Downloads/espectro-24 && venv/bin/python scripts/conferir_tmdb_c22.py
```
Filme com divergência sai da publicação e vai para a lista `divergentes` do mesmo arquivo. `ano_divergente: true` é
só evidência (o ano publicado é o do Letterboxd), não é reprovação.

**6. (Mac) Documento de leitura do dono: 3 lotes de 10 + RE-LEITURA do C6**
```bash
cd ~/Downloads/espectro-24-finetune
../espectro-24/venv/bin/python scripts/finetune/c22_leitura.py lotes
```
Gera `docs/arquivo-de-estudos/finetune-c22/leitura_lote_{1,2,3}.md`, `leitura_lotes_respostas.csv` (coluna `publico`) e
`leitura_fora.json` (quem saiu e por quê: TMDB, bucket sem síntese válida, sobra sem lote).
**⏸ PARE** — o dono lê e responde S/N em cada filme. Dúvida = N. (Pode responder pelo chat, como no C6; o Claude
preenche o CSV e registra a origem.)

**7. (Mac) Aprovados**
```bash
../espectro-24/venv/bin/python scripts/finetune/c22_leitura.py avaliar
```
Grava `finetune/c22/aprovados.json` (os S dos lotes + os 5 do C6, menos o C6 que for N na re-leitura).

**8. (Mac) Montar `resultado/<slug>.json` dos aprovados — NÃO CONSTRUÍDO.** Ver "Decisão em aberto".

**9. (Mac) Condições pelo Featherless (teto US$ 0,50)** — só depois do 8, só nos aprovados:
```bash
cd ~/Downloads/espectro-24 && venv/bin/python scripts/gerar_condicoes.py --slug <slug> --provider featherless --saida resultado/c22-publicacao/condicoes
```
(`--saida` nunca é `resultado/`; o §0 exige a leitura humana de 100% das condições antes de publicar.) Registrar o custo
real em `resultado/c22-publicacao/custo.json`.
**⏸ PARE** — leitura das condições pelo dono.

**10. (Mac) Publicar os 5 do C6 primeiro** (depois de 1–9 para eles), **depois cada lote aprovado**: acrescentar os
slugs a `dados/publicados.json`, `python3 frontend/build_data.py`, `python3 frontend/build_indice.py`, `pytest`, e
**subir `SPEC_VERSION` no commit do primeiro filme publicado com `quantidade_fallback`** (decisão do dono).
**⏸ PARE antes do push** (publicação só pelo git; o hook de pre-push roda `test_publicacao_consistente`).

**11. (Mac) Verificação no ar** (depois do push, o Vercel leva ~1 min)
```bash
curl -s https://espectro-24-eu6z.vercel.app/js/indice.js | grep -c '"slug"'      # esperado: 128 + N publicados
for s in <slugs>; do curl -s -o /dev/null -w "$s %{http_code}\n" https://espectro-24-eu6z.vercel.app/data/$s.json; done
```

## Decisão em aberto (PROPOSTO) — passo 8

O CLI (`espectro24.cli`) só monta o `resultado/<slug>.json` com a coleta do Letterboxd: offline ele exige as páginas
em `resultado/cache/` (que não existem para os 35; testei `full-metal-jacket --offline`: `FetchError: offline e sem
cache`), e coletar de novo esbarra na regra de parar no 403. Os 35 têm o bruto (`dados/bruto/<slug>`, versionado) e a
classificação (`consenso_verificado`), e as buckets do C22 foram montadas a partir do bruto (`prosa_local._buckets_do_bruto`).

**Proposta:** um montador offline (`scripts/montar_resultado_c22.py`) que repete o que o CLI faz depois da coleta, sem
rede de Letterboxd: buckets do bruto → síntese = a saída de produção do passo 4 (não chama o modelo) → eixos pela
classificação verificada → rotulagem (LLM Featherless, dentro do teto) → ficha TMDB (já conferida) → distribuição a
partir do `histograma_bruto` do `meta.json` → `build_output`. **Risco:** a distribuição vinda do histograma do meta
pode não ser byte a byte a que o CLI grava; eu mediria a diferença nos 29 de 08/11 (que têm as duas) antes de usar.
**Alternativa:** recoletar o histograma de cada filme (rede do Letterboxd), o que a regra do 403 desaconselha.
