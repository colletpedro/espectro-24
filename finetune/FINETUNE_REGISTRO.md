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
  (aparece em Settings da conta) — NÃO CONFIRMADA.

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
- A cota semanal de GPU do Kaggle desta conta.
- (fechamento do gate 0) O teste de fumaça no Kaggle, a viabilidade e o
  import no Windows, e o juiz da limpeza: preparados, não rodados. A
  cota de GPU (~2–4 h) e as ~7,9 h de juiz são ESTIMATIVAS.
- Se o template que o Unsloth aplica no Kaggle é idêntico ao `comum.chat`
  (o teste de fumaça registra a comparação em `template_confere`).
- Se a cota de 0,35 token/caractere separa bem os pares que cabem na janela
  do juiz (`medir-contexto` confere os 10 maiores julgáveis no servidor).
- (fase 1) Nenhuma medida de especificidade sobre título real: os rótulos da
  calibração ainda não voltaram; a validação nem foi montada.
- O tamanho do disco temporário do Kaggle (a documentação não declara).
