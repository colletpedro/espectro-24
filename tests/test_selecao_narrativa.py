"""[§D2, v1.9.9] Best-of-3 com seleção POR CÓDIGO — Entrega 5.

O que estes testes travam: a escolha entre N narrativas é MECÂNICA e
determinística. Nenhum LLM julga prosa aqui — os critérios são contagem de
clichê, repetição de construção quantificadora, ritmo (proxy declarado) e
cobertura dos temas. Testes antes do módulo, na ordem da sessão.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
            f"{pos} concentra as avaliações mais favoráveis. A maioria "
            f"cita a atmosfera perturbadora, ao passo que boa parte "
            f"aponta o ritmo lento.\n\n"
            f"{neg} discorda, e vários citam o roteiro fraco. {extra}")


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
            f"a maioria aponta o ritmo lento.\n\n{neg} discorda, e vários "
            f"citam o roteiro fraco.")
    uma = (f"Um filme de 1997.\n\nRitmo lento e atmosfera densa.\n\n"
           f"{pos} elogia: a maioria cita a atmosfera perturbadora e "
           f"boa parte aponta o ritmo lento.\n\n{neg} discorda, e vários "
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


# ============================================================ v1.9.9
# Fechamento — cobertura ESTRUTURAL (ordem + grupo), não léxica
#
# Substitui o casamento de termos com o RÓTULO do tema, que tinha falso
# negativo SISTEMÁTICO em paráfrase — medido na calibração: em `cure`, 5
# dos 9 temas "ausentes" do candidato escolhido estavam no texto, só
# reescritos ("Pacing Lento e Deliberado" → "o andamento metódico").
# ============================================================

def _briefing_dois_grupos():
    return {
        "movimento3": {"ordem": ["positivas", "negativas"]},
        "grupos": {
            "positivas": {"rotulo_peso": "a maioria das notas (~80%)",
                          "temas": [{"tema": "atmosfera perturbadora"},
                                    {"tema": "ritmo lento e deliberado"}]},
            "negativas": {"rotulo_peso": "uma fração mínima das notas (~5%)",
                          "temas": [{"tema": "roteiro fraco e repetitivo"}]},
        },
    }


def test_cobertura_nao_pune_mais_a_parafrase_sem_overlap_lexical():
    """O defeito medido: zero sobreposição de palavras com o rótulo do
    tema, e o proxy antigo lia isso como ausência. A cobertura estrutural
    não olha para as palavras do tema — só para o span do grupo certo."""
    b = _briefing_dois_grupos()
    texto = ("Um filme.\n\nCadência pausada.\n\n"
             "a maioria das notas (~80%) concentra as leituras favoráveis. "
             "O ambiente carregado surpreende o público, ao passo que a "
             "cadência vagarosa intriga quem assiste com atenção. "
             "uma fração mínima das notas (~5%) discorda: aponta "
             "fragilidades sérias na condução do enredo escrito.")
    assert sn.cobertura(texto, b) == 1.0


def test_spans_por_grupo_ancoram_pelo_rotulo_de_peso_literal():
    b = _briefing_dois_grupos()
    pos, neg = (b["grupos"]["positivas"]["rotulo_peso"],
                b["grupos"]["negativas"]["rotulo_peso"])
    texto = f"Abertura. {pos} elogia. {neg} discorda."
    spans = sn.spans_por_grupo(texto, b)
    assert spans["positivas"].startswith(pos)
    assert spans["negativas"].startswith(neg)
    assert pos not in spans["negativas"] and neg not in spans["positivas"]


def test_conteudo_do_grupo_errado_nao_conta_para_o_grupo_certo():
    """GRUPO é garantido pelo span: um span longo e detalhado do grupo
    errado não empresta cobertura para o grupo que ficou raso."""
    b = _briefing_dois_grupos()
    pos, neg = (b["grupos"]["positivas"]["rotulo_peso"],
                b["grupos"]["negativas"]["rotulo_peso"])
    texto = (f"{pos} elogia isso. "
             f"{neg} discorda, aponta o roteiro fraco, critica a "
             f"condução do enredo, questiona o ritmo e ainda reclama da "
             f"atmosfera do longa inteiro.")
    # positivas: só a frase de abertura (única cláusula, sem "corpo" a
    # descartar) — 1 tema coberto de 2. negativas: várias cláusulas, mas
    # elas NUNCA contam para positivas, mesmo sendo sobre os MESMOS termos.
    spans = sn.spans_por_grupo(texto, b)
    assert "atmosfera" not in spans["positivas"]


def test_grupo_sem_rotulo_no_texto_conta_ZERO_nao_herda_de_outro():
    """Rótulo ausente (§qualidade.rotulos_peso_faltando já reprova isso à
    parte) não pode, aqui, virar cobertura emprestada de outro grupo."""
    b = _briefing_dois_grupos()
    neg = b["grupos"]["negativas"]["rotulo_peso"]
    texto = f"Um filme muito longo sobre atmosfera e ritmo. {neg} discorda do roteiro visto."
    spans = sn.spans_por_grupo(texto, b)
    assert spans["positivas"] == ""
    # positivas contribui 2 temas ao total e 0 cobertos, mesmo com
    # "atmosfera"/"ritmo" escritos no texto ANTES do span de negativas.
    cobertura = sn.cobertura(texto, b)
    assert cobertura < 1.0


def test_grupo_curto_de_uma_frase_nao_e_zerado_pelo_descarte_da_abertura():
    """A primeira cláusula só é descartada quando há MAIS de uma — um grupo
    com uma única frase não pode acabar sempre em zero por definição."""
    b = {"movimento3": {"ordem": ["negativas"]},
         "grupos": {"negativas": {"rotulo_peso": "a maioria das notas (~60%)",
                                  "temas": [{"tema": "roteiro fraco"}]}}}
    texto = "a maioria das notas (~60%) reclama do roteiro fraco e do final abrupto."
    assert sn.cobertura(texto, b) == 1.0


def test_cobertura_e_media_ponderada_por_numero_de_temas_do_grupo():
    """Um grupo com 5 temas pesa 5× mais que um com 1 — soma total sobre
    soma total, não média simples entre grupos (que daria 0,8, não 0,667)."""
    b = {"movimento3": {"ordem": ["positivas", "negativas"]},
         "grupos": {
             "positivas": {"rotulo_peso": "a maioria das notas (~80%)",
                          "temas": [{"tema": t} for t in "abcde"]},
             "negativas": {"rotulo_peso": "uma fração mínima das notas (~5%)",
                          "temas": [{"tema": "f"}]},
         }}
    pos, neg = (b["grupos"]["positivas"]["rotulo_peso"],
                b["grupos"]["negativas"]["rotulo_peso"])
    # positivas: abertura + 3 cláusulas de corpo — cobre 3 dos 5 temas
    # (0,6). negativas: uma única cláusula, cobre o seu único tema (1,0).
    # Média simples seria (0,6+1,0)/2=0,8; a ponderada é 4/6=0,667.
    texto = (f"{pos} destaca isso com força total. "
             f"Primeiro ponto relevante do filme todo. "
             f"Segundo ponto relevante do filme todo. "
             f"Terceiro ponto relevante do filme todo. "
             f"{neg} apenas discorda.")
    assert sn.cobertura(texto, b) == pytest.approx(4 / 6)


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
