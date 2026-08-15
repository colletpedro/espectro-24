"""Parâmetros congelados da spec (SPEC.md §2) e constantes técnicas (§2.1).

Nenhum valor aqui deve divergir da SPEC.md sem bump de versão.
"""
from __future__ import annotations

SPEC_VERSION = "1.9.0"

BASE = "https://letterboxd.com"

# Fronteiras de bucket: leia `buckets.py`. NADA aqui redigita uma fronteira —
# tudo abaixo é derivado (SPEC §2.2, v1.9.0).
from .buckets import (  # noqa: E402  (import posicionado junto do que ele alimenta)
    FRONTEIRAS,
    NIVEIS,
    bucket_de_nivel,
    mapa_de_niveis,
)

# --- Headers validados na Fase 0 (RESULTADO.md / §2.1) ---
# IMPORTANTE: Accept-Encoding sem `br` — requests não decodifica Brotli.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://letterboxd.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Chromium";v="126", "Not(A:Brand";v="24", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}

DELAY_SECONDS = 2.0  # §2: ≥2s, sem paralelismo

# --- Retentativa de rede (§2.4, v1.9.6) ------------------------------------
# Só erro de TRANSPORTE retenta. 403/challenge, 404 e o SEGUNDO 503 do lote
# param imediatamente — retentar bloqueio é evasão, e a spec proíbe.
# Motivação medida: na recoleta da v1.9.5, 10 falhas de rede em 28 filmes
# (36%), todas transitórias, cada uma abortando um filme inteiro por falta de
# uma segunda tentativa.
MAX_TENTATIVAS = 3
# Backoff exponencial `2s · 4s` entre as tentativas (a 3ª falha não espera:
# não há quarta). O jitter existe para que um lote que tropece no mesmo
# instante não volte em uníssono — sem ele, a retentativa vira pressão
# coordenada, que é o oposto do que o delay de educação (§2) protege.
BACKOFF_BASE_SEGUNDOS = 2.0
BACKOFF_JITTER = 0.25
# 503 é o servidor dizendo que está sobrecarregado. A espera é
# DELIBERADAMENTE muito maior que a de transporte: ali o problema é o
# caminho, aqui é o site — esperar mais é cooperar, insistir rápido seria
# pressão.
ESPERA_503 = 30.0
# Quantos 503 o LOTE absorve com retentativa antes de PARAR. `1` — a segunda
# ocorrência levanta `SobrecargaError`. A v1.9.5 foi interrompida por um 503 e
# essa decisão foi correta; automatizar a insistência a desfaria.
LIMITE_503_LOTE = 1

# --- Buckets e cotas (§2) ---
# DERIVADO das fronteiras (v1.9.0). Cada nível pertence a exatamente um bucket
# — garantido por `validar_fronteiras`, que roda no import de `buckets.py`.
BUCKETS: dict[str, list[float]] = mapa_de_niveis(FRONTEIRAS)

# --- Cota de ANÁLISE (§2, v1.9.0) ---
# 40 por bucket, IGUAL nos três. Até a v1.8.2 os alvos eram 50/20/30, que não
# era decisão de profundidade e sim aritmética: 10 reviews × o número de
# níveis de estrela de cada faixa (5/2/3). O grupo mediano recebia 40% da
# profundidade do negativo por ter dois níveis em vez de cinco. A cota igual
# escreve como número o que o §0 já dizia como frase: profundidade igual por
# perspectiva, peso informado à parte.
COTA_POR_BUCKET = 40
BUCKET_ALVO = {nome: COTA_POR_BUCKET for nome in BUCKETS}

# Piso de alocação POR NÍVEL dentro do bucket (§3[C1]). Só se aplica a níveis
# que têm material no histograma. Garante que um nível pequeno não desapareça
# da amostra por arredondamento — sem ele, "negativas" de um filme muito
# amado poderia virar só 2,0★.
# ARBITRÁRIO e calibrável, como os limiares do piso escalonado abaixo: não há
# evidência empírica que o fixe em 2; é a ordem de grandeza que faz sentido
# para 4 níveis dividindo 40 vagas.
PISO_ALOCACAO_POR_NIVEL = 2

# Piso de análise por bucket — ESCALONADO em 4 estados (§3[C3], v1.9.0).
# Substitui o piso binário de 3 (`PISO_POR_BUCKET`), que só distinguia "tem
# análise" de "não tem". Lido do maior para o menor: o primeiro limiar que o
# `n` final alcançar vence.
# LIMIARES ARBITRÁRIOS — entram na spec com esse rótulo explícito, mesma
# política dos limiares de `marcacao_perspectiva` (v1.5.0). A ordem de
# grandeza é defensável pela tabela de precisão de §3[C2] (em n=8 o intervalo
# de 95% já passa de ±34pp, o que torna um quantificador verbal
# indefensável); os cortes exatos não são.
PISO_ESCALONADO: tuple[tuple[int, str], ...] = (
    (15, "completa"),            # temas + frequências + quantificadores
    (8, "sem_quantificador"),    # frequências, com marca de amostra pequena
    (3, "sem_numero"),           # temas listados, sem número nem quantificador
    (0, "sem_analise"),          # contagem + reviews_url, nenhum tema
)
PISO_POR_BUCKET = 3          # piso mínimo p/ QUALQUER análise temática (= 3)

# LEGADO — cota de reviews válidas POR NÍVEL (v1.1.0), REVOGADA em §2 pela
# alocação proporcional (§3[C1]). Ainda referenciada pelo caminho de coleta
# da v1.8.2 (`collector.collect_level`), que é substituído mais adiante nesta
# mesma versão pelo superset (§3[B]). Some junto com ele.
COTA_POR_NIVEL = 10

MIN_CHARS = 150              # §2: filtro de comprimento padrão
CASCATA_CHARS = [150, 50, 0] # §2/§C: 150 → 50 → sem filtro (0 = sem filtro)

# --- Parâmetros de COLETA do superset (§3[B], v1.9.0/v1.9.1) ---
# LEGADO — teto de paginação POR NÍVEL (6 → 4 na v1.9.0). REVOGADO na v1.9.1:
# misturava unidades (teto por NÍVEL, cota por BUCKET) — um bucket com menos
# níveis (ex. `medianas`, 2 níveis sob a opção C) tinha metade do teto
# AGREGADO de um bucket de 4 níveis, e por isso nunca fechava a cota (medido:
# 35/23/26 de 40 nos 3 filmes, sempre `medianas`). Substituído por
# ORCAMENTO_PAGINAS_POR_BUCKET (abaixo). Mantida como default de
# `raspar_nivel`/`coletar_superset` para uso direto/testes de unidade — a
# v1.9.1 e sua produção não a usam mais (pipeline.py passa um orçamento POR
# NÍVEL calculado via `alocacao.orcamento_paginas`).
TETO_PAGINAS = 4
# Piso de páginas por nível — SEGURO DE REVERSIBILIDADE DA FRONTEIRA (§2.2).
# v1.9.1: piso da alocação de PÁGINAS por bucket (`orcamento_paginas_bucket`)
# — garante que todo nível com material no histograma receba orçamento >= 1,
# mesmo que a alocação de REVIEWS daquele nível seja zero.
# v1.9.2: deixou de ter um segundo uso em `raspar_nivel` (gating da parada
# por ALVO, removida — ver changelog v1.9.2). A reversibilidade continua
# garantida, só que por este único caminho agora.
PISO_PAGINAS_POR_NIVEL = 1

# Orçamento de páginas POR BUCKET (v1.9.1, §3[B]) — substitui TETO_PAGINAS
# como o mecanismo real de parada em produção. `16 = 4 × 4`: o mesmo teto
# AGREGADO que `negativas`/`positivas` (4 níveis cada, sob a opção C) já
# tinham na v1.9.0 (4 páginas/nível × 4 níveis). O orçamento não SOBE para
# esses dois — ele EQUALIZA o que `medianas` (2 níveis) tinha pela metade (8).
# Distribuído entre os níveis do bucket proporcional ao histograma, reusando
# `alocar_bucket` (a mesma função da alocação de reviews) — não é uma segunda
# fórmula de distribuição.
ORCAMENTO_PAGINAS_POR_BUCKET = 16
# Teto de EXTENSÃO por bucket (v1.9.4, §3[B]) — o orçamento MÁXIMO que um
# bucket pode alcançar somando a base às páginas extras concedidas por
# déficit. `24 = 16 + 8`, ou seja +50% sobre a base.
#
# Não é um novo orçamento: é um TETO DE CUSTO para a extensão. Um bucket que
# fecha a meta com folga dentro da base continua parando em 16, exatamente
# como antes da v1.9.4 — a extensão nunca dispara para ele, e o custo dos
# filmes que já fechavam a cota é ZERO. Só o bucket que fecha a base abaixo da
# meta chega perto de 24.
#
# Por que 24 e não "até fechar": sem teto, a extensão vira paginação sem
# limite num bucket cujo rendimento é estruturalmente baixo — exatamente o
# caso que a diagnose descreve (rendimento 6,9%-10% em `wicked-2024`), onde
# fechar 40 exigiria dezenas de páginas. O teto é o que mantém o custo de um
# lote previsível, e é também o que garante que ALGUNS buckets sigam abaixo
# de 40 — resíduo esperado, absorvido pelo piso escalonado (§3[C3]), não
# falha da extensão (§3[B], "Correção e declaração são CAMADAS").
TETO_EXTENSAO_PAGINAS = 24
# Teto de SEGURANÇA por nível dentro do orçamento do bucket (v1.9.1). Sem
# ele, um bucket de 2 níveis muito desbalanceado no histograma (ex.:
# `medianas` de `cidade-de-deus`, onde 3,0★ tem 85% do bucket) daria a esse
# nível sozinho quase o orçamento inteiro. O excedente cortado é
# redistribuído para os outros níveis do MESMO bucket reusando
# `redistribuir_deficit` (§3[C1]) — não um mecanismo novo, o mesmo já usado
# para o déficit de reviews, com o teto como "disponibilidade".
TETO_SEGURANCA_PAGINAS_NIVEL = 10
# Folga sobre a cota alocada, usada SÓ para o orçamento do completamento [C']
# desde a v1.9.2 (não decide mais quando parar de paginar — ver
# RESERVA_PROFUNDIDADE e o changelog v1.9.2). A contagem é OTIMISTA por
# construção: usa o texto VISÍVEL, e parte do que ela aprova cai depois no
# completamento ou na re-checagem de spoiler.
FOLGA_ALVO_COLETA = 1.25

# Fração do orçamento de páginas de um NÍVEL reservada para posicionamento
# PROFUNDO (v1.9.2, §3[B]) — o resto (1 - RESERVA_PROFUNDIDADE) fica no bloco
# RASO, consecutivo, como sempre. Motivação: sob `by/added`, páginas
# consecutivas amostram sistematicamente o material mais RECENTE (medido na
# v1.9.0: 79-100% da amostra numa janela de ~7 semanas). Reservar uma fração
# do orçamento para posições em progressão geométrica além do bloco raso
# alarga a cobertura temporal sem gastar requisição extra — mesmo orçamento,
# posições diferentes (ver `alocacao.dividir_raso_profundo`).
# 0,25 é o ponto de partida: grande o bastante para alcançar profundidade
# real com poucos termos geométricos (2,4,8,16,…), pequeno o bastante para
# não sacrificar a densidade do bloco raso. Não há evidência empírica prévia
# que o calibre — mesma política dos limiares do piso escalonado (§3[C3]).
RESERVA_PROFUNDIDADE = 0.25

# --- Âncora de profundidade (v1.9.5, §3[B]) --------------------------------
# ONDE as páginas da reserva profunda caem. `RESERVA_PROFUNDIDADE` (acima)
# decide QUANTAS e não muda nesta versão.
#
# O defeito que isto corrige, medido: a progressão geométrica da v1.9.2
# partia do FIM DO BLOCO RASO (`n_raso+2, +4, +8, +16`), o que com n_raso≈12
# punha as posições "profundas" em 14-28 de níveis que vão a ~256. O bloco
# comprava mediana de 3 DIAS sobre o raso (26 de 34 filmes abaixo de 7 dias)
# — profundo em POSIÇÃO DE PÁGINA, raso em TEMPO.
#
# As frações são da PROFUNDIDADE REAL do nível. 0,95 em vez de 1,0
# deliberadamente: a profundidade estimada por proxy do histograma erra, e
# mirar no último ponto exato converteria todo erro para cima numa página
# vazia. 5% de folga é barato e evita a maior parte desse desperdício.
FRACOES_PROFUNDIDADE: tuple[float, ...] = (0.25, 0.50, 0.75, 0.95)

# Escada da sondagem (§3[B]): degraus geométricos ×4. Filme popular responde
# nos quatro (4 requisições, profundidade = teto de plataforma, zero
# refinamento); filme obscuro cai cedo e o refinamento binário resolve o
# resto. Custo máximo = len(SONDA_ESCADA) + SONDA_MAX_REFINAMENTO.
SONDA_ESCADA: tuple[int, ...] = (4, 16, 64, 256)
# Passos de refinamento binário depois da escada. 3 passos reduzem o
# intervalo de incerteza a ~1/8 dele — precisão de sobra para ancorar
# frações, e um teto de custo que a coleta de um lote pode planejar.
SONDA_MAX_REFINAMENTO = 3

# Teto de paginação do SITE para listagem populosa. Medido na v1.9.2 (§3[B]):
# 3 filmes de volumes muito diferentes (120 mil a 1,2M de notas) bateram
# exatamente no mesmo ponto, enquanto `the-room-1993` (890 notas) esgotou
# organicamente em 4 páginas. Aqui ele é o TETO da profundidade estimada — a
# sondagem nunca reporta mais que isto.
TETO_PLATAFORMA_PAGINAS = 256

# --- Ordenação da listagem: PARÂMETRO DE AMOSTRAGEM (§2.3, v1.9.0) ---
# Só as primeiras N páginas de cada nível são lidas, então a ordenação decide
# QUAIS reviews entram na amostra. Medido ao vivo em `cure`/4★ (datas das 6
# primeiras reviews de cada uma):
#   by/added          2026-08-07 … 2026-08-06   estritamente DECRESCENTE
#   by/added-earliest 2012-11-10 … 2014-03-16   estritamente CRESCENTE
#   by/activity       2023, 2020, 2024, 2022, 2021, 2025 — SEM ordem temporal
# A terceira é a prova de que `by/activity` ordena por ENGAJAMENTO (curtidas,
# comentários), não por tempo — e engajamento enviesa para review longa e
# promovida. Default trocado para a cronológica mais recente.
# `by/added-earliest`, embora igualmente cronológica, concentraria a amostra
# na janela de lançamento (coorte de festival / primeiros adeptos).
ORDENACOES: dict[str, str] = {
    "mais_recentes": "by/added",           # Newest First
    "mais_antigas": "by/added-earliest",   # Earliest First
    "atividade": "by/activity",            # Review Activity (engajamento)
}
ORDENACAO_DEFAULT = "mais_recentes"
ORDENACAO = ORDENACOES[ORDENACAO_DEFAULT]  # segmento de URL em vigor

# --- Passada seletiva sob `by/added-earliest` (§2.3, v1.9.6) ---------------
# A v1.9.5 mediu que cobertura temporal NÃO é alcançável por posição de
# página: a mediana do catálogo precisa de 1783 páginas para cobrir um ano
# contra um teto de plataforma de 256. O parâmetro que a controla é a
# ORDENAÇÃO — e `by/added-earliest` devolve a listagem crescente desde 2012.
ORDENACAO_PASSADA = ORDENACOES["mais_antigas"]
# Limiar de `dias_por_100_paginas` (§3[B']) abaixo do qual um filme RECEBE a
# passada. Acima dele, as 256 páginas expostas sob `by/added` já cobrem mais
# de um ano e a passada compraria cobertura que já existe — `friday-the-13th-
# 2009` (163,6) sequer sai da página ~14, enquanto `avengers-endgame` (0,8)
# não alcança nada além de dias.
# ARBITRÁRIO na mesma acepção dos limiares do piso escalonado (§3[C3]): a
# ordem de grandeza é defensável (é o corte que responde "as 256 páginas que
# existem cobrem pelo menos um ano?"), o número exato não.
LIMIAR_PASSADA_ANTIGA = 20.0
# Orçamento de páginas POR BUCKET da passada — uma FATIA do orçamento base
# (16, `ORCAMENTO_PAGINAS_POR_BUCKET`), não um segundo orçamento cheio: a
# passada compra cobertura temporal, não cota de análise. ~18 páginas por
# filme contra as 48 da coleta base.
ORCAMENTO_PAGINAS_PASSADA = 6

# Versão do COLETOR, gravada em meta.json do bruto (§3[B']). Distinta de
# SPEC_VERSION: só sobe quando muda o que é RASPADO ou PERSISTIDO, para que
# um bruto antigo diga sob qual coletor foi obtido.
#
# v1.9.6: sobe pela primeira vez desde a v1.9.0, porque `reviews.jsonl` ganhou
# um campo (`ordenacao_origem`, §3[B']) — o gatilho que o parágrafo acima
# descreve. REGISTRO HONESTO: ela deveria ter subido antes (a v1.9.2 e a
# v1.9.4/v1.9.5 acrescentaram campos ao meta.json e ficou em "1.9.0"), e a
# passada desta sessão rodou com o processo que já tinha importado o valor
# antigo — as 12 entradas de `passadas` gravadas em 2026-08-09 dizem "1.9.0"
# apesar de terem sido feitas pelo coletor 1.9.6. Não reescrito à mão: um
# carimbo de versão corrigido depois do fato não é evidência de nada.
VERSAO_COLETOR = "1.9.6"

# Raiz do superset persistido (§3[B']). Versionada no git, ao contrário de
# `resultado/cache/`: o cache é HTML reconstruível e volumoso; o bruto é o
# INSUMO DE ANÁLISE — pequeno, textual, e a coisa cuja recoleta a v1.9.0
# existe para evitar.
DADOS_BRUTO_DIR = "dados/bruto"

# --- LLM (§D / B2) — provider-agnostic (v1.1.1) ---
# As instruções fixas do prompt (SYSTEM_PROMPT em synthesize.py) são
# byte-idênticas entre providers; só o transporte muda.
PROVIDER_ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}
PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    # gemini-2.5-flash (não flash-lite) — ratificado em v1.1.2 com evidência
    # empírica: a comparação de modelos (resultado/comparacao/COMPARACAO.md)
    # documentou 3 violações de instrução do flash-lite rodando o MESMO
    # prompt §D sobre o MESMO corpus — (1) bucket "negativas" inteiro em
    # inglês, violando a regra de saída sempre em pt-BR; (2)-(3) generalização
    # indevida do bucket para "a maioria dos críticos"/o filme como um todo,
    # o próprio erro de enquadramento que motivou o preâmbulo de papel da
    # v1.1.2. O 2.5-flash, no mesmo teste, não repetiu nenhuma das três.
    "gemini": "gemini-2.5-flash",
    # deepseek-v4-flash — aposta seguinte após o encerramento dos
    # experimentos de LLM local (ver experimentos-ollama-arquivado/): SDK
    # compatível com o da OpenAI, ~$0,14/M tokens de entrada (cache miss;
    # ~$0,0028/M com prefixo cacheado) e ~$0,28/M de saída, sem teto diário
    # de requisições — ataca diretamente o gargalo do free tier do Gemini
    # (20 req/dia) que inviabilizava construir catálogo. ATENÇÃO: os aliases
    # antigos `deepseek-chat`/`deepseek-reasoner` foram descontinuados em
    # 24/07/2026; não existe mais "DeepSeek-V3" na API — os nomes atuais são
    # `deepseek-v4-flash` e `deepseek-v4-pro`.
    "deepseek": "deepseek-v4-flash",
}

# Provider DEFAULT de produção (v1.8.0 — TROCA de anthropic para deepseek).
# Decisão registrada em VALIDACAO_DEEPSEEK.md, após smoke test (`cure`) +
# validação em 3 filmes do catálogo, todos via --reuse-synthesis (mesmos
# dados de síntese, só o narrador/editor mudam de provider):
#   - TESTE DECISIVO (o ponto em que o modelo local Qwen3.5-9B falhava —
#     colapso da narrativa num resumo de filme só, ou omissão do movimento
#     de contraste): PASSOU nos 3/3 filmes — os três movimentos completos,
#     rótulos de peso ancorados, marcadores de perspectiva presentes;
#   - 23 das 24 checagens de honestidade (3 filmes × 8 flags) vieram limpas
#     — a única exceção foi `perspectiva_nao_marcada` num filme;
#   - custo ~US$0,0005/filme (narrador+editor), com 96-99% de cache hit no
#     prompt do narrador, e SEM teto diário de requisições — o gargalo que
#     inviabilizava o Gemini free tier para construir catálogo.
# `anthropic` e `gemini` continuam plenamente selecionáveis via --provider;
# a troca é só do que o CLI assume quando a flag é omitida.
DEFAULT_PROVIDER = "deepseek"

# --- Provider por ESTÁGIO (v1.9.8, §3[D]) ---
# O provider deixa de ser global. A decisão, e o racional de cada metade:
#
# `classificacao` FICA em DeepSeek. Ela está calibrada e auditada contra um
# gabarito humano de 100 reviews, com precisão e recall medidos por eixo
# (CLASSIFICACAO_CONSOLIDADO.md). Trocar o modelo ali invalida oito sessões
# de medição — e o faria em SILÊNCIO, porque `taxonomia_id` hasheia prompt +
# eixos, não o modelo. É também onde capacidade de modelo rende menos:
# tarefa estruturada, alto volume, saída JSON curta.
#
# `narrativa` vai para Gemini. É o oposto em todos os eixos: uma chamada por
# filme (volume irrelevante), prosa longa, nada calibrado a invalidar — a
# qualidade é julgada por leitura humana. O risco histórico do Gemini
# (auditoria antiga o flagrou INFLANDO contagens) fica neutralizado POR
# CONSTRUÇÃO, não por confiança: sob o briefing determinístico (§D2) o
# narrador não computa número nenhum, e a checagem de conjunto de tokens
# numéricos (§E2) reprova qualquer número inventado.
#
# `--provider` continua existindo e, quando passado, força TODOS os estágios.
PROVIDER_POR_ESTAGIO = {
    "classificacao": "deepseek",
    "narrativa": "gemini",
}

# Modelo default de cada estágio. O da narrativa é decidido por medição na
# sessão de comparação (Entrega 3/4); até lá, o flash mais recente é o
# ponto de partida declarado.
MODELO_POR_ESTAGIO = {
    "classificacao": "deepseek-v4-flash",
    "narrativa": "gemini-flash-latest",
}

# mantido por compatibilidade (era o único provider na v1.1.0); agora segue
# o provider DEFAULT de produção (v1.8.0), não mais fixo em "anthropic".
MODEL_DEFAULT = PROVIDER_DEFAULT_MODELS[DEFAULT_PROVIDER]
# Nota histórica: 2000 causava JSON truncado no Gemini porque, por padrão,
# gemini-2.5-flash gasta tokens de "thinking" do MESMO orçamento de
# max_output_tokens antes do JSON — consumo que escala com o tamanho do
# prompt e não tem teto seguro previsível (medido ao vivo: 7679/8000 tokens
# só de thinking no bucket "negativas", 50 reviews). A causa raiz foi
# corrigida desligando thinking no adaptador Gemini (thinking_budget=0, ver
# gemini_client_call) — com thinking off, 6 temas de JSON usam ~700 tokens no
# pior caso medido; 3000 dá margem folgada para ambos os providers.
LLM_MAX_TOKENS = 3000
MAX_TEMAS = 6                # §D.3

# --- Configuração de produção da PROSA (narrador §D2 + editor §E2) — v1.6.0 ---
# A síntese por bucket (§D) NÃO usa estes valores: continua com
# LLM_MAX_TOKENS=3000 e thinking desligado, porque é extração estruturada, não
# escrita — e nada no diagnóstico indicou problema lá.
#
# Para as etapas de PROSA, a v1.6.0 adota thinking LIGADO com orçamento FIXO,
# revertendo o `thinking_budget=0` que valia desde a v1.2.x. Base empírica
# (DIAGNOSTICO_FLUENCIA_V2.md, matriz B):
#   - thinking DINÂMICO (sem budget fixo) sob teto de 8000 consumiu até 7676
#     tokens — 96% do orçamento — e truncou 1 chamada em CADA célula testada
#     (finish_reason=MAX_TOKENS, JSON inválido, correção descartada em
#     silêncio). Foi esse modo de falha que originalmente justificou desligar
#     thinking na v1.2.x;
#   - com budget FIXO em 4096 e teto de 16000, as 4/4 chamadas terminaram em
#     STOP, nenhuma truncou, e o raciocínio ficou entre 2430 e 4095 tokens.
# Ou seja: o problema nunca foi "thinking", foi thinking SEM TETO competindo
# com a resposta pelo mesmo orçamento. Fixar o budget resolve a causa raiz e
# devolve o planejamento que a v1.2.x teve de sacrificar.
PROSA_THINKING_BUDGET = 4096
PROSA_MAX_TOKENS = 16000

# Teto de TENTATIVAS do editor [E2] (v1.7.3). Até a v1.7.2, era 1 chamada +
# 1 retentativa (2 no total) — restritivo demais para uma etapa cujo
# descarte já é fail-safe (a bruta do narrador sempre prevalece). Defeito
# real: na regeneração da v1.7.1, a edição foi DESCARTADA em 2 dos 3 filmes
# (`cure` — número alterado; `cidade-de-deus` — regressão de
# `perspectiva_nao_marcada`), publicando a bruta nos dois, enquanto a MESMA
# combinação de código+dados na v1.7.0 tinha aceitado os 3 — nada mudou no
# código nesse sentido, é VARIÂNCIA do modelo entre chamadas. Subir o teto
# dá mais chances de a variância favorecer sem custo de honestidade (o
# fail-safe de descarte continua intacto se todas as tentativas falharem).
# `EDITOR_MAX_TENTATIVAS` conta RETENTATIVAS (não a chamada inicial): total
# de chamadas no pior caso = 1 (chamada inicial) + `EDITOR_MAX_TENTATIVAS`.
EDITOR_MAX_TENTATIVAS = 3

# Limiar de EDIÇÃO NULA do editor [E2] (v1.7.4): similaridade (0-1,
# `difflib.SequenceMatcher.ratio` sobre os textos normalizados por espaço
# em branco) entre `narrativa_bruta` e o texto editado a partir da qual a
# edição é tratada como "não editou de verdade" — falha de tentativa, não
# sucesso. Buraco identificado: até a v1.7.3, nenhuma checagem verificava
# que a edição FEZ algo — só que não QUEBROU nada. Um editor que devolva a
# entrada praticamente intacta passa em protegidos, números e honestidade
# (é o mesmo texto) e era marcado como "aplicada".
# 0.97 é DELIBERADAMENTE conservador: só pega devolução literal ou
# trivialmente alterada (pontuação, um sinônimo isolado); uma edição
# legítima que preserve bastante vocabulário do rótulo/atribuição
# protegidos (que É esperado — eles são intocáveis por definição) não deve
# cair aqui. Calibrável: se a telemetria (`edicao_flags.similaridade`,
# persistida SEMPRE, em todo resultado) mostrar edições legítimas perto
# do limiar, ajustar aqui é a mudança certa — não no código do editor.
EDITOR_LIMIAR_EDICAO_NULA = 0.97

# EDITOR [E2] LIGADO por padrão (v1.8.1 — REATIVADO; era False na v1.8.0).
# Histórico: a v1.8.0 desligou o editor por precaução depois de um defeito
# real em `the-invite-2026` — ACEITO por todas as checagens mecânicas então
# existentes (protegidos presentes, números idênticos, honestidade sem
# regressão) e, mesmo assim, o editor reordenou o MOVIMENTO 1 e ACRESCENTOU
# um parágrafo de opinião inteiro sem origem no texto recebido (CONTEÚDO
# INVENTADO — nenhuma checagem até a v1.7.4 detectava ADIÇÃO, só PERDA). A
# MESMA v1.8.0 já implementou a correção: a checagem de CONTEÚDO ADICIONADO
# + ORDEM DOS MOVIMENTOS logo abaixo, que roda ANTES das demais em
# `editar_narrativa` (`synthesize.py`).
#
# Reativação (v1.8.1) baseada em validação DEPOIS da correção
# (VALIDACAO_EDITOR_V18.md, 3 filmes reais, --com-editor): os 3/3 foram
# aceitos com ganho de ritmo sobre a bruta; a checagem nova DISPAROU DE
# VERDADE em produção uma vez (`cidade-de-deus`, 1ª tentativa, motivo
# "conteudo_adicionado") e o modelo se AUTOCORRIGIU na retentativa — prova
# de que o fail-safe funciona sobre dados reais, não só em teste sintético;
# e os limiares calibrados ficaram bem separados do ruído normal de uma
# boa edição de ritmo (1-3 frases "sem origem" nos casos legítimos,
# EDITOR_MIN_FRASES_SEM_ORIGEM=4, contra as 15 do defeito original). O
# defeito de `the-invite-2026` não se repetiu na validação, mas está
# coberto por um teste de regressão determinístico
# (`tests/test_editor.py`) que injeta o texto literal do defeito e
# confirma DESCARTE — a garantia não depende de o defeito nunca mais
# ocorrer, depende de ele ser pego quando ocorrer.
#
# `--no-edicao` (CLI) continua disponível para desligar pontualmente
# (debug, economia de 1 chamada), independente deste default.
EDITOR_ATIVO = True

# --- Checagem de CONTEÚDO ADICIONADO pelo editor [E2] (v1.8.0, Tarefa 3;
# métrica corrigida na v1.8.2) ---
# Motivação: ver comentário de `EDITOR_ATIVO` acima. Estratégia: dividir bruto
# e editado em frases (`_dividir_frases`, já usado pela telemetria de
# fluência) e, para cada frase do EDITADO, calcular a MELHOR COBERTURA DE
# PALAVRAS (v1.8.2 — multiset, insensível a ORDEM; ver
# `_melhor_cobertura_palavras` em synthesize.py) contra a MELHOR frase
# individual do BRUTO — uma frase sem nenhuma cobertura razoável em
# qualquer frase do texto recebido é candidata a invenção.
#
# v1.8.2 — CORREÇÃO DE FALSO POSITIVO (DIAGNOSTICO_CONTEUDO_ADICIONADO.md).
# A métrica original da v1.8.0 (`difflib.SequenceMatcher.ratio`, char-level,
# SENSÍVEL A ORDEM, frase inteira contra frase inteira) reprovava edição
# LEGÍTIMA sempre que o editor (a) quebrava uma frase longa do bruto em duas
# menores — cada metade, sozinha, tem `ratio()` baixo contra a frase-fonte
# inteira só por diferença de COMPRIMENTO — ou (b) reordenava palavras
# dentro da frase (mesmo conteúdo, ordem diferente). Foi o que descartou o
# `cure` na v1.8.1 após 3 reprovações seguidas por este motivo. A correção
# troca para cobertura de palavras (multiset), restrita à MELHOR frase
# INDIVIDUAL do bruto (comparar contra o bruto INTEIRO de uma vez, medido ao
# vivo, infla o placar de frases genuinamente inventadas — elas pegam
# carona em vocabulário genérico de crítica de cinema espalhado por frases
# distantes do bruto).
#
# Calibração EMPÍRICA (não só teórica) — dados completos em
# DIAGNOSTICO_CONTEUDO_ADICIONADO.md, VALIDACAO_DEEPSEEK.md e
# VALIDACAO_EDITOR_V18.md:
#   - 6 frases legítimas marcadas nas duas validações (quebras de frase +
#     1 caso de reordenação) — cobertura entre 0,765 e 1,000 com a métrica
#     nova (a MESMA reordenação que zerava a métrica antiga bate 1,000
#     aqui: "conforme avança, o ritmo desacelera" ~ bruto "ritmo que
#     desacelera conforme avança", mesmas palavras);
#   - as frases do parágrafo REALMENTE inventado do `the-invite-2026`
#     (texto literal da v1.8.0/v1.8.1) — cobertura entre 0,222 e 0,500.
# Folga de 0,265 entre os dois grupos (0,765 legítimo mínimo vs 0,500
# inventado máximo) — `EDITOR_LIMIAR_FRASE_SEM_ORIGEM = 0.6` fica bem no
# meio, com margem folgada dos dois lados.
# `EDITOR_MIN_FRASES_SEM_ORIGEM`/`EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO`
# mantidos como estavam (v1.8.0) — a Tarefa 1 da v1.8.2 corrige só a
# métrica POR FRASE, não a política de agregação:
#   - abaixo de EDITOR_LIMIAR_FRASE_SEM_ORIGEM: a frase é candidata;
#   - EDITOR_MIN_FRASES_SEM_ORIGEM+ candidatas, OU candidatas somando mais de
#     EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO das palavras do texto editado
#     → falha "conteudo_adicionado" (retentativa, depois descarte).
# CALIBRÁVEL: se a telemetria `edicao_flags.frases_sem_origem`/
# `similaridade_minima_por_frase`/`tentativas_detalhe` (persistida SEMPRE)
# mostrar, com mais filmes, edições legítimas perto destes números, ajustar
# aqui — não no código do editor nem na lógica da checagem.
EDITOR_LIMIAR_FRASE_SEM_ORIGEM = 0.6
EDITOR_MIN_FRASES_SEM_ORIGEM = 4
EDITOR_LIMIAR_PALAVRAS_SEM_ORIGEM_FRACAO = 0.35

# Checagem de ORDEM DOS MOVIMENTOS (v1.8.0, Tarefa 3.2): o texto bruto do
# narrador sempre abre com o MOVIMENTO 1 (a apresentação do filme, quando há
# ficha técnica) — é a própria estrutura exigida pelo prompt (§D2). O caso
# real de `the-invite-2026` moveu esse movimento para o meio do texto. A
# checagem compara a PRIMEIRA frase do editado contra as 3 PRIMEIRAS frases
# do bruto (não só a primeira — o editor pode legitimamente fundir/quebrar
# frases de abertura sem mudar a ordem dos movimentos); se a melhor
# similaridade entre elas for menor que este limiar, a abertura mudou de
# lugar → falha "ordem_alterada". Mesma calibração propositalmente
# permissiva do limiar acima — 0,5 aceita reescrita de abertura considerável,
# só pega deslocamento real.
EDITOR_LIMIAR_ORDEM_MOVIMENTO_1 = 0.5

# Timeout de rede das chamadas LLM, em MILISSEGUNDOS (v1.6.0). Sem timeout
# explícito o SDK do Gemini bloqueia indefinidamente: durante a regeneração
# desta versão um processo ficou 67 minutos parado (0% CPU, dormindo num
# socket), sem voltar nem falhar. 180s cobre com folga o pior caso medido
# (~110s numa chamada com thinking) e converte trava permanente em erro.
LLM_TIMEOUT_MS = 180_000


def nota_para_url(n: float) -> str:
    """Formato decimal da nota na URL (§2.1): 3.0 -> '3', 3.5 -> '3.5'."""
    return str(int(n)) if float(n).is_integer() else str(n)


def bucket_de_nota(n: float) -> str | None:
    """Alias histórico de `buckets.bucket_de_nivel` (v1.9.0).

    Mantido para não churnar os call sites; a implementação é a função pura
    do módulo de fronteiras, então não há um segundo mapeamento a divergir.
    """
    return bucket_de_nivel(n)


# Ordem de VARREDURA dos níveis na coleta: a escala inteira, crescente. Até a
# v1.8.2 era derivada de `BUCKETS` (e portanto reordenada pelas fronteiras);
# agora vem de `NIVEIS`, porque a coleta não sabe nada de bucket — varre a
# escala do Letterboxd (v1.9.0, §3).
NIVEIS_ORDENADOS = list(NIVEIS)
