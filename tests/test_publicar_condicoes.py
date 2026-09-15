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
    """**A fixture lê o `resultado/` real, que DEPOIS da publicação já tem o
    bloco.** Comparar contra a lista crua faria o teste passar antes de
    publicar e falhar depois, por motivo nenhum — a mesma armadilha que o
    teste equivalente do veredito já documenta."""
    antes = list(documento)
    _pc().publicar_um(SLUG, origem, dry_run=False)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    assert "condicoes" in depois
    assert set(depois) == set(documento) | {"condicoes"}
    if "condicoes" in documento:
        assert list(depois) == antes          # já publicado: ordem idêntica
    else:
        assert list(depois)[:-1] == antes     # entra no fim
        assert list(depois)[-1] == "condicoes"
    for chave in documento:
        if chave == "condicoes":
            continue                          # é a única que o harness escreve
        assert depois[chave] == documento[chave], (
            f"o harness alterou a chave {chave!r} — ele só pode escrever "
            f"`condicoes`")


@pytest.mark.parametrize("fim", ["", "\n"])
def test_preserva_o_fim_de_arquivo_do_original(sandbox, origem, fim):
    """O JSON republicado pelo CLI não tem `\\n` final; o de condições tinha.
    Trocar o fim de linha é diff sem conteúdo (mesma regra de
    `republicar_eixos`) — apareceu ao retirar os dois `expectativa` no ar."""
    alvo = sandbox / f"{SLUG}.json"
    alvo.write_text(alvo.read_text(encoding="utf-8").rstrip("\n") + fim,
                    encoding="utf-8")
    _pc().publicar_um(SLUG, origem, dry_run=False)
    texto = alvo.read_text(encoding="utf-8")
    assert texto.endswith("}" + fim) and not texto.endswith("}\n" + fim)


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


# As oito da antiga lista literal (seis da FASE 1 + C030 e C134 do piloto).
# A lista saiu do código em 2026-09-15 (C14.16); fica aqui como gabarito.
OITO_DA_LISTA = {
    ("the-godfather", "NEG-B"),
    ("hereditary", "NEG-B"),
    ("interstellar", "NEG-B"),
    ("longlegs", "NEG-B"),
    ("parasite-2019", "NEG-C"),
    ("everything-everywhere-all-at-once", "NEG-F"),
    ("get-out-2017", "NEG-C"),
    ("whiplash-2014", "NEG-F"),
}


def _temas_retidos_no_catalogo():
    """`(slug, tema)` de todo tema de condição PEDIDO no catálogo que a regra
    retém — `get-out-2017` pelo lote corrigido, o único sem bloco publicado."""
    import votacao_3 as v3
    slugs = {json.loads(l)["slug"] for l in
             v3.ARQ_CONSENSO.read_text(encoding="utf-8").splitlines() if l.strip()}
    fora = set()
    for slug in slugs:
        doc = json.loads((RAIZ / "resultado" / f"{slug}.json").read_text(
            encoding="utf-8"))
        bloco = doc.get("condicoes")
        if bloco is None and (CORRIGIDO / f"{slug}.json").exists():
            bloco = _bloco_corrigido(slug)
        if not bloco:
            continue
        idx = C.indexar(doc)
        for lado in C.LADOS:
            for tid in (bloco.get("temas_pedidos") or {}).get(lado) or []:
                t = idx[tid]
                if _pc().EIXO_RETIDO_R13 in C.eixos_do_tema(doc, t["bucket"],
                                                            t["tema"]):
                    fora.add((slug, tid))
    return fora


def test_a_r13_e_REGRA_e_a_lista_literal_nao_existe_mais():
    """Decisão do dono (C14.16): a lista mantida à mão divergia em silêncio
    com o catálogo. Se ela voltar, volta o modo de falha dela."""
    assert not hasattr(_pc(), "RETIRADAS")
    assert _pc().EIXO_RETIDO_R13 == "expectativa"


def test_a_regra_reproduz_as_oito_da_lista_e_so_retem_as_tres_medidas():
    """Validação feita ANTES de a lista sair, travada no dado real: a regra
    retém as oito, e além delas exatamente os três temas que a medição
    achou — dois no ar até 2026-09-15 e um nunca publicado. Um quarto é
    conversa, não surpresa: a classificação mudou por baixo de um filme."""
    if not (RAIZ / "resultado" / "votacao-3" / "consenso.jsonl").exists():
        pytest.skip("catálogo ausente neste checkout")
    retidos = _temas_retidos_no_catalogo()
    assert OITO_DA_LISTA <= retidos
    assert retidos - OITO_DA_LISTA == {
        ("talk-to-me-2022", "NEG-C"),
        ("spider-man-across-the-spider-verse", "POS-E"),
        ("mother-2017", "POS-C"),
    }


def test_o_lote_do_piloto_sai_igual_sob_a_regra(capsys):
    """O dry-run do lote corrigido dava 134 condições e 2 retiradas (C030,
    C134) sob a lista; sob a regra dá o mesmo."""
    if not CORRIGIDO.exists():
        pytest.skip("lote corrigido do piloto ausente neste checkout")
    total = retiradas = 0
    for p in sorted(CORRIGIDO.glob("*.json")):
        r = _pc().publicar_um(p.stem, CORRIGIDO, dry_run=True)
        total += r["n"]
        retiradas += r["retiradas"]
    assert (total, retiradas) == (134, 2)


# Os dois itens que a lista incompleta deixou no ar, com o texto publicado.
NO_AR_ATE_2026_09_15 = {
    "talk-to-me-2022": ("talvez_evite", {
        "texto": "se frustra quando premissas promissoras se perdem em "
                 "subtramas mal exploradas",
        "tema_origem": "NEG-C", "bucket_origem": "negativas",
        "tema_texto": "Subaproveitamento do potencial da premissa",
        "rotulo_forca": "alguns"}),
    "spider-man-across-the-spider-verse": ("vale_a_pena", {
        "texto": "gosta de desfechos em aberto que criam forte expectativa "
                 "para continuações",
        "tema_origem": "POS-E", "bucket_origem": "positivas",
        "tema_texto": "Cliffhanger e expectativa pela continuação",
        "rotulo_forca": "alguns"}),
}


@pytest.mark.parametrize("slug", sorted(NO_AR_ATE_2026_09_15))
def test_os_dois_expectativa_que_estavam_no_ar_nao_publicam(
        tmp_path, monkeypatch, slug):
    """Decisão (a) do dono: se a R13 diz que `expectativa` não publica, eles
    não deveriam estar lá. Com a condição de volta na origem, a regra a tira
    — e nenhuma coluna fica vazia."""
    res = _sandbox_de(tmp_path, monkeypatch, slug)
    doc = json.loads((res / f"{slug}.json").read_text(encoding="utf-8"))
    bloco = json.loads(json.dumps(doc["condicoes"]))
    lado, cond = NO_AR_ATE_2026_09_15[slug]
    if cond["tema_origem"] not in {c["tema_origem"] for c in bloco[lado]}:
        bloco[lado].append(cond)
    r = _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=False)
    assert r["retiradas"] == 1
    pub = json.loads((res / f"{slug}.json").read_text(encoding="utf-8"))
    assert cond["tema_origem"] not in {c["tema_origem"]
                                       for c in pub["condicoes"][lado]}
    assert all(pub["condicoes"][l] for l in C.LADOS)


@pytest.mark.parametrize("slug,tema", [("im-still-here-2024", "POS-E"),
                                       ("mother-2017", "POS-A")])
def test_tema_sem_eixo_BLOQUEIA_o_filme(tmp_path, monkeypatch, slug, tema):
    """Decisão (b) do dono: sem eixo a regra não sabe se é `expectativa`, e
    regra que falha aberta não protege. Os dois casos reais do catálogo."""
    res = _sandbox_de(tmp_path, monkeypatch, slug)
    doc = json.loads((res / f"{slug}.json").read_text(encoding="utf-8"))
    assert tema in {c["tema_origem"] for l in C.LADOS
                    for c in doc["condicoes"][l]}
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(slug, _origem_com(tmp_path, slug, doc["condicoes"]),
                          dry_run=True)
    assert f"[{tema}]" in str(e.value) and "sem eixo" in str(e.value)


def test_tema_sem_eixo_bloqueia_mesmo_sem_nenhum_expectativa(sandbox, origem,
                                                             monkeypatch):
    """A trava não depende de o filme ter tema `expectativa`: basta o bloco
    `eixos` não conhecer o tema de uma condição."""
    monkeypatch.setattr(C, "eixos_do_tema", lambda doc, b, t: [])
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(SLUG, origem, dry_run=True)
    assert "sem eixo" in str(e.value)


# ===========================================================================
# (5) [piloto de expansão] Texto de AUTORIA HUMANA e "sem condição publicável"
# ===========================================================================

CORRIGIDO = (RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"
             / "lote-piloto-18-corrigido")


def _sandbox_de(tmp_path, monkeypatch, slug):
    caminho = RAIZ / "resultado" / f"{slug}.json"
    if not caminho.exists():
        pytest.skip(f"{slug} não publicado neste checkout")
    dir_ = tmp_path / "resultado"
    dir_.mkdir(exist_ok=True)
    (dir_ / f"{slug}.json").write_text(caminho.read_text(encoding="utf-8"),
                                       encoding="utf-8")
    monkeypatch.setattr(_pc(), "RESULTADO_DIR", dir_)
    return dir_


def _origem_com(tmp_path, slug, bloco):
    d = tmp_path / "origem"
    d.mkdir(exist_ok=True)
    (d / f"{slug}.json").write_text(
        json.dumps({"slug": slug, "condicoes": bloco}, ensure_ascii=False),
        encoding="utf-8")
    return d


def _bloco_corrigido(slug):
    p = CORRIGIDO / f"{slug}.json"
    if not p.exists():
        pytest.skip("lote corrigido do piloto ausente neste checkout")
    return json.loads(p.read_text(encoding="utf-8"))["condicoes"]


def test_texto_humano_publica_com_AVISO_e_o_mesmo_texto_sem_origem_nao(
        tmp_path, monkeypatch):
    """C058 (`memories-of-murder` POS-A), texto do dono: "interpretações"
    por "atuações", "figuras" por "personagens" — a abstração que a R12 pede
    e a régua de prefixo reprova. Com a marca de autoria, publica e o aviso
    fica gravado na condição; SEM a marca, a mesma frase é recusada — é a
    trava inteira de sempre."""
    slug = "memories-of-murder"
    res = _sandbox_de(tmp_path, monkeypatch, slug)
    bloco = _bloco_corrigido(slug)
    c058 = next(c for c in bloco["vale_a_pena"] if c["tema_origem"] == "POS-A")
    assert c058["origem"] == "leitura_humana"

    r = _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=False)
    assert r["avisos"] == {"POS-A": ["ancora_nao_verificavel"]}
    pub = json.loads((res / f"{slug}.json").read_text(encoding="utf-8"))
    gravada = next(c for c in pub["condicoes"]["vale_a_pena"]
                   if c["tema_origem"] == "POS-A")
    assert gravada["avisos"] == ["ancora_nao_verificavel"]

    del c058["origem"]
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=True)
    assert "ancora_nao_verificavel" in str(e.value)


@pytest.mark.parametrize("texto,flag", [
    ("aprecia interpretações fortes de 2 figuras complexas", "digito"),
    ('aprecia "interpretações fortes" de figuras complexas', "aspas"),
    ("aprecia interpretações fortes de figuras complexas e de conduta "
     "ambivalente num filme longo e muito escuro", "comprimento"),
    ("aprecia, como a maioria, interpretações fortes de figuras complexas",
     "quantidade_escrita"),
])
def test_texto_humano_continua_sob_os_validadores_EXATOS(
        tmp_path, monkeypatch, texto, flag):
    """A marca de autoria só tira da trava as flags LÉXICAS. Algarismo,
    aspas, comprimento, quantidade — reprovam o texto do dono como
    reprovam o do modelo."""
    slug = "memories-of-murder"
    _sandbox_de(tmp_path, monkeypatch, slug)
    bloco = _bloco_corrigido(slug)
    c = next(c for c in bloco["vale_a_pena"] if c["tema_origem"] == "POS-A")
    c["texto"] = texto
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=True)
    assert flag in str(e.value)


def test_recusa_do_dono_publica_e_recusa_invalida_bloqueia(tmp_path,
                                                          monkeypatch):
    """C051 (`hard-to-be-a-god` POS-C): recusa do dono, R2. Publica como
    `sem_condicao_publicavel`; com regra fora do conjunto fechado, o filme
    inteiro é recusado."""
    slug = "hard-to-be-a-god"
    res = _sandbox_de(tmp_path, monkeypatch, slug)
    bloco = _bloco_corrigido(slug)
    rec = bloco["sem_condicao_publicavel"]
    assert [(r["tema_origem"], r["regra"], r["origem"]) for r in rec] == [
        ("POS-C", "R2", "leitura_humana")]
    assert "POS-C" not in {c["tema_origem"] for c in bloco["vale_a_pena"]}

    _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco), dry_run=False)
    pub = json.loads((res / f"{slug}.json").read_text(encoding="utf-8"))
    assert pub["condicoes"]["sem_condicao_publicavel"][0]["motivo"]

    rec[0]["regra"] = "R9"
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=True)
    assert "recusa_regra_invalida" in str(e.value)


def test_par_recusado_precisa_estar_consolidado(tmp_path, monkeypatch):
    """C024 (`force-majeure-2014` NEG-E) foi FORÇADO por POS-B e o dono o
    recusou: POS-B publica com a marca `par_recusado`. Sem a marca, o
    bloco não está consolidado e o filme é recusado — a regra do par não
    depende de alguém lembrar de aplicá-la."""
    slug = "force-majeure-2014"
    _sandbox_de(tmp_path, monkeypatch, slug)
    bloco = _bloco_corrigido(slug)
    base = next(c for c in bloco["vale_a_pena"] if c["tema_origem"] == "POS-B")
    assert base["par_recusado"] == "NEG-E"
    _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco), dry_run=True)

    del base["par_recusado"]
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(slug, _origem_com(tmp_path, slug, bloco),
                          dry_run=True)
    assert "par não consolidado" in str(e.value)


def test_coluna_vazia_BLOQUEIA_o_filme(sandbox, origem):
    """Coluna vazia é decisão humana: o harness recusa, e o código não
    completa a coluna com outro tema."""
    b = json.loads((origem / f"{SLUG}.json").read_text(encoding="utf-8"))
    b["condicoes"]["vale_a_pena"] = []
    (origem / f"{SLUG}.json").write_text(json.dumps(b, ensure_ascii=False),
                                         encoding="utf-8")
    with pytest.raises(_pc().CondicaoInvalida) as e:
        _pc().publicar_um(SLUG, origem, dry_run=True)
    assert "VAZIA" in str(e.value)


def test_o_motivo_da_recusa_nao_vai_para_a_pagina():
    """O `motivo` fica no JSON de `resultado/` (material de revisão) e sai
    na geração do site — `frontend/build_data.py`, a única ponte entre os
    dois. A regra, o tema e a origem ficam: são proveniência."""
    sys.path.insert(0, str(RAIZ / "frontend"))
    import build_data
    data = {"condicoes": {"sem_condicao_publicavel": [
        {"tema_origem": "POS-C", "lado": "vale_a_pena", "regra": "R2",
         "motivo": "o tema relata dificuldade", "origem": "leitura_humana"}]}}
    build_data.sem_motivo_de_recusa(data)
    assert data["condicoes"]["sem_condicao_publicavel"] == [
        {"tema_origem": "POS-C", "lado": "vale_a_pena", "regra": "R2",
         "origem": "leitura_humana"}]
    assert "motivo" not in json.dumps(data)
    fonte = (RAIZ / "frontend" / "build_data.py").read_text(encoding="utf-8")
    assert "sem_motivo_de_recusa(data)" in fonte.split("def main")[1]
    assert "sem_condicao" not in (RAIZ / "frontend" / "js" / "filme.js"
                                  ).read_text(encoding="utf-8")
