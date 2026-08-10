"""[v1.9.6, §3[B']] `dias_por_100_paginas` — o discriminador, e suas bordas.

A métrica decide QUAL estratégia cada filme precisa (§2.3), então errar uma
borda em silêncio é decidir errado em silêncio.
"""
from __future__ import annotations

from espectro24.bruto import (
    ReviewBruta,
    dias_por_100_paginas,
    dias_por_100_paginas_por_nivel,
    reviews_da_ordenacao,
)


def rb(id_, pagina, data, nivel=4.0, ordenacao=None, n_chars=200):
    return ReviewBruta(
        id=id_, nivel=nivel, texto="x" * n_chars, n_chars=n_chars,
        spoiler_flag=False, pagina_origem=pagina, url="", autor_hash="a",
        truncada=False, texto_completo=True, data=data,
        ordenacao_origem=ordenacao,
    )


def test_taxa_basica():
    """100 páginas cobrindo 10 dias → 10 dias/100 páginas."""
    reviews = [rb("a", 1, "2026-08-11"), rb("b", 101, "2026-08-01")]
    m = dias_por_100_paginas(reviews)
    assert m["pagina_min"] == 1 and m["pagina_max"] == 101
    assert m["dias"] == 10
    assert m["dias_por_100_paginas"] == 10.0
    assert m["n_paginas"] == 2
    # 100 páginas por 10 dias → 36,5 páginas/dia → 3650 páginas para 1 ano
    assert m["paginas_para_1_ano"] == 3650


def test_mediana_por_pagina_resiste_a_outlier_de_data_assistida():
    """A data é proxy CONTAMINADO (§3[B']): uma review de 2011 na página 1 não
    pode dominar a taxa. Por isso a métrica usa a MEDIANA da página."""
    p1 = [rb(f"p1-{i}", 1, "2026-08-11") for i in range(4)] + [rb("velha", 1, "2011-01-01")]
    p101 = [rb(f"p101-{i}", 101, "2026-08-01") for i in range(5)]
    m = dias_por_100_paginas(p1 + p101)
    assert m["dias"] == 10


def test_uma_pagina_so_devolve_none():
    assert dias_por_100_paginas([rb("a", 1, "2026-08-11")]) is None
    assert dias_por_100_paginas([rb("a", 1, "2026-08-11"),
                                 rb("b", 1, "2026-08-01")]) is None


def test_lista_vazia_e_sem_data_devolvem_none():
    assert dias_por_100_paginas([]) is None
    assert dias_por_100_paginas([rb("a", 1, None), rb("b", 9, None)]) is None


def test_todas_as_datas_iguais():
    """Taxa genuinamente zero. `paginas_para_1_ano` é None, não 0: não há
    resposta finita, e 0 mentiria."""
    m = dias_por_100_paginas([rb("a", 1, "2026-08-11"), rb("b", 51, "2026-08-11")])
    assert m["dias"] == 0
    assert m["dias_por_100_paginas"] == 0.0
    assert m["paginas_para_1_ano"] is None


def test_paginas_adjacentes():
    m = dias_por_100_paginas([rb("a", 1, "2026-08-03"), rb("b", 2, "2026-08-02")])
    assert m["dias"] == 1
    assert m["dias_por_100_paginas"] == 100.0
    assert m["paginas_para_1_ano"] == 365


def test_data_com_hora_e_truncada_para_o_dia():
    m = dias_por_100_paginas([rb("a", 1, "2026-08-11T22:30:00Z"),
                              rb("b", 101, "2026-08-01")])
    assert m["dias"] == 10


def test_taxa_negativa_e_reportada_como_medida():
    """Fundo mais NOVO que o topo: acontece com data assistida contaminada.
    Reportar o número medido é mais honesto que zerar."""
    m = dias_por_100_paginas([rb("a", 1, "2026-08-01"), rb("b", 101, "2026-08-11")])
    assert m["dias"] == -10
    assert m["dias_por_100_paginas"] == -10.0
    assert m["paginas_para_1_ano"] is None


def test_por_nivel_calcula_cada_nivel_isolado():
    reviews = [
        rb("a", 1, "2026-08-11", nivel=4.0), rb("b", 101, "2026-08-01", nivel=4.0),
        rb("c", 1, "2026-08-11", nivel=1.0), rb("d", 51, "2026-07-12", nivel=1.0),
        rb("e", 1, "2026-08-11", nivel=2.0),   # 1 página só → None
    ]
    por_nivel = dias_por_100_paginas_por_nivel(reviews)
    assert por_nivel["4.0"]["dias_por_100_paginas"] == 10.0
    assert por_nivel["1.0"]["dias"] == 30
    assert "2.0" not in por_nivel      # nível sem taxa não inventa entrada


# --- resolução de `ordenacao_origem` (§3[B'], compatibilidade) ---------------

def test_reviews_da_ordenacao_resolve_none_pela_base():
    """`None` = coletada antes do campo existir; a leitura correta é a
    `ordenacao_usada` da coleta base — resolvida no CONSUMO, sem reescrever
    dado histórico com uma inferência."""
    antigas = [rb("a", 1, "2026-08-11")]
    novas = [rb("b", 1, "2013-01-01", ordenacao="by/added-earliest")]
    base = reviews_da_ordenacao(antigas + novas, "by/added", "by/added")
    assert [r.id for r in base] == ["a"]
    passada = reviews_da_ordenacao(antigas + novas, "by/added-earliest", "by/added")
    assert [r.id for r in passada] == ["b"]


def test_metrica_ignora_a_outra_ponta():
    """Misturar ordenações somaria posições que não significam a mesma coisa:
    página 3 sob `by/added` é a 3ª mais RECENTE; sob `by/added-earliest`, a 3ª
    mais ANTIGA."""
    base = [rb("a", 1, "2026-08-11"), rb("b", 101, "2026-08-01")]
    antigas = [rb("c", 1, "2012-05-01", ordenacao="by/added-earliest"),
               rb("d", 3, "2012-06-01", ordenacao="by/added-earliest")]
    todas = base + antigas
    m = dias_por_100_paginas(reviews_da_ordenacao(todas, "by/added", "by/added"))
    assert m["dias_por_100_paginas"] == 10.0


# --- gravação em meta.json na COLETA (§3[B'], Entrega 2) --------------------

def _rb_pag(rid, pagina, data, nivel=4.0, ordenacao=None):
    return rb(rid, pagina, data, nivel=nivel, ordenacao=ordenacao)


def test_pipeline_grava_metrica_no_meta(tmp_path):
    import json

    from espectro24.bruto import caminho_meta, persistir
    from espectro24.pipeline import atualizar_dias_por_100_paginas

    revs = [_rb_pag("a", 1, "2026-08-11"), _rb_pag("b", 101, "2026-08-01"),
            _rb_pag("c", 1, "2026-08-11", nivel=1.0),
            _rb_pag("d", 51, "2026-07-12", nivel=1.0)]
    persistir("cure", {"slug": "cure", "ordenacao_usada": "by/added"}, revs,
              raiz=tmp_path)

    atualizar_dias_por_100_paginas("cure", raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    assert meta["dias_por_100_paginas"]["dias_por_100_paginas"] == 10.0
    assert meta["dias_por_100_paginas_por_nivel"]["1.0"]["dias"] == 30
    assert meta["slug"] == "cure"      # mescla, não substitui


def test_pipeline_ignora_a_ponta_da_passada_ao_calcular(tmp_path):
    """A métrica é sobre UMA ordenação: somar as duas misturaria posições que
    não significam a mesma coisa."""
    import json

    from espectro24.bruto import caminho_meta, persistir
    from espectro24.pipeline import atualizar_dias_por_100_paginas

    revs = [_rb_pag("a", 1, "2026-08-11"), _rb_pag("b", 101, "2026-08-01"),
            _rb_pag("c", 1, "2012-05-01", ordenacao="by/added-earliest"),
            _rb_pag("d", 3, "2012-06-01", ordenacao="by/added-earliest")]
    persistir("cure", {"slug": "cure", "ordenacao_usada": "by/added"}, revs,
              raiz=tmp_path)
    atualizar_dias_por_100_paginas("cure", raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    assert meta["dias_por_100_paginas"]["dias_por_100_paginas"] == 10.0
    assert meta["dias_por_100_paginas"]["pagina_max"] == 101
