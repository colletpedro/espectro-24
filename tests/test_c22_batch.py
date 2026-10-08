"""[2026-09-22, C22] Orquestrador do batch Gemini dos 55 — ponta a ponta, falso.

Zero rede: o batch (`gemini_batch_submeter/estado/resultados`) e a chamada
síncrona (`resposta_json_gemini`) são substituídos. O mundo é o de
`test_lote_em_blocos` (`velho` = os 99 publicados), com dois filmes dos 55.

O que se prova:
1. o fluxo p12 → p3 → verificador → commit leva os blocos ao consenso, com
   os registros marcados (`excecao`, provider, modelo efetivo, finish_reason);
2. o passe 3 só pede as reviews em que 1 e 2 divergem, e as outras entram no
   consenso com `passe_3_dispensado`;
3. o verificador só pede as candidatas (com `impacto_emocional`);
4. `velho` passa byte a byte;
5. resposta inválida do batch vira `ok: False` e o commit a retenta síncrona;
6. o teto barra a submissão; a coleta é idempotente.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))

import c22_batch as B  # noqa: E402
import excecao_gemini_c22 as C22  # noqa: E402
import lote_em_blocos as D  # noqa: E402
import verificador_impacto as vi  # noqa: E402
import votacao_3 as v3  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from test_lote_em_blocos import (  # noqa: E402
    ATUACAO,
    IMPACTO,
    _idx,
    _jsonl,
    criar_mundo,
)

NOVOS = sorted(C22.SLUGS)[:2]
USO = {"prompt_tokens": 1000, "completion_tokens": 40,
       "cache_hit_tokens": 0, "cache_miss_tokens": 1000}


def voto(rid: str, passe: int) -> list[str]:
    """Índice par: passes 1 e 2 IGUAIS (passe 3 dispensável). Ímpar: 1 e 2
    divergem, e o 3 desempata a favor do passe 1."""
    i = _idx(rid)
    if i % 2 == 0:
        return [IMPACTO, ATUACAO]
    return [ATUACAO] if passe in (1, 3) else [ATUACAO, IMPACTO]


def _resp(texto: str) -> dict:
    return {"texto": texto, "provider": "gemini", "modelo": "gemini-3.7-flash",
            "modelo_efetivo": "gemini-3.7-flash", "uso": dict(USO),
            "thinking_tokens": 10, "finish_reason": "STOP", "camada": "batch",
            "motivo_camada": None, "traffic_type": "SERVICE_TIER_STANDARD",
            "fallback_conteudo": None, "latencia_s": None}


class Batch:
    def __init__(self, invalido: set[str] = frozenset()):
        self.jobs: dict[str, list] = {}
        self.invalido = invalido
        self.sincronas = 0

    def submeter(self, pedidos, nome, dir_trabalho):
        nome_job = f"batches/{len(self.jobs)}"
        self.jobs[nome_job] = pedidos
        return nome_job

    def estado(self, nome):
        return {"nome": nome, "estado": "JOB_STATE_SUCCEEDED", "criado": "c",
                "inicio": None, "fim": "f", "arquivo_saida": "x", "erro": None}

    def resultados(self, nome):
        saida = {}
        for chave, system, user in self.jobs[nome]:
            slug, bucket, rid, passe = chave.split("|")
            if chave in self.invalido:
                saida[chave] = _resp("{isto não é json")
            elif passe == "V2":
                saida[chave] = _resp(json.dumps(
                    {"confirma": _idx(rid) % 4 != 0, "frase": "f",
                     "alvo": "espectador"}))
            else:
                saida[chave] = _resp(json.dumps(
                    {"eixos": voto(rid, int(passe)), "temas_livres": []}))
        return saida

    def sincrona(self, system, user, *, estagio, camada=None):
        self.sincronas += 1
        if estagio == "verificador":
            return {**_resp(json.dumps({"confirma": True, "frase": "f"})),
                    "camada": "padrao"}
        return {**_resp(json.dumps({"eixos": [ATUACAO], "temas_livres": []})),
                "camada": "padrao"}


@pytest.fixture
def mundo(tmp_path, monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)
    monkeypatch.setattr(D, "registrar_bloco", lambda bloco: (0, []))
    base = criar_mundo(tmp_path / "mundo", monkeypatch, novos=tuple(NOVOS))
    lista = tmp_path / "lista.txt"
    lista.write_text("\n".join(NOVOS) + "\n", encoding="utf-8")
    monkeypatch.setattr(B, "LISTA", lista)
    monkeypatch.setattr(B, "TAMANHO_BLOCO", 1)
    monkeypatch.setattr(B, "ARQ_JOBS", base / "votacao-3" / "c22_batch_jobs.json")
    monkeypatch.setattr(B, "DIR_BATCH", base / "votacao-3" / "_c22_batch")
    monkeypatch.setattr(B, "ARQ_IMPACTO", base / "votacao-3" / "recusas_impacto.json")
    # a medida pós-commit lê o consenso REAL (`proveniencia_classificacao`);
    # aqui ela é observada, não exercitada — o mundo é outro
    import proveniencia_classificacao as PC
    monkeypatch.setattr(PC, "impacto_das_recusas",
                        lambda s: {"slug": s, "estado": "medida isolada no teste"})
    return base


def instalar(monkeypatch, batch: Batch) -> None:
    monkeypatch.setattr(S, "gemini_batch_submeter", batch.submeter)
    monkeypatch.setattr(S, "gemini_batch_estado", batch.estado)
    monkeypatch.setattr(S, "gemini_batch_resultados", batch.resultados)
    monkeypatch.setattr(v3, "resposta_json_gemini", batch.sincrona)
    monkeypatch.setattr(vi, "resposta_json_gemini", batch.sincrona)


def _ate_o_fim(teto=100.0, max_tiques=10) -> int:
    for n in range(1, max_tiques + 1):
        if B.avancar(teto):
            return n
    raise AssertionError("não terminou")


def test_o_fluxo_leva_os_dois_filmes_ao_consenso_marcado(mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)
    velho_antes = [l for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")
                   if l["slug"] == "velho"]
    _ate_o_fim()
    consenso = _jsonl(mundo / "votacao-3" / "consenso.jsonl")
    assert [l for l in consenso if l["slug"] == "velho"] == velho_antes
    novos = [l for l in consenso if l["slug"] in NOVOS]
    assert len(novos) == 12
    assert all(l["classificacao_excecao"]["provider"] == "gemini" for l in novos)
    assert all(l["classificacao_excecao"]["camadas"] == ["batch"] for l in novos)
    for l in novos:
        par = _idx(l["id"]) % 2 == 0
        assert l.get("passe_3_dispensado", False) is par
        assert l["eixos"] == sorted(voto(l["id"], 1))
    assert D.estado_consistente() == []
    for n in (1, 2, 3):
        regs = [r for r in _jsonl(mundo / "votacao-3" / f"passe_{n}.jsonl")
                if r["slug"] in NOVOS]
        assert regs and all(r["excecao"] == C22.EXCECAO
                            and r["modelo_efetivo"] == "gemini-3.7-flash"
                            and r["finish_reason"] == "STOP" for r in regs)
    assert batch.sincronas == 0


def test_o_passe_3_so_pede_as_divergentes_e_o_verificador_so_as_candidatas(
        mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)
    _ate_o_fim()
    jobs = B.ler_jobs()["jobs"]
    pedidos = {(j["bloco"], j["etapa"]): batch.jobs[j["job"]]
               for j in jobs if j["job"]}
    for bloco in (1, 2):
        assert len(pedidos[(bloco, "p12")]) == 12            # 6 reviews × 2
        p3 = [c.split("|")[2] for c, _, _ in pedidos[(bloco, "p3")]]
        assert p3 and all(_idx(r) % 2 == 1 for r in p3)      # só as ímpares
        v2 = [c.split("|")[2] for c, _, _ in pedidos[(bloco, "verificador")]]
        assert v2 and all(_idx(r) % 2 == 0 for r in v2)      # só com impacto


def test_resposta_invalida_do_batch_vira_falha_e_o_commit_a_retenta(
        mundo, monkeypatch):
    alvo = f"{NOVOS[0]}|medianas|{NOVOS[0]}-r1|1"
    batch = Batch(invalido={alvo})
    instalar(monkeypatch, batch)
    _ate_o_fim()
    regs = [r for r in _jsonl(mundo / "votacao-3" / "passe_1.jsonl")
            if r.get("id") == f"{NOVOS[0]}-r1"]
    assert regs[0]["ok"] is False and regs[0]["resposta_crua"] == "{isto não é json"
    assert regs[0]["excecao"] == C22.EXCECAO
    assert regs[-1]["ok"] is True and regs[-1]["camada"] == "padrao"
    assert batch.sincronas == 1


def test_o_teto_barra_a_submissao(mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)
    assert B.avancar(teto=0.0) is False
    assert batch.jobs == {}
    assert B.ler_jobs()["jobs"] == []


def test_coletar_duas_vezes_nao_duplica(mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)
    B.avancar(100.0)                         # submete p12 dos dois blocos
    estado = B.ler_jobs()
    j = estado["jobs"][0]
    B.coletar(estado, j, [NOVOS[0]])
    j["coletado"] = None
    B.coletar(estado, j, [NOVOS[0]])
    regs = [r for r in _jsonl(mundo / "votacao-3" / "passe_1.jsonl")
            if r["slug"] == NOVOS[0]]
    assert len(regs) == 6


def test_a_excecao_recusa_rodar_com_votos_deepseek_dos_55_nos_passes(
        mundo, monkeypatch):
    instalar(monkeypatch, Batch())
    arq = mundo / "votacao-3" / "passe_1.jsonl"
    with arq.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ok": True, "slug": NOVOS[0], "bucket": "negativas",
                            "id": f"{NOVOS[0]}-r0", "eixos": [ATUACAO],
                            "passe": 1}) + "\n")
    with pytest.raises(v3.ProviderMisturadoNoVoto):
        B.avancar(100.0)


def test_so_blocos_restringe_e_nao_toca_os_outros(mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)
    for _ in range(6):
        if B.avancar(100.0, so_blocos={1}):
            break
    jobs = B.ler_jobs()["jobs"]
    assert {j["bloco"] for j in jobs} == {1}
    assert any(j["etapa"] == "commit" for j in jobs)
    consenso = _jsonl(mundo / "votacao-3" / "consenso.jsonl")
    assert {l["slug"] for l in consenso} == {"velho", NOVOS[0]}


def test_bloqueio_de_conteudo_do_gemini_e_nomeado_no_registro():
    """Medido no bloco 1 (2026-09-23): 9 reviews com `PROHIBITED_CONTENT`,
    sem candidato nem texto. O registro diz o motivo, não `JSONDecodeError`."""
    review = {"slug": NOVOS[0], "perfil": "x", "bucket": "negativas",
              "id": "r", "nivel": 2.0, "n_chars": 10, "texto": "t"}
    resp = {**_resp(""), "bloqueio": "PROHIBITED_CONTENT", "finish_reason": None}
    reg = v3.registro_excecao(review, 1, "tid", resp)
    assert reg["ok"] is False
    assert reg["erro"].startswith("BloqueioDeConteudoGemini: PROHIBITED_CONTENT")
    assert reg["bloqueio"] == "PROHIBITED_CONTENT" and reg["excecao"] == C22.EXCECAO
    reg_v = vi.registro_excecao("V2_alvo", 1, review, resp)
    assert reg_v["erro"].startswith("BloqueioDeConteudoGemini")


def test_recusa_no_batch_e_substituida_e_o_passe_3_nao_a_pede(mundo, monkeypatch):
    """Um pedido bloqueado nos passes 1 e 2 do batch vira recusa registrada
    logo após a coleta; o passe 3 não o pede; o commit classifica a
    substituta (síncrono) e o bloco fecha sem incompleta."""
    from espectro24 import pipeline as PL
    from espectro24 import recusas

    alvo_id = f"{NOVOS[0]}-r1"
    substituta = f"{NOVOS[0]}-r9"

    class BatchComBloqueio(Batch):
        def resultados(self, nome):
            saida = super().resultados(nome)
            for chave in saida:
                if chave.split("|")[2] == alvo_id:
                    saida[chave] = {**_resp(""), "bloqueio": "PROHIBITED_CONTENT",
                                    "finish_reason": None}
            return saida

    batch = BatchComBloqueio()
    instalar(monkeypatch, batch)

    amostra_arq = mundo / "votacao-3" / "amostra.json"

    def selecao_falsa(slug, coleta=None, **kw):
        a = json.loads(amostra_arq.read_text(encoding="utf-8"))
        ids = {r["id"] for r in a["reviews"] if r["slug"] == slug}
        ids -= set(recusas.ids_recusados(slug))
        if slug == NOVOS[0] and alvo_id in recusas.ids_recusados(slug):
            ids.add(substituta)
        return {"medianas": ids}
    monkeypatch.setattr(PL, "ids_analisados_do_bruto", selecao_falsa)

    def registrar_falso(bloco):
        # o registro de verdade lê o bruto; aqui a substituta entra na amostra
        a = json.loads(amostra_arq.read_text(encoding="utf-8"))
        if (alvo_id in recusas.ids_recusados(NOVOS[0])
                and not any(r["id"] == substituta for r in a["reviews"])):
            a["reviews"].append({"slug": NOVOS[0], "perfil": "x",
                                 "bucket": "medianas", "id": substituta,
                                 "nivel": 3.0, "n_chars": 20, "texto": "sub"})
            amostra_arq.write_text(json.dumps(a), encoding="utf-8")
        return (0, [])
    monkeypatch.setattr(D, "registrar_bloco", registrar_falso)

    _ate_o_fim()
    [rec] = recusas.recusas()
    assert rec["id"] == alvo_id and rec["bloqueio"] == "PROHIBITED_CONTENT"
    assert rec["substituta"] == substituta
    jobs = B.ler_jobs()["jobs"]
    p3 = next(j for j in jobs if j["bloco"] == 1 and j["etapa"] == "p3")
    assert alvo_id not in {c.split("|")[2] for c, _, _ in batch.jobs[p3["job"]]}
    commit = next(j for j in jobs if j["bloco"] == 1 and j["etapa"] == "commit")
    assert commit["resumo"]["incompletas"] == 0
    consenso = {l["id"] for l in _jsonl(mundo / "votacao-3" / "consenso.jsonl")}
    assert substituta in consenso and alvo_id not in consenso


def test_teto_a_preco_cheio_barra_o_que_o_de_batch_deixaria_passar(mundo, monkeypatch):
    """[C22 (e)] O billing não pôde ser conferido: a preço cheio o mesmo teto
    barra a submissão que, com o desconto suposto, passaria."""
    batch = Batch()
    instalar(monkeypatch, batch)
    ped = B.pedidos_passes([NOVOS[0]], (1, 2))
    c_desc = B.custo_estimado([p[3]["n_chars"] for p in ped])
    teto = c_desc * 1.5
    monkeypatch.setitem(B.TETO, "preco_cheio", True)
    assert B.submeter(B.ler_jobs(), 1, "p12", ped, teto) is False
    monkeypatch.setitem(B.TETO, "preco_cheio", False)
    assert B.submeter(B.ler_jobs(), 1, "p12", ped, teto) is True
    [j] = B.ler_jobs()["jobs"]
    assert j["custo_estimado_cheio"] == pytest.approx(2 * j["custo_estimado"], rel=1e-3)


def test_reserva_esgotada_para_a_execucao(mundo, monkeypatch):
    from espectro24 import recusas
    recusas.registrar([{"slug": NOVOS[0], "bucket": "medianas", "id": "x",
                        "provider": "gemini", "modelo": "m",
                        "bloqueio": "PROHIBITED_CONTENT",
                        "n_tentativas_bloqueadas": 2, "evidencia": "t"}])
    recusas.anotar_substitutas(NOVOS[0], {"medianas": {"x"}}, {"medianas": set()})
    with pytest.raises(B.ReservaEsgotada):
        B._parar_se_reserva_esgotada([NOVOS[0]])
    B._parar_se_reserva_esgotada([NOVOS[1]])


def test_429_na_criacao_nao_derruba_e_tenta_de_novo(mundo, monkeypatch):
    """[2026-09-23] Cota do Tier 1 (tokens enfileirados / gasto por janela):
    nada é criado, o tique segue, e o próximo tenta de novo."""
    batch = Batch()
    instalar(monkeypatch, batch)
    chamadas = {"n": 0}
    original = batch.submeter

    def com_429(pedidos, nome, dir_trabalho):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            e = RuntimeError("429 RESOURCE_EXHAUSTED")
            e.code = 429
            raise e
        return original(pedidos, nome, dir_trabalho)
    monkeypatch.setattr(S, "gemini_batch_submeter", com_429)
    ped = B.pedidos_passes([NOVOS[0]], (1, 2))
    estado = B.ler_jobs()
    assert B.submeter(estado, 1, "p12", ped, 100.0) is False
    assert B.ler_jobs()["n_429"] == 1 and B.ler_jobs()["jobs"] == []
    assert B.submeter(B.ler_jobs(), 1, "p12", ped, 100.0) is True
    assert "primeiro_429" not in B.ler_jobs()


def test_429_com_job_nosso_na_fila_nao_conta_como_cota_travada(mundo, monkeypatch):
    batch = Batch()
    instalar(monkeypatch, batch)

    def sempre_429(pedidos, nome, dir_trabalho):
        e = RuntimeError("429")
        e.code = 429
        raise e
    estado = B.ler_jobs()
    estado["jobs"].append({"bloco": 9, "etapa": "p12", "job": "batches/x", "n": 1,
                           "estado": "JOB_STATE_RUNNING", "coletado": None,
                           "custo_estimado": 0.0})
    B.gravar_jobs(estado)
    monkeypatch.setattr(S, "gemini_batch_submeter", sempre_429)
    ped = B.pedidos_passes([NOVOS[0]], (1, 2))
    monkeypatch.setattr(B, "MAX_ESPERA_429_S", -1)       # estouraria na hora
    assert B.submeter(B.ler_jobs(), 1, "p12", ped, 100.0) is False
    assert "primeiro_429" not in B.ler_jobs()


def test_falha_na_medida_pos_commit_nao_derruba_o_laco(mundo, monkeypatch):
    import proveniencia_classificacao as PC
    from espectro24 import recusas

    def explode(slug):
        raise RuntimeError("amostra diverge")
    monkeypatch.setattr(PC, "impacto_das_recusas", explode)
    recusas.registrar([{"slug": NOVOS[0], "bucket": "medianas", "id": "x",
                        "provider": "gemini", "modelo": "m",
                        "bloqueio": "PROHIBITED_CONTENT",
                        "n_tentativas_bloqueadas": 2, "evidencia": "t"}])
    [m] = B.medir_impacto_das_recusas([NOVOS[0]], {})
    assert m["estado"].startswith("indeterminado: a medida falhou")


@pytest.mark.parametrize("antes,agora,aceita", [
    (38, 37, True),     # abaixo de 40 antes, queda 1, n ≥ 10
    (39, 37, True),     # queda 2: ainda aceita
    (39, 36, False),    # queda 3
    (40, 39, False),    # estava em 40: a reserva esgotou PELO filtro
    (11, 9, False),     # n resultante abaixo de 10
])
def test_regra_fixa_de_aceite_automatico(mundo, monkeypatch, antes, agora, aceita):
    """[2026-09-27] As três condições do dono, e a declaração que o aceite deixa."""
    from espectro24 import pipeline as PL
    from espectro24 import recusas
    recusas.registrar([{"slug": NOVOS[0], "bucket": "medianas", "id": "x",
                        "provider": "gemini", "modelo": "m",
                        "bloqueio": "PROHIBITED_CONTENT",
                        "n_tentativas_bloqueadas": 2, "evidencia": "t",
                        "idioma": "az"}])
    recusas.anotar_substitutas(NOVOS[0], {"medianas": {"x"}}, {"medianas": set()})

    def selecao(slug, coleta=None, ignorar_recusas=False, **kw):
        n = antes if ignorar_recusas else agora
        return {"medianas": {f"r{i}" for i in range(n)}}
    monkeypatch.setattr(PL, "ids_analisados_do_bruto", selecao)
    estado = B.ler_jobs()
    feitos = B.aplicar_regra_de_aceite([NOVOS[0]], estado)
    assert bool(feitos) is aceita
    if aceita:
        assert recusas.reservas_esgotadas([NOVOS[0]]) == []
        assert B.ler_jobs()["aceites_automaticos"][0]["queda"] == antes - agora
        dec = recusas.declaracao_do_bucket(NOVOS[0], "medianas")
        assert dec["sem_substituta"][0]["aceite_do_dono"].startswith("ACEITE AUTOMÁTICO")
    else:
        with pytest.raises(B.ReservaEsgotada):
            B._parar_se_reserva_esgotada([NOVOS[0]])


class _Erro402(Exception):
    code = 402

    def __str__(self):
        return "402 RESOURCE_EXHAUSTED. Your prepayment credits are depleted."


def test_402_do_gemini_no_commit_nao_grava_nem_commita(mundo, monkeypatch):
    """[2026-09-27] Crédito pré-pago esgotado: as substitutas do bloco 4 viraram
    `ok: False` e o bloco foi commitado com incompletas. Agora: nenhuma
    review vira registro, o passe ABORTA e os três arquivos ficam intactos."""
    from test_lote_em_blocos import producao
    batch = Batch()
    instalar(monkeypatch, batch)

    def sincrona_402(system, user, *, estagio, camada=None):
        raise S._abrir_disjuntor_de_saldo_gemini(_Erro402())
    monkeypatch.setattr(v3, "resposta_json_gemini", sincrona_402)
    antes = producao(mundo)
    n_antes = len(_jsonl(mundo / "votacao-3" / "passe_1.jsonl"))
    with pytest.raises(SystemExit) as e:
        D.processar_bloco([NOVOS[0]], excecao=True)
    assert "Gemini" in str(e.value)
    assert producao(mundo) == antes
    assert len(_jsonl(mundo / "votacao-3" / "passe_1.jsonl")) == n_antes
    S.limpar_parada_por_saldo()


def test_402_na_submissao_para_o_orquestrador_com_codigo_5(mundo, monkeypatch, capsys):
    batch = Batch()
    instalar(monkeypatch, batch)

    def submeter_402(pedidos, nome, dir_trabalho):
        raise S._abrir_disjuntor_de_saldo_gemini(_Erro402())
    monkeypatch.setattr(S, "gemini_batch_submeter", submeter_402)
    assert B.main(["avancar", "--teto-usd", "100"]) == 5
    assert "saldo do Gemini esgotado" in capsys.readouterr().out
    assert B.ler_jobs()["jobs"] == []
    S.limpar_parada_por_saldo()


def test_o_402_do_gemini_e_reconhecido_pelo_code_e_pela_mensagem():
    assert S._saldo_gemini_esgotado(_Erro402())
    assert not S._saldo_gemini_esgotado(RuntimeError("429 quota"))
