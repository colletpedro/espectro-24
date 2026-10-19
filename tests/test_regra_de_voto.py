"""[2026-10-12] Regra de voto (k de 3) — recálculo sem chamadas."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import auditoria_acuracia as aa  # noqa: E402
import regra_de_voto as RV  # noqa: E402
import variante_impacto_estrito as vie  # noqa: E402


def _escrever(base: Path, prefixo: str, passes: list[dict[str, list[str]]]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    for n, p in enumerate(passes, 1):
        (base / f"{prefixo}_passe_{n}.jsonl").write_text(
            "\n".join(json.dumps({"ok": True, "id": rid, "eixos": e})
                      for rid, e in p.items()) + "\n", encoding="utf-8")


def test_k_conta_votos_entre_os_tres_passes(tmp_path):
    _escrever(tmp_path, "c", [{"r1": ["ritmo", "atuacao"]},
                              {"r1": ["ritmo"]},
                              {"r1": ["ritmo", "som_trilha"]}])
    assert RV.consenso_k(tmp_path, "c", 1)["r1"] == ["atuacao", "ritmo", "som_trilha"]
    assert RV.consenso_k(tmp_path, "c", 2)["r1"] == ["ritmo"]
    assert RV.consenso_k(tmp_path, "c", 3)["r1"] == ["ritmo"]
    _escrever(tmp_path, "d", [{"r1": ["ritmo"]}, {"r1": ["atuacao"]}, {"r1": []}])
    assert RV.consenso_k(tmp_path, "d", 3)["r1"] == []
    assert RV.consenso_k(tmp_path, "d", 2)["r1"] == []


def test_k2_e_exatamente_o_consenso_de_producao():
    prod = vie.consenso("A_regra", RV.DIR_DS_CLASS)
    k2 = RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 2)
    assert {r: g["eixos"] for r, g in prod.items()} == k2


def test_as_regras_sao_aninhadas_k1_contem_k2_contem_k3():
    k = {n: RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", n) for n in (1, 2, 3)}
    for rid in k[1]:
        assert set(k[3][rid]) <= set(k[2][rid]) <= set(k[1][rid])


def test_verificador_remove_so_com_veredito_falso_e_conta_o_que_nao_tem_veredito():
    pred = {"a": ["impacto_emocional", "ritmo"], "b": ["impacto_emocional"],
            "c": ["impacto_emocional"], "d": ["ritmo"]}
    out, info = RV.com_verificador(pred, {"a": False, "b": True})
    assert out["a"] == ["ritmo"] and out["b"] == ["impacto_emocional"]
    assert out["c"] == ["impacto_emocional"] and out["d"] == ["ritmo"]  # sem veredito: mantém
    assert info == {"candidatas_sem_veredito": 1, "removidas": 1}
    assert pred["a"] == ["impacto_emocional", "ritmo"]  # não muta a entrada


def test_deepseek_em_producao_reproduz_o_f1_publicado_0_811():
    anot = aa.ler_anotacoes_humanas()
    ds, _ = RV.com_verificador(RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 2),
                               RV.veredito_passe1(RV.DIR_DS_VERIF / "V2_alvo_passe_1.jsonl"))
    ids = sorted(ds)
    c = RV._contagens(anot, ds, ids)["_micro"]
    f1 = RV._prf(*c)["f1"]
    assert round(f1, 3) == 0.811


def test_bootstrap_e_pareado_deterministico_e_delta_zero_contra_si_mesmo():
    anot = aa.ler_anotacoes_humanas()
    ds = RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 2)
    t = RV.tabela_com_ic(anot, ds, ds)
    assert t["_micro"]["delta_f1"] == {"valor": 0.0, "ic95": [0.0, 0.0]}
    assert t["n"] == 100 and sum(t["positivos"].values()) > 0
    a = RV.tabela_com_ic(anot, ds, RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 3))
    b = RV.tabela_com_ic(anot, ds, RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 3))
    assert a == b


def test_regra_mais_exigente_sobe_precisao_e_cai_recall():
    anot = aa.ler_anotacoes_humanas()
    ds2 = RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 2)
    ds1 = RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 1)
    ds3 = RV.consenso_k(RV.DIR_DS_CLASS, "A_regra", 3)
    p = {k: RV._prf(*RV._contagens(anot, d, sorted(d))["_micro"])
         for k, d in ((1, ds1), (2, ds2), (3, ds3))}
    assert p[1]["recall"] >= p[2]["recall"] >= p[3]["recall"]
    assert p[1]["precisao"] <= p[2]["precisao"] <= p[3]["precisao"]


def test_o_aviso_de_escolha_da_regra_consta_do_relatorio():
    rel = {"aviso": RV.AVISO, "B": 5000, "semente": RV.SEMENTE, "verificador": "x",
           "regras": {}}
    md = RV.markdown(rel)
    assert "infla o resultado" in md and "pista, não como aprovação" in md
    assert RV.SEMENTE == 20261012 and RV.N_BOOTSTRAP == 5000


def test_guia_do_windows_usa_o_tempo_de_leitura_e_nao_o_prompt_eval_count():
    doc = (RAIZ / "docs" / "SETUP_WINDOWS.md").read_text(encoding="utf-8")
    assert "tempo de leitura do prompt" in doc
    assert "prompt_eval_count` pequeno" not in doc
    assert "Não** use `prompt_eval_count` como sinal" in doc
    assert "gerar_prosa_local.py" in doc and "gpt-oss:20b" in doc
