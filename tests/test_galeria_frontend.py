"""[v1.9.38] Galeria de pôsteres alternativos — travas no FRONTEND.

Mesma convenção de `test_frontend_constantes_hoisted.py`: checagem
TEXTUAL/estrutural sobre `filme.js`/`poster.js`, não um parser de JS nem
execução em runtime (o projeto não tem infraestrutura de teste JS). Cobre
o que o SPEC exige e um teste em Python consegue travar sem executar
JavaScript: posição no `render()`, e que galeria vazia não anexa nada
(§3[F] — "sem placeholder, sem estado de erro visível").
"""
import re
from pathlib import Path

FILME_JS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "filme.js"
POSTER_JS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "poster.js"


def _filme_js():
    return FILME_JS.read_text(encoding="utf-8")


def _poster_js():
    return POSTER_JS.read_text(encoding="utf-8")


def test_galeria_vem_depois_da_narrativa_e_antes_da_pesquisa():
    """SPEC: 'DEPOIS da narrativa, ANTES da pesquisa. Não mover nada
    acima.' Checa a ORDEM das três linhas dentro de `render()`."""
    fonte = _filme_js()
    m_narrativa = re.search(r"narrativaCollapsedBlock\(f\.narrativa\)", fonte)
    m_galeria = re.search(r"galeriaBlock\(f\)", fonte)
    m_pesquisa = re.search(r"window\.mountSurvey\(app, f\)", fonte)
    assert m_narrativa and m_galeria and m_pesquisa, (
        "uma das três chamadas não foi encontrada em render() — a âncora "
        "deste teste mudou de forma")
    assert m_narrativa.start() < m_galeria.start() < m_pesquisa.start(), (
        "a galeria não está entre a narrativa e a pesquisa")


def test_nenhum_bloco_existente_antes_da_narrativa_foi_movido():
    """A ordem anterior (header → ficha → barra → condições → divisor →
    bullets → veredito) não pode ter mudado de posição RELATIVA — a
    restrição da entrega era acrescentar, não redesenhar."""
    fonte = _filme_js()
    ordem_esperada = [
        r"app\.appendChild\(header\(f\)\)",
        r"app\.appendChild\(fichaBlock\(",
        r"app\.appendChild\(proporcaoBlock\(f\)\)",
        r"condicoesBlock\(f\)",
        r"app\.appendChild\(detailDivider\(\)\)",
        r"app\.appendChild\(sentimentGroupsBlock\(f\)\)",
        r"veredictoBlock\(f\)",
        r"narrativaCollapsedBlock\(f\.narrativa\)",
        r"galeriaBlock\(f\)",
    ]
    posicoes = []
    for padrao in ordem_esperada:
        m = re.search(padrao, fonte)
        assert m, f"âncora não encontrada: {padrao}"
        posicoes.append(m.start())
    assert posicoes == sorted(posicoes), (
        "a ordem dos blocos em render() mudou — um bloco existente foi "
        "deslocado, o que a entrega da galeria não deveria fazer")


def test_render_so_anexa_a_galeria_se_o_bloco_nao_for_null():
    fonte = _filme_js()
    assert re.search(r"var galeria = galeriaBlock\(f\);", fonte)
    assert re.search(r"if \(galeria\) app\.appendChild\(galeria\);", fonte)


def test_galeria_block_retorna_null_quando_nao_ha_itens():
    """'Filme com galeria vazia: seção não renderiza. Sem placeholder, sem
    estado de erro visível ao leitor' — a função precisa ter esse retorno
    ANTES de criar qualquer elemento de seção."""
    fonte = _filme_js()
    m_func = re.search(r"function galeriaBlock\(f\) \{(.*?)\n  \}", fonte, re.S)
    assert m_func, "função galeriaBlock não encontrada"
    corpo = m_func.group(1)
    m_guarda = re.search(r"if \(!itens\.length\) return null;", corpo)
    m_section = re.search(r"createElement\(\"section\"\)", corpo)
    assert m_guarda and m_section
    assert m_guarda.start() < m_section.start(), (
        "a checagem de galeria vazia precisa vir ANTES de criar a seção — "
        "senão uma seção vazia (ainda que sem itens) chega a ser anexada")


def test_montar_galeria_existe_e_e_exportado_em_espectro_poster():
    fonte = _poster_js()
    assert "function montarGaleria(" in fonte
    assert re.search(r"montarGaleria:\s*montarGaleria", fonte), (
        "montarGaleria não está no objeto exportado window.ESPECTRO_POSTER")


def test_montar_galeria_nunca_retorna_null_so_array_vazio():
    """Diferença deliberada de `montarBackdrop` (que retorna `null`): quem
    chama (`galeriaBlock`) testa `.length`, não truthiness — um array vazio
    é o contrato, não `null`."""
    fonte = _poster_js()
    m_func = re.search(r"function montarGaleria\(.*?\) \{(.*?)\n  \}", fonte, re.S)
    assert m_func
    corpo = m_func.group(1)
    assert "return []" in corpo


def test_atribuicao_ao_tmdb_menciona_a_galeria():
    """Obrigação legal (não opcional): a página de créditos precisa cobrir
    as imagens da galeria, não só o pôster principal."""
    creditos = (Path(__file__).resolve().parent.parent / "frontend"
                / "creditos.html").read_text(encoding="utf-8")
    assert "galeria de pôsteres alternativos" in creditos
