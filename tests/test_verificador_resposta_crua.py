"""[C3(B)] A falha de parse passa a guardar a RESPOSTA CRUA.

O achado da C3: ~30 `JSONDecodeError` por lote (0,87%, taxa estável) do
verificador, com causa não investigada. O registro guardava só a mensagem do
erro (`Extra data: line 1 column 45`) — a resposta que a causou sumia, e sem
ela a causa é inalcançável por construção.

O que se prova, sem chamada de LLM (o cliente é falso):

1. o registro de falha de parse carrega `resposta_crua`, IDÊNTICA à recebida;
2. carrega também `uso`: a chamada foi cobrada e o registro de falha não a
   contava — o custo de 0,87% das chamadas ficava fora de todo relatório;
3. NADA é retentado: uma falha custa exatamente uma chamada;
4. falha de TRANSPORTE (sem resposta) não ganha `resposta_crua` inventada;
5. os registros de sucesso e de falha carregam `ts`, que a janela de preço lê;
6. a mesma garantia na classificação (`votacao_3`), que tem o mesmo padrão;
7. a falha com `resposta_crua` continua sendo pendência do verificador — o
   contrato do resume (`ok: False` → retentada na reexecução) não muda.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import verificador_impacto as vi  # noqa: E402
import votacao_3 as v3  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.preco import custo_de_registros  # noqa: E402

# O modo de falha REAL registrado em ABERTO.md C3(B): JSON válido seguido de
# lixo. `json.loads` levanta `Extra data`.
CRUA_EXTRA_DATA = '{"confirma": true, "frase": "f", "alvo": "espectador"} {"x"'
USO = {"prompt_tokens": 640, "completion_tokens": 41,
       "cache_hit_tokens": 512, "cache_miss_tokens": 128}


@pytest.fixture(autouse=True)
def _sem_rede_nem_estado(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    S.limpar_parada_por_saldo()
    yield
    S.limpar_parada_por_saldo()


class Chamadas:
    def __init__(self, resposta=None, excecao=None):
        self.n = 0
        self._resposta, self._excecao = resposta, excecao

    def __call__(self, *a, **kw):
        self.n += 1
        if self._excecao is not None:
            raise self._excecao
        return {"texto": self._resposta, "provider": "deepseek",
                "modelo": "deepseek-v4-flash", "uso": dict(USO),
                "latencia_s": 0.2, "fallback_conteudo": None}


def _rodar_verificador(monkeypatch, tmp_path, fake, n_reviews=1):
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: object())
    monkeypatch.setattr(vi, "resposta_json_com_fallback", fake)
    arq = tmp_path / "verificador.jsonl"
    reviews = [{"id": f"r{i}", "slug": "f", "nivel": 4.0, "n_chars": 30,
                "texto": "texto da review"} for i in range(n_reviews)]
    vi.rodar_passe("V2_alvo", 1, reviews, arq=arq)
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()]


def test_a_falha_de_parse_guarda_a_resposta_crua_identica(monkeypatch, tmp_path):
    fake = Chamadas(CRUA_EXTRA_DATA)
    [reg] = _rodar_verificador(monkeypatch, tmp_path, fake)
    assert reg["ok"] is False
    assert reg["erro"].startswith("JSONDecodeError")
    assert reg["resposta_crua"] == CRUA_EXTRA_DATA          # byte a byte


def test_a_falha_de_parse_guarda_o_uso_porque_a_chamada_foi_cobrada(
        monkeypatch, tmp_path):
    [reg] = _rodar_verificador(monkeypatch, tmp_path, Chamadas(CRUA_EXTRA_DATA))
    assert reg["uso"] == USO
    assert reg["provider"] == "deepseek" and reg["modelo"] == "deepseek-v4-flash"
    # ...e o relatório de custo passa a enxergá-la.
    assert custo_de_registros([reg]).custo_usd > 0


def test_uma_falha_de_parse_custa_exatamente_uma_chamada(monkeypatch, tmp_path):
    """Sem retentativa: o passo é só evidência para a próxima ocorrência."""
    fake = Chamadas(CRUA_EXTRA_DATA)
    regs = _rodar_verificador(monkeypatch, tmp_path, fake, n_reviews=5)
    assert fake.n == 5
    assert len(regs) == 5 and all(not r["ok"] for r in regs)


def test_falha_de_transporte_nao_ganha_resposta_inventada(monkeypatch, tmp_path):
    """Sem resposta não há o que guardar — e o registro não pode fingir."""
    fake = Chamadas(excecao=S.LLMTransportError("timeout"))
    [reg] = _rodar_verificador(monkeypatch, tmp_path, fake)
    assert reg["ok"] is False
    assert "resposta_crua" not in reg and "uso" not in reg
    assert reg["erro"].startswith("LLMTransportError")


def test_registro_de_sucesso_nao_carrega_resposta_crua(monkeypatch, tmp_path):
    ok = '{"confirma": false, "frase": "f", "alvo": "espectador"}'
    [reg] = _rodar_verificador(monkeypatch, tmp_path, Chamadas(ok))
    assert reg["ok"] is True and "resposta_crua" not in reg
    assert reg["confirma"] is False


def test_os_registros_do_verificador_carregam_ts(monkeypatch, tmp_path):
    ok = '{"confirma": true, "frase": "f", "alvo": "espectador"}'
    outro = tmp_path / "outro"
    outro.mkdir()
    [sucesso] = _rodar_verificador(monkeypatch, tmp_path, Chamadas(ok))
    [falha] = _rodar_verificador(monkeypatch, outro, Chamadas(CRUA_EXTRA_DATA))
    for reg in (sucesso, falha):
        assert reg["ts"].endswith("+00:00")
        assert custo_de_registros([{**reg, "uso": USO}]).n_sem_horario == 0


def test_a_falha_com_resposta_crua_continua_pendente_e_e_retentada_no_resume(
        monkeypatch, tmp_path):
    """O contrato do resume não muda: só `ok: True` conta como feito, então a
    reexecução retenta a review — agora com a evidência da primeira tentativa
    no arquivo (append-only)."""
    arq = tmp_path / "verificador.jsonl"
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: object())
    review = {"id": "r0", "slug": "f", "nivel": 4.0, "n_chars": 30, "texto": "t"}

    monkeypatch.setattr(vi, "resposta_json_com_fallback",
                        Chamadas(CRUA_EXTRA_DATA))
    vi.rodar_passe("V2_alvo", 1, [review], arq=arq)
    ok = '{"confirma": true, "frase": "f", "alvo": "espectador"}'
    segunda = Chamadas(ok)
    monkeypatch.setattr(vi, "resposta_json_com_fallback", segunda)
    vi.rodar_passe("V2_alvo", 1, [review], arq=arq)

    regs = [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()]
    assert segunda.n == 1
    assert [r["ok"] for r in regs] == [False, True]
    assert regs[0]["resposta_crua"] == CRUA_EXTRA_DATA     # a evidência fica


def test_o_motivo_da_pendencia_nao_muda_com_o_campo_novo():
    """`_motivo_pendencia` lê só `erro`; `resposta_crua` não vaza para o
    `consenso_verificado.jsonl` publicado."""
    m = vi._motivo_pendencia("JSONDecodeError: Extra data: line 1 column 45")
    assert m["motivo"] == "erro_JSONDecodeError"
    assert "resposta_crua" not in m


# --- a mesma garantia na classificação ---------------------------------------

def _rodar_passe_classificacao(monkeypatch, tmp_path, fake):
    tid = v3.taxonomia_id()
    amostra = {"taxonomia_id": tid, "filmes": [{"slug": "f", "perfil": "x"}],
               "reviews": [{"slug": "f", "perfil": "x", "bucket": "negativas",
                            "id": "r1", "nivel": 1.0, "n_chars": 10,
                            "texto": "t"}]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    passe = tmp_path / "passe_1.jsonl"
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", {1: passe})
    monkeypatch.setattr(v3, "RAIZ", tmp_path)
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: object())
    monkeypatch.setattr(v3, "resposta_classificacao", fake)
    v3.classificar_passe(1)
    return [json.loads(l) for l in passe.read_text(encoding="utf-8").splitlines()]


def test_classificacao_tambem_guarda_resposta_crua_uso_e_ts(monkeypatch, tmp_path):
    fake = Chamadas('{"eixos": ["atuacao"]} lixo depois')
    [reg] = _rodar_passe_classificacao(monkeypatch, tmp_path, fake)
    assert reg["ok"] is False and reg["erro"].startswith("JSONDecodeError")
    assert reg["resposta_crua"] == '{"eixos": ["atuacao"]} lixo depois'
    assert reg["uso"] == USO and reg["ts"].endswith("+00:00")
    assert fake.n == 1


def test_classificacao_de_sucesso_grava_ts(monkeypatch, tmp_path):
    fake = Chamadas('{"eixos": ["atuacao"], "temas_livres": []}')
    [reg] = _rodar_passe_classificacao(monkeypatch, tmp_path, fake)
    assert reg["ok"] is True and reg["ts"].endswith("+00:00")
    assert "resposta_crua" not in reg
