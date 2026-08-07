"""[v1.9.0] Fronteiras de bucket como CONFIGURAÇÃO (SPEC §2.2).

O ponto destes testes NÃO é conferir que a opção C está certa — é provar que
as fronteiras são **parâmetro** e não constante enterrada no código. Por isso
quase todo teste aqui roda a mesma função duas vezes: sob as fronteiras em
vigor e sob fronteiras ALTERNATIVAS, conferindo que o resultado acompanha.
Se alguém hardcodar `0.5–2.0` em algum ponto do caminho, o par de asserções
sob fronteiras alternativas quebra.
"""
import pytest

from espectro24.buckets import (
    FRONTEIRAS,
    FRONTEIRAS_C,
    FRONTEIRAS_V18,
    NIVEIS,
    bucket_de_nivel,
    intervalo_de,
    mapa_de_niveis,
    niveis_de,
    shares_por_bucket,
    validar_fronteiras,
)

# Fronteiras inventadas só para os testes — nenhuma relação com a spec. Servem
# para provar que o código não sabe nada sobre a opção C em particular.
FRONTEIRAS_INVENTADAS = {
    "negativas": (0.5, 1.0),
    "medianas": (1.5, 4.0),
    "positivas": (4.5, 5.0),
}


# --- a configuração em vigor é a opção C (§2.2) ---

def test_fronteiras_em_vigor_sao_a_opcao_c():
    assert FRONTEIRAS == FRONTEIRAS_C
    assert FRONTEIRAS_C == {
        "negativas": (0.5, 2.0),
        "medianas": (2.5, 3.0),
        "positivas": (3.5, 5.0),
    }


def test_opcao_c_tem_4_2_4_niveis():
    mapa = mapa_de_niveis(FRONTEIRAS_C)
    assert mapa["negativas"] == [0.5, 1.0, 1.5, 2.0]
    assert mapa["medianas"] == [2.5, 3.0]
    assert mapa["positivas"] == [3.5, 4.0, 4.5, 5.0]


def test_os_10_niveis_canonicos():
    assert NIVEIS == (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)


# --- mapeamento nível→bucket: função pura, sob C e sob alternativas ---

@pytest.mark.parametrize("nivel,esperado", [
    (0.5, "negativas"), (1.0, "negativas"), (1.5, "negativas"), (2.0, "negativas"),
    (2.5, "medianas"), (3.0, "medianas"),
    (3.5, "positivas"), (4.0, "positivas"), (4.5, "positivas"), (5.0, "positivas"),
])
def test_bucket_de_nivel_sob_fronteiras_c(nivel, esperado):
    assert bucket_de_nivel(nivel, FRONTEIRAS_C) == esperado


@pytest.mark.parametrize("nivel,esperado", [
    (2.5, "negativas"),   # sob C seria medianas
    (3.0, "medianas"),
    (3.5, "medianas"),    # sob C seria positivas
    (4.0, "positivas"),
])
def test_bucket_de_nivel_sob_fronteiras_historicas(nivel, esperado):
    """Os dois níveis que a opção C move trocam de bucket — prova de parâmetro."""
    assert bucket_de_nivel(nivel, FRONTEIRAS_V18) == esperado


def test_bucket_de_nivel_sob_fronteiras_inventadas():
    assert bucket_de_nivel(1.0, FRONTEIRAS_INVENTADAS) == "negativas"
    assert bucket_de_nivel(4.0, FRONTEIRAS_INVENTADAS) == "medianas"
    assert bucket_de_nivel(4.5, FRONTEIRAS_INVENTADAS) == "positivas"


def test_bucket_de_nivel_usa_as_fronteiras_em_vigor_por_default():
    assert bucket_de_nivel(3.5) == bucket_de_nivel(3.5, FRONTEIRAS)


def test_bucket_de_nivel_fora_da_escala_e_none():
    assert bucket_de_nivel(0.0) is None
    assert bucket_de_nivel(5.5) is None
    assert bucket_de_nivel(2.2) is None   # não é um nível canônico


def test_niveis_de_e_o_inverso_de_bucket_de_nivel():
    for fr in (FRONTEIRAS_C, FRONTEIRAS_V18, FRONTEIRAS_INVENTADAS):
        for nome in fr:
            for n in niveis_de(nome, fr):
                assert bucket_de_nivel(n, fr) == nome


def test_intervalo_de_acompanha_as_fronteiras():
    assert intervalo_de("negativas", FRONTEIRAS_C) == (0.5, 2.0)
    assert intervalo_de("negativas", FRONTEIRAS_V18) == (0.5, 2.5)


# --- validação: fronteiras precisam PARTICIONAR os 10 níveis ---

def test_validar_aceita_as_tres_configuracoes_validas():
    for fr in (FRONTEIRAS_C, FRONTEIRAS_V18, FRONTEIRAS_INVENTADAS):
        validar_fronteiras(fr)   # não levanta


def test_validar_rejeita_buraco():
    # 2.5 não pertence a bucket nenhum
    with pytest.raises(ValueError, match="não cobertos"):
        validar_fronteiras({"a": (0.5, 2.0), "b": (3.0, 3.0), "c": (3.5, 5.0)})


def test_validar_rejeita_sobreposicao():
    with pytest.raises(ValueError, match="mais de um bucket"):
        validar_fronteiras({"a": (0.5, 2.5), "b": (2.5, 3.0), "c": (3.5, 5.0)})


def test_validar_rejeita_intervalo_invertido():
    with pytest.raises(ValueError, match="invertido"):
        validar_fronteiras({"a": (2.0, 0.5), "b": (2.5, 3.0), "c": (3.5, 5.0)})


def test_validar_rejeita_bucket_vazio():
    # (2.6, 2.9) não contém nenhum nível canônico
    with pytest.raises(ValueError, match="vazio"):
        validar_fronteiras({"a": (0.5, 2.5), "b": (2.6, 2.9), "c": (3.0, 5.0)})


def test_a_configuracao_em_vigor_e_valida():
    validar_fronteiras(FRONTEIRAS)


# --- recálculo de shares do histograma sob fronteiras diferentes ---

# Histograma REAL do `cure` (resultado/cure.json, distribuicao.por_nivel).
HISTOGRAMA_CURE = {
    0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251, 2.5: 6214,
    3.0: 23371, 3.5: 41371, 4.0: 110990, 4.5: 87357, 5.0: 99242,
}
HISTOGRAMA_CIDADE = {
    0.5: 893, 1.0: 1645, 1.5: 1143, 2.0: 5503, 2.5: 6324,
    3.0: 35847, 3.5: 58393, 4.0: 245630, 4.5: 241463, 5.0: 619540,
}
HISTOGRAMA_INVITE = {
    0.5: 503, 1.0: 909, 1.5: 926, 2.0: 3169, 2.5: 4999,
    3.0: 18554, 3.5: 41311, 4.0: 125276, 4.5: 86297, 5.0: 56504,
}


@pytest.mark.parametrize("hist,antigas,novas", [
    (HISTOGRAMA_CURE, (3, 17, 79), (2, 8, 90)),
    (HISTOGRAMA_CIDADE, (1, 8, 91), (1, 3, 96)),
    (HISTOGRAMA_INVITE, (3, 18, 79), (2, 7, 91)),
])
def test_shares_mudam_sob_a_opcao_c(hist, antigas, novas):
    """Os shares PUBLICADOS mudam — é a consequência declarada em §2.2.

    Os valores "antigas" são exatamente os que estão nos resultado/*.json
    gerados sob a v1.8.2, então este teste também é uma regressão do
    recálculo: se `shares_por_bucket` mudasse de fórmula, a coluna antiga
    deixaria de bater com o dado publicado.
    """
    velho = shares_por_bucket(hist, FRONTEIRAS_V18)
    novo = shares_por_bucket(hist, FRONTEIRAS_C)
    assert (velho["negativas"], velho["medianas"], velho["positivas"]) == antigas
    assert (novo["negativas"], novo["medianas"], novo["positivas"]) == novas


def test_positivas_crescem_e_negativas_encolhem_nos_tres_filmes():
    """A direção do movimento é a prevista em §2.2, não só o valor."""
    for hist in (HISTOGRAMA_CURE, HISTOGRAMA_CIDADE, HISTOGRAMA_INVITE):
        velho = shares_por_bucket(hist, FRONTEIRAS_V18)
        novo = shares_por_bucket(hist, FRONTEIRAS_C)
        assert novo["positivas"] > velho["positivas"]      # entra o 3.5
        assert novo["negativas"] <= velho["negativas"]     # sai o 2.5
        assert novo["medianas"] < velho["medianas"]


def test_shares_arredondam_cada_bucket_independentemente():
    """Invariante da v1.4.0 preservada: a soma pode dar 99 ou 101."""
    soma = sum(shares_por_bucket(HISTOGRAMA_CURE, FRONTEIRAS_V18).values())
    assert soma == 99   # 3+17+79 — o caso já documentado na SPEC


def test_shares_com_nivel_ausente_do_histograma():
    hist = {0.5: 10, 5.0: 90}   # 8 níveis ausentes
    s = shares_por_bucket(hist, FRONTEIRAS_C)
    assert s == {"negativas": 10, "medianas": 0, "positivas": 90}


def test_shares_sem_notas_e_none():
    assert shares_por_bucket({}, FRONTEIRAS_C) is None
    assert shares_por_bucket({n: 0 for n in NIVEIS}, FRONTEIRAS_C) is None


# --- nada no resto do código pode reintroduzir a fronteira hardcoded ---

def test_config_deriva_buckets_das_fronteiras():
    from espectro24 import config
    assert config.BUCKETS == mapa_de_niveis(FRONTEIRAS)
    assert config.NIVEIS_ORDENADOS == list(NIVEIS)


def test_config_bucket_de_nota_delega_para_a_funcao_pura():
    from espectro24 import config
    for n in NIVEIS:
        assert config.bucket_de_nota(n) == bucket_de_nivel(n)


def test_cota_por_bucket_e_igual_nos_tres():
    from espectro24 import config
    assert set(config.BUCKET_ALVO.values()) == {40}
    assert set(config.BUCKET_ALVO) == set(FRONTEIRAS)


def test_distribuicao_agrega_pelas_fronteiras_em_vigor():
    from espectro24.models import Distribuicao
    d = Distribuicao.de_histograma(HISTOGRAMA_CURE)
    assert d.por_bucket == shares_por_bucket(HISTOGRAMA_CURE, FRONTEIRAS)
    assert d.n_notas_total == sum(HISTOGRAMA_CURE.values())


def test_intervalo_do_prompt_de_sintese_acompanha_as_fronteiras():
    """O preâmbulo de papel (§D) escreve o intervalo do bucket no prompt.

    Se ele estivesse hardcoded, continuaria dizendo "0.5–2.5 estrelas" para
    `negativas` depois da opção C — uma mentira entregue ao LLM.
    """
    from espectro24.synthesize import _intervalo_bucket
    assert _intervalo_bucket("negativas") == "0.5–2 estrelas"
    assert _intervalo_bucket("medianas") == "2.5–3 estrelas"
    assert _intervalo_bucket("positivas") == "3.5–5 estrelas"
