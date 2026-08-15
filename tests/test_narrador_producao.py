"""[§D2, v1.9.11] O narrador de PRODUÇÃO — briefing + best-of-3, no pipeline.

O que estes testes travam é a INTEGRAÇÃO, que é o defeito que a v1.9.11
corrige: até a v1.9.10, `cli.py` chamava o narrador pré-briefing e todo o
trabalho das três versões anteriores vivia só em `scripts/best_of_3.py`.
As narrativas aprovadas na leitura humana não eram as que o produto geraria.

Zero rede: o gerador é injetado.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import narrador  # noqa: E402
from espectro24.config import BEST_OF_N  # noqa: E402


# --------------------------------------------------------------- fixtures

def _output():
    return {
        "ficha": {"titulo": "F", "ano": 1997, "diretor": "D", "duracao_min": 111,
                  "generos": ["terror"], "sinopse_oficial": "uma sinopse"},
        "total_reviews_observadas": 100,
        "buckets": [
            {"bucket": "positivas", "n_validas": 40, "estado_piso": "completa",
             "observacao_geral": "", "temas": [
                 {"tema": "atmosfera perturbadora", "mencoes_aproximadas": 30,
                  "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"},
                 {"tema": "ritmo lento", "mencoes_aproximadas": 12,
                  "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"}]},
            {"bucket": "negativas", "n_validas": 40, "estado_piso": "completa",
             "observacao_geral": "", "temas": [
                 {"tema": "roteiro fraco", "mencoes_aproximadas": 20,
                  "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"}]},
        ],
        "distribuicao": {"n_notas_total": 100,
                         "por_bucket": {"positivas": 80, "negativas": 20}},
    }


def _texto_limpo(extra="", pos="a grande maioria das notas (~80%)",
                 neg="uma parcela das notas (~20%)"):
    return (f"Um filme de 1997 dirigido por D.\n\n"
            f"A experiência é de ritmo lento e atmosfera densa.\n\n"
            f"{pos} concentra o elogio. A maioria cita a atmosfera "
            f"perturbadora, ao passo que boa parte aponta o ritmo lento.\n\n"
            f"{neg} discorda, e vários citam o roteiro fraco. {extra}")


def _gerador(textos):
    """Injeta as respostas do LLM, em ordem, e registra as chamadas."""
    chamadas = []

    def gerar(system, user):
        chamadas.append({"system": system, "user": user})
        i = min(len(chamadas) - 1, len(textos) - 1)
        return textos[i], {"prompt_tokens": 10, "completion_tokens": 20,
                           "cache_hit_tokens": 0, "cache_miss_tokens": 10}, 1.5

    gerar.chamadas = chamadas
    return gerar


# ------------------------------------------------- o caminho é o do briefing

def test_usa_o_prompt_do_BRIEFING_nao_o_do_narrador_antigo():
    """O defeito da v1.9.10 em uma asserção: o caminho de produção tem de
    ser o do briefing determinístico."""
    from espectro24 import briefing as br
    g = _gerador([_texto_limpo()])
    narrador.narrar(_output(), gerar=g)
    assert g.chamadas[0]["system"] == br.PROMPT_NARRADOR_BRIEFING
    # e a mensagem do usuário é o briefing serializado, não o dump antigo
    assert "BRIEFING (todas as decisões já foram tomadas" in g.chamadas[0]["user"]


def test_gera_BEST_OF_N_candidatos_independentes():
    g = _gerador([_texto_limpo(), _texto_limpo("Um."), _texto_limpo("Dois tres.")])
    r = narrador.narrar(_output(), gerar=g)
    assert len(g.chamadas) == BEST_OF_N
    assert len(r.candidatos) == BEST_OF_N
    # mesma mensagem nas N chamadas — são amostras independentes do MESMO
    # briefing, não um refinamento em cadeia
    assert len({c["user"] for c in g.chamadas}) == 1


def test_a_selecao_e_por_codigo_e_o_motivo_fica_registrado():
    g = _gerador([_texto_limpo(), _texto_limpo("Um."), _texto_limpo("Dois tres.")])
    r = narrador.narrar(_output(), gerar=g)
    assert r.escolha["motivo"] == "melhor_entre_limpos"
    assert r.texto == r.candidatos[r.escolha["indice"]]
    assert len(r.escolha["candidatos"]) == BEST_OF_N


def test_telemetria_soma_tokens_e_latencia_de_TODAS_as_chamadas():
    """3 chamadas por filme é o custo declarado do best-of-3 — some, não
    reporte só a da narrativa escolhida."""
    g = _gerador([_texto_limpo()])
    r = narrador.narrar(_output(), gerar=g)
    assert r.n_chamadas == BEST_OF_N
    assert r.uso["completion_tokens"] == 20 * BEST_OF_N
    assert r.latencia_s == pytest.approx(1.5 * BEST_OF_N)


# ------------------------------------------------- fallback (retry dirigido)

def test_sem_nenhuma_limpa_faz_retry_DIRECIONADO_e_aplica_se_melhorar():
    sujo = _texto_limpo("A nota média é 8.")      # número inventado
    g = _gerador([sujo, sujo, sujo, _texto_limpo()])
    r = narrador.narrar(_output(), gerar=g)
    assert r.escolha["motivo"] == "menor_severidade"
    assert r.retry is not None and r.retry["aplicado"] is True
    assert r.texto == _texto_limpo()
    assert r.n_chamadas == BEST_OF_N + 1
    # o retry recebeu as FRASES infratoras, não o texto inteiro para reescrever
    assert "A nota média é 8." in g.chamadas[-1]["user"]
    assert "FRASES A CORRIGIR" in g.chamadas[-1]["user"]


def test_retry_que_NAO_melhora_e_descartado():
    """Um retry que piora não é conserto — a de menor severidade prevalece."""
    sujo = _texto_limpo("A nota média é 8.")
    pior = '{"narrativa": "' + sujo + ' 9 10 11."}'   # formato + mais números
    g = _gerador([sujo, sujo, sujo, pior])
    r = narrador.narrar(_output(), gerar=g)
    assert r.retry["aplicado"] is False
    assert r.texto == sujo


def test_sem_retry_quando_ha_candidata_limpa():
    g = _gerador([_texto_limpo("A nota média é 8."), _texto_limpo(), _texto_limpo()])
    r = narrador.narrar(_output(), gerar=g)
    assert r.retry is None
    assert r.n_chamadas == BEST_OF_N


# ------------------------------------------------- robustez

def test_resposta_vazia_nao_derruba_o_filme():
    """Uma amostra vazia é uma amostra perdida, não uma falha do estágio —
    o best-of-N existe justamente para sobreviver a isso."""
    g = _gerador([""])
    r = narrador.narrar(_output(), gerar=g)
    assert r.falhou is True
    assert r.texto == ""


def test_uma_vazia_entre_tres_nao_impede_a_selecao():
    g = _gerador([_texto_limpo(), "", _texto_limpo("Um.")])
    r = narrador.narrar(_output(), gerar=g)
    assert r.falhou is False
    assert r.texto
    assert len(r.candidatos) == 2, "a vazia não entra na disputa"


def test_verificacao_acompanha_o_texto_escolhido():
    g = _gerador([_texto_limpo()])
    r = narrador.narrar(_output(), gerar=g)
    assert r.verificacao["n_flags"] == 0
    assert "grupos_sem_paragrafo_proprio" in r.verificacao
