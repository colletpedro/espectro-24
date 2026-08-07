"""Testes de parsing contra fixtures reais e sintéticas (zero rede)."""
from conftest import fx

from espectro24 import parser


def test_rating_glyphs_incluindo_meia_estrela():
    revs = parser.parse_reviews(fx("synthetic_cases.html"))
    ratings = [r.rating for r in revs]
    assert ratings == [3.5, 0.5, 5.0, None, 4.0, 2.0]


def test_meia_estrela_pura_e_meio_ponto():
    # "½" sozinho = 0.5 ; "★★★½" = 3.5
    assert parser.parse_reviews(fx("synthetic_cases.html"))[1].rating == 0.5
    assert parser.parse_reviews(fx("synthetic_cases.html"))[0].rating == 3.5


def test_deteccao_de_spoiler():
    revs = parser.parse_reviews(fx("synthetic_cases.html"))
    assert revs[2].spoiler is True           # placeholder no corpo
    assert [r.spoiler for r in revs].count(True) == 1


def test_canario_spoiler_placeholder_real_e_flaggeado():
    # CANÁRIO (v1.1.1 / Tarefa 4): protege contra REGRESSÃO DE CÓDIGO no
    # matching do detector — ex. alguém "simplificar" is_spoiler_text() de
    # volta para uma substring frouxa, ou trocar a string âncora sem
    # atualizar aqui. Este fixture tem o placeholder real capturado de uma
    # página ao vivo do Letterboxd na Fase 0/1 (fixtures/oppenheimer-2023_
    # rated5_page2.html), em inglês.
    #
    # O QUE ESTE TESTE **NÃO** COBRE: localização da interface do Letterboxd.
    # Se o Letterboxd um dia servir esse placeholder em pt-BR (ou qualquer
    # outro idioma) para alguma sessão, o detector para de casar em silêncio
    # e este teste continua verde — porque o fixture nunca localiza junto
    # com o código. Essa lacuna só está coberta como ressalva textual na
    # SPEC.md (§2.1), não por um teste automatizado.
    revs = parser.parse_reviews(fx("oppenheimer-2023_rated5_page2.html"))
    spoilers = [r for r in revs if r.spoiler]
    assert len(spoilers) >= 1, (
        "regressão: nenhuma review foi flaggeada como spoiler na página "
        "que sabidamente contém o placeholder real do Letterboxd"
    )


def test_spoiler_nao_falso_positivo_em_prosa_legitima():
    # Anti-falso-positivo (v1.1.1): a versão antiga do detector usava a
    # substring solta "may contain spoilers", que capturaria esta review
    # legítima só por citar a palavra em prosa — sem nunca mencionar o
    # placeholder real do Letterboxd.
    texto = ("This may contain spoilers for the novel it's based on, but "
             "the film itself stands on its own and the pacing is great.")
    assert parser.is_spoiler_text(texto) is False


def test_review_sem_nota_vira_none():
    assert parser.parse_reviews(fx("synthetic_cases.html"))[3].rating is None


def test_detector_truncamento_positivos_e_negativos():
    # Ground truth da Etapa A (A3): truncadas = índices 2,4,6,8,11.
    revs = parser.parse_reviews(fx("oppenheimer-2023_reviews_base.html"))
    truncadas = {i for i, r in enumerate(revs) if r.truncated}
    assert truncadas == {2, 4, 6, 8, 11}
    # negativos explícitos
    for i in (0, 1, 3, 5, 7, 9, 10):
        assert revs[i].truncated is False


def test_data_full_text_url_nao_e_detector():
    # Todos têm data-full-text-url, mas só 5 são truncadas — o detector NÃO
    # pode ser data-full-text-url (senão daria 12 positivos).
    revs = parser.parse_reviews(fx("oppenheimer-2023_reviews_base.html"))
    com_ftu = sum(1 for r in revs if r.full_text_url)
    truncadas = sum(1 for r in revs if r.truncated)
    assert com_ftu == 12 and truncadas == 5


def test_viewing_id_universal_e_dedup():
    p1 = parser.parse_reviews(fx("oppenheimer-2023_rated5_page1.html"))
    p2 = parser.parse_reviews(fx("oppenheimer-2023_rated5_page2.html"))
    ids1 = {r.viewing_id for r in p1}
    ids2 = {r.viewing_id for r in p2}
    assert all(r.viewing_id for r in p1 + p2)     # todos presentes
    assert len(ids1) == 12 and len(ids2) == 12
    assert ids1.isdisjoint(ids2)                  # sem repetição entre páginas


def test_pagina_alem_da_ultima_vazia():
    revs = parser.parse_reviews(fx("oppenheimer-2023_rated5_page9999.html"))
    assert revs == []


def test_busca_extrai_slug_titulo_ano():
    res = parser.parse_search_results(fx("search_ajax_city-of-god.html"))
    assert len(res) == 20
    first = res[0]
    assert first.slug == "city-of-god"
    assert first.year == 2002
    assert "City of God" in first.name
    # ambiguidade presente
    anos = {r.year for r in res if r.slug.startswith("city-of-god")}
    assert {2002, 2011}.issubset(anos)


def test_full_text_parse():
    ft = parser.parse_full_text(fx("fulltext_pos_2_viewing1401220676.html"))
    assert len(ft) == 3237
    assert "post Oppenheimer world" in ft


# --- v1.9.0: metadados persistidos no superset bruto (§3[B']) ---

def test_extrai_autor_permalink_e_data_da_fixture_real():
    revs = parser.parse_reviews(fx("oppenheimer-2023_rated5_page1.html"))
    r = revs[0]
    assert r.autor == "justinwuah"
    assert r.permalink == "https://letterboxd.com/justinwuah/film/oppenheimer-2023/"
    assert r.data == "2023-07-12"


def test_todas_as_reviews_da_pagina_real_tem_autor_e_data():
    revs = parser.parse_reviews(fx("oppenheimer-2023_rated5_page1.html"))
    assert len(revs) == 12
    assert all(r.autor for r in revs)
    assert all(r.data for r in revs)
    assert all(r.permalink and r.permalink.startswith("https://letterboxd.com/")
               for r in revs)


def test_metadados_ausentes_viram_none_sem_levantar():
    # fixture sintética não tem avatar/atribuição/timestamp
    revs = parser.parse_reviews(fx("synthetic_cases.html"))
    assert all(r.data is None for r in revs)
    assert revs[0].permalink is None or revs[0].permalink.startswith("https://")
