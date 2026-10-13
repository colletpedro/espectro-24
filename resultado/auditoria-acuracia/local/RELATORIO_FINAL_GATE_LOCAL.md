# Gate local (Ollama, notebook RTX 3050 4 GB / 16 GB RAM) — relatório final

Referência: DeepSeek, F1 micro 0,811 (produção = consenso de 3 passes + verificador V2). 100 reviews do gabarito humano.
Critério de parada: IC95 de ΔF1 inteiro < 0, ou ΔF1 ≤ −0,10, ou falha > 2%.

| Modelo | Completo? | F1 micro | ΔF1 micro (IC95) | Eixos reprovados | Falhas (JSON/truncamento) | Tempo/chamada | Gate |
|---|---|---|---|---|---|---|---|
| qwen3:14b | sim (300 + 228 verificador) | 0,638 | −0,173 [−0,219; −0,126] | 8 de 10 | 0 | ~11,4 s | **PARAR** |
| gpt-oss:20b (think=low, num_predict=4000) | sim (300 + 117 verificador) | 0,680 | −0,130 [−0,174; −0,088] | 6 de 10 | 0 (0 truncadas) | ~11 s geração + ~1,2 s prompt | **PARAR** |
| mistral-small3.2:24b | **não** — 16 chamadas | — | — | — | — | ~532 s (paginando em disco) | não cabe |

Eixos reprovados — gpt-oss: ritmo, tom_atmosfera, impacto_emocional, comparacoes, expectativa, critica_social.
qwen3: ritmo, atuacao, som_trilha, tom_atmosfera, impacto_emocional, comparacoes, expectativa, critica_social.

## O que os números dizem
- Os dois modelos completos reprovam no critério de parada, inclusive no agregado (IC95 do micro inteiro abaixo de zero e ΔF1 < −0,10).
- O gpt-oss:20b é melhor que o qwen3:14b (+0,04 de F1 micro, 2 eixos a menos reprovados), mas a diferença entre os dois não muda o veredito.
- Perfil de erro: o gpt-oss é conservador. Precisão 0,90 (DeepSeek: 0,89), porém recall 0,55 (DeepSeek: 0,74): deixa passar cerca de metade dos temas
  que os humanos marcaram. O qwen3 tem recall parecido (0,50) com precisão menor (0,88 na produção).
- Verificador: o do gpt-oss removeu pouco (7 remoções, 5 corretas, 2 danos; 11 falsos positivos sobreviveram); o do qwen3 removeu 58 (39 corretas, 19 danos).
  O do DeepSeek: 38 remoções, 30 corretas, 8 danos.
- Reprodutibilidade entre os 3 passes (idênticos): gpt-oss 25%, qwen3 78%, DeepSeek 16%.
- Operacional: sem JSON inválido, sem truncamento, ~11 s/chamada em ambos; o gpt-oss rodou com RAM livre ~1,8–2,1 GB e pagefile estável (cabe de fato).

## Recomendação
**Nenhum dos modelos testados serve** como substituto do DeepSeek neste notebook. Nenhum passa o gate; o melhor (gpt-oss:20b) fica 0,13 abaixo
e perde sobretudo em recall. Não usar a classificação local em produção. Os modelos maiores (mistral-small3.2:24b) não cabem na máquina.
Caminhos que ficam fora desta máquina/escopo (não testados): recarregar crédito em API; ou, se quiser insistir no local, tentar outro modelo/prompt
voltado a recall — isso é decisão e alteração de código a fazer no Mac. Se for usar algo local mesmo assim, o gpt-oss:20b (think=low) é a melhor opção medida.

## Notas
- Execução do gpt-oss: mínimo de memória baixado de 13,5 para 13,0 GB (justificativa em `~/espectro-24-run/relatorio_gate_local.md`).
  Houve um falso "PARADO" no log (código de saída vazio do `Start-Process`) ao fim dos passes; os 300 registros estavam completos e o script foi corrigido.
- Nenhum código do pipeline foi alterado; os 13 testes que falham só no Windows não foram tocados.
