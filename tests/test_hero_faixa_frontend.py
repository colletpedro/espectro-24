"""[v1.9.42] A FAIXA DE STILLS COMO HERO — travas no FRONTEND.

Substitui `test_galeria_frontend.py` (v1.9.38–41), que travava a seção
"Galeria" do RODAPÉ. Essa seção foi REMOVIDA por correção de escopo do
dono: a faixa passou a ser o topo da página, e o mesmo conteúdo em dois
lugares seria repetição. **A CONTABILIDADE das travas antigas — o que
sobreviveu adaptado, o que foi apagado e por quê — está em
`test_travas_removidas_v1942` no fim deste arquivo, para que a remoção
seja auditável e não apenas afirmada.**

Mesma convenção do arquivo que substitui: checagem TEXTUAL/estrutural
sobre `filme.js`/`poster.js`/`styles.css`, porque o projeto não tem
runner de JavaScript. O COMPORTAMENTO da faixa (velocidade por delta de
tempo, loop sem salto, pausa, movimento reduzido) é EXECUTADO sob node em
`test_faixa_stills.py`.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FILME_JS = RAIZ / "frontend" / "js" / "filme.js"
POSTER_JS = RAIZ / "frontend" / "js" / "poster.js"
FAIXA_JS = RAIZ / "frontend" / "js" / "faixa.js"
CSS = RAIZ / "frontend" / "css" / "styles.css"


def _filme_js():
    return FILME_JS.read_text(encoding="utf-8")


def _poster_js():
    return POSTER_JS.read_text(encoding="utf-8")


def _faixa_js():
    return FAIXA_JS.read_text(encoding="utf-8")


def _css():
    return CSS.read_text(encoding="utf-8")


def _corpo(fonte, nome, fecho="\n  }"):
    m = re.search(r"function " + nome + r"\(.*?\) \{(.*?)" + re.escape(fecho),
                  fonte, re.S)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


# --- a seção de rodapé sumiu de verdade -------------------------------

def _sem_comentarios(fonte):
    """Só o CÓDIGO. Os comentários desta versão NOMEIAM o que foi removido
    (é assim que a remoção fica registrada onde alguém vai ler), e casar
    com a prosa transformaria a trava numa proibição de explicar."""
    fonte = re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    return re.sub(r"//.*", "", fonte)


def test_a_secao_antiga_da_galeria_nao_voltou_com_o_nome_antigo():
    """A seção de rodapé da v1.9.39–41 continua REMOVIDA. O que a v1.9.43
    trouxe de volta é OUTRA coisa, com outro nome e outra condição: a
    `.galeria-mobile`, que só existe abaixo de 1024px e cujos itens abrem
    em tela cheia. O código antigo (`galeriaBlock`, `montarGaleria`, as
    classes `stills-galeria*`) não pode ter ressuscitado junto — dois
    caminhos de renderização para o mesmo conteúdo foi o defeito."""
    for nome, fonte in (("filme.js", _filme_js()), ("poster.js", _poster_js()),
                        ("styles.css", _css())):
        codigo = _sem_comentarios(fonte)
        assert "galeriaBlock(" not in codigo, f"galeriaBlock vivo em {nome}"
        assert "montarGaleria(" not in codigo, f"montarGaleria vivo em {nome}"
        for classe in ("stills-galeria__grid", "stills-galeria__faixa",
                       "stills-galeria__trilha", "stills-galeria"):
            assert classe not in codigo, f"{classe} ainda vivo em {nome}"


def test_render_nao_anexa_mais_nenhuma_secao_de_galeria():
    fonte = _filme_js()
    assert "var galeria = galeriaBlock" not in fonte
    assert not re.search(r"app\.appendChild\(galeria\)", fonte)


# --- nada mais na página se moveu -------------------------------------

def test_a_ordem_dos_blocos_da_pagina_esta_intacta():
    """A entrega troca QUEM ocupa a caixa da abertura e remove a seção do
    rodapé. Nada entre uma coisa e outra pode ter mudado de lugar."""
    fonte = _filme_js()
    ordem = [
        r"app\.appendChild\(header\(f\)\)",
        r"app\.appendChild\(fichaBlock\(",
        r"app\.appendChild\(proporcaoBlock\(f\)\)",
        r"condicoesBlock\(f\)",
        r"app\.appendChild\(detailDivider\(\)\)",
        r"app\.appendChild\(sentimentGroupsBlock\(f\)\)",
        r"veredictoBlock\(f\)",
        r"narrativaCollapsedBlock\(f\.narrativa\)",
        r"window\.mountSurvey\(app, f\)",
    ]
    pos = []
    for padrao in ordem:
        m = re.search(padrao, fonte)
        assert m, f"âncora não encontrada: {padrao}"
        pos.append(m.start())
    assert pos == sorted(pos), "um bloco existente mudou de posição relativa"


def test_entre_a_narrativa_e_a_pesquisa_so_entra_a_galeria_do_mobile():
    """[v1.9.43] A posição da galeria voltou a ser esta — só que agora
    condicionada ao modo. Entre narrativa e pesquisa só podem existir a
    âncora (nó inerte) e a chamada que decide a galeria; qualquer outro
    bloco ali seria conteúdo novo que a entrega não pediu."""
    fonte = _filme_js()
    i = re.search(r"narrativaCollapsedBlock\(f\.narrativa\)", fonte).start()
    j = re.search(r"window\.mountSurvey\(app, f\)", fonte).start()
    meio = _sem_comentarios(fonte[i:j])
    anexos = re.findall(r"app\.appendChild\((\w+)", meio)
    assert anexos == ["ancoraGaleria"], (
        f"outra coisa foi anexada entre narrativa e pesquisa: {anexos}")
    assert "aplicarModoGaleria(f)" in meio


# --- a faixa é o hero -------------------------------------------------

def test_o_hero_monta_a_faixa_e_cai_no_backdrop_estatico_quando_nao_ha():
    """O topo da página NUNCA fica vazio: `heroFaixa` devolve `null` e o
    `montarBackdrop` de sempre assume. É o caminho de `talk-to-me-2022`
    (filtro de duração), de filme sem ficha e de pool abaixo do piso."""
    fonte = _filme_js()
    assert re.search(
        r"var abertura = \(ehModoFaixa\(\) \? heroFaixa\(f, ano\) : null\) \|\|\s*"
        r"window\.ESPECTRO_POSTER\.montarBackdrop\(", fonte), (
        "o hero não cai no backdrop estático quando não há faixa — ou "
        "deixou de ser condicionado ao modo")


def test_hero_faixa_retorna_null_antes_de_criar_qualquer_elemento():
    corpo = _corpo(_filme_js(), "heroFaixa")
    guarda = re.search(r"if \(!itens\.length\) return null;", corpo)
    section = re.search(r"createElement\(", corpo)
    assert guarda and section
    assert guarda.start() < section.start(), (
        "a checagem de faixa vazia precisa vir ANTES de criar elemento")


def test_a_faixa_ocupa_a_caixa_do_backdrop_com_a_proporcao_reservada():
    """Mesma largura, mesma proporção, mesmo fade: a CAIXA leva a classe
    `.backdrop` junto da sua, e reserva a proporção do PRIMEIRO quadro —
    sem isso o topo da página salta enquanto a imagem carrega."""
    corpo = _corpo(_filme_js(), "heroFaixa")
    assert 'caixa.className = "backdrop hero-faixa-caixa"' in corpo
    assert "caixa.style.aspectRatio = itens[0].style.aspectRatio" in corpo


def test_o_FADE_nao_mora_na_caixa_que_rola():
    """REGRESSÃO de um defeito real, achado só medindo a página: o fade da
    base (`.backdrop::after`) é `position: absolute; left/right/bottom: 0`,
    e dentro de um contêiner com scroll isso ancora no CONTEÚDO. Com a
    faixa em `scrollLeft = 1500`, o fade ficava em `left: -1147px` — fora
    da tela, levando junto o PISO DE CONTRASTE do par ano → título
    (`.backdrop::after`, v1.9.33), que é garantido por construção e não
    por sorte com a imagem.

    A correção são três caixas: `.backdrop.hero-faixa-caixa` não rola e
    leva o fade; `.hero-faixa` rola; `.hero-faixa__trilha` alinha os
    quadros. Esta trava impede que alguém volte a fundir as duas
    primeiras."""
    corpo = _corpo(_filme_js(), "heroFaixa")
    # a classe .backdrop (que carrega o ::after) está na caixa, NÃO na faixa
    assert 'className = "backdrop hero-faixa-caixa"' in corpo
    assert 'faixa.className = "hero-faixa"' in corpo
    assert '"backdrop hero-faixa"' not in corpo, (
        "a classe .backdrop voltou para o elemento que rola — o fade "
        "escapa junto com o conteúdo")
    css = _css()
    # e quem tem overflow é a faixa, não a caixa do fade
    m_caixa = re.search(r"\.hero-faixa-caixa \{(.*?)\}", css, re.S)
    assert m_caixa and "overflow-x: auto" not in m_caixa.group(1)
    m_faixa = re.search(r"\.hero-faixa \{(.*?)\}", css, re.S)
    assert "overflow-x: auto" in m_faixa.group(1)


def test_montar_hero_faixa_existe_e_e_exportado():
    fonte = _poster_js()
    assert "function montarHeroFaixa(" in fonte
    assert re.search(r"montarHeroFaixa:\s*montarHeroFaixa", fonte)


def test_montar_hero_faixa_nunca_retorna_null_so_array_vazio():
    """Contrato mantido de `montarGaleria`: quem chama testa `.length`,
    não truthiness."""
    corpo = _corpo(_poster_js(), "montarHeroFaixa")
    assert "return []" in corpo


def test_faixa_js_carrega_antes_de_filme_js():
    html = (RAIZ / "frontend" / "filme.html").read_text(encoding="utf-8")
    i, j = html.find('src="js/faixa.js"'), html.find('src="js/filme.js"')
    assert i != -1 and i < j


def test_a_faixa_degrada_sem_o_script_em_vez_de_quebrar():
    assert re.search(
        r"if \(window\.ESPECTRO_FAIXA && window\.ESPECTRO_FAIXA\.montarFaixa\)",
        _filme_js())


# --- largura de CDN ---------------------------------------------------

def test_o_hero_serve_w1280_no_desktop_e_w780_no_mobile():
    """A nitidez do topo NÃO regride: `w1280` é exatamente o que o
    backdrop estático já servia. `w780` no mobile porque ali ele dá 2,08×
    (praticamente o ideal) por 2,3× menos bytes."""
    fonte = _poster_js()
    assert 'var TAMANHO_STILLS_DESKTOP = "w1280";' in fonte
    assert 'var TAMANHO_STILLS_MOBILE = "w780";' in fonte
    assert fonte.count('var TAMANHO_BACKDROP = "w1280";') == 1, (
        "o backdrop estático mudou de largura junto — não deveria")
    corpo = _corpo(_poster_js(), "montarHeroFaixa")
    assert "srcset:" in corpo and "sizes: STILLS_SIZES" in corpo


def test_o_breakpoint_do_sizes_bate_com_o_do_css():
    """`sizes` é HTML e não enxerga a media query. Se um mudar sem o
    outro, o navegador escolhe a largura errada em silêncio."""
    assert 'var STILLS_SIZES = "(max-width: 640px) 100vw, 720px";' in _poster_js()
    assert "@media (max-width: 640px)" in _css()


def test_carregamento_sob_demanda_so_os_primeiros_sao_eager():
    """Uma volta inteira a `w1280` passa de 1,5 MB. A resposta NÃO foi
    baixar a qualidade (recusado pelo dono) e sim carregar sob demanda —
    os primeiros ansiosos, o resto conforme a faixa avança."""
    fonte = _poster_js()
    assert re.search(r"var EAGER_NO_HERO = \d+;", fonte)
    corpo = _corpo(_poster_js(), "montarHeroFaixa")
    assert "lazy: i >= EAGER_NO_HERO" in corpo


# --- proibições -------------------------------------------------------

def test_nenhum_indicador_de_quantidade_e_renderizado():
    corpo = _corpo(_filme_js(), "heroFaixa")
    criados = re.findall(r'createElement\("(\w+)"\)', corpo)
    # três div e nada mais: caixa (fade) > faixa (scroll) > trilha
    assert sorted(criados) == ["div", "div", "div"], (
        f"heroFaixa criou elementos além dos três div: {criados}")
    codigo = re.sub(r"//.*", "", corpo)
    for proibido in ("button", "dots", "indicador", "contador", "arrow"):
        assert proibido not in codigo.lower()


def test_a_barra_de_scroll_e_escondida_nos_tres_motores():
    css = _css()
    m = re.search(r"\.hero-faixa \{(.*?)\}", css, re.S)
    assert m, "regra .hero-faixa não encontrada"
    bloco = m.group(1)
    assert "scrollbar-width: none" in bloco
    assert "-ms-overflow-style: none" in bloco
    assert ".hero-faixa::-webkit-scrollbar { display: none; }" in css
    assert "overflow-x: auto" in bloco


def test_o_scroll_vertical_da_pagina_nao_e_sequestrado():
    """Pesa mais aqui que na galeria de rodapé: a faixa é a PRIMEIRA coisa
    da página, onde o polegar começa a rolar."""
    m = re.search(r"\.hero-faixa \{(.*?)\}", _css(), re.S)
    bloco = m.group(1)
    assert "touch-action" not in bloco
    assert "overscroll-behavior-x: contain" in bloco
    assert "preventDefault" not in _faixa_js()
    assert "{ passive: true }" in _faixa_js()


def test_sem_gap_entre_os_quadros():
    """Sequência contínua, não slideshow: um respiro entre quadros
    desenharia a fronteira que o movimento existe para dissolver."""
    m = re.search(r"\.hero-faixa__trilha \{(.*?)\}", _css(), re.S)
    assert m and "gap: 0" in m.group(1)


# --- acessibilidade ---------------------------------------------------

def test_a_faixa_e_alcancavel_por_teclado_com_nome_e_foco_visivel():
    corpo = _corpo(_filme_js(), "heroFaixa")
    assert 'setAttribute("role", "region")' in corpo
    assert 'setAttribute("tabindex", "0")' in corpo
    assert 'setAttribute("aria-label"' in corpo
    assert ".hero-faixa:focus-visible" in _css()


def test_as_copias_do_loop_sao_invisiveis_para_leitor_de_tela():
    corpo = _corpo(_faixa_js(), "duplicar", fecho="\n    }")
    assert 'setAttribute("aria-hidden", "true")' in corpo


def test_o_alt_numerado_de_cada_still_continua_como_estava():
    """Requisito explícito desde a v1.9.41: alt preservado como está."""
    assert ('alt: "Still " + (i + 1) + " de " + nome + sufixoAno(opcoes.ano)'
            in _poster_js())


def test_movimento_reduzido_desliga_a_rolagem_mas_nao_a_faixa():
    fonte = _faixa_js()
    assert "prefers-reduced-motion: reduce" in fonte
    corpo = _corpo(fonte, "deveRolar", fecho="\n  }")
    assert "if (reduzMovimento) return false;" in corpo


def test_atribuicao_ao_tmdb_continua_cobrindo_as_imagens_do_filme():
    """Obrigação legal, e ela NÃO some com a seção: os stills continuam
    publicados, agora no topo. O texto teve de mudar (não há mais
    'galeria'), a cobertura não."""
    creditos = (RAIZ / "frontend" / "creditos.html").read_text(encoding="utf-8")
    assert "stills que abrem a página do filme" in creditos
    assert "galeria de stills" not in creditos, (
        "os créditos ainda falam de uma galeria que não existe mais")


# --- contabilidade da remoção ------------------------------------------

def test_travas_removidas_v1942():
    """As travas de `test_galeria_frontend.py` que foram APAGADAS, e o
    motivo de cada uma. Apagar teste que perdeu o objeto é diferente de
    afrouxar asserção — este teste existe para que a diferença fique
    escrita, e para que o arquivo antigo não volte por engano.

    APAGADAS (3), todas por PERDA DE OBJETO — a coisa que elas afirmavam
    não existe mais em nenhuma forma:

      1. `test_galeria_vem_depois_da_narrativa_e_antes_da_pesquisa`
         Afirmava a POSIÇÃO da seção do rodapé entre narrativa e
         pesquisa. Não há mais seção para posicionar. O que sobra da
         afirmação — "nada mais se moveu" — está coberto, e mais forte,
         por `test_a_ordem_dos_blocos_da_pagina_esta_intacta` (que hoje
         inclui `mountSurvey` na cadeia) e por
         `test_a_narrativa_agora_e_seguida_direto_pela_pesquisa`.

      2. `test_render_so_anexa_a_galeria_se_o_bloco_nao_for_null`
         Afirmava a guarda `if (galeria)` em `render()`. A chamada saiu.
         Substituída por
         `test_render_nao_anexa_mais_nenhuma_secao_de_galeria` (a
         afirmação inversa) e por
         `test_o_hero_monta_a_faixa_e_cai_no_backdrop_estatico_quando_nao_ha`,
         que trava a guarda equivalente no lugar novo.

      3. `test_a_grade_estatica_nao_existe_mais`
         Afirmava que a grade da v1.9.39 não sobrevivia à v1.9.41.
         Absorvida, com escopo maior, por
         `test_a_secao_galeria_do_rodape_nao_existe_mais_em_lugar_nenhum`,
         que varre as três camadas em vez de duas.

    ADAPTADAS (todas as demais): mesma asserção, objeto renomeado —
    `galeriaBlock` → `heroFaixa`, `montarGaleria` → `montarHeroFaixa`,
    `.stills-galeria__faixa` → `.hero-faixa`. Nenhuma perdeu força; duas
    ganharam (`test_o_hero_serve_w1280...` passou a travar também que o
    backdrop estático NÃO mudou de largura junto).
    """
    assert not (RAIZ / "tests" / "test_galeria_frontend.py").exists(), (
        "o arquivo antigo voltou — ele e este cobrem o mesmo terreno, e "
        "o antigo trava um objeto que não existe mais")


# --- o hero NUNCA fica vazio (caminho de talk-to-me-2022) --------------

def test_talk_to_me_2022_cai_no_MESMO_hero_estatico_que_ja_mostrava():
    """O caminho de fallback, testado no DADO PUBLICADO e não só no
    código. `talk-to-me-2022` resolve para um curta de 3 min (guarda de
    identidade PENDENTE, ver `duracao_compativel_com_longa`) e é ele quem
    exercita este caminho no catálogo real.

    **E ele é o caso mais duro possível: é o ÚNICO filme do catálogo SEM
    `backdrop_path`** (medido desde a v1.9.30, registrado em `filme.js`).
    Ou seja, o "hero estático de hoje" dele nunca foi um backdrop — é o
    segundo degrau do fallback, o pôster contido (`.film-hero--poster`).
    A entrega prometeu "volta a exibir o hero estático de hoje", e é
    exatamente isso que a cascata entrega, sem nenhum caminho novo: faixa
    ausente → `montarBackdrop` devolve `null` → pôster.

    A trava aqui é que a cascata continua com os TRÊS degraus e que este
    filme tem com que preencher o topo."""
    import json
    ficha = json.loads((RAIZ / "resultado" / "talk-to-me-2022.json")
                       .read_text(encoding="utf-8"))["ficha"]
    assert ficha["galeria_stills"] == [], (
        "talk-to-me-2022 passou a ter faixa — o filtro de duração quebrou, "
        "e com ele a guarda que segrega o curta errado")
    assert not ficha.get("backdrop_path"), (
        "este filme ganhou um backdrop — a premissa do teste mudou; "
        "confira se ele ainda é o caso sem backdrop do catálogo")
    assert ficha.get("poster_path"), (
        "sem backdrop E sem pôster o topo da página deste filme fica no "
        "estado de ausência desenhado — não vazio, mas também não é o que "
        "a entrega prometeu")
    # e o degrau do pôster continua existindo no código do hero
    corpo = _corpo(_filme_js(), "header")
    assert 'hero.classList.add("film-hero--poster")' in corpo
    assert "ESPECTRO_POSTER.montar(" in corpo


def test_todo_filme_publicado_tem_hero_de_algum_tipo():
    """Trava do catálogo inteiro: faixa OU backdrop estático. O topo da
    página não pode ficar vazio em nenhum dos 35."""
    import json
    sem_hero = []
    for p in sorted((RAIZ / "resultado").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        f = d.get("ficha") or {}
        if not f:
            continue
        tem_faixa = bool(f.get("galeria_stills"))
        tem_estatico = bool(f.get("backdrop_path") or f.get("poster_path"))
        if not (tem_faixa or tem_estatico):
            sem_hero.append(p.stem)
    assert sem_hero == [], f"filmes sem nada para abrir a página: {sem_hero}"


def test_o_primeiro_quadro_da_faixa_e_o_backdrop_publicado_ou_gemeo_dele():
    """A faixa abre no MESMO quadro que o hero estático mostraria — é o
    que torna os dois caminhos indistinguíveis na abertura.

    Nos filmes em que o backdrop colapsou num gêmeo perceptual da dedup
    (pHash ≤ 14), quem abre é o gêmeo: MESMO quadro, outro arquivo. A
    trava aceita esse caso e nomeia os filmes, para que um oitavo
    aparecendo aqui seja uma conversa e não uma surpresa."""
    import json
    import sys
    sys.path.insert(0, str(RAIZ / "src"))
    from espectro24.still_hash import distancia
    from espectro24.ficha import LIMIAR_PHASH

    memo_p = RAIZ / "dados" / "cache" / "_stills_phash.json"
    memo = json.loads(memo_p.read_text(encoding="utf-8")) if memo_p.exists() else {}

    divergentes = []
    for p in sorted((RAIZ / "resultado").glob("*.json")):
        f = (json.loads(p.read_text(encoding="utf-8")).get("ficha") or {})
        g = f.get("galeria_stills") or []
        if not g:
            continue
        bp, primeiro = f.get("backdrop_path"), g[0]["still_path"]
        if primeiro == bp:
            continue
        divergentes.append(p.stem)
        if memo and bp in memo and primeiro in memo:
            # transitividade da dedup pode passar do limiar par a par;
            # o teto de 2× é a folga que o fecho transitivo permite
            assert distancia(memo[bp], memo[primeiro]) <= 2 * LIMIAR_PHASH, (
                f"{p.stem}: a faixa abre num quadro que NÃO é o backdrop "
                f"publicado nem um gêmeo dele")
    assert divergentes == [
        "anatomy-of-a-fall", "cats-2019", "dune-2021", "dune-part-two",
        "everything-everywhere-all-at-once", "friday-the-13th-2009",
        "the-substance",
    ], f"mudou o conjunto de filmes cujo hero colapsou num gêmeo: {divergentes}"
