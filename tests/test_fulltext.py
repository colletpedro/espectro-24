"""Completamento de truncadas — regra "nunca pela metade" (SPEC §C')."""
from conftest import FakeFetcher

from espectro24.fulltext import complete_review, complete_truncated
from espectro24.models import Review
from espectro24.urls import full_text_cache_key


def _trunc(vid="viewing:5", ftu="/s/full-text/viewing:5/"):
    return Review(viewing_id=vid, rating=4.0, text="visível truncado…",
                  truncated=True, full_text_url=ftu, spoiler=False)


def test_truncada_completada_com_sucesso():
    r = _trunc()
    key = full_text_cache_key("slug", "viewing:5")
    ff = FakeFetcher({key: "<p>texto completo bem maior do que o visível</p>"})
    assert complete_review(ff, "slug", r) is True
    assert r.full_text == "texto completo bem maior do que o visível"
    assert r.effective_text == r.full_text


def test_completa_revela_spoiler_descarta():
    r = _trunc()
    key = full_text_cache_key("slug", "viewing:5")
    ff = FakeFetcher({key: "<p>This review may contain spoilers. I can handle the truth.</p>"})
    assert complete_review(ff, "slug", r) is False   # descartada
    assert r.spoiler is True


def test_nao_truncada_nao_busca():
    r = Review(viewing_id="v", rating=4.0, text="completo visível",
               truncated=False, full_text_url=None, spoiler=False)
    ff = FakeFetcher({})
    assert complete_review(ff, "slug", r) is True
    assert r.full_text == "completo visível"
    assert ff.calls == []                             # nenhuma requisição


def test_truncada_sem_url_descarta():
    r = _trunc(ftu=None)
    ff = FakeFetcher({})
    assert complete_review(ff, "slug", r) is False
    assert ff.calls == []


def test_falha_persistente_uma_retentativa_e_descarta():
    r = _trunc()
    key = full_text_cache_key("slug", "viewing:5")
    ff = FakeFetcher(raise_on={key})
    assert complete_review(ff, "slug", r) is False    # falhou 2x → descarta
    assert sum(1 for _, k in ff.calls if k == key) == 2  # tentativa + retentativa


def test_complete_truncated_conta_descartes():
    ok = _trunc(vid="viewing:1", ftu="/s/full-text/viewing:1/")
    bad = _trunc(vid="viewing:2", ftu="/s/full-text/viewing:2/")
    ff = FakeFetcher(
        {full_text_cache_key("slug", "viewing:1"): "<p>texto completo ok</p>"},
        raise_on={full_text_cache_key("slug", "viewing:2")},
    )
    mantidas, n_desc = complete_truncated(ff, "slug", [ok, bad])
    assert len(mantidas) == 1 and n_desc == 1
    assert all(r.full_text is not None for r in mantidas)  # nunca pela metade
