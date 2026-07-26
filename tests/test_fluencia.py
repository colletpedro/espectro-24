"""[v1.5.0] Fluência do narrador (ritmo/registro) + marcação de perspectiva —
mock/fixtures, ZERO rede.

Cobre: cálculo de métricas de fluência sobre textos sintéticos (monótono vs.
variado); classificação de marcacao_perspectiva a partir de shares (bordas
dominante/3 e dominante/10, caso 40/30/30 -> nenhuma); validação dos
marcadores declarados (ausente, trecho inexistente, posição tardia em
"antecipada"); presença das regras novas e do par antes/depois no prompt;
invariantes anteriores (peso, quantificador, consensos) seguem presentes.
"""
import pytest

from conftest import fx

from espectro24.models import BucketResult, Distribuicao, LevelResult, Review, Tema
from espectro24.parser import parse_rating_histogram
from espectro24.render import build_output, render_terminal
from espectro24.synthesize import (
    NARRATOR_SYSTEM_PROMPT,
    NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO,
    _ancora_de_grupo,
    _ancoragem_de_peso_ok,
    _dominante_share,
    _marcacao_perspectiva,
    _marcacoes_por_bucket,
    _marcadores_validos,
    _metricas_fluencia,
    build_narrator_prompt,
    narrate_output,
)


# =====================================================================
# métricas de fluência — textos sintéticos
# =====================================================================

_MONOTONO = (
    "A grande maioria das notas elogia intensamente a direção do filme e o "
    "roteiro, destacando a habilidade de equilibrar comédia e drama. Uma "
    "minoria das notas reconhece a competência técnica, mas considera que a "
    "repetição das situações torna a experiência cansativa na segunda "
    "metade. Uma pequena minoria classifica o humor como previsível e "
    "aponta os personagens como caricaturas rasas e sem nuance alguma."
)

_VARIADO = (
    "Quem gostou é a grande maioria das notas (~79%), e essa turma repete "
    "sempre a mesma dupla: o jeito como a direção equilibra comédia e drama "
    "sem deixar nenhum dos dois perder força. No meio-termo, uma minoria "
    "das notas (~18%). Só que até certo ponto. Para esse grupo as "
    "situações começam a se repetir, e o filme estica. Já uma pequena "
    "minoria (~3%) não entra na brincadeira. Para eles o humor é "
    "previsível do começo ao fim."
)


def test_metricas_texto_monotono_dispara_gatilhos():
    m = _metricas_fluencia(_MONOTONO)
    # 3 frases de comprimento parecido (25-35 palavras), sem frase curta
    assert m["n_frases"] == 3
    assert m["frase_mais_curta"] > 10
    assert m["cv_comprimento"] < 0.40


def test_metricas_texto_variado_nao_dispara_gatilhos():
    m = _metricas_fluencia(_VARIADO)
    assert m["frase_mais_curta"] <= 10
    assert m["cv_comprimento"] >= 0.40
    assert m["aberturas_repetidas"] == 0


def test_metricas_contam_verbos_de_reporte():
    texto = "As reviews elogiam o filme. Também destacam o ritmo. Muitos apontam o roteiro."
    m = _metricas_fluencia(texto)
    assert m["verbos_reporte"] == 3  # elogiam, destacam, apontam


def test_metricas_contam_adverbios_intensificadores():
    texto = "O filme emociona profundamente. Também assusta intensamente o público."
    m = _metricas_fluencia(texto)
    assert m["adverbios_mente"] == 2


def test_metricas_nao_conta_adverbio_fora_da_lista_fechada():
    # "praticamente"/"geralmente" não são intensificadores — heurística
    # deliberadamente restrita (mesma política das demais do módulo)
    texto = "O filme é praticamente perfeito e geralmente bem avaliado."
    m = _metricas_fluencia(texto)
    assert m["adverbios_mente"] == 0


def test_metricas_detectam_abertura_repetida():
    texto = "O filme prende do início ao fim. O roteiro surpreende a cada cena."
    m = _metricas_fluencia(texto)
    assert m["aberturas_repetidas"] == 1


def test_metricas_texto_vazio():
    m = _metricas_fluencia("")
    assert m["n_frases"] == 0


def test_v160_metricas_nao_disparam_mais_retentativa_nem_flag():
    """v1.6.0: `_fluencia_ok` e a flag `fluencia_baixa` foram REMOVIDAS.

    Motivo (DIAGNOSTICO_FLUENCIA_V2.md): as métricas não acompanham
    qualidade — no `cure`, o texto melhor pontuou PIOR em cv_comprimento
    (0.35 -> 0.28) e verbos_reporte (3 -> 6). Otimizar contra elas degrada
    o texto. Elas seguem sendo calculadas e persistidas, como diagnóstico
    para leitura humana."""
    import espectro24.synthesize as s
    assert not hasattr(s, "_fluencia_ok")
    assert not hasattr(s, "_REFORCO_FLUENCIA")
    from espectro24.models import NarrativaResult
    assert not hasattr(NarrativaResult(texto="x"), "fluencia_baixa")


# =====================================================================
# marcação de perspectiva — classificação a partir de shares
# =====================================================================

def test_dominante_share_e_o_maior_pct():
    pesos = {"negativas": (3, "uma pequena minoria"),
             "medianas": (18, "uma minoria"), "positivas": (79, "a grande maioria")}
    assert _dominante_share(pesos) == 79


def test_dominante_share_none_sem_pesos():
    assert _dominante_share({}) is None


@pytest.mark.parametrize("pct,dominante,esperado", [
    (79, 79, "nenhuma"),   # o próprio dominante: 79 > 79/3
    (30, 90, "simples"),   # 30 <= 90/3=30 (borda), e 30 > 90/10=9
    (50, 90, "nenhuma"),   # 50 > 90/3=30
])
def test_marcacao_casos_simples(pct, dominante, esperado):
    assert _marcacao_perspectiva(pct, dominante) == esperado


def test_marcacao_borda_exatamente_dominante_terco():
    # share == dominante/3 -> "simples" (regra: <= dominante/3)
    dominante = 90
    assert _marcacao_perspectiva(30, dominante) == "simples"
    assert _marcacao_perspectiva(31, dominante) == "nenhuma"


def test_marcacao_borda_exatamente_dominante_decimo():
    # share == dominante/10 -> "antecipada" (mais restritiva, checada primeiro)
    dominante = 90
    assert _marcacao_perspectiva(9, dominante) == "antecipada"
    assert _marcacao_perspectiva(10, dominante) == "simples"


def test_marcacao_caso_40_30_30_nenhuma_marcacao():
    pesos = {"negativas": (30, "uma parcela expressiva"),
             "medianas": (30, "uma parcela expressiva"),
             "positivas": (40, "a maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)
    assert marcacoes == {"negativas": "nenhuma", "medianas": "nenhuma",
                         "positivas": "nenhuma"}


def test_marcacoes_por_bucket_vazio_sem_distribuicao():
    assert _marcacoes_por_bucket({}) == {}


def test_marcacoes_por_bucket_cure():
    pesos = {"negativas": (3, "uma pequena minoria"),
             "medianas": (17, "uma minoria"), "positivas": (79, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)
    # dominante=79; 79/10=7.9, 79/3=26.33
    assert marcacoes == {"negativas": "antecipada", "medianas": "simples",
                         "positivas": "nenhuma"}


# =====================================================================
# validação dos marcadores declarados
# =====================================================================

_PESOS_TESTE = {"negativas": (3, "uma pequena minoria"),
                "medianas": (17, "uma minoria"), "positivas": (79, "a grande maioria")}
_MARCACOES_TESTE = _marcacoes_por_bucket(_PESOS_TESTE)  # antecipada/simples/nenhuma

_TEXTO_OK = (
    "Quem gostou é a grande maioria das notas (~79%), e o filme prende do "
    "início ao fim. Já uma minoria das notas (~17%) ficou no meio-termo. "
    "Nessa leitura, o ritmo pesa mais do que deveria. Uma pequena minoria "
    "das notas (~3%) reclamou do arrastado. Para eles, nada funciona."
)


def test_marcadores_completos_e_corretos_sao_validos():
    marcadores = [
        {"grupo": "medianas", "trecho": "Nessa leitura, o ritmo pesa mais do que deveria."},
        {"grupo": "negativas", "trecho": "Para eles, nada funciona."},
    ]
    assert _marcadores_validos(marcadores, _TEXTO_OK, _MARCACOES_TESTE, _PESOS_TESTE) is True


def test_v161_declaracao_nao_participa_mais_da_validacao():
    """v1.6.1: `marcadores_perspectiva` virou telemetria pura — a checagem
    escaneia o TEXTO em busca de uma expressão de atribuição reconhecida no
    movimento do grupo, não mais o `trecho` que o LLM declarou. Uma lista
    declarada vazia, incompleta ou com grupo inexistente não muda o
    resultado: o que importa é o que está REALMENTE escrito."""
    for marcadores_ruins in (
        [],  # nada declarado
        [{"grupo": "medianas", "trecho": "Nessa leitura, o ritmo pesa mais do que deveria."}],  # falta negativas
        [{"grupo": "negativas", "trecho": "Um trecho que não está na narrativa."}],  # trecho inventado
        [{"grupo": "neutras", "trecho": "Para eles, nada funciona."}],  # grupo inexistente
        "isto nem é uma lista de dicts",  # lixo estrutural
    ):
        assert _marcadores_validos(marcadores_ruins, _TEXTO_OK, _MARCACOES_TESTE,
                                   _PESOS_TESTE) is True, marcadores_ruins


def test_v161_texto_sem_atribuicao_e_invalido_mesmo_com_declaracao_perfeita():
    """O inverso do teste acima: mesmo que o LLM declare um marcador
    perfeito, se o TEXTO não contém nenhuma expressão de atribuição
    reconhecida no movimento daquele grupo, a checagem falha."""
    texto_sem_atribuicao = (
        "Quem gostou é a grande maioria das notas (~79%), e o filme prende "
        "do início ao fim. Já uma minoria das notas (~17%) ficou no "
        "meio-termo, achando o ritmo irregular. Uma pequena minoria das "
        "notas (~3%) reclamou do arrastado e do roteiro fraco."
    )
    marcadores_perfeitos = [
        {"grupo": "medianas", "trecho": "achando o ritmo irregular"},
        {"grupo": "negativas", "trecho": "reclamou do arrastado e do roteiro fraco"},
    ]
    assert _marcadores_validos(marcadores_perfeitos, texto_sem_atribuicao,
                               _MARCACOES_TESTE, _PESOS_TESTE) is False


def test_marcador_antecipado_tardio_e_invalido():
    # a única menção de atribuição para "negativas" (antecipada) vem ANTES
    # da âncora do próprio grupo ("uma pequena minoria das notas (~3%)") —
    # cai fora do MOVIMENTO daquele grupo (que só começa na âncora), então
    # nem é contada como ocorrência.
    texto = (
        "Para eles, nada funciona — mas isso é só um comentário solto no "
        "início. Quem gostou é a grande maioria das notas (~79%), e o "
        "filme prende do início ao fim. Já uma minoria das notas (~17%) "
        "ficou no meio-termo. Nessa leitura, o ritmo pesa mais do que "
        "deveria. Uma pequena minoria das notas (~3%) reclamou do "
        "arrastado, sem qualquer marcador logo em seguida."
    )
    assert _marcadores_validos([], texto, _MARCACOES_TESTE, _PESOS_TESTE) is False


def test_lista_vazia_valida_quando_nenhum_grupo_exige_marcacao():
    assert _marcadores_validos([], "qualquer texto", {}, {}) is True


def test_v161_caso_real_cidade_de_deus_ordem_das_palavras_diferente():
    """O caso que motivou a v1.6.1: normalizar caixa/acento/demonstrativo
    (v1.6.0) não bastou, porque a diferença aqui é de ORDEM DAS PALAVRAS.
    O narrador declarou "Para esse grupo, muitos reconhecem…" e escreveu
    "Muitos NESTE grupo reconhecem…" — mesma ideia, ordem diferente. A
    checagem por escaneamento de texto passa porque "neste grupo" já é uma
    expressão reconhecida por si só, independente do que foi declarado."""
    texto = (
        "A grande maioria das notas (~91%) repete sempre a mesma dupla de "
        "elogios: o estilo visual e a edição. Para esse grupo, muitos "
        "consideram que a narrativa se mantém envolvente e abrangente. "
        "Uma pequena minoria das notas (~8%), no entanto, aponta que o "
        "filme não conseguiu gerar uma conexão emocional profunda. Muitos "
        "neste grupo reconhecem a qualidade técnica e estilística. Já "
        "para uma fração mínima das notas (~1%), a perspectiva é bem "
        "diferente. Para eles, muitos sentiram a violência excessiva e "
        "gratuita."
    )
    pesos = {"negativas": (1, "uma fração mínima"),
             "medianas": (8, "uma pequena minoria"),
             "positivas": (91, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)   # dominante=91: 91/10=9.1, 91/3~30.3
    assert marcacoes["medianas"] in ("simples", "antecipada")
    # a declaração é EXATAMENTE a que o narrador realmente fez (reordenada
    # em relação ao texto) — e ainda assim passa, porque o que conta é o
    # texto, não a fidelidade da transcrição
    marcadores_declarados = [
        {"grupo": "medianas", "trecho": "Para esse grupo, muitos reconhecem a "
                                        "qualidade técnica e estilística."},
        {"grupo": "negativas", "trecho": "Para eles, muitos sentiram a violência "
                                         "excessiva e gratuita."},
    ]
    assert _marcadores_validos(marcadores_declarados, texto, marcacoes, pesos) is True
    # e continua passando mesmo se nada tivesse sido declarado
    assert _marcadores_validos([], texto, marcacoes, pesos) is True


# =====================================================================
# integração via narrate_output — retentativa e flag
# =====================================================================

def _bucket(nome, alvo, n=5, temas=None):
    lvl = LevelResult(4.0, 150, 1, n, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{nome}{i}", rating=4.0, text="x" * 200,
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text="x" * 200) for i in range(n)]
    return BucketResult(nome=nome, alvo=alvo, modo="completo", niveis=[lvl],
                        temas=temas or [Tema("ritmo", 3, 5, "acharam o ritmo lento")],
                        observacao_geral=f"as reviews {nome} comentam o ritmo")


def _output_com_distribuicao():
    buckets = [_bucket("negativas", 50), _bucket("medianas", 20), _bucket("positivas", 30)]
    d = Distribuicao.de_histograma(parse_rating_histogram(fx("histograma_cure.html")))
    return build_output("cure", buckets, "2026-01-01", {}, 252, distribuicao=d)


def test_narrador_recebe_marcacao_perspectiva_na_serializacao():
    from espectro24.synthesize import _serialize_output_for_narrator
    ser = _serialize_output_for_narrator(_output_com_distribuicao())
    assert 'marcacao_perspectiva: "antecipada"' in ser  # negativas, 3%
    assert 'marcacao_perspectiva: "simples"' in ser      # medianas, 17%
    assert 'marcacao_perspectiva: "nenhuma"' in ser       # positivas, 79%


def test_marcadores_completos_nao_retentam_nem_flaggam():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": ' + repr(_TEXTO_OK).replace("'", '"') + ', '
                '"consensos_usados": [], "quantificadores_usados": [], '
                '"marcadores_perspectiva": ['
                '{"grupo": "medianas", "trecho": '
                '"Nessa leitura, o ritmo pesa mais do que deveria."}, '
                '{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]}')

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    assert r.perspectiva_nao_marcada is False
    assert len(r.marcadores_perspectiva) == 2
    assert len(calls) == 1


# v1.6.1: como a checagem agora escaneia o TEXTO (não o `trecho`
# declarado), o gatilho de retentativa precisa de um texto SEM nenhuma
# expressão de atribuição no movimento — declarar (ou não declarar)
# `marcadores_perspectiva` deixou de fazer diferença por si só.
_TEXTO_SEM_ATRIBUICAO = (
    "Quem gostou é a grande maioria das notas (~79%), e o filme prende do "
    "início ao fim. Já uma minoria das notas (~17%) ficou no meio-termo, "
    "achando o ritmo irregular por vezes. Uma pequena minoria das notas "
    "(~3%) reclamou do arrastado e do roteiro fraco também."
)


def test_marcador_faltante_dispara_retentativa_e_flag():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return ('{"narrativa": ' + repr(_TEXTO_SEM_ATRIBUICAO).replace("'", '"') + ', '
                '"consensos_usados": [], "quantificadores_usados": [], '
                '"marcadores_perspectiva": []}')

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    assert r.perspectiva_nao_marcada is True
    assert len(systems) == 2                      # houve retentativa
    assert "marcador de perspectiva" in systems[1]


def test_marcador_corrigido_na_retentativa_zera_a_flag():
    respostas = [
        ('{"narrativa": ' + repr(_TEXTO_SEM_ATRIBUICAO).replace("'", '"') + ', '
         '"marcadores_perspectiva": []}'),
        ('{"narrativa": ' + repr(_TEXTO_OK).replace("'", '"') + ', '
         '"consensos_usados": [], "quantificadores_usados": [], '
         '"marcadores_perspectiva": ['
         '{"grupo": "medianas", "trecho": '
         '"Nessa leitura, o ritmo pesa mais do que deveria."}, '
         '{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]}'),
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    assert r.perspectiva_nao_marcada is False


def test_sem_distribuicao_marcador_nunca_flagga():
    buckets = [_bucket("negativas", 50), _bucket("medianas", 20), _bucket("positivas", 30)]
    out = build_output("filme-x", buckets, "2026-01-01", {}, 100)  # sem distribuicao

    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou. Já entre '
                'quem gostou, a direção surpreende do início ao fim.", '
                '"marcadores_perspectiva": []}')

    r = narrate_output(out, client_call=fake, model="m")
    assert r.perspectiva_nao_marcada is False


def test_v160_texto_monotono_nao_dispara_retentativa():
    """v1.6.0: métrica ruim NÃO retenta mais — o eixo de fluência é do
    editor (§E2), e o narrador só responde por honestidade."""
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return f'{{"narrativa": "{_MONOTONO}", "marcadores_perspectiva": []}}'

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    # métrica ruim, persistida como diagnóstico...
    assert r.metricas_fluencia["cv_comprimento"] < 0.40
    # ...mas a única retentativa aqui é a de marcadores (que o mock não
    # satisfaz), nunca uma retentativa POR MÉTRICA
    assert not hasattr(r, "fluencia_baixa")


def test_v160_texto_bom_nao_retenta():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return ('{"narrativa": ' + repr(_TEXTO_OK).replace("'", '"') + ', '
                '"consensos_usados": [], "quantificadores_usados": [], '
                '"marcadores_perspectiva": ['
                '{"grupo": "medianas", "trecho": '
                '"Nessa leitura, o ritmo pesa mais do que deveria."}, '
                '{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]}')

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    assert len(calls) == 1


def test_metricas_fluencia_persistidas_no_resultado():
    def fake(system, user, model):
        return ('{"narrativa": ' + repr(_TEXTO_OK).replace("'", '"') + ', '
                '"marcadores_perspectiva": ['
                '{"grupo": "medianas", "trecho": '
                '"Nessa leitura, o ritmo pesa mais do que deveria."}, '
                '{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]}')

    r = narrate_output(_output_com_distribuicao(), client_call=fake, model="m")
    assert r.metricas_fluencia["n_frases"] > 0
    assert "cv_comprimento" in r.metricas_fluencia


# =====================================================================
# prompt: regras novas + par antes/depois
# =====================================================================

def test_v160_narrador_nao_contem_mais_regras_de_ritmo_nem_registro():
    """v1.6.0 (Tarefa 2): ritmo e registro SAÍRAM do narrador e migraram para
    o editor (§E2). O narrador volta a ter UMA responsabilidade — dizer a
    verdade com a estrutura certa."""
    for p in (NARRATOR_SYSTEM_PROMPT, NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO):
        for termo in ("Variação de comprimento", "Variação de abertura",
                      "Tecido conjuntivo", "NO MÁXIMO 1 por movimento",
                      "advérbios intensificadores",
                      "contando de um filme para um amigo"):
            assert termo not in p, f"regra de estilo sobrou no narrador: {termo}"
        # e o par few-shot também saiu
        assert "ANTES (evite este ritmo)" not in p
        assert "DEPOIS (busque este ritmo)" not in p


def test_v160_narrador_avisa_que_a_edicao_vem_depois():
    """O narrador precisa saber que não deve se preocupar com estilo — senão
    volta a otimizar as duas coisas no mesmo passe."""
    for p in (NARRATOR_SYSTEM_PROMPT, NARRATOR_SYSTEM_PROMPT_COM_DISTRIBUICAO):
        assert "ESTÁGIO SEGUINTE" in p
        assert "gramaticalmente correta" in p


def test_v160_narrador_mantem_todas_as_invariantes_de_honestidade():
    """Tarefa 2: o que NÃO pode ter saído na poda."""
    com = build_narrator_prompt(True)
    sem = build_narrator_prompt(False)
    for p in (sem, com):
        for termo in ("MOVIMENTO 1", "MOVIMENTO 2", "MOVIMENTO 3",
                      "CRITÉRIO DE CATEGORIA", "OMISSÃO AUTORIZADA",
                      "consensos_usados", "QUANTIFICADOR PRÉ-COMPUTADO",
                      "DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES",
                      "quantificadores_usados", "ANTI-SPOILER",
                      "SEM aspas de citação", "português do Brasil"):
            assert termo in p, f"invariante perdida na poda: {termo}"
    # peso/vocabulário/marcação só existem na variante COM distribuição
    for termo in ("ANCORAGEM OBRIGATÓRIA", "das notas",
                  "MARCAÇÃO DE PERSPECTIVA", "marcadores_perspectiva"):
        assert termo in com, f"invariante de peso perdida: {termo}"


def test_prompt_com_distribuicao_contem_marcacao_de_perspectiva():
    p = build_narrator_prompt(True)
    assert "MARCAÇÃO DE PERSPECTIVA" in p
    assert "marcacao_perspectiva" in p
    assert "antecipada" in p and "simples" in p
    assert "marcadores_perspectiva" in p


def test_prompt_sem_distribuicao_nao_contem_marcacao_de_perspectiva():
    # marcação depende de share_real — não existe sem distribuição, mesmo
    # motivo pelo qual a cota de coleta não pode ser usada nesse cálculo
    p = build_narrator_prompt(False)
    assert "MARCAÇÃO DE PERSPECTIVA" not in p


def test_v160_few_shot_migrou_para_o_editor():
    """Tarefa 3.5: o par ANTES/DEPOIS descontaminado foi MOVIDO para o editor
    (não duplicado) — ele é exemplo de RITMO, e ritmo agora é do editor."""
    from espectro24.synthesize import _EDITOR_SYSTEM_PROMPT as E
    assert "ANTES (ritmo monótono)" in E
    assert "DEPOIS (ritmo desejado" in E
    assert ("elogia intensamente a condução do filme e o trabalho de câmera, "
            "destacando a habilidade de sustentar o clima em cena") in E
    assert ("o elogio se concentra num ponto só: o filme não tem pressa e usa "
            "isso a favor, porque cada silêncio entre os dois protagonistas "
            "pesa mais que a cena anterior") in E
    assert "Para eles a lentidão nunca vira método" in E
    # e NÃO ficou para trás no narrador
    assert "ANTES (evite este ritmo)" not in build_narrator_prompt(True)


def test_v160_few_shot_do_editor_segue_descontaminado():
    """A descontaminação (filme fictício) tem de sobreviver à migração: um
    exemplo com dados de um filme do catálogo faz o modelo COPIAR em vez de
    aprender a forma — foi o que aconteceu na v1.5.0 (58 8-gramas)."""
    from espectro24.synthesize import _EDITOR_SYSTEM_PROMPT as E
    inicio = E.index("EXEMPLO DE RITMO COM FILME FICTÍCIO")
    few_shot = E[inicio:]
    for termo in ("Olivia Wilde", "Buscapé", "Cidade de Deus", "Meirelles",
                  "O Convite", "A Cura", "Kurosawa"):
        assert termo not in few_shot, f"few-shot contaminado: {termo}"
    for share in ("~79%", "~18%", "~17%", "~91%", "~8%", "~3%", "~1%"):
        assert share not in few_shot, f"share de catálogo no few-shot: {share}"
    assert "~74%" in few_shot and "~19%" in few_shot and "~7%" in few_shot
    assert "NÃO EXISTE" in few_shot and "INVENTADOS" in few_shot


def test_formato_de_saida_pede_marcadores_perspectiva():
    p = build_narrator_prompt(True)
    assert '"marcadores_perspectiva"' in p
    assert '"grupo"' in p and '"trecho"' in p


# =====================================================================
# invariantes anteriores seguem presentes (v1.2.x-v1.4.1)
# =====================================================================

def test_invariantes_anteriores_seguem_no_prompt():
    for p in (build_narrator_prompt(False), build_narrator_prompt(True)):
        assert "CRITÉRIO DE CATEGORIA" in p
        assert "OMISSÃO AUTORIZADA" in p
        assert "QUANTIFICADOR PRÉ-COMPUTADO" in p
        assert "DECLARAÇÃO OBRIGATÓRIA DOS QUANTIFICADORES" in p
        assert "consensos_usados" in p
        assert "SEM aspas de citação" in p

    com = build_narrator_prompt(True)
    assert "VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS" in com
    assert "ANCORAGEM OBRIGATÓRIA" in com


def test_render_mostra_bloco_de_marcadores_perspectiva():
    out = _output_com_distribuicao()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {}
    out["marcadores_perspectiva"] = [{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]
    r = render_terminal(out, tom="narrativo")
    assert "Marcadores de perspectiva:" in r
    assert "negativas" in r
    assert "Para eles, nada funciona." in r


def test_render_mostra_flag_de_perspectiva_nao_marcada():
    out = _output_com_distribuicao()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {"perspectiva_nao_marcada": True}
    assert "sem marcador" in render_terminal(out, tom="narrativo")


def test_render_mostra_resumo_de_metricas_fluencia():
    out = _output_com_distribuicao()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {}
    out["metricas_fluencia"] = {
        "n_frases": 5, "media_palavras": 12.0, "cv_comprimento": 0.77,
        "frase_mais_curta": 4, "aberturas_repetidas": 0,
        "verbos_reporte": 0, "adverbios_mente": 0,
    }
    r = render_terminal(out, tom="narrativo")
    assert "Fluência (diagnóstico, não critério):" in r
    assert "cv_comprimento=0.77" in r


# =====================================================================
# v1.6.0 — Tarefa 5: dois bugs do validador de marcadores
# =====================================================================

def test_v160_antecipada_basta_UM_marcador_bem_posicionado():
    """Bug 5.1 (observado no `the-invite` v2): o narrador legitimamente
    declara MAIS DE UM marcador quando elabora o grupo em frases seguidas.
    A regra antiga exigia que TODOS estivessem na janela da âncora, então o
    segundo (mais tarde no texto) derrubava a validação inteira — mesmo com
    ambos válidos em conteúdo. Agora basta UM chegar cedo."""
    texto = (
        "A grande maioria das notas (~79%) gostou do filme. "
        "Já uma pequena minoria das notas (~3%) não embarca. "
        "Para eles, o humor não funciona. "
        "O elenco também não convence, e o final chega sem construir nada. "
        "Quem está nessa faixa ainda aponta a duração."
    )
    marcacoes = {"negativas": "antecipada", "positivas": "nenhuma"}
    pesos = {"negativas": (3, "uma fração mínima"),
             "positivas": (79, "a grande maioria")}
    marcadores = [
        # o 1º está logo após a âncora (posição OK)
        {"grupo": "negativas", "trecho": "Para eles, o humor não funciona."},
        # o 2º vem bem depois — antes derrubava tudo
        {"grupo": "negativas", "trecho": "Quem está nessa faixa ainda aponta a duração."},
    ]
    assert _marcadores_validos(marcadores, texto, marcacoes, pesos) is True


def test_v160_antecipada_falha_se_NENHUM_marcador_chega_cedo():
    """A regra continua tendo dente: se todos vierem tarde, é violação."""
    texto = (
        "A grande maioria das notas (~79%) gostou do filme. "
        "Já uma pequena minoria das notas (~3%) não embarca. "
        "O humor não funciona em momento nenhum do filme inteiro. "
        "O elenco também não convence, e o final chega sem construir nada. "
        "Para eles, a duração ainda pesa demais."
    )
    marcacoes = {"negativas": "antecipada", "positivas": "nenhuma"}
    pesos = {"negativas": (3, "uma fração mínima"),
             "positivas": (79, "a grande maioria")}
    marcadores = [{"grupo": "negativas", "trecho": "Para eles, a duração ainda pesa demais."}]
    assert _marcadores_validos(marcadores, texto, marcacoes, pesos) is False


def test_v161_texto_sem_nenhuma_expressao_de_atribuicao_falha():
    """v1.6.1: independentemente do que foi declarado, um texto sem NENHUMA
    expressão de atribuição reconhecida no movimento do grupo é inválido —
    a checagem é sobre o texto, não sobre a fidelidade da declaração (ver
    `_trecho_aparece`/`_normalizar_trecho`, REMOVIDAS nesta versão: a
    normalização de caixa/acento/demonstrativo não fechava o caso real do
    `cidade-de-deus`, que era de ordem de palavras, não de grafia)."""
    texto = "A grande maioria das notas (~79%) gostou. Uma fração mínima das notas (~3%) não."
    marcacoes = {"negativas": "antecipada"}
    pesos = {"negativas": (3, "uma fração mínima")}
    assert _marcadores_validos([], texto, marcacoes, pesos) is False
    # declarar um marcador "perfeito" não resgata: o texto continua sem
    # nenhuma expressão de atribuição
    marcadores = [{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]
    assert _marcadores_validos(marcadores, texto, marcacoes, pesos) is False


def test_v161_funcoes_de_normalizacao_de_trecho_foram_removidas():
    """`_normalizar_trecho`/`_trecho_aparece` (v1.6.0) tentavam consertar a
    comparação por normalização de caixa/acento/demonstrativo — insuficiente
    para o caso real (ordem de palavras). A v1.6.1 trocou O QUE se
    verifica (existência de atribuição no texto) em vez de refinar COMO se
    compara, e por isso essas funções saíram do módulo."""
    import espectro24.synthesize as s
    assert not hasattr(s, "_normalizar_trecho")
    assert not hasattr(s, "_trecho_aparece")


# =====================================================================
# v1.6.1 — bugfix: percentual como substring solta ("1%" dentro de "91%")
# =====================================================================
# Descoberto ao vivo na regeneração da v1.6.1, com os shares REAIS do
# `cidade-de-deus` (1/8/91): `_ancora_de_grupo` e `_ancoragem_de_peso_ok`
# buscavam f"{pct}%" como substring solta, então pct=1 "encontrava" o "1"
# final de "(~91%)" — muito antes da menção real de "(~1%)" — corrompendo o
# MOVIMENTO inteiro do grupo e produzindo falso positivo em
# `perspectiva_nao_marcada`.

def test_v161_ancora_de_grupo_nao_confunde_1_por_cento_com_91_por_cento():
    # rótulo de "negativas" OMITIDO de propósito: sem ele, o único jeito de
    # ancorar é pelo percentual "(~1%)" — isola exatamente o bug do
    # percentual em substring solta, sem o match alternativo pelo rótulo.
    texto = "A grande maioria das notas (~91%) adorou. Uma fração qualquer (~1%) não."
    t = texto.lower()
    idx_91 = t.find("(~91%)")
    idx_1_real = t.find("1%", idx_91 + len("(~91%)"))  # o "1" de "(~1%)", após o parágrafo de 91%
    idx_1_bugado = t.find("1%")     # o "1" final de "91%" — é aqui que o bug antigo caía
    assert idx_1_bugado < idx_91 + len("(~91%)") <= idx_1_real  # confirma o cenário de colisão

    ancora_1 = _ancora_de_grupo(texto, 1, "uma fração mínima")  # rótulo não aparece no texto
    ancora_91 = _ancora_de_grupo(texto, 91, "a grande maioria")
    assert ancora_1 == idx_1_real       # não mais o "1" de dentro de "91%"
    assert ancora_91 is not None and ancora_91 <= idx_91 + 5


def test_v161_ancoragem_de_peso_nao_confunde_1_por_cento_com_91_por_cento():
    """Sem o fix, um grupo de 1% "achava" ancoragem em qualquer texto que
    mencionasse 91%/21%/etc — mascarando `peso_nao_ancorado` real."""
    texto_sem_1_pct_de_verdade = "A grande maioria das notas (~91%) adorou o filme inteiro."
    pesos = {"negativas": (1, "uma fração mínima"), "positivas": (91, "a grande maioria")}
    # negativas NUNCA foi mencionado — só existe "91%", que contém "1%" como
    # substring. Isto TEM que falhar.
    assert _ancoragem_de_peso_ok(texto_sem_1_pct_de_verdade, pesos) is False

    texto_com_1_pct_de_verdade = texto_sem_1_pct_de_verdade + " Uma fração mínima (~1%) discordou."
    assert _ancoragem_de_peso_ok(texto_com_1_pct_de_verdade, pesos) is True


def test_v161_caso_real_cidade_de_deus_1_8_91_nao_flagga_falso_positivo():
    """Reprodução fiel do caso real que revelou o bug: shares 1/8/91, texto
    no mesmo formato que o narrador produz, com "Para eles" e "Para esse
    grupo" corretamente posicionados logo após suas âncoras reais."""
    texto = (
        "A grande maioria das notas (~91%) considera o filme uma obra-prima. "
        "Muitos destacam o estilo visual. "
        "Já para uma fração mínima das notas (~1%), o filme estetiza a violência. "
        "Para eles, isso falha em gerar reflexão. "
        "Por fim, uma pequena minoria das notas (~8%) reconhece a qualidade técnica. "
        "Para esse grupo, falta conexão emocional."
    )
    pesos = {"negativas": (1, "uma fração mínima"), "medianas": (8, "uma pequena minoria"),
             "positivas": (91, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)   # dominante=91 -> ambos antecipada
    assert marcacoes["negativas"] == "antecipada"
    assert marcacoes["medianas"] == "antecipada"
    assert _marcadores_validos([], texto, marcacoes, pesos) is True
    assert _ancoragem_de_peso_ok(texto, pesos) is True


# =====================================================================
# v1.7.1 (Tarefa 3) — família "quem gostou/não gostou" reconhecida
# =====================================================================
# Caso real publicado em `cure`: o grupo de 3% (negativas, share mínimo,
# marcação "antecipada") tinha a frase "quem não gostou considerou o ritmo
# lento e tedioso" — cumpre a função de atribuição, mas a lista de
# expressões reconhecidas não tinha essa família, e a validação marcava
# `perspectiva_nao_marcada=true` num texto honesto e bem marcado.

def test_v171_caso_real_cure_quem_nao_gostou_e_reconhecido():
    """Reprodução fiel do texto publicado (narrativa_bruta de `cure`,
    v1.7.0): shares 3/17/79, "quem não gostou" como atribuição do grupo
    negativas."""
    texto = (
        "A grande maioria das notas (~79%) aprova a obra, destacando a "
        "atmosfera e o tom perturbador e hipnótico que muitos acharam "
        "envolventes. Para esses espectadores, o ritmo lento e deliberado "
        "intensifica o suspense e o horror psicológico. "
        "Uma minoria das notas (~17%) ficou no meio, e para eles, o filme "
        "apresenta ideias intrigantes e uma atmosfera eficaz. "
        "Já para uma fração mínima das notas (~3%), quem não gostou "
        "considerou o ritmo lento e tedioso, e a maioria sentiu que o "
        "filme falha em criar tensão, mistério ou terror."
    )
    pesos = {"negativas": (3, "uma fração mínima"), "medianas": (17, "uma minoria"),
             "positivas": (79, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)
    assert marcacoes["negativas"] == "antecipada"
    assert _marcadores_validos([], texto, marcacoes, pesos) is True


def test_v171_quem_gostou_e_variantes_sao_reconhecidas():
    for expressao in ("quem gostou", "quem não gostou", "quem amou",
                      "quem ficou no meio", "para quem gostou",
                      "para quem não gostou"):
        texto = (f"Uma fração mínima das notas (~3%) discorda. "
                 f"{expressao.capitalize()} considerou o filme fraco.")
        pesos = {"negativas": (3, "uma fração mínima"), "positivas": (90, "a grande maioria")}
        marcacoes = _marcacoes_por_bucket(pesos)
        assert _marcadores_validos([], texto, marcacoes, pesos) is True, expressao


def test_v171_para_quem_isolado_continua_de_fora():
    """"para quem" sozinho (pronome relativo) NÃO pode contar como
    atribuição — é o que causou o falso negativo original na v1.6.0."""
    texto = ("Uma fração mínima das notas (~3%), para quem o filme é "
             "superestimado e pretensioso, a maioria considerou o ritmo lento.")
    pesos = {"negativas": (3, "uma fração mínima"), "positivas": (90, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)
    assert _marcadores_validos([], texto, marcacoes, pesos) is False


def test_v171_texto_sem_nenhuma_atribuicao_continua_falhando():
    texto = ("A grande maioria das notas (~90%) aprova. Uma fração mínima "
             "das notas (~3%) considerou o filme fraco, sem tensão.")
    pesos = {"negativas": (3, "uma fração mínima"), "positivas": (90, "a grande maioria")}
    marcacoes = _marcacoes_por_bucket(pesos)
    assert marcacoes["negativas"] == "antecipada"
    assert _marcadores_validos([], texto, marcacoes, pesos) is False
