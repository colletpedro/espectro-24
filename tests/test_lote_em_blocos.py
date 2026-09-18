"""[2026-09-18] Driver por BLOCOS: passes + consenso + verificador por bloco.

O defeito medido no lote noturno de 18/09: os passes rodavam um a um sobre
TODOS os filmes e o consenso só depois do último. O saldo zerou no passe 3 e
2,4 passes pagos (~US$1,75) ficaram em `passe_*.jsonl`, fora da produção.

O que se prova, em ordem de importância — tudo com LLM FALSO, zero chamada:

1. **Interrupção deixa os arquivos consistentes.** Saldo que acaba no meio dos
   passes de um bloco, ou no meio do verificador, NÃO toca `consenso.jsonl`,
   `consenso_verificado.jsonl` nem o manifesto (byte a byte); o que foi pago
   fica nos `passe_*.jsonl`, e o resume não paga duas vezes.
2. **A gravação é atômica**: queda entre os arquivos do commit deixa cada um
   INTEIRO, o estado inconsistente é DETECTADO, e o reparo o fecha sem gastar.
3. **Por blocos = monolítico.** Blocos de 1, blocos de 4 e o `cmd_consenso`
   original produzem o MESMO consenso e o MESMO verificado, byte a byte — é a
   prova de que a votação nunca exigiu o lote inteiro.
4. Os filmes já publicados (aqui, `velho`) passam intactos, linha a linha.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import lote_em_blocos as D  # noqa: E402
import verificador_impacto as vi  # noqa: E402
import votacao_3 as v3  # noqa: E402
from classificar_10 import EIXOS  # noqa: E402
from espectro24 import atomico  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.preco import custo_usd  # noqa: E402

IMPACTO, ATUACAO = "impacto_emocional", "atuacao"
assert IMPACTO in EIXOS and ATUACAO in EIXOS
BUCKETS = ["negativas", "medianas", "positivas"]
USO = {"prompt_tokens": 1000, "completion_tokens": 40,
       "cache_hit_tokens": 800, "cache_miss_tokens": 200}
N_REVIEWS = 6          # por filme; índices 0..5
NOVOS = ["n1", "n2", "n3", "n4"]


# --- o mundo de mentira -------------------------------------------------------

def _jsonl(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8")
            .splitlines() if l.strip()]


def _idx(review_id: str) -> int:
    return int(review_id.rsplit("-r", 1)[1])


def eixos_do_voto(review_id: str, passe: int) -> list[str]:
    """Determinístico. Par → impacto+atuação nos 3 passes. `i == 1` recebe o
    impacto SÓ no passe 3 (1 voto de 3: o consenso o descarta)."""
    i = _idx(review_id)
    if i % 2 == 0:
        return [IMPACTO, ATUACAO]
    if i == 1 and passe == 3:
        return [ATUACAO, IMPACTO]
    return [ATUACAO]


def veredito(review_id: str) -> bool:
    return _idx(review_id) % 4 != 0          # `-r0` e `-r4` são removidas


class LLM:
    """Cliente falso com ORÇAMENTO: `orc_class`/`orc_verif` são quantas
    chamadas ainda respondem; `None` = ilimitado. Estourado, faz o que o
    adaptador real faz com um 402 — levanta `LLMSaldoEsgotado` e liga a
    parada por saldo do processo."""

    def __init__(self, orc_class=None, orc_verif=None, falha_em=None):
        self.orc_class, self.orc_verif = orc_class, orc_verif
        self.falha_em = falha_em or set()     # {(review_id, passe)} com erro
        self.classificacoes: Counter = Counter()
        self.verificacoes: Counter = Counter()
        self._lock = Lock()

    @property
    def n_total(self) -> int:
        return sum(self.classificacoes.values()) + sum(self.verificacoes.values())

    def _gastar(self, campo: str) -> None:
        orc = getattr(self, campo)
        if orc is None:
            return
        if orc <= 0:
            S._parada_por_saldo.set()
            raise S.LLMSaldoEsgotado("saldo_esgotado: fake — 402")
        setattr(self, campo, orc - 1)

    def classificacao(self, system, user, model, *, max_tokens, unidade,
                      client=None):
        slug, bucket, rid, passe = unidade.split("/")
        n_passe = int(passe.removeprefix("passe"))
        with self._lock:
            self._gastar("orc_class")
            self.classificacoes[(rid, n_passe)] += 1
        if (rid, n_passe) in self.falha_em:
            raise ValueError("falha de conteúdo simulada")
        return {"texto": json.dumps({"eixos": eixos_do_voto(rid, n_passe),
                                     "temas_livres": []}),
                "provider": "deepseek", "modelo": "deepseek-v4-flash",
                "uso": dict(USO), "latencia_s": 0.1, "fallback_conteudo": None}

    def verificador(self, system, user, model, *, max_tokens, estagio, unidade,
                    client=None):
        slug, rid = unidade.split("/")
        with self._lock:
            self._gastar("orc_verif")
            self.verificacoes[rid] += 1
        return {"texto": json.dumps({"confirma": veredito(rid), "frase": "f",
                                     "alvo": "espectador"}),
                "provider": "deepseek", "modelo": "deepseek-v4-flash",
                "uso": dict(USO), "latencia_s": 0.1, "fallback_conteudo": None}


def _escrever_jsonl(caminho: Path, linhas: list[dict]) -> None:
    caminho.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n"
                               for l in linhas), encoding="utf-8")


def criar_mundo(base: Path, monkeypatch, novos=tuple(NOVOS)) -> Path:
    """`resultado/votacao-3/` mínimo: `velho` JÁ classificado, consensuado,
    verificado e coberto pelo manifesto (o análogo dos 99 publicados), e os
    `novos` registrados na amostra, sem nenhum passe. Aponta os módulos para
    `base` ANTES de ler qualquer coisa: as funções de leitura usam caminhos de
    módulo, e sem isso leriam os arquivos REAIS do repositório."""
    votacao = base / "votacao-3"
    votacao.mkdir(parents=True)
    apontar(monkeypatch, base)
    tid = v3.taxonomia_id()
    filmes = ["velho", *novos]
    reviews = [{"slug": s, "perfil": "x", "bucket": BUCKETS[i % 3],
                "id": f"{s}-r{i}", "nivel": float(1 + i % 5), "n_chars": 20,
                "texto": f"review {i} de {s}"}
               for s in filmes for i in range(N_REVIEWS)]
    amostra = {"taxonomia_id": tid,
               "filmes": [{"slug": s, "perfil": "x"} for s in filmes],
               "reviews": reviews}
    (votacao / "amostra.json").write_text(json.dumps(amostra), encoding="utf-8")

    velhos = [r for r in reviews if r["slug"] == "velho"]
    for n in (1, 2, 3):
        _escrever_jsonl(votacao / f"passe_{n}.jsonl", [
            {"ok": True, "taxonomia_id": tid, "passe": n, "slug": "velho",
             "perfil": "x", "bucket": r["bucket"], "id": r["id"],
             "nivel": r["nivel"], "n_chars": r["n_chars"],
             "eixos": eixos_do_voto(r["id"], n), "eixos_invalidos": [],
             "uso": dict(USO), "ts": "2026-09-01T12:00:00+00:00"}
            for r in velhos])
    passes = [v3._ler_passe(n) for n in (1, 2, 3)]
    linhas, _ = v3.consenso_incremental([], passes, amostra, ["velho"])
    candidatas = [l for l in linhas if IMPACTO in l["eixos"]]
    verificacoes = [{"ok": True, "variante": "V2_alvo", "passe": 1, "id": l["id"],
                     "n_chars": 20, "confirma": veredito(l["id"]), "frase": "f",
                     "alvo": "espectador", "uso": dict(USO),
                     "ts": "2026-09-01T12:00:00+00:00"} for l in candidatas]
    _escrever_jsonl(votacao / "verificador_producao.jsonl", verificacoes)
    verificado = vi.gerar_consenso_verificado(
        linhas, {v["id"]: v["confirma"] for v in verificacoes})
    _escrever_jsonl(votacao / "consenso.jsonl", linhas)
    _escrever_jsonl(votacao / "consenso_verificado.jsonl", verificado)
    (votacao / "verificador_manifesto.json").write_text(json.dumps({
        "fonte_n_linhas": len(linhas), "n_candidatas": len(candidatas)}),
        encoding="utf-8")
    return base


def apontar(monkeypatch, base: Path) -> None:
    votacao = base / "votacao-3"
    monkeypatch.setattr(v3, "RAIZ", base)
    monkeypatch.setattr(v3, "SAIDA", votacao)
    monkeypatch.setattr(v3, "ARQ_AMOSTRA", votacao / "amostra.json")
    monkeypatch.setattr(v3, "ARQ_PASSE",
                        {n: votacao / f"passe_{n}.jsonl" for n in (1, 2, 3)})
    monkeypatch.setattr(v3, "ARQ_CONSENSO", votacao / "consenso.jsonl")
    monkeypatch.setattr(vi, "RAIZ", base)
    monkeypatch.setattr(vi, "ARQ_PRODUCAO", votacao / "verificador_producao.jsonl")
    monkeypatch.setattr(vi, "ARQ_CONSENSO_PRODUCAO", votacao / "consenso.jsonl")
    monkeypatch.setattr(vi, "ARQ_AMOSTRA_PRODUCAO", votacao / "amostra.json")
    monkeypatch.setattr(vi, "ARQ_CONSENSO_VERIFICADO",
                        votacao / "consenso_verificado.jsonl")
    monkeypatch.setattr(vi, "ARQ_MANIFESTO_VERIFICADOR",
                        votacao / "verificador_manifesto.json")


def instalar(monkeypatch, llm: LLM) -> None:
    monkeypatch.setattr(v3, "deepseek_client", lambda *a, **kw: object())
    monkeypatch.setattr(vi, "deepseek_client", lambda *a, **kw: object())
    monkeypatch.setattr(v3, "resposta_classificacao", llm.classificacao)
    monkeypatch.setattr(vi, "resposta_json_com_fallback", llm.verificador)


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    monkeypatch.setattr(D, "registrar_bloco", lambda bloco: (0, []))
    monkeypatch.setattr(D, "_saldo", lambda: None)
    monkeypatch.setattr(S, "saldo_deepseek", lambda *a, **kw: None)
    S.limpar_parada_por_saldo()
    yield
    S.limpar_parada_por_saldo()


@pytest.fixture
def mundo(tmp_path, monkeypatch):
    return criar_mundo(tmp_path / "mundo", monkeypatch)


def producao(base: Path) -> dict[str, bytes]:
    v = base / "votacao-3"
    return {n: (v / n).read_bytes() for n in
            ("consenso.jsonl", "consenso_verificado.jsonl",
             "verificador_manifesto.json")}


def slugs_do(base: Path, arquivo: str) -> set[str]:
    return {l["slug"] for l in _jsonl(base / "votacao-3" / arquivo)}


def lista_de(tmp_path: Path, slugs: list[str]) -> str:
    f = tmp_path / "lista.txt"
    f.write_text("\n".join(slugs) + "\n", encoding="utf-8")
    return str(f)


# --- utilitários puros --------------------------------------------------------

def test_dividir_em_blocos_preserva_a_ordem_e_o_tamanho():
    assert D.dividir_em_blocos(list("abcdefg"), 3) == [
        ["a", "b", "c"], ["d", "e", "f"], ["g"]]
    assert D.dividir_em_blocos(list("ab"), 10) == [["a", "b"]]
    assert D.dividir_em_blocos([], 3) == []


def test_dividir_em_blocos_descarta_repetidos_sem_mudar_a_ordem():
    assert D.dividir_em_blocos(["a", "b", "a", "c", "b"], 2) == [
        ["a", "b"], ["c"]]


def test_tamanho_de_bloco_invalido_e_recusado():
    with pytest.raises(ValueError):
        D.dividir_em_blocos(["a"], 0)


# --- 1. um bloco completo -----------------------------------------------------

def test_um_bloco_commita_os_tres_arquivos_consistentes(mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    velho_antes = [l for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")
                   if l["slug"] == "velho"]

    r = D.processar_bloco(["n1", "n2"])

    consenso = _jsonl(mundo / "votacao-3" / "consenso.jsonl")
    assert {l["slug"] for l in consenso} == {"velho", "n1", "n2"}
    assert [l for l in consenso if l["slug"] == "velho"] == velho_antes
    keys = [(l["slug"], l["bucket"], l["id"]) for l in consenso]
    assert keys == sorted(keys)
    manifesto = json.loads((mundo / "votacao-3"
                            / "verificador_manifesto.json").read_text())
    assert manifesto["fonte_n_linhas"] == len(consenso)
    assert D.estado_consistente() == []
    # 2 filmes × 6 reviews × 3 passes; verificador: 3 pares por filme.
    assert sum(llm.classificacoes.values()) == 36
    assert sum(llm.verificacoes.values()) == 6
    assert r["incompletas"] == 0 and r["reviews_no_consenso"] == 12


def test_o_verificado_remove_so_o_que_o_verificador_removeu(mundo, monkeypatch):
    instalar(monkeypatch, LLM())
    D.processar_bloco(["n1"])
    por_id = {l["id"]: l for l in _jsonl(
        mundo / "votacao-3" / "consenso_verificado.jsonl")}
    assert IMPACTO not in por_id["n1-r0"]["eixos"]        # veredito: remove
    assert IMPACTO in por_id["n1-r2"]["eixos"]            # veredito: confirma
    assert ATUACAO in por_id["n1-r0"]["eixos"]            # outros eixos intactos
    assert "verificacao_pendente" not in por_id["n1-r0"]


def test_o_consenso_do_bloco_aplica_a_maioria_de_dois_em_tres(mundo, monkeypatch):
    instalar(monkeypatch, LLM())
    D.processar_bloco(["n1"])
    por_id = {l["id"]: l for l in _jsonl(
        mundo / "votacao-3" / "consenso.jsonl")}
    assert por_id["n1-r1"]["eixos"] == [ATUACAO]          # impacto: 1 voto
    assert por_id["n1-r1"]["votos"][IMPACTO] == 1


# --- 3. por blocos = monolítico ----------------------------------------------

def test_blocos_de_1_blocos_de_4_e_o_cmd_consenso_original_dao_o_mesmo_arquivo(
        tmp_path, monkeypatch):
    """A prova de que a votação nunca exigiu o lote inteiro."""
    resultados = {}
    for nome, tamanho in (("b1", 1), ("b4", 4)):
        base = criar_mundo(tmp_path / nome, monkeypatch)
        instalar(monkeypatch, LLM())
        rc = D.main([lista_de(tmp_path, NOVOS), "--tamanho-bloco", str(tamanho)])
        assert rc == 0
        resultados[nome] = producao(base)
        assert D.estado_consistente() == []

    assert resultados["b1"]["consenso.jsonl"] == resultados["b4"]["consenso.jsonl"]
    assert (resultados["b1"]["consenso_verificado.jsonl"]
            == resultados["b4"]["consenso_verificado.jsonl"])

    # ...e contra o `cmd_consenso` MONOLÍTICO original, sobre os mesmos passes.
    base = tmp_path / "b1"
    apontar(monkeypatch, base)
    mono = base / "votacao-3" / "monolitico.jsonl"
    monkeypatch.setattr(v3, "ARQ_CONSENSO", mono)
    v3.cmd_consenso()
    assert mono.read_bytes() == resultados["b1"]["consenso.jsonl"]


def test_cada_bloco_so_chama_o_llm_para_os_seus_filmes(mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1"])
    assert {rid.split("-r")[0] for rid, _ in llm.classificacoes} == {"n1"}
    assert {rid.split("-r")[0] for rid in llm.verificacoes} == {"n1"}


def test_reexecutar_um_bloco_ja_feito_nao_gasta_nada(mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1", "n2"])
    depois = producao(mundo)
    n = llm.n_total
    D.processar_bloco(["n1", "n2"])
    assert llm.n_total == n
    assert producao(mundo)["consenso.jsonl"] == depois["consenso.jsonl"]
    assert (producao(mundo)["consenso_verificado.jsonl"]
            == depois["consenso_verificado.jsonl"])


def test_filme_ja_classificado_so_precisa_do_commit_e_nao_gasta_passe(
        mundo, monkeypatch):
    """O caso REAL dos 20 filmes com os 3 passes completos do lote noturno:
    entram no consenso sem uma única chamada de classificação."""
    votacao = mundo / "votacao-3"
    tid = v3.taxonomia_id()
    for n in (1, 2, 3):
        with (votacao / f"passe_{n}.jsonl").open("a", encoding="utf-8") as f:
            for i in range(N_REVIEWS):
                rid = f"n1-r{i}"
                f.write(json.dumps({
                    "ok": True, "taxonomia_id": tid, "passe": n, "slug": "n1",
                    "perfil": "x", "bucket": BUCKETS[i % 3], "id": rid,
                    "nivel": 3.0, "n_chars": 20,
                    "eixos": eixos_do_voto(rid, n), "eixos_invalidos": []}) + "\n")
    llm = LLM(orc_class=0)          # qualquer chamada de classificação estoura
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1"])
    assert sum(llm.classificacoes.values()) == 0
    assert "n1" in slugs_do(mundo, "consenso.jsonl")
    assert D.estado_consistente() == []


# --- 1. interrupção: saldo no meio dos passes --------------------------------

def test_saldo_que_acaba_no_meio_dos_passes_nao_toca_nenhum_dos_tres_arquivos(
        mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1", "n2"])                    # bloco 1 commitado
    snapshot = producao(mundo)
    velho_e_bloco1 = slugs_do(mundo, "consenso.jsonl")

    llm.orc_class = 10                                  # o saldo acaba no bloco 2
    with pytest.raises(SystemExit, match="PARADO"):
        D.processar_bloco(["n3", "n4"])

    assert producao(mundo) == snapshot                  # byte a byte
    assert slugs_do(mundo, "consenso.jsonl") == velho_e_bloco1
    assert D.estado_consistente() == []
    # O que foi pago ficou registrado: exatamente as 10 chamadas que responderam.
    pagos = [r for n in (1, 2, 3)
             for r in _jsonl(mundo / "votacao-3" / f"passe_{n}.jsonl")
             if r["slug"] in ("n3", "n4")]
    assert len(pagos) == 10 and all(r["ok"] for r in pagos)


def test_o_resume_depois_do_deposito_nao_paga_duas_vezes(mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1", "n2"])
    llm.orc_class = 10
    with pytest.raises(SystemExit):
        D.processar_bloco(["n3", "n4"])

    S.limpar_parada_por_saldo()                         # o dono depositou
    llm.orc_class = None
    D.processar_bloco(["n3", "n4"])

    assert max(llm.classificacoes.values()) == 1        # nenhuma review em dobro
    assert sum(llm.classificacoes.values()) == 2 * 36   # 4 filmes × 6 × 3
    assert slugs_do(mundo, "consenso.jsonl") == {"velho", *NOVOS}
    assert D.estado_consistente() == []


# --- 1. interrupção: saldo no meio do verificador ----------------------------

def test_saldo_que_acaba_no_verificador_nao_commita_nem_o_consenso(
        mundo, monkeypatch):
    """Os passes do bloco terminaram (pagos, gravados), mas o commit é do
    bloco INTEIRO: sem o verificador, o consenso NÃO avança — `consenso` à
    frente do manifesto é o estado que quebra `montar_eixos` para os 99."""
    llm = LLM(orc_verif=1)
    instalar(monkeypatch, llm)
    antes = producao(mundo)

    with pytest.raises(SystemExit, match="PARADO"):
        D.processar_bloco(["n1"])

    assert producao(mundo) == antes
    assert "n1" not in slugs_do(mundo, "consenso.jsonl")
    assert D.estado_consistente() == []
    assert sum(llm.classificacoes.values()) == 18       # os 3 passes ficaram
    assert sum(llm.verificacoes.values()) == 1

    S.limpar_parada_por_saldo()
    llm.orc_verif = None
    D.processar_bloco(["n1"])
    assert sum(llm.classificacoes.values()) == 18       # passes NÃO refeitos
    assert sum(llm.verificacoes.values()) == 3          # 1 antes + 2 depois
    assert max(llm.verificacoes.values()) == 1
    assert "n1" in slugs_do(mundo, "consenso.jsonl")
    assert D.estado_consistente() == []


# --- 2. queda no commit -------------------------------------------------------

def _falhar_na_k_esima_escrita(monkeypatch, k: int):
    real, n = D.escrever_atomico, [0]

    def escreve(destino, conteudo, *a, **kw):
        n[0] += 1
        if n[0] == k:
            raise OSError(f"queda na escrita {k}")
        return real(destino, conteudo, *a, **kw)

    monkeypatch.setattr(D, "escrever_atomico", escreve)


def _todos_os_arquivos_sao_jsonl_inteiros(base: Path) -> None:
    for nome in ("consenso.jsonl", "consenso_verificado.jsonl"):
        texto = (base / "votacao-3" / nome).read_text(encoding="utf-8")
        assert texto.endswith("\n")
        for linha in texto.splitlines():
            json.loads(linha)
    json.loads((base / "votacao-3" / "verificador_manifesto.json").read_text())


def test_queda_ao_gravar_o_consenso_deixa_cada_arquivo_inteiro_e_o_consenso_antigo(
        mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    antes = producao(mundo)
    _falhar_na_k_esima_escrita(monkeypatch, 2)          # o consenso.jsonl

    with pytest.raises(OSError, match="queda na escrita 2"):
        D.processar_bloco(["n1"])

    _todos_os_arquivos_sao_jsonl_inteiros(mundo)
    depois = producao(mundo)
    assert depois["consenso.jsonl"] == antes["consenso.jsonl"]
    assert depois["verificador_manifesto.json"] == antes["verificador_manifesto.json"]
    # O verificado já avançou: a janela existe e é DETECTADA.
    assert depois["consenso_verificado.jsonl"] != antes["consenso_verificado.jsonl"]
    assert D.estado_consistente() != []


def test_reexecutar_o_bloco_apos_a_queda_fecha_o_estado_sem_gastar(
        mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    _falhar_na_k_esima_escrita(monkeypatch, 2)
    with pytest.raises(OSError):
        D.processar_bloco(["n1"])
    monkeypatch.setattr(D, "escrever_atomico", atomico.escrever_atomico)
    n = llm.n_total

    D.processar_bloco(["n1"])

    assert llm.n_total == n                             # zero chamadas novas
    assert "n1" in slugs_do(mundo, "consenso.jsonl")
    assert D.estado_consistente() == []


def test_queda_ao_gravar_o_manifesto_e_detectada_e_o_reparo_fecha_sem_gastar(
        mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    _falhar_na_k_esima_escrita(monkeypatch, 3)          # o manifesto
    with pytest.raises(OSError, match="queda na escrita 3"):
        D.processar_bloco(["n1"])

    _todos_os_arquivos_sao_jsonl_inteiros(mundo)
    problemas = D.estado_consistente()
    assert problemas and "manifesto registra" in problemas[0]

    n = llm.n_total
    monkeypatch.setattr(D, "escrever_atomico", atomico.escrever_atomico)
    assert D.reparar() == 0
    assert llm.n_total == n                             # o reparo NÃO gasta
    assert D.estado_consistente() == []


def test_o_driver_se_recusa_a_comecar_sobre_estado_inconsistente(
        mundo, monkeypatch, tmp_path, capsys):
    llm = LLM()
    instalar(monkeypatch, llm)
    manifesto = mundo / "votacao-3" / "verificador_manifesto.json"
    manifesto.write_text(json.dumps({"fonte_n_linhas": 3}), encoding="utf-8")
    antes = producao(mundo)

    rc = D.main([lista_de(tmp_path, ["n1"])])

    assert rc == 2 and llm.n_total == 0
    assert producao(mundo) == antes
    assert "ESTADO INCONSISTENTE" in capsys.readouterr().out


# --- estado_consistente -------------------------------------------------------

def test_estado_consistente_no_mundo_inicial_e_vazio(mundo):
    assert D.estado_consistente() == []


def test_sem_verificado_ou_sem_manifesto_nao_ha_o_que_cruzar(mundo):
    (mundo / "votacao-3" / "consenso_verificado.jsonl").unlink()
    assert D.estado_consistente() == []


def test_estado_consistente_detecta_verificado_com_outras_reviews(mundo):
    v = mundo / "votacao-3" / "consenso_verificado.jsonl"
    linhas = _jsonl(v)
    linhas[0] = {**linhas[0], "id": "outra-review"}
    _escrever_jsonl(v, linhas)
    [problema] = D.estado_consistente()
    assert "não as mesmas reviews" in problema


# --- interface: main ----------------------------------------------------------

def test_main_processa_todos_os_blocos_e_devolve_zero(mundo, monkeypatch,
                                                      tmp_path, capsys):
    instalar(monkeypatch, LLM())
    rc = D.main([lista_de(tmp_path, NOVOS), "--tamanho-bloco", "2"])
    saida = capsys.readouterr().out
    assert rc == 0
    assert "bloco 1/2" in saida and "bloco 2/2" in saida and "FIM: 2/2" in saida
    assert slugs_do(mundo, "consenso.jsonl") == {"velho", *NOVOS}


def test_main_dry_run_conta_as_chamadas_sem_chamar_nem_gravar(
        mundo, monkeypatch, tmp_path, capsys):
    llm = LLM()
    instalar(monkeypatch, llm)
    antes = producao(mundo)
    rc = D.main([lista_de(tmp_path, NOVOS), "--tamanho-bloco", "2", "--dry-run"])
    saida = capsys.readouterr().out
    assert rc == 0 and llm.n_total == 0
    assert producao(mundo) == antes
    assert "p1=12 p2=12 p3=12" in saida                 # 2 filmes × 6 reviews
    assert "TOTAL de chamadas de classificação pendentes: 72" in saida   # 4×6×3


def test_main_para_antes_do_bloco_quando_a_conta_nao_tem_credito(
        mundo, monkeypatch, tmp_path, capsys):
    llm = LLM()
    instalar(monkeypatch, llm)
    monkeypatch.setattr(D, "_saldo", lambda: {
        "is_available": False,
        "balance_infos": [{"total_balance": "-0.02"}]})
    antes = producao(mundo)
    rc = D.main([lista_de(tmp_path, NOVOS)])
    assert rc == 1 and llm.n_total == 0
    assert producao(mundo) == antes
    assert "PARADO antes do bloco" in capsys.readouterr().out


def test_main_devolve_1_e_diz_onde_parou_quando_o_saldo_acaba(
        mundo, monkeypatch, tmp_path, capsys):
    llm = LLM()
    instalar(monkeypatch, llm)
    llm.orc_class = 36 + 6 + 10        # bloco 1 inteiro + 10 chamadas do bloco 2
    rc = D.main([lista_de(tmp_path, NOVOS), "--tamanho-bloco", "2"])
    saida = capsys.readouterr().out
    assert rc == 1
    assert "PARADO no bloco 2/2" in saida
    assert "CONSISTENTE" in saida and "bloco 1 commitado" in saida
    assert slugs_do(mundo, "consenso.jsonl") == {"velho", "n1", "n2"}


def test_main_saldo_com_sonda_falha_segue_em_frente(mundo, monkeypatch,
                                                    tmp_path):
    """Sonda que falha não fecha o lote (mesma política do disjuntor)."""
    instalar(monkeypatch, LLM())
    monkeypatch.setattr(D, "_saldo", lambda: None)
    assert D.main([lista_de(tmp_path, ["n1"])]) == 0


# --- reviews que falham num passe --------------------------------------------

def test_review_que_falha_fica_fora_do_consenso_e_a_reexecucao_a_recupera(
        mundo, monkeypatch):
    llm = LLM(falha_em={("n1-r3", 2)})
    instalar(monkeypatch, llm)

    r = D.processar_bloco(["n1"])
    assert r["incompletas"] == 1
    ids = {l["id"] for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")}
    assert "n1-r3" not in ids and "n1-r2" in ids
    assert D.estado_consistente() == []

    llm.falha_em = set()
    r2 = D.processar_bloco(["n1"])
    assert r2["incompletas"] == 0
    ids = {l["id"] for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")}
    assert "n1-r3" in ids
    assert llm.classificacoes[("n1-r3", 2)] == 2        # a falha + a retentativa
    assert llm.classificacoes[("n1-r3", 1)] == 1        # o passe 1 NÃO refeito


# --- custo do bloco respeita a janela ----------------------------------------

def _com_ts(monkeypatch, iso: str) -> None:
    for modulo in (v3, vi, D):
        monkeypatch.setattr(modulo, "agora_utc_iso", lambda iso=iso: iso)


def test_o_custo_do_bloco_usa_o_preco_do_instante_da_chamada(
        tmp_path, monkeypatch):
    """Mesmas 21 chamadas (18 de classificação + 3 do verificador), duas
    janelas: sexta 08:00 UTC (pico) e sábado 08:00 UTC (fora de pico)."""
    sexta = "2026-09-18T08:00:00+00:00"
    sabado = "2026-09-19T08:00:00+00:00"
    por_janela = {}
    for nome, ts in (("sexta", sexta), ("sabado", sabado)):
        base = criar_mundo(tmp_path / nome, monkeypatch)
        instalar(monkeypatch, LLM())
        _com_ts(monkeypatch, ts)
        por_janela[nome] = D.processar_bloco(["n1"])["custo"]

    um = custo_usd(USO, datetime(2026, 9, 18, 8, tzinfo=timezone.utc))
    assert por_janela["sexta"]["n_chamadas"] == 21
    assert por_janela["sexta"]["total"] == pytest.approx(21 * um)
    assert por_janela["sexta"]["fora_de_pico"] == 0
    assert por_janela["sabado"]["total"] == pytest.approx(21 * um / 2)
    assert por_janela["sabado"]["pico"] == 0
    assert por_janela["sexta"]["total"] == pytest.approx(
        2 * por_janela["sabado"]["total"])


def test_o_manifesto_registra_a_tabela_de_preco_e_quantas_chamadas_sem_horario(
        mundo, monkeypatch):
    instalar(monkeypatch, LLM())
    D.processar_bloco(["n1"])
    m = json.loads((mundo / "votacao-3" / "verificador_manifesto.json").read_text())
    assert m["tabela_de_preco"] == {"modelo": "DeepSeek-V4.1-Flash",
                                    "vigente_desde": "2026-09-10",
                                    "verificada_em": "2026-09-18"}
    # `velho` tem `ts`; nenhum registro do mundo é anterior ao campo.
    assert m["custo_n_sem_horario"] == 0
    assert m["custo_usd"] > 0


# --- pedaços do desenho -------------------------------------------------------

def test_classificar_passe_restrito_a_slugs_so_toca_esses_filmes(
        mundo, monkeypatch):
    llm = LLM()
    instalar(monkeypatch, llm)
    v3.classificar_passe(1, slugs=["n2"])
    assert {rid.split("-r")[0] for rid, _ in llm.classificacoes} == {"n2"}
    assert len(v3.pendentes_do_passe(1, ["n2"])[2]) == 0
    assert len(v3.pendentes_do_passe(1, ["n3"])[2]) == N_REVIEWS
    assert len(v3.pendentes_do_passe(1)[2]) == 3 * N_REVIEWS   # n1, n3, n4


def test_calcular_aplicacao_com_lista_vazia_nao_chama_ninguem(mundo, monkeypatch):
    """`slugs=[]` é "nenhuma chamada" (o reparo), não "todas": a regressão
    seria o reparo gastar dinheiro."""
    llm = LLM()
    instalar(monkeypatch, llm)
    D.processar_bloco(["n1"])
    n = llm.n_total
    linhas = _jsonl(mundo / "votacao-3" / "consenso.jsonl")
    vi.calcular_aplicacao(linhas, slugs=[])
    assert llm.n_total == n


def test_consenso_incremental_preserva_as_linhas_de_fora_do_bloco_byte_a_byte(
        mundo):
    """Uma linha do consenso com campo que a votação de hoje não produz (o
    caso de uma linha antiga, de outra versão) passa INTACTA."""
    arq = mundo / "votacao-3" / "consenso.jsonl"
    linhas = _jsonl(arq)
    linhas[0] = {**linhas[0], "campo_de_outra_versao": {"a": [1, 2]}}
    passes = [v3._ler_passe(n) for n in (1, 2, 3)]
    amostra = json.loads((mundo / "votacao-3" / "amostra.json").read_text())
    novas, n_inc = v3.consenso_incremental(linhas, passes, amostra, ["n1"])
    assert novas == linhas                 # n1 sem passes: nada entra, nada some
    assert n_inc == N_REVIEWS


def test_a_ordem_da_saida_e_a_do_cmd_consenso_original(mundo, monkeypatch):
    instalar(monkeypatch, LLM())
    D.processar_bloco(["n3"])
    D.processar_bloco(["n1"])              # fora de ordem alfabética de propósito
    chaves = [(l["slug"], l["bucket"], l["id"])
              for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")]
    assert chaves == sorted(chaves)
