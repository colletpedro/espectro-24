"""[v1.9.6, §2.3] Passada SELETIVA sob `by/added-earliest`.

A v1.9.5 mediu, e o número é o argumento inteiro deste módulo: sob `by/added`
a mediana do catálogo precisa de **1783 páginas** para cobrir um ano, contra
um teto de plataforma de **256**. As 256 páginas expostas são as ~3000 adições
mais recentes — o passado do filme não é alcançável por POSIÇÃO. É alcançável
por ORDENAÇÃO: `by/added-earliest` devolve a listagem crescente desde 2012.

**Seletiva, não uniforme.** `dias_por_100_paginas` (§3[B']) separa duas
populações: filme de fluxo baixo já tem anos de cobertura dentro das primeiras
páginas de `by/added`, e uma passada nele gastaria requisição comprando o que
já existe. Só quem está abaixo do limiar recebe.

Este módulo não inventa mecanismo nenhum de coleta: reusa `coletar_superset`
com outro `ordenacao` e outro orçamento. O que ele acrescenta é a DECISÃO de
quem recebe e a costura do `meta.json` para que a passada some ao bruto sem
apagar a descrição da coleta base (§3[B'], "Duas ordenações no mesmo bruto").
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .alocacao import alocar, orcamento_paginas
from .bruto import atualizar_meta, carregar
from .collector import coletar_superset
from .config import (
    BUCKETS,
    COTA_POR_BUCKET,
    DADOS_BRUTO_DIR,
    LIMIAR_PASSADA_ANTIGA,
    NIVEIS_ORDENADOS,
    ORCAMENTO_PAGINAS_PASSADA,
    ORDENACAO_PASSADA,
)


@dataclass
class Decisao:
    """Por que este filme recebe (ou não) a passada — sempre com o número."""
    slug: str
    recebe: bool
    motivo: str
    dias_por_100_paginas: float | None


def decidir(slug: str, metrica: dict | None,
            limiar: float = LIMIAR_PASSADA_ANTIGA) -> Decisao:
    """`recebe ⇔ dias_por_100_paginas < limiar` (§2.3).

    Filme **sem métrica** fica de FORA, e a escolha é deliberada: sem métrica
    não há critério, e incluir "por precaução" gastaria requisição numa aposta.
    A passada é ganho de cobertura, não pré-requisito de nada.
    """
    valor = (metrica or {}).get("dias_por_100_paginas")
    if valor is None:
        return Decisao(slug, False, "sem_metrica (menos de 2 páginas com data)", None)
    if valor < limiar:
        return Decisao(slug, True, f"dias_por_100_paginas={valor:.1f} < {limiar:g}",
                       valor)
    return Decisao(slug, False,
                   f"dias_por_100_paginas={valor:.1f} >= {limiar:g} — a "
                   "profundidade sob by/added já cobre mais de um ano", valor)


def decidir_lote(metricas: dict[str, dict | None],
                 limiar: float = LIMIAR_PASSADA_ANTIGA
                 ) -> tuple[list[Decisao], list[Decisao]]:
    """`(dentro, fora)` — os dois lados, ambos com número, nunca só o de dentro."""
    decisoes = [decidir(slug, metricas[slug], limiar) for slug in sorted(metricas)]
    return ([d for d in decisoes if d.recebe], [d for d in decisoes if not d.recebe])


def coletar_passada(fetcher, slug: str, *,
                    raiz: str | Path = DADOS_BRUTO_DIR,
                    ordenacao: str = ORDENACAO_PASSADA,
                    orcamento_paginas_bucket: int = ORCAMENTO_PAGINAS_PASSADA,
                    cota_por_bucket: int = COTA_POR_BUCKET,
                    motivo: str = "") -> dict:
    """Coleta a fatia sob `ordenacao` e SOMA ao bruto do filme. Devolve o bloco
    de telemetria gravado em `meta["passadas"]`.

    **Sem sondagem de profundidade e sem extensão por déficit** (§2.3): a
    sondagem existe para ancorar o bloco PROFUNDO, e sob ordenação CRESCENTE o
    fundo da listagem é o material mais RECENTE — exatamente o que a coleta
    base já tem; a extensão mede déficit contra a cota de análise, que a
    passada não está tentando fechar.

    **Sem requisição de histograma:** ele é lido do `meta.json` da coleta base
    (é o acumulado da vida do filme, não muda por ordenação) — a alocação e o
    orçamento por nível saem dele, pelas MESMAS funções da coleta base.

    O `alvo_por_nivel` passado adiante só governa o orçamento do completamento
    [C'] (§3[B], v1.9.2), e é o mesmo da coleta base **de propósito**: as duas
    pontas do bruto precisam ter passado pela mesma política de completamento
    para que o perfil de uma seja comparável ao da outra. Sob orçamento menor,
    o material antigo pareceria mais curto por artefato de medição.
    """
    meta_base, _ = carregar(slug, raiz=raiz)
    if not meta_base:
        raise ValueError(
            f"{slug}: passada exige coleta base — o histograma, o orçamento e a "
            "ordenação de referência vêm do meta.json que ela grava.")

    hist = {float(k): v for k, v in (meta_base.get("histograma_bruto") or {}).items()}
    hist = hist or None

    alocacao = alocar({nome: cota_por_bucket for nome in BUCKETS}, hist)
    alvo_por_nivel = {n: 0 for n in NIVEIS_ORDENADOS}
    for por_nivel in alocacao.values():
        alvo_por_nivel.update(por_nivel)

    orc = orcamento_paginas({nome: orcamento_paginas_bucket for nome in BUCKETS},
                            hist)
    teto_por_nivel = {n: orcamento_paginas_bucket for n in NIVEIS_ORDENADOS}
    for por_nivel in orc.values():
        teto_por_nivel.update(por_nivel)

    entrada: dict = {}

    def costurar_meta(meta_exec: dict) -> dict:
        """Preserva o meta da coleta BASE e registra a passada na lista.

        Sem isto, `persistir` sobrescreveria `orcamento_paginas_por_nivel` (que
        a seleção LÊ para achar a fronteira raso/profundo, §3[C2]),
        `paginas_gastas_por_nivel`, `profundidade_sondagem` e `janela_temporal`
        da coleta que produziu a maior parte do material.
        """
        entrada.update({
            "ordenacao": ordenacao,
            "coletado_em": meta_exec["coletado_em"],
            "versao_coletor": meta_exec["versao_coletor"],
            "motivo": motivo,
            "orcamento_paginas_por_bucket": orcamento_paginas_bucket,
            "orcamento_paginas_por_nivel": meta_exec["orcamento_paginas_por_nivel"],
            "paginas_gastas_por_nivel": meta_exec["paginas_gastas_por_nivel"],
            "motivo_parada_por_nivel": meta_exec["motivo_parada_por_nivel"],
            "contagem_bruta_por_nivel": meta_exec["contagem_bruta_por_nivel"],
            "requisicoes": getattr(fetcher, "n_network", 0),
            "retentativa": (fetcher.telemetria_retentativa()
                            if hasattr(fetcher, "telemetria_retentativa") else None),
        })
        final = dict(meta_base)
        # A lista descreve ORDENAÇÕES PRESENTES no bruto, não um log de
        # execuções: repetir a mesma ordenação substitui o item dela.
        outras = [p for p in final.get("passadas", [])
                  if p.get("ordenacao") != ordenacao]
        final["passadas"] = outras + [entrada]
        return final

    res = coletar_superset(
        fetcher, slug, alvo_por_nivel, hist, raiz=raiz, ordenacao=ordenacao,
        teto_paginas=teto_por_nivel, extensao=None,
        profundidade_por_nivel=None, sondagem=None, meta_hook=costurar_meta)

    # `n_novas`/`n_atualizadas` só existem DEPOIS da escrita (é `persistir` que
    # os conta, mesclando com o disco), então entram como um segundo passe —
    # sem rede, sem reescrever `reviews.jsonl`.
    entrada["n_novas"] = res.n_novas
    entrada["n_atualizadas"] = res.n_atualizadas
    entrada["n_total_no_bruto"] = res.n_reviews
    entrada["requisicoes"] = getattr(fetcher, "n_network", 0)
    if hasattr(fetcher, "telemetria_retentativa"):
        entrada["retentativa"] = fetcher.telemetria_retentativa()
    meta_final = dict(res.meta)
    meta_final["passadas"] = [p for p in meta_final.get("passadas", [])
                              if p.get("ordenacao") != ordenacao] + [entrada]
    atualizar_meta(slug, {"passadas": meta_final["passadas"]}, raiz=raiz)

    # A janela temporal descreve o bruto ACUMULADO, e a passada acabou de
    # mudá-lo — deixá-la como estava seria publicar uma janela que não é mais a
    # do material em disco. Zero rede: lê o que acabou de ser persistido.
    from .pipeline import atualizar_dias_por_100_paginas, atualizar_janela_temporal

    atualizar_janela_temporal(slug, raiz=raiz)
    atualizar_dias_por_100_paginas(slug, raiz=raiz)
    return entrada
