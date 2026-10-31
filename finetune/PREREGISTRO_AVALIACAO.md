# PRÉ-REGISTRO — avaliação do fine-tuning (Fases 2 e 4)

Data: 2026-10-31. Commitado em commit PRÓPRIO, ANTES de qualquer medição nos
filmes de teste, inclusive a do publicado. Base: `PROPOSTA_FASE2.md`
(sha256 `99c9b127…`) com as decisões do dono de 2026-10-31; onde há conflito,
valem as decisões. Etiquetas: **MEDIDO**, **ESTIMADO**, **PROPOSTO** (aqui,
"fixado" = pré-registrado).

Nada foi gerado, julgado ou medido nos filmes de teste para escrever este
documento. A única leitura de dado de teste foi o sha256 da entrada do juiz
já existente (seção "Ordem e integridade"), sem conta sobre ela.

Qualquer mudança depois deste commit vira um `DESVIO_xx.md` (motivo, o que
muda, o que já tinha sido visto), escrito e commitado ANTES da medição afetada.

## 1. Lados e conjunto

- **PUBLICADO (P):** a síntese DeepSeek publicada em `resultado/<slug>.json`
  (sem regerar). Gerada SEM temperatura explícita
  (`src/espectro24/synthesize.py:523–532`: os `kwargs` do DeepSeek não têm
  `temperature`; vale o padrão da API).
- **BASE (B):** Qwen3-8B sem treino. GGUF exportado pelo kernel
  `scripts/finetune/kaggle/kernel_base/exportar_base.py` (provas: `lora_B` = 0,
  logits iguais com e sem adaptador, fusão igual ao 16-bit original),
  importado por `viabilidade_ollama.py importar-pasta` (Modelfile corrigido
  com o TEMPLATE canônico) e com `E4_importa_e_gera` true.
- **TREINADO (T):** Qwen3-8B + LoRA. Mesmo caminho (mesma função de export,
  mesmo `importar-pasta`) e o MESMO commit do llama.cpp da base;
  `gerar_sintese_teste.py` recusa commit diferente.
- **Teste:** os 30 filmes de `split.json` (semente 20261020, sha256
  `3232b2ad…`), **89 buckets**: o `a-brighter-summer-day/positivas` (Gemini,
  `buckets_excluidos`) fica fora de todos os lados.
- **Os 5 filmes de referência** (`fixos_no_teste`): anatomy-of-a-fall,
  incendies, mother-2017, napoleon-2023, the-substance.

## 2. Geração (B e T idênticos)

Script: `scripts/finetune/gerar_sintese_teste.py gerar --lado base|treinado`
(Windows), sobre o `plano_teste.json` gerado no Mac.

- **Prompt:** o template atual da síntese (`build_system_prompt` /
  `build_user_message`, via `comum.prompt_sintese`), sobre os buckets
  remontados do bruto (`comum.buckets_remontados`); o sha256 de system e user
  de cada par é conferido contra o plano.
- **`think` false**, `num_predict` 3.000, JSON livre (`schema="json"`),
  `num_ctx` POR CHAMADA = (tokens exatos do prompt + 3.000) × 1,10,
  arredondado para cima no múltiplo de 1.024 (regra do gate 0).
- **Temperatura: 0,8 (fixada, passada EXPLICITAMENTE em cada chamada).**
  É o valor que o pipeline atual usa de fato:
  - `src/espectro24/local_ollama.py:163–165`: o pipeline só fixa temperatura
    se `ESPECTRO24_OLLAMA_TEMPERATURE` existir; sem ela, vale o Modelfile;
  - `scripts/finetune/viabilidade_ollama.py:450–452`: o Modelfile corrigido
    tem só `FROM`, `TEMPLATE` e `PARAMETER stop`, sem parâmetro de amostragem
    (MEDIDO no import do smoke, `importar_espectro-qwen3-8b_20261031_140521.json`
    → `modelfile_usado`);
  - sem `PARAMETER temperature`, o Ollama usa o padrão dele, **0,8**
    (ESTIMADO: valor da documentação e do código do Ollama, não medido nesta
    rodada; Ollama 0.40.13 no Windows). Passar 0,8 explícito fixa o valor
    mesmo se o padrão do Ollama mudar.
  - Achado (MEDIDO): o Modelfile ORIGINAL do Unsloth trazia temperature 0,6,
    top_k 20, top_p 0,95, min_p 0 e repeat_penalty 1. A correção do TEMPLATE
    descartou essas linhas. Logo, a geração base da Fase 1 rodou com o
    padrão do Ollama, não com o do Unsloth. Os demais parâmetros de amostragem
    (top_k, top_p, min_p, repeat_penalty) ficam no padrão do Ollama, IGUAIS
    nos dois lados (mesmo `importar-pasta`).
- **Seed: 20261019 (fixada, explícita em cada chamada).** O pipeline da síntese
  não fixa seed (`local_ollama.py:166–167`: só se o chamador passar; a síntese
  não passa). O único seed fixo do caminho local do projeto é o do juiz,
  `scripts/juiz_bullets_v2.py:116` (`SEED = 20261019`), e é esse que se usa.
- **`ESPECTRO24_OLLAMA_TEMPERATURE` é proibida durante a geração:** o script
  aborta se ela existir no ambiente (como o juiz, `juiz_bullets_v2.py:906`).
- **Retentativa: a de produção**, `synthesize_bucket`
  (`src/espectro24/synthesize.py:2169–2197`), chamada com o cliente local
  injetado:
  1. chamada; se o JSON não parsear, UMA nova chamada com o mesmo prompt; se
     de novo não parsear, o bucket fica sem temas ("Falha ao obter JSON
     válido do LLM.");
  2. com JSON válido, `_construir_temas` (n = reviews analisadas do bucket) e
     as checagens de idioma e escopo; se alguma falhar, UMA retentativa com
     `_REFORCO_VALIDACAO` anexado ao system; se a retentativa parsear, ela
     substitui a 1ª; as flags `idioma_invalido` / `escopo_suspeito` ficam.
  São no máximo 3 chamadas por bucket. Cada chamada fica gravada (texto cru,
  tempos, memória); a 1ª tentativa é guardada à parte para a descrição.
- **Partida limpa, guarda de latência e guarda de RAM livre ≥ 2 GB**, como no
  script preparado (não se desligam).
- **Regra do outlier e da memória:** `500-days-of-summer/positivas` (o
  `num_ctx` pela regra fica entre 28.672 e 31.744, ESTIMADO, acima do probe de
  27.648) e qualquer outro bucket que a guarda de RAM derrube:
  - o bucket é tentado de novo UMA vez, depois de nova partida limpa; se a
    guarda de RAM derrubar de novo, ele fica **fora por memória**;
  - bucket fora por memória em QUALQUER lado sai dos DOIS lados de TODA
    comparação (C1 a C5 e descritivas), inclusive do publicado; é reportado
    à parte e NÃO conta como falha do modelo;
  - falha por erro do modelo (texto inválido, JSON que não parseia depois
    da retentativa, validador reprovado) conta normalmente.

## 3. Critérios do TREINADO

**Decisão "publicável" = C1, C2, C3, C4, C5 e C6 passam, TODOS.** Cada um a 95%,
sem correção de multiplicidade (a decisão exige todos).

**IC (C1–C3):** bootstrap POR FILME, **10.000 reamostras, semente 20261101**,
percentil 2,5 / 97,5. Em cada reamostra, os mesmos filmes nos lados
comparados (pareado); a taxa de um lado é a razão das somas (eventos / total)
nos filmes sorteados; a diferença é T − P em pontos percentuais. Os buckets
fora por memória ficam fora antes de reamostrar.

### C1 — sem apoio (juiz v2.2)

- Juiz congelado, `config_sha256`
  `44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669`
  (gpt-oss:20b no Windows), mesma recuperação e5 e mesmos 5 pares por bullet
  da limpeza; **parada no 2º "sim"**. O bullet julgado é o que seria
  publicado (depois de `_construir_temas`).
- **% sem apoio** = bullets com 0 "sim" / bullets julgados. Indeterminado (sem
  par julgável) fica fora do denominador e é reportado por lado.
- **Passa se:** limite superior do IC 95% de (T − P) **< +4,0 pp** E estimativa
  pontual de (T − P) **≤ +2,0 pp**.
- A margem de 4,0 pp é a menor diferença detectável com 30 filmes
  (`poder.md`: ICC 0,023 MEDIDO só para "sem apoio", 18 bullets por filme,
  α = 0,05, poder 0,80). **É um limite de PODER, não uma tolerância de
  produto.** O teto pontual de +2,0 pp é a decisão do dono.

### C2 — apoio ≥ 2

- **% com apoio ≥ 2** = bullets com ≥ 2 "sim" / bullets julgados (mesmo
  denominador do C1).
- **Passa se:** limite inferior do IC 95% de (T − P) **> −δ₂**, com δ₂ = 8 pp
  até o recálculo abaixo.
- **Recálculo de δ₂ (fixado agora):** depois de julgar P no teste (Fase 2) e
  ANTES de gerar T, com p₀ = taxa de apoio ≥ 2 MEDIDA em P (bullets julgados
  dos buckets que ficam):
  - n = 30 × m / (1 + (m − 1) × ICC), com m = 18 e ICC = 0,023;
  - z_a = 1,95996 (α = 0,05 bilateral), z_b = 0,84162 (poder 0,80);
  - δ₂ = p₀ − p₁, com p₁ < p₀ o menor valor que satisfaz
    p₀ − p₁ ≥ z_a·√(2·p̄·(1 − p̄)/n) + z_b·√((p₀(1 − p₀) + p₁(1 − p₁))/n),
    p̄ = (p₀ + p₁)/2 (a fórmula de `poder.mde_analitico`, no sentido da
    queda); bisseção em [0, p₀], 60 iterações;
  - arredondado ao 0,1 pp mais próximo. Exemplos (ESTIMADO): p₀ = 0,80 → 8,6;
    0,85 → 7,9; 0,90 → 6,8;
  - o valor de δ₂ e o p₀ são gravados e commitados ANTES da geração do T, e
    substituem os 8 pp.

### C3 — M1, palavras de quantidade (um lado só)

- `scripts/finetune/metricas.py`, lista CONGELADA
  `finetune/metricas/palavras_quantidade.txt` (sha256
  `a7fcd5a5663c3ebdc0112b27bd8821c839d47de86673ef4ebdea83c0524c14af`).
  M1 = `exemplo_parafraseado` com ≥ 1 expressão da lista / exemplos.
- **Passa se:** limite superior do IC 95% de (T − P) **< +10 pp**. Usar MENOS
  palavras de quantidade não reprova (não há limite inferior).

### C4 — JSON e validadores mecânicos, com a retentativa do pipeline

- Por bucket, sobre o resultado FINAL do `synthesize_bucket` (seção 2):
  passa se o JSON parseou E todos os validadores de
  `scripts/finetune/reconstruir_sintese.py:167–200` (`validar_publicado` →
  `passa_publicado`) passam: idioma pt-BR, escopo sem marcador, sem aspas,
  menções em [0, n], ≤ 6 temas, ordem decrescente, `n_reviews_analisadas` = n,
  campos não vazios, sem tema de menção única (n ≥ 5), sem as flags
  `idioma_invalido` / `escopo_suspeito`.
- **Passa se:** **≥ 87 dos 89 buckets** (se k buckets saírem por memória:
  ≥ 87 − k dos 89 − k).
- A taxa na 1ª tentativa (sem retentativa) entra só como descrição.

### C5 — especificidade pela rotulagem cega do dono (Fase 4)

- **Sorteio (semente 20261102),** script próprio (commit separado, depois
  deste):
  - frame de cada lado: os bullets que seriam publicados dos buckets que
    ficam (bucket fora por memória sai dos dois lados; bucket do T sem temas
    não tem bullet);
  - **60 do T e 60 do P**, estratificados por bucket: **20 por bucket**
    (negativas, medianas, positivas) em cada lado, uniformes sem reposição
    dentro do estrato;
  - ordem do sorteio: T negativas, T medianas, T positivas, P negativas,
    P medianas, P positivas (cada um sobre os ids ordenados); embaralha os
    120; **+ 6 repetidos** (3 do T, 3 do P), cada um a ≥ 40 posições do
    original.
- **Documento cego** em `docs/arquivo-de-estudos/finetune-fase4/` (fora do
  git): só id e bullet completo (**tema** — exemplo). Mesma normalização de
  exibição nos dois lados (`especificidade_validacao.exibir`: 1ª letra
  maiúscula, ponto final quando falta). Mesma definição de G/E da Fase 1,
  no topo. Mapa em `finetune/fase4/especificidade_mapa.json`, com o sha256
  impresso no fim do documento; o mapa não vai ao dono.
- **Medida:** proporção de E entre os 60 distintos de cada lado (rótulo da 1ª
  ocorrência), com **IC de Wilson 95%** nos dois lados. A consistência dos 6
  repetidos é reportada.
- **Passa se:** proporção de E do T **≥ 10%** (≥ 6 de 60; estimativa pontual).
- **Referência registrada (MEDIDO, Fase 1):** publicado 17/80 = 21%
  (calibração v2) e 6/30 = 20% (validação v2); base 0/30.
- Limitação: o IC de Wilson trata os bullets como independentes (ignora o
  agrupamento por filme); o estilo pode denunciar o lado, como na validação
  da Fase 1.

### C6 — leitura cega (Fase 4)

- T × P nos 5 filmes de referência, só a síntese (os 3 buckets), no formato
  do bloco "1. Bullets da síntese" de
  `prosa-local-qwen3-leitura/leitura_cega.md` (`gate-local`, `cef0b16`):
  por bucket, os bullets (**tema** — exemplo, sem contagens) e a
  `observacao_geral` em itálico. O texto é o que seria publicado, sem
  normalização. Narrativa, veredito e condições NÃO entram (o alvo do treino
  é só a síntese, decisão 4 do gate 0).
- **Lados sorteados por filme, semente 20261103.** Mapa em
  `finetune/fase4/leitura_mapa.json`, sha256 impresso no fim do documento;
  documento em `docs/arquivo-de-estudos/finetune-fase4/` (fora do git).
- Por filme, o dono marca: "publicaria sem mudança" (A / B / ambos / nenhum) e
  "melhor" (A / B / empate).
- **Passa se:** o dono julga o T publicável em **≥ 4 de 5** filmes. A
  preferência é descritiva.
- Ordem: o C5 é rotulado ANTES do C6 (a leitura de sínteses inteiras
  ensinaria o estilo de cada lado).

## 4. Só descritivo (não decide)

- Superioridade sobre a BASE em C1 a C4: (T − B) com o mesmo IC.
- C1 a C4 calculados na BASE. **Se a BASE também satisfizer C1 a C4, isso é
  registrado como achado.** Usar a base em produção exigiria uma leitura cega
  própria, NÃO prevista aqui.
- M2 (concordância de `mencoes_aproximadas` com o publicado, `metricas.py`):
  o τ do pareamento é fixado num DESVIO antes de qualquer M2, sem olhar o
  teste.
- Validade na 1ª tentativa; tempos por bucket; memória; buckets fora por
  memória.

## 5. Ordem e integridade

1. **Fase 2 (agora):** gerar com a BASE nos 30 filmes; julgar P e B; calcular
   C1 a C4 nos dois; recalcular δ₂ pela taxa do P e commitar.
2. **Reaproveitamento do P dos 5 de referência:** só se o sha256 das 450 linhas
   do lado publicado da entrada do juiz montada agora (na ordem do arquivo,
   cada linha com `\n`) for
   `a68a6c9b16d08d90482566a71cb26afc3e9af5416813cdf394dc85b3cad1e10a`
   (MEDIDO hoje sobre `checagem-bullets/juiz_entrada.jsonl`, commit `91397da`,
   `gate-local`, 900 linhas, 450 de `lado: publicado`), e o `config_sha256`
   for o do C1. Senão, mede-se de novo.
3. **Fase 3:** treino. **Nenhuma escolha de treino** (época, checkpoint,
   hiperparâmetro) olha filme de teste: só a perda na validação
   (**19 exemplos**).
4. **Fase 4:** o T é gerado e medido **UMA vez**: geração, juiz, C1–C4, C5,
   C6, nesta ordem. Sem segunda geração do T no teste.
5. **Limite conhecido:** os filmes de teste já tinham sido vistos antes deste
   pré-registro: as saídas publicadas existem e são públicas, e os 5 de
   referência foram medidos (juiz) e lidos pelo dono (leitura cega de
   17/10). Os critérios não mudam por isso; fica registrado.

## 6. Pontos da PROPOSTA_FASE2 que mudaram ou saíram

- C3 (M1): de equivalência ±10 pp para um lado só (< +10 pp) — decisão do dono.
- C1: acrescentado o teto pontual de +2,0 pp — decisão do dono.
- C4: de "saída crua de 1 amostra" para "com a retentativa de produção"; a
  crua vira descrição.
- Especificidade: a M-disp saiu (validação da Fase 1 NEGATIVA); entra o C5,
  rotulagem do dono.
- C6: só a síntese, sem a pergunta "A é publicável?" separada por lado: a
  tabela do formato antigo (A / B / ambos / nenhum) responde as duas.
- Não entram: margens com ICC 0,05 (só sensibilidade na proposta); M2 com τ
  fixado na validação (vira DESVIO antes do uso); custo e calendário (estão
  na proposta, não decidem nada).
