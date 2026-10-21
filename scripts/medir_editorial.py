#!/usr/bin/env python3
"""[Etapa 0 da rodada editorial] MEDE a matéria-prima da home editorial
para os 99 filmes do catálogo publicado — logos do TMDB, país de produção e
stills deduplicados. Nenhum LLM; nenhum campo publicado existente muda.

Grava:
  * `dados/logos.json` — metadados de logo por slug (versionado);
  * `ficha.paises` em `resultado/{slug}.json` — campo NOVO: a lista de
    códigos ISO 3166-1 de `production_countries`, na ordem do TMDB;
  * caches de rede em `dados/cache/` (sob `.gitignore`):
      `_tmdb_images/{id}.json`  resposta de /movie/{id}/images (pt,en,null)
      `_tmdb_detalhe/{id}.json` resposta de /movie/{id} (production_countries)
      `_logos_w500/`            PNG w500 do logo escolhido, só para medir
      `_stills_w300/`, `_stills_phash.json` (os mesmos de `popular_stills.py`)

Luminância: luma Rec.709 sobre os valores sRGB codificados (sem
linearizar), normalizada em [0, 1]; "pixel escuro" = luma < 0,25. Só entram
os pixels com alfa >= 128 (bordas antisserrilhadas semitransparentes ficam
de fora). A média linear (luminância relativa WCAG) também é gravada, para
referência.

Regra do logo: pt-BR > en > sem idioma (`null`/`xx`). pt-PT NUNCA é
escolhido: o TMDB marca os dois como `pt` e a região vem em `iso_3166_1` da
imagem; `pt` sem região conta como pt-PT (conservador). Sem candidato, o
logo é `null` e o frontend usa o título em texto. Desempate: maior
`vote_average`, maior largura, `file_path`.

Contraste: a razão WCAG do logo contra o fundo escuro de referência
(FUNDO_REFERENCIA, #111111), (L + 0,05) / (L_fundo + 0,05), com L = média da
luminância relativa LINEAR dos pixels visíveis. Classe medida: `claro`
(razão >= LIMIAR_CONTRASTE), `escuro_mono` (abaixo e croma médio — max − min
dos canais, 0–1 — < LIMIAR_CROMA_MONO) ou `escuro_cor` (abaixo e croma >=
LIMIAR_CROMA_MONO). Substitui a classe por luma Rec.709 da etapa anterior,
que pesava o vermelho em 0,21 e classificava vermelho vivo como escuro. A
classe
final é a de `dados/logos_override.json` quando o slug estiver lá, senão a
medida; o override também pode desligar o logo (`classe` = `desligado`).

Uso:
    venv/bin/python scripts/medir_editorial.py            # os 99
    venv/bin/python scripts/medir_editorial.py --slug cure
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from espectro24.ficha import TMDB_BASE, _deduplicar, _still_16_9  # noqa: E402
from espectro24.still_hash import hashes_de  # noqa: E402
from popular_stills import _api_key  # noqa: E402

RESULTADO = ROOT / "resultado"
CACHE = ROOT / "dados" / "cache"
CACHE_IMAGES = CACHE / "_tmdb_images"
CACHE_DETALHE = CACHE / "_tmdb_detalhe"
CACHE_LOGOS = CACHE / "_logos_w500"
MEMO_PHASH = CACHE / "_stills_phash.json"
SAIDA_LOGOS = ROOT / "dados" / "logos.json"
DATA_JS = ROOT / "frontend" / "js" / "data.js"

IMG_W500 = "https://image.tmdb.org/t/p/w500"
OVERRIDE_LOGOS = ROOT / "dados" / "logos_override.json"
LIMIAR_ESCURO = 0.25
ALFA_MIN = 128
# classe de contraste (WCAG contra fundo escuro de referência)
FUNDO_REFERENCIA = "#111111"
LIMIAR_CONTRASTE = 3.0
LIMIAR_CROMA_MONO = 0.15
CLASSES = ("claro", "escuro_mono", "escuro_cor")
ORDEM_IDIOMA = ("pt-BR", "en", "sem_idioma")

_SESSAO = requests.Session()


def catalogo() -> list[str]:
    s = DATA_JS.read_text(encoding="utf-8")
    m = re.search(r'"catalogo":\s*\[(.*?)\]', s, re.S)
    return json.loads("[" + m.group(1) + "]")


def _get_json_cacheado(caminho: Path, url: str, params: dict) -> dict:
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))
    for tentativa in range(4):
        r = _SESSAO.get(url, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(2 ** tentativa)
            continue
        r.raise_for_status()
        dado = r.json()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(dado, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        return dado
    raise RuntimeError(f"{url}: 429 persistente")


def imagens(tmdb_id: int, key: str) -> dict:
    return _get_json_cacheado(
        CACHE_IMAGES / f"{tmdb_id}.json", f"{TMDB_BASE}/movie/{tmdb_id}/images",
        {"api_key": key, "include_image_language": "pt,en,null"})


def detalhe(tmdb_id: int, key: str) -> dict:
    return _get_json_cacheado(
        CACHE_DETALHE / f"{tmdb_id}.json", f"{TMDB_BASE}/movie/{tmdb_id}",
        {"api_key": key})


def _idioma(logo: dict) -> str:
    """`pt-BR`, `pt-PT`, `en`, `sem_idioma` ou o código cru de outro idioma.

    `xx` (sem linguagem) é tratado como `null`. `pt` se divide pela região
    da imagem (`iso_3166_1`): só `BR` é pt-BR; `PT` e `pt` sem região são
    pt-PT — na dúvida, o logo não é tratado como brasileiro."""
    iso = logo.get("iso_639_1")
    if iso in (None, "", "xx"):
        return "sem_idioma"
    if iso == "pt":
        return "pt-BR" if logo.get("iso_3166_1") == "BR" else "pt-PT"
    return iso


def escolher_logo(logos: list[dict]) -> dict | None:
    """pt-BR > en > sem idioma (pt-PT nunca); dentro do idioma, maior
    `vote_average`, depois maior largura, depois `file_path` (desempate
    estável)."""
    for idioma in ORDEM_IDIOMA:
        doidioma = [l for l in logos if _idioma(l) == idioma]
        if doidioma:
            return sorted(doidioma, key=lambda l: (-(l.get("vote_average") or 0),
                                                    -(l.get("width") or 0),
                                                    l.get("file_path") or ""))[0]
    return None


def baixar_png_w500(file_path: str) -> Path:
    """PNG w500 do logo. Para logo SVG, o TMDB serve a versão rasterizada
    trocando a extensão por `.png` — é essa que se mede."""
    png = re.sub(r"\.svg$", ".png", file_path)
    destino = CACHE_LOGOS / png.lstrip("/")
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    r = _SESSAO.get(f"{IMG_W500}{png}", timeout=30)
    r.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    return destino


def medir_luminancia(caminho: Path) -> dict:
    with Image.open(caminho) as im:
        tinha_alfa = im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info
        rgba = np.asarray(im.convert("RGBA"), dtype=np.float64) / 255.0
    rgb, alfa = rgba[..., :3], rgba[..., 3]
    opacos = alfa >= ALFA_MIN / 255.0
    n = int(opacos.sum())
    if n == 0:
        return {"pixels_opacos": 0, "tinha_alfa": tinha_alfa}
    px = rgb[opacos]
    luma = px @ np.array([0.2126, 0.7152, 0.0722])
    vmax, vmin = px.max(axis=1), px.min(axis=1)
    sat = np.where(vmax > 0, (vmax - vmin) / np.where(vmax > 0, vmax, 1), 0.0)
    lin = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    lum_lin = lin @ np.array([0.2126, 0.7152, 0.0722])
    return {
        "luminancia_media": round(float(luma.mean()), 4),
        "fracao_escura": round(float((luma < LIMIAR_ESCURO).mean()), 4),
        "saturacao_media": round(float(sat.mean()), 4),
        "croma_medio": round(float((vmax - vmin).mean()), 4),
        "luminancia_relativa_media": round(float(lum_lin.mean()), 4),
        "pixels_opacos": n,
        "fracao_opaca": round(n / alfa.size, 4),
        "tinha_alfa": tinha_alfa,
        "largura_medida": int(rgba.shape[1]),
        "altura_medida": int(rgba.shape[0]),
    }


def _registro_logo(logo: dict) -> dict:
    reg = {
        "file_path": logo["file_path"],
        "idioma": _idioma(logo),
        "iso_639_1_original": logo.get("iso_639_1"),
        "iso_3166_1": logo.get("iso_3166_1"),
        "file_type": logo.get("file_type")
                     or Path(logo["file_path"]).suffix.lstrip("."),
        "largura": logo.get("width"),
        "altura": logo.get("height"),
        "vote_average": logo.get("vote_average"),
        "vote_count": logo.get("vote_count"),
    }
    try:
        reg["medida_w500"] = medir_luminancia(baixar_png_w500(logo["file_path"]))
    except Exception as e:  # registra, não derruba os outros 98
        reg["medida_w500"] = {"erro": f"{type(e).__name__}: {e}"}
    return reg


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminancia_relativa_hex(cor: str) -> float:
    r, g, b = (int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def razao_contraste(l_logo: float, fundo: str = FUNDO_REFERENCIA) -> float:
    """Razão WCAG do logo (o mais claro dos dois sobre um fundo escuro)."""
    l_fundo = luminancia_relativa_hex(fundo)
    claro, escuro = max(l_logo, l_fundo), min(l_logo, l_fundo)
    return (claro + 0.05) / (escuro + 0.05)


def titulo_do_logo(idioma: str, ficha: dict, detalhe_tmdb) -> str | None:
    """O título que o LOGO escreve, pelo idioma dele: pt-BR → o título da
    ficha (que é o pt-BR do TMDB); en → o `title` do TMDB (en-US, o idioma
    padrão de /movie/{id}); sem idioma → o `original_title`. É a base da
    comparação que decide se o título brasileiro se repete na linha da
    manchete (selecao.js, `tituloNaLinha`)."""
    if idioma == "pt-BR":
        return ficha.get("titulo")
    det = detalhe_tmdb()
    return det.get("title") if idioma == "en" else det.get("original_title")


def classe_medida(medida: dict) -> str | None:
    lum, croma = medida.get("luminancia_relativa_media"), medida.get("croma_medio")
    if lum is None or croma is None:
        return None
    if razao_contraste(lum) >= LIMIAR_CONTRASTE:
        return "claro"
    return "escuro_mono" if croma < LIMIAR_CROMA_MONO else "escuro_cor"


def ler_overrides(slugs: list[str]) -> dict:
    """`{slug: {"classe": <classe>} | {"desligar": true}}`, validado —
    override com slug fora do catálogo ou classe desconhecida é erro, não
    é ignorado em silêncio."""
    if not OVERRIDE_LOGOS.exists():
        return {}
    ov = json.loads(OVERRIDE_LOGOS.read_text(encoding="utf-8")).get("overrides") or {}
    for slug, o in ov.items():
        if slug not in slugs:
            raise SystemExit(f"logos_override: slug fora do catálogo: {slug}")
        if set(o) - {"classe", "desligar", "motivo"}:
            raise SystemExit(f"logos_override: chave desconhecida em {slug}: {o}")
        if "classe" in o and o["classe"] not in CLASSES:
            raise SystemExit(f"logos_override: classe inválida em {slug}: {o}")
        if "classe" not in o and not o.get("desligar"):
            raise SystemExit(f"logos_override: {slug} sem `classe` nem `desligar`")
    return ov


def stills_deduplicados(imgs: dict) -> dict:
    """Mesmo filtro e mesma dedup de `ficha._stills` (sem idioma, 16:9,
    pHash <= 14), mas SEM teto nem piso: é o pool disponível."""
    candidatos = [b for b in (imgs.get("backdrops") or [])
                  if b.get("file_path") and b.get("iso_639_1") is None
                  and _still_16_9(b)]
    candidatos.sort(key=lambda b: (-(b.get("vote_average") or 0), b["file_path"]))
    hashes = hashes_de([b["file_path"] for b in candidatos], memo=MEMO_PHASH)
    dedup = _deduplicar(candidatos, hashes)
    return {"candidatos_16_9": len(candidatos),
            "sem_hash": len(candidatos) - len(hashes),
            "deduplicados": len(dedup)}


def processar(slug: str, key: str) -> dict:
    caminho = RESULTADO / f"{slug}.json"
    texto = caminho.read_text(encoding="utf-8")
    d = json.loads(texto)
    ficha = d["ficha"]
    tmdb_id = ficha["tmdb_id"]

    imgs = imagens(tmdb_id, key)
    logos = imgs.get("logos") or []
    por_idioma = {"pt-BR": 0, "pt-PT": 0, "pt_sem_pais": 0, "en": 0,
                  "sem_idioma": 0}
    for l in logos:
        chave = _idioma(l)
        if l.get("iso_639_1") == "pt" and not l.get("iso_3166_1"):
            por_idioma["pt_sem_pais"] += 1      # contado também em pt-PT
        if chave in por_idioma:
            por_idioma[chave] += 1
    escolhido = escolher_logo(logos)
    reg_logo = _registro_logo(escolhido) if escolhido else None
    if reg_logo:
        reg_logo["titulo_do_logo"] = titulo_do_logo(reg_logo["idioma"], ficha,
                                                    lambda: detalhe(tmdb_id, key))

    # país: campo NOVO (lista de códigos ISO 3166-1, na ordem do TMDB). O
    # formato anterior desta rodada (objetos com nome) nunca foi commitado e
    # é reescrito; qualquer outro valor já presente fica como está.
    paises_novos = False
    atual = ficha.get("paises")
    if atual is None or (atual and isinstance(atual[0], dict)):
        det = detalhe(tmdb_id, key)
        ficha["paises"] = [c["iso_3166_1"]
                           for c in det.get("production_countries") or []]
        # mesma serialização do arquivo de origem (o final de linha varia
        # entre os arquivos), para o diff ser SÓ o campo novo
        fim = "\n" if texto.endswith("\n") else ""
        caminho.write_text(json.dumps(d, ensure_ascii=False, indent=2) + fim,
                           encoding="utf-8")
        paises_novos = True

    return {
        "slug": slug,
        "tmdb_id": tmdb_id,
        "logos_disponiveis": por_idioma,
        "logos_total": len(logos),
        "logo_escolhido": reg_logo,
        "_paises_gravados_agora": paises_novos,
        "_stills": stills_deduplicados(imgs),
        "_stills_publicados": len(ficha.get("galeria_stills") or []),
        "_diretor": bool(ficha.get("diretor")),
        "_duracao": ficha.get("duracao_min"),
        "_paises": ficha.get("paises") or [],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    args = ap.parse_args()
    key = _api_key()
    slugs = [args.slug] if args.slug else catalogo()

    overrides = ler_overrides(catalogo())
    regs = [processar(s, key) for s in slugs]
    for r in regs:
        logo = r["logo_escolhido"]
        r["idioma_logo"] = logo["idioma"] if logo else None
        r["titulo_difere_do_logo"] = bool(logo) and logo["idioma"] != "pt-BR"
        medida = classe_medida(logo["medida_w500"]) if logo else None
        if logo and "luminancia_relativa_media" in logo["medida_w500"]:
            logo["medida_w500"]["contraste_wcag"] = round(razao_contraste(
                logo["medida_w500"]["luminancia_relativa_media"]), 3)
        ov = overrides.get(r["slug"])
        r["classe_medida"] = medida
        r["override"] = ov
        if ov and ov.get("desligar"):
            r["classe"] = "desligado"
        elif ov:
            r["classe"] = ov["classe"]
        else:
            r["classe"] = medida

    if not args.slug:
        saida = {
            "_leia": ("Etapa 0 da rodada editorial (scripts/medir_editorial.py). "
                      "Logo do TMDB por slug: disponibilidade por idioma e o "
                      "escolhido (pt-BR > en > sem idioma; pt-PT e pt sem "
                      "país nunca; vote_average, largura). Luminância = luma "
                      "Rec.709 sRGB em [0,1] dos pixels com alfa >= 128 do PNG "
                      "w500; fracao_escura = luma < 0,25; saturação = S do HSV. "
                      "classe medida = razão WCAG (luminância relativa linear "
                      "média vs. #111111) >= 3,0 → claro; abaixo, croma médio "
                      "(max − min) < 0,15 → escuro_mono, senão escuro_cor. "
                      "classe = override (dados/logos_override.json) ou a "
                      "medida; titulo_difere_do_logo = há logo e ele não é "
                      "pt-BR."),
            "consulta": "/movie/{id}/images?include_image_language=pt,en,null",
            "limiares": {"fundo_referencia": FUNDO_REFERENCIA,
                         "contraste_claro": LIMIAR_CONTRASTE,
                         "croma_mono": LIMIAR_CROMA_MONO,
                         "luma_pixel_escuro": LIMIAR_ESCURO,
                         "alfa_visivel": ALFA_MIN},
            "logos": {r["slug"]: {k: v for k, v in r.items()
                                  if not k.startswith("_") and k != "slug"}
                      for r in regs},
        }
        SAIDA_LOGOS.write_text(json.dumps(saida, ensure_ascii=False, indent=1)
                               + "\n", encoding="utf-8")
    medida = CACHE / "_medida_editorial.json"
    medida.write_text(json.dumps(regs, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print(f"{len(regs)} filmes; medida completa em {medida.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
