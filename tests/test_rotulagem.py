"""[v1.9.14, §D3] Rotulagem de tema por EIXO — a metade qualitativa da linha.

O que [D3] pode fazer: dizer em qual LINHA a frase de um grupo aparece.
O que [D3] NÃO pode fazer: mexer em número. Estes testes cercam as duas
coisas — a segunda com mais força, porque é a fronteira que torna tolerável
uma etapa não calibrada ao lado de uma classificação auditada (§D3, "A
assimetria de validação").
"""
from __future__ import annotations

import json

import pytest

from espectro24 import rotulagem as R
from espectro24.taxonomia import EIXOS, definicoes


def _temas(*nomes):
    return [{"tema": n, "mencoes_aproximadas": 20 - i,
             "n_reviews_analisadas": 40,
             "exemplo_parafraseado": f"exemplo de {n}"}
            for i, n in enumerate(nomes)]


def _cliente(respostas):
    """Dublê de `client_call` que devolve as respostas em sequência."""
    chamadas = []

    def call(system, user, model):
        chamadas.append({"system": system, "user": user, "model": model})
        return respostas[min(len(chamadas) - 1, len(respostas) - 1)]

    call.chamadas = chamadas
    return call


# --- o prompt --------------------------------------------------------------

def test_prompt_traz_as_10_definicoes_da_taxonomia_sem_redigitar():
    """As definições vêm de `taxonomia.definicoes()`, extraídas do SYSTEM que
    entra no `taxonomia_id` — não de uma segunda cópia que possa divergir."""
    system = R.build_system_prompt()
    for eixo, definicao in definicoes().items():
        assert eixo in system
        assert definicao in system


def test_prompt_nao_leva_numero_nenhum():
    """[D3] não vê frequência, denominador nem os outros grupos. Se visse,
    poderia começar a 'corrigir' a contagem — e a contagem é do código."""
    user = R.build_user_message("negativas", _temas("Ritmo lento", "Final fraco"))
    assert "20" not in user and "40" not in user
    assert "Ritmo lento" in user and "Final fraco" in user


def test_prompt_nao_menciona_os_outros_buckets():
    user = R.build_user_message("negativas", _temas("Ritmo lento"))
    assert "medianas" not in user and "positivas" not in user


# --- validação da saída ----------------------------------------------------

def test_rotulo_fora_da_lista_fechada_vira_livre():
    """A regra explícita do dono do projeto: eixo inventado NUNCA entra."""
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "cinematografia_geral"}]})])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    assert saida["rotulos"][0]["eixo"] == "livre"
    assert saida["fora_da_taxonomia"] == ["cinematografia_geral"]


def test_tema_que_o_modelo_esqueceu_vira_livre():
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "ritmo"}]})])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento", "Final fraco"),
                             client_call=call)
    por_tema = {r["tema"]: r["eixo"] for r in saida["rotulos"]}
    assert por_tema == {"Ritmo lento": "ritmo", "Final fraco": "livre"}


def test_tema_inventado_pelo_modelo_e_descartado():
    """O conjunto de temas é do CÓDIGO. Um tema que o modelo devolve e que não
    estava na entrada não pode aparecer na tela."""
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "ritmo"},
        {"tema": "Tema que ninguém pediu", "eixo": "atuacao"}]})])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    assert [r["tema"] for r in saida["rotulos"]] == ["Ritmo lento"]


def test_json_invalido_tem_UMA_retentativa():
    call = _cliente(["isto não é json",
                     json.dumps({"rotulos": [
                         {"tema": "Ritmo lento", "eixo": "ritmo"}]})])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    assert len(call.chamadas) == 2
    assert saida["rotulos"][0]["eixo"] == "ritmo"
    assert saida["houve_retentativa"] is True


def test_json_invalido_duas_vezes_degrada_para_livre_sem_estourar():
    """Falha de [D3] tira a FRASE da célula; não pode derrubar o filme nem
    apagar o número, que não depende dela."""
    call = _cliente(["nada", "também não"])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    assert saida["falhou"] is True
    assert saida["rotulos"][0]["eixo"] == "livre"


def test_bucket_sem_tema_nao_gasta_chamada():
    call = _cliente(["não deveria ser chamado"])
    saida = R.rotular_bucket("negativas", [], client_call=call)
    assert call.chamadas == []
    assert saida["rotulos"] == []


def test_aceita_a_saida_com_cercas_de_codigo():
    call = _cliente(['```json\n{"rotulos": [{"tema": "Ritmo lento", '
                     '"eixo": "ritmo"}]}\n```'])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    assert saida["rotulos"][0]["eixo"] == "ritmo"


# --- a tabela de células ---------------------------------------------------

def test_celulas_ligam_eixo_a_tema_e_exemplo():
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "ritmo"}]})])
    saida = R.rotular_bucket("negativas", _temas("Ritmo lento"), client_call=call)
    celulas = R.celulas_por_eixo(saida["rotulos"])
    assert celulas["ritmo"]["tema"] == "Ritmo lento"
    assert celulas["ritmo"]["exemplo_parafraseado"] == "exemplo de Ritmo lento"


def test_dois_temas_no_mesmo_eixo_o_mais_mencionado_fica_com_a_celula():
    """A célula é uma; o critério de desempate é o número que o CÓDIGO já
    tem (menções), não a ordem em que o modelo respondeu."""
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo arrastado", "eixo": "ritmo"},
        {"tema": "Ritmo lento", "eixo": "ritmo"}]})])
    temas = _temas("Ritmo lento", "Ritmo arrastado")  # o 1º tem mais menções
    saida = R.rotular_bucket("negativas", temas, client_call=call)
    celulas = R.celulas_por_eixo(saida["rotulos"])
    assert celulas["ritmo"]["tema"] == "Ritmo lento"
    assert celulas["ritmo"]["temas_no_mesmo_eixo"] == ["Ritmo arrastado"]


def test_tema_rotulado_livre_nao_ocupa_celula():
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Legenda ruim na sessão", "eixo": "livre"}]})])
    saida = R.rotular_bucket("negativas", _temas("Legenda ruim na sessão"),
                             client_call=call)
    assert R.celulas_por_eixo(saida["rotulos"]) == {}


def test_celulas_so_conhecem_eixos_da_lista_fechada():
    celulas = R.celulas_por_eixo([{"tema": "x", "eixo": "ritmo",
                                   "exemplo_parafraseado": "y",
                                   "mencoes_aproximadas": 1}])
    assert set(celulas) <= set(EIXOS)


# --- o filme inteiro -------------------------------------------------------

def test_rotular_output_percorre_os_tres_buckets():
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "ritmo"}]})])
    output = {"buckets": [{"bucket": b, "n_validas": 40,
                           "temas": _temas("Ritmo lento")}
                          for b in ("negativas", "medianas", "positivas")]}
    tabela, telemetria = R.rotular_output(output, client_call=call)
    assert set(tabela) == {"negativas", "medianas", "positivas"}
    assert len(call.chamadas) == 3
    assert telemetria["n_chamadas"] == 3


def test_bucket_sem_analise_nao_e_rotulado():
    """Piso escalonado: grupo que não pode citar tema não tem célula — mesma
    permissão que o briefing consulta, nunca uma segunda regra (§3[C3])."""
    call = _cliente([json.dumps({"rotulos": []})])
    output = {"buckets": [
        {"bucket": "negativas", "estado_piso": "sem_analise",
         "temas": _temas("Ritmo lento")}]}
    tabela, telemetria = R.rotular_output(output, client_call=call)
    assert tabela["negativas"] == {}
    assert call.chamadas == []


def test_telemetria_registra_o_que_saiu_da_taxonomia():
    call = _cliente([json.dumps({"rotulos": [
        {"tema": "Ritmo lento", "eixo": "vibe"}]})])
    output = {"buckets": [{"bucket": "negativas", "n_validas": 40,
                           "temas": _temas("Ritmo lento")}]}
    _, telemetria = R.rotular_output(output, client_call=call)
    assert telemetria["fora_da_taxonomia"] == {"negativas": ["vibe"]}


def test_falha_de_um_bucket_nao_derruba_os_outros():
    respostas = ["lixo", "lixo",
                 json.dumps({"rotulos": [{"tema": "Ritmo lento",
                                          "eixo": "ritmo"}]})]
    call = _cliente(respostas)
    output = {"buckets": [{"bucket": "negativas", "n_validas": 40,
                           "temas": _temas("Ritmo lento")},
                          {"bucket": "medianas", "n_validas": 40,
                           "temas": _temas("Ritmo lento")}]}
    tabela, telemetria = R.rotular_output(output, client_call=call)
    assert tabela["negativas"] == {}
    assert tabela["medianas"]["ritmo"]["tema"] == "Ritmo lento"
    assert telemetria["falharam"] == ["negativas"]


def test_erro_de_transporte_nao_sobe_pelo_pipeline():
    """[D3] é ADITIVO: sem ele o schema perde a frase, nunca o número."""
    def call(system, user, model):
        raise RuntimeError("timeout")
    output = {"buckets": [{"bucket": "negativas", "n_validas": 40,
                           "temas": _temas("Ritmo lento")}]}
    tabela, telemetria = R.rotular_output(output, client_call=call)
    assert tabela["negativas"] == {}
    assert telemetria["falharam"] == ["negativas"]
