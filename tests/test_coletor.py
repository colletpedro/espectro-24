"""[v1.9.0] Coletor de SUPERSET + ordenação parametrizada (SPEC §3[B], §2.3).

O coletor não sabe nada sobre fronteira, cota de bucket ou filtro de análise.
Ele recebe um ALVO por nível (da alocação, §3[C1]), pagina até a condição de
parada, e **persiste tudo** — inclusive o que a heurística de parada
reprovou.
"""
import pytest

from conftest import FakeFetcher, fx

from espectro24 import collector
from espectro24.bruto import carregar
from espectro24.collector import coletar_superset, raspar_nivel
from espectro24.config import ORDENACOES
from espectro24.urls import level_page_cache_key, level_page_url


def _pagina(n_reviews: int, chars: int = 200, spoiler: bool = False,
            truncada: bool = False, base_id: int = 0,
            autor: str = "ana", data: str = "2026-01-01") -> str:
    """Página sintética de reviews — marcação espelhando a real (Fase 1)."""
    from espectro24.parser import SPOILER_PLACEHOLDER
    corpo = SPOILER_PLACEHOLDER if spoiler else ("x" * chars)
    colapso = '<div class="collapsed-text">…</div>' if truncada else ""
    itens = []
    for i in range(n_reviews):
        vid = base_id + i
        itens.append(f"""
<article class="production-viewing -viewing">
  <a class="avatar" href="/{autor}{vid}/"><img alt="{autor}{vid}"/></a>
  <span class="attribution-detail">
    <a class="context" href="/{autor}{vid}/film/filme/"><span class="owner">
      <strong class="displayname">{autor}{vid}</strong></span></a>
  </span>
  <span class="date"><time class="timestamp" datetime="{data}">{data}</time></span>
  <div class="body-text js-review-body" data-full-text-url="/s/full-text/viewing:{vid}/" lang="en">
    <p>{corpo}</p>{colapso}
  </div>
  <p data-likeable-identifier='{{"uid":"viewing:{vid}","type":"viewing"}}'></p>
</article>""")
    return "<html><body>" + "".join(itens) + "</body></html>"


def _fetcher_com_paginas(slug, nivel, paginas: list[str], ordenacao="by/added"):
    return FakeFetcher({
        level_page_cache_key(slug, nivel, i + 1, ordenacao): html
        for i, html in enumerate(paginas)
    })


# --- ordenação como parâmetro (§2.3) ---

def test_ordenacoes_conhecidas_sao_as_tres_do_menu_real():
    assert ORDENACOES == {
        "mais_recentes": "by/added",
        "mais_antigas": "by/added-earliest",
        "atividade": "by/activity",
    }


def test_default_e_a_cronologica_nao_a_de_engajamento():
    from espectro24.config import ORDENACAO, ORDENACAO_DEFAULT
    assert ORDENACAO_DEFAULT == "mais_recentes"
    assert ORDENACAO == "by/added"
    assert ORDENACAO != "by/activity"


def test_url_carrega_a_ordenacao_pedida():
    assert level_page_url("cure", 4.0, 2, "by/added") == \
        "https://letterboxd.com/film/cure/reviews/rated/4/by/added/page/2/"
    assert level_page_url("cure", 4.0, 2, "by/activity") == \
        "https://letterboxd.com/film/cure/reviews/rated/4/by/activity/page/2/"


def test_url_usa_formato_decimal_da_nota():
    assert "/rated/3.5/" in level_page_url("cure", 3.5, 1, "by/added")
    assert "/rated/3/" in level_page_url("cure", 3.0, 1, "by/added")


def test_chave_de_cache_INCLUI_a_ordenacao():
    """Ordenação diferente é AMOSTRA diferente — servir a antiga do cache
    seria um erro silencioso (§3[B], 'Cache')."""
    a = level_page_cache_key("cure", 4.0, 1, "by/added")
    b = level_page_cache_key("cure", 4.0, 1, "by/activity")
    assert a != b
    assert "by_added" in a and "by_activity" in b


def test_chave_de_cache_distingue_added_de_added_earliest():
    """[v1.9.6, §2.3] A passada depende disto: as duas ordenações CRONOLÓGICAS
    são prefixo uma da outra como texto, e confundi-las serviria a ponta
    errada do bruto — do cache, sem tocar a rede, sem erro visível."""
    a = level_page_cache_key("cure", 4.0, 1, "by/added")
    b = level_page_cache_key("cure", 4.0, 1, "by/added-earliest")
    assert a != b
    assert a not in b and b not in a
    ua = level_page_url("cure", 4.0, 1, "by/added")
    ub = level_page_url("cure", 4.0, 1, "by/added-earliest")
    assert ua != ub and ua.endswith("/by/added/page/1/")


def test_coletor_usa_a_ordenacao_recebida_na_url_de_rede():
    ff = FakeFetcher({})
    raspar_nivel(ff, "cure", 4.0, alvo=0, ordenacao="by/activity")
    assert all("by/activity" in url for url, _ in ff.calls)


# --- condição de parada DETERMINÍSTICA (v1.9.2, §3[B]) ---
# Só dois motivos possíveis agora: "orcamento_esgotado" (o orçamento foi
# gasto integralmente, o site provavelmente tem mais) ou "material_esgotado"
# (página vazia encontrada — o nível está provadamente completo). A parada
# por ALVO (heurística) foi REMOVIDA — ver changelog v1.9.2.

def test_orcamento_e_sempre_gasto_integralmente_quando_ha_material():
    """teto_paginas=2, sem reserva profunda (teto pequeno demais para reservar
    nada — dividir_raso_profundo(2)==(2,0)): as 2 páginas do orçamento são
    buscadas, mesmo que o material heuristicamente já bastasse na 1ª."""
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(12, base_id=0), _pagina(12, base_id=100)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=1, teto_paginas=2)
    assert r.paginas_gastas == 2
    assert r.motivo_parada == "orcamento_esgotado"
    assert r.n_bruta == 24


def test_alvo_zero_nao_afeta_mais_a_paginacao():
    """`alvo` não decide mais quando parar — só o orçamento do completamento.
    Com alvo=0, o nível ainda pagina o orçamento inteiro."""
    ff = _fetcher_com_paginas("cure", 0.5, [_pagina(12, base_id=0), _pagina(12, base_id=100)])
    r = raspar_nivel(ff, "cure", 0.5, alvo=0, teto_paginas=2)
    assert r.paginas_gastas == 2
    assert r.n_bruta == 24          # e o material FOI persistido, não descartado


def test_nivel_sem_material_nenhum_nao_gasta_pagina():
    ff = FakeFetcher({})            # toda página vem vazia
    r = raspar_nivel(ff, "cure", 0.5, alvo=0, teto_paginas=4)
    assert r.paginas_gastas == 0 and r.n_bruta == 0
    assert r.motivo_parada == "material_esgotado"
    assert len(ff.calls) == 1       # 1 requisição para descobrir que está vazio


def test_material_esgotado_para_antes_do_orcamento_e_registra():
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(3)])   # página 2 vem vazia
    r = raspar_nivel(ff, "cure", 4.0, alvo=40, teto_paginas=4)
    assert r.paginas_gastas == 1
    assert r.esgotado is True
    assert r.motivo_parada == "material_esgotado"
    assert r.parou_por_teto is False       # esgotou, não gastou o orçamento


def test_orcamento_pequeno_e_parametro():
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(2, base_id=b * 100)
                                            for b in range(9)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=40, teto_paginas=2)
    assert r.paginas_gastas == 2
    assert r.motivo_parada == "orcamento_esgotado"


def test_orcamento_zero_nao_faz_nenhuma_requisicao_de_paginacao():
    ff = FakeFetcher({})
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=0)
    assert r.paginas_gastas == 0 and r.n_bruta == 0
    assert len(ff.calls) == 0


# --- persiste TUDO: os filtros só decidem parar ---

def test_spoiler_e_review_curta_sao_PERSISTIDOS():
    """Os filtros existem aqui com uma função só: decidir quando parar.

    Até a v1.8.2 spoiler era 'descartado na coleta'; agora é decisão de
    seleção (§2, camada 'análise').
    """
    ff = _fetcher_com_paginas("cure", 4.0, [
        _pagina(2, spoiler=True, base_id=0) + _pagina(2, chars=10, base_id=10)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=0)
    assert r.n_bruta == 4                    # nada descartado
    assert r.n_estimada_valida == 0          # mas nada conta para a parada
    assert sum(1 for x in r.reviews if x.spoiler_flag) == 2


def test_contagem_bruta_e_estimada_valida_sao_registradas_separadas():
    ff = _fetcher_com_paginas("cure", 4.0, [
        _pagina(6, chars=200, base_id=0) + _pagina(6, chars=10, base_id=50)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=0)
    assert r.n_bruta == 12
    assert r.n_estimada_valida == 6


def test_dedupe_entre_paginas_do_mesmo_nivel():
    p = _pagina(5, base_id=0)
    ff = _fetcher_com_paginas("cure", 4.0, [p, p, p])   # mesmas ids repetidas
    r = raspar_nivel(ff, "cure", 4.0, alvo=40)
    assert r.n_bruta == 5


def test_nivel_da_review_vem_da_URL_nao_do_parsing():
    """A URL já filtra por nível — é a fonte autoritativa."""
    ff = _fetcher_com_paginas("cure", 2.5, [_pagina(3)])
    r = raspar_nivel(ff, "cure", 2.5, alvo=0)
    assert {x.nivel for x in r.reviews} == {2.5}


def test_pagina_origem_e_registrada():
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(12, base_id=0),
                                            _pagina(12, base_id=100)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=15)
    assert {x.pagina_origem for x in r.reviews} == {1, 2}


def test_metadados_da_review_chegam_ao_registro_bruto():
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(1, autor="zeca",
                                                    data="2019-03-04")])
    r = raspar_nivel(ff, "cure", 4.0, alvo=0)
    (rev,) = r.reviews
    assert rev.data == "2019-03-04"
    assert rev.url.endswith("/zeca0/film/filme/")
    assert rev.autor_hash and "zeca" not in rev.autor_hash
    assert rev.texto_completo is True and rev.truncada is False


# --- completamento de truncadas: orçado pelo mesmo alvo da paginação ---

def test_truncada_nao_completada_fica_marcada_e_persistida():
    ff = _fetcher_com_paginas("cure", 4.0, [_pagina(3, truncada=True)])
    r = raspar_nivel(ff, "cure", 4.0, alvo=0)     # alvo 0 → orçamento 0
    assert r.n_bruta == 3
    assert all(x.truncada for x in r.reviews)
    assert all(x.texto_completo is False for x in r.reviews)


def test_truncada_completada_entra_com_texto_completo():
    from espectro24.urls import full_text_cache_key
    paginas = {level_page_cache_key("cure", 4.0, 1, "by/added"):
               _pagina(2, truncada=True)}
    for vid in (0, 1):
        paginas[full_text_cache_key("cure", f"viewing:{vid}")] = \
            "<p>" + "y" * 900 + "</p>"
    r = raspar_nivel(FakeFetcher(paginas), "cure", 4.0, alvo=2)
    assert all(x.texto_completo for x in r.reviews)
    assert all(x.n_chars == 900 for x in r.reviews)


def test_orcamento_de_completamento_segue_o_alvo_com_folga():
    """Não se gasta requisição completando material muito além do alvo — o
    resto fica no bruto marcado, para uma execução futura resolver se uma
    fronteira nova o tornar relevante (§3[B])."""
    from espectro24.urls import full_text_cache_key
    paginas = {level_page_cache_key("cure", 4.0, 1, "by/added"):
               _pagina(12, truncada=True)}
    for vid in range(12):
        paginas[full_text_cache_key("cure", f"viewing:{vid}")] = "<p>" + "y" * 900 + "</p>"
    ff = FakeFetcher(paginas)
    r = raspar_nivel(ff, "cure", 4.0, alvo=4)          # 4 × 1,25 = 5
    completas = [x for x in r.reviews if x.texto_completo]
    assert len(completas) == 5
    assert r.n_bruta == 12                              # o resto continua no bruto


# --- coletar_superset: varre a escala e persiste ---

def test_superset_varre_os_10_niveis_e_persiste(tmp_path):
    from espectro24.buckets import NIVEIS
    ff = FakeFetcher({level_page_cache_key("cure", n, 1, "by/added"):
                      _pagina(3, base_id=int(n * 100)) for n in NIVEIS})
    res = coletar_superset(ff, "cure", alvo_por_nivel={n: 0 for n in NIVEIS},
                           histograma={n: 10 for n in NIVEIS}, raiz=tmp_path)
    meta, revs = carregar("cure", raiz=tmp_path)
    assert len(revs) == 30
    assert {r.nivel for r in revs} == set(NIVEIS)
    assert res.n_reviews == 30


def test_meta_registra_ordenacao_versao_e_telemetria(tmp_path):
    from espectro24.buckets import NIVEIS
    ff = FakeFetcher({level_page_cache_key("cure", n, 1, "by/added"):
                      _pagina(2, base_id=int(n * 100)) for n in NIVEIS})
    coletar_superset(ff, "cure", alvo_por_nivel={n: 0 for n in NIVEIS},
                     histograma={n: 7 for n in NIVEIS}, raiz=tmp_path)
    meta, _ = carregar("cure", raiz=tmp_path)
    assert meta["ordenacao_usada"] == "by/added"
    assert meta["versao_coletor"]
    assert meta["slug"] == "cure"
    assert meta["histograma_bruto"]["0.5"] == 7
    assert meta["paginas_gastas_por_nivel"]["0.5"] == 1
    assert meta["contagem_bruta_por_nivel"]["0.5"] == 2
    assert "contagem_estimada_valida_por_nivel" in meta
    assert meta["paradas_por_limite"] == []


def test_meta_registra_niveis_que_pararam_por_teto(tmp_path):
    from espectro24.buckets import NIVEIS
    resp = {}
    for n in NIVEIS:
        for p in range(1, 6):
            resp[level_page_cache_key("cure", n, p, "by/added")] = \
                _pagina(1, base_id=int(n * 1000) + p * 10)
    coletar_superset(FakeFetcher(resp), "cure",
                     alvo_por_nivel={n: 40 for n in NIVEIS},
                     histograma={n: 10 for n in NIVEIS}, raiz=tmp_path)
    meta, _ = carregar("cure", raiz=tmp_path)
    assert sorted(meta["paradas_por_limite"]) == sorted(str(n) for n in NIVEIS)


def test_superset_e_incremental_entre_execucoes(tmp_path):
    from espectro24.buckets import NIVEIS
    alvo = {n: 0 for n in NIVEIS}
    ff1 = FakeFetcher({level_page_cache_key("cure", 4.0, 1, "by/added"):
                       _pagina(3, base_id=0)})
    coletar_superset(ff1, "cure", alvo, histograma=None, raiz=tmp_path)
    ff2 = FakeFetcher({level_page_cache_key("cure", 4.0, 1, "by/activity"):
                       _pagina(3, base_id=50)})
    coletar_superset(ff2, "cure", alvo, histograma=None, raiz=tmp_path,
                     ordenacao="by/activity")
    meta, revs = carregar("cure", raiz=tmp_path)
    assert len(revs) == 6                       # ACUMULOU
    assert meta["ordenacao_usada"] == "by/activity"   # meta = a última coleta


def test_superset_e_idempotente(tmp_path):
    from espectro24.buckets import NIVEIS
    alvo = {n: 0 for n in NIVEIS}
    resp = {level_page_cache_key("cure", 4.0, 1, "by/added"): _pagina(4)}
    coletar_superset(FakeFetcher(resp), "cure", alvo, None, raiz=tmp_path)
    coletar_superset(FakeFetcher(resp), "cure", alvo, None, raiz=tmp_path)
    _, revs = carregar("cure", raiz=tmp_path)
    assert len(revs) == 4


# --- fixture REAL: o coletor funciona sobre a página que veio do Letterboxd ---

def test_coletor_sobre_a_pagina_real_do_oppenheimer():
    key = level_page_cache_key("oppenheimer-2023", 5.0, 1, "by/added")
    r = raspar_nivel(FakeFetcher({key: fx("oppenheimer-2023_rated5_page1.html")}),
                     "oppenheimer-2023", 5.0, alvo=0)
    assert r.n_bruta == 12
    assert all(x.nivel == 5.0 for x in r.reviews)
    assert all(x.autor_hash for x in r.reviews)
    assert all(x.data for x in r.reviews)
