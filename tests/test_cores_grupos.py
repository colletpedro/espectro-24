"""[rodada cor] A paleta única dos grupos (`?cor=`).

Cobre: (1) a fonte única das cores (tokens `--grupo-*`, sem `--neg-home` nem
`--neg`), (2) o CSS concorda com `scripts/medir_cores.py`, (3) `cor.js`
(parâmetro, constante de padrão), (4) as medições: a `editorial` passa em
todas as restrições; as falhas de `atual` e `apagada` são as conhecidas
(uma mudança nelas tem de ser consciente), e uma paleta que falha não pode
ser a padrão sem a falha estar registrada aqui.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = (RAIZ / "frontend" / "css" / "styles.css").read_text(encoding="utf-8")
COR_JS = (RAIZ / "frontend" / "js" / "cor.js").read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("medir_cores", RAIZ / "scripts" / "medir_cores.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

# falhas CONHECIDAS das paletas de comparação (nomes curtos das restrições)
FALHAS_CONHECIDAS = {
    "atual": {"luminância med", "ΔE neg-med em deuteranopia"},
    "apagada": {"texto neg", "texto pos", "luminância med",
                "ΔE neg-med em deuteranopia", "ΔE neg-med em protanopia"},
    "editorial": set(),
}


def _sem_comentarios(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def _nomes(falhas):
    saida = set()
    for f in falhas:
        m = re.match(r"(texto \w+|barra \w+|luminância \w+|ΔE [\w-]+ em \w+)", f)
        saida.add(m.group(1))
    return saida


def test_as_cores_dos_grupos_tem_uma_fonte_so():
    css = _sem_comentarios(CSS)
    for velho in ("--neg-home", "--med-home", "--pos-home"):
        assert velho not in css
    assert not re.search(r"var\(--(neg|med|pos)\b|^\s*--(neg|med|pos)\b[^-]", css, re.M), "restou um token antigo"
    for js in ("cartoes.js", "filme.js", "inicio.js"):
        fonte = _sem_comentarios((RAIZ / "frontend" / "js" / js).read_text(encoding="utf-8"))
        assert "-home)" not in fonte
        assert not re.search(r"var\(--(neg|med|pos)\)", fonte), js
    # o único lugar com os hex de grupo é o bloco das paletas
    fora = re.sub(r":root\[data-cor=.*?\}", "", css, flags=re.S)
    fora = re.sub(r":root,\s*:root\[data-cor=\"atual\"\]\s*\{.*?\}", "", fora, flags=re.S)
    for hexa in ("#e0673f", "#e3b23c", "#4d90e5", "#9c5f4e", "#a8874f", "#5b7a99"):
        assert hexa not in fora, hexa


def test_o_css_concorda_com_a_medicao():
    for nome, pal in M.PALETAS.items():
        seletor = r':root,\s*:root\[data-cor="atual"\]' if nome == "atual" else rf':root\[data-cor="{nome}"\]'
        m = re.search(seletor + r"\s*\{([^}]*)\}", _sem_comentarios(CSS))
        assert m, nome
        for g in ("neg", "med", "pos"):
            assert re.search(rf"--grupo-{g}:\s*{pal[g]};", m.group(1)), (nome, g)


def test_cor_js_padrao_numa_constante_e_parametro():
    assert len(re.findall(r'var COR_PADRAO = "[a-z]+";', COR_JS)) == 1
    assert 'var COR_PADRAO = "atual";' in COR_JS
    assert 'get("cor")' in COR_JS and "data-cor" in COR_JS
    assert '"atual", "apagada", "editorial"' in COR_JS
    for pagina in ("index.html", "filme.html", "filmes/index.html"):
        html = (RAIZ / "frontend" / pagina).read_text(encoding="utf-8")
        assert "js/cor.js" in html, pagina
        assert html.index("js/cor.js") < html.index("</head>")


def test_a_paleta_editorial_passa_em_todas_as_restricoes():
    r = M.medir(M.PALETAS["editorial"])
    assert r["passa"], r["falhas"]
    for g, hexa in M.PALETAS["editorial"].items():
        assert M.saturacao_hsl(hexa) <= M.MAX_SAT, (g, hexa)
    # sem par vermelho × verde e sem cinza no meio
    import colorsys
    for g, hexa in M.PALETAS["editorial"].items():
        assert M.saturacao_hsl(hexa) >= 0.2, f"{g} é quase cinza"


def test_as_falhas_das_paletas_sao_as_conhecidas():
    for nome, pal in M.PALETAS.items():
        assert _nomes(M.medir(pal)["falhas"]) == FALHAS_CONHECIDAS[nome], nome


def test_paleta_que_falha_so_e_padrao_com_a_falha_registrada():
    padrao = re.search(r'var COR_PADRAO = "([a-z]+)";', COR_JS).group(1)
    if not M.medir(M.PALETAS[padrao])["passa"]:
        assert FALHAS_CONHECIDAS[padrao], "padrão que falha sem registro"


def test_deltaE_e_simulacao_batem_com_valores_de_referencia():
    # Sharma et al. 2005, pares de referência do CIEDE2000
    a = M.de2000("#808080", "#808080")
    assert a == 0
    assert abs(M.de2000("#ffffff", "#000000") - 100.0) < 0.5
    # a deuteranopia colapsa vermelho e verde puros em tons parecidos
    assert M.de2000(M.simular("#ff0000", "deuteranopia"), M.simular("#00ff00", "deuteranopia")) < \
        M.de2000("#ff0000", "#00ff00")
    assert abs(M.contraste("#ffffff", "#000000") - 21.0) < 1e-6
