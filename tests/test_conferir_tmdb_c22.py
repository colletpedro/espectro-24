"""`scripts/conferir_tmdb_c22.py`: conferência de identidade (TMDB) dos filmes do C22. Zero rede."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import conferir_tmdb_c22 as T  # noqa: E402


def _bruto(tmp_path, slug, identidade):
    (tmp_path / slug).mkdir()
    meta = {"slug": slug}
    if identidade is not None:
        meta["identidade_letterboxd"] = identidade
    (tmp_path / slug / "meta.json").write_text(json.dumps(meta))


def _ident(**kw):
    return {"titulo": "Perfect Blue", "tmdb_id_letterboxd": 10494, "ano": 1997, **kw}


def test_validada_traz_o_ano_do_tmdb_da_evidencia(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "BRUTO", tmp_path)
    _bruto(tmp_path, "pb", _ident())
    ficha = {"tmdb_id": 10494, "ano": 1997,
             "identidade": {"ano_tmdb": 1998, "ano_divergente": True,
                            "titulo_tmdb_correspondente": "PERFECT BLUE", "titulo_tmdb_campo": "original_title"}}
    monkeypatch.setattr(T.F, "buscar_ficha", lambda *a, **k: (ficha, None, None))
    r = T.conferir("pb", "k", cache=tmp_path)
    assert r["estado"] == "validada" and r["ano_tmdb"] == 1998 and r["ano_divergente"] is True


def test_divergente_quando_a_ficha_foi_descartada(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "BRUTO", tmp_path)
    _bruto(tmp_path, "pb", _ident())
    monkeypatch.setattr(T.F, "buscar_ficha", lambda *a, **k: (None, "titulo nao confere", {"motivo": "titulo_divergente"}))
    r = T.conferir("pb", "k", cache=tmp_path)
    assert r["estado"] == "divergente" and r["motivo"] == "titulo_divergente"


def test_sem_identidade_e_sem_ano_nao_consultam_o_tmdb(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "BRUTO", tmp_path)
    monkeypatch.setattr(T.F, "buscar_ficha", lambda *a, **k: (_ for _ in ()).throw(AssertionError("não devia consultar")))
    _bruto(tmp_path, "a", None)
    _bruto(tmp_path, "b", _ident(ano=None))
    assert T.conferir("a", "k", cache=tmp_path)["estado"] == "sem_identidade"
    assert T.conferir("b", "k", cache=tmp_path)["estado"] == "ano_desconhecido"


def test_indisponivel_quando_o_tmdb_nao_respondeu(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "BRUTO", tmp_path)
    _bruto(tmp_path, "pb", _ident())
    monkeypatch.setattr(T.F, "buscar_ficha", lambda *a, **k: (None, "TMDB fora do ar", None))
    assert T.conferir("pb", "k", cache=tmp_path)["estado"] == "tmdb_indisponivel"


def test_so_a_chave_do_tmdb_sai_do_env(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=pago\nTMDB_API_KEY=abc123\nFEATHERLESS_API_KEY=pago2\n")
    monkeypatch.setattr(T, "RAIZ", tmp_path)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    assert T.chave_do_env() == "abc123"
    import os
    assert "DEEPSEEK_API_KEY" not in os.environ or os.environ["DEEPSEEK_API_KEY"] != "pago"
