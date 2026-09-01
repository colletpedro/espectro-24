# Espectro 24 — Especificação v1.9.25

**Data:** 2026-08-26
**Status:** v1 fechada (aceite em "Status de aceite da v1", fim do documento). **v1.9.6 puxa o único lever que a v1.9.5 mediu como capaz de mover a cobertura temporal: a ORDENAÇÃO (§2.3).** A v1.9.5 provou, com número, que profundidade de PÁGINA não compra tempo — a mediana do catálogo é de 1783 páginas para cobrir um ano contra um teto de plataforma de 256, e as 256 páginas expostas sob `by/added` são as ~3000 adições mais recentes. Esta versão (1) dá ao `Fetcher` **retentativa com backoff para erro de TRANSPORTE** — e só de transporte: 403, `AntiBotError` e o SEGUNDO 503 do lote continuam parando imediatamente, porque retentar bloqueio é evasão (§2.4); (2) promove `dias_por_100_paginas` a **métrica de primeira classe**, calculada na coleta e gravada em `meta.json` — é ela que separa as duas populações de filme e decide quem precisa de quê (§3[B']); e (3) coleta uma **passada SELETIVA sob `by/added-earliest`** só nos filmes abaixo do limiar dessa métrica, somando material genuinamente antigo ao bruto por incrementalidade (§2.3), sem tocar em quem já é bem servido pela profundidade sob `by/added`. Executada em 12 de 35 filmes por 610 requisições, a passada leva a janela `p5-p95` do bruto de **47 para 1487 dias** de mediana e revela que o material antigo é **2,4× mais longo** que o recente (55% abaixo de `min_chars` contra 77%) — achado que interage direto com o filtro e com a estratificação. A mudança de SELEÇÃO que as duas pontas agora tornam possível é **medida e proposta, não aplicada** (§3[C2], "Proposta temporal"). **CORREÇÃO DE REGISTRO:** a v1.9.5 se declarou "a última sessão da camada de COLETA"; a declaração não sobreviveu à medição da própria v1.9.5, que apontou a ORDENAÇÃO como o parâmetro de coleta ainda por decidir. A frase original fica abaixo, com esta correção ao lado. **v1.9.5 é a ÚLTIMA sessão da camada de COLETA.** Ela corrige a ÂNCORA do posicionamento profundo (§3[B]) e estratifica a SELEÇÃO por profundidade (§3[C2]). O defeito medido: o bloco profundo da v1.9.2 comprava mediana de 3 DIAS sobre o raso, porque a progressão geométrica partia do fim do bloco raso e punha as posições "profundas" em 14-28 de níveis que vão a ~256 — profundo em POSIÇÃO DE PÁGINA, raso em TEMPO. As posições passam a ser frações da profundidade REAL, descoberta por uma sondagem por filme de ~4 requisições; `RESERVA_PROFUNDIDADE` e o orçamento por bucket não mudam — muda ONDE as páginas caem, não QUANTAS. A alternativa (declarar a recência como escolha) foi rejeitada com razão registrada: o histograma NÃO é recortável no tempo, então declarar não alinharia os canais, apenas confessaria o desalinhamento para sempre. Na análise, a seleção adota E1 (três faixas de profundidade), medida antes de adotar com custo ZERO em buckets fechados. Depois desta versão, todo parâmetro restante do projeto é de ANÁLISE. **v1.9.4 corrige o déficit do bucket DOMINANTE com uma extensão de orçamento por DÉFICIT (§3[B]) e transforma numa verificação mecânica a lição sobre o adaptador de LLM (§3[D]).** A extensão é OBSERVACIONAL por decisão explícita — nenhum rendimento é estimado: o bucket gasta a base de 16 páginas exatamente como antes e, só se fechar abaixo da meta com folga, recebe páginas extras uma a uma até o teto de 24, alocadas aos níveis em déficit MEDIDO pelo quarto uso de `redistribuir_deficit`. O desenho preditivo foi rejeitado com racional registrado (as páginas são log-espaçadas desde a v1.9.2 e não amostram o mesmo regime; e a parada por ALVO, removida na v1.9.2, já era uma heurística otimista decidindo orçamento). Registra também que correção e declaração são CAMADAS: a extensão encolhe a classe de buckets sub-40, o piso escalonado absorve o resíduo, e a declaração honesta segue sendo o mecanismo final. Nada de `min_chars`, cascata, fronteira, cota, alocação proporcional, orçamento BASE, ordenação ou reserva de profundidade é tocado. **v1.9.3 não muda a camada de coleta — constrói o harness de LOTE (§3[H]) sobre ela e roda a coleta de um conjunto maior de filmes.** Checkpoint em arquivo (resume sem refazer filme completo), validação de slug por 1 requisição antes de gastar orçamento de páginas, falha isolada por filme (um slug ruim nunca derruba o lote), e `material_esgotado` tratado explicitamente como caso esperado — os 3 filmes do catálogo, sendo populares, nunca tinham exercitado esse caminho em produção. Estimativa de custo medida ANTES do lote (§5.6), com veto explícito se a projeção para 50 filmes passar de ~4h. **v1.9.2 fechou o gate de profundidade que a v1.9.1 deixou em aberto e resolve o déficit residual de `medianas`.** É a última sessão de coleta antes do lote de 30-50 filmes, e o reenquadramento que a motiva é este: a profundidade de paginação é o ÚNICO parâmetro da camada de coleta que o superset NÃO torna reversível — página não baixada não está em disco, e coletar o lote sem resolver isso é aceitar recoleta total se a janela temporal se provar um problema. Quatro entregas: (a) a **parada por ALVO é removida** — era um vestígio de quando o teto era por nível e o custo por bucket não tinha limite; sob o orçamento por bucket da v1.9.1 ela só introduzia não-determinismo (foi a causa exata do 37/40 residual de `cidade-de-deus`), e o orçamento passa a ser sempre gasto integralmente, com única parada antecipada por esgotamento real de material — custo aceito e medido: ~32→48 páginas/filme; (b) **posicionamento estratificado por profundidade** substitui a paginação puramente consecutiva — uma reserva de 25% do orçamento de cada nível (`RESERVA_PROFUNDIDADE`) é posicionada em progressão geométrica a partir do fim do bloco raso, com descoberta de profundidade real e redistribuição do orçamento restante **reaproveitando `redistribuir_deficit`** — MESMO número de requisições que a paginação consecutiva, cobertura temporal muito maior; (c) o **teto de 256 páginas** suspeitado na v1.9.1 é medido num filme obscuro — resultado em §3[B]; (d) `pagina_origem` (rank de adição sob ordenação cronológica, sem a contaminação de `data`, que é a data ASSISTIDA) vira o **instrumento temporal PRIMÁRIO**; `janela_temporal` por `data` (v1.9.1) fica como secundária, rotulada como proxy contaminado. Nada de fronteira, cota, piso escalonado, `min_chars`, ordenação ou síntese é tocado. **v1.9.1 corrigiu dois defeitos que a telemetria MEDIDA da v1.9.0 revelou na camada de coleta**, sem tocar fronteira, cota, piso escalonado ou qualquer etapa de síntese/narrativa: (a) o **orçamento de páginas por BUCKET** (§3[B]) substitui o teto por NÍVEL, corrigindo o defeito estrutural registrado na v1.9.0 (o bucket `medianas`, com metade dos níveis dos outros dois, nunca conseguia o mesmo teto agregado de páginas — 8 contra 16 — e por isso nunca fechava a cota) — **medido: fecha 40/40 em 2 dos 3 filmes (era 35 e 26) e melhora para 37/40 no terceiro (era 23)**, um achado residual e distinto, com causa identificada, registrado em §3[B]; (b) os **motivos de descarte** na seleção passam a ser discriminados (`abaixo_min_chars`/`spoiler`/`truncada_sem_texto`/`duplicata`/`excedente_cota`/`outros`), telemetria pura, sem mudança de comportamento. Duas entregas adicionais: (c) a **janela temporal** (mín./máx./p5/p50/p95 das datas do bruto, por bucket e total) passa a ser gravada em `meta.json`, não exposta ao frontend; (d) o literal `50 · 20 · 30` remanescente em `frontend/js/filme.js` (pendência registrada na v1.9.0) passa a derivar do próprio JSON de resultado. Uma quinta questão — **paginação de passo largo**, candidata a resolver o viés de recência medido na v1.9.0 (79-100% da amostra em ~7 semanas) — foi **só MEDIDA nesta versão, não implementada**: o gate de decisão está em §3[B], "Medição de profundidade (v1.9.1, gate)", com um achado que contraria a expectativa registrada no briefing (o custo de descobrir a profundidade via sonda de rede NÃO é neutro — é uma sonda de ~10 requisições por nível — mas há evidência forte, ainda que de amostra pequena, de um TETO FIXO do site em 256 páginas que, se confirmado mais amplamente, eliminaria essa sonda por completo). **v1.9.0 reestruturou a camada de COLETA e desacoplou COLETA de ANÁLISE** — a maior mudança de arquitetura de dados desde a v1. Até a v1.8.2, a coleta usava cota fixa de 10 reviews por nível de estrela e gravava, no material coletado, as decisões de **fronteira de bucket**, **cota** e **filtro**: mudar qualquer uma delas custava recoletar tudo. A v1.9.0 (a) move as **fronteiras de bucket** para configuração lida de um único lugar, com o mapeamento nível→bucket como função pura (§2.2), e adota a **opção C** (`0,5–2,0` / `2,5–3,0` / `3,5–5,0`, semântica "não recomendam / mornos / recomendam"); (b) faz a coleta raspar um **superset por nível** e **persistir tudo em disco** (`dados/bruto/<slug>/`, §3[B']), com condição de parada em três degraus de precedência (piso de 1 página por nível com material > alvo com folga de 25% > teto de 4 páginas); (c) torna a **ordenação de listagem** um parâmetro de amostragem explícito, gravado no material coletado, com default trocado de `by/activity` (ordenada por ENGAJAMENTO) para `by/added` (**cronológica**, mais recentes primeiro) — ver §2.3; (d) substitui a cota igual por nível por **alocação proporcional ao histograma** dentro de cada bucket, com piso por nível e redistribuição de déficit restrita ao mesmo bucket (§3[C1]); (e) aplica a **cota de análise 40/40/40 downstream**, sobre o bruto persistido, com min_chars/spoiler/cascata como parâmetros (§3[C2]); e (f) troca o piso binário de 3 por um **piso escalonado de 4 estados** (`completa`/`sem_quantificador`/`sem_numero`/`sem_analise`), exposto como campo no JSON (§3[C3]). **Consequência publicada:** sob as fronteiras C os shares dos 3 filmes do catálogo MUDAM — `cure` 3/17/79 → 2/8/90, `the-invite-2026` 3/18/79 → 2/7/91, `cidade-de-deus` 1/8/91 → 1/3/96. **Risco aceito e mitigações** em §2.2. v1.2.0 adiciona a etapa **[D2] narrador** (§D2) e a flag `--tom` como **mecanismo de desenvolvimento** para A/B de saída. v1.2.1 corrige uma classe de infidelidade do narrador (cota de amostragem apresentada como distribuição da recepção) — invariante nova no §D2 + telemetria. v1.2.2 adiciona calibração numérica dos quantificadores da narrativa (mapa fração→palavra, faixa mais fraca em caso de dúvida) — verificação por instrução ao LLM. v1.2.3 move a calibração do prompt para o CÓDIGO: os rótulos de quantificador passam a ser pré-computados e o LLM só os usa, não os escolhe (mesmo princípio da v1.1.1 — código como autoridade de número/rótulo). v1.3.0 adiciona uma **ficha técnica do filme via TMDB** (§3a, aditiva — nunca bloqueia o pipeline) e reestrutura §D2 para uma narrativa em **três movimentos** (filme → experiência consensual → contraste entre grupos), com uma emenda pontual à regra de "zero conteúdo de trama" para permitir a sinopse OFICIAL curta como fonte do primeiro movimento (ver §3[D] "Anti-spoiler"). **v1.3.1** corrige um defeito real observado na primeira execução do MOVIMENTO 2 (a narrativa de `the-invite-2026` importou um juízo de QUALIDADE — "atuações marcantes"/"roteiro inteligente" — como se fosse um consenso DESCRITIVO, contradizendo diretamente os temas do grupo negativas): a regra do MOVIMENTO 2 ganha três critérios explícitos (categoria/presença/não-contradição) e telemetria de `consensos_usados` para revisão humana de cada execução (ver §D2). **v1.4.0** é a maior mudança desde a v1: o pipeline passa a coletar a **distribuição real de notas** (histograma público do Letterboxd, §3b) e, com ela, **inverte** a regra de prevalência do §D2 — o que a v1.2.1 proibiu por falta do dado, a v1.4.0 torna obrigatório e ancorado (ver "Princípio norteador" abaixo). **v1.4.1** corrige três defeitos pontuais observados na entrega da v1.4.0, todos no §D2: (1) telemetria de quantificadores **por par declarado** (`quantificadores_usados`), depois da 3ª reincidência do mesmo modo de falha, que a rede de nível de bucket não pega; (2) **omissão autorizada** do MOVIMENTO 2, contra a pressão de preenchimento que produz juízo de qualidade hedgeado; (3) **invariante de vocabulário do peso** — rótulos de peso dizem "das notas", nunca "das reviews"/"do público"/"dos espectadores". **v1.5.0** ataca um defeito de **fluência**, não de honestidade: as narrativas entregues até a v1.4.1 são factualmente corretas, mas soam mecânicas — forma sintática repetida (rótulo de peso + verbo de reporte + complemento, três vezes seguidas), frases quase todas do mesmo comprimento, excesso de verbos de reporte e nominalizações no lugar de verbos. O diagnóstico (registrado no changelog) é que o acúmulo de invariantes de honestidade das versões anteriores empurrou o modelo à única forma que satisfaz todas simultaneamente. A correção prescreve **ritmo** e **registro** com a mesma precisão de código com que já se prescrevem números, adiciona uma **marcação de perspectiva** pré-computada (para que a redução de verbos de reporte não deixe a fala de um grupo minoritário soar como fato do narrador) e duas telemetrias novas (`marcadores_perspectiva`, `metricas_fluencia`) — **sem afrouxar nenhuma invariante de honestidade** das versões anteriores. **v1.6.0** conclui que a v1.5.0 errou no MÉTODO, não no objetivo: empilhar honestidade e fluência num prompt só não funcionou (as regras de ritmo não transferiram entre filmes, as métricas que as fiscalizavam não acompanhavam qualidade, e a configuração de produção chegou a publicar uma frase agramatical). A correção é **separar responsabilidades**: o narrador (§D2) é podado de volta a UMA responsabilidade — dizer a verdade com a estrutura certa — e um estágio novo, o **editor [E2]** (§E2), assume ritmo e leitura sem ter acesso a nenhuma fonte de fato e sem poder alterar número, rótulo ou atribuição (trechos protegidos + verificação mecânica + descarte da edição em caso de violação). **v1.6.1** corrige o defeito 5.2 que a v1.6.0 deixou em aberto: em vez de normalizar a COMPARAÇÃO entre o trecho declarado e o texto (caixa/acento/demonstrativo), passa a verificar a EXISTÊNCIA de uma expressão de atribuição reconhecida no texto realmente escrito — o que fecha também o caso de reordenação de palavras que a normalização não alcançava, e reduz `marcadores_perspectiva` a telemetria pura (auditoria humana, não fonte de validação). **v1.6.2** corrige um bug de substring solta descoberto ao vivo na regeneração de `cidade-de-deus` (shares 1%/8%/91%): `_ancora_de_grupo` e `_ancoragem_de_peso_ok` buscavam o percentual de um grupo com `f"{pct}%" in texto`/`texto.find(...)`, que casa **dentro** de outro número — `"1%"` combinava com o "1" final de `"(~91%)"`, ancorando o grupo `negativas` (1%) numa posição muito anterior à sua menção real, corrompendo o cálculo do span de movimento e produzindo falso positivo em `perspectiva_nao_marcada` mesmo com o texto correto e bem marcado. A busca agora usa `re.search(rf"(?<!\d){pct}%", texto)` (nega dígito imediatamente anterior), então `"1%"` só casa como número isolado, nunca como sufixo de `"91%"`/`"21%"`/etc. Mesmo defeito corrigido nos dois pontos que faziam a busca (âncora de grupo e checagem de ancoragem de peso), com testes de regressão cobrindo o caso real. Nenhuma invariante de honestidade foi afrouxada — o fix é estritamente sobre a CHECAGEM, não sobre o que é permitido no texto. **v1.7.0** corrige dois defeitos reais observados na regeneração das narrativas: (1) **resolução de ficha do filme errado** — `espectro24 --slug cure` sem `--ano` resolvia no TMDB para "The Cure" (2026, dir. Nancy Leopardi) em vez de Cure (1997, Kiyoshi Kurosawa), porque a desambiguação por popularidade sem ano escolhe o candidato errado quando o título é comum; a resolução de ano ganha uma cadeia de fallback confiável (slug → página do Letterboxd → sem ficha) e uma guarda de sanidade que descarta a ficha inteira se o ano devolvido pelo TMDB divergir do esperado em mais de 1 ano (ver §3[A]); (2) **lista de protegidos do editor §E2 enxugada** — protegia até 16 trechos por filme, incluindo quantificadores soltos ("muitos") e expressões de atribuição, o que descartava o editor com frequência (`cure`) ou o levava a inventar frases só para reencaixar um protegido movido ("Essa é a opinião de uma fração mínima das notas.", `cidade-de-deus`), e ainda deixava sobreviver um defeito gramatical real ("destacando a a maioria o estilo visual") porque a frase continha um rótulo protegido; a proteção literal agora cobre só rótulo de peso COM percentual e tokens numéricos — quantificador e atribuição passam a valer SÓ pela checagem semântica que já existia e era mais forte (`conferencia_quantificador` v1.4.1, `_marcadores_validos` v1.6.1), revalidada dentro do próprio `editar_narrativa` (ver §E2). **v1.7.1** corrige três defeitos de acabamento observados no texto PUBLICADO da v1.7.0, nenhum deles de honestidade: (1) **contrabarra residual** — `_remover_aspas` trocava só o caractere de aspas por "", então uma citação escapada (`\"A Cura\"`) virava `\A Cura\` (publicado em `cure` e `the-invite-2026`); a remoção agora consome a contrabarra que precede a aspas junto, como uma unidade. (2) **capitalização de rótulo protegido movido** — o rótulo de peso guarda a caixa de onde apareceu a primeira vez (início de frase, capitalizado); quando o editor o move para o meio de um período, a checagem 100% literal não deixava ajustar só a inicial, e o defeito ("Para A grande maioria...", `cidade-de-deus`) sobrevivia porque corrigir quebraria o protegido; a checagem de trecho perdido agora aceita a primeira letra em qualquer caixa — e SÓ ela, nenhuma outra letra, palavra ou número do trecho. (3) **família "quem gostou/não gostou" ausente do vocabulário de atribuição** — o `cure` escreveu "quem não gostou considerou o ritmo lento e tedioso" para o grupo de 3%, uma atribuição real, mas fora da lista de expressões reconhecidas (`_EXPRESSOES_DE_PERSPECTIVA`), produzindo falso positivo em `perspectiva_nao_marcada`; a família foi acrescentada ("quem gostou", "quem não gostou", "quem amou", "quem ficou no meio", e as formas com "para" na frente), mantendo de fora o "para quem" ISOLADO (pronome relativo comum, motivo do falso negativo original da v1.6.0). Nenhuma invariante de honestidade foi afrouxada nas três correções — são fixes de CHECAGEM e de limpeza mecânica, não mudança do que é permitido no texto. **v1.7.2** corrige um defeito real observado na regeneração do `cidade-de-deus` sob a v1.7.1: o editor devolveu a prosa embrulhada num invólucro `{ text: "..." }`, ignorando a instrução de responder só texto puro — e TODAS as checagens mecânicas de então (protegidos, conjunto numérico, honestidade) passaram, porque rodam sobre SUBSTRING e o protegido/os números continuavam achados DENTRO do invólucro. A edição foi marcada "aplicada"; só a leitura humana antes de publicar pegou o defeito. A correção acrescenta uma **checagem ESTRUTURAL** (`_formato_invalido`, §E2), aplicada ANTES de todas as outras: rejeita o texto se ele começar com `{`/`[`, contiver cerca de código (```), tiver uma das primeiras linhas com cara de campo JSON (`"text":`, `text:`, `"narrativa":`), ou tiver chaves desbalanceadas — mesma política das demais checagens (1 retentativa com reforço explicando o formato exigido; se persistir, descarta com `motivo_descarte: "formato_invalido"` e publica a bruta). Deliberadamente NÃO rejeita uma chave/colchete equilibrado no MEIO da prosa — só o formato de invólucro, não qualquer ocorrência do caractere. **v1.7.3** corrige um defeito de POLÍTICA, não de checagem: na regeneração da v1.7.1, a edição foi DESCARTADA em 2 dos 3 filmes (`cure` — número alterado; `cidade-de-deus` — regressão de `perspectiva_nao_marcada`), publicando a bruta nos dois, enquanto a MESMA combinação de código e dados tinha sido ACEITA nos 3 filmes sob a v1.7.0 — nada mudou no código nesse sentido entre as duas rodadas; é VARIÂNCIA do modelo entre chamadas, e a política de então (1 chamada + 1 retentativa, 2 no total) dava pouca margem para a variância favorecer numa etapa cujo descarte já é fail-safe (a bruta do narrador sempre prevalece). A correção eleva o teto para até `1 + EDITOR_MAX_TENTATIVAS` chamadas (`EDITOR_MAX_TENTATIVAS = 3` em `config.py`, 4 no total no pior caso) e muda o reforço de SUBSTITUÍDO para ACUMULADO entre tentativas — se a 1ª falha por número e a 2ª por atribuição, a 3ª recebe os dois reforços juntos, para o modelo não consertar um problema criando outro. Nova telemetria em `edicao_flags`: `n_tentativas` (quantas chamadas foram feitas) e `motivos_por_tentativa` (o motivo de cada falha, na ordem) — visibilidade de qual checagem mais reprova o editor, não critério de aprovação. Nenhuma invariante de honestidade foi afrouxada: o fail-safe de descarte após esgotar as tentativas continua idêntico, só o número de chances antes dele mudou. **v1.7.4** corrige dois defeitos: um buraco de arquitetura e um resíduo cosmético recorrente. (1) **checagem de EDIÇÃO NULA** — nenhuma checagem até a v1.7.3 verificava que a edição FEZ algo, só que ela não QUEBROU nada; um editor que devolva a entrada praticamente intacta passa em protegidos (nunca saíram), números (nada mudou) e honestidade (é o mesmo texto), e era marcado "aplicada" sem nenhum sinal de que não houve edição de verdade. A correção calcula a similaridade (`difflib.SequenceMatcher.ratio`, textos normalizados só por espaço em branco) entre `narrativa_bruta` e o texto editado; se as demais checagens TERIAM passado mas a similaridade é `>= EDITOR_LIMIAR_EDICAO_NULA` (0.97, deliberadamente conservador — só pega devolução literal ou trivial, não uma edição legítima que preserve vocabulário protegido), trata como falha de tentativa com motivo `"edicao_nula"`, no mesmo ciclo de retentativa/descarte já existente. `edicao_flags.similaridade` é persistido SEMPRE (aceita ou não), telemetria para calibrar o limiar. (2) **capitalização residual, correção determinística** — a v1.7.1 AUTORIZOU o editor a ajustar a caixa de um rótulo de peso movido para o meio da frase, mas não o OBRIGA, e ele frequentemente não ajusta ("Já Uma fração mínima...", "Para A grande maioria..."). Em vez de depender do LLM, um pós-processamento em CÓDIGO (`_corrigir_capitalizacao_residual`) roda sobre toda edição ACEITA: baixa a inicial de qualquer rótulo de peso canônico que apareça capitalizado fora de início de período (mesmo princípio de toda pré-computação do pipeline — o determinístico é decidido pelo código, não pelo LLM). `edicao_flags.capitalizacao_ajustada` registra se algo mudou. **v1.8.1** REATIVA o editor [E2] por padrão (`EDITOR_ATIVO=True`) — a v1.8.0 tinha desligado por precaução após um defeito de conteúdo inventado, mas a MESMA versão já corrigira a causa raiz (checagem de conteúdo adicionado + ordem dos movimentos); a validação pós-correção (`VALIDACAO_EDITOR_V18.md`, 3 filmes reais) mostrou a checagem disparando de verdade em produção e o modelo se autocorrigindo na retentativa, com os limiares bem separados do ruído normal de uma edição legítima — evidência suficiente para reativar. **v1.8.0** troca o provider DEFAULT de produção para **DeepSeek** (`deepseek-v4-flash`, ver Changelog) e, na mesma versão, DESLIGA o editor [E2] por padrão como medida de contenção — a validação que justificou a troca de provider também descobriu um defeito real e mais sério: o editor pode ACRESCENTAR conteúdo (opinião, frase de fechamento, reordenar movimentos) sem que nenhuma checagem mecânica até a v1.7.4 detecte, porque todas checavam PERDA, nenhuma ADIÇÃO. Duas checagens novas (conteúdo adicionado por similaridade de frase, ordem dos movimentos) mitigam o defeito e o editor volta a ser ligável via `--com-editor`, mas o default de produção segue conservador até mais evidência.

**v1.9.21 — o VEREDITO passa a ser escrito por LLM sobre briefing determinístico (§3[V], estágio NOVO), e a dívida de registro das v1.9.17–v1.9.20 é paga.** O defeito medido antes de qualquer código: **19 dos 35 filmes recebiam veredito byte-idêntico**, 20 caíam no ramo que o produz, e o catálogo inteiro tinha **14 textos distintos para 35 filmes**. A causa não é o template ser burro — é o briefing ser pobre: a frase relata a AUSÊNCIA de contraste e nunca a PRESENÇA de assunto, enquanto o campo `tema` de cada célula de `eixos` (a única fonte de variedade real, já rotulada por [D3] e já filtrada de spoiler) era descartado. O estágio novo roda na PUBLICAÇÃO, monta em código puro um briefing cuja **serialização não contém nenhum algarismo** — o modelo recebe rótulos prontos e nomes de tema prontos, nunca números —, gera best-of-3, valida por dez checagens em código, e cai no TEMPLATE determinístico da v1.9.19/v1.9.20 quando nada sai limpo. **O risco central, e o motivo de a proibição de fabricar contraste ser o coração da entrega:** 17 dos 35 filmes são `contraste: valorativo` e são EXATAMENTE os 17 do ramo — um modelo solto sobre um briefing pobre produziria 20 maneiras diferentes de dizer a mesma coisa vazia, o que é PIOR que a repetição atual, porque disfarça um achado real de homogeneidade como se cada filme fosse diferente. Por isso o briefing carrega `assunto_compartilhado` (o eixo que maximiza `min(freq_negativas, freq_positivas)`, piso de 25% nos dois lados; medido: todos os 35 têm, e nos 17 `valorativo` o min fica entre 40% e 84%). **Registro honesto:** o veredito deixa de ser 100% determinístico — e isso NÃO viola "código é autoridade sobre números", porque o modelo não vê algarismo nenhum, não escolhe eixo/tema/grupo/rótulo/estado de contraste, e o único número que sobrevive no texto renderizado (o peso do meio dominante) é prefixado pelo CÓDIGO, fora da saída dele. Na mesma versão: correção da inflação retórica no fallback (`obsession-2026` afirmava "um assunto que todos os grupos citam" a partir de 2 de 5 reviews, `eighth-grade` a partir de 13 de 34 — mesma classe das v1.2.2/v1.2.3, reintroduzida num lugar novo), unificação do mapa de quantificador que existia em duplicata (`quantificador.py`), e o changelog retroativo das quatro versões de frontend que rodaram carimbadas no código e ausentes da spec.

**v1.9.22 — acabamento do veredito: DEFLAÇÃO é falsidade, e a repetição migrou para a ESTRUTURA.** Três defeitos achados na LEITURA dos 17 vereditos `valorativo` publicados, que nenhuma métrica da v1.9.21 capturou. **(1) Deflação de quantificador, e ela é violação do §0, não de estilo.** Em `pearl-2022` os dois lados têm a MESMA frequência (58%, rótulo `cerca de metade` nos dois): o positivo recebeu o rótulo, o negativo virou "impressões negativas pontuais". Mesmo número, dois tratamentos, e o que os separa é o SENTIMENTO do grupo. Em `the-godfather`, "relatos pontuais apontam que a maioria dos que desaprovam…" — o rótulo estava CERTO e o hedge o desmente na mesma oração. A invariante 4 do prompt dizia "mais fraco é permitido" e essa metade estava errada: **deflação mente sobre o dado exatamente como inflação, e o §0 não distingue direção**. Medido nos 35 ANTES de corrigir: **zero rótulos divergentes em 72 pares** — o defeito nunca foi o rótulo, foi o hedge que o substitui ou o envolve, e ele aparece em 2 filmes, **os dois com `negativas` em modo reduzido**. A causa raiz é a invariante de CAUTELA disparando como deflação, e ela recorreria: no catálogo, `negativas` está em modo reduzido em 5 filmes e `positivas` em 2, e **não existe filme com positivas reduzida sem negativas também reduzida** — o grupo que falta material é quase sempre o negativo, então uma regra que afrouxa a quantidade em amostra pequena afrouxa sempre do mesmo lado. Correção: o rótulo fornecido passa a ser o ÚNICO admissível (trava preventiva, reprova zero hoje); a cautela passa a qualificar a **base** e nunca a **magnitude**; e a validação `deflacao_por_hedge` reprova adjetivo de magnitude reduzida sobre substantivo de review, com exceção ancorada na amostra — a exceção existe para `wonka` e tem teste nomeado. **(2) A repetição saiu do léxico e foi para a ESTRUTURA.** Jaccard 0,06 e cego a isto: 14 dos 17 `valorativo` abriam com fórmula de divergência. Métrica nova e permanente — o **padrão sintático de abertura** (núcleo do primeiro sintagma nominal, com o quantificador colapsado em `QUANT`, porque qual rótulo abre a frase é decisão do código). Linha de base medida: **6 padrões para 35 filmes, três maiores cobrindo 91%**. Atacado pela SELEÇÃO e não pelo prompt: a frequência da abertura entra como desempate ANTES da brevidade, sobre os candidatos que o best-of-3 já gera — custo zero de chamada, com política de estabilidade que mantém o resultado independente da ordem dos filmes. **(3) `the-godfather` lendo como lista** foi desfeito pela correção (1), como previsto — sem estrutura nova para um caso único.

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

> **EXCEÇÃO DELIBERADA na INTERFACE (frontend, sessão "dados primeiro",
> código de UI ~v1.9.19) — o meio sai do meio-a-meio, com uma volta
> automática.** Feedback de uso apontou que o grupo `medianas` — minoritário
> em **33 dos 35** filmes do catálogo — "polui sem informar" quando recebe o
> MESMO destaque visual que negativas/positivas: o leitor decide entre
> recomendar e não recomendar, e o meio raramente é onde a decisão mora.
> `filme.html` passa a mostrar **dois** blocos em destaque (negativas,
> positivas, mesmo formato entre os dois — a neutralidade de TRATAMENTO
> continua valendo AÍ) e recolhe `medianas` numa linha discreta e
> expansível abaixo.
>
> Isto quebra, de propósito, a promessa deste §0 ("três grupos, formato
> idêntico"). **A exceção automática que impede a decisão virar
> distorção:** quando `medianas` é o grupo DOMINANTE (maior `share_real`
> dos três), ele SOBE de volta pro destaque, junto dos outros dois —
> `napoleon-2023` (45% no meio) e `friday-the-13th-2009` (41% no meio) caem
> aqui. Descrever esses dois filmes só pelos dois grupos que, somados, são
> METADE da recepção seria exatamente a infidelidade por omissão que este
> §0 foi escrito para proibir — só que pelo lado oposto do que motivou a
> v1.4.0 (lá, o filme aclamado parecia dividido; aqui, sem a exceção, o
> filme dividido pareceria bipolar quando na verdade é tripolar).
>
> **O que NÃO muda:** o DADO — coleta, classificação, lift, o bloco `eixos`
> do JSON — continua com os três buckets, sem distinção nenhuma. A exceção
> é só de onde o CSS/JS decide desenhar `medianas` em destaque; o grupo
> recolhido mantém os mesmos temas, barras e paráfrases de sempre (a
> invariante 2 acima), só atrás de um `<details>` fechado por padrão.

> **SEGUNDA EXCEÇÃO DELIBERADA na INTERFACE (frontend, v1.9.26) — o
> VOCABULÁRIO DE RÓTULO dos três grupos, e SÓ ele.** Decisão do dono do
> projeto, tomada com objetivo de **conexão geracional e uso em campanha
> de marketing**: onde a tela nomeia um grupo como RÓTULO, ela passa a
> escrever `negativas` → **HATERS**, `medianas` → **MIXED**, `positivas`
> → **FANS**.
>
> **O trade-off, escrito por extenso, porque é ele que a exceção custa.**
> Este §0 exige neutralidade de tratamento entre o grupo negativo e o
> positivo, e **"Fans/Haters" não é um par simétrico**: "hater" imputa
> MÁ-FÉ a quem não gostou — descreve alguém movido por hostilidade, não
> alguém que assistiu e achou ruim —, enquanto "fã" imputa entusiasmo,
> que é uma disposição favorável e não uma acusação. O produto passa,
> portanto, a nomear um dos dois lados com uma palavra que carrega juízo
> sobre a MOTIVAÇÃO de quem escreveu, e o outro não. Isso contradiz a
> invariante 2 ("a perspectiva minoritária continua analisada com o mesmo
> rigor... sem desdém, sem ironia, sem sugerir que quem pensa assim está
> errado") no plano do vocabulário. Não há como registrar isto de outro
> jeito: é uma perda de neutralidade, aceita conscientemente em troca de
> alcance, e não uma equivalência que o documento possa fingir.
>
> **O ESCOPO é o que delimita a perda, e é a metade obrigatória da
> decisão.** A exceção é de VOCABULÁRIO DE RÓTULO, restrita a onde o nome
> do grupo aparece ISOLADO, identificando a coluna:
>
> - o cabeçalho de cada bloco de bullets;
> - a legenda e a alternativa textual (`aria-label`) da barra de
>   proporção (§3[E], v1.9.26);
> - qualquer `aria-label` cuja função é dizer de qual grupo é o elemento;
> - qualquer lugar da home onde o grupo seja nomeado como rótulo (hoje:
>   nenhum — a home não nomeia grupo nenhum).
>
> **A PROSA do produto permanece NEUTRA, e pelo mesmo motivo.** Quando a
> palavra aparece como adjetivo dentro de uma frase corrida, ela carrega
> o contexto da sentença e não funciona como nome próprio do grupo — e é
> na prosa que mora a afirmação sobre pessoas. Continuam em
> `positivas`/`medianas`/`negativas`, ou em redação neutra:
>
> - o texto do VEREDITO (§3[V]), inclusive o prefixo de bucket dominante
>   montado em CÓDIGO ("O meio-termo é o maior grupo da recepção (~45%
>   das notas)") — este é prosa determinística e é **proibido trocar**;
> - o texto da NARRATIVA e a `observacao_geral` de cada grupo;
> - os avisos curtos dentro do bloco do grupo ("modo reduzido", "sem
>   análise temática") — são frase, não rótulo, e o cabeçalho logo acima
>   já identificou o grupo;
> - o disclaimer da cota.
>
> **A NEUTRALIDADE ESTRUTURAL DESTE §0 NÃO É AFETADA e continua
> integralmente em vigor.** A exceção não toca em nada do que este
> parágrafo governa de verdade: a **cota 40/40/40** continua literal, a
> **mesma margem de lift** (§2.5) vale para os dois lados, e negativas e
> positivas continuam com **o mesmo leiaute, o mesmo espaço estrutural e
> a mesma quantidade de bullets** — 6 e 6 nos 35 filmes do catálogo,
> conferido depois da mudança. Trocar a etiqueta de uma coluna não move
> um único número, um único bullet nem um único pixel de estrutura.
>
> **O DADO não muda em nada.** `negativas`/`medianas`/`positivas`
> continuam sendo as chaves do JSON, do briefing, dos prompts, dos
> validadores, desta spec e dos testes. Nenhum arquivo de `resultado/`
> foi tocado; nenhum filme foi regerado. A troca vive num mapa do
> frontend (`GRUPO_LABEL`, `frontend/js/filme.js`) e em nenhum outro
> lugar.
>
> **REVERSÃO BARATA, DE PROPÓSITO.** O rename é de UM PONTO SÓ porque a
> hipótese ainda não foi testada em público: se o ganho de conexão não se
> confirmar, voltar aos rótulos antigos é **uma edição de uma linha**, e
> não uma varredura por um produto inteiro. O custo de errar foi
> desenhado para ser baixo antes de a aposta ser feita.
>
> **ANOTADO, NÃO IMPLEMENTADO:** "MID" é mais idiomático que "MIXED" em
> português brasileiro, e era o termo da versão originalmente arquivada.
>
> **O CASO DE FRONTEIRA QUE FECHOU O CRITÉRIO: a legenda do mosaico da
> home vira GLOSSÁRIO (v1.9.26).** A varredura da Entrega 3 encontrou um
> caso que não caía limpo dos dois lados do critério, e ele foi escalado em
> vez de decidido por conta própria. A legenda da faixa da home dizia *"a
> faixa na base de cada quadro é a distribuição real do filme: quem não
> gostou, quem ficou no meio, quem gostou"*, com as três expressões nas
> cores dos grupos. Ela tem **função de rótulo** (é a legenda que explica a
> faixa, paralela exata da legenda da barra de proporção, que TROCA) escrita
> em **forma de prosa** (enumeração dentro de uma frase corrida, e sem
> nenhuma das três palavras-chave, que MANTERIA).
>
> **Decisão do dono do projeto: nem manter, nem trocar — virar glossário.**
> Passa a ser **"HATERS (quem não gostou), MIXED (quem ficou no meio), FANS
> (quem gostou)"**, com as cores de grupo preservadas.
>
> **O raciocínio, porque ele generaliza para o próximo caso de fronteira.**
> As duas saídas puras eram ruins por motivos opostos. Trocar seco
> produziria "…a distribuição real do filme: HATERS, MIXED, FANS" e
> **destruiria a única função que a legenda tem** — ela existe para
> explicar a faixa a quem acabou de chegar, e três palavras em inglês sem
> glosa explicam menos que as expressões que estavam lá. Manter como
> estava criaria **descompasso**: o leitor sairia da home com um
> vocabulário e encontraria outro em toda página de filme, sem nada
> ligando os dois. O glossário resolve as duas coisas de uma vez, porque a
> legenda é exatamente **onde o vocabulário novo se ensina**: o rótulo vem
> primeiro, a glosa entre parênteses logo atrás, e o leitor sai dali
> sabendo ler as páginas de filme. É a única posição do produto em que as
> duas formas convivem de propósito.

> **A ORDEM DE LEITURA DOS BLOCOS PASSA A SEGUIR O PESO (v1.9.30) — e isto
> NÃO é uma terceira exceção a este §0.** É o contrário: é o §0 sendo
> aplicado a uma dimensão da tela em que ele estava sendo ignorado.
>
> **O defeito.** Os dois blocos em destaque saíam em ordem FIXA — negativas
> antes de positivas — qualquer que fosse o peso de cada grupo.
> `the-godfather` é 2 / 5 / 93: a leitura abria por **HATERS, 2% das
> notas**, e o grupo que responde por 93% da recepção só chegava depois. É a
> mesma **infidelidade por omissão** que motivou a v1.4.0, num canal que a
> v1.4.0 não tinha olhado: cada bloco era verdadeiro, e a ordem em que eles
> chegavam comunicava outra coisa.
>
> **A regra: os blocos em destaque são ordenados por `share_real`, do maior
> para o menor.** Medido no catálogo: em `cats-2019` (86 / 7 / 7) o primeiro
> bloco é HATERS; em `the-godfather` (2 / 5 / 93) é FANS.
>
> **POR QUE ELA É COMPATÍVEL COM ESTE §0, e a frase é a inteira: a regra é
> função do DADO, não do sentimento.** Ela nunca privilegia o negativo nem o
> positivo — privilegia **quem é maior**, e quem é maior sai do
> `share_real`, que é o histograma do Letterboxd, não um juízo do produto.
> Não existe caminho pelo qual esta regra favoreça um lado: o lado que ela
> favorece é escolhido pelas notas de quem assistiu.
>
> **E A ORDEM ANTIGA NÃO ERA NEUTRA — ERA CONSTANTE, que é outra coisa.**
> Isto precisa ficar escrito porque a intuição diz o oposto (uma ordem que
> nunca muda *parece* a opção neutra). Liderar sempre pelo negativo é uma
> **escolha editorial fixa**, tomada uma vez e repetida 35 vezes sem que o
> dado fosse consultado nenhuma delas. Neutralidade de tratamento é dar
> **formato idêntico** aos grupos; nunca foi dar posição idêntica, que é
> impossível — alguém tem de vir primeiro. Quando duas posições são
> desiguais por construção, a única regra defensável é a que decide entre
> elas **pelo dado**.
>
> **A NEUTRALIDADE DE TRATAMENTO CONTINUA INTEGRALMENTE EM VIGOR, e a
> mudança foi desenhada para não tocar em nada dela:** mesmo leiaute, mesmo
> peso tipográfico, **mesma quantidade de bullets** (6 e 6 nos 35, conferido
> depois da mudança), mesmas cores, mesmo espaço estrutural. **Só a POSIÇÃO
> muda.** Nenhum número, nenhum bullet, nenhum pixel de estrutura se move.
>
> **A POLÍTICA DO MEIO NÃO MUDA.** `medianas` continua rebaixado por padrão,
> com a mesma exceção automática de quando é o grupo dominante (o parágrafo
> acima). A ordenação só ordena o que já está em destaque: quando o meio
> está lá, ele entra na mesma conta — `napoleon-2023` (22 / 45 / 33) abre
> por MIXED, `friday-the-13th-2009` (33 / 41 / 26) também.
>
> **EMPATE: a ordem canônica do produto** (negativas → medianas →
> positivas), como critério de desempate explícito no código, e não como
> efeito colateral da estabilidade do `sort` do runtime. O mesmo filme
> renderiza sempre na mesma ordem. Nenhum dos 35 empata hoje entre grupos em
> destaque; a regra existe para o filme que ainda não foi publicado.
>
> **A BARRA DE PROPORÇÃO NÃO É REORDENADA**, e a razão é de significado, não
> de esforço: a ordem dela é **semântica**, um eixo ordinal de 0,5★ a 5★.
> Ver §3[E].
>
> **O DADO não muda em nada.** Nenhum arquivo de `resultado/` foi tocado por
> esta regra; nenhum filme foi regerado. Ela vive numa função de
> `frontend/js/filme.js` (`ordenarPorPeso`) e em nenhum outro lugar.

> **A MARGEM DE CONTRASTE PASSA A DEPENDER DE `n` (v1.9.34) — e isto NÃO é uma
> terceira exceção a este §0. É o §0 aplicado a uma dimensão em que ele estava
> sendo ignorado**, exatamente como a ordenação por peso da v1.9.30.
>
> **O ESCOPO, primeiro, porque ele resolve metade da pergunta.** Este §0 governa
> a neutralidade entre os TRÊS GRUPOS **dentro** de um filme: cota 40/40/40,
> mesma estrutura, mesmo espaço, mesma margem para os dois lados. Ele nunca
> falou sobre neutralidade **entre filmes**. A lei por `n` (§2.5) **não toca em
> nada que este parágrafo governa**: dentro de cada filme os três buckets são
> julgados pelo MESMO limiar, com a mesma métrica e o mesmo denominador. Não
> existe caminho pelo qual `negativas` receba um limiar e `positivas` outro — e
> há teste travando isso (`tests/test_eixos.py`).
>
> **NEUTRALIDADE DE TRATAMENTO É MESMA EXIGÊNCIA PROBATÓRIA, NÃO MESMO NÚMERO.**
> É a frase que esta versão acrescenta ao princípio, e ela precisa estar escrita
> porque a intuição diz o oposto (um número igual para todos *parece* a opção
> neutra). **MEDIDO** (`ESTUDO_MARGEM_20PP.md` §4.1): o mesmo limiar de 20pp é o
> percentil **3** do ruído com n=10, **34** com n=20, **65** com n=30, **83**
> com n=40 e **99,8** com n=100. Um número constante aplicado a amostras de
> tamanhos diferentes exige provas **sistematicamente diferentes**, e a régua é
> mais FROUXA exatamente onde o dado é mais fraco — o filme com amostra pequena
> passa mais fácil, e o que ele publica tem mais chance de ser ruído. Chamar
> isso de neutralidade é chamar de neutro o resultado de não olhar.
>
> **O PRECEDENTE JÁ ESTAVA AQUI DENTRO, e o argumento é o mesmo trocando duas
> palavras.** A v1.9.30 escreveu, sobre a ordem dos blocos: *"a ordem antiga não
> era neutra — era CONSTANTE, que é outra coisa… quando duas posições são
> desiguais por construção, a única regra defensável é a que decide entre elas
> pelo DADO."* Troque "ordem" por "limiar" e "peso" por "tamanho de amostra" e o
> parágrafo se lê sem uma emenda.
>
> **E O TESTE QUE A v1.9.30 USOU PARA SE AUTORIZAR PASSA AQUI TAMBÉM, POR
> CONSTRUÇÃO:** a regra é função do DADO, não do sentimento. `n` é quantas
> reviews com texto ≥150 caracteres o Letterboxd tem naquele bucket — contagem,
> não juízo. **Não existe mecanismo pelo qual um limiar em função de `n`
> favoreça o grupo negativo ou o positivo**, porque `n` é o mesmo para os três
> dentro de um filme (é o MENOR dos três, §2.5) e entra uma vez só.
>
> **O QUE SE PERDE, escrito por extenso porque é a metade honesta.**
> **Comparabilidade entre páginas.** O leitor que vê `tematico` em `cats-2019` e
> `valorativo` em `the-godfather` não tem como saber que o segundo foi julgado
> sob um limiar mais alto (26,4pp contra 22,8pp). A afirmação implícita "estes
> dois filmes são diferentes" fica um grau mais fraca do que parece. **MEDIDO:
> isso afeta 6 dos 35 filmes hoje** (os que têm algum bucket abaixo de 40), e em
> 4 deles a diferença de limiar é menor que um passo do quantum. O caso extremo
> é um só (`obsession-2026`, n = 5/6/8) e é exatamente aquele em que o produto
> **deveria** estar dizendo outra coisa — e passa a dizer: ele sai sem estado
> publicado (§2.5, piso de `n`).
>
> **O DADO por filme não muda de forma.** A cota 40/40/40 continua literal, os
> três buckets continuam com o mesmo leiaute, o mesmo espaço estrutural e a
> mesma quantidade de bullets. O que muda é **quais filmes** caem em cada ramo
> do veredito — não como um filme trata seus três grupos.

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
| **Teto de EXTENSÃO por bucket** | **24 páginas** (= base 16 + até 8 extras, +50%) — só é alcançado por bucket que fecha o orçamento base ABAIXO da meta com folga; bucket que fecha a meta na base para em 16, como sempre | coleta | **v1.9.4 (§3[B])** |
| **Teto de segurança por nível** | **10 páginas** — nenhum nível sozinho consome o orçamento inteiro do bucket | coleta | **v1.9.1 (§3[B])** |
| **Reserva de profundidade** | **25%** do orçamento de cada nível — a FRAÇÃO não muda na v1.9.5; muda onde as páginas caem | coleta | **v1.9.2 (§3[B])** |
| **Frações de profundidade** | **25% · 50% · 75% · 95%** da profundidade REAL do nível — a âncora das posições profundas desde a v1.9.5 (era progressão geométrica a partir do fim do bloco raso) | coleta | **v1.9.5 (§3[B])** |
| **Escada da sondagem de profundidade** | **4 · 16 · 64 · 256** páginas, + até 3 passos de refinamento binário | coleta | **v1.9.5 (§3[B])** |
| **Teto de plataforma** | **256 páginas** — medido na v1.9.2 (§3[B]) e usado como teto da profundidade estimada | coleta | **v1.9.5** |
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

**APLICADO EM PRODUÇÃO na v1.9.14 (2026-08-16).** A tabela abaixo deixou de
ser projeção: os três `resultado/*.json` foram sobrescritos pelos artefatos
da v1.9.13 e o frontend passou a exibir a coluna "Novas C". Quem tinha lido
"17% ficaram no meio" em `cure` lê agora "8%" — **o dado não mudou, a régua
mudou**, e é este parágrafo que registra o momento em que a troca ficou
visível ao leitor. Ver o changelog da v1.9.14 para as outras três mudanças
visíveis publicadas no mesmo evento.

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

#### A passada SELETIVA sob `by/added-earliest` (v1.9.6)

O candidato registrado acima ("amostragem estratificada por período") deixa de
ser candidato. A v1.9.5 mediu por que ele é o **único** lever disponível: sob
`by/added`, a mediana do catálogo precisa de **1783 páginas** para cobrir um
ano, contra um teto de plataforma de **256** (§3[B], "Achado que refuta"). As
256 páginas expostas são as ~3000 adições mais recentes — nenhum orçamento,
nenhuma âncora e nenhum desenho de seleção alcança o passado por posição. A
ordenação alcança: `by/added-earliest` devolve a listagem estritamente
crescente desde 2012 (tabela do menu, acima).

**Ela é SELETIVA, e a seletividade é o ponto.** A mesma medição separou duas
populações pelo `dias_por_100_paginas` (§3[B']): `friday-the-13th-2009` cobre
163,6 dias a cada 100 páginas e sequer sai da página ~14; `avengers-endgame`
cobre 0,8. Para o primeiro, a profundidade sob `by/added` **já** entrega anos
de recepção, e uma passada por ordenação gastaria requisição comprando
cobertura que já existe. Para o segundo, 256 páginas são questão de dias.

```
recebe passada  ⇔  dias_por_100_paginas < LIMIAR_PASSADA_ANTIGA (= 20)
```

**Por que 20 e não outro número:** abaixo de 20 dias/100 páginas, o teto de 256
páginas da plataforma não cobre um ano (256 × 20/100 = 51 dias… e o filme
mediano da classe está muito abaixo disso). É o corte que responde à pergunta
"as 256 páginas que existem cobrem pelo menos um ano?" — não um quantil da
distribuição observada, que mudaria a cada filme novo no catálogo. **Limiar
ARBITRÁRIO na mesma acepção dos limiares do piso escalonado (§3[C3]):** a
ordem de grandeza é defensável, o corte exato não; ele é config, não constante
enterrada.

**Orçamento da passada:** a mesma estrutura por bucket de §3[B], com uma fatia
menor — `ORCAMENTO_PAGINAS_PASSADA = 6` por bucket (~18 páginas por filme,
contra 48 da coleta base). **Sem extensão por déficit e sem sondagem de
profundidade**, e as duas exclusões têm razão: a extensão (§3[B], v1.9.4) mede
déficit contra a cota de análise, que a passada não está tentando fechar; e a
sondagem existe para ancorar o bloco PROFUNDO, que sob ordenação CRESCENTE
aponta para o material mais RECENTE — exatamente o que a coleta base já tem.
Uma passada que gastasse orçamento fundo em `by/added-earliest` compraria
duplicata.

**A passada SOMA, não substitui** — a persistência é incremental e deduplica
por `id` (§3[B']), e a chave de cache inclui a ordenação (`urls.py`, v1.9.0),
então não há risco de servir a amostra errada. As duas assimetrias que a
passada obriga a resolver estão em §3[B'] ("Duas ordenações no mesmo bruto").

**Ressalva que não some com a passada:** o material de `by/added-earliest` é
um recorte de coorte severo (público de festival / primeiros adeptos) — foi
exatamente por isso que a v1.9.0 o rejeitou como ordenação ÚNICA, e essa
rejeição continua de pé. O que muda é que ele deixa de ser *a* amostra para
ser *uma ponta* dela; quanto de cada ponta entra na análise é decisão de
SELEÇÃO (§3[C2], "Proposta temporal"), medida nesta versão e **não aplicada**.

---

## 2.4 Retentativa de rede — TRANSPORTE sim, BLOQUEIO nunca (v1.9.6)

Até a v1.9.5, `Fetcher.get` fazia **uma** tentativa por requisição: qualquer
`ConnectionResetError`/`ReadTimeout` propagava e abortava o filme inteiro. Com
~48 requisições de rede por filme, a probabilidade de um reset transitório em
algum ponto é alta — medido na recoleta da v1.9.5: **10 falhas em 28 filmes
processados (36%)**, todas transitórias, nenhuma com 403 e nenhuma com
`AntiBotError`. Não era bloqueio: era rede.

**O que RETENTA** — erro de transporte, isto é, a requisição não produziu
resposta HTTP nenhuma: reset de conexão, timeout de leitura/conexão, falha de
DNS/socket. Até **3 tentativas** por requisição, com backoff exponencial
`2s · 4s · 8s` e **jitter de ±25%** (o jitter existe para que um lote inteiro
que tropece no mesmo instante não volte em uníssono). O **delay de educação
(§2.1, ≥2s) continua valendo entre todas as tentativas** — a retentativa
**soma** a ele, nunca o substitui. Custo do pior caso por requisição:
`3×delay + backoffs ≈ 6 + 14 = 20s`.

**O que NÃO retenta, e por quê** — esta é a metade da regra que importa:

| Condição | Comportamento | Razão |
|---|---|---|
| **HTTP 403** / challenge Cloudflare (`AntiBotError`) | **PARA imediatamente**, sem retentar, sem escalar | Retentar bloqueio é evasão, e a spec proíbe (§restrições). O servidor respondeu, e a resposta foi "não" |
| **HTTP 503**, 1ª ocorrência no lote | **1 retentativa**, com backoff LONGO (`ESPERA_503 = 30s`) | Sobrecarga é transitória por definição, e é o servidor pedindo espaço — esperar mais é cooperar, não insistir |
| **HTTP 503**, 2ª ocorrência no lote | **PARA o lote** (`SobrecargaError`) e reporta | A v1.9.5 foi interrompida por um 503 e essa decisão foi correta; automatizar a insistência a desfaria. Duas vezes não é ruído |
| **HTTP 404** e demais status ≠ 200 | `FetchError` na hora, sem retentar | Resposta legítima do servidor, não erro de transporte. Slug inexistente é resultado, não falha a repetir |

**O contador de 503 é do LOTE, não da requisição nem do filme** — o harness
(§3[H]) cria um `Fetcher` por filme, então o estado vive num objeto
compartilhado (`PressaoDoSite`) passado a todos eles. Sem isso, "segundo 503 do
lote" seria inexprimível: cada filme recomeçaria a contagem do zero e a spec
estaria dizendo "retenta 503 para sempre, uma vez por filme".

`SobrecargaError` **não** herda de `FetchError`, deliberadamente: as etapas
ADITIVAS do pipeline (histograma §3[G], ficha §3[F]) engolem `FetchError` para
não derrubar uma coleta cara por causa de um dado opcional, e engolir uma
parada de lote seria o oposto do que esta regra existe para garantir.

**Telemetria obrigatória por filme** (`Fetcher.telemetria_retentativa()`):
tentativas gastas em retentativa, contagem por tipo de erro, e nº de 503.
**Taxa alta de retentativa é sinal de pressão no site e precisa ser VISÍVEL**
— o modo de falha desta versão seria absorver em silêncio a degradação que a
v1.9.5 conseguiu ver justamente porque o `Fetcher` quebrava.

---

## 2.5 Eixos, lift e margem de contraste — a régua do Ponto 2 (v1.9.14)

Fecha o Ponto 2 do projeto: os bullets de cada grupo deixam de ser três
listas livres, independentes entre si, e passam a ser organizados por uma
**taxonomia FECHADA de 10 eixos**. A promessa estrutural é o alinhamento POR
LINHA — com eixo fixo, os três grupos ficam comparáveis célula a célula, em
vez de exigir do leitor a reconciliação mental de três listas soltas.

`ritmo` · `atuacao` · `direcao_imagem` · `roteiro_estrutura` · `som_trilha` ·
`tom_atmosfera` · `impacto_emocional` · `comparacoes` · `expectativa` ·
`critica_social`, mais `livre` para o que não couber.

`taxonomia_id` corrente: **`ebab2667de74`** (hash do prompt de classificação
+ da lista de eixos). A classificação dos 35 filmes está em
`resultado/votacao-3/consenso.jsonl`, por votação de 3 passadas
independentes (eixo entra no consenso se aparece em ≥2 de 3). A fase inteira
de medição que produziu essa régua está consolidada em
`CLASSIFICACAO_CONSOLIDADO.md`; esta seção registra só o que virou
PARÂMETRO.

### `taxonomia_id` no veredito não é burocracia

Todo veredito de contraste carrega o `taxonomia_id` sob o qual foi
calculado. **Um filme classificado como sem contraste sob uma taxonomia pode
deixar de sê-lo sob a seguinte** — aconteceu com `barbie`: sob a taxonomia
anterior o contraste vinha de `impacto_emocional` (22,5pp); sob
`ebab2667de74` esse eixo saturou (0,0pp, 65/70/70% nos três grupos) e o
contraste MIGROU para `critica_social` (20,0pp, gradiente limpo 82,5%→47,5%
do bucket negativo ao positivo).

O estado descreve **o que a régua atual enxerga**, não uma propriedade do
filme. Sem o `taxonomia_id` ao lado, `contraste: valorativo` seria lido como
afirmação sobre a obra, e a próxima régua o desmentiria em silêncio.

### Lift — a definição, e por que ABSOLUTO

```
lift(eixo, bucket) = freq(eixo, bucket) − max( freq(eixo, outros dois buckets) )
```

Frequência é sempre `n_reviews_do_bucket_com_o_eixo / n_reviews_classificadas_do_bucket`
— fração com denominador visível, como toda frequência deste projeto.

**Lift NORMALIZADO foi testado e REFUTADO** (`scripts/metricas_lift.py`).
`(freq_top − freq_2o)/(1 − freq_2o)` e log-odds amplificam o quantum de
discretização (1 review de diferença) exatamente no regime saturado: 15×
mais sensível a ruído com o segundo colocado em 95% do que em 25%. Sob o
nulo de permutação, a normalização faz `impacto_emocional` sozinho responder
por **62,6%** do ruído, contra 13,9% do maior contribuinte sob o lift
absoluto. Nenhuma das três métricas atinge cobertura ≥18/35 filmes com ruído
≤35%; **a métrica atual é a menos ruim das três**, e é assim que ela deve
ser lida.

### A MARGEM — a lei por `n` (v1.9.34). **Este é o parâmetro em vigor.**

```
limiar(n) = 144,4 / √n   pontos percentuais       n = o MENOR dos três buckets
```

**A comparação é EXATA, na forma quadrada que elimina a raiz.** `144,4/√n` é
irracional e comparar em float jogaria fora a garantia que a v1.9.15 comprou
caro (*"nenhuma decisão de estado depende de arredondamento de float"* — cinco
filmes já caíram fora da margem uma vez por isso). Para `lift > 0`:

```
lift >= (1444/1000)/√n      ⟺      lift² · n  >=  Fraction(2085136, 1000000)
```

`lift` é `Fraction` de 0 a 1 (não pontos percentuais: 144,4pp de constante é
1,444 nessa escala), `n` é `int`, e `lift² · n >= Fraction(2085136, 1000000)` é
uma comparação de racionais **exata** — sem raiz, sem float, sem tabela de
arredondamento. **Conferido: a forma exata devolve exatamente os mesmos 6 filmes
que a aritmética de alta precisão.**

> **A GUARDA DE SINAL `lift > 0` É PARTE DA LEI, NÃO OTIMIZAÇÃO — e quem for
> "simplificar" a expressão precisa esbarrar nisto.** Elevar ao quadrado
> **apaga o sinal** e só é monotônico no ramo positivo. Sem a guarda, um lift de
> **−0,5** com n = 40 daria `0,25 · 40 = 10 >= 2,085136` — **APROVADO**. E −0,5
> de lift significa que o eixo é 50pp MENOS falado naquele grupo que no
> concorrente: o produto publicaria "este é o assunto próprio deste grupo"
> sobre o assunto que o grupo é o que MENOS toca. Não é um erro de borda, é a
> afirmação exatamente invertida, e ela passaria em qualquer teste que só
> exercitasse lifts positivos.
>
> Isto estava **latente na formulação da lei** quando ela foi aprovada — a
> equivalência `lift >= k/√n ⟺ lift² · n >= k²` só vale sob `lift > 0`, e a
> condição não estava escrita. Fica escrita agora, com teste nomeado
> (`test_lift_nao_positivo_reprova_sempre`).
>
> **A ordem importa:** `lift <= 0` reprova **por inspeção, ANTES** da
> multiplicação. Não é o mesmo que checar depois.

**PISO — `n < 10` no menor bucket: o estado `contraste` NÃO É PUBLICADO.** Não
é `valorativo`: é **ausente**, no mesmo estatuto de `montar_bloco` devolver
`None` sem classificação — **chave ausente distingue "não medido" de "medido e
sem contraste"**. Publicar `valorativo` ali seria trocar uma afirmação sem
lastro por outra: naquele `n` a medição não distingue os dois estados, e dizer
"os grupos falam das mesmas coisas" é tão sem base quanto dizer o contrário.
Afeta **1 filme hoje** (`obsession-2026`, n = 5/6/8, cujo estado tem
**P(ruído) = 0,976**); o piso entra na versão completa, e não como exceção
nomeada, porque a expansão de catálogo trará mais filmes com bucket pequeno.

> **O DEFEITO QUE O PISO ENCONTROU, e ele se manifesta de dois jeitos OPOSTOS
> nos dois lados do produto.** Antes desta versão o estado nunca podia faltar,
> então os dois consumidores tratavam a ausência por omissão — e cada um caía
> num ramo diferente, os dois publicando exatamente o que o piso existe para
> não afirmar:
>
> - **Python** (`veredito.py`, montagem do briefing): `if estado ==
>   "valorativo": … else: <ramo temático>`. Estado ausente cai no **ramo
>   TEMÁTICO**, e o briefing manda o modelo escrever *"a medição encontrou
>   assunto próprio de pelo menos um grupo"* — sobre o filme cuja medição se
>   RECUSOU a decidir.
> - **Frontend** (`frontend/js/filme.js`, `veredictoBlock`): sem
>   `veredito.texto` cai no fallback de render, que com nenhum eixo acima da
>   margem produz a frase **VALORATIVA** — *"os grupos falam das mesmas coisas
>   e divergem no julgamento"*, que é a outra afirmação proibida ali.
>
> **Um defeito que produz as duas afirmações contrárias, por caminhos
> diferentes, merece estar escrito** — porque a lição não é "faltou um `elif`".
> É que **ausência tratada por omissão vira a asserção que o código já tinha à
> mão**, e qual delas é acidente da estrutura do `if`. Correção: os dois
> caminhos passam a ter tratamento EXPLÍCITO de estado ausente (`montar_briefing`
> devolve `None`, e o fallback de render é bloqueado), nunca um ramo padrão.

#### A linha que explica a AUSÊNCIA de veredito (v1.9.34)

Sem `contraste`, a chave `veredito` **some do JSON** — estatuto aditivo de
`ficha` (§3[F]) e `distribuicao` (§3[G]). Mas a página **não fica em silêncio**,
pelo mesmo argumento que este §2.5 já usou para a ausência de bullets de
contraste: *"se ficar como AUSÊNCIA, vai parecer bug ao leitor"*. Na posição do
veredito entra, gerada por **CÓDIGO**, determinística, **zero LLM**:

> **"A amostra analisada deste filme é pequena demais para dizer se os grupos
> falam de coisas diferentes ou se falam das mesmas coisas e divergem no
> julgamento."**

**Ela NÃO é um veredito** — é a explicação de por que não há um —, e o
tratamento visual a distingue de um (classe própria, não `.verdict`).

**Por que esta frase e não outra, em três invariantes:**

1. **Ancorada na BASE, nunca na MAGNITUDE.** É exatamente a exceção que a
   v1.9.22 preservou ao proibir deflação: hedge sobre *"a amostra analisada"* é
   legítimo; hedge que encolhe a quantidade (*"relatos pontuais…"*) é
   falsidade. A frase fala do denominador, não do achado.
2. **Zero algarismo** (v1.9.20) e **zero quantificador de magnitude** (v1.9.22).
3. **Os DOIS estados aparecem no mesmo nível** — "falam de coisas diferentes"
   e "falam das mesmas coisas e divergem no julgamento", por extenso, nenhum
   reduzido a resíduo do outro. **É a neutralidade do §0 aplicada à frase que
   explica por que não há estado:** discordar sobre o mesmo assunto é achado de
   primeira classe neste produto (é o que 29 dos 35 filmes publicam), e uma
   redação como *"ou apenas discordam"* rebaixaria em prosa o estado que o
   resto do produto trata como primeira classe. Protegida por teste nomeado.

#### O limiar por `n`, e a taxa que ele realiza

| n | limiar | taxa de falso contraste realizada |
|---:|---:|---:|
| 10 | 45,7pp | 0,060 |
| 15 | 37,3pp | 0,061 |
| 20 | 32,3pp | 0,049 |
| 25 | 28,9pp | 0,040 |
| 30 | 26,4pp | 0,075 |
| 35 | 24,4pp | 0,053 |
| **40** | **22,8pp** | **0,037** |
| 50 | 20,4pp | 0,040 |
| 100 | 14,4pp | 0,047 |

Entre **3,7% e 7,5%**, média ≈ 5%. A oscilação em torno do alvo é a
**quantização** — o lift só assume múltiplos de `100/n`, e em n=30 nenhum limiar
acerta 5% exatamente. **Leitura prática:** nos 29 filmes com 40/40/40 a lei dá
22,8pp e o corte operante é **25,0pp** (o próximo múltiplo de 2,5pp). A lei não
faz nada de mais fino que um limiar fixo de 25pp ali — **ela existe pelos outros
6**, cujos limiares são `talk-to-me-2022` 23,1 · `wicked-2024` 23,7 · `wonka`
25,5 · `the-godfather` 26,4 · `pearl-2022` 27,8 · `obsession-2026` 64,6.

#### O que mediu isso: o NULO DO MÁXIMO, que é novo

Três medições de nulo/reamostragem já existiam no projeto e **nenhuma era
esta**. O nulo de permutação da tabela histórica abaixo conta **pares (eixo,
bucket) agregados sobre o catálogo**; os bootstraps de
`ESTUDO_CATALOGO_35.md` §8 e `MEDICAO_VERIFICACAO_BINARIA.md` Entrega 2
reamostram em torno do **observado**. Faltava a distribuição do **máximo sobre
as 30 células sob a hipótese de que não há contraste nenhum** — que é a
estatística que o estado `contraste` de fato usa, porque `tematico` é
*"alguma das 30 células passa do limiar"*.

Desenho registrado ANTES de rodar em `DESENHO_NULO_DO_MAXIMO.md`; resultados em
`ESTUDO_MARGEM_20PP.md`. **B = 10.000 permutações por filme, semente 24**,
embaralhando o rótulo de bucket dentro de cada filme — preserva o conjunto de
eixos de cada review intacto (logo toda a **dependência entre eixos da mesma
review**), a frequência global de cada eixo e o tamanho de cada bucket.

**O que ele mediu, e é o diagnóstico que fecha o caso da margem de 20pp:**

| | |
|---|---|
| percentil de 20pp no nulo (mediana dos 35) | **82** |
| taxa de falso contraste a 20pp, n=40 | **17,3%** |
| taxa de falso contraste a 20pp, no `n` MEDIANO em que o catálogo foi publicado (28) | **37,3%** |
| filmes distinguíveis do nulo a α=0,05, sem correção | **6 de 35** |
| … com Holm–Bonferroni sobre os 35 | **1 de 35** |
| FDR entre os 16 `tematico` sob cobertura 100% | **24% a 38%** |
| nos 6 filmes cujo veredito nomeia causa que o dado completo não sustenta: P(ruído) média | **0,633** |

O último número é o que justifica a mudança: **essas seis páginas nomeavam uma
causa que, na amostra em que foram decididas, tinha ~63% de chance de ser
sorteio.**

**E o `n` publicado nunca foi 40.** Reconstruído do campo `de_n` dos 35
`resultado/<slug>.json`: mediana **28**, média 27,3, mínimo **5**, com **56 dos
105 buckets abaixo de 30** e **24 abaixo de 20**. A frase "n≈40 é insuficiente
para a margem de 20pp" era verdadeira e otimista.

#### ⚠️ LIMITAÇÃO IN-SAMPLE — leia isto ANTES de expandir o catálogo

**A lei foi calibrada sobre exatamente os mesmos 35 filmes que ela julga.** Com
35 não existe como separar treino de teste sem perder todo o poder, e não foi
feito. Consequências, sem maquiagem:

- **A taxa de 5% é uma estimativa in-sample, e portanto OTIMISTA.** O valor
  out-of-sample é desconhecido e quase certamente maior. Não cite "5%" como
  propriedade da regra; cite como "5% medido nos 35 que a calibraram".
- **A constante 144,4 é `média(q95 · √n)` sobre n ∈ {20, 30, 40, 50, 100}** do
  nulo desses 35. Ela carrega a estrutura de co-ocorrência de eixos DESTE
  corpus (2,95 eixos por review em média, faixa 2,12–3,67). Um catálogo com
  carga de eixos diferente terá nulo diferente — **MEDIDO: corr(carga,
  P(falso)) = +0,74**, com a taxa indo de 0,119 a 0,206 entre os extremos do
  catálogo atual. É efeito de segunda ordem contra `n`, mas não é zero.
- **A expansão de catálogo é o PRIMEIRO teste out-of-sample desta lei, e deve
  ser tratada como teste.** Ao acrescentar filmes: rode o nulo do máximo sobre
  os filmes NOVOS, sozinhos, e compare a taxa realizada com a tabela acima. Se
  divergir materialmente, **é a constante que precisa ser recalibrada — não os
  filmes novos que estão errados.**
- **Nada aqui vale para filmes fora dos 35.** Nem a constante, nem a tabela, nem
  o piso de `n < 10` como "afeta 1 filme".

#### O critério "cerca de um terço do catálogo" está APOSENTADO

A v1.9.15 registrou como critério de sucesso: *"20pp entrega contraste em cerca
de um terço dos filmes sem publicar listas majoritariamente ruidosas"*, e
celebrou 18/35 por estar mais perto de um terço que 13/35. **Esse critério sai
de vigor nesta versão, e a razão é medida, não estética.**

Ele é um alvo de **COBERTURA**, e foi fixado quando `valorativo` era o estado
fraco — o defeito da v1.9.20 era o veredito publicar a MESMA frase em 20 de 35
filmes. **`valorativo` não é mais o estado fraco. MEDIDO
(`ESTUDO_MARGEM_20PP.md` §5.2):**

- os 17 vereditos `valorativo` publicados são **17 textos distintos**, com
  **zero frases de mais de 25 caracteres repetidas** entre dois filmes
  quaisquer — a reescrita da v1.9.21 e o ataque estrutural da v1.9.22 mataram o
  defeito;
- o ramo `valorativo` **nomeia o `assunto_compartilhado`**, que é uma afirmação
  de conteúdo real e vem de **FREQUÊNCIA**, não de lift;
- e frequência é a estatística estável do sistema: no evento real de cobertura
  70,7% → 100%, o eixo nomeado pelo ramo `valorativo` mudou em **8 de 35**
  filmes, contra **16 de 35** do eixo de maior lift que o ramo `tematico`
  nomeia. **Mover um filme para `valorativo` move a afirmação publicada da
  estatística MENOS estável do sistema para a MAIS estável.**

**O critério que entra no lugar é de ERRO, não de cobertura:** o limiar é o que
mantém a taxa de falso contraste em nível declarado (≈5%), e o número de filmes
`tematico` é **consequência**, não alvo. Sob a lei, o catálogo é **6 `tematico`
/ 29 `valorativo` / 1 sem estado** — e 6/35 não é um defeito a corrigir
afrouxando a lei.

#### α = 0,05 e não 0,10 — a razão é assimetria de dano

`ESTABILIDADE_10_FLIPS.md` isolou os dois erros e eles não custam o mesmo. Um
filme que deveria ser `valorativo` e sai `tematico` publica, em prosa
categórica, uma causa que não existe ("quem não recomenda rejeita pelo ritmo
arrastado"). Um filme que deveria ser `tematico` e sai `valorativo`
**subafirma** — deixa de contar algo verdadeiro, sem afirmar nada falso.
**Quando os dois erros custam coisas diferentes, o nível se escolhe pelo mais
caro.** α = 0,10 daria 9 `tematico` com FDR de ~24–39%; α = 0,05 dá 6 com FDR
de ~15–23%.

**Registrado como escolha, não como fato:** a multiplicidade entre os 35 filmes
NÃO é corrigida. Corrigir (Holm) responde *"existe alguma afirmação errada no
catálogo?"* — a pergunta certa se o produto fizesse uma afirmação sobre o
catálogo. Cada página faz sua própria afirmação, lida isoladamente, então o
controle certo é o de **proporção** (FDR), não o de família. Quem argumentar
que o leitor navega o catálogo inteiro e forma impressão agregada estará
pedindo Holm, e **não estará errado** — estará pedindo um catálogo com 1
`tematico`.

#### O que MUDA e o que NÃO MUDA de forma

**NÃO muda de forma:** o template do veredito continua ramificando em
`tematico`/`valorativo` com os mesmos dois blocos de instrução (§3[V]); a
interface continua com os mesmos comportamentos por ramo; a métrica de lift, a
seleção 2+3 de bullets, a taxonomia, o `taxonomia_id`, a cota 40/40/40, o
`assunto_compartilhado`, o piso de 25% e `min_chars` estão **intocados**.
**Só muda QUAIS filmes caem em cada ramo** — mais o caminho novo de estado
ausente, que é a única adição de forma da versão.

---

### A margem de 20pp — REGISTRO HISTÓRICO (v1.9.14 a v1.9.33)

**Esta seção descreve o parâmetro que vigorou até a v1.9.33 e não está mais em
vigor.** Fica porque o raciocínio dela é o que a lei acima substitui, e porque
a tabela de nulo por par continua sendo a medição correta de *outra* coisa (a
taxa de ruído por célula agregada).

Medida por **nulo de permutação** (2000 rodadas, embaralhando o rótulo de
bucket DENTRO de cada filme — preserva a frequência global de cada eixo e
destrói só a associação com o grupo). **Tabela original da v1.9.14, sob a
comparação `>` estrita que se revelou o mesmo bug de arredondamento da
medição de referência** (ver seção anterior) — mantida como registro
histórico:

| margem | pares acima | fração que cruzaria por acaso | filmes com ≥1 eixo acima |
|---|---:|---:|---:|
| 15pp | 41 | 63% | 22/35 |
| 20pp | 21 | 41% | 13/35 |
| 25pp | 12 | 29% | 9/35 |

**Recalculada na v1.9.15 sob `>=` exato** (a comparação corrigida, mesma
seção anterior) — os números que valem a partir desta versão:

| margem | pares acima | fração que cruzaria por acaso | filmes com ≥1 eixo acima |
|---|---:|---:|---:|
| 15pp | 44 | 61% | 24/35 |
| **20pp** | **27** | **34%** | **18/35** |
| 25pp | 13 | 27% | 10/35 |

(`scripts/recalcular_margem_exata.py`, rodado DEPOIS da unificação da
Entrega 1 — mesma metodologia da medição original de
`classificar_10.py`/`votacao_3.py`: 2000 rodadas de permutação, mesma
semente, embaralhando o rótulo de bucket dentro de cada filme; só a
aritmética do lift e da comparação muda de `float` para `Fraction`. Os
números de `pares`/`ruído` mudam por 1-2 unidades em relação à primeira
rodada desta versão — os 3 filmes estendidos pela Entrega 1 têm, na
classificação BRUTA que esta tabela usa, buckets de tamanho ligeiramente
diferente de 40 agora, porque `consenso.jsonl` acumula a seleção antiga e a
nova lado a lado; a contagem `filmes com ≥1 eixo acima` — o que a margem de
20pp de fato decide — não mudou. Esta tabela mede a REGRA sobre o catálogo
inteiro e usa a amostra classificada bruta por decisão metodológica de
longa data (não a analisada — essa é a base do bloco `eixos` publicado por
filme, §[D3]); a ordem de execução desta versão é RECALCULAR a tabela
DEPOIS de qualquer mudança na classificação, nunca antes.)

**Decisão do dono do projeto: 20pp.** Não há margem correta — é pureza de
lista contra cobertura, e o trade-off ficou mais caro depois da correção de
recall em review curta, porque a frequência média por eixo subiu. 20pp
segue sendo o ponto escolhido entre os dois extremos, com os números
recalculados aqui para que a escolha continue revisável com dado, não com
memória.

**CORREÇÃO DE REGISTRO (v1.9.34): o "34% que cruzaria por acaso" está medido na
população ERRADA, e o número na população certa é PIOR.** A tabela acima usa,
por decisão metodológica declarada logo abaixo, a amostra classificada **bruta**
(`consenso.jsonl`), que acumula a seleção antiga e a nova lado a lado (§[D3],
"duas populações de 40") e **não** é a população que o bloco `eixos` publicado
conta. Recalculada na população publicada (produção ∩ `consenso_verificado`,
cobertura 100% de §2.8), com o mesmo método:

| margem | pares acima (observado) | esperado sob o nulo | fração de ruído |
|---|---:|---:|---:|
| 15pp | 56 | 28,9 | **51,6%** |
| **20pp** | **23** | **9,9** | **42,8%** |
| 25pp | 11 | 3,7 | **33,3%** |

**A margem de 20pp entregava 42,8% de ruído por célula na população que o
produto de fato publicava, não 34%.** O número antigo não está errado para o
que mede; está medindo outra população. `CLASSIFICACAO_CONSOLIDADO.md` §6 já
registrava 41,1% num terceiro corpus, e o valor recomputado cai em cima dele.

### A comparação é `>=`, EXATA — revertida na v1.9.15

Cinco dos 35 filmes têm o melhor lift em **exatamente 20,0pp**: `barbie`,
`bones-and-all`, `hereditary`, `im-still-here-2024` e
`spider-man-across-the-spider-verse` (com cota 40, o quantum do lift é
2,5pp, e 20,0pp = 8 reviews de diferença — cair na linha não é raro, é
esperado).

A medição de referência (`resultado/votacao-3/metricas_lift.json`), a que
fundamentou a escolha original de margem, comparou com `>=` em ponto
flutuante — e `0,2` binário é ligeiramente MENOR que a fração exata: os
cinco caíram fora por acidente de representação, não por decisão, e é daí
que veio o número **13/35** que a v1.9.14 registrou como escolhido.

**A v1.9.14 tentou fechar essa falha trocando a comparação para ESTRITA
(`lift > margem`)** — errado: isso reproduzia o número 13/35 por construir
a MESMA fronteira que o bug produzia por acidente, em vez de corrigir o
bug e aceitar a fronteira real que a medição sempre mediu. Sob aritmética
exata **sempre foram 18/35** — o `>=` que a medição de referência pretendia
usar. **Decisão do dono do projeto (v1.9.15): manter a margem em 20pp, com
`>=` exato.** Contraste temático passa de 13 para **18 de 35 filmes**. O
critério original — "20pp entrega contraste em cerca de um terço dos filmes
sem publicar listas majoritariamente ruidosas" — **melhora** sob 18/35
(mais perto de um terço do catálogo que 13/35 estava), e `>=` é a semântica
natural de "margem mínima": um eixo com exatamente 20pp de lift ATINGE a
margem, não fica fora dela por uma fração de ponto percentual.

**O cálculo NÃO usa ponto flutuante.** Frequência e lift são frações exatas
(`Fraction`) sobre contagens inteiras, e a margem é `Fraction(20, 100)`,
comparada com `>=` também em `Fraction`. É o mesmo compromisso da v1.9.14
(nenhuma decisão de estado depende de arredondamento de float) com a
fronteira corrigida para a que a medição sempre pretendeu produzir.

### Seleção de bullets — 2 de FREQUÊNCIA + 3 de LIFT

Os bullets de cada bucket deixam de ser "os 6 temas que o LLM devolveu,
ordenados por menção" e passam a ser escolhidos em CÓDIGO, sobre os eixos:

- **2 bullets de maior FREQUÊNCIA** — o que o grupo mais fala. É o eixo de
  CONSENSO, e ele entra mesmo quando os outros grupos falam tanto quanto:
  frequência alta sem lift não é ruído, é o assunto do filme.
- **3 bullets de maior LIFT** — o que **só** esse grupo fala. É o eixo de
  CONTRASTE, e aqui a margem de 20pp vale: eixo com lift abaixo dela **não
  entra**, e a lista fica mais curta em vez de completada com ruído.

Um eixo já escolhido por frequência não é escolhido de novo por lift — a
lista tem no máximo 5 entradas e no mínimo 2, e o número de entradas é
informação, não defeito de preenchimento. Empate é desfeito pela ordem
canônica dos eixos, para que dois filmes com o mesmo perfil não saiam em
ordens diferentes por acidente de iteração.

**Por que os dois critérios, e não só o lift.** Uma lista só de contraste
seria vazia em 22 dos 35 filmes (§2.5) e, nos outros 13, esconderia do
leitor o assunto principal do grupo. Uma lista só de frequência é o que
existia antes, e não responde a pergunta que o produto faz — *no que estes
grupos discordam?*. Os dois lados vêm rotulados como o que são, nunca
misturados numa lista única sem etiqueta.

### Estado `contraste`: `tematico` | `valorativo` | **ausente** (v1.9.34)

**Os três casos, e o terceiro é novo:**

| `n` do menor bucket | condição | `contraste` |
|---|---|---|
| ≥ 10 | alguma das 30 células atinge `limiar(n)` | `"tematico"` |
| ≥ 10 | nenhuma atinge | `"valorativo"` |
| **< 10** | — | **chave AUSENTE do bloco `eixos`** |

**Ausente não é um terceiro VALOR; é a ausência da chave**, no mesmo estatuto
do bloco `eixos` inteiro quando não há classificação. Um consumidor que faça
`eixos.get("contraste") == "valorativo"` continua correto; um que faça
`eixos["contraste"]` quebra, e deve quebrar. **A regra para todo consumidor:
ausência significa "não medido", nunca "medido e sem contraste".** O resto do
bloco `eixos` (linhas, frequências, lifts, bullets) **continua sendo publicado
normalmente** — o que falta é só a decisão binária, porque é ela que o `n` não
sustenta.

Contagem atual do catálogo sob a lei da v1.9.34: **6 `tematico`, 29
`valorativo`, 1 sem estado** (`obsession-2026`).

---

*A partir daqui, esta subseção é o registro da v1.9.14/v1.9.15, sob a margem
fixa de 20pp. As contagens abaixo (13/22, 18/17) são históricas.*

Filme sem NENHUM eixo acima da margem recebe `contraste: valorativo`. **São
22 de 35 filmes (63%) — quase dois terços do catálogo.** O estado não é caso
de borda; é o mais comum.

Isso **não é falha do produto**. Significa que os três grupos falam das
mesmas coisas e discordam apenas no veredito — informação honesta e
interessante sobre o filme. A consequência de desenho é obrigatória: o
estado precisa de tratamento de **primeira classe** (campo explícito no
JSON, o movimento 3 sabendo dizê-lo, e área visual própria na interface). Se
ficar como AUSÊNCIA de bullets de contraste, vai parecer bug ao leitor.

*(Nota de registro: a tabela da seção 7 de `CLASSIFICACAO_CONSOLIDADO.md`
rotula a coluna de 13/9/22 como `contraste: valorativo`; a coluna é, na
verdade, a de filmes COM contraste temático. A leitura correta é a desta
seção: a 20pp, 13 com contraste temático e 22 valorativos.)*

**Atualização da contagem (v1.9.15, `>=` exato; confirmada na v1.9.21):** sob
a comparação exata o catálogo é **18 `tematico` / 17 `valorativo`** de 35 — o
"22 de 35" acima é a contagem da v1.9.14, sob o `>` estrito que reproduzia o
bug de ponto flutuante. Fica no texto porque o raciocínio de desenho que ele
sustenta não muda: o estado não é caso de borda, é quase metade do catálogo.

**Achado da v1.9.21 — os 17 `valorativo` são EXATAMENTE os 17 filmes que
caem no ramo "os grupos falam das mesmas coisas" do veredito (§3[V]).**
Nenhum filme `valorativo` escapa do ramo. Os outros 3 filmes do ramo
(`joker-folie-a-deux`, `spider-man-across-the-spider-verse`, `wonka`) são
`tematico` com o contraste morando SÓ no bucket do meio — que nunca é um dos
dois lados do veredito. A consequência prática é de método, não de produto: a
verificação anti-fabricação de contraste do §3[V] é uma varredura de
**população inteira**, não de amostra.

### `impacto_emocional` entra no schema COM a limitação registrada

O eixo aparece em **75,5%** do corpus — o mais frequente por larga margem —
e tem **precisão medida de 0,486** contra o gabarito humano fechado de 100
reviews: **51% das marcações de produção são falsas**. Recall 0,921.

**Três tentativas de corrigir a saturação foram testadas e REFUTADAS por
medição** (detalhe em `CLASSIFICACAO_CONSOLIDADO.md` §5): lift normalizado
(amplifica o ruído, acima); separar eixo de cobertura de eixo de contraste
(move o problema — filmes sem nenhum bullet de contraste sobem de 17 para
20 de 35); e definição apertada no prompt (75,5%→71,3% projetado, segue
saturado; nos 13 veredictos secos que o gabarito humano desmarcou, a
variante deixou de marcar em só 3, e ADICIONOU marcação errada em 2 onde o
prompt original acertava).

O eixo **entra assim mesmo**, com esta limitação declarada, e não escondido:
removê-lo do schema apagaria um eixo que o público de fato usa, e as três
tentativas de conserto estão medidas e registradas como refutadas — não como
pendências.

Existe uma correção que **funcionou** — o passe de verificação separado
(V2 `alvo`), que leva a precisão de 0,486 para 0,794 em passada única, com
projeção de de-saturação de 75,5% para 35,7% no corpus.

**CORREÇÃO DE REGISTRO (v1.9.31): ela FOI aplicada, na v1.9.16, e este
parágrafo a descrevia como pendente desde então.** O texto anterior — *"uma
correção que funcionou e que NÃO foi aplicada… é decisão pendente do dono do
projeto"* — descrevia o estado de quando foi escrito, e não foi atualizado
quando a adoção aconteceu (changelog da v1.9.16, item 1). O passe roda como
estágio à parte após o consenso de votação
(`scripts/verificador_impacto.py aplicar-producao`), produz
`resultado/votacao-3/consenso_verificado.jsonl` + manifesto, e
`pipeline._carregar_consenso_producao` **prefere o verificado** quando ele
existe e está em dia — com erro explícito, não fallback silencioso, se
`consenso.jsonl` cresceu depois da verificação. A aplicação é declarada no
bloco publicado, em `eixos.verificador`.

**O estado ATUAL do eixo, medido sobre o consenso de produção:**

| | `consenso.jsonl` (cru) | `consenso_verificado.jsonl` (**produção**) |
|---|---:|---:|
| `impacto_emocional` no corpus (n=4.181) | 75,6% | **36,1%** |
| na seleção de produção (n=2.866) | 75,6% | **34,6%** |
| eixos por review | 3,42 | 3,01 |
| reviews sem nenhum eixo | 0,2% | 2,0% |

A projeção de 35,7% acertou dentro de 1pp. **O eixo não está mais saturado**;
`n_removidas_no_corpus` é 1.654 e está carimbado em cada filme publicado.

**O que NÃO mudou, e continua valendo:** a precisão de 0,486 é a do prompt de
classificação **sem** o passe, e é ela que justifica o passe existir; as três
tentativas de conserto pelo prompt seguem **refutadas** (parágrafos acima); o
ganho de margem é pequeno (15/35 filmes a 20pp contra 13/35 sem o passe, na
contagem da v1.9.14) — a de-saturação corrigiu a precisão do eixo, não o
problema do lift. E a dependência de arquitetura fica registrada como
limitação: a precisão de 0,79 depende de um **script separado** ter sido
rodado, e não de uma etapa do pipeline; o `taxonomia_id` cobre o prompt de
classificação, não o passe de verificação.

---

## 2.6 Feelings — EM ESPERA, com dependência de ordem registrada (2026-08-29)

Registro de decisão do dono do projeto. **Nada aqui está implementado, e nada
aqui autoriza implementar.**

**Feelings NÃO é descartado.** A medição de `MEDICAO_SPLIT_E_FONTES.md`
(Entrega 3) achou que o TMDB emite `mood` editorial junto com as `keywords` —
`moody`, `bitter`, `playful`, `so bad it's good`, presentes em 17 de 35 filmes
— colidindo com a categoria que `DESENHO_CLASSIFICACAO_V2.md` atribuiu à
review. **Essa colisão é argumento para NÃO misturar as duas fontes, não para
descartar uma delas.** As duas semânticas são diferentes e ambas são reais:

| fonte | o que a etiqueta significa | quem atribuiu |
|---|---|---|
| **review-derived** (`mood`, `experiencia`, `narrativa`) | o que ficou em quem assistiu | o público |
| **work-derived** (`tema`, `contexto`) | do que a obra trata — máfia, família, guerra | quem cataloga |

Elas continuam como **entidades internas SEPARADAS**, com listas próprias e
sem precedência de uma sobre a outra, exatamente porque `mood` do TMDB é
catalogação editorial e `mood` de review é relato de leitor. Fundi-las
produziria uma etiqueta cuja procedência o produto não saberia declarar.

**Feelings não avança até a granularidade/faithfulness dos TEMAS estar
resolvida.** A razão é de ordem, não de mérito: feelings é uma **segunda**
camada de classificação sobre o mesmo material, e adicioná-la a um sistema cuja
**primeira** camada ainda erra — `roteiro_estrutura` em 55,5% do corpus, a
contagem por tema sem gabarito confiável, o `contradiz` com recall medido em
~1 de 5 — aumenta o espaço de erro sem isolar a causa. Um filtro público errado
não seria distinguível de uma classificação de tema errada por baixo dele.

**A dependência, explícita:** feelings aguarda o veredito da verificação
binária por (review, tema) — a Entrega 1 de `MEDICAO_VERIFICACAO_BINARIA.md`,
que **reprovou** no critério registrado. Enquanto a primeira camada não tiver
um número de menções que o código possa defender, a segunda não começa. As
cinco perguntas bloqueantes já listadas em `DESENHO_CLASSIFICACAO_V2.md`
(entre elas o gabarito humano de ~100 reviews para feelings) continuam
valendo e são posteriores a esta.

**Ressalva acrescentada em 2026-08-30:** a reprovação da verificação binária
citada acima **não está estabelecida** — o critério que a produziu (C1a) foi
medido contra o gabarito dos 5 casos, que §2.7 mostra subestimar. Isso não
libera feelings: a dependência de ordem continua valendo, agora com a primeira
camada em estado *indeterminado* em vez de *reprovado*, o que é motivo igual
para não empilhar a segunda.

---

## 2.7 AVISO — o gabarito de contagem à mão dos 5 casos SUBESTIMA (2026-08-30)

**Quem for usar os cinco números de contagem à mão do `ESTUDO_CATALOGO_35.md`
§12 (`wonka`, `talk-to-me-2022`, `napoleon-2023`, `interstellar`, `cats-2019`)
precisa ler isto antes.** Eles já foram a régua de **duas** reprovações — a da
contagem por eixo (`MEDICAO_CONTAGEM_E_AB.md`, Entrega 1) e a da verificação
binária (`MEDICAO_VERIFICACAO_BINARIA.md`, critério C1a) — e **subestimam de
forma sistemática, não aleatória.**

**A causa é o protocolo, e está declarada no próprio estudo** (§12, "Protocolo
de leitura"): para cada bullet, ler **até 12** reviews que já carregam o eixo do
bullet, mais **até 6** que casam por palavra de conteúdo do tema. **Até 18 de
40**, e a segunda metade por casamento de palavra, num corpus multilíngue. Isso
não pode achar paráfrase, e não pode achar nada nos idiomas em que a palavra de
busca não foi escrita.

O estudo declarou um viés, mas na direção errada: escreveu que *"o viés deste
protocolo favorece o produto"* porque procura suporte onde ele é mais provável.
**Isso vale para o veredito qualitativo — achar suporte —, não para a
CONTAGEM:** ler 18 de 40 e casar por palavra só pode contar **a menos**.

**Os dois casos relidos por inteiro em texto corrido (as 40 reviews de cada
bucket, sem casamento por palavra):**

| caso | gabarito §12 | releitura integral | erro do gabarito |
|---|---:|---:|---:|
| `cats-2019` neg — *Experiência de visualização desconfortável* | 8 | **16** | **−8** |
| `interstellar` pos — *Fotografia e efeitos visuais deslumbrantes* | 8 | **14** | **−6** |

Em `interstellar` o número 8 **nunca teve derivação registrada**: o estudo
discute o *exemplo* do bullet e diz que o *tema* é "impecavelmente sustentado",
sem contar; o 8 aparece pela primeira vez na tabela de
`MEDICAO_CONTAGEM_E_AB.md`.

**ATUALIZAÇÃO (2026-08-31): os outros três casos foram refeitos sob o
protocolo P1–P7 completo, com resolução humana onde o modelo divergiu. Os
cinco casos estão todos refeitos agora.**

| caso | gabarito §12 | valor refeito (P1–P7) | fonte |
|---|---:|---:|---|
| `wonka` neg — *Fotografia e efeitos visuais criticados* | 1 | **sustenta 3, contradiz 1** | leitura integral direta pelo dono (32/32), sem estágio reduzido |
| `talk-to-me-2022` neg — *Diálogos e tom juvenil artificiais* | 2 | **sustenta 2, contradiz 0** | leitura em duas etapas, resolução humana — ver §"Confiabilidade medida..." abaixo |
| `napoleon-2023` med — *Batalhas visualmente impressionantes* | 13 | **sustenta 12, contradiz 1** | idem |

`talk-to-me-2022` fechou no MESMO valor do gabarito antigo (2). **Isto é
coincidência de destino, não validação do protocolo antigo** — os dois
métodos chegaram lá por caminhos diferentes: um por casamento de
palavra-chave numa subamostra do bucket (o método que §2.7 mediu subcontar
`cats-2019` em −8 e `interstellar` em −6, sem garantia nenhuma de acerto por
método, só por sorte de amostra); o outro por leitura completa das 40
reviews com frase literal registrada e resolução humana em cada
discordância. Concordarem no número não dá crédito ao protocolo antigo.

**Consequência para as duas reprovações, medida:** recomputando as mesmas
tabelas com os dois casos corrigidos e os três outros inalterados, o erro
absoluto médio contra o gabarito vira

| | gabarito §12 | gabarito com 2 de 5 corrigidos |
|---|---:|---:|
| `mencoes_aproximadas` | 3,00 | **3,80** |
| contagem por eixo | 3,60 | **2,80** |
| verificação binária | 5,20 | **2,40** |

**As duas reprovações se invertem sob a correção parcial**, e a direção do erro
residual é conhecida: os três casos não relidos estão, pelo mesmo mecanismo,
provavelmente baixos também — e corrigi-los para cima favorece ainda mais os
métodos que contam mais alto. **Nenhuma das duas reprovações deve ser tratada
como estabelecida enquanto os cinco não forem relidos por inteiro.**

**O que continua de pé sem depender do gabarito:** o argumento conceitual contra
a contagem por eixo (o eixo é **superconjunto** do tema, então trocar o número
do tema pelo do eixo é erro de categoria, não de calibração), a colisão de
barras em 28% dos bullets, os dois bullets com barra zero; e, contra a
verificação binária, a reprodutibilidade entre execuções idênticas
(Jaccard 0,70; `wonka` de 4 para 1), o recall de `contradiz` de 1 em 5, e o
custo real medido de US$ 23,82 em 300 filmes com 3 votos.

**Protocolo exigido para qualquer refação (P1–P7):** leitura **integral** do
bucket (todas as 32–40 reviews), **sem** casamento por palavra-chave, julgando
no idioma original, contra o **tema E a paráfrase publicada** (ver a revisão de
P4 abaixo), com três valores (`sustenta`/`não sustenta`/`contradiz`) e a frase
literal de cada review contada. Ver `AUDITORIA_POPULACAO_E_GABARITO.md`
§Entrega 4.

### P4 REVISADO (2026-08-31) — julgar contra o tema E contra a paráfrase

A versão anterior de P4 dizia *"contando no nível do **tema** (não do
exemplo)"*. **Está errada, e a calibração mostrou como.**

O que o leitor vê na tela é o par tema + `exemplo_parafraseado`, e é a
paráfrase que carrega a afirmação específica. Julgar só contra a formulação
curta do tema perde reviews que sustentam o que o produto de fato afirma.

**O caso que forçou a correção.** Em `wonka`/negativas, a paráfrase publicada
diz literalmente *"cenários artificiais"*, e a review [11] (alemão) diz *"Alles
ist mir einen Ticken zu künstlich"* com um exemplo visual concreto — o
chocolate que "não tem mais nada a ver com chocolate". Julgando só contra o
título *"Fotografia e efeitos visuais criticados"*, isso sai como `não
sustenta`; julgando contra a paráfrase, é `sustenta`. O dono contou `sustenta`;
a leitura por modelo contou `não sustenta`.

**P4 passa a ser:** o julgamento é contra o tema **e** contra o
`exemplo_parafraseado` publicado. Uma review que sustenta o que a paráfrase
afirma sustenta o bullet, mesmo que a formulação curta do tema não capture
aquilo. O quantificador da paráfrase continua **não** sendo testado (P3): se
ela diz "para a maioria", a pergunta segue sendo se ESTA review afirma a coisa.

### Confiabilidade medida da leitura por modelo sob P1–P7 — NÃO tem direção fixa

**CORREÇÃO DE REGISTRO (2026-08-31): a frase original aqui dizia que o
viés do modelo "tende ao conservadorismo", generalizando a partir de um
único ponto de calibração (`wonka`). Um segundo ponto (`talk-to-me-2022`)
mostrou o viés na direção OPOSTA. A generalização estava errada e o texto
abaixo a substitui — não a preserva como histórico, porque manteria uma
conclusão falsa disponível para leitura.**

**MEDIDO, três calibrações (leitura integral independente do dono e do
modelo, comparadas depois — `wonka`/negativas 32 reviews completas;
`talk-to-me-2022`/negativas e `napoleon-2023`/medianas com a folha reduzida
de duas etapas, §Consequência de desenho abaixo):**

| caso | tipo de julgamento | concordância |
|---|---|---:|
| `napoleon-2023`/med — *"Batalhas visualmente impressionantes"* | visual/concreto | **27/28 = 96,4%** |
| `wonka`/neg — *"Fotografia e efeitos visuais criticados"* | visual/concreto | **30/32 = 93,8%** |
| `talk-to-me-2022`/neg — *"Diálogos e tom juvenil artificiais"* | registro de fala, referência cultural, ironia | **10/14 = 71,4%** |

**A leitura correta não é "o modelo erra numa direção" — é que a
confiabilidade depende do TIPO de julgamento.** Temas visuais/concretos
("a fotografia é bonita/feia", "a batalha impressiona") têm alta
concordância nos dois casos medidos. Um tema de registro de fala — se a
gíria soa forçada, se uma referência cultural é a mesma coisa que o tema
afirma — tem concordância bem mais baixa, e a direção do erro nesse caso
foi para SUPERCONTAGEM, não subcontagem:

Em `talk-to-me-2022`, dos 5 casos que o modelo marcou `sustenta` (grupo G1),
**3 foram derrubados pelo dono** — o modelo aceitou como sustentação coisas
adjacentes ao tema (comparar o filme a um vídeo de conscientização escolar;
criticar o uso de memes num filme de terror; qualificar o diálogo de
"estilo Tarantino") sem que nenhuma delas afirme especificamente que a
gíria/diálogo *soa artificial/forçado*, que é o que o tema e a paráfrase
publicada afirmam. Em `wonka` e `napoleon-2023`, o padrão foi o oposto ou
ausente: em `wonka` o modelo perdeu um `sustenta` e um `contradiz`
(subcontagem, os dois casos do texto anterior); em `napoleon-2023` houve
só 1 discordância em 28, sem padrão de direção.

**Isso é o que justifica manter a leitura humana como DECISÃO, não como
fator de correção fixo.** Não existe um ajuste único ("some 1 sustenta",
"desconte 10%") que corrija a leitura do modelo em qualquer tema — o
próprio tipo de julgamento decide se o modelo tende a perder ou a
inflar, e isso só se sabe calibrando cada tema, não aplicando uma
constante.

### Achado novo — o modelo nunca usa "não sei julgar", mesmo devendo

**MEDIDO.** Nas 42 reviews das duas folhas reduzidas (`talk-to-me-2022` +
`napoleon-2023`), cobrindo pelo menos 6 idiomas além do português (inglês,
espanhol, francês, alemão, sueco, holandês, árabe, russo — a mistura variou
por bucket), **o modelo escolheu `não sei julgar` zero vezes**. Isso inclui
`viewing:1431255087` (árabe, `talk-to-me-2022`), que o dono marcou
corretamente como `não sei julgar` e o modelo respondeu `não sustenta` com
confiança implícita — sem sinalizar a limitação.

**A distinção que importa:** isto não é o mesmo erro que uma leitura errada
num idioma que o modelo de fato processa (esse é erro de interpretação,
esperado e mensurável pela concordância). É **excesso de confiança em
idioma dominado só parcialmente** — o modelo produziu um veredito com a
mesma aparência de certeza de qualquer outro, em vez de declarar a
limitação que a regra do prompt explicitamente autoriza ("é preferível a
chutar"). Zero ocorrências em 42 tentativas, num corpus que sabidamente
tem reviews em idiomas raros (ver a distribuição de idiomas do `wonka`,
§2.7 acima), é sinal de que a instrução de abstenção não está sendo
seguida na prática, não só de que o modelo raramente precisa dela.

**Recomendação para os próximos gabaritos da expansão:** reforçar a
instrução de abstenção no prompt com este caso como exemplo concreto —
"uma review em árabe/idioma pouco comum não é candidata automática a
`não sustenta`; se a confiança de tradução for baixa, declare `não sei
julgar`" — em vez de deixar a regra genérica ("é preferível a chutar")
sem um exemplo que mostre a falha real já observada.

**Consequência de desenho, registrada:** gabarito não deve ser produzido por
modelo sozinho. O desenho adotado é de duas etapas — o modelo lê o bucket
inteiro; o humano lê uma folha reduzida contendo (i) tudo que o modelo marcou
`sustenta`/`contradiz`, (ii) tudo que ele marcou `não sustenta` **com** o
assunto tocado, e (iii) uma amostra cega de controle das `não sustenta` que nem
tocaram o assunto, misturada sem marcação (semente registrada). **Onde houver
divergência, o veredito humano vale** — o gabarito existe para julgar saída de
modelo, e deixá-lo ser decidido por modelo onde há divergência com o humano é
a circularidade que a calibração existe para quebrar. A confiabilidade
variável por tipo de julgamento (acima) é o motivo estrutural de a decisão
final ser sempre humana: um fator de correção fixo não existe para aplicar
no lugar da leitura.

### Gabaritos fechados nesta calibração

| caso | sustenta | contradiz | não sustenta | não sei julgar |
|---|---:|---:|---:|---:|
| `talk-to-me-2022`/negativas — *"Diálogos e tom juvenil artificiais"* | **2** | **0** | 11 | 1 |
| `napoleon-2023`/medianas — *"Batalhas visualmente impressionantes"* | **12** | **1** | 15 | 0 |

**`talk-to-me-2022` fechou em 2 — o mesmo número do gabarito antigo de
`ESTUDO_CATALOGO_35.md` §12. Isto é COINCIDÊNCIA DE DESTINO, não validação
do protocolo antigo.** Os dois métodos chegaram ao mesmo número por
caminhos diferentes e por razões diferentes: o protocolo antigo leu uma
subamostra do bucket e casou por palavra-chave — o mesmo método que
§2.7 mediu subcontar em `cats-2019` (−8) e `interstellar` (−6), e que aqui
não tem nenhuma garantia de ter acertado por método, só por sorte de
amostra. O número desta sessão vem de leitura completa das 40 reviews com
resolução humana nos pontos de discordância — um processo auditável, com
frase literal registrada para cada veredito. Concordarem no valor final não
torna o protocolo antigo confiável; ele continua sem crédito.

---

## 2.8 Cobertura de classificação estendida a 100% (2026-08-30)

**Aplicado.** `1.190` reviews que faltavam classificar foram classificadas sob
a MESMA taxonomia (`ebab2667de74`), a mesma votação de 3 passadas, e o mesmo
verificador `V2_alvo`, pelo caminho oficial
(`scripts/estender_classificacao_producao.py` + `verificador_impacto.py
aplicar-producao`) — nenhum desenho novo. `pipeline.amostra_do_bruto` foi o
caminho usado (não `classificar_10.py:152`, que tem o defeito registrado em
§[D3]), então a extensão **não** reproduz o "dois quarentas". Custo medido por
diferença de linhas novas contra o commit-base: classificação US$ 0,1030
(3.570 chamadas), verificador US$ 0,0471 (964 chamadas) — **US$ 0,15 no
total**, não os US$ 0,03 nem os US$ 0,33 que duas projeções anteriores
estimaram.

**Cobertura: 100% verificada** (4.056/4.056, 35/35 filmes), não presumida —
conferida reconstruindo `amostra_do_bruto` para os 35 slugs e checando
interseção com `consenso_verificado.jsonl`.

### O que fecha

- **A ressalva de cobertura desigual de `ESTUDO_CATALOGO_35.md` §6c**
  (70,7%, 8 filmes abaixo de 50%) — fechada. Todo filme agora tem denominador
  de eixo igual ao denominador de análise.
- **A composição do bootstrap da margem** (§8 daquele estudo) — recomputada
  sobre a população completa; ver números abaixo.
- **As frequências por eixo publicadas** — recalculadas ao dígito sobre 100%
  da amostra; nenhuma se move mais que 1,2pp (tabela abaixo).

### O que NÃO fecha

- **O `n` por bucket** continua ~40 — a extensão preenche o denominador
  existente, não coleta review nova.
- **A margem de 20pp** não foi tocada nesta sessão — permanecia o parâmetro em
  vigor. **[v1.9.34] Deixou de ser: a margem fixa deu lugar à lei por `n`
  (§2.5), e a investigação que os 10 flips desta seção motivaram é exatamente
  a que a produziu.**
- **O gabarito dos 5 casos de `ESTUDO_CATALOGO_35.md` §12** — nenhum dos
  cinco foi relido; a extensão não tem relação com contagem de tema, só com
  cobertura de classificação por eixo.

### Achado principal — a margem porosa, confirmada com dado real

**MEDIDO.** Frequência por eixo: delta máximo **1,2pp** entre antes (n=2.866)
e depois (n=4.056) — a previsão registrada antes de rodar ("nenhuma
frequência se move mais que ~2pp") **se confirmou**.

A previsão sobre o estado `contraste` **não se confirmou**: **10 de 35 filmes
mudaram de estado** (6 tematico→valorativo, 4 valorativo→tematico) —
`bones-and-all`, `dune-2021`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `oppenheimer-2023`, `perfect-days-2023`,
`spider-man-across-the-spider-verse`, `the-substance`, `wicked-2024`.

**Investigado antes de prosseguir, como o critério desta sessão exigia.** A
causa **não é viés de conteúdo** das reviews que faltavam (a mesma medição que
sustentou a previsão original — comprimento e nota das 1.190 faltantes contra
as 2.866 já classificadas — permanece válida, e a frequência por eixo confirma
isso: delta máximo 1,2pp). A causa é que os 10 filmes tinham o lift observado
**a poucos pontos percentuais da margem de 20pp** (entre 14,9pp e 28,9pp nos
dois lados), e a margem já era conhecida como porosa nesse regime de n:
`ESTUDO_CATALOGO_35.md` §8 mediu, por bootstrap, que 13 das 31 marcações de
contraste sobrevivem a **menos de 60%** das reamostragens. Seis dos dez filmes
que mudaram de estado — `bones-and-all`, `everything-everywhere-all-at-once`,
`hereditary`, `napoleon-2023`, `perfect-days-2023`,
`spider-man-across-the-spider-verse` — já estavam nomeados naquela lista de
marcações frágeis (p<60%), e `the-substance` no near-miss. **Isto não é um
achado novo de instabilidade — é o mesmo achado, agora observado com dado
completo em vez de reamostragem simulada**, e reforça (não contradiz) a leitura
de que n≈40 é insuficiente para a margem de 20pp decidir com confiança.

### Recálculo lado a lado

| | antes (n=2.866, 70,7%) | depois (n=4.056, 100%) |
|---|---:|---:|
| reviews órfãs | 337/2.866 = 11,8% | 477/4.056 = 11,8% |
| reviews sem eixo | 57 = 2,0% | 79 = 1,9% |
| células acima da margem (bootstrap) | 31 | 23 |
| — p < 60% | 14 | 12 |
| — 60–90% | 16 | 10 |
| — ≥ 90% | 1 | 1 |
| filmes `tematico` | 18 | **16** |
| filmes `valorativo` | 17 | **19** |

Frequência por eixo (maior delta): `impacto_emocional` +0,8pp · `livre`
+0,5pp · `roteiro_estrutura` +0,3pp · `comparacoes` +0,4pp · `atuacao` −1,2pp —
todos os 11 eixos dentro de ±1,2pp.

**Nota de honestidade sobre a suíte de testes.** A extensão expôs dois
defeitos pré-existentes na suíte, nenhum deles novo nesta sessão: (1) a
fixture `catalogo` de `tests/test_eixos.py` lia `consenso.jsonl` (cru,
pré-verificador) em vez de `consenso_verificado.jsonl` — resíduo de quando o
teste foi escrito na v1.9.15, nunca atualizado quando o verificador foi
adotado na v1.9.16; (2) nem essa fixture nem `verificador_impacto.py
_cobertura_exata`/`_corpus_consenso` aplicavam `eixos._filtrar_pela_analisada`
— o mesmo "dois quarentas" que a v1.9.15 corrigiu em `montar_bloco`, nunca
replicado nesses dois caminhos de teste/projeção. Com 9 de 105 buckets
acumulados (o estado antes desta sessão) os dois defeitos eram invisíveis;
com 93 de 105 (o estado depois de estender 32 filmes) eles quebraram os
testes visivelmente. (1) foi corrigido nesta sessão (fixture agora lê o
verificado). (2) foi corrigido na fixture de `test_eixos.py` (que agora
filtra), mas **não** em `verificador_impacto.py` — fora do escopo autorizado;
fica registrado como limitação conhecida em
`tests/test_verificador_impacto.py::test_base_da_projecao_reproduz_10_de_35`.
Suíte: **1.524 de 1.525** — um teste (`test_os_5_filmes_na_linha_dos_20pp_
agora_sao_tematicos`) foi retirado, não substituído: a sua premissa (5 filmes
nomeados sentados exatamente em 20,0pp) era uma coincidência da amostra
PARCIAL de antes da extensão e deixou de ser verdade por construção — não há
assinatura equivalente a reafirmar sob a amostra completa.

---

## 2.9 Defasagem entre os artefatos publicados e o consenso estendido (2026-08-31)

**Para quem chegar aqui sem contexto:** os arquivos `resultado/<slug>.json`
**não foram tocados** por §2.8 e **continuam internamente coerentes** — eixos,
lift, `contraste` e `veredito` concordam entre si dentro de cada arquivo
publicado. Não há inconsistência dentro do produto. O que existe é
**defasagem**: cada `resultado/<slug>.json` foi gerado sob a cobertura de
classificação vigente na hora em que rodou (para a maioria dos 35, 70,7% —
ver §2.5, "duas populações de 40"), e `resultado/votacao-3/consenso_
verificado.jsonl` agora tem cobertura 100% (§2.8). Os dois nunca foram
reconciliados por regeneração.

**Medido, sem regenerar nada:** sob o consenso completo, **10 de 35 filmes
teriam estado `contraste` diferente do publicado** — detalhado em
`ESTABILIDADE_10_FLIPS.md`, com o lift antes/depois de cada um e, para os 6
que virariam `tematico → valorativo`, o texto do veredito publicado hoje na
íntegra:

| filme | publicado | sob consenso completo |
|---|---|---|
| `bones-and-all` | tematico | valorativo |
| `everything-everywhere-all-at-once` | tematico | valorativo |
| `hereditary` | tematico | valorativo |
| `napoleon-2023` | tematico | valorativo |
| `perfect-days-2023` | tematico | valorativo |
| `spider-man-across-the-spider-verse` | tematico | valorativo |
| `dune-2021` | valorativo | tematico |
| `oppenheimer-2023` | valorativo | tematico |
| `the-substance` | valorativo | tematico |
| `wicked-2024` | valorativo | tematico |

**Decisão do dono: NÃO republicar por ora.** Razão registrada: o estado de
contraste desses 10 filmes está instável **perto da margem de 20pp**, e três
medições independentes concordam nisso — o bootstrap de
`ESTUDO_CATALOGO_35.md` §8 (13/31 marcações sobrevivem a <60% das
reamostragens), a curva de retorno marginal por `n` (`MEDICAO_VERIFICACAO_
BINARIA.md`, Entrega 2: IC95 do lift dominante em 38,4pp com n=40, quase o
dobro da própria margem), e esta observação direta (§2.8, 6 dos 10 flips já
estavam na lista de marcações frágeis do bootstrap). **O estudo da margem —
a próxima sessão — pode reformular o limiar de 20pp, o que mudaria a lista
de filmes afetados.** Republicar agora, sob a margem atual, seria trabalho
refeito se a margem mudar.

**Esta defasagem é insumo do estudo da margem, não pendência esquecida.**
Qualquer sessão que reabra a margem de lift deve ler `ESTABILIDADE_10_
FLIPS.md` antes de decidir o novo limiar — ele é o conjunto de casos reais
que o novo limiar precisa resolver, não hipotéticos de bootstrap.

### FECHADA na v1.9.34 — a republicação aconteceu, sob a lei nova

**A defasagem descrita acima não existe mais.** O estudo da margem rodou
(`ESTUDO_MARGEM_20PP.md`), o dono aprovou a lei por `n` (§2.5), e os filmes
afetados foram republicados sob ela — **16 filmes**, não os 10 desta seção,
porque a lei muda mais estados que a extensão de cobertura sozinha. Os
`resultado/<slug>.json` e o consenso verificado voltam a estar reconciliados.

**A decisão de esperar se confirmou, mas por uma razão diferente da registrada
acima, e vale corrigir.** Esta seção disse que republicar sob 20pp "seria
trabalho refeito se a margem mudar". **MEDIDO: dos 10 filmes acima, apenas 2
(`dune-2021` e `wicked-2024`) teriam estado diferente sob a lei em relação ao
que a republicação sob 20pp lhes daria** — os outros 8 receberiam o mesmo
estado das duas vezes. A contabilidade real era 20 regenerações (10 agora + 10
depois) contra 16 (uma vez só): um argumento de **4 regenerações**, não do
trabalho inteiro. A razão FORTE para esperar era outra, e é a que valeu:
republicar sob 20pp colocaria no ar 16 estados com taxa de falso contraste de
24–38%, para tirar depois.

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

#### Âncora de profundidade — a progressão estava presa ao lugar errado (v1.9.5)

**O defeito, medido.** O bloco profundo da v1.9.2 compra uma mediana de **3
dias** sobre o raso. Em **26 de 34** filmes com material nos dois blocos, o
gap é de 7 dias ou menos; a média é 10 dias, o máximo 97.

A causa é a ÂNCORA da progressão geométrica. Ela parte do **fim do bloco
raso** — `n_raso+2, n_raso+4, n_raso+8, n_raso+16` — e com `n_raso ≈ 12` isso
põe as posições "profundas" em **14, 16, 20 e 28**, de níveis que vão até
~256. O bloco cobre ~10% da profundidade real. **Ele é profundo em POSIÇÃO DE
PÁGINA e raso em TEMPO:** para um filme que recebe centenas de reviews por
semana, a página 28 ainda é deste mês.

As duas exceções medidas (`cats-2019`, 97 dias; `im-still-here-2024`, 80)
confirmam o mecanismo em vez de contrariá-lo: são filmes de fluxo baixo, onde
28 páginas atravessam meses porque cada página cobre mais tempo.

**É o quarto caso do mesmo padrão neste projeto** — um parâmetro que ninguém
classificou como parâmetro. O `50/20/30` era o número de degraus de estrela
vezes 10; o teto por NÍVEL contra a cota por BUCKET era mistura de unidades; a
ordem de consumo da seleção virou critério de coorte sem que ninguém a
escolhesse; e agora a âncora da progressão. Nos quatro, o valor não estava
errado: ele nunca tinha sido decidido.

**Por que a alternativa não serve.** A saída barata seria não recoletar e
declarar a recência como escolha ("a análise cobre as reviews mais recentes").
Ela não alinha os dois canais, e a razão é uma propriedade do dado: **o
histograma não é recortável no tempo.** O endpoint do Letterboxd devolve o
acumulado da vida do filme e não existe versão temporal dele. Declarar a
recência congelaria permanentemente um parágrafo em que o rótulo de peso fala
de 2012-2026 e a frequência de tema fala de 6 semanas — não corrigido, só
confessado. Como a única metade ajustável é a da amostra, é ela que tem de se
mover.

**Por que agora, e por que esta é a última sessão da camada de coleta.**
Posicionamento é o último parâmetro que o superset (§3[B']) não torna
reversível — página não baixada não está em disco. A 35 filmes a recoleta
custa ~1,5 h; a 150 filmes, ~6 h. Depois desta versão, toda decisão restante
do projeto é de ANÁLISE, aplicável sobre o bruto sem uma requisição.

##### Sondagem de profundidade — POR FILME, não por nível

A âncora nova exige saber a profundidade real, que o HTML não informa (gate da
v1.9.1: não há numeração de página). A sondagem é **por filme**:

1. **sondar o nível mais populoso** do histograma, por escada geométrica
   (`SONDA_ESCADA = (4, 16, 64, 256)`) seguida de refinamento binário de no
   máximo `SONDA_MAX_REFINAMENTO = 3` passos, dentro do último intervalo
   `(última não-vazia, primeira vazia)`;
2. **escalar os demais níveis pela proporção do histograma** —
   `prof(L) = round(prof_sondada × hist(L) / hist(L_sondado))`, com piso 1 e
   teto `TETO_PLATAFORMA_PAGINAS = 256`.

**O passo 2 é um PROXY, e entra na spec com esse rótulo.** O histograma conta
NOTAS; a paginação conta REVIEWS COM TEXTO. É a mesma aproximação que §3[C1]
já usa para alocar vagas, e o registro é o mesmo: nada garante que a razão
texto/nota seja igual entre níveis. A defesa não é que o proxy acerte — é que
**errar sai barato**, porque o mecanismo de descoberta da v1.9.2 já trata
posição estimada que volta vazia: ela revela a profundidade real por
monotonicidade e o orçamento sobrante é redistribuído para o intervalo
confirmado, **reusando `redistribuir_deficit`**. Nenhum segundo caminho é
escrito.

**Custo:** 4 requisições no caso comum (filme popular, os quatro degraus da
escada não-vazios → profundidade = teto de plataforma, sem refinamento); até
7 no pior caso. A Sessão C já havia estabelecido os dois extremos: 256 é teto
de PLATAFORMA para listagem populosa, e filme obscuro esgota organicamente
muito antes (`the-room-1993`, 890 notas, 4 páginas).

Quando a escada inteira volta vazia — ou a sondagem falha por rede —
`profundidade_sondada` fica `None` e o posicionamento **degrada para o
comportamento da v1.9.2**, registrado em telemetria. Nenhuma coleta é
bloqueada por uma sondagem que não deu certo.

##### Reancoragem: frações da profundidade, não incrementos do bloco raso

```
posições profundas = [round(f × profundidade(L)) para f em FRACOES_PROFUNDIDADE]
FRACOES_PROFUNDIDADE = (0,25 · 0,50 · 0,75 · 0,95)
```

tomadas as `n_profundo` primeiras, deduplicadas, e sempre `> n_raso`.

**`RESERVA_PROFUNDIDADE` (25%) e o orçamento de páginas por bucket não mudam.
O que muda é ONDE as páginas caem, não QUANTAS.** Essa é a premissa central do
desenho e o teste que a prova compara, nível a nível, o número de páginas
buscadas antes e depois — igualdade exata.

Degenerados, todos com comportamento nomeado:

- **profundidade ≤ `n_raso`** — o bloco profundo se fundiria ao raso; nenhuma
  posição profunda é emitida e o nível degrada para consecutivo puro. É o
  resultado correto para filme obscuro: não há profundidade a alcançar;
- **profundidade menor que o número de posições pedidas** — as frações
  colidem, a deduplicação as reduz, e o orçamento restante volta ao bloco raso
  pelo mecanismo já existente;
- **profundidade desconhecida** — comportamento v1.9.2 (progressão geométrica
  a partir do fim do bloco raso);
- **nível zerado no histograma** — recebe profundidade 1 pelo piso; na
  prática não recebe orçamento de página (§3[B], alocação), então a questão
  não chega a se colocar.

##### Telemetria (`meta.json`)

`profundidade_sondagem`: `{nivel_sondado, profundidade, exata, requisicoes,
motivo}` e `profundidade_estimada_por_nivel` — `{nível: páginas}`, o que a
âncora usou. Sem esses dois campos, "por que a página 137 foi buscada" é
irrespondível a partir do bruto.

#### Extensão de orçamento por DÉFICIT (v1.9.4)

**O defeito que corrige.** A diagnose da v1.9.3 (registrada em §3[H]) achou
uma classe, não um caso: **10 buckets DOMINANTES abaixo da cota**, dos quais
9 são filmes muito populares (1,4M-5,7M notas) com rendimento pós-filtro de
10-20%. Em **4 deles** (`wicked-2024`, `avengers-endgame`, `talk-to-me-2022`,
`aftersun`) o bucket dominante — o que abre o MOVIMENTO 3 e carrega o rótulo
de peso mais forte — tem `n` **MENOR** que os outros dois buckets do mesmo
filme: a perspectiva majoritária medida com menos precisão que a minoritária.

O mecanismo é uma **interação entre duas decisões válidas isoladamente**: a
alocação proporcional ao histograma (§3[C1]) concentra o orçamento de páginas
nos níveis mais populosos, e `MIN_CHARS` filtra pior justamente esses níveis,
porque reação de massa é curta. A redistribuição de déficit (§3[C1]) não
socorre: ela pressupõe SOBRA em algum nível do bucket, e aqui o bucket inteiro
rende mal ao mesmo tempo (`deficit_redistribuido = 0` no caso medido).

**Por que corrigir agora, e não depois.** O orçamento de páginas é o **único**
parâmetro da camada de coleta que o superset (§3[B']) não torna reversível —
página não baixada não está em disco, e nenhum parâmetro downstream a traz de
volta. Com 35 filmes, corrigir custa ~20 minutos de recoleta incremental;
com mais 100 filmes coletados sob o orçamento antigo, custa horas. E o gate de
taxonomia mediu, por nulo de permutação, que a margem de lift de 15 pp só é
defensável na cota de 40 (a 20 reviews por bucket, ~2/3 dos pares que cruzam a
margem cruzariam por acaso) — déficit no bucket dominante degrada exatamente
a comparação ENTRE buckets, que é a tese do produto.

**A regra — OBSERVACIONAL, e é isso que a define:**

1. Gastar o orçamento base do bucket (`ORCAMENTO_PAGINAS_POR_BUCKET = 16`),
   **exatamente como hoje**, com o mesmo posicionamento estratificado.
2. Se, ao fim do orçamento base, o total de reviews **VÁLIDAS** do bucket for
   menor que a meta com folga (`cota × FOLGA_ALVO_COLETA` = 40 × 1,25 = 50),
   conceder páginas extras **UMA A UMA**, até `TETO_EXTENSAO_PAGINAS = 24`
   (+8 sobre a base), alocadas aos níveis **em déficit**.
3. Parar no teto ou ao atingir a meta, o que vier primeiro.

O bucket que rende bem para em 16 exatamente como antes — a extensão nunca
dispara para ele, e o custo dos filmes que já fechavam a cota é **zero**. O
bucket que rende mal ganha até 8 páginas extras.

**Por que observacional e NÃO preditivo.** A saída óbvia seria estimar o
rendimento de cada nível pelas páginas já baixadas e comprar páginas onde o
rendimento previsto compensa. Está rejeitada, por duas razões:

- **as páginas não são uma amostra do mesmo regime.** Desde a v1.9.2 elas são
  log-espaçadas em profundidade (bloco raso consecutivo + bloco profundo
  geométrico). O rendimento do bloco raso de um blockbuster mede reação de
  massa em semana de estreia; o do bloco profundo mede outra coorte, outro
  tamanho de texto, outro rendimento. Um estimador ajustado no primeiro não
  descreve o segundo;
- **um preditor ruidoso decidindo orçamento é uma peça nova com modo de falha
  próprio** — e esta spec já pagou esse preço uma vez: a parada por ALVO
  (v1.9.0) era exatamente isso, uma heurística otimista decidindo quando
  parar, e foi removida na v1.9.2 por não-determinismo depois de causar o
  37/40 de `cidade-de-deus`. Reintroduzir estimativa na mesma decisão, dois
  releases depois de tê-la removido dali, seria repetir o erro com outro nome.

A regra acima **não estima nada**. Todo número que ela consulta já foi medido:
quantas válidas o bucket tem AGORA (contadas sobre o bruto em disco, pelo
mesmo `_cascade_pool` da seleção), e quais níveis estão abaixo do próprio
alvo. Nenhum parâmetro de calibração novo é introduzido: `TETO_EXTENSAO_PAGINAS`
é um teto de custo, não um limiar ajustável de qualidade, e a meta com folga
reusa `FOLGA_ALVO_COLETA`, que já existe.

**Alocação das extras — QUARTO uso de `redistribuir_deficit`, nenhum mecanismo
novo.** A cada página concedida, o plano de gasto das extras restantes é
recalculado:

```
deficit(L)   = max(0, alvo_com_folga(L) − válidas_atuais(L))
plano        = alocar_bucket(extras_restantes, deficit, níveis_vivos, piso=0)
plano_final  = redistribuir_deficit(plano, {L: extras_restantes se L vivo senão 0})
```

e a página vai para o nível com maior alocação no plano (desempate pelo nível
mais alto, o mesmo de `_maior_resto`). "Nível vivo" é o que ainda não devolveu
página vazia. São as MESMAS duas funções que já alocam reviews entre níveis
(§3[C1]), páginas entre níveis (v1.9.1) e posições dentro de um nível
(v1.9.2) — agora extras entre níveis. Quatro usos, uma implementação.

**Peso por DÉFICIT, não por histograma — e a escolha é deliberada.** Todos os
outros usos de `alocar_bucket` pesam pelo histograma. Aqui não: pesar as
extras pelo histograma daria todas elas ao mesmo nível populoso de baixo
rendimento que a diagnose identificou como o amplificador do problema —
repetiria a concentração em vez de corrigi-la. O déficit é **medido**, não
estimado, e é o que a extensão existe para fechar.

**Onde as páginas extras caem, posicionalmente.** Não recalculam a divisão
raso/profundo — isso mudaria as posições geométricas e faria a base deixar de
ser um prefixo da coleta estendida. Elas são **anexadas**, nesta ordem:

1. posições ainda não buscadas **dentro do intervalo já confirmado** (`≤` a
   maior posição buscada com sucesso). Por monotonicidade da paginação, essas
   páginas **têm conteúdo garantido** — toda extra gasta ali rende;
2. esgotadas essas, posições consecutivas **além** da mais profunda já
   buscada. Aqui uma página pode vir vazia, e vir vazia marca o nível como
   `material_esgotado` para o resto da extensão.

**O teto é POR EXECUÇÃO, não pela vida do bruto — limitação declarada.** A
contabilidade posicional (`posicoes_buscadas`, `maior_confirmada`) vive no
resultado da raspagem, não no `meta.json`, então uma segunda execução do mesmo
filme reconstrói o estado a partir do orçamento BASE e volta a ter 8 extras
disponíveis. Consequências, ambas benignas mas reais: (a) o bruto de um filme
executado duas vezes pode acumular mais que 24 páginas num bucket; (b) a
segunda execução gasta parte das extras **em posições que a primeira já
buscou** — cacheadas, portanto sem custo de rede, mas também sem material
novo, o que aparece na telemetria como extras concedidas sem ganho de
válidas. Não é corrigido aqui: exigiria um registro posicional persistente, e
o checkpoint do lote (§3[H]) já evita a reexecução acidental. Quem reexecutar
um filme de propósito precisa saber disso.

**`--offline` não estende, e preserva a telemetria da coleta que houve.** A
reexecução 100% cache é uma garantia anterior a esta versão (README: "zero
rede, nunca falha"), e a extensão a quebrou: um filme coletado ANTES da
v1.9.4 pede, em `--offline`, uma página que nunca esteve no cache, e o
`FetchError` sobe pelo pipeline inteiro — observado ao vivo em `longlegs`,
página 9 do nível 2,0★. A guarda é explícita: com `fetcher.offline`, o gancho
devolve o `extensao_por_bucket` já gravado em disco, sem buscar nada. Não
devolver nada apagaria o registro (`persistir` SOBRESCREVE o meta) e devolver
zeros inventaria uma extensão que não aconteceu.

**Telemetria obrigatória, por bucket, em `meta.json` (`extensao_por_bucket`):**

| campo | significado |
|---|---|
| `paginas_base` | páginas com conteúdo gastas no orçamento base |
| `paginas_extensao` | extras efetivamente concedidas (0 quando não disparou) |
| `extras_por_nivel` | `{nível: extras}` — a quem foram |
| `motivo_parada` | `meta_atingida` \| `teto_extensao` \| `material_esgotado` |
| `n_validas_pos_base` | válidas do bucket ao fim da base |
| `n_validas_pos_extensao` | válidas do bucket ao fim da extensão |
| `meta` | a meta com folga usada (cota × 1,25) |

A extensão precisa ser **auditável**: "o bucket X recebeu N páginas de extensão
e parou por Y" tem de ser lido do `meta.json`, não reconstruído.

#### Correção e declaração são CAMADAS, não alternativas (v1.9.4)

O teto de 24 garante que **alguns buckets ainda não fecharão 40**. Isso é
esperado e **não é falha da extensão** — é a consequência de haver um teto de
custo, que é o que impede a extensão de virar paginação sem limite.

O registro explícito, para que nenhuma versão futura leia uma coisa como
substituta da outra:

- a **extensão** (§3[B], acima) encolhe a CLASSE de buckets sub-40 — ataca os
  casos em que o material existe e o orçamento é que acabou cedo;
- o **piso escalonado** (§3[C3]) e o **denominador visível** na interface
  absorvem o RESÍDUO — os casos em que o material simplesmente não está lá,
  ou está atrás de mais páginas do que o teto autoriza.

A declaração honesta continua sendo o mecanismo **final**, não a alternativa
rejeitada. Nenhuma quantidade de orçamento de páginas torna o piso escalonado
dispensável: sempre existirá filme obscuro (`obsession-2026`, 214 notas no
total) para o qual nenhum orçamento acha material que não existe. A extensão
muda **quantos** buckets caem no resíduo, nunca **se** o resíduo precisa ser
declarado.

#### Resultado MEDIDO da recoleta v1.9.4 (2026-08-08) — extensão por déficit

Recoleta SELETIVA dos 9 filmes da classe identificada pela diagnose
(`obsession-2026` fora: escassez genuína, mecanismo diferente). Incremental —
as páginas da base já estavam no cache do lote da v1.9.3, então o custo de
rede medido é o das páginas de EXTENSÃO e do completamento que elas geram.

| Filme | dom. | antes (n/m/p) | depois | extras (n/m/p) | motivo (n/m/p) | rede |
|---|---|---|---|---|---|---|
| `wicked-2024` | pos | 30/32/**20** | 36/40/**24** | 8/8/8 | teto/teto/teto | 26 |
| `avengers-endgame` | pos | 40/40/**34** | **40/40/40** | 3/3/8 | meta/meta/teto | 20 |
| `talk-to-me-2022` | pos | 28/24/**23** | 40/31/**34** | 8/8/8 | teto/teto/teto | 30 |
| `aftersun` | pos | 40/40/**38** | **40/40/40** | 0/0/8 | meta/meta/teto | 9 |
| `pearl-2022` | pos | 15/24/**30** | 26/33/**35** | 8/8/8 | teto/teto/teto | 27 |
| `parasite-2019` | pos | 28/40/**32** | **40/40/40** | 8/7/8 | teto/meta/teto | 32 |
| `wonka` | pos | 18/23/**32** | 32/25/**38** | 8/8/8 | teto/teto/teto | 25 |
| `hereditary` | pos | 28/31/**34** | 36/40/**39** | 8/8/8 | teto/teto/teto | 24 |
| `shutter-island` | pos | 30/36/**36** | **40/40/40** | 8/7/8 | teto/meta/teto | 29 |

**Agregado:** bucket dominante fechando a cota **0/9 → 4/9**; buckets abaixo
de 40 **22/27 → 12/27**; dominante MENOR que outro bucket do mesmo filme
**5 → 3**. Os 27 buckets em `estado_piso = completa` antes e depois.

**Custo:** 222 requisições nos 9 filmes (**24,7/filme**, contra ~78/filme de
uma coleta do zero), 603 servidas de cache, 551 s (~9 min).

**Rendimento das extras: 188 páginas concedidas → 225 válidas ganhas**, ~10%
do bruto (a ~12 reviews/página) — exatamente a faixa de 10-20% que a diagnose
mediu para esta classe. A extensão não descobriu material melhor; comprou
mais material do mesmo, que é tudo o que um desenho observacional promete.

**Motivos de parada: 21 `teto_extensao`, 6 `meta_atingida`, 0
`material_esgotado`.** Coerente com serem os filmes mais populares do
catálogo: nenhum chega perto de esgotar o Letterboxd.

**A seletividade é o que distingue isto de um aumento de orçamento.**
`aftersun` é o caso limpo: `negativas` e `medianas` fecharam a meta dentro da
base e receberam ZERO extras (9 requisições no filme inteiro); só `positivas`
estendeu. Um aumento de `ORCAMENTO_PAGINAS_POR_BUCKET` teria gasto 24 páginas
nos três.

**O que NÃO fechou, e por quê — resíduo esperado, não falha:**
- `wicked-2024`/positivas (20→24): 8 extras renderam +4 válidas (~4%), pior
  que os 6,9% da diagnose. Fechar 40 exigiria da ordem de 40-50 páginas no
  bucket. É o pior rendimento dos 35 filmes.
- `hereditary` **passou** a ter o dominante menor que outro bucket (39 contra
  40 em `medianas`) — efeito colateral da extensão ter ajudado mais
  `medianas`; diferença de 1 review, irrelevante para precisão (±7,9pp vs.
  ±8,0pp a 1 EP), mas registrada por honestidade.
- `talk-to-me-2022`/medianas (24→31): o bucket morno tem 2 níveis sob a opção
  C, então as extras se espalham por menos níveis e batem antes no material
  de baixo rendimento.

**Consequência de custo, medida:** a regra é POR BUCKET, então um filme
deficitário estende os três — até 24 páginas extras por filme, não 8. Nos 9
filmes: 188 extras, média 20,9/filme.

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

#### `dias_por_100_paginas` (v1.9.6) — métrica de PRIMEIRA CLASSE

Quanto **tempo** cada 100 páginas da listagem cobre. Calculada na COLETA e
gravada em `meta.json`, por filme e por nível — a v1.9.5 a calculou em
análise, ad-hoc, num script de sessão; ela sobe para o material persistido
porque é **o discriminador de qual estratégia cada filme precisa**, consultado
por esta versão (limiar da passada, §2.3) e pelas seguintes.

```
dias = mediana(data na página MAIS RASA) − mediana(data na página MAIS PROFUNDA)
dias_por_100_paginas = 100 × dias / (pagina_max − pagina_min)
paginas_para_1_ano   = 365 × (pagina_max − pagina_min) / dias      (None se dias == 0)
```

A mediana por página, e não a data de uma review, porque uma página tem ~12
reviews e a data de qualquer uma delas é o proxy contaminado de §3[B'] — a
mediana da página é robusta ao outlier que domina min/max.

**Ela usa `data` (data ASSISTIDA, proxy contaminado, §3[B']), e para ESTA
finalidade a contaminação importa pouco.** O que se mede é a **TAXA ao longo
das páginas**, não a data absoluta: a contaminação (usuário que registra hoje
uma sessão de anos atrás) é ruído aproximadamente uniforme sobre as posições,
então ela alarga a dispersão dentro de cada página sem inclinar
sistematicamente a diferença ENTRE páginas distantes. O uso proibido continua
proibido: "esta amostra cobre de X a Y" segue sendo afirmação sobre `data`
absoluta, e segue valendo a ressalva de §3[B'].

**Campos gravados** — `dias_por_100_paginas` (bloco do filme) e
`dias_por_100_paginas_por_nivel` (um bloco por nível, chave string como todo
mapa por nível do meta):
`{pagina_min, pagina_max, dias, dias_por_100_paginas, paginas_para_1_ano, n_paginas}`.

**Calculada sobre UMA ordenação de cada vez** — a da coleta base
(`ordenacao_usada`). Misturar as duas ordenações num só cálculo seria somar
posições que não significam a mesma coisa: página 3 sob `by/added` é a 3ª
adição mais recente, página 3 sob `by/added-earliest` é a 3ª mais antiga.

**Bordas nomeadas e testadas:** menos de 2 páginas distintas com data → `None`
(não há taxa a medir); todas as datas iguais → `dias = 0`,
`dias_por_100_paginas = 0.0` e `paginas_para_1_ano = None` (a taxa é
genuinamente zero, e "quantas páginas para um ano" não tem resposta finita —
`None` diz isso, `0` mentiria).

**Precisão limitada pelo alcance do bruto**, e o campo carrega o próprio
denominador (`pagina_min`, `pagina_max`) para que isso seja lido, não
suposto: um filme cujo bruto vai só até a página 12 estima a taxa sobre um
vão de 12 páginas, e extrapolar dela para 256 é extrapolação — declarada
aqui, não corrigida.

#### Duas ordenações no mesmo bruto (v1.9.6)

A passada de §2.3 é a primeira vez que um mesmo `dados/bruto/<slug>/` guarda
material de duas ordenações. Isso quebra duas coisas que eram implícitas
enquanto havia uma só, e as duas se resolvem no material persistido:

**(1) `pagina_origem` deixa de ter significado único.** Sob `by/added` ela é o
rank de adição decrescente (o instrumento temporal PRIMÁRIO, acima); sob
`by/added-earliest` a mesma página 1 é o material mais ANTIGO que existe. Sem
distinguir, `distribuicao_pagina_origem` e a estratificação da seleção
(§3[C2], faixas de profundidade) passariam a tratar reviews de 2012 como "a
faixa mais rasa/recente" — silenciosamente, e com o número parecendo certo.
Por isso `reviews.jsonl` ganha o campo **`ordenacao_origem`** (segmento de URL
sob o qual AQUELA review foi raspada).

É propriedade da review na mesma acepção de `pagina_origem` — *como ela foi
obtida*, nunca uma decisão de seleção —, então respeita o mesmo princípio que
mantém `passou_por_relaxamento` fora do bruto.

**Compatibilidade:** o campo tem default `None`, e `None` significa "coletada
antes do campo existir". A leitura correta de `None` é `meta["ordenacao_usada"]`
da coleta base — resolvida no consumo, **sem reescrever dado histórico com uma
inferência**. Isso exige que a passada NÃO sobrescreva `ordenacao_usada`, o
que nos leva ao segundo ponto.

**(2) `meta.json` não pode mais ser "a última execução".** A regra da v1.9.0 —
meta sobrescrito pela execução mais recente, reviews acumulando — funcionava
porque toda execução era da mesma natureza. Uma passada de 6 páginas por
bucket sob outra ordenação sobrescreveria `orcamento_paginas_por_nivel`
(que a seleção LÊ para achar a fronteira raso/profundo, §3[C2]),
`paginas_gastas_por_nivel`, `profundidade_sondagem` e `janela_temporal` da
coleta base — apagando a descrição da coleta que produziu 95% do material.

Regra da v1.9.6: **o corpo do `meta.json` continua descrevendo a coleta BASE**
(a de `by/added`), e toda passada entra como um item da lista **`passadas`**:

```json
"passadas": [{"ordenacao": "by/added-earliest", "coletado_em": "...",
              "versao_coletor": "...", "motivo": "dias_por_100_paginas=5.5 < 20",
              "orcamento_paginas_por_bucket": 6,
              "orcamento_paginas_por_nivel": {...}, "paginas_gastas_por_nivel": {...},
              "requisicoes": 71, "n_novas": 183, "n_atualizadas": 0,
              "retentativa": {...}}]
```

Uma passada repetida sob a MESMA ordenação substitui o item daquela ordenação
em vez de anexar um segundo — a lista descreve *ordenações presentes no
bruto*, não um log de execuções, e um log de execuções não é o que qualquer
consumidor precisa saber.

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
5. **Estratificação por profundidade dentro do nível (v1.9.5)** — ver abaixo.
   Ordem de escolha DENTRO de cada faixa: `(pagina_origem, ordem de aparição
   no jsonl)`, que é a ordem de amostragem da ordenação escolhida (§2.3).
   Determinística e reproduzível.

**Registrar por bucket** (§4): `n` final, **composição por nível** (alvo vs.
atingida), e **quantas reviews entraram por cada degrau da cascata**.

#### Estratificação da seleção por profundidade — E1 (v1.9.5)

**O defeito que corrige.** A seleção consumia o pool em ordem de
`(pagina_origem, ordem no jsonl)` e parava ao fechar a cota — então **recência
virou critério de seleção implícito**, escolhido por ninguém. Medido sobre os
35 filmes: das 1316 reviews profundas que sobreviviam ao filtro, só **716
(54,4%)** entravam na amostra; **600 ficavam em disco sem chegar ao produto**,
e 13 dos 105 buckets tinham material profundo e selecionavam ZERO dele.

**A regra.** O intervalo de `pagina_origem` de cada nível é dividido em três
faixas e a cota daquele nível é alocada entre elas:

```
faixa 1 = 1 .. ⌈n_raso/2⌉        (raso recente)
faixa 2 = ⌈n_raso/2⌉+1 .. n_raso  (raso)
faixa 3 = > n_raso                (profundo)
```

A divisão é **estrutural, não um tercil da distribuição observada**: a coleta
já produz dois blocos de naturezas diferentes — o raso é consecutivo e denso,
o profundo é esparso e cada página cobre muito mais tempo. Um tercil das
posições presentes daria faixas diferentes em cada filme, sem significado
comum entre eles.

A alocação entre faixas é `alocar_bucket` com pesos iguais seguida de
`redistribuir_deficit` com a contagem de cada faixa como disponibilidade —
**quinto uso da mesma função** (reviews entre níveis, páginas entre níveis,
posições dentro de um nível, extras da v1.9.4 entre níveis, agora vagas entre
faixas). Faixa vazia devolve suas vagas às outras automaticamente.

**Custo medido: ZERO.** Simulado sobre os 35 filmes antes de adotar — **0 de
105 buckets perdem uma única review**, porque o pool elegível (4906) é 24%
maior que a cota consumida (3948). O uso do material profundo sobe de 54,4%
para **86,2%**. O comprimento médio da amostra não muda (469 → 472 chars), e
o material profundo não tem perfil diferente do raso (147 contra 153 chars de
média, 78,5% contra 76,3% abaixo de `min_chars`, spoiler 2,6% contra 2,5%) —
não há interação com o filtro de comprimento a temer.

**Quando os dois critérios de estratificação competem, quem cede é este.**
Em 9% dos pares (bucket, nível) a cota do nível é menor que 3 e não cabe em
três faixas. Aí a estratificação por profundidade cede para a **alocação
proporcional por nível** (§3[C1]), e o comportamento é idêntico ao de antes da
v1.9.5. A ordem de precedência não é arbitrária: a alocação por nível carrega
uma garantia de representatividade que o histograma sustenta, enquanto a
estratificação por profundidade é preferência de cobertura.

**A estratificação depende do orçamento de páginas**, que é quem define
`n_raso`. `selecionar` passa a aceitar `orcamento_paginas_por_nivel` (lido do
`meta.json`); **sem ele, o comportamento é byte-idêntico ao da v1.9.4** — o
que mantém offline e testes antigos válidos e torna a estratificação uma
adição, não uma substituição.

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

**Decisão (usuário, pós-leitura da Entrega 2): manter `MIN_CHARS=150` e
`CASCATA_CHARS=[150, 50, 0]`.** Nenhum parâmetro alterado nem commitado
por causa desta auditoria — a simulação em 100 quase não mudou nada
(17/18 vs. 14/18) e a rung intermediária testada na Entrega 4 piorou um
bucket já deficitário; a leitura foi que 150 não é o defeito.

**Diagnose de acompanhamento (v1.9.3, pós-lote de 29 filmes) — bucket
DOMINANTE abaixo da cota, quando popularidade não é a causa.** Motivada
por `wicked-2024`/positivas: 76,2% do histograma, 2,8M notas, mas
`n_final=20` — volume não explica escassez. Diagnose sobre o bruto
persistido (`selecao.selecionar` reexecutado, zero rede):

- **H1 (rendimento extremo) — CONFIRMADA.** Rendimento pós-filtro por
  nível de `wicked-2024`/positivas comparado à mediana dos 35 filmes:
  nível 3,5★ = 8,3% (mediana 20,8%, **pior de 35**); 4,0★ = 6,9%
  (mediana 20,8%, **pior de 35**); 5,0★ = 10,0% (mediana 19,8%, 4º pior
  de 35); só 4,5★ fica perto da mediana (25,0% vs. 20,8%). Não é
  escassez de material — é rendimento pós-filtro anormalmente baixo em
  3 dos 4 níveis, contra o mesmo filtro que os outros 34 filmes
  atravessam melhor.
- **H2 (concentração da alocação) — fator AMPLIFICADOR, não causa
  isolada.** A alocação proporcional ao histograma concentra 35,0% do
  orçamento do bucket no nível 4,0★ e 32,5% no 5,0★ — exatamente os 2
  níveis com pior rendimento (6,9% e 10,0%). `deficit_redistribuido=0`:
  a redistribuição (§3[C1]) não teve de onde puxar excedente porque
  TODOS os níveis do bucket rendem mal ao mesmo tempo — o mecanismo que
  socorre um nível fraco com sobra de outro não tem sobra para dar
  quando o déficit é sistêmico ao bucket inteiro, não pontual a um
  nível.
- **H3 (profundidade insuficiente) — REFUTADA.** Zero páginas vazias:
  `paginas_gastas` == páginas distintas com review em todo nível do
  bucket. O orçamento de 16 páginas foi todo gasto em páginas com
  conteúdo real; a causa não é alcance, é filtro.
- **Distribuição de `n_chars` do bucket:** 52,6% abaixo de 50 chars,
  79,2% abaixo de 150 — mais pesado na cauda curta que a média geral dos
  6 filmes da auditoria anterior (74,3%), consistente com H1.

**Generalização (35 filmes) — não é só `wicked-2024`, é uma CLASSE.** 10
casos de bucket dominante abaixo da cota; excluindo `obsession-2026`
(escassez genuína — só 214 notas totais, mecanismo diferente), os outros
9 são TODOS filmes muito populares (1,4M-5,7M notas) com rendimento
10-20%: `talk-to-me-2022`, `pearl-2022`, `parasite-2019`, `wonka`,
`avengers-endgame`, `hereditary`, `shutter-island`, `aftersun`, além de
`wicked-2024`. **Isso reconcilia com o `r≈0,05-0,13` do relatório
agregado do lote** (que olhou os 105 buckets, dominantes e minoritários
juntos, e por isso diluiu o padrão) — filtrando só para o bucket
DOMINANTE de cada filme, o padrão aparece: filme muito popular tende a
render pior no bucket que concentra a maioria das notas, porque esse é o
bucket que mais atrai reação curta de massa. Share do histograma e
volume total de notas **não predizem** `n_final` olhando todos os
buckets juntos, mas prediz mal especificamente o bucket que mais precisa
de precisão (o dominante).

**Consequência para o produto.** Em **4 dos 35 filmes**
(`wicked-2024`, `avengers-endgame`, `talk-to-me-2022`, `aftersun` — os
mesmos 4 mais extremos da lista acima) **o bucket que abre o MOVIMENTO 3
e carrega o rótulo de peso mais forte tem `n` MENOR que os outros dois
buckets do mesmo filme** — a perspectiva majoritária é medida com MENOS
precisão que a minoritária, o oposto do que a intuição sugeriria. Não é
um defeito de honestidade (o piso escalonado e as invariantes de §D2
continuam corretos com qualquer `n`), mas é uma tensão real entre
"popular" e "bem-medido" que a narrativa não expõe ao leitor.

**Correção possível, NÃO aplicada — decisão do usuário.** O mecanismo
identificado é uma interação entre duas decisões independentes e válidas
isoladamente: alocação proporcional ao histograma (§3[C1], que concentra
orçamento nos níveis com mais notas) e `MIN_CHARS=150` (que filtra pior
justamente os níveis de blockbuster com reação de massa) — juntas,
sistematicamente subalocam páginas para o nível ERRADO quando os dois
efeitos coincidem no MESMO nível popular. Não corrigido nesta sessão,
por instrução explícita.

**CORRIGIDO na v1.9.4** pela extensão de orçamento por déficit (§3[B]) —
a correção é observacional, não preditiva, e não toca nenhuma das duas
decisões acima: `MIN_CHARS` e a alocação proporcional seguem idênticos; o
que muda é que um bucket que fecha o orçamento base abaixo da meta com
folga ganha até 8 páginas extras. Resultado medido em §3[B], "Resultado
MEDIDO da recoleta v1.9.4".

#### Proposta temporal (v1.9.6) — MEDIDA, não aplicada

Com as duas pontas em disco (§2.3), a seleção passa a ter uma escolha que
antes não existia: **quanto da cota vem de cada época**. Até aqui a pergunta
não fazia sentido — só havia uma época no bruto.

Três desenhos, simulados sobre os filmes que receberam a passada, sem aplicar
nenhum:

| | desenho | o que assume |
|---|---|---|
| **S1** | seleção ATUAL — ignora `ordenacao_origem`, consome o pool inteiro por `(pagina_origem, ordem no jsonl)` | que as duas pontas são intercambiáveis. **É o comportamento em vigor**, e a simulação existe para mostrar o que ele faz agora que o pool mudou |
| **S2** | cota dividida entre as pontas — 70% recente / 30% antigo | que a recepção recente é o objeto principal e a antiga é contexto |
| **S3** | proporcional ao volume de cada ponta no bruto | que o bruto já é a melhor evidência disponível sobre o peso de cada época |

**Resultado medido (12 filmes, 36 buckets):** os três fecham **36/36** buckets
na cota de 40, com `p5` mediano idêntico (2022-09-02) e comprimento médio
dentro de 5%. A cobertura NÃO decide entre eles. O que decide é a variação da
mistura por bucket:

| | S1 (atual) | S2 (70/30) | S3 (proporcional) |
|---|---:|---:|---:|
| antigas por bucket — mediana | 8,0 | 12,0 | 10,0 |
| antigas por bucket — faixa | **1 a 19** | 12 a 12 | 7 a 11 |
| antigas por bucket — desvio | **4,6** | 0,0 | 1,0 |
| buckets que deixam de fechar | 0 | 0 | 0 |

**RECOMENDAÇÃO: S2**, com a fração `70/30` entrando como parâmetro
ARBITRÁRIO declarado (mesma política de §3[C3] e de `LIMIAR_PASSADA_ANTIGA`).
S3 é mais elegante e perde por um motivo específico: a "proporção do bruto"
que ele segue **não é propriedade do filme**, é consequência do orçamento da
passada (18 páginas antigas contra 48 recentes) — dobrar esse orçamento mudaria
a composição da ANÁLISE sem ninguém decidir nada, que é a classe exata de
defeito que esta versão existe para não repetir.

**Ressalva medida:** em S2/S3 as pontas são selecionadas independentemente e
**não há redistribuição entre elas**; um bucket cujo pool antigo seja menor que
a cota não completa pela ponta recente. Não ocorreu nos 12 filmes (216 antigas
por filme, ~97 acima de `min_chars`, contra cota de 12), mas os 12 receberam o
orçamento inteiro — a redistribuição entre pontas é peça a implementar junto da
aplicação, não algo que a simulação validou.

**S1 não é o caso neutro que o nome sugere, e é o principal achado:**
a estratificação por faixas de profundidade (acima) ordena o pool por
`pagina_origem`, e sob `by/added-earliest` `pagina_origem = 1` é o material
**mais antigo**, não o mais recente. Sem consciência de `ordenacao_origem`, a
seleção atual classifica reviews de 2012 como "faixa 1" — a mais rasa/recente.
É o mesmo modo de falha que §2.3 e §3[B'] descrevem: um número que continua
parecendo certo depois que o significado por baixo dele mudou. **Medido:** sob
S1 a mistura varia de 1 a 19 antigas por bucket, e varia DENTRO do mesmo filme
— `the-substance` fica com 47,5% de material antigo em `medianas` e 5% em
`positivas`, no mesmo parágrafo de saída.

**Não aplicada nesta versão, por decisão explícita:** a mudança de seleção
entra junto do schema, para não invalidar a classificação de eixos que roda em
paralelo. O resultado da medição e a recomendação estão em `V196_ORDENACAO.md`.

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

> #### Guard-rail: nenhum caminho novo fala com o SDK do LLM direto (v1.9.4)
>
> **A reincidência que o motiva.** A v1.8.0 documentou e resolveu uma causa
> raiz: `deepseek-v4-*` tem *thinking* LIGADO por padrão, os tokens de
> raciocínio competem pelo MESMO orçamento de `max_tokens` que a resposta, e
> sem `thinking: {"type": "disabled"}` a resposta volta truncada ou vazia. A
> correção vive em `synthesize.deepseek_client_call` desde então — e mesmo
> assim o defeito voltou: o script do gate de taxonomia (2026-08-08) chamou a
> API direto, sem o parâmetro, e **8 de 12 chamadas voltaram com `content`
> vazio**. Não porque a lição estivesse perdida: porque um caminho novo não
> herda o que não usa.
>
> **Uma regra escrita não resolve isso.** "Nenhum script novo chama a API
> direto" falharia da mesma forma na próxima vez — a fase de síntese vai
> gerar mais scripts de medição, e cada um é uma chance de reintroduzir o
> mesmo bug. O padrão desta spec, aplicado desde a v1.2.3 (quantificador
> pré-computado em vez de instruído) e a v1.6.1 (checagem de existência em
> vez de comparação de string), é **lição vira mecanismo**.
>
> **O mecanismo:** `tests/test_guardrail_adaptador.py` varre `src/` e
> `scripts/` — a varredura inclui deliberadamente os scripts de análise e
> medição, que foi onde o defeito reapareceu — procurando import ou
> instanciação de SDK de LLM (`openai`/`OpenAI(`, `anthropic`,
> `google.genai`) e chamadas diretas de geração (`chat.completions.create`,
> `messages.create`, `models.generate_content`) fora do módulo adaptador
> (`src/espectro24/synthesize.py`). Qualquer ocorrência **falha o teste**, com
> o arquivo e a linha.
>
> **A allowlist é explícita e justificada, arquivo por arquivo.** Três scripts
> de diagnóstico anteriores (`diagnostico_fluencia.py`,
> `diagnostico_fluencia_v2.py`, `compare_models.py`) chamam o SDK direto de
> propósito: o `thinking_budget` e o modelo **são o objeto de estudo** deles —
> passar pelo adaptador, que fixa esses parâmetros, tornaria o experimento
> impossível. Eles estão numa constante literal no próprio teste, com o
> motivo escrito ao lado; adicionar um arquivo à allowlist é uma mudança
> deliberada e revisável, não um efeito colateral.
>
> **`tests/` fica FORA da varredura** — os testes importam o SDK para
> construir dublês e nunca fazem chamada real. A única exceção é a fixture do
> próprio guard-rail, que injeta uma violação sintética num arquivo temporário
> e confirma que a varredura a detecta: sem ela, um guard-rail que não
> detecta nada passaria como um que não tem nada a detectar.
>
> **O que o guard-rail NÃO garante.** Ele checa o CAMINHO, não os parâmetros:
> um chamador que use o adaptador está protegido; um que replique o transporte
> com outro nome de variável pode escapar da varredura textual. É uma rede de
> classe de regressão, no mesmo estatuto das checagens mecânicas do §E2 — cobre
> o modo de falha observado, não todo modo de falha concebível.

> #### Retentativa de TRANSPORTE em `resposta()` — o mesmo desenho do `Fetcher`, trazido do scraping para o LLM (v1.9.24)
>
> **O achado que motiva.** A v1.9.23 registrou, como observação fora de
> escopo: um `ServerError` transitório do Gemini abortou um lote de 35 filmes
> **no primeiro item**, obrigando a refazer a execução inteira. `synthesize.
> resposta()` — a função por onde passam as chamadas de LLM de narrador
> (§D2, produção) e veredito (§V, produção) — não tinha nenhuma retentativa
> de transporte, ao contrário do `Fetcher` (§2.4, desde a v1.9.6). Com 35
> filmes um 5xx custa uma reexecução; com os ~300 do plano de expansão de
> catálogo, um 5xx no filme 12 descartaria o lote inteiro — e o scraping roda
> a 2s por requisição sem paralelismo (§2), então refazer é caro em HORAS.
>
> **O desenho é o do Fetcher, deliberadamente, não um novo.** Só erro de
> TRANSPORTE retenta — a chamada não produziu resposta da API (timeout,
> falha de conexão), ou a API respondeu 5xx (o SERVIDOR sinalizando
> sobrecarga). Até `LLM_MAX_TENTATIVAS` (3) tentativas, com o MESMO backoff
> exponencial `2s · 4s` e jitter de ±25% do §2.4 — constantes SEPARADAS
> (`LLM_MAX_TENTATIVAS`/`LLM_BACKOFF_*` em `config.py`, mesmo valor hoje),
> porque scraping de HTML e API de LLM têm perfis de confiabilidade
> diferentes e acoplar as duas configs impediria ajustar uma sem a outra.
> **O que NUNCA retenta:** erro de conteúdo, autenticação, cota ou parâmetro
> inválido (4xx no DeepSeek: `RateLimitError`, `AuthenticationError`,
> `PermissionDeniedError`, `BadRequestError`, `NotFoundError`,
> `UnprocessableEntityError`; `ClientError` no Gemini, que cobre 400/401/403
> **e** 429 de cota) — esses são decisão do serviço sobre o pedido, retentar
> seria pressão, não recuperação de rede, e a spec proíbe pressão sobre
> serviço em qualquer camada (mesmo princípio do 403/`AntiBotError` do
> Fetcher). Exceção genérica (ex.: bug de parsing local) também não retenta.
>
> **Ponto ambíguo do SDK do Gemini, investigado e resolvido.** `google-genai`
> não embrulha erro de transporte cru quando chamado sem `HttpRetryOptions`
> (o caso deste projeto): sem essa opção, `retry_args` (`_api_client.py` do
> SDK) usa `stop_after_attempt(1)` e deixa `httpx.TimeoutException`/
> `httpx.ConnectError` subirem intactos, ao lado de `errors.ServerError`
> (5xx, tipado). Os dois entram na lista de transporte do Gemini; o
> `errors.ClientError` (4xx) fica de fora.
>
> **Divergência DELIBERADA do precedente — registrada, não escondida.** O
> Fetcher tem `PressaoDoSite`: um teto de 503 ABSORVIDOS **por lote** (acima
> do teto por-requisição), porque insistir além dele é pressão sobre o site
> (§2.4). Esse mecanismo depende de um objeto compartilhado passado a CADA
> chamada; nenhum chamador de `resposta()` hoje (narrador, veredito, scripts)
> recebe ou repassa um objeto assim, e criar um exigiria plumbing por todos
> eles — fora do escopo desta sessão. O teto por-chamada é o único freio
> aqui; um teto por-lote fica registrado como candidato de sessão futura, se
> a telemetria justificar.
>
> **Onde vive, e por que não é contornável.** Dentro de `resposta()`, no
> mesmo lugar que despacha por provider — não num invólucro por fora que um
> chamador (ou um script futuro) possa contornar chamando `deepseek_resposta`
> /`_gemini_resposta` direto. Esgotadas as tentativas, levanta
> `LLMTransportError` (subclasse de `LLMError`) encadeando o erro original.
> Testado com a mesma técnica de `tests/test_publicar_catalogo.py`
> (`test_a_guarda_roda_dentro_de_cmd_publicar`): chamar `resposta()` — o
> caminho real de produção — e confirmar que o transporte é invocado mais de
> uma vez pela MESMA chamada.
>
> **O que este item NÃO cobria, e a v1.9.25 corrigiu.** `resposta()` é só
> UMA das duas portas de entrada do adaptador. A síntese por bucket (§D,
> `synthesize_bucket`) entra pela outra — `client_call` — e nunca passa por
> `resposta()`, então a v1.9.24 **não a cobria**: um 5xx na síntese continuava
> descartando o lote inteiro, e o pré-requisito de expansão seguia aberto. A
> instrução daquela sessão ("a retentativa vive dentro de `resposta()`,
> valendo para todo estágio de uma vez") presumia um ponto de estrangulamento
> único que não existia; a lacuna foi reportada em vez de o escopo ser
> estendido por conta própria. Ver a subseção seguinte.

> #### A retentativa desce para o TRANSPORTE, e o Gemini para de ter dois (v1.9.25)
>
> **O mapa que a v1.9.24 não tinha.** O adaptador tinha **quatro** pontos de
> contato com o SDK, não dois:
>
> | função | alcançada por | coberta pela v1.9.24? |
> |---|---|---|
> | `deepseek_resposta` | `resposta()` **e** `_deepseek_call` | só via `resposta()` |
> | `_gemini_resposta` | só `resposta()` | sim |
> | `_gemini_call` | só `gemini_client_call*` | **não** — transporte PRÓPRIO |
> | `anthropic_client_call` | só `anthropic_client_call*` | não (fora de `resposta()`) |
>
> **A correção: a retentativa desce um nível.** Sai de `resposta()` e passa a
> viver em `deepseek_resposta` e `_gemini_resposta` — as duas funções que
> efetivamente falam com o SDK —, numa implementação única
> (`_com_retentativa`). As camadas de cima HERDAM. Colocá-la no ponto mais
> baixo é o que torna "uma implementação, todas as camadas" verdadeiro em vez
> de aspiracional: ninguém pode contorná-la sem falar com o SDK direto, que é
> exatamente o que o guard-rail de §3[D] já proíbe. **Classificação de erro,
> teto, backoff, jitter e telemetria são os da v1.9.24, sem redecisão — só
> mudaram de lugar.**
>
> **`_gemini_call` passa a DELEGAR.** Ele duplicava o transporte inteiro
> (`genai.Client` próprio + `generate_content` próprio) em vez de delegar,
> como `_deepseek_call` sempre fez. A duplicata era EXATA: verificado por
> diff de AST que os corpos só diferiam em devolver `resp.text` em vez da
> resposta inteira, e em grafar a checagem de chave inline em vez de chamar
> `_exigir_chave` — e verificado **em runtime** que as duas levantam
> `LLMError` com mensagem byte-idêntica (`GEMINI_API_KEY não definida no
> ambiente.`), de modo que a delegação não troca comportamento nenhum, nem no
> caminho de chave ausente, que tem teste próprio. `thinking_budget` é
> repassado EXPLICITAMENTE, sem cair no default de `_gemini_resposta`, com
> teste que confirma o valor chegando inalterado ao SDK. **Pontos de contato
> com o SDK: 4 → 3**, travado por teste.
>
> **Razão de uniformizar em vez de retentar em três lugares** (decisão do
> dono do projeto, registrada): manter três implementações contraria o "uma
> implementação" da entrega e repete a dívida que a v1.9.4 (transporte
> reimplementado por script novo) e a extração de `quantificador.py` (mapa em
> duas cópias) já pagaram. Cobrir só o DeepSeek fecharia o pré-requisito
> apenas enquanto ninguém rodasse `--provider gemini` — é fechar por acidente
> de configuração, não por desenho.
>
> **Ausência de aninhamento é testada, não presumida.** Retentativa nos dois
> níveis produziria `LLM_MAX_TENTATIVAS²` chamadas. Os testes atravessam as
> duas portas de entrada e contam o SDK FALSO — o único lugar onde o
> aninhamento apareceria — exigindo exatamente `LLM_MAX_TENTATIVAS`.
>
> **O terceiro ponto de contato, registrado e NÃO consertado:**
> `anthropic_client_call` continua sem retentativa. Não é código morto — é
> alcançável por `--provider anthropic` e por ter só `ANTHROPIC_API_KEY` no
> ambiente (via `detect_provider`), incluindo a variante de prosa —, mas não
> está em nenhum default de produção (`PROVIDER_POR_ESTAGIO` só tem
> `deepseek`/`gemini`) e `resposta()` o rejeita. Lacuna conhecida, deixada
> deliberadamente para uma sessão futura.

> #### A retentativa dos scripts de classificação: MEDIDA, depois removida (v1.9.25)
>
> **Medição ANTES de mexer, sobre 37.300 chamadas reais** (os JSONL de
> `resultado/taxonomia-10/` e `resultado/votacao-3/`):
>
> | | |
> |---|---|
> | falhas permanentes (`ok: False`) | **0** |
> | retentativas (`tentativas > 1`) | **8** (0,021%), todas resolvidas na 2ª |
> | classes de exceção absorvidas | **irrecuperáveis** |
>
> A terceira linha é achado por si: o campo `erro` só era gravado quando o
> laço ESGOTAVA; no sucesso a classe da exceção era descartada. O laço
> absorvia sem deixar rastro do QUE absorvia — 8 eventos de classe
> desconhecida por construção.
>
> **O ALCANCE exato do que foi medido — para não ser mal lido depois.** As
> 37.300 chamadas são **100% DeepSeek**, do estágio de CLASSIFICAÇÃO
> (`classificar_10`/`gate_taxonomia`/`votacao_3`), que já rodava com o laço
> local há sessões. **Não existe histórico equivalente para o Gemini** — o
> provider do incidente que abriu esta sessão (§ anterior, "o achado que
> motiva") nunca teve um script de medição de massa como este. **0,021% de
> retentativa não é uma medida da taxa de falha do Gemini, nem da síntese
> de bucket, nem de nada fora da classificação DeepSeek** — é a taxa de UM
> transporte, sob UM provider, medida por um script que já absorvia a
> falha antes de qualquer coisa nesta sessão existir.
>
> **A retentativa NÃO é conserto de falha frequente — é seguro contra
> evento raro e caro.** Uma taxa de 0,021% não torna a retentativa
> desnecessária: o que a motiva não é a frequência, é o CUSTO de perder o
> evento raro. Com 35 filmes, um 5xx no primeiro item custa refazer a
> execução inteira; com os ~300 do plano de expansão, um 5xx no filme 12
> descarta o lote inteiro — e o scraping roda a 2s por requisição sem
> paralelismo (§2), então refazer é caro em HORAS, não em centavos. Um
> evento que acontece 1 vez em 5000 e custa horas quando acontece vale a
> retentativa mesmo que a medição disponível (de um provider e um estágio
> diferentes do incidente) mostre uma taxa baixíssima. Ler "0,021%" daqui a
> algumas versões como "a retentativa era desnecessária" seria comparar a
> taxa medida no lugar ERRADO com o risco que motivou a sessão.
>
> **O anti-padrão, e onde estava.** `for tentativa in range(MAX_TENTATIVAS):
> try: ... except Exception: time.sleep(2*(tentativa+1))`, com `json.loads` e
> `_normalizar` DENTRO do `try` — então conteúdo malformado repetia a chamada
> de API. Estava em **oito** scripts, não nos três reportados na v1.9.24:
> `classificar_10`, `gate_taxonomia`, `votacao_3`, `auditoria_acuracia`,
> `inspecao_assistir`, `variante_impacto_estrito`, `variantes_prompt_curtas`,
> `verificador_impacto`.
>
> **A interação que forçou a decisão:** com a retentativa descendo para
> `deepseek_resposta`, esses laços passariam a envolver um transporte que já
> retenta — **3 × 3 = 9 chamadas** por review, com backoffs somados (~30s
> contra 6s), em 37 mil chamadas sob concorrência 8.
>
> **O que foi feito: laço removido, REGISTRO mantido.** O `except` que grava
> `ok: False` fica — sem ele, `list(pool.map(tarefa, ...))` re-levantaria e
> uma única review malformada em 8.171 abortaria o lote. O que sai é a
> repetição. Consequências: erro de conteúdo passa a custar **1 chamada em
> vez de 3**; o transporte é retentado uma vez só, com backoff exponencial e
> jitter em vez de linear; e a taxa passa a ser IMPRESSA no fim de cada lote
> (falhas `ok: False` + retentativas do adaptador), porque todo consumidor faz
> `if not r.get("ok"): continue` e uma taxa alta somiria entre milhares de
> registros. O campo `tentativas` foi removido dos registros — ninguém o lia
> (verificado), e depois desta versão ele seria uma meia-verdade.
>
> **Dependência de absorção, verificada:** os consumidores pulam `ok: False`
> e o resume só marca `ok: True` como feito, então um registro falho é
> retentado na EXECUÇÃO seguinte. É por isso que o `except` de registro não
> pôde simplesmente sumir — a absorção sustenta o lote longo; o que não se
> sustentava era a REPETIÇÃO silenciosa.
>
> **`comparar_narrador.py` é exceção deliberada e MANTÉM seu laço.** Ele não
> é o anti-padrão: não tem `except` nenhum dentro do laço (transporte propaga
> na hora, para o `try` de fora, que registra e passa ao PRÓXIMO candidato) e
> retenta por EXTRAÇÃO VAZIA, que é qualidade de conteúdo, não transporte.
> Congelado por teste, para não ser "consertado" por engano nem copiado como
> padrão.
>
> **Guard-rail estrutural:** um teste varre os oito scripts procurando
> chamada de LLM dentro de um laço de CONTAGEM (`for _ in range(...)`) cujo
> `except` não re-levanta. O discriminador é deliberado — um laço sobre
> COLEÇÃO com `try` por item é o padrão normal de lote (a exceção passa ao
> item seguinte, não refaz o mesmo); só o laço sobre `range()` em volta da
> mesma chamada é retentativa. Com fixture que injeta o laço removido e
> confirma que a varredura o detecta.
>
> **A remoção do laço foi provada por COMPORTAMENTO em 3 dos 8 scripts, e
> por `import` nos outros 5 — a assimetria é DECIDIDA, não descoberta por
> acidente.** `classificar_10.py`, `votacao_3.py` e `gate_taxonomia.py` têm
> teste de ponta a ponta com SDK falso (`tests/test_contrato_falha_lote_
> classificacao.py`) exercitando as quatro propriedades do contrato de
> falha JUNTAS, no mesmo lote: erro de conteúdo custa 1 chamada; o item vira
> `ok: False`; o lote não aborta; o resume retenta o item falho. São os TRÊS
> que rodam sobre a AMOSTRA DE PRODUÇÃO real (a classificação que alimenta
> `taxonomia_id`, calibrada contra gabarito humano) — o risco de um defeito
> silencioso ali é alto e o custo de prová-lo é baixo.
>
> `auditoria_acuracia.py`, `inspecao_assistir.py`,
> `variante_impacto_estrito.py`, `variantes_prompt_curtas.py` e
> `verificador_impacto.py` têm só a prova estrutural do guard-rail acima
> (a varredura AST) mais `import` bem-sucedido depois da transformação —
> prova de PARSE, não de contrato. São scripts de ANÁLISE e EXPERIMENTO,
> arquivados ou usados uma vez para uma medição já registrada em outra
> parte da spec (`variante_impacto_estrito.py`/`variantes_prompt_curtas.py`
> alimentaram a promoção da regra `A_regra`, §3[D] "razão PAREADA"), fora
> do caminho que roda de novo a cada expansão de catálogo — o mesmo
> critério de proporcionalidade que já rege o resto do projeto (ex.: os três
> scripts na ALLOWLIST do guard-rail de SDK, isentos por serem objeto de
> estudo, não caminho de produção). `import` é a prova PROPORCIONAL ao risco
> deles; escrever o mesmo harness de ponta a ponta para os 5 gastaria tempo
> de sessão num lugar que não paga por si.

> #### `load_dotenv` como efeito colateral de produção — dívida conhecida, não corrigida (v1.9.25)
>
> **O que é.** Os oito scripts que a Entrega 2 tocou chamam `from dotenv
> import load_dotenv; load_dotenv(RAIZ / ".env")` de DENTRO da função de
> classificação — não uma vez no import do módulo, mas TODA VEZ que a
> função roda. `load_dotenv` escreve direto em `os.environ`, fora do
> controle de qualquer coisa que não seja o próprio processo. Pontos de
> chamada (linha da chamada, não do `import`):
>
> | script | linha(s) |
> |---|---|
> | `classificar_10.py` | 266 (`classificar`) |
> | `votacao_3.py` | 117 (`classificar_passe`) |
> | `gate_taxonomia.py` | 312, 427, 504 (`classificar`, e as duas etapas de famílias/triagem) |
> | `auditoria_acuracia.py` | 615 |
> | `inspecao_assistir.py` | 124 |
> | `variante_impacto_estrito.py` | 245 |
> | `variantes_prompt_curtas.py` | 326 |
> | `verificador_impacto.py` | 261, 833 |
>
> **Por que é propriedade de PRODUÇÃO, não só ruído de teste.** Qualquer
> processo Python que importe um destes módulos e chame a função de
> classificação ganha, como efeito colateral não pedido, todo par
> chave=valor do `.env` local injetado no próprio ambiente — inclusive um
> processo que já tinha decidido explicitamente NÃO usar aquela chave (ex.:
> `--provider` explícito, ou um teste com SDK falso que não deveria
> precisar de credencial nenhuma). Foi assim que a suíte vazou
> `DEEPSEEK_API_KEY`/`GEMINI_API_KEY` reais para `test_provider.py` ao
> escrever o teste de contrato de falha desta sessão — o sintoma apareceu
> num arquivo SEM relação nenhuma com classificação, porque `os.environ` é
> global ao processo.
>
> **Por que NÃO foi corrigido nesta sessão.** É comportamento PRÉ-EXISTENTE
> — nenhuma das mudanças de v1.9.24/v1.9.25 o introduziu — e mexer nele
> (mover o `load_dotenv` para fora da função, ou trocar por injeção
> explícita de configuração) é uma decisão sobre como scripts de linha de
> comando carregam credencial, ortogonal ao objeto desta sessão
> (retentativa de transporte). Está fora do escopo declarado.
>
> **A contenção que existe é NO TESTE, não no código de produção.**
> `tests/test_contrato_falha_lote_classificacao.py` tem um fixture autouse
> (`_conter_o_efeito_colateral_de_producao_do_load_dotenv`) que bloqueia
> `dotenv.load_dotenv` antes de qualquer chamada às funções de
> classificação — nomeado e documentado explicitamente como contenção de um
> efeito colateral de PRODUÇÃO, não como configuração do teste, para que
> não seja removido "por limpeza" numa sessão futura sem que quem remove
> entenda que o vazamento volta em silêncio.

> #### Telemetria de retentativa do LLM: atravessa o PROCESSO e chega ao relatório de lote (v1.9.25)
>
> **O obstáculo real, que não era onde parecia.** A v1.9.24 deixou
> `telemetria_retentativa_llm()` sem consumidor. Conectá-la não é escolher um
> relatório: o harness de lote (§3[H]) roda o CLI como **SUBPROCESSO**
> (`subprocess.run([... "-m", "espectro24.cli" ...])`), então o contador de
> módulo vive no processo FILHO e morre com ele. Nenhum import resolve isso.
>
> **O menor canal que já existe: `stderr`.** O log de publicação já captura
> `stderr_tail`. O CLI passa a imprimir uma linha ao lado da que já existia
> (`Requisições de rede nesta execução: N`); `publicar_um` a extrai para um
> campo próprio (`retentativa_llm`) no `publicacao_log.jsonl`; e
> `--relatorio` agrega o LOTE. Nada por filme (a esmagadora maioria é zero,
> seria ruído), nada em `render.py`, nada na interface, nenhum JSON de filme
> tocado.
>
> **Formato e parser vivem JUNTOS** (`linha_telemetria_llm` /
> `parse_linha_telemetria_llm`, ambos em `synthesize`), pela mesma razão que
> levou o mapa de quantificador a virar `quantificador.py` na v1.9.21: duas
> metades do mesmo contrato em arquivos diferentes divergem. Teste de ida e
> volta cobre o contrato.
>
> **`None` é "não sei", e não vira zero.** Filme publicado antes da v1.9.25,
> ou execução que morreu antes do fim, não tem a linha. O relatório conta
> esses à parte (`N sem telemetria`) em vez de somá-los como zero
> retentativas — somar maquiaria a taxa exatamente no caso em que ela
> importa.

> #### Prever o efeito de trocar o prompt de classificação: razão PAREADA, nunca extrapolação de teto (v1.9.7)
>
> **O erro que motiva.** Antes de reclassificar o corpus sob a variante
> `A_regra` (2026-08-13), duas previsões foram feitas sobre como as
> frequências por eixo mudariam. A que entrou no relatório da sessão
> anterior era `observado × precisão_antiga / recall_antigo` — uma
> extrapolação de TETO: "qual seria a frequência se o prompt ANTIGO tivesse
> recall perfeito". Ela previu `expectativa` subindo **2,02×**. A
> reclassificação real mediu **0,75×** — não só a magnitude, a DIREÇÃO
> estava errada.
>
> **Por que ela não podia funcionar.** A extrapolação de teto estima a
> frequência VERDADEIRA do corpus. É uma quantidade legítima, mas responde
> outra pergunta: ela não sabe nada sobre o prompt NOVO, que tem erros
> próprios e diferentes. Usá-la como previsão equivale a supor que o prompt
> novo acerta tudo — o que nenhum prompt faz.
>
> **O preditor certo já existia na mesma sessão**, na validação pareada de
> variantes (`resultado/auditoria-acuracia/variantes/comparacao.json`):
>
> ```
> fator = (recall_novo / precisão_nova) / (recall_antigo / precisão_antiga)
> ```
>
> A frequência observada sob um prompt é ≈ `freq_verdadeira × recall ÷
> precisão`. A frequência verdadeira é propriedade das REVIEWS, não do
> classificador — é a mesma sob os dois prompts, então **cancela na razão** e
> sobra só a diferença de comportamento entre eles. É exatamente a
> quantidade que se quer, e ela dispensa estimar a mais difícil.
>
> **O mecanismo:** `src/espectro24/previsao_frequencia.py`
> (`fator_pareado`, `prever_frequencias`, `acuracia_da_previsao`), com
> `tests/test_previsao_frequencia.py`. Não é nota escrita: é função, com as
> bordas tratadas (precisão zero, recall antigo zero e medida ausente
> devolvem `None` com motivo, nunca número inventado) e com o caso histórico
> travado em teste.
>
> **Resultado medido do preditor, honesto:** sobre os 10 eixos, **10 de 10**
> ficaram dentro de 25% do fator real e houve **1 erro direcional de
> consequência** (`comparacoes`: previsto 1,05×, real 0,92×). Os dois
> movimentos grandes foram acertados — `impacto_emocional` para cima
> (1,95× previsto, 1,64× real) e `expectativa` para baixo (0,79× / 0,75×),
> justamente o que a extrapolação de teto errava. *(Correção de registro: o
> relatório da sessão da promoção afirmou "acerta o sinal em 9 dos 10
> eixos". Sob a definição limpa de sinal que `acuracia_da_previsao` aplica —
> com faixa morta de ±0,05 para não contar ruído como erro — o número é
> **6 de 10**, porque 3 eixos tiveram fator previsto exatamente 1,00 contra
> movimentos reais pequenos de 0,93–1,03. O "9 de 10" contava esses três
> como acerto sem critério declarado. O que se sustenta é o par acima:
> 10/10 em ordem de grandeza e 1 erro direcional real.)*
>
> **Pré-requisito, e é ele que decide a aplicabilidade.** Precisão e recall
> dos DOIS prompts medidos contra o MESMO gabarito humano, no mesmo conjunto
> de reviews. Sem esse par, o módulo não se aplica — e a saída NÃO é voltar
> à extrapolação de teto, que já está registrada aqui como preditor errado:
> é medir o par primeiro.
>
> **O que o preditor NÃO modela.** Competição entre eixos. Na promoção de
> `A_regra`, **40% das reviews que perderam `expectativa` ganharam
> `impacto_emocional` no mesmo texto** — o sinal migrou para um eixo mais
> específico quando os dois disputavam a mesma frase. Nenhum preditor por
> eixo isolado enxerga isso, e é a explicação de por que a magnitude erra
> mais que a direção.

> #### Provider por ESTÁGIO — DeepSeek classifica, Gemini narra (v1.9.8)
>
> **A decisão.** O provider deixa de ser global e passa a ser configuração
> **por estágio do pipeline**: `PROVIDER_POR_ESTAGIO` em `config.py`, com
> `classificacao` e `narrativa` resolvidos independentemente. `--provider`
> continua existindo e, quando passado, força TODOS os estágios — é o
> override manual, não o caminho normal.
>
> **Por que a classificação NÃO migra.** Ela está calibrada e auditada
> contra um gabarito humano de 100 reviews, com precisão e recall medidos
> por eixo (`CLASSIFICACAO_CONSOLIDADO.md`). **[v1.9.34] O gabarito vive em
> `resultado/auditoria-acuracia/leitura.md`, e a TRILHA das duas correções
> que o produziram está versionada ao lado, em `leitura.md.bak-0` e
> `.bak-1`** (`.bak-0` → `.bak-1` → vigente; o que se move entre eles é
> `impacto_emocional`, 32 reviews de diferença entre o primeiro snapshot e o
> atual — a correção de `CLASSIFICACAO_CONSOLIDADO.md` §5). **Não recrie um
> snapshot solto na raiz do repositório:** a trilha já existe, e uma segunda
> cópia do gabarito permanente num caminho mais visível que o real passa a
> ter aparência de régua aplicada sem ser — o cenário que o docstring de
> `scripts/corrigir_gabarito.py` existe para evitar. Trocar o modelo ali invalida
> oito sessões de medição de uma vez: o `taxonomia_id` não muda (ele
> hasheia prompt + eixos, não o modelo), então a troca seria **silenciosa**
> — o pior tipo. É tarefa estruturada, alto volume, saída JSON curta: o
> lugar onde capacidade de modelo rende menos.
>
> **Por que a narrativa migra.** É o oposto em todos os eixos: uma chamada
> por filme (volume irrelevante), saída em prosa longa, e nada calibrado a
> invalidar — a qualidade é julgada por leitura humana, não por métrica
> contra gabarito. É exatamente onde capacidade de modelo vira qualidade
> percebida.
>
> **O risco histórico, e por que ele está neutralizado.** O Gemini foi o
> provider original do projeto e saiu por duas razões: teto de 20
> requisições/dia no free tier (resolvido — a chave atual tem billing) e
> uma auditoria que o flagrou **inflando contagens** (dizia 35 onde a
> contagem humana era ~30). Esse segundo risco é neutralizado **por
> construção, não por confiança**: sob o briefing determinístico (§D2) o
> narrador não computa nenhum número — todos vêm prontos — e a checagem de
> conjunto de tokens numéricos (§E2) já reprova qualquer número que ele
> invente. A defesa não depende do provider ser bem-comportado.
>
> **Consequência para o adaptador.** `deepseek_resposta`/`deepseek_uso`
> eram específicos e foi essa lacuna que fez um script reimplementar o
> transporte e reintroduzir um bug conhecido (v1.9.4). A generalização
> (`resposta`/`uso`, despachadas por provider) fecha o mesmo buraco para o
> Gemini ANTES que ele apareça. O guard-rail do CI cobre os dois SDKs.

> #### Instrução não remove o que a distribuição do material impõe — a saída é arquitetura (v1.9.7)
>
> **O padrão, com as ocorrências que o sustentam.** Quando um defeito vem do
> MATERIAL (o que as reviews de fato dizem, na proporção em que dizem) e não
> do texto do prompt, adicionar ou apertar instrução no prompt tende a
> falhar — porque não muda a distribuição, só pede ao modelo para lutar
> contra ela numa única chamada. A correção que funciona é de ARQUITETURA
> (mover a decisão para outro lugar — código, um estágio separado, um passe
> de verificação) ou de ACEITAÇÃO DECLARADA (registrar o limite, não
> escondê-lo atrás de mais uma regra).
>
> **Duas ocorrências anteriores no projeto, ambas já resolvidas por
> arquitetura, não por instrução:**
> 1. **Inflação de quantificador retórico, síntese §D2 (v1.2.2 → v1.2.3).**
>    A v1.2.2 tentou calibrar por INSTRUÇÃO — pedir ao LLM que calculasse a
>    fração e escolhesse o rótulo por uma tabela dada no prompt. Reduziu mas
>    **reincidiu**: na primeira regeneração pós-fix, "quase todos" foi
>    aplicado a frações de 65-70% duas vezes. A v1.2.3 moveu a decisão para
>    o CÓDIGO — o rótulo é pré-computado e o LLM só o usa, não o escolhe —
>    e o modo de falha fechou. Mesmo princípio da v1.1.1 (denominador
>    `n_reviews_analisadas` sempre carimbado pelo código, nunca pelo LLM).
> 2. **Empilhar honestidade e fluência num prompt só, narrador §D2 (v1.5.0
>    → v1.6.0).** A v1.5.0 tentou prescrever ritmo e registro por instrução,
>    em cima do acúmulo de invariantes de honestidade já presentes no prompt — as regras de
>    ritmo não transferiram entre filmes e a configuração de produção chegou
>    a publicar uma frase agramatical. A v1.6.0 separou em DOIS ESTÁGIOS: o
>    narrador podado a UMA responsabilidade (dizer a verdade), e um editor
>    novo (§E2) para ritmo, sem acesso a fato nenhum e sem poder alterar
>    número/rótulo/atribuição — trechos protegidos + verificação mecânica.
>
> **Uma tentativa fora do projeto, abandonada:** o experimento local com
> Ollama/Qwen3.5-9B (`experimentos-ollama-arquivado/`) tentou sustentar as
> ~18 invariantes do narrador numa única chamada de modelo pequeno — não
> sustentou, e o caminho foi abandonado em favor de API (Gemini/Anthropic/
> DeepSeek), não de mais instrução sobre o modelo local.
>
> **Três ocorrências nesta sessão** (classificação de 10 eixos,
> `CLASSIFICACAO_CONSOLIDADO.md` §5), todas atacando a saturação de
> `impacto_emocional` (75,5% do corpus) por INSTRUÇÃO, todas refutadas por
> medição:
> - **`B_fewshot`** (exemplos de review curta resolvidos no prompt) —
>   ancorou o modelo e degradou review longa (recall 401-800: 0,888→0,847).
> - **Lift normalizado** (reponderar a métrica de contraste em vez de
>   reponderar o que entra na contagem) — amplifica o quantum de ruído
>   exatamente no regime saturado; nenhuma das três variantes testadas
>   (L1/L2/L3) atinge cobertura ≥18/35 filmes com ruído ≤35%.
> - **Definição apertada** (proibir veredicto seco em dois pontos do
>   prompt) — nos 13 casos que o gabarito humano corrigido desmarcou, o
>   modelo deixou de marcar em só 3, e adicionou marcação errada em 2 onde
>   o prompt original acertava. Instrução explícita, repetida, ignorada na
>   maioria dos casos.
>
> **O que diferencia as duas classes.** Nos dois casos resolvidos (1, 2), o
> defeito estava em uma regra sobre FORMA DA SAÍDA (rótulo, ritmo) — algo
> que o código PODE decidir sozinho, porque a resposta certa é computável a
> partir do dado já disponível. Nas três tentativas desta sessão, o defeito
> está em JULGAMENTO DE CONTEÚDO (esta frase é ou não é `impacto_emocional`)
> — o código não tem como decidir isso sozinho, então a arquitetura que
> resolveria não é "mover para o código", é um SEGUNDO PASSE que audite o
> primeiro contra a régua (`REGRA_ANOTACAO.md`).
>
> **QUARTA OCORRÊNCIA, e a primeira que CONFIRMA a saída (2026-08-14).** O
> segundo passe foi construído e medido (`scripts/verificador_impacto.py`,
> `CLASSIFICACAO_CONSOLIDADO.md` §5b): estágio separado, rodando após o
> consenso, pergunta binária e local, sem reapresentar a taxonomia. Levou a
> precisão de `impacto_emocional` de **0,486 para 0,794** com queda de
> recall de 0,921 para 0,711 — e a combinação `A_regra` + verificador
> **domina o prompt antigo nos dois eixos** (micro geral P 0,895/R 0,741
> contra P 0,858/R 0,715). O padrão se fecha: mudar QUEM DECIDE funcionou
> onde três formulações de instrução ao mesmo decisor falharam.
>
> **Dois detalhes de desenho que a medição isolou, e que valem para o
> próximo passe de verificação que este projeto escrever:**
> - **Procedimento vence regra declarativa.** Duas variantes do verificador
>   foram testadas com a MESMA régua. A que só declarava (confirma isto,
>   remove aquilo) cortou demais — 49 remoções, 69% de acerto, perda de
>   recall MAIOR que o ganho de precisão, reprovada. A que transformava a
>   régua em PROCEDIMENTO — identificar o ALVO da frase num campo
>   estruturado ANTES de decidir — fez 38 remoções com 79% de acerto e
>   passou. Forçar o compromisso com o passo intermediário, em campo
>   próprio da saída, é o que separou as duas.
> - **Verificar é mais estável que classificar, medido.** A classificação
>   precisou de votação de 3 (26,5% de reprodutibilidade em passada única).
>   O verificador tem **88,9%** — passada única basta, e o custo cai a um
>   terço. Não presumir: medir, porque a tarefa mais simples pode dispensar
>   o mecanismo que a difícil exigiu.
>
> **O que este padrão NÃO diz.** Não diz que toda instrução falha — as 7
> regras de `A_regra` (§ correção de recall em review curta) SÃO instrução,
> e funcionaram, medido. A diferença é que ali a instrução mudava um
> CRITÉRIO DE DECISÃO bem definido (brevidade não é ausência), e aqui as
> três tentativas pediam para o modelo SUPRIMIR um comportamento que parece
> vir de um prior mais profundo do modelo pré-treinado (associar veredicto
> a `impacto_emocional`) — instrução muda critério, não sempre suprime prior.

> **CORREÇÃO DA PROJEÇÃO DE LIFT (Entrega 4 do verificador, 2026-08-22).** A
> projeção de lift que acompanhou a medição de 2026-08-14
> (`verificador/projecao.json`) foi calculada ANTES da correção de margem da
> v1.9.15, e herdou os dois defeitos que aquela versão consertou no caminho
> de produção:
>
> 1. **Comparação em float.** `variante_impacto_estrito._projetar_lift`
>    compara `lift >= m` sobre `float`, reproduzindo o mesmo `0.2 >= 0.2`
>    falso em binário que fez 5 filmes caírem fora da margem por engano. A
>    base contra a qual a projeção se comparava era **13/35**; sob `>=`
>    exato sempre foram **18/35**. A projeção anunciava "de 13/35 para
>    15/35" — um ganho medido contra uma régua torta.
> 2. **Uma única amostra.** O modelo de remoção é estocástico (cada
>    marcação cai com probabilidade `1 - fator`), mas a projeção sorteava
>    UMA vez. Para uma pergunta binária por filme ("o veredito de contraste
>    vira?") um sorteio só não tem incerteza declarada.
>
> A projeção corrigida (`verificador_impacto.py projetar-exato`) usa
> `espectro24.eixos.acima_da_margem`/`contraste` — a mesma fonte de verdade
> do caminho de produção, `Fraction` do começo ao fim — e roda 2000
> sorteios, reportando a FRAÇÃO de sorteios em que cada veredito vira, em
> vez de um ponto. A projeção antiga fica no disco como registro do que foi
> medido quando; ela não é reescrita.
>
> **O achado material da correção (medido, 2000 sorteios).** A projeção
> antiga anunciava um GANHO de cobertura de contraste ("13/35 → 15/35").
> Contra a base certa não há ganho: **18/35 → mediana 17/35, IC95 [16, 19]**
> sob `V2_alvo/passe1` — o intervalo contém a base, então a leitura honesta
> é **nenhuma mudança detectável**, com estimativa pontual levemente para
> baixo. Sob `V1_regua` a mediana cai a 16/35 (IC95 [16, 18]), encostando na
> base pelo topo. O "ganho" registrado em 2026-08-14 era artefato da régua
> torta, nas duas pontas: base errada E direção errada.
>
> Isso REFORÇA a conclusão que a sessão anterior já tinha registrado — a
> saturação de `impacto_emocional` não era a causa da fraqueza do lift. E
> acrescenta o sinal que faltava: o eixo saturado estava, se algo,
> CARREGANDO cobertura de contraste, não a suprimindo. O caso para adotar o
> verificador é de PRECISÃO, e ele se paga com (no máximo) um filme de
> cobertura — trade-off explícito, não um ganho em duas frentes.
>
> **A de-saturação em si funciona como previsto:** `impacto_emocional` sai
> de **75,6%** para **35,7%** projetados (V2/passe1), entrando na faixa dos
> outros nove eixos (13,7% a 55,9%, mediana 28,5%) — deixa de ser o outlier
> saturado. E o veredito de contraste dos três filmes no ar é **estável**:
> `cure` e `the-invite-2026` não viram em nenhum dos 2000 sorteios,
> `cidade-de-deus` vira em 0,6%. Adotar o verificador não obriga a
> republicar os três por mudança de veredito.
>
> **ADOTADO em produção (v1.9.16, 2026-08-22) — decisão do dono do projeto.**
> `V2_alvo`, passada única, sem votação. O racional que decide, registrado
> porque a troca é real e não deve ficar implícita: **é precisão comprada
> com recall.** Um falso positivo publica um bullet que descreve um efeito
> que a review não relatou e infla um denominador visível — quebra o
> princípio central do produto, "o código soma, ninguém inventa" (`eixos.py`,
> cabeçalho): o número aparece verificável e não é. Um falso negativo deixa
> de mostrar um tema — perda silenciosa e conservadora, o produto **diz
> menos** em vez de **dizer errado**. Entre as duas, para este produto,
> precisão vale mais.
>
> **Integração ao pipeline (`pipeline._carregar_consenso_producao`,
> `scripts/verificador_impacto.py aplicar-producao`).** O passe roda como
> estágio À PARTE, depois do consenso de votação e antes de `montar_eixos`,
> sobre TODA review em que `impacto_emocional` está no consenso — não só a
> amostra de 100 do gabarito. Escreve `resultado/votacao-3/consenso_verificado.jsonl`
> (mesmo schema do `consenso.jsonl` cru, só `eixos` muda) e um manifesto com
> a telemetria declarada (veredito + frase + alvo por review, checkpoint/
> resume) — o padrão de auditoria que já vale para as outras verificações do
> projeto. `consenso.jsonl` cru **nunca é sobrescrito**: `estender_classificacao_producao.py`
> e as ferramentas de auditoria da classificação continuam lendo ele.
>
> `montar_eixos` sem `consenso=` explícito passa a preferir o verificado
> quando ele existe — é a adoção, não uma alternativa que o código escolhe
> às cegas — e GRAVA a declaração no bloco publicado (`bloco["verificador"]`:
> variante, passada, `n_removidas_no_corpus` — nome que deixa explícito
> o escopo GLOBAL do número, depois de um susto ao publicar: o campo
> chamado só `n_removidas` no bloco de `cure.json` levaria um leitor a
> pensar que 1654 marcações saíram só de `cure`), no mesmo estatuto aditivo de
> `fonte_classificacao`: a chave só existe quando o passe rodou, e sua
> ausência num JSON antigo é a verdade sobre aquele artefato, não um default
> silencioso. **Guarda de atualidade, não fallback silencioso:** se
> `consenso.jsonl` cresceu depois da verificação (nova votação, novo filme
> classificado), `montar_eixos` RECUSA com erro explícito em vez de publicar
> sob um verificado que ficou para trás — a mistura silenciosa entre
> classificação com e sem V2 é exatamente o que esta guarda existe para
> impedir.
>
> **APLICADO ao corpus inteiro (Entrega 2, medido, não projetado).** 3162
> das 4181 reviews classificadas dos 35 filmes (75,6%), passada única,
> `scripts/verificador_impacto.py aplicar-producao`: **1654 removidas
> (52,3%)** — quase o mesmo número que a amostra de 100 do gabarito previa
> (V2/passe1: 38/72, 52,8%), o sinal de que a amostra generalizou. Frequência
> de `impacto_emocional` no corpus: **75,6% → 36,1%** (a projeção da Entrega
> 4 anterior tinha estimado 35,7% — a 0,4pp de diferença). Custo real **US$
> 0,1558** (a projeção tinha estimado US$ 0,10 — 56% acima, ainda
> irrelevante em termos absolutos).
>
> **Cobertura de contraste: 18/35 → 18/35, TOTAL INALTERADO** — dentro do
> IC95 [16, 19] que a projeção previu, e melhor que a mediana projetada
> (17/35). Mas o total esconde dois vereditos que MUDARAM em sentidos
> opostos e se cancelam: `eighth-grade` (valorativo → tematico, 38
> removidas) e `napoleon-2023` (tematico → valorativo, 43 removidas) — nenhum
> dos dois no catálogo dos 3 publicados, então nenhum republica por este
> achado; ambos entram sob a classificação verificada quando publicados
> (Entrega 4).
>
> **Os 3 filmes publicados: vereditos estáveis**, como a projeção previa —
> `cure` (tematico, 56 removidas), `cidade-de-deus` (valorativo, 82
> removidas), `the-invite-2026` (tematico, 76 removidas). Republicar muda os
> BULLETS (frequências menores em `impacto_emocional` reordenam a seleção de
> consenso e de contraste), não o estado.

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

> #### BRIEFING DETERMINÍSTICO — o código decide O QUE dizer, o narrador só VERBALIZA (v1.9.8)
>
> **O que muda.** Até a v1.9.7 o narrador fazia duas coisas ao mesmo tempo:
> SELECIONAR o que dizer (quais temas, em que ordem, com que ênfase) e
> ESCREVER, segurando ~18 invariantes de instrução simultaneamente. A
> v1.9.8 separa as duas: `briefing.montar_briefing(output)` produz, em
> CÓDIGO, um documento com todas as decisões já tomadas, e o narrador
> recebe um prompt que só pede prosa.
>
> **Por que, e por que agora.** É a terceira aplicação do padrão registrado
> em §3[D] ("Instrução não remove o que a distribuição do material impõe —
> a saída é arquitetura"). As duas anteriores: v1.2.3 (rótulo de
> quantificador movido para o código, depois de a calibração por instrução
> reincidir) e v1.6.0 (narrador e editor separados em dois estágios, depois
> de empilhar honestidade e fluência num prompt só falhar). A v1.9.7 fechou
> o padrão com uma quarta ocorrência e a primeira confirmação de saída (o
> passe de verificação de `impacto_emocional`). Aqui o mesmo princípio se
> aplica ao narrador: **toda invariante que pode ser resolvida por código
> deixa de ser instrução.**
>
> **O que o briefing carrega, tudo pré-computado:**
> - ficha do filme (TMDB: premissa, diretor, gênero, ano, duração);
> - temas por bucket com contagem e fração, **já ordenados** e **já
>   cortados** no número que o movimento 3 deve usar;
> - `rotulo_peso` por bucket, derivado do histograma;
> - **a ordem de apresentação do movimento 3**, como lista explícita —
>   antes era a instrução "comece pela perspectiva de MAIOR peso";
> - o `quantificador` verbal de cada tema, por faixa percentual;
> - o **orçamento de frases** de cada movimento;
> - o `estado_piso` de cada bucket **traduzido em permissão** — o que pode e
>   o que não pode ser dito sobre aquele grupo, em vez de o narrador ter de
>   inferir isso de `modo=sem_analise`;
> - a `marcacao_perspectiva` exigida por grupo.
>
> **O que continua sendo instrução, e por quê.** Nem toda invariante é
> computável. Continuam no prompt: anti-spoiler, proibição de importar fato
> externo, tom neutro do movimento 2, respeito à minoria, e o vocabulário
> "notas, nunca reviews". Essas são regras sobre COMO ESCREVER uma frase
> que o código não tem como pré-decidir sem escrever a frase ele mesmo. A
> medida de sucesso da entrega é quantas SAÍRAM, não zero.
>
> **O que o narrador continua NÃO podendo fazer:** escolher tema, computar
> número, decidir ordem. Toda quantificação que aparece na prosa vem do
> briefing — mesma autoridade do código sobre número que vale desde a
> v1.1.1 (denominador) e v1.2.3 (quantificador).
>
> **Compatibilidade.** O caminho antigo (`_serialize_output_for_narrator` +
> `build_narrator_prompt`) permanece no módulo e continua testado: a
> comparação entre os dois é o que justifica a troca, e apagar o anterior
> tornaria a regressão impossível de medir.

> #### TIQUES DE PROSA — o que a verificação mecânica não via (v1.9.9)
>
> A v1.9.8 fechou o briefing determinístico e mediu 4 modelos × 3 filmes
> com verificação mecânica (`resultado/comparacao-narrador/`). A LEITURA
> HUMANA dos 12 textos achou três defeitos que **nenhuma** flag pegou —
> todos os três invisíveis por construção, e cada um com uma causa
> identificada no CÓDIGO, não no modelo.
>
> **(1) O tique do quantificador.** Em `cure`, os QUATRO modelos escrevem
> "muitos" 8 vezes no mesmo texto ("muitos enfatizam… muitos valorizam…
> muitos ressaltam… muitos apontam…"). A causa não é o modelo: o briefing
> entrega o quantificador como **string única pré-computada** por tema
> (`escreva a frequência como: "muitos"`), e o modelo obedece
> literalmente, tema a tema. A instrução estava certa; a repetição é o
> comportamento CORRETO diante de um briefing que manda repetir.
>
> Correção, preservando o princípio de que o código é a autoridade sobre
> NÚMERO: o briefing passa a entregar, por tema, a **faixa** (`faixa`,
> chave estável) e o **conjunto de construções equivalentes** daquela
> faixa (`FAIXAS_QUANTIFICADOR`). O código continua decidindo a faixa — o
> que é a afirmação sobre o dado; o modelo escolhe a construção — o que é
> escolha de palavra. É a mesma fronteira de §3[D]: o que é computável
> vira dado, o que é prosa fica com quem escreve prosa.
>
> **Os conjuntos não se sobrepõem entre faixas, e isso é a invariante.**
> "cerca de metade" não pode estar no conjunto de "quase todos" — a faixa
> continua sendo verdade sobre o dado, e uma construção que pertença a
> duas faixas destruiria a checagem. Há teste que verifica a disjunção de
> todos os conjuntos, e teste que verifica que nenhuma construção de uma
> faixa é substring de uma construção de faixa vizinha.
>
> Duas checagens mecânicas novas, ambas em `qualidade.py`:
> - `quantificador_fora_de_faixa` — toda construção quantificadora
>   presente no texto tem de pertencer a uma faixa que o briefing
>   REALMENTE atribuiu a algum tema. Substitui a comparação literal por
>   uma comparação de PERTENCIMENTO, que é o que a invariante sempre quis
>   dizer;
> - `quantificador_repetido` — nenhuma construção pode aparecer mais de
>   `QUANT_MAX_REPETICOES` (= 2) vezes no texto. É a checagem que teria
>   pego o defeito, e a razão de ela não existir antes é que a repetição
>   nunca foi violação de nenhuma regra: era obediência.
>
> **Detalhe que a implementação obriga:** o `rotulo_peso` de cada grupo
> (§3[G]) compartilha vocabulário com as construções ("a maioria", "boa
> parte") e é literal obrigatório. Antes de contar construções, as
> ocorrências dos rótulos de peso do briefing são REMOVIDAS do texto —
> senão o texto seria punido por escrever exatamente o que o briefing
> mandou escrever.
>
> **(2) Estrutura de parágrafo.** `gemini-3.1-pro` entregou os 3 filmes
> num bloco único de até 318 palavras, sem uma quebra de linha. Zero
> flags: `formato_invalido` (v1.7.2) checa se a prosa veio embrulhada em
> JSON ou markdown, não se ela é legível.
>
> `paragrafos_insuficientes` e `paragrafo_longo` passam a ser flags. O
> mínimo **não é uma constante**: é o número de movimentos com orçamento
> maior que zero — 3 com ficha, 2 sem ela. Derivar do briefing evita o
> caso em que o narrador é reprovado por obedecer à instrução de pular o
> movimento 1. O teto por parágrafo é `MAX_PALAVRAS_PARAGRAFO` (= 180).
>
> **(3) Orçamento do movimento 2 — DIAGNÓSTICO ANTES DA CORREÇÃO.**
> O movimento 2 encolheu em todos os modelos (em
> `gemini-3.7-flash`/`cure`, uma única frase). Três causas eram possíveis
> — orçamento, material, prompt — e a correção de cada uma é diferente.
> **A medição descarta o orçamento e aponta o material, mas não a
> escassez dele: a truncagem.**
>
> - **Não é o orçamento.** Ele é `(0, 5)` frases e NENHUM modelo chegou
>   perto do teto em nenhum dos 3 filmes. Um limite que ninguém encosta
>   não é o que está limitando; aumentá-lo produziria enchimento, que é
>   exatamente o que a regra de omissão autorizada da v1.4.1 existe para
>   impedir.
> - **Não é o prompt.** A regra diz "se menos de duas propriedades
>   servirem, este movimento fica com UMA frase". Em `cure`, o modelo
>   escreveu uma frase — ele estava OBEDECENDO, e corretamente.
> - **É a truncagem, e ela é do movimento 3.** O único material do
>   movimento 2 é a lista de temas, e ela chega ao narrador já cortada em
>   `MAX_TEMAS_POR_GRUPO = 3`, corte definido para o movimento 3
>   ("priorize os 2-3 temas mais fortes"). O movimento 2 precisa de
>   propriedade DESCRITIVA presente em MAIS DE UM grupo — e é exatamente
>   nos postos médios que ela mora. Medido em `cure`: dentro do top-3,
>   a única propriedade compartilhada pelos três grupos é o RITMO
>   ("ritmo lento e tedioso" / "ritmo lento e confusão narrativa" /
>   "pacing lento e deliberado") — uma só, o que dispara a regra de uma
>   frase. Na lista COMPLETA aparecem mais duas: a ATMOSFERA
>   (`medianas` #4, `positivas` #1) e a AMBIGUIDADE DO FINAL
>   (`medianas` #2, `positivas` #6). Ambas caem no corte. Em
>   `cidade-de-deus`, a montagem/estilo visual só sobrevive porque está
>   em #2 e #1; o correspondente em `negativas` ("montagem frenética")
>   é #6 e cai.
>
> **Correção: separar o material do movimento 2 do corte do movimento 3.**
> O briefing ganha uma seção `movimento2.material` com **todos** os temas
> de **todos** os grupos, marcados com o grupo de origem, **sem
> frequência e sem quantificador**, e com escopo explícito: serve só para
> localizar propriedade descritiva compartilhada; é PROIBIDO usá-la para
> acrescentar tema ao movimento 3. O orçamento de frases **não muda** —
> `(0, 5)`, com o mínimo em zero, porque omitir continua sendo o
> comportamento correto quando o consenso descritivo não existe.
>
> **O que NÃO migra para o código, e por quê.** Decidir quais temas
> "compartilham o mesmo núcleo factual" é casamento SEMÂNTICO entre
> rótulos escritos em português por outro estágio ("ritmo lento e
> tedioso" ≡ "pacing lento e deliberado"). O código não resolve isso sem
> um segundo LLM julgando, e o projeto não põe LLM para julgar prosa. A
> invariante permanece onde §D2 já a registrava, em
> `INVARIANTES_REMANESCENTES` ("critério de categoria do MOVIMENTO 2") —
> o que muda é que o material deixa de chegar mutilado.
>
> **(4) Best-of-3 com seleção POR CÓDIGO.** Três narrativas independentes
> por filme; escolha mecânica, em `selecao_narrativa.py`. Eliminatório:
> todas as flags limpas. Entre as limpas, ordena por (a) clichê da
> blocklist, (b) repetição de construção quantificadora, (c) variância do
> comprimento de frase — PROXY DECLARADO de ritmo, pela hipótese de que
> texto com frases todas do mesmo tamanho lê como lista, e (d) cobertura
> dos temas do briefing. **Fallback obrigatório:** se nenhuma das 3
> passar limpa, seleciona a de menor severidade e faz retry DIRECIONADO
> só nas frases infratoras — descartar as três seria jogar fora prosa boa
> por causa de uma frase.
>
> **Os proxies são calibrados contra leitura humana antes de valer.** As
> 3 narrativas de um filme são apresentadas ao dono do projeto SEM
> indicação de qual o código escolheu, e a preferência dele é comparada
> com a escolha automática (`resultado/best-of-3/calibracao.md`).
> Registro honesto: poucos casos NÃO provam que os proxies estão certos;
> provam, no máximo, que não estão obviamente errados. Um desacordo é
> resultado publicável — significa que o proxy mede outra coisa.
>
> **(5) Gate do editor [E2] — PREPARADO, não decidido.** As narrativas
> finais dos 3 filmes são geradas sob briefing determinístico +
> best-of-3 e **sem passar pelo editor**, para leitura. Se o ritmo se
> sustentar sem ele, o E2 é aposentado (código arquivado, no padrão de
> `experimentos-ollama-arquivado/`) — deletar o estágio deleta todas as
> suas classes de falha de uma vez (4 tentativas descartadas em `cure`,
> parágrafo de opinião inventado, inversão de movimentos). Se faltar
> ritmo, a alternativa já decidida é reescopar o editor por MOVIMENTO
> (3 blocos), o que torna inversão de ordem impossível POR CONSTRUÇÃO.
> Esta versão **não** aposenta nem reescopa nada: só produz o material
> da decisão.
> #### FECHAMENTO DO NARRADOR — cobertura estrutural, parágrafo por grupo, editor aposentado (v1.9.10)
>
> Esta sessão fecha o ciclo de correções da v1.9.9: conserta o proxy de
> cobertura ANTES de ele decidir alguma escolha (a calibração já tinha
> registrado o defeito, sem corrigi-lo), fecha o ponto fraco que a leitura
> apontou em `cidade-de-deus` (movimento 3 num bloco único, apesar de o
> texto ter 3 parágrafos ao todo), e executa a aposentadoria do editor [E2]
> que a v1.9.9 só preparou.
>
> **(1) Cobertura deixa de ser léxica — passa a ser ESTRUTURAL.** O
> registro da calibração (`resultado/best-of-3/CALIBRACAO.md`) já tinha
> medido o defeito: em `cure`, 5 dos 9 temas "ausentes" do candidato
> escolhido estavam no texto, só reescritos ("Pacing Lento e Deliberado" →
> "o andamento metódico") — cobertura real 1,00, medida 0,44. O proxy
> antigo casava termos de conteúdo com o RÓTULO do tema; punia
> sistematicamente o texto que evita copiar o rótulo, isto é, a prosa
> melhor.
>
> A pergunta muda de "este tema específico foi mencionado" (exige
> semântica — casamento por significado, que só um segundo LLM faz, e este
> projeto não põe LLM julgando prosa) para algo mais fraco e puramente
> ESTRUTURAL: o texto é dividido em SPANS por grupo (mesma âncora literal
> que `ordem_dos_grupos_ok` já usa — a primeira ocorrência do
> `rotulo_peso`), e cada span conta quantas CLÁUSULAS distintas tem
> (regex sobre pontuação e um conjunto pequeno de conectivos — "enquanto",
> "ao passo que", "além disso", "por sua vez", "embora" — a primeira
> cláusula, tipicamente a frase de abertura que só retoma o peso, é
> descartada da contagem). Cobertura = cláusulas de corpo contra temas
> atribuídos, somado sobre todos os grupos (ponderado pelo número de
> temas de cada um, não média simples entre grupos).
>
> GRUPO é garantido por construção (conteúdo do span de um grupo nunca
> soma para outro); ORDEM, por percorrer os grupos na ordem que o
> briefing fixa. **O que isto declaradamente NÃO verifica:** que a
> cláusula N seja REALMENTE sobre o tema N — só que existem cláusulas
> suficientes. Uma ideia repetida três vezes com sinônimos conta como
> três. É a mesma troca declarada de todo proxy do projeto: extinguir o
> falso negativo sistemático (grave e medido) custa a capacidade de pegar
> a omissão de UM tema específico dentro de um grupo bem escrito em
> volume — mais rara, e sem exemplo medido até agora. Sob a métrica nova,
> as 9 narrativas do best-of-3 medem 1,00 de cobertura — o proxy segue
> nunca decidindo entre candidatos limpos, mas agora pela razão oposta: os
> candidatos realmente cobrem os temas, não porque o proxy está cego.
>
> **(2) Parágrafo por GRUPO no movimento 3.** A leitura apontou
> `cidade-de-deus`: 3 parágrafos ao todo (passa em `problemas_de_paragrafo`,
> v1.9.9), mas o movimento 3 inteiro — os três grupos — espremido num
> bloco único. `problemas_de_paragrafo` só contava o TOTAL de parágrafos
> do texto, não a que grupo cada um pertence.
>
> `grupos_sem_paragrafo_proprio` localiza, para cada grupo do movimento 3,
> o parágrafo em que seu `rotulo_peso` aparece pela primeira vez (mesma
> âncora do item 1), e reprova quando dois grupos APRESENTADOS — permissão
> `pode_citar_temas`, ou seja, fora de `sem_analise` — caem no MESMO
> índice de parágrafo. Um grupo em `sem_analise` não entra na contagem: a
> regra acompanha o número real de grupos apresentados, não um total fixo
> de 3 — um filme com um bucket sem análise exige menos parágrafos, não os
> mesmos 3 com um deles vazio.
>
> Aplicada retroativamente ao best-of-3 já gerado (sem nenhuma chamada
> nova de LLM — a seleção roda de novo sobre os MESMOS 3 candidatos por
> filme): o candidato de `cidade-de-deus` que o código tinha escolhido na
> v1.9.9 tinha exatamente esse defeito (dois grupos dividindo parágrafo) e
> passa a ser eliminado; a escolha automática muda de B para A, o único
> candidato limpo dos três. `resultado/best-of-3/resultados.json` e
> `GATE_SEM_EDITOR.md` foram regravados com a escolha corrigida;
> `resultado/comparacao-narrador/resultados-v199.json` também foi
> reavaliado com as duas checagens novas — `gemini-3.7-flash` passa de 0
> para 1 flag no total dos 3 filmes (a mesma classe de defeito, em
> `cure`), mas segue o candidato com menos flags de longe (10/4/2 para os
> outros três).
>
> **(3) Editor [E2] APOSENTADO.** Decisão do dono do projeto, registrada
> após a leitura das 3 narrativas sem editor da v1.9.9: o ritmo se
> sustenta sem o estágio. Código movido para
> `experimentos-editor-e2-arquivado/` (mesmo padrão de
> `experimentos-ollama-arquivado/` — arquivado, não deletado, com o motivo
> ao lado), chamada removida do pipeline (`cli.py`).
>
> **Por que aposentar em vez de reescopar.** A alternativa já decidida
> (reescopar por MOVIMENTO, 3 blocos) tornaria inversão de ordem
> impossível por construção, mas não elimina as OUTRAS duas classes de
> falha do editor — conteúdo inventado e edição descartada por esgotar
> tentativas — que exigiriam sua própria mitigação em CADA bloco. Deletar
> o estágio deleta as TRÊS classes de falha de uma vez: as 4 tentativas
> descartadas em `cure` (v1.7.1, variância do modelo entre chamadas), o
> parágrafo de opinião inventado em `the-invite-2026` (v1.8.0, checagem
> de conteúdo adicionado não existia ainda), e a inversão de movimentos
> que motivou a checagem de ordem (v1.8.0). Nenhuma dessas falhas pode
> mais ocorrer, porque o mecanismo que as causava não roda.
>
> **O que a arquivagem levou, e o que ficou.** `editar_narrativa` e toda a
> maquinaria exclusiva dele (protegidos, checagem de conteúdo adicionado,
> checagem de ordem de movimento, edição nula, capitalização residual,
> `_EDITOR_SYSTEM_PROMPT`) saíram de `synthesize.py`; `EdicaoResult` saiu
> de `models.py`; as constantes `EDITOR_*` saíram de `config.py`. O
> módulo arquivado ainda importa um punhado de funções PRIVADAS de
> `synthesize.py` (`_resolve_call_and_model`, `_pesos_por_bucket`,
> `_marcadores_validos`, `_validar_prosa`, `_dividir_frases`,
> `_metricas_fluencia`, entre outras) — deliberado, não acidente: essas
> funções são a maquinaria de honestidade do narrador ANTIGO (§D2 pré-
> briefing, ainda em uso e testado por compatibilidade), e duplicá-las no
> arquivo criaria duas fontes de verdade para a MESMA checagem, um risco
> maior que um import de nome privado através da fronteira do arquivo.
>
> As checagens que continuam fazendo sentido sobre a saída do narrador
> — porque não comparam bruto×editado, e sim validam o texto sozinho —
> **permaneceram** em `synthesize.py`/`qualidade.py`, e passam a
> verificar o NARRADOR, não mais o editor: `_ancoragem_de_peso_ok`,
> `_marcadores_validos`, `_validar_prosa` (idioma/escopo/prevalência),
> `qualidade.formato_invalido`, `qualidade.numeros_inventados`,
> `qualidade.rotulos_peso_faltando`, `qualidade.ordem_dos_grupos_ok` — e,
> desta sessão, `quantificadores_fora_de_faixa`/`repetidos`,
> `problemas_de_paragrafo` e `grupos_sem_paragrafo_proprio`. As que
> **deixaram de ter objeto**, porque compunham BRUTO contra EDITADO e não
> há mais um par a comparar: conteúdo adicionado
> (`_conteudo_adicionado_ok`/`_frases_sem_origem`), ordem de movimento
> alterada (`_ordem_movimento_alterada`), edição nula (a checagem de
> similaridade bruta×editada), e a proteção literal de trecho
> (`montar_protegidos`/`_protegidos_perdidos`) — todas arquivadas junto.
>
> `cli.py` publica agora, sempre, a narrativa do narrador diretamente —
> mesmo formato de saída que o antigo caminho "editor desligado"
> (`--no-edicao`), que era o já testado e o mais conservador dos dois.
> As flags `--no-edicao`/`--com-editor` foram removidas (não há mais o
> que ligar ou desligar); `edicao_flags`/`narrativa_bruta` não são mais
> gravados em runs NOVOS — `resultado/*.json` publicados antes desta
> versão continuam com o campo, e o renderizador de terminal continua
> sabendo lê-lo (compatibilidade histórica, não vestígio morto).
>
> **(4) Escolha de modelo de narrativa — FECHADA: `gemini-3.7-flash`,
> FIXADO em `MODELO_POR_ESTAGIO["narrativa"]` (`config.py`) com versão
> explícita — nunca o alias `gemini-flash-latest` que o campo carregava
> como placeholder desde a v1.9.8 (alvo móvel: comparação não reproduzível
> e preço não ancorável).**
>
> Base da decisão — 4 candidatos × 3 filmes sob briefing determinístico
> (v1.9.8) + correções de prosa (v1.9.9) + cobertura estrutural/parágrafo
> por grupo (v1.9.10), `resultado/comparacao-narrador/RELATORIO_V199.md`:
>
> | candidato | flags totais (3 filmes) | custo/filme | latência |
> |---|---|---|---|
> | **gemini-3.7-flash (escolhido)** | **1** | US$0,0037 | ~14s |
> | gemini-3.1-pro-preview | 2 | US$0,0365 | ~22s |
> | gemini-2.5-flash | 4 | US$0,0061 | ~17s |
> | deepseek-baseline | 10 | US$0,0006 | ~7s |
>
> **A escolha é por CONFORMIDADE, não por custo** (palavras do dono do
> projeto). A única flag do 3.7-flash nos 3 filmes é colisão de parágrafo
> — defeito de FORMA, já coberto por `grupos_sem_paragrafo_proprio`; as dos
> concorrentes incluem defeito de CONTEÚDO (rótulo de peso ausente,
> vocabulário do peso misturando "notas" com "reviews"/"público") — a
> invariante central do produto (§0, §D2). A diferença de custo entre os
> quatro (~1 centavo por filme no pior caso) não pesou.
>
> **Ressalva registrada, não resolvida:** o 3.7-flash é o mais conciso dos
> quatro, e o movimento 2 de `cure` segue com uma única frase mesmo com o
> material do briefing completo — a Entrega 3 da v1.9.9 já tinha descartado
> orçamento e prompt como causa; é escolha de concisão do próprio modelo.
> Não muda a decisão desta sessão; é o primeiro sintoma a observar se o
> texto parecer raso quando o catálogo crescer.

> #### INTEGRAÇÃO — o narrador novo entra no caminho de produção (v1.9.11)
>
> **O defeito que esta versão corrige é de ARQUITETURA, não de prosa.** O
> levantamento da v1.9.10 (`MAPA_PROXIMA_FASE.md`) achou o item que
> bloqueava todo o resto: **o pipeline de produção nunca passou a usar
> nada do que as três versões anteriores construíram.** `cli.py` chamava
> `narrate_output` — o narrador PRÉ-briefing (§D2 v1.2.0–1.9.7) — e o
> briefing determinístico (v1.9.8), as correções de tique/parágrafo/
> movimento 2 (v1.9.9), a cobertura estrutural e o parágrafo por grupo
> (v1.9.10) e o best-of-3 existiam apenas em `scripts/best_of_3.py`,
> rodando à parte.
>
> Consequência medida, e ela é o ponto: **as narrativas aprovadas na
> leitura humana não eram as que o produto geraria.** Dez sessões de
> medição, nenhuma no caminho de produção.
>
> **Segundo fio solto encontrado na mesma inspeção:** `PROVIDER_POR_ESTAGIO`
> /`MODELO_POR_ESTAGIO` (v1.9.8) e os resolvedores `provider_do_estagio`/
> `modelo_do_estagio` existiam, estavam testados — e **nenhum caminho de
> produção os chamava**. `narrate_output` resolvia provider por
> `_resolve_call_and_model` → `detect_provider`, que devolve o
> `DEFAULT_PROVIDER` global. Ou seja: a decisão "DeepSeek classifica,
> Gemini narra" estava escrita, testada e inerte — na prática o narrador
> de produção rodava em DeepSeek. A integração liga os dois.
>
> **O que passa a ser o caminho de produção** (`narrador.narrar`, módulo
> novo): `montar_briefing` → `serializar_briefing` →
> `PROMPT_NARRADOR_BRIEFING` → **N narrativas independentes**
> (`BEST_OF_N = 3`) → **seleção POR CÓDIGO** (`selecao_narrativa.
> selecionar`: flags limpas eliminatórias, depois clichê, repetição de
> construção quantificadora, ritmo e cobertura estrutural) → **fallback de
> retry DIRECIONADO** nas frases infratoras quando nenhuma passa limpa. O
> provider e o modelo vêm de `provider_do_estagio("narrativa")`/
> `modelo_do_estagio("narrativa")` — `gemini-3.7-flash`, fixado na
> v1.9.10.
>
> **Custo declarado da mudança: 3 chamadas LLM por filme em vez de 1** (4
> no pior caso, com o retry direcionado). É o preço do best-of-3, e ele
> foi aceito quando o best-of-3 foi decidido; o que muda aqui é só que
> agora o preço é pago em produção. A ~US$0,0037 por narrativa medidos na
> v1.9.10, são ~US$0,011 por filme.
>
> **Uma implementação, não duas.** `scripts/best_of_3.py` deixa de ter
> lógica própria de geração/seleção e passa a ser um invólucro fino sobre
> `narrador.narrar` — duas implementações do mesmo estágio é exatamente a
> divergência que produziu este defeito, e mantê-las seria repetir a causa
> enquanto se corrige o efeito.
>
> **O narrador ANTIGO é arquivado**, no padrão do editor [E2] (v1.9.10) e
> dos experimentos de LLM local: código movido para
> `experimentos-narrador-antigo-arquivado/`, com o motivo registrado ao
> lado, nunca deletado. **A fronteira do que saiu é mais estreita que a do
> editor, e por uma razão medida:** o editor era um bloco contíguo com uma
> entrada e testes próprios; o narrador antigo tem ~60 nomes no fecho de
> chamadas, e boa parte deles é MAQUINARIA COMPARTILHADA — `_rotulo_peso`,
> `_marcacao_perspectiva`, `_pesos_por_bucket`, `_marcadores_validos`,
> `_ancoragem_de_peso_ok`, `conferencia_quantificador` — usada por
> `render.py`, pelo editor arquivado e por scripts de diagnóstico
> históricos. Sai o que é EXCLUSIVO do estágio (os prompts
> `NARRATOR_SYSTEM_PROMPT*`, `build_narrator_prompt`,
> `_serialize_output_for_narrator`, `narrate_output`, os blocos de reforço
> e as validações de campo DECLARADO — `consensos_usados`,
> `quantificadores_usados`, `marcadores_perspectiva`); fica o que é
> compartilhado, documentado como tal. Arrastar a maquinaria compartilhada
> junto criaria duas fontes de verdade para a mesma checagem — o risco que
> a v1.9.10 já tinha recusado ao arquivar o editor.
>
> **Telemetria no JSON de resultado.** `narrativa_flags` (as 10 flags do
> narrador antigo, derivadas de campos que o LLM DECLARAVA) não existe
> mais em execução nova — o narrador sob briefing não declara nada, só
> escreve prosa. No lugar entram dois campos:
> `verificacao_narrativa` (a saída de `qualidade.verificar` — as flags
> mecânicas, computadas sobre o TEXTO) e `narrativa_selecao` (o registro
> do best-of-3: métricas de cada candidato, índice escolhido, motivo,
> critério decisivo, retry, provider/modelo, tokens e latência). O
> briefing NÃO é persistido: é função determinística do próprio `output`,
> e gravá-lo dobraria o JSON para reproduzir o que já é reproduzível.
> `render_terminal` lê os dois formatos — `resultado/*.json` publicados
> antes desta versão continuam renderizando com o bloco antigo.
>
> **Preposição do rótulo de peso — variantes CONTRAÍDAS pré-aprovadas.**
> Defeito real na narrativa final de `cidade-de-deus` (v1.9.10): "Em a
> grande maioria das notas (~91%)". A causa é colisão entre duas regras
> corretas: o rótulo é preservado LITERALMENTE (invariante desde a v1.6.0,
> é o que impede o peso de virar retórica solta) e o português contrai
> "em + a" → "na". O modelo obedeceu à invariante e escreveu agramatical.
>
> A correção NÃO afrouxa a invariante: `rotulos_peso_faltando` passa a
> aceitar, como preservação válida, qualquer forma de um conjunto
> pré-aprovado de CONTRAÇÕES do artigo inicial ("a grande maioria das
> notas (~91%)" ~ "na grande maioria…", "da grande maioria…", "à grande
> maioria…", "pela grande maioria…"). **O número e a palavra "notas"
> continuam intocáveis** — só o artigo inicial varia, e só para as
> contrações listadas. O briefing passa a dizer isso explicitamente ao
> narrador, para ele não ter de escolher entre obedecer e escrever
> português.


> #### FICHA PERSISTIDA E RÓTULO COMPARATIVO — os dois bloqueios da republicação (v1.9.12)
>
> A execução da v1.9.11 num filme fora do catálogo (`joker-folie-a-deux`,
> distribuição invertida) achou dois defeitos que a amostra de 3 filmes
> aclamados escondia. Nenhum é do narrador: os dois são de DADO chegando
> errado — ou não chegando — ao briefing.
>
> **(1) O ano do filme não sobrevive à coleta, e sem ele o texto não diz
> que filme é.** Cadeia medida: slug sem sufixo de ano (`joker-folie-a-deux`)
> → execução `--offline` → o fallback da v1.7.0, que resolve o ano buscando
> a página do Letterboxd, **precisa de rede** e não roda → ano
> desconhecido → a guarda da v1.7.0 recusa buscar a ficha (corretamente:
> desambiguar por título só já produziu o defeito real do `cure`,
> resolvido para "The Cure" 2026) → `ORCAMENTO_SEM_FICHA` põe o movimento 1
> em `(0,0)` → **a narrativa abre na experiência e nunca apresenta o
> filme.** Cada elo está certo; a composição é o defeito.
>
> Alcance medido: **21 dos 35 slugs do catálogo não têm ano no nome.**
> Nenhum deles gera movimento 1 numa execução offline com cache frio. Um
> agregador de reviews que não apresenta o filme não é publicável.
>
> **A correção é de ARQUITETURA, e ela já estava escrita em §3[B'].** O
> superset existe para que "qualquer reprocessamento custe zero rede"; o ano
> é dado estável, buscado uma vez, e simplesmente não estava sendo
> guardado — pela mesma lógica que já guarda o histograma. A coleta passa a
> resolver e gravar `ano_lancamento` + `ano_fonte` no `meta.json` do bruto,
> e a resolução de ficha lê o bruto ANTES de tentar rede. A precedência
> fica: `--ano` explícito → **bruto** → sufixo do slug → Letterboxd (rede) →
> sem ficha.
>
> **Rede de segurança, não correção:** falha de ficha passa a AVISAR no
> stderr, com o motivo e a consequência dita ("movimento 1 será omitido").
> `ficha_indisponivel` continua no JSON, mas deixa de ser a única evidência
> — falha silenciosa é o que a spec proíbe em todo lugar, e esta passou
> despercebida por uma sessão inteira exatamente por ser silenciosa.
>
> **(2) O rótulo de peso não olha os vizinhos, e colide em 66% do
> catálogo.** Medido: `joker-folie-a-deux` (46/33/21) abre dois parágrafos
> seguidos com "Em boa parte das notas" — 46% e 33% caem na mesma faixa
> (30–50). Varrido o histograma dos 35 filmes: **23 de 35 (66%) têm pelo
> menos dois grupos com rótulo IDÊNTICO**, e o caso dominante é o filme
> aclamado — com `positivas` acima de 80%, os outros dois caem ambos abaixo
> de 15% e viram os dois "uma fração mínima das notas". **Vale para os 3
> filmes do catálogo sob as fronteiras C.**
>
> **Duas alternativas foram REJEITADAS, com motivo:**
> - *aceitar e declarar* (o percentual entre parênteses já desambigua) —
>   rejeitada porque contradiz o princípio que criou o rótulo: ele existe
>   para que o leitor NÃO precise fazer aritmética. Se a distinção entre
>   dois grupos está só no número, o rótulo parou de trabalhar, e aceitar
>   isso em 66% dos filmes é aceitar que ele não funciona;
> - *mais faixas* — rejeitada porque não resolve: com `cure` em 2/8/90,
>   qualquer granularidade razoável ainda junta 2% e 8%. **O problema não é
>   a largura das faixas, é o rótulo ser calculado sem olhar os vizinhos.**
>
> **Adotado: rótulo COMPARATIVO na colisão.** `rotulos_peso(shares)`
> substitui `_rotulo_peso_completo(pct)` e computa os três de uma vez:
> quando dois ou mais grupos caem na mesma faixa, o MAIOR mantém a forma
> base e os menores recebem a forma comparativa da mesma faixa
> (`boa parte` → `uma parte menor` → `uma parte ainda menor`;
> `uma fração mínima` → `uma fração ainda menor` → …). As formas são uma
> TABELA por faixa, não uma operação de string — mesma política de todo
> vocabulário do projeto.
>
> **O que NÃO muda, e é o que mantém a invariante de pé:** o rótulo continua
> carimbado por CÓDIGO e preservado LITERALMENTE pelo narrador; o número
> entre parênteses é o mesmo; as contrações pré-aprovadas (v1.9.11)
> continuam valendo, porque `variantes_rotulo` opera sobre o primeiro token
> do rótulo, seja ele qual for.
>
> **A verdade do comparativo é condição, não estilo:** a forma "menor" só é
> aplicada quando o grupo é DE FATO menor que o vizinho de mesma faixa.
> Grupos com percentual IGUAL na mesma faixa mantêm o mesmo rótulo — dizer
> "menor" ali seria falso, e a coincidência de rótulo é honesta quando os
> pesos coincidem de verdade.
>
> **(3) Reprodutibilidade offline — dívida DIAGNOSTICADA, não paga.** A
> v1.9.11 registrou que `the-invite-2026` não roda offline: pede uma página
> que nunca foi cacheada. O diagnóstico desta versão está em §3[B'],
> "Posição recomputada": o bruto guarda as reviews mas **não guarda quais
> POSIÇÕES foram buscadas**, e a escolha de páginas é recomputada a cada
> execução por uma estratégia que mudou (v1.9.2 geométrica → v1.9.5 frações
> da profundidade real). Fura a promessa central do superset. A correção
> não entra nesta versão porque toca a camada de coleta — a recomendação
> registrada é gravar as posições efetivamente buscadas no `meta.json` e o
> modo offline honrá-las.
>
> #### FECHAMENTO DE PROSA E TELEMETRIA — o gate final antes de publicar (v1.9.13)
>
> Três defeitos pequenos, apontados pela própria leitura da v1.9.12, mais
> um achado incidental durante a regeneração.
>
> **(1) Um parágrafo por MOVIMENTO, não só por grupo.** Medido: em `cure`,
> os movimentos 1 e 2 saem no MESMO parágrafo (a frase "A experiência do
> filme é conduzida por um ritmo desacelerado..." — claramente movimento 2
> — está colada ao fim do parágrafo de apresentação). O total de parágrafos
> (4) passa no mínimo (3), então a checagem existente não via nada errado —
> ela conta quantidade, não posição.
>
> **A distinção entre "movimento 2 omitido" (autorizado desde a v1.4.1) e
> "movimento 2 escrito, mas fundido ao parágrafo errado" NÃO é computável
> por posição:** as duas produzem exatamente a mesma contagem de
> parágrafos entre a âncora do movimento 1 e o início do movimento 3 — a
> diferença só existe no CONTEÚDO da frase, e decidir se uma frase é sobre
> "a experiência de assistir" é o mesmo casamento semântico que a v1.9.9
> já registrou como fora do alcance do código.
>
> A correção adotada é um PROXY declarado, no mesmo espírito de
> `selecao_narrativa.cobertura`: âncora o parágrafo do movimento 1 pelo
> `ano` da ficha (número literal, praticamente garantido) e conta as
> FRASES desse parágrafo. Mais de duas frases ali é sinal de que o
> parágrafo carrega mais do que "diretor, gênero, ano, premissa" — medido
> nos 4 textos da v1.9.12: `cure` (3 frases, a terceira é movimento 2)
> dispara; `cidade-de-deus`, `the-invite-2026` e `joker-folie-a-deux` (2
> frases cada) não disparam. **Declaradamente imperfeito** — um filme cuja
> premissa genuinamente precise de 3 frases seria um falso positivo — mas
> é o mesmo tipo de troca que todo proxy do projeto já assume.
>
> **(2) Repetição por RAIZ, não por string literal.** Medido:
> `joker-folie-a-deux` usa "a maior parcela" e "a maior parte" em
> parágrafos vizinhos — duas construções DIFERENTES da mesma faixa
> (`a maioria`), então a checagem de repetição (que conta string idêntica)
> não via nada, mas o efeito no leitor é o tique de novo, em forma mais
> sutil.
>
> `quantificadores_repetidos` passa a agrupar por RAIZ dentro da MESMA
> faixa — nunca entre faixas, porque faixas diferentes medem frequências
> diferentes e agrupá-las apagaria a distinção que a faixa existe para
> preservar (`RAIZ_POR_CONSTRUCAO`, tabela explícita, não stemming
> algorítmico — mesma política de `COMPARATIVOS_PESO`).
>
> **O crítico que a Entrega 2 pediu, medido:** agrupar por raiz reduz
> `alguns`, `cerca de metade`, `a maioria` e `quase todos` para MENOS de 3
> raízes distintas (o pior caso, `cerca de metade`, cai para 1 — as 4
> construções da faixa são todas sinônimo direto de "metade", e não existe
> jeito natural de dizer "~50%" em português sem essa raiz). Três faixas
> foram corrigidas com uma construção nova, natural e sem colisão de
> substring com nada existente: `alguns` ganha "uma fatia menor"
> (→ 3 raízes), `a maioria` ganha "grande parte" (→ 3 raízes), `quase
> todos` ganha "praticamente sem exceção" (→ 3 raízes). `cerca de metade`
> ganhou "meio a meio" mas **fica em 2 raízes, registrado como limite
> estrutural do português, não resolvido por engenharia**.
>
> **(3) `duma` fora das contrações pré-aprovadas.** Decisão do dono do
> projeto: gramaticalmente correta, mas soa arcaica em prosa escrita.
> `de uma` continua valendo (é a forma NÃO contraída, nunca precisou de
> autorização). `numa` — a contração de "em + uma" — permanece: é comum e
> soa natural ("numa fração mínima das notas").
>
> **(4) `coletado_em` mentindo em execução sem rede.** Achado ao regenerar
> os 4 filmes da v1.9.12 `--offline`: o campo avançou ~5h mesmo com ZERO
> requisições — `persistir`/`coletar_superset` sempre carimbam "agora",
> independente de terem tocado a rede. É o SEGUNDO sintoma da mesma raiz
> diagnosticada em "Reprodutibilidade offline" (v1.9.12): `meta.json` não
> separa O QUE A COLETA FEZ de QUANDO ALGUÉM RODOU O PIPELINE.
>
> Corrigido o sintoma imediato, contido: `coletado_em` só avança quando
> `fetcher.n_network > 0` nesta execução; sem requisição nenhuma, o valor
> anterior é preservado. **A correção estrutural (posições gravadas,
> separação de campos de execução) continua diagnosticada e NÃO
> implementada** — aguarda a mesma decisão de §3[B'], "Posição
> recomputada".


Etapa **PÓS-síntese**, opcional, controlada pela flag `--tom` (ver abaixo). Uma **única chamada LLM para o filme inteiro** (não por bucket); **o provider é escolhido por ESTÁGIO desde a v1.9.8** (ver §3[D], "Provider por estágio") — não mais forçosamente o mesmo da síntese.

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

### [D3] Rotulagem de temas por EIXO — a metade qualitativa da linha (v1.9.14)

O alinhamento por linha precisa de duas metades que vivem em lugares
diferentes do pipeline:

```
Ritmo — arrasta (24/40) | lento mas justificado (11/40) | hipnótico (19/40)
        └── FRASE:  vem dos `temas` de §[D]        └── NÚMERO: vem da
            (o que ESTE grupo diz do eixo)             classificação por
                                                       review (§2.5), somado
                                                       em CÓDIGO
```

Elas não estavam ligadas: os `temas` são texto livre por bucket, a
classificação é por review, e nada dizia que "Ritmo lento e arrastado" é o
eixo `ritmo`. **[D3] é essa ligação, e só ela.**

**Uma chamada por bucket.** Entrada: a lista FECHADA dos 10 eixos com as
definições byte-idênticas às de `scripts/classificar_10.py`, mais os ≤6
temas daquele bucket. Saída: um eixo por tema. Nenhum número entra no
prompt e nenhum número sai dele — [D3] não vê frequência, não vê
denominador e não vê os outros grupos.

**Validação mecânica, não confiança.** O código confere cada rótulo contra a
lista fechada; **o que não estiver nela vira `livre`**. Um eixo inventado
nunca entra no schema — mesmo padrão de verificação em vez de instrução que
a spec aplica desde a v1.2.3.

#### A assimetria de validação, declarada

A classificação de produção (§2.5) passou por auditoria humana de 100
reviews, votação de 3 passadas, precisão e recall medidos **por eixo**, e
duas variantes de prompt comparadas contra o mesmo gabarito com bootstrap
pareado. **[D3] não passou por nada disso.** É um segundo uso da mesma
taxonomia por um prompt que nunca foi medido contra gabarito humano.

Isto está aqui como **ressalva de primeira classe, não nota de rodapé**: o
número da célula tem oito sessões de medição atrás dele; o rótulo que decide
em qual LINHA a célula aparece não tem nenhuma. As duas coisas convivem no
mesmo pixel e não têm o mesmo estatuto.

**A mitigação adotada** é proporcional ao risco e ao tamanho do problema:
são ~50 células nos 3 filmes publicados, e a tabela `tema → eixo atribuído`
é **conferida à mão pelo dono do projeto** antes de publicar
(`resultado/v1914/ROTULAGEM_CONFERENCIA.md`, atualizada na v1.9.15 em
`resultado/v1915/ROTULAGEM_CONFERENCIA.md`). Não é a auditoria de 100
reviews — é muito melhor que publicar sem validação nenhuma, e o que ela
cobrir fica registrado como conferido, não como presumido.

**Reprodutibilidade medida (v1.9.15, Entrega 4).** A conferência da v1.9.14
achou um caso concreto: em `cidade-de-deus`, "Excesso de violência e ritmo
exaustivo" (negativas) foi rotulado `ritmo` e "Excesso de violência"
(medianas) foi rotulado `tom_atmosfera` — mesmo núcleo, eixos diferentes.
Para saber se é caso isolado ou padrão, [D3] foi rodado DUAS VEZES sobre os
MESMOS 54 temas dos 3 filmes publicados
(`scripts/medir_reprodutibilidade_d3.py`): **98,1% dos temas mantiveram o
mesmo eixo entre as rodadas — 1 de 54 divergiu.** É a mesma tema flagrada na
conferência: "Excesso de violência" (`cidade-de-deus`/medianas) oscilou
entre `livre` e `tom_atmosfera`; contando a execução já publicada como uma
terceira amostra independente, o placar é 2 de 3 para `tom_atmosfera` — o
tema está genuinamente numa fronteira, não é ruído aleatório sem direção.

**Leitura: NÃO é a mesma classe de problema que a classificação por review
tinha antes da votação de 3** (26,5% de reprodutibilidade individual medida
em `ESTABILIDADE_AGREGADA.md` — [D3] está em 98,1%, quase 4× mais estável).
Um tema por bucket em 54 é o ritmo de divergência esperado numa tarefa de
classificação com fronteiras reais entre categorias (§2.5, os mesmos eixos
que saturam ou colidem na classificação por review têm o mesmo efeito aqui).
**Decisão: NÃO implementar votação em [D3]** — o custo seria recorrente por
filme (hoje 1 chamada/bucket, viraria 3), e a taxa medida não justifica.
Revisitar se a fração de divergência crescer com o catálogo.

**O que [D3] NÃO pode fazer:** mudar o número. Se o rótulo põe um tema na
linha errada, a linha erra a FRASE; a frequência daquele eixo continua sendo
a contagem de reviews classificadas, alheia ao que [D3] decidiu. O modo de
falha é de legenda, nunca de aritmética — e é por isso que uma etapa não
calibrada é tolerável aqui e não seria na classificação.

#### DUAS POPULAÇÕES DE 40 — UNIFICADAS na v1.9.15

**Achado da v1.9.14, corrigido na v1.9.15.** Esta seção documenta o defeito
como foi medido e por que a correção era necessária; a tabela de
sobreposição abaixo é HISTÓRICA — depois da unificação, a sobreposição é
100% por construção em todo bucket dos 3 filmes publicados (verificado, não
presumido — número em `ROTULAGEM_CONFERENCIA.md`/changelog da v1.9.15).

**Por que a declaração não bastou.** A v1.9.14 tratou a divergência como
limitação aceitável, declarada em `fonte_classificacao` e no rótulo
"reviews classificadas" da interface. Isso viola o princípio central da
spec — frequência sempre com denominador visível — porque o denominador só
é verificável se aponta para a MESMA população que o texto ao lado resume.
"Estética e estilo vazios — 21/40" ao lado de "40 de 40 analisadas" com 67%
de sobreposição real é um denominador que aponta para outra população; é
pior que não ter denominador, porque parece verificável e não é. Uma nota
de rodapé não resolve — o leitor lê "21 de 40" e associa às 40 da amostra
ao lado, não às 40 que a nota descreve em abstrato.

`resultado/votacao-3/amostra.json` se declara "a população que a síntese
veria". **Não é.** Ela foi montada com `selecao.selecionar(todas, hist)` —
sem o argumento `orcamento_paginas_por_nivel`, que é o que liga a
**estratificação por profundidade** da v1.9.5 (§3[C2]). O pipeline de
produção passa esse argumento. Resultado: os dois lados selecionam 40
reviews do mesmo bucket, sob os mesmos filtros, e **não são as mesmas 40**.

Sobreposição medida (seleção de produção ∩ amostra classificada), 105
buckets do catálogo: **mediana 75%, mínimo 30%, máximo 100%**. Os 3 filmes
publicados estão entre os PIORES casos, e por um motivo estrutural — são os
que mais recoletas acumularam, logo os de bruto mais profundo, e é
exatamente onde a estratificação mais desloca a escolha:

| filme | negativas | medianas | positivas |
|---|---:|---:|---:|
| `cure` | 27/40 | 25/40 | 23/40 |
| `cidade-de-deus` | **13/40** | 19/40 | 15/40 |
| `the-invite-2026` | 17/40 | 13/40 | 17/40 |

**Por que isto importa tanto neste projeto.** É a mesma classe de defeito
que a spec já protege entre NOTAS e REVIEWS COM TEXTO (§D2, invariante de
vocabulário) e que a Entrega 6 desta versão fecha entre a janela da amostra
e a janela do histograma: duas populações diferentes que o texto não pode
apresentar como se fossem as mesmas pessoas. "40 de 40 analisadas" no
cabeçalho do grupo e "24 de 40" na linha do eixo são **dois quarentas
diferentes**.

**O que a v1.9.14 fez, mantido como registro histórico (a mitigação da
época, substituída pela correção estrutural abaixo):**

1. A frequência por eixo era calculada sobre a amostra CLASSIFICADA, não
   sobre a intersecção — preservava a calibração de 20pp, medida com `n=40`
   por bucket, às custas de um denominador que apontava para a população
   errada.
2. A divergência era declarada em `fonte_classificacao`
   (`n_classificadas`/`n_analisadas`/`sobreposicao_com_analisadas`).
3. A interface rotulava o denominador do eixo como *reviews classificadas*,
   distinto de *analisadas* no cabeçalho do grupo.

**A correção aplicada na v1.9.15: ESTENDER a classificação até cobrir a
seleção de produção inteira, sob o MESMO `taxonomia_id` e a MESMA votação de
3 passadas.** Não é reclassificar o corpus — o que já está classificado é
reusado, como o versionamento por `taxonomia_id` foi desenhado para
permitir. As reviews da seleção de produção que nunca passaram pela
classificação são as ÚNICAS que geram chamada nova.

Consequência aceita e verificada: `n=40` continua sendo `n=40` — a
calibração de 20pp não muda de unidade, só passa a contar as 40 reviews
certas. Os 3 filmes publicados são medidos sobre uma amostra que os outros
32 do catálogo não têm (ainda) — cada um deles segue com a amostra
CLASSIFICADA original até passar pela mesma extensão. O lift de cada eixo
nos 3 filmes foi recomputado antes/depois (changelog da v1.9.15) e o estado
`contraste` de cada um foi conferido explicitamente.

**Correção de registro, agora fechada:** o campo `criterio` de
`amostra.json` afirmava "a amostra é a população que a síntese veria" desde
a v1.9.5 sem que isso fosse verdade. Com a extensão da v1.9.15, para os 3
filmes publicados **volta a ser verdade por construção** — a divergência
`fonte_classificacao`/nota de rodapé perde objeto para esses 3 e é removida
do bloco (`sobreposicao_com_analisadas == n_classificadas == n_analisadas`
em todo bucket). Continua valendo para o resto do catálogo até a mesma
extensão ser aplicada lá.

### [V] Veredito — a linha de contraste, escrita por LLM sobre briefing determinístico (v1.9.21)

O **veredito** é a linha de 1–2 frases no topo de `filme.html`, entre a ficha
e os bullets: a leitura de UMA frase que a tabela "eixo a eixo" (removida na
v1.9.19) pedia ao leitor para fazer de cabeça. Ele nasceu na v1.9.19 como
TEMPLATE determinístico sobre o lift já computado, zero LLM, e foi corrigido
na v1.9.20 para não mentir por omissão (`eixoDeMaiorFrequencia`). Esta versão
troca o gerador do texto — **o briefing continua sendo código; a redação passa
a ser LLM** — e mantém o template como rede.

#### O defeito medido, e por que ele não é do template

**19 dos 35 filmes recebiam texto BYTE-IDÊNTICO** — `"Os grupos falam das
mesmas coisas — discordam sobre se elas funcionam."` — e **20 caíam no ramo
que a produz** (o vigésimo, `friday-the-13th-2009`, difere só pelo prefixo de
meio dominante). O catálogo inteiro tinha **14 textos distintos para 35
filmes**. Repetido assim, o veredito não acrescenta nada à experiência.

A causa não é o template ser burro — é o **briefing ser pobre**. A frase
relata a AUSÊNCIA de contraste e nunca a PRESENÇA de assunto. O dado para
dizer *do que cada grupo fala* já existe em `eixos.linhas[].por_bucket[]`
(`tema`, `mencoes`, `de_n`) e era descartado.

**Medição que fecha a porta do conserto barato:** se o template passasse
apenas a NOMEAR o eixo dominante de cada lado, a repetição não seria
resolvida — são 10 combinações distintas para os 20 filmes, com
`roteiro_estrutura / roteiro_estrutura` saindo 5 vezes. Os 10 eixos são lista
fechada (§2.5) e `roteiro_estrutura` domina o catálogo. **A variedade real
está no campo `tema`**, string por filme, já rotulada por [D3], já exibida
nos bullets, já passada pelo filtro anti-spoiler da síntese. É esse dado que
o briefing precisa carregar.

#### Posição no pipeline, insumo e saída

O estágio roda **na PUBLICAÇÃO, não a cada pageview** — ~35 chamadas por
regeneração de catálogo, não uma por leitor.

```
[D3]/eixos  ──►  [V] veredito  ──►  resultado/<slug>.json
                      ▲                        │
                      │                        ▼
             buckets + ficha        build_data.py ──► frontend/js/data.js
                                                              │
                                                              ▼
                                                     filme.js (render puro)
```

- **Consome:** o dict `output` já montado — `eixos` (obrigatório: sem ele o
  estágio devolve `None` e a chave não é emitida), `buckets`, `ficha`.
  **Nunca reviews brutas** — mesma fronteira de §D2 desde a v1.2.0.
- **Depende de** [D3] ter rodado antes, pela mesma razão que o briefing do
  narrador depende: `contraste` vem de lá.
- **Independe de** [D2]: veredito e narrativa não se leem. Regenerar um não
  obriga a regenerar o outro.
- **Grava:** a chave de topo `veredito` (schema abaixo).

**`veredito.spec_version`, e por que o carimbo do FILME não sobe.** O bloco
carrega a própria versão, como `eixos` já faz desde a v1.9.14. Regenerar só o
veredito sobre um JSON existente **não** re-roda coleta, seleção, síntese,
[D3] nem narrativa — e escrever `1.9.21` no `spec_version` de topo afirmaria
que rodou. Mesma política de `VERSAO_COLETOR` (§3[B']): um carimbo que não
corresponde ao que foi executado não é evidência de nada.

> **Consequência registrada, não corrigida nesta versão:** o checkpoint de
> `scripts/publicar_catalogo.py` considera um filme "publicado sob o pipeline
> corrente" quando `spec_version == SPEC_VERSION`. Com `SPEC_VERSION` em
> `1.9.21` e os 35 JSONs em `1.9.16`, aquele script passa a enxergar os 35
> como pendentes. **Isto é correto** — eles de fato não passaram pelo
> pipeline completo da v1.9.21 — mas significa que rodar
> `publicar_catalogo.py` sem `--slug` republicaria o catálogo inteiro. O
> estágio [V] tem harness PRÓPRIO (`scripts/gerar_veredito.py`), que não usa
> aquele checkpoint e não chama coleta/síntese/narrativa.
>
> **O footgun é FECHADO, não apenas registrado (v1.9.21).** Antes desta
> versão, rodar `publicar_catalogo.py` sem argumento era inócuo: os 32 slugs
> default eram todos pulados por `_ja_publicado`. Com a constante em
> `1.9.21`, nenhum é pulado — um comando de uma linha dispara re-scrape de 32
> filmes a 2s por requisição sem paralelismo, e apaga o histórico `passadas`
> do `meta.json` (dívida conhecida, `DIAGNOSTICO_OFFLINE.md`). Caro e
> irreversível para o histórico. `cmd_publicar` passa a **recusar execução**
> quando mais de `LIMITE_LOTE_SEM_CONFIRMACAO = 5` filmes seriam de fato
> republicados, exigindo `--republicar-tudo`, com mensagem que diz **quantos
> e por quê**. O limiar é decisão de produto: acima de um punhado, o comando
> deixa de ser "conserta um caso" e vira "republica o catálogo", e a
> diferença entre os dois é de horas de rede. A guarda conta quem SERIA
> republicado, não o tamanho da lista — passar os 35 com 32 em dia é um lote
> de 3, e passa. **Escopo estritamente este:** o checkpoint em si não muda, e
> a dívida do `passadas` continua aberta.

#### Schema do bloco `veredito`

```json
"veredito": {
  "texto": "<1–2 frases, pt-BR, sem algarismos>",
  "origem": "llm" | "template_fallback",
  "prefixo_codigo": "<string ou null>",
  "provider": "gemini",
  "modelo": "gemini-3.1-pro-preview",
  "n_candidatos": 3,
  "n_chamadas": 3,
  "indice_escolhido": 0,
  "motivo": "melhor_entre_limpos" | "menor_severidade" | "template_fallback",
  "criterio_decisivo": "flags" | "comprimento" | "unico" | "empate",
  "candidatos": [
    {"indice": 0, "n_flags": 0, "flags": [], "n_palavras": 31, "eliminado": false}
  ],
  "flags": [],
  "uso": {"prompt_tokens": 0, "completion_tokens": 0,
          "cache_hit_tokens": 0, "cache_miss_tokens": 0},
  "latencia_s": 0.0,
  "spec_version": "1.9.21"
}
```

`texto` é o texto FINAL, já com `prefixo_codigo` concatenado quando existe —
o frontend renderiza `texto` e nada mais. `prefixo_codigo` fica ao lado como
telemetria de qual parte não veio do modelo.

**Telemetria é DIAGNÓSTICO DE PRODUÇÃO, não informação de leitor.** Nenhum
campo além de `texto` chega à tela — mesma decisão já tomada para
`verificacao_narrativa` e `narrativa_selecao`.

#### O contrato do briefing (`veredito.py`, código puro, zero LLM)

**Regra dura: todo número e todo rótulo quantificador que aparece no briefing
é calculado aqui.** O modelo recebe rótulos prontos e nomes de tema prontos;
nunca calcula, nunca arredonda, nunca escolhe intensidade. Mesmo princípio da
v1.1.1 (denominador), v1.2.3 (quantificador) e v1.4.0 (peso).

**Nível do filme:**

| Campo | Origem | Quem calcula |
|---|---|---|
| `titulo`, `ano` | `ficha` (com fallback para o slug) | código |
| `contraste` | `eixos.contraste` | [D3]/`eixos.py` |
| `margem_lift_pp` | `eixos.margem_lift_pp` | `config.MARGEM_LIFT_PP` |
| `bucket_dominante` | maior `share_real` dos `buckets` | código |
| `assunto_compartilhado` | ver critério abaixo | código |
| `grupos` | por bucket, tabela seguinte | código |

**Por bucket** (`negativas` e `positivas` sempre; `medianas` **só quando é o
bucket dominante** — o meio nunca é um dos dois lados do contraste):

| Campo | Origem | Quem calcula |
|---|---|---|
| `eixo_maior_lift` + `lift_pp` + `acima_da_margem` | `eixos.linhas[].por_bucket[]` — o eixo e o `lift_pp` de lá; **e desde a v1.9.34 o `acima_da_margem` também vem de lá, LIDO e não recalculado** (§4). Até a v1.9.33 este campo era `lift_pp >= margem` em float, e com a lei por `n` isso passaria a poder divergir da decisão exata | código |
| `eixo_maior_frequencia` + `tema` + `freq_pct` | `mencoes`/`de_n` e `tema` da mesma linha | código |
| `rotulo_quantificador` | `freq_pct` → mapa de faixas | código (`quantificador.py`) |
| `share_pct` | `buckets[].share_real` | histograma (§3[G]) |
| `modo`, `estado_piso` | `buckets[]` | §3[C3] |

Bucket com `estado_piso: "sem_analise"` não empresta eixo nenhum ao briefing
— mesma guarda que `eixoDeMaiorLift`/`eixoDeMaiorFrequencia` já aplicavam.

#### `assunto_compartilhado` — o critério, o piso e a medição

**Critério:** entre os eixos que os DOIS extremos mencionam, o que maximiza
`min(freq_negativas, freq_positivas)`. Desempate por `freq_negativas +
freq_positivas`; persistindo, pela ordem canônica de `taxonomia.EIXOS`.
**Piso: 25% nos dois lados** — abaixo disso o eixo não é "assunto de ambos os
grupos", é ruído que os dois tocaram de passagem. 25% é a fronteira inferior
da faixa `muitos` do mapa de quantificador (§D2 v1.2.3), reusada aqui em vez
de um número novo.

É esse campo que dá substância ao caso `valorativo`: quando nenhum lado tem
assunto PRÓPRIO, o veredito precisa nomear o assunto COMPARTILHADO e dizer
que a divergência é de julgamento.

**Medição sobre os 35 do catálogo (v1.9.21):** todos os 35 têm assunto
compartilhado sob esse critério; nos 17 filmes `valorativo` o `min` fica
entre **40% e 84%**. Exemplos do que o campo produz:

| Filme | Eixo | Tema nas negativas | Tema nas positivas |
|---|---|---|---|
| `talk-to-me-2022` | `roteiro_estrutura` | Protagonista irritante e decisões idiotas | Personagens exasperantes e decisões irracionais |
| `wicked-2024` | `som_trilha` | Músicas genéricas e esquecíveis | Músicas marcantes e bem integradas |
| `shutter-island` | `roteiro_estrutura` | Plot twist previsível ou decepcionante | Roteiro e construção do mistério |

> **LIMITAÇÃO REGISTRADA, não contornada.** O campo `tema` de uma célula só
> existe quando aquele eixo virou BULLET daquele grupo (§2.5, seleção 2+3).
> Em **2 dos 17** filmes `valorativo` — `dune-2021` (`comparacoes`) e
> `the-substance` (`impacto_emocional`) — o eixo compartilhado não tem tema
> nomeado em NENHUM dos dois lados. Nesses casos o briefing carrega o rótulo
> do eixo sem tema, e a substância vem do top-frequência de cada lado. **Não
> se inventa texto para tapar o buraco** — é a mesma política de omissão
> autorizada da v1.4.1: preencher com genérico é pior do que não preencher.

#### A serialização não contém NENHUM algarismo

`serializar_briefing_veredito()` — o texto que efetivamente vai na mensagem
do usuário — emite **rótulos, nunca números**. O dict do briefing carrega
`freq_pct`, `lift_pp` e `share_pct` (para os testes, para a telemetria e para
o template de fallback); a serialização carrega `rotulo_quantificador` e o
booleano `acima_da_margem`.

Duas coisas caem disso, e as duas são deliberadas:

1. **A invariante "zero dígitos na saída" (§ prompt, regra 5) passa a ser
   garantida por CONSTRUÇÃO.** O modelo não pode copiar um número que nunca
   viu.

   > **As duas defesas são independentes, e é preciso saber disso ao mexer
   > em qualquer uma.** A validação `digito` em código continua existindo
   > como **redundância DELIBERADA** — não é sobra da defesa antiga, e não
   > é a defesa primária. Afrouxar a serialização (deixar um número
   > escapar para a mensagem) **não** fica coberto pela validação, porque
   > um número plausível copiado do briefing passaria a existir na saída
   > exatamente onde ela não sabe distinguir invenção de cópia; e remover
   > a validação achando que a serialização cobre **não** fica coberto
   > pela serialização, porque nada impede o modelo de INVENTAR um
   > algarismo que ninguém lhe deu. Remover qualquer uma das duas é
   > mudança de política, não limpeza.
2. **`lift_pp` não chega ao prompt, então "chegou perto" não existe para o
   modelo.** Ver a invariante do limiar binário, abaixo.
3. **O TÍTULO DO FILME também não entra.** Duas razões, e a segunda é a
   forte: (a) `friday-the-13th-2009` se chama "Sexta-Feira 13" — o título
   CARREGA algarismo, e emiti-lo abriria na serialização exatamente o buraco
   que ela existe para fechar (o mesmo falso positivo que a varredura da
   v1.9.20 já tinha investigado no frontend); (b) nomear o filme CONVIDA o
   modelo a usar o que ele sabe sobre o filme, e a invariante 2 proíbe
   contexto externo — **um briefing anônimo torna a fidelidade mais fácil de
   obedecer do que de violar**. O veredito nunca precisou dizer de que filme
   se trata: é renderizado logo abaixo do título na página.

#### O limiar é BINÁRIO — nenhuma noção de "quase passou"

`the-godfather` tem o melhor lift das negativas em **19,6pp** contra a margem
de 20 (eixo `ritmo`, 16 de 25 = 64%, tema "Ritmo lento e tédio"). Falha por
0,4pp e o filme é `valorativo`.

Isto é **observação registrada, e nada mais**. Explicitamente NÃO autoriza:

- **alterar `MARGEM_LIFT_PP`**, aqui ou em lugar nenhum. É parâmetro a
  montante que alimenta a seleção de bullets inteira (§2.5), escolhido por
  nulo de permutação com os três números à vista; mexer nele por esta porta
  mudaria o produto sem decisão de produto;
- **tratar quase-passou como contraste** no briefing ou no prompt. Se o lift
  não atinge a margem, aquele lado **não tem assunto próprio**, e ponto. O
  briefing pode carregar `lift_pp` como número; o prompt não recebe nenhuma
  noção de proximidade e o modelo não pode insinuar contraste a partir dela.

#### As invariantes do prompt

O projeto documenta prompts por extenso. O texto integral de
`PROMPT_VEREDITO` está em `src/espectro24/veredito.py`; as invariantes que
ele codifica, na íntegra:

1. **Papel e público.** Escreve para quem **ainda não assistiu** ao filme e
   está decidindo se assiste. Não é crítica, não é resenha, não é
   recomendação — é o mapa de ONDE as opiniões divergem.
2. **Fidelidade absoluta ao briefing.** Só pode citar assuntos e temas
   presentes no briefing. É PROIBIDO introduzir tema, adjetivo avaliativo
   sobre o filme, ou informação de enredo que não esteja ali.
3. **Anti-fabricação de contraste.** Quando o briefing marca `valorativo`, é
   PROIBIDO afirmar que os grupos falam de assuntos DIFERENTES. A tarefa é
   nomear o assunto COMPARTILHADO e dizer que a divergência é sobre se ele
   funciona. Concordar sobre o que o filme é e discordar sobre se ele
   funciona é um RESULTADO, não uma falta de resultado. *(Mesma invariante
   7b de §D2, aplicada a um estágio novo.)*
4. **Quantificadores (corrigida na v1.9.22).** O `rotulo_quantificador`
   fornecido é o **único admissível**. Rótulo mais FORTE é PROIBIDO e mais
   FRACO **também** — e é PROIBIDO envolver o rótulo em algo que o desminta
   ("relatos pontuais apontam que a maioria…").

   > **A v1.9.21 dizia "mais fraco é permitido", e essa metade estava
   > errada.** Foi erro de especificação, não de implementação. **Deflação
   > mente sobre o dado exatamente como inflação**, e o §0 — o código é a
   > autoridade sobre quantidade — não distingue direção. Um grupo de 58%
   > descrito como anedota é tão falso quanto um de 40% descrito como
   > "quase todos".
5. **Zero dígitos.** Nenhum algarismo na saída. Nenhuma contagem de review,
   nenhum percentual, nenhuma nota, score ou estrela. Quando o filme tem o
   meio como grupo dominante, o percentual de peso é **prefixado pelo
   CÓDIGO**, fora do texto do modelo.
6. **Anti-spoiler.** Nada de reviravolta, final, morte de personagem ou
   mecanismo central da trama. Os temas do briefing já passaram por esse
   filtro (§3[D]); não os expanda nem os detalhe.
7. **Escopo.** PROIBIDO generalizar para "os críticos", "o consenso", "a
   recepção do filme". Cada grupo é uma perspectiva, nunca uma fatia
   quantificada do público.
8. **Forma.** 1–2 frases, pt-BR, alvo de ~45 palavras, **teto de 55
   palavras**. Sem aspas de citação. Tom seco e informativo, não
   publicitário.
9. **Cautela com amostra pequena (reescrita na v1.9.22).** Quando o
   briefing indica `modo: "reduzido"`, a redação diz isso — mas **a cautela
   é sobre a AMOSTRA (quantas reviews foram analisadas), nunca sobre a
   FREQUÊNCIA (que fatia daquele grupo disse aquilo)**. PERMITIDO: "numa
   amostra pequena", "entre os poucos relatos analisados", "no material
   disponível". PROIBIDO: "impressões pontuais", "relatos isolados",
   "menções esparsas" — isso afirma um TAMANHO, e o tamanho já veio no
   quantificador. Um grupo com amostra pequena continua recebendo o rótulo
   que o briefing deu, com a ressalva sobre a base ao lado.

9b. **Mesmo tratamento para os dois lados (v1.9.22).** Quando o briefing dá
    o MESMO quantificador a quem recomenda e a quem não recomenda, os dois
    recebem o mesmo tratamento textual. É PROIBIDO nomear a frequência de um
    lado e tratar o outro como anedota. O que separa os dois grupos é o que
    eles dizem, nunca o peso que a redação lhes dá.
10. **Limiar binário.** O prompt não recebe `lift_pp` e não tem nenhuma
    noção de "quase atingiu a margem"; um lado sem assunto próprio é um lado
    sem assunto próprio.

#### [v1.9.22] Deflação, neutralidade do §0, e o padrão de abertura

Três defeitos achados na **leitura** dos 17 vereditos `valorativo`
publicados sob a v1.9.21. Nenhuma métrica daquela versão os capturou, e é
por isso que a leitura continua sendo o aceite final.

##### Defeito 1 — deflação de quantificador, medida antes de corrigir

| Medição sobre os 35 publicados | Resultado |
|---|---|
| Filmes usando rótulo FORA do conjunto autorizado (mais forte **ou** mais fraco) | **0 / 35** |
| Filmes com deflação por hedge de magnitude | **2 / 35** (`pearl-2022`, `the-godfather`) |
| Filmes com algum rótulo de grupo ausente do texto | 2 / 35 |
| Pares (filme, grupo) com rótulo autorizado | 72, dos quais **61 usam o rótulo exato** |

**O defeito nunca foi o rótulo.** Foi o hedge que o SUBSTITUI (`pearl-2022`:
"impressões negativas pontuais") ou que o ENVOLVE (`the-godfather`: "relatos
pontuais apontam que a maioria…" — pontual e maioria na mesma oração). A
checagem da v1.9.21 olhava só o rótulo e por isso era cega aos dois.

**Por que é violação do §0 e não imprecisão de estilo.** Em `pearl-2022` as
negativas e as positivas têm a **mesma frequência** — 58% as duas, rótulo
`cerca de metade` nas duas. O lado positivo recebeu o rótulo; o negativo
virou anedota. Mesmo número, dois tratamentos, e o que os separa é o
**sentimento do grupo** — exatamente o que o §0 (neutralidade de tratamento,
a assimetria vem dos dados) existe para impedir.

**E recorreria.** A deflação veio da invariante de cautela com amostra
pequena, e amostra pequena não é distribuída ao acaso: `negativas` está em
modo reduzido em **5** dos 35 filmes e `positivas` em **2**, e **não existe
nenhum filme com positivas reduzida sem negativas também reduzida**. O
catálogo é majoritariamente bem avaliado, então o grupo sem material é quase
sempre o negativo — e uma regra que afrouxa a quantidade quando a amostra é
pequena afrouxa, na prática, sempre do mesmo lado.

**Medição de simetria, pedida e feita:** dos 35, **14 filmes** têm o mesmo
rótulo autorizado nos dois lados. **10 saem simétricos**; dos 4 assimétricos,
**1 é por deflação** (`pearl-2022`) e 3 por OMISSÃO — e a omissão não tem
viés de sentimento (`avengers-endgame` e `the-hateful-eight` calam o lado
positivo, `wonka` cala o negativo).

**O mapa de faixas da v1.2.3 NÃO muda.** 58% resolve para `cerca de metade`,
não para `a maioria`, porque a banda 40–60 vence `a maioria` (50–80) no
empate — a política de "sempre o rótulo mais fraco na fronteira
compartilhada". Duas razões para não mexer: é calibração intocada que
atravessa a narrativa dos 35 e o §D2 inteiro, e mudá-la a partir da leitura
de um filme seria alterar o produto por porta lateral (mesma classe da
margem de lift de 20pp, fechada na v1.9.21). A medição mostra que não é o
problema: no MESMO `pearl-2022`, o lado positivo com os MESMOS 58% recebeu
`cerca de metade` corretamente. O rótulo funcionou; o hedge é que não.

**Limitação aceita e não convertida em validação:** rótulo AUSENTE não é
rótulo errado (2 filmes). Num texto de 1–2 frases com teto de 55 palavras,
exigir quantificador para os três grupos estoura o orçamento e produz
rigidez. Há teste confirmando que as validações novas **não** forçam
presença de rótulo por efeito colateral.

##### Defeito 2 — a repetição migrou de LÉXICO para ESTRUTURA

O Jaccard caiu 7× na v1.9.21 e é cego a isto: **14 dos 17 filmes
`valorativo` abriam com uma fórmula de divergência** ("A divergência central
está…", "As opiniões divergem…"). As palavras de conteúdo de cada um são
distintas — a métrica não vê; quem navega três filmes seguidos vê.

**Métrica nova e permanente — o PADRÃO SINTÁTICO DE ABERTURA.** É o núcleo
do primeiro sintagma nominal (primeiro token de conteúdo fora da classe
fechada), truncado a 5 caracteres, com os **rótulos de quantificador
colapsados em `QUANT`**. Duas decisões, as duas medidas antes de fixar:

- **Sem o verbo.** A definição "núcleo + verbo principal" foi testada e
  descartada: sem analisador sintático o verbo sai por terminação, "está"
  colide com "esta" ao remover acento, e o primeiro verbo finito costuma
  estar dentro do sujeito ("dos que recomendam"). Ela reporta **22 padrões
  distintos contra 7** da definição sem verbo — **parece melhor porque é mais
  ruidosa**, e uma métrica que melhora o número por imprecisão é pior que não
  ter métrica.
- **Quantificador colapsado.** Qual rótulo abre a frase é decisão do CÓDIGO.
  Contar "A maioria…" e "Cerca de metade…" como aberturas diferentes
  creditaria ao modelo uma variedade que é do dado.

**O desempate por abertura, e a política de estabilidade que o torna
admissível.** A frequência do padrão entra na chave de seleção **antes da
brevidade** — âncoras → abertura menos frequente → menos palavras → primeiro
índice —, sobre os candidatos que o best-of-3 já gera, sem nenhuma chamada
nova. O risco era a saída passar a depender da ordem dos filmes; a política
fecha isso:

> O histórico é um **snapshot** dos padrões PUBLICADOS, tirado **uma vez,
> antes de qualquer escrita**, e o filme em geração sai da própria conta.
> Consequências: o resultado não depende da ordem (todo filme deriva do
> mesmo snapshot), e **regenerar um filme isolado vê o mesmo histórico que a
> regeneração completa veria para ele**. Um histórico atualizado no meio da
> execução seria mais eficaz e INSTÁVEL — o mesmo filme sairia diferente
> conforme fosse o primeiro ou o último da fila.

*Bug real achado ao implementar isso, e invisível para os testes que rodavam
contra um diretório de sandbox: o caminho de PRODUÇÃO grava em `resultado/`,
então recalcular o histórico a cada filme faria o segundo ver o veredito novo
do primeiro. O snapshot único é a correção, e há teste de regressão que
escreve por cima no meio do caminho e exige que o histórico não se mexa.*

##### [v1.9.23] A repetição MIGRA de dimensão — observação de método

**A cada correção, a repetição muda de camada, e a métrica vigente captura
exatamente a camada que acabou de ser consertada.** O histórico do estágio
[V], em três versões:

| Versão | Consertou | Métrica que provou | Para onde a repetição foi |
|---|---|---|---|
| v1.9.21 | texto byte-idêntico (19/35) | Jaccard sobre palavras de conteúdo | **abertura** — e o Jaccard não via |
| v1.9.22 | abertura (6 padrões/35) | padrão sintático de abertura | **molde contrastivo** — e o padrão de abertura não via |
| v1.9.23 | — (só mede) | conectivo contrastivo | ? |

**A regra que fica: estender a métrica ANTES de declarar vitória, não
depois.** Uma dimensão não medida não é uma dimensão sem defeito — é uma
dimensão sem número. Cada versão declarou vitória com o número da dimensão
que tinha acabado de instrumentar, e o defeito seguinte foi encontrado por
LEITURA, não por medição. A leitura continua sendo o aceite final; a métrica
serve para que o achado da leitura vire número e não volte.

##### [v1.9.23] Conectivo contrastivo — a métrica, e o que ela NÃO decide

**Definição:** o conectivo contrastivo PRINCIPAL de um veredito é o primeiro,
por posição no texto, de uma lista fechada — `ao passo que`, `em
contrapartida`, `por outro lado`, `em contraste`, `por sua vez`, `no
entanto`, `entretanto`, `todavia`, `contudo`, `enquanto`, `porém`, `embora`,
`ainda que`, `apesar de`, `já entre/já os/já as/já a/já o`, `mas`. Texto sem
nenhum deles recebe `nenhum` — o contraste pode estar só na pontuação ou na
oposição semântica, e inventar categoria onde não há tornaria a distribuição
uma ficção.

**Linha de base medida (catálogo sob a v1.9.22):**

| População | Conectivos distintos | Maior grupo |
|---|---|---|
| Os 35 | 7 | `enquanto` **18/35 (51%)** — seguido de `em contrapartida` 10/35 |
| Os 17 `valorativo` | 4 | `enquanto` **14/17 (82%)** |

**Nenhum dos 35 sai com `nenhum`:** o molde contrastivo é universal no
estágio.

> **Isto NÃO está registrado como defeito confirmado, e nada no código reage
> a ele.** Pode ser o **piso do gênero**: um produto cujo conteúdo É a
> divergência entre dois grupos tende ao período contrastivo, e não existe
> forma neutra de dizer "um grupo acha X, o outro acha o contrário" em
> português que não seja contrastiva. A métrica existe para que a decisão
> seja tomada com o número à vista — quem decide se 82% é problema é o dono
> do projeto, que é quem vê o produto em uso real.

##### [v1.9.23] `BEST_OF_N` maior — testado e REJEITADO, com o número

A v1.9.22 registrou que a seleção bateu num teto porque, em vários filmes,
os três candidatos abrem igual — e nomeou aumentar `BEST_OF_N` como a
próxima alavanca verificável. **Testada: não paga.** Dois braços com tudo
idêntico fora do N (mesmo modelo, mesmo briefing, mesmo snapshot de
aberturas, mesma ordem):

| | N=3 | N=6 |
|---|---|---|
| Aberturas distintas | 10 | 10 |
| Maior grupo de abertura | 16/35 | 14/35 |
| Três maiores | 27/35 | 27/35 |
| Fórmula de divergência (17 `valorativo`) | 12/17 | **13/17** |
| Conectivos distintos | 6 | 6 |
| `enquanto` nos 35 | 16/35 | **22/35** |
| `enquanto` nos 17 | 15/17 | 15/17 |
| Jaccard médio | 0,0578 | **0,0612** |
| Fallback / flags | 0 / nenhuma | 0 / nenhuma |
| **Custo** | 105 chamadas · 501s | **210 chamadas · 948s** |

**N=6 é PIOR em três dimensões, marginalmente melhor em uma, empatado em
duas — a exatamente o DOBRO do custo.** E a diferença observada não excede a
variância que o próprio N=3 tem entre execuções: o catálogo publicado (N=3)
está em 10/17 na fórmula de divergência e a rodada nova de N=3 deu 12/17, uma
banda de ±2 que engloba os 13/17 do N=6.

**A explicação, e é ela que fecha o assunto:** amostrar mais da mesma
distribuição rende mais da MODA, não mais da cauda. O desempate já escolhe a
melhor abertura disponível em 3 sorteios; 3 sorteios a mais acrescentam
sobretudo repetições da construção mais provável — visível no critério
decisivo, em que o `empate` sobe de 5 para 9. **O gargalo não é o número de
amostras, é a distribuição de saída do modelo.**

**Consequência registrada:** o único instrumento restante para o molde
contrastivo é o PROMPT — que continua sendo o mais fraco e o mais difícil de
verificar. Esta conclusão é o entregável; nada foi alterado.

##### [v1.9.23] Tautologia de um lado — DIAGNÓSTICO (não corrigido)

Quatro filmes têm um lado cujo conteúdo colapsa em reafirmação da própria
divergência — o defeito original da v1.9.21 (verdadeiro e inútil)
sobrevivendo em escala de oração:

| Filme | Oração tautológica | Lado |
|---|---|---|
| `avengers-endgame` | "a maioria dos que não recomendam discorda do resultado dessa comparação" | negativas |
| `mother-2017` | "discorda do resultado dessa mesma condução narrativa" | negativas |
| `dune-2021` | "recorre a comparações ao avaliar se a obra realmente funciona" | negativas |
| `cats-2019` | "recorre a comparações" | positivas |

*(`cats-2019` não constava do relato original; apareceu na varredura.)*

**Causa ÚNICA, e é de DADO:** nos quatro, o lado tautológico é exatamente
aquele cuja âncora de frequência tem **`tema = None`**. O briefing entrega o
rótulo do eixo ("comparações", "roteiro e estrutura") e nenhum conteúdo — a
linha `tema:` simplesmente não é emitida —, e o modelo preenche o vazio
reafirmando a divergência. É a mesma limitação já registrada para
`assunto_compartilhado` em `dune-2021` e `the-substance`, agora visível
também no bloco por GRUPO.

**Necessária, mas não suficiente.** **12 dos 72** pares (filme, grupo) têm
âncora de frequência sem tema, espalhados por 10 filmes — e só 4
tautologizam. Os outros 6 param na formulação honesta e fina: "centram suas
análises em comparações", que nomeia o eixo, atribui ao grupo e não inventa
nada. A diferença entre os dois desfechos é de REDAÇÃO, não de dado.

**Contraexemplo que enfraquece o conserto óbvio.** `dune-2021` **já recebe**
um aviso explícito de ausência de tema — *"(sem tema nomeado dos dois lados —
use só o nome do assunto, não invente detalhe)"* — e tautologiza mesmo
assim. O aviso existe no bloco do ASSUNTO COMPARTILHADO; a tautologia vem do
bloco do GRUPO, que é silencioso. Sinalizar no bloco do grupo é a hipótese
natural, mas o caso do `dune-2021` mostra que um aviso equivalente noutro
bloco não bastou — então o conserto é plausível, **não provado**.

**Estado: diagnosticado, não corrigido.** A decisão é do dono do projeto.

##### Defeito 3 — `the-godfather` lendo como lista

Empilhava ritmo, roteiro e comparações numa frase. Caso único entre os 35, e
a hipótese registrada era que o hedge truncado ("relatos pontuais apontam
que…") fosse parte da causa. **Confirmado: a correção do Defeito 1 o desfez**,
sem estrutura nova para um caso único.

#### Best-of-3, validações e seleção

Mesmo padrão de `narrador.narrar()` (§D2, v1.9.11), **reproduzido, não
reusado**. `selecao_narrativa.selecionar()` está acoplado ao formato de três
movimentos — `spans_por_grupo()` ancora no `rotulo_peso` literal, `cobertura()`
conta cláusulas por span de grupo, `ritmo()` exige ≥2 frases. Num texto de
1–2 frases sem rótulo de peso ancorado, esses três critérios nunca desempatam
nada: seria auditoria de aparência, não de fato. `qualidade.py` é reusado no
que se aplica (`tokens_numericos`, `formato_invalido`, `achar_resenha_speak`
+ `carregar_blocklist`, `_normalizar`).

**Validações pós-parsing — em CÓDIGO, nunca só no prompt:**

| Flag | O que reprova |
|---|---|
| `formato_invalido` | invólucro JSON, cerca de código, chaves desbalanceadas (§E2 v1.7.2) |
| `digito` | qualquer algarismo na saída |
| `quantificador_mais_forte` | rótulo acima do fornecido para aquele grupo |
| `tema_ausente` | tema/eixo que não está no briefing |
| `idioma` | saída fora de pt-BR |
| `comprimento` | acima do teto de palavras, ou mais de 2 frases |
| `escopo_generalizado` | "os críticos", "o consenso", "a recepção do filme", "o público" |
| `nota_ou_score` | marcadores de nota/estrela/score |
| `contraste_fabricado` | em filme `valorativo`, afirmação de que os grupos falam de coisas DIFERENTES |
| `cliche` | blocklist de resenha (`dados/blocklist_resenha.txt`) |

**Seleção:** candidato com `n_flags > 0` é eliminado — validação vem antes
de qualquer critério de qualidade, porque um texto que mente com riqueza
continua mentindo. Entre os limpos, **nenhum LLM julga prosa**, como em todo
o projeto: todo critério é contagem.

**Seleção entre candidatos limpos — chave DUPLA.** A primeira proposta desta
sessão foi "o mais curto", e foi **reprovada**: ela otimiza na direção exata
do defeito que a versão veio corrigir. Os 19 vereditos idênticos não eram
longos, eram **vazios** — entre candidatos que passam em todas as validações,
o mais curto tende a ser o mais genérico. A chave é:

1. **PRIMÁRIA — informatividade ancorada.** Quantas **âncoras substantivas
   distintas** do briefing o texto efetivamente nomeia. Mais âncoras vence.
2. **SECUNDÁRIA — brevidade.** Empate na primária desempata por menos
   palavras; empate total, pelo primeiro índice (arbitrário, determinístico).

**Âncora substantiva** = o `assunto_compartilhado` e o eixo de top-frequência
de cada lado, cada um com o conjunto de palavras de conteúdo do seu `tema` e
do rótulo do seu eixo.

Três guarda-corpos, todos obrigatórios:

- **TETO de 2 na chave primária.** Sem teto, o critério premiaria empilhar
  tema atrás de tema até estourar o limite de palavras — trocaria o defeito
  "vazio" pelo defeito "lista". Duas âncoras é o que um veredito de 1–2
  frases comporta.
- **Casamento por PALAVRAS DE CONTEÚDO, nunca por substring do `tema`.**
  Substring exata recompensaria copiar a string verbatim e a saída
  degeneraria em citação empilhada. A regra: normaliza (NFKD sem
  diacríticos, minúsculas, quebra em não-letras), descarta stopwords e
  tokens com menos de 4 caracteres, e compara por **prefixo de 5
  caracteres** — proxy declarado que absorve flexão (`ritmos`→`ritmo`) e
  **subconta** o que não absorve (`lentidão` não casa com `lento`).
  Subcontar é a direção certa: torna a chave primária mais difícil de
  satisfazer, nunca mais fácil. Uma âncora conta como nomeada quando
  `min(2, |palavras da âncora|)` das suas palavras aparecem no texto.
- **A cópia literal é REPROVADA, não premiada.** A validação
  `tema_verbatim` reprova o candidato cujo texto contenha a sequência
  completa de palavras de conteúdo de um `tema` do briefing (só para temas
  com 3+ palavras de conteúdo — um tema de uma ou duas palavras não é
  copiável, é a única forma de nomeá-lo). O modelo tem de dizer o assunto
  com as palavras dele.

**Verificado nos 35 antes de implementar:** nenhum filme fica com menos de 2
âncoras disponíveis, inclusive os dois sem `tema` no eixo compartilhado
(`dune-2021`, `the-substance`) — cada um deles tem, no top-frequência de
algum lado, uma âncora com tema nomeado de verdade. Se algum ficasse com zero
ou uma, a chave primária seria CONSTANTE naquele filme e a escolha cairia
inteira na brevidade — exatamente o critério reprovado.

> **Se a medição da Entrega 7 mostrar que este critério seleciona texto
> EMPILHADO em vez de fluente, ele é o primeiro parâmetro a revisar.** A
> hipótese sob teste é a informatividade ancorada, não a brevidade.

#### O que estas validações DECLARADAMENTE não pegam

Duas delas são proxies, e registrar o alcance é o que impede que "passou nas
validações" seja lido como "está correto":

> **Três falsos positivos MEDIDOS na primeira geração dos 35, e corrigidos
> antes do A/B valer.** O custo de um falso positivo aqui é caro e concreto:
> ele elimina candidatos bons e empurra o filme para `template_fallback` — ou
> seja, **devolve ao leitor exatamente a frase genérica que esta versão veio
> eliminar**. (1) O marcador `tom` casava como SUBSTRING dentro de "tomam",
> "sintoma" e "átomo", reprovando por `tom_atmosfera` um texto que só dizia
> "decisões que eles tomam" — mesma família do bug de substring da v1.6.2
> (`"1%"` casando dentro de `"91%"`), e mesma correção: fronteira de token
> explícita. Marcadores passam a casar TOKEN INTEIRO por padrão, e por
> PREFIXO só quando escritos com `*` (`arrastad*`). (2) `desenvolvimento` saiu
> de `roteiro_estrutura`: "desenvolvimento arrastado" é RITMO,
> "desenvolvimento dos personagens" é ROTEIRO, e um marcador que casa nos
> dois não discrimina nada — custou `hereditary`. (3) `incomod*` saiu de
> `impacto_emocional`: incômodo é como se descreve qualquer coisa de que não
> se gostou, inclusive uma personagem irritante, que é `roteiro_estrutura` —
> custou `pearl-2022`. Os três viraram teste de regressão.

- **`tema_ausente` detecta EIXO, não tema.** O eixo tem vocabulário fechado
  (10 itens, §2.5) e um `tema` não tem; checar tema a tema exigiria casamento
  por SIGNIFICADO, que só um segundo LLM faz — e este projeto não põe LLM
  para julgar saída de LLM. Consequência: um texto que invente um detalhe
  DENTRO de um eixo que o briefing cita passa. A rede que resta contra isso é
  a fidelidade pedida no prompt e a leitura humana do aceite.
- **`contraste_fabricado` é por MARCADOR DE FRASE.** Ela pega a afirmação
  explícita ("falam de coisas diferentes", "discordam sobre qual é o
  assunto"); não pega uma insinuação construída só pela estrutura da frase.
  O que fecha boa parte da folga é indireto e vale registrar: num filme
  `valorativo` o briefing costuma ter pouquíssimos eixos, então nomear um
  segundo assunto normalmente já trip `tema_ausente`. **A verificação de
  aceite dos 17 `valorativo` NÃO usa esta validação** — usaria a mesma
  checagem para se auto-aprovar. Ela usa uma lista de marcadores
  independente e mais larga, mais leitura humana dos 17 textos.

**Fallback obrigatório, em dois degraus:**

1. Nenhum candidato limpo → o de **menor severidade** entra num retry
   direcionado, com as flags disparadas explicadas (mesma mecânica do retry
   de §D2).
2. Esgotadas as tentativas sem candidato limpo → o filme cai no **TEMPLATE
   DETERMINÍSTICO** da v1.9.19/v1.9.20, que permanece no código, e
   `origem` grava `template_fallback`.

**Nunca fica sem veredito; nunca publica veredito inválido.** O template é a
rede, e é a mesma rede que o frontend usa para JSON antigo (abaixo).

#### Persistência e render

`build_data.py` copia o JSON de resultado inteiro e verbatim (menos
`origem_paginas`), então a chave nova viaja para `frontend/js/data.js` sem
nenhuma edição naquele arquivo.

Em `filme.js`, `veredictoBlock()` passa a preferir `f.veredito.texto` quando
existe. **A função `veredito()` NÃO é deletada** — vira o fallback de render
para filme sem o campo novo (compatibilidade com JSON publicado antes desta
versão) e continua sendo a rede que o estágio [V] usa em `template_fallback`.

> **`teste-degradado` fica DELIBERADAMENTE sem o campo `veredito`.** O filme
> sintético de `build_data.py` existe para exercitar os caminhos que os 35
> reais não têm; a partir desta versão ele exercita também o **fallback de
> render por compatibilidade**. Não é esquecimento — está registrado aqui e
> no comentário do próprio `_filme_degradado()`, porque sem isso a próxima
> pessoa a mexer no arquivo "conserta" a ausência e apaga a cobertura.

#### O veredito deixa de ser 100% determinístico — o registro honesto

Até a v1.9.20 o veredito era função pura do JSON: mesma entrada, mesma saída,
byte a byte, para sempre. **Não é mais.** Duas execuções do estágio sobre o
mesmo filme podem produzir textos diferentes, pela mesma variância entre
chamadas que a v1.7.3 já mediu e registrou.

**Por que isso NÃO viola "código é autoridade sobre números" (§0, v1.1.1):**

- O modelo não vê número nenhum — a serialização do briefing não tem
  algarismo (acima). Ele não pode calcular, arredondar ou inflar o que nunca
  recebeu.
- O modelo não escolhe **qual** eixo, **qual** tema, **qual** grupo, **qual**
  rótulo de intensidade nem **qual** estado de contraste. Todos são resolvidos
  em `veredito.py`, em código puro, antes de qualquer chamada.
- O percentual de peso do meio dominante — o único número que sobrevive no
  texto renderizado — é **prefixado pelo código**, fora da saída do modelo.
- Validação em código reprova o que o prompt proíbe, e o fallback determinístico
  é o piso.

O que o modelo decide é **como escrever**: exatamente a fronteira já
estabelecida e validada em §D2 desde a v1.9.8. O estágio novo não é exceção
ao princípio; é a quarta aplicação dele.

**O que se PERDE, dito sem maquiagem:** reprodutibilidade byte a byte do
texto publicado, e a garantia trivial de que dois filmes com o mesmo formato
de dado recebem a mesma frase. A primeira é custo aceito (a telemetria grava
modelo, candidatos e flags, então a escolha é auditável mesmo sem ser
reproduzível). A segunda é precisamente o que esta versão quer perder.

#### O risco central desta mudança

**17 dos 35 filmes são `contraste: valorativo`, e são EXATAMENTE os 17 que
caem no ramo sem contraste** (medido na v1.9.21: nenhum filme `valorativo`
escapa do ramo; os outros 3 filmes do ramo são `tematico` com o contraste
morando só no bucket do meio). Isso torna a verificação anti-fabricação uma
varredura de POPULAÇÃO INTEIRA, não de amostra.

O risco: um modelo solto sobre um briefing pobre ("nenhum eixo passa a
margem") produz **20 maneiras diferentes de dizer a mesma coisa vazia** —
variedade de redação sem variedade de informação. Isso é **pior que a
repetição atual**, porque disfarça um achado real de homogeneidade como se
cada filme fosse diferente. A proibição de fabricar diferença de assunto
(invariante 3) e o campo `assunto_compartilhado` são a resposta a esse risco,
e o critério de aceite da versão os mede diretamente.

#### Critério de aceite (v1.9.21)

Medido ANTES e DEPOIS com a MESMA implementação de contagem:

| Métrica | Antes (v1.9.20) | **Publicado** (flash) | pro (braço B do A/B) |
|---|---|---|---|
| Vereditos byte-idênticos entre si (maior grupo) | **19** | **0** | 0 |
| Filmes em algum grupo duplicado | 25 | **0** | 0 |
| Textos distintos / 35 | **14** | **35** | 35 |
| Abertura compartilhada (5 primeiros tokens) | 29 | **15** | 13 |
| Aberturas distintas | 10 | **26** | 27 |
| Sobreposição lexical média entre pares (Jaccard sobre palavras de conteúdo) | **0,3744** | **0,0601** | 0,0526 |
| Jaccard máximo entre pares | 1,0 | 0,3333 | 0,2593 |
| Palavras (média / máximo) | 16,6 / 31 | 41,4 / 58 | 45,5 / 59 |
| Origem | — | **35 llm / 0 fallback** | 34 llm / 1 fallback |
| Flags disparadas | — | **nenhuma** | `tema_ausente`: 1 |

**A sobreposição lexical média caiu 6,2×** e a repetição byte-idêntica foi a
zero. A métrica é Jaccard sobre `palavras_de_conteudo` normalizadas, média
sobre os 595 pares — mesma implementação nos dois lados da comparação.

**O critério de âncoras NÃO produziu texto empilhado**, que era a hipótese
sob teste e o risco de troca-de-defeito: a chave primária decidiu 11 de 35
(brevidade decidiu 15, "único" 3, empate 6), e a média de palavras ficou em
41,4 contra um teto de 55 — se ela estivesse premiando empilhamento, a média
estaria colada no teto. O teto de 2 âncoras cumpriu o papel.

**Verificação anti-fabricação nos 17 `valorativo` — ZERO ocorrências, nos
dois braços do A/B.** Duas checagens independentes, e a independência é o
ponto: (a) uma lista de 32 marcadores que é SUPERSET da validação
`contraste_fabricado` — usar a própria validação devolveria "limpo" por
construção, já que todo texto publicado passou nela; (b) leitura dos 17, em
que **17/17** nomeiam o assunto compartilhado e enquadram a divergência como
de julgamento. *(A checagem automática contou 16/17 em cada braço; os dois
"faltantes" fazem o enquadramento com palavras fora da lista de marcadores —
"A avaliação do roteiro divide as opiniões", "O ponto de discórdia está no
julgamento". A régua subcontou; os textos estão corretos.)* **Qualquer
ocorrência de contraste fabricado é falha de aceite, não detalhe de
redação.**

#### Modelo — configurável, nunca hardcoded, nunca alias

Chave `"veredito"` em `PROVIDER_POR_ESTAGIO` e `MODELO_POR_ESTAGIO`
(`config.py`) — único ponto de configuração, resolvido por
`synthesize.provider_do_estagio`/`modelo_do_estagio`, passando pelo adaptador
e pelo guard-rail de §3[D].

**Inventário da chave, consultado na API (não de memória), 2026-08-25:** o
tier `pro` disponível é **`gemini-3.1-pro-preview`** (`version:
3.1-pro-preview-01-2026`) e não existe tier acima dele. O flash mais recente
é `gemini-3.7-flash` (`3.7-flash-08-2026`), **sete meses mais novo que o
único pro disponível**. `gemini-pro-latest` existe e é REJEITADO por política
(v1.9.10: alias é alvo móvel — comparação não reproduzível, preço não
ancorável).

Tensão registrada: a comparação de modelos da v1.9.10 mediu
`gemini-3.1-pro-preview` PIOR que `gemini-3.7-flash` no narrador (2 flags
contra 1, ~10× o custo), em amostra de 3 filmes. Resolvida do jeito que este
projeto resolve as coisas — **por medição**: o A/B da v1.9.21 roda o critério
de aceite INTEIRO nos dois braços (as três métricas de repetição, taxa de
flag, taxa de `template_fallback`, os 20 textos do ramo na íntegra por
modelo, e a verificação anti-fabricação nos 17 por modelo), com briefing,
prompt, best-of-3, validadores e ordem de filmes IDÊNTICOS — a única variável
é o modelo. **Conformidade não decide sozinha:** um modelo pode passar limpo
em todas as validações e ainda produzir 35 vereditos corretos, insossos e
intercambiáveis, que é exatamente a falha que esta versão existe para evitar.
Empate em qualidade legível desempata por custo, e aí o flash vence. O
default efetivo é decisão do dono do projeto lendo os textos, registrada no
changelog.

### [F] Ficha do filme (TMDB) — v1.3.0

Etapa **aditiva e independente** do resto do pipeline (`ficha.py`): dado o título/ano do filme (derivados do slug por default — `titulo_ano_de_slug`, com override via `--titulo`/`--ano` no CLI para os casos em que o slug não carrega ano, ex. `cure`), busca a ficha técnica na API pública do TMDB (`api.themoviedb.org/3`).

**Resolução do ID:** `GET /search/movie?query=<título>&language=pt-BR[&year=<ano>]`. Quando `ano` está disponível, é usado tanto como parâmetro de busca quanto para desambiguação pós-resposta: entre os candidatos com `release_date` no ano pedido, prefere o de maior `popularity` do TMDB — **não** o primeiro da lista. Necessário porque títulos comuns podem devolver mais de um candidato do MESMO ano (ex. "The Invite" tem múltiplas entradas no TMDB; "Cure" 1997 devolve o filme de Kiyoshi Kurosawa E um documentário obscuro do mesmo ano) — a ordem da API não é por relevância quando o filtro de ano está ativo. Medido ao vivo na regeneração da v1.3.0: escolher o primeiro resultado do ano pegou o documentário (`popularity=0.28`, 1 voto) em vez do filme correto (`popularity=3.79`, 820 votos); corrigido para desempate por popularidade antes da entrega.

**Resolução de ano confiável (v1.7.0) — Tarefa 1.** Defeito real: `espectro24 --slug cure` sem `--ano` desambiguava só pelo TÍTULO (nenhum ano para filtrar), e o TMDB devolveu como único candidato "The Cure" (2026, dir. Nancy Leopardi) — um filme completamente diferente — sem nenhum aviso. A cadeia de resolução do ano passa a ter três degraus, nesta ordem, cada um só tentado se o anterior não resolveu: **(a)** sufixo `-YYYY` do slug (`titulo_ano_de_slug`, já existia); **(b)** se ausente, **1 requisição** à página principal do filme no Letterboxd (`resolver_ano_letterboxd`, `ficha.py`) — mesmo `fetcher`/cache/headers/delay do resto do pipeline, extrai o ano do link `/films/year/YYYY/` ou do `<meta property="og:title">` (formato "Título (YYYY)"); falha de rede/ausência de ano → `None`, nunca levanta; **(c)** se AINDA assim indisponível, a ficha **não é buscada** — o pipeline segue sem ela (`output["ficha"] = None`, `output["ficha_indisponivel"] = "ano_desconhecido"`) em vez de arriscar a desambiguação cega que causou o defeito. O campo `ano_fonte` (`"slug" | "letterboxd" | "argumento"`) entra na própria ficha, sempre visível.

**Guarda de sanidade — ano divergente descarta a ficha inteira (v1.7.0, Tarefa 1.2).** Mesmo com ano resolvido, o TMDB pode devolver o candidato errado quando NENHUM resultado da busca tem `release_date` no ano pedido (o código então cai para o primeiro resultado da lista, que pode ser de qualquer ano — o próprio modo de falha do defeito real do `cure`). Depois de montar a ficha, se o ano esperado (nunca o do próprio resultado do TMDB — seria circular) divergir do `ano` da ficha em mais de 1, a ficha inteira é DESCARTADA: `buscar_ficha` retorna `(None, aviso, {"motivo": "ano_divergente", "esperado": X, "recebido": Y})`, e o CLI persiste esse dict em `output["ficha_descartada"]`. Melhor nenhuma ficha do que a ficha de outro filme. A ficha descartada por esse motivo NÃO é cacheada como "não encontrado" — uma nova tentativa (ex. com um título mais preciso) não fica travada numa rejeição antiga.

**Detalhes:** `GET /movie/{id}?language=pt-BR&append_to_response=credits`. Extraídos: título pt-BR (`title`), sinopse oficial (`overview`), gêneros (`genres[].name`), duração (`runtime`), diretor (primeiro `credits.crew[]` com `job == "Director"`), ano (`release_date[:4]`).

**Imagens — PÔSTER e backdrops (v1.9.29).** A mesma chamada de detalhes passa a pedir `append_to_response=credits,images&include_image_language=pt,null`. **Custo marginal de rede ZERO** — nenhuma requisição nova, `images` entra no `append_to_response` que já trazia `credits`.

**`include_image_language` é obrigatório, e o valor é `pt`, NÃO `pt-BR`.** Duas medições ao vivo (2026-08-27) sustentam as duas metades da frase. (a) *Obrigatório:* `language=pt-BR` filtra também o bloco `images`, e a esmagadora maioria dos backdrops não declara idioma — sem o parâmetro o campo volta VAZIO para filmes com pouca cobertura pt-BR e o sintoma parece "este filme não tem imagens". Medido: `eighth-grade` 1 pôster / **0 backdrops** sem o parâmetro contra 2 / 18 com ele; `the-invite-2026` 4 / **0** contra 10 / 21; o curta experimental (id 1079736) **0 / 0** contra 1 / 0; `the-godfather` 6 / 4 contra 21 / 102. (b) *`pt`, não `pt-BR`:* o parâmetro aceita códigos **ISO-639-1**, e um código de LOCALIDADE é descartado em **silêncio** — com `pt-BR,null` só o degrau `null` sobrevive. O sintoma não é um erro, é um dado faltando sem aviso: dos 9 filmes sondados, **7** (`aftersun`, `anatomy-of-a-fall`, `cats-2019`, `cure`, `hereditary`, `the-northman`, `wonka`) ficaram **sem as dimensões do pôster** com `pt-BR,null`, porque o `poster_path` que o TMDB escolheu é uma arte `iso_639_1='pt'` que o filtro tinha jogado fora; com `pt,null`, nenhum ficou.

**O pôster é o `poster_path` do PRÓPRIO TMDB — a cascata não foi reimplementada, e isso foi MEDIDO antes de decidir.** A política pedida (pt-BR → arte sem idioma → idioma original → melhor avaliado) já é o que aquele campo entrega: ele é sensível a `language`. Medido: `napoleon-2023` devolve `/2UY2xfk…` (`iso_639_1='pt'`) em pt-BR e `/ytFOXyg…` em en-US — a localidade é respeitada; o curta experimental, que só tem arte SEM idioma, devolve a mesma imagem nas duas localidades — o degrau neutro também. Reescrever a cascata em código seria refazer, com menos informação, uma escolha que a API já faz — e divergir dela em silêncio no dia em que ela mudasse de critério.

**As DIMENSÕES, essas, o campo não traz** — e são obrigatórias para o frontend reservar a proporção antes de carregar (§3[E]). O `poster_path` escolhido é procurado dentro de `images.posters`, que traz `width`/`height` reais. Elas **não são sempre 2:3**: medido no catálogo, `aftersun` é 1632×2449 (0,666) e o curta experimental é 505×750 (0,673). Se o caminho não aparecer na lista, as dimensões ficam ausentes e o frontend cai na razão padrão — ausência é estado válido, nunca erro.

**`backdrop_paths[]` — a LISTA continua coletada e não percorrida; o
ESCOLHIDO passa a ser renderizado (v1.9.30).** Teto de **10** por filme
(`TETO_BACKDROPS`), na ordem que a API devolve. **Até a v1.9.29 nenhum
backdrop era renderizado**, e a razão registrada era esta: o TMDB não
garante que um backdrop seja livre de spoiler, e *"0 spoilers para quem
ainda não assistiu"* é a promessa central do produto (§0). **Esse fato
continua verdadeiro; o que mudou foi a decisão sobre ele.** Na v1.9.30 o
dono do projeto decidiu, com o trade-off explicitamente na mesa, abrir a
página do filme com **um** backdrop, sem curadoria de spoiler — **exceção
explícita ao §0**, registrada por extenso em §3[E], "O BACKDROP no topo da
página do filme". **Não existe galeria**, e a distinção não é retórica: a
lista continua sendo dado guardado que arquivo nenhum do frontend percorre;
o frontend lê `backdrop_path`, o campo do escolhido.

**A ESCOLHA É DO CÓDIGO, por uma ORDEM TOTAL (v1.9.30).** Ao contrário do
pôster — onde a cascata pedida já era o que o `poster_path` da API entrega —
aqui não há nada para reaproveitar: o TMDB não expõe campo de topo para "o
melhor backdrop" nem para "a arte sem texto". `_ordem_imagem`/`_melhor`
(`ficha.py`) ordenam por **(1)** sem texto sobreposto (`iso_639_1 is None`,
preferência e não filtro), **(2)** `vote_average` desc, **(3)** `vote_count`
desc, **(4)** `width` desc, **(5)** `file_path` asc. O último degrau é o que
fecha a ordem total. A escolha sai de dentro de `backdrops[:TETO_BACKDROPS]`
— o `backdrop_path` é sempre um dos itens de `backdrop_paths[]`, e isso é
travado por teste. Racional degrau a degrau, com as três medições que o
sustentam, em §3[E].

**O PÔSTER SEM TEXTO (v1.9.30)** — `poster_sem_texto_path` e dimensões: a
melhor arte de `images.posters` com `iso_639_1: null`, pela mesma ordem.
**Aqui o `iso_639_1 is None` é FILTRO, não preferência:** arte com idioma
declarado tem texto sobreposto por definição, e devolvê-la neste campo seria
devolver a coisa que ele existe para evitar. Campo próprio, **aditivo**: não
substitui `poster_path`. Medido nos 35: **todos têm**; em 1
(`talk-to-me-2022`) coincide com o próprio `poster_path`.

**CUSTO MARGINAL DE REDE ZERO, confirmado.** Os dois campos novos saem do
**mesmo bloco `images`** que a v1.9.29 já pedia, com o mesmo
`include_image_language=pt,null` — nenhuma requisição nova, e o teste
`test_os_campos_novos_nao_custam_UMA_requisicao_a_mais` trava isso contando
as chamadas a `/movie/{id}`.

**As DIMENSÕES do backdrop vêm junto**, pelo mesmo motivo das do pôster: sem
elas o frontend não reserva a proporção antes de carregar e o ganho de CLS
zero da v1.9.29 regride — e aqui regrediria **pior**, porque a caixa é mais
alta (§3[E], a tabela de medição). Elas vêm da própria entrada de
`images.backdrops`, que traz `width`/`height`; não são todas 16:9 (medido:
`eighth-grade` é 3500×1969).

**RASTREABILIDADE — `tmdb_fetched_at`, e vale para TODOS os campos derivados do TMDB**, não só as imagens: título, sinopse, diretor, gêneros, duração, pôster e backdrops vêm todos da mesma resposta, no mesmo instante, e um carimbo por campo seria a mesma data repetida sete vezes. **Por que ele existe:** os termos de uso da API do TMDB proíbem **cachear por mais de 6 meses** qualquer informação obtida através dela, e o projeto guarda dados de ficha **indefinidamente** em `resultado/*.json` desde a v1.3.0. **Isto NÃO é problema novo criado pelos pôsteres — é uma limitação PRÉ-EXISTENTE que os pôsteres tornam visível.** Esta versão **não** constrói cache, revalidação, expiração nem coleta de lixo, deliberadamente: a entrega é só a data de obtenção, que é o que torna uma política de revalidação possível depois. Sem ela não há sequer como saber o que está vencido. A intenção fica registrada aqui; a implementação é de outra versão.

**O TMDB não estende nenhum direito sobre as imagens.** O copyright dos pôsteres é dos estúdios e distribuidores; o TMDB apenas hospeda e declara não reivindicar propriedade sobre as imagens da API. Nenhum binário é baixado ou versionado (§3[E]): o JSON guarda só `file_path`, e a imagem vem do CDN.

**Cache de ficha de uma versão anterior — a checagem de COMPLETUDE.** Uma entrada gravada antes de uma versão que acrescenta campo de imagem não tem esse campo. Devolvê-la como está produziria o pior sintoma possível — *"este filme não tem pôster"*, *"não tem backdrop"* — para um filme que tem, sem nenhum aviso. Uma entrada **incompleta** conta como **MISS** e é refeita por cima. Não é expiração (que o projeto continua não construindo, por decisão); é uma entrada de formato antigo sendo reconhecida como incompleta.

**[v1.9.30] A checagem deixou de ser o `tmdb_fetched_at` da v1.9.29 e passou a ser a LISTA de chaves que a versão corrente escreve (`_CHAVES_COMPLETUDE`), e a lição vale registrar porque ela quase mordeu.** A regra da v1.9.29 olhava só o carimbo — e as 35 entradas em cache **já o tinham**. Mantida como estava, esta versão teria devolvido `backdrop_path` e `poster_sem_texto_path` ausentes, em silêncio, para os 35: o defeito exato que aquela regra existia para evitar, repetido um degrau adiante. É **presença de chave**, não valor verdadeiro: `backdrop_path: None` é resposta válida (filme sem backdrop) e não pode forçar uma requisição nova a cada execução. **Ao acrescentar campo de imagem, acrescente à lista.**

**Campos de imagem na ficha:** `tmdb_id`, `tmdb_fetched_at`, `poster_path`, `poster_largura`, `poster_altura`, `backdrop_paths[]` (v1.9.29) e — **v1.9.30** — `backdrop_path`, `backdrop_largura`, `backdrop_altura`, `poster_sem_texto_path`, `poster_sem_texto_largura`, `poster_sem_texto_altura`. **Aditivos por design, como toda a ficha desde a v1.3.0:** qualquer falha (rede, HTTP, filme sem imagem, chave ausente) nunca bloqueia coleta, publicação ou render. **Ausência de pôster é estado válido, não erro.**

**Retrofit dos 35 — `scripts/enriquecer_ficha.py` (v1.9.29).** Os filmes já publicados ganham os campos novos **sem re-rodar o pipeline**: harness próprio, no espírito de `scripts/gerar_veredito.py` (v1.9.21) e da trava por teste da v1.9.25. Ele lê o JSON em disco, faz UMA consulta ao TMDB e grava só as chaves acima dentro do bloco `ficha`. Não chama coleta, seleção, classificação, verificação, síntese, [D3], narrativa nem veredito; **não passa pela guarda de lote de `publicar_catalogo.py` (`LIMITE_LOTE_SEM_CONFIRMACAO = 5`) e não deve — e também não a contorna:** publicar continua inalcançável dali, inclusive por caminho indireto. `tests/test_enriquecer_ficha.py` trava as quatro coisas substituindo os pontos de entrada por `pytest.fail` e comparando o documento campo a campo. Ele carrega ainda uma **guarda de identidade**: reconsultar o TMDB reabre a desambiguação que o pipeline já fez, então se a resposta descrever outro filme (título, ano ou diretor divergentes) o filme é abortado sem gravar — melhor ficar sem pôster do que colar o pôster de outro filme numa página publicada. Ela disparou de verdade em `mother-2017` e apontou uma causa real: buscar pelo `ficha.titulo` (o título pt-BR, `"mãe!"`) em vez do título do slug resolve outro filme ("Perfeita é a Mãe 2"). O harness passou a usar o título do SLUG, como o pipeline usa. **Resultado medido (v1.9.29): 35 de 35 filmes com pôster, 0 sem, 0 falhas.**

**Retrofit da v1.9.30 — mesmo harness, mesmas travas, `CHAVES_NOVAS` maior.** Os seis campos da v1.9.30 entraram pelo mesmo passe, com a guarda de lote continuando inalcançável e a **guarda de identidade** (a que pegou `mother-2017`) em vigor. **Resultado medido: 35 de 35 processados, 0 falhas; 34 com backdrop e 1 sem (`talk-to-me-2022`); 35 com arte sem texto e 0 sem.** Diff dos `resultado/*.json` conferido campo a campo contra o `HEAD` anterior: **nada mudou fora do bloco `ficha`**, e dentro dele mudaram exatamente os seis campos novos mais `tmdb_fetched_at` — que é o carimbo da nova consulta e está em `CHAVES_NOVAS` desde a v1.9.29. `poster_path`, as dimensões do pôster e `backdrop_paths[]` vieram **idênticos** aos de antes, o que é a confirmação independente de que a reconsulta resolveu os mesmos 35 filmes.

**RESSALVA MEDIDA, PRÉ-EXISTENTE E NÃO CORRIGIDA AQUI — `talk-to-me-2022` publica a ficha de OUTRO FILME.** O slug é o de *Talk to Me* (2022, Danny e Michael Philippou), e a ficha em `resultado/talk-to-me-2022.json` é a de **"The Elms Estate: You Can Talk To Me"** (`tmdb_id` 976680), um curta de **3 minutos** dirigido por George Williams — título, sinopse, diretor, duração e pôster, todos do filme errado, publicados desde a v1.3.0. É uma falha da desambiguação do TMDB por título, do mesmo tipo que a guarda de ano da v1.7.0 foi escrita para pegar e que ela não pega neste caso (os dois são de 2022). A **guarda de identidade** do retrofit não a detecta por construção: ela compara o disco com a resposta nova, e as duas são o mesmo filme errado. **É também a razão real do único "sem backdrop" do catálogo** — não é escassez de acervo (o *Talk to Me* verdadeiro, `tmdb_id` 1008042, tem 49 backdrops); é que o curta não tem nenhum. **Não corrigido nesta versão de propósito:** o conserto trocaria `titulo`, `sinopse_oficial`, `diretor` e `duracao_min` — campos fora de `CHAVES_NOVAS` — e a narrativa e o veredito publicados desse filme foram escritos sobre a ficha errada, o que faz do conserto uma **republicação**, não um retrofit.

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

   **(v1.9.26) A PÁGINA DO FILME, ordem publicada.** O frontend divergiu do
   render de terminal em ORDEM e em ÊNFASE — o terminal continua como
   descrito acima; `filme.html` é o que o leitor vê, e nele a ordem é:

   1. ano + título
   2. botão "reviews no Letterboxd"
   3. ficha (sinopse + linha de metadados)
   4. **BARRA DE PROPORÇÃO** + o disclaimer da cota logo abaixo dela
   5. linha arco-íris
   6. bullets por sentimento (dois blocos, ou três sob a exceção do §0)
   7. **VEREDITO** (§3[V])
   8. narrativa completa, colapsada
   9. micro-pesquisa

   **(v1.9.32) A ORDEM ATUALIZADA.** A lista acima é a da v1.9.26 e fica
   como registro histórico. A publicada hoje:

   1. **BACKDROP** dissolvido no fundo (v1.9.30, refeito na v1.9.32), com
      **ano + título começando SOBRE a imagem**, dentro do fade
   2. linha de metadados — **DIRETOR EM CAIXA ALTA** · gêneros · duração ·
      fonte TMDB, solta, sem card (a **SINOPSE SAIU** na v1.9.32)
   3. "reviews no Letterboxd ↗", **link secundário** (deixou de ser pill)
   4. **RECEPÇÃO** (etiqueta de seção) + **BARRA DE PROPORÇÃO** + callout de
      percentual + legenda HATERS · MIXED · FANS
   5. linha arco-íris + **EM DETALHE · TEMA A TEMA** (etiqueta de seção,
      de volta — ver abaixo)
   6. bullets por sentimento, **ordenados por peso** (v1.9.30)
   7. **VEREDITO** (§3[V]) — inalterado
   8. narrativa completa, colapsada — inalterada
   9. micro-pesquisa — inalterada

   Os itens 7, 8 e 9 não foram tocados pela v1.9.32 e continuam exatamente
   onde estavam; o rodapé com a atribuição ao TMDB também.

   **A BARRA DE PROPORÇÃO** é a divisão dos três grupos numa faixa
   **contínua**, largura proporcional ao peso real, na ordem de leitura de
   sempre. Ela lê `share_real` — a MESMA fonte que os cabeçalhos de grupo
   imprimem, e não `distribuicao.por_bucket`, que carrega os mesmos
   valores: uma fonte só por fato é o que impede a barra e os cabeçalhos de
   divergirem em silêncio. **Nenhum número dentro da barra** (os
   percentuais continuam nos cabeçalhos), e a alternativa textual é o
   `aria-label` com rótulo e peso dos três — número permitido pela v1.9.20,
   que proibiu contagem bruta de review e não proporção.

   **CONTÍNUA quer dizer SEM VÃO, e isso é requisito, não acabamento.** A
   primeira rodada desta versão separava as três faixas com 3px de respiro
   escuro e foi rejeitada pelo dono do projeto com o diagnóstico certo: a
   barra "não dá ideia de continuidade — parece que são três barras
   separadas, cortadas com vão no meio". O erro era conceitual. A recepção
   de um filme é **uma população particionada em três**, não três medições
   independentes; um vão entre as faixas desenha três objetos onde o dado
   tem um só. A barra publicada tem zero gap, zero fio separador e zero
   respiro escuro entre faixas.

   **A fronteira é uma DIAGONAL**: uma cor terminando e a outra começando.
   Desenhada por camadas empilhadas (cada cor começa na borda esquerda e
   termina na sua fronteira, a última preenchendo a barra), porque fatias
   lado a lado com aresta inclinada deixariam um triângulo vazio em cada
   fronteira — o vão de novo. A diagonal fica **centrada** na fronteira
   verdadeira, então ela empresta área de um lado e devolve do outro: na
   meia altura da barra, o limite está exatamente no percentual (medido em
   `napoleon-2023`: 22,000% contra um cabeçalho de 22%).

   **A DIAGONAL É ADAPTATIVA, porque senão ela come a fatia estreita.** A
   pior do catálogo é `the-godfather`, com 2% em negativas. A projeção
   horizontal da diagonal é `clamp(3px, 0,55 × menorFatia, 12px)`, e o
   cálculo mora no **CSS**, não no JS: o percentual da menor fatia é DADO
   (o JS grava `--menor-pct` uma vez), e a conversão para pixel usa `cqw`,
   que reage a resize sozinha. A primeira implementação usou
   `ResizeObserver` e foi trocada — media em JS uma coisa que o CSS já
   sabe, e um observador que não dispara deixaria o ângulo errado sem
   sintoma visível. Medido: a fatia de 2% mede 14,40px de média em desktop
   (720px de barra) e 6,70px em mobile (335px); no ponto mais fino da
   diagonal, 10,91px e 5,07px — a diagonal encolhe sozinha no mobile
   (7,9px → 3,7px) exatamente para a fatia sobreviver.

   **A marca da fronteira, e por que ela não é um vão.** Sem respiro, a
   distinção entre faixas adjacentes passaria a depender só do contraste
   entre as cores. Cada camada recebe um `drop-shadow` de 1px que, por
   acompanhar o `clip-path`, traça **exatamente a diagonal e só ela**. É
   uma dobra, não um corte: as cores continuam encostadas.

   **A VARIANTE ALTERNATIVA, e por que não foi a escolhida.** Uma segunda
   proposta desta rodada foi um **diverging stacked bar** (Heiberger &
   Robbins, *Journal of Statistical Software* 57(5), 2014) — o meio
   ancorado no centro, a cavaleiro sobre um zero, com negativas crescendo
   para a esquerda e positivas para a direita. É a técnica que a
   literatura recomenda como primária para escalas ordenadas de opinião
   com centro neutro, e a ressalva honesta era que parte do valor do
   padrão vem de comparar VÁRIAS linhas contra a mesma linha-base — a
   página do filme tem uma só. **O dono do projeto comparou as duas e
   escolheu a contínua.** A implementação da divergente foi removida do
   JS e do CSS junto com a escolha; se precisar voltar, o histórico do git
   tem a construção completa (fórmula do zero, marca de divergência,
   verificação de honestidade em `napoleon-2023` e `the-godfather`).

   **O DISCLAIMER DA COTA — REMOVIDO DO RAMO COM BARRA na v1.9.27, e isso
   é decisão registrada, não esquecimento.** Na v1.9.26 ele morava debaixo
   da barra, com este texto: *"A barra é o peso real de cada grupo. A
   análise abaixo tem profundidade igual nos três — o tamanho das listas
   não indica peso."* Com o **callout de percentual** (v1.9.27) o topo
   passou a dizer o peso duas vezes — a barra e os três números ancorados
   nela —, e a frase virou uma terceira explicação do mesmo fato, a uma
   rolagem inteira de distância das listas que ela existia para desarmar.

   **O que a remoção custa, escrito porque é ele que a decisão paga.** Era
   a única frase que dizia, em palavras, que listas de bullets do mesmo
   tamanho NÃO são grupos do mesmo peso. Sem ela, o único sinal de peso
   **co-localizado com as listas** é o `~X% DAS NOTAS` no cabeçalho de cada
   grupo — e **é por isso que o percentual do cabeçalho FICA**. As duas
   coisas são uma decisão só: a frase sai porque o número do cabeçalho
   cobre a mesma leitura errada no lugar certo (ao lado dos bullets, não a
   800px deles). Quem rolar direto para a análise encontra seis marcadores
   em HATERS e seis em FANS com `~2%` e `~93%` impressos ao lado do nome de
   cada grupo; é o número no cabeçalho que impede "listas iguais, pesos
   iguais" de fechar. **Se o percentual do cabeçalho algum dia sair da
   tela, esta frase tem de voltar** — e essa é a condição que amarra a
   remoção.

   **O RAMO SEM DISTRIBUIÇÃO REAL fica INTACTO, no texto da v1.2.1** (*"Os
   grupos são cotas de coleta — não a proporção real das opiniões."*).
   Nesse caminho não há barra, não há callout e não há percentual em
   cabeçalho nenhum: a única coisa na tela sobre tamanho de grupo são as
   listas, e a regra da v1.2.1 volta a valer sozinha e inteira. Mantido em
   sincronia com `render.py` (`DISCLAIMER_*`); o render de TERMINAL não
   mudou.

   **O cabeçalho "EM DETALHE · TEMA A TEMA" foi REMOVIDO** — com o veredito
   no rodapé, não há mais um resumo antes dele do qual separar "o detalhe".

   **Os RÓTULOS dos três grupos na tela são HATERS/MIXED/FANS** desde a
   v1.9.26, onde o nome aparece isolado; a prosa continua em
   negativas/medianas/positivas, e as chaves do dado não mudam. Escopo,
   trade-off e política de reversão em **§0, "SEGUNDA EXCEÇÃO DELIBERADA na
   INTERFACE"**.

   #### A ORDEM DOS BLOCOS EM DESTAQUE — POR PESO (v1.9.30)

   O item 6 da ordem publicada acima ("bullets por sentimento") passa a ter
   ordem **interna** definida pelo dado: os blocos em destaque saem
   ordenados por `share_real`, **do maior para o menor**. O racional
   completo — por que a regra é compatível com o §0, e por que a ordem fixa
   anterior não era neutra e sim constante — está em **§0, "A ORDEM DE
   LEITURA DOS BLOCOS PASSA A SEGUIR O PESO"**. Aqui ficam a mecânica e a
   medição.

   **Vale nos DOIS leiautes, e é a mesma linha de código nos dois.** O
   contêiner é grid e **a ordem do DOM é a ordem visual**: no desktop
   "primeiro" é a coluna da ESQUERDA; no mobile, empilhado em coluna única,
   é o de CIMA. Nada de `order:` no CSS, nada de reordenar por
   breakpoint — o mobile é onde a ordem pesa mais, porque lá o segundo bloco
   só existe depois de uma rolagem, e ele é servido pela mesma decisão.
   MEDIDO em `the-godfather` a 375px: FANS em y=1203, HATERS em y=2166.

   **RESULTADO MEDIDO nos 35: a ordem MUDOU em 33.** Os dois que ficaram
   iguais são os dois filmes de recepção negativa dominante —
   `cats-2019` (86 / 7 / 7) e `joker-folie-a-deux` (46 / 33 / 21) —, e é
   exatamente a prova de que a regra não é "positivas primeiro" com outro
   nome: nesses dois, HATERS continua abrindo a leitura, porque HATERS é o
   maior grupo. Dos 33 que mudaram, 31 passaram de `NEG→POS` para
   `POS→NEG`, e os 2 de meio dominante viraram `MED→NEG→POS`
   (`friday-the-13th-2009`) e `MED→POS→NEG` (`napoleon-2023`).

   **A BARRA DE PROPORÇÃO NÃO É REORDENADA — e isso não é uma inconsistência
   por esquecimento, é a diferença entre dois tipos de ordem.** A ordem da
   barra é **SEMÂNTICA**: ela é um eixo ordinal de 0,5★ a 5★, e HATERS à
   esquerda / MIXED no meio / FANS à direita é o que faz a barra ler como
   **uma população particionada** em vez de três medições justapostas.
   Ordenar por peso ali destruiria o eixo — o meio deixaria de estar no
   meio, e a diagonal entre duas faixas deixaria de separar níveis de nota
   vizinhos. **Continuam todos em negativas → medianas → positivas:** a
   barra da página do filme, a faixa do mosaico da home, a legenda e o
   `aria-label`. Conferido depois da mudança em `the-godfather`
   (*"HATERS, cerca de 2%…; MIXED, cerca de 5%…; FANS, cerca de 93%…"*) e em
   `cats-2019`.

   **A DESSINCRONIA ENTRE A BARRA E OS BULLETS — observada na tela, e é
   pequena.** Sim, a página passa a ter dois objetos com ordens diferentes:
   a barra em ordem de estrela e os bullets em ordem de peso. Na tela isso
   quase não se nota, por dois motivos concretos: eles estão a uma rolagem
   um do outro (barra no topo, bullets depois da linha arco-íris), e o
   **callout de percentual** ancora cada número na sua fatia, então o leitor
   chega aos bullets já sabendo qual grupo é o grande — encontrar esse grupo
   primeiro **confirma** a barra em vez de contradizê-la. O caso em que a
   diferença é mais visível é `cats-2019`, onde a fatia esquerda é 86% e o
   primeiro bloco é justamente HATERS: ali as duas ordens **coincidem**.
   Onde elas divergem (`the-godfather`), a fatia grande é a da direita e o
   bloco grande é o de cima — eixos diferentes, sem confronto direto.

   **O VEREDITO PODE FICAR EM DESCOMPASSO, e isto é RESSALVA REGISTRADA, não
   defeito corrigido.** O veredito (§3[V]) é **estágio fechado**: escrito por
   LLM sobre briefing determinístico, com a sua própria ordem de
   apresentação dos grupos, e **não foi regenerado nem alterado** por esta
   versão. Ele pode, portanto, abrir por um grupo diferente do primeiro
   bloco de bullets.

   **MEDIDO nos 35, e o número surpreende na direção boa:** o descompasso
   (primeiro grupo citado no veredito ≠ primeiro bloco de bullets) aparece
   em **6 de 35** DEPOIS desta mudança, contra **31 de 35** ANTES dela. A
   ordem fixa era a que estava fora de sincronia com o veredito quase
   sempre — o texto do LLM tende a abrir pelo grupo dominante, e a tela
   abria pelo negativo. Os 6 remanescentes: `cats-2019` e
   `joker-folie-a-deux` (bullets em HATERS, veredito abre pelos que
   recomendam) e `cure`, `pearl-2022`, `perfect-days-2023`,
   `spider-man-across-the-spider-verse` (bullets em FANS, veredito abre
   pelos que não recomendam). Medição por detecção de vocabulário no texto
   publicado (`recomendam`/`não recomendam`/`aprovam`/`reprovam`/
   `meio-termo`), sobre `veredito.texto` incluindo o prefixo determinístico
   de meio dominante.

   #### O CALLOUT DE PERCENTUAL abaixo da barra (v1.9.27)

   Os três percentuais deixam de aparecer **só** nos cabeçalhos de grupo e
   passam a aparecer também **abaixo da barra**, cada um **ancorado na sua
   fatia** por um indicador fino. O percentual do cabeçalho **continua onde
   estava** — ver o parágrafo do disclaimer acima: é ele que carrega a
   informação de peso para o lado das listas de bullets. **A fonte
   continua sendo uma só:** `b.share_real`, o mesmo inteiro que o cabeçalho
   e que o `aria-label` imprimem; o callout não recalcula nada.

   **A COLISÃO é o problema real desta entrega.** `the-godfather` é
   2% / 5% / 93%: os centros verdadeiros das duas primeiras fatias caem a
   1% e 4,5% da largura da barra — **7,2px e 32,4px** em desktop (720px),
   **3,35px e 15,07px** a 375px (barra de 335px). A caixa de um número mede
   **39,91px**. Três números centrados nos seus centros verdadeiros se
   sobrepõem, e nenhum dos dois primeiros cabe dentro da própria fatia. O
   pior caso do catálogo não é nem esse: é `cidade-de-deus`, 1% / 3% / 96%.

   **A REGRA: empacotamento da ESQUERDA para a DIREITA com folga mínima, e
   o indicador inclinado absorve o deslocamento.**

   ```
   x1 = max(0,          min(c1 − L/2,  100% − 3L − 2g))
   x2 = max(x1 + L + g, min(c2 − L/2,  100% − 2L − g))
   x3 = max(x2 + L + g, min(c3 − L/2,  100% − L))
   ```

   `c` é o centro VERDADEIRO da fatia (o mesmo número normalizado que
   desenha a barra), `L` a largura da caixa do número (`5.6ch` da mono) e
   `g` a folga mínima (**14px desde a v1.9.28** — era 8px; a diferença é o
   espaço que o halo do neon permanente passou a ocupar, ver "A COLISÃO QUE
   O NEON PERMANENTE CRIA"). Cada número vai para o centro da sua fatia;
   quando não cabe, escorrega o mínimo necessário e a linha que o liga ao
   centro verdadeiro inclina. **O ponto de ancoragem nunca se move** —
   quem se move é o rótulo, e a inclinação é a declaração visível de que
   ele se moveu. O termo `100% − L` na última linha é o que trata o outro
   lado: uma fatia colada na borda direita puxa o rótulo para DENTRO, e aí
   o indicador inclina para a direita em vez de para a esquerda
   (`cats-2019`, 86/7/7, é o caso).

   **Por que esta regra e não as outras duas consideradas:**
   - **Omissão abaixo de um limiar** foi descartada de saída: sumir com o
     `~2%` é apagar exatamente o número que o leitor não esperava, e a
     exigência de acessibilidade desta versão é que os três estejam
     legíveis e no DOM desde o primeiro frame.
   - **Empilhamento vertical** resolve a colisão, mas cobra altura, desfaz
     a leitura em linha única e **não evita o problema**: um número na
     segunda linha continua precisando de um indicador inclinado para achar
     a sua fatia. Paga o custo do deslocamento sem se livrar dele.

   **Por que ela vale para QUALQUER distribuição futura, e não só para as
   35 de hoje.** É uma passada de empacotamento, não uma exceção por filme:
   sempre tem solução enquanto `3L + 2g` couber na barra — **147,7px contra
   335px** de barra a 375px de viewport (com `g` = 14px), folga de 2,3×. Qualquer trinca que
   some 100 é acomodada, inclusive 0/0/100 e 33/33/34; abaixo de ~180px de
   barra (viewport que não existe) os números encostariam.

   **ONDE A CONTA MORA: no CSS**, pela mesma razão de `--diag`. Ela mistura
   três grandezas que vivem em lugares diferentes — o centro da fatia é
   **dado** (percentual, sai do JSON e nunca muda), a largura da caixa do
   número é **tipografia** (`ch` da mono, que o CSS conhece e o JS só
   saberia medindo) e a largura da barra é **layout** (muda a cada resize).
   `min()`/`max()` misturam porcentagem e `ch` sem problema, então a conta
   inteira reage a resize e a zoom de fonte sozinha: **sem
   `ResizeObserver`, sem ouvinte de `resize`, sem um único recálculo em
   JS**. O JS grava só `--c1..--cn` e `--n`.

   **O INDICADOR tem duas metades porque o CSS não tem sinal.** A que
   aponta para a direita mede `max(0, rótulo − centro)`; a que aponta para
   a esquerda, `max(0, centro − rótulo)`. Só uma tem largura de verdade; a
   outra colapsa para a espessura mínima (1px) e, por estar ancorada NO
   CENTRO VERDADEIRO, vira a marquinha vertical em cima dele — que é
   exatamente o que se quer ali. Sem deslocamento nenhum as duas colapsam e
   o indicador é uma marca vertical de 2px, que é o caso da maioria do
   catálogo.

   **MEDIDO em `the-godfather`, os dois tamanhos** (posição em px a partir
   da borda esquerda da barra; `centro` é o centro do rótulo, `fatia` o
   centro verdadeiro da fatia):

   | | rótulo | esquerda | centro | fatia | desloc. |
   |---|---|---|---|---|---|
   | desktop (barra 720px) | `~2%` | 0,00 | 19,96 | 7,20 | +12,76 |
   | | `~5%` | 53,91 | 73,87 | 32,40 | +41,47 |
   | | `~93%` | 365,23 | 385,19 | 385,20 | −0,01 |
   | 375px (barra 335px) | `~2%` | 0,00 | 19,96 | 3,35 | +16,61 |
   | | `~5%` | 53,91 | 73,87 | 15,07 | +58,80 |
   | | `~93%` | 159,27 | 179,22 | 179,22 | 0,00 |

   Caixa de 39,91px nos dois tamanhos (a fonte não encolhe no mobile);
   nenhuma sobreposição, nenhum overflow horizontal. (Valores da v1.9.28,
   com `--gap` de 14px; na v1.9.27, com 8px, o segundo rótulo ficava 6px
   à esquerda destes.)

   **`aria-hidden="true"` no callout — DIVERGE, de propósito, da decisão
   tomada para a LEGENDA.** A legenda visível não é escondida de leitor de
   tela ("esconder texto visível troca um problema por outro"), e a
   redundância com o `aria-label` é aceita — mas a legenda carrega o **nome
   do grupo**: lida isolada, ela informa. Um `~2%` solto, não. Sem o nome
   ao lado, os três números viram três grandezas órfãs anunciadas logo
   depois de o leitor de tela já ter lido *"HATERS, cerca de 2% das notas;
   MIXED…"* — que é o `aria-label` da barra, com rótulo, na mesma ordem e
   com os mesmos inteiros. O callout **não acrescenta um bit** ao que a
   alternativa textual da barra já diz: é uma re-apresentação VISUAL dela.
   Esconder aqui não perde informação e evita três números sem dono.

   #### A ANIMAÇÃO DE ENTRADA DA BARRA — as FRONTEIRAS DESLIZAM (v1.9.28)

   **O MODELO DA v1.9.27 SAIU INTEIRO.** Lá a barra crescia de 0 a 100%
   como um bloco neutro (`#454b5a`) e só então as cores nasciam por cima,
   em duas fases (fill + partição). A camada de prefill foi **removida do
   JS e do CSS**, não escondida atrás de flag. Decisão do dono do projeto.

   **O MODELO PUBLICADO:** a barra **nasce completa**, particionada em
   **três partes iguais**, e as fronteiras deslizam até a distribuição
   real. Com isso as duas fases viram **uma**.

   ```
   x1: 33,333%  ──▶  h            x2: 66,667%  ──▶  h + m
   x(k) = neutro + (fim − neutro) × k
   ```

   | fase | janela | o quê |
   |---|---|---|
   | A · fronteiras | 0 → 650ms | terços ──▶ distribuição real |
   | B · ignição | 650 → 1020ms | 3 números × 260ms, escalonados 55ms |

   **Total 1020ms** (era 1190ms com o modelo antigo), medido pela Web
   Animations API.

   **UMA FUNÇÃO TEMPORAL SÓ, e ela é literal.** `--k` é um número
   registrado por `@property` e animado **uma vez**, na barra; as duas
   fronteiras e a diagonal são funções puras dele. Não são duas animações
   com temporização igual que *pareceriam* a mesma função — é uma animação,
   lida por dois lugares. Isso mata na origem o frame em que a soma não
   fecha 100%.

   **E A ARQUITETURA DE CAMADAS EMPILHADAS dá a garantia mais forte
   ainda**, e é por isso que ela foi preservada: a camada de baixo ocupa
   **100% da barra em todos os frames**, então a região da terceira fatia é
   literalmente "o que sobra". A soma fecha **por construção**, não por
   sincronia — e não existe superfície descoberta em frame nenhum. Três
   segmentos independentes em flex/grid é a forma de fazer isto que deixa
   buraco; foi recusada.

   **A DURAÇÃO É FIXA (650ms) e independente da distribuição.** A
   DISTÂNCIA percorrida é consequência do dado — `cats-2019` move a
   primeira fronteira 52,7 pontos percentuais e `napoleon-2023` move 11,3 —,
   mas as duas levam os mesmos 650ms. Amarrar a duração à distância faria a
   animação codificar uma segunda variável competindo com a barra.

   **A CURVA — `cubic-bezier(0.22, 0.68, 0.28, 1)`, desaceleração pura.** A
   proibição de overshoot/bounce/spring é **geométrica antes de ser
   estética**: os dois pontos de controle dentro de [0,1] são o que garante
   `k ∈ [0,1]` em todo instante, e `k` fora desse intervalo produziria
   `x1 > x2`, ou seja, uma fatia de largura **negativa**.

   **NENHUM VÃO EM FRAME NENHUM.** Durante o deslize as camadas não mudam
   de opacidade nem de posição — só de **limite** —, e continuam encostadas
   o tempo todo. Zero gutter, zero fio separador, zero margem, zero borda
   como separador, zero pixel transparente.

   ##### `--diag` durante a interpolação — ACOMPANHA (v1.9.28)

   A diagonal é derivada da fatia mais fina. No estado de terços a mais
   fina é 33,333%; no final pode ser 2%. **Escolhido ACOMPANHAR a
   interpolação**, com as duas variantes construídas e medidas lado a lado.

   `--menor-agora = 33,333 + (menor_final − 33,333) × k`, e a identidade
   `min(lerp(t, f_i, k)) = lerp(t, min(f_i), k)` — todas as fatias partem
   do MESMO 33,333% — é o que permite escrever isso como **uma conta só**,
   sem comparar as três em tempo de execução.

   **Por quê:** a diagonal existe para proteger a fatia estreita, e durante
   o deslize a fatia estreita ainda não é estreita. Fixá-la no valor final
   faz a barra animar inteira com uma diagonal dimensionada para um destino
   que ainda não chegou — e isso é **visível**: em `the-godfather` a 375px,
   no meio da animação, a variante fixa desenha uma fronteira de 3,68px
   entre duas regiões largas, que lê como corte reto e não como a diagonal
   da barra publicada. A variante que acompanha desenha 12px ali, e a barra
   lê como o mesmo objeto do começo ao fim. Os dois estados finais são
   idênticos.

   **O risco levantado (tremor / artefato de subpixel na fatia estreita)
   foi medido e NÃO existe.** Em 131 amostras de 5ms, nas duas variantes:
   **zero reversões** na aresta de cima e na de baixo da diagonal (a de
   baixo é a que corre risco, porque `base = x1 − diag/2` e os dois termos
   encolhem juntos); o ponto mais fino da fatia de 2% nunca desce de
   **4,861px**, o mesmo valor final nas duas variantes.

   **O que ACOMPANHAR de fato custa, registrado:** o `clamp()` prende a
   diagonal no teto de 12px durante a primeira metade e só então a solta,
   então o **valor** é contínuo mas a **taxa** tem um canto no ponto em que
   o clamp deixa de morder (t ≈ 301ms a 375px, t ≈ 470ms em desktop).
   Medido: a diagonal muda no máximo **0,947px por quadro**, contra
   **8,425px por quadro** de deslocamento da própria fronteira — a mudança
   do ângulo é ~9× mais lenta que o movimento em que ela viaja, e fica
   enterrada nele.

   ##### Os rótulos durante a interpolação — AUSENTES (v1.9.28)

   Os rótulos do callout são ancorados aos segmentos, e o empacotamento
   **não depende de `--k`**: as posições são as finais desde o primeiro
   frame. Um `~2%` visível durante o deslize ficaria meio segundo apontando
   para uma região que naquele instante é 33% — ou teria de deslizar junto
   (mostrando número que não bate com a região) ou mudar de valor (animar
   dado, descartado desde a v1.9.27).

   **Rótulos e indicadores AUSENTES durante a interpolação**, acendendo
   depois, já nas posições finais e com os valores finais. A ignição
   continua sendo o momento em que o número aparece. Isso **reverte** o
   `opacity: 0.16` inicial da v1.9.27 (o "tubo apagado"), que só fazia
   sentido enquanto a barra crescia vazia e o número não contradizia nada.
   **O texto continua no DOM com o valor final desde o primeiro frame** — o
   que muda é opacidade, cor e sombra.

   ##### O NEON FICA LIGADO (v1.9.28)

   **Correção da decisão da v1.9.27, pelo dono do projeto:** o brilho NÃO
   decai depois do pico. A ignição continua sendo o EVENTO — apagado →
   flicker → pico → estabiliza —, e o pico continua mais intenso que o
   repouso; o que mudou foi o **destino**: em vez de o halo praticamente
   desaparecer, ele estabiliza num estado **aceso permanente**.

   Calibrado na tela: núcleo branco fechado (2px a 65%), halo na cor do
   grupo (6px) e halo externo na cor a 20% de alfa (**11px, e esse teto é
   requisito de layout — ver abaixo**). O pico vai a 28px, por ~35ms.

   **AS QUATRO CAMADAS DE SOMBRA SÃO AS MESMAS EM TODOS OS QUADROS**, com a
   quarta zerada no repouso. `text-shadow` com número DIFERENTE de camadas
   entre dois quadros **não interpola** — salta. Manter a contagem é o que
   faz o pico descer suavemente até o repouso em vez de piscar para ele.

   ##### A COLISÃO QUE O NEON PERMANENTE CRIA, e como ela foi fechada

   Com o halo aceso o tempo todo, ele passa a **ocupar espaço** o tempo
   todo — e a regra de empacotamento tinha sido calculada sem ele. Em
   `the-godfather` a 375px o segundo número começa a 8px do fim do
   primeiro; um halo de raio grande atravessa essa folga e mistura o brilho
   de dois grupos de **cores diferentes**, que é exatamente o que a paleta
   por grupo existe para não fazer.

   **ESCOLHIDAS AS DUAS SAÍDAS, e não uma.** Limitar o raio (11px) **e**
   fazer o empacotamento contar o halo (`--gap` de 8px para 14px). Cada uma
   sozinha é frágil: só limitar o raio deixaria a garantia dependendo de um
   número que a próxima calibração de brilho pode mexer sem perceber; só
   aumentar a folga deixaria o halo livre para crescer. A conta, com `R` o
   raio do halo e `P` o respiro que a caixa já dá em volta do texto:

   ```
   folga_entre_tintas = --gap + 2P  ≥  2R
   ```

   O pior caso possível é dois rótulos de **4 caracteres** empacotados lado
   a lado (`P` mínimo = 5,46px): `--gap ≥ 2(11) − 2(5,46) = 11,08px`.
   Com 14px sobram 2,92px **no pior caso que a regra admite**, e não só nos
   filmes de hoje. Aumentar a folga **não custa nada** nos filmes em que a
   restrição não morde — o rótulo já cabia no centro da sua fatia —; custa
   ~6px de deslocamento a mais só nos que já estavam deslocados.

   **MEDIDO** (folga entre as TINTAS, medida com `Range`, não entre as
   caixas; precisa de 22px):

   | filme | par | desktop | 375px |
   |---|---|---|---|
   | `the-godfather` | `~2%` · `~5%` | 32,17px | 32,17px |
   | `cidade-de-deus` | `~1%` · `~3%` | 32,17px | 32,17px |
   | `eighth-grade` | `~6%` · `~18%` | 61,91px | **28,55px** |
   | `cats-2019` | `~7%` · `~7%` | 32,17px | 32,18px |

   Nenhuma mistura em nenhum dos dois tamanhos. O par mais apertado do
   catálogo não é o de `the-godfather` e sim o de `eighth-grade` a 375px,
   porque ali um dos dois rótulos tem 4 caracteres e sobra menos respiro
   dentro da caixa.


   #### ACESSIBILIDADE DA ANIMAÇÃO (v1.9.27, reconfirmada na v1.9.28)

   1. **`prefers-reduced-motion`: nenhuma fase roda.** A construção é a
      única que entrega isso sem depender de regra de desligamento: **o
      estado base do CSS É o estado final**, e tudo que a animação faz —
      inclusive o estado INICIAL (`--k: 0`, número apagado) — vive dentro
      de `@media (prefers-reduced-motion: no-preference)`. O
      `* { animation: none !important }` que já existia sob `reduce`
      continua valendo como segunda linha, mas nada aqui depende dele —
      **e essa é a diferença que importa**: se o estado inicial morasse
      fora do bloco, `reduce` deixaria a barra em terços para sempre.
      Verificado nos dois sentidos: com o bloco `no-preference` inativo, 0
      animações, `--k = 1`, barra na distribuição real e números acesos;
      reativado, as 10 animações voltam e a sequência re-arma do zero.
      **O NEON PERMANENTE NÃO É MOVIMENTO E FICA** — conferido: sob
      `reduce` o `text-shadow` de repouso está aplicado por inteiro.
   2. **A alternativa textual descreve sempre o ESTADO FINAL.** O
      `aria-label` do `role="img"` é escrito na montagem, com os três
      rótulos e os três pesos, e nunca é tocado pela animação. **O estado
      neutro de terços é expressivo e nunca é anunciado**: um leitor de
      tela jamais ouve "33% / 33% / 33%".
   3. **Os percentuais são conteúdo, não aparência.** O texto está no DOM
      com os **valores finais** desde o primeiro frame; a animação não
      cria, remove nem altera um caractere — muda opacidade, cor e sombra.
      Que eles fiquem **invisíveis** durante o deslize é decisão de
      apresentação (ver "Os rótulos durante a interpolação"), não de
      conteúdo.
   4. **Sair da página no meio não deixa nada pela metade.** Não há estado
      guardado em lugar nenhum: a página é remontada do zero a cada visita,
      a sequência é CSS puro com `animation-fill-mode: both`, e o estado
      final coincide com o estado base.

   **CADÊNCIA — DECISÃO EM ABERTO PARA O DONO DO PROJETO.** Implementado
   **SEMPRE** (roda a cada visita a uma página de filme), que é o que a
   intenção "sensação de estar sendo calculado na hora" pede. A alternativa
   é uma vez por sessão (`sessionStorage`), e ela tem um custo próprio: a
   barra passaria a aparecer pronta em algumas visitas e animada em outras,
   sem que o leitor saiba por quê. A leitura sobre cansaço em navegação
   repetida continua não podendo ser dada por experiência — ver a ressalva
   de método em `frontend/TESTE_MANUAL.md`. O total caiu de 1190ms para
   1020ms na v1.9.28, o que reduz o custo por visita em 14%.

   #### O PÔSTER (v1.9.29) — na home e na página do filme

   **Decisão de produto, tomada e não reaberta:** pôster SIM, na home e na
   página do filme; **galeria de backdrops NÃO na v1** (§3[F] — o TMDB não
   garante que um backdrop seja livre de spoiler). O pipeline coleta
   `backdrop_paths[]` e **nenhum arquivo do frontend os lê**.

   **Página do filme — CONTIDO.** O pôster abre a ficha, 200px no desktop e
   140px no mobile. O produto não vira catálogo visual: o pôster representa
   o FILME, a barra logo abaixo representa a RECEPÇÃO, e a composição existe
   para que **nenhum dos dois domine o outro**. Um pôster em largura total
   empurraria a barra para fora da primeira tela e inverteria a hierarquia
   que a v1.9.26 estabeleceu. A composição de referência do dono é
   `[PÔSTER] → TÍTULO → ANO → barra`; o que a página publica desde a v1.9.26
   é **ano → título** (item 1 da ordem publicada acima), e essa micro-ordem
   não é o que esta sessão veio mudar — o pôster entra ACIMA do par e o par
   segue como está. **A BARRA não foi tocada:** nem posição, nem geometria,
   nem a animação de entrada da v1.9.28.

   **Home — REDESENHO da célula, não acréscimo.** A célula da v1.9.18 foi
   desenhada SEM imagem (card escuro em 4/5, texto como protagonista, faixa
   de 5px na base). Encaixar um pôster nela daria o pior dos dois — uma
   miniatura apertada disputando espaço com o título. Então: a célula muda
   de proporção (**4/5 → 2/3**, a do próprio pôster), o pôster ocupa a
   célula inteira, e o texto sobe para um **degradê** na base que chega a
   98% de preto — o título tem de ser legível sobre pôster claro
   (`barbie`, `wonka`) e sobre escuro, e um véu uniforme apagaria a arte.
   A grade fica ~20% mais alta (5 linhas de 213px contra 165px no desktop);
   é o custo de densidade que mostrar pôster cobra. **A faixa de recepção
   continua**, de 5px para **6px** com um fio escuro em cima que a separa de
   qualquer arte sem depender da cor dela — ela é o único sinal de RECEPÇÃO
   da célula, e é o que impede a home de virar um catálogo de capas. Cores,
   ordem e semântica: idênticas.

   **A ANIMAÇÃO DA BARRA NÃO RODA NA HOME — decisão registrada.** Trinta e
   cinco sequências simultâneas na entrada viram espetáculo e competem entre
   si. A home mostra a faixa no **estado final**; a animação continua sendo
   o momento de **abrir um filme**.

   **AUSÊNCIA DE PÔSTER É ESTADO DESENHADO**, nunca imagem quebrada. Nenhum
   dos 35 publicados está nesse caso (medido: 35/35 com pôster), mas a
   expansão trará filmes obscuros com menos cobertura, e o estado precisa
   existir ANTES do primeiro — senão ele vira um ícone de imagem quebrada em
   produção. O desenho mantém a silhueta do pôster, com hachura diagonal
   sutil, a marca do produto e "SEM PÔSTER". Uma falha do CDN (404, rede,
   `file_path` que envelheceu) cai no MESMO estado.

   **A PROPORÇÃO É RESERVADA ANTES DE CARREGAR**, em dois níveis: um
   `aspect-ratio` inline escrito pelo JS a partir de
   `ficha.poster_largura`/`poster_altura` (segura a caixa mesmo se a imagem
   nunca chegar) **e** `width`/`height` no próprio `<img>` (dá ao navegador
   a razão intrínseca sem depender do CSS). **Medido:** com a reserva, a
   geometria da home é **byte-idêntica** com e sem as 35 imagens no DOM
   (altura de documento 1657px nos dois casos, 0 de 35 células mudando de
   retângulo) e a CLS observada é **0**; na página do filme, o título fica
   em y=425,52 com ou sem o pôster. **Sem a reserva**, a caixa do pôster
   mediria **2px** de altura até a imagem chegar — o título saltaria
   **298px** quando ela chegasse. Esse é o número que a reserva compra.

   **TAMANHOS DO CDN, e o cálculo.** O TMDB serve variantes de largura
   (`w92 · w154 · w185 · w342 · w500 · w780 · original`). A regra é a maior
   largura CSS que o elemento atinge, vezes 2 (telas de densidade 2x/3x),
   arredondada para cima na lista.
   - **mosaico → `w342`.** A célula mede ~142px CSS no desktop (mosaico de
     1080px, 7 colunas) e ~111px no mobile de 375px (3 colunas); 142×2=284,
     111×3=333. **Peso medido dos 35:** `w185` 525 KB (pequeno demais em
     retina), **`w342` 1282 KB** (37 KB de média, 17–66 KB), `w500` 2362 KB
     (+84% por pixels que a célula não usa).
   - **ficha → `w500`.** O pôster mede 200px CSS no desktop; 200×2=400.
     `w342` ficaria abaixo em retina, e é UMA imagem por página.
   `original` (2000px de largura) num card de mosaico é desperdiçar 99% dos
   bytes, e é explicitamente o que não se faz.

   **`loading="lazy"` na home** (35 imagens, a maioria abaixo da dobra) e
   **`eager` na ficha** (UMA imagem, sempre acima da dobra — adiá-la só
   atrasaria a abertura). `alt` diz o que a imagem É ("Pôster de <título>
   (<ano>)"): descrever a arte seria invenção, e o texto ao lado já nomeia o
   filme. **Nada de binário no repositório:** o JSON guarda só `file_path`,
   a imagem vem do CDN do TMDB, sem download, proxy ou cache local.

   **Onde mora.** `frontend/js/poster.js`, compartilhado pelas duas páginas
   — e a exceção à duplicação deliberada do projeto (`EIXO_LABEL` vive em
   home.js E filme.js) é justificada: lá a lista é fechada e divergir seria
   visível no primeiro filme; aqui uma home servindo `w500` e uma ficha
   servindo `w342` não quebrariam nada, não apareceriam em teste nenhum, e a
   única consequência seria peso de rede que ninguém mede.

   #### O BACKDROP no topo da página do filme (v1.9.30)

   **O pôster vertical SAI do topo da página do filme e entra um BACKDROP
   (16:9, horizontal), no mesmo lugar — acima do par ano → título.** Decisão
   do dono do projeto, tomada e **não reaberta**. **O PÔSTER CONTINUA NA
   HOME**, sem nenhuma alteração: esta entrega troca a imagem SÓ na página
   do filme.

   ##### ISTO É EXCEÇÃO EXPLÍCITA AO PRINCÍPIO ANTI-SPOILER DO §0

   Este registro é obrigatório e é a parte da decisão que custa alguma
   coisa. Não há como escrevê-lo sem tensão, e ele não tenta.

   **O que o produto promete.** A home anuncia **"0 SPOILERS"** em caixa
   alta, ao lado de "24 QUADROS" e "3 GRUPOS". O parágrafo de abertura desta
   spec diz, sobre o público-alvo: *"pessoa que ainda NÃO assistiu ao filme.
   Toda decisão de design que envolva trade-off entre completude e risco de
   spoiler resolve a favor de evitar spoiler."* E o produto cumpre isso em
   toda parte: as reviews passam por filtro anti-spoiler na coleta (§3[C]),
   o prompt de síntese proíbe descrever eventos de enredo (§3[D]), o
   veredito é **proibido de citar reviravolta** (§3[V]), e a galeria de
   backdrops foi recusada na v1 **por este exato motivo**.

   **O que o backdrop é.** Um quadro do filme, do acervo do TMDB, **sem
   nenhuma garantia** de que não seja do terceiro ato. Não existe curadoria
   — nem humana, nem automática, nem por metadado: o TMDB não marca imagem
   por posição na narrativa, e não há sinal na API do qual isso se derive.
   **O dono do projeto decidiu prosseguir SEM curadoria de spoiler**, com o
   trade-off explicitamente na mesa.

   **E ele fica na POSIÇÃO MAIS PROEMINENTE DA PÁGINA** — o primeiro
   elemento, acima do título, **antes da sinopse**, em largura total. Não é
   um detalhe periférico onde a exceção seria pequena: é literalmente a
   primeira coisa que o leitor vê, e ele a vê sem ter escolhido vê-la.

   **O QUE SE GANHA:**
   - **Leitura horizontal.** 16:9 é o formato da imagem em movimento, e um
     quadro largo abre a página como abertura editorial em vez de capa de
     catálogo.
   - **Menos espaço vertical no topo.** Medido: o backdrop reserva **405px**
     de altura em desktop (720px de coluna) contra os ~300px do pôster de
     200px de largura — mas ele ocupa a **largura inteira**, então não
     divide a linha com nada e não empurra o par ano → título para o lado.
     No mobile o ganho é o real: de borda a borda, contra uma capa de 140px
     que deixava dois terços da linha vazios.
   - **Abertura editorial.** O pôster é o objeto de marketing do filme; o
     quadro é o filme. Para uma página que existe para descrever recepção, a
     segunda leitura é a que o dono quis.

   **O QUE SE PERDE, sem maquiagem:** **a promessa anti-spoiler deixa de
   valer neste elemento.** Não fica mais fraca, não fica condicionada, não
   fica "mitigada por curadoria": ela **não vale ali**. Um leitor que confia
   no "0 spoilers" da home e abre uma página de filme pode ver, antes de
   qualquer texto, um quadro do desfecho. O produto continua a resolver todo
   o resto contra o spoiler; este elemento, e só ele, é a exceção. Se algum
   dia existir política de curadoria, ela entra aqui — e o pipeline já está
   preparado para isso, porque a lista de candidatos continua guardada.

   ##### QUAL backdrop — regra determinística, em código

   A escolha é do **pipeline** (`_ordem_imagem`/`_melhor` em `ficha.py`,
   §3[F]), gravada no JSON como `backdrop_path`, e sai de **dentro dos até
   10 coletados** (`backdrop_paths[]`) — nunca do acervo inteiro. Isso é o
   que mantém "qual imagem esta página mostra" respondível olhando só o JSON
   publicado. **NÃO EXISTE GALERIA:** `backdrop_paths[]` continua sendo lista
   guardada que nenhum arquivo do frontend percorre; o frontend lê **um**
   campo, o do escolhido.

   **A ordem, do degrau mais forte ao mais fraco, e por que cada um:**

   1. **sem texto sobreposto** (`iso_639_1 is None`) antes de arte com
      idioma declarado;
   2. **`vote_average`** decrescente — a resposta a "o mais bem avaliado";
   3. **`vote_count`** decrescente;
   4. **`width`** decrescente;
   5. **`file_path`** crescente — o degrau que fecha a **ordem total**.

   **Por que "mais bem avaliado" e não as outras duas propostas.**
   *Maior resolução* como primeiro critério escolhe o maior arquivo, não o
   melhor quadro: o acervo é cheio de 3840×2160 sem voto nenhum, e a régua
   viraria "quem exportou em 4K". *Primeiro da lista* delega a escolha a uma
   ordenação que a API **não declara**: `images.backdrops` chega por
   `vote_average` decrescente, mas isso não é ordem total — empates são
   comuns e o desempate é indefinido. **MEDIDO nos 35: em 3 filmes**
   (`eighth-grade`, `friday-the-13th-2009`, `wicked-2024`) **o primeiro da
   lista não é o que esta ordem escolhe.** Confiar na posição deixaria a
   imagem de um filme publicado livre para mudar entre duas execuções sem
   que nada no dado tivesse mudado — que é exatamente o que "determinística"
   proíbe. Os degraus 3–5 existem por isso: sem o `file_path` no fim, a
   ordem não é total e o problema volta pela porta dos fundos.

   **O degrau 1 é PREFERÊNCIA, nunca filtro** — um filme cujas imagens sejam
   todas `pt` continua tendo backdrop. Ele existe porque uma imagem
   `iso_639_1='pt'` é **key art de campanha**: título tratado e bloco de
   elenco gravados no pixel, indo logo ACIMA do par ano → título que a
   própria página escreve. **MEDIDO: afeta 2 dos 35** —
   `joker-folie-a-deux` e `longlegs`, os dois com uma peça `pt` de
   `vote_average` 7,542 que venceria sem a regra (a do Joker traz
   *"PHOENIX GAGA / JOKER: LOUCURA A DOIS"* em tipografia de cartaz). É
   também o degrau mais fácil de reverter se o dono preferir a key art:
   é um argumento de `_melhor`.

   ##### FALLBACK, em dois degraus

   1. filme **sem backdrop** usa o **pôster** que já estava ali — contido,
      200px no desktop / 140px no mobile, exatamente como na v1.9.29;
   2. filme **sem os dois** cai no **estado de ausência já desenhado**.

   O backdrop **não cai no pôster por conta própria** dentro de
   `montarBackdrop` (ele devolve `null` e quem chama decide), porque as duas
   caixas têm proporção e tamanho diferentes — um pôster 2:3 esticado na
   largura da coluna seria pior que qualquer um dos dois estados.

   **MEDIDO: 34 dos 35 têm backdrop; 1 não** — `talk-to-me-2022`, e o motivo
   dele **não é escassez de acervo**: a ficha publicada desse slug é a de
   outro filme (ver a ressalva no §3[F]). Uma falha do CDN cai no mesmo
   estado desenhado da ausência, na caixa 16:9.

   ##### PROPORÇÃO RESERVADA — o requisito ficou mais duro, não menos

   Mesma construção em dois níveis do pôster (§3[E], v1.9.29):
   `aspect-ratio` inline vindo de `ficha.backdrop_largura`/`backdrop_altura`
   **e** `width`/`height` no `<img>`. **Aqui a reserva importa MAIS:** sendo
   largo, o backdrop reserva mais altura em pixels que o pôster contido, e
   sem ela o salto seria **pior** que o de antes.

   **MEDIDO** (`the-godfather`, viewport 1280, coluna de 720px):

   | | valor |
   |---|---|
   | caixa reservada | 720 × 405 px |
   | `aspect-ratio` inline | `1920 / 1080` (dimensões reais do TMDB) |
   | y do `<h1>` **com** a imagem carregada | 530,52 px |
   | y do `<h1>` **sem** a imagem (só a reserva) | 530,52 px |
   | y do `<h1>` **sem a reserva** | 125,52 px |
   | **salto que a reserva evita** | **405 px** |
   | **CLS observada** | **0** (0 entradas de `layout-shift`) |

   A CLS foi medida com `PerformanceObserver({type:'layout-shift',
   buffered:true})` sobre um carregamento completo, em desktop (1280px) e a
   375px: **0 nos dois**, com **zero** entradas — não é um total pequeno, é
   a ausência de qualquer deslocamento. A home, que não mudou, foi medida de
   novo para confirmar que não regrediu: **CLS 0**, altura de documento
   **1657px** — o mesmo número da v1.9.29 — nas duas variantes de pôster.

   ##### TAMANHO DE CDN — `w1280`, e a conta

   O TMDB serve backdrops numa lista de larguras **própria**
   (`w300 · w780 · w1280 · original`) — `w500` nem existe para backdrop, e
   por isso ele não entra no mapa de tamanhos do pôster. A coluna de leitura
   é `--maxw` (720px, 760px acima do breakpoint largo) menos 20px de padding
   de cada lado: **680–720px CSS**. A regra do projeto (maior largura CSS ×
   2, arredondando para cima na lista) pediria 1360–1440 — e o degrau
   seguinte é **`original`** (3840×2160, ~1,5 MB), que a regra do projeto
   proíbe servir e que num elemento decorativo seria desperdício de quase
   toda a transferência.

   **`w1280` é a escolha, com o custo declarado:** ela entrega **1,78–1,88×**
   num aparelho de densidade 2, contra os 2,0× ideais — diferença que não se
   vê num quadro fotográfico e que custaria megabytes para fechar. `w780`
   ficaria em **1,08×** no desktop, visivelmente mole em retina.

   ##### `alt`, e a moldura

   `alt` = **"Imagem de &lt;título&gt; (&lt;ano&gt;)"**. Mesma política do
   pôster: diz o que a imagem **É**, sem descrever a arte (não temos a
   descrição, e inventá-la seria mentir para quem depende do `alt`) e sem
   repetir o que o `<h1>` logo abaixo já diz. **Não é chamada de "cena"** de
   propósito: parte do acervo é arte de divulgação, não fotograma, e o `alt`
   afirmaria uma coisa que nem sempre é verdade.

   **Sem borda e sem sombra projetada, ao contrário do pôster** — o pôster é
   um objeto pousado na página e a borda o recorta do fundo; o backdrop é a
   abertura, e uma moldura o transformaria num print. Um degradê na base
   costura a imagem no fundo da página, porque o par ano → título vem logo
   abaixo e uma aresta dura ali cortaria os dois. No mobile ele vai **de
   borda a borda** (recuo negativo de 20px de cada lado): com o padding, um
   quadro 16:9 mediria 335px de largura numa tela de 375 e leria como
   miniatura.

   #### O TOPO EDITORIAL (v1.9.32) — a sinopse sai, o backdrop dissolve, o título invade

   Cinco mudanças de uma vez no topo da página do filme, todas decisão do
   dono do projeto. A barra de proporção **não foi tocada** — nem
   geometria, nem ordem, nem callout, nem a regra de colisão, nem a
   animação de entrada da v1.9.28.

   ##### A SINOPSE SAI — decisão final, e o que ela custa

   O bloco de sinopse e o **card escuro** que o continha foram **removidos**
   da página. Não é ocultar nem colapsar: não existem mais. A **linha de
   metadados sobrevive**, agora **solta** — sem fundo, sem borda, sem
   padding de caixa —, porque com uma linha só um card desenha uma caixa
   sem conteúdo para conter.

   **A CONSEQUÊNCIA PREVISTA, escrita porque é ela que a decisão paga.** O
   público-alvo declarado do produto (§1) é **quem ainda NÃO assistiu**, e
   a sinopse era **o único elemento da página inteira que dizia do que o
   filme trata**. Sem ela, os bullets chegam **sem premissa onde se
   apoiar**: "o ritmo arrasta" pressupõe saber o que arrasta, "a atuação
   sustenta" pressupõe saber quem atua. O produto passa a assumir que o
   leitor **já sabe qual é o filme** antes de chegar.

   **O custo é BAIXO HOJE e CRESCENTE depois, e essa assimetria é o ponto.**
   Nos 35 do catálogo atual ele quase não morde: são filmes conhecidos, e o
   backdrop faz muito do trabalho de situar (o quadro de `dune-2021` diz
   "deserto, ficção científica" sem uma palavra). Na expansão — filmes
   obscuros, estrangeiros, sem circulação no Brasil — nada disso vale: nem
   o leitor traz contexto de casa, nem o backdrop de um drama iraniano
   comunica premissa. **A dívida cresce com o catálogo, e não aparece
   enquanto o catálogo for o de hoje.** Decisão consciente do dono, tomada
   com isto na mesa.

   **A ATRIBUIÇÃO AO TMDB NÃO É AFETADA e continua integralmente em vigor.**
   Conferido depois da mudança: a linha de metadados (diretor, gêneros,
   duração) **continua vindo do TMDB**, e por isso continua carregando
   **"fonte TMDB"**; o aviso exigido pelos termos segue no **rodapé de
   `index.html`, `filme.html` e `creditos.html`**, e a página de créditos
   segue no ar e linkada. Usar menos da API não reduz em nada o que se deve
   a ela. O que saiu junto com a sinopse foi só o **aviso de sinopse em
   inglês** (`sinopse_fallback_en`) — ele avisava sobre um texto que não
   está mais na tela; o campo continua no JSON, intocado.

   **O DIRETOR EM CAIXA ALTA, sem o prefixo "dir."** — o esboço do dono abre
   a linha pelo nome, e o prefixo era muleta de quando o nome vinha em caixa
   normal no meio de outros dados. **A caixa alta é do CSS
   (`text-transform`), nunca do dado:** `toUpperCase()` em JS mudaria o que
   o leitor de tela anuncia e o que uma busca por texto encontra. **Só o
   nome do diretor** muda de caixa — gêneros, duração e fonte continuam em
   sans caixa normal, como a v1.9.26 decidiu; isto **não** é uma volta ao
   mono-caixa-alta que aquela versão removeu. Conferido com o nome mais
   longo do catálogo (`FRANCIS FORD COPPOLA`, 20 caracteres): cabe em uma
   linha no desktop e quebra limpo no mobile, sem hifenização nem estouro.

   ##### O BACKDROP DISSOLVE, e o título INVADE — com piso de contraste

   O backdrop deixa de ser bloco fechado: **sem `border-radius`, sem margem
   inferior**, terminando dissolvido no fundo da página. O par ano → título
   **começa SOBRE a imagem**, dentro do fade, e **termina no fundo escuro** —
   a passagem de obra visual para conteúdo editorial vira contínua, não um
   corte.

   **O REQUISITO DURO: contraste garantido em QUALQUER backdrop.** Os
   backdrops variam muito no brilho da faixa inferior, e um degradê que só
   "escurece um pouco" entrega contraste diferente por filme — os que
   ficarem bons ficam por sorte.

   **A CONSTRUÇÃO — a mesma ideia do degradê da célula do mosaico (v1.9.29,
   título legível sobre pôster claro), adaptada.** O degradê chega a **100%
   opaco antes do fim da imagem**, formando uma **faixa chapada** na base; o
   recuo negativo do texto é **menor que essa faixa**. O texto, portanto,
   **nunca pousa sobre pixel de imagem** — só sobre `--bg` já chapado.

   | | fade | faixa 100% opaca | recuo do texto | folga |
   |---|---|---|---|---|
   | desktop | 232px | 68px | 58px | 10px |
   | ≤640px | 156px | 58px | 52px | 6px |

   **A CONSEQUÊNCIA é o que torna o requisito verificável: o contraste vira
   INDEPENDENTE DA IMAGEM.** Não é "medimos os 34 e deu bom" — é que a
   imagem **não entra na conta**.

   **Duas diferenças para o mosaico, ambas deliberadas.** (a) Lá a base do
   degradê é **preta** (a célula é um card sobre fundo escuro e o preto some
   nela); aqui é **`--bg`**, porque o degradê tem de casar exatamente com o
   fundo da página — qualquer outra cor deixaria emenda visível onde a
   imagem acaba. (b) As paradas são em **px, não em %**: a faixa chapada
   precisa ter a mesma altura que o recuo, que é em px; em % ela mudaria de
   altura com a proporção do backdrop (de 3840×2160 a 3500×1969 no
   catálogo) e o casamento quebraria sem sintoma.

   **MEDIDO — composição analítica sobre os pixels reais dos 34 backdrops**
   (imagem `w1280` baixada, luminância relativa WCAG, composição
   `img×(1−α) + bg×α` com o α exato de cada parada do degradê, pior pixel
   de cada linha que o texto ocupa):

   | | título (`--text`) | ano (`--text-mute`) |
   |---|---|---|
   | **fade da v1.9.32, nos 34** | **17,15:1** | **4,56:1** |
   | texto sobre o fundo puro `#0b0c10` | 17,15:1 | 4,56:1 |
   | fade da v1.9.30, se o texto invadisse (pior caso) | 4,92:1 | **1,31:1** |

   Em **34 de 34** o fundo sob o texto compõe **exatamente `#0b0c10`** —
   idêntico, dígito a dígito, ao fundo da página. **Nenhum filme fica
   abaixo do piso**, e não há caso a tratar. O ano a 4,56:1 passa o AA de
   texto normal (4,5:1) e **é o mesmo valor que ele já tinha** em qualquer
   outro ponto do site: não há regressão, e o teto dele é uma dívida
   pré-existente da paleta, não desta versão.

   **O PIOR BACKDROP DO CATÁLOGO NÃO É O QUE SE SUPUNHA, e vale registrar.**
   A hipótese de trabalho era `dune-2021` (céu claro embaixo). Medindo a
   luminância média da faixa inferior dos 34, `dune-2021` é o **12º**
   (0,098); os dois piores são **`barbie` (0,370)** e **`the-hateful-eight`
   (0,351)**. Com o fade antigo, `barbie` daria **1,33:1** no ano — texto
   praticamente ilegível. Com o novo, 4,56:1 como todos os outros.

   ##### O ACOPLAMENTO FECHADO POR CONSTRUÇÃO (v1.9.33)

   **A INVARIANTE, em uma frase: o recuo do texto é sempre menor que a
   faixa opaca, e é isso que faz a imagem não entrar no cálculo de
   contraste.**

   Na v1.9.32 essa invariante vivia em DOIS comentários, num arquivo só,
   sobre DOIS números que só concordavam porque alguém fez a conta certo
   uma vez: a faixa chapada do degradê (`68px` em `.backdrop::after`) e o
   recuo do texto (`58px`, `--hero-overlap`). Nada no CSS impedia editar um
   sem lembrar do outro — mudar a faixa sem tocar no recuo teria revertido
   a garantia **em silêncio**, e o sintoma só reapareceria como título
   ilegível no próximo backdrop claro que entrasse no catálogo.

   **A correção segue o mesmo padrão de `--k` na barra de proporção**
   (§3[E]: uma propriedade é a fonte, as fronteiras e a diagonal são
   funções puras dela). Aqui: **`--fade-solid` é a fonte** (a faixa chapada
   — o único número pensado para se ajustar), e **`--hero-overlap` é
   `calc(var(--fade-solid) - var(--fade-folga))`**, com `--fade-folga` uma
   constante **fixa e sempre positiva** (10px no desktop, 6px em ≤640px).

   **Por que isto fecha a desigualdade por ARITMÉTICA, não por disciplina.**
   Subtrair um número positivo de `--fade-solid` produz, por definição de
   subtração, um valor **menor** que `--fade-solid` — não é uma verificação
   que roda, é uma propriedade da própria expressão. Mudar só
   `--fade-solid` (para dar mais ou menos invasão do título) move
   `--hero-overlap` **junto, na mesma direção**, e a desigualdade não pode
   quebrar por essa edição. O único jeito de quebrá-la seria zerar ou
   negativar `--fade-folga` — e ela é declarada como constante justamente
   para não ser o dial que uma entrega futura mexe sem pensar.

   **Os estágios intermediários do degradê também deixaram de ser paradas
   fixas independentes.** `--fade-opaco-em: calc(var(--fade-h) -
   var(--fade-solid))` é o ponto em que a opacidade chega a 100%, e as três
   paradas parciais do gradiente são **frações dessa mesma distância**
   (`× 0.415`, `× 0.756`, `× 0.927`) — editar `--fade-h` ou `--fade-solid`
   redesenha a curva inteira de forma consistente consigo mesma, em vez de
   deixar paradas antigas apontando para uma altura que já não existe.

   **O breakpoint mobile deixou de redeclarar o gradiente inteiro.** Como
   `.backdrop::after` já é 100% `calc()`/`var()`, a media query de `≤640px`
   só sobrescreve as três variáveis-fonte (`--fade-h`, `--fade-solid`,
   `--fade-folga`); `--fade-opaco-em` e `--hero-overlap`, por serem
   `calc()`, recalculam sozinhas quando o navegador resolve as regras que
   as consomem — não precisam ser redeclaradas.

   **VERIFICADO, não só argumentado — em dois sentidos.** (1) *Regressão
   zero:* os valores computados depois da refatoração são **byte-idênticos**
   aos de antes, nos dois breakpoints — desktop `18,1px` de título sobre a
   imagem (o mesmo de `the-invite-2026` na v1.9.32), mobile `12,1px` (o
   mesmo de `the-godfather`/`barbie`). (2) *A invariante segura sob
   tensão:* sobrescrevendo `--fade-solid` para `20px` em runtime, SEM tocar
   em mais nada, `--hero-overlap` recalculou sozinho para `calc(20px -
   6px)` = `14px` — a desigualdade se manteve automaticamente, exatamente o
   comportamento que o design promete.

   **A garantia agora é estrutural: não existe edição de um valor só que a
   viole**, exceto zerar/negativar a folga — e essa é uma ação deliberada
   sobre uma constante nomeada como tal, não um efeito colateral de ajustar
   a faixa.

   ##### O LINK DO LETTERBOXD, secundário

   Deixa de ser pill: **sem caixa, sem borda, sem fundo** — mono pequena,
   na mesma direção do disclosure APROFUNDAR da v1.9.26 (parte do bloco
   editorial, não componente pousado nele). Desce do topo para logo abaixo
   da linha de metadados.

   **O que NÃO foi sacrificado junto com a caixa:** continua `<a>` de
   verdade, `target="_blank"` + `rel="noopener noreferrer"`, **foco visível**
   (`:focus-visible` com contorno de 2px) e **área de toque de 46px medidos
   no mobile** (≥ 44px recomendado) — o padding vertical continua existindo,
   invisível mas clicável. Um link discreto que fica difícil de acertar com
   o polegar seria downgrade de acessibilidade disfarçado de refinamento.

   **O TEXTO CONTINUA "reviews no Letterboxd", e não só "letterboxd".** O
   esboço do dono escreve a forma curta, e ela foi mantida longa de
   propósito: é o **nome acessível** do link, e o que ele promete é a LISTA
   DE REVIEWS daquele filme, não a home do site. Era a única perda de
   informação de uma entrega que pediu tratamento visual — decisão de uma
   palavra, trivial de reverter se o dono quiser a forma curta.

   ##### SEÇÕES NOMEADAS, e o rótulo que VOLTA

   Duas etiquetas, na tipografia mono de rótulo que o projeto já usa
   (mesma família, corpo e tracking; nenhuma família nova entra):

   - **RECEPÇÃO**, antes da barra — que passa a ser o primeiro grande bloco
     **nomeado** da página;
   - **EM DETALHE · TEMA A TEMA**, antes dos bullets.

   **"EM DETALHE · TEMA A TEMA" ESTÁ VOLTANDO, e a reversão é consciente.**
   Ele foi **removido na v1.9.26**, e a razão de lá está registrada acima:
   com o veredito descendo para o rodapé, não havia mais um resumo ANTES
   dos bullets do qual separar "o detalhe", e o rótulo virou promessa sem
   contraparte. **A razão de agora é outra**, e é isso que faz disto
   reversão e não vaivém: (a) a página passou a ter **seções nomeadas**, e
   numa página seccionada o bloco de bullets seria o único anônimo; (b) a
   **sinopse saiu**, e com ela o último texto corrido antes dos bullets — o
   leitor chega ali vindo direto da barra, e o rótulo é o que avisa que a
   régua mudou de "peso de cada grupo" para "o que cada grupo disse".

   A legenda `HATERS · MIXED · FANS` fica **abaixo dos percentuais**, que já
   era a ordem do DOM desde a v1.9.27 — nada mudou nela.

   ##### A REDUNDÂNCIA DE PESO — percorrida, MEDIDA, e MANTIDA por decisão do dono

   A pergunta levantada foi se peso aparece em três lugares (callout,
   legenda, cabeçalhos de grupo). **Medido: são DOIS, não três.** A legenda
   carrega **nome e cor**, nenhum número — ela é chave de leitura, não
   afirmação de peso. Os dois que afirmam peso com número são o **callout**
   (`~2% ~7% ~91%`, ancorado nas fatias) e o **cabeçalho de cada grupo**
   (`~91% DAS NOTAS`).

   **MEDIDO em `the-invite-2026`: 134px** entre o callout e o primeiro
   cabeçalho de grupo, e **os dois cabem na mesma tela** — tanto em
   1280×900 quanto em 375×812. Ou seja: o leitor vê `~91%` e, um terço de
   tela abaixo, `~91% DAS NOTAS`. **Isso lê como repetição**, e a medição
   não maquia isso.

   **DECISÃO DO DONO DO PROJETO: manter os dois, com a razão registrada —
   eles não servem ao mesmo leitor.** O callout serve a quem está **olhando
   a barra**: o número nasce ali, ancorado na fatia, no momento em que a
   proporção é o assunto da tela. O percentual do cabeçalho serve a quem já
   **rolou para dentro dos bullets** e está lendo tema por tema — sobretudo
   no **mobile**, onde os grupos empilham em vez de ficar lado a lado e o
   segundo bloco pode estar uma tela inteira de distância do callout. Ali o
   cabeçalho é o **único sinal de peso co-localizado com as listas** —
   exatamente a função que a v1.9.27 já tinha reconhecido ao **remover** o
   disclaimer da cota e manter o percentual do cabeçalho no lugar dele: *"o
   número no cabeçalho cobre a mesma leitura errada no lugar certo (ao lado
   dos bullets, não a 800px deles)"*. Tirar agora o segundo número
   reabriria exatamente o buraco que aquela remoção fechou.

   **A observação que continua valendo, e não muda a decisão:** a distância
   entre os dois **aumentou**, não diminuiu — na v1.9.31 publicada eram
   **65px** entre a legenda e o primeiro cabeçalho, contra **98px** agora,
   porque a etiqueta EM DETALHE entrou no meio. Isso torna os dois blocos
   mais claramente **duas leituras diferentes** (uma acima da etiqueta, uma
   abaixo dela) em vez de um número ecoando o de cima sem intervalo — o que
   é consistente com a razão de mantê-los, não uma correção adicional.
   **A CONDIÇÃO DA v1.9.27 CONTINUA DE PÉ:** *"se o percentual do cabeçalho
   algum dia sair da tela, [o disclaimer da cota] tem de voltar"* — nada
   nesta versão toca esse número, e a condição segue amarrada a ele.

   ##### ANIMAÇÃO DE ENTRADA DE ANO E TÍTULO — a coreografia, decidida

   Segunda animação de entrada da página, ao lado da sequência da barra
   (v1.9.28). **Decisão: rodam EM PARALELO, as duas a partir de 0ms**, e a
   do título é muito mais curta.

   | animação | início | duração | fim |
   |---|---|---|---|
   | ano (`hero-in`) | 0ms | 430ms | 430ms |
   | título (`hero-in`) | 70ms | 430ms | **500ms** |
   | barra · fronteiras | 0ms | 650ms | 650ms |
   | barra · ignição dos 3 números | 650ms | 260ms × 3, escalonados 55ms | **1020ms** |

   **Total da página: 1020ms — exatamente o da v1.9.28. O título não
   atrasou a barra em um único milissegundo.** Verificado pela Web
   Animations API: 13 animações na página (as **10 da barra, intactas**, as
   2 novas do herói e o `poster-in` de 240ms da imagem, que já existia).

   **POR QUE NÃO ENCADEADAS.** Encadear (título, depois barra) somaria
   ~500ms de tempo morto antes de o conteúdo começar a se mover, e **a
   barra é o conteúdo; o título é a moldura**. A página abriria com meio
   segundo em que nada do que ela veio dizer está acontecendo.

   **POR QUE O TÍTULO AINDA ASSIM "VEM PRIMEIRO".** Ele vem primeiro na
   ordem em que **termina**, não na em que começa: a moldura se assenta e
   fica parada enquanto o conteúdo ainda resolve. O olho pousa no que parou
   de se mexer. O escalonamento ano → título (70ms) é a única sequência
   interna, e é de leitura: o ano é metadado, o título é o assunto.

   **MESMA DISCIPLINA DA BARRA:** `transform` + `opacity` apenas (as duas
   propriedades que compõem sem relayout), **10px** de deslocamento,
   `cubic-bezier(0.22, 0.68, 0.28, 1)` — desaceleração pura, sem bounce,
   sem spring, sem overshoot.

   **`prefers-reduced-motion`: nenhuma das duas roda, estado final
   imediato.** Mesma construção da v1.9.27/v1.9.28 — **o estado base do CSS
   É o final**, e o estado INICIAL (`opacity: 0` + `animation`) vive inteiro
   dentro de `@media (prefers-reduced-motion: no-preference)`. **Verificado
   no CSSOM, não no arquivo:** varrendo `document.styleSheets`, a regra com
   `opacity: 0` para `.film-hero__text` aparece **1 vez dentro** do bloco
   `no-preference` e **0 vezes fora dele**. Se ela morasse fora, `reduce`
   deixaria o título invisível para sempre.

   ##### O FALLBACK SEM BACKDROP não herda a sobreposição

   Filme sem backdrop continua caindo no **pôster contido** (200px), e com
   ele volta a **composição antiga**: texto inteiramente ABAIXO da imagem
   (`.film-hero--poster` zera o recuo negativo). Um pôster 2:3 de 200px não
   tem faixa inferior larga o bastante para um título de 3,6rem, e deixar o
   título subir cobriria o cartaz. Conferido em `talk-to-me-2022`, o único
   do catálogo nessa condição: `margin-top: 0px`, texto começando 18px
   abaixo da base do pôster, estrutura nova (metadados soltos, link
   secundário, RECEPÇÃO, EM DETALHE) toda funcionando.

   #### O PÔSTER SEM TEXTO — DECISÃO FINAL: a arte limpa venceu (v1.9.30, decidido v1.9.31)

   **A queixa do dono:** os pôsteres são poluídos — bloco de créditos,
   tagline, laurel de festival. O TMDB serve **arte-chave sem texto**, que é
   a que declara `iso_639_1: null`, e o pipeline coleta em **campo próprio**
   (§3[F]): `poster_sem_texto_path` e suas dimensões. **Aditivo: não
   substitui `poster_path`**, que continua sendo o do próprio TMDB — o
   fallback abaixo depende de os dois campos coexistirem.

   **A v1.9.30 rodou as duas variantes ATIVAS e alternáveis por query
   param** (`?poster=texto` / `?poster=limpo`), o mesmo mecanismo de
   `?barra=`/`?ficha=` da v1.9.26, para a escolha ser feita **olhando**.

   **O DONO DO PROJETO COMPAROU AS DUAS E ESCOLHEU A ARTE SEM TEXTO
   (v1.9.31).** Seguindo a mesma convenção das duas decisões anteriores (a
   barra contínua venceu a divergente; a pilha de sistema venceu a Inter
   auto-hospedada): a variante vencedora fica como **único caminho**, e o
   mecanismo de escolha — o parâmetro, a leitura de `location.search`, o
   ramo condicional — **sai do JS**, não fica como opção morta atrás de
   flag. `?poster=` não existe mais em nenhum lugar do código; uma URL
   antiga com esse parâmetro não quebra nada, só o ignora, como já é o
   comportamento estabelecido para query params obsoletos de rodadas
   passadas.

   **VALE NA HOME, e só nela**, porque a página do filme trocou o pôster por
   um backdrop (v1.9.30) — não há pôster lá para variar.

   **O FALLBACK NÃO É RESQUÍCIO DO MECANISMO DE ESCOLHA — é a mesma regra de
   AUSÊNCIA que já rege backdrop e ficha desde a v1.3.0.** Filme sem arte
   sem texto usa o pôster normal (com texto); a lógica em `fonteDoPoster`
   (`poster.js`) é a mesma de antes, só sem o parâmetro decidindo entre as
   duas — agora ela sempre tenta a arte limpa primeiro e cai para a com
   texto quando o campo está ausente.

   **MEDIDO nos 35: os 35 têm arte sem texto — o fallback não é exercitado
   pelo catálogo de hoje, e existe para o filme obscuro que a expansão vai
   trazer.** Em **34** ela é uma imagem diferente do pôster normal; em **1**
   (`talk-to-me-2022`) o `poster_sem_texto_path` é **o mesmo arquivo** do
   `poster_path`, porque aquele registro do TMDB tem uma única arte e ela já
   é sem idioma. A home foi medida com a arte limpa como único caminho em
   **CLS 0** e altura de documento **1657px** — o mesmo número de antes da
   decisão: a variante troca o arquivo servido, não a geometria (a reserva
   usa as dimensões da imagem efetivamente escolhida).

   #### ATRIBUIÇÃO AO TMDB (v1.9.29) — obrigatória, não cosmética

   Até a v1.9.28 o site inteiro dizia apenas "fonte TMDB" numa linha de
   metadados da ficha, e não existia seção "Sobre" ou "Créditos". Os termos
   de uso da API exigem mais. Passa a existir:

   - **O aviso, de forma proeminente, em TODAS as páginas** (rodapé de
     `index.html`, `filme.html` e `creditos.html`) — um aviso escondido
     atrás de um clique não é proeminente. Texto **conferido contra a página
     oficial de atribuição do TMDB** antes de ser escrito, e não contra
     memória: *"This product uses the TMDB API but is not endorsed or
     certified by TMDB."* Ele aparece na página de créditos em inglês,
     LITERAL — é a frase que os termos pedem — com a tradução ao lado, porque
     o produto é em pt-BR e um aviso que o leitor não entende não avisa.
   - **`frontend/creditos.html`**, a seção "Sobre/Créditos" que o site não
     tinha: o que vem do TMDB, o que vem do Letterboxd, e o que o site faz
     com isso.
   - **O copyright das imagens não é do TMDB.** Registrado na spec e na
     página: os pôsteres pertencem aos estúdios e distribuidores; o TMDB
     apenas hospeda e declara não reivindicar propriedade sobre as imagens
     da API.
   - **O LOGO DO TMDB NÃO É USADO — decisão registrada.** Os termos permitem
     usá-lo desde que seja um dos oficiais, sem alterar cor, proporção,
     espelhar ou rotacionar, e menos proeminente que a marca do próprio
     Espectro. Nenhuma condição é difícil, mas o projeto não versiona
     binário nem baixa asset de terceiro (mesma regra dos pôsteres), e a
     atribuição em texto satisfaz a exigência por inteiro. Se o logo entrar,
     entra por decisão de design, não por obrigação.

   #### A LINHA DE METADADOS DA FICHA — tipografia (v1.9.26)

   A linha `DIR. · GÊNEROS · DURAÇÃO · FONTE` era monoespaçada em caixa
   alta com tracking largo, e lia como log de terminal. Passa a ser
   **sans**, em caixa normal, corpo maior e tracking quase nulo. Só a linha
   de metadados; `sinopse_oficial` continua serifada e intocada.

   **O pedido era "a fonte que a Apple usa" — a San Francisco (SF Pro) —, e
   ela NÃO PODE ser embutida.** A licença da Apple restringe o uso da SF
   Pro a mock-ups de interface para iOS/OS X/tvOS; não autoriza
   redistribuição nem uso como webfont em site próprio. **Nenhum arquivo de
   SF Pro é baixado, hospedado ou referenciado neste projeto**, e isso não
   é negociável. A saída legal é a **pilha de fontes de SISTEMA**:

   `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica,
   Arial, sans-serif` — entrega a **SF real** em Mac e iPhone porque usa a
   fonte **já instalada no aparelho do leitor** (o site não distribui
   nada), Segoe UI no Windows, Roboto no Android. Custo zero de
   carregamento; em troca, a página muda de aparência conforme o
   aparelho.

   **A alternativa comparada, e por que não foi a escolhida.** Uma segunda
   variante rodou lado a lado desta: **Inter**, desenhada como equivalente
   aberta da SF, auto-hospedada (SIL Open Font License 1.1, subconjunto
   latin, variável 400–700, 85 KB), idêntica em todo aparelho ao custo de
   85 KB de rede. **O dono do projeto comparou as duas e escolheu a pilha
   de sistema.** O arquivo da fonte, sua licença e o `@font-face` foram
   removidos do repositório junto com a escolha — não ficam sem uso
   ocupando espaço; se precisar voltar, o histórico do git tem o arquivo,
   a licença e a regra completos.

   **CORREÇÃO DE REGISTRO, para a spec não guardar uma frase falsa:** sans
   **não** é família nova no projeto. `--sans` (pilha de sistema) existe
   desde a v1 e é o que `body` e os campos de busca já usam — a paleta
   tipográfica sempre foi serifada + monoespaçada + sans de interface. O
   que é novo é usar **sans na linha editorial da ficha**, que era
   monoespaçada.

#### As TRÊS COLUNAS ALINHADAS POR EIXO (v1.9.14) — a promessa estrutural do produto

Até aqui o frontend exibia três listas de temas empilhadas, cada uma na sua
ordem, e a comparação entre grupos era trabalho mental do leitor. Com eixo
fixo, a mesma informação vira **uma linha por eixo, três células**:

```
Ritmo   |  arrasta (24/40)  |  lento mas justificado (11/40)  |  hipnótico (19/40)
```

A ordem das colunas é **sempre** negativas → medianas → positivas, nunca
reordenada por peso (regra inalterada desde a v1.4.0), e o formato das três
células é idêntico (§0: a assimetria vem do dado, não da apresentação).

**Os quatro estados que a renderização tem de tratar, e nenhum deles é
ausência de conteúdo:**

1. **Eixo presente em só um ou dois buckets.** A célula do bucket que não
   fala daquele eixo fica VAZIA, marcada como vazia — não é zero, não é
   traço solto: é "este grupo não fala disso", que é a informação.
2. **`contraste: valorativo`.** O alinhamento existe e é exibido
   normalmente; o que não existe é linha de contraste. A área ganha
   **enunciado próprio** — os grupos concordam sobre o que o filme é e
   discordam sobre se funciona —, nunca uma lista mais curta sem explicação.
   `cidade-de-deus` (melhor lift 10pp) é o **caso de referência** deste
   estado: se a interface parecer vazia ou quebrada nele, o estado não está
   desenhado como primeira classe.
3. **Bucket em estado reduzido do piso escalonado** (`sem_quantificador`,
   `sem_numero`, `sem_analise`). A linha acompanha o que AQUELE bucket pode
   dizer, célula a célula: sem número quando o piso proíbe número, sem
   célula nenhuma quando proíbe análise. A permissão já existe em código
   (`PERMISSOES_POR_ESTADO`, §D2) e é a mesma consultada aqui — não uma
   segunda regra que possa divergir dela.
4. **Filme sem bloco de eixos** (classificação ausente para aquele slug). O
   frontend cai na lista de temas anterior, sem quebrar. É o caminho de todo
   filme fora dos 35 classificados.

**Denominador: `X de N reviews classificadas`.** Distinto de "N de N
analisadas" no cabeçalho do grupo — não por preciosismo de vocabulário, mas
porque até a v1.9.14 eram duas amostras de 40 DIFERENTES (§[D3], "Duas
populações de 40"), e apresentá-las com o mesmo rótulo seria repetir
exatamente o defeito que a Entrega 6 daquela versão fechou do outro lado.
**Na v1.9.15 (Entrega 1) as duas populações foram unificadas** para os
filmes cuja classificação foi estendida — a nota de rodapé que declarava a
divergência (`denominadorNota`, `frontend/js/filme.js`) passa a exibir um
texto DIFERENTE quando `fonte_classificacao` está ausente do bloco: em vez
do caveat "não exatamente as mesmas reviews", confirma que a amostra é a
mesma. A chave `fonte_classificacao` só volta a aparecer — e o caveat com
ela — para um filme cuja seleção de produção ainda não foi estendida.

#### Busca — de decorativa a filtro real (v1.9.14)

A busca da home nunca filtrou nada: exibia "Busca em breve" e o catálogo
inteiro seguia abaixo. Com eixos, ela passa a ter um critério real —
**filtra por título e por eixo**, sobre o dado já embutido, sem rede. Digitar
`ritmo` devolve os filmes cujo bloco de eixos tem `ritmo`; digitar um título
segue funcionando como se espera. Sem resultado, a mensagem diz o que não
casou, em vez de fingir que a funcionalidade não existe.

#### Janela temporal declarada AO LADO DO DENOMINADOR (v1.9.14)

O defeito: a amostra de reviews cobre uma janela estreita (mediana ~26 dias)
enquanto o histograma de notas acumula desde 2012, e as duas frases apareciam
no mesmo parágrafo como se descrevessem as mesmas pessoas.

**Onde a declaração entra, e onde ela NÃO entra.** Ao lado do **denominador
da amostra** — *"entre as 40 reviews analisadas, escritas majoritariamente
em ⟨janela⟩"* —, **nunca** ao lado do rótulo de peso. O rótulo de peso fala
do histograma de NOTAS, que é a população acumulada da vida do filme;
carimbar nele uma janela de 26 dias inverteria o sentido e diria que 96% das
notas são recentes. É a mesma invariante de vocabulário notas × reviews da
v1.4.1, aplicada ao eixo do tempo.

**O número vem da MEDIANA, nunca da média.** Em `data` a média é ~10× a
mediana, por contaminação conhecida (`data` é a data ASSISTIDA, campo livre
de diário — há review datada de 1442 no catálogo). A média seria mais
lisonjeira (janela "mais ampla") e menos verdadeira; a mediana é robusta ao
outlier que a contaminação produz. Fonte: `janela_temporal` e
`distribuicao_pagina_origem`, ambos já calculados e persistidos desde as
v1.9.1/v1.9.2 — nenhuma coleta nova, nenhum parâmetro de coleta tocado.


---

## 4. Metadados obrigatórios no output

Por nível: `n_validas`, `n_brutas`, `filtro_aplicado`, `n_descartadas_spoiler`, `n_descartadas_curtas`, `n_descartadas_truncamento` (**v1.9.0: sempre 0** — uma truncada não resolvida não é mais *descartada*, ela fica no bruto marcada `texto_completo: false`; o número que importa passou a ser `n_indisponivel_truncamento`. O campo permanece para não quebrar consumidores existentes), `paginas_buscadas`, **(v1.9.0)** `n_alvo` (a alocação de §3[C1] para aquele nível — é o "ALVO" da ressalva 2, e sem ele a composição atingida não é interpretável), `n_indisponivel_truncamento` (persistidas mas inelegíveis por texto incompleto), **(v1.9.1)** `motivos_descarte` (dict `motivo→n` — §3[C2]; `n_descartadas_spoiler`/`n_descartadas_curtas`/`n_indisponivel_truncamento` passam a ser derivados dele, uma única fonte de verdade).
Por bucket: agregados dos níveis + `modo` (completo/reduzido/sem_analise) + **(v1.1.2)** `idioma_invalido`, `escopo_suspeito` + **(v1.9.0)** `estado_piso` (`completa`/`sem_quantificador`/`sem_numero`/`sem_analise`, §3[C3]), `composicao_alvo` e `composicao_atingida` (dicts nível→n, lado a lado — a mitigação obrigatória da ressalva 2 de §3[C1]), `cascata_por_degrau` (dict `chars`→n, quantas reviews entraram por cada degrau do relaxamento), `deficit_redistribuido` (int), **(v1.9.2)** `distribuicao_pagina_origem` (`{n, min, max, p5, p50, p95, fracao_profunda}` sobre a amostra SELECIONADA daquele bucket — §3[B'], instrumento temporal primário).
**(v1.9.0, campos ajustados nas v1.9.1/v1.9.2)** Bloco global `coleta`: `{ordenacao_usada, versao_coletor, coletado_em, paginas_gastas_por_nivel, paradas_por_limite, contagem_bruta_por_nivel, contagem_estimada_valida_por_nivel, n_reviews_bruto}` — espelha o `meta.json` do bruto (§3[B']) dentro do resultado, para que um JSON de entrega seja auditável sem abrir `dados/`. **(v1.9.1)** ganha `orcamento_paginas_por_nivel` (o orçamento dado a cada nível, derivado do orçamento por bucket — §3[B]) e `janela_temporal` (`{total, por_bucket}`, cada bloco `{n, min, max, p5, p50, p95}` — §3[B'], SECUNDÁRIA e rotulada como proxy contaminado desde a v1.9.2, não consumida pelo frontend). **(v1.9.2)** ganha `motivo_parada_por_nivel` (dict nível→`"orcamento_esgotado"`\|`"material_esgotado"` — §3[B], substitui `paradas_por_limite` como fonte primária de telemetria de parada; `paradas_por_limite` permanece, derivado, para não quebrar consumidores).
Por tema: **(v1.1.2)** `aspas_removidas`, além de `mencoes_clampadas`/`mencoes_valor_original` (v1.1.1).
Globais: `slug`, `data_coleta`, `origem` (cache/rede por página), versão da spec, **(v1.1.4)** `reviews_url`, **(v1.2.0)** `narrativa` + `narrativa_flags` (só quando `--tom narrativo|ambos`), **(v1.3.0)** `ficha` (objeto TMDB ou `null` — §3a), **(v1.3.1)** `consensos_usados` (lista de `{propriedade, grupos_de_origem, temas_de_origem}` do MOVIMENTO 2 — só quando `--tom narrativo|ambos`) + `narrativa_flags.consenso_suspeito`, **(v1.4.0)** `distribuicao` (bloco do histograma ou `null` — §3[G]) + `narrativa_flags.peso_nao_ancorado`, **(v1.4.1)** `quantificadores_usados` (lista de `{quantificador, tema}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.vocabulario_peso_suspeito`, **(v1.5.0)** `marcadores_perspectiva` (lista de `{grupo, trecho}` do MOVIMENTO 3 — só quando `--tom narrativo|ambos`) + `narrativa_flags.perspectiva_nao_marcada`, `metricas_fluencia` (`{n_frases, media_palavras, cv_comprimento, frase_mais_curta, aberturas_repetidas, verbos_reporte, adverbios_mente}` — só quando `--tom narrativo|ambos`), **(v1.6.0)** `narrativa_bruta` (saída do narrador antes da edição, para auditoria) + `edicao_flags` (`{edicao_descartada, motivo_descarte, protegidos_perdidos, numeros_alterados, houve_retentativa, falhou, n_protegidos}` — só quando `--tom narrativo|ambos` e sem `--no-edicao`; **(v1.7.3)** `n_tentativas` (quantas chamadas o editor fez, 1 a `1 + EDITOR_MAX_TENTATIVAS`) e `motivos_por_tentativa` (lista do motivo de cada falha, na ordem — telemetria de qual checagem mais reprova, não critério de aprovação); **(v1.7.4)** `similaridade` (float 0-1, SEMPRE presente, aceita ou não a edição) e `capitalizacao_ajustada` (bool)). **A flag `narrativa_flags.fluencia_baixa` foi REMOVIDA na v1.6.0** (ver §D2, "Telemetria de fluência"). Na ficha: **(v1.6.0)** `diretor_transliterado` (bool), **(v1.7.0)** `ano_fonte` (`"slug" | "letterboxd" | "argumento"`). Globais **(v1.7.0)**: `ficha_indisponivel` (`"ano_desconhecido"` — presente só quando a ficha não foi buscada por falta de ano confiável, §3[F]) e `ficha_descartada` (`{motivo, esperado, recebido}` — presente só quando o TMDB resolveu para um filme de ano divergente e a ficha inteira foi rejeitada, §3[F]); ambos ausentes do JSON no caminho normal (ficha resolvida com sucesso ou `--no-ficha`).
Por bucket: **(v1.4.0)** `share_real` (percentual inteiro), **omitido** quando não há distribuição.

**(v1.9.14) Bloco global `eixos`** — o schema do Ponto 2 (§2.5). Presente só quando existe classificação para o slug sob o `taxonomia_id` corrente; **ausente por completo** (chave não emitida) quando não existe, para que o consumidor distinga "não classificado" de "classificado e sem eixo". Estrutura:

```json
{
  "eixos": {
    "taxonomia_id": "ebab2667de74",
    "margem_lift_pp": 20,
    "contraste": "valorativo",
    "fonte_classificacao": {
      "arquivo": "resultado/votacao-3/consenso.jsonl",
      "criterio": "votacao_3_consenso_2_de_3",
      "por_bucket": {
        "negativas": {"n_classificadas": 40, "n_analisadas": 40,
                      "sobreposicao_com_analisadas": 13}
      }
    },
    "linhas": [
      {
        "eixo": "ritmo",
        "por_bucket": {
          "negativas": {"mencoes": 24, "de_n": 40, "freq_pct": 60,
                        "lift_pp": 27.5, "tema": "Ritmo lento e arrastado",
                        "exemplo_parafraseado": "…"},
          "medianas":  {"mencoes": 11, "de_n": 40, "freq_pct": 27.5,
                        "lift_pp": -32.5, "tema": null,
                        "exemplo_parafraseado": null}
        },
        "bullet_de": {"negativas": "contraste", "medianas": null}
      }
    ]
  }
}
```

`mencoes`/`de_n` são as contagens INTEIRAS — a fonte da verdade; `freq_pct` e `lift_pp` são derivados e arredondados **para exibição**. `tema`/`exemplo_parafraseado` vêm de §[D3] e são `null` quando aquele bucket não tem tema naquele eixo — célula vazia é estado, não falta de dado. `bullet_de` é `"frequencia"` | `"contraste"` | `null` por bucket, e é o que a interface lê para saber o que exibir como bullet daquele grupo. `contraste` é `"tematico"` | `"valorativo"` (§2.5), sempre acompanhado do `taxonomia_id` sob o qual foi decidido — o veredito descreve a régua atual, não o filme.

### (v1.9.34) O bloco `margem`, `acima_da_margem` por célula, e um DEFEITO que a lei por `n` expôs

**O defeito, primeiro, porque ele desmente uma frase que estava escrita aqui.**
Esta seção afirmava que *"nenhuma decisão do código lê os derivados (a comparação
com a margem é exata)"*. **Isso era falso desde a v1.9.20.** Dois consumidores a
jusante decidem lendo `lift_pp`, que é o float **arredondado a uma casa**:

- `veredito.py:_maior_lift` → o campo `acima_da_margem` do briefing, que é o que
  decide se o veredito diz "ASSUNTO PRÓPRIO deste grupo";
- `frontend/js/filme.js:veredito()` → a frase de veredito montada em código.

Com a margem fixa **inteira** de 20pp o defeito era inofensivo por acidente
aritmético: `lift_pp` vinha de múltiplos de `100/n` e nenhum arredondamento podia
cruzar um inteiro. **`limiar(n) = 144,4/√n` é irracional, e o acidente acaba.**
Uma célula a menos de 0,05pp do limiar decidiria diferente no código exato e no
consumidor arredondado. **MEDIDO nas 35 × 30 células sob a lei: 0 divergências, e
nenhuma célula a menos de 0,15pp da fronteira** — mas o mecanismo já está vivo
(`wicked-2024` tem buckets 37/40/37, logo quantum de lift de **0,068pp**), e a
expansão de catálogo o aciona.

**O ALCANCE do defeito, e ele é menor do que parece — a varredura completa
achou um TERCEIRO canal, e é ele que explica por que nada nunca apareceu na
tela.** `bullet_de` (§4, acima) é computado por `eixos.bullets()` **com a mesma
comparação exata** de `contraste`, e é o que `briefing.py`, `frontend/js/
filme.js` (grade e ordenação de temas) e `frontend/js/home.js` leem para saber o
que é bullet de contraste. **Os BULLETS sempre estiveram certos.** O defeito
estava **confinado ao VEREDITO** — a frase que nomeia o assunto próprio de um
grupo —, em dois pontos (`veredito.py:_maior_lift` e o template de fallback de
`filme.js`), e não distribuído pela interface. Isto precisa ficar registrado
porque as duas coisas têm consequências diferentes: um defeito confinado a um
consumidor se conserta num lugar e não deixa rastro em dado publicado antigo;
um distribuído pela interface exigiria auditar tudo que já foi renderizado.
Aqui é o primeiro caso.

**A correção: `eixos.py` publica a decisão, e ninguém a recalcula.**

```json
{
  "eixos": {
    "taxonomia_id": "ebab2667de74",
    "margem": {
      "lei": "lift^2 * n >= 2085136/1000000",
      "constante_quadrada": [2085136, 1000000],
      "n": 40,
      "limiar_pp": 22.83
    },
    "margem_lift_pp": 22.83,
    "contraste": "valorativo",
    "linhas": [
      {"eixo": "ritmo",
       "por_bucket": {
         "negativas": {"mencoes": 24, "de_n": 40, "freq_pct": 60,
                       "lift_pp": 27.5, "acima_da_margem": true, "…": "…"}}}
    ]
  }
}
```

- **`acima_da_margem`** (bool, por célula) é calculado por `eixos.py` em
  `Fraction` exato e é **a única fonte de verdade sobre "esta célula atinge a
  margem"**. `veredito.py` e `filme.js` passam a LER este campo em vez de
  comparar `lift_pp`. A frase de invariante volta a ser verdadeira, agora por
  construção e com teste que falha se alguém reintroduzir a comparação em float.
- **`margem_lift_pp`** continua existindo e continua significando "o limiar em pp
  que governou ESTE filme" — só que agora é o **limiar resolvido** (float, uma
  casa: 22,83 para n=40) em vez do inteiro 20. É **derivado e para exibição**;
  nenhuma decisão o lê.
- **`margem`** é o bloco novo, e existe por um critério só: **um artefato precisa
  poder ser auditado sozinho, sem consultar a versão do código que o gerou.** Ele
  carrega a lei em forma **exata** (a constante como par de inteiros, e o `n`
  usado), de modo que qualquer terceiro reproduza a decisão de cada célula com
  aritmética racional e sem adivinhar nada. `limiar_pp` fica ao lado, derivado,
  para leitura humana.
- **`contraste` pode estar AUSENTE** quando `n < 10` (§2.5). `margem`,
  `margem_lift_pp` e `acima_da_margem` **continuam presentes** nesse caso — o que
  falta é só a decisão binária do filme, não a medição das células. Um consumidor
  que assuma a chave `contraste` presente quebra, e **deve** quebrar.

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
- **v1.9.34** (2026-09-01) — **A MARGEM DE CONTRASTE DEIXA DE SER UM NÚMERO FIXO E PASSA A SER UMA LEI POR `n`.** Primeira mudança do arco que altera dado publicado e republica filmes. `limiar(n) = 144,4/√n` pp, `n` = o MENOR dos três buckets, comparado em `Fraction` **exato** pela forma quadrada `lift² · n >= Fraction(2085136, 1000000)` — que elimina a raiz e preserva a garantia da v1.9.15 (*nenhuma decisão de estado depende de arredondamento de float*). **Piso: `n < 10` → `contraste` AUSENTE do bloco `eixos`**, não `valorativo` — chave ausente distingue "não medido" de "medido e sem contraste". Catálogo: **6 `tematico` / 29 `valorativo` / 1 sem estado**, contra 18/17 publicados. §0, §2.5, §2.8, §2.9 e §4 reescritos.
  - **(1) O que motivou: o NULO DO MÁXIMO, uma medição que não existia.** O estado `contraste` nunca foi um teste — é o **máximo sobre 30 células** (10 eixos × 3 buckets) comparado a um limiar, e o máximo de um conjunto ruidoso é enviesado para cima, com o viés crescendo quando `n` encolhe. As três medições anteriores (nulo por PAR de §2.5, bootstraps de `ESTUDO_CATALOGO_35.md` §8 e `MEDICAO_VERIFICACAO_BINARIA.md`) mediam outras coisas. Desenho registrado ANTES de rodar (`DESENHO_NULO_DO_MAXIMO.md`, com previsões escritas para poderem falhar — **uma falhou e está reportada como falha**); resultados em `ESTUDO_MARGEM_20PP.md`. **MEDIDO:** 20pp cai no percentil **82** do ruído com n=40; taxa de falso contraste **17,3%** em n=40 e **37,3%** no `n` mediano em que o catálogo foi de fato publicado; **6 de 35** filmes distinguíveis do nulo a α=0,05, **1** sobrevivendo a Holm; FDR de **24–38%** entre os 16 `tematico`.
  - **(2) O número que decidiu, e é sobre as páginas no ar.** Nos **6 filmes cujo veredito nomeia por extenso a causa que separa os grupos e que o dado completo não sustenta** (`ESTABILIDADE_10_FLIPS.md`), a probabilidade média de aquele contraste ter vindo puramente de ruído era **0,633**. Não é "a margem é porosa": é seis páginas nomeando uma causa que tinha ~63% de chance de ser sorteio.
  - **(3) O `n` publicado NUNCA foi 40 — a correção de registro que reenquadra §2.8/§2.9.** Reconstruído do campo `de_n` dos 35 JSONs: mediana **28**, média 27,3, mínimo **5**; **56 dos 105 buckets abaixo de 30** e **24 abaixo de 20**. `perfect-days-2023` publica com [18, 12, 17]; `hereditary` com [22, 13, 16]. O regime era muito pior que o "n≈40" que o registro supunha.
  - **(4) As três opções não eram três.** **MEDIDO:** o valor crítico do nulo a α=0,05 varia **0,12pp** entre os 29 filmes com 40/40/40 — o "critério estatístico" É o "limiar fixo" para 29 dos 35, e só diverge nos 6 com bucket abaixo de 40, o que É o limiar por `n`. A decisão real era binária: o limiar olha para `n` ou não. E o critério estatístico recalculado em produção foi **rejeitado por um motivo de arquitetura, não de estatística** — um p-valor por permutação faria o estado depender de uma SEMENTE, regressão direta no compromisso central do §2.5.
  - **(5) §0 ganha a frase que faltava: neutralidade de tratamento é MESMA EXIGÊNCIA PROBATÓRIA, não mesmo número.** O mesmo 20pp é o percentil **3** do ruído com n=10 e **99,8** com n=100 — um número constante exige provas sistematicamente diferentes, e mais frouxas exatamente onde o dado é mais fraco. O precedente é o próprio §0 na v1.9.30 (*"a ordem antiga não era neutra — era CONSTANTE, que é outra coisa"*), e o teste que ela usou passa aqui: a regra é função do DADO (`n` é contagem de reviews, não juízo), e **`n` é o mesmo para os três buckets dentro de um filme**, travado por teste. O que se perde está escrito: comparabilidade entre páginas, em 6 dos 35 filmes.
  - **(6) O critério "cerca de um terço do catálogo" está APOSENTADO, e a razão é medida.** Era um alvo de COBERTURA, fixado quando `valorativo` era o estado fraco. **MEDIDO:** os 17 vereditos `valorativo` publicados são **17 textos distintos, com zero frases de mais de 25 caracteres repetidas** — o defeito das v1.9.21–23 está morto; e o ramo `valorativo` nomeia o `assunto_compartilhado`, que vem de **FREQUÊNCIA**: no evento real de cobertura 70,7%→100%, o eixo que ele nomeia mudou em **8 de 35** filmes contra **16 de 35** do eixo de maior lift. **Mover um filme para `valorativo` move a afirmação publicada da estatística menos estável para a mais estável.** O critério que entra é de ERRO (taxa de falso contraste ≈5%); a contagem de `tematico` é consequência, não alvo.
  - **(7) α = 0,05 e não 0,10, por assimetria de dano.** `tematico` errado publica causa falsa em prosa categórica; `valorativo` errado subafirma. Quando os erros custam diferente, o nível se escolhe pelo mais caro. **Registrado como escolha, não como fato:** a multiplicidade entre os 35 filmes NÃO é corrigida, porque cada página faz sua própria afirmação lida isoladamente — quem pedir Holm não está errado, está pedindo um catálogo com 1 `tematico`.
  - **(8) LIMITAÇÃO IN-SAMPLE, escrita onde quem expandir o catálogo vá encontrá-la (§2.5).** A lei foi calibrada sobre exatamente os 35 filmes que ela julga; com 35 não há como separar treino de teste. **A taxa de 5% é in-sample e otimista**, e a constante 144,4 carrega a estrutura de co-ocorrência de eixos deste corpus (**corr(carga de eixos, P(falso)) = +0,74**). A expansão é o primeiro teste out-of-sample e deve ser tratada como teste: rodar o nulo nos filmes NOVOS e comparar com a tabela — se divergir, é a constante que se recalibra.
  - **(9) UM DEFEITO PRÉ-EXISTENTE que a lei expôs, e a frase da spec que ele desmentia.** §4 afirmava que *"nenhuma decisão do código lê os derivados"*. Falso desde a v1.9.20: `veredito.py:_maior_lift` e `frontend/js/filme.js:veredito()` decidiam comparando `lift_pp`, o float **arredondado a uma casa**. Com margem inteira o defeito era inofensivo por acidente aritmético; com um limiar irracional o acidente acaba. **MEDIDO: 0 divergências nas 35 × 30 células de hoje, e nenhuma célula a menos de 0,15pp da fronteira** — mas o mecanismo está vivo (`wicked-2024`, buckets 37/40/37, quantum de **0,068pp**). Correção: `eixos.py` publica **`acima_da_margem` por célula**, exato, e os dois consumidores passam a LER em vez de recalcular.
  - **(10) O carimbo, e o critério que o decidiu: um artefato precisa poder ser auditado SOZINHO.** O bloco `eixos` ganha `margem` (`{lei, constante_quadrada, n, limiar_pp}`) — a lei em forma **exata**, com o `n` usado, para que um terceiro reproduza a decisão de cada célula sem a versão do código que a gerou. `margem_lift_pp` sobrevive com o mesmo significado ("o limiar em pp deste filme") e passa a ser o limiar RESOLVIDO (22,83 em n=40) em vez do inteiro 20; segue derivado e para exibição.
  - **(11) §2.9 FECHA, e uma correção de registro dela.** A defasagem entre artefatos publicados e consenso estendido é resolvida pela republicação desta versão. **MEDIDO:** dos 10 filmes de §2.9, só **2** teriam estado diferente sob a lei em relação ao que a republicação sob 20pp lhes daria — o argumento de "trabalho refeito" valia **4 regenerações** (20 contra 16), não o trabalho inteiro. A razão forte para esperar era outra: republicar sob 20pp colocaria no ar 16 estados com FDR de 24–38%.
  - **(12) Fora de escopo e NÃO tocados:** taxonomia, `taxonomia_id`, cota 40/40/40, `assunto_compartilhado`, piso de 25%, `min_chars`, seleção 2+3 de bullets, métrica de lift, fronteiras de bucket, ordenação, pôster/backdrop/barra/disclosure/rótulos/home. Nenhuma reclassificação, nenhuma coleta. **A "quarta opção"** (publicar a confiança ao lado do estado) foi avaliada e **NÃO implementada** — bom complemento, péssimo primeiro passo. **E os 5 filmes que trocam de estado em função de o verificador de `impacto_emocional` ter rodado ou não** (`dune-2021`, `eighth-grade`, `im-still-here-2024`, `napoleon-2023`, `the-godfather`) ficam para a próxima sessão: é instabilidade de CLASSIFICAÇÃO, fonte separada desta. A republicação usa `consenso_verificado.jsonl`, para não misturar as duas.
- **v1.9.33** (2026-08-27) — **O piso de contraste do backdrop fecha por CONSTRUÇÃO, não por comentário.** Até aqui a faixa chapada do degradê (68px) e o recuo do texto (58px) eram dois números concordando por acaso — editar um sem o outro reverteria a garantia em silêncio. `--hero-overlap` passa a ser `calc(var(--fade-solid) - var(--fade-folga))`, com `--fade-folga` uma constante fixa e sempre positiva: subtrair um positivo de `--fade-solid` produz por aritmética algo menor que `--fade-solid`, então a desigualdade **não pode** ser violada mudando só o dial pretendido (`--fade-solid`). Os estágios do degradê também derivam de `--fade-h`/`--fade-solid` via `--fade-opaco-em`. **Verificado nos dois sentidos:** os valores computados são byte-idênticos aos de antes da refatoração (18,1px/12,1px de invasão do título); e sobrescrever só `--fade-solid` em runtime moveu `--hero-overlap` junto, sem quebrar a desigualdade. Mesmo padrão de `--k` na barra de proporção. Nenhum arquivo de `resultado/` no diff; suíte inalterada.
  - **Redundância de peso (callout + cabeçalho): MANTIDA, por decisão do dono.** Os dois não servem ao mesmo leitor — o callout serve a quem está olhando a barra, o cabeçalho a quem já rolou para os bullets (sobretudo no mobile, onde os grupos empilham e o segundo bloco fica longe do callout). É o único sinal de peso co-localizado com as listas, a mesma função que a v1.9.27 preservou ao remover o disclaimer da cota. Nada mexido.
- **v1.9.32** (2026-08-27) — **O TOPO VIRA EDITORIAL: a sinopse sai, o backdrop se dissolve com o título invadindo a imagem, o link do Letterboxd vira secundário, a página ganha seções nomeadas e o par ano → título ganha animação de entrada.** Só frontend: **nenhum arquivo de `resultado/` no diff**, pipeline intocado. Suíte Python: **1525 passando**, inalterada.
  - **(1) A SINOPSE SAI, e o card com ela** — decisão final do dono. A linha de metadados sobrevive **solta**, sem card. **O custo, registrado e não maquiado:** o público-alvo é quem ainda NÃO assistiu, e a sinopse era o único elemento da página que dizia **do que o filme trata** — sem ela os bullets chegam sem premissa onde se apoiar. **Baixo hoje** (35 filmes conhecidos, backdrop expressivo) e **crescente na expansão** (obscuros, estrangeiros), que é a parte que não aparece enquanto o catálogo for o de hoje. §3[E].
  - **(2) ATRIBUIÇÃO CONFERIDA e intacta.** A linha de metadados continua vindo do TMDB e continua com "fonte TMDB"; o aviso exigido segue no rodapé das três páginas e `creditos.html` segue no ar. Saiu junto só o aviso de sinopse em inglês — avisava sobre um texto que não está mais na tela; o campo `sinopse_fallback_en` continua no JSON.
  - **(3) DIRETOR EM CAIXA ALTA, sem "dir."** — caixa alta pelo CSS, **nunca pelo dado** (`toUpperCase()` mudaria o que o leitor de tela anuncia). Só o nome; gêneros/duração/fonte continuam em sans caixa normal, como a v1.9.26 decidiu. Conferido no nome mais longo do catálogo (`FRANCIS FORD COPPOLA`).
  - **(4) BACKDROP DISSOLVIDO + TÍTULO INVADINDO, com PISO DE CONTRASTE por construção.** O degradê chega a **100% opaco antes do fim da imagem** e o recuo do texto é menor que essa faixa chapada (desktop 68px de faixa / 58px de recuo; mobile 58/52). **O texto nunca pousa sobre pixel de imagem** — e por isso o contraste é **independente da imagem**, não "deu bom nos 34".
  - **(5) MEDIDO nos 34 backdrops** (composição analítica sobre os pixels reais, α exato do degradê, pior pixel de cada linha): fundo sob o texto compõe **exatamente `#0b0c10` em 34 de 34** → título **17,15:1**, ano **4,56:1**, idênticos ao texto sobre o fundo da página. **Nenhum filme abaixo do piso.** Com o fade da v1.9.30, o pior caso daria **1,31:1** no ano. **O pior backdrop não é o suposto:** `dune-2021` é o 12º em brilho da faixa inferior; os piores são `barbie` e `the-hateful-eight`.
  - **(6) LINK DO LETTERBOXD SECUNDÁRIO** — sem caixa, sem borda, sem fundo, mono pequena, na direção do disclosure APROFUNDAR. Mantidos: `<a>` real, `rel="noopener noreferrer"`, foco visível e **46px medidos de alvo de toque** no mobile. **O texto continua "reviews no Letterboxd"** e não a forma curta do esboço: é o nome acessível, e o link promete a lista de reviews, não a home do site.
  - **(7) SEÇÕES NOMEADAS: RECEPÇÃO e EM DETALHE · TEMA A TEMA.** O segundo **está voltando** — removido na v1.9.26 porque, com o veredito no rodapé, não havia resumo do qual separar "o detalhe"; volta por **razão diferente**: a página passou a ter seções nomeadas e a sinopse saiu, então o bloco de bullets seria o único anônimo e o leitor chega nele direto da barra. Reversão consciente, não vaivém.
  - **(8) REDUNDÂNCIA DE PESO — percorrida, MEDIDA, NÃO corrigida.** São **dois** lugares com número, não três: callout e cabeçalho de grupo (a legenda tem nome e cor, nenhum número). **134px** entre eles, **os dois na mesma tela** em 1280×900 e em 375×812 — lê como repetição, e o relatório diz isso. A distância **aumentou** (de 65px para 98px entre legenda e cabeçalho: a etiqueta EM DETALHE entrou no meio), e a condição da v1.9.27 que preserva o percentual do cabeçalho continua valendo. Nada mexido.
  - **(9) ANIMAÇÃO DE ANO E TÍTULO — em PARALELO com a da barra.** Ano 0→430ms, título 70→500ms, barra 0→1020ms. **Total da página: 1020ms, o mesmo da v1.9.28 — o título não atrasou a barra em 1ms**; 13 animações medidas (as 10 da barra intactas + 2 novas + o `poster-in` que já existia). Encadear somaria ~500ms de tempo morto antes de o **conteúdo** se mover, e a barra é o conteúdo. O título "vem primeiro" na ordem em que **termina**. `prefers-reduced-motion` verificado **no CSSOM**: o estado inicial aparece 1× dentro de `no-preference` e 0× fora.
  - **(10) FALLBACK SEM BACKDROP não herda a sobreposição** — `.film-hero--poster` zera o recuo e o texto volta inteiramente abaixo do pôster contido. Conferido em `talk-to-me-2022`.
- **v1.9.31** (2026-08-27) — **DECISÃO FINAL do dono: o pôster SEM TEXTO vence e vira o único caminho na home. O mecanismo `?poster=texto`/`?poster=limpo` sai do código**, seguindo a mesma convenção das duas decisões anteriores (barra contínua venceu a divergente; pilha de sistema venceu a Inter). O parâmetro não existe mais em `poster.js`/`home.js`; uma URL antiga com `?poster=` não quebra nada, só o ignora. **O fallback continua** — filme sem arte sem texto usa o pôster com texto —, e não é resquício do switch: é a mesma regra de ausência que já rege backdrop e ficha desde a v1.3.0. Página do filme (backdrop) não foi tocada — já era definitiva desde a v1.9.30. Merge de `preview/posteres` em `main`, sem branch de preview.
- **v1.9.30** (2026-08-27) — **A ordem dos bullets passa a seguir o PESO; o topo da página do filme troca o pôster por um BACKDROP (exceção explícita ao anti-spoiler do §0, decidida pelo dono); e o pôster SEM TEXTO entra como variante testável na home.** Suíte Python: **1525 passando** (1512 da baseline + 13 novos em `test_ficha.py`), nenhum teste anterior alterado. `SPEC_VERSION` continua em 1.9.25, pelo mesmo registro da v1.9.26–v1.9.29.
  - **(1) ORDEM DOS BLOCOS EM DESTAQUE — por `share_real`, do maior para o menor.** `the-godfather` (2/5/93) abria a leitura por HATERS, 2% das notas. A regra é **função do dado, não do sentimento**: em `cats-2019` (86/7/7) o primeiro bloco continua sendo HATERS. A ordem fixa anterior não era neutra — era **constante**, que é outra coisa. **MEDIDO: a ordem mudou em 33 dos 35**; os 2 que ficaram iguais são os dois de recepção negativa dominante. Empate desempata pela ordem canônica, explicitamente no código. Vale nos dois leiautes (o DOM é a ordem visual; no mobile, FANS em y=1203 e HATERS em y=2166 em `the-godfather` a 375px). **Neutralidade de tratamento intacta:** mesmo leiaute, mesmo peso tipográfico, 6 e 6 bullets, mesmas cores — só a POSIÇÃO muda. §0 e §3[E].
  - **(2) A BARRA NÃO É REORDENADA.** A ordem dela é **semântica** — eixo ordinal de 0,5★ a 5★. HATERS → MIXED → FANS na barra, na faixa do mosaico, na legenda e no `aria-label`, conferido depois da mudança. A dessincronia com os bullets é pequena na tela (uma rolagem de distância, e o callout já ancorou cada peso na sua fatia).
  - **(3) DESCOMPASSO COM O VEREDITO — ressalva reportada, veredito NÃO tocado.** Estágio fechado, nada regenerado. **MEDIDO: 6 de 35 depois da mudança, contra 31 de 35 antes** — a ordem fixa é que estava fora de sincronia quase sempre, porque o texto do LLM tende a abrir pelo grupo dominante.
  - **(4) BACKDROP no topo da página do filme — EXCEÇÃO EXPLÍCITA AO §0, registrada por extenso.** Decisão do dono, tomada com o trade-off na mesa: **sem curadoria de spoiler**. O produto anuncia "0 spoilers" e resolve todo trade-off contra o spoiler (bullets filtrados, veredito proibido de citar reviravolta); o backdrop é quadro do filme, **sem garantia nenhuma** de não ser do terceiro ato, e ocupa a posição mais proeminente da página, antes da sinopse. Ganha-se leitura horizontal, menos espaço vertical desperdiçado e abertura editorial; perde-se a promessa anti-spoiler **neste elemento** — não enfraquecida, **não valendo**. §3[E].
  - **(5) QUAL backdrop — ordem TOTAL, no pipeline.** sem texto → `vote_average` → `vote_count` → `width` → `file_path`. "Primeiro da lista" foi recusado com número: **em 3 dos 35** o primeiro da resposta não é o escolhido, e a API não declara desempate. "Maior resolução" escolheria o maior arquivo, não o melhor quadro. A escolha sai de dentro dos ≤10 coletados — o `backdrop_path` é sempre um item de `backdrop_paths[]`, travado por teste. A preferência por arte sem texto **afeta 2 dos 35** (`joker-folie-a-deux`, `longlegs`, os dois com key art de campanha vencendo).
  - **(6) FALLBACK e CLS.** Sem backdrop → pôster; sem os dois → estado de ausência desenhado. **34 dos 35 têm backdrop.** **CLS medida: 0** na página do filme (0 entradas de `layout-shift`), em desktop e a 375px; o título fica em **y=530,52 com e sem a imagem**, e **sem a reserva** o salto seria de **405px**. Home reconferida: CLS 0 e 1657px de altura, o mesmo número da v1.9.29.
  - **(7) CDN `w1280` para o backdrop.** Lista própria (`w300 · w780 · w1280 · original`). Coluna de 680–720px CSS pediria 1360–1440; o degrau seguinte é `original` (~1,5 MB), proibido. `w1280` entrega 1,78–1,88× em densidade 2 — custo declarado. `alt` = "Imagem de &lt;título&gt; (&lt;ano&gt;)": diz o que a imagem É, e **não** a chama de "cena".
  - **(8) PÔSTER SEM TEXTO — campo próprio, aditivo, variante só na HOME.** `?poster=texto` (DEFAULT, e é **só** default) / `?poster=limpo`, pelo mecanismo temporário das rodadas anteriores. **Nenhuma requisição nova** — mesmo bloco `images`, confirmado por teste que conta as chamadas. **MEDIDO: os 35 têm arte sem texto**; em 34 é imagem diferente do pôster normal, em 1 (`talk-to-me-2022`) coincide.
  - **(9) A CHECAGEM DE CACHE virou lista de chaves, e quase mordeu.** A regra da v1.9.29 olhava só `tmdb_fetched_at` — que as 35 entradas **já tinham**. Mantida, esta versão teria devolvido os campos novos ausentes em silêncio, nos 35: o defeito exato que aquela regra existia para evitar. Agora é presença das chaves da versão corrente (`_CHAVES_COMPLETUDE`), e presença, não verdade.
  - **(10) RETROFIT dos 35 pelo harness existente**, travas por teste em vigor e guarda de identidade mantida. Diff conferido campo a campo: **nada fora do bloco `ficha`**; dentro dele, os seis campos novos mais `tmdb_fetched_at`. `poster_path`, dimensões e `backdrop_paths[]` vieram idênticos.
  - **(11) RESSALVA PRÉ-EXISTENTE, encontrada e NÃO corrigida: `talk-to-me-2022` publica a ficha de outro filme** — um curta de 3 minutos ("The Elms Estate: You Can Talk To Me", `tmdb_id` 976680) no lugar de *Talk to Me* (2022). Falha de desambiguação do TMDB, publicada desde a v1.3.0, invisível para a guarda de ano (ambos 2022) e para a guarda de identidade (disco e resposta são o mesmo filme errado). É a razão real do único "sem backdrop" do catálogo. Corrigir é **republicar**, não retrofitar: mexeria em título, sinopse, diretor e duração, e a narrativa e o veredito foram escritos sobre a ficha errada. §3[F].
- **v1.9.29** (2026-08-27) — **PÔSTER entra no catálogo: o pipeline coleta imagens numa chamada única, os 35 publicados ganham os campos por RETROFIT, a célula da home é REDESENHADA em torno do pôster, e o site ganha a ATRIBUIÇÃO ao TMDB que os termos exigem.** Não é galeria: `backdrop_paths[]` é coletado e **não renderizado em lugar nenhum** (§3[F] — o TMDB não garante backdrop livre de spoiler, e "0 spoilers" é a promessa central, §0). Suíte Python: **1512 passando** (1492 da baseline + 20 novos: 10 de imagens em `test_ficha.py`, 10 do harness em `test_enriquecer_ficha.py`), nenhum teste anterior alterado. `SPEC_VERSION` continua em 1.9.25 pelo mesmo registro da v1.9.26–v1.9.28.
  - **(1) Coleta, custo marginal ZERO.** `images` entra no `append_to_response` que já trazia `credits` — nenhuma requisição nova. Campos novos: `tmdb_id`, `tmdb_fetched_at`, `poster_path`, `poster_largura`, `poster_altura`, `backdrop_paths[]` (teto 10).
  - **(2) `include_image_language` é `pt`, NÃO `pt-BR` — correção MEDIDA da instrução original.** O parâmetro aceita ISO-639-1 e descarta um código de localidade em **silêncio**. Dos 9 filmes sondados, **7** perdiam as dimensões do pôster com `pt-BR,null`; com `pt,null`, nenhum. Sem o parâmetro, `backdrops` volta vazio para filmes de pouca cobertura (`eighth-grade`: 0 contra 18).
  - **(3) O pôster é o `poster_path` do próprio TMDB.** A cascata pedida já é o que aquele campo entrega (ele é sensível a `language`) — medido antes de decidir, e registrado em vez de reimplementado. As DIMENSÕES, que ele não traz, vêm de `images.posters`; não são sempre 2:3 (`aftersun` 1632×2449, o curta experimental 505×750).
  - **(4) Retrofit dos 35 por harness próprio,** `scripts/enriquecer_ficha.py`, travado por teste como na v1.9.21/v1.9.25. **Medido: 35 de 35 com pôster, 0 sem, 0 falhas.** Diff conferido campo a campo nos 35 `resultado/*.json`: **zero alteração fora do bloco `ficha`, zero alteração dentro dele fora das 6 chaves novas, ordem de chaves preservada.** A guarda de identidade disparou de verdade em `mother-2017` e revelou a causa (buscar pelo título pt-BR em vez do título do slug resolve outro filme).
  - **(5) Home: REDESENHO da célula.** 4/5 → 2/3, pôster ocupando a célula, texto num degradê na base, faixa de recepção de 5px → 6px com fio. **A animação da barra NÃO roda na home** — decisão registrada. **Layout shift medido: CLS 0**, geometria byte-idêntica com e sem as imagens; sem a reserva de proporção o título saltaria 298px na página do filme. **`w342` na home (1282 KB nos 35, 37 KB de média), `w500` na ficha.**
  - **(6) Rastreabilidade e o teto de 6 meses.** `tmdb_fetched_at` grava a data de obtenção de TODOS os campos vindos do TMDB. Os termos proíbem cachear por mais de 6 meses, e o projeto guarda ficha indefinidamente desde a v1.3.0 — **limitação pré-existente que os pôsteres tornam visível**, não problema novo. **Nenhum cache, revalidação, expiração ou coleta de lixo foi construído**, deliberadamente: a entrega é a data, que é o que torna a política possível depois.
  - **(7) Atribuição.** Aviso proeminente em todas as páginas + `frontend/creditos.html`. Texto conferido contra a página oficial do TMDB. Logo não usado, por decisão registrada. Registrado que o copyright dos pôsteres é dos estúdios — o TMDB apenas hospeda.
  - **PRESERVADO e conferido:** barra de proporção (posição, geometria, animação da v1.9.28), disclosure APROFUNDAR, rótulos HATERS/MIXED/FANS, glossário da home, exceção do bucket dominante, ordem da página. Nenhum veredito ou narrativa regerado. Nenhuma segunda fonte de imagem. Nenhum backdrop renderizado.
- **v1.9.28** (2026-08-27) — **FRONTEND: a animação da barra troca de modelo — as FRONTEIRAS DESLIZAM de uma partição em terços até a distribuição real — e o neon dos percentuais deixa de decair e fica ACESO.** Sessão de interface: os únicos arquivos alterados são `frontend/js/filme.js` e `frontend/css/styles.css` (mais SPEC.md e `frontend/TESTE_MANUAL.md`). **Nenhum filme regenerado, nenhum `resultado/*.json` tocado, nenhum estágio do pipeline alterado.** Nenhuma biblioteca de animação adicionada. Suíte Python: **1492 passando, intacta**. `SPEC_VERSION` continua em 1.9.25 pelo mesmo registro da v1.9.26/v1.9.27 (a constante carimba artefato de PIPELINE).
  - **(1) O MODELO fill 0→100% SAIU INTEIRO, e a camada de prefill neutra foi REMOVIDA** do JS e do CSS — não escondida atrás de flag. A barra passa a **nascer completa**, particionada em três partes iguais, com as fronteiras deslizando até `h` e `h+m`. As antigas Fase 1 (fill) e Fase 2 (partição) viram **uma**. Linha do tempo nova: **fronteiras 0→650ms · ignição 650→1020ms · total 1020ms** (era 1190ms).
  - **(2) UMA FUNÇÃO TEMPORAL SÓ, e é literal — não são duas animações sincronizadas.** `--k` é um `<number>` registrado por `@property`, animado UMA vez na barra; as duas fronteiras e a diagonal são funções puras dele. **E a arquitetura de camadas empilhadas dá a garantia mais forte ainda:** a camada de baixo ocupa 100% da barra em todo frame, então a terceira região é "o que sobra" e a soma fecha **por construção**, não por sincronia. Três segmentos independentes em flex/grid foi recusado por ser justamente a forma que deixa buraco. **Medido em 60 quadros** (6 filmes × 2 tamanhos × 5 instantes): soma = **100,00000 em todos**; erro absoluto máximo entre a fronteira medida e a prevista por `x_i(k)` com o MESMO `k` = **0,070pp** em desktop e **0,151pp** a 375px — e o erro escala exatamente com `1/largura_da_barra`, que é a assinatura da resolução do instrumento (varredura por hit-test a 0,25px), não da animação.
  - **(3) NENHUM PIXEL TRANSPARENTE ENTRE REGIÕES, verificado e não presumido.** Varredura por `elementFromPoint` a cada 0,25px, em **três alturas** (topo, meio, base — a base é onde a diagonal mais corta), nos mesmos 60 quadros: **exatamente 3 regiões contíguas em todas as 180 varreduras**, zero ocorrências de "buraco" (a própria barra visível por baixo) e zero pontos sem elemento. A verificação é de **hit-test**, não de amostragem de pixel — está registrado assim em `TESTE_MANUAL.md`.
  - **(4) `--diag` durante a interpolação: ACOMPANHA (Ponto 1 decidido).** As duas variantes foram construídas e medidas lado a lado. Escolhida a que acompanha, pelo argumento que o dono já tinha: a diagonal é função do dado EXIBIDO, e durante o deslize o dado exibido é o interpolado. **E é visível:** em `the-godfather` a 375px, no meio da animação, a variante fixa desenha 3,68px entre duas regiões largas — lê como corte reto, não como a diagonal da barra publicada; a que acompanha desenha 12px e a barra lê como o mesmo objeto do começo ao fim. **O risco de tremor foi medido e não existe:** 131 amostras de 5ms, zero reversões nas duas arestas da diagonal, nas duas variantes; o ponto mais fino da fatia de 2% nunca desce de 4,861px. **O que custa, registrado:** o `clamp()` prende a diagonal no teto de 12px na primeira metade e a solta depois, então o valor é contínuo mas a taxa tem um canto (t ≈ 301ms a 375px) — medido em **0,947px por quadro** no máximo, contra **8,425px por quadro** da própria fronteira, ~9× mais lento que o movimento em que viaja.
  - **(5) Os rótulos durante a interpolação: AUSENTES (Ponto 2, recomendação do dono aceita sem contraproposta).** O empacotamento do callout não depende de `--k` — as posições são as finais desde o primeiro frame —, então um `~2%` visível durante o deslize ficaria meio segundo apontando para uma região que naquele instante é 33%. Rótulos e indicadores acendem depois, já no lugar certo e com o valor certo. **Isso reverte o `opacity: 0.16` da v1.9.27**, que só fazia sentido enquanto a barra crescia vazia. O texto continua no DOM com o valor final desde o primeiro frame.
  - **(6) O NEON FICA LIGADO — correção da decisão da v1.9.27, pelo dono.** O brilho não decai depois do pico: estabiliza num estado aceso permanente (núcleo branco 2px, halo do grupo 6px, halo externo 11px a 20% de alfa). A ignição continua sendo o evento e o pico continua mais intenso (28px, ~35ms). Detalhe técnico que a mudança exigiu: **as quatro camadas de `text-shadow` são as mesmas em todos os quadros**, com a quarta zerada no repouso — `text-shadow` com contagem diferente de camadas não interpola, salta.
  - **(7) A COLISÃO QUE O NEON PERMANENTE CRIA, fechada pelas DUAS saídas.** Limitar o raio do halo (11px) **e** fazer o empacotamento contar o halo (`--gap` de 8px → 14px). Cada uma sozinha é frágil: só o raio deixa a garantia dependendo de um número que a próxima calibração de brilho mexe sem perceber; só a folga deixa o halo livre para crescer. Conta: `folga_entre_tintas = gap + 2P ≥ 2R`, com o pior caso sendo dois rótulos de 4 caracteres empacotados (`gap ≥ 11,08px`) — 14px deixa 2,92px de sobra **no pior caso que a regra admite**, não só nos 35 de hoje. **Medido** (folga entre as TINTAS, com `Range`; precisa de 22px): `the-godfather` e `cidade-de-deus` 32,17px nos dois tamanhos; `cats-2019` 32,17/32,18px; e o par mais apertado do catálogo, `eighth-grade` a 375px, **28,55px** — porque ali um dos rótulos tem 4 caracteres. Zero misturas.
  - **(8) ACESSIBILIDADE reconfirmada, com o item novo.** Sob `reduce`: 0 animações, `--k = 1`, barra na distribuição real e números acesos no primeiro frame — **e o neon permanente FICA**, conferido no `text-shadow` computado (não é movimento). Reativado: as 10 animações voltam e a sequência re-arma do zero. O `aria-label` descreve sempre o estado final e **o estado neutro de terços nunca é anunciado**. Os percentuais estão no DOM com os valores finais desde o primeiro frame.
  - **REGISTRO DE DEPENDÊNCIA NOVA: `@property`.** É o que torna `--k` interpolável — propriedade personalizada não registrada não interpola, salta no meio do keyframe. Degradação em navegador anterior a Chrome 85 / Safari 16.4 / Firefox 128: o `var(--k, 1)` de cada fórmula garante o **estado final correto em repouso**; o que se perde é a continuidade do deslize. Nunca fica errado parado — fica sem interpolação. Mesma política do fallback de `container-type` que já existia.
- **v1.9.27** (2026-08-27) — **FRONTEND: a barra de proporção ganha ANIMAÇÃO DE ENTRADA em três fases, os percentuais descem para um CALLOUT ancorado nas fatias, e o disclaimer da cota sai do ramo com barra.** Sessão de interface: os únicos arquivos alterados são `frontend/js/filme.js` e `frontend/css/styles.css` (mais SPEC.md e `frontend/TESTE_MANUAL.md`). **Nenhum filme regenerado, nenhum `resultado/*.json` tocado, nenhum estágio do pipeline alterado** — nada de §3[D], §3[D2], §3[D3], §3[V], seleção, coleta, classificação, verificação, briefing, prompt, validadores ou adaptador de LLM. **Nenhuma biblioteca de animação adicionada** (o projeto não tem nenhuma, e continua sem). Conferido no diff antes do commit. Suíte Python: **1492 passando, intacta**.
  - **NUMERAÇÃO, mesmo registro da v1.9.26.** `SPEC_VERSION` (config.py) e o título deste documento continuam em 1.9.25; a constante carimba artefato de PIPELINE e esta sessão não mudou pipeline nenhum. A decisão em aberto (se a numeração de frontend passa a subir o título) segue em aberto.
  - **(1) O DISCLAIMER DA COTA SAIU do ramo com barra (Entrega 1), e o percentual do cabeçalho FICOU — as duas coisas são UMA decisão.** A frase *"A barra é o peso real de cada grupo. A análise abaixo tem profundidade igual nos três — o tamanho das listas não indica peso."* saiu porque, com o callout, o topo passou a dizer o peso duas vezes e ela virou uma terceira explicação do mesmo fato a uma rolagem de distância das listas que existia para desarmar. **O que a remoção custa está escrito por extenso em §3[E]:** era a única frase em PALAVRAS contra a leitura "listas do mesmo tamanho, grupos do mesmo peso", e o que resta contra ela é o `~X% DAS NOTAS` no cabeçalho de cada grupo — o único sinal de peso CO-LOCALIZADO com os bullets. **Condição registrada: se o percentual do cabeçalho algum dia sair da tela, a frase tem de voltar.** O ramo SEM distribuição real (o degradado sintético) fica intacto no texto da v1.2.1, conferido; o render de TERMINAL não mudou.
  - **(2) CALLOUT DE PERCENTUAL abaixo da barra (Entrega 3), e a REGRA DE COLISÃO que ele exigiu.** Os três números passam a ficar ancorados na sua fatia, ligados por um indicador fino. A colisão é o problema real: `the-godfather` (2/5/93) tem os centros das duas primeiras fatias a 7,20px e 32,40px em desktop e a 3,35px e 15,07px a 375px, contra uma caixa de rótulo de 39,91px — e o pior caso do catálogo é `cidade-de-deus` (1/3/96). **Regra escolhida: empacotamento esquerda→direita com folga mínima, com o indicador inclinado absorvendo o deslocamento** (fórmula, alternativas rejeitadas e medições nos dois tamanhos em §3[E]). Ela vale para qualquer distribuição futura porque é uma passada de empacotamento e não uma exceção por filme: sempre tem solução enquanto `3L + 2g` couber na barra — 135,7px contra 335px a 375px. **A conta mora no CSS**, pela mesma razão de `--diag`: mistura dado (o centro da fatia), tipografia (`ch` da mono) e layout (a largura da barra), e `min()`/`max()` misturam `%` com `ch` — resize e zoom de fonte funcionam sozinhos, sem `ResizeObserver` e sem um recálculo em JS. **`aria-hidden` no callout diverge de propósito da decisão tomada para a legenda**, e a razão está em §3[E]: a legenda carrega o NOME do grupo e informa isolada; um `~2%` solto, não — e o `aria-label` da barra já anunciou os três, com rótulo, na mesma ordem.
  - **(3) ANIMAÇÃO DE ENTRADA em três fases (Entrega 2 + Fase 3), 1190ms no total.** fill 0→650ms (bloco único, cor NEUTRA, duração FIXA e jamais proporcional ao valor) · partição 650→820ms (3 camadas × 90ms escalonadas 40ms, esquerda→direita) · ignição 820→1190ms (3 números × 260ms escalonados 55ms). **A animação trabalha COM a arquitetura de camadas empilhadas, e não contra ela** — foi o que tornou a ordem da partição possível: o bloco neutro fica no fundo da pilha e as cores aparecem por cima dele, com a última camada (100% da barra) cobrindo o resto. **Nenhum frame introduz vão, gutter ou fio separador**: a barra contínua é decisão do dono do projeto e uma animação que abrisse um gap transitório contradiria a decisão em movimento. A expansão curta é `translateX` de `--diag × 0,35`, presa à MESMA escala adaptativa da diagonal (1,29px em `the-godfather` no mobile, onde um deslocamento fixo comeria a fatia de 6,7px). **O NEON É EVENTO, NUNCA ESTADO:** pico de ~35ms com núcleo branco + halo na cor do grupo, repouso com um único `0 0 7px` a 20% de alfa. **Zero temporizador em JS** — todo o encadeamento é `animation-delay` sobre `--ordem`.
  - **(4) ACESSIBILIDADE (Entrega 4) — o estado base do CSS É o estado final.** Tudo que a animação faz, INCLUSIVE os estados iniciais, vive dentro de `@media (prefers-reduced-motion: no-preference)`. Essa é a parte não óbvia: se os estados iniciais morassem fora do bloco, `reduce` deixaria a barra invisível para sempre, e o `* { animation: none !important }` que já existia não salvaria. Verificado nos dois sentidos (0 animações e estado final com o bloco inativo; 13 animações re-armando quando reativado). `aria-label` descreve sempre o estado final; os percentuais estão no DOM com texto de verdade desde o primeiro frame (a ignição começa em opacidade 0,16 — apagado, não ausente); sair a 400ms e voltar pelo histórico recomeça do zero e termina no estado final.
  - **(5) CADÊNCIA — implementado SEMPRE, e a leitura pedida vem com uma RESSALVA DE MÉTODO.** A sequência roda a cada visita, que é o que "sensação de estar sendo calculado na hora" pede. **A leitura honesta é que não pude formá-la por experiência:** o painel de navegação desta sessão roda em documento OCULTO, onde `document.timeline` fica congelado e as animações só avançam quando um frame é forçado (screenshot). Percorri os filmes e MEDI a sequência pela Web Animations API, mas **não a vi rodando em velocidade real nem uma vez**, muito menos várias seguidas — e cansaço em navegação repetida é exatamente o tipo de coisa que só a experiência mede. O que dá para dizer sem inventar: 1,19s é curto para uma visita e longo para a quinta seguida, e o único trecho que o leitor espera *sem receber informação nova* é a Fase 1 (650ms, mais da metade do total) — se a cadência incomodar, é dela que se corta, antes de trocar "sempre" por "uma vez por sessão". A decisão fica com o dono do projeto, que vai ver a animação antes de publicar.
  - **PRESERVADO e conferido:** geometria da barra (fronteira diagonal adaptativa, zero vão, proporção exata), ordem da página, disclosure APROFUNDAR, rótulos HATERS/MIXED/FANS e o critério rótulo-versus-prosa, glossário da home, exceção do bucket dominante (`napoleon-2023` e `friday-the-13th-2009` seguem com os três em destaque), ficha na pilha de sistema. **Conferência barra × cabeçalhos nos 35: zero divergência** — a fronteira medida na meia altura bate com o `share_real` normalizado em todos, exatamente como na v1.9.26.
- **v1.9.26** (2026-08-26) — **FRONTEND: a página do filme é reordenada em torno de uma BARRA DE PROPORÇÃO no topo, o veredito desce para o fecho, os três grupos ganham NOME DE RÓTULO (HATERS/MIXED/FANS) e o disclosure do bullet deixa de parecer botão.** Sessão de interface: os únicos arquivos alterados são `frontend/js/filme.js` e `frontend/css/styles.css`. **Nenhum filme regenerado, nenhum `resultado/*.json` tocado, nenhum estágio do pipeline alterado** — nada de §3[D], §3[D2], §3[D3], §3[V], seleção, coleta, classificação, verificação, briefing, prompt, validadores ou adaptador de LLM. Conferido no diff antes do commit. Suíte Python: **1492 passando, intacta**.
  - **NUMERAÇÃO, registro honesto.** `SPEC_VERSION` (config.py) e o título deste documento **continuam em 1.9.25**, e o teste que amarra os dois (`test_spec_version.py`) segue verde. A constante carimba `resultado/*.json` e existe para dizer sob qual versão do PIPELINE um artefato foi gerado; esta sessão não mudou pipeline nenhum, e subi-la faria o próximo filme gerado carimbar uma versão que não descreve nada do que ele contém. É o mesmo tratamento que as v1.9.17–v1.9.20 receberam (quatro versões de frontend numeradas no changelog enquanto a constante ficou parada) — com a diferença de que aqui a entrada é escrita NA SESSÃO, e não como dívida paga quatro versões depois. **Decisão em aberto para o dono do projeto:** se a numeração de frontend passar a subir o título, esta entrada e a constante sobem juntas.
  - **(1) A página reordenada (Entrega 1).** Ordem nova, de cima para baixo: ano + título → botão de reviews → ficha (sinopse + metadados) → **BARRA DE PROPORÇÃO** (nova) → linha arco-íris → bullets por sentimento, direto → **VEREDITO** (movido) → narrativa colapsada → pesquisa. O topo passa a ser ocupado pelo sinal DIMENSIONAL ("quanta gente de cada lado", legível de relance, sem leitura) em vez do VERBAL; o veredito é uma CONCLUSÃO, e conclusão lida antes da evidência é asserção, lida depois é fecho. O cabeçalho **"EM DETALHE · TEMA A TEMA" SAI** — não há mais um resumo antes dele do qual separar "o detalhe". O veredito muda de POSIÇÃO e **não de conteúdo**: mesmo texto, mesma origem, mesma geração, §3[V] intocado.
  - **(2) O DISCLAIMER DA COTA foi preservado, em forma mínima, e reancorado.** Ele é o que impede a leitura errada mais provável da página — listas de bullets do mesmo tamanho NÃO significam grupos do mesmo peso — e migra de baixo do cabeçalho removido para uma linha discreta **debaixo da barra**, onde a substância fica ancorada no objeto que mostra o peso: *"A barra é o peso real de cada grupo. A análise abaixo tem profundidade igual nos três — o tamanho das listas não indica peso."* O ramo sem distribuição real (o filme sintético degradado) mantém o texto da v1.2.1 inteiro, porque sem barra a regra volta a valer sozinha. Nenhum algarismo de contagem de review (v1.9.20 preservada).
  - **(3) A EXCEÇÃO AUTOMÁTICA DO MEIO (§0, v1.9.19) NÃO foi quebrada pela reordenação, e isso foi verificado e não presumido.** Quem decide se `medianas` sobe ao destaque é `sentimentGroupsBlock`, lendo `bucketDominante(f.buckets)` — função do DADO, não da posição do bloco na página; `veredictoBlock` não lê nem escreve esse estado (o prefixo do meio dominante já vem concatenado do Python dentro de `f.veredito.texto`). Varredura nos **35 filmes + o degradado**: os únicos com os três grupos em destaque são `napoleon-2023` (45% no meio) e `friday-the-13th-2009` (41%), exatamente os dois que a v1.9.19 registrou; os outros 33 mantêm o meio recolhido. O prefixo do dominante continua neutro nos dois.
  - **(4) BARRA DE PROPORÇÃO (Entrega 2) — FECHADA na variante `continua`.** *Duas rodadas de comparação até aqui: a primeira propôs três variantes com respiro escuro entre as faixas e foi REJEITADA inteira; a segunda propôs duas contínuas ("contínua" e "divergente"), e o dono escolheu a contínua — ver o item (11) para o diagnóstico da rodada 1 e o item (12) para a decisão final.* Faixa contínua fatiada em três, largura proporcional ao peso real, na ordem de leitura de sempre. A FONTE do número é `b.share_real` — a MESMA que os cabeçalhos imprimem —, não `distribuicao.por_bucket`, que carrega os mesmos valores: ler duas fontes para o mesmo fato é como se cria divergência silenciosa. **Sem número dentro da barra**; `role="img"` com `aria-label` completo (percentual de peso é número permitido pela v1.9.20, que proibiu contagem BRUTA de review). Paleta oficial, nada de verde/vermelho, fronteira em diagonal adaptativa. Descrição completa em **§3[E]**.
  - **(5) NOMENCLATURA DOS GRUPOS: `negativas` → HATERS, `medianas` → MIXED, `positivas` → FANS (Entrega 3).** Decisão de produto do dono, com objetivo de conexão geracional e campanha de marketing. **O trade-off, o escopo, a preservação da neutralidade ESTRUTURAL e a política de reversão estão escritos por extenso em §0** ("SEGUNDA EXCEÇÃO DELIBERADA na INTERFACE") — inclusive o reconhecimento de que "Fans/Haters" não é um par simétrico, e por quê. Resumo operacional:
    - **Troca onde o nome é RÓTULO ISOLADO** (cabeçalho do bloco de bullets, legenda e `aria-label` da barra, `aria-label` que identifica o grupo de um elemento), com o **mesmo destaque visual de antes**: mesmo peso, mesma cor de grupo, mesma posição.
    - **Mantém em PROSA** (veredito, narrativa, `observacao_geral`, prefixo do meio dominante gerado em código, avisos curtos de piso, disclaimer da cota). Verificado nos 35: **zero** veredito, aviso ou resumo de grupo colapsado contém rótulo novo.
    - **AS CHAVES INTERNAS NÃO MUDAM.** `negativas`/`medianas`/`positivas` seguem em JSON, briefing, prompts, validadores, spec, testes e nos atributos `data-group` que o CSS casa. Nenhum arquivo de `resultado/` tocado, nenhum filme regerado.
    - **UM PONTO SÓ.** O mapa vive em `GRUPO_LABEL` (`frontend/js/filme.js`) e em nenhum outro lugar; reverter os três rótulos é **uma edição de uma linha**. Isso é requisito, não conveniência: a aposta vai ser testada em público e o custo de errar foi desenhado antes de ela ser feita.
    - **ANOTADO, NÃO IMPLEMENTADO:** "MID" é mais idiomático que "MIXED" em pt-BR, e era o termo da versão originalmente arquivada.
  - **(6) O disclosure do bullet: "EXEMPLO PARAFRASEADO" → "APROFUNDAR", e deixa de parecer botão (Entrega 4).** UM rótulo só, igual nos dois estados — o indicador de estado é o chevron, e dois labels para a mesma coisa é ruído que o `aria-expanded` já cobre. **O pill da v1.9.19 sai inteiro** (fundo preenchido, borda, `border-radius: 999px`, padding de CTA): ele resolveu a afordance do "+" que ninguém percebia ser clicável, mas resolveu demais e virou o elemento mais chamativo de um bullet cujo protagonista é o NOME do tema. A referência agora é disclosure editorial minimalista (GOV.UK Details e afins) — fundo transparente, sem borda, sem cápsula, monoespaçada já existente, cor do próprio grupo com intensidade menor que o título e a barra. **Nenhuma linguagem visual nova.** Preservados: posição do controle no bullet, barras de frequência, hierarquia tipográfica, cores dos grupos, conteúdo expandido e a lógica de expansão/colapso.
  - **(7) A ANIMAÇÃO do disclosure — o requisito principal da entrega, acima do visual.** O conteúdo deve parecer que estava ESCONDIDO EMBAIXO do bullet e desliza para fora dele: efeito espacial e vertical, não fade. Três camadas, cada uma com um trabalho: a caixa externa ABRE (`grid-template-rows` de `0fr` para `1fr` — altura "até o conteúdo" sem altura fixa e sem medir nada em JS, evitando o hack de `max-height` chutado); a camada do meio RECORTA (`overflow: hidden`), que é o que faz o texto parecer estar atrás da borda de cima; a interna DESLIZA de 10px acima da posição final enquanto a caixa cresce, com a opacidade COMPLEMENTANDO (220ms contra 320ms), nunca substituindo. Fechamento pela mesma declaração ao contrário; chevron na mesma curva e na mesma duração.
    - **A curva foi escolhida por MEDIÇÃO, não por gosto** — altura da caixa amostrada a 0/80/160/240/320ms, nos dois sentidos, em três candidatas. Uma ease-out agressiva (`0.22,0.61,0.36,1`) colapsava **84% da altura nos primeiros 80ms** ao fechar, o que lê como corte e não como recolher; uma ease-in-out (`0.4,0,0.2,1`) espremia metade do movimento entre 80 e 160ms e dava 80ms de nada no começo da abertura, que num controle de manipulação direta lê como atraso. **`cubic-bezier(0, 0, 0.58, 1)`** é a única em que nenhum quarto da duração carrega mais que ~40% do movimento nos DOIS sentidos. **Sem spring e sem bounce**, e não por promessa: os dois pontos de controle ficam dentro de [0,1] e as séries medidas são monotônicas.
    - **A regressão de acessibilidade que a técnica traz de brinde, e a correção.** Ao contrário de `display: none`, uma linha de grid de altura zero **não** tira o conteúdo da árvore de acessibilidade — sem tratamento, um leitor de tela leria a paráfrase de todo bullet fechado da página. `visibility: hidden` no recorte resolve, com `transition-delay` igual à duração para o texto não sumir de uma vez no meio do fechamento. Conferido com `checkVisibility()`: o conteúdo colapsado dá `false`, o mesmo que o `<details>` da narrativa dá nativamente.
    - **Acessibilidade e responsividade:** continua `<button type="button">` nativo (Enter e Space são comportamento do agente, sem handler de tecla concorrente que pudesse cancelá-los), `aria-expanded` + `aria-controls` apontando para o elemento certo, anel de foco visível, área de toque de 44px sob `@media (hover: none)` e 40px no desktop, texto e chevron alinhados, integrado às duas colunas do desktop. **`prefers-reduced-motion` conferido**: as três transições morrem, o estado final é correto em aberto e em fechado, e a visibilidade deixa de ter atraso.
  - **(8) Tipografia da linha de metadados da ficha — FECHADA na pilha de SISTEMA.** *A variante Inter auto-hospedada rodou lado a lado desta para comparação e foi descartada pelo dono; ver o item (12).* A linha era monoespaçada em caixa alta com tracking largo e lia como log de terminal; passa a ser **sans**, caixa normal, corpo maior, tracking quase nulo. **O pedido era "a fonte que a Apple usa" — a San Francisco —, e ela NÃO PODE ser embutida:** a licença da Apple restringe a SF Pro a mock-ups de interface para iOS/OS X/tvOS e não autoriza redistribuição nem uso como webfont. Nenhum arquivo de SF Pro é baixado, hospedado ou referenciado. A pilha `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` usa a SF **já instalada no aparelho** — o site não distribui nada; Segoe UI no Windows, Roboto no Android; custo zero de carregamento, aparência variável por aparelho. Correção de registro sobre "sans não é família nova" em **§3[E]**.
  - **(10) Verificação — MANUAL e ENUMERADA, porque o frontend tem ZERO teste automatizado.** Varredura por iframe sobre os **35 filmes do catálogo + o degradado sintético**, conferindo por página: ordem dos blocos, posição do veredito, barra proporcional coerente com os percentuais dos cabeçalhos, rótulo certo para cada chave, prosa preservada neutra, rótulo antigo ausente, cabeçalho "EM DETALHE" ausente, "Exemplo parafraseado" ausente, disclosure fechado por padrão, e simetria estrutural entre negativas e positivas (**6 e 6 bullets em todos**). **Zero divergência.** Inspeção dirigida em desktop (1280×900) e mobile (375×812) nos casos de referência: `eighth-grade` (base), `napoleon-2023` (meio dominante), `obsession-2026` (amostra reduzida, avisos curtos), `the-godfather` e `talk-to-me-2022` (valorativos, veredito longo agora no rodapé), e a home. **Zero erro de console.** Alternativa textual da barra inspecionada na árvore de acessibilidade, não presumida.
    - **Limitação declarada da verificação:** o painel de navegador usado roda com `document.visibilityState === "hidden"`, o que congela a linha do tempo de animação e não entrega evento de teclado à página. As transições foram medidas pela **Web Animations API**, fixando `currentTime` e lendo o estilo computado quadro a quadro — mais preciso que cronometrar, mas não é o mesmo que ver rodar. O acionamento por Enter/Space foi verificado por PROPRIEDADE (elemento `<button>` nativo, na ordem de tabulação, sem handler de tecla que cancele o padrão), não por injeção de tecla de ponta a ponta. Registrado como o que é: uma rede a menos.
  - **(11) RODADA 2 do desenho da barra e da tipografia — as SEIS variantes da rodada 1 foram REJEITADAS e removidas.** O veredito do dono, na íntegra: a variante "sóbria" era *"extremamente dessaturada"*; a "angular", *"os formatos terríveis"*; e a "sólida" — a que ele considerou mais promissora — *"tem umas coisas interessantes, mas não dá ideia de continuidade: parece que são três barras separadas, cortadas com vão no meio"*.
    - **O VÃO era o defeito central, e o diagnóstico está certo por uma razão que vale registrar:** a recepção de um filme é **uma população particionada em três**, não três medições independentes. Um respiro entre as faixas desenha três objetos onde o dado tem um só — é erro de representação, não de acabamento. As duas variantes novas partem daí: zero gap, zero fio separador, zero respiro escuro.
    - **Consequência técnica da remoção do vão, e a correção que ela obrigou:** com respiro, as larguras usavam `flex-grow` proporcional com base 0, para o respiro sair do espaço livre e não roubar largura das faixas. Sem vão não há espaço livre a distribuir, e as larguras voltam a ser **percentuais somando exatamente 100** (a normalização pela soma continua necessária porque os três `share_real` são inteiros arredondados e somam 99–101 no catálogo).
    - **A `continua` precisou de camadas, não de fatias.** Fatias lado a lado com aresta inclinada deixariam um triângulo vazio em cada fronteira — o vão de volta, com outra forma. As três cores viraram camadas empilhadas, cada uma começando na borda esquerda e terminando na sua fronteira com recorte diagonal, a última preenchendo a barra inteira. Nenhuma superfície fica descoberta: cada fronteira é literalmente uma cor terminando em cima da outra.
    - **A diagonal é adaptativa e o cálculo mora no CSS.** `clamp(3px, 0,55 × menorFatia, 12px)`, com o percentual da menor fatia gravado pelo JS uma única vez (`--menor-pct`) e a conversão para pixel feita com `cqw`. **Achado, e corrigido na sessão:** a primeira implementação usava `ResizeObserver`, que **nunca dispara em documento oculto** — a barra ficaria com o ângulo de partida, errado, e sem nenhum sintoma visível. Foi trocada por unidade de contêiner, que reage a resize sozinha e não depende de callback nenhum. Fallback declarado em `@supports` para navegador sem unidade de contêiner.
    - **A `divergente` segue Heiberger & Robbins (2014), lido antes de implementar.** A regra central, na descrição dos próprios autores: *"The 'No Opinion' column is split into two. Columns on the 'Disagree' side are given negative values."* A ressalva obrigatória — parte do valor do padrão vem de comparar VÁRIAS linhas contra a mesma linha-base, e a página do filme tem uma só — está registrada em **§3[E]**, junto com a razão pela qual ele foi escolhido mesmo assim, e com a concessão dos próprios autores de que o gráfico de barras agrupadas é *"clear, accurate and easy to read"* e é rejeitado por enfatizar a comparação errada, não por ser menos legível.
    - **A LEGENDA DO MOSAICO DA HOME vira GLOSSÁRIO** — o caso de fronteira nº 1 da Entrega 3, escalado na rodada 1 e decidido pelo dono agora: nem manter, nem trocar. Passa a ser "**HATERS** (quem não gostou), **MIXED** (quem ficou no meio), **FANS** (quem gostou)", com as cores de grupo preservadas. Raciocínio completo em **§0** — a legenda é o único lugar do produto onde os dois vocabulários convivem de propósito, porque é onde o novo se ensina.
    - **BUG DE MEDIÇÃO achado na própria verificação, e vale registrar porque quase virou um falso positivo publicado.** A primeira varredura acusou 45 divergências entre a barra e os cabeçalhos na variante `continua`. Nenhuma era real: a sonda lia `--diag` com `getComputedStyle().getPropertyValue()`, que devolve a **cadeia `clamp(...)` não resolvida** (propriedade customizada não vira comprimento sem `@property`), o `parseFloat` dava `NaN`, e o fallback `|| 0` fazia a sonda esquecer de descontar meia diagonal da largura de caixa de cada camada. O erro batia exatamente com D/2 em todos os 45 casos. A varredura foi refeita medindo a **geometria realmente desenhada**, por hit-testing com `elementFromPoint` (que respeita `clip-path`) na meia-altura da barra, com bisseção para achar cada fronteira — método que não depende de ler valor de CSS nenhum.
  - **(12) DECISÃO FINAL DO DONO — barra `continua`, ficha `sistema`. O seletor, a variante `divergente` e a Inter foram REMOVIDOS.** Depois de comparar as quatro alternativas da rodada 2 no seletor em tempo real, o veredito: "gostei da barra contínua com ficha sistema, pode publicar ela como versão oficial". Nesta mesma sessão:
    - **O seletor `.vswitch` e `montarSeletor()`/`grupoDeOpcoes()`/`sincronizarURL()` saíram do JS e do CSS** — ele se anunciava como ferramenta de teste (item 9, rodada anterior) e cumpriu o papel: comparar em tempo real. Não sobrevive à escolha.
    - **`barraDivergente()` e as classes `.proportion__seg`/`.proportion__zero` saíram do JS e do CSS.** A construção completa (fórmula do zero, marca de divergência, a ressalva de Heiberger & Robbins) fica só no histórico do git e resumida em **§3[E]** — não apagada da spec, porque a leitura ("dividido, com leve inclinação positiva" em `napoleon-2023`) é um raciocínio de produto que pode voltar a ser relevante, mesmo sem o código.
    - **A variante `inter` de tipografia, o `@font-face`, `--sans-inter` e o diretório `frontend/fonts/` inteiro (arquivo woff2 + `OFL.txt` + `LEIA-ME.md`) foram REMOVIDOS do repositório.** Nenhuma fonte auto-hospedada sobrevive nesta versão — o produto usa só fontes de SISTEMA (serifada, monoespaçada, sans) mais a `--spectrum` da marca. Se a Inter precisar voltar, o histórico do git tem o arquivo e a licença completos; não é reconstruída de memória.
    - **`?barra=` e `?ficha=` deixam de existir como query param** — a página não lê mais `URLSearchParams` para nenhuma das duas escolhas. `?tint=1` e `?slug=` continuam (nada relacionado a eles foi tocado).
    - **Verificado depois da remoção:** suíte Python 1492 passando; `resultado/` intacto; a página renderiza a barra contínua e a ficha em sans-sistema em todos os 35 filmes + degradado, sem nenhuma referência residual a `divergente`/`inter`/`vswitch`/`data-variante`/`data-ficha` em JS ou CSS; zero erro de console.
- **v1.9.25** (2026-08-26) — **A retentativa de transporte desce para o TRANSPORTE e passa a valer para as DUAS portas de entrada do adaptador; o retry que engolia erro de conteúdo sai dos scripts; a telemetria atravessa o processo e chega ao relatório de lote.** Nenhum filme regenerado; nenhum `resultado/*.json` alterado.
  - **(1) O defeito da v1.9.24, verificado.** A retentativa entrou em `resposta()`, mas o adaptador tem DUAS portas de entrada: `resposta()` (narrador §D2, veredito §V) e `client_call` (síntese de bucket §D). A síntese entra pela segunda e **não estava coberta** — um 5xx nela continuava descartando o lote. A instrução da sessão anterior presumia um ponto de estrangulamento único que não existia; a lacuna foi reportada, não contornada por conta própria.
  - **(2) Eram QUATRO pontos de contato com o SDK, não dois.** `deepseek_resposta` (alcançado pelas duas portas), `_gemini_resposta` (só `resposta()`), `_gemini_call` (só `client_call`, com transporte PRÓPRIO duplicado) e `anthropic_client_call`. A retentativa desce para `deepseek_resposta`/`_gemini_resposta` numa implementação única (`_com_retentativa`), e as camadas de cima herdam. Classificação de erro, teto, backoff, jitter e telemetria são os da v1.9.24 — só mudaram de lugar.
  - **(3) `_gemini_call` passa a DELEGAR a `_gemini_resposta`,** espelhando `_deepseek_call`. A duplicata era exata: diff de AST mostrou que os corpos só diferiam em `resp.text` vs. resposta inteira e na grafia da checagem de chave; verificação em RUNTIME confirmou que as duas levantam `LLMError` com mensagem byte-idêntica, com teste congelando o caminho de chave ausente. `thinking_budget` repassado explicitamente, com teste de que chega inalterado ao SDK. **Pontos de contato com o SDK: 4 → 3**, travado por teste.
  - **(4) Ausência de aninhamento, testada.** Retentativa nos dois níveis daria `LLM_MAX_TENTATIVAS²`. Os testes atravessam as duas portas e contam o SDK falso, exigindo exatamente 3.
  - **(5) Lacuna registrada e NÃO consertada:** `anthropic_client_call` segue sem retentativa. Não é código morto — alcançável por `--provider anthropic` e por ter só `ANTHROPIC_API_KEY` no ambiente —, mas não está em nenhum default de produção e `resposta()` o rejeita.
  - **(6) O retry dos scripts: MEDIDO antes de tocar — e o ALCANCE da medição registrado.** 37.300 chamadas reais: **0 falhas permanentes, 8 retentativas (0,021%)**, todas resolvidas na 2ª. E um achado por si — **a classe das exceções absorvidas é irrecuperável**: `erro` só era gravado quando o laço esgotava, então no sucesso a classe era descartada. O anti-padrão estava em **oito** scripts, não nos três reportados. **As 37.300 chamadas são 100% DeepSeek, do estágio de classificação — não existe histórico equivalente para o Gemini**, o provider do incidente que abriu a v1.9.24. A retentativa não é conserto de falha frequente: é seguro contra evento RARO e CARO (perder um lote de ~300 filmes num pipeline limitado por scraping a 2s/requisição), e 0,021% medido no lugar errado não é evidência de que ela seja desnecessária.
  - **(7) Laço removido, REGISTRO mantido.** O `except` que grava `ok: False` fica — sem ele, `list(pool.map(...))` re-levantaria e uma review malformada em 8.171 abortaria o lote. Sai a repetição: erro de conteúdo passa a custar **1 chamada em vez de 3**, o transporte é retentado uma vez só (exponencial + jitter, não linear), e a taxa passa a ser IMPRESSA no fim de cada lote, porque todo consumidor pula `ok: False` em silêncio. Campo `tentativas` removido — ninguém o lia (verificado) e viraria meia-verdade.
  - **(8) `comparar_narrador.py` mantém o laço, deliberadamente:** não tem `except` dentro dele (transporte propaga na hora) e retenta por EXTRAÇÃO VAZIA, que é conteúdo, não transporte. Congelado por teste para não ser "consertado" nem copiado.
  - **(9) Guard-rail com discriminador explícito:** a varredura procura chamada de LLM dentro de laço de CONTAGEM (`for _ in range(...)`) cujo `except` não re-levanta. Laço sobre COLEÇÃO com `try` por item é o padrão normal de lote e NÃO é acusado — distinção necessária, achada por falso positivo em `comparar_narrador` durante a implementação.
  - **(10) Telemetria conectada, com o obstáculo real nomeado:** o harness roda o CLI como SUBPROCESSO, então o contador de módulo morre no filho. A travessia é uma linha em `stderr` (canal que o log já capturava), com formato e parser JUNTOS em `synthesize` — mesma lição de `quantificador.py`. `publicar_um` extrai para campo próprio; `--relatorio` agrega o LOTE. **`None` é "não sei" e conta à parte, nunca como zero** — somar maquiaria a taxa no caso em que ela importa.
  - **(11) Dois testes existentes foram reescritos, não deletados,** com a premissa invertida de propósito: `..._continua_sem_retentativa` (afirmava que o caminho direto NÃO retentava — verdade só enquanto a retentativa estava em `resposta()`) e `test_gemini_resposta_devolve_o_objeto_nao_o_texto`, que casava a linha literal do fonte e passou a asserir COMPORTAMENTO (mais forte, e imune ao próximo refactor).
  - **(12) Contrato de falha do LOTE, provado por comportamento, não só por `import`.** A remoção do laço (item 7) foi uma transformação automatizada com dois bugs de indentação corrigidos no processo — `import` prova que o arquivo parseia, não que o comportamento sobreviveu. Um teste de ponta a ponta com SDK falso, sobre os três caminhos de produção (`classificar_10`, `votacao_3`, `gate_taxonomia`), prova as QUATRO propriedades JUNTAS no MESMO lote: erro de conteúdo custa 1 chamada; o item vira `ok: False`; o lote não aborta (os itens seguintes são processados); e o resume retenta o item falho na execução seguinte, sem retocar os que já sucederam. **Achado no processo:** `classificar()`/`classificar_passe()` chamam `load_dotenv(RAIZ / ".env")`, e o `.env` real deste repo tem chaves — sem bloquear isso, os testes vazariam `DEEPSEEK_API_KEY`/`GEMINI_API_KEY` de verdade para o resto da suíte (`os.environ` não é revertido pelo `monkeypatch` quando quem escreve é `load_dotenv`), quebrando `detect_provider` em testes não relacionados. Corrigido com `monkeypatch.setattr("dotenv.load_dotenv", ...)` nos novos testes.
  - **(13) Tripwire para o `anthropic_client_call`.** A lacuna do item 5 (sem retentativa) não fica só em prosa: um teste afirma `"anthropic" not in PROVIDER_POR_ESTAGIO.values()`. Se um dia anthropic virar provider de ALGUM estágio de produção, o teste falha com uma mensagem que diz o porquê — a retentativa é pré-requisito para essa promoção — em vez da lacuna entrar em produção em silêncio.
  - **(14) Assimetria de prova entre os 8 scripts, DECIDIDA e registrada.** `classificar_10`/`votacao_3`/`gate_taxonomia` — os três que rodam sobre a amostra de PRODUÇÃO real — têm teste de comportamento de ponta a ponta; os outros 5 (`auditoria_acuracia`, `inspecao_assistir`, `variante_impacto_estrito`, `variantes_prompt_curtas`, `verificador_impacto`), scripts de análise/experimento fora do caminho que roda a cada expansão, têm só a prova estrutural do guard-rail AST + `import` — prova de parse, proporcional ao risco, não lacuna descoberta por acidente.
  - **(15) `load_dotenv` como efeito colateral de PRODUÇÃO, registrado como dívida — NÃO corrigido.** Os 8 scripts chamam `load_dotenv(RAIZ / ".env")` de DENTRO da função de classificação (não uma vez no import), escrevendo direto em `os.environ` a cada chamada — qualquer processo que importe e chame a função ganha as chaves do `.env` local como efeito colateral não pedido. Foi assim que a suíte vazou chaves reais para `test_provider.py` ao escrever os testes desta sessão. Comportamento PRÉ-EXISTENTE (nenhuma mudança de v1.9.24/25 o introduziu) e ortogonal ao objeto da sessão — fica fora de escopo. A contenção fica só no TESTE: um fixture autouse nomeado e documentado como contenção de efeito colateral de produção, não como configuração de teste, para não ser removido "por limpeza" sem que o vazamento seja entendido.
  - Suíte: 1455 → **1492**, todos passando; guard-rail do adaptador intacto; nenhum arquivo de `resultado/` tocado.
- **v1.9.24** (2026-08-26) — **Pré-requisito de expansão de catálogo: `synthesize.resposta()` ganha a retentativa de transporte que o `Fetcher` já tinha desde a v1.9.6. Nenhum veredito regerado; nenhum `resultado/*.json` mudou.**
  - **(1) O gatilho.** A v1.9.23 registrou como observação fora de escopo: um `ServerError` transitório do Gemini abortou um lote de 35 filmes no primeiro item. Com o plano de expansão para ~300 filmes, um 5xx no filme 12 descartaria o lote inteiro, e refazer é caro em HORAS — o scraping roda a 2s por requisição sem paralelismo (§2).
  - **(2) Mesmo desenho do Fetcher (§2.4), não um novo.** Só erro de TRANSPORTE retenta (timeout/falha de conexão/5xx), até `LLM_MAX_TENTATIVAS` (3) com backoff `2s · 4s` + jitter ±25%. Nunca erro de conteúdo/autenticação/cota/parâmetro inválido — esses continuam subindo na hora. Ponto ambíguo do SDK do Gemini investigado e resolvido: `httpx.TimeoutException`/`ConnectError` sobem crus (sem `HttpRetryOptions`, o SDK não os embrulha) e entram na lista de transporte ao lado de `errors.ServerError`.
  - **(3) Divergência deliberada do precedente, registrada.** O Fetcher tem `PressaoDoSite` — teto de 503 absorvidos POR LOTE, via objeto compartilhado passado a cada chamada. `resposta()` não tem hoje esse canal (narrador/veredito/scripts não repassam um objeto assim), e criá-lo exigiria plumbing fora de escopo. Só o teto por-chamada existe; teto por-lote fica candidato de sessão futura.
  - **(4) Onde vive, e por quê.** Dentro de `resposta()`, no mesmo lugar que despacha por provider — não num invólucro contornável. Esgotado o teto, levanta `LLMTransportError(LLMError)` encadeando o erro original. Teste com a técnica de `test_a_guarda_roda_dentro_de_cmd_publicar`: chama `resposta()` (o caminho real) e confirma retentativa real do transporte.
  - **(5) Gap registrado, não corrigido:** a síntese por bucket (§D, `synthesize_bucket`) usa um caminho de transporte separado (`client_call`/`_deepseek_call`) que nunca passa por `resposta()` — hoje em DeepSeek por padrão, não o Gemini do incidente. Estender a retentativa até lá tocaria código de síntese, fora de escopo aqui.
  - **(6) DeepSeek já tinha retentativa própria, em outro lugar e mais frouxa:** `scripts/classificar_10.py`/`gate_taxonomia.py`/`votacao_3.py` (classificação e votação de 3 passadas) já envolvem `deepseek_resposta` num catch genérico (retenta CONTEÚDO também) com backoff linear sem jitter. Não migrado nem removido — chamam o adaptador, não o SDK cru, então não violam o guard-rail; consolidação fica para quem mantém esses scripts.
  - **(7) Telemetria module-level:** `synthesize.telemetria_retentativa_llm()` acumula `n_retentativas`/`por_tipo` por PROCESSO (não por-objeto, como o Fetcher — `resposta()` não tem um objeto por-filme). Ainda não gravada em nenhum relatório (tocar `passada.py`/`render.py` está fora de escopo) — decisão registrada.
  - **(8) 17 testes novos** (`tests/test_retentativa_transporte_llm.py`): retenta 5xx/timeout e sucede na 2ª tentativa (DeepSeek e Gemini); nunca retenta 4xx de conteúdo/auth/cota nem exceção genérica; teto respeitado com telemetria correta; backoff exponencial verificado sem depender de tempo real (`time.sleep` espionado); a retentativa roda DENTRO de `resposta()`, provado chamando só esse caminho e espiando o transporte por baixo — e o contraste de que chamar `deepseek_resposta` direto (como os scripts) continua sem retentativa, documentando o limite exato da mudança. Suíte completa: 1438 + 17 = 1455, todos passando; guard-rail intacto.
- **v1.9.23** (2026-08-25) — **Medição, não correção: o molde contrastivo ganha número, `BEST_OF_N` maior é rejeitado, e a tautologia é diagnosticada.** Nenhum veredito foi regerado; o catálogo publicado continua sendo o da v1.9.22.
  - **(1) Observação de MÉTODO, e é o item mais importante desta versão.** A repetição MIGRA de dimensão a cada correção, e a métrica vigente captura exatamente a dimensão que acabou de ser consertada: a v1.9.21 consertou o texto idêntico e mediu por Jaccard, e a repetição foi para a ABERTURA (invisível ao Jaccard); a v1.9.22 consertou a abertura e mediu por padrão sintático, e a repetição foi para o MOLDE CONTRASTIVO (invisível ao padrão de abertura). Nos três casos o defeito seguinte foi achado por LEITURA, nunca por medição. **A regra que fica: estender a métrica ANTES de declarar vitória, não depois — uma dimensão não medida não é uma dimensão sem defeito, é uma dimensão sem número.**
  - **(2) Métrica nova: o CONECTIVO CONTRASTIVO principal** (primeiro, por posição, de uma lista fechada de 20 formas; `nenhum` quando não há). Linha de base: nos 35, **7 conectivos distintos com `enquanto` em 18/35 (51%)**; nos 17 `valorativo`, **4 distintos com `enquanto` em 14/17 (82%)**. **Nenhum dos 35 sai sem conectivo** — o molde contrastivo é universal no estágio. **NÃO registrado como defeito e nada no código reage a ele:** pode ser o piso do gênero, já que não existe forma neutra de dizer "um grupo acha X, o outro o contrário" em português que não seja contrastiva. A métrica existe para a decisão ser tomada com o número à vista.
  - **(3) `BEST_OF_N` maior: TESTADO E REJEITADO.** N=6 contra N=3, tudo idêntico fora do N: pior em três dimensões (fórmula de divergência 13/17 contra 12/17, `enquanto` 22/35 contra 16/35, Jaccard 0,0612 contra 0,0578), marginalmente melhor em uma (maior grupo de abertura 14 contra 16), empatado em duas — **ao dobro do custo (210 chamadas e 948s contra 105 e 501s)**. A diferença não excede a variância do próprio N=3 entre execuções (±2 na fórmula de divergência). **Amostrar mais da mesma distribuição rende mais da MODA, não mais da cauda** — o `empate` como critério decisivo sobe de 5 para 9. O gargalo não é o número de amostras, é a distribuição de saída do modelo, e o único instrumento restante para o molde contrastivo é o PROMPT.
  - **(4) Tautologia de um lado: diagnosticada, não corrigida.** Quatro filmes (`avengers-endgame`, `mother-2017`, `dune-2021` e `cats-2019`, este último não listado no relato original) têm um lado cujo conteúdo colapsa em reafirmação da divergência. **Causa ÚNICA e de DADO:** em todos os quatro, o lado tautológico é exatamente aquele cuja âncora de frequência tem `tema = None` — o briefing entrega o rótulo do eixo e nenhum conteúdo, e o modelo preenche o vazio. **Necessária mas não suficiente:** 12 dos 72 pares (filme, grupo) têm âncora sem tema, distribuídos por 10 filmes, e só 4 tautologizam; os outros 6 param na formulação honesta e fina ("centram suas análises em comparações"). **Contraexemplo relevante:** `dune-2021` JÁ recebe um aviso explícito de "sem tema nomeado" — mas no bloco do assunto compartilhado, não no bloco do grupo — e tautologiza mesmo assim, o que enfraquece a hipótese de que sinalizar resolve. Decisão pendente do dono do projeto.
  - **(5) Achado operacional, não corrigido (fora de escopo):** um `ServerError` transitório do Gemini abortou um lote inteiro de 35 filmes no primeiro item. O adaptador de LLM não tem retentativa de transporte, ao contrário do `Fetcher` (§2.4). Registrado como observação.
- **v1.9.22** (2026-08-25) — **Acabamento do veredito: deflação é falsidade, e a repetição migrou de LÉXICO para ESTRUTURA.** Três defeitos achados na LEITURA dos 17 `valorativo` publicados; nenhuma métrica da v1.9.21 os capturou.
  - **(1) Medição do Defeito 1 ANTES de corrigir, e ela corrige a premissa.** Nos 35 publicados: **zero rótulos fora do conjunto autorizado em 72 pares (filme, grupo)** — nem mais fortes nem mais fracos —, **61 dos 72 pares usam o rótulo EXATO**, e a deflação aparece em **2 filmes**. O defeito nunca foi o rótulo: foi o hedge que o SUBSTITUI (`pearl-2022`, "impressões negativas pontuais") ou que o ENVOLVE (`the-godfather`, "relatos pontuais apontam que a maioria…"). Corrigido também um erro de premissa da sessão: 58% resolve para `cerca de metade` e não para `a maioria` — a banda 40–60 vence `a maioria` (50–80) no empate, pela política da v1.2.3 de sempre resolver a fronteira compartilhada para o rótulo mais fraco.
  - **(1b) Instrumento de medição corrigido antes de valer.** A primeira versão atribuía cada quantificador ao marcador de grupo mais próximo e errou em 4 de 35: `defendem`, `discordam`, `contrárias` e `desfavoráveis` não estavam na lista de marcadores, e `pela maioria` não casava porque a regex exigia o artigo solto — sendo que a contração do artigo é forma LEGÍTIMA do rótulo desde §D2 (regra 4, v1.4.1). A medição definitiva é de nível de FILME, sem atribuição por proximidade, que é também o que a validação consegue sustentar num texto de 1–2 frases.
  - **(2) É violação do §0, não imprecisão de estilo.** Em `pearl-2022` os dois lados têm a MESMA frequência (58%, `cerca de metade` nos dois): o positivo recebeu o rótulo, o negativo virou anedota, e o que os separa é o SENTIMENTO do grupo. **E recorreria:** `negativas` está em modo reduzido em 5 dos 35 filmes e `positivas` em 2, e **não existe filme com positivas reduzida sem negativas também reduzida** — o catálogo é majoritariamente bem avaliado, então o grupo sem material é quase sempre o negativo, e uma regra que afrouxa a quantidade em amostra pequena afrouxa sempre do mesmo lado. Medição de simetria: dos **14** filmes com o mesmo rótulo nos dois lados, **10 simétricos**; dos 4 assimétricos, **1 por deflação** e 3 por OMISSÃO — e a omissão não tem viés de sentimento (2 calam o lado positivo, 1 o negativo).
  - **(3) Invariantes 4 e 9 do prompt corrigidas.** A 4 dizia "mais forte proibido, mais fraco permitido"; a segunda metade estava errada e era erro de especificação. O rótulo fornecido passa a ser o **único admissível**, e envolvê-lo em algo que o desminta é proibido. A 9 passa a dizer por extenso que **a cautela é sobre a AMOSTRA (quantas reviews foram analisadas), nunca sobre a FREQUÊNCIA** — com as formas permitidas e proibidas listadas. Invariante **9b** nova: rótulo igual nos dois lados exige tratamento textual igual.
  - **(4) Duas validações.** `quantificador_divergente` substitui `quantificador_mais_forte` e reprova nos DOIS sentidos (trava preventiva: reprova zero textos hoje). `deflacao_por_hedge` reprova adjetivo de magnitude reduzida sobre substantivo de review, **com exceção quando a frase ancora na amostra** ("analisadas", "disponíveis", "coletadas") — a exceção existe para `wonka`, que escreveu a única formulação honesta de "a base é pequena", e tem teste de regressão nomeado para ninguém "simplificá-la". Contrações do artigo passam a contar como o rótulo (`pela maioria` = `a maioria`), senão a checagem nova viraria falso positivo em quem escreve português correto.
  - **(5) Métrica nova e permanente: o PADRÃO SINTÁTICO DE ABERTURA.** Núcleo do primeiro sintagma nominal, truncado a 5 caracteres, com os rótulos de quantificador colapsados em `QUANT` (qual rótulo abre a frase é decisão do CÓDIGO — contá-lo como variação creditaria ao modelo a variedade do dado). A definição "núcleo + verbo" foi testada e DESCARTADA: reporta 22 padrões contra 7, **parece melhor porque é mais ruidosa** (sem analisador sintático, "está" colide com "esta" ao remover acento e o primeiro verbo finito costuma estar dentro do sujeito).
  - **(6) Defeito 2 atacado pela SELEÇÃO, não pelo prompt.** A frequência da abertura entra na chave ANTES da brevidade, sobre os candidatos que o best-of-3 já gera — custo zero de chamada. **A política de estabilidade que o tornou admissível:** o histórico é um SNAPSHOT dos padrões publicados, tirado UMA vez antes de qualquer escrita, com o próprio filme fora da conta — o resultado não depende da ordem dos filmes, e regenerar um filme isolado vê o mesmo histórico que a regeneração completa veria para ele. **Bug real achado ao implementar, invisível para os testes que rodavam contra sandbox:** o caminho de produção grava em `resultado/`, então recalcular o histórico a cada filme faria o segundo ver o veredito novo do primeiro — snapshot único é a correção, com teste de regressão que escreve por cima no meio do caminho.
  - **(7) MEDIDO, antes e depois, mesma régua.** Padrões de abertura **6 → 11**; maior grupo **18/35 → 16/35**; três maiores **32/35 (91%) → 23/35 (66%)**. Nos 17 `valorativo`: padrões **4 → 9**, fórmula de divergência na abertura **14/17 → 10/17**. Jaccard médio praticamente estável (0,0606 → 0,0598) e 35/35 textos distintos nos dois — como esperado, já que o defeito era estrutural e o Jaccard é cego a ele. Origem: **35/35 por LLM, zero `template_fallback`** antes e depois — a correção do Defeito 1 **não** elevou a taxa de fallback.
  - **(8) Defeito 3 desfeito de graça.** `the-godfather` empilhava ritmo, roteiro e comparações; a hipótese registrada era que o hedge truncado fosse parte da causa. Confirmado — o texto novo lê como prosa, e nenhuma estrutura foi criada para um caso único.
  - **(9) O mapa de faixas da v1.2.3 NÃO muda,** por decisão explícita do dono do projeto: é calibração intocada que atravessa a narrativa dos 35 e o §D2, e alterá-la a partir da leitura de um filme seria mudar o produto por porta lateral (mesma classe da margem de lift de 20pp, fechada na v1.9.21). A medição sustenta: no MESMO `pearl-2022`, o lado positivo com os MESMOS 58% recebeu `cerca de metade` corretamente.
  - **(10) O que NÃO foi resolvido, com número.** `QUANT` continua sendo a maior abertura (**16/35**) e a fórmula de divergência persiste em **10 dos 17** `valorativo`. O desempate só escolhe entre os candidatos que existem, e para vários filmes os três abrem igual — o teto do que a seleção alcança sem tocar no prompt. Rótulo AUSENTE segue como limitação aceita (2 filmes), com teste confirmando que as validações novas não forçam presença de rótulo por efeito colateral. As limitações de `tema_ausente` (detecta eixo, não tema) e `contraste_fabricado` (marcador de frase) continuam registradas e intocadas.
- **v1.9.21** (2026-08-25) — **O VEREDITO passa a ser escrito por LLM sobre briefing determinístico (§3[V], NOVO).**
  - **(0) O defeito, medido antes de tocar em código.** 19 dos 35 filmes recebiam veredito BYTE-IDÊNTICO ("Os grupos falam das mesmas coisas — discordam sobre se elas funcionam"), 20 caíam no ramo que a produz (o vigésimo, `friday-the-13th-2009`, difere só pelo prefixo de meio dominante), e o catálogo inteiro tinha **14 textos distintos para 35 filmes**. A causa não é o template — é o BRIEFING: a frase relata a AUSÊNCIA de contraste e nunca a PRESENÇA de assunto, enquanto o campo `tema` de cada célula de `eixos` (a única fonte de variedade real, já rotulada por [D3] e já filtrada de spoiler) era descartado. Medição que fecha o conserto barato: nomear só o EIXO dominante de cada lado dá 10 combinações para 20 filmes, com `roteiro_estrutura/roteiro_estrutura` saindo 5 vezes — os 10 eixos são lista fechada e um deles domina o catálogo.
  - **(1) Estágio [V] (§3[V]).** Roda na PUBLICAÇÃO (~35 chamadas por regeneração), não por pageview. Consome `eixos` + `buckets` + `ficha` do JSON já montado, nunca reviews brutas; grava a chave de topo `veredito`. Depende de [D3] ter rodado (o `contraste` vem de lá); independe de [D2] — veredito e narrativa não se leem.
  - **(2) Briefing determinístico (`veredito.py`), e a serialização SEM ALGARISMO.** Todo número e todo rótulo do briefing é calculado em código puro: eixo de maior lift + `acima_da_margem`, eixo de maior frequência + `tema` + `freq_pct` + `rotulo_quantificador`, `share_pct`, `modo`, `estado_piso`, `contraste`, `bucket_dominante`, `assunto_compartilhado`. **A serialização que vai ao modelo emite RÓTULOS, nunca números** — com isso a invariante "zero dígitos na saída" deixa de depender de obediência (o modelo não copia um número que nunca viu) e `lift_pp` não chega ao prompt, então "quase passou" não existe para ele.
  - **(3) `assunto_compartilhado` — o critério, com a medição.** Entre os eixos que os DOIS extremos mencionam, o que maximiza `min(freq_negativas, freq_positivas)`; desempate por soma, depois ordem canônica de `EIXOS`. Piso de **25% nos dois lados**, reusando a fronteira inferior da faixa `muitos` (v1.2.3) em vez de inventar número novo. Medido nos 35: **todos** têm assunto compartilhado; nos 17 `valorativo` o `min` fica entre **40% e 84%**. É o campo que dá substância ao caso `valorativo` — quando nenhum lado tem assunto PRÓPRIO, o veredito nomeia o assunto COMPARTILHADO e diz que a divergência é de julgamento.
  - **(4) Limitação registrada, não contornada.** Em 2 dos 17 `valorativo` (`dune-2021`/`comparacoes`, `the-substance`/`impacto_emocional`) o eixo compartilhado não tem `tema` nomeado em nenhum dos dois lados — o campo só existe quando aquele eixo virou BULLET daquele grupo (§2.5). Briefing carrega o rótulo do eixo sem tema; a substância vem do top-frequência de cada lado. Nada é inventado para tapar o buraco (mesma política de omissão autorizada da v1.4.1).
  - **(5) Best-of-3 REPRODUZIDO, não reusado, e o motivo.** `selecao_narrativa.selecionar()` está acoplado ao formato de três movimentos (`spans_por_grupo` ancora no `rotulo_peso` literal; `cobertura` conta cláusulas por span; `ritmo` exige ≥2 frases). Num texto de 1–2 frases sem rótulo ancorado, os três critérios nunca desempatam nada — seria auditoria de aparência. O padrão de `narrador.narrar()` é reproduzido com critérios próprios; `qualidade.py` é reusado no que se aplica. **Nenhum LLM julga prosa**, como em todo o projeto.
  - **(6) Dez validações em CÓDIGO** (`formato_invalido`, `digito`, `quantificador_mais_forte`, `tema_ausente`, `idioma`, `comprimento`, `escopo_generalizado`, `nota_ou_score`, `contraste_fabricado`, `cliche`), retry direcionado quando nenhum candidato sai limpo, e **fallback obrigatório para o TEMPLATE determinístico da v1.9.19/v1.9.20**, que permanece no código. Nunca fica sem veredito; nunca publica veredito inválido. `veredito.origem` grava `llm` | `template_fallback`; telemetria completa no JSON, **nada na interface** (mesma decisão de `verificacao_narrativa`).
  - **(7) O limiar continua BINÁRIO.** `the-godfather` tem o melhor lift das negativas em 19,6pp contra margem de 20 (eixo `ritmo`, 16 de 25 = 64%, tema "Ritmo lento e tédio") — falha por 0,4pp e o filme é `valorativo`. Registrado como observação e **nada mais**: não autoriza mexer em `MARGEM_LIFT_PP` (parâmetro a montante que alimenta a seleção de bullets inteira, escolhido por nulo de permutação) nem tratar quase-passou como contraste no briefing ou no prompt.
  - **(8) Registro honesto: o veredito deixa de ser 100% determinístico.** Duas execuções sobre o mesmo filme podem produzir textos diferentes (mesma variância entre chamadas medida na v1.7.3). **Não viola "código é autoridade sobre números"** — o modelo não vê algarismo nenhum, não escolhe eixo/tema/grupo/rótulo/estado de contraste, e o único número que sobrevive no texto renderizado (o peso do meio dominante) é prefixado pelo CÓDIGO, fora da saída dele. O que se perde, dito sem maquiagem: reprodutibilidade byte a byte do texto publicado — custo aceito, com a escolha auditável pela telemetria mesmo sem ser reproduzível.
  - **(9) Correção de inflação retórica no FALLBACK (a mesma classe das v1.2.2/v1.2.3, reintroduzida num lugar novo).** O ramo de fallback do template terminava com a frase fixa "— um assunto que todos os grupos citam", disparada sempre que existia qualquer eixo com `mencoes > 0`, sem checar se a frequência sustenta "todos". Casos medidos em produção: `obsession-2026` afirmava isso a partir de **2 de 5 reviews (40%)** num bucket que o próprio site rotula `modo: reduzido`; `eighth-grade`, com amostra completa, a partir de **13 de 34 (38%)**. Corrigido com o MESMO mapa de quantificador do briefing, e `modo: "reduzido"` tratado como caso à parte (cautela explícita, nunca generalização).
  - **(9b) Paridade Python/JS travada por teste.** O veredito determinístico existe DUAS vezes de propósito — `veredito.veredito_template` (a rede do estágio) e `veredito()` em `filme.js` (o fallback de render para JSON anterior à v1.9.21) — e duas implementações da mesma regra em linguagens diferentes é uma divergência esperando acontecer, com sintoma silencioso: um filme antigo e um filme novo em `template_fallback` dizendo coisas diferentes sobre dados equivalentes. `tests/test_veredito_paridade_js.py` roda o JS REAL (o arquivo, via `node`, não um port) sobre os 35 e exige igualdade byte a byte. **Medido: 35/35 idênticos.** Pula quando `node` não existe — é rede a mais, não bloqueio de ambiente.
  - **(6b) Três falsos positivos de `tema_ausente`, medidos na primeira geração dos 35 e corrigidos antes de o A/B valer.** O custo de um falso positivo neste estágio é concreto: elimina candidatos bons e empurra o filme para `template_fallback`, devolvendo ao leitor a frase genérica que a versão veio eliminar. **(a)** O marcador `tom` casava como SUBSTRING dentro de "tomam"/"sintoma"/"átomo" — mesma família do bug da v1.6.2 (`"1%"` dentro de `"91%"`), e mesma correção: marcador passa a casar TOKEN INTEIRO por padrão e por PREFIXO só quando escrito com `*` (`arrastad*`). **(b)** `desenvolvimento` saiu de `roteiro_estrutura` ("arrastado" é ritmo, "dos personagens" é roteiro) — custava `hereditary`. **(c)** `incomod*` saiu de `impacto_emocional` (incômodo descreve qualquer desagrado, inclusive personagem irritante) — custava `pearl-2022`. Os três viraram teste de regressão, e o A/B foi **inteiramente regerado** depois da correção: mudar o validador entre os braços invalidaria a comparação.
  - **(10) Mapa de quantificador unificado (`quantificador.py`, NOVO).** A tabela de faixas da v1.2.3 existia DUAS vezes — `synthesize._rotulo_quantificador` e `briefing._quantificador`, esta última reimportada por valor de propósito, para não depender de um módulo que importa SDKs. Uma terceira cópia em `veredito.py` seria o erro real, então as duas viram uma: módulo novo sem nenhuma dependência, importado pelos três. Comportamento preservado para todo `pct` em 0–100; o `pct` fora de faixa (inalcançável, e com fallbacks que DIVERGIAM entre as duas cópias) passa a ser clampado a [0,100], tornando as duas caudas mortas e o comportamento determinístico. **O portão da extração tem duas metades, e a distinção importa para quem ler depois:** (a) um GATE DE SESSÃO, executado uma vez — montar os briefings de narrativa dos 35 filmes antes e depois da extração e comparar byte a byte: **35/35 idênticos, mesmo SHA-256 do dump agregado (`6083b84c…`)**; (b) um TESTE PERMANENTE (`tests/test_quantificador.py`) que congela as DUAS implementações antigas como oráculo e mede equivalência sobre toda a faixa 0–100 e sobre todo `pct` que os 35 filmes realmente produzem. A comparação byte a byte **não foi esquecida — foi executada e reportada**; ela não virou fixture permanente porque um golden file de 336 KB quebraria por motivo LEGÍTIMO na próxima republicação de qualquer filme, e um teste que falha por motivo certo em contexto errado é um teste que se aprende a ignorar.
  - **(11) Modelo — inventário consultado na API, não de memória.** O tier `pro` disponível na chave é `gemini-3.1-pro-preview` (`3.1-pro-preview-01-2026`) e não existe tier acima; o flash mais recente é `gemini-3.7-flash` (`3.7-flash-08-2026`), sete meses mais novo que o único pro. `gemini-pro-latest` rejeitado por política (alias é alvo móvel, v1.9.10). Tensão registrada: a comparação da v1.9.10 mediu o 3.1-pro PIOR que o 3.7-flash no narrador (2 flags contra 1, ~10× o custo, amostra de 3 filmes). Resolvida por MEDIÇÃO — o A/B roda o critério de aceite inteiro nos dois braços, com tudo idêntico menos o modelo. Conformidade não decide sozinha: um modelo pode passar limpo em todas as validações e ainda produzir 35 vereditos corretos, insossos e intercambiáveis — a falha exata que esta versão existe para evitar.
  - **(11b) Footgun de republicação em massa, FECHADO na mesma versão.** Subir `SPEC_VERSION` faz `publicar_catalogo.py` deixar de pular os 32 slugs default — um comando de uma linha passaria a disparar re-scrape de 32 filmes a 2s por requisição, apagando de quebra o histórico `passadas` do `meta.json` (dívida conhecida, `DIAGNOSTICO_OFFLINE.md`). `cmd_publicar` passa a RECUSAR acima de `LIMITE_LOTE_SEM_CONFIRMACAO = 5` filmes efetivamente republicáveis, exigindo `--republicar-tudo`, com mensagem dizendo quantos e por quê. A guarda conta quem SERIA republicado, não o tamanho da lista. Escopo estritamente este: o checkpoint não muda e a dívida do `passadas` continua aberta.
  - **(11c) Critério de seleção entre candidatos limpos: informatividade ancorada, NÃO brevidade.** A proposta inicial ("o mais curto") foi reprovada dentro da própria sessão, com razão: os 19 vereditos idênticos não eram longos, eram VAZIOS — otimizar para brevidade otimiza na direção do defeito. Chave primária: número de âncoras substantivas distintas do briefing que o texto nomeia, com **teto de 2** (sem teto, premiaria empilhar tema atrás de tema); secundária: menos palavras. Casamento por palavras de conteúdo com prefixo de 5 caracteres, nunca por substring do `tema` — e a cópia literal do tema é REPROVADA por validação (`tema_verbatim`), não premiada. Verificado nos 35 antes de implementar: nenhum filme fica com menos de 2 âncoras disponíveis, inclusive `dune-2021` e `the-substance`.
  - **(11d) RESULTADO MEDIDO do A/B, e a decisão de modelo.** Mesma régua nos dois braços, com briefing, prompt, best-of-3, validadores e ordem de filmes idênticos. **Antes: 19 vereditos byte-idênticos, 20 filmes no ramo sem contraste, 14 textos distintos em 35, Jaccard médio 0,3744. Depois (os dois braços): 35 textos distintos, ZERO byte-idênticos.** Jaccard médio 0,0583 (flash) e 0,0526 (pro) — queda de ~6-7x. Conformidade: flash **35/35 por LLM, zero flags, zero retries**; pro 34/35, com `cure` caindo em `template_fallback` (escreveu "a ambientação criada pela direção", e `direcao_imagem` não está no briefing daquele filme) — regressão de produto concreta, porque aquele filme volta a exibir a frase genérica. Latência total 454s (flash) contra 1564s (pro). **Decisão do dono do projeto, lendo os 35 textos de cada braço: `gemini-3.7-flash`.** Registro honesto do que o pro ganha: varia um pouco mais a construção sintática (o flash recai com mais frequência em "A divergência está em..."), e é a ÚNICA dimensão em que ele vence. **O achado que importa mais que a escolha: a diferença entre os dois MODELOS é muito menor que a diferença que o BRIEFING fez** — os dois saíram de 14 para 35 textos distintos. O trabalho estava no briefing, e por isso a linha de modelo é reversível sem consequência estrutural.
  - **(11e) Publicação dos 35 (Entrega 5), com o diff auditado campo a campo.** `scripts/gerar_veredito.py --todos`: **35/35 por LLM, zero `template_fallback`**. Conferido programaticamente nos 35 documentos, contra `HEAD`: **nenhum campo fora de `veredito` mudou**, a ordem das chaves de topo foi preservada e `veredito` entrou como última chave em todos. `spec_version` de topo de cada filme continua no valor original — o bloco carrega a própria versão. Verificado em navegador (servidor local): os 6 filmes do aceite renderizam o texto do JSON, na posição certa (depois da ficha, antes dos bullets), com zero contagem bruta de review no texto; `napoleon-2023` e `friday-the-13th-2009` trazem o prefixo de meio dominante vindo do código; `obsession-2026` sai com cautela de amostra pequena; `teste-degradado` exercita o FALLBACK DE RENDER como planejado; home com 35 cards; **zero erro de console em toda a bateria**.
  - **(12) Dívida de registro paga: v1.9.17 a v1.9.20 entram no changelog** (abaixo). Quatro versões de frontend rodaram carimbadas no código e ausentes da spec — a mesma deriva silenciosa que `test_spec_version.py` (v1.9.14) existe para impedir, agora fechada nos dois sentidos: a constante e o título sobem juntos para `1.9.21`.

- **v1.9.20** (2026-08-24, `8d457a3`) — **REGISTRO RETROATIVO (frontend, escrito na v1.9.21).** *Não teve entrada de changelog na época; o carimbo vivia só nos comentários de `frontend/js/filme.js`.*
  - **(1) O veredito deixa de mentir por omissão.** Defeito real em `anatomy-of-a-fall` (88% positivas): quando um bucket não tinha eixo acima da margem, a frase "nenhum assunto se destaca" comunicava "esse grupo não falou de nada", enquanto o dado dizia "esse grupo falou do que todo mundo cita" — contraste BAIXO com frequência ALTA são coisas diferentes. O lado sem lift passa a cair no eixo de maior FREQUÊNCIA (`eixoDeMaiorFrequencia`, nova), com redação que distingue os dois casos ("destaca X" contra "fala sobretudo de Y — um assunto que todos os grupos citam"). Ainda zero LLM, ainda sem inventar contraste que o dado não sustenta. *(A segunda metade dessa frase é o defeito corrigido na v1.9.21, item 9 — o quantificador "todos" não era conferido contra a frequência.)*
  - **(2) Nenhum algarismo de contagem de review no TEXTO** (decisão do dono do projeto). Saem: "~X de N" ao lado de cada bullet, "N de M analisadas" no header do grupo, "(40 · 40 · 40 reviews)" no disclaimer, "N reviews observadas" no header do filme. **Ficam:** a BARRA de proporção (inclusive o `aria-label` — não é texto visível, é a alternativa da barra para leitor de tela), o PERCENTUAL de peso ("~79% das notas"), a janela temporal, e todos os números do JSON (pipeline intocado).
  - **(3) Avisos de piso reduzido reescritos sem algarismo** — "Modo reduzido: amostra pequena para este grupo" (era "apenas N de M reviews-alvo"); "Sem análise temática: amostra insuficiente neste grupo" (era "apenas N review(s)... o piso é 3").
  - **(4) Varredura automatizada nos 35** (iframe + regex `\d+\s+de\s+\d+` / `\d+\s+reviews?`): zero ocorrência real. Dois falsos positivos investigados e descartados — "Sexta-Feira 13" (o número está no TÍTULO, concatenado ao rótulo estático no `innerText` plano) e um artefato de cache de iframe em `obsession-2026`.

- **v1.9.19** (2026-08-24, `38fb204`) — **REGISTRO RETROATIVO (frontend, escrito na v1.9.21).**
  - **(1) `filme.html` reordenada — dados primeiro.** Feedback de usuários reais: a parede de texto narrativo aparecia ANTES dos bullets e ninguém lia; havia redundância entre o resumo no topo e a observação por grupo no fim. Ordem nova: header → ficha → **VEREDITO** → bullets por sentimento → narrativa completa **COLAPSADA** → pesquisa.
  - **(2) O VEREDITO nasce, como TEMPLATE sobre o lift já computado, zero LLM** (`veredito()`/`eixoDeMaiorLift()`/`bucketDominante()`). Casos tratados: nenhum bucket acima da margem, só um lado qualifica, piso `sem_analise` (bucket não empresta eixo), meio dominante (prefixo dedicado). Testado nos 35: 0 falhas, 0 sem veredito, 0 com texto de nota/score. *(É este template que a v1.9.21 substitui como gerador e preserva como fallback.)*
  - **(3) A tabela "eixo a eixo" SAI DA TELA** (decisão de produto — "não funciona na prática"), removida do CSS e do JS, não escondida atrás de flag. O bloco `eixos` do JSON não muda em nada: continua calculado pelo mesmo `eixos.py`, e passa a alimentar duas coisas que a view antiga não fazia — o veredito, e a ORDEM dos temas dentro de cada grupo (`ordenarTemasPorEixo`: tema com papel de contraste sobe ao topo).
  - **(4) O meio rebaixado, com EXCEÇÃO AUTOMÁTICA.** Dois blocos em destaque (negativas/positivas, mesmo formato entre os dois); `medianas` vira `<details>` colapsado — **exceto** quando é o grupo DOMINANTE, e aí os três sobem ao destaque: `napoleon-2023` (45%) e `friday-the-13th-2009` (41%), verificados. Quebra deliberada da neutralidade de tratamento do §0, com a simetria explícita: lá o problema era filme aclamado parecendo dividido; aqui seria filme tripolar parecendo bipolar sem a exceção. O dado (coleta, classificação, lift, JSON) não muda. **Registrado em §0 na época; só o changelog faltava.**
  - **(5) Acabamento:** "+" vira chevron dentro de pill na cor do grupo; hierarquia tipográfica dos bullets; tint de fundo por sentimento atrás de flag `?tint=1`, nunca ligado por padrão.

- **v1.9.18** (2026-08-23, `b1dccea`) — **REGISTRO RETROATIVO (frontend, escrito na v1.9.21).** A célula do mosaico refeita. A v1.9.17 preenchia a célula INTEIRA com a distribuição em cor saturada; com ~30 dos 35 filmes majoritariamente positivos, a home virava dezenas de retângulos quase idênticos, e o título só aparecia num hover que escurecia a tela toda. A célula vira um card escuro com título SEMPRE visível (revoga a v1.9.17) e a distribuição reduzida a uma faixa de 5px na base; paleta PARALELA só para essa faixa (`--neg-home`/`--med-home`/`--pos-home`), com as originais intactas (divergência deliberada, comentada em `:root`); hover sutil (scale 1.06, nada escurece); `aspect-ratio` 4/5 para o título mais longo do catálogo caber em 3 linhas. Trade-off aceito e reportado: com a célula maior, o mosaico não cabe mais inteiro em 1440×900 sem scroll (~270px) — legibilidade vinha antes no pedido.

- **v1.9.17** (2026-08-23, `f66eb5e`) — **REGISTRO RETROATIVO (frontend, escrito na v1.9.21).** A home vira mosaico. A lista vertical de 35 cards vira uma grade de quadrados cujo repouso mostra **só a distribuição real** do filme (`distribuicao.por_bucket`, as cores já existentes) — **nenhuma nota, score ou estrela**, a restrição de produto não-negociável do §1. Responsivo por LARGURA, não por N (7 colunas em desktop, 5 em tablet, 3 em mobile): um catálogo de 20 vira menos LINHAS, um de 60 vira mais. A busca continua sobre o mesmo `dataset.busca` e REORGANIZA a grade em vez de esmaecer células vazias. Bug real achado ao testar: `.mosaic-cell { display: block }` e o `[hidden]` do UA stylesheet têm a MESMA especificidade — sem regra explícita, células "escondidas" pela busca ficavam invisíveis ao teste por atributo e continuavam ocupando espaço na tela.
- **v1.9.16** (2026-08-22/23) — **Verificador de `impacto_emocional` adotado em produção e os 35 filmes do catálogo publicados.**
  - **(1) Verificador integrado ao pipeline (Entrega 1).** Decisão do dono do projeto: adotar `V2_alvo`, passada única, sem votação (88,9% de reprodutibilidade medida na fase de classificação justifica). Roda como estágio à parte após o consenso de votação: `scripts/verificador_impacto.py aplicar-producao` gera `resultado/votacao-3/consenso_verificado.jsonl` + manifesto (telemetria declarada — veredito, frase, alvo por review). `pipeline._carregar_consenso_producao` passa a PREFERIR o verificado quando existe, com guarda de atualidade (erro explícito, não fallback silencioso, se `consenso.jsonl` cresceu depois da verificação) e declara a aplicação no bloco publicado (`eixos.verificador`). Racional registrado: é precisão comprada com recall — falso positivo quebra "o código soma, ninguém inventa"; falso negativo é perda silenciosa e conservadora. Para este produto, precisão vale mais.
  - **(2) Aplicado ao corpus inteiro (Entrega 2, medido).** 3162 das 4181 reviews classificadas (75,6%): **1654 removidas (52,3%)**, quase idêntico ao 52,8% medido na amostra de 100 do gabarito — sinal de que ela generalizou. `impacto_emocional`: 75,6% → 36,1% (projeção anterior: 35,7%). Custo real US$ 0,1558. Cobertura de contraste: **18/35 → 18/35, total inalterado** (dentro do IC95 [16,19] projetado) — mas dois vereditos mudam em sentidos opostos e se cancelam: `eighth-grade` (valorativo→tematico) e `napoleon-2023` (tematico→valorativo). Os 3 publicados (`cure`, `cidade-de-deus`, `the-invite-2026`) têm veredito estável.
  - **(3) Republicados os 3 filmes já no ar (Entrega 3)** sob a classificação verificada — bullets mudam (frequências menores em `impacto_emocional` reordenam consenso e contraste), veredito não muda, narrativa não regerada (gate de leitura da v1.9.13 continua valendo). Achado ao publicar: o manifesto guardava `n_removidas` — a contagem GLOBAL do corpus — sob um nome que um leitor de `cure.json` leria como "removido só de `cure`"; renomeado para `n_removidas_no_corpus`.
  - **(4) Bug real achado ao rodar o pipeline fresco pela primeira vez desde a v1.9.14:** `pipeline.ids_analisados` lia `r.id` de um `models.Review` recém-sintetizado — que não tem esse atributo (é `viewing_id`; só `bruto.ReviewBruta`, lido do disco, tem `.id`). Nunca exercitado em produção porque os 3 filmes publicados sempre passaram pelo caminho de ENRIQUECIMENTO (`ids_analisados_do_bruto`, sobre `ReviewBruta`), nunca pelo pipeline fresco do CLI (`espectro24 --slug X`) — o único caminho que chama a função quebrada. Corrigido antes de publicar qualquer filme novo.
  - **(5) Os 32 filmes restantes publicados (Entrega 4)** — síntese + narrativa (best-of-3) + eixos, sob o pipeline corrente e a classificação verificada. `scripts/publicar_catalogo.py`: cada filme roda como subprocesso isolado (falha de um não derruba o lote), checkpoint é o próprio filesystem (`spec_version` + `eixos.verificador.aplicado`). **31 publicados, 1 pulado (já em dia), ZERO falhas**, ~41 minutos, ~US$ 0,45 de narração (122 chamadas gemini-3.7-flash) + síntese/D3 (DeepSeek, marginal). Catálogo final: **18 filmes `tematico` / 17 `valorativo`** de 35 — o mesmo número medido na Entrega 2, agora publicado.
    - `obsession-2026` (69 reviews observadas, o único filme obscuro do catálogo) exercitou o piso escalonado reduzido pela primeira vez em produção: `sem_numero` em negativas/medianas, `sem_quantificador` em positivas — não chegou a `sem_analise`, mas os dois estados reduzidos renderizam no frontend com o aviso "modo reduzido" e sem número inventado ("amostra pequena demais para número").
    - Filmes de distribuição invertida (`cats-2019`, 86% negativas; `joker-folie-a-deux`, 46% negativas) abrem "a recepção em resumo" pelo grupo dominante corretamente — confirmado lendo o texto publicado, não presumido.
    - **Achado, não corrigido nesta sessão:** 15 de 35 filmes (43%) carregam alguma flag mecânica de FORMA em `verificacao_narrativa` (colisão de movimento 1/2 no mesmo parágrafo, ou grupo sem parágrafo próprio) — a mesma ressalva que a decisão do `gemini-3.7-flash` (v1.9.10, `config.py`) já tinha previsto ("o primeiro sintoma a observar se o texto parecer raso quando o catálogo crescer"), agora medida numa taxa (43%) bem acima da amostra de 3 filmes que decidiu o modelo (1/3). Zero flag de CONTEÚDO — o fallback `menor_severidade` do best-of-3 absorveu todos os casos. Não muda a decisão de modelo; abre item para a próxima sessão que tocar o narrador.
  - **(6) Frontend regenerado para os 35 (Entrega 5).** `build_data.py`: `CATALOGO` deixa de ser uma lista de 3 slugs redigitada e passa a derivar de `votacao-3/consenso.jsonl` (mesma fonte única de `publicar_catalogo.py`), com `the-invite-2026` mantido em destaque por curadoria. Achado ao verificar a home com 35 cards: a legenda "3 análises prontas · ... · catálogo em expansão" era um literal HTML — corrigido para derivar de `DATA.catalogo.length` em `home.js` (mesmo princípio da v1.9.1, "o literal 50·20·30 passa a derivar do próprio JSON"). Verificado em navegador (servidor HTTP local): home com 35 cards, busca por eixo filtrando de verdade (13 filmes para "ritmo"), `obsession-2026` sem parecer quebrado, filme `valorativo` (`avengers-endgame`) com o enunciado "os três grupos concordam... e discordam no veredito" — zero erro de console em todos.
- **v1.9.15** (2026-08-16) — **Corrige as duas populações de 40 e a fronteira da margem** — dois defeitos medidos na v1.9.14 que afetavam números já publicados, fechados na mesma sessão em que foram achados.
  - **(1) Unificação da amostra classificada com a analisada (Entrega 1, §[D3]).** `amostra.json` era montada sem `orcamento_paginas_por_nivel` (a estratificação por profundidade da v1.9.5) — a classificação e a síntese liam 40 reviews DIFERENTES do mesmo bucket, com sobreposição mediana de 75% no catálogo e mínima de 30%. Estendida a classificação para cobrir a seleção de PRODUÇÃO inteira dos 3 filmes publicados: 191 reviews, 573 chamadas (votação de 3, mesmo `taxonomia_id`), `scripts/estender_classificacao_producao.py`. **Sobreposição depois: 100% em todo bucket dos 3 filmes**, verificado, não presumido. `fonte_classificacao` some do JSON para eles — a chave só existe quando há uma divergência real a declarar.
  - **(2) O bug real achado ao verificar o "antes/depois": o denominador quase infla.** `consenso.jsonl` ACUMULA — a classificação antiga (órfã, fora da seleção nova) continua lá depois da extensão, e `n` saltava de 40 para 53-67 sem filtro. Corrigido filtrando a classificação pela amostra analisada ANTES de contar (`eixos._filtrar_pela_analisada`), com teste que reproduz o cenário exato de `cure`. `n=40` continua `n=40` nos 3 filmes, com as 40 certas.
  - **(3) Nenhum veredito de contraste mudou** — `cure` e `the-invite-2026` seguem `tematico`, `cidade-de-deus` segue `valorativo`. Mudanças de lift por eixo, sim: `cure`/negativas `ritmo` caiu de 20,0pp para 5,0pp; `the-invite-2026`/positivas `direcao_imagem` caiu de 22,5pp para 17,5pp e SAIU da margem de 20pp — não muda o estado do filme (outro eixo mantém `tematico`), mas muda qual bullet aparece na tela. A narrativa dos 3 filmes NÃO foi regerada — não era necessária, já que nenhum contraste mudou, e o gate de leitura da v1.9.13 continua valendo.
  - **(4) Margem: `>=` exata, não `>` estrita (Entrega 2, §2.5).** A v1.9.14 corrigiu o cálculo para `Fraction` mas manteve a comparação ESTRITA — o que reproduzia por acidente o MESMO bug de ponto flutuante da medição de referência (`0,2 >= 0,2` avaliando falso em binário), só que agora "por escolha". Corrigido para `>=` exato: **contraste temático passa de 13 para 18 de 35 filmes**. `cidade-de-deus` — o caso de referência do estado `valorativo` na Entrega 5 da v1.9.14 — CONTINUA `valorativo` sob a nova comparação; não precisou de outro filme de referência.
  - **(5) Tabela de trade-off da margem recalculada DEPOIS da unificação** (`scripts/recalcular_margem_exata.py`, mesma metodologia — 2000 rodadas de permutação, mesma semente — só a aritmética muda de `float` para `Fraction`): 15pp → 44 pares/61%/24 filmes; **20pp → 27 pares/34%/18 filmes**; 25pp → 13 pares/27%/10 filmes. A ordem de execução importa: rodar a tabela ANTES da unificação (como a primeira tentativa desta sessão fez) produz números que ficam desatualizados assim que a classificação muda — a tabela foi recalculada depois, para casar com o repositório.
  - **(6) Reprodutibilidade de [D3] medida, não implementada votação (Entrega 4).** O caso apontado na conferência da v1.9.14 (`cidade-de-deus`: "Excesso de violência e ritmo exaustivo" → `ritmo`, "Excesso de violência" → `tom_atmosfera`, mesmo núcleo) foi investigado rodando [D3] duas vezes sobre os mesmos 54 temas dos 3 filmes: **98,1% de reprodutibilidade — 1 de 54 divergiu**, e é a mesma tema do caso apontado (oscila entre `livre` e `tom_atmosfera`, fronteira real, não ruído). Muito acima dos 26,5% da classificação por review antes da votação de 3. **Decisão: não implementar votação** — custo recorrente por filme sem justificativa na taxa medida.
  - **(7) Estado do produto depois das correções (Entrega 5):** 3 filmes publicados, populações unificadas, margem `>=` exata. Limitações que continuam declaradas, não resolvidas: `impacto_emocional` (precisão 0,486 contra gabarito, ocupa vaga de consenso em 9 de 9 buckets dos 3 filmes); [D3] não calibrado contra gabarito humano (98,1% reprodutível, mas isso mede consistência, não acerto); janela temporal da amostra é proxy declarado, não medida direta de recência de opinião.
- **v1.9.14** (2026-08-16) — **REPUBLICAÇÃO dos 3 filmes do catálogo** (Entrega 1). Primeiro evento de publicação desde a v1.6.0: `resultado/{cure,cidade-de-deus,the-invite-2026}.json` sobrescritos pelos artefatos gerados na v1.9.13 (`resultado/v1913/`), que passaram no gate de leitura humana do dono do projeto (`resultado/v1913/NARRATIVAS_GATE_LEITURA.md`). `frontend/js/data.js` e `frontend/data/*.json` regerados por `frontend/build_data.py`; as três páginas de filme + a home + o filme sintético degradado renderizam com **zero erro de console** (verificado em navegador, não presumido). **Decisão de escopo registrada:** publicados **3**, não os 35 do bruto — o schema de eixos da mesma sessão muda o JSON, e publicar 35 agora seria republicar 35 depois.
  - **(1) O que muda VISIVELMENTE para quem já tinha visto o site.** Quatro mudanças, nenhuma cosmética: **(a) os shares** sob as fronteiras C (§2.2) — `cure` 3/17/79 → **2/8/90**, `cidade-de-deus` 1/8/91 → **1/3/96**, `the-invite-2026` 3/18/79 → **2/7/91**; o grupo do meio encolhe nos três, e o dado não mudou, a régua mudou; **(b) a cota de análise** de 50/20/30 para **40/40/40** por bucket — o grupo mediano era lido com 40% da profundidade do negativo e passa a ter a mesma, com efeito visível de temas menos genéricos no meio; **(c) a narrativa é outra** — briefing determinístico + best-of-3, sem editor [E2], sem tique de quantificador (o texto publicado repetia "muitos" até 8 vezes), um parágrafo por movimento e por grupo, movimento 2 sem a truncagem que o esvaziava; **(d) `spec_version`** sai de `1.6.0`.
  - **(2) `spec_version` publicado é `1.9.11`, não `1.9.13` — registro honesto, não corrigido à mão.** Os artefatos foram gerados quando a constante `SPEC_VERSION` (config.py) ainda estava em `1.9.11`, enquanto o documento já estava em v1.9.13. É a **segunda ocorrência** da mesma deriva (a v1.9.11 achou a constante parada em `1.9.0` desde a v1.9.1). Reescrever o carimbo depois do fato foi recusado pelo mesmo motivo já registrado para `VERSAO_COLETOR`: um carimbo corrigido a posteriori não é evidência de nada. A correção é de MECANISMO e entra nesta versão — ver item (3).
  - **(3) Lição vira mecanismo: a deriva de `SPEC_VERSION` passa a falhar o CI.** `tests/test_spec_version.py` compara a constante com a versão declarada no título de `SPEC.md`. Duas ocorrências silenciosas em treze versões era evidência suficiente de que a disciplina escrita não sustenta o invariante.
  - **(4) SCHEMA DE EIXOS — o Ponto 2 do projeto, fechado (§2.5, Entregas 2-4).** O JSON de resultado ganha o bloco global `eixos`: por eixo da taxonomia fechada de 10 (`taxonomia_id` `ebab2667de74`), a frequência em cada um dos três buckets com denominador, o `lift` (`freq_bucket − max(freq_outros)`), o papel de bullet por grupo e o estado `contraste`. Tudo em `Fraction` sobre contagens inteiras — **nenhum número passa por LLM**, e a comparação com a margem não passa por ponto flutuante. Módulos: `taxonomia.py` (a taxonomia sobe de `scripts/` para `src/`, bytes idênticos, `taxonomia_id` inalterado e travado por teste), `eixos.py` (contagem, lift, margem, contraste, bullets) e `pipeline.montar_eixos` (orquestração ADITIVA, no estatuto de ficha e distribuição: sem classificação, com taxonomia divergente ou com [D3] falhando, a chave simplesmente não é emitida).
  - **(5) A comparação com a margem é ESTRITA, e 5 filmes dependem disso (§2.5).** Achado ao implementar: `barbie`, `bones-and-all`, `hereditary`, `im-still-here-2024` e `spider-man-across-the-spider-verse` têm o melhor lift em **exatamente 20,0pp**. A medição de referência comparou com `>=` em ponto flutuante e os cinco caíram fora — é daí que vem o número decidido de 13/35 filmes com contraste temático. Sob `>=` com aritmética exata seriam **18/35**. Decisão registrada: `lift > margem`, por reproduzir o número decidido e por ser o que a frase da decisão diz ("acima da margem"). Sem ponto flutuante em lugar nenhum da decisão.
  - **(6) [D3] — rotulagem de tema por eixo (§D3, NOVA etapa).** Uma chamada por bucket em DeepSeek: recebe a lista fechada de eixos com as definições vindas de `taxonomia.definicoes()` (extraídas do próprio SYSTEM, nunca redigitadas) e os ≤6 temas do grupo; devolve um eixo por tema. **Não vê número nenhum.** O código valida contra a lista fechada e **o que não estiver nela vira `livre`**; tema que o modelo inventa é descartado, tema que ele esquece vira `livre`. **Assimetria de validação declarada como ressalva de primeira classe:** a classificação por review tem auditoria de 100 reviews, votação de 3 e precisão/recall por eixo; [D3] não tem nada disso. Mitigação adotada: as 46 células dos 3 filmes vão para conferência à mão do dono do projeto (`resultado/v1914/ROTULAGEM_CONFERENCIA.md`).
  - **(7) DUAS POPULAÇÕES DE 40 — o achado mais importante da versão (§D3).** `resultado/votacao-3/amostra.json` se declara "a população que a síntese veria" e **não é**: foi montada com `selecionar(todas, hist)`, sem o `orcamento_paginas_por_nivel` que liga a estratificação por profundidade da v1.9.5. Medido nos 105 buckets do catálogo: sobreposição **mediana de 75%, mínima de 30%** — e os 3 filmes publicados estão entre os piores casos (`cidade-de-deus`/negativas: **13 de 40**), por serem os de bruto mais profundo. Consequência: "40 de 40 analisadas" no cabeçalho e "24 de 40" na linha do eixo são **dois quarentas diferentes**. Não escondido: `fonte_classificacao` grava os três números por bucket, a interface rotula o denominador como *reviews classificadas* e a spec registra a correção estrutural recomendada (estender a classificação às reviews que faltam, ~191 nos 3 filmes, mesmo `taxonomia_id`) como **não aplicada**.
  - **(8) Seleção de bullets, e a correção que o dado real forçou (§2.5).** 2 bullets de maior frequência + 3 de maior lift acima da margem. A primeira implementação descontava do contraste os eixos já escolhidos por frequência — e em `cure`/positivas isso escondia `tom_atmosfera`, **o maior contraste do filme (40pp)**, atrás do rótulo de consenso. Os dois critérios passam a ser independentes e o eixo entra uma vez, com papel `frequencia_e_contraste`. Segunda correção da mesma natureza: tema que colide com outro no mesmo eixo sumia da tela (em `cure`/negativas, 6 temas ocupam 3 células) — os excedentes viajam em `temas_no_mesmo_eixo`.
  - **(9) `contraste` chega ao MOVIMENTO 3 (Entrega 4).** O briefing ganha o estado, o `taxonomia_id` que o decidiu e os eixos de contraste por grupo; em `valorativo` o narrador recebe a ordem de dizer que os grupos concordam sobre o que o filme é e discordam sobre se funciona, **mais a proibição de fabricar diferença de assunto**. Regra 7b no prompt. **As narrativas publicadas NÃO foram regeradas** — por decisão do dono do projeto: esta versão já publica schema, lift, contraste e frontend novo sem gate visual, e somar texto novo impediria isolar a causa de qualquer estranheza. A capacidade está no código e com teste; a próxima geração já sai com a frase.
  - **(10) FRONTEND — as três colunas alinhadas (§[E], Entrega 5).** Primeira vez que o frontend é tocado nesta fase. Seção "Eixo a eixo" com uma linha por eixo e três células comparáveis, e os quatro estados tratados: célula vazia, `contraste: valorativo` com enunciado próprio (`cidade-de-deus` como caso de referência — 0 selos, e a área não parece quebrada), piso escalonado célula a célula, e filme sem bloco de eixos caindo na lista anterior. Empilha no mobile com o rótulo do grupo em cada célula. **A busca deixa de ser decorativa:** filtra por título e pelos eixos EM DESTAQUE — casar com os 10 devolveria o catálogo inteiro para qualquer eixo, que é o mesmo defeito com outra roupa. Registro: a pendência da cota hardcoded **já estava resolvida desde a v1.9.1**; conferida, nada a fazer. 27 cenários em `frontend/TESTE_MANUAL.md`, um deles achando uma regressão real (`var` içado sem atribuição).
  - **(11) JANELA TEMPORAL declarada (Entrega 6).** Novo campo por bucket `janela_amostra` — a janela das reviews **ANALISADAS**, não a do bruto. A armadilha evitada: `coleta.janela_temporal` já existia, mas cobre 678 reviews em `cure` contra as 40 analisadas; exibi-la ao lado de "40 de 40 analisadas" trocaria uma confusão de populações por outra. Calculada pela MESMA função pura (`bruto.janela_temporal`), sobre outra população declarada. Na interface, linha própria abaixo do denominador da amostra e **nunca** ao lado do rótulo de peso (o peso vem do histograma de NOTAS, que acumula desde 2012). Sai dos quantis `p5`-`p95`: em `cure`/negativas o `min` é de 2024 contra uma `p5` de maio de 2026, e há review datada de **1442** no catálogo — a média seria mais lisonjeira e menos verdadeira.
  - **(12) Fora de escopo, não tocados:** seleção S2 (70/30), reclassificação do corpus, taxonomia, prompt de classificação, margem, qualquer parâmetro de coleta, a correção estrutural do `meta.json` (`DIAGNOSTICO_OFFLINE.md`) e a publicação dos 35 filmes do bruto.
- **v1.9.6** (2026-08-09) — **retentativa de transporte no `Fetcher`** (§2.4) + **`dias_por_100_paginas` como métrica persistida** (§3[B']) + **passada seletiva sob `by/added-earliest`** (§2.3). Fora de escopo e **não tocados**: fronteiras, cota, `min_chars`, cascata, orçamento base, teto de extensão, `RESERVA_PROFUNDIDADE`, `FRACOES_PROFUNDIDADE`, schema de eixos, lift, estado `contraste`, `taxonomia_id`, narrador, editor. Nenhuma mudança de SELEÇÃO aplicada; nenhum `resultado/*.json` republicado.
  - **(1) Retentativa que distingue transporte de bloqueio (§2.4).** `Fetcher.get` retenta até 3× com backoff `2s·4s·8s` ± jitter de 25% **apenas** erro de transporte (reset, timeout, falha de socket) — o delay de educação (§2.1) continua valendo entre tentativas e a retentativa SOMA a ele. **403/`AntiBotError` e o SEGUNDO 503 do lote não retentam e param na hora**; o primeiro 503 do lote ganha uma única retentativa com espera longa (30s); 404 e demais status ≠ 200 falham sem retentar. O contador de 503 é do LOTE (`PressaoDoSite` compartilhado entre os `Fetcher` que o harness cria por filme), senão "segundo 503 do lote" seria inexprimível. `SobrecargaError` **não** herda de `FetchError` de propósito: as etapas aditivas (§3[F], §3[G]) engolem `FetchError` e engoliriam uma parada de lote. Motivação medida na v1.9.5: **10 falhas de rede em 28 filmes (36%)**, todas transitórias.
  - **(2) `dias_por_100_paginas` promovida a métrica de primeira classe (§3[B']).** Calculada na coleta e gravada em `meta.json` por filme e por nível. É o discriminador entre as duas populações que a v1.9.5 mediu (`friday-the-13th-2009` 163,6 dias/100 páginas contra 0,8 de `avengers-endgame`) e o que decide quem precisa de passada. Usa `data` (proxy contaminado, §3[B']) com ressalva registrada: mede a **TAXA ao longo das páginas**, não a data absoluta, e a contaminação é ruído aproximadamente uniforme sobre as posições. Bordas nomeadas e testadas (menos de 2 páginas → `None`; todas as datas iguais → `dias=0` e `paginas_para_1_ano=None`).
  - **(3) Passada SELETIVA sob `by/added-earliest` (§2.3).** Só filmes com `dias_por_100_paginas < 20` — os demais já são bem servidos pela profundidade sob `by/added`, e gastar requisição neles duplicaria cobertura existente. Orçamento de 6 páginas por bucket (~18/filme), **sem extensão por déficit e sem sondagem de profundidade** (a sondagem ancora o bloco profundo, que sob ordenação CRESCENTE aponta para o material mais recente — duplicata). Soma ao bruto por incrementalidade (§3[B']); a chave de cache já inclui a ordenação desde a v1.9.0.
  - **(4) Duas ordenações no mesmo bruto obrigam duas correções (§3[B']).** `reviews.jsonl` ganha **`ordenacao_origem`** (default `None` = "coletada antes do campo existir", resolvida no consumo por `meta["ordenacao_usada"]`, **sem reescrever dado histórico com inferência**) — sem ele, `pagina_origem=1` significaria "mais recente" e "mais antiga" no mesmo arquivo. E `meta.json` deixa de ser "a última execução": o corpo continua descrevendo a coleta BASE e cada passada entra na lista **`passadas`**, porque sobrescrever `orcamento_paginas_por_nivel` com o orçamento de uma passada de 6 páginas mudaria a fronteira raso/profundo que a seleção (§3[C2]) lê para estratificar.
  - **(5) Passada EXECUTADA — 12 filmes, 0 falhas, 610 requisições, 0,62 h.** 18 páginas por filme (orçamento gasto integralmente, `material_esgotado` em nenhum nível), +216 reviews por filme (2592 no total), 1 retentativa de transporte absorvida (`barbie` — sob a v1.9.5 esse filme teria abortado), 0 × HTTP 503. **Ganho medido:** nos 12 filmes, a janela `p5-p95` do bruto vai de **47 para 1487 dias** de mediana (`cidade-de-deus` alcança 2012-08-30, praticamente toda a vida do filme no site); **no catálogo inteiro de 35**, de **116 para 582 dias**, com os filmes que cobrem ≥ 1 ano passando de **11 para 20**. Os 2 buckets sub-40 dos filmes selecionados fecham (**34/36 → 36/36**). `min`/`max` foram declarados inutilizáveis com evidência: `barbie` tem review datada de **1442**, e data assistida é campo livre (§3[B']).
  - **(5b) PERFIL DO MATERIAL ANTIGO — o achado que decide a seleção.** Ele é sistematicamente **mais longo**: 361 vs 151 chars de média (2,4×), **55,2% vs 76,5%** abaixo de `min_chars`, 16,4% vs 6,0% de truncamento na listagem, 4,9% vs 2,6% de spoiler. **Não é artefato de medição** — as duas pontas passaram pela MESMA política de completamento e terminam com 99% de texto resolvido (foi por isso que a passada usou o `alvo_por_nivel` da coleta base em vez de um proporcionalmente menor). **O que NÃO se pode concluir:** que reviews antigas sejam mais longas — `by/added-earliest` amostra uma COORTE (quem escreveu primeiro), e coorte e época estão confundidas por construção neste endpoint. Distribuição de nível: dentro de ±3 pp em oito dos dez níveis.
  - **(6) Proposta de seleção temporal MEDIDA, não aplicada (§3[C2]).** S1 (atual) / S2 (70-30) / S3 (proporcional ao volume). **Os três fecham 36/36 buckets** com `p5` idêntico e comprimento dentro de 5% — cobertura não decide. Decide a variação: sob **S1** a mistura vai de **1 a 19 antigas por bucket** (desvio 4,6) e varia DENTRO do mesmo filme (`the-substance`: 47,5% antigo em `medianas`, 5% em `positivas`); S2 fixa 12; S3 fica em 7-11. **Recomendado: S2**, com `70/30` como parâmetro arbitrário declarado. S3 perde porque a proporção que ele segue não é propriedade do filme e sim do orçamento da passada — dobrá-lo mudaria a análise sem decisão. A aplicação fica para a sessão do schema, para não invalidar a classificação de eixos em paralelo.
  - **(7) Correção de registro:** a v1.9.5 declarou-se "a última sessão da camada de COLETA". A própria medição dela identificou a ORDENAÇÃO como parâmetro de coleta ainda não decidido, e esta versão o decide. A declaração original fica no cabeçalho, com a correção ao lado.
- **v1.9.5** (2026-08-09) — **âncora de profundidade** (§3[B]) + **estratificação da seleção por profundidade** (§3[C2]). **Última sessão da camada de coleta:** depois desta versão, todo parâmetro restante do projeto é de ANÁLISE, aplicável sobre o bruto sem uma requisição. Fronteiras, cota, `min_chars`, cascata, orçamento base, teto de extensão, ordenação e `RESERVA_PROFUNDIDADE` **não tocados**.
  - **(1) A âncora da progressão profunda estava presa ao lugar errado.** Medido na sessão anterior: o bloco profundo da v1.9.2 comprava mediana de **3 dias** sobre o raso (26 de 34 filmes abaixo de 7 dias). Causa: a progressão partia do FIM DO BLOCO RASO (`n_raso+2, +4, +8, +16`), o que com `n_raso≈12` põe as posições "profundas" em 14-28 de níveis que vão a ~256 — profundo em POSIÇÃO DE PÁGINA, raso em TEMPO. **Quarto caso do mesmo padrão do projeto** (50/20/30 pelo nº de degraus; teto por nível contra cota por bucket; ordem de consumo definindo a coorte; agora a âncora): um parâmetro que ninguém tinha classificado como parâmetro. Correção: as posições profundas passam a ser **frações da profundidade REAL** do nível (`FRACOES_PROFUNDIDADE = 0,25/0,50/0,75/0,95`). `RESERVA_PROFUNDIDADE` e o orçamento por bucket **não mudam** — muda ONDE as páginas caem, não QUANTAS, e há teste que compara o número de páginas por nível antes e depois exigindo igualdade exata.
  - **(2) Sondagem de profundidade POR FILME (§3[B]).** Escada geométrica (4·16·64·256) no nível mais populoso + refinamento binário de até 3 passos; os demais níveis escalados pela proporção do histograma. O passo de escala é um **PROXY declarado** (histograma conta NOTAS, paginação conta REVIEWS COM TEXTO — mesma aproximação de §3[C1]); a defesa não é que acerte, é que errar sai barato, porque posição estimada que volta vazia cai no mecanismo de descoberta da v1.9.2, **reusando `redistribuir_deficit`**, sem segundo caminho. Sondagem que falha → degrada para o comportamento v1.9.2, registrado em telemetria, sem bloquear coleta. Novos campos em `meta.json`: `profundidade_sondagem` e `profundidade_estimada_por_nivel`.
  - **(3) Por que não bastava declarar a recência.** O histograma **não é recortável no tempo** — o endpoint devolve o acumulado da vida do filme e não há versão temporal dele. Declarar congelaria um parágrafo em que o rótulo de peso fala de 2012-2026 e a frequência de tema fala de 6 semanas: não corrigido, só confessado. Como a única metade ajustável é a da amostra, é ela que se move.
  - **(4) Estratificação da seleção — E1 (§3[C2]).** A seleção consumia o pool por `(pagina_origem, ordem no jsonl)` e parava na cota, então recência era critério implícito: das 1316 profundas elegíveis só 716 (54,4%) entravam, e 13 de 105 buckets selecionavam ZERO profundo. Agora a cota de cada nível é alocada entre 3 faixas de profundidade (**quinto uso de `redistribuir_deficit`**). **Custo medido antes de adotar: ZERO** — 0 de 105 buckets perdem uma review, uso do profundo sobe para 86,2%, comprimento e perfil da amostra inalterados. Nos 9% de níveis com cota < 3 a estratificação **cede** para a alocação proporcional por nível. `selecionar` sem `orcamento_paginas_por_nivel` continua byte-idêntica à v1.9.4.
- **v1.9.4** (2026-08-08) — **extensão de orçamento por DÉFICIT** (§3[B]) + guard-rail de adaptador de LLM (§3[D]). Nenhum outro parâmetro de coleta tocado: `MIN_CHARS`, cascata, fronteiras, cota, alocação proporcional, `ORCAMENTO_PAGINAS_POR_BUCKET` (a base **continua 16**), ordenação e reserva de profundidade seguem idênticos. Nenhuma etapa de síntese/narrador/editor tocada; nenhum `resultado/*.json` republicado.
  - **(1) Extensão por déficit, OBSERVACIONAL (§3[B]).** Fecha a classe achada pela diagnose da v1.9.3: 9 filmes muito populares com o bucket DOMINANTE abaixo da cota, 4 deles com o dominante tendo `n` MENOR que os buckets minoritários do mesmo filme. Regra: gasta a base de 16 como sempre; se o bucket fecha a base com menos válidas que a meta com folga (40 × 1,25 = 50), concede páginas extras **uma a uma** até `TETO_EXTENSAO_PAGINAS = 24`, aos níveis em déficit; para no teto, na meta ou em material esgotado. **Zero estimativa de rendimento** — a rejeição do desenho preditivo está registrada em §3[B] com o racional (páginas log-espaçadas não são amostra do mesmo regime; e a parada por ALVO, removida na v1.9.2, era exatamente uma heurística otimista decidindo orçamento). Alocação das extras: **quarto uso de `redistribuir_deficit`**, pesada por DÉFICIT MEDIDO e não por histograma — pesar por histograma daria as extras ao mesmo nível populoso de baixo rendimento que a diagnose apontou como amplificador. Extras são ANEXADAS (posições não buscadas dentro do intervalo já confirmado primeiro, com conteúdo garantido por monotonicidade; depois consecutivas além), nunca recalculam a divisão raso/profundo — a base continua sendo prefixo exato da coleta estendida. Telemetria obrigatória por bucket em `meta.json` (`extensao_por_bucket`): páginas base, extras concedidas, extras por nível, motivo de parada, válidas antes e depois.
  - **(2) Correção e declaração como CAMADAS (§3[B]).** O teto de 24 garante que alguns buckets seguem abaixo de 40 — esperado, não falha. Registrado que a extensão encolhe a CLASSE de buckets sub-40 e que o piso escalonado (§3[C3]) + o denominador visível absorvem o RESÍDUO; a declaração honesta continua sendo o mecanismo final, não a alternativa rejeitada.
  - **(2b) Recoleta seletiva MEDIDA — 9 filmes, 0 falhas.** Bucket dominante fechando a cota **0/9 → 4/9**; buckets abaixo de 40 **22/27 → 12/27**; dominante medido com menos precisão que um minoritário do mesmo filme **5 → 3** filmes. 222 requisições (24,7/filme, contra ~78/filme de coleta do zero), 551 s. 188 páginas extras → 225 válidas (~10% de rendimento, dentro da faixa que a diagnose mediu). 21 buckets pararam por `teto_extensao`, 6 por `meta_atingida`, **0 por `material_esgotado`**. Os 12 buckets que seguem abaixo de 40 param TODOS por teto de custo, não por falta de material — é o resíduo que o piso escalonado absorve (27/27 em `completa`). Tabela e ressalvas em §3[B], "Resultado MEDIDO da recoleta v1.9.4".
  - **(2c) Regressão introduzida pela extensão e corrigida na mesma sessão:** `--offline` passou a quebrar em todo filme coletado ANTES da v1.9.4 — a extensão pedia página nunca cacheada e o `FetchError` subia pelo pipeline (reproduzido em `longlegs`, página 9 do nível 2,0★). Guarda explícita no gancho: com `fetcher.offline`, devolve o `extensao_por_bucket` já em disco sem buscar nada (não devolver nada apagaria o registro, porque `persistir` sobrescreve o meta). Verificado contra dado real: 0 requisições de rede. Limitação declarada e NÃO corrigida: o teto de 24 é por EXECUÇÃO, não pela vida do bruto.
  - **(3) Guard-rail do adaptador de LLM (§3[D]).** O gate de taxonomia reintroduziu um bug resolvido na v1.8.0 — chamada direta ao SDK do DeepSeek sem `thinking: disabled`, 8 de 12 respostas vazias. Uma regra escrita falharia igual na próxima; o padrão da spec é lição vira mecanismo. `tests/test_guardrail_adaptador.py` varre `src/` **e `scripts/`** procurando import/instanciação de SDK e chamadas diretas de geração fora de `synthesize.py`, com allowlist literal e justificada (os 3 scripts de diagnóstico cujo objeto de estudo É o parâmetro de thinking). `scripts/gate_taxonomia.py` foi reparado para usar o adaptador.
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