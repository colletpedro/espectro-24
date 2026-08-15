# Narrador PRÉ-BRIEFING [D2] — arquivado (v1.9.11)

Foi o narrador de produção da **v1.2.0 até a v1.9.10**. Este diretório
guarda o código e os testes como estavam no momento da retirada:
**arquivado, não deletado**, mesmo padrão de `experimentos-ollama-arquivado/`
e `experimentos-editor-e2-arquivado/`.

## O desenho que saiu, e o que entrou no lugar

| | narrador antigo (aqui) | narrador de produção (`espectro24/narrador.py`) |
|---|---|---|
| entrada | o JSON validado inteiro, serializado | um BRIEFING pronto (o código já escolheu tema, ordem, ênfase) |
| invariantes | ~18 como INSTRUÇÃO no prompt | 10 viraram dado; as não-computáveis seguem no prompt |
| quem escolhe | o LLM escolhe, o código audita | o código escolhe, o LLM só verbaliza |
| verificação | sobre campos que o LLM DECLARAVA (`consensos_usados`, `quantificadores_usados`, `marcadores_perspectiva`) | sobre o TEXTO (`qualidade.verificar`) |
| amostras | 1 chamada | `BEST_OF_N` chamadas + seleção por código |

## Por que foi arquivado só agora

A substituição do desenho aconteceu na v1.9.8 (briefing determinístico), e
as v1.9.9/v1.9.10 corrigiram os defeitos de prosa e acrescentaram o
best-of-3. **Mas nada disso estava no pipeline:** até a v1.9.10 o `cli.py`
continuava chamando `narrate_output` daqui, e todo o trabalho novo vivia em
`scripts/best_of_3.py`, rodando à parte. A v1.9.11 integrou — e só então
este código ficou sem chamador.

## O que está aqui

- `narrador_antigo.py` — os prompts (`NARRATOR_SYSTEM_PROMPT*`,
  `_NARRADOR_PARTE_*`, as duas variantes da regra (c)), os blocos de
  reforço de retentativa, `build_narrator_prompt`,
  `_serialize_output_for_narrator`, `narrate_output`, e as validações de
  campo DECLARADO (consensos, quantificadores por par, marcadores).
- `test_narrate.py` — os 58 testes do arquivo dedicado ao estágio. Roda
  isolado (`pytest experimentos-narrador-antigo-arquivado/`), fora de
  `pytest tests/`.

## O que NÃO veio junto, e por quê

A fronteira aqui é **mais estreita que a do editor [E2]**, por uma razão
medida: o editor era um bloco contíguo com uma entrada e testes próprios; o
narrador antigo tem ~60 nomes no fecho de chamadas, e boa parte é
**maquinaria COMPARTILHADA** — `_rotulo_peso`, `_marcacao_perspectiva`,
`_pesos_por_bucket`, `_marcadores_validos`, `_ancoragem_de_peso_ok`,
`_validar_prosa`, `_metricas_fluencia`, `conferencia_quantificador` — usada
por `render.py`, pelo editor arquivado e por scripts de diagnóstico. Ela
**fica em `synthesize.py`**, e este módulo a importa (mesmo padrão do
editor). Arrastá-la para cá criaria duas fontes de verdade para a mesma
checagem.

Resíduo declarado: `tests/test_fluencia.py` e `tests/test_distribuicao.py`
têm testes que exercitam o narrador antigo misturados a testes da
maquinaria compartilhada (15 de 51 e 19 de 46). Eles **continuam em
`tests/`** e importam daqui — separá-los exigiria partir os dois arquivos
teste a teste, e o ganho não paga o risco. O que importa está garantido: o
pipeline tem UM caminho.

## Como rodar (não recomendado)

```bash
python -m pytest experimentos-narrador-antigo-arquivado/
```

Ver `SPEC.md`, seção "Integração" (v1.9.11), para o registro da decisão.
