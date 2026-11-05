"""[2026-11-05] Avaliação de produção do treinado no C22 (`scripts/finetune/c22.py`),
pelo `finetune/PREREGISTRO_C22.md`: escopo, entrada congelada, guarda dentro da
geração, critérios absolutos com IC por filme, C6, trava do pré-registro."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import c22 as X  # noqa: E402
import comum as K  # noqa: E402
from espectro24.models import BucketResult, LevelResult, Review  # noqa: E402


def _bucket(n=6, nome="medianas"):
    lvl = LevelResult(3.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"viewing:{i}", rating=3.5, text=f"review {i} completa",
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text=f"review {i} completa com mais texto") for i in range(n)]
    return BucketResult(nome=nome, alvo=40, modo="completo", niveis=[lvl])


# --- escopo -------------------------------------------------------------------

META = {"ano_lancamento": 2019, "identidade_letterboxd": {"titulo": "1917", "ano": 2019,
                                                          "tmdb_id_letterboxd": 530915}}


def _ok(*_):
    return None


def _recusa(*_):
    raise ValueError("a amostra analisada diverge da classificada — publicar encolheria o "
                     "denominador em silêncio. positivas: 1 de 40 analisadas sem classificação (x). "
                     "Causas conhecidas: ...")


@pytest.mark.parametrize("args,estado", [
    (("1917", False, False, {"a": 1}, {"a": {"x"}}, META, _ok), "incluido"),
    (("1917", True, False, {"a": 1}, {}, META, _ok), "ja_publicado"),
    (("1917", False, True, {"a": 1}, {}, META, _ok), "ja_publicado"),
    (("1917", False, False, None, {}, META, _ok), "excluido"),           # sem classificação
    (("1917", False, False, {"a": 1}, {}, META, _recusa), "excluido"),   # C14.8
    (("1917", False, False, {"a": 1}, {}, {**META, "identidade_letterboxd": {}}, _ok), "excluido"),
    (("scarface-1983", False, False, {"a": 1}, {}, {**META, "ano_lancamento": 1983}, _ok), "excluido"),
])
def test_decidir_filme(args, estado):
    e, motivo = X.decidir_filme(*args)
    assert e == estado
    assert (motivo == "") == (estado == "incluido")


def test_motivo_da_c14_8_nomeia_a_pendencia():
    _, motivo = X.decidir_filme("f", False, False, {"a": 1}, {}, META, _recusa)
    assert "C14.8" in motivo and "positivas" in motivo


# --- entrada congelada --------------------------------------------------------

def test_entrada_congelada_reproduz_o_prompt():
    b = _bucket()
    d = json.loads(json.dumps(X.entrada_do_bucket("f", b)))      # passa pelo JSON, como no disco
    s, u = K.prompt_sintese(b)
    assert K.prompt_sintese(X.bucket_da_entrada(d)) == (s, u)
    assert X.bucket_da_entrada(d).n_validas == 6 and X.bucket_da_entrada(d).nome == "medianas"


# --- a guarda dentro da geração -------------------------------------------------

def _resposta(exemplos):
    return json.dumps({"bucket": "medianas",
                       "temas": [{"tema": f"t{i}", "mencoes_aproximadas": 5 - i,
                                  "n_reviews_analisadas": 6, "exemplo_parafraseado": e}
                                 for i, e in enumerate(exemplos)],
                       "observacao_geral": "Este grupo tem opiniões mistas."}, ensure_ascii=False)


def test_executar_par_aplica_a_guarda_e_nao_perde_bullet():
    exemplos = ["Muitas reviews medianas elogiam a trilha.", "A fotografia é frequentemente citada.",
                "Poucos gostaram do final."]

    def chamar(system, user, **kw):
        return {"texto": _resposta(exemplos), "latencia_s": 1.0}

    reg, tent = X.executar_par(_bucket(), "modelo-x", 8192, chamar)
    temas = reg["bucket_final"]["temas"]
    assert reg["ok"] and reg["json_parseia"] and len(tent) == 1
    assert len(temas) == 3                                         # ninguém some
    assert [t["tema"] for t in temas] == ["t0", "t1", "t2"]         # mesma ordem
    assert temas[0]["exemplo_parafraseado"] == "Reviews medianas elogiam a trilha."
    assert temas[0]["quantidade_reescrita"] and temas[0]["exemplo_antes_da_guarda"] == exemplos[0]
    assert temas[1]["exemplo_parafraseado"] == "A fotografia é citada."
    assert temas[2]["quantidade_pendente"] and temas[2]["exemplo_parafraseado"] == exemplos[2]
    assert tent[0]["texto"] == _resposta(exemplos)                  # a resposta crua fica gravada


# --- critérios absolutos ---------------------------------------------------------

def _pf(n_filmes=30, sem_apoio=2, julgados=20, apoio2=18, m1_k=1, m1_n=18):
    return {f"f{i}": {"julgados": julgados, "sem_apoio": sem_apoio, "apoio_2": apoio2,
                      "m1_k": m1_k, "m1_n": m1_n, "buckets": 3, "c4_ok": 3}
            for i in range(n_filmes)}


def test_criterios_passam_com_dados_bons():
    pf = _pf(sem_apoio=0, apoio2=19, m1_k=0)
    filmes = sorted(pf)
    boot = X.A.reamostras(filmes, 200, 1)
    r = X.criterios_absolutos(pf, filmes, boot, 90)
    assert r["C1"]["passa"] and r["C2"]["passa"] and r["C3"]["passa"] and r["C4"]["passa"]
    assert r["C1_a_C4_passam"]


def test_cada_criterio_reprova_sozinho():
    filmes = sorted(_pf())
    boot = X.A.reamostras(filmes, 200, 1)
    assert not X.criterios_absolutos(_pf(sem_apoio=3), filmes, boot, 90)["C1"]["passa"]     # 15% sem apoio
    assert not X.criterios_absolutos(_pf(apoio2=14), filmes, boot, 90)["C2"]["passa"]       # 70% com apoio ≥ 2
    assert not X.criterios_absolutos(_pf(m1_k=4), filmes, boot, 90)["C3"]["passa"]          # 22% de M1
    assert not X.criterios_absolutos({**_pf(), "f0": {**_pf()["f0"], "c4_ok": 0}} | {
        f"f{i}": {**_pf()[f"f{i}"], "c4_ok": 2} for i in range(1, 30)}, filmes, boot, 90)["C4"]["passa"]


def test_c1_exige_o_ponto_e_o_limite_superior():
    # 5% de sem apoio por filme: o ponto passa (5 ≤ 5,6) mas o IC de um conjunto pequeno estoura 7,6
    pf = {f"f{i}": {"julgados": 20, "sem_apoio": 2 if i % 2 == 0 else 0, "apoio_2": 19,
                    "m1_k": 0, "m1_n": 10, "buckets": 3, "c4_ok": 3} for i in range(8)}
    filmes = sorted(pf)
    boot = X.A.reamostras(filmes, 2000, 1)
    r = X.criterios_absolutos(pf, filmes, boot, 24)["C1"]
    assert r["ponto_pct"] == pytest.approx(5.0) and r["ic95_pct"][1] >= 7.6 and not r["passa"]


def test_c4_piso_e_97_por_cento_dos_validos():
    assert X.criterios_absolutos(_pf(), sorted(_pf()), X.A.reamostras(sorted(_pf()), 50, 1), 105)["C4"]["piso"] == 102
    assert X.criterios_absolutos(_pf(), sorted(_pf()), X.A.reamostras(sorted(_pf()), 50, 1), 100)["C4"]["piso"] == 97


# --- C6 -----------------------------------------------------------------------------

def test_sorteio_do_c6_e_deterministico_e_sem_repeticao():
    filmes = [f"filme-{i:02d}" for i in range(35)]
    a, b = X.sortear_c6(filmes), X.sortear_c6(list(reversed(filmes)))
    assert a == b and len(set(a)) == 5 and set(a) <= set(filmes)


def test_avaliar_c6():
    filmes = ["a", "b", "c", "d", "e"]
    resp = lambda v: [{"filme": str(i + 1), "publicavel": x} for i, x in enumerate(v)]
    assert X.avaliar_c6(filmes, resp("SSSSN"))["C6_passa"]
    assert not X.avaliar_c6(filmes, resp("SSSNN"))["C6_passa"]
    with pytest.raises(SystemExit):
        X.avaliar_c6(filmes, resp("SSSSX"))


def test_documento_do_c6_traz_so_os_bullets():
    escopo = {"incluidos": [{"slug": "f", "titulo": "Filme", "ano": 2000}]}
    b = {"temas": [{"tema": "Ritmo", "exemplo_parafraseado": "Reviews acham lento.",
                    "mencoes_aproximadas": 7}], "observacao_geral": "NAO DEVE APARECER"}
    doc = X.documento_c6(escopo, ["f"], {("f", k): b for k in K.BUCKETS}, "selo")
    assert "**Ritmo** — Reviews acham lento." in doc
    assert "NAO DEVE APARECER" not in doc and "mencoes" not in doc and "7" not in doc.split("Selo")[0].split("---")[2]


# --- a trava do pré-registro ---------------------------------------------------------

def _repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    return tmp_path


def test_gerar_recusa_sem_preregistro_commitado(tmp_path):
    repo = _repo(tmp_path)
    arq = repo / "PREREGISTRO_C22.md"
    with pytest.raises(SystemExit, match="sem PREREGISTRO"):
        X.exigir_preregistro(arq, repo / "e.json", repo / "p.json")
    arq.write_text("x\n")
    with pytest.raises(SystemExit, match="não está commitado"):
        X.exigir_preregistro(arq, repo / "e.json", repo / "p.json")
    subprocess.run(["git", "-C", str(repo), "add", arq.name], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "x"], check=True)
    arq.write_text("y\n")
    with pytest.raises(SystemExit, match="difere do commitado"):
        X.exigir_preregistro(arq, repo / "e.json", repo / "p.json")


def test_gerar_recusa_com_fluencia_reprovada_ou_ausente(tmp_path):
    with pytest.raises(SystemExit, match="sem fluencia_resultado"):
        X.exigir_fluencia(tmp_path / "nao.json")
    f = tmp_path / "f.json"
    f.write_text(json.dumps({"passa": False, "S": 25}))
    with pytest.raises(SystemExit, match="REPROVOU"):
        X.exigir_fluencia(f)
    f.write_text(json.dumps({"passa": True, "S": 28}))
    assert X.exigir_fluencia(f)["S"] == 28
