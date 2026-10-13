# Relatório do gate local

> Nota (2026-10-11): o arquivo `relatorio_gate_local.md` citado nas instruções não existia nesta máquina
> (procurado em `~/espectro-24-run` e em todo o `~`). Este arquivo foi criado agora apenas com o que foi
> verificado nos logs e no resultado. O histórico qwen3/mistral abaixo vem do resumo do dono, não de um relatório anterior.

## Resumo dos modelos (a confirmar nos logs na sessão final)
- qwen3:14b — completo, não passou: F1 micro 0,638 vs 0,811 (DeepSeek); 8/10 eixos reprovaram; 0 JSON inválido; 11,4 s/chamada.
- mistral-small3.2:24b — não cabe: 16 chamadas em 2h13, 532 s/chamada (paginação em disco). 16 registros parciais, a marcar como incompletos.
- gpt-oss:20b (think=low, num_predict=4000) — em andamento.

## 2026-10-11 — gpt-oss:20b: mínimo de memória 13,5 → 13,0 GB
Justificativa: na 1ª execução o gpt-oss:20b rodou 69 chamadas estáveis com a RAM em ~0,5 GB e o pagefile parado — cabe.
Os 13,5 GB eram estimativa anterior a qualquer medição e contam como ocupada a memória de cache que o Windows devolve sob pressão.
Na 2ª tentativa, a conferência deu 13,28 GB (RAM+VRAM) e o gate não rodou.

Observação sobre a 1ª execução: ela terminou porque a guarda de RAM (então 0,5 GB, sem condição de pagefile) disparou com
0,46 GB disponíveis na chamada 69; o pagefile estava em 1433 MB (base 2289), isto é, não crescia.

Mudanças no `rodar_gate_gptoss.ps1` (script de execução, não é código do pipeline):
- `MinSomaGB` 13,5 → 13,0 (registrado no log a cada início).
- Mantidas: guarda de RAM (< 0,3 GB por 3 leituras **com** paginação > 256 MB acima da base → para, descarrega o modelo e registra o motivo);
  guarda de crescimento do pagefile (> 1024 MB); parada se algum registro tiver `think = "omitido"`; contagem de truncamentos nos checkpoints.
- Base da paginação agora é medida após o 1º registro NOVO (antes, na retomada, seria medida antes de o modelo carregar e poderia disparar a guarda de crescimento falsamente).
- Novo parâmetro `-Novas N`: retoma do que existe, para após N chamadas novas, mantém os registros (o `-Teste` apaga o que grava e se recusa a rodar com resultado existente).
- Sem checkpoint espúrio dos registros antigos na retomada.

Teste de retomada (`-Novas 3`, 18:32–18:34, app do Claude aberto, RAM+VRAM livres 11,69 GB, soma ignorada no modo teste):
69 → 72 registros, 72 ids ok distintos, 0 repetidos, 0 truncados, think=low nos novos. Retomou sem refazer nenhuma das 69.
Estado ao fim: 72 de 100 no passe 1; faltam 28 do passe 1 + passes 2 e 3 + verificador.

## 2026-10-11 — execução completa dos passes (gpt-oss:20b)
Retomou de 72 e concluiu os 3 passes: 100/100 ok em cada, 0 truncados, 0 falhas, think=low em todos, sem repetidos.
Tempo ~11 s/chamada de geração + ~1,2 s de leitura do prompt; RAM livre estabilizou em ~1,8–2,1 GB; pagefile 1807→~2030 MB (base 1807) — nenhuma guarda disparou.
O log registrou "PARADO: etapa 'passes' terminou com codigo (vazio)": falso alarme do script (ExitCode vazio do Start-Process, tratado como diferente de 0).
Corrigido (cache do Handle; código vazio não é falha) e criado `-Etapas verificar,comparar` para rodar só o que faltou. Verificador e comparação ainda NÃO rodaram.
