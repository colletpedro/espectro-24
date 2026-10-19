#!/usr/bin/env python3
"""[home nova, rodada 3] Retrofit da DATA DE ESTREIA COMPLETA na ficha de
`resultado/*.json` já publicados.

A ficha guardava só o ANO de estreia (`ficha.py` lia o `release_date` do
TMDB e descartava dia e mês). O gancho de aniversário da home precisa da
data inteira. Este harness faz, por filme publicado, **uma** chamada
`GET /movie/{tmdb_id}` ao TMDB — com o `tmdb_id` JÁ PUBLICADO, sem reabrir a
desambiguação nem a prova de identidade — e grava **uma** chave nova dentro
de `ficha`:

    data_estreia   (AAAA-MM-DD do `release_date`, ou null se vazio)

**Nada mais muda, e isso é conferido antes de gravar**, no mesmo espírito de
`enriquecer_ficha.py`: o documento é comparado campo a campo, e o arquivo
reescrito tem de ser byte a byte o original com UMA linha a mais. Qualquer
outra diferença aborta sem gravar. Não roda LLM, não coleta Letterboxd, não
republica, não toca `dados/bruto/`.

**O ANO PUBLICADO NÃO É SOBRESCRITO.** O ano derivado da data nova é
comparado com `ficha.ano` e as divergências são LISTADAS (caso conhecido:
`talk-to-me-2022`, Letterboxd 2022, TMDB 2023). A data entra como dado novo
mesmo quando diverge: o `ano` publicado é a escolha editorial (Letterboxd,
v1.9.49) e o `release_date` do TMDB é outra grandeza.

**`tmdb_fetched_at` NÃO é atualizado** — ele data a ficha inteira, e a ficha
inteira não foi rebuscada. A data desta consulta fica registrada na saída do
harness e no commit.

**O cache local do TMDB (`dados/cache/_tmdb/`, fora do git) recebe a mesma
chave** nas entradas do mesmo `tmdb_id`. `ficha.py` passou a exigir
`data_estreia` numa entrada completa (`_CHAVES_COMPLETUDE`); sem este passo,
toda entrada antiga viraria miss, e uma republicação futura refaria a ficha
inteira em vez de reaproveitar a que está publicada.

Uso:
    python scripts/backfill_data_estreia.py              # simula e lista
    python scripts/backfill_data_estreia.py --gravar     # grava
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

RESULTADO_DIR = RAIZ / "resultado"
CACHE_DIR = RAIZ / "dados" / "cache" / "_tmdb"
DATA_JS = RAIZ / "frontend" / "js" / "data.js"

CHAVE = "data_estreia"
_DATA_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class Abortado(Exception):
    pass


def catalogo_publicado(data_js: Path = DATA_JS) -> list[str]:
    """Os slugs do catálogo PUBLICADO (o `catalogo` de `data.js`)."""
    texto = data_js.read_text(encoding="utf-8")
    return json.loads(texto[texto.index("=") + 1:].strip().rstrip(";"))["catalogo"]


def _serializar(doc: dict) -> str:
    # O MESMO formato de `render.write_json` e do cache de `ficha.py`.
    return json.dumps(doc, ensure_ascii=False, indent=2)


def com_data(ficha: dict, data: str | None) -> dict:
    """A ficha com `data_estreia` logo depois de `ano` (a ordem de
    `_montar_ficha`); sem `ano`, no fim. Substitui se já existir."""
    saida = {}
    for k, v in ficha.items():
        if k == CHAVE:
            continue
        saida[k] = v
        if k == "ano":
            saida[CHAVE] = data
    if CHAVE not in saida:
        saida[CHAVE] = data
    return saida


def buscar_release_date(session, api_key: str, tmdb_id: int) -> str | None:
    from espectro24.ficha import TMDB_BASE, _get_json
    detalhes = _get_json(session, f"{TMDB_BASE}/movie/{tmdb_id}",
                         {"api_key": api_key, "language": "pt-BR"})
    if detalhes.get("id") != tmdb_id:
        raise Abortado(f"TMDB devolveu id {detalhes.get('id')} para {tmdb_id}")
    data = detalhes.get("release_date") or ""
    return data if _DATA_RE.fullmatch(data) else None


def reescrever(caminho: Path, doc: dict, ficha_nova: dict, gravar: bool,
               ficha_em=lambda d: d["ficha"], por_ficha=None) -> bool:
    """Troca a ficha de `doc` por `ficha_nova` e grava se — e só se — o
    resultado for o original com UMA linha a mais (a da data). Devolve
    True se gravou (ou gravaria)."""
    original = caminho.read_text(encoding="utf-8")
    # 18 dos `resultado/*.json` terminam com "\n" (gravados fora de
    # `write_json`); o final de linha do arquivo é preservado como está.
    fim = "\n" if original.endswith("\n") else ""
    if _serializar(doc) + fim != original:
        raise Abortado(f"{caminho.name}: o arquivo não é reproduzível pelo "
                       "formato de write_json — gravar mudaria mais do que a data")
    antiga = ficha_em(doc)
    sem_chave = {k: v for k, v in ficha_nova.items() if k != CHAVE}
    if sem_chave != {k: v for k, v in antiga.items() if k != CHAVE}:
        raise Abortado(f"{caminho.name}: a ficha mudaria além de {CHAVE}")
    novo_doc = por_ficha(doc, ficha_nova) if por_ficha else {**doc, "ficha": ficha_nova}
    novo = _serializar(novo_doc) + fim
    if CHAVE not in antiga:
        a, b = original.splitlines(), novo.splitlines()
        extras = [l for l in b if l not in a]
        if len(b) != len(a) + 1 or len(extras) != 1 or f'"{CHAVE}"' not in extras[0]:
            raise Abortado(f"{caminho.name}: o diff não é UMA linha de {CHAVE}")
    if novo == original:
        return False
    if gravar:
        caminho.write_text(novo, encoding="utf-8")
    return True


def entradas_de_cache(tmdb_id: int, cache_dir: Path = CACHE_DIR) -> list[Path]:
    saida = []
    for p in sorted(cache_dir.glob("*.json")) if cache_dir.exists() else []:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if isinstance(d, dict) and d.get("tmdb_id") == tmdb_id:
            saida.append(p)
    return saida


def processar(slugs, session, api_key, *, gravar: bool,
              resultado_dir: Path = RESULTADO_DIR,
              cache_dir: Path = CACHE_DIR) -> list[dict]:
    relatorio = []
    for slug in slugs:
        caminho = resultado_dir / f"{slug}.json"
        doc = json.loads(caminho.read_text(encoding="utf-8"))
        ficha = doc.get("ficha")
        if not ficha or not ficha.get("tmdb_id"):
            relatorio.append({"slug": slug, "ok": False, "motivo": "sem ficha/tmdb_id"})
            continue
        try:
            data = buscar_release_date(session, api_key, ficha["tmdb_id"])
            ano_data = int(data[:4]) if data else None
            r = {"slug": slug, "ok": True, "tmdb_id": ficha["tmdb_id"],
                 "data_estreia": data, "ano_publicado": ficha.get("ano"),
                 "ano_da_data": ano_data,
                 "diverge": bool(data) and ano_data != ficha.get("ano")}
            # Confere TUDO antes de gravar QUALQUER arquivo deste filme.
            alvos = [(caminho, doc, com_data(ficha, data), {})]
            for p in entradas_de_cache(ficha["tmdb_id"], cache_dir):
                c = json.loads(p.read_text(encoding="utf-8"))
                alvos.append((p, c, com_data(c, data),
                              {"ficha_em": lambda d: d, "por_ficha": lambda d, f: f}))
            for alvo, d, f, kw in alvos:
                reescrever(alvo, d, f, False, **kw)
            r["gravou"] = reescrever(caminho, doc, alvos[0][2], gravar)
            r["cache"] = [a.name for a, d, f, kw in alvos[1:]
                          if reescrever(a, d, f, gravar, **kw)]
        except Abortado as e:
            r = {"slug": slug, "ok": False, "motivo": str(e)}
        relatorio.append(r)
    return relatorio


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gravar", action="store_true",
                    help="grava (sem isto, só consulta e lista)")
    ap.add_argument("--slug", action="append", help="slug (repetível)")
    args = ap.parse_args()

    import os
    import requests
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    chave = os.environ.get("TMDB_API_KEY")
    if not chave:
        raise SystemExit("TMDB_API_KEY ausente")

    slugs = args.slug or catalogo_publicado()
    with requests.Session() as s:
        rel = processar(slugs, s, chave, gravar=args.gravar)

    com = [r for r in rel if r.get("ok") and r["data_estreia"]]
    print(json.dumps(rel, ensure_ascii=False, indent=1))
    print(f"\n{len(com)}/{len(slugs)} com data · "
          f"{sum(1 for r in rel if r.get('diverge'))} divergências de ano · "
          f"{sum(len(r.get('cache', [])) for r in rel)} entradas de cache"
          + ("" if args.gravar else "  (SIMULAÇÃO — nada gravado)"))


if __name__ == "__main__":
    main()
