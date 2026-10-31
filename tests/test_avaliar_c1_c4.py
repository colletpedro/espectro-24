"""[2026-10-31] C1–C4 (`avaliar_c1_c4.py`) pelo pré-registro, com dados SINTÉTICOS.

- o juiz para no 2º "sim"; par fora da janela é pulado; bullet sem par
  julgável é indeterminado (fora do denominador);
- bucket fora por memória em QUALQUER lado gerado sai de todos os lados;
- o reaproveitamento compara as linhas no formato e na ordem da entrada antiga;
- bootstrap por filme reprodutível pela semente; os limiares de C1–C4 e a
  fórmula do δ₂ são os pré-registrados."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import avaliar_c1_c4 as A  # noqa: E402


def _par(b, rank, julgavel=True, slug="f1", bucket="positivas"):
    return {"id_par": f"{b}|r{rank}", "id_bullet": b, "rank": rank, "julgavel_estimado": julgavel,
            "slug": slug, "bucket": bucket, "texto": "x"}


def _apoio_de(veredito):
    """`veredito`: id_par → True/False (sem chave = sem veredito)."""
    return lambda reg, par: veredito.get(par["id_par"])


def test_parada_no_segundo_sim_e_estados():
    ps = [_par("b", r) for r in range(1, 6)]
    v = {"b|r1": True, "b|r2": False, "b|r3": True}
    e = A.estado_do_bullet(ps, {}, _apoio_de(v))
    assert e["estado"] == "apoio_2" and e["julgados"] == 3 and e["proximo"] is None
    e = A.estado_do_bullet(ps, {}, _apoio_de({"b|r1": True, "b|r2": False}))
    assert e["estado"] == "pendente" and e["proximo"]["rank"] == 3
    todos_nao = {f"b|r{r}": False for r in range(1, 6)}
    assert A.estado_do_bullet(ps, {}, _apoio_de(todos_nao))["estado"] == "sem_apoio"
    um = {**todos_nao, "b|r4": True}
    assert A.estado_do_bullet(ps, {}, _apoio_de(um))["estado"] == "apoio_1"
    # par fora da janela é pulado; nenhum julgável = indeterminado
    ps2 = [_par("c", 1, julgavel=False), _par("c", 2)]
    e = A.estado_do_bullet(ps2, {}, _apoio_de({"c|r2": False}))
    assert e["estado"] == "sem_apoio" and e["pulados"] == 1
    ps3 = [_par("d", r, julgavel=False) for r in range(1, 6)]
    assert A.estado_do_bullet(ps3, {}, _apoio_de({}))["estado"] == "indeterminado"


def test_bucket_fora_por_memoria_sai_de_todos_os_lados():
    pares = [("f1", "positivas"), ("f1", "negativas"), ("f2", "positivas")]
    regs = {"base": {("f1", "positivas"): {"ok": True}, ("f1", "negativas"): {"ok": True},
                     ("f2", "positivas"): {"fora_por_memoria": True}},
            "treinado": {("f1", "positivas"): {"ok": True},
                         ("f1", "negativas"): {"fora_por_memoria": True},
                         ("f2", "positivas"): {"ok": True}}}
    mantidos, fora = A.buckets_mantidos(pares, regs)
    assert mantidos == [("f1", "positivas")]
    assert fora == [("f1", "negativas"), ("f2", "positivas")]
    # o publicado é contado só nos mantidos: o bullet sem apoio do bucket fora não entra
    est = {"p1": {"estado": "apoio_2", "slug": "f1", "bucket": "positivas"},
           "p2": {"estado": "sem_apoio", "slug": "f2", "bucket": "positivas"}}
    est = {k: e for k, e in est.items() if (e["slug"], e["bucket"]) in set(mantidos)}
    pf = A.por_filme(est, {}, None)
    assert A.taxa(pf, ["f1", "f2"], "sem_apoio") == 0.0


def test_linhas_no_formato_e_na_ordem_da_entrada_antiga():
    base = {"lado": "publicado", "i": 0, "tema": "t", "exemplo": "e", "nivel": 4.0,
            "texto": "r", "rank": 1, "sim": 0.5, "score": 0.1, "julgavel_estimado": True}
    pares = [{**base, "id_par": "publicado|incendies|positivas|0|v2",
              "id_bullet": "publicado|incendies|positivas|0", "slug": "incendies",
              "bucket": "positivas", "review_id": "v2"},
             {**base, "id_par": "publicado|incendies|negativas|0|v9",
              "id_bullet": "publicado|incendies|negativas|0", "slug": "incendies",
              "bucket": "negativas", "review_id": "v9"},
             {**base, "id_par": "publicado|outro|negativas|0|v1", "id_bullet": "x",
              "slug": "outro", "bucket": "negativas", "review_id": "v1"}]
    linhas = A.linhas_formato_antigo(pares, {"publicado|incendies|negativas|0": {"v9"}})
    assert len(linhas) == 2                                   # só os 5 de referência
    d = [json.loads(l) for l in linhas]
    assert [x["bucket"] for x in d] == ["negativas", "positivas"]
    assert list(d[0]) == list(A.CAMPOS_ENTRADA_ANTIGA)
    assert d[0]["review_tem_eixo"] is True and d[1]["review_tem_eixo"] is False
    assert A.sha_das_linhas(linhas) == A.K.sha256_texto(linhas[0] + "\n" + linhas[1] + "\n")


def _pf(sem_apoio, apoio_2, m1_k, c4_ok=3, n=18, filmes=("a", "b", "c", "d")):
    return {f: {"julgados": n, "sem_apoio": sem_apoio, "apoio_2": apoio_2, "m1_n": n,
                "m1_k": m1_k, "c4_ok": c4_ok, "buckets": 3} for f in filmes}


def test_criterios_nos_limiares_pre_registrados():
    filmes = ["a", "b", "c", "d"]
    boot = A.reamostras(filmes, n=200)
    assert boot == A.reamostras(filmes, n=200)
    p = _pf(0, 15, 9)
    igual = A.criterios(_pf(0, 15, 9), p, filmes, boot, 8.0, 12)
    assert igual["C1"]["passa"] and igual["C2"]["passa"] and igual["C3"]["passa"]
    assert igual["C4"]["piso"] == 87 - (89 - 12)
    # +5,6 pp de sem apoio: estimativa pontual acima de +2,0 → C1 reprova
    pior = A.criterios(_pf(1, 15, 9), p, filmes, boot, 8.0, 12)
    assert pior["C1"]["ponto_pp"] > A.C1_PONTUAL_PP and not pior["C1"]["passa"]
    # menos palavras de quantidade não reprova o C3 (um lado só)
    assert A.criterios(_pf(0, 15, 0), p, filmes, boot, 8.0, 12)["C3"]["passa"]
    # queda grande de apoio ≥ 2 reprova o C2
    assert not A.criterios(_pf(0, 5, 9), p, filmes, boot, 8.0, 12)["C2"]["passa"]


def test_delta2_pela_formula_registrada():
    assert [A.delta2_pp(p) for p in (0.80, 0.85, 0.90)] == [8.6, 7.9, 6.8]


def test_c4_exige_json_e_validadores():
    temas = [{"tema": "Fotografia elogiada", "mencoes_aproximadas": 4, "n_reviews_analisadas": 5,
              "exemplo_parafraseado": "Muitas críticas elogiam a fotografia e o uso das cores."},
             {"tema": "Trilha sonora marcante", "mencoes_aproximadas": 2,
              "n_reviews_analisadas": 5,
              "exemplo_parafraseado": "Algumas reviews destacam a trilha sonora do filme."}]
    bp = {"temas": temas, "n_validas": 5, "json_parseia": True,
          "observacao_geral": "Este grupo de reviews elogia a fotografia e a trilha sonora.",
          "idioma_invalido": False, "escopo_suspeito": False}
    assert A.c4_do_bucket(bp)
    assert not A.c4_do_bucket({**bp, "json_parseia": False})
    assert not A.c4_do_bucket({**bp, "temas": list(reversed(temas))})       # ordem decrescente
