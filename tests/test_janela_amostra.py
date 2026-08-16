"""[v1.9.14, Entrega 6] A janela temporal DA AMOSTRA ANALISADA.

**O defeito que isto fecha.** A amostra de reviews cobre uma janela estreita
(mediana ~26 dias no catálogo) enquanto o histograma de notas acumula desde
2012, e as duas frases apareciam no mesmo parágrafo como se descrevessem as
mesmas pessoas. É a mesma classe de defeito que a spec já protege entre
NOTAS e REVIEWS COM TEXTO (§D2, invariante de vocabulário).

**A armadilha que quase reintroduz o defeito.** `coleta.janela_temporal` já
existia — mas é calculada sobre o BRUTO (678 reviews em `cure`), não sobre as
40 analisadas. Exibi-la ao lado de "40 de 40 analisadas" trocaria uma
confusão de populações por outra. Daí `janela_amostra`, por bucket, sobre as
reviews que a síntese de fato leu.

**Mediana, nunca média/extremos.** Em `data` (data ASSISTIDA, campo livre de
diário) os extremos são contaminados — há review datada de 1442 no catálogo,
e em `cure` a janela `min`-`max` é ~16× a `p5`-`p95`. A janela publicada sai
dos quantis robustos; `min`/`max` ficam no dado, fora da tela.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import ReviewBruta, janela_temporal  # noqa: E402


def _r(data, nivel=2.0, id_="v1"):
    return ReviewBruta(id=id_, nivel=nivel, texto="x" * 200, n_chars=200,
                       spoiler_flag=False, pagina_origem=1, url="", 
                       autor_hash="", truncada=False, texto_completo=True,
                       data=data)


def test_janela_da_amostra_ignora_o_bruto_e_ve_so_o_que_foi_analisado():
    """A função é pura: quem decide a população é quem chama. O teste trava
    a expectativa de que a população certa é a SELECIONADA."""
    analisadas = [_r("2026-07-01"), _r("2026-07-15"), _r("2026-08-01")]
    resto_do_bruto = [_r("2012-01-01"), _r("2003-05-05")]
    j = janela_temporal(analisadas)
    assert j["n"] == 3
    assert j["min"] >= "2026-07-01"
    assert janela_temporal(analisadas + resto_do_bruto)["n"] == 5


def test_um_outlier_de_diario_domina_os_extremos_e_nao_os_quantis():
    """`data` é a data ASSISTIDA. Uma pessoa que registra o filme com 20 anos
    de atraso move `min` em duas décadas e a `p5` quase nada — é por isso que
    a janela exibida sai dos quantis."""
    datas = [f"2026-08-{d:02d}" for d in range(1, 21)] + ["2003-04-01"]
    j = janela_temporal([_r(d) for d in datas])
    assert j["min"] == "2003-04-01"
    assert j["p5"] >= "2026-08-01"
    assert j["p50"] >= "2026-08-01"


def test_sem_data_nenhuma_devolve_None_em_vez_de_janela_inventada():
    assert janela_temporal([_r(None), _r(None)]) is None
