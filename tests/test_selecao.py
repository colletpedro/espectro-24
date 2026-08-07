"""[v1.9.0] Seleção downstream 40/40/40 + piso escalonado (SPEC §3[C2], §3[C3]).

A seleção lê o bruto persistido e aplica, como PARÂMETROS, tudo o que até a
v1.8.2 estava congelado dentro da coleta: fronteiras, cota, min_chars,
exclusão de spoiler, cascata e piso. Zero rede.
"""
import pytest

from espectro24.bruto import ReviewBruta
from espectro24.buckets import FRONTEIRAS_C, FRONTEIRAS_V18
from espectro24.collector import estado_do_piso
from espectro24.selecao import _cascade_pool, selecionar


def _r(rid, nivel, chars=200, spoiler=False, completo=True, pagina=1):
    return ReviewBruta(id=str(rid), nivel=nivel, texto="x" * chars, n_chars=chars,
                       spoiler_flag=spoiler, pagina_origem=pagina, url="u",
                       autor_hash="h", truncada=not completo,
                       texto_completo=completo, data="2026-01-01")


def _muitas(nivel, n, **kw):
    return [_r(f"{nivel}-{i}", nivel, **kw) for i in range(n)]


HIST = {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251, 2.5: 6214,
        3.0: 23371, 3.5: 41371, 4.0: 110990, 4.5: 87357, 5.0: 99242}


# --- cota respeitada ---

def test_cota_de_40_por_bucket():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    sel = selecionar(revs, HIST)
    assert sel["negativas"].n_final == 40


def test_cota_e_parametro():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    assert selecionar(revs, HIST, cota_por_bucket=12)["negativas"].n_final == 12


def test_os_tres_buckets_recebem_a_MESMA_cota():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
            for r in _muitas(n, 50)]
    sel = selecionar(revs, HIST)
    assert {b.n_final for b in sel.values()} == {40}


def test_material_insuficiente_fecha_curto_sem_inventar():
    sel = selecionar(_muitas(2.0, 5), HIST)
    assert sel["negativas"].n_final == 5


# --- fronteiras como parâmetro ---

def test_selecao_usa_as_fronteiras_recebidas():
    revs = _muitas(2.5, 50) + _muitas(3.5, 50)
    sob_c = selecionar(revs, HIST, fronteiras=FRONTEIRAS_C)
    sob_v18 = selecionar(revs, HIST, fronteiras=FRONTEIRAS_V18)
    # 2.5 é "medianas" sob C e "negativas" sob as históricas
    assert 2.5 in sob_c["medianas"].composicao_atingida
    assert 2.5 in sob_v18["negativas"].composicao_atingida
    # 3.5 é "positivas" sob C e "medianas" sob as históricas
    assert 3.5 in sob_c["positivas"].composicao_atingida
    assert 3.5 in sob_v18["medianas"].composicao_atingida


def test_o_MESMO_bruto_serve_as_duas_fronteiras_sem_recoletar():
    """A propriedade central da v1.9.0: trocar fronteira custa 0 requisições."""
    revs = [r for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
            for r in _muitas(n, 40)]
    a = selecionar(revs, HIST, fronteiras=FRONTEIRAS_C)
    b = selecionar(revs, HIST, fronteiras=FRONTEIRAS_V18)
    assert a["negativas"].composicao_atingida != b["negativas"].composicao_atingida


# --- composição por nível: alvo vs atingida ---

def test_composicao_segue_a_alocacao_proporcional():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    sel = selecionar(revs, HIST)["negativas"]
    assert sel.composicao_atingida == sel.composicao_alvo
    assert sel.composicao_atingida[2.0] > sel.composicao_atingida[0.5]
    assert sum(sel.composicao_atingida.values()) == 40


def test_alvo_e_atingida_sao_publicados_lado_a_lado():
    """Mitigação obrigatória da ressalva 2 de §3[C1]: sem os dois, 40
    alcançados como planejado e 40 por redistribuição pareceriam iguais."""
    revs = _muitas(0.5, 1) + _muitas(1.0, 50) + _muitas(1.5, 50) + _muitas(2.0, 50)
    sel = selecionar(revs, HIST)["negativas"]
    assert sel.composicao_alvo[0.5] > 1
    assert sel.composicao_atingida[0.5] == 1
    assert sel.composicao_alvo != sel.composicao_atingida
    assert sum(sel.composicao_atingida.values()) == 40   # fechou por redistribuição
    assert sel.deficit_redistribuido > 0


def test_sem_deficit_o_contador_de_redistribuicao_fica_zero():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    assert selecionar(revs, HIST)["negativas"].deficit_redistribuido == 0


def test_redistribuicao_nao_atravessa_bucket():
    """negativas com material de sobra não empresta vaga para medianas."""
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 90)]
    revs += _muitas(2.5, 3) + _muitas(3.0, 3)
    sel = selecionar(revs, HIST)
    assert sel["negativas"].n_final == 40
    assert sel["medianas"].n_final == 6          # ficou curto, e continua curto


# --- filtros como parâmetro ---

def test_min_chars_e_parametro():
    revs = _muitas(2.0, 20, chars=100)
    assert selecionar(revs, HIST, min_chars=50)["negativas"].n_final == 20
    # com 150 o nível daria zero → a cascata desce (ver testes de cascata)


def test_excluir_spoiler_e_parametro():
    revs = _muitas(2.0, 20) + _muitas(1.0, 20, spoiler=True)
    assert selecionar(revs, HIST, excluir_spoiler=True)["negativas"].n_final == 20
    assert selecionar(revs, HIST, excluir_spoiler=False)["negativas"].n_final == 40


def test_texto_incompleto_e_INELEGIVEL_e_contado():
    """'Nunca pela metade' (v1.1.0) sobrevive ao superset: truncada não
    resolvida fica no bruto, mas não entra na análise."""
    revs = _muitas(2.0, 10) + _muitas(1.0, 10, completo=False)
    sel = selecionar(revs, HIST)["negativas"]
    assert sel.n_final == 10
    assert sel.niveis[1.0].n_indisponivel_truncamento == 10


# --- cascata: na ordem certa, e SÓ em zero ---

def test_cascata_na_ordem_150_50_0():
    assert _cascade_pool(_muitas(2.0, 5, chars=200), 150, [150, 50, 0], True)[1] == 150
    assert _cascade_pool(_muitas(2.0, 5, chars=80), 150, [150, 50, 0], True)[1] == 50
    assert _cascade_pool(_muitas(2.0, 5, chars=20), 150, [150, 50, 0], True)[1] == 0


def test_cascata_so_dispara_em_ZERO_nunca_para_completar_cota():
    """1 review longa + 30 curtas: o nível fica com 1, não relaxa para 31."""
    revs = _muitas(2.0, 1, chars=200) + _muitas(1.0, 30, chars=60)
    sel = selecionar(revs, HIST)["negativas"]
    assert sel.niveis[2.0].filtro_aplicado == 150
    assert sel.niveis[2.0].n_validas == 1
    # o nível 1.0 daria ZERO em 150 → aí sim relaxa
    assert sel.niveis[1.0].filtro_aplicado == 50


def test_cascata_e_por_NIVEL_nao_por_bucket():
    revs = _muitas(2.0, 20, chars=200) + _muitas(0.5, 20, chars=60)
    sel = selecionar(revs, HIST)["negativas"]
    assert sel.niveis[2.0].filtro_aplicado == 150
    assert sel.niveis[0.5].filtro_aplicado == 50


def test_registra_quantas_entraram_por_cada_degrau():
    revs = _muitas(2.0, 30, chars=200) + _muitas(0.5, 30, chars=60)
    sel = selecionar(revs, HIST)["negativas"]
    assert set(sel.cascata_por_degrau) <= {150, 50, 0}
    assert sum(sel.cascata_por_degrau.values()) == sel.n_final
    assert sel.cascata_por_degrau[150] > 0 and sel.cascata_por_degrau[50] > 0


def test_nivel_sem_nada_termina_vazio():
    sel = selecionar(_muitas(2.0, 3), HIST)["negativas"]
    assert sel.niveis[0.5].n_validas == 0


def test_cascata_e_parametro():
    revs = _muitas(2.0, 5, chars=80)
    sel = selecionar(revs, HIST, cascata=[150, 0])["negativas"]
    assert sel.niveis[2.0].filtro_aplicado == 0   # sem o degrau de 50


# --- ordem de escolha: determinística e reproduzível ---

def test_escolhe_na_ordem_de_amostragem_pagina_depois_jsonl():
    revs = ([_r(f"p2-{i}", 2.0, pagina=2) for i in range(5)]
            + [_r(f"p1-{i}", 2.0, pagina=1) for i in range(5)])
    sel = selecionar(revs, {2.0: 100}, cota_por_bucket=3, piso_nivel=0)["negativas"]
    assert [r.id for r in sel.niveis[2.0].validas] == ["p1-0", "p1-1", "p1-2"]


def test_selecao_e_deterministica():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    a = selecionar(revs, HIST)["negativas"]
    b = selecionar(revs, HIST)["negativas"]
    assert [r.id for r in a.niveis[2.0].validas] == [r.id for r in b.niveis[2.0].validas]


def test_zero_rede_a_selecao_so_ve_a_lista():
    """Garantia estrutural: `selecionar` não recebe fetcher nenhum."""
    import inspect
    assert "fetcher" not in inspect.signature(selecionar).parameters


# --- piso escalonado: os 4 estados nas fronteiras EXATAS ---

@pytest.mark.parametrize("n,esperado", [
    (0, "sem_analise"), (1, "sem_analise"), (2, "sem_analise"),
    (3, "sem_numero"), (4, "sem_numero"), (7, "sem_numero"),
    (8, "sem_quantificador"), (9, "sem_quantificador"), (14, "sem_quantificador"),
    (15, "completa"), (16, "completa"), (40, "completa"), (999, "completa"),
])
def test_piso_escalonado_nas_fronteiras_exatas(n, esperado):
    assert estado_do_piso(n) == esperado


@pytest.mark.parametrize("abaixo,acima,de,para", [
    (2, 3, "sem_analise", "sem_numero"),
    (7, 8, "sem_numero", "sem_quantificador"),
    (14, 15, "sem_quantificador", "completa"),
])
def test_as_tres_transicoes_2_3_7_8_14_15(abaixo, acima, de, para):
    assert estado_do_piso(abaixo) == de
    assert estado_do_piso(acima) == para


def test_estado_piso_sai_na_selecao():
    revs = _muitas(2.0, 20)
    sel = selecionar(revs, HIST)
    assert sel["negativas"].estado_piso == "completa"
    assert sel["medianas"].estado_piso == "sem_analise"


@pytest.mark.parametrize("n,esperado", [
    (20, "completa"), (10, "sem_quantificador"), (5, "sem_numero"), (2, "sem_analise"),
])
def test_estado_do_bucket_acompanha_o_n_final(n, esperado):
    sel = selecionar(_muitas(2.0, n), HIST)
    assert sel["negativas"].estado_piso == esperado


# --- sem histograma: cai para uniforme e não quebra ---

def test_sem_histograma_a_selecao_ainda_funciona():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    sel = selecionar(revs, None)["negativas"]
    assert sel.n_final == 40
    assert sel.composicao_alvo == {0.5: 10, 1.0: 10, 1.5: 10, 2.0: 10}


def test_bruto_vazio_nao_quebra():
    sel = selecionar([], HIST)
    assert all(b.n_final == 0 for b in sel.values())
    assert all(b.estado_piso == "sem_analise" for b in sel.values())


def test_nivel_fora_da_escala_e_ignorado():
    revs = _muitas(2.0, 5) + [_r("x", 7.0)]
    sel = selecionar(revs, HIST)
    assert sum(b.n_final for b in sel.values()) == 5


# --- ordem dos filtros (§C), herdada de tests/test_cascade.py (v1.8.2) ---
# O arquivo antigo testava a cascata DURANTE a coleta; na v1.9.0 a cascata é
# de análise, então a cobertura vive aqui. As três regras são as mesmas.

def test_ordem_dos_filtros_nota_spoiler_comprimento():
    # (1) tem nota: garantida pela URL de coleta, que já é por nível — uma
    #     review sem nota não existe no bruto (ver test_coletor).
    # (2) sem spoiler:
    assert _cascade_pool([_r("a", 2.0, spoiler=True)], 150, [150, 50, 0], True)[0] == []
    # (3) comprimento:
    pool, thr = _cascade_pool([_r("b", 2.0, chars=200), _r("c", 2.0, chars=10)],
                              150, [150, 50, 0], True)
    assert [r.id for r in pool] == ["b"] and thr == 150


def test_texto_incompleto_nunca_entra_no_pool():
    assert _cascade_pool([_r("a", 2.0, completo=False)], 150, [150, 50, 0], True)[0] == []


def test_nivel_so_com_spoiler_termina_vazio_mesmo_apos_a_cascata():
    pool, thr = _cascade_pool([_r("a", 2.0, spoiler=True)], 150, [150, 50, 0], True)
    assert pool == [] and thr == 0
