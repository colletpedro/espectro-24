"""[2026-10-08] Provider `local` (Ollama) — com um SERVIDOR FALSO de verdade.

Zero rede externa e zero custo: um `http.server` numa thread, em porta livre
do loopback, fala o formato de `/api/chat` e `/api/tags` do Ollama. O que se
prova:
1. a requisição leva o schema em `format`, `stream: false`, `think: false`,
   system + user nessa ordem, `num_ctx`;
2. a resposta vira o formato do gate, com custo zero, provider/modelo efetivo
   e o tempo separado em leitura do prompt × geração (ns → s);
3. o endereço e o prazo vêm do ambiente; padrão é localhost:11434;
4. falha (HTTP 500, prazo, servidor fora do ar) levanta `LLMLocalFalhou` COM
   a latência de parede;
5. 400 por causa de `think` refaz a chamada sem o campo;
6. os schemas só aceitam eixos da taxonomia;
7. `PROVIDER_POR_ESTAGIO` não foi tocado;
8. o gate com `--provider local`: grava em `local/<modelo>/`, chama em
   sequência na ordem do gabarito, registra provider/modelo/tempo, registra
   a falha com a latência, e recusa `--modelo` ausente.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import config, local_ollama  # noqa: E402
from espectro24.local_ollama import LLMLocalFalhou  # noqa: E402

import gate_gemini_classificacao as G  # noqa: E402


class OllamaFalso:
    """Servidor de verdade; `respostas` é a fila (dict de corpo, ou int de
    status HTTP, ou float de espera em segundos antes de responder 200)."""

    def __init__(self):
        self.requisicoes: list[dict] = []
        self.respostas: list = []
        self.modelos = ["qwen3:8b"]
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):  # silencioso
                pass

            def _enviar(self, status, corpo):
                b = json.dumps(corpo).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                assert self.path == "/api/tags"
                self._enviar(200, {"models": [{"name": n} for n in fake.modelos]})

            def do_POST(self):
                assert self.path == "/api/chat"
                n = int(self.headers["Content-Length"])
                fake.requisicoes.append(json.loads(self.rfile.read(n)))
                r = fake.respostas.pop(0) if fake.respostas else _corpo_ok()
                if isinstance(r, int):
                    return self._enviar(r, {"error": f"falha {r}"})
                if isinstance(r, float):
                    time.sleep(r)
                    r = _corpo_ok()
                self._enviar(200, r)

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fechar(self):
        self.srv.shutdown()
        self.srv.server_close()


def _corpo_ok(conteudo: dict | None = None, **extra) -> dict:
    c = conteudo if conteudo is not None else {"eixos": ["ritmo"], "temas_livres": []}
    base = {"model": "qwen3:8b", "message": {"role": "assistant",
                                              "content": json.dumps(c)},
            "done": True, "done_reason": "stop",
            "total_duration": 12_500_000_000, "load_duration": 2_000_000_000,
            "prompt_eval_count": 311, "prompt_eval_duration": 4_250_000_000,
            "eval_count": 27, "eval_duration": 6_000_000_000}
    base.update(extra)
    return base


@pytest.fixture
def ollama(monkeypatch):
    f = OllamaFalso()
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", f.url)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("ESPECTRO24_OLLAMA_PRAZO_S", raising=False)
    yield f
    f.fechar()


def _chamar(**kw):
    args = dict(estagio="classificacao", modelo="qwen3:8b",
                schema=local_ollama.schema_classificacao(["ritmo", "livre"]))
    args.update(kw)
    return local_ollama.resposta_json_local("SISTEMA", "usuario", **args)


# --- requisição e resposta ---------------------------------------------------

def test_requisicao_leva_schema_sem_stream_e_sem_thinking(ollama):
    schema = local_ollama.schema_classificacao(["ritmo", "livre"])
    _chamar(schema=schema)
    req = ollama.requisicoes[0]
    assert req["model"] == "qwen3:8b"
    assert req["stream"] is False
    assert req["format"] == schema
    assert req["think"] is False
    assert [m["role"] for m in req["messages"]] == ["system", "user"]
    assert req["messages"][0]["content"] == "SISTEMA"
    assert req["messages"][1]["content"] == "usuario"
    assert req["options"]["num_ctx"] == local_ollama.NUM_CTX_PADRAO
    assert req["options"]["num_predict"] == config.FALLBACK_CONTEUDO_MAX_TOKENS_JSON
    assert "temperature" not in req["options"]


def test_resposta_tem_custo_zero_provider_modelo_e_tempo_separado(ollama):
    r = _chamar()
    assert json.loads(r["texto"]) == {"eixos": ["ritmo"], "temas_livres": []}
    assert r["provider"] == "local"
    assert r["modelo"] == "qwen3:8b"
    assert r["modelo_efetivo"] == "qwen3:8b"
    assert r["custo_usd"] == 0.0
    assert r["leitura_prompt_s"] == 4.25
    assert r["geracao_s"] == 6.0
    assert r["carga_s"] == 2.0
    assert r["total_s"] == 12.5
    assert r["prompt_eval_count"] == 311 and r["eval_count"] == 27
    assert r["uso"] == {"prompt_tokens": 311, "completion_tokens": 27}
    assert r["finish_reason"] == "stop"
    assert r["latencia_s"] >= 0
    assert r["thinking_tokens"] == 0


def test_modelo_efetivo_e_o_que_o_servidor_devolve(ollama):
    ollama.respostas.append(_corpo_ok(model="qwen3:8b-q4_K_M"))
    assert _chamar()["modelo_efetivo"] == "qwen3:8b-q4_K_M"


def test_temperatura_opcional_vem_do_ambiente(ollama, monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_TEMPERATURE", "0")
    monkeypatch.setenv("ESPECTRO24_OLLAMA_NUM_CTX", "4096")
    _chamar()
    op = ollama.requisicoes[0]["options"]
    assert op["temperature"] == 0.0 and op["num_ctx"] == 4096


# --- configuração ------------------------------------------------------------

def test_padrao_e_localhost_11434(monkeypatch):
    monkeypatch.delenv("ESPECTRO24_OLLAMA_URL", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert local_ollama.url_base() == "http://localhost:11434"


def test_url_aceita_ollama_host_sem_esquema(monkeypatch):
    monkeypatch.delenv("ESPECTRO24_OLLAMA_URL", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "192.168.0.7:11434/")
    assert local_ollama.url_base() == "http://192.168.0.7:11434"


def test_variavel_propria_vence_a_do_ollama(monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", "http://a:1")
    monkeypatch.setenv("OLLAMA_HOST", "http://b:2")
    assert local_ollama.url_base() == "http://a:1"


def test_prazo_padrao_e_maior_que_o_da_nuvem(monkeypatch):
    monkeypatch.delenv("ESPECTRO24_OLLAMA_PRAZO_S", raising=False)
    assert local_ollama.prazo_s() == local_ollama.PRAZO_PADRAO_S == 600.0
    assert local_ollama.prazo_s() > config.LLM_TIMEOUT_MS / 1000
    monkeypatch.setenv("ESPECTRO24_OLLAMA_PRAZO_S", "900")
    assert local_ollama.prazo_s() == 900.0


# --- falhas ------------------------------------------------------------------

def test_http_500_levanta_com_latencia(ollama):
    ollama.respostas.append(500)
    with pytest.raises(LLMLocalFalhou) as e:
        _chamar()
    assert "HTTP 500" in str(e.value)
    assert e.value.latencia_s >= 0


def test_prazo_estourado_levanta_com_latencia_de_parede(ollama):
    ollama.respostas.append(2.0)
    t0 = time.monotonic()
    with pytest.raises(LLMLocalFalhou) as e:
        _chamar(prazo=0.3)
    assert "prazo" in str(e.value)
    assert 0.25 <= e.value.latencia_s < 1.9
    assert time.monotonic() - t0 < 1.9


def test_servidor_fora_do_ar_levanta(monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", "http://127.0.0.1:1")
    with pytest.raises(LLMLocalFalhou):
        _chamar()


def test_400_por_causa_de_think_refaz_sem_o_campo(ollama):
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        corpo = json.loads(self.rfile.read(n))
        ollama.requisicoes.append(corpo)
        if "think" in corpo:
            return self._enviar(400, {"error": "model does not support think"})
        self._enviar(200, _corpo_ok())

    ollama.srv.RequestHandlerClass.do_POST = do_POST
    r = _chamar()
    assert len(ollama.requisicoes) == 2
    assert "think" in ollama.requisicoes[0] and "think" not in ollama.requisicoes[1]
    assert r["provider"] == "local"


# --- schemas -----------------------------------------------------------------

def test_schema_de_classificacao_so_aceita_eixos_da_taxonomia():
    s = local_ollama.schema_classificacao({"ritmo", "livre", "atuacao"})
    enum = s["properties"]["eixos"]["items"]["enum"]
    assert enum == ["atuacao", "livre", "ritmo"]
    assert s["required"] == ["eixos", "temas_livres"]


def test_schema_de_classificacao_cobre_exatamente_a_taxonomia_de_producao():
    s = local_ollama.schema_classificacao(G.EIXOS_VALIDOS)
    assert set(s["properties"]["eixos"]["items"]["enum"]) == set(G.EIXOS) | {"livre"}


def test_schema_do_verificador_tem_os_tres_campos_do_prompt():
    s = local_ollama.SCHEMA_VERIFICADOR
    assert list(s["properties"]) == ["alvo", "confirma", "frase"]
    assert s["properties"]["alvo"]["enum"] == ["espectador", "filme"]
    assert s["properties"]["confirma"]["type"] == "boolean"


def test_provider_por_estagio_nao_foi_tocado():
    assert config.PROVIDER_POR_ESTAGIO["classificacao"] == "deepseek"
    assert "local" not in set(config.PROVIDER_POR_ESTAGIO.values())


# --- o gate com --provider local ----------------------------------------------

@pytest.fixture
def gate_local(tmp_path, monkeypatch, ollama):
    monkeypatch.setattr(G, "SAIDA_BASE", tmp_path)
    for nome in ("SAIDA", "ARQ_RELATORIO", "PROVIDER_GATE", "MODELO_LOCAL"):
        monkeypatch.setattr(G, nome, getattr(G, nome))
    G._configurar("local", "qwen3:8b")
    reviews = [{"id": f"viewing:{i}", "bucket": "positivas", "nivel": 4.0,
                "n_chars": 200, "texto": f"texto {i}"} for i in range(1, 4)]
    monkeypatch.setattr(G, "_reviews", lambda: reviews)
    monkeypatch.setattr(G, "_carregar_env", lambda: None)
    return tmp_path, reviews


def test_gate_local_grava_em_local_modelo(gate_local):
    tmp, _ = gate_local
    assert G.SAIDA == tmp / "local" / "qwen3-8b"
    assert G.ARQ_RELATORIO == tmp / "local" / "qwen3-8b" / "gate.json"


def test_slug_do_modelo_nao_tem_caractere_proibido_no_windows():
    s = G._slug_modelo("hf.co/org/modelo:Q4_K_M")
    assert not set(':/\\*?"<>|') & set(s)


def test_gate_local_roda_em_sequencia_na_ordem_do_gabarito_e_grava_tempo(gate_local, ollama):
    _, reviews = gate_local
    G._rodar(G._arq_class(1), reviews, "SISTEMA", G._user_classificacao,
             G._interpretar_classificacao, "classificacao", "passe 1",
             concorrencia=8, schema=local_ollama.schema_classificacao(G.EIXOS_VALIDOS))
    textos = [r["messages"][1]["content"] for r in ollama.requisicoes]
    assert [t.split("\n\n", 1)[1] for t in textos] == ["texto 1", "texto 2", "texto 3"]
    # o system prompt (prefixo) é idêntico em todas
    assert {r["messages"][0]["content"] for r in ollama.requisicoes} == {"SISTEMA"}
    regs = G._linhas(G._arq_class(1))
    assert [r["id"] for r in regs] == [r["id"] for r in reviews]
    for r in regs:
        assert r["ok"] and r["provider"] == "local" and r["modelo"] == "qwen3:8b"
        assert r["modelo_efetivo"] == "qwen3:8b"
        assert r["custo_usd"] == 0.0
        assert r["leitura_prompt_s"] == 4.25 and r["geracao_s"] == 6.0
        assert r["eixos"] == ["ritmo"]


def test_gate_local_registra_falha_com_provider_modelo_e_latencia(gate_local, ollama):
    _, reviews = gate_local
    ollama.respostas.append(500)
    G._rodar(G._arq_class(1), reviews[:1], "SISTEMA", G._user_classificacao,
             G._interpretar_classificacao, "classificacao", "passe 1",
             schema=local_ollama.schema_classificacao(G.EIXOS_VALIDOS))
    (r,) = G._linhas(G._arq_class(1))
    assert r["ok"] is False and "HTTP 500" in r["erro"]
    assert r["provider"] == "local" and r["modelo"] == "qwen3:8b"
    assert r["custo_usd"] == 0.0 and r["latencia_s"] is not None
    # a reexecução retenta só a que não tem ok:true
    G._rodar(G._arq_class(1), reviews[:1], "SISTEMA", G._user_classificacao,
             G._interpretar_classificacao, "classificacao", "passe 1",
             schema=local_ollama.schema_classificacao(G.EIXOS_VALIDOS))
    assert [r["ok"] for r in G._linhas(G._arq_class(1))] == [False, True]


def test_gate_local_verificador_usa_o_schema_do_verificador(gate_local, ollama):
    _, reviews = gate_local
    ollama.respostas.append(_corpo_ok({"alvo": "filme", "confirma": False, "frase": "x"}))
    G._rodar(G._arq_verif(1), reviews[:1], "SIS", G._user_verificador,
             G._interpretar_verificador, "verificador", "V2 passe 1",
             schema=local_ollama.SCHEMA_VERIFICADOR)
    assert ollama.requisicoes[0]["format"] == local_ollama.SCHEMA_VERIFICADOR
    (r,) = G._linhas(G._arq_verif(1))
    assert r["confirma"] is False and r["alvo"] == "filme"


def test_gate_local_exige_modelo(monkeypatch):
    for nome in ("SAIDA", "ARQ_RELATORIO", "PROVIDER_GATE", "MODELO_LOCAL"):
        monkeypatch.setattr(G, nome, getattr(G, nome))
    with pytest.raises(SystemExit):
        G._configurar("local", None)


def test_gate_gemini_recusa_modelo(monkeypatch):
    with pytest.raises(SystemExit):
        G._configurar("gemini", "qwen3:8b")


def test_gate_gemini_continua_em_gemini_por_padrao():
    assert G.PROVIDER_GATE == "gemini"
    assert G.SAIDA.name == "gemini"


def test_modelo_nao_instalado_falha_cedo_com_a_lista(gate_local, ollama, monkeypatch):
    ollama.modelos = ["outro:7b"]
    with pytest.raises(SystemExit) as e:
        G._exigir_modelo_instalado()
    assert "ollama pull qwen3:8b" in str(e.value)
    ollama.modelos = ["qwen3:8b"]
    G._exigir_modelo_instalado()  # não levanta


def test_custo_local_e_zero_e_resume_o_tempo(gate_local, ollama):
    _, reviews = gate_local
    G._rodar(G._arq_class(1), reviews, "SISTEMA", G._user_classificacao,
             G._interpretar_classificacao, "classificacao", "passe 1",
             schema=local_ollama.schema_classificacao(G.EIXOS_VALIDOS))
    c = G._custo_local([G._arq_class(1)])
    assert c["usd"] == 0.0 and c["n_chamadas"] == 3
    assert c["tempo_local"]["leitura_prompt_s"]["media"] == 4.25
    assert c["tempo_local"]["geracao_s"]["max"] == 6.0
    assert c["modelo_efetivo"] == {"qwen3:8b": 3}


# --- o critério de parada, ponta a ponta (sem chamada) -------------------------

def _copiar_como_local(destino: Path, degradar: bool) -> None:
    """Usa os passes do DeepSeek que estão em disco como se fossem a saída do
    modelo local: ΔF1 = 0 em todo eixo. `degradar` esvazia os eixos."""
    destino.mkdir(parents=True, exist_ok=True)
    for n in (1, 2, 3):
        for origem, nome in ((G.DIR_DEEPSEEK_CLASS / f"A_regra_passe_{n}.jsonl",
                              f"classificacao_passe_{n}.jsonl"),
                             (G.DIR_DEEPSEEK_VERIF / f"V2_alvo_passe_{n}.jsonl",
                              f"V2_alvo_passe_{n}.jsonl")):
            linhas = []
            for l in origem.read_text(encoding="utf-8").splitlines():
                if not l.strip():
                    continue
                r = json.loads(l)
                if degradar and "eixos" in r:
                    r["eixos"] = ["livre"]
                linhas.append(json.dumps(r, ensure_ascii=False))
            (destino / nome).write_text("\n".join(linhas) + "\n", encoding="utf-8")


@pytest.mark.parametrize("degradar,parar", [(False, False), (True, True)])
def test_gate_local_aplica_o_mesmo_criterio_de_parada(gate_local, degradar, parar):
    _copiar_como_local(G.SAIDA, degradar)
    G.cmd_comparar()
    rel = json.loads((G.SAIDA / "gate.json").read_text(encoding="utf-8"))
    assert rel["provider"] == "local" and rel["lado"] == "local"
    assert rel["gate"]["parar"] is parar
    assert "local" in rel["tabelas"]["producao_consenso_mais_v2_passe1"]
    assert rel["custo"]["usd"] == 0.0
    assert rel["criterio"]["limiar_delta_f1"] == -0.10
    assert rel["criterio"]["limiar_falha_primeira_tentativa"] == 0.02
    if not parar:
        assert all(v["delta_f1"] == 0 for v in rel["gate_por_eixo"].values())
