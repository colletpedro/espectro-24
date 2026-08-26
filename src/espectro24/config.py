"""Parâmetros congelados da spec (SPEC.md §2) e constantes técnicas (§2.1).

Nenhum valor aqui deve divergir da SPEC.md sem bump de versão.
"""
from __future__ import annotations

# v1.9.11: estava parada em "1.9.0" desde então, enquanto a SPEC.md
# avançava até a v1.9.11 — todo `resultado/*.json` gerado de v1.9.1 a
# v1.9.10 carimbou a versão errada. Achado ao rodar o pipeline de ponta a
# ponta pela primeira vez desde a v1.8.2 (a comparação com o publicado
# mostrou "1.6.0 → 1.9.0" quando deveria ser "1.6.0 → 1.9.11"). Os JSONs
# já publicados NÃO foram reescritos: carimbo corrigido depois do fato não
# é evidência de nada — mesma política de `VERSAO_COLETOR` abaixo.
SPEC_VERSION = "1.9.23"

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
    # v1.9.14 (§D3): rotulagem de tema por eixo. Fica em DeepSeek pelo mesmo
    # critério que manteve a classificação lá — tarefa estruturada, saída
    # JSON curta, escolha dentro de lista fechada: o lugar onde capacidade de
    # modelo rende menos. Não é a mesma etapa que a classificação (esta não
    # entra no `taxonomia_id`, e não é calibrada contra gabarito), mas é a
    # mesma NATUREZA de tarefa.
    "rotulagem": "deepseek",
    # [v1.9.21] §3[V] veredito. Fica em Gemini pelo mesmo critério que levou a
    # narrativa para lá: uma chamada por filme (volume irrelevante), prosa, e
    # nada calibrado a invalidar — a qualidade é julgada por leitura humana.
    # O risco histórico do Gemini (inflar contagem) é neutralizado por
    # CONSTRUÇÃO e não por confiança: a serialização do briefing do veredito
    # não contém nenhum algarismo, então não há número para inflar.
    "veredito": "gemini",
}

# Modelo default de cada estágio.
#
# `narrativa` = `gemini-3.7-flash`, FIXADO por decisão do dono do projeto
# (v1.9.10) — versão explícita, nunca o alias `gemini-flash-latest` (alvo
# móvel: comparação não reproduzível e preço não ancorável, ver
# `scripts/comparar_narrador.py`). Base da decisão — 4 candidatos × 3
# filmes, briefing determinístico (v1.9.8) + correções de prosa (v1.9.9) +
# cobertura estrutural/parágrafo por grupo (v1.9.10),
# `resultado/comparacao-narrador/RELATORIO_V199.md`:
#
#   candidato            flags totais (3 filmes)   custo/filme   latência
#   gemini-3.7-flash               1                 US$0,0037     ~14s
#   gemini-3.1-pro-preview          2                 US$0,0365     ~22s
#   gemini-2.5-flash                4                 US$0,0061     ~17s
#   deepseek-baseline               10                US$0,0006      ~7s
#
# A escolha é por CONFORMIDADE, não por custo. A única flag do 3.7-flash
# nos 3 filmes é colisão de parágrafo (defeito de FORMA, já coberto por
# `qualidade.grupos_sem_paragrafo_proprio`); as dos concorrentes incluem
# defeito de CONTEÚDO — rótulo de peso ausente, vocabulário do peso
# misturando "notas" com "reviews"/"público" — que é a invariante central
# do produto (§0, §D2). A diferença de custo entre os quatro (~1 centavo
# por filme no pior caso) não pesou na decisão.
#
# RESSALVA REGISTRADA: o 3.7-flash é o mais conciso dos quatro candidatos, e
# o movimento 2 de `cure` segue com uma única frase mesmo com o material do
# briefing completo (a Entrega 3 da v1.9.9 já tinha descartado orçamento e
# prompt como causa — é escolha de concisão do modelo). Não muda a decisão;
# é o primeiro sintoma a observar se o texto parecer raso quando o catálogo
# crescer.
#
# CONFIRMADO na v1.9.16, ao publicar os 32 filmes restantes: 15 de 35
# filmes do catálogo (43%) carregam `n_flags >= 1` em `verificacao_narrativa`
# — quase todos a MESMA colisão de forma (movimento 1 e 2 no mesmo parágrafo,
# ou grupo sem parágrafo próprio), nunca defeito de CONTEÚDO. A taxa de 43%
# é bem acima do 1/3 medido na comparação de modelos que decidiu o 3.7-flash
# — a amostra de 3 filmes não previu a taxa real. O fallback de
# `narrativa_selecao` (`menor_severidade`, escolher o candidato com menos
# flags quando os 3 são flagrados) absorveu todos os casos — nenhuma
# narrativa saiu sem candidato, nenhum flag de CONTEÚDO apareceu. Não muda a
# decisão de modelo (é o sintoma já previsto, não um defeito novo), mas eleva
# a prioridade de investigar: o próximo passo natural seria medir se ajustar
# o orçamento do briefing ou o prompt do movimento 2 reduz a taxa — ainda não
# feito, fora do escopo desta sessão (só publicação, não tocou o narrador).
# [v1.9.21] `veredito` = `gemini-3.7-flash`, DECIDIDO PELO A/B (decisão do
# dono do projeto, lendo os 35 textos de cada braço). O default entrou na
# sessão como `gemini-3.1-pro-preview` — o único tier `pro` disponível — e
# saiu trocado pela MEDIÇÃO, não por argumento:
#
#   braço                     origem        flags   retries  latência  jaccard
#   gemini-3.7-flash          35/35 llm       0        0        454s    0,0583
#   gemini-3.1-pro-preview    34/35 llm       1        2       1564s    0,0526
#
# O pro perde `cure` para o `template_fallback` (escreveu "a ambientação
# criada pela direção", e `direcao_imagem` não está no briefing daquele
# filme) — regressão de produto concreta: aquele filme volta a exibir a
# frase genérica. Em repetição os dois empatam tecnicamente; em prosa o pro
# varia um pouco mais a construção sintática, e é a ÚNICA dimensão em que
# ganha. Flash é 3,4x mais rápido e ~10x mais barato por token.
#
# **O achado que importa mais que a escolha:** a diferença entre os dois
# modelos é MUITO menor que a diferença que o briefing fez — os dois saíram
# de 14 textos distintos para 35. O trabalho estava no briefing, não no
# modelo, e por isso esta linha é reversível sem consequência estrutural.
#
# INVENTÁRIO CONSULTADO NA
# API (não de memória, 2026-08-25): é o único tier `pro` de texto disponível
# na chave (`version: 3.1-pro-preview-01-2026`) e não existe tier acima dele.
# `gemini-pro-latest` existe e é REJEITADO por política (v1.9.10): alias é
# alvo móvel — comparação não reproduzível e preço não ancorável.
#
# TENSÃO REGISTRADA, e resolvida por medição em vez de por argumento: o flash
# mais recente (`gemini-3.7-flash`, `3.7-flash-08-2026`) é SETE MESES mais
# novo que o único pro disponível, e a comparação da v1.9.10 mediu o 3.1-pro
# PIOR que o 3.7-flash no narrador (2 flags contra 1, ~10x o custo) — em
# amostra de 3 filmes, evidência fraca, mas é a que existe. O A/B da v1.9.21
# roda o critério de aceite INTEIRO nos dois braços, com briefing, prompt,
# best-of-3, validadores e ordem de filmes idênticos: a única variável é o
# modelo. Conformidade NÃO decide sozinha — um modelo pode passar limpo em
# todas as validações e ainda produzir 35 vereditos corretos, insossos e
# intercambiáveis, que é a falha exata que esta versão existe para evitar.
MODELO_POR_ESTAGIO = {
    "classificacao": "deepseek-v4-flash",
    "narrativa": "gemini-3.7-flash",
    "rotulagem": "deepseek-v4-flash",
    "veredito": "gemini-3.7-flash",
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

# --- Margem de LIFT (§2.5, v1.9.14) ---------------------------------------
# Em PONTOS PERCENTUAIS, inteiros: a comparação é feita em `Fraction` contra
# `MARGEM_LIFT_PP/100`, nunca em float (5 dos 35 filmes do catálogo têm o
# melhor lift em exatamente 20,0pp, e `0.2` binário decidiria o estado deles
# por erro de representação — ver `eixos.acima_da_margem`).
#
# 20 é DECISÃO DE PRODUTO entre pureza de lista e cobertura, medida por nulo
# de permutação (2000 rodadas): a 15pp, 63% dos pares que cruzam a margem
# cruzariam por acaso; a 20pp, 41%; a 25pp, 29% — mas só 9 de 35 filmes
# teriam algum contraste. Não existe margem correta; existe esta, escolhida
# com os três números à vista.
MARGEM_LIFT_PP = 20

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

# As constantes `EDITOR_*` (teto de tentativas, limiares de edição nula,
# conteúdo adicionado e ordem de movimento, e o interruptor `EDITOR_ATIVO`)
# viviam aqui de v1.7.3 a v1.9.9. O editor [E2] foi APOSENTADO na v1.9.10
# (ver SPEC.md, "Fechamento do narrador") — as constantes e seus comentários
# originais foram para `experimentos-editor-e2-arquivado/editor.py`, junto
# com o resto do estágio.

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


# --- [v1.9.9] Tiques de prosa do narrador (§D2) ---------------------------
# Achados pela LEITURA HUMANA dos 12 textos da comparação de modelos da
# v1.9.8 — nenhuma verificação mecânica de então os via.
#
# `QUANT_MAX_REPETICOES`: quantas vezes a MESMA construção quantificadora
# pode aparecer numa narrativa. Medido: em `cure`, os 4 modelos escreveram
# "muitos" 8 vezes no mesmo texto. Duas ocorrências é prosa normal; três já
# é tique — o 2 é arbitrário e está declarado como tal.
QUANT_MAX_REPETICOES = 2

# `MAX_PALAVRAS_PARAGRAFO`: teto por parágrafo. Medido: `gemini-3.1-pro`
# entregou 3 de 3 filmes em bloco único, de até 318 palavras, com ZERO
# flags — `formato_invalido` (v1.7.2) checa invólucro, não legibilidade.
MAX_PALAVRAS_PARAGRAFO = 180

# `BEST_OF_N`: narrativas independentes geradas por filme antes da seleção
# POR CÓDIGO (§D2, Entrega 5). 3 é o número da tarefa; o custo é linear.
BEST_OF_N = 3

# [v1.9.13] `MAX_FRASES_MOVIMENTO1`: teto de frases no parágrafo ancorado
# pelo ANO da ficha, PROXY de "movimento 1 e movimento 2 no mesmo
# parágrafo". Medido: `cure` tem 3 frases nesse parágrafo (a terceira é
# claramente movimento 2 — "A experiência do filme é conduzida por um
# ritmo..."); os outros 3 filmes da v1.9.12 têm 2, e nenhum deles dispara.
# Declaradamente imperfeito: um filme cuja premissa genuinamente precise de
# 3 frases seria falso positivo — mesma troca de todo proxy do projeto.
MAX_FRASES_MOVIMENTO1 = 2
