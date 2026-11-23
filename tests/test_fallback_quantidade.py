"""Fallback da guarda de quantidade (2026-11-23) e estrutura impossível de `temas`.

A guarda reescreve o que tem regra segura; o que sobra (`quantidade_pendente`, ou palavra da lista
no nome do tema) ganha UMA nova chamada do bucket com reforço, aceita só se mantiver o mesmo número
de temas, não piorar idioma/escopo e reduzir os pendentes. Cliente falso, zero rede."""
import json

import pytest

from espectro24 import synthesize as S
from espectro24.models import BucketResult, LevelResult, Review
from espectro24.synthesize import LLMError, _REFORCO_QUANTIDADE, synthesize_bucket

PENDENTE = "Poucos gostaram do final."          # 'poucos' está na lista e não tem regra segura
LIMPO = "Espectadores não gostaram do final."


def _bucket(n=6):
    lvl = LevelResult(3.0, 150, 1, 0, 0, 0, 0, 0)
    lvl.validas = [Review(viewing_id=f"viewing:{i}", rating=3.5, text=f"review {i} completa",
                          truncated=False, full_text_url=None, spoiler=False,
                          full_text=f"review {i} completa com mais texto") for i in range(n)]
    return BucketResult(nome="medianas", alvo=40, modo="completo", niveis=[lvl])


def _resp(exemplos, nomes=None, obs="Este grupo tem opiniões mistas."):
    nomes = nomes or [f"Tema {i} do filme" for i in range(len(exemplos))]
    return json.dumps({"temas": [{"tema": n, "mencoes_aproximadas": 3, "exemplo_parafraseado": e}
                                 for n, e in zip(nomes, exemplos)],
                       "observacao_geral": obs}, ensure_ascii=False)


class Cliente:
    def __init__(self, *respostas):
        self.respostas, self.systems = list(respostas), []

    def __call__(self, system, user, model):
        self.systems.append(system)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _rodar(cliente, **kw):
    return synthesize_bucket(_bucket(), client_call=cliente, model="m", **kw)


def test_sem_pendente_uma_chamada_e_sem_marca():
    c = Cliente(_resp(["A fotografia chama atenção.", "A trilha é marcante."]))
    b = _rodar(c)
    assert len(c.systems) == 1 and b.quantidade_fallback is None


def test_pendente_aceito_quando_a_segunda_resposta_limpa_e_mantem_os_bullets():
    c = Cliente(_resp([PENDENTE, "A trilha é marcante."]), _resp([LIMPO, "A trilha é marcante."]))
    b = _rodar(c)
    assert len(c.systems) == 2
    assert c.systems[1] == c.systems[0] + _REFORCO_QUANTIDADE
    assert b.quantidade_fallback == "aceito"
    assert [t.exemplo_parafraseado for t in b.temas] == [LIMPO, "A trilha é marcante."] or \
        sorted(t.exemplo_parafraseado for t in b.temas) == sorted([LIMPO, "A trilha é marcante."])
    assert not any(t.quantidade_pendente for t in b.temas)


def test_recusa_se_mudar_o_numero_de_bullets():
    c = Cliente(_resp([PENDENTE, "A trilha é marcante."]), _resp([LIMPO]))
    b = _rodar(c)
    assert b.quantidade_fallback == "recusado_n_bullets"
    assert len(b.temas) == 2 and any(t.quantidade_pendente for t in b.temas)


def test_recusa_se_ainda_pendente():
    c = Cliente(_resp([PENDENTE, "A trilha é marcante."]), _resp([PENDENTE, "A trilha é marcante."]))
    b = _rodar(c)
    assert b.quantidade_fallback == "recusado_sem_ganho"


def test_recusa_se_a_segunda_nao_parseia():
    c = Cliente(_resp([PENDENTE]), "isto não é json")
    b = _rodar(c)
    assert b.quantidade_fallback == "recusado_json"
    assert b.temas and b.temas[0].quantidade_pendente


def test_erro_da_chamada_extra_nao_derruba_o_bucket_valido():
    c = Cliente(_resp([PENDENTE]), LLMError("servidor caiu"))
    b = _rodar(c)
    assert b.quantidade_fallback == "recusado_erro_chamada" and len(b.temas) == 1


def test_recusa_se_a_segunda_piora_o_idioma():
    ingles = "The cinematography is great and the pacing is slow for most of the runtime here."
    c = Cliente(_resp([PENDENTE, "A trilha é marcante."]),
                _resp([ingles, ingles], obs="This group has mixed opinions about the film overall."))
    b = _rodar(c)
    assert b.quantidade_fallback == "recusado_validacao" and not b.idioma_invalido


def test_desligado_nao_chama():
    c = Cliente(_resp([PENDENTE]))
    b = _rodar(c, fallback_quantidade=False)
    assert len(c.systems) == 1 and b.quantidade_fallback is None


def test_palavra_da_lista_no_nome_do_tema_tambem_dispara():
    c = Cliente(_resp(["A trilha é marcante."], nomes=["Muitos elogios à trilha"]),
                _resp(["A trilha é marcante."], nomes=["Elogios à trilha"]))
    b = _rodar(c)
    assert len(c.systems) == 2 and b.quantidade_fallback == "aceito"
    assert b.temas[0].tema == "Elogios à trilha"


def test_estrutura_impossivel_de_temas_vira_json_invalido_e_retenta():
    c = Cliente(json.dumps({"temas": [3, 5], "observacao_geral": "x"}), _resp(["A trilha é marcante."]))
    b = _rodar(c)
    assert len(c.systems) == 2 and len(b.temas) == 1


def test_estrutura_impossivel_duas_vezes_e_a_falha_de_sempre():
    ruim = json.dumps({"temas": [3, 5]})
    b = _rodar(Cliente(ruim, ruim))
    assert b.observacao_geral == "Falha ao obter JSON válido do LLM." and not b.temas


# --- o provider `local` só entra por pedido explícito ---------------------------

def test_local_so_por_pedido_explicito(monkeypatch):
    from espectro24.config import PROVIDER_ENV_KEYS
    assert "local" not in PROVIDER_ENV_KEYS
    for env in PROVIDER_ENV_KEYS.values():
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "x")
    assert S.detect_provider() == "deepseek"           # a detecção por chave nunca escolhe o local
    assert S.detect_provider("local") == "local"       # e o local não pede chave
    assert S.PROVIDER_CLIENTS["local"] is S.local_client_call


def test_local_nao_serve_a_prosa():
    with pytest.raises(S.ProviderError):
        S._resolve_call_and_model(None, None, "local", prosa=True)
