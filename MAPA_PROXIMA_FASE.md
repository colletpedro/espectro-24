# Mapa da próxima fase — o que falta para publicar (Entrega 6, v1.9.10)

Levantamento, **sem implementação**. Nenhum item aqui foi tocado nesta
sessão; a lista é o material para o dono do projeto decidir a ordem da
próxima sessão.

## Os itens, e o que cada um exige

### 1. Ligar o narrador novo ao pipeline de produção

**Estado hoje:** `cli.py` (o pipeline que `espectro24 --slug X` roda)
continua chamando o narrador ANTIGO (`narrate_output`, pré-briefing,
§D2 v1.2.0-1.9.7) e não chama editor nenhum (retirado). O briefing
determinístico (v1.9.8), as correções de prosa (v1.9.9/v1.9.10) e o
best-of-3 (`selecao_narrativa.py`) só existem em `scripts/best_of_3.py` —
rodam sob demanda, fora do pipeline principal.

**O que falta:** trocar a chamada em `cli.py` de `narrate_output` para
`briefing.montar_briefing` + `PROMPT_NARRADOR_BRIEFING` + best-of-3, com
`MODELO_POR_ESTAGIO["narrativa"]` (já fixado). Decisão a tomar: manter o
caminho antigo acessível (a spec já registra que ele "permanece testado,
para a comparação continuar possível") ou substituí-lo de vez.

**Por que vem primeiro:** é pré-requisito de TUDO que segue — nenhum dos
outros itens muda o que já está em produção enquanto o pipeline não usa o
narrador novo.

### 2. Republicar `resultado/*.json` com o narrador novo

**Depende de (1).** Fora de escopo desta sessão E da anterior por decisão
explícita ("republicar `resultado/*.json`"). Assim que (1) estiver pronto,
é o passo natural para os 3 filmes do catálogo saírem do estado atual
(narrador antigo, sem best-of-3) para o de produção.

**Recomendação:** combinar com o item 5 (seleção S2) num único evento de
republicação, se S2 for adotado — dois republish em sequência para o
MESMO filme, um logo depois do outro, seria trabalho duplicado.

### 3. Schema de eixos, lift e estado `contraste`

**Não depende de (1)/(2).** É mudança na camada de CLASSIFICAÇÃO (§D),
que fica em DeepSeek e está calibrada/auditada — o briefing e o narrador
leem `temas` como estrutura de saída da classificação; se o schema mudar
(eixos, lift, estado `contraste`), o formato de `temas` que
`briefing.montar_briefing` consome muda junto.

**Por que interessa à ordem:** a spec já registra (v1.9.5) que a aplicação
da seleção S2 (item 5) foi adiada explicitamente "para a sessão do
schema, para não invalidar a classificação de eixos em paralelo" — os dois
temas foram sempre tratados como acoplados no planejamento do projeto.
Decidir esta sessão ANTES de (2) evita publicar `resultado/*.json` duas
vezes com o narrador novo (uma vez com o schema atual, outra com o novo).

### 4. Janela temporal da amostra, declarada na interface

**Depende de (5)** ou é motivada por ela: `janela_temporal`/
`distribuicao_pagina_origem` já são gravados em `meta.json` desde a
v1.9.1/v1.9.2, mas **não expostos ao frontend** (decisão explícita
registrada). Se a seleção S2 (mistura 70/30 de material recente/antigo)
for adotada, a janela deixa de ser um detalhe de coleta e passa a
descrever um material que o narrador está de fato lendo — omiti-la da
interface deixaria de ser neutro.

**O que falta:** decidir o formato de exibição (texto simples? faixa de
datas? não é frontend deste projeto — ver item 6) e o texto que a
acompanha, sem reintroduzir número-síntese (§1) nem contradizer o
princípio de neutralidade (§0).

### 5. Seleção temporal S2 (70/30 recente/antigo)

**Medida e recomendada, não aplicada** (§3[C2], v1.9.5). Decisão já
tomada sobre QUAL variante (S2, com o parâmetro 70/30 declarado como
arbitrário) — falta só aplicar. Bloqueada, por decisão registrada, até a
sessão do schema (item 3) e até estar pronta para o republish (item 2).

### 6. Frontend não conhece nenhum campo novo

**Depende de (2), (3) e (4) estarem decididos** — não faz sentido mexer
no frontend antes do schema final estabilizar, sob risco de precisar
mexer duas vezes. Campos que o frontend hoje NÃO lê: `estado_piso`
(4 estados, v1.9.0), `distribuicao`/`marcacao_perspectiva` do briefing
determinístico, `distribuicao_pagina_origem`/`janela_temporal` (se o
item 4 decidir expô-los), e qualquer campo novo de eixos/lift do item 3.

## Ordem recomendada (não vinculante — decisão do dono do projeto)

```
3 (schema de eixos/lift/contraste)
   │
   ├──▶ 5 (aplicar S2, já recomendado)
   │        │
   1 (ligar narrador novo ao pipeline)      │
   │                                        │
   └────────────┬───────────────────────────┘
                ▼
        2 (republicar resultado/*.json — UMA vez, com tudo decidido)
                │
                ▼
        4 (janela temporal na interface)
                │
                ▼
        6 (frontend lê os campos novos)
```

`1` (ligar o narrador ao pipeline) é independente dos demais e pode
acontecer em paralelo a `3`/`5` — só precisa terminar antes de `2`.

## Fora do escopo desta lista

Este mapa não avalia CUSTO nem prazo de nenhum item — é só dependência
estrutural. Também não inclui parâmetros de coleta ou de classificação já
fechados (fronteiras de bucket, cota, piso escalonado, calibração de
`classificacao`), que continuam fora de escopo por decisão de sessões
anteriores.
