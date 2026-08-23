"""[v1.9.16, Entrega 4] `_ja_publicado` — o critério de resume do lote de
publicação: um filme conta como PUBLICADO sob a versão corrente só se o
`spec_version` bate E o verificador foi aplicado. Sem os dois, o resume
pularia um filme publicado sob uma versão antiga (ex.: `oppenheimer-2023`,
`spec_version 1.1.1`) como se estivesse em dia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


def _pc():
    import publicar_catalogo
    return publicar_catalogo


def test_ausente_nao_e_publicado(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    assert pc._ja_publicado("nao-existe") is False


def test_json_de_versao_antiga_nao_conta(tmp_path, monkeypatch):
    """O caso real: `oppenheimer-2023.json` existe, mas é `spec_version
    1.1.1` — pré-eixos, pré-verificador. Resume tem que tratar como
    pendente, não como feito."""
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    (tmp_path / "oppenheimer-2023.json").write_text(
        json.dumps({"slug": "oppenheimer-2023", "spec_version": "1.1.1"}),
        encoding="utf-8")
    assert pc._ja_publicado("oppenheimer-2023") is False


def test_versao_atual_sem_eixos_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9"}), encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_versao_atual_com_eixos_mas_sem_verificador_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9",
                    "eixos": {"contraste": "tematico"}}), encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_versao_atual_com_verificador_aplicado_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9",
                    "eixos": {"contraste": "tematico",
                              "verificador": {"aplicado": True}}}),
        encoding="utf-8")
    assert pc._ja_publicado("x") is True


def test_json_corrompido_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    (tmp_path / "x.json").write_text("{ nao é json", encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_filmes_padrao_sao_os_32_faltantes():
    """A lista default é o catálogo (35, de `consenso.jsonl`) menos os 3 já
    publicados sob o pipeline corrente — travado no número, não recomputado
    aqui, para que uma mudança silenciosa no catálogo apareça como falha."""
    pc = _pc()
    if not (RAIZ / "resultado" / "votacao-3" / "consenso.jsonl").exists():
        import pytest
        pytest.skip("consenso.jsonl indisponível")
    faltantes = pc.filmes_pendentes()
    assert len(faltantes) == 32
    assert "oppenheimer-2023" in faltantes
    assert "cure" not in faltantes
