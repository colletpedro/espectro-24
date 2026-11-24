"""`scripts/finetune/c22_leitura.py`: lotes de leitura do dono. Dados sintéticos, zero rede."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import _cego  # noqa: E402
_PASTA_CEGA_ANTES = _cego.PASTA
import c22_leitura as L  # noqa: E402
_cego.PASTA = _PASTA_CEGA_ANTES
import comum as K  # noqa: E402


def _prod(slugs, origem_por=None, sem=None):
    origem_por, sem = origem_por or {}, sem or set()
    out = {}
    for s in slugs:
        for b in K.BUCKETS:
            if (s, b) in sem:
                out[(s, b)] = {"slug": s, "bucket": b, "ok": True, "origem": "c22_sem_fallback",
                               "bucket_final": {"temas": []}}
                continue
            out[(s, b)] = {"slug": s, "bucket": b, "ok": True, "origem": origem_por.get((s, b), "c22_sem_fallback"),
                           "bucket_final": {"temas": [{"tema": "Trilha", "exemplo_parafraseado": "A trilha é marcante.",
                                                       "quantidade_pendente": s == "pend"}]}}
    return out


def _escopo(slugs):
    return {"incluidos": [{"slug": s, "titulo": s.upper(), "ano": 2000} for s in slugs]}


def test_lotes_de_10_sem_os_do_c6_e_sem_divergentes():
    slugs = [f"f{i:02d}" for i in range(40)]
    c6 = slugs[:5]
    prod = _prod(slugs, sem={("f20", "positivas")})
    tmdb_ok = set(slugs) - {"f10"}
    m = L.montar(_escopo(slugs), prod, tmdb_ok, c6)
    assert [len(x) for x in m["lotes"]] == [10, 10, 10]
    assert not (set(sum(m["lotes"], [])) & set(c6))
    assert m["fora"] == {"f10": "tmdb_divergente_ou_indisponivel", "f20": "bucket_positivas_sem_sintese_valida"}
    assert m["sobra"] == [s for s in slugs[5:] if s not in m["fora"]][30:]
    assert m["reler"] == []


def test_bucket_do_c6_trocado_pelo_fallback_vai_para_releitura():
    slugs = [f"f{i:02d}" for i in range(40)]
    prod = _prod(slugs, origem_por={("f01", "positivas"): "c22_fallback_aceito"})
    m = L.montar(_escopo(slugs), prod, set(slugs), slugs[:5])
    assert m["reler"] == [("f01", "positivas")]


def test_documento_marca_a_palavra_de_quantidade_que_sobrou():
    prod = _prod(["pend"])
    doc = L.documento("lote 1", ["pend"], {"pend": "Pend (2000)"}, prod)
    assert "publico? S ou N" in doc and "palavra de quantidade ainda presente em: Trilha" in doc
