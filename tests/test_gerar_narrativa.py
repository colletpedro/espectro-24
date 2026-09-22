"""[2026-09-22, §D2] O ESCOPO de `scripts/gerar_narrativa.py`, travado por
teste — mesmo desenho de `tests/test_gerar_veredito.py` (§3[V]), mesma lição:
harness novo com "cuidado diferente" é como se abre o próximo footgun.

Três travas:
  1. nenhum estágio a montante é chamado (coleta, seleção, síntese, [D3]/eixos);
  2. nenhuma chamada de rede sai fora do adaptador de LLM;
  3. rodar altera APENAS `narrativa`, `verificacao_narrativa` e
     `narrativa_selecao` — diff campo a campo do resto.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

SLUG = "the-godfather"


def _gn():
    import gerar_narrativa
    return gerar_narrativa


@pytest.fixture
def documento():
    caminho = RAIZ / "resultado" / f"{SLUG}.json"
    if not caminho.exists():
        pytest.skip(f"{SLUG} não publicado neste checkout")
    d = json.loads(caminho.read_text(encoding="utf-8"))
    if not d.get("narrativa"):
        pytest.skip(f"{SLUG} sem narrativa publicada neste checkout")
    return d


@pytest.fixture
def sandbox(tmp_path, documento, monkeypatch):
    """Um `resultado/` de mentira com UM filme real dentro, para o harness
    escrever sem tocar no repositório."""
    gn = _gn()
    (tmp_path / f"{SLUG}.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(gn, "RESULTADO_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sem_llm(monkeypatch):
    """Substitui a geração por um texto fixo e determinístico — o harness
    roda inteiro (briefing, seleção, verificação), sem rede."""
    import espectro24.narrador as N

    texto = ("Quem não recomenda aponta o ritmo lento; quem recomenda "
             "destaca a mesma duração como parte da experiência.")

    def falso(system, user):
        return (texto, {"prompt_tokens": 1, "completion_tokens": 1,
                        "cache_hit_tokens": 0, "cache_miss_tokens": 1}, 0.0)

    original = N.narrar

    def narrar(output, **kw):
        kw.pop("gerar", None)
        return original(output, gerar=falso, **kw)

    monkeypatch.setattr(_gn(), "narrar", narrar)
    return texto


# ===========================================================================
# (1) Nenhum estágio a montante
# ===========================================================================

def _explode(humano):
    def falha(*a, **kw):
        pytest.fail(f"o harness de narrativa chamou {humano} — ele não pode "
                    f"rodar nenhum estágio a montante")
    return falha


def test_nao_chama_NENHUM_estagio_a_montante(sandbox, sem_llm, monkeypatch):
    """Cada ponto de entrada de coleta, seleção, síntese e [D3]/eixos vira um
    `pytest.fail`; se o harness tocar em qualquer um deles, o teste diz QUAL."""
    from espectro24 import eixos, pipeline, rotulagem, selecao, synthesize

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
    ]
    for modulo, nome, humano in proibidos:
        if not hasattr(modulo, nome):
            continue
        monkeypatch.setattr(modulo, nome, _explode(humano))

    r = _gn().gerar_um(SLUG, saida=sandbox)
    assert r["ok"] is True


def test_nao_importa_o_coletor_nem_o_fetcher_nem_o_pipeline(sandbox, sem_llm):
    """Complemento estrutural: `narrador.py` e `briefing.py` não podem
    depender de coleta nem de rede HTTP."""
    for modulo_nome in ("narrador", "briefing"):
        fonte = (RAIZ / "src" / "espectro24" / f"{modulo_nome}.py").read_text(
            encoding="utf-8")
        for proibido in ("from .collector", "from .fetcher", "from .pipeline",
                         "from .selecao", "from .ficha", "import requests"):
            assert proibido not in fonte, f"{modulo_nome}.py importa {proibido!r}"


# ===========================================================================
# (2) Nenhuma rede fora do adaptador de LLM
# ===========================================================================

def test_nenhuma_chamada_de_rede_fora_do_adaptador(sandbox, sem_llm,
                                                    monkeypatch):
    """Envenena o transporte HTTP inteiro. Com a geração substituída, um
    harness correto não toca a rede em NENHUM ponto — nem TMDB, nem
    histograma, nem Letterboxd."""
    import socket

    import requests

    def proibido(*a, **kw):
        pytest.fail("o harness de narrativa fez chamada de rede")

    monkeypatch.setattr(requests, "get", proibido, raising=False)
    monkeypatch.setattr(requests, "post", proibido, raising=False)
    monkeypatch.setattr(requests.Session, "request", proibido, raising=False)
    monkeypatch.setattr(socket.socket, "connect", proibido, raising=False)

    assert _gn().gerar_um(SLUG, saida=sandbox)["ok"] is True


# ===========================================================================
# (3) Só as três chaves de narrativa mudam
# ===========================================================================

def test_so_as_chaves_de_narrativa_mudam_no_json(sandbox, documento, sem_llm):
    """Diff CAMPO A CAMPO do documento inteiro. Todo campo fora de
    `narrativa`/`verificacao_narrativa`/`narrativa_selecao` tem de sair
    idêntico — mesma estrutura, mesmos valores."""
    from gerar_narrativa import CHAVES

    _gn().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    for chave in CHAVES:
        assert chave in depois
    for chave in set(documento) | set(depois):
        if chave in CHAVES:
            continue
        assert json.dumps(depois.get(chave), ensure_ascii=False, sort_keys=True) \
            == json.dumps(documento.get(chave), ensure_ascii=False, sort_keys=True), \
            f"o campo {chave!r} mudou"


def test_a_narrativa_escrita_e_a_do_texto_fixo_injetado(sandbox, sem_llm):
    _gn().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert depois["narrativa"] == sem_llm


def test_a_ordem_das_chaves_de_topo_e_preservada(sandbox, documento, sem_llm):
    antes = list(documento)
    _gn().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert list(depois) == antes


def test_campo_fora_das_chaves_mudado_a_montante_aborta_sem_gravar(
        sandbox, documento, sem_llm, monkeypatch):
    """Se algo a montante (por engano futuro) mudasse outro campo, o harness
    tem de RECUSAR gravar — mesma trava de `gerar_veredito.aplicar`."""
    gn = _gn()
    original = gn.narrar

    def corrompe(output, **kw):
        output["veredito"] = {"texto": "mutação indevida"}
        return original(output, **kw)

    monkeypatch.setattr(gn, "narrar", corrompe)
    with pytest.raises(SystemExit, match="ABORTADO"):
        gn.gerar_um(SLUG, saida=sandbox)
    # nada foi gravado no sandbox além da cópia original
    disco = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert disco == documento
