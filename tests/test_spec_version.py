"""[v1.9.14] `SPEC_VERSION` não pode divergir do título de `SPEC.md`.

**A deriva aconteceu duas vezes em treze versões, as duas em silêncio.** A
v1.9.11 achou a constante parada em `"1.9.0"` — todo `resultado/*.json` de
v1.9.1 a v1.9.10 carimbou a versão errada. A v1.9.14 achou a mesma coisa de
novo: os 3 filmes republicados dizem `1.9.11` porque a constante ficou para
trás quando o documento foi para v1.9.12 e v1.9.13.

Nenhuma das duas foi pega por leitura — as duas foram pegas depois, ao
comparar um artefato publicado com a spec. É o gatilho do padrão do projeto
(**lição vira mecanismo**, §3[D]): a disciplina escrita "lembre de subir a
constante" já falhou duas vezes, então o invariante vira teste.

O carimbo NUNCA é corrigido à mão num artefato já gerado (mesma política de
`VERSAO_COLETOR`, config.py): um carimbo corrigido depois do fato não é
evidência de nada. Este teste protege a PRÓXIMA geração, não conserta as
anteriores.
"""
from __future__ import annotations

import re
from pathlib import Path

from espectro24.config import SPEC_VERSION

SPEC = Path(__file__).resolve().parent.parent / "SPEC.md"


def _versao_do_titulo() -> str:
    """A versão declarada na primeira linha de `SPEC.md`.

    Lê só o título — o corpo cita dezenas de versões históricas e casar com
    qualquer uma delas tornaria o teste um detector de nada.
    """
    primeira = SPEC.read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"v(\d+\.\d+\.\d+)", primeira)
    assert m, f"título de SPEC.md sem versão reconhecível: {primeira!r}"
    return m.group(1)


def test_spec_version_bate_com_o_titulo_da_spec():
    assert SPEC_VERSION == _versao_do_titulo(), (
        f"SPEC_VERSION={SPEC_VERSION!r} e SPEC.md declara "
        f"v{_versao_do_titulo()}. O carimbo de todo resultado/*.json sai de "
        "SPEC_VERSION: divergir aqui publica a versão errada em silêncio, o "
        "que já aconteceu duas vezes (v1.9.0 e v1.9.11)."
    )


def test_extrator_do_titulo_le_a_primeira_linha(tmp_path, monkeypatch):
    """O extrator tem de pegar a versão do TÍTULO, não a primeira do arquivo.

    Sem esta fixture, um extrator quebrado que casasse com qualquer versão do
    corpo passaria igual a um correto — o modo de falha clássico de guard-rail
    que não detecta nada (mesma ressalva de `test_guardrail_adaptador.py`).
    """
    falso = tmp_path / "SPEC.md"
    falso.write_text(
        "# Espectro 24 — Especificação v9.8.7\n\nCorpo citando v1.0.0 e v1.2.3.\n",
        encoding="utf-8")
    monkeypatch.setattr("tests.test_spec_version.SPEC", falso, raising=False)
    import tests.test_spec_version as mod
    monkeypatch.setattr(mod, "SPEC", falso)
    assert mod._versao_do_titulo() == "9.8.7"
