"""[v1.9.37] O ESCOPO do harness de PUBLICAÇÃO das condições, travado por teste.

Este é o harness que **escreve em `resultado/`** — o único do arco de
condições que faz isso. A versão de estudo (`gerar_condicoes.py`) recusava
`--saida` dentro de `resultado/`; aqui a trava **muda de lugar, não
desaparece**: passa a ser o CONTEÚDO.

Quatro travas:
  1. nenhum estágio a montante é alcançado (envenenamento + `assert hasattr`
     antes, para o trap não ficar vazio — lição da v1.9.25);
  2. rodar altera APENAS a chave `condicoes` — diff campo a campo;
  3. o harness RECUSA publicar condição que não passe em `validar()`;
  4. as seis condições retiradas do eixo `expectativa` não são publicadas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import condicoes as C  # noqa: E402

SLUG = "the-godfather"


def _pc():
    import publicar_condicoes
    return publicar_condicoes


@pytest.fixture
def documento():
    caminho = RAIZ / "resultado" / f"{SLUG}.json"
    if not caminho.exists():
        pytest.skip(f"{SLUG} não publicado neste checkout")
    return json.loads(caminho.read_text(encoding="utf-8"))


@pytest.fixture
def origem(tmp_path, documento):
    """Um bloco `condicoes` válido, gerado pelo próprio código, sem LLM."""
    pc = _pc()
    idx = C.indexar(documento)
    sel = C.selecionar(idx)
    bloco = {
        "vale_a_pena": [], "talvez_evite": [],
        "ordem_colunas": C.ordem_das_colunas(idx),
        "peso": {l: C.peso_do_lado(idx, l) for l in C.LADOS},
        "peso_meio": C.peso_do_meio(idx),
        "origem": "llm",
    }
    # textos reais do que foi ao ar, incluindo UMA das seis retiradas
    textos = {
        "POS-A": "aprecia interpretações expressivas e complexas que conduzem "
                 "a transformação dos personagens",
        "NEG-A": "se cansa com narrativas de longa duração e ritmo arrastado",
        "NEG-B": "acha que o filme não merece tanto elogio quanto recebe",
    }
    for lado in C.LADOS:
        for t in sel[lado]:
            if t["id"] not in textos:
                continue
            bloco[lado].append({
                "texto": textos[t["id"]], "tema_origem": t["id"],
                "bucket_origem": t["bucket"], "tema_texto": t["tema"],
                "rotulo_forca": t["rotulo_forca"],
            })
    d = tmp_path / f"{SLUG}.json"
    d.write_text(json.dumps({"slug": SLUG, "condicoes": bloco},
                            ensure_ascii=False), encoding="utf-8")
    return tmp_path


@pytest.fixture
def sandbox(tmp_path, documento, monkeypatch):
    """Um `resultado/` de mentira, para o harness escrever sem tocar no repo."""
    dir_ = tmp_path / "resultado"
    dir_.mkdir()
    (dir_ / f"{SLUG}.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(_pc(), "RESULTADO_DIR", dir_)
    return dir_


# ===========================================================================
# (1) Nenhum estágio a montante
# ===========================================================================

def _explode(humano):
    def falha(*a, **kw):
        pytest.fail(f"o harness de publicação chamou {humano} — ele não pode "
                    f"rodar nenhum estágio a montante")
    return falha


def test_nao_chama_NENHUM_estagio_a_montante(sandbox, origem, monkeypatch):
    """A trava principal. Cada ponto de entrada vira `pytest.fail`; se o
    harness tocar em qualquer um deles, o teste diz QUAL.

    **`assert hasattr` ANTES de envenenar** — é a lição da v1.9.25: um trap
    montado sobre um atributo que não existe mais não protege nada e fica
    verde para sempre.
    """
    from espectro24 import (eixos, narrador, pipeline, rotulagem, selecao,
                            synthesize, veredito)

    proibidos = [
        (pipeline, "collect_all_levels", "coleta"),
        (pipeline, "run_pipeline", "pipeline completo"),
        (pipeline, "montar_eixos", "[D3]/eixos"),
        (pipeline, "montar_buckets", "montagem de buckets"),
        (selecao, "selecionar", "seleção downstream"),
        (synthesize, "synthesize_bucket", "síntese [D]"),
        (synthesize, "resposta", "qualquer chamada de LLM"),
        (synthesize, "cliente", "construção de cliente de LLM"),
        (eixos, "montar_bloco", "bloco de eixos"),
        (eixos, "carregar_classificacao", "leitura da classificação"),
        (rotulagem, "rotular_output", "[D3] rotulagem"),
        (narrador, "narrar", "narrativa [D2]"),
        (veredito, "gerar", "veredito [V]"),
        (C, "gerar", "geração de condições (o harness só PUBLICA)"),
    ]
    for modulo, nome, humano in proibidos:
        assert hasattr(modulo, nome), (
            f"{modulo.__name__}.{nome} não existe mais — este trap ficaria "
            f"VAZIO e verde para sempre. Atualize a lista, não a remova.")
        monkeypatch.setattr(modulo, nome, _explode(humano))

    r = _pc().publicar_um(SLUG, origem, dry_run=False)
    assert r["n"] >= 1


# ===========================================================================
# (2) Só a chave `condicoes` muda
# ===========================================================================

def test_publicar_altera_APENAS_a_chave_condicoes(sandbox, origem, documento):
    _pc().publicar_um(SLUG, origem, dry_run=False)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    assert "condicoes" in depois
    assert set(depois) == set(documento) | {"condicoes"}
    # ordem das chaves de topo preservada, com `condicoes` acrescentada no fim
    assert list(depois)[:-1] == list(documento)
    for chave in documento:
        assert depois[chave] == documento[chave], (
            f"o harness alterou a chave {chave!r} — ele só pode escrever "
            f"`condicoes`")


def test_dry_run_nao_escreve_nada(sandbox, origem, documento):
    _pc().publicar_um(SLUG, origem, dry_run=True)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert depois == documento


# ===========================================================================
# (3) A trava de CONTEÚDO — substitui a recusa de `--saida` do harness de estudo
# ===========================================================================

def test_recusa_publicar_condicao_invalida(sandbox, origem, tmp_path,
                                           documento):
    """A trava mudou de lugar: o harness de estudo recusava o DESTINO, este
    recusa o CONTEÚDO. Uma condição com algarismo (proibido em qualquer lugar
    do produto) reprova o FILME inteiro."""
    ruim = json.loads((origem / f"{SLUG}.json").read_text(encoding="utf-8"))
    ruim["condicoes"]["talvez_evite"][0]["texto"] = "se cansa com 3 horas de filme"
    (origem / f"{SLUG}.json").write_text(json.dumps(ruim, ensure_ascii=False),
                                         encoding="utf-8")

    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(SLUG, origem, dry_run=False)
    assert "digito" in str(e.value)

    # e NADA foi escrito
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert depois == documento


def test_recusa_bloco_vazio(sandbox, origem, documento):
    vazio = json.loads((origem / f"{SLUG}.json").read_text(encoding="utf-8"))
    vazio["condicoes"]["vale_a_pena"] = []
    vazio["condicoes"]["talvez_evite"] = []
    (origem / f"{SLUG}.json").write_text(json.dumps(vazio, ensure_ascii=False),
                                         encoding="utf-8")
    with pytest.raises(_pc().CondicaoInvalida):
        _pc().publicar_um(SLUG, origem, dry_run=False)


# ===========================================================================
# (4) As seis retiradas do eixo `expectativa`
# ===========================================================================

def test_as_seis_retiradas_nao_sao_publicadas(sandbox, origem):
    """`the-godfather` NEG-B (*Filme superestimado*) está na origem e NÃO pode
    sair do outro lado. §0, pendência editorial nomeada."""
    antes = json.loads((origem / f"{SLUG}.json").read_text(encoding="utf-8"))
    ids_antes = {c["tema_origem"] for l in C.LADOS for c in antes["condicoes"][l]}
    assert "NEG-B" in ids_antes, "a fixture precisa conter a condição retirada"

    _pc().publicar_um(SLUG, origem, dry_run=False)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    ids = {c["tema_origem"] for l in C.LADOS for c in depois["condicoes"][l]}
    assert "NEG-B" not in ids


def test_a_lista_de_retiradas_e_literal_e_completa():
    """São seis, nomeadas. Se alguém derivar isto do eixo, o conjunto passa a
    mudar sozinho quando o catálogo mudar — e é decisão editorial sobre seis
    frases, não uma regra."""
    assert _pc().RETIRADAS == {
        ("the-godfather", "NEG-B"),
        ("hereditary", "NEG-B"),
        ("interstellar", "NEG-B"),
        ("longlegs", "NEG-B"),
        ("parasite-2019", "NEG-C"),
        ("everything-everywhere-all-at-once", "NEG-F"),
    }
