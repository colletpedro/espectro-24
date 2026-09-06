"""[v1.9.40] `scripts/popular_stills.py` FALHA se Pillow/imagehash não
estiverem instalados — não degrada. Ver a docstring de
`_exigir_dependencias_dedup` para a distinção com `_hashes_dos_candidatos`
(que degrada, e continua degradando, na ficha em produção).

Testado por SUBSTITUIÇÃO do import (a mesma técnica de
`test_enriquecer_ficha.py` para travar escopo): forçar `import PIL` e
`import imagehash` a levantar `ImportError` sem precisar desinstalar nada
do ambiente de teste.
"""
from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import popular_stills  # noqa: E402


def _sem_modulo(nome_bloqueado, monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == nome_bloqueado:
            raise ImportError(f"simulado: {nome_bloqueado} ausente")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_falha_se_PIL_faltar(monkeypatch):
    _sem_modulo("PIL", monkeypatch)
    with pytest.raises(SystemExit, match="Pillow"):
        popular_stills._exigir_dependencias_dedup()


def test_falha_se_imagehash_faltar_mesmo_com_PIL_presente(monkeypatch):
    """`imagehash` importa PIL por baixo — bloquear só `imagehash` prova
    que a checagem detecta a ausência DELE especificamente, não um efeito
    colateral de bloquear PIL (que também derrubaria `imagehash`, ver o
    teste acima e `test_falha_reporta_as_DUAS...` abaixo)."""
    _sem_modulo("imagehash", monkeypatch)
    with pytest.raises(SystemExit) as exc:
        popular_stills._exigir_dependencias_dedup()
    assert "imagehash" in str(exc.value) and "Pillow" not in str(exc.value)


def test_falha_reporta_as_DUAS_dependencias_quando_ambas_faltam(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("PIL", "imagehash"):
            raise ImportError("simulado")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(SystemExit) as exc:
        popular_stills._exigir_dependencias_dedup()
    assert "Pillow" in str(exc.value) and "imagehash" in str(exc.value)


def test_nao_falha_quando_as_dependencias_existem():
    """Sanidade: no ambiente de teste (que TEM as duas), a checagem não
    levanta nada — sem isso o teste acima poderia estar passando por um
    motivo errado (ex. a função sempre levanta)."""
    popular_stills._exigir_dependencias_dedup()


def test_main_falha_antes_de_pedir_a_TMDB_API_KEY(monkeypatch):
    """A ordem importa: a checagem de dependência vem ANTES de exigir a
    chave da API — quem roda sem Pillow/imagehash E sem `.env` configurado
    vê o erro de dependência, não um erro de chave que mascara o real."""
    _sem_modulo("imagehash", monkeypatch)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    monkeypatch.setattr(popular_stills, "_api_key",
                        lambda: pytest.fail("não deveria chegar aqui"))
    monkeypatch.setattr(sys, "argv", ["popular_stills.py", "--dry-run"])
    with pytest.raises(SystemExit, match="imagehash"):
        popular_stills.main()
