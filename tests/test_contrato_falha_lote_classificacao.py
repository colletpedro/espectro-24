"""[v1.9.25, §3[D]] O CONTRATO DE FALHA do lote de classificação, provado por
COMPORTAMENTO — não só por `import` (que prova apenas que o arquivo parseia).

A Entrega 2 removeu o laço de retentativa de 8 scripts por transformação
automatizada (dois bugs de indentação corrigidos no processo). O que estava
em jogo é justamente o contrato de falha, então este arquivo o exercita de
ponta a ponta com um SDK FALSO, sobre os caminhos de produção
(`classificar_10.classificar`, `votacao_3.classificar_passe`,
`gate_taxonomia.classificar`), provando as QUATRO propriedades JUNTAS, no
mesmo lote — é a combinação que descreve o comportamento real, e a que a
transformação poderia ter quebrado sem que nada mais acusasse:

1. Erro de CONTEÚDO consome exatamente 1 chamada de API (não 3).
2. Esse item é gravado com `ok: False`.
3. O lote NÃO aborta — os itens seguintes são processados.
4. Na execução seguinte, o resume RETENTA o item `ok: False` (só `ok: True`
   conta como feito).

E, ao lado: erro de TRANSPORTE num item é absorvido pelo ADAPTADOR (não pelo
script) e o lote também não aborta.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from threading import Lock

import httpx
import openai
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import synthesize as S  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_espera_real(monkeypatch):
    """Nenhum teste aqui precisa de tempo de parede — nem o backoff do
    adaptador, nem o `time.sleep` que sobrava nos scripts (removido, mas
    espiar não custa nada e blinda contra reintrodução)."""
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    S.resetar_telemetria_retentativa_llm()
    yield
    S.resetar_telemetria_retentativa_llm()


@pytest.fixture(autouse=True)
def _sem_vazamento_de_env(monkeypatch):
    """`classificar()`/`classificar_passe()` chamam `load_dotenv(RAIZ /
    ".env")` — e o `.env` real deste repo TEM chaves. `load_dotenv` escreve
    direto em `os.environ`, fora do controle do `monkeypatch`: sem este
    bloqueio, cada chamada aqui vazaria `DEEPSEEK_API_KEY`/`GEMINI_API_KEY`
    de verdade para o resto da suíte, quebrando testes não relacionados
    (`detect_provider` passa a ver "múltiplas chaves presentes"). Os testes
    deste arquivo não precisam de chave nenhuma — o SDK é falso."""
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)


class _FakeChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _FakeUsage:
    prompt_tokens = 10
    completion_tokens = 5
    prompt_cache_hit_tokens = 0
    prompt_cache_miss_tokens = 10


class _FakeResp:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsage()


def _erro_transporte(status=500, msg="overload"):
    return openai.InternalServerError(
        msg, response=httpx.Response(status, request=httpx.Request("POST", "http://x")),
        body=None)


class FakeSDKClient:
    """`client.chat.completions.create(**kwargs)` — dublê do transporte
    DeepSeek. Efeitos são resolvidos por MARCADOR: uma substring própria de
    cada review, embutida no `texto` para não depender de ordem entre
    threads (`CONCORRENCIA=8` nos scripts reais).

    A retentativa de TRANSPORTE não é simulada aqui — é a REAL
    (`synthesize.deepseek_resposta` chama este dublê por baixo dela), então
    a contagem de chamadas por marcador é evidência do comportamento do
    adaptador de produção, não de um mock do adaptador.
    """

    def __init__(self, efeitos_por_marcador: dict[str, list]):
        self._efeitos = {m: list(e) for m, e in efeitos_por_marcador.items()}
        self._lock = Lock()
        self.chamadas_por_marcador = collections.Counter()

        outer = self

        class _Completions:
            def create(inner, **kwargs):
                conteudo = kwargs["messages"][-1]["content"]
                with outer._lock:
                    marcador = next(m for m in outer._efeitos if m in conteudo)
                    outer.chamadas_por_marcador[marcador] += 1
                    efeito = outer._efeitos[marcador].pop(0)
                if isinstance(efeito, BaseException):
                    raise efeito
                return _FakeResp(efeito)

        self.chat = type("Chat", (), {"completions": _Completions()})()

    @property
    def total_chamadas(self) -> int:
        return sum(self.chamadas_por_marcador.values())


JSON_OK = '{"eixos": ["ritmo"], "temas_livres": []}'

# Três reviews, um por propriedade a exercitar. O marcador vai no `texto`
# para o dublê identificar qual review está sendo respondida.
REVIEWS = [
    {"id": "rev-conteudo-ruim", "marcador": "MARCA-CONTEUDO-RUIM",
     "efeitos": ["isto não é um JSON"]},
    {"id": "rev-transporte", "marcador": "MARCA-TRANSPORTE",
     "efeitos": [_erro_transporte, JSON_OK]},   # 1ª cai, 2ª sucede (adaptador)
    {"id": "rev-ok", "marcador": "MARCA-OK", "efeitos": [JSON_OK]},
]


def _amostra(tid: str) -> dict:
    return {
        "taxonomia_id": tid,
        "reviews": [
            {"slug": "filme-x", "perfil": "misto", "bucket": "negativas",
             "id": r["id"], "nivel": 2.0, "n_chars": 200,
             "texto": f"{r['marcador']} — review de teste completa o bastante."}
            for r in REVIEWS
        ],
    }


def _efeitos_resolvidos() -> dict[str, list]:
    """`_erro_transporte` é uma FÁBRICA (cada tentativa precisa de uma
    instância NOVA da exceção — reusar a mesma pelas 3 tentativas do
    adaptador seria irreal, embora inofensivo aqui)."""
    out = {}
    for r in REVIEWS:
        out[r["marcador"]] = [e() if callable(e) and e is _erro_transporte else e
                              for e in r["efeitos"]]
    return out


def _achar(linhas: list[dict], review_id: str) -> dict:
    achados = [l for l in linhas if l["id"] == review_id]
    assert len(achados) == 1, f"{review_id}: {len(achados)} registro(s)"
    return achados[0]


# ===========================================================================
# classificar_10.py — o caminho de PRODUÇÃO da classificação de 10 eixos
# ===========================================================================

def test_contrato_de_falha_do_lote_classificar_10(monkeypatch, tmp_path):
    import classificar_10 as c10

    tid = c10.taxonomia_id()
    arq_amostra = tmp_path / "amostra.json"
    arq_classif = tmp_path / "classificacoes.jsonl"
    arq_amostra.write_text(json.dumps(_amostra(tid)), encoding="utf-8")
    monkeypatch.setattr(c10, "ARQ_AMOSTRA", arq_amostra)
    monkeypatch.setattr(c10, "ARQ_CLASSIF", arq_classif)

    cliente1 = FakeSDKClient(_efeitos_resolvidos())
    monkeypatch.setattr(c10, "deepseek_client", lambda *a, **kw: cliente1)

    # --- 1ª execução: o lote inteiro, com um erro de conteúdo e um de
    # transporte no meio -------------------------------------------------
    c10.classificar()

    linhas = [json.loads(l) for l in arq_classif.read_text(encoding="utf-8")
              .splitlines() if l.strip()]

    # (3) o lote NÃO abortou — os TRÊS itens foram processados, inclusive os
    # que vêm depois do erro (a ordem entre threads não é garantida, então a
    # prova é "todos os três aparecem", não "aparecem em ordem").
    assert len(linhas) == 3
    assert {l["id"] for l in linhas} == {r["id"] for r in REVIEWS}

    # (1) conteúdo malformado custou EXATAMENTE 1 chamada — não 3.
    assert cliente1.chamadas_por_marcador["MARCA-CONTEUDO-RUIM"] == 1
    # e o transporte foi retentado pelo ADAPTADOR: exatamente 2 (falhou,
    # depois sucedeu) — nem 1 (sem retry) nem 3+ (empilhado com um laço
    # local que teria sobrevivido à transformação).
    assert cliente1.chamadas_por_marcador["MARCA-TRANSPORTE"] == 2
    assert cliente1.chamadas_por_marcador["MARCA-OK"] == 1
    assert cliente1.total_chamadas == 4

    # (2) o item de conteúdo malformado foi gravado com ok: False — não foi
    # descartado nem confundido com sucesso.
    reg_ruim = _achar(linhas, "rev-conteudo-ruim")
    assert reg_ruim["ok"] is False
    assert "erro" in reg_ruim

    # O de transporte e o normal sucederam de verdade (não sobreviveram só
    # porque a exceção foi engolida em silêncio).
    reg_transporte = _achar(linhas, "rev-transporte")
    assert reg_transporte["ok"] is True
    assert reg_transporte["eixos"] == ["ritmo"]
    reg_ok = _achar(linhas, "rev-ok")
    assert reg_ok["ok"] is True

    # E a telemetria do adaptador registrou a retentativa de transporte —
    # sinal de que quem absorveu foi ELE, não um laço local.
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 1

    # --- (4) 2ª execução (resume): só o item ok:False deve ser retentado.
    S.resetar_telemetria_retentativa_llm()
    cliente2 = FakeSDKClient({"MARCA-CONTEUDO-RUIM": [JSON_OK]})
    monkeypatch.setattr(c10, "deepseek_client", lambda *a, **kw: cliente2)

    c10.classificar()

    # Só a review malformada foi rechamada — as duas que já tinham ok:True
    # entraram em `feitos` e não voltaram a gastar chamada de API.
    assert cliente2.total_chamadas == 1
    assert cliente2.chamadas_por_marcador["MARCA-CONTEUDO-RUIM"] == 1

    linhas2 = [json.loads(l) for l in arq_classif.read_text(encoding="utf-8")
               .splitlines() if l.strip()]
    # o arquivo é append-only: a review malformada agora tem DOIS registros
    # (a falha antiga + o sucesso do resume) — o consumidor de produção
    # (`_carregar_ok`) lê o último `ok: True` que encontrar por chave.
    reprocessados = [l for l in linhas2 if l["id"] == "rev-conteudo-ruim"]
    assert len(reprocessados) == 2
    assert reprocessados[-1]["ok"] is True


# ===========================================================================
# votacao_3.py — mesma tarefa, parametrizada por PASSE
# ===========================================================================

def test_contrato_de_falha_do_lote_votacao_3(monkeypatch, tmp_path):
    import classificar_10 as c10
    import votacao_3 as v3

    tid = c10.taxonomia_id()
    arq_amostra = tmp_path / "amostra.json"
    arq_passe1 = tmp_path / "passe_1.jsonl"
    arq_amostra.write_text(json.dumps(_amostra(tid)), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", arq_amostra)
    monkeypatch.setattr(v3, "ARQ_PASSE", {1: arq_passe1, 2: tmp_path / "p2.jsonl",
                                          3: tmp_path / "p3.jsonl",
                                          4: tmp_path / "p4.jsonl"})

    cliente1 = FakeSDKClient(_efeitos_resolvidos())
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: cliente1)

    v3.classificar_passe(1)

    linhas = [json.loads(l) for l in arq_passe1.read_text(encoding="utf-8")
              .splitlines() if l.strip()]
    assert len(linhas) == 3                                    # (3) não abortou
    assert cliente1.chamadas_por_marcador["MARCA-CONTEUDO-RUIM"] == 1  # (1)
    assert cliente1.chamadas_por_marcador["MARCA-TRANSPORTE"] == 2     # adaptador
    assert _achar(linhas, "rev-conteudo-ruim")["ok"] is False          # (2)

    # (4) resume do PASSE: só o falho volta.
    cliente2 = FakeSDKClient({"MARCA-CONTEUDO-RUIM": [JSON_OK]})
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: cliente2)
    v3.classificar_passe(1)
    assert cliente2.total_chamadas == 1


# ===========================================================================
# gate_taxonomia.py — mesma tarefa, resume sem checar taxonomia_id
# ===========================================================================

def test_contrato_de_falha_do_lote_gate_taxonomia(monkeypatch, tmp_path):
    import gate_taxonomia as gt

    arq_amostra = tmp_path / "amostra.json"
    arq_classif = tmp_path / "classificacoes.jsonl"
    # gate_taxonomia.classificar() não checa taxonomia_id — qualquer valor serve.
    arq_amostra.write_text(json.dumps(_amostra("qualquer")), encoding="utf-8")
    monkeypatch.setattr(gt, "ARQ_AMOSTRA", arq_amostra)
    monkeypatch.setattr(gt, "ARQ_CLASSIF", arq_classif)

    cliente1 = FakeSDKClient(_efeitos_resolvidos())
    monkeypatch.setattr(gt, "deepseek_client", lambda *a, **kw: cliente1)

    gt.classificar()

    linhas = [json.loads(l) for l in arq_classif.read_text(encoding="utf-8")
              .splitlines() if l.strip()]
    assert len(linhas) == 3
    assert cliente1.chamadas_por_marcador["MARCA-CONTEUDO-RUIM"] == 1
    assert cliente1.chamadas_por_marcador["MARCA-TRANSPORTE"] == 2
    assert _achar(linhas, "rev-conteudo-ruim")["ok"] is False

    cliente2 = FakeSDKClient({"MARCA-CONTEUDO-RUIM": [JSON_OK]})
    monkeypatch.setattr(gt, "deepseek_client", lambda *a, **kw: cliente2)
    gt.classificar()
    assert cliente2.total_chamadas == 1
