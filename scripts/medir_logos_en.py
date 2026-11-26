#!/usr/bin/env python3
"""Logos do TMDB para a versão em inglês -> dados/logos_en.json.

Irmão de scripts/medir_editorial.py (reaproveita cliente, escolha, medição de
luminância e classe de contraste), com a ORDEM DE IDIOMA da versão EN:

    en > sem idioma (null)         [pt-BR, pt-PT e qualquer outro idioma NUNCA]

Consulta: /movie/{id}/images?include_image_language=en,null. Desempate dentro
do idioma, como no original: maior vote_average, maior largura, file_path.

Para cada slug publicado grava UMA entrada, sempre:
  * `origem` = "tmdb_en" | "tmdb_sem_idioma" -> `logo_escolhido` preenchido;
  * `origem` = "ausente" -> `logo_escolhido` null: o front em inglês mostra o
    título em texto (`titulo_en`) e NUNCA o logo PT.
`reutiliza_logo_pt` = o logo EN é o mesmo arquivo que o do site em PT.

`titulo_do_logo`: en -> `title` do TMDB (en-US); sem idioma ->
`original_title`. `titulo_difere_do_logo` (EN) = há logo e ele não é `en`.
A classe vem da MEDIÇÃO (override de logos_override.json só vale se o arquivo
for o mesmo do logo PT). Idempotente: respostas e PNGs ficam em dados/cache
(ignorado pelo git); rodar de novo sem rede reaproveita tudo.

Uso: venv/bin/python scripts/medir_logos_en.py
     venv/bin/python scripts/medir_logos_en.py --slug boogie-nights   # só acrescenta/atualiza estes
                                                                      # (as outras entradas ficam como estão)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import medir_editorial as me  # noqa: E402

SAIDA = ROOT / "dados" / "logos_en.json"
LOGOS_PT = ROOT / "dados" / "logos.json"
OVERRIDE = ROOT / "dados" / "logos_override.json"
PUBLICADOS = ROOT / "dados" / "publicados.json"
CACHE_IMAGES_EN = me.CACHE / "_tmdb_images_en"
# cache próprio: dados/cache/_tmdb_detalhe é lido por test_paises_editorial
me.CACHE_DETALHE = me.CACHE / "_tmdb_detalhe_en"
ORDEM_EN = ("en", "sem_idioma")
PAUSA = 0.1  # s entre chamadas de rede (rate limit do TMDB ~50/s; folga larga)


def escolher_logo_en(logos: list[dict]) -> dict | None:
    for idioma in ORDEM_EN:
        doidioma = [l for l in logos if me._idioma(l) == idioma]
        if doidioma:
            return sorted(doidioma, key=lambda l: (-(l.get("vote_average") or 0),
                                                    -(l.get("width") or 0),
                                                    l.get("file_path") or ""))[0]
    return None


def processar(slug: str, key: str, pt: dict, overrides: dict) -> dict:
    ficha = json.loads((me.RESULTADO / f"{slug}.json").read_text(encoding="utf-8"))["ficha"]
    tmdb_id = ficha["tmdb_id"]
    cache = CACHE_IMAGES_EN / f"{tmdb_id}.json"
    if not cache.exists():
        time.sleep(PAUSA)
    imgs = me._get_json_cacheado(cache, f"{me.TMDB_BASE}/movie/{tmdb_id}/images",
                                 {"api_key": key, "include_image_language": "en,null"})
    logos = imgs.get("logos") or []
    disp = {"en": 0, "sem_idioma": 0, "outros_ignorados": 0}
    for l in logos:
        i = me._idioma(l)
        disp[i if i in disp else "outros_ignorados"] += 1
    escolhido = escolher_logo_en(logos)
    reg = {"tmdb_id": tmdb_id, "logos_disponiveis": disp, "logos_total": len(logos),
           "logo_escolhido": None, "idioma_logo": None, "origem": "ausente",
           "reutiliza_logo_pt": False, "titulo_difere_do_logo": False,
           "classe_medida": None, "override": None, "classe": None}
    if not escolhido:
        return reg
    lg = me._registro_logo(escolhido)
    det = lambda: me.detalhe(tmdb_id, key)  # noqa: E731
    lg["titulo_do_logo"] = me.titulo_do_logo(lg["idioma"], ficha, det)
    lg["medida_w500"]["contraste_wcag"] = round(me.razao_contraste(
        lg["medida_w500"]["luminancia_relativa_media"]), 3)
    reg["logo_escolhido"] = lg
    reg["idioma_logo"] = lg["idioma"]
    reg["origem"] = "tmdb_en" if lg["idioma"] == "en" else "tmdb_sem_idioma"
    reg["titulo_difere_do_logo"] = lg["idioma"] != "en"
    reg["classe_medida"] = me.classe_medida(lg["medida_w500"])
    reg["classe"] = reg["classe_medida"]
    pt_esc = (pt.get(slug) or {}).get("logo_escolhido")
    if pt_esc and pt_esc["file_path"] == lg["file_path"]:
        reg["reutiliza_logo_pt"] = True
        ov = overrides.get(slug)
        reg["override"] = ov
        if ov and ov.get("desligar"):
            reg["classe"] = "desligado"
        elif ov and ov.get("classe"):
            reg["classe"] = ov["classe"]
    return reg


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", help="mede só estes slugs e preserva o resto de logos_en.json")
    args = ap.parse_args()
    slugs = json.loads(PUBLICADOS.read_text(encoding="utf-8"))["slugs"]
    if args.slug:
        faltam = [s for s in args.slug if s not in slugs]
        if faltam:
            sys.exit(f"fora de dados/publicados.json: {faltam}")
    pt = json.loads(LOGOS_PT.read_text(encoding="utf-8"))["logos"]
    ov = (json.loads(OVERRIDE.read_text(encoding="utf-8")).get("overrides") or {})
    key = me._api_key()
    if args.slug:
        logos = json.loads(SAIDA.read_text(encoding="utf-8"))["logos"]
        logos.update({s: processar(s, key, pt, ov) for s in args.slug})
    else:
        logos = {s: processar(s, key, pt, ov) for s in sorted(slugs)}
    saida = {
        "_leia": ("Logos do TMDB para a versão EN (scripts/medir_logos_en.py), por "
                  "slug publicado. Ordem de idioma: en > sem idioma (null); pt-BR, "
                  "pt-PT e outros idiomas NUNCA. Mesma medição e classe de "
                  "contraste de dados/logos.json. `origem` = tmdb_en | "
                  "tmdb_sem_idioma | ausente; ausente = sem logo EN: o front "
                  "em inglês usa o título em texto (titulo_en), jamais o logo "
                  "PT. `reutiliza_logo_pt` = mesmo arquivo do logo do site em PT."),
        "consulta": "/movie/{id}/images?include_image_language=en,null",
        "limiares": json.loads(LOGOS_PT.read_text(encoding="utf-8"))["limiares"],
        "logos": logos,
    }
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1, sort_keys=True)
                     + "\n", encoding="utf-8")
    cont = {}
    for r in logos.values():
        cont[r["origem"]] = cont.get(r["origem"], 0) + 1
    print(len(logos), "slugs;", cont, "| reutiliza PT:",
          sum(r["reutiliza_logo_pt"] for r in logos.values()))
    print("ausentes:", sorted(s for s, r in logos.items() if r["origem"] == "ausente"))


if __name__ == "__main__":
    main()
