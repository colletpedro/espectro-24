"""Invariantes do passe de verificação de `impacto_emocional`.

O passe roda DEPOIS do consenso e só pode REMOVER marcações — é essa
assimetria que define o critério de sucesso (precisão sobe, recall só pode
cair) e ela precisa ser estrutural, não uma promessa da prosa do prompt.
Estes testes travam isso, mais o comportamento nas bordas de parsing (onde
a política é conservadora: na dúvida, não mexe na classificação original).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


@pytest.fixture(scope="module")
def vi():
    import verificador_impacto
    return verificador_impacto


# ------------------------------------------------------- parsing do veredito

@pytest.mark.parametrize("bruto,esperado", [
    (True, True), (False, False),
    ("true", True), ("false", False),
    ("False", False), ("nao", False), ("não", False), ("no", False), ("0", False),
    ("sim", True), ("yes", True),
])
def test_confirma_tolera_bool_e_string(vi, bruto, esperado):
    confirma, _, _ = vi._normalizar_veredito({"confirma": bruto})
    assert confirma is esperado


def test_confirma_ausente_e_conservador_nao_remove(vi):
    """Falha de parsing NÃO pode remover — um verificador que apaga marcação
    por JSON malformado seria pior que não ter verificador."""
    confirma, _, _ = vi._normalizar_veredito({"frase": "algo"})
    assert confirma is True


def test_frase_e_alvo_sao_extraidos(vi):
    _, frase, alvo = vi._normalizar_veredito(
        {"confirma": False, "frase": "  não gostei  ", "alvo": "Filme"})
    assert frase == "não gostei"
    assert alvo == "filme"


def test_alvo_ausente_vira_none(vi):
    """V1 não pede `alvo`; o campo é opcional por desenho."""
    _, _, alvo = vi._normalizar_veredito({"confirma": True})
    assert alvo is None


# ----------------------------------------------------------------- aplicar()

def _consenso(**por_id):
    return {rid: {"eixos": list(eixos), "confianca": "maioria"}
            for rid, eixos in por_id.items()}


def test_aplicar_so_remove_nunca_acrescenta(vi):
    base = _consenso(a=["ritmo"], b=["impacto_emocional", "ritmo"])
    # veredito manda "confirmar" em a (que nem tem o eixo) e remover em b
    saida = vi.aplicar(base, {"a": True, "b": False})
    assert saida["a"]["eixos"] == ["ritmo"]           # inalterada
    assert saida["b"]["eixos"] == ["ritmo"]           # só o eixo saiu


def test_aplicar_nao_toca_outros_eixos(vi):
    base = _consenso(a=["atuacao", "impacto_emocional", "som_trilha", "livre"])
    saida = vi.aplicar(base, {"a": False})
    assert saida["a"]["eixos"] == ["atuacao", "som_trilha", "livre"]


def test_aplicar_preserva_campos_do_consenso(vi):
    base = {"a": {"eixos": ["impacto_emocional"], "confianca": "unanime",
                  "votos": {"impacto_emocional": 3}}}
    saida = vi.aplicar(base, {"a": False})
    assert saida["a"]["confianca"] == "unanime"
    assert saida["a"]["votos"] == {"impacto_emocional": 3}


def test_review_sem_veredito_fica_intacta(vi):
    """Review que o passe não visitou (o eixo não estava marcado) não muda."""
    base = _consenso(a=["impacto_emocional"], b=["ritmo"])
    saida = vi.aplicar(base, {})            # nenhum veredito
    assert saida["a"]["eixos"] == ["impacto_emocional"]
    assert saida["b"]["eixos"] == ["ritmo"]


def test_confirmar_mantem_a_marcacao(vi):
    base = _consenso(a=["impacto_emocional"])
    assert vi.aplicar(base, {"a": True})["a"]["eixos"] == ["impacto_emocional"]


# ------------------------------------------------------- consenso de 3 votos

def test_consenso3_e_maioria_de_2_de_3(vi, monkeypatch):
    passes = {
        1: {"x": {"confirma": True}, "y": {"confirma": False}, "z": {"confirma": True}},
        2: {"x": {"confirma": True}, "y": {"confirma": True}, "z": {"confirma": False}},
        3: {"x": {"confirma": False}, "y": {"confirma": False}, "z": {"confirma": False}},
    }
    monkeypatch.setattr(vi, "_ler", lambda variante, n: passes[n])
    v = vi.vereditos("V2_alvo", "consenso3")
    assert v["x"] is True      # 2 de 3 confirmam
    assert v["y"] is False     # 2 de 3 removem
    assert v["z"] is False     # 1 de 3 confirma


def test_passe1_usa_so_a_primeira_passada(vi, monkeypatch):
    passes = {1: {"x": {"confirma": False}},
              2: {"x": {"confirma": True}},
              3: {"x": {"confirma": True}}}
    monkeypatch.setattr(vi, "_ler", lambda variante, n: passes[n])
    assert vi.vereditos("V2_alvo", "passe1")["x"] is False


# ------------------------------------------------------------------- prompts

@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_e_curto_e_sobre_uma_decisao(vi, nome):
    """O passe existe porque verificar é pergunta MAIS FÁCIL que classificar.
    Reapresentar a taxonomia recriaria a tarefa difícil."""
    p = vi.VARIANTES[nome]
    assert len(p) < 2000
    for eixo in ("roteiro_estrutura", "tom_atmosfera", "comparacoes",
                 "direcao_imagem", "som_trilha"):
        assert f"- {eixo}:" not in p       # nenhuma definição de eixo inteira


@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_trata_os_dois_polos(vi, nome):
    """A assimetria positivo/negativo foi o defeito original — o prompt do
    verificador tem de barrar veredicto nos DOIS polos."""
    p = vi.VARIANTES[nome]
    assert "não gostei" in p and "amei" in p


@pytest.mark.parametrize("nome", ["V1_regua", "V2_alvo"])
def test_prompt_pede_a_frase_justificadora(vi, nome):
    """Telemetria declarada: é o que permite auditar o verificador depois."""
    assert '"frase"' in vi.VARIANTES[nome]


def test_apenas_v2_pede_o_alvo(vi):
    """A diferença estrutural entre as variantes: V2 força o compromisso
    com o ALVO antes do veredito."""
    assert '"alvo"' not in vi.SYSTEM_V1_REGUA
    assert '"alvo"' in vi.SYSTEM_V2_ALVO


def test_o_eixo_verificado_e_apenas_impacto_emocional(vi):
    assert vi.EIXO == "impacto_emocional"


# ============================================================ projeção exata
# [2026-08-22] A projeção de lift da Entrega 4 foi medida ANTES da correção
# de margem da v1.9.15 e herdou os dois defeitos que aquela versão consertou:
# comparação `>=` em float (o mesmo `0.2 >= 0.2` falso em binário) e um único
# sorteio de um modelo estocástico. Estes testes travam a versão corrigida
# contra a fonte de verdade do caminho de produção.


@pytest.fixture(scope="module")
def corpus(vi):
    return vi._corpus_consenso()


def test_projecao_usa_a_margem_exata_e_nao_float(vi):
    """O bug de v1.9.14/float: 20,0pp EXATOS atingem a margem mínima.

    Se a projeção voltar a comparar em float, este caso — 8/40 contra 0/40,
    exatamente 20,0pp — deixa de contar e o teste cai.
    """
    from fractions import Fraction
    assert vi._atinge(Fraction(8, 40) - Fraction(0, 40))
    assert not vi._atinge(Fraction(199, 1000))


def test_base_da_projecao_reproduz_18_de_35(vi, corpus):
    """A base correta é 18/35, não os 13/35 que a projeção antiga usava.

    Este é o número que a v1.9.15 estabeleceu sob `>=` exato, e é a régua
    contra a qual qualquer ganho projetado tem de ser lido.
    """
    base = vi._cobertura_exata(corpus)
    assert base["n_filmes_com_algum"] == 18
    assert base["n_filmes"] == 35


def test_base_da_projecao_reproduz_o_contraste_publicado(vi, corpus):
    """Fator 1,0 (nenhuma remoção) tem de devolver o estado que está no ar."""
    base = vi._cobertura_exata(corpus)
    assert base["contraste"]["cure"] == "tematico"
    assert base["contraste"]["cidade-de-deus"] == "valorativo"
    assert base["contraste"]["the-invite-2026"] == "tematico"


def test_projecao_so_remove_nunca_acrescenta(vi, corpus):
    """A assimetria do verificador tem de sobreviver à projeção."""
    sorteado = vi._sortear_remocoes(corpus, 0.5, semente=1)
    for antes, depois in zip(corpus, sorteado):
        assert set(depois["eixos"]) <= set(antes["eixos"])
        assert set(antes["eixos"]) - set(depois["eixos"]) <= {vi.EIXO}


def test_projecao_e_deterministica_por_semente(vi, corpus):
    a = vi._sortear_remocoes(corpus, 0.5, semente=7)
    b = vi._sortear_remocoes(corpus, 0.5, semente=7)
    c = vi._sortear_remocoes(corpus, 0.5, semente=8)
    assert [r["eixos"] for r in a] == [r["eixos"] for r in b]
    assert [r["eixos"] for r in a] != [r["eixos"] for r in c]


def test_fator_1_nao_remove_nada(vi, corpus):
    igual = vi._sortear_remocoes(corpus, 1.0, semente=3)
    assert [r["eixos"] for r in igual] == [list(r["eixos"]) for r in corpus]


# ================================================== v1.9.16 aplicação real
# `gerar_consenso_verificado` é o transform PURO que produz
# `consenso_verificado.jsonl` a partir do `consenso.jsonl` de produção e dos
# vereditos do passe — sem rede, sem I/O, testável direto.


def test_gerar_consenso_verificado_so_remove_o_eixo_alvo(vi):
    linhas = [
        {"slug": "x", "bucket": "negativas", "id": "a",
         "eixos": ["impacto_emocional", "ritmo"]},
        {"slug": "x", "bucket": "negativas", "id": "b",
         "eixos": ["impacto_emocional"]},
    ]
    vereditos_ = {"a": False, "b": True}
    saida = vi.gerar_consenso_verificado(linhas, vereditos_)
    por_id = {r["id"]: r for r in saida}
    assert por_id["a"]["eixos"] == ["ritmo"]          # removeu SÓ o eixo alvo
    assert por_id["b"]["eixos"] == ["impacto_emocional"]  # confirmado, intacto


def test_gerar_consenso_verificado_ignora_outros_eixos(vi):
    """Nunca mexe em linha sem `impacto_emocional`, mesmo com veredito."""
    linhas = [{"slug": "x", "bucket": "negativas", "id": "c", "eixos": ["ritmo"]}]
    saida = vi.gerar_consenso_verificado(linhas, {"c": False})
    assert saida[0]["eixos"] == ["ritmo"]


def test_gerar_consenso_verificado_sem_veredito_fica_intacto(vi):
    """Review candidata cuja chamada falhou (sem entrada no dict de
    vereditos) não pode perder a marcação — política conservadora, mesma do
    parsing (`_normalizar_veredito`)."""
    linhas = [{"slug": "x", "bucket": "negativas", "id": "d",
              "eixos": ["impacto_emocional"]}]
    saida = vi.gerar_consenso_verificado(linhas, {})
    assert saida[0]["eixos"] == ["impacto_emocional"]


def test_gerar_consenso_verificado_preserva_campos_da_linha(vi):
    """`votos`, `eixos_por_passe` e qualquer outro campo sobrevivem
    intactos — o transform só toca `eixos`."""
    linhas = [{"slug": "x", "bucket": "negativas", "id": "e",
              "eixos": ["impacto_emocional"], "votos": {"impacto_emocional": 3},
              "eixos_por_passe": [["impacto_emocional"]] * 3, "nivel": 1.5}]
    saida = vi.gerar_consenso_verificado(linhas, {"e": False})
    assert saida[0]["votos"] == {"impacto_emocional": 3}
    assert saida[0]["eixos_por_passe"] == [["impacto_emocional"]] * 3
    assert saida[0]["nivel"] == 1.5


def test_gerar_consenso_verificado_preserva_a_ordem_e_o_total(vi):
    linhas = [{"slug": "x", "bucket": "negativas", "id": str(i),
              "eixos": ["impacto_emocional"] if i % 2 else ["ritmo"]}
             for i in range(10)]
    saida = vi.gerar_consenso_verificado(linhas, {})
    assert [r["id"] for r in saida] == [r["id"] for r in linhas]
    assert len(saida) == 10


def test_gerar_consenso_verificado_so_pode_reduzir_o_total_de_eixos(vi):
    """A assimetria estrutural (§ Entrega 1) travada no caminho de produção:
    para toda review, o conjunto de eixos depois é subconjunto do de antes,
    e a única diferença possível é `impacto_emocional`."""
    import random
    rng = random.Random(42)
    todos = ["impacto_emocional", "ritmo", "roteiro_estrutura", "livre"]
    linhas = [{"slug": "x", "bucket": "negativas", "id": str(i),
              "eixos": rng.sample(todos, k=rng.randint(0, len(todos)))}
             for i in range(50)]
    vereditos_ = {str(i): rng.choice([True, False, None]) for i in range(50)}
    vereditos_ = {k: v for k, v in vereditos_.items() if v is not None}

    saida = vi.gerar_consenso_verificado(linhas, vereditos_)
    for antes, depois in zip(linhas, saida):
        assert set(depois["eixos"]) <= set(antes["eixos"])
        assert set(antes["eixos"]) - set(depois["eixos"]) <= {vi.EIXO}
