"""[v1.9.4] Extensão por déficit ligada ao pipeline, ponta a ponta — §3[B].

Os testes de `test_extensao.py` cobrem a REGRA com dublês; estes cobrem a
FIAÇÃO: que o gancho roda entre o orçamento base e a persistência, que a
telemetria chega ao `meta.json`, e — o mais importante — que o filme cujo
bucket já fecha a meta na base não gasta nem uma requisição a mais.
"""
from __future__ import annotations

import json

import re
import tempfile
from pathlib import Path

from conftest import FakeFetcher, histograma_de_contagens

from espectro24.buckets import NIVEIS, mapa_de_niveis
from espectro24.config import ORCAMENTO_PAGINAS_POR_BUCKET, TETO_EXTENSAO_PAGINAS
from espectro24.pipeline import collect_all_levels
from espectro24.urls import level_page_cache_key
from test_posicionamento import _pagina

HIST = histograma_de_contagens(negativas=1000, medianas=1000, positivas=1000)


def _fetcher(slug: str, profundidade: int, por_pagina: int = 12,
             ordenacao: str = "by/added") -> FakeFetcher:
    """Todo nível com `profundidade` páginas de `por_pagina` reviews longas."""
    resp = {}
    for nivel in NIVEIS:
        for p in range(1, profundidade + 1):
            resp[level_page_cache_key(slug, nivel, p, ordenacao)] = _pagina(
                por_pagina, base_id=int(nivel * 100_000) + p * 1000)
    return FakeFetcher(resp)


def _pagina_mista(n_longas: int, n_curtas: int, base_id: int) -> str:
    """Página com poucas reviews LONGAS e muitas CURTAS.

    É o formato que reproduz a diagnose: se TODAS fossem curtas, a cascata
    (§3[C]) desceria o degrau e as contaria como válidas — o déficit só
    existe quando há material longo suficiente para o degrau de 150 vigorar,
    mas pouco dele.
    """
    longas = _pagina(n_longas, base_id=base_id)
    curtas = re.sub(r"<p>x+</p>", "<p>curta</p>",
                    _pagina(n_curtas, base_id=base_id + 500))
    return (longas.replace("</body></html>", "")
            + curtas.replace("<html><body>", ""))


def _fetcher_misto(slug: str, profundidade: int = 60, n_longas: int = 1,
                   n_curtas: int = 11, ordenacao: str = "by/added") -> FakeFetcher:
    resp = {}
    for nivel in NIVEIS:
        for p in range(1, profundidade + 1):
            resp[level_page_cache_key(slug, nivel, p, ordenacao)] = _pagina_mista(
                n_longas, n_curtas, base_id=int(nivel * 100_000) + p * 1000)
    return FakeFetcher(resp)


def _rodar(ff, slug, tmp_path):
    return collect_all_levels(ff, slug, dados_dir=tmp_path, distribuicao=False)


def _meta(tmp_path, slug) -> dict:
    return json.loads((tmp_path / slug / "meta.json").read_text(encoding="utf-8"))


# --- REGRESSÃO: material farto, nada muda ----------------------------------

def test_material_farto_nao_dispara_extensao_e_nao_gasta_pagina_extra():
    """A garantia que protege os filmes que já fechavam: com material de
    sobra, todo bucket atinge a meta dentro da base e a extensão não faz
    nenhuma requisição."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        ff = _fetcher("farto", profundidade=60, por_pagina=12)
        _rodar(ff, "farto", tmp)
        m = _meta(tmp, "farto")
        for nome, tel in m["extensao_por_bucket"].items():
            assert tel["paginas_extensao"] == 0, nome
            assert tel["motivo_parada"] == "meta_atingida", nome
        assert all(v == 0 for v in m["paginas_extensao_por_nivel"].values())


def test_base_continua_gastando_o_orcamento_de_sempre():
    """Com material farto, cada bucket gasta exatamente as 16 páginas da
    base — o valor não mudou na v1.9.4."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _rodar(_fetcher("farto", profundidade=60), "farto", tmp)
        m = _meta(tmp, "farto")
        base = {float(k): v for k, v in m["paginas_base_por_nivel"].items()}
        for nome, niveis in mapa_de_niveis().items():
            assert sum(base[n] for n in niveis) == ORCAMENTO_PAGINAS_POR_BUCKET


# --- material escasso: a extensão dispara ----------------------------------

def test_material_pobre_dispara_a_extensao_ate_o_teto():
    """O caso da diagnose, em miniatura: páginas de sobra, mas só 1 review
    longa por página — o bucket nunca alcança a meta e a extensão vai até o
    teto, sem nunca excedê-lo."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _rodar(_fetcher_misto("pobre"), "pobre", tmp)
        m = _meta(tmp, "pobre")
        teto_extras = TETO_EXTENSAO_PAGINAS - ORCAMENTO_PAGINAS_POR_BUCKET
        for nome, tel in m["extensao_por_bucket"].items():
            assert tel["paginas_extensao"] == teto_extras, nome
            assert tel["motivo_parada"] == "teto_extensao", nome
            assert tel["n_validas_pos_extensao"] > tel["n_validas_pos_base"], nome
            assert tel["n_validas_pos_extensao"] < tel["meta"], nome
        base = {float(k): v for k, v in m["paginas_base_por_nivel"].items()}
        gastas = {float(k): v for k, v in m["paginas_gastas_por_nivel"].items()}
        for nome, niveis in mapa_de_niveis().items():
            assert sum(base[n] for n in niveis) == ORCAMENTO_PAGINAS_POR_BUCKET
            assert sum(gastas[n] for n in niveis) == TETO_EXTENSAO_PAGINAS


def test_extensao_aumenta_de_fato_o_numero_de_validas():
    """Não basta gastar página: a extensão tem de render válidas. Compara o
    mesmo filme com e sem teto de extensão."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        collect_all_levels(_fetcher_misto("sem_ext"), "sem_ext",
                           dados_dir=tmp, distribuicao=False,
                           teto_extensao=ORCAMENTO_PAGINAS_POR_BUCKET)
        sem = _meta(tmp, "sem_ext")["extensao_por_bucket"]
        _rodar(_fetcher_misto("com_ext"), "com_ext", tmp)
        com = _meta(tmp, "com_ext")["extensao_por_bucket"]
        for nome in sem:
            assert sem[nome]["paginas_extensao"] == 0
            assert com[nome]["n_validas_pos_extensao"] > sem[nome]["n_validas_pos_extensao"]


def test_material_esgotado_para_a_extensao_sem_gastar_o_teto():
    """Filme obscuro: 2 páginas por nível. A extensão descobre o fim do
    material e para por `material_esgotado`, não por teto."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        ff = _fetcher("obscuro", profundidade=2, por_pagina=2)
        _rodar(ff, "obscuro", tmp)
        m = _meta(tmp, "obscuro")
        for nome, tel in m["extensao_por_bucket"].items():
            assert tel["motivo_parada"] == "material_esgotado", nome
            assert tel["paginas_extensao"] < TETO_EXTENSAO_PAGINAS - ORCAMENTO_PAGINAS_POR_BUCKET


# --- telemetria ------------------------------------------------------------

def test_telemetria_da_extensao_chega_ao_meta_json():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _rodar(_fetcher("tel", profundidade=60), "tel", tmp)
        m = _meta(tmp, "tel")
        assert set(m["extensao_por_bucket"]) == set(mapa_de_niveis())
        for tel in m["extensao_por_bucket"].values():
            assert tel["meta"] == 50
            assert tel["paginas_base"] == ORCAMENTO_PAGINAS_POR_BUCKET
            assert tel["motivo_parada"] in {"meta_atingida", "teto_extensao",
                                            "material_esgotado"}


def test_base_mais_extensao_soma_as_paginas_gastas():
    """Invariante de contabilidade: base + extensão == gastas, por nível."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _rodar(_fetcher_misto("soma"), "soma", tmp)
        m = _meta(tmp, "soma")
        for k, gastas in m["paginas_gastas_por_nivel"].items():
            assert gastas == m["paginas_base_por_nivel"][k] + m["paginas_extensao_por_nivel"][k]


def test_extensao_persiste_as_reviews_que_trouxe():
    """A extensão roda ANTES da persistência — o material extra tem de estar
    no `reviews.jsonl`, não só na memória."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _rodar(_fetcher_misto("persist"), "persist", tmp)
        m = _meta(tmp, "persist")
        linhas = (tmp / "persist" / "reviews.jsonl").read_text(
            encoding="utf-8").strip().splitlines()
        esperado = sum(m["paginas_gastas_por_nivel"][k] * 12
                       for k in m["paginas_gastas_por_nivel"])
        assert len(linhas) == esperado


# --- reexecução 100% cache (`--offline`) -----------------------------------

def test_offline_nao_tenta_estender_e_nao_quebra():
    """REGRESSÃO REAL (v1.9.4): sem esta guarda, todo filme coletado ANTES
    desta versão quebrava em `--offline` — a extensão pedia uma página que
    nunca esteve no cache e o `FetchError` subia pelo pipeline inteiro.
    Observado ao vivo em `longlegs`, página 9 do nível 2,0★."""
    class SoOPrimeiroBloco(FakeFetcher):
        """Fetcher que só conhece o que uma coleta ANTERIOR teria cacheado."""
        offline = True

        def get(self, url, cache_key):
            if cache_key not in self.responses:
                from espectro24.fetcher import FetchError
                raise FetchError(f"offline e sem cache para {cache_key}")
            return super().get(url, cache_key)

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # 1) coleta normal, com material pobre → a extensão dispara e grava
        _rodar(_fetcher_misto("off"), "off", tmp)
        antes = _meta(tmp, "off")["extensao_por_bucket"]
        assert any(v["paginas_extensao"] > 0 for v in antes.values())

        # 2) reexecução offline com um cache que só tem as páginas da BASE
        base = _fetcher_misto("off")
        so_base = {k: v for k, v in base.responses.items()
                   if int(k.rsplit("page_", 1)[1].split(".")[0]) <= 12}
        ff = SoOPrimeiroBloco(so_base)
        collect_all_levels(ff, "off", dados_dir=tmp, distribuicao=False)
        # nenhuma posição além do bloco base foi sequer pedida
        pedidas = [int(k.rsplit("page_", 1)[1].split(".")[0])
                   for _u, k in ff.calls if "page_" in k]
        assert pedidas and max(pedidas) <= 12

        # 3) a telemetria da coleta que REALMENTE aconteceu é preservada
        assert _meta(tmp, "off")["extensao_por_bucket"] == antes
