"""A máquina de estados de amostra do bucket (`estado_amostra`).

Três coisas são travadas aqui: a tabela de transições (n_validas → estado),
o fallback para JSON antigo sem o campo, e que nenhum módulo volte a
recalcular o estado ou o predicado "amostra pequena" à mão.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from espectro24 import estado_amostra as EA
from espectro24.config import COTA_POR_BUCKET, PISO_POR_BUCKET

RAIZ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("n, piso, modo", [
    (0, "sem_analise", "sem_analise"),
    (2, "sem_analise", "sem_analise"),
    (3, "sem_numero", "reduzido"),
    (7, "sem_numero", "reduzido"),
    (8, "sem_quantificador", "reduzido"),
    (14, "sem_quantificador", "reduzido"),
    (15, "completa", "reduzido"),
    (39, "completa", "reduzido"),
    (40, "completa", "completo"),
    (500, "completa", "completo"),
])
def test_tabela_de_transicoes(n, piso, modo):
    assert EA.estado_do_piso(n) == piso
    assert EA.modo_do_bucket(n) == modo


def test_os_dois_eixos_concordam_em_sem_analise():
    # O piso mínimo do `modo` e o último degrau do piso escalonado precisam
    # cair no mesmo n — senão um bucket seria "sem análise" num eixo e
    # analisado no outro.
    for n in range(0, COTA_POR_BUCKET + 5):
        assert ((EA.estado_do_piso(n) == "sem_analise")
                == (EA.modo_do_bucket(n) == "sem_analise")), n
    assert EA.estado_do_piso(PISO_POR_BUCKET) != "sem_analise"


def test_todo_estado_tem_permissao_declarada():
    from espectro24.briefing import PERMISSOES_POR_ESTADO
    assert set(PERMISSOES_POR_ESTADO) == set(EA.ESTADOS_PISO)


def test_collector_e_briefing_reexportam_a_mesma_regra():
    from espectro24 import briefing, collector
    assert collector.estado_do_piso is EA.estado_do_piso
    assert briefing._estado_piso is EA.estado_piso_do_bucket


@pytest.mark.parametrize("bucket, piso, modo", [
    # Campo declarado vence sempre.
    ({"estado_piso": "sem_numero", "modo": "reduzido", "n_validas": 50},
     "sem_numero", "reduzido"),
    # JSON anterior à v1.9.0: derivado de n_validas, nunca um default fixo.
    ({"modo": "completo", "n_validas": 50}, "completa", "completo"),
    ({"modo": "sem_analise", "n_validas": 1}, "sem_analise", "sem_analise"),
    ({"n_validas": 10, "alvo": 40}, "sem_quantificador", "reduzido"),
    ({}, "sem_analise", "sem_analise"),
])
def test_fallback_de_bucket_serializado(bucket, piso, modo):
    assert EA.estado_piso_do_bucket(bucket) == piso
    assert EA.modo_de_bucket_serializado(bucket) == modo


@pytest.mark.parametrize("modo, piso, esperado", [
    ("completo", "completa", False),
    ("reduzido", "completa", True),
    ("completo", "sem_quantificador", True),
    ("sem_analise", "sem_analise", True),
    (None, None, True),
])
def test_amostra_pequena(modo, piso, esperado):
    assert EA.amostra_pequena(modo, piso) is esperado


# Formas de recalcular o estado à mão que existiam antes da centralização.
_REIMPLEMENTACOES = [
    re.compile(r"""modo['"\]\)]*\s*==\s*['"]reduzido['"]\s+or"""),
    re.compile(r"""estado_piso['"\]\)]*\s*!=\s*['"]completa['"]\s+or"""),
    re.compile(r"""get\(\s*['"]estado_piso['"]\s*\)\s*or\s*['"]completa['"]"""),
    re.compile(r"""modo\s*=\s*['"]sem_analise['"]\s*$""", re.M),
]


def test_ninguem_reimplementa_o_estado_fora_do_modulo():
    ofensores = []
    for pasta in ("src/espectro24", "scripts"):
        for arq in (RAIZ / pasta).rglob("*.py"):
            if arq.name == "estado_amostra.py":
                continue
            texto = arq.read_text(encoding="utf-8")
            for padrao in _REIMPLEMENTACOES:
                if padrao.search(texto):
                    ofensores.append(f"{arq.relative_to(RAIZ)}: {padrao.pattern}")
    assert not ofensores, (
        "estado de amostra recalculado à mão — use espectro24.estado_amostra:\n"
        + "\n".join(ofensores))
