"""[§3[B'], v1.9.12] O ANO do filme persiste no bruto — Entrega 1.

Defeito medido em `joker-folie-a-deux` (v1.9.11): slug sem sufixo de ano +
`--offline` ⇒ o fallback da v1.7.0 (que resolve o ano buscando a página do
Letterboxd) precisa de REDE e não roda ⇒ a guarda da v1.7.0 recusa buscar a
ficha sem ano ⇒ `ORCAMENTO_SEM_FICHA` põe o movimento 1 em (0,0) ⇒ a
narrativa nunca diz que filme é, em silêncio.

21 dos 35 slugs do catálogo não têm ano no nome.

O ano é dado ESTÁVEL e já foi buscado uma vez — pela mesma lógica do
histograma, o superset (§3[B']) deveria estar guardando desde a v1.9.0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import ficha as F  # noqa: E402


class _FetcherFake:
    """Devolve a página do filme (com o ano) e conta requisições."""

    def __init__(self, html: str = '<a href="/films/year/1997/">1997</a>',
                 falha: bool = False):
        self.html, self.falha, self.n = html, falha, 0

    def get(self, url, cache_key):
        self.n += 1
        if self.falha:
            from espectro24.fetcher import FetchError
            raise FetchError("offline e sem cache")
        return self.html


# ------------------------------------------------------- precedência

def test_argumento_explicito_vence_tudo():
    f = _FetcherFake()
    ano, fonte = F.resolver_ano(f, "cure", ano_explicito=1997,
                                meta_bruto={"ano_lancamento": 2020})
    assert (ano, fonte) == (1997, "argumento")
    assert f.n == 0, "não toca a rede quando já sabe"


def test_bruto_vence_slug_e_rede():
    """O ponto da entrega: o ano gravado na coleta é lido ANTES de tentar
    rede — é isso que faz a execução offline ter ficha."""
    f = _FetcherFake()
    ano, fonte = F.resolver_ano(f, "cure",
                                meta_bruto={"ano_lancamento": 1997,
                                            "ano_fonte": "letterboxd"})
    assert (ano, fonte) == (1997, "bruto")
    assert f.n == 0


def test_sem_bruto_cai_para_o_slug():
    f = _FetcherFake()
    ano, fonte = F.resolver_ano(f, "the-invite-2026", meta_bruto={})
    assert (ano, fonte) == (2026, "slug")
    assert f.n == 0


def test_sem_bruto_nem_slug_cai_para_a_rede():
    f = _FetcherFake()
    ano, fonte = F.resolver_ano(f, "cure", meta_bruto=None)
    assert (ano, fonte) == (1997, "letterboxd")
    assert f.n == 1


def test_offline_sem_bruto_devolve_None_sem_estourar():
    """O caso que produziu o defeito — continua degradando, mas agora só
    quando o bruto REALMENTE não tem o ano."""
    f = _FetcherFake(falha=True)
    ano, fonte = F.resolver_ano(f, "joker-folie-a-deux", meta_bruto={})
    assert ano is None and fonte is None


def test_meta_sem_a_chave_nao_quebra():
    """Bruto coletado ANTES desta versão não tem `ano_lancamento` — tem de
    degradar para o comportamento antigo, não estourar."""
    f = _FetcherFake()
    ano, fonte = F.resolver_ano(f, "cure", meta_bruto={"slug": "cure"})
    assert (ano, fonte) == (1997, "letterboxd")


def test_ano_zero_ou_invalido_no_bruto_e_ignorado():
    f = _FetcherFake()
    for ruim in (0, None, "", "mil"):
        ano, fonte = F.resolver_ano(f, "the-invite-2026",
                                    meta_bruto={"ano_lancamento": ruim})
        assert (ano, fonte) == (2026, "slug"), ruim


def test_fetcher_ausente_nao_impede_bruto_nem_slug():
    """Caminhos que não têm fetcher (ex. re-render puro) continuam podendo
    resolver o ano — a rede é o ÚLTIMO recurso, não um pré-requisito."""
    assert F.resolver_ano(None, "cure",
                          meta_bruto={"ano_lancamento": 1997}) == (1997, "bruto")
    assert F.resolver_ano(None, "the-invite-2026") == (2026, "slug")
    assert F.resolver_ano(None, "cure") == (None, None)


# ------------------------------------------------------- gravação no meta

def test_coleta_grava_ano_e_fonte_no_meta():
    from espectro24.ficha import meta_com_ano
    f = _FetcherFake()
    meta = meta_com_ano({"slug": "cure"}, f, "cure")
    assert meta["ano_lancamento"] == 1997
    assert meta["ano_fonte"] == "letterboxd"


def test_meta_com_ano_nao_rebusca_o_que_ja_esta_gravado():
    """Idempotente: recoletar um filme não gasta requisição de ano de novo."""
    from espectro24.ficha import meta_com_ano
    f = _FetcherFake()
    meta = meta_com_ano({"slug": "cure", "ano_lancamento": 1997,
                         "ano_fonte": "letterboxd"}, f, "cure")
    assert meta["ano_lancamento"] == 1997
    assert f.n == 0


def test_meta_com_ano_nao_grava_chave_quando_nao_resolve():
    """Sem ano, o campo NÃO entra — um `ano_lancamento: null` no meta seria
    lido como "já tentei e não tem", e a próxima execução com rede não
    tentaria de novo."""
    from espectro24.ficha import meta_com_ano
    f = _FetcherFake(falha=True)
    meta = meta_com_ano({"slug": "joker-folie-a-deux"}, f, "joker-folie-a-deux")
    assert "ano_lancamento" not in meta
