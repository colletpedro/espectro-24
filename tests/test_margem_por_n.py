"""[v1.9.34, §2.5] A margem de contraste como LEI POR `n`.

    limiar(n) = 144,4 / √n  pontos percentuais       n = o MENOR dos três buckets

comparada em `Fraction` EXATO pela forma quadrada que elimina a raiz:

    lift > 0  e  lift² · n  >=  Fraction(2085136, 1000000)

**O que estes testes protegem, em ordem de importância:**

1. **A lei e a forma quadrada são a MESMA coisa.** Elevar ao quadrado é
   monotônico só no ramo positivo, e um erro de sinal aqui aprovaria lift
   negativo — a afirmação exatamente invertida.
2. **Nenhum float decide estado.** `144,4/√n` é IRRACIONAL, e é isso que muda
   em relação à v1.9.15: com margem inteira o arredondamento era inofensivo
   por acidente aritmético (`lift_pp` vinha de múltiplos de `100/n` e nenhum
   arredondamento cruza um inteiro). O acidente acabou. O teste que trava isso
   usa dois lifts que **colapsam no mesmo `double`** e caem em lados opostos
   do limiar exato: qualquer implementação em ponto flutuante devolve a MESMA
   resposta para os dois, e por isso erra um.
3. **O piso.** `n < 10` → `contraste` AUSENTE, não `valorativo`. Chave ausente
   distingue "não medido" de "medido e sem contraste", e nenhum consumidor
   pode confundir os dois — em particular, ausente NÃO pode cair no ramo
   `tematico` do veredito, que é o que aconteceria com um `if estado ==
   "valorativo": ... else:` desatento.
4. **A neutralidade do §0, travada por teste e não por convenção.** Os três
   buckets de um filme recebem o MESMO limiar. `n` é o MENOR dos três porque o
   lift é uma diferença entre buckets e a precisão da diferença é governada
   pelo menor denominador.
5. **Ninguém RECALCULA a decisão a partir de `lift_pp`.** A varredura da
   v1.9.34 achou dois consumidores que faziam isso (`veredito.py:_maior_lift`
   e `frontend/js/filme.js:veredito()`); os testes de envenenamento abaixo
   existem para que não voltem.
"""
from __future__ import annotations

import json
import math
from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from espectro24 import eixos as E

getcontext().prec = 60

# A constante da lei, escrita aqui INDEPENDENTEMENTE do código, para que um
# erro de digitação em `config.py` não passe despercebido por os dois lados
# lerem a mesma fonte.
K_PP = Decimal("144.4")
K2 = Fraction(2085136, 1000000)


def _limiar_exato(n: int) -> Decimal:
    """O limiar como FRAÇÃO de 0 a 1 (não pp), em 60 dígitos."""
    return (K_PP / Decimal(100)) / Decimal(n).sqrt()


def _fracao_de(d: Decimal, escala: int = 10 ** 30) -> Fraction:
    return Fraction(int(d * escala), escala)


def _uniforme(bucket_eixos, n_por_bucket):
    """`{bucket: {id: [eixos]}}`; `n_por_bucket` é dict bucket→n."""
    out = {}
    for bucket, n in n_por_bucket.items():
        reviews = {f"{bucket}:{i}": [] for i in range(n)}
        for eixo, k in bucket_eixos.get(bucket, []):
            for i in range(k):
                reviews[f"{bucket}:{i}"].append(eixo)
        out[bucket] = reviews
    return out


# --------------------------------------------------------------------------
# 1. A forma quadrada reproduz a lei
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", [10, 12, 15, 20, 27, 30, 32, 34, 37, 39, 40,
                               50, 64, 100, 147, 400])
def test_forma_quadrada_reproduz_a_lei_em_alta_precisao(n):
    """`lift² · n >= K²` decide igual a `lift >= 144,4/√n` em 60 dígitos.

    Varre a faixa de `n` que o catálogo tem hoje (5 a 40) mais a que a
    expansão trará, e testa dos dois lados do limiar com folga larga.
    """
    t = _limiar_exato(n)
    for delta in (Decimal("-0.05"), Decimal("-0.001"), Decimal("-1e-20"),
                  Decimal("1e-20"), Decimal("0.001"), Decimal("0.05")):
        alvo = t + delta
        if alvo <= 0:
            continue
        lift = _fracao_de(alvo)
        esperado = Decimal(lift.numerator) / Decimal(lift.denominator) >= t
        assert E.acima_da_margem(lift, n) is bool(esperado), (
            f"n={n} delta={delta}: exato={esperado} código={E.acima_da_margem(lift, n)}")


@pytest.mark.parametrize("n", [10, 20, 30, 40, 50, 100])
def test_pontos_de_fronteira_exatos(n):
    """Exatamente NO limiar aprova (`>=`, a semântica da v1.9.15); um quantum
    abaixo, reprova."""
    t = _fracao_de(_limiar_exato(n))
    # `t` é uma truncagem de 30 dígitos do irracional, logo t < limiar real:
    # ela reprova. t + 1 ulp da escala já ultrapassa.
    assert E.acima_da_margem(t + Fraction(1, 10 ** 30), n) is True
    assert E.acima_da_margem(t - Fraction(1, 10 ** 30), n) is False


def test_lift_nao_positivo_reprova_sempre():
    """O quadrado é monotônico só no ramo positivo. Sem a guarda de sinal,
    `lift = -0.5` com n=40 daria `0,25 · 40 = 10 >= 2,085` — APROVADO, e a
    afirmação publicada seria a inversa da verdadeira."""
    for n in (10, 20, 40, 100):
        assert E.acima_da_margem(Fraction(0), n) is False
        assert E.acima_da_margem(Fraction(-1, 2), n) is False
        assert E.acima_da_margem(Fraction(-99, 100), n) is False


def test_a_constante_e_o_quadrado_de_1444_milesimos():
    """Se alguém "simplificar" a constante, isto reclama."""
    assert K2 == Fraction(1444, 1000) ** 2
    assert E.MARGEM_LEI_K2 == K2


@pytest.mark.parametrize("n,esperado_pp", [(10, 45.7), (20, 32.3), (30, 26.4),
                                            (40, 22.8), (50, 20.4), (100, 14.4)])
def test_limiar_pp_e_derivado_para_exibicao(n, esperado_pp):
    """`limiar_pp` existe só para carimbo e leitura humana — a tabela de
    §2.5 tem de bater com ele."""
    assert round(E.limiar_pp(n), 1) == esperado_pp


# --------------------------------------------------------------------------
# 2. Nenhum float decide estado
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", [20, 30, 40, 100])
def test_dois_lifts_indistinguiveis_em_float_sao_separados_pelo_exato(n):
    """**O teste que falha se alguém trocar a comparação por ponto flutuante.**

    Construção: dois racionais que caem em lados OPOSTOS do limiar exato e
    cuja distância é menor que o espaçamento do `double` naquela magnitude —
    logo `float(a) == float(b)`. Qualquer implementação que converta para
    float devolve necessariamente a MESMA resposta para os dois, e portanto
    erra um. A comparação exata separa.
    """
    t = _limiar_exato(n)
    abaixo = _fracao_de(t - Decimal("1e-25"))
    acima = _fracao_de(t + Decimal("1e-25"))

    # a premissa do teste: em `double` os dois são o mesmo número
    assert float(abaixo) == float(acima), (
        "premissa quebrada: escolha um delta menor")

    assert E.acima_da_margem(abaixo, n) is False
    assert E.acima_da_margem(acima, n) is True


def test_acima_da_margem_recusa_float():
    """Aceitar `float` reintroduz o defeito por uma porta lateral: quem passar
    `0.2283` em vez de `Fraction` não recebe erro, recebe uma resposta que
    parece certa."""
    with pytest.raises((TypeError, ValueError)):
        E.acima_da_margem(0.25, 40)


# --------------------------------------------------------------------------
# 3. O piso `n < 10` — ausente, não `valorativo`
# --------------------------------------------------------------------------

def test_contraste_e_None_abaixo_do_piso():
    cls = _uniforme({"negativas": [("ritmo", 8)]},
                    {"negativas": 8, "medianas": 6, "positivas": 5})
    lifts = E.lifts(E.frequencias(cls))
    assert E.contraste(lifts, n=5) is None


def test_o_piso_e_10_e_a_fronteira_e_inclusiva():
    cls = _uniforme({"negativas": [("ritmo", 10)]},
                    {"negativas": 10, "medianas": 10, "positivas": 10})
    lifts = E.lifts(E.frequencias(cls))
    assert E.contraste(lifts, n=10) is not None
    assert E.contraste(lifts, n=9) is None
    assert E.MARGEM_N_MINIMO == 10


def test_bloco_omite_a_chave_contraste_abaixo_do_piso():
    """AUSÊNCIA da chave, não `None` serializado — é o mesmo estatuto de
    `montar_bloco` devolver `None` sem classificação, e de `share_real`
    omitido sem distribuição."""
    cls = _uniforme({"negativas": [("ritmo", 8)]},
                    {"negativas": 8, "medianas": 6, "positivas": 5})
    analisadas = {b: set(rs) for b, rs in cls.items()}
    bloco = E.montar_bloco(cls, analisadas, {})
    assert "contraste" not in bloco
    # o RESTO do bloco continua publicado: o que falta é só a decisão binária
    assert bloco["linhas"]
    assert bloco["margem"]["n"] == 5
    assert "acima_da_margem" in bloco["linhas"][0]["por_bucket"]["negativas"]


def test_ausente_e_distinguivel_de_valorativo_no_briefing():
    """`briefing._contraste_do_output` não pode devolver "valorativo" nem
    deixar o veredito cair no ramo `tematico` por omissão."""
    from espectro24 import briefing as B
    out = {"eixos": {"taxonomia_id": E.TAXONOMIA_ID, "linhas": []}}
    c = B._contraste_do_output(out)
    assert c is None or c.get("estado") is None


def test_veredito_nao_e_gerado_sem_estado_de_contraste():
    """Sem `contraste`, `montar_briefing` devolve None e não há veredito — a chave `veredito` some
    do JSON, no estatuto aditivo de `ficha` (§3[F]) e `distribuicao` (§3[G]).

    O que este teste IMPEDE é o modo de falha silencioso: `veredito.py:341`
    faz `if estado == "valorativo": ... else: <ramo temático>`, e um estado
    ausente cairia no ramo TEMÁTICO — publicando "a medição encontrou assunto
    próprio de pelo menos um grupo" sobre um filme cuja medição se recusou a
    decidir.
    """
    from espectro24 import veredito as V
    out = {
        "slug": "teste", "buckets": [],
        "eixos": {"taxonomia_id": E.TAXONOMIA_ID,
                  "margem": {"n": 5, "limiar_pp": 64.6},
                  "linhas": [{"eixo": "ritmo", "por_bucket": {}}]},
    }
    assert V.montar_briefing(out) is None


# --------------------------------------------------------------------------
# 4 e 5. Neutralidade do §0, e `n` é o MENOR dos três
# --------------------------------------------------------------------------

def test_os_tres_buckets_recebem_o_mesmo_limiar():
    """A neutralidade estrutural do §0, travada por teste.

    Dentro de um filme não existe caminho pelo qual `negativas` receba um
    limiar e `positivas` outro. Montado com os três buckets de tamanhos
    DIFERENTES de propósito: se o limiar fosse resolvido por bucket em vez de
    por filme, cada um receberia um número diferente e este teste cairia.
    """
    cls = _uniforme({}, {"negativas": 30, "medianas": 40, "positivas": 37})
    freqs = E.frequencias(cls)
    n = E.n_efetivo(freqs)
    limiares = {b: E.limiar_pp(n) for b in cls}
    assert len(set(limiares.values())) == 1


def test_n_efetivo_e_o_menor_dos_tres_buckets():
    freqs = E.frequencias(_uniforme(
        {}, {"negativas": 30, "medianas": 40, "positivas": 37}))
    assert E.n_efetivo(freqs) == 30

    freqs = E.frequencias(_uniforme(
        {}, {"negativas": 40, "medianas": 39, "positivas": 40}))
    assert E.n_efetivo(freqs) == 39

    freqs = E.frequencias(_uniforme(
        {}, {"negativas": 5, "medianas": 6, "positivas": 8}))
    assert E.n_efetivo(freqs) == 5


def test_o_menor_bucket_governa_e_nao_a_media():
    """`pearl-2022` é [27, 40, 40]: média 35,7 (limiar 24,2pp) contra mínimo
    27 (limiar 27,8pp). A diferença atravessa um passo do quantum, então a
    escolha entre média e mínimo MUDA estado no catálogo real."""
    freqs = E.frequencias(_uniforme({}, {"negativas": 27, "medianas": 40,
                                          "positivas": 40}))
    assert E.n_efetivo(freqs) == 27
    assert round(E.limiar_pp(E.n_efetivo(freqs)), 1) == 27.8


# --------------------------------------------------------------------------
# 8. Envenenamento — ninguém recalcula a decisão a partir de `lift_pp`
# --------------------------------------------------------------------------

def _bloco_publicado(lift_pp: float, acima: bool, n: int = 40):
    """Um bloco `eixos` mínimo, no schema da v1.9.34."""
    return {
        "slug": "teste",
        "buckets": [{"bucket": "negativas", "share_real": 50,
                     "modo": "completo", "estado_piso": "completa"},
                    {"bucket": "positivas", "share_real": 50,
                     "modo": "completo", "estado_piso": "completa"}],
        "eixos": {
            "taxonomia_id": E.TAXONOMIA_ID,
            "margem": {"lei": "lift^2 * n >= 2085136/1000000",
                       "constante_quadrada": [2085136, 1000000],
                       "n": n, "limiar_pp": E.limiar_pp(n)},
            "margem_lift_pp": E.limiar_pp(n),
            "contraste": "tematico",
            "linhas": [{
                "eixo": "ritmo",
                "por_bucket": {
                    "negativas": {"mencoes": 20, "de_n": n, "freq_pct": 50.0,
                                  "lift_pp": lift_pp, "acima_da_margem": acima,
                                  "tema": "Ritmo arrastado",
                                  "exemplo_parafraseado": "",
                                  "temas_no_mesmo_eixo": []},
                    "positivas": {"mencoes": 2, "de_n": n, "freq_pct": 5.0,
                                  "lift_pp": -lift_pp, "acima_da_margem": False,
                                  "tema": None, "exemplo_parafraseado": None,
                                  "temas_no_mesmo_eixo": []}},
                "bullet_de": {"negativas": "contraste", "positivas": None}}],
        },
    }


def test_envenenar_lift_pp_nao_muda_a_decisao_publicada():
    """**O teste central do item 1 da v1.9.34.**

    `lift_pp` é DERIVADO e arredondado a uma casa. Envenená-lo com um valor
    absurdo não pode mudar decisão nenhuma — se mudar, algum consumidor ainda
    está recalculando a margem a partir dele, que é o defeito que esta versão
    fecha.
    """
    from espectro24 import veredito as V
    limpo = V.montar_briefing(_bloco_publicado(45.0, True))
    for veneno in (0.0, -999.0, 1e9):
        envenenado = V.montar_briefing(_bloco_publicado(veneno, True))
        assert (envenenado["grupos"]["negativas"]["eixo_maior_lift"]
                ["acima_da_margem"]) is True
        assert (envenenado["grupos"]["negativas"]["eixo_maior_lift"]["eixo"]
                == limpo["grupos"]["negativas"]["eixo_maior_lift"]["eixo"])


def test_inverter_acima_da_margem_MUDA_a_decisao():
    """O simétrico, e ele é obrigatório: sem este teste, um consumidor que
    ignorasse os dois campos e devolvesse `True` fixo passaria no teste acima.
    Aqui provamos que o campo é de fato LIDO."""
    from espectro24 import veredito as V
    b = V.montar_briefing(_bloco_publicado(45.0, False))
    assert b["grupos"]["negativas"]["eixo_maior_lift"]["acima_da_margem"] is False


def test_remover_acima_da_margem_e_ERRO_nao_recalculo_silencioso():
    """Um bloco sem o campo é anterior à v1.9.34 ou foi corrompido. Recalcular
    a partir de `lift_pp` seria voltar ao defeito em silêncio — a mesma
    política de `_carregar_consenso_producao`: erro explícito, nunca fallback.
    """
    from espectro24 import veredito as V
    out = _bloco_publicado(45.0, True)
    del out["eixos"]["linhas"][0]["por_bucket"]["negativas"]["acima_da_margem"]
    with pytest.raises((KeyError, ValueError)):
        V.montar_briefing(out)


def test_nenhuma_comparacao_de_lift_pp_com_margem_no_codigo():
    """Sentinela de fonte, complementar aos diferenciais acima: a expressão
    que foi o defeito (`lift_pp` comparado a uma margem) não pode reaparecer
    em `veredito.py` nem em `filme.js`."""
    import re
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    padrao = re.compile(r"lift_pp\"?\]?\s*>=?\s*margem|lift_pp\s*>=\s*\w*margem")
    for rel in ("src/espectro24/veredito.py", "frontend/js/filme.js"):
        texto = (raiz / rel).read_text(encoding="utf-8")
        # Descarta PROSA, não código. Os dois arquivos CITAM o defeito por
        # extenso na documentação (é assim que ele fica registrado), e uma
        # sentinela que casasse a citação seria um teste que só se satisfaz
        # apagando a explicação.
        #
        # A regra é a crase: em `veredito.py` ela só existe em docstring
        # (Python não tem sintaxe de crase) e em `filme.js` só em comentário
        # (conferido: zero template literals). Linha com crase é prosa.
        codigo = "\n".join(
            l for l in texto.splitlines()
            if not l.lstrip().startswith(("#", "//", "*")) and "`" not in l)
        assert not padrao.search(codigo), f"{rel} voltou a recalcular a margem"


# --------------------------------------------------------------------------
# 9. O filme sintético degradado conforma ao mesmo schema dos 35 reais
# --------------------------------------------------------------------------

def _chaves_da_lei_no_bloco(bloco: dict) -> dict:
    return {
        "tem_margem": "margem" in bloco,
        "margem_tem_n": isinstance((bloco.get("margem") or {}).get("n"), int),
        "margem_tem_constante": (
            (bloco.get("margem") or {}).get("constante_quadrada")
            == [2085136, 1000000]),
        "celulas_tem_acima_da_margem": all(
            "acima_da_margem" in cel
            for linha in bloco.get("linhas") or []
            for cel in (linha.get("por_bucket") or {}).values()),
    }


def test_filme_sintetico_degradado_conforma_ao_schema_da_lei():
    """`frontend/build_data.py` carrega o bloco `eixos` do filme degradado
    HARDCODED — é o único lugar que exercita `sem_numero`, `sem_analise` e
    célula vazia lado a lado. Sem este teste ele fica para trás numa mudança
    de schema **e continua verde**, testando um schema que não existe mais.
    """
    import sys
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(raiz / "frontend"))
    try:
        import build_data
    finally:
        sys.path.pop(0)
    bloco = build_data._filme_degradado()["eixos"]
    assert _chaves_da_lei_no_bloco(bloco) == {
        "tem_margem": True, "margem_tem_n": True,
        "margem_tem_constante": True, "celulas_tem_acima_da_margem": True}


def test_o_degradado_tem_o_MESMO_conjunto_de_chaves_de_um_filme_real():
    """Não basta ter os campos: eles têm de ser os MESMOS de um filme real,
    senão a divergência volta pela borda."""
    import json
    import sys
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    real = json.loads((raiz / "resultado" / "cure.json").read_text(
        encoding="utf-8"))["eixos"]
    if "margem" not in real:
        pytest.skip(
            "resultado/cure.json ainda não foi republicado sob a v1.9.34 "
            "(sem o bloco `margem`). Este teste compara o fixture sintético "
            "com um filme REAL, e só tem sentido depois da republicação — "
            "ele volta sozinho quando ela acontecer. A conformidade do "
            "fixture ao schema da lei é checada sem depender disto em "
            "`test_filme_sintetico_degradado_conforma_ao_schema_da_lei`.")
    sys.path.insert(0, str(raiz / "frontend"))
    try:
        import build_data
    finally:
        sys.path.pop(0)
    deg = build_data._filme_degradado()["eixos"]

    ignorar = {"rotulagem", "fonte_classificacao", "spec_version", "contraste",
                "verificador"}
    assert set(real) - ignorar == set(deg) - ignorar

    def chaves_de_celula(bloco):
        return {frozenset(cel)
                for linha in bloco["linhas"]
                for cel in linha["por_bucket"].values()}
    assert chaves_de_celula(deg) <= chaves_de_celula(real)


# --------------------------------------------------------------------------
# A LINHA DE AUSÊNCIA DE VEREDITO — texto travado por teste
# --------------------------------------------------------------------------

# O texto DEFINITIVO, decidido pelo dono do projeto (SPEC §2.5). Escrito aqui
# por extenso, e não importado de lugar nenhum: um teste que lesse a frase da
# mesma fonte que o código não travaria nada.
LINHA_AUSENCIA = (
    "A amostra analisada deste filme é pequena demais para dizer se os "
    "grupos falam de coisas diferentes ou se falam das mesmas coisas e "
    "divergem no julgamento."
)


def _js_filme():
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent
            / "frontend" / "js" / "filme.js").read_text(encoding="utf-8")


def test_a_linha_de_ausencia_esta_no_frontend_palavra_por_palavra():
    """No padrão do teste que protege a exceção de hedge por BASE da v1.9.22:
    a frase é decisão de produto, e uma reescrita "de estilo" a desfaria em
    silêncio. Comparação sobre o texto CONCATENADO, não sobre o literal, para
    que quebrar a linha em outro ponto não seja falso negativo."""
    import re
    js = _js_filme()
    trecho = js[js.index("function semEstadoDeContraste"):]
    trecho = trecho[:trecho.index("}")]
    partes = re.findall(r'"((?:[^"\\]|\\.)*)"', trecho)
    assert "".join(partes) == LINHA_AUSENCIA


def test_a_linha_de_ausencia_nao_tem_algarismo_nem_quantificador():
    """As duas proibições que ela herda: zero dígito (v1.9.20) e nenhum
    quantificador de MAGNITUDE (v1.9.22). "pequena" qualifica a AMOSTRA — a
    base —, que é exatamente a exceção que a v1.9.22 preservou; o que seria
    proibido é encolher o achado ("poucos", "alguns", "pontuais")."""
    assert not any(c.isdigit() for c in LINHA_AUSENCIA)
    for proibido in ("poucos", "poucas", "alguns", "algumas", "pontuais",
                     "raros", "raras", "alguma medida"):
        assert proibido not in LINHA_AUSENCIA.lower()


def test_a_linha_poe_os_DOIS_estados_no_MESMO_nivel():
    """A neutralidade do §0 aplicada à frase que explica por que não há
    estado. Discordar sobre o mesmo assunto é achado de primeira classe neste
    produto — 29 dos 35 filmes publicam exatamente isso —, e uma redação como
    "ou apenas discordam" o rebaixaria a resíduo do outro estado."""
    assert "falam de coisas diferentes" in LINHA_AUSENCIA
    assert "falam das mesmas coisas e divergem no julgamento" in LINHA_AUSENCIA
    assert "apenas discordam" not in LINHA_AUSENCIA


def test_a_linha_de_ausencia_NAO_usa_a_classe_do_veredito():
    """Ela ocupa a POSIÇÃO do veredito e não pode ser lida como um. `.verdict`
    é serifa 1,22rem em `--text`; `.verdict-absent` é sans menor em
    `--text-dim`. **Classe própria, não modificador de `.verdict`** — um
    modificador convida a herdar a serifa de volta num refactor e a linha
    viraria veredito por acidente de CSS."""
    from pathlib import Path
    js = _js_filme()
    trecho = js[js.index("function veredictoBlock"):]
    trecho = trecho[:trecho.index("\n  function ", 10)]
    assert 'aviso.className = "verdict-absent"' in trecho
    css = (Path(__file__).resolve().parent.parent
           / "frontend" / "css" / "styles.css").read_text(encoding="utf-8")
    assert ".verdict-absent {" in css
    assert ".verdict--" not in css          # nada de modificador


def test_a_linha_e_HASTEADA_e_nao_depende_da_ordem_do_arquivo():
    """**Regressão de um defeito REAL desta sessão, pego no navegador com a
    suíte inteira verde.**

    A primeira versão era `var SEM_ESTADO_DE_CONTRASTE = "…"` declarado ao
    lado de quem usa (~linha 900). Mas `render(film)` roda na **linha 110** —
    muito antes —, então no momento da chamada o `var` ainda valia `undefined`,
    e `textContent = undefined` grava **string vazia** (não a palavra
    "undefined"). A página renderizava o `<p class="verdict-absent">` VAZIO, e
    nada gritava: sem erro de console, sem teste vermelho.

    Declaração de função é hasteada inteira e torna a ordem irrelevante. Este
    teste falha se alguém a converter de volta para `var`/`const`.
    """
    js = _js_filme()
    assert "function semEstadoDeContraste" in js
    for forma in ("var SEM_ESTADO_DE_CONTRASTE =",
                  "const SEM_ESTADO_DE_CONTRASTE =",
                  "let SEM_ESTADO_DE_CONTRASTE ="):
        codigo = "\n".join(l for l in js.splitlines()
                           if not l.lstrip().startswith("//"))
        assert forma not in codigo
