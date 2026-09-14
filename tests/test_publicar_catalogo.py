"""[v1.9.16, Entrega 4] `_ja_publicado` — o critério de resume do lote de
publicação: um filme conta como PUBLICADO sob a versão corrente só se o
`spec_version` bate E o verificador foi aplicado. Sem os dois, o resume
pularia um filme publicado sob uma versão antiga (ex.: `oppenheimer-2023`,
`spec_version 1.1.1`) como se estivesse em dia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))


def _pc():
    import publicar_catalogo
    return publicar_catalogo


def test_ausente_nao_e_publicado(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    assert pc._ja_publicado("nao-existe") is False


def test_json_de_versao_antiga_nao_conta(tmp_path, monkeypatch):
    """O caso real: `oppenheimer-2023.json` existe, mas é `spec_version
    1.1.1` — pré-eixos, pré-verificador. Resume tem que tratar como
    pendente, não como feito."""
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    (tmp_path / "oppenheimer-2023.json").write_text(
        json.dumps({"slug": "oppenheimer-2023", "spec_version": "1.1.1"}),
        encoding="utf-8")
    assert pc._ja_publicado("oppenheimer-2023") is False


def test_versao_atual_sem_eixos_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9"}), encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_versao_atual_com_eixos_mas_sem_verificador_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9",
                    "eixos": {"contraste": "tematico"}}), encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_versao_atual_com_verificador_aplicado_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    (tmp_path / "x.json").write_text(
        json.dumps({"slug": "x", "spec_version": "9.9.9",
                    "eixos": {"contraste": "tematico",
                              "verificador": {"aplicado": True}}}),
        encoding="utf-8")
    assert pc._ja_publicado("x") is True


def test_json_corrompido_nao_conta(tmp_path, monkeypatch):
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    (tmp_path / "x.json").write_text("{ nao é json", encoding="utf-8")
    assert pc._ja_publicado("x") is False


def test_filmes_padrao_sao_o_catalogo_menos_os_ja_publicados():
    """A lista default é o catálogo (`consenso.jsonl`) menos os já publicados
    sob o pipeline corrente (`JA_PUBLICADOS_ANTES`).

    [piloto de expansão, 2026-09] **Deixou de fixar `32`.** A expansão faz
    esse número crescer por construção. O que continua travado — e é o que
    "uma mudança silenciosa no catálogo aparece como falha" realmente
    precisa provar — é a RELAÇÃO: `filmes_pendentes()` é exatamente o
    catálogo declarado em `consenso.jsonl` menos `JA_PUBLICADOS_ANTES`, nem
    um filme a mais nem a menos. O catálogo é lido AQUI de novo,
    independente de `pc.catalogo_completo()`, para que o teste prove que
    aquela função lê o arquivo certo — não só que ela concorda consigo
    mesma."""
    import json
    pc = _pc()
    caminho = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"
    if not caminho.exists():
        import pytest
        pytest.skip("consenso.jsonl indisponível")
    do_catalogo = {json.loads(l)["slug"] for l in
                   caminho.read_text(encoding="utf-8").splitlines() if l.strip()}
    faltantes = pc.filmes_pendentes()
    assert set(faltantes) == do_catalogo - pc.JA_PUBLICADOS_ANTES
    assert len(faltantes) == len(set(faltantes)), "filmes_pendentes duplicou slug"
    assert "oppenheimer-2023" in faltantes
    assert "cure" not in faltantes


# ===========================================================================
# [v1.9.21] Recusa de republicação em MASSA — o footgun que a v1.9.21 abre
# ===========================================================================
# `cmd_publicar` pula quem `_ja_publicado`, e `_ja_publicado` exige
# `spec_version == SPEC_VERSION`. Enquanto a constante ficou em `1.9.16`, os
# 32 slugs default eram todos pulados e rodar o script sem argumento era
# inócuo. Com `SPEC_VERSION` em `1.9.21` e os 35 JSONs em `1.9.16`, NENHUM é
# pulado: um comando de uma linha dispara re-scrape de 32 filmes a 2s por
# requisição sem paralelismo, e apaga o histórico `passadas` do `meta.json`
# (dívida conhecida, `DIAGNOSTICO_OFFLINE.md`) — caro e irreversível.
#
# O mínimo que fecha: recusar acima de um lote pequeno, exigindo flag
# explícita. NÃO mexe no checkpoint em si nem na dívida do `passadas`.

import pytest  # noqa: E402


def _resultado_com(tmp_path, monkeypatch, publicados: int, pendentes: int):
    """Monta um `resultado/` de mentira: `publicados` filmes em dia sob a
    versão corrente, `pendentes` sob uma versão antiga."""
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "SPEC_VERSION", "9.9.9")
    slugs = []
    for i in range(publicados):
        s = f"em-dia-{i}"
        (tmp_path / f"{s}.json").write_text(json.dumps(
            {"slug": s, "spec_version": "9.9.9",
             "eixos": {"verificador": {"aplicado": True}}}), encoding="utf-8")
        slugs.append(s)
    for i in range(pendentes):
        s = f"atrasado-{i}"
        (tmp_path / f"{s}.json").write_text(json.dumps(
            {"slug": s, "spec_version": "1.0.0",
             "eixos": {"verificador": {"aplicado": True}}}), encoding="utf-8")
        slugs.append(s)
    return pc, slugs


def test_o_limite_e_pequeno_e_declarado():
    """O limiar é decisão de produto, não número mágico: acima de um punhado
    de filmes o comando deixa de ser "conserta um caso" e vira "republica o
    catálogo", e a diferença de custo entre os dois é de horas de rede."""
    pc = _pc()
    assert pc.LIMITE_LOTE_SEM_CONFIRMACAO == 5


def test_lote_pequeno_passa_sem_flag(tmp_path, monkeypatch):
    pc, slugs = _resultado_com(tmp_path, monkeypatch, publicados=30, pendentes=5)
    pc.checar_tamanho_do_lote(slugs, republicar_tudo=False)   # não levanta


def test_lote_grande_e_RECUSADO_sem_a_flag(tmp_path, monkeypatch):
    pc, slugs = _resultado_com(tmp_path, monkeypatch, publicados=3, pendentes=32)
    with pytest.raises(SystemExit) as e:
        pc.checar_tamanho_do_lote(slugs, republicar_tudo=False)
    msg = str(e.value)
    # a mensagem tem de dizer QUANTOS e POR QUÊ — um "recusado" seco manda o
    # leitor caçar a causa no código
    assert "32" in msg
    assert "9.9.9" in msg
    assert "--republicar-tudo" in msg


def test_a_flag_explicita_libera(tmp_path, monkeypatch):
    pc, slugs = _resultado_com(tmp_path, monkeypatch, publicados=3, pendentes=32)
    pc.checar_tamanho_do_lote(slugs, republicar_tudo=True)    # não levanta


def test_a_contagem_ignora_quem_ja_esta_em_dia(tmp_path, monkeypatch):
    """O que importa é quantos SERIAM republicados, não o tamanho da lista:
    passar os 35 slugs com 32 em dia é um lote de 3, e tem de passar."""
    pc, slugs = _resultado_com(tmp_path, monkeypatch, publicados=32, pendentes=3)
    assert len(slugs) == 35
    pc.checar_tamanho_do_lote(slugs, republicar_tudo=False)   # não levanta


def test_a_guarda_roda_dentro_de_cmd_publicar(tmp_path, monkeypatch):
    """Sem isto, a função existiria e ninguém a chamaria — o modo de falha
    clássico de guard-rail que não detecta nada."""
    pc, slugs = _resultado_com(tmp_path, monkeypatch, publicados=0, pendentes=32)
    monkeypatch.setattr(pc, "publicar_um", lambda slug: pytest.fail(
        f"publicou {slug} apesar da guarda"))
    with pytest.raises(SystemExit):
        pc.cmd_publicar(slugs)


# ===========================================================================
# [piloto de expansão, `ABERTO.md` C14.8] A amostra não muda entre
# classificação e publicação — (A) `--offline`, (B) recusa antes do CLI
# ===========================================================================

def test_publicar_um_roda_o_cli_em_offline(tmp_path, monkeypatch):
    """(A) Sem `--offline`, toda publicação recoletava da rede — foi assim que
    `get-out-2017` ganhou uma review não classificada na amostra."""
    import subprocess
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    visto = {}

    def fake_run(argv, **kw):
        visto["argv"] = argv
        return subprocess.CompletedProcess(argv, 0, "", "")
    monkeypatch.setattr(pc.subprocess, "run", fake_run)
    pc.publicar_um("get-out-2017")
    assert visto["argv"][-5:] == ["--slug", "get-out-2017", "--tom", "ambos",
                                  "--offline"]


def _classificacao_de_40(monkeypatch, analisadas_positivas):
    """Classificação de produção com 40 nas positivas; o bruto, lido por
    `ids_analisados_do_bruto`, devolve `analisadas_positivas`."""
    from espectro24 import pipeline as P
    classificadas = {f"viewing:{i}": [] for i in range(40)}
    monkeypatch.setattr(P, "_carregar_consenso_producao", lambda E: (
        {"get-out-2017": {"positivas": classificadas}}, {"aplicado": True}))
    monkeypatch.setattr(P, "ids_analisados_do_bruto",
                        lambda slug, **k: {"positivas": set(analisadas_positivas)})
    return list(classificadas)


def test_amostra_divergente_e_RECUSADA_antes_do_cli(tmp_path, monkeypatch):
    """(B) O caso `get-out-2017` no harness: classificada com 40; o bruto
    passou a ter 41 candidatas e a seleção ficou com a nova. O filme é
    recusado ANTES do subprocesso — nenhuma chamada paga —, a recusa vai para
    o log, e o lote segue (falha isolada por filme, como o resto do harness)."""
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "LOG_DIR", tmp_path)
    monkeypatch.setattr(pc, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(pc, "RAIZ", tmp_path)   # o resumo imprime LOG relativo à raiz
    classificadas = _classificacao_de_40(monkeypatch, [])
    candidatas = classificadas + ["viewing:1493797951"]            # 41
    _classificacao_de_40(monkeypatch, candidatas[:39] + candidatas[40:])
    monkeypatch.setattr(pc, "publicar_um", lambda slug: pytest.fail(
        f"{slug} chegou ao CLI com a amostra divergente"))

    pc.cmd_publicar(["get-out-2017"])

    registro = json.loads((tmp_path / "log.jsonl").read_text(encoding="utf-8"))
    assert registro["ok"] is False
    assert registro["recusado_antes_do_cli"] == "AmostraNaoClassificada"
    assert "viewing:1493797951" in registro["motivo"]


def test_amostra_consistente_segue_para_o_cli(tmp_path, monkeypatch):
    """O contraponto: a guarda não pode recusar o caso normal — classificada
    com MAIS reviews do que as analisadas (acúmulo legítimo de §[D3])."""
    pc = _pc()
    monkeypatch.setattr(pc, "RESULTADO_DIR", tmp_path)
    monkeypatch.setattr(pc, "LOG_DIR", tmp_path)
    monkeypatch.setattr(pc, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(pc, "RAIZ", tmp_path)   # o resumo imprime LOG relativo à raiz
    classificadas = _classificacao_de_40(monkeypatch, [])
    _classificacao_de_40(monkeypatch, classificadas[:35])
    chamados = []
    monkeypatch.setattr(pc, "publicar_um", lambda slug: (
        chamados.append(slug), {"slug": slug, "ok": False, "elapsed_s": 0,
                                "returncode": 1, "expirou": False,
                                "stderr_tail": ""})[1])
    pc.cmd_publicar(["get-out-2017"])
    assert chamados == ["get-out-2017"]
