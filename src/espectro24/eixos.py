"""[v1.9.14, §2.5; margem corrigida na v1.9.15] Eixos, lift, margem e estado
`contraste`.

**O código soma; ninguém mais.** Toda frequência aqui é `Counter` sobre a
classificação já persistida (`resultado/votacao-3/consenso.jsonl`, votação de
3 passadas, eixo entra se aparece em ≥2 de 3). Nenhum número deste módulo
passa por LLM — o que um LLM faz nesta fase é só escolher a FRASE da célula
(§[D3], `rotulagem.py`), nunca a quantidade.

**Aritmética exata, e o motivo é medido.** Cinco dos 35 filmes do catálogo
têm o melhor lift em EXATAMENTE 20,0pp. A medição de referência
(`scripts/metricas_lift.py`) comparou com `>=` em ponto flutuante e os cinco
caíram fora, porque `0.2` binário é ligeiramente menor que a fração exata —
é daí que veio o número publicado de 13/35 filmes com contraste temático na
v1.9.14. **Correção da v1.9.15:** a comparação é `>=` EXATA (`Fraction`), a
semântica que a medição de referência sempre pretendeu — 18/35 filmes têm
contraste temático. Float só aparece no fim, nos campos DERIVADOS que
existem para exibição (`freq_pct`, `lift_pp`), e nenhuma decisão os lê.

**O denominador é o da amostra CLASSIFICADA.** Até a v1.9.14 essa amostra
NÃO era a mesma que a síntese analisava (`amostra.json` sem a estratificação
por profundidade da v1.9.5) — achado medido e declarado, com sobreposição
mediana de 75% no catálogo. **A v1.9.15 unifica as duas populações** para os
filmes cuja classificação foi estendida (ver `pipeline.amostra_do_bruto` e
`scripts/estender_classificacao_producao.py`): para eles, "classificada" e
"analisada" voltam a ser a mesma coisa, e `fonte_classificacao` reporta
`sobreposicao_com_analisadas == n_classificadas == n_analisadas`. Filmes que
ainda não passaram pela extensão continuam com a divergência antiga,
declarada como sempre.
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

from .config import BUCKETS, MARGEM_LIFT_PP
from .taxonomia import EIXOS, LIVRE, TAXONOMIA_ID

# Onde a classificação do catálogo vive, relativa à raiz do repositório. É
# DADO, não código: um corpus classificado sob outro `taxonomia_id` mora em
# outro diretório e é recusado no carregamento.
CONSENSO_PADRAO = "resultado/votacao-3/consenso.jsonl"

# Quantos bullets de cada papel (§2.5). Dois de consenso, três de contraste —
# e a lista ENCURTA quando não há eixo acima da margem, em vez de ser
# completada com o próximo colocado.
N_BULLETS_FREQUENCIA = 2
N_BULLETS_CONTRASTE = 3

__all__ = ["EIXOS", "LIVRE", "TAXONOMIA_ID", "MARGEM_LIFT_PP",
           "CONSENSO_PADRAO", "carregar_classificacao", "frequencias",
           "fracao", "lifts", "acima_da_margem", "contraste", "bullets",
           "montar_bloco"]


# --- carregamento ----------------------------------------------------------

def carregar_classificacao(caminho: str | Path,
                           taxonomia_id_esperado: str = TAXONOMIA_ID
                           ) -> dict[str, dict[str, dict[str, list[str]]]]:
    """`{slug: {bucket: {id_da_review: [eixos]}}}`, conferindo a taxonomia.

    O `consenso.jsonl` não carrega o `taxonomia_id` linha a linha; quem o
    declara é o `amostra.json` ao lado, produzido pela mesma execução. A
    conferência é obrigatória e a ausência do manifesto é ERRO, não default:
    os nomes dos eixos são os mesmos sob qualquer versão do prompt, então
    classificação obsoleta reaproveitada não se denuncia sozinha — é
    exatamente o silêncio que o versionamento por `taxonomia_id` existe para
    impedir (§2.5).
    """
    caminho = Path(caminho)
    manifesto = caminho.parent / "amostra.json"
    if not manifesto.exists():
        raise ValueError(
            f"{manifesto} ausente: sem ele não há como saber sob qual "
            "taxonomia a classificação foi produzida.")
    declarado = json.loads(manifesto.read_text(encoding="utf-8")).get(
        "taxonomia_id")
    if declarado != taxonomia_id_esperado:
        raise ValueError(
            f"taxonomia divergente: {caminho} foi classificado sob "
            f"{declarado!r} e o código corrente espera "
            f"{taxonomia_id_esperado!r}.")

    fora: dict[str, dict[str, dict[str, list[str]]]] = {}
    with caminho.open(encoding="utf-8") as fh:
        for linha in fh:
            linha = linha.strip()
            if not linha:
                continue
            r = json.loads(linha)
            slug, bucket = r.get("slug"), r.get("bucket")
            if not slug or not bucket:
                continue
            fora.setdefault(slug, {}).setdefault(bucket, {})[r["id"]] = list(
                r.get("eixos") or [])
    return fora


# --- frequência ------------------------------------------------------------

def frequencias(classificacao: dict[str, dict[str, list[str]]]
                ) -> dict[str, dict[str, Any]]:
    """`{bucket: {"n": int, "por_eixo": Counter}}` de UM filme.

    `n` é o número de reviews CLASSIFICADAS do bucket — o denominador que vai
    para a tela. Um eixo repetido na mesma review conta uma vez: a unidade é
    a review, como em toda frequência deste projeto.
    """
    fora: dict[str, dict[str, Any]] = {}
    for bucket, reviews in classificacao.items():
        c: Counter[str] = Counter()
        for eixos in reviews.values():
            for eixo in set(eixos):
                c[eixo] += 1
        fora[bucket] = {"n": len(reviews), "por_eixo": c}
    return fora


def fracao(freq_do_bucket: dict[str, Any], eixo: str) -> Fraction:
    """A frequência do eixo naquele bucket, EXATA. Zero sem denominador."""
    n = freq_do_bucket["n"]
    if not n:
        return Fraction(0)
    return Fraction(freq_do_bucket["por_eixo"].get(eixo, 0), n)


# --- lift ------------------------------------------------------------------

def lifts(freqs: dict[str, dict[str, Any]]
          ) -> dict[str, dict[str, Fraction]]:
    """`{bucket: {eixo: lift}}` — `freq(bucket) − max(freq(outros buckets))`.

    Com um bucket só o lift é ZERO, não a própria frequência: sem outro grupo
    não existe contraste, e devolver a frequência faria um filme de um grupo
    só parecer todo contraste.
    """
    presentes = list(freqs)
    fora: dict[str, dict[str, Fraction]] = {b: {} for b in presentes}
    for eixo in EIXOS:
        por_bucket = {b: fracao(freqs[b], eixo) for b in presentes}
        for b in presentes:
            outros = [v for k, v in por_bucket.items() if k != b]
            fora[b][eixo] = por_bucket[b] - (max(outros) if outros
                                             else por_bucket[b])
    return fora


def acima_da_margem(lift: Fraction, margem_pp: int = MARGEM_LIFT_PP) -> bool:
    """Comparação `>=`, EXATA (§2.5, corrigida na v1.9.15).

    "Atinge a margem" é `>=`: um eixo com exatamente 20,0pp de lift ATINGE a
    margem mínima de 20pp — é a semântica natural de "margem mínima", e é o
    que a medição de referência sempre pretendeu produzir. A v1.9.14 usava
    `>` estrito, o que reproduzia por acidente o MESMO bug de ponto
    flutuante da medição de referência (`0.2 >= 0.2` avaliando falso em
    binário) em vez de corrigi-lo — 5 dos 35 filmes do catálogo têm o
    melhor lift em exatamente 20,0pp e viravam `valorativo` por essa
    coincidência. Sob `>=` exato eles atingem a margem, como sempre
    deveriam.
    """
    return Fraction(lift) >= Fraction(margem_pp, 100)


def contraste(lifts_do_filme: dict[str, dict[str, Fraction]],
              margem_pp: int = MARGEM_LIFT_PP) -> str:
    """`"tematico"` | `"valorativo"` (§2.5).

    `valorativo` = nenhum eixo ATINGE a margem em nenhum grupo: os três falam
    das mesmas coisas e discordam só no veredito. É o estado de 17 dos 35
    filmes do catálogo (v1.9.15, sob `>=` exato) — quase metade, e por isso
    tratado como primeira classe em toda a cadeia, do briefing à tela.
    """
    for por_eixo in lifts_do_filme.values():
        for eixo, lift in por_eixo.items():
            if eixo != LIVRE and acima_da_margem(lift, margem_pp):
                return "tematico"
    return "valorativo"


# --- seleção de bullets ----------------------------------------------------

def _ordem(eixo: str) -> int:
    return EIXOS.index(eixo) if eixo in EIXOS else len(EIXOS)


def bullets(freqs: dict[str, dict[str, Any]],
            lifts_do_filme: dict[str, dict[str, Fraction]],
            margem_pp: int = MARGEM_LIFT_PP
            ) -> dict[str, list[dict[str, Any]]]:
    """2 bullets de maior FREQUÊNCIA + 3 de maior LIFT, por bucket (§2.5).

    **Os dois critérios são INDEPENDENTES, e um eixo pode ganhar os dois.**
    A primeira versão deste código descontava do contraste os eixos já
    escolhidos por frequência, e o efeito apareceu no dado real: em `cure`,
    `tom_atmosfera` tem lift de 40pp nas positivas — o maior contraste do
    filme — e, por ser também o mais falado do grupo, saía rotulado apenas
    como consenso. O leitor perdia exatamente a informação mais rara. Agora o
    eixo aparece UMA vez, com papel `frequencia_e_contraste`: a linha não
    duplica, e nenhum dos dois sinais some.

    Consequência aceita: a lista tem de 0 a 5 linhas, e menos de 5 é
    informação — ou o grupo tem poucos eixos, ou o que ele mais fala é também
    o que só ele fala. Eixo com lift abaixo (ou em cima) da margem não entra
    como contraste; a lista encurta em vez de ser completada com ruído.
    Empate sai pela ordem canônica dos eixos, para que dois filmes com o
    mesmo perfil não saiam em ordens diferentes por acidente de iteração.
    """
    fora: dict[str, list[dict[str, Any]]] = {}
    for bucket, f in freqs.items():
        candidatos = [e for e in EIXOS if f["por_eixo"].get(e, 0) > 0]
        lift_do = lifts_do_filme.get(bucket, {})

        por_freq = sorted(candidatos, key=lambda e: (-fracao(f, e), _ordem(e)))
        de_frequencia = por_freq[:N_BULLETS_FREQUENCIA]

        acima = [e for e in candidatos
                 if acima_da_margem(lift_do.get(e, Fraction(0)), margem_pp)]
        acima.sort(key=lambda e: (-lift_do[e], _ordem(e)))
        de_contraste = acima[:N_BULLETS_CONTRASTE]

        linhas = []
        for eixo in candidatos:
            f_ok, c_ok = eixo in de_frequencia, eixo in de_contraste
            if not (f_ok or c_ok):
                continue
            papel = ("frequencia_e_contraste" if f_ok and c_ok
                     else "frequencia" if f_ok else "contraste")
            linhas.append({"eixo": eixo, "papel": papel})
        # ordem de exibição: contraste primeiro (é o que só este grupo diz),
        # depois consenso; dentro de cada papel, pela força do critério.
        linhas.sort(key=lambda l: (
            0 if l["papel"] != "frequencia" else 1,
            -lift_do.get(l["eixo"], Fraction(0)) if l["papel"] != "frequencia"
            else -fracao(f, l["eixo"]),
            _ordem(l["eixo"])))
        fora[bucket] = linhas
    return fora


# --- o bloco do JSON -------------------------------------------------------

def _pp(valor: Fraction) -> float:
    """Fração → pontos percentuais, arredondado para EXIBIÇÃo.

    Derivado: nenhuma decisão do código lê este número (a comparação com a
    margem é exata, `acima_da_margem`). Uma casa decimal porque o quantum com
    cota 40 é 2,5pp — arredondar para inteiro apagaria metade dos passos
    exprimíveis.
    """
    return round(float(valor) * 100, 1)


def _filtrar_pela_analisada(
    classificacao: dict[str, dict[str, list[str]]],
    analisadas: dict[str, Iterable[str]],
) -> dict[str, dict[str, list[str]]]:
    """[v1.9.15, Entrega 1] O denominador da frequência é a amostra ANALISADA,
    não "tudo que já foi classificado alguma vez" para aquele bucket.

    Achado ao rodar a extensão real: `consenso.jsonl` ACUMULA classificação
    — reviews da seleção antiga (a errada, sem `orcamento_paginas_por_nivel`)
    continuam lá depois que a seleção de produção é estendida, porque
    estender é ADITIVO (§[D3]). Sem este filtro, o denominador de `cure`
    saltava de 40 para 53 (40 antigas + 13 novas), quebrando a promessa da
    unificação — "n=40 continua sendo n=40, só com as 40 certas" — e
    inflando `n` com reviews que a síntese nunca leu.

    Bucket cujo `analisadas` está vazio/ausente NÃO é filtrado: significa que
    quem chamou não tem essa informação (compatibilidade com chamadas que
    não passam `analisadas`, e com filmes fora dos 3 estendidos onde a
    intersecção ainda é o melhor dado disponível).
    """
    fora: dict[str, dict[str, list[str]]] = {}
    for bucket, reviews in classificacao.items():
        ids_analisadas = set(analisadas.get(bucket) or ())
        if ids_analisadas:
            fora[bucket] = {rid: ex for rid, ex in reviews.items()
                            if rid in ids_analisadas}
        else:
            fora[bucket] = reviews
    return fora


def montar_bloco(classificacao: dict[str, dict[str, list[str]]],
                 analisadas: dict[str, Iterable[str]],
                 temas_por_eixo: dict[str, dict[str, dict[str, str]]],
                 margem_pp: int = MARGEM_LIFT_PP) -> dict[str, Any] | None:
    """O bloco global `eixos` do JSON de resultado (§4).

    `analisadas` são os ids da amostra que a SÍNTESE leu, por bucket. Desde a
    v1.9.15 eles também FILTRAM a classificação usada no cálculo — a
    frequência só conta reviews que estão nos dois lados (classificadas E
    analisadas), para que o denominador seja sempre a amostra que a síntese
    de fato leu, nunca "tudo que o consenso acumulou até hoje" (§[D3],
    "Duas populações de 40", corrigido nesta versão).
    `temas_por_eixo` é a saída de §[D3]: `{bucket: {eixo: {tema, exemplo}}}`.

    Devolve `None` quando não há classificação nenhuma — chave ausente no
    JSON distingue "filme não classificado" de "classificado e sem eixo".
    """
    if not classificacao:
        return None

    classificacao = _filtrar_pela_analisada(classificacao, analisadas)
    freqs = frequencias(classificacao)
    lifts_do_filme = lifts(freqs)
    papeis = bullets(freqs, lifts_do_filme, margem_pp)
    papel_por = {b: {l["eixo"]: l["papel"] for l in linhas}
                 for b, linhas in papeis.items()}

    ordem_buckets = [b for b in BUCKETS if b in freqs]
    ordem_buckets += [b for b in freqs if b not in BUCKETS]

    linhas = []
    for eixo in EIXOS:
        if not any(freqs[b]["por_eixo"].get(eixo, 0) for b in ordem_buckets):
            continue
        por_bucket = {}
        for b in ordem_buckets:
            tema = (temas_por_eixo.get(b) or {}).get(eixo) or {}
            por_bucket[b] = {
                "mencoes": freqs[b]["por_eixo"].get(eixo, 0),
                "de_n": freqs[b]["n"],
                "freq_pct": _pp(fracao(freqs[b], eixo)),
                "lift_pp": _pp(lifts_do_filme[b][eixo]),
                "tema": tema.get("tema"),
                "exemplo_parafraseado": tema.get("exemplo_parafraseado"),
                # Os temas do MESMO grupo que caíram neste eixo e não ficaram
                # com a célula (§D3, `celulas_por_eixo`). Viajam junto porque
                # a alternativa é o leitor perder tema: com 6 temas e 10
                # eixos a colisão é frequente — em `cure`/negativas, 6 temas
                # ocupam 3 células. O que não vira legenda continua visível.
                "temas_no_mesmo_eixo": list(tema.get("temas_no_mesmo_eixo")
                                            or []),
            }
        linhas.append({
            "eixo": eixo,
            "por_bucket": por_bucket,
            "bullet_de": {b: papel_por.get(b, {}).get(eixo)
                          for b in ordem_buckets},
        })

    fonte = {}
    diverge = False
    for b in ordem_buckets:
        ids_analisadas = set(analisadas.get(b) or ())
        n_cls = freqs[b]["n"]
        n_ana = len(ids_analisadas)
        sobreposicao = len(ids_analisadas & set(classificacao.get(b, {})))
        fonte[b] = {
            "n_classificadas": n_cls,
            "n_analisadas": n_ana,
            "sobreposicao_com_analisadas": sobreposicao,
        }
        if not (sobreposicao == n_cls == n_ana):
            diverge = True

    bloco = {
        "taxonomia_id": TAXONOMIA_ID,
        "margem_lift_pp": margem_pp,
        "contraste": contraste(lifts_do_filme, margem_pp),
        "linhas": linhas,
    }
    # v1.9.15 (Entrega 1): a chave só existe quando há algo a declarar. Depois
    # da unificação (§[D3]) a amostra classificada e a analisada são a MESMA
    # em todo bucket para os filmes já estendidos — manter o bloco ali seria
    # texto morto (na melhor hipótese) ou uma divergência que não existe mais
    # apresentada como se existisse (na pior). Ausência da chave É a
    # declaração "estas duas populações são a mesma", no mesmo espírito de
    # `share_real` (omitido sem distribuição) e do próprio bloco `eixos`
    # (omitido sem classificação).
    if diverge:
        bloco["fonte_classificacao"] = {
            "arquivo": CONSENSO_PADRAO,
            "criterio": "votacao_3_consenso_2_de_3",
            "por_bucket": fonte,
        }
    return bloco
