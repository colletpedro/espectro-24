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


# ============================================================ v1.9.9
# Entrega 1 — o tique do quantificador: FAIXA (código) × CONSTRUÇÃO (modelo)
# ============================================================

def test_toda_faixa_tem_conjunto_de_construcoes():
    """A faixa continua sendo decisão do CÓDIGO; o que o modelo ganha é a
    escolha da palavra dentro da faixa que o código fixou."""
    for faixa, construcoes in br.FAIXAS_QUANTIFICADOR.items():
        assert len(construcoes) >= 3, faixa
        assert construcoes[0] == faixa, "a construção canônica abre a lista"


def test_conjuntos_de_faixas_sao_DISJUNTOS():
    """A invariante crítica: nenhuma construção pode pertencer a duas
    faixas. Se pertencesse, a checagem de pertencimento não decidiria nada
    e a faixa deixaria de ser verdade sobre o dado."""
    vistas: dict[str, str] = {}
    for faixa, construcoes in br.FAIXAS_QUANTIFICADOR.items():
        for c in construcoes:
            assert c not in vistas, f"{c!r} em {faixa} e em {vistas.get(c)}"
            vistas[c] = faixa


def test_nenhuma_construcao_e_substring_de_outra_faixa():
    """'cerca de metade' não pode estar contida numa construção de 'quase
    todos' — a detecção é textual, e substring cruzada faria a faixa errada
    casar."""
    for faixa_a, cons_a in br.FAIXAS_QUANTIFICADOR.items():
        for faixa_b, cons_b in br.FAIXAS_QUANTIFICADOR.items():
            if faixa_a == faixa_b:
                continue
            for a in cons_a:
                for b in cons_b:
                    assert a not in b, f"{a!r} ({faixa_a}) dentro de {b!r} ({faixa_b})"


@pytest.mark.parametrize("pct,faixa", [
    (0, "poucos"), (9, "poucos"), (10, "alguns"), (25, "alguns"),
    (26, "muitos"), (40, "muitos"), (50, "muitos"),
    (55, "cerca de metade"), (60, "cerca de metade"),
    (70, "a maioria"), (80, "a maioria"), (90, "quase todos"), (100, "quase todos"),
])
def test_faixa_resolve_nas_mesmas_bordas_da_v123(pct, faixa):
    """A escala não muda — só o que se entrega dela. Regressão contra
    afrouxar a calibração por acidente ao introduzir os conjuntos."""
    assert br.faixa_quantificador(pct) == faixa


def test_tema_carrega_faixa_e_construcoes_em_vez_de_string_unica():
    b = br.montar_briefing(_output())
    t = b["grupos"]["negativas"]["temas"][0]          # 30/40 = 75%
    assert t["faixa"] == "a maioria"
    assert t["quantificadores"] == list(br.FAIXAS_QUANTIFICADOR["a maioria"])
    assert t["quantificador"] == "a maioria", "a canônica continua exposta"


def test_serializacao_oferece_o_conjunto_nao_uma_ordem_literal():
    """O defeito medido: 'escreva a frequência como: \"muitos\"' produziu 8
    'muitos' no mesmo texto, nos QUATRO modelos. O briefing deixa de mandar
    repetir."""
    ser = br.serializar_briefing(br.montar_briefing(_output()))
    assert 'escreva a frequência como: "' not in ser
    assert "a maioria" in ser and "a maior parte" in ser
    assert "varie" in ser.lower() or "não repita" in ser.lower()


def test_sem_permissao_de_quantificador_nao_vem_nem_faixa_nem_conjunto():
    """`sem_quantificador` (§3[C3]) continua significando o que sempre
    significou — o campo simplesmente não existe, para não ser copiado."""
    out = _output(buckets=[_bucket("negativas", 9,
                                   [_tema("ritmo lento", 5, 9)],
                                   estado="sem_quantificador")])
    t = br.montar_briefing(out)["grupos"]["negativas"]["temas"][0]
    assert "faixa" not in t and "quantificadores" not in t


# ============================================================ v1.9.9
# Entrega 3 — material do MOVIMENTO 2, separado do corte do MOVIMENTO 3
# ============================================================

def test_material_do_movimento2_ignora_o_corte_do_movimento3():
    """O diagnóstico medido: o corte `MAX_TEMAS_POR_GRUPO=3` é do movimento
    3, e come justamente os postos médios onde mora a propriedade descritiva
    compartilhada (em `cure`: atmosfera é #4 em medianas)."""
    out = _output(buckets=[
        _bucket("negativas", 40, [_tema(f"n{i}", 30 - i, 40) for i in range(6)]),
        _bucket("positivas", 40, [_tema(f"p{i}", 30 - i, 40) for i in range(5)]),
    ])
    b = br.montar_briefing(out)
    assert len(b["grupos"]["negativas"]["temas"]) == 3      # movimento 3, cortado
    material = b["movimento2"]["material"]
    nomes = [m["tema"] for m in material]
    assert "n5" in nomes and "p4" in nomes                  # movimento 2, inteiro
    assert len(material) == 11


def test_material_do_movimento2_nao_carrega_frequencia_nem_quantificador():
    """Movimento 2 é DESCRITIVO e sem valência — número ali seria convite a
    escrever frequência fora do movimento 3."""
    b = br.montar_briefing(_output())
    for m in b["movimento2"]["material"]:
        assert set(m) == {"tema", "grupo"}


def test_material_do_movimento2_respeita_a_permissao_do_piso():
    """Grupo em `sem_analise` não entrega tema em lugar nenhum — nem como
    material do movimento 2."""
    out = _output(buckets=[
        _bucket("negativas", 2, [_tema("invisível", 1, 2)], estado="sem_analise"),
        _bucket("positivas", 40, [_tema("atmosfera", 30, 40)]),
    ])
    material = br.montar_briefing(out)["movimento2"]["material"]
    assert [m["tema"] for m in material] == ["atmosfera"]


def test_o_orcamento_do_movimento2_NAO_mudou():
    """Registrado no delta: o teto (0,5) nunca foi encostado por nenhum
    modelo. Aumentá-lo produziria enchimento, não movimento 2."""
    b = br.montar_briefing(_output())
    assert b["orcamento_frases"]["movimento2"] == (0, 5)


def test_material_do_movimento2_e_escopado_na_serializacao():
    ser = br.serializar_briefing(br.montar_briefing(_output()))
    assert "MOVIMENTO 2" in ser
    assert "movimento 3" in ser.lower()


# ============================================================ v1.9.11
# Entrega 3 — o briefing AUTORIZA a contração da preposição
#
# Defeito real (`cidade-de-deus`, v1.9.10): "Em a grande maioria das notas
# (~91%)". O modelo obedeceu à instrução de escrever o rótulo LITERALMENTE
# e produziu português agramatical. A correção primária é aqui: dizer a ele
# que pode contrair.
# ============================================================

def test_serializacao_autoriza_a_contracao_do_artigo():
    ser = br.serializar_briefing(br.montar_briefing(_output()))
    assert "contra" in ser.lower()
    # cita ao menos uma contração concreta, para não ser regra abstrata
    assert "na " in ser or "da " in ser


def test_prompt_autoriza_contrair_sem_afrouxar_numero_nem_notas():
    p = br.PROMPT_NARRADOR_BRIEFING
    assert "contra" in p.lower()
    # a invariante segue escrita: número e "das notas" continuam intocáveis
    assert "das notas" in p


# ============================================================ v1.9.12
# Entrega 2 — rótulo de peso COMPARATIVO quando dois grupos colidem
#
# Medido em `joker-folie-a-deux` (46/33/21): dois parágrafos seguidos do
# movimento 3 abrindo com "Em boa parte das notas". Varrido o catálogo: 23
# de 35 filmes (66%) têm ao menos dois grupos com rótulo IDÊNTICO. O
# problema não é a largura das faixas (2% e 8% caem juntos em qualquer
# granularidade razoável) — é o rótulo ser calculado sem olhar os vizinhos.
# ============================================================

def test_sem_colisao_os_rotulos_sao_os_de_sempre():
    """Regressão: onde não há colisão, nada muda."""
    r = br.rotulos_peso({"positivas": 80, "medianas": 15, "negativas": 5})
    assert r == {"positivas": "a grande maioria das notas (~80%)",
                 "medianas": "uma parcela das notas (~15%)",
                 "negativas": "uma fração mínima das notas (~5%)"}


def test_colisao_o_maior_mantem_a_base_e_o_menor_recebe_comparativo():
    """O caso medido em `joker-folie-a-deux`."""
    r = br.rotulos_peso({"negativas": 46, "medianas": 33, "positivas": 21})
    assert r["negativas"] == "boa parte das notas (~46%)"
    assert r["medianas"] == "uma parte menor das notas (~33%)"
    assert r["positivas"] == "uma parcela das notas (~21%)"


def test_colisao_do_filme_aclamado_o_caso_dominante_do_catalogo():
    """21 dos 23 filmes em colisão são deste formato: `positivas` acima de
    80% empurra os outros dois para baixo de 15%."""
    r = br.rotulos_peso({"positivas": 90, "medianas": 8, "negativas": 2})
    assert r["positivas"] == "a grande maioria das notas (~90%)"
    assert r["medianas"] == "uma fração mínima das notas (~8%)"
    assert r["negativas"] == "uma fração ainda menor das notas (~2%)"


def test_tres_grupos_na_MESMA_faixa():
    """36+34+30 cabe numa faixa só (30-49) — a tabela tem de ter forma para
    o terceiro, senão dois deles voltam a colidir."""
    r = br.rotulos_peso({"a": 36, "b": 34, "c": 30})
    assert len(set(r.values())) == 3, r
    assert r["a"].startswith("boa parte")
    assert r["b"].startswith("uma parte menor")
    assert r["c"].startswith("uma parte ainda menor")


def test_percentual_IGUAL_nao_ganha_comparativo():
    """A verdade do comparativo é condição, não estilo: dizer "menor" para
    quem tem o MESMO peso seria falso. Rótulo coincidente é honesto quando
    o peso coincide de verdade."""
    r = br.rotulos_peso({"a": 40, "b": 40, "c": 20})
    assert r["a"] == r["b"] == "boa parte das notas (~40%)"


def test_todo_comparativo_e_verdadeiro_sobre_o_dado():
    """Varre todas as combinações que somam 100: sempre que um grupo recebe
    forma comparativa, ele é DE FATO menor que quem ficou com a base."""
    for neg in range(0, 101, 3):
        for med in range(0, 101 - neg, 3):
            shares = {"negativas": neg, "medianas": med,
                      "positivas": 100 - neg - med}
            rot = br.rotulos_peso(shares)
            base_de = {}
            for g, r in rot.items():
                faixa = br._faixa_peso(shares[g])
                base_de.setdefault(faixa, []).append((shares[g], r))
            for faixa, itens in base_de.items():
                base = [p for p, r in itens if r.startswith(faixa)]
                comp = [p for p, r in itens if not r.startswith(faixa)]
                for pc in comp:
                    assert all(pc <= pb for pb in base), (shares, rot)


def test_o_numero_entre_parenteses_nunca_muda():
    r = br.rotulos_peso({"negativas": 46, "medianas": 33, "positivas": 21})
    for g, pct in (("negativas", 46), ("medianas", 33), ("positivas", 21)):
        assert f"(~{pct}%)" in r[g]
        assert "das notas" in r[g]


def test_o_briefing_usa_o_rotulo_resolvido_em_conjunto():
    out = _output(distribuicao={"n_notas_total": 100,
                                "por_bucket": {"negativas": 46, "medianas": 33,
                                               "positivas": 21}})
    b = br.montar_briefing(out)
    rotulos = [b["grupos"][n]["rotulo_peso"] for n in b["movimento3"]["ordem"]]
    assert len(set(rotulos)) == 3, rotulos
    assert rotulos[0].startswith("boa parte")
    assert rotulos[1].startswith("uma parte menor")


def test_contracoes_continuam_valendo_sobre_a_forma_comparativa():
    """`variantes_rotulo` opera sobre o PRIMEIRO token — a autorização de
    contração da v1.9.11 tem de sobreviver ao rótulo comparativo."""
    from espectro24 import qualidade as q
    vs = q.variantes_rotulo("uma parte menor das notas (~33%)")
    assert "numa parte menor das notas (~33%)" in vs
    assert "duma parte menor das notas (~33%)" in vs
