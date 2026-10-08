"""[2026-09-22, C22 Etapa 2] Síntese e rotulagem dos 55 em Gemini, na publicação.

Zero rede: `_gemini_resposta` é substituído, e o DeepSeek é trocado por uma
armadilha que falha o teste se for chamado.

O que se prova:
1. `ChamadaGeminiExcecao` fixa o modelo, e grava por chamada o modelo EFETIVO,
   `finish_reason`, thinking e a unidade;
2. síntese e rotulagem com o cliente injetado NÃO tocam o DeepSeek nem
   `provider_do_estagio` — `PROVIDER_POR_ESTAGIO` fica como está;
3. o CLI recusa slug fora dos 55, `--provider`, `--reuse-synthesis` e filme
   cuja classificação no consenso não é inteira da exceção;
4. bucket com síntese sem JSON PARA a publicação (exit 7), com o
   `finish_reason` no aviso;
5. `frontend/build_data.py` tira `proveniencia_llm` antes do site.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import cli  # noqa: E402
from espectro24 import config as CFG  # noqa: E402
from espectro24 import eixos as E  # noqa: E402
from espectro24 import excecao_c22 as C22  # noqa: E402
from espectro24 import rotulagem as R  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.models import BucketResult, LevelResult, Review  # noqa: E402

SLUG = sorted(C22.SLUGS)[0]


def _resp_gemini(texto: str, finish: str = "STOP", thinking: int = 12):
    return SimpleNamespace(
        text=texto, model_version="gemini-3.7-flash",
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name=finish))],
        usage_metadata=SimpleNamespace(prompt_token_count=900,
                                       candidates_token_count=300,
                                       cached_content_token_count=0,
                                       thoughts_token_count=thinking))


@pytest.fixture
def sem_deepseek(monkeypatch):
    def armadilha(*a, **kw):
        raise AssertionError("o DeepSeek foi chamado na exceção C22")
    monkeypatch.setattr(S, "deepseek_resposta", armadilha)
    monkeypatch.setattr(S, "deepseek_client_call", armadilha)
    monkeypatch.setattr(S, "provider_do_estagio", armadilha)
    monkeypatch.setitem(S.PROVIDER_CLIENTS, "deepseek", armadilha)


def _instalar_gemini(monkeypatch, respostas: list):
    pedidos = []

    def falso(system, user, model, **kw):
        pedidos.append({"model": model, "user": user, **kw})
        return respostas.pop(0)
    monkeypatch.setattr(S, "_gemini_resposta", falso)
    return pedidos


def _bucket(nome="positivas", n=5):
    lvl = LevelResult(4.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"v{i}", rating=4.0, text=f"review {i}",
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text=f"review {i} completa") for i in range(n)]
    return BucketResult(nome=nome, alvo=30, modo="reduzido", niveis=[lvl])


SINTESE_OK = json.dumps({"bucket": "positivas", "temas": [
    {"tema": "Atuações marcantes", "mencoes_aproximadas": 3,
     "n_reviews_analisadas": 5,
     "exemplo_parafraseado": "O elenco é elogiado pela entrega."}],
    "observacao_geral": "Este grupo destaca as atuações."})


def test_a_chamada_fixa_o_modelo_e_grava_o_efetivo(monkeypatch):
    pedidos = _instalar_gemini(monkeypatch, [_resp_gemini("{}", thinking=40)])
    c = S.ChamadaGeminiExcecao("sintese")
    assert c("sys", "Bucket: positivas\nresto", "deepseek-v4-flash") == "{}"
    assert pedidos[0]["model"] == "gemini-3.7-flash"
    assert pedidos[0]["thinking_budget"] == 0
    assert pedidos[0]["max_output_tokens"] == CFG.LLM_MAX_TOKENS
    r = c.resumo()
    assert r["provider"] == "gemini" and r["modelos_efetivos"] == ["gemini-3.7-flash"]
    assert r["chamadas"][0]["unidade"] == "Bucket: positivas"
    assert r["chamadas"][0]["thinking_tokens"] == 40
    assert r["finish_reason"] == {"STOP": 1}


def test_a_sintese_com_o_cliente_da_excecao_nao_toca_o_deepseek(
        monkeypatch, sem_deepseek):
    _instalar_gemini(monkeypatch, [_resp_gemini(SINTESE_OK)])
    c = S.ChamadaGeminiExcecao("sintese")
    b = S.synthesize_bucket(_bucket(), client_call=c, model=C22.MODELO)
    assert [t.tema for t in b.temas] == ["Atuações marcantes"]
    assert b.fallback_conteudo is None
    assert c.resumo()["n_chamadas"] == 1


def test_a_rotulagem_com_o_cliente_da_excecao_nao_toca_o_deepseek(
        monkeypatch, sem_deepseek):
    _instalar_gemini(monkeypatch, [_resp_gemini(json.dumps(
        {"rotulos": [{"tema": "Atuações marcantes", "eixo": "atuacao"}]}))])
    c = S.ChamadaGeminiExcecao("rotulagem")
    r = R.rotular_bucket("positivas", [{"tema": "Atuações marcantes",
                                        "mencoes_aproximadas": 3}],
                         client_call=c, model=C22.MODELO)
    assert r["rotulos"][0]["eixo"] == "atuacao" and not r["falhou"]
    assert c.resumo()["chamadas"][0]["unidade"] == "Grupo: positivas"


def test_provider_por_estagio_continua_deepseek_na_sintese_e_na_rotulagem():
    assert CFG.PROVIDER_POR_ESTAGIO["classificacao"] == "deepseek"
    assert CFG.PROVIDER_POR_ESTAGIO["rotulagem"] == "deepseek"


# --- o CLI ----------------------------------------------------------------

def _args(**kw):
    base = dict(slug=SLUG, provider=None, reuse_synthesis=False)
    return SimpleNamespace(**{**base, **kw})


def _consenso(tmp_path, monkeypatch, linhas):
    arq = tmp_path / "consenso.jsonl"
    arq.write_text("".join(json.dumps(l) + "\n" for l in linhas), encoding="utf-8")
    monkeypatch.setattr(E, "CONSENSO_PADRAO", str(arq))


def _linha(rid, excecao=True):
    l = {"slug": SLUG, "bucket": "positivas", "id": rid, "eixos": ["atuacao"]}
    if excecao:
        l["classificacao_excecao"] = {"excecao": C22.EXCECAO, "provider": "gemini"}
    return l


@pytest.mark.parametrize("args", [
    _args(slug=None), _args(slug="the-godfather"),
    _args(provider="gemini"), _args(reuse_synthesis=True)])
def test_o_cli_recusa_fora_do_escopo(tmp_path, monkeypatch, args):
    _consenso(tmp_path, monkeypatch, [_linha("r1")])
    with pytest.raises(SystemExit) as e:
        cli._preparar_excecao_c22(args)
    assert e.value.code == 2


def test_o_cli_recusa_filme_com_classificacao_de_fora_da_excecao(
        tmp_path, monkeypatch):
    _consenso(tmp_path, monkeypatch, [_linha("r1"), _linha("r2", excecao=False)])
    with pytest.raises(SystemExit):
        cli._preparar_excecao_c22(_args())
    _consenso(tmp_path, monkeypatch, [])
    with pytest.raises(SystemExit):
        cli._preparar_excecao_c22(_args())


def test_o_cli_prepara_os_dois_clientes(tmp_path, monkeypatch):
    _consenso(tmp_path, monkeypatch, [_linha("r1"), _linha("r2")])
    ex = cli._preparar_excecao_c22(_args())
    assert ex["n_consenso"] == 2
    assert ex["sintese"].modelo_fixo == ex["rotulagem"].modelo_fixo == C22.MODELO


def test_proveniencia_gravada_e_falha_de_json_para_a_publicacao(tmp_path, monkeypatch):
    _consenso(tmp_path, monkeypatch, [_linha("r1")])
    ex = cli._preparar_excecao_c22(_args())
    ok = {"buckets": [{"bucket": "positivas", "observacao_geral": "Este grupo..."}]}
    cli._fechar_excecao_c22(ok, ex)
    p = ok["proveniencia_llm"]
    assert p["excecao"] == C22.EXCECAO and p["sintese"]["provider"] == "gemini"
    assert p["classificacao"]["n_reviews_no_consenso"] == 1

    ruim = {"buckets": [{"bucket": "negativas",
                         "observacao_geral": cli.FALHA_JSON_SINTESE}]}
    with pytest.raises(SystemExit) as e:
        cli._fechar_excecao_c22(ruim, ex)
    assert e.value.code == 7


def test_build_data_tira_a_proveniencia_do_site():
    fonte = (RAIZ / "frontend" / "build_data.py").read_text(encoding="utf-8")
    assert 'data.pop("proveniencia_llm", None)' in fonte


def test_ipv4_so_quando_pedido(monkeypatch):
    """[2026-09-23] Contorno de ambiente (rota IPv6 quebrada): sem a variável,
    o cliente Gemini é o de sempre; com ela, o httpx sai só por IPv4."""
    monkeypatch.delenv("ESPECTRO24_GEMINI_IPV4", raising=False)
    op = S._http_options_gemini(1000)
    assert op.timeout == 1000 and not op.client_args
    monkeypatch.setenv("ESPECTRO24_GEMINI_IPV4", "1")
    op = S._http_options_gemini(1000)
    transporte = op.client_args["transport"]
    assert transporte._pool._local_address == "0.0.0.0"


def test_a_publicacao_declara_as_recusas_e_para_sem_aceite(tmp_path, monkeypatch):
    from espectro24 import recusas
    _consenso(tmp_path, monkeypatch, [_linha("r1")])
    ex = cli._preparar_excecao_c22(_args())
    reg = {"slug": SLUG, "bucket": "negativas", "id": "x", "provider": "gemini",
           "modelo": "m", "bloqueio": "PROHIBITED_CONTENT",
           "n_tentativas_bloqueadas": 2, "evidencia": "t"}
    recusas.registrar([reg])
    recusas.anotar_substitutas(SLUG, {"negativas": {"x"}}, {"negativas": set()})
    out = {"slug": SLUG, "buckets": [{"bucket": "negativas", "observacao_geral": "ok"},
                                     {"bucket": "positivas", "observacao_geral": "ok"}]}
    with pytest.raises(SystemExit) as e:
        cli._fechar_excecao_c22(out, ex)          # esgotada, sem aceite
    assert e.value.code == 8
    recusas.aceitar_n_menor(SLUG, "negativas", "aceito")
    cli._fechar_excecao_c22(out, ex)
    assert out["buckets"][0]["recusas_filtro_conteudo"]["sem_substituta"][0][
        "aceite_do_dono"] == "aceito"
    assert "recusas_filtro_conteudo" not in out["buckets"][1]
