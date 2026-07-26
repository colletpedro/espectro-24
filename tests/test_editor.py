"""[E2] Passe de edição (v1.6.0) — mock, ZERO rede.

Cobre a separação honestidade × fluência: o editor melhora o ritmo mas é
estruturalmente incapaz de mentir (não recebe fonte de fato) e mecanicamente
impedido de alterar número, rótulo ou atribuição (trechos protegidos +
conjunto numérico + revalidação de honestidade). Quando ele quebra qualquer
uma dessas garantias, a edição é DESCARTADA e a narrativa do narrador
prevalece — o editor pode não melhorar, mas nunca piorar.
"""
import pytest

from conftest import fx

from espectro24.models import (
    BucketResult,
    Distribuicao,
    LevelResult,
    NarrativaResult,
    Review,
    Tema,
)
from espectro24.parser import parse_rating_histogram
from espectro24.render import build_output, render_terminal
from espectro24.synthesize import (
    _EDITOR_SYSTEM_PROMPT,
    _protegido_presente,
    _tokens_numericos,
    build_editor_user_message,
    editar_narrativa,
    montar_protegidos,
)


# --- fixtures de apoio -------------------------------------------------

_TEXTO_NARRADOR = (
    "Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
    "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
    "hipnótico, e muitos destacam o ritmo lento e deliberado. Uma minoria "
    "das notas (~17%) reconhece as ideias, mas acha a execução falha. Para "
    "esse grupo, o ritmo gera confusão. Uma fração mínima das notas (~3%) "
    "considerou o filme tedioso."
)


def _bucket(nome, alvo, n=5, temas=None):
    lvl = LevelResult(4.0, 150, 1, n, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{nome}{i}", rating=4.0, text="x" * 200,
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text="x" * 200) for i in range(n)]
    return BucketResult(nome=nome, alvo=alvo, modo="completo", niveis=[lvl],
                        temas=temas or [Tema("ritmo", 3, 5, "acharam o ritmo lento")],
                        observacao_geral=f"as reviews {nome} comentam o ritmo")


def _output():
    buckets = [_bucket("negativas", 50), _bucket("medianas", 20),
               _bucket("positivas", 30)]
    d = Distribuicao.de_histograma(
        parse_rating_histogram(fx("histograma_cure.html")))
    return build_output("cure", buckets, "2026-01-01", {}, 252, distribuicao=d)


def _res(texto=_TEXTO_NARRADOR, quantificadores=None, marcadores=None):
    return NarrativaResult(
        texto=texto,
        quantificadores_usados=quantificadores if quantificadores is not None
        else [{"quantificador": "muitos", "tema": "ritmo"}],
        marcadores_perspectiva=marcadores if marcadores is not None
        else [{"grupo": "medianas", "trecho": "Para esse grupo, o ritmo gera confusão."}],
    )


# =====================================================================
# 3.2 — o editor NÃO recebe fonte de fato
# =====================================================================

def test_editor_nao_recebe_buckets_reviews_nem_ficha():
    """Garantia ESTRUTURAL do §E2: o editor não pode inventar fato porque
    não tem fonte de fato. Verificado por inspeção do prompt montado."""
    out = _output()
    out["ficha"] = {"titulo": "Cure", "sinopse_oficial": "SINOPSE_SECRETA",
                    "diretor": "Kiyoshi Kurosawa", "ano": 1997}
    res = _res()
    protegidos = montar_protegidos(res, out)
    user = build_editor_user_message(res.texto, protegidos)

    # nada de bucket / tema / observação / ficha / review
    assert "SINOPSE_SECRETA" not in user
    assert "observacao_geral" not in user
    assert "n_reviews_analisadas" not in user
    assert "mencoes_aproximadas" not in user
    assert "exemplo_parafraseado" not in user
    assert "acharam o ritmo lento" not in user      # texto do tema
    assert "negativas" not in user and "medianas" not in user
    # só o texto e os protegidos
    assert "TEXTO A EDITAR" in user and "TRECHOS PROTEGIDOS" in user
    assert _TEXTO_NARRADOR in user


def test_prompt_do_editor_tem_as_regras_da_tarefa_3_4():
    E = _EDITOR_SYSTEM_PROMPT
    assert "TRECHOS PROTEGIDOS" in E and "INVIOLÁVEL" in E
    assert "EXATAMENTE como foi entregue" in E
    for termo in ("30-50 palavras", "3-10 palavras", "até 10 palavras",
                  "conectivos de fala", "nominalizações", "-mente",
                  "verbos de reporte", "220 e 400 palavras"):
        assert termo in E, f"regra ausente do prompt do editor: {termo}"
    assert "GRAMÁTICA" in E and "CORRIGI-LO É OBRIGATÓRIO" in E
    assert "Responda APENAS com o texto final" in E
    assert "sem JSON" in E


# =====================================================================
# 3.3 — montagem da lista de protegidos (em CÓDIGO)
# =====================================================================

def test_protegidos_incluem_peso_e_numeros_mas_nao_quantificador_nem_marcador():
    """v1.7.0 (Tarefa 2) — a lista foi ENXUGADA: só rótulo de peso COM
    percentual e tokens numéricos são protegidos LITERALMENTE. Quantificador
    e atribuição de perspectiva saíram da proteção literal porque já têm
    verificação SEMÂNTICA melhor (conferência de quantificador v1.4.1,
    `_marcadores_validos` v1.6.1) — proteger a string era redundante e
    engessava a reescrita (o editor era descartado com 14-16 protegidos)."""
    out = _output()
    res = _res()
    p = montar_protegidos(res, out)
    assert "A grande maioria das notas (~79%)" in p     # rótulo de peso
    # protegido é a forma COMO APARECE no texto (o narrador capitaliza
    # no início de frase); o rótulo canônico é minúsculo
    assert "a grande maioria das notas (~79%)" not in p
    assert "muitos" not in p                            # quantificador: FORA
    assert "Para esse grupo" not in p                   # marcador: FORA
    assert any("111" in x for x in p)                   # token com dígito
    assert any("(~17%)" in x for x in p)


def test_protegidos_nao_incluem_rotulo_de_peso_sem_percentual():
    """v1.7.0 — só a forma COM percentual é protegida; a forma nua ("___ das
    notas", sem "(~X%)") saiu, porque não é o que a Tarefa 2.1(a) pede."""
    out = _output()
    res = _res()
    p = montar_protegidos(res, out)
    assert "A grande maioria das notas" not in p
    assert not any(x.strip() == "das notas" for x in p)


def test_protegidos_so_incluem_o_que_realmente_aparece_no_texto():
    """Proteger uma string ausente tornaria a checagem impossível de
    satisfazer. Caso real: em `cidade-de-deus` o narrador declarou um
    marcador que ele mesmo não reproduziu literalmente."""
    res = _res(marcadores=[{"grupo": "medianas", "trecho": "TRECHO QUE NAO EXISTE"}])
    p = montar_protegidos(res, _output())
    assert "TRECHO QUE NAO EXISTE" not in p


def test_tokens_numericos_e_multiconjunto_ordenado():
    assert _tokens_numericos("~79% e 17% e 79%") == sorted(["79%", "17%", "79%"])
    assert _tokens_numericos("sem numeros") == []


# =====================================================================
# Tarefa 4a — trecho protegido perdido → retentativa e descarte
# =====================================================================

def test_protegido_perdido_dispara_retentativa_e_depois_descarta():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        # reescreve trocando o rótulo de peso (quebra um protegido)
        return _TEXTO_NARRADOR.replace("A grande maioria das notas (~79%)",
                                       "Quase todo mundo")

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert len(systems) == 2                      # houve retentativa
    assert "QUEBROU trechos protegidos" in systems[1]
    assert ed.edicao_descartada is True
    assert ed.texto == _TEXTO_NARRADOR            # narrativa original preservada
    assert ed.protegidos_perdidos


def test_protegido_recuperado_na_retentativa_e_aceito():
    respostas = [
        _TEXTO_NARRADOR.replace("A grande maioria das notas (~79%)", "Quase todo mundo"),
        _TEXTO_NARRADOR + " Só que muda.",
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.houve_retentativa is True
    assert "Só que muda." in ed.texto
    assert ed.texto_bruto == _TEXTO_NARRADOR


# =====================================================================
# Tarefa 4b — número alterado → descarte
# =====================================================================

def test_numero_alterado_descarta_a_edicao():
    def fake(system, user, model):
        # mantém os protegidos, mas altera um número solto (111 -> 112)
        return _TEXTO_NARRADOR.replace("111 minutos", "112 minutos")

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.numeros_alterados is True
    assert ed.texto == _TEXTO_NARRADOR
    # todo token com dígito é protegido (3.3.4), então alterar um número
    # existente é detectado JÁ como trecho protegido perdido — a checagem
    # numérica (4b) é a segunda rede, e pega sobretudo número INVENTADO
    assert "protegido" in ed.motivo_descarte


def test_numero_novo_inventado_descarta_a_edicao():
    def fake(system, user, model):
        return _TEXTO_NARRADOR + " O filme tem 3 atos."

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.numeros_alterados is True


# =====================================================================
# Tarefa 4c — regressão de honestidade → descarte
# =====================================================================

def test_regressao_de_vocabulario_de_peso_descarta():
    """Editor troca "das notas" por "das reviews" — vocabulário do peso
    (v1.4.1) regride e a edição é rejeitada."""
    def fake(system, user, model):
        return _TEXTO_NARRADOR.replace("Uma minoria das notas (~17%)",
                                       "Uma minoria das reviews (~17%)")

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.texto == _TEXTO_NARRADOR


def test_edicao_limpa_e_aceita_sem_retentativa():
    novo = (
        "Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
        "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
        "hipnótico. E muitos destacam o ritmo lento e deliberado. Uma minoria "
        "das notas (~17%) reconhece as ideias. Para esse grupo, o ritmo gera "
        "confusão. Uma fração mínima das notas (~3%) considerou o filme tedioso."
    )
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return novo

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert len(calls) == 1
    assert ed.texto == novo
    assert ed.texto_bruto == _TEXTO_NARRADOR      # auditoria preservada
    assert ed.metricas_fluencia["n_frases"] > 0


def test_editor_sem_texto_nao_quebra():
    def fake(system, user, model):
        return ""

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.falhou is True
    assert ed.edicao_descartada is True
    assert ed.texto == _TEXTO_NARRADOR


def test_narrativa_vazia_nao_chama_o_llm():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return "qualquer coisa"

    ed = editar_narrativa(_res(texto=""), [], output=_output(),
                          client_call=fake, model="m")
    assert calls == []
    assert ed.falhou is True


# =====================================================================
# render
# =====================================================================

def test_render_mostra_edicao_aplicada():
    out = _output()
    out["narrativa"] = "prosa final"
    out["narrativa_flags"] = {}
    out["edicao_flags"] = {"edicao_descartada": False, "n_protegidos": 7,
                           "houve_retentativa": False}
    r = render_terminal(out, tom="narrativo")
    assert "Edição [E2]: aplicada" in r
    assert "7 trechos protegidos" in r


def test_render_mostra_edicao_descartada_com_motivo():
    out = _output()
    out["narrativa"] = "prosa do narrador"
    out["narrativa_flags"] = {}
    out["edicao_flags"] = {"edicao_descartada": True,
                           "motivo_descarte": "2 trecho(s) protegido(s) perdido(s)",
                           "protegidos_perdidos": ["a grande maioria das notas (~79%)"]}
    r = render_terminal(out, tom="narrativo")
    assert "DESCARTADA" in r
    assert "trecho perdido: a grande maioria das notas (~79%)" in r


# =====================================================================
# v1.6.0 — conflito real entre "proteger marcadores" e "corrigir gramática"
# =====================================================================
# Descoberto no ensaio E2E sobre o `cure` publicado: o narrador declarou como
# "trecho" de marcador o PRÓPRIO PERÍODO AGRAMATICAL. Proteger o período
# inteiro tornava impossível a correção que o §E2 exige — o editor CERTO era
# descartado justamente por consertar o defeito.

_CURE_QUEBRADO = (
    "A grande maioria das notas (~79%) descreve o filme como hipnótico. "
    "Para esses, muitos destacam o ritmo lento. Para eles, alguns comentam "
    "que seria necessária uma revisitação. Uma pequena minoria das notas "
    "(~3%), para quem o filme é superestimado e pretensioso, a maioria "
    "considerou o ritmo lento e tedioso."
)


def _res_cure():
    return NarrativaResult(
        texto=_CURE_QUEBRADO,
        quantificadores_usados=[{"quantificador": "muitos", "tema": "ritmo"}],
        marcadores_perspectiva=[
            {"grupo": "medianas", "trecho": "Para esses, muitos destacam o ritmo lento. "
                                            "Para eles, alguns comentam que seria necessária uma revisitação."},
            # marcador cujo "trecho" É a frase quebrada, sem expressão de
            # atribuição reconhecível (só o "para quem" de oração relativa)
            {"grupo": "negativas", "trecho": "Uma pequena minoria das notas (~3%), "
                                             "para quem o filme é superestimado e pretensioso, "
                                             "a maioria considerou o ritmo lento e tedioso."},
        ],
    )


def test_marcador_nao_e_mais_protegido_literalmente():
    """v1.7.0 (Tarefa 2) — nenhuma expressão de atribuição entra na lista de
    protegidos, nem a que É reconhecida ("Para esses", "Para eles") nem a
    que não é ("para quem", pronome relativo). A garantia de que a
    atribuição sobrevive à edição passou a ser a checagem SEMÂNTICA
    (`_marcadores_validos`, dentro de `editar_narrativa`), não mais a
    presença literal da string na lista de protegidos."""
    res = _res_cure()
    p = montar_protegidos(res, _output())
    assert "Para esses" not in p
    assert "Para eles" not in p
    assert "para quem" not in [x.lower() for x in p]
    # mas o que é honestidade-crítica dentro daquela frase segue protegido:
    # o número isolado (o rótulo de peso deste fixture, "Uma pequena
    # minoria", é texto antigo anterior à faixa <5% da v1.6.0 e não bate
    # mais com o rótulo canônico de 3%, "uma fração mínima" — por isso não
    # entra por (1); o que teria de sobreviver de qualquer forma, o
    # percentual, entra por (2), independente do rótulo por extenso).
    assert "~3%" in p


def test_editor_PODE_corrigir_periodo_agramatical():
    """A regra de GRAMÁTICA do §E2 tem de ser exequível: corrigir o anacoluto
    do `cure` não pode ser motivo de descarte."""
    def fake(system, user, model):
        return _CURE_QUEBRADO.replace(
            "Uma pequena minoria das notas (~3%), para quem o filme é "
            "superestimado e pretensioso, a maioria considerou o ritmo lento e tedioso.",
            "Uma pequena minoria das notas (~3%) acha o filme superestimado. "
            "Para eles, a maioria considerou o ritmo lento e tedioso.")

    res = _res_cure()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False, ed.motivo_descarte
    assert "pretensioso, a maioria considerou" not in ed.texto   # anacoluto sumiu


def test_editor_NAO_pode_apagar_atribuicao_de_perspectiva():
    """O outro lado da moeda: afrouxar a proteção literal não pode deixar o
    editor apagar de quem é a opinião — mas agora é a checagem SEMÂNTICA
    (`_marcadores_validos`, revalidada dentro de `editar_narrativa`) que
    pega isso, não mais a presença de uma string na lista de protegidos
    (v1.7.0, Tarefa 2.5 — "editor que remove atribuição ainda é reprovado
    pela checagem semântica, não pela literal")."""
    texto = ("A grande maioria das notas (~90%) adorou o filme, elogiando a "
             "atuação. Uma minoria das notas (~10%) discorda; para esse "
             "grupo, o ritmo é lento e cansativo.")
    out = {"buckets": [
        {"bucket": "positivas", "share_real": 90},
        {"bucket": "medianas", "share_real": 10},
    ]}
    res = NarrativaResult(
        texto=texto, quantificadores_usados=[],
        marcadores_perspectiva=[
            {"grupo": "medianas", "trecho": "para esse grupo, o ritmo é lento e cansativo."},
        ],
    )

    def fake(system, user, model):
        # remove a ÚNICA expressão de atribuição do movimento de "medianas"
        # sem tocar em número, rótulo de peso ou vocabulário — nada que a
        # checagem literal (já não protege atribuição) ou as outras
        # checagens de honestidade pegariam sozinhas.
        return texto.replace(
            "discorda; para esse grupo, o ritmo é lento e cansativo.",
            "discorda, achando o ritmo lento e cansativo.")

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True, ed.motivo_descarte
    assert "perspectiva" in ed.motivo_descarte
    assert ed.texto == texto


def test_token_numerico_protegido_sem_pontuacao_em_volta():
    """Proteger "(~3%)," blindaria parêntese e vírgula — e repontuar é metade
    do trabalho de ritmo do editor."""
    res = _res_cure()
    p = montar_protegidos(res, _output())
    assert "~3%" in p
    assert "(~3%)," not in p


# =====================================================================
# v1.7.1 (Tarefa 2) — capitalização de rótulo protegido movido
# =====================================================================
# Defeito real publicado em `cidade-de-deus` (v1.7.0): o editor moveu o
# rótulo de peso para o meio da frase ("Para A grande maioria das notas
# (~91%), Cidade de Deus é uma obra-prima") sem poder corrigir a
# capitalização, porque a checagem de protegido era 100% literal. A
# correção autoriza SÓ a primeira letra a mudar de caixa.

def test_protegido_presente_aceita_so_a_primeira_letra_com_caixa_trocada():
    protegido = "A grande maioria das notas (~91%)"
    texto = "Para a grande maioria das notas (~91%), o filme é uma obra-prima."
    assert _protegido_presente(protegido, texto) is True


def test_protegido_presente_rejeita_qualquer_outra_palavra_alterada():
    protegido = "A grande maioria das notas (~91%)"
    # só a inicial pode mudar de caixa — trocar QUALQUER outra letra/palavra
    # continua sendo perda, mesmo que pareça uma variação pequena
    texto_errado = "a Grande maioria das notas (~91%)"    # 2ª palavra maiúscula
    assert _protegido_presente(protegido, texto_errado) is False
    texto_sinonimo = "a grande parte das notas (~91%)"     # palavra trocada
    assert _protegido_presente(protegido, texto_sinonimo) is False


def test_editor_PODE_ajustar_capitalizacao_do_rotulo_movido():
    """O caso real: mover o rótulo para o meio da frase e baixar a caixa
    inicial não pode descartar a edição."""
    texto = ("A grande maioria das notas (~91%) considera o filme uma "
             "obra-prima. Muitos elogiam o estilo visual.")
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=texto, quantificadores_usados=[],
                          marcadores_perspectiva=[])

    def fake(system, user, model):
        return ("Para a grande maioria das notas (~91%), o filme é uma "
                "obra-prima. Muitos elogiam o estilo visual.")

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False, ed.motivo_descarte
    assert "Para a grande maioria das notas (~91%)" in ed.texto


def test_editor_NAO_pode_alterar_numero_do_rotulo_mesmo_com_caixa_ajustada():
    """A folga é SÓ a primeira letra — mudar o número continua descartando,
    mesmo que a caixa inicial também tenha sido "corrigida" no processo."""
    texto = ("A grande maioria das notas (~91%) considera o filme uma "
             "obra-prima. Muitos elogiam o estilo visual.")
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=texto, quantificadores_usados=[],
                          marcadores_perspectiva=[])

    def fake(system, user, model):
        return ("Para a grande maioria das notas (~92%), o filme é uma "
                "obra-prima. Muitos elogiam o estilo visual.")

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.texto == texto
