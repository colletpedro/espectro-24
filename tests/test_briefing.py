"""Briefing determinístico (§D2, v1.9.8) — o código decide, o narrador verbaliza.

O que estes testes travam é a fronteira: TUDO que o briefing entrega já é
decisão tomada. Se uma dessas decisões voltar a ser instrução no prompt, o
narrador volta a poder escolher tema, ordem ou número — que é exatamente o
que a v1.9.8 tira dele.

Os testes vêm ANTES do módulo, na ordem de execução pedida para a sessão.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import briefing as br  # noqa: E402


# --------------------------------------------------------------- fixtures

def _tema(nome, mencoes, n, exemplo="ex"):
    return {"tema": nome, "mencoes_aproximadas": mencoes,
            "n_reviews_analisadas": n, "exemplo_parafraseado": exemplo}


def _bucket(nome, n, temas, modo="completo", estado="completa", obs="obs"):
    return {"bucket": nome, "n_validas": n, "modo": modo,
            "estado_piso": estado, "observacao_geral": obs, "temas": temas}


def _output(**kw):
    base = {
        "total_reviews_observadas": 1000,
        "buckets": [
            _bucket("negativas", 40, [_tema("ritmo lento", 30, 40),
                                      _tema("final fraco", 10, 40),
                                      _tema("som ruim", 4, 40)]),
            _bucket("medianas", 40, [_tema("irregular", 20, 40)]),
            _bucket("positivas", 40, [_tema("atmosfera", 36, 40),
                                      _tema("fotografia", 18, 40)]),
        ],
        "distribuicao": {"n_notas_total": 10000,
                         "por_bucket": {"negativas": 3, "medianas": 17,
                                        "positivas": 80}},
    }
    base.update(kw)
    return base


# ------------------------------------------------- ordem do movimento 3

def test_ordem_do_movimento3_abre_pelo_bucket_dominante():
    """Era a instrução 'o MOVIMENTO 3 começa pela perspectiva de MAIOR peso'.
    Agora é lista pronta — o narrador não decide ordem."""
    b = br.montar_briefing(_output())
    assert b["movimento3"]["ordem"][0] == "positivas"     # 80%
    assert b["movimento3"]["ordem"] == ["positivas", "medianas", "negativas"]


def test_ordem_e_estavel_com_empate():
    """Empate resolve pela ordem canônica dos buckets, não por sorte de
    iteração — dois filmes com o mesmo perfil têm de dar a mesma ordem."""
    out = _output(distribuicao={"n_notas_total": 100,
                                "por_bucket": {"negativas": 33,
                                               "medianas": 33,
                                               "positivas": 33}})
    a = br.montar_briefing(out)["movimento3"]["ordem"]
    b = br.montar_briefing(out)["movimento3"]["ordem"]
    assert a == b


def test_sem_distribuicao_a_ordem_e_a_canonica():
    out = _output(distribuicao=None)
    b = br.montar_briefing(out)
    assert b["movimento3"]["ordem"] == ["negativas", "medianas", "positivas"]
    assert b["distribuicao"]["disponivel"] is False


# ------------------------------------------------------- seleção de temas

def test_temas_vem_ordenados_por_frequencia_decrescente():
    b = br.montar_briefing(_output())
    neg = b["grupos"]["negativas"]["temas"]
    assert [t["tema"] for t in neg] == ["ritmo lento", "final fraco", "som ruim"]


def test_temas_sao_cortados_no_teto_do_movimento3():
    """A instrução era 'priorize os 2-3 temas MAIS FORTES'. Vira corte em
    código: o narrador recebe só os que deve usar."""
    out = _output()
    out["buckets"][0]["temas"] = [_tema(f"t{i}", 40 - i, 40) for i in range(8)]
    b = br.montar_briefing(out, max_temas_por_grupo=3)
    assert len(b["grupos"]["negativas"]["temas"]) == 3
    assert [t["tema"] for t in b["grupos"]["negativas"]["temas"]] == ["t0", "t1", "t2"]


def test_temas_cortados_sao_reportados_nao_sumidos():
    """Truncar em silêncio esconderia do leitor do briefing que houve corte."""
    out = _output()
    out["buckets"][0]["temas"] = [_tema(f"t{i}", 40 - i, 40) for i in range(8)]
    b = br.montar_briefing(out, max_temas_por_grupo=3)
    assert b["grupos"]["negativas"]["temas_omitidos"] == 5


# ------------------------------------------------- quantificador e peso

def test_cada_tema_carrega_quantificador_precomputado():
    b = br.montar_briefing(_output())
    t = b["grupos"]["negativas"]["temas"][0]      # 30/40 = 75%
    assert t["fracao_pct"] == 75
    assert t["quantificador"] == "a maioria"


def test_rotulo_de_peso_vem_pronto_com_percentual():
    b = br.montar_briefing(_output())
    assert b["grupos"]["positivas"]["rotulo_peso"] == "a grande maioria das notas (~80%)"


def test_marcacao_de_perspectiva_vem_por_grupo():
    b = br.montar_briefing(_output())
    for nome in ("negativas", "medianas", "positivas"):
        assert b["grupos"][nome]["marcacao_perspectiva"] in (
            "nenhuma", "simples", "antecipada")


# ------------------------------------------- estado do piso vira PERMISSÃO

def test_estado_piso_vira_permissao_explicita():
    """O narrador não deve ter de inferir de `modo=sem_analise` o que pode
    dizer — o briefing diz."""
    out = _output()
    out["buckets"][0]["estado_piso"] = "sem_numero"
    b = br.montar_briefing(out)
    p = b["grupos"]["negativas"]["permissoes"]
    assert p["pode_citar_temas"] is True
    assert p["pode_citar_numero"] is False
    assert p["pode_citar_quantificador"] is False


def test_estado_piso_ausente_e_derivado_de_n_validas():
    """Regressão de um defeito real, pego em `cure`: `estado_piso` não está
    serializado nos `resultado/*.json` publicados antes da v1.9.0, e um
    default para `sem_analise` apagava 6 temas de um bucket de 50 reviews.
    O estado é FUNÇÃO de n_validas — recomputar é exato."""
    out = _output()
    for b in out["buckets"]:
        b.pop("estado_piso")
    b = br.montar_briefing(out)
    assert b["grupos"]["negativas"]["estado_piso"] == "completa"
    assert b["grupos"]["negativas"]["temas"]            # não sumiram


def test_estado_piso_derivado_respeita_os_limiares():
    out = _output()
    out["buckets"][0].pop("estado_piso")
    out["buckets"][0]["n_validas"] = 10        # entre 8 e 15
    assert (br.montar_briefing(out)["grupos"]["negativas"]["estado_piso"]
            == "sem_quantificador")
    out["buckets"][0]["n_validas"] = 1         # abaixo de 3
    assert (br.montar_briefing(out)["grupos"]["negativas"]["estado_piso"]
            == "sem_analise")


def test_estado_piso_declarado_tem_precedencia_sobre_o_derivado():
    out = _output()
    out["buckets"][0]["estado_piso"] = "sem_numero"   # n=40 daria "completa"
    assert (br.montar_briefing(out)["grupos"]["negativas"]["estado_piso"]
            == "sem_numero")


def test_permissao_completa_libera_tudo():
    b = br.montar_briefing(_output())
    p = b["grupos"]["negativas"]["permissoes"]
    assert p == {"pode_citar_temas": True, "pode_citar_numero": True,
                 "pode_citar_quantificador": True}


def test_sem_analise_nao_libera_tema_nenhum():
    out = _output()
    out["buckets"][1]["estado_piso"] = "sem_analise"
    b = br.montar_briefing(out)
    p = b["grupos"]["medianas"]["permissoes"]
    assert p["pode_citar_temas"] is False
    assert b["grupos"]["medianas"]["temas"] == []


def test_sem_quantificador_permite_numero_mas_nao_rotulo_verbal():
    out = _output()
    out["buckets"][2]["estado_piso"] = "sem_quantificador"
    b = br.montar_briefing(out)
    p = b["grupos"]["positivas"]["permissoes"]
    assert p["pode_citar_numero"] is True
    assert p["pode_citar_quantificador"] is False


def test_tema_sem_permissao_de_quantificador_nao_carrega_o_rotulo():
    """Se a permissão diz não, o campo não pode estar lá para ser copiado."""
    out = _output()
    out["buckets"][0]["estado_piso"] = "sem_quantificador"
    b = br.montar_briefing(out)
    assert "quantificador" not in b["grupos"]["negativas"]["temas"][0]


# --------------------------------------------------- orçamento de frases

def test_orcamento_de_frases_por_movimento():
    b = br.montar_briefing(_output())
    o = b["orcamento_frases"]
    assert o["movimento1"][1] >= o["movimento1"][0] >= 0
    assert o["movimento3"][0] >= 1


def test_sem_ficha_o_movimento1_tem_orcamento_zero():
    """Era a instrução 'só escreva se houver FICHA'. Vira número."""
    b = br.montar_briefing(_output(ficha=None))
    assert b["orcamento_frases"]["movimento1"] == (0, 0)
    assert b["ficha"] is None


def test_com_ficha_o_movimento1_tem_orcamento_positivo():
    b = br.montar_briefing(_output(ficha={"titulo": "X", "ano": 2020,
                                          "diretor": "D", "generos": ["drama"],
                                          "duracao_min": 100,
                                          "sinopse_oficial": "S"}))
    assert b["orcamento_frases"]["movimento1"][1] > 0


# ------------------------------------------------------------- serialização

def test_serializar_nao_vaza_review_bruta():
    """A fronteira de §D2 que existe desde a v1.2.0: nunca reviews brutas."""
    out = _output()
    out["buckets"][0]["reviews_analisadas"] = ["texto secreto de review"]
    txt = br.serializar_briefing(br.montar_briefing(out))
    assert "texto secreto" not in txt


def test_serializar_lista_a_ordem_do_movimento3():
    txt = br.serializar_briefing(br.montar_briefing(_output()))
    assert "positivas" in txt
    assert "ORDEM" in txt.upper()


def test_serializar_e_deterministico():
    out = _output()
    assert (br.serializar_briefing(br.montar_briefing(out))
            == br.serializar_briefing(br.montar_briefing(out)))


def test_serializar_marca_o_que_o_grupo_nao_pode_receber():
    out = _output()
    out["buckets"][1]["estado_piso"] = "sem_analise"
    txt = br.serializar_briefing(br.montar_briefing(out))
    assert "medianas" in txt.lower()


# ------------------------------------------------ invariantes que migraram

def test_prompt_novo_nao_repete_as_invariantes_computaveis():
    """A medida de sucesso da Entrega 1: o prompt do narrador determinístico
    NÃO contém mais as regras que viraram dado no briefing."""
    p = br.PROMPT_NARRADOR_BRIEFING
    # ordem do movimento 3 — agora é lista no briefing
    assert "começa pela perspectiva de MAIOR peso" not in p
    # escolha de tema — agora é corte em código
    assert "priorize os 2-3 temas" not in p
    # cálculo de quantificador — já era pré-computado, some da prosa também
    assert "Escala de força" not in p


def test_prompt_novo_mantem_as_invariantes_nao_computaveis():
    """O que o código não pode decidir sem escrever a frase continua no
    prompt — e some daqui seria regressão de honestidade, não simplificação."""
    p = br.PROMPT_NARRADOR_BRIEFING
    baixo = p.lower()
    assert "spoiler" in baixo
    assert "das notas" in p               # vocabulário notas != reviews
    for termo in ("minoria", "proibido", "fidelidade", "neutro"):
        assert termo in baixo


def test_prompt_novo_pede_json_com_a_narrativa():
    assert '"narrativa"' in br.PROMPT_NARRADOR_BRIEFING


def test_invariantes_migradas_e_uma_contagem_declarada():
    """O número que a entrega reporta não pode ser prosa solta — é dado."""
    assert isinstance(br.INVARIANTES_MIGRADAS, tuple)
    assert isinstance(br.INVARIANTES_REMANESCENTES, tuple)
    assert len(br.INVARIANTES_MIGRADAS) >= 6
    total = len(br.INVARIANTES_MIGRADAS) + len(br.INVARIANTES_REMANESCENTES)
    assert total >= 15


# ------------------------------------------------- extração da narrativa

def test_extrai_json_bem_formado():
    assert br.extrair_narrativa('{"narrativa": "Um texto."}') == "Um texto."


def test_extrai_com_quebra_de_linha_escapada():
    assert br.extrair_narrativa(r'{"narrativa": "A\nB"}') == "A\nB"


def test_extrai_com_quebra_de_linha_CRUA_dentro_da_string():
    """Regressão do defeito real de `cidade-de-deus`: o DeepSeek escapa a
    quebra de linha de forma inconsistente na MESMA resposta, e json.loads
    recusa o texto inteiro — que está perfeitamente bom."""
    bruto = '{"narrativa": "Primeiro parágrafo.\nSegundo parágrafo."}'
    assert br.extrair_narrativa(bruto) == "Primeiro parágrafo.\nSegundo parágrafo."


def test_extrai_com_escape_misturado():
    bruto = '{"narrativa": "A\\nB\nC"}'
    assert br.extrair_narrativa(bruto) == "A\nB\nC"


def test_extrai_removendo_cerca_de_codigo():
    assert br.extrair_narrativa('```json\n{"narrativa": "X"}\n```') == "X"


def test_extrai_preserva_aspas_escapadas():
    assert br.extrair_narrativa(r'{"narrativa": "diz \"oi\" aqui"}') == 'diz "oi" aqui'


def test_extrai_devolve_vazio_quando_nada_funciona():
    """Prosa meio parseada e não percebida é pior que falha explícita."""
    assert br.extrair_narrativa("isto não é json nem tem o campo") == ""
    assert br.extrair_narrativa("") == ""


def test_extrai_vazio_quando_o_campo_nao_existe():
    assert br.extrair_narrativa('{"outra_coisa": "X"}') == ""


# ------------------------------------------------------------------ bordas

def test_bucket_ausente_do_output_nao_quebra():
    out = _output()
    out["buckets"] = [out["buckets"][0]]
    b = br.montar_briefing(out)
    assert set(b["grupos"]) == {"negativas"}
    assert b["movimento3"]["ordem"] == ["negativas"]


def test_tema_com_denominador_zero_nao_divide_por_zero():
    out = _output()
    out["buckets"][0]["temas"] = [_tema("x", 0, 0)]
    b = br.montar_briefing(out)
    assert b["grupos"]["negativas"]["temas"][0]["fracao_pct"] == 0


def test_output_vazio_devolve_briefing_vazio_sem_erro():
    b = br.montar_briefing({"buckets": []})
    assert b["grupos"] == {}
    assert b["movimento3"]["ordem"] == []
