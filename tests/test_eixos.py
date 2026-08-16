"""[v1.9.14, §2.5] Frequência por eixo, lift, margem e estado `contraste`.

O que estes testes protegem, em ordem de importância:

1. **A aritmética é EXATA.** 5 dos 35 filmes do catálogo têm o melhor lift em
   exatamente 20,0pp; sob ponto flutuante `0.2 >= 0.2` pode ser falso, e foi
   assim que a medição de referência produziu 13/35 em vez de 18/35. Aqui a
   comparação é `Fraction`, e a decisão de estar acima da margem é ESTRITA
   por escolha declarada (§2.5), não por acidente de representação.
2. **O código soma; ninguém mais.** Toda frequência é `Counter` sobre a
   classificação persistida — nenhum número vem de LLM.
3. **O denominador é o da amostra CLASSIFICADA**, e o bloco diz isso de si
   mesmo (§[D3], "Duas populações de 40").
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from espectro24 import eixos as E


def _classificacao(**por_bucket: dict[str, list[str]]):
    """Monta `{bucket: {id: [eixos]}}` a partir de kwargs legíveis."""
    return {b: dict(rs) for b, rs in por_bucket.items()}


def _uniforme(bucket_eixos: dict[str, tuple[str, int]], n: int = 40):
    """`{bucket: {id: [eixos]}}` com `k` reviews carregando cada eixo, de `n`.

    `{"negativas": ("ritmo", 24)}` → 40 reviews no bucket, 24 com `ritmo`.
    """
    out = {}
    for bucket, pares in bucket_eixos.items():
        reviews = {f"{bucket}:{i}": [] for i in range(n)}
        for eixo, k in (pares if isinstance(pares, list) else [pares]):
            for i in range(k):
                reviews[f"{bucket}:{i}"].append(eixo)
        out[bucket] = reviews
    return out


# --- frequência: o código conta ------------------------------------------

def test_frequencia_conta_reviews_e_nao_mencoes():
    """Uma review com o eixo conta UMA vez, mesmo repetindo o eixo."""
    cls = _classificacao(
        negativas={"a": ["ritmo", "ritmo"], "b": ["ritmo"], "c": ["atuacao"]})
    f = E.frequencias(cls)
    assert f["negativas"]["n"] == 3
    assert f["negativas"]["por_eixo"]["ritmo"] == 2


def test_frequencia_e_fracao_exata_com_denominador_visivel():
    cls = _uniforme({"negativas": [("ritmo", 24)]}, n=40)
    f = E.frequencias(cls)
    assert E.fracao(f["negativas"], "ritmo") == Fraction(24, 40)
    assert f["negativas"]["n"] == 40


def test_bucket_sem_review_classificada_nao_inventa_denominador():
    f = E.frequencias({"negativas": {}})
    assert f["negativas"]["n"] == 0
    assert E.fracao(f["negativas"], "ritmo") == Fraction(0)


# --- lift ------------------------------------------------------------------

def test_lift_e_freq_menos_o_maior_dos_outros_dois():
    cls = _uniforme({"negativas": [("ritmo", 24)],
                     "medianas": [("ritmo", 11)],
                     "positivas": [("ritmo", 19)]}, n=40)
    lifts = E.lifts(E.frequencias(cls))
    # negativas: 24/40 − max(11/40, 19/40) = 5/40
    assert lifts["negativas"]["ritmo"] == Fraction(5, 40)
    # medianas: 11/40 − 24/40 (o maior dos outros) = negativo
    assert lifts["medianas"]["ritmo"] == Fraction(-13, 40)


def test_lift_com_um_bucket_so_nao_tem_com_quem_comparar():
    """Sem outro bucket, não existe contraste — lift é zero, não a própria
    frequência (que faria um filme de um grupo só parecer todo contraste)."""
    cls = _uniforme({"positivas": [("ritmo", 30)]}, n=40)
    lifts = E.lifts(E.frequencias(cls))
    assert lifts["positivas"]["ritmo"] == Fraction(0)


# --- a margem, e a fronteira exata dos 5 filmes ---------------------------

def test_lift_exatamente_na_margem_NAO_esta_acima_dela():
    """O caso dos 5 filmes do catálogo (§2.5). 8 reviews de diferença em 40
    são exatamente 20,0pp; a decisão registrada é comparação ESTRITA."""
    cls = _uniforme({"negativas": [("critica_social", 33)],
                     "medianas": [("critica_social", 25)],
                     "positivas": [("critica_social", 19)]}, n=40)
    lifts = E.lifts(E.frequencias(cls))
    assert lifts["negativas"]["critica_social"] == Fraction(1, 5)  # 20,0pp
    assert not E.acima_da_margem(lifts["negativas"]["critica_social"])
    assert E.contraste(lifts) == "valorativo"


def test_um_quantum_acima_da_margem_ja_conta():
    """Com cota 40 o quantum é 1/40 = 2,5pp — o menor passo exprimível."""
    cls = _uniforme({"negativas": [("critica_social", 34)],
                     "medianas": [("critica_social", 25)],
                     "positivas": [("critica_social", 19)]}, n=40)
    lifts = E.lifts(E.frequencias(cls))
    assert lifts["negativas"]["critica_social"] == Fraction(9, 40)  # 22,5pp
    assert E.acima_da_margem(lifts["negativas"]["critica_social"])
    assert E.contraste(lifts) == "tematico"


def test_a_comparacao_nao_passa_por_ponto_flutuante():
    """A regressão que motivou o teste: `0.2 >= 0.2` em binário é FALSO para
    a fração exata 1/5 construída por subtração de floats. Se algum dia a
    implementação converter para float antes de comparar, este teste cai."""
    exato = Fraction(33, 40) - Fraction(25, 40)
    assert exato == Fraction(1, 5)
    assert not E.acima_da_margem(exato)
    # e o vizinho de baixo continua fora, sem depender de arredondamento
    assert not E.acima_da_margem(Fraction(199, 1000))


def test_margem_e_parametro_e_nao_constante_enterrada():
    lift = Fraction(1, 5)
    assert not E.acima_da_margem(lift)
    assert E.acima_da_margem(lift, margem_pp=15)


# --- contraste -------------------------------------------------------------

def test_contraste_valorativo_quando_nenhum_eixo_passa():
    cls = _uniforme({"negativas": [("ritmo", 20)],
                     "medianas": [("ritmo", 20)],
                     "positivas": [("ritmo", 21)]}, n=40)
    assert E.contraste(E.lifts(E.frequencias(cls))) == "valorativo"


def test_contraste_e_sempre_um_dos_dois_estados():
    assert E.contraste({}) == "valorativo"


# --- seleção de bullets: 2 de frequência + 3 de lift ----------------------

def test_bullets_sao_2_de_frequencia_e_3_de_lift():
    cls = _uniforme({
        "negativas": [("ritmo", 32), ("roteiro_estrutura", 30),
                      ("som_trilha", 28), ("atuacao", 26), ("comparacoes", 24)],
        "medianas": [("ritmo", 30), ("roteiro_estrutura", 29),
                     ("som_trilha", 2), ("atuacao", 3), ("comparacoes", 4)],
        "positivas": [("ritmo", 31), ("roteiro_estrutura", 28),
                      ("som_trilha", 1), ("atuacao", 2), ("comparacoes", 3)],
    }, n=40)
    f, l = E.frequencias(cls), E.lifts(E.frequencias(cls))
    bullets = E.bullets(f, l)["negativas"]
    # CONTRASTE primeiro — é o que só este grupo diz; consenso depois.
    assert [b["papel"] for b in bullets] == (
        ["contraste", "contraste", "contraste", "frequencia", "frequencia"])
    assert [b["eixo"] for b in bullets[3:]] == ["ritmo", "roteiro_estrutura"]
    assert len({b["eixo"] for b in bullets}) == 5


def test_eixo_que_e_consenso_E_contraste_entra_uma_vez_com_os_dois_papeis():
    """Achado no dado real (`cure`/positivas, `tom_atmosfera` com 40pp de
    lift): descontar do contraste o que já foi escolhido por frequência
    escondia o maior contraste do filme atrás do rótulo de consenso. Uma
    linha, os dois papéis."""
    cls = _uniforme({"negativas": [("ritmo", 36), ("atuacao", 20)],
                     "medianas": [("ritmo", 4), ("atuacao", 18)],
                     "positivas": [("ritmo", 2), ("atuacao", 19)]}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)))
    eixos = [b["eixo"] for b in bullets["negativas"]]
    assert eixos.count("ritmo") == 1
    papel = next(b["papel"] for b in bullets["negativas"] if b["eixo"] == "ritmo")
    assert papel == "frequencia_e_contraste"


def test_lista_encurta_em_vez_de_completar_com_ruido():
    """Sem eixo acima da margem, sobram só os 2 de frequência — a lista curta
    é informação (`contraste: valorativo`), não falha de preenchimento."""
    cls = _uniforme({"negativas": [("ritmo", 20), ("atuacao", 18)],
                     "medianas": [("ritmo", 20), ("atuacao", 18)],
                     "positivas": [("ritmo", 19), ("atuacao", 17)]}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)))
    papeis = [b["papel"] for b in bullets["negativas"]]
    assert papeis == ["frequencia", "frequencia"]


def test_empate_desfeito_pela_ordem_canonica_dos_eixos():
    """Dois filmes com o mesmo perfil não podem sair em ordens diferentes por
    acidente de iteração — mesma política de `ORDEM_CANONICA` no briefing."""
    cls = _uniforme({"negativas": [("atuacao", 20), ("ritmo", 20)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)))
    eixos = [b["eixo"] for b in bullets["negativas"][:2]]
    assert eixos == sorted(eixos, key=E.EIXOS.index)


def test_eixo_ausente_do_bucket_nao_vira_bullet():
    cls = _uniforme({"negativas": [("ritmo", 10)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)))
    assert [b["eixo"] for b in bullets["negativas"]] == ["ritmo"]


def test_livre_nunca_vira_bullet():
    """`livre` é o fallback da taxonomia — o que não coube em eixo nenhum.
    Publicá-lo como linha diria ao leitor que 'diversos' é um assunto."""
    cls = _uniforme({"negativas": [("livre", 30), ("ritmo", 10)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)))
    assert "livre" not in [b["eixo"] for b in bullets["negativas"]]


# --- o bloco do JSON -------------------------------------------------------

def test_bloco_declara_taxonomia_margem_e_contraste():
    cls = _uniforme({"negativas": [("ritmo", 30)],
                     "medianas": [("ritmo", 10)],
                     "positivas": [("ritmo", 8)]}, n=40)
    bloco = E.montar_bloco(cls, analisadas={}, temas_por_eixo={})
    assert bloco["taxonomia_id"] == E.TAXONOMIA_ID
    assert bloco["margem_lift_pp"] == E.MARGEM_LIFT_PP
    assert bloco["contraste"] == "tematico"


def test_bloco_carrega_as_contagens_inteiras_e_os_derivados():
    cls = _uniforme({"negativas": [("ritmo", 24)],
                     "medianas": [("ritmo", 11)],
                     "positivas": [("ritmo", 19)]}, n=40)
    bloco = E.montar_bloco(cls, analisadas={}, temas_por_eixo={})
    linha = next(l for l in bloco["linhas"] if l["eixo"] == "ritmo")
    cel = linha["por_bucket"]["negativas"]
    assert (cel["mencoes"], cel["de_n"]) == (24, 40)
    assert cel["freq_pct"] == 60.0
    assert cel["lift_pp"] == 12.5


def test_bloco_declara_a_sobreposicao_com_a_amostra_analisada():
    """§[D3]: são duas amostras de 40 diferentes, e o JSON tem de dizer o
    tamanho da divergência sem que ninguém precise remedi-la."""
    cls = _uniforme({"negativas": [("ritmo", 24)]}, n=40)
    analisadas = {"negativas": {f"negativas:{i}" for i in range(30, 70)}}
    bloco = E.montar_bloco(cls, analisadas=analisadas, temas_por_eixo={})
    fonte = bloco["fonte_classificacao"]["por_bucket"]["negativas"]
    assert fonte["n_classificadas"] == 40
    assert fonte["n_analisadas"] == 40
    assert fonte["sobreposicao_com_analisadas"] == 10


def test_bloco_sem_classificacao_nenhuma_e_None():
    """Chave ausente distingue 'não classificado' de 'classificado e vazio'."""
    assert E.montar_bloco({}, analisadas={}, temas_por_eixo={}) is None


def test_celula_sem_tema_e_None_e_nao_string_vazia():
    cls = _uniforme({"negativas": [("ritmo", 24)],
                     "medianas": [("ritmo", 11)]}, n=40)
    bloco = E.montar_bloco(cls, analisadas={},
                           temas_por_eixo={"negativas": {"ritmo": {
                               "tema": "Ritmo lento", "exemplo_parafraseado": "x"}}})
    linha = next(l for l in bloco["linhas"] if l["eixo"] == "ritmo")
    assert linha["por_bucket"]["negativas"]["tema"] == "Ritmo lento"
    assert linha["por_bucket"]["medianas"]["tema"] is None


def test_bloco_e_serializavel_em_json_sem_Fraction():
    import json
    cls = _uniforme({"negativas": [("ritmo", 24)],
                     "medianas": [("ritmo", 11)],
                     "positivas": [("ritmo", 19)]}, n=40)
    json.dumps(E.montar_bloco(cls, analisadas={}, temas_por_eixo={}))


def test_linhas_saem_na_ordem_canonica_dos_eixos():
    cls = _uniforme({"negativas": [("critica_social", 10), ("ritmo", 20)]},
                    n=40)
    bloco = E.montar_bloco(cls, analisadas={}, temas_por_eixo={})
    ordem = [l["eixo"] for l in bloco["linhas"]]
    assert ordem == sorted(ordem, key=E.EIXOS.index)


# --- contra o dado REAL do catálogo ---------------------------------------

@pytest.fixture(scope="module")
def catalogo():
    from pathlib import Path
    caminho = Path(__file__).resolve().parent.parent / E.CONSENSO_PADRAO
    if not caminho.exists():
        pytest.skip(f"classificação não disponível: {caminho}")
    return E.carregar_classificacao(caminho)


def test_catalogo_tem_os_35_filmes_classificados(catalogo):
    assert len(catalogo) == 35


def test_catalogo_reproduz_13_tematicos_e_22_valorativos(catalogo):
    """O número decidido em §2.5. Se a margem, a métrica ou a comparação
    mudarem, é aqui que o catálogo inteiro reclama."""
    estados = {slug: E.contraste(E.lifts(E.frequencias(cls)))
               for slug, cls in catalogo.items()}
    tematicos = [s for s, e in estados.items() if e == "tematico"]
    assert (len(tematicos), len(estados) - len(tematicos)) == (13, 22)


def test_os_5_filmes_na_linha_dos_20pp_ficam_valorativos(catalogo):
    """Documenta quem depende da comparação estrita — sob `>=` exato estes 5
    virariam `tematico` e o catálogo iria a 18/35 (§2.5)."""
    na_linha = {"barbie", "bones-and-all", "hereditary", "im-still-here-2024",
                "spider-man-across-the-spider-verse"}
    for slug in na_linha:
        lifts = E.lifts(E.frequencias(catalogo[slug]))
        melhor = max(v for por_eixo in lifts.values() for v in por_eixo.values())
        assert melhor == Fraction(1, 5), slug
        assert E.contraste(lifts) == "valorativo", slug


def test_estado_dos_3_filmes_publicados(catalogo):
    esperado = {"cure": "tematico", "the-invite-2026": "tematico",
                "cidade-de-deus": "valorativo"}
    for slug, estado in esperado.items():
        assert E.contraste(E.lifts(E.frequencias(catalogo[slug]))) == estado


def _corpus_falso(tmp_path, taxonomia_id: str):
    import json
    (tmp_path / "amostra.json").write_text(
        json.dumps({"taxonomia_id": taxonomia_id}), encoding="utf-8")
    (tmp_path / "consenso.jsonl").write_text(
        json.dumps({"slug": "x", "bucket": "negativas", "id": "viewing:1",
                    "eixos": ["ritmo"]}) + "\n", encoding="utf-8")
    return tmp_path / "consenso.jsonl"


def test_carregar_recusa_taxonomia_diferente(tmp_path):
    """Reaproveitar classificação de outra taxonomia em silêncio é o modo de
    falha que o `taxonomia_id` existe para impedir (§2.5) — e ele é SILENCIOSO
    por natureza: os eixos têm os mesmos nomes sob qualquer versão do prompt."""
    caminho = _corpus_falso(tmp_path, "0000deadbeef")
    with pytest.raises(ValueError, match="taxonomia"):
        E.carregar_classificacao(caminho)


def test_carregar_aceita_a_taxonomia_corrente(tmp_path):
    caminho = _corpus_falso(tmp_path, E.TAXONOMIA_ID)
    assert E.carregar_classificacao(caminho) == {
        "x": {"negativas": {"viewing:1": ["ritmo"]}}}


def test_carregar_exige_o_manifesto_da_taxonomia(tmp_path):
    """Sem `amostra.json` ao lado não há como saber sob qual régua o arquivo
    foi produzido — e presumir a corrente é exatamente o silêncio acima."""
    import json
    (tmp_path / "consenso.jsonl").write_text(
        json.dumps({"slug": "x", "bucket": "negativas", "id": "v:1",
                    "eixos": []}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="taxonomia"):
        E.carregar_classificacao(tmp_path / "consenso.jsonl")


def test_tema_que_perde_a_celula_por_colisao_nao_some_do_bloco():
    """Com 6 temas e 10 eixos a colisão é frequente (medido: `cure`/negativas
    tem 6 temas em 3 células). O tema que não vira legenda da linha continua
    no dado — perder tema em silêncio seria a interface escondendo material
    que a síntese produziu."""
    cls = _uniforme({"negativas": [("roteiro_estrutura", 26)]}, n=40)
    bloco = E.montar_bloco(cls, analisadas={}, temas_por_eixo={
        "negativas": {"roteiro_estrutura": {
            "tema": "Personagens pouco cativantes",
            "exemplo_parafraseado": "x",
            "temas_no_mesmo_eixo": ["Enredo confuso", "Diálogos fracos"]}}})
    cel = bloco["linhas"][0]["por_bucket"]["negativas"]
    assert cel["temas_no_mesmo_eixo"] == ["Enredo confuso", "Diálogos fracos"]
