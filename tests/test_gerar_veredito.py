"""[v1.9.21, §3[V]] O ESCOPO do harness novo, travado por teste.

`scripts/gerar_veredito.py` não passa pela guarda de lote de
`publicar_catalogo.py`, e não deve: regenerar veredito não faz rede fora do
adaptador de LLM, não re-scrapeia e não toca o histórico `passadas`.

Mas a lição do footgun que a v1.9.21 fechou é que **harness novo com "cuidado
diferente" é exatamente como se abre o próximo**. O risco aqui é menor —
sobrescrever 35 JSONs — e não é zero. Então o escopo é travado por TESTE, não
por disciplina, com a mesma técnica que pegou o footgun original: substituir
o ponto de entrada por `pytest.fail` e rodar de verdade. Leitura de código
não pega o que uma chamada indireta faz; isto pega.

Três travas:
  1. nenhum estágio a montante é chamado;
  2. nenhuma chamada de rede sai fora do adaptador de LLM;
  3. rodar altera APENAS o bloco `veredito` — diff campo a campo do resto.

A terceira é a que protege a Entrega 5 inteira.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import veredito as V  # noqa: E402


def _gv():
    import gerar_veredito
    return gerar_veredito


SLUG = "the-godfather"


@pytest.fixture
def documento():
    caminho = RAIZ / "resultado" / f"{SLUG}.json"
    if not caminho.exists():
        pytest.skip(f"{SLUG} não publicado neste checkout")
    from conftest import exige_resultado_sob_a_lei
    exige_resultado_sob_a_lei(caminho)
    return json.loads(caminho.read_text(encoding="utf-8"))


@pytest.fixture
def sandbox(tmp_path, documento, monkeypatch):
    """Um `resultado/` de mentira com UM filme real dentro, para o harness
    escrever sem tocar no repositório."""
    gv = _gv()
    (tmp_path / f"{SLUG}.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(gv, "RESULTADO_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sem_llm(monkeypatch):
    """Substitui a geração por um texto fixo e VÁLIDO — o harness roda
    inteiro, sem rede."""
    texto = ("Quem não recomenda aponta o ritmo lento; quem recomenda destaca "
             "a mesma duração como parte da experiência.")

    def falso(system, user):
        return (texto, {"prompt_tokens": 1, "completion_tokens": 1,
                        "cache_hit_tokens": 0, "cache_miss_tokens": 1}, 0.0)

    original = V.gerar

    def gerar(output, **kw):
        kw.pop("gerar", None)
        return original(output, gerar=falso, **kw)

    monkeypatch.setattr(V, "gerar", gerar)
    return texto


# ===========================================================================
# (1) Nenhum estágio a montante
# ===========================================================================

def test_nao_chama_NENHUM_estagio_a_montante(sandbox, sem_llm, monkeypatch):
    """A trava principal. Cada ponto de entrada de coleta, seleção, síntese,
    [D3] e narrativa vira um `pytest.fail`; se o harness tocar em qualquer um
    deles, o teste diz QUAL.

    Mesma técnica usada em `test_publicar_catalogo` com `publicar_um` — ela
    pega o que a leitura de código não pega, porque uma chamada indireta
    (import de conveniência, helper compartilhado) não aparece num grep.
    """
    from espectro24 import eixos, narrador, pipeline, rotulagem
    from espectro24 import selecao, synthesize

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
    ]
    for modulo, nome, humano in proibidos:
        if not hasattr(modulo, nome):
            continue
        monkeypatch.setattr(modulo, nome, _explode(humano))

    r = _gv().gerar_um(SLUG, saida=sandbox)
    assert r["ok"] is True


def _explode(humano):
    def falha(*a, **kw):
        pytest.fail(f"o harness de veredito chamou {humano} — ele não pode "
                    f"rodar nenhum estágio a montante")
    return falha


def test_nao_importa_o_coletor_nem_o_fetcher_no_caminho_de_geracao(sandbox,
                                                                   sem_llm):
    """Complemento estrutural do teste acima: o módulo `veredito` não pode
    depender de coleta nem de rede HTTP. Se um dia alguém precisar de um dado
    que não está no JSON, o caminho certo é gravá-lo no JSON a montante — não
    ir buscá-lo daqui."""
    import espectro24.veredito as mod

    fonte = Path(mod.__file__).read_text(encoding="utf-8")
    for proibido in ("from .collector", "from .fetcher", "from .pipeline",
                     "from .selecao", "from .ficha", "import requests"):
        assert proibido not in fonte, f"veredito.py importa {proibido!r}"


# ===========================================================================
# (2) Nenhuma rede fora do adaptador de LLM
# ===========================================================================

def test_nenhuma_chamada_de_rede_fora_do_adaptador(sandbox, sem_llm,
                                                   monkeypatch):
    """Envenena o transporte HTTP inteiro. Com a geração substituída, um
    harness correto não toca a rede em NENHUM ponto — nem TMDB (§3[F]), nem
    histograma (§3[G]), nem Letterboxd."""
    import socket

    import requests

    def proibido(*a, **kw):
        pytest.fail("o harness de veredito fez chamada de rede")

    monkeypatch.setattr(requests, "get", proibido, raising=False)
    monkeypatch.setattr(requests, "post", proibido, raising=False)
    monkeypatch.setattr(requests.Session, "request", proibido, raising=False)
    monkeypatch.setattr(socket.socket, "connect", proibido, raising=False)

    assert _gv().gerar_um(SLUG, saida=sandbox)["ok"] is True


# ===========================================================================
# (3) Só o bloco `veredito` muda — o teste que protege a Entrega 5
# ===========================================================================

def test_so_o_bloco_veredito_muda_no_json(sandbox, documento, sem_llm):
    """Diff CAMPO A CAMPO do documento inteiro. Todo campo fora de `veredito`
    tem de sair idêntico — mesma estrutura, mesmos valores, mesma ordem de
    chaves de topo.

    Se este teste falhar, a Entrega 5 ("regenerar o veredito dos 35 não é
    republicar o filme") deixou de ser verdade, e nenhum diff manual é
    substituto: o documento tem dezenas de milhares de campos.
    """
    _gv().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))

    assert "veredito" in depois
    for chave in set(documento) | set(depois):
        if chave == "veredito":
            continue
        assert json.dumps(depois.get(chave), ensure_ascii=False, sort_keys=True) \
            == json.dumps(documento.get(chave), ensure_ascii=False, sort_keys=True), \
            f"o campo {chave!r} mudou"


def test_a_ordem_das_chaves_de_topo_e_preservada(sandbox, documento, sem_llm):
    """`veredito` entra no FIM, e nada é reordenado — um diff de git legível
    é o que torna a Entrega 5 auditável por leitura humana, além do teste."""
    _gv().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    # `documento` já pode TER o bloco (é o estado normal depois da v1.9.21):
    # comparar contra a lista crua faria o teste passar antes da publicação e
    # falhar depois, por motivo nenhum.
    esperado = [k for k in documento if k != "veredito"]
    assert [k for k in depois if k != "veredito"] == esperado
    assert list(depois)[-1] == "veredito"


def test_o_spec_version_do_FILME_nao_sobe(sandbox, documento, sem_llm):
    """Regenerar só o veredito não re-roda coleta, síntese, [D3] nem
    narrativa — carimbar a versão nova no topo afirmaria que rodou. O bloco
    carrega a PRÓPRIA versão, como `eixos` já faz desde a v1.9.14 (mesma
    política de `VERSAO_COLETOR`)."""
    from espectro24.config import SPEC_VERSION

    _gv().gerar_um(SLUG, saida=sandbox)
    depois = json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert depois["spec_version"] == documento["spec_version"]
    assert depois["veredito"]["spec_version"] == SPEC_VERSION


def test_aborta_sem_gravar_se_algo_fora_do_bloco_mudar(sandbox, documento,
                                                      monkeypatch):
    """A mesma guarda do teste acima, mas em PRODUÇÃO: o harness confere
    campo a campo antes de gravar e aborta em vez de publicar um documento
    que ele não sabe explicar."""
    gv = _gv()

    def sabotar(output, **kw):
        output["total_reviews_observadas"] = -1
        return {"texto": "x", "origem": "llm", "modelo": "m", "flags": [],
                "motivo": "m", "spec_version": "0"}

    monkeypatch.setattr(V, "gerar", sabotar)
    antes = (sandbox / f"{SLUG}.json").read_text(encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        gv.gerar_um(SLUG, saida=sandbox)
    assert "total_reviews_observadas" in str(e.value)
    assert (sandbox / f"{SLUG}.json").read_text(encoding="utf-8") == antes


# ===========================================================================
# População e modo A/B
# ===========================================================================

def test_slugs_publicados_pula_filme_sem_eixos(sandbox):
    gv = _gv()
    (sandbox / "sem-eixos.json").write_text(
        json.dumps({"slug": "sem-eixos", "buckets": []}), encoding="utf-8")
    (sandbox / "quebrado.json").write_text("{ nao é json", encoding="utf-8")
    slugs = gv.slugs_publicados()
    assert SLUG in slugs
    assert "sem-eixos" not in slugs and "quebrado" not in slugs


def test_saida_alternativa_nao_toca_o_resultado_original(tmp_path, sandbox,
                                                         sem_llm):
    """O que o A/B de modelo usa: os dois braços gravam em diretórios
    próprios, e `resultado/` fica intacto até haver decisão."""
    gv = _gv()
    antes = (sandbox / f"{SLUG}.json").read_text(encoding="utf-8")
    destino = tmp_path / "braco-a"
    gv.gerar_um(SLUG, saida=destino, so_veredito=True)

    assert (sandbox / f"{SLUG}.json").read_text(encoding="utf-8") == antes
    parcial = json.loads((destino / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert set(parcial) == {"slug", "veredito"}


# ===========================================================================
# [v1.9.22] ESTABILIDADE do desempate por abertura
# ===========================================================================
# O desempate consulta um histórico de aberturas, e histórico é justamente o
# que torna uma saída dependente de ordem. A sessão que autorizou o critério
# pôs duas condições, e estes testes são elas:
#   · o resultado não pode depender da ORDEM dos filmes;
#   · regenerar UM filme isolado tem de dar o mesmo resultado que a
#     regeneração completa daria para ele.
# A política que satisfaz as duas: o histórico vem do que está PUBLICADO e
# NÃO é atualizado durante a execução.

def test_o_historico_de_aberturas_nao_depende_da_ordem(sandbox, documento):
    """Função pura do estado do diretório — `sorted(glob)` e soma comutativa.
    Sem isto, o desempate seria não-determinístico entre execuções."""
    gv = _gv()
    a = gv.aberturas_publicadas()
    for _ in range(3):
        assert gv.aberturas_publicadas() == a


def test_regenerar_isolado_ve_o_MESMO_historico_que_a_regeneracao_completa(
        sandbox, documento, monkeypatch):
    """A condição que decide se o critério entra. O histórico de um filme é
    "os OUTROS publicados" — e isso não muda conforme ele seja regenerado
    sozinho ou no meio dos 35, porque nada é atualizado no meio do caminho.
    """
    gv = _gv()
    # dois filmes de mentira, com aberturas conhecidas, além do real
    for nome, texto in (("filme-a", "A divergência está no roteiro."),
                        ("filme-b", "As opiniões divergem sobre o roteiro.")):
        (sandbox / f"{nome}.json").write_text(json.dumps(
            {"slug": nome, "veredito": {"texto": texto, "texto_modelo": texto}}),
            encoding="utf-8")

    isolado = gv.aberturas_publicadas(exceto=SLUG)
    # "regeneração completa": o histórico consultado para SLUG é o mesmo,
    # porque os outros arquivos não mudaram durante a execução
    for outro in ("filme-a", "filme-b"):
        gv.aberturas_publicadas(exceto=outro)      # não deve ter efeito
    assert gv.aberturas_publicadas(exceto=SLUG) == isolado
    assert isolado.get("diver") == 1 and isolado.get("opini") == 1


def test_o_filme_gerado_NAO_entra_no_proprio_historico(sandbox, documento):
    """Senão o veredito anterior dele mesmo penalizaria a abertura que ele
    talvez devesse manter — e a regeneração viraria uma fuga da própria
    escolha anterior, não uma escolha entre candidatos."""
    gv = _gv()
    com = gv.aberturas_publicadas()
    sem = gv.aberturas_publicadas(exceto=SLUG)
    padrao = V.padrao_de_abertura(
        json.loads((sandbox / f"{SLUG}.json").read_text(encoding="utf-8"))
        ["veredito"]["texto_modelo"])
    assert sem.get(padrao, 0) == com.get(padrao, 0) - 1


def test_o_desempate_pode_ser_DESLIGADO_para_medicao(sandbox, sem_llm):
    """`--sem-desempate-de-abertura`: existe para medir o efeito do critério
    contra ele mesmo desligado, que é como a v1.9.22 decidiu se ele entra."""
    gv = _gv()
    r = gv.gerar_um(SLUG, saida=sandbox, usar_aberturas=False)
    assert r["ok"] is True


def test_o_historico_e_tirado_UMA_vez_e_nao_ve_o_que_a_execucao_grava(
        sandbox, sem_llm, monkeypatch):
    """**Bug real, achado no caminho de PRODUÇÃO e invisível para os testes
    que usavam `--saida`.** `gerar_um` sem `--saida` grava em `resultado/`.
    Se o histórico fosse recalculado a cada filme, o filme nº 2 veria o
    veredito NOVO do nº 1 — e a saída passaria a depender da ORDEM, que é
    exatamente a instabilidade que a política de estabilidade existe para
    impedir e a condição que a sessão pôs para o critério entrar.

    A trava: o snapshot é tirado ANTES do laço e `historico_para` deriva
    dele. Este teste grava por cima de um filme no meio do caminho e exige
    que o histórico do snapshot não se mexa.
    """
    gv = _gv()
    snapshot = gv.snapshot_de_aberturas()
    antes = gv.historico_para(snapshot, SLUG)

    # simula a escrita que a execução real faz num OUTRO filme
    (sandbox / "outro.json").write_text(json.dumps(
        {"slug": "outro", "veredito": {
            "texto": "A divergência central está no roteiro.",
            "texto_modelo": "A divergência central está no roteiro."}}),
        encoding="utf-8")

    assert gv.historico_para(snapshot, SLUG) == antes, (
        "o histórico derivado do snapshot mudou depois de uma escrita — "
        "a saída voltou a depender da ordem dos filmes")
    # e um snapshot NOVO enxerga a escrita: é isso que torna o teste um
    # detector de verdade, e não uma tautologia sobre um dict congelado.
    assert gv.historico_para(gv.snapshot_de_aberturas(), SLUG) != antes


def test_a_ordem_dos_filmes_nao_muda_o_historico_de_ninguem(sandbox):
    """Order-independence por construção: cada filme deriva do MESMO
    snapshot, então percorrer os 35 em qualquer ordem dá o mesmo histórico
    para cada um."""
    gv = _gv()
    for nome, texto in (("filme-a", "A divergência está no roteiro."),
                        ("filme-b", "As opiniões divergem sobre o roteiro."),
                        ("filme-c", "Quem recomenda destaca o roteiro.")):
        (sandbox / f"{nome}.json").write_text(json.dumps(
            {"slug": nome, "veredito": {"texto": texto, "texto_modelo": texto}}),
            encoding="utf-8")
    snapshot = gv.snapshot_de_aberturas()
    direta = {s: gv.historico_para(snapshot, s) for s in sorted(snapshot)}
    inversa = {s: gv.historico_para(snapshot, s) for s in sorted(snapshot, reverse=True)}
    assert direta == inversa
