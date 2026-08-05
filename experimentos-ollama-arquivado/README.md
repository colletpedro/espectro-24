# Experimentos de LLM local (Ollama / Qwen3.5-9B) — arquivado

Este diretório reúne os artefatos dos experimentos 1–7, que avaliaram se um LLM
rodando localmente (Ollama, modelo `qwen3-espectro` = Qwen3.5-9B, Q4_K_M) poderia
substituir o Gemini como provider de síntese (§D), narrador (§D2) e editor (§E2) do
Espectro 24 — motivação original: viabilizar um catálogo maior sem depender da cota
gratuita do Gemini (20 req/dia). Nenhum destes artefatos foi consumido pelo pipeline
de produção em `src/espectro24/`; são resultado de scripts avulsos em `scripts/`,
nunca importados de lá.

Todos os experimentos rodaram 100% offline em relação a rede externa de dados
(`n_network=0` confirmado — cache local de reviews, zero requisições Letterboxd/TMDB);
a única rede envolvida era o servidor Ollama em `localhost:11434`. Nenhum bump de
versão do `SPEC.md` de produção resultou destes experimentos.

## Resultado por experimento

1. **Síntese local vs. gabarito Gemini** (`COMPARACAO_LOCAL.md`,
   `scripts/comparar_sintese_local.py`) — mesma síntese §D rodada no Ollama
   (`think=false`) e comparada ao gabarito Gemini já publicado. Resultado: JSON
   estruturalmente válido, mas frequência de tema (`mencoes_aproximadas`) sistematicamente
   inflada — razão soma/n_reviews acima do gabarito em todos os buckets, um tema
   cobrindo até 96% do bucket.

2. **Thinking ligado, sem relatório dedicado** (`scripts/comparar_sintese_local_thinking.py`,
   citado em `COMPARACAO_LOCAL_V3.md`) — raciocínio livre divergiu sem produzir
   resultado utilizável em 2 de 3 buckets (~483s na chamada mais longa, sem terminar
   em JSON aproveitável). Não gerou documento próprio; registrado só como referência
   dentro do experimento 3.

3. **Duas hipóteses contra a inflação de frequência** (`COMPARACAO_LOCAL_V3.md`,
   `scripts/comparar_sintese_local_v3.py`) — variante A (instrução explícita de
   contagem) melhorou o bucket maior mas piorou os dois menores, resultado
   inconsistente; variante B (raciocínio breve e limitado) não pôde ser testada —
   timeout de infraestrutura (>600s) em 100% das tentativas.

4. **Síntese em dois estágios, contagem em código** (`COMPARACAO_LOCAL_V4.md`,
   `scripts/comparar_sintese_local_v4.py`) — separar identificação de temas
   (estágio 1) de classificação por review (estágio 2), com a contagem feita em
   código e não pelo LLM, resolveu a inflação: razão soma/n_reviews caiu abaixo do
   gabarito nos três buckets, maior tema nunca acima de 52%. Custo: ~1,9x mais lento
   (13 chamadas/filme vs. 3).

5. **Refinamento do dois-estágios + validação em 2 filmes** (`COMPARACAO_LOCAL_V5.md`,
   `scripts/comparar_sintese_local_v5.py`) — reforços de nomenclatura e anti-spoiler
   no prompt do estágio 1, lotes maiores (25) no estágio 2, validado em `cure` e
   `cidade-de-deus`. O padrão do experimento 4 se sustentou fora da amostra original
   (razão sempre ≤2,35, maior fração ≤54%), mas nomenclatura malformada (2/33 temas) e
   taxa de reviews sem tema atribuído não melhoraram de forma consistente.

6. **Recall do classificador de temas** (`RECALL_V6.md`, `AUDITORIA_RECALL_V6_V3.md`,
   `scripts/experimento_recall_v6.py`) — comparou 3 variantes de tamanho de lote/prompt
   do estágio 2 contra uma auditoria humana de recall (quais reviews deveriam ter sido
   marcadas com qual tema). Nenhuma variante teve retentativa ou lote falho, mas o
   recall variou bastante entre variantes (de 0 a 6 temas capturados no mesmo índice
   de teste) — não houve uma variante claramente superior nos dois critérios extras
   avaliados.

7. **Narrador [D2] e editor [E2] no modelo local** (`NARRADOR_EDITOR_LOCAL_V7.md`,
   `scripts/experimento_narrador_editor_local_v7.py`) — usando os prompts de produção
   byte-idênticos (importados direto de `synthesize.py`, nunca copiados) sobre os
   buckets já sintetizados de `cure` e `cidade-de-deus`. **Este é o experimento
   decisivo**: o narrador local não sustentou as ~18 invariantes de honestidade
   exigidas numa única chamada — colapsou ou omitiu movimento em teste real, ao
   contrário do gabarito Gemini. O editor, testado em condição de pipeline 100% local,
   foi sempre descartado (reprovação estrutural antes de produzir uma edição avaliável).
   Tempo medido: ~20,8 min/filme para o pipeline local completo (síntese + narrador +
   editor), o que projetava ~17,3h para um catálogo de 50 filmes.

## `AUDITORIA_PRECISAO.md`

Auditoria humana de precisão (falsos positivos de atribuição de tema) sobre a saída
do dois-estágios dos experimentos 4/5 — texto integral das reviews marcadas, cada uma
com espaço para conferência manual. Não produz veredito automatizado; é o material
que fundamentou as leituras "parece razoável"/"zona cinzenta" citadas nos relatórios 4 e 5.

## Conclusão que motivou o abandono

Dois estágios (identificar temas, depois classificar e contar em código) resolvem de
forma robusta a inflação de frequência que o modelo local produzia numa chamada só
(experimentos 3→4→5). Mas essa técnica não se generaliza para o narrador: as ~18
invariantes de honestidade do narrador (ancoragem de peso, quantificador, escopo,
consenso, marcador de perspectiva, vocabulário "das notas", anti-spoiler, formato,
entre outras) precisam ser satisfeitas simultaneamente dentro de uma única prosa
coerente, e o Qwen3.5-9B local não sustentou isso em teste real (experimento 7) — ao
contrário da síntese estruturada, não há como quebrar a tarefa do narrador em estágios
menores sem reintroduzir os mesmos problemas de fragmentação que o produto já rejeita
(ver invariante de neutralidade de tratamento, `SPEC.md`). Combinado ao custo de tempo
medido (~17,3h de LLM local para 50 filmes, sem contar coleta), a decisão foi abandonar
o caminho local e migrar a exploração de provider alternativo para a API DeepSeek
(compatível com o SDK OpenAI, sem teto diário de requisições).
