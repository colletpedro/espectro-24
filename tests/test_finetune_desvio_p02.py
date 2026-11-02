"""[2026-11-02] DESVIO_P02: a `prova_fusao` falsa da base, aceita com exceção EXATA.

- `comum.prova_fusao_aceita`: aceita `ok` e o padrão exato (1 tensor, o
  embed_tokens, max_abs 0,029541015625); reprova 2 tensores, outro tensor e
  outro max_abs;
- `gerar_sintese_teste.conferir_modelo`: a base com o padrão exato passa;
  o treinado exige `tensores.json` com a embedding e o lm_head da base;
- `viabilidade_ollama.conferir_treinados`: o import aborta antes de importar um
  treinado com embedding/lm_head diferentes dos da base;
- `treino.linhas_diferentes` (só com torch instalado)."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import comum as K  # noqa: E402
import gerar_sintese_teste as G  # noqa: E402
import viabilidade_ollama as V  # noqa: E402

# o padrão do log da base v2 (finetune/kaggle/base_saida_qwen3/.../log.json)
SHARDS = {f"model-0000{i}-of-00004.safetensors": {"chaves_iguais": True} for i in range(1, 5)}
PROVA_EXATA = {"tensores": 399, "iguais": 398, "n_diferentes": 1, "ok": False, "shards": SHARDS,
               "diferentes": [{"tensor": "model.embed_tokens.weight",
                               "dtype": ["torch.bfloat16", "torch.bfloat16"],
                               "max_abs": 0.029541015625}]}


def _prova(**mudar) -> dict:
    p = copy.deepcopy(PROVA_EXATA)
    p.update(mudar)
    return p


def test_aceita_ok_e_o_padrao_exato():
    assert K.prova_fusao_aceita({"ok": True})
    assert K.prova_fusao_aceita(PROVA_EXATA)


def test_o_log_real_da_base_e_aceito():
    log = RAIZ / "finetune" / "kaggle" / "base_saida_qwen3" / "base" / "qwen3-8b-base__14336" / "log.json"
    if not log.exists():                       # o log está no branch finetune
        pytest.skip("log da base v2 não está nesta árvore")
    assert K.prova_fusao_aceita(K.ler_json(log)["prova_fusao"])


def test_reprova_dois_tensores():
    dois = PROVA_EXATA["diferentes"] + [{"tensor": "lm_head.weight", "max_abs": 0.01}]
    assert not K.prova_fusao_aceita(_prova(n_diferentes=2, diferentes=dois))
    # contagem e lista incoerentes também reprovam
    assert not K.prova_fusao_aceita(_prova(n_diferentes=2))
    assert not K.prova_fusao_aceita(_prova(diferentes=dois))


def test_reprova_outro_tensor():
    outro = [{**PROVA_EXATA["diferentes"][0], "tensor": "lm_head.weight"}]
    assert not K.prova_fusao_aceita(_prova(diferentes=outro))


def test_reprova_outro_max_abs():
    for m in (0.0295, 0.029541015626, 0.0, None):
        outro = [{**PROVA_EXATA["diferentes"][0], "max_abs": m}]
        assert not K.prova_fusao_aceita(_prova(diferentes=outro))


def test_reprova_chaves_diferentes_ou_prova_vazia():
    shards = {**SHARDS, "model-00004-of-00004.safetensors": {"chaves_iguais": False}}
    assert not K.prova_fusao_aceita(_prova(shards=shards))
    assert not K.prova_fusao_aceita(_prova(shards={}))
    assert not K.prova_fusao_aceita(None)
    assert not K.prova_fusao_aceita({"ok": False, "erro": "revisões dos shards"})


# ---------------------------------------------------------------------------
# gerar_sintese_teste: base com o padrão exato; treinado com a embedding da base
# ---------------------------------------------------------------------------

def _log(pasta: Path, sha: str = "abc", **extra) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    p = pasta / "log.json"
    p.write_text(json.dumps({"gguf_arquivos": [{"nome": "Qwen3-8B.Q4_K_M.gguf", "sha256": sha},
                                               {"nome": "Modelfile", "sha256": "x"}],
                             "llama_cpp_depois": {"ok": True}, **extra}))
    return p


def _tensores(pasta: Path, **shas) -> Path:
    t = {**K.SHA_VOCAB_BASE, **shas}
    p = pasta / "tensores.json"
    p.write_text(json.dumps({"n_tensores": 3, "tensores": [
        {"nome": n, "tipo": "Q4_K", "sha256": s} for n, s in t.items()]
        + [{"nome": "blk.0.attn_q.weight", "tipo": "Q4_K", "sha256": "projecao"}]}))
    return p


def _importacao(pasta: Path, nome: str, sha: str, ts: str = "20261102_000000") -> None:
    pasta.mkdir(exist_ok=True)
    (pasta / f"importar_{nome}_{ts}.json").write_text(json.dumps(
        {"E4_importa_e_gera": True, "importacao": {"gguf_sha256": sha, "modelfile_usado": "FROM x",
                                                   "nome_ollama": nome}}))


def test_gerar_aceita_a_base_com_o_padrao_exato_e_reprova_outro(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "VIABILIDADE", tmp_path / "viab")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-base", "abc")
    ok = _log(tmp_path / "a", prova_adaptador={"B_zero": True}, prova_fusao=PROVA_EXATA)
    assert G.conferir_modelo("base", "espectro-qwen3-8b-base", ok, None)["gguf_sha256"] == "abc"
    outro = [{**PROVA_EXATA["diferentes"][0], "max_abs": 0.03}]
    ruim = _log(tmp_path / "b", prova_adaptador={"B_zero": True}, prova_fusao=_prova(diferentes=outro))
    with pytest.raises(SystemExit, match="DESVIO_P02"):
        G.conferir_modelo("base", "espectro-qwen3-8b-base", ruim, None)


def _treinado(tmp_path: Path, monkeypatch, **shas_treinado):
    monkeypatch.setattr(G, "VIABILIDADE", tmp_path / "viab")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-treinado", "sha-ft")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-base", "sha-base")
    base = _log(tmp_path / "base", sha="sha-base", llama_cpp={"commit": "c1"})
    ft = _log(tmp_path / "ft", sha="sha-ft", llama_cpp={"commit": "c1"})
    _tensores(tmp_path / "base")
    _tensores(tmp_path / "ft", **shas_treinado)
    return ft, base


def test_gerar_treinado_com_a_embedding_da_base_passa(tmp_path, monkeypatch):
    ft, base = _treinado(tmp_path, monkeypatch)
    r = G.conferir_modelo("treinado", "espectro-qwen3-8b-treinado", ft, base)
    assert r["gguf_sha256"] == "sha-ft"


@pytest.mark.parametrize("nome", ["token_embd.weight", "output.weight"])
def test_gerar_treinado_com_embedding_ou_lm_head_diferente_aborta(tmp_path, monkeypatch, nome):
    ft, base = _treinado(tmp_path, monkeypatch, **{nome: "outro"})
    with pytest.raises(SystemExit, match="DESVIO_P02"):
        G.conferir_modelo("treinado", "espectro-qwen3-8b-treinado", ft, base)


def test_gerar_treinado_sem_tensores_aborta(tmp_path, monkeypatch):
    ft, base = _treinado(tmp_path, monkeypatch)
    (tmp_path / "ft" / "tensores.json").unlink()
    with pytest.raises(SystemExit, match="tensores.json"):
        G.conferir_modelo("treinado", "espectro-qwen3-8b-treinado", ft, base)


def test_vocab_confere_tambem_a_base_dada():
    t = json.loads(_tensores_dict())
    assert K.conferir_vocab_igual_base(t, t) == K.SHA_VOCAB_BASE
    outra = json.loads(_tensores_dict(**{"output.weight": "x"}))
    with pytest.raises(SystemExit, match="base:output.weight"):
        K.conferir_vocab_igual_base(t, outra)
    with pytest.raises(SystemExit):
        K.conferir_vocab_igual_base({"tensores": []})


def _tensores_dict(**shas) -> str:
    t = {**K.SHA_VOCAB_BASE, **shas}
    return json.dumps({"tensores": [{"nome": n, "sha256": s} for n, s in t.items()]})


# ---------------------------------------------------------------------------
# importar-pasta: o treinado é conferido ANTES de qualquer import
# ---------------------------------------------------------------------------

def test_importar_pasta_aborta_treinado_divergente_e_ignora_a_base(tmp_path):
    base, ft = tmp_path / "base", tmp_path / "ft"
    base.mkdir()
    ft.mkdir()
    achados = [{"pasta": base, "nome": "espectro-qwen3-8b-base"},
               {"pasta": ft, "nome": "espectro-qwen3-8b-treinado"}]
    with pytest.raises(SystemExit, match="sem tensores.json"):
        V.conferir_treinados(achados)
    _tensores(ft)
    V.conferir_treinados(achados)                      # a base não precisa de tensores.json
    _tensores(ft, **{"token_embd.weight": "outro"})
    with pytest.raises(SystemExit, match="DESVIO_P02"):
        V.conferir_treinados(achados)


def test_importar_pasta_confere_antes_de_importar(tmp_path, monkeypatch):
    d = tmp_path / "treino" / "qwen3-8b-treinado__12288"
    d.mkdir(parents=True)
    (d / "Qwen3-8B.Q4_K_M.gguf").write_bytes(b"x")
    (d / "Modelfile").write_text("FROM x")
    (d / "log.json").write_text(json.dumps({"modelo": "qwen3-8b-treinado"}))
    _tensores(d, **{"output.weight": "outro"})
    importou = []
    monkeypatch.setattr(V, "cmd_importar", lambda a: importou.append(a))
    import argparse
    with pytest.raises(SystemExit, match="DESVIO_P02"):
        V.cmd_importar_pasta(argparse.Namespace(pasta=tmp_path))
    assert importou == []


# ---------------------------------------------------------------------------
# kernel de treino: o registro por linha do embed_tokens
# ---------------------------------------------------------------------------

def _funcao_do_kernel(nome: str):
    src = (RAIZ / "scripts" / "finetune" / "kaggle" / "kernel_treino" / "treino.py").read_text(encoding="utf-8")
    no = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == nome)
    ns: dict = {}
    exec(compile(ast.Module([no], []), "treino.py", "exec"), ns)   # só a função, sem o módulo
    return ns[nome]


def test_linhas_diferentes_acha_so_as_linhas_alteradas():
    torch = pytest.importorskip("torch")
    linhas_diferentes = _funcao_do_kernel("linhas_diferentes")
    b = torch.randn(20, 8, dtype=torch.bfloat16)
    a = b.clone()
    a[13] = 0
    r = linhas_diferentes(a, b, torch, bloco=6)
    assert r["n_linhas"] == 1 and r["linhas"][0]["id"] == 13
    assert r["linhas"][0]["max_abs"] == float(b[13].float().abs().max()) == r["max_abs"]
    assert linhas_diferentes(b, b, torch)["n_linhas"] == 0


def test_o_registro_por_linha_nao_aborta_o_treino():
    src = (RAIZ / "scripts" / "finetune" / "kaggle" / "kernel_treino" / "treino.py").read_text(encoding="utf-8")
    i = src.index('reg["embed_contra_original"] = embed_contra_original(dst, torch)')
    trecho = src[src.rindex("try:", 0, i):src.index("_json(log, reg)", i)]
    assert "except Exception" in trecho and "raise" not in trecho
