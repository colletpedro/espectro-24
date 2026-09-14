# ETAPA 0 — proposta do piloto de 20 filmes

**Estado: aguardando decisão do dono. Nada foi coletado.**
Documento de estudo, untracked (política de `ESTUDO_MARGEM_20PP.md`).

O que já foi gasto: **67 requisições** de sondagem (busca de slug, página do
filme, histograma) — nenhuma escrita em `dados/bruto/`, nenhuma chamada de LLM.
Baseline da suíte: **1822 testes** (`pytest --collect-only -q`).

---

## 1. Correção de premissa: a guarda não tem os motivos que o briefing supõe

O briefing pede o motivo de cada omissão entre "sem candidato / múltiplos
candidatos / divergência de ano / falha de duração". Lendo
`src/espectro24/ficha.py:1087` (`buscar_ficha`) e `src/espectro24/cli.py:250`,
o caminho de PRODUÇÃO (com `identidade`) tem outro conjunto:

| motivo publicado | quando |
|---|---|
| `identidade_letterboxd_indisponivel` | a página do LB não deu `production:name` + `data-tmdb-id` |
| `ano_desconhecido` | identidade ok, mas nenhuma fonte de ano |
| `tmdb_id_letterboxd_ausente` | identidade sem ID utilizável |
| `override_manual_desatualizado` | override existe e o mundo mudou (hoje o mapa está vazio) |
| `titulo_divergente` | nenhum título TMDB bate por igualdade normalizada |
| `duracao_incompativel_com_longa` | `runtime < 40 min` |
| `tmdb_indisponivel` | rede/HTTP/chave |

Duas diferenças que mudam o que o piloto pode medir:

- **"múltiplos candidatos" não existe.** Em produção o ID vem do
  `data-tmdb-id` da própria página do Letterboxd; não há busca, logo não há
  desambiguação. `_resolver_id` (busca + popularidade) só roda no caminho
  legado, sem `identidade`.
- **Divergência de ano NÃO omite ficha em produção.** O descarte por ano
  (`ficha.py:1200`) está guardado por `identidade is None`. Com identidade, a
  divergência vira `ano_divergente: true` na evidência e o **ano do Letterboxd
  prevalece** no valor publicado. Dois dos 35 filmes atuais estão nesse estado
  (`obsession-2025`, `talk-to-me-2022`).

**Consequência para o piloto:** os únicos eixos que ele pode estressar de
verdade são *igualdade de título* e *piso de duração*.

## 2. Correção de baseline: a guarda foi exercida sobre 2 filmes, não 35

O briefing diz "os 35 atuais (29 aprovando por `original_title`)". Medido nos
artefatos publicados (`resultado/*.json` e `frontend/data/*.json`):

| | n |
|---|---|
| filmes publicados com ficha | 35 |
| fichas que carregam `ficha.identidade` (evidência do contrato v1.9.49) | **2** |
| aprovadas por `original_title` | 2 (`obsession-2025`, `talk-to-me-2022`) |
| aprovadas por `title` ou `alternative_title` | 0 |
| com `ano_divergente: true` | 2 |

As outras 33 fichas foram geradas ANTES da v1.9.49 e nunca voltaram a passar
pela guarda. `_entrada_completa` (`ficha.py:546`) as trata como MISS na próxima
execução — mas essa execução não aconteceu. O `ABERTO.md` C2 está correto ao
dizer "as 35 entradas antigas viram miss"; o que não aconteceu foi o *re-run*.

Isso reforça o piloto: a taxa de aprovação da guarda hoje é medida sobre n=2.

## 3. Os 20 filmes

Nenhum colide com os 36 diretórios de `dados/bruto/`. Todos verificados ao vivo:
slug real (via a busca do próprio produto), `production:name`, ano e
`data-tmdb-id` extraídos da página. **Nenhuma consulta ao TMDB foi feita** — é
exatamente a prova que o piloto existe para medir, e pré-consultá-la
selecionaria a lista para passar.

| # | slug | título LB | ano | tmdb_id | notas | neg/med/pos % | por que está na lista |
|---|---|---|---|---|---|---|---|
| 1 | `memories-of-murder` | Memories of Murder | 2003 | 11423 | 1.098.638 | 1/5/94 | KR. `original_title` coreano, pt-BR "Memórias de um Assassino": só passa por `alternative_titles` |
| 2 | `the-wailing` | The Wailing | 2016 | 293670 | 327.019 | 4/13/83 | KR. pt-BR "O Lamento" — mesmo padrão |
| 3 | `burning-2018` | Burning | 2018 | 491584 | 334.962 | 4/13/82 | KR. pt-BR "Em Chamas" |
| 4 | `drive-my-car` | Drive My Car | 2021 | 758866 | 395.980 | 3/10/87 | JP. pt-BR provavelmente idêntico ao LB — controle DENTRO do grupo não-latino |
| 5 | `happy-hour-2015-1` | Happy Hour | 2015 | 354759 | 14.888 | 2/7/91 | JP, 317 min, pouco visto. Slug com sufixo `-1` (desambiguação do próprio LB) |
| 6 | `a-brighter-summer-day` | A Brighter Summer Day | 1991 | 15804 | 81.998 | 2/6/92 | TW. Título internacional longo, sem relação com o original |
| 7 | `the-cloud-capped-star` | The Cloud-Capped Star | 1960 | 59239 | **7.921** | 3/10/87 | IN, bengali. Único abaixo do limiar de 10.000 que o código chama de `obscuro`. Hífen no título testa a normalização |
| 8 | `woman-of-fire` | Woman of Fire | 1971 | 108175 | **1.145** | 5/29/66 | KR. O caso extremo: quase certamente NÃO fecha 40/40/40 e pode produzir bucket com n<10 |
| 9 | `neighboring-sounds` | Neighboring Sounds | 2012 | 97989 | 38.214 | 5/18/77 | BR. LB usa o título em INGLÊS; TMDB tem "O Som ao Redor" em `original_title` E em pt-BR. Nenhum dos dois bate |
| 10 | `the-second-mother` | The Second Mother | 2015 | 310569 | 149.576 | 1/5/93 | BR. Mesmo padrão ("Que Horas Ela Volta?") |
| 11 | `force-majeure-2014` | Force Majeure | 2014 | 265189 | 138.906 | 4/17/80 | SE. `original_title` "Turist", pt-BR "Força Maior" — LB não bate nenhum dos dois |
| 12 | `zama` | Zama | 2017 | 326382 | 25.021 | 9/25/66 | AR. Título idêntico nos três campos — controle da coluna latina |
| 13 | `satantango` | Satantango | 1994 | 31414 | 45.536 | 5/7/88 | HU. "Sátántangó" com diacríticos: testa `normalizar_titulo_identidade` |
| 14 | `the-turin-horse` | The Turin Horse | 2011 | 81401 | 47.834 | 5/10/85 | HU. "A torinói ló" |
| 15 | `hard-to-be-a-god` | Hard to Be a God | 2013 | 110402 | 18.101 | 11/16/73 | RU, cirílico. Obscuro e com negativas relevantes |
| 16 | `guillermo-del-toros-pinocchio` | Guillermo del Toro's Pinocchio | 2022 | 555604 | 714.140 | 3/12/85 | Homônimo do mesmo ano (par com o #17). Apóstrofo testa a normalização |
| 17 | `pinocchio-2022` | Pinocchio | 2022 | 532639 | 110.315 | **60/25/15** | O outro Pinocchio de 2022 (Zemeckis). Também é o único de distribuição invertida da lista |
| 18 | `speak-no-evil-2022` | Speak No Evil | 2022 | 833339 | 247.174 | 11/28/61 | DK, "Gæsterne". Homônimo EXATO do remake de 2024 (`speak-no-evil-2024`, tmdb 1114513) |
| 19 | `whiplash-2014` | Whiplash | 2014 | 244786 | 4.774.893 | 1/6/93 | Controle conhecido |
| 20 | `get-out-2017` | Get Out | 2017 | 419430 | 4.739.915 | 2/11/87 | Controle conhecido |

**Composição:** 8 de script não-latino · 4 com título LB divergente do
`original_title` latino · 3 europeus obscuros/diacríticos · 2 homônimos do
mesmo ano · 1 homônimo exato entre anos · 2 controles.
Dois (`woman-of-fire`, `the-cloud-capped-star`) foram escolhidos para
FALHAR o piso de amostra, não a guarda.

### O que esta lista já revela antes de coletar

**Os 20/20 têm `data-tmdb-id` na página do Letterboxd.** Isso é uma das
medições pedidas, e ela já está fechada: nenhuma omissão do piloto virá por
`identidade_letterboxd_indisponivel` ou `tmdb_id_letterboxd_ausente`. Todos os
20 também expõem o ano, então `ano_desconhecido` também está descartado.

Também não espero omissão por duração: o piso é 40 min e todos os 20 são
longas (nenhum é curta; não verifiquei as durações no TMDB de propósito — é a segunda prova da guarda). O
piso só dispararia se um `data-tmdb-id` do LB apontasse para um curta — o
defeito exato do `obsession-2026`, que é justamente o que ele existe para pegar.

**Ou seja: a omissão de ficha neste piloto será decidida quase inteiramente
por `titulo_divergente`.** É o eixo certo para estressar — é o único nunca
exercitado (0 de 35 aprovaram por `title` ou `alternative_title`) — mas o dono
deve saber que o número que sair do gate mede UMA coisa, não quatro.

## 4. Backup de `dados/bruto/`

### O que o `ABERTO.md` C7 não diz

`dados/bruto/` **já é versionado e já está no GitHub**. 72 arquivos rastreados,
árvore limpa, `main` sem commits à frente de `origin/main`. O superset dos 35
filmes existe hoje em três lugares (árvore, `.git` local, `origin`). "Não existe
política" é verdade como política escrita; o artefato não está desprotegido.

O que **não** tem cópia em lugar nenhum:

| artefato | tamanho | versionado |
|---|---|---|
| `resultado/cache/` (HTML bruto do Letterboxd) | **309 MB**, 4.763 arquivos | **não** (gitignored) |
| `dados/cache/` (cache TMDB) | 44 MB | **não** |
| `dados/lote/estado.json` | 12 KB | **não** |
| `dados/bruto/` | 14 MB | sim |
| `resultado/votacao-3/` | 37 MB | sim (23 arquivos) |
| `resultado/*.json` | — | sim (139) |

O `resultado/cache/` é o artefato realmente frágil: é ele que torna a
re-coleta gratuita, e é o único grande sem cópia. **O volume está com 6,4 GiB
livres de 228 GiB (97% cheio)** — a 8,6 MB de cache por filme, os 300 projetam
~2,6 GB, o que cabe, mas não com folga confortável.

### Estratégia proposta — três camadas

**Camada 1 — snapshot imutável, antes de qualquer escrita.**
`cp -a` de `dados/bruto/`, `dados/lote/`, `resultado/votacao-3/`,
`resultado/*.json` e `frontend/data/` para `~/backups-espectro-24/<UTC>/`
(fora da árvore, para não sujar o `git status`; carimbado, para nunca colidir
com um snapshot anterior), mais um manifesto `sha256` por arquivo.
Custo: ~55 MB e alguns segundos. **Precisa da autorização do dono para
escrever em `~/`** — se preferir outro destino, é um parâmetro.

**Camada 2 — verificação por hash depois.**
O manifesto é reconferido ao final. Qualquer arquivo dos 35 filmes existentes
com sha256 diferente é um bug, não um efeito colateral tolerável. É isso que
transforma "não sobrescrever" de intenção em asserção verificável.

**Camada 3 — isolamento da escrita nova.**
`lote.py` aceita `--dados-dir`, então há duas opções:

- **(A) coletar direto em `dados/bruto/`.** Slug novo é diretório novo;
  `persistir()` nunca toca os 35. É o que todo o pipeline a jusante espera —
  `classificar_10.montar_amostra()` varre `dados/bruto` com o caminho
  HARDCODED, e o mesmo vale para os scripts de publicação.
- **(B) coletar em `dados/bruto-piloto/` e mesclar depois do gate.**
  Isolamento perfeito da coleta, mas as etapas de classificação e de produto
  não rodariam sem editar código ou copiar os diretórios à mão — risco novo
  para proteger contra um risco que as camadas 1 e 2 já cobrem.

**Recomendação: (A)**, com um checkpoint de lote SEPARADO
(`dados/lote/estado-piloto.json`), para não tocar o checkpoint dos 29.

Fora do snapshot, com o custo declarado: `resultado/cache/` (309 MB). Se o
dono quiser cobri-lo, são +309 MB de um volume que tem 6,4 GiB livres.

## 5. Retomada — confirmada, com uma lacuna

**Coleta — retomável.** `lote.rodar_lote` chama `estado.salvar()` depois de
CADA filme, e slug `concluido` é pulado sem gastar requisição. Cair no filme
137 e reexecutar continua do 137. `AntiBotError` e `SobrecargaError` param o
lote inteiro, mas gravam o estado antes de propagar.

**Classificação — retomável.** `votacao_3.py passe N` é append-only: reconstrói
`feitos` a partir do JSONL e pula cada `(slug, bucket, id)` já classificado.
Recusa rodar se o `taxonomia_id` mudou.

**A amostra não é reamostrada.** `montar_amostra()` percorre filme a filme e
"nada é sorteado" — acrescentar 20 filmes não muda a seleção dos 35. Os 9.497
registros de cada passe continuam válidos; só as reviews novas custam LLM.
*Mas* `votacao_3.py amostra` **sobrescreve** `resultado/votacao-3/amostra.json`,
que é versionado — está coberto pela camada 1.

**A lacuna:** síntese, eixos, narrativa, veredito e condições rodam por filme
pelo CLI, e não existe harness com checkpoint para eles. A retomada é "pular os
slugs que já têm `resultado/<slug>.json`", que eu implementaria no laço. Isso é
retomada com granularidade de FILME: cair no meio da narrativa de um filme
repete aquele filme inteiro (~9 chamadas Gemini). Aceitável no custo, mas é
uma lacuna real e não quero que apareça como surpresa.

## 6. Baseline do produto (35 filmes) — para comparar depois

| medição | valor |
|---|---|
| filmes publicados | 35 |
| `contraste: valorativo` | **28 (80,0%)** |
| `contraste: tematico` | 7 (20,0%) |
| filmes com algum bucket n<10 | **0** |
| menor bucket do catálogo | 27 (`pearl-2022`, negativas) |
| filmes que NÃO fecham 40/40/40 | 5 (`pearl-2022`, `talk-to-me-2022`, `the-godfather`, `wicked-2024`, `wonka`) |
| reviews analisadas por filme | mín 106 · mediana 120 · máx 120 |
| testes coletados | 1822 |

A proporção de `valorativo` **já é 80%**. Se o briefing esperava que ela
subisse com filmes obscuros, o espaço para subir é de 20 pontos; e o piloto
pode perfeitamente não mover nada. Registro isso antes de medir para que o
resultado não seja lido como confirmação do que já se esperava.

## 7. Projeções

### Scraping

Medido ao vivo agora: **2,51 s por requisição** (8 requisições frescas;
`DELAY_SECONDS` = 2,0 + latência). Do checkpoint dos 29 filmes:
**mediana 76, média 77,7 requisições por filme**.

| | requisições | tempo |
|---|---|---|
| 20 filmes | ~1.554 | **~65 min** |
| 300 filmes | ~23.300 | **~16,3 h** |

Filmes obscuros podem cair para os dois lados: menos material para paginar
(menos requisições) ou orçamento de extensão gasto tentando fechar buckets que
não fecham (mais). O piloto mede isso; a projeção acima usa o perfil dos 29.

### Custo de LLM

Classificação (3 passes DeepSeek), medido sobre os 28.491 registros dos
`passe_*.jsonl` com os preços do próprio repositório
(`classificar_10.py:128`):

| | por filme | 20 filmes | 300 filmes |
|---|---|---|---|
| mediana | US$ 0,0227 | ~US$ 0,45 | **~US$ 6,80** |
| mínimo observado | US$ 0,0027 | | |
| máximo observado | US$ 0,0288 | | |

Gemini (narrativa + veredito + condições, 3 candidatos cada), tokens medidos
nos 35 `resultado/*.json`: **mediana 23.461 de entrada e 2.622 de saída por
filme**. O repositório **não registra preço de Gemini em lugar nenhum**, então
não vou inventar um: a US$ 0,30/M entrada e US$ 2,50/M saída — *premissa
minha, não um número do projeto* — isso dá ~US$ 0,014/filme, ~US$ 4,20 para 300.

**Uma medição que não existe:** `synthesize_bucket` (3 chamadas DeepSeek por
filme, os `temas` e a `observacao_geral` de cada bucket) não grava telemetria
de uso em lugar nenhum. Estimo ~US$ 0,007/filme pelo tamanho do prompt, mas é
estimativa. Meço no piloto.

**Total projetado para os 300: ordem de US$ 15, não de centenas.** O gargalo é
inteiramente o scraping.

## 8. Gate

Corte declarado: **omissão de ficha acima de ~20% (5 de 20) → parar e reportar.**

Dado que os 20/20 têm `data-tmdb-id`, ano e duração de longa, o gate mede
essencialmente `titulo_divergente`. Se ele disparar, a decisão de produto que
chega ao dono é: *o Letterboxd nomeia obras internacionais por um título que o
TMDB não lista entre os seus* — e as saídas seriam ampliar o conjunto de
títulos aceitos (ex.: `translations`), aceitar a ficha sem prova de título
quando o ID vem do LB, ou publicar sem ficha. Nenhuma delas é minha para tomar.

## 9. O que peço antes de coletar

1. **Destino do snapshot** — `~/backups-espectro-24/<UTC>/` serve?
2. **Camada 3: (A) ou (B)?** Recomendo (A).
3. **`resultado/cache/` entra no snapshot?** +309 MB de 6,4 GiB livres.
4. **A lista de 20 está aprovada?** Trocas são baratas agora e caras depois.

## 10. Três achados fora do escopo, registrados sem agir

- **`_ARTHOUSE` é um conjunto fixo do catálogo atual** (`classificar_10.py:190`).
  Nenhum dos 20 novos será rotulado `arthouse`; `drive-my-car`,
  `a-brighter-summer-day` e `satantango` cairiam em `aclamado`. O `perfil`
  alimenta `metricas_lift` e o relatório. Não é bloqueio; é distorção que
  cresce com o catálogo.
- **`ABERTO.md` D1** manda rodar o nulo do máximo sobre os filmes NOVOS e
  recalibrar a constante da lei de margem — este piloto é o primeiro material
  out-of-sample que existe para isso. É computação local, sem custo de rede ou
  de LLM. Não fiz: não foi pedido.
- **`ABERTO.md` E2 x `home.js`** — o `ABERTO.md` registra a busca da home como
  "pendência sem decisão", enquanto `frontend/js/home.js:4` afirma que ela
  "deixou de ser decorativa" na v1.9.14 e busca título + eixos em destaque. O
  mosaico também não é 7×5 fixo: é
  `repeat(auto-fill, minmax(132px, 1fr))` — 7 colunas é consequência da
  largura, não do código. Meço os dois com 55 filmes depois da coleta, como
  pedido, sem implementar nada.

---

## Adendo — 2026-09-10 (reconferência antes de coletar)

**Estado: continua aguardando decisão. Nada foi coletado, nenhuma requisição
nova, nenhuma chamada de LLM.** Reconferido contra o HEAD `0a777c3` (v1.9.50,
8/set — anterior a esta proposta, então a base não mudou).

### Reconfirmado

- Baseline da suíte: **1822** (`pytest --collect-only -q`, medido de novo).
- Os 20 slugs: zero colisão com `dados/bruto/`, `resultado/*.json`,
  `consenso.jsonl`, `amostra.json`, `dados/lote/estado.json` e
  `frontend/data/`. Os 20 têm `production:name` + ano + `data-tmdb-id`
  extraíveis da página já em `resultado/cache/` (checado OFFLINE com
  `extrair_identidade_letterboxd`, zero rede).
- `dados/bruto/`: 72 arquivos, todos rastreados, idênticos a `origin/main`.

### Mudou desde a proposta

- **Disco: 3,2 GiB livres (99%)**, contra 6,4 GiB ontem. Para o piloto é
  irrelevante (~170 MB de cache). **Para os 300 é bloqueio**: ~2,6 GB de cache
  projetado deixaria ~0,6 GB livres. Snapshot de `resultado/cache/` (309 MB)
  passa a custar 10% do espaço livre — recomendo NÃO incluir.

### Correções à proposta

1. **§5 "A lacuna" está errada: o harness de publicação já existe.**
   `scripts/publicar_catalogo.py` roda cada filme como subprocesso do CLI
   (falha isolada, `TIMEOUT_S = 300`) e o checkpoint é o filesystem
   (`_ja_publicado`: `spec_version == 1.9.50` E `eixos.verificador.aplicado`).
   Retomada por filme já existe; não há laço novo a escrever.
   **Mas tem uma armadilha:** `LIMITE_LOTE_SEM_CONFIRMACAO = 5`. Com 20
   `--slug`, ele exige `--republicar-tudo` — e essa flag sem `--slug` publica a
   lista default (os 32 do catálogo), refazendo a coleta e apagando `passadas`.
   **Proposta: publicar em 4 lotes de 5 `--slug` cada, sem nunca passar a flag.**
2. **Ordem obrigatória, não citada:** quando `consenso.jsonl` cresce,
   `pipeline._carregar_consenso_producao` levanta `ValueError` (verificado
   desatualizado) para QUALQUER filme até rodar `verificador_impacto.py
   aplicar-producao`. A sequência é: `lote.py` → `estender_classificacao_producao.py`
   (3 passes + consenso) → `verificador_impacto.py aplicar-producao` →
   `publicar_catalogo.py` (4×5) → `build_data.py`. Os três estágios de LLM são
   retomáveis por id (`classificar_passe` e `rodar_passe` reconstroem `feitos`
   do JSONL).
3. **§3 superestima a dificuldade de título para os BR/SE.** `buscar_ficha`
   compara contra a resposta pt-BR (`original_title`, `title`,
   `alternative_titles`) e, se nada bater, contra a en-US (`original_title`,
   `title` — **sem** `alternative_titles`, porque essa chamada usa
   `com_imagens=False`). "Neighboring Sounds"/"The Second Mother"/"Force
   Majeure" provavelmente passam pelo `title` en-US. O piloto pode estressar
   menos do que a lista sugere; isso é resultado, não defeito da lista.
4. **Lacuna de medição na evidência:** `titulo_tmdb_campo = "title"` não diz se
   bateu o `title` pt-BR ou o en-US. Resolvo depois, sem mexer em código,
   comparando `titulo_tmdb_correspondente` com `ficha.titulo` (que é o pt-BR).
5. **Efeito colateral a declarar:** o catálogo da home é o conjunto de slugs de
   `consenso.jsonl` (`build_data._catalogo`). Rodar `build_data.py` para medir
   a home com 55 reescreve `frontend/js/data.js` (rastreado, é o que o Vercel
   serve). Proposta: medir e depois restaurar `data.js` e remover os 20
   `frontend/data/*.json` novos, para que um commit acidental não publique 55.
6. **Risco pequeno, a medir:** a amostra classificada sai de
   `amostra_do_bruto(slug, coleta=None)`, que cai no `meta.json` do bruto
   (mesmo histograma e orçamento que o CLI usa) — coincide com a analisada
   SE a execução do CLI não trouxer material novo. Mede-se pela
   `sobreposicao_com_analisadas` de `eixos.fonte_classificacao`.
7. `EstadoLote.salvar()` e `persistir()` usam `write_text` (não atômico). Kill
   no meio da escrita do checkpoint derruba a próxima execução com erro de
   JSON (ruidoso, não silencioso); no `reviews.jsonl`, a recoleta do mesmo
   filme (100% cache) regrava o arquivo. Não bloqueia; registrado.

---

## Execução — 2026-09-10 — PARADA antes da publicação

**Parado pela regra do dono** ("se QUALQUER dado dos 35 mudar, parar e
reportar, não corrigir"). Nada publicado; `frontend/js/data.js` e os 36
`resultado/*.json` batem com o snapshot por hash.

Snapshot: `~/backups-espectro-24/20260910T181842Z/` (169 arquivos, 56 MB,
`MANIFESTO.sha256`, cópia conferida).

### O que disparou a parada

`consenso_verificado.jsonl`: **1 linha dos 35 mudou** —
`spider-man-across-the-spider-verse` / positivas / `viewing:1439420676`,
`impacto_emocional` removido. Causa: `verificador_impacto.rodar_passe` retoma
todo id SEM registro `ok`; 8 reviews dos 35 tinham falhado na rodada original
(`n_falharam: 8` no manifesto antigo) e foram reverificadas agora — 7 sem
efeito, 1 com `confirma=False`. É o desenho da retomada, não corrupção; mas é
mudança em dado dos 35. Efeito sobre o bloco `eixos` publicado de spider-man:
nenhum até uma republicação; efeito sobre o contraste dele: não medido.

### Medições até a parada

- **Coleta:** 20/20, 0 falhas, 94,8 min. **284 s/filme** (mediana 256,
  177–457), 115,8 req/filme, 2,46 s/req. Obscuros pedem mais requisições
  (satantango 187, hard-to-be-a-god 174). **Projeção 300: ~23,7 h** (não 16 h).
- **Gate da ficha:** **20/20 publicariam, 0 omissões.** `tmdb_id` = `data-tmdb-id`
  nos 20; rótulo manual por diretor: 20/20 corretos (matriz 20 VP / 0 FP /
  0 FN; nenhum negativo na amostra, o caminho de recusa não foi exercido).
  Por campo: `original_title` 8 · `title` pt-BR 1 · `alternative_title` 3 ·
  **`title` en-US 8**. 12/20 falhariam só com `original_title`; os 8 do en-US
  dependem da 2ª chamada (sem `alternative_titles`). `ano_divergente`: 1
  (hard-to-be-a-god).
- **Piso:** `woman-of-fire` negativas **n=9** (`sem_quantificador`, <10 → sem
  contraste por lei); `the-cloud-capped-star` negativas n=27. 18/20 fecham 40/40/40.
- **Custo real (DeepSeek, preços do repo):** classificação US$ 0,309 +
  verificador US$ 0,117 = **US$ 0,426 para 20 (US$ 0,0213/filme)**. Gemini,
  síntese e rotulagem: não medidos (parada antes da publicação). Preço
  oficial Gemini 3.7 Flash: US$ 0,75/M entrada, 3,75/M saída até 31/12/2026;
  o dobro depois.

### Achados de pipeline

1. **`estender_classificacao_producao.py` não registra filme novo em
   `amostra["filmes"]`, e `cmd_consenso` filtra por esse campo** — o caminho
   oficial classifica (7068 chamadas pagas) e o consenso descarta tudo em
   silêncio. Contornado por passo de DADO (scratchpad
   `registrar_filmes.py`): as 20 entradas geradas por
   `classificar_10.montar_amostra()` em memória, só por apêndice; as 35
   entradas conferidas idênticas antes e depois.
2. **7 das 35 entradas de `amostra["filmes"]` estão defasadas** em
   `n_por_bucket` (bruto recoletado em 22/08, entradas de 10–16/08).
   Nenhum leitor de produção usa o campo (`eixos.py` lê só `taxonomia_id`).
3. **Filtro de conteúdo do DeepSeek:** 1 review (`a-brighter-summer-day`)
   recusada nos 3 passes com `400 Content Exists Risk` — determinístico.
   Verificador: 14 falhas persistentes (motivo não inspecionado).
4. **`synthesize.uso()` ignora `thoughts_token_count` do Gemini** — o `uso`
   gravado na narrativa/veredito/condições subestima a saída cobrada.
5. **Veredito e condições não saem do CLI.** `write_json` sobrescreve o
   JSON inteiro; veredito vem de `gerar_veredito.py`; condições exigem
   leitura humana de 100% (§0) antes de `publicar_condicoes.py`.

---

## Execução — 2026-09-13 — decisão (A) e publicação

Dono decidiu (A): aceitar a linha do verificador em spider-man. Registrado
em `ABERTO.md` (C3 atualizado; C14 com 10 bloqueantes da expansão).

- **Efeito em spider-man** (bloco recalculado; o cálculo sobre o snapshot
  reproduz o publicado): estado, margem e bullets inalterados; só
  `impacto_emocional`/positivas 17→16.
- **Falhas do verificador:** todas `JSONDecodeError`, não determinísticas
  (as 8 antigas passaram na retomada). Nos 12 filmes novos com falha, nenhum
  estado muda; em `speak-no-evil-2022` os bullets das medianas mudariam.
- **Publicação (4×5, sem `--republicar-tudo`): 18/20.** Falharam
  `a-brighter-summer-day` (DeepSeek `Content Exists Risk` na síntese) e
  `woman-of-fire` (`KeyError: 'contraste'` em `cli.py:348` com n=9).
  60,0 s/filme (49–70). `get-out-2017` saiu com margem n=39: o CLI recoletou
  (826→862) e uma review nova entrou sem classificação.
- **Contraste dos 18:** 4 `tematico` (force-majeure, zama, satantango,
  pinocchio-2022) · 14 `valorativo` (77,8%). Catálogo publicado: 42/53
  valorativo (79,2%; baseline 28/35 = 80,0%). Nenhum publicado com n<10 —
  o único (woman-of-fire) não publicou.
- **Custo real por filme** (instrumentado): classificação 0,0154 ·
  verificador 0,0058 · síntese 0,0037 · rotulagem 0,0003 · narrativa Gemini
  **0,0518** · condições Gemini 0,0250 → **~US$ 0,10/filme** sem veredito
  (não gerado). Gemini: ~10,2k tokens de raciocínio por narrativa contra
  ~1,4k visíveis — o `uso` gravado subestima 3,8×.
- **Condições (geradas fora de `resultado/`, não publicadas):** 138 itens
  nos 18 (66 + 72), 7,7/filme, 3 descartadas pelo validador, 2 de
  `expectativa`. Para 300: ~2.300 itens para leitura humana.
- **Home com 53:** desktop 1280 → 7 colunas × 8 linhas, 2,58 telas; mobile
  375 → 3 × 18, 4,5 telas, sem overflow. Busca: "memories of murder" e
  "get out" devolvem 0 (título do LB não é indexado); "roteiro" 51/53.
- **`frontend/js/data.js` restaurado**, sha256 idêntico ao do snapshot; os 18
  `frontend/data/*.json` gerados foram removidos.
- **Suíte:** 1822 coletados = baseline; 1813 passam, 8 falham (todos passam
  no `HEAD` limpo — a causa é o dado do piloto; nenhuma asserção tocada).
- **Tempo total projetado para 300:** scraping 284 s + classificação ~51 s +
  verificador ~12 s + publicação 60 s + condições ~18 s ≈ **7 min/filme,
  ~35 h**.
