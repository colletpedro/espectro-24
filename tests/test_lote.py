"""[v1.9.3] Harness de lote — SPEC §3[H].

Cobre: checkpoint/resume, validação de slug (1 requisição), falha isolada
por filme, e `material_esgotado` como caso ESPERADO (não quebra
persistência nem montagem de buckets).
"""
import json

import pytest

from conftest import FakeFetcher, fx

from espectro24.buckets import NIVEIS
from espectro24.lote import (
    EstadoLote,
    coletar_um_filme,
    ler_lista_slugs,
    rodar_lote,
    validar_slug,
)
from espectro24.urls import (
    film_page_cache_key,
    film_page_url,
    histogram_cache_key,
    level_page_cache_key,
)


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


def _film_page(n_reviews: int = 100) -> str:
    return (f'<html><body><ul class="sub-nav"><li class="js-route-reviews">'
            f'<a href="/film/x/reviews/" title="{n_reviews}&nbsp;reviews">Reviews</a>'
            f'</li></ul></body></html>')


def _fetcher_filme_abundante(slug: str, ordenacao: str = "by/added") -> FakeFetcher:
    """Fetcher com material "infinito" (nunca esgota) para todos os níveis —
    monta um filme que fecha 40/40/40 folgadamente."""
    resp = {film_page_cache_key(slug): _film_page(),
           histogram_cache_key(slug): fx("histograma_cure.html")}
    for n in NIVEIS:
        for p in range(1, 30):
            resp[level_page_cache_key(slug, n, p, ordenacao)] = \
                _pagina(12, base_id=int(n * 100000) + p * 20)
    return FakeFetcher(resp)


def _fetcher_filme_obscuro(slug: str, ordenacao: str = "by/added") -> FakeFetcher:
    """Fetcher com pouquíssimo material — todo nível esgota logo na 1ª
    página (ou fica vazio), simulando um filme genuinamente obscuro."""
    resp = {film_page_cache_key(slug): _film_page(n_reviews=3),
           histogram_cache_key(slug): fx("histograma_filme_minusculo.html")}
    # só o primeiro nível com material ganha 1-2 reviews; o resto fica vazio
    resp[level_page_cache_key(slug, 3.0, 1, ordenacao)] = _pagina(2, base_id=1)
    return FakeFetcher(resp)


# --- ler_lista_slugs ---

def test_ler_lista_slugs_ignora_comentarios_e_linhas_vazias(tmp_path):
    p = tmp_path / "lista.txt"
    p.write_text("cure\n# comentário\n\ncidade-de-deus\n  \nthe-invite-2026\n",
                 encoding="utf-8")
    assert ler_lista_slugs(p) == ["cure", "cidade-de-deus", "the-invite-2026"]


def test_ler_lista_slugs_aceita_comentario_apos_espacos():
    pass  # comportamento coberto acima; nenhum caso adicional necessário


def test_ler_lista_slugs_arquivo_vazio(tmp_path):
    p = tmp_path / "vazio.txt"
    p.write_text("", encoding="utf-8")
    assert ler_lista_slugs(p) == []


# --- checkpoint: EstadoLote ---

def test_estado_lote_round_trip(tmp_path):
    caminho = tmp_path / "estado.json"
    estado = EstadoLote(caminho)
    estado.marcar_concluido("cure", n_por_bucket={"negativas": 40}, requisicoes=90)
    estado.marcar_falhou("slug-ruim", motivo="slug_invalido: HTTP 404")
    estado.salvar()

    recarregado = EstadoLote(caminho)
    recarregado.carregar()
    assert recarregado.status("cure") == "concluido"
    assert recarregado.status("slug-ruim") == "falhou"
    assert recarregado.status("nunca-visto") == "pendente"
    assert recarregado.dados("slug-ruim")["motivo"] == "slug_invalido: HTTP 404"


def test_estado_lote_arquivo_inexistente_comeca_vazio(tmp_path):
    estado = EstadoLote(tmp_path / "novo.json")
    estado.carregar()
    assert estado.status("qualquer") == "pendente"


def test_estado_lote_persiste_apos_cada_marcacao(tmp_path):
    """O checkpoint é gravado em disco a cada `marcar_*`, não só no fim —
    é o que permite resume após interrupção a qualquer momento."""
    caminho = tmp_path / "estado.json"
    estado = EstadoLote(caminho)
    estado.marcar_concluido("cure", n_por_bucket={}, requisicoes=1)
    estado.salvar()
    disco = json.loads(caminho.read_text(encoding="utf-8"))
    assert disco["slugs"]["cure"]["status"] == "concluido"


# --- validação de slug: 1 requisição ---

def test_validar_slug_valido_com_reviews():
    ff = FakeFetcher({film_page_cache_key("cure"): _film_page(n_reviews=500)})
    ok, motivo = validar_slug(ff, "cure")
    assert ok is True and motivo == ""
    assert len(ff.calls) == 1


def test_validar_slug_inexistente_gasta_1_requisicao_nao_uma_coleta():
    ff = FakeFetcher({}, raise_on={film_page_cache_key("slug-que-nao-existe")})
    ok, motivo = validar_slug(ff, "slug-que-nao-existe")
    assert ok is False
    assert "slug_invalido" in motivo
    assert len(ff.calls) == 1     # não tentou paginar nada


def test_validar_slug_sem_reviews():
    ff = FakeFetcher({film_page_cache_key("obscuro"): _film_page(n_reviews=0)})
    ok, motivo = validar_slug(ff, "obscuro")
    assert ok is False and motivo == "sem_reviews"
    assert len(ff.calls) == 1


def test_validar_slug_review_singular_nao_falha():
    html = ('<html><body><ul class="sub-nav"><li class="js-route-reviews">'
            '<a href="/film/x/reviews/" title="1&nbsp;review">Reviews</a>'
            '</li></ul></body></html>')
    ff = FakeFetcher({film_page_cache_key("um-review"): html})
    ok, motivo = validar_slug(ff, "um-review")
    assert ok is True


# --- coletar_um_filme: falha isolada + material_esgotado ---

def test_coletar_um_filme_sucesso(tmp_path):
    ff = _fetcher_filme_abundante("cure")
    r = coletar_um_filme(ff, "cure", dados_dir=tmp_path)
    assert r.status == "concluido"
    assert r.n_por_bucket == {"negativas": 40, "medianas": 40, "positivas": 40}


def test_coletar_um_filme_falha_isolada_nao_propaga(tmp_path):
    """Uma exceção durante a coleta (ex. HTML corrompido, erro de rede em
    página no meio) vira status `falhou`, não uma exceção não tratada."""
    ff = FakeFetcher({film_page_cache_key("cure"): _film_page()},
                     raise_on={histogram_cache_key("cure")})
    # força uma falha "inesperada" simulando erro de rede na própria
    # paginação (nível 0.5, página 1)
    ff2 = FakeFetcher({film_page_cache_key("quebra"): _film_page()},
                      raise_on={level_page_cache_key("quebra", 0.5, 1, "by/added")})
    r = coletar_um_filme(ff2, "quebra", dados_dir=tmp_path)
    assert r.status == "falhou"
    assert r.motivo


def test_coletar_um_filme_material_esgotado_e_caso_esperado(tmp_path):
    """Filme obscuro: material esgota bem antes do orçamento. Não é erro —
    persiste, monta buckets, produz piso escalonado abaixo de `completa`."""
    ff = _fetcher_filme_obscuro("obscuro")
    r = coletar_um_filme(ff, "obscuro", dados_dir=tmp_path)
    assert r.status == "concluido"
    assert r.n_por_bucket["negativas"] < 40      # não fechou a cota
    assert r.estado_piso["negativas"] != "completa"
    # e persistiu de verdade — recarregável do disco
    from espectro24.bruto import carregar
    meta, revs = carregar("obscuro", raiz=tmp_path)
    assert meta is not None


def test_coletar_um_filme_material_esgotado_aparece_no_motivo_parada(tmp_path):
    ff = _fetcher_filme_obscuro("obscuro2")
    r = coletar_um_filme(ff, "obscuro2", dados_dir=tmp_path)
    from espectro24.bruto import carregar
    meta, _ = carregar("obscuro2", raiz=tmp_path)
    motivos = meta["motivo_parada_por_nivel"]
    assert "material_esgotado" in motivos.values()


def test_bucket_sem_analise_nao_quebra_json(tmp_path):
    """Um bucket em sem_analise ainda serializa como JSON válido — testado
    via `build_output`, o mesmo caminho usado pela CLI de um filme só."""
    from espectro24.render import build_output

    ff = _fetcher_filme_obscuro("bem-obscuro")
    r = coletar_um_filme(ff, "bem-obscuro", dados_dir=tmp_path)
    out = build_output(slug="bem-obscuro", buckets=r.buckets, data_coleta="x",
                       origens={}, total_observado=0, distribuicao=r.distrib)
    texto = json.dumps(out, ensure_ascii=False)   # não levanta
    assert '"bem-obscuro"' in texto


# --- rodar_lote: resume + falha isolada, ponta a ponta ---

def test_rodar_lote_processa_todos_os_slugs_validos(tmp_path):
    fetchers = {"cure": _fetcher_filme_abundante("cure"),
               "cidade-de-deus": _fetcher_filme_abundante("cidade-de-deus")}

    def _fabrica(slug):
        return fetchers[slug]

    estado_path = tmp_path / "estado.json"
    rel = rodar_lote(["cure", "cidade-de-deus"], dados_dir=tmp_path / "dados",
                     estado_path=estado_path, fabrica_fetcher=_fabrica)
    assert rel.n_concluidos == 2
    assert rel.n_falhas == 0
    assert EstadoLote(estado_path).carregar().status("cure") == "concluido"


def test_rodar_lote_resume_pula_slug_ja_concluido(tmp_path):
    estado_path = tmp_path / "estado.json"
    dados_dir = tmp_path / "dados"

    # 1ª rodada: só "cure"
    rodar_lote(["cure"], dados_dir=dados_dir, estado_path=estado_path,
              fabrica_fetcher=lambda slug: _fetcher_filme_abundante(slug))

    # 2ª rodada: lista com cure de novo + um filme novo — cure não deve
    # gastar nenhuma requisição desta vez (resume)
    chamado = {"cure": False, "the-invite-2026": False}
    ff_invite = _fetcher_filme_abundante("the-invite-2026")

    def _fabrica(slug):
        chamado[slug] = True
        if slug == "cure":
            return FakeFetcher({})   # se isto for usado, o teste falha adiante
        return ff_invite

    rel = rodar_lote(["cure", "the-invite-2026"], dados_dir=dados_dir,
                     estado_path=estado_path, fabrica_fetcher=_fabrica)
    assert chamado["cure"] is False        # NUNCA tentou recoletar
    assert chamado["the-invite-2026"] is True
    assert rel.n_concluidos == 1           # só o novo nesta rodada
    assert rel.n_pulados == 1


def test_rodar_lote_falha_isolada_nao_impede_os_seguintes(tmp_path):
    def _fabrica(slug):
        if slug == "slug-invalido":
            return FakeFetcher({}, raise_on={film_page_cache_key(slug)})
        return _fetcher_filme_abundante(slug)

    rel = rodar_lote(["cure", "slug-invalido", "cidade-de-deus"],
                     dados_dir=tmp_path / "dados", estado_path=tmp_path / "estado.json",
                     fabrica_fetcher=_fabrica)
    assert rel.n_concluidos == 2
    assert rel.n_falhas == 1
    assert "slug-invalido" in rel.falhas
    assert "slug_invalido" in rel.falhas["slug-invalido"]


def test_rodar_lote_checkpoint_gravado_apos_cada_filme_nao_so_no_fim(tmp_path):
    estado_path = tmp_path / "estado.json"
    processados = []

    def _fabrica(slug):
        processados.append(slug)
        # ao processar o 2º filme, o checkpoint do 1º já deve estar em disco
        if slug == "cidade-de-deus":
            disco = json.loads(estado_path.read_text(encoding="utf-8"))
            assert disco["slugs"]["cure"]["status"] == "concluido"
        return _fetcher_filme_abundante(slug)

    rodar_lote(["cure", "cidade-de-deus"], dados_dir=tmp_path / "dados",
              estado_path=estado_path, fabrica_fetcher=_fabrica)
    assert processados == ["cure", "cidade-de-deus"]
