"""[piloto de expansão] O material de ROTULAGEM dos pares obrigatórios: os
pares são os da seleção, cada um traz o que o formou, e o documento não
carrega julgamento nenhum — o rótulo é do dono.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

INSUMO = (RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"
          / "insumo-piloto-18")


@pytest.fixture(scope="module")
def pares():
    if not INSUMO.exists():
        pytest.skip("insumo do piloto ausente neste checkout")
    import pares_para_rotulagem as PP
    return PP, PP.montar_pares(sorted(p.stem for p in INSUMO.glob("*.json")))


def test_sao_os_38_pares_do_piloto_numerados_em_ordem(pares):
    _, ps = pares
    assert len(ps) == 38
    assert [p["id"] for p in ps] == [f"P{i:02d}" for i in range(1, 39)]


def test_cada_par_traz_os_prefixos_e_de_onde_vieram(pares):
    _, ps = pares
    for p in ps:
        assert len(p["prefixos"]) >= 2, p["id"]           # a régua da seleção
        for px in p["prefixos"]:
            assert px["no_base"] and px["no_forcado"], (p["id"], px)
        assert p["base"]["tema"] and p["forcado"]["tema"]
        assert p["base"]["grupo"] != p["forcado"]["grupo"]


def test_o_documento_pergunta_e_nao_julga(pares):
    """O MOLDE não carrega julgamento. Temas, paráfrases e palavras de
    origem são DADO (uma paráfrase pode dizer "fraco") — por isso são
    trocados por um marcador antes da varredura."""
    PP, ps = pares
    md = PP.renderizar(ps, nome_lote="t")
    assert md.count("estes dois temas falam do mesmo assunto?** SIM / NÃO") \
        == len(ps)
    neutros = [{**p,
                "base": {**p["base"], "tema": "X", "parafrase": "X"},
                "forcado": {**p["forcado"], "tema": "X", "parafrase": "X"},
                "prefixos": [{"prefixo": "x", "no_base": ["x"],
                              "no_forcado": ["x"]} for _ in p["prefixos"]]}
               for p in ps]
    molde = PP.renderizar(neutros, nome_lote="t").split("## Pares")[1].lower()
    for grupo in ("quem recomenda", "quem não recomenda"):
        molde = molde.replace(grupo, "")          # nome do grupo é dado
    for palavra in ("discurso", "coincid", "suspeit", "duvidos", "fraco",
                    "provável", "recomend", "provavelmente"):
        assert palavra not in molde, palavra
    gab = PP.gabarito_vazio(ps, nome_lote="t")
    assert all(p["resposta"] is None for p in gab["pares"])
