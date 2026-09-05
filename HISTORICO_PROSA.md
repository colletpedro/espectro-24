# Histórico — SÍNTESE, NARRADOR, VEREDITO e o EDITOR aposentado

Este arquivo responde *"por que a prosa é assim, e o que já foi tentado?"*.

Cobre: o guard-rail do adaptador e a arqueologia da retentativa, o briefing
determinístico, os tiques de prosa, o narrador antigo (arquivado), o estágio
`[E2] Editor` (**aposentado na v1.9.10** — está aqui, e não em `SPEC.md`,
porque não roda), a deflação e o padrão de abertura do veredito, e a pendência
editorial do eixo `expectativa`.

> **Aviso de leitura.** Duas seções aqui descrevem coisas que **não estão em
> vigor**: o prompt do narrador antigo e o estágio `[E2]`. Ambas foram
> verificadas contra o código em 2026-09-04 — `NARRATOR_SYSTEM_PROMPT` não
> existe em `src/`, e `cli.py` não chama o editor.

---

<!-- SPEC.md linhas 46–60 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

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


<!-- SPEC.md linhas 432–460 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **DETECÇÃO MECÂNICA DE SPOILER: MEDIDA E RECUSADA como validador.** Sobre as
> 266 condições da rodada 3, o marcador lexical dispara em 19 (7,1%) e acerta
> 3 dos 5 casos reais — **precisão de 15,8%**, pior que os 7,7% do léxico de
> valência que a rodada 3 removeu, e com o mesmo modo de falha caro (falso
> positivo descarta condição boa). Ele entra apenas como **marca no
> BRIEFING**, por **assimetria de custo**: ali um falso positivo só deixa o
> modelo mais cuidadoso. A rede continua sendo a regra no prompt mais a
> leitura humana — que é o que a terceira garantia desta exceção já dizia.
>
> **[v1.9.37] ACHADO DE MÉTODO, não bug corrigido: UM EXEMPLO DENTRO DO
> PROMPT TEM FORÇA DE REGRA, e um exemplo contraditório derrota a regra que
> ele deveria ilustrar.** É a SEGUNDA vez neste arco que isso acontece, e as
> duas vezes o mecanismo é o mesmo: a proibição explícita fica correta, e o
> exemplo ilustrativo ao lado dela ensina o padrão oposto.
>
> - **Primeira vez (rodada 1→4).** O preâmbulo original do prompt dizia *"Ela
>   descreve o LEITOR, não o filme"*, com o par de exemplo *"quer um retrato
>   íntimo, não o estadista" / "o filme é íntimo"*. A proibição de perfil não
>   estava escrita ainda — só o exemplo —, e o exemplo produziu exatamente o
>   molde *"prioriza X em vez de Y"* que a rodada 4 teve de proibir por
>   extenso.
> - **Segunda vez (rodada 4→5).** A regra de anti-spoiler da rodada 4 dava
>   como formulação **PREFERÍVEL** *"busca histórias que recontextualizam o
>   que veio antes"* — e "recontextualizar" é precisamente a descrição do
>   EFEITO de uma reviravolta que a Decisão 2 da rodada 5 veio proibir. O
>   modelo seguiu o exemplo que o prompt lhe deu como bom: `shutter-island`
>   produziu *"aprecia uma mudança memorável de perspectiva na trama"*, a
>   mesma família da frase "preferível" que estava escrita ali.
>

<!-- SPEC.md linhas 470–534 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **O conflito é ESTRUTURAL, não de redação.** `expectativa` é o **único dos
> dez eixos da taxonomia cujo objeto não é o filme** — é a relação entre o
> público e a REPUTAÇÃO do filme. Os outros nove nomeiam algo que está na
> tela (ritmo, atuação, imagem, som, roteiro, tom, comparações, crítica
> social, impacto). Este nomeia algo que está **fora** dela.
>
> A gramática das condições exige ancorar na obra (*"estas são experiências e
> qualidades que a recepção encontrou NESTE filme"*). Um eixo cujo assunto é
> a reputação não tem o que ancorar, e as três saídas observadas em cinco
> rodadas de estudo foram todas ruins:
>
> 1. **abster** — perde informação de decisão real (rodada 4, 6 filmes);
> 2. **subir ao meta** — *"quando obras de grande reputação não correspondem
>    a altas expectativas"*, reprovado no portão editorial;
> 3. **descer ao conteúdo que a paráfrase carrega ao lado da reputação** — só
>    funciona quando esse conteúdo existe.
>
> **DECISÃO EDITORIAL DO DONO: não reescrever agora.** As condições deste
> eixo saem do conjunto considerado fechado até que o destino do eixo seja
> decidido. Reescrevê-las seria inventar soluções pontuais para um problema
> que é do eixo, e salvar a categoria fabricando atributo do filme é o que a
> regra de lastro proíbe.
>
> **AS OCORRÊNCIAS SÃO SEIS, e não cinco.** A varredura por eixo (e não por
> memória da leitura) encontrou uma que a lista não continha:
>
> | filme | tema | texto atual |
> |---|---|---|
> | `the-godfather` NEG-B | Filme superestimado | *acha que o filme não merece tanto elogio quanto recebe* |
> | `hereditary` NEG-B | Expectativa vs. realidade (hype) | *se decepciona quando filmes de grande repercussão não correspondem a altas expectativas* |
> | `interstellar` NEG-B | Filme superestimado | *se frustra quando um filme muito elogiado parece superestimado* |
> | `longlegs` NEG-B | Expectativa alta, decepção | *se frustra quando obras cercadas de grande expectativa não correspondem à forte repercussão* |
> | `parasite-2019` NEG-C | Expectativa não correspondida | *se frustra quando obras premiadas e consagradas não correspondem a altas expectativas* |
> | **`everything-everywhere-all-at-once` NEG-F** | Superestimado e prêmios injustificados | *se decepciona quando obras muito aclamadas aparentam profundidade sem substância real* |
>
> **Duas condições do eixo NÃO entram na pendência**, e a razão é a mesma que
> define o conflito — nelas o objeto **é o filme**:
> `spider-man-across-the-spider-verse` POS-E (o final aberto da própria obra)
> e `talk-to-me-2022` NEG-C (o potencial da própria premissa).
>
> **`friday-the-13th-2009` POS-B é EXCEÇÃO, não molde.** Ele saiu do eixo
> porque a paráfrase dele oferecia uma comparação concreta fora da reputação
> (*"é superior a outros remakes e à maioria das sequências originais"*), e a
> condição final usa essa comparação: *"acha este remake superior às
> sequências originais da franquia"*. **A maioria das paráfrases deste eixo
> não oferece esse conteúdo**, e tratar o caso dele como receita produziria
> exatamente a fabricação que a regra de lastro proíbe.
>
> **O DADO QUE INFORMA A DECISÃO FUTURA — MEDIDO nesta sessão** sobre
> `consenso_verificado.jsonl` (5.371 reviews) e sobre os 629 bullets
> publicados:
>
> | | reviews | bullets | razão |
> |---|---:|---:|---:|
> | `expectativa` | **20,6%** | **4,0%** | 5,2× |
>
> **CORREÇÃO DE REGISTRO: `expectativa` NÃO é a segunda maior assimetria do
> catálogo.** Por razão entre as duas taxas é a **terceira** (atrás de
> `comparacoes` 16,3× e `impacto_emocional` 5,6×); por diferença em pontos
> percentuais é a **sexta** (+16,6pp, atrás de `comparacoes` +36,6,
> `roteiro_estrutura` +30,9, `impacto_emocional` +29,8, `direcao_imagem`
> +19,6 e `ritmo` +18,4). **O que a medição sustenta é a conclusão, não a
> posição:** com 20,6% das reviews carregando o eixo e 4,0% dos bullets
> publicando-o, **o problema nunca foi de volume de informação.**
>

<!-- SPEC.md linhas 546–550 · origem: 0. Princípio norteador (v1.4.0) — NEUTRALIDADE DE TRATAMENTO, NÃO DE FATO -->

> **PUBLICADO em 2026-09-04:** 257 condições nos 35 filmes,
> `https://espectro-24-eu6z.vercel.app`. Harness `publicar_condicoes.py`,
> travado por `tests/test_publicar_condicoes.py`. O bloco entra entre a BARRA
> e os BULLETS; o veredito continua no fecho (v1.9.26, não movido).
>

<!-- SPEC.md linhas 4075–4104 · origem: [D] Síntese LLM -->

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

<!-- SPEC.md linhas 4128–4172 · origem: [D] Síntese LLM -->

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

<!-- SPEC.md linhas 4183–4504 · origem: [D] Síntese LLM -->

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
> alimentaram a promoção da regra `A_regra` — o que ela é está definido em
> §3[D], "Instrução não remove o que a distribuição do material impõe";
> *correção de 2026-09-04: este ponteiro dizia "§3[D] 'razão PAREADA'", que é
> a subseção do PREDITOR de mudança de frequência, não a da promoção*), fora
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

<!-- SPEC.md linhas 4511–4784 · origem: [D] Síntese LLM -->

> **Por que a classificação NÃO migra.** Ela está calibrada e auditada
> contra um gabarito humano de 100 reviews, com precisão e recall medidos
> por eixo (`docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md`). **[v1.9.34] O gabarito vive em
> `resultado/auditoria-acuracia/leitura.md`, e a TRILHA das duas correções
> que o produziram está versionada ao lado, em `leitura.md.bak-0` e
> `.bak-1`** (`.bak-0` → `.bak-1` → vigente; o que se move entre eles é
> `impacto_emocional`, 32 reviews de diferença entre o primeiro snapshot e o
> atual — a correção de `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §5). **Não recrie um
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
> `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §5), todas atacando a saturação de
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
> `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §5b): estágio separado, rodando após o
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
> **O que este padrão NÃO diz.** Não diz que toda instrução falha — o bloco
> REGRAS de `A_regra` É instrução, e funcionou, medido. A diferença é que ali
> a instrução mudava um
> CRITÉRIO DE DECISÃO bem definido (brevidade não é ausência), e aqui as
> três tentativas pediam para o modelo SUPRIMIR um comportamento que parece
> vir de um prior mais profundo do modelo pré-treinado (associar veredicto
> a `impacto_emocional`) — instrução muda critério, não sempre suprime prior.
>
> > **O QUE É `A_regra`, escrito aqui porque a remissão anterior apontava para
> > lugar nenhum (correção de 2026-09-04).** O texto dizia *"as **7 regras** de
> > `A_regra` (**§ correção de recall em review curta**)"*, e **não existe
> > seção com esse nome nesta spec** — `A_regra` aparecia seis vezes no
> > documento sem nunca ser definida, e o número "7" não tem fonte.
> >
> > **`A_regra` é a variante PROMOVIDA do bloco REGRAS do prompt de
> > classificação** (`scripts/classificar_10.py`), adotada em 2026-08-13. A
> > mudança, por extenso: **brevidade não é ausência de conteúdo, e `livre` é
> > redefinido por ASSUNTO** (a review não fala do filme) **em vez de por
> > profundidade** (fala pouco do filme). Ela corrige um defeito medido de
> > recall em review curta: recall 0,35 em reviews ≤200 chars contra 0,88
> > acima de 400, com precisão estável em toda a faixa — o modelo não trocava
> > de eixo em texto curto, ele OMITIA eixo.
> >
> > **MEDIDO (bootstrap pareado, B=5000):** recall ≤200 chars 0,35→0,61
> > (δ +0,265, IC95 [+0,171, +0,370]); recall geral 0,69→0,76; reviews com
> > recall zero 27→5; consensos vazios 8→0; **sem perda de precisão
> > detectável** (IC95 de δ precisão cruza zero). A variante B (`fewshot`, as
> > mesmas regras + 6 exemplos de review curta) foi **REJEITADA**: os exemplos
> > ancoraram o modelo e degradaram review longa.
> >
> > **Só o bloco REGRAS mudou** — a lista de eixos e as 10 definições seguem
> > byte-idênticas, travadas por `tests/test_variantes_prompt.py` e
> > `tests/test_promocao_a_regra.py`. É por isso que o `taxonomia_id` mudou de
> > `11871105c0d3` para **`ebab2667de74`** (§2.5), que é o corrente.
> > Fonte: `docs/arquivo-de-estudos/classificacao/CLASSIFICACAO_CONSOLIDADO.md` §3; `docs/arquivo-de-estudos/classificacao/TAXONOMIA_10.md`, "Correção de
> > recall em review curta"; `resultado/auditoria-acuracia/variantes/`.

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


<!-- SPEC.md linhas 4894–4915 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

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

<!-- SPEC.md linhas 4947–4977 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

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

<!-- SPEC.md linhas 5014–5055 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

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

<!-- SPEC.md linhas 5086–5364 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

> **O que a decisão comprou:** deletar o estágio deletou as suas três classes
> de falha de uma vez — as 4 tentativas descartadas em `cure`, o parágrafo
> de opinião inventado em `the-invite-2026`, e a inversão de movimentos.
> Nenhuma delas pode mais ocorrer, porque o mecanismo que as causava não
> roda.
>
> **A alternativa que NÃO foi usada, e por que ela fica registrada:** se o
> ritmo tivesse faltado, o plano já decidido era reescopar o editor por
> MOVIMENTO (3 blocos), o que tornaria inversão de ordem impossível POR
> CONSTRUÇÃO. Ela nunca foi executada, e é o ponto de partida de quem um dia
> quiser um passe de edição de novo — o reescopo resolve a inversão, mas as
> outras duas classes de falha continuariam exigindo mitigação em cada bloco,
> que foi o argumento que decidiu por aposentar em vez de reescopar.
>
> *(Correção de registro, 2026-09-04: este item dizia "PREPARADO, não
> decidido" e "Esta versão **não** aposenta nem reescopa nada". Era verdade
> na v1.9.9, e a decisão saiu na v1.9.10 — o bloco seguinte, nesta mesma
> seção. A condicional ficou de pé por 28 versões, ao lado da sua própria
> resposta.)*
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
> levantamento da v1.9.10 (`docs/arquivo-de-estudos/aceite-e-mapa/MAPA_PROXIMA_FASE.md`) achou o item que
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



<!-- SPEC.md linhas 5372–5428 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

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

<!-- SPEC.md linhas 5441–5528 · origem: [D2] Narrador — saída narrativa, em TRÊS MOVIMENTOS (v1.2.0, reescrito v1.3.0/v1.3.1/v1.4.0) -->

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



<!-- SPEC.md linhas 5544–5566 · origem: Diagnóstico de fluência (v1.5.0) — por que as narrativas soavam mecânicas -->

#### Diagnóstico de fluência (v1.5.0) — por que as narrativas soavam mecânicas

Leitura adversarial das narrativas entregues até a v1.4.1 (o texto de `the-invite-2026`, ver `resultado/the-invite-2026.json` campo `narrativa`, é o caso citado) revelou um padrão sistemático, não um defeito isolado:

- **Forma sintática repetida:** cada perspectiva era apresentada com a MESMA estrutura — rótulo de peso, seguido de verbo de reporte ("elogia", "reconhece", "classifica"), seguido de complemento — três vezes seguidas, uma por grupo.
- **Comprimento de frase quase constante:** a maioria das frases caía na faixa de 25-35 palavras, sem variação perceptível.
- **Densidade alta de verbos de reporte e nominalizações** no lugar de verbos diretos ("a repetição das situações torna a experiência cansativa" em vez de "as situações se repetem e o filme cansa").

**Causa provável:** o acúmulo de invariantes de honestidade das versões anteriores (peso ancorado com percentual, quantificador pré-computado, escopo por grupo, anti-spoiler, sem aspas, vocabulário "das notas") — cada uma necessária e nenhuma removida nesta versão — levou o modelo à ÚNICA forma sintática que satisfaz todas simultaneamente ao mesmo tempo: relatar, com um verbo, o que cada grupo (identificado pelo rótulo de peso) diz. É previsível: sob restrição suficiente, convergir para uma forma única é o caminho de menor risco para o modelo não violar nenhuma regra. A correção desta versão não afrouxa nenhuma invariante — prescreve **ritmo** e **registro** com a mesma precisão de código com que os números já são prescritos, para que a honestidade não dependa de sacrificar a fluência.

#### RITMO E REGISTRO — MIGRADOS PARA O EDITOR §E2 (v1.6.0)

As regras de ritmo e registro introduzidas na v1.5.0 (variação de comprimento e de abertura, conectivos de fala, limite de verbos de reporte, proibição de advérbios em -mente, tom de "contar para um amigo") **saíram do prompt do narrador** e passaram a viver no **editor (§E2)**. O par few-shot ANTES/DEPOIS foi movido junto — não duplicado.

**Por que a v1.5.0 falhou** (evidência em `docs/arquivo-de-estudos/editor-e-narrador/DIAGNOSTICO_FLUENCIA.md` e `docs/arquivo-de-estudos/editor-e-narrador/DIAGNOSTICO_FLUENCIA_V2.md`):
- **as regras não transferiram.** O `the-invite` pareceu obedecer, mas estava **copiando o few-shot** — 58 8-gramas compartilhados, porque o exemplo fora escrito com os dados daquele mesmo filme. `cure` e `cidade-de-deus`, sem nada a copiar, não transferiram estilo nenhum e pioraram em pontos;
- **a fiscalização era cega.** As métricas que disparavam retentativa não acompanham qualidade: no `cure`, o texto qualitativamente melhor pontuou PIOR em `cv_comprimento` (0.35 → 0.28) e em `verbos_reporte` (3 → 6);
- **o custo apareceu na saída publicada.** A configuração de produção (`thinking_budget=0`) gerou uma frase agramatical que foi ao ar.

**O diagnóstico de fundo permanece válido** (ver seção anterior): sob restrição suficiente, o modelo converge para a única forma que satisfaz todas as regras. O erro foi tentar resolver isso **empilhando mais regras no mesmo prompt** — o que aumenta a restrição em vez de aliviá-la. A v1.6.0 tira a carga de estilo do narrador e a entrega a um estágio que só tem essa função, e que é estruturalmente incapaz de comprometer a honestidade (§E2).

**O que o narrador ganhou no lugar:** uma nota curta avisando que existe um estágio de edição depois, que ele não precisa se preocupar com ritmo, e que deve escrever de forma clara e **gramaticalmente correta**. Nada além disso.


<!-- SPEC.md linhas 5606–5611 · origem: EXEMPLO DE ESTILO — MIGRADO PARA O EDITOR §E2 (v1.6.0) -->

#### EXEMPLO DE ESTILO — MIGRADO PARA O EDITOR §E2 (v1.6.0)

O par ANTES/DEPOIS foi **movido** para o prompt do editor (§E2), onde o eixo de ritmo agora vive. Ele permanece **descontaminado** — filme fictício, números inventados (74/19/7) —, e um teste (`test_v160_few_shot_do_editor_segue_descontaminado`) impede a reintrodução de nomes ou shares do catálogo.

> **Registro histórico da descontaminação (sessão de diagnóstico, 2026-07-25):** a primeira versão do par usava os **dados reais do `the-invite-2026`** (79/18/3, o nome da diretora, o apartamento único). Medindo sobreposição de 8-gramas com as construções mandatórias mascaradas: `the-invite` **58**, `cure` **0**, `cidade-de-deus` **0**. Ou seja, o filme que parecia ter aprendido o estilo estava **copiando o exemplo**, e os outros dois não transferiram nada. Um few-shot construído sobre um filme do catálogo contamina a avaliação daquele filme e só daquele — e por isso não mede nada. Dois micro-exemplos que também carregavam dados do `the-invite` (a regra (e) de REGISTRO e a ilustração da ANCORAGEM) foram neutralizados junto.


<!-- SPEC.md linhas 5641–5706 · origem: Telemetria de fluência (v1.5.0, NOVO) — métricas calculadas em código, não pelo LLM -->

**Prompt fixo do narrador ANTIGO (pré-briefing, v1.2.0–v1.9.7) — REGISTRO HISTÓRICO, não é o prompt em vigor:**

> **CORREÇÃO DE REGISTRO (2026-09-04): este bloco estava rotulado "SPEC —
> texto oficial, `NARRATOR_SYSTEM_PROMPT` em `synthesize.py`", e as duas
> metades do rótulo estavam erradas.** Conferido no código: **`NARRATOR_SYSTEM_PROMPT`
> não existe em `src/`** — ele vive em
> `experimentos-narrador-antigo-arquivado/narrador_antigo.py`, arquivado na
> v1.9.11 junto com `build_narrator_prompt` e `narrate_output`; e o caminho de
> produção é `narrador.narrar()`, que monta **`PROMPT_NARRADOR_BRIEFING`**
> (`briefing.py`) sobre o briefing determinístico e gera best-of-3.
>
> **O que isso muda para quem lê:** o texto abaixo descreve um narrador que
> SELECIONAVA e ESCREVIA ao mesmo tempo, segurando ~18 invariantes numa
> chamada só. O narrador em vigor **só verbaliza** — tema, ordem, número,
> rótulo e orçamento de frases chegam prontos do briefing (§D2, "BRIEFING
> DETERMINÍSTICO"). As invariantes que sobreviveram estão em
> `INVARIANTES_REMANESCENTES` (`briefing.py`) e são nove, não dezoito.
>
> **O bloco fica porque é a linha de base de toda medição de prosa do
> projeto** — os diagnósticos de fluência, a comparação de modelos e o
> best-of-3 se comparam contra ele. **Nada abaixo é instrução em vigor.**

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


<!-- SPEC.md linhas 5806–5827 · origem: Telemetria de `quantificadores_usados` (v1.4.1, NOVO) — o quantificador declarado junto do seu tema -->

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


<!-- SPEC.md linhas 6052–6073 · origem: O defeito medido, e por que ele não é do template -->

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


<!-- SPEC.md linhas 6313–6330 · origem: O limiar é BINÁRIO — nenhuma noção de "quase passou" -->

#### O limiar é BINÁRIO — nenhuma noção de "quase passou"

**O caso, com os números do artefato publicado hoje** (conferido em
`resultado/the-godfather.json`, 2026-09-04): `the-godfather` tem `n = 30` (o
MENOR dos três buckets), logo `limiar(30) = 26,36pp`; o melhor lift das
negativas é **12,5pp** no eixo `ritmo` (18 de 30 = 60%, tema *"Ritmo lento e
tédio"*), `acima_da_margem: false`. Nenhuma das 30 células atinge o limiar, e
o filme é **`valorativo`**.

> **CORREÇÃO DE REGISTRO (2026-09-04): os números que estavam aqui eram os da
> v1.9.21 e não descrevem mais nenhum artefato.** O texto dizia *"o melhor
> lift das negativas em **19,6pp** contra a margem de 20 (eixo `ritmo`, 16 de
> 25 = 64%) … falha por 0,4pp"*. **Três dos quatro números mudaram**, por dois
> eventos independentes e ambos registrados nesta spec: a cobertura de
> classificação foi a 100% (§2.8), o que mexeu nas contagens (16/25 → 18/30);
> e a margem virou lei por `n` (§2.5), o que mexeu no limiar (20 → 26,36). O
> filme continua `valorativo` — **a conclusão sobreviveu, a aritmética não**.
>

<!-- SPEC.md linhas 6437–6500 · origem: [v1.9.22] Deflação, neutralidade do §0, e o padrão de abertura -->

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


<!-- SPEC.md linhas 6559–6669 · origem: [v1.9.22] Deflação, neutralidade do §0, e o padrão de abertura -->

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


<!-- SPEC.md linhas 6818–6903 · origem: O veredito deixa de ser 100% determinístico — o registro honesto -->

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


<!-- SPEC.md linhas 7125–7238 · origem: [E2] Editor — passe de EDIÇÃO da narrativa (v1.6.0) — **APOSENTADO na v1.9.10, seção mantida como REGISTRO HISTÓRICO** -->

### [E2] Editor — passe de EDIÇÃO da narrativa (v1.6.0) — **APOSENTADO na v1.9.10, seção mantida como REGISTRO HISTÓRICO**

> **ESTE ESTÁGIO NÃO RODA. Leia isto antes de qualquer linha abaixo.** O
> editor [E2] foi **APOSENTADO na v1.9.10** (decisão do dono do projeto,
> registrada em §D2, "FECHAMENTO DO NARRADOR … editor aposentado"): a leitura
> das narrativas geradas sem ele mostrou que o ritmo se sustenta sozinho, e
> deletar o estágio deletou de uma vez as suas três classes de falha (edição
> descartada por esgotar tentativas, conteúdo inventado, inversão de
> movimentos).
>
> **Conferido no código em 2026-09-04, e é por isso que a redação desta seção
> mudou de presente para passado:** `cli.py` não chama o editor (só um
> comentário registrando a aposentadoria); **as flags `--no-edicao` e
> `--com-editor` não existem** em nenhum `add_argument`; as constantes
> `EDITOR_*` (inclusive `EDITOR_ATIVO`) saíram de `config.py`, que guarda
> apenas um comentário no lugar delas; `editar_narrativa` e
> `_EDITOR_SYSTEM_PROMPT` não existem em `src/` — sobrevivem só em
> `experimentos-editor-e2-arquivado/editor.py`, arquivado com o motivo ao
> lado, nunca deletado.
>
> **A seção fica, e não é sentimentalismo:** o prompt, os trechos protegidos e
> as três verificações mecânicas abaixo são o registro do desenho que foi
> tentado e do porquê de ele ter saído — e a v1.9.9 registra a alternativa que
> chegou a ser decidida caso o ritmo NÃO se sustentasse (reescopar por
> MOVIMENTO). Quem for reabrir o assunto precisa disto. **Tudo abaixo está no
> PASSADO; nada abaixo descreve comportamento em vigor.**

Era uma etapa **PÓS-narrador**, ativada junto com `--tom narrativo|ambos` e desligável com `--no-edicao` (as duas flags foram removidas na v1.9.10). **Uma única chamada LLM por filme** (+1 sobre o custo da v1.5.0), mesmo provider/modelo, na configuração de prosa (§2: `thinking_budget=4096`, `max_output_tokens=16000`).

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

