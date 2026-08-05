"""Parâmetros congelados da spec (SPEC.md §2) e constantes técnicas (§2.1).

Nenhum valor aqui deve divergir da SPEC.md sem bump de versão.
"""
from __future__ import annotations

SPEC_VERSION = "1.6.0"

BASE = "https://letterboxd.com"

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

# --- Buckets e cotas (§2) ---
# Cada nível de nota (0.5 .. 5) pertence a exatamente um bucket.
BUCKETS: dict[str, list[float]] = {
    "negativas": [0.5, 1.0, 1.5, 2.0, 2.5],
    "medianas": [3.0, 3.5],
    "positivas": [4.0, 4.5, 5.0],
}
# alvo derivado por bucket (5/2/3 níveis × 10)
BUCKET_ALVO = {"negativas": 50, "medianas": 20, "positivas": 30}

COTA_POR_NIVEL = 10          # §2: cota de reviews válidas POR NÍVEL
PISO_POR_BUCKET = 3          # §2: piso mínimo por bucket p/ análise temática
MIN_CHARS = 150              # §2: filtro de comprimento padrão
CASCATA_CHARS = [150, 50, 0] # §2/§C: 150 → 50 → sem filtro (0 = sem filtro)
TETO_PAGINAS = 6             # §2: teto de paginação por nível

ORDENACAO = "by/activity"    # §2

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
    # deepseek-v4-flash (v1.8.0) — provider adicional, NÃO default de
    # produção (ver PROVIDER_CLIENTS em synthesize.py). Aposta seguinte após
    # o encerramento dos experimentos de LLM local (ver
    # experimentos-ollama-arquivado/): SDK compatível com o da OpenAI,
    # ~$0,14/M tokens de entrada (cache miss; ~$0,0028/M com prefixo
    # cacheado) e ~$0,28/M de saída, sem teto diário de requisições — ataca
    # diretamente o gargalo do free tier do Gemini (20 req/dia) que
    # inviabilizava construir catálogo. ATENÇÃO: os aliases antigos
    # `deepseek-chat`/`deepseek-reasoner` foram descontinuados em 24/07/2026;
    # não existe mais "DeepSeek-V3" na API — os nomes atuais são
    # `deepseek-v4-flash` e `deepseek-v4-pro`.
    "deepseek": "deepseek-v4-flash",
}
# mantido por compatibilidade (era o único provider na v1.1.0)
MODEL_DEFAULT = PROVIDER_DEFAULT_MODELS["anthropic"]
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
    for nome, niveis in BUCKETS.items():
        if n in niveis:
            return nome
    return None


NIVEIS_ORDENADOS = [n for niveis in BUCKETS.values() for n in niveis]
