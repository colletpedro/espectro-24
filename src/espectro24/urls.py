"""Construção de URLs e chaves de cache (SPEC §2.1, FASE1_INCOGNITAS §A2)."""
from __future__ import annotations

from urllib.parse import quote

from .config import BASE, nota_para_url


def level_page_url(slug: str, nivel: float, page: int) -> str:
    n = nota_para_url(nivel)
    return f"{BASE}/film/{slug}/reviews/rated/{n}/by/activity/page/{page}/"


def level_page_cache_key(slug: str, nivel: float, page: int) -> str:
    n = nota_para_url(nivel).replace(".", "_")
    return f"{slug}/pages/rated_{n}_page_{page}.html"


def full_text_url(path: str) -> str:
    """`path` é o data-full-text-url (ex. '/s/full-text/viewing:123/')."""
    return f"{BASE}{path}"


def full_text_cache_key(slug: str, viewing_id: str) -> str:
    safe = viewing_id.replace(":", "_")
    return f"{slug}/fulltext/{safe}.html"


def search_url(query: str) -> str:
    return f"{BASE}/s/search/films/{quote(query)}/"


def search_cache_key(query: str) -> str:
    safe = quote(query, safe="").replace("%", "_")
    return f"_search/{safe}.html"
