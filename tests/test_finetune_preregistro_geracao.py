"""[2026-10-31] Geração da avaliação conforme `PREREGISTRO_AVALIACAO.md`, seção 2.

- amostragem do DESVIO_P01 (temperature 0,7, top_p 0,8, top_k 20, min_p 0,
  repeat_penalty 1,0) e seed 20261019 explícitas em CADA chamada, até o corpo
  da requisição ao Ollama; a variável `ESPECTRO24_OLLAMA_TEMPERATURE` aborta
  a geração; o hash do juiz não muda;
- a retentativa é a de produção (`synthesize_bucket` com o cliente local
  injetado): JSON inválido ganha UMA nova chamada, e o reforço de validação vai
  só no system;
- par derrubado pela guarda de RAM duas vezes fica fora por memória e não é
  refeito."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import gerar_sintese_teste as G  # noqa: E402
from espectro24 import local_ollama as L  # noqa: E402
from espectro24.models import BucketResult, LevelResult, Review  # noqa: E402
from espectro24.synthesize import synthesize_bucket  # noqa: E402

VALIDO = ('{"bucket":"positivas","temas":[{"tema":"fotografia","mencoes_aproximadas":3,'
          '"n_reviews_analisadas":5,"exemplo_parafraseado":"Elogios à fotografia."}],'
          '"observacao_geral":"Este grupo elogia a fotografia."}')


def _bucket(n=5):
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i} completa",
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text=f"review {i} completa") for i in range(n)]
    return BucketResult(nome="positivas", alvo=30, modo="reduzido", niveis=[lvl])


def test_temperatura_do_ambiente_aborta(monkeypatch):
    monkeypatch.setenv(G.VAR_TEMPERATURA, "")
    with pytest.raises(SystemExit):
        G.recusar_temperatura_do_ambiente()
    monkeypatch.delenv(G.VAR_TEMPERATURA)
    G.recusar_temperatura_do_ambiente()


def test_amostragem_explicita_sobrepoe_o_ambiente(monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_TEMPERATURE", "0.2")
    op = L._opcoes(3000, 8192, 20261019, G.AMOSTRAGEM)
    assert op["temperature"] == 0.7 and op["seed"] == 20261019
    assert L._opcoes(3000, 8192)["temperature"] == 0.2


def test_amostragem_do_desvio_p01():
    assert G.AMOSTRAGEM == {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
                            "repeat_penalty": 1.0}
    assert G.SEED == 20261019


def test_os_seis_parametros_chegam_a_requisicao(monkeypatch):
    from test_provider_local import OllamaFalso, _corpo_ok
    f = OllamaFalso()
    monkeypatch.setenv("ESPECTRO24_OLLAMA_URL", f.url)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    f.respostas = [_corpo_ok({"x": 1}), _corpo_ok({"x": 1})]
    try:
        tentativas = []
        cli = G.cliente_registrado(L.resposta_json_local, "S", "m", 9216, tentativas)
        cli("S", "U", "m")
        cli("S" + "reforço", "U", "m")
    finally:
        f.fechar()
    for req in f.requisicoes:
        op = req["options"]
        assert {k: op[k] for k in G.AMOSTRAGEM} == G.AMOSTRAGEM
        assert op["seed"] == 20261019 and op["num_ctx"] == 9216 and op["num_predict"] == 3000
        assert req["think"] is False
    assert [t["reforco"] for t in tentativas] == [False, True]


def test_hash_do_juiz_nao_muda():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import juiz_bullets_v2 as J
    assert J.config_sha256() == "44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669"


def test_retentativa_de_producao_com_temperatura_e_seed_do_preregistro():
    pedidos, tentativas = [], []

    def chamar(system, user, **kw):
        pedidos.append(kw)
        return {"texto": "isto não é JSON" if len(pedidos) == 1 else VALIDO}

    b = _bucket()
    s = "SYSTEM"
    final = synthesize_bucket(b, model="m", client_call=G.cliente_registrado(
        chamar, s, "m", 8192, tentativas))
    assert len(pedidos) == 2                          # chamada + 1 retentativa de JSON
    assert all(k["amostragem"] == G.AMOSTRAGEM and k["seed"] == 20261019 for k in pedidos)
    assert all(k["num_ctx"] == 8192 and k["think"] == "false" for k in pedidos)
    assert [t["texto"] for t in tentativas] == ["isto não é JSON", VALIDO]
    bf = G.bucket_final(final)
    assert bf["temas"][0]["tema"] == "fotografia" and bf["n_analisadas"] == 5


def test_fora_por_memoria_nao_e_refeito(tmp_path):
    arq = tmp_path / "x__positivas.json"
    assert not G.ja_feito(arq) and G.abortos_anteriores(arq) == 0
    arq.write_text(json.dumps({"ok": False, "abortos_memoria": 1, "fora_por_memoria": False}))
    assert not G.ja_feito(arq) and G.abortos_anteriores(arq) == 1
    arq.write_text(json.dumps({"ok": False, "abortos_memoria": 2, "fora_por_memoria": True}))
    assert G.ja_feito(arq)
    assert G.MAX_ABORTOS_MEMORIA == 2
