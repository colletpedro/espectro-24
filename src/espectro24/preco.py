"""Preço do DeepSeek — fonte ÚNICA, com a janela de pico.

**ESTE NÚMERO TEM VALIDADE.** Preço de provider muda sem aviso. A tabela abaixo
foi lida em `TABELA_VERIFICADA_EM` e vale desde `TABELA_VIGENTE_DESDE`; se hoje
estiver a mais de `VALIDADE_DIAS` da leitura, `aviso_de_validade()` devolve um
texto que os relatórios de custo imprimem. Reler antes de decidir depósito.

Fonte: https://api-docs.deepseek.com/quick_start/pricing/ — COM a barra final.
Sem ela a página não renderiza a tabela (é montada por JS); a versão em chinês
(`/zh-cn/quick_start/pricing`) traz os mesmos valores em RMB e serve de
conferência cruzada da janela (horário de Pequim, UTC+8).

Por que o módulo existe (2026-09-18): as constantes `PRECO_*` que viviam em
`classificar_10`, `gate_taxonomia` e `verificador_impacto` eram de 14/08,
anteriores à tabela V4.1-Flash de 10/09. Elas reportavam ~38% do custo real no
pico (2,6× de subestimativa) e o saldo zerou duas vezes sem aviso. O lote
noturno de 18/09 calculou US$0,66 e custou US$1,75.

A JANELA. O preço fora de pico é METADE do de pico. Pico = segunda a sexta,
01:00-04:00 e 06:00-10:00 UTC (9:00-12:00 e 14:00-18:00 em Pequim). Todo o
resto — inclusive sábado e domingo inteiros — é fora de pico. A página não diz
se o instante exato do fim da janela é pico; tratamos cada janela como
`[início, fim)`. O erro possível é de uma chamada por fronteira.
Feriados chineses não constam da página e NÃO são modelados.

HORÁRIO DA CHAMADA. Os registros novos de passe e do verificador gravam `ts`
(UTC, ISO-8601). Registro antigo não tem `ts`, e sem horário o cálculo assume
PICO: superestimar é o lado seguro, e o erro que zerou o saldo foi o oposto.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Iterable, Mapping

TABELA_MODELO = ("DeepSeek-V4.1-Flash (nome `deepseek-flash`; o alias legado "
                 "`deepseek-v4-flash`, que o código ainda usa, é roteado para "
                 "ele e cobrado a este preço)")
TABELA_VIGENTE_DESDE = date(2026, 9, 10)     # 04:00 UTC, release do V4.1-Flash
TABELA_VERIFICADA_EM = date(2026, 9, 18)
VALIDADE_DIAS = 30


@dataclass(frozen=True)
class Preco:
    """USD por 1M de tokens."""
    entrada_miss: float
    entrada_hit: float
    saida: float

    @property
    def miss_por_token(self) -> float:
        return self.entrada_miss / 1_000_000

    @property
    def hit_por_token(self) -> float:
        return self.entrada_hit / 1_000_000

    @property
    def saida_por_token(self) -> float:
        return self.saida / 1_000_000


FORA_DE_PICO = Preco(entrada_miss=0.15, entrada_hit=0.003, saida=0.60)
PICO = Preco(entrada_miss=0.30, entrada_hit=0.006, saida=1.20)

# `[início, fim)`, em UTC, segunda a sexta (`datetime.weekday()` 0..4).
JANELAS_PICO_UTC = ((time(1, 0), time(4, 0)), (time(6, 0), time(10, 0)))
DIAS_DE_PICO = (0, 1, 2, 3, 4)


def _em_utc(quando: datetime) -> datetime:
    if quando.tzinfo is None:
        raise ValueError(
            "horário sem fuso: a janela de pico é definida em UTC e um datetime "
            "ingênuo é ambíguo. Passe um datetime com tzinfo.")
    return quando.astimezone(timezone.utc)


def em_pico(quando: datetime) -> bool:
    u = _em_utc(quando)
    if u.weekday() not in DIAS_DE_PICO:
        return False
    t = u.time()
    return any(ini <= t < fim for ini, fim in JANELAS_PICO_UTC)


def preco_em(quando: datetime | None) -> Preco:
    """A tabela vigente no instante. `None` → PICO (pior caso, ver o módulo)."""
    if quando is None:
        return PICO
    return PICO if em_pico(quando) else FORA_DE_PICO


def custo_usd(uso: Mapping[str, int] | None,
              quando: datetime | None = None) -> float:
    """Custo de UMA chamada (ou de um agregado no MESMO regime de preço).
    `uso` tem as chaves do adaptador: `cache_miss_tokens`, `cache_hit_tokens`,
    `completion_tokens`."""
    if not uso:
        return 0.0
    p = preco_em(quando)
    return (uso.get("cache_miss_tokens", 0) * p.miss_por_token
            + uso.get("cache_hit_tokens", 0) * p.hit_por_token
            + uso.get("completion_tokens", 0) * p.saida_por_token)


def _ler_ts(bruto) -> datetime | None:
    if not bruto:
        return None
    try:
        return _em_utc(datetime.fromisoformat(bruto))
    except (TypeError, ValueError):
        return None


@dataclass
class CustoAgregado:
    custo_usd: float = 0.0
    n_chamadas: int = 0
    n_sem_horario: int = 0          # cobradas como PICO por falta de `ts`
    custo_pico_usd: float = 0.0
    custo_fora_de_pico_usd: float = 0.0


def custo_de_registros(registros: Iterable[Mapping]) -> CustoAgregado:
    """Soma o custo de registros de chamada (`uso` + `ts` opcional), cada um
    no preço do SEU instante. Registro de outro provider (fallback Gemini)
    fica de fora — o preço aqui é o do DeepSeek."""
    ag = CustoAgregado()
    for r in registros:
        if r.get("provider", "deepseek") != "deepseek":
            continue
        quando = _ler_ts(r.get("ts"))
        c = custo_usd(r.get("uso"), quando)
        ag.custo_usd += c
        ag.n_chamadas += 1
        if quando is None:
            ag.n_sem_horario += 1
            ag.custo_pico_usd += c
        elif em_pico(quando):
            ag.custo_pico_usd += c
        else:
            ag.custo_fora_de_pico_usd += c
    return ag


def agora_utc_iso() -> str:
    """O `ts` que os registros novos gravam."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def aviso_de_validade(hoje: date | None = None) -> str | None:
    """Texto de aviso se a tabela passou da validade; `None` se está em dia."""
    hoje = hoje or date.today()
    idade = (hoje - TABELA_VERIFICADA_EM).days
    if idade <= VALIDADE_DIAS:
        return None
    return (f"AVISO: a tabela de preço do DeepSeek foi lida em "
            f"{TABELA_VERIFICADA_EM.isoformat()} ({idade} dias; validade "
            f"{VALIDADE_DIAS}). Preço de provider muda: releia "
            f"https://api-docs.deepseek.com/quick_start/pricing/ antes de "
            f"decidir depósito.")


# Preço "sem horário" para os scripts de estudo, que agregam `uso` sem `ts`:
# o PICO, pelo mesmo motivo do pior caso.
PRECO_ENTRADA_MISS = PICO.miss_por_token
PRECO_ENTRADA_HIT = PICO.hit_por_token
PRECO_SAIDA = PICO.saida_por_token
