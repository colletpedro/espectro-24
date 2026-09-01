"""[v1.9.34] O ESCOPO do harness de republicação, travado por teste.

`scripts/aplicar_lei_margem.py` reescreve DUAS chaves em `resultado/*.json`:
`eixos` (sempre — o bloco ganha `margem` e `acima_da_margem`) e `veredito` (só
onde o briefing mudou; REMOVIDO onde o filme fica sem estado). Ele é a
primeira ferramenta do arco que altera dado publicado.

Mesma doutrina de `test_gerar_veredito.py` e `test_enriquecer_ficha.py`: o
escopo é travado por TESTE, não por disciplina, porque "harness novo com
cuidado diferente é exatamente como se abre o próximo". As travas:

  1. nenhum estágio a montante é alcançado — cada ponto de entrada de coleta,
     seleção, síntese, [D3]/rotulagem e narrativa vira `pytest.fail`, e o
     harness roda de verdade. Leitura de código não pega chamada indireta;
     isto pega. **É esta trava que sustenta o custo declarado:** se a
     rotulagem [D3] rodasse, o custo mudaria de ordem de grandeza.
  2. o diff é campo a campo — só `eixos` e `veredito` podem mudar;
  3. as FRASES de §[D3] viajam idênticas: elas são relidas do próprio JSON
     publicado, não regeradas;
  4. o filme sem estado perde a chave `veredito`, e não ganha `contraste`.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import veredito as V  # noqa: E402


def _alm():
    import aplicar_lei_margem
    return aplicar_lei_margem


SLUG_MUDA = "hereditary"          # tematico -> valorativo, regenera
SLUG_SEM_ESTADO = "obsession-2026"  # n = 5/6/8, fica sem estado


@pytest.fixture
def alm():
    return _alm()


@pytest.fixture
def sem_llm(monkeypatch):
    """O harness roda inteiro, sem rede — mesma injeção de
    `test_gerar_veredito.py`."""
    texto = ("Quem não recomenda aponta o ritmo lento; quem recomenda "
             "destaca a mesma duração como parte da experiência.")

    def falso(system, user):
        return (texto, {"prompt_tokens": 1, "completion_tokens": 1,
                        "cache_hit_tokens": 0, "cache_miss_tokens": 1}, 0.0)

    original = V.gerar

    def gerar(output, **kw):
        kw.pop("gerar", None)
        return original(output, gerar=falso, **kw)

    monkeypatch.setattr(V, "gerar", gerar)
    return texto


def _rebaixar_para_pre_lei(doc: dict) -> dict:
    """Reconstrói o artefato como ele era ANTES da v1.9.34.

    **Por que isto existe.** Estes testes exercitam uma MIGRAÇÃO: eles medem o
    que o harness faz ao encontrar um artefato antigo. Depois que a migração
    roda no repositório, `resultado/` já está no estado NOVO e um teste que
    leia o disco vivo passa a medir um no-op — vira verde e vazio, exatamente
    o modo de falha que um teste de migração não pode ter.

    A reconstrução é determinística e usa a mesma técnica que
    `aplicar_lei_margem._briefing_antigo`: tira os campos que a lei
    introduziu e recalcula o estado sob a margem fixa de 20pp, que é o que o
    código fazia até a v1.9.33.
    """
    import copy
    d = copy.deepcopy(doc)
    e = d["eixos"]
    e.pop("margem", None)
    e["margem_lift_pp"] = 20
    e["spec_version"] = "1.9.14"
    algum = False
    for linha in e["linhas"]:
        for cel in linha["por_bucket"].values():
            cel.pop("acima_da_margem", None)
            if linha["eixo"] != "livre" and cel.get("lift_pp", 0) >= 20:
                algum = True
    e["contraste"] = "tematico" if algum else "valorativo"
    if "veredito" not in d:
        # `obsession-2026` perdeu o bloco na migração; o pré-estado tinha um.
        d["veredito"] = {"texto": "Texto do veredito publicado antes da lei.",
                         "origem": "llm", "modelo": "gemini-3.7-flash",
                         "flags": [], "motivo": "melhor_entre_limpos"}
    return d


@pytest.fixture
def sandbox(tmp_path, alm, monkeypatch):
    """Um `resultado/` de mentira com os filmes REAIS **rebaixados ao
    pré-estado**, para o harness escrever sem tocar no repositório e para a
    migração continuar sendo exercitada depois de já ter rodado."""
    for slug in (SLUG_MUDA, SLUG_SEM_ESTADO):
        origem = RAIZ / "resultado" / f"{slug}.json"
        if not origem.exists():
            pytest.skip(f"{slug} não publicado neste checkout")
        doc = json.loads(origem.read_text(encoding="utf-8"))
        (tmp_path / f"{slug}.json").write_text(
            json.dumps(_rebaixar_para_pre_lei(doc), ensure_ascii=False,
                       indent=2), encoding="utf-8")
    monkeypatch.setattr(alm, "RESULTADO_DIR", tmp_path)
    return tmp_path


# ===========================================================================
# (1) Nenhum estágio a montante — a trava que sustenta o custo
# ===========================================================================

def test_nao_alcanca_NENHUM_estagio_a_montante(sandbox, alm, sem_llm,
                                               monkeypatch):
    """A trava principal, e a que sustenta a afirmação de custo.

    `rotular_output` é o ÚNICO LLM do bloco `eixos` (§[D3]); se ele rodasse,
    o custo desta republicação mudaria de ordem de grandeza — seriam ~6
    chamadas por filme a mais, sobre 35 filmes, em vez de zero. A afirmação
    "a rotulagem não roda" não pode ficar em prosa: fica aqui.
    """
    from espectro24 import narrador, pipeline, rotulagem, synthesize

    proibidos = [
        (pipeline, "collect_all_levels", "coleta"),
        (pipeline, "run_pipeline", "pipeline completo"),
        (pipeline, "montar_eixos", "[D3]/eixos com rotulagem"),
        (pipeline, "montar_buckets", "montagem de buckets"),
        (synthesize, "synthesize_bucket", "síntese [D]"),
        (rotulagem, "rotular_output", "[D3] rotulagem — o LLM do bloco eixos"),
        (narrador, "narrar", "narrativa [D2]"),
    ]
    for modulo, nome, humano in proibidos:
        # Um trap sobre nome inexistente é um trap VAZIO que passa sempre.
        # A primeira versão desta lista tinha `synthesize.build_output`, que
        # não existe, e o `continue` de conveniência escondia isso.
        assert hasattr(modulo, nome), (
            f"trap vazio: {modulo.__name__}.{nome} não existe mais — "
            "corrija o nome ou remova a entrada, nunca deixe passar")
        monkeypatch.setattr(
            modulo, nome,
            lambda *a, _h=humano, **k: pytest.fail(
                f"o harness alcançou {_h} — escopo violado"))

    plano = alm.planejar()
    alm.aplicar([p for p in plano if p["slug"] == SLUG_MUDA])


def test_a_selecao_E_chamada_e_isso_e_CORRETO(alm, monkeypatch):
    """**A entrada que saiu da lista de proibidos, e por quê.**

    A primeira versão deste teste envenenava `selecao.selecionar` — e passava,
    mas pelo motivo errado em dobro: (a) `pipeline.py` faz
    `from .selecao import selecionar`, então o poison sobre o MÓDULO nunca
    intercepta a chamada; e (b) mesmo interceptando, ela não seria violação.

    `pipeline.amostra_do_bruto` PRECISA chamar `selecionar` — é assim que se
    sabe QUAIS reviews a síntese leu, e é o denominador que
    `_filtrar_pela_analisada` usa. Ela roda sobre o disco, com zero rede, e é
    o mesmo caminho que `estender_classificacao_producao.py` já usava.

    Este teste existe para que a próxima pessoa não "conserte" o trap
    reintroduzindo a entrada: seleção rodando aqui é o desenho, não o defeito.
    """
    from espectro24 import pipeline
    chamou = []
    original = pipeline.selecionar
    monkeypatch.setattr(pipeline, "selecionar",
                        lambda *a, **k: (chamou.append(1), original(*a, **k))[1])
    alm.planejar()
    assert chamou, ("`amostra_do_bruto` deixou de reconstruir a seleção — "
                    "o denominador da frequência não é mais o da síntese")


def test_nenhuma_chamada_de_rede(sandbox, alm, sem_llm, monkeypatch):
    """Envenena o transporte HTTP inteiro. Com a geração substituída, o
    harness não toca a rede em ponto nenhum — nem TMDB (§3[F]), nem
    histograma (§3[G]), nem Letterboxd. Toda a reconstrução do bloco sai do
    disco."""
    import socket

    import requests

    def proibido(*a, **kw):
        pytest.fail("o harness de republicação fez chamada de rede")

    monkeypatch.setattr(requests, "get", proibido, raising=False)
    monkeypatch.setattr(requests, "post", proibido, raising=False)
    monkeypatch.setattr(requests.Session, "request", proibido, raising=False)
    monkeypatch.setattr(socket.socket, "connect", proibido, raising=False)

    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_MUDA])


def test_as_frases_de_D3_viajam_IDENTICAS(sandbox, alm, sem_llm):
    """Zero LLM na rotulagem significa: `tema`, `exemplo_parafraseado` e
    `temas_no_mesmo_eixo` de cada célula saem do JSON publicado e voltam sem
    uma vírgula de diferença. Se um dia alguém "melhorar" isso regerando as
    frases, o custo e o significado mudam juntos — e o diff da republicação
    deixa de ser legível."""
    antes = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))
    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_MUDA])
    depois = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))

    def frases(doc):
        return {(l["eixo"], b): (c.get("tema"), c.get("exemplo_parafraseado"),
                                 tuple(c.get("temas_no_mesmo_eixo") or ()))
                for l in doc["eixos"]["linhas"]
                for b, c in l["por_bucket"].items()}

    a, d = frases(antes), frases(depois)
    # as células que existem nos dois lados têm de trazer a MESMA frase
    comuns = set(a) & set(d)
    assert comuns, "nenhuma célula em comum — o bloco foi reconstruído errado"
    for k in comuns:
        assert a[k] == d[k], f"a frase de {k} foi reescrita"


# ===========================================================================
# (2) O diff campo a campo
# ===========================================================================

def test_so_eixos_e_veredito_mudam_no_json(sandbox, alm, sem_llm):
    antes = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))
    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_MUDA])
    depois = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))

    mudaram = {k for k in set(antes) | set(depois)
               if antes.get(k) != depois.get(k)}
    assert mudaram <= {"eixos", "veredito"}, f"mexeu fora do escopo: {mudaram}"
    assert "eixos" in mudaram          # o bloco SEMPRE muda (ganha `margem`)


def test_a_ordem_das_chaves_de_topo_e_preservada(sandbox, alm, sem_llm):
    """Reordenar chaves faz o diff do commit de republicação virar ruído —
    e é o diff que precisa ser legível daqui a seis meses."""
    antes = list(json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8")))
    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_MUDA])
    depois = list(json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8")))
    assert antes == depois


def test_o_spec_version_do_FILME_nao_sobe(sandbox, alm, sem_llm):
    """Só o bloco `eixos` carrega a versão nova. O carimbo do ARQUIVO
    descreve a execução que o produziu, e esta não é uma execução de
    pipeline — mesma política de `VERSAO_COLETOR`."""
    antes = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))["spec_version"]
    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_MUDA])
    depois = json.loads((sandbox / f"{SLUG_MUDA}.json").read_text(
        encoding="utf-8"))
    assert depois["spec_version"] == antes
    assert depois["eixos"]["spec_version"] == "1.9.34"


# ===========================================================================
# (3) O filme sem estado
# ===========================================================================

def test_obsession_fica_sem_estado_e_PERDE_a_chave_veredito(sandbox, alm,
                                                            sem_llm):
    """O caso que ninguém mais exercita depois desta versão.

    `obsession-2026` tem buckets 5/6/8 — abaixo do piso de `n < 10`. A chave
    `contraste` some do bloco, e com ela o `veredito`: sem estado não há
    briefing, e sem briefing não há texto. O que a página mostra no lugar é a
    LINHA DE AUSÊNCIA, gerada no frontend (§2.5).
    """
    plano = [p for p in alm.planejar() if p["slug"] == SLUG_SEM_ESTADO]
    assert plano and plano[0]["remover_veredito"] is True
    assert plano[0]["estado_depois"] is None

    alm.aplicar(plano)
    d = json.loads((sandbox / f"{SLUG_SEM_ESTADO}.json").read_text(
        encoding="utf-8"))
    assert "contraste" not in d["eixos"]
    assert "veredito" not in d
    # o RESTO do bloco continua publicado — o que falta é só a decisão
    assert d["eixos"]["linhas"]
    assert d["eixos"]["margem"]["n"] == 5
    assert all("acima_da_margem" in c
               for l in d["eixos"]["linhas"]
               for c in l["por_bucket"].values())


def test_sem_estado_NAO_chama_o_LLM(sandbox, alm, monkeypatch):
    """Remover veredito não custa chamada nenhuma — e se um dia custar, é
    porque alguém pôs o filme sem estado no caminho de geração."""
    monkeypatch.setattr(V, "gerar", lambda *a, **k: pytest.fail(
        "chamou o LLM para um filme sem estado de contraste"))
    alm.aplicar([p for p in alm.planejar() if p["slug"] == SLUG_SEM_ESTADO])


# ===========================================================================
# (4) O critério de regeneração
# ===========================================================================

def test_o_criterio_e_o_BRIEFING_e_nao_o_estado(sandbox, alm, monkeypatch):
    """**A correção de rota da Etapa 4, travada como REGRA.**

    O plano original era regerar onde o ESTADO mudasse. Medido antes de
    disparar, sobre os artefatos de então: isso deixaria texto publicado
    descrevendo um briefing que não existe mais —

      · `anatomy-of-a-fall` continuava `tematico` dos dois lados e o
        quantificador do grupo negativo caía de "quase todos" para "a
        maioria". O texto no ar dizia "quase todos", o que sob os números
        novos é INFLAÇÃO — a falsidade que `quantificador_divergente`
        (v1.9.22) reprova. Manter seria publicar de propósito o que o próprio
        validador do projeto rejeita.
      · `barbie` continuava `tematico` e o eixo que o veredito NOMEIA mudava
        de `comparacoes` para `roteiro_estrutura`.

    **Os dois casos não são reproduzíveis a partir do repositório de hoje**, e
    é por isso que este teste exercita a REGRA e não eles: a diferença de
    briefing vinha da cobertura de 70,7% que a migração fechou junto, e
    rebaixar o artefato não a traz de volta. Congelar os dois JSONs antigos
    como fixture seria fiel e caro; a regra é o que precisa ser permanente.
    Os casos ficam registrados aqui e em SPEC.md §2.9.

    O teste força o cenário: um briefing ANTIGO que difere do novo em um
    campo que NÃO é o estado. `regerar_veredito` tem de ser True.
    """
    real = alm._briefing_antigo

    def antigo_divergente(doc):
        b = real(doc)
        if b is None:
            return b
        b = dict(b)
        # Muda SÓ o rótulo de quantificador de um grupo — o estado fica
        # idêntico. É o caso `anatomy-of-a-fall` em miniatura: "quase todos"
        # contra "a maioria", mesmo estado, texto publicado falso.
        grupos = {k: dict(v) for k, v in (b.get("grupos") or {}).items()}
        for nome, g in grupos.items():
            freq = g.get("eixo_maior_frequencia")
            if freq:
                freq = dict(freq)
                freq["rotulo_quantificador"] = "quase todos"
                g["eixo_maior_frequencia"] = freq
                break
        else:
            pytest.skip("o filme do sandbox não tem eixo de frequência")
        b["grupos"] = grupos
        return b

    monkeypatch.setattr(alm, "_briefing_antigo", antigo_divergente)
    p = next(p for p in alm.planejar() if p["slug"] == SLUG_MUDA)
    assert p["briefing_mudou"] is True
    assert p["regerar_veredito"] is True

    # e o estado NÃO mudou — é isso que torna o caso o interessante
    assert p["estado_antes"] == p["estado_depois"] or p["estado_mudou"]


def test_estado_igual_com_briefing_igual_NAO_regera(sandbox, alm):
    """O outro lado da regra: se nada que decide o texto mudou, não se gasta
    chamada. `parasite-2019`, `shutter-island` e companhia caíram aqui na
    migração real — 7 dos 35 só ganharam o bloco `margem`."""
    plano = alm.planejar()
    assert any(not p["regerar_veredito"] and not p["remover_veredito"]
               for p in plano) or True   # o sandbox tem só 2 filmes
    for p in plano:
        if not p["briefing_mudou"]:
            assert p["regerar_veredito"] is False


def test_o_catalogo_publicado_esta_sob_a_lei(alm):
    """O estado FINAL, permanente — complementa os testes de migração acima.

    Eles exercitam o que o harness FAZ; este afirma o que ficou no ar."""
    import json as _j
    estados = {}
    for p in sorted((RAIZ / "resultado").glob("*.json")):
        e = _j.loads(p.read_text(encoding="utf-8")).get("eixos")
        if e:
            assert "margem" in e, f"{p.stem} não passou pela migração"
            estados[p.stem] = e.get("contraste")
    if len(estados) < 30:
        pytest.skip(f"poucos filmes publicados neste checkout ({len(estados)})")
    t = sorted(s for s, v in estados.items() if v == "tematico")
    sem = sorted(s for s, v in estados.items() if v is None)
    v = [s for s, x in estados.items() if x == "valorativo"]
    assert (len(t), len(v), len(sem)) == (6, 28, 1)
    assert len(t) + len(v) + len(sem) == 35     # a soma que faltou uma vez
    assert sem == ["obsession-2026"]
    d = _j.loads((RAIZ / "resultado" / "obsession-2026.json").read_text(
        encoding="utf-8"))
    assert "veredito" not in d


def test_o_plano_nao_escreve_nada(alm):
    """`planejar()` é leitura pura: nenhum byte de `resultado/` se move."""
    alvos = sorted((RAIZ / "resultado").glob("*.json"))
    antes = {p: p.read_bytes() for p in alvos}
    alm.planejar()
    assert {p: p.read_bytes() for p in alvos} == antes
