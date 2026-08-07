"""[v1.9.2, Entrega 4] `pagina_origem` como instrumento temporal PRIMÁRIO
(SPEC §3[B']).

`janela_temporal` (por `data`) mede a data ASSISTIDA — contaminada por quem
registra filmes com atraso (causa do resultado misto do gate de profundidade
na v1.9.1). `pagina_origem`, sob ordenação cronológica, é o rank de ADIÇÃO,
sem essa contaminação.
"""
import json

from espectro24.bruto import ReviewBruta, distribuicao_pagina_origem, percentil


def _r(rid, pagina_origem, nivel=4.0):
    return ReviewBruta(id=str(rid), nivel=nivel, texto="x" * 200, n_chars=200,
                       spoiler_flag=False, pagina_origem=pagina_origem, url="u",
                       autor_hash="h", truncada=False, texto_completo=True,
                       data="2026-01-01")


# --- função pura, bucket-agnóstica ---

def test_lista_vazia_e_none():
    assert distribuicao_pagina_origem([]) is None


def test_uma_review_todos_os_campos_sao_a_mesma_pagina():
    d = distribuicao_pagina_origem([_r(1, pagina_origem=7)])
    assert d["n"] == 1
    assert d["min"] == d["max"] == d["p5"] == d["p50"] == d["p95"] == 7


def test_todas_na_mesma_pagina():
    d = distribuicao_pagina_origem([_r(i, pagina_origem=3) for i in range(10)])
    assert d["min"] == d["max"] == d["p5"] == d["p50"] == d["p95"] == 3
    assert d["n"] == 10


def test_min_max_sao_os_extremos_reais():
    d = distribuicao_pagina_origem([_r(1, 5), _r(2, 1), _r(3, 20)])
    assert d["min"] == 1 and d["max"] == 20


def test_mediana_com_numero_impar():
    d = distribuicao_pagina_origem([_r(1, 1), _r(2, 10), _r(3, 20)])
    assert d["p50"] == 10


def test_percentis_sao_monotonicos():
    d = distribuicao_pagina_origem([_r(i, pagina_origem=i) for i in range(1, 29)])
    assert d["min"] <= d["p5"] <= d["p50"] <= d["p95"] <= d["max"]


# --- percentil genérico (reaproveitado de janela_temporal) ---

def test_percentil_generico_funciona_sobre_inteiros():
    assert percentil([1, 2, 3, 4, 5], 0.5) == 3
    assert percentil([7], 0.9) == 7


# --- fracao_profunda: None sem orçamento, calculada quando fornecido ---

def test_sem_orcamento_fracao_profunda_e_none():
    d = distribuicao_pagina_origem([_r(1, 5), _r(2, 30)])
    assert d["fracao_profunda"] is None


def test_fracao_profunda_usa_dividir_raso_profundo_por_nivel():
    # orcamento=16 -> dividir_raso_profundo(16) == (12, 4): raso = 1..12
    revs = [_r(f"r{i}", pagina_origem=p, nivel=4.0)
            for i, p in enumerate([1, 5, 12, 14, 20])]   # 3 rasas, 2 profundas
    d = distribuicao_pagina_origem(revs, orcamento_por_nivel={4.0: 16})
    assert d["fracao_profunda"] == 2 / 5


def test_fracao_profunda_multiplos_niveis_cada_um_com_seu_raso():
    # nivel 4.0: orcamento 16 -> raso=12; nivel 0.5: orcamento 4 -> raso=3
    revs = [_r("a", pagina_origem=10, nivel=4.0),    # rasa (<=12)
            _r("b", pagina_origem=14, nivel=4.0),    # profunda (>12)
            _r("c", pagina_origem=2, nivel=0.5),     # rasa (<=3)
            _r("d", pagina_origem=5, nivel=0.5)]     # profunda (>3)
    d = distribuicao_pagina_origem(revs, orcamento_por_nivel={4.0: 16, 0.5: 4})
    assert d["fracao_profunda"] == 2 / 4


def test_nivel_sem_orcamento_no_dict_e_ignorado_na_fracao():
    """Nível ausente do dict de orçamento (não deveria acontecer em produção,
    mas não pode quebrar) — não conta nem no numerador nem no denominador
    ERRADO; a review simplesmente não participa do cálculo."""
    revs = [_r("a", pagina_origem=100, nivel=4.0)]
    d = distribuicao_pagina_origem(revs, orcamento_por_nivel={0.5: 4})
    assert d["fracao_profunda"] == 0    # nenhuma review classificável -> 0/1


# --- integração com pipeline (a orquestração bucket-aware) ---

def test_pipeline_grava_distribuicao_pagina_origem_por_bucket(tmp_path):
    from espectro24.bruto import persistir
    from espectro24.pipeline import atualizar_janela_temporal
    from espectro24.selecao import selecionar

    revs = ([_r(f"n{i}", pagina_origem=i + 1, nivel=0.5) for i in range(3)]
            + [_r(f"p{i}", pagina_origem=i + 1, nivel=4.0) for i in range(3)])
    meta_base = {"slug": "cure", "coletado_em": "x", "versao_coletor": "1.9.2",
                "ordenacao_usada": "by/added", "histograma_bruto": {},
                "paginas_gastas_por_nivel": {}, "paradas_por_limite": [],
                "contagem_bruta_por_nivel": {},
                "contagem_estimada_valida_por_nivel": {}}
    persistir("cure", meta_base, revs, raiz=tmp_path)
    # smoke: janela temporal por data segue funcionando lado a lado (secundária)
    bloco = atualizar_janela_temporal("cure", raiz=tmp_path)
    assert bloco["total"]["n"] == 6
