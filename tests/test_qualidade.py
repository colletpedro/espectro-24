"""Blocklist de resenha-speak e verificações mecânicas da prosa (§D2, v1.9.8).

A blocklist é DADO VERSIONADO fora do prompt — listar as expressões dentro
do prompt as introduziria no contexto, o que em vários modelos aumenta a
chance de aparecerem. Verificação em código, no padrão das demais checagens
mecânicas do projeto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import qualidade as q  # noqa: E402


# ------------------------------------------------------------- carregamento

def test_a_blocklist_e_arquivo_versionado_fora_do_prompt():
    assert q.ARQ_BLOCKLIST.exists()
    assert q.ARQ_BLOCKLIST.suffix == ".txt"


def test_carrega_expressoes_ignorando_comentario_e_vazio():
    exprs = q.carregar_blocklist()
    assert exprs
    assert all(not e.startswith("#") and e.strip() for e in exprs)


def test_as_expressoes_semente_estao_na_lista():
    exprs = set(q.carregar_blocklist())
    for e in ("uma jornada", "vale a pena conferir", "prende do inicio ao fim"):
        assert e in exprs


def test_a_blocklist_nao_aparece_no_prompt_do_narrador():
    """Se as expressões entrarem no prompt, elas entram no contexto — que é
    exatamente o que este desenho evita."""
    from espectro24 import briefing as br
    p = br.PROMPT_NARRADOR_BRIEFING.lower()
    for e in q.carregar_blocklist():
        assert e not in p


# ------------------------------------------------------------- detecção

def test_detecta_expressao_simples():
    achados = q.achar_resenha_speak("O filme é uma jornada e tanto.")
    assert [a["expressao"] for a in achados] == ["uma jornada"]


def test_detecta_ignorando_acento():
    """'de tirar o fôlego' tem de casar a entrada sem acento da lista."""
    achados = q.achar_resenha_speak("Uma cena de tirar o fôlego.")
    assert achados and achados[0]["expressao"] == "de tirar o folego"


def test_detecta_ignorando_caixa():
    assert q.achar_resenha_speak("VALE A PENA CONFERIR!")


def test_conta_ocorrencias_repetidas():
    txt = "uma jornada aqui, uma jornada ali"
    achados = q.achar_resenha_speak(txt)
    assert sum(a["n"] for a in achados) == 2


def test_texto_limpo_nao_acusa_nada():
    txt = ("O filme dura 111 minutos e a maioria das notas aponta um ritmo "
           "lento. Para esse grupo, a tensão não se sustenta.")
    assert q.achar_resenha_speak(txt) == []


def test_devolve_o_trecho_para_auditoria():
    """Mesma política de telemetria declarada do resto do projeto: o número
    sozinho não permite conferir se o achado é real."""
    a = q.achar_resenha_speak("Sem dúvida, vale a pena conferir esse filme.")[0]
    assert "vale a pena conferir" in a["trecho"].lower()


def test_nao_casa_dentro_de_palavra_maior():
    """'um must' não pode casar em 'um mustang'."""
    assert q.achar_resenha_speak("um mustang vermelho") == []


# ----------------------------------------------- checagens de formato/número

def test_formato_invalido_pega_json_embrulhado():
    assert q.formato_invalido('{"narrativa": "texto"}')
    assert q.formato_invalido("```\ntexto\n```")
    assert not q.formato_invalido("Um texto de prosa normal.")


def test_tokens_numericos_extrai_numeros_e_percentuais():
    assert q.tokens_numericos("111 minutos e ~79% das notas") == {"111", "79"}


def test_numeros_inventados_sao_detectados():
    """A defesa que neutraliza o risco histórico do Gemini de inflar
    contagem: qualquer número fora do briefing é reprovado."""
    permitidos = {"1997", "111", "79", "17", "3"}
    assert q.numeros_inventados("O filme de 1997 tem 111 min", permitidos) == set()
    assert q.numeros_inventados("nota média 8.5", permitidos) == {"8", "5"}


def test_numeros_do_briefing_reune_tudo_que_pode_aparecer():
    from espectro24 import briefing as br
    b = br.montar_briefing({
        "buckets": [{"bucket": "negativas", "n_validas": 40,
                     "estado_piso": "completa", "observacao_geral": "",
                     "temas": [{"tema": "t", "mencoes_aproximadas": 30,
                                "n_reviews_analisadas": 40}]}],
        "distribuicao": {"n_notas_total": 100,
                         "por_bucket": {"negativas": 55}},
    })
    nums = q.numeros_do_briefing(b)
    for esperado in ("40", "30", "55", "75"):     # n, menções, share, fração
        assert esperado in nums


def test_ordem_dos_movimentos_confere_a_do_briefing():
    briefing = {"movimento3": {"ordem": ["positivas", "negativas"]},
                "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)"},
                           "negativas": {"rotulo_peso": "uma fração mínima das notas (~3%)"}}}
    bom = ("... a grande maioria das notas (~80%) gostou. "
           "Já uma fração mínima das notas (~3%) reclamou.")
    ruim = ("... uma fração mínima das notas (~3%) reclamou. "
            "Já a grande maioria das notas (~80%) gostou.")
    assert q.ordem_dos_grupos_ok(bom, briefing)
    assert not q.ordem_dos_grupos_ok(ruim, briefing)


def test_rotulos_de_peso_presentes_literalmente():
    briefing = {"movimento3": {"ordem": ["positivas"]},
                "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)"}}}
    assert q.rotulos_peso_faltando("a grande maioria das notas (~80%) gostou",
                                   briefing) == []
    assert q.rotulos_peso_faltando("quase todo mundo gostou", briefing)


def test_vocabulario_do_peso_proibe_reviews_e_publico():
    assert q.vocabulario_peso_violado("a maioria das reviews gostou")
    assert q.vocabulario_peso_violado("a maioria do público gostou")
    assert not q.vocabulario_peso_violado("a maioria das notas gostou")


# ------------------------------------------------------------- verificar()

def _briefing_min():
    return {"movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)",
                                     "marcacao_perspectiva": "nenhuma",
                                     "temas": []}},
            "orcamento_frases": {"movimento1": (0, 0)}}


def test_verificar_devolve_todas_as_flags():
    r = q.verificar("a grande maioria das notas (~80%) gostou do filme.",
                    _briefing_min())
    for chave in ("formato_invalido", "numeros_inventados", "rotulos_faltando",
                  "ordem_incorreta", "vocabulario_peso", "resenha_speak",
                  "n_flags"):
        assert chave in r


def test_verificar_conta_zero_flags_num_texto_limpo():
    r = q.verificar("a grande maioria das notas (~80%) gostou do filme.",
                    _briefing_min())
    assert r["n_flags"] == 0


def test_verificar_soma_as_flags_disparadas():
    r = q.verificar('{"narrativa": "a maioria das reviews adorou, uma jornada"}',
                    _briefing_min())
    assert r["n_flags"] >= 3      # formato + vocabulário + resenha-speak
