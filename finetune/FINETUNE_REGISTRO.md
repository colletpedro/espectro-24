# FINETUNE_REGISTRO — fase 0: inventário e desenho (2026-10-20)

**Objetivo.** Ajustar (LoRA/QLoRA) um modelo local que substitua o DeepSeek na
SÍNTESE (os bullets — `buckets[].temas` — por bucket). Esta fase não treinou,
não rodou modelo e não fez chamada paga: é inventário, reconstrução e desenho.

Cada número traz a etiqueta **MEDIDO** (contado/lido nesta sessão),
**ESTIMADO** (projeção) ou **PROPOSTO** (escolha a decidir).

Scripts (todos em `scripts/finetune/`, destino: `main`): `_guarda.py`,
`comum.py`, `inventario.py`, `reconstruir_sintese.py`, `_remontar_epoca.py`,
`dividir.py`, `poder.py`, `estimar_limpeza.py`, `viabilidade_ollama.py`,
`baixar_tokenizers.py`, e no fechamento do gate 0 `metricas.py`,
`limpar_treino.py`, `kaggle/montar_dataset_smoke.py`,
`kaggle/kernel/{smoke_treino.py,kernel-metadata.json}`. Dados (destino:
branch `finetune`, pasta `finetune/`): `inventario.{json,md}`,
`reconstrucao.{json,md}`, `split.{json,md}`, `poder.{json,md}`,
`limpeza.{json,md}`, `par_exemplo/`, `CRITERIO_ESCOLHA_BASE.md`,
`metricas/palavras_quantidade.txt`, `kaggle/smoke_dataset/`,
`limpeza/entrada{.jsonl,_meta.json}`.

Scripts novos de 2026-10-22 (`main` `d6456c87162b0699dffea48a87b7f97563db4822`; filtro de comprimento em `9e5692fcc3f0fb57270e2d06074bea9b293b820c`): `_latencia.py` (guarda de
latência do juiz), `conjunto_limpo.py`, `kaggle/montar_dataset_smoke_qwen3.py`,
`kaggle/kernel_qwen3/kernel-metadata.json`; revistos: `kaggle/kernel/smoke_treino.py`,
`viabilidade_ollama.py`, `limpar_treino.py`, `comum.py`, `baixar_tokenizers.py`.

## Invariantes

1. A unidade é o FILME. Nenhum filme de teste entra no treino em estágio
   nenhum, nem agora nem depois. Filme publicado depois deste split vai para o
   treino (PROPOSTO); o teste está congelado em `split.json`.
2. O teste contém os 5 da referência: anatomy-of-a-fall, incendies,
   mother-2017, napoleon-2023, the-substance.
3. `resultado/*.json` é só leitura (manifesto sha256 antes e depois, idêntico).
4. Nenhuma chamada a DeepSeek, Gemini, Anthropic ou TMDB: `_guarda.py` recusa
   rodar com chave no ambiente, troca `load_dotenv` por um erro e bloqueia todo
   socket que não seja loopback (MEDIDO: `detect_provider` → `ProviderError`,
   `deepseek_client_call` → `LLMError`, conexão externa → `RedeBloqueada`).
5. gpt-oss é proibido como base: o juiz é o gpt-oss:20b.
6. Nenhum bucket é "aparado": se o alvo de um bucket for rejeitado, sai o
   bucket inteiro — nunca um bullet (o número de bullets por grupo é parte do
   que se ensina).

## a) Inventário (MEDIDO, `inventario.md`)

100 JSONs publicados. Excluídos de TODOS os conjuntos (PROPOSTO):
`obsession-2025` (família obsession-*: o corpus começou como o do curta
`obsession-2026` e foi migrado em v1.9.50, ABERTO C13; o gabarito humano ainda
tem 6 reviews do curta) e `como-fazer-um-curta-metragem-…` (JSON de v1.1.3, os
3 buckets `sem_analise`, 0 chamadas de síntese, sem nenhum outro estágio).
Os 55 filmes C22 não têm `resultado/*.json`: zero exemplos.

Tokens com os tokenizers reais (revisões fixadas; o `tokenizer.json` do Gemma
4 E4B e do 12B é o MESMO arquivo, sha256 `cc8d3a0c…`, então as contagens são
iguais). Template montado à mão a partir do `chat_template.jinja` de cada repo,
raciocínio desligado. Alvo da síntese = publicado em JSON indent=2 (formato
PROPOSTO). Entrada/saída: mediana / p90 / p99 / máx.

| estágio | exemplos (filmes) | Qwen3.5-9B entrada | saída | Gemma 4 (E4B=12B) entrada | saída |
|---|---|---|---|---|---|
| síntese (bucket) | 293 (98) | 5820 / 7771 / 12437 / 21733 | 674 / 731 / 780 / 922 | 5855 / 7817 / 12585 / 21976 | 687 / 743 / 793 / 929 |
| narrativa | 98 (98) | 3334 / 3453 / 3648 / 3648 | 380 / 418 / 457 / 457 | 3358 / 3478 / 3682 / 3682 | 382 / 422 / 456 / 456 |
| veredito | 79 (79) | 1221 / 1237 / 1347 / 1347 | 66 / 76 / 78 / 78 | 1227 / 1244 / 1353 / 1353 | 66 / 76 / 79 / 79 |
| condições | 96 (96) | 3810 / 4051 / 4524 / 4524 | 278 / 328 / 397 / 397 (ESTIMADO) | 3858 / 4111 / 4564 / 4564 | 289 / 342 / 409 / 409 |
| classificação (consenso) | 12.976 reviews (98) | 1034 / 1211 / 1756 / 14509 | 31 / 43 / 56 / 66 | 1031 / 1208 / 1756 / 14700 | 31 / 45 / 57 / 69 |
| classificação (gabarito humano) | 94 de 100 (32) | 1017 / 1329 / 2213 / 2213 | 29 / 56 / 66 / 66 | 1012 / 1331 / 2149 / 2149 | 29 / 57 / 69 / 69 |

Os prompts de narrativa, veredito e condições são os do código ATUAL sobre o
publicado (capturados sem chamar modelo); os da época podem diferir (ESTIMADO).
A saída de condições é montada do publicado, que passou por leitura humana.

**Contexto necessário (síntese, PROPOSTO).** Uma review de 66.674 caracteres
faz de `500-days-of-summer/positivas` um outlier (21.976 tokens de entrada; o
segundo maior tem 13.159).
- Treino: `max_seq_length` **14.336** cobre os 180 exemplos de treino; 12.288
  derruba 2 (`pinocchio-2022/negativas`, `satantango/positivas`); 8.192
  derruba 26.
- Inferência (`num_ctx`): (entrada + teto de produção de 3.000) × 1,10 →
  **18.432** cobre 292/293 buckets; **27.648** cobre todos, inclusive o outlier
  — que caiu no TESTE.

**Filmes sem estágio** (fora os excluídos): 19 sem bloco `veredito`
(burning-2018, drive-my-car, force-majeure-2014, get-out-2017,
guillermo-del-toros-pinocchio, happy-hour-2015-1, hard-to-be-a-god,
memories-of-murder, neighboring-sounds, pinocchio-2022, satantango,
speak-no-evil-2022, the-cloud-capped-star, the-second-mother, the-turin-horse,
the-wailing, whiplash-2014, woman-of-fire, zama); 2 sem `condicoes`
(a-brighter-summer-day, woman-of-fire).

**Bullets.** `MAX_TEMAS = 6` em `src/espectro24/config.py:562` é TETO, não
número fixo: o prompt pede "no máximo" (`synthesize.py:113`) e o código corta
(`synthesize.py:2098`). Na prática: 292 buckets com 6 e 1 com 5; por filme,
96 com 18, 1 com 17, 1 com 12 (`a-brighter-summer-day`, cujo bucket Gemini sai).

**Lote e época** (commit em que os temas publicados apareceram, por `git log`
de cada JSON; o alias `deepseek-v4-flash` vai para o V4.1-Flash desde
2026-09-10 04:00 UTC, `preco.TABELA_VIGENTE_DESDE`):

| lote | commit | data | professor | filmes |
|---|---|---|---|---|
| republicacao-3 | d0dee5159 | 2026-08-16 | V4-Flash | 3 |
| catalogo-35 | 31c463528 | 2026-08-22 | V4-Flash | 31 |
| obsession-migracao | 0a777c3e2 | 2026-09-08 | V4-Flash | 1 (excluído) |
| expansao-53 | 1253eb73d | 2026-09-14 | V4.1-Flash | 19 |
| fallback-conteudo | 594786f55 | 2026-09-14 | V4.1-Flash (+1 bucket Gemini) | 1 |
| expansao-99 | 7d2fa09eb | 2026-09-17 | V4.1-Flash | 44 |
| demo-v1.1.3 | b3f3f732c | 2026-07-20 | nenhum | 1 (excluído) |

**Pendências de identidade/corpus.**
- `talk-to-me-2022`: identidade `validada` (tmdb 1008042, Philippou, 95 min).
  O erro de C1 era a FICHA; a síntese não lê a ficha. No corpus analisado,
  44/119 reviews têm termo do longa de 2022 e 0 do homônimo de 2007 (sinal, não
  prova). **Fica** (treino).
- 33 filmes (fora os excluídos) não têm bloco `identidade`: a guarda v1.9.49
  nunca rodou no artefato. Entre eles estão 4 dos 5 da referência. Excluí-los
  esvaziaria o teste; a pendência afeta a ficha (narrativa, veredito,
  condições), não a síntese. Ver decisão 3.
- `spider-man-across-the-spider-verse`: o bloco `eixos` não reconcilia com o
  consenso verificado de hoje numa célula (positivas/impacto_emocional: 16
  contado × 17 publicado). É da classificação (ABERTO C3), não da síntese.

## b) Reconstrução do par da síntese (MEDIDO, `reconstrucao.md`)

1. **Fonte primária: não existe.** 1.960 arquivos de texto varridos (árvore
   principal, `dados/lote`, logs, o worktree), 0 com o prompt ou o cabeçalho
   da mensagem. `synthesize_bucket` guarda só os temas pós-processados;
   `publicacao_log.jsonl` guarda o stdout renderizado e a telemetria de
   transporte, não o prompt nem a resposta crua.
2. **Reconstrução byte a byte: SIM, contra o código e o dado da época.**
   294/294 buckets (98 filmes) com `system` e `user` de sha256 idêntico entre o
   código atual e o `src/` exportado de cada commit de síntese (5 commits),
   com o bruto conferido blob a blob igual ao de HEAD (`reviews.jsonl` e
   `meta.json`), e a `coleta` que alimenta a seleção igual. O template
   (`build_system_prompt`, `build_user_message`, `MAX_TEMAS`) não muda desde
   2026-07-19. Seleção: n e composição iguais ao publicado em 294/294;
   o bloco `eixos` reconcilia célula a célula em 97/98 filmes (2.910 células).
   **Limite:** é igual ao que o código da época GERARIA; não há registro do que
   foi ENVIADO para comparar. E, se a retentativa de idioma/escopo disparou, o
   `system` enviado foi o prompt + `_REFORCO_VALIDACAO` — isso não foi gravado
   (frequência NÃO MEDIDA).
3. **O publicado NÃO é a saída crua.** Entre a resposta e o JSON:
   `_construir_temas` corta em 6, faz clamp de `mencoes_aproximadas` em [0, n],
   remove aspas mecanicamente (com a contrabarra de escape), sobrescreve
   `n_reviews_analisadas` com o n real e reordena por menções; uma retentativa
   com reforço se idioma/escopo falharem; `bucket` e o JSON são reserializados.
   Não há verificador, filtro nem best-of-N na síntese (1 amostra, temperatura
   padrão, modo JSON, raciocínio desligado). Medido nos 293 buckets: aspas
   removidas em 3 temas (2 buckets), clamp 0, `idioma_invalido` 0,
   `escopo_suspeito` 0. Lado a lado: `eighth-grade/negativas`, "Diálogos
   artificiais e repetitivos" — o cru tinha aspas em torno de palavras citadas;
   o publicado ficou "…muletas linguísticas como tipo e gucci…" (as posições
   das aspas não foram gravadas).
4. **Validadores mecânicos atuais**: o publicado passa em 293/293 (idioma,
   escopo, sem aspas, menções em [0, n], ≤ 6 temas, ordem decrescente,
   `n_reviews_analisadas` = n, campos não vazios, regra 3 do prompt "sem tema
   de menção única", flags publicadas). A resposta crua passaria em 291/293
   (as aspas de `eighth-grade/negativas` e `wicked-2024/positivas`).
5. **Proposta (decisão 4):** alvo = **publicado** (passa em todas as regras de
   hoje; o cru ensinaria aspas em 2 buckets, e o cru exato nem existe);
   prompt = **template atual**, que é byte a byte o da época. O que se perde:
   o modelo não aprende o caminho do reforço (que fica no código, como hoje).

Par completo para leitura (filme de TREINO, fora os 5):
`finetune/par_exemplo/whiplash-2014__negativas.{md,json}`.

## c) Divisão por filme (`split.json`, PROPOSTO)

Semente 20261020; estratos = época do professor (V4/V4.1) × tercil de tokens
de entrada da síntese × perfil (`aclamado` × demais: o equilíbrio entre os
buckets). Proporcional, os 5 fixos descontados.

| conjunto | filmes | exemplos | bullets |
|---|---|---|---|
| treino | 60 | 180 | 1.079 |
| validação | 8 | 24 | 144 |
| teste | 30 | 89 | 534 |

**Tamanho do teste: 30, não 20** (`poder.md`, ESTIMADO). Base 2/90 = 2,2% sem
apoio, 18 bullets por filme, α 0,05 bilateral, poder 0,80, filme como cluster.
ICC medido na referência (ANOVA, 10 clusters, 9 eventos): 0,023.

| filmes de teste | menor aumento detectável, analítico com ICC 0,023 (DEFF 1,39) | simulado, bootstrap por filme, r = 0 | horas de juiz (3 lados) | reaproveitando o publicado dos 5 |
|---|---|---|---|---|
| 20 | +5,3 pp | +4,2 pp | 24,0 h | 22,0 h |
| 25 | +4,6 pp | +3,8 pp | 30,0 h | 28,0 h |
| 30 | +4,0 pp | +3,3 pp | 36,0 h | 34,0 h |

A diferença qwen3:14b − publicado foi +4,4 pp: só 30 filmes a detectam no
cálculo conservador. O teste simulado tem erro tipo I de 5–9% (anti-
conservador). O teste sorteado tem 534 bullets → 35,6 h (3 lados), 33,6 h
reaproveitando o publicado dos 5. Parar no 2º "sim" (preserva "apoio ≥ 1" e
"apoio ≥ 2") economiza 36% (MEDIDO na referência) → ~22,8 h.

**Reaproveitar a medição do publicado nos 5:** pode, se (i) o
`config_sha256` for `44606cf1…` (MEDIDO: é) e (ii) a entrada do juiz for a
mesma — os mesmos bullets publicados (sim, `resultado/` não muda) e o mesmo
top-5 da recuperação, que é centrada nos bullets publicados do catálogo fora
do C22: publicar filme novo fora do C22 muda a referência e o top-5. Conferir
pelo sha256 das 450 linhas de `juiz_entrada.jsonl` antes de reaproveitar.

Atenção: o teste tem o outlier (`500-days-of-summer`, exige `num_ctx` 27.648) e
`a-brighter-summer-day` (o bucket Gemini não tem lado "publicado DeepSeek").
30 reviews do gabarito humano estão em filmes de teste (lista em `split.json`):
nunca treinar classificação nelas.

## d) Modelo base (consultado em 2026-10-20)

| | Qwen3.5-9B | Gemma 4 12B | Gemma 4 E4B |
|---|---|---|---|
| repo | `Qwen/Qwen3.5-9B` (`qwen3_5`, 9,65 B com visão, `lm_head` não amarrado) | `google/gemma-4-12B-it` (`gemma4_unified`, 11,96 B) | `google/gemma-4-E4B-it` (`gemma4`, 8,0 B com PLE) |
| licença | Apache 2.0, sem gate | Apache 2.0, sem gate | Apache 2.0, sem gate |
| Unsloth em T4 | **o guia desaconselha QLoRA 4-bit no Qwen3.5, denso inclusive**; bf16 LoRA do 9B = 22 GB (> 16 GB da T4, que nem tem bf16); exige transformers v5; kernels Triton/Mamba lentos de compilar, "especialmente em T4" | listado como treinável; **sem número de VRAM nem notebook** | QLoRA recomendado ("E4B QLoRA rather than E2B LoRA"); 10 GB (intro) × 17 GB LoRA (quickstart), conflito no próprio guia; bug fp16/T4 só no áudio; bug `use_cache=False` em E2B/E4B dado como corrigido |
| VRAM QLoRA a 14k (ESTIMADO) | ~11–13 GB (pesos 4-bit ~4 GB + embedding e `lm_head` 16-bit ~4 GB + ativações) — mas contra a recomendação | ~11–13 GB (pesos ~5,5 GB + embedding 2 GB + ativações ~3 GB): marginal em 15 GB | ~12 GB (âncora do Unsloth + ativações) |
| GGUF Q4_K_M (Unsloth) | 5,68 GB | 7,12 GB | 4,98 GB |
| Ollama | tag `qwen3.5:9b` existe; import de GGUF `qwen35` do HF: relatos (sem data) de `unknown model architecture` e erro 500 — **não confirmado** | tag `gemma4:12b-it-q4_K_M` (8,0 GB); `hf.co/unsloth/gemma-4-12B-it-qat-GGUF` documentado | tag `gemma4:e4b-it-q4_K_M` (6,6 GB); a falha de GGUF ajustado do E4B no Ollama **não foi achada** em fonte primária (o changelog do Unsloth registra re-upload dos GGUF do Gemma 4 por correções do llama.cpp) |
| raciocínio desligado | treino: `enable_thinking=False` (bloco `<think>\n\n</think>\n\n` vazio); Ollama: `think: false` | padrão do template já é desligado (sem `<|think|>`); Unsloth: template `gemma-4` (não `gemma-4-thinking`); Ollama: `think: false` | idem 12B |

Fontes: unsloth.ai/docs/models/qwen3.5/fine-tune, unsloth.ai/docs/models/gemma-4/train,
unsloth.ai/docs/new/changelog, ollama.com/library/gemma4/tags, ollama.com/library/qwen3.5,
huggingface.co/api/models/* (2026-10-20), huggingface.co/unsloth/Qwen3.5-9B-GGUF/discussions/4.

**Teste de viabilidade no Windows** (`viabilidade_ollama.py`, preparado, NÃO
rodado): carrega `hf.co/unsloth/<repo>-GGUF:Q4_K_M` (tag da biblioteca só com
`--fallback-biblioteca`), manda o prompt de `do-the-right-thing/negativas`
(treino, 7.770–7.817 tokens = p90) com `num_ctx` 18.432 (e 27.648 com
`--tambem-ctx-maximo`), `num_predict` 3.000, `think=false`; mede tempo,
tokens/s, pico de RAM/VRAM/working set do Ollama, se o JSON parseia; reinicia
o Ollama entre candidatos; aborta com RAM livre < 2 GB; recusa filme que não
seja de treino e recusa rodar dentro do Claude Code. Disco: ~18 GB (os 3
GGUF) + ~21 GB se usar as tags de fallback.

## e) Limpeza do treino com o juiz v2.2 (`limpeza.md`, ESTIMADO)

- Juiz completo nos 60 filmes de treino: 1.079 bullets × 5 pares × 16 s =
  **24,0 h**.
- **Parar no 1º "sim" na ordem de similaridade dá a MESMA decisão "sem
  apoio"** (lido no código): sem apoio = `n_apoio == 0`
  (`checagem_bullets.apoio_por_bullet`/`resumo`); cada par é uma chamada
  independente, com seed fixa e sem estado (`juiz_bullets_v2.rodar`), e
  `vereditos` recalcula o apoio de cada par só do trecho e do texto dele.
  REGISTRO (gate-local): "sem apoio quer dizer sem apoio nas 5 mais
  parecidas". Bullet sem apoio é julgado nos 5 pares nas duas variantes.
  Ressalva NÃO MEDIDA: a ordem das chamadas muda o reaproveitamento de
  prefixo no KV do Ollama, o que pode mexer na numérica do servidor; isso
  afeta o juiz completo do mesmo jeito.
- Economia, MEDIDA na referência (lado publicado): 1º "sim" na posição
  1: 64, 2: 17, 3: 5, 4: 2, nenhum: 2 → 131 de 450 pares (−71%) → **7,0 h**.
- Regra do bucket inteiro: na referência, 2 de 15 buckets publicados têm algum
  bullet sem apoio (13%, IC95 3,7–37,9%) → **~24 de 180 exemplos** saem
  (faixa 7–68).

| opção | horas de Windows | exemplos perdidos |
|---|---|---|
| filtrar tudo (60 filmes) | 7,0 h (24 h sem parada) | ~24 (7–68) |
| filtrar parte: só a época V4-Flash (20 filmes; recorte PROPOSTO) | 2,3 h | ~8 |
| não filtrar | 0 h | 0 (~24 bullets sem apoio ficam no alvo) |

Antes do juiz, a recuperação (top-5 por e5, no Mac) dos 1.079 bullets —
tempo NÃO MEDIDO.

**Risco declarado:** limpar com o juiz e avaliar com o mesmo juiz pode ensinar
as preferências dele (o modelo aprende a escrever bullets que o gpt-oss:20b
aprova). Os filmes são diferentes, então não há vazamento de dado; é viés a
declarar ao ler o resultado do teste.

## f) Plataforma (PROPOSTO: Kaggle Notebooks; Colab de fallback)

Documentação do Kaggle (kaggle.com/docs/notebooks, 2026-10-20): 12 h por
sessão de CPU/GPU (9 h TPU); "Save & Run All" roda em segundo plano e precisa
terminar em 12 h; T4 ×2 ou P100, 4 CPUs e **29 GB de RAM**; 20 GB salvos em
`/kaggle/working` mais disco de rascunho não salvo. A cota semanal de GPU não
está na página (aparece nas configurações da conta). A T4 e a P100 não têm
bf16: treino em fp16.

Risco de disco: o merge 16-bit do 12B tem ~24 GB (do 9B, ~19 GB) — tem de ir
para o disco de rascunho, salvando só o GGUF (5–7 GB) em `/kaggle/working`.

**Privacidade:** o dataset do Kaggle terá reviews de terceiros do Letterboxd →
dataset e notebook PRIVADOS. Nota: o repositório `colletpedro/espectro-24` é
PÚBLICO (MEDIDO, `gh repo view`), e `dados/bruto` já tem essas reviews; o
`par_exemplo/` as repete.

## Termos de uso (registro para o dono, que já decidiu; sem parecer jurídico)

Textos arquivados em `docs/arquivo-de-estudos/finetune-fase0/termos/` (fora do
git), consultados em 2026-10-20:
- **DeepSeek Open Platform Terms of Service** (cdn.deepseek.com/policies/en-US/
  deepseek-open-platform-terms-of-service.html; HTML sha256 `2b433c53…`):
  "Release date: April 22, 2026", "Effective date: April 29, 2026" — é a
  versão que a URL serve hoje. §4.2(3): pode-se aplicar Inputs e Outputs a
  usos que incluem "training other models (such as model distillation)".
- **Gemini API Additional Terms of Service** (ai.google.dev/gemini-api/terms;
  HTML sha256 `f36a70fe…`; "Last updated 2026-04-28 UTC"), seção "Use
  Restrictions": não se pode usar os Serviços para desenvolver modelos que
  concorram com eles.
- Dependência por estágio: **síntese = DeepSeek**; narrativa, veredito e
  condições = Gemini; condições revisadas = dado do dono. Também Gemini, e
  fora do alvo da síntese: o bucket `fallback_conteudo` de
  `a-brighter-summer-day`, e a classificação dos 55 C22.

## Decisões do gate 0 (20/10/2026)

Tomadas pelo dono depois do relatório da fase 0; substituem a lista de
"decisões pendentes" daquele relatório.

1. **Teste = 30 filmes**, split com semente 20261020 (`split.json`).
2. **Exclusões.** `obsession-2025` e `como-fazer-…` ficam fora de todos os
   conjuntos (já estavam fora do pool do sorteio: o split não mudou de
   composição). O bucket `a-brighter-summer-day/positivas`, sintetizado pelo
   Gemini (`fallback_conteudo`), fica fora do treino e de TODA avaliação, em
   todos os lados (publicado, base, treinado); o filme (teste) é avaliado só
   nos 2 buckets do DeepSeek. A marca está em `split.json`
   (`buckets_excluidos` e `filmes[...].buckets_excluidos`); sha256 do
   `split.json` depois da marca: `3232b2ad48178aaf19c4825aff6e17aa53a5de2ef4b15c2d19a574c0180be423`
   (antes: `579020025d64…`; treino, validação e teste idênticos).
3. **Os 33 filmes sem bloco `identidade` ficam.** Limitação registrada: a
   guarda de identidade v1.9.49 nunca rodou nesses artefatos; a síntese não
   lê a ficha, mas narrativa, veredito e condições leem.
4. **Alvo de treino = síntese publicada. Prompt = template atual** (byte a
   byte o da época, ver b).
5. **Formato do alvo.** A regra do dono é JSON compacto, salvo se o template
   do prompt mostrar ao modelo um exemplo de saída indentado — e ele mostra:
   o "Formato de saída (JSON puro)" de `build_system_prompt`
   (`synthesize.py:126-138`) é um esqueleto indentado com 2 espaços. **Vale a
   exceção: alvo indentado com 2 espaços** (`comum.serializar_alvo`, como já
   estava).
6. **Contexto.** Treino: `max_seq_length` 14.336; 12.288 se o critério de VRAM
   (E1 de `CRITERIO_ESCOLHA_BASE.md`) reprovar 14.336. Inferência: `num_ctx`
   calculado pelo código POR CHAMADA = tokens do prompt + teto de saída +
   margem, arredondado para cima ao múltiplo de 1.024. Só a regra fica
   registrada aqui; a implementação é da Fase 2.
7. **Candidatos ao modelo base:** Gemma 4 12B, Gemma 4 E4B e Qwen3-8B
   (reserva). O Qwen3.5-9B sai: o guia do Unsloth desaconselha QLoRA nele e o
   LoRA em 16 bits do 9B não cabe na T4. A escolha segue a regra
   pré-registrada em `CRITERIO_ESCOLHA_BASE.md` (commit próprio, antes de
   qualquer resultado de Kaggle ou de Windows).
8. **Limpeza:** filtrar treino E validação inteiros, parando no 1º "sim"; um
   bucket com qualquer bullet sem apoio sai inteiro. O teste NUNCA é filtrado.
   Script: `scripts/finetune/limpar_treino.py`.
9. **Avaliação parando no 2º "sim": aprovada.** O publicado dos 5 filmes da
   referência só é reaproveitado se o sha256 das 450 linhas de entrada do
   juiz (lado publicado) bater; senão, mede-se de novo.
10. **Publicação.** O branch `finetune` pode ser publicado (o conteúdo já é
    público em `dados/bruto` e `resultado/`). Dataset e notebooks do Kaggle
    são PRIVADOS.
11. **`.gitignore`.** `git ls-files docs/arquivo-de-estudos` lista 48 arquivos
    versionados, então só a subpasta `docs/arquivo-de-estudos/finetune-fase0/`
    é ignorada (a pasta inteira, não).

**Reconciliação (2c).** A reconstrução conta 294 buckets (98 filmes × 3,
inclusive o do Gemini, porque o prompt é o mesmo seja quem for o modelo); o
inventário conta 293 exemplos utilizáveis (294 − o bucket
`a-brighter-summer-day/positivas`).

## Limitação conhecida: `mencoes_aproximadas` (gate 0)

**O fato (MEDIDO por leitura do código).** O código só LIMITA
`mencoes_aproximadas` a [0, n] (`synthesize.py:2100-2103`): isso barra o
impossível, mas dentro da faixa o número é o do modelo, e ele chega ao
produto em 4 lugares:

1. **Barra e `aria-label` do bullet:** `frontend/js/filme.js:1754-1755`
   (fração x/n), `:1774` ("Mencionado em cerca de X de N reviews") e `:1776`
   (largura da barra).
2. **Quantificador e fração da narrativa**, via `fracao_pct`:
   `briefing.py:383` (ordem por menções), `:387` (`fracao_pct`), `:392`
   (número, quando o piso permite) e `:395` (faixa do quantificador).
3. **Ordem dos bullets e legendas dos eixos:** `synthesize.py:2118` (ordem por
   menções), `rotulagem.py:153` e `:167` (o tema mais "mencionado" vira a
   legenda da célula do eixo) e `frontend/js/filme.js:1605-1612` (a ordem na
   tela parte dessa ordem).
4. **`rotulo_forca` das condições:** `condicoes.py:111` e `:122` (no JSON
   publicado; fora da tela desde a v1.9.46).

Os demais campos de quantidade: `n_reviews_analisadas` é SOBRESCRITO pelo n
real (`synthesize.py:2112`); `bucket` é IGNORADO (o código usa o nome do
bucket); o número de temas é LIMITADO a 6 (`synthesize.py:2098`).

**O texto.** 863 de 1.757 `exemplo_parafraseado` (49%, todos os filmes fora
os excluídos, com o léxico de `checagem_bullets.quantificador_do_texto`) têm
palavra de quantidade, e nenhum validador da síntese olha isso; o texto
aparece no "Aprofundar" do bullet. Com a lista congelada desta fase, só no
treino: 591/1.079 (54,8%).

**A escala.** Nas 1.436 células de eixo que têm tema, o número do modelo e a
contagem do eixo divergem em ≥ 5 reviews em 765, e caem em rótulo de força
diferente em 828. **Isto NÃO prova erro do modelo:** o eixo é mais largo que o
tema e não separa elogio de crítica — são medidas diferentes.

**A contradição com o README** ("Cada número na tela é contagem de código…
nenhuma frequência é estimada… por um LLM"): é o comportamento ATUAL do
DeepSeek em produção, não algo introduzido pelo fine-tuning.

**A decisão (dono, opção A).** O alvo mantém `mencoes_aproximadas`, para que o
modelo local substitua o DeepSeek sem mudar o pipeline. Isso não cria
dependência: se o código passar a contar por tema, o campo será sobrescrito ou
ignorado sem retreino.

**Pendência de produto, FORA desta frente e decisão do dono:** opção B
(contagem por tema feita por código) e opção C (tratamento das palavras de
quantidade). Esta frente não toca README, SPEC, frontend nem código de
produto.

## Duas métricas definidas no gate 0 (limites ficam para o pré-registro da Fase 2)

Nenhuma das duas foi calculada em validação ou teste nesta fase.

**M1 — taxa de `exemplo_parafraseado` com palavra de quantidade.**
- Lista CONGELADA: `finetune/metricas/palavras_quantidade.txt`, 56
  expressões, sha256 `a7fcd5a5663c3ebdc0112b27bd8821c839d47de86673ef4ebdea83c0524c14af`.
  Montada SÓ com os 60 filmes de treino.
- Casamento: sem caixa; palavra inteira (nem letra, nem dígito, nem "_"
  antes ou depois); acento como escrito; só as flexões listadas. Formas
  ambíguas ("metade", "parte", "certos/certas") só em expressão explícita.
- M1 = (exemplos com ≥ 1 expressão) / (exemplos), por lado.
- Medida na Fase 2 e na Fase 4 no publicado, na base e no treinado, nos
  filmes de teste (`scripts/finetune/metricas.py`; hoje o script só aceita
  `--conjunto treino`).
- Referência MEDIDA só no treino (publicado): 591/1.079 = 54,8%.

**M2 — concordância de `mencoes_aproximadas`, treinado × publicado**, nos
buckets de teste (fora o excluído):
- Pareamento por bucket: cosseno e5 (`query: tema. exemplo`) entre os temas
  dos dois lados; atribuição um a um que maximiza a soma (húngaro); só pares
  com cosseno ≥ τ (τ é parâmetro da Fase 2, fixado antes de medir).
- Por bucket, com P pares (iᵏ, jᵏ): DAM = (1/P) Σₖ |m_T(iᵏ) − m_P(jᵏ)|, em
  reviews e dividida por n; τ_b = tau-b de Kendall entre (m_T(iᵏ)) e
  (m_P(jᵏ)), definido só com P ≥ 3 e variação nos dois lados.
- Agregado: média de DAM e de τ_b sobre os buckets em que são definidos, com
  a fração de temas pareados e de buckets com τ_b definido, e IC por
  bootstrap por FILME.
- **Mede a imitação do professor, NÃO o acerto da contagem:** o publicado não
  é gabarito de contagem.

## Medições preparadas no fechamento do gate 0 (quem roda é o dono)

Nada abaixo rodou nesta sessão, exceto o preparo da limpeza no Mac (recuperação
e5, sem juiz) e a montagem do dataset de fumaça. O critério que decide as
medições está commitado antes delas: `CRITERIO_ESCOLHA_BASE.md`, commit
`0466cead8e9d138ef071ca9da682ba9caff050b8` (push em `origin/finetune`).

**Kaggle — teste de fumaça (E1–E4)**: `scripts/finetune/kaggle/`.
- `montar_dataset_smoke.py` → `finetune/kaggle/smoke_dataset/smoke.jsonl`
  (sha256 `0652119bd04671eb3a74efd3dd8a73a912c1143df01b7be3ea9f5221d19ecc11`),
  só TREINO, com assert contra o split: `mais_longo` satantango/positivas
  (13.857 tokens), `mais_longo_12k` the-turin-horse/negativas (11.357),
  `mediano_1..4` cure/negativas, the-wailing/negativas, prisoners/negativas,
  pinocchio-2022/medianas (6.592–6.606; mediana do treino 6.592,5). Cada
  linha leva o texto de chat ESPERADO (`comum.chat`) para conferir o template
  no Kaggle.
- `kernel/smoke_treino.py` (code_file do kernel): Gemma 4 12B
  (`unsloth/gemma-4-12b-it`, quantizado na carga: o Unsloth não publica
  bnb-4bit do 12B) e Gemma 4 E4B (`unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`),
  cada um num subprocesso; Qwen3-8B (`unsloth/Qwen3-8B-unsloth-bnb-4bit`) só
  com `ESPECTRO24_INCLUIR_QWEN=1`, se nenhum Gemma passar. QLoRA 4-bit, r=16
  em q/k/v/o/gate/up/down, gradient checkpointing "unsloth", fp16, batch 1,
  seed 3407, só nas respostas (`<|turn>model\n` / `<|im_start|>assistant\n`),
  template sem raciocínio; 10 passos no mais longo a 14.336 (OOM → tudo de
  novo a 12.288 com o mais longo que cabe), 5 passos nos medianos; pico de
  `max_memory_reserved`, s/passo, perdas; fusão + GGUF Q4_K_M em `/tmp`
  (fora dos 20 GB de `/kaggle/working`), com tempo, pico de RAM, tamanho,
  sha256 e Modelfile; versões de unsloth/transformers/trl/torch/peft e o
  ambiente `KAGGLE_*` (sem segredos) em `log.json`.
- `kernel/kernel-metadata.json`: `is_private: true`, `enable_gpu: true`,
  `enable_internet: true` (pip, Hugging Face, build do llama.cpp),
  `machine_shape: "NvidiaTeslaT4"`. O CLI atual só oferece T4 ×2 com esse
  valor (kaggle-api `docs/kernels_metadata.md` e `docs/kernels.md`,
  2026-10-20): a "T4 única" do E1 é imposta por `CUDA_VISIBLE_DEVICES=0`.
- Cota estimada (ESTIMADO, nada medido): instalação ~10 min; 12B (download de
  ~24 GB + quantização na carga) ~20 min; 10 passos a 13,9 mil tokens numa
  T4 ~10–30 min; medianos ~5 min; llama.cpp + fusão + Q4_K_M ~30–50 min; o
  E4B em cerca de metade disso → **~2–4 h de GPU** (a sessão inteira conta,
  inclusive a parte de CPU). A cota semanal não está na página de docs
  (aparece em Settings da conta) — NÃO CONFIRMADA em 20/10; MEDIDA em 22/10
  com `kaggle quota`: GPU **30,00 h/semana**, 0,36 h usadas, 29,64 h restantes,
  renova em 2026-10-24 00:00.

**Windows — viabilidade (E4, E5)**: `scripts/finetune/viabilidade_ollama.py`.
Candidatos `hf.co/unsloth/gemma-4-12b-it-GGUF:Q4_K_M` (7,12 GB),
`hf.co/unsloth/gemma-4-E4B-it-GGUF:Q4_K_M` (4,98 GB),
`hf.co/unsloth/Qwen3-8B-GGUF:Q4_K_M` (5,03 GB); fallback na biblioteca
(`gemma4:12b-it-q4_K_M`, `gemma4:e4b-it-q4_K_M`, `qwen3:8b`). `medir`: o prompt
p90 de treino a 18.432 (registra `E5_ate_20_min`) e o probe de memória a
27.648 (`num_predict` 16; não eliminatório). `importar`: confere o TEMPLATE do
Modelfile do Unsloth contra o canônico (o template do HF sem raciocínio, em Go
template), corrige e registra o diff se não reproduzir, `ollama create`,
compara o `prompt_eval_count` via template × texto cru esperado, e mede como
em `medir` (registra `E4_importa_e_gera`). Mantidos: recusa de filme de
teste/validação, reinício do Ollama entre candidatos, guarda de RAM livre
≥ 2 GB, recusa dentro do Claude Code.

**Windows — limpeza (decisão 8)**: `scripts/finetune/limpar_treino.py`.
`preparar` (Mac, rodado), `medir-contexto`, `julgar`, `resumir` (Windows).
Confere `config_sha256` = `44606cf1…` ao iniciar e usa `J.rodar` sem
alteração (retomável por par). A lógica de parada foi conferida na medição de
referência: com as 900 respostas reais do juiz, o estado "sem apoio" sai
igual ao do juiz completo em 180/180 bullets (MEDIDO). Reinício do Ollama a
cada 10 filmes se o working set cresceu > 25% (justificativa no script).
- `preparar` rodou no Mac (MEDIDO, 1.928 s): 68 filmes (60 treino + 8
  validação), 1.223 bullets, 6.115 pares em `finetune/limpeza/entrada.jsonl`
  (sha256 `11b5d44ff6d4601c6971a0555d3c53fd7bc79f441f1a9d3c0789934f1642744b`);
  centragem pelos 1.780 bullets publicados do catálogo menos os do próprio
  filme (a regra da referência, que excluiu os 5 filmes medidos); e5
  `d1287505…`, pesos `a18a44fa…`.
- **24 pares (23 bullets) não cabem** na janela congelada do juiz pela cota
  de 0,35 token/caractere (ESTIMADO): são pulados; o bullet segue para o
  próximo posto, e só fica `indeterminado` se nenhum par julgável der "sim".
  PROPOSTO: bucket com bullet indeterminado também sai
  (`resumir --indeterminado-fica` muda).
- Custo ESTIMADO no Windows: 1.223 × 1,456 pares/bullet × 16 s ≈ **7,9 h**
  (mais ~10 min de `medir-contexto`).

## Pré-voo do Kaggle (2026-10-20)

**Documentação** (kaggle.com/docs/notebooks, consultada em 2026-10-20):
`/kaggle/working` = 20 GB salvos ("auto-saved disk space"); o disco
temporário é só "Additional scratchpad disk space (outside /kaggle/working)
that will not be saved", **sem tamanho declarado** (nenhuma fonte oficial dá o
número; o script mede com `df -h`); máquina T4 ×2 = 2 × T4, 4 CPUs, **29 GB de
RAM**; sessão de 12 h.

**Pesos sem token (MEDIDO):** `unsloth/gemma-4-12b-it` (sha `55cdba07…`),
`unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` (`6f10b2aa…`) e
`unsloth/Qwen3-8B-unsloth-bnb-4bit` (`62efd7f9…`): `gated: False`,
Apache 2.0, `config.json` baixa sem token (HTTP 200). `kernel-metadata.json`:
`is_private: true`, `enable_internet: true`.

**`smoke_treino.py` revisado** (`main` `621977e4…`, KAGGLE LIBERADO): E4B antes
do 12B, cada um no seu try/except; cache do HF, `cwd` (llama.cpp e cache de
compilação do Unsloth), fusão 16-bit e GGUF intermediário em
`/tmp/espectro24_smoke`; em `/kaggle/working` só Q4_K_M, Modelfile, adaptador
LoRA e logs; E1–E3 gravados com fsync antes de exportar; adaptador salvo antes
da fusão; linha do tempo de RAM/disco por fase (carga, treino, fusão,
conversão) a cada 2 s e `df -h` em cada troca. A exportação é sempre tentada
(a estimativa de disco é só registro), para que uma falha deixe a causa
demonstrada no log.

**Adendo ao critério** (`CRITERIO_ESCOLHA_BASE_ADENDO.md`, commit próprio
`f49c21350cc2a1b287b859207074a712937fdbf6`): E4 pelo caminho alternativo
(adaptador do Kaggle, fusão e Q4_K_M no Mac com llama.cpp) se a exportação
cair por limite da plataforma. MEDIDO no Mac: 16,0 GiB de RAM, **5,5 GiB de
disco livre**, sem llama.cpp — a fusão em memória do 12B não cabe e a
tensor a tensor precisa de ~60 GB de disco: o caminho alternativo é inviável
no Mac até liberar disco.

## Fase 1 — medida de especificidade (desenho e calibração)

**Objetivo.** Separar, por código e sem LLM, bullet GENÉRICO de ESPECÍFICO, para
funcionar nas saídas de modelo local (a régua de fidelidade não pega bullet
genérico). Unidade: o título. Definição: GENÉRICO = o título caberia, sem
mudança, em bullets de muitos filmes diferentes; ESPECÍFICO = só faz sentido
para este filme ou para poucos.

**Pré-registro.** `finetune/especificidade/PROTOCOLO.md`, commit próprio
`fe7d7a02f271729913eef1886a8298edaa5f165d` (sha256 do arquivo `3568d4ef…`),
ANTES do documento de rotulagem. Código: `scripts/finetune/especificidade.py`
(sha256 `7d40e620…`, `main` `a3807be4…`).

**Referência congelada.** `finetune/especificidade/referencia.jsonl`, sha256
`92e4f2f0e98c63ee62c6310338181ec66921fcde6b08112e05bcd190156fcb44`: 1.223
títulos publicados de 68 filmes (1.079 treino, 144 validação), sem o bucket do
Gemini e sem os filmes excluídos. Sem teste, sem saída de modelo; toda medida
sem o próprio filme do item.

**Medidas.** M-disp (e5 com `query:` dos dois lados e a correção de viés do
juiz; média dos 10 maiores máximos por OUTRO filme; alto = genérico) — a forma
"média dos k maiores" foi escolhida contra a contagem acima de τ porque τ seria
um segundo parâmetro livre ajustado nos mesmos rótulos. M-anc (máximo, nas
palavras de conteúdo do título, de presente nas reviews analisadas do próprio
filme × idf entre os outros filmes; alto = específico). M-comb (logística
ponderada com as duas). Fórmulas completas no protocolo.

**Calibração preparada.** 80 títulos de TREINO, 20 por quartil de M-disp no
pool de treino (quartis 270/270/270/269 → pesos 13,5/13,5/13,5/13,45), semente
20261021, mais 10 repetidos a ≥ 41 posições do original: **90 itens**.
Documento cego `docs/arquivo-de-estudos/finetune-fase1/rotulagem_calibracao.md`
(fora do git; só id e título), respostas em branco em `rotulos_calibracao.csv`
(mesma pasta), mapa em `finetune/especificidade/mapa/calibracao_mapa.json`
(selo `2bcbf74376ad28c1d41b9de50e5a8dd6777a52cbe34a01d01f92050bb2fdf3a2`,
impresso no fim do documento; só o quartil, nenhum valor de medida). Nenhuma
medida foi calculada sobre os itens sorteados (o M-anc não rodou em nada real).

**Depois da escolha do modelo base.** Seletor rodado: os 5 filmes de TREINO da
geração são fight-club, hereditary, pinocchio-2022, soul-2020, the-wailing
(`validacao_filmes.json`, semente 20261022). A geração
(`scripts/finetune/gerar_titulos_base.py --modelo <escolhido>`, Windows) e o
sorteio dos 60 + 6 itens da validação ficam para depois.

**Ordem combinada no Windows** (PowerShell novo, FORA do Claude Code):
1. viabilidade agora (`viabilidade_ollama.py baixar` + `medir`);
2. limpeza de madrugada (`limpar_treino.py medir-contexto` + `julgar` +
   `resumir`);
3. import do Kaggle quando a saída existir — baixada direto no Windows pelo
   Kaggle CLI (`kaggle kernels output …`) e importada com
   `viabilidade_ollama.py importar`.

## Smoke do Kaggle (20/10): diagnóstico do OOM e aplicação do critério (2026-10-22)

Insumos: `finetune/kaggle/smoke_saida/` (4 rodadas + `resumo.json` + log do kernel,
MEDIDO em 2026-10-20 20:04–20:25 UTC) e o código instalado na rodada, lido em
2026-10-22 (`unsloth 2026.10.7` e `unsloth_zoo 2026.10.7`, as mesmas versões do
`log.json`, baixadas só para leitura; nada foi executado). Ambiente MEDIDO no
log: 1 GPU (`CUDA_VISIBLE_DEVICES=0`, `dispositivos_cuda` 1), Tesla T4,
`bf16_suportado` False, torch 2.11.0+cu128, transformers 5.16.1, trl 1.15.0,
peft 0.20.0, bitsandbytes 0.50.2, xformers 0.0.35, Python 3.13.15. LoRA em
q/k/v/o/gate/up/down nas 4 rodadas (`projecoes_faltando` vazio).

**O que as 4 rodadas mediram (MEDIDO):** todas caíram por OOM de VRAM na fase
`treino_longo`. Nenhuma chegou aos medianos, ao adaptador nem à exportação:
E2, E3 e E4 desses candidatos NÃO foram medidos. O log não tem VRAM por fase
(só RAM, que ficou em 8,7–9,5 GiB de 31,35 GiB), nem o passo em que cada uma
caiu.

### Tabela do diagnóstico (MEDIDO, `log.json` → `erro`)

| rodada | exemplo (Gemma, tokens) | tentou alocar | em uso no processo | livre / total | ponto do traceback |
|---|---|---|---|---|---|
| E4B @ 14.336 | satantango/positivas, 13.857 | **5,72 GiB** | 9,91 GiB (9,58 PyTorch + 0,21 reservado-livre) | 4,65 / 14,56 GiB | **forward**, dentro do gradient checkpointing: `modeling_gemma4.py:1402 self_attn` → `unsloth_zoo/temporary_patches/gemma4_float32.py:507 scaled_dot_product_attention` |
| E4B @ 12.288 | the-turin-horse/negativas, 11.357 | **3,84 GiB** | 12,54 GiB (12,30 + 0,12) | 2,02 / 14,56 GiB | o mesmo ponto (`gemma4_float32.py:507`) |
| 12B @ 14.336 | 13.857 | 408,00 MiB | 14,37 GiB (14,03 + 0,19) | 178,81 MiB / 14,56 GiB | **backward**: `loss.backward()` → `unsloth_zoo/gradient_checkpointing.py:1635 backward` → AOT autograd `_backward_impl` → kernel do inductor `empty_strided_cuda((s27, 15360), (15360, 1), torch.float16)` |
| 12B @ 12.288 | 11.357 | 334,00 MiB | 14,30 GiB (13,69 + 0,47) | 254,81 MiB / 14,56 GiB | o mesmo; o processo ainda saiu com `rc` −11 (SIGSEGV) depois da exceção |

Tempo na fase `treino_longo` até o erro (linha do tempo de RAM): 59 s, 22 s,
124 s, 385 s. O buffer (`s27`, 15.360) em fp16 do 12B é o intermediário do MLP
(`intermediate_size` 15.360): 408 MiB ↔ 13.926 tokens e 334 MiB ↔ 11.401, 0,5%
e 0,4% acima dos 13.857/11.357 contados no Mac (diferença NÃO explicada;
possível preenchimento do shape compilado).

### A hipótese do tech lead, contra os números

Hipótese: na T4 (sem bf16) o Unsloth roda a atenção do Gemma 4 em fp32; o SDPA
cai no backend matemático, que materializa L×L; a memória cresce com L².

**Confirmada para o E4B, com exatidão (MEDIDO + conta).** Cabeças de atenção do
E4B: 8 (`num_attention_heads` 8, `num_key_value_heads` 2, `head_dim` 256,
`global_head_dim` 512; config da revisão carregada). Matriz de pontuação em
fp32, batch 1: `cabeças × L² × 4 B`.

| | L (tokens) | 8 × L² × 4 B | falhou ao alocar |
|---|---|---|---|
| E4B @ 14.336 | 13.857 | **5,723 GiB** | 5,72 GiB |
| E4B @ 12.288 | 11.357 | **3,844 GiB** | 3,84 GiB |

Alternativas descartadas pela mesma conta: fp16 daria 2,861 e 1,922 GiB; a
máscara aditiva fp32 L×L daria 0,715 e 0,480 GiB. Só 8 × L² × 4 B bate, nos
dois comprimentos (razão 5,723/3,844 = 1,489 = (13.857/11.357)², como L² manda).

**Backend de SDPA usado: matemático (INFERIDO da alocação; o log não registra o
backend).** Um kernel mem-efficient ou flash nunca aloca L×L; alocar
`cabeças × L² × 4 B` é o que o backend matemático faz. Por que o seletor cai
nele (LIDO no código, não observado em execução):

1. **dtype:** `gemma4_float32.py` converte q, k e v para fp32 explicitamente
   (linhas 397, 406–407, 418, 422) e a máscara para fp32 (linha 486). O flash
   do PyTorch exige sm ≥ 80 e não aceita fp32 (`sdp_utils.cpp` v2.11.0:
   `check_flash_attention_hardware_support`, `check_dtypes_flash_attention`); a
   T4 é sm75. Fora o flash, sobra o mem-efficient.
2. **GQA:** a chamada passa `enable_gqa = num_key_value_groups != 1`
   (linha 515) e o E4B tem 8 cabeças de query para 2 de key/value. O
   mem-efficient não suporta GQA (`check_batch_size_and_num_heads_dense<false /*
   supports_grouped_query_attention */>` no mesmo arquivo); o `unsloth_zoo` diz o
   mesmo num comentário (`gemma4_banded_attention.py`: "enable_gqa would put
   fp32 on the math kernel"). Resultado: math.
3. **Máscara:** aditiva fp32, `is_causal` False quando há máscara (linha 487);
   por si só não tira o mem-efficient. **Softcapping de atenção:** o Gemma 4 não
   tem (`attn_logit_softcapping` ausente do `text_config`; só
   `final_logit_softcapping` 30, aplicado no `lm_head`). Não entra.
4. **O que ligou o fp32:** `loader.py` (linhas 2745–2757) põe
   `UNSLOTH_FORCE_FLOAT32=1` se o `model_type` contém `gemma4` e
   (`dtype == float16` **ou** `not SUPPORTS_BFLOAT16`). Na T4 a segunda condição
   é verdadeira sozinha: o fp32 viria mesmo sem o `fp16` do critério.
5. **Por que as camadas deslizantes também pagam L²:** o `unsloth_zoo` tem um
   roteador O(S·janela) para as camadas de janela deslizante
   (`gemma4_flash_sliding.py`, registrado em `ALL_ATTENTION_FUNCTIONS["sdpa"]`).
   O forward fp32 de `gemma4_float32.py` só usa essa tabela se `attn_impl` não
   for `sdpa`/`eager` (linhas 437–445); com `sdpa` cai no ramo SDPA cru (linhas
   483–516) e **contorna o roteador**. No E4B são 35 de 42 camadas deslizantes
   (janela 512) pagando L² sem precisar.

**NÃO confirmada para o 12B (MEDIDO).** Com 16 cabeças de query
(`num_attention_heads` 16, `num_key_value_heads` 8), a mesma conta daria
**11,445 GiB** a 14.336 e **7,688 GiB** a 12.288 numa única chamada de SDPA. O
12B não caiu aí: o forward inteiro terminou e a falha veio no backward, num
buffer de 408/334 MiB, com 14 GiB já alocados. A hipótese, estendida ao 12B,
prevê um OOM que o log não mostra. O 12B é `gemma4_unified`
(`Gemma4UnifiedForConditionalGeneration`, `num_kv_shared_layers` 0), e o log
não diz por qual caminho de atenção ele passou (a hipótese mais simples é que o
patch fp32 não tenha sido aplicado à classe unificada e ele tenha usado o
roteador padrão; NÃO verificada). O que o log do 12B prova é só: memória
esgotada no backward do MLP com ~14 GiB em uso, nos dois comprimentos.

**Observação do 12B, fora do OOM (MEDIDO):** `template_confere` deu 0/6 nas duas
rodadas do 12B (6/6 no E4B). A diferença é um canal de raciocínio vazio,
`<|channel>thought\n<channel|>`, que o template do 12B escreve antes da resposta
(+28 caracteres em 55.601) e `comum.chat('gemma')` não escreve. Não explica o
OOM; deixa de importar com o Gemma fora, mas fica registrado: o `comum.chat`
não reproduz o template do Gemma 4 12B.

### Classificação da causa

- **E4B: (a)** — propriedade do modelo nesta plataforma, sob a configuração
  fixada pelo critério. Demonstrada: a conta bate a 3 algarismos nos dois
  comprimentos e o código instalado explica cada passo (dtype fp32 forçado pela
  falta de bf16, GQA → math, roteador contornado). Nada no script o causa:
  `smoke_treino.py` não fixa `attn_implementation`, não chama `sdpa_kernel` e
  não define variável de ambiente de atenção; só pede `dtype=torch.float16`, o
  que o critério manda.
- **12B: não é (b) — não achei, no script nem na configuração, nada fora do
  critério que o explique** (QLoRA 4-bit, r=16 nas 7 projeções, checkpointing
  "unsloth", fp16, batch 1, `max_seq_length` 14.336 e 12.288, seed 3407). **Mas
  a causa (a) não está demonstrada**: o mecanismo da hipótese não foi o que
  falhou. O E1 reprova por medição, sem depender da causa: o processo esgotou
  os 14,56 GiB da T4 (14,37 em uso a 14.336) e o critério pede pico ≤ 14,0
  GiB.
- Reprodutibilidade (ressalva do script, não causa): `pip install --upgrade
  unsloth unsloth_zoo` sem versão. A rodada usou 2026.10.7; o próximo smoke
  fixa essas versões.

### Aplicação do critério (CRITERIO_ESCOLHA_BASE.md, sem alteração)

- **Gemma 4 12B reprova no E1** a 14.336 e a 12.288 (OOM; 14,37 e 14,30 GiB em
  uso de 14,56). **Gemma 4 E4B reprova no E1** a 14.336 e a 12.288 (OOM no
  SDPA; 5,72 e 3,84 GiB pedidos). A causa está demonstrada para o E4B e NÃO
  para o 12B (acima).
- Regra pré-registrada: nenhum Gemma aprovado → entra o **Qwen3-8B** (o
  critério já o nomeia como reserva e o `smoke_treino.py` o roda só nesse caso).
- **Achado:** o Gemma 4 E4B não é treinável na T4 gratuita do Kaggle com o
  Unsloth 2026.10.7, em fp16, nos nossos comprimentos (12.288 e 14.336); o 12B
  também não coube. Reabrir exige dado novo: uma correção no Unsloth (por
  exemplo o forward fp32 passar a respeitar o roteador deslizante e o GQA fora
  do math) ou uma GPU com bf16.
- **Não foi feito:** nenhum ajuste de comprimento, dtype, backend ou
  configuração para "salvar" o Gemma. Mudar qualquer um depois de ver o
  resultado mudaria o critério.

## Limpeza do treino com o juiz v2.2 (resultado, 2026-10-20/21)

Fonte: `finetune/limpeza/` (`resumo.json`, `resumo.md`, `saida_v2.2.jsonl`,
`contexto_medido.json`). Juiz `44606cf1…` (congelado). Substitui a ESTIMATIVA da
seção e).

- **Pares:** 1.863 julgados de 6.115 (parada no 1º "sim"), todos `ok`. Janela:
  20/10 22:59 → 21/10 07:22 UTC = 8,4 h de parede (16,2 s/par); latência por
  chamada: mediana 14,73 s, p90 24,86 s, máx 52,58 s. ESTIMADO era 7,9 h.
- **Bullets (1.223, 68 filmes):** `com_apoio` 1.176 · `sem_apoio` 45 ·
  `indeterminado` 2.
- **Buckets removidos: 44 de 204** — treino **39 de 180** (21,7%; a
  estimativa era ~24, faixa 7–68), validação **5 de 24**. Por época do
  professor (treino): V4-Flash 17 de 60 (28,3%), V4.1-Flash 22 de 120
  (18,3%); validação: V4-Flash 3 de 9, V4.1-Flash 2 de 15. Por bucket
  (treino): medianas 16, negativas 12, positivas 11 (de 60 cada).
- **Por filme:** 33 dos 68 filmes perdem ao menos um bucket (treino 29 de 60:
  V4-Flash 11, V4.1-Flash 18; validação 4 de 8). 23 filmes perdem 1 bucket, 9
  perdem 2, 1 perde 3 (`wonka`).
- **Pares fora da janela do juiz (24 pares, 23 bullets, cota de 0,35
  token/caractere):** 21 dos 23 bullets receberam "sim" em outro posto
  (`com_apoio`); 2 ficaram `indeterminado` e por regra conservadora o bucket
  sai: `cidade-de-deus/negativas` e `pinocchio-2022/negativas` (os dois de
  treino). Esses 2 buckets são os únicos removidos por causa dos 24 pares;
  nenhum `sem_apoio` tem par não julgável. ESTIMADO, sem medir: dos 24 pares,
  10 caberiam na janela com a pior razão medida (0,28 token/caractere,
  `contexto_medido.json`) e 18 com a menor (0,232); o par de posto 1 do
  `cidade-de-deus` tem 10.428 caracteres (caberia, pelo 0,28), o de posto 4 do
  `pinocchio-2022` tem 37.728 (não caberia). `resumir --indeterminado-fica`
  devolveria os 2 buckets ao treino (143).
- **Sobram: 141 exemplos de treino e 19 de validação** (180 − 39 e 24 − 5);
  **140 de treino** depois de tirar o `satantango/positivas` por comprimento
  (seção do Qwen3-8B).
- **RISCO CONHECIDO para a fase de treino (não bloqueio):** a limpeza removeu
  **21,7% do treino** (39 de 180), contra os **~13% ESTIMADOS** na referência
  (IC 95% 3,7–37,9%: o valor real cai dentro do intervalo, mas acima do ponto
  central). Restam 141 exemplos (140 com o filtro de comprimento) de uma base
  que já era pequena: menos dados que o planejado, e a perda não é uniforme
  (treino: V4-Flash 28,3%, V4.1-Flash 18,3%; medianas 16 de 60, negativas 12,
  positivas 11). Risco registrado para o dimensionamento do treino (épocas,
  regularização, poder da avaliação); `resumir --indeterminado-fica` devolveria
  2 buckets se for preciso (143 → 142 sem o outlier).
- **Conjunto limpo:** `finetune/limpeza/conjunto_limpo.json`
  (`scripts/finetune/conjunto_limpo.py`; a limpeza pelo juiz + o filtro por
  comprimento). `sha256_ids` =
  `ecdd5558b5881f4104ce922c1ba3dd8775184b0d5c997f5af72a60f503395438`
  (hash das linhas `conjunto|slug|bucket` dos 159 exemplos que ficam: 140 de
  treino + 19 de validação, em ordem; prende QUAIS exemplos ficaram). Sem o
  filtro de comprimento (só a limpeza, 141 de treino) o hash era
  `52debafa445935e9f4485241e4929c4b2af93c5014e791e5f9e3383e6604f2c8`.
  `sha256_conteudo` do treino (140 linhas
  `treino|slug|bucket|sha256(texto de chat do Qwen)`; prende prompt e alvo) =
  `983dd01bd611899b4153a1d1b2926c59efcd19ba101bfc8d3875d63bfaed6d4a`.
  `split.json` `3232b2ad…`, `resumo.json` `0afc947d…`.
- **A rodada correu com a guarda de RAM desligada
  (`--ram-livre-min-gb 0`), e por quê:** com o gpt-oss:20b carregado a RAM livre
  fica perto de 0,3 GB por construção, então o limite de 2 GB pararia a rodada
  inteira sem haver problema. Que não houve paginação lê-se no tempo por par:
  14,73 s de latência mediana, 16,2 s de parede por par contra a referência de
  ~16 s, e nenhuma chamada fora do padrão (simulei a nova guarda de latência
  sobre as 1.863 chamadas em ordem de `ts`: 0 disparos; a mais lenta, 52,58 s,
  é 3,6× a mediana). O que NÃO foi medido: a RAM durante a rodada (a guarda
  estava desligada e nada mais a registrou).
- **Guarda trocada** (`scripts/finetune/_latencia.py`, usada por
  `limpar_treino.py julgar`): pausa e avisa (código 3, retomável) se UMA chamada
  passar de 4× a mediana das últimas 20 chamadas. Vale com ≥ 10 chamadas na
  janela; a chamada lenta é gravada e a SEGUINTE é barrada; a anômala não entra
  na janela; a 1ª chamada depois de reiniciar o Ollama não é medida. A guarda de
  RAM saiu de `julgar`; continua no `viabilidade_ollama.py`, que mede
  memória (e não usa o juiz) e no `gerar_titulos_base.py` (Fase 1, em espera,
  modelo base — não é o juiz).

## Windows: a 1ª viabilidade (20/10) e por que o E5 do Qwen3-8B é refeito

`finetune/viabilidade/viabilidade_20261020_170533.json` (Ollama 0.40.5, RAM
15,19 GB, prompt `do-the-right-thing/negativas`):

| candidato | medição @ 18.432 (E5) | probe @ 27.648 |
|---|---|---|
| Gemma 4 12B | ok, 248,3 s (≤ 20 min), 7.821 tokens de prompt, 652 de saída; RAM livre mín. 3,58 GB; 3,88 tok/s de geração | **abortada pela guarda de RAM** (livre mín. 1,05 GB < 2,0): o `ConnectionResetError` é o servidor derrubado pelo próprio script |
| Gemma 4 E4B | ok, 100,4 s, 676 tokens de saída; livre mín. 4,92 GB; 10,89 tok/s | abortada pela guarda (livre mín. 2,00 GB) |
| Qwen3-8B | **não medido**: abortada em 5,7 s pela guarda (livre mín. 1,97 GB < 2,0) | recusada (servidor já derrubado) |

O Qwen3-8B começou sem memória livre porque o candidato anterior ainda estava
carregado (pico de RAM usada de 13,22 GB nos 5,7 s da tentativa): a medição está contaminada e não
conta. As sondas de 27.648 dos dois Gemma também morreram pela guarda, não por
falha do Ollama; são não eliminatórias e não ficam como "falhou". E4 (importar o
GGUF do Kaggle) ainda não foi medido para nenhum candidato.

`viabilidade_ollama.py` agora faz **partida limpa** antes de cada medição:
`ollama stop` em todo modelo de `ollama ps`, confirma `ollama ps` vazio, mata o
servidor, espera a RAM livre voltar a `--ram-partida-min-gb` (PROPOSTO: 6 GB,
até 90 s) e grava `partida` (RAM livre, working set, VRAM de partida). Se a RAM
não voltar, a medição NÃO roda (`partida_contaminada`, `E5_ate_20_min` nulo, não
reprovado). Novos: `--so-probe` e `importar-pasta` (acha as pastas do Kaggle
pelo `.gguf` Q4_K_M + `Modelfile`, sem supor o nome).

**Regras da repetição (decisão do dono, 2026-10-22).** Sonda de 27.648 SEM guarda
de memória: não. Se a guarda derrubar a sonda do Qwen3-8B, para-se e reportam-se
os números (`partida`, `memoria`, `abortado_por_memoria`); a guarda não é
desligada. No Windows todo Python é `.\venv\Scripts\python.exe` (o `python` do
sistema não tem os pacotes) e o repositório é `C:\espectro\espectro-24`.

## Smoke do Qwen3-8B (preparado em 2026-10-22; quem roda é o dono)

Critério e configuração iguais (QLoRA 4-bit, r=16 em todas as projeções, checkpointing
"unsloth", fp16, batch 1, seed 3407, 10 passos no mais longo a 14.336 e, em
OOM, a 12.288; 5 passos nos medianos; GGUF Q4_K_M e Modelfile; mesmo disco e
flush do pré-voo). `unsloth` e `unsloth_zoo` FIXADOS em 2026.10.7.

- **Repositório:** `unsloth/Qwen3-8B-unsloth-bnb-4bit`, revisão
  `62efd7f9d748e394734a7adae2adf96e13a2abc8` (a do pré-voo). Tokenizer baixado
  nessa revisão (`tokenizer.json` `aeb13307…`).
- **Template:** `enable_thinking=False`. Conferido renderizando com jinja2 o
  `chat_template.jinja` oficial e o `qwen3_template` do Unsloth: os dois dão o
  mesmo texto, e `comum.chat('qwen')` bate com ele (treino e prompt de inferência).
  O turno do assistente abre com `<think>\n\n</think>\n\n` **vazio**; o alvo
  (o JSON) não tem `<think>` nem `</think>` em nenhum dos 141 exemplos limpos (nem nos 140 finais)
  (conferido na montagem). Como o bloco vazio é PROMPT na inferência, a parte
  de resposta da máscara é `<|im_start|>assistant\n<think>\n\n</think>\n\n`: o
  bloco fica mascarado e o `log.json` grava os tokens treinados decodificados
  (`mascara`: começo, fim, `tem_bloco_think`, `comeca_em_chave`); o kernel
  levanta erro se a máscara sair vazia ou o alvo tiver `<think>`.
- **Mais longo e mediano, com o tokenizer do Qwen3-8B.** O tokenizer gera mais
  tokens que o do Gemma: `satantango/positivas` tem **15.414** tokens e só o
  prompt dele (14.690) passa de 14.336 — truncado, o alvo cairia fora inteiro e
  o exemplo não teria token treinável. **Decisão do dono (2026-10-22): filtrar
  do treino, não subir o `max_seq_length` por um exemplo.** Motivo: único
  exemplo acima de 14.336 e de 12.288. **RESSALVA:** é o exemplo mais longo e
  denso do treino; sem ele o modelo nunca vê o caso extremo de comprimento (o
  maior que sobra tem 12.014). Implementado em
  `conjunto_limpo.FORA_POR_COMPRIMENTO` e gravado em `conjunto_limpo.json` e no
  `meta.json`. **Tamanho final do treino: 140 exemplos** (180 − 39 da limpeza −
  1 por comprimento); validação 19. Com 140: mediana 6.855,5, p90 9.156, p99
  11.947, máx 12.014. O E1 mede o maior que cabe, agora o MAIOR do conjunto:
  `the-turin-horse/negativas`, **12.014** tokens, nos cortes de 14.336 e de
  12.288 (é o MESMO exemplo: um OOM a 14.336 se repete a 12.288, e o kernel roda
  as duas por fidelidade à letra do critério). **Limitação:** o E1 mede 12.014
  tokens, não ~14 mil; como nenhum exemplo do treino passa de 12.014, o E1
  cobre o pior caso do treino que existirá, mas passar não prova 14.336.
  Medianos (6.843–6.865): `happy-hour-2015-1/negativas`, `inception/positivas`,
  `inglourious-basterds/negativas`, `bones-and-all/medianas`. Dataset
  `smoke_dataset_qwen3/`, `smoke.jsonl` sha256
  `ae74737defb435017b763f11e13e0f82bdf5bcdc1f136f2366d2765cd81ac14f`
  (substitui o `136d4450…` da primeira montagem, com 141).
- **Atenção:** o kernel grava `atencao` no `log.json`: configuração, flags do
  Unsloth, classe/forward da atenção, dtype visto na camada 0 e, num passo curto
  (1.024 tokens) sob `torch.profiler`, os operadores do ATen e os kernels CUDA
  que rodaram (mem-efficient/cutlass, flash, xformers, math; o nome do kernel
  traz f16/f32). A leitura do código dá o esperado (NÃO medido): o `model_type`
  `qwen3` não está em `FORCE_FLOAT32` (só `qwen3_moe` e `qwen3_5` estão), então
  a atenção fica em fp16 no caminho rápido do Unsloth.
- **E3:** `s/passo (mediano) × 140 × 3 / 3600 ≤ 20` passa se o s/passo for
  **≤ 171,4 s** (era 170,2 s com 141). O kernel já grava `e3`
  com o s/passo medido nos medianos e o nº de exemplos do `meta.json`.
  Substitui a conta com 156 do critério ("180 − 24", ESTIMADO).
- **Pastas de saída previsíveis:** `<modelo>__<seq>` (`qwen3-8b__14336`,
  `qwen3-8b__12288`), com ou sem erro; `viabilidade_ollama.py importar-pasta`
  acha as que têm `.gguf`.

## Fase 1 — títulos arquivados e troca da unidade (2026-10-30)

**Achado (informado pelo dono).** O dono rotulou pessoalmente os 90 títulos da
calibração v1: **77 G e 13 E (85,6% G)**. Isso sugere que o título sozinho, sem
filme e sem contexto, não carrega a especificidade que a premissa atribui ao
publicado. O arquivo de rótulos não foi aberto. Nenhuma medida (M-disp, M-anc,
M-comb), AUC, limiar ou consistência foi calculada sobre ele, e nunca será. Ele
não entra em calibração nem em validação. Rótulos e documento arquivados, fora
do git, em `docs/arquivo-de-estudos/finetune-fase1/titulos_arquivado/`
(`rotulos_calibracao.csv` sha256 `9064da6a…`; `rotulagem_calibracao.md`
`66cfdce2…`).

**Desvio.** `especificidade/DESVIO_01.md` (commit próprio `2440345`): a unidade
passa a ser o BULLET COMPLETO. O bloco do bullet no frontend só mostra o título
e a barra (`frontend/js/filme.js:1781`, `1768`, `1785–1793`); o único texto
além do título é o `exemplo_parafraseado` ("Aprofundar", `filme.js:1819–1837`;
schema `src/espectro24/models.py:93–97`). A leitura cega anterior mostrava
"tema — exemplo". Decisão do dono: **bullet completo = `tema` + " — " +
`exemplo_parafraseado`**, sem contagens nem nome do bucket.

**Pré-registro v2.** `especificidade/PROTOCOLO_v2.md`, commit próprio `b9649e7`
(sha256 `2716b42e…`), ANTES do documento. Código
`scripts/finetune/especificidade_bullet.py` (sha256 `ff71747e…`, `main`
`50522eb6…`; copiado sem alteração para este branch), que importa sem
alteração as medidas de `especificidade.py` (`7d40e620…`).

**Referência v2.** `especificidade/referencia_bullets.jsonl`, sha256
`da8723a62ebf8de16b8344e1e73a0891cc64bb4c76505a7046ddcd963de54522`: os mesmos
1.223 bullets (68 filmes; 1.079 treino, 144 validação), com o exemplo. Os
`tema` e `exemplo_parafraseado` são idênticos em `resultado/` de `main` e deste
branch (MEDIDO: 0 divergências). e5 com `query:`: **0 truncados** (máx. 97
tokens, mediana 49; limite 512).

**Calibração v2 preparada.** Pool elegível de TREINO = 1.079 − 133 = **946**
(80 pelo id da amostra v1 + 53 com o mesmo título normalizado). Limitação: a
exclusão por título tira títulos recorrentes, que tendem ao genérico. 20 por
quartil de M-disp no pool (237/236/237/236 → pesos 11,85/11,8/11,85/11,8),
semente 20261030, mais 10 repetidos a ≥ 40 posições: **90 itens**, 47 filmes
distintos, 0 colisões com a amostra v1. Documento cego
`docs/arquivo-de-estudos/finetune-fase1/rotulagem_calibracao_v2.md` (fora do
git; sha256 `beb743e5…`; 3.501 palavras), respostas em branco
`rotulos_calibracao_v2.csv` (`62d3aa51…`), mapa
`especificidade/mapa/calibracao_v2_mapa.json` (selo
`1dc2dc09888a19b1e011cf220a2f72ce733c11a24d2256b20cf4c070cc6d9c16`; só o
quartil, nenhum valor de medida). Em 16 linhas do documento (13 bullets distintos;
3 deles aparecem também como repetidos), o próprio exemplo publicado cita o grupo ("reviews
negativas", "medianas"…). O texto não foi alterado, porque é o bullet como está
escrito. Contingência pré-registrada: se houver < 15 E distintos,
`especificidade_bullet.py lote-extra` (40 itens, quartis de M-anc 5/5/10/20,
semente 20261031) antes de `medir`.

## Kaggle — correção do registro e invalidação das versões 2 e 3 (2026-10-30)

- **Correção:** o relatório anterior citava o sha256 `136d4450…` como o do
  dataset do smoke do Qwen3-8B. Esse é o da primeira montagem, com 141
  exemplos, de ANTES da saída do `satantango/positivas`. O correto é
  `ae74737defb435017b763f11e13e0f82bdf5bcdc1f136f2366d2765cd81ac14f` (140).
- **Versões 2 e 3 do kernel qwen3:** rodaram ANTES de o dataset ser versionado
  no Kaggle, sobre uma versão antiga cujo conteúdo não foi possível verificar
  (o download deu 404). Por isso foram **canceladas e invalidadas**: nenhum
  número delas entra em critério nenhum.
- **Versão 4:** enviada DEPOIS da versão nova do dataset (`ae74737d…`). Os
  logs ainda não chegaram.
- **Conferência pronta:** `scripts/finetune/kaggle/conferir_saida_smoke.py
  --saida <pasta baixada>` (em `main`) compara os logs com os 6 exemplos do
  `smoke_dataset_qwen3/smoke.jsonl`. Ela confere o sha do dataset local, o
  `meta_dataset.smoke_sha256` lido no Kaggle, o `template_confere` dos 6 papéis
  e, no longo e no 1º mediano, slug/bucket, `tokens_entrada` = `tokens.total` e
  `tokens_treinados` = `tokens.saida`, em igualdade exata, com código de saída
  1 se algo divergir. Limitação: o log só conta tokens do 1º lote de cada
  treino; os medianos 2–4 ficam conferidos pelo texto renderizado.
- **Kernel (`main`):** `smoke_treino.py` calcula o sha256 do `smoke.jsonl` lido
  ao iniciar (orquestrador e cada subprocesso), grava o sha em
  `resumo.json`/`log.json` (`dataset`) e no stdout, e ABORTA se ele divergir de
  `meta.json["smoke_sha256"]` ou se o `meta.json` não trouxer o sha. Regra para
  todo kernel de treino futuro. Nada foi reenviado ao Kaggle.

## O que NÃO foi medido

- O que foi ENVIADO ao DeepSeek e o que ele devolveu (não gravado); quantos
  buckets passaram pela retentativa com reforço.
- O formato exato (espaços, ordem de chaves) da resposta crua.
- Os prompts de narrativa/veredito/condições DA ÉPOCA (contados com o código
  atual).
- VRAM do QLoRA, velocidade de treino, tempo de merge/exportação no Kaggle.
- Se o Ollama atual importa os GGUF `qwen35` e `gemma4_unified` do HF (o teste
  de viabilidade decide).
- Tempo da recuperação (e5) dos bullets de treino; determinismo do juiz sob
  outra ordem de chamadas.
- (resolvido em 22/10) A cota semanal de GPU do Kaggle desta conta: 30 h
  (`kaggle quota`).
- (fechamento do gate 0) O teste de fumaça no Kaggle, a viabilidade e o
  import no Windows, e o juiz da limpeza: preparados, não rodados. A
  cota de GPU (~2–4 h) e as ~7,9 h de juiz são ESTIMATIVAS.
- Se o template que o Unsloth aplica no Kaggle é idêntico ao `comum.chat`
  (o teste de fumaça registra a comparação em `template_confere`).
- Se a cota de 0,35 token/caractere separa bem os pares que cabem na janela
  do juiz (`medir-contexto` confere os 10 maiores julgáveis no servidor).
- (fase 1) Nenhuma medida de especificidade sobre item rotulado: os rótulos de
  títulos foram arquivados sem conta (DESVIO_01); os da v2 (bullet completo)
  ainda não voltaram; a validação nem foi montada.
- O tamanho do disco temporário do Kaggle (a documentação não declara).
- (22/10) O backend de SDPA do E4B foi INFERIDO da alocação e do código; o
  smoke de 20/10 não o registrou. O mecanismo do OOM do 12B não está nos logs
  (sem VRAM por fase, sem o passo da falha). Nem E2, E3 nem E4 de nenhum Gemma.
- (22/10) A RAM durante a limpeza (guarda desligada). Se os 24 pares fora da
  janela caberiam (`medir-contexto` só mediu os 10 maiores julgáveis).
- (22/10) E5 e E4 do Qwen3-8B; o E1 do Qwen3-8B a ~14 mil tokens (só 12.014).
