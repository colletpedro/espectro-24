"""[experimento de briefing] O briefing e o prompt VARIANTE são o DEFAULT de
produção desde 2026-09-15 (ABERTO.md C14.18) — a troca aprovada pelo dono
depois do experimento pareado pré-registrado. `variante=None` continua
existindo, byte a byte o de ANTES do experimento, para reproduzir o braço
`controle` do experimento ou para reverter — não é mais o caminho de quem
chama sem pedir nada.

Todo marcador entra em PAR, como em `test_condicoes.py`: casos que marcam e
casos que não marcam. Os que marcam são paráfrases REAIS do catálogo.
"""
import json
import re
from pathlib import Path

import pytest

from espectro24 import condicoes as C

RAIZ = Path(__file__).resolve().parent.parent
RESULTADO = RAIZ / "resultado"
VAR = C.VARIANTE_EXPERIMENTO


def _briefings():
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = C.montar_briefing(d)
        if b is not None:
            yield d["slug"], b


def _doc(slug):
    return json.loads((RESULTADO / f"{slug}.json").read_text(encoding="utf-8"))


# ===========================================================================
# `variante=None` continua byte a byte o de ANTES do experimento — a garantia
# que sustenta reproduzir o braço `controle` ou reverter (não é mais a que
# um chamador sem argumento recebe; essa é a seção seguinte)
# ===========================================================================

def test_variante_none_nao_tem_marca_de_ressalva():
    for slug, b in _briefings():
        assert "RESSALVA NESTE TEMA" not in C.serializar_briefing(b), slug


def test_prompt_de_none_nao_tem_as_trocas():
    p = C.PROMPT_CONDICOES
    assert "adjetivo avaliativo" in p
    assert "9h." not in p
    assert "RESSALVA NESTE TEMA" not in p
    assert C.prompt_de(None) is C.PROMPT_CONDICOES


def test_prompt_variante_e_o_de_antes_mais_as_tres_trocas_e_nada_mais():
    """Desfazer as três trocas devolve o prompt de ANTES do experimento
    (`variante=None`) byte a byte."""
    p = C.PROMPT_CONDICOES_VARIANTE
    for velho, novo in C._TROCAS_DO_VARIANTE:
        assert p.count(novo) == 1
        p = p.replace(novo, velho)
    assert p == C.PROMPT_CONDICOES


def test_prompt_variante_traz_os_casos_do_piloto():
    p = C.PROMPT_CONDICOES_VARIANTE
    assert "adjetivo avaliativo" not in p
    for ruim in ("ambiguidade deliberada", "dramas que retratam hierarquias",
                 "clássicos de mestres autorais", "confronto marcante",
                 "contundentes", "rigor"):
        assert ruim in p, ruim
    assert "9h. ARCO É TRAJETÓRIA" in p
    assert "RESSALVA NESTE TEMA" in p


def test_troca_com_ancora_ausente_recusa():
    with pytest.raises(RuntimeError):
        C._aplicar_trocas("texto sem a âncora", C._TROCAS_DO_VARIANTE)


def test_variante_desconhecida_e_recusada():
    _, b = next(_briefings())
    with pytest.raises(ValueError):
        C.serializar_briefing(b, variante="outra")
    with pytest.raises(ValueError):
        C.prompt_de("outra")
    with pytest.raises(ValueError):
        C.gerar(_doc("napoleon-2023"), variante="outra")


# ===========================================================================
# Mesma seleção — a condição do pareamento
# ===========================================================================

def _ids(texto):
    return re.findall(r"^  \[([A-Z]{3}-[A-H])\]", texto, flags=re.M)


def test_variante_pede_os_mesmos_temas_na_mesma_ordem():
    for slug, b in _briefings():
        assert (_ids(C.serializar_briefing(b))
                == _ids(C.serializar_briefing(b, variante=VAR))), slug


def test_variante_so_acrescenta_linhas_de_marca():
    for slug, b in _briefings():
        prod = C.serializar_briefing(b).splitlines()
        var = [linha for linha in
               C.serializar_briefing(b, variante=VAR).splitlines()
               if not linha.lstrip().startswith("RESSALVA NESTE TEMA: ")]
        assert var == prod, slug


# ===========================================================================
# Algarismo — o variante não abre fonte nova
# ===========================================================================

def test_variante_nao_acrescenta_algarismo():
    """O trecho citado vem da paráfrase, que o briefing já carrega: o
    conjunto de algarismos do variante está contido no de ANTES do
    experimento (`variante=None`)."""
    for slug, b in _briefings():
        prod = set(C.algarismos_proibidos_no_briefing(b))
        var = set(C.algarismos_proibidos_no_briefing(b, variante=VAR))
        assert var <= prod, slug


def test_marca_de_ressalva_nao_tem_algarismo_proprio():
    assert not re.search(r"\d", C.marca_de_ressalva(["mas alguns acham lento"]))


# ===========================================================================
# ressalvas_do_tema — em PAR
# ===========================================================================

@pytest.mark.parametrize("parafrase, esperado", [
    # burning-2018 NEG-F — conector no meio: até o fim da frase
    ("A cinematografia e as imagens são reconhecidas como belas, mas "
     "insuficientes para salvar o filme.",
     ["mas insuficientes para salvar o filme"]),
    # hard-to-be-a-god NEG-F — conector abre a frase: até a vírgula
    ("Apesar de reconhecerem a qualidade técnica e a construção de mundo, os "
     "críticos afirmam que isso não compensa a experiência desagradável e "
     "tediosa.",
     ["Apesar de reconhecerem a qualidade técnica e a construção de mundo"]),
    # force-majeure-2014 POS-F
    ("Algumas reviews mencionam um ritmo lento e um desfecho que não agradou "
     "a todos, embora reconheçam que a abordagem funciona para a proposta do "
     "filme.",
     ["embora reconheçam que a abordagem funciona para a proposta do filme"]),
    # the-turin-horse NEG-E — pára na frase, não no texto
    ("Várias reviews reconhecem a qualidade da fotografia, mas argumentam que "
     "esses aspectos não compensam a falta de envolvimento. A beleza das "
     "imagens é vista como um atrativo isolado.",
     ["mas argumentam que esses aspectos não compensam a falta de "
      "envolvimento"]),
    # trecho contido noutro não se repete
    ("É ousado, mas funciona bem, apesar de algumas decisões questionáveis.",
     ["mas funciona bem, apesar de algumas decisões questionáveis"]),
    # acento no conector
    ("O visual é belo, porém frio.", ["porém frio"]),
])
def test_ressalvas_do_tema_marca(parafrase, esperado):
    assert C.ressalvas_do_tema({"exemplo": parafrase}) == esperado


@pytest.mark.parametrize("parafrase", [
    "O filme é longo e bonito.",
    "É mais lento do que devia, e mais bonito.",      # "mais" não é "mas"
    "Uma masmorra e um mastro dominam a cena.",       # prefixo não conta
    "",
])
def test_ressalvas_do_tema_nao_marca(parafrase):
    assert C.ressalvas_do_tema({"exemplo": parafrase}) == []


def test_marca_de_ressalva_aparece_so_no_variante():
    b = C.montar_briefing(_doc("burning-2018"))
    marca = "RESSALVA NESTE TEMA: «mas insuficientes para salvar o filme»"
    assert marca in C.serializar_briefing(b, variante=VAR)
    assert marca not in C.serializar_briefing(b)


# ===========================================================================
# gerar — o braço chega inteiro ao modelo, e fica registrado
# ===========================================================================

def _capturar(chamadas):
    def gerar(system, user):
        chamadas.append((system, user))
        return (json.dumps({"vale_a_pena": [], "talvez_evite": []}),
                {"prompt_tokens": 1, "completion_tokens": 1,
                 "cache_hit_tokens": 0, "cache_miss_tokens": 0}, 0.01)
    return gerar


def test_gerar_com_variante_explicito_usa_briefing_e_prompt_variantes():
    d = _doc("burning-2018")
    chamadas = []
    out = C.gerar(d, n=2, gerar=_capturar(chamadas), variante=VAR)
    esperado = C.serializar_briefing(C.montar_briefing(d), variante=VAR)
    assert chamadas and all(s == C.PROMPT_CONDICOES_VARIANTE and u == esperado
                            for s, u in chamadas)
    assert out["variante"] == VAR


# ===========================================================================
# [2026-09-15] O DEFAULT MUDOU — ver ABERTO.md C14.18 e o docstring de
# `gerar()`. `variante=VARIANTE_EXPERIMENTO` é produção; `variante=None`
# passa a ser a reprodução EXPLÍCITA do braço `controle` do experimento, não
# mais o caminho que um chamador cai sem pedir nada.
# ===========================================================================

def test_gerar_sem_variante_usa_o_default_novo_e_registra_variante():
    """Omitir `variante` é o caminho de PRODUÇÃO desde 2026-09-15: usa o
    briefing e o prompt do experimento, e registra `variante` no bloco —
    igual a passar `variante=VAR` explicitamente."""
    d = _doc("burning-2018")
    chamadas = []
    out = C.gerar(d, n=2, gerar=_capturar(chamadas))
    esperado = C.serializar_briefing(C.montar_briefing(d), variante=VAR)
    assert chamadas and all(s == C.PROMPT_CONDICOES_VARIANTE and u == esperado
                            for s, u in chamadas)
    assert out["variante"] == VAR == C.VARIANTE_EXPERIMENTO


def test_gerar_com_variante_none_explicito_reproduz_o_controle_do_experimento():
    """`variante=None` continua existindo, e continua produzindo o briefing e
    o prompt de ANTES do experimento byte a byte — para reproduzir o braço
    `controle` ou para reverter. Não registra `variante`, como sempre."""
    d = _doc("burning-2018")
    chamadas = []
    out = C.gerar(d, n=2, gerar=_capturar(chamadas), variante=None)
    esperado = C.serializar_briefing(C.montar_briefing(d))
    assert chamadas and all(s == C.PROMPT_CONDICOES and u == esperado
                            for s, u in chamadas)
    assert "variante" not in out
