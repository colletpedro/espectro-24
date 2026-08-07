"""[v1.9.1, Entrega 4] Janela temporal em meta.json (SPEC §3[B']).

Motivada por dois achados: o viés de recência medido na v1.9.0 (79-100% da
amostra em ~7 semanas) e o achado do gate desta versão de que `min`/`max`
sozinhos são enganosos (dominados por outlier de data ASSISTIDA antiga, não
de publicação). A correção nos dois é a mesma: gravar a distribuição
(p5/50/95), não só os extremos.
"""
import json

import pytest

from espectro24.bruto import ReviewBruta, atualizar_meta, caminho_meta, janela_temporal, persistir


def _r(rid, data, nivel=4.0):
    return ReviewBruta(id=str(rid), nivel=nivel, texto="x" * 200, n_chars=200,
                       spoiler_flag=False, pagina_origem=1, url="u",
                       autor_hash="h", truncada=False, texto_completo=True,
                       data=data)


# --- função pura, bucket-agnóstica ---

def test_lista_vazia_e_none():
    assert janela_temporal([]) is None


def test_sem_nenhuma_data_e_none():
    assert janela_temporal([_r(1, None)]) is None


def test_uma_review_todos_os_campos_sao_a_mesma_data():
    j = janela_temporal([_r(1, "2026-03-15")])
    assert j == {"n": 1, "min": "2026-03-15", "max": "2026-03-15",
                "p5": "2026-03-15", "p50": "2026-03-15", "p95": "2026-03-15"}


def test_todas_na_mesma_data():
    j = janela_temporal([_r(i, "2026-03-15") for i in range(10)])
    assert j["min"] == j["max"] == j["p5"] == j["p50"] == j["p95"] == "2026-03-15"
    assert j["n"] == 10


def test_min_max_sao_os_extremos_reais():
    j = janela_temporal([_r(1, "2026-06-01"), _r(2, "2026-01-01"), _r(3, "2026-08-07")])
    assert j["min"] == "2026-01-01" and j["max"] == "2026-08-07"


def test_mediana_com_numero_impar():
    j = janela_temporal([_r(1, "2026-01-01"), _r(2, "2026-06-01"), _r(3, "2026-08-01")])
    assert j["p50"] == "2026-06-01"


def test_reviews_sem_data_sao_ignoradas_nao_quebram():
    j = janela_temporal([_r(1, "2026-01-01"), _r(2, None), _r(3, "2026-06-01")])
    assert j["n"] == 2


def test_data_com_hora_e_truncada_para_YYYY_MM_DD():
    j = janela_temporal([_r(1, "2026-08-06T22:04:27.498Z"), _r(2, "2026-08-06")])
    assert j["min"] == j["max"] == "2026-08-06"


def test_percentis_sao_monotonicos():
    j = janela_temporal([_r(i, f"2026-01-{i:02d}") for i in range(1, 29)])
    assert j["min"] <= j["p5"] <= j["p50"] <= j["p95"] <= j["max"]


def test_n_reflete_quantidade_com_data():
    revs = [_r(i, "2026-01-01") for i in range(5)] + [_r(f"s{i}", None) for i in range(3)]
    assert janela_temporal(revs)["n"] == 5


# --- atualizar_meta: mescla sem tocar reviews.jsonl ---

def _meta_base(**over):
    m = {"slug": "cure", "coletado_em": "2026-08-07T00:00:00+00:00",
        "versao_coletor": "1.9.1", "ordenacao_usada": "by/added",
        "histograma_bruto": {}, "paginas_gastas_por_nivel": {},
        "paradas_por_limite": [], "contagem_bruta_por_nivel": {},
        "contagem_estimada_valida_por_nivel": {}}
    m.update(over)
    return m


def test_atualizar_meta_mescla_sem_apagar_campos_existentes(tmp_path):
    persistir("cure", _meta_base(), [_r(1, "2026-01-01")], raiz=tmp_path)
    atualizar_meta("cure", {"janela_temporal": {"total": {"n": 1}}}, raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    assert meta["slug"] == "cure"                      # campo antigo preservado
    assert meta["janela_temporal"] == {"total": {"n": 1}}   # campo novo presente


def test_atualizar_meta_nao_toca_reviews_jsonl(tmp_path):
    from espectro24.bruto import caminho_reviews, carregar
    persistir("cure", _meta_base(), [_r(1, "2026-01-01"), _r(2, "2026-02-01")], raiz=tmp_path)
    antes = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8")
    atualizar_meta("cure", {"janela_temporal": {"total": {"n": 2}}}, raiz=tmp_path)
    depois = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8")
    assert antes == depois


def test_atualizar_meta_sobrescreve_campo_existente(tmp_path):
    persistir("cure", _meta_base(), [_r(1, "2026-01-01")], raiz=tmp_path)
    atualizar_meta("cure", {"ordenacao_usada": "by/activity"}, raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    assert meta["ordenacao_usada"] == "by/activity"


def test_atualizar_meta_filme_sem_meta_ainda_nao_quebra(tmp_path):
    atualizar_meta("nunca-coletado", {"janela_temporal": {"total": None}}, raiz=tmp_path)
    meta = json.loads(caminho_meta("nunca-coletado", tmp_path).read_text(encoding="utf-8"))
    assert meta["janela_temporal"] == {"total": None}


# --- agregação por bucket, via pipeline (a orquestração bucket-aware) ---

def test_pipeline_grava_janela_temporal_por_bucket_e_total(tmp_path):
    from espectro24.pipeline import atualizar_janela_temporal

    revs = ([_r(f"n{i}", "2026-01-01", nivel=0.5) for i in range(3)]
            + [_r(f"p{i}", "2026-08-01", nivel=4.0) for i in range(3)])
    persistir("cure", _meta_base(), revs, raiz=tmp_path)

    atualizar_janela_temporal("cure", raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    jt = meta["janela_temporal"]
    assert jt["total"]["n"] == 6
    assert jt["por_bucket"]["negativas"]["min"] == "2026-01-01"
    assert jt["por_bucket"]["positivas"]["min"] == "2026-08-01"
    assert set(jt["por_bucket"]) == {"negativas", "medianas", "positivas"}


def test_pipeline_bucket_sem_review_com_data_e_none(tmp_path):
    from espectro24.pipeline import atualizar_janela_temporal

    persistir("cure", _meta_base(), [_r(1, "2026-01-01", nivel=0.5)], raiz=tmp_path)
    atualizar_janela_temporal("cure", raiz=tmp_path)
    meta = json.loads(caminho_meta("cure", tmp_path).read_text(encoding="utf-8"))
    assert meta["janela_temporal"]["por_bucket"]["medianas"] is None
