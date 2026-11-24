# Publicação dos filmes do C22 — lista única de comandos (nada publicado)

Atualizado em 2026-11-24. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO**. O push é sempre do dono (⏸ PARE).
Política: validadores mecânicos + guarda de quantidade em código + leitura do dono (decisão de 2026-11-23). O veredito
do C22 (`finetune/RESULTADO_C22.md`: C1–C4 e C6 passam) é registro de portfólio e não é degrau do gate.

## Decisões do dono desta rodada
- Montador offline: SIM, validado primeiro nos 29 (feito, abaixo). **Rotulagem por LLM autorizada dentro do MESMO teto
  de US$ 0,50 no total** (rotulagem + condições + qualquer estágio pago); custo real por estágio registrado.
- `harry-potter-and-the-deathly-hallows-part-1/positivas` (reprovou no C4): UMA nova geração local; se passar nos
  validadores e na guarda volta para os lotes; senão fica fora desta rodada (registrar).
- `perfect-blue` 1997 × 1998: aceito, registrado como evidência.
- Ficam FORA: `coleta_pos_esfriamento.py`, `coletar_biblioteca.py`, `coleta_direta_lenta.py`, os scripts Firecrawl/sessão.

## Onde estamos (MEDIDO)

| Peça | Estado |
|---|---|
| Montador offline (`src/espectro24/montagem_offline.py`) | **validado nos 29: 29/29 idênticos** (ver abaixo) |
| Conferência TMDB dos 35 | 35 validados, 0 divergentes, US$ 0 (`resultado/c22-publicacao/tmdb_conferencia.json`) |
| 5 filmes do C6 | aprovados pelo dono (S nos 5, pelo chat) |
| Buckets com `quantidade_pendente` | 16 de 105 (19 bullets); 2 são dos filmes do C6 |
| Bucket reprovado no C4 | `harry-potter-and-the-deathly-hallows-part-1/positivas`: `observacao_geral` vazia (validador `campos_nao_vazios`) |
| Fallback e nova geração | `scripts/finetune/c22_fallback.py` (`listar`, `rodar`, `regerar`, `aplicar`); só testados com cliente falso |
| Leitura em lotes | `scripts/finetune/c22_leitura.py` (`lotes`, `avaliar`) |
| Rotulagem, condições, publicação | depois de 3–6 abaixo |

### Validação do montador nos 29 de 08/11 (MEDIDO, `resultado/c22-publicacao/validacao_montador_29.json`)

Para cada um dos 29: bruto versionado + a classificação que o resultado cita (sha conferido) + a síntese INJETADA a
partir do `resultado/<slug>.json` + a rotulagem REPETIDA das respostas gravadas (chave = sha256 do prompt, então o
prompt remontado é idêntico byte a byte; 87 chamadas, 3 por filme). Comparação campo a campo com o resultado
versionado menos `condicoes` e `ficha.paises` (etapas seguintes): **0 diferenças em 29/29**. Contra o `bullets.json`
original (em `execucoes/`, fora do git) as únicas diferenças são o caminho da fonte (`eixos.verificador.fonte` e
`proveniencia_llm.classificacao.fonte`: relativo de propósito, 29 × 2). **O que a validação NÃO cobre:** a `ficha` é
entrada do montador (não foi regerada pelo TMDB: a regeneração baixa imagens para o pHash e travou; a ficha do C22 vem
da conferência TMDB já feita) e `condicoes`/R13 (etapa seguinte, igual à dos 29).

### Os 6 testes vermelhos (sem afrouxar asserção)
- `hero_faixa`: lista nomeada atualizada para 128 (+7: alien, cinema-paradiso, life-is-beautiful, modern-times,
  seven-samurai, the-godfather-part-ii, wall-e); a trava pHash segue valendo para todos. **Corrigido.**
- `paises_editorial`: reescrito sem conjunto fixo (nenhum filme da base apagado ou alterado além de `ficha.paises`; filme
  novo exige `ficha.paises` válido). **Corrigido.**
- `aplicar_lei_margem` (`KeyError 'alien'`): a classificação dos 29 entrou em `consenso.jsonl` e
  `consenso_verificado.jsonl` (3.455 linhas cada, sem chamada), e `verificador_manifesto.json` registra a incorporação.
  **Corrigido.**
- `test_condicoes` (leon) e `publicar_condicoes` (5 filmes): **diagnosticados, NÃO alterados** — ver "Conteúdo no ar".

### Conteúdo no ar: diagnóstico e proposta (nada aplicado)
- **`leon-the-professional` ("12" no briefing).** O "12" vem da PARÁFRASE de três bullets publicados ("personagem de 12
  anos", NEG-A, MED-A, POS-C), não de uma condição: o texto das condições publicadas NÃO tem "12" (MEDIDO). A regra R4
  (zero dígitos) é sobre o que a condição diz; o briefing leva o dígito ao modelo. **Proposta A (custo zero):** reescrever
  nos três bullets "uma personagem de 12 anos" → "uma personagem muito jovem" (troca mecânica, nenhum número novo).
  **Proposta B:** exceção estreita "idade de personagem", como a do ano no nome do tema (Pinocchio), o que MUDA o teste e é
  decisão sua. Recomendo A.
- **`psycho` NEG-B, `pulp-fiction` NEG-A, `the-shawshank-redemption` NEG-A, `harakiri` NEG-B, `the-lion-king` NEG-E.** Em
  todos, o tema (eixo `expectativa`, "superestimado") foi PEDIDO (`temas_pedidos`) e a regra R13 o retém; **nenhuma condição
  publicada tem esse `tema_origem`** (MEDIDO nos 5). Ou seja, a regra foi cumprida no ar; o teste só não conhecia a medição
  nova. **Proposta:** acrescentar os 5 pares ao conjunto esperado do teste (igualdade exata, como em 2026-09-17 para fight-club,
  gladiator-2000 e the-truman-show), com o diagnóstico acima no docstring. Custo zero.

## Comandos (Mac = `~/Downloads/espectro-24`; Windows = a árvore do `finetune`)

**0. (Mac) Estado de partida**
```bash
cd ~/Downloads/espectro-24 && git pull && git log --oneline -1
cd ~/Downloads/espectro-24-finetune && git pull && git log --oneline -1
```
Esperado: `main` em `c202203` ou depois e `finetune` em `23852be` ou depois.

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
**⏸ PARE** — veja `[1/1] <filme>/<bucket>: <desfecho> · pendentes N→M`. Erro `ModeloLocalIndisponivel` = o GGUF não está
no Ollama: não prossiga.

**3. (Windows) Os 15 restantes** (retoma sozinho; um bucket por vez; ESTIMADO ~45 min = 16 × 168,5 s, a mediana MEDIDA do C22)
```powershell
python scripts\finetune\c22_fallback.py rodar
```

**4. (Windows) UMA nova geração do bucket reprovado do Harry Potter** (uma só; usa o prompt de retentativa da produção
porque a mesma semente reproduziria a saída reprovada — ESTIMADO; ~3 min)
```powershell
python scripts\finetune\c22_fallback.py regerar harry-potter-and-the-deathly-hallows-part-1/positivas
git add finetune\c22\fallback finetune\c22\regeracao
git commit -m "c22: fallback nos 16 pendentes e nova geracao do bucket reprovado (resultado real)"
git push origin finetune
```
Esperado na linha do `regerar`: `passa=True` (validadores + nenhum `quantidade_pendente`). **⏸ PARE** — avise o Claude.

**5. (Mac) Saída de produção do C22**
```bash
cd ~/Downloads/espectro-24-finetune && git pull
../espectro-24/venv/bin/python scripts/finetune/c22_fallback.py aplicar
```
Mostra quantos fallbacks foram aceitos/recusados, se o Harry Potter voltou (`c22_regerado`) ou fica fora
(`c22_regeracao_reprovada`) e quantos bullets seguem pendentes.

**6. (Mac) Documento de leitura: re-leitura dos buckets do C6 trocados + 3 lotes de 10**
```bash
../espectro-24/venv/bin/python scripts/finetune/c22_leitura.py lotes
```
Gera `docs/arquivo-de-estudos/finetune-c22/leitura_lote_{1,2,3}.md`, `leitura_lotes_respostas.csv` e `leitura_fora.json`.
**⏸ PARE** — o dono lê. Primeiro, **só se o fallback mudou** `american-sniper/positivas` e/ou `the-simpsons-movie/positivas`:
a seção RE-LEITURA do lote 1 (se o dono responder N, o filme sai dos aprovados). Os lotes de 10 vêm depois.

**7. (Mac) Montar o `resultado/<slug>.json` + rotulagem (Featherless, dentro do teto) — dos 5 do C6 primeiro**
`scripts/montar_resultado_c22.py` (a construir quando 5 existir; usa `montagem_offline.montar_documento` com a síntese de
`finetune/c22/producao/` e a ficha de `resultado/c22-publicacao/cache_tmdb`; `FEATHERLESS_SESSION_DIR` com teto
US$ 0,50 total, custo por estágio em `resultado/c22-publicacao/custo.json`). **⏸ PARE** antes de qualquer chamada paga.

**8. (Mac) Condições (R13 + validadores) e leitura do dono das condições** — mesmo caminho dos 29
(`condicoes.gerar` + `publicar_condicoes.aplicar_retiradas`). **⏸ PARE.**

**9. (Mac) Publicar os 5 do C6; depois cada lote aprovado** — slugs em `dados/publicados.json`, `python3
frontend/build_data.py`, `python3 frontend/build_indice.py`, `pytest`, e **subir `SPEC_VERSION` no commit do primeiro filme
com `quantidade_fallback`**. **⏸ PARE antes do push** (publicação só pelo git; o hook roda `test_publicacao_consistente`).

**10. (Mac) Verificação no ar**
```bash
curl -s https://espectro-24-eu6z.vercel.app/js/indice.js | grep -c '"slug"'      # 128 + N
for s in <slugs>; do curl -s -o /dev/null -w "$s %{http_code}\n" https://espectro-24-eu6z.vercel.app/data/$s.json; done
```

## Custo (US$, teto total 0,50)
Gasto até agora nesta rodada: **0,00** (TMDB e fallback não custam; nenhuma chamada paga foi feita). ESTIMADO ≤ 0,0139 por
filme com os três estágios pagos (mediana 0,0117, 49 filmes de 08/11, sem desconto de cache) ⇒ ≤ 0,49 para 35 no pior
caso; com a síntese local, rotulagem + condições devem ficar bem abaixo. Parar se a soma real passar de 0,50.
