"""[2026-10-12] Comparação cega da prosa: o documento de leitura não revela o
lado, o mapeamento fica fora dele com hash, e as métricas batem com a conta
feita à mão."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import comparacao_cega_prosa as K  # noqa: E402
import gerar_prosa_local as GP  # noqa: E402

PUB = RAIZ / "resultado"


def _doc(marca: str, **extra) -> dict:
    d = {"slug": "filme-x", "ficha": {"titulo": "Filme X"},
         "buckets": [{"bucket": "negativas", "n_validas": 40,
                      "temas": [{"tema": f"Tema {marca}", "mencoes_aproximadas": 10,
                                 "n_reviews_analisadas": 40,
                                 "exemplo_parafraseado": f"Exemplo {marca}",
                                 "aspas_removidas": False, "mencoes_clampadas": False}],
                      "observacao_geral": f"Obs {marca}"}],
         "narrativa": f"Narrativa {marca}", "veredito": {"texto": f"Veredito {marca}",
                                                         "origem": "llm", "flags": []},
         "condicoes": {"vale_a_pena": [{"texto": f"Vale {marca}"}],
                       "talvez_evite": [{"texto": f"Evite {marca}"}], "origem": "llm"},
         "eixos": {"linhas": [{"eixo": "ritmo", "por_bucket": {"negativas": {
             "mencoes": 20, "de_n": 40, "tema": f"Tema {marca}"}}}],
             "rotulagem": {"n_chamadas": 1, "falharam": [], "fora_da_taxonomia": {},
                           "houve_retentativa": []}},
         "verificacao_narrativa": {"n_flags": 1, "n_resenha_speak": 0}}
    d.update(extra)
    return d


def _mundo(slugs):
    return {s: {"publicado": _doc("PUBXYZ"), "local": _doc("LOCXYZ")} for s in slugs}


def test_o_documento_de_leitura_nao_nomeia_lado_modelo_nem_provider():
    slugs = ["a", "b", "c", "d", "e"]
    a_e = K.sortear(slugs)
    txt = K.montar_leitura(slugs, _mundo(slugs), a_e)
    for proibido in ("publicado", "local ", "gpt", "ollama", "deepseek", "gemini",
                     "provider", "modelo", "think"):
        assert proibido not in txt.lower(), proibido
    assert txt.count("#### A") == txt.count("#### B") == 4 * len(slugs)


def test_o_texto_de_cada_lado_cai_sob_o_rotulo_do_mapeamento():
    slugs = ["a", "b", "c", "d", "e"]
    a_e = K.sortear(slugs)
    txt = K.montar_leitura(slugs, _mundo(slugs), a_e)
    filmes = txt.split("## Filme ")[1:]
    for slug, bloco in zip(sorted(slugs), filmes):
        marca_a = "PUBXYZ" if a_e[slug] == "publicado" else "LOCXYZ"
        marca_b = "LOCXYZ" if marca_a == "PUBXYZ" else "PUBXYZ"
        narr = bloco.split("### 2. Narrativa")[1].split("### 3.")[0]
        sob_a = narr.split("#### A")[1].split("#### B")[0]
        sob_b = narr.split("#### B")[1]
        assert f"Narrativa {marca_a}" in sob_a and f"Narrativa {marca_b}" in sob_b


def test_sorteio_e_estavel_e_usa_os_dois_lados_nos_cinco_filmes_padrao():
    a = K.sortear(list(GP.FILMES_COMPARACAO))
    assert a == K.sortear(list(reversed(GP.FILMES_COMPARACAO)))
    assert set(a.values()) == {"publicado", "local"}


def test_hash_do_mapeamento_detecta_adulteracao():
    mapa = {"semente": K.SEMENTE, "a_e": K.sortear(["a", "b"]), "filmes": ["a", "b"]}
    h = K.hash_do_mapa(mapa)
    assert h == K.hash_do_mapa(copy.deepcopy(mapa))
    outro = copy.deepcopy(mapa)
    outro["a_e"]["a"] = "local" if mapa["a_e"]["a"] == "publicado" else "publicado"
    assert K.hash_do_mapa(outro) != h


def test_metricas_nomeiam_os_lados_e_trazem_o_mapeamento():
    slugs = ["a", "b"]
    a_e = K.sortear(slugs)
    faixa = K.faixa_deepseek([_doc("PUBXYZ")])
    txt = K.montar_metricas(slugs, _mundo(slugs), a_e, faixa, {})
    assert "publicado" in txt and "local" in txt and "| a |" in txt


def test_celula_da_barra_confere_sintese_com_classificacao():
    (c,) = K.celulas_barra(_doc("X"))
    assert c["sintese"] == 10 and c["classificacao"] == 20 and c["n"] == 40
    assert c["razao"] == 0.5 and c["dif_pp"] == -25.0


def test_faixa_do_deepseek_sobre_o_publicado_real():
    docs = [json.loads((PUB / "uncut-gems.json").read_text(encoding="utf-8"))]
    f = K.faixa_deepseek(docs)
    # a célula `ritmo` de `uncut-gems` negativas: síntese 14, classificação 15
    cel = {(c["bucket"], c["eixo"]): c for c in K.celulas_barra(docs[0])}
    assert cel[("negativas", "ritmo")]["sintese"] == 14
    assert cel[("negativas", "ritmo")]["classificacao"] == 15
    assert f["razao"]["p5"] <= f["razao"]["p50"] <= f["razao"]["p95"]


def test_validadores_contam_o_que_os_estagios_gravaram():
    d = _doc("X")
    d["buckets"][0]["temas"][0]["aspas_removidas"] = True
    d["buckets"][0]["idioma_invalido"] = True
    d["veredito"] = {"origem": "template_fallback", "flags": ["a", "b"], "retry": {"x": 1}}
    v = K.validadores(d)
    assert v["sintese"]["temas_aspas_removidas"] == 1
    assert v["sintese"]["buckets_idioma_invalido"] == 1
    assert v["veredito"]["origem"] == "template_fallback" and v["veredito"]["n_flags"] == 2
    t = K.taxas([v, K.validadores(_doc("Y"))])
    assert t["veredito_em_template_fallback"] == "1/2"
    assert t["sintese_temas_aspas_removidas"] == "1/2"


def test_validadores_toleram_documento_antigo_sem_blocos():
    v = K.validadores({"slug": "x", "buckets": []})
    assert v["condicoes"]["publicadas"] == 0 and v["veredito"]["origem"] is None


def test_filmes_da_comparacao_estao_publicados_fora_do_c22_e_com_bruto():
    from espectro24.excecao_c22 import SLUGS
    assert len(GP.FILMES_COMPARACAO) == 5
    for s in GP.FILMES_COMPARACAO:
        assert s not in SLUGS
        d = json.loads((PUB / f"{s}.json").read_text(encoding="utf-8"))
        assert d.get("eixos") and d.get("veredito") and d.get("condicoes") and d.get("narrativa")
        assert (RAIZ / "dados" / "bruto" / s).exists()
    contrastes = {json.loads((PUB / f"{s}.json").read_text(encoding="utf-8"))["eixos"]["contraste"]
                  for s in GP.FILMES_COMPARACAO}
    assert contrastes == {"tematico", "valorativo"}


def test_cli_recusa_mapa_dentro_da_leitura(tmp_path):
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "comparacao_cega_prosa.py"),
                        "--local-dir", str(tmp_path), "--leitura", str(tmp_path / "l"),
                        "--mapa", str(tmp_path / "l" / "m"), "--slug", "x"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "dentro de --leitura" in r.stderr
