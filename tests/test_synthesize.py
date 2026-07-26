"""Síntese LLM: parsing defensivo, retentativa, skip de bucket sem análise."""
from espectro24.models import BucketResult, LevelResult, Review
from espectro24.synthesize import _remover_aspas, build_system_prompt, synthesize_bucket


def _bucket_com_reviews(n=5):
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [
        Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i} completa",
               truncated=False, full_text_url=None, spoiler=False,
               full_text=f"review {i} completa")
        for i in range(n)
    ]
    return BucketResult(nome="positivas", alvo=30, modo="reduzido", niveis=[lvl])


def test_parsing_defensivo_com_fences():
    calls = []

    def fake(system, user, model):
        calls.append(user)
        return '```json\n{"bucket":"positivas","temas":[' \
               '{"tema":"fotografia","mencoes_aproximadas":3,' \
               '"n_reviews_analisadas":5,"exemplo_parafraseado":"elogios à fotografia"}],' \
               '"observacao_geral":"bem recebido"}\n```'

    b = synthesize_bucket(_bucket_com_reviews(), client_call=fake)
    assert len(calls) == 1
    assert b.temas[0].tema == "fotografia"
    assert b.observacao_geral == "bem recebido"


def test_retentativa_em_json_invalido():
    respostas = ["isto não é json", '{"temas":[],"observacao_geral":"ok"}']

    def fake(system, user, model):
        return respostas.pop(0)

    b = synthesize_bucket(_bucket_com_reviews(), client_call=fake)
    assert b.observacao_geral == "ok"          # usou a 2ª resposta


def test_json_invalido_duas_vezes_nao_quebra():
    def fake(system, user, model):
        return "lixo"

    b = synthesize_bucket(_bucket_com_reviews(), client_call=fake)
    assert b.temas == []
    assert "Falha" in b.observacao_geral


def test_bucket_sem_analise_nao_chama_llm():
    called = []

    def fake(system, user, model):
        called.append(1)
        return "{}"

    b = BucketResult(nome="negativas", alvo=50, modo="sem_analise", niveis=[])
    synthesize_bucket(b, client_call=fake)
    assert called == []                        # LLM não é chamado


def test_temas_ordenados_e_limitados_a_6():
    def fake(system, user, model):
        temas = ",".join(
            f'{{"tema":"t{i}","mencoes_aproximadas":{i},'
            f'"n_reviews_analisadas":5,"exemplo_parafraseado":"e"}}'
            for i in range(8)
        )
        return f'{{"temas":[{temas}],"observacao_geral":"o"}}'

    b = synthesize_bucket(_bucket_com_reviews(), client_call=fake)
    assert len(b.temas) == 6                    # máx 6
    mencoes = [t.mencoes_aproximadas for t in b.temas]
    assert mencoes == sorted(mencoes, reverse=True)   # decrescente


def test_nunca_envia_texto_truncado_ao_llm():
    # todas as reviews enviadas devem ter texto completo (full_text setado)
    from espectro24.synthesize import build_user_message
    b = _bucket_com_reviews()
    msg = build_user_message(b)
    for r in b.reviews_analisadas:
        assert r.full_text is not None
        assert r.effective_text in msg


# --- Tarefa 3 (v1.1.1): código é a autoridade do denominador ---

def test_denominador_do_llm_e_sempre_ignorado():
    # bucket real tem 5 reviews; LLM mente e diz que analisou 50 (o alvo!)
    def fake(system, user, model):
        return ('{"temas":[{"tema":"ritmo","mencoes_aproximadas":3,'
                '"n_reviews_analisadas":50,"exemplo_parafraseado":"e"}],'
                '"observacao_geral":"o"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.temas[0].n_reviews_analisadas == 5      # real, nunca 50 (o alvo)


def test_numerador_maior_que_denominador_e_clampado_e_registrado():
    # bucket com 5 reviews; LLM alucina 12 menções (impossível)
    def fake(system, user, model):
        return ('{"temas":[{"tema":"fotografia","mencoes_aproximadas":12,'
                '"n_reviews_analisadas":5,"exemplo_parafraseado":"e"}],'
                '"observacao_geral":"o"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    t = b.temas[0]
    assert t.mencoes_aproximadas == 5                 # clampado ao teto real
    assert t.mencoes_clampadas is True
    assert t.mencoes_valor_original == 12              # valor original preservado p/ visibilidade


def test_numerador_negativo_e_clampado_para_zero():
    def fake(system, user, model):
        return ('{"temas":[{"tema":"roteiro","mencoes_aproximadas":-4,'
                '"n_reviews_analisadas":5,"exemplo_parafraseado":"e"}],'
                '"observacao_geral":"o"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    t = b.temas[0]
    assert t.mencoes_aproximadas == 0
    assert t.mencoes_clampadas is True
    assert t.mencoes_valor_original == -4


def test_numerador_dentro_do_range_nao_e_marcado_como_clampado():
    def fake(system, user, model):
        return ('{"temas":[{"tema":"atuações","mencoes_aproximadas":3,'
                '"n_reviews_analisadas":999,"exemplo_parafraseado":"e"}],'
                '"observacao_geral":"o"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    t = b.temas[0]
    assert t.mencoes_aproximadas == 3
    assert t.mencoes_clampadas is False
    assert t.mencoes_valor_original is None


# --- Tarefa v1.1.2: preâmbulo de papel parametrizado por bucket ---

def test_preambulo_contem_nome_e_intervalo_de_notas_por_bucket():
    casos = {
        "negativas": "0.5–2.5 estrelas",
        "medianas": "3–3.5 estrelas",
        "positivas": "4–5 estrelas",
    }
    for nome, intervalo_esperado in casos.items():
        prompt = build_system_prompt(nome)
        assert f'"{nome}"' in prompt or f"a faixa \"{nome}\"" in prompt
        assert intervalo_esperado in prompt
        assert "NÃO representa a recepção geral do filme" in prompt
        assert "PROIBIDO generalizar" in prompt


def test_preambulo_ainda_contem_instrucoes_invariantes():
    prompt = build_system_prompt("negativas")
    assert "PROIBIDO mencionar eventos da trama" in prompt   # anti-spoiler
    assert "sempre em pt-BR" in prompt or "SEMPRE em pt-BR" in prompt
    assert "aspas" in prompt.lower()                          # regra nova


# --- Tarefa v1.1.2: validação pós-parsing — ASPAS (mecânica, sem retentativa) ---

def test_aspas_sao_removidas_mecanicamente_e_flag_registrada():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
                '"n_reviews_analisadas":5,'
                '"exemplo_parafraseado":"um review disse que o filme era '
                '\\"incrível e emocionante\\""}],'
                '"observacao_geral":"este grupo elogia o roteiro"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    t = b.temas[0]
    assert '"' not in t.exemplo_parafraseado
    assert t.aspas_removidas is True
    assert len(calls) == 1  # SEM retentativa — correção mecânica basta


def test_sem_aspas_nao_marca_flag():
    def fake(system, user, model):
        return ('{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
                '"n_reviews_analisadas":5,'
                '"exemplo_parafraseado":"este grupo elogia o roteiro sem citar '
                'diretamente nenhuma review"}],'
                '"observacao_geral":"este grupo elogia o roteiro"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.temas[0].aspas_removidas is False


# --- v1.7.1 — bugfix: contrabarra residual da remoção de aspas ---

def test_remover_aspas_nao_deixa_contrabarra_residual():
    """Caso real publicado em `cure` e `the-invite-2026` (v1.7.0): o texto
    trazia uma citação ESCAPADA ("\\"A Cura\\""), e a remoção mecânica
    trocava só o caractere de aspas por "" — a contrabarra de escape
    sobrevivia, publicando "\\A Cura\\" no texto final."""
    texto = ('Kiyoshi Kurosawa nos entrega um thriller de crime e terror de '
            '1997, em \\"A Cura\\". Nele, um detetive...')
    limpo, removida = _remover_aspas(texto)
    assert removida is True
    assert "\\" not in limpo
    assert '"' not in limpo
    assert "em A Cura. Nele" in limpo


def test_remover_aspas_ainda_remove_aspas_normais_sem_contrabarra():
    """Não regride o caso comum (sem escape) que já funcionava."""
    texto = 'o filme é descrito como "hipnótico" pela crítica'
    limpo, removida = _remover_aspas(texto)
    assert removida is True
    assert limpo == "o filme é descrito como hipnótico pela crítica"


# --- Tarefa v1.1.2: validação pós-parsing — IDIOMA (1 retentativa) ---

def test_idioma_em_ingles_aciona_retentativa_e_registra_flag_se_persistir():
    def fake(system, user, model):
        # sempre devolve o mesmo texto em inglês, mesmo na retentativa
        return ('{"temas":[{"tema":"pacing and structure",'
                '"mencoes_aproximadas":2,"n_reviews_analisadas":5,'
                '"exemplo_parafraseado":"the pacing of the movie is slow and '
                'the editing feels disjointed throughout"}],'
                '"observacao_geral":"this group criticizes the pacing and '
                'the editing of the film"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.idioma_invalido is True


def test_idioma_pt_br_nao_aciona_retentativa():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"temas":[{"tema":"ritmo e edição",'
                '"mencoes_aproximadas":2,"n_reviews_analisadas":5,'
                '"exemplo_parafraseado":"este grupo destaca que o ritmo do '
                'filme é lento e que a edição parece desconexa em vários '
                'momentos da narrativa"}],'
                '"observacao_geral":"este grupo de reviews critica o ritmo '
                'e a edição do filme, mas reconhece méritos técnicos"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.idioma_invalido is False
    assert len(calls) == 1  # texto já em pt-BR -> sem retentativa


def test_idioma_corrigido_na_retentativa_zera_a_flag():
    respostas = [
        '{"temas":[{"tema":"pacing","mencoes_aproximadas":2,'
        '"n_reviews_analisadas":5,"exemplo_parafraseado":"the pacing is '
        'slow and the editing feels disjointed"}],'
        '"observacao_geral":"this group criticizes the pacing of the film"}',
        '{"temas":[{"tema":"ritmo e edição","mencoes_aproximadas":2,'
        '"n_reviews_analisadas":5,"exemplo_parafraseado":"este grupo '
        'destaca que o ritmo é lento e a edição parece desconexa"}],'
        '"observacao_geral":"este grupo de reviews critica o ritmo e a '
        'edição do filme"}',
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.idioma_invalido is False
    assert b.temas[0].tema == "ritmo e edição"  # usou o resultado da retentativa


# --- Tarefa v1.1.2: validação pós-parsing — ESCOPO (1 retentativa) ---

def test_escopo_generalizado_aciona_retentativa_e_registra_flag_se_persistir():
    def fake(system, user, model):
        return ('{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
                '"n_reviews_analisadas":5,"exemplo_parafraseado":"este '
                'grupo critica o roteiro por ser confuso e superficial"}],'
                '"observacao_geral":"a maioria dos críticos considera o '
                'filme um fracasso completo em todos os aspectos técnicos"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.escopo_suspeito is True


def test_escopo_referenciando_o_grupo_nao_aciona_retentativa():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
                '"n_reviews_analisadas":5,"exemplo_parafraseado":"este '
                'grupo critica o roteiro por ser confuso e superficial"}],'
                '"observacao_geral":"as reviews negativas apontam para um '
                'roteiro confuso e personagens rasos"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.escopo_suspeito is False
    assert len(calls) == 1


def test_escopo_corrigido_na_retentativa_zera_a_flag():
    respostas = [
        '{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
        '"n_reviews_analisadas":5,"exemplo_parafraseado":"critica ao '
        'roteiro"}],'
        '"observacao_geral":"a maioria dos críticos considera o filme um '
        'fracasso"}',
        '{"temas":[{"tema":"roteiro","mencoes_aproximadas":2,'
        '"n_reviews_analisadas":5,"exemplo_parafraseado":"critica ao '
        'roteiro"}],'
        '"observacao_geral":"as reviews negativas apontam um roteiro '
        'fraco"}',
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert b.escopo_suspeito is False
    assert b.observacao_geral == "as reviews negativas apontam um roteiro fraco"


def test_idioma_e_escopo_ruins_juntos_disparam_uma_unica_retentativa_combinada():
    # ambos os problemas na 1a resposta -> apenas 1 chamada extra (não 2)
    calls = []

    def fake(system, user, model):
        calls.append(1)
        if len(calls) == 1:
            return ('{"temas":[{"tema":"pacing","mencoes_aproximadas":2,'
                    '"n_reviews_analisadas":5,"exemplo_parafraseado":"the '
                    'pacing is slow"}],'
                    '"observacao_geral":"the majority of critics consider '
                    'this a failure"}')
        return ('{"temas":[{"tema":"ritmo","mencoes_aproximadas":2,'
                '"n_reviews_analisadas":5,"exemplo_parafraseado":"este '
                'grupo acha o ritmo lento"}],'
                '"observacao_geral":"este grupo de reviews considera o '
                'ritmo arrastado"}')

    b = synthesize_bucket(_bucket_com_reviews(n=5), client_call=fake)
    assert len(calls) == 2                 # 1 chamada normal + 1 retentativa combinada
    assert b.idioma_invalido is False
    assert b.escopo_suspeito is False
