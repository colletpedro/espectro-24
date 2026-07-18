"""
Espectro 24 — Teste de viabilidade (Fase 0)
============================================
Responde, nesta ordem:
  1. Conseguimos acessar a pagina de reviews sem bloqueio de bot?
  2. O filtro por nota na URL funciona? Em qual formato (3.5 vs 3½)?
  3. Conseguimos extrair nota, texto e flag de spoiler de cada review?
  4. Quantas reviews sobrevivem ao filtro de 150+ caracteres?

Uso:
    pip install requests beautifulsoup4
    python teste_viabilidade_espectro24.py oppenheimer-2023
    python teste_viabilidade_espectro24.py <slug-de-outro-filme>

O slug e o que aparece em letterboxd.com/film/<slug>/
"""

import sys
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://letterboxd.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://letterboxd.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Chromium";v="126", "Not(A:Brand";v="24", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}
DELAY = 2.0  # segundos entre requisicoes — seja educado
MIN_CHARS = 150


def get(url: str) -> requests.Response:
    time.sleep(DELAY)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    print(f"  GET {url} -> {resp.status_code}")
    return resp


def teste_1_acesso(slug: str) -> BeautifulSoup | None:
    print("\n[1] Acesso a pagina base de reviews")
    resp = get(f"{BASE}/film/{slug}/reviews/")
    if resp.status_code != 200:
        print(f"  FALHOU: status {resp.status_code}. Anti-bot ou slug errado.")
        return None
    if "just a moment" in resp.text.lower() or "cf-challenge" in resp.text.lower():
        print("  FALHOU: pagina de challenge do Cloudflare retornada.")
        return None
    print("  OK: pagina carregou.")
    return BeautifulSoup(resp.text, "html.parser")


def teste_2_url_por_nota(slug: str) -> None:
    print("\n[2] Formato da URL de filtro por nota")
    candidatos = [
        f"{BASE}/film/{slug}/reviews/rated/3/by/activity/",
        f"{BASE}/film/{slug}/reviews/rated/3.5/by/activity/",
        f"{BASE}/film/{slug}/reviews/rated/3\u00bd/by/activity/",  # 3½
    ]
    for url in candidatos:
        try:
            resp = get(url)
            status = "OK" if resp.status_code == 200 else "nao funciona"
            print(f"    -> {status}")
        except Exception as e:
            print(f"    -> erro: {e}")


def teste_3_extracao(soup: BeautifulSoup) -> list[dict]:
    print("\n[3] Extracao de reviews da pagina base")
    reviews = []

    # Seletores candidatos — a estrutura do Letterboxd muda de tempos em tempos.
    # Estrutura atual (jul/2026): cada review e um <article.production-viewing>.
    # Fallbacks para o layout antigo <li.film-detail> ficam por ultimo.
    # Se nenhum funcionar, o bloco de diagnostico abaixo imprime o HTML cru
    # para voce identificar os seletores atuais.
    itens = (
        soup.select("article.production-viewing")
        or soup.select("li.film-detail")
        or soup.select("div.film-detail-content")
    )

    if not itens:
        print("  Nenhum review encontrado com os seletores conhecidos.")
        print("  DIAGNOSTICO — classes de <li> e <div> presentes na pagina:")
        classes = set()
        for tag in soup.find_all(["li", "div", "article"]):
            for c in tag.get("class", []):
                classes.add(c)
        for c in sorted(classes):
            print(f"    .{c}")
        return []

    for item in itens:
        texto_el = item.select_one(".body-text") or item.select_one(
            ".js-review-body"
        )
        texto = texto_el.get_text(" ", strip=True) if texto_el else ""

        # Nota (jul/2026): <span.inline-rating> com glifos de estrela, ex "★★★½".
        # Cada ★ = 1.0, cada ½ = 0.5. O layout antigo usava classe "rated-N"
        # (N = estrelas*2) em <span.rating> — mantido como fallback.
        nota = None
        rating_el = item.select_one("span.inline-rating") or item.select_one(
            "span.rating"
        )
        if rating_el:
            rating_txt = rating_el.get_text(strip=True)
            if "★" in rating_txt or "½" in rating_txt:
                nota = rating_txt.count("★") + (0.5 if "½" in rating_txt else 0.0)
            else:
                for c in rating_el.get("class", []):
                    if c.startswith("rated-"):
                        nota = int(c.removeprefix("rated-")) / 2

        # Spoiler: procurar aviso textual ou classe de spoiler
        html_item = str(item).lower()
        spoiler = (
            "contains spoilers" in html_item
            or "hidden-spoilers" in html_item
            or "spoiler" in " ".join(
                c for tag in item.find_all(True) for c in tag.get("class", [])
            ).lower()
        )

        reviews.append({"nota": nota, "chars": len(texto), "spoiler": spoiler,
                        "preview": texto[:80]})

    print(f"  {len(reviews)} reviews extraidas. Amostra:")
    for r in reviews[:5]:
        print(f"    nota={r['nota']} chars={r['chars']} spoiler={r['spoiler']} | "
              f"{r['preview']}...")
    return reviews


def teste_4_filtro(reviews: list[dict]) -> None:
    print(f"\n[4] Filtros da spec (min {MIN_CHARS} chars, sem spoiler)")
    com_nota = [r for r in reviews if r["nota"] is not None]
    validas = [r for r in com_nota if r["chars"] >= MIN_CHARS and not r["spoiler"]]
    print(f"  total extraidas:       {len(reviews)}")
    print(f"  com nota:              {len(com_nota)}")
    print(f"  sem spoiler + {MIN_CHARS}+ ch: {len(validas)}")
    if reviews:
        taxa = len(validas) / len(reviews)
        print(f"  taxa de aproveitamento: {taxa:.0%}")
        print(f"  -> para 20 reviews validas por bucket, estime buscar "
              f"~{int(20 / max(taxa, 0.05))} reviews brutas por bucket")


def main() -> None:
    slug = sys.argv[1] if len(sys.argv) > 1 else "oppenheimer-2023"
    print(f"=== Espectro 24 — teste de viabilidade: {slug} ===")

    soup = teste_1_acesso(slug)
    if soup is None:
        print("\nVEREDITO: bloqueado. Proximos passos possiveis: testar com "
              "headers adicionais, curl_cffi (impersonation de TLS), ou "
              "reavaliar IMDB como fonte.")
        sys.exit(1)

    teste_2_url_por_nota(slug)
    reviews = teste_3_extracao(soup)
    if reviews:
        teste_4_filtro(reviews)

    print("\nVEREDITO: se [1]-[4] passaram, a coleta e viavel e a spec pode "
          "ser escrita sem incognitas. Anote qual formato de URL funcionou "
          "no [2] — isso entra na spec.")


if __name__ == "__main__":
    main()
