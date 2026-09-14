"""[piloto de expansão] A APLICAÇÃO da revisão do dono a um lote — o que ela
precisa garantir: o texto do dono entra VERBATIM e marcado como autoria
humana, a recusa vira `sem_condicao_publicavel`, o par é consolidado, e nada
é aplicado a um lote que não é o revisado.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

REV = RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"
INSUMO = REV / "insumo-piloto-18"
CORRECOES = REV / "correcoes-piloto-18.json"


def _ar():
    import aplicar_revisao_condicoes
    return aplicar_revisao_condicoes


@pytest.fixture(scope="module")
def dados():
    if not (INSUMO.exists() and CORRECOES.exists()):
        pytest.skip("revisão do piloto ausente neste checkout")
    ar = _ar()
    lote = ar.RR.carregar_lote(INSUMO)
    correcoes = json.loads(CORRECOES.read_text(encoding="utf-8"))
    return lote, correcoes, ar.aplicar(lote, correcoes)


def test_texto_do_dono_entra_verbatim_e_marcado(dados):
    lote, correcoes, blocos = dados
    humanos = {(s, l, c["tema_origem"]): c["texto"] for s, b in blocos.items()
               for l in ("vale_a_pena", "talvez_evite") for c in b[l]
               if c.get("origem") == "leitura_humana"}
    assert len(humanos) == 18        # 21 itens do dono − 3 recusas
    linhas = [i["linha_do_dono"] for i in correcoes["itens"]
              if "SEM CONDIÇÃO" not in i["linha_do_dono"]]
    for texto in humanos.values():
        assert any(l.endswith(" se você " + texto) for l in linhas), texto


def test_as_tres_recusas_viram_sem_condicao_publicavel(dados):
    _, _, blocos = dados
    rec = sorted((s, r["tema_origem"], r["regra"], r["origem"])
                 for s, b in blocos.items()
                 for r in b.get("sem_condicao_publicavel") or [])
    assert rec == [("force-majeure-2014", "NEG-E", "R6", "leitura_humana"),
                   ("hard-to-be-a-god", "POS-C", "R2", "leitura_humana"),
                   ("speak-no-evil-2022", "POS-C", "R6/R12", "leitura_humana")]
    for s, tid, *_ in rec:
        assert tid not in {c["tema_origem"] for l in ("vale_a_pena",
                           "talvez_evite") for c in blocos[s][l]}
        assert tid not in sum(blocos[s]["temas_saltados"].values(), [])


def test_c020_volta_da_descartada_para_a_coluna_na_posicao_da_selecao(dados):
    _, _, blocos = dados
    b = blocos["force-majeure-2014"]
    assert b["descartadas"] == []
    assert [c["tema_origem"] for c in b["vale_a_pena"]] == [
        "POS-A", "POS-B", "POS-C", "POS-F"]
    assert b["vale_a_pena"][-1]["origem"] == "leitura_humana"


def test_o_par_de_c024_e_consolidado(dados):
    """C024 (NEG-E) foi forçado por POS-B: POS-B ganha `par_recusado`."""
    _, _, blocos = dados
    b = blocos["force-majeure-2014"]
    pos_b = next(c for c in b["vale_a_pena"] if c["tema_origem"] == "POS-B")
    assert pos_b["par_recusado"] == "NEG-E"
    assert all("par_recusado" not in c for s, bb in blocos.items()
               for l in ("vale_a_pena", "talvez_evite") for c in bb[l]
               if (s, c["tema_origem"]) != ("force-majeure-2014", "POS-B"))


def test_filme_sem_correcao_fica_identico_ao_insumo(dados):
    lote, _, blocos = dados
    for slug in ("happy-hour-2015-1", "neighboring-sounds", "the-wailing"):
        assert blocos[slug] == dict(lote)[slug]


def test_recusa_revisao_de_outro_lote(dados):
    lote, correcoes, _ = dados
    outra = {**correcoes, "impressao_digital": "000000000000"}
    with pytest.raises(_ar().RevisaoInvalida):
        _ar().aplicar(lote, outra)


def test_recusa_abertura_que_nao_bate_com_a_coluna(dados):
    lote, correcoes, _ = dados
    trocada = copy.deepcopy(correcoes)
    item = next(i for i in trocada["itens"] if i["numero"] == "C032")
    item["linha_do_dono"] = item["linha_do_dono"].replace(
        "Talvez evite se você", "Vale a pena se você")
    with pytest.raises(_ar().RevisaoInvalida):
        _ar().aplicar(lote, trocada)
