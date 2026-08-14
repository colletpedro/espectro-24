"""Previsão de frequência de produção ao trocar o prompt de classificação.

**A lição que este módulo mecaniza** (padrão da spec: lição vira mecanismo).

Ao promover a variante `A_regra` (2026-08-13), duas previsões de como as
frequências por eixo mudariam foram feitas ANTES de reclassificar o corpus.
Uma errou a direção; a outra acertou. A diferença não foi sorte — foi qual
pergunta cada uma respondia:

    ERRADA — extrapolação de TETO sobre o prompt antigo
        estimado = observado × precisão_antiga / recall_antigo
    Responde "qual seria a frequência se o prompt ANTIGO tivesse recall
    perfeito". É uma estimativa da frequência VERDADEIRA no corpus, e diz
    nada sobre o que um prompt NOVO vai produzir — ele tem erros próprios,
    diferentes, que essa conta não conhece. Previu `expectativa` subindo
    2,02×; ela CAIU para 0,75×.

    CERTA — razão PAREADA entre os dois prompts
        fator = (recall_novo / precisao_novo) / (recall_antigo / precisao_antigo)
        estimado = observado_sob_o_prompt_antigo × fator
    Responde "o que o prompt NOVO produz em relação ao que o antigo
    produzia". Acertou o SINAL em 9 dos 10 eixos e a ordem de grandeza em 8,
    incluindo a queda de `expectativa` (previu 0,79×, veio 0,75×) e a de
    `tom_atmosfera` (previu 0,83×, veio 0,89×).

**Por que a razão pareada funciona.** Para um eixo, a frequência observada
sob um prompt é aproximadamente `freq_verdadeira × recall / precisão`: o
recall diz que fração do sinal real ele captura, e dividir pela precisão
recoloca os falsos positivos que ele acrescenta. A frequência verdadeira do
corpus é a MESMA sob os dois prompts — ela é propriedade das reviews, não do
classificador. Então ela cancela na razão, e sobra só a diferença de
comportamento entre os dois. A extrapolação de teto não cancela nada: ela
tenta estimar a frequência verdadeira, que é justamente a quantidade mais
difícil de estimar e a que menos importa para a pergunta.

**Pré-requisito, e é ele que decide se este módulo se aplica:** precisão e
recall dos DOIS prompts medidos contra o MESMO gabarito humano, no mesmo
conjunto de reviews. É exatamente o que uma validação pareada de variantes
produz (ver `resultado/auditoria-acuracia/variantes/comparacao.json`). Sem
isso, não use este módulo — e não substitua por extrapolação de teto, que
já está registrada como preditor errado. Meça o par primeiro.

**Limites declarados.** (a) O fator é uma razão de razões medida em n=100
reviews: ele prevê sinal e ordem de grandeza, não o segundo decimal.
(b) Ele não modela COMPETIÇÃO entre eixos — na promoção de A_regra, 40% das
reviews que perderam `expectativa` ganharam `impacto_emocional` no mesmo
texto, e nenhum preditor por eixo isolado enxerga isso. (c) Precisão ou
recall zero num dos prompts torna o fator indefinido; a função devolve
`None` para aquele eixo em vez de inventar número.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrevisaoEixo:
    """Previsão para um eixo. `fator` é multiplicativo sobre a frequência
    observada sob o prompt antigo; `None` quando indefinido."""

    eixo: str
    fator: float | None
    freq_antiga: float | None = None
    freq_prevista: float | None = None
    motivo_indefinido: str | None = None


def fator_pareado(precisao_antiga: float | None, recall_antigo: float | None,
                  precisao_nova: float | None, recall_novo: float | None,
                  ) -> tuple[float | None, str | None]:
    """Fator multiplicativo de frequência ao trocar o prompt antigo pelo novo.

    Devolve `(fator, motivo_indefinido)`. O fator é
    `(R_novo/P_novo) / (R_antigo/P_antigo)`; a frequência verdadeira do
    corpus cancela porque é a mesma sob os dois prompts.

    Indefinido — e devolvido como `None`, nunca como número inventado —
    quando falta alguma das quatro medidas, ou quando um denominador é zero:
    recall antigo zero (o eixo não existia na saída do prompt antigo, então
    não há base multiplicativa) ou precisão zero em qualquer um dos dois.
    """
    valores = {"precisao_antiga": precisao_antiga, "recall_antigo": recall_antigo,
               "precisao_nova": precisao_nova, "recall_novo": recall_novo}
    faltando = [k for k, v in valores.items() if v is None]
    if faltando:
        return None, f"medida ausente: {', '.join(sorted(faltando))}"
    if precisao_antiga == 0 or precisao_nova == 0:
        return None, "precisão zero — razão recall/precisão indefinida"
    if recall_antigo == 0:
        return None, ("recall antigo zero — sem base multiplicativa "
                      "(o eixo não aparecia na saída do prompt antigo)")

    razao_antiga = recall_antigo / precisao_antiga
    razao_nova = recall_novo / precisao_nova
    return razao_nova / razao_antiga, None


def prever_frequencias(metricas_antigas: dict[str, dict],
                       metricas_novas: dict[str, dict],
                       freq_observada: dict[str, float] | None = None,
                       ) -> dict[str, PrevisaoEixo]:
    """Previsão por eixo a partir de duas medições PAREADAS.

    `metricas_antigas` e `metricas_novas` mapeiam eixo → dict com as chaves
    `precisao` e `recall`, medidas contra o MESMO gabarito humano (é o
    formato que `auditoria_acuracia.calcular_metricas` produz em
    `geral.por_eixo`, e que `variantes_prompt_curtas` grava por variante).

    `freq_observada` é a frequência de cada eixo no corpus de produção sob o
    prompt ANTIGO. Quando fornecida, a previsão sai também em frequência
    absoluta; quando omitida, sai só o fator.

    Eixos ausentes de qualquer um dos dois lados são devolvidos com
    `fator=None` e motivo — nunca silenciosamente omitidos, para que uma
    taxonomia que ganhou ou perdeu eixo apareça no resultado.
    """
    eixos = sorted(set(metricas_antigas) | set(metricas_novas))
    saida: dict[str, PrevisaoEixo] = {}
    for e in eixos:
        antiga, nova = metricas_antigas.get(e), metricas_novas.get(e)
        if antiga is None or nova is None:
            lado = "novas" if antiga is not None else "antigas"
            saida[e] = PrevisaoEixo(
                eixo=e, fator=None,
                motivo_indefinido=f"eixo ausente nas métricas {lado}")
            continue
        fator, motivo = fator_pareado(
            antiga.get("precisao"), antiga.get("recall"),
            nova.get("precisao"), nova.get("recall"))
        f_ant = (freq_observada or {}).get(e)
        saida[e] = PrevisaoEixo(
            eixo=e, fator=fator, freq_antiga=f_ant,
            freq_prevista=(f_ant * fator
                           if fator is not None and f_ant is not None else None),
            motivo_indefinido=motivo)
    return saida


def acuracia_da_previsao(previsto: dict[str, PrevisaoEixo],
                         fator_real: dict[str, float]) -> dict:
    """Confere a previsão contra o que a reclassificação de fato produziu.

    Existe para que a próxima sessão AUDITE o preditor em vez de confiar
    nele: foi exatamente por medir o preditor anterior contra o resultado
    real que a extrapolação de teto foi descartada. O critério principal é
    ACERTO DE SINAL (subiu/desceu/estável), não erro absoluto — o preditor é
    honesto sobre ordem de grandeza, não sobre o segundo decimal.

    `estavel` é |fator − 1| ≤ 0,05 nos dois lados: sem essa faixa morta,
    um eixo que foi de 1,00× para 1,01× contaria como "erro de sinal".
    """
    def _sinal(f: float) -> str:
        if abs(f - 1.0) <= 0.05:
            return "estavel"
        return "subiu" if f > 1.0 else "caiu"

    linhas, n_sinal, n_ordem, n_comparados = [], 0, 0, 0
    for e, p in sorted(previsto.items()):
        real = fator_real.get(e)
        if p.fator is None or real is None:
            linhas.append({"eixo": e, "fator_previsto": p.fator,
                           "fator_real": real, "comparavel": False,
                           "motivo": p.motivo_indefinido or "fator real ausente"})
            continue
        n_comparados += 1
        ok_sinal = _sinal(p.fator) == _sinal(real)
        # "ordem de grandeza": erro relativo até 25% do fator real.
        ok_ordem = abs(p.fator - real) / real <= 0.25 if real else False
        n_sinal += ok_sinal
        n_ordem += ok_ordem
        linhas.append({
            "eixo": e, "fator_previsto": round(p.fator, 3),
            "fator_real": round(real, 3), "comparavel": True,
            "erro_absoluto": round(abs(p.fator - real), 3),
            "sinal_previsto": _sinal(p.fator), "sinal_real": _sinal(real),
            "acertou_sinal": ok_sinal, "acertou_ordem_de_grandeza": ok_ordem,
        })
    return {
        "n_comparados": n_comparados,
        "acertos_de_sinal": n_sinal,
        "acertos_de_ordem_de_grandeza": n_ordem,
        "por_eixo": linhas,
    }
