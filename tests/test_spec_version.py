"""[v1.9.14] O carimbo `SPEC_VERSION` não pode carimbar uma versão que a spec
não registra, nem passar à frente do título.

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

---

**[2026-09-04] O invariante MUDOU, porque a regra mudou.** Até esta data o
teste exigia `SPEC_VERSION == versão do título`. O §0 da `SPEC.md` passou a
declarar que as duas são coisas diferentes e que a divergência é DELIBERADA:
o título é a versão do DOCUMENTO (a última decisão registrada), `SPEC_VERSION`
é o carimbo de ARTEFATO DE PIPELINE, e ele só sobe quando muda alguma coisa
que um `resultado/<slug>.json` carrega. As v1.9.26–v1.9.37 foram sessões de
frontend e de harness que não regeraram artefato, então o carimbo ficou em
`1.9.25` de propósito. Sob a regra nova, a igualdade é falsa por desenho, e um
teste que a exigisse só poderia ser satisfeito mentindo em `config.py` — que é
exatamente o defeito que ele existe para impedir.

**O que sobra de protegível mecanicamente, e é o que os dois testes abaixo
fazem:** (1) o carimbo nunca está À FRENTE do título — carimbar uma versão que
o documento ainda não registrou é publicar uma versão que não existe; e (2) o
carimbo é uma versão que o changelog da spec de fato registra — o que pega
número inventado ou digitado errado.

**A lacuna que isto NÃO cobre, declarada em vez de escondida:** uma versão que
MUDA artefato de pipeline e esquece de subir a constante passa nos dois — é
exatamente o modo de falha de 2026-07 e 2026-08. Distinguir "ficou para trás
de propósito" de "ficou para trás por esquecimento" exige saber se as versões
no intervalo tocaram o pipeline, e isso não está estruturado em lugar nenhum
que um teste possa ler. Fechar essa lacuna pede um campo por versão no
changelog (`artefato: sim/não`), que é mudança de formato da spec — decisão do
dono, registrada como pendência, não resolvida aqui.
"""
from __future__ import annotations

import re
from pathlib import Path

from espectro24.config import SPEC_VERSION

SPEC = Path(__file__).resolve().parent.parent / "SPEC.md"


def _tupla(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def _versao_do_titulo() -> str:
    """A versão declarada na primeira linha de `SPEC.md`.

    Lê só o título — o corpo cita dezenas de versões históricas e casar com
    qualquer uma delas tornaria o teste um detector de nada.
    """
    primeira = SPEC.read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"v(\d+\.\d+\.\d+)", primeira)
    assert m, f"título de SPEC.md sem versão reconhecível: {primeira!r}"
    return m.group(1)


def _versoes_do_changelog() -> set[str]:
    """As versões que o changelog registra, pela forma `- **vX.Y.Z**`.

    Deliberadamente NÃO é "qualquer vX.Y.Z no corpo": o corpo cita dezenas de
    versões em prosa, e aceitar todas transformaria a checagem num detector de
    nada — a mesma ressalva que `_versao_do_titulo` já carrega.
    """
    txt = SPEC.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*-\s*\*\*v(\d+\.\d+\.\d+)\*\*", txt, re.MULTILINE))


def test_spec_version_nunca_esta_a_frente_do_titulo():
    """Carimbar versão que o documento ainda não registrou publica o que não existe."""
    assert _tupla(SPEC_VERSION) <= _tupla(_versao_do_titulo()), (
        f"SPEC_VERSION={SPEC_VERSION!r} está À FRENTE do título de SPEC.md "
        f"(v{_versao_do_titulo()}). O carimbo de todo resultado/*.json sai de "
        "SPEC_VERSION: carimbar uma versão que o documento não registrou "
        "publica uma versão que não existe. Ficar ATRÁS é permitido e "
        "deliberado (§0) — à frente, não."
    )


def test_spec_version_e_uma_versao_que_o_changelog_registra():
    """Pega número inventado ou digitado errado, que a comparação de ordem deixa passar."""
    registradas = _versoes_do_changelog()
    assert registradas, "o leitor do changelog não achou nenhuma versão — parser quebrado"
    assert SPEC_VERSION in registradas, (
        f"SPEC_VERSION={SPEC_VERSION!r} não aparece no changelog de SPEC.md. "
        "O carimbo tem de ser uma versão que o documento de fato registra — "
        "senão todo resultado/*.json aponta para uma versão que ninguém "
        "consegue ler."
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
    import tests.test_spec_version as mod
    monkeypatch.setattr(mod, "SPEC", falso)
    assert mod._versao_do_titulo() == "9.8.7"


def test_leitor_do_changelog_ignora_versao_citada_em_prosa(tmp_path, monkeypatch):
    """Mesma ressalva do extrator de título, para o leitor do changelog.

    Um leitor que casasse com qualquer `vX.Y.Z` do corpo aceitaria qualquer
    carimbo, e o segundo teste viraria decoração.
    """
    falso = tmp_path / "SPEC.md"
    falso.write_text(
        "# Espectro 24 — Especificação v3.2.1\n\n"
        "Prosa citando a v9.9.9 e a v0.0.1 sem registrá-las.\n\n"
        "- **v3.2.1** (2026-01-01) — entrada de changelog de verdade.\n"
        "- **v3.2.0** (2025-12-31) — outra entrada.\n",
        encoding="utf-8")
    import tests.test_spec_version as mod
    monkeypatch.setattr(mod, "SPEC", falso)
    assert mod._versoes_do_changelog() == {"3.2.1", "3.2.0"}
