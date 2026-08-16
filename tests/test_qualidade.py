"""Blocklist de resenha-speak e verificações mecânicas da prosa (§D2, v1.9.8).

A blocklist é DADO VERSIONADO fora do prompt — listar as expressões dentro
do prompt as introduziria no contexto, o que em vários modelos aumenta a
chance de aparecerem. Verificação em código, no padrão das demais checagens
mecânicas do projeto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import qualidade as q  # noqa: E402


# ------------------------------------------------------------- carregamento

def test_a_blocklist_e_arquivo_versionado_fora_do_prompt():
    assert q.ARQ_BLOCKLIST.exists()
    assert q.ARQ_BLOCKLIST.suffix == ".txt"


def test_carrega_expressoes_ignorando_comentario_e_vazio():
    exprs = q.carregar_blocklist()
    assert exprs
    assert all(not e.startswith("#") and e.strip() for e in exprs)


def test_as_expressoes_semente_estao_na_lista():
    exprs = set(q.carregar_blocklist())
    for e in ("uma jornada", "vale a pena conferir", "prende do inicio ao fim"):
        assert e in exprs


def test_a_blocklist_nao_aparece_no_prompt_do_narrador():
    """Se as expressões entrarem no prompt, elas entram no contexto — que é
    exatamente o que este desenho evita."""
    from espectro24 import briefing as br
    p = br.PROMPT_NARRADOR_BRIEFING.lower()
    for e in q.carregar_blocklist():
        assert e not in p


# ------------------------------------------------------------- detecção

def test_detecta_expressao_simples():
    achados = q.achar_resenha_speak("O filme é uma jornada e tanto.")
    assert [a["expressao"] for a in achados] == ["uma jornada"]


def test_detecta_ignorando_acento():
    """'de tirar o fôlego' tem de casar a entrada sem acento da lista."""
    achados = q.achar_resenha_speak("Uma cena de tirar o fôlego.")
    assert achados and achados[0]["expressao"] == "de tirar o folego"


def test_detecta_ignorando_caixa():
    assert q.achar_resenha_speak("VALE A PENA CONFERIR!")


def test_conta_ocorrencias_repetidas():
    txt = "uma jornada aqui, uma jornada ali"
    achados = q.achar_resenha_speak(txt)
    assert sum(a["n"] for a in achados) == 2


def test_texto_limpo_nao_acusa_nada():
    txt = ("O filme dura 111 minutos e a maioria das notas aponta um ritmo "
           "lento. Para esse grupo, a tensão não se sustenta.")
    assert q.achar_resenha_speak(txt) == []


def test_devolve_o_trecho_para_auditoria():
    """Mesma política de telemetria declarada do resto do projeto: o número
    sozinho não permite conferir se o achado é real."""
    a = q.achar_resenha_speak("Sem dúvida, vale a pena conferir esse filme.")[0]
    assert "vale a pena conferir" in a["trecho"].lower()


def test_nao_casa_dentro_de_palavra_maior():
    """'um must' não pode casar em 'um mustang'."""
    assert q.achar_resenha_speak("um mustang vermelho") == []


# ----------------------------------------------- checagens de formato/número

def test_formato_invalido_pega_json_embrulhado():
    assert q.formato_invalido('{"narrativa": "texto"}')
    assert q.formato_invalido("```\ntexto\n```")
    assert not q.formato_invalido("Um texto de prosa normal.")


def test_tokens_numericos_extrai_numeros_e_percentuais():
    assert q.tokens_numericos("111 minutos e ~79% das notas") == {"111", "79"}


def test_numeros_inventados_sao_detectados():
    """A defesa que neutraliza o risco histórico do Gemini de inflar
    contagem: qualquer número fora do briefing é reprovado."""
    permitidos = {"1997", "111", "79", "17", "3"}
    assert q.numeros_inventados("O filme de 1997 tem 111 min", permitidos) == set()
    assert q.numeros_inventados("nota média 8.5", permitidos) == {"8", "5"}


def test_numeros_do_briefing_reune_tudo_que_pode_aparecer():
    from espectro24 import briefing as br
    b = br.montar_briefing({
        "buckets": [{"bucket": "negativas", "n_validas": 40,
                     "estado_piso": "completa", "observacao_geral": "",
                     "temas": [{"tema": "t", "mencoes_aproximadas": 30,
                                "n_reviews_analisadas": 40}]}],
        "distribuicao": {"n_notas_total": 100,
                         "por_bucket": {"negativas": 55}},
    })
    nums = q.numeros_do_briefing(b)
    for esperado in ("40", "30", "55", "75"):     # n, menções, share, fração
        assert esperado in nums


def test_ordem_dos_movimentos_confere_a_do_briefing():
    briefing = {"movimento3": {"ordem": ["positivas", "negativas"]},
                "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)"},
                           "negativas": {"rotulo_peso": "uma fração mínima das notas (~3%)"}}}
    bom = ("... a grande maioria das notas (~80%) gostou. "
           "Já uma fração mínima das notas (~3%) reclamou.")
    ruim = ("... uma fração mínima das notas (~3%) reclamou. "
            "Já a grande maioria das notas (~80%) gostou.")
    assert q.ordem_dos_grupos_ok(bom, briefing)
    assert not q.ordem_dos_grupos_ok(ruim, briefing)


def test_rotulos_de_peso_presentes_literalmente():
    briefing = {"movimento3": {"ordem": ["positivas"]},
                "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)"}}}
    assert q.rotulos_peso_faltando("a grande maioria das notas (~80%) gostou",
                                   briefing) == []
    assert q.rotulos_peso_faltando("quase todo mundo gostou", briefing)


def test_vocabulario_do_peso_proibe_reviews_e_publico():
    assert q.vocabulario_peso_violado("a maioria das reviews gostou")
    assert q.vocabulario_peso_violado("a maioria do público gostou")
    assert not q.vocabulario_peso_violado("a maioria das notas gostou")


# ------------------------------------------------------------- verificar()

def _briefing_min():
    return {"movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": "a grande maioria das notas (~80%)",
                                     "marcacao_perspectiva": "nenhuma",
                                     "temas": []}},
            "orcamento_frases": {"movimento1": (0, 0)}}


def test_verificar_devolve_todas_as_flags():
    r = q.verificar("a grande maioria das notas (~80%) gostou do filme.",
                    _briefing_min())
    for chave in ("formato_invalido", "numeros_inventados", "rotulos_faltando",
                  "ordem_incorreta", "vocabulario_peso", "resenha_speak",
                  "n_flags"):
        assert chave in r


def test_verificar_conta_zero_flags_num_texto_limpo():
    r = q.verificar("a grande maioria das notas (~80%) gostou do filme.",
                    _briefing_min())
    assert r["n_flags"] == 0


def test_verificar_soma_as_flags_disparadas():
    r = q.verificar('{"narrativa": "a maioria das reviews adorou, uma jornada"}',
                    _briefing_min())
    assert r["n_flags"] >= 3      # formato + vocabulário + resenha-speak


# ============================================================ v1.9.9
# Entrega 1 — pertencimento à faixa e repetição de construção
# ============================================================

def _briefing_de_faixas(*faixas):
    """Briefing mínimo com uma faixa atribuída por tema — é o que a checagem
    de pertencimento consulta."""
    return {"movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~60%)",
                                     "temas": [{"tema": f"t{i}", "faixa": f}
                                               for i, f in enumerate(faixas)]}}}


def test_construcao_da_faixa_certa_passa_mesmo_sem_ser_a_canonica():
    """O ponto da Entrega 1: a verificação deixa de exigir a string literal
    e passa a exigir PERTENCIMENTO ao conjunto da faixa."""
    b = _briefing_de_faixas("muitos")
    assert q.quantificadores_fora_de_faixa(
        "Uma parcela expressiva aponta o ritmo.", b) == []


def test_construcao_de_outra_faixa_e_flag():
    """'quase todos' num texto cuja única faixa é 'muitos' inflaria o dado —
    é o modo de falha que a verificação literal pegava por acidente e este
    desenho tem de continuar pegando."""
    b = _briefing_de_faixas("muitos")
    assert q.quantificadores_fora_de_faixa(
        "Quase todos apontam o ritmo.", b) == ["quase todos"]


def test_repeticao_da_mesma_construcao_e_flag():
    """O defeito medido em `cure`: 8 'muitos' no mesmo texto, nos 4
    modelos."""
    texto = ("muitos enfatizam. muitos valorizam. muitos ressaltam. "
             "muitos apontam.")
    rep = q.quantificadores_repetidos(texto)
    assert rep == [{"construcao": "muitos", "n": 4}]


def test_duas_ocorrencias_ainda_passam():
    """O limite é `QUANT_MAX_REPETICOES`; duas usos da mesma palavra é
    prosa normal, não tique."""
    assert q.quantificadores_repetidos("muitos apontam. muitos valorizam.") == []


def test_o_rotulo_de_peso_nao_conta_como_repeticao_de_construcao():
    """`rotulo_peso` compartilha vocabulário com as construções e é literal
    OBRIGATÓRIO — punir sua presença seria punir a obediência ao briefing."""
    b = {"movimento3": {"ordem": ["positivas", "negativas"]},
         "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~60%)",
                                  "temas": [{"tema": "t", "faixa": "a maioria"}]},
                    "negativas": {"rotulo_peso": "boa parte das notas (~40%)",
                                  "temas": [{"tema": "u", "faixa": "muitos"}]}}}
    texto = ("A maioria das notas (~60%) elogia; a maioria destaca o ritmo. "
             "Boa parte das notas (~40%) discorda, e boa parte cita o roteiro.")
    assert q.quantificadores_repetidos(texto, briefing=b) == []


def test_faixa_ausente_no_briefing_nao_gera_falso_positivo():
    """Grupo sem permissão de quantificador (§3[C3]) não tem faixa; o texto
    correto simplesmente não usa construção nenhuma."""
    b = {"movimento3": {"ordem": ["positivas"]},
         "grupos": {"positivas": {"temas": [{"tema": "t"}]}}}
    assert q.quantificadores_fora_de_faixa("O grupo aponta o ritmo.", b) == []


# ============================================================ v1.9.9
# Entrega 2 — estrutura de parágrafo
# ============================================================

def _briefing_com_ficha(ficha=True):
    return {"movimento3": {"ordem": []}, "grupos": {},
            "orcamento_frases": {"movimento1": (2, 3) if ficha else (0, 0),
                                 "movimento2": (0, 5), "movimento3": (4, 8)}}


def test_bloco_unico_e_flag():
    """`gemini-3.1-pro` entregou os 3 filmes num bloco único de até 318
    palavras e NENHUMA flag disparou — `formato_invalido` (v1.7.2) checa
    invólucro, não legibilidade."""
    texto = " ".join(["palavra"] * 200)
    p = q.problemas_de_paragrafo(texto, _briefing_com_ficha())
    assert p["n_paragrafos"] == 1
    assert p["insuficientes"] is True
    assert p["longos"]


def test_um_paragrafo_por_movimento_passa():
    texto = "Um filme de 1997.\n\nA experiência é lenta.\n\nOs grupos divergem."
    p = q.problemas_de_paragrafo(texto, _briefing_com_ficha())
    assert p["n_paragrafos"] == 3 and p["insuficientes"] is False


def test_o_minimo_vem_do_ORCAMENTO_nao_de_uma_constante():
    """Sem ficha o movimento 1 não existe — exigir 3 parágrafos reprovaria
    o narrador por obedecer à instrução de pular o movimento."""
    texto = "A experiência é lenta.\n\nOs grupos divergem."
    assert q.problemas_de_paragrafo(
        texto, _briefing_com_ficha(ficha=False))["insuficientes"] is False
    assert q.problemas_de_paragrafo(
        texto, _briefing_com_ficha(ficha=True))["insuficientes"] is True


def test_paragrafo_acima_do_teto_e_reportado_com_o_tamanho():
    texto = "Curto.\n\n" + " ".join(["p"] * (q.MAX_PALAVRAS_PARAGRAFO + 1)) + "\n\nFim."
    longos = q.problemas_de_paragrafo(texto, _briefing_com_ficha())["longos"]
    assert longos == [{"indice": 1, "n_palavras": q.MAX_PALAVRAS_PARAGRAFO + 1}]


def test_verificar_soma_as_flags_novas():
    """As flags novas entram em `n_flags` no mesmo padrão das antigas — é o
    que faz a tabela da Entrega 4 mudar de veredito."""
    b = _briefing_de_faixas("muitos")
    b["orcamento_frases"] = {"movimento1": (2, 3), "movimento2": (0, 5),
                             "movimento3": (4, 8)}
    limpo = ("A maioria das notas (~60%) elogia o ritmo.\n\n"
             "Boa parte aponta a atmosfera.\n\n"
             "Uma parcela expressiva cita o roteiro.")
    v = q.verificar(limpo, b)
    assert v["quantificador_fora_de_faixa"] == [] and v["quantificador_repetido"] == []
    assert v["paragrafos_insuficientes"] is False

    tique = ("A maioria das notas (~60%) elogia. muitos apontam. muitos citam. "
             "muitos ressaltam. muitos julgam.")
    v2 = q.verificar(tique, b)
    assert v2["quantificador_repetido"]
    assert v2["paragrafos_insuficientes"] is True
    assert v2["n_flags"] >= 2


# ============================================================ v1.9.9
# Fechamento — parágrafo por GRUPO no movimento 3
#
# Medido: `cidade-de-deus` saiu com 3 parágrafos (passa em
# `problemas_de_paragrafo`), mas o movimento 3 inteiro — os três grupos —
# ficou espremido num bloco único. Nenhuma flag existente via essa
# diferença: `problemas_de_paragrafo` só conta o TOTAL de parágrafos do
# texto, não a que grupo cada um pertence.
# ============================================================

def _briefing_3grupos(estados=("completa", "completa", "completa")):
    nomes = ("positivas", "medianas", "negativas")
    grupos = {}
    for nome, pct, estado in zip(nomes, (80, 17, 3), estados):
        permissoes = {"pode_citar_temas": estado != "sem_analise",
                      "pode_citar_numero": estado in ("completa", "sem_quantificador"),
                      "pode_citar_quantificador": estado == "completa"}
        grupos[nome] = {"rotulo_peso": f"peso de {nome} (~{pct}%)",
                        "permissoes": permissoes,
                        "temas": [{"tema": "t"}] if permissoes["pode_citar_temas"] else []}
    return {"movimento3": {"ordem": list(nomes)}, "grupos": grupos,
            "orcamento_frases": {"movimento1": (2, 3), "movimento2": (0, 5),
                                 "movimento3": (4, 8)}}


def test_paragrafos_por_grupo_localiza_o_indice_do_paragrafo_de_cada_um():
    b = _briefing_3grupos()
    texto = ("Abertura.\n\n"
             "peso de positivas (~80%) elogia.\n\n"
             "peso de medianas (~17%) hesita.\n\n"
             "peso de negativas (~3%) reclama.")
    pares = q.paragrafos_por_grupo(texto, b)
    assert pares == {"positivas": 1, "medianas": 2, "negativas": 3}


def test_movimento3_num_bloco_unico_e_flag():
    """O defeito medido: os 3 grupos, cada um com rótulo de peso próprio,
    todos dentro do MESMO parágrafo."""
    b = _briefing_3grupos()
    texto = ("Abertura.\n\n"
             "Experiência.\n\n"
             "peso de positivas (~80%) elogia. peso de medianas (~17%) "
             "hesita. peso de negativas (~3%) reclama.")
    colisoes = q.grupos_sem_paragrafo_proprio(texto, b)
    assert set(colisoes) == {"medianas", "negativas"}


def test_um_paragrafo_por_grupo_apresentado_nao_e_flag():
    b = _briefing_3grupos()
    texto = ("Abertura.\n\n"
             "Experiência.\n\n"
             "peso de positivas (~80%) elogia.\n\n"
             "peso de medianas (~17%) hesita.\n\n"
             "peso de negativas (~3%) reclama.")
    assert q.grupos_sem_paragrafo_proprio(texto, b) == []


def test_grupo_sem_analise_nao_exige_paragrafo_proprio():
    """'um filme com bucket em sem_analise tem menos [parágrafos], e a
    regra acompanha o número real de grupos APRESENTADOS' — grupo sem
    permissão de citar tema não entra na contagem."""
    b = _briefing_3grupos(estados=("completa", "completa", "sem_analise"))
    texto = ("Abertura.\n\n"
             "Experiência.\n\n"
             "peso de positivas (~80%) elogia.\n\n"
             "peso de medianas (~17%) hesita. peso de negativas (~3%) tem poucas reviews.")
    # negativas (sem_analise) divide parágrafo com medianas — não conta como
    # colisão, porque negativas não é um grupo "apresentado".
    assert q.grupos_sem_paragrafo_proprio(texto, b) == []


def test_rotulo_ausente_nao_gera_falso_positivo_de_colisao():
    """Rótulo que não aparece no texto já é reprovado por
    `rotulos_peso_faltando` — não deve também aparecer aqui como colisão."""
    b = _briefing_3grupos()
    texto = "Abertura.\n\npeso de positivas (~80%) elogia."
    assert q.grupos_sem_paragrafo_proprio(texto, b) == []


def test_verificar_reporta_movimento3_em_bloco_unico():
    b = _briefing_3grupos()
    texto = ("Abertura.\n\n"
             "Experiência.\n\n"
             "peso de positivas (~80%) elogia. peso de medianas (~17%) "
             "hesita. peso de negativas (~3%) reclama.")
    v = q.verificar(texto, b)
    assert v["grupos_sem_paragrafo_proprio"]
    assert v["n_flags"] >= 1


# ============================================================ v1.9.11
# Entrega 3 — a preposição do rótulo de peso
#
# Defeito real na narrativa final de `cidade-de-deus` (v1.9.10): "Em a
# grande maioria das notas (~91%)". Colisão entre duas regras CORRETAS: o
# rótulo é preservado LITERALMENTE (invariante desde a v1.6.0) e o
# português contrai "em + a" → "na". O modelo obedeceu e escreveu
# agramatical.
# ============================================================

def _briefing_rotulo(rotulo="a grande maioria das notas (~91%)"):
    return {"movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": rotulo,
                                     "permissoes": {"pode_citar_temas": True},
                                     "temas": [{"tema": "t", "faixa": "muitos"}]}},
            "orcamento_frases": {"movimento1": (2, 3), "movimento2": (0, 5),
                                 "movimento3": (4, 8)}}


@pytest.mark.parametrize("escrito", [
    "a grande maioria das notas (~91%)",      # literal
    "na grande maioria das notas (~91%)",     # em + a
    "da grande maioria das notas (~91%)",     # de + a
    "à grande maioria das notas (~91%)",      # a + a  (crase: NÃO é substring)
    "pela grande maioria das notas (~91%)",   # por + a
])
def test_contracao_pre_aprovada_conta_como_rotulo_presente(escrito):
    """A correção: o modelo não precisa escolher entre obedecer à
    invariante e escrever português.

    Nota de medição: `na`/`da`/`pela` já passavam ANTES desta versão, por
    ACIDENTE — a checagem é `rotulo in texto`, e "na grande maioria…"
    contém "a grande maioria…" como substring. Só a CRASE ("à") quebrava,
    porque "à" ≠ "a". O acidente não é garantia, e é o que este teste
    transforma em contrato.
    """
    b = _briefing_rotulo()
    assert q.rotulos_peso_faltando(f"Texto. {escrito} elogia o filme.", b) == []


def test_variantes_listam_so_contracoes_do_artigo_que_existe():
    """O conjunto é PRÉ-APROVADO, não "qualquer prefixo": um rótulo que
    começa com artigo definido ganha as contrações dele; um que não começa
    com artigo nenhum não ganha variante inventada."""
    com_artigo = q.variantes_rotulo("a grande maioria das notas (~91%)")
    assert "à grande maioria das notas (~91%)" in com_artigo
    assert "na grande maioria das notas (~91%)" in com_artigo

    sem_artigo = q.variantes_rotulo("boa parte das notas (~40%)")
    assert sem_artigo == ["boa parte das notas (~40%)"]

    # e toda variante preserva número e a palavra "notas"
    for v in com_artigo:
        assert "notas (~91%)" in v


def test_primeira_letra_em_qualquer_caixa_continua_valendo():
    """Mesma regra que o editor tinha (v1.7.1): a INICIAL pode mudar de
    caixa (início de período), nenhuma outra letra pode."""
    b = _briefing_rotulo()
    assert q.rotulos_peso_faltando("A grande maioria das notas (~91%) elogia.", b) == []
    assert q.rotulos_peso_faltando("Na grande maioria das notas (~91%) elogia.", b) == []


def test_o_NUMERO_continua_intocavel():
    """Só o artigo inicial varia. Trocar o percentual é violação, com ou
    sem contração."""
    b = _briefing_rotulo()
    assert q.rotulos_peso_faltando("na grande maioria das notas (~90%) elogia.", b)
    assert q.rotulos_peso_faltando("a grande maioria das notas (~90%) elogia.", b)


def test_a_palavra_notas_continua_intocavel():
    """A invariante de vocabulário do peso (v1.4.1) não é afrouxada pela
    contração."""
    b = _briefing_rotulo()
    assert q.rotulos_peso_faltando("na grande maioria das reviews (~91%) elogia.", b)


def test_contracao_de_artigo_indefinido():
    """`uma parcela`/`uma fração mínima` contraem com em: numa. `de uma`
    (não contraído) sempre valeu — nunca precisou de autorização."""
    b = _briefing_rotulo("uma parcela das notas (~17%)")
    for escrito in ("uma parcela das notas (~17%)",
                    "numa parcela das notas (~17%)",
                    "de uma parcela das notas (~17%)"):
        assert q.rotulos_peso_faltando(f"Texto. {escrito} discorda.", b) == [], escrito


def test_duma_NAO_e_mais_uma_contracao_pre_aprovada():
    """[v1.9.13] Decisão do dono do projeto: `duma` é gramaticalmente
    correta mas soa arcaica em prosa escrita. Removida do conjunto
    AUTORIZADO — o briefing deixa de oferecê-la ao narrador.

    Nota de medição: `rotulos_peso_faltando` continua aceitando um rótulo
    escrito com "duma" por ACIDENTE de substring ("duma X" contém "uma X"
    dentro) — o mesmo acidente que já valia para "na"/"da"/"pela" antes da
    v1.9.11. Não é regressão: a correção desta entrega é o que o briefing
    OFERECE, não uma proibição nova na checagem de presença."""
    vs = q.variantes_rotulo("uma parcela das notas (~17%)")
    assert not any(v.startswith("duma ") for v in vs), vs
    # "de uma" (não contraída) nunca precisou de autorização — continua.
    b = _briefing_rotulo("uma parcela das notas (~17%)")
    assert q.rotulos_peso_faltando(
        "Texto. de uma parcela das notas (~17%) discorda.", b) == []


def test_rotulo_sem_artigo_passa_com_preposicao_solta():
    """`boa parte` não contrai — "em boa parte" já é a forma correta, e o
    rótulo aparece literal. Nada a fazer aqui, e o teste existe para travar
    que a mudança não introduziu exigência nova nesse caso."""
    b = _briefing_rotulo("boa parte das notas (~40%)")
    assert q.rotulos_peso_faltando("Em boa parte das notas (~40%) há elogio.", b) == []


def test_a_contracao_nao_quebra_a_ordem_dos_grupos():
    """Todo consumidor da âncora do rótulo tem de enxergar a contração —
    senão um grupo escrito com "na…" some da verificação de ORDEM."""
    b = {"movimento3": {"ordem": ["positivas", "negativas"]},
         "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~80%)"},
                    "negativas": {"rotulo_peso": "uma fração mínima das notas (~5%)"}}}
    bom = "Na maioria das notas (~80%) há elogio. Numa fração mínima das notas (~5%), crítica."
    ruim = "Numa fração mínima das notas (~5%), crítica. Na maioria das notas (~80%) há elogio."
    assert q.ordem_dos_grupos_ok(bom, b)
    assert not q.ordem_dos_grupos_ok(ruim, b)


def test_a_contracao_nao_quebra_o_paragrafo_por_grupo():
    b = {"movimento3": {"ordem": ["positivas", "negativas"]},
         "grupos": {
             "positivas": {"rotulo_peso": "a maioria das notas (~80%)",
                           "permissoes": {"pode_citar_temas": True}, "temas": [{"tema": "t"}]},
             "negativas": {"rotulo_peso": "uma fração mínima das notas (~5%)",
                           "permissoes": {"pode_citar_temas": True}, "temas": [{"tema": "u"}]}}}
    texto = ("Abertura.\n\nNa maioria das notas (~80%) há elogio.\n\n"
             "Numa fração mínima das notas (~5%), crítica.")
    assert q.paragrafos_por_grupo(texto, b) == {"positivas": 1, "negativas": 2}
    assert q.grupos_sem_paragrafo_proprio(texto, b) == []


def test_a_contracao_nao_vira_repeticao_de_quantificador():
    """`_texto_sem_rotulos_de_peso` tem de remover a forma CONTRAÍDA também
    — senão o "a maioria" dentro de "na maioria das notas (~80%)" é contado
    como construção quantificadora e o texto é punido por obedecer."""
    b = {"movimento3": {"ordem": ["positivas"]},
         "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~80%)",
                                  "temas": [{"tema": "t", "faixa": "a maioria"}]}}}
    texto = ("Na maioria das notas (~80%) há elogio. A maioria cita o ritmo, "
             "e a maioria destaca a fotografia.")
    assert q.quantificadores_repetidos(texto, briefing=b) == []


# ============================================================ v1.9.13
# Entrega 1 — movimento 1 e movimento 2 no MESMO parágrafo
#
# Medido em `cure`: "A experiência do filme é conduzida por um ritmo
# desacelerado..." (claramente movimento 2) colado ao fim do parágrafo de
# apresentação. O TOTAL de parágrafos (4) já passava no mínimo (3) — a
# checagem existente conta quantidade, não POSIÇÃO.
#
# PROXY DECLARADO (mesmo espírito de `selecao_narrativa.cobertura`): a
# distinção entre "movimento 2 omitido" (autorizado) e "movimento 2
# fundido no parágrafo errado" não é computável por posição — as duas
# produzem a MESMA contagem de parágrafos entre a âncora do movimento 1 e
# o início do movimento 3. O proxy conta FRASES do parágrafo ancorado pelo
# ANO da ficha: mais de duas é sinal de que ele carrega mais do que
# "diretor, gênero, ano, premissa".
# ============================================================

def _briefing_com_ano(ano=1997):
    return {"ficha": {"ano": ano}, "movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~80%)",
                                     "permissoes": {"pode_citar_temas": True},
                                     "temas": [{"tema": "t"}]}}}


def test_paragrafo_do_ano_com_mais_de_duas_frases_e_flag():
    """O caso medido em `cure`: 3 frases no parágrafo de abertura, a
    terceira sendo claramente movimento 2."""
    b = _briefing_com_ano()
    texto = ("Lançado em 1997, o filme é um suspense. A trama acompanha "
             "uma investigação complexa. A experiência é conduzida por um "
             "ritmo lento e denso.\n\n"
             "a maioria das notas (~80%) elogia o filme.")
    assert q.movimento1_e_movimento2_no_mesmo_paragrafo(texto, b) is True


def test_paragrafo_do_ano_com_duas_frases_passa():
    """`cidade-de-deus`/`the-invite-2026`/`joker-folie-a-deux`: 2 frases,
    ambas movimento 1 — não dispara."""
    b = _briefing_com_ano()
    texto = ("Lançado em 1997, o filme é um suspense. A trama acompanha "
             "uma investigação complexa.\n\n"
             "a maioria das notas (~80%) elogia o filme.")
    assert q.movimento1_e_movimento2_no_mesmo_paragrafo(texto, b) is False


def test_sem_ficha_nao_ha_o_que_checar():
    b = {"ficha": None, "movimento3": {"ordem": []}, "grupos": {}}
    texto = "Frase um. Frase dois. Frase três. Frase quatro."
    assert q.movimento1_e_movimento2_no_mesmo_paragrafo(texto, b) is False


def test_ano_ausente_do_texto_nao_e_punido_aqui():
    """Ano que não aparece é outro defeito (número inventado/faltando) —
    esta checagem não dobra a reprovação."""
    b = _briefing_com_ano()
    texto = "Um suspense atmosférico. Muito bem dirigido. Ótima atuação."
    assert q.movimento1_e_movimento2_no_mesmo_paragrafo(texto, b) is False


def test_verificar_soma_a_flag_de_movimento1_e_2():
    b = _briefing_com_ano()
    b["orcamento_frases"] = {"movimento1": (2, 3), "movimento2": (0, 5),
                             "movimento3": (4, 8)}
    ruim = ("Lançado em 1997, um suspense. A trama é complexa. O ritmo é "
            "lento e denso.\n\na maioria das notas (~80%) elogia.")
    v = q.verificar(ruim, b)
    assert v["movimento1_e_movimento2_no_mesmo_paragrafo"] is True
    assert v["n_flags"] >= 1


# ============================================================ v1.9.13
# Entrega 2 — repetição por RAIZ, não por string literal
#
# Medido em `joker-folie-a-deux`: "a maior parcela" e "a maior parte" em
# parágrafos vizinhos — duas construções DIFERENTES da mesma faixa, então
# a checagem por string não via nada, mas o efeito no leitor é o tique de
# novo, em forma mais sutil.
# ============================================================

def _briefing_faixa_a_maioria():
    return {"movimento3": {"ordem": ["positivas"]},
            "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~60%)",
                                     "temas": [{"tema": "t", "faixa": "a maioria"}]}}}


def test_duas_construcoes_da_MESMA_raiz_disparam_a_flag():
    b = _briefing_faixa_a_maioria()
    texto = ("A maioria das notas (~60%) elogia. A maior parcela cita o "
             "ritmo, a maior parte destaca a atuação, e a maior parcela "
             "também elogia a fotografia.")
    rep = q.quantificadores_repetidos(texto, briefing=b)
    assert rep, "três ocorrências da raiz 'maior' deviam contar juntas"
    assert rep[0]["n"] == 3


def test_construcoes_de_RAIZES_diferentes_na_mesma_faixa_nao_disparam():
    """'a maioria' e 'grande parte' são raízes distintas dentro da mesma
    faixa — usar as duas não é tique, é variação."""
    b = _briefing_faixa_a_maioria()
    texto = ("A maioria das notas (~60%) elogia. A maioria cita o ritmo, "
             "e grande parte destaca a atuação.")
    assert q.quantificadores_repetidos(texto, briefing=b) == []


def test_raiz_nao_agrupa_ENTRE_faixas_diferentes():
    """'boa parte' (faixa muitos) e 'uma parte' (faixa alguns) compartilham
    a palavra 'parte', mas medem frequências DIFERENTES — agrupar entre
    faixas apagaria a distinção que a faixa existe para preservar."""
    b = {"movimento3": {"ordem": ["positivas", "negativas"]},
         "grupos": {"positivas": {"rotulo_peso": "a maioria das notas (~60%)",
                                  "temas": [{"tema": "t", "faixa": "muitos"}]},
                    "negativas": {"rotulo_peso": "uma fração mínima das notas (~10%)",
                                  "temas": [{"tema": "u", "faixa": "alguns"}]}}}
    texto = ("A maioria das notas (~60%) elogia: boa parte cita o ritmo. "
             "Uma fração mínima das notas (~10%) discorda: uma parte "
             "reclama do roteiro.")
    assert q.quantificadores_repetidos(texto, briefing=b) == []


def test_todas_as_faixas_tem_pelo_menos_3_raizes_OU_estao_documentadas():
    """O crítico da Entrega 2: agrupar por raiz não pode reduzir uma faixa
    a ponto de o narrador ficar sem variação, sem que isso seja EXPLÍCITO.
    `cerca de metade` é a exceção conhecida (limite estrutural do
    português) — todas as outras têm de alcançar 3."""
    from espectro24.briefing import FAIXAS_QUANTIFICADOR
    excecoes = {"cerca de metade"}
    for faixa, construcoes in FAIXAS_QUANTIFICADOR.items():
        raizes = {q.RAIZ_POR_CONSTRUCAO.get(c, c) for c in construcoes}
        if faixa in excecoes:
            continue
        assert len(raizes) >= 3, f"{faixa}: só {len(raizes)} raízes — {raizes}"


def test_construcoes_novas_nao_colidem_com_nada_existente():
    """As construções acrescentadas para resolver o crítico não podem
    quebrar a invariante de disjunção da v1.9.9 (nenhuma é substring de
    outra, em faixa nenhuma)."""
    from espectro24.briefing import FAIXAS_QUANTIFICADOR
    todas = [c for cs in FAIXAS_QUANTIFICADOR.values() for c in cs]
    for a in todas:
        for b in todas:
            if a == b:
                continue
            assert a not in b, f"{a!r} é substring de {b!r}"
