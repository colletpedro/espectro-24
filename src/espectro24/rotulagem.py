"""[v1.9.14, §D3] Rotulagem de tema por EIXO — a metade qualitativa da linha.

O alinhamento por linha precisa de duas metades que vivem em lugares
diferentes do pipeline:

    Ritmo — arrasta (24/40) | lento mas justificado (11/40) | hipnótico (19/40)
            └─ FRASE: os `temas` de §D      └─ NÚMERO: a classificação por
               (o que ESTE grupo diz)          review, somada em CÓDIGO (§2.5)

Nada ligava as duas: os temas são texto livre por bucket, a classificação é
por review. **Este módulo é essa ligação, e só ela.**

**A fronteira que torna a etapa tolerável.** [D3] escolhe em qual LINHA a
frase de um grupo aparece; não escolhe, não ajusta e não vê nenhum número. Se
o rótulo estiver errado, a linha erra a FRASE — a frequência daquele eixo
continua sendo a contagem de reviews classificadas, alheia ao que [D3]
decidiu. O modo de falha é de legenda, nunca de aritmética.

**A assimetria de validação, declarada (§D3 na spec).** A classificação de
produção passou por auditoria humana de 100 reviews, votação de 3 passadas e
precisão/recall medidos por eixo. [D3] não passou por nada disso — é um
segundo uso da mesma taxonomia por um prompt nunca medido contra gabarito.
A mitigação adotada é proporcional: são ~50 células nos 3 filmes publicados,
e a tabela `tema → eixo` é conferida à mão antes de publicar.

**Aditivo por construção.** Falha de JSON, rótulo fora da taxonomia, erro de
transporte — nada disso sobe pelo pipeline nem apaga número: o pior caso é
célula sem frase, registrado em telemetria.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from .taxonomia import EIXOS, LIVRE, definicoes

# O estado do piso escalonado (§3[C3]) decide se o grupo pode citar tema. É a
# MESMA permissão que o briefing consulta — importada de lá, não recopiada,
# para que não existam duas regras sobre o que um grupo mal medido pode dizer.
from .briefing import PERMISSOES_POR_ESTADO, _estado_piso

ESTAGIO = "rotulagem"

_INSTRUCOES = """Você associa cada TEMA de um grupo de reviews de cinema a UM eixo de uma taxonomia FECHADA.

Os eixos disponíveis são exatamente estes:

{definicoes}

REGRAS:
1. Devolva EXATAMENTE um eixo para cada tema recebido, na ordem em que os temas chegaram.
2. Use SOMENTE os nomes de eixo listados acima, ou "livre". Qualquer outro nome é inválido.
3. Escolha o eixo do ASSUNTO do tema, não do juízo: "ritmo arrastado" e "ritmo hipnótico" são os dois `ritmo`.
4. Use "livre" quando o tema não couber em nenhum eixo — nunca force um eixo aproximado.
5. NÃO reescreva, NÃO reordene e NÃO invente tema. NÃO conte nada. NÃO comente.

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{{"rotulos": [{{"tema": "...", "eixo": "..."}}]}}"""


def build_system_prompt() -> str:
    """As definições vêm de `taxonomia.definicoes()` — extraídas do SYSTEM que
    entra no `taxonomia_id`, nunca redigitadas aqui."""
    linhas = "\n".join(f"- {eixo}: {d}" for eixo, d in definicoes().items())
    return _INSTRUCOES.format(definicoes=linhas)


def build_user_message(bucket_nome: str, temas: list[dict]) -> str:
    """Só os NOMES dos temas, em ordem.

    Sem menções, sem denominador e sem os outros grupos: [D3] não tem o que
    fazer com número, e um número à vista é convite a "corrigir" a contagem
    que é do código.
    """
    linhas = [f"Grupo: {bucket_nome}", "", "Temas:"]
    linhas += [f"{i}. {t.get('tema')}" for i, t in enumerate(temas, 1)]
    return "\n".join(linhas)


def _valido(eixo: Any) -> str:
    """Lista fechada: o que não estiver nela vira `livre`, nunca eixo novo."""
    return eixo if eixo in EIXOS or eixo == LIVRE else LIVRE


def rotular_bucket(bucket_nome: str, temas: list[dict],
                   client_call: Callable | None = None,
                   model: str | None = None,
                   provider: str | None = None) -> dict[str, Any]:
    """Uma chamada, um bucket. Devolve rótulos + telemetria.

    O conjunto de temas é do CÓDIGO: tema que o modelo esquecer vira `livre`,
    tema que ele inventar é descartado. Uma única retentativa em JSON
    inválido (mesmo orçamento de chamadas de §D); persistindo, degrada para
    `livre` em tudo e marca `falhou`.
    """
    saida = {"bucket": bucket_nome, "rotulos": [], "fora_da_taxonomia": [],
             "houve_retentativa": False, "falhou": False, "n_chamadas": 0}
    if not temas:
        return saida

    call, modelo = _resolver(client_call, model, provider)
    system, user = build_system_prompt(), build_user_message(bucket_nome, temas)

    bruto = None
    for tentativa in range(2):
        saida["n_chamadas"] += 1
        try:
            resposta = call(system, user, modelo)
            bruto = _parse(resposta)
        except Exception:
            bruto = None
        if bruto is not None:
            break
        saida["houve_retentativa"] = True

    por_tema: dict[str, str] = {}
    if bruto is None:
        saida["falhou"] = True
    else:
        for item in bruto.get("rotulos") or []:
            if not isinstance(item, dict):
                continue
            nome = item.get("tema")
            eixo = _valido(item.get("eixo"))
            if eixo == LIVRE and item.get("eixo") not in (LIVRE, None):
                saida["fora_da_taxonomia"].append(item.get("eixo"))
            if nome is not None:
                por_tema.setdefault(nome, eixo)

    for t in temas:
        saida["rotulos"].append({
            "tema": t.get("tema"),
            "eixo": por_tema.get(t.get("tema"), LIVRE),
            "exemplo_parafraseado": t.get("exemplo_parafraseado"),
            "mencoes_aproximadas": t.get("mencoes_aproximadas") or 0,
        })
    return saida


def celulas_por_eixo(rotulos: list[dict]) -> dict[str, dict[str, Any]]:
    """`{eixo: {tema, exemplo_parafraseado, temas_no_mesmo_eixo}}`.

    A célula é UMA. Quando dois temas caem no mesmo eixo, fica com ela o mais
    mencionado — desempate pelo número que o código já tem, não pela ordem em
    que o modelo respondeu. O(s) outro(s) ficam registrados em
    `temas_no_mesmo_eixo`: o tema não some, ele só não vira legenda da linha.
    """
    fora: dict[str, dict[str, Any]] = {}
    for r in sorted(rotulos, key=lambda r: -(r.get("mencoes_aproximadas") or 0)):
        eixo = r.get("eixo")
        if eixo not in EIXOS:
            continue
        if eixo in fora:
            fora[eixo]["temas_no_mesmo_eixo"].append(r.get("tema"))
            continue
        fora[eixo] = {"tema": r.get("tema"),
                      "exemplo_parafraseado": r.get("exemplo_parafraseado"),
                      "temas_no_mesmo_eixo": []}
    return fora


def rotular_output(output: dict, client_call: Callable | None = None,
                   model: str | None = None, provider: str | None = None
                   ) -> tuple[dict[str, dict], dict[str, Any]]:
    """Roda [D3] nos três buckets de um `output` já montado.

    Devolve `({bucket: {eixo: célula}}, telemetria)`. Bucket cujo piso não
    permite citar tema não é rotulado e não gasta chamada — a permissão vem
    de `PERMISSOES_POR_ESTADO`, a mesma do briefing.
    """
    tabela: dict[str, dict] = {}
    telemetria: dict[str, Any] = {"n_chamadas": 0, "falharam": [],
                                  "fora_da_taxonomia": {},
                                  "houve_retentativa": []}
    for b in output.get("buckets", []):
        nome = b.get("bucket")
        if not nome:
            continue
        permissoes = PERMISSOES_POR_ESTADO.get(
            _estado_piso(b), PERMISSOES_POR_ESTADO["sem_analise"])
        if not permissoes["pode_citar_temas"]:
            tabela[nome] = {}
            continue
        r = rotular_bucket(nome, list(b.get("temas") or []),
                           client_call=client_call, model=model,
                           provider=provider)
        telemetria["n_chamadas"] += r["n_chamadas"]
        if r["falhou"]:
            telemetria["falharam"].append(nome)
        if r["fora_da_taxonomia"]:
            telemetria["fora_da_taxonomia"][nome] = r["fora_da_taxonomia"]
        if r["houve_retentativa"]:
            telemetria["houve_retentativa"].append(nome)
        tabela[nome] = celulas_por_eixo(r["rotulos"])
    return tabela, telemetria


# --- transporte: SEMPRE pelo adaptador (§3[D], guard-rail do CI) ----------

def _resolver(client_call, model, provider):
    from .synthesize import (
        PROVIDER_CLIENTS, modelo_do_estagio, provider_do_estagio)

    if client_call is not None:
        from .config import MODEL_DEFAULT
        return client_call, (model or MODEL_DEFAULT)
    p = provider_do_estagio(ESTAGIO, provider)
    return PROVIDER_CLIENTS[p], (model or modelo_do_estagio(ESTAGIO, provider))


def _parse(resposta: str) -> dict | None:
    from .synthesize import _parse_llm_json

    try:
        dados = _parse_llm_json(resposta)
    except Exception:
        return None
    return dados if isinstance(dados, dict) else None
