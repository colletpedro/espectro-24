"""[2026-09-18] Escrita atômica: gravar em temporário e renomear.

`open(path, "w")` trunca antes de escrever; uma queda no meio deixa o arquivo
pela metade, e `consenso.jsonl`/`consenso_verificado.jsonl` são lidos por
`pipeline.montar_eixos` para os filmes PUBLICADOS. Com o driver por blocos as
gravações passam a ser frequentes, então o risco deixa de ser teórico.

O que se prova aqui: em QUALQUER falha durante a gravação o arquivo original
fica inteiro, byte a byte, e nenhum temporário sobra.
"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import atomico  # noqa: E402
from espectro24.atomico import escrever_atomico  # noqa: E402

ORIGINAL = "linha 1\nlinha 2\nlinha 3\n"


def _sobras(pasta: Path) -> list[str]:
    return sorted(p.name for p in pasta.iterdir() if p.name.endswith(".tmp"))


def test_grava_o_conteudo_e_nao_deixa_temporario(tmp_path):
    alvo = tmp_path / "saida.jsonl"
    escrever_atomico(alvo, "a\nb\n")
    assert alvo.read_text(encoding="utf-8") == "a\nb\n"
    assert _sobras(tmp_path) == []


def test_substitui_o_arquivo_existente_inteiro(tmp_path):
    alvo = tmp_path / "saida.jsonl"
    alvo.write_text(ORIGINAL, encoding="utf-8")
    escrever_atomico(alvo, "novo\n")
    assert alvo.read_text(encoding="utf-8") == "novo\n"


def test_cria_o_diretorio_que_falta(tmp_path):
    alvo = tmp_path / "a" / "b" / "saida.json"
    escrever_atomico(alvo, "{}")
    assert alvo.read_text(encoding="utf-8") == "{}"


def test_preserva_o_modo_do_arquivo_existente(tmp_path):
    """`mkstemp` cria 0600; sem cópia do modo, o consenso 0644 viraria 0600
    depois do primeiro bloco."""
    alvo = tmp_path / "saida.jsonl"
    alvo.write_text(ORIGINAL, encoding="utf-8")
    os.chmod(alvo, 0o644)
    escrever_atomico(alvo, "novo\n")
    assert stat.S_IMODE(alvo.stat().st_mode) == 0o644


def test_arquivo_novo_segue_o_umask_nao_o_0600_do_mkstemp(tmp_path):
    alvo = tmp_path / "saida.jsonl"
    antigo = os.umask(0o022)
    try:
        escrever_atomico(alvo, "x")
    finally:
        os.umask(antigo)
    assert stat.S_IMODE(alvo.stat().st_mode) == 0o644


def test_queda_no_meio_da_escrita_deixa_o_original_intacto(tmp_path, monkeypatch):
    """O defeito que `open("w")` tinha: a queda entre o truncamento e o fim da
    escrita. Simulada no `fsync`, DEPOIS de o conteúdo novo estar no
    temporário e ANTES do renome."""
    alvo = tmp_path / "saida.jsonl"
    alvo.write_text(ORIGINAL, encoding="utf-8")

    def cai(fd):
        raise OSError("disco cheio / processo morto")

    monkeypatch.setattr(atomico.os, "fsync", cai)
    with pytest.raises(OSError, match="disco cheio"):
        escrever_atomico(alvo, "conteudo novo que nao pode aparecer\n")

    assert alvo.read_text(encoding="utf-8") == ORIGINAL
    assert _sobras(tmp_path) == []


def test_falha_no_renome_deixa_o_original_intacto(tmp_path, monkeypatch):
    alvo = tmp_path / "saida.jsonl"
    alvo.write_text(ORIGINAL, encoding="utf-8")

    def cai(origem, destino):
        raise OSError("renome falhou")

    monkeypatch.setattr(atomico.os, "replace", cai)
    with pytest.raises(OSError, match="renome falhou"):
        escrever_atomico(alvo, "novo\n")

    assert alvo.read_text(encoding="utf-8") == ORIGINAL
    assert _sobras(tmp_path) == []


def test_interrupcao_tambem_limpa_o_temporario(tmp_path, monkeypatch):
    """`KeyboardInterrupt`/`SystemExit` não são `Exception`: o `except` tem de
    ser de `BaseException`, senão Ctrl-C no meio deixa lixo no diretório."""
    alvo = tmp_path / "saida.jsonl"
    alvo.write_text(ORIGINAL, encoding="utf-8")

    def interrompe(origem, destino):
        raise KeyboardInterrupt

    monkeypatch.setattr(atomico.os, "replace", interrompe)
    with pytest.raises(KeyboardInterrupt):
        escrever_atomico(alvo, "novo\n")
    assert alvo.read_text(encoding="utf-8") == ORIGINAL
    assert _sobras(tmp_path) == []


def test_o_temporario_fica_no_mesmo_diretorio_do_destino(tmp_path, monkeypatch):
    """`os.replace` só é atômico dentro do mesmo filesystem."""
    vistos = []
    real = atomico.os.replace

    def espia(origem, destino):
        vistos.append((Path(origem).parent, Path(destino).parent))
        return real(origem, destino)

    monkeypatch.setattr(atomico.os, "replace", espia)
    escrever_atomico(tmp_path / "saida.jsonl", "x")
    assert vistos == [(tmp_path, tmp_path)]


# --- os gravadores de produção usam mesmo a escrita atômica ------------------

def test_cmd_consenso_nao_deixa_o_consenso_pela_metade(tmp_path, monkeypatch):
    """`votacao_3.cmd_consenso` gravava com `open("w")`. Com a gravação
    falhando no meio, o consenso que já existia sobrevive inteiro."""
    import votacao_3 as v3

    tid = v3.taxonomia_id()
    amostra = {"taxonomia_id": tid, "filmes": [{"slug": "f", "perfil": "x"}],
               "reviews": [{"slug": "f", "perfil": "x", "bucket": "negativas",
                            "id": "r1", "nivel": 1.0, "n_chars": 10,
                            "texto": "t"}]}
    (tmp_path / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")
    passes = {}
    for n in (1, 2, 3):
        p = tmp_path / f"passe_{n}.jsonl"
        p.write_text(json.dumps({
            "ok": True, "taxonomia_id": tid, "passe": n, "slug": "f",
            "perfil": "x", "bucket": "negativas", "id": "r1", "nivel": 1.0,
            "n_chars": 10, "eixos": ["atuacao"], "eixos_invalidos": []}) + "\n",
            encoding="utf-8")
        passes[n] = p
    consenso = tmp_path / "consenso.jsonl"
    consenso.write_text(ORIGINAL, encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", tmp_path / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE", passes)
    monkeypatch.setattr(v3, "ARQ_CONSENSO", consenso)
    monkeypatch.setattr(v3, "SAIDA", tmp_path)
    monkeypatch.setattr(v3, "RAIZ", tmp_path)

    fsync_real = os.fsync      # `atomico.os` É o módulo `os`: guardar ANTES

    def cai(fd):
        raise OSError("queda")

    monkeypatch.setattr(atomico.os, "fsync", cai)
    with pytest.raises(OSError, match="queda"):
        v3.cmd_consenso()
    assert consenso.read_text(encoding="utf-8") == ORIGINAL
    assert _sobras(tmp_path) == []

    monkeypatch.setattr(atomico.os, "fsync", fsync_real)   # a queda passou
    v3.cmd_consenso()
    assert json.loads(consenso.read_text(encoding="utf-8").splitlines()[0])[
        "slug"] == "f"


def test_os_gravadores_de_producao_nao_usam_open_w_nem_write_text():
    """Guard estrutural: `consenso.jsonl`, `consenso_verificado.jsonl`, o
    manifesto e a amostra só se gravam por `escrever_atomico`."""
    import ast

    alvos = {"votacao_3.py": {"cmd_consenso"},
             "verificador_impacto.py": {"gravar_aplicacao"},
             "estender_classificacao_producao.py": {"_acrescentar_a_amostra"},
             "lote_em_blocos.py": {"gravar_bloco"}}
    for arquivo, funcoes in alvos.items():
        tree = ast.parse((RAIZ / "scripts" / arquivo).read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name in funcoes]:
            trecho = ast.unparse(fn)
            assert "escrever_atomico" in trecho, f"{arquivo}:{fn.name}"
            assert ".write_text(" not in trecho, f"{arquivo}:{fn.name}"
            assert '.open("w"' not in trecho, f"{arquivo}:{fn.name}"
