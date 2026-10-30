# DESVIO_01 — a unidade da Fase 1 passa a ser o BULLET COMPLETO

Data: 2026-10-30. Registrado em commit próprio, ANTES de gerar a nova amostra e
antes de qualquer conta. Desvia do protocolo pré-registrado
`finetune/especificidade/PROTOCOLO.md` (commit
`fe7d7a02f271729913eef1886a8298edaa5f165d`, sha256 do arquivo `3568d4ef…`).

## Motivo

- O dono rotulou pessoalmente os 90 títulos da calibração (80 + 10 repetidos):
  **77 G e 13 E (85,6% G)**. A distribuição foi informada pelo dono; o arquivo
  de rótulos não foi aberto nesta rodada.
- O dono não lembra se, na leitura cega anterior, a diferença de
  especificidade entre o publicado e o qwen3 aparecia no título ou só no texto
  do bullet.
- A premissa do projeto é que o publicado é o lado específico. Os 85,6% de G
  sugerem que o título sozinho, sem filme e sem contexto, não carrega a
  especificidade.

**Decisão do dono:** a unidade passa a ser o BULLET COMPLETO.

## O que é o bullet completo (decidido pelo dono em 2026-10-30)

O pedido original dizia "título + texto principal, o que o leitor vê sem
expandir", com o `exemplo_parafraseado` FORA. A leitura do código mostrou que
esse texto principal não existe:

- `frontend/js/filme.js:1781` — o bloco do bullet escreve `t.tema` (o título);
- `frontend/js/filme.js:1768` e `1785–1793` — a barra, cuja largura e cujo
  `aria-label` ("Mencionado em cerca de X de N reviews") vêm de
  `mencoes_aproximadas` / `n_reviews_analisadas`; não há outro texto visível;
- `frontend/js/filme.js:1819–1837` — o `exemplo_parafraseado` só aparece ao
  abrir "Aprofundar";
- schema: `src/espectro24/models.py:93–97` (`Tema`: `tema`,
  `mencoes_aproximadas`, `n_reviews_analisadas`, `exemplo_parafraseado`; o
  resto são marcas do código) e o pedido ao modelo em
  `src/espectro24/synthesize.py:131–134`.

Sem o exemplo, o "bullet completo" seria o próprio título: a mesma unidade dos
rótulos arquivados, e o desvio não mudaria nada. A leitura cega anterior
(`gate-local`, commit `cef0b16`, `prosa-local-qwen3-leitura/leitura_cega.md`)
mostrava cada bullet como **"tema — exemplo_parafraseado"**; num caso dela, o
título é "desempenho atorial" e o nome "Sandra Hüller" está só no exemplo.

Proposto e aceito pelo dono: **bullet completo = `tema` + `exemplo_parafraseado`**,
no formato da leitura cega. A regra "o exemplo fica FORA" está revogada por
esta decisão. Ficam fora os números e contagens (`mencoes_aproximadas`,
`n_reviews_analisadas`, a barra, "cerca de X de N") e o nome do bucket. Nomes
próprios dentro do texto ficam: são parte da especificidade. A definição exata
do texto está no `PROTOCOLO_v2.md`.

## O que NÃO foi feito com os rótulos de títulos

- Nenhuma medida (M-disp, M-anc, M-comb) foi calculada sobre os rótulos de
  títulos: nem AUC, nem limiar, nem consistência dos repetidos. O
  `limiares.json` da versão 1 nunca foi escrito.
- Eles não entram em calibração nem em validação, nem agora nem depois.
  Nenhuma medida será calculada sobre eles.
- Arquivados, fora do git, em
  `docs/arquivo-de-estudos/finetune-fase1/titulos_arquivado/`:
  - `rotulos_calibracao.csv`, sha256
    `9064da6a077370e40dcd86b9781a9fdadf3cddca9a07711e08563a67d94031a2`;
  - `rotulagem_calibracao.md`, sha256
    `66cfdce225b970ce4a1193b77228e3505c06a40a700472b515c9034810c9e485`.
- O mapa da versão 1 (`mapa/calibracao_mapa.json`, selo `2bcbf743…`) fica no
  git. Ele só serve para EXCLUIR da nova amostra os bullets cujo título o dono
  já viu.

## O que continua valendo

O protocolo `fe7d7a02` continua valendo em tudo o que não for alterado aqui ou
no `PROTOCOLO_v2.md`:

- a forma das três medidas, sem ajuste (M-disp com e5, prefixo `query:`,
  correção de viés e k = 10; M-anc = máx presente·idf; M-comb = logística
  ponderada sem penalização com as duas);
- a orientação fixa, o Youden ponderado e o congelamento único dos limiares;
- o critério de aceite da validação (AUC ≥ 0,80 com IC por bootstrap por filme;
  acurácia balanceada ≥ 0,75; diferença publicado × local ≤ 0,15), montada
  depois da escolha do modelo base;
- a regra da mais simples, o teto pela consistência do dono, o resultado
  negativo como entrega e a proibição de rever limiar ou fórmula depois da
  validação.

O que muda (unidade, referência, amostra, semente, exclusões, contingência e a
definição em uma linha) é pré-registrado em `PROTOCOLO_v2.md`, em commit
próprio, antes do documento de rotulagem.
