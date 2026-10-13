# Gate local (Ollama) — relatório completo da rodada

Máquina: notebook Windows 11, Ryzen 7 6800H, 16 GB RAM DDR5, RTX 3050 Laptop 4 GB VRAM. Modelo dividido entre VRAM e RAM.
Ollama com flash attention, KV cache q8_0, paralelismo 1, um modelo carregado por vez. Custo em API: US$ 0,00.

## 1. Método
- 100 reviews do gabarito humano, 10 eixos temáticos, 3 passes de classificação + verificador V2, comparados ao DeepSeek.
- Referência (DeepSeek, produção = consenso dos 3 passes + V2): F1 micro **0,811** (precisão 0,895 / recall 0,741).
- Critério de parada: IC95 de ΔF1 inteiro abaixo de zero, ou ΔF1 ≤ −0,10, ou falha (JSON inválido/truncamento) > 2%.
- gpt-oss:20b com `ESPECTRO24_OLLAMA_THINK=low` e `ESPECTRO24_OLLAMA_NUM_PREDICT=4000`.

## 2. Resultado geral

| Modelo | Completo? | F1 micro | ΔF1 micro (IC95) | Precisão / Recall | Eixos reprovados | Falhas | Gate |
|---|---|---|---|---|---|---|---|
| DeepSeek (ref.) | — | 0,811 | — | 0,895 / 0,741 | — | 0 | — |
| gpt-oss:20b | sim: 300 + 117 | 0,680 | −0,130 [−0,174; −0,088] | 0,900 / 0,546 | 6 de 10 | 0 de 417 (0 truncadas) | **PARAR** |
| qwen3:14b | sim: 300 + 228 | 0,638 | −0,173 [−0,219; −0,126] | 0,876 / 0,501 | 8 de 10 | 0 de 528 | **PARAR** |
| mistral-small3.2:24b | **não** (16 chamadas) | — | — | — | — | — | não cabe |

Sem consenso+V2 (só consenso dos 3 passes): gpt-oss 0,679, qwen3 0,639 (DeepSeek 0,791); o verificador quase não altera o F1 micro dos modelos locais.

## 3. Por eixo (produção = consenso + V2). F1; entre parênteses precisão/recall; ΔF1 vs DeepSeek com IC95

| Eixo | Positivos no gabarito | DeepSeek | gpt-oss:20b | ΔF1 gpt-oss | qwen3:14b | ΔF1 qwen3 |
|---|---|---|---|---|---|---|
| ritmo | 30 | 0,85 | 0,61 (0,88/0,47) | −0,24 [−0,42; −0,09] ✗ | 0,56 (0,92/0,40) | −0,29 [−0,48; −0,13] ✗ |
| atuacao | 33 | 0,90 | 0,82 (0,89/0,76) | −0,08 [−0,19; 0,02] | 0,77 (0,92/0,67) | −0,13 [−0,25; −0,03] ✗ |
| direcao_imagem | 42 | 0,93 | 0,89 (1,00/0,81) | −0,03 [−0,11; 0,04] | 0,93 (0,91/0,95) | 0,00 [−0,06; 0,08] |
| roteiro_estrutura | 69 | 0,84 | 0,89 (0,95/0,84) | +0,05 [−0,00; 0,12] | 0,86 (0,88/0,84) | +0,02 [−0,05; 0,09] |
| som_trilha | 20 | 0,92 | 0,83 (0,94/0,75) | −0,08 [−0,24; 0,04] | 0,74 (0,87/0,65) | −0,18 [−0,35; −0,05] ✗ |
| tom_atmosfera | 37 | 0,71 | 0,31 (0,88/0,19) | −0,40 [−0,58; −0,20] ✗ | 0,30 (0,78/0,19) | −0,41 [−0,61; −0,20] ✗ |
| impacto_emocional | 38 | 0,75 | 0,60 (0,66/0,55) | −0,15 [−0,31; 0,00] ✗ | 0,57 (0,89/0,42) | −0,18 [−0,34; −0,03] ✗ |
| comparacoes | 47 | 0,83 | 0,48 (1,00/0,32) | −0,35 [−0,50; −0,20] ✗ | 0,37 (0,92/0,23) | −0,46 [−0,62; −0,30] ✗ |
| expectativa | 40 | 0,65 | 0,40 (1,00/0,25) | −0,24 [−0,43; −0,06] ✗ | 0,25 (0,75/0,15) | −0,40 [−0,56; −0,23] ✗ |
| critica_social | 23 | 0,71 | 0,48 (0,80/0,35) | −0,22 [−0,44; −0,02] ✗ | 0,32 (0,62/0,22) | −0,39 [−0,61; −0,17] ✗ |

✗ = reprovou (IC95 inteiro < 0 ou ΔF1 ≤ −0,10). Note o impacto_emocional do gpt-oss: reprovou só por ΔF1 ≤ −0,10 (IC chega a 0,00).
Os dois modelos acertam bem os eixos concretos (direcao_imagem, roteiro_estrutura, atuacao) e falham nos subjetivos/abstratos
(tom_atmosfera, comparacoes, expectativa, critica_social). Em quase todo eixo a precisão é alta e o recall é o problema: o modelo local não marca o tema.
Eixos com poucos positivos (som_trilha 20, critica_social 23, ritmo 30) têm IC largo; leia com cautela.

## 4. Verificador V2

| | Chamadas | Remoções | Remoções corretas | Danos (tirou o que o gabarito mantinha) | Falsos positivos que sobreviveram |
|---|---|---|---|---|---|
| DeepSeek | 72×3 passes | 38 | 30 (79%) | 8 | 7 |
| gpt-oss:20b | 117 | 7 | 5 (71%) | 2 | 11 |
| qwen3:14b | 228 | 58 | 39 (67%) | 19 | 2 |

O verificador do gpt-oss é tímido (quase não remove nada); o do qwen3 é agressivo e causa mais dano.
Nenhum dos dois é o gargalo: o limite do F1 já vem da classificação (recall).

## 5. Estabilidade entre os 3 passes (reviews com os 3 passes idênticos)
- DeepSeek: 16% (Jaccard médio entre pares 0,69)
- gpt-oss:20b: 25% (Jaccard 0,68); verificador 77% idêntico
- qwen3:14b: 78% (Jaccard 0,94); verificador 96% idêntico
O qwen3 é quase determinístico, mas errando de forma consistente (recall 0,50). O gpt-oss varia tanto quanto o DeepSeek.

## 6. Desempenho e operação

| | qwen3:14b | gpt-oss:20b |
|---|---|---|
| Chamadas | 528 | 417 (300 + 117) |
| Tempo por chamada | ~11,4 s | média 13,5 s de parede (mediana 11,5; p95 27,3; máx 59) |
| Leitura do prompt | — | 1,26 s média |
| Geração | — | 9,9 s média (138 tokens em média; máx 696) |
| Prompt | — | ~1.000 tokens em média (máx 2.211) |
| JSON inválido / truncamento | 0 | 0 / 0 |
| `think` | — | `low` em 417 de 417 (nenhum "omitido") |
| Tempo total de parede | — | ~93,6 min (5.618 s) |

gpt-oss: RAM livre estabilizou em ~1,8–2,1 GB e o pagefile ficou ~2.000–2.500 MB (base 1.807–2.474), sem crescimento. Nenhuma guarda disparou.

mistral-small3.2:24b: 16 chamadas em 2h13 (~532 s/chamada), paginando para o disco. Descartado; 16 registros parciais em `mistral-small3.2-24b/` marcados com `INCOMPLETO.md`.

## 7. Registro da execução do gpt-oss:20b
1. 1ª execução: 69 chamadas, ~14 s cada, sem falhas. Terminou porque a guarda de RAM (então 0,5 GB, sem condição de pagefile) disparou com 0,46 GB livres; o pagefile estava em 1.433 MB (base 2.289), isto é, não crescia.
2. 2ª tentativa: não rodou (RAM+VRAM livres 13,28 GB contra mínimo de 13,5).
3. Mínimo reduzido de 13,5 para 13,0 GB. Justificativa: cabe (69 chamadas estáveis com a RAM em ~0,5 GB e pagefile parado); os 13,5 GB eram estimativa anterior à medição e contavam como ocupado o cache que o Windows devolve sob pressão.
4. Guardas mantidas: RAM < 0,3 GB por 3 leituras com pagefile > 256 MB acima da base → para, descarrega o modelo e registra; pagefile > 1 GB acima da base → para; `think = "omitido"` → para; truncamentos contados.
5. Teste de retomada (`-Novas 3`): 69 → 72 registros, sem refazer nenhum.
6. Execução completa (após reinício): 72 → 300 nos passes; falso alarme "PARADO" no log por código de saída vazio do `Start-Process` (os 300 registros estavam completos); script corrigido (cache do Handle; código vazio não é falha) e criado `-Etapas verificar,comparar`.
7. Verificador (117 chamadas, ~21 min) e comparação concluídos em 12/10/2026.

## 8. Recomendação
**Nenhum modelo testado serve** como substituto do DeepSeek. Ambos reprovam no agregado (IC95 do micro inteiro abaixo de zero e ΔF1 < −0,10), com zero falhas técnicas;
o problema é qualidade (recall), não robustez. O gpt-oss:20b é o melhor medido (−0,13 vs −0,17) mas ainda longe de passar.
Não usar classificação local em produção. O mistral-small3.2:24b não cabe nesta máquina.
Opções fora do escopo desta máquina (não testadas, decisão e código no Mac): recarregar crédito em API; ou insistir no local com outro modelo ou prompt voltado a recall
(os eixos que mais precisam são tom_atmosfera, comparacoes, expectativa e critica_social). Se algo local for usado de qualquer forma, preferir gpt-oss:20b (`think=low`).

## 9. Limites
- n = 100 reviews; vários eixos têm poucos positivos (20–47), ICs largos.
- Um único modelo local por família, um único prompt, think=low fixo no gpt-oss; não se testou think=medium/high nem outras quantizações.
- Nenhum código do pipeline foi alterado; os 13 testes que falham só no Windows ficaram para o Mac.
