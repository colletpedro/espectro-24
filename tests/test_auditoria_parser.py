"""Guard-rail do parser de `leitura.md` (auditoria de acurácia).

Regressão de um defeito real: um reformatador de markdown trocou o marcador
de lista `-` por `*` nas 1100 linhas de checkbox do arquivo anotado. O regex
só reconhecia `-`, então NENHUMA marcação casou, e o parser devolveu 100 ×
`eixos: []` sem erro — só um aviso por review. O relatório de métricas foi
calculado inteiro sobre dado vazio antes de alguém notar.

Dois consertos, testados aqui:
  1. aceitar os dois marcadores (`-` e `*`), já que ambos são markdown válido;
  2. tratar "nenhuma review tem marcação" como ERRO DE PARSING, não como
     resultado — um arquivo anotado de verdade tem ao menos uma marcação.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))


def _leitura(marcador: str, marcados: dict[int, list[str]]) -> str:
    """Monta um `leitura.md` sintético com `marcador` como bullet.

    `marcados` mapeia número do bloco → eixos a marcar com `[x]`.
    """
    eixos = ["ritmo", "atuacao", "impacto_emocional", "roteiro_estrutura"]
    blocos = []
    for i in (1, 2):
        linhas = [f"### #{i:03d} · `viewing:{1000 + i}` · filme-x (arthouse) · "
                  f"negativas · 2.0★ · 180 chars", "", "> texto da review", "",
                  "**Meus eixos**:", ""]
        for e in eixos:
            marca = "x" if e in marcados.get(i, []) else " "
            linhas.append(f"{marcador} [{marca}] {e}")
        linhas.append(f"{marcador} [ ] livre — temas: ____________________")
        blocos.append("\n".join(linhas))
    return "# Auditoria\n\n---\n\n" + "\n\n---\n\n".join(blocos) + "\n"


@pytest.fixture
def aa():
    import auditoria_acuracia
    return auditoria_acuracia


@pytest.mark.parametrize("marcador", ["-", "*"])
def test_aceita_os_dois_marcadores_de_lista(aa, tmp_path, marcador):
    """`- [x]` e `* [x]` são o mesmo markdown e devem parsear igual."""
    p = tmp_path / f"leitura_{marcador!r}.md"
    p.write_text(_leitura(marcador, {1: ["ritmo"], 2: ["atuacao"]}),
                 encoding="utf-8")
    anot = aa.ler_anotacoes_humanas(p)
    assert anot["viewing:1001"]["eixos"] == ["ritmo"]
    assert anot["viewing:1002"]["eixos"] == ["atuacao"]


def test_hifen_e_estrela_produzem_resultado_identico(aa, tmp_path):
    marcados = {1: ["ritmo", "impacto_emocional"], 2: ["roteiro_estrutura"]}
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(_leitura("-", marcados), encoding="utf-8")
    b.write_text(_leitura("*", marcados), encoding="utf-8")
    assert aa.ler_anotacoes_humanas(a) == aa.ler_anotacoes_humanas(b)


def test_nenhuma_marcacao_em_lugar_nenhum_e_erro_nao_resultado(aa, tmp_path):
    """O defeito original: marcador que o regex não conhece → tudo vazio.

    Antes, isso devolvia 2 × `eixos: []` e seguia em frente. Agora falha.
    """
    p = tmp_path / "quebrado.md"
    # `+` é bullet de markdown que o parser deliberadamente NÃO aceita —
    # serve aqui como um formato inesperado qualquer.
    p.write_text(_leitura("+", {1: ["ritmo"], 2: ["atuacao"]}), encoding="utf-8")
    with pytest.raises(SystemExit, match="ERRO DE PARSING"):
        aa.ler_anotacoes_humanas(p)


def test_erro_de_parsing_nomeia_o_formato_esperado(aa, tmp_path):
    """A mensagem tem de dizer o que fazer, não só que falhou."""
    p = tmp_path / "quebrado.md"
    p.write_text(_leitura("+", {1: ["ritmo"]}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        aa.ler_anotacoes_humanas(p)
    msg = str(exc.value)
    assert "checkbox reconhecidas pelo regex: 0" in msg
    assert "- [x]" in msg


def test_uma_unica_marcacao_ja_desarma_o_guard_rail(aa, tmp_path):
    """Zero eixos numa review é julgamento legítimo; zero no arquivo INTEIRO
    é que não. Uma marcação basta para o arquivo ser considerado anotado."""
    p = tmp_path / "quase_vazio.md"
    p.write_text(_leitura("-", {2: ["ritmo"]}), encoding="utf-8")
    anot = aa.ler_anotacoes_humanas(p)
    assert anot["viewing:1001"]["eixos"] == []      # legítimo, não derruba
    assert anot["viewing:1002"]["eixos"] == ["ritmo"]


def test_arquivo_real_da_auditoria_parseia_com_as_100_anotadas(aa):
    """O arquivo de produção continua parseando — 100 reviews, todas com
    ao menos um eixo (foi anotado à mão pelo dono do projeto)."""
    anot = aa.ler_anotacoes_humanas()
    assert len(anot) == 100
    assert all(a["eixos"] for a in anot.values())


def test_regex_de_checkbox_nao_casa_bullet_desconhecido(aa):
    """Trava a superfície aceita: só `-` e `*`, nada mais."""
    assert aa._RE_CHECK.findall("- [x] ritmo")
    assert aa._RE_CHECK.findall("* [x] ritmo")
    assert not aa._RE_CHECK.findall("+ [x] ritmo")
    assert not re.findall(aa._RE_CHECK, "[x] ritmo")
