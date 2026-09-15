"""[2026-09-14] `scripts/republicar_eixos.py` — republica SÓ o bloco `eixos`
de um filme já publicado, com zero LLM, e RECUSA quando o estado publicado
muda.

Mesma técnica de `test_gerar_veredito.py`/`test_publicar_condicoes.py`:
envenenar os pontos de entrada de LLM e de rede com `pytest.fail` e rodar de
verdade, sobre um filme publicado real (cópia em diretório temporário).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import republicar_eixos as R  # noqa: E402

# Publicado, classificado, fora da retentativa: nada nele pode mudar.
CONTROLE = "burning-2018"


@pytest.fixture(autouse=True)
def _sem_llm_e_sem_rede(monkeypatch):
    from espectro24 import condicoes, fetcher, narrador, rotulagem, veredito
    from espectro24 import synthesize as S

    def falha(*a, **kw):
        pytest.fail("republicar_eixos alcançou um estágio que não pode rodar")

    for alvo, nome in ((S, "deepseek_resposta"), (S, "_gemini_resposta"),
                       (S, "resposta"), (S, "synthesize_bucket"),
                       (rotulagem, "rotular_output"), (narrador, "narrar"),
                       (veredito, "gerar"), (condicoes, "gerar"),
                       (fetcher.Fetcher, "get")):
        monkeypatch.setattr(alvo, nome, falha)


def _requer(slug: str) -> None:
    if not ((RAIZ / "resultado" / f"{slug}.json").exists()
            and (RAIZ / "dados" / "bruto" / slug / "meta.json").exists()):
        pytest.skip(f"{slug}: resultado ou bruto indisponível")


def _copia(tmp_path, monkeypatch, slug=CONTROLE) -> Path:
    _requer(slug)
    shutil.copy(RAIZ / "resultado" / f"{slug}.json", tmp_path / f"{slug}.json")
    monkeypatch.setattr(R, "RESULTADO_DIR", tmp_path)
    return tmp_path / f"{slug}.json"


def _adulterar(arq: Path, fn) -> dict:
    d = json.loads(arq.read_text(encoding="utf-8"))
    fn(d["eixos"])
    arq.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def test_reconstrucao_reproduz_o_bloco_publicado():
    """A ferramenta não introduz diff próprio: frases relidas do publicado,
    carimbos iguais aos de `pipeline.montar_eixos`."""
    _requer(CONTROLE)
    m = R.medir(CONTROLE)
    assert m["bloco_identico"] is True
    assert m["estado_publicado_mudou"] is False
    assert (m["celulas_cruzando_margem"], m["bullets"], m["mencoes"],
            m["briefings_que_mudam"]) == ([], [], [], [])


def test_aplicar_escreve_so_o_bloco_eixos(tmp_path, monkeypatch):
    arq = _copia(tmp_path, monkeypatch)
    antes = json.loads(arq.read_text(encoding="utf-8"))
    m = R.medir(CONTROLE)
    R.aplicar(CONTROLE, m)
    depois = json.loads(arq.read_text(encoding="utf-8"))
    assert ({k: v for k, v in depois.items() if k != "eixos"}
            == {k: v for k, v in antes.items() if k != "eixos"})
    assert depois["eixos"] == m["bloco_novo"]


@pytest.mark.parametrize("fim", ["\n", ""], ids=["com-newline", "sem-newline"])
def test_republicar_bloco_identico_nao_muda_um_byte(tmp_path, monkeypatch, fim):
    """Filme sem nada a mudar sai byte a byte igual — inclusive o fim de
    arquivo, que varia entre os harnesses que publicaram cada JSON."""
    arq = _copia(tmp_path, monkeypatch)
    doc = json.loads(arq.read_text(encoding="utf-8"))
    original = json.dumps(doc, ensure_ascii=False, indent=2) + fim
    arq.write_text(original, encoding="utf-8")
    R.aplicar(CONTROLE, R.medir(CONTROLE))
    assert arq.read_text(encoding="utf-8") == original


def _outro_contraste(e):
    e["contraste"] = "tematico" if e.get("contraste") != "tematico" else "valorativo"


def _outro_bullet(e):
    linha = e["linhas"][0]
    bucket = next(iter(linha["bullet_de"]))
    linha["bullet_de"][bucket] = None if linha["bullet_de"][bucket] else "frequencia"


def _outra_margem(e):
    cel = next(iter(e["linhas"][0]["por_bucket"].values()))
    cel["acima_da_margem"] = not cel["acima_da_margem"]


@pytest.mark.parametrize("adulterar, campo", [
    (_outro_contraste, "contraste"),
    (_outro_bullet, "bullets"),
    (_outra_margem, "celulas_cruzando_margem"),
], ids=["contraste", "bullet", "margem"])
def test_recusa_quando_o_estado_publicado_muda(tmp_path, monkeypatch,
                                               adulterar, campo):
    """O publicado (adulterado) diverge do recalculado num campo de ESTADO:
    a medição acusa, e `aplicar` recusa sem gravar nada."""
    arq = _copia(tmp_path, monkeypatch)
    publicado = _adulterar(arq, adulterar)
    m = R.medir(CONTROLE)
    assert m["estado_publicado_mudou"] is True
    assert m[campo] and m[campo] != [None, None]
    with pytest.raises(SystemExit, match="RECUSADO"):
        R.aplicar(CONTROLE, m)
    assert json.loads(arq.read_text(encoding="utf-8")) == publicado


def test_carimbo_global_nao_se_move_sem_mudanca_de_contagem(tmp_path, monkeypatch):
    """`n_removidas_no_corpus` é global: uma remoção em OUTRO filme o move.
    Num filme cujas contagens não mudaram, a republicação mantém o carimbo
    publicado — senão todo filme tocado ganharia um diff sem conteúdo."""
    arq = _copia(tmp_path, monkeypatch)
    publicado = _adulterar(
        arq, lambda e: e["verificador"].__setitem__("n_removidas_no_corpus", 1))
    m = R.medir(CONTROLE)
    assert m["mencoes"] == [] and m["bloco_identico"] is True
    assert m["bloco_novo"]["verificador"] == publicado["eixos"]["verificador"]


def test_carimbo_global_acompanha_o_corpus_quando_a_contagem_muda(tmp_path, monkeypatch):
    """Quando a contagem do PRÓPRIO filme muda, o carimbo é o do corpus
    atual — é a execução do verificador que produziu os números novos."""
    import contextlib

    from espectro24 import eixos as E
    from espectro24 import pipeline as P

    arq = _copia(tmp_path, monkeypatch)

    def outra_contagem(e):
        cel = next(iter(e["linhas"][0]["por_bucket"].values()))
        cel["mencoes"] += 1
        e["verificador"]["n_removidas_no_corpus"] = 1

    _adulterar(arq, outra_contagem)
    m = R.medir(CONTROLE)
    assert m["mencoes"]
    with contextlib.chdir(R.RAIZ):
        _, meta = P._carregar_consenso_producao(E)
    assert m["bloco_novo"]["verificador"] == meta


def test_aceitar_mudanca_so_com_a_flag_explicita(tmp_path, monkeypatch):
    arq = _copia(tmp_path, monkeypatch)
    _adulterar(arq, _outro_contraste)
    m = R.medir(CONTROLE)
    R.aplicar(CONTROLE, m, aceitar_mudanca=True)
    assert json.loads(arq.read_text(encoding="utf-8"))["eixos"] == m["bloco_novo"]
