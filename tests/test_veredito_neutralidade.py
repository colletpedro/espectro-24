"""[v1.9.22, §0 + §3[V]] Neutralidade de tratamento DENTRO do veredito.

O §0 diz que os grupos recebem **formato idêntico** e que a assimetria vem
dos dados, não da apresentação. A v1.9.21 respeitou isso na estrutura (os
dois lados aparecem, com os mesmos verbos e o mesmo espaço) e o quebrou na
QUANTIDADE, num lugar que nenhuma métrica daquela versão media.

**O caso medido, `pearl-2022` sob a v1.9.21:** negativas e positivas com a
MESMA frequência (58% as duas, rótulo `cerca de metade` nas duas). O lado
positivo recebeu o rótulo — "cerca de metade das avaliações favoráveis
destaca..." — e o negativo virou "impressões negativas pontuais apontam...".
Mesmo número, dois tratamentos, e o que os separa é o SENTIMENTO do grupo.

**Por que isso recorreria sem trava, e é por isso que a trava é de §0 e não
de estilo.** A deflação veio da invariante de cautela com amostra pequena, e
a amostra pequena não é distribuída ao acaso: nos 35 filmes do catálogo,
`negativas` está em modo reduzido em 5 e `positivas` em 2 — e **não existe
nenhum filme com positivas reduzida sem negativas também reduzida**. O
catálogo é majoritariamente bem avaliado, então o grupo que falta material é
quase sempre o negativo. Uma regra que afrouxa a quantidade quando a amostra
é pequena afrouxa, na prática, sempre do mesmo lado.

**O que estes testes sustentam, e o que não sustentam.** A propriedade geral
— nenhum veredito publicado encolhe um grupo por hedge — é verificável em
qualquer texto e é o que efetivamente garante a simetria: sem deflação, não
existe o caso "um lado nomeado, o outro tratado como anedota". O teste por
FILME existe para falhar com nome próprio nos casos onde a propriedade mais
importa, não porque acrescente poder de detecção.

**Não sustentam simetria de OMISSÃO**, e isso é deliberado: rótulo ausente
não é rótulo errado. Medido nos publicados sob a v1.9.21, 3 de 14 filmes com
rótulo igual nos dois lados nomeiam um lado e calam o outro
(`avengers-endgame` e `the-hateful-eight` calam o positivo, `wonka` cala o
negativo — a omissão não tem viés de sentimento). Exigir quantificador para
os três grupos em 55 palavras produziria rigidez, e a limitação fica
registrada na spec em vez de virar validação.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import veredito as V  # noqa: E402

RESULTADO = RAIZ / "resultado"


def _publicados():
    saida = []
    for caminho in sorted(RESULTADO.glob("*.json")):
        d = json.loads(caminho.read_text(encoding="utf-8"))
        if "veredito" in d and (d.get("eixos") or {}).get("linhas"):
            saida.append((d["slug"], d, V.montar_briefing(d)))
    return saida


def _rotulo(b, grupo):
    g = (b.get("grupos") or {}).get(grupo) or {}
    f = g.get("eixo_maior_frequencia")
    return f["rotulo_quantificador"] if f else None


@pytest.fixture(scope="module")
def publicados():
    from conftest import exige_resultado_sob_a_lei
    exige_resultado_sob_a_lei()
    p = _publicados()
    if len(p) < 30:
        pytest.skip(f"poucos filmes publicados neste checkout ({len(p)})")
    return p


# ===========================================================================
# A propriedade GERAL — é ela que garante a simetria
# ===========================================================================

def test_nenhum_veredito_publicado_encolhe_um_grupo_por_hedge(publicados):
    culpados = []
    for slug, d, b in publicados:
        texto = d["veredito"].get("texto_modelo") or d["veredito"]["texto"]
        if "deflacao_por_hedge" in V.validar(texto, b):
            culpados.append(f"{slug}: {texto}")
    assert not culpados, "vereditos com deflação:\n  " + "\n  ".join(culpados)


def test_nenhum_veredito_publicado_usa_rotulo_fora_do_briefing(publicados):
    """Nos DOIS sentidos (v1.9.22) — deflação é falsidade tanto quanto
    inflação, e o §0 não distingue direção."""
    culpados = []
    for slug, d, b in publicados:
        texto = d["veredito"].get("texto_modelo") or d["veredito"]["texto"]
        if "quantificador_divergente" in V.validar(texto, b):
            autorizados = sorted(V._rotulos_autorizados(b))
            culpados.append(f"{slug}: autorizados={autorizados} · {texto}")
    assert not culpados, "vereditos com rótulo divergente:\n  " + "\n  ".join(culpados)


# ===========================================================================
# O caso onde a propriedade mais importa, com nome próprio
# ===========================================================================

def test_frequencia_igual_nos_dois_lados_recebe_tratamento_igual(publicados):
    """Filmes em que o CÓDIGO deu o mesmo rótulo a quem recomenda e a quem
    não recomenda. Se um lado for encolhido por hedge enquanto o outro é
    nomeado, o que separou os dois foi o sentimento — e o dado dizia que
    eles são iguais.

    Falha com o nome do filme de propósito: `pearl-2022` passou pela v1.9.21
    inteira sem nenhuma métrica apontá-lo, e a próxima ocorrência precisa
    ser lida, não contada.
    """
    culpados = []
    avaliados = 0
    for slug, d, b in publicados:
        neg, pos = _rotulo(b, "negativas"), _rotulo(b, "positivas")
        if not neg or neg != pos:
            continue
        avaliados += 1
        texto = d["veredito"].get("texto_modelo") or d["veredito"]["texto"]
        if V._deflacao_por_hedge(texto, b):
            culpados.append(f"{slug} (rótulo {neg!r} nos dois lados): {texto}")
    assert avaliados >= 5, (
        f"só {avaliados} filmes com rótulo igual nos dois lados — o teste "
        "não mediu quase nada")
    assert not culpados, (
        "frequência igual, tratamento diferente:\n  " + "\n  ".join(culpados))


def test_o_texto_publicado_continua_passando_em_TODAS_as_validacoes(publicados):
    """A invariante-resumo do estágio, revalidada sob as regras novas: o que
    está no ar passa no que o próprio produto exige. Se uma validação nova
    reprovar texto já publicado, o catálogo precisa ser regerado ANTES de a
    validação entrar — não depois."""
    culpados = []
    for slug, d, b in publicados:
        texto = d["veredito"].get("texto_modelo") or d["veredito"]["texto"]
        flags = V.validar(texto, b)
        if flags:
            culpados.append(f"{slug}: {flags} · {texto}")
    assert not culpados, "publicado e inválido:\n  " + "\n  ".join(culpados)
