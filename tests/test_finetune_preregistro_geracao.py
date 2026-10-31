"""[2026-10-31] Geração da avaliação conforme `PREREGISTRO_AVALIACAO.md`, seção 2.

- temperatura 0,8 e seed 20261019 explícitas em CADA chamada; a variável
  `ESPECTRO24_OLLAMA_TEMPERATURE` aborta a geração;
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


def test_temperatura_explicita_sobrepoe_o_ambiente(monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_TEMPERATURE", "0.2")
    op = L._opcoes(3000, 8192, 20261019, 0.8)
    assert op["temperature"] == 0.8 and op["seed"] == 20261019
    assert L._opcoes(3000, 8192)["temperature"] == 0.2


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
    assert all(k["temperatura"] == 0.8 and k["seed"] == 20261019 for k in pedidos)
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
