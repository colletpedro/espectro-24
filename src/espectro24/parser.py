"""Parsing de HTML do Letterboxd — seletores validados na Fase 1 (FASE1_INCOGNITAS.md).

Todas as funções operam sobre HTML já baixado (string) — zero rede aqui.
"""
from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from .models import Review, SearchResult

# Placeholder EXATO com que o Letterboxd substitui o corpo de uma review
# marcada como spoiler (confirmado em RESULTADO.md / fixtures da Fase 0-1:
# fixtures/oppenheimer-2023_rated5_page2.html, fixtures/synthetic_cases.html).
# v1.1.1: ancorado na frase completa em vez de substring solta — "may contain
# spoilers" sozinho dava falso positivo em prosa legítima (ex.: uma review que
# escreve "this may contain spoilers for the novel" seria descartada à toa).
SPOILER_PLACEHOLDER = "This review may contain spoilers. I can handle the truth."


def _soup(html: str | BeautifulSoup) -> BeautifulSoup:
    return html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "html.parser")


# --- Reviews de uma página de /reviews/rated/N/ ---

def review_elements(soup: BeautifulSoup) -> list[Tag]:
    # atual (jul/2026) + fallback do layout antigo
    return soup.select("article.production-viewing") or soup.select("li.film-detail")


def parse_rating(item: Tag) -> float | None:
    """Nota via glifos de estrela (★=1, ½=0.5). Fallback: classe rated-N (N/2)."""
    el = item.select_one("span.inline-rating") or item.select_one("span.rating")
    if el is None:
        return None
    txt = el.get_text(strip=True)
    if "★" in txt or "½" in txt:
        return txt.count("★") + (0.5 if "½" in txt else 0.0)
    for c in el.get("class", []) or []:
        if c.startswith("rated-"):
            try:
                return int(c.removeprefix("rated-")) / 2
            except ValueError:
                return None
    return None


def _body(item: Tag) -> Tag | None:
    return item.select_one(".body-text") or item.select_one(".js-review-body")


def extract_viewing_id(item: Tag) -> str | None:
    """Id canônico de dedup/cache: p[data-likeable-identifier].uid (universal).

    Fallback: derivar de data-full-text-url (nem sempre presente — ver A1).
    """
    likeable = item.select_one("[data-likeable-identifier]")
    if likeable:
        try:
            uid = json.loads(likeable["data-likeable-identifier"]).get("uid")
            if uid:
                return uid
        except (ValueError, KeyError, TypeError):
            pass
    body = _body(item)
    if body and body.get("data-full-text-url"):
        m = re.search(r"viewing:(\d+)", body["data-full-text-url"])
        if m:
            return f"viewing:{m.group(1)}"
    return None


def is_truncated(item: Tag) -> bool:
    """Detector de truncamento VALIDADO (A3): marcador de colapso `.collapsed-text`.

    NÃO usa data-full-text-url (presente em quase todos os reviews → falsos
    positivos). Reforço: texto visível terminando em reticências.
    """
    body = _body(item)
    if body is None:
        return False
    if body.select_one(".collapsed-text"):
        return True
    return body.get_text(" ", strip=True).rstrip().endswith(("…", "..."))


def full_text_url(item: Tag) -> str | None:
    body = _body(item)
    return body.get("data-full-text-url") if body else None


def is_spoiler_text(text: str) -> bool:
    """Detecta o placeholder EXATO de spoiler do Letterboxd (v1.1.1).

    Ancorado na frase completa `SPOILER_PLACEHOLDER`, não numa substring
    genérica como "may contain spoilers" — essa versão anterior tinha falso
    positivo em prosa legítima que mencionasse a própria palavra "spoiler"
    (ex.: "this may contain spoilers for the novel"). Match sensível a maiúsculas:
    é um texto de interface fixo do Letterboxd, não conteúdo gerado por usuário.

    RESSALVA (ver SPEC.md §2.1 / FASE1_INCOGNITAS.md): se o Letterboxd
    localizar a interface (ex. servir esse placeholder em pt-BR ou outro
    idioma para alguns usuários), este detector para de funcionar em
    silêncio — nenhum teste desta suíte cobre esse cenário, porque o fixture
    de spoiler conhecido nunca localiza junto com o código.
    """
    return SPOILER_PLACEHOLDER in text


def parse_review(item: Tag) -> Review:
    body = _body(item)
    text = body.get_text(" ", strip=True) if body else ""
    lang = body.get("lang") if body else None
    return Review(
        viewing_id=extract_viewing_id(item) or "",
        rating=parse_rating(item),
        text=text,
        truncated=is_truncated(item),
        full_text_url=full_text_url(item),
        spoiler=is_spoiler_text(text),
        lang=lang,
    )


def parse_reviews(html: str | BeautifulSoup) -> list[Review]:
    return [parse_review(el) for el in review_elements(_soup(html))]


# --- Texto completo (endpoint /s/full-text/viewing:<id>/) ---

def parse_full_text(html: str) -> str:
    """O endpoint retorna um fragmento de <p>...</p> sem wrapper."""
    return _soup(html).get_text(" ", strip=True)


# --- Busca de filmes (endpoint AJAX /s/search/films/<query>/) ---

def parse_search_results(html: str | BeautifulSoup) -> list[SearchResult]:
    soup = _soup(html)
    out: list[SearchResult] = []
    for li in soup.select("li.search-result"):
        fig = li.select_one("[data-item-slug]")
        if not fig:
            continue
        slug = fig.get("data-item-slug")
        name = fig.get("data-item-name") or fig.get("data-item-full-display-name") or slug
        link = fig.get("data-item-link") or f"/film/{slug}/"
        year = None
        meta = li.select_one("small.metadata")
        if meta and meta.get_text(strip=True).isdigit():
            year = int(meta.get_text(strip=True))
        else:
            m = re.search(r"\((\d{4})\)", name)
            if m:
                year = int(m.group(1))
        out.append(SearchResult(slug=slug, name=name, year=year, link=link))
    return out
