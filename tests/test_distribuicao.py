"""[v1.4.0] Distribuição real de notas — mock/fixtures, ZERO rede.

Cobre: parsing do histograma (incl. níveis zerados, que não têm <a>),
agregação por bucket, bordas do rótulo de peso, o fallback completo quando
não há distribuição (regras v1.2.1 seguem ativas) e a validação de
ancoragem do narrador.
"""
import pytest

from conftest import CONTAGENS_3_17_79, FakeFetcher, fx, histograma_de_contagens

from espectro24.collector import collect_distribuicao
from espectro24.models import BucketResult, Distribuicao, LevelResult, Review, Tema
from espectro24.parser import parse_rating_histogram
from espectro24.render import (
    DISCLAIMER_COM_DISTRIBUICAO,
    DISCLAIMER_SEM_DISTRIBUICAO,
    aplicar_distribuicao,
    build_output,
    render_terminal,
)
# [v1.9.11] O narrador PRÉ-BRIEFING foi arquivado
# (`experimentos-narrador-antigo-arquivado/narrador_antigo.py`, ver SPEC.md
# "Integração"). Os testes deste arquivo que o exercitam continuam aqui —
# eles cobrem a maquinaria de honestidade COMPARTILHADA, que segue viva em
# `synthesize.py` — e importam o narrador antigo de onde ele está agora.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent
                        / "experimentos-narrador-antigo-arquivado"))
from espectro24.synthesize import (
    _rotulo_peso,
    _rotulo_peso_completo,
    _vocabulario_peso_ok,
)
from narrador_antigo import (  # noqa: E402
    NARRATOR_SYSTEM_PROMPT,
    _serialize_output_for_narrator,
    build_narrator_prompt,
    narrate_output,
)
from espectro24.urls import histogram_cache_key, histogram_url


# --- parsing do fragmento CSI ---

def test_parse_histograma_conta_os_10_niveis():
    h = parse_rating_histogram(fx("histograma_cure.html"))
    assert set(h) == {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0}
    assert h[0.5] == 456          # separador de milhar tratado
    assert h[4.0] == 110990
    assert sum(h.values()) == 375278


def test_parse_histograma_captura_niveis_zerados():
    """Nível sem nota nenhuma vem como <span> (não <a>) e title='No ★½ ratings'.
    Um parser que buscasse só `a.barcolumn` perderia esses e inflaria o total."""
    h = parse_rating_histogram(fx("histograma_filme_minusculo.html"))
    assert h[1.5] == 0
    assert h[4.5] == 0
    assert h[3.0] == 8
    assert sum(h.values()) == 26   # total do filme minúsculo, com os zeros


@pytest.mark.parametrize("html", [
    "<html><body>sem tabela</body></html>",
    "<table class='chart'><tbody><tr><th>★</th></tr></tbody></table>",  # 1 nível só
    "",
])
def test_parse_histograma_estrutura_inesperada_vira_none(html):
    assert parse_rating_histogram(html) is None


# --- agregação por bucket ---

def test_agregacao_por_bucket_do_cure():
    """v1.9.0 — sob a opção C o `cure` sai 2/8/90 (era 3/17/79 até a v1.8.2).

    6.733 / 29.585 / 338.960 sobre 375.278. A mudança é a consequência
    declarada em §2.2 (o 3,5★ populoso migra para positivas), não regressão.
    """
    d = Distribuicao.de_histograma(parse_rating_histogram(fx("histograma_cure.html")))
    assert d.n_notas_total == 375278
    assert d.por_bucket == {"negativas": 2, "medianas": 8, "positivas": 90}
    assert d.fonte == "letterboxd_histograma"


def test_agregacao_com_histograma_sintetico_exato():
    # 10 por nível => 4/2/4 níveis sob a opção C => 40/20/40 de 100
    por_nivel = {n: 10 for n in [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]}
    d = Distribuicao.de_histograma(por_nivel)
    assert d.por_bucket == {"negativas": 40, "medianas": 20, "positivas": 40}
    assert d.n_notas_total == 100


def test_sem_nota_alguma_nao_produz_distribuicao():
    assert Distribuicao.de_histograma({n: 0 for n in
                                       [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]}) is None


def test_metadata_serializa_niveis_como_string():
    d = Distribuicao.de_histograma({n: 1 for n in
                                    [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]})
    meta = d.metadata()
    assert meta["por_nivel"]["0.5"] == 1
    assert meta["n_notas_total"] == 10
    assert meta["fonte"] == "letterboxd_histograma"


# --- bordas do rótulo de peso (mesma convenção da v1.2.3: mais fraco vence) ---

@pytest.mark.parametrize("pct,esperado", [
    # v1.6.0 — faixa NOVA "uma fração mínima" (<5%), para não achatar 1% e 8%
    (0, "uma fração mínima"), (4, "uma fração mínima"),
    (5, "uma pequena minoria"),   # borda: <5 é exclusivo -> 5 cai na seguinte
    (9, "uma pequena minoria"),
    (10, "uma minoria"),            # borda: pequena minoria exige pct < 10
    (24, "uma minoria"),
    (25, "uma minoria"),            # borda: empata com parcela expressiva -> fraco
    (26, "uma parcela expressiva"),
    (44, "uma parcela expressiva"),
    (45, "uma parcela expressiva"),  # borda: empata com a maioria -> fraco
    (46, "a maioria"),
    (69, "a maioria"),
    (70, "a maioria"),              # borda: empata com a grande maioria -> fraco
    (71, "a grande maioria"),
    (100, "a grande maioria"),
])
def test_rotulo_peso_resolve_faixas_e_bordas(pct, esperado):
    assert _rotulo_peso(pct) == esperado


def test_rotulo_peso_completo_sempre_traz_o_percentual():
    assert _rotulo_peso_completo(79) == "a grande maioria das notas (~79%)"
    assert _rotulo_peso_completo(3) == "uma fração mínima das notas (~3%)"
    assert _rotulo_peso_completo(8) == "uma pequena minoria das notas (~8%)"


# --- coleta: 1 requisição, cache, e falha que não quebra o pipeline ---

def test_collect_distribuicao_usa_endpoint_csi_e_uma_requisicao():
    key = histogram_cache_key("cure")
    f = FakeFetcher({key: fx("histograma_cure.html")})
    d = collect_distribuicao(f, "cure")
    assert d.por_bucket["positivas"] == 90   # v1.9.0, opção C (era 79)
    assert len(f.calls) == 1
    assert f.calls[0] == (histogram_url("cure"), key)
    assert "csi/film/cure/rating-histogram" in histogram_url("cure")


def test_collect_distribuicao_falha_de_rede_vira_none_sem_levantar():
    key = histogram_cache_key("cure")
    f = FakeFetcher({}, raise_on={key})
    assert collect_distribuicao(f, "cure") is None


def test_collect_distribuicao_html_invalido_vira_none():
    key = histogram_cache_key("cure")
    f = FakeFetcher({key: "<html>nada aqui</html>"})
    assert collect_distribuicao(f, "cure") is None


# --- helpers de output ---

def _bucket(nome, alvo, n=5, temas=None):
    lvl = LevelResult(4.0, 150, 1, n, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{nome}{i}", rating=4.0, text="x" * 200,
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text="x" * 200) for i in range(n)]
    return BucketResult(nome=nome, alvo=alvo, modo="completo", niveis=[lvl],
                        temas=temas or [Tema("ritmo", 3, 5, "acharam o ritmo lento")],
                        observacao_geral=f"as reviews {nome} comentam o ritmo")


def _output(com_distribuicao=True):
    # v1.9.0: histograma SINTÉTICO com shares 3/17/79 em vez do histograma
    # real do `cure` — as asserções abaixo são sobre rótulo de peso e
    # ancoragem, não sobre onde fica a fronteira (ver conftest).
    buckets = [_bucket("negativas", 40), _bucket("medianas", 40),
               _bucket("positivas", 40)]
    d = None
    if com_distribuicao:
        d = Distribuicao.de_histograma(histograma_de_contagens(**CONTAGENS_3_17_79))
    return build_output("cure", buckets, "2026-01-01", {}, 252, distribuicao=d)


# --- JSON de saída ---

def test_output_traz_bloco_distribuicao_e_share_por_bucket():
    out = _output()
    assert out["distribuicao"]["n_notas_total"] == 10000   # sintético (conftest)
    assert out["distribuicao"]["por_bucket"]["positivas"] == 79
    shares = {b["bucket"]: b.get("share_real") for b in out["buckets"]}
    assert shares == {"negativas": 3, "medianas": 17, "positivas": 79}


def test_output_sem_distribuicao_nao_inventa_share():
    out = _output(com_distribuicao=False)
    assert out["distribuicao"] is None
    for b in out["buckets"]:
        assert "share_real" not in b   # ausente, não 0 — "não coletado" != "0%"


def test_aplicar_distribuicao_reproduz_a_estrutura_do_caminho_fresh():
    """O caminho --reuse-synthesis usa aplicar_distribuicao; tem que dar o
    MESMO resultado que build_output produz no caminho fresh."""
    d = Distribuicao.de_histograma(histograma_de_contagens(**CONTAGENS_3_17_79))
    fresh = _output()
    reaplicado = aplicar_distribuicao(_output(com_distribuicao=False), d)
    assert reaplicado["distribuicao"] == fresh["distribuicao"]
    assert [b.get("share_real") for b in reaplicado["buckets"]] == \
           [b.get("share_real") for b in fresh["buckets"]]


def test_aplicar_distribuicao_none_limpa_shares_orfaos():
    out = aplicar_distribuicao(_output(), None)
    assert out["distribuicao"] is None
    for b in out["buckets"]:
        assert "share_real" not in b


# --- render de terminal ---

def test_render_mostra_share_no_header_dos_tres_grupos():
    render = render_terminal(_output())
    assert "~3% das notas" in render
    assert "~17% das notas" in render
    assert "~79% das notas" in render


def test_render_troca_o_disclaimer_conforme_o_dado():
    assert DISCLAIMER_COM_DISTRIBUICAO in render_terminal(_output())
    assert DISCLAIMER_SEM_DISTRIBUICAO in render_terminal(
        _output(com_distribuicao=False))


def test_render_sem_distribuicao_nao_mostra_share():
    assert "% das notas" not in render_terminal(_output(com_distribuicao=False))


def test_render_flag_peso_nao_ancorado_visivel():
    out = _output()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {"peso_nao_ancorado": True}
    assert "não foi ancorado no seu peso" in render_terminal(out, tom="narrativo")


# --- prompt: a regra (c) inverte SÓ quando há distribuição ---

def test_prompt_sem_distribuicao_e_byte_identico_ao_historico():
    assert build_narrator_prompt(False) == NARRATOR_SYSTEM_PROMPT
    assert "PROIBIDO comparar tamanhos entre grupos" in NARRATOR_SYSTEM_PROMPT


def test_prompt_com_distribuicao_inverte_a_regra():
    p = build_narrator_prompt(True)
    assert "PESO REAL DE CADA GRUPO" in p
    assert "ANCORAGEM OBRIGATÓRIA" in p
    assert "ABERTURA OBRIGATÓRIA" in p
    assert "ÊNFASE PROPORCIONAL" in p
    assert "RESPEITO À MINORIA" in p
    # a proibição da v1.2.1 sai de cena
    assert "PROIBIDO comparar tamanhos entre grupos" not in p
    # mas a proibição de score agregado permanece
    assert "nota média" in p


def test_prompt_muda_apenas_a_regra_c():
    """A regra (c) — e o que depende diretamente dela (marcação de
    perspectiva e o exemplo de estilo, v1.5.0, que dependem do share_real) —
    é o que muda entre as variantes; os marcadores dos três movimentos e das
    invariantes independentes de distribuição seguem presentes nas duas."""
    sem, com = build_narrator_prompt(False), build_narrator_prompt(True)
    for marcador in ("MOVIMENTO 1", "MOVIMENTO 2", "MOVIMENTO 3",
                     "CRITÉRIO DE CATEGORIA", "QUANTIFICADOR PRÉ-COMPUTADO",
                     "consensos_usados", "ANTI-SPOILER"):
        assert marcador in sem and marcador in com
    # v1.6.0: RITMO/REGISTRO saíram do narrador (migraram para o editor §E2)
    for removido in ("RITMO (v1.5.0", "REGISTRO (v1.5.0"):
        assert removido not in sem and removido not in com
    # só a com_distribuicao carrega marcação de perspectiva e o few-shot,
    # que dependem do share_real (não existe sem distribuição)
    assert "MARCAÇÃO DE PERSPECTIVA" not in sem
    assert "MARCAÇÃO DE PERSPECTIVA" in com


def test_narrador_recebe_a_variante_certa_conforme_o_output():
    capturado = {}

    def fake(system, user, model):
        capturado["system"] = system
        capturado["user"] = user
        return ('{"narrativa": "a grande maioria das notas (~79%) veio de quem '
                'gostou e elogia o ritmo; uma minoria das notas (~17%) ficou no '
                'meio; uma pequena minoria das notas (~3%) nao gostou.", '
                '"consensos_usados": []}')

    narrate_output(_output(), client_call=fake, model="m")
    assert "PESO REAL DE CADA GRUPO" in capturado["system"]
    assert "DISTRIBUIÇÃO REAL DAS NOTAS" in capturado["user"]
    assert 'rotulo_peso: "a grande maioria das notas (~79%)"' in capturado["user"]

    capturado.clear()
    narrate_output(_output(com_distribuicao=False), client_call=fake, model="m")
    assert "PESO REAL DE CADA GRUPO" not in capturado["system"]
    assert "DISTRIBUIÇÃO REAL DAS NOTAS" not in capturado["user"]


# --- serialização ---

def test_serializacao_injeta_rotulo_peso_por_grupo():
    ser = _serialize_output_for_narrator(_output())
    assert "DISTRIBUIÇÃO REAL DAS NOTAS" in ser
    assert "10000 notas no total" in ser   # histograma sintético (conftest)
    assert 'rotulo_peso: "uma fração mínima das notas (~3%)"' in ser
    assert 'rotulo_peso: "a grande maioria das notas (~79%)"' in ser


def test_serializacao_sem_distribuicao_nao_menciona_peso():
    ser = _serialize_output_for_narrator(_output(com_distribuicao=False))
    assert "rotulo_peso" not in ser
    assert "DISTRIBUIÇÃO REAL" not in ser


# --- validação: ancoragem de peso ---

_PROSA_ANCORADA = (
    '{"narrativa": "Quem gostou é a grande maioria das notas (~79%), e para '
    'esse grupo o filme prende do início ao fim, equilibra humor e drama sem '
    'perder o ritmo em nenhum momento. Já uma minoria das notas (~17%) ficou '
    'no meio-termo. Nessa leitura, o ritmo pesa mais do que deveria. Uma '
    'pequena minoria das notas (~3%) reclamou do arrastado. Para eles, nada '
    'funciona.", '
    '"consensos_usados": [], "quantificadores_usados": [], '
    '"marcadores_perspectiva": ['
    '{"grupo": "medianas", "trecho": "Nessa leitura, o ritmo pesa mais do que deveria."}, '
    '{"grupo": "negativas", "trecho": "Para eles, nada funciona."}]}'
)
_PROSA_SEM_ANCORA = (
    '{"narrativa": "entre quem nao gostou, o ritmo incomodou; para quem ficou '
    'no meio, ficou irregular; ja entre quem amou, o ritmo foi elogiado como '
    'deliberado e envolvente ao longo de toda a projecao.", '
    '"consensos_usados": []}'
)


def test_ancoragem_presente_nao_flagga_nem_retenta():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return _PROSA_ANCORADA

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.peso_nao_ancorado is False
    assert len(calls) == 1


def test_ancoragem_ausente_retenta_e_flagga():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return _PROSA_SEM_ANCORA

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.peso_nao_ancorado is True
    assert len(systems) == 2                      # houve retentativa
    assert "ancorou cada grupo no rotulo_peso" in systems[1]


def test_ancoragem_corrigida_na_retentativa_zera_a_flag():
    respostas = [_PROSA_SEM_ANCORA, _PROSA_ANCORADA]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.peso_nao_ancorado is False


def test_rotulo_mais_fraco_conta_como_ancorado():
    """O prompt permite descer de força; a checagem tem que aceitar isso."""
    def fake(system, user, model):
        return ('{"narrativa": "a maioria das notas veio de quem gostou; uma '
                'minoria ficou no meio; uma fração mínima nao gostou do ritmo '
                'nem do roteiro deste filme longo.", "consensos_usados": []}')

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.peso_nao_ancorado is False


def test_sem_distribuicao_ancoragem_nunca_flagga():
    def fake(system, user, model):
        return _PROSA_SEM_ANCORA

    r = narrate_output(_output(com_distribuicao=False), client_call=fake, model="m")
    assert r.peso_nao_ancorado is False


# --- a rede de prevalência da v1.2.1 muda de sinal ---

def test_com_distribuicao_palavra_minoria_nao_e_mais_violacao():
    """"uma minoria" é EXIGIDA pela regra invertida — não pode mais flaggar
    prevalencia_suspeita, senão toda narrativa correta viria marcada."""
    def fake(system, user, model):
        return _PROSA_ANCORADA

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.prevalencia_suspeita is False


def test_sem_distribuicao_prevalencia_continua_sendo_violacao():
    def fake(system, user, model):
        return ('{"narrativa": "a recepcao e polarizada: um grupo grande de fas '
                'e uma minoria de criticos que nao gostaram do filme.", '
                '"consensos_usados": []}')

    r = narrate_output(_output(com_distribuicao=False), client_call=fake, model="m")
    assert r.prevalencia_suspeita is True


# =====================================================================
# v1.4.1 — invariante de vocabulário do peso: NOTAS, não REVIEWS
# =====================================================================
# Os rótulos de peso derivam do histograma de NOTAS (todos que avaliaram); os
# temas derivam das REVIEWS COM TEXTO (subconjunto). Dizer "a grande maioria
# das reviews" empresta ao peso um denominador que não é o dele.

def test_prompt_com_distribuicao_traz_a_invariante_de_vocabulario():
    p = build_narrator_prompt(True)
    assert "VOCABULÁRIO OBRIGATÓRIO — NOTAS, NUNCA REVIEWS" in p
    assert 'é OBRIGATÓRIO escrever "das notas"' in p
    assert 'é PROIBIDO escrever "das reviews", "dos espectadores" ou "do público"' in p
    # e a distinção das duas populações fica explícita
    assert "histograma de NOTAS do Letterboxd" in p
    assert "os temas vêm das REVIEWS COM TEXTO" in p


def test_invariante_de_vocabulario_so_existe_na_variante_com_distribuicao():
    # sem distribuição não há peso a expressar — a regra não faz sentido lá
    assert "NOTAS, NUNCA REVIEWS" not in build_narrator_prompt(False)


_PESOS_CURE = {"negativas": (3, "uma pequena minoria"),
               "medianas": (17, "uma minoria"),
               "positivas": (79, "a grande maioria")}


def test_vocabulario_ok_quando_o_rotulo_vem_com_notas():
    assert _vocabulario_peso_ok(
        "a grande maioria das notas (~79%) gostou; uma minoria das notas "
        "(~17%) ficou no meio; uma pequena minoria das notas (~3%) nao gostou.",
        _PESOS_CURE) is True


def test_vocabulario_flagga_rotulo_de_peso_com_reviews():
    assert _vocabulario_peso_ok(
        "a grande maioria das reviews (~79%) gostou do filme.",
        _PESOS_CURE) is False


@pytest.mark.parametrize("prosa", [
    "a grande maioria dos espectadores (~79%) gostou do filme.",
    "uma pequena minoria do público (~3%) nao gostou do filme.",
    "uma minoria dos espectadores ficou no meio-termo sobre o filme.",
])
def test_vocabulario_flagga_publico_e_espectadores(prosa):
    assert _vocabulario_peso_ok(prosa, _PESOS_CURE) is False


def test_frequencia_de_tema_em_relacao_a_reviews_continua_permitida():
    """A regra (d) EXIGE ancorar frequência de tema nas reviews analisadas —
    a checagem não pode flaggar isso. "a maioria" sem percentual é
    quantificador de tema, não rótulo de peso."""
    assert _vocabulario_peso_ok(
        "a grande maioria das notas (~79%) gostou; dentro desse grupo, a "
        "maioria das reviews analisadas destaca o ritmo, e muitas reviews "
        "citam a atmosfera.", _PESOS_CURE) is True


def test_vocabulario_dispara_retentativa_e_flagga_na_narrativa():
    systems = []

    def fake(system, user, model):
        systems.append(system)
        return ('{"narrativa": "a grande maioria das reviews (~79%) gostou e '
                'destaca o ritmo; uma minoria das notas (~17%) ficou no meio; '
                'uma pequena minoria das notas (~3%) reclamou do arrastado.", '
                '"consensos_usados": [], "quantificadores_usados": []}')

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.vocabulario_peso_suspeito is True
    assert len(systems) == 2                      # houve retentativa
    assert 'troque para "das notas"' in systems[1]  # reforço específico anexado


def test_vocabulario_corrigido_na_retentativa_zera_a_flag():
    respostas = [
        ('{"narrativa": "a grande maioria das reviews (~79%) gostou do ritmo.", '
         '"consensos_usados": []}'),
        _PROSA_ANCORADA,
    ]

    def fake(system, user, model):
        return respostas.pop(0)

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.vocabulario_peso_suspeito is False


def test_vocabulario_correto_nao_retenta_nem_flagga():
    calls = []

    def fake(system, user, model):
        calls.append(1)
        return _PROSA_ANCORADA

    r = narrate_output(_output(), client_call=fake, model="m")
    assert r.vocabulario_peso_suspeito is False
    assert len(calls) == 1


def test_sem_distribuicao_vocabulario_nunca_flagga():
    """Sem histograma não há rótulo de peso — nada a checar (vacuamente OK)."""
    def fake(system, user, model):
        return ('{"narrativa": "entre quem nao gostou, o ritmo incomodou; ja '
                'entre quem gostou, a maioria das reviews analisadas elogia a '
                'direcao deste filme longo e denso."}')

    r = narrate_output(_output(com_distribuicao=False), client_call=fake, model="m")
    assert r.vocabulario_peso_suspeito is False


def test_render_mostra_flag_de_vocabulario_de_peso():
    out = _output()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {"vocabulario_peso_suspeito": True}
    assert "em vez de \"das notas\"" in render_terminal(out, tom="narrativo")


# --- render: bloco compacto de quantificadores_usados (v1.4.1) ---

def test_render_mostra_bloco_de_quantificadores_com_a_conferencia():
    out = _output()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {}
    out["quantificadores_usados"] = [
        {"quantificador": "cerca de metade", "tema": "ritmo"}]
    r = render_terminal(out, tom="narrativo")
    assert "Quantificadores do movimento 3:" in r
    assert "cerca de metade" in r
    # a conferência contra o número real é o que torna o bloco útil
    assert "fração real 60%" in r
    assert "rótulo: cerca de metade" in r


def test_render_sinaliza_tema_inexistente_no_bloco_de_quantificadores():
    out = _output()
    out["narrativa"] = "prosa qualquer"
    out["narrativa_flags"] = {}
    out["quantificadores_usados"] = [
        {"quantificador": "quase todos", "tema": "tema fantasma"}]
    assert "tema inexistente no relatório" in render_terminal(out, tom="narrativo")
