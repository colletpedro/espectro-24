"""Adaptador da importação manual (`scripts/importar_manual.py`).

Garantias: o bruto sai no formato do coletor (o resto do pipeline não sabe a
diferença); recusa do arquivo inteiro com mensagem clara; identidade fora do
TMDB vai para a quarentena; dedupe por `review_id` e por `url`; spoiler tratado
como o coletor (flag gravado, exclusão na seleção); nenhuma rede.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import importar_manual as IM  # noqa: E402
from espectro24.bruto import ReviewBruta, carregar, persistir  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

HIST = {"0.5": 1, "1": 2, "1.5": 3, "2": 4, "2.5": 5, "3": 6, "3.5": 7,
        "4": 8, "4.5": 9, "5": 10}


def _meta(**kw):
    m = {"slug": "/film/filme-x/", "titulo": "Filme X", "ano": 1999,
         "tmdb_id": "123", "histograma": dict(HIST), "total_notas": 55,
         "coletado_em": "2026-11-26T12:40:00-03:00"}
    m.update(kw)
    return m


def _rev(usuario="ana", nota=4.0, texto="Texto de teste com bastante conteudo.",
         spoiler=False, sufixo="", slug="filme-x", **kw):
    r = {"review_id": f"/{usuario}/film/{slug}/{sufixo}",
         "url": f"https://letterboxd.com/{usuario}/film/{slug}/{sufixo}",
         "usuario": usuario, "nota": nota, "data": "2026-11-25",
         "spoiler": spoiler, "review": texto}
    r.update(kw)
    return r


def _ficha_ok(identidade):
    return ({"tmdb_id": int(identidade["tmdb_id_letterboxd"]), "duracao_min": 120,
             "ano": identidade["ano"],
             "identidade": {"ano_tmdb": identidade["ano"]}}, None, None)


def _paises_ok(tmdb_id):
    return ["US", "GB"]


def _escrever(tmp, meta, reviews, nome="in"):
    d = tmp / nome
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (d / "reviews.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reviews),
        encoding="utf-8")
    return d / "meta.json", d / "reviews.jsonl"


def _importar(tmp, meta, reviews, ficha_fn=_ficha_ok, **kw):
    m, r = _escrever(tmp, meta, reviews)
    kw.setdefault("paises_fn", _paises_ok)
    return IM.importar(m, r, raiz_bruto=tmp / "bruto",
                       raiz_importacao=tmp / "imp", ficha_fn=ficha_fn, **kw)


def _sem_rede(monkeypatch):
    import socket

    def _proibido(*a, **k):
        raise AssertionError("o adaptador não pode abrir conexão de rede")
    monkeypatch.setattr(socket.socket, "connect", _proibido)


# --- slug -----------------------------------------------------------------

@pytest.mark.parametrize("entrada,esperado", [
    ("/film/boogie-nights/", "boogie-nights"),
    ("film/boogie-nights", "boogie-nights"),
    ("boogie-nights", "boogie-nights"),
    ("https://letterboxd.com/film/boogie-nights/", "boogie-nights"),
    ("/film/primetime-2026/", "primetime-2026"),
])
def test_slug_normalizado(entrada, esperado):
    assert IM.normalizar_slug(entrada) == esperado


@pytest.mark.parametrize("ruim", ["", "   ", None, "/film/", "/film/a/b/", "Boogie Nights"])
def test_slug_invalido_e_recusado(ruim):
    with pytest.raises(IM.ImportacaoRecusada):
        IM.normalizar_slug(ruim)


# --- histograma -----------------------------------------------------------

def test_histograma_normaliza_chaves_para_a_forma_do_coletor():
    h = IM.validar_histograma(dict(HIST), 55)
    assert list(h) == ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"]
    assert sum(h.values()) == 55


def test_histograma_que_nao_soma_e_recusado():
    with pytest.raises(IM.ImportacaoRecusada, match="soma=55 total_notas=56"):
        IM.validar_histograma(dict(HIST), 56)


@pytest.mark.parametrize("hist", [{}, {"6": 1}, {"abc": 1}, {"1": -1}, {"1": 1.5}])
def test_histograma_invalido_e_recusado(hist):
    with pytest.raises(IM.ImportacaoRecusada):
        IM.validar_histograma(hist, 1)


def test_histograma_nivel_repetido_por_formato_e_recusado():
    with pytest.raises(IM.ImportacaoRecusada, match="repetido"):
        IM.validar_histograma({"1": 1, "1.0": 1}, 2)


# --- meta -----------------------------------------------------------------

@pytest.mark.parametrize("campo", list(_meta()))
def test_meta_sem_campo_obrigatorio_e_recusado(campo, tmp_path):
    m = _meta()
    del m[campo]
    with pytest.raises(IM.ImportacaoRecusada, match=campo):
        IM.validar_meta(m)


def test_meta_normalizado():
    n = IM.validar_meta(_meta())
    assert (n["slug"], n["ano"], n["tmdb_id"]) == ("filme-x", 1999, 123)


# --- reviews --------------------------------------------------------------

@pytest.mark.parametrize("nota", [0, 0.0, 0.4, 5.5, 6, -1, 3.3, "4", True, None])
def test_nota_fora_de_05_a_5_recusa_o_arquivo_inteiro(nota, tmp_path):
    revs = [_rev("ana"), _rev("bia", nota=nota)]
    with pytest.raises(IM.ImportacaoRecusada, match="linha 2"):
        _importar(tmp_path, _meta(), revs)
    assert not (tmp_path / "bruto").exists()   # NADA gravado, nem a review boa


@pytest.mark.parametrize("campo", ["review_id", "url", "usuario", "nota", "data", "spoiler", "review"])
def test_review_sem_campo_obrigatorio_recusa_o_arquivo(campo, tmp_path):
    r = _rev("bia")
    del r[campo]
    with pytest.raises(IM.ImportacaoRecusada, match=campo):
        _importar(tmp_path, _meta(), [_rev("ana"), r])
    assert not (tmp_path / "bruto").exists()


def test_texto_vazio_conta_como_campo_ausente(tmp_path):
    with pytest.raises(IM.ImportacaoRecusada, match="review"):
        _importar(tmp_path, _meta(), [_rev("ana", texto="   ")])


def test_review_de_outro_filme_recusa_o_arquivo(tmp_path):
    with pytest.raises(IM.ImportacaoRecusada, match="outro filme"):
        _importar(tmp_path, _meta(), [_rev("ana"), _rev("bia", slug="outro")])


def test_review_id_de_outro_usuario_recusa(tmp_path):
    r = _rev("ana")
    r["review_id"] = "/bia/film/filme-x/"
    with pytest.raises(IM.ImportacaoRecusada, match="outro usuário"):
        _importar(tmp_path, _meta(), [r])


def test_json_corrompido_recusa_em_vez_de_ignorar_linha(tmp_path):
    m, r = _escrever(tmp_path, _meta(), [_rev("ana")])
    r.write_text(r.read_text() + "{quebrado\n", encoding="utf-8")
    with pytest.raises(IM.ImportacaoRecusada, match="JSON inválido"):
        IM.importar(m, r, raiz_bruto=tmp_path / "bruto", ficha_fn=_ficha_ok, paises_fn=_paises_ok)


def test_arquivo_sem_reviews_e_recusado(tmp_path):
    with pytest.raises(IM.ImportacaoRecusada, match="sem nenhuma review"):
        _importar(tmp_path, _meta(), [])


# --- formato do bruto -----------------------------------------------------

def test_grava_no_formato_do_coletor(tmp_path):
    rel = _importar(tmp_path, _meta(), [_rev("ana", 4.0), _rev("bia", 0.5, spoiler=True)])
    assert (rel["n_novas"], rel["modo"]) == (2, "novo")
    meta, reviews = carregar("filme-x", raiz=tmp_path / "bruto")
    # o carregador do pipeline lê sem saber a origem
    assert [r.nivel for r in reviews] == [4.0, 0.5]
    r = reviews[0]
    assert isinstance(r, ReviewBruta)
    assert (r.id, r.texto_completo, r.truncada, r.pagina_origem, r.data) == (
        "/ana/film/filme-x/", True, False, 1, "2026-11-25")
    assert r.n_chars == len(r.texto)
    assert r.autor_hash and "ana" not in r.autor_hash
    assert r.ordenacao_origem == "importacao_manual"
    assert reviews[1].spoiler_flag is True
    # chaves que o pipeline lê do meta
    assert meta["histograma_bruto"]["1.0"] == 2 and meta["slug"] == "filme-x"
    assert meta["identidade_letterboxd"]["tmdb_id_letterboxd"] == 123
    assert meta["ano_lancamento"] == 1999
    # nada que o pipeline interprete como orçamento de páginas / estratificação
    assert "orcamento_paginas_por_nivel" not in meta


def test_meta_marca_origem_data_e_hash_dos_arquivos(tmp_path):
    m, r = _escrever(tmp_path, _meta(), [_rev("ana")])
    IM.importar(m, r, raiz_bruto=tmp_path / "bruto", ficha_fn=_ficha_ok,
                paises_fn=_paises_ok, agora="2026-11-26T15:00:00+00:00")
    meta, _ = carregar("filme-x", raiz=tmp_path / "bruto")
    im = meta["importacao_manual"]
    assert im["origem"] == "importacao_manual"
    assert im["importado_em"] == "2026-11-26T15:00:00+00:00"
    assert im["arquivos"]["meta"]["sha256"] == IM.sha256_arquivo(m)
    assert im["arquivos"]["reviews"]["sha256"] == IM.sha256_arquivo(r)
    assert "diario" in im["data_semantica"] and "NAO" in im["data_semantica"]
    # nada que dependa da data de publicação foi calculado
    assert "janela_temporal" not in {k for k in meta if meta[k] not in (None, "")} - {"importacao_manual"}
    assert "dias_por_100_paginas" not in meta


def test_importacao_e_idempotente_byte_a_byte(tmp_path):
    revs = [_rev("ana"), _rev("bia", 2.0)]
    _importar(tmp_path, _meta(), revs, agora="2026-11-26T15:00:00+00:00")
    arq = tmp_path / "bruto" / "filme-x" / "reviews.jsonl"
    antes = arq.read_bytes()
    rel = _importar(tmp_path, _meta(), revs, agora="2026-11-26T15:00:00+00:00")
    assert rel["n_novas"] == 0 and rel["n_ja_existentes_por_id"] == 2
    assert arq.read_bytes() == antes


def test_dry_run_nao_grava(tmp_path):
    rel = _importar(tmp_path, _meta(), [_rev("ana")], dry_run=True)
    assert rel["n_novas"] == 1 and not (tmp_path / "bruto").exists()


# --- dedupe ---------------------------------------------------------------

def test_review_id_repetido_no_arquivo_entra_uma_vez(tmp_path):
    rel = _importar(tmp_path, _meta(), [_rev("ana"), _rev("ana", texto="outra")])
    assert (rel["n_novas"], rel["n_duplicadas_no_arquivo"]) == (1, 1)
    _, rs = carregar("filme-x", raiz=tmp_path / "bruto")
    assert len(rs) == 1 and rs[0].texto.startswith("Texto de teste")   # a primeira vale


def _bruto_do_coletor(tmp_path, id_="viewing:777", url="https://letterboxd.com/ana/film/filme-x/"):
    antigo = ReviewBruta(id=id_, nivel=4.0, texto="Review do coletor antigo.", n_chars=25,
                         spoiler_flag=False, pagina_origem=3, url=url, autor_hash="h",
                         truncada=False, texto_completo=True, data="2026-09-01",
                         ordenacao_origem="by/added")
    meta_antigo = {"slug": "filme-x", "versao_coletor": "1.9.6", "ordenacao_usada": "by/added",
                   "orcamento_paginas_por_nivel": {"4.0": 3}, "histograma_bruto": {"4.0": 9}}
    persistir("filme-x", meta_antigo, [antigo], raiz=tmp_path / "bruto")
    return meta_antigo


def test_dedupe_contra_bruto_existente_por_review_id(tmp_path):
    antigo = ReviewBruta(id="/ana/film/filme-x/", nivel=4.0, texto="t", n_chars=1,
                         spoiler_flag=False, pagina_origem=1, url="", autor_hash="h",
                         truncada=False, texto_completo=True, data=None)
    persistir("filme-x", {"slug": "filme-x"}, [antigo], raiz=tmp_path / "bruto")
    rel = _importar(tmp_path, _meta(), [_rev("ana"), _rev("bia")])
    assert (rel["n_ja_existentes_por_id"], rel["n_novas"]) == (1, 1)


def test_dedupe_contra_bruto_do_coletor_por_url(tmp_path):
    # o id do coletor é `viewing:N`; só a URL casa com a da exportação manual
    _bruto_do_coletor(tmp_path)
    rel = _importar(tmp_path, _meta(), [_rev("ana"), _rev("bia")])
    assert (rel["n_ja_existentes_por_url"], rel["n_novas"]) == (1, 1)
    _, rs = carregar("filme-x", raiz=tmp_path / "bruto")
    assert [r.id for r in rs] == ["viewing:777", "/bia/film/filme-x/"]


def test_meta_do_coletor_nao_e_sobrescrito_na_mescla(tmp_path):
    antigo = _bruto_do_coletor(tmp_path)
    rel = _importar(tmp_path, _meta(), [_rev("bia")])
    assert rel["modo"] == "mescla"
    meta, _ = carregar("filme-x", raiz=tmp_path / "bruto")
    assert meta["orcamento_paginas_por_nivel"] == antigo["orcamento_paginas_por_nivel"]
    assert meta["versao_coletor"] == "1.9.6"
    assert meta["importacoes_manuais"][0]["origem"] == "importacao_manual"


# --- identidade -----------------------------------------------------------

def _ficha_com(**alt):
    def f(identidade):
        ficha, a, d = _ficha_ok(identidade)
        ficha.update(alt)
        return ficha, a, d
    return f


@pytest.mark.parametrize("ficha_fn,trecho", [
    (lambda i: (None, "TMDB: título não comprova", {"motivo": "titulo_divergente"}), "titulo_divergente"),
    (lambda i: (None, "TMDB: duração", {"motivo": "duracao_incompativel_com_longa"}), "duracao_incompativel"),
    (_ficha_com(duracao_min=39), "duração 39"),
    (_ficha_com(duracao_min=None), "duração None"),
    (_ficha_com(tmdb_id=999), "tmdb_id da ficha"),
    (_ficha_com(identidade={"ano_tmdb": 2005}), "ano do meta"),
])
def test_identidade_divergente_vai_para_quarentena_e_nao_importa(tmp_path, ficha_fn, trecho):
    with pytest.raises(IM.IdentidadeDivergente, match=trecho):
        _importar(tmp_path, _meta(), [_rev("ana")], ficha_fn=ficha_fn)
    assert not (tmp_path / "bruto").exists()
    q = tmp_path / "imp" / "_quarentena" / "filme-x"
    assert (q / "meta.json").exists() and (q / "reviews.jsonl").exists()
    assert trecho in json.loads((q / "motivo.json").read_text())["motivo"]


def test_duracao_exatamente_40_passa(tmp_path):
    _importar(tmp_path, _meta(), [_rev("ana")], ficha_fn=_ficha_com(duracao_min=40))


def test_ano_com_diferenca_de_1_passa(tmp_path):
    _importar(tmp_path, _meta(), [_rev("ana")],
              ficha_fn=_ficha_com(identidade={"ano_tmdb": 2000}))


def test_identidade_entregue_a_ficha_e_a_do_meta(tmp_path):
    vistas = []

    def f(identidade):
        vistas.append(identidade)
        return _ficha_ok(identidade)
    _importar(tmp_path, _meta(), [_rev("ana")], ficha_fn=f)
    assert vistas == [{"slug": "filme-x", "titulo": "Filme X", "ano": 1999,
                       "tmdb_id_letterboxd": 123, "fonte": "importacao_manual"}]


def test_nada_e_gravado_se_a_validacao_falha_antes_da_identidade(tmp_path):
    chamadas = []
    with pytest.raises(IM.ImportacaoRecusada):
        _importar(tmp_path, _meta(total_notas=1), [_rev("ana")],
                  ficha_fn=lambda i: chamadas.append(i) or _ficha_ok(i))
    assert chamadas == []   # nem consulta o TMDB com material recusado


# --- spoiler e seleção ----------------------------------------------------

def test_spoiler_e_gravado_e_a_selecao_exclui_como_sempre(tmp_path):
    textos = "x" * 200
    revs = [_rev("ana", 5.0, textos), _rev("bia", 5.0, textos, spoiler=True)]
    _importar(tmp_path, _meta(), revs)
    meta, rs = carregar("filme-x", raiz=tmp_path / "bruto")
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    sel = selecionar(rs, hist)
    ids = {r.id for b in sel.values() for n in b.niveis.values() for r in n.validas}
    assert ids == {"/ana/film/filme-x/"}
    assert sel["positivas"].niveis[5.0].motivos_descarte["spoiler"] == 1


# --- usuário repetido -----------------------------------------------------

def test_usuario_com_duas_reviews_entra_com_as_duas_e_e_reportado(tmp_path):
    revs = [_rev("seb", 4.5, sufixo="1/"), _rev("seb", 4.5), _rev("bia")]
    rel = _importar(tmp_path, _meta(), revs)
    assert rel["n_novas"] == 3     # o adaptador não inventa regra por autor
    assert set(rel["usuarios_repetidos"]) == {"seb"}
    assert len(rel["usuarios_repetidos"]["seb"]) == 2


def test_selecao_nao_tem_regra_por_autor():
    """Se este teste quebrar, alguém criou uma regra por autor: o relatório da
    importação manual precisa ser revisto (ela afirma que não existe)."""
    import inspect
    from espectro24 import selecao
    assert "autor" not in inspect.getsource(selecao).lower().replace("autor_hash", "")


# --- rede -----------------------------------------------------------------

def test_o_adaptador_nao_usa_rede_proprio(tmp_path, monkeypatch):
    _sem_rede(monkeypatch)
    _importar(tmp_path, _meta(), [_rev("ana")])   # ficha injetada: zero conexão


def test_o_adaptador_nao_importa_o_fetcher_do_letterboxd():
    src = (RAIZ / "scripts" / "importar_manual.py").read_text(encoding="utf-8")
    assert "fetcher" not in src.lower().replace("fetcher do letterboxd", "")
    assert "collect_all_levels" not in src


# --- países (ficha.paises) -------------------------------------------------

def test_paises_do_tmdb_vao_para_o_meta_e_para_a_ficha(tmp_path):
    rel = _importar(tmp_path, _meta(), [_rev("ana")])
    assert rel["paises"] == ["US", "GB"]
    meta, _ = carregar("filme-x", raiz=tmp_path / "bruto")
    assert meta["paises_tmdb"] == ["US", "GB"]
    ficha = IM.ficha_com_paises({"tmdb_id": 123, "titulo": "Filme X"}, meta)
    assert ficha["paises"] == ["US", "GB"] and ficha["titulo"] == "Filme X"


def test_ficha_sem_paises_no_meta_e_erro_nao_lista_vazia():
    with pytest.raises(IM.ImportacaoRecusada, match="sem `paises`"):
        IM.ficha_com_paises({"tmdb_id": 1}, {})


@pytest.mark.parametrize("ruim", [[], None, ["usa"], ["US", "US"], [None], "US"])
def test_paises_invalidos_recusam_o_arquivo_inteiro(tmp_path, ruim):
    with pytest.raises(IM.ImportacaoRecusada, match="production_countries"):
        _importar(tmp_path, _meta(), [_rev("ana")], paises_fn=lambda i: ruim)
    assert not (tmp_path / "bruto").exists()


def test_paises_so_sao_pedidos_depois_da_identidade_provada(tmp_path):
    pedidos = []
    with pytest.raises(IM.IdentidadeDivergente):
        _importar(tmp_path, _meta(), [_rev("ana")], ficha_fn=_ficha_com(duracao_min=10),
                  paises_fn=lambda i: pedidos.append(i) or ["US"])
    assert pedidos == []


def test_paises_do_tmdb_le_o_detalhe_na_ordem_e_cacheia(tmp_path, monkeypatch):
    chamadas = []

    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {"id": 77, "production_countries": [
                {"iso_3166_1": "FR", "name": "France"}, {"iso_3166_1": "IT", "name": "Italy"}]}

    class Sess:
        def get(self, url, **kw):
            chamadas.append(url)
            return Resp()

    monkeypatch.setenv("TMDB_API_KEY", "x")
    cache = tmp_path / "det"
    assert IM.paises_do_tmdb(77, cache=cache, session=Sess()) == ["FR", "IT"]
    assert IM.paises_do_tmdb(77, cache=cache, session=Sess()) == ["FR", "IT"]   # cache
    assert len(chamadas) == 1 and (cache / "77.json").exists()


def test_reimportar_o_mesmo_par_nao_duplica_o_registro_da_importacao(tmp_path):
    revs = [_rev("ana")]
    _importar(tmp_path, _meta(), revs)
    _importar(tmp_path, _meta(), revs)
    meta, _ = carregar("filme-x", raiz=tmp_path / "bruto")
    assert "importacoes_manuais" not in meta and meta["paises_tmdb"] == ["US", "GB"]


# --- CLI ------------------------------------------------------------------

def test_cli_recusa_com_codigo_2_e_mensagem(tmp_path, capsys):
    m, r = _escrever(tmp_path, _meta(total_notas=1), [_rev("ana")])
    assert IM.main(["--meta", str(m), "--reviews", str(r), "--dry-run"]) == 2
    assert "RECUSADO (nada gravado)" in capsys.readouterr().err


def test_ler_a_chave_do_tmdb_nao_despeja_o_env_no_ambiente(monkeypatch, tmp_path):
    """Regressão: `load_dotenv` poluía o ambiente e quebrava `test_provider`
    (detecção de provider pela ÚNICA chave presente) na suíte inteira."""
    import os
    for k in ("DEEPSEEK_API_KEY", "GEMINI_API_KEY", "FEATHERLESS_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("TMDB_API_KEY=abc\nDEEPSEEK_API_KEY=zzz\nGEMINI_API_KEY=yyy\n")
    monkeypatch.setattr(IM, "RAIZ", tmp_path)
    assert IM.chave_tmdb() == "abc"
    assert "DEEPSEEK_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ
    assert "TMDB_API_KEY" not in os.environ
