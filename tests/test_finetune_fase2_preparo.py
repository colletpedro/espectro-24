"""[2026-10-31] Fine-tuning: o preparo da Fase 2 e a validação da Fase 1.

- `gerar_sintese_teste.py`: só filmes de TESTE, o bucket do Gemini fora, a
  regra de `num_ctx`, e a origem do GGUF (a base tem de vir do kernel, com a
  prova do adaptador identidade; o treinado, com o mesmo llama.cpp da base);
- `especificidade_validacao.exibir`: a mesma normalização de formato nas duas
  fontes;
- `kernel_base/exportar_base.py` compila (roda só no Kaggle)."""
from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import gerar_sintese_teste as G  # noqa: E402


def test_num_ctx_pela_regra_do_gate_0():
    # os mesmos valores do plano da geração base (soul-2020/negativas, pinocchio-2022/negativas)
    assert G.num_ctx_da_chamada(4202) == 8192
    assert G.num_ctx_da_chamada(14267) == 19456


def test_recusa_filme_de_teste_que_tambem_e_de_treino():
    split = {"teste": ["a", "b"], "treino": ["b", "c"], "validacao": []}
    with pytest.raises(SystemExit):
        G.filmes_de_teste(split)
    assert G.filmes_de_teste({"teste": ["b", "a"], "treino": ["c"], "validacao": ["d"]}) == ["a", "b"]


def test_bucket_do_gemini_fica_fora():
    split = {"buckets_excluidos": [{"slug": "a-brighter-summer-day", "bucket": "positivas"}]}
    assert G.excluidos(split) == {("a-brighter-summer-day", "positivas")}


def _log(tmp_path: Path, nome: str, sha: str = "abc", **extra) -> Path:
    p = tmp_path / nome
    p.write_text(json.dumps({"gguf_arquivos": [{"nome": "Qwen3-8B.Q4_K_M.gguf", "sha256": sha},
                                               {"nome": "Modelfile", "sha256": "x"}], **extra}))
    return p


def _importacao(pasta: Path, nome: str, sha: str, e4: bool = True,
                ts: str = "20261101_000000") -> None:
    pasta.mkdir(exist_ok=True)
    (pasta / f"importar_{nome}_{ts}.json").write_text(json.dumps(
        {"E4_importa_e_gera": e4, "importacao": {"gguf_sha256": sha, "modelfile_usado": "FROM x",
                                                 "nome_ollama": nome}}))


def test_base_exige_prova_do_adaptador_e_da_fusao(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "VIABILIDADE", tmp_path / "viab")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-base", "abc")
    sem_prova = _log(tmp_path, "a.json", prova_adaptador={"B_zero": False}, prova_fusao={"ok": True})
    with pytest.raises(SystemExit):
        G.conferir_modelo("base", "espectro-qwen3-8b-base", sem_prova, None)
    ok = _log(tmp_path, "b.json", prova_adaptador={"B_zero": True}, prova_fusao={"ok": True})
    assert G.conferir_modelo("base", "espectro-qwen3-8b-base", ok, None)["gguf_sha256"] == "abc"


def test_base_recusa_gguf_que_nao_e_o_do_kernel(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "VIABILIDADE", tmp_path / "viab")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-base", "outro-sha")   # p. ex. a biblioteca
    ok = _log(tmp_path, "b.json", prova_adaptador={"B_zero": True}, prova_fusao={"ok": True})
    with pytest.raises(SystemExit):
        G.conferir_modelo("base", "espectro-qwen3-8b-base", ok, None)


def test_treinado_exige_o_mesmo_llama_cpp_da_base(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "VIABILIDADE", tmp_path / "viab")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-ft", "abc")
    _importacao(tmp_path / "viab", "espectro-qwen3-8b-base", "sha-base")
    base = _log(tmp_path, "base.json", llama_cpp={"commit": "c1"}, sha="sha-base")
    outro = _log(tmp_path, "ft1.json", llama_cpp={"commit": "c2"})
    with pytest.raises(SystemExit):
        G.conferir_modelo("treinado", "espectro-qwen3-8b-ft", outro, base)
    with pytest.raises(SystemExit):
        G.conferir_modelo("treinado", "espectro-qwen3-8b-ft", outro, None)
    igual = _log(tmp_path, "ft2.json", llama_cpp={"commit": "c1"})
    assert G.conferir_modelo("treinado", "espectro-qwen3-8b-ft", igual, base)["gguf_sha256"] == "abc"


def test_exibicao_normaliza_igual_nas_duas_fontes():
    import especificidade_validacao as V
    assert V.exibir("narrativa confusa", False) == "Narrativa confusa"
    assert V.exibir("Ritmo lento", False) == "Ritmo lento"
    assert V.exibir("as reviews destacam o jazz", True) == "As reviews destacam o jazz."
    assert V.exibir("Várias críticas citam o final.", True) == "Várias críticas citam o final."
    assert V.exibir("O grupo cita “o twist”", True) == "O grupo cita “o twist”"


def test_kernel_da_base_compila():
    py_compile.compile(str(RAIZ / "scripts" / "finetune" / "kaggle" / "kernel_base" /
                           "exportar_base.py"), doraise=True)
    meta = json.loads((RAIZ / "scripts" / "finetune" / "kaggle" / "kernel_base" /
                       "kernel-metadata.json").read_text())
    assert meta["code_file"] == "exportar_base.py" and meta["is_private"] is True
    assert meta["dataset_sources"] == []
