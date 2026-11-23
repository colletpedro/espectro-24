"""Síntese de produção pelo modelo local (`sintese_local.py`): servidor Ollama FALSO de verdade
(`http.server` em porta livre do loopback). Zero rede externa, zero custo."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from espectro24 import sintese_local as SL
from espectro24 import synthesize as S
from espectro24.local_ollama import LLMLocalFalhou

SHA = SL.GGUF_SHA256
OUTRO = "0" * 64


def _modelfile(sha, windows=False):
    caminho = (f"C:\\Users\\x\\.ollama\\models\\blobs\\sha256-{sha}" if windows
               else f"/root/.ollama/models/blobs/sha256-{sha}")
    return f"# Modelfile\nFROM {caminho}\nTEMPLATE x\n"


class Servidor:
    def __init__(self, modelos):
        self.modelos, self.chats, self.resposta = modelos, [], '{"temas": [], "observacao_geral": "ok"}'
        dono = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, corpo, status=200):
                b = json.dumps(corpo).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                self._json({"models": [{"name": n} for n in dono.modelos]})

            def do_POST(self):
                corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/api/show":
                    sha = dono.modelos.get(corpo["model"])
                    return self._json({"modelfile": _modelfile(sha)}) if sha else self._json({}, 404)
                dono.chats.append(corpo)
                self._json({"model": corpo["model"], "message": {"content": dono.resposta},
                            "done_reason": "stop", "prompt_eval_count": 10, "eval_count": 5,
                            "prompt_eval_duration": 2_000_000_000, "eval_duration": 1_000_000_000,
                            "load_duration": 0, "total_duration": 3_000_000_000})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def parar(self):
        self.httpd.shutdown()


@pytest.fixture
def ollama(monkeypatch):
    SL._cache_modelo.clear()
    SL.REGISTRO.clear()
    for v in (SL.VAR_TEMPERATURA, SL.VAR_NUM_CTX, SL.VAR_TOKENIZER, SL.VAR_GGUF_SHA):
        monkeypatch.delenv(v, raising=False)
    srv = Servidor({"espectro-qwen3-8b-base:latest": OUTRO, "espectro-qwen3-8b-treinado:latest": SHA})
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", srv.url)
    yield srv
    srv.parar()


def test_sha_do_modelfile_no_linux_e_no_windows():
    assert SL.sha_do_modelfile(_modelfile(SHA)) == SHA
    assert SL.sha_do_modelfile(_modelfile(SHA, windows=True)) == SHA
    assert SL.sha_do_modelfile("FROM qwen3:8b\n") is None


def test_o_modelo_e_escolhido_pelo_sha_e_nao_pelo_nome(ollama):
    ollama.modelos = {"qualquer-nome:latest": SHA, "espectro-qwen3-8b-treinado:latest": OUTRO}
    assert SL.modelo_pelo_sha() == "qualquer-nome:latest"


def test_sem_modelo_com_o_sha_recusa(ollama):
    ollama.modelos = {"espectro-qwen3-8b-treinado:latest": OUTRO}
    with pytest.raises(SL.ModeloLocalIndisponivel, match="e488697e"):
        SL.client_call_local("s", "u", SL.MODELO_PADRAO)
    assert not ollama.chats


def test_chamada_leva_a_configuracao_do_desvio_p01(ollama):
    texto = SL.client_call_local("system", "user", "espectro-qwen3-8b-treinado")
    assert texto == ollama.resposta
    c = ollama.chats[0]
    assert c["model"] == "espectro-qwen3-8b-treinado:latest"
    assert c["format"] == "json" and c["stream"] is False and c["think"] is False
    assert [m["role"] for m in c["messages"]] == ["system", "user"]
    op = c["options"]
    assert (op["temperature"], op["top_p"], op["top_k"], op["min_p"], op["repeat_penalty"]) == \
        (0.7, 0.8, 20, 0.0, 1.0)
    assert op["seed"] == 20261019 and op["num_predict"] == 3000
    r = SL.REGISTRO[0]
    assert r["sha_conferido"] and r["gguf_sha256"] == SHA and r["num_ctx_metodo"] == "estimado"
    assert r["modelo_efetivo"] == "espectro-qwen3-8b-treinado:latest" and r["latencia_s"] >= 0


def test_num_ctx_pela_regra_do_gate_0():
    assert SL.num_ctx_da_chamada(1000) == 5120               # (1000 + 3000) × 1,10 = 4400 → 5 × 1024
    assert SL.num_ctx_da_chamada(18_000) == 23_552            # 23.100 → 23 × 1024
    assert SL.num_ctx_da_chamada(0) % 1024 == 0


def test_estimativa_de_tokens_nunca_fica_abaixo_do_medido():
    # MEDIDO nos 105 prompts do C22: caracteres/token ≥ 2,96. A estimativa usa 2,8.
    assert SL.CARACTERES_POR_TOKEN_CONSERVADOR < 2.96
    n, metodo = SL.tokens_do_prompt("a" * 2800, "b" * 2800)
    assert metodo == "estimado" and n >= 5600 / 2.96


def test_num_ctx_fixo_pelo_ambiente(ollama, monkeypatch):
    monkeypatch.setenv(SL.VAR_NUM_CTX, "9216")
    SL.client_call_local("s", "u", None)
    assert ollama.chats[0]["options"]["num_ctx"] == 9216 and SL.REGISTRO[0]["num_ctx_metodo"] == "fixo"


def test_temperatura_do_ambiente_e_recusada(ollama, monkeypatch):
    monkeypatch.setenv(SL.VAR_TEMPERATURA, "0.2")
    with pytest.raises(SL.ModeloLocalIndisponivel, match="DESVIO_P01"):
        SL.client_call_local("s", "u", None)
    assert not ollama.chats


def test_outro_nome_pedido_vale_como_esta_e_sai_marcado(ollama):
    ollama.modelos["outro:latest"] = OUTRO
    SL.client_call_local("s", "u", "outro:latest")
    assert ollama.chats[0]["model"] == "outro:latest" and SL.REGISTRO[0]["sha_conferido"] is False
    assert SL.REGISTRO[0]["gguf_sha256"] is None


def test_servidor_fora_do_ar_levanta_com_latencia(monkeypatch):
    SL._cache_modelo.clear()
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", "http://127.0.0.1:9")
    with pytest.raises(LLMLocalFalhou):
        SL.client_call_local("s", "u", None)


def test_integrado_ao_synthesize_bucket(ollama):
    from tests.test_fallback_quantidade import _bucket  # noqa: F401  (mesmo bucket de teste)
    ollama.resposta = json.dumps({"temas": [{"tema": "Trilha", "mencoes_aproximadas": 3,
                                             "exemplo_parafraseado": "Muitos elogiam a trilha."}],
                                  "observacao_geral": "Este grupo elogia a trilha."}, ensure_ascii=False)
    b = S.synthesize_bucket(_bucket(), provider="local")
    assert b.temas[0].exemplo_parafraseado == "Elogiam a trilha." or "Muitos" not in b.temas[0].exemplo_parafraseado
    assert b.quantidade_fallback is None and len(ollama.chats) == 1
