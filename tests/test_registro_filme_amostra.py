"""[C14.1] Filme novo classificado NÃO pode sumir do consenso em silêncio.

O defeito medido no piloto: `estender_classificacao_producao.py` somava
reviews a `amostra["reviews"]` e não registrava o filme em
`amostra["filmes"]`; `votacao_3.cmd_consenso` filtra por essa lista, e 7.068
chamadas pagas saíram do consenso sem erro nem aviso. Três travas:

  1. filme classificado (ou amostrado) e ausente da lista → FALHA ALTO, e o
     consenso não é escrito;
  2. o caminho oficial registra o filme, com a MESMA entrada de
     `montar_amostra()`, e antes de qualquer chamada paga;
  3. reexecutar é idempotente.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import classificar_10 as c10  # noqa: E402
import estender_classificacao_producao as est  # noqa: E402
import votacao_3 as v3  # noqa: E402

SLUG = "cure"          # bruto real em disco, com histograma


def _precisa_do_bruto():
    if not (RAIZ / "dados" / "bruto" / SLUG / "meta.json").exists():
        pytest.skip(f"bruto de {SLUG} ausente neste checkout")


def _registro(slug, bucket, rid, passe, tid):
    return {"ok": True, "taxonomia_id": tid, "passe": passe, "slug": slug,
            "perfil": "x", "bucket": bucket, "id": rid, "nivel": 4.0,
            "n_chars": 200, "eixos": ["atuacao"], "eixos_invalidos": []}


def _consenso_isolado(tmp_path, monkeypatch, amostra, registros):
    arq_amostra = tmp_path / "amostra.json"
    arq_amostra.write_text(json.dumps(amostra), encoding="utf-8")
    tid = v3.taxonomia_id()
    passes = {}
    for n in (1, 2, 3):
        p = tmp_path / f"passe_{n}.jsonl"
        p.write_text("".join(json.dumps(_registro(*r, n, tid)) + "\n"
                             for r in registros), encoding="utf-8")
        passes[n] = p
    consenso = tmp_path / "consenso.jsonl"
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", arq_amostra)
    monkeypatch.setattr(v3, "ARQ_PASSE", passes)
    monkeypatch.setattr(v3, "ARQ_CONSENSO", consenso)
    monkeypatch.setattr(v3, "SAIDA", tmp_path)
    monkeypatch.setattr(v3, "RAIZ", tmp_path)
    return consenso


# ===========================================================================
# (1) Classificado e fora da lista → falha alto, nada escrito
# ===========================================================================

def test_filme_classificado_e_nao_registrado_FALHA_ALTO(tmp_path, monkeypatch):
    """Exatamente o piloto: reviews na amostra, três passes completos, filme
    fora de `amostra["filmes"]`. Antes: consenso escrito sem ele, sem aviso."""
    amostra = {"filmes": [{"slug": "registrado"}],
               "reviews": [{"slug": "registrado", "bucket": "positivas", "id": "a"},
                           {"slug": "novo", "bucket": "positivas", "id": "b"}]}
    consenso = _consenso_isolado(tmp_path, monkeypatch, amostra, [
        ("registrado", "positivas", "a"), ("novo", "positivas", "b")])

    with pytest.raises(v3.FilmeForaDaAmostra) as e:
        v3.cmd_consenso()
    assert "novo" in str(e.value)
    assert "registrado'" not in str(e.value)
    assert not consenso.exists(), "o consenso não pode ser escrito sem o filme"


def test_classificado_so_nos_passes_tambem_falha(tmp_path, monkeypatch):
    """Filme com classificação nos passes e nenhuma linha na amostra (a
    amostra foi regenerada sem ele): também é descarte silencioso."""
    amostra = {"filmes": [{"slug": "registrado"}],
               "reviews": [{"slug": "registrado", "bucket": "positivas", "id": "a"}]}
    consenso = _consenso_isolado(tmp_path, monkeypatch, amostra, [
        ("registrado", "positivas", "a"), ("sumido", "negativas", "z")])
    with pytest.raises(v3.FilmeForaDaAmostra) as e:
        v3.cmd_consenso()
    assert "sumido" in str(e.value)
    assert not consenso.exists()


def test_review_na_amostra_de_filme_nao_registrado_falha_sem_passe():
    """Pega ANTES de pagar: a checagem vale com passes vazios, que é como
    `estender` a chama antes de classificar."""
    amostra = {"filmes": [], "reviews": [{"slug": "novo", "bucket": "x", "id": "b"}]}
    with pytest.raises(v3.FilmeForaDaAmostra):
        v3.checar_filmes_registrados(amostra, [])


def test_o_unico_descarte_permitido_e_o_filme_retirado(tmp_path, monkeypatch):
    """`obsession-2026` segue nos passes (append-only) e fora da amostra de
    propósito: é filtrado, não é erro. É o que distingue retirada de
    esquecimento — e a lista é a mesma de `montar_amostra()`."""
    assert "obsession-2026" in c10.SLUGS_BRUTOS_RETIRADOS
    amostra = {"filmes": [{"slug": "registrado"}],
               "reviews": [{"slug": "registrado", "bucket": "positivas", "id": "a"}]}
    consenso = _consenso_isolado(tmp_path, monkeypatch, amostra, [
        ("registrado", "positivas", "a"), ("obsession-2026", "positivas", "c")])
    v3.cmd_consenso()
    linhas = [json.loads(l) for l in consenso.read_text().splitlines()]
    assert {r["slug"] for r in linhas} == {"registrado"}


def test_o_consenso_real_passa_na_checagem():
    """Os 55 filmes em disco estão todos registrados — a checagem não pode
    nascer quebrando o dado real."""
    if not v3.ARQ_AMOSTRA.exists():
        pytest.skip("amostra ausente neste checkout")
    amostra = json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))
    v3.checar_filmes_registrados(amostra, [v3._ler_passe(n) for n in (1, 2, 3)])


# ===========================================================================
# (2) O caminho oficial registra — e antes de pagar
# ===========================================================================

def _faltantes(ids):
    return {SLUG: {"positivas": [SimpleNamespace(id=i, nivel=4.5, n_chars=300,
                                                 texto=f"texto {i}")
                                 for i in ids]}}


@pytest.fixture
def amostra_sem_o_filme(tmp_path, monkeypatch):
    _precisa_do_bruto()
    arq = tmp_path / "amostra.json"
    arq.write_text(json.dumps({"taxonomia_id": c10.taxonomia_id(),
                               "filmes": [], "reviews": []}), encoding="utf-8")
    monkeypatch.setattr(est, "ARQ_AMOSTRA", arq)
    monkeypatch.setattr(est, "RAIZ", tmp_path)   # `main` imprime relativo
    return arq


def test_estender_registra_o_filme_com_a_entrada_de_montar_amostra(
        amostra_sem_o_filme):
    n, novos = est._acrescentar_a_amostra(_faltantes(["r1", "r2"]))
    a = json.loads(amostra_sem_o_filme.read_text(encoding="utf-8"))
    assert (n, novos) == (2, [SLUG])
    assert [f["slug"] for f in a["filmes"]] == [SLUG]
    oficial = next(f for f in c10.montar_amostra()["filmes"] if f["slug"] == SLUG)
    assert a["filmes"][0] == oficial
    assert list(a["filmes"][0]) == list(oficial)   # mesma ordem de chaves
    assert {r["perfil"] for r in a["reviews"]} == {oficial["perfil"]}


def test_reexecucao_e_idempotente(amostra_sem_o_filme):
    est._acrescentar_a_amostra(_faltantes(["r1", "r2"]))
    bytes_1 = amostra_sem_o_filme.read_bytes()
    assert est._acrescentar_a_amostra(_faltantes(["r1", "r2"])) == (0, [])
    assert amostra_sem_o_filme.read_bytes() == bytes_1
    a = json.loads(bytes_1)
    assert [f["slug"] for f in a["filmes"]] == [SLUG]
    assert len(a["reviews"]) == 2


def test_entrada_ja_registrada_nao_e_tocada(amostra_sem_o_filme):
    """As 7 entradas com `n_por_bucket` defasado (C14.1) continuam como
    estão: registrar não é reescrever o que já existe."""
    antiga = {"slug": SLUG, "perfil": "arthouse", "n_por_bucket": {"x": 1}}
    a = json.loads(amostra_sem_o_filme.read_text(encoding="utf-8"))
    a["filmes"] = [antiga]
    amostra_sem_o_filme.write_text(json.dumps(a), encoding="utf-8")
    assert est._acrescentar_a_amostra(_faltantes(["r1"])) == (1, [])
    assert json.loads(amostra_sem_o_filme.read_text())["filmes"] == [antiga]


def _rodar_main(monkeypatch, faltantes, argv=()):
    chamadas = []
    monkeypatch.setattr(est, "_faltantes_por_slug", lambda slugs: faltantes)
    monkeypatch.setattr(est, "classificar_passe",
                        lambda n: chamadas.append(
                            ("passe", n, json.loads(est.ARQ_AMOSTRA.read_text())
                             ["filmes"])))
    monkeypatch.setattr(est, "cmd_consenso", lambda: chamadas.append(("consenso",)))
    monkeypatch.setattr(sys, "argv", ["estender", "--slug", SLUG, *argv])
    est.main()
    return chamadas


def test_main_registra_ANTES_da_primeira_chamada_paga(amostra_sem_o_filme,
                                                      monkeypatch):
    chamadas = _rodar_main(monkeypatch, _faltantes(["r1"]))
    assert [c[:2] for c in chamadas] == [("passe", 1), ("passe", 2),
                                         ("passe", 3), ("consenso",)]
    assert [f["slug"] for f in chamadas[0][2]] == [SLUG]


def test_main_registra_mesmo_sem_review_faltante(amostra_sem_o_filme,
                                                 monkeypatch):
    """Filme já classificado e nunca registrado (o estado do piloto): rodar
    o caminho oficial conserta de graça, sem chamada."""
    chamadas = _rodar_main(monkeypatch, {SLUG: {"positivas": []}})
    assert chamadas == []
    a = json.loads(amostra_sem_o_filme.read_text())
    assert [f["slug"] for f in a["filmes"]] == [SLUG]


def test_dry_run_nao_registra(amostra_sem_o_filme, monkeypatch):
    antes = amostra_sem_o_filme.read_bytes()
    assert _rodar_main(monkeypatch, _faltantes(["r1"]), ["--dry-run"]) == []
    assert amostra_sem_o_filme.read_bytes() == antes


def test_sem_registro_NENHUMA_chamada_paga(amostra_sem_o_filme, monkeypatch):
    """Se o registro falhar por qualquer motivo (aqui: o comportamento antigo,
    que só somava reviews), `main` recusa antes do primeiro passe."""
    def so_reviews(faltantes):
        a = json.loads(est.ARQ_AMOSTRA.read_text())
        a["reviews"].append({"slug": SLUG, "bucket": "positivas", "id": "r1"})
        est.ARQ_AMOSTRA.write_text(json.dumps(a))
        return 1, []
    monkeypatch.setattr(est, "_acrescentar_a_amostra", so_reviews)
    with pytest.raises(v3.FilmeForaDaAmostra):
        _rodar_main(monkeypatch, _faltantes(["r1"]))
