"""[2026-10-12] Prosa em modelo local — exceção escopada, ponta a ponta, falsa.

Zero rede e zero custo: `resposta_json_local` é substituída por um REPLAY que
responde a cada estágio com o texto JÁ PUBLICADO de `uncut-gems` (reconhece o
estágio pelo system prompt, o mesmo que o estágio de produção envia). Os
estágios, os extratores e os validadores são os de produção — só quem responde
muda. O que se prova:
1. os cinco estágios recebem o provider local por injeção, e o registro de
   cada chamada leva provider, modelo, modelo efetivo e nível de raciocínio;
2. `PROVIDER_POR_ESTAGIO` não muda e nenhum estágio chama a nuvem;
3. a saída nunca vai para `resultado/`, o lote C22 e o filme não publicado
   são recusados;
4. os 99 publicados ficam byte a byte iguais;
5. a seleção refeita do bruto reproduz a publicada;
6. falha de um estágio é registrada e não derruba os outros.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import briefing as br  # noqa: E402
from espectro24 import condicoes as C  # noqa: E402
from espectro24 import config, excecao_c22, local_ollama, prosa_local  # noqa: E402
from espectro24 import rotulagem as R  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24 import veredito as V  # noqa: E402
from espectro24.local_ollama import LLMLocalFalhou  # noqa: E402

SLUG = "uncut-gems"
PUB = RAIZ / "resultado"


def _hash_publicados() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PUB.glob("*.json"))}


def _resposta(texto: str, **extra) -> dict:
    base = {"texto": texto, "provider": "local", "modelo": "gpt-oss:20b",
            "modelo_efetivo": "gpt-oss:20b", "uso": {"prompt_tokens": 100,
                                                      "completion_tokens": 20},
            "thinking_tokens": 0, "finish_reason": "stop", "camada": "local",
            "latencia_s": 1.5, "custo_usd": 0.0, "think": local_ollama.nivel_think(),
            "leitura_prompt_s": 0.5, "geracao_s": 1.0, "carga_s": 0.0,
            "total_s": 1.6, "prompt_eval_count": 100, "eval_count": 20}
    base.update(extra)
    return base


class Replay:
    """Responde com o publicado. `chamadas` guarda (estágio, kwargs)."""

    def __init__(self, pub: dict):
        self.pub = pub
        self.chamadas: list[tuple[str, dict]] = []
        self.falhar: set[str] = set()

    def estagio_de(self, system: str, user: str) -> str:
        if system == br.PROMPT_NARRADOR_BRIEFING:
            return "narrativa"
        if system == V.PROMPT_VEREDITO:
            return "veredito"
        if system in (C.prompt_de(C.VARIANTE_EXPERIMENTO), C.prompt_de(None)):
            return "condicoes"
        if user.startswith("Grupo:"):
            return "rotulagem"
        if user.startswith("Bucket:"):
            return "sintese"
        raise AssertionError(f"estágio não reconhecido: {user[:60]!r}")

    def __call__(self, system, user, *, estagio, modelo, schema, prazo=None,
                 num_predict=None, num_ctx=None):
        e = self.estagio_de(system, user)
        self.chamadas.append((e, {"estagio_arg": estagio, "modelo": modelo,
                                  "schema": schema, "num_predict": num_predict,
                                  "num_ctx": num_ctx, "prazo": prazo}))
        if e in self.falhar:
            raise LLMLocalFalhou("prazo de 1800s estourado", 1800.0)
        p = self.pub
        if e == "sintese":
            nome = user.split("\n", 1)[0].split(": ", 1)[1].strip()
            b = next(x for x in p["buckets"] if x["bucket"] == nome)
            return _resposta(json.dumps({"temas": b["temas"],
                                         "observacao_geral": b["observacao_geral"]}))
        if e == "rotulagem":
            nome = user.split("\n", 1)[0].split(": ", 1)[1].strip()
            por_tema = {}
            for linha in p["eixos"]["linhas"]:
                cel = linha["por_bucket"].get(nome) or {}
                if cel.get("tema"):
                    por_tema[cel["tema"]] = linha["eixo"]
                for t in cel.get("temas_no_mesmo_eixo") or []:
                    por_tema[t] = linha["eixo"]
            temas = [l.split(". ", 1)[1] for l in user.splitlines() if l[:1].isdigit()]
            return _resposta(json.dumps({"rotulos": [
                {"tema": t, "eixo": por_tema.get(t, "livre")} for t in temas]}))
        if e == "narrativa":
            return _resposta(json.dumps({"narrativa": p["narrativa"]}))
        if e == "veredito":
            return _resposta(json.dumps({"veredito": p["veredito"]["texto_modelo"]
                                         or p["veredito"]["texto"]}))
        c = p["condicoes"]
        return _resposta(json.dumps({
            lado: [{"texto": x["texto"], "tema_origem": x["tema_origem"]}
                   for x in c[lado]] for lado in ("vale_a_pena", "talvez_evite")}
            | {"sem_condicao": []}))


@pytest.fixture
def pub():
    return json.loads((PUB / f"{SLUG}.json").read_text(encoding="utf-8"))


@pytest.fixture
def replay(monkeypatch, pub):
    r = Replay(pub)
    monkeypatch.setattr(prosa_local, "resposta_json_local", r)
    monkeypatch.delenv("ESPECTRO24_OLLAMA_THINK", raising=False)
    # a nuvem não pode ser tocada
    for nome in ("deepseek_resposta", "_gemini_resposta", "resposta"):
        monkeypatch.setattr(S, nome, lambda *a, **k: pytest.fail("chamou a nuvem"))
    return r


def test_regenera_o_filme_com_os_cinco_estagios_locais(replay, tmp_path, monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_THINK", "low")
    antes = _hash_publicados()
    tele = prosa_local.regenerar_filme(SLUG, modelo="gpt-oss:20b",
                                       saida=tmp_path, n=1)
    out = json.loads((tmp_path / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert tele["falhas"] == {}
    assert tele["selecao_reproduz_publicada"] is True
    assert {e for e, _ in replay.chamadas} == set(prosa_local.ESTAGIOS)
    for estagio in prosa_local.ESTAGIOS:
        r = tele["estagios"][estagio]
        assert r["provider"] == "local" and r["modelo"] == "gpt-oss:20b"
        assert r["think"] == "low" and r["custo_usd"] == 0.0
        assert r["modelos_efetivos"] == ["gpt-oss:20b"]
        assert all(c["provider"] == "local" and c["think"] == "low"
                   and c["modelo"] == "gpt-oss:20b" and "leitura_prompt_s" in c
                   and "geracao_s" in c for c in r["chamadas"])
    # os blocos de prosa nasceram do injetado, com provider e modelo declarados
    assert out["narrativa_selecao"] is not None and out["narrativa"]
    assert out["veredito"]["provider"] == "local"
    assert out["veredito"]["modelo"] == "gpt-oss:20b"
    assert out["condicoes"]["provider"] == "local"
    assert out["proveniencia_llm"]["excecao"] == prosa_local.EXCECAO
    assert out["proveniencia_llm"]["think"] == "low"
    # o que não é texto de LLM vem do publicado
    pub = json.loads((PUB / f"{SLUG}.json").read_text(encoding="utf-8"))
    for k in ("ficha", "distribuicao", "coleta", "total_reviews_observadas"):
        assert out[k] == pub[k]
    assert out["eixos"]["linhas"][0]["por_bucket"]["negativas"]["mencoes"] == \
        pub["eixos"]["linhas"][0]["por_bucket"]["negativas"]["mencoes"]
    # os 99 publicados intocados
    assert _hash_publicados() == antes


def test_sintese_usa_o_teto_e_a_janela_da_prosa_e_schema_json(replay, tmp_path):
    prosa_local.regenerar_filme(SLUG, modelo="m", saida=tmp_path, n=1,
                                estagios=("rotulagem",))
    sint = [k for e, k in replay.chamadas if e == "sintese"]
    pros = [k for e, k in replay.chamadas if e == "narrativa"]
    assert sint and all(k["schema"] == "json" for k in sint)
    assert all(k["num_ctx"] == prosa_local.NUM_CTX_PROSA for _, k in replay.chamadas)
    assert all(k["num_predict"] == prosa_local.NUM_PREDICT_ESTRUTURADO for k in sint)
    assert not pros  # estágio não pedido não roda


def test_provider_por_estagio_nao_foi_tocado(replay, tmp_path):
    antes = copy.deepcopy(config.PROVIDER_POR_ESTAGIO)
    prosa_local.regenerar_filme(SLUG, modelo="m", saida=tmp_path, n=1)
    assert config.PROVIDER_POR_ESTAGIO == antes
    assert "local" not in set(config.PROVIDER_POR_ESTAGIO.values())


def test_recusa_saida_dentro_de_resultado(tmp_path):
    with pytest.raises(prosa_local.ForaDoEscopo, match="resultado"):
        prosa_local.exigir_escopo(SLUG, PUB / "qualquer")
    with pytest.raises(prosa_local.ForaDoEscopo):
        prosa_local.exigir_escopo(SLUG, PUB)


def test_recusa_o_lote_c22_mesmo_que_exista_publicado(tmp_path):
    c22 = sorted(excecao_c22.SLUGS)[0]
    with pytest.raises(prosa_local.ForaDoEscopo, match="C22"):
        prosa_local.exigir_escopo(c22, tmp_path)


def test_recusa_filme_nao_publicado(tmp_path):
    with pytest.raises(prosa_local.ForaDoEscopo, match="publicado"):
        prosa_local.exigir_escopo("filme-que-nao-existe", tmp_path)


def test_falha_de_um_estagio_e_registrada_e_nao_derruba_os_outros(replay, tmp_path):
    replay.falhar.add("narrativa")
    tele = prosa_local.regenerar_filme(SLUG, modelo="m", saida=tmp_path, n=1)
    assert "narrativa" in tele["falhas"]
    assert "veredito" not in tele["falhas"] and "condicoes" not in tele["falhas"]
    n = tele["estagios"]["narrativa"]
    assert n["n_falhas"] >= 1
    assert any(c["ok"] is False and c["latencia_s"] == 1800.0
               for c in n["chamadas"])
    assert (tmp_path / f"{SLUG}.json").exists()


def test_think_invalido_nao_chama_nada(replay, tmp_path, monkeypatch):
    monkeypatch.setenv("ESPECTRO24_OLLAMA_THINK", "true")
    with pytest.raises(ValueError):
        prosa_local.regenerar_filme(SLUG, modelo="m", saida=tmp_path, n=1)
    assert replay.chamadas == []


def test_chamadas_locais_sao_o_client_call_e_o_gerar():
    c = prosa_local.ChamadasLocais("narrativa", "m", extrair=lambda t: t.upper())
    assert c.estagio == "narrativa"
    with pytest.raises(ValueError):
        prosa_local.ChamadasLocais("classificacao", "m")


def test_prazo_da_prosa_e_maior_que_o_da_classificacao(monkeypatch):
    monkeypatch.delenv("ESPECTRO24_OLLAMA_PRAZO_PROSA_S", raising=False)
    assert prosa_local.prazo_prosa_s() == 1800.0 > local_ollama.PRAZO_PADRAO_S
    monkeypatch.setenv("ESPECTRO24_OLLAMA_PRAZO_PROSA_S", "3600")
    assert prosa_local.prazo_prosa_s() == 3600.0
