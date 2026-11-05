"""Guarda de quantidade (2026-11-05): reescrita determinística de
`exemplo_parafraseado`. Os pares abaixo são exemplos de desenvolvimento
(saídas da Fase 4), não o conjunto de avaliação do C22."""
import hashlib
import json
import re
from pathlib import Path

import pytest

from espectro24 import guarda_quantidade as G
from espectro24.models import BucketResult
from espectro24.synthesize import _construir_temas, synthesize_bucket

LISTA_FINETUNE = Path(__file__).resolve().parents[1] / "finetune" / "metricas" / "palavras_quantidade.txt"


# --- a lista é a CONGELADA do M1 -------------------------------------------

def test_lista_e_a_congelada():
    assert hashlib.sha256(G.LISTA.read_bytes()).hexdigest() == G.LISTA_SHA256


@pytest.mark.skipif(not LISTA_FINETUNE.exists(), reason="finetune/ não está ligado a este checkout")
def test_lista_igual_a_do_m1():
    assert G.LISTA.read_bytes() == LISTA_FINETUNE.read_bytes()


def test_detecta_como_o_m1():
    assert G.tem_quantidade("Algumas reviews apontam isso.")
    assert not G.tem_quantidade("Reviews apontam isso.")
    assert not G.tem_quantidade("A segunda metade do filme.")          # posição, fora da lista
    assert not G.tem_quantidade("pouquíssimos")                          # palavra inteira


def test_toda_expressao_da_lista_tem_regra_ou_esta_declarada_sem_regra():
    """Nada fica sem decisão: ou tem regra, ou está aqui como 'sem reescrita'."""
    sem = {e for e in G.carregar_lista() if G._despachar(e) is None}
    assert sem == {"poucos", "poucas", "minoria", "parcela", "unanimidade", "unânime",
                   "unânimes", "consenso"}


# --- reescritas -------------------------------------------------------------

CASOS = [
    ("Algumas reviews medianas apontam que o roteiro é previsível.",
     "Reviews medianas apontam que o roteiro é previsível."),
    ("Muitos espectadores acham o filme longo demais.", "Espectadores acham o filme longo demais."),
    ("Várias reviews destacam a fotografia.", "Reviews destacam a fotografia."),
    ("A fotografia é frequentemente elogiada por sua beleza.", "A fotografia é elogiada por sua beleza."),
    ("Frequentemente, a trilha é citada como ponto alto.", "A trilha é citada como ponto alto."),
    ("A trilha, frequentemente, é citada como ponto alto.", "A trilha é citada como ponto alto."),
    ("A maioria das reviews positivas elogia a atuação.", "As reviews positivas elogiam a atuação."),
    ("Parte do público reclama do ritmo.", "Espectadores reclamam do ritmo."),
    ("Há quem aprecie a violência exagerada.", "Espectadores apreciam a violência exagerada."),
    ("O filme é lento em alguns momentos.", "O filme é lento em certos momentos."),
    ("Embora alguns considerem o final fraco, o resto funciona.",
     "Embora espectadores considerem o final fraco, o resto funciona."),
    ("A cena é criticada por muitos como forçada.", "A cena é criticada por espectadores como forçada."),
    ("O filme tem muitas cenas de diálogo.", "O filme tem cenas de diálogo."),
    ("Algumas reviews criticam o ritmo, mas outras o defendem.",
     "Reviews criticam o ritmo, mas outras o defendem."),
    ("Alguns elogiam a direção, enquanto outros criticam o roteiro.",
     "Espectadores elogiam a direção, enquanto outros criticam o roteiro."),
    ("Muitas vezes o ritmo cansa.", "O ritmo cansa."),
    ("Um número significativo de reviews relatam tédio.", "Reviews relatam tédio."),
    ("Certas reviews mencionam o final.", "Reviews mencionam o final."),
]


@pytest.mark.parametrize("antes,depois", CASOS)
def test_reescreve(antes, depois):
    r = G.reescrever(antes)
    assert r.texto == depois
    assert r.alterado and not r.residual and not r.pendentes


# --- o que NÃO se reescreve --------------------------------------------------

SEM_REESCRITA = [
    "Poucos espectadores elogiam o final.",            # "poucos" carrega sentido próprio
    "A minoria das reviews reclama.",
    "Não é frequentemente citado como ponto alto.",     # negação inverteria o sentido
    "O consenso é que o final é fraco.",
    "Muitos dos atores são amadores.",
    "Boa parte da projeção é arrastada.",               # quantidade do filme, não das reviews
    "O filme dura alguns minutos a mais.",              # tempo medido
    "O filme foi revisto várias vezes.",
]


@pytest.mark.parametrize("texto", SEM_REESCRITA)
def test_sem_reescrita_segura_deixa_o_texto_intacto(texto):
    r = G.reescrever(texto)
    assert r.texto == texto and not r.alterado
    assert r.pendentes and r.residual


# --- invariantes --------------------------------------------------------------

def test_nunca_introduz_numero():
    for antes, _ in CASOS:
        r = G.reescrever(antes)
        assert re.findall(r"\d+", r.texto) == re.findall(r"\d+", antes)
    r = G.reescrever("Alguns 10 espectadores acham ruim.")
    assert not re.search(r"\d", r.texto.replace("10", ""))


def test_nao_introduz_expressao_da_lista():
    for antes, _ in CASOS:
        r = G.reescrever(antes)
        assert not G.tem_quantidade(r.texto), r.texto


def test_idempotente():
    for antes, _ in CASOS:
        uma = G.reescrever(antes).texto
        assert G.reescrever(uma).texto == uma


def test_texto_sem_quantidade_nao_muda():
    t = "O roteiro é previsível e a fotografia é bonita."
    r = G.reescrever(t)
    assert r.texto == t and not r.alterado and not r.pendentes and not r.residual


def test_mesma_quantidade_de_frases():
    antes = "Algumas reviews elogiam. Muitas criticam o ritmo. Frequentemente se fala da trilha."
    r = G.reescrever(antes)
    assert r.texto.count(". ") + 1 == antes.count(". ") + 1
    assert r.texto == "Reviews elogiam. Reviews criticam o ritmo. Se fala da trilha."


def test_maiuscula_no_inicio_da_frase():
    assert G.reescrever("Várias críticas apontam isso.").texto.startswith("Críticas")
    assert G.reescrever("O filme cansa, e várias críticas apontam isso.").texto == \
        "O filme cansa, e críticas apontam isso."


# --- no pipeline ----------------------------------------------------------------

def _json_com(exemplos):
    return json.dumps({"temas": [{"tema": f"t{i}", "mencoes_aproximadas": 10 - i,
                                  "n_reviews_analisadas": 10, "exemplo_parafraseado": e}
                                 for i, e in enumerate(exemplos)],
                       "observacao_geral": "grupo"}, ensure_ascii=False)


def test_construir_temas_reescreve_e_registra_o_original():
    ex = ["Muitas reviews elogiam a trilha.", "A fotografia é bonita.", "Poucos gostaram do final."]
    temas = _construir_temas(json.loads(_json_com(ex)), 10)
    assert [t.tema for t in temas] == ["t0", "t1", "t2"]                 # ninguém some, ordem igual
    assert [t.mencoes_aproximadas for t in temas] == [10, 9, 8]            # a barra não muda
    assert temas[0].exemplo_parafraseado == "Reviews elogiam a trilha."
    assert temas[0].quantidade_reescrita and temas[0].exemplo_antes_da_guarda == ex[0]
    assert not temas[1].quantidade_reescrita and temas[1].exemplo_antes_da_guarda is None
    assert temas[2].exemplo_parafraseado == ex[2]
    assert temas[2].quantidade_pendente and not temas[2].quantidade_reescrita


def test_synthesize_bucket_aplica_a_guarda_a_qualquer_fonte():
    ex = ["Algumas reviews acham o filme longo.", "Várias críticas elogiam a direção.",
          "Frequentemente a trilha é citada."]

    def cliente(system, user, model):
        return _json_com(ex)

    from tests.test_synthesize import _bucket_com_reviews
    b = synthesize_bucket(_bucket_com_reviews(n=10), client_call=cliente)
    assert len(b.temas) == 3
    assert not any(G.tem_quantidade(t.exemplo_parafraseado) for t in b.temas)
    assert all(t.quantidade_reescrita for t in b.temas)
