"""[piloto de expansão] O relatório de revisão de condições — o que ele
PRECISA garantir para servir de insumo a uma revisora externa que não tem o
repositório: numeração estável, campos completos, regras autocontidas antes
do primeiro item, categorias exatas no lugar certo, e nenhum julgamento.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


def _rr():
    import relatorio_revisao_condicoes
    return relatorio_revisao_condicoes


def _tema(t, ex, mencoes=12):
    return {"tema": t, "mencoes_aproximadas": mencoes,
            "n_reviews_analisadas": 40, "exemplo_parafraseado": ex}


def _doc(slug):
    pos = [_tema("Fotografia sombria", "a fotografia sombria e opressiva"),
           _tema("Comparação com o clássico de 1940",
                 "o grupo compara com o clássico animado")]
    neg = [_tema("Filme superestimado", "a fama não corresponde ao filme"),
           _tema("Ritmo lento", "acharam o andamento arrastado e cansativo")]
    return {"slug": slug, "ficha": {"titulo": f"Título de {slug}"},
            "buckets": [
                {"bucket": "positivas", "estado_piso": "completa",
                 "modo": "completo", "share_real": 70, "temas": pos},
                {"bucket": "negativas", "estado_piso": "completa",
                 "modo": "completo", "share_real": 20, "temas": neg}],
            "eixos": {"linhas": [
                {"eixo": "expectativa", "por_bucket": {
                    "negativas": {"tema": "Filme superestimado",
                                  "temas_no_mesmo_eixo": []}}}]}}


def _bloco():
    return {
        "vale_a_pena": [
            # sem "clima": o marcador de spoiler `clim*` (clímax) casa "clima"
            {"texto": "aprecia uma fotografia sombria de tom opressivo",
             "tema_origem": "POS-A", "tema_texto": "Fotografia sombria",
             "rotulo_forca": "muitos"},
            {"texto": "busca a mesma emoção da animação clássica",
             "tema_origem": "POS-B",
             "tema_texto": "Comparação com o clássico de 1940",
             "rotulo_forca": "muitos"}],
        "talvez_evite": [
            {"texto": "se frustra quando a fama da obra supera o que ela entrega",
             "tema_origem": "NEG-A", "tema_texto": "Filme superestimado",
             "rotulo_forca": "muitos"}],
        "descartadas": [
            {"texto": "se cansa com 3 horas de andamento arrastado",
             "tema_origem": "NEG-B", "lado": "talvez_evite",
             "flags": ["digito"]}],
        "temas_pedidos": {"vale_a_pena": ["POS-A", "POS-B"],
                          "talvez_evite": ["NEG-A", "NEG-B"]},
        "temas_saltados": {"vale_a_pena": [], "talvez_evite": ["NEG-B"]},
        "peso": {"vale_a_pena": {"peso_texto": "~70% das notas"},
                 "talvez_evite": {"peso_texto": "~20% das notas"}},
    }


@pytest.fixture
def ambiente(tmp_path):
    res = tmp_path / "resultado"
    res.mkdir()
    for slug in ("filme-b", "filme-a"):
        (res / f"{slug}.json").write_text(json.dumps(_doc(slug)),
                                          encoding="utf-8")
    lote = [("filme-b", _bloco()), ("filme-a", _bloco())]
    return res, lote


def test_numeracao_e_estavel_e_nao_depende_da_ordem_do_lote(ambiente):
    rr = _rr()
    res, lote = ambiente
    a = rr.montar_itens(lote, res)
    b = rr.montar_itens(list(reversed(lote)), res)
    assert [(i["numero"], i["slug"], i["lado"], i["tema_origem"]) for i in a] \
        == [(i["numero"], i["slug"], i["lado"], i["tema_origem"]) for i in b]
    assert rr.impressao_digital(a) == rr.impressao_digital(b)
    # ordem canônica: filme, coluna, posição do tema — descartada no lugar dela
    assert [(i["slug"], i["tema_origem"]) for i in a[:4]] == [
        ("filme-a", "POS-A"), ("filme-a", "POS-B"),
        ("filme-a", "NEG-A"), ("filme-a", "NEG-B")]
    assert [i["numero"] for i in a] == [f"C{n:03d}" for n in range(1, 9)]


def test_cada_item_traz_os_campos_que_a_revisora_precisa(ambiente):
    rr = _rr()
    res, lote = ambiente
    itens = rr.montar_itens(lote, res)
    md = rr.renderizar(itens, lote, nome_lote="t", origem="x")
    for it in itens:
        bloco = md.split(f"#### {it['numero']} ")[1].split("\n#### ")[0]
        assert it["slug"] in bloco                               # filme
        assert rr.COLUNA[it["lado"]] in bloco                    # coluna
        assert it["texto"] in bloco                              # texto integral
        assert it["tema"] in bloco and it["tema_origem"] in bloco  # tema
        assert "rótulo de força (do código):** `muitos`" in bloco \
            or it["flags_validador"]                             # rótulo
        assert "categorias de risco" in bloco                    # categoria


def test_regras_vem_antes_do_primeiro_item_e_sao_autocontidas(ambiente):
    rr = _rr()
    res, lote = ambiente
    md = rr.renderizar(rr.montar_itens(lote, res), lote, nome_lote="t",
                       origem="x")
    assert md.index("## 1. Regras") < md.index("#### C001")
    topo = md[:md.index("#### C001")]
    for trecho in ("rótulo de força", "`poucos` abaixo de 10%",
                   "R4 — Zero algarismo", "clássico de 1940",
                   "R13 — O eixo `expectativa`", "NÃO que o item não",
                   "CONFIRMO", "DUVIDOSO"):
        assert trecho in topo, trecho


def test_categorias_exatas_caem_no_lugar_certo(ambiente):
    rr = _rr()
    res, lote = ambiente
    por = {(i["slug"], i["tema_origem"]): i
           for i in rr.montar_itens(lote, res)}
    assert por[("filme-a", "NEG-B")]["categoria"] == "descartada"
    assert "algarismo" in dict(por[("filme-a", "NEG-B")]["categorias"])[
        "descartada"]                                   # o MOTIVO vai junto
    assert por[("filme-a", "NEG-A")]["categoria"] == "expectativa"
    assert por[("filme-a", "POS-A")]["categoria"] == rr.SEM_CATEGORIA


def test_ano_em_nome_de_tema_nao_cai_em_digito_mas_digito_na_condicao_cai(
        ambiente):
    rr = _rr()
    res, lote = ambiente
    por = {(i["slug"], i["tema_origem"]): i
           for i in rr.montar_itens(lote, res)}
    ano = por[("filme-a", "POS-B")]
    assert "digito" not in dict(ano["categorias"])
    assert ano["anos_admitidos"] == ["1940"]
    assert "digito" in dict(por[("filme-a", "NEG-B")]["categorias"])


def test_tema_que_mudou_depois_da_geracao_e_apontado(ambiente):
    """Uma republicação regera a síntese e troca os temas; a condição gerada
    antes passa a citar um tema que não é mais aquele."""
    rr = _rr()
    res, lote = ambiente
    doc = _doc("filme-a")
    doc["buckets"][0]["temas"][0]["tema"] = "Direção de arte"
    (res / "filme-a.json").write_text(json.dumps(doc), encoding="utf-8")
    por = {(i["slug"], i["tema_origem"]): i
           for i in rr.montar_itens(lote, res)}
    assert por[("filme-a", "POS-A")]["categoria"] == "integridade"


def test_o_relatorio_nao_julga(ambiente):
    """Organiza e apresenta. Nenhum campo de veredito, nota ou recomendação
    no item — o julgamento é de fora."""
    rr = _rr()
    res, lote = ambiente
    proibidas = {"aprovado", "aprovada", "rejeitado", "rejeitada", "nota",
                 "score", "pontuacao", "recomendacao", "veredito", "confianca"}
    for it in rr.montar_itens(lote, res):
        assert not proibidas & set(it), set(it) & proibidas


def test_recusa_escrever_em_resultado():
    rr = _rr()
    with pytest.raises(SystemExit):
        rr._checar_saida(rr.RESULTADO_DIR / "relatorio.md")


# ===========================================================================
# [piloto de expansão] "Sem condição publicável", par e autoria
# ===========================================================================

def _bloco_com_recusa():
    b = _bloco()
    b["vale_a_pena"][0]["origem"] = "leitura_humana"
    b["vale_a_pena"] = b["vale_a_pena"][:1]            # POS-B sai da coluna
    b["sem_condicao_publicavel"] = [{
        "tema_origem": "POS-B", "lado": "vale_a_pena", "regra": "R6/R12",
        "motivo": "o tema usa só o desfecho", "origem": "leitura_humana"}]
    b["talvez_evite"][0]["par_recusado"] = "POS-B"
    b["descartadas"] = []                               # NEG-B vira desfeito
    b["par_desfeito"] = [{
        "texto": "se cansa com andamento arrastado", "tema_origem": "NEG-B",
        "lado": "talvez_evite", "tema_base": "POS-B",
        "tema_texto": "Ritmo lento", "rotulo_forca": "muitos"}]
    b["temas_saltados"] = {"vale_a_pena": ["POS-B"], "talvez_evite": ["NEG-B"]}
    return b


@pytest.fixture
def ambiente_recusa(tmp_path):
    res = tmp_path / "resultado"
    res.mkdir()
    (res / "filme-a.json").write_text(json.dumps(_doc("filme-a")),
                                      encoding="utf-8")
    return res, [("filme-a", _bloco_com_recusa())]


def test_recusa_e_item_na_posicao_do_tema_e_secao_antes_de_descartada(
        ambiente_recusa):
    rr = _rr()
    res, lote = ambiente_recusa
    itens = rr.montar_itens(lote, res)
    assert [(i["numero"], i["tema_origem"]) for i in itens] == [
        ("C001", "POS-A"), ("C002", "POS-B"), ("C003", "NEG-A"),
        ("C004", "NEG-B")]
    rec = itens[1]
    assert rec["categoria"] == "sem_condicao" and rec["texto"] == ""
    md = rr.renderizar(itens, lote, nome_lote="t", origem="x")
    assert md.index("### 3.1 Sem condição publicável") < md.index(
        "Descartada pelo validador automático (")
    assert "A recusa procede? DUVIDOSO = existia uma condição honesta" in md
    bloco = md.split("#### C002 ")[1].split("\n#### ")[0]
    for trecho in ("sem condição publicável", "`R6/R12`", "anti-spoiler",
                   "especificidade", "o tema usa só o desfecho",
                   "**autoria:** leitura humana", "efeito sobre o par",
                   "`NEG-A`", "`NEG-B`"):
        assert trecho in bloco, trecho


def test_par_recusado_e_par_desfeito_sao_categorias_exatas(ambiente_recusa):
    rr = _rr()
    res, lote = ambiente_recusa
    por = {i["tema_origem"]: i for i in rr.montar_itens(lote, res)}
    assert por["NEG-B"]["categoria"] == "par_desfeito"
    # NEG-A é `expectativa` antes de tudo; o par RECUSADO aparece como toque
    assert "par_recusado" in dict(por["NEG-A"]["categorias"])
    assert por["POS-A"]["origem"] == "leitura_humana"


def test_regra_de_topo_publicar_menos_nao_e_defeito(ambiente_recusa):
    rr = _rr()
    res, lote = ambiente_recusa
    md = rr.renderizar(rr.montar_itens(lote, res), lote, nome_lote="t",
                       origem="x")
    topo = md[:md.index("#### C001")]
    assert "Publicar menos não é defeito" in topo
    assert "R1, R2,\nR6, R12 ou R13" in topo


def test_apendice_de_silencio_nao_lista_recusa_nem_par_desfeito(
        ambiente_recusa):
    _, lote = ambiente_recusa
    assert _rr().saltados(lote) == []


INSUMO_REAL = (RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"
               / "insumo-piloto-18")


def test_a_numeracao_do_lote_real_nao_mudou():
    """O lote `0ec05ad3e326` foi revisado pelo número. Nenhuma mudança no
    relatório pode renumerar um lote que não tem recusa nem par."""
    if not INSUMO_REAL.exists():
        pytest.skip("insumo do piloto ausente neste checkout")
    rr = _rr()
    itens = rr.montar_itens(rr.carregar_lote(INSUMO_REAL))
    assert rr.impressao_digital(itens) == "0ec05ad3e326"
    assert len(itens) == 141
