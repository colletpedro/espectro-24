"""Parâmetros congelados da spec (SPEC.md §2) e constantes técnicas (§2.1).

Nenhum valor aqui deve divergir da SPEC.md sem bump de versão.
"""
from __future__ import annotations

SPEC_VERSION = "1.4.0"

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


def nota_para_url(n: float) -> str:
    """Formato decimal da nota na URL (§2.1): 3.0 -> '3', 3.5 -> '3.5'."""
    return str(int(n)) if float(n).is_integer() else str(n)


def bucket_de_nota(n: float) -> str | None:
    for nome, niveis in BUCKETS.items():
        if n in niveis:
            return nome
    return None


NIVEIS_ORDENADOS = [n for niveis in BUCKETS.values() for n in niveis]
