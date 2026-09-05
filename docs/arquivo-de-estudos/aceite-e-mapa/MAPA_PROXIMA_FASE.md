# Mapa da próxima fase — o que falta (v1.9.14)

Levantamento, **sem implementação**. Substitui a versão da v1.9.11, cujos
itens 1, 2, 4 e 5 foram ENTREGUES nesta sessão e saíram da lista.

## O que saiu da lista

- **Republicar `resultado/*.json`** — feito (3 filmes; ver
  `ESTADO_REPUBLICACAO.md` e o changelog da v1.9.14).
- **Schema de eixos, lift e estado `contraste`** — feito, com [D3] como
  etapa nova e duas correções que só o dado real expôs.
- **Janela temporal na interface** — feita, sobre a amostra ANALISADA.
- **Frontend não conhece os campos novos** — as três colunas alinhadas, a
  busca real e a janela estão no ar; a telemetria de narrativa
  (`verificacao_narrativa`, `narrativa_selecao`) segue não exibida, por
  decisão: é diagnóstico de produção, não informação de leitor.

## Os itens, e o que cada um exige

### 1. A amostra CLASSIFICADA não é a amostra ANALISADA (NOVO, e é o maior)

Achado e medido na v1.9.14 (§[D3]): `amostra.json` foi montada sem a
estratificação por profundidade da v1.9.5, então as 40 reviews classificadas
de um bucket não são as 40 que a síntese leu. Sobreposição **mediana de 75%
no catálogo, mínima de 30%**; os 3 filmes publicados são os piores casos
(`cidade-de-deus`/negativas: 13/40).

Hoje isto está **declarado** — no JSON (`fonte_classificacao`), na interface
(denominador rotulado "classificadas") e na spec. A correção estrutural é
**estender** a classificação às reviews da seleção de produção que ainda não
a têm: ~191 reviews nos 3 filmes publicados, ~573 chamadas com a votação de
3, sob o MESMO `taxonomia_id` e o MESMO prompt. Não é reclassificar o corpus
— é classificar o que nunca passou.

**Consequência a considerar ANTES de fazer:** os 3 filmes passariam a ser
medidos sobre uma amostra diferente da dos outros 32, e o lift de cada um
pode mudar — inclusive o estado `contraste` de `cidade-de-deus`.
**Depende de:** decisão de escopo. **Bloqueia:** a honestidade plena do
denominador, hoje sustentada por declaração.

### 2. Seleção temporal S2 (70/30 recente/antigo)

Medida e recomendada na v1.9.5, não aplicada; a spec registrava que a
aplicação ficaria "para a sessão do schema". **O schema chegou e S2 não
foi aplicada** — por escopo declarado, não por impedimento. Note que aplicar
S2 muda a seleção de produção e, portanto, **agrava o item 1**: a amostra
analisada se afastaria ainda mais da classificada. Os dois devem ser
decididos juntos.

### 3. O passe de verificação de `impacto_emocional` (NOVO na lista)

Medido na fase de classificação, nunca aplicado: leva a precisão do eixo de
**0,486 para 0,794** em passada única (~3013 chamadas, ~US$ 0,10). O efeito
observado na v1.9.14 dá urgência ao item: **`impacto_emocional` ocupa uma
das duas vagas de consenso em 9 dos 9 buckets dos 3 filmes publicados** — o
eixo menos confiável do schema é o mais exibido. Rodá-lo muda a frequência
de todos os 35 filmes e, com ela, lift e `contraste`.

### 4. Frontend sem teste automatizado

Não há runner de JS no projeto, e `filme.js` saiu de ~330 para ~630 linhas
nesta versão. A verificação é o roteiro manual de `frontend/TESTE_MANUAL.md`
(27 cenários), que já achou uma regressão real. É a maior dívida de teste do
projeto hoje.

### 5. `--offline` não é reproduzível após mudança de posicionamento

Inalterado desde a v1.9.11, e continua não bloqueando ninguém. Segue
diagnosticado em `DIAGNOSTICO_OFFLINE.md`, aguardando decisão.

### 6. Publicar os 35 filmes do bruto

Nunca feito. Agora o custo inclui [D3] (3 chamadas/filme) além da síntese e
da narrativa. **Depende de:** itens 1 e 3, se a intenção for publicar sob a
classificação corrigida em vez de republicar depois.

## Ordem recomendada (não vinculante)

```
3 (verificador de impacto_emocional)
   │
   └──▶ 1 (estender a classificação)  ──▶  2 (aplicar S2)
                     │
                     └──▶ 6 (publicar os 35)

4 (teste de frontend) — independente, e quanto antes melhor
5 (--offline) — independente, sem bloquear ninguém
```

Os itens 1, 2 e 3 mexem todos na mesma coisa — **quais reviews contam para a
frequência de um eixo** — e cada um invalida a medição do outro se feito
isolado. Fazer os três numa sessão só custa uma rodada de classificação;
fazer um por sessão custa três.
