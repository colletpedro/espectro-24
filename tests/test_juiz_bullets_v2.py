"""[2026-10-19] Juiz v2 da checagem de apoio dos bullets (`scripts/juiz_bullets_v2.py`):
outro modelo que não o autor do lado local, a frase de prova conferida pelo
CÓDIGO (o modelo não tem a palavra final), o critério do dono no prompt, a
configuração inteira num hash, o contexto que cabe no maior par, e a
calibração nos 40 pares antigos que se declara calibração — não validação."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))

import checagem_bullets as C  # noqa: E402
import juiz_bullets_v2 as J  # noqa: E402
from test_checagem_bullets import _csv, _entrada, _hash_publicados, _montar_dir  # noqa: E402

PUB = RAIZ / "resultado"

REVIEW = "Great acting,  but the STORY sucked.\nJ’ai adoré la fin — très émouvante."


# ---------------------------------------------------------------------------
# Modelo e configuração
# ---------------------------------------------------------------------------

def test_modelo_nao_e_o_que_escreveu_o_lado_local():
    assert J.MODELO == "gpt-oss:20b" and J.THINK == "low"
    assert J.MODELO.split(":")[0] not in C.AUTOR["local"]


def test_no_maximo_dois_ajustes_e_versao_atual_existe():
    assert len(J.VERSOES) <= J.MAX_VERSOES == 3
    assert J.VERSAO_ATUAL in J.VERSOES and list(J.VERSOES)[0] == "v2.0"
    assert J.CONGELADA is None or J.CONGELADA in J.VERSOES


def test_hash_cobre_prompt_modelo_parametros_e_regra(monkeypatch):
    base = J.config_sha256()
    assert base == J.config_sha256()
    for nome, valor in (("NUM_CTX", 4096), ("NUM_PREDICT", 512), ("SEED", 1),
                        ("THINK", "medium"), ("MODELO", "outro:1b")):
        with monkeypatch.context() as m:
            m.setattr(J, nome, valor)
            assert J.config_sha256() != base, nome
    with monkeypatch.context() as m:
        m.setitem(J.VERSOES, "v2.0", {**J.VERSOES["v2.0"], "system": "outro"})
        assert J.config_sha256() != base
    cfg = J.config()
    assert {"system", "user_template", "schema", "regra_sha256", "temperatura"} <= set(cfg)


def test_criterio_do_dono_esta_no_prompt_inteiro():
    s = J.system()
    assert J.CRITERIO_DONO in s
    for trecho in ("NO MESMO SENTIDO", "implícito", "outra língua", "juízo oposto",
                   "atribui a opinião a outros e discorda", "ambivalente demais",
                   "NÚCLEO do bullet, que é o título", "parte lateral", "Na dúvida, NÃO",
                   "Não julgue se o bullet é verdadeiro", "ESTA review"):
        assert trecho in s, trecho
    assert "LITERALMENTE" in s and "língua original da review" in s
    assert J.SCHEMA["required"] == ["trecho", "apoia"]
    assert J.SCHEMA["properties"]["trecho"]["type"] == ["string", "null"]


def test_mensagem_review_primeiro_titulo_e_descricao_por_ultimo():
    _, pares = _entrada()
    u = J.user(pares[0])
    assert u.startswith("Review (nota 1.5 de 5 estrelas):\n\ntexto r1")
    assert u.index("texto r1") < u.index("título (o núcleo)") < u.index("descrição")


# ---------------------------------------------------------------------------
# Frase de prova — a regra é do código
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("trecho", ["great acting, but the story sucked.",
                                    "GREAT   ACTING,\tbut the story",
                                    "  j’ai adoré la fin  ", "très émouvante"])
def test_trecho_encontrado_so_normaliza_espaco_e_caixa(trecho):
    assert J.trecho_encontrado(trecho, REVIEW)


@pytest.mark.parametrize("trecho", [None, "", "   ", "tres emouvante",          # sem acento
                                    "J'ai adoré la fin",                         # outra aspa
                                    "Ótima atuação",                              # traduzido
                                    "Great acting... the STORY sucked"])        # juntado
def test_trecho_que_nao_e_literal_nao_e_encontrado(trecho):
    assert not J.trecho_encontrado(trecho, REVIEW)


def test_trecho_com_forma_unicode_diferente_e_o_mesmo_texto():
    decomposto = "très émouvante"           # è e é decompostos
    assert J.trecho_encontrado(decomposto, REVIEW)


@pytest.mark.parametrize("apoia,trecho,esperado", [
    (True, "Great acting", True),
    (True, None, False),                 # disse que apoia sem prova
    (True, "Ótima atuação", False),      # prova que não está na review
    (False, "Great acting", False),      # prova sem o sim
    (False, None, False)])
def test_apoio_final_e_a_conjuncao_das_tres(apoia, trecho, esperado):
    assert J.apoio_final(apoia, trecho, REVIEW) is esperado


@pytest.mark.parametrize("texto", ['{"apoia": true}', '{"trecho": null}',
                                   '{"trecho": "x", "apoia": "sim"}',
                                   '{"trecho": 3, "apoia": true}',
                                   '{"trecho": null, "apoia": false, "x": 1}', "[]", "sim"])
def test_resposta_fora_do_formato_e_falha(texto):
    with pytest.raises(Exception):
        J.ler_resposta(texto)


def test_resposta_no_formato():
    assert J.ler_resposta('{"trecho": null, "apoia": false}') == {"trecho": None,
                                                                    "apoia": False}
    assert J.ler_resposta('{"trecho": "a b", "apoia": true}')["trecho"] == "a b"


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

def _par(id_par, n_chars, review_id=None):
    return {"id_par": id_par, "slug": "f", "review_id": review_id or id_par, "nivel": 3.0,
            "texto": "x" * n_chars, "tema": "t", "exemplo": "e"}


def test_contexto_estimado_cabe_o_maior_par_mais_a_saida():
    pares = [_par("a", 100), _par("b", 4990), _par("c", 3000)]
    est = J.estimar_contexto(pares)
    assert est["maior_id_par"] == "b"
    assert est["cota_tokens_prompt"] == pytest.approx(0.35 * J.chars_do_prompt(pares[1]), abs=1)
    assert est["precisa"] == est["cota_tokens_prompt"] + J.NUM_PREDICT
    assert est["menor_multiplo_512"] % 512 == 0
    assert est["menor_multiplo_512"] - 512 < est["precisa"] <= est["menor_multiplo_512"]


def test_num_ctx_e_o_menor_multiplo_de_512_para_o_maior_par_real():
    # O maior par dos 900 (gate-local): review de 4.990 caracteres.
    est = J.estimar_contexto([_par("maior", 4990)])
    assert J.NUM_CTX == est["menor_multiplo_512"] == 3584


def test_maiores_pares_uma_review_por_vez():
    pares = [_par("a1", 5000, "A"), _par("a2", 4999, "A"), _par("b", 4000), _par("c", 10)]
    assert [p["id_par"] for p in J.maiores_pares(pares, n=2)] == ["a1", "b"]


def test_medicao_julga_com_a_saida_inteira():
    ok = J.julgar_medicao([{"prompt_eval_count": 2000}, {"prompt_eval_count": 2400}])
    assert ok["cabe"] and ok["precisa"] == 2400 + J.NUM_PREDICT
    assert ok["folga"] == J.NUM_CTX - ok["precisa"]
    ruim = J.julgar_medicao([{"prompt_eval_count": J.NUM_CTX - J.NUM_PREDICT + 1}])
    assert not ruim["cabe"]


def test_guarda_por_chamada_pega_prompt_que_encosta_na_janela():
    assert J.contexto_estoura({"prompt_eval_count": 2000, "eval_count": 300}) is None
    assert J.contexto_estoura({"prompt_eval_count": J.NUM_CTX - J.NUM_PREDICT + 1,
                               "eval_count": 5})
    assert J.contexto_estoura({"prompt_eval_count": 2500, "eval_count": J.NUM_CTX})


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def _resp(texto, **kw):
    r = {"texto": texto, "finish_reason": "stop", "modelo_efetivo": J.MODELO,
         "think": J.THINK, "latencia_s": 1.0, "prompt_eval_count": 500, "eval_count": 80,
         "custo_usd": 0.0, "pensamento": "a review elogia a atuação"}
    r.update(kw)
    return r


def test_juiz_retoma_e_registra_truncamento_e_estouro_como_falha(tmp_path):
    _, pares = _entrada()
    vistos, n = [], {"i": 0}

    def chamar(system, user):
        assert system == J.system()
        vistos.append(user)
        n["i"] += 1
        if n["i"] == 2:
            return _resp('{"trecho": "texto', finish_reason="length")
        if n["i"] == 3:
            return _resp('{"trecho": null, "apoia": false}', prompt_eval_count=J.NUM_CTX)
        if n["i"] == 4:
            raise RuntimeError("prazo")
        return _resp('{"trecho": "texto", "apoia": true}')

    saida = tmp_path / "s.jsonl"
    r = J.rodar(pares, saida, chamar, versao="v2.0")
    assert r["rodados"] == 8 and r["falhas"] == 3
    regs = C._ler_jsonl(saida)
    erros = [x["erro"] for x in regs if not x["ok"]]
    assert any("finish_reason='length'" in e for e in erros)
    assert any("contexto" in e for e in erros)
    assert any(e.startswith("RuntimeError") for e in erros)
    ok = [x for x in regs if x["ok"]]
    assert all(x["config_sha256"] == J.config_sha256() and x["pensamento"] for x in ok)
    r2 = J.rodar(pares, saida, chamar, versao="v2.0")
    assert r2["rodados"] == 3 and len(vistos) == 11
    ver = J.vereditos(pares, C._ler_jsonl(saida), "v2.0")
    assert len(ver) == 8 and all(v["apoio"] for v in ver.values())


def test_vereditos_recalculam_o_apoio_do_texto_e_nao_confiam_no_modelo():
    _, pares = _entrada()
    sha = J.config_sha256()
    base = {"ok": True, "config_sha256": sha, "modelo_efetivo": J.MODELO, "think": J.THINK}
    regs = [{**base, "id_par": p["id_par"], "apoia": True,
             "trecho": "texto r1" if p["review_id"] == "r1" else "texto r1"} for p in pares]
    ver = J.vereditos(pares, regs, "v2.0")
    for p in pares:
        v = ver[p["id_par"]]
        assert v["apoia_modelo"] is True
        # "texto r1" não está na review r2: o código derruba o sim do modelo
        assert v["apoio"] is (p["review_id"] == "r1") and v["trecho_encontrado"] is v["apoio"]


def test_vereditos_exigem_configuracao_modelo_think_e_todos_os_pares():
    _, pares = _entrada()
    base = {"ok": True, "config_sha256": J.config_sha256(), "modelo_efetivo": J.MODELO,
            "think": J.THINK, "apoia": False, "trecho": None}
    regs = [{**base, "id_par": p["id_par"]} for p in pares]
    with pytest.raises(ValueError, match="sem veredito"):
        J.vereditos(pares, regs[1:], "v2.0")
    for campo, valor, erro in (("config_sha256", "outra", "outra configuração"),
                               ("modelo_efetivo", "qwen3:14b", "juiz v2 é"),
                               ("think", "omitido", "juiz v2 é")):
        ruim = [dict(r) for r in regs]
        ruim[0][campo] = valor
        with pytest.raises(ValueError, match=erro):
            J.vereditos(pares, ruim, "v2.0")
    assert not any(v["apoio"] for v in J.vereditos(pares, regs, "v2.0").values())


def test_juiz_nao_escreve_em_resultado():
    with pytest.raises(SystemExit, match="RECUSADO"):
        J.rodar([], PUB / "x.jsonl", lambda s, u: {}, versao="v2.0")
    with pytest.raises(SystemExit, match="RECUSADO"):
        J.main(["calibrar", "--dir", str(PUB / "checagem")])


def test_chamador_fixa_modelo_think_seed_e_janela_no_codigo(monkeypatch):
    from espectro24 import local_ollama

    visto = {}
    monkeypatch.setattr(local_ollama, "resposta_json_local",
                        lambda s, u, **kw: visto.update(kw) or {})
    J._chamador(num_ctx=J.NUM_CTX, num_predict=J.NUM_PREDICT)("S", "U")
    assert visto == {"estagio": J.ESTAGIO, "modelo": J.MODELO, "schema": J.SCHEMA,
                     "num_predict": J.NUM_PREDICT, "num_ctx": J.NUM_CTX,
                     "think": J.THINK, "seed": J.SEED}


def test_juiz_recusa_temperatura_do_ambiente_e_rodar_sem_medicao(tmp_path, monkeypatch):
    monkeypatch.setenv(J.VAR_TEMPERATURA, "0")
    with pytest.raises(SystemExit, match="temperatura"):
        J.cmd_juiz(SimpleNamespace(dir=tmp_path, calibracao=True, todos=False))
    monkeypatch.delenv(J.VAR_TEMPERATURA)
    with pytest.raises(SystemExit, match="medir-contexto"):
        J.cmd_juiz(SimpleNamespace(dir=tmp_path, calibracao=True, todos=False))
    C._json(tmp_path / J.arq_contexto(J.VERSAO_ATUAL),
            {"config_sha256": "outra", "cabe": True})
    with pytest.raises(SystemExit, match="outra configuração"):
        J.cmd_juiz(SimpleNamespace(dir=tmp_path, calibracao=True, todos=False))


def test_os_900_so_rodam_com_a_versao_congelada(tmp_path, monkeypatch):
    C._json(tmp_path / J.arq_contexto(J.VERSAO_ATUAL),
            {"config_sha256": J.config_sha256(), "cabe": True})
    monkeypatch.setattr(J, "CONGELADA", None)
    with pytest.raises(SystemExit, match="CONGELADA"):
        J.cmd_juiz(SimpleNamespace(dir=tmp_path, calibracao=False, todos=True))


# ---------------------------------------------------------------------------
# Critério e calibração
# ---------------------------------------------------------------------------

def _m(vp, fp, fn, vn):
    return C.matriz([(True, True)] * vp + [(False, True)] * fp + [(True, False)] * fn
                    + [(False, False)] * vn)


def test_criterio_reprova_juiz_que_erra_mais_num_lado():
    # geral passa (P 0,84, R 1,0), mas um lado tem precisão 1,0 e o outro 0,684
    pub, loc = _m(12, 0, 0, 8), _m(13, 6, 0, 1)
    geral = _m(25, 6, 0, 9)
    j = J.julgar(geral, {"publicado": pub, "local": loc})
    assert geral["precisao"] >= 0.8 and not j["vale"]
    assert j["dif_precisao_lados"] == pytest.approx(0.316, abs=1e-3)
    assert any("entre os lados" in m for m in j["motivos"])
    ok = J.julgar(_m(25, 2, 1, 12), {"publicado": _m(12, 1, 1, 6), "local": _m(13, 1, 0, 6)})
    assert ok["vale"] and ok["dif_precisao_lados"] <= 0.15


def test_criterio_reprova_lado_sem_nenhum_sim():
    j = J.julgar(_m(10, 0, 0, 10), {"publicado": _m(10, 0, 0, 0), "local": _m(0, 0, 0, 10)})
    assert not j["vale"] and any("indefinida" in m for m in j["motivos"])


def test_calibracao_ponta_a_ponta_se_declara_calibracao(tmp_path):
    # v1 diz sim a tudo; v2: o modelo diz que apoia tudo, com prova só em r1
    d, pares, mapa = _montar_dir(tmp_path, lambda p: True)
    por = {p["id_par"]: p for p in pares}
    _csv(d / C.ARQ_ROTULOS, [(k, "sim" if por[v]["review_id"] == "r1" else "não")
                            for k, v in mapa["pares"].items()])
    base = {"ok": True, "config_sha256": J.config_sha256(), "modelo_efetivo": J.MODELO,
            "think": J.THINK, "apoia": True, "pensamento": "raciocínio"}
    C._escrever(d / J.DIR_V2 / "calibracao_v2.0_saida.jsonl", "".join(
        json.dumps({**base, "id_par": p["id_par"],
                    "trecho": "texto r1" if p["review_id"] == "r1" else "inventado"}) + "\n"
        for p in pares))
    J.cmd_calibrar(SimpleNamespace(dir=d, versao=None))
    cal = json.loads((d / J.DIR_V2 / "calibracao_v2.0.json").read_text())
    assert cal["geral"]["precisao"] == 1.0 and cal["geral"]["recall"] == 1.0
    assert cal["v1"]["geral"]["precisao"] == 0.5
    assert len(cal["derrubados_pelo_trecho"]) == 4 and not cal["erros"]
    md = (d / J.DIR_V2 / "calibracao_v2.0.md").read_text()
    assert md.splitlines()[2].startswith("> **CALIBRAÇÃO, NÃO VALIDAÇÃO.**")


def test_calibracao_lista_o_erro_com_trecho_e_raciocinio(tmp_path):
    d, pares, mapa = _montar_dir(tmp_path, lambda p: True)
    _csv(d / C.ARQ_ROTULOS, [(k, "não") for k in mapa["pares"]])
    base = {"ok": True, "config_sha256": J.config_sha256(), "modelo_efetivo": J.MODELO,
            "think": J.THINK, "apoia": True, "trecho": "texto", "pensamento": "PENSEI"}
    C._escrever(d / J.DIR_V2 / "calibracao_v2.0_saida.jsonl", "".join(
        json.dumps({**base, "id_par": p["id_par"]}) + "\n" for p in pares))
    J.cmd_calibrar(SimpleNamespace(dir=d, versao="v2.0"))
    md = (d / J.DIR_V2 / "calibracao_v2.0.md").read_text()
    assert "REPROVARIA" in md and "PENSEI" in md and '"texto"' in md
    assert "### P01" in md


def test_nada_disto_toca_os_publicados(tmp_path):
    antes = _hash_publicados()
    test_calibracao_ponta_a_ponta_se_declara_calibracao(tmp_path)
    assert _hash_publicados() == antes
