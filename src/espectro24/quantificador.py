"""[v1.9.21] O mapa fração→palavra da v1.2.3, em UM lugar só.

**Por que um módulo para uma tabela de seis linhas.** Este mapa existia DUAS
vezes antes desta versão: o original em `synthesize._rotulo_quantificador`
(v1.2.3) e uma cópia em `briefing._quantificador`, feita de propósito e com o
motivo escrito no docstring — *"reimportada por valor, não por import, para
que este módulo não dependa de `synthesize` (que importa SDKs)"*.

Duas cópias com um motivo eram defensáveis. **Três não:** o estágio [V]
(§3[V]) precisa do mesmo mapa, e a terceira cópia é o ponto em que
"calibração intocada desde a v1.2.3" vira uma frase que ninguém consegue mais
verificar. Este módulo não importa NADA — nem SDK, nem `config`, nem
`taxonomia` — então o motivo original da cópia desaparece em vez de ser
contornado.

**Nada aqui é novo.** As faixas, a ordem fraca→forte e a resolução de empate
são idênticas às da v1.2.3; o portão de equivalência que autorizou a extração
está em `tests/test_quantificador.py`, com as duas implementações antigas
congeladas literalmente como oráculo.

**A correção pela raiz que o mapa É** (v1.2.3, mesmo tipo da v1.1.1 sobre o
denominador): o LLM não decide número nem rótulo numérico — o código decide.
A calibração por INSTRUÇÃO (v1.2.2, o LLM calculava a fração e escolhia o
quantificador sozinho) reduziu mas não eliminou o modo de falha "quase
todos"/"praticamente todos" aplicado a frações de 65-70%, que reincidiu 2×
na primeira regeneração pós-fix.
"""
from __future__ import annotations

# Faixas do mais FRACO ao mais FORTE. Cada uma é
# `(rótulo, limite_inferior_inclusive, limite_superior, superior_inclusive)`.
# "poucos" é a ÚNICA faixa com superior EXCLUSIVO ("abaixo de 10%", i.e.
# pct < 10); todas as demais são inclusivas nos dois extremos, exatamente
# como escritas na v1.2.2 ("25%-50%" inclui 25 e 50).
#
# Resolução determinística de sobreposição — a regra é **sempre o rótulo mais
# fraco**, e ela cai de graça de iterar do fraco para o forte devolvendo o
# PRIMEIRO match. Cada fronteira compartilhada resolve assim:
#
#   pct == 10  -> só "alguns" bate ("poucos" exige pct < 10, exclusivo)
#   pct == 25  -> "alguns" (10-25) e "muitos" (25-50) empatam -> "alguns"
#   pct == 50  -> "muitos" (25-50), "cerca de metade" (40-60) e "a maioria"
#                 (50-80) empatam -> "muitos" (o mais fraco dos três)
#   pct == 80  -> "a maioria" (50-80) e "quase todos" (>=80) empatam -> "a maioria"
BANDAS_FRACA_PARA_FORTE: tuple[tuple[str, int, int, bool], ...] = (
    ("poucos", 0, 10, False),
    ("alguns", 10, 25, True),
    ("muitos", 25, 50, True),
    ("cerca de metade", 40, 60, True),
    ("a maioria", 50, 80, True),
    ("quase todos", 80, 100, True),
)

ROTULOS = tuple(r for r, _, _, _ in BANDAS_FRACA_PARA_FORTE)


def fracao_percentual(mencoes: int, n_analisadas: int | None) -> int:
    """Fração `mencoes/n_analisadas` em percentual inteiro arredondado (0-100).

    Denominador ausente, zero ou negativo devolve 0 em vez de estourar: um
    bucket sem reviews analisadas não pode derrubar o pipeline.
    """
    if not n_analisadas or n_analisadas <= 0:
        return 0
    return round(100 * mencoes / n_analisadas)


def rotulo(pct: int) -> str:
    """O rótulo determinístico de uma fração percentual.

    **O clamp a [0,100], e o registro honesto do que ele unifica.** As duas
    cópias antigas discordavam fora da faixa: `synthesize` devolvia "quase
    todos" (comentado como "fallback seguro"), `briefing` devolvia "poucos".
    Nenhum teste cobria o caso e nenhum caminho de produção o alcança — a
    síntese clampa o numerador ao denominador antes de construir o `Tema`
    (`synthesize._construir_temas`, v1.1.1), e a varredura dos 35 filmes
    publicados confirma `0 <= mencoes <= n` em todo tema e toda célula de
    eixo (`tests/test_quantificador.py`).

    Clampar mata as duas caudas divergentes e torna o comportamento
    determinístico para qualquer entrada, em vez de deixar duas respostas
    diferentes esperando alguém alcançá-las.
    """
    pct = max(0, min(100, pct))
    for nome, lo, hi, hi_inclusive in BANDAS_FRACA_PARA_FORTE:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return nome
    raise AssertionError(f"pct clampado a [0,100] sem faixa: {pct!r}")


def fracao_e_rotulo(mencoes: int, n_analisadas: int | None) -> tuple[int, str]:
    """`(fração%, rótulo)` — o par que quase todo chamador quer."""
    pct = fracao_percentual(mencoes, n_analisadas)
    return pct, rotulo(pct)


def mais_forte_que(candidato: str, permitido: str) -> bool:
    """Se `candidato` afirma uma faixa MAIS FORTE que `permitido`.

    A assimetria é a política do projeto desde a v1.2.3 e vale em toda
    fronteira ambígua: rótulo mais forte MENTE sobre o dado; mais fraco só
    subestima. Rótulo desconhecido nunca é tratado como mais forte — a
    checagem que o consome já reprova por outra via, e inventar severidade
    aqui produziria falso positivo em texto correto.
    """
    if candidato not in ROTULOS or permitido not in ROTULOS:
        return False
    return ROTULOS.index(candidato) > ROTULOS.index(permitido)
