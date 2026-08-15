# Editor [E2] — aposentado (v1.9.10)

O estágio de EDIÇÃO pós-narrador — reescrever a narrativa para ritmo e
leitura, sem acesso a nenhuma fonte de fato e sem poder alterar número,
rótulo ou atribuição — rodou de v1.6.0 (2026) até v1.9.9. Este diretório
guarda o código e os testes tal como estavam no momento da retirada:
**arquivado, não deletado**, mesmo padrão de `experimentos-ollama-arquivado/`.

## Por que foi aposentado

Decisão do dono do projeto, depois de ler as 3 narrativas do best-of-3
(v1.9.9) geradas **sem** passar pelo editor: o ritmo se sustenta sem o
estágio. A alternativa considerada — reescopar o editor por MOVIMENTO (3
blocos), que tornaria inversão de ordem impossível por construção — foi
preterida porque não elimina as outras duas classes de falha do estágio
(conteúdo inventado, edição descartada por esgotar tentativas), que
exigiriam mitigação própria em cada bloco. Deletar o estágio inteiro deleta
as TRÊS classes de falha de uma vez:

- **4 tentativas de edição descartadas em `cure`** (v1.7.1) — variância do
  modelo entre chamadas; a MESMA combinação de código e dados tinha sido
  aceita nos 3 filmes sob a versão anterior;
- **parágrafo de opinião inventado, sem origem no texto recebido**, em
  `the-invite-2026` (v1.8.0) — a checagem de conteúdo adicionado ainda não
  existia quando o defeito ocorreu;
- **inversão de movimentos** (v1.8.0), que motivou a checagem de ordem
  correspondente.

## O que está aqui

- `editor.py` — o módulo inteiro: `EdicaoResult` (antes em `models.py`),
  as constantes `EDITOR_*` (antes em `config.py`), `_EDITOR_SYSTEM_PROMPT`,
  `montar_protegidos`, `editar_narrativa`, e toda a maquinaria de checagem
  exclusiva do editor (conteúdo adicionado, ordem de movimento, edição
  nula, capitalização residual). Ainda importa um punhado de funções
  PRIVADAS de `espectro24.synthesize` — deliberado, ver o docstring do
  módulo.
- `test_editor.py` — os 55 testes originais de `tests/test_editor.py`, mais
  2 movidos de `tests/test_fluencia.py` (o few-shot de ritmo era exclusivo
  do prompt do editor). Roda isolado (`pytest
  experimentos-editor-e2-arquivado/`), não faz parte de `pytest tests/`.

## O que NÃO veio junto (ficou vivo, porque não é exclusivo do editor)

As checagens que validam o texto SOZINHO — não uma comparação bruto×editado
— continuam em `synthesize.py`/`qualidade.py`, e agora verificam o
NARRADOR: `_ancoragem_de_peso_ok`, `_marcadores_validos`, `_validar_prosa`,
`qualidade.formato_invalido`, `qualidade.numeros_inventados`,
`qualidade.rotulos_peso_faltando`, `qualidade.ordem_dos_grupos_ok`, e as
da v1.9.9/v1.9.10 (`quantificadores_fora_de_faixa`/`repetidos`,
`problemas_de_paragrafo`, `grupos_sem_paragrafo_proprio`).

## Como rodar isto de novo (não recomendado)

Não é uma opção de configuração — `cli.py` não importa mais nada daqui.
Para explorar o código isoladamente:

```bash
python -m pytest experimentos-editor-e2-arquivado/
```

Ver `SPEC.md`, seção "Fechamento do narrador" (v1.9.10), para o registro
completo da decisão.
