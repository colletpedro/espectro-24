"""[v1.9.21] `quantificador.py` — o mapa de faixas da v1.2.3, UNIFICADO.

**Por que existe um módulo novo para uma tabela de seis linhas.** O mapa
existia DUAS vezes antes desta versão:

  - `synthesize._rotulo_quantificador` — o original da v1.2.3;
  - `briefing._quantificador` — cópia deliberada, com o motivo escrito no
    docstring: *"reimportada por valor, não por import, para que este módulo
    não dependa de `synthesize` (que importa SDKs)"*.

A duplicação era defensável com duas cópias e um motivo. Com TRÊS deixa de
ser: o estágio [V] (§3[V]) precisa do mesmo mapa, e uma terceira cópia é o
ponto em que "calibração intocada desde a v1.2.3" vira uma frase que ninguém
consegue mais verificar. O módulo novo não importa nada — nem SDK, nem
`config`, nem `taxonomia` — então o motivo original da cópia desaparece em
vez de ser contornado.

**O portão desta extração** (ela atravessa `synthesize` e `briefing`, que
alimentam a narrativa dos 35 filmes publicados) tem três partes, e as três
estão neste arquivo:

  1. comportamento fixado em toda a faixa, incluindo as fronteiras de cada
     rótulo e os dois extremos do clamp;
  2. demonstração de que `pct` fora de 0-100 é INALCANÇÁVEL por caminho de
     produção — sem ela, o clamp deixaria de ser unificação de cauda morta e
     viraria mudança de comportamento alcançável;
  3. equivalência com as DUAS implementações antigas, congeladas literalmente
     abaixo, sobre toda a faixa e sobre todo `pct` que os 35 filmes do
     catálogo realmente produzem.

**A cauda divergente, registrada.** Para `pct` fora de 0-100 as duas cópias
antigas discordavam: `synthesize` devolvia `"quase todos"` (comentado como
"fallback seguro"), `briefing` devolvia `"poucos"`. Nenhum teste cobria o
caso e nenhum caminho de produção o alcança (item 2). O módulo novo CLAMPA a
[0,100] antes da consulta, o que mata as duas caudas e torna o comportamento
determinístico — registrado no changelog da v1.9.21 como o que é: unificação
com diferença de comportamento em entrada hoje inalcançável, não refatoração
silenciosa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import quantificador as Q  # noqa: E402


# ===========================================================================
# As DUAS implementações antigas, congeladas LITERALMENTE
# ===========================================================================
# Copiadas de `synthesize.py` e `briefing.py` como estavam na v1.9.20, antes
# da extração. Ficam aqui como ORÁCULO — se alguém mexer no módulo novo, é
# contra estas duas que a mudança é medida, não contra a memória de ninguém.
# Não importam nada do pacote de propósito: um oráculo que chama o código sob
# teste não testa nada.

def _sintetize_v1920(pct: int) -> str:
    for rotulo, lo, hi, hi_inclusive in [
        ("poucos", 0, 10, False),
        ("alguns", 10, 25, True),
        ("muitos", 25, 50, True),
        ("cerca de metade", 40, 60, True),
        ("a maioria", 50, 80, True),
        ("quase todos", 80, 100, True),
    ]:
        if pct < lo:
            continue
        if (hi_inclusive and pct <= hi) or (not hi_inclusive and pct < hi):
            return rotulo
    return "quase todos"


def _briefing_v1920(pct: int) -> str:
    for rotulo, lo, hi, hi_incl in (
        ("poucos", 0, 10, False), ("alguns", 10, 25, True),
        ("muitos", 25, 50, True), ("cerca de metade", 40, 60, True),
        ("a maioria", 50, 80, True), ("quase todos", 80, 100, True),
    ):
        if pct >= lo and (pct <= hi if hi_incl else pct < hi):
            return rotulo
    return "poucos"


# ===========================================================================
# (1) Comportamento fixado — faixa inteira e fronteiras
# ===========================================================================

# As fronteiras COMPARTILHADAS, com a resolução que a v1.2.3 escreveu por
# extenso: em caso de empate entre faixas, sempre o rótulo mais FRACO.
FRONTEIRAS = [
    (0, "poucos"),
    (9, "poucos"),
    (10, "alguns"),           # "poucos" exige pct < 10 (único superior exclusivo)
    (24, "alguns"),
    (25, "alguns"),           # "alguns"(10-25) e "muitos"(25-50) empatam -> o fraco
    (26, "muitos"),
    (39, "muitos"),
    (40, "muitos"),           # "muitos" e "cerca de metade"(40-60) empatam -> o fraco
    (49, "muitos"),
    (50, "muitos"),           # "muitos", "cerca de metade" e "a maioria" empatam
    (51, "cerca de metade"),
    (60, "cerca de metade"),
    (61, "a maioria"),
    (79, "a maioria"),
    (80, "a maioria"),        # "a maioria"(50-80) e "quase todos"(>=80) empatam
    (81, "quase todos"),
    (100, "quase todos"),
]


@pytest.mark.parametrize("pct,esperado", FRONTEIRAS)
def test_fronteiras_resolvem_para_o_rotulo_mais_fraco(pct, esperado):
    """A regra da v1.2.3, escrita como teste em vez de como comentário.

    Cada fronteira compartilhada é um empate entre duas ou três faixas, e o
    empate resolve SEMPRE para o rótulo mais fraco — a política que impede o
    "quase todos" aplicado a 65-70% que motivou a v1.2.3.
    """
    assert Q.rotulo(pct) == esperado


def test_toda_a_faixa_devolve_um_rotulo_conhecido():
    conhecidos = {r for r, _, _, _ in Q.BANDAS_FRACA_PARA_FORTE}
    for pct in range(0, 101):
        assert Q.rotulo(pct) in conhecidos


def test_o_rotulo_e_monotono_nao_decrescente():
    """Subir a fração nunca pode ENFRAQUECER o rótulo.

    Não é redundante com as fronteiras: elas fixam pontos, esta fixa a
    FORMA da função. Uma faixa mal ordenada passaria nos pontos testados e
    quebraria aqui.
    """
    ordem = [r for r, _, _, _ in Q.BANDAS_FRACA_PARA_FORTE]
    anterior = 0
    for pct in range(0, 101):
        i = ordem.index(Q.rotulo(pct))
        assert i >= anterior, f"pct={pct} enfraqueceu o rótulo"
        anterior = i


# --- os dois extremos do clamp ---------------------------------------------

def test_clamp_no_extremo_superior():
    """`pct > 100` clampa a 100. As duas cópias antigas DISCORDAVAM aqui
    (`synthesize` dizia "quase todos", `briefing` dizia "poucos"); o clamp
    escolhe o comportamento que a fração realmente significa — mais menções
    que reviews é, no limite, todo mundo."""
    assert Q.rotulo(101) == "quase todos"
    assert Q.rotulo(10_000) == "quase todos"


def test_clamp_no_extremo_inferior():
    """`pct < 0` clampa a 0. `briefing` já devolvia "poucos" por acidente do
    fallback; `synthesize` devolvia "quase todos", que era simplesmente
    errado. O clamp torna o certo o único resultado possível."""
    assert Q.rotulo(-1) == "poucos"
    assert Q.rotulo(-10_000) == "poucos"


def test_fracao_percentual_arredonda_e_protege_denominador_zero():
    assert Q.fracao_percentual(16, 25) == 64
    assert Q.fracao_percentual(0, 40) == 0
    assert Q.fracao_percentual(40, 40) == 100
    # denominador ausente/zero/negativo -> 0, nunca ZeroDivisionError: um
    # bucket sem reviews analisadas não pode derrubar o pipeline.
    assert Q.fracao_percentual(3, 0) == 0
    assert Q.fracao_percentual(3, None) == 0
    assert Q.fracao_percentual(3, -5) == 0


# ===========================================================================
# (2) A inalcançabilidade — demonstrada, não afirmada
# ===========================================================================

def test_o_numerador_e_clampado_na_sintese_antes_de_virar_fracao():
    """A demonstração ESTRUTURAL: `pct > 100` exigiria `mencoes > n`, e a
    síntese (§D, v1.1.1) clampa o numerador ao denominador ANTES de
    construir o `Tema`. Não é convenção — é `max(0, min(bruto, n))` em
    `synthesize._construir_temas`, com o valor original preservado à parte
    (`mencoes_valor_original`) para auditoria.

    Este teste chama a função real, e não relê o código-fonte: um teste que
    afirma "existe um clamp lá" grepando o arquivo passaria com o clamp
    comentado.
    """
    from espectro24 import synthesize as S

    temas = S._construir_temas(
        {"temas": [
            {"tema": "inflado", "mencoes_aproximadas": 999,
             "exemplo_parafraseado": "x"},
            {"tema": "negativo", "mencoes_aproximadas": -7,
             "exemplo_parafraseado": "x"},
        ]},
        n_analisadas=40)
    por_nome = {t.tema: t for t in temas}
    assert por_nome["inflado"].mencoes_aproximadas == 40
    assert por_nome["inflado"].mencoes_valor_original == 999
    assert por_nome["negativo"].mencoes_aproximadas == 0
    for t in temas:
        assert 0 <= Q.fracao_percentual(
            t.mencoes_aproximadas, t.n_reviews_analisadas) <= 100


def test_nenhum_tema_publicado_produz_fracao_fora_da_faixa():
    """A demonstração EMPÍRICA, sobre o corpus real: nos 35 filmes
    publicados, todo tema de todo bucket tem `0 <= mencoes <= n`, e toda
    célula de `eixos` tem `0 <= mencoes <= de_n`.

    Junto com o teste estrutural acima, é o que sustenta a afirmação
    "inalcançável" do changelog. Se um dia falhar, o clamp deixa de ser
    unificação de cauda morta e vira mudança de comportamento ALCANÇÁVEL —
    e o registro da v1.9.21 precisa ser corrigido, não o teste.
    """
    vistos = 0
    for caminho in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        for b in d.get("buckets") or []:
            n = b.get("n_validas") or 0
            for t in b.get("temas") or []:
                m = t.get("mencoes_aproximadas", 0)
                assert 0 <= m <= max(n, 0), f"{caminho.name}: {t.get('tema')}"
                assert 0 <= Q.fracao_percentual(m, n) <= 100
                vistos += 1
        for linha in ((d.get("eixos") or {}).get("linhas") or []):
            for celula in (linha.get("por_bucket") or {}).values():
                m, de_n = celula.get("mencoes", 0), celula.get("de_n", 0)
                assert 0 <= m <= max(de_n, 0), f"{caminho.name}: {linha['eixo']}"
                assert 0 <= Q.fracao_percentual(m, de_n) <= 100
                vistos += 1
    assert vistos > 0, "nenhum resultado/*.json lido — o teste não mediu nada"


# ===========================================================================
# (3) Equivalência com as duas implementações antigas
# ===========================================================================

def test_equivale_as_duas_implementacoes_antigas_em_toda_a_faixa():
    """O portão da extração: para todo `pct` alcançável (0-100), o módulo
    novo concorda com AS DUAS cópias congeladas. Fora dessa faixa as duas
    discordavam entre si, e é exatamente onde o clamp entra."""
    for pct in range(0, 101):
        novo = Q.rotulo(pct)
        assert novo == _sintetize_v1920(pct), f"divergiu de synthesize em {pct}"
        assert novo == _briefing_v1920(pct), f"divergiu de briefing em {pct}"


def test_equivale_nas_fracoes_que_o_catalogo_REALMENTE_produz():
    """Equivalência sobre a população real, não só sobre a faixa teórica.

    Varre os 35 filmes publicados, recalcula cada fração de tema e de célula
    de eixo, e confere o rótulo contra as duas cópias antigas. É o teste que
    responde "os 35 briefings de narrativa saem idênticos depois da
    extração?" sem depender de um golden file de 336 KB que quebraria por
    motivo legítimo na próxima vez que um filme for republicado.
    """
    pcts = set()
    for caminho in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        for b in d.get("buckets") or []:
            n = b.get("n_validas") or 0
            for t in b.get("temas") or []:
                pcts.add(Q.fracao_percentual(t.get("mencoes_aproximadas", 0), n))
        for linha in ((d.get("eixos") or {}).get("linhas") or []):
            for celula in (linha.get("por_bucket") or {}).values():
                pcts.add(Q.fracao_percentual(celula.get("mencoes", 0),
                                             celula.get("de_n", 0)))
    assert len(pcts) > 20, f"amostra pobre demais para valer como portão: {pcts}"
    for pct in sorted(pcts):
        assert Q.rotulo(pct) == _sintetize_v1920(pct) == _briefing_v1920(pct)


# ===========================================================================
# A extração aconteceu de fato — nenhuma cópia sobrevivente
# ===========================================================================

def test_synthesize_e_briefing_usam_o_modulo_comum():
    """Sem isto, a extração poderia ter ADICIONADO um terceiro mapa em vez
    de unificar os dois — e todos os testes acima continuariam verdes,
    medindo um módulo que ninguém chama.
    """
    from espectro24 import briefing as br
    from espectro24 import synthesize as S

    # A identidade, e não a igualdade de resultado: dois mapas idênticos
    # escritos em lugares diferentes dariam o mesmo rótulo e continuariam
    # sendo duas cópias — que é precisamente o que esta extração remove.
    assert S._rotulo_quantificador is Q.rotulo
    assert br._quantificador is Q.rotulo
