"""[v1.9.0] Persistência do superset bruto (SPEC §3[B']).

O bruto é o artefato que desacopla coleta de análise: ele não sabe nada sobre
fronteira, cota ou filtro. Estes testes cobrem as três propriedades de que o
desacoplamento depende — **idempotência**, **dedupe por id** e
**incrementalidade** — mais a garantia de que nenhuma decisão de SELEÇÃO
vazou para dentro do arquivo.
"""
import json

import pytest

from espectro24.bruto import (
    ReviewBruta,
    autor_hash,
    carregar,
    caminho_meta,
    caminho_reviews,
    dir_do_filme,
    id_estavel,
    persistir,
)


def _rb(rid, nivel=4.0, texto="x" * 200, pagina=1, spoiler=False,
        truncada=False, completo=True, data="2026-01-01", autor="ana"):
    return ReviewBruta(
        id=rid, nivel=nivel, texto=texto, n_chars=len(texto),
        spoiler_flag=spoiler, pagina_origem=pagina,
        url=f"https://letterboxd.com/{autor}/film/cure/", autor_hash=autor_hash(autor),
        truncada=truncada, texto_completo=completo, data=data,
    )


def _meta(**over):
    m = {
        "slug": "cure",
        "coletado_em": "2026-08-07T00:00:00+00:00",
        "versao_coletor": "1.9.0",
        "ordenacao_usada": "by/added",
        "histograma_bruto": {"0.5": 10, "5.0": 90},
        "paginas_gastas_por_nivel": {"4.0": 2},
        "paradas_por_limite": [],
        "contagem_bruta_por_nivel": {"4.0": 24},
        "contagem_estimada_valida_por_nivel": {"4.0": 12},
    }
    m.update(over)
    return m


# --- layout em disco (§3[B']) ---

def test_layout_e_o_da_spec(tmp_path):
    assert dir_do_filme("cure", tmp_path) == tmp_path / "cure"
    assert caminho_meta("cure", tmp_path).name == "meta.json"
    assert caminho_reviews("cure", tmp_path).name == "reviews.jsonl"


def test_persistir_cria_os_dois_arquivos(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    assert caminho_meta("cure", tmp_path).exists()
    assert caminho_reviews("cure", tmp_path).exists()


def test_jsonl_tem_uma_review_por_linha(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1"), _rb("viewing:2")], raiz=tmp_path)
    linhas = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 2
    assert json.loads(linhas[0])["id"] == "viewing:1"


def test_campos_da_linha_sao_os_da_spec(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1", nivel=2.5)], raiz=tmp_path)
    d = json.loads(caminho_reviews("cure", tmp_path).read_text(encoding="utf-8"))
    assert set(d) == {
        # formato pedido
        "id", "nivel", "texto", "n_chars", "spoiler_flag", "pagina_origem",
        "url", "autor_hash",
        # três adições documentadas em §3[B'], todas propriedades da review
        "truncada", "texto_completo", "data",
        # v1.9.6 (§3[B']): a quarta, pelo mesmo critério — COMO a review foi
        # obtida. Sem ela, com duas ordenações no mesmo bruto (§2.3),
        # `pagina_origem=1` significaria "mais recente" e "mais antiga" no
        # mesmo arquivo.
        "ordenacao_origem",
    }
    assert d["nivel"] == 2.5 and d["n_chars"] == 200


def test_nao_grava_decisao_de_selecao_no_bruto(tmp_path):
    """`passou_por_relaxamento` é decisão de SELEÇÃO, não propriedade da review.

    Gravá-la recolocaria no bruto exatamente o tipo de decisão que a v1.9.0
    tirou de lá. Vale para qualquer campo dessa família.
    """
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    texto = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8")
    for proibido in ("passou_por_relaxamento", "bucket", "valida", "selecionada",
                     "filtro_aplicado", "min_chars"):
        assert proibido not in texto


def test_bruto_nao_carrega_nome_de_bucket_nem_no_meta(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    meta_txt = caminho_meta("cure", tmp_path).read_text(encoding="utf-8")
    for nome in ("negativas", "medianas", "positivas"):
        assert nome not in meta_txt


# --- idempotência ---

def test_persistir_duas_vezes_o_mesmo_material_nao_duplica(tmp_path):
    revs = [_rb("viewing:1"), _rb("viewing:2"), _rb("viewing:3")]
    persistir("cure", _meta(), revs, raiz=tmp_path)
    r1 = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8")
    res = persistir("cure", _meta(), revs, raiz=tmp_path)
    r2 = caminho_reviews("cure", tmp_path).read_text(encoding="utf-8")
    assert r1 == r2                      # byte-idêntico
    assert res.n_novas == 0
    assert res.n_total == 3


def test_recoletar_nao_duplica_mesmo_com_ordem_diferente(tmp_path):
    revs = [_rb("viewing:1"), _rb("viewing:2")]
    persistir("cure", _meta(), revs, raiz=tmp_path)
    persistir("cure", _meta(), list(reversed(revs)), raiz=tmp_path)
    _, carregadas = carregar("cure", raiz=tmp_path)
    assert [r.id for r in carregadas] == ["viewing:1", "viewing:2"]  # ordem preservada


def test_dedupe_dentro_do_mesmo_lote(tmp_path):
    res = persistir("cure", _meta(),
                    [_rb("viewing:1"), _rb("viewing:1"), _rb("viewing:2")],
                    raiz=tmp_path)
    assert res.n_total == 2


# --- incrementalidade ---

def test_segunda_coleta_acumula_material_novo(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    res = persistir("cure", _meta(), [_rb("viewing:2"), _rb("viewing:3")],
                    raiz=tmp_path)
    assert res.n_novas == 2 and res.n_total == 3
    _, carregadas = carregar("cure", raiz=tmp_path)
    assert [r.id for r in carregadas] == ["viewing:1", "viewing:2", "viewing:3"]


def test_review_reincidente_e_atualizada_na_posicao_original(tmp_path):
    """Um completamento resolvido numa execução POSTERIOR precisa entrar.

    Caso real: a review foi persistida truncada (texto visível) numa coleta e
    o texto completo só foi resolvido depois. A linha nova sobrescreve a
    antiga do mesmo id — mas na posição original, para não embaralhar a ordem
    de amostragem de que a seleção depende (§3[C2], passo 5).
    """
    persistir("cure", _meta(),
              [_rb("viewing:1", texto="curto", completo=False, truncada=True),
               _rb("viewing:2")], raiz=tmp_path)
    res = persistir("cure", _meta(),
                    [_rb("viewing:1", texto="y" * 900, completo=True, truncada=True)],
                    raiz=tmp_path)
    assert res.n_novas == 0 and res.n_atualizadas == 1
    _, carregadas = carregar("cure", raiz=tmp_path)
    assert [r.id for r in carregadas] == ["viewing:1", "viewing:2"]
    assert carregadas[0].n_chars == 900 and carregadas[0].texto_completo is True


def test_meta_e_sobrescrito_pela_execucao_mais_recente(tmp_path):
    persistir("cure", _meta(ordenacao_usada="by/activity"), [_rb("viewing:1")],
              raiz=tmp_path)
    persistir("cure", _meta(ordenacao_usada="by/added"), [_rb("viewing:2")],
              raiz=tmp_path)
    meta, revs = carregar("cure", raiz=tmp_path)
    assert meta["ordenacao_usada"] == "by/added"
    assert len(revs) == 2       # material ACUMULA mesmo com o meta trocando


def test_meta_registra_os_campos_da_spec(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    meta, _ = carregar("cure", raiz=tmp_path)
    for campo in ("slug", "coletado_em", "versao_coletor", "ordenacao_usada",
                  "histograma_bruto", "paginas_gastas_por_nivel",
                  "paradas_por_limite", "contagem_bruta_por_nivel",
                  "contagem_estimada_valida_por_nivel"):
        assert campo in meta


# --- round-trip e casos de borda ---

def test_round_trip_preserva_todos_os_campos(tmp_path):
    r = _rb("viewing:9", nivel=0.5, texto="ação é ótimo — çãé", pagina=3,
            spoiler=True, truncada=True, completo=False, data="2011-05-02")
    persistir("cure", _meta(), [r], raiz=tmp_path)
    _, (lido,) = carregar("cure", raiz=tmp_path)
    assert lido == r


def test_carregar_filme_inexistente_e_vazio(tmp_path):
    meta, revs = carregar("nao-existe", raiz=tmp_path)
    assert meta is None and revs == []


def test_linha_corrompida_e_ignorada_sem_derrubar_a_carga(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1"), _rb("viewing:2")], raiz=tmp_path)
    p = caminho_reviews("cure", tmp_path)
    p.write_text(p.read_text(encoding="utf-8") + "{lixo não-json\n", encoding="utf-8")
    _, revs = carregar("cure", raiz=tmp_path)
    assert [r.id for r in revs] == ["viewing:1", "viewing:2"]


def test_persistir_lote_vazio_nao_apaga_o_que_ja_existe(tmp_path):
    persistir("cure", _meta(), [_rb("viewing:1")], raiz=tmp_path)
    res = persistir("cure", _meta(), [], raiz=tmp_path)
    assert res.n_total == 1


# --- id estável para review sem viewing_id ---

def test_id_estavel_e_deterministico():
    a = id_estavel(4.0, "mesmo texto")
    b = id_estavel(4.0, "mesmo texto")
    assert a == b and a.startswith("txt:")


def test_id_estavel_distingue_texto_e_nivel():
    assert id_estavel(4.0, "a") != id_estavel(4.0, "b")
    assert id_estavel(4.0, "a") != id_estavel(4.5, "a")


def test_review_sem_viewing_id_ainda_deduplica(tmp_path):
    """Sem id do Letterboxd, o dedupe cairia — e a recoleta duplicaria tudo.

    O id derivado do conteúdo (nivel+texto) é determinístico, então a mesma
    review anônima vinda duas vezes continua sendo uma só.
    """
    r = _rb(id_estavel(4.0, "sem viewing id"), texto="sem viewing id")
    persistir("cure", _meta(), [r], raiz=tmp_path)
    res = persistir("cure", _meta(), [r], raiz=tmp_path)
    assert res.n_total == 1


# --- autor_hash: estável e sem o handle em claro ---

def test_autor_hash_e_estavel_e_nao_contem_o_handle():
    h = autor_hash("justinwuah")
    assert h == autor_hash("justinwuah")
    assert "justinwuah" not in h
    assert autor_hash("justinwuah") != autor_hash("outra-pessoa")


def test_autor_hash_de_ausente_e_vazio():
    assert autor_hash(None) == ""
    assert autor_hash("") == ""
