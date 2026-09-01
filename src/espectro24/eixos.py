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

from .config import (BUCKETS, MARGEM_LEI_K2, MARGEM_LEI_K2_PAR,
                     MARGEM_N_MINIMO)
from .taxonomia import EIXOS, LIVRE, TAXONOMIA_ID

# Onde a classificação do catálogo vive, relativa à raiz do repositório. É
# DADO, não código: um corpus classificado sob outro `taxonomia_id` mora em
# outro diretório e é recusado no carregamento.
CONSENSO_PADRAO = "resultado/votacao-3/consenso.jsonl"

# [v1.9.16] O consenso DEPOIS do passe de verificação de `impacto_emocional`
# (`scripts/verificador_impacto.py aplicar-producao`) — mesmo diretório (o
# manifesto `amostra.json` é compartilhado, a taxonomia não muda), arquivo
# À PARTE. `CONSENSO_PADRAO` continua sendo a saída CRUA da votação de 3 —
# `estender_classificacao_producao.py` e as ferramentas de auditoria da
# classificação (recálculo de margem, relatório de unificação) leem ele, não
# este. `pipeline.montar_eixos` prefere este arquivo quando ele existe E o
# manifesto ao lado (`verificador_manifesto.json`) confere com o `consenso.jsonl`
# atual — divergência é erro, não fallback silencioso, porque um `consenso.jsonl`
# que cresceu depois da verificação teria reviews novas sem passar pelo passe.
CONSENSO_VERIFICADO = "resultado/votacao-3/consenso_verificado.jsonl"

# Quantos bullets de cada papel (§2.5). Dois de consenso, três de contraste —
# e a lista ENCURTA quando não há eixo acima da margem, em vez de ser
# completada com o próximo colocado.
N_BULLETS_FREQUENCIA = 2
N_BULLETS_CONTRASTE = 3

__all__ = ["EIXOS", "LIVRE", "TAXONOMIA_ID",
           "MARGEM_LEI_K2", "MARGEM_N_MINIMO",
           "CONSENSO_PADRAO", "CONSENSO_VERIFICADO",
           "carregar_classificacao", "frequencias",
           "fracao", "lifts", "n_efetivo", "limiar_pp", "acima_da_margem",
           "contraste", "bullets", "montar_bloco"]


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


def n_efetivo(freqs: dict[str, dict[str, Any]]) -> int:
    """O `n` que governa a margem: o MENOR dos três buckets (§2.5, v1.9.34).

    Não é a média, e a escolha muda estado no catálogo real: `pearl-2022` é
    [27, 40, 40] — média 35,7 (limiar 24,2pp) contra mínimo 27 (limiar
    27,8pp), e a diferença atravessa um passo do quantum.

    A razão é de significado, não de conservadorismo: **o lift é uma DIFERENÇA
    entre buckets**, e a precisão de uma diferença é governada pelo menor dos
    denominadores. Um lift de 25pp entre um bucket de 40 e um de 27 não é mais
    confiável que a metade de 27 que o produziu.

    Buckets vazios não contam — um filme com um bucket sem nenhuma review
    classificada seria `n = 0` e travaria a lei em "nada passa", quando a
    resposta certa é olhar os que existem.
    """
    ns = [f["n"] for f in freqs.values() if f["n"]]
    return min(ns) if ns else 0


def limiar_pp(n: int) -> float:
    """O limiar em PONTOS PERCENTUAIS — **derivado, para exibição e carimbo**.

    Nenhuma decisão lê este número: quem decide é `acima_da_margem`, em
    `Fraction`. Ele existe para o campo `margem.limiar_pp` do JSON e para
    leitura humana, no mesmo estatuto de `freq_pct`/`lift_pp`.
    """
    if n <= 0:
        return float("inf")
    return float(MARGEM_LEI_K2) ** 0.5 / n ** 0.5 * 100


def acima_da_margem(lift: Fraction, n: int) -> bool:
    """A LEI POR `n`, EXATA (§2.5, v1.9.34).

        limiar(n) = 144,4/√n pp   ⟺   lift > 0  e  lift² · n >= 2085136/1000000

    **A forma quadrada existe para eliminar a raiz.** `144,4/√n` é irracional;
    comparar em float jogaria fora a garantia que a v1.9.15 comprou caro
    (nenhuma decisão de estado depende de arredondamento — 5 filmes já caíram
    fora da margem uma vez por `0.2` binário). `lift` é `Fraction`, `n` é
    `int`, e `lift * lift * n >= MARGEM_LEI_K2` é comparação de racionais.

    **A GUARDA DE SINAL É PARTE DA LEI, NÃO OTIMIZAÇÃO (§2.5).** Elevar ao
    quadrado APAGA o sinal e só é monotônico no ramo positivo. Sem ela, um
    lift de −0,5 com n=40 daria `0,25 · 40 = 10 >= 2,085136` — **APROVADO** —,
    e −0,5 significa que o eixo é 50pp MENOS falado naquele grupo que no
    concorrente: o produto publicaria "este é o assunto próprio deste grupo"
    sobre o assunto que o grupo MENOS toca. A afirmação exatamente invertida,
    e ela passa em qualquer teste que só exercite lift positivo.
    `test_lift_nao_positivo_reprova_sempre` existe para isso.

    A ordem importa: `lift <= 0` reprova ANTES da multiplicação.
    """
    if not isinstance(lift, Fraction):
        raise TypeError(
            f"acima_da_margem espera Fraction, recebeu {type(lift).__name__} "
            "— float aqui reintroduz o defeito que a v1.9.15 fechou (§2.5).")
    if lift <= 0:
        return False
    return lift * lift * n >= MARGEM_LEI_K2


def contraste(lifts_do_filme: dict[str, dict[str, Fraction]],
              n: int) -> str | None:
    """`"tematico"` | `"valorativo"` | `None` (§2.5, v1.9.34).

    - `tematico` — algum eixo atinge `limiar(n)` em algum grupo.
    - `valorativo` — nenhum atinge: os três falam das mesmas coisas e
      discordam só no julgamento. É o estado de 29 dos 35 filmes do catálogo,
      e **não é ausência de achado** — é o achado, e repousa sobre a
      estatística mais estável do sistema (frequência, via
      `assunto_compartilhado`).
    - **`None` — `n < MARGEM_N_MINIMO`: o estado NÃO é decidido.** Quem chama
      OMITE a chave; ela não vira `None` serializado, e **nunca** vira
      `valorativo`. Naquele `n` a medição não separa os dois estados, e
      publicar qualquer um seria trocar uma afirmação sem lastro por outra.

    **Todo consumidor precisa distinguir `None` de `"valorativo"`**, e o modo
    de falha é conhecido: um `if estado == "valorativo": ... else:` desatento
    põe o ausente no ramo TEMÁTICO (§2.5, "o defeito que o piso encontrou").
    """
    if n < MARGEM_N_MINIMO:
        return None
    for por_eixo in lifts_do_filme.values():
        for eixo, lift in por_eixo.items():
            if eixo != LIVRE and acima_da_margem(lift, n):
                return "tematico"
    return "valorativo"


# --- seleção de bullets ----------------------------------------------------

def _ordem(eixo: str) -> int:
    return EIXOS.index(eixo) if eixo in EIXOS else len(EIXOS)


def bullets(freqs: dict[str, dict[str, Any]],
            lifts_do_filme: dict[str, dict[str, Fraction]],
            n: int) -> dict[str, list[dict[str, Any]]]:
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
                 if acima_da_margem(lift_do.get(e, Fraction(0)), n)]
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
                 ) -> dict[str, Any] | None:
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

    **[v1.9.34] A margem não é mais parâmetro deste função — ela é DERIVADA
    do próprio dado**, via `n_efetivo` (o menor bucket). Não havia como manter
    `margem_pp` como argumento sem permitir que quem chama passasse um `n` que
    não é o do filme, o que quebraria a promessa de auditabilidade do bloco
    `margem` que ele mesmo carimba.
    """
    if not classificacao:
        return None

    classificacao = _filtrar_pela_analisada(classificacao, analisadas)
    freqs = frequencias(classificacao)
    n = n_efetivo(freqs)
    lifts_do_filme = lifts(freqs)
    papeis = bullets(freqs, lifts_do_filme, n)
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
                # [v1.9.34] A DECISÃO, exata, publicada. `lift_pp` acima é
                # derivado e arredondado a uma casa; até a v1.9.33 dois
                # consumidores (`veredito.py:_maior_lift` e o template de
                # `frontend/js/filme.js`) recalculavam a margem a partir DELE,
                # o que era inofensivo por acidente aritmético enquanto a
                # margem era um inteiro. Com `144,4/√n` irracional o acidente
                # acabou. Este campo é a ÚNICA fonte de verdade sobre "esta
                # célula atinge a margem"; ninguém recalcula (§4, e
                # `tests/test_margem_por_n.py`, testes de envenenamento).
                "acima_da_margem": acima_da_margem(
                    lifts_do_filme[b][eixo], n) if eixo != LIVRE else False,
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

    # [v1.9.34] O carimbo da margem. Critério que o decidiu: **um artefato
    # precisa poder ser auditado SOZINHO**, sem consultar a versão do código
    # que o gerou — daí a lei em forma EXATA (a constante como par de
    # inteiros) e o `n` que de fato governou este filme. `limiar_pp` fica ao
    # lado, derivado, para leitura humana. `margem_lift_pp` sobrevive com o
    # MESMO significado de sempre ("o limiar em pp deste filme"), agora
    # resolvido em vez de constante — manter os consumidores existentes
    # corretos vale mais que quebrá-los em silêncio.
    bloco = {
        "taxonomia_id": TAXONOMIA_ID,
        "margem": {
            "lei": "lift^2 * n >= 2085136/1000000",
            "constante_quadrada": list(MARGEM_LEI_K2_PAR),
            "n": n,
            "limiar_pp": round(limiar_pp(n), 2),
        },
        "margem_lift_pp": round(limiar_pp(n), 2),
        "linhas": linhas,
    }
    # O estado do FILME. `None` (n abaixo do piso) OMITE a chave — ausente é
    # "não medido", nunca `valorativo` (§2.5). Serializar `None` seria pior
    # que omitir: um consumidor que faça `if estado == "valorativo"` trata os
    # dois igual, e um que faça `eixos["contraste"]` precisa QUEBRAR.
    estado = contraste(lifts_do_filme, n)
    if estado is not None:
        bloco["contraste"] = estado
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
