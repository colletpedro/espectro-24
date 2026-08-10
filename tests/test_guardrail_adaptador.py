"""[v1.9.4] Guard-rail: nenhum caminho novo fala com o SDK do LLM direto.

SPEC §3[D]. A v1.8.0 documentou e resolveu uma causa raiz — `deepseek-v4-*`
tem *thinking* ligado por padrão, os tokens de raciocínio competem pelo mesmo
orçamento de `max_tokens` que a resposta, e sem `thinking: disabled` o
`content` volta vazio. A correção vive em `synthesize.deepseek_client_call`
desde então, e mesmo assim o defeito VOLTOU: o script do gate de taxonomia
(2026-08-08) chamou a API direto e 8 de 12 chamadas voltaram vazias.

Uma regra escrita falharia igual na próxima vez. O padrão da spec é **lição
vira mecanismo** — este arquivo é o mecanismo.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

# O ÚNICO módulo autorizado a instanciar SDK de LLM e a chamar geração.
ADAPTADOR = RAIZ / "src" / "espectro24" / "synthesize.py"

# Diretórios varridos. `scripts/` entra deliberadamente: foi lá que o defeito
# reapareceu, e é lá que a fase de síntese vai criar mais caminhos novos.
# `tests/` fica de fora — os testes importam o SDK para construir dublês e
# nunca fazem chamada real.
ESCOPO = [RAIZ / "src", RAIZ / "scripts"]

# ALLOWLIST — literal, e cada entrada com o motivo escrito ao lado. Adicionar
# um arquivo aqui é uma mudança deliberada e revisável, nunca um efeito
# colateral. Estes três scripts chamam o SDK direto DE PROPÓSITO: o
# `thinking_budget` e a escolha de modelo SÃO o objeto de estudo deles
# (DIAGNOSTICO_FLUENCIA*.md, resultado/comparacao/), e passar pelo adaptador
# — que fixa exatamente esses parâmetros — tornaria o experimento impossível.
ALLOWLIST = {
    "scripts/diagnostico_fluencia.py",
    "scripts/diagnostico_fluencia_v2.py",
    "scripts/compare_models.py",
}

# Instanciação/import de SDK.
PADROES_SDK = [
    re.compile(r"\bfrom\s+openai\s+import\b"),
    re.compile(r"\bimport\s+openai\b"),
    re.compile(r"\bOpenAI\s*\("),
    re.compile(r"\bimport\s+anthropic\b"),
    re.compile(r"\bfrom\s+anthropic\s+import\b"),
    re.compile(r"\banthropic\.Anthropic\s*\("),
    re.compile(r"\bfrom\s+google\s+import\s+genai\b"),
    re.compile(r"\bgenai\.Client\s*\("),
    re.compile(r"\bimport\s+google\.generativeai\b"),
]
# Chamadas de geração — o que REALMENTE reintroduz o bug, porque é onde os
# parâmetros de thinking/formato são (ou não são) passados.
PADROES_CHAMADA = [
    re.compile(r"\.chat\.completions\.create\s*\("),
    re.compile(r"\.messages\.create\s*\("),
    re.compile(r"\.models\.generate_content\s*\("),
]
PADROES = PADROES_SDK + PADROES_CHAMADA


def varrer(caminhos, adaptador: Path = ADAPTADOR,
           allowlist: set[str] | None = None) -> list[tuple[str, int, str]]:
    """Devolve `[(arquivo_relativo, linha, trecho)]` de toda violação.

    Ignora linhas de comentário e o conteúdo de docstrings simples de uma
    linha — um padrão CITADO em prosa (como os desta docstring) não é uma
    chamada, e um guard-rail que se auto-acusa não é utilizável.
    """
    allowlist = ALLOWLIST if allowlist is None else allowlist
    achados: list[tuple[str, int, str]] = []
    for raiz in caminhos:
        if not raiz.exists():
            continue
        for arq in sorted(raiz.rglob("*.py")):
            if arq.resolve() == adaptador.resolve() or "__pycache__" in arq.parts:
                continue
            try:
                rel = arq.relative_to(RAIZ).as_posix()
            except ValueError:
                rel = arq.as_posix()   # varredura de um diretório de teste
            if rel in allowlist:
                continue
            for i, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
                nua = linha.split("#", 1)[0]
                if any(p.search(nua) for p in PADROES):
                    achados.append((rel, i, linha.strip()))
    return achados


# --- o guard-rail em si -----------------------------------------------------

def test_nenhum_caminho_fora_do_adaptador_fala_com_o_sdk():
    achados = varrer(ESCOPO)
    assert not achados, (
        "SDK de LLM usado fora de src/espectro24/synthesize.py — o adaptador "
        "é quem garante `thinking: disabled` e o modo JSON (§3[D], v1.8.0). "
        "Se o desvio for deliberado, acrescente o arquivo à ALLOWLIST deste "
        "teste COM o motivo.\n"
        + "\n".join(f"  {a}:{n}  {t}" for a, n, t in achados))


def test_o_adaptador_continua_sendo_o_lugar_onde_o_sdk_vive():
    """Espelho do teste acima: se `synthesize.py` deixar de conter as
    chamadas, o guard-rail estaria vigiando um lugar vazio."""
    fonte = ADAPTADOR.read_text(encoding="utf-8")
    assert any(p.search(fonte) for p in PADROES_SDK)
    assert any(p.search(fonte) for p in PADROES_CHAMADA)


def test_o_adaptador_desliga_thinking_no_deepseek():
    """A razão de o guard-rail existir: é ESTE parâmetro que o caminho novo
    esquece. Se ele sair do adaptador, o guard-rail passaria a proteger um
    caminho que já não corrige nada."""
    fonte = ADAPTADOR.read_text(encoding="utf-8")
    assert '"thinking": {"type": "disabled"}' in fonte


# --- a fixture que prova que a varredura DETECTA ---------------------------
# Sem ela, um guard-rail quebrado (regex que nunca casa, escopo vazio) passaria
# exatamente como um guard-rail que não tem nada a detectar.

@pytest.mark.parametrize("violacao", [
    "from openai import OpenAI",
    "import openai",
    "client = OpenAI(api_key=k, base_url='https://api.deepseek.com')",
    "import anthropic",
    "from google import genai",
    "cli = genai.Client(api_key=k)",
    "resp = client.chat.completions.create(model=m, messages=msgs)",
    "resp = client.messages.create(model=m, messages=msgs)",
    "resp = client.models.generate_content(model=m, contents=u)",
])
def test_a_varredura_detecta_violacao_injetada(tmp_path, violacao):
    (tmp_path / "script_novo.py").write_text(
        f"def f():\n    {violacao}\n", encoding="utf-8")
    achados = varrer([tmp_path], allowlist=set())
    assert achados, f"varredura não detectou: {violacao}"
    assert achados[0][1] == 2


def test_a_varredura_ignora_o_padrao_em_comentario(tmp_path):
    """Um padrão CITADO em prosa não é uma chamada — sem isto, a própria
    docstring deste arquivo reprovaria o repositório."""
    (tmp_path / "s.py").write_text(
        "# from openai import OpenAI  <- citado, não chamado\n", encoding="utf-8")
    assert varrer([tmp_path], allowlist=set()) == []


def test_a_allowlist_isenta_o_arquivo_listado(tmp_path):
    alvo = tmp_path / "s.py"
    alvo.write_text("from openai import OpenAI\n", encoding="utf-8")
    assert varrer([tmp_path], allowlist=set())          # sem isenção: acusa
    assert varrer([tmp_path], allowlist={alvo.as_posix()}) == []


def test_a_allowlist_e_literal_e_pequena():
    """Uma allowlist que cresce em silêncio é uma allowlist que não protege.
    Este teste cai quando alguém acrescenta um arquivo — de propósito: a
    adição tem de vir acompanhada da atualização deste número e do motivo."""
    assert ALLOWLIST == {
        "scripts/diagnostico_fluencia.py",
        "scripts/diagnostico_fluencia_v2.py",
        "scripts/compare_models.py",
    }


def test_todo_arquivo_da_allowlist_existe():
    """Allowlist com entrada morta esconde o tamanho real da exceção."""
    for rel in ALLOWLIST:
        assert (RAIZ / rel).exists(), rel
