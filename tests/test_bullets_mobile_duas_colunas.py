"""[v1.9.45] O BLOCO DE BULLETS EM DUAS COLUNAS NO MOBILE — Tentativa A.

Feedback de uso: no celular o bloco tema a tema empilhava (HATERS inteiro,
depois FANS inteiro), o que mostrava "uma coisa por vez" e custava duas
telas e meia de rolagem. A mudança é SÓ de CSS: abaixo de 640px a grade
`.sentiment-groups` passa a ter as mesmas duas colunas do desktop.

O QUE ESTE ARQUIVO TRAVA, e por que cada trava existe:

  1. NEUTRALIDADE ESTRUTURAL (§0). Nenhuma regra do bloco mobile pode
     olhar para `[data-group]`: se uma olhar, um dos lados passa a ter
     largura, corpo, margem ou contagem diferente do outro por decisão de
     folha de estilo — exatamente o que o §0 proíbe. A única diferença
     autorizada entre os grupos continua sendo a POSIÇÃO, que sai de
     `ordenarPorPeso` em `filme.js`, do `share_real`, e não daqui.

  2. AS COLUNAS SÃO IGUAIS. `1fr 1fr`, e não `2fr 1fr` nem `auto`.

  3. O DESKTOP NÃO FOI TOCADO. A regra de `min-width: 720px` continua
     idêntica, e o bloco novo inteiro vive dentro de `max-width: 640px` —
     nada entre 641 e 719px (tablet estreito) muda de comportamento.

  4. A ORDEM DAS REGRAS NO ARQUIVO. Regressão de um defeito REAL desta
     sessão: `@media` não soma especificidade, então o bloco declarado
     ANTES de `.theme__name { font-size: 1rem }` perdia para ela em
     silêncio — sem erro de console, sem teste vermelho, e a página
     renderizava duas colunas com a tipografia do desktop. O bloco precisa
     vir DEPOIS de cada regra que ele sobrescreve.

  5. O PISO DE LEGIBILIDADE. O corpo do nome do tema não pode cair abaixo
     dos 13px que o projeto já usa como mínimo em `.mosaic-cell__title`.

  6. NENHUM NÚMERO REFORMATADO. As strings com algarismo (`~X% das notas`,
     a faixa de estrelas, a janela da amostra) continuam montadas em
     `filme.js` exatamente como antes — CSS não pode ter virado desculpa
     para abreviar número.

Estrutural, pela razão de sempre: o projeto não tem runner de JS com DOM.
As medidas de altura da entrega foram feitas no navegador e estão no
relatório da sessão.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = RAIZ / "frontend" / "css" / "styles.css"
FILME_JS = RAIZ / "frontend" / "js" / "filme.js"

# O prefixo de versão desambigua: a frase sozinha também aparece no
# comentário-ponteiro que ficou lá em cima, ao lado de `.sentiment-groups`.
MARCA = "[v1.9.45] AS DUAS COLUNAS CABEM NO CELULAR"


def _txt(p):
    return p.read_text(encoding="utf-8")


def _sem_comentarios(fonte):
    return re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)


def _bloco_mobile():
    """O corpo do `@media (max-width: 640px)` que carrega a marca, SEM os
    comentários — o que é asserido é a declaração, nunca a prosa."""
    css = _txt(CSS)
    i = css.index(MARCA)
    j = css.index("@media (max-width: 640px) {", i)
    # varre contando chaves até fechar a media query
    nivel, k = 0, j
    while True:
        if css[k] == "{":
            nivel += 1
        elif css[k] == "}":
            nivel -= 1
            if nivel == 0:
                break
        k += 1
    return _sem_comentarios(css[j:k + 1])


# =====================================================================
# 1 e 2. Neutralidade estrutural entre os grupos
# =====================================================================

def test_o_bloco_mobile_nao_distingue_um_grupo_do_outro():
    """§0: nenhuma regra do modo mobile pode casar `[data-group=…]`.

    A folha inteira tem regras por grupo (cor do nome, cor da barra, cor do
    "APROFUNDAR") e elas continuam onde estavam — são COR, e são simétricas.
    O que não pode existir é uma regra de LEIAUTE por grupo dentro do bloco
    que reorganiza a tela: seria dar a um dos lados largura, corpo ou
    margem que o outro não tem.
    """
    bloco = _bloco_mobile()
    assert "data-group" not in bloco, (
        "uma regra do modo mobile passou a olhar para o grupo — a "
        "neutralidade estrutural do §0 quebra aqui")
    for cor in ("--neg", "--pos", "--med"):
        assert cor not in bloco, (
            f"{cor} entrou no bloco mobile: cor de grupo dentro de uma "
            "regra de leiaute é tratamento assimétrico disfarçado")


def test_as_duas_colunas_do_mobile_tem_a_mesma_largura():
    """`1fr 1fr` — não `2fr 1fr`, não `auto auto`, não `minmax` desigual.

    "A coluna do grupo maior fica maior" é a infidelidade que a v1.4.0
    corrigiu na barra e que `.decide__grid` registra por escrito; ela não
    volta pela porta do mobile.
    """
    bloco = _bloco_mobile()
    colunas = re.findall(r"grid-template-columns:\s*([^;]+);", bloco)
    assert colunas, "o bloco mobile não declara `grid-template-columns`"
    for decl in colunas:
        assert decl.strip() == "1fr 1fr", (
            f"coluna desigual no mobile: {decl.strip()!r}")


def test_os_dois_casos_de_grade_recebem_a_mesma_grade():
    """`--2` (HATERS+FANS) e `--3` (o meio dominante entra em destaque)
    usam a MESMA declaração. Três colunas em 375px dariam ~100px cada; no
    `--3` o terceiro por peso desce para a segunda linha da grade, na mesma
    largura e com o mesmo leiaute — só a posição muda, e ela vem do
    `share_real` via `ordenarPorPeso`."""
    bloco = _bloco_mobile()
    m = re.search(
        r"\.sentiment-groups\.sentiment-groups--2,\s*"
        r"\.sentiment-groups\.sentiment-groups--3\s*\{([^}]*)\}", bloco)
    assert m, ("`--2` e `--3` deixaram de compartilhar a mesma declaração "
               "de grade no mobile")
    assert "1fr 1fr" in m.group(1)


def test_a_contagem_de_bullets_nao_e_tocada_por_css():
    """Mesma contagem entre os grupos é garantia de DADO, e continua sendo.
    Nenhum `display: none`, `:nth-child` ou `max-height` pode aparecer no
    bloco mobile escondendo o sexto bullet de um lado para caber."""
    bloco = _bloco_mobile()
    for arma in ("display: none", "display:none", ":nth-child", ":nth-of-type",
                 "-webkit-line-clamp", "max-height"):
        assert arma not in bloco, (
            f"{arma!r} no bloco mobile — bullet escondido não é bullet curto")


# =====================================================================
# 3. O desktop não foi tocado
# =====================================================================

def test_a_regra_do_desktop_continua_identica():
    css = _sem_comentarios(_txt(CSS))
    esperado = (
        "@media (min-width: 720px) {\n"
        "  .sentiment-groups.sentiment-groups--2 { grid-template-columns: 1fr 1fr; }\n"
        "  .sentiment-groups.sentiment-groups--3 { grid-template-columns: 1fr 1fr 1fr; }\n"
        "}")
    assert esperado in css, (
        "a regra de ≥720px mudou — a entrega era só do modo mobile")


def test_o_bloco_novo_inteiro_vive_abaixo_de_640px():
    """A faixa 641-719px (tablet em retrato estreito) empilhava antes e
    continua empilhando: o bloco não pode ter vazado para fora da media
    query nem ter adotado um breakpoint mais largo."""
    css = _txt(CSS)
    i = css.index(MARCA)
    j = css.index("@media", i)
    # entre a marca e a media query só pode haver o fim do comentário
    assert "}" not in css[i:j].replace("*/", ""), (
        "há declaração solta entre o comentário do bloco e a media query")
    assert css[j:].startswith("@media (max-width: 640px) {"), (
        "o bloco mobile mudou de breakpoint")


# =====================================================================
# 4. A ordem no arquivo — o defeito real desta sessão
# =====================================================================

def test_o_bloco_mobile_vem_depois_das_regras_que_ele_sobrescreve():
    """`@media` NÃO soma especificidade.

    `.theme__name { font-size: 0.875rem }` dentro da media query e
    `.theme__name { font-size: 1rem }` fora dela têm a MESMA
    especificidade (0,1,0): quem vence é a última do arquivo. A primeira
    versão desta entrega declarou o bloco ao lado de `.sentiment-groups`,
    ~470 linhas ANTES de `.theme__name` — a grade de duas colunas aplicava
    e a tipografia não, em silêncio. Este teste falha se alguém mover o
    bloco para "junto de quem ele modifica", que é a arrumação óbvia e
    errada.
    """
    css = _txt(CSS)
    pos_bloco = css.index(MARCA)
    for seletor in (".theme__name {", ".themes {", ".theme__bar {",
                    ".theme__toggle {", ".theme__example-inner {",
                    ".group__obs {", ".group__header {", ".group__share {",
                    ".group__janela {", ".mode-warning {"):
        pos = css.index(seletor)
        assert pos < pos_bloco, (
            f"{seletor} está DEPOIS do bloco mobile e vence dele — a "
            "sobrescrita do celular vira silenciosamente inativa")


# =====================================================================
# 5. Piso de legibilidade
# =====================================================================

def test_o_nome_do_tema_nao_desce_abaixo_de_13px():
    """13px é o piso que o projeto já pratica (`.mosaic-cell__title`, com
    o número escrito no comentário). A coluna do mobile tem ~160px; a
    tentação de ganhar altura encolhendo a fonte é permanente, e é aqui
    que ela para."""
    bloco = _bloco_mobile()
    m = re.search(r"\.theme__name\s*\{[^}]*font-size:\s*([\d.]+)rem", bloco)
    assert m, "o bloco mobile não declara mais o corpo do nome do tema"
    px = float(m.group(1)) * 16
    assert px >= 13, f"nome do tema em {px}px — abaixo do piso de 13px"


def test_o_alvo_de_toque_do_aprofundar_continua_em_44px():
    """A regra vive em `@media (hover: none)` e o bloco mobile só zera o
    `margin-top` dela. Encolher o alvo seria o caminho mais fácil para
    ganhar ~260px por coluna, e é o que este teste impede."""
    css = _sem_comentarios(_txt(CSS))
    # há dois `@media (hover: none)` na folha; o do alvo de toque é o que
    # fala de `.theme__toggle`.
    blocos = [b for b in re.findall(r"@media \(hover: none\) \{(.*?)\n\}",
                                    css, re.S) if ".theme__toggle" in b]
    assert len(blocos) == 1, "o `@media (hover: none)` do APROFUNDAR sumiu"
    assert "min-height: 44px" in blocos[0]
    bloco = _bloco_mobile()
    m2 = re.search(r"\.theme__toggle\s*\{([^}]*)\}", bloco)
    assert m2, "`.theme__toggle` saiu do bloco mobile"
    assert "min-height" not in m2.group(1), (
        "o bloco mobile passou a mexer na altura do alvo de toque")


# =====================================================================
# 6. Nenhum número foi reformatado
# =====================================================================

def test_as_strings_com_algarismo_continuam_as_mesmas_no_js():
    """A entrega era de CSS. As três strings visíveis que carregam
    algarismo — o peso do grupo, a faixa de estrelas e a janela da amostra
    — continuam montadas em `filme.js` exatamente como antes; o mobile só
    decide onde elas quebram de linha."""
    js = _txt(FILME_JS)
    assert 'share.textContent = "~" + b.share_real + "% das notas";' in js
    assert 'return "★ " + starTxt(lo) + "–" + starTxt(hi);' in js
    assert 'return "escritas majoritariamente " + quando;' in js


def test_a_proveniencia_do_bullet_nao_virou_disclosure():
    """A barra de frequência é a proveniência visível de cada bullet e ela
    não pode ter sido escondida atrás de clique para o bloco caber: a
    `.theme__bar` continua fora de qualquer `.theme__example`, e o bloco
    mobile só ajusta a margem dela."""
    js = _txt(FILME_JS)
    assert 'bar.className = "theme__bar"' in js
    assert "row.appendChild(bar);" in js
    bloco = _bloco_mobile()
    m = re.search(r"\.theme__bar\s*\{([^}]*)\}", bloco)
    assert m, "`.theme__bar` saiu do bloco mobile"
    assert set(re.findall(r"([a-z-]+):", m.group(1))) <= {"margin"}, (
        "o bloco mobile passou a mexer em mais que a margem da barra")
