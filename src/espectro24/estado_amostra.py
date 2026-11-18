"""Estado de AMOSTRA de um bucket — a máquina de estados que era implícita.

Cada bucket (negativas · medianas · positivas) tem um estado que é FUNÇÃO
PURA do número de reviews válidas que sobraram da seleção (`n_validas`). Esse
estado decide o que o produto pode dizer sobre o grupo: se há temas, se há
número, se há quantificador verbal, e se o texto leva a marca "amostra
pequena". Até aqui ele vivia espalhado em três codificações recalculadas à
mão em oito lugares (pipeline, collector, briefing, condições, veredito,
scripts), com defaults diferentes para o campo ausente — `condicoes` e
`veredito` assumiam `"completa"` onde o `briefing` recomputava de
`n_validas`. Este módulo é a única fonte.

Os dois eixos, ambos derivados de `n_validas` (limiares em `config`):

    n_validas:      0 ── 3 ──────── 8 ────────── 15 ─────────── alvo (40) ──▶
    estado_piso:    sem_analise │ sem_numero │ sem_quantificador │ completa
    modo:           sem_analise │ reduzido ─────────────────────────│ completo

- `estado_piso` (§3[C3], v1.9.0) governa PERMISSÃO de citação — ver
  `briefing.PERMISSOES_POR_ESTADO`.
- `modo` (v1.1) é o eixo antigo, ainda serializado e lido por `render` e pelo
  frontend (`filme.js`). Não foi removido para não mudar o contrato do JSON
  publicado.
- `amostra_pequena(modo, estado_piso)` é o predicado derivado que decide a
  marca "amostra pequena" nos briefings de condições e de veredito.

Sem imports além de `config`: pode ser usado por qualquer camada (inclusive
as que evitam puxar SDKs, como `briefing`).
"""
from __future__ import annotations

from typing import Literal, Mapping

from .config import COTA_POR_BUCKET, PISO_ESCALONADO, PISO_POR_BUCKET

EstadoPiso = Literal["completa", "sem_quantificador", "sem_numero",
                     "sem_analise"]
Modo = Literal["completo", "reduzido", "sem_analise"]

# Do mais permissivo para o menos — a mesma ordem de `PISO_ESCALONADO`.
ESTADOS_PISO: tuple[str, ...] = tuple(e for _, e in PISO_ESCALONADO)
MODOS: tuple[str, ...] = ("completo", "reduzido", "sem_analise")


def estado_do_piso(n_validas: int) -> str:
    """[v1.9.0, §3[C3]] Piso ESCALONADO — 4 estados a partir do n final.

    Os limiares (3, 8, 15) são **ARBITRÁRIOS** e estão registrados com esse
    rótulo na spec: a ordem de grandeza é defensável pela tabela de precisão
    de §3[C2] (em n=8 o intervalo de 95% já passa de ±34pp, o que torna um
    quantificador verbal indefensável), mas os cortes exatos não.
    """
    for limiar, estado in PISO_ESCALONADO:
        if n_validas >= limiar:
            return estado
    return PISO_ESCALONADO[-1][1]


def modo_do_bucket(n_validas: int, alvo: int = COTA_POR_BUCKET) -> str:
    """`modo` (eixo antigo): sem análise abaixo do piso, completo no alvo."""
    if n_validas < PISO_POR_BUCKET:
        return "sem_analise"
    if n_validas >= alvo:
        return "completo"
    return "reduzido"


def _n_validas(bucket: Mapping) -> int:
    return bucket.get("n_validas", 0) or 0


def estado_piso_do_bucket(bucket: Mapping) -> str:
    """`estado_piso` de um bucket SERIALIZADO, derivado quando ausente.

    O campo é da v1.9.0 e não está em `resultado/*.json` publicado antes
    dela. Um default fixo é o pior fallback possível nos dois sentidos:
    `"sem_analise"` apagaria em silêncio temas bons (medido ao vivo em
    `cure`, 50 reviews com 6 temas indo para "SEM TEMAS"), e `"completa"`
    trataria um bucket de 1 review como amostra cheia. Como o estado é
    FUNÇÃO de `n_validas`, recomputá-lo é exato, não uma estimativa.
    """
    return bucket.get("estado_piso") or estado_do_piso(_n_validas(bucket))


def modo_de_bucket_serializado(bucket: Mapping) -> str:
    """`modo` de um bucket SERIALIZADO, derivado quando ausente (ver acima)."""
    declarado = bucket.get("modo")
    if declarado:
        return declarado
    return modo_do_bucket(_n_validas(bucket),
                          bucket.get("alvo") or COTA_POR_BUCKET)


def amostra_pequena(modo: str, estado_piso: str) -> bool:
    """True quando o texto sobre o grupo deve levar a marca "amostra pequena".

    Qualquer um dos dois eixos basta: abaixo do alvo (`modo="reduzido"`) ou
    abaixo do piso completo (`estado_piso != "completa"`, o que inclui
    `sem_analise`).
    """
    return modo == "reduzido" or estado_piso != "completa"
