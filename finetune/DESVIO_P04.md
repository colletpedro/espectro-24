# DESVIO_P04 — estrutura impossível de `temas` conta como JSON inválido

Data: 2026-11-04. Desvia do `PREREGISTRO_AVALIACAO.md` (seção 2, retentativa de
produção), durante a síntese do TREINADO (Fase 4), ANTES de qualquer outro par
ser gerado depois do problema. Nenhum número do treinado foi visto.

## O que aconteceu (MEDIDO)

Na 1ª execução, 13 pares foram gravados e `mother-2017/positivas` foi derrubado
uma vez pela guarda de RAM. Na 2ª, depois de 13 pares, `anatomy-of-a-murder/medianas`
levantou `AttributeError: 'int' object has no attribute 'get'` em
`synthesize._construir_temas` (`synthesize.py:2100`): o modelo devolveu JSON
válido com `temas` contendo inteiros no lugar de objetos. O código de produção
só trata JSON que não parseia; aqui ele estoura, a série parou e o par não foi
gravado (a resposta crua se perdeu). Nada parecido ocorreu nos 89 pares da base
nem no publicado.

## O que muda

Só em `scripts/finetune/gerar_sintese_teste.py` (`main` `0576943`, corrigido em `eb8f27d`), no lado treinado e
no base: a função de parse usada por `synthesize_bucket` passa a exigir a estrutura que a
produção supõe (objeto; `temas` ausente, nulo ou lista de objetos). Estrutura
impossível levanta `ValueError` e entra na regra que já existia: 1 nova chamada;
se de novo, o bucket fica sem temas ("Falha ao obter JSON válido do LLM.") e
conta como falha do modelo no C4 (não é "fora por memória"). `synthesize.py` não muda.

## Conferências

- MEDIDO: nas 89 tentativas da base, o parse estrito e o de produção dão o
  mesmo resultado (0 diferenças); a base não precisa ser regerada.
- O treinado ainda não tem nenhuma estrutura impossível gravada; os 26 pares
  gravados passaram pelo parse de produção e, por construção, também passam
  pelo estrito.
- Teste: `tests/test_finetune_fase4_cego.py` (a produção estoura no caso;
  o estrito o recusa).

## Limite

Com seed e prompt iguais, a nova chamada pode repetir a mesma saída; então o
par pode terminar como falha. É o efeito da regra pré-registrada, não de
escolha. A resposta crua da 1ª ocorrência não foi guardada.

## Correção do próprio desvio (2026-11-04)

A 1ª versão (`0576943`) tinha um erro meu: `parse_estrito` importava
`_parse_llm_json` de `synthesize` na hora da chamada, depois de o `gerar` trocar
esse nome por ele mesmo, e entrava em recursão (`RecursionError`, antes de
qualquer chamada ao modelo; nada foi gerado nem gravado). Em `eb8f27d` ele usa o corpo
original (`json.loads(_strip_fences(raw))`). Conferido fim a fim com cliente falso e o
`synthesize_bucket` real: estrutura impossível + resposta válida = 2 chamadas e
temas; duas inválidas = "Falha ao obter JSON válido do LLM.".
