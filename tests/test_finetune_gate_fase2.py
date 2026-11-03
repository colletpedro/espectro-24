"""[2026-11-03] Gate da Fase 2, com dados SINTÉTICOS.

- `gerar_sintese_teste.exigir_gate_fase2`: o treinado só é gerado com
  `GATE_FASE2.md` commitado, igual ao HEAD, e com o `c1_c4_fase2.json` e o
  `delta2.json` dos sha256 que ele registra;
- `gate_fase2`: recusa sem o δ₂ fixado, sem os dois lados ou com o treinado já
  gerado; IC por lado pelo bootstrap por filme; o relatório traz a marca que a
  guarda lê, o aviso das entradas diferentes e o que não foi medido."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

# `gate_fase2` importa `_guarda` (troca `load_dotenv` e o socket): os originais voltam logo depois
import socket  # noqa: E402

import dotenv  # noqa: E402

_ORIGINAIS = (dotenv.load_dotenv, socket.socket.connect, socket.create_connection)
import gate_fase2 as GF  # noqa: E402
import ollama_pronto  # noqa: E402,F401
import gerar_sintese_teste as G  # noqa: E402

dotenv.load_dotenv, socket.socket.connect, socket.create_connection = _ORIGINAIS


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _repo_com_gate(tmp_path: Path, commitar: bool = True) -> tuple[Path, Path]:
    repo, pasta = tmp_path / "repo", tmp_path / "fase2"
    repo.mkdir()
    pasta.mkdir()
    (pasta / "c1_c4_fase2.json").write_text('{"x": 1}')
    (pasta / "delta2.json").write_text('{"delta2_pp": 7.9}')
    shas = {"c1_c4_fase2_sha256": G.K.sha256_arquivo(pasta / "c1_c4_fase2.json"),
            "delta2_sha256": G.K.sha256_arquivo(pasta / "delta2.json")}
    gate = repo / "GATE_FASE2.md"
    gate.write_text(f"# gate\n\n{G.MARCA_GATE}{json.dumps(shas)} -->\n", encoding="utf-8")
    _git(repo, "init", "-q")
    if commitar:
        _git(repo, "add", "GATE_FASE2.md")
        _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "gate")
    return gate, pasta


def test_treinado_recusado_sem_gate(tmp_path):
    with pytest.raises(SystemExit, match="gate da Fase 2"):
        G.exigir_gate_fase2(tmp_path / "GATE_FASE2.md", tmp_path)


def test_treinado_recusado_com_gate_nao_commitado(tmp_path):
    gate, pasta = _repo_com_gate(tmp_path, commitar=False)
    with pytest.raises(SystemExit, match="não está commitado"):
        G.exigir_gate_fase2(gate, pasta)


def test_treinado_recusado_com_gate_alterado_depois_do_commit(tmp_path):
    gate, pasta = _repo_com_gate(tmp_path)
    gate.write_text(gate.read_text() + "editado\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="difere do commitado"):
        G.exigir_gate_fase2(gate, pasta)


def test_treinado_recusado_se_c1_c4_ou_delta2_mudaram(tmp_path):
    gate, pasta = _repo_com_gate(tmp_path)
    assert G.exigir_gate_fase2(gate, pasta)["delta2_sha256"]
    (pasta / "delta2.json").write_text('{"delta2_pp": 8.0}')
    with pytest.raises(SystemExit, match="delta2.json"):
        G.exigir_gate_fase2(gate, pasta)


def test_gerar_treinado_para_na_guarda_antes_do_modelo(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv(G.VAR_TEMPERATURA, raising=False)
    monkeypatch.setattr(G, "ARQ_GATE", tmp_path / "GATE_FASE2.md")
    monkeypatch.setattr(G, "exigir_gate_fase2", lambda: (_ for _ in ()).throw(SystemExit("gate")))
    a = type("A", (), {"lado": "treinado"})()
    with pytest.raises(SystemExit, match="gate"):
        G.cmd_gerar(a)


def test_ordem_exigida_pelo_gerador(tmp_path, monkeypatch):
    monkeypatch.setattr(GF.G, "PASTA", tmp_path)
    ok = {"lados": {"publicado": {}, "base": {}}, "delta2_fixado": True, "delta2_pp": 7.9,
          "decisao": None}
    GF.exigir_ordem(ok, {"delta2_pp": 7.9})
    with pytest.raises(SystemExit, match="δ₂"):
        GF.exigir_ordem({**ok, "delta2_fixado": False, "delta2_pp": 8.0}, {"delta2_pp": 7.9})
    with pytest.raises(SystemExit, match="base"):
        GF.exigir_ordem({**ok, "lados": {"publicado": {}}}, {"delta2_pp": 7.9})
    (tmp_path / "sintese_treinado").mkdir()
    (tmp_path / "sintese_treinado" / "manifesto.json").write_text("{}")
    with pytest.raises(SystemExit, match="treinado"):
        GF.exigir_ordem(ok, {"delta2_pp": 7.9})


def _pf(sem, n=18, filmes=("a", "b", "c", "d")):
    return {f: {"julgados": n, "sem_apoio": sem[i], "apoio_2": 15, "m1_n": n, "m1_k": 9,
                "c4_ok": 3, "buckets": 3} for i, f in enumerate(filmes)}


def test_ic_do_lado_pelo_bootstrap_por_filme():
    filmes = ["a", "b", "c", "d"]
    boot = GF.A.reamostras(filmes, n=500)
    x = GF.ic_do_lado(_pf([0, 0, 2, 2]), filmes, boot, "sem_apoio")
    assert (x["k"], x["n"]) == (4, 72) and abs(x["pct"] - 100 * 4 / 72) < 1e-9
    assert x["ic95_pct"][0] < x["pct"] < x["ic95_pct"][1]
    c4 = GF.ic_do_lado(_pf([0, 0, 0, 0]), filmes, boot, "c4")
    assert c4["pct"] == 100 and c4["ic95_pct"] == [100, 100]


def _dados():
    ic = {"k": 2, "n": 500, "pct": 0.4, "ic95_pct": [0.0, 1.0], "reamostras_validas": 10000}
    lado = lambda: {"ic": {m: ic for m in GF.METRICAS_IC}, "estados": {"indeterminado": 3},
                    "resumo": {"c4_ok_1a_tentativa": 80},
                    "juiz": {"chamadas": 10, "ok": 10, "reaproveitadas": 0, "soma_latencia_h": 7.1,
                             "mediana_s": 16.0, "primeira": "t0", "ultima": "t1"},
                    "preparar_s": 900.0, "reaproveitamento": None}
    pub = {**lado(), "referencia_5": {"sem_apoio": 1, "julgados": 88, "indeterminados": 0,
                                      "antigo": {"sem_apoio": 2, "julgados": 90}},
           "reaproveitamento": {"linhas": 450, "sha256": "059f3825" + "0" * 56, "bate": False}}
    dif = {"ponto_pp": 1.0, "ic95_pp": [-1.0, 3.0], "passa": True}
    return {"c1c4": {"reamostras": 10000, "semente_bootstrap": 20261101, "juiz": "44606cf1" * 8,
                     "achado_base_satisfaz_c1_c4": False,
                     "descritivo": {"base_contra_publicado": {
                         "C1": dif, "C2": dif, "C3": dif,
                         "C4": {"ok": 80, "buckets": 89, "piso": 87, "passa": False}}}},
            "delta2": {"p0_apoio_2": 0.85, "bullets_julgados": 520, "delta2_pp": 7.9,
                       "formula": "f"},
            "lados": {"publicado": pub, "base": lado()}, "filmes": 30, "buckets_mantidos": 89,
            "entradas": {"commit": "742cfe3c7d", "n_arquivos": 162, "sha256": "f2a7a0ba" * 8},
            "excluidos_split": [{"slug": "a-brighter-summer-day", "bucket": "positivas",
                                 "motivo": "Gemini", "regra": "fora"}],
            "fora_por_memoria": [], "abortos_recuperados": [],
            "outlier": {"par": "500-days-of-summer/positivas", "num_ctx": 30720, "ok": True,
                        "abortos_memoria": 0, "fora_por_memoria": False, "parede_s": 300.0},
            "sintese_base": {"buckets": 89, "total_h": 4.0, "mediana_s": 150, "min_s": 120,
                             "max_s": 300, "chamadas": {1: 85, 2: 4}},
            "shas": {"c1_c4_fase2_sha256": "aa", "delta2_sha256": "bb"}}


def test_relatorio_traz_a_marca_o_aviso_e_o_nao_medido():
    t = GF.renderizar(_dados())
    assert G.ler_marca_gate(t) == {"c1_c4_fase2_sha256": "aa", "delta2_sha256": "bb"}
    assert "**δ₂ = 7,9 pp**" in t
    assert "2/90" in t and "1/88" in t and "As entradas diferem" in t and "bate: False" in t
    assert "O que NÃO foi medido" in t and "O TREINADO" in t
    assert "a-brighter-summer-day/positivas" in t and "500-days-of-summer/positivas" in t
    assert "| C4 | 80/89 buckets | — | ≥ 87 | não |" in t


def test_ollama_pronto_confere_por_http_sem_o_cli_interativo():
    import ollama_pronto as O
    assert O.modelo_presente(["gpt-oss:20b"], "gpt-oss:20b")
    assert O.modelo_presente(["x:latest"], "x") and not O.modelo_presente(["y"], "x")
    fonte = (RAIZ / "scripts" / "finetune" / "ollama_pronto.py").read_text(encoding="utf-8")
    assert '"list"' not in fonte and '"ps"' not in fonte
