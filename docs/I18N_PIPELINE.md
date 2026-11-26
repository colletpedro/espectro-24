# Inglês no pipeline: caminho proposto

Status: proposta, nada implementado. Estimativas de token são premissas (sem rede, sem tokenizador do provider); o primeiro passo do plano as substitui por medida. Regra do dono: medir antes de implementar; resultado negativo é entrega válida.

## 1. Estado atual

Fluxo hoje, 100% offline e sem LLM:

```
resultado/<slug>.json (PT, gerado pelo pipeline)
  -> scripts/i18n_extrair_en.py   extrai as strings PT que o front renderiza
  -> dados/traducao_en/<slug>.json + _vocabulario.json   {"<PT>": "<EN>"|null}
  -> agentes Claude preenchem os null seguindo dados/traducao_en/_GUIA.md
  -> frontend/build_traducao_en.py (chamado por build_data.py) -> frontend/js/data_en.js, data_en_home.js
  -> frontend/js/filme.js: traduzido(slug, pt) = filme.textos[pt] || vocabulario[pt] || null
```

- Chave = string PT byte a byte. Não há id estável por campo; a tradução segue o texto, não a posição.
- Extraído (`textos_do_filme`): `veredito.texto`; `buckets[].temas[].tema` e `.exemplo_parafraseado` (bucket `sem_analise` fora); `condicoes.{vale_a_pena,talvez_evite}[].texto`; `narrativa` (um parágrafo por chave, `split(/\n{2,}/)`); `ficha.generos[]` (vocabulário). Mais `titulo_en` por filme.
- Vocabulário: gêneros e temas que aparecem em 2 ou mais filmes (146 chaves). Total atual: 128 filmes, 5.547 strings por filme + 146 de vocabulário = 5.693; cerca de 680 mil caracteres PT (média 5.315 chars e 43 strings por filme: narrativa ~1.250, veredito ~160, condições ~570, o resto temas e exemplos).
- Quando o PT muda (filme regenerado): `fonte_sha256` do arquivo deixa de bater com `resultado/<slug>.json`. O extrator reexecutado marca `null` nas strings novas e move as que sumiram para `_orfaos` (guardadas, voltam se a string voltar). O build avisa (`AVISO traducao_en: ... regenerado depois da tradução`) e omite do `data_en.js` as traduções cuja chave PT não existe mais. No front, string sem tradução cai para o PT, com `lang="pt-BR"` no elemento e o aviso `aviso-analise-pt` na página.
- Testes que já travam o formato: `tests/test_traducao_en.py` (completude, números/%/~/quebras idênticos ao PT, condição EN minúscula sem ponto e sem you/if/who, tema sem ponto final, idempotência do extrator, data_en.js determinístico).
- O `_GUIA.md` é feito para tradutor humano/agente: tem inventário (§2), regras de registro, neutralidade e quantificadores (§3, §6), forma das condições (§4), checklist (§5). §3, §4 e §6 já são, na prática, especificação de prompt.

## 2. Inventário: o que precisa de EN e onde nasce

| Campo EN necessário | Gerado em (PT) | Prompt | Notas |
|---|---|---|---|
| `buckets[].temas[].tema`, `.exemplo_parafraseado` | `synthesize.synthesize_bucket` (1 chamada por bucket, 3 por filme; retry de idioma/escopo; fallback de quantidade) | `synthesize.build_system_prompt(bucket)`, reforços `_REFORCO_VALIDACAO`, `_REFORCO_QUANTIDADE` | Em produção do C22 a síntese entra pronta via `montagem_offline.aplicar_sintese` (`bucket_final`); `exemplo_antes_da_guarda` guarda o texto antes da guarda de quantidade. |
| `buckets[].observacao_geral` | idem | idem | Não renderiza; fora do escopo EN. |
| `narrativa` | `narrador.narrar` (best-of-3 + retry direcionado) sobre o briefing de `briefing.montar_briefing` | `briefing.PROMPT_NARRADOR_BRIEFING` (4.542 chars), retry em `selecao_narrativa.prompt_retry` | Modelo de estágio: `gemini-3.7-flash` (`config.MODELO_POR_ESTAGIO`). Rótulos de peso ("a maioria das notas (~N%)") vêm do código: `briefing.rotulos_peso`, `COMPARATIVOS_PESO`. |
| `veredito.texto` | `veredito.gerar` (best-of-3) sobre `veredito.montar_briefing` | `veredito.PROMPT_VEREDITO` (3.551 chars) | `veredito.prefixo_de_codigo` ("O meio-termo é o maior grupo da recepção (~N% das notas).") é concatenado pelo CÓDIGO, fora do modelo; em EN precisa de template próprio. Hoje 0 dos 128 usam. |
| `condicoes.*[].texto` | `condicoes.gerar` (best-of-3) sobre `condicoes.montar_briefing` | `condicoes.PROMPT_CONDICOES` (9.311 chars) | Publicadas por `scripts/publicar_condicoes.py` (valida com `condicoes.validar`, aplica retiradas R13). Texto de autoria humana (`origem: leitura_humana`) passa só por validadores exatos. |
| `ficha.generos`, títulos | TMDB/Letterboxd (`ficha.py`, `identidade.py`) | nenhum | `titulo_en` vem do Letterboxd quando há identidade guardada; 33 filmes foram preenchidos à mão. Não depende de LLM de síntese. |
| strings montadas por código | `briefing._rotulo_peso_completo`, `quantificador.ROTULOS`, `veredito.prefixo_de_codigo`, nota de amostra | n/a | Determinísticas: devem ter template EN em código, não passar por LLM. |

Montagem offline (`montagem_offline.montar_documento`) isola a síntese injetável e termina antes de condições e build; é aí que um estágio EN se encaixa (depois de condições, antes de `build_data.py`).

### Guardas que dependem de PT

Todas rodam sobre o texto PT e continuam valendo sem mudança se o EN for derivado do PT já validado (opção A). Só viram trabalho novo se o EN for gerado antes ou em paralelo (B, C).

| Guarda | Onde | Dependência de PT |
|---|---|---|
| Quantificadores canônicos e faixas | `quantificador.BANDAS_FRACA_PARA_FORTE`, `ROTULOS`; `qualidade.quantificadores_fora_de_faixa`, `quantificadores_repetidos`, `_padrao_construcao` (flexão de gênero PT); `veredito._quantificador_divergente`, `_deflacao_por_hedge` | léxico PT ("poucos"…"quase todos", "relatos pontuais") |
| Quantidade proibida em exemplo/condição | `guarda_quantidade.reescrever`, `palavras_quantidade.txt` (sha congelado `a7fcd5a5…`); `condicoes._RE_QUANTIDADE` | lista PT, regras de concordância verbal PT |
| Peso das notas vs reviews | `qualidade._PESO_PROIBIDO`, `vocabulario_peso_violado`, `rotulos_peso_faltando`, `ocorrencia_rotulo` (contrações "da/na/pela") | regex PT |
| Escopo generalizado | `veredito._ESCOPO_GENERALIZADO`, `synthesize._tem_marcador_de_escopo`, `condicoes._ESCOPO_GENERALIZADO` | frases PT |
| Nota/score/estrela | `veredito._NOTA_OU_SCORE`, `condicoes` idem | regex PT |
| Contraste fabricado | `veredito._CONTRASTE_FABRICADO` | frases PT |
| Clichê de resenha | `dados/blocklist_resenha.txt` via `qualidade.achar_resenha_speak` | lista PT |
| Perfil de leitor | `condicoes._PERFIL_DE_LEITOR` | frases PT |
| Âncora e discriminação | `condicoes._validar_ancora`, `_validar_discriminacao`, `palavras_copiaveis`, `nomes_proprios`, `_prefixos` (radical por prefixo, sem acento) | morfologia PT |
| Anti-spoiler lexical | `condicoes._MARCADORES_SPOILER`, `risco_de_spoiler`, `veredito._MARCADORES_EIXO` | léxico PT |
| Idioma | `synthesize._idioma_e_pt_br` (stopwords PT vs EN) | em EN a checagem inverte |
| Forma | `condicoes.TETO_PALAVRAS` (14), minúscula inicial, abertura "Vale a pena se você…"; `veredito` 55 palavras, 2 frases | a abertura em EN é "Worth it if you…" / "Maybe skip it if you…" (já fixada no `_GUIA` §4) |
| Independentes de idioma (reaproveitáveis) | dígitos (`\d`), aspas, `numeros_inventados`, `tokens_numericos`, quebras de linha, cobertura de parágrafos por grupo | nenhuma |

Neutralidade (`SPEC.md` §0, §3[V] 8b "mesmo tratamento para os dois lados", §3[CD]) hoje é garantida por três coisas: números e rótulos decididos por código, validadores lexicais e leitura humana. Nenhum validador mede simetria de tom; o que protege o EN é herdar o PT validado e verificar que o mapeamento de quantificadores é 1:1.

## 3. Opções de arquitetura

Premissas de custo (a medir no passo 0): PT ≈ 3,3 chars/token, EN ≈ 4,0 chars/token, preço de `src/espectro24/preco.py` (`deepseek-v4-flash`). Por filme: entrada ≈ 1.900 tokens (5.315 chars PT = 1.610, mais ~290 de ids/JSON), saída ≈ 1.600 tokens (5.255 chars EN = 1.310, mais ~290), prompt fixo ≈ 6.000 tokens (`_GUIA` 12.410 chars ≈ 3.800, mais exemplos e instruções), identico entre filmes e portanto elegível a cache. Tabela `preco.py`: fora de pico US$ 0,15 miss / 0,003 hit / 0,60 saída por M tokens; pico 0,30 / 0,006 / 1,20.

Aviso: `TABELA_VERIFICADA_EM` = 2026-09-18, hoje 2026-11-26 (69 dias, validade 30). `aviso_de_validade()` dispararia. Reler a página de preço antes de qualquer depósito.

### A. Tradução pós-síntese com LLM, gravando em `dados/traducao_en/`

Uma chamada por filme: recebe a lista de strings PT sem tradução (com id curto e papel: veredito, tema, exemplo, condição lado X, parágrafo), devolve lista de EN pelo mesmo id. Modelo sem raciocínio oculto.

Conta por filme, fora de pico:
- quente (prefixo em cache): 1.900 × 0,15/M + 6.000 × 0,003/M + 1.600 × 0,60/M = 0,000285 + 0,000018 + 0,000960 = US$ 0,00126
- frio (sem cache): 7.900 × 0,15/M + 1.600 × 0,60/M = 0,001185 + 0,000960 = US$ 0,00215

Pico: quente 1.900 × 0,30/M + 6.000 × 0,006/M + 1.600 × 1,20/M = 0,00057 + 0,000036 + 0,00192 = US$ 0,00253; frio US$ 0,00429.

Para 128 filmes: fora de pico US$ 0,16 (quente) a 0,28 (frio); pico US$ 0,32 a 0,55. Com 15% de retentativa: US$ 0,19 fora de pico, 0,37 pico. Vocabulário (146 strings, ~1.100 tokens de entrada, ~900 de saída): US$ 0,0016 fora de pico. Mesma ordem de grandeza na Featherless `DeepSeek-V4.1-Flash-1017` (prompt 0,225, completion 0,9 por M): ~US$ 0,003 por filme sem cache.

- Prós: PT validado é a fonte (todas as guardas da seção 2 já passaram); formato idêntico ao atual, front e `build_traducao_en.py` não mudam; reaproveita o `_GUIA` como prompt; regenerar um filme só retraduz o que mudou; custo desprezível; baseline de 5.693 strings para medir; falha isolada e reexecutável.
- Contras: é tradução, não geração: carrega qualquer defeito do PT; a fidelidade de quantificador e tom depende do modelo e precisa de verificador novo em EN; EN lido como "traduzido" (decalque) se o prompt for fraco; guia e verificador passam a ser código a manter.

### B. Geração nativa bilíngue no mesmo prompt

Cada estágio devolve `{pt, en}`.
- Custo marginal por filme (saída extra do EN em todas as amostras do best-of): síntese ~1.000 tokens de saída, narrativa 3,3 amostras × ~330, veredito 3 × ~60, condições 3 × ~220, mais ~600 tokens de instrução EN em ~13 chamadas = ~2.930 tokens de saída e ~7.800 de entrada. Em DeepSeek: US$ 0,0029 fora de pico, US$ 0,0059 pico (US$ 0,37 e 0,75 para 128). Nos estágios que hoje rodam em Gemini 3.7 Flash (US$ 0,75 entrada, 3,75 saída por M): US$ 0,017 por filme, US$ 2,16 para 128, e o raciocínio oculto pode multiplicar: o piloto mediu 10.173 tokens de raciocínio por filme na narrativa (`ABERTO.md`, custo real US$ 0,0518 contra 0,0136 visível).
- Prós: EN idiomático, sem "cheiro de tradução"; um só passe.
- Contras: dobra a superfície de cada guarda (todas da seção 2 precisam de gêmeo EN antes de rodar); o best-of passa a escolher entre pares, e a chave de seleção fica ambígua (PT limpo com EN sujo); invalida a calibração e a leitura humana dos 128 PT (muda prompt = muda saída PT); mistura risco de regressão do PT, que é o ativo validado; nada do EN atual serve de gabarito direto.

### C. Geração EN separada a partir das classificações

Reexecuta o pipeline em EN (síntese, narrativa, veredito, condições) sobre bruto e consenso existentes.
- Custo: o pipeline custou ~US$ 0,10 por filme medido (classificação + verificador + síntese + rotulagem + narrativa, sem veredito; `ABERTO.md`); só os estágios que mudam de idioma (síntese, narrativa, veredito, condições) não incluem classificação, estimo US$ 0,05 a 0,08 por filme, ou US$ 6 a 10 para 128, com os mesmos riscos de raciocínio oculto do Gemini. Estimativa grosseira, a medir; não há gasto medido de veredito/condições.
- Prós: texto nativo, sem decalque; cada língua tem pipeline próprio.
- Contras: PT e EN divergem em conteúdo (temas, ordem, quantificador, quais condições passam), o que quebra a premissa de produto de mesmo conteúdo nos dois idiomas; reimplementar toda a bateria de guardas em EN (a lista da seção 2 inteira) e recalibrar; best-of, retries e condições recusadas (R1…R13) ocorrem independentemente por língua, então um tema pode sair publicado em um idioma e retido no outro; custo e tempo maiores; sem gabarito.

### Recomendação: A

Justificativa:
1. Fidelidade ao PT validado: o PT passou por guardas mecânicas e leitura humana de 100% (`SPEC` §0). A é a única opção em que o EN herda isso por construção; B e C exigem reprovar tudo de novo.
2. Custo: ~US$ 0,16 a 0,55 para 128 filmes, uma ordem de grandeza abaixo de B em Gemini e dois abaixo de C. A decisão não é de custo; é de risco.
3. Reuso: formato, front, build, extrator e testes ficam; o `_GUIA` vira prompt; as 5.693 traduções manuais atuais viram baseline e conjunto de few-shot.
4. Neutralidade é trabalhada uma vez, no verificador de tradução (quantificador 1:1, mesmas flags de polaridade), em vez de duas vezes em guardas lexicais EN.
5. Reversível: se a medição reprovar, o fluxo manual atual continua intacto.

Ressalva honesta: A traduz; se o dono quiser EN com voz própria (não decalcado), B ou C seriam o caminho e a conta seria outra. Só vale discutir isso depois de ler a saída de A contra o baseline.

## 4. Como validar antes de adotar

Nada de limiar sem rótulo manual prévio. Ordem:

0. Medir a base: tokens reais por filme (contar com o tokenizador do modelo, ou o campo `uso` de 3 chamadas), taxa de cache do prefixo, preço lido de novo em `preco.py`.
1. Amostra: 12 filmes estratificados (grupos de síntese; com e sem condição retida; amostra pequena; um com `prefixo_de_codigo` se existir; um com título não inglês), ~520 strings, mais as 146 do vocabulário. Rodar A em modo seco, sem gravar em `dados/traducao_en/` (saída em diretório de scratch).
2. Rótulo manual do dono (cego ao baseline) sobre cada string: ok / erro leve (estilo) / erro grave (sentido, quantificador, número, spoiler novo, tom assimétrico). Dois rótulos cegos de modelo e baseline para a mesma string, ordem aleatória.
3. Verificadores automáticos (código, offline), medidos contra o rótulo manual:
   - número, `%`, `~`, quebras de linha, placeholders idênticos ao PT (já em `test_traducao_en.py`);
   - forma das condições: minúscula, sem ponto, sem you/if/who, começa por verbo na forma base, completa a abertura;
   - quantificadores: mapa PT→EN da `_GUIA` §6 aplicado como regra, extraindo os quantificadores do PT e exigindo o EN canônico correspondente, sem palavra de outra faixa (`some`↔`a few`/`a handful`, `most`↔`nearly all`, `middling`≠`mixed`);
   - ratings vs reviews preservados; "notas" = ratings, "reviews" = reviews;
   - dígitos, aspas, sem score/"out of 10";
   - nomes próprios e títulos preservados (conjunto de tokens capitalizados do EN ⊂ do PT mais lista de títulos);
   - razão de comprimento EN/PT (a `_GUIA` pede parecido; baseline atual: 673 mil/680 mil chars, razão ~0,99).
4. Matriz de acerto, por verificador e agregada: linhas = rótulo manual (grave / não grave), colunas = verificador (reprova / aprova); relatar verdadeiros e falsos positivos e negativos, e o recall sobre erros graves. Mesma matriz para o baseline manual atual aplicado aos mesmos verificadores (o baseline também erra; a medida é relativa).
5. Comparação com o baseline: para cada string, concordância com a tradução atual (idêntica / equivalente a juízo humano / diferente). Divergência não é erro: o baseline foi feito por agentes, sem gabarito humano.
6. Critério de aceite proposto, a ser fechado pelo dono antes de rodar: (a) zero erro grave de quantificador, número, spoiler novo ou assimetria de tom na amostra; (b) taxa de erro grave não maior que a do baseline manual no mesmo rótulo; (c) verificador com recall de erro grave a definir pelo dono (sem limiar escolhido aqui); (d) custo medido dentro de 2× da estimativa. Se (a) ou (b) falhar, o resultado é "A não substitui o fluxo manual" e isso é a entrega; o passo seguinte seria A só como pré-tradução revisada por humano.

## 5. Plano de migração (passos pequenos)

Cada passo é independente e reversível; o front e o formato `dados/traducao_en/<slug>.json` não mudam.

1. Medição (seção 4, passos 0 a 5), sem tocar em `src/`. Script de estudo em `scripts/` no padrão de `gerar_condicoes.py`: recusa gravar em `dados/traducao_en/`. Arquivos: `scripts/medir_traducao_en.py` (novo), `resultado/` de estudo.
2. Extrair as guardas de sanidade de `tests/test_traducao_en.py` (números, forma da condição, tema sem ponto) para `src/espectro24/guardas_en.py` e fazer os testes importarem de lá, sem mudar comportamento. Acrescentar o verificador de quantificadores (mapa da `_GUIA` §6 como dado versionado em `dados/traducao_en/quantificadores.json`, sha registrado como `palavras_quantidade.txt`).
3. Módulo `src/espectro24/traducao_en.py`: monta o prompt, chama `synthesize.resposta` (nunca provider direto; é o guard-rail de §3[D]), valida com `guardas_en`, retenta só as strings reprovadas (uma vez), devolve `{pt: en}` + uso. Estágio novo `traducao_en` em `config.MODELO_POR_ESTAGIO` e `PROVIDER_POR_ESTAGIO`; `thinking` desligado; temperatura baixa; saída por id, não ecoando o PT.
4. `scripts/i18n_traduzir_en.py`: lê os `null` de `dados/traducao_en/` (que o extrator já cria), traduz, grava com `scripts/i18n_extrair_en.mesclar` para preservar o que já está preenchido e nunca sobrescrever tradução existente sem `--refazer`. Registra `proveniencia_en` no arquivo (modelo, sha256 do `_GUIA`, versão do verificador, `ts` UTC, uso para `preco.custo_de_registros`). `--dry-run` por padrão; `--teto-usd` com `preco.aviso_de_validade()` impresso.
5. Prompt vindo do `_GUIA.md`: marcar no guia as seções que entram no prompt (§3, §4, §6) com delimitadores, e o módulo as carrega em tempo de execução; as demais (§1, §2, §5) ficam só para humano. O guia continua a única fonte das regras; mudar uma regra muda o sha na proveniência e acusa traduções feitas com guia antigo.
6. Strings montadas por código: templates EN para `prefixo_de_codigo` e rótulos de peso (`briefing.rotulos_peso`), ligados a uma função `rotulo_en(...)` em `src/espectro24/`, testada contra a tabela §6 do guia. Só necessário quando surgir uma string dessas no resultado publicado (hoje o extrator vê os rótulos de peso dentro da narrativa; são traduzidos como parte do parágrafo).
7. Gancho no fluxo de publicação: depois de `scripts/publicar_condicoes.py` e antes de `frontend/build_data.py`, rodar extrator, `i18n_traduzir_en.py`, build. Adicionar o passo ao `docs/PUBLICACAO_C22_COMANDOS.md`. Filme regenerado: o `sha` muda, o extrator marca `null` nas strings novas, só elas são traduzidas.
8. Testes novos: `tests/test_traducao_en_pipeline.py` com `gerar` injetado (padrão de `narrador.narrar`), sem rede, cobrindo: não sobrescreve existente; só chama para `null`; retenta só reprovadas; falha isolada por filme; proveniência gravada; `pytest.fail` envenenando provider real; verificador de quantificador com casos de §6 (pares aprovados e reprovados); `test_traducao_en.py` continua passando. Teto de custo com preço de `preco.py`.
9. Gate de adoção: só depois do aceite da seção 4, rodar nos 128 e o dono ler uma amostra de 100% das condições (a regra do PT: coluna vazia e condição publicada passam por pessoa).

## 6. Pontos abertos

- Limiares de aceite (seção 4, 6c) e tamanho da amostra: decisão do dono, após o rótulo.
- Tokens reais por filme e taxa de cache: premissa até o passo 0. O preço do DeepSeek em `preco.py` está vencido (lido em 2026-09-18).
- Qual provider: DeepSeek (preço de pico/fora de pico; recusas determinísticas `400 Content Exists Risk` já ocorreram em um filme, exigem fallback), Featherless ou Gemini 3.7 Flash (preço dobra em 2027-01-01; raciocínio oculto cobrado como saída, medido 10.173 tokens por filme na narrativa; se usado, fixar `thinking` em zero e medir). Escolha só depois da medição.
- Granularidade: uma chamada por filme (contexto entre strings, melhor consistência de vocabulário) vs. por bloco (falha menor). Medir consistência de quantificador entre blocos.
- Vocabulário compartilhado: traduzir uma vez e injetar como glossário no prompt, para os temas repetidos saírem iguais entre filmes.
- Temas e exemplos legados: parte dos exemplos publicados ainda traz quantificador ("Muitas reviews descrevem…"), de antes da `guarda_quantidade`; a tradução precisa preservar a força, não "corrigir" para o EN.
- Chave por string PT: um ajuste de pontuação no PT invalida a tradução. Um id estável por campo (`tema_origem`, índice de parágrafo) evitaria, mas muda o formato e o front; deixado fora desta proposta.
- Simetria de tom em EN não tem validador lexical hoje; a proposta depende de verificar quantificador/polaridade 1:1 e de rótulo humano. Avaliar um verificador de pares (mesma condição de PT, mesmos marcadores de força nos dois lados).
- Se o dono quiser EN nativo (B ou C) no futuro: precisaria de gêmeos EN de toda a seção 2 e de nova leitura humana; só faz sentido com evidência de que A traduz mal.
- Títulos (`titulo_en`) dos 33 filmes sem identidade: fora desta proposta, dependem de fonte externa e não de LLM de síntese.
