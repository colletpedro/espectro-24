"""[v1.9.29, §3[F]] O ESCOPO do harness de retrofit da ficha, travado por teste.

`scripts/enriquecer_ficha.py` não passa pela guarda de lote de
`publicar_catalogo.py` (`LIMITE_LOTE_SEM_CONFIRMACAO = 5`), e não deve:
enriquecer a ficha é UMA requisição de API por filme, não re-scrapeia o
superset do Letterboxd e não toca o histórico `passadas` do bruto.

Mas vale aqui a mesma lição da v1.9.21 e da v1.9.25: **harness novo com
"cuidado diferente" é exatamente como se abre o próximo footgun**. O risco é
sobrescrever 35 JSONs publicados, e não é zero. Então o escopo é travado por
TESTE, não por disciplina, com a mesma técnica que pegou o footgun original —
substituir os pontos de entrada por `pytest.fail` e rodar de verdade. Leitura
de código não pega o que uma chamada indireta faz; isto pega.

Quatro travas:
  1. nenhum estágio a montante é chamado;
  2. NENHUMA republicação é disparada, nem por caminho indireto (a guarda de
     lote não é acionada porque `publicar_catalogo` nem entra em jogo);
  3. rodar altera APENAS as chaves novas DENTRO de `ficha` — diff campo a
     campo do resto do documento;
  4. a única rede que sai daqui é a do TMDB.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


def _ef():
    import enriquecer_ficha
    return enriquecer_ficha


SLUG = "the-godfather"

# A resposta que `buscar_ficha` devolveria — com os campos novos preenchidos
# e os de identidade batendo com o que está no disco. O teste nunca vai à
# rede; quem foi à rede foi a sondagem que fixou estes valores (2026-08-27,
# tmdb id 238).
NOVA_FICHA = {
    "poster_path": "/oJagOzBu9Rdd9BrciseCm3U3MCU.jpg",
    "poster_largura": 2000,
    "poster_altura": 3000,
    "backdrop_paths": ["/a.jpg", "/b.jpg"],
    "tmdb_id": 238,
    "tmdb_fetched_at": "2026-08-27T00:00:00+00:00",
}


@pytest.fixture
def documento():
    caminho = RAIZ / "resultado" / f"{SLUG}.json"
    if not caminho.exists():
        pytest.skip(f"{SLUG} não publicado neste checkout")
    return json.loads(caminho.read_text(encoding="utf-8"))


@pytest.fixture
def sandbox(tmp_path, documento, monkeypatch):
    """Um `resultado/` de mentira com UM filme real dentro, para o harness
    escrever sem tocar no repositório."""
    ef = _ef()
    (tmp_path / f"{SLUG}.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(ef, "RESULTADO_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sem_rede(monkeypatch, documento):
    """Substitui `buscar_ficha` por uma resposta fixa — o harness roda
    inteiro, sem rede. A identidade (título/ano/diretor) é copiada do
    documento real para que a guarda de identidade passe."""
    ef = _ef()
    antiga = documento["ficha"]
    resposta = dict(NOVA_FICHA)
    for k in ("titulo", "ano", "diretor"):
        resposta[k] = antiga.get(k)

    def falso(titulo, ano, cache_dir=None, **kw):
        return dict(resposta), None, None

    monkeypatch.setattr(ef, "buscar_ficha", falso)
    return resposta


# ===========================================================================
# (1) Nenhum estágio a montante
# ===========================================================================

def _explode(humano):
    def falha(*a, **kw):
        pytest.fail(f"o harness de ficha chamou {humano} — ele não pode "
                    f"rodar nenhum estágio a montante")
    return falha


def test_nao_chama_NENHUM_estagio_a_montante(sandbox, sem_rede, monkeypatch):
    """A trava principal. Cada ponto de entrada de coleta, seleção,
    classificação, verificação, síntese, [D3], narrativa e veredito vira um
    `pytest.fail`; se o harness tocar em qualquer um deles, o teste diz
    QUAL."""
    from espectro24 import eixos, narrador, pipeline, rotulagem
    from espectro24 import selecao, synthesize, veredito

    proibidos = [
        (pipeline, "collect_all_levels", "coleta"),
        (pipeline, "run_pipeline", "pipeline completo"),
        (pipeline, "montar_eixos", "[D3]/eixos"),
        (pipeline, "montar_buckets", "montagem de buckets"),
        (selecao, "selecionar", "seleção downstream"),
        (synthesize, "synthesize_bucket", "síntese [D]"),
        (synthesize, "build_output", "montagem de output"),
        (eixos, "montar_bloco", "bloco de eixos"),
        (rotulagem, "rotular", "[D3] rotulagem"),
        (narrador, "narrar", "narrativa [D2]"),
        (veredito, "gerar", "veredito [V]"),
    ]
    for modulo, nome, humano in proibidos:
        if not hasattr(modulo, nome):
            continue
        monkeypatch.setattr(modulo, nome, _explode(humano))

    assert _ef().enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)["ok"]


# ===========================================================================
# (2) Nenhuma republicação, nem por caminho indireto
# ===========================================================================

def test_nao_dispara_republicacao_por_nenhum_caminho(sandbox, sem_rede,
                                                     monkeypatch):
    """A guarda de lote (`LIMITE_LOTE_SEM_CONFIRMACAO = 5`) protege
    `publicar_catalogo.py`. Este harness não passa por ela e não deve — o que
    o teste exige é que ele também não a CONTORNE: publicar tem de continuar
    inalcançável daqui, inclusive por chamada indireta.

    Envenena os três pontos de entrada de publicação E o `subprocess.run` que
    `publicar_um` usa para invocar o CLI.
    """
    import subprocess

    import publicar_catalogo as pc

    for nome in ("publicar_um", "cmd_publicar", "checar_tamanho_do_lote"):
        if hasattr(pc, nome):
            monkeypatch.setattr(pc, nome, _explode(f"publicar_catalogo.{nome}"))
    monkeypatch.setattr(subprocess, "run", _explode("subprocess.run (CLI)"))

    assert _ef().enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)["ok"]


def test_o_harness_nao_importa_publicacao_nem_cli(sandbox):
    """Complemento estrutural: o arquivo não deve nem mencionar os módulos de
    publicação. Se um dia alguém precisar republicar, o caminho é o script de
    publicação — não este."""
    fonte = (RAIZ / "scripts" / "enriquecer_ficha.py").read_text(encoding="utf-8")
    codigo = fonte.split('"""', 2)[-1]     # fora do docstring, que os cita
    for proibido in ("publicar_catalogo", "espectro24.cli", "subprocess",
                     "run_pipeline"):
        assert proibido not in codigo, \
            f"enriquecer_ficha.py referencia {proibido!r} fora do docstring"


# ===========================================================================
# (3) Só as chaves novas de `ficha` mudam
# ===========================================================================

def test_so_as_chaves_novas_da_ficha_mudam(sandbox, documento, sem_rede):
    """Diff CAMPO A CAMPO do documento inteiro. Todo campo fora de `ficha`
    sai idêntico; dentro de `ficha`, só as chaves de `CHAVES_NOVAS` mudam.

    Se este teste falhar, "retrofit não é republicar" deixou de ser verdade,
    e nenhum diff manual é substituto: o documento tem dezenas de milhares de
    campos.
    """
    ef = _ef()
    ef.enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    for chave in set(documento) | set(depois):
        if chave == "ficha":
            continue
        assert json.dumps(depois.get(chave), ensure_ascii=False, sort_keys=True) \
            == json.dumps(documento.get(chave), ensure_ascii=False, sort_keys=True), \
            f"o campo {chave!r} mudou"

    antes_f, depois_f = documento["ficha"], depois["ficha"]
    mudaram = {k for k in set(antes_f) | set(depois_f)
               if antes_f.get(k) != depois_f.get(k)}
    assert mudaram <= set(ef.CHAVES_NOVAS), \
        f"a ficha mudou fora de CHAVES_NOVAS: {sorted(mudaram - set(ef.CHAVES_NOVAS))}"
    assert mudaram, "o harness não gravou nada"


def test_a_ordem_das_chaves_e_preservada(sandbox, documento, sem_rede):
    """As chaves novas entram no FIM da ficha, e nada é reordenado — um diff
    de git legível é o que torna o retrofit auditável por leitura humana,
    além do teste."""
    _ef().enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    assert list(depois) == list(documento), "ordem das chaves de topo mudou"
    novas = set(_ef().CHAVES_NOVAS)
    esperado = [k for k in documento["ficha"] if k not in novas]
    assert [k for k in depois["ficha"] if k not in novas] == esperado


def test_dry_run_nao_grava(sandbox, documento, sem_rede):
    antes = (sandbox / f"{SLUG}.json").read_text(encoding="utf-8")
    r = _ef().enriquecer_um(SLUG, cache_dir=sandbox, dry_run=True, saida=sandbox)
    assert r["ok"] is True
    assert (sandbox / f"{SLUG}.json").read_text(encoding="utf-8") == antes


# ===========================================================================
# (4) Comportamento aditivo — ausência não é erro
# ===========================================================================

def test_filme_sem_ficha_e_pulado_nao_e_erro(tmp_path, monkeypatch):
    ef = _ef()
    monkeypatch.setattr(ef, "RESULTADO_DIR", tmp_path)
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "ficha": None}), encoding="utf-8")
    r = ef.enriquecer_um("x", cache_dir=tmp_path, saida=tmp_path)
    assert r == {"slug": "x", "ok": False, "motivo": "sem_ficha"}


def test_falha_de_rede_nao_grava_e_nao_levanta(sandbox, monkeypatch):
    ef = _ef()
    monkeypatch.setattr(ef, "buscar_ficha",
                        lambda *a, **kw: (None, "TMDB indisponível", None))
    antes = (sandbox / f"{SLUG}.json").read_text(encoding="utf-8")
    r = ef.enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)
    assert r["ok"] is False and "indisponível" in r["motivo"]
    assert (sandbox / f"{SLUG}.json").read_text(encoding="utf-8") == antes


def test_filme_sem_poster_e_estado_valido_nao_falha(sandbox, documento,
                                                    monkeypatch):
    """Ausência de pôster é ESTADO, não erro (§3[F]): os campos entram com
    `None`/lista vazia, e o frontend desenha o vazio."""
    ef = _ef()
    antiga = documento["ficha"]
    resposta = {"poster_path": None, "poster_largura": None,
                "poster_altura": None, "backdrop_paths": [],
                "tmdb_id": 238, "tmdb_fetched_at": "2026-08-27T00:00:00+00:00",
                "titulo": antiga.get("titulo"), "ano": antiga.get("ano"),
                "diretor": antiga.get("diretor")}
    monkeypatch.setattr(ef, "buscar_ficha", lambda *a, **kw: (resposta, None, None))

    r = ef.enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)
    assert r["ok"] is True and r["poster"] is False
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert depois["ficha"]["poster_path"] is None
    assert depois["ficha"]["backdrop_paths"] == []


def test_identidade_divergente_aborta_o_filme_sem_gravar(sandbox, monkeypatch):
    """Reconsultar o TMDB é reabrir a desambiguação que o pipeline já fez.
    Se a resposta descreve outro filme, nada é gravado — melhor ficar sem
    pôster do que colar o pôster de outro filme numa página publicada
    (mesmo princípio da guarda de ano divergente da v1.7.0)."""
    ef = _ef()
    resposta = dict(NOVA_FICHA, titulo="Outro Filme Completamente",
                    ano=2026, diretor="Outra Pessoa")
    monkeypatch.setattr(ef, "buscar_ficha", lambda *a, **kw: (resposta, None, None))

    antes = (sandbox / f"{SLUG}.json").read_text(encoding="utf-8")
    r = ef.enriquecer_um(SLUG, cache_dir=sandbox, saida=sandbox)
    assert r["ok"] is False and "identidade_divergente" in r["motivo"]
    assert (sandbox / f"{SLUG}.json").read_text(encoding="utf-8") == antes
