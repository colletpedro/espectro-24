"""[v1.9.2, Entrega 2] Posicionamento estratificado por profundidade (§3[B]).

Substitui a paginação puramente consecutiva: uma reserva do orçamento de
cada nível é posicionada em progressão geométrica além do bloco raso, para
que a amostra cubra profundidade real, não só o mais recente. O custo em
requisições não aumenta — muda QUAIS páginas são buscadas, não QUANTAS.
"""
import pytest

from conftest import FakeFetcher

from espectro24.alocacao import dividir_raso_profundo, redistribuir_deficit
from espectro24.collector import raspar_nivel
from espectro24.urls import level_page_cache_key


def _pagina(n_reviews: int, base_id: int = 0) -> str:
    itens = []
    for i in range(n_reviews):
        vid = base_id + i
        itens.append(f"""
<article class="production-viewing -viewing">
  <a class="avatar" href="/a{vid}/"><img alt="a{vid}"/></a>
  <span class="attribution-detail">
    <a class="context" href="/a{vid}/film/filme/"><span class="owner">
      <strong class="displayname">a{vid}</strong></span></a>
  </span>
  <span class="date"><time class="timestamp" datetime="2026-01-01">2026-01-01</time></span>
  <div class="body-text js-review-body" data-full-text-url="/s/full-text/viewing:{vid}/" lang="en">
    <p>{"x" * 200}</p>
  </div>
  <p data-likeable-identifier='{{"uid":"viewing:{vid}","type":"viewing"}}'></p>
</article>""")
    return "<html><body>" + "".join(itens) + "</body></html>"


def _fetcher_profundidade(slug: str, nivel: float, profundidade: int,
                          ordenacao: str = "by/added") -> FakeFetcher:
    """Fetcher cujo nível tem exatamente `profundidade` páginas de conteúdo
    (cada uma com 1 review, id único por página) — além disso, tudo vazio."""
    resp = {}
    for p in range(1, profundidade + 1):
        resp[level_page_cache_key(slug, nivel, p, ordenacao)] = _pagina(1, base_id=p * 1000)
    return FakeFetcher(resp)


def _paginas_buscadas(ff: FakeFetcher, slug: str, nivel: float,
                      ordenacao: str = "by/added") -> list[int]:
    """Extrai os números de página das chamadas feitas a este nível, em ordem."""
    import re
    saida = []
    for url, _key in ff.calls:
        m = re.search(r"/page/(\d+)/", url)
        if m:
            saida.append(int(m.group(1)))
    return saida


# --- nº de páginas buscadas == orçamento, sempre que há profundidade suficiente ---

@pytest.mark.parametrize("orcamento", [4, 8, 10, 16, 20])
def test_numero_de_requisicoes_nunca_excede_o_orcamento(orcamento):
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1000)  # "infinita"
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    assert len(ff.calls) <= orcamento
    assert r.paginas_gastas <= orcamento


@pytest.mark.parametrize("orcamento", [4, 8, 10, 16])
def test_paginas_gastas_bate_o_orcamento_quando_ha_profundidade_de_sobra(orcamento):
    """Caso COMUM: profundidade real >> orçamento — todas as posições
    tentadas têm conteúdo, então o orçamento é usado por inteiro."""
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1000)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    assert r.paginas_gastas == orcamento
    assert r.motivo_parada == "orcamento_esgotado"


# --- sem posições duplicadas ---

@pytest.mark.parametrize("orcamento", [4, 8, 10, 16, 20])
def test_sem_posicoes_duplicadas(orcamento):
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1000)
    raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = _paginas_buscadas(ff, "cure", 4.0)
    assert len(paginas) == len(set(paginas))


# --- reserva profunda respeitada quando há profundidade ---

def test_posicoes_profundas_vao_alem_do_bloco_raso():
    orcamento = 16   # dividir_raso_profundo(16) == (12, 4)
    n_raso, n_profundo = dividir_raso_profundo(orcamento)
    assert (n_raso, n_profundo) == (12, 4)
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1000)
    raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = _paginas_buscadas(ff, "cure", 4.0)
    # bloco raso: 1..12 consecutivas
    assert sorted(p for p in paginas if p <= n_raso) == list(range(1, n_raso + 1))
    # bloco profundo: progressão geométrica a partir do fim do raso
    profundas = sorted(p for p in paginas if p > n_raso)
    assert profundas == [n_raso + 2, n_raso + 4, n_raso + 8, n_raso + 16]


def test_reviews_da_amostra_tem_pagina_origem_espalhada():
    """Consequência observável: a amostra cobre posições MUITO além do que a
    paginação puramente consecutiva alcançaria com o mesmo orçamento."""
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1000)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=16)
    origens = {rev.pagina_origem for rev in r.reviews}
    assert max(origens) > 16   # nenhum esquema consecutivo com orçamento 16 chegaria aqui


# --- degrada para consecutivo quando o nível é raso ---

@pytest.mark.parametrize("profundidade", [1, 2, 3])
def test_degrada_para_consecutivo_quando_nivel_e_mais_raso_que_o_bloco_raso(profundidade):
    orcamento = 16
    ff = _fetcher_profundidade("cure", 4.0, profundidade=profundidade)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = _paginas_buscadas(ff, "cure", 4.0)
    # nunca tentou nada além do bloco raso — esgotou antes de chegar lá
    assert max(paginas) <= dividir_raso_profundo(orcamento)[0]
    assert r.motivo_parada == "material_esgotado"
    assert r.paginas_gastas == profundidade


def test_degenerado_nivel_com_1_pagina():
    ff = _fetcher_profundidade("cure", 4.0, profundidade=1)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=16)
    assert r.paginas_gastas == 1
    assert r.motivo_parada == "material_esgotado"


def test_degenerado_nivel_vazio():
    ff = _fetcher_profundidade("cure", 4.0, profundidade=0)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=16)
    assert r.paginas_gastas == 0
    assert r.motivo_parada == "material_esgotado"
    assert len(ff.calls) == 1


def test_degenerado_orcamento_maior_que_profundidade_real():
    """Profundidade real (20) menor que o orçamento (40) — fecha curto,
    honestamente, sem inventar nem exceder."""
    ff = _fetcher_profundidade("cure", 4.0, profundidade=20)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=40)
    assert r.motivo_parada == "material_esgotado"
    assert r.paginas_gastas <= 20


# --- descoberta: página vazia em K redistribui dentro de [1, K-1], nunca além ---

def test_descoberta_no_bloco_profundo_nao_ultrapassa_a_posicao_vazia():
    orcamento = 16
    n_raso, n_profundo = dividir_raso_profundo(orcamento)   # (12, 4) -> geométricas 14,16,20,28
    # profundidade real = 15: geométrica 14 tem conteúdo, 16 não.
    ff = _fetcher_profundidade("cure", 4.0, profundidade=15)
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = _paginas_buscadas(ff, "cure", 4.0)
    assert max(paginas) < n_raso + 16    # nunca tentou 20 nem 28 (além da vazia)
    assert n_raso + 16 not in paginas and n_raso + 8 not in paginas
    assert r.motivo_parada == "material_esgotado"


def test_backfill_so_usa_posicoes_ja_confirmadas():
    """profundidade=14: geométrica n_raso+2 (=14) tem conteúdo, n_raso+4 (=16)
    não. Só n_raso+2 foi confirmado — não há posição segura entre n_raso e
    n_raso+2 sobrando pra redistribuir (n_raso+1 é a única, e cabe)."""
    orcamento = 16
    n_raso, _ = dividir_raso_profundo(orcamento)  # 12
    ff = _fetcher_profundidade("cure", 4.0, profundidade=n_raso + 2)  # == 14
    r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = set(_paginas_buscadas(ff, "cure", 4.0))
    # nunca busca além da profundidade real confirmada
    assert all(p <= n_raso + 2 or p == n_raso + 4 for p in paginas)
    assert (n_raso + 4) in paginas    # a que revelou o limite (vazia)
    assert (n_raso + 1) in paginas    # backfill dentro do intervalo confirmado


def test_no_maximo_1_pagina_desperdicada_por_nivel():
    for profundidade in range(0, 30):
        ff = _fetcher_profundidade("cure", 4.0, profundidade=profundidade)
        r = raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=16)
        paginas = _paginas_buscadas(ff, "cure", 4.0)
        vazias = [p for p in paginas if p > profundidade]
        assert len(vazias) <= 1, f"profundidade={profundidade}: vazias={vazias}"


# --- redistribuição REAPROVEITA redistribuir_deficit — nenhum caminho novo ---

def test_backfill_e_literalmente_redistribuir_deficit():
    """Reproduz manualmente a chamada que `raspar_nivel` faz por dentro, no
    caso de descoberta, e confere que os resultados batem — não há uma
    segunda fórmula de redistribuição de posições."""
    orcamento = 16
    n_raso, n_profundo = dividir_raso_profundo(orcamento)  # (12, 4)
    geometricas = [n_raso + 2 ** k for k in range(1, n_profundo + 1)]  # 14,16,20,28
    # profundidade real = 15 -> geométrica 14 sucesso, 16 vazia (k_vazio)
    maior_confirmada = n_raso + 2
    candidatas = [p for p in range(n_raso + 1, maior_confirmada + 1)
                 if p not in geometricas[:1]]
    universo = sorted(set(geometricas) | set(candidatas))
    alocacao_pos = {p: (1 if p in geometricas else 0) for p in universo}
    disponivel_pos = {p: (1 if p <= maior_confirmada else 0) for p in universo}
    esperado = redistribuir_deficit(alocacao_pos, disponivel_pos)
    extras_esperados = sorted(p for p in candidatas if esperado.get(p, 0) == 1)

    ff = _fetcher_profundidade("cure", 4.0, profundidade=15)
    raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    paginas = set(_paginas_buscadas(ff, "cure", 4.0))
    for p in extras_esperados:
        assert p in paginas


# --- custo: estratificado vs. consecutivo, mesmo orçamento — IGUAIS no caso comum ---

def _consecutivo_n_requisicoes(profundidade: int, orcamento: int) -> int:
    """Simula quantas requisições um esquema puramente CONSECUTIVO faria."""
    n = 0
    for pagina in range(1, orcamento + 1):
        n += 1
        if pagina > profundidade:
            break
    return n


@pytest.mark.parametrize("orcamento", [4, 8, 16])
def test_custo_igual_ao_consecutivo_quando_profundidade_e_folgada(orcamento):
    """A premissa central da Entrega 2: com material de sobra (o caso comum
    — é justamente por isso que vale a pena reservar profundidade), o
    posicionamento estratificado gasta EXATAMENTE o mesmo número de
    requisições que a paginação consecutiva teria gasto."""
    profundidade = 1000  # bem além de qualquer orçamento testado
    ff = _fetcher_profundidade("cure", 4.0, profundidade=profundidade)
    raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=orcamento)
    estratificado = len(ff.calls)
    consecutivo = _consecutivo_n_requisicoes(profundidade, orcamento)
    assert estratificado == consecutivo == orcamento


def test_custo_nunca_maior_que_o_orcamento_em_nenhum_caso():
    for profundidade in range(0, 40):
        ff = _fetcher_profundidade("cure", 4.0, profundidade=profundidade)
        raspar_nivel(ff, "cure", 4.0, alvo=0, teto_paginas=16)
        assert len(ff.calls) <= 16
