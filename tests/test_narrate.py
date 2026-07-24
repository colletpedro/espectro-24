"""[D2] Narrador (v1.2.0) — mock, zero rede.

Garante que: (1) o narrador recebe SÓ o JSON validado (reviews brutas nunca
entram no prompt); (2) as validações de prosa (idioma/aspas/escopo) funcionam
com as mesmas flags; (3) modo degradado (sem_analise) narra a escassez sem
inventar temas.
"""
import pytest

from espectro24.models import BucketResult, LevelResult, Review, Tema
from espectro24.render import build_output
from espectro24.synthesize import (
    NARRATOR_SYSTEM_PROMPT,
    _forca_declarada,
    _fracao_e_rotulo,
    _fracao_percentual,
    _quantificadores_validos,
    _rotulo_quantificador,
    _serialize_output_for_narrator,
    conferencia_quantificador,
    narrate_output,
)


def _bucket(nome, alvo, modo, temas=None, obs="", n_reviews=0, review_text="x"):
    lvl = LevelResult(4.0, 150, 1, n_reviews, 0, 0, 0, 0)
    lvl.validas = [
        Review(viewing_id=f"v{i}", rating=4.0, text=review_text, truncated=False,
               full_text_url=None, spoiler=False, full_text=review_text)
        for i in range(n_reviews)
    ]
    return BucketResult(nome=nome, alvo=alvo, modo=modo, niveis=[lvl],
                        temas=temas or [], observacao_geral=obs)


def _output_completo(review_text="TEXTO_BRUTO_SECRETO_DA_REVIEW"):
    temas = [Tema("ritmo", 3, 5, "este grupo achou o ritmo lento")]
    buckets = [
        _bucket("negativas", 50, "completo", temas, "as reviews negativas apontam ritmo lento", 5, review_text),
        _bucket("medianas", 20, "completo", temas, "as reviews medianas ficaram divididas", 5, review_text),
        _bucket("positivas", 30, "completo", temas, "as reviews positivas elogiam a direção", 5, review_text),
    ]
    return build_output("cure", buckets, "2026-01-01", {}, 42)


# --- (1) narrador recebe SÓ o JSON validado ---

def test_serializacao_nao_vaza_texto_bruto_de_review():
    out = _output_completo(review_text="TEXTO_BRUTO_SECRETO_DA_REVIEW")
    ser = _serialize_output_for_narrator(out)
    assert "TEXTO_BRUTO_SECRETO_DA_REVIEW" not in ser
    # mas os dados validados estão lá
    assert "ritmo" in ser and "42" in ser


def test_narrador_prompt_construido_nao_contem_reviews_brutas():
    out = _output_completo(review_text="SPOILER_DO_FINAL_XYZ")
    capturado = {}

    def fake(system, user, model):
        capturado["system"] = system
        capturado["user"] = user
        return '{"narrativa": "as reviews negativas apontam ritmo; quem gostou elogia a direção; o grupo mediano ficou dividido."}'

    narrate_output(out, client_call=fake, model="gemini-2.5-flash")
    assert "SPOILER_DO_FINAL_XYZ" not in capturado["user"]
    assert capturado["system"] == NARRATOR_SYSTEM_PROMPT  # prompt fixo §D2


def test_uma_chamada_para_o_filme_inteiro():
    out = _output_completo()
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return '{"narrativa": "as reviews negativas apontam ritmo lento; quem deu nota alta elogia a direção."}'

    narrate_output(out, client_call=fake, model="gemini-2.5-flash")
    assert len(calls) == 1  # não por bucket


# --- (2) validações de prosa ---

def test_aspas_removidas_da_prosa():
    out = _output_completo()

    def fake(system, user, model):
        return '{"narrativa": "as reviews negativas dizem que o filme e \\"chato\\" e lento, mas quem gostou elogia a direção."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert '"' not in r.texto
    assert r.aspas_removidas is True


def test_idioma_ingles_marca_flag_apos_retentativa():
    out = _output_completo()

    def fake(system, user, model):
        return '{"narrativa": "the negative reviews point to a slow pace and the positive ones praise the direction of the film with great enthusiasm."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.idioma_invalido is True


def test_idioma_ptbr_nao_marca_flag_e_nao_retenta():
    out = _output_completo()
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return '{"narrativa": "as reviews negativas apontam que o ritmo do filme e lento e arrastado, enquanto quem deu notas altas elogia a direcao e a construcao dos personagens ao longo da trama."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.idioma_invalido is False
    assert len(calls) == 1  # sem retentativa


def test_escopo_generalizado_marca_flag():
    # usa um marcador que existe em _MARCADORES_ESCOPO ("o consenso")
    out = _output_completo()

    def fake(system, user, model):
        return '{"narrativa": "o consenso e que o filme e um fracasso completo e sem gracas em todos os seus aspectos tecnicos."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.escopo_suspeito is True


def test_escopo_corrigido_na_retentativa_zera_flag():
    respostas = [
        '{"narrativa": "o consenso e que o filme e um fracasso."}',
        '{"narrativa": "as reviews negativas apontam um filme fraco, mas quem gostou destaca a direcao competente."}',
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.escopo_suspeito is False
    assert "as reviews negativas" in r.texto


def test_json_invalido_duas_vezes_marca_falhou():
    def fake(system, user, model):
        return "isto não é json"

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.falhou is True
    assert r.texto == ""


# --- (3) modo degradado: sem_analise ---

def test_narrativa_degradada_serializa_escassez_sem_inventar_temas():
    buckets = [
        _bucket("negativas", 50, "sem_analise", [], "Bucket sem análise temática: apenas 1 review(s) válida(s) (piso é 3).", 1),
        _bucket("medianas", 20, "sem_analise", [], "Bucket sem análise temática: apenas 2 review(s) válida(s) (piso é 3).", 2),
        _bucket("positivas", 30, "sem_analise", [], "Bucket sem análise temática: apenas 0 review(s) válida(s) (piso é 3).", 0),
    ]
    out = build_output("filme-obscuro", buckets, "2026-01-01", {}, 3)
    ser = _serialize_output_for_narrator(out)
    # a serialização informa a escassez e NÃO fabrica temas
    assert "sem temas" in ser
    assert "sem_analise" in ser

    capturado = {}

    def fake(system, user, model):
        capturado["user"] = user
        return '{"narrativa": "este filme tem pouquíssimas reviews: os poucos que escreveram se dividem, sem um padrão claro o suficiente para uma análise temática."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.falhou is False
    # o prompt não contém nenhum tema (não havia temas a passar)
    assert "mencionado em" not in capturado["user"]


# --- v1.2.1: invariante anti-prevalência (cota ≠ distribuição da recepção) ---

def test_prompt_contem_invariante_de_tamanho_de_grupo():
    assert "TAMANHO DOS GRUPOS" in NARRATOR_SYSTEM_PROMPT
    assert "MÉTODO DE COLETA" in NARRATOR_SYSTEM_PROMPT
    # proíbe explicitamente os marcadores citados na tarefa
    for termo in ("igualmente expressivo", "polarizada", "minoria",
                  "maioria dos espectadores"):
        assert termo in NARRATOR_SYSTEM_PROMPT
    # a antiga proporção cross-group foi removida da regra de proporções
    assert "uma minoria mediana" not in NARRATOR_SYSTEM_PROMPT


def test_narrador_prompt_montado_carrega_a_invariante():
    capturado = {}

    def fake(system, user, model):
        capturado["system"] = system
        return '{"narrativa": "entre quem nao gostou, os temas foram ritmo e roteiro; ja entre quem gostou, a direcao foi elogiada."}'

    narrate_output(_output_completo(), client_call=fake, model="m")
    assert "PROIBIDO comparar tamanhos entre grupos" in capturado["system"]


# --- v1.2.3: quantificadores pré-computados pelo código (não mais pelo LLM) ---
# Correção pela raiz do modo de falha "quase todos"/"praticamente todos"
# aplicado a frações de 65-70%, que reincidiu 2x na 1a regeneração pós-v1.2.2
# (a calibração por INSTRUÇÃO — LLM calcula a fração e escolhe sozinho —
# reduziu mas não eliminou o defeito). Mesmo princípio da v1.1.1
# (denominador): o código é a autoridade, o LLM só usa o rótulo fornecido.

def test_prompt_contem_regra_de_quantificador_pre_computado():
    assert "QUANTIFICADOR PRÉ-COMPUTADO" in NARRATOR_SYSTEM_PROMPT
    assert "rótulo_quantificador" in NARRATOR_SYSTEM_PROMPT
    assert "PROIBIDO usar um quantificador MAIS FORTE" in NARRATOR_SYSTEM_PROMPT
    assert "MAIS FRACO é permitido" in NARRATOR_SYSTEM_PROMPT
    # a escala de força, do mais fraco ao mais forte, ainda é comunicada
    for termo in ("poucos", "alguns", "muitos", "cerca de metade",
                  "a maioria", "quase todos"):
        assert termo in NARRATOR_SYSTEM_PROMPT
    # o LLM não deve mais ser instruído a calcular a fração sozinho
    assert "CALIBRAÇÃO NUMÉRICA" not in NARRATOR_SYSTEM_PROMPT
    assert "nunca escolha \"no olho\"" not in NARRATOR_SYSTEM_PROMPT


def test_narrador_prompt_montado_carrega_a_regra_de_quantificador():
    capturado = {}

    def fake(system, user, model):
        capturado["system"] = system
        return '{"narrativa": "entre quem nao gostou, alguns citaram o ritmo; ja entre quem gostou, a maioria elogiou a direcao."}'

    narrate_output(_output_completo(), client_call=fake, model="m")
    assert "QUANTIFICADOR PRÉ-COMPUTADO" in capturado["system"]


# --- v1.2.3: resolução determinística fração -> rótulo (código, não LLM) ---

@pytest.mark.parametrize("pct,esperado", [
    (0, "poucos"), (5, "poucos"), (9, "poucos"),
    (10, "alguns"),          # borda: só "alguns" bate (poucos exige pct<10)
    (24, "alguns"),
    (25, "alguns"),          # borda: alguns×muitos empatam -> mais fraco (alguns)
    (26, "muitos"),
    (49, "muitos"),
    (50, "muitos"),          # borda: muitos×cerca×maioria empatam -> mais fraco (muitos)
    (51, "cerca de metade"),
    (59, "cerca de metade"),
    (60, "cerca de metade"),
    (61, "a maioria"),
    (79, "a maioria"),
    (80, "a maioria"),       # borda: a maioria×quase todos empatam -> mais fraco (a maioria)
    (81, "quase todos"),
    (100, "quase todos"),
])
def test_rotulo_quantificador_resolve_faixas_e_bordas(pct, esperado):
    assert _rotulo_quantificador(pct) == esperado


def test_fracao_percentual_arredonda():
    assert _fracao_percentual(15, 30) == 50
    assert _fracao_percentual(1, 3) == 33      # 33.33... -> 33
    assert _fracao_percentual(2, 3) == 67      # 66.66... -> 67
    assert _fracao_percentual(0, 0) == 0       # sem denominador válido


def test_fracao_e_rotulo_a_partir_de_tema_dict():
    tema = {"mencoes_aproximadas": 21, "n_reviews_analisadas": 30}  # 70%
    pct, rotulo = _fracao_e_rotulo(tema)
    assert pct == 70
    assert rotulo == "a maioria"  # NÃO "quase todos" — é o bug relatado


# --- v1.2.3: serialização carrega fracao + rótulo pré-computados ---

def test_serializacao_carrega_fracao_e_rotulo_por_tema():
    out = _output_completo()  # tema único: 3/5 = 60%
    ser = _serialize_output_for_narrator(out)
    assert "fracao: 60%" in ser
    assert 'rótulo_quantificador: "cerca de metade"' in ser


# --- v1.2.3: rede de segurança — bucket sem tema >=80% + "quase todos" na prosa ---

def test_quantificador_forte_sem_lastro_marca_flag_e_retenta():
    # nenhum tema do filme tem fração >= 80% (o único tema é 3/5 = 60%)
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return '{"narrativa": "entre quem nao gostou, quase todos citaram o ritmo; ja entre quem gostou, muitos elogiaram a direcao."}'

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is True
    assert len(systems) == 2  # houve retentativa
    assert "rótulo_quantificador correto" in systems[1]


def test_quantificador_forte_com_lastro_nao_marca_flag():
    # tema com fração >= 80% dá lastro para "quase todos"
    buckets = [_bucket("positivas", 30, "completo",
                       [Tema("direção", 27, 30, "elogio grande")],  # 90%
                       "as reviews positivas elogiam a direção", 5)]
    out = build_output("filme-x", buckets, "2026-01-01", {}, 30)
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return '{"narrativa": "entre quem amou, quase todos elogiam a direção deste filme."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.quantificador_suspeito is False
    assert len(calls) == 1  # sem retentativa


def test_quantificador_fraco_nunca_dispara_a_checagem():
    # "alguns"/"muitos"/"a maioria" nunca acionam essa rede de segurança,
    # mesmo sem nenhum tema forte — ela é deliberadamente restrita a
    # "quase todos"/"praticamente todos"
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return '{"narrativa": "entre quem nao gostou, a maioria citou o ritmo; ja entre quem gostou, alguns elogiaram a direcao."}'

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is False
    assert len(calls) == 1


def test_prevalencia_marcador_persistente_marca_flag_e_retenta():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        # sempre compara tamanhos ("igualmente expressivo" + "minoria")
        return ('{"narrativa": "quem nao gostou forma um grupo consideravel e quem '
                'gostou e igualmente expressivo; ja as medianas sao uma minoria."}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.prevalencia_suspeita is True
    assert len(systems) == 2                      # houve retentativa
    assert "os tamanhos vêm da cota" in systems[1]  # reforço de prevalência anexado


def test_prevalencia_prosa_limpa_nao_flagga():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": "entre quem nao gostou, o ritmo e o roteiro foram '
                'os alvos; mais da metade das reviews negativas analisadas citou o '
                'humor fraco. ja entre quem amou, a direcao e as atuacoes brilham '
                'para esse grupo, sem que se possa dizer nada sobre o publico geral."}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.prevalencia_suspeita is False
    assert len(calls) == 1                        # sem retentativa


# --- v1.3.0: três movimentos + ficha TMDB ---

def _ficha(overview="Um detetive investiga uma série de assassinatos estranhos."):
    return {
        "titulo": "Cure", "sinopse_oficial": overview, "sinopse_fallback_en": False,
        "generos": ["Suspense", "Terror"], "duracao_min": 111,
        "diretor": "Kiyoshi Kurosawa", "ano": 1997, "fonte": "tmdb",
    }


def test_prompt_contem_os_tres_movimentos_nesta_ordem():
    idx1 = NARRATOR_SYSTEM_PROMPT.index("MOVIMENTO 1")
    idx2 = NARRATOR_SYSTEM_PROMPT.index("MOVIMENTO 2")
    idx3 = NARRATOR_SYSTEM_PROMPT.index("MOVIMENTO 3")
    assert idx1 < idx2 < idx3
    assert "O FILME" in NARRATOR_SYSTEM_PROMPT
    assert "A EXPERIÊNCIA" in NARRATOR_SYSTEM_PROMPT
    assert "O CONTRASTE" in NARRATOR_SYSTEM_PROMPT


def test_prompt_alvo_de_tamanho_atualizado_para_250_400():
    assert "250 e 400 palavras" in NARRATOR_SYSTEM_PROMPT
    assert "200 e 350 palavras" not in NARRATOR_SYSTEM_PROMPT


def test_prompt_ainda_contem_invariantes_pre_existentes():
    # todas as invariantes da v1.2.x continuam de pé na v1.3.0
    assert "TAMANHO DOS GRUPOS" in NARRATOR_SYSTEM_PROMPT
    assert "QUANTIFICADOR PRÉ-COMPUTADO" in NARRATOR_SYSTEM_PROMPT
    assert "PROIBIDO usar um quantificador MAIS FORTE" in NARRATOR_SYSTEM_PROMPT
    assert "SEM aspas de citação" in NARRATOR_SYSTEM_PROMPT


def test_serializacao_inclui_ficha_quando_presente():
    out = _output_completo()
    out["ficha"] = _ficha()
    ser = _serialize_output_for_narrator(out)
    assert "FICHA TÉCNICA" in ser
    assert "Kiyoshi Kurosawa" in ser
    assert "Cure" in ser
    assert "Um detetive investiga" in ser


def test_serializacao_omite_ficha_quando_ausente():
    out = _output_completo()
    out["ficha"] = None
    ser = _serialize_output_for_narrator(out)
    assert "FICHA TÉCNICA" not in ser


def test_narrador_recebe_ficha_e_nao_vaza_reviews_brutas():
    out = _output_completo(review_text="SPOILER_BRUTO")
    out["ficha"] = _ficha()
    capturado = {}

    def fake(system, user, model):
        capturado["user"] = user
        return '{"narrativa": "Cure e um filme de Kiyoshi Kurosawa. Entre quem nao gostou, o ritmo incomodou; ja entre quem gostou, a direcao foi elogiada."}'

    narrate_output(out, client_call=fake, model="m")
    assert "SPOILER_BRUTO" not in capturado["user"]
    assert "FICHA TÉCNICA" in capturado["user"]


def test_validacoes_de_prosa_seguem_ativas_com_ficha_presente():
    # idioma/escopo/prevalencia/quantificador continuam checados mesmo com
    # ficha no relatório — a ficha não desliga nenhuma validação existente.
    out = _output_completo()
    out["ficha"] = _ficha()

    def fake(system, user, model):
        return '{"narrativa": "the film has a slow pace according to the negative reviews, while positive ones praise the direction with enthusiasm and clear admiration for the craft."}'

    r = narrate_output(out, client_call=fake, model="m")
    assert r.idioma_invalido is True


# --- v1.3.1: regra do MOVIMENTO 2 reescrita (categoria/presença/não-contradição) ---

def test_prompt_contem_os_tres_criterios_do_movimento_2():
    assert "CRITÉRIO DE CATEGORIA" in NARRATOR_SYSTEM_PROMPT
    assert "CRITÉRIO DE PRESENÇA" in NARRATOR_SYSTEM_PROMPT
    assert "CRITÉRIO DE NÃO-CONTRADIÇÃO" in NARRATOR_SYSTEM_PROMPT
    assert "PELO MENOS DOIS grupos" in NARRATOR_SYSTEM_PROMPT
    assert "PROIBIDO qualquer" in NARRATOR_SYSTEM_PROMPT


def test_prompt_contem_exemplo_positivo_e_negativo():
    assert "EXEMPLO POSITIVO" in NARRATOR_SYSTEM_PROMPT
    assert "EXEMPLO NEGATIVO" in NARRATOR_SYSTEM_PROMPT
    # o caso real observado (the-invite-2026) está documentado no prompt
    assert "atuações marcantes" in NARRATOR_SYSTEM_PROMPT
    assert "roteiro inteligente" in NARRATOR_SYSTEM_PROMPT
    assert "atuações e direção questionáveis" in NARRATOR_SYSTEM_PROMPT


def test_prompt_pede_consensos_usados_no_formato_de_saida():
    assert "consensos_usados" in NARRATOR_SYSTEM_PROMPT
    assert "grupos_de_origem" in NARRATOR_SYSTEM_PROMPT
    assert "temas_de_origem" in NARRATOR_SYSTEM_PROMPT


# --- v1.3.1: parsing/telemetria de consensos_usados ---

def test_consensos_usados_validos_sao_parseados_e_persistidos():
    out = _output_completo()  # tema único "ritmo" em negativas/medianas/positivas

    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; '
                'ja entre quem gostou, a direcao foi elogiada.", '
                '"consensos_usados": [{"propriedade": "ritmo lento", '
                '"grupos_de_origem": ["negativas", "positivas"], '
                '"temas_de_origem": ["ritmo"]}]}')

    r = narrate_output(out, client_call=fake, model="m")
    assert r.consenso_suspeito is False
    assert len(r.consensos_usados) == 1
    assert r.consensos_usados[0]["propriedade"] == "ritmo lento"
    assert r.consensos_usados[0]["grupos_de_origem"] == ["negativas", "positivas"]


def test_consensos_vazio_e_valido_sem_retentativa():
    out = _output_completo()
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; '
                'ja entre quem gostou, a direcao foi elogiada.", '
                '"consensos_usados": []}')

    r = narrate_output(out, client_call=fake, model="m")
    assert r.consenso_suspeito is False
    assert r.consensos_usados == []
    assert len(calls) == 1  # sem retentativa


def test_consenso_com_grupo_inexistente_dispara_retentativa_e_flag():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; '
                'ja entre quem gostou, a direcao foi elogiada.", '
                '"consensos_usados": [{"propriedade": "ritmo", '
                '"grupos_de_origem": ["neutras"], "temas_de_origem": ["ritmo"]}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.consenso_suspeito is True
    assert len(systems) == 2  # houve retentativa
    assert "grupos e nomes de tema que existem" in systems[1]


def test_consenso_com_tema_inexistente_dispara_retentativa_e_flag():
    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; '
                'ja entre quem gostou, a direcao foi elogiada.", '
                '"consensos_usados": [{"propriedade": "roteiro", '
                '"grupos_de_origem": ["negativas"], '
                '"temas_de_origem": ["tema que nao existe"]}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.consenso_suspeito is True


def test_consenso_corrigido_na_retentativa_zera_flag():
    respostas = [
        ('{"narrativa": "primeira tentativa.", "consensos_usados": '
         '[{"propriedade": "x", "grupos_de_origem": ["inexistente"], "temas_de_origem": []}]}'),
        ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja entre '
         'quem gostou, a direcao foi elogiada.", "consensos_usados": '
         '[{"propriedade": "ritmo", "grupos_de_origem": ["negativas"], '
         '"temas_de_origem": ["ritmo"]}]}'),
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.consenso_suspeito is False
    assert r.consensos_usados[0]["propriedade"] == "ritmo"


def test_consensos_ausentes_no_json_nao_quebra_e_nao_marca_suspeito():
    # compatibilidade: resposta sem o campo novo (formato v1.3.0) continua
    # válida, consensos_usados vira [] e nada é sinalizado.
    def fake(system, user, model):
        return '{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja entre quem gostou, a direcao foi elogiada."}'

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.consenso_suspeito is False
    assert r.consensos_usados == []


# =====================================================================
# v1.4.1 — telemetria POR PAR {quantificador, tema}
# =====================================================================
# A 3ª ocorrência do mesmo modo de falha: na v1.4.0 a narrativa de
# `the-invite-2026` usou "Quase todos" para "Atuações e química do elenco"
# (20/30 = 67%, rótulo "a maioria"). A rede da v1.2.3 é de nível de BUCKET e
# não pega isso, porque outro tema do mesmo grupo tinha 83% e dava lastro.

def test_prompt_pede_a_declaracao_de_quantificadores_usados():
    assert "quantificadores_usados" in NARRATOR_SYSTEM_PROMPT
    assert "DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES" in NARRATOR_SYSTEM_PROMPT
    # o par declarado é {quantificador, tema}, com o tema copiado literalmente
    assert '"quantificador"' in NARRATOR_SYSTEM_PROMPT
    assert "NOME EXATO do tema" in NARRATOR_SYSTEM_PROMPT


@pytest.mark.parametrize("expressao,forca", [
    ("poucos", 0), ("poucas reviews", 0),
    ("alguns", 1), ("uma parte", 1),
    ("muitos", 2), ("boa parte", 2),
    ("cerca de metade", 3),
    ("a maioria", 4), ("mais da metade", 4),
    ("quase todos", 5), ("quase todos os elogios", 5),
    ("praticamente todas", 5),
    ("um punhado disperso", None),   # irreconhecível -> não comparável
])
def test_forca_declarada_resolve_a_escala_do_prompt(expressao, forca):
    assert _forca_declarada(expressao) == forca


def test_forca_declarada_prefere_a_chave_mais_longa():
    # "mais da metade" (4) não pode ser lido como "metade" (3)
    assert _forca_declarada("mais da metade") == 4
    assert _forca_declarada("cerca de metade") == 3


def test_par_valido_nao_flagga_nem_retenta():
    # tema "ritmo" = 3/5 = 60% -> rótulo "cerca de metade"
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": "entre quem nao gostou, cerca de metade citou o '
                'ritmo lento; ja entre quem gostou, a direcao foi elogiada.", '
                '"consensos_usados": [], "quantificadores_usados": '
                '[{"quantificador": "cerca de metade", "tema": "ritmo"}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is False
    assert len(calls) == 1                       # sem retentativa
    assert r.quantificadores_usados == [
        {"quantificador": "cerca de metade", "tema": "ritmo"}]


def test_quantificador_declarado_mais_fraco_e_permitido():
    """O prompt autoriza descer de força; só subir é violação."""
    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, alguns citaram o ritmo '
                'lento; ja entre quem gostou, a direcao foi elogiada.", '
                '"quantificadores_usados": [{"quantificador": "alguns", '
                '"tema": "ritmo"}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is False


def test_quantificador_declarado_inflado_retenta_e_flagga():
    """O defeito do the-invite, reproduzido: quantificador MAIS FORTE que o
    rótulo pré-computado do tema que o próprio narrador declarou."""
    systems = []

    def fake(system, user, model):
        systems.append(system)
        # "a maioria" (força 4) > "cerca de metade" (força 3) do tema ritmo
        return ('{"narrativa": "entre quem nao gostou, a maioria citou o ritmo '
                'lento; ja entre quem gostou, a direcao foi elogiada.", '
                '"quantificadores_usados": [{"quantificador": "a maioria", '
                '"tema": "ritmo"}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is True
    assert len(systems) == 2                     # houve retentativa
    assert "rótulo_quantificador do tema citado" in systems[1]


def test_quantificador_declarado_com_tema_inexistente_retenta_e_flagga():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return ('{"narrativa": "entre quem nao gostou, alguns citaram o ritmo; '
                'ja entre quem gostou, a direcao foi elogiada.", '
                '"quantificadores_usados": [{"quantificador": "alguns", '
                '"tema": "tema que nao existe"}]}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is True
    assert len(systems) == 2
    assert "copiados literalmente do relatório" in systems[1]


def test_quantificador_declarado_corrigido_na_retentativa_zera_a_flag():
    respostas = [
        ('{"narrativa": "entre quem nao gostou, a maioria citou o ritmo.", '
         '"quantificadores_usados": [{"quantificador": "a maioria", '
         '"tema": "ritmo"}]}'),
        ('{"narrativa": "entre quem nao gostou, cerca de metade citou o ritmo; '
         'ja entre quem gostou, a direcao foi elogiada.", '
         '"quantificadores_usados": [{"quantificador": "cerca de metade", '
         '"tema": "ritmo"}]}'),
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is False
    assert r.quantificadores_usados[0]["quantificador"] == "cerca de metade"


def test_lista_vazia_de_quantificadores_e_valida_sem_retentativa():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja '
                'entre quem gostou, a direcao foi elogiada.", '
                '"quantificadores_usados": []}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is False
    assert r.quantificadores_usados == []
    assert len(calls) == 1


def test_campo_quantificadores_ausente_no_json_nao_quebra():
    """Compatibilidade: resposta no formato v1.4.0 (sem o campo novo) segue
    válida — vira [] e nada é sinalizado."""
    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja '
                'entre quem gostou, a direcao foi elogiada."}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificadores_usados == []
    assert r.quantificador_suspeito is False


def test_expressao_irreconhecivel_nao_e_tratada_como_violacao():
    """Limitação documentada: sem casar a expressão na escala, o código não
    tem como julgar força — e prefere não flaggar prosa possivelmente certa."""
    out = _output_completo()
    assert _quantificadores_validos(
        [{"quantificador": "um punhado disperso", "tema": "ritmo"}], out) is True


def test_rede_de_bucket_da_v1_2_3_continua_ativa():
    """A checagem nova SOMA à antiga, não a substitui: "quase todos" sem
    nenhum tema >=80% segue flaggando mesmo sem par declarado."""
    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, quase todos citaram o '
                'ritmo lento do filme ao longo da projecao inteira.", '
                '"quantificadores_usados": []}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.quantificador_suspeito is True


def test_regressao_the_invite_quase_todos_com_lastro_de_outro_tema():
    """O defeito REAL da v1.4.0, reproduzido: "quase todos" para um tema de
    67% enquanto OUTRO tema do mesmo grupo tem 83%. A rede de bucket da
    v1.2.3 acha lastro e deixa passar; a checagem por par (v1.4.1) pega."""
    temas = [
        Tema("Direção e roteiro (geral)", 25, 30, "elogio amplo à direção"),  # 83%
        Tema("Atuações e química do elenco", 20, 30, "destaque para o elenco"),  # 67%
    ]
    buckets = [_bucket("positivas", 30, "completo", temas,
                       "as reviews positivas elogiam a direção", 30)]
    out = build_output("the-invite-2026", buckets, "2026-01-01", {}, 100)

    # a rede de bucket sozinha não flagga (há tema >= 80% no filme)
    from espectro24.synthesize import _algum_tema_tem_fracao_forte
    assert _algum_tema_tem_fracao_forte(out) is True

    systems = []

    def fake(system, user, model):
        systems.append(system)
        return ('{"narrativa": "quase todos salientam o desempenho do elenco e '
                'a quimica entre os atores deste filme.", '
                '"quantificadores_usados": [{"quantificador": "Quase todos", '
                '"tema": "Atuações e química do elenco"}]}')

    r = narrate_output(out, client_call=fake, model="m")
    assert r.quantificador_suspeito is True       # 67% -> rótulo "a maioria"
    assert len(systems) == 2


def test_conferencia_quantificador_devolve_fracao_e_rotulo_reais():
    out = _output_completo()
    assert conferencia_quantificador(out, "ritmo") == (60, "cerca de metade")
    assert conferencia_quantificador(out, "inexistente") is None


def test_tema_repetido_em_grupos_resolve_pela_forca_mais_alta():
    """Par declarado não diz de qual grupo veio; na ambiguidade a checagem
    aceita o rótulo mais forte entre os homônimos (não flagga prosa certa)."""
    buckets = [
        _bucket("negativas", 50, "completo", [Tema("ritmo", 1, 10, "poucos")],
                "as reviews negativas comentam o ritmo", 10),      # 10% -> alguns
        _bucket("positivas", 30, "completo", [Tema("ritmo", 9, 10, "quase todos")],
                "as reviews positivas comentam o ritmo", 10),      # 90% -> quase todos
    ]
    out = build_output("filme-y", buckets, "2026-01-01", {}, 20)
    assert _quantificadores_validos(
        [{"quantificador": "a maioria", "tema": "ritmo"}], out) is True


# --- v1.4.1: MOVIMENTO 2 pode ser OMITIDO (pressão de preenchimento) ---
# Diagnóstico do defeito: o the-invite tem poucos temas descritivos e o
# narrador completou o espaço com juízo de qualidade hedgeado ("estilo visual
# eficaz", "abordagem arrojada"), violando o critério de categoria.

def test_prompt_autoriza_explicitamente_a_omissao_do_movimento_2():
    assert "OMISSÃO AUTORIZADA" in NARRATOR_SYSTEM_PROMPT
    assert "MENOS DE DUAS propriedades" in NARRATOR_SYSTEM_PROMPT
    assert "OMITIR É O COMPORTAMENTO CORRETO" in NARRATOR_SYSTEM_PROMPT
    # nomear o defeito: preencher com juízo hedgeado é PIOR que omitir
    assert "é PIOR do que não ter o movimento" in NARRATOR_SYSTEM_PROMPT
    assert "estilo visual eficaz" in NARRATOR_SYSTEM_PROMPT
    assert "abordagem arrojada" in NARRATOR_SYSTEM_PROMPT
    # e o contrato de saída quando ele é omitido
    assert "lista VAZIA ([])" in NARRATOR_SYSTEM_PROMPT


def test_prompt_autoriza_omissao_nas_duas_variantes_da_regra_c():
    from espectro24.synthesize import build_narrator_prompt
    for com_dist in (False, True):
        assert "OMISSÃO AUTORIZADA" in build_narrator_prompt(com_dist)


def test_movimento_2_omitido_com_consensos_vazios_nao_e_suspeito():
    """Omitir é o comportamento CORRETO — `consensos_usados: []` não pode
    disparar nem retentativa nem flag."""
    calls = []

    def fake(system, user, model):
        calls.append(1)
        # narrativa sem movimento 2: premissa -> contraste, direto
        return ('{"narrativa": "este filme e um drama dirigido por alguem. '
                'entre quem nao gostou, o ritmo incomodou; ja entre quem '
                'gostou, a direcao foi elogiada com entusiasmo.", '
                '"consensos_usados": [], "quantificadores_usados": []}')

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.consenso_suspeito is False
    assert r.consensos_usados == []
    assert len(calls) == 1                       # sem retentativa


def test_prevalencia_corrigida_na_retentativa_zera_flag():
    respostas = [
        '{"narrativa": "a recepcao e polarizada: um grupo grande e uma minoria."}',
        '{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja entre quem gostou, a direcao foi celebrada por esse grupo."}',
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output_completo(), client_call=fake, model="m")
    assert r.prevalencia_suspeita is False
    assert "entre quem nao gostou" in r.texto
