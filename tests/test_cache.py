"""Cache em disco: segunda chamada não toca a rede (SPEC §5.5)."""
import pytest

from conftest import FakeSession, fx

from espectro24.fetcher import FetchError, Fetcher


def test_segunda_chamada_nao_toca_a_rede(tmp_path):
    html = fx("oppenheimer-2023_rated5_page1.html")
    session = FakeSession(html)
    fetcher = Fetcher(cache_dir=tmp_path, delay=0, session=session)

    key = "oppenheimer-2023/pages/rated_5_page_1.html"
    url = "https://letterboxd.com/film/oppenheimer-2023/reviews/rated/5/by/activity/page/1/"

    # 1ª chamada: rede
    out1 = fetcher.get(url, key)
    assert session.n_calls == 1
    assert fetcher.n_network == 1
    assert fetcher.origins[key] == "network"

    # 2ª chamada (mesma chave): cache, session NÃO é chamada de novo
    out2 = fetcher.get(url, key)
    assert session.n_calls == 1          # continua 1
    assert fetcher.n_cache == 1
    assert fetcher.origins[key] == "cache"
    assert out1 == out2


def test_offline_sem_cache_levanta(tmp_path):
    fetcher = Fetcher(cache_dir=tmp_path, delay=0, offline=True)
    with pytest.raises(FetchError):
        fetcher.get("https://x", "missing/key.html")


def test_403_levanta_antibot(tmp_path):
    from espectro24.fetcher import AntiBotError
    session = FakeSession("blocked", status=403)
    fetcher = Fetcher(cache_dir=tmp_path, delay=0, session=session)
    with pytest.raises(AntiBotError):
        fetcher.get("https://x", "k.html")
