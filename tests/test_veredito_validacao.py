"""[v1.9.21, §3[V]] Validações pós-parsing, seleção best-of-3 e fallback.

**Nenhum LLM julga prosa aqui** — como em todo o projeto, todo critério é
contagem sobre o texto e sobre o briefing.

**A chave de seleção, e por que ela NÃO é "o mais curto".** A primeira
proposta desta sessão foi brevidade, e foi reprovada com razão: os 19
vereditos idênticos que a versão veio corrigir não eram longos, eram VAZIOS —
otimizar para brevidade otimiza na direção exata do defeito. A chave é dupla:

  1. PRIMÁRIA — informatividade ancorada: quantas âncoras substantivas
     DISTINTAS do briefing o texto efetivamente nomeia, com TETO de 2. Sem o
     teto, o critério premiaria empilhar tema atrás de tema até estourar o
     limite de palavras; duas é o que um veredito de 1-2 frases comporta.
  2. SECUNDÁRIA — menos palavras.

**O casamento é por PALAVRAS DE CONTEÚDO, nunca por substring exata do
`tema`.** Substring exata recompensaria copiar a string verbatim, e a saída
degeneraria em citação empilhada — por isso a cópia literal do tema é
REPROVADA por validação (`tema_verbatim`), não premiada pela seleção.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import veredito as V  # noqa: E402

from tests.test_veredito_briefing import (  # noqa: E402
    _dois_lados_com_lift, _um_lado_com_lift, _valorativo, _output, _linha,
    _celula)


@pytest.fixture
def bf_tematico():
    return V.montar_briefing(_dois_lados_com_lift())


@pytest.fixture
def bf_valorativo():
    return V.montar_briefing(_valorativo())


def _flags(texto, briefing):
    return set(V.validar(texto, briefing))


# ===========================================================================
# As dez validações
# ===========================================================================

def test_texto_limpo_nao_dispara_nada(bf_tematico):
    limpo = ("Quem não recomenda fala sobretudo do ritmo arrastado; quem "
             "recomenda destaca a atmosfera densa do filme.")
    assert _flags(limpo, bf_tematico) == set()


def test_digito_e_reprovado(bf_tematico):
    """Redundância DELIBERADA: a serialização já não entrega número nenhum ao
    modelo (ver `test_veredito_briefing`). Esta validação existe para o caso
    de o modelo INVENTAR um — e para que remover uma das duas defesas não
    passe despercebido."""
    assert "digito" in _flags(
        "Cerca de 64% de quem não recomenda aponta o ritmo arrastado.",
        bf_tematico)
    # inclusive número por extenso em forma de contagem de review
    assert "digito" in _flags("Em 3 reviews o ritmo aparece.", bf_tematico)


def test_quantificador_divergente_reprova_NOS_DOIS_SENTIDOS(bf_tematico):
    """[v1.9.22] MUDANÇA DE POLÍTICA, e ela é a correção do Defeito 1.

    Até a v1.9.21 a invariante 4 dizia "mais forte é proibido, mais fraco é
    permitido", e a validação só barrava o mais forte. **A segunda metade
    estava errada:** deflação é falsidade tanto quanto inflação, e o §0 ("o
    código é a autoridade sobre quantidade") não distingue direção. Um grupo
    de 58% descrito como anedota mente sobre o dado exatamente como um de
    40% descrito como "quase todos".
    """
    # o briefing autoriza {"a maioria" (75%, negativas e positivas),
    # "muitos" (35%, assunto compartilhado)}
    assert "quantificador_divergente" in _flags(
        "Quase todos que não recomendam apontam o ritmo arrastado.",
        bf_tematico)
    assert "quantificador_divergente" in _flags(
        "Poucos que não recomendam apontam o ritmo arrastado.", bf_tematico)


def test_o_rotulo_AUTORIZADO_passa_limpo(bf_tematico):
    """O par indispensável do teste acima: se a checagem também reprovasse o
    uso CORRETO, ela tornaria a tarefa impossível em vez de discipliná-la."""
    assert "quantificador_divergente" not in _flags(
        "A maioria de quem não recomenda aponta o ritmo arrastado.",
        bf_tematico)
    # e "muitos", que o assunto compartilhado autoriza, também é rótulo dado
    assert "quantificador_divergente" not in _flags(
        "Muitos de quem não recomenda apontam o ritmo arrastado.",
        bf_tematico)


def test_a_contracao_do_artigo_e_forma_do_rotulo_nao_desvio(bf_tematico):
    """Achado ao medir o Defeito 1: `dune-2021` escreveu "pela maioria dos
    que reprovam" — o rótulo EXATO do briefing, com a contração que §D2
    (regra 4, v1.4.1) já reconhece — e o instrumento não o via. Era falso
    negativo na medição; viraria falso POSITIVO agora que a checagem exige o
    rótulo, e empurraria o filme para o fallback por escrever português
    correto."""
    for forma in ("pela maioria", "da maioria", "na maioria", "à maioria"):
        assert "quantificador_divergente" not in _flags(
            f"O ritmo arrastado é apontado {forma} de quem não recomenda.",
            bf_tematico), forma


def test_tema_ausente_do_briefing_e_reprovado(bf_tematico):
    assert "tema_ausente" in _flags(
        "Quem não recomenda critica a trilha sonora e a fotografia.",
        bf_tematico)


def test_idioma_diferente_de_ptbr_e_reprovado(bf_tematico):
    assert "idioma" in _flags(
        "Those who recommend it highlight the dense atmosphere of the film.",
        bf_tematico)


def test_comprimento_acima_do_teto_e_reprovado(bf_tematico):
    curto = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
             "destaca a atmosfera densa.")
    assert "comprimento" not in _flags(curto, bf_tematico)
    longo = curto + " " + " ".join(["palavra"] * 60)
    assert "comprimento" in _flags(longo, bf_tematico)


def test_mais_de_duas_frases_e_reprovado(bf_tematico):
    tres = ("Quem não recomenda aponta o ritmo arrastado. Quem recomenda "
            "destaca a atmosfera densa. Os dois grupos falam do filme.")
    assert "comprimento" in _flags(tres, bf_tematico)


@pytest.mark.parametrize("frase", [
    "Os críticos apontam o ritmo arrastado do filme.",
    "O consenso é que a atmosfera densa funciona.",
    "A recepção do filme gira em torno do ritmo arrastado.",
    "O público destaca a atmosfera densa.",
])
def test_generalizacao_de_escopo_e_reprovada(frase, bf_tematico):
    """Invariante 7: cada grupo é uma PERSPECTIVA, nunca uma fatia
    quantificada do público. É a mesma regra 7 de §D2, e o mesmo defeito que
    a v1.1.2 mediu no flash-lite ("a maioria dos críticos")."""
    assert "escopo_generalizado" in _flags(frase, bf_tematico)


@pytest.mark.parametrize("frase", [
    "Quem recomenda dá nota alta para a atmosfera densa.",
    "O filme fica com três estrelas para quem não recomenda.",
    "O score sobe entre quem recomenda a atmosfera densa.",
])
def test_marcadores_de_nota_ou_score_sao_reprovados(frase, bf_tematico):
    """A restrição de produto não-negociável do §1: nenhuma nota média,
    score ou estrela agregada, em lugar nenhum."""
    assert "nota_ou_score" in _flags(frase, bf_tematico)


def test_contraste_fabricado_e_reprovado_em_filme_valorativo(bf_valorativo):
    """**O coração da entrega.** Num filme `valorativo` a medição diz que os
    grupos falam das MESMAS coisas. Afirmar que falam de coisas diferentes
    não é imprecisão de redação — é inventar um achado."""
    assert "contraste_fabricado" in _flags(
        "Quem não recomenda fala de personagens; quem recomenda fala de "
        "outras coisas completamente diferentes.", bf_valorativo)
    assert "contraste_fabricado" in _flags(
        "Os dois grupos discordam sobre qual é o assunto do filme.",
        bf_valorativo)


def test_nomear_o_assunto_compartilhado_NAO_e_contraste_fabricado(bf_valorativo):
    """O falso positivo que tornaria a validação inútil: o texto CERTO para
    um filme `valorativo` nomeia o assunto compartilhado e diz que a
    divergência é de julgamento. Isso tem de passar limpo."""
    ok = ("Os dois lados falam dos personagens e das decisões que eles "
          "tomam; discordam sobre se isso funciona.")
    assert "contraste_fabricado" not in _flags(ok, bf_valorativo)


def test_contraste_fabricado_nao_se_aplica_a_filme_tematico(bf_tematico):
    """Num filme `tematico` os grupos REALMENTE falam de coisas diferentes —
    dizer isso é o trabalho, não uma violação."""
    assert "contraste_fabricado" not in _flags(
        "Quem não recomenda aponta o ritmo arrastado; quem recomenda destaca "
        "a atmosfera densa, um assunto diferente.", bf_tematico)


def test_formato_invalido_e_reprovado(bf_tematico):
    """Mesma checagem ESTRUTURAL de §E2 (v1.7.2): o invólucro JSON passava
    por todas as checagens de substring porque o conteúdo continuava lá
    DENTRO dele."""
    assert "formato_invalido" in _flags(
        '{"veredito": "Quem recomenda destaca a atmosfera densa."}',
        bf_tematico)
    assert "formato_invalido" in _flags(
        "```\nQuem recomenda destaca a atmosfera densa.\n```", bf_tematico)


def test_aspas_de_citacao_sao_reprovadas(bf_tematico):
    assert "aspas" in _flags(
        'Quem recomenda destaca a "atmosfera densa e imersiva".', bf_tematico)


def test_cliche_de_resenha_e_reprovado(bf_tematico):
    """Reusa a blocklist já existente (`dados/blocklist_resenha.txt`) — o
    veredito não é resenha, e a mesma lista que protege a narrativa protege
    aqui."""
    from espectro24 import qualidade as q
    blocklist = q.carregar_blocklist()
    if not blocklist:
        pytest.skip("blocklist vazia neste checkout")
    frase = f"Quem recomenda destaca {blocklist[0]} do filme."
    assert "cliche" in _flags(frase, bf_tematico)


# ===========================================================================
# `tema_verbatim` — o guarda-corpo contra a citação empilhada
# ===========================================================================

def test_copiar_o_tema_inteiro_e_reprovado(bf_valorativo):
    """O guarda-corpo pedido: se o casamento fosse por substring exata, a
    saída ótima seria empilhar os temas verbatim. Copiar o tema inteiro é
    REPROVADO — o modelo tem de dizer o assunto com as palavras dele."""
    tema = bf_valorativo["assunto_compartilhado"]["tema_negativas"]
    assert tema == "Personagens que tomam decisões idiotas"
    assert "tema_verbatim" in _flags(
        f'Quem não recomenda fala de "{tema}".', bf_valorativo)
    # e sem as aspas também — não é a pontuação que reprova, é a cópia
    assert "tema_verbatim" in _flags(
        f"Quem não recomenda fala de {tema.lower()}, e quem recomenda "
        "discorda.", bf_valorativo)


def test_nomear_o_assunto_com_palavras_proprias_passa_limpo(bf_valorativo):
    """O complemento indispensável do teste acima: se a checagem de verbatim
    também reprovasse a paráfrase, ela tornaria a tarefa impossível em vez
    de discipliná-la."""
    parafrase = ("Os dois lados falam das decisões dos personagens e "
                 "discordam sobre se elas funcionam.")
    assert "tema_verbatim" not in _flags(parafrase, bf_valorativo)


def test_tema_curto_nao_dispara_verbatim(bf_tematico):
    """A checagem só vale para tema com 3+ palavras de conteúdo. Um tema de
    uma ou duas palavras não é copiável — é a única forma de nomeá-lo."""
    out = _output([
        _linha("ritmo", _celula(30, 40, 45.0, "Ritmo lento"),
               _celula(10, 40, -5.0), _celula(4, 40, -35.0)),
        _linha("tom_atmosfera", _celula(4, 40, -40.0), _celula(12, 40, -5.0),
               _celula(32, 40, 44.0, "Atmosfera densa")),
    ])
    b = V.montar_briefing(out)
    assert "tema_verbatim" not in _flags(
        "Quem não recomenda aponta o ritmo lento; quem recomenda destaca a "
        "atmosfera densa.", b)


# ===========================================================================
# Âncoras e a chave PRIMÁRIA de seleção
# ===========================================================================

def test_contagem_de_ancoras_por_palavras_de_conteudo(bf_valorativo):
    """Casamento por palavras de conteúdo, não por substring: a paráfrase
    conta, e é o comportamento que a chave primária precisa premiar."""
    nenhuma = "Os dois lados discordam sobre se o filme funciona."
    uma = ("Os dois lados falam das decisões dos personagens e discordam "
           "sobre se funcionam.")
    assert V.n_ancoras(nenhuma, bf_valorativo) == 0
    assert V.n_ancoras(uma, bf_valorativo) >= 1


def test_o_teto_da_chave_primaria_e_dois(bf_tematico):
    """Sem teto, o critério premiaria empilhar tema atrás de tema até
    estourar o limite de palavras — trocaria um defeito (vazio) por outro
    (lista). Duas âncoras é o que um veredito de 1-2 frases comporta."""
    empilhado = ("Quem não recomenda aponta o ritmo arrastado e o roteiro "
                 "previsível; quem recomenda destaca a atmosfera densa e o "
                 "roteiro engenhoso do filme.")
    assert V.n_ancoras(empilhado, bf_tematico) >= 3
    assert V.pontuacao_ancoras(empilhado, bf_tematico) == 2


def test_selecao_prefere_MAIS_ancoras_mesmo_sendo_mais_longo(bf_tematico):
    """A correção que substitui "o mais curto": entre candidatos limpos, o
    informativo vence o genérico ainda que gaste mais palavras."""
    generico = "Os grupos discordam sobre o filme."
    informativo = ("Quem não recomenda aponta o ritmo arrastado; quem "
                   "recomenda destaca a atmosfera densa.")
    escolha = V.selecionar([generico, informativo], bf_tematico)
    assert escolha["texto"] == informativo
    assert escolha["criterio_decisivo"] == "ancoras"


def test_empate_em_ancoras_desempata_por_brevidade(bf_tematico):
    curto = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
             "destaca a atmosfera densa.")
    longo = curto[:-1] + " do filme, segundo o que cada grupo escreveu."
    escolha = V.selecionar([longo, curto], bf_tematico)
    assert escolha["texto"] == curto
    assert escolha["criterio_decisivo"] == "brevidade"


def test_candidato_com_flag_e_eliminado_mesmo_tendo_mais_ancoras(bf_tematico):
    """Validação vem antes de qualquer critério de qualidade: um texto que
    mente com riqueza continua mentindo."""
    rico_mas_invalido = ("Cerca de 75% de quem não recomenda aponta o ritmo "
                         "arrastado; quem recomenda destaca a atmosfera densa.")
    pobre_mas_limpo = "Quem recomenda destaca a atmosfera densa."
    escolha = V.selecionar([rico_mas_invalido, pobre_mas_limpo], bf_tematico)
    assert escolha["texto"] == pobre_mas_limpo
    assert escolha["motivo"] == "melhor_entre_limpos"
    assert escolha["candidatos"][0]["eliminado"] is True


def test_nenhum_limpo_cai_em_menor_severidade_e_pede_retry(bf_tematico):
    a = "Cerca de 75% de quem não recomenda aponta o ritmo arrastado."
    b = 'Os críticos dizem que 3 de 4 acham o "ritmo arrastado e cansativo".'
    escolha = V.selecionar([a, b], bf_tematico)
    assert escolha["motivo"] == "menor_severidade"
    assert escolha["precisa_retry"] is True
    assert escolha["texto"] == a          # menos flags


def test_empate_total_resolve_pelo_primeiro_indice(bf_tematico):
    t = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
         "destaca a atmosfera densa.")
    escolha = V.selecionar([t, t], bf_tematico)
    assert escolha["indice"] == 0
    assert escolha["criterio_decisivo"] == "empate"


def test_candidato_unico_e_registrado_como_tal(bf_tematico):
    t = "Quem recomenda destaca a atmosfera densa."
    assert V.selecionar([t], bf_tematico)["criterio_decisivo"] == "unico"


# ===========================================================================
# Fallback — o template determinístico continua sendo o piso
# ===========================================================================

def test_o_template_determinístico_continua_existindo(bf_tematico):
    """A rede da Entrega 4 e o caminho de compatibilidade do frontend são o
    MESMO código. Se ele sumir, os dois quebram juntos."""
    texto = V.veredito_template(V.montar_briefing(_dois_lados_com_lift()))
    assert texto and not texto.endswith(" ")
    assert "recomenda" in texto


def test_template_de_filme_valorativo_mantem_a_frase_historica():
    texto = V.veredito_template(V.montar_briefing(_valorativo()))
    assert texto == ("Os grupos falam das mesmas coisas — discordam sobre se "
                     "elas funcionam.")


def test_template_do_lado_sem_lift_NAO_afirma_todos_sem_lastro():
    """**A Entrega 6 — o bug real ainda em produção.** O ramo de fallback
    terminava com "— um assunto que todos os grupos citam", disparado
    sempre que existia qualquer eixo com `mencoes > 0`, sem checar se a
    frequência sustenta "todos". Medido: `obsession-2026` afirmava isso a
    partir de 2 de 5 reviews (40%); `eighth-grade`, de 13 de 34 (38%).

    É a mesma classe de inflação retórica que as v1.2.2/v1.2.3 resolveram
    para a narrativa, reintroduzida num lugar novo.
    """
    out = _um_lado_com_lift()
    # negativas: 26/40 = 65% -> "a maioria", nunca "todos"
    texto = V.veredito_template(V.montar_briefing(out))
    assert "todos os grupos citam" not in texto
    assert "a maioria" in texto


def test_template_afirma_todos_apenas_com_lastro_de_quase_todos():
    out = _output([
        _linha("tom_atmosfera", _celula(4, 40, -40.0), _celula(12, 40, -5.0),
               _celula(32, 40, 44.0, "Atmosfera densa")),
        _linha("roteiro_estrutura", _celula(36, 40, 5.0, "Roteiro previsível"),
               _celula(30, 40, 0.0), _celula(30, 40, -2.0, "Roteiro engenhoso")),
    ])
    texto = V.veredito_template(V.montar_briefing(out))
    assert "quase todos" in texto


def test_template_em_modo_reduzido_nao_generaliza():
    """`obsession-2026`: um grupo que o próprio site rotula como amostra
    pequena não pode sustentar afirmação de prevalência. Cautela explícita,
    nunca generalização."""
    out = _um_lado_com_lift()
    out["buckets"][0].update(modo="reduzido", estado_piso="sem_numero", n_validas=5)
    out["eixos"]["linhas"][1]["por_bucket"]["negativas"] = _celula(
        2, 5, 5.0, "Roteiro previsível")
    texto = V.veredito_template(V.montar_briefing(out))
    assert "todos os grupos citam" not in texto
    assert "amostra pequena" in texto.lower()


def test_template_prefixa_o_meio_dominante():
    out = _um_lado_com_lift()
    for b_, share in zip(out["buckets"], (25, 45, 30)):
        b_["share_real"] = share
    texto = V.veredito_template(V.montar_briefing(out))
    assert texto.startswith("O meio-termo é o maior grupo da recepção (~45% "
                            "das notas). ")


def test_o_template_nunca_devolve_vazio_em_nenhum_filme_publicado():
    """A rede precisa segurar os 35, senão não é rede."""
    import json
    vistos = 0
    for caminho in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = V.montar_briefing(d)
        if b is None:
            continue
        assert V.veredito_template(b), f"{caminho.name}: template vazio"
        vistos += 1
    assert vistos >= 30


# ===========================================================================
# `tema_ausente` — a fronteira de palavra, e os marcadores que foram REMOVIDOS
# ===========================================================================
# Estes três testes vêm de falsos positivos MEDIDOS na primeira geração dos
# 35 filmes, não de imaginação. Os dois primeiros custaram um filme cada: com
# a validação reprovando texto correto, o filme caía em `template_fallback` e
# recebia de volta a frase genérica que esta versão veio eliminar.

def test_marcador_casa_TOKEN_INTEIRO_e_nao_substring(bf_valorativo):
    """Bug real, mesma família do de substring da v1.6.2 (`"1%"` casando
    dentro de `"91%"`). Como substring solta, o marcador `tom` (de
    `tom_atmosfera`) casava dentro de "tomam", "sintoma" e "átomo" — e
    reprovava por assunto ausente um texto que só dizia "decisões que eles
    tomam", que é `roteiro_estrutura` e ESTÁ no briefing."""
    assert "tom_atmosfera" not in V.eixos_do_briefing(bf_valorativo)
    texto = ("Os dois lados falam das decisões que os personagens tomam e "
             "discordam sobre se elas funcionam.")
    assert "tema_ausente" not in _flags(texto, bf_valorativo)
    # e o marcador continua funcionando quando é a palavra de verdade:
    assert "tema_ausente" in _flags(
        "Os dois lados falam do tom da obra e discordam sobre ele.",
        bf_valorativo)


def test_desenvolvimento_nao_e_marcador_de_roteiro(bf_tematico):
    """Medido em `hereditary` (briefing: comparações + ritmo): o texto dizia
    "apontando um desenvolvimento arrastado", que é RITMO, e era reprovado
    como se fosse ROTEIRO. "Desenvolvimento dos personagens" é roteiro,
    "desenvolvimento arrastado" é ritmo — um marcador que casa nos dois não
    discrimina nada."""
    from espectro24.veredito import _MARCADORES_EIXO
    assert "desenvolvimento" not in _MARCADORES_EIXO["roteiro_estrutura"]


def test_incomodo_nao_e_marcador_de_impacto_emocional(bf_valorativo):
    """Medido em `pearl-2022` (briefing: só roteiro): "incômodo com a figura
    central" descreve uma PERSONAGEM irritante, que é `roteiro_estrutura`, e
    era reprovado como `impacto_emocional`. Incômodo é como se descreve
    qualquer coisa de que não se gostou."""
    from espectro24.veredito import _MARCADORES_EIXO
    assert not any(m.startswith("incomod")
                   for m in _MARCADORES_EIXO["impacto_emocional"])
    texto = ("Os dois lados citam o incômodo com a figura central do enredo "
             "e discordam sobre se isso funciona.")
    assert "tema_ausente" not in _flags(texto, bf_valorativo)


def test_o_marcador_com_asterisco_casa_por_PREFIXO(bf_valorativo):
    """A outra metade da convenção: `arrastad*` precisa pegar "arrastado" e
    "arrastada" sem virar substring solta."""
    assert "ritmo" not in V.eixos_do_briefing(bf_valorativo)
    for flexao in ("arrastado", "arrastada"):
        assert "tema_ausente" in _flags(
            f"Os dois lados acham o filme {flexao} e discordam sobre isso.",
            bf_valorativo)


# ===========================================================================
# [v1.9.22] DEFLAÇÃO POR HEDGE — a correção de NEUTRALIDADE (§0)
# ===========================================================================
# Estes testes vêm de dois textos MEDIDOS em produção sob a v1.9.21, não de
# imaginação. A regra que eles travam: **cautela é sobre a AMOSTRA (quantas
# reviews foram analisadas), nunca sobre a FREQUÊNCIA (que fatia daquele
# grupo disse aquilo)**.

def test_hedge_que_encolhe_o_grupo_e_reprovado(bf_tematico):
    """`pearl-2022`, o caso grave: negativas e positivas com a MESMA
    frequência (58%, rótulo `cerca de metade` nos dois). O lado positivo
    recebeu o rótulo; o negativo virou "impressões negativas pontuais".
    Mesmo número, dois tratamentos, e o que os separa é o SENTIMENTO do
    grupo — violação direta da neutralidade de tratamento do §0."""
    assert "deflacao_por_hedge" in _flags(
        "A maioria de quem recomenda destaca o ritmo arrastado, enquanto "
        "impressões negativas pontuais apontam a atmosfera densa.",
        bf_tematico)


def test_hedge_que_ENVOLVE_o_rotulo_certo_tambem_e_reprovado(bf_tematico):
    """`the-godfather`: "relatos pontuais apontam que a maioria dos que
    desaprovam considera a cadência arrastada". O rótulo está CERTO e o
    briefing autoriza — e mesmo assim o texto mente, porque pontual e
    maioria não podem ser a mesma coisa. A checagem de rótulo sozinha é cega
    a isto: foi por isso que o defeito passou pela v1.9.21."""
    assert "deflacao_por_hedge" in _flags(
        "Relatos pontuais apontam que a maioria de quem não recomenda cita o "
        "ritmo arrastado.", bf_tematico)


def test_o_uso_CORRETO_do_rotulo_passa_limpo(bf_tematico):
    """O par indispensável. Sem ele a checagem vira armadilha: um texto que
    nomeia a frequência dos dois lados com o rótulo dado é exatamente o que
    a correção quer produzir, e tem de passar."""
    assert "deflacao_por_hedge" not in _flags(
        "A maioria de quem não recomenda aponta o ritmo arrastado; a maioria "
        "de quem recomenda destaca a atmosfera densa.", bf_tematico)


def test_REGRESSAO_wonka_a_ancora_de_AMOSTRA_preserva_a_cautela_legitima(
        bf_tematico):
    """**A exceção existe para este caso, e ele é real.** `wonka` escreveu
    "entre as poucas manifestações desfavoráveis ANALISADAS" — uma afirmação
    sobre QUANTAS reviews foram lidas, que é verdadeira, e que a invariante
    8 do prompt OBRIGA quando o grupo está em modo reduzido.

    Sem a âncora de amostra, a checagem reprovaria a única forma honesta de
    dizer "a base é pequena" e empurraria o filme para o `template_fallback`
    — devolvendo ao leitor a frase genérica que a v1.9.21 veio eliminar. Não
    "simplifique" esta exceção.
    """
    for ancora in ("analisadas", "disponíveis", "coletadas"):
        assert "deflacao_por_hedge" not in _flags(
            f"A maioria de quem recomenda destaca o ritmo arrastado; entre as "
            f"poucas manifestações desfavoráveis {ancora}, aparece a "
            f"atmosfera densa.", bf_tematico), ancora


def test_cautela_sobre_a_BASE_passa_limpo(bf_tematico):
    """As três formulações que a invariante 8 lista como PERMITIDAS."""
    for frase in ("numa amostra pequena", "entre os poucos relatos analisados",
                  "no material disponível"):
        assert "deflacao_por_hedge" not in _flags(
            f"A maioria de quem não recomenda aponta o ritmo arrastado, "
            f"{frase}; a maioria de quem recomenda destaca a atmosfera densa.",
            bf_tematico), frase


def test_a_validacao_nova_NAO_forca_presenca_de_rotulo(bf_tematico):
    """Confirmação pedida: rótulo AUSENTE não é rótulo errado. Num texto de
    1-2 frases com teto de 55 palavras, exigir quantificador para os três
    grupos estoura o orçamento e produz rigidez. Um texto sem nenhum
    quantificador passa limpo nas duas checagens novas — a limitação fica
    registrada na spec, não convertida em validação por efeito colateral."""
    sem_rotulo = ("Quem não recomenda aponta o ritmo arrastado; quem "
                  "recomenda destaca a atmosfera densa.")
    flags = _flags(sem_rotulo, bf_tematico)
    assert "quantificador_divergente" not in flags
    assert "deflacao_por_hedge" not in flags


# ===========================================================================
# [v1.9.22] PADRÃO DE ABERTURA — a métrica do Defeito 2 e o desempate
# ===========================================================================

def test_padrao_de_abertura_colapsa_o_quantificador():
    """Qual rótulo abre a frase é decisão do CÓDIGO (mapa da v1.2.3), não do
    modelo. Contar "A maioria..." e "Cerca de metade..." como aberturas
    DIFERENTES creditaria ao modelo uma variedade que é do dado."""
    for frase in ("A maioria dos que recomendam destaca o ritmo.",
                  "Cerca de metade de quem recomenda cita o ritmo.",
                  "Muitos dos que não recomendam relatam tédio.",
                  "Quase todos os que recomendam destacam o ritmo."):
        assert V.padrao_de_abertura(frase) == V.ABERTURA_QUANTIFICADOR, frase


def test_padrao_de_abertura_ignora_a_classe_fechada():
    """Determinante, preposição e conjunção não carregam o assunto da
    abertura — "A divergência" e "Enquanto a divergência" são a mesma
    fórmula."""
    assert (V.padrao_de_abertura("A divergência central está no roteiro.")
            == V.padrao_de_abertura("Enquanto a divergência sobre o roteiro "
                                    "cresce, o resto some.")
            == "diver")
    assert V.padrao_de_abertura("As opiniões divergem sobre o roteiro.") == "opini"


def test_padrao_de_abertura_de_texto_vazio():
    assert V.padrao_de_abertura("") == ""
    assert V.padrao_de_abertura("A de o e.") == ""


def test_a_abertura_MENOS_frequente_vence_entre_limpos(bf_tematico):
    """O ataque ao Defeito 2 pela SELEÇÃO: entre candidatos que já passaram
    nas validações e empatam em âncoras, vence o que abre com o padrão menos
    repetido no catálogo. Usa os candidatos que o best-of-3 já gerou — custo
    zero de chamada."""
    comum = ("A divergência está no ritmo arrastado, que quem não recomenda "
             "aponta, e na atmosfera densa que quem recomenda destaca.")
    raro = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
            "destaca a atmosfera densa do longa.")
    assert V.padrao_de_abertura(comum) == "diver"
    assert V.padrao_de_abertura(raro) == "quem"

    historico = {"diver": 8, "opini": 6, "quem": 1}
    escolha = V.selecionar([comum, raro], bf_tematico, historico)
    assert escolha["texto"] == raro
    assert escolha["criterio_decisivo"] == "abertura"


def test_as_ANCORAS_continuam_vencendo_a_abertura(bf_tematico):
    """A ordem das chaves é a da tarefa: informatividade primeiro. Um texto
    com abertura rara e sem assunto nomeado perde para um informativo — o
    Defeito 2 não pode reintroduzir o defeito que a v1.9.21 corrigiu."""
    raro_e_vazio = "Quem não recomenda discorda de quem recomenda."
    comum_e_rico = ("A divergência está no ritmo arrastado e na atmosfera "
                    "densa do longa.")
    escolha = V.selecionar([raro_e_vazio, comum_e_rico], bf_tematico,
                           {"diver": 8, "quem": 0})
    assert escolha["texto"] == comum_e_rico
    assert escolha["criterio_decisivo"] == "ancoras"


def test_a_brevidade_continua_desempatando_quando_a_abertura_empata(bf_tematico):
    curto = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
             "destaca a atmosfera densa.")
    longo = curto[:-1] + " do filme, segundo o que cada grupo escreveu."
    escolha = V.selecionar([longo, curto], bf_tematico, {"quem": 3})
    assert escolha["texto"] == curto
    assert escolha["criterio_decisivo"] == "brevidade"


def test_sem_historico_a_selecao_e_a_da_v1921(bf_tematico):
    """`aberturas=None` zera a chave nova para todos os candidatos, e a
    ordem de decisão volta a ser âncoras -> brevidade. É o que garante que
    ligar o desempate não muda nada em quem não o usa (e é como o
    `--sem-desempate-de-abertura` do harness mede o efeito dele)."""
    curto = ("Quem não recomenda aponta o ritmo arrastado; quem recomenda "
             "destaca a atmosfera densa.")
    longo = curto[:-1] + " do filme, segundo o que cada grupo escreveu."
    escolha = V.selecionar([longo, curto], bf_tematico)
    assert escolha["texto"] == curto
    assert escolha["criterio_decisivo"] == "brevidade"
