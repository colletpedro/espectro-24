"""`scripts/regenerar_item.py` — regeneração de UM item de um filme já gerado.

Foi o caminho que reescreveu o `exemplo_parafraseado` de casablanca (dado publicado).
Garantias: só o campo pedido muda; as MESMAS validações da síntese valem (aspas, quantidade
vaga, idioma, vazio/igual, tema com outro nome, validar_publicado); se nada passa, NADA é
gravado; a chamada vai pelo livro-caixa do Featherless (estágio `sintese`, slug do filme) e a
troca fica registrada em `estado.json`. Sem rede: o cliente é falso.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import etapa2_featherless as E2  # noqa: E402
import importacao_ponta_a_ponta as IPP  # noqa: E402
import regenerar_item as RI  # noqa: E402
from espectro24 import featherless as F  # noqa: E402

SLUG, BUCKET = "filme-x", "positivas"
ANTIGO = "A produção valoriza o significado do filmepara o público da época."
# primeira resposta REAL do casablanca: a guarda de quantidade não consegue reescrevê-la
VAGA = ("Várias destas reviews positivas valorizam o fato de o longa ter sido produzido e lançado "
        "enquanto a guerra ainda acontecia, enxergando nisso uma marca de coragem.")
OUTRO = "Reviews positivas valorizam o contexto histórico e a mensagem antifascista da obra."
TEMA = "Contexto histórico e mensagem"
MODEL = "deepseek-ai/DeepSeek-V4.1-Flash-1017"


def _tema(nome, exemplo, mencoes):
    return {"tema": nome, "mencoes_aproximadas": mencoes, "n_reviews_analisadas": 5,
            "exemplo_parafraseado": exemplo, "mencoes_clampadas": False,
            "mencoes_valor_original": None, "aspas_removidas": False}


def _doc():
    temas = [_tema("Fotografia", "A fotografia em preto e branco é elogiada.", 4),
             _tema(TEMA, ANTIGO, 3)]
    return {
        "slug": SLUG,
        "buckets": [
            {"bucket": "negativas", "temas": [_tema("Ritmo", "O ritmo inicial é lento.", 2)],
             "observacao_geral": "Este grupo critica o ritmo.", "n_validas": 5},
            {"bucket": BUCKET, "temas": temas, "observacao_geral": "Este grupo elogia a obra.",
             "n_validas": 5, "idioma_invalido": False, "escopo_suspeito": False},
        ],
        "eixos": {"positivas": {"contexto": {"tema": TEMA, "exemplo_parafraseado": ANTIGO,
                                             "temas_no_mesmo_eixo": []},
                                "foto": {"tema": "Fotografia",
                                         "exemplo_parafraseado": "A fotografia em preto e branco é elogiada."}}},
    }


def _estado():
    return {"slug": SLUG, "estado": "gerado",
            "validadores_bullets": {BUCKET: {"passa_publicado": True}}}


class _Rev:
    def __init__(self, i):
        self.rating = 4.0
        self.effective_text = f"review numero {i} sobre o filme"
        self.texto = self.effective_text


@pytest.fixture
def cena(tmp_path, monkeypatch):
    """Pasta de execução falsa + tudo que tocaria rede/ambiente real substituído."""
    out = tmp_path / "exec"
    (out / SLUG).mkdir(parents=True)
    (out / SLUG / "bullets.json").write_text(json.dumps(_doc(), ensure_ascii=False), encoding="utf-8")
    (out / SLUG / "estado.json").write_text(json.dumps(_estado()), encoding="utf-8")
    # `definir_out` e `ambiente` mexem em globais/variáveis de ambiente: restaura tudo
    monkeypatch.setattr(IPP, "OUT", IPP.OUT)
    monkeypatch.setattr(IPP, "SLUGS", IPP.SLUGS)
    monkeypatch.setattr(IPP, "ambiente", lambda: None)
    monkeypatch.setattr(IPP, "conferir_invariantes", lambda: None)
    monkeypatch.setattr(F, "sessao_ambiente", lambda: None)
    revs = [_Rev(i) for i in range(5)]
    bucket = NS(nome=BUCKET, reviews_analisadas=revs)
    monkeypatch.setattr(RI, "_bucket_do_bruto", lambda slug, nome: bucket)
    from espectro24 import pipeline as P
    monkeypatch.setattr(P, "amostra_do_bruto", lambda slug, raiz=None: {BUCKET: revs})
    return NS(out=out, pasta=out / SLUG, revs=revs)


class Cliente:
    """Cliente do SDK falso: devolve as respostas na ordem e guarda o que recebeu."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.pedidos.append(kw)
        conteudo = self.respostas.pop(0)
        return NS(model=MODEL, usage=NS(prompt_tokens=100, completion_tokens=20,
                                        completion_tokens_details=NS(reasoning_tokens=0)),
                  choices=[NS(message=NS(content=conteudo))])


@pytest.fixture
def livro(tmp_path, monkeypatch, cena):
    """Livro-caixa REAL (`featherless.Sessao`) com cliente falso, no lugar da sessão do ambiente."""
    pasta = tmp_path / "caixa"
    pasta.mkdir()
    (pasta / "plano.json").write_text(json.dumps({"concurrency": 100, "max_context_length": None}))
    sessao = F.Sessao(pasta)
    real = F.resposta

    def configurar(respostas):
        cli = Cliente(respostas)
        monkeypatch.setattr(F, "resposta", lambda *a, **k: real(*a, client=cli, sessao=sessao, **k))
        return cli
    return NS(sessao=sessao, configurar=configurar, pasta=pasta)


def _json(exemplo, tema=TEMA):
    return json.dumps({"tema": tema, "exemplo_parafraseado": exemplo}, ensure_ascii=False)


def _ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rodar(cena):
    return RI.regenerar_exemplo(cena.out, SLUG, BUCKET, TEMA)


# ---------------------------------------------------------------- só o campo pedido

def test_reescreve_so_o_campo_pedido(cena, livro):
    livro.configurar([_json(OUTRO)])
    antes = _ler(cena.pasta / "bullets.json")
    r = _rodar(cena)
    depois = _ler(cena.pasta / "bullets.json")
    assert r["antes"] == ANTIGO and r["depois"] == OUTRO and r["celulas_eixos"] == 1

    esperado = copy.deepcopy(antes)
    b = next(b for b in esperado["buckets"] if b["bucket"] == BUCKET)
    next(t for t in b["temas"] if t["tema"] == TEMA)["exemplo_parafraseado"] = OUTRO
    esperado["eixos"]["positivas"]["contexto"]["exemplo_parafraseado"] = OUTRO
    assert depois == esperado  # NADA mais mudou: outros temas, menções, observação, outros buckets


def test_nao_toca_outro_tema_com_o_mesmo_exemplo_em_outro_bucket(cena, livro):
    """A troca em `eixos` exige tema E texto antigo iguais: célula de outro tema fica."""
    d = _ler(cena.pasta / "bullets.json")
    d["eixos"]["positivas"]["outra"] = {"tema": "Outro tema", "exemplo_parafraseado": ANTIGO}
    (cena.pasta / "bullets.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    livro.configurar([_json(OUTRO)])
    _rodar(cena)
    depois = _ler(cena.pasta / "bullets.json")
    assert depois["eixos"]["positivas"]["outra"]["exemplo_parafraseado"] == ANTIGO


def test_prompt_e_sintese_do_bucket_mais_o_reforco_de_item(cena, livro):
    from espectro24 import synthesize as S
    cli = livro.configurar([_json(OUTRO)])
    _rodar(cena)
    msgs = cli.pedidos[0]["messages"]
    assert msgs[0]["content"] == S.build_system_prompt(BUCKET) + RI._REFORCO_ITEM
    assert msgs[1]["content"].startswith(S.build_user_message(cena_bucket(cena)))
    assert f"Tema cujo `exemplo_parafraseado` deve ser reescrito: {TEMA}" in msgs[1]["content"]
    assert cli.pedidos[0]["model"] == MODEL  # o modelo da síntese, sem mistura
    assert cli.pedidos[0]["response_format"] == {"type": "json_object"}


def cena_bucket(cena):
    return NS(nome=BUCKET, reviews_analisadas=cena.revs)


def test_reforco_de_item_diz_o_que_e():
    r = RI._REFORCO_ITEM
    assert "APENAS o `exemplo_parafraseado`" in r and "NÃO refaz a análise do bucket" in r
    assert "anti-spoiler" in r and "sem aspas" in r and "pt-BR" in r
    assert "palavras separadas por espaço" in r


# ---------------------------------------------------------------- mesmas validações

def test_aspas_sao_removidas_como_na_sintese(cena, livro):
    livro.configurar([_json('Elogiam o "contexto histórico" e a mensagem da obra.')])
    r = _rodar(cena)
    assert '"' not in r["depois"] and "contexto histórico" in r["depois"]
    tema = next(t for b in _ler(cena.pasta / "bullets.json")["buckets"] if b["bucket"] == BUCKET
                for t in b["temas"] if t["tema"] == TEMA)
    assert tema["aspas_removidas"] is True


def test_quantidade_vaga_e_recusada_e_a_retentativa_leva_o_reforco(cena, livro):
    cli = livro.configurar([_json(VAGA), _json(OUTRO)])
    r = _rodar(cena)
    assert r["depois"] == OUTRO
    assert [t["recusada"] for t in r["tentativas"]] == ["quantidade_pendente", None]
    sistema = [p["messages"][0]["content"] for p in cli.pedidos]
    assert RI.REFORCO_RETENTATIVA not in sistema[0] and sistema[1].endswith(RI.REFORCO_RETENTATIVA)


@pytest.mark.parametrize("resposta,motivo", [
    (_json("The film is praised for its historical context and the message it carries today."), "idioma"),
    (_json("   "), "vazio"),
    (_json(ANTIGO), "igual_ao_anterior"),
])
def test_recusas_individuais(resposta, motivo, cena, livro):
    cli = livro.configurar([resposta, _json(OUTRO)])
    r = _rodar(cena)
    assert r["tentativas"][0]["recusada"] == motivo and r["depois"] == OUTRO
    assert len(cli.pedidos) == 2


def test_json_invalido_e_tema_com_outro_nome_sao_recusados(cena, livro):
    livro.configurar(["isto não é json", _json(OUTRO, tema="Outro nome"), _json(OUTRO)])
    r = _rodar(cena)
    assert [bool(t.get("recusada")) for t in r["tentativas"]] == [True, True, False]


# ---------------------------------------------------------------- recusa e não grava

def _hash_dos_arquivos(pasta):
    return {p.name: p.read_bytes() for p in pasta.iterdir() if p.is_file()}


def test_sem_tentativa_valida_levanta_e_nao_grava_nada(cena, livro):
    livro.configurar(["lixo", "lixo", "lixo"])
    antes = _hash_dos_arquivos(cena.pasta)
    with pytest.raises(RI.RecusaDeItem, match="nenhuma tentativa passou"):
        _rodar(cena)
    assert _hash_dos_arquivos(cena.pasta) == antes
    assert "itens_regerados" not in _ler(cena.pasta / "estado.json")


def test_validador_do_bucket_reprova_e_nao_grava(cena, livro, monkeypatch):
    from espectro24 import validacao_publicado as VP
    monkeypatch.setattr(VP, "validar_publicado", lambda b: {"passa_publicado": False})
    livro.configurar([_json(OUTRO)])
    antes = _hash_dos_arquivos(cena.pasta)
    with pytest.raises(AssertionError, match="reprovou nos validadores"):
        _rodar(cena)
    assert _hash_dos_arquivos(cena.pasta) == antes


def test_exemplo_antigo_ausente_em_eixos_nao_grava(cena, livro):
    d = _ler(cena.pasta / "bullets.json")
    d["eixos"] = {}
    (cena.pasta / "bullets.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    livro.configurar([_json(OUTRO)])
    antes = _hash_dos_arquivos(cena.pasta)
    with pytest.raises(AssertionError, match="não aparece em `eixos`"):
        _rodar(cena)
    assert _hash_dos_arquivos(cena.pasta) == antes


def test_amostra_divergente_recusa_antes_de_chamar(cena, livro, monkeypatch):
    from espectro24 import pipeline as P
    monkeypatch.setattr(P, "amostra_do_bruto",
                        lambda slug, raiz=None: {BUCKET: [NS(texto="outra review") for _ in cena.revs]})
    cli = livro.configurar([_json(OUTRO)])
    with pytest.raises(AssertionError, match="amostra do bucket diverge"):
        _rodar(cena)
    assert cli.pedidos == [] and livro.sessao.resumo()["chamadas"] == 0


def test_tema_inexistente_nao_chama_o_modelo(cena, livro):
    cli = livro.configurar([_json(OUTRO)])
    with pytest.raises(StopIteration):
        RI.regenerar_exemplo(cena.out, SLUG, BUCKET, "Tema que não existe")
    assert cli.pedidos == []


# ---------------------------------------------------------------- livro-caixa e registro

def test_chamada_vai_pelo_livro_caixa(cena, livro):
    livro.configurar([_json(VAGA), _json(OUTRO)])
    _rodar(cena)
    r = livro.sessao.resumo()
    assert r["chamadas"] == 2 and r["custo_usd"] > 0 and r["reservas_pendentes_usd"] == 0
    linhas = [json.loads(l) for l in (livro.pasta / "uso.jsonl").read_text().splitlines()]
    assert {(l["estagio"], l["slug"], l["modelo_efetivo"]) for l in linhas} == {("sintese", SLUG, MODEL)}


def test_registro_em_estado_com_antes_e_depois(cena, livro):
    livro.configurar([_json(OUTRO)])
    _rodar(cena)
    est = _ler(cena.pasta / "estado.json")
    (reg,) = est["itens_regerados"]
    assert (reg["tipo"], reg["bucket"], reg["tema"]) == ("exemplo", BUCKET, TEMA)
    assert reg["antes"] == ANTIGO and reg["depois"] == OUTRO and reg["tentativas"] == 1
    assert reg["celulas_eixos"] == 1 and reg["em_utc"]
    assert est["validadores_bullets"][BUCKET]["passa_publicado"] is True


def test_nao_escreve_fora_da_pasta_de_execucao(cena, livro):
    """Nem `resultado/`, nem `frontend/`, nem `dados/publicados.json`: só `<out>/<slug>/`."""
    antes = {p: p.stat().st_mtime_ns for p in
             [RAIZ / "dados" / "publicados.json", RAIZ / "resultado" / "casablanca.json"]}
    livro.configurar([_json(OUTRO)])
    _rodar(cena)
    assert {p: p.stat().st_mtime_ns for p in antes} == antes
