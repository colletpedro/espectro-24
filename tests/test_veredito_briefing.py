"""[v1.9.21, §3[V]] O briefing determinístico do VEREDITO — o código decide.

Mesma fronteira que §D2 trava desde a v1.9.8, aplicada a um estágio novo:
**tudo que o briefing entrega já é decisão tomada**. O modelo recebe rótulos
prontos e nomes de tema prontos; nunca calcula, nunca arredonda, nunca
escolhe intensidade, nunca escolhe qual eixo ou qual grupo.

Os testes vêm ANTES do módulo, na ordem de execução pedida para a sessão.

**A invariante mais importante deste arquivo** é a da SERIALIZAÇÃO: o dict do
briefing carrega `freq_pct`/`lift_pp`/`share_pct` (para teste, telemetria e
fallback), mas o TEXTO enviado ao modelo não contém nenhum algarismo. Com
isso a regra "zero dígitos na saída" passa a ser garantida por CONSTRUÇÃO — o
modelo não copia um número que nunca viu — e a validação em código
(`test_veredito_validacao.py`) é redundância DELIBERADA, não a defesa
primária. Quem mexer aqui precisa saber das duas coisas ao mesmo tempo:
afrouxar a serialização não fica coberto pela validação, e remover a
validação não fica coberto pela serialização.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import veredito as V  # noqa: E402


# --------------------------------------------------------------- fixtures

def _celula(mencoes, de_n, lift_pp, tema=None):
    return {"mencoes": mencoes, "de_n": de_n,
            "freq_pct": round(100 * mencoes / de_n, 1) if de_n else 0.0,
            "lift_pp": lift_pp, "tema": tema, "exemplo_parafraseado": "",
            "temas_no_mesmo_eixo": []}


def _linha(eixo, neg, med, pos):
    return {"eixo": eixo,
            "por_bucket": {"negativas": neg, "medianas": med, "positivas": pos},
            "bullet_de": {"negativas": None, "medianas": None, "positivas": None}}


def _bucket(nome, share, modo="completo", estado="completa", n=40):
    return {"bucket": nome, "n_validas": n, "modo": modo,
            "estado_piso": estado, "share_real": share, "temas": []}


def _output(linhas, contraste="tematico", shares=(10, 20, 70), **kw):
    neg, med, pos = shares
    base = {
        "slug": "filme-de-teste",
        "ficha": {"titulo": "Filme de Teste", "ano": 2026},
        "buckets": [_bucket("negativas", neg), _bucket("medianas", med),
                    _bucket("positivas", pos)],
        "eixos": {"contraste": contraste, "margem_lift_pp": 20,
                  "taxonomia_id": "ebab2667de74", "linhas": linhas},
    }
    base.update(kw)
    return base


def _dois_lados_com_lift():
    """`tematico` com os DOIS extremos acima da margem — o caso mais rico."""
    return _output([
        _linha("ritmo",
               _celula(30, 40, 45.0, "Ritmo arrastado e cansativo"),
               _celula(10, 40, -5.0),
               _celula(4, 40, -35.0)),
        _linha("tom_atmosfera",
               _celula(4, 40, -40.0),
               _celula(12, 40, -5.0),
               _celula(32, 40, 44.0, "Atmosfera densa e imersiva")),
        _linha("roteiro_estrutura",
               _celula(14, 40, 0.0, "Roteiro previsível"),
               _celula(14, 40, 0.0),
               _celula(14, 40, 0.0, "Roteiro engenhoso")),
    ])


def _um_lado_com_lift():
    """Só as positivas passam a margem. O lado sem lift NÃO fica mudo — cai
    no eixo de maior FREQUÊNCIA (a correção da v1.9.20)."""
    return _output([
        _linha("tom_atmosfera",
               _celula(4, 40, -40.0),
               _celula(12, 40, -5.0),
               _celula(32, 40, 44.0, "Atmosfera densa e imersiva")),
        _linha("roteiro_estrutura",
               _celula(26, 40, 5.0, "Roteiro previsível"),
               _celula(22, 40, 0.0),
               _celula(24, 40, -2.0, "Roteiro engenhoso")),
    ])


def _valorativo():
    """Nenhum lado acima da margem — o estado de 17 dos 35 filmes."""
    return _output([
        _linha("roteiro_estrutura",
               _celula(30, 40, 2.0, "Personagens que tomam decisões idiotas"),
               _celula(28, 40, 0.0),
               _celula(29, 40, -2.0, "Personagens exasperantes de propósito")),
        _linha("ritmo",
               _celula(12, 40, 5.0),
               _celula(10, 40, 0.0),
               _celula(10, 40, -5.0)),
    ], contraste="valorativo")


# ===========================================================================
# Os seis casos de montagem que a sessão pediu
# ===========================================================================

def test_tematico_com_os_dois_lados_acima_da_margem():
    b = V.montar_briefing(_dois_lados_com_lift())
    assert b["contraste"] == "tematico"
    neg, pos = b["grupos"]["negativas"], b["grupos"]["positivas"]
    assert neg["eixo_maior_lift"]["eixo"] == "ritmo"
    assert neg["eixo_maior_lift"]["acima_da_margem"] is True
    assert pos["eixo_maior_lift"]["eixo"] == "tom_atmosfera"
    assert pos["eixo_maior_lift"]["acima_da_margem"] is True


def test_tematico_com_so_um_lado_acima_da_margem():
    b = V.montar_briefing(_um_lado_com_lift())
    assert b["grupos"]["positivas"]["eixo_maior_lift"]["acima_da_margem"] is True
    assert b["grupos"]["negativas"]["eixo_maior_lift"]["acima_da_margem"] is False
    # O lado sem lift não fica mudo: carrega o que ele MAIS fala (v1.9.20).
    freq = b["grupos"]["negativas"]["eixo_maior_frequencia"]
    assert freq["eixo"] == "roteiro_estrutura"
    assert freq["tema"] == "Roteiro previsível"


def test_valorativo_carrega_assunto_compartilhado_e_marca_o_estado():
    """O caso central da v1.9.21. Sem `assunto_compartilhado`, o briefing de
    um filme `valorativo` diz só "nenhum eixo passa a margem" — e um modelo
    solto sobre isso escreve 20 maneiras diferentes de dizer a mesma coisa
    vazia, que é PIOR que a repetição que a versão veio corrigir."""
    b = V.montar_briefing(_valorativo())
    assert b["contraste"] == "valorativo"
    assert b["grupos"]["negativas"]["eixo_maior_lift"]["acima_da_margem"] is False
    assert b["grupos"]["positivas"]["eixo_maior_lift"]["acima_da_margem"] is False

    a = b["assunto_compartilhado"]
    assert a is not None
    assert a["eixo"] == "roteiro_estrutura"
    assert a["tema_negativas"] == "Personagens que tomam decisões idiotas"
    assert a["tema_positivas"] == "Personagens exasperantes de propósito"


def test_bucket_reduzido_e_sem_analise_viajam_no_briefing():
    """Caso `obsession-2026`: o briefing precisa poder pedir CAUTELA, e um
    bucket `sem_analise` não empresta eixo nenhum (mesma guarda que
    `eixoDeMaiorLift`/`eixoDeMaiorFrequencia` já aplicavam no frontend)."""
    out = _um_lado_com_lift()
    out["buckets"][0].update(modo="reduzido", estado_piso="sem_numero",
                             n_validas=5)
    b = V.montar_briefing(out)
    assert b["grupos"]["negativas"]["modo"] == "reduzido"
    assert b["grupos"]["negativas"]["estado_piso"] == "sem_numero"
    assert b["amostra_reduzida"] is True

    out["buckets"][0].update(estado_piso="sem_analise")
    b2 = V.montar_briefing(out)
    assert b2["grupos"]["negativas"]["eixo_maior_lift"] is None
    assert b2["grupos"]["negativas"]["eixo_maior_frequencia"] is None


def test_meio_dominante_entra_no_briefing_e_ganha_prefixo_de_codigo():
    """O meio nunca é um dos DOIS LADOS do contraste — só ganha menção
    quando é o grupo DOMINANTE da recepção. E o percentual dele é prefixado
    pelo CÓDIGO, fora do texto do modelo (invariante 5 do prompt)."""
    out = _um_lado_com_lift()
    for b_, share in zip(out["buckets"], (25, 45, 30)):
        b_["share_real"] = share
    b = V.montar_briefing(out)
    assert b["bucket_dominante"]["bucket"] == "medianas"
    assert b["bucket_dominante"]["e_o_meio"] is True
    assert b["bucket_dominante"]["share_pct"] == 45
    assert "medianas" in b["grupos"]
    assert V.prefixo_de_codigo(b) == ("O meio-termo é o maior grupo da "
                                      "recepção (~45% das notas). ")


def test_meio_nao_dominante_nao_entra_nos_grupos_nem_prefixa():
    b = V.montar_briefing(_um_lado_com_lift())      # shares 10/20/70
    assert b["bucket_dominante"]["e_o_meio"] is False
    assert "medianas" not in b["grupos"]
    assert V.prefixo_de_codigo(b) == ""


def test_filme_sem_bloco_eixos_devolve_None():
    """Defensivo, e com a mesma política aditiva de ficha (§3[F]) e
    distribuição (§3[G]): sem o insumo, a chave não é emitida — nunca um
    veredito montado sobre buraco."""
    out = _um_lado_com_lift()
    out.pop("eixos")
    assert V.montar_briefing(out) is None
    out["eixos"] = {"contraste": "tematico", "margem_lift_pp": 20, "linhas": []}
    assert V.montar_briefing(out) is None


# ===========================================================================
# `assunto_compartilhado` — critério, piso e desempate
# ===========================================================================

def test_assunto_compartilhado_maximiza_o_MINIMO_dos_dois_lados():
    """Não é o eixo mais citado no total — é o mais citado PELOS DOIS. Um
    eixo com 90% num lado e 5% no outro não é assunto compartilhado, é
    assunto de um lado só."""
    out = _output([
        # soma maior (95), mas um dos lados quase não fala disso
        _linha("ritmo", _celula(36, 40, 5.0, "T1"), _celula(20, 40, 0.0),
               _celula(2, 40, -5.0, "T2")),
        # soma menor (80), mas os dois falam muito
        _linha("atuacao", _celula(16, 40, 0.0, "T3"), _celula(16, 40, 0.0),
               _celula(16, 40, 0.0, "T4")),
    ], contraste="valorativo")
    assert V.montar_briefing(out)["assunto_compartilhado"]["eixo"] == "atuacao"


def test_piso_de_25pp_nos_DOIS_lados():
    """Abaixo do piso o eixo não é "assunto de ambos os grupos", é ruído que
    os dois tocaram de passagem. 25% é a fronteira inferior da faixa
    `muitos` (v1.2.3), reusada em vez de um número novo."""
    out = _output([
        _linha("ritmo", _celula(9, 40, 0.0, "T1"), _celula(9, 40, 0.0),
               _celula(9, 40, 0.0, "T2")),          # 22,5% dos dois lados
    ], contraste="valorativo")
    assert V.montar_briefing(out)["assunto_compartilhado"] is None

    out["eixos"]["linhas"][0]["por_bucket"]["negativas"] = _celula(10, 40, 0.0, "T1")
    out["eixos"]["linhas"][0]["por_bucket"]["positivas"] = _celula(10, 40, 0.0, "T2")
    assert V.montar_briefing(out)["assunto_compartilhado"]["eixo"] == "ritmo"


def test_desempate_por_soma_e_depois_por_ordem_canonica():
    out = _output([
        # empatam no mínimo (40%); `atuacao` tem soma maior
        _linha("ritmo", _celula(16, 40, 0.0, "A"), _celula(16, 40, 0.0),
               _celula(16, 40, 0.0, "B")),
        _linha("atuacao", _celula(16, 40, 0.0, "C"), _celula(16, 40, 0.0),
               _celula(24, 40, 0.0, "D")),
    ], contraste="valorativo")
    assert V.montar_briefing(out)["assunto_compartilhado"]["eixo"] == "atuacao"

    # empate TOTAL -> ordem canônica de `taxonomia.EIXOS` (ritmo vem antes)
    out["eixos"]["linhas"][1]["por_bucket"]["positivas"] = _celula(16, 40, 0.0, "D")
    assert V.montar_briefing(out)["assunto_compartilhado"]["eixo"] == "ritmo"


def test_assunto_compartilhado_sobrevive_sem_tema_nomeado():
    """A limitação registrada na spec: o campo `tema` de uma célula só existe
    quando aquele eixo virou BULLET daquele grupo (§2.5). Em `dune-2021` e
    `the-substance` o eixo compartilhado não tem tema em nenhum dos dois
    lados. O briefing carrega o rótulo do EIXO e segue — nada é inventado
    para tapar o buraco (política de omissão autorizada, v1.4.1)."""
    out = _output([
        _linha("comparacoes", _celula(24, 40, 0.0), _celula(20, 40, 0.0),
               _celula(23, 40, 0.0)),
    ], contraste="valorativo")
    a = V.montar_briefing(out)["assunto_compartilhado"]
    assert a["eixo"] == "comparacoes"
    assert a["eixo_rotulo"] == "Comparações"
    assert a["tema_negativas"] is None and a["tema_positivas"] is None


# ===========================================================================
# Quantificador: vem do mapa COMUM, e o código é a autoridade
# ===========================================================================

def test_rotulo_quantificador_vem_do_mapa_comum_e_nao_de_copia_local():
    from espectro24 import quantificador as Q

    out = _dois_lados_com_lift()
    b = V.montar_briefing(out)
    freq = b["grupos"]["negativas"]["eixo_maior_frequencia"]
    assert freq["freq_pct"] == 75
    assert freq["rotulo_quantificador"] == Q.rotulo(75) == "a maioria"


@pytest.mark.parametrize("mencoes,n,esperado", [
    (2, 5, "muitos"),          # obsession-2026: 40% NUNCA vira "todos"
    (13, 34, "muitos"),        # eighth-grade: 38%
    (16, 25, "a maioria"),     # the-godfather negativas: 64%
    (25, 33, "a maioria"),     # talk-to-me-2022: 76%
    (36, 40, "quase todos"),   # 90%
])
def test_casos_reais_de_producao_recebem_o_rotulo_certo(mencoes, n, esperado):
    """Os dois primeiros são os casos MEDIDOS da inflação retórica que a
    v1.9.21 corrige: o fallback afirmava "um assunto que todos os grupos
    citam" a partir de 40% e de 38%."""
    out = _output([
        _linha("ritmo", _celula(mencoes, n, 0.0, "T"), _celula(1, n, 0.0),
               _celula(1, n, 0.0)),
    ], contraste="valorativo")
    b = V.montar_briefing(out)
    assert b["grupos"]["negativas"]["eixo_maior_frequencia"][
        "rotulo_quantificador"] == esperado


# ===========================================================================
# SERIALIZAÇÃO — a garantia por CONSTRUÇÃO
# ===========================================================================

def test_a_mensagem_ao_modelo_nao_contem_nenhum_algarismo():
    """A invariante que torna "zero dígitos na saída" independente de
    obediência: o modelo não copia um número que nunca viu.

    Montado a partir de um briefing com números PRESENTES no dict — se a
    fixture não tivesse número, o teste passaria sem medir nada.
    """
    b = V.montar_briefing(_dois_lados_com_lift())
    assert b["grupos"]["negativas"]["eixo_maior_frequencia"]["freq_pct"] == 75
    assert b["grupos"]["negativas"]["eixo_maior_lift"]["lift_pp"] == 45.0
    assert b["grupos"]["positivas"]["share_pct"] == 70

    texto = V.serializar_briefing(b)
    achados = re.findall(r"\d", texto)
    assert not achados, f"a serialização vazou algarismo(s): {achados!r}"


def test_a_serializacao_nao_vaza_algarismo_em_NENHUM_filme_publicado():
    """A mesma invariante sobre a população real — inclusive `obsession-2026`
    (amostra reduzida), `napoleon-2023` (meio dominante) e os 17
    `valorativo`. Fixture sintética não pega vazamento que só aparece num
    campo que o filme de teste não exercita."""
    vistos = 0
    for caminho in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = V.montar_briefing(d)
        if b is None:
            continue
        achados = re.findall(r"\d", V.serializar_briefing(b))
        assert not achados, f"{caminho.name} vazou {achados!r}"
        vistos += 1
    assert vistos >= 30, f"leu poucos filmes ({vistos}) — o teste não mediu nada"


def test_a_serializacao_nao_menciona_lift_nem_proximidade_da_margem():
    """`the-godfather` falha a margem por 0,4pp. O prompt não pode ter
    NENHUMA noção de "chegou perto": o limiar é binário, e um lado sem
    assunto próprio é um lado sem assunto próprio (SPEC §3[V])."""
    b = V.montar_briefing(_um_lado_com_lift())
    texto = V.serializar_briefing(b).lower()
    for proibido in ("lift", "margem", "quase atingiu", "perto", "próximo",
                     "pouco abaixo", "por pouco"):
        assert proibido not in texto, f"a serialização mencionou {proibido!r}"


def test_a_serializacao_diz_o_estado_valorativo_por_extenso():
    """O modelo precisa SABER que a divergência é de veredito — senão ele
    procura uma diferença temática que a medição não encontrou."""
    texto = V.serializar_briefing(V.montar_briefing(_valorativo())).lower()
    assert "valorativo" in texto
    assert "personagens que tomam decisões idiotas" in texto


def test_a_serializacao_e_deterministica():
    """Mesma entrada, mesma saída, byte a byte — o briefing continua sendo
    função pura do JSON, mesmo que o TEXTO gerado a partir dele não seja."""
    out = _dois_lados_com_lift()
    a = V.serializar_briefing(V.montar_briefing(out))
    b = V.serializar_briefing(V.montar_briefing(json.loads(json.dumps(out))))
    assert a == b


# ===========================================================================
# Âncoras — o insumo da chave PRIMÁRIA de seleção
# ===========================================================================

def test_ancoras_saem_do_briefing_com_id_e_palavras_de_conteudo():
    b = V.montar_briefing(_valorativo())
    ancoras = V.ancoras(b)
    ids = {a["id"] for a in ancoras}
    assert "assunto_compartilhado" in ids
    assert "frequencia_negativas" in ids and "frequencia_positivas" in ids
    for a in ancoras:
        assert a["palavras"], f"âncora {a['id']} sem palavra de conteúdo"


def test_nenhum_filme_publicado_fica_com_menos_de_duas_ancoras():
    """Guarda-corpo pedido para `dune-2021` e `the-substance`: se um filme
    ficasse com zero (ou uma) âncora possível, a chave PRIMÁRIA da seleção
    seria constante nele e a escolha cairia inteira na brevidade — que é
    exatamente o critério reprovado.

    O teto da chave primária é 2, então dois é o número que importa.
    """
    magros = []
    for caminho in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        b = V.montar_briefing(d)
        if b is None:
            continue
        if len(V.ancoras(b)) < 2:
            magros.append((caminho.stem, len(V.ancoras(b))))
    assert not magros, f"filmes com menos de 2 âncoras: {magros}"


def test_dune_e_the_substance_tem_ancora_com_tema_nomeado():
    """Os dois casos sem `tema` no eixo compartilhado. Confirma que eles não
    dependem SÓ do rótulo do eixo — cada um tem, no top-frequência de algum
    lado, uma âncora com tema nomeado de verdade."""
    for slug in ("dune-2021", "the-substance"):
        caminho = RAIZ / "resultado" / f"{slug}.json"
        if not caminho.exists():
            pytest.skip(f"{slug} não publicado neste checkout")
        b = V.montar_briefing(json.loads(caminho.read_text(encoding="utf-8")))
        com_tema = [a for a in V.ancoras(b) if a.get("tema")]
        assert com_tema, f"{slug} só tem âncora de rótulo de eixo"


def test_a_serializacao_nao_nomeia_o_filme():
    """Duas razões, e a segunda é a forte. (1) `friday-the-13th-2009` se chama
    "Sexta-Feira 13" — o título CARREGA algarismo, e emiti-lo abriria na
    serialização o buraco que ela existe para fechar. (2) Nomear o filme
    convida o modelo a usar o que ele SABE sobre o filme, e a invariante 1
    proíbe contexto externo; um briefing anônimo torna a fidelidade mais
    fácil de obedecer do que de violar."""
    b = V.montar_briefing(_dois_lados_com_lift())
    assert b["titulo"] == "Filme de Teste"        # no DICT, para telemetria
    assert "Filme de Teste" not in V.serializar_briefing(b)
