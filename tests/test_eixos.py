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

def test_lift_exatamente_na_margem_ESTA_acima_dela():
    """A semântica `>=` da v1.9.15 SOBREVIVE à lei por `n` (v1.9.34) — só
    mudou onde a fronteira fica.

    O teste original usava 20,0pp com n=40, porque 5 dos 35 filmes sentavam
    exatamente ali sob a margem fixa. Sob a lei, o limiar de n=40 é 22,83pp e
    NENHUM lift racional o atinge exatamente (`144,4/√40` é irracional). A
    fronteira exata existe quando `n` é um QUADRADO PERFEITO: com n=100,
    `144,4/√100 = 14,44pp` é racional, e `lift = 1444/10000` cai exatamente
    em cima dela.

    "Margem MÍNIMA" continua sendo `>=`: quem senta na fronteira ATINGE."""
    lift = Fraction(1444, 10000)
    assert lift * lift * 100 == E.MARGEM_LEI_K2      # exatamente na fronteira
    assert E.acima_da_margem(lift, 100) is True
    assert E.acima_da_margem(lift - Fraction(1, 10 ** 12), 100) is False


def test_um_quantum_abaixo_da_margem_fica_fora():
    """Com cota 40 o quantum é 1/40 = 2,5pp — o menor passo exprimível."""
    cls = _uniforme({"negativas": [("critica_social", 32)],
                     "medianas": [("critica_social", 25)],
                     "positivas": [("critica_social", 19)]}, n=40)
    lifts = E.lifts(E.frequencias(cls))
    assert lifts["negativas"]["critica_social"] == Fraction(7, 40)  # 17,5pp
    assert not E.acima_da_margem(lifts["negativas"]["critica_social"], 40)
    assert E.contraste(lifts, n=40) == "valorativo"


def test_a_comparacao_nao_passa_por_ponto_flutuante():
    """A regressão que motivou o teste: `0.2 >= 0.2` em binário é FALSO para
    a fração exata 1/5 construída por subtração de floats — foi essa
    conversão silenciosa que produziu o 13/35 errado na medição de
    referência. Se algum dia a implementação converter para float antes de
    comparar, este teste cai."""
    exato = Fraction(33, 40) - Fraction(25, 40)
    assert exato == Fraction(1, 5)
    # [v1.9.34] a margem deixou de ser 20pp fixo; com n=40 o limiar é 22,83pp,
    # então 1/5 NÃO atinge mais — o que este teste protege é a EXATIDÃO, não
    # o valor: a fração construída por subtração continua sendo comparada sem
    # passar por float. `test_margem_por_n.py` cobre a lei em si.
    assert E.acima_da_margem(Fraction(23, 100), 40)     # 23pp > 22,83pp
    assert not E.acima_da_margem(Fraction(2283, 10000), 40)  # o vizinho de baixo


def test_a_margem_depende_de_n_e_nao_e_constante_enterrada():
    """[v1.9.34] Era `margem_pp` como parâmetro; virou `n`, e o limiar sai da
    lei. O MESMO lift decide diferente conforme o tamanho da amostra — que é
    a mudança inteira desta versão em uma asserção."""
    lift = Fraction(1, 5)                       # 20,0pp
    assert not E.acima_da_margem(lift, 40)      # limiar 22,83pp — não atinge
    assert E.acima_da_margem(lift, 60)          # limiar 18,64pp — atinge
    assert not E.acima_da_margem(lift, 20)      # limiar 32,29pp — longe


# --- contraste -------------------------------------------------------------

def test_contraste_valorativo_quando_nenhum_eixo_passa():
    cls = _uniforme({"negativas": [("ritmo", 20)],
                     "medianas": [("ritmo", 20)],
                     "positivas": [("ritmo", 21)]}, n=40)
    assert E.contraste(E.lifts(E.frequencias(cls)), n=40) == "valorativo"


def test_contraste_sem_classificacao_nenhuma():
    """Sem bucket nenhum, `n_efetivo` é 0 — abaixo do piso, e o estado NÃO é
    decidido. Até a v1.9.33 isto devolvia `valorativo`, que afirmava "os
    grupos falam das mesmas coisas" sobre zero reviews."""
    assert E.contraste({}, n=E.n_efetivo({})) is None


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
    bullets = E.bullets(f, l, 40)["negativas"]
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
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)), 40)
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
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)), 40)
    papeis = [b["papel"] for b in bullets["negativas"]]
    assert papeis == ["frequencia", "frequencia"]


def test_empate_desfeito_pela_ordem_canonica_dos_eixos():
    """Dois filmes com o mesmo perfil não podem sair em ordens diferentes por
    acidente de iteração — mesma política de `ORDEM_CANONICA` no briefing."""
    cls = _uniforme({"negativas": [("atuacao", 20), ("ritmo", 20)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)), 40)
    eixos = [b["eixo"] for b in bullets["negativas"][:2]]
    assert eixos == sorted(eixos, key=E.EIXOS.index)


def test_eixo_ausente_do_bucket_nao_vira_bullet():
    cls = _uniforme({"negativas": [("ritmo", 10)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)), 40)
    assert [b["eixo"] for b in bullets["negativas"]] == ["ritmo"]


def test_livre_nunca_vira_bullet():
    """`livre` é o fallback da taxonomia — o que não coube em eixo nenhum.
    Publicá-lo como linha diria ao leitor que 'diversos' é um assunto."""
    cls = _uniforme({"negativas": [("livre", 30), ("ritmo", 10)],
                     "medianas": [], "positivas": []}, n=40)
    bullets = E.bullets(E.frequencias(cls), E.lifts(E.frequencias(cls)), 40)
    assert "livre" not in [b["eixo"] for b in bullets["negativas"]]


# --- o bloco do JSON -------------------------------------------------------

def test_bloco_declara_taxonomia_margem_e_contraste():
    cls = _uniforme({"negativas": [("ritmo", 30)],
                     "medianas": [("ritmo", 10)],
                     "positivas": [("ritmo", 8)]}, n=40)
    bloco = E.montar_bloco(cls, analisadas={}, temas_por_eixo={})
    assert bloco["taxonomia_id"] == E.TAXONOMIA_ID
    assert bloco["margem_lift_pp"] == round(E.limiar_pp(40), 2)
    assert bloco["margem"]["n"] == 40
    assert bloco["margem"]["constante_quadrada"] == [2085136, 1000000]
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


def test_classificacao_orfa_da_selecao_antiga_nao_infla_o_denominador():
    """[v1.9.15, Entrega 1] A REGRESSÃO REAL achada ao estender a
    classificação de `cure`: `consenso.jsonl` acumula — 27 reviews da
    seleção antiga (errada) continuam classificadas depois que as 13 que
    faltavam à seleção de produção são adicionadas, e `n` saltava de 40 para
    53 sem este filtro. `analisadas` (as 40 da produção) tem de FILTRAR a
    classificação, não só somar-se a ela."""
    # 27 "boas" (na produção) + 13 "órfãs" (só na seleção antiga, fora da
    # produção) — o cenário exato medido em `cure`/negativas.
    boas = {f"boa:{i}": ["ritmo"] if i < 20 else [] for i in range(27)}
    orfas = {f"orfa:{i}": ["ritmo"] for i in range(13)}
    cls = {"negativas": {**boas, **orfas}}
    analisadas = {"negativas": set(boas)}  # só as 27 pertencem à produção
    bloco = E.montar_bloco(cls, analisadas=analisadas, temas_por_eixo={})
    linha = next(l for l in bloco["linhas"] if l["eixo"] == "ritmo")
    assert linha["por_bucket"]["negativas"]["de_n"] == 27  # NÃO 40
    assert linha["por_bucket"]["negativas"]["mencoes"] == 20  # NÃO 33


def test_bloco_declara_a_sobreposicao_quando_ha_divergencia():
    """§[D3]: quando as duas amostras (classificada e analisada) DIVERGEM, o
    JSON tem de dizer o tamanho da divergência sem que ninguém precise
    remedi-la à mão. [v1.9.15] E a frequência é calculada só sobre a
    INTERSECÇÃO — `n_classificadas` é o filtrado (10), nunca o total bruto
    (40): é o que impede o denominador de inflar com classificação órfã, o
    bug real achado ao rodar a extensão (`cure` saltando de 40 para 53)."""
    cls = _uniforme({"negativas": [("ritmo", 24)]}, n=40)
    analisadas = {"negativas": {f"negativas:{i}" for i in range(30, 70)}}
    bloco = E.montar_bloco(cls, analisadas=analisadas, temas_por_eixo={})
    fonte = bloco["fonte_classificacao"]["por_bucket"]["negativas"]
    assert fonte["n_classificadas"] == 10   # intersecção: ids 30-39 (10 de 40)
    assert fonte["n_analisadas"] == 40
    assert fonte["sobreposicao_com_analisadas"] == 10


def test_fonte_classificacao_e_omitida_quando_as_populacoes_sao_iguais():
    """[v1.9.15, Entrega 1] Com a unificação, `fonte_classificacao` deixa de
    ter objeto para os filmes já estendidos: declarar uma divergência que não
    existe mais é pior que não declarar nada — texto morto que engana. A
    chave some do bloco quando TODO bucket tem sobreposição completa."""
    cls = _uniforme({"negativas": [("ritmo", 24)], "positivas": [("ritmo", 10)]},
                    n=40)
    analisadas = {"negativas": {f"negativas:{i}" for i in range(40)},
                  "positivas": {f"positivas:{i}" for i in range(40)}}
    bloco = E.montar_bloco(cls, analisadas=analisadas, temas_por_eixo={})
    assert "fonte_classificacao" not in bloco


def test_fonte_classificacao_aparece_se_qualquer_bucket_divergir():
    """Um bucket unificado e outro não: a chave PRECISA aparecer, porque
    ainda há divergência a declarar em algum lugar do filme."""
    cls = _uniforme({"negativas": [("ritmo", 24)], "positivas": [("ritmo", 10)]},
                    n=40)
    analisadas = {"negativas": {f"negativas:{i}" for i in range(40)},
                  "positivas": {f"positivas:{i}" for i in range(30, 70)}}
    bloco = E.montar_bloco(cls, analisadas=analisadas, temas_por_eixo={})
    assert "fonte_classificacao" in bloco


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
    """[2026-08-31] DUAS correções em relação à versão original.

    **(1) Lê `CONSENSO_VERIFICADO`, não `CONSENSO_PADRAO`.** A fixture
    original lia `consenso.jsonl` — o consenso CRU, pré-verificador —, um
    resíduo de quando o teste foi escrito (v1.9.15), ANTES da adoção do
    passe `V2_alvo` na v1.9.16. Desde então, `_carregar_consenso_producao`
    prefere o VERIFICADO sempre que ele existe e está em dia (§2.5 da SPEC)
    — é ele que produção usa, não o cru. A divergência era invisível porque
    ninguém tinha comparado os dois; ficou exposta ao investigar a
    discrepância desta correção.

    **(2) Filtrado por `_filtrar_pela_analisada`, como `montar_bloco` faz na
    produção real** — não o dict cru de `carregar_classificacao`.

    Achado ao estender a cobertura de classificação aos 35 filmes
    (`AUDITORIA_POPULACAO_E_GABARITO.md`/`RELATORIO_GABARITO_E_COBERTURA.md`):
    `consenso.jsonl`/`consenso_verificado.jsonl` ACUMULAM classificação de
    seleções antigas (o mesmo defeito que motivou `_filtrar_pela_analisada`
    na v1.9.15, agora manifesto em 93 dos 105 buckets, não só nos 9 que a
    extensão original tocou). O dict cru chega a ter 68 reviews classificadas
    num bucket de 40 — sem o filtro, os testes mediam um denominador que a
    síntese nunca leu, exatamente o "dois quarentas" que a v1.9.15 corrigiu
    só para os 3 filmes publicados na época. Este fixture aplica a MESMA
    correção que `montar_eixos`/`montar_bloco` já aplicam em produção, para
    que o teste continue sendo um sentinela do catálogo REAL, não de um
    caminho de cálculo que a produção não usa.
    """
    from pathlib import Path
    from espectro24.pipeline import amostra_do_bruto
    caminho = Path(__file__).resolve().parent.parent / E.CONSENSO_VERIFICADO
    if not caminho.exists():
        pytest.skip(f"classificação não disponível: {caminho}")
    bruto = E.carregar_classificacao(caminho)
    raiz_bruto = Path(__file__).resolve().parent.parent / "dados" / "bruto"
    saida = {}
    for slug, cls in bruto.items():
        if not (raiz_bruto / slug).is_dir():
            saida[slug] = cls
            continue
        jp = Path(__file__).resolve().parent.parent / "resultado" / f"{slug}.json"
        import json
        coleta = (json.loads(jp.read_text(encoding="utf-8")).get("coleta")
                  if jp.exists() else None)
        analisadas = {b: {r.id for r in rs} for b, rs in
                      amostra_do_bruto(slug, coleta=coleta, raiz=raiz_bruto).items()}
        saida[slug] = E._filtrar_pela_analisada(cls, analisadas)
    return saida


def test_catalogo_tem_os_35_filmes_classificados(catalogo):
    assert len(catalogo) == 35


def test_catalogo_reproduz_6_tematicos_29_valorativos_e_1_sem_estado(catalogo):
    """[v1.9.34] **A contagem do catálogo sob a LEI POR `n` (§2.5).**

    A história desta asserção, porque ela é o sentinela do catálogo inteiro e
    já mudou três vezes por razões diferentes:

    - **13/35** (v1.9.14) — margem fixa de 20pp com `>` estrito, que
      reproduzia por construção o bug de ponto flutuante da medição de
      referência.
    - **18/17** (v1.9.15) — o mesmo 20pp com `>=` exato, a fronteira que a
      medição sempre pretendeu. Cobertura de classificação em 70,7%.
    - **16/19** (2026-08-31) — mesmo 20pp, cobertura estendida a 100%: 10
      filmes mudaram de estado, 6 deles perdendo um contraste que o veredito
      publicado nomeava por extenso.
    - **6/28/1** (v1.9.34, esta) — a margem deixa de ser um número fixo. Não
      é mais um ajuste de fronteira: os 16/19 vinham de um limiar cuja taxa
      de falso contraste era de **17,3% em n=40 e 37,3% no `n` mediano em que
      o catálogo foi de fato publicado (28)**, com FDR de 24–38% entre os 16
      `tematico`. A lei calibra o limiar para ≈5%.

    O 1 sem estado é `obsession-2026` (buckets 5/6/8): abaixo do piso de
    `n < 10`, o estado NÃO é publicado — e ele é o filme cujo `tematico`
    carregava menos informação de todo o catálogo (**P(ruído) = 0,976**,
    `ESTUDO_MARGEM_20PP.md` §2.3).

    Se a lei, a constante, o piso, a métrica de lift ou a escolha de `n`
    mudarem, é aqui que o catálogo inteiro reclama.
    """
    estados = {slug: E.contraste(E.lifts(E.frequencias(cls)),
                                 n=E.n_efetivo(E.frequencias(cls)))
               for slug, cls in catalogo.items()}
    tematicos = sorted(s for s, e in estados.items() if e == "tematico")
    valorativos = [s for s, e in estados.items() if e == "valorativo"]
    sem_estado = sorted(s for s, e in estados.items() if e is None)

    assert (len(tematicos), len(valorativos), len(sem_estado)) == (6, 28, 1)
    assert tematicos == ["anatomy-of-a-fall", "barbie", "cats-2019", "cure",
                         "oppenheimer-2023", "the-substance"]
    assert sem_estado == ["obsession-2026"]


def test_os_6_filmes_que_publicavam_causa_sem_lastro_saem_de_tematico(catalogo):
    """[v1.9.34] Os 6 de `ESTABILIDADE_10_FLIPS.md` cujo veredito NOMEIA por
    extenso a causa que separa os grupos, e cujo contraste tinha **63% de
    probabilidade média de ser ruído** na amostra em que foram decididos
    (`ESTUDO_MARGEM_20PP.md` §2.3). É o dano concreto que motivou a versão;
    esta asserção existe para que nenhum deles volte sem alguém notar."""
    for slug in ("bones-and-all", "everything-everywhere-all-at-once",
                 "hereditary", "napoleon-2023", "perfect-days-2023",
                 "spider-man-across-the-spider-verse"):
        freqs = E.frequencias(catalogo[slug])
        assert E.contraste(E.lifts(freqs), n=E.n_efetivo(freqs)) == "valorativo"


def test_estado_dos_3_filmes_publicados(catalogo):
    # [v1.9.34] `the-invite-2026` era `tematico` sob a margem fixa de 20pp
    # (lift dominante 22,5pp) e passa a `valorativo`: com n=40 o limiar é
    # 22,83pp, e o corte operante na grade de 2,5pp é 25pp. Ele estava a um
    # quantum da fronteira antiga — p-valor 0,1015 no nulo do máximo, ou seja
    # ~1 chance em 10 de o contraste dele ser sorteio.
    esperado = {"cure": "tematico", "the-invite-2026": "valorativo",
                "cidade-de-deus": "valorativo"}
    for slug, estado in esperado.items():
        assert E.contraste(E.lifts(E.frequencias(catalogo[slug])),
                            n=E.n_efetivo(E.frequencias(catalogo[slug]))) == estado


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
