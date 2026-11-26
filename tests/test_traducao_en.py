"""Tradução EN do conteúdo gerado: extrator, build de data_en.js e sanidade.

O extrator (`scripts/i18n_extrair_en.py`) mantém `dados/traducao_en/<slug>.json`
(mapa string-PT -> string-EN, a tradução é manual); o build
(`frontend/build_traducao_en.py`) gera `frontend/js/data_en.js`. Offline.
"""
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "dados" / "traducao_en"
DATA_EN = RAIZ / "frontend" / "js" / "data_en.js"


def _carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


EX = _carregar("i18n_extrair_en", RAIZ / "scripts" / "i18n_extrair_en.py")
BUILD = _carregar("build_traducao_en", RAIZ / "frontend" / "build_traducao_en.py")

SLUGS = EX.ler_publicados()


def _lido(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _todos_os_arquivos():
    return [ENTRADA / f"{s}.json" for s in SLUGS] + [ENTRADA / "_vocabulario.json"]


# --- extrator -------------------------------------------------------------

def test_todo_slug_publicado_tem_arquivo_e_vocabulario():
    faltam = [s for s in SLUGS if not (ENTRADA / f"{s}.json").exists()]
    assert not faltam, faltam[:5]
    assert (ENTRADA / "_vocabulario.json").exists()
    assert (ENTRADA / "_GUIA.md").exists()


def test_arquivos_batem_com_o_resultado_atual():
    """Reexecutar o extrator não muda nada: arquivos em dia com resultado/."""
    r = EX.montar(escrever=False)
    for s in SLUGS:
        assert _lido(ENTRADA / f"{s}.json") == r["filmes"][s], \
            f"{s}: rode scripts/i18n_extrair_en.py"
    assert _lido(ENTRADA / "_vocabulario.json") == r["vocabulario"]


def test_extrator_idempotente(tmp_path):
    saida = tmp_path / "t"
    shutil.copytree(ENTRADA, saida)
    antes = {p.name: p.read_bytes() for p in saida.glob("*.json")}
    EX.montar(saida=saida)
    EX.montar(saida=saida)
    depois = {p.name: p.read_bytes() for p in saida.glob("*.json")}
    assert antes == depois


def test_extrator_preserva_traducao_e_manda_sumidas_para_orfaos(tmp_path):
    slug = SLUGS[0]
    saida = tmp_path / "t"
    shutil.copytree(ENTRADA, saida)
    arq = saida / f"{slug}.json"
    obj = _lido(arq)
    primeira = next(iter(obj["textos"]))
    obj["textos"][primeira] = "TRADUZIDO"
    obj["textos"]["string que não existe mais"] = "traduzida e obsoleta"
    arq.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    EX.montar(saida=saida)
    novo = _lido(arq)
    assert novo["textos"][primeira] == "TRADUZIDO"
    assert "string que não existe mais" not in novo["textos"]
    assert novo["_orfaos"]["string que não existe mais"] == "traduzida e obsoleta"
    # a ordem de aparição não muda ao preservar
    assert list(novo["textos"]) == list(_lido(ENTRADA / f"{slug}.json")["textos"])


def test_vocabulario_nao_repete_chave_dos_filmes():
    vocab = set(_lido(ENTRADA / "_vocabulario.json")["textos"])
    for s in SLUGS:
        repetidas = vocab & set(_lido(ENTRADA / f"{s}.json")["textos"])
        assert not repetidas, (s, list(repetidas)[:3])


def test_extrai_o_que_o_render_mostra():
    """Amostra: narrativa por parágrafo, veredito, condições e temas entram;
    observacao_geral e niveis, que não renderizam, não."""
    d = EX.ler_resultado("12-angry-men")
    t = set(EX.textos_do_filme(d))
    assert d["veredito"]["texto"] in t
    for p in EX.paragrafos(d["narrativa"]):
        assert p in t
    assert d["narrativa"] not in t
    for lado in ("vale_a_pena", "talvez_evite"):
        for c in d["condicoes"][lado]:
            assert c["texto"] in t
    for b in d["buckets"]:
        assert b["observacao_geral"] not in t
        for tm in b["temas"]:
            assert tm["tema"] in t and tm["exemplo_parafraseado"] in t


# --- data_en.js -----------------------------------------------------------

def _payload_do_js():
    t = DATA_EN.read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def test_data_en_js_deterministico_e_consistente():
    esperado = BUILD.renderizar(BUILD.montar_payload(avisar=lambda *_: None))
    assert DATA_EN.read_text(encoding="utf-8") == esperado, \
        "rode python3 frontend/build_traducao_en.py"
    assert BUILD.renderizar(BUILD.montar_payload(avisar=lambda *_: None)) == esperado
    assert esperado.endswith(";\n") and "window.ESPECTRO_EN = " in esperado


def test_data_en_js_so_tem_traducoes_nao_nulas_dos_arquivos():
    p = _payload_do_js()
    voc = _lido(ENTRADA / "_vocabulario.json")["textos"]
    assert p["vocabulario"] == {k: v for k, v in voc.items() if v}
    for s, f in p["filmes"].items():
        arq = _lido(ENTRADA / f"{s}.json")
        assert f.get("textos", {}) == {k: v for k, v in arq["textos"].items() if v}
        assert f.get("titulo_en") == arq["titulo_en"]
    assert set(p["filmes"]) <= set(SLUGS)


DATA_EN_HOME = RAIZ / "frontend" / "js" / "data_en_home.js"


def _home_do_js():
    t = DATA_EN_HOME.read_text(encoding="utf-8")
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def test_data_en_home_js_deterministico_e_consistente():
    payload = BUILD.montar_payload(avisar=lambda *_: None)
    esperado = BUILD.renderizar_home(BUILD.montar_home(payload))
    assert DATA_EN_HOME.read_text(encoding="utf-8") == esperado, \
        "rode python3 frontend/build_traducao_en.py"
    assert "window.ESPECTRO_EN_HOME = " in esperado and esperado.endswith(";\n")


def test_data_en_home_js_so_tem_titulos_e_generos_e_e_pequeno():
    h = _home_do_js()
    assert set(h) == {"logos", "vocabulario_generos", "titulos"}
    p = _payload_do_js()
    assert h["titulos"] == {s: f["titulo_en"] for s, f in p["filmes"].items() if f.get("titulo_en")}
    assert set(h["vocabulario_generos"]) <= set(p["vocabulario"])
    assert all(h["vocabulario_generos"].values())
    assert DATA_EN_HOME.stat().st_size < 60_000     # nunca o texto gerado


# --- logos em inglês (dados/logos_en.json, scripts/medir_logos_en.py) -----------
LOGOS_EN = RAIZ / "dados" / "logos_en.json"
LOGOS_PT = RAIZ / "dados" / "logos.json"


def test_todo_slug_publicado_tem_entrada_em_logos_en_logo_ou_ausencia_explicita():
    reg = _lido(LOGOS_EN)["logos"]
    assert set(reg) == set(SLUGS)
    for s, r in reg.items():
        assert r["origem"] in ("tmdb_en", "tmdb_sem_idioma", "ausente"), s
        if r["origem"] == "ausente":
            assert r["logo_escolhido"] is None and r["classe"] is None, s
        else:
            lg = r["logo_escolhido"]
            # só en ou sem idioma: nunca pt-BR/pt-PT nem outro idioma
            assert lg["idioma"] in ("en", "sem_idioma"), s
            assert lg["file_path"].startswith("/"), s
            assert r["classe"] in ("claro", "escuro_mono", "escuro_cor", "desligado"), s
            assert r["titulo_difere_do_logo"] == (lg["idioma"] != "en"), s


def test_logos_en_nunca_usa_o_logo_pt_quando_ele_difere():
    en = _lido(LOGOS_EN)["logos"]
    pt = _lido(LOGOS_PT)["logos"]
    for s in SLUGS:
        lg = en[s]["logo_escolhido"]
        pt_lg = (pt.get(s) or {}).get("logo_escolhido")
        if not lg or not pt_lg or lg["file_path"] != pt_lg["file_path"]:
            assert not en[s]["reutiliza_logo_pt"], s
            continue
        # o mesmo arquivo do PT só é aceito se o logo PT não é pt-BR/pt-PT
        assert pt_lg["idioma"] in ("en", "sem_idioma"), s
        assert en[s]["reutiliza_logo_pt"], s
    # caso conhecido: o logo PT de get-out ("Corra!") não vai para o EN
    assert en["get-out-2017"]["logo_escolhido"]["file_path"] != \
        pt["get-out-2017"]["logo_escolhido"]["file_path"]
    assert en["get-out-2017"]["logo_escolhido"]["titulo_do_logo"] == "Get Out"


def test_data_en_home_js_logos_batem_com_logos_en_json():
    h = _home_do_js()
    en = _lido(LOGOS_EN)["logos"]
    assert set(h["logos"]) == set(SLUGS)
    for s in SLUGS:
        lg = en[s]["logo_escolhido"]
        if lg is None:
            assert h["logos"][s] is None, s
        else:
            assert h["logos"][s] == {"path": lg["file_path"], "idioma": lg["idioma"],
                                     "classe": en[s]["classe"],
                                     "titulo": lg["titulo_do_logo"]}, s
            assert h["logos"][s]["idioma"] in ("en", "sem_idioma")


def test_logos_en_sem_entrada_para_slug_publicado_faz_o_build_falhar(tmp_path):
    parcial = _lido(LOGOS_EN)
    parcial["logos"].pop(SLUGS[0])
    arq = tmp_path / "logos_en.json"
    arq.write_text(json.dumps(parcial), encoding="utf-8")
    with pytest.raises(SystemExit):
        BUILD.logos_en(SLUGS, arq)


def test_logos_en_deterministico():
    assert BUILD.logos_en(SLUGS) == BUILD.logos_en(list(reversed(SLUGS)))
    txt = LOGOS_EN.read_text(encoding="utf-8")
    assert txt == json.dumps(json.loads(txt), ensure_ascii=False, indent=1,
                             sort_keys=True) + "\n"


def test_build_avisa_e_omite_traducao_de_string_que_sumiu(tmp_path):
    slug = SLUGS[0]
    entrada = tmp_path / "t"
    shutil.copytree(ENTRADA, entrada)
    arq = entrada / f"{slug}.json"
    obj = _lido(arq)
    viva = next(iter(obj["textos"]))
    obj["textos"][viva] = "still valid"
    obj["textos"]["string que sumiu"] = "gone"
    obj["fonte_sha256"] = "0" * 64
    arq.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    avisos = []
    p = BUILD.montar_payload(entrada=entrada, avisar=avisos.append)
    assert any(slug in a for a in avisos)
    textos = p["filmes"][slug]["textos"]
    assert textos[viva] == "still valid" and "string que sumiu" not in textos
    assert set(textos) <= set(_lido(ENTRADA / f"{slug}.json")["textos"]) - {"string que sumiu"}


# --- completude (a tradução é manual e está em andamento) -------------------

def test_completude_toda_string_traduzida():
    pendentes = []
    for arq in _todos_os_arquivos():
        o = _lido(arq)
        if "titulo_en" in o and not o["titulo_en"]:
            pendentes.append((arq.stem, "titulo_en"))
        for pt, en in o["textos"].items():
            if en is None:
                pendentes.append((arq.stem, pt[:40]))
            elif en == pt and len(pt) > 40:     # nomes próprios curtos podem coincidir
                pendentes.append((arq.stem, "idêntico ao PT: " + pt[:40]))
    assert not pendentes, f"{len(pendentes)} pendentes, ex.: {pendentes[:3]}"


# --- sanidade das traduções JÁ preenchidas -----------------------------------

def _pares_preenchidos():
    for arq in _todos_os_arquivos():
        for pt, en in _lido(arq)["textos"].items():
            if isinstance(en, str) and en.strip():
                yield arq.stem, pt, en


def _numeros(s):
    return sorted(re.findall(r"\d+(?:[.,]\d+)?", s))


def test_sanidade_numeros_percentuais_e_marcacao_preservados():
    for nome, pt, en in _pares_preenchidos():
        assert en.count("%") == pt.count("%"), (nome, "'%' diferente", pt[:50])
        assert _numeros(en) == _numeros(pt), (nome, "números diferentes", pt[:50])
        assert en.count("~") == pt.count("~"), (nome, "'~' diferente", pt[:50])
        assert re.findall(r"\{[^}]*\}|<[^>]+>|%s", en) == re.findall(r"\{[^}]*\}|<[^>]+>|%s", pt), \
            (nome, "placeholder/marcação", pt[:50])
        assert en.count("\n") == pt.count("\n"), (nome, "quebras de linha", pt[:50])
        assert en == en.strip(), (nome, "espaço nas pontas", pt[:50])


def test_sanidade_condicoes_continuam_a_abertura():
    """Condição EN: minúscula, sem ponto final, sem 'you'/'if' no começo."""
    for slug in SLUGS:
        d = EX.ler_resultado(slug)
        textos = _lido(ENTRADA / f"{slug}.json")["textos"]
        for lado in ("vale_a_pena", "talvez_evite"):
            for c in (d.get("condicoes") or {}).get(lado) or []:
                en = textos.get(c["texto"])
                if not en:
                    continue
                assert not en.rstrip().endswith("."), (slug, en)
                assert en[0].islower() or en.startswith("I "), (slug, en)
                assert not re.match(r"(?i)(you|if|who)\b", en), (slug, en)


def test_sanidade_temas_sem_ponto_final():
    for slug in SLUGS:
        d = EX.ler_resultado(slug)
        mapas = [_lido(ENTRADA / f"{slug}.json")["textos"],
                 _lido(ENTRADA / "_vocabulario.json")["textos"]]
        for tema in EX.temas_renderizados(d):
            en = next((m[tema] for m in mapas if m.get(tema)), None)
            if en:
                assert not en.rstrip().endswith("."), (slug, en)
