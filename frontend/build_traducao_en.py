#!/usr/bin/env python3
"""Gera frontend/js/data_en.js a partir de dados/traducao_en/*.json.

    window.ESPECTRO_EN = {"vocabulario": {pt: en}, "filmes": {slug: {"titulo_en", "textos": {pt: en}}}}

Só entram traduções NÃO nulas. `fonte_sha256` diferente do `resultado/<slug>.json`
atual significa que o conteúdo do filme foi regenerado depois da tradução: o
build AVISA e mantém só as traduções cujas strings PT ainda existem no
resultado atual (strings idênticas continuam válidas; as que sumiram são
omitidas). Saída determinística (chaves ordenadas, JSON compacto).

Carregado só na versão EN (o `<script>` condicional é da interface). Não toca
em data.js. Offline, zero rede.

Uso: python3 frontend/build_traducao_en.py   (chamado também por build_data.py)
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
ENTRADA = ROOT / "dados" / "traducao_en"
DATA_EN_JS = FRONTEND / "js" / "data_en.js"
DATA_EN_HOME_JS = FRONTEND / "js" / "data_en_home.js"
LOGOS_EN = ROOT / "dados" / "logos_en.json"


def _extrator():
    spec = importlib.util.spec_from_file_location(
        "i18n_extrair_en", ROOT / "scripts" / "i18n_extrair_en.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _preenchidas(mapa: dict) -> dict:
    return {k: v for k, v in (mapa or {}).items() if isinstance(v, str) and v.strip()}


def montar_payload(entrada: Path = ENTRADA, avisar=print) -> dict:
    ex = _extrator()
    slugs = ex.ler_publicados()
    vocab_arq = json.loads((entrada / "_vocabulario.json").read_text(encoding="utf-8")) \
        if (entrada / "_vocabulario.json").exists() else {"textos": {}}
    vocab = _preenchidas(vocab_arq.get("textos"))

    filmes = {}
    for slug in slugs:
        arq = entrada / f"{slug}.json"
        if not arq.exists():
            avisar(f"  AVISO traducao_en: sem arquivo para {slug}")
            continue
        obj = json.loads(arq.read_text(encoding="utf-8"))
        textos = _preenchidas(obj.get("textos"))
        d = ex.ler_resultado(slug)
        if obj.get("fonte_sha256") != ex.sha256_do_resultado(slug):
            vivos = set(ex.textos_do_filme(d))
            sumidos = [k for k in textos if k not in vivos]
            avisar(f"  AVISO traducao_en: {slug} foi regenerado depois da tradução "
                   f"(sha diferente); {len(sumidos)} tradução(ões) omitida(s) por não "
                   f"existir(em) mais no resultado — rode scripts/i18n_extrair_en.py")
            textos = {k: v for k, v in textos.items() if k in vivos}
        entrada_filme = {}
        if obj.get("titulo_en"):
            entrada_filme["titulo_en"] = obj["titulo_en"]
        if textos:
            entrada_filme["textos"] = textos
        if entrada_filme:
            filmes[slug] = entrada_filme
    return {"vocabulario": vocab, "filmes": filmes}


def renderizar(payload: dict) -> str:
    corpo = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return ("// GERADO por frontend/build_traducao_en.py — NÃO editar à mão.\n"
            "// Fonte: dados/traducao_en/*.json. Carregado só na versão EN.\n"
            "window.ESPECTRO_EN = " + corpo + ";\n")


def logos_en(slugs: list[str], caminho: Path = LOGOS_EN) -> dict:
    """{slug: {path, idioma, classe, titulo} | None} a partir de
    dados/logos_en.json (scripts/medir_logos_en.py). Mesma forma de
    `ficha.logo` do índice PT. `None` = sem logo EN: o front em inglês usa o
    título em texto — nunca o logo PT. Slug sem entrada no arquivo é erro."""
    reg = json.loads(caminho.read_text(encoding="utf-8"))["logos"]
    faltam = [s for s in slugs if s not in reg]
    if faltam:
        raise SystemExit(f"logos_en.json sem entrada para: {faltam} — "
                         "rode scripts/medir_logos_en.py")
    saida = {}
    for s in sorted(slugs):
        lg = reg[s].get("logo_escolhido")
        saida[s] = ({"path": lg["file_path"], "idioma": lg["idioma"],
                     "classe": reg[s]["classe"], "titulo": lg.get("titulo_do_logo")}
                    if lg else None)
    return saida


def montar_home(payload: dict) -> dict:
    """O pequeno pacote da home e de /filmes: o nome em inglês de cada gênero
    em uso, o título em inglês de cada filme (sem textos gerados) e o logo
    do TMDB em inglês de cada filme (`logos`, null = título em texto)."""
    ex = _extrator()
    generos = set()
    for slug in ex.ler_publicados():
        generos.update(ex.generos_do_filme(ex.ler_resultado(slug)))
    voc = payload["vocabulario"]
    return {
        "logos": logos_en(ex.ler_publicados()),
        "vocabulario_generos": {g: voc[g] for g in sorted(generos) if g in voc},
        "titulos": {s: f["titulo_en"] for s, f in sorted(payload["filmes"].items())
                    if f.get("titulo_en")},
    }


def renderizar_home(home: dict) -> str:
    corpo = json.dumps(home, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return ("// GERADO por frontend/build_traducao_en.py — NÃO editar à mão.\n"
            "// Fonte: dados/traducao_en/*.json. Carregado só na versão EN (home e /filmes).\n"
            "window.ESPECTRO_EN_HOME = " + corpo + ";\n")


def main(argv=None) -> int:
    payload = montar_payload()
    DATA_EN_JS.write_text(renderizar(payload), encoding="utf-8")
    DATA_EN_HOME_JS.write_text(renderizar_home(montar_home(payload)), encoding="utf-8")
    n = sum(len(f.get("textos", {})) for f in payload["filmes"].values())
    print(f"OK: frontend/js/data_en.js — {len(payload['filmes'])} filmes, "
          f"{n} traduções por filme, {len(payload['vocabulario'])} no vocabulário")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
