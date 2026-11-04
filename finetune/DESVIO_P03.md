# DESVIO_P03 — τ do pareamento do M2, fixado só com dados de TREINO

Data: 2026-11-04. Completa o `PREREGISTRO_AVALIACAO.md` (commit `8339a67`,
sha256 `4e9d61b6…`), seção 4: "M2 (...): o τ do pareamento é fixado num DESVIO
antes de qualquer M2, sem olhar o teste". Commitado em commit PRÓPRIO, ANTES de
qualquer cálculo do τ e ANTES de gerar o TREINADO. **O critério abaixo foi
escrito sem nenhum cosseno base × publicado calculado.** O M2 continua só
descritivo: não entra em C1–C6 nem na decisão "publicável".

## O que já tinha sido visto

- Nenhum pareamento de temas entre dois lados foi calculado em filme nenhum. A
  Fase 1 usou o e5 em outras contas (recuperação de reviews do juiz, M-disp),
  nunca tema × tema entre base e publicado.
- Os bullets da geração base da Fase 1 foram lidos pelo dono na validação v2
  (rotulagem G/E), sem contagem e sem cosseno.
- Nada do teste entra aqui: os 5 filmes são de TREINO e a conta só lê
  `finetune/especificidade/geracao_base/` e os publicados desses 5.

## Dados (só TREINO)

- **Lado gerado:** `finetune/especificidade/geracao_base/`, 5 filmes de TREINO
  (`validacao_filmes.json` → `filmes_geracao`: fight-club, hereditary,
  pinocchio-2022, soul-2020, the-wailing) × 3 buckets = 15 buckets, cada
  arquivo conferido contra o `manifesto.json`; os bullets com `completo` true,
  como em `especificidade_validacao.bullets_base`. O script recusa se algum
  filme não for de treino ou estiver em validação, teste ou nos 5 de referência.
- **Publicado:** `resultado/<slug>.json` desses 5, do commit fixo
  `742cfe3c7d443decd7cfd395e32dce080011bd45` (`comum.entradas_do_commit`), os
  temas do mesmo bucket.

## Critério de escolha (fixado agora)

- **Pareamento:** o de `metricas.parear`, sem mudança: texto
  `"{tema}. {exemplo_parafraseado}"`, `encoder_e5` (`queries`, o mesmo modelo
  e5 do juiz), cosseno, atribuição húngara que maximiza a soma.
- **Distribuição nula D₀:** para cada tipo de bucket b e cada par ORDENADO de
  filmes diferentes (x, y), a atribuição húngara entre os temas da base de
  (x, b) e os do publicado de (y, b); entram TODOS os cossenos atribuídos, sem
  limiar. São 3 × 5 × 4 = 60 atribuições. Filmes diferentes não podem
  compartilhar um ponto específico; só temas genéricos ("ritmo lento").
- **τ = percentil 95 de D₀**, pelo posto mais próximo (o valor na posição
  ⌈0,95·N⌉ da lista crescente, 1-indexada), arredondado PARA CIMA na 3ª casa
  decimal. Leitura: um par só conta no M2 se os dois temas forem mais
  parecidos que 95% dos pareamentos forçados entre filmes diferentes.
- **Sem alternativa:** o τ é o valor que sair, sem segunda conta, sem outro
  percentil e sem ajuste por D₁.
- **D₁ (só descrição, não muda o τ):** a mesma atribuição no MESMO filme e
  bucket, base (x, b) × publicado (x, b), 15 atribuições; reporta-se a fração
  dos pares atribuídos com cosseno ≥ τ e os quantis de D₀ e D₁.
- Script: `scripts/finetune/tau_m2.py fixar` (Mac), que recusa se este arquivo
  não estiver commitado e sem mudança, grava `finetune/fase4/tau_m2.json`
  UMA vez (o τ, N de D₀ e D₁, quantis, sha256 de cada entrada, o sha256 deste
  arquivo) e recusa se a síntese do treinado já existir.

## Como o M2 é calculado na Fase 4 (fixado agora; descritivo)

Por lado L ∈ {treinado, base} contra o publicado, nos buckets mantidos (os 89
menos os fora por memória), só onde os dois lados têm temas:

- pares = `metricas.parear(temas_L, temas_P, encoder, τ)`;
  `metricas.concordancia_bucket` por bucket;
- **taxa de pareamento** = Σ pares / Σ temas do publicado;
- **DAM** (reviews) = Σ |m_L − m_P| / Σ pares; **DAM relativa** = Σ
  (|m_L − m_P| / n) / Σ pares, n = `n_reviews_analisadas` do publicado;
- **tau-b**: mediana dos buckets com tau-b definido (≥ 3 pares e variação nos
  dois lados), e quantos buckets têm tau-b;
- IC 95% por filme da DAM relativa e da diferença treinado − base, com as
  mesmas 10.000 reamostras de filmes do C1–C3 (semente 20261101).

Script: `scripts/finetune/fase4_m2.py calcular` (Mac), depois do juiz do
treinado; grava em `finetune/fase4/cego/` e só imprime o sha256 (cegueira do
dono até o C5 e o C6).

## Limites (não medido)

- A geração base da Fase 1 rodou com o padrão de amostragem do Ollama (antes do
  DESVIO_P01) e com o modelo base, não com o treinado; o τ vem de outra
  distribuição de texto que a do teste.
- D₀ inclui pares genéricos legítimos entre filmes ("ritmo lento" existe em
  muitos): o τ é conservador e pode deixar de parear temas que de fato
  coincidem no mesmo filme.
- Nenhum rótulo manual confere o pareamento: precisão e recall do τ não são
  medidos. O M2 mede imitação das contagens do professor, não acerto.
