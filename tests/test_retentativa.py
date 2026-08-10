"""[v1.9.6, §2.4] Retentativa no `Fetcher` — TRANSPORTE sim, BLOQUEIO nunca.

A metade que importa destes testes é a NEGATIVA: 403, `AntiBotError` e o
segundo 503 do lote **não** podem retentar. Retentar bloqueio é evasão, e a
spec proíbe.
"""
from __future__ import annotations

import pytest
import requests

from espectro24 import fetcher as mod
from espectro24.fetcher import (
    AntiBotError,
    FetchError,
    Fetcher,
    PressaoDoSite,
    SobrecargaError,
)


class FakeResp:
    def __init__(self, status_code=200, text="<html>ok</html>"):
        self.status_code = status_code
        self.text = text


class FakeSession:
    """Devolve/levanta o próximo item de `roteiro` a cada `get`."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.chamadas = 0

    def get(self, url, **kwargs):
        self.chamadas += 1
        item = self.roteiro.pop(0) if self.roteiro else FakeResp()
        if isinstance(item, BaseException):
            raise item
        return item


@pytest.fixture
def sem_dormir(monkeypatch):
    """Captura os `sleep` em vez de dormir — é a asserção, não só a agilidade."""
    dormidas: list[float] = []
    monkeypatch.setattr(mod.time, "sleep", dormidas.append)
    # jitter fixo em 1.0 para que o backoff seja verificável
    monkeypatch.setattr(mod.random, "uniform", lambda a, b: 1.0)
    return dormidas


def _fetcher(tmp_path, roteiro, **kw):
    return Fetcher(cache_dir=tmp_path, session=FakeSession(roteiro), **kw)


# --- transporte: RETENTA -----------------------------------------------------

@pytest.mark.parametrize("erro", [
    ConnectionResetError("reset by peer"),
    requests.exceptions.ConnectionError("conn aborted"),
    requests.exceptions.ReadTimeout("read timed out"),
    requests.exceptions.ConnectTimeout("connect timed out"),
    requests.exceptions.ChunkedEncodingError("broken chunk"),
])
def test_erro_de_transporte_retenta_e_sucede_na_segunda(tmp_path, sem_dormir, erro):
    f = _fetcher(tmp_path, [erro, FakeResp(text="<html>bom</html>")])
    assert f.get("http://x/1", "k1") == "<html>bom</html>"
    assert f.session.chamadas == 2
    assert f.n_retentativas == 1
    assert sum(f.retentativas_por_tipo.values()) == 1


def test_transporte_retenta_no_maximo_3_tentativas(tmp_path, sem_dormir):
    erros = [ConnectionResetError("x") for _ in range(5)]
    f = _fetcher(tmp_path, erros)
    with pytest.raises(FetchError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 3          # 3 tentativas, não 5
    assert f.n_retentativas == 3
    assert not (tmp_path / "k1").exists()   # falha não escreve cache


def test_backoff_exponencial_soma_ao_delay_de_educacao(tmp_path, sem_dormir):
    """§2.4: o delay de educação vale entre TODAS as tentativas; o backoff
    SOMA a ele, nunca o substitui."""
    f = _fetcher(tmp_path, [ConnectionResetError("x"), ConnectionResetError("x"),
                            FakeResp()], delay=2.0)
    f.get("http://x/1", "k1")
    # delay, backoff(2s), delay, backoff(4s), delay
    assert sem_dormir == [2.0, 2.0, 2.0, 4.0, 2.0]


def test_jitter_fica_na_faixa_de_25_por_cento(tmp_path, monkeypatch):
    dormidas: list[float] = []
    monkeypatch.setattr(mod.time, "sleep", dormidas.append)
    f = _fetcher(tmp_path, [ConnectionResetError("x")] * 3, delay=0.0)
    with pytest.raises(FetchError):
        f.get("http://x/1", "k1")
    backoffs = [d for d in dormidas if d > 0]
    assert len(backoffs) == 2
    assert 1.5 <= backoffs[0] <= 2.5      # 2s ±25%
    assert 3.0 <= backoffs[1] <= 5.0      # 4s ±25%


# --- bloqueio: NÃO RETENTA ---------------------------------------------------

def test_403_nao_retenta_e_para_na_hora(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp(403, "forbidden"), FakeResp()])
    with pytest.raises(AntiBotError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 1
    assert f.n_retentativas == 0


def test_challenge_cloudflare_nao_retenta(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp(200, "<title>Just a moment...</title>"),
                            FakeResp()])
    with pytest.raises(AntiBotError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 1
    assert f.n_retentativas == 0


def test_404_nao_retenta(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp(404, "nao existe"), FakeResp()])
    with pytest.raises(FetchError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 1
    assert f.n_retentativas == 0


# --- 503: uma retentativa por LOTE, a segunda para --------------------------

def test_primeiro_503_retenta_com_espera_longa(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp(503, "overloaded"), FakeResp(text="ok")],
                 delay=2.0)
    assert f.get("http://x/1", "k1") == "ok"
    assert f.session.chamadas == 2
    assert mod.ESPERA_503 in sem_dormir
    assert mod.ESPERA_503 > 8.0            # "backoff LONGO", não o de transporte
    assert f.n_503 == 1


def test_segundo_503_do_lote_para_o_lote(tmp_path, sem_dormir):
    """O contador é do LOTE: o segundo 503 pode vir em OUTRO filme, com outro
    `Fetcher`, e ainda assim para."""
    pressao = PressaoDoSite()
    f1 = _fetcher(tmp_path, [FakeResp(503), FakeResp(text="ok")], pressao=pressao)
    assert f1.get("http://x/1", "k1") == "ok"

    f2 = _fetcher(tmp_path, [FakeResp(503), FakeResp(text="ok")], pressao=pressao)
    with pytest.raises(SobrecargaError):
        f2.get("http://x/2", "k2")
    assert f2.session.chamadas == 1        # não retentou o segundo


def test_sobrecarga_nao_e_fetcherror(tmp_path):
    """§2.4: as etapas ADITIVAS engolem `FetchError`; engolir uma parada de
    lote seria o oposto do que a regra garante."""
    assert not issubclass(SobrecargaError, FetchError)
    assert not issubclass(SobrecargaError, AntiBotError)


def test_503_repetido_na_mesma_requisicao_tambem_para(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp(503), FakeResp(503), FakeResp(text="ok")])
    with pytest.raises(SobrecargaError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 2


# --- telemetria e invariantes de sempre -------------------------------------

def test_telemetria_por_tipo_de_erro(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [ConnectionResetError("x"),
                            requests.exceptions.ReadTimeout("y"),
                            FakeResp(text="ok")])
    assert f.get("http://x/1", "k1") == "ok"
    tel = f.telemetria_retentativa()
    assert tel["n_retentativas"] == 2
    assert tel["por_tipo"]["ConnectionResetError"] == 1
    assert tel["por_tipo"]["ReadTimeout"] == 1
    assert tel["n_503"] == 0


def test_cache_continua_evitando_a_rede_inteiramente(tmp_path, sem_dormir):
    (tmp_path / "k1").write_text("cacheado", encoding="utf-8")
    f = _fetcher(tmp_path, [ConnectionResetError("nunca chamado")])
    assert f.get("http://x/1", "k1") == "cacheado"
    assert f.session.chamadas == 0
    assert sem_dormir == []               # cache não paga nem o delay


def test_offline_sem_cache_falha_sem_tocar_a_rede(tmp_path, sem_dormir):
    f = _fetcher(tmp_path, [FakeResp()], offline=True)
    with pytest.raises(FetchError):
        f.get("http://x/1", "k1")
    assert f.session.chamadas == 0
