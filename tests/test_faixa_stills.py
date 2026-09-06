"""[v1.9.41] FAIXA DE ROLAGEM CONTÍNUA da galeria — travas de COMPORTAMENTO.

**Diferença deliberada de `test_galeria_frontend.py`**, que checa o TEXTO
do JS porque o projeto não tem infraestrutura de teste JavaScript. As
garantias exigidas por esta entrega não são verificáveis assim: "a
velocidade não depende da taxa de quadros" e "o loop não salta" são
afirmações sobre o que o código CALCULA, e um `assert "px/s" in fonte`
passaria com a conta errada.

Por isso o núcleo de `faixa.js` foi escrito como funções PURAS (sem DOM,
sem relógio próprio) e é EXECUTADO aqui, sob `node`, com o delta de tempo
mockado — que é o que "mockar delta de tempo" pede.

Quando `node` não existe na máquina, estes testes são PULADOS com motivo
visível, e as travas textuais de `test_galeria_frontend.py` continuam
valendo como piso. O que não se faz é fingir que o comportamento foi
verificado.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

FAIXA_JS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "faixa.js"

# [v1.9.42] A velocidade deixou de ser uma constante em px/s e passou a
# sair da LARGURA MEDIDA do item (`velocidadeParaItem`), porque a faixa
# virou o hero e o item passou a ocupar a coluna inteira — 720px no
# desktop, 375px no mobile. Estes números são os medidos ao vivo, e a
# velocidade de referência dos testes deriva deles, não de um literal.
ITEM_DESKTOP, ITEM_MOBILE = 720, 375

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node não encontrado — o núcleo puro de faixa.js não pôde ser "
           "EXECUTADO; as travas textuais de test_galeria_frontend.py "
           "continuam valendo, mas o comportamento fica sem verificação")


def _node(corpo: str):
    """Roda `corpo` em node com `F` = a API de faixa.js, e devolve o JSON
    que ele imprimir."""
    script = textwrap.dedent(f"""
        const F = require({json.dumps(str(FAIXA_JS))});
        {textwrap.dedent(corpo)}
    """)
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, f"node falhou:\n{r.stderr}"
    return json.loads(r.stdout)


# --- velocidade independente da taxa de quadros -----------------------

def test_mesma_distancia_em_60hz_e_em_120hz():
    """A trava central: 1 segundo de animação anda o MESMO tanto num
    monitor de 60Hz (16,67ms/quadro) e num de 120Hz (8,33ms/quadro). Um
    incremento fixo por quadro daria o dobro no de 120Hz."""
    out = _node("""
        const V = F.velocidadeParaItem(720);
        function percorrer(dtMs, segundos) {
            let t = 0, pos = 0;
            const n = Math.round(segundos * 1000 / dtMs);
            for (let i = 0; i < n; i++) {
                pos += F.passoDoQuadro(t, t + dtMs, V);
                t += dtMs;
            }
            return pos;
        }
        console.log(JSON.stringify({
            hz60: percorrer(1000 / 60, 1),
            hz120: percorrer(1000 / 120, 1),
            hz30: percorrer(1000 / 30, 1),
            velocidade: V,
        }));
    """)
    assert out["hz60"] == pytest.approx(out["velocidade"], abs=0.01)
    assert out["hz120"] == pytest.approx(out["velocidade"], abs=0.01)
    assert out["hz30"] == pytest.approx(out["velocidade"], abs=0.01)
    assert out["hz120"] == pytest.approx(out["hz60"], abs=0.01), (
        "120Hz andou diferente de 60Hz — o passo voltou a ser por quadro")


def test_primeiro_quadro_nao_salta():
    """Sem `ultimoMs` não há intervalo medido; chutar um daria um pulo no
    primeiro quadro, justamente quando o olho está chegando."""
    out = _node("""
        console.log(JSON.stringify({
            sem_anterior: F.passoDoQuadro(null, 1000, F.velocidadeParaItem(720)),
            tempo_para_tras: F.passoDoQuadro(1000, 900, F.velocidadeParaItem(720)),
            igual: F.passoDoQuadro(1000, 1000, F.velocidadeParaItem(720)),
        }));
    """)
    assert out["sem_anterior"] == 0
    assert out["tempo_para_tras"] == 0
    assert out["igual"] == 0


def test_aba_em_segundo_plano_nao_vira_salto():
    """`requestAnimationFrame` não roda em aba oculta. Ao voltar, o delta
    é de dezenas de segundos — sem teto, a faixa saltaria centenas de
    pixels de uma vez."""
    out = _node("""
        console.log(JSON.stringify({
            trinta_s: F.passoDoQuadro(0, 30000, F.velocidadeParaItem(720)),
            teto: F.DT_MAX_S * F.velocidadeParaItem(720),
        }));
    """)
    assert out["trinta_s"] == pytest.approx(out["teto"])
    assert out["trinta_s"] < 4, "um quadro andou mais de 4px — o teto sumiu"


# --- o loop não salta -------------------------------------------------

def test_posicao_e_continua_ao_cruzar_o_limite():
    """Percorre mais de dois ciclos inteiros e confirma que a posição
    nunca dá um passo maior que o passo de um quadro — o reposicionamento
    do loop tem que ser invisível, e invisível aqui quer dizer que a
    posição EQUIVALENTE (posição + voltas) segue crescendo em linha."""
    out = _node("""
        const V = F.velocidadeParaItem(720);
        const CICLO = 500;
        let pos = 0, t = 0, voltas = 0, maiorPasso = 0, anterior = 0;
        const dt = 1000 / 60;
        for (let i = 0; i < 60 * 60; i++) {   // 60s de animação
            const passo = F.passoDoQuadro(t, t + dt, V);
            t += dt;
            const bruta = pos + passo;
            pos = F.normalizarScroll(bruta, CICLO);
            if (bruta >= CICLO) voltas++;
            const equivalente = pos + voltas * CICLO;
            maiorPasso = Math.max(maiorPasso, equivalente - anterior);
            anterior = equivalente;
        }
        console.log(JSON.stringify({
            voltas, maiorPasso, pos,
            passoNominal: V * (dt / 1000),
        }));
    """)
    assert out["voltas"] >= 2, "o teste não chegou a cruzar o limite duas vezes"
    assert out["maiorPasso"] == pytest.approx(out["passoNominal"], abs=1e-9), (
        "houve um passo maior que o de um quadro — o loop saltou")
    assert 0 <= out["pos"] < 500


def test_normalizar_devolve_sempre_dentro_do_ciclo_nos_dois_sentidos():
    """Arrastar para trás do zero também não pode piscar."""
    out = _node("""
        const casos = [[0,100],[99.9,100],[100,100],[100.5,100],[250,100],
                       [-0.5,100],[-100,100],[-250,100]];
        console.log(JSON.stringify(casos.map(c => F.normalizarScroll(c[0], c[1]))));
    """)
    assert out == [0, 99.9, 0, 0.5, 50, 99.5, 0, 50]
    assert all(0 <= v < 100 for v in out)


def test_ciclo_zero_nao_trava_nem_divide_por_zero():
    out = _node("""
        console.log(JSON.stringify({
            zero: F.normalizarScroll(42, 0),
            negativo: F.normalizarScroll(42, -1),
        }));
    """)
    assert out["zero"] == 42 and out["negativo"] == 42


# --- pausa e retomada -------------------------------------------------

def test_pausa_e_imediata_e_retomada_e_em_rampa():
    out = _node("""
        const dt = 1000 / 60;
        const V = F.velocidadeParaItem(720);
        const pausada = F.velocidadeComRampa(V, 0, dt);
        // retomada: alvo de volta, medindo quantos quadros até chegar lá
        let atual = 0, quadros = 0;
        while (atual < V && quadros < 1000) {
            atual = F.velocidadeComRampa(atual, V, dt);
            quadros++;
        }
        console.log(JSON.stringify({
            pausada,
            quadros,
            segundos: quadros * dt / 1000,
            rampa: F.RAMPA_S,
            nunca_passa: F.velocidadeComRampa(V, V, 10000),
            alvo: V,
        }));
    """)
    assert out["pausada"] == 0, "pausa não foi imediata"
    assert out["segundos"] == pytest.approx(out["rampa"], rel=0.05), (
        "a retomada não levou o tempo de rampa declarado")
    assert out["quadros"] > 1, "a retomada foi instantânea — a rampa sumiu"
    assert out["nunca_passa"] == out["alvo"], (
        "a rampa ultrapassou a velocidade alvo")


def test_rampa_tambem_independe_da_taxa_de_quadros():
    out = _node("""
        const V = F.velocidadeParaItem(720);
        function subir(dt) {
            let v = 0, t = 0;
            while (v < V && t < 5000) { v = F.velocidadeComRampa(v, V, dt); t += dt; }
            return t / 1000;
        }
        console.log(JSON.stringify({hz60: subir(1000/60), hz120: subir(1000/120)}));
    """)
    assert out["hz60"] == pytest.approx(out["hz120"], abs=0.02)


# --- prefers-reduced-motion e poucos itens ----------------------------

def test_reduced_motion_desliga_a_rolagem_automatica():
    """A faixa continua existindo e rolável à mão — `deveRolar` responde
    só sobre a animação."""
    out = _node("""
        console.log(JSON.stringify({
            com_movimento: F.deveRolar(2000, 720, false),
            reduzido: F.deveRolar(2000, 720, true),
        }));
    """)
    assert out["com_movimento"] is True
    assert out["reduzido"] is False


def test_poucos_itens_nao_rolam():
    """Trilha que não enche a largura visível fica ESTÁTICA: rolar abriria
    um vão vazio e o traria de volta ciclicamente."""
    out = _node("""
        console.log(JSON.stringify({
            tres_itens: F.deveRolar(3 * 182, 720, false),
            quatro_itens: F.deveRolar(4 * 182, 720, false),
            exatamente_igual: F.deveRolar(720, 720, false),
            um_item: F.deveRolar(182, 720, false),
        }));
    """)
    assert out["tres_itens"] is False, "3 itens (546px) não enchem 720px"
    assert out["quatro_itens"] is True, "4 itens (728px) passam de 720px"
    assert out["exatamente_igual"] is False, (
        "trilha do tamanho exato da janela não tem para onde rolar")
    assert out["um_item"] is False


# --- o período da repetição (bug achado na verificação ao vivo) --------

def test_periodo_da_trilha_nao_e_metade_da_largura():
    """REGRESSÃO de um defeito real, achado só ao medir a página no
    navegador: a primeira versão usava `scrollWidth / 2` como período do
    loop. Uma trilha com `2n` itens tem `2n − 1` intervalos (não há gap
    depois do último), então metade da largura fica MEIO GAP curta, e o
    loop devolvia a faixa 5px adiantada a cada volta — sempre no mesmo
    sentido. Os números aqui são os de `wonka` medidos ao vivo: 16 itens
    de 172px com gap de 10px."""
    out = _node("""
        const ITEM = 172, GAP = 10, N = 16;
        const passo = ITEM + GAP;
        const offsets = [];
        for (let i = 0; i < 2 * N; i++) offsets.push(i * passo);
        const larguraTotal = (2 * N - 1) * passo + ITEM;   // sem gap no fim
        console.log(JSON.stringify({
            periodo: F.periodoDaTrilha(offsets, N),
            metade_da_largura: larguraTotal / 2,
            esperado: N * passo,
        }));
    """)
    assert out["periodo"] == out["esperado"] == 2912
    assert out["metade_da_largura"] == 2907
    assert out["periodo"] != out["metade_da_largura"], (
        "o período voltou a ser scrollWidth/2 — o loop salta meio gap por volta")


def test_periodo_e_robusto_a_gap_zero_e_a_entrada_degenerada():
    out = _node("""
        const semGap = []; for (let i = 0; i < 8; i++) semGap.push(i * 172);
        console.log(JSON.stringify({
            gap_zero: F.periodoDaTrilha(semGap, 4),
            n_zero: F.periodoDaTrilha(semGap, 0),
            curto: F.periodoDaTrilha([0, 10], 4),
            vazio: F.periodoDaTrilha(null, 4),
        }));
    """)
    assert out["gap_zero"] == 4 * 172
    assert out["n_zero"] == 0 and out["curto"] == 0 and out["vazio"] == 0


# --- velocidade em TEMPO, não em pixels (v1.9.42) ---------------------

def test_desktop_e_mobile_levam_o_MESMO_tempo_por_quadro():
    """A razão de a velocidade ter virado tempo. O item deixou de ter
    largura fixa (172px) e passou a ocupar a coluna — 720px no desktop,
    375px no mobile, MEDIDOS. Com px/s fixo, o mesmo movimento levaria
    25,7s no desktop e 13,4s no mobile: ritmos diferentes sem nenhuma
    razão de produto."""
    out = _node(f"""
        const d = F.velocidadeParaItem({ITEM_DESKTOP});
        const m = F.velocidadeParaItem({ITEM_MOBILE});
        console.log(JSON.stringify({{
            px_s_desktop: d, px_s_mobile: m,
            s_por_quadro_desktop: {ITEM_DESKTOP} / d,
            s_por_quadro_mobile: {ITEM_MOBILE} / m,
            declarado: F.SEGUNDOS_POR_QUADRO,
        }}));
    """)
    assert out["s_por_quadro_desktop"] == pytest.approx(out["declarado"])
    assert out["s_por_quadro_mobile"] == pytest.approx(out["declarado"])
    assert out["s_por_quadro_desktop"] == pytest.approx(
        out["s_por_quadro_mobile"]), "os dois tamanhos andam em ritmos diferentes"
    # e o ritmo é o de "movimento lento": um quadro leva mais de 8 segundos
    assert out["declarado"] >= 8


def test_a_volta_inteira_nao_fica_curta_demais():
    """Com `TETO_STILLS` quadros e 1 quadro por tela, a volta é
    `teto × SEGUNDOS_POR_QUADRO`. O teto vive no Python; esta é a trava do
    lado do JS de que o ritmo não vira um piscar."""
    from espectro24.ficha import TETO_STILLS
    out = _node("console.log(JSON.stringify({s: F.SEGUNDOS_POR_QUADRO}))")
    volta = TETO_STILLS * out["s"]
    assert volta >= 120, f"a volta inteira leva só {volta}s — curta demais"


def test_largura_degenerada_cai_no_piso_e_nao_para_a_faixa():
    """Medir antes do layout devolveria largura ~0 e, com ela, velocidade
    zero: uma faixa parada sem nada dizer que parou."""
    out = _node("""
        console.log(JSON.stringify({
            zero: F.velocidadeParaItem(0),
            negativo: F.velocidadeParaItem(-5),
            piso: F.VELOCIDADE_MIN_PX_S,
        }));
    """)
    assert out["zero"] == out["piso"] > 0
    assert out["negativo"] == out["piso"]


def test_a_rampa_leva_o_mesmo_tempo_no_desktop_e_no_mobile():
    """A inclinação passou a derivar do `alvo`. Com a constante antiga, a
    rampa completaria em tempos diferentes nos dois tamanhos."""
    out = _node(f"""
        function subir(alvo) {{
            let v = 0, t = 0, dt = 1000 / 60;
            while (v < alvo && t < 20000) {{ v = F.velocidadeComRampa(v, alvo, dt); t += dt; }}
            return t / 1000;
        }}
        console.log(JSON.stringify({{
            desktop: subir(F.velocidadeParaItem({ITEM_DESKTOP})),
            mobile: subir(F.velocidadeParaItem({ITEM_MOBILE})),
            rampa: F.RAMPA_S,
        }}));
    """)
    assert out["desktop"] == pytest.approx(out["rampa"], rel=0.05)
    assert out["mobile"] == pytest.approx(out["rampa"], rel=0.05)


# --- [v1.9.43] velocidade menor -------------------------------------

def test_a_velocidade_caiu_e_a_travessia_de_tela_e_a_declarada():
    """Decisão do dono depois de ver a faixa rodando: 12s → 18s por
    quadro. Com a faixa full-bleed, o que se percebe é o tempo de a TELA
    se renovar, não o de um quadro isolado."""
    out = _node(f"""
        const v = F.velocidadeParaItem({ITEM_DESKTOP});
        console.log(JSON.stringify({{
            s_por_quadro: F.SEGUNDOS_POR_QUADRO, px_s: v,
            tela_1440: 1440 / v, tela_2560: 2560 / v,
        }}));
    """)
    assert out["s_por_quadro"] == 18
    assert out["px_s"] == pytest.approx(40)
    assert out["tela_1440"] == pytest.approx(36, abs=0.5)
    assert out["tela_2560"] == pytest.approx(64, abs=0.5)


# --- [v1.9.43] pausa: só por scroll ----------------------------------

def test_o_mecanismo_de_motivos_continua_de_pe():
    """A entrega reduziu os MOTIVOS, não trocou o mecanismo: dois motivos
    simultâneos ainda não podem religar a faixa quando o primeiro sai."""
    fonte = FAIXA_JS.read_text(encoding="utf-8")
    assert "estado.motivos[motivo] = true;" in fonte
    assert re.search(r"for \(var k in estado\.motivos\)", fonte), (
        "a retomada deixou de checar se ainda há outro motivo ativo")


def test_hover_e_foco_nao_pausam_mais():
    """O que a v1.9.43 removeu, travado pela AUSÊNCIA dos listeners: a
    faixa não pode parar só porque o cursor cruzou o topo da página."""
    codigo = re.sub(r"/\*.*?\*/", "", FAIXA_JS.read_text(encoding="utf-8"),
                    flags=re.S)
    codigo = re.sub(r"//.*", "", codigo)
    for evento in ("pointerenter", "pointerleave", "focusin", "focusout",
                   "pointerdown", "pointerup"):
        assert evento not in codigo, (
            f"a faixa voltou a escutar {evento!r} — só scroll pode pausar")
    assert '"hover"' not in codigo and '"foco"' not in codigo
    assert '"press"' not in codigo


def test_scroll_continua_pausando_e_retomando_com_rampa():
    codigo = FAIXA_JS.read_text(encoding="utf-8")
    assert 'viewport.addEventListener("scroll"' in codigo
    assert 'pausar("scroll")' in codigo
    assert re.search(r'setTimeout\(function \(\) \{ retomar\("scroll"\); \}, \d+\)',
                     codigo), "a retomada depois do scroll sumiu"


def test_arrasto_e_swipe_pausam_por_serem_scroll():
    """Não há mais `pointerdown`: arrastar pausa porque arrastar um
    contêiner rolável DISPARA scroll. Um toque parado (sem movimento) não
    pausa, e é o comportamento pedido."""
    fonte = FAIXA_JS.read_text(encoding="utf-8")
    assert "arrastar um contêiner rolável" in fonte or "DISPARA scroll" in fonte, (
        "o raciocínio de por que arrasto ainda pausa saiu do código")


# --- [v1.9.43] carregamento sob demanda da faixa ---------------------

def test_a_janela_carregada_cabe_no_teto_de_peso():
    """A faixa full-bleed mostra mais quadros ao mesmo tempo, e o peso de
    uma volta inteira (12 × 138,6 kB = 1,62 MB em `w1280`) passa do teto
    de ~1,5 MB por página. A resposta NÃO foi baixar a qualidade e sim
    carregar sob demanda: só a janela em torno do que está à vista."""
    out = _node("""
        const r = {};
        for (const vw of [1024, 1440, 1920, 2560]) r[vw] = F.raioDeCarga(vw, 720);
        console.log(JSON.stringify(r));
    """)
    for vw, raio in out.items():
        quadros = 2 * raio + 1
        mb = quadros * 138.6 / 1024
        assert mb <= 1.5, f"{vw}px carrega {quadros} quadros = {mb:.2f} MB"
    # e a janela cobre com folga o que está visível na tela
    assert out["2560"] * 2 + 1 >= 2560 / 720 + 1


def test_o_raio_e_metade_do_visivel_mais_margem():
    """Com o raio igual ao número de quadros visíveis (e não à metade), a
    2560 a janela seria de 11 imagens — 1,52 MB, e o carregamento sob
    demanda não teria servido para nada."""
    out = _node("""
        console.log(JSON.stringify({
            v1440: F.raioDeCarga(1440, 720),
            v2560: F.raioDeCarga(2560, 720),
            degenerado: F.raioDeCarga(1440, 0),
        }));
    """)
    assert out["v1440"] == 2 and out["v2560"] == 3
    assert out["degenerado"] == 1, "largura zero precisa cair num raio seguro"


def test_a_faixa_difere_o_src_e_nao_confia_so_no_lazy():
    """REGRESSÃO de um defeito MEDIDO duas vezes (faixa e lightbox):
    `loading="lazy"` é dica, não teto — na abertura da página as 12
    imagens do hero saíram juntas. Quem segura é a ausência de `src`."""
    fonte = FAIXA_JS.read_text(encoding="utf-8")
    assert "function carregarVizinhanca()" in fonte
    assert "img.dataset.src" in fonte
    assert 'img.getAttribute("src")' in fonte
    poster = (FAIXA_JS.parent / "poster.js").read_text(encoding="utf-8")
    assert "if (cfg.diferido) {" in poster
    assert "img.dataset.src = url(cfg.path, cfg.tamanho);" in poster


def test_a_faixa_que_nao_rola_tambem_carrega_o_que_esta_a_vista():
    """Poucos itens ou `prefers-reduced-motion`: a faixa fica parada, mas
    não pode ficar EM BRANCO — sem `src` ninguém busca nada."""
    fonte = FAIXA_JS.read_text(encoding="utf-8")
    m = re.search(r"if \(!deveRolar\(.*?\)\) \{(.*?)\n      \}", fonte, re.S)
    assert m and "carregarVizinhanca();" in m.group(1), (
        "a faixa estática não carrega as imagens visíveis")


def test_a_copia_do_loop_recebe_src_junto_da_original():
    """A segunda cópia mostra os mesmos quadros um ciclo depois. Se ela
    não for preenchida junto, a faixa pisca em branco ao dar a volta."""
    fonte = FAIXA_JS.read_text(encoding="utf-8")
    assert "var gemea = filhos[i + n]" in fonte
