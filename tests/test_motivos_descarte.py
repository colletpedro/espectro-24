"""[v1.9.1, Entrega 2] Motivos de descarte, discriminados (SPEC §3[C2]).

Telemetria pura — nenhuma mudança de comportamento da seleção. Cada review
do bruto de um nível é classificada em EXATAMENTE uma categoria
(`selecionada` ou um motivo), numa ordem de precedência fixa, de modo que a
soma dos motivos sempre feche com `n_brutas − n_validas`.
"""
import pytest

from espectro24.bruto import ReviewBruta
from espectro24.selecao import _discriminar_descartes, selecionar

HIST = {0.5: 456, 1.0: 1037, 1.5: 989, 2.0: 4251, 2.5: 6214,
        3.0: 23371, 3.5: 41371, 4.0: 110990, 4.5: 87357, 5.0: 99242}


def _r(rid, nivel=2.0, chars=200, spoiler=False, completo=True, pagina=1):
    return ReviewBruta(id=str(rid), nivel=nivel, texto="x" * chars, n_chars=chars,
                       spoiler_flag=spoiler, pagina_origem=pagina, url="u",
                       autor_hash="h", truncada=not completo,
                       texto_completo=completo, data="2026-01-01")


# --- invariante central: a soma SEMPRE fecha ---

@pytest.mark.parametrize("brutas,selecionadas_ids,filtro,excluir_spoiler", [
    ([], set(), 150, True),
    ([_r(1)], {"1"}, 150, True),
    ([_r(1), _r(2, chars=50)], {"1"}, 150, True),
    ([_r(1, spoiler=True), _r(2)], {"2"}, 150, True),
    ([_r(1, spoiler=True), _r(2)], {"1", "2"}, 150, False),   # spoiler elegível
    ([_r(1, completo=False), _r(2)], {"2"}, 150, True),
    ([_r(i) for i in range(10)], {"0", "1", "2"}, 150, True),  # excedente
])
def test_soma_dos_motivos_fecha_com_descartadas(brutas, selecionadas_ids, filtro,
                                                 excluir_spoiler):
    motivos = _discriminar_descartes(brutas, selecionadas_ids, filtro, excluir_spoiler)
    n_descartadas = len(brutas) - len(selecionadas_ids)
    assert sum(motivos.values()) == n_descartadas


def test_todas_as_chaves_de_motivo_sempre_presentes():
    """Mesmo quando um motivo não ocorre, a chave existe com 0 — previsibilidade
    de schema para quem consome o JSON."""
    motivos = _discriminar_descartes([_r(1)], {"1"}, 150, True)
    assert set(motivos) == {"abaixo_min_chars", "spoiler", "truncada_sem_texto",
                            "duplicata", "excedente_cota", "outros"}


# --- cada motivo, isolado ---

def test_abaixo_min_chars():
    motivos = _discriminar_descartes([_r(1, chars=50)], set(), 150, True)
    assert motivos["abaixo_min_chars"] == 1
    assert sum(v for k, v in motivos.items() if k != "abaixo_min_chars") == 0


def test_spoiler_quando_excluido():
    motivos = _discriminar_descartes([_r(1, spoiler=True)], set(), 150, True)
    assert motivos["spoiler"] == 1


def test_spoiler_NAO_conta_quando_excluir_spoiler_e_falso():
    """excluir_spoiler=False: a review É elegível — se não foi selecionada,
    o motivo é excedente_cota, não spoiler (senão o parâmetro estaria
    mentindo sobre o que descartou)."""
    motivos = _discriminar_descartes([_r(1, spoiler=True)], set(), 150, False)
    assert motivos["spoiler"] == 0
    assert motivos["excedente_cota"] == 1


def test_truncada_sem_texto():
    motivos = _discriminar_descartes([_r(1, completo=False)], set(), 150, True)
    assert motivos["truncada_sem_texto"] == 1


def test_excedente_cota_passou_em_tudo_mas_nao_coube():
    motivos = _discriminar_descartes([_r(1), _r(2)], {"1"}, 150, True)
    assert motivos["excedente_cota"] == 1


def test_duplicata_e_defensivo_e_normalmente_zero():
    motivos = _discriminar_descartes([_r(1), _r(2), _r(3)], {"1", "2", "3"}, 150, True)
    assert motivos["duplicata"] == 0
    assert motivos["outros"] == 0


def test_duplicata_detectada_quando_id_repete():
    """Defensivo: o dedupe já acontece na persistência do bruto (§3[B']), mas
    a seleção não confia cegamente — um id repetido na entrada é contado,
    não ignorado silenciosamente."""
    dup = _r(1)
    motivos = _discriminar_descartes([_r(1), dup], {"1"}, 150, True)
    assert motivos["duplicata"] == 1


# --- ordem de precedência: cada review cai em exatamente 1 categoria ---

def test_truncada_tem_precedencia_sobre_spoiler_e_curta():
    """Uma review truncada, marcada spoiler E curta é UMA coisa: truncada."""
    r = _r(1, completo=False, spoiler=True, chars=10)
    motivos = _discriminar_descartes([r], set(), 150, True)
    assert motivos["truncada_sem_texto"] == 1
    assert motivos["spoiler"] == 0 and motivos["abaixo_min_chars"] == 0


def test_spoiler_tem_precedencia_sobre_curta():
    r = _r(1, spoiler=True, chars=10)
    motivos = _discriminar_descartes([r], set(), 150, True)
    assert motivos["spoiler"] == 1
    assert motivos["abaixo_min_chars"] == 0


# --- derivados: os campos antigos passam a vir do mesmo dict ---

def test_niveis_selecionados_derivam_os_campos_antigos_do_discriminado():
    revs = [_r(i, chars=200) for i in range(5)] + [_r(f"s{i}", spoiler=True) for i in range(2)]
    sel = selecionar(revs, HIST, cota_por_bucket=3)["negativas"]
    ns = sel.niveis[2.0]
    assert ns.n_descartadas_spoiler == ns.motivos_descarte["spoiler"]
    assert ns.n_descartadas_curtas == ns.motivos_descarte["abaixo_min_chars"]
    assert ns.n_indisponivel_truncamento == ns.motivos_descarte["truncada_sem_texto"]


def test_soma_dos_motivos_bate_no_pipeline_de_selecao_real():
    """O invariante central, verificado end-to-end através de `selecionar`,
    não só da função isolada."""
    revs = ([_r(f"a{i}", chars=200) for i in range(30)]
            + [_r(f"b{i}", chars=50) for i in range(20)]
            + [_r(f"c{i}", spoiler=True) for i in range(5)]
            + [_r(f"d{i}", completo=False) for i in range(3)])
    sel = selecionar(revs, HIST, cota_por_bucket=10)["negativas"]
    ns = sel.niveis[2.0]
    assert sum(ns.motivos_descarte.values()) == ns.n_brutas - ns.n_validas


def test_soma_bate_para_todos_os_niveis_e_buckets_de_um_filme_completo():
    import random
    rng = random.Random(42)
    revs = []
    for nivel in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0):
        for i in range(rng.randint(5, 60)):
            revs.append(_r(f"{nivel}-{i}", nivel=nivel,
                          chars=rng.choice([20, 60, 100, 150, 300, 500]),
                          spoiler=rng.random() < 0.1,
                          completo=rng.random() > 0.05))
    sel = selecionar(revs, HIST)
    for bucket in sel.values():
        for ns in bucket.niveis.values():
            assert sum(ns.motivos_descarte.values()) == ns.n_brutas - ns.n_validas
