"""`scripts/custo_por_lote.py`: a alocação no tempo dos registros sem `ts`.

Os registros anteriores a 2026-09-18 não guardam horário; o script os aloca
linearmente entre o início e o fim do estágio (janelas dos logs do driver).
É uma aproximação, então a parte que a sustenta é testada: a alocação, a
divisão pico/fora de pico e as janelas dos dois lotes.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import custo_por_lote as C  # noqa: E402
from espectro24.preco import em_pico  # noqa: E402

UTC = timezone.utc
USO = {"cache_miss_tokens": 1_000_000}


def test_aloca_cada_registro_no_meio_da_sua_fatia_do_estagio():
    ini = datetime(2026, 9, 16, 5, 58, tzinfo=UTC)
    fim = datetime(2026, 9, 16, 6, 2, tzinfo=UTC)
    alocados = C.alocar_no_tempo([{"i": i} for i in range(4)], ini, fim)
    assert [t.strftime("%H:%M:%S") for _, t in alocados] == [
        "05:58:30", "05:59:30", "06:00:30", "06:01:30"]


def test_estagio_que_cruza_a_janela_e_cobrado_metade_em_cada_regime():
    ini = datetime(2026, 9, 16, 5, 58, tzinfo=UTC)          # quarta
    fim = datetime(2026, 9, 16, 6, 2, tzinfo=UTC)
    c = C.custo_alocado(C.alocar_no_tempo(
        [{"uso": USO} for _ in range(4)], ini, fim))
    assert c.n == 4 and c.em_pico_n == 2
    assert c.real == pytest.approx(2 * 0.15 + 2 * 0.30)
    assert c.pico_puro == pytest.approx(4 * 0.30)
    assert c.fora_puro == pytest.approx(4 * 0.15)
    assert c.velho == pytest.approx(4 * 0.14)


def test_sem_registros_nao_divide_por_zero():
    assert C.alocar_no_tempo([], C.LOTE_44.classificacao[0],
                             C.LOTE_44.classificacao[1]) == []


def test_outro_provider_fica_fora_do_custo():
    t = datetime(2026, 9, 18, 8, tzinfo=UTC)
    c = C.custo_alocado([({"uso": USO, "provider": "gemini"}, t),
                         ({"uso": USO}, t)])
    assert c.n == 1


def test_o_lote_de_55_rodou_inteiro_no_pico_de_uma_sexta():
    """O fato que explica US$1,75 e não US$0,66."""
    ini, fim = C.LOTE_55.classificacao
    assert ini.weekday() == 4 and em_pico(ini) and em_pico(fim)


def test_o_lote_de_44_comecou_3_minutos_antes_do_pico():
    ini, fim = C.LOTE_44.classificacao
    assert not em_pico(ini) and em_pico(fim)
    assert C.LOTE_44.verificador[0] == fim
