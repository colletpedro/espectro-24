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
TEXTO_LONGO = "Texto longo da review {rid} com prova suficiente."
TRECHO_R1 = "texto longo da review r1"            # 5 palavras, só na review r1


def _entrada_longa():
    """A entrada sintética com reviews de frases de verdade (a de
    `test_checagem_bullets` tem duas palavras por review)."""
    bl, pares = _entrada()
    return bl, [{**p, "texto": TEXTO_LONGO.format(rid=p["review_id"])} for p in pares]


def _alongar(d):
    """Reescreve a entrada de `_montar_dir` com os textos longos."""
    pares = [{**p, "texto": TEXTO_LONGO.format(rid=p["review_id"])}
             for p in C._ler_jsonl(d / C.ARQ_ENTRADA)]
    C._escrever(d / C.ARQ_ENTRADA, "".join(json.dumps(p) + "\n" for p in pares))
    return pares


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


def test_hash_da_v2_0_nao_muda_com_a_v2_1():
    # os 40 registros da v2.0 (gate-local) foram julgados com este hash; se
    # ele mudasse, a calibração da v2.0 deixaria de ser legível
    assert J.config_sha256("v2.0") == (
        "a42f48932713ff322535116cb17538bc51a14bdb5e49c9c8389c35b687461c22")
    assert J.config_sha256("v2.1") != J.config_sha256("v2.0")
    assert J.VERSAO_ATUAL == "v2.1"


def test_hash_cobre_prompt_modelo_parametros_e_regra(monkeypatch):
    base = J.config_sha256()
    assert base == J.config_sha256()
    for nome, valor in (("NUM_PREDICT", 512), ("SEED", 1),
                        ("THINK", "medium"), ("MODELO", "outro:1b"),
                        ("MIN_PALAVRAS_TRECHO", 3)):
        with monkeypatch.context() as m:
            m.setattr(J, nome, valor)
            assert J.config_sha256() != base, nome
    atual = J.VERSOES[J.VERSAO_ATUAL]
    for campo, valor in (("system", "outro"), ("num_ctx", 8192),
                         ("schema", J.SCHEMA), ("regra", atual["regra"][:-1]),
                         ("regra_dados", ["{}"])):
        with monkeypatch.context() as m:
            m.setitem(J.VERSOES, J.VERSAO_ATUAL, {**atual, campo: valor})
            assert J.config_sha256() != base, campo
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
    assert "FRASE INTEIRA" in s and "não um fragmento" in s
    assert f"menos de {J.MIN_PALAVRAS_TRECHO} palavras" in s and J.MIN_PALAVRAS_TRECHO == 4
    assert J.schema("v2.0")["required"] == ["trecho", "apoia"]
    assert J.schema("v2.1")["required"] == ["trecho", "ambiguo", "apoia"]
    assert J.schema()["properties"]["trecho"]["type"] == ["string", "null"]
    assert J.CRITERIO_DONO in J.system("v2.0")


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


@pytest.mark.parametrize("apoia,trecho,motivo", [
    (True, "Great acting,  but the STORY sucked.", None),
    (True, "J’ai adoré la fin", None),                        # 4 palavras: o mínimo
    (True, None, "trecho nulo"),                              # disse que apoia sem prova
    (True, "   ", "trecho nulo"),
    (True, "Great acting", "trecho curto (2 palavras < 4)"),
    (True, "acting,", "trecho curto (1 palavra < 4)"),
    (True, "Ótima atuação, mas a história é fraca.", "trecho não encontrado na review"),
    (False, "Great acting,  but the STORY sucked.", "modelo disse que não apoia"),
    (False, None, "modelo disse que não apoia")])
def test_apoio_final_exige_sim_trecho_de_4_palavras_e_achado(apoia, trecho, motivo):
    assert J.motivo_sem_apoio(apoia, trecho, REVIEW) == motivo
    assert J.apoio_final(apoia, trecho, REVIEW) is (motivo is None)


def test_great_acting_nao_prova_atuacoes_insuficientes():
    # O par real local|anatomy-of-a-fall|negativas|4 (bullet "atuações
    # insuficientes"): copiar "acting" ou "Great acting" de uma review que
    # ELOGIA a atuação não pode virar apoio só porque a palavra existe nela.
    review = ("Music was cool, acting was decent. Story sucked ass. Great acting "
              "though, I'll give it that.")
    for trecho in ("acting", "Great acting", "acting was decent."):
        assert J.trecho_encontrado(trecho, review)
        assert not J.apoio_final(True, trecho, review)
        assert J.motivo_sem_apoio(True, trecho, review).startswith("trecho curto")


def test_palavras_contam_por_espaco_depois_de_normalizar():
    assert J.n_palavras("  Great\n\tacting ,  ok  ") == 4
    assert J.n_palavras(None) == 0 and J.n_palavras("") == 0


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


@pytest.mark.parametrize("versao,ctx", [("v2.0", 3584), ("v2.1", 4096)])
def test_num_ctx_e_o_menor_multiplo_de_512_para_o_maior_par_real(versao, ctx):
    # O maior par dos 900 (gate-local): review de 4.990 caracteres.
    est = J.estimar_contexto([_par("maior", 4990)], versao)
    assert J.num_ctx(versao) == est["menor_multiplo_512"] == ctx


def test_maiores_pares_uma_review_por_vez():
    pares = [_par("a1", 5000, "A"), _par("a2", 4999, "A"), _par("b", 4000), _par("c", 10)]
    assert [p["id_par"] for p in J.maiores_pares(pares, n=2)] == ["a1", "b"]


def test_medicao_julga_com_a_saida_inteira():
    ok = J.julgar_medicao([{"prompt_eval_count": 2000}, {"prompt_eval_count": 2400}])
    assert ok["cabe"] and ok["precisa"] == 2400 + J.NUM_PREDICT
    assert ok["folga"] == J.num_ctx() - ok["precisa"]
    ruim = J.julgar_medicao([{"prompt_eval_count": J.num_ctx() - J.NUM_PREDICT + 1}])
    assert not ruim["cabe"]


def test_guarda_por_chamada_pega_prompt_que_encosta_na_janela():
    assert J.contexto_estoura({"prompt_eval_count": 2000, "eval_count": 300}) is None
    assert J.contexto_estoura({"prompt_eval_count": J.num_ctx() - J.NUM_PREDICT + 1,
                               "eval_count": 5})
    assert J.contexto_estoura({"prompt_eval_count": 2500, "eval_count": J.num_ctx()})
    # a janela é a da versão: 3000 de prompt cabe na v2.1, não na v2.0
    assert J.contexto_estoura({"prompt_eval_count": 3000, "eval_count": 50}, "v2.0")
    assert J.contexto_estoura({"prompt_eval_count": 3000, "eval_count": 50}, "v2.1") is None


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
    _, pares = _entrada_longa()
    vistos, n = [], {"i": 0}

    def chamar(system, user):
        assert system == J.system("v2.0")
        assert "Texto longo da review" in user
        vistos.append(user)
        n["i"] += 1
        if n["i"] == 2:
            return _resp('{"trecho": "texto', finish_reason="length")
        if n["i"] == 3:
            return _resp('{"trecho": null, "apoia": false}',
                         prompt_eval_count=J.num_ctx("v2.0"))
        if n["i"] == 4:
            raise RuntimeError("prazo")
        return _resp('{"trecho": "texto longo da review", "apoia": true}')

    saida = tmp_path / "s.jsonl"
    r = J.rodar(pares, saida, chamar, versao="v2.0")
    assert r["rodados"] == 8 and r["falhas"] == 3
    regs = C._ler_jsonl(saida)
    erros = [x["erro"] for x in regs if not x["ok"]]
    assert any("finish_reason='length'" in e for e in erros)
    assert any("contexto" in e for e in erros)
    assert any(e.startswith("RuntimeError") for e in erros)
    ok = [x for x in regs if x["ok"]]
    assert all(x["config_sha256"] == J.config_sha256("v2.0") and x["pensamento"] for x in ok)
    assert all(x["motivo_sem_apoio"] is None for x in ok)
    r2 = J.rodar(pares, saida, chamar, versao="v2.0")
    assert r2["rodados"] == 3 and len(vistos) == 11
    ver = J.vereditos(pares, C._ler_jsonl(saida), "v2.0")
    assert len(ver) == 8 and all(v["apoio"] for v in ver.values())


def test_vereditos_recalculam_o_apoio_do_texto_e_nao_confiam_no_modelo():
    _, pares = _entrada_longa()
    sha = J.config_sha256("v2.0")
    base = {"ok": True, "config_sha256": sha, "modelo_efetivo": J.MODELO, "think": J.THINK,
            "motivo_sem_apoio": None}           # o campo gravado não é lido
    regs = [{**base, "id_par": p["id_par"], "apoia": True, "trecho": TRECHO_R1}
            for p in pares]
    ver = J.vereditos(pares, regs, "v2.0")
    for p in pares:
        v = ver[p["id_par"]]
        assert v["apoia_modelo"] is True
        # o trecho da r1 não está na review r2: o código derruba o sim do modelo
        assert v["apoio"] is (p["review_id"] == "r1") and v["trecho_encontrado"] is v["apoio"]
        assert v["motivo"] == (None if v["apoio"] else "trecho não encontrado na review")
    regs = [{**base, "id_par": p["id_par"], "apoia": True, "trecho": "texto longo"}
            for p in pares]
    ver = J.vereditos(pares, regs, "v2.0")
    assert all(v["trecho_encontrado"] and not v["apoio"]
               and v["motivo"] == "trecho curto (2 palavras < 4)" for v in ver.values())


def test_vereditos_exigem_configuracao_modelo_think_e_todos_os_pares():
    _, pares = _entrada()
    base = {"ok": True, "config_sha256": J.config_sha256("v2.0"), "modelo_efetivo": J.MODELO,
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
    J._chamador(num_ctx=J.num_ctx(), num_predict=J.NUM_PREDICT, schema=J.schema())("S", "U")
    assert visto == {"estagio": J.ESTAGIO, "modelo": J.MODELO, "schema": J.SCHEMA_V2_1,
                     "num_predict": J.NUM_PREDICT, "num_ctx": J.num_ctx(),
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
    _alongar(d)
    por = {p["id_par"]: p for p in pares}
    _csv(d / C.ARQ_ROTULOS, [(k, "sim" if por[v]["review_id"] == "r1" else "não")
                            for k, v in mapa["pares"].items()])
    base = {"ok": True, "config_sha256": J.config_sha256("v2.0"), "modelo_efetivo": J.MODELO,
            "think": J.THINK, "apoia": True, "pensamento": "raciocínio"}
    trecho_r2 = {0: "frase inventada que não está", 1: "review"}   # não achado; curto
    C._escrever(d / J.DIR_V2 / "calibracao_v2.0_saida.jsonl", "".join(
        json.dumps({**base, "id_par": p["id_par"],
                    "trecho": TRECHO_R1 if p["review_id"] == "r1" else trecho_r2[p["i"]]})
        + "\n" for p in pares))
    J.cmd_calibrar(SimpleNamespace(dir=d, versao="v2.0"))
    cal = json.loads((d / J.DIR_V2 / "calibracao_v2.0.json").read_text())
    assert cal["geral"]["precisao"] == 1.0 and cal["geral"]["recall"] == 1.0
    assert cal["v1"]["geral"]["precisao"] == 0.5
    assert not cal["erros"]
    assert sorted(x["motivo"] for x in cal["derrubados_pelo_codigo"]) == (
        ["trecho curto (1 palavra < 4)"] * 2 + ["trecho não encontrado na review"] * 2)
    md = (d / J.DIR_V2 / "calibracao_v2.0.md").read_text()
    assert "(trecho curto (1 palavra < 4))" in md
    assert md.splitlines()[2].startswith("> **CALIBRAÇÃO, NÃO VALIDAÇÃO.**")


def test_calibracao_lista_o_erro_com_trecho_e_raciocinio(tmp_path):
    d, pares, mapa = _montar_dir(tmp_path, lambda p: True)
    _alongar(d)
    _csv(d / C.ARQ_ROTULOS, [(k, "não") for k in mapa["pares"]])
    base = {"ok": True, "config_sha256": J.config_sha256("v2.0"), "modelo_efetivo": J.MODELO,
            "think": J.THINK, "apoia": True, "trecho": "texto longo da review",
            "pensamento": "PENSEI"}
    C._escrever(d / J.DIR_V2 / "calibracao_v2.0_saida.jsonl", "".join(
        json.dumps({**base, "id_par": p["id_par"]}) + "\n" for p in pares))
    J.cmd_calibrar(SimpleNamespace(dir=d, versao="v2.0"))
    md = (d / J.DIR_V2 / "calibracao_v2.0.md").read_text()
    assert "REPROVARIA" in md and "PENSEI" in md and '"texto longo da review"' in md
    assert "4 palavras; motivo: —" in md
    assert "### P01" in md


def test_nada_disto_toca_os_publicados(tmp_path):
    antes = _hash_publicados()
    test_calibracao_ponta_a_ponta_se_declara_calibracao(tmp_path)
    assert _hash_publicados() == antes


# ---------------------------------------------------------------------------
# v2.1 — o primeiro ajuste (uma correção por causa de erro da v2.0)
# ---------------------------------------------------------------------------

# Trechos dos pares reais da calibração da v2.0 (gate-local).
REVIEW_P28 = ("The first half was great, but then the visuals got exhausting and the "
              "fake-ahh body horror really started to annoy me. I spent the last 45 "
              "minutes waiting for it to end.")
TRECHO_P28 = "the fake‑ahh body horror really started to annoy me."   # U+2011
REVIEW_P08 = ("bon ok la façon dont c’est réalisé est très intéressante. par contre, "
              "j’ai carrément détesté la fin, pcq tout le long on s’attend à une réponse "
              "concrète mais le but du film c’est justement de ne donner aucune réponse, "
              "du coup c’est super frustrant.")
REVIEW_P13 = ("Joaquin Phoenix ist einerseits natürlich einnehmend, wirkt aber sehr "
              "distanziert. • Joaquin Phoenix als Napoleon Fazit: Dieser Film ist eine "
              "einzige Wucht.")


def test_v2_1_hifen_u2011_numa_copia_fiel_e_encontrado():
    # P28: a v2.0 derrubou uma cópia fiel por causa do hífen não separável
    assert not J.trecho_encontrado(TRECHO_P28, REVIEW_P28)
    assert J.trecho_encontrado_v2_1(TRECHO_P28, REVIEW_P28)
    resp = {"trecho": TRECHO_P28, "ambiguo": False, "apoia": True}
    assert J.motivo_sem_apoio_v2_1(resp, REVIEW_P28) is None


@pytest.mark.parametrize("trecho,texto", [
    ("o final — aberto — frustra", "O final - aberto - frustra"),        # travessão
    ("o final – aberto", "o final - aberto"),                                  # meia-risca
    ("“obra-prima”, disse ele", '"obra-prima", disse ele'),              # aspas
    ("j'ai adoré la fin", "J’ai adoré la fin"),                                # apóstrofo
    ("a  fotografia é linda", "a fotografia é linda"),                         # NBSP
    ("a fotografia é linda", "a fotografia é linda"),                          # espaço fino
    ("a foto​grafia é linda", "a fotografia é linda"),                         # largura zero
    ("e então... nada", "e então… nada"),                                      # NFKC
    ("ﬁlme lindo demais", "filme lindo demais"),                                    # ligadura
])
def test_v2_1_normaliza_variantes_tipograficas(trecho, texto):
    assert J.trecho_encontrado_v2_1(trecho, texto)


def test_v2_1_copia_com_palavra_omitida_ou_partes_coladas_segue_nao_contando():
    # P08: o modelo omitiu "j’ai carrément" do meio da frase
    omitido = ("je détesté la fin, pcq tout le long on s’attend à une réponse concrète "
               "mais le but du film c’est justement de ne donner aucune réponse, du coup "
               "c’est super frustrant.")
    assert not J.trecho_encontrado_v2_1(omitido, REVIEW_P08)
    # P13: partes distantes coladas com "…" (acerto do código na v2.0)
    colado = "Joaquin Phoenix als Napoleon … wirkt sehr distanziert."
    assert not J.trecho_encontrado_v2_1(colado, REVIEW_P13)
    for trecho in (omitido, colado):
        resp = {"trecho": trecho, "ambiguo": False, "apoia": True}
        assert J.motivo_sem_apoio_v2_1(resp, REVIEW_P08 + " " + REVIEW_P13) == (
            "trecho não encontrado na review")
    # sem acento continua diferente
    assert not J.trecho_encontrado_v2_1("tres emouvante", REVIEW)


@pytest.mark.parametrize("ambiguo,apoia,trecho,motivo", [
    (False, True, "Great acting,  but the STORY sucked.", None),
    (True, True, "Great acting,  but the STORY sucked.", "modelo disse que é ambíguo"),
    (True, False, None, "modelo disse que não apoia"),
    (True, True, None, "modelo disse que é ambíguo"),
    (False, True, "Great acting", "trecho curto (2 palavras < 4)"),
    (False, True, None, "trecho nulo"),
    (False, True, "Ótima atuação, mas a história é fraca.", "trecho não encontrado na review"),
])
def test_v2_1_ambiguo_nunca_e_apoio(ambiguo, apoia, trecho, motivo):
    # P15: o raciocínio dizia "ambíguo" e o modelo respondeu sim
    resp = {"trecho": trecho, "ambiguo": ambiguo, "apoia": apoia}
    assert J.motivo_sem_apoio_v2_1(resp, REVIEW) == motivo
    assert J.motivo_da_versao(resp, REVIEW, "v2.1") == motivo


@pytest.mark.parametrize("texto", ['{"trecho": null, "apoia": false}',
                                   '{"trecho": null, "ambiguo": "não", "apoia": false}',
                                   '{"trecho": null, "ambiguo": false, "apoia": 1}',
                                   '{"trecho": null, "ambiguo": false, "apoia": false, "x": 1}'])
def test_v2_1_resposta_sem_ambiguo_booleano_e_falha(texto):
    with pytest.raises(Exception):
        J.ler_resposta_v2_1(texto)


def test_v2_1_resposta_no_formato():
    assert J.ler_resposta_v2_1('{"trecho": "a b", "ambiguo": true, "apoia": true}') == {
        "trecho": "a b", "ambiguo": True, "apoia": True}


def test_v2_1_prompt_destaca_nucleo_implicito_duas_ideias_ambiguo_e_copia():
    s = J.system("v2.1")
    assert J.CRITERIO_DONO in s
    for trecho in ("O NÚCLEO do bullet é o TÍTULO", "NÃO é exigência",
                   "Apoio implícito CONTA, desde que inequívoco",
                   "elogiar a protagonista é elogiar a atuação",
                   "Título com duas ideias", "ideia PRINCIPAL",
                   '"ambiguo": true não conta como apoio',
                   "Não omita nem altere NADA", "não use reticências",
                   "FRASE INTEIRA", "LITERALMENTE", "menos de 4 palavras"):
        assert trecho in s, trecho
    assert '"ambiguo": true ou false' in s


def test_v2_1_exemplos_sao_de_filmes_fora_dos_40_pares():
    s = J.system("v2.1").casefold()
    for nome in ("jennifer lawrence", "mother", "napoleão", "napoleon", "josefina",
                 "joséphine", "phoenix", "substance", "demi moore", "anatomia",
                 "anatomy", "sandra", "incêndios", "incendies", "aronofsky"):
        assert nome not in s, nome


def test_v2_1_roda_e_le_o_campo_ambiguo(tmp_path):
    _, pares = _entrada_longa()

    def chamar(system, user):
        assert system == J.system("v2.1")
        amb = "r2" in user
        return _resp(json.dumps({"trecho": "texto longo da review", "ambiguo": amb,
                                 "apoia": True}))

    saida = tmp_path / "s.jsonl"
    r = J.rodar(pares, saida, chamar, versao="v2.1")
    assert r["falhas"] == 0
    regs = C._ler_jsonl(saida)
    assert all(x["config_sha256"] == J.config_sha256("v2.1") for x in regs)
    ver = J.vereditos(pares, regs, "v2.1")
    por = {p["id_par"]: p for p in pares}
    for id_par, v in ver.items():
        r2 = por[id_par]["review_id"] == "r2"
        assert v["ambiguo"] is r2 and v["apoia_modelo"] is True
        assert v["apoio"] is (not r2)
        assert v["motivo"] == ("modelo disse que é ambíguo" if r2 else None)
    # registro da v2.0 não serve para a v2.1
    with pytest.raises(ValueError, match="outra configuração"):
        J.vereditos(pares, [{**x, "config_sha256": J.config_sha256("v2.0")} for x in regs],
                    "v2.1")


def test_calibracao_v2_1_ao_lado_do_v1_e_da_v2_0(tmp_path):
    d, pares, mapa = _montar_dir(tmp_path, lambda p: True)
    _alongar(d)
    por = {p["id_par"]: p for p in pares}
    _csv(d / C.ARQ_ROTULOS, [(k, "sim" if por[v]["review_id"] == "r1" else "não")
                            for k, v in mapa["pares"].items()])
    comum = {"ok": True, "modelo_efetivo": J.MODELO, "think": J.THINK, "pensamento": "p"}
    # v2.0 diz sim a tudo com prova; v2.1 diz que r2 é ambíguo
    C._escrever(d / J.DIR_V2 / "calibracao_v2.0_saida.jsonl", "".join(
        json.dumps({**comum, "config_sha256": J.config_sha256("v2.0"), "id_par": p["id_par"],
                    "apoia": True, "trecho": "texto longo da review"}) + "\n"
        for p in pares))
    C._escrever(d / J.DIR_V2 / "calibracao_v2.1_saida.jsonl", "".join(
        json.dumps({**comum, "config_sha256": J.config_sha256("v2.1"), "id_par": p["id_par"],
                    "apoia": True, "ambiguo": p["review_id"] == "r2",
                    "trecho": "texto longo da review"}) + "\n" for p in pares))
    J.cmd_calibrar(SimpleNamespace(dir=d, versao=None))
    cal = json.loads((d / J.DIR_V2 / "calibracao_v2.1.json").read_text())
    assert list(cal["comparacao"]) == ["v1", "v2.0", "v2.1"]
    assert cal["comparacao"]["v2.0"]["geral"]["precisao"] == 0.5
    assert cal["geral"]["precisao"] == 1.0 and cal["geral"]["recall"] == 1.0
    assert {x["motivo"] for x in cal["derrubados_pelo_codigo"]} == {
        "modelo disse que é ambíguo"}
    md = (d / J.DIR_V2 / "calibracao_v2.1.md").read_text()
    for linha in ("| v1 · todos |", "| v2.0 · todos |", "| v2.1 · todos |",
                  "| par | lado | dono | v1 | v2.0 | v2.1 |"):
        assert linha in md, linha
