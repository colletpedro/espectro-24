"""Página estática /en/about (inglês, para quem avalia o pedido de API)."""
import re
from pathlib import Path

FRONT = Path(__file__).resolve().parent.parent / "frontend"
PAGINA = FRONT / "en" / "about" / "index.html"


def test_pagina_existe_em_ingles_com_a_imagem():
    html = PAGINA.read_text(encoding="utf-8")
    assert '<html lang="en">' in html
    assert (PAGINA.parent / "example-alien.png").is_file()
    assert "example-alien.png" in html


def test_pagina_traz_a_frase_sobre_treino_como_pedida():
    html = PAGINA.read_text(encoding="utf-8")
    assert "The data is not used to train any model." in html


def test_rodape_das_paginas_linka_para_o_about():
    for nome in ("index.html", "filme.html", "creditos.html"):
        assert 'href="en/about/"' in (FRONT / nome).read_text(encoding="utf-8"), nome


def test_links_internos_da_pagina_existem():
    html = PAGINA.read_text(encoding="utf-8")
    for alvo in re.findall(r'(?:href|src)="(/[^"#?]+)', html):
        assert (FRONT / alvo.lstrip("/")).exists(), alvo
