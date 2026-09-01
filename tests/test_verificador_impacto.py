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
    """A projeção aplica a MESMA lei que a produção, em `Fraction`.

    [v1.9.34] Era 20,0pp fixo; virou `limiar(n) = 144,4/√n` (§2.5), e
    `_atinge` ganhou `n`. O que o teste protege não mudou: a comparação é
    exata e o script não tem régua própria. A fronteira exata usada aqui é a
    de n=100 (`144,4/√100 = 14,44pp`), a única racional — com n quadrado
    perfeito a lei tem um ponto de igualdade que se pode escrever.
    """
    from fractions import Fraction
    assert vi._atinge(Fraction(1444, 10000), 100)              # na fronteira
    assert not vi._atinge(Fraction(1444, 10000) - Fraction(1, 10 ** 9), 100)
    # e o MESMO lift decide diferente conforme `n` — a mudança da versão
    assert vi._atinge(Fraction(1, 5), 60) and not vi._atinge(Fraction(1, 5), 40)


def test_base_da_projecao_reproduz_10_de_35(vi, corpus):
    """Era 18/35 sob a cobertura parcial de 2.866/4.056 que vigorava desde a
    v1.9.15. **NÃO é o número de produção** (esse é 16/35, ver
    `tests/test_eixos.py::test_catalogo_reproduz_16_tematicos_e_19_valorativos`)
    — é o número que `_cobertura_exata`/`_corpus_consenso` DEVOLVEM, porque
    estas duas funções, ao contrário de `eixos.montar_bloco`, NÃO chamam
    `_filtrar_pela_analisada`. `_corpus_consenso()` lê `consenso.jsonl` cru e
    conta toda review classificada para aquele bucket, mesmo a que não está
    na seleção de produção atual — o mesmo "dois quarentas" que a v1.9.15
    corrigiu em `montar_bloco`, nunca replicado aqui porque este script é
    ferramenta de PROJEÇÃO (usada durante a investigação da saturação de
    `impacto_emocional`), não parte do caminho de renderização.

    **Achado desta sessão** (extensão de cobertura,
    `RELATORIO_GABARITO_E_COBERTURA.md`): a lacuna era invisível com 9 de 105
    buckets acumulados; com a extensão aos 35 filmes ela passou a 93 de 105,
    e `_cobertura_exata` sobre `consenso.jsonl` cru diverge do número real de
    produção em 6 filmes (10 contra 16). **Fica registrado como limitação
    conhecida, não corrigido nesta sessão** (fora do escopo autorizado —
    `verificador_impacto.py` não foi tocado). Se `_cobertura_exata` for usada
    de novo para decidir alguma coisa sobre o catálogo real, aplicar
    `eixos._filtrar_pela_analisada` antes é pré-requisito.

    [v1.9.34] Passou de 10 para **11** sob a lei por `n`, e a direção é
    contraintuitiva: um limiar MAIOR (22,83pp em n=40 contra 20pp) devolvendo
    MAIS filmes com contraste. A causa é a mesma lacuna que este docstring já
    descreve — `_corpus_consenso()` lê `consenso.jsonl` CRU e acumula reviews
    de seleções antigas, então os buckets aqui têm n MAIOR que 40 (até 68), e
    `limiar(n)` CAI com n. Não é a lei se comportando mal: é esta função
    medindo uma população que a produção não usa, o que a limitação registrada
    abaixo já dizia. O número de produção é 6 (`tests/test_eixos.py`).

    `obsession-2026` sai da conta por baixo: com n=5 no menor bucket ele fica
    abaixo do piso e `contraste` devolve `None` — nem `tematico` nem
    `valorativo`.
    """
    base = vi._cobertura_exata(corpus)
    assert base["n_filmes_com_algum"] == 11
    assert base["n_filmes"] == 35
    assert base["contraste"]["obsession-2026"] is None


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


# ================================================ v1.9.16 relatório real (E2)
# `relatorio_aplicacao` compara consenso CRU x VERIFICADO por filme/bucket —
# a base do relatório medido (não projetado) da Entrega 2.


def _linha(slug, bucket, rid, eixos):
    return {"slug": slug, "bucket": bucket, "id": rid, "eixos": eixos}


def test_relatorio_aplicacao_conta_remocoes_por_filme_e_bucket(vi):
    cru = ([_linha("a", "negativas", f"n{i}",
                   ["impacto_emocional", "ritmo"] if i < 5 else ["ritmo"])
           for i in range(10)]
          + [_linha("a", "positivas", f"p{i}", ["impacto_emocional"])
             for i in range(4)])
    ver = ([_linha("a", "negativas", f"n{i}",
                   ["ritmo"] if i < 5 else ["ritmo"])  # as 5 primeiras: removidas
           for i in range(10)]
          + [_linha("a", "positivas", f"p{i}", ["impacto_emocional"] if i < 2 else [])
             for i in range(4)])  # 2 removidas

    rel = vi.relatorio_aplicacao(cru, ver)
    d = rel["por_filme"]["a"]
    assert d["removidas"] == 7
    assert d["removidas_por_bucket"] == {"negativas": 5, "positivas": 2}


def test_relatorio_aplicacao_detecta_mudanca_de_veredito(vi):
    """Filme sintético: `impacto_emocional` é o ÚNICO eixo acima da margem
    (tematico); removê-lo por completo em todos os buckets derruba pra
    valorativo — cenário construído para travar a detecção, não medido."""
    cru = ([_linha("b", "negativas", f"n{i}", ["impacto_emocional"])
           for i in range(20)]
          + [_linha("b", "negativas", f"n{i}", []) for i in range(20, 40)]
          + [_linha("b", "positivas", f"p{i}", []) for i in range(40)])
    ver = ([_linha("b", "negativas", f"n{i}", []) for i in range(40)]
          + [_linha("b", "positivas", f"p{i}", []) for i in range(40)])

    rel = vi.relatorio_aplicacao(cru, ver)
    d = rel["por_filme"]["b"]
    assert d["contraste_antes"] == "tematico"
    assert d["contraste_depois"] == "valorativo"
    assert d["veredito_mudou"] is True
    assert rel["vereditos_mudaram"] == ["b"]


def test_relatorio_aplicacao_agrega_cobertura(vi):
    cru = [_linha("a", "negativas", "n0", ["impacto_emocional"]),
          _linha("a", "positivas", "p0", [])]
    ver = [_linha("a", "negativas", "n0", []),
          _linha("a", "positivas", "p0", [])]
    rel = vi.relatorio_aplicacao(cru, ver)
    assert rel["n_filmes"] == 1
    assert rel["total_removidas"] == 1
    assert rel["cobertura_antes"] in (0, 1)
    assert rel["cobertura_depois"] in (0, 1)
