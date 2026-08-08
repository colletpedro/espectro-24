# Espectro 24 — Especificação v1.9.3

**Data:** 2026-08-07
**Status:** v1 fechada (aceite em "Status de aceite da v1", fim do documento). **v1.9.3 não muda a camada de coleta — constrói o harness de LOTE (§3[H]) sobre ela e roda a coleta de um conjunto maior de filmes.** Checkpoint em arquivo (resume sem refazer filme completo), validação de slug por 1 requisição antes de gastar orçamento de páginas, falha isolada por filme (um slug ruim nunca derruba o lote), e `material_esgotado` tratado explicitamente como caso esperado — os 3 filmes do catálogo, sendo populares, nunca tinham exercitado esse caminho em produção. Estimativa de custo medida ANTES do lote (§5.6), com veto explícito se a projeção para 50 filmes passar de ~4h. **v1.9.2 fechou o gate de profundidade que a v1.9.1 deixou em aberto e resolve o déficit residual de `medianas`.** É a última sessão de coleta antes do lote de 30-50 filmes, e o reenquadramento que a motiva é este: a profundidade de paginação é o ÚNICO parâmetro da camada de coleta que o superset NÃO torna reversível — página não baixada não está em disco, e coletar o lote sem resolver isso é aceitar recoleta total se a janela temporal se provar um problema. Quatro entregas: (a) a **parada por ALVO é removida** — era um vestígio de quando o teto era por nível e o custo por bucket não tinha limite; sob o orçamento por bucket da v1.9.1 ela só introduzia não-determinismo (foi a causa exata do 37/40 residual de `cidade-de-deus`), e o orçamento passa a ser sempre gasto integralmente, com única parada antecipada por esgotamento real de material — custo aceito e medido: ~32→48 páginas/filme; (b) **posicionamento estratificado por profundidade** substitui a paginação puramente consecutiva — uma reserva de 25% do orçamento de cada nível (`RESERVA_PROFUNDIDADE`) é posicionada em progressão geométrica a partir do fim do bloco raso, com descoberta de profundidade real e redistribuição do orçamento restante **reaproveitando `redistribuir_deficit`** — MESMO número de requisições que a paginação consecutiva, cobertura temporal muito maior; (c) o **teto de 256 páginas** suspeitado na v1.9.1 é medido num filme obscuro — resultado em §3[B]; (d) `pagina_origem` (rank de adição sob ordenação cronológica, sem a contaminação de `data`, que é a data ASSISTIDA) vira o **instrumento temporal PRIMÁRIO**; `janela_temporal` por `data` (v1.9.1) fica como secundária, rotulada como proxy contaminado. Nada de fronteira, cota, piso escalonado, `min_chars`, ordenação ou síntese é tocado. **v1.9.1 corrigiu dois defeitos que a telemetria MEDIDA da v1.9.0 revelou na camada de coleta**, sem tocar fronteira, cota, piso escalonado ou qualquer etapa de síntese/narrativa: (a) o **orçamento de páginas por BUCKET** (§3[B]) substitui o teto por NÍVEL, corrigindo o defeito estrutural registrado na v1.9.0 (o bucket `medianas`, com metade dos níveis dos outros dois, nunca conseguia o mesmo teto agregado de páginas — 8 contra 16 — e por isso nunca fechava a cota) — **medido: fecha 40/40 em 2 dos 3 filmes (era 35 e 26) e melhora para 37/40 no terceiro (era 23)**, um achado residual e distinto, com causa identificada, registrado em §3[B]; (b) os **motivos de descarte** na seleção passam a ser discriminados (`abaixo_min_chars`/`spoiler`/`truncada_sem_texto`/`duplicata`/`excedente_cota`/`outros`), telemetria pura, sem mudança de comportamento. Duas entregas adicionais: (c) a **janela temporal** (mín./máx./p5/p50/p95 das datas do bruto, por bucket e total) passa a ser gravada em `meta.json`, não exposta ao frontend; (d) o literal `50 · 20 · 30` remanescente em `frontend/js/filme.js` (pendência registrada na v1.9.0) passa a derivar do próprio JSON de resultado. Uma quinta questão — **paginação de passo largo**, candidata a resolver o viés de recência medido na v1.9.0 (79-100% da amostra em ~7 semanas) — foi **só MEDIDA nesta versão, não implementada**: o gate de decisão está em §3[B], "Medição de profundidade (v1.9.1, gate)", com um achado que contraria a expectativa registrada no briefing (o custo de descobrir a profundidade via sonda de rede NÃO é neutro — é uma sonda de ~10 requisições por nível — mas há evidência forte, ainda que de amostra pequena, de um TETO FIXO do site em 256 páginas que, se confirmado mais amplamente, eliminaria essa sonda por completo). **v1.9.0 reestruturou a camada de COLETA e desacoplou COLETA de ANÁLISE** — a maior mudança de arquitetura de dados desde a v1. Até a v1.8.2, a coleta usava cota fixa de 10 reviews por nível de estrela e gravava, no material coletado, as decisões de **fronteira de bucket**, **cota** e **filtro**: mudar qualquer uma delas custava recoletar tudo. A v1.9.0 (a) move as **fronteiras de bucket** para configuração lida de um único lugar, com o mapeamento nível→bucket como função pura (§2.2), e adota a **opção C** (`0,5–2,0` / `2,5–3,0` / `3,5–5,0`, semântica "não recomendam / mornos / recomendam"); (b) faz a coleta raspar um **superset por nível** e **persistir tudo em disco** (`dados/bruto/<slug>/`, §3[B']), com condição de parada em três degraus de precedência (piso de 1 página por nível com material > alvo com folga de 25% > teto de 4 páginas); (c) torna a **ordenação de listagem** um parâmetro de amostragem explícito, gravado no material coletado, com default trocado de `by/activity` (ordenada por ENGAJAMENTO) para `by/added` (**cronológica**, mais recentes primeiro) — ver §2.3; (d) substitui a cota igual por nível por **alocação proporcional ao histograma** dentro de cada bucket, com piso por nível e redistribuição de déficit restrita ao mesmo bucket (§3[C1]); (e) aplica a **cota de análise 40/40/40 downstream**, sobre o bruto persistido, com min_chars/spoiler/cascata como parâmetros (§3[C2]); e (f) troca o piso binário de 3 por um **piso escalonado de 4 estados** (`completa`/`sem_quantificador`/`sem_numero`/`sem_analise`), exposto como campo no JSON (§3[C3]). **Consequência publicada:** sob as fronteiras C os shares dos 3 filmes do catálogo MUDAM — `cure` 3/17/79 → 2/8/90, `the-invite-2026` 3/18/79 → 2/7/91, `cidade-de-deus` 1/8/91 → 1/3/96. **Risco aceito e mitigações** em §2.2. v1.2.0 adiciona a etapa **[D2] narrador** (§D2) e a flag `--tom` como **mecanismo de desenvolvimento** para A/B de saída. v1.2.1 corrige uma classe de infidelidade do narrador (cota de amostragem apresentada como distribuição da recepção) — invariante nova no §D2 + telemetria. v1.2.2 adiciona calibração numérica dos quantificadores da narrativa (mapa fração→palavra, faixa mais fraca em caso de dúvida) — verificação por instrução ao LLM. v1.2.3 move a calibração do prompt para o CÓDIGO: os rótulos de quantificador passam a ser pré-computados e o LLM só os usa, não os escolhe (mesmo princípio da v1.1.1 — código como autoridade de número/rótulo). v1.3.0 adiciona uma **ficha técnica do filme via TMDB** (§3a, aditiva — nunca bloqueia o pipeline) e reestrutura §D2 para uma narrativa em **três movimentos** (filme → experiência consensual → contraste entre grupos), com uma emenda pontual à regra de "zero conteúdo de trama" para permitir a sinopse OFICIAL curta como fonte do primeiro movimento (ver §3[D] "Anti-spoiler"). **v1.3.1** corrige um defeito real observado na primeira execução do MOVIMENTO 2 (a narrativa de `the-invite-2026` importou um juízo de QUALIDADE — "atuações marcantes"/"roteiro inteligente" — como se fosse um consenso DESCRITIVO, contradizendo diretamente os temas do grupo negativas): a regra do MOVIMENTO 2 ganha três critérios explícitos (categoria/presença/não-contradição) e telemetria de `consensos_usados` para revisão humana de cada execução (ver §D2). **v1.4.0** é a maior mudança desde a v1: o pipeline passa a coletar a **distribuição real de notas** (histograma público do Letterboxd, §3b) e, com ela, **inverte** a regra de prevalência do §D2 — o que a v1.2.1 proibiu por falta do dado, a v1.4.0 torna obrigatório e ancorado (ver "Princípio norteador" abaixo). **v1.4.1** corrige três defeitos pontuais observados na entrega da v1.4.0, todos no §D2: (1) telemetria de quantificadores **por par declarado** (`quantificadores_usados`), depois da 3ª reincidência do mesmo modo de falha, que a rede de nível de bucket não pega; (2) **omissão autorizada** do MOVIMENTO 2, contra a pressão de preenchimento que produz juízo de qualidade hedgeado; (3) **invariante de vocabulário do peso** — rótulos de peso dizem "das notas", nunca "das reviews"/"do público"/"dos espectadores". **v1.5.0** ataca um defeito de **fluência**, não de honestidade: as narrativas entregues até a v1.4.1 são factualmente corretas, mas soam mecânicas — forma sintática repetida (rótulo de peso + verbo de reporte + complemento, três vezes seguidas), frases quase todas do mesmo comprimento, excesso de verbos de reporte e nominalizações no lugar de verbos. O diagnóstico (registrado no changelog) é que o acúmulo de invariantes de honestidade das versões anteriores empurrou o modelo à única forma que satisfaz todas simultaneamente. A correção prescreve **ritmo** e **registro** com a mesma precisão de código com que já se prescrevem números, adiciona uma **marcação de perspectiva** pré-computada (para que a redução de verbos de reporte não deixe a fala de um grupo minoritário soar como fato do narrador) e duas telemetrias novas (`marcadores_perspectiva`, `metricas_fluencia`) — **sem afrouxar nenhuma invariante de honestidade** das versões anteriores. **v1.6.0** conclui que a v1.5.0 errou no MÉTODO, não no objetivo: empilhar honestidade e fluência num prompt só não funcionou (as regras de ritmo não transferiram entre filmes, as métricas que as fiscalizavam não acompanhavam qualidade, e a configuração de produção chegou a publicar uma frase agramatical). A correção é **separar responsabilidades**: o narrador (§D2) é podado de volta a UMA responsabilidade — dizer a verdade com a estrutura certa — e um estágio novo, o **editor [E2]** (§E2), assume ritmo e leitura sem ter acesso a nenhuma fonte de fato e sem poder alterar número, rótulo ou atribuição (trechos protegidos + verificação mecânica + descarte da edição em caso de violação). **v1.6.1** corrige o defeito 5.2 que a v1.6.0 deixou em aberto: em vez de normalizar a COMPARAÇÃO entre o trecho declarado e o texto (caixa/acento/demonstrativo), passa a verificar a EXISTÊNCIA de uma expressão de atribuição reconhecida no texto realmente escrito — o que fecha também o caso de reordenação de palavras que a normalização não alcançava, e reduz `marcadores_perspectiva` a telemetria pura (auditoria humana, não fonte de validação). **v1.6.2** corrige um bug de substring solta descoberto ao vivo na regeneração de `cidade-de-deus` (shares 1%/8%/91%): `_ancora_de_grupo` e `_ancoragem_de_peso_ok` buscavam o percentual de um grupo com `f"{pct}%" in texto`/`texto.find(...)`, que casa **dentro** de outro número — `"1%"` combinava com o "1" final de `"(~91%)"`, ancorando o grupo `negativas` (1%) numa posição muito anterior à sua menção real, corrompendo o cálculo do span de movimento e produzindo falso positivo em `perspectiva_nao_marcada` mesmo com o texto correto e bem marcado. A busca agora usa `re.search(rf"(?<!\d){pct}%", texto)` (nega dígito imediatamente anterior), então `"1%"` só casa como número isolado, nunca como sufixo de `"91%"`/`"21%"`/etc. Mesmo defeito corrigido nos dois pontos que faziam a busca (âncora de grupo e checagem de ancoragem de peso), com testes de regressão cobrindo o caso real. Nenhuma invariante de honestidade foi afrouxada — o fix é estritamente sobre a CHECAGEM, não sobre o que é permitido no texto. **v1.7.0** corrige dois defeitos reais observados na regeneração das narrativas: (1) **resolução de ficha do filme errado** — `espectro24 --slug cure` sem `--ano` resolvia no TMDB para "The Cure" (2026, dir. Nancy Leopardi) em vez de Cure (1997, Kiyoshi Kurosawa), porque a desambiguação por popularidade sem ano escolhe o candidato errado quando o título é comum; a resolução de ano ganha uma cadeia de fallback confiável (slug → página do Letterboxd → sem ficha) e uma guarda de sanidade que descarta a ficha inteira se o ano devolvido pelo TMDB divergir do esperado em mais de 1 ano (ver §3[A]); (2) **lista de protegidos do editor §E2 enxugada** — protegia até 16 trechos por filme, incluindo quantificadores soltos ("muitos") e expressões de atribuição, o que descartava o editor com frequência (`cure`) ou o levava a inventar frases só para reencaixar um protegido movido ("Essa é a opinião de uma fração mínima das notas.", `cidade-de-deus`), e ainda deixava sobreviver um defeito gramatical real ("destacando a a maioria o estilo visual") porque a frase continha um rótulo protegido; a proteção literal agora cobre só rótulo de peso COM percentual e tokens numéricos — quantificador e atribuição passam a valer SÓ pela checagem semântica que já existia e era mais forte (`conferencia_quantificador` v1.4.1, `_marcadores_validos` v1.6.1), revalidada dentro do próprio `editar_narrativa` (ver §E2). **v1.7.1** corrige três defeitos de acabamento observados no texto PUBLICADO da v1.7.0, nenhum deles de honestidade: (1) **contrabarra residual** — `_remover_aspas` trocava só o caractere de aspas por "", então uma citação escapada (`\"A Cura\"`) virava `\A Cura\` (publicado em `cure` e `the-invite-2026`); a remoção agora consome a contrabarra que precede a aspas junto, como uma unidade. (2) **capitalização de rótulo protegido movido** — o rótulo de peso guarda a caixa de onde apareceu a primeira vez (início de frase, capitalizado); quando o editor o move para o meio de um período, a checagem 100% literal não deixava ajustar só a inicial, e o defeito ("Para A grande maioria...", `cidade-de-deus`) sobrevivia porque corrigir quebraria o protegido; a checagem de trecho perdido agora aceita a primeira letra em qualquer caixa — e SÓ ela, nenhuma outra letra, palavra ou número do trecho. (3) **família "quem gostou/não gostou" ausente do vocabulário de atribuição** — o `cure` escreveu "quem não gostou considerou o ritmo lento e tedioso" para o grupo de 3%, uma atribuição real, mas fora da lista de expressões reconhecidas (`_EXPRESSOES_DE_PERSPECTIVA`), produzindo falso positivo em `perspectiva_nao_marcada`; a família foi acrescentada ("quem gostou", "quem não gostou", "quem amou", "quem ficou no meio", e as formas com "para" na frente), mantendo de fora o "para quem" ISOLADO (pronome relativo comum, motivo do falso negativo original da v1.6.0). Nenhuma invariante de honestidade foi afrouxada nas três correções — são fixes de CHECAGEM e de limpeza mecânica, não mudança do que é permitido no texto. **v1.7.2** corrige um defeito real observado na regeneração do `cidade-de-deus` sob a v1.7.1: o editor devolveu a prosa embrulhada num invólucro `{ text: "..." }`, ignorando a instrução de responder só texto puro — e TODAS as checagens mecânicas de então (protegidos, conjunto numérico, honestidade) passaram, porque rodam sobre SUBSTRING e o protegido/os números continuavam achados DENTRO do invólucro. A edição foi marcada "aplicada"; só a leitura humana antes de publicar pegou o defeito. A correção acrescenta uma **checagem ESTRUTURAL** (`_formato_invalido`, §E2), aplicada ANTES de todas as outras: rejeita o texto se ele começar com `{`/`[`, contiver cerca de código (```), tiver uma das primeiras linhas com cara de campo JSON (`"text":`, `text:`, `"narrativa":`), ou tiver chaves desbalanceadas — mesma política das demais checagens (1 retentativa com reforço explicando o formato exigido; se persistir, descarta com `motivo_descarte: "formato_invalido"` e publica a bruta). Deliberadamente NÃO rejeita uma chave/colchete equilibrado no MEIO da prosa — só o formato de invólucro, não qualquer ocorrência do caractere. **v1.7.3** corrige um defeito de POLÍTICA, não de checagem: na regeneração da v1.7.1, a edição foi DESCARTADA em 2 dos 3 filmes (`cure` — número alterado; `cidade-de-deus` — regressão de `perspectiva_nao_marcada`), publicando a bruta nos dois, enquanto a MESMA combinação de código e dados tinha sido ACEITA nos 3 filmes sob a v1.7.0 — nada mudou no código nesse sentido entre as duas rodadas; é VARIÂNCIA do modelo entre chamadas, e a política de então (1 chamada + 1 retentativa, 2 no total) dava pouca margem para a variância favorecer numa etapa cujo descarte já é fail-safe (a bruta do narrador sempre prevalece). A correção eleva o teto para até `1 + EDITOR_MAX_TENTATIVAS` chamadas (`EDITOR_MAX_TENTATIVAS = 3` em `config.py`, 4 no total no pior caso) e muda o reforço de SUBSTITUÍDO para ACUMULADO entre tentativas — se a 1ª falha por número e a 2ª por atribuição, a 3ª recebe os dois reforços juntos, para o modelo não consertar um problema criando outro. Nova telemetria em `edicao_flags`: `n_tentativas` (quantas chamadas foram feitas) e `motivos_por_tentativa` (o motivo de cada falha, na ordem) — visibilidade de qual checagem mais reprova o editor, não critério de aprovação. Nenhuma invariante de honestidade foi afrouxada: o fail-safe de descarte após esgotar as tentativas continua idêntico, só o número de chances antes dele mudou. **v1.7.4** corrige dois defeitos: um buraco de arquitetura e um resíduo cosmético recorrente. (1) **checagem de EDIÇÃO NULA** — nenhuma checagem até a v1.7.3 verificava que a edição FEZ algo, só que ela não QUEBROU nada; um editor que devolva a entrada praticamente intacta passa em protegidos (nunca saíram), números (nada mudou) e honestidade (é o mesmo texto), e era marcado "aplicada" sem nenhum sinal de que não houve edição de verdade. A correção calcula a similaridade (`difflib.SequenceMatcher.ratio`, textos normalizados só por espaço em branco) entre `narrativa_bruta` e o texto editado; se as demais checagens TERIAM passado mas a similaridade é `>= EDITOR_LIMIAR_EDICAO_NULA` (0.97, deliberadamente conservador — só pega devolução literal ou trivial, não uma edição legítima que preserve vocabulário protegido), trata como falha de tentativa com motivo `"edicao_nula"`, no mesmo ciclo de retentativa/descarte já existente. `edicao_flags.similaridade` é persistido SEMPRE (aceita ou não), telemetria para calibrar o limiar. (2) **capitalização residual, correção determinística** — a v1.7.1 AUTORIZOU o editor a ajustar a caixa de um rótulo de peso movido para o meio da frase, mas não o OBRIGA, e ele frequentemente não ajusta ("Já Uma fração mínima...", "Para A grande maioria..."). Em vez de depender do LLM, um pós-processamento em CÓDIGO (`_corrigir_capitalizacao_residual`) roda sobre toda edição ACEITA: baixa a inicial de qualquer rótulo de peso canônico que apareça capitalizado fora de início de período (mesmo princípio de toda pré-computação do pipeline — o determinístico é decidido pelo código, não pelo LLM). `edicao_flags.capitalizacao_ajustada` registra se algo mudou. **v1.8.1** REATIVA o editor [E2] por padrão (`EDITOR_ATIVO=True`) — a v1.8.0 tinha desligado por precaução após um defeito de conteúdo inventado, mas a MESMA versão já corrigira a causa raiz (checagem de conteúdo adicionado + ordem dos movimentos); a validação pós-correção (`VALIDACAO_EDITOR_V18.md`, 3 filmes reais) mostrou a checagem disparando de verdade em produção e o modelo se autocorrigindo na retentativa, com os limiares bem separados do ruído normal de uma edição legítima — evidência suficiente para reativar. **v1.8.0** troca o provider DEFAULT de produção para **DeepSeek** (`deepseek-v4-flash`, ver Changelog) e, na mesma versão, DESLIGA o editor [E2] por padrão como medida de contenção — a validação que justificou a troca de provider também descobriu um defeito real e mais sério: o editor pode ACRESCENTAR conteúdo (opinião, frase de fechamento, reordenar movimentos) sem que nenhuma checagem mecânica até a v1.7.4 detecte, porque todas checavam PERDA, nenhuma ADIÇÃO. Duas checagens novas (conteúdo adicionado por similaridade de frase, ordem dos movimentos) mitigam o defeito e o editor volta a ser ligável via `--com-editor`, mas o default de produção segue conservador até mais evidência.

---

## 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO

> Os três grupos recebem **formato idêntico**: mesma profundidade de análise
> (cota **40/40/40** — v1.9.0; era 50/20/30 até a v1.8.2), mesma estrutura de
> temas, mesmo estilo tipográfico, mesmo espaço estrutural na interface. **A
> assimetria vem dos dados, não da apresentação.**

> **v1.9.0 — a cota igual passou a ser literal.** Até a v1.8.2 o princípio era
> declarado mas não cumprido: 50/20/30 não era uma decisão de profundidade, era
> um **acidente aritmético** (10 reviews × o número de níveis de estrela de cada
> faixa: 5/2/3). O grupo mediano recebia 40% da profundidade do negativo por
> ter dois níveis em vez de cinco — e a diferença não tinha nenhuma
> justificativa de design. A cota 40/40/40 é a mesma frase de sempre, agora
> escrita como número: **profundidade igual por perspectiva, peso informado à
> parte**. O piso escalonado (§3[C3]) é o que trata o caso em que um grupo
> simplesmente não tem 40 reviews com texto — sem fingir que tem.

**O problema que motivou a versão** (feedback recorrente de usuários reais):
filmes amplamente aclamados *soam divididos* no produto, porque os três grupos
recebem o mesmo peso textual e visual. Um filme com 91% das notas na faixa alta
era apresentado com a mesma proeminência dada ao grupo de 1% — o leitor saía
com a impressão de controvérsia onde havia consenso. Isso é uma **infidelidade
por omissão**: cada frase era verdadeira, mas o conjunto comunicava algo falso.

A v1.2.1 já havia diagnosticado a raiz (as cotas de coleta não são a
distribuição da recepção) e escolhido a única saída disponível na época:
**proibir** qualquer afirmação de prevalência. O changelog daquela versão e a
seção "Candidatos à próxima versão" registraram explicitamente que a correção
de raiz seria coletar o histograma. É o que esta versão faz — e por isso a
regra inverte em vez de ser "afrouxada": não é uma concessão, é o dado que
faltava chegando.

**Duas invariantes que a inversão NÃO toca:**

1. **`share` por faixa NÃO é nota média.** São três números que particionam a
   população de notas, cada um atribuído à sua faixa. A proibição de score
   agregado, nota média ou "X de 10" (§1) permanece **intacta** e está escrita
   dentro da própria regra invertida do prompt. Em nenhum lugar do produto
   existe um número-síntese único do filme.
2. **A perspectiva minoritária continua analisada com o mesmo rigor.** Menos
   espaço na prosa, **mesma seriedade**: sem desdém, sem ironia, sem sugerir
   que quem pensa assim está errado. Quem procura saber se vai gostar precisa
   entender o que incomodou aquela parcela — e um grupo de 1% mantém seus 6
   temas, suas barras e suas paráfrases na interface.

---
**Objetivo:** dado o nome de um filme, agregar reviews de usuários do Letterboxd em três buckets por nota e produzir, via LLM, uma síntese temática de cada bucket — pontos recorrentes com frequência — permitindo entender a recepção do filme sem viés de leitura seletiva e sem spoilers.

**Público-alvo:** pessoa que ainda NÃO assistiu ao filme. Toda decisão de design que envolva trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler.

---

## 1. Escopo v1

**Dentro:** CLI/script local; fonte única Letterboxd; três buckets com cota por nível de nota; busca de texto completo de reviews truncadas; cache em disco; saída estruturada JSON + render em texto no terminal.

**Fora (explicitamente):** UI web, FastAPI, deploy, IMDB como fallback, reviews sem nota, múltiplos idiomas de saída (saída em pt-BR, reviews de entrada em qualquer idioma).

---

## 2. Parâmetros congelados

> **v1.9.0 — "congelado" deixou de significar "hardcoded".** Metade desta
> tabela descreve decisões de **ANÁLISE** (fronteira, cota, filtro, piso) que
> até a v1.8.2 eram aplicadas **durante a coleta** e ficavam gravadas no
> material coletado. Elas continuam congeladas no sentido de "não se muda sem
> bump de versão", mas passam a ser **parâmetros aplicados downstream**, sobre
> um bruto persistido que não sabe nada sobre elas (§3[B']). A coluna "Camada"
> diz onde cada parâmetro atua: `coleta` (afeta o que é raspado e persistido —
> mudar exige recoletar) ou `análise` (aplicado sobre o bruto — mudar exige só
> re-rodar a seleção).

| Parâmetro | Valor | Camada | Origem |
|---|---|---|---|
| **Fronteiras de bucket** | **Negativas 0,5–2,0 · Mornos 2,5–3,0 · Positivas 3,5–5,0** | análise | **v1.9.0 — opção C (§2.2)** |
| ~~Cota de reviews válidas POR NÍVEL de nota (10)~~ | **REMOVIDA na v1.9.0** — substituída por alocação proporcional (§3[C1]) | — | v1.1.0, revogada v1.9.0 |
| **Cota de análise por bucket** | **40 · 40 · 40** | análise | **v1.9.0 — profundidade igual, literal (§0)** |
| **Alocação dentro do bucket** | proporcional ao histograma, `n(L) = max(piso_nivel, round(N × c_L / C_bucket))` | análise | **v1.9.0 (§3[C1])** |
| **Piso de alocação por nível** | **2** (só para níveis com material no histograma) | análise | **v1.9.0 — ARBITRÁRIO, calibrável** |
| **Piso de análise por bucket** | **escalonado, 4 estados** (≥15 · 8–14 · 3–7 · <3) | análise | **v1.9.0 — limiares ARBITRÁRIOS (§3[C3])** |
| Filtro de comprimento (padrão) | ≥ 150 chars | análise | Decisão de design |
| Relaxamento em cascata (por nível) | 150 → 50 → sem filtro | análise | Decisão de design |
| **Folga do alvo de coleta** | **× 1,25** sobre a cota alocada — usada SÓ para o orçamento de completamento [C'] desde a v1.9.2 (§3[B]) | coleta | **v1.9.0**, escopo reduzido v1.9.2 |
| ~~Piso de páginas por nível (gate do ALVO)~~ | **REVOGADO na v1.9.2** — só existia para condicionar a parada por ALVO, que foi removida; a reversibilidade (§2.2) já é garantida pelo piso da alocação de páginas (`orcamento_paginas_bucket`), não por esta constante | — | v1.9.0, revogado v1.9.2 |
| ~~Parada por ALVO (cota × folga, heurística)~~ | **REMOVIDA na v1.9.2** — causava não-determinismo sob orçamento fixo (foi a causa do 37/40 residual de `cidade-de-deus` na v1.9.1); o orçamento de páginas passa a ser sempre gasto integralmente | coleta | v1.9.0, revogada v1.9.2 (§3[B]) |
| ~~Teto de paginação por nível de nota (4 páginas)~~ | **REVOGADO na v1.9.1** — o teto passou a ser por BUCKET, não por nível (defeito estrutural registrado na v1.9.0) | — | v1.9.0, revogado v1.9.1 |
| **Orçamento de páginas por BUCKET** | **16 páginas** (~192 reviews brutas), distribuídas entre os níveis do bucket proporcional ao histograma | coleta | **v1.9.1 (§3[B])** |
| **Teto de segurança por nível** | **10 páginas** — nenhum nível sozinho consome o orçamento inteiro do bucket | coleta | **v1.9.1 (§3[B])** |
| **Reserva de profundidade** | **25%** do orçamento de cada nível, posicionada em progressão geométrica além do bloco raso | coleta | **v1.9.2 (§3[B])** |
| **Texto truncado enviado ao LLM** | **PROIBIDO — texto completo obrigatório ou descarte** | ambas | **v1.1.0 — decisão do usuário** |
| Delay entre requisições | ≥ 2s, sem paralelismo | coleta | Fase 0: anti-bot presente |
| **Ordenação da listagem** | **`by/added`** (cronológica, mais recentes primeiro) | coleta | **v1.9.0 (§2.3)** — era `by/activity` |
| Reviews sem nota | Não coletadas (a URL já é por nível) | coleta | Decisão de design |
| Reviews com flag de spoiler | **Persistidas no bruto, excluídas na seleção** | análise | **v1.9.0** — era "descartadas na coleta" |

### 2.1 Parâmetros técnicos congelados (Fase 0)

| Item | Valor |
|---|---|
| URL de coleta | `letterboxd.com/film/<slug>/reviews/rated/<N>/<ordenacao>/[page/<n>/]` — `<ordenacao>` é PARÂMETRO (§2.3), default `by/added` |
| Formato de nota na URL | **Decimal**: `0.5, 1, 1.5 … 5` (nunca o glifo `½`) |
| **Página além da última** | **Validado (Fase 1):** retorna **200 com lista de reviews vazia** — esse é o sinal de parada da paginação, não erro/redirect |
| Endpoint de texto completo | **Validado (Fase 1):** `letterboxd.com/s/full-text/viewing:<id>/`, retorna fragmento HTML (`<p>` sem wrapper) |
| **Endpoint de busca de slug** | **Validado (Fase 1):** `letterboxd.com/s/search/films/<query>/` (AJAX, server-rendered). A URL humana `letterboxd.com/search/films/<query>/` é só um shell React — resultados vêm vazios no HTML estático dela |
| **Dedup / cache por review** | **Validado (Fase 1):** `p[data-likeable-identifier]` → JSON `uid` = `viewing:<id>`. Universal (presente em toda review); NÃO usar `data-full-text-url` para isso — ele falta em alguns casos |
| Container de review | `article.production-viewing` (fallback: `li.film-detail`) |
| Corpo do texto | `.body-text` / `.js-review-body` |
| Nota | `span.inline-rating`, parsing `count("★") + (0.5 se "½")` (fallback: `span.rating` classe `rated-N`, N = estrelas×2) |
| Spoiler | **Corrigido (Fase 1 / v1.1.1):** placeholder de texto **exato** `"This review may contain spoilers. I can handle the truth."` no corpo. Não usar substring genérica ("may contain spoilers" sozinho tem falso positivo em prosa legítima). **Ressalva:** se o Letterboxd localizar essa string para outros idiomas, o detector quebra silenciosamente — nenhum teste automatizado cobre esse cenário (ver `FASE1_INCOGNITAS.md`) |
| Headers | User-Agent de navegador + `Accept`, `Referer`, `Upgrade-Insecure-Requests`, `Sec-Fetch-*`, `Sec-Ch-Ua` |
| `Accept-Encoding` | **`gzip, deflate` apenas** (nunca `br` sem lib brotli instalada) |
| Plano B anti-bot (não ativar sem necessidade) | `curl_cffi` com `impersonate="chrome"`, mesmo delay |
| **Config LLM da PROSA (v1.6.0)** — narrador §D2 + editor §E2 | `thinking_budget=4096` (FIXO) · `max_output_tokens=16000` |
| **Config LLM da SÍNTESE (§D)** — inalterada | `thinking_budget=0` · `max_output_tokens=3000` |

---

## 2.2 Fronteiras de bucket — CONFIGURAÇÃO, não constante (v1.9.0)

**A regra estrutural, e ela é a razão de ser desta versão:** as fronteiras
**não podem estar hardcoded em nenhum ponto do código**. Elas vivem num único
lugar (`FRONTEIRAS`, em `buckets.py`), e o mapeamento nível→bucket é uma
**função pura testável** (`bucket_de_nivel`). Todo o resto — a lista de níveis
de cada bucket, os intervalos escritos nos prompts, a agregação do histograma,
a alocação, a seleção — é **derivado** dessa configuração, nunca redigitado.
A prova de que é parâmetro e não constante é um teste que roda o mapeamento
sob fronteiras **alternativas** e confere que tudo acompanha.

**Fronteiras em vigor — opção C.** Semântica: *não recomendam / mornos /
recomendam*.

| Bucket | Faixa | Níveis | Antes (v1.8.2) |
|---|---|---|---|
| `negativas` | **0,5–2,0★** | 4 | 0,5–2,5★ (5) |
| `medianas` (mornos) | **2,5–3,0★** | 2 | 3,0–3,5★ (2) |
| `positivas` | **3,5–5,0★** | 4 | 4,0–5,0★ (3) |

Duas mudanças: **2,5★ sai de negativas e entra em mornos**; **3,5★ sai de
mornos e entra em positivas**. O nome interno do bucket do meio continua
`medianas` (é chave de JSON consumida pelo frontend e pelo narrador — renomear
seria churn fora do escopo desta versão); a **semântica** documentada é
"mornos".

**Por que:** 2,5★ é o ponto médio exato da escala do Letterboxd e ler o meio da
escala como "não recomenda" é uma escolha, não um dado; e 3,5★ é, na prática
observada, uma nota de recomendação com ressalva — tratá-la como morna
subestimava sistematicamente a recepção positiva. A fronteira nova alinha o
corte à pergunta que o produto responde ("vale assistir?"), em vez de à
aritmética da escala.

### Consequência medida — os shares publicados MUDAM

Recalculados sobre o **mesmo** histograma já coletado (zero requisições):

| Filme | Antigas (neg/med/pos) | **Novas C** | Movimento |
|---|---|---|---|
| `cure` | 3 / 17 / 79 | **2 / 8 / 90** | positivas +11pp, medianas −9pp |
| `the-invite-2026` | 3 / 18 / 79 | **2 / 7 / 91** | positivas +12pp, medianas −11pp |
| `cidade-de-deus` | 1 / 8 / 91 | **1 / 3 / 96** | positivas +5pp, medianas −5pp |

O padrão é o esperado: **positivas crescem com a entrada do 3,5★** (um nível
populoso — 11-12% de todas as notas nos três filmes) e **negativas encolhem
com a saída do 2,5★** (um nível pequeno, daí o movimento de só 1-2pp desse
lado). O grosso do deslocamento vem do bucket do meio, que perde o nível
grande e ganha o pequeno.

### RISCO ACEITO da opção C, e as mitigações

**Risco 1 — saturação do rótulo de peso no extremo forte.** Com positivas
rotineiramente em 90-96%, a faixa mais alta do mapa de `rotulo_peso` (§D2,
`≥ 70% → "a grande maioria"`) satura: filmes de 71% e de 96% recebem o **mesmo
rótulo**. É exatamente o defeito que a v1.6.0 corrigiu no extremo **fraco**
(8% e 1% recebiam ambos "uma pequena minoria"), reaparecendo simétrico no
extremo oposto — e a opção C o torna a regra, não a exceção.
*Mitigação:* registrado como **candidato explícito** (faixa nova acima de ~90%,
ex. `≥ 90% → "praticamente todas as notas"`), **NÃO aplicado nesta versão** —
o mapa de rótulos é do narrador, fora do escopo desta sessão. O percentual
continua sendo entregue junto do rótulo, então o número não mente enquanto o
rótulo estiver achatado; e a telemetria desta versão publica os shares sob as
duas fronteiras lado a lado, para que a decisão de recalibrar seja tomada com
dado, não com estimativa.

**Risco 2 — mudança silenciosa da marcação de perspectiva.** `marcacao_perspectiva`
(§D2) é pré-computada a partir do `share_real` com limiares `dominante/3` e
`dominante/10`. Subir o dominante de 91 para 96 (`cidade-de-deus`) empurra
mais grupos para o degrau mais restritivo (`antecipada`). Nenhuma linha de
código muda; o comportamento do narrador muda porque o **dado** de entrada
mudou.
*Mitigação:* declarado aqui como consequência prevista, e não como bug quando
aparecer na próxima regeneração de narrativa. Os limiares já estão registrados
como "ponto de partida, calibráveis" desde a v1.5.0.

**Risco 3 — a fronteira pode estar errada.** É uma decisão semântica sem
ground truth. 2,5★ pode ser, para parte do público, uma não-recomendação.
*Mitigação, e é a principal:* **a fronteira deixou de ser cara de trocar.** O
bruto persistido (§3[B']) não sabe onde ficam as fronteiras — guarda reviews
etiquetadas por **nível de estrela**, que é dado do Letterboxd, não decisão
nossa. Trocar a fronteira é editar `FRONTEIRAS` e re-rodar a **seleção**, com
**zero requisições de rede**. O que antes custava uma recoleta completa hoje
custa um re-run offline. Reforçando essa garantia, a condição de parada da
coleta tem um **piso de 1 página por nível sempre que houver material** (§3[B]),
**mesmo para níveis cuja alocação é zero** — é o seguro de reversibilidade:
garante que o bruto sempre contenha material de todos os 10 níveis, para que
qualquer fronteira futura tenha o que reavaliar.

---

## 2.3 Ordenação da listagem — parâmetro de amostragem (v1.9.0)

A ordem em que o Letterboxd lista as reviews de um nível **é um parâmetro de
amostragem**, não um detalhe de URL: só as primeiras `N` páginas são lidas, e a
ordenação decide *quais* reviews caem nessa janela. Até a v1.8.2 ela estava
congelada em `by/activity` e não era registrada em lugar nenhum do material
coletado — não dava para saber, olhando um dado antigo, sob qual amostragem
ele foi obtido. A partir da v1.9.0 é **configuração**, e é **gravada no
`meta.json` do bruto** (`ordenacao_usada`).

**Menu real do Letterboxd** (lido do HTML de `/film/<slug>/reviews/rated/<N>/`,
grupo "Sort by"; três opções, confirmadas ao vivo em `cure`, nível 4★):

| Chave | Segmento de URL | Rótulo no site | Comportamento medido (datas das 6 primeiras reviews) |
|---|---|---|---|
| **`mais_recentes`** | **`by/added`** | Newest First | `2026-08-07 … 2026-08-06` — **estritamente decrescente** |
| `mais_antigas` | `by/added-earliest` | Earliest First | `2012-11-10 … 2014-03-16` — estritamente crescente |
| `atividade` | `by/activity` | Review Activity | `2023-02-15, 2020-10-22, 2024-04-04, 2022-10-23, 2021-10-09, 2025-11-21` — **sem ordem temporal** |

**Default novo: `by/added` (`mais_recentes`).** É a opção mais próxima de
cronológica e a que **não carrega sinal de engajamento**. `by/activity` ordena
por atividade recente na review (curtidas, comentários) — as datas medidas
acima, espalhadas por seis anos sem ordem, são a prova de que o critério é
engajamento e não tempo; e engajamento enviesa para review longa, escrita com
intenção de ser lida, e promovida pela comunidade. Esse é precisamente o viés
que a amostra não deve ter.

**Por que não `by/added-earliest`**, que é igualmente cronológica: para um
filme com centenas de milhares de reviews, as primeiras páginas por
"Earliest First" vêm todas da janela de lançamento (no `cure`, de 2012-2014) —
um recorte de coorte severo (público de festival / primeiros adeptos), pior
como amostra da recepção do que o recorte recente.

**Correção de registro:** a v1.0.0 justificou `by/activity` como quem "mitiga
viés de *popularity* e review-piada" (§2, Fase 0). O menu real do site não
oferece uma ordenação "popularity" separada — as três opções são as da tabela
acima, e `by/activity` **é** a ordenada por engajamento. A justificativa
original não se sustenta contra o HTML observado, e está corrigida aqui.

**Ressalva honesta:** trocar `by/activity` por `by/added` troca um viés
(engajamento) por outro (recência). Não existe amostragem neutra dentro deste
menu — existe amostragem **declarada**. O ganho desta versão é que a escolha
virou parâmetro visível e gravado, não uma constante enterrada numa URL.

#### O tamanho MEDIDO do viés de recência (recoleta de 2026-08-07)

A ressalva acima era qualitativa. Medida sobre o bruto persistido, ela é
maior do que a palavra "recência" sugere:

| Filme | janela dos 2 meses mais densos | concentração |
|---|---|---|
| `the-invite-2026` | 2026-07 + 2026-08 | **100%** das 396 |
| `cure` (1997) | 2026-07 + 2026-08 | **95%** das 384 |
| `cidade-de-deus` (2002) | 2026-07 + 2026-08 | **79%** das 384 |

Para um filme de catálogo com centenas de milhares de notas, **a amostra
inteira vem de ~6 semanas de atividade recente**. Isso não é um detalhe de
ordenação: a análise temática passa a descrever *quem está descobrindo o filme
agora*, não a recepção acumulada. Sob `by/activity` a mesma sondagem devolvia
reviews espalhadas por 2020-2025 (§2.3, tabela do menu).

**Isso não reverte a decisão** — engajamento continua sendo o pior dos dois
vieses, porque correlaciona com o *conteúdo* da review (longa, performática,
promovida), enquanto recência correlaciona só com *quando*. Mas o tamanho do
efeito precisa estar escrito, e agora está. Candidato de próxima versão:
amostragem estratificada por período (N páginas de `by/added` + N de
`by/added-earliest`), que o superset persistido já suporta sem mudança de
arquitetura — coletas com ordenações diferentes **acumulam** no mesmo `jsonl`
(§3[B']).

**Correção sobre o campo `data` (§3[B']):** ele vem do `<time class="timestamp">`
da listagem, que é a data **ASSISTIDA** (entrada de diário), não a data em que
a review foi publicada. Consequência observada: ~16% dos pares consecutivos do
`cure` aparecem "fora de ordem" decrescente, e a amostra tem extremos de 2023
— são reviews **recentes** sobre sessões **antigas**, não falha de ordenação.
O campo continua sendo a melhor evidência disponível sobre a janela da amostra,
mas é evidência **indireta**; a spec não deve tratá-lo como carimbo de ordem.

---

## 3. Pipeline

```
input (nome do filme)
  → [A] resolução de slug
  → [G] distribuição real de notas — histograma (v1.4.0; PROMOVIDO na v1.9.0)
  ══ COLETA ══ (não sabe nada de fronteira, cota ou filtro)
  → [C1] alocação proporcional ao histograma (v1.9.0 — define o alvo por nível)
  → [B]  raspagem do SUPERSET por nível de nota (com cache)
  → [C'] completamento de reviews truncadas
  → [B'] PERSISTÊNCIA do bruto em dados/bruto/<slug>/ (v1.9.0)
  ══ ANÁLISE ══ (lê o bruto persistido; zero rede)
  → [C2] seleção 40/40/40: fronteiras + filtros + cascata como PARÂMETROS
  → [C3] piso escalonado (4 estados)
  → [D] síntese LLM por bucket
  → [D2] narrador (opcional, --tom; lê [G] se existir)
  → [E2] editor — passe de fluência sobre a narrativa (v1.6.0; --no-edicao pula)
  → [F] ficha do filme via TMDB (aditiva, independente de D/D2 — v1.3.0)
  → [E] render (JSON + terminal)
```

**A linha divisória COLETA / ANÁLISE é a mudança central da v1.9.0.** Acima
dela, nada sabe onde ficam as fronteiras de bucket, qual é a cota, ou qual
filtro de comprimento vale: a coleta raspa por **nível de estrela** — que é
dado do Letterboxd — e persiste tudo. Abaixo dela, tudo é parâmetro aplicado
sobre o material já em disco. A consequência prática: **mudar fronteira, cota,
filtro ou piso não custa mais nenhuma requisição de rede.** A única coisa que
atravessa a linha na direção "análise → coleta" é a **alocação** ([C1]), e ela
atravessa apenas como *alvo de quando parar de paginar* — nunca como filtro do
que é gravado.

**[G] foi PROMOVIDO na v1.9.0** de etapa aditiva pós-coleta para **pré-requisito
da coleta**: a alocação proporcional ([C1]) precisa do histograma para calcular
o alvo por nível. **Continua sem custar requisição extra** (é o mesmo 1 request
cacheado de sempre, só que executado antes) e **continua sem bloquear**: sem
histograma, [C1] cai para alocação **uniforme** (`N_bucket ÷ nº de níveis do
bucket`), a coleta segue igual, e o resto do pipeline degrada como já degradava
(§D2 fallback). O que muda é a ordem, não a dependência.

**[F] roda em paralelo conceitual a [D]/[D2]:** não depende das reviews
coletadas nem é bloqueada por elas ([F] usa título/ano derivados do slug —
§3[F]). Uma falha em [F] nunca impede [D]/[D2]/[E] de rodar, e vice-versa: as
fontes de dados são independentes.

**[G] é a única exceção à independência total:** o narrador [D2] *lê* a
distribuição quando ela existe, para escolher a variante da regra (c). Mas a
dependência é **opcional por construção** — ausência de [G] não é erro, é o
caminho de fallback (regras da v1.2.1), e nenhum outro estágio muda.

### [A] Resolução de slug
Busca via o endpoint AJAX `letterboxd.com/s/search/films/<query>/` (**corrigido na Fase 1** — a URL humana `letterboxd.com/search/films/<query>/` é um shell React vazio no HTML estático; ver §2.1); apresentar os top resultados (título + ano) e pedir confirmação do usuário quando houver ambiguidade. Se o usuário passar o slug diretamente (flag `--slug`), pular a busca.

### [C1] Alocação proporcional ao histograma (v1.9.0) — define o alvo, não o filtro

Dentro de cada bucket, as vagas são distribuídas segundo o **histograma real
daquele filme**, em vez de cota igual por nível:

```
n(nível L) = max(piso_nivel, round(N_bucket × contagem(L) / contagem_do_bucket))
```

com `N_bucket = 40` (§2), `piso_nivel = 2` (§2, arbitrário e calibrável), e o
piso aplicado **só a níveis com material** (`contagem(L) > 0`). Níveis ausentes
do histograma recebem 0 e não quebram a conta.

**Reconciliação para somar exatamente `N_bucket`** (o arredondamento e o piso
não fecham sozinhos): distribui-se por *maior resto* e, se o piso empurrar a
soma acima de `N_bucket`, corta-se dos níveis com **maior alocação acima do
piso**, sempre do maior para o menor, com desempate determinístico pelo nível
mais alto. Caso degenerado registrado: se `nº de níveis com material × piso_nivel
> N_bucket`, o piso é impossível de honrar para todos — a alocação então
distribui `N_bucket` o mais uniformemente possível e o piso é **relaxado**, não
violado em silêncio.

**Custo: zero requisições extras.** O endpoint de histograma já é chamado uma
vez por filme desde a v1.4.0 (§3[G]); a v1.9.0 só o executa **antes** da
coleta em vez de depois.

**Por que substituiu a cota igual por nível.** A cota de 10 por nível fazia
cada nível de estrela pesar o mesmo dentro do bucket, o que **super-representa
os extremos**: num filme com 456 notas de 0,5★ e 4.251 de 2,0★, ambos entravam
com 10 reviews — 0,5★ com 22× mais peso relativo do que tem na população. O
grupo "negativas" saía lido como mais raivoso do que é.

#### Duas ressalvas, declaradas

1. **O histograma mede NOTAS; a alocação distribui REVIEWS COM TEXTO.** São
   populações diferentes (a mesma distinção que a v1.4.1 registrou para o
   vocabulário do peso, §D2): nada garante que a proporção de quem *escreve*
   em cada nível seja a proporção de quem *avalia*. A alocação é uma
   **aproximação por proxy**, e está declarada como tal — não como medida.
   O proxy é usado porque é o único dado de forma da distribuição disponível
   sem gastar requisição, e porque é estritamente melhor que a alternativa que
   substituiu (cota igual, que é o proxy "todos os níveis são igualmente
   populosos" — falso em todo filme).
2. **A redistribuição de déficit muda a composição silenciosamente.** Quando um
   nível não completa a alocação (esgotou material ou bateu o teto de páginas),
   a sobra vai para os níveis do **mesmo bucket** com mais material disponível
   — o bucket fecha com `N` certo e composição **diferente da planejada**.
   *Mitigação obrigatória:* a telemetria registra a composição **ALVO** e a
   **ATINGIDA** por nível, **lado a lado** (§4). Um bucket que alcançou 40 por
   redistribuição não pode parecer igual a um que alcançou 40 como planejado.

**A redistribuição NUNCA aciona relaxamento na coleta.** Déficit é resolvido
puxando mais material de **outro nível do mesmo bucket**, jamais afrouxando
filtro ou paginando além do teto. Cascata de relaxamento é decisão de seleção
(§3[C2]), e continua sendo por nível.

### [B] Raspagem do SUPERSET por nível de nota

Para cada um dos 10 níveis (`rated/0.5/` … `rated/5/`), na ordenação do §2.3,
paginar e **persistir tudo o que vier** (§3[B']). Os filtros existem aqui com
uma função só: **decidir quando parar**.

**Condição de parada — dois motivos possíveis, DETERMINÍSTICA desde a v1.9.2:**

**(a) ORÇAMENTO — o orçamento de páginas do nível (derivado do orçamento por
BUCKET, ver abaixo) é sempre gasto INTEGRALMENTE**, salvo esgotamento real de
material. `motivo_parada = "orcamento_esgotado"`: o site provavelmente tem
mais conteúdo, mas o orçamento desta coleta acabou.

**(b) MATERIAL ESGOTADO — página além da última devolve 200 com lista vazia**
(§2.1). `motivo_parada = "material_esgotado"`: o nível está provadamente
completo — não há mais o que coletar ali, com QUALQUER orçamento.

> **v1.9.2 — a parada por ALVO (heurística, cota × folga) foi REMOVIDA.** Até
> a v1.9.1 havia um terceiro motivo, PISO/ALVO: parar cedo quando a contagem
> heurística de válidas (nota + sem spoiler + comprimento) alcançava a cota
> alocada com 25% de folga, mesmo com orçamento de páginas sobrando. Esse
> mecanismo fazia sentido quando o teto era por NÍVEL e o custo total por
> BUCKET não tinha limite (v1.9.0): parar cedo economizava requisição sem
> arriscar o bucket inteiro. Sob o orçamento por BUCKET da v1.9.1, ele virou
> **fonte de não-determinismo**: a heurística é otimista (mede texto visível,
> antes da cascata precisa e da re-checagem de spoiler — §3[B], "Orçamento de
> páginas"), então pode julgar "material suficiente" e parar de paginar
> exatamente no ponto em que, na prática, o rendimento real cairia abaixo da
> cota — foi o mecanismo EXATO por trás do 37/40 residual de `cidade-de-deus`
> na v1.9.1 (nível 2,5★ parou na página 3 por ALVO, com 3 páginas de
> orçamento ainda disponíveis; a página 4 nunca foi buscada). Removê-la
> significa que o orçamento de páginas passa a ser a ÚNICA variável que
> controla quanto se coleta — o resultado de uma coleta com o mesmo orçamento
> é sempre o mesmo, o que é pré-requisito para planejar o custo de um lote de
> 30-50 filmes com confiança.
>
> **Custo aceito e medido:** mais páginas por filme (o orçamento que antes
> podia parar cedo agora é sempre gasto) — ver "Resultado MEDIDO da recoleta
> v1.9.2" abaixo para os números reais. `FOLGA_ALVO_COLETA` (1,25) e a
> heurística de contagem continuam existindo, mas com escopo REDUZIDO: só
> decidem o orçamento do completamento [C'] (quantas truncadas resolver),
> nunca mais quando parar de paginar.
>
> **O piso de páginas por nível (v1.9.0, §2.2 Risco 3) não desaparece — muda
> de mecanismo.** Ele existia para garantir que todo nível com material fosse
> raspado ao menos 1 vez, mesmo com alocação de reviews zero (o seguro de
> reversibilidade da fronteira). Essa garantia já vinha, desde a v1.9.1, do
> PISO DA ALOCAÇÃO DE PÁGINAS (`orcamento_paginas_bucket`, piso=1 por nível
> com material) — não do parâmetro `piso_paginas` que gatilhava o ALVO. Com o
> ALVO removido, esse parâmetro fica sem função e é revogado (§2); a garantia
> de reversibilidade continua de pé, só que por um único caminho em vez de
> dois.

#### Orçamento de páginas POR BUCKET (v1.9.1) — corrige o defeito estrutural da v1.9.0

**O defeito, como a v1.9.0 o deixou registrado:** o teto de páginas era **por
NÍVEL** (4, flat) enquanto a cota de análise é **por BUCKET** (40). Sob a
opção C, `medianas` tem **2 níveis** contra **4** dos outros dois buckets — seu
teto AGREGADO de páginas era `2 × 4 = 8`, metade do teto agregado de
`negativas`/`positivas` (`4 × 4 = 16`). Era uma mistura de unidades, não falta
de material: o bucket nunca tinha orçamento de página suficiente para tentar
chegar a 40, não importa quanto material existisse no Letterboxd. Medido nos
3 filmes da recoleta v1.9.0: `medianas` fechou 35, 23 e 26 — nunca 40;
`negativas`/`positivas` fecharam 40 sempre.

**A correção:** o teto deixa de ser uma constante fixa por nível e passa a ser
**um orçamento por BUCKET** (`ORCAMENTO_PAGINAS_POR_BUCKET = 16`, igual para os
três — não depende do número de níveis), distribuído entre os níveis daquele
bucket **na mesma proporção do histograma já usada para a alocação de reviews**
(§3[C1]) — não é uma segunda fórmula: é a função `alocar_bucket` reaproveitada,
agora recebendo o orçamento de páginas em vez da cota de reviews como `N`:

```
paginas(nível L) = alocar_bucket(orcamento_bucket=16, histograma, niveis_do_bucket, piso_nivel=1)
```

com dois ajustes sobre o resultado:

- **piso de 1 página por nível com material** — o MESMO seguro de
  reversibilidade da fronteira (§2.2, Risco 3), agora expresso na alocação de
  páginas em vez de numa constante solta;
- **teto de segurança de 10 páginas num único nível** (`TETO_SEGURANCA_PAGINAS_NIVEL
  = 10`) — sem ele, um bucket de 2 níveis muito desbalanceado no histograma
  (ex.: `medianas` de `cidade-de-deus`, onde 3,0★ tem 85% do bucket) daria a
  esse nível sozinho quase o orçamento inteiro, deixando o outro nível do
  bucket com quase nada. O excedente cortado pelo teto é **redistribuído para
  os outros níveis do mesmo bucket** — literalmente `redistribuir_deficit`
  (§3[C1]) chamada de novo, com a "disponibilidade" sendo o teto de segurança
  em vez da contagem de material: **nenhum mecanismo novo de redistribuição
  foi escrito**, o mesmo já existente é reaproveitado com um `disponivel`
  diferente.

**Garantia:** a soma de páginas nunca excede o orçamento do bucket; pode ficar
**abaixo** dele só no caso degenerado de um bucket com um único nível
(nada para redistribuir o excedente do teto de segurança) — caso raro sob a
opção C (nenhum bucket tem 1 nível só), coberto em teste por completude.

**Por que 16, e por que a razão importa mais que o número:** `16 = 4 × 4`, o
mesmo teto agregado que `negativas`/`positivas` já tinham sob a v1.9.0 (4
páginas × 4 níveis). O orçamento não SOBE para os buckets de 4 níveis — ele
**equaliza** o teto agregado que `medianas` (2 níveis) tinha pela metade. É a
correção mínima que fecha a lacuna sem tocar em fronteira, cota ou piso
escalonado, as três decisões que a v1.9.0 já havia congelado e que o registro
do defeito explicitamente preservou para decisão humana separada.

#### Posicionamento estratificado por profundidade (v1.9.2)

**O defeito que corrige:** as páginas de um nível eram sempre as primeiras `N`
consecutivas. Sob `by/added` (cronológica, mais recentes primeiro, §2.3), isso
amostra sistematicamente as reviews MAIS RECENTES — a v1.9.0 mediu 79-100% da
amostra numa janela de ~7 semanas. Para um filme de catálogo como `cure`
(1997), a análise passa a caracterizar a coorte que descobriu o filme
recentemente, não a recepção do filme ao longo da vida dele.

**A correção não muda QUANTAS páginas são buscadas — muda QUAIS.** O
orçamento de páginas por nível é dividido em dois blocos:

```
n_raso    = orçamento − n_profundo
n_profundo = round(orçamento × RESERVA_PROFUNDIDADE)     # RESERVA_PROFUNDIDADE = 0,25
```

- **bloco raso** — posições `1..n_raso`, consecutivas, igual a antes;
- **bloco profundo** — até `n_profundo` posições em **progressão geométrica**
  a partir do FIM do bloco raso: `n_raso+2, n_raso+4, n_raso+8, n_raso+16, …`
  (dobra a cada termo). Cresce rápido de propósito: com um orçamento pequeno
  de posições profundas, cobrir uma faixa ampla da profundidade real exige
  saltos grandes, não uma amostra densa perto do início do bloco raso.

**Descoberta e redistribuição, sem custo extra.** A profundidade real de um
nível não é conhecida a priori (§3[B], gate da v1.9.1: sem numeração de
página no HTML). As posições profundas são buscadas em ordem CRESCENTE de
offset; a primeira que devolver página vazia revela que a profundidade real
fica **abaixo** dela — e as posições profundas maiores, ainda não tentadas
(agora sabidamente vazias, por monotonicidade da paginação: se a página `K`
está vazia, toda página `> K` também está), NÃO são buscadas. O orçamento
que sobra dessas posições descartadas é redistribuído para dentro do
**intervalo já confirmado como válido** — todo posição `≤` à maior posição
profunda **efetivamente buscada com sucesso** (não à posição vazia, nem a
qualquer coisa além dela: só o que já foi provado ter conteúdo, por
monotonicidade na direção oposta — se a página `P` tem conteúdo, toda
página `< P` também tem). Isso garante **no máximo 1 página desperdiçada por
nível** — a que revelou a profundidade — e nenhuma aposta arriscada em
território desconhecido.

**A redistribuição REAPROVEITA `redistribuir_deficit` — não é um mecanismo
novo.** As posições candidatas (as geométricas originais + posições dentro
do intervalo confirmado ainda não buscadas) entram como o "nível" da função;
`alocacao` é o que se queria originalmente (1 por posição geométrica),
`disponivel` é 1 para toda posição dentro do intervalo confirmado e 0 para
o resto — a mesma função que já redistribui déficit de reviews entre níveis
de um bucket (§3[C1]) e déficit de páginas entre níveis (v1.9.1, acima),
agora aplicada a POSIÇÕES DENTRO de um nível. Três usos, uma implementação.

**Custo: IGUAL ao consecutivo no caso comum; NUNCA maior, em qualquer caso.**
Quando a profundidade real cobre todas as posições tentadas (o caso
DOMINANTE — é justamente o material populoso que justifica gastar reserva
profunda), o total é exatamente `n_raso + n_profundo` = o orçamento, igual
ao esquema consecutivo. **Ressalva honesta, no caso de fronteira exata:** o
backfill só usa posições JÁ CONFIRMADAS (nunca aposta em território
desconhecido, para preservar a garantia de ≤1 desperdício) — se a
profundidade real cai DENTRO de um salto geométrico ainda não coberto por
nenhuma posição confirmada (ex.: confirmado até `n_raso+2`, a profundidade
real é `n_raso+3`, mas a próxima tentativa geométrica é `n_raso+4` e vem
vazia), esse conteúdo real específico fica **fora do backfill** — o
orçamento correspondente simplesmente não é gasto nesse nível, em vez de
arriscar uma segunda página vazia para persegui-lo. **Nunca mais caro que o
consecutivo; igual sempre que há posições confirmadas suficientes para
preencher a reserva (o caso comum); pode ficar levemente ABAIXO do
consecutivo no caso de fronteira, deixando uma fração pequena e real do
conteúdo fora — aceito em troca da garantia de custo previsível.** Testado
explicitamente (`tests/test_posicionamento.py`): igualdade exata no caso
comum (profundidade folgada); nunca excede o orçamento em nenhum caso.

**Degrada para consecutivo quando o nível é raso.** Se a profundidade real
do nível é menor que `n_raso`, o bloco raso já esgota o material (página
vazia dentro dele) e o bloco profundo nunca é tentado — mesmo comportamento
de sempre, sem código especial: a checagem de esgotamento roda ANTES da fase
profunda, e material esgotado na fase rasa pula a fase profunda inteira.

**Reversibilidade — por que esta é a última peça que faltava (v1.9.2).**
Fronteira (§2.2), cota (§0) e filtro (§3[C2]) já eram parâmetros aplicados
DOWNSTREAM sobre o bruto persistido — mudar qualquer um deles não custa
requisição. A profundidade de paginação era a exceção: página não baixada
não está no bruto, e não tem como um parâmetro downstream trazê-la de volta.
Com raso e profundo no MESMO bruto, "analisar só o material recente" ou
"analisar tudo, incluindo o profundo" também vira parâmetro filtrável por
`pagina_origem` na seleção (§3[C2]) — não implementado nesta sessão (fora do
escopo: a seleção continua escolhendo por `(pagina_origem, ordem no jsonl)`,
sem filtro de profundidade), mas agora POSSÍVEL sem recoleta. Sem isto, a
janela temporal ficaria gravada no bruto de forma irreversível, e corrigi-la
exigiria recoletar os 30-50 filmes do lote inteiro depois de já publicados.

#### Resultado MEDIDO da primeira recoleta, v1.9.0 (2026-08-07) — o defeito ANTES da correção

Recoleta ao vivo dos 3 filmes do catálogo, sob `by/added`, teto 4, cota 40:

| Filme | requisições | páginas | bruto | níveis no teto | negativas | medianas | positivas |
|---|---|---|---|---|---|---|---|
| `cure` | **65** | 32 | 384 | 3 | 39/40 | **35/40** | 40/40 |
| `cidade-de-deus` | **61** | 32 | 384 | 4 | 40/40 | **23/40** | 40/40 |
| `the-invite-2026` | **58** | 33 | 396 | 4 | 40/40 | **26/40** | 40/40 |

**DEFEITO ESTRUTURAL — `medianas` não consegue fechar a cota, e a causa é
aritmética, não de material.** O bucket do meio tem **2 níveis** sob a opção
C; os outros dois têm 4. Com teto de 4 páginas e ~12 reviews por página, o
material bruto máximo de um bucket é `nº de níveis × 4 × 12`:

| Bucket | níveis | bruto máximo | válidas a 27% (rendimento medido) |
|---|---|---|---|
| `negativas` / `positivas` | 4 | 192 | ~52 |
| **`medianas`** | **2** | **96** | **~26** |

Ou seja: **`medianas` topa em ~26 válidas e a cota de 40 é inalcançável por
construção** — não por falta de reviews no Letterboxd, mas porque o teto de
páginas é POR NÍVEL e o bucket do meio tem metade dos níveis. Foi o que
aconteceu nos 3 filmes (35, 23 e 26), e vai acontecer em todo filme.

Isto é uma **interação não prevista** entre três decisões desta versão que
foram tomadas separadamente: a fronteira 4/2/4 (§2.2), a cota igual 40/40/40
(§0) e o teto de 4 páginas por nível (§3[B]). Cada uma é defensável sozinha;
juntas, tornam um terço da promessa "profundidade igual" impossível de
cumprir.

**Não corrigido nesta versão** — corrigir exigiria mexer numa das três
decisões que a v1.9.0 acabou de congelar, e a escolha entre elas merece uma
decisão explícita e não uma correção de rodapé. Registrado como o **candidato
número 1 da próxima versão**, com quatro saídas conhecidas:
1. **orçamento de páginas por BUCKET** em vez de por nível (`4 × nº de níveis`,
   redistribuível internamente) — corrige a assimetria na raiz e não muda
   fronteira nem cota; custo: até +8 páginas/filme só no bucket do meio;
2. **teto de volta a 6** globalmente — custo: até +20 páginas/filme, e ainda
   assim `medianas` chegaria a ~39, no limite;
3. **aceitar** e deixar o piso escalonado reportar — hoje `medianas` fecha em
   23-35, que é `completa` (≥15) nos 3 filmes; a precisão em `n=26` é ±9,8pp
   (1 EP) / ±19,2pp (95%), pior que a de 40 mas dentro da mesma ordem;
4. **fronteira com 3 níveis no meio** — reabre §2.2, que acabou de ser
   decidida com base semântica.

5. **baixar `min_chars`** — medido: com `min_chars=50`, os **três** buckets
   fecham 40/40/40 nos **três** filmes, a partir do MESMO bruto e sem nenhuma
   requisição. Ou seja, o material existe; o que não passa é o filtro de
   comprimento. Trocaria profundidade de texto por contagem, o que é uma
   decisão de qualidade de análise e não de coleta — por isso não é a saída
   default, mas é a mais barata de todas.

A opção 3 é o comportamento em vigor, por omissão: nada quebra, os três
buckets ficam `completa`, e a telemetria mostra a diferença em vez de
escondê-la.

**Confirmação do diagnóstico (reseleção offline, 0 requisições):** rodando a
seleção sobre o mesmo bruto **sob as fronteiras HISTÓRICAS** (3 níveis em
`positivas`, 2 em `medianas`, 5 em `negativas`), quem passa a ficar curto é
**`positivas`** — 36/40 em `cidade-de-deus` e em `the-invite-2026` —, enquanto
`negativas` (5 níveis) fecha 40 em todos. O déficit acompanha o **número de
níveis do bucket**, exatamente como a aritmética prevê, e não a faixa de nota.
É a prova de que o defeito é do teto-por-nível, não da opção C.

**Orçamento de requisições, MEDIDO:** 58-65 por filme (média 61), dos quais
32-33 de paginação, 24-33 de completamento e 1 de histograma. Para comparação,
sob a v1.8.2 o `cure` custou **83** e o `cidade-de-deus` **68** — a v1.9.0
custa **menos** apesar de coletar ~50% mais material bruto (384 vs. 252 no
`cure`), porque o orçamento de completamento cortou a parte cara. A estimativa
de "~45" feita antes desta medição estava otimista, como se previa.

#### Resultado MEDIDO da recoleta v1.9.1 (2026-08-07) — depois da correção

Recoleta ao vivo (incremental sobre o bruto da v1.9.0), sob o orçamento por
bucket (16 páginas, teto de segurança 10/nível):

| Filme | requisições de rede | negativas | medianas | positivas |
|---|---|---|---|---|
| `cure` | **17** | 40/40 | **40/40** | 40/40 |
| `cidade-de-deus` | **26** | 40/40 | **37/40** | 40/40 |
| `the-invite-2026` | **20** | 40/40 | **40/40** | 40/40 |

**O defeito fecha em 2 dos 3 filmes, melhora substancialmente no terceiro.**
`medianas` foi de 35→**40**, 26→**40**, 23→**37** — de 3/3 buckets abaixo da
cota para 8/9 buckets no total, e 2/3 filmes com os TRÊS buckets em 40/40/40.

**`cidade-de-deus`/`medianas` ficou 3 abaixo — causa identificada, e NÃO é o
mesmo defeito.** O nível 2,5★ recebeu orçamento de 6 páginas mas usou só 3
(confirmado: página 4 nunca foi buscada, `resultado/cache/cidade-de-deus/
pages/by_added/rated_2_5_page_4.html` não existe) — a condição de parada
**ALVO** (§3[B], degrau b: cota alocada × 1,25 de folga, contada por
heurística) foi satisfeita antes de esgotar o orçamento de páginas. O alvo
de reviews para 2,5★ nesse bucket é 6 (com folga, 8); a heurística julgou
ter material suficiente na página 3, mas parte não sobreviveu ao filtro real
(cascata precisa, exclusão de spoiler) — e o nível 3,0★ (que bateu o teto de
10 páginas) não teve material extra para cobrir a diferença via
redistribuição. **Este é o mecanismo de folga da v1.9.0, inalterado nesta
sessão** (fora de escopo — a lista de "não tocar" desta sessão inclui `cota`
mas a folga é parte do coletor, não da cota em si; ajustá-la não foi pedido).
Registrado como achado residual, candidato a próxima sessão se o padrão se
repetir em mais filmes.

**Requisições: 17-26 por filme (execução incremental), média 21** — bem
abaixo da média de 61 da v1.9.0, porque a maior parte do material já estava
persistida da recoleta anterior; só o incremento (páginas novas dentro do
orçamento maior) gerou requisições reais. **Não é comparável 1:1 com os 61
da v1.9.0** (que foi coleta do zero) — é o custo real medido de ALARGAR uma
coleta já existente, que é o caso de uso que a incrementalidade do bruto
(§3[B']) foi desenhada para servir.

**Motivos de descarte, agregados nos 3 filmes:** `abaixo_min_chars` domina
com folga (~65-70% dos descartes em todo bucket) — confirma que `min_chars`
é o filtro que mais custa rendimento, como já indicado pela saída "baixar
min_chars" de §3[B] (não aplicada, apenas registrada). `excedente_cota`
(material que passaria em tudo mas não coube) aparece em quase todo
bucket — sinal de que o bruto tem folga além do que a cota consome.
`spoiler` e `truncada_sem_texto` são marginais (poucas unidades por
bucket). `duplicata`/`outros`: **zero em todos os filmes/buckets/níveis** —
a garantia de dedupe do bruto se sustenta sob dado real.

**Janela temporal, medida (entrega 4) — confirma o achado do gate.** Os
percentis mudam MUITO mais do que os extremos brutos sugerem: `cure`
positivas tem `min=2023-12-06` mas `p5=2026-08-04` — 95% da amostra desse
bucket está dentro de 3 dias, apesar do extremo de quase 3 anos atrás. É a
prova, em dado real e não sintético, do achado do gate (§3[B]): min/max é
dominado por outlier, a mediana e os percentis são a leitura honesta de onde
a amostra realmente está.

#### Resultado MEDIDO da recoleta v1.9.2 (2026-08-07) — parada determinística + posicionamento estratificado

Recoleta incremental (sobre o bruto da v1.9.1), sob a parada determinística
(entrega 1) e o posicionamento estratificado (entrega 2):

| Filme | requisições de rede | negativas | medianas | positivas |
|---|---|---|---|---|
| `cure` | **15** | 40/40 | 40/40 | 40/40 |
| `cidade-de-deus` | **15** | 40/40 | **40/40** | 40/40 |
| `the-invite-2026` | **13** | 40/40 | 40/40 | 40/40 |

**O DÉFICIT RESIDUAL DA v1.9.1 FECHOU.** `cidade-de-deus`/`medianas`, que
tinha ficado em 37/40 (o nível 2,5★ parando cedo por ALVO antes de esgotar
o orçamento), agora fecha **40/40** — exatamente a correção prevista ao
remover a parada heurística. **Os 3 filmes, os 9 buckets, todos em 40/40 —
a primeira vez desde a v1.9.0 que isso acontece nos três simultaneamente.**

**`motivo_parada` por nível: 100% `orcamento_esgotado`, nos 3 filmes, em
todos os 10 níveis de cada um** (30 valores no total, nenhum
`material_esgotado`) — os 3 filmes do catálogo têm material de sobra em
todo nível, então o orçamento (16/bucket) foi o fator limitante em toda
parte, nunca o conteúdo real do Letterboxd. Consistente com o achado da
Entrega 3 (filmes populares raramente esgotam organicamente).

**Requisições: 13-15 por filme, média 14,3** — abaixo da execução incremental
da v1.9.1 (~21), porque grande parte do bloco raso já estava cacheada;
o custo novo concentrou-se nas posições PROFUNDAS (nunca visitadas antes).
Não comparável ao valor esperado de coleta do zero (~85, §5.6) pelo mesmo
motivo já registrado nas sessões anteriores: incremental reaproveita cache.

**Distribuição de `pagina_origem` (entrega 4) — a primeira medição real do
posicionamento estratificado.** `fracao_profunda` variou de **0,00 a 0,23**
entre buckets — no `the-invite-2026`/negativas, **23% da amostra final veio
do bloco profundo**, contribuição real e mensurável à diversidade temporal
da amostra. Em buckets com material abundante (`cure`/positivas), a fração
profunda ficou em 0 — o bloco raso já basta para fechar a cota, e a seleção
(ainda ordenada por `pagina_origem` ascendente, §3[B], "Reversibilidade")
não precisa alcançar o material profundo. **Confirma a hipótese registrada
durante a implementação (Entrega 4, commit [2/6]):** o benefício do
posicionamento estratificado na amostra FINAL depende de quão escasso é o
material raso — não é automático, é condicional à disponibilidade.

**Janela por `data` (secundária)** segue reportada lado a lado — sem
mudança de leitura em relação à v1.9.1 (ainda concentrada nos últimos
meses/dias em todos os buckets), confirmando que `pagina_origem` e `data`
medem coisas relacionadas mas distintas: a amostra ficou mais profunda em
RANK DE ADIÇÃO sem necessariamente recuar em CALENDÁRIO — o que é esperado
sob `by/added`, onde adições recentes concentram-se numa janela curta e
"profundo" ainda significa, na maioria dos casos, "há algumas semanas", não
"há anos".

#### Medição de profundidade de paginação (v1.9.1, GATE — passo largo NÃO implementado)

A v1.9.0 mediu que 79-100% da amostra de cada filme vem de uma janela de ~7
semanas (viés de recência, §2.3) — para um filme de catálogo como `cure`
(1997), a análise passa a descrever quem descobre o filme AGORA. A correção
candidata é **paginação de PASSO LARGO**: em vez das páginas `1..N`
consecutivas, amostrar `N` páginas espalhadas pela profundidade total
disponível — mesmo número de requisições, cobertura temporal inteira.

**Esta subseção é MEDIÇÃO, não implementação.** Nada do coletor de produção
mudou por causa dela. Metodologia e dado completo em
`scripts/medicao_profundidade_v191.py` (nível 4,0★, `by/added`, os 3 filmes);
respostas às quatro perguntas do gate:

**(a) A profundidade é conhecível a partir da página 1 (ou de outra forma
barata)? NÃO.** O HTML de listagem do Letterboxd usa um widget simples
"Newer/Older" — sem contagem total de páginas, sem numeração, sem link para a
última página, confirmado nos 3 filmes. Uma estimativa por PROXY foi testada
(total de reviews do filme, do nav — já presente em toda página, custo zero —
× participação do nível no histograma ÷ 12/página) e **superestimou a
profundidade real em 11,6×–27,2×** — a maioria das notas não vem acompanhada
de texto, e essa proporção não é uniforme por nível nem ao longo do tempo, o
que torna o proxy inútil para planejar índices de página. A única forma
CONFIÁVEL encontrada foi **sonda exponencial** (dobrar a página até achar uma
vazia): ~10 requisições de rede por nível para um limite confiável, medido nos
3 filmes.

**Achado lateral, não pedido mas relevante para a decisão:** a sonda parou
EXATAMENTE no mesmo intervalo (última não-vazia 256, primeira vazia 512) nos
3 filmes — coincidência grande demais para ser orgânica. Uma busca binária
sobre o `cure` fechou o limite exato: **página 256 tem conteúdo, página 257
não tem** (confirmado por contagem real de reviews parseadas, não por
tamanho de arquivo — ver `resultado/cache/*/pages/by_added/rated_4_page_256.html`
vs. `_257.html`). `256 = 2⁸` é suspeito o bastante para ser um **teto
fixo do site**, não exaustão orgânica de conteúdo — hipótese reforçada por
níveis pouco populosos (ex. `cure` 0,5★, 456 notas) esgotarem naturalmente na
1ª página, muito antes de qualquer teto. **Não confirmado para outros
níveis/filmes** — testado só em `cure`/4,0★; registrado como pista, não fato
estabelecido.

**(b) Páginas profundas rendem reviews normais? SIM.** Contagem de válidas
(≥150 chars) e comprimento médio em páginas a 50%/75%/95% da profundidade
sondada ficaram na MESMA ordem de grandeza das páginas rasas (1-4), nos 3
filmes — sem degradação sistemática de rendimento ou de comprimento à medida
que se pagina mais fundo.

**(c) Qual a janela temporal do passo largo, contra a atual de ~7 semanas?
MISTO — mais complexo do que a hipótese previa, e por um motivo já registrado
na v1.9.0.** Comparando a janela `min↔max` das páginas 1-4 (atual) contra uma
amostra de passo largo (páginas 1, ~33%, ~66%, 100% da profundidade sondada):

| Filme | atual (pág. 1-4) | passo largo | resultado |
|---|---|---|---|
| `cure` | 2026-08-05 → 2026-08-07 (2 dias) | 2026-04-01 → 2026-08-07 (~4 meses) | **confirma a hipótese** |
| `cidade-de-deus` | 2025-11-29 → 2026-08-07 (~8 meses) | 2026-05-19 → 2026-08-07 (~2,5 meses) | **janela mais ESTREITA** |
| `the-invite-2026` | 2026-07-08 → 2026-08-07 (~1 mês) | 2026-07-28 → 2026-08-06 (~9 dias) | **janela mais ESTREITA** |

Em 2 dos 3 filmes o passo largo **estreitou** a janela medida por
`min`/`max` — o oposto do esperado. **Causa provável, já registrada na
v1.9.0:** `data` é a data ASSISTIDA (diário), não a de publicação da review;
alguém pode postar HOJE uma review de um rewatch antigo, produzindo um
outlier de data velha em QUALQUER posição da sequência `by/added` — inclusive
nas páginas 1-4. `min`/`max` sobre uma janela pequena é dominado pelo
outlier mais extremo que ela contém, não pela distribuição real. **Esta
medição é evidência a favor da Entrega 4** (percentis p5/50/95 em vez de só
min/max): a métrica certa para avaliar cobertura temporal não é o extremo,
é a distribuição.

**(d) O custo em requisições muda? O briefing previu que não — a medição diz
que SIM, seria mais caro, a menos que o achado do item (a) se confirme.**
Esta MEDIÇÃO gastou ~11 requisições novas de rede por filme (a maior parte já
estava em cache da coleta anterior). Um coletor de PRODUÇÃO com passo largo
precisaria de alguma forma barata de saber a profundidade ANTES de escolher
os índices de página a amostrar — e a única forma confiável encontrada (sonda
exponencial, ~10 req./nível) seria um custo NOVO, pago em TODA coleta, que a
paginação sequencial atual não paga. Isso inverteria o ganho: passo largo
resolveria o viés de recência mas pioraria o orçamento de requisições que a
v1.9.0 acabou de medir e otimizar. **A única saída que preserva "custo não
muda" é o teto fixo do achado lateral (a) se confirmar** — um valor constante
(256) não precisa de sonda, dispensa completamente esse custo. Mas isso
depende de uma verificação mais ampla (mais níveis, mais filmes) que esta
sessão não fez.

**GATE — decisão tomada na v1.9.2, ver abaixo.** O passo largo (amostra
regular por toda a profundidade) continua NÃO implementado — a v1.9.2
implementa **posicionamento estratificado** (acima), que é uma resposta
diferente e mais barata ao mesmo problema: não precisa conhecer a
profundidade a priori (a reserva geométrica descobre e se adapta, custando
no máximo 1 página por nível), então o argumento "custo não muda só se o
teto de 256 se confirmar" deixou de ser bloqueante.

#### Confirmação do teto de 256 páginas (v1.9.2, Entrega 3) — RESULTADO MEDIDO

Medido em `the-room-1993` — **890 notas no total** (`collect_distribuicao`),
um filme genuinamente obscuro (não confundir com o "The Room" de 2003; é um
título homônimo de 1993 quase sem audiência). Nível mais populoso: **3,0★,
249 notas** — o testado, sob `by/added` (mesma ordenação da sondagem v1.9.1).

Sonda exponencial (`1, 2, 4, 8`) + busca binária de refinamento, **6
requisições no total**:

```
página 1: 12 reviews    página 2: 12 reviews    página 4: 2 reviews
página 8: 0 reviews (limite superior)
página 6: 0 reviews     página 5: 0 reviews
→ última página não-vazia = 4; primeira vazia = 5
```

**Resultado: a profundidade foi determinada pelo CONTEÚDO REAL do filme, não
por um teto do site.** A última página com conteúdo é a **4**, muitíssimo
abaixo de 256 — confirma a hipótese: um filme obscuro esgota organicamente
muito antes de qualquer teto de plataforma, enquanto os 3 filmes populares
da v1.9.1 bateram EXATAMENTE no mesmo ponto (256/512) apesar de terem
volumes de notas completamente diferentes entre si (120 mil a 1,2 milhão) —
um padrão que só faz sentido como limite do SITE, não como coincidência de
conteúdo. **O achado lateral da v1.9.1 fica CONFIRMADO** (ainda que só para
os 4 níveis testados até agora, não generalizado para toda a plataforma):
Letterboxd aparenta impor um teto de paginação por volta de 256 páginas para
listagens populosas, e filmes obscuros nunca chegam perto dele.

**Consequência para o posicionamento estratificado:** nenhuma, como previsto
— o algoritmo de descoberta (acima) não assume o valor 256 em nenhum ponto;
funciona igual, e com o mesmo custo, seja a profundidade real do nível 4
páginas (`the-room-1993`) ou 256 (os filmes populares da v1.9.1). Esta
medição completa o registro do achado da v1.9.1; não foi bloqueante para o
posicionamento estratificado, que já estava implementado sem depender dela.

**Cache:** por filme+nível+página (e por texto completo, ver C'), em disco.
Nunca rebuscar página cacheada. Cache não expira. **A chave de cache inclui a
ordenação** (v1.9.0) — trocar de ordenação é uma amostra diferente, e servir a
antiga do cache seria um erro silencioso.

### [B'] Persistência do bruto (v1.9.0) — o artefato que desacopla

**Layout:**

```
dados/bruto/<slug>/meta.json
dados/bruto/<slug>/reviews.jsonl
```

**`meta.json`:** `slug`, `coletado_em` (ISO 8601), `versao_coletor`,
`ordenacao_usada`, `histograma_bruto` (contagem por nível, os 10 níveis),
`paginas_gastas_por_nivel`, `paradas_por_limite` (lista de níveis que pararam
no teto), `contagem_bruta_por_nivel`, `contagem_estimada_valida_por_nivel`,
**(v1.9.1)** `orcamento_paginas_por_nivel` (o orçamento QUE FOI dado a cada
nível, derivado do orçamento por bucket — §3[B] — distinto de
`paginas_gastas_por_nivel`, que é o QUANTO foi de fato usado; a razão entre os
dois é a mesma composição-alvo-vs-atingida que §3[C1] já exige para reviews,
agora também para páginas) e **(v1.9.1)** `janela_temporal` (§4).

**`reviews.jsonl`**, uma review por linha: `id`, `nivel` (0,5–5,0), `texto`,
`n_chars`, `spoiler_flag`, `pagina_origem`, `url`, `autor_hash`.

**Três campos ADICIONAIS ao formato pedido, e o porquê de cada um** — todos são
**propriedades da review**, nunca decisões de seleção, então respeitam o mesmo
princípio que exclui `passou_por_relaxamento` (abaixo):

- **`truncada`** (bool) — a review veio colapsada na listagem (detector
  `.collapsed-text`, §C'.1). Sem esse campo, a invariante de v1.1.0 **"texto
  truncado nunca chega ao LLM"** ficaria impossível de garantir a partir do
  bruto: `n_chars` de um texto truncado é o do trecho visível, e nada
  distinguiria "review curta" de "review longa cortada".
- **`texto_completo`** (bool) — `texto` é o texto integral (nunca foi truncada,
  ou o completamento resolveu). A seleção (§3[C2]) só considera elegível quem
  tem `texto_completo: true`; o resto entra em `n_indisponivel_truncamento`.
- **`data`** (ISO 8601, do `<time class="timestamp">`) — a data da review. É a
  **evidência** de que a ordenação escolhida (§2.3) é a que se acredita ser:
  sem ela, `ordenacao_usada` seria uma declaração inverificável a partir do
  próprio material coletado.

**O que NÃO é gravado no bruto: `passou_por_relaxamento`.** Relaxamento é uma
**decisão de seleção**, não uma propriedade da review — a mesma review é
"relaxada" ou não conforme o filtro que se aplique depois. Gravá-la no bruto
recolocaria no material coletado exatamente o tipo de decisão que esta versão
tirou de lá. É **derivada** no downstream a partir de `n_chars` e
`spoiler_flag`.

**Idempotente e incremental.** Recoletar um filme já coletado **não duplica
reviews** (dedupe por `id`; a linha nova sobrescreve a antiga do mesmo `id`,
para que um completamento resolvido numa execução posterior seja incorporado) e
**atualiza o `meta.json`**. Consequência desejada: coletas sucessivas
**acumulam** superset — trocar a ordenação e recoletar soma material em vez de
substituí-lo, e o `meta.json` registra a ordenação da execução mais recente.

**`dados/` é versionado** (ao contrário de `resultado/cache/`, que é
`.gitignore`d): o cache é HTML reconstruível e volumoso; o bruto é o **insumo
de análise** — pequeno, textual, e a coisa cuja recoleta esta versão existe
para evitar.

#### Distribuição de `pagina_origem` (v1.9.2) — instrumento temporal PRIMÁRIO

`janela_temporal` (abaixo) mede `data`, e `data` é a data ASSISTIDA (campo
de diário), não a de publicação da review — um usuário pode postar HOJE uma
review de um rewatch de anos atrás, produzindo um outlier de data velha em
QUALQUER posição da amostra. Foi essa contaminação que produziu o resultado
MISTO do gate da v1.9.1 (a janela por `data` ESTREITOU sob amostragem mais
profunda em 2 dos 3 filmes — o oposto do esperado).

`pagina_origem`, sob ordenação cronológica (`by/added`, §2.3), não tem essa
contaminação: é o **rank de adição** — a página 40 foi adicionada ao site
antes da página 1, sempre, por construção da ordenação, independente de
quando o AUTOR diz ter assistido. Não é uma data de calendário, mas é um
proxy de recência **sem o ruído** que compromete `data`.

**Telemetria primária** (`distribuicao_pagina_origem`, por bucket, sobre a
amostra SELECIONADA — não o bruto inteiro): `{n, min, max, p5, p50, p95,
fracao_profunda}`, onde `fracao_profunda` é a fração da amostra cujo
`pagina_origem` cai no BLOCO PROFUNDO do respectivo nível (posicionamento
estratificado, acima) — calculada com a mesma divisão raso/profundo
(`RESERVA_PROFUNDIDADE`) usada na coleta, para que telemetria e coleta nunca
divirjam sobre o que conta como "profundo". Espelhada no bloco `coleta` do
resultado.

#### Janela temporal (v1.9.1) — SECUNDÁRIA desde a v1.9.2, proxy contaminado

**Rebaixada a secundária na v1.9.2** — mantida como telemetria (é dado real e
o problema que motivou §2.3 continua relevante), mas o instrumento PRIMÁRIO
de "onde a amostra está no tempo" passa a ser `pagina_origem` (acima), livre
da contaminação de data assistida vs. data de publicação que produziu o
resultado misto do gate. `janela_temporal` fica no JSON com o rótulo
explícito de proxy contaminado — não removida, porque continua sendo o único
sinal de CALENDÁRIO (ano/mês real) que o pipeline tem; `pagina_origem` diz
"quão fundo", não "quando".

A medição da v1.9.0 (§2.3) achou que 79-100% da amostra de cada filme vem de
uma janela de ~7 semanas; a medição de profundidade desta versão (§3[B], gate)
achou que `min`/`max` sozinhos são enganosos (dominados por outliers de data
assistida antiga). A correção nos dois achados é a mesma: gravar a
**distribuição**, não só os extremos.

`meta.json` ganha o campo `janela_temporal`: `{"total": {...}, "por_bucket":
{"negativas": {...}, "medianas": {...}, "positivas": {...}}}`, cada bloco no
formato `{"n", "min", "max", "p5", "p50", "p95"}` — datas truncadas para
`YYYY-MM-DD` (o campo `data` mistura formatos com e sem hora, §3[B']; a hora
não importa para janela). `p50` é a mediana: uma leitura muito mais honesta de
"quando a amostra realmente está" do que o extremo mais velho. Bordas: 1
review → os 5 campos de data são a mesma data; todas as reviews na mesma data
→ idem.

**A computação é bucket-aware, mas o módulo de persistência não é.** O bruto
(`bruto.py`, `collector.py`) continua sem saber onde ficam as fronteiras — a
função pura que calcula min/max/percentis de uma lista de datas vive em
`bruto.py` (opera sobre qualquer lista de reviews que receba, sem embutir
fronteira nenhuma), mas quem agrupa por bucket antes de chamá-la é o
`pipeline.py`, que já é o único módulo que enxerga as duas camadas — o mesmo
padrão de `montar_buckets` (§3[C2]). O campo é escrito como uma atualização
posterior de `meta.json`, sem reescrever `reviews.jsonl`.

**Não exposto no frontend nesta sessão.** Como todo campo de `meta.json`, é
espelhado no bloco global `coleta` do JSON de resultado (§4, mesmo mecanismo
de auditoria da v1.9.0) — mas `frontend/js/filme.js` não lê `coleta` hoje, e
esta sessão não adiciona esse consumo. O dado existe para auditoria e para
decisões futuras (ex.: informar o passo largo do gate acima), não para exibir
ao usuário final.

### [H] Harness de lote (v1.9.3)

Infraestrutura para rodar [A]→[B'] (só COLETA, sem síntese) sobre uma lista
de filmes, não um só — o que a v1.9.2 fechou tecnicamente na camada de
coleta ainda exigia uma execução manual por filme. `src/espectro24/lote.py`;
racional curto porque é orquestração, não uma nova regra de negócio.

**Checkpoint em arquivo, não em memória.** Um `estado.json` (`dados/lote/
<nome>/estado.json`) registra, por slug: `status` (`pendente` /
`concluido` / `falhou`), motivo (se falhou) e timestamp. Escrito **após
cada filme**, não em lote ao final — um lote interrompido a qualquer
momento (rede, Ctrl-C, sono da máquina) retoma pulando todo slug já
`concluido`. A persistência do bruto (§3[B']) já era idempotente; o
checkpoint é o que falta para não RECOMEÇAR a decidir o que já foi feito.

**Validação de slug — 1 requisição, antes de gastar orçamento de páginas.**
Busca a listagem de reviews "qualquer nota" (`reviews_qualquer_nota_url`,
`/film/<slug>/reviews/by/activity/`) e reaproveita o `parser.parse_reviews`
já testado: 404/erro de rede → slug inválido, `FetchError`/`AntiBotError`
capturado e reportado como falha isolada, sem derrubar o lote; 200 sem
nenhuma review reconhecida pelo parser → tratado como falha de validação
(`sem_reviews`), pulando a coleta pesada.

**Achado real (v1.9.3, durante a Entrega 2):** a primeira versão desta
função buscava a página PRINCIPAL do filme (`film_page_url`, mesma usada
por `ficha.resolver_ano_letterboxd`) e casava um trecho de markup
(`js-route-reviews`, tooltip de contagem) contra ela — e falhou contra os
3 filmes reais testados (`parasite-2019`, `eighth-grade`,
`everything-everywhere-all-at-once`), todos marcados `sem_reviews`
incorretamente, porque essa tag só existe nas páginas de LISTAGEM de
reviews, não na página raiz do filme. Um detalhe de markup que as
fixtures sintéticas dos testes não capturavam (a fixture reproduzia a
mesma suposição errada). Corrigido para reusar o parser real de reviews
em vez de um regex ad-hoc — existência e presença de review verificadas
juntas, na mesma requisição, pelo mesmo código que a coleta de verdade
usa. Duas funções novas em `urls.py`: `reviews_qualquer_nota_url` e
`reviews_qualquer_nota_cache_key`.
`histograma` ausente **não** é motivo de rejeição aqui — o pipeline já
degrada esse caso graciosamente (alocação uniforme, §3[G]), então
pré-validar duas vezes a mesma coisa seria custo redundante, não segurança.

**Falha isolada.** Cada slug roda dentro de um `try/except` que cerca
TODO o pipeline de coleta daquele filme — qualquer exceção (rede, parsing,
markup inesperado) vira uma entrada `falhou` no checkpoint com o motivo, e
o loop segue para o próximo slug. Nenhuma exceção de um filme escapa para
derrubar o lote inteiro; a única exceção que ainda para tudo é
`AntiBotError` em `--offline=False` sem intenção de escalar (mesma política
de sempre, §restrições) — mas mesmo essa é registrada por slug antes de
propagar, para o resume saber onde parou.

**`material_esgotado` é CASO ESPERADO, não erro (§3[B]).** Um filme
obscuro esgotando material antes do orçamento não é uma falha do harness
— é o comportamento correto e já coberto pela persistência e pelo piso
escalonado (§3[C3]). Os 3 filmes do catálogo, sendo populares, nunca
exercitaram esse caminho em produção (só em teste sintético, §3[B]/§3[C3]):
o lote é a primeira vez que ele roda contra o Letterboxd real em escala, e
por isso os testes desta entrega verificam explicitamente que ele não
quebra nem a persistência, nem `montar_buckets`, nem a serialização do
JSON — um bucket em `sem_analise` é dado válido, não uma falha do harness.

**Log por filme.** Uma linha por nível durante a coleta (reaproveita o
`on_level` que `run_pipeline`/`collect_all_levels` já aceitam) e um
resumo por filme ao final de cada um — o lote roda por horas, e progresso
sem eco é indistinguível de travado.

**Fora do harness, deliberadamente:** paralelismo/concorrência (§2, delay
sequencial ≥2s continua valendo, filme a filme) e qualquer mudança de
parâmetro de coleta — o harness só ORQUESTRA a execução de [A]→[B'] já
existente, não modifica seu comportamento.

**Diagnose do déficit de buckets nos 3 filmes da Entrega 2 (v1.9.3,
2026-08-07, offline sobre o bruto já em disco — zero requisições).** O
relatório da Entrega 2 afirmou "os 3 fecharam 40/40/40" — **errado**,
contradizendo a própria tabela: só 5 dos 9 buckets atingem a cota cheia
de 40 (`parasite-2019` 28/40/32, `eighth-grade` 38/39/40,
`everything-everywhere-all-at-once` 40/40/40); os 9 fecham
`estado_piso=completa` (limiar n≥15, §3[C3]) — as duas afirmações não são
a mesma coisa, e a confusão entre elas foi o erro. Corrigido em §5.6.

Classificação dos 4 déficits (`parasite-2019`/negativas=28,
`parasite-2019`/positivas=32, `eighth-grade`/negativas=38,
`eighth-grade`/medianas=39), via `selecao.selecionar` reexecutado sobre o
bruto persistido:

- **`motivo_parada_por_nivel` = `orcamento_esgotado` em TODOS os 30
  níveis dos 3 filmes** — nenhum esgotou material organicamente;
  `paginas_gastas_por_nivel` == `orcamento_paginas_por_nivel` em todos.
- **Zero sondagem caindo em página vazia dentro do orçamento** — para
  cada nível, o número de `pagina_origem` distintos com review bate
  exatamente com `paginas_gastas`; toda página orçada retornou conteúdo
  real. Não há DESPERDÍCIO em nenhum dos 4 déficits.
- **Descarte dominado por `abaixo_min_chars`**, 63-87% do bruto de cada
  nível deficitário (ex.: `parasite-2019`/negativas nível 2,0★: 101/120;
  `parasite-2019`/positivas nível 5,0★: 78/96) — o filtro `MIN_CHARS=150`
  descarta reviews curtas. `deficit_redistribuido` (§3[C1]) ativou
  corretamente em todos os 4 (puxou excedente de níveis com sobra para os
  com falta, dentro do mesmo bucket) mas não bastou porque o BUCKET
  inteiro carecia de material elegível, não só um nível.
- **Hipótese de spoiler (`parasite-2019`/positivas, suspeita de
  reviravolta) REFUTADA.** Fração de `spoiler_flag=True` sobre o bruto
  por bucket, nos 6 filmes já coletados: 0,5%-4,9%, `parasite-2019` em
  2,1%-2,6% — dentro do mesmo intervalo dos outros 5 filmes (`cure`,
  aliás, tem a fração mais alta, 4,9% em `medianas`/`positivas`, e fechou
  40/40/40). Spoiler não explica um déficit de 20% da cota; a causa é
  `abaixo_min_chars`, não `spoiler`.
- **Comparação com o catálogo (`cure`/`cidade-de-deus`/`the-invite-2026`,
  os 3 fecham 40/40/40 nos 9 buckets):** a diferença não é volume bruto
  (`n_brutas` por nível é da mesma ordem de grandeza nos dois grupos) —
  é a FRAÇÃO que sobrevive ao filtro de 150 caracteres. No nível 2,0★ de
  `negativas`, o pool elegível pós-filtro foi ~12% do bruto em
  `parasite-2019` (14/120) contra ~36% em `cidade-de-deus` (43/120), quase
  3× de diferença. Estrutural, não ruído: filmes muito populares atraem
  um volume desproporcional de reviews curtas de reação rápida
  ("garbage", "meh"), diluindo o pool de texto substantivo (≥150 chars)
  amostrado dentro de um orçamento de páginas FIXO — o histograma de
  notas é enorme, mas isso não garante densidade de review LONGA na
  amostra. **Achado estrutural para o lote (registrado, não corrigido
  nesta sessão):** filmes populares (alto volume no Letterboxd) tendem a
  fechar buckets extremos (`negativas`/`positivas`) abaixo da cota mais
  do que filmes de nicho, mesmo com orçamento de páginas idêntico — o
  piso escalonado absorve isso corretamente (n≥15 ainda dá `completa`),
  mas a narrativa de um filme popular pode ter `n` menor que a de um
  filme obscuro do catálogo, contra a intuição.
- **Achado lateral, fora do escopo desta diagnose:** recolher os MESMOS 3
  filmes do zero duas vezes (a 1ª rodada de dados foi apagada por engano
  e precisou ser refeita, ~2h de intervalo entre as duas coletas) produziu
  `n` finais diferentes por bucket sob os MESMOS parâmetros — ver §5.6,
  "Achado lateral não previsto".

**Resultado do lote (v1.9.3, 2026-08-08) — 29 filmes, 0 falhas, `min_chars`
e cascata mantidos em 150/[150,50,0] (auditoria fechou pela manutenção).**
Custo real: 2254 requisições (média 77,7/filme, 12,6% acima da projeção de
69 medida na Entrega 2), 5363s de parede (~1,49h, 15% acima da projeção de
~1,3h — ainda bem abaixo do teto de ~4h), ~6,95 MB de bruto (quase exato à
projeção de ~7,1 MB). Achados estruturais (REGISTRADOS, não corrigidos):

- **`material_esgotado` disparou pela primeira vez em produção.**
  `obsession-2026` (214 notas no total — o filme mais obscuro já coletado)
  parou por esgotamento real em 9 dos 10 níveis (só 1,5★ parou por
  orçamento, tendo 1 página de orçamento e 3 notas totais no nível).
  Persistência, `montar_buckets` e o JSON se comportaram corretamente —
  produziu os primeiros estados REAIS de piso reduzido:
  `negativas`=5 (`sem_numero`), `medianas`=6 (`sem_numero`),
  `positivas`=8 (`sem_quantificador`). Os 3 outros estados do piso
  escalonado (todos exceto `completa`) agora têm exemplo real, não só
  sintético.
- **Distribuição invertida — 2 de 4 candidatos confirmados, não 4.** A
  lista foi curada esperando `joker-folie-a-deux`, `cats-2019`,
  `napoleon-2023` e `wonka` como negativas-dominantes. Medido sob as
  fronteiras C: só `cats-2019` (85,9%) e `joker-folie-a-deux` (46,2%) têm
  `negativas` como bucket dominante do histograma; `napoleon-2023` é
  dominado por `medianas` (44,8%) e `wonka` por `positivas` (50,2%) — a
  expectativa de reputação/crítica não bate com a distribuição real de
  NOTAS sob a fronteira C. Onde a inversão realmente ocorreu, a montagem
  de buckets e a agregação do histograma funcionaram sem incidente — o
  caminho "bucket dominante = negativas" nunca tinha sido exercitado
  contra dado real e não quebrou nada; o campo que informa a ordem de
  abertura do MOVIMENTO 3 ao narrador (fora de escopo tocar aqui) recebe
  o mesmo dado de sempre, só que agora com `negativas` no topo em 2 casos
  reais.
- **Rendimento pós-filtro NÃO correlaciona com popularidade — corrige o
  sinal direcional da diagnose anterior (n=6).** Com os 35 filmes já
  coletados (105 buckets), Pearson r(total de notas do histograma,
  n_final) = 0,05-0,13 por tipo de bucket — essencialmente ZERO,
  contra a leitura direcional de n=6 que sugeria filmes populares
  rendendo pior. Também r(share do bucket no histograma, n_final) = 0,06
  no agregado dos 105 buckets; buckets com share <10% do histograma
  fecham a cota tanto quanto buckets com share ≥10% (70% vs. 65%, mediana
  40 em ambos os grupos). Caso ilustrativo: `wicked-2024`/`positivas` é
  76,2% do histograma (bucket dominante, filme com 2,8M notas) e ainda
  assim fecha só `n=20` — o rendimento pós-filtro é IDIOSSINCRÁTICO ao
  filme (composição de quem escreve review longa naquele fandom
  específico), não previsível por popularidade nem por share. **A
  correção do sinal de n=6: não há evidência, com n grande, de que
  filmes populares rendam sistematicamente pior.**
- **Fechamento de cota por tipo de bucket é equilibrado, não estrutural.**
  `negativas` fecha 66% (23/35), `medianas` 63% (22/35), `positivas` 71%
  (25/35) — nenhum dos três tipos concentra o déficit. Sob o orçamento
  POR BUCKET (v1.9.1+), o viés histórico contra `medianas` (2 níveis vs.
  4) não reaparece; o déficit, quando ocorre, é por filme e por nível
  específico, não pelo formato do bucket.
- **14/29 filmes fecham a cota 40 nos 3 buckets; 84/87 buckets em
  `estado_piso=completa`.** A maioria dos déficits (todos exceto
  `obsession-2026`) fica acima do limiar `completa` (≥15) — a narrativa
  teria número/quantificador/temas completos mesmo nos buckets abaixo da
  cota cheia.

### [C2] Seleção downstream — cota 40/40/40 sobre o bruto persistido (v1.9.0)

Lê `dados/bruto/<slug>/` e escolhe **até 40 reviews por bucket**, com tudo o
que era decisão de coleta virando **parâmetro de chamada**: `fronteiras`,
`cota_por_bucket` (40), `min_chars` (150), `excluir_spoiler` (True), `cascata`
(150 → 50 → sem filtro), `piso_nivel` (2). **Zero requisições de rede.**

Por bucket:

1. Elegíveis = reviews dos níveis daquele bucket (pelas `fronteiras` recebidas)
   com `texto_completo: true` e — se `excluir_spoiler` — sem `spoiler_flag`.
2. Alvo por nível = alocação de [C1] recomputada sobre o **mesmo histograma**
   (persistido em `meta.json`, portanto disponível offline).
3. **Cascata por nível**, na ordem: `≥150` → se o nível daria **zero**, `≥50` →
   se ainda zero, **sem filtro**. Idêntica à regra da v1.1.0 (§C): a cascata só
   dispara quando o degrau anterior daria zero naquele nível, nunca para
   "completar cota".
4. **Redistribuição de déficit** ([C1], ressalva 2), restrita ao mesmo bucket.
5. Ordem de escolha dentro do nível: `(pagina_origem, ordem de aparição no
   jsonl)` — que é a ordem de amostragem da ordenação escolhida (§2.3).
   Determinística e reproduzível.

**Registrar por bucket** (§4): `n` final, **composição por nível** (alvo vs.
atingida), e **quantas reviews entraram por cada degrau da cascata**.

#### Motivos de descarte, discriminados (v1.9.1) — telemetria pura

O rendimento medido na v1.9.0 foi ~27% (73% do bruto não entra na seleção), e
até esta versão a telemetria não dizia **por quê** — sem isso não dá para
defender `min_chars=150` como número (§3[B], "Resultado medido", saída 5: com
`min_chars=50` os três buckets fecham 40/40/40), nem para avaliar qualquer
mudança futura de filtro com dado em vez de intuição.

Cada review do bruto de um nível é classificada em **exatamente uma**
categoria — `selecionada` ou um dos motivos abaixo — numa ordem de
precedência fixa, de modo que a soma dos motivos **sempre** fecha com
`n_brutas − n_validas` daquele nível:

1. `truncada_sem_texto` — `texto_completo == false` (a truncada não foi
   resolvida, ou o completamento a descartou — §C');
2. `spoiler` — marcada spoiler e `excluir_spoiler=True` (não conta quando o
   parâmetro é `False`: nesse caso a review é elegível, não descartada);
3. `abaixo_min_chars` — mais curta que o degrau da cascata que vigorou
   NAQUELE nível (não o `min_chars` nominal — se a cascata relaxou para 50,
   o corte real é 50);
4. `excedente_cota` — passou em tudo (texto completo, sem spoiler, comprimento
   suficiente) mas ficou **além** do que a alocação/redistribuição daquele
   nível permitiu — é material real, apenas não coube na cota;
5. `duplicata` — defensivo; o dedupe por `id` já acontece na persistência do
   bruto (§3[B']), então esperado **sempre zero** aqui; existir e não ser zero
   seria sinal de um bug na camada de baixo, não desta camada;
6. `outros` — catch-all; esperado **sempre zero**, canário de classificação
   incompleta.

Persistido por nível (`motivos_descarte`, dict `motivo → n`) e agregados nos
campos já existentes — `n_descartadas_spoiler`/`n_descartadas_curtas`/
`n_indisponivel_truncamento` passam a ser **derivados** do mesmo dict
discriminado (uma fonte de verdade, não duas contagens que podem divergir).
Nenhuma mudança de comportamento: é telemetria sobre decisões que a seleção
já tomava, só que agora nomeadas.

#### Precisão da amostra — nos DOIS níveis de confiança

Uma frequência de tema medida sobre `n` reviews é uma estimativa, e a régua de
**1 erro padrão sozinha promete mais do que entrega** (cobre ~68%, não a
confiança que um leitor assume ao ver uma barra). Ambas ficam registradas:

| `n` do bucket | ±1 EP | ±95% |
|---|---|---|
| **40** (cota cheia) | **±7,9pp** | **±15,5pp** |
| **30** | **±9,1pp** | **±17,9pp** |
| 15 (fronteira de `completa`) | ±12,9pp | ±25,3pp |
| 8 (fronteira de `sem_quantificador`) | ±17,7pp | ±34,6pp |

Pior caso `p = 0,5` (`EP = √(0,25/n)`), que é o teto para qualquer proporção.
Leitura direta: com `n=40`, um tema em 40% e um tema em 25% **não são
distinguíveis** a 95%. É o que justifica o piso escalonado (§3[C3]) suprimir
número antes de suprimir tema — o tema é observação, o número é estimativa, e
os dois degradam em ritmos diferentes.

**Auditoria de `MIN_CHARS=150` (v1.9.3, 2026-08-08) — MEDIÇÃO, zero
requisições, nenhum parâmetro alterado.** `min_chars=150` nunca tinha sido
validado contra dado (herança da v1.0). Motivada pela diagnose do déficit
de buckets (§3[H]), que atribuiu 63-87% do descarte dos 4 buckets
deficitários a `abaixo_min_chars`. Medido sobre os 6 filmes em
`dados/bruto/` (`selecao.selecionar` reexecutado, sem tocar `config.py`):

- **Distribuição de `n_chars`:** 40,6% do bruto agregado tem 0-49 chars,
  23,8% tem 50-99, 9,9% tem 100-149 — **74,3% do bruto fica abaixo de 150**
  em TODOS os 6 filmes, deficitários ou não (46,2%/26,4%/10,4% nos
  deficitários vs. 39,0%/23,1%/9,7% no resto — a cauda curta não é
  exclusiva dos buckets que faltam cota, é a forma normal da distribuição
  em qualquer filme).
- **Simulação de limiares (18 buckets, 6 filmes):** `min_chars=50` fecha
  18/18 na cota; `100` fecha 17/18; `150` (atual) fecha 14/18; `200` fecha
  9/18. Comprimento médio da amostra selecionada cresce monotonicamente
  com o limiar (270 → 362 → 459 → 564 chars). Composição por nível
  respeitada em todos os casos testados (a alocação proporcional não
  quebra sob nenhum limiar simulado).
- **Cascata com rung intermediária (`150→100→50→0` vs. atual
  `150→50→0`):** **NÃO ajudou — piorou um bucket já deficitário.**
  `parasite-2019`/negativas caiu de 28 para 22. Causa isolada por nível:
  o nível 0,5★ (12 reviews brutas, nenhuma ≥150 chars) tem 6 reviews entre
  50-99 chars e só 1 entre 100-149; sob a cascata atual ele cai direto
  para o degrau 50 e pega as 7 (filtro nunca desce "para completar cota",
  só quando o degrau atual dá ZERO — regra da v1.1.0, preservada); sob a
  cascata testada ele para no degrau 100 (não-zero, 1 review) e NUNCA
  chega ao 50, perdendo as 6 reviews de 50-99 que a cascata atual
  aproveitava. Os buckets que já fecham a 150 não mudaram em nenhum caso
  (mudança é localizada, como esperado), mas o efeito na direção oposta
  à hipótese — a regra "só desce em zero" pode tornar uma rung
  intermediária estritamente PIOR para um nível específico, não neutra.
- **Amostra qualitativa (40 reviews, 50-149 chars, semente `24081900`,
  estratificada pelos 6 filmes × 3 buckets):** dado bruto, sem
  classificação — decisão do usuário. **Ressalva de qualidade:** 4 das 40
  (10%) são o placeholder de spoiler do parser (`SPOILER_PLACEHOLDER`,
  "This review may contain spoilers..."), não texto real — `n_chars`
  mede o placeholder, não a review original redigida.
- **Rendimento vs. popularidade (n=6, sinal direcional, NÃO conclusivo):**
  correlação de Pearson entre total de notas do histograma e fração de
  bruto abaixo de 150 chars — os 2 filmes mais populares (`parasite-2019`
  5,7M notas, `everything-everywhere-all-at-once` 4,1M) têm as maiores
  frações abaixo de 150 (83,3% e 74,8%); os 3 do catálogo, com 0,3-1,2M
  notas, ficam em 67,7-72,5%. Direção consistente com a hipótese da
  diagnose, mas `n=6` não sustenta conclusão estatística.

**Nenhuma decisão tomada.** `MIN_CHARS`, `CASCATA_CHARS` e o orçamento de
páginas seguem inalterados — a leitura dos dados acima e a decisão sobre
o limiar são do usuário.

### [C3] Piso escalonado — 4 estados (v1.9.0)

Substitui o piso binário de 3 (`sem_analise` ou tudo). Calculado sobre o **`n`
final de cada bucket** depois da seleção:

| `n` final | Estado | O que o bucket entrega |
|---|---|---|
| **≥ 15** | `completa` | temas + frequências + quantificadores |
| **8–14** | `sem_quantificador` | frequências, com marca de amostra pequena; sem quantificador verbal |
| **3–7** | `sem_numero` | temas listados, **sem número e sem quantificador** |
| **< 3** | `sem_analise` | comportamento atual: contagem + `reviews_url`, nenhum tema |

**Os limiares (3, 8, 15) são ARBITRÁRIOS** e entram na spec com esse rótulo
explícito — mesma política dos limiares de `marcacao_perspectiva` (v1.5.0). Não
há evidência empírica que os fixe; são um primeiro corte com a ordem de
grandeza certa (ver a tabela de precisão acima: em `n=8` o intervalo de 95% já
passa de ±34pp, o que torna um quantificador verbal indefensável).

**Nesta sessão, apenas o CAMPO é exposto.** `estado_piso` entra no JSON de
resultado, consumível pelo frontend e pelo narrador. As **variantes de
narrador** e os **estados de UI** correspondentes **NÃO** são implementados
aqui. O campo `modo` (`completo`/`reduzido`/`sem_analise`) permanece intacto,
para não quebrar frontend e render existentes.

#### Caso de borda — bucket DOMINANTE em modo reduzido

A regra de **ABERTURA OBRIGATÓRIA** do MOVIMENTO 3 (§D2, variante COM
distribuição) manda abrir pelo grupo de **maior peso**. Num filme obscuro, o
bucket dominante pode cair em `sem_numero` ou `sem_analise` — não há narrativa
definida para "abrir por um grupo que não tem temas". Comportamento definido
(documentado agora, **implementado depois**):

> **O peso vem do histograma de NOTAS e NÃO depende de haver review com
> texto.** Portanto a abertura **continua sendo do grupo dominante**, com seu
> `rotulo_peso` e percentual — esse é um fato sobre o filme, e suprimi-lo
> reintroduziria a infidelidade por omissão que a v1.4.0 corrigiu (um filme
> amplamente amado soando dividido porque o grupo grande ficou mudo).
> O que muda é o **conteúdo** da abertura, conforme o estado do grupo
> dominante:
> - `completa` / `sem_quantificador`: comportamento atual.
> - `sem_numero`: abre pelo peso e cita os temas do grupo **sem nenhuma
>   frequência** — nem número, nem quantificador verbal.
> - `sem_analise`: abre pelo peso e diz, explicitamente, que **não há material
>   escrito suficiente desse grupo para descrever o que ele achou** — e só
>   então segue para o grupo de maior peso seguinte, que passa a carregar o
>   corpo do movimento. A ausência é declarada, nunca preenchida com os temas
>   de outro grupo nem disfarçada abrindo por quem tem material.
>
> Invariante que amarra os três casos: **peso e temas são dados diferentes, com
> disponibilidade diferente** — a narrativa pode ter o peso sem ter os temas, e
> nesse caso reporta o peso e declara a falta, em vez de reordenar os grupos
> para esconder o buraco.

Registrar por nível (bruto, §3[B']): `paginas_gastas_por_nivel`,
`contagem_bruta_por_nivel`, `contagem_estimada_valida_por_nivel`,
`paradas_por_limite`. Registrar por nível (análise, §4): `n_validas`,
`n_alvo`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`,
`n_descartadas_truncamento`.

**Cache:** por filme+nível+página (e por texto completo, ver C'), em disco (SQLite ou JSON por filme). Nunca rebuscar página cacheada. Cache não expira na v1.

**Caminho do cache — PROVISÓRIO (v1.1.1):** implementado em `resultado/cache/<slug>/` em vez de `cache/<slug>/` na raiz. Consequência direta da restrição de arquivos da Fase 1 (que não permitia criar `cache/` fora de `resultado/`), não uma decisão de design. Ratificado para v1.1.1 — mudar agora seria churn sem ganho. **Candidato a v1.2:** desacoplar para `cache/` ou `.cache/` na raiz — `resultado/` é semanticamente a **entrega** (descartável/versionável), enquanto o cache é **estado reconstruível caro** (dezenas a centenas de páginas HTML); misturar os dois acopla ciclos de vida opostos (ex.: limpar `resultado/` hoje também apaga o cache e força recoleta completa).

### [C] Filtros e cascata (por nível)

> **v1.9.0 — esta seção descreve REGRAS, não mais um estágio de coleta.** Os
> filtros e a cascata continuam idênticos no conteúdo, mas passaram a ser
> aplicados **downstream, sobre o bruto persistido** (§3[C2]), com cada valor
> entrando como **parâmetro** em vez de constante. Durante a coleta os mesmos
> filtros são usados **só para decidir parar de paginar** (§3[B], degrau b) —
> nada é descartado por eles.

Ordem por review: (1) tem nota → (2) sem flag de spoiler → (3) comprimento.

Cascata avaliada por nível, sobre o material persistido do nível:
1. Filtro padrão (≥150 chars). Se `n_validas ≥` alvo do nível: nível completo.
2. Se `n_validas <` alvo: nível abaixo do alvo — o déficit vai para a
   redistribuição dentro do bucket (§3[C1]), **nunca** para relaxamento.
3. Se `n_validas == 0` no nível: relaxar para ≥50 chars; se ainda 0, remover
   filtro. Nível pode terminar vazio. **A cascata só dispara em zero** — ela
   nunca é usada para completar cota.

O piso de análise continua **por bucket**, agora **escalonado em 4 estados**
(§3[C3]). No estado mais baixo (`sem_analise`, `n < 3`) o comportamento é o de
sempre: exibir a **contagem** e a **URL da página de reviews do filme**
(`https://letterboxd.com/film/<slug>/reviews/`), no formato `→ N review(s)
disponíveis em <url>`, tanto no terminal quanto no JSON (campo global
`reviews_url`). **NÃO exibir os textos brutos das reviews.**

> **Por que não exibir texto bruto (v1.1.4):** a cláusula anterior ("se houver 1–2 reviews, exibir os textos brutos com aviso") contradizia o princípio de design do cabeçalho da spec — *todo trade-off entre completude e risco de spoiler resolve a favor de evitar spoiler*. Texto integral de review **sem** passar pela camada anti-spoiler do LLM (§D) é o caminho de **maior** risco de spoiler do produto; e a flag de spoiler do Letterboxd é **autodeclarada** (não confiável como garantia). Apontar para a página de reviews transfere a decisão de risco para o usuário, de forma consciente, em vez de o produto imprimir o texto por ele.

**Nota sobre comprimento e truncamento:** o filtro de comprimento usa o texto visível. Review truncada que já passa dos 150 chars no trecho visível é válida; o texto completo é resolvido em C'.

### [C'] Completamento de reviews truncadas — regra "nunca pela metade"
Aplicado somente a reviews que **já passaram todos os filtros** (não gastar requisição com review descartável):

1. **Detecção de truncamento — corrigido (Fase 1 / v1.1.1):** o detector é **exclusivamente o marcador de colapso `.collapsed-text`** no corpo (equivalente observável: texto visível terminando em `…`). `data-full-text-url` está presente em **quase toda review** (truncada ou não) e por isso **NÃO discrimina** — usá-lo como sinal de truncamento daria falsos positivos em massa. Validado com 2 casos positivos + 2 negativos, zero erros (ver `FASE1_INCOGNITAS.md` §A3). `data-full-text-url` continua sendo a **fonte da URL de completamento**, só não é mais o detector.
2. Para cada review truncada válida: buscar `data-full-text-url` (delay 2s, cache por id de viewing — chave via `p[data-likeable-identifier].uid`, ver §2.1).
3. Falha na busca → **uma** retentativa. Falha persistente → **descartar a review** e registrar em `n_descartadas_truncamento`. Nunca enviar texto parcial ao LLM.
4. O texto completo substitui o visível para todos os fins (inclusive re-checagem de spoiler: se o texto completo revelar o placeholder de spoiler, descartar).
5. **Sem backfill de cota na v1.1.1:** se o completamento descartar uma review (passo 3), a cota do nível fecha com o que sobrou (ex. 9/10) — **não há reposição** buscando outra bruta para substituir a descartada. Razões: (i) o shortfall fica **visível** via `n_descartadas_truncamento`, não é silencioso; (ii) o piso de 3 por bucket (§2) + modo `sem_analise` já tratam o caso degenerado sem inventar dados; (iii) backfill ingênuo tem custo de requisição **não limitado** — cada reposição pode ela mesma vir truncada e falhar, encadeando. **Candidato a v1.2**, com uma distinção que deve orientar o design: **backfill barato** (repor a partir da lista de brutas já paginadas no nível — custo = 1 requisição de full-text por reposição) é razoável; **backfill caro** (repaginar o nível para buscar mais brutas) não é — só o barato deve entrar em v1.2.
6. **SUPOSIÇÃO ABERTA — não verificada ao vivo:** o comportamento do endpoint `/s/full-text/` para uma review **simultaneamente truncada e com spoiler** é *assumido* (devolver o placeholder de spoiler, permitindo o descarte no passo 4), não confirmado com um caso real — nenhuma review nessa condição apareceu nas amostras da Fase 1. Coberto por teste com fixture sintética (caminho de código exercitado), mas **não** por um caso ao vivo. Se o endpoint devolver o texto real em vez do placeholder, o spoiler vazaria ao LLM. **Instrução operacional:** se um viewing id truncado+spoiler aparecer numa coleta futura, gastar 1 requisição para confirmar o comportamento antes de confiar cegamente nesta suposição.

Custo estimado: no pior caso ~100 requisições extras por filme novo (uma por review válida truncada), ~3 min adicionais a 2s/req. Aceitável para ferramenta pessoal com cache.

### [D] Síntese LLM
- **Uma chamada por bucket** (máx. 3 por filme), modelo configurável.
- **Provider-agnóstico (v1.1.1):** a interface de cliente injetável (`client_call(system, user, model) -> str`) é o **contrato formal**. Providers suportados: **Gemini** (chave `GEMINI_API_KEY`, modo JSON nativo) e **Anthropic** (chave `ANTHROPIC_API_KEY`). Seleção via `--provider {gemini,anthropic}`; sem a flag, auto-detecta pela chave presente no ambiente; se ambas as chaves estiverem presentes, ou nenhuma, é erro — exige decisão explícita.
- **Default de modelo Gemini — `gemini-2.5-flash` (v1.1.2, ratificado com evidência):** a comparação de modelos (`resultado/comparacao/COMPARACAO.md`) rodou o MESMO prompt sobre o MESMO corpus (`oppenheimer-2023`) em `gemini-2.5-flash-lite` e `gemini-2.5-flash`. O flash-lite cometeu **3 violações de instrução** documentadas: (1) bucket `negativas` inteiro em inglês, violando "saída sempre em pt-BR"; (2)-(3) `observacao_geral` generalizando o recorte filtrado do bucket para "a maioria dos críticos considera o filme um fracasso" — o próprio erro de enquadramento que motivou o preâmbulo de papel abaixo. O `gemini-2.5-flash`, no mesmo teste, não repetiu nenhuma das três. Default Anthropic: `claude-sonnet-4-6`.
- **Prompt PARAMETRIZADO POR BUCKET (v1.1.2)** — não mais uma string única. A parametrização é **por bucket** (nome + intervalo de notas), nunca por provider/modelo: o texto para um dado bucket é **byte-idêntico** entre Gemini e Anthropic; só o transporte (SDK, formato de chamada) muda por adaptador.
- Entrada: todas as reviews válidas do bucket (texto COMPLETO + nota), instruções fixas.
- Frequências sempre relativas a `n_reviews_analisadas`, nunca absolutas soltas. *(Até a v1.8.2 esta linha dizia "buckets têm tamanhos-alvo diferentes (50/20/30)"; sob a cota 40/40/40 os alvos são iguais, mas o `n` REAL de cada bucket continua podendo diferir — material insuficiente fecha um bucket curto (§3[C3]) —, então a regra do denominador não muda.)*
- **Denominador e clamp — regra de código, não de prompt (v1.1.1):**
  - `n_reviews_analisadas` é **sempre carimbado pelo código**, a partir da contagem real de reviews enviadas ao LLM naquele bucket. Qualquer valor que o LLM devolva nesse campo do JSON é **ignorado** — nunca usado, nem como fallback. (Correção de bug: a v1.1.0 fazia o inverso — confiava no valor do LLM e só usava o real como fallback.) Em modo degradado essa distinção é a diferença entre honestidade e maquiagem estatística.
  - `mencoes_aproximadas` é **clampado** para o intervalo `[0, n_reviews_analisadas]` (o código nunca aceita um numerador maior que o total de reviews do bucket, nem negativo). Quando o clamp atua, é sinal de alucinação do modelo e **fica visível, não silencioso**: o tema carrega `mencoes_clampadas: true` + `mencoes_valor_original` (o valor cru que o LLM devolveu), exibido também no render do terminal.
- Saída obrigatória em JSON:

```json
{
  "bucket": "negativas",
  "temas": [
    {
      "tema": "ritmo lento",
      "mencoes_aproximadas": 14,
      "n_reviews_analisadas": 50,
      "exemplo_parafraseado": "vários reviewers acham o segundo ato arrastado",
      "mencoes_clampadas": false,
      "mencoes_valor_original": null,
      "aspas_removidas": false
    }
  ],
  "observacao_geral": "1-2 frases de síntese do bucket",
  "idioma_invalido": false,
  "escopo_suspeito": false
}
```

(`mencoes_clampadas`/`mencoes_valor_original`/`aspas_removidas`/`idioma_invalido`/`escopo_suspeito` são carimbados pelo código pós-parsing — não fazem parte do que se pede ao LLM no prompt; ver regras abaixo.)

#### Template do prompt (SPEC — texto oficial, `build_system_prompt(bucket_nome)` em `synthesize.py`)

**a. Preâmbulo de papel — NOVO (v1.1.2), parametrizado por `{bucket_nome}` e `{intervalo}` (ex.: `negativas` / `0.5–2.5 estrelas`):**

> Você é uma etapa de um pipeline que agrega reviews de usuários de um filme do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES desta etapa (negativas, medianas, positivas); você está recebendo EXCLUSIVAMENTE a faixa "`{bucket_nome}`" (`{intervalo}`) — um recorte enviesado POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.
>
> Sua função é descrever o que ESTE grupo específico de reviews diz. Outros módulos do pipeline cuidam das outras faixas de nota; o usuário final verá as três análises lado a lado, cada uma rotulada com sua faixa.
>
> Consequência explícita: é PROIBIDO generalizar para "os críticos", "a maioria", "o consenso" ou "a recepção do filme". A `observacao_geral` deve se referir sempre a ESTE grupo (ex.: "as reviews `{bucket_nome}` apontam...", "este grupo destaca..."), nunca ao filme em termos absolutos.

**Motivação (evidência empírica):** rodando o prompt v1.1.1 (sem preâmbulo) sobre o bucket `negativas` de `oppenheimer-2023`, o flash-lite escreveu `observacao_geral: "a maioria dos críticos considera o filme um fracasso"` — generalizando um recorte filtrado por construção (só notas ≤2.5) para a opinião geral do filme. O preâmbulo ataca esse erro de enquadramento na raiz, antes de qualquer instrução de formato.

**b. Instruções fixas (invariáveis) — as 5 anteriores + 2 novas (v1.1.2):**
  1. Anti-spoiler: descrever críticas em nível temático (ritmo, atuações, fotografia, roteiro em termos abstratos); **proibido mencionar eventos da trama, destinos de personagens, reviravoltas ou o final**, mesmo que as reviews os mencionem.
  2. `exemplo_parafraseado` é paráfrase, nunca citação literal de review.
  3. Temas ordenados por `mencoes_aproximadas` decrescente; máximo 6 temas por bucket; não inventar temas com menção única salvo se o bucket tiver < 5 reviews.
  4. Reviews em qualquer idioma; saída sempre em pt-BR.
  5. Responder apenas o JSON, sem preâmbulo.
  6. **NOVO:** proibido usar aspas (simples, duplas ou angulares) dentro de `exemplo_parafraseado` — nunca citar nem reproduzir um trecho entre aspas, mesmo traduzido; reescrever sempre em terceira pessoa, com palavras próprias. **Motivação:** o `gemini-2.5-flash`, na mesma comparação, usou frases entre aspas em `exemplo_parafraseado`, violando a regra de paráfrase (citação literal, ainda que traduzida).
  7. **NOVO:** reforço de idioma — TODOS os campos de texto em pt-BR, incluindo os NOMES DOS TEMAS, independentemente do idioma das reviews de origem.
- Parsing defensivo (strip de fences, try/except) e uma única retentativa em caso de JSON inválido (inalterado, v1.1.1).

#### Validações pós-parsing (código, não prompt) — v1.1.2

Rede de segurança/telemetria — o preâmbulo de papel (acima) é a **defesa principal** contra vazamento de escopo; estas checagens são baratas e propositalmente imperfeitas (heurísticas), não substituem revisão humana.

a. **Idioma:** heurística de contagem de stopwords pt-BR vs. inglês sobre a concatenação de `temas` + `exemplos` + `observacao_geral`. Ausência de stopwords de qualquer idioma (texto curto/indeterminado) **não** conta como violação — só conta quando há evidência de maioria em outro idioma. Se detectar não-pt-BR: **uma retentativa**, com instrução de idioma reforçada anexada ao FIM do prompt (não substitui o preâmbulo/instruções). Se persistir: aceita o resultado da retentativa e registra `idioma_invalido: true` no bucket (visível no render).
b. **Aspas:** se qualquer `exemplo_parafraseado` contiver aspas de citação (`" ' “ ” ‘ ’ « » ‹ ›`), remove-as **mecanicamente** (não é reescrita — apenas apaga os caracteres e normaliza espaços) e registra `aspas_removidas: true` **no tema**. **Sem retentativa** — correção mecânica basta, não vale gastar uma chamada de LLM. **v1.7.1 — bugfix:** quando a aspas vinha ESCAPADA no texto (`\"A Cura\"`), a remoção trocava só o caractere de aspas, deixando a contrabarra órfã (`\A Cura\`) — publicado ao vivo em `cure` e `the-invite-2026`. A remoção agora consome a contrabarra que precede a aspas junto, como uma unidade (`_remover_aspas`, `synthesize.py`).
c. **Escopo:** checagem barata na `observacao_geral` por marcadores literais de generalização ("a maioria dos críticos", "o consenso", "os críticos consideram", "amplamente aclamado", "amplamente rejeitado"). Se encontrar: **uma retentativa**; se persistir, aceita e registra `escopo_suspeito: true` no bucket. Heurística imperfeita por design (lista curta e literal, não NLP) — o preâmbulo de papel é a defesa principal; isto é rede de segurança e telemetria.

**Retentativa combinada:** se idioma **e** escopo falharem na mesma resposta, é feita **UMA única chamada extra** que reforça os dois ao mesmo tempo (não duas retentativas separadas) — mantém o orçamento de chamadas por bucket previsível (no máximo 1 retentativa de JSON + 1 retentativa de validação = 3 chamadas no pior caso por bucket).

#### Anti-spoiler: escopo da proteção e risco aceito (v1.1.3)

> **RISCO ACEITO** (decisão do usuário, 2026-07-19, validada com juiz humano que conhecia o filme — *Cure*, 1997): a proteção anti-spoiler cobre eventos da trama, desfechos e destinos de personagens. A zona cinzenta "mecanismo/dispositivo central da trama" (ex: nomear a técnica que conecta os eventos) é **risco aceito e NÃO deve ser endurecida**: instruções mais restritivas degradariam a especificidade dos temas em todos os filmes para evitar um falso negativo raro e tolerável. Saídas nessa zona são comportamento dentro do risco aceito, não bug.

> **EMENDA — sinopse oficial curta como fonte do MOVIMENTO 1 (v1.3.0, decisão do usuário, 2026-07-20):** a regra de "zero conteúdo de trama" continua valendo para reviews e para o conhecimento próprio do modelo, mas ganha uma exceção estreita e explícita: a **sinopse OFICIAL** de um filme (campo `overview` do TMDB — material de divulgação curado pelo próprio estúdio/distribuidor, categoria equivalente à sinopse de contracapa/poster) pode ser usada, condensada, como fonte do MOVIMENTO 1 da narrativa (§D2). Justificativa: esse texto é escrito para ser lido por quem ainda não assistiu — é a mesma informação que o usuário veria no pôster ou na página do filme antes de decidir assistir; não é "conteúdo de trama" no sentido que a regra original protege (revelações extraídas de reviews de quem já assistiu, ou conhecimento factual do modelo sobre o filme). O que **continua proibido**, sem exceção:
> - sinopses de **terceiros** (não oficiais — resenhas, wikis, sinopses de outros catálogos) como fonte de premissa;
> - **expansão** da sinopse oficial com qualquer conhecimento externo do modelo sobre o filme, elenco, direção ou produção;
> - usar a sinopse oficial para justificar relaxar o anti-spoiler dos MOVIMENTOS 2/3 (temas dos buckets) — a fronteira entre síntese validada e reviews brutas (§D2, "Decisão de arquitetura") não muda.
>
> Ressalva operacional: a sinopse oficial do TMDB é, na prática observada, quase sempre limitada à premissa (é material de marketing) — mas não há garantia formal disso. Por isso o prompt do narrador (§D2) instrui explicitamente: se a `sinopse_oficial` parecer revelar algo além da premissa inicial, usar só a parte que é premissa. Essa é uma instrução ao LLM (julgamento, não checagem mecânica) — no mesmo espírito de risco aceito do parágrafo acima, não um novo validador de código.

### [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0)

Etapa **PÓS-síntese**, opcional, controlada pela flag `--tom` (ver abaixo). Uma **única chamada LLM para o filme inteiro** (não por bucket), mesmo provider/modelo da síntese.

**Decisão de arquitetura (invariante, inalterada desde v1.2.0):** o narrador recebe **EXCLUSIVAMENTE o JSON validado** — os temas, `mencoes_aproximadas`, `n_reviews_analisadas` e `observacao_geral` dos 3 buckets, o total de reviews, e (v1.3.0) a **ficha técnica** do filme quando existir (§3a). **NUNCA as reviews brutas.** Ele reescreve informação **já validada** como prosa; não tem acesso a nada que as validações (§D) não tenham aprovado, nem a nada que não venha da ficha oficial do TMDB. Isso é garantido **por construção**: a entrada do narrador é o dict de saída de `build_output` (que não serializa texto de review) mais o campo `ficha` (que vem só do TMDB, nunca de reviews).

Por que essa fronteira (justificativa anti-embelezamento / anti-spoiler): dar reviews brutas ao narrador reabriria os dois riscos que o pipeline inteiro existe para conter — (1) **spoiler**, pois texto integral não passou pela camada anti-spoiler do LLM; e (2) **embelezamento/infidelidade**, pois o narrador poderia "florear" com material não contabilizado, quebrando a fidelidade às frequências. Lendo só o relatório validado (+ ficha oficial), o narrador não pode afirmar nada que a camada de baixo não tenha aprovado.

**v1.3.0 — narrativa em três movimentos:** a v1.2.x produzia um único bloco de prosa livre. A v1.3.0 estrutura esse bloco em três movimentos sequenciais, sem subtítulos visíveis no texto final (a divisão organiza o LLM, não aparece como marcação para o leitor) — motivada pela interface em vídeo que consome a narrativa em três passos de review: apresentar o filme, descrever a experiência de assisti-lo, e só então contrastar as reações.

1. **MOVIMENTO 1 — O FILME** (2-3 frases; só existe se houver `ficha` no relatório — sem ficha, a narrativa começa direto no Movimento 2): premissa a partir da `sinopse_oficial` do TMDB (pode condensar, PROIBIDO expandir com conhecimento externo — ver emenda de anti-spoiler em §3[D]), diretor, gênero, ano; duração só se for relevante ao que os movimentos 2/3 dizem.
2. **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): como é assistir ao filme, usando **apenas** propriedades DESCRITIVAS (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade) em que os grupos concordam no **núcleo factual**, mesmo divergindo na avaliação. Tom neutro, sem valência — descreve, não julga; a avaliação fica para o Movimento 3. **v1.3.1 — três critérios obrigatórios** para uma propriedade entrar aqui: **(a) categoria** — só descritiva, PROIBIDO juízo de qualidade (atuação/roteiro/direção boa-ou-ruim, isso é sempre disputa e pertence ao Movimento 3); **(b) presença** — vem de temas de pelo menos DOIS grupos com o mesmo núcleo factual, mesmo com valência diferente ("lento e tedioso" + "lento e deliberado" → núcleo "ritmo lento"); **(c) não-contradição** — se QUALQUER grupo nega o núcleo factual (não só diverge na avaliação), a propriedade é desqualificada. Cada propriedade usada é registrada em `consensos_usados` (telemetria — ver abaixo).
   **v1.4.1 — OMISSÃO AUTORIZADA:** se **menos de duas** propriedades passarem nos três critérios, o MOVIMENTO 2 deve ser **CURTO (1 frase) ou AUSENTE**, e a narrativa passa direto ao MOVIMENTO 3. **Omitir é o comportamento CORRETO, não uma falha** — não há cota de frases a cumprir, e um filme com poucos temas descritivos simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de qualidade suavizado ("estilo visual eficaz", "abordagem arrojada") é **pior** do que não ter o movimento: é a violação do critério (a) disfarçada de descrição por um advérbio de hesitação. Quando omitido, `consensos_usados` vem como **lista vazia** — resultado esperado, e a validação de `_consensos_validos` **não** trata lista vazia como suspeita (válida por vacuidade, regra já vigente desde a v1.3.1).
3. **MOVIMENTO 3 — O CONTRASTE** (enxuto — ~40% menor que a narrativa única da v1.2.x): as perspectivas dos três grupos, priorizando os 2-3 temas **mais fortes** de cada grupo em vez de cobrir todos os até 6 possíveis — decisão motivada pela interface, que já exibe as barras de frequência tema a tema (a narrativa não precisa duplicar essa cobertura completa). Mantém **todas** as invariantes vigentes desde v1.2.x (rótulos de quantificador pré-computados, escopo por grupo, proibição de prevalência entre grupos, sem aspas, anti-spoiler, pt-BR).

Alvo de tamanho total: **250-400 palavras** (ajustado de 200-350 na v1.2.x — o movimento 1 adiciona conteúdo quando há ficha).

#### Diagnóstico de fluência (v1.5.0) — por que as narrativas soavam mecânicas

Leitura adversarial das narrativas entregues até a v1.4.1 (o texto de `the-invite-2026`, ver `resultado/the-invite-2026.json` campo `narrativa`, é o caso citado) revelou um padrão sistemático, não um defeito isolado:

- **Forma sintática repetida:** cada perspectiva era apresentada com a MESMA estrutura — rótulo de peso, seguido de verbo de reporte ("elogia", "reconhece", "classifica"), seguido de complemento — três vezes seguidas, uma por grupo.
- **Comprimento de frase quase constante:** a maioria das frases caía na faixa de 25-35 palavras, sem variação perceptível.
- **Densidade alta de verbos de reporte e nominalizações** no lugar de verbos diretos ("a repetição das situações torna a experiência cansativa" em vez de "as situações se repetem e o filme cansa").

**Causa provável:** o acúmulo de invariantes de honestidade das versões anteriores (peso ancorado com percentual, quantificador pré-computado, escopo por grupo, anti-spoiler, sem aspas, vocabulário "das notas") — cada uma necessária e nenhuma removida nesta versão — levou o modelo à ÚNICA forma sintática que satisfaz todas simultaneamente ao mesmo tempo: relatar, com um verbo, o que cada grupo (identificado pelo rótulo de peso) diz. É previsível: sob restrição suficiente, convergir para uma forma única é o caminho de menor risco para o modelo não violar nenhuma regra. A correção desta versão não afrouxa nenhuma invariante — prescreve **ritmo** e **registro** com a mesma precisão de código com que os números já são prescritos, para que a honestidade não dependa de sacrificar a fluência.

#### RITMO E REGISTRO — MIGRADOS PARA O EDITOR §E2 (v1.6.0)

As regras de ritmo e registro introduzidas na v1.5.0 (variação de comprimento e de abertura, conectivos de fala, limite de verbos de reporte, proibição de advérbios em -mente, tom de "contar para um amigo") **saíram do prompt do narrador** e passaram a viver no **editor (§E2)**. O par few-shot ANTES/DEPOIS foi movido junto — não duplicado.

**Por que a v1.5.0 falhou** (evidência em `DIAGNOSTICO_FLUENCIA.md` e `DIAGNOSTICO_FLUENCIA_V2.md`):
- **as regras não transferiram.** O `the-invite` pareceu obedecer, mas estava **copiando o few-shot** — 58 8-gramas compartilhados, porque o exemplo fora escrito com os dados daquele mesmo filme. `cure` e `cidade-de-deus`, sem nada a copiar, não transferiram estilo nenhum e pioraram em pontos;
- **a fiscalização era cega.** As métricas que disparavam retentativa não acompanham qualidade: no `cure`, o texto qualitativamente melhor pontuou PIOR em `cv_comprimento` (0.35 → 0.28) e em `verbos_reporte` (3 → 6);
- **o custo apareceu na saída publicada.** A configuração de produção (`thinking_budget=0`) gerou uma frase agramatical que foi ao ar.

**O diagnóstico de fundo permanece válido** (ver seção anterior): sob restrição suficiente, o modelo converge para a única forma que satisfaz todas as regras. O erro foi tentar resolver isso **empilhando mais regras no mesmo prompt** — o que aumenta a restrição em vez de aliviá-la. A v1.6.0 tira a carga de estilo do narrador e a entrega a um estágio que só tem essa função, e que é estruturalmente incapaz de comprometer a honestidade (§E2).

**O que o narrador ganhou no lugar:** uma nota curta avisando que existe um estágio de edição depois, que ele não precisa se preocupar com ritmo, e que deve escrever de forma clara e **gramaticalmente correta**. Nada além disso.

#### MARCAÇÃO DE PERSPECTIVA (v1.5.0, regra nova — só existe COM distribuição)

**Motivação:** ao remover os verbos de reporte (regra de REGISTRO, item f), a afirmação de um grupo minoritário pode soar como fato do próprio narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante (o grupo de maior peso, apresentado primeiro pela regra de ABERTURA OBRIGATÓRIA). Sem "eles apontam que", a frase "o humor é previsível" lida isolada parece uma afirmação do produto sobre o filme, não a opinião de uma fatia minoritária das notas.

**Pré-computação em código (`_marcacoes_por_bucket`/`_marcacao_perspectiva`, `synthesize.py`), por grupo, a partir dos `share_real`:**
- `dominante` = maior share entre os três grupos do filme;
- `marcacao_perspectiva = "nenhuma"` se `share > dominante/3`;
- `marcacao_perspectiva = "simples"` se `share <= dominante/3`;
- `marcacao_perspectiva = "antecipada"` se `share <= dominante/10`.

A condição mais restritiva (`antecipada`) é checada primeiro — um share que a satisfaz também satisfaz `simples`. **Só existe quando há distribuição real:** o mesmo motivo pelo qual a COTA de coleta (50/20/30) não pode alimentar este cálculo — usar a cota apresentaria amostragem como se fosse prevalência, o defeito que a v1.2.1 proíbe (§D2, regra (c) sem distribuição). Sem `share_real`, não há "dominante" legítimo a calcular. O valor é passado ao narrador na serialização, junto do `rotulo_peso` de cada grupo — o LLM não calcula nem escolhe.

**Limiares são ponto de partida, calibráveis:** ao contrário das faixas de quantificador (v1.2.2/v1.2.3) e de peso (v1.4.0), que vieram de casos reais observados e comparação de modelos, estes limiares (`dominante/3`, `dominante/10`) não têm evidência empírica prévia — são um primeiro corte razoável, sujeito a ajuste em versões futuras conforme a leitura adversarial das narrativas regeneradas.

**Regra no prompt:**
- TODO trecho que fala de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra exigido).
- `marcacao_perspectiva = "simples"`: além da abertura, ao menos UM marcador de perspectiva dentro do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
- `marcacao_perspectiva = "antecipada"`: o marcador interno deve vir ANTES da primeira afirmação substantiva do trecho sobre aquele grupo — não no fim.
- Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
- PROIBIDO marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito, conforme a v1.4.0 (RESPEITO À MINORIA).

**Telemetria (`marcadores_perspectiva`, mesmo padrão de `consensos_usados`/`quantificadores_usados`):** o narrador declara `{grupo, trecho}` para cada marcador usado, com o trecho copiado literalmente da narrativa. **v1.6.1 — esta declaração é auditoria humana, não fonte de validação** (ver abaixo); ela é persistida no JSON e exibida no render exatamente como antes.

**Validação pós-parsing (`_marcadores_validos`, `synthesize.py`) — v1.6.1, reescrita para verificar o TEXTO, não a declaração:**
(a) para todo grupo com `marcacao_perspectiva != "nenhuma"`, o MOVIMENTO daquele grupo (`_span_de_movimento`: do ponto em que ele é ancorado — rótulo de peso ou percentual — até a âncora do próximo grupo, ou o fim do texto) contém **alguma expressão de atribuição reconhecida** (a mesma lista `_EXPRESSOES_DE_PERSPECTIVA` que `montar_protegidos`, §E2, já usa — fonte única, sem duplicação: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa" e variantes); **v1.7.1** ampliou o vocabulário com a família "quem gostou/não gostou/amou/ficou no meio" (e as formas com "para" na frente) — caso real do `cure`, onde "quem não gostou considerou o ritmo lento e tedioso" cumpria a função de atribuição para o grupo de 3%, mas não estava na lista, produzindo falso positivo em `perspectiva_nao_marcada` num texto honesto. O "para quem" ISOLADO continua de fora — é pronome relativo comum e foi o que causou o falso NEGATIVO original da v1.6.0.)
(b) para `marcacao_perspectiva == "antecipada"`, **PELO MENOS UMA** dessas ocorrências precisa cair na MESMA frase em que o grupo é ancorado ou na frase IMEDIATAMENTE seguinte.

**v1.6.0 — dois bugs corrigidos:** "antecipada" passou a exigir **um** marcador bem posicionado, não todos (o narrador legitimamente declara mais de um ao elaborar o grupo — foi o que aconteceu no `the-invite`); e a comparação do trecho declarado ganhou normalização de caixa/acento/demonstrativo.

**v1.6.1 — a normalização não bastou, e a correção foi trocar O QUE se verifica.** O caso concreto do `cidade-de-deus` sobreviveu à v1.6.0: o narrador declarou *"Para esse grupo, muitos reconhecem a qualidade técnica…"* e escreveu *"Muitos neste grupo reconhecem a qualidade técnica…"* — divergência de **ORDEM DAS PALAVRAS** (similaridade 0.92), que nenhuma normalização de caixa/acento fecha. Fechar por comparação difusa com limiar foi **descartado** (de novo): um limiar de similaridade é uma linha arbitrária, e a checagem existe para confirmar que o marcador de perspectiva **EXISTE no texto** — não que a frase declarada é uma transcrição fiel dele.

A correção pela raiz separa as duas coisas que a v1.6.0 ainda misturava:
- `marcadores_perspectiva` é o que o LLM **diz que fez** — telemetria para revisão humana, exatamente como `consensos_usados`;
- a validação escaneia o que o LLM **realmente escreveu**, procurando qualquer expressão de atribuição reconhecida no trecho de texto associado ao grupo — **igual usa `trecho` declarado**.

Consequência: `_normalizar_trecho`/`_trecho_aparece` (v1.6.0) foram **removidas** — não davam conta do problema real, e a nova checagem não compara mais string contra string. `montar_protegidos` (§E2) e `_marcadores_validos` agora leem a **mesma constante** `_EXPRESSOES_DE_PERSPECTIVA`, então um vocabulário novo de atribuição só precisa ser ensinado num lugar.

Falha em qualquer critério → **1 retentativa** com reforço (`_REFORCO_MARCADORES`); se persistir, aceita e sinaliza `perspectiva_nao_marcada: true` em `narrativa_flags`. Lista vazia é válida por vacuidade quando nenhum grupo exige marcação (dominante ≈ os três grupos, ex. 40/30/30 — nenhum passa nos limiares). Persistido no JSON como campo global `marcadores_perspectiva` e exibido no render de terminal como bloco compacto, mesmo padrão de `consensos_usados`.

#### EXEMPLO DE ESTILO — MIGRADO PARA O EDITOR §E2 (v1.6.0)

O par ANTES/DEPOIS foi **movido** para o prompt do editor (§E2), onde o eixo de ritmo agora vive. Ele permanece **descontaminado** — filme fictício, números inventados (74/19/7) —, e um teste (`test_v160_few_shot_do_editor_segue_descontaminado`) impede a reintrodução de nomes ou shares do catálogo.

> **Registro histórico da descontaminação (sessão de diagnóstico, 2026-07-25):** a primeira versão do par usava os **dados reais do `the-invite-2026`** (79/18/3, o nome da diretora, o apartamento único). Medindo sobreposição de 8-gramas com as construções mandatórias mascaradas: `the-invite` **58**, `cure` **0**, `cidade-de-deus` **0**. Ou seja, o filme que parecia ter aprendido o estilo estava **copiando o exemplo**, e os outros dois não transferiram nada. Um few-shot construído sobre um filme do catálogo contamina a avaliação daquele filme e só daquele — e por isso não mede nada. Dois micro-exemplos que também carregavam dados do `the-invite` (a regra (e) de REGISTRO e a ilustração da ANCORAGEM) foram neutralizados junto.

#### Telemetria de fluência (v1.5.0, NOVO) — métricas calculadas em código, não pelo LLM

Mesma filosofia das demais telemetrias do §D2: o código não reescreve a prosa, só mede e sinaliza. Calculadas por `_metricas_fluencia` (`synthesize.py`) sobre o texto final da narrativa e persistidas em `metricas_fluencia`:

| Métrica | Definição |
|---|---|
| `n_frases` | Frases (divisão heurística por `.`/`!`/`?`, sem tratar abreviações) |
| `media_palavras` | Média de palavras por frase |
| `cv_comprimento` | **Desvio padrão ÷ média** de palavras por frase — mede VARIAÇÃO, não o comprimento em si (a regra de ritmo pede variação, não frases curtas o tempo todo) |
| `frase_mais_curta` | Menor contagem de palavras entre as frases |
| `aberturas_repetidas` | Pares de frases CONSECUTIVAS com a mesma primeira palavra (normalizada, minúscula) — proxy barato para "mesma estrutura de abertura" |
| `verbos_reporte` | Ocorrências dos verbos da regra (f) e flexões (`elogi-`, `destac-`, `apont-`, `relat-`, `consider-`, `classific-`, `mencion-`, `ressalt-`, `reconhec-`, `express-`, `descrev-`) |
| `adverbios_mente` | Ocorrências de advérbios intensificadores de uma lista fechada (intensamente, profundamente, extremamente, excessivamente e sinônimos comuns da mesma família) — deliberadamente NÃO cobre todo advérbio em `-mente` (ex. "praticamente" não é intensificador) |

**v1.6.0 — as métricas viram DIAGNÓSTICO PURO.** Os gatilhos automáticos de retentativa (`cv_comprimento < 0.40` · nenhuma frase ≤ 10 palavras · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`), o reforço `_REFORCO_FLUENCIA` e a flag `fluencia_baixa` foram **REMOVIDOS**.

**Motivo — as métricas não acompanham qualidade.** No `cure` (DIAGNOSTICO_FLUENCIA_V2.md, células A vs. B), o texto qualitativamente MELHOR pontuou PIOR nas duas métricas centrais:

| | A (pior texto) | B (melhor texto) |
|---|---|---|
| `cv_comprimento` | 0.35 | **0.28** |
| `verbos_reporte` | 3 | **6** |

`cv_comprimento` mede **dispersão** de comprimento de frase, não legibilidade: um texto com frases uniformemente boas pontua mal, e um texto truncado no meio pontua bem. Otimizar contra a métrica — que é exatamente o que uma retentativa automática faz — empurra o modelo a **degradar** a prosa para satisfazer um número. É o mesmo erro que o projeto já evitou em outros eixos (o código é autoridade sobre NÚMERO e RÓTULO; não é, e não deve ser, autoridade sobre ESTILO).

`_metricas_fluencia` continua sendo calculada e persistida em `metricas_fluencia`, com o mesmo estatuto de `consensos_usados`: **material de revisão humana**, não critério automático. O eixo de fluência passa a ser responsabilidade do editor (§E2), que trabalha por instrução e exemplo, não por limiar.

Persistida no JSON como campo global `metricas_fluencia` e exibida no render de terminal como linha-resumo, após os blocos de consensos/quantificadores/marcadores.

**Prompt fixo do narrador (SPEC — texto oficial, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`):**

> Você recebe um RELATÓRIO DE RECEPÇÃO já validado de um filme: três grupos de reviews separados por faixa de nota (negativas, medianas, positivas), cada um com seus temas, frequências aproximadas e uma observação; e, quando disponível, uma FICHA TÉCNICA do filme (sinopse oficial, diretor, gênero, ano, duração — fonte: TMDB). Sua tarefa é reescrever esse material como um texto corrido e envolvente, em TRÊS MOVIMENTOS, SEM subtítulos ou marcações entre eles (a divisão é para você se organizar, não para aparecer no texto), NESTA ORDEM:
>
> **MOVIMENTO 1 — O FILME** (2-3 frases; SÓ escreva este movimento SE houver FICHA TÉCNICA no relatório — sem ficha, comece direto no MOVIMENTO 2): apresente a premissa do filme a partir da `sinopse_oficial` da ficha — pode condensá-la, mas é PROIBIDO expandi-la com qualquer conhecimento externo sobre o filme, elenco, direção ou produção que não esteja na ficha fornecida. Se a `sinopse_oficial` parecer revelar algo além da premissa inicial do filme, use só a parte que é premissa e ignore o resto (a ficha NÃO tem passe livre sobre a regra de anti-spoiler abaixo). Mencione diretor, gênero e ano; duração só se for relevante para o que os dois movimentos seguintes vão dizer.
>
> **MOVIMENTO 2 — A EXPERIÊNCIA** (3-5 frases): descreva como é assistir ao filme usando APENAS propriedades DESCRITIVAS da experiência (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade) em que os grupos CONCORDAM no NÚCLEO FACTUAL, mesmo divergindo na avaliação. Tom NEUTRO, SEM valência — este movimento descreve, não julga; gostar ou não gostar fica para o MOVIMENTO 3. Uma propriedade só entra neste movimento se passar nos TRÊS critérios abaixo, TODOS obrigatórios (v1.3.1 — reescrito após um defeito real observado):
>
> a. CRITÉRIO DE CATEGORIA: só propriedades DESCRITIVAS. É PROIBIDO qualquer juízo de QUALIDADE (atuações boas/ruins, roteiro inteligente/fraco, direção competente/questionável, elenco talentoso/fraco) — julgamento de qualidade é sempre disputado entre quem gostou e quem não gostou, e pertence ao MOVIMENTO 3, NUNCA a este.
> b. CRITÉRIO DE PRESENÇA: a propriedade precisa derivar de temas de PELO MENOS DOIS grupos, com o mesmo núcleo factual — a valência pode divergir ("lento e tedioso" num grupo + "lento e deliberado" noutro = consenso factual "ritmo lento"; a avaliação de cada grupo sobre esse ritmo é coisa diferente e não entra aqui).
> c. CRITÉRIO DE NÃO-CONTRADIÇÃO: se QUALQUER grupo contradiz o núcleo factual (não só diverge na avaliação, mas nega o fato em si), a propriedade está desqualificada — não entra no MOVIMENTO 2 de jeito nenhum.
>
> EXEMPLO POSITIVO (os três critérios satisfeitos): as reviews negativas chamam o ritmo de "lento e tedioso", as positivas de "lento e deliberado" — ambos descrevem RITMO (categoria descritiva, critério a), os dois grupos concordam no núcleo "lento" (critério b), nenhum grupo nega isso (critério c) → consenso válido para o MOVIMENTO 2: "ritmo lento e contemplativo".
>
> EXEMPLO NEGATIVO (falha real observada, v1.3.0 — caso de "the-invite-2026"): as reviews positivas elogiam "atuações marcantes" e "roteiro inteligente"; as negativas têm os temas "atuações e direção questionáveis" e "roteiro fraco". Isso NÃO é consenso: é uma propriedade AVALIATIVA (qualidade de atuação, qualidade de roteiro — falha o critério a) E os grupos se contradizem diretamente sobre ela (falha o critério c também). O correto é NÃO mencionar qualidade de atuação/roteiro no MOVIMENTO 2 — essa disputa pertence ao MOVIMENTO 3, atribuída a cada grupo separadamente.
>
> É PROIBIDO importar qualquer informação que não venha dos temas validados dos três grupos.
>
> OMISSÃO AUTORIZADA (v1.4.1 — leia isto antes de escrever o movimento): se MENOS DE DUAS propriedades passarem nos três critérios ao mesmo tempo, este movimento deve ser CURTO (1 frase) ou AUSENTE — e a narrativa passa direto ao MOVIMENTO 3. OMITIR É O COMPORTAMENTO CORRETO, não uma falha: não há cota de frases a cumprir aqui, e um filme cujos temas descritivos são poucos simplesmente não tem um MOVIMENTO 2. Preencher o espaço com juízo de qualidade suavizado ("estilo visual eficaz", "abordagem arrojada", "atuações competentes", "roteiro habilidoso") é PIOR do que não ter o movimento — é o defeito que o critério (a) proíbe, disfarçado de descrição por um advérbio de hesitação. Quando o movimento é omitido, `consensos_usados` vem como lista VAZIA (`[]`) — isso é resultado esperado, não erro. Para CADA propriedade usada no MOVIMENTO 2, registre em `consensos_usados` (ver formato de saída) a propriedade, os grupos de onde ela veio e os nomes EXATOS dos temas (copiados literalmente do relatório) que a sustentam — esse registro é o artefato de revisão humana que confirma que o consenso é real, não inventado.
>
> **MOVIMENTO 3 — O CONTRASTE** (enxuto — a interface já exibe as barras de frequência tema a tema, então aqui priorize os 2-3 temas MAIS FORTES de cada grupo, não a cobertura completa dos 6 possíveis): as perspectivas dos três grupos — quem não gostou, quem ficou no meio, quem gostou — sobre o filme. Neste movimento (e em qualquer lugar do texto que fale de grupos) valem as invariantes abaixo, TODAS ainda em vigor:
>
> a. **PAPEL:** o texto inteiro é para alguém que está DECIDINDO se assiste ao filme e que AINDA NÃO ASSISTIU.
> b. **FIDELIDADE:** toda afirmação deve derivar da ficha técnica e/ou dos temas e números recebidos. É PROIBIDO adicionar fatos, opiniões próprias, ou qualquer contexto externo sobre o filme, elenco, direção ou produção que não esteja no relatório. Se não está nos dados, não existe.
> c. **TAMANHO DOS GRUPOS — REGRA CRÍTICA:** os três grupos NÃO têm o tamanho da opinião real do público. O tamanho de cada grupo é fixado pelo MÉTODO DE COLETA (uma cota fixa por faixa de nota), não pela quantidade de pessoas que pensam assim — as medianas, por exemplo, serão sempre o menor grupo por construção, em todo filme. Portanto é PROIBIDO comparar tamanhos entre grupos ou inferir prevalência global: NADA de "a maioria dos espectadores", "a maioria do público", "grupo maior", "grupo menor", "minoria", "igualmente expressivo", "recepção polarizada", "opiniões divididas", "consenso" ou qualquer equivalente. Trate cada grupo como uma PERSPECTIVA, não como uma fatia quantificada do público: apresente-os como "entre quem não gostou...", "já entre quem amou...", "para quem ficou no meio-termo...".
> d. **PROPORÇÕES (só DENTRO de um grupo):** proporções são permitidas APENAS internamente a um grupo e SEMPRE ancoradas ao denominador daquele grupo. NUNCA uma proporção que compare grupos ou fale do público como um todo.
> **QUANTIFICADOR PRÉ-COMPUTADO (obrigatório, v1.2.3):** cada tema do relatório já vem com um `rótulo_quantificador` calculado pelo CÓDIGO a partir da fração real de menções — você NÃO calcula nem escolhe o quantificador sozinho. Ao expressar a frequência de um tema em prosa, USE o `rótulo_quantificador` fornecido para aquele tema (sinônimos de mesma força são permitidos: "a maioria" ~ "mais da metade"; "muitos" ~ "boa parte"; "alguns" ~ "uma parte"). É PROIBIDO usar um quantificador MAIS FORTE do que o fornecido. Um quantificador MAIS FRACO é permitido se a fluência do texto pedir — nunca o oposto. Escala de força, do mais fraco ao mais forte: poucos < alguns/uma parte < muitos/boa parte < cerca de metade < a maioria/mais da metade < quase todos/praticamente todos.
> **DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES (v1.4.1):** para CADA expressão de frequência que você usar na prosa ao falar de um tema, registre um item em `quantificadores_usados` (ver formato de saída) com o quantificador EXATO que você escreveu e o NOME EXATO do tema (copiado literalmente do relatório) de onde aquela frequência vem — um item por expressão usada. Antes de declarar, confira o par contra o relatório: se o quantificador que você escreveu for mais forte que o `rótulo_quantificador` daquele tema, corrija a PROSA (não o registro). Se você não usar nenhum quantificador de tema, a lista vem vazia.
> e. **ESTRUTURA:** a divisão em três grupos (quem não gostou / quem ficou no meio / quem gostou) deve permanecer legível na prosa do MOVIMENTO 3, em qualquer ordem que sirva à narrativa.
> f. **ESCOPO:** cada afirmação sobre um grupo é atribuída ao SEU grupo ("as reviews negativas apontam...", "quem deu notas altas destaca..."). É PROIBIDO generalizar para "os críticos", "a maioria" (do filme todo) ou "o consenso".
> g. **ANTI-SPOILER:** em QUALQUER movimento (incluindo o 1, com a sinopse oficial), é PROIBIDO mencionar eventos de trama, personagens específicos ou desfechos, mesmo que a sinopse ou algum tema tangencie isso (defesa em profundidade — a camada anterior já filtra os temas, você reforça, e a sinopse oficial é tratada com a mesma cautela).
> h. **FORMA:** português do Brasil, SEM aspas de citação, SEM subtítulos ou rótulos dos movimentos no texto final, entre 250 e 400 palavras ao todo.
>
> **RITMO** (v1.5.0 — aplica-se à narrativa INTEIRA, não só ao MOVIMENTO 3): **a.** alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras); PROIBIDO três períodos consecutivos de comprimento semelhante; ao menos UMA frase de até 10 palavras na narrativa inteira. **b.** PROIBIDO abrir dois períodos consecutivos com a mesma estrutura. **c.** o rótulo de peso pode aparecer em QUALQUER posição do período, não só na abertura. **d.** use conectivos de fala ("só que", "aí", "já", "e", "mas"); pode iniciar período por conjunção.
>
> **REGISTRO** (v1.5.0): **e.** depois de estabelecer QUEM fala, descreva o filme DIRETAMENTE, sem reintroduzir o sujeito a cada frase. **f.** verbos de reporte (elogia, destaca, aponta, relata, considera, classifica, menciona, ressalta, reconhece, expressa, descreve): NO MÁXIMO 1 por movimento. **g.** prefira verbos a nominalizações. **h.** PROIBIDOS advérbios intensificadores em -mente (intensamente, profundamente, extremamente, excessivamente) — NO MÁXIMO 1 em toda a narrativa. **i.** escreva como alguém contando de um filme para um amigo — fluido e leve, SEM gíria, SEM emoji, SEM interpelação direta ao leitor, SEM hipérbole.
>
> Responda APENAS com JSON puro no formato: `{"narrativa": "<seu texto>", "consensos_usados": [{"propriedade": "<nome curto da propriedade descritiva>", "grupos_de_origem": ["<negativas|medianas|positivas>", ...], "temas_de_origem": ["<nome EXATO do tema, copiado do relatório>", ...]}], "quantificadores_usados": [{"quantificador": "<a expressão de frequência EXATA que você escreveu na prosa>", "tema": "<nome EXATO do tema, copiado do relatório, de onde ela vem>"}], "marcadores_perspectiva": [{"grupo": "<negativas|medianas|positivas>", "trecho": "<o trecho EXATO da narrativa, copiado literalmente, onde o marcador de perspectiva desse grupo aparece>"}]}`. `consensos_usados` pode ser `[]` se o MOVIMENTO 2 não usou nenhuma propriedade consensual (ver OMISSÃO AUTORIZADA); `quantificadores_usados` pode ser `[]` se a prosa não quantificou nenhum tema; `marcadores_perspectiva` pode ser `[]` quando nenhum grupo do relatório exige marcação de perspectiva (regra presente só quando há distribuição real — ver abaixo).

#### A regra (c) tem DUAS variantes (v1.4.0) — a escolha é do CÓDIGO, pelo dado

O §D2 passa a ter duas versões da regra (c), e **só ela** muda entre as
variantes: todo o resto do prompt (os três movimentos, os critérios do
MOVIMENTO 2, o quantificador pré-computado, anti-spoiler, forma) é
**byte-idêntico**, para que a comparação A/B isole a mudança.

- **SEM distribuição** → `build_narrator_prompt(False)` devolve o prompt
  histórico (`NARRATOR_SYSTEM_PROMPT`), com a regra (c) restritiva da v1.2.1
  intacta. O fallback não é uma reescrita parecida: é a MESMA constante.
  **Emenda v1.4.1:** até a v1.4.0 esse texto era byte-idêntico ao da v1.3.1;
  a v1.4.1 alterou as partes **compartilhadas** do prompt (omissão do
  MOVIMENTO 2 e declaração de quantificadores), que valem nas duas variantes.
  A invariante que continua de pé — e é a que a comparação A/B precisa — é a
  original: **só a regra (c) difere entre as duas variantes** (verificado em
  teste). **Emenda v1.5.0:** a marcação de perspectiva e o exemplo de estilo
  few-shot (ambos abaixo) foram adicionados **dentro** da regra (c) COM
  distribuição, porque dependem do `share_real` — a marcação usa o
  `dominante` calculado a partir dele, e o exemplo usa vocabulário de peso
  que a variante SEM distribuição proíbe. A invariante "só a regra (c)
  difere" continua válida por construção: é justamente por dependerem do
  mesmo dado que essas duas adições vivem dentro dela, não fora. As regras
  de RITMO e REGISTRO (que não dependem de share), por sua vez, entraram nas
  partes **compartilhadas** do prompt — presentes, idênticas, nas duas
  variantes.
- **COM distribuição** → a regra (c) INVERTE, virando "PESO REAL DE CADA GRUPO":

> c. **PESO REAL DE CADA GRUPO — REGRA CRÍTICA** (a distribuição está disponível neste relatório): você recebeu a DISTRIBUIÇÃO REAL das notas do filme, vinda do histograma público — quantas pessoas deram cada nota. Isso é um dado diferente do tamanho dos grupos de reviews analisadas (40/40/40), que é apenas a COTA DE COLETA e continua NÃO significando prevalência. Regras:
> - **ANCORAGEM OBRIGATÓRIA:** cada grupo DEVE ser apresentado, na primeira vez que aparecer no MOVIMENTO 3, com o `rotulo_peso` que veio no relatório para ele (ex.: "a grande maioria das notas (~79%)"). É PROIBIDO usar um rótulo MAIS FORTE do que o fornecido; um MAIS FRACO é permitido se a fluência pedir — nunca o oposto. Você NÃO calcula nem escolhe esse rótulo: ele é dado.
> - **ABERTURA OBRIGATÓRIA:** o MOVIMENTO 3 começa pela perspectiva de MAIOR peso. Esta regra tem precedência sobre a liberdade de ordem da regra (e).
> - **ÊNFASE PROPORCIONAL:** dê aproximadamente mais espaço ao grupo de maior peso e menos ao de menor peso — um filme amplamente amado não pode soar dividido, e um amplamente rejeitado não pode soar morno.
> - **RESPEITO À MINORIA:** a perspectiva minoritária é apresentada COMO minoritária, mas SEM desdém, ironia ou insinuação de que quem pensa assim está errado. Menos espaço, mesma seriedade analítica: quem procura saber se vai gostar precisa entender o que incomodou essa parcela.
> - **VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS (v1.4.1):** o `rotulo_peso` vem do histograma de NOTAS do Letterboxd, ou seja, de TODO MUNDO que avaliou o filme; os temas vêm das REVIEWS COM TEXTO, um subconjunto bem menor. São duas populações diferentes. Portanto, ao expressar peso, é OBRIGATÓRIO escrever "das notas" ("a grande maioria das notas (~79%)") e é PROIBIDO escrever "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review nem sobre quem assistiu sem avaliar. As frequências de TEMA seguem no vocabulário oposto (regra d): sempre em relação às reviews analisadas daquele grupo. Os dois vocabulários nunca se misturam.
> - Continua PROIBIDO inventar um número-síntese do filme (nota média, score, "X de 10", "nota N"): os shares por faixa são a ÚNICA quantificação permitida, e são três números, nunca um só.
>
> **MARCAÇÃO DE PERSPECTIVA** (v1.5.0 — motivada pela regra de REGISTRO acima): ao reduzir os verbos de reporte, a fala de um grupo minoritário pode soar como fato do narrador — porque ela chega depois de o texto já ter estabelecido a leitura dominante. Cada grupo do relatório vem com uma `marcacao_perspectiva` PRÉ-COMPUTADA (nenhuma/simples/antecipada, a partir do `share_real` — você NÃO calcula nem escolhe esse valor):
> - TODO trecho que falar de um grupo precisa conter ao menos uma ANCORAGEM de perspectiva para ele; para o grupo DOMINANTE, o próprio rótulo de peso já cumpre esse papel ("quem gostou é a grande maioria das notas (~74%)" já ancora — nenhum marcador extra é exigido).
> - `marcacao_perspectiva="simples"`: além da abertura, inclua ao menos UM marcador de perspectiva DENTRO do trecho que fala desse grupo (ex.: "para eles", "para esse grupo", "nessa leitura", "quem está nessa faixa").
> - `marcacao_perspectiva="antecipada"`: o marcador interno precisa vir ANTES da primeira afirmação substantiva sobre esse grupo, não no fim do trecho.
> - Um marcador de perspectiva NÃO é um verbo de reporte e NÃO conta para o limite da regra (f) de REGISTRO: "para eles o humor é previsível" é marcação; "eles apontam que o humor é previsível" é reporte e continua limitado.
> - É PROIBIDO um marcador com carga depreciativa ("apenas para eles", "só para esses poucos") — a perspectiva minoritária continua apresentada com respeito (mesma RESPEITO À MINORIA acima).
> Para CADA marcador de perspectiva que você usar, registre em `marcadores_perspectiva` (ver formato de saída) o grupo e o TRECHO EXATO, copiado literalmente da narrativa, onde ele aparece.
>
> EXEMPLO DE RITMO E MARCAÇÃO COM FILME FICTÍCIO — nunca reaproveitar seu conteúdo; os fatos vêm sempre do JSON recebido. O filme abaixo NÃO EXISTE e os números são INVENTADOS: eles servem só para mostrar a FORMA (variação de comprimento, aberturas diferentes, marcadores de perspectiva, ausência de verbos de reporte). Copiar qualquer fato, adjetivo ou número daqui é uma violação da regra de FIDELIDADE.
>
> ANTES (evite este ritmo): "A grande maioria das notas (~74%) elogia intensamente a condução do filme e o trabalho de câmera, destacando a habilidade de sustentar o clima em cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas sente que a indefinição do meio e a duração prolongada tornam a experiência cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo como arrastado e os personagens como estáticos."
>
> DEPOIS (busque este ritmo): "Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra num ponto só: o filme não tem pressa e usa isso a favor, porque cada silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma minoria das notas (~19%) chega até a metade junto. Para esse grupo, o problema aparece quando a história precisa decidir para onde vai, e não decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para eles a lentidão nunca vira método, os personagens não saem do lugar, e o final chega sem ter construído nada."

**`rotulo_peso` é PRÉ-COMPUTADO pelo código** — mesmo princípio da v1.2.3
(quantificador) e da v1.1.1 (denominador): o LLM não escolhe rótulo numérico.
Mapa determinístico sobre o `share_real`, do mais fraco ao mais forte:

| Faixa | Rótulo |
|---|---|
| **< 5%** | **uma fração mínima** *(v1.6.0)* |
| 5–10% | uma pequena minoria |
| 10–25% | uma minoria |
| 25–45% | uma parcela expressiva |
| 45–70% | a maioria |
| ≥ 70% | a grande maioria |

**v1.6.0 — faixa nova no extremo fraco.** Até a v1.5.0, 8% e 1% recebiam ambos "uma pequena minoria", achatando uma diferença de **oito vezes** entre os dois grupos minoritários — observado em `cidade-de-deus` (shares 91/8/1), onde o grupo mediano e o negativo apareciam com o mesmo peso verbal. A faixa `< 5% → "uma fração mínima"` separa o "muito pouco" do "quase nada" sem mexer em nenhuma outra fronteira, e sem tocar na convenção de desempate.

**Bordas resolvidas SEMPRE para o rótulo mais fraco** (itera do mais fraco ao
mais forte, primeiro match vence) — mesma convenção da v1.2.3:
`10 → uma minoria`, `25 → uma minoria`, `45 → uma parcela expressiva`,
`70 → a maioria`. Consequência documentada: "a grande maioria" começa de fato
em **71%**, não em 70% — subestimar o peso é aceitável, inflar não é.

O rótulo é sempre entregue **junto do percentual** (`"a grande maioria das
notas (~79%)"`): o número é o que impede o rótulo de virar retórica solta.

**Validação — a rede de prevalência MUDA DE SINAL:**

| | Sem distribuição | Com distribuição |
|---|---|---|
| Marcadores de prevalência ("minoria", "a maioria do público"…) | **violação** → retentativa → `prevalencia_suspeita` | **desligada** — essas palavras agora são EXIGIDAS pela regra (c); manter o detector ligado flaggaria toda narrativa correta |
| Ancoragem de peso | não se aplica (nada a ancorar) | **exigida** → retentativa (`_REFORCO_ANCORAGEM`) → `peso_nao_ancorado` |
| **(v1.4.1)** Vocabulário do peso ("das notas") | não se aplica (não há rótulo de peso) | **exigida** → retentativa (`_REFORCO_VOCABULARIO_PESO`) → `vocabulario_peso_suspeito` |

A checagem de ancoragem (`_ancoragem_de_peso_ok`) aceita, por grupo: o rótulo
fornecido, **qualquer rótulo mais fraco** (o prompt permite descer de força) ou
o percentual literal. Heurística deliberadamente permissiva — a defesa
principal é a instrução; isto detecta o modo de falha que importa: o narrador
ignorar os pesos e reescrever a narrativa antiga, de grupos equivalentes.

**Fallback (§3[G]):** sem distribuição, tudo isso desaparece sozinho — prompt
histórico, rede de prevalência original ativa, `peso_nao_ancorado` sempre
`False`, render com o disclaimer antigo, frontend sem shares. **Não há flag de
configuração:** a presença do dado é o interruptor.

**Por que a invariante (c) existe (v1.2.1 — defeito corrigido):** os buckets têm tamanhos fixados pela **cota de coleta** — na época 50/20/30 (= 10 válidas × nº de níveis de nota do bucket: 5/2/3), hoje 40/40/40 (v1.9.0) —, que **não** refletem a distribuição real da recepção. *(A v1.9.0 removeu o acidente aritmético mas NÃO a razão da invariante: uma cota, igual ou desigual, continua sendo amostragem, não prevalência.)* A narrativa da v1.2.0, sem a regra (c), inferia prevalência a partir das cotas ("grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada") — as medianas seriam "minoria" em todo filme, para sempre, por construção. A invariante (c) é a **defesa principal**; a telemetria abaixo é a rede de segurança.

**Por que o quantificador virou pré-computado (v1.2.3 — reincidência corrigida pela raiz):** a v1.2.2 tentou corrigir a inflação de quantificadores por INSTRUÇÃO — pedir ao LLM que calculasse a fração e escolhesse o rótulo por uma tabela. Funcionou parcialmente, mas **reincidiu**: na primeira regeneração das 3 narrativas pós-fix, "quase todos"/"praticamente todos" foi aplicado a frações de 65-70% **2 vezes** (a condição de escalada que o próprio changelog da v1.2.2 previa: *"um checador numérico pós-parsing é candidato futuro caso a inflação reincida"*). A correção pela raiz é o **mesmo princípio da v1.1.1** (denominador de `n_reviews_analisadas`): o LLM não decide número nem rótulo numérico — **o código é a autoridade**. `_serialize_output_for_narrator` agora pré-computa `fracao`/`rótulo_quantificador` por tema (`_fracao_e_rotulo`, mapa determinístico em `_rotulo_quantificador` — mesmas faixas da v1.2.2, resolução de sobreposição sempre para o rótulo mais fraco) e os injeta na entrada do narrador; o prompt (d) deixou de pedir cálculo e passou a proibir só usar um rótulo MAIS FORTE que o dado. **Rede de segurança complementar (v1.2.3):** checagem em nível de bucket — se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço; se persistir, `quantificador_suspeito: true`. Deliberadamente restrita a esse quantificador (o único modo de falha observado) — não cobre uso indevido dos demais rótulos.

**Por que o Movimento 1 é condicional à ficha (v1.3.0):** a ficha TMDB é aditiva por design (§3a) — pode faltar (API fora do ar, filme não encontrado, `--no-ficha`). Sem ela não há `sinopse_oficial` para ancorar o Movimento 1, e nada no prompt permite ao narrador inventar uma premissa a partir dos temas de review (violaria (b) FIDELIDADE e a proibição de conhecimento externo). Por isso o prompt instrui explicitamente pular para o Movimento 2 quando a ficha está ausente — mesmo comportamento defensivo do resto do pipeline (buckets `sem_analise` não inventam temas; a ficha ausente não inventa premissa).

O formato de saída `{"narrativa": ..., "consensos_usados": [...]}` reusa os mesmos adaptadores de provider (modo JSON nativo) e o parsing defensivo do §D. Sobre a prosa retornada aplicam-se as **mesmas validações pós-parsing** que fazem sentido para texto livre: **aspas** (remoção mecânica → `aspas_removidas`), **idioma**, **escopo**, **(v1.2.1) prevalência**, **(v1.2.3) quantificador** (ver acima) e **(v1.4.1) vocabulário do peso** — inalteradas pela reestruturação em movimentos da v1.3.0, elas operam sobre o texto final completo, independente de quantos movimentos o compõem. Todas com 1 retentativa combinada (reforço anexado ao prompt); se persistir, aceita e sinaliza a flag correspondente (`idioma_invalido`/`escopo_suspeito`/`prevalencia_suspeita`/`quantificador_suspeito`/`vocabulario_peso_suspeito`). As checagens sobre os campos **declarados** pelo narrador (`consensos_usados`, v1.3.1; `quantificadores_usados`, v1.4.1) entram na MESMA retentativa combinada — o orçamento do narrador continua sendo, no pior caso, 1 chamada + 1 retentativa de JSON + 1 retentativa de validação. Heurísticas **acento-sensíveis** como as demais (rede de segurança; a defesa principal é a invariante/pré-computação do prompt). A narrativa entra no JSON no campo global **`narrativa`** (+ `narrativa_flags` de telemetria).

**Telemetria de `consensos_usados` (v1.3.1, NOVO):** para cada propriedade que o narrador usar no MOVIMENTO 2, o próprio LLM declara `{propriedade, grupos_de_origem, temas_de_origem}` — `grupos_de_origem` restrito a `negativas`/`medianas`/`positivas`, `temas_de_origem` com os nomes de tema EXATOS (copiados do relatório recebido). Esse registro é o **artefato de revisão humana** de cada execução: permite conferir, tema a tema, se o consenso declarado é real (existe nos dados citados) ou inventado — o mesmo tipo de exercício feito manualmente no relatório da v1.3.0 que descobriu o defeito do `the-invite-2026`, agora com o material pronto em vez de precisar recomputar frações à mão.

Validação pós-parsing (código, não substitui a revisão humana): `_consensos_validos` (`synthesize.py`) confere que todo `grupos_de_origem` citado é um dos três nomes válidos E existe no relatório do filme, e que todo `temas_de_origem` citado corresponde a um tema real de algum dos grupos citados naquele item — comparação por igualdade de string com o nome do tema como veio no relatório. Falha em qualquer item → **1 retentativa combinada** com as demais (reforço anexado ao prompt, `_REFORCO_CONSENSOS`); se persistir, aceita a resposta da retentativa e sinaliza `consenso_suspeito: true` em `narrativa_flags` — telemetria visível, não correção silenciosa (mesma política das demais flags do §D2). `consensos_usados: []` é válido por vacuidade (MOVIMENTO 2 pode não ter nenhuma propriedade que passe nos três critérios).

`consensos_usados` é persistido no JSON do filme como campo global (junto de `narrativa`/`narrativa_flags`) e exibido no render de terminal, no tom `narrativo`/`ambos`, como bloco compacto após a prosa ("Consensos do movimento 2: • propriedade — grupos: ... — temas: ...") — visível em toda execução, não só sob demanda.

#### Telemetria de `quantificadores_usados` (v1.4.1, NOVO) — o quantificador declarado junto do seu tema

**O defeito (3ª ocorrência do MESMO modo de falha).** Na v1.4.0, a narrativa de `the-invite-2026` escreveu "Quase todos" para o tema `Atuações e química do elenco` (**20/30 = 67%**), cujo `rotulo_quantificador` pré-computado era **"a maioria"**. As duas defesas vigentes não pegaram:
- a **pré-computação** (v1.2.3) entrega o rótulo certo no relatório, mas não impede o modelo de escrever outra coisa na prosa;
- a **rede de segurança** (v1.2.3) é de **nível de bucket** — ela só pergunta se ALGUM tema do filme tem fração ≥80%. Outro tema do mesmo grupo (`Direção e roteiro (geral)`, 25/30 = 83%) dava lastro, e a checagem passou.

O buraco é estrutural: **nenhuma checagem sobre a prosa consegue saber a QUAL tema um "quase todos" solto se refere.** A correção segue o padrão que já resolveu o problema análogo do MOVIMENTO 2 (`consensos_usados`, v1.3.1): em vez de adivinhar, **o narrador declara**, e o código julga — o LLM continua sem decidir número nem rótulo (princípio da v1.1.1/v1.2.3).

**Formato.** A saída do narrador ganha `quantificadores_usados`: lista de `{quantificador, tema}` — **cada expressão de frequência usada na prosa**, declarada junto do **nome EXATO do tema** de onde ela vem (copiado literalmente do relatório recebido). Lista vazia é válida (a prosa pode não quantificar tema nenhum).

**Validação pós-parsing** (`_quantificadores_validos`, `synthesize.py`), par a par:
1. **Tema inexistente** no relatório (nenhum bucket tem um tema com esse nome exato) → violação.
2. **Quantificador MAIS FORTE** que o `rótulo_quantificador` pré-computado daquele tema → violação. A força da expressão declarada é resolvida por `_forca_declarada` sobre a mesma escala do prompt (`poucos` < `alguns`/`uma parte` < `muitos`/`boa parte` < `cerca de metade` < `a maioria`/`mais da metade` < `quase todos`/`praticamente todos`), casando por substring com a chave mais longa primeiro (`mais da metade` nunca é lido como `metade`). Quantificador **mais fraco** continua permitido (o prompt autoriza descer de força).

Violação em qualquer par → **1 retentativa** combinada com as demais validações de prosa (reforço `_REFORCO_QUANT_DECLARADO`); se persistir, aceita e sinaliza **`quantificador_suspeito: true`** — a flag **já existente** (v1.2.3) passa a ser alimentada por esta checagem **além** da de bucket, que permanece ativa e inalterada. Mesma política de telemetria visível das demais flags.

**Duas limitações deliberadas** (heurística, como as demais redes do §D2; a defesa principal é a instrução + pré-computação):
- **Expressão irreconhecível** (fora da escala, ex. "um punhado disperso") não é comparável e **não** conta como violação — não flaggar prosa possivelmente correta é preferível a flaggar por não entender.
- **Tema homônimo em mais de um grupo** (frações diferentes): o par declarado não diz de qual grupo veio, então a checagem resolve pela força **mais alta** entre os homônimos. Na ambiguidade, não flagga.

`quantificadores_usados` é persistido no JSON como campo global (junto de `narrativa`/`consensos_usados`) e exibido no render de terminal (tom `narrativo`/`ambos`) como bloco compacto, no mesmo padrão do bloco de consensos — e **com a conferência ao lado de cada par** ("• "quase todos" — tema: X (fração real 67% → rótulo: a maioria)"), porque o par sozinho não diria a um leitor humano se está inflado.

#### Invariante de vocabulário do peso (v1.4.1): **notas × reviews**

Duas populações **diferentes** alimentam a narrativa, e confundi-las é uma infidelidade silenciosa:

| | Origem | Denominador | Vocabulário obrigatório |
|---|---|---|---|
| **Rótulo de peso** (`rotulo_peso`, §3[G]) | histograma público de **NOTAS** | todo mundo que **avaliou** o filme | "**das notas**" |
| **Frequência de tema** (`rótulo_quantificador`, v1.2.3) | **REVIEWS COM TEXTO** analisadas (subconjunto) | `n_reviews_analisadas` do grupo | "das **reviews** analisadas" (regra d) |

Regra: ao expressar **peso**, é **OBRIGATÓRIO** dizer "das notas" e **PROIBIDO** dizer "das reviews", "dos espectadores" ou "do público" — o histograma não diz nada sobre quem escreveu review, nem sobre quem assistiu sem avaliar. As frequências de tema continuam expressas em relação às **reviews analisadas**. Os dois vocabulários não se misturam. A regra está escrita dentro da própria regra (c) invertida do prompt (variante COM distribuição — sem distribuição não há peso a expressar, e a invariante não existe).

**Checagem barata** (`_vocabulario_peso_ok`, `synthesize.py`), duas passadas literais sobre a prosa, só quando há distribuição:
1. **rótulos inequívocos de peso** (`uma pequena minoria`, `uma minoria`, `uma parcela expressiva`, `a grande maioria`) → inspeciona os ~40 chars seguintes; se aparecer "reviews"/"público"/"espectadores" **antes** de "notas", é violação;
2. **qualquer percentual** (`~79%`) → inspeciona os ~60 chars anteriores, com o mesmo teste.

A passada (2) existe porque **"a maioria" é ambígua**: é rótulo de peso E rótulo de quantificador de tema — e "a maioria das reviews negativas analisadas" é a forma **correta** exigida pela regra (d). Ancorar no percentual (que só acompanha peso, nunca frequência de tema na prosa) desambigua sem flaggar prosa certa. Violação → **1 retentativa** (reforço `_REFORCO_VOCABULARIO_PESO`); se persistir, **`vocabulario_peso_suspeito: true`** em `narrativa_flags`, visível no render.

**Flag `--tom {estruturado,narrativo,ambos}` — MECANISMO DE DESENVOLVIMENTO (não é feature final):** existe para o **teste A/B humano** entre a saída estruturada (atual) e a narrativa durante o desenvolvimento. `estruturado` (default) mantém o comportamento histórico intacto; `narrativo` imprime só a prosa **mas os metadados de coleta e os avisos NUNCA somem** — modo degradado (sem_analise/reduzido) e flags continuam visíveis nos dois tons; `ambos` imprime os dois lado a lado. `narrativo`/`ambos` gastam **+1 chamada LLM** (o narrador). **A v2 consolidará um tom único** após a avaliação humana do A/B; até lá, `--tom` é dev-only. (Atalho de A/B: `--reuse-synthesis` reaproveita a síntese de um JSON já gerado, gastando só a chamada do narrador — para comparar tons sobre a MESMA síntese.)

### [F] Ficha do filme (TMDB) — v1.3.0

Etapa **aditiva e independente** do resto do pipeline (`ficha.py`): dado o título/ano do filme (derivados do slug por default — `titulo_ano_de_slug`, com override via `--titulo`/`--ano` no CLI para os casos em que o slug não carrega ano, ex. `cure`), busca a ficha técnica na API pública do TMDB (`api.themoviedb.org/3`).

**Resolução do ID:** `GET /search/movie?query=<título>&language=pt-BR[&year=<ano>]`. Quando `ano` está disponível, é usado tanto como parâmetro de busca quanto para desambiguação pós-resposta: entre os candidatos com `release_date` no ano pedido, prefere o de maior `popularity` do TMDB — **não** o primeiro da lista. Necessário porque títulos comuns podem devolver mais de um candidato do MESMO ano (ex. "The Invite" tem múltiplas entradas no TMDB; "Cure" 1997 devolve o filme de Kiyoshi Kurosawa E um documentário obscuro do mesmo ano) — a ordem da API não é por relevância quando o filtro de ano está ativo. Medido ao vivo na regeneração da v1.3.0: escolher o primeiro resultado do ano pegou o documentário (`popularity=0.28`, 1 voto) em vez do filme correto (`popularity=3.79`, 820 votos); corrigido para desempate por popularidade antes da entrega.

**Resolução de ano confiável (v1.7.0) — Tarefa 1.** Defeito real: `espectro24 --slug cure` sem `--ano` desambiguava só pelo TÍTULO (nenhum ano para filtrar), e o TMDB devolveu como único candidato "The Cure" (2026, dir. Nancy Leopardi) — um filme completamente diferente — sem nenhum aviso. A cadeia de resolução do ano passa a ter três degraus, nesta ordem, cada um só tentado se o anterior não resolveu: **(a)** sufixo `-YYYY` do slug (`titulo_ano_de_slug`, já existia); **(b)** se ausente, **1 requisição** à página principal do filme no Letterboxd (`resolver_ano_letterboxd`, `ficha.py`) — mesmo `fetcher`/cache/headers/delay do resto do pipeline, extrai o ano do link `/films/year/YYYY/` ou do `<meta property="og:title">` (formato "Título (YYYY)"); falha de rede/ausência de ano → `None`, nunca levanta; **(c)** se AINDA assim indisponível, a ficha **não é buscada** — o pipeline segue sem ela (`output["ficha"] = None`, `output["ficha_indisponivel"] = "ano_desconhecido"`) em vez de arriscar a desambiguação cega que causou o defeito. O campo `ano_fonte` (`"slug" | "letterboxd" | "argumento"`) entra na própria ficha, sempre visível.

**Guarda de sanidade — ano divergente descarta a ficha inteira (v1.7.0, Tarefa 1.2).** Mesmo com ano resolvido, o TMDB pode devolver o candidato errado quando NENHUM resultado da busca tem `release_date` no ano pedido (o código então cai para o primeiro resultado da lista, que pode ser de qualquer ano — o próprio modo de falha do defeito real do `cure`). Depois de montar a ficha, se o ano esperado (nunca o do próprio resultado do TMDB — seria circular) divergir do `ano` da ficha em mais de 1, a ficha inteira é DESCARTADA: `buscar_ficha` retorna `(None, aviso, {"motivo": "ano_divergente", "esperado": X, "recebido": Y})`, e o CLI persiste esse dict em `output["ficha_descartada"]`. Melhor nenhuma ficha do que a ficha de outro filme. A ficha descartada por esse motivo NÃO é cacheada como "não encontrado" — uma nova tentativa (ex. com um título mais preciso) não fica travada numa rejeição antiga.

**Detalhes:** `GET /movie/{id}?language=pt-BR&append_to_response=credits`. Extraídos: título pt-BR (`title`), sinopse oficial (`overview`), gêneros (`genres[].name`), duração (`runtime`), diretor (primeiro `credits.crew[]` com `job == "Director"`), ano (`release_date[:4]`).

**Diretor em escrita latina (v1.6.0):** o TMDB devolve o nome do diretor no **alfabeto nativo** quando a localidade pt-BR não tem tradução — `cure` vinha com `"黒沢清"`, que foi parar na narrativa **publicada** (o narrador só reproduz o que a ficha entrega). Quando o nome pt-BR não está em escrita latina (`_e_escrita_latina`, checagem sobre `unicodedata.name` de cada letra — cobre diacríticos latinos como ç/é/ñ sem lista de exceções), o `credits` de `en-US` é consultado e a transliteração é usada (`"Kiyoshi Kurosawa"`). A ficha carrega `diretor_transliterado: true` — visível, nunca silencioso. **Custo:** no máximo 1 requisição extra, e só para filmes nessa condição; quando o fallback de sinopse já buscou `en-US`, a resposta é **reaproveitada** em vez de refeita. Se o `en-US` também não for latino, mantém o nome original (melhor um nome em alfabeto nativo do que nenhum). Cacheado junto da ficha, como todo o resto.

**Fallback de sinopse:** se `overview` vier vazio na resposta pt-BR (acontece para filmes com localização incompleta no TMDB), uma segunda chamada com `language=en-US` busca o overview em inglês; a ficha carrega esse texto com a flag `sinopse_fallback_en: true` — nunca fica silenciosamente vazia, mas também nunca finge ser pt-BR quando não é.

**Cache em disco** (mesmo padrão do cache do Letterboxd em `fetcher.py`, raiz própria `<cache-dir>/_tmdb/`): chave determinística por `título_normalizado[_ano]`; nunca rebusca filme já buscado, inclusive "não encontrado" (evita reconsultar buscas vazias). Diferente do cache de rede do Letterboxd, falhas transitórias (rede, HTTP não-200) **não são cacheadas** — podem ser passageiras, vale tentar de novo na próxima execução; só resultado de sucesso ou "sem resultado" persistem.

**Falha nunca bloqueia (decisão de design central desta etapa):** chave ausente, erro de rede, HTTP não-200, filme não encontrado, ou ano indisponível/divergente → `buscar_ficha` retorna `(None, aviso, ficha_descartada)` (v1.7.0 — terceiro elemento da tupla, `None` nos casos que não são divergência de ano). O CLI imprime o aviso em stderr, persiste `ficha_descartada` no JSON quando presente, e segue o pipeline inteiro (coleta, síntese, narrador, render) com `output["ficha"] = None`. Nenhuma exceção de `ficha.py` escapa para o `main()` do CLI.

**Saída:** campo global `ficha` no JSON (§4), formato:
```json
{
  "titulo": "Cure", "sinopse_oficial": "...", "sinopse_fallback_en": false,
  "generos": ["Suspense", "Terror"], "duracao_min": 111,
  "diretor": "Kiyoshi Kurosawa", "ano": 1997, "fonte": "tmdb"
}
```
`null` quando a ficha não foi obtida (busca falhou, `--no-ficha`, ou filme não encontrado).

**Consumo:** a ficha (quando presente) é serializada para o narrador (§D2) como fonte exclusiva do MOVIMENTO 1; fora do modo narrativo, o render estruturado/terminal também exibe um resumo de uma linha da ficha, quando existe (título/ano/diretor/gênero/duração), separado dos buckets e sem interferir nos avisos existentes.

### [G] Distribuição real de notas (histograma do Letterboxd) — v1.4.0

Etapa **aditiva e independente**, irmã da ficha TMDB (§F): não depende das
reviews coletadas e não é bloqueada por elas. Detalhes de sondagem, seletores
e armadilhas em **`FASE_HISTOGRAMA.md`**.

**Endpoint:** `letterboxd.com/csi/film/<slug>/rating-histogram/` — fragmento CSI
server-rendered, **1 requisição por filme**, cacheada em
`<cache-dir>/_histograma/<slug>.html`. Preferido à página principal do filme
por ser ~5,8 KB em vez de centenas, expondo exatamente o dado desejado.

**Estrutura (validada ao vivo):** `table.chart tbody tr` × **10** (sempre 10,
um por nível de 0.5 a 5, em ordem crescente). Nível em `th._sr-only` (glifos:
`half-★`, `★`, `★½`, …). **Contagem exata no atributo `title` do `.barcolumn`.**

Três armadilhas, todas tratadas (ver `FASE_HISTOGRAMA.md` §3):
1. **Nível zerado não tem `<a>`** — vira `<span class="barcolumn" title="No ★½ ratings">`.
   Buscar `a.barcolumn` perderia os zeros **em silêncio** e inflaria o total,
   justamente em filmes pequenos (onde o denominador é mais frágil). O seletor
   é `.barcolumn`, qualquer tag.
2. **O `_sr-only` da barra ABREVIA** (`23.4K`, `111K`) — inútil como fonte. O
   `title` traz o número exato.
3. **Singular/plural e "No"** — `456 … ratings`, `1 … rating`, `No … ratings`.

**Agregação (código, não prompt):** `share_real` por bucket =
`soma dos níveis do bucket / total`, em **percentual inteiro**. Cada bucket é
arredondado **independentemente**, para que o número de cada grupo seja a
melhor aproximação inteira do seu próprio share. **Consequência aceita e
documentada:** a soma dos três pode dar 99 ou 101 (ex.: `cure` → 3+17+79=99).
Preferido a redistribuir o resto, o que tornaria algum bucket menos fiel ao
próprio dado — coerente com a política do projeto de não maquiar número. A
interface **nunca exibe a soma**.

**A cota NÃO passa a seguir o peso** (decisão explícita, reafirmada na
v1.9.0). Racional: cota e peso respondem a perguntas diferentes e ambas
continuam necessárias.
- A **cota** é *amostragem estratificada*: garante **profundidade igual por
  perspectiva**. Quem quer saber o que incomodou o grupo minoritário precisa de
  ~40 reviews negativas lidas, não de 1 review porque só 1% deu nota baixa.
  Reduzir a amostra do grupo pequeno destruiria a análise temática justamente
  onde ela é mais informativa para a decisão de assistir.
- O **peso** é a prevalência real, e está exibido separadamente.

Ou seja: **profundidade igual, peso informado** — que é o princípio norteador
(§0) aplicado à coleta.

> **v1.9.0 — o que mudou, e o que deliberadamente não mudou.** A cota **entre**
> buckets deixou de ser 50/20/30 e passou a ser **40/40/40** (§0): o desenho
> antigo já pretendia profundidade igual, mas entregava 5/2/3 níveis × 10, que é
> aritmética de escala, não decisão de profundidade. **Dentro** de cada bucket,
> ao contrário, o histograma passa a mandar (§3[C1]) — porque ali a pergunta é
> outra: distribuir 40 vagas entre 4 níveis do MESMO grupo por cota igual
> super-representa os extremos, sem nenhum ganho de perspectiva. Em uma frase:
> **peso informa a composição DENTRO do grupo; nunca o tamanho ENTRE grupos.**
> É a mesma fronteira da v1.4.0, aplicada um nível abaixo.

**Consequência de vocabulário (v1.4.1) — o histograma conta NOTAS, não
reviews.** O denominador de `share_real` é `n_notas_total`: **todo mundo que
avaliou** o filme. Os temas, por outro lado, saem das **reviews com texto**
que passaram nos filtros (§C) — um subconjunto muito menor da mesma
população. As duas coisas nunca compartilham denominador, e por isso o
produto **nunca** apresenta um rótulo de peso como se fosse sobre reviews,
espectadores ou "o público": um rótulo de peso é sempre "**das notas**". A
regra completa, com a checagem que a defende no narrador, está em §D2
("Invariante de vocabulário do peso"); o render de terminal e o frontend já
seguiam esse vocabulário desde a v1.4.0 (`· ~X% das notas`).

**Falha nunca bloqueia** (idêntico a §F): chave estrutural inesperada, rede,
HTTP, anti-bot ou filme sem nota alguma → `collect_distribuicao` retorna `None`,
o campo sai `null` e **todo o resto do pipeline degrada sozinho** para o
comportamento da v1.3.1 (ver "Fallback" no §D2). Nem `AntiBotError` escapa:
perder a distribuição não justifica abortar uma coleta que já custou dezenas de
requisições.

**Saída** (§4): bloco global `distribuicao` + `share_real` por bucket.
```json
{
  "n_notas_total": 375278,
  "por_nivel": {"0.5": 456, "1.0": 1037, "…": 0, "5.0": 99242},
  "por_bucket": {"negativas": 3, "medianas": 17, "positivas": 79},
  "fonte": "letterboxd_histograma"
}
```
`share_real` é **omitido** (chave ausente, não `0`) quando não há distribuição —
o consumidor distingue "não coletado" de "coletado e deu 0%".

**Flag `--no-distribuicao`** pula a busca (e cai no fallback), para A/B.

### [E2] Editor — passe de EDIÇÃO da narrativa (v1.6.0, NOVO)

Etapa **PÓS-narrador**, ativa junto com `--tom narrativo|ambos`, desligável com `--no-edicao`. **Uma única chamada LLM por filme** (+1 sobre o custo da v1.5.0), mesmo provider/modelo, na configuração de prosa (§2: `thinking_budget=4096`, `max_output_tokens=16000`).

**O princípio: separar o que não devia ter sido empilhado.** Até a v1.5.0, um único prompt respondia por honestidade (números, rótulos, atribuição, anti-spoiler) **e** por fluência (ritmo, registro). Falhou nas três frentes documentadas no §D2. A v1.6.0 separa:

| | Narrador §D2 | Editor §E2 |
|---|---|---|
| Responde por | **verdade** e estrutura | **leitura** e ritmo |
| Recebe | relatório validado + ficha | **só o texto + trechos protegidos** |
| Pode inventar fato? | não (só usa o relatório) | **não tem como** — não recebe fonte de fato |
| Pode alterar número? | não escolhe número (pré-computado) | **não** — verificado mecanicamente |

**Decisão de arquitetura (invariante):** o editor recebe **EXCLUSIVAMENTE** o texto da narrativa validada e a lista de trechos protegidos. **Não recebe** o JSON dos buckets, nem as reviews, nem a ficha, nem os temas. A garantia anti-invenção é **estrutural, não uma instrução**: o que não está na entrada, o editor não tem como saber. É a mesma fronteira que o §D2 estabelece para o narrador, apertada mais um nível.

#### Trechos protegidos (montados em CÓDIGO, `montar_protegidos`) — ENXUGADOS na v1.7.0

O editor nunca escolhe o que é intocável. A lista sai do que o narrador **já declarou**:

1. **Rótulos de peso, SEMPRE com percentual** — a forma canônica e as mais fracas permitidas (`"a grande maioria das notas (~79%)"`); a forma nua sem percentual (`"a grande maioria das notas"`) **saiu** na v1.7.0 — ver abaixo;
2. **Todo token que contenha dígito** (percentuais, anos, durações).

Até a v1.6.2, a lista também incluía (2) as expressões de quantificador declaradas em `quantificadores_usados` e (3) as expressões de atribuição dos `marcadores_perspectiva`. **A v1.7.0 (Tarefa 2) removeu as duas.** Defeito real: com 14-16 protegidos por filme — incluindo palavras soltas como "muitos" —, o editor era descartado com frequência (`cure`, 2 protegidos perdidos mesmo após retentativa) ou inventava frases penduradas só para reencaixar um protegido que mudou de lugar (`cidade-de-deus`: *"Essa é a opinião de uma fração mínima das notas."*, sem função nenhuma além de conter a string exigida). Pior: um defeito gramatical real da narrativa bruta — *"destacando a a maioria o estilo visual"* — **sobreviveu à edição** porque "a maioria" estava na lista de protegidos, e o editor não ousou tocar na frase.

A remoção é segura porque as duas coisas removidas **já tinham verificação semântica melhor do que a comparação literal**, preexistente e mais forte:
- **Quantificador** — `conferencia_quantificador` (v1.4.1) confere o PAR declarado (`{quantificador, tema}`) contra o rótulo pré-computado da fração real; não exige que a STRING sobreviva, só que a afirmação continue certa.
- **Atribuição de perspectiva** — `_marcadores_validos` (v1.6.1) varre o MOVIMENTO de cada grupo em busca de qualquer expressão de atribuição reconhecida; não exige que a string DECLARADA sobreviva, só que alguma expressão válida exista onde precisa. **v1.7.0 estende essa checagem para dentro do próprio `editar_narrativa`**: o estado de `_marcadores_validos` sobre o texto bruto é comparado ao mesmo sobre o texto editado, e uma regressão (válido → inválido) entra no mesmo mecanismo de regressão de honestidade que já existia para idioma/escopo/prevalência/vocabulário/ancoragem — motivo `"perspectiva_nao_marcada"` no descarte.

Proteger a STRING era redundante com uma checagem melhor, e engessava a reescrita sem ganhar nada em honestidade — a checagem semântica já cobria o que importa.

Dois cuidados de implementação, ambos motivados por comportamento real (continuam valendo para o que ainda é protegido):
- **Só entram candidatos que REALMENTE ocorrem no texto do narrador.** Proteger uma string ausente tornaria a checagem impossível de satisfazer — o editor seria punido por algo que o narrador não escreveu. Em `cidade-de-deus` (v1.5.0) o narrador declarou um marcador que ele mesmo não reproduziu literalmente.
- **O protegido é a forma COMO APARECE no texto**, não a canônica: o narrador capitaliza no início de frase ("A grande maioria das notas (~79%)") enquanto o rótulo canônico é minúsculo. A busca casa ignorando caixa e guarda a fatia real.
- **Tokens numéricos entram SEM a pontuação em volta** (`~3%`, não `(~3%),`): blindar parêntese e vírgula impediria o editor de repontuar, que é metade do trabalho de ritmo.

##### Exceção de capitalização na checagem de trecho perdido (v1.7.1)

Defeito real: o rótulo protegido guarda a caixa de onde apareceu a **primeira vez** — em início de frase, capitalizado ("A grande maioria das notas (~91%)"). Quando o editor move o rótulo para o **meio** de um período reescrito ("Para a grande maioria das notas (~91%), ..."), a letra inicial deveria virar minúscula — mas a checagem, sendo 100% literal, tratava isso como perda do protegido. Publicado ao vivo em `cidade-de-deus` (v1.7.0): "Para A grande maioria...", "Já Uma pequena minoria...", maiúscula incorreta no meio da frase, porque o editor não ousou ajustar por medo do descarte.

`_protegido_presente` (`synthesize.py`) agora aceita o trecho tanto na forma literal quanto com **só a primeira letra** em caixa alternada (`_variante_primeira_letra`) — nenhuma outra letra, palavra, número ou pontuação ganha essa folga. O prompt do editor (regra INVIOLÁVEL — TRECHOS PROTEGIDOS) ganhou uma exceção explícita autorizando esse ajuste específico. Testado nos dois sentidos: caixa ajustada é aceito; qualquer outra palavra alterada (mesmo pequena) continua sendo perda; número alterado continua descartando mesmo com a caixa "corrigida" no processo.

##### Conflito histórico (v1.6.0, superado pela v1.7.0): proteger marcadores × corrigir gramática

Descoberto num ensaio ponta a ponta sobre o `cure` **publicado**, antes de qualquer chamada real: o narrador havia declarado, como `trecho` do marcador de `negativas`, **o próprio período agramatical** — *"Uma pequena minoria das notas (~3%), para quem o filme é superestimado e pretensioso, a maioria considerou o ritmo…"*. Proteger o período inteiro (ou mesmo só a expressão de atribuição dentro dele, solução da v1.6.0) tornava as regras do §E2 tensas: o editor que reescrevesse em volta de um protegido corria o risco de ter de inventar contexto para reencaixá-lo. A v1.7.0 resolve pela raiz: a atribuição não é mais protegida por STRING nenhuma — só pela checagem semântica (`_marcadores_validos`, ver acima), que valida a EXISTÊNCIA da atribuição, não a sobrevivência de uma redação específica. **A regra de gramática obrigatória (§E2, "GRAMÁTICA") ganhou uma frase explícita (Tarefa 2.4):** corrigir "a a"/"de de"/artigo repetido é obrigatório mesmo quando o defeito encosta num trecho protegido, desde que o protegido em si (o rótulo de peso ou o número) permaneça intacto por dentro.

#### Prompt do editor (SPEC — texto oficial, `_EDITOR_SYSTEM_PROMPT` em `synthesize.py`)

> Você é um EDITOR de texto. Recebe um texto pronto sobre a recepção de um filme e o reescreve para que ele SOE MELHOR — sem mudar nada do que ele diz.
>
> Você NÃO tem acesso aos dados de origem. Tudo o que você pode afirmar já está no texto recebido; não há nada a acrescentar, e você não teria como verificar nada que inventasse.
>
> **REGRA INVIOLÁVEL — TRECHOS PROTEGIDOS:** junto do texto você recebe uma lista de TRECHOS PROTEGIDOS. Cada um deles precisa aparecer no seu texto final EXATAMENTE como foi entregue — mesmos caracteres, mesma pontuação, mesmos números, sem reformulação, sem sinônimo, sem reordenar as palavras dentro do trecho. Você pode mover um trecho protegido para outro ponto da frase ou do parágrafo, e pode reescrever tudo em volta dele; o que não pode é alterar o trecho por dentro. Se uma melhoria de ritmo exigir quebrar um trecho protegido, NÃO faça a melhoria — o trecho vence. EXCEÇÃO ÚNICA (v1.7.1): se mover um trecho protegido para o meio de uma frase deixar a letra inicial dele com a caixa errada (maiúscula que devia virar minúscula, ou o contrário), você PODE ajustar só essa primeira letra — nenhuma outra letra, palavra, número ou pontuação do trecho.
>
> **TAMBÉM PROIBIDO:** adicionar, remover ou alterar QUALQUER número ou percentual, mesmo fora dos trechos protegidos; adicionar, remover ou alterar nome próprio (de pessoa, filme, lugar); adicionar, remover ou alterar qualquer afirmação factual — se o texto diz que um grupo achou o ritmo lento, o seu texto diz a mesma coisa; acrescentar informação que não esteja no texto recebido, inclusive conhecimento seu sobre o filme; trocar a quem uma opinião é atribuída.
>
> **RITMO:** alterne períodos longos (30-50 palavras) com frases curtas (3-10 palavras); o texto final precisa ter pelo menos UMA frase de até 10 palavras; não abra dois períodos seguidos com a mesma estrutura; use conectivos de fala ("só que", "aí", "já", "e", "mas"), podendo iniciar período por conjunção.
>
> **REGISTRO:** prefira verbos a nominalizações ("as situações se repetem e o filme cansa", não "a repetição das situações torna a experiência cansativa"); no máximo UM advérbio terminado em -mente no texto inteiro; reduza verbos de reporte (elogia, destaca, aponta, relata, considera, classifica, menciona, ressalta, reconhece) quando já estiver claro de quem é a opinião — MAS nunca à custa de um trecho protegido, e nunca apagando a atribuição de quem pensa o quê.
>
> **TOM:** alguém contando de um filme para um amigo. Fluido e leve, mas SEM gíria, SEM emoji, SEM interpelação direta ao leitor ("você vai adorar"), SEM hipérbole, SEM aspas de citação.
>
> **GRAMÁTICA (obrigatório):** cada período do texto final precisa ser uma frase completa e correta em português do Brasil — sujeito e predicado coerentes, concordância certa, sem anacoluto. Se o texto recebido contiver um período quebrado ou truncado, CORRIGI-LO É OBRIGATÓRIO; essa é a única situação em que você reescreve a estrutura de uma frase por necessidade, e mesmo assim preservando o que ela afirma e os trechos protegidos que ela contém.
>
> **TAMANHO:** entre 220 e 400 palavras.
>
> **EXEMPLO DE RITMO COM FILME FICTÍCIO** — nunca reaproveitar seu conteúdo. O filme abaixo NÃO EXISTE e os números são INVENTADOS: servem só para mostrar a FORMA. Copiar qualquer fato, adjetivo ou número daqui seria inventar informação.
>
> ANTES (ritmo monótono): "A grande maioria das notas (~74%) elogia intensamente a condução do filme e o trabalho de câmera, destacando a habilidade de sustentar o clima em cena. Uma minoria das notas (~19%) reconhece a competência técnica, mas sente que a indefinição do meio e a duração prolongada tornam a experiência cansativa na segunda metade. Uma pequena minoria (~7%) classifica o ritmo como arrastado e os personagens como estáticos."
>
> DEPOIS (ritmo desejado — mesmos fatos, mesmos números, mesma atribuição): "Quem gostou é a grande maioria das notas (~74%), e o elogio se concentra num ponto só: o filme não tem pressa e usa isso a favor, porque cada silêncio entre os dois protagonistas pesa mais que a cena anterior. Uma minoria das notas (~19%) chega até a metade junto. Para esse grupo, o problema aparece quando a história precisa decidir para onde vai, e não decide. Já uma pequena minoria (~7%) não embarca em momento nenhum. Para eles a lentidão nunca vira método, os personagens não saem do lugar, e o final chega sem ter construído nada."
>
> Responda APENAS com o texto final editado. Sem preâmbulo, sem explicação, sem JSON, sem aspas envolvendo o texto.

**A regra de gramática não é decorativa:** a v1.5.0 publicou, na configuração de produção, a frase *"Muitos para eles, há uma falta de tensão ou mistério…"* (`cure`, célula flash/thinking-off do diagnóstico) e um anacoluto no `cure` publicado (*"Uma pequena minoria das notas (~3%), para quem o filme é superestimado e pretensioso, a maioria considerou o ritmo…"*). Corrigir período quebrado é a única reescrita estrutural que o editor tem **obrigação** de fazer.

#### Verificação mecânica da saída do editor (código, não prompt)

Sobre o texto editado, nesta ordem:

**(a) Trechos protegidos** — cada um precisa aparecer **literalmente**. Aqui a comparação é literal de propósito (ao contrário da checagem de marcadores do §D2): o ponto é justamente que o editor não reformule.
**(b) Conjunto numérico** — o multiconjunto ordenado de tokens numéricos (`_tokens_numericos`) do texto editado deve ser **idêntico** ao do original. Nenhum número novo, nenhum removido, nenhum alterado. Como todo token com dígito também é protegido por (a), esta checagem é a **segunda rede**: pega sobretudo número **inventado**, que (a) não veria.
**(c) Honestidade reexecutada** — as validações do §D2 que fazem sentido sobre texto livre (idioma, aspas, escopo, prevalência, vocabulário de peso, ancoragem de peso) rodam de novo sobre o texto editado. A comparação é **contra o estado do texto original**: a edição não pode **regredir** (e não é obrigada a consertar o que já vinha marcado do narrador).

Falha em qualquer uma → **1 retentativa** com reforço (listando os trechos perdidos e/ou cobrando o conjunto numérico). Se persistir, a edição é **DESCARTADA** e a narrativa original do narrador prevalece, com `edicao_descartada: true` e `motivo_descarte` em `edicao_flags`.

> **A garantia que isso compra:** o editor **pode não melhorar** o texto — pode ser descartado e não entregar ganho nenhum. O que ele não pode, em hipótese alguma, é **piorá-lo**. Toda propriedade de honestidade conquistada da v1.1.1 à v1.5.0 sobrevive ao estágio novo por construção, não por confiança no modelo.

**Persistência (§4):** `narrativa` passa a ser o texto **final** (editado); `narrativa_bruta` guarda a saída do narrador para auditoria; `metricas_fluencia` passa a ser calculada sobre o texto final; `edicao_flags` carrega o resultado das checagens. O render de terminal exibe uma linha de status da edição (aplicada / descartada com motivo e trechos perdidos).

### [E] Render
1. `resultado/<slug>.json` — objeto completo: 3 buckets + metadados por nível e globais.
2. Terminal — por bucket: título, `n_validas/alvo` (com decomposição por nível quando houver nível degradado), filtro aplicado, temas com frequência relativa ("mencionado em ~14 de 50 reviews"), observação geral. Avisos de modo reduzido/degradado sempre visíveis e concretos ("análise negativa baseada em apenas 7 de 50 reviews-alvo — interprete com cautela").
3. Rodapé: contagem total de reviews observada, para distinguir "bucket vazio porque ninguém odeia" de "bucket vazio porque ninguém assistiu".
4. **(v1.4.0)** Header do grupo ganha `· ~X% das notas` quando há distribuição — **formato e estilo idênticos nos três grupos** (§0: a assimetria vem do dado, não da apresentação). O disclaimer da seção tema-a-tema tem duas variantes, escolhidas pela presença do dado (constantes `DISCLAIMER_*` em `render.py`, mantidas em sincronia com o frontend):
   - **sem** distribuição: *"grupos de 40 · 40 · 40 reviews são cotas de coleta — não a proporção real das opiniões"*
   - **com** distribuição: *"análise em profundidade igual por grupo (40 · 40 · 40 reviews); o peso real de cada faixa está indicado em cada grupo"*

   **(v1.9.0)** Os números destes dois textos são **derivados de `BUCKET_ALVO`**, não literais — a v1.9.0 mudou a cota, e um disclaimer com o número antigo seria uma afirmação falsa sobre o método na cara do leitor. **PENDÊNCIA RESOLVIDA NA v1.9.1:** `frontend/js/filme.js` tinha os mesmos dois textos com "50 · 20 · 30" hardcoded — corrigido para ler `f.buckets[i].alvo` do próprio JSON de resultado (o campo já existe desde a v1.1.0; o frontend não tem acesso a `config.py`, então lê do dado, não de uma constante compartilhada) em vez de repetir o número.

   O frontend (`frontend/`) aplica exatamente o mesmo tratamento e **tolera JSONs sem `distribuicao`** (filmes antigos/fallback) sem quebrar: omite os shares e usa o disclaimer antigo. Ordem visual dos grupos permanece negativas → medianas → positivas em qualquer caso — **a ordem não é reordenada por peso**; quem muda de ordem é só a prosa do MOVIMENTO 3.

---

## 4. Metadados obrigatórios no output

Por nível: `n_validas`, `n_brutas`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_descartadas_truncamento` (**v1.9.0: sempre 0** — uma truncada não resolvida não é mais *descartada*, ela fica no bruto marcada `texto_completo: false`; o número que importa passou a ser `n_indisponivel_truncamento`. O campo permanece para não quebrar consumidores existentes), `paginas_buscadas`, **(v1.9.0)** `n_alvo` (a alocação de §3[C1] para aquele nível — é o "ALVO" da ressalva 2, e sem ele a composição atingida não é interpretável), `n_indisponivel_truncamento` (persistidas mas inelegíveis por texto incompleto), **(v1.9.1)** `motivos_descarte` (dict `motivo→n` — §3[C2]; `n_descartadas_spoiler`/`n_descartadas_curtas`/`n_indisponivel_truncamento` passam a ser derivados dele, uma única fonte de verdade).
Por bucket: agregados dos níveis + `modo` (completo/reduzido/sem_analise) + **(v1.1.2)** `idioma_invalido`, `escopo_suspeito` + **(v1.9.0)** `estado_piso` (`completa`/`sem_quantificador`/`sem_numero`/`sem_analise`, §3[C3]), `composicao_alvo` e `composicao_atingida` (dicts nível→n, lado a lado — a mitigação obrigatória da ressalva 2 de §3[C1]), `cascata_por_degrau` (dict `chars`→n, quantas reviews entraram por cada degrau do relaxamento), `deficit_redistribuido` (int), **(v1.9.2)** `distribuicao_pagina_origem` (`{n, min, max, p5, p50, p95, fracao_profunda}` sobre a amostra SELECIONADA daquele bucket — §3[B'], instrumento temporal primário).
**(v1.9.0, campos ajustados nas v1.9.1/v1.9.2)** Bloco global `coleta`: `{ordenacao_usada, versao_coletor, coletado_em, paginas_gastas_por_nivel, paradas_por_limite, contagem_bruta_por_nivel, contagem_estimada_valida_por_nivel, n_reviews_bruto}` — espelha o `meta.json` do bruto (§3[B']) dentro do resultado, para que um JSON de entrega seja auditável sem abrir `dados/`. **(v1.9.1)** ganha `orcamento_paginas_por_nivel` (o orçamento dado a cada nível, derivado do orçamento por bucket — §3[B]) e `janela_temporal` (`{total, por_bucket}`, cada bloco `{n, min, max, p5, p50, p95}` — §3[B'], SECUNDÁRIA e rotulada como proxy contaminado desde a v1.9.2, não consumida pelo frontend). **(v1.9.2)** ganha `motivo_parada_por_nivel` (dict nível→`"orcamento_esgotado"`\|`"material_esgotado"` — §3[B], substitui `paradas_por_limite` como fonte primária de telemetria de parada; `paradas_por_limite` permanece, derivado, para não quebrar consumidores).
Por tema: **(v1.1.2)** `aspas_removidas`, além de `mencoes_clampadas`/`mencoes_valor_original` (v1.1.1).
Globais: `slug`, `data_coleta`, `origem` (cache/rede por página), versão da spec, **(v1.1.4)** `reviews_url`, **(v1.2.0)** `narrativa` + `narrativa_flags` (só quando `--tom narrativo|ambos`), **(v1.3.0)** `ficha` (objeto TMDB ou `null` — §3a), **(v1.3.1)** `consensos_usados` (lista de `{propriedade, grupos_de_origem, temas_de_origem}` do MOVIMENTO 2 — só quando `--tom narrativo|ambos`) + `narrativa_flags.consenso_suspeito`, **(v1.4.0)** `distribuicao` (bloco do histograma ou `null` — §3[G]) + `narrativa_flags.peso_nao_ancorado`, **(v1.4.1)** `quantificadores_usados` (lista de `{quantificador, tema}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.vocabulario_peso_suspeito`, **(v1.5.0)** `marcadores_perspectiva` (lista de `{grupo, trecho}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.perspectiva_nao_marcada`, `metricas_fluencia` (`{n_frases, media_palavras, cv_comprimento, frase_mais_curta, aberturas_repetidas, verbos_reporte, adverbios_mente}` — só quando `--tom narrativo|ambos`), **(v1.6.0)** `narrativa_bruta` (saída do narrador antes da edição, para auditoria) + `edicao_flags` (`{edicao_descartada, motivo_descarte, protegidos_perdidos, numeros_alterados, houve_retentativa, falhou, n_protegidos}` — só quando `--tom narrativo|ambos` e sem `--no-edicao`; **(v1.7.3)** `n_tentativas` (quantas chamadas o editor fez, 1 a `1 + EDITOR_MAX_TENTATIVAS`) e `motivos_por_tentativa` (lista do motivo de cada falha, na ordem — telemetria de qual checagem mais reprova, não critério de aprovação); **(v1.7.4)** `similaridade` (float 0-1, SEMPRE presente, aceita ou não a edição) e `capitalizacao_ajustada` (bool)). **A flag `narrativa_flags.fluencia_baixa` foi REMOVIDA na v1.6.0** (ver §D2, "Telemetria de fluência"). Na ficha: **(v1.6.0)** `diretor_transliterado` (bool), **(v1.7.0)** `ano_fonte` (`"slug" | "letterboxd" | "argumento"`). Globais **(v1.7.0)**: `ficha_indisponivel` (`"ano_desconhecido"` — presente só quando a ficha não foi buscada por falta de ano confiável, §3[F]) e `ficha_descartada` (`{motivo, esperado, recebido}` — presente só quando o TMDB resolveu para um filme de ano divergente e a ficha inteira foi rejeitada, §3[F]); ambos ausentes do JSON no caminho normal (ficha resolvida com sucesso ou `--no-ficha`).
Por bucket: **(v1.4.0)** `share_real` (percentual inteiro), **omitido** quando não há distribuição.

---

## 5. Critérios de aceite da v1

1. Filme popular (ex: `oppenheimer-2023`): **os três buckets em `estado_piso: completa` com os 40 preenchidos** (v1.9.0; era "10 níveis completos, 10 válidas cada"), temas coerentes, zero spoilers na saída (verificação manual).
2. Filme de fanbase "review curta" (ex: `cidade-de-deus`): o filtro de comprimento descarta reviews curtas em volume, a coleta fecha os níveis dentro do teto de paginação, e a análise permanece útil com observações corretamente escopadas. *(Reescrito em v1.1.4 — ver nota abaixo; o critério original presumia cascata de relaxamento/modo degradado, que `cidade-de-deus` não aciona por ser coberto demais por nível. A demonstração da cascata e do modo degradado é atribuída ao critério 3, onde ocorre de fato.)*
3. Filme obscuro (a escolher): modo degradado severo — piso de 3 por bucket respeitado, bucket sem análise renderiza aviso (contagem + `reviews_url`) e não inventa temas; a cascata de relaxamento por nível (`filtro_aplicado` assumindo 50/0) é exercitada aqui.
4. **Nenhum texto truncado chega ao LLM:** teste com filme contendo reviews longas colapsadas; verificar que todas as reviews enviadas ao LLM têm texto completo ou foram descartadas com registro.
5. Segunda execução de qualquer filme: **zero requisições de rede** (100% cache).
6. Orçamento de requisições por filme novo — **reescrito na v1.9.1**: teto absoluto de **paginação** = **48** (3 buckets × 16 páginas de orçamento — era 40 = 10 níveis × 4 na v1.9.0, computado por nível; a v1.9.1 muda a unidade de contagem para bucket, não o gasto real, que segue medido, não projetado), + 1 histograma + truncadas completadas + busca de slug. **Valor típico MEDIDO sob a v1.9.0 (2026-08-07, 3 filmes): 58-65, média 61** — 32-33 de paginação, 24-33 de completamento, 1 de histograma; abaixo dos 83 (`cure`) e 68 (`cidade-de-deus`) da v1.8.2, apesar de ~50% mais material bruto coletado. **Valor MEDIDO sob a v1.9.1, recoleta INCREMENTAL sobre o bruto da v1.9.0 (2026-08-07, 3 filmes): 17-26, média 21** — não comparável 1:1 com os 61 da v1.9.0 (que foi coleta do zero); é o custo real de alargar uma coleta já existente para o orçamento maior, o caso de uso que a incrementalidade do bruto (§3[B']) foi desenhada para servir. Tabela completa e o achado residual (`cidade-de-deus`/`medianas` fechou 37/40, não 40/40) em §3[B], "Resultado MEDIDO da recoleta v1.9.1". **Valor ESPERADO sob a v1.9.2** (parada determinística — orçamento sempre gasto, salvo esgotamento real): ~32→48 páginas/filme, ~61→~85 requisições numa coleta DO ZERO — custo aceito explicitamente em troca de determinismo (§3[B]). **Valor MEDIDO (2026-08-07, recoleta incremental sobre o bruto da v1.9.1, 3 filmes): 13-15, média 14,3** — não comparável ao valor esperado de coleta do zero, mesmo motivo das sessões anteriores (a maior parte do material já estava cacheada; o custo novo concentrou-se nas posições profundas, nunca visitadas antes). **Resultado central: os 3 filmes fecharam 40/40/40 nos 9 buckets — o déficit residual da v1.9.1 (`cidade-de-deus`/`medianas`, 37/40) fechou.** Tabela completa em §3[B], "Resultado MEDIDO da recoleta v1.9.2". **Valor MEDIDO sob a v1.9.3 (coleta DO ZERO, 3 filmes, harness de lote, 2026-08-07): 67-73 requisições, média 70,0** (`parasite-2019`=67, `eighth-grade`=70, `everything-everywhere-all-at-once`=73) — a primeira medição do zero desde a v1.9.0, com o coletor da v1.9.2 (parada determinística + posicionamento estratificado). **Correção de registro (achado da diagnose pós-Entrega 2, ver §3[H] "Diagnose do déficit de buckets"): os 9 buckets fecham `estado_piso=completa` (n≥15 em todos), mas só 5 dos 9 atingem a COTA cheia de 40** — `parasite-2019` fechou 28/40/32 (negativas/medianas/positivas), `eighth-grade` 38/39/40, `everything-everywhere-all-at-once` 40/40/40; NÃO é "40/40/40 nos 9 buckets" como uma versão anterior deste parágrafo afirmou incorretamente, contradizendo a própria tabela do relatório da Entrega 2. Diagnose completa (motivo de parada, páginas orçadas vs. gastas, descarte discriminado, teste da hipótese de spoiler) em §3[H]: os 4 déficits são 100% ESCASSEZ (filtro `min_chars=150` descartando reviews curtas — 63-87% do bruto de cada nível deficitário — sobre um bruto onde TODAS as páginas orçadas retornaram conteúdo, zero sondagem caindo em página vazia); nenhum é DESPERDÍCIO. Tempo de parede: 499,5s para os 3 (média 166,5s/filme, ~2,8 min/filme, `DELAY_SECONDS=2.0`). Disco do bruto persistido: 240-264 KB/filme, média 248 KB/filme. **Extrapolação para 30 filmes: ~2100 requisições, ~83 min (~1,4 h), ~7,3 MB. Para 50 filmes: ~3500 requisições, ~139 min (~2,3 h), ~12,1 MB** — ambos bem abaixo do teto de ~4h que dispararia parada e pedido de decisão ao usuário (§3[H]). **Achado lateral não previsto:** recoletando os MESMOS 3 filmes do zero ~2h depois com os MESMOS parâmetros, `n` final por bucket variou (`parasite-2019`/positivas: 36→32; `eighth-grade`/negativas: 37→38, medianas: 37→39) — o site é um alvo VIVO sob `by/added`; buckets que fecham exatamente na cota mascaram essa variância, buckets abaixo dela a revelam. Registrado como achado, não corrigido (fora de escopo desta sessão).

---

## 6. Incógnitas de Fase 1 — RESOLVIDAS (ver `FASE1_INCOGNITAS.md`)

As três incógnitas abaixo foram resolvidas na Fase 1; os achados já estão incorporados em §2.1 e §3 [A]/[C'] acima. Mantidas aqui só como registro histórico.

1. ~~**Paginação** `.../rated/N/by/activity/page/2/`: confirmar que funciona e não repete conteúdo.~~ **Resolvido:** funciona, não repete (dedup por viewing id), página além da última = 200 com lista vazia.
2. ~~**Página de busca** de slug: estrutura não verificada.~~ **Resolvido:** endpoint real é `/s/search/films/<query>/` (AJAX), não a URL humana (shell React vazio).
3. ~~**Endpoint de texto completo** (`/s/full-text/viewing:<id>/`): validar formato da resposta, e validar o **detector de truncamento** com casos positivos e negativos conhecidos (crítico — ver C'.1).~~ **Resolvido:** endpoint validado; detector corrigido para `.collapsed-text` (não `data-full-text-url`, que não discrimina) — 2 positivos + 2 negativos, zero erros.

---

## Changelog
- **v1.9.3** (2026-08-07) — harness de LOTE (§3[H]), infraestrutura sobre a camada de coleta fechada na v1.9.2. Nenhum parâmetro de coleta tocado; nenhuma síntese/narrativa.
  - **(1) Checkpoint em arquivo.** `estado.json` por lote, atualizado APÓS cada filme (não em lote ao final) — resume pula todo slug já `concluido`, sem refazer trabalho nem perder o parcial de um lote interrompido a qualquer momento.
  - **(2) Validação de slug — 1 requisição, antes do orçamento de páginas.** Listagem "qualquer nota" (`reviews_qualquer_nota_url`) + `parser.parse_reviews` já testado: 404/erro → slug inválido; 200 sem review reconhecida pelo parser → `sem_reviews`. **Corrigido durante a Entrega 2** — a primeira versão buscava a página principal do filme e casava a tag `js-route-reviews`, que só existe em páginas de LISTAGEM de reviews, não na raiz; achado real contra os 3 filmes de teste, invisível nas fixtures sintéticas. Detalhe em §3[H]. Histograma ausente NÃO é motivo de rejeição — o pipeline já degrada esse caso (§3[G]), pré-validar de novo seria custo redundante.
  - **(3) Falha isolada.** Todo o pipeline de coleta de um slug roda dentro de um `try/except`; qualquer exceção vira entrada `falhou` no checkpoint com o motivo, e o lote segue.
  - **(4) `material_esgotado` tratado como caso ESPERADO** — os 3 filmes do catálogo, populares, nunca exercitaram esse caminho em produção; testado explicitamente que não quebra persistência, `montar_buckets` nem o JSON.
  - **(5) Estimativa de custo medida antes do lote** — 3 filmes DO ZERO (`parasite-2019`, `eighth-grade`, `everything-everywhere-all-at-once`): 61-76 requisições/filme (média 69,0), ~163s/filme, 220-268 KB/filme (média 242,7 KB). Extrapolado: 30 filmes ≈ 2070 requisições / ~1,4h / ~7,1 MB; 50 filmes ≈ 3450 requisições / ~2,3h / ~11,8 MB — ambos abaixo do teto de ~4h, sem necessidade de veto. Detalhe completo em §5.6.
  - **(6) Lote executado — 29 filmes, lista fornecida pelo usuário (`dados/lote-slugs.txt`), 0 falhas.** 2254 requisições (média 77,7/filme — 12,6% acima da projeção de 69, dentro do razoável), 5363s de parede (~1,49h — 15% acima da projeção de ~1,3h), ~6,95 MB de bruto persistido (quase exato à projeção de ~7,1 MB). `material_esgotado` disparou pela primeira vez em produção (`obsession-2026`, 214 notas no total, 9 de 10 níveis — primeira vez fora de teste sintético) sem quebrar persistência nem montagem de buckets, produzindo os primeiros estados reais de piso reduzido (`sem_numero` ×2, `sem_quantificador` ×1). 14/29 filmes fecham a cota 40 nos 3 buckets; 84/87 buckets em `estado_piso=completa`. Achados estruturais em §3[H], "Resultado do lote (v1.9.3)" — não corrigidos nesta sessão.
  - **(7) Diagnose do déficit de buckets nos 3 filmes da Entrega 2** — corrige o registro "40/40/40 nos 9 buckets" (errado; real: 5/9 na cota, 9/9 em `estado_piso=completa`) e classifica os 4 déficits como ESCASSEZ (filtro `min_chars`, zero desperdício de página) via `selecao.selecionar` reexecutado offline sobre o bruto. Hipótese de spoiler testada e refutada. Achado estrutural: filmes populares tendem a fechar buckets extremos abaixo da cota mais que filmes de nicho, mesmo com orçamento idêntico — registrado, não corrigido. Detalhe completo em §3[H].
- **v1.9.2** (2026-08-07) — fecha o gate de profundidade da v1.9.1 e resolve o déficit residual de `medianas`. Última sessão de coleta antes do lote de 30-50 filmes. Fronteiras, cota, piso escalonado, `min_chars`, ordenação e qualquer etapa de síntese/narrador/editor **não tocados**.
  - **(1) Parada por ALVO removida (§3[B]).** Era um vestígio de quando o teto era por NÍVEL e o custo por BUCKET não tinha limite (v1.9.0); sob o orçamento por bucket da v1.9.1 virou fonte de NÃO-DETERMINISMO — foi o mecanismo exato do 37/40 residual de `cidade-de-deus` (nível 2,5★ parou por ALVO na página 3, com 3 páginas de orçamento ainda disponíveis, página 4 nunca buscada). Agora o orçamento de páginas por nível é sempre gasto INTEGRALMENTE; única parada antecipada é esgotamento REAL de material. `motivo_parada` por nível: `"orcamento_esgotado"` \| `"material_esgotado"`, gravado em `meta.json`. O piso de páginas por nível (gate do ALVO) some — a garantia de reversibilidade da fronteira (§2.2) já vinha, desde a v1.9.1, do piso da ALOCAÇÃO de páginas, não deste parâmetro. `FOLGA_ALVO_COLETA` sobrevive com escopo reduzido: só decide o orçamento do completamento [C'], nunca mais quando parar de paginar. Custo aceito e medido em troca de determinismo — ver Resultado MEDIDO.
  - **(2) Posicionamento estratificado por profundidade (§3[B]).** O defeito: páginas de um nível eram sempre as primeiras `N` consecutivas, amostrando sistematicamente o mais recente sob `by/added` (79-100% da amostra em ~7 semanas, medido na v1.9.0). Correção: `RESERVA_PROFUNDIDADE = 0,25` do orçamento de cada nível é posicionada em progressão geométrica (`n_raso+2, n_raso+4, n_raso+8, …`) a partir do fim do bloco raso; a primeira posição profunda vazia revela a profundidade real (por monotonicidade da paginação), e o orçamento não gasto é redistribuído para dentro do intervalo JÁ CONFIRMADO como válido (nunca além — no máximo 1 página desperdiçada por nível). A redistribuição **reaproveita `redistribuir_deficit`** — terceiro uso da mesma função (reviews entre níveis, páginas entre níveis, agora posições dentro de um nível), nenhum mecanismo novo. **Custo IGUAL ao consecutivo no caso comum (profundidade folgada); nunca MAIOR em nenhum caso** — no caso de fronteira exata (profundidade real cai dentro de um salto geométrico ainda não confirmado), o orçamento pode ficar parcialmente não-gasto em vez de arriscar mais de 1 página vazia — testado explicitamente (`tests/test_posicionamento.py`). Degrada para consecutivo puro quando o nível é raso (material esgota dentro do bloco raso, fase profunda nunca tentada). **Racional de reversibilidade:** com raso e profundo no MESMO bruto, "analisar só o recente" vs. "analisar tudo" vira parâmetro filtrável por `pagina_origem` na seleção (não implementado, mas agora POSSÍVEL sem recoleta) — a profundidade de paginação era o único parâmetro de coleta que o superset ainda não tornava reversível.
  - **(3) Confirmação do teto de 256 páginas — Entrega 3.** Medido em `the-room-1993` (890 notas, obscuro), nível mais populoso 3,0★ (249 notas) — sonda exponencial + binária, **6 requisições**. Resultado: **última página com conteúdo = 4**, muitíssimo abaixo de 256 — a profundidade foi determinada pelo CONTEÚDO REAL, não por um teto de site, ao contrário dos 3 filmes populares da v1.9.1 (todos batendo exatamente em 256/512 apesar de volumes de notas muito diferentes entre si). O achado lateral da v1.9.1 fica CONFIRMADO: Letterboxd aparenta impor um teto de paginação por volta de 256 para listagens populosas. O posicionamento estratificado (item 2) não dependeu desta resposta — funciona igual, mesmo custo, seja a profundidade real 4 páginas ou 256.
  - **(4) `pagina_origem` vira instrumento temporal PRIMÁRIO (§3[B']).** `janela_temporal` (v1.9.1) mede `data`, que é a data ASSISTIDA (diário) — contaminada por quem registra filmes com atraso, causa raiz do resultado MISTO do gate da v1.9.1 (janela por `data` ESTREITOU sob amostragem mais profunda em 2 dos 3 filmes). `pagina_origem`, sob ordenação cronológica, é o rank de ADIÇÃO — sem essa contaminação. Nova telemetria `distribuicao_pagina_origem` por bucket (`{n, min, max, p5, p50, p95, fracao_profunda}`), sobre a amostra SELECIONADA (não o bruto inteiro), com `fracao_profunda` usando a MESMA divisão raso/profundo do item 2 — telemetria e coleta nunca divergem sobre o que conta como profundo. `janela_temporal` rebaixada a secundária, rotulada como proxy contaminado, mantida (é o único sinal de calendário real que existe).
  - **(5) Recoleta dos 3 filmes, MEDIDA — o déficit residual da v1.9.1 fechou.** `cidade-de-deus`/`medianas` (37/40 na v1.9.1, nível 2,5★ parando cedo por ALVO) agora fecha **40/40** — os 3 filmes, os 9 buckets, todos em 40/40/40 pela primeira vez desde a v1.9.0. Requisições: 13-15 por filme (incremental, não comparável à coleta do zero). `motivo_parada`: 100% `orcamento_esgotado` nos 30 níveis medidos (10 níveis × 3 filmes) — os filmes do catálogo têm material de sobra em todo nível, nunca esgotam organicamente. `fracao_profunda` (entrega 4) variou 0,00-0,23 entre buckets — real e mensurável quando o material raso não basta para fechar a cota (`the-invite-2026`/negativas: 23% da amostra final veio do bloco profundo), zero quando basta (o bloco raso já fecha a cota e a seleção, ainda ordenada por `pagina_origem` ascendente, não precisa alcançar o profundo — o filtro de profundidade na seleção continua não-implementado, só possível). Ver §3[B] "Resultado MEDIDO da recoleta v1.9.2" e §5.6 para a tabela completa.
- **v1.9.1** (2026-08-07) — corrige dois defeitos que a telemetria MEDIDA da v1.9.0 revelou na camada de coleta, mais duas entregas de acabamento. Nenhuma etapa de síntese/narrador/editor tocada; fronteiras, cota e piso escalonado **não mudaram**.
  - **(1) Orçamento de páginas POR BUCKET, não por nível (§3[B]) — fecha o defeito estrutural.** O teto de páginas era por NÍVEL (4, flat) enquanto a cota é por BUCKET (40); sob a opção C, `medianas` (2 níveis) tinha metade do teto AGREGADO de `negativas`/`positivas` (4 níveis) — 8 contra 16 — e por isso nunca fechava a cota (medido na v1.9.0: 35, 23, 26). Correção: `ORCAMENTO_PAGINAS_POR_BUCKET = 16`, igual nos três buckets, distribuído entre os níveis do bucket **reaproveitando `alocar_bucket`** (a mesma função da alocação de reviews, agora recebendo páginas em vez de reviews como `N`) com piso de 1 página/nível (mesmo seguro de reversibilidade) e teto de segurança de 10 páginas/nível (nenhum nível domina o orçamento do bucket sozinho) — o excedente cortado pelo teto de segurança é redistribuído **reaproveitando `redistribuir_deficit`** com o teto como "disponibilidade", não um segundo mecanismo. `16 = 4×4`: o orçamento não sobe para os buckets de 4 níveis, ele equaliza o que `medianas` tinha pela metade.
  - **(2) Motivos de descarte discriminados (§3[C2]) — telemetria pura.** Cada review do bruto é classificada em exatamente uma categoria (`selecionada` ou um motivo), em ordem de precedência fixa: `truncada_sem_texto` → `spoiler` (só quando `excluir_spoiler=True`) → `abaixo_min_chars` (contra o degrau de cascata que vigorou, não o `min_chars` nominal) → `excedente_cota` (passou em tudo, mas além do que a alocação permitiu) → `duplicata`/`outros` (defensivos, esperados sempre zero — canário de bug). Invariante: soma dos motivos == `n_brutas − n_validas`, sempre. `n_descartadas_spoiler`/`n_descartadas_curtas`/`n_indisponivel_truncamento` passam a ser derivados do mesmo dict, uma fonte de verdade em vez de duas contagens que podiam divergir. Zero mudança de comportamento.
  - **(3) Medição de profundidade de paginação — GATE, passo largo NÃO implementado (§3[B]).** Responde as 4 perguntas do briefing com dado real dos 3 filmes (`scripts/medicao_profundidade_v191.py`, nível 4,0★, `by/added`), sem tocar o coletor de produção: **(a)** profundidade NÃO é conhecível a partir da página 1 (sem numeração no HTML); um proxy por histograma foi testado e **superestimou 11,6×-27,2×** (a maioria das notas não tem texto, e a proporção não é uniforme) — a única forma confiável foi sonda exponencial (~10 req./nível). Achado lateral não confirmado amplamente: os 3 filmes bateram no mesmo intervalo (256/512), e uma busca binária no `cure` fechou exatamente 256 — suspeito de ser TETO FIXO do site, não exaustão orgânica; testado só num nível de um filme. **(b)** páginas profundas (50/75/95% da profundidade sondada) rendem contagem e comprimento médio na MESMA ordem de grandeza das rasas, sem degradação — favorável ao passo largo. **(c)** MISTO: para `cure`, passo largo ampliou a janela de 2 dias para ~4 meses (confirma a hipótese); para `cidade-de-deus` e `the-invite-2026`, a janela por `min`/`max` ficou mais **ESTREITA** sob passo largo — artefato de outlier (data é a ASSISTIDA, não a de publicação, e `min`/`max` é dominado pelo extremo mais velho de QUALQUER posição da amostra) — evidência a favor da entrega (4) abaixo. **(d)** o briefing previu custo neutro; a medição diz que **NÃO é neutro** — a única forma confiável de saber a profundidade (sonda exponencial) custaria ~10 requisições NOVAS por nível em TODA coleta, a menos que o teto fixo do achado (a) se confirme (nesse caso o custo desaparece, porque a profundidade vira uma constante conhecida, sem sonda). **Decisão não tomada** — se prosseguir, o próximo passo é confirmar/refutar o teto fixo em mais níveis/filmes, não escrever o paginador.
  - **(4) Janela temporal em `meta.json` (§3[B']), não exposta no frontend.** `janela_temporal: {total, por_bucket}`, cada bloco `{n, min, max, p5, p50, p95}` sobre as datas do bruto (truncadas a `YYYY-MM-DD`). Motivada pelos dois achados acima (viés de recência da v1.9.0 + `min`/`max` enganoso desta versão): a métrica certa para avaliar cobertura temporal é a distribuição, não os extremos. Cálculo bucket-agnóstico em `bruto.py` (função pura sobre qualquer lista de reviews); agrupamento por bucket em `pipeline.py` (único módulo que já enxerga as duas camadas, mesmo padrão de `montar_buckets`). Espelhado no bloco `coleta` do resultado (mesmo mecanismo de auditoria da v1.9.0) — `frontend/js/filme.js` não lê esse bloco, então não fica visível ao usuário nesta sessão.
  - **(5) Pendência da v1.9.0 resolvida: `frontend/js/filme.js`** tinha o literal `"50 · 20 · 30"` em duas linhas, o mesmo número já corrigido em `render.py`/prompt do narrador na v1.9.0. Corrigido para ler `f.buckets[i].alvo` do JSON de resultado (o frontend não importa `config.py`, então deriva do dado, não de uma constante compartilhada).
  - **Recoleta dos 3 filmes sob o orçamento novo, MEDIDA (não projetada).** `medianas` fechou **40/40** em `cure` (era 35) e em `the-invite-2026` (era 26); em `cidade-de-deus` fechou **37/40** (era 23) — melhora grande, mas não o fim do defeito nesse filme especificamente. Causa identificada e distinta do defeito original: o nível 2,5★ parou por **ALVO** (degrau b, folga heurística) antes de esgotar o orçamento de páginas (confirmado: página 4 nunca foi buscada), e o material real pós-filtro ficou abaixo do que a heurística previu — mecanismo da v1.9.0, inalterado nesta sessão, fora do escopo do orçamento por bucket. Requisições: 17-26 por filme (recoleta INCREMENTAL sobre o bruto já persistido, não comparável 1:1 com os 61 da v1.9.0, que foi do zero). `duplicata`/`outros` (entrega 2) deram **zero em todos os filmes/buckets/níveis** — a garantia de dedupe do bruto se sustenta sob dado real. Ver §3[B], "Resultado MEDIDO da recoleta v1.9.1", e §5.6 para a tabela completa.
- **v1.9.0** (2026-08-07) — **desacopla COLETA de ANÁLISE.** A maior mudança de arquitetura de dados desde a v1. Nenhuma etapa de síntese, narrador, editor ou frontend foi tocada.
  - **O problema.** A coleta gravava, no material coletado, as decisões de **fronteira de bucket**, **cota** e **filtro**. Três consequências, todas reais: (1) os buckets de 50/20/30 eram **acidente aritmético** (10 reviews × 5/2/3 níveis), não decisão de profundidade — o grupo mediano recebia 40% da profundidade do negativo sem nenhuma justificativa de design; (2) a cota igual **por nível de estrela** super-representava os extremos dentro de cada bucket (no `cure`, 0,5★ tem 456 notas e 2,0★ tem 4.251, e ambos entravam com 10 reviews — 0,5★ com ~9× o peso relativo que tem na população, fazendo o grupo negativo soar mais raivoso do que é); (3) **mudar qualquer uma dessas decisões custava recoletar tudo**, o que na prática as tornava irrevogáveis.
  - **(1) Fronteiras viram CONFIGURAÇÃO (§2.2).** `FRONTEIRAS` vive num único lugar (`buckets.py`) e o mapeamento nível→bucket é **função pura** (`bucket_de_nivel`); lista de níveis, intervalos dos prompts, agregação do histograma, alocação e seleção são todos **derivados**, nunca redigitados. Um teste roda o mapeamento sob fronteiras **alternativas** e confere que tudo acompanha — é a prova de que é parâmetro, não constante. **Opção C adotada** (`0,5–2,0` / `2,5–3,0` / `3,5–5,0`; semântica "não recomendam / mornos / recomendam"): 2,5★ é o ponto médio exato da escala e lê-lo como "não recomenda" é escolha, não dado; 3,5★ é, na prática, recomendação com ressalva. **Shares publicados MUDAM**, recalculados sobre o mesmo histograma (0 requisições): `cure` 3/17/79 → **2/8/90**, `the-invite-2026` 3/18/79 → **2/7/91**, `cidade-de-deus` 1/8/91 → **1/3/96** — positivas crescem com a entrada do 3,5★ (nível populoso, 11-12% de todas as notas), negativas encolhem pouco com a saída do 2,5★ (nível pequeno). **Risco aceito registrado em §2.2**, com três itens e mitigação de cada: saturação do `rotulo_peso` no extremo forte (candidato a faixa nova ≥90%, **não aplicado** — é do narrador, fora do escopo), deslocamento silencioso da `marcacao_perspectiva` (consequência prevista, não bug), e a possibilidade de a fronteira estar simplesmente errada — mitigada pelo fato de que trocá-la passou a custar **zero requisições**.
  - **(2) Superset persistido (§3[B'])** em `dados/bruto/<slug>/{meta.json,reviews.jsonl}`, **versionado** (ao contrário de `resultado/cache/`, que é HTML reconstruível): o bruto é o insumo de análise, e é exatamente a coisa cuja recoleta esta versão existe para evitar. **Idempotente e incremental** — dedupe por `id`, a linha nova sobrescreve a do mesmo `id` (para incorporar um completamento resolvido depois), `meta.json` atualizado; coletas sucessivas **acumulam** superset. **Três campos além do formato pedido**, todos propriedades da review e nunca decisões de seleção: `truncada` e `texto_completo` (sem eles a invariante de v1.1.0 "texto truncado nunca chega ao LLM" seria impossível de garantir a partir do bruto — `n_chars` de um texto cortado não distingue "review curta" de "review longa truncada") e `data` (a evidência de que `ordenacao_usada` é o que se declara). **`passou_por_relaxamento` NÃO é gravado**: relaxamento é decisão de seleção, não propriedade da review, e gravá-lo recolocaria no bruto o tipo exato de decisão que esta versão tirou de lá; é derivado de `n_chars`/`spoiler_flag`.
  - **(3) Condição de parada em três degraus de precedência (§3[B]).** **(a) piso** de 1 página por nível sempre que houver material, **mesmo com alocação zero** — é o **seguro de reversibilidade da fronteira**: sem ele, um nível com alocação zero nunca seria raspado e uma fronteira futura que o incluísse não teria o que reavaliar, o que devolveria o custo de recoleta que a versão inteira existe para eliminar. **(b) alvo** = cota alocada × **1,25**, contado por heurística (os filtros decidem apenas **parar**, e tudo continua sendo persistido) — a folga existe porque a contagem heurística é otimista por construção: usa o texto **visível**, e parte do que ela aprova cai depois no completamento ou na re-checagem de spoiler. **(c) teto** de **4 páginas** (era 6), com o nível registrado em `paradas_por_limite`. **Superset incompleto é resultado honesto**: a moagem de 6 páginas existia para fechar uma cota rígida de 10 válidas; sob alocação proporcional, quem precisa de muitas reviews são os níveis populosos (onde 4 páginas × 12 sobram) e quem não fecha são os raros (onde a 5ª página raramente existe) — migrar o teto de 6 multiplicaria o custo por 10 níveis sem ganho, e o déficit tem tratamento explícito em vez de ser escondido gastando requisição.
  - **(4) Ordenação vira parâmetro declarado (§2.3),** gravado em `meta.json` e **na chave de cache** (servir do cache uma amostra de outra ordenação seria erro silencioso). **Default trocado de `by/activity` para `by/added`.** Evidência medida ao vivo (`cure`, nível 4★, datas das 6 primeiras reviews): `by/added` **2026-08-07 … 2026-08-06** (estritamente decrescente); `by/added-earliest` **2012-11-10 … 2014-03-16** (estritamente crescente); `by/activity` **2023-02-15, 2020-10-22, 2024-04-04, 2022-10-23, 2021-10-09, 2025-11-21** — **sem ordem temporal nenhuma**, que é a prova de que o critério é engajamento (curtidas/comentários) e não tempo. Engajamento enviesa para review longa e promovida, exatamente o viés que a amostra não deve ter. `by/added-earliest`, embora igualmente cronológica, concentraria a amostra na janela de lançamento (coorte de festival/primeiros adeptos). **Correção de registro:** a justificativa da v1.0.0 (`by/activity` "mitiga viés de popularity") **não se sustenta** contra o HTML observado — o menu real do site tem só as três opções acima e `by/activity` **é** a ordenada por engajamento. **Ressalva honesta:** troca-se um viés (engajamento) por outro (recência); não há amostragem neutra neste menu, há amostragem **declarada**.
  - **(5) Alocação proporcional dentro do bucket (§3[C1]),** `n(L) = max(piso_nivel, round(N × c_L / C_bucket))` com `piso_nivel = 2` (ARBITRÁRIO, calibrável) aplicado só a níveis com material, reconciliação por **maior resto** para somar exatamente `N_bucket`, e corte pelos níveis de maior alocação acima do piso quando o piso empurra a soma para cima. Caso degenerado documentado: se `nº de níveis com material × piso > N_bucket`, o piso é **relaxado** explicitamente, não violado em silêncio. **Zero requisições extras** — [G] já era 1 request cacheado por filme desde a v1.4.0, e só foi **promovido** para antes da coleta (sem histograma, a alocação cai para uniforme e nada bloqueia). **Duas ressalvas declaradas:** o histograma mede **NOTAS** e a alocação distribui **REVIEWS COM TEXTO** (populações diferentes, a mesma distinção da v1.4.1) — a alocação é **aproximação por proxy**, declarada como tal, e usada por ser estritamente melhor que o proxy que substituiu ("todos os níveis são igualmente populosos", falso em todo filme); e a **redistribuição de déficit muda a composição silenciosamente**, o que obriga a telemetria de composição **ALVO vs. ATINGIDA** por nível, lado a lado (§4). Redistribuição é restrita ao **mesmo bucket** e **nunca** aciona cascata de relaxamento na coleta.
  - **(6) Cota de análise 40/40/40 aplicada downstream (§3[C2]),** sobre o bruto persistido, com `fronteiras`/`cota_por_bucket`/`min_chars`/`excluir_spoiler`/`cascata`/`piso_nivel` como **parâmetros de chamada** e **zero rede**. A cascata mantém a semântica da v1.1.0 (dispara **só em zero**, nunca para completar cota) e passa a registrar quantas reviews entraram por cada degrau. Ordem de escolha dentro do nível = `(pagina_origem, ordem no jsonl)`, que é a ordem de amostragem da ordenação escolhida — determinística e reproduzível. **Precisão registrada nos DOIS níveis de confiança**, porque a régua de 1 erro padrão sozinha promete mais do que entrega (cobre ~68%, não a confiança que um leitor assume ao ver uma barra): `n=40` → **±7,9pp (1 EP) / ±15,5pp (95%)**; `n=30` → **±9,1pp / ±17,9pp**. Leitura direta: com `n=40`, um tema em 40% e um em 25% **não são distinguíveis** a 95%.
  - **(7) Piso escalonado, 4 estados (§3[C3]):** `≥15 → completa` · `8–14 → sem_quantificador` · `3–7 → sem_numero` · `<3 → sem_analise`. **Os limiares são ARBITRÁRIOS** e entram com esse rótulo explícito (mesma política dos limiares de `marcacao_perspectiva`, v1.5.0) — a ordem de grandeza é defensável pela tabela de precisão (em `n=8` o intervalo de 95% já passa de ±34pp, o que torna um quantificador verbal indefensável), os cortes exatos não. **Nesta versão apenas o CAMPO é exposto** (`estado_piso` no JSON, consumível por frontend e narrador); **variantes de narrador e estados de UI NÃO foram implementados**, e `modo` permanece intacto para não quebrar render/frontend. **Caso de borda definido e documentado (não implementado):** quando o bucket DOMINANTE cai em modo reduzido, a abertura do MOVIMENTO 3 **continua sendo dele** — o peso vem do histograma de NOTAS e não depende de haver review com texto; suprimi-lo reintroduziria a infidelidade por omissão que a v1.4.0 corrigiu. Muda o conteúdo: `sem_numero` cita temas sem nenhuma frequência; `sem_analise` declara explicitamente que **não há material escrito suficiente daquele grupo** e só então passa ao grupo de maior peso seguinte — a ausência é declarada, nunca preenchida com temas de outro grupo nem disfarçada reordenando os grupos.
  - **Duas mudanças fora da camada de coleta, ambas de DES-HARDCODING de número, zero mudança de regra:** o disclaimer de `render.py` e o literal `(50/20/30)` dentro da regra (c) do prompt do narrador passaram a ser **derivados de `BUCKET_ALVO`**. Não são mudanças de comportamento — são a correção de um número que a v1.9.0 tornaria falso, e ficam registradas aqui por atravessarem a fronteira de escopo desta sessão. **PENDÊNCIA CONHECIDA:** `frontend/js/filme.js` tem o mesmo texto "50 · 20 · 30" hardcoded em duas linhas e **NÃO foi tocado** (frontend está fora do escopo); precisa ser atualizado para 40 · 40 · 40 antes da próxima publicação do site.
  - **Orçamento de requisições (§5.6), MEDIDO na recoleta de 2026-08-07:** **58-65 por filme (média 61)** — 32-33 de paginação, 24-33 de completamento, 1 de histograma. **Abaixo** dos 83 (`cure`) e 68 (`cidade-de-deus`) da v1.8.2, apesar de coletar ~50% mais material bruto (384 vs. 252 no `cure`): o orçamento de completamento cortou a parte cara. A estimativa de "~45" feita antes da medição estava otimista, como a própria sessão previu ao exigir "a medir".
  - **DEFEITO ESTRUTURAL descoberto pela recoleta, NÃO corrigido nesta versão (§3[B], "Resultado medido"):** o bucket `medianas` **não consegue fechar a cota de 40 em filme nenhum** — 35, 23 e 26 nos três. A causa é aritmética, não falta de material: sob a opção C o bucket do meio tem **2 níveis** contra 4 dos outros, e o teto de páginas é **por nível**, então o bruto máximo de `medianas` é metade (96 vs. 192) e, ao rendimento medido de ~27%, topa em ~26 válidas. É uma **interação não prevista** entre três decisões desta versão tomadas separadamente — fronteira 4/2/4, cota igual 40/40/40 e teto de 4 páginas por nível: cada uma defensável sozinha, juntas tornando um terço da promessa de "profundidade igual" impossível de cumprir. Deixado em aberto de propósito: corrigir exige mexer numa das três decisões recém-congeladas, e essa escolha merece decisão explícita, não correção de rodapé. **Cinco** saídas registradas em §3[B]; a que vigora por omissão é a (3) — aceitar e deixar o piso escalonado reportar, já que `medianas` fecha em `completa` (≥15) nos três filmes. **Diagnóstico confirmado offline:** reselecionando o mesmo bruto sob as fronteiras HISTÓRICAS, quem fica curto passa a ser `positivas` (3 níveis, 36/40 em dois filmes) e `negativas` (5 níveis) fecha 40 em todos — o déficit acompanha o **número de níveis do bucket**, não a faixa de nota, que é a prova de que o defeito é do teto-por-nível e não da opção C. E com `min_chars=50` os três buckets fecham 40/40/40 nos três filmes a partir do mesmo material: o que falta não é review, é review **longa**.
  - **Prova de reversibilidade, sobre dado real:** a mesma reseleção acima — duas configurações de fronteira e um filtro alternativo, sobre 1.164 reviews persistidas — rodou com **zero requisições de rede**. É a propriedade que justifica a versão inteira, verificada contra o bruto de produção e não só em teste.
  - **Viés de recência MEDIDO (§2.3):** a ressalva qualitativa da spec subestimava o efeito. **79-100% da amostra de cada filme vem dos 2 meses mais recentes** — para `cure` (1997) e `cidade-de-deus` (2002), a análise passa a descrever quem está descobrindo o filme AGORA, não a recepção acumulada. A decisão não é revertida (engajamento continua sendo o pior viés, por correlacionar com o CONTEÚDO da review e não só com o quando), mas o tamanho do efeito ficou escrito. Candidato: amostragem estratificada por período, que o superset já suporta — coletas com ordenações diferentes acumulam no mesmo `jsonl`. **Correção junto:** o campo `data` é a data ASSISTIDA (diário), não a de publicação da review — daí ~16% de pares "fora de ordem" e extremos de 2023 numa amostra recente; é evidência indireta da janela, não carimbo de ordem.
  - **Regeneração de síntese/narrativa NÃO foi feita** (fora do escopo da sessão): a recoleta escreveu em `resultado/v190-coleta/` e os `resultado/*.json` publicados seguem os da v1.8.2 — portanto com os shares das fronteiras ANTIGAS (3/17/79, 1/8/91, 3/18/79) e com a cota 50/20/30. **Publicar exige regenerar**, e até lá o site e os JSONs de entrega estão defasados em relação à spec.
- **v1.8.2** (2026-08-04) — corrige o **falso positivo** da checagem `conteudo_adicionado` (v1.8.0) e regenera a produção. Detalhe completo em `CORRECAO_CONTEUDO_ADICIONADO_V182.md` e `DIAGNOSTICO_CONTEUDO_ADICIONADO.md`.
  - **Diagnóstico:** a métrica original comparava cada frase do editado contra frases INTEIRAS do bruto com `SequenceMatcher.ratio()` (char-level, sensível a ORDEM). Quando o editor QUEBRAVA uma frase longa em duas (o trabalho normal de ritmo) ou REORDENAVA palavras dentro dela, a métrica caía por diferença de comprimento/ordem, não por conteúdo novo — foi o que descartou o `cure` na v1.8.1 após 3 reprovações seguidas por `conteudo_adicionado`.
  - **Correção (Tarefa 1):** métrica trocada para COBERTURA DE PALAVRAS (multiset, insensível a ordem — tokeniza, ordena os tokens, roda `SequenceMatcher.get_matching_blocks()`, matematicamente equivalente à interseção de multiset), contra a MELHOR frase INDIVIDUAL do bruto (comparar contra o bruto inteiro de uma vez infla o placar de frases inventadas, medido ao vivo). `EDITOR_LIMIAR_FRASE_SEM_ORIGEM` sobe de 0,45 para 0,6; `EDITOR_MIN_FRASES_SEM_ORIGEM`/`EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO` mantidos.
  - **Calibração (Tarefa 2, offline, zero LLM):** 11 frases legítimas reais (quebras de frase + 1 reordenação, de `VALIDACAO_EDITOR_V18.md` e da produção v1.8.1) ficaram entre 0,765-1,000; as 6 frases do parágrafo REALMENTE inventado do `the-invite-2026` (texto literal) ficaram entre 0,222-0,500 — folga de 0,265. Uma ressalva documentada (não bloqueante): 1 frase de reenquadramento (não é quebra de frase) empata com o pior caso inventado em 0,500 — não reprova nada sozinha (`EDITOR_MIN_FRASES_SEM_ORIGEM=4`). 3 testes de calibração novos; suíte 392 passed.
  - **Regeneração (Tarefa 3):** 13 chamadas DeepSeek, 0 Letterboxd/TMDB. Resultado central: **zero disparos de `conteudo_adicionado`** nesta rodada (contra 6 na v1.8.1). `cidade-de-deus` passou a aceitar de primeira (era 2 tentativas); `the-invite-2026` caiu de 4 para 2. O `cure` continua descartado, mas por motivos NÃO relacionados a esta correção (`ordem_alterada`, `perspectiva_nao_marcada`, `edicao_nula`) — achado à parte registrado (possível falso positivo residual em `ordem_alterada`, checagem sensível a ordem que esta versão não tocou), não investigado. Nenhum defeito conhecido (parágrafo inventado, movimento fora de ordem, contrabarra residual, capitalização mid-frase) reapareceu nos 3 textos publicados.
- **v1.8.1** (2026-08-04) — **reativa o editor [E2] por padrão** (`EDITOR_ATIVO=True`, era `False` na v1.8.0) e **regenera os 3 JSONs de produção** com o provider default novo (DeepSeek) e o editor ligado — as narrativas publicadas eram todas do Gemini até esta versão.
  - **Reativação (Tarefa 1).** `EDITOR_ATIVO=True`; comentário reescrito para citar a checagem que hoje cobre o defeito (conteúdo adicionado + ordem dos movimentos, v1.8.0 Tarefa 3) e a validação que a comprovou (`VALIDACAO_EDITOR_V18.md`), em vez de só o defeito original. `--no-edicao` continua desligando pontualmente; `--com-editor` virou redundante (mantida por compatibilidade). Testes que assumiam o default anterior (`EDITOR_ATIVO=False`) reescritos para o novo default.
  - **Regeneração de produção (Tarefa 2, 13 chamadas DeepSeek dos 16 do orçamento; 0 chamadas Letterboxd/TMDB — `--offline`, cache intocado):** os 3 `resultado/*.json` foram sobrescritos — intencional nesta versão. **`cure`: edição DESCARTADA** (`n_tentativas=4`: 3× `conteudo_adicionado`, depois `perspectiva_nao_marcada`; publicada a narrativa bruta do narrador, similaridade final 0,960 — a checagem nova barrou 3 tentativas ruins seguidas antes de esgotar). **`cidade-de-deus`: aceita na 2ª tentativa** (1ª reprovada por `conteudo_adicionado`; similaridade 0,618, 0 protegidos perdidos). **`the-invite-2026`: aceita na 4ª tentativa** (`conteudo_adicionado`, `perspectiva_nao_marcada`, `conteudo_adicionado`, aceita; similaridade 0,661; capitalização residual ajustada). **Nos 3 filmes**, as 8 flags de honestidade do narrador vieram limpas (só `aspas_removidas=true`, mecânico) e nenhum dos defeitos conhecidos das versões anteriores reapareceu: sem parágrafo de opinião inventado, movimento 1 sempre na abertura, sem contrabarra residual, sem rótulo de peso capitalizado no meio de frase. `frontend/build_data.py` rodado para embutir as narrativas novas em `frontend/js/data.js`. Suíte: 386 passed.
  - **Leitura do resultado:** a checagem nova disparou de verdade em produção em 2 dos 3 filmes (`cidade-de-deus`, `the-invite-2026`) e, no 3º (`cure`), acionou o fail-safe de descarte depois de 3 tentativas ruins seguidas — nenhuma delas publicou conteúdo inventado. O sistema se comportou como desenhado: mais chamadas gastas que o esperado num filme, mas nenhuma garantia de honestidade comprometida.
- **v1.8.0** (2026-08-04) — **DeepSeek vira o provider DEFAULT de produção**, e o editor [E2] é **DESLIGADO por padrão** como medida de contenção, na mesma versão.
  - **Troca de default (Tarefa 1).** `DEFAULT_PROVIDER = "deepseek"` (config.py) — `anthropic`/`gemini` seguem plenamente selecionáveis via `--provider`, só o que o CLI assume sem a flag mudou. Decisão baseada na validação em 3 filmes (`VALIDACAO_DEEPSEEK.md`, sessão anterior): **3/3 no TESTE DECISIVO** (os três movimentos completos, sem colapso — o defeito que inviabilizou o modelo local Qwen3.5-9B); 23 das 24 checagens de honestidade (3 filmes × 8 flags) vieram limpas; custo ~US$0,0005/filme com 96-99% de cache hit no prompt do narrador; sem teto diário de requisições (o gargalo que inviabilizava o Gemini free tier para construir catálogo).
  - **O buraco descoberto na mesma validação (Tarefa 2/3).** A validação também achou um defeito mais sério que o esperado: em `the-invite-2026`, o editor foi ACEITO por TODAS as checagens mecânicas então existentes (protegidos presentes, números idênticos, honestidade sem regressão — similaridade 0,406) e, mesmo assim, (a) reordenou o MOVIMENTO 1 (a apresentação do filme) para o meio do texto, e (b) ACRESCENTOU um parágrafo de fechamento inteiro com opinião própria ("O saldo geral, no entanto, é positivo... a minoria que reprova não apaga o brilho do conjunto") sem correspondência no texto recebido — CONTEÚDO INVENTADO, a violação mais grave possível da regra central do editor (ele não tem fonte de fato, não pode ter opinião), e nenhuma checagem até a v1.7.4 detectava ADIÇÃO — todas checavam PERDA.
  - **Contenção imediata:** `EDITOR_ATIVO = False` (config.py) — o editor não roda mais por padrão; o pipeline publica a narrativa do narrador tal como está (`narrativa == narrativa_bruta`, `edicao_flags: {"editor_desativado": true}`), sem gastar a chamada extra. Reativável com `--com-editor` (CLI) para testes/validação. O `render_terminal` ganhou um ramo explícito para esse estado (não confundir com "aplicada").
  - **Correção estrutural (Tarefa 3): duas checagens novas em `editar_narrativa`, ANTES das existentes.** (1) **Conteúdo adicionado** — divide bruto e editado em frases (`_dividir_frases`) e calcula, para cada frase do editado, a melhor `difflib.SequenceMatcher.ratio` contra as frases do bruto; `EDITOR_MIN_FRASES_SEM_ORIGEM=4` candidatas OU mais de `EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO=35%` das palavras do texto abaixo do limiar (`EDITOR_LIMIAR_FRASE_SEM_ORIGEM=0.45`) → falha `"conteudo_adicionado"` (retentativa com reforço explícito, depois descarte). Limiares calibrados EMPIRICAMENTE sobre os 3 filmes reais das duas validações (`VALIDACAO_DEEPSEEK.md` + `VALIDACAO_EDITOR_V18.md`): edições LEGÍTIMAS (quebra de frase longa em duas — ruído esperado do trabalho normal do editor) ficaram em 1-3 frases/16-18% das palavras nos 4 filmes×tentativa observados; o defeito real teve 15 frases/70% — folga grande dos dois lados. (2) **Ordem dos movimentos** — a 1ª frase do editado precisa ter similaridade ≥ `EDITOR_LIMIAR_ORDEM_MOVIMENTO_1=0.5` contra alguma das 3 primeiras frases do bruto (o narrador sempre abre com a apresentação do filme); abaixo disso, `"ordem_alterada"`. Telemetria nova, persistida SEMPRE em `edicao_flags`: `frases_sem_origem` (lista) e `similaridade_minima_por_frase` (dict). `_EDITOR_SYSTEM_PROMPT` ganhou duas proibições explícitas (acrescentar frase/opinião/fechamento; reordenar movimentos).
  - **Testes (Tarefa 4, mock, zero rede):** reprodução DETERMINÍSTICA do defeito real com o texto LITERAL do `the-invite-2026` → detectado, retentado (reforço específico anexado), descartado após esgotar as tentativas, bruta prevalece; edição LEGÍTIMA de ritmo (frase longa quebrada em duas, mesmo padrão do `cure` real) → NÃO reprovada; reordenação do movimento 1 → detectada isoladamente; `--com-editor`/`EDITOR_ATIVO`/`--no-edicao` (precedência) e o caminho `editor_desativado` (0 chamadas LLM extra) → cobertos em `test_cli_tom.py`. Suíte: 385 passed.
  - **Validação da correção (Tarefa 5, `VALIDACAO_EDITOR_V18.md`):** os 3 filmes rodados com `--provider deepseek --com-editor`, 8 chamadas DeepSeek no total, nenhum descartado. A checagem de conteúdo adicionado disparou DE VERDADE em produção uma vez (`cidade-de-deus`, 1ª tentativa, motivo `"conteudo_adicionado"`) e se autocorrigiu na 2ª — evidência de que a checagem funciona sobre dados reais, não só no teste sintético. O defeito original do `the-invite-2026` não se repetiu nesta rodada (variância do modelo entre chamadas — o mesmo bruto pode gerar edições diferentes), mas está coberto pelo teste de regressão determinístico. **`EDITOR_ATIVO` continua `False`** — a validação é evidência a favor de reativar, mas a troca desse default específico fica para decisão humana à parte, não foi aplicada nesta versão.
- **DeepSeek — provider ADICIONAL (2026-08-04, Parte B)** — sem bump de versão (adição, não muda comportamento do default): `deepseek_client_call`/`deepseek_client_call_prosa` registrados em `PROVIDER_CLIENTS`/`PROVIDER_CLIENTS_PROSA`/`PROVIDER_DEFAULT_MODELS` (`synthesize.py`/`config.py`), selecionável via `--provider deepseek` (`DEEPSEEK_API_KEY`). SDK compatível com o da OpenAI (só `base_url="https://api.deepseek.com"` muda), modelo `deepseek-v4-flash` (os aliases antigos `deepseek-chat`/`deepseek-reasoner` foram descontinuados em 24/07/2026 — não existe mais "DeepSeek-V3" na API), NON-THINKING explícito (`extra_body={"thinking": {"type": "disabled"}}` — thinking vem LIGADO por padrão e, sem isso, compete pelo mesmo orçamento de tokens que a resposta visível, o mesmo modo de falha já visto no Gemini e no experimento local com Ollama). Adaptador DIFERENCIA chamada-JSON (síntese §D + narrador §D2, `response_format={"type":"json_object"}`) de chamada-PROSA (editor §E2, texto puro, sem forçar JSON) desde o primeiro commit — a mistura das duas foi exatamente o bug que invalidou o teste do editor no experimento local arquivado. **O default de produção NÃO mudou** — DeepSeek é opcional, a decisão de trocar o default fica para depois.
  - **Smoke test real (`cure`, cache reaproveitado, 0 chamadas Letterboxd/TMDB, 8 chamadas DeepSeek no total da sessão):** pipeline completo (`--reuse-synthesis --tom narrativo --provider deepseek`) rodou sem erro — narrador (1 chamada) + editor (3 tentativas até aceitar, `houve_retentativa=true`). **TESTE DECISIVO: PASSOU** — os TRÊS movimentos completos (filme/experiência/contraste) saíram sustentados numa única chamada, com os três rótulos de peso ancorados (~79%/~17%/~3% "das notas") e os dois marcadores de perspectiva exigidos presentes; TODAS as 8 flags de honestidade vieram `false` (só `aspas_removidas=true`, remoção mecânica esperada) — o ponto exato em que o Qwen3.5-9B local falhou (colapso de movimento / omissão do movimento 3) não se repetiu aqui. Custo medido (chamadas representativas com o mesmo prompt real): narrador ~8-9,5s, 6592 tokens de entrada (6528 em cache, 64 miss) + ~900 de saída; editor ~4s, 1996 de entrada (1408 cache, 588 miss) + 398 de saída — pipeline completo por filme fica bem abaixo de US$ 0,001, sem teto diário de requisições (o gargalo que inviabilizava o Gemini free tier). Detalhe completo (textos, flags, telemetria) reportado na sessão; nenhum veredito de qualidade literária foi emitido.
- **Nota histórica (2026-08-04)** — sem bump de versão, não é mudança de comportamento: os artefatos dos experimentos 1-7 de síntese/narrador/editor via LLM local (Qwen3.5-9B/Ollama) foram movidos para `experimentos-ollama-arquivado/` (ver `experimentos-ollama-arquivado/README.md` para o resumo e a conclusão de cada experimento). Decisão: abandonar o caminho local — o modelo não sustentou as ~18 invariantes do narrador numa única chamada — e migrar a exploração de provider alternativo para a API DeepSeek.
- **v1.6.1** (2026-07-25): conclui a Tarefa 10 da v1.6.0 (regeneração, bloqueada por cota naquela sessão) e corrige a pendência registrada como "decisão deixada em aberto" — a correção 5.2 do validador de marcadores.
  - **A correção 5.2, revisitada.** A v1.6.0 já tinha corrigido dois defeitos do validador de `marcadores_perspectiva` (§D2): bastar UM marcador bem posicionado por grupo (5.1), e normalizar caixa/acento/demonstrativo na comparação entre o `trecho` declarado e o texto (5.2 original). Mas o caso real que motivou 5.2 — `cidade-de-deus`, narrador declarou *"Para esse grupo, muitos reconhecem…"* e escreveu *"Muitos neste grupo reconhecem…"* — **sobreviveu** à normalização: a diferença é de ORDEM DAS PALAVRAS, não de grafia, e nenhuma normalização de caixa/acento fecha isso. Comparação difusa com limiar foi cogitada e **descartada de novo** (um limiar é uma linha arbitrária).
  - **A correção pela raiz muda O QUE se verifica, não COMO se compara.** `_marcadores_validos` deixou de comparar o `trecho` declarado contra o texto. Em vez disso, escaneia o MOVIMENTO de cada grupo que exige marcação (`_span_de_movimento`: da âncora do grupo — rótulo de peso/percentual — até a âncora do próximo grupo, ou o fim do texto) em busca de qualquer expressão de atribuição reconhecida (`_EXPRESSOES_DE_PERSPECTIVA`) — a MESMA constante que `montar_protegidos` (§E2) já usava, unificada num só lugar. Para `marcacao_perspectiva == "antecipada"`, a exigência de posição (mesma frase da âncora ou a seguinte) passa a valer sobre QUALQUER ocorrência encontrada no movimento, não sobre o `trecho` declarado. `marcadores_perspectiva` (a declaração do LLM) vira **telemetria pura** — persistida e exibida como sempre, mas não mais fonte da validação. Confirmado sobre o `cidade-de-deus` PUBLICADO (dado real, não sintético): o validador agora aceita tanto a declaração original quanto uma lista vazia — o que importa é que o texto realmente contém "neste grupo" e "Para eles" nos movimentos certos.
  - **`_normalizar_trecho`/`_trecho_aparece` (v1.6.0) foram REMOVIDAS** — a normalização de caixa/acento/demonstrativo deixou de ser necessária porque a checagem não compara mais string contra string.
  - **Regeneração (Tarefa 2/3 desta sessão):** ver bloco abaixo, dentro do changelog da v1.6.0, para o resultado exato (filmes concluídos, chamadas gastas, e o que ficou pendente se a cota ou uma chave inválida interromperam a sessão).
- **v1.6.0** (2026-07-25): **separação de responsabilidades** — o narrador volta a responder só por verdade, e um estágio novo (**editor [E2]**) assume ritmo e leitura. Fecha, junto, quatro pendentes acumulados. Nenhum parâmetro congelado de §2 mudou (a config de LLM da prosa é adição, não alteração da síntese).
  - **O diagnóstico acumulado que motiva a versão** (duas sessões, `DIAGNOSTICO_FLUENCIA.md` e `DIAGNOSTICO_FLUENCIA_V2.md`):
    **(a) O few-shot da v1.5.0 usava dados de um filme do catálogo.** O `the-invite` copiou **58 8-gramas** do exemplo (medidos com as construções mandatórias mascaradas), enquanto `cure` e `cidade-de-deus` — sem nada a copiar — ficaram em **0**. A "melhora" daquele filme na v1.5.0 era **artefato de cópia**, não transferência de estilo. Corrigido na sessão de diagnóstico (exemplo passou a ser de filme fictício); registrado aqui porque invalidou a leitura original da v1.5.0.
    **(b) As regras de ritmo no prompt do narrador não transferiram** para os outros dois filmes, e pioraram ambos (períodos emendados, um trecho agramatical no `cure`, "muitos" como sujeito repetido no `cidade-de-deus`).
    **(c) As métricas de fluência não acompanham qualidade.** No `cure`, o texto qualitativamente MELHOR pontuou PIOR em `cv_comprimento` (0.35 → 0.28) e em `verbos_reporte` (3 → 6). Fiscalizar estilo por limiar empurra o modelo a degradar a prosa para satisfazer um número.
    **(d) A configuração de produção gerou uma frase agramatical publicada** — `thinking_budget=0` no `cure`: *"Muitos para eles, há uma falta de tensão ou mistério…"*.
    **Conclusão:** acumular regras num único prompt falhou. A correção não é mais uma regra — é separar as duas responsabilidades em dois estágios, cada um com uma função e com fronteiras estruturais.
  - **(1) Config de produção da PROSA** (`config.py`, §2.1): `thinking_budget=4096` **FIXO** e `max_output_tokens=16000` para narrador e editor, revertendo o `thinking_budget=0` da v1.2.x. Base empírica: com thinking DINÂMICO sob teto de 8000, o raciocínio consumiu até 7676 tokens (96% do orçamento) e truncou 1 chamada em CADA célula testada; com budget FIXO e teto de 16000, **4/4 chamadas terminaram em STOP**. O problema nunca foi "thinking", foi thinking **sem teto** competindo com a resposta pelo mesmo orçamento. A **síntese por bucket (§D) não muda** — é extração estruturada, e nada no diagnóstico apontou problema lá.
  - **(2) Narrador podado** (§D2): saíram todas as regras de RITMO e REGISTRO da v1.5.0 e o par few-shot. Ficaram intactas as invariantes de honestidade — três movimentos, anti-spoiler e risco aceito, critérios do MOVIMENTO 2 + `consensos_usados`, rótulos de peso com percentual e vocabulário "das notas", quantificadores pré-computados + `quantificadores_usados`, marcação de perspectiva + `marcadores_perspectiva`, escopo por grupo, sem aspas, pt-BR, JSON puro. No lugar das regras de estilo, uma nota curta avisando que existe um estágio de edição depois e que ele deve escrever de forma clara e **gramaticalmente correta**.
  - **(3) Estágio [E2] — editor** (§E2, NOVO): 1 chamada LLM por filme, após o narrador. Recebe **exclusivamente** o texto validado e a lista de **trechos protegidos** — não recebe buckets, reviews nem ficha. A garantia anti-invenção é **estrutural**: o que não está na entrada, o editor não tem como saber. A lista de protegidos é montada **em código** a partir do que o narrador já declarou (rótulos de peso com percentual, quantificadores declarados, trechos de marcadores, todo token com dígito), incluindo só o que realmente ocorre no texto e na forma **como aparece** (o narrador capitaliza no início de frase). O prompt traz o par few-shot **movido** da v1.5.0, e uma regra de **gramática obrigatória**: corrigir período quebrado é a única reescrita estrutural que o editor tem obrigação de fazer.
  - **(4) Verificação mecânica da edição** (§E2): **(0, v1.7.2) checagem ESTRUTURAL, aplicada ANTES das demais** — rejeita se o texto começar com `{`/`[`, contiver cerca de código (```), tiver campo estilo JSON nas primeiras linhas (`"text":`, `text:`, `"narrativa":`), ou tiver chaves desbalanceadas (`_formato_invalido`); sem essa checagem, um invólucro `{ text: "..." }` passa pelas checagens (a)-(c) porque elas rodam sobre substring e continuam achando protegidos/números DENTRO do invólucro — foi exatamente o defeito real do `cidade-de-deus` sob a v1.7.1. (a) todo trecho protegido aparece **literalmente** (com a exceção de capitalização inicial, v1.7.1); (b) o multiconjunto de tokens numéricos é **idêntico** ao do original (segunda rede — pega sobretudo número inventado); (c) as validações de honestidade do §D2 são **reexecutadas** e nenhuma pode **regredir** em relação ao texto original; **(d, v1.7.4) EDIÇÃO NULA** — só avaliada quando (a)-(c) TERIAM passado: se a similaridade (`difflib.SequenceMatcher.ratio`, textos normalizados por espaço em branco) entre a bruta e o texto editado for `>= EDITOR_LIMIAR_EDICAO_NULA` (0.97), reprova mesmo assim, motivo `"edicao_nula"` — um editor que devolve a entrada quase intacta passaria por (a)-(c) sem nenhum sinal (é o mesmo texto). Falha em qualquer uma → retentativa com o reforço ACUMULADO das checagens que já falharam (v1.7.3 — até `EDITOR_MAX_TENTATIVAS=3` retentativas, 4 chamadas no total no pior caso; se a 1ª falhar por número e a 2ª por atribuição, a 3ª recebe os dois reforços); esgotadas as tentativas, a edição é **DESCARTADA** e a narrativa do narrador prevalece (`edicao_descartada: true`, `motivo_descarte: "formato_invalido"` no caso da checagem estrutural, ou o motivo da última tentativa nos demais casos). `n_tentativas` e `motivos_por_tentativa` (`edicao_flags`) registram quantas chamadas foram feitas e por que cada uma falhou; `similaridade` (v1.7.4) é persistida SEMPRE, aceita ou não a edição — telemetria para calibrar o limiar de edição nula, não critério em si. Uma edição ACEITA ainda passa por um pós-processamento DETERMINÍSTICO (v1.7.4, `_corrigir_capitalizacao_residual`) que baixa a caixa de um rótulo de peso capitalizado fora de início de período (resíduo de quando o editor o move para o meio da frase sem ajustar a capitalização, autorizado desde a v1.7.1 mas não obrigatório) — `capitalizacao_ajustada` registra se algo mudou. **A garantia:** o editor pode não melhorar o texto, mas não pode piorá-lo — toda propriedade conquistada da v1.1.1 à v1.5.0 sobrevive por construção, não por confiança no modelo. Persistidos `narrativa` (final), `narrativa_bruta` (auditoria) e `edicao_flags`.
  - **(5) Dois bugs do validador de marcadores** (§D2): **(5.1)** "antecipada" exigia que **TODOS** os marcadores declarados de um grupo respeitassem a posição — mas o narrador legitimamente declara mais de um ao elaborar o grupo, e foi assim que o `the-invite` disparou `perspectiva_nao_marcada` com os **dois** marcadores válidos em conteúdo. Passou a bastar **PELO MENOS UM** bem posicionado. **(5.2)** a comparação do trecho declarado passou a ser **normalizada** (minúsculas, sem acentos, série `esse/este` equivalente), com os demonstrativos mapeados **antes** da remoção de acento para não confundir "esta" (demonstrativo) com "está" (verbo). **Limitação registrada:** a normalização não cobre **reordenação** — no caso concreto do `cidade-de-deus` ("Para esse grupo, muitos reconhecem…" declarado vs. "Muitos neste grupo reconhecem…" escrito, similaridade 0.92), o falso positivo **persiste**; fechá-lo exigiria comparação difusa com limiar, o que enfraqueceria a garantia de que o marcador declarado é o que está no texto. Decisão deixada em aberto.
  - **(6) Métricas de fluência viram DIAGNÓSTICO PURO** (§D2): removidos os gatilhos automáticos de retentativa, o reforço `_REFORCO_FLUENCIA` e a flag `fluencia_baixa`. O cálculo e a persistência de `metricas_fluencia` continuam, com o mesmo estatuto de `consensos_usados` — material de revisão humana. Motivo em (c) acima: as métricas medem **dispersão**, não legibilidade.
  - **(7) Granularidade do rótulo de peso** (§D2): faixa nova `< 5% → "uma fração mínima"`. Antes, 8% e 1% recebiam ambos "uma pequena minoria", achatando uma diferença de **oito vezes** — observado em `cidade-de-deus` (91/8/1). Demais faixas e a convenção de desempate (sempre o rótulo mais fraco) inalteradas.
  - **(7b) Timeout nas chamadas LLM** (`LLM_TIMEOUT_MS = 180_000`, `config.py`): o SDK do Gemini bloqueia **indefinidamente** sem timeout explícito. Observado ao vivo durante a regeneração desta versão — um processo ficou **67 minutos** parado, 0% de CPU, dormindo num socket, sem voltar nem falhar (era o retry interno do SDK batendo em 429 sucessivos). Um timeout converte "trava para sempre" em erro que o chamador vê. 180s cobre com folga o pior caso medido (~110s numa chamada com thinking).
  - **PENDÊNCIA DESTA VERSÃO — as 3 narrativas NÃO foram regeneradas.** O código, a SPEC e os testes da v1.6.0 estão completos, mas a regeneração ao vivo esbarrou na **cota diária do free tier** do `gemini-2.5-flash` (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `limit: 20`), esgotada pelas sessões de diagnóstico do mesmo dia. Seis tentativas com backoff ao longo de 10 minutos devolveram 429 — não é janela curta, é o teto diário. **Consequência:** `resultado/*.json` e `frontend/js/data.js` seguem com as narrativas da **v1.5.0** (portanto sem `narrativa_bruta`/`edicao_flags`, com o rótulo antigo "uma pequena minoria" para 1%/3%, e com o diretor do `cure` ainda em `"黒沢清"`). O caminho foi validado ponta a ponta com LLM mockado sobre os dados reais dos três filmes (editor identidade ACEITO, editor que infla número DESCARTADO em 3/3). **Para concluir:** com cota disponível, `--slug <slug> --reuse-synthesis --tom narrativo --offline` nos três filmes (6 chamadas Gemini) + `python frontend/build_data.py`. O cache TMDB do `cure` foi propositalmente invalidado para que a correção do diretor seja aplicada na próxima execução (custa 3 requisições TMDB, só nesse filme).
  - **(8) Diretor em escrita latina** (§3[F]): o TMDB devolve o nome no alfabeto nativo quando pt-BR não tem tradução — `cure` publicou `"黒沢清"` na narrativa. Quando o nome pt-BR não é latino, o `credits` de `en-US` é consultado e a transliteração usada, com `diretor_transliterado: true` na ficha. No máximo 1 requisição extra, só para filmes nessa condição, reaproveitando a resposta `en-US` quando o fallback de sinopse já a buscou.
- **v1.5.0** (2026-07-25): fluência da narrativa (ritmo/registro) + marcação de perspectiva — a primeira mudança do §D2 motivada por QUALIDADE de prosa, não por uma infidelidade factual. Nenhum parâmetro congelado (§2) mudou; nenhuma invariante de honestidade das versões anteriores foi afrouxada.
  - **Diagnóstico (registrado por extenso na SPEC, §D2):** as narrativas entregues até a v1.4.1 são factualmente corretas mas soam mecânicas — forma sintática repetida (rótulo de peso + verbo de reporte + complemento, três vezes seguidas), comprimento de frase quase constante (25-35 palavras), densidade alta de verbos de reporte e nominalizações no lugar de verbos. **Causa provável:** o acúmulo de invariantes de honestidade das versões anteriores (peso ancorado, quantificador pré-computado, escopo por grupo, anti-spoiler, vocabulário "das notas") levou o modelo à ÚNICA forma sintática que satisfaz todas simultaneamente — relatar, com um verbo, o que cada grupo diz. **A correção:** prescrever ritmo, registro e marcação de perspectiva com a mesma precisão de código com que já se prescrevem os números, sem tocar em nenhuma regra de honestidade existente.
  - **(a) Regras de RITMO** (§D2, prompt): variação de comprimento de período (30-50 palavras alternadas com 3-10), pelo menos uma frase curta obrigatória, proibição de três períodos consecutivos de comprimento semelhante, proibição de repetir a estrutura de abertura entre períodos consecutivos, liberdade de posição para o rótulo de peso (não mais preso à abertura), conectivos de fala. Regras compartilhadas — presentes nas DUAS variantes da regra (c), pois não dependem do `share_real`.
  - **(b) Regras de REGISTRO** (§D2, prompt): descrever o filme diretamente após estabelecer quem fala (em vez de reintroduzir o sujeito a cada frase); verbos de reporte (elogia/destaca/aponta/relata/considera/classifica/menciona/ressalta/reconhece/expressa/descreve) limitados a 1 por movimento; preferência por verbos sobre nominalizações; advérbios intensificadores em -mente limitados a 1 em toda a narrativa; registro de "alguém contando de um filme para um amigo" — sem gíria, emoji, interpelação direta ou hipérbole. Também compartilhadas entre as duas variantes.
  - **(c) MARCAÇÃO DE PERSPECTIVA (regra nova, pedida pelo usuário) — só existe COM distribuição.** Motivação: ao remover os verbos de reporte (b), a fala de um grupo minoritário pode soar como fato do narrador, porque chega depois de o texto já ter estabelecido a leitura dominante. Pré-computação em CÓDIGO (`_marcacoes_por_bucket`/`_marcacao_perspectiva`, `synthesize.py`), por grupo, a partir do `share_real`: `dominante` = maior share do filme; `marcacao_perspectiva` = "nenhuma" se `share > dominante/3`, "simples" se `share <= dominante/3`, "antecipada" se `share <= dominante/10` (condição mais restritiva checada primeiro). Só existe com distribuição pelo MESMO motivo pelo qual a cota de coleta não pode alimentar esse cálculo (usar a cota apresentaria amostragem como prevalência, o defeito que a v1.2.1 proíbe). **Limiares são ponto de partida, calibráveis** — ao contrário das faixas de quantificador/peso, não vieram de evidência empírica prévia. O prompt exige ancoragem em todo trecho que fale de um grupo (o rótulo de peso já cumpre esse papel para o grupo dominante); `"simples"` exige um marcador em algum lugar do trecho ("para eles", "nessa leitura"); `"antecipada"` exige o marcador ANTES da primeira afirmação substantiva. Marcador de perspectiva é explicitamente distinguido de verbo de reporte no prompt (não conta para o limite da regra f) e é proibida carga depreciativa.
  - **(d) Telemetria `marcadores_perspectiva` (NOVO campo, mesmo padrão de `consensos_usados`/`quantificadores_usados`):** o narrador declara `{grupo, trecho}` por marcador usado. Validação pós-parsing (`_marcadores_validos`): grupo com marcação exigida precisa ter marcador declarado; trecho precisa aparecer literalmente no texto final; para "antecipada", o trecho precisa estar na MESMA frase da âncora do grupo (rótulo de peso/percentual) ou na frase IMEDIATAMENTE seguinte — aproximação por frase, já que os movimentos não têm marcação estrutural no texto final. Falha → 1 retentativa combinada (`_REFORCO_MARCADORES`); se persistir, `perspectiva_nao_marcada: true`. Lista vazia é válida por vacuidade quando nenhum grupo exige marcação (ex. 40/30/30 — nenhum passa nos limiares).
  - **(e) Exemplo few-shot ANTES/DEPOIS** embutido literalmente no prompt (só na variante COM distribuição, porque usa vocabulário de peso que a variante SEM distribuição proíbe) — descrito na SPEC como "o lever mais forte" contra a monotonia observada, por mostrar a forma desejada em vez de só descrevê-la. Marcado explicitamente como exemplo de ESTILO, não de conteúdo: os fatos e números de cada filme vêm sempre do relatório recebido.
  - **(f) Telemetria de fluência `metricas_fluencia` (NOVO campo, calculado em CÓDIGO, não pelo LLM):** `n_frases`, `media_palavras`, `cv_comprimento` (desvio padrão ÷ média de palavras por frase — mede variação, não comprimento em si), `frase_mais_curta`, `aberturas_repetidas` (frases consecutivas com a mesma primeira palavra), `verbos_reporte`, `adverbios_mente` (lista fechada de intensificadores, não todo advérbio em -mente). Gatilhos de 1 retentativa (`_REFORCO_FLUENCIA`), NUNCA bloqueiam: `cv_comprimento < 0.40` · nenhuma frase ≤10 palavras · `verbos_reporte > 3` · `adverbios_mente > 1` · `aberturas_repetidas > 0`. Se persistir, `fluencia_baixa: true`. Mesma ressalva de calibração da marcação de perspectiva: limiares são ponto de partida.
  - **(g) Render/CLI:** blocos compactos de `marcadores_perspectiva` (mesmo padrão do bloco de consensos) e resumo numérico de `metricas_fluencia`, exibidos no tom `narrativo`/`ambos`, após os blocos existentes; duas flags novas no aviso de terminal.
  - **(h) Emenda à invariante "só a regra (c) difere entre as variantes"** (v1.4.0, reafirmada com ressalva na v1.4.1): a marcação de perspectiva e o exemplo few-shot foram adicionados DENTRO da regra (c) COM distribuição — dependem do `share_real`, então pertencem a ela por construção. As regras de RITMO e REGISTRO, que não dependem de share, entraram nas partes compartilhadas do prompt, presentes e idênticas nas duas variantes. A invariante segue válida: o que muda é exatamente o que depende do dado.
- **v1.4.1** (2026-07-24): três correções pontuais no §D2, todas motivadas por defeitos reais na entrega da v1.4.0. Nenhum parâmetro congelado (§2) mudou; nenhuma etapa nova de pipeline.
  - **(a) Telemetria de quantificadores POR PAR — `quantificadores_usados` (NOVO campo na saída do narrador).** **A motivação é a reincidência:** é a **3ª ocorrência** do mesmo modo de falha (v1.2.2 por instrução → v1.2.3 por pré-computação → agora). Na v1.4.0, `the-invite-2026` usou "Quase todos" para `Atuações e química do elenco` (**20/30 = 67%**, rótulo pré-computado "a maioria"), e **a rede de segurança da v1.2.3 não pega**, porque ela é de **nível de bucket**: outro tema do mesmo grupo (`Direção e roteiro (geral)`, 25/30 = **83%**) dava lastro para "quase todos" existir em algum lugar do relatório. O buraco é estrutural — nenhuma checagem sobre a prosa sabe a QUAL tema um "quase todos" solto se refere. **A correção repete o padrão que funcionou no MOVIMENTO 2** (`consensos_usados`, v1.3.1): o narrador **declara** cada expressão de frequência junto do nome EXATO do tema de onde ela vem, e o CÓDIGO confere par a par contra o `rótulo_quantificador` pré-computado (`_quantificadores_validos`/`_forca_declarada`). Quantificador mais forte que o rótulo, ou tema inexistente → 1 retentativa combinada (`_REFORCO_QUANT_DECLARADO`); se persistir, alimenta a flag **já existente** `quantificador_suspeito`, agora com **duas** fontes (bucket + par), ambas ativas. Persistido no JSON e exibido no render como bloco compacto **com a conferência ao lado** (fração real → rótulo). Limitações deliberadas e documentadas: expressão fora da escala não é comparável (não flagga) e tema homônimo em dois grupos resolve pela força mais alta (não flagga na ambiguidade).
  - **(b) MOVIMENTO 2 pode ser OMITIDO — omissão autorizada explicitamente no prompt.** **O defeito:** na v1.4.0, o MOVIMENTO 2 do `the-invite-2026` trouxe juízos de qualidade **hedgeados** ("estilo visual eficaz", "abordagem arrojada"), violando o critério (a) de categoria — que a v1.3.1 escreveu justamente para esse filme. **Diagnóstico: pressão de preenchimento.** O filme tem poucos temas descritivos, o prompt pedia "3-5 frases" e só admitia encolher ("pode ser curto"); o modelo completou o espaço com avaliação suavizada, que é a violação disfarçada de descrição. **A correção não é mais uma proibição — é uma AUTORIZAÇÃO:** com menos de duas propriedades aprovadas nos três critérios, o movimento deve ser CURTO (1 frase) ou **AUSENTE**, passando direto ao MOVIMENTO 3. Omitir é o comportamento **correto**, não falha; preencher com juízo hedgeado é **pior** que não ter o movimento. `consensos_usados: []` é o resultado esperado nesse caso — e a validação da v1.3.1 **já** tratava lista vazia como válida por vacuidade (comportamento confirmado por teste, não alterado).
  - **(c) Invariante de vocabulário: NOTAS × REVIEWS.** **A distinção que faltava explicitar:** os rótulos de peso derivam do histograma de **notas** (todo mundo que avaliou); os temas derivam das **reviews com texto** (subconjunto). São populações diferentes e não compartilham denominador. Registrada em §D2 (tabela + regra) e em §3[G] (onde a distribuição é documentada), e reforçada dentro da regra (c) invertida do prompt: **OBRIGATÓRIO** "das notas", **PROIBIDO** "das reviews"/"dos espectadores"/"do público" ao expressar peso; frequência de tema continua em relação às reviews analisadas. **Checagem barata** (`_vocabulario_peso_ok`): rótulos inequívocos de peso → janela seguinte; qualquer percentual → janela anterior. A segunda passada existe porque **"a maioria" é ambígua** (também é rótulo de quantificador de tema, e "a maioria das reviews negativas analisadas" é a forma CORRETA da regra (d)) — ancorar no percentual desambigua sem flaggar prosa certa. Violação → 1 retentativa (`_REFORCO_VOCABULARIO_PESO`); se persistir, flag nova `vocabulario_peso_suspeito`.
  - **(d) Emenda ao "byte a byte" da v1.4.0:** a v1.4.0 registrava que `build_narrator_prompt(False)` devolvia o prompt da v1.3.1 byte a byte. As correções (a) e (b) vivem nas partes **compartilhadas** do prompt e valem nas duas variantes, então essa igualdade histórica deixou de existir. A invariante que a comparação A/B realmente precisa — **só a regra (c) difere entre as variantes** — continua de pé e verificada em teste.
- **v1.4.0** (2026-07-21): **distribuição real de notas** coletada e a regra de prevalência do §D2 **invertida** — a maior mudança desde a v1.
  - **A motivação (feedback de usuários reais, não hipótese):** filmes amplamente aclamados *soavam divididos*, porque os três grupos recebiam o mesmo peso textual e visual. `cidade-de-deus` tem **91%** das notas na faixa alta e era apresentado com a mesma proeminência dada ao grupo de **1%**. Infidelidade **por omissão**: cada frase verdadeira, o conjunto comunicando controvérsia onde havia consenso.
  - **A v1.2.1 previu esta correção.** Ela proibiu prevalência *porque o dado não existia*, e registrou em "Candidatos à próxima versão" que a correção de raiz seria coletar o histograma (inclusive o custo: 1 requisição cacheável — confirmado exato). A regra não foi afrouxada; o dado que faltava chegou.
  - **(a) Princípio norteador registrado (§0):** *neutralidade de TRATAMENTO, não de fato* — formato idêntico para os três grupos; a assimetria vem dos dados. Com duas invariantes intocadas: **share por faixa NÃO é nota média** (são três números que particionam a população; a proibição de score agregado segue escrita dentro da própria regra invertida) e **a minoria mantém o mesmo rigor analítico** (menos espaço na prosa, mesma seriedade; na interface, um grupo de 1% mantém seus 6 temas e barras).
  - **(b) Coleta (§3[G], `FASE_HISTOGRAMA.md`):** endpoint CSI `/csi/film/<slug>/rating-histogram/`, 1 requisição cacheada por filme. Três armadilhas reais tratadas — nível zerado troca `<a>` por `<span>` (buscar `a.barcolumn` perderia os zeros **em silêncio** e inflaria o total justo em filmes pequenos); o `_sr-only` da barra **abrevia** (`23.4K`) e é imprestável como fonte, o `title` é exato; singular/plural/"No" no `title`. Validação estrutural exige os 10 níveis canônicos, senão `None`.
  - **(c) Agregação em código:** `share_real` por bucket, percentual inteiro, cada bucket arredondado **independentemente** — a soma pode dar 99 ou 101 (`cure`: 3+17+79=99), aceito e documentado em vez de redistribuir o resto e tornar algum bucket menos fiel ao próprio dado. A interface nunca exibe a soma.
  - **(d) Cota 50/20/30 MANTIDA, com racional explícito:** cota é *amostragem estratificada* (profundidade igual por perspectiva — entender o que incomodou o grupo de 1% exige ~50 reviews lidas, não 1); peso é prevalência, agora exibida à parte. **Profundidade igual, peso informado.**
  - **(e) Regra (c) do §D2 em duas variantes, escolhidas pelo CÓDIGO:** sem distribuição, `build_narrator_prompt(False)` devolve o prompt da v1.3.1 **byte a byte** (verificado em teste) — o fallback é o texto anterior, não uma reescrita parecida. Com distribuição: ancoragem obrigatória no `rotulo_peso`, abertura do MOVIMENTO 3 pela perspectiva de maior peso, ênfase proporcional e respeito explícito à minoria. **Só a regra (c) difere** entre as variantes, para a comparação A/B isolar a mudança.
  - **(f) `rotulo_peso` pré-computado** (mesmo princípio da v1.2.3/v1.1.1): mapa determinístico com bordas sempre para o rótulo **mais fraco** (`70% → "a maioria"`, não "a grande maioria" — que começa de fato em 71%). Sempre entregue junto do percentual, que é o que impede o rótulo de virar retórica.
  - **(g) A rede de prevalência muda de sinal:** com distribuição, o detector da v1.2.1 é **desligado** (as palavras que ele caça passaram a ser exigidas) e quem cobre o eixo é a nova checagem de **ancoragem** (`peso_nao_ancorado`, 1 retentativa com `_REFORCO_ANCORAGEM`). Sem distribuição, o detector original continua ativo. **Não há flag de configuração — a presença do dado é o interruptor.**
  - **(h) Render e frontend:** `· ~X% das notas` no header, formato idêntico nos três; disclaimer com duas variantes; frontend tolera JSON sem `distribuicao`. Ordem visual dos grupos **não** é reordenada por peso — só a prosa do MOVIMENTO 3 abre pelo dominante.
  - **Resultado medido nas 3 demos:** ancoragem 3/3 filmes, abertura pelo grupo dominante 3/3, zero `peso_nao_ancorado`. Shares reais: `the-invite-2026` 3/18/79, `cure` 3/17/79, `cidade-de-deus` 1/8/91.
- **v1.3.1** (2026-07-20): regra do MOVIMENTO 2 reescrita (categoria/presença/não-contradição) + telemetria `consensos_usados` (§D2).
  - **O defeito real:** na primeira execução da narrativa em três movimentos (v1.3.0), o MOVIMENTO 2 de `the-invite-2026` afirmou "elenco com atuações marcantes" e "roteiro elogiado por sua inteligência" como fatos neutros de experiência — mas o grupo negativas tem literalmente os temas "Atuações e direção questionáveis" (~15/50) e "Humor e roteiro fracos/entediantes" (~27/50), uma contradição direta, não um consenso. **Diagnóstico:** erro de CATEGORIA — o narrador importou um juízo AVALIATIVO (qualidade de atuação/roteiro, que é sempre disputado) como se fosse uma propriedade DESCRITIVA (ritmo/tom/atmosfera, sobre a qual pode haver consenso factual mesmo com valência diferente). A regra da v1.3.0 pedia "características em que os grupos concordam factualmente" mas não distinguia essas duas categorias nem dava um exemplo do modo de falha.
  - **(a) Regra reescrita com três critérios obrigatórios** (§D2, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`): **(i) CRITÉRIO DE CATEGORIA** — só propriedades descritivas (ritmo, tom, atmosfera, intensidade, estrutura, ambientação, nível de violência, ambiguidade, densidade); PROIBIDO qualquer juízo de qualidade, que pertence sempre ao MOVIMENTO 3. **(ii) CRITÉRIO DE PRESENÇA** — a propriedade precisa vir de temas de PELO MENOS DOIS grupos com o mesmo núcleo factual (valência pode divergir). **(iii) CRITÉRIO DE NÃO-CONTRADIÇÃO** — se qualquer grupo nega o núcleo factual (não só diverge na avaliação), a propriedade é desqualificada. O prompt inclui os dois exemplos pedidos: o POSITIVO (ritmo lento/tedioso vs lento/deliberado → consenso válido) e o NEGATIVO — o caso real das atuações do `the-invite-2026`, documentado por extenso como o modo de falha a evitar.
  - **(b) Telemetria `consensos_usados` (NOVO campo na saída do narrador):** o LLM agora declara, para cada propriedade usada no MOVIMENTO 2, `{propriedade, grupos_de_origem, temas_de_origem}` — grupos restritos a negativas/medianas/positivas, temas com o nome EXATO como aparece no relatório. É o artefato de revisão humana que substitui o exercício manual (recalcular frações e comparar com o texto) feito no relatório da v1.3.0 para achar o defeito do `the-invite-2026` — agora fica pronto em toda execução. Persistido no JSON do filme (campo global `consensos_usados`) e exibido no render de terminal (tom `narrativo`/`ambos`) como bloco compacto após a prosa.
  - **(c) Validação pós-parsing** (`_consensos_validos`, `synthesize.py`): confere que todo grupo citado é um dos três nomes válidos e existe no relatório, e que todo tema citado corresponde, por igualdade exata de string, a um tema real de algum dos grupos citados naquele item. Falha → 1 retentativa combinada com as demais validações de prosa (reforço `_REFORCO_CONSENSOS`); se persistir, aceita e sinaliza `consenso_suspeito: true` em `narrativa_flags` — telemetria visível, mesma política das demais flags do §D2. Lista vazia (`[]`) é válida — o MOVIMENTO 2 pode não ter nenhuma propriedade que passe nos três critérios.
  - **(d) Correção retroativa documentada em §3a:** durante a regeneração das narrativas da v1.3.0, a desambiguação por ano do TMDB (§3a) mostrou um bug real — escolher o primeiro resultado do ano certo, em vez de desempatar por popularidade, pegava o filme errado para "Cure" 1997 (um documentário obscuro em vez do filme de Kiyoshi Kurosawa). Corrigido antes da entrega da v1.3.0; texto de §3a atualizado nesta versão para refletir o comportamento real do código.
- **v1.3.0** (2026-07-20): ficha técnica via TMDB (§3a/[F], NOVO) + narrativa do narrador reestruturada em TRÊS MOVIMENTOS (§D2 reescrito).
  - **(a) Ficha do filme — TMDB** (`ficha.py`, NOVO módulo): dado título/ano do filme (derivados do slug por default, `titulo_ano_de_slug`; override via `--titulo`/`--ano`), busca `/search/movie` (com desambiguação por ano — necessária para títulos comuns como "The Invite", que têm múltiplas entradas no TMDB) e depois `/movie/{id}?language=pt-BR&append_to_response=credits`. Extrai título pt-BR, sinopse oficial, gêneros, duração, diretor e ano. Cache em disco no mesmo padrão do cache do Letterboxd (`<cache-dir>/_tmdb/`), chave por título normalizado + ano, nunca rebusca filme já buscado (inclusive "não encontrado"). **Aditiva por design:** qualquer falha (chave ausente, rede, HTTP, sem resultado) retorna `(None, aviso)` — NUNCA levanta; o pipeline (coleta, síntese, narrador, render) segue normalmente com `ficha: null` no JSON, e o CLI só imprime o aviso em stderr. Campo global `ficha` no output (§4). Fallback de sinopse: overview pt-BR vazio → busca `en-US`, sinalizado com `sinopse_fallback_en: true` (nunca some silenciosamente, nunca finge ser pt-BR).
  - **(b) Emenda de anti-spoiler — sinopse oficial como fonte do Movimento 1** (§3[D], "Anti-spoiler: escopo da proteção e risco aceito"): a regra de "zero conteúdo de trama" ganha uma exceção estreita — a sinopse OFICIAL do TMDB (material de divulgação curado, categoria equivalente ao texto de pôster/contracapa) pode ser usada, condensada, como fonte do novo Movimento 1 da narrativa. Sinopses de terceiros e qualquer expansão com conhecimento externo do modelo continuam PROIBIDAS. O prompt instrui o narrador a usar só a parte de premissa da sinopse caso ela pareça revelar algo além disso — julgamento do LLM, não checagem mecânica (mesmo espírito de risco aceito da v1.1.3).
  - **(c) Narrador em três movimentos** (§D2, `NARRATOR_SYSTEM_PROMPT`/`_serialize_output_for_narrator` em `synthesize.py`): a prosa única da v1.2.x vira MOVIMENTO 1 — O FILME (premissa da ficha, condicional à existência de ficha; sem ficha, pula direto pro Movimento 2), MOVIMENTO 2 — A EXPERIÊNCIA (consensos factuais entre grupos, tom neutro sem valência, avaliação fica pro Movimento 3), MOVIMENTO 3 — O CONTRASTE (perspectivas dos 3 grupos, enxuto — prioriza os 2-3 temas mais fortes de cada grupo em vez de cobrir todos os 6 possíveis, já que a interface exibe as barras tema a tema). Nenhum subtítulo aparece no texto final. Todas as invariantes de v1.2.0–v1.2.3 permanecem em vigor (tamanho de grupo/anti-prevalência, quantificador pré-computado, escopo por grupo, anti-spoiler, forma) — a reestruturação organiza a prosa em torno delas, não as substitui. Alvo de tamanho ajustado de 200–350 para **250–400 palavras** (o Movimento 1 adiciona conteúdo quando há ficha).
  - **(d) Validações pós-parsing inalteradas:** aspas/idioma/escopo/prevalência/quantificador continuam operando sobre o texto final completo, independente de quantos movimentos o compõem — nenhuma mudança de mecânica, só de conteúdo do prompt.
  - **(e) Render/CLI:** novo campo `ficha` no JSON (`null` quando ausente); resumo de uma linha da ficha no render de terminal (título/ano/diretor/gênero/duração) quando presente, sem interferir nos avisos e metadados existentes; flags `--titulo`, `--ano`, `--no-ficha` no CLI.
- **v1.2.3** (2026-07-19): quantificadores pré-computados pelo CÓDIGO — o LLM deixa de escolher (§D2, regra "d. PROPORÇÕES").
  - **A reincidência:** a calibração por instrução (v1.2.2 — o LLM calculava a fração e escolhia o rótulo por uma tabela dada no prompt) reduziu mas não eliminou o modo de falha. Na primeira regeneração das 3 narrativas pós-fix v1.2.2, "quase todos"/"praticamente todos" foi aplicado a frações de 65–70% **2 vezes** — exatamente a condição de escalada que o próprio changelog da v1.2.2 previu ("um checador numérico pós-parsing é candidato futuro caso a inflação reincida").
  - **O princípio da correção:** mesmo da v1.1.1 (denominador de `n_reviews_analisadas`) — o LLM não decide número nem rótulo numérico; **o código é a autoridade**.
  - **(a) Pré-computação** (`synthesize.py`): `_serialize_output_for_narrator` agora injeta, por tema, `fracao` (percentual arredondado) e `rótulo_quantificador` — resolvidos por `_fracao_e_rotulo`/`_rotulo_quantificador`, mapa determinístico com as MESMAS faixas da v1.2.2. Sobreposições nas fronteiras (40–50%, 50–60%, e os pontos exatos 25/50/80%) resolvidas SEMPRE para o rótulo mais fraco, por construção do algoritmo (itera do mais fraco pro mais forte, retorna o primeiro match) — documentado por extenso no código-fonte. O prompt (d) mudou de "calcule e escolha pela tabela" para "use o `rótulo_quantificador` fornecido; PROIBIDO um mais forte; mais fraco é permitido".
  - **(b) Rede de segurança complementar** (validação pós-parsing, nível de bucket, não por tema): se a prosa contém "quase todos"/"praticamente todos" e NENHUM tema do filme tem fração ≥80%, 1 retentativa com reforço (`_REFORCO_QUANTIFICADOR`); se persistir, `quantificador_suspeito: true` em `narrativa_flags`. Deliberadamente restrita a esse quantificador — é o único modo de falha observado; não cobre uso indevido dos demais rótulos (limitação documentada).
  - **Resultado esperado:** zero violações na regeneração das 3 narrativas — qualquer quantificador fora da faixa pré-computada agora é bug de implementação, não variância do modelo (ver `ACEITE_FINAL.md`/relatório da sessão para a conferência).
- **v1.2.2** (2026-07-19): calibração numérica dos quantificadores da narrativa (§D2, regra "d. PROPORÇÕES").
  - **O defeito:** na narrativa do filme *Cure*, o narrador escreveu "quase todos os elogios neste grupo destacam a atmosfera" para um tema de ~15 de 30 (50%) — inflação retórica. Nos outros dois filmes testados os quantificadores saíram honestos; defeito de **variância**, não sistemático, mas incompatível com a promessa central de frequência honesta do produto.
  - **A correção:** mapa explícito quantificador → faixa percentual, calculado sobre `mencoes_aproximadas / n_reviews_analisadas` do grupo: "quase todos"/"praticamente todos" só ≥80%; "a maioria"/"mais da metade" 50–80%; "cerca de metade" 40–60%; "muitos"/"boa parte" 25–50%; "alguns"/"uma parte" 10–25%; "poucos" <10%. Em caso de fronteira ambígua entre duas faixas, instrução explícita de usar sempre a mais **fraca** — subestimar é aceitável, inflar não é.
  - **Verificação:** permanece **humana** (leitura adversarial, quantificador contra número real) nesta versão — sem validador pós-parsing automático. Candidato futuro se a inflação reincidir (ver "Candidatos à próxima versão").
- **v1.2.1** (2026-07-19): corrige uma classe de infidelidade do modo narrativo — **cota de amostragem apresentada como distribuição da recepção**.
  - **O defeito:** os buckets têm tamanhos fixados pela cota de coleta (50/20/30 = 10 válidas × nº de níveis do bucket), que **não** refletem a distribuição real da recepção. A narrativa da v1.2.0 tirava inferências de prevalência das cotas — "grupo considerável", "igualmente expressivo", "minoria de opiniões medianas", "recepção polarizada". As medianas serão "minoria" em todo filme, para sempre, por construção (2 níveis vs 5/3) — logo qualquer afirmação de prevalência entre grupos é infiel.
  - **(a) Invariante nova no prompt §D2** (regra "c. TAMANHO DOS GRUPOS — REGRA CRÍTICA"): os tamanhos vêm do método de coleta, não da recepção; PROIBIDO comparar tamanhos entre grupos ou inferir prevalência global (maioria/minoria/grupo maior ou menor/igualmente expressivo/polarizada/dividida/consenso). Proporções só DENTRO de um grupo, sempre ancoradas ("mais da metade das reviews negativas analisadas"). Grupos apresentados como PERSPECTIVAS ("entre quem não gostou...", "já entre quem amou..."), nunca como fatias quantificadas do público. A antiga regra de proporções (que dava "uma minoria mediana" como exemplo) foi reescrita.
  - **(b) Telemetria** (validação pós-parsing da narrativa): checagem de marcadores de prevalência entre grupos, mesma mecânica das demais (1 retentativa combinada; flag `prevalencia_suspeita: true` em `narrativa_flags` se persistir; visível no render). Heurística acento-sensível como as outras — rede de segurança; a defesa principal é a invariante (a) do prompt.
- **v1.2.0** (2026-07-19): etapa **[D2] narrador** + flag `--tom` (mecanismo de desenvolvimento para A/B de saída).
  - **(a) Narrador pós-síntese** (§D2): `narrate_output(output)` faz UMA chamada LLM para o filme inteiro e reescreve o relatório validado como prosa (200–350 palavras, pt-BR). **Decisão de arquitetura:** o narrador lê **exclusivamente o JSON validado** (temas/números/observacoes dos 3 buckets + total), **nunca as reviews brutas** — garantido por construção (a entrada é o dict de `build_output`, que não serializa texto de review). Justificativa anti-embelezamento/anti-spoiler registrada em §D2. Prompt fixo do narrador documentado na íntegra (invariantes a–g: papel, fidelidade, proporções, estrutura dos 3 grupos, escopo, anti-spoiler em profundidade, forma).
  - **(b) Validações de prosa reaproveitadas** (§D): sobre a narrativa aplicam-se aspas (remoção mecânica → `aspas_removidas`), idioma e escopo (1 retentativa combinada; `idioma_invalido`/`escopo_suspeito`), com as mesmas flags/telemetria da síntese. Saída via JSON `{"narrativa": ...}` reusa os adaptadores em modo JSON e o parsing defensivo do §D.
  - **(c) Flag `--tom {estruturado,narrativo,ambos}`** (default `estruturado` — comportamento histórico intacto): **MECANISMO DE DESENVOLVIMENTO** para o A/B humano entre saída estruturada e narrativa; a v2 consolidará um tom único após avaliação. `narrativo`/`ambos` não escondem metadados nem avisos — modo degradado permanece visível nos dois tons. Campo `narrativa` (+ `narrativa_flags`) no JSON. Atalho `--reuse-synthesis` compara tons sobre a MESMA síntese gastando só a chamada do narrador.
- **v1.1.4** (2026-07-19): fechamento da v1 — resolve os dois gaps do `ACEITE_FINAL.md` por emenda de spec + mudança mínima de render.
  - **(a) §3[C] — texto bruto removido, URL no lugar.** Removida a cláusula "se houver 1–2 reviews, exibir os textos brutos com aviso" de buckets `sem_analise`. **Motivo:** contradizia o princípio do cabeçalho da spec (trade-offs resolvem a favor de evitar spoiler) — texto integral sem a camada anti-spoiler do LLM é o caminho de maior risco de spoiler do produto, e a flag de spoiler do Letterboxd é autodeclarada. **Substituto (código, `render.py`):** bucket `sem_analise` passa a exibir, além da contagem, `→ N review(s) disponíveis em https://letterboxd.com/film/<slug>/reviews/`, no terminal e no JSON (campo global novo `reviews_url`). Resolve o gap 1 do aceite (o render não exibia texto bruto — agora, por decisão de design, não deve mesmo, e aponta para a fonte).
  - **(b) §5.2 — critério reescrito para o comportamento real.** O critério original presumia cascata de relaxamento/modo degradado em `cidade-de-deus`; o aceite mostrou que o filme é **coberto demais por nível** (10 válidas ≥150 chars em cada um dos 10 níveis, `filtro_aplicado=150` em todos, zero relaxação — ver `ACEITE_FINAL.md`). Novo texto: o filtro de comprimento descarta as curtas em volume, os níveis fecham dentro do teto de paginação, e a análise permanece útil e corretamente escopada. A demonstração da **cascata de relaxamento** e do **modo degradado** é atribuída ao **critério 3** (filme minúsculo), onde ocorreu de fato (`filtro_aplicado` 50/0). Previsão empírica da spec corrigida com dado real.
  - **(c) Selo de aceite.** Nova seção "Status de aceite da v1" (fim do documento) com o veredito por critério e a evidência.
- **v1.1.3** (2026-07-19): registro de risco aceito na proteção anti-spoiler (§3 [D], subseção "Anti-spoiler: escopo da proteção e risco aceito"). A zona cinzenta "mecanismo/dispositivo central da trama" é risco aceito e não deve ser endurecida — endurecer degradaria a especificidade dos temas em todos os filmes para evitar um falso negativo raro e tolerável. Decisão do usuário, validada com juiz humano que conhecia o filme (*Cure*, 1997). Nenhuma mudança de código ou de parâmetro — apenas documentação da fronteira de decisão. (Bateria de aceite §5 dos critérios 2 e 3 executada nesta data — ver `ACEITE_FINAL.md`.)
- **v1.1.2** (2026-07-19): reengenharia do prompt §D + validações pós-parsing, motivadas por evidência empírica da comparação de modelos (`resultado/comparacao/COMPARACAO.md`).
  - **(a) Preâmbulo de papel por bucket** (§3 [D]): NOVO texto antes das instruções invariantes, parametrizado por bucket (nome + intervalo de notas) — não por provider/modelo, que continuam recebendo prompt byte-idêntico para o mesmo bucket. **Motivação:** o flash-lite, com o prompt v1.1.1 (sem preâmbulo), gerou `observacao_geral: "a maioria dos críticos considera o filme um fracasso"` a partir do bucket NEGATIVAS — generalizando um recorte filtrado por construção (só notas ≤2.5) para a recepção geral do filme. O preâmbulo explica ao modelo que ele só vê uma faixa de nota, que esse recorte é enviesado por construção, e proíbe explicitamente generalizações como "os críticos"/"a maioria"/"o consenso"/"a recepção do filme" — ataca o erro na raiz do enquadramento, antes de qualquer instrução de formato.
  - **(b) Regras de aspas e idioma como invariantes §D** (item 6 e 7 da lista de instruções fixas, novos): proibido usar aspas de citação em `exemplo_parafraseado` (motivado pelo 2.5-flash ter citado reviews entre aspas, violando a regra de paráfrase); reforço explícito de que TODOS os campos de texto — incluindo nomes de temas — devem estar em pt-BR.
  - **(c) Validações pós-parsing como camada de código** (não fazem parte do prompt): idioma (heurística de stopwords, 1 retentativa, `idioma_invalido` se persistir), aspas (remoção mecânica, sem retentativa, `aspas_removidas` por tema), escopo (marcadores literais de generalização, 1 retentativa, `escopo_suspeito` se persistir). Idioma e escopo compartilham UMA retentativa combinada quando ambos falham na mesma resposta (não duas separadas) — mantém o orçamento de chamadas por bucket previsível (máx. 3 chamadas no pior caso: 1 + retentativa de JSON + retentativa de validação). Todas as flags são telemetria visível (JSON + terminal), não correção silenciosa — a defesa principal contra vazamento de escopo é o preâmbulo (a), estas são rede de segurança.
  - **(d) Default `gemini-2.5-flash` ratificado com evidência** (§3 [D]): a comparação de modelos rodou o MESMO prompt sobre o MESMO corpus em `gemini-2.5-flash-lite` e `gemini-2.5-flash`; o flash-lite cometeu as 3 violações de instrução que motivaram (a) e (b) acima, o 2.5-flash não repetiu nenhuma. O valor do default não mudou (já era `gemini-2.5-flash` desde v1.1.1), mas agora está documentado com a evidência que o justifica, não só como escolha arbitrária.
- **v1.1.1** (2026-07-18): correções e clarificações da Fase 1, sem alterar nenhum parâmetro congelado de §2.
  - **(a) Correções factuais de Fase 1** (§2.1, §3 [A]/[C'], §6): detector de truncamento = **marcador de colapso `.collapsed-text`** (não `data-full-text-url`, que é quase universal e não discrimina); endpoint de busca real = `/s/search/films/<query>/` (AJAX; a URL de página humana é um shell React vazio); dedup/cache de review por **viewing id via `p[data-likeable-identifier]`**; página além da última retorna **200 com lista vazia** (sinal de parada, não erro).
  - **(b) Cache em `resultado/cache/`** (§3 [B]): registrado como **caminho provisório** — consequência da restrição de arquivos da Fase 1, não decisão de design. Ratificado para v1.1.1 (mudar agora é churn sem ganho); candidato a desacoplar para `cache/` ou `.cache/` na v1.2, já que `resultado/` (entrega descartável/versionável) e o cache (estado reconstruível caro) têm ciclos de vida opostos.
  - **(c) Sem backfill de cota na v1.1.1** (§3 [C'].5): se o completamento de uma truncada falhar e ela for descartada, o nível fecha com a cota reduzida (ex. 9/10), sem repor — shortfall fica visível via `n_descartadas_truncamento`, e o piso-de-3 + modo `sem_analise` já cobrem o caso degenerado. Anotada para v1.2 a distinção entre backfill barato (repor da lista de brutas já paginadas, 1 requisição por reposição — candidato) e backfill caro (repaginar o nível — não é candidato).
  - **(d) Detector de spoiler apertado** (§2.1): ancorado na frase-placeholder **exata** do Letterboxd, substituindo o match por substring solta ("may contain spoilers") que tinha falso positivo em prosa legítima. Ressalva explícita mantida: localização da interface do Letterboxd quebraria o detector em silêncio; nenhum teste automatizado cobre esse cenário.
  - **(e) Suposição aberta registrada, não como coberta** (§3 [C'].6): o comportamento do endpoint `/s/full-text/` para review truncada+spoiler é assumido (devolver o placeholder), não verificado ao vivo — só coberto por fixture sintética. Instrução operacional adicionada: confirmar com 1 requisição se o caso aparecer numa coleta futura.
  - **(f) Denominador e clamp como regra de spec** (§3 [D]): corrigido bug onde o código confiava no `n_reviews_analisadas` devolvido pelo LLM (usando a contagem real só como fallback) — invertido: o código é **sempre** a autoridade do denominador, valor do LLM é ignorado. Adicionado clamp do numerador `mencoes_aproximadas` a `[0, n_reviews_analisadas]`, com o valor original preservado em `mencoes_valor_original` e sinalizado em `mencoes_clampadas` quando o clamp atua — visibilidade de alucinação, não correção silenciosa.
  - **(g) Síntese provider-agnóstica** (§3 [D]): interface de cliente injetável formalizada como contrato (`client_call(system, user, model) -> str`). Providers suportados: **Gemini** (default operacional desta versão) e **Anthropic**; seleção via `--provider` ou auto-detecção pela chave de API presente no ambiente (erro claro se ambas ou nenhuma). Instruções fixas do prompt continuam byte-idênticas entre providers.
- **v1.1.0** (2026-07-18): (1) cota de 10 reviews válidas POR NÍVEL de nota substitui alvo de 20 por bucket — buckets resultantes 50/20/30, cascata movida para o nível, coleta intercalada removida por desnecessária; (2) regra "nunca pela metade": texto completo obrigatório para reviews truncadas via `data-full-text-url`, com detector de truncamento como item de teste crítico e descarte registrado em caso de falha — promovido de incógnita (era seção 6.3) para requisito (C').
- **v1.0.0** (2026-07-18): spec inicial, incorporando resultados da Fase 0 (`RESULTADO.md`).

---

## Status de aceite da v1

**v1 fechada sob v1.1.4** (2026-07-19). Vereditos mecânicos verificados pelo pipeline; qualidade dos temas e ausência de spoiler nos exemplos são de juízo **humano** (aplicado onde indicado).

| # | Critério (§5) | Veredito | Evidência |
|---|---|---|---|
| 1 | Filme popular: 10 níveis completos, temas coerentes, zero spoilers | ✅ | `resultado/oppenheimer-2023.json` (10 níveis × 10 válidas, smoke test); `resultado/cure.json` (juiz humano conhecia o filme — ver risco aceito §3[D]) |
| 2 | Fanbase "review curta": filtro descarta curtas em volume, níveis fecham no teto, análise útil e escopada | ✅ | `ACEITE_FINAL.md` §5.2; `resultado/cidade-de-deus.json` (~76 curtas descartadas, 3 buckets `completo`, observações escopadas) |
| 3 | Filme obscuro: modo degradado severo, piso de 3 respeitado, `sem_analise` avisa (contagem + `reviews_url`) e não inventa temas; cascata de relaxamento exercitada | ✅ | `ACEITE_FINAL.md` §5.3; `resultado/como-fazer-um-curta-metragem-experimental-cult-e-pseudo-intelectual.json` (3 buckets `sem_analise` 1/2/2, `filtro_aplicado` 0/50/150, 0 chamadas Gemini) |
| 4 | Nenhum texto truncado chega ao LLM | ✅ | Smoke `oppenheimer` (100 reviews ao LLM, 0 parcial, 59 truncadas completadas); `cure.json`/`cidade-de-deus.json` (`n_descartadas_truncamento=0`) |
| 5 | Segunda execução: zero requisições de rede (100% cache) | ✅ | Verificado em execução `--offline` do `oppenheimer` (0 rede, 78 cache hits); `tests/test_cache.py` |

§5.6 (orçamento de requisições por filme novo) respeitado em todas as execuções: `cure` 83, `cidade-de-deus` 68, minúsculo 15 — todas dentro do teto.

Evidência transversal de qualidade de instrução: `resultado/comparacao/COMPARACAO.md` (comparação de modelos que motivou o preâmbulo de papel e o default `gemini-2.5-flash` da v1.1.2).

**Pendência de verificação contínua (NÃO bloqueante):** *ground truth* manual das contagens de menções (`mencoes_aproximadas`) — na fila do usuário. As frequências são estimativas do LLM, clampadas a `[0, n_reviews_analisadas]` pelo código (v1.1.1); a aferição da sua acurácia contra contagem manual real é acompanhamento pós-v1, não requisito de fechamento.

---

## Candidatos à próxima versão (pós-v1.2)

- ~~**Histograma de distribuição real de notas (torna prevalência legítima em vez de proibida).**~~ **ENTREGUE na v1.4.0** (§0, §3[G], §D2) — o texto original do candidato fica abaixo como registro de que a v1.2.1 já previa esta correção de raiz, inclusive o custo estimado (1 requisição extra, cacheável), que se confirmou exato.
- *(candidato original, cumprido)* **Histograma de distribuição real de notas.** A v1.2.1 **proíbe** afirmações de prevalência entre grupos porque as cotas de coleta (50/20/30) não são a distribuição da recepção. A correção de raiz — em vez da proibição — é **coletar o histograma de notas da página do filme no Letterboxd** (a barra de distribuição de ratings; **1 requisição extra** por filme, cacheável). Com a distribuição real disponível, o narrador **e** o render estruturado poderiam fazer afirmações de prevalência **legítimas e ancoradas nos dados** ("a maior parte das avaliações fica na faixa alta"), e o `--tom` narrativo deixaria de ter uma invariante puramente restritiva. Enquanto o histograma não existe no pipeline, a proibição da v1.2.1 é o comportamento correto. *(Também destrava a distinção "bucket vazio porque ninguém odiou" vs "porque ninguém assistiu" com número real, não só o total observado do rodapé.)*
- **Validador pós-parsing por tema (não só o quantificador mais forte).** A v1.2.3 pré-computa o rótulo (código como autoridade) e adiciona uma rede de segurança em nível de BUCKET restrita a "quase todos"/"praticamente todos" — deliberadamente não cobre uso indevido dos demais rótulos (ex.: "poucos" aplicado a um tema de 40%). Candidato futuro: correspondência por `tema` no texto da narrativa, recalcular a fração daquele tema específico e conferir contra QUALQUER rótulo usado, não só o mais forte — mesma mecânica de retentativa + flag das demais validações de prosa. Só vale a pena se o padrão de uso indevido de rótulos mais fracos aparecer na prática; nenhuma evidência disso até a v1.2.3.
- **Cache em `cache/`/`.cache/` na raiz** (desacoplar de `resultado/`, ver §3[B]) e **backfill barato de cota** (§3[C'].5) — candidatos herdados da v1.1.x.