# Estado da republicação (Entrega 1, v1.9.14) — **FEITA em 2026-08-16**

Este documento nasceu na v1.9.12 dizendo "não republicado nesta sessão".
**Deixou de ser verdade.** O que segue é o registro do evento, com o
histórico preservado abaixo da linha.

## O que aconteceu

`resultado/{cure,cidade-de-deus,the-invite-2026}.json` foram sobrescritos
pelos artefatos da v1.9.13 (`resultado/v1913/`), e o site regerado.

| item | estado |
|---|---|
| leitura humana dos textos | **feita** — `resultado/v1913/NARRATIVAS_GATE_LEITURA.md` |
| escopo: 3 filmes ou 35 | **3** — decidido; o schema de eixos da mesma sessão muda o JSON, e publicar 35 agora seria republicar 35 depois |
| frontend aguenta os campos novos | **verificado em navegador** — 3 filmes + home + degradado, zero erro de console |
| `frontend/js/data.js` + `frontend/data/*.json` | regerados por `frontend/build_data.py` |

As quatro mudanças visíveis ao leitor (shares, cota, narrativa, carimbo de
versão) estão no changelog da v1.9.14, não repetidas aqui.

## O que ficou de fora, e por quê

- **Os 31 filmes restantes do bruto.** Decisão de escopo, não impedimento
  técnico. Continua valendo o custo estimado (~35 × 6 chamadas LLM).
- **`spec_version` publicado diz `1.9.11`.** Os artefatos foram gerados com
  a constante ainda atrasada. Não reescrito à mão — ver changelog v1.9.14,
  item (2), e o mecanismo que fecha a classe em `tests/test_spec_version.py`.
- **`--offline` não reproduzível** para filme coletado sob outra estratégia
  de posicionamento — segue diagnosticado em `DIAGNOSTICO_OFFLINE.md`, e
  não bloqueou nada aqui.

---

# Histórico — o documento como estava na v1.9.12


**Não republicado nesta sessão** — por decisão explícita. Este documento diz
o que falta e o que muda para quem já viu o site.

## O que estava bloqueando, e o estado agora

Os dois defeitos que a v1.9.11 achou em `joker-folie-a-deux` eram os
bloqueios nomeados. Os dois estão **resolvidos e verificados nos 4 filmes**:

| bloqueio | estado |
|---|---|
| ficha ausente offline ⇒ narrativa não apresenta o filme | **resolvido** — ano persistido no bruto (35/35 backfillados, 19 requisições) |
| rótulo de peso idêntico em dois grupos (23/35 filmes) | **resolvido** — rótulo comparativo; colisão cai para 1/35 |

## O que ainda falta para sobrescrever `resultado/*.json`

### 1. Leitura humana dos 4 textos — o único item obrigatório

A verificação mecânica está limpa (0 flags nos 4), mas ela nunca disse que
um texto é bom: essa é a leitura do dono do projeto, e é o passo que as
v1.9.9–v1.9.12 mantiveram como não-automatizável.

### 2. Decidir o que fazer com os 31 filmes restantes do catálogo

Os `resultado/*.json` publicados são **3**. O bruto tem **35 filmes**, todos
já com ano persistido. Publicar só os 3 regenerados deixa o catálogo
incoerente com o que existe em disco; publicar os 35 é uma execução de
~35 × 6 chamadas LLM (~US$0,40 de narrativa, mais a síntese) e nunca foi
feita. **É decisão de escopo, não técnica** — nada impede as duas.

### 3. Confirmar que o frontend aguenta os campos novos

Verificado na v1.9.11: o frontend lê **apenas** `narrativa` da etapa [D2].
Os campos novos (`verificacao_narrativa`, `narrativa_selecao`, `coleta`) são
ignorados sem erro. **Não bloqueia** — mas significa que a telemetria nova
não aparece para ninguém até o item de frontend do mapa.

### 4. Nada mais é técnico

`--offline` não reproduzível (diagnosticado em `DIAGNOSTICO_OFFLINE.md`)
**não bloqueia a republicação**: os 4 filmes regeneram offline hoje. Ele
bloqueia a próxima vez que a estratégia de posicionamento mudar.

## O que a republicação muda VISIVELMENTE para quem já viu o site

Três mudanças, todas visíveis, nenhuma cosmética.

### (a) Os shares mudam — fronteiras C (v1.9.0, nunca publicadas)

| filme | publicado hoje | depois |
|---|---|---|
| `cure` | 3 / 17 / 79 | **2 / 8 / 90** |
| `cidade-de-deus` | 1 / 8 / 91 | **1 / 3 / 96** |
| `the-invite-2026` | 3 / 18 / 79 | **2 / 7 / 91** |

O grupo do meio encolhe em todos: as fronteiras C movem 2,5★ e 3,0★ de
lugar. Quem leu "17% ficaram no meio" vai ler "8%". **O dado não mudou — a
régua mudou**, e isso está registrado em §2.2 como risco aceito.

### (b) A profundidade de análise passa a ser igual entre grupos

Cota de análise de 50/20/30 para **40/40/40** por bucket. O grupo mediano
era lido com 40% da profundidade do negativo; passa a ter a mesma. Efeito
visível: os temas do grupo do meio ficam mais específicos e menos genéricos.

### (c) O texto é outro — e a diferença é de desenho, não de estilo

A narrativa publicada hoje vem do narrador pré-briefing, com editor [E2]
aplicado. A nova vem de briefing determinístico + best-of-3, sem editor.
Diferenças que o leitor percebe:

- **sem tique de quantificador** — o publicado repete "muitos" até 8 vezes;
  o novo varia dentro da faixa medida;
- **rótulos de peso distintos entre grupos** (item resolvido acima);
- **um parágrafo por grupo** no movimento 3, em vez de bloco corrido;
- **movimento 2 mais substancial** — a truncagem que o esvaziava foi
  corrigida na v1.9.9.

### (d) Metadado: `spec_version` sai de `1.6.0` e vai a `1.9.12`

Os JSONs publicados dizem `1.6.0`. Não é cosmético: é o carimbo que diz sob
qual spec aquele resultado foi produzido, e ele estava errado (parado em
`1.9.0` no código) até esta sessão.

## Recomendação de ordem

1. ler os 4 textos;
2. decidir 3 filmes ou 35;
3. republicar num único evento — republicar duas vezes seguidas (uma agora,
   outra depois do schema de eixos) é trabalho duplicado, e o mapa da
   próxima fase já registra que o schema é o item que vem antes.
