"""[2026-11-04] Fase 4: τ do M2 (DESVIO_P03), cegueira do dono e M2, com dados SINTÉTICOS.

- o τ é o percentil 95 de D₀ pelo posto mais próximo, arredondado para cima na
  3ª casa; D₀ junta só filmes diferentes, D₁ só o mesmo filme;
- no lado treinado a tela recebe só o progresso e o resto vai para o log; nos
  outros lados nada muda; o que o juiz imprime dentro de `silenciar` não chega
  à tela;
- o C1–C4 da Fase 4 vai para `fase4/cego/`;
- o M2 agrega pela razão das somas e ignora bucket sem temas."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

# os módulos importam `_guarda`, que troca `load_dotenv` e o socket do processo; os
# originais voltam logo depois do import (ver test_avaliar_c1_c4.py)
import socket  # noqa: E402

import dotenv  # noqa: E402

_ORIGINAIS = (dotenv.load_dotenv, socket.socket.connect, socket.create_connection)
import _cego  # noqa: E402
import avaliar_c1_c4 as A  # noqa: E402
import fase4_m2 as M2  # noqa: E402
import tau_m2 as T  # noqa: E402

dotenv.load_dotenv, socket.socket.connect, socket.create_connection = _ORIGINAIS


def test_percentil_pelo_posto_mais_proximo_e_arredondamento_para_cima():
    vals = [i / 100 for i in range(1, 101)]                # 0,01 … 1,00
    assert T.percentil_posto(vals) == 0.95                 # posição ⌈0,95·100⌉ = 95
    assert T.percentil_posto([0.3, 0.1, 0.2]) == 0.3       # ⌈2,85⌉ = 3
    assert T.arredondar_para_cima(0.9626188) == 0.963
    assert T.arredondar_para_cima(0.962) == 0.962
    assert T.arredondar_para_cima(0.9620001) == 0.963


def test_d0_so_filmes_diferentes_e_d1_so_o_mesmo():
    slugs = ["a", "b", "c"]
    base = {(s, b): [{"slug": s}] for s in slugs for b in T.K.BUCKETS}
    pub = {(s, b): [{"slug": s}] for s in slugs for b in T.K.BUCKETS}
    parear = lambda ta, tb: [(0, 0, 1.0 if ta[0]["slug"] == tb[0]["slug"] else 0.5)]
    d0, d1 = T.distribuicoes(base, pub, slugs, parear)
    assert len(d0) == 3 * 3 * 2 and set(d0) == {0.5}
    assert len(d1) == 3 * 3 and set(d1) == {1.0}


def test_cego_no_treinado_tela_so_com_progresso(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(_cego, "PASTA", tmp_path)
    out = _cego.Saida("treinado", "x.log")
    out("sem_apoio 3 · apoio_2 10", curto="[1/30] filme · 2 min")
    with out.silenciar():
        print("juiz v2: 12 feitos · 4 pendentes")
    tela = capsys.readouterr().out
    assert tela == "[1/30] filme · 2 min\n"
    log = (tmp_path / "x.log").read_text(encoding="utf-8")
    assert "sem_apoio 3" in log and "4 pendentes" in log


def test_fora_do_treinado_nada_muda(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(_cego, "PASTA", tmp_path)
    out = _cego.Saida("base", "x.log")
    out("sem_apoio 3", curto="progresso")
    with out.silenciar():
        print("juiz")
    assert capsys.readouterr().out == "sem_apoio 3\njuiz\n"
    assert not (tmp_path / "x.log").exists()


def test_c1_c4_da_fase4_fica_na_pasta_cega():
    assert A.ARQ_FASE4.parent == _cego.PASTA
    assert A.ARQ_FASE4.parent.name == "cego" and A.ARQ_FASE4.parent.parent.name == "fase4"
    assert M2.ARQ_M2.parent == _cego.PASTA


def _t(m, n=10):
    return {"tema": "t", "exemplo_parafraseado": "e", "mencoes_aproximadas": m,
            "n_reviews_analisadas": n}


def test_m2_razao_das_somas_e_bucket_sem_temas():
    um_a_um = lambda tl, tp: [(i, i, 0.99) for i in range(min(len(tl), len(tp)))]
    ls = [M2.linha_do_bucket("f1", "negativas", [_t(4), _t(2)], [_t(5), _t(2)], um_a_um),
          M2.linha_do_bucket("f2", "negativas", [_t(1)], [_t(4), _t(3)], um_a_um),
          M2.linha_do_bucket("f2", "medianas", [], [_t(4)], um_a_um)]
    r = M2.resumo(ls, ["f1", "f2"], [["f1", "f2"], ["f1", "f1"]])
    assert r["buckets_comparaveis"] == 2 and r["buckets_sem_temas"] == 1
    assert r["pares"] == 3 and r["temas_publicado"] == 4
    assert r["taxa_pareamento"] == 3 / 4
    assert r["dam"] == (1 + 0 + 3) / 3
    assert abs(r["dam_relativa"] - 0.4 / 3) < 1e-12
    d = M2.diferenca_dam(ls, ls, ["f1", "f2"], [["f1", "f2"]])
    assert d["ponto"] == 0.0 and d["ic95"] == [0.0, 0.0]


def test_estrutura_impossivel_de_temas_e_json_invalido_no_gerar():
    import gerar_sintese_teste as G
    import pytest
    from espectro24 import synthesize as S
    assert G.parse_estrito('{"temas": [{"tema": "a"}], "observacao_geral": "x"}')["temas"]
    assert G.parse_estrito('{"observacao_geral": "x"}') == {"observacao_geral": "x"}
    for ruim in ('{"temas": [3, 5]}', '{"temas": "abc"}', '{"temas": {"a": 1}}', '[1, 2]'):
        with pytest.raises(ValueError):
            G.parse_estrito(ruim)
    # a produção estoura exatamente neste caso; o estrito o trata como JSON inválido
    with pytest.raises(AttributeError):
        S._construir_temas(S._parse_llm_json('{"temas": [3, 5]}'), 10)
