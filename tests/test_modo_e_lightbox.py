"""[v1.9.43] OS DOIS MODOS DA PÁGINA e o MODO TELA CHEIA da galeria.

Cobre as quatro mudanças autorizadas nesta versão que não cabem em
`test_faixa_stills.py` (velocidade e pausa, executadas sob node) nem em
`test_hero_faixa_frontend.py` (estrutura do hero):

  1. a faixa é full-bleed e SÓ ela — nada mais na página muda de largura;
  4. abaixo de 1024px o hero volta a ser estático e a galeria reaparece
     embaixo; acima, a galeria não é construída (não é escondida);
  4b. o modo tela cheia: abre, navega, fecha por três caminhos, trava o
     scroll de trás e devolve o foco.

As funções PURAS do lightbox são EXECUTADAS sob node — decidir o que um
gesto quer dizer é aritmética, e aritmética se testa rodando, não lendo.
O resto é estrutural, pela mesma razão de sempre (o projeto não tem
runner de JS com DOM).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FILME_JS = RAIZ / "frontend" / "js" / "filme.js"
POSTER_JS = RAIZ / "frontend" / "js" / "poster.js"
LIGHTBOX_JS = RAIZ / "frontend" / "js" / "lightbox.js"
CSS = RAIZ / "frontend" / "css" / "styles.css"


def _txt(p):
    return p.read_text(encoding="utf-8")


def _sem_comentarios(fonte):
    fonte = re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    return re.sub(r"//.*", "", fonte)


def _corpo(fonte, nome, fecho="\n  }"):
    m = re.search(r"function " + nome + r"\(.*?\) \{(.*?)" + re.escape(fecho),
                  fonte, re.S)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _regra(css, seletor):
    m = re.search(re.escape(seletor) + r"\s*\{(.*?)\}", css, re.S)
    assert m, f"regra {seletor} não encontrada"
    return m.group(1)


# =====================================================================
# 1. FULL-BLEED — e só a faixa
# =====================================================================

def test_a_caixa_da_faixa_e_full_bleed():
    bloco = _regra(_txt(CSS), ".hero-faixa-caixa")
    assert "width: 100vw" in bloco
    assert "margin-left: calc(50% - 50vw)" in bloco
    assert "margin-right: calc(50% - 50vw)" in bloco


def test_a_altura_do_hero_nao_acompanha_a_largura():
    """O pedido foi explícito: mantém a ALTURA e o tamanho de item atuais.
    Se a proporção 16:9 governasse a caixa full-bleed, o hero teria 810px
    de altura a 1440 e 1440px a 2560 — engoliria a página."""
    bloco = _regra(_txt(CSS), ".hero-faixa-caixa")
    assert "height: var(--hero-faixa-h)" in bloco
    assert "aspect-ratio: auto !important" in bloco, (
        "sem neutralizar a proporção inline, a altura volta a seguir a "
        "largura da janela")
    raiz = _regra(_txt(CSS), ":root")
    assert "--hero-faixa-h: 405px" in raiz
    assert "--hero-faixa-item-w: 720px" in raiz


def test_o_quadro_mantem_a_largura_de_antes():
    bloco = _regra(_txt(CSS), ".hero-faixa .hero-still")
    assert "flex: 0 0 var(--hero-faixa-item-w)" in bloco
    assert "100%" not in bloco, (
        "o quadro voltou a ocupar a faixa inteira — com full-bleed isso "
        "faz um quadro só encher a janela, o oposto do efeito pedido")


def test_so_a_faixa_e_full_bleed_e_o_resto_nao_muda_de_largura():
    """`100vw` só pode aparecer na caixa da faixa (e no `sizes` das
    imagens, que é outra coisa). Se outro bloco da página ganhasse
    largura de janela, a promessa 'nada mais muda' teria sido quebrada."""
    css = _sem_comentarios(_txt(CSS))
    donos = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        if "100vw" in m.group(2):
            donos.append(m.group(1).strip().splitlines()[-1].strip())
    assert donos == [".hero-faixa-caixa"], (
        f"outros seletores ganharam largura de janela: {donos}")


def test_o_body_apara_o_transbordo_de_100vw():
    """`100vw` inclui a barra de rolagem; sem aparar, a página inteira
    ganha alguns pixels de rolagem horizontal. `clip` e não `hidden`:
    `hidden` faria do body um contêiner de rolagem e quebraria `sticky`."""
    bloco = _regra(_txt(CSS), "body")
    assert "overflow-x: clip" in bloco
    assert "overflow-x: hidden" not in bloco


# =====================================================================
# 4. OS DOIS MODOS
# =====================================================================

def test_o_ponto_de_corte_e_1024_e_esta_num_lugar_so():
    fonte = _txt(FILME_JS)
    assert 'var MQ_MODO_FAIXA = "(min-width: 1024px)";' in fonte
    # o listener usa a MESMA expressão — dois valores divergentes deixariam
    # a página num modo e o observador em outro
    # o valor aparece UMA vez só: o listener usa a constante, não repete a
    # string. Duas cópias divergentes deixariam a página num modo e o
    # observador em outro.
    assert fonte.count("(min-width: 1024px)") == 1, (
        "o breakpoint foi duplicado — o listener deve usar MQ_MODO_FAIXA")
    assert "window.matchMedia(MQ_MODO_FAIXA)" in fonte


def test_a_faixa_so_e_construida_no_modo_faixa():
    fonte = _txt(FILME_JS)
    assert "(ehModoFaixa() ? heroFaixa(f, ano) : null)" in fonte


def test_a_galeria_do_mobile_nao_e_construida_no_desktop():
    """NÃO é `display: none`. Escondida, o navegador baixaria 12 imagens
    que ninguém veria."""
    corpo = _corpo(_txt(FILME_JS), "aplicarModoGaleria")
    assert "var precisa = !ehModoFaixa();" in corpo
    assert "galeriaEl.remove()" in corpo
    css = _sem_comentarios(_txt(CSS))
    m = re.search(r"\.galeria-mobile\s*\{([^}]*)\}", css)
    assert m and "display: none" not in m.group(1), (
        "a galeria passou a ser escondida por CSS em vez de não construída")


def test_a_troca_de_modo_e_idempotente():
    """Reconciliar não pode reconstruir o hero quando o modo já está
    certo: cada reconstrução troca o `<img>` por um igual e o topo da
    página pisca."""
    corpo = _corpo(_txt(FILME_JS), "aplicarModoHero")
    assert "if (temFaixa === ehModoFaixa()) return;" in corpo
    corpo_g = _corpo(_txt(FILME_JS), "aplicarModoGaleria")
    assert "if (precisa === !!galeriaEl) return;" in corpo_g


def test_a_reconciliacao_nao_depende_de_requestAnimationFrame():
    """rAF não roda em aba oculta: uma página aberta em segundo plano
    ficaria presa no modo de parse até ganhar foco."""
    fonte = _txt(FILME_JS)
    assert "setTimeout(function () { aoTrocarModo(film); }, 0);" in fonte
    assert "requestAnimationFrame(function () { aoTrocarModo" not in fonte


def test_a_troca_ao_vivo_escuta_media_query_E_resize():
    fonte = _txt(FILME_JS)
    assert 'mql.addEventListener("change", reconciliar)' in fonte
    assert 'mql.addListener(reconciliar)' in fonte      # Safari antigo
    assert 'window.addEventListener("resize", reconciliar);' in fonte


def test_a_galeria_do_mobile_e_uma_coluna_com_respiro():
    """'Não é fileira de miniaturas': uma coluna, borda a borda, com
    espaço entre os itens."""
    bloco = _regra(_txt(CSS), ".galeria-mobile__lista")
    assert "grid-template-columns: 1fr" in bloco
    assert re.search(r"gap: \d+px", bloco)
    assert "width: calc(100% + 40px)" in bloco, (
        "os itens deixaram de ir de borda a borda")


def test_cada_item_da_galeria_e_um_botao():
    """Abrir tela cheia é ação: precisa estar no fluxo de teclado e
    responder a Enter/Espaço sem que a gente reimplemente isso."""
    corpo = _corpo(_txt(FILME_JS), "galeriaMobileBlock")
    assert 'document.createElement("button")' in corpo
    assert 'botao.type = "button"' in corpo
    assert ".galeria-mobile__item:focus-visible" in _txt(CSS)


def test_a_galeria_do_mobile_nao_renderiza_sem_stills():
    """Mesmo contrato de sempre — `talk-to-me-2022`."""
    corpo = _corpo(_txt(FILME_JS), "galeriaMobileBlock")
    guarda = re.search(r"if \(!itens\.length\) return null;", corpo)
    section = re.search(r'createElement\("section"\)', corpo)
    assert guarda and section and guarda.start() < section.start()


# =====================================================================
# 4b. MODO TELA CHEIA — núcleo puro, executado sob node
# =====================================================================

pytest_node = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node ausente — o núcleo puro do lightbox não pôde ser EXECUTADO")


def _node(corpo: str):
    script = textwrap.dedent(f"""
        const L = require({json.dumps(str(LIGHTBOX_JS))});
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, f"node falhou:\n{r.stderr}"
    return json.loads(r.stdout)


@pytest_node
def test_o_gesto_de_fechar_e_vertical_e_longo():
    """Um swipe lateral levemente torto NÃO pode fechar — navegar é o
    gesto que mais se usa aqui."""
    out = _node("""
        console.log(JSON.stringify({
            baixo_longo: L.gestoFecha(0, 120),
            baixo_curto: L.gestoFecha(0, 40),
            cima: L.gestoFecha(0, -120),
            lateral_torto: L.gestoFecha(100, 120),
            lateral_puro: L.gestoFecha(200, 10),
            limiar: L.FECHAR_PX,
        }));
    """)
    assert out["baixo_longo"] is True
    assert out["baixo_curto"] is False, "gesto curto fecharia por engano"
    assert out["cima"] is False
    assert out["lateral_torto"] is False
    assert out["lateral_puro"] is False
    assert out["limiar"] >= 60


@pytest_node
def test_a_navegacao_nao_circula_nas_pontas():
    """As setas do teclado precisam concordar com o swipe nativo, que
    para nas pontas. Se um circulasse e o outro não, os dois discordariam
    sobre onde a pessoa está."""
    out = _node("""
        console.log(JSON.stringify({
            primeiro_esquerda: L.proximoIndice(0, -1, 12),
            ultimo_direita: L.proximoIndice(11, 1, 12),
            meio_direita: L.proximoIndice(5, 1, 12),
            meio_esquerda: L.proximoIndice(5, -1, 12),
        }));
    """)
    assert out["primeiro_esquerda"] == 0
    assert out["ultimo_direita"] == 11
    assert out["meio_direita"] == 6 and out["meio_esquerda"] == 4


@pytest_node
def test_o_indice_visivel_sai_da_posicao_de_rolagem():
    out = _node("""
        console.log(JSON.stringify({
            zero: L.indiceVisivel(0, 375, 12),
            terceiro: L.indiceVisivel(750, 375, 12),
            meio_do_caminho: L.indiceVisivel(700, 375, 12),
            alem_do_fim: L.indiceVisivel(99999, 375, 12),
            largura_zero: L.indiceVisivel(500, 0, 12),
        }));
    """)
    assert out["zero"] == 0 and out["terceiro"] == 2
    assert out["meio_do_caminho"] == 2      # arredonda para o mais próximo
    assert out["alem_do_fim"] == 11
    assert out["largura_zero"] == 0


# --- estrutura do modo tela cheia ------------------------------------

def test_o_lightbox_e_um_dialogo_modal_com_botao_de_fechar():
    corpo = _corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }")
    assert 'setAttribute("role", "dialog")' in corpo
    assert 'setAttribute("aria-modal", "true")' in corpo
    assert 'className = "lightbox__fechar"' in corpo
    assert 'setAttribute("aria-label", "Fechar")' in corpo


def test_o_lightbox_trava_o_scroll_de_tras_e_destrava_ao_fechar():
    corpo = _corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }")
    assert 'document.body.classList.add("lightbox-aberto")' in corpo
    assert 'document.body.classList.remove("lightbox-aberto")' in corpo
    assert "body.lightbox-aberto" in _txt(CSS)
    assert "overflow: hidden" in _regra(_txt(CSS), "body.lightbox-aberto")


def test_o_lightbox_devolve_o_foco_ao_item_de_origem():
    corpo = _corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }")
    assert "var anterior = origem || document.activeElement;" in corpo
    assert "if (anterior && anterior.focus) anterior.focus();" in corpo


def test_esc_fecha_e_as_setas_navegam():
    corpo = _corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }")
    assert 'e.key === "Escape"' in corpo
    assert 'e.key === "ArrowRight" || e.key === "ArrowLeft"' in corpo
    assert 'document.addEventListener("keydown", aoTeclado, true)' in corpo
    assert 'document.removeEventListener("keydown", aoTeclado, true)' in corpo, (
        "o listener de teclado fica pendurado depois de fechar")


def test_o_lightbox_nao_tem_indicador_nem_seta_nem_contador():
    """A proibição vale aqui também. O botão de fechar é o ÚNICO controle
    visível, e é exigido por extenso."""
    corpo = _sem_comentarios(_corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }"))
    # UM botão: o de fechar
    assert corpo.count('createElement("button")') == 1, (
        "apareceu um segundo botão no modo tela cheia")
    # e três tipos de elemento no total: div (caixa), div (quadro), img
    criados = sorted(set(re.findall(r'createElement\("(\w+)"\)', corpo)))
    assert criados == ["button", "div", "img"], (
        f"o modo tela cheia criou outros elementos: {criados}")
    # a varredura de palavra roda sobre o que é RENDERIZADO (classes e
    # texto), não sobre o código inteiro: `ArrowRight` é nome de tecla, e
    # casar com ele proibiria navegar por teclado.
    renderizado = " ".join(re.findall(r'className = "([^"]*)"', corpo) +
                           re.findall(r'textContent = "([^"]*)"', corpo))
    for proibido in ("dot", "indicador", "contador", "arrow", "seta",
                     "prev", "next"):
        assert proibido not in renderizado.lower(), (
            f"{proibido!r} apareceu em algo renderizado: {renderizado!r}")


def test_o_lightbox_carrega_sob_demanda_pelo_src_e_nao_so_pelo_lazy():
    """REGRESSÃO de um defeito medido: com `loading="lazy"` apenas, abrir
    o modo disparou as 12 imagens de uma vez — o limiar do lazy nativo
    cobre o trilho inteiro numa conexão rápida. `lazy` é dica; o teto tem
    de estar no `src`."""
    corpo = _corpo(_txt(LIGHTBOX_JS), "abrir", fecho="\n  }")
    assert "img.dataset.src = it.src;" in corpo
    assert re.search(r"function garantirVizinhanca\(centro\)", corpo)
    assert "garantirVizinhanca(indice);" in corpo
    # e o src só é atribuído dentro do raio
    assert 'if (img.getAttribute("src")) continue;' in corpo


def test_o_swipe_lateral_nao_e_cancelado_pelo_gesto_de_fechar():
    """`preventDefault` no caminho do toque mataria o swipe de navegação,
    que é scroll nativo."""
    fonte = _txt(LIGHTBOX_JS)
    assert "{ passive: true }" in fonte
    corpo = _corpo(fonte, "abrir", fecho="\n  }")
    assert "preventDefault" not in corpo.split("aoTeclado")[0], (
        "há preventDefault no caminho de toque")


def test_o_botao_de_fechar_tem_alvo_de_toque_confortavel():
    bloco = _regra(_txt(CSS), ".lightbox__fechar")
    assert "width: 44px" in bloco and "height: 44px" in bloco


def test_lightbox_js_carrega_na_pagina_do_filme():
    html = _txt(RAIZ / "frontend" / "filme.html")
    i, j = html.find('src="js/lightbox.js"'), html.find('src="js/filme.js"')
    assert i != -1 and i < j
