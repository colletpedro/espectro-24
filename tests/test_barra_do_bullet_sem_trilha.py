"""[v1.9.47] A BARRA DO BULLET PERDEU A TRILHA — sobra o traço.

A trilha (`#242832` + borda de 1px) fazia a barra ler como BARRA DE
PROGRESSO: trilha cheia + preenchimento é a gramática de uma coisa que se
completa. Ela saiu; sobra o traço na cor do grupo, sobre o fundo da página.

**A PREMISSA DA ENTREGA ESTAVA ERRADA E A MEDIÇÃO CORRIGIU.** O briefing
dizia que a largura vinha de `rotulo_forca` (ordinal, discreto). Não vem:
`rotulo_forca` só existe em `condicoes.*` e o `filme.js` não lê esse campo
em lugar nenhum. A largura é `mencoes_aproximadas / n_reviews_analisadas`,
CONTÍNUA — 633 itens e 60 larguras distintas no catálogo publicado. Isso
importa para o piso (abaixo) e está travado no teste que verifica a fonte
da largura, para que a confusão não volte.

O QUE ESTE ARQUIVO TRAVA:

  1. A TRILHA NÃO VOLTA. A caixa da barra não declara `background`,
     `border` nem `overflow` — os três são a trilha, e `overflow` só
     existia para recortar o preenchimento contra o raio dela.

  2. O PISO É INERTE NO CATÁLOGO, e é isso que o torna honesto. Sem
     trilha, um traço curto demais vira cisco; mas um piso ACIMA do menor
     item publicado estaria alongando esse item e mentindo sobre ele. O
     teste calcula a largura do MENOR item real na coluna mais estreita
     (mobile) e exige que o piso fique abaixo dela.

  3. NEUTRALIDADE ENTRE OS GRUPOS. A forma do traço (altura, raio, piso) é
     declarada UMA vez, no seletor compartilhado. A única coisa declarada
     por grupo é a COR — e as três regras por grupo declaram exatamente a
     mesma propriedade, nada além.

  4. NENHUMA DECISÃO DE QUANTIDADE NO FRONTEND. A largura continua saindo
     da fração do dado, e o denominador continua na alternativa textual da
     barra (que é o que sobrou dele agora que a trilha não o desenha).

  5. CONTRASTE. O traço passou a encostar no fundo da página em vez da
     trilha; os três tokens de grupo precisam passar o piso de 3:1 da
     WCAG 1.4.11 contra `--bg`.

Estrutural + aritmético, pela razão de sempre: o projeto não tem runner de
JS com DOM. As medidas de geometria da entrega foram feitas no navegador e
estão no relatório da sessão.
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = RAIZ / "frontend" / "css" / "styles.css"
FILME_JS = RAIZ / "frontend" / "js" / "filme.js"
DADOS = RAIZ / "frontend" / "data"

VIEWPORT_MOBILE_PX = 375          # o menor alvo declarado da entrega


def _txt(p):
    return p.read_text(encoding="utf-8")


def _sem_comentarios(fonte):
    return re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)


def _regra(seletor, css=None):
    """Corpo da PRIMEIRA regra `seletor { ... }` de TOPO, sem comentários.

    Ancorado em início de linha de propósito: sem a âncora, `.wrap` casaria
    dentro de `.site-footer .wrap`, e `.theme__bar` casaria dentro da
    sobrescrita indentada do bloco mobile.
    """
    css = _sem_comentarios(_txt(CSS)) if css is None else css
    m = re.search(r"(?m)^" + re.escape(seletor) + r"\s*\{([^}]*)\}", css)
    assert m, f"regra {seletor!r} não encontrada"
    return m.group(1)


def _props(corpo):
    return set(re.findall(r"([a-z-]+)\s*:", corpo))


def _num(corpo, prop):
    """Primeiro valor em px da propriedade."""
    m = re.search(re.escape(prop) + r"\s*:\s*([\d.]+)px", corpo)
    assert m, f"{prop} não encontrada (ou não está em px) em {corpo!r}"
    return float(m.group(1))


def _px_horizontal(corpo, prop):
    """Último valor em px de uma taquigrafia — em `padding: 0 20px` é o
    lado horizontal, que é o que interessa para a largura da coluna."""
    m = re.search(re.escape(prop) + r"\s*:\s*([^;]+);", corpo)
    assert m, f"{prop} não encontrada em {corpo!r}"
    vals = re.findall(r"([\d.]+)px", m.group(1))
    assert vals, f"{prop} sem valor em px: {m.group(1)!r}"
    return float(vals[-1])


# =====================================================================
# 1. A trilha não volta
# =====================================================================

def test_a_caixa_da_barra_nao_desenha_mais_trilha():
    """`background`/`border` eram a trilha. `overflow: hidden` era o
    recorte do preenchimento contra o raio dela — sem caixa, não há o que
    recortar, e mantê-lo esconderia silenciosamente um traço que
    estourasse a largura (o piso pode fazer isso numa coluna minúscula)."""
    corpo = _regra(".theme__bar")
    for proibida in ("background", "border", "border-radius", "overflow"):
        assert proibida not in _props(corpo), (
            f"`{proibida}` voltou para `.theme__bar` — a trilha está de "
            "volta, e com ela a leitura de barra de progresso")


def test_a_caixa_da_barra_so_declara_geometria():
    """Ela é o retângulo de referência (o 100% da fração) e o espaçador
    vertical. Nada mais deve morar nela."""
    assert _props(_regra(".theme__bar")) <= {"height", "margin"}


def test_nenhuma_cor_de_trilha_sobrou_na_folha():
    """`#242832` era um literal, sem token — se ele reaparecer em qualquer
    lugar, é a trilha voltando por outro seletor."""
    assert "#242832" not in _sem_comentarios(_txt(CSS)), (
        "a cor da trilha voltou à folha")


# =====================================================================
# 2. O piso de comprimento — inerte no catálogo publicado
# =====================================================================

def _coluna_mobile_px():
    """Largura da coluna de um grupo em 375px, derivada da folha (e não
    chutada): a página tem `padding: 0 20px` no `.wrap`, e o bloco de
    bullets do mobile é `1fr 1fr` com um `gap` de coluna. Medido no
    navegador em 375px: 159,5px — o mesmo que esta conta dá."""
    padding = _px_horizontal(_regra(".wrap"), "padding")
    i = _sem_comentarios(_txt(CSS)).index("@media (max-width: 640px)")
    m = re.search(r"\.sentiment-groups\s*\{\s*gap:\s*[\d.]+px\s+([\d.]+)px",
                  _sem_comentarios(_txt(CSS))[i:])
    assert m, "não achei o `gap` de coluna do bloco de bullets no mobile"
    gap = float(m.group(1))
    return (VIEWPORT_MOBILE_PX - 2 * padding - gap) / 2


def _menor_fracao_publicada():
    """A menor razão `mencoes_aproximadas / n_reviews_analisadas` do
    catálogo — é ela que produz o traço mais curto da tela."""
    menor, onde = 1.0, None
    for p in sorted(glob.glob(str(DADOS / "*.json"))):
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        for b in d.get("buckets") or []:
            for t in b.get("temas") or []:
                n = t.get("n_reviews_analisadas")
                if not n:
                    continue
                f = max(0.0, min(1.0, (t.get("mencoes_aproximadas") or 0) / n))
                if f < menor:
                    menor, onde = f, (Path(p).stem, b["bucket"], t.get("tema"))
    return menor, onde


def test_o_piso_de_comprimento_existe():
    """Sem trilha, largura zero é um traço INVISÍVEL — e o clamp de
    `_construir_temas` (`max(0, min(bruto, n))`) permite zero menções. O
    piso é a rede desse caso, que ainda não ocorreu no catálogo."""
    assert "min-width" in _props(_regra(".theme__bar span")), (
        "o piso de comprimento do traço sumiu: um tema com zero menções "
        "renderiza um traço de largura zero, invisível")


def test_o_piso_nao_alonga_nenhum_item_publicado():
    """**A trava de fidelidade desta entrega.**

    Um piso ACIMA do menor item real deixa de ser rede e vira distorção:
    ele desenha o item mais fraco do catálogo maior do que ele é, e o
    leitor compara traços que não são comparáveis. O piso só é honesto
    enquanto for INERTE — enquanto nenhum item publicado encostar nele.

    Se este teste cair, ou o piso subiu, ou o catálogo passou a publicar um
    item mais fraco que o piso. Nos dois casos a resposta é MEDIR de novo,
    não afrouxar o número.
    """
    piso = _num(_regra(".theme__bar span"), "min-width")
    coluna = _coluna_mobile_px()
    fracao, onde = _menor_fracao_publicada()
    menor_traco = fracao * coluna
    assert piso < menor_traco, (
        f"piso de {piso}px alonga o menor item do catálogo "
        f"({fracao * 100:.1f}% = {menor_traco:.1f}px na coluna de "
        f"{coluna:.1f}px, em {onde}) — o piso virou distorção")


def test_o_piso_ainda_le_como_traco_e_nao_como_ponto():
    """O piso existe para o traço degenerado não virar cisco. Um traço
    precisa ser mais comprido que alto para ler como traço; abaixo de 2×
    a altura ele lê como ponto."""
    piso = _num(_regra(".theme__bar span"), "min-width")
    altura = _num(_regra(".theme__bar"), "height")
    assert piso >= 2 * altura, (
        f"piso {piso}px contra altura {altura}px — o traço mínimo "
        "vira ponto")


# =====================================================================
# 3. Neutralidade entre os grupos
# =====================================================================

def test_a_forma_do_traco_e_declarada_uma_vez_para_os_tres_grupos():
    """Altura, raio e piso vivem no seletor COMPARTILHADO. Declarar forma
    por grupo é o caminho pelo qual um lado ganharia presença que o outro
    não tem."""
    corpo = _regra(".theme__bar span")
    for prop in ("height", "min-width", "border-radius"):
        assert prop in _props(corpo), f"{prop} saiu do seletor compartilhado"


def test_o_unico_por_grupo_e_a_cor():
    """As três regras por grupo existem, e declaram EXATAMENTE `background`
    — nada de largura, altura, opacidade ou margem por sentimento."""
    css = _sem_comentarios(_txt(CSS))
    vistos = {}
    for grupo in ("negativas", "medianas", "positivas"):
        # `\s+` e não um espaço: a folha alinha os três seletores em coluna,
        # e `medianas` (nome mais curto) leva dois espaços por causa disso.
        m = re.search(r'(?m)^\.group\[data-group="' + grupo
                      + r'"\]\s+\.theme__bar span\s*\{([^}]*)\}', css)
        assert m, f"a regra de cor de {grupo} sumiu"
        corpo = m.group(1)
        assert _props(corpo) == {"background"}, (
            f"a regra de {grupo} declara {_props(corpo)} — só a cor pode "
            "variar entre os grupos")
        vistos[grupo] = corpo.strip()
    assert len(vistos) == 3, "um dos três grupos perdeu a regra de cor"
    # e as três apontam para tokens DIFERENTES (senão a cor do grupo sumiu)
    assert len(set(vistos.values())) == 3


def test_o_traco_nao_ganha_opacidade_por_grupo():
    """Reforço do §0 pelo lado do que NÃO pode existir: opacidade por
    sentimento apagaria um lado sem mexer em largura nenhuma."""
    css = _sem_comentarios(_txt(CSS))
    for m in re.finditer(r'\.group\[data-group="\w+"\][^{}]*\.theme__bar[^{}]*\{([^}]*)\}', css):
        assert "opacity" not in _props(m.group(1))


# =====================================================================
# 4. Nenhuma decisão de quantidade no frontend
# =====================================================================

def test_a_largura_vem_da_fracao_do_dado():
    """O JS lê `mencoes_aproximadas` e `n_reviews_analisadas` e divide.
    Nenhuma escada, nenhum limiar, nenhum arredondamento de conveniência
    entra aqui — o frontend não decide quantidade."""
    js = _txt(FILME_JS)
    assert "var x = t.mencoes_aproximadas, n = t.n_reviews_analisadas;" in js
    assert "var pct = n > 0 ? Math.max(0, Math.min(100, (x / n) * 100)) : 0;" in js
    assert 'fill.style.width = pct.toFixed(1) + "%";' in js


def test_o_filme_js_nao_le_rotulo_forca():
    """**A premissa corrigida, travada.** `rotulo_forca` é o rótulo das
    CONDIÇÕES e não tem nada a ver com a barra do bullet. Se alguém ligar
    um no outro, a barra passa a codificar uma escada de 6 degraus no
    lugar de uma fração contínua — mudança de significado, não de estilo.
    """
    codigo = "\n".join(
        l for l in _txt(FILME_JS).splitlines() if not l.lstrip().startswith("//"))
    assert "rotulo_forca" not in codigo


def test_o_denominador_continua_na_alternativa_textual():
    """A trilha era a única representação VISUAL do denominador. Com ela
    fora, o `aria-label` da barra é onde `N` sobrevive — e a barra é
    `role="img"`, então sem ele ela fica muda."""
    js = _txt(FILME_JS)
    assert 'bar.setAttribute("role", "img");' in js
    assert ('bar.setAttribute("aria-label", "Mencionado em cerca de " + x '
            '+ " de " + n + " reviews");') in js


# =====================================================================
# 5. Contraste contra o fundo da página
# =====================================================================

def _luminancia(hexa):
    hexa = hexa.lstrip("#")
    canais = []
    for i in (0, 2, 4):
        c = int(hexa[i:i + 2], 16) / 255
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _token(nome):
    m = re.search(r"--" + nome + r":\s*(#[0-9a-fA-F]{6})", _txt(CSS))
    assert m, f"token --{nome} não encontrado"
    return m.group(1)


def test_o_traco_passa_o_piso_de_contraste_nos_tres_grupos():
    """WCAG 1.4.11 (componente gráfico não-textual): 3:1. O traço agora
    encosta no fundo da página, não na trilha — e o fundo é mais escuro
    que a trilha era, então o contraste SUBIU nos três. O teste existe
    para o dia em que alguém mexer num token de grupo."""
    fundo = _luminancia(_token("bg"))
    for nome in ("neg", "med", "pos"):
        l = _luminancia(_token(nome))
        hi, lo = max(l, fundo), min(l, fundo)
        razao = (hi + 0.05) / (lo + 0.05)
        assert razao >= 3.0, (
            f"--{nome} contra --bg: {razao:.2f}:1, abaixo do piso de 3:1")
