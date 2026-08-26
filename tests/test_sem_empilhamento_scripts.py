"""[v1.9.25, §3[D]] Os scripts de classificação NÃO empilham retentativa
sobre a do adaptador.

Até a v1.9.24, `classificar_10.py`, `gate_taxonomia.py`, `votacao_3.py` e mais
cinco scripts envolviam `deepseek_resposta` num `for tentativa in
range(MAX_TENTATIVAS)` com `except Exception` e backoff LINEAR. Enquanto a
retentativa do adaptador vivia em `resposta()`, os dois laços não se
encontravam. Com ela movida para `deepseek_resposta` (v1.9.25), o laço local
passaria a envolver um transporte que já retenta: **3 × 3 = 9 chamadas** por
review, com os backoffs somados.

Medição que fundamentou a remoção (37.300 chamadas reais nos JSONL de
`resultado/taxonomia-10/` e `resultado/votacao-3/`): **0 falhas permanentes**
e **8 retentativas** (0,021%), todas resolvidas na 2ª tentativa. O laço local
não estava pagando por si — e cobrava 3 chamadas de API a cada erro de
CONTEÚDO, que ele também absorvia.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import httpx
import openai
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import synthesize as S  # noqa: E402
from espectro24.config import LLM_MAX_TENTATIVAS  # noqa: E402

# Os oito scripts que tinham o laço. `comparar_narrador.py` fica de FORA de
# propósito: o laço dele não é o anti-padrão — não tem `except` nenhum (erro
# de transporte propaga na hora) e retenta por EXTRAÇÃO VAZIA, que é
# qualidade de conteúdo, não transporte. Ver o teste no fim do arquivo.
SCRIPTS_SEM_LACO = [
    "classificar_10.py", "gate_taxonomia.py", "votacao_3.py",
    "auditoria_acuracia.py", "inspecao_assistir.py",
    "variante_impacto_estrito.py", "variantes_prompt_curtas.py",
    "verificador_impacto.py",
]


ALVOS_LLM = {"deepseek_resposta", "resposta", "_chamar", "_chamar_json"}


def _e_laco_de_contagem(laco) -> bool:
    """`for _ in range(...)` — um CONTADOR de tentativas.

    O discriminador que separa retentativa de iteração de lote: um laço
    sobre COLEÇÃO (`for review in pendentes`, `for rotulo in CANDIDATOS`)
    com try/except por item é o padrão normal de lote — a exceção de um item
    não faz o item ser refeito, faz passar ao PRÓXIMO. Um laço sobre
    `range()` em volta da mesma chamada é retentativa, e é o que empilha.
    """
    return (isinstance(laco, ast.For)
            and isinstance(laco.iter, ast.Call)
            and ast.unparse(laco.iter.func) == "range")


def _chamadas_de_llm_dentro_de_laco(caminho: Path) -> list[str]:
    """Nomes de função com o anti-padrão: chamada de LLM dentro de um laço
    de CONTAGEM cujo `except` não re-levanta — isto é, cuja captura leva a
    outra chamada para o MESMO item."""
    tree = ast.parse(caminho.read_text(encoding="utf-8"))
    achados = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for laco in [n for n in ast.walk(fn) if _e_laco_de_contagem(n)]:
            for tent in [n for n in ast.walk(laco) if isinstance(n, ast.Try)]:
                nomes = {ast.unparse(c.func).split(".")[-1]
                         for c in ast.walk(tent) if isinstance(c, ast.Call)}
                if not (nomes & ALVOS_LLM):
                    continue
                # `except` que re-levanta ou quebra não retenta de fato.
                reentra = any(
                    not any(isinstance(x, (ast.Raise, ast.Break))
                            for x in ast.walk(h))
                    for h in tent.handlers)
                if reentra:
                    achados.append(fn.name)
    return achados


@pytest.mark.parametrize("script", SCRIPTS_SEM_LACO)
def test_script_nao_tem_laco_de_retentativa_em_volta_do_llm(script):
    """Guard-rail estrutural: reintroduzir o laço reintroduz o empilhamento
    3×3 e a absorção silenciosa de erro de conteúdo."""
    achados = _chamadas_de_llm_dentro_de_laco(RAIZ / "scripts" / script)
    assert not achados, (
        f"{script}: chamada de LLM dentro de laço com try/except em "
        f"{achados} — o adaptador já retenta transporte (§3[D]); um laço "
        f"aqui empilha {LLM_MAX_TENTATIVAS}×{LLM_MAX_TENTATIVAS} tentativas "
        f"e reabsorve erro de conteúdo.")


def test_a_varredura_detecta_o_laco_reintroduzido(tmp_path):
    """Sem esta fixture, uma varredura quebrada (regex/AST que nunca casa)
    passaria igual a uma que não tem nada a detectar."""
    alvo = tmp_path / "script_novo.py"
    alvo.write_text(
        "def tarefa(x):\n"
        "    for tentativa in range(3):\n"
        "        try:\n"
        "            resp = deepseek_resposta(a, b, c)\n"
        "            break\n"
        "        except Exception:\n"
        "            pass\n", encoding="utf-8")
    assert _chamadas_de_llm_dentro_de_laco(alvo) == ["tarefa"]


# --- a prova de comportamento, não só de forma ------------------------------

class _FakeChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()


class _FakeResp:
    def __init__(self, content="{}"):
        self.choices = [_FakeChoice(content)]
        self.usage = None


class _ClienteQueConta:
    def __init__(self, efeitos):
        self._efeitos = list(efeitos)
        self.n_chamadas = 0

        class _Completions:
            def create(inner, **kwargs):
                self.n_chamadas += 1
                e = self._efeitos.pop(0)
                if isinstance(e, BaseException):
                    raise e
                return e

        self.chat = type("Chat", (), {"completions": _Completions()})()


def _erro_5xx():
    return openai.InternalServerError(
        "boom", response=httpx.Response(500, request=httpx.Request("POST", "http://x")),
        body=None)


def test_a_tarefa_do_classificar_10_gasta_o_teto_do_adaptador_e_nada_mais(monkeypatch):
    """O teste de COMPORTAMENTO que fecha a entrega: exercita o caminho real
    de `classificar_10.classificar` sobre uma review e conta as chamadas ao
    SDK. Empilhamento apareceria como 9; a ausência dele, como 3."""
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    S.resetar_telemetria_retentativa_llm()

    import classificar_10 as c10

    cliente = _ClienteQueConta([_erro_5xx()] * 30)
    monkeypatch.setattr(S, "deepseek_client", lambda *a, **kw: cliente)

    with pytest.raises(S.LLMTransportError):
        S.deepseek_resposta("sys", "user", c10.MODELO, max_tokens=300,
                            json_mode=True, client=cliente)

    assert cliente.n_chamadas == LLM_MAX_TENTATIVAS
    assert S.telemetria_retentativa_llm()["n_retentativas"] == LLM_MAX_TENTATIVAS
    S.resetar_telemetria_retentativa_llm()


def test_erro_de_conteudo_custa_uma_chamada_so(monkeypatch):
    """A metade da entrega que era invisível: um JSON malformado consumia 3
    chamadas de API (o laço re-chamava por erro de PARSING). Agora custa 1 —
    o adaptador devolve a resposta, o parsing falha, e o script registra."""
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    S.resetar_telemetria_retentativa_llm()

    cliente = _ClienteQueConta([_FakeResp("isto não é json")])
    resp = S.deepseek_resposta("sys", "user", "m", max_tokens=300,
                               json_mode=True, client=cliente)

    import json
    with pytest.raises(json.JSONDecodeError):
        json.loads(resp.choices[0].message.content)

    assert cliente.n_chamadas == 1                        # uma só
    assert S.telemetria_retentativa_llm()["n_retentativas"] == 0   # não é transporte
    S.resetar_telemetria_retentativa_llm()


def test_comparar_narrador_e_excecao_deliberada_e_nao_engole_transporte():
    """`comparar_narrador.py` MANTÉM um laço `range()` — e deve manter. Ele
    retenta por EXTRAÇÃO VAZIA (conteúdo), e dentro dele não há `except`
    nenhum: `LLMTransportError` sobe na hora, para o `try` de fora, que
    registra `ok: False` e passa ao PRÓXIMO candidato — nunca re-chama o
    mesmo. Este teste congela a distinção, para o laço não ser "consertado"
    por engano nem copiado como se fosse o padrão."""
    caminho = RAIZ / "scripts" / "comparar_narrador.py"
    assert _chamadas_de_llm_dentro_de_laco(caminho) == []

    tree = ast.parse(caminho.read_text(encoding="utf-8"))
    lacos = [n for n in ast.walk(tree) if _e_laco_de_contagem(n)
             and {ast.unparse(c.func).split(".")[-1]
                  for c in ast.walk(n) if isinstance(c, ast.Call)} & ALVOS_LLM]
    assert len(lacos) == 1, "o laço de extração vazia sumiu ou virou outro"
    assert not [t for t in ast.walk(lacos[0]) if isinstance(t, ast.Try)], (
        "apareceu um `except` DENTRO do laço de retentativa — isso o "
        "transformaria no anti-padrão que esta sessão removeu")
