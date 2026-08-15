"""[§D2, v1.9.9] Best-of-3 com seleção POR CÓDIGO — Entrega 5.

O que estes testes travam: a escolha entre N narrativas é MECÂNICA e
determinística. Nenhum LLM julga prosa aqui — os critérios são contagem de
clichê, repetição de construção quantificadora, ritmo (proxy declarado) e
cobertura dos temas. Testes antes do módulo, na ordem da sessão.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import briefing as br  # noqa: E402
from espectro24 import selecao_narrativa as sn  # noqa: E402


def _briefing():
    return br.montar_briefing({
        "ficha": {"titulo": "F", "ano": 1997, "diretor": "D",
                  "generos": ["terror"], "sinopse_oficial": "s", "duracao_min": 111},
        "total_reviews_observadas": 100,
        "buckets": [
            {"bucket": "positivas", "n_validas": 40, "estado_piso": "completa",
             "observacao_geral": "", "temas": [
                 {"tema": "atmosfera perturbadora", "mencoes_aproximadas": 30,
                  "n_reviews_analisadas": 40},
                 {"tema": "ritmo lento", "mencoes_aproximadas": 12,
                  "n_reviews_analisadas": 40}]},
            {"bucket": "negativas", "n_validas": 40, "estado_piso": "completa",
             "observacao_geral": "", "temas": [
                 {"tema": "roteiro fraco", "mencoes_aproximadas": 20,
                  "n_reviews_analisadas": 40}]},
        ],
        "distribuicao": {"n_notas_total": 100,
                         "por_bucket": {"positivas": 80, "negativas": 20}},
    })


def _limpo(b, extra=""):
    """Narrativa que passa em todas as flags — base para variar UM critério
    de cada vez."""
    pos = b["grupos"]["positivas"]["rotulo_peso"]
    neg = b["grupos"]["negativas"]["rotulo_peso"]
    return (f"Um filme de 1997 dirigido por D.\n\n"
            f"A experiência é de ritmo lento e atmosfera densa.\n\n"
            f"{pos} elogia: a maioria cita a atmosfera perturbadora e "
            f"boa parte aponta o ritmo lento. {neg} discorda, e "
            f"vários citam o roteiro fraco. {extra}")


# ------------------------------------------------------- eliminatório

def test_candidato_com_flag_e_eliminado_mesmo_sendo_melhor_nos_proxies():
    """Flag limpa é ELIMINATÓRIA: um texto com número inventado não compete
    por ritmo. Os proxies ordenam entre os honestos, nunca contra."""
    b = _briefing()
    sujo = _limpo(b) + " A nota média é 8."
    esc = sn.selecionar([sujo, _limpo(b)], b)
    assert esc["indice"] == 1
    assert esc["motivo"] == "melhor_entre_limpos"
    assert esc["candidatos"][0]["eliminado"] is True


def test_menos_cliche_vence():
    b = _briefing()
    com = _limpo(b, "Em suma, vale a pena conferir.")
    esc = sn.selecionar([com, _limpo(b)], b)
    assert esc["indice"] == 1
    assert esc["criterio_decisivo"] == "cliche"


def test_menos_repeticao_de_construcao_vence():
    """O critério que nasce do defeito medido em `cure`."""
    b = _briefing()
    pos, neg = (b["grupos"]["positivas"]["rotulo_peso"],
                b["grupos"]["negativas"]["rotulo_peso"])
    repetitivo = (f"Um filme de 1997.\n\nRitmo lento.\n\n{pos} elogia: "
                  f"a maioria cita a atmosfera perturbadora, a maioria aponta "
                  f"o ritmo lento. {neg} discorda: a maioria cita o roteiro "
                  f"fraco.")
    esc = sn.selecionar([repetitivo, _limpo(b)], b)
    assert esc["indice"] == 1
    # Acima do teto a repetição é FLAG, e flag é eliminatória — o critério de
    # ordenação por repetição só decide ENTRE os limpos (teste abaixo).
    assert esc["candidatos"][0]["eliminado"] is True


def test_entre_limpos_a_menor_repeticao_vence():
    b = _briefing()
    pos, neg = (b["grupos"]["positivas"]["rotulo_peso"],
                b["grupos"]["negativas"]["rotulo_peso"])
    duas = (f"Um filme de 1997.\n\nRitmo lento e atmosfera densa.\n\n"
            f"{pos} elogia: a maioria cita a atmosfera perturbadora e "
            f"a maioria aponta o ritmo lento. {neg} discorda, e vários "
            f"citam o roteiro fraco.")
    uma = (f"Um filme de 1997.\n\nRitmo lento e atmosfera densa.\n\n"
           f"{pos} elogia: a maioria cita a atmosfera perturbadora e "
           f"boa parte aponta o ritmo lento. {neg} discorda, e vários "
           f"citam o roteiro fraco.")
    esc = sn.selecionar([duas, uma], b)
    assert [c["n_flags"] for c in esc["candidatos"]] == [0, 0]
    assert esc["indice"] == 1
    assert esc["criterio_decisivo"] == "repeticao"


def test_ritmo_e_proxy_DECLARADO_e_arredondado():
    """Desvio-padrão do comprimento de frase, EM PALAVRAS INTEIRAS. O
    arredondamento é deliberado: sem ele, um float nunca empata e a
    cobertura de temas jamais decidiria nada."""
    iguais = "Um dois tres. Um dois tres. Um dois tres."
    variado = "Um. Um dois tres quatro cinco seis sete oito nove dez. Um dois."
    assert sn.ritmo(iguais) == 0
    assert sn.ritmo(variado) > sn.ritmo(iguais)
    assert isinstance(sn.ritmo(variado), int)


def test_cobertura_conta_os_temas_do_briefing():
    b = _briefing()
    assert sn.cobertura(_limpo(b), b) == 1.0
    parcial = "Um filme.\n\nRitmo lento.\n\nSó a atmosfera perturbadora aqui."
    assert 0 < sn.cobertura(parcial, b) < 1.0


def test_a_selecao_e_DETERMINISTICA():
    b = _briefing()
    cands = [_limpo(b, "Um."), _limpo(b), _limpo(b, "Dois tres.")]
    assert sn.selecionar(cands, b)["indice"] == sn.selecionar(cands, b)["indice"]


def test_empate_total_resolve_pelo_primeiro():
    b = _briefing()
    esc = sn.selecionar([_limpo(b), _limpo(b)], b)
    assert esc["indice"] == 0
    assert esc["criterio_decisivo"] == "empate"


# ------------------------------------------------------- fallback

def test_nenhum_limpo_seleciona_o_de_MENOR_SEVERIDADE_sem_descartar_tudo():
    """Fallback obrigatório: descartar as três seria jogar fora prosa boa
    por causa de uma frase."""
    b = _briefing()
    uma_flag = _limpo(b) + " A nota média é 8."
    duas_flags = ('{"narrativa": "' + _limpo(b) + ' A nota média é 8."}')
    esc = sn.selecionar([duas_flags, uma_flag], b)
    assert esc["indice"] == 1
    assert esc["motivo"] == "menor_severidade"
    assert esc["precisa_retry"] is True


def test_frases_infratoras_localizam_o_alvo_do_retry():
    """O retry é DIRECIONADO: só as frases que violam, com o motivo de cada
    uma. Reescrever o texto todo perderia o que já estava bom."""
    b = _briefing()
    texto = _limpo(b) + " A nota média é 8. Em suma, uma jornada."
    infratoras = sn.frases_infratoras(texto, b)
    alvos = " ".join(f["frase"] for f in infratoras)
    assert "nota média" in alvos and "Em suma" in alvos
    assert "A experiência é de ritmo lento" not in alvos
    motivos = {m for f in infratoras for m in f["motivos"]}
    assert "numero_inventado" in motivos and "cliche" in motivos


def test_frases_infratoras_vazio_num_texto_limpo():
    b = _briefing()
    assert sn.frases_infratoras(_limpo(b), b) == []


def test_prompt_de_retry_manda_preservar_o_resto_literalmente():
    b = _briefing()
    texto = _limpo(b) + " A nota média é 8."
    msg = sn.prompt_retry(texto, sn.frases_infratoras(texto, b))
    assert "A nota média é 8." in msg
    assert "literal" in msg.lower() or "intacta" in msg.lower()


def test_relatorio_expoe_todos_os_candidatos_para_auditoria():
    """Escolha mecânica que não mostra os perdedores não é auditável."""
    b = _briefing()
    esc = sn.selecionar([_limpo(b), _limpo(b, "Em suma.")], b)
    assert len(esc["candidatos"]) == 2
    for c in esc["candidatos"]:
        for chave in ("indice", "n_flags", "cliches", "repeticao_max",
                      "ritmo", "cobertura", "eliminado"):
            assert chave in c
