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
    _conteudo_adicionado_ok,
    _corrigir_capitalizacao_residual,
    _formato_invalido,
    _frases_sem_origem,
    _ordem_movimento_alterada,
    _protegido_presente,
    _similaridade,
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
    # v1.7.3: até 1 + EDITOR_MAX_TENTATIVAS (=3) chamadas — falhando sempre
    # da mesma forma, esgota as 4
    assert len(systems) == 4
    assert ed.n_tentativas == 4
    assert "QUEBROU trechos protegidos" in systems[1]
    assert ed.edicao_descartada is True
    assert ed.texto == _TEXTO_NARRADOR            # narrativa original preservada
    assert ed.protegidos_perdidos
    assert len(ed.motivos_por_tentativa) == 4
    assert all("protegido" in m for m in ed.motivos_por_tentativa)


def test_protegido_recuperado_na_retentativa_e_aceito():
    respostas = [
        _TEXTO_NARRADOR.replace("A grande maioria das notas (~79%)", "Quase todo mundo"),
        # reescrita o bastante para não cair no limiar de edição nula (v1.7.4)
        ("Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
         "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
         "hipnótico. Só que muda. E muitos destacam o ritmo lento e deliberado. "
         "Uma minoria das notas (~17%) reconhece as ideias. Para esse grupo, o "
         "ritmo gera confusão. Uma fração mínima das notas (~3%) considerou o "
         "filme tedioso."),
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
    # v1.7.3: acerto de primeira -> n_tentativas=1, sem motivo de falha
    assert ed.n_tentativas == 1
    assert ed.motivos_por_tentativa == []
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


# =====================================================================
# v1.7.2 — checagem ESTRUTURAL do formato da saída do editor
# =====================================================================
# Defeito real: o `cidade-de-deus` (v1.7.1) devolveu a prosa embrulhada num
# invólucro `{ text: "..." }`. As checagens de então (protegidos, conjunto
# numérico, honestidade) rodam sobre SUBSTRING e continuavam achando tudo
# lá dentro — a edição foi aceita como "aplicada", e só a leitura humana
# pegou o defeito antes de publicar.

_TEXTO_LIMPO_PARA_INVOLUCRO = (
    "A grande maioria das notas (~91%) considera o filme uma obra-prima. "
    "Muitos elogiam o estilo visual."
)


def test_formato_invalido_detecta_involucro_de_objeto_com_campo_text():
    """O caso real exato do `cidade-de-deus`."""
    bruto = '{\n text: "' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"\n}'
    assert _formato_invalido(bruto) is True


def test_formato_invalido_detecta_comeco_com_chave_ou_colchete():
    assert _formato_invalido('{"narrativa": "texto"}') is True
    assert _formato_invalido('["texto"]') is True


def test_formato_invalido_detecta_cerca_de_codigo():
    bruto = "```\n" + _TEXTO_LIMPO_PARA_INVOLUCRO + "\n```"
    assert _formato_invalido(bruto) is True


def test_formato_invalido_detecta_campo_json_nas_primeiras_linhas():
    for prefixo in ('"text": ', "text: ", '"narrativa": '):
        bruto = prefixo + '"' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"'
        assert _formato_invalido(bruto) is True, prefixo


def test_formato_invalido_detecta_chaves_desbalanceadas():
    bruto = "{" + _TEXTO_LIMPO_PARA_INVOLUCRO
    assert _formato_invalido(bruto) is True


def test_formato_invalido_nao_marca_texto_limpo():
    assert _formato_invalido(_TEXTO_LIMPO_PARA_INVOLUCRO) is False


def test_formato_invalido_nao_marca_chave_legitima_equilibrada_no_meio_da_prosa():
    """Falso positivo a evitar: uma chave/colchete equilibrado no MEIO da
    prosa (ex. uma observação entre chaves) não é invólucro estrutural."""
    bruto = ("A grande maioria das notas (~91%) considera o filme uma "
             "obra-prima {segundo a crítica especializada}. Muitos elogiam "
             "o estilo visual.")
    assert _formato_invalido(bruto) is False


def test_editor_com_involucro_de_objeto_dispara_retentativa_e_depois_descarta():
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=_TEXTO_LIMPO_PARA_INVOLUCRO,
                          quantificadores_usados=[], marcadores_perspectiva=[])
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return '{\n text: "' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"\n}'

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert len(systems) == 4                        # v1.7.3: esgota as 4
    assert ed.n_tentativas == 4
    assert "EMBRULHADA" in systems[1]               # reforço de formato
    assert ed.edicao_descartada is True
    assert ed.motivo_descarte == "formato_invalido"
    assert ed.texto == _TEXTO_LIMPO_PARA_INVOLUCRO  # bruta prevalece
    assert ed.motivos_por_tentativa == ["formato_invalido"] * 4


def test_editor_recupera_formato_na_retentativa_e_aceita():
    # v1.8.0: a 2ª resposta precisa ser uma PARÁFRASE legítima (deriva das
    # mesmas frases da bruta) — texto idêntico dispara "edicao_nula"
    # (similaridade >= EDITOR_LIMIAR_EDICAO_NULA) e conteúdo genuinamente
    # novo dispara "conteudo_adicionado" (Tarefa 3.1); nenhum dos dois é o
    # que este teste mede (recuperação de FORMATO).
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=_TEXTO_LIMPO_PARA_INVOLUCRO,
                          quantificadores_usados=[], marcadores_perspectiva=[])
    texto_parafraseado = (
        "A grande maioria das notas (~91%) considera o filme uma "
        "obra-prima. Muitos elogiam bastante o estilo visual do filme."
    )
    respostas = [
        '{\n text: "' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"\n}',
        texto_parafraseado,
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.houve_retentativa is True
    assert ed.texto == texto_parafraseado


# =====================================================================
# v1.7.3 (Tarefa 3) — política de até 1 + EDITOR_MAX_TENTATIVAS chamadas
# =====================================================================
# Defeito real que motivou a mudança: na regeneração da v1.7.1, a edição
# foi DESCARTADA em 2 dos 3 filmes (`cure` — número alterado;
# `cidade-de-deus` — regressão de `perspectiva_nao_marcada`), publicando a
# bruta nos dois, enquanto a v1.7.0 (mesmo código+dados) tinha aceitado os
# 3 — VARIÂNCIA do modelo, não regressão. Uma única retentativa dava pouca
# chance de a variância favorecer.

def test_falha_nas_3_primeiras_e_acerto_na_4a_aceita_com_n_tentativas_4():
    novo_limpo = (
        "Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
        "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
        "hipnótico. E muitos destacam o ritmo lento e deliberado. Uma minoria "
        "das notas (~17%) reconhece as ideias. Para esse grupo, o ritmo gera "
        "confusão. Uma fração mínima das notas (~3%) considerou o filme tedioso."
    )
    respostas = [
        # 1ª: quebra um protegido (rótulo de peso trocado)
        _TEXTO_NARRADOR.replace("A grande maioria das notas (~79%)", "Quase todo mundo"),
        # 2ª: invólucro estrutural
        '{\n text: "' + novo_limpo + '"\n}',
        # 3ª: regressão de honestidade (vocabulário do peso)
        novo_limpo.replace("das notas (~17%)", "das reviews (~17%)"),
        # 4ª: limpa, aceita
        novo_limpo,
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.n_tentativas == 4
    assert ed.texto == novo_limpo
    assert len(ed.motivos_por_tentativa) == 3   # só as que falharam


def test_falha_nas_4_descarta_com_fallback_e_4_motivos():
    def fake(system, user, model):
        # sempre quebra o mesmo protegido — nunca acerta
        return _TEXTO_NARRADOR.replace("A grande maioria das notas (~79%)", "Quase todo mundo")

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.texto == _TEXTO_NARRADOR              # fallback para a bruta
    assert ed.n_tentativas == 4
    assert len(ed.motivos_por_tentativa) == 4


def test_acerto_de_primeira_n_tentativas_1_sem_reforco():
    novo = (
        "Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
        "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
        "hipnótico. E muitos destacam o ritmo lento e deliberado. Uma minoria "
        "das notas (~17%) reconhece as ideias. Para esse grupo, o ritmo gera "
        "confusão. Uma fração mínima das notas (~3%) considerou o filme tedioso."
    )
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return novo

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.n_tentativas == 1
    assert ed.motivos_por_tentativa == []
    assert len(systems) == 1
    assert systems[0] == _EDITOR_SYSTEM_PROMPT   # sem NENHUM reforço anexado


def test_reforco_acumulado_terceira_chamada_contem_os_dois_reforcos():
    """2ª falha DIFERENTE da 1ª -> a 3ª chamada recebe os reforços das duas,
    não só o da mais recente."""
    novo_limpo = (
        "Em 1997, o diretor Kiyoshi Kurosawa apresenta A Cura, um suspense de "
        "111 minutos. A grande maioria das notas (~79%) descreve o filme como "
        "hipnótico. E muitos destacam o ritmo lento e deliberado. Uma minoria "
        "das notas (~17%) reconhece as ideias. Para esse grupo, o ritmo gera "
        "confusão. Uma fração mínima das notas (~3%) considerou o filme tedioso."
    )
    respostas = [
        # 1ª: número alterado (também derruba o protegido "111")
        _TEXTO_NARRADOR.replace("111 minutos", "112 minutos"),
        # 2ª: invólucro estrutural — falha DIFERENTE da 1ª
        '{\n text: "' + novo_limpo + '"\n}',
        # 3ª: aceita (só para não gastar a 4ª)
        novo_limpo,
    ]
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return respostas.pop(0)

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.n_tentativas == 3
    terceira_chamada = systems[2]
    assert "REFORÇO CRÍTICO — sua edição anterior ALTEROU os números" in terceira_chamada
    assert "EMBRULHADA" in terceira_chamada   # os DOIS reforços presentes juntos


# =====================================================================
# v1.7.4 (Tarefa 1) — checagem de EDIÇÃO NULA
# =====================================================================
# Buraco identificado: as checagens até a v1.7.3 verificam que a edição
# não QUEBROU nada; nenhuma verifica que ela FEZ algo. Um editor que
# devolva a entrada intacta (ou trivialmente igual) passa em protegidos,
# números e honestidade — é o MESMO texto — e era marcado como "aplicada".

def test_devolucao_literal_e_detectada_como_nula_e_descarta():
    def fake(system, user, model):
        return _TEXTO_NARRADOR   # devolve a entrada, sem alterar nada

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is True
    assert ed.motivo_descarte == "edicao_nula"
    assert ed.texto == _TEXTO_NARRADOR
    assert ed.n_tentativas == 4                 # esgota as tentativas
    assert ed.motivos_por_tentativa == ["edicao_nula"] * 4
    assert ed.similaridade == 1.0


def test_edicao_legitima_preservando_vocabulario_nao_e_reprovada():
    """Reestruturar frases (juntar, quebrar, trocar aberturas) É esperado
    que preserve MUITO vocabulário — rótulo de peso e números são
    protegidos, atribuição é esperada. Isso não pode ser confundido com
    edição nula."""
    novo = (
        "Em 1997, Kiyoshi Kurosawa dirige A Cura. É um suspense de 111 "
        "minutos. Para a grande maioria das notas (~79%), o filme é "
        "hipnótico — muitos destacam justamente o ritmo lento e "
        "deliberado. Já uma minoria das notas (~17%) reconhece as ideias, "
        "só que acha a execução falha; para esse grupo, o ritmo confunde. "
        "Uma fração mínima das notas (~3%) achou tudo isso tedioso."
    )

    def fake(system, user, model):
        return novo

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.motivo_descarte != "edicao_nula"
    assert ed.similaridade < 0.97


def test_similaridade_persistida_em_todos_os_casos():
    """Aceita, descarta por outro motivo, e descarta por edição nula —
    `similaridade` sempre presente (Tarefa 1.4)."""
    # aceita
    ed_aceita = editar_narrativa(
        _res(), montar_protegidos(_res(), _output()), output=_output(),
        client_call=lambda s, u, m: (
            "Em 1997, Kiyoshi Kurosawa dirige A Cura. É um suspense de 111 "
            "minutos. Para a grande maioria das notas (~79%), o filme é "
            "hipnótico. Muitos destacam o ritmo lento. Já uma minoria das "
            "notas (~17%) reconhece as ideias, mas acha a execução falha. "
            "Para esse grupo, o ritmo confunde. Uma fração mínima das "
            "notas (~3%) achou tudo tedioso."
        ),
        model="m")
    assert ed_aceita.similaridade is not None

    # descarta por protegido perdido (motivo diferente de edicao_nula)
    ed_perdido = editar_narrativa(
        _res(), montar_protegidos(_res(), _output()), output=_output(),
        client_call=lambda s, u, m: _TEXTO_NARRADOR.replace(
            "A grande maioria das notas (~79%)", "Quase todo mundo"),
        model="m")
    assert ed_perdido.similaridade is not None

    # descarta por edição nula
    ed_nula = editar_narrativa(
        _res(), montar_protegidos(_res(), _output()), output=_output(),
        client_call=lambda s, u, m: _TEXTO_NARRADOR, model="m")
    assert ed_nula.similaridade == 1.0


def test_similaridade_ausente_quando_editor_nunca_responde():
    def fake(system, user, model):
        return ""

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.falhou is True
    assert ed.similaridade is None   # nenhuma tentativa chegou a ser avaliada


# =====================================================================
# v1.7.4 (Tarefa 2) — correção determinística de capitalização residual
# =====================================================================
# Defeito conhecido e recorrente: a v1.7.1 autorizou o editor a ajustar a
# caixa de um rótulo de peso movido para o meio da frase, mas não o
# obriga — e ele frequentemente não ajusta ("Já Uma fração mínima das
# notas...", "Para A grande maioria...").

def test_capitalizacao_residual_e_baixada_no_meio_do_periodo():
    texto = "Já Uma fração mínima das notas (~3%) discordou."
    corrigido, ajustado = _corrigir_capitalizacao_residual(texto)
    assert corrigido == "Já uma fração mínima das notas (~3%) discordou."
    assert ajustado is True


def test_capitalizacao_em_inicio_de_periodo_permanece_maiuscula():
    texto = "Uma fração mínima das notas (~3%) discordou. Outra frase aqui."
    corrigido, ajustado = _corrigir_capitalizacao_residual(texto)
    assert corrigido == texto        # nada muda — já está em início de período
    assert ajustado is False


def test_capitalizacao_nao_altera_mais_nada_alem_da_inicial():
    texto = ("A grande maioria das notas (~91%) aprova. Para A grande "
             "maioria das notas (~91%), o estilo visual convence.")
    corrigido, ajustado = _corrigir_capitalizacao_residual(texto)
    assert ajustado is True
    # a 1ª ocorrência (início de período) NÃO muda
    assert corrigido.startswith("A grande maioria das notas (~91%) aprova.")
    # só a 2ª (meio de período) tem a inicial baixada — resto intocado
    assert "Para a grande maioria das notas (~91%), o estilo visual convence." in corrigido


def test_capitalizacao_ajustada_e_registrada_em_edicao_aceita():
    def fake(system, user, model):
        return ("Em 1997, Kiyoshi Kurosawa dirige A Cura. É um suspense de "
                "111 minutos. Para A grande maioria das notas (~79%), o "
                "filme é hipnótico. Muitos destacam o ritmo lento. Já uma "
                "minoria das notas (~17%) reconhece as ideias, mas acha a "
                "execução falha. Para esse grupo, o ritmo confunde. Uma "
                "fração mínima das notas (~3%) achou tudo tedioso.")

    res = _res()
    out = _output()
    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.capitalizacao_ajustada is True
    assert "Para a grande maioria das notas (~79%)" in ed.texto
    assert "Para A grande maioria" not in ed.texto


# =====================================================================
# v1.8.0 (Tarefa 3/4) — checagem de CONTEÚDO ADICIONADO e ORDEM DOS
# MOVIMENTOS. Textos LITERAIS do caso real (VALIDACAO_DEEPSEEK.md,
# `the-invite-2026`, DeepSeek): o editor foi ACEITO por todas as checagens
# até a v1.7.4 mesmo tendo (a) reordenado o MOVIMENTO 1 para o meio do
# texto e (b) acrescentado um parágrafo de opinião inteiro sem origem no
# texto recebido.
# =====================================================================

_INVITE_BRUTO_REAL = (
    "O Convite (2026), dirigido por Olivia Wilde, mistura drama e comédia "
    "ao apresentar um casal à beira do divórcio que convida os enigmáticos "
    "vizinhos do andar de cima para um jantar, transformando a noite em "
    "algo inesperado. O filme transita entre o humor e o drama em um "
    "cenário íntimo, com um ritmo que se torna mais cansativo na segunda "
    "metade, especialmente pela repetição de situações e pela transição "
    "tonal percebida como abrupta por parte das análises. A grande "
    "maioria das notas (~79%) celebra a produção, destacando quase todos "
    "dos textos positivos a direção e o roteiro como pontos fortes, além "
    "do equilíbrio entre comédia e drama e das atuações, vistas por cerca "
    "de metade como excepcionais e com boa química. Para esses "
    "espectadores, o filme é hilário e tocante ao mesmo tempo, com uma "
    "abordagem original e visualmente envolvente. Já para a minoria das "
    "notas (~18%), que se posiciona no meio, trata-se de uma comédia bem "
    "executada, com atuações elogiadas por muitos e um roteiro "
    "inteligente, mas que se torna repetitivo e previsível, e cuja "
    "mudança de tom no final divide opiniões — enquanto alguns acham o "
    "desfecho impactante, outros o veem como abrupto e pouco "
    "desenvolvido. Por fim, uma fração mínima das notas (~3%) rejeita a "
    "obra: para esse grupo, cerca de metade aponta humor e roteiro fracos "
    "e entediantes, muitos criticam personagens e diálogos superficiais, "
    "e a abordagem da sexualidade é percebida como forçada e "
    "constrangedora, resultando em uma experiência decepcionante e "
    "previsível."
)

# Editado REAL publicado na validação: reordena o MOVIMENTO 1 (apresentação
# do filme, "O Convite (2026)...") para o MEIO do texto, e acrescenta um
# parágrafo de fechamento inteiro ("O saldo geral, no entanto...") sem
# correspondência no bruto acima.
_INVITE_EDITADO_COM_DEFEITO = (
    "A grande maioria das notas (~79%) celebra o filme. Os textos "
    "positivos destacam a direção, o roteiro, o equilíbrio entre comédia "
    "e drama e as atuações, que cerca de metade considera excepcionais, "
    "com boa química. Para esse grupo, o filme é hilário e tocante ao "
    "mesmo tempo, com abordagem original e visualmente envolvente. O "
    "Convite (2026), de Olivia Wilde, mistura drama e comédia: um casal à "
    "beira do divórcio convida os enigmáticos vizinhos do andar de cima "
    "para um jantar, e a noite vira algo inesperado. O ritmo, porém, "
    "cansa na segunda metade, sobretudo pela repetição de situações e "
    "pela transição tonal que algumas análises veem como abrupta. "
    "Já a minoria das notas (~18%) fica no meio. Para ela, é uma comédia "
    "bem executada, com atuações elogiadas por muitos e um roteiro "
    "inteligente, só que repetitivo e previsível. A mudança de tom no "
    "final divide opiniões: uns acham o desfecho impactante, outros o "
    "veem como abrupto e pouco desenvolvido. O filme transita entre o "
    "humor e o drama num cenário íntimo, e aí está o nó. "
    "Por fim, uma fração mínima das notas (~3%) rejeita a obra. Cerca de "
    "metade desse grupo aponta humor e roteiro fracos e entediantes; "
    "muitos criticam personagens e diálogos superficiais. A abordagem da "
    "sexualidade parece forçada e constrangedora para eles. O resultado é "
    "uma experiência decepcionante e previsível. O saldo geral, no "
    "entanto, é positivo. O drama se mistura à comédia com originalidade, "
    "e mesmo os críticos reconhecem a qualidade técnica da direção. As "
    "atuações seguram o filme, e a química do casal principal convence. A "
    "segunda metade perde fôlego, mas a ideia central sustenta o "
    "interesse até o fim. O desfecho polariza, e é justamente essa "
    "divisão que faz o filme render conversa. No conjunto, a recepção "
    "majoritária é calorosa, e a minoria que reprova não apaga o brilho "
    "do conjunto."
)


def test_conteudo_adicionado_detecta_paragrafo_inventado_caso_real_invite():
    """Unidade: as funções de checagem, isoladas, sobre o texto LITERAL do
    caso real — sem passar pela retentativa do editor."""
    frases_ruins = _frases_sem_origem(_INVITE_BRUTO_REAL, _INVITE_EDITADO_COM_DEFEITO)
    assert len(frases_ruins) >= 4          # bem acima de EDITOR_MIN_FRASES_SEM_ORIGEM
    assert _conteudo_adicionado_ok(frases_ruins, _INVITE_EDITADO_COM_DEFEITO) is False
    # o parágrafo inventado propriamente dito está entre as frases flagradas
    assert any("saldo geral" in f for f in frases_ruins)


def test_ordem_movimento_alterada_detecta_deslocamento_caso_real_invite():
    assert _ordem_movimento_alterada(
        _INVITE_BRUTO_REAL, _INVITE_EDITADO_COM_DEFEITO) is True


def test_editor_descarta_o_caso_real_do_the_invite_apos_retentar():
    """Integração: `editar_narrativa` recebendo repetidamente o texto COM
    DEFEITO real (o editor "insiste" no mesmo erro) — detectado, retentado
    (reforço específico anexado) e, esgotadas as tentativas, DESCARTADO. A
    bruta prevalece, exatamente como qualquer outro motivo de descarte."""
    out = {"buckets": [{"bucket": "positivas", "share_real": 79},
                       {"bucket": "medianas", "share_real": 18},
                       {"bucket": "negativas", "share_real": 3}]}
    res = NarrativaResult(texto=_INVITE_BRUTO_REAL, quantificadores_usados=[],
                          marcadores_perspectiva=[])
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return _INVITE_EDITADO_COM_DEFEITO

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")

    assert ed.edicao_descartada is True
    assert ed.motivo_descarte == "conteudo_adicionado"
    assert ed.texto == _INVITE_BRUTO_REAL             # bruta prevalece
    assert all(m == "conteudo_adicionado" for m in ed.motivos_por_tentativa)
    assert ed.frases_sem_origem                       # telemetria não-vazia
    assert ed.similaridade_minima_por_frase            # telemetria não-vazia
    # o reforço específico foi anexado a partir da 2ª tentativa
    assert any("ACRESCENTOU conteúdo" in s for s in systems[1:])


def test_edicao_legitima_de_ritmo_preservando_conteudo_nao_e_reprovada():
    """A checagem nova NÃO pode reprovar uma edição honesta — reescrita de
    ritmo (frase longa quebrada em duas, conectivos, sinônimos) que
    preserva o conteúdo inteiro. Caso real ACEITO em produção (`cure`,
    ver VALIDACAO_DEEPSEEK.md) usado como regressão: a quebra de UMA frase
    longa em duas menores, sozinha, não pode disparar "conteudo_adicionado".
    """
    bruto = (
        "Em A Cura (1997), o diretor Kiyoshi Kurosawa conduz um thriller de "
        "mistério e terror sobre um detetive obcecado em investigar "
        "assassinatos marcados por um estranho x. A premissa de um "
        "suspeito tímido e enigmático promete um mergulho psicológico "
        "sombrio. A experiência de assistir é marcada por um ritmo "
        "deliberadamente lento e contemplativo, sustentado por uma "
        "atmosfera perturbadora e hipnótica, que se constrói mais pela "
        "sugestão do que por sustos diretos. A narrativa evita respostas "
        "fáceis e mantém uma ambiguidade constante, mergulhando em temas "
        "sobre a fragilidade da mente e a natureza inexplicável do mal. "
        "Entre as notas, a grande maioria das notas (~79%) é positiva, e "
        "para esses espectadores, o ritmo lento é uma ferramenta que "
        "intensifica a sensação de transe e desconforto, com muitos "
        "destacando a maestria em criar uma atmosfera perturbadora e a "
        "exploração de temas psicológicos profundos. Alguns também "
        "elogiam a atuação do antagonista, descrita como assustadoramente "
        "calma. Já uma minoria das notas (~17%) ficou no meio-termo: para "
        "eles, as ideias são intrigantes, mas a execução falha em "
        "aprofundá-las, e o ritmo lento gera confusão narrativa, com "
        "muitos apontando um final ambíguo e insatisfatório. Por fim, uma "
        "fração mínima das notas (~3%) rejeita o filme: para esse grupo, "
        "antes de qualquer análise, o ritmo é simplesmente tedioso e "
        "arrastado, e a falta de tensão ou mistério torna a experiência "
        "decepcionante, com muitos considerando o enredo repetitivo e os "
        "personagens desinteressantes."
    )
    editado = (
        "A Cura (1997) começa com Kiyoshi Kurosawa à frente de um thriller "
        "de mistério e terror, e a trama acompanha um detetive obcecado em "
        "investigar assassinatos marcados por um estranho x. A premissa de "
        "um suspeito tímido e enigmático promete um mergulho psicológico "
        "sombrio. Só que a experiência de assistir é marcada por um ritmo "
        "deliberadamente lento e contemplativo, sustentado por uma "
        "atmosfera perturbadora e hipnótica, que se constrói mais pela "
        "sugestão do que por sustos diretos. A narrativa evita respostas "
        "fáceis e mantém uma ambiguidade constante, mergulhando em temas "
        "sobre a fragilidade da mente e a natureza inexplicável do mal. "
        "Entre as notas, a grande maioria das notas (~79%) é positiva, e "
        "para esses espectadores o ritmo lento funciona como ferramenta "
        "que intensifica a sensação de transe e desconforto. Muitos "
        "destacam a maestria em criar uma atmosfera perturbadora e a "
        "exploração de temas psicológicos profundos, e alguns também "
        "elogiam a atuação do antagonista, descrita como assustadoramente "
        "calma. Já uma minoria das notas (~17%) ficou no meio-termo: para "
        "eles, as ideias são intrigantes, mas a execução falha em "
        "aprofundá-las, e o ritmo lento gera confusão narrativa, com "
        "muitos apontando um final ambíguo e insatisfatório. Por fim, uma "
        "fração mínima das notas (~3%) rejeita o filme. Para esse grupo, "
        "antes de qualquer análise, o ritmo é simplesmente tedioso e "
        "arrastado. A falta de tensão ou mistério torna a experiência "
        "decepcionante, e muitos consideram o enredo repetitivo e os "
        "personagens desinteressantes."
    )
    frases_ruins = _frases_sem_origem(bruto, editado)
    assert _conteudo_adicionado_ok(frases_ruins, editado) is True
    assert _ordem_movimento_alterada(bruto, editado) is False

    out = {"buckets": [{"bucket": "positivas", "share_real": 79},
                       {"bucket": "medianas", "share_real": 17},
                       {"bucket": "negativas", "share_real": 3}]}
    res = NarrativaResult(texto=bruto, quantificadores_usados=[],
                          marcadores_perspectiva=[])

    def fake(system, user, model):
        return editado

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")
    assert ed.edicao_descartada is False
    assert ed.motivo_descarte != "conteudo_adicionado"
    assert ed.texto == editado


# =====================================================================
# v1.8.1 (Tarefa 1, DIAGNOSTICO_CONTEUDO_ADICIONADO.md) —
# `tentativas_detalhe`: registro COMPLETO de toda tentativa do editor
# (aceita ou reprovada), não só a última avaliada.
# =====================================================================

def test_tentativas_detalhe_registra_reprovada_e_aceita_na_ordem():
    """Reprova por formato na 1ª, aceita (paráfrase legítima) na 2ª —
    `tentativas_detalhe` precisa ter os DOIS registros, na ordem, com o
    texto completo de cada tentativa e o motivo certo em cada uma."""
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=_TEXTO_LIMPO_PARA_INVOLUCRO,
                          quantificadores_usados=[], marcadores_perspectiva=[])
    invalido = '{\n text: "' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"\n}'
    texto_parafraseado = (
        "A grande maioria das notas (~91%) considera o filme uma "
        "obra-prima. Muitos elogiam bastante o estilo visual do filme."
    )
    respostas = [invalido, texto_parafraseado]

    def fake(system, user, model):
        return respostas.pop(0)

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")

    assert len(ed.tentativas_detalhe) == 2
    t1, t2 = ed.tentativas_detalhe
    assert t1["tentativa"] == 1
    assert t1["motivo"] == "formato_invalido"
    assert t1["texto"] == invalido            # texto CRU da tentativa reprovada
    assert isinstance(t1["frases_sem_origem"], list)   # pode ser [] (formato barra antes)
    assert t2["tentativa"] == 2
    assert t2["motivo"] == ""                 # aceita
    assert t2["texto"] == texto_parafraseado
    assert t2["similaridade"] is not None


def test_tentativas_detalhe_frases_sem_origem_carrega_similaridade_maxima():
    """Cada item de `frases_sem_origem` (dentro de uma tentativa) tem a
    MESMA similaridade máxima usada pela checagem — não um valor
    recalculado à parte."""
    out = {"buckets": [{"bucket": "positivas", "share_real": 79},
                       {"bucket": "medianas", "share_real": 18},
                       {"bucket": "negativas", "share_real": 3}]}
    res = NarrativaResult(texto=_INVITE_BRUTO_REAL, quantificadores_usados=[],
                          marcadores_perspectiva=[])

    def fake(system, user, model):
        return _INVITE_EDITADO_COM_DEFEITO

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")

    assert ed.edicao_descartada is True
    assert len(ed.tentativas_detalhe) == ed.n_tentativas
    for t in ed.tentativas_detalhe:
        assert t["motivo"] == "conteudo_adicionado"
        assert t["texto"] == _INVITE_EDITADO_COM_DEFEITO   # o mock sempre devolve o mesmo texto
        for item in t["frases_sem_origem"]:
            assert set(item) == {"frase", "similaridade"}
            # a mesma similaridade que apareceria em similaridade_minima_por_frase
            assert item["similaridade"] == ed.similaridade_minima_por_frase[item["frase"]]


def test_tentativas_detalhe_registra_todas_as_tentativas_no_descarte_total():
    """Esgotadas as `1 + EDITOR_MAX_TENTATIVAS` chamadas (caso real do
    invólucro), `tentativas_detalhe` tem exatamente esse número de
    registros, todos com motivo não-vazio (nenhuma foi aceita)."""
    out = {"buckets": [{"bucket": "positivas", "share_real": 91}]}
    res = NarrativaResult(texto=_TEXTO_LIMPO_PARA_INVOLUCRO,
                          quantificadores_usados=[], marcadores_perspectiva=[])
    invalido = '{\n text: "' + _TEXTO_LIMPO_PARA_INVOLUCRO + '"\n}'

    def fake(system, user, model):
        return invalido

    ed = editar_narrativa(res, montar_protegidos(res, out), output=out,
                          client_call=fake, model="m")

    assert ed.edicao_descartada is True
    assert len(ed.tentativas_detalhe) == ed.n_tentativas == 4
    assert all(t["motivo"] == "formato_invalido" for t in ed.tentativas_detalhe)
    assert all(t["texto"] == invalido for t in ed.tentativas_detalhe)
    assert [t["tentativa"] for t in ed.tentativas_detalhe] == [1, 2, 3, 4]
