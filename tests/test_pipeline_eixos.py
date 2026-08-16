"""[v1.9.14] Orquestração do bloco `eixos` no pipeline (§2.5 + §D3).

O que estes testes cercam é o estatuto ADITIVO: o schema de eixos é a
entrega central da versão, e mesmo assim nada nele pode derrubar um filme.
Sem classificação, sem taxonomia batendo, sem [D3] — o pipeline segue e o
JSON sai sem a chave, exatamente como já acontece com ficha e distribuição.
"""
from __future__ import annotations

import json

import pytest

from espectro24 import pipeline as P


@pytest.fixture
def output():
    return {"buckets": [
        {"bucket": "negativas", "n_validas": 40,
         "temas": [{"tema": "Ritmo lento", "mencoes_aproximadas": 20,
                    "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"}]},
        {"bucket": "positivas", "n_validas": 40,
         "temas": [{"tema": "Atmosfera", "mencoes_aproximadas": 30,
                    "n_reviews_analisadas": 40, "exemplo_parafraseado": "ex"}]},
    ]}


def _consenso():
    return {"filme-x": {
        "negativas": {f"v{i}": (["ritmo"] if i < 30 else []) for i in range(40)},
        "positivas": {f"p{i}": (["ritmo"] if i < 4 else []) for i in range(40)},
    }}


def _cliente(eixo="ritmo"):
    def call(system, user, model):
        tema = user.split("1. ")[1].splitlines()[0]
        return json.dumps({"rotulos": [{"tema": tema, "eixo": eixo}]})
    return call


def test_filme_fora_do_catalogo_classificado_devolve_None(output):
    assert P.montar_eixos("filme-inexistente", output, {},
                          consenso=_consenso(),
                          client_call=_cliente()) is None


def test_bloco_junta_o_numero_do_codigo_com_a_frase_da_rotulagem(output):
    bloco = P.montar_eixos("filme-x", output, {}, consenso=_consenso(),
                           client_call=_cliente())
    linha = next(l for l in bloco["linhas"] if l["eixo"] == "ritmo")
    assert linha["por_bucket"]["negativas"]["mencoes"] == 30      # do CÓDIGO
    assert linha["por_bucket"]["negativas"]["tema"] == "Ritmo lento"  # de [D3]
    assert bloco["contraste"] == "tematico"                       # 75% − 10%


def test_rotulagem_que_falha_deixa_o_numero_intacto(output):
    def call(system, user, model):
        raise RuntimeError("timeout")
    bloco = P.montar_eixos("filme-x", output, {}, consenso=_consenso(),
                           client_call=call)
    linha = next(l for l in bloco["linhas"] if l["eixo"] == "ritmo")
    assert linha["por_bucket"]["negativas"]["mencoes"] == 30
    assert linha["por_bucket"]["negativas"]["tema"] is None
    assert bloco["rotulagem"]["falharam"] == ["negativas", "positivas"]


def test_bloco_carrega_a_telemetria_da_rotulagem(output):
    bloco = P.montar_eixos("filme-x", output, {}, consenso=_consenso(),
                           client_call=_cliente())
    assert bloco["rotulagem"]["n_chamadas"] == 2


def test_sobreposicao_com_as_analisadas_entra_no_bloco(output):
    """[v1.9.15] `n_classificadas` é a INTERSECÇÃO com `analisadas`, não o
    total de linhas classificadas naquele bucket — do contrário, reviews
    classificadas fora da seleção de produção inflariam o denominador (o bug
    real achado ao unificar as duas populações, Entrega 1)."""
    analisadas = {"negativas": {f"v{i}" for i in range(20, 60)}}
    bloco = P.montar_eixos("filme-x", output, analisadas, consenso=_consenso(),
                           client_call=_cliente())
    fonte = bloco["fonte_classificacao"]["por_bucket"]["negativas"]
    assert (fonte["n_classificadas"], fonte["n_analisadas"],
            fonte["sobreposicao_com_analisadas"]) == (20, 40, 20)


def test_ids_analisados_do_bruto_reproduz_a_selecao_de_producao():
    """O caminho de enriquecimento tem de ver as MESMAS reviews que a síntese
    viu — foi a omissão do orçamento por nível que criou as duas amostras
    divergentes de §[D3], e este teste é o que impede a repetição."""
    from pathlib import Path
    if not Path("dados/bruto/cure/meta.json").exists():
        pytest.skip("bruto de `cure` indisponível")
    from espectro24.bruto import carregar
    from espectro24.selecao import selecionar

    meta, todas = carregar("cure", raiz="dados/bruto")
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    orc = {float(k): v for k, v in meta["orcamento_paginas_por_nivel"].items()}
    sel = selecionar(todas, hist, cota_por_bucket=40,
                     orcamento_paginas_por_nivel=orc)
    esperado = {n: {r.id for ns in b.niveis.values() for r in ns.validas}
                for n, b in sel.items()}
    assert P.ids_analisados_do_bruto("cure") == esperado


def test_o_bloco_carrega_a_propria_versao(output):
    """Enriquecer um JSON já publicado deixa DOIS carimbos no arquivo: o da
    narrativa e o do schema. A divergência é a verdade sobre o artefato — a
    alternativa seria reescrever o carimbo do arquivo inteiro depois do fato,
    que é o que a política de `VERSAO_COLETOR` já recusa."""
    from espectro24.config import SPEC_VERSION
    bloco = P.montar_eixos("filme-x", output, {}, consenso=_consenso(),
                           client_call=_cliente())
    assert bloco["spec_version"] == SPEC_VERSION
