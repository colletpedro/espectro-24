# Passes DeepSeek arquivados — exceção C22 (2026-09-22)

Registros de classificação DeepSeek (`deepseek-v4-flash`, roteado para o
V4.1-Flash) dos 55 filmes do lote noturno de 2026-09-18
(`dados/lote/lista-noturno-2026-09-18.txt`): passes 1 e 2 completos, passe 3
em 38% quando o saldo DeepSeek acabou. Pagos (~US$1,75, ABERTO.md C19).

**Por que saíram de `passe_*.jsonl`:** o dono decidiu não recarregar o
DeepSeek e refazer os TRÊS passes destes 55 em Gemini (ABERTO.md C22). Não
completar o passe 3 em Gemini sobre os passes 1-2 DeepSeek: a votação de 3
pressupõe três sorteios do MESMO modelo, e misturar provider dentro do voto
quebra a premissa sem volta. Um provider por filme.

**Por que não foram apagados:** foram pagos, e são a única classificação
V4.1-Flash com `ts` destes filmes — servem para recoletar em DeepSeek no
futuro (reaproveitando os passes 1-2) ou para comparar os dois provedores
sobre o mesmo volume.

Linhas copiadas com os bytes originais, na ordem original.
Script: `scripts/arquivar_passes_c22.py`.
