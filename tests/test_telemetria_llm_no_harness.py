"""[v1.9.25, §3[D], Entrega 3] A telemetria de retentativa atravessa o limite
de PROCESSO e chega ao relatório do harness de lote.

O harness (§3[H], `scripts/publicar_catalogo.py`) roda o CLI como
SUBPROCESSO, então `synthesize._telemetria_llm` — um contador de módulo —
vive no processo filho e morre com ele. O pai só vê o que o filho escreveu.
`stderr` já era capturado no log de publicação, então a travessia é uma linha
nele, com formato e parser no MESMO lugar (`synthesize`), e agregação no
`--relatorio`.

Num lote de ~300 filmes, taxa de retentativa invisível é degradação
silenciosa: o sintoma seria lentidão sem causa aparente.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import synthesize as S  # noqa: E402


@pytest.fixture(autouse=True)
def _telemetria_limpa():
    S.resetar_telemetria_retentativa_llm()
    yield
    S.resetar_telemetria_retentativa_llm()


# --- o contrato de ida e volta ---------------------------------------------

def test_ida_e_volta_preserva_a_telemetria():
    """Formato e parser são as duas metades do mesmo contrato. Se alguém
    mudar a linha sem mudar o parser, é aqui que quebra."""
    S._registrar_retentativa_llm("ServerError")
    S._registrar_retentativa_llm("ServerError")
    S._registrar_retentativa_llm("ConnectTimeout")

    linha = S.linha_telemetria_llm()
    devolta = S.parse_linha_telemetria_llm(f"ruído antes\n{linha}\nruído depois")

    assert devolta == {"n_retentativas": 3,
                       "por_tipo": {"ServerError": 2, "ConnectTimeout": 1}}


def test_zero_retentativas_atravessa_como_zero_nao_como_ausencia():
    """Distinção que o relatório depende: zero medido ≠ não medido."""
    devolta = S.parse_linha_telemetria_llm(S.linha_telemetria_llm())
    assert devolta == {"n_retentativas": 0, "por_tipo": {}}


@pytest.mark.parametrize("stderr", [
    "",                                   # execução sem a linha
    "Requisições de rede nesta execução: 48",   # versão anterior à v1.9.25
    "Retentativas de transporte do LLM: xx {}",  # linha corrompida
    "Retentativas de transporte do LLM: 3 {não json}",
])
def test_stderr_sem_linha_valida_devolve_none(stderr):
    """`None` significa "não sei" — o relatório o conta à parte em vez de
    somar como zero, que maquiaria a taxa."""
    assert S.parse_linha_telemetria_llm(stderr) is None


def test_a_linha_sai_no_stderr_do_cli_de_verdade():
    """Guard-rail contra o modo de falha clássico: a função existe, o parser
    existe, e ninguém chama a função no CLI."""
    fonte = (RAIZ / "src" / "espectro24" / "cli.py").read_text(encoding="utf-8")
    assert "linha_telemetria_llm()" in fonte
    assert "file=sys.stderr" in fonte.split("linha_telemetria_llm()")[1][:40]


# --- a agregação no relatório do harness -----------------------------------

def _pc():
    import publicar_catalogo
    return publicar_catalogo


def test_publicar_um_grava_a_telemetria_como_campo(monkeypatch, tmp_path):
    """Sem campo próprio, a telemetria ficaria só dentro de `stderr_tail` —
    legível por grep, invisível para o relatório."""
    pc = _pc()

    class _R:
        returncode, stdout = 0, ""
        stderr = ("JSON salvo em x\nRequisições de rede nesta execução: 48\n"
                  'Retentativas de transporte do LLM: 2 {"ServerError": 2}')

    monkeypatch.setattr(pc.subprocess, "run", lambda *a, **kw: _R())
    monkeypatch.setattr(pc, "_ja_publicado", lambda slug: True)

    res = pc.publicar_um("um-filme")
    assert res["retentativa_llm"] == {"n_retentativas": 2,
                                      "por_tipo": {"ServerError": 2}}


def test_relatorio_agrega_o_lote_e_separa_quem_nao_tem_telemetria(capsys):
    """A soma é do LOTE — por filme seria ruído, já que a esmagadora maioria
    é zero. E quem não tem telemetria conta à parte, nunca como zero."""
    pc = _pc()
    pc._linha_retentativa_llm({
        "a": {"retentativa_llm": {"n_retentativas": 2,
                                  "por_tipo": {"ServerError": 2}}},
        "b": {"retentativa_llm": {"n_retentativas": 1,
                                  "por_tipo": {"ConnectTimeout": 1}}},
        "c": {"retentativa_llm": {"n_retentativas": 0, "por_tipo": {}}},
        "d": {"retentativa_llm": None},        # versão anterior
        "e": {},                                # campo ausente
    })
    out = capsys.readouterr().out
    assert "3 em 3 execução(ões)" in out
    assert "'ServerError': 2" in out and "'ConnectTimeout': 1" in out
    assert "2 sem telemetria" in out


def test_relatorio_silencia_quando_nao_ha_log(capsys):
    pc = _pc()
    pc._linha_retentativa_llm({})
    assert capsys.readouterr().out == ""
