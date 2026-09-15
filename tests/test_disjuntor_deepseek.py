"""[2026-09-15] Disjuntor do DeepSeek — estado em ARQUIVO, global, aberto por
`LLMSobrecarga` seguidas, reaberto por sonda depois de um prazo fixo.

O que está sob teste, na ordem do pedido:

1. abre em `CIRCUITO_LIMIAR_SOBRECARGAS` (3) sobrecargas SEGUIDAS — e não antes;
2. NÃO abre com `LLMPrazoExcedido` (é suposição nossa, não declaração do
   provider);
3. qualquer resposta válida zera a contagem;
4. o estado sobrevive entre PROCESSOS — é o que protege o lote de publicação,
   que roda cada filme num subprocesso;
5. depois de `CIRCUITO_REABERTURA_S`, uma chamada passa como sonda: responde,
   fecha; sobrecarga, reabre por mais um prazo;
6. a falha por disjuntor aberto não chama a rede e fica PENDENTE (`ok: False`,
   motivo `circuito_aberto`) — e a reexecução retenta só ela.

O arquivo de estado de cada teste é isolado por `tests/conftest.py`
(`_disjuntor_deepseek_isolado`); aqui ele é lido pelo caminho que o fixture
instalou.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import config  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402

MSG_FILA = ("We were unable to start processing your request within the "
            "900-second timeout limit. Please try again later.")
CORPO_FILA = {"error": {"message": MSG_FILA}}
NORMAL = {"id": "x", "object": "chat.completion", "created": 0,
          "model": "deepseek-v4-flash",
          "choices": [{"index": 0, "finish_reason": "stop",
                       "message": {"role": "assistant",
                                   "content": '{"confirma": true, "frase": "f", "alvo": "espectador"}'}}],
          "usage": {"prompt_tokens": 10, "completion_tokens": 3,
                    "total_tokens": 13}}


@pytest.fixture(autouse=True)
def _sem_espera(monkeypatch):
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    S.resetar_telemetria_retentativa_llm()
    yield
    S.resetar_telemetria_retentativa_llm()


class Cliente:
    """O SDK REAL da OpenAI sobre transporte falso: devolve `corpo` sempre
    (ou cada item de uma lista, em ordem) e conta as requisições HTTP."""

    def __init__(self, corpo):
        self._fila = list(corpo) if isinstance(corpo, list) else None
        self._sempre = None if isinstance(corpo, list) else corpo
        self._lock = threading.Lock()
        self.n = 0

        def handler(req):
            with self._lock:
                self.n += 1
                c = self._fila.pop(0) if self._fila is not None else self._sempre
            return httpx.Response(200, json=c)

        self.sdk = openai.OpenAI(
            api_key="fake", base_url="https://api.deepseek.com", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _chamar(cliente):
    return S.deepseek_resposta("sys", "user", "deepseek-v4-flash",
                               max_tokens=300, json_mode=True, client=cliente.sdk)


def _sobrecargas(n: int) -> Cliente:
    c = Cliente(CORPO_FILA)
    for _ in range(n):
        with pytest.raises(S.LLMSobrecarga):
            _chamar(c)
    return c


def _estado() -> dict:
    return S.estado_circuito()


# ===========================================================================
# 1. Abre em 3 seguidas — e não antes
# ===========================================================================

def test_duas_sobrecargas_nao_abrem():
    _sobrecargas(2)
    e = _estado()
    assert e["seguidas"] == 2 and e["aberto"] is False


def test_abre_em_tres_sobrecargas_seguidas_e_para_de_chamar_a_rede():
    c = _sobrecargas(config.CIRCUITO_LIMIAR_SOBRECARGAS)
    e = _estado()
    assert e["aberto"] is True and e["seguidas"] == 3
    assert MSG_FILA in e["ultimo_motivo"]
    antes = c.n                                   # 3 chamadas × 2 tentativas
    assert antes == 3 * (1 + config.LLM_RETENTATIVAS_INDISPONIVEL)
    with pytest.raises(S.LLMCircuitoAberto, match="circuito_aberto"):
        _chamar(c)
    assert c.n == antes                           # nenhuma requisição saiu


def test_circuito_aberto_e_indisponivel_mas_nao_e_retentado():
    """Subclasse de `LLMIndisponivel` (a rotulagem não empilha em cima), mas
    barrado ANTES da retentativa: falhar rápido é o objetivo inteiro."""
    assert issubclass(S.LLMCircuitoAberto, S.LLMIndisponivel)
    _sobrecargas(3)
    t0 = time.monotonic()
    with pytest.raises(S.LLMCircuitoAberto):
        _chamar(Cliente(NORMAL))
    assert time.monotonic() - t0 < 1
    assert S.telemetria_retentativa_llm()["por_tipo"].get("LLMCircuitoAberto") is None


# ===========================================================================
# 2. LLMPrazoExcedido NÃO conta
# ===========================================================================

def test_prazo_de_parede_nao_abre_o_disjuntor(monkeypatch):
    monkeypatch.setattr(S, "LLM_PRAZO_PAREDE_S", 0.05)
    solta = threading.Event()

    def pendurada(**kw):
        solta.wait(30)
        return SimpleNamespace(choices=None)

    lento = SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=pendurada)))
    try:
        for _ in range(config.CIRCUITO_LIMIAR_SOBRECARGAS + 2):
            with pytest.raises(S.LLMPrazoExcedido):
                S.deepseek_resposta("s", "u", "m", max_tokens=10,
                                    json_mode=True, client=lento)
    finally:
        solta.set()
    assert not _estado().get("aberto")
    assert not _estado().get("seguidas")
    _chamar(Cliente(NORMAL))                      # e a próxima passa


# ===========================================================================
# 3. Sucesso reseta
# ===========================================================================

def test_sucesso_zera_a_contagem():
    _sobrecargas(2)
    _chamar(Cliente(NORMAL))
    assert _estado()["seguidas"] == 0
    _sobrecargas(2)                               # 2 + 2 com sucesso no meio
    assert _estado()["aberto"] is False


def test_sucesso_com_estado_limpo_nao_escreve_o_arquivo():
    """Milhares de chamadas bem-sucedidas não podem virar milhares de
    escritas em disco."""
    _chamar(Cliente(NORMAL))
    assert not Path(S.CIRCUITO_ARQUIVO).exists()


# ===========================================================================
# 4. O estado sobrevive entre processos
# ===========================================================================

def _em_outro_processo(codigo: str) -> subprocess.CompletedProcess:
    prelude = (
        "import sys; from pathlib import Path\n"
        f"sys.path.insert(0, {str(RAIZ / 'src')!r})\n"
        "from espectro24 import synthesize as S\n"
        f"S.CIRCUITO_ARQUIVO = Path({str(S.CIRCUITO_ARQUIVO)!r})\n")
    return subprocess.run([sys.executable, "-c", prelude + codigo],
                          capture_output=True, text=True, timeout=60)


def test_estado_aberto_por_um_processo_barra_outro():
    """O lote de publicação roda cada filme num subprocesso: o disjuntor que
    um filme abre tem de valer para o filme seguinte."""
    r = _em_outro_processo(
        "for _ in range(3): S._circuito_registrar_sobrecarga('fila cheia')\n")
    assert r.returncode == 0, r.stderr
    assert "DISJUNTOR DO DEEPSEEK ABERTO" in r.stderr        # visível no log
    c = Cliente(NORMAL)
    with pytest.raises(S.LLMCircuitoAberto):
        _chamar(c)
    assert c.n == 0


def test_contagem_soma_entre_processos():
    """Global: 2 sobrecargas num processo + 1 em outro = aberto."""
    _sobrecargas(2)
    r = _em_outro_processo("S._circuito_registrar_sobrecarga('fila cheia')\n"
                           "print(S.estado_circuito()['aberto'])\n")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "True"
    assert _estado()["aberto"] is True


def test_barrado_em_outro_processo():
    _sobrecargas(3)
    r = _em_outro_processo(
        "try:\n    S._circuito_barrar('m')\nexcept Exception as e:\n"
        "    print(type(e).__name__)\n")
    assert r.stdout.strip() == "LLMCircuitoAberto"


# ===========================================================================
# 5. Sonda de reabertura depois do prazo fixo
# ===========================================================================

def _abrir_vencido():
    _sobrecargas(3)
    e = _estado()
    e["reabre_em_epoch"] = time.time() - 1               # os 5 min passaram
    Path(S.CIRCUITO_ARQUIVO).write_text(json.dumps(e), encoding="utf-8")


def test_antes_do_prazo_continua_barrado():
    _sobrecargas(3)
    reabre = _estado()["reabre_em_epoch"]
    assert 0 < reabre - time.time() <= config.CIRCUITO_REABERTURA_S
    assert config.CIRCUITO_REABERTURA_S == 300
    with pytest.raises(S.LLMCircuitoAberto):
        _chamar(Cliente(NORMAL))


def test_sonda_que_responde_fecha_o_disjuntor(capsys):
    _abrir_vencido()
    c = Cliente(NORMAL)
    resp = _chamar(c)                                    # a sonda PASSA
    assert c.n == 1 and resp.choices
    e = _estado()
    assert e["aberto"] is False and e["seguidas"] == 0
    assert "FECHADO" in capsys.readouterr().err
    _chamar(Cliente(NORMAL))                             # e o tráfego volta


def test_sonda_que_volta_sobrecarga_reabre_por_mais_um_prazo():
    _abrir_vencido()
    desde = _estado()["aberto_desde"]
    with pytest.raises(S.LLMSobrecarga):
        _chamar(Cliente(CORPO_FILA))                     # a sonda falha
    e = _estado()
    assert e["aberto"] is True
    assert config.CIRCUITO_REABERTURA_S - 5 < e["reabre_em_epoch"] - time.time() \
        <= config.CIRCUITO_REABERTURA_S
    assert e["aberto_desde"] == desde                    # a abertura é a mesma
    with pytest.raises(S.LLMCircuitoAberto):
        _chamar(Cliente(NORMAL))


# ===========================================================================
# 6. Falha por disjuntor aberto fica PENDENTE; reexecução retenta só ela
# ===========================================================================

def test_verificador_com_disjuntor_aberto_marca_pendente_e_reexecucao_retenta(tmp_path, monkeypatch):
    import verificador_impacto as vi

    _sobrecargas(3)
    c = Cliente(NORMAL)
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: c.sdk)
    arq = tmp_path / "v.jsonl"
    review = {"id": "r1", "slug": "f", "nivel": 4.0, "n_chars": 10, "texto": "t"}

    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, [review], arq=arq)
    reg = json.loads(arq.read_text(encoding="utf-8").splitlines()[0])
    assert reg["ok"] is False and reg["erro"].startswith("LLMCircuitoAberto")
    assert c.n == 0                                      # a rede nem foi tocada
    pend = vi._motivo_pendencia(reg["erro"])
    assert pend["motivo"] == "circuito_aberto"
    linha = vi.gerar_consenso_verificado(
        [{"slug": "f", "bucket": "b", "id": "r1", "eixos": [vi.EIXO]}], {},
        pendencias={"r1": pend})[0]
    assert linha["eixos"] == [vi.EIXO]                   # nada perdido
    assert linha["verificacao_pendente"]["motivo"] == "circuito_aberto"

    Path(S.CIRCUITO_ARQUIVO).unlink()                    # a fila voltou
    vi.rodar_passe(vi.VARIANTE_PRODUCAO, 1, [review], arq=arq)
    linhas = [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines()]
    assert [l["ok"] for l in linhas] == [False, True]    # só o pendente voltou
    assert c.n == 1


def test_classificacao_com_disjuntor_aberto_grava_ok_false(tmp_path, monkeypatch):
    import classificar_10 as c10
    import votacao_3 as v3

    amostra = {"taxonomia_id": c10.taxonomia_id(), "filmes": [{"slug": "f"}],
               "reviews": [{"slug": "f", "perfil": "misto", "bucket": "negativas",
                            "id": "r1", "nivel": 2.0, "n_chars": 10,
                            "texto": "t"}]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", {n: tmp_path / f"p{n}.jsonl"
                                          for n in (1, 2, 3, 4)})
    _sobrecargas(3)
    c = Cliente(NORMAL)
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: c.sdk)

    v3.classificar_passe(1)

    reg = json.loads((tmp_path / "p1.jsonl").read_text(encoding="utf-8"))
    assert reg["ok"] is False and "circuito_aberto" in reg["erro"]
    assert c.n == 0


# ===========================================================================
# O arquivo
# ===========================================================================

def test_arquivo_de_producao_mora_em_dados_lote_que_o_git_ignora():
    assert config.CIRCUITO_ARQUIVO == RAIZ / "dados" / "lote" / "circuito_deepseek.json"
    r = subprocess.run(["git", "check-ignore", "-q", str(config.CIRCUITO_ARQUIVO)],
                       cwd=RAIZ)
    assert r.returncode == 0


def test_escrita_atomica_nao_deixa_temporario_e_arquivo_corrompido_e_fechado():
    _sobrecargas(3)
    pasta = Path(S.CIRCUITO_ARQUIVO).parent
    assert [p.name for p in pasta.iterdir()] == ["circuito_deepseek.json"]
    json.loads(Path(S.CIRCUITO_ARQUIVO).read_text(encoding="utf-8"))
    Path(S.CIRCUITO_ARQUIVO).write_text("{corrompido", encoding="utf-8")
    _chamar(Cliente(NORMAL))                             # ilegível = fechado
