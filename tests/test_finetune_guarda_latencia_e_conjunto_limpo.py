"""[2026-10-22] Fine-tuning, fase 0: a guarda de LATÊNCIA do juiz
(`scripts/finetune/_latencia.py`, no lugar da guarda de RAM livre) e o conjunto
LIMPO do treino/validação (`scripts/finetune/conjunto_limpo.py`), e o
orquestrador do smoke no Kaggle (candidatos do `meta.json`, pastas de saída
`<modelo>__<seq>`)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))

import conjunto_limpo as CL  # noqa: E402
from _latencia import GuardaDeLatencia, LatenciaAnomala  # noqa: E402


def _env_sem_chaves() -> dict:
    """Outros testes carregam o `.env` e deixam chaves em `os.environ`; a guarda do
    subprocesso (`_guarda`) recusa rodar com elas."""
    import os
    return {k: v for k, v in os.environ.items()
            if not k.endswith("_API_KEY") and k != "GOOGLE_API_KEY"}


def _chamada(guarda: GuardaDeLatencia, latencia_s: float) -> None:
    guarda.registrar(latencia_s)


def test_sem_historico_suficiente_nao_pausa():
    g = GuardaDeLatencia(minimo=10)
    for _ in range(9):
        _chamada(g, 15.0)
    assert g.mediana() is None               # 9 na janela: ainda não há mediana
    _chamada(g, 900.0)
    assert g.pendente is None


def test_pausa_acima_de_4x_a_mediana_e_so_acima():
    g = GuardaDeLatencia()
    for _ in range(20):
        _chamada(g, 15.0)
    _chamada(g, 60.0)                        # exatamente 4× não passa
    assert g.pendente is None
    _chamada(g, 60.1)
    assert isinstance(g.pendente, LatenciaAnomala)
    assert g.pendente.mediana_s == 15.0


def test_a_chamada_anomala_nao_entra_na_janela():
    g = GuardaDeLatencia()
    for _ in range(20):
        _chamada(g, 15.0)
    _chamada(g, 200.0)
    assert 200.0 not in g.recentes and g.mediana() == 15.0


def test_janela_e_das_ultimas_20():
    g = GuardaDeLatencia()
    for _ in range(20):
        _chamada(g, 100.0)
    for _ in range(20):
        _chamada(g, 10.0)                    # as lentas saem da janela
    assert g.mediana() == 10.0
    _chamada(g, 41.0)
    assert g.pendente is not None


def test_ignorar_proxima_nao_mede_nem_entra_na_janela():
    g = GuardaDeLatencia()
    for _ in range(20):
        _chamada(g, 15.0)
    g.ignorar_proxima()
    _chamada(g, 120.0)                       # recarga do modelo depois de reiniciar
    assert g.pendente is None and 120.0 not in g.recentes
    _chamada(g, 120.0)                       # só a PRÓXIMA é ignorada
    assert g.pendente is not None


def test_envolver_deixa_a_lenta_terminar_e_barra_a_seguinte(monkeypatch):
    relogio = iter([0.0, 15.0] * 10 + [0.0, 200.0])    # 10 normais, 1 lenta
    monkeypatch.setattr("_latencia.time.monotonic", lambda: next(relogio))
    chamadas = []
    g = GuardaDeLatencia()
    chamar = g.envolver(lambda s, u: chamadas.append(1) or {"ok": True})
    for _ in range(11):
        assert chamar("s", "u") == {"ok": True}          # a lenta (11ª) devolve o resultado
    assert g.pendente is not None
    with pytest.raises(LatenciaAnomala):
        chamar("s", "u")
    assert len(chamadas) == 11                           # a 12ª nem saiu


def test_lat_anomala_atravessa_except_exception():
    """O `J.rodar` captura `Exception`; a pausa não pode virar "falha de par"."""
    assert not issubclass(LatenciaAnomala, Exception)
    with pytest.raises(LatenciaAnomala):
        try:
            raise LatenciaAnomala(90.0, 15.0, 4.0, 20)
        except Exception:                    # noqa: BLE001
            pytest.fail("a pausa foi engolida")


# ---------------------------------------------------------------------------
# conjunto limpo
# ---------------------------------------------------------------------------

def _mundo():
    split = {"treino": ["a", "b"], "validacao": ["v"], "teste": ["t"],
             "buckets_excluidos": [{"slug": "t", "bucket": "positivas"}]}
    inv = {"exemplos_sintese": [
        *({"slug": s, "bucket": b, "excluido": False}
          for s in ("a", "b", "v", "t") for b in ("negativas", "medianas", "positivas")),
        {"slug": "x", "bucket": "negativas", "excluido": True}]}
    buckets = [{"slug": s, "bucket": b, "removido": (s, b) in {("a", "medianas"), ("v", "positivas")},
                "pendente": False}
               for s in ("a", "b", "v") for b in ("negativas", "medianas", "positivas")]
    return split, inv, {"buckets": buckets}


def test_conjunto_limpo_tira_so_o_que_saiu_e_nunca_le_o_teste():
    split, inv, resumo = _mundo()
    r = CL.calcular(split, inv, resumo)
    assert r["base"] == {"treino": 6, "validacao": 3}
    assert ("a", "medianas") not in r["fica"]["treino"] and len(r["fica"]["treino"]) == 5
    assert r["sai"]["validacao"] == [("v", "positivas")] and len(r["fica"]["validacao"]) == 2
    assert all(s != "t" for c in r["fica"].values() for s, _ in c)


def test_exemplo_fora_por_comprimento_sai_so_do_treino_e_fica_registrado():
    split, inv, resumo = _mundo()
    r = CL.calcular(split, inv, resumo, {("b", "negativas"): "longo demais",
                                         ("v", "negativas"): "ignorado: validação"})
    assert ("b", "negativas") not in r["fica"]["treino"] and len(r["fica"]["treino"]) == 4
    assert ("v", "negativas") in r["fica"]["validacao"]            # só vale para o treino
    assert r["fora_por_comprimento"] == [("b", "negativas")]
    assert r["motivo_comprimento"] == {"b/negativas": "longo demais"}
    sem = CL.calcular(split, inv, resumo, {})
    assert sem["sha256_ids"] != r["sha256_ids"] and len(sem["fica"]["treino"]) == 5


def test_hash_do_conjunto_muda_quando_um_exemplo_sai():
    split, inv, resumo = _mundo()
    h1 = CL.calcular(split, inv, resumo)["sha256_ids"]
    resumo["buckets"][0]["removido"] = True
    assert CL.calcular(split, inv, resumo)["sha256_ids"] != h1


def test_limpeza_com_bucket_pendente_ou_faltando_nao_passa_em_silencio():
    split, inv, resumo = _mundo()
    resumo["buckets"][0]["pendente"] = True
    with pytest.raises(ValueError, match="pendente"):
        CL.calcular(split, inv, resumo)
    split, inv, resumo = _mundo()
    resumo["buckets"].pop()
    with pytest.raises(ValueError, match="sem veredito"):
        CL.calcular(split, inv, resumo)


# ---------------------------------------------------------------------------
# orquestrador do smoke no Kaggle: candidatos do meta.json, pastas previsíveis
# ---------------------------------------------------------------------------

def _rodar_orquestrador(tmp_path, meta, oom_em):
    """Executa `orquestrar` num subprocesso (o módulo faz `chdir` ao importar)."""
    entrada = tmp_path / "input" / "ds"
    entrada.mkdir(parents=True)
    (entrada / "smoke.jsonl").write_text("{}\n")
    if meta is not None:
        (entrada / "meta.json").write_text(json.dumps(meta))
    codigo = f"""
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("smoke", {str(RAIZ / 'scripts/finetune/kaggle/kernel/smoke_treino.py')!r})
m = importlib.util.module_from_spec(spec); sys.modules["smoke"] = m; spec.loader.exec_module(m)
tmp = Path({str(tmp_path)!r})
m.SAIDA, m.ENTRADA_GLOB = tmp / "smoke", str(tmp / "input" / "**" / "smoke.jsonl")
m.instalar = lambda: {{"rc": 0}}
chamadas = []
def falso(nome, seq, timeout_s):
    chamadas.append((nome, seq))
    (m.SAIDA / nome).mkdir(parents=True, exist_ok=True)
    (m.SAIDA / nome / "log.json").write_text("{{}}")
    return {{"modelo": nome, "seq": seq, "oom": (nome, seq) in {oom_em!r}}}
m.rodar_um = falso
m.orquestrar(False)
print(json.dumps({{"chamadas": chamadas, "pastas": sorted(p.name for p in m.SAIDA.iterdir() if p.is_dir())}}))
"""
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=60,
                       env=_env_sem_chaves())
    assert r.returncode == 0, r.stderr[-800:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_smoke_roda_so_os_candidatos_do_meta_e_nomeia_as_pastas_pela_sequencia(tmp_path):
    out = _rodar_orquestrador(tmp_path, {"candidatos": ["qwen3-8b"]}, {("qwen3-8b", 14336)})
    assert out["chamadas"] == [["qwen3-8b", 14336], ["qwen3-8b", 12288]]
    assert out["pastas"] == ["qwen3-8b__12288", "qwen3-8b__14336"]


def test_smoke_sem_meta_mantem_e4b_depois_12b_e_nao_repete_o_que_passou(tmp_path):
    out = _rodar_orquestrador(tmp_path, None, set())
    assert out["chamadas"] == [["gemma-4-e4b", 14336], ["gemma-4-12b", 14336]]
    assert out["pastas"] == ["gemma-4-12b__14336", "gemma-4-e4b__14336"]


# ---------------------------------------------------------------------------
# Windows: importar as exportações achando as pastas pelo .gguf
# ---------------------------------------------------------------------------

def test_importar_acha_as_pastas_pelo_gguf_e_nao_pelo_nome(tmp_path):
    # o módulo importa `_guarda` (rede bloqueada) e `comum`: só a função pura interessa
    codigo = f"""
import json, sys
sys.argv = ["x", "--sem-autoteste"]
sys.path.insert(0, {str(RAIZ / 'scripts' / 'finetune')!r})
import viabilidade_ollama as V
from pathlib import Path
raiz = Path({str(tmp_path)!r})
print(json.dumps([[str(x["pasta"].relative_to(raiz)), x["gguf"].name, x["familia"], x["nome"]]
                  for x in V.achar_exportacoes(raiz)]))
"""
    for rel, modelo, gguf, mf in [
            ("smoke/qwen3-8b__14336", "qwen3-8b", "qwen3-8b.Q4_K_M.gguf", True),
            ("smoke/qualquer-nome-estranho", "gemma-4-e4b", "model.Q4_K_M.gguf", True),
            ("smoke/gemma-4-12b__12288", "gemma-4-12b", None, False),     # OOM: sem gguf
            ("smoke/sem-modelfile", "qwen3-8b", "x.Q4_K_M.gguf", False),
            ("smoke/f16", "qwen3-8b", "x.F16.gguf", True)]:                # não é Q4_K_M
        d = tmp_path / rel
        d.mkdir(parents=True)
        (d / "log.json").write_text(json.dumps({"modelo": modelo}))
        if gguf:
            (d / gguf).write_bytes(b"x")
        if mf:
            (d / "Modelfile").write_text("FROM x")
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=60,
                       env=_env_sem_chaves())
    assert r.returncode == 0, r.stderr[-800:]
    achados = json.loads(r.stdout.strip().splitlines()[-1])
    assert achados == [
        ["smoke/qualquer-nome-estranho", "model.Q4_K_M.gguf", "gemma", "espectro-gemma-4-e4b"],
        ["smoke/qwen3-8b__14336", "qwen3-8b.Q4_K_M.gguf", "qwen", "espectro-qwen3-8b"]]
