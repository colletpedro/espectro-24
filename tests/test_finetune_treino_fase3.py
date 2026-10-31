"""[2026-10-31] Fase 3: kernel de treino e a escolha do modelo pelo sha do GGUF.

- `kernel_treino/treino.py` compila; a regra de escolha é a do TREINO_CONFIG
  (menor perda na validação na 4ª casa; empate → menos épocas); o sha do
  dataset é o do TREINO_CONFIG; o kernel lê o llama.cpp do meta.json;
- `gerar_sintese_teste.conferir_modelo` escolhe o modelo do Ollama pelo sha256
  do GGUF do log do kernel, recusa nome reimportado com outro GGUF e base e
  treinado com o mesmo nome."""
from __future__ import annotations

import ast
import json
import py_compile
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
KERNEL = RAIZ / "scripts" / "finetune" / "kaggle" / "kernel_treino" / "treino.py"
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import gerar_sintese_teste as G  # noqa: E402


def _funcoes(*nomes):
    """As funções puras do kernel, sem importá-lo (o import faz chdir para /tmp)."""
    arvore = ast.parse(KERNEL.read_text(encoding="utf-8"))
    ns = {}
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "CASAS_EMPATE" for t in no.targets):
            exec(compile(ast.Module([no], []), str(KERNEL), "exec"), ns)
        if isinstance(no, ast.FunctionDef) and no.name in nomes:
            exec(compile(ast.Module([no], []), str(KERNEL), "exec"), ns)
    return ns


def test_kernel_compila_e_traz_o_sha_do_treino_config():
    py_compile.compile(str(KERNEL), doraise=True)
    txt = KERNEL.read_text(encoding="utf-8")
    assert '"36f81ac1a48d11bdc1b7f1fc27e71fb3dd54ca063b29caa862ff4459ee45e53d"' in txt
    meta = json.loads((KERNEL.parent / "kernel-metadata.json").read_text())
    assert meta["is_private"] and meta["code_file"] == "treino.py"


def test_regra_de_escolha():
    ns = _funcoes("escolher", "curva_de_validacao")
    hist = [{"epoch": 1.0, "step": 35, "eval_loss": 0.81234}, {"loss": 0.9, "step": 36},
            {"epoch": 2.0, "step": 70, "eval_loss": 0.79001},
            {"epoch": 3.0, "step": 105, "eval_loss": 0.79004}]
    curva = ns["curva_de_validacao"](hist)
    assert [c["epoca"] for c in curva] == [1, 2, 3]
    assert ns["escolher"](curva)["epoca"] == 2          # 0,7900 = 0,7900: empate → menos épocas
    curva[2]["eval_loss"] = 0.7899
    assert ns["escolher"](curva)["epoca"] == 3


def _imp(pasta: Path, nome: str, sha: str, ts: str, e4: bool = True) -> None:
    pasta.mkdir(exist_ok=True)
    (pasta / f"importar_{nome}_{ts}.json").write_text(json.dumps(
        {"E4_importa_e_gera": e4, "importacao": {"gguf_sha256": sha, "nome_ollama": nome,
                                                 "modelfile_usado": "FROM x"}}))


def test_modelo_escolhido_pelo_sha(tmp_path, monkeypatch):
    v = tmp_path / "viab"
    monkeypatch.setattr(G, "VIABILIDADE", v)
    _imp(v, "espectro-qwen3-8b-base", "sha-base", "20261101_000000")
    _imp(v, "espectro-qwen3-8b-treinado", "sha-t", "20261105_000000")
    assert G.modelo_pelo_sha("sha-t") == ("espectro-qwen3-8b-treinado",
                                         "importar_espectro-qwen3-8b-treinado_20261105_000000.json")
    # o nome da base reimportado depois com OUTRO GGUF: recusa
    _imp(v, "espectro-qwen3-8b-base", "outro", "20261106_000000")
    with pytest.raises(SystemExit):
        G.modelo_pelo_sha("sha-base")


def test_base_e_treinado_nao_colidem(tmp_path, monkeypatch):
    v = tmp_path / "viab"
    monkeypatch.setattr(G, "VIABILIDADE", v)
    _imp(v, "espectro-x", "sha-base", "20261101_000000")
    _imp(v, "espectro-x", "sha-t", "20261105_000000")       # o treinado sobrescreveu a base
    lb = tmp_path / "base.json"
    lb.write_text(json.dumps({"gguf_arquivos": [{"nome": "a.Q4_K_M.gguf", "sha256": "sha-base"}],
                              "llama_cpp": {"commit": "c1"}}))
    lt = tmp_path / "t.json"
    lt.write_text(json.dumps({"gguf_arquivos": [{"nome": "a.Q4_K_M.gguf", "sha256": "sha-t"}],
                              "llama_cpp": {"commit": "c1"}}))
    with pytest.raises(SystemExit):
        G.conferir_modelo("treinado", None, lt, lb)
