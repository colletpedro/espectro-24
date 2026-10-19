"""[2026-10-19] Checagem de apoio dos bullets (`scripts/checagem_bullets.py`):
a contagem do eixo bate com o bloco publicado, a recuperação centra o hub e
fica no próprio grupo, o juiz é um par por chamada e retoma sem refazer, o
documento de rotulagem não revela lado nem resposta, e a validação e o
relatório não deixam par sem veredito ou sem rótulo virar "não" em silêncio."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import checagem_bullets as C  # noqa: E402

PUB = RAIZ / "resultado"


def _hash_publicados() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PUB.glob("*.json"))}


# ---------------------------------------------------------------------------
# Parte 1a
# ---------------------------------------------------------------------------

def _doc(lado: str = "x") -> dict:
    return {"slug": "f", "buckets": [
        {"bucket": "negativas", "n_validas": 4, "temas": [
            {"tema": "ritmo lento", "mencoes_aproximadas": 3, "n_reviews_analisadas": 4,
             "exemplo_parafraseado": "Várias críticas acham lento."},
            {"tema": "ritmo cansativo", "mencoes_aproximadas": 2, "n_reviews_analisadas": 4,
             "exemplo_parafraseado": "Alguns cansaram."},
            {"tema": "atuações fracas", "mencoes_aproximadas": 2, "n_reviews_analisadas": 4,
             "exemplo_parafraseado": "O elenco não convence."},
            {"tema": "tema livre", "mencoes_aproximadas": 1, "n_reviews_analisadas": 4,
             "exemplo_parafraseado": ""}]}],
        "eixos": {"linhas": [
            {"eixo": "ritmo", "por_bucket": {"negativas": {
                "mencoes": 3, "de_n": 4, "tema": "ritmo lento",
                "temas_no_mesmo_eixo": ["ritmo cansativo"]}}},
            {"eixo": "atuacao", "por_bucket": {"negativas": {
                "mencoes": 1, "de_n": 4, "tema": "atuações fracas",
                "temas_no_mesmo_eixo": []}}}]}}


CLS = {"negativas": {"r1": ["ritmo"], "r2": ["ritmo", "atuacao"], "r3": ["ritmo", "ritmo"],
                     "r4": ["roteiro_estrutura"]}}


def test_eixo_por_tema_le_a_celula_e_os_temas_no_mesmo_eixo():
    m = C.eixo_por_tema(_doc())
    assert m[("negativas", "ritmo lento")] == "ritmo"
    assert m[("negativas", "ritmo cansativo")] == "ritmo"
    assert m[("negativas", "atuações fracas")] == "atuacao"
    assert ("negativas", "tema livre") not in m


def test_reconciliar_confere_cada_celula_e_quebra_na_divergencia():
    assert C.reconciliar(_doc(), CLS) == 2
    ruim = _doc()
    ruim["eixos"]["linhas"][0]["por_bucket"]["negativas"]["mencoes"] = 2
    with pytest.raises(ValueError, match="ritmo"):
        C.reconciliar(ruim, CLS)


def test_classificacao_restrita_a_analisada_e_sem_buraco():
    cat = {"f": {"negativas": {"a": ["ritmo"], "b": [], "c": ["atuacao"]}}}
    assert C.classificacao_analisada("f", {"negativas": {"a", "b"}}, cat) == {
        "negativas": {"a": ["ritmo"], "b": []}}
    with pytest.raises(ValueError, match="sem classificação"):
        C.classificacao_analisada("f", {"negativas": {"a", "z"}}, cat)


def test_medida_eixo_marca_suspeito_sem_eixo_e_declarado_acima():
    filmes = {"f": {"docs": {"publicado": _doc(), "local": _doc()}, "cls": CLS}}
    bl = {(b["lado"], b["tema"]): b for b in C.medida_eixo(filmes)}
    assert len(bl) == 8
    r = bl[("publicado", "ritmo lento")]
    assert (r["eixo"], r["n_com_eixo"], r["de_n"]) == ("ritmo", 3, 4)
    assert r["ids_com_eixo"] == ["r1", "r2", "r3"] and not r["suspeito"]
    a = bl[("local", "atuações fracas")]
    assert a["n_com_eixo"] == 1 and a["suspeito"] and a["declarado_acima_do_eixo"]
    livre = bl[("local", "tema livre")]
    assert livre["sem_eixo"] and livre["eixo"] is None and not livre["suspeito"]


# ---------------------------------------------------------------------------
# Quantificador
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto,palavra,faixa", [
    ("Várias críticas destacam o ritmo.", "varias", "muitos"),
    ("Alguns espectadores acharam fraco.", "alguns", "alguns"),
    ("A maioria das reviews, e muitos outros, elogiam.", "a maioria", "a maioria"),
    ("Muitos dizem que quase todos dormiram.", "muitos", "muitos"),
    ("Poucas pessoas notaram.", "poucas", "poucos"),
])
def test_quantificador_e_o_primeiro_do_texto(texto, palavra, faixa):
    assert C.quantificador_do_texto(texto) == {"palavra": palavra, "faixa": faixa}


def test_texto_sem_quantificador_e_parte_do_filme_nao_conta():
    assert C.quantificador_do_texto("O filme é lento na segunda parte do filme.") is None
    assert C.quantificador_do_texto("") is None


def test_faixa_do_declarado_e_a_do_site():
    assert C.faixa_do_declarado(25, 40) == "a maioria"
    assert C.faixa_do_declarado(3, 40) == "poucos"


# ---------------------------------------------------------------------------
# Parte 1b — recuperação
# ---------------------------------------------------------------------------

class _EncFalso:
    """Vetores a mão: o texto escolhe a direção. `hub` é parecida com quase
    tudo; `ortogonal` não é parecida com nada (referência que não centra)."""
    DIR = {"lento": [1, 0, 0, 0], "atuação": [0, 1, 0, 0], "hub": [0.75, 0.75, 0.2, 0],
           "fraco": [0.6, 0, 0.8, 0], "nada": [0, 0, 1, 0], "ortogonal": [0, 0, 0, 1]}

    def _v(self, t):
        for k, v in self.DIR.items():
            if k in t:
                x = np.array(v, float)
                return x / np.linalg.norm(x)
        raise AssertionError(t)

    def queries(self, textos):
        return np.array([self._v(t) for t in textos])

    def passagens(self, textos):
        return np.array([self._v(t) for t in textos])


def _r(rid, texto, nivel=2.0):
    return SimpleNamespace(id=rid, texto=texto, nivel=nivel)


def _bl(tema):
    return [{"id_bullet": "x|f|negativas|0", "slug": "f", "bucket": "negativas",
             "tema": tema, "exemplo": ""}]


def test_recuperacao_fica_no_grupo_corta_em_k_e_desempata_por_id():
    grupos = {("f", "negativas"): [_r("b", "lento demais"), _r("n", "nada"),
                                   _r("a", "muito lento")],
              ("f", "positivas"): [_r("p", "lento")]}
    rec = C.recuperar(_bl("lento"), grupos, _EncFalso(), ["ortogonal"], k=2)[0]
    assert [t["id"] for t in rec["top"]] == ["a", "b"]          # empate em 1.0: por id
    assert [t["rank"] for t in rec["top"]] == [1, 2]
    assert set(rec["score"]) == {"a", "b", "n"}                 # nunca o outro grupo
    assert rec["top"][0]["sim"] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="referência"):
        C.recuperar(_bl("lento"), grupos, _EncFalso(), [])


def test_centrar_derruba_o_hub_que_o_cosseno_cru_poe_no_topo():
    grupos = {("f", "negativas"): [_r("h", "hub"), _r("g", "fraco")]}
    cru = C.recuperar(_bl("lento"), grupos, _EncFalso(), ["ortogonal"], k=2)[0]
    assert [t["id"] for t in cru["top"]] == ["h", "g"]          # 0,69 > 0,60
    cen = C.recuperar(_bl("lento"), grupos, _EncFalso(), ["atuação"], k=2)[0]
    assert [t["id"] for t in cen["top"]] == ["g", "h"]
    h = next(t for t in cen["top"] if t["id"] == "h")
    # o deslocamento do hub é o cosseno dele com "atuação" (4 casas gravadas)
    assert h["score"] == pytest.approx(h["sim"] - 0.75 / np.linalg.norm([0.75, 0.75, 0.2]),
                                       abs=1e-4)


# ---------------------------------------------------------------------------
# Parte 2 — o juiz
# ---------------------------------------------------------------------------

def _bullets_eixo(lado):
    return [{"id_bullet": f"{lado}|f|negativas|{i}", "lado": lado, "slug": "f",
             "bucket": "negativas", "i": i, "tema": f"tema {lado} {i}",
             "exemplo": "desc", "mencoes": 5, "n": 40, "ids_com_eixo": ["r1"]}
            for i in range(2)]


def _entrada():
    bl = _bullets_eixo("publicado") + _bullets_eixo("local")
    rec = [{"id_bullet": b["id_bullet"],
            "top": [{"rank": 1, "id": "r2", "sim": 0.8, "score": 0.03},
                    {"rank": 2, "id": "r1", "sim": 0.79, "score": 0.02}]} for b in bl]
    revs = {("f", "negativas", rid): _r(rid, f"texto {rid}", 1.5) for rid in ("r1", "r2")}
    return bl, C.montar_entrada(bl, rec, revs)


def test_entrada_um_par_por_bullet_e_review_agrupada_por_review():
    bl, pares = _entrada()
    assert len(pares) == 8 and len({p["id_par"] for p in pares}) == 8
    assert [p["review_id"] for p in pares] == ["r1"] * 4 + ["r2"] * 4
    assert {p["lado"] for p in pares[:4]} == {"publicado", "local"}
    r1 = [p for p in pares if p["review_id"] == "r1"]
    assert all(p["review_tem_eixo"] for p in r1)
    assert pares[0]["texto"] == "texto r1" and pares[0]["nivel"] == 1.5


def test_mensagem_do_juiz_review_primeiro_tema_por_ultimo():
    _, pares = _entrada()
    u = C.user_juiz(pares[0])
    assert u.startswith("Review (nota 1.5 de 5 estrelas):\n\ntexto r1")
    assert u.index("texto r1") < u.index("Tema: ") < u.index("A review menciona")


def test_juiz_e_dono_respondem_a_mesma_pergunta():
    assert C.CRITERIO in C.SYSTEM_JUIZ
    assert C.SCHEMA_JUIZ["properties"] == {"menciona": {"type": "boolean"}}


@pytest.mark.parametrize("texto", ['{"menciona": "sim"}', '{"x": true}', '[true]', 'sim'])
def test_veredito_fora_do_formato_e_falha(texto):
    with pytest.raises(Exception):
        C.veredito_do_juiz(texto)


def test_veredito_no_formato():
    assert C.veredito_do_juiz('{"menciona": true}') is True
    assert C.veredito_do_juiz('{"menciona": false}') is False


def test_juiz_retoma_sem_refazer_e_refaz_so_a_falha(tmp_path):
    _, pares = _entrada()
    vistos, n = [], {"i": 0}

    def chamar(system, user):
        assert system == C.SYSTEM_JUIZ
        vistos.append(user)
        n["i"] += 1
        if n["i"] == 3:
            raise RuntimeError("prazo")
        return {"texto": '{"menciona": true}', "latencia_s": 1.0, "eval_count": 7,
                "modelo_efetivo": "qwen3:14b", "custo_usd": 0.0}

    saida = tmp_path / "s.jsonl"
    r = C.rodar_juiz(pares, saida, chamar, modelo="qwen3:14b", think="false")
    assert r["rodados"] == 8 and r["falhas"] == 1 and len(vistos) == 8
    regs = C._ler_jsonl(saida)
    assert sum(1 for x in regs if not x["ok"]) == 1
    falhou = next(x for x in regs if not x["ok"])
    assert falhou["erro"].startswith("RuntimeError") and falhou["modelo"] == "qwen3:14b"
    r2 = C.rodar_juiz(pares, saida, chamar, modelo="qwen3:14b", think="false")
    assert r2["rodados"] == 1 and len(vistos) == 9
    ver = C.vereditos(pares, C._ler_jsonl(saida))
    assert len(ver) == 8 and all(ver.values())


def test_vereditos_nao_completam_buraco_nem_aceitam_outro_prompt():
    _, pares = _entrada()
    sha = hashlib.sha256(C.SYSTEM_JUIZ.encode()).hexdigest()
    regs = [{"ok": True, "id_par": p["id_par"], "menciona": False, "system_sha256": sha}
            for p in pares[1:]]
    with pytest.raises(ValueError, match="sem veredito"):
        C.vereditos(pares, regs)
    regs.append({"ok": True, "id_par": pares[0]["id_par"], "menciona": True,
                 "system_sha256": "outro"})
    with pytest.raises(ValueError, match="outro system prompt"):
        C.vereditos(pares, regs)
    regs[-1]["system_sha256"] = sha
    regs.append({"ok": True, "id_par": pares[1]["id_par"], "menciona": True,
                 "system_sha256": sha})   # o último ok vale
    ver = C.vereditos(pares, regs)
    assert ver[pares[0]["id_par"]] is True and ver[pares[1]["id_par"]] is True


def test_juiz_nao_escreve_em_resultado():
    with pytest.raises(SystemExit, match="RECUSADO"):
        C.rodar_juiz([], PUB / "x.jsonl", lambda s, u: {}, modelo="m", think="false")


def test_estimativa_soma_par_a_par():
    vel = C.medir_velocidade([
        {"ok": True, "leitura_prompt_s": 1.0, "geracao_s": 4.0, "latencia_s": 7.0,
         "n_chars": 500, "eval_count": 20},
        {"ok": True, "leitura_prompt_s": 3.0, "geracao_s": 4.0, "latencia_s": 9.0,
         "n_chars": 1500, "eval_count": 20}])
    assert vel["leitura_s_por_char"] == pytest.approx(0.002)
    assert vel["geracao_s_por_token"] == pytest.approx(0.2)
    assert vel["sobra_s_mediana"] == pytest.approx(2.0)
    pares = [{"texto": "x" * 420, "tema": "t" * 50, "exemplo": "e" * 50}]
    est = C.estimar_tempo(pares, vel)
    # (420+50+50+80)*0.002 + 10*0.2 + 2.0 = 5.2 s, + 60 s da 1ª carga
    assert est["s_por_chamada_mediana"] == pytest.approx(5.2)
    assert est["total_min"] == pytest.approx(round(65.2 / 60, 1))


# ---------------------------------------------------------------------------
# Parte 3 — rotulagem e validação
# ---------------------------------------------------------------------------

def _pares_grandes():
    pares = []
    for lado in C.LADOS:
        for f in ("a", "b", "c", "d", "e"):
            for i in range(6):
                for rank in range(1, 6):
                    pares.append({"id_par": f"{lado}|{f}|negativas|{i}|r{rank}",
                                  "id_bullet": f"{lado}|{f}|negativas|{i}", "lado": lado,
                                  "slug": f, "bucket": "negativas", "i": i, "rank": rank,
                                  "tema": f"tema {i}", "exemplo": "desc",
                                  "nivel": 2.0, "texto": "linha 1\nlinha 2",
                                  "sim": 0.81, "score": 0.0123})
    return pares


def test_sorteio_metade_de_cada_lado_espalhado_e_reprodutivel():
    pares = _pares_grandes()
    am = C.sortear_rotulo(pares)
    assert len(am) == 40
    for lado in C.LADOS:
        x = [p for p in am if p["lado"] == lado]
        assert len(x) == 20
        assert all(sum(p["slug"] == f for p in x) == 4 for f in "abcde")
        assert sum(p["rank"] <= 2 for p in x) == 10
        assert len({p["id_bullet"] for p in x}) == 20
    assert [p["id_par"] for p in am] == [p["id_par"] for p in C.sortear_rotulo(pares)]
    assert {p["lado"] for p in am[:10]} == set(C.LADOS)   # embaralhado


def test_documento_de_rotulo_nao_revela_lado_modelo_nem_numero():
    am = C.sortear_rotulo(_pares_grandes())
    doc = C.montar_doc_rotulo(am, {f: f"Filme {f}" for f in "abcde"}, "selo123")
    baixo = doc.lower()
    for proibido in ("publicado", "local", "deepseek", "qwen", "gemini", "ollama",
                     "0.81", "0.0123", "rank", "juiz disse"):
        assert proibido not in baixo, proibido
    assert C.CRITERIO in doc and "selo123" in doc
    assert doc.count("menciona o tema?** sim / não") == 40
    assert "> linha 1\n> linha 2" in doc


def _csv(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("par,rotulo\n" + "".join(f"{p},{r}\n" for p, r in linhas),
                       encoding="utf-8")


def test_rotulos_exigem_todos_os_pares_com_sim_ou_nao(tmp_path):
    arq = tmp_path / "r.csv"
    _csv(arq, [("P01", "sim"), ("P02", "não"), ("P03", "Nao")])
    assert C.ler_rotulos(arq, ["P01", "P02", "P03"]) == {"P01": True, "P02": False,
                                                         "P03": False}
    _csv(arq, [("P01", "sim"), ("P02", "")])
    with pytest.raises(ValueError, match="P02"):
        C.ler_rotulos(arq, ["P01", "P02"])
    _csv(arq, [("P01", "sim")])
    with pytest.raises(ValueError, match="sem rótulo"):
        C.ler_rotulos(arq, ["P01", "P02"])
    _csv(arq, [("P01", "talvez")])
    with pytest.raises(ValueError, match="talvez"):
        C.ler_rotulos(arq, ["P01"])
    _csv(arq, [("P01", "sim"), ("P01", "não")])
    with pytest.raises(ValueError, match="duas vezes"):
        C.ler_rotulos(arq, ["P01"])


def test_matriz_contra_a_conta_a_mao():
    # dono, juiz: 6 VP, 2 FP, 1 FN, 3 VN
    pares = [(True, True)] * 6 + [(False, True)] * 2 + [(True, False)] + [(False, False)] * 3
    m = C.matriz(pares)
    assert (m["vp"], m["fp"], m["fn"], m["vn"]) == (6, 2, 1, 3)
    assert m["precisao"] == 0.75 and m["recall"] == round(6 / 7, 3)
    assert m["acuracia"] == 0.75
    lo, hi = m["precisao_ic95"]
    assert lo < 0.75 < hi
    assert C.wilson(0, 0) is None


def test_criterio_reprova_com_motivo():
    ruim = C.matriz([(True, True)] * 7 + [(False, True)] * 3 + [(True, False)])
    j = C.julgar_validacao(ruim)
    assert not j["vale"] and any("precisão" in m for m in j["motivos"])
    bom = C.matriz([(True, True)] * 9 + [(False, False)] * 5 + [(True, False)])
    assert C.julgar_validacao(bom)["vale"]


# ---------------------------------------------------------------------------
# Do começo ao fim, num diretório sintético
# ---------------------------------------------------------------------------

def _montar_dir(tmp_path, juiz_diz):
    """Entrada, saída do juiz, mapa e rótulos sintéticos coerentes."""
    _, pares = _entrada()
    d = tmp_path / "cb"
    bl = [{**b, "eixo": "ritmo", "n_com_eixo": 1, "de_n": 40, "suspeito": True,
           "sem_eixo": False, "declarado_acima_do_eixo": True}
          for b in _bullets_eixo("publicado") + _bullets_eixo("local")]
    C._json(d / C.ARQ_EIXO, {"meta": {"filmes": ["anatomy-of-a-fall"]},
                             "bullets": [{**b, "slug": "anatomy-of-a-fall",
                                          "id_bullet": b["id_bullet"].replace("|f|", "|anatomy-of-a-fall|")}
                                         for b in bl]})
    pares = [{**p, "slug": "anatomy-of-a-fall",
              "id_bullet": p["id_bullet"].replace("|f|", "|anatomy-of-a-fall|"),
              "id_par": p["id_par"].replace("|f|", "|anatomy-of-a-fall|")} for p in pares]
    C._escrever(d / C.ARQ_ENTRADA, "".join(json.dumps(p) + "\n" for p in pares))
    sha = hashlib.sha256(C.SYSTEM_JUIZ.encode()).hexdigest()
    C._escrever(d / C.ARQ_SAIDA, "".join(
        json.dumps({"ok": True, "id_par": p["id_par"], "menciona": juiz_diz(p),
                    "system_sha256": sha}) + "\n" for p in pares))
    mapa = {"semente": 1, "pares": {f"P{k:02d}": p["id_par"] for k, p in enumerate(pares, 1)}}
    selo = C._sha256_texto(json.dumps(mapa, sort_keys=True, ensure_ascii=False))
    C._json(d / C.ARQ_MAPA, {**mapa, "sha256": selo})
    return d, pares, mapa


def test_validacao_e_relatorio_ponta_a_ponta(tmp_path):
    # o juiz diz "sim" só para r1; o dono concorda em tudo
    d, pares, mapa = _montar_dir(tmp_path, lambda p: p["review_id"] == "r1")
    por = {p["id_par"]: p for p in pares}
    _csv(d / C.ARQ_ROTULOS, [(k, "sim" if por[v]["review_id"] == "r1" else "não")
                            for k, v in mapa["pares"].items()])
    with pytest.raises(SystemExit, match="sem validacao"):
        C.cmd_relatorio(SimpleNamespace(dir=d))
    C.cmd_validar_juiz(SimpleNamespace(dir=d))
    val = json.loads((d / C.ARQ_VALIDACAO).read_text())
    assert val["julgamento"]["vale"] and val["geral"]["precisao"] == 1.0
    C.cmd_relatorio(SimpleNamespace(dir=d))
    fin = json.loads((d / "resultado_final.json").read_text())
    assert fin["vale"] and fin["por_lado"]["publicado"]["frac_ge1"] == 1.0
    assert fin["por_lado"]["local"]["apoio_ge2"] == 0
    md = (d / "resultado_final.md").read_text()
    assert "NÃO VALE" not in md and "o teto é 5" in md


def test_relatorio_diz_que_nao_vale_quando_o_juiz_falha(tmp_path):
    d, pares, mapa = _montar_dir(tmp_path, lambda p: True)   # o juiz diz sim a tudo
    por = {p["id_par"]: p for p in pares}
    _csv(d / C.ARQ_ROTULOS, [(k, "sim" if por[v]["review_id"] == "r1" else "não")
                            for k, v in mapa["pares"].items()])
    C.cmd_validar_juiz(SimpleNamespace(dir=d))
    assert "NÃO VALE" in (d / "validacao_juiz.md").read_text()
    C.cmd_relatorio(SimpleNamespace(dir=d))
    assert not json.loads((d / "resultado_final.json").read_text())["vale"]
    assert "ESTE RESULTADO NÃO VALE" in (d / "resultado_final.md").read_text()


def test_validacao_recusa_mapa_adulterado(tmp_path):
    d, _, mapa = _montar_dir(tmp_path, lambda p: True)
    m = json.loads((d / C.ARQ_MAPA).read_text())
    m["pares"]["P01"], m["pares"]["P02"] = m["pares"]["P02"], m["pares"]["P01"]
    (d / C.ARQ_MAPA).write_text(json.dumps(m))
    with pytest.raises(SystemExit, match="selo"):
        C.cmd_validar_juiz(SimpleNamespace(dir=d))


def test_sorteio_nunca_por_cima_de_rotulo_preenchido(tmp_path):
    d = tmp_path / "cb"
    C._escrever(d / C.ARQ_ENTRADA, "".join(json.dumps(p) + "\n" for p in _pares_grandes()))
    _csv(d / C.ARQ_ROTULOS, [("P01", "sim"), ("P02", "")])
    with pytest.raises(SystemExit, match="1 rótulos"):
        C.cmd_amostra_rotulo(SimpleNamespace(dir=d, refazer=True))
    _csv(d / C.ARQ_ROTULOS, [("P01", ""), ("P02", "")])
    with pytest.raises(SystemExit, match="--refazer"):
        C.cmd_amostra_rotulo(SimpleNamespace(dir=d, refazer=False))


def test_cli_recusa_dir_dentro_de_resultado():
    with pytest.raises(SystemExit, match="RECUSADO"):
        C.main(["relatorio", "--dir", str(PUB / "checagem")])


# ---------------------------------------------------------------------------
# Dado real: a contagem do eixo bate com o publicado, e nada é tocado
# ---------------------------------------------------------------------------

def test_eixo_no_dado_real_reconcilia_e_nao_toca_os_publicados(tmp_path):
    """Os dois lados = o publicado (a prosa local vive no branch gate-local):
    exercita a amostra refeita do bruto, o consenso de produção e a
    reconciliação célula a célula contra o bloco `eixos` publicado."""
    antes = _hash_publicados()
    C.main(["eixo", "--local-dir", str(PUB), "--dir", str(tmp_path / "cb"),
            "--slug", "anatomy-of-a-fall"])
    dado = json.loads((tmp_path / "cb" / C.ARQ_EIXO).read_text())
    assert dado["meta"]["celulas_conferidas"] > 0
    bl = dado["bullets"]
    pub = json.loads((PUB / "anatomy-of-a-fall.json").read_text())
    assert len(bl) == 2 * sum(len(b["temas"]) for b in pub["buckets"])
    ritmo = next(b for b in bl if b["lado"] == "publicado" and b["bucket"] == "negativas"
                 and b["eixo"] == "ritmo")
    linha = next(l for l in pub["eixos"]["linhas"] if l["eixo"] == "ritmo")
    assert ritmo["n_com_eixo"] == linha["por_bucket"]["negativas"]["mencoes"]
    assert all(b["de_n"] == 40 for b in bl)
    assert _hash_publicados() == antes
