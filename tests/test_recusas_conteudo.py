"""[2026-09-23, C22] Reviews recusadas pelo filtro de conteúdo: SUBSTITUÍDAS.

Decisão do dono: não reduzir o `n` e não afrouxar a guarda C14.8 — a review
recusada sai da seleção e a próxima elegível do MESMO bucket entra, pela
mesma regra determinística. O que se prova:

1. `selecionar(excluir_ids=…)` tira a recusada e completa a cota com a próxima
   na ordem de sempre; vazio é byte a byte a seleção de antes; a contabilidade
   de descarte continua fechando (`recusada_conteudo` só existe quando há);
2. esgotada a reserva, o `n` cai — e a seleção não inventa review;
3. o registro só aceita os 55, é idempotente e anota a substituta;
4. a detecção exige 2 tentativas bloqueadas e nenhuma ok;
5. a recusada deixa de ser pendente e de contar como incompleta.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))

from espectro24 import excecao_c22 as C22  # noqa: E402
from espectro24 import recusas  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402
from test_selecao import HIST, _muitas, _r  # noqa: E402

SLUG = sorted(C22.SLUGS)[0]


def _ids(sel, bucket):
    return [r.id for ns in sel[bucket].niveis.values() for r in ns.validas]


def test_vazio_e_a_selecao_de_sempre():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    a, b = selecionar(revs, HIST), selecionar(revs, HIST, excluir_ids=frozenset())
    for bucket in a:
        assert _ids(a, bucket) == _ids(b, bucket)
        for n in a[bucket].niveis:
            assert "recusada_conteudo" not in a[bucket].niveis[n].motivos_descarte


def test_a_recusada_sai_e_a_proxima_elegivel_do_mesmo_nivel_entra():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    antes = _ids(selecionar(revs, HIST), "negativas")
    recusada = antes[5]
    depois = _ids(selecionar(revs, HIST, excluir_ids=frozenset({recusada})),
                  "negativas")
    assert recusada not in depois and len(depois) == len(antes) == 40
    entrou = set(depois) - set(antes)
    assert set(antes) - set(depois) == {recusada} and len(entrou) == 1
    nivel = float(recusada.split("-")[0])
    assert float(next(iter(entrou)).split("-")[0]) == nivel   # mesmo nível


def test_a_contabilidade_de_descarte_continua_fechando():
    revs = [r for n in (0.5, 1.0, 1.5, 2.0) for r in _muitas(n, 50)]
    recusada = _ids(selecionar(revs, HIST), "negativas")[0]
    sel = selecionar(revs, HIST, excluir_ids=frozenset({recusada}))
    for ns in sel["negativas"].niveis.values():
        assert sum(ns.motivos_descarte.values()) == ns.n_brutas - ns.n_validas
    assert sum(ns.motivos_descarte.get("recusada_conteudo", 0)
               for ns in sel["negativas"].niveis.values()) == 1


def test_reserva_esgotada_o_n_cai_sem_inventar_review():
    revs = [_r(f"a-{i}", 0.5) for i in range(3)]
    sel = selecionar(revs, {0.5: 1}, excluir_ids=frozenset({"a-1"}))
    assert _ids(sel, "negativas") == ["a-0", "a-2"]


# --- o registro -----------------------------------------------------------

def _recusa(rid, bucket="negativas", slug=SLUG):
    return {"slug": slug, "bucket": bucket, "id": rid, "provider": "gemini",
            "modelo": "gemini-3.7-flash", "bloqueio": "PROHIBITED_CONTENT",
            "n_tentativas_bloqueadas": 2, "evidencia": "teste"}


def test_o_registro_so_aceita_os_55_e_e_idempotente():
    with pytest.raises(C22.ForaDaExcecao):
        recusas.registrar([_recusa("x", slug="the-godfather")])
    assert len(recusas.registrar([_recusa("r1")])) == 1
    assert recusas.registrar([_recusa("r1")]) == []
    assert recusas.ids_recusados(SLUG) == {"r1"}
    assert recusas.ids_recusados("cure") == frozenset()


def test_anotar_substitutas_pareia_por_bucket_e_declara_reserva_esgotada():
    recusas.registrar([_recusa("r1"), _recusa("r2"), _recusa("p1", "positivas")])
    resumo = recusas.anotar_substitutas(
        SLUG,
        antes={"negativas": {"r1", "r2", "k"}, "positivas": {"p1", "q"}},
        depois={"negativas": {"s1", "s2", "k"}, "positivas": {"q"}})
    subs = {r["id"]: r["substituta"] for r in recusas.recusas()}
    assert subs == {"r1": "s1", "r2": "s2", "p1": "RESERVA_ESGOTADA"}
    assert resumo["positivas"]["n_depois"] == 1


# --- detecção e pendência (votacao_3) -----------------------------------------

@pytest.fixture
def passes(tmp_path, monkeypatch):
    import votacao_3 as v3
    arqs = {n: tmp_path / f"passe_{n}.jsonl" for n in (1, 2, 3, 4)}
    monkeypatch.setattr(v3, "ARQ_PASSE", arqs)

    def gravar(n, regs):
        with arqs[n].open("a", encoding="utf-8") as f:
            for r in regs:
                f.write(json.dumps(r) + "\n")
    return v3, gravar


def _reg(rid, ok, bloqueio=None, passe=1):
    r = {"ok": ok, "slug": SLUG, "bucket": "negativas", "id": rid,
         "passe": passe, "excecao": C22.EXCECAO, "provider": "gemini",
         "modelo": "gemini-3.7-flash"}
    if bloqueio:
        r["bloqueio"] = bloqueio
    if ok:
        r["eixos"] = ["atuacao"]
    return r


def test_deteccao_exige_duas_tentativas_bloqueadas_e_nenhuma_ok(passes):
    v3, gravar = passes
    gravar(1, [_reg("a", False, "PROHIBITED_CONTENT"),
               _reg("b", False, "PROHIBITED_CONTENT"),
               _reg("c", False, "PROHIBITED_CONTENT"),
               _reg("d", False)])                         # falha sem bloqueio
    gravar(2, [_reg("a", False, "PROHIBITED_CONTENT", 2),
               _reg("c", True, passe=2),                  # uma ok: não é recusa
               _reg("d", False, passe=2)])
    det = v3.recusas_detectadas([SLUG])
    assert [d["id"] for d in det] == ["a"]
    assert det[0]["bloqueio"] == "PROHIBITED_CONTENT"
    assert det[0]["n_tentativas_bloqueadas"] == 2


def test_a_recusada_nao_e_mais_pendente_nem_incompleta(passes, tmp_path, monkeypatch):
    v3, _ = passes
    tid = v3.taxonomia_id()
    amostra = {"taxonomia_id": tid, "filmes": [{"slug": SLUG}],
               "reviews": [{"slug": SLUG, "bucket": "negativas", "id": i,
                            "perfil": "x", "nivel": 1.0, "n_chars": 10,
                            "texto": "t"} for i in ("a", "b")]}
    arq = tmp_path / "amostra.json"
    arq.write_text(json.dumps(amostra), encoding="utf-8")
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", arq)
    recusas.registrar([_recusa("a")])
    _, _, pend = v3.pendentes_do_passe(1, [SLUG])
    assert [r["id"] for r in pend] == ["b"]
    _, n_incompletas = v3.consenso_incremental([], [{}, {}, {}], amostra, [SLUG])
    assert n_incompletas == 1


def test_consenso_deepseek_arquivado_e_indeterminado_sem_maioria(tmp_path, monkeypatch):
    """A medida do custo do filtro (`proveniencia_classificacao --recusas`) usa
    os votos DeepSeek ARQUIVADOS: 3 passes → maioria; 2 passes iguais → eles;
    2 passes diferentes ou 1 só → indeterminado (nunca chute)."""
    import proveniencia_classificacao as PC
    monkeypatch.setattr(PC, "ARQUIVO_DS", tmp_path)
    votos = {1: {"a": ["x", "y"], "b": ["x"], "c": ["x"], "d": ["x"]},
             2: {"a": ["x"], "b": ["x"], "c": ["y"]},
             3: {"a": ["y"]}}
    for n, por_id in votos.items():
        (tmp_path / f"passe_{n}.jsonl").write_text("".join(
            json.dumps({"ok": True, "slug": SLUG, "id": i, "eixos": e}) + "\n"
            for i, e in por_id.items()), encoding="utf-8")
    c = PC._consenso_arquivado({"a", "b", "c", "d"}, SLUG)
    assert c == {"a": ["x", "y"], "b": ["x"], "c": None, "d": None}


def test_aceite_do_dono_libera_so_o_bucket_aceito_e_a_declaracao_o_diz():
    recusas.registrar([_recusa("r1"), _recusa("p1", "positivas")])
    recusas.anotar_substitutas(SLUG, {"negativas": {"r1"}, "positivas": {"p1"}},
                               {"negativas": set(), "positivas": {"s"}})
    assert [r["id"] for r in recusas.reservas_esgotadas([SLUG])] == ["r1"]
    with pytest.raises(ValueError):
        recusas.aceitar_n_menor(SLUG, "positivas", "x")   # teve substituta
    recusas.aceitar_n_menor(SLUG, "negativas", "publicar com n menor")
    assert recusas.reservas_esgotadas([SLUG]) == []
    assert len(recusas.reservas_esgotadas([SLUG], incluir_aceitas=True)) == 1
    d = recusas.declaracao_do_bucket(SLUG, "negativas")
    assert d["n_recusadas"] == 1 and d["substituidas"] == []
    assert d["sem_substituta"][0]["aceite_do_dono"] == "publicar com n menor"
    assert "PROHIBITED_CONTENT" in d["motivo"]
    p = recusas.declaracao_do_bucket(SLUG, "positivas")
    assert p["substituidas"] == [{"recusada": "p1", "substituta": "s"}]
    assert recusas.declaracao_do_bucket(SLUG, "medianas") is None


@pytest.mark.parametrize("texto,esperado", [
    ("Вообще не понравилось. Фильм долгим и скучным", "cirilico"),
    ("Hola soy la villana de esta peli y odio a batman por eso me lo voy", "es"),
    ("J'en ai un peu marre des films qui sont bien mais pas pour moi", "fr"),
    ("Sidney necə yoxluqdadısa bu bir çox amma film deyə olur", "az"),
    ("the movie was not good and this is it", "en"),
    ("ok", "indeterminado"),
])
def test_idioma_provavel_heuristica(texto, esperado):
    assert recusas.idioma_provavel(texto) == esperado
