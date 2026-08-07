"""[v1.9.0] Alocação proporcional ao histograma + redistribuição (SPEC §3[C1]).

Substitui a cota igual por nível, que super-representava os extremos: no
`cure`, 0,5★ tem 456 notas e 2,0★ tem 4.251, e ambos entravam com 10 reviews.
"""
import pytest

from conftest import histograma_de_contagens

from espectro24.alocacao import (
    alocar,
    alocar_bucket,
    redistribuir_deficit,
)
from espectro24.buckets import FRONTEIRAS_C, FRONTEIRAS_V18, mapa_de_niveis

NEG_C = mapa_de_niveis(FRONTEIRAS_C)["negativas"]      # [0.5, 1.0, 1.5, 2.0]
MED_C = mapa_de_niveis(FRONTEIRAS_C)["medianas"]        # [2.5, 3.0]


# --- a soma bate com N_bucket, sempre ---

@pytest.mark.parametrize("contagens", [
    {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251},     # cure, negativas
    {0.5: 893, 1.0: 1645, 1.5: 1143, 2.0: 5503},    # cidade-de-deus
    {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 99997},           # extremo: 1 nível domina
    {0.5: 25, 1.0: 25, 1.5: 25, 2.0: 25},           # uniforme
    {0.5: 0, 1.0: 0, 1.5: 0, 2.0: 10},              # 3 níveis zerados
])
@pytest.mark.parametrize("n_bucket", [40, 30, 12, 9])
def test_soma_bate_exatamente_com_n_bucket(contagens, n_bucket):
    a = alocar_bucket(n_bucket, contagens, NEG_C, piso_nivel=2)
    assert sum(a.values()) == n_bucket
    assert set(a) == set(NEG_C)
    assert all(v >= 0 for v in a.values())


def test_soma_bate_com_dois_niveis():
    a = alocar_bucket(40, {2.5: 6214, 3.0: 23371}, MED_C, piso_nivel=2)
    assert sum(a.values()) == 40


# --- proporcionalidade: o nível populoso leva mais ---

def test_proporcional_ao_histograma_do_cure():
    # negativas do `cure`: 456 / 1037 / 989 / 4251 = 6733
    a = alocar_bucket(40, {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251}, NEG_C,
                      piso_nivel=2)
    assert a[2.0] > a[1.0] > a[0.5]          # ordem segue o histograma
    assert a[2.0] == 25                       # 40 * 4251/6733 = 25.25
    assert sum(a.values()) == 40


def test_cota_igual_teria_dado_10_para_cada_a_diferenca_e_o_ponto():
    """O defeito que a alocação corrige: 0,5★ entrando com o mesmo peso de 2,0★."""
    a = alocar_bucket(40, {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251}, NEG_C,
                      piso_nivel=2)
    assert a[0.5] < 10 < a[2.0]


def test_nivel_dominante_nao_zera_os_outros_por_causa_do_piso():
    a = alocar_bucket(40, {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 99997}, NEG_C,
                      piso_nivel=2)
    assert a[0.5] == a[1.0] == a[1.5] == 2     # piso respeitado
    assert a[2.0] == 34
    assert sum(a.values()) == 40


# --- piso: só para níveis COM material ---

def test_piso_respeitado_em_todo_nivel_com_material():
    a = alocar_bucket(40, {0.5: 3, 1.0: 5, 1.5: 2, 2.0: 9000}, NEG_C, piso_nivel=2)
    for n in (0.5, 1.0, 1.5):
        assert a[n] >= 2


def test_nivel_sem_material_no_histograma_recebe_zero():
    a = alocar_bucket(40, {0.5: 0, 1.0: 100, 1.5: 0, 2.0: 100}, NEG_C, piso_nivel=2)
    assert a[0.5] == 0 and a[1.5] == 0
    assert a[1.0] == a[2.0] == 20


def test_nivel_ausente_do_dict_nao_quebra():
    """Histograma incompleto (chave faltando) é tratado como zero, não erro."""
    a = alocar_bucket(40, {1.0: 100, 2.0: 100}, NEG_C, piso_nivel=2)
    assert sum(a.values()) == 40
    assert a[0.5] == 0 and a[1.5] == 0


def test_piso_zero_e_aceito():
    a = alocar_bucket(40, {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 9997}, NEG_C, piso_nivel=0)
    assert sum(a.values()) == 40
    assert a[2.0] == 40    # sem piso, o dominante leva tudo


# --- casos degenerados ---

def test_sem_material_nenhum_cai_para_uniforme():
    """Bucket inteiro zerado no histograma: sem forma, o palpite honesto é
    dividir igual — o mesmo caminho do fallback sem histograma."""
    a = alocar_bucket(40, {n: 0 for n in NEG_C}, NEG_C, piso_nivel=2)
    assert sum(a.values()) == 40
    assert a == {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}


def test_uniforme_com_resto_distribui_o_resto():
    a = alocar_bucket(10, {}, [0.5, 1.0, 1.5, 2.0], piso_nivel=2)
    assert sum(a.values()) == 10
    assert sorted(a.values()) == [2, 2, 3, 3]


def test_piso_impossivel_e_RELAXADO_nao_violado_em_silencio():
    """4 níveis com material × piso 2 = 8 > N_bucket 5.

    Honrar o piso estouraria a cota. A alocação distribui os 5 o mais
    uniformemente possível e o piso é relaxado — mas a SOMA continua exata.
    """
    a = alocar_bucket(5, {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}, NEG_C, piso_nivel=2)
    assert sum(a.values()) == 5
    assert min(a.values()) < 2      # piso relaxado, explicitamente


def test_n_bucket_zero():
    a = alocar_bucket(0, {0.5: 10, 2.0: 10}, NEG_C, piso_nivel=2)
    assert sum(a.values()) == 0


# --- determinismo ---

def test_alocacao_e_deterministica():
    args = (40, {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251}, NEG_C)
    assert alocar_bucket(*args, piso_nivel=2) == alocar_bucket(*args, piso_nivel=2)


# --- alocar() sobre o filme inteiro, pelas fronteiras recebidas ---

def test_alocar_usa_as_fronteiras_recebidas():
    hist = {n: 100 for n in
            (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)}
    sob_c = alocar({"negativas": 40, "medianas": 40, "positivas": 40}, hist,
                   fronteiras=FRONTEIRAS_C)
    sob_v18 = alocar({"negativas": 40, "medianas": 40, "positivas": 40}, hist,
                     fronteiras=FRONTEIRAS_V18)
    assert set(sob_c["negativas"]) == {0.5, 1.0, 1.5, 2.0}
    assert set(sob_v18["negativas"]) == {0.5, 1.0, 1.5, 2.0, 2.5}   # prova de parâmetro
    assert sum(sob_c["positivas"].values()) == 40


def test_alocar_sem_histograma_cai_para_uniforme():
    a = alocar({"negativas": 40, "medianas": 40, "positivas": 40}, None,
               fronteiras=FRONTEIRAS_C)
    assert a["negativas"] == {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    assert a["medianas"] == {2.5: 20, 3.0: 20}
    assert sum(a["positivas"].values()) == 40


def test_alocar_cobre_os_10_niveis_sem_sobreposicao():
    a = alocar({"negativas": 40, "medianas": 40, "positivas": 40},
               histograma_de_contagens(negativas=100, medianas=100, positivas=100))
    todos = [n for niveis in a.values() for n in niveis]
    assert sorted(todos) == [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


# --- redistribuição de déficit ---

def test_deficit_vai_para_o_nivel_com_mais_material_do_MESMO_bucket():
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {0.5: 2, 1.0: 10, 1.5: 10, 2.0: 40}   # 0.5 só tem 2
    final = redistribuir_deficit(alocacao, disponivel)
    assert sum(final.values()) == 40         # o bucket fecha com N certo
    assert final[0.5] == 2                   # não inventa material
    assert final[2.0] > 10                   # a sobra foi para quem tem mais


def test_redistribuicao_nunca_estoura_n_bucket():
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {0.5: 0, 1.0: 999, 1.5: 999, 2.0: 999}
    final = redistribuir_deficit(alocacao, disponivel)
    assert sum(final.values()) == sum(alocacao.values()) == 40


def test_redistribuicao_nao_sai_do_bucket():
    """Estruturalmente: a função só vê os níveis do bucket que recebeu."""
    alocacao = {2.5: 20, 3.0: 20}
    disponivel = {2.5: 5, 3.0: 999}
    final = redistribuir_deficit(alocacao, disponivel)
    assert set(final) == {2.5, 3.0}
    assert sum(final.values()) == 40


def test_deficit_irrecuperavel_fecha_o_bucket_curto_sem_inventar():
    """Material insuficiente no bucket inteiro: fecha abaixo do alvo.

    É resultado honesto — o piso escalonado (§3[C3]) é quem trata a
    consequência, não a alocação inventando reviews.
    """
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 1}
    final = redistribuir_deficit(alocacao, disponivel)
    assert final == {0.5: 1, 1.0: 1, 1.5: 1, 2.0: 1}
    assert sum(final.values()) == 4


def test_sem_deficit_a_alocacao_passa_intacta():
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {n: 99 for n in alocacao}
    assert redistribuir_deficit(alocacao, disponivel) == alocacao


def test_redistribuicao_respeita_o_disponivel_de_cada_nivel():
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {0.5: 0, 1.0: 12, 1.5: 12, 2.0: 12}
    final = redistribuir_deficit(alocacao, disponivel)
    for n, v in final.items():
        assert v <= disponivel[n]
    assert sum(final.values()) == 36     # 12+12+12, teto do material


def test_redistribuicao_e_deterministica():
    alocacao = {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}
    disponivel = {0.5: 1, 1.0: 50, 1.5: 50, 2.0: 50}
    assert (redistribuir_deficit(alocacao, disponivel)
            == redistribuir_deficit(alocacao, disponivel))


# --- [v1.9.2] divisão raso/profundo (posicionamento estratificado, §3[B]) ---

from espectro24.alocacao import dividir_raso_profundo  # noqa: E402


@pytest.mark.parametrize("orcamento,esperado", [
    (16, (12, 4)),   # round(16*0.25)=4
    (10, (8, 2)),    # round(10*0.25)=round(2.5)=2 (banker's rounding)
    (6, (4, 2)),     # round(6*0.25)=round(1.5)=2 (banker's rounding, 2 é par)
    (3, (2, 1)),     # round(3*0.25)=round(0.75)=1
    (1, (1, 0)),     # round(1*0.25)=round(0.25)=0
    (2, (2, 0)),     # round(2*0.25)=round(0.5)=0 (banker's rounding, 0 é par)
    (0, (0, 0)),
])
def test_dividir_raso_profundo_valores_conhecidos(orcamento, esperado):
    assert dividir_raso_profundo(orcamento) == esperado


def test_dividir_raso_profundo_soma_sempre_bate():
    for orc in range(0, 40):
        raso, profundo = dividir_raso_profundo(orc)
        assert raso + profundo == orc


def test_dividir_raso_profundo_raso_nunca_negativo_e_ge_1_quando_orc_ge_1():
    for orc in range(1, 40):
        raso, profundo = dividir_raso_profundo(orc)
        assert raso >= 1
        assert profundo >= 0


def test_dividir_raso_profundo_reserva_e_parametro():
    assert dividir_raso_profundo(16, reserva=0.5) == (8, 8)
    assert dividir_raso_profundo(16, reserva=0.0) == (16, 0)
