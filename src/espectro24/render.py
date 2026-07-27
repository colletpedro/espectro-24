"""[E] Render — JSON em resultado/<slug>.json + saída no terminal (SPEC §E)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import BASE, SPEC_VERSION
from .models import BucketResult


def reviews_url_de(slug: str) -> str:
    """URL pública da página de reviews do filme (§3[C], v1.1.4)."""
    return f"{BASE}/film/{slug}/reviews/"


# Disclaimer da seção tema-a-tema (v1.4.0). Duas variantes porque a mensagem
# honesta depende do dado disponível: sem distribuição, o leitor precisa ser
# avisado de que os tamanhos NÃO significam prevalência; com distribuição, o
# peso real existe e está exibido, então o aviso vira uma explicação do
# método. Mantidos em sincronia com os mesmos textos no frontend (filme.js).
DISCLAIMER_SEM_DISTRIBUICAO = (
    "grupos de 50 · 20 · 30 reviews são cotas de coleta — "
    "não a proporção real das opiniões"
)
DISCLAIMER_COM_DISTRIBUICAO = (
    "análise em profundidade igual por grupo (50·20·30 reviews); "
    "o peso real de cada faixa está indicado em cada grupo"
)


def disclaimer_de(output: dict) -> str:
    """Escolhe o disclaimer pela presença do dado, não por configuração."""
    return (DISCLAIMER_COM_DISTRIBUICAO if output.get("distribuicao")
            else DISCLAIMER_SEM_DISTRIBUICAO)


def build_output(slug: str, buckets: list[BucketResult], data_coleta: str,
                 origens: dict[str, str], total_observado: int,
                 ficha: dict[str, Any] | None = None,
                 distribuicao=None) -> dict[str, Any]:
    # v1.4.0: share real por bucket, quando a distribuição existe. Ausente
    # (chave não emitida) quando não existe — o consumidor distingue
    # "não coletado" de "coletado e deu 0%". A aplicação é delegada a
    # `aplicar_distribuicao` para que o caminho fresh (aqui) e o caminho
    # --reuse-synthesis (cli.py) produzam EXATAMENTE a mesma estrutura.
    shares = distribuicao.por_bucket if distribuicao else {}
    return {
        "slug": slug,
        "data_coleta": data_coleta,
        "spec_version": SPEC_VERSION,
        "total_reviews_observadas": total_observado,
        # v1.1.4: buckets sem_analise apontam para cá em vez de exibir texto
        # bruto (menor risco de spoiler — ver §3[C]).
        "reviews_url": reviews_url_de(slug),
        # v1.3.0: ficha técnica via TMDB — aditiva, None quando indisponível
        # (busca falhou, chave ausente, filme não encontrado) — ver ficha.py.
        "ficha": ficha,
        # v1.4.0: distribuição REAL de notas (histograma do Letterboxd).
        # None quando indisponível → narrador volta às regras da v1.2.1.
        "distribuicao": distribuicao.metadata() if distribuicao else None,
        "origem_paginas": origens,  # cache | network por chave
        "buckets": [
            {
                "bucket": b.nome,
                "alvo": b.alvo,
                "modo": b.modo,
                "n_validas": b.n_validas,
                **({"share_real": shares[b.nome]} if b.nome in shares else {}),
                "niveis": [lvl.metadata() for lvl in b.niveis],
                "temas": [
                    {
                        "tema": t.tema,
                        "mencoes_aproximadas": t.mencoes_aproximadas,
                        "n_reviews_analisadas": t.n_reviews_analisadas,
                        "exemplo_parafraseado": t.exemplo_parafraseado,
                        "mencoes_clampadas": t.mencoes_clampadas,
                        "mencoes_valor_original": t.mencoes_valor_original,
                        "aspas_removidas": t.aspas_removidas,
                    }
                    for t in b.temas
                ],
                "observacao_geral": b.observacao_geral,
                "idioma_invalido": b.idioma_invalido,
                "escopo_suspeito": b.escopo_suspeito,
            }
            for b in buckets
        ],
    }


def aplicar_distribuicao(output: dict, distribuicao) -> dict:
    """[v1.4.0] Injeta a distribuição num `output` já montado (caminho
    `--reuse-synthesis`, que carrega um JSON de disco em vez de reconstruí-lo).

    Produz a MESMA estrutura que `build_output` monta no caminho fresh:
    bloco global `distribuicao` + `share_real` por bucket. `None` limpa o
    bloco e remove os shares — assim um JSON antigo re-renderizado sem o
    dado não fica com share órfão de uma execução anterior.
    """
    output["distribuicao"] = distribuicao.metadata() if distribuicao else None
    shares = distribuicao.por_bucket if distribuicao else {}
    for b in output.get("buckets", []):
        if b.get("bucket") in shares:
            b["share_real"] = shares[b["bucket"]]
        else:
            b.pop("share_real", None)
    return output


def write_json(output: dict, out_dir: str | Path = "resultado") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{output['slug']}.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def render_terminal(output: dict, tom: str = "estruturado") -> str:
    """Render do terminal (§E). `tom` (v1.2.0, mecanismo de A/B):
    - "estruturado" (default): comportamento histórico — temas + observações.
    - "narrativo": metadados de coleta e avisos (que NUNCA somem — modo
      degradado continua visível) + a prosa; SEM os temas/observações.
    - "ambos": os dois, para o A/B humano.

    Os metadados por bucket e todos os avisos (reduzido, sem_analise, idioma,
    escopo) aparecem nos dois tons; só o detalhe estruturado (bullets de tema
    + observação) é exclusivo do tom estruturado.
    """
    mostrar_estruturado = tom in ("estruturado", "ambos")
    mostrar_narrativo = tom in ("narrativo", "ambos")

    L: list[str] = []
    L.append(f"═══ Espectro 24 — {output['slug']} "
             f"(spec v{output['spec_version']}) ═══")
    ficha = output.get("ficha")
    if ficha:
        generos = ", ".join(ficha.get("generos") or [])
        duracao = f"{ficha['duracao_min']}min" if ficha.get("duracao_min") else "?"
        L.append(f"  {ficha.get('titulo')} ({ficha.get('ano')}) — "
                 f"dir. {ficha.get('diretor')} — {generos} — {duracao} [TMDB]")
        if ficha.get("sinopse_fallback_en"):
            L.append("  ⚠️  ficha: sinopse oficial pt-BR indisponível — usando fallback em inglês.")
    distrib = output.get("distribuicao")
    if distrib:
        L.append(f"  distribuição real: {distrib.get('n_notas_total', 0):,} notas "
                 f"[Letterboxd]".replace(",", "."))
    L.append(f"  ({disclaimer_de(output)})")
    reviews_url = output.get("reviews_url") or reviews_url_de(output["slug"])
    for b in output["buckets"]:
        L.append("")
        decomposicao = " · ".join(
            f"{n['nivel']}★: {n['n_validas']}" for n in b["niveis"]
        )
        # --- metadados + avisos: sempre visíveis, nos dois tons ---
        # v1.4.0: o share real entra no header, com formato IDÊNTICO nos três
        # grupos (neutralidade de TRATAMENTO — a assimetria vem do dado, não
        # da apresentação). Ausente quando não há distribuição.
        share = b.get("share_real")
        share_txt = f"  · ~{share}% das notas" if isinstance(share, int) else ""
        L.append(f"▸ {b['bucket'].upper()}  {b['n_validas']}/{b['alvo']} válidas "
                 f"[{decomposicao}]  modo={b['modo']}{share_txt}")
        filtros = sorted({n["filtro_aplicado"] for n in b["niveis"]})
        L.append(f"  filtro aplicado (chars): {filtros}")

        if b["modo"] == "sem_analise":
            # v1.1.4: exibir contagem + URL da página de reviews, NÃO o texto
            # bruto (§3[C]) — texto integral sem a camada anti-spoiler do LLM
            # é o caminho de maior risco de spoiler; a flag do Letterboxd é
            # autodeclarada.
            L.append(f"  ⚠️  {b['observacao_geral']}")
            L.append(f"  → {b['n_validas']} review(s) disponíveis em {reviews_url}")
            continue
        if b["modo"] == "reduzido":
            L.append(f"  ⚠️  modo reduzido: análise baseada em apenas "
                     f"{b['n_validas']} de {b['alvo']} reviews-alvo — "
                     f"interprete com cautela.")
        if b.get("idioma_invalido"):
            L.append(f"  ⚠️  idioma: saída não confirmadamente em pt-BR mesmo "
                     f"após retentativa — revisar manualmente.")
        if b.get("escopo_suspeito"):
            L.append(f"  ⚠️  escopo: observação geral pode generalizar este "
                     f"recorte para o filme inteiro mesmo após retentativa — "
                     f"revisar manualmente.")

        # --- detalhe estruturado: só no tom estruturado/ambos ---
        if not mostrar_estruturado:
            continue
        for t in b["temas"]:
            L.append(f"    • {t['tema']} — mencionado em ~{t['mencoes_aproximadas']} "
                     f"de {t['n_reviews_analisadas']} reviews")
            L.append(f"        ex.: {t['exemplo_parafraseado']}")
            if t.get("mencoes_clampadas"):
                L.append(f"        ⚠️  LLM reportou {t['mencoes_valor_original']} "
                         f"menções (valor implausível, fora de [0, {t['n_reviews_analisadas']}]) "
                         f"— corrigido pelo código")
            if t.get("aspas_removidas"):
                L.append(f"        ⚠️  exemplo continha aspas de citação — "
                         f"removidas mecanicamente pelo código")
        if b["observacao_geral"]:
            L.append(f"  » {b['observacao_geral']}")

    # --- narrativa: só no tom narrativo/ambos, após metadados+avisos ---
    if mostrar_narrativo:
        L.append("")
        L.append("─────────────────────  NARRATIVA  ─────────────────────")
        narrativa = output.get("narrativa")
        flags = output.get("narrativa_flags") or {}
        if narrativa:
            L.append(narrativa)
        else:
            L.append("(narrativa não gerada)")
        if flags.get("falhou"):
            L.append("  ⚠️  narrativa: falha ao obter texto válido do LLM.")
        if flags.get("idioma_invalido"):
            L.append("  ⚠️  narrativa: idioma não confirmadamente em pt-BR mesmo "
                     "após retentativa — revisar manualmente.")
        if flags.get("escopo_suspeito"):
            L.append("  ⚠️  narrativa: possível generalização de escopo mesmo "
                     "após retentativa — revisar manualmente.")
        if flags.get("prevalencia_suspeita"):
            L.append("  ⚠️  narrativa: possível comparação de tamanho entre grupos / "
                     "prevalência (cota de amostragem apresentada como distribuição "
                     "da recepção) mesmo após retentativa — revisar manualmente.")
        if flags.get("quantificador_suspeito"):
            L.append("  ⚠️  narrativa: \"quase todos\"/\"praticamente todos\" usado sem "
                     "nenhum tema do filme ter fração ≥80% mesmo após retentativa — "
                     "revisar manualmente.")
        if flags.get("peso_nao_ancorado"):
            L.append("  ⚠️  narrativa: havia distribuição real, mas algum grupo não foi "
                     "ancorado no seu peso (rótulo nem percentual) mesmo após "
                     "retentativa — revisar manualmente.")
        if flags.get("consenso_suspeito"):
            L.append("  ⚠️  narrativa: consensos_usados citou grupo/tema inexistente no "
                     "relatório mesmo após retentativa — revisar manualmente.")
        if flags.get("vocabulario_peso_suspeito"):
            L.append("  ⚠️  narrativa: rótulo de peso escrito como \"das reviews\"/"
                     "\"do público\"/\"dos espectadores\" em vez de \"das notas\" mesmo "
                     "após retentativa — o peso vem do histograma de NOTAS; "
                     "revisar manualmente.")
        if flags.get("perspectiva_nao_marcada"):
            L.append("  ⚠️  narrativa: algum grupo com marcação de perspectiva exigida "
                     "ficou sem marcador (ou com trecho inexistente/tardio) mesmo "
                     "após retentativa — revisar manualmente.")
        if flags.get("aspas_removidas"):
            L.append("  ⚠️  narrativa: aspas de citação removidas mecanicamente.")

        # v1.3.1: bloco compacto de consensos_usados — artefato de revisão
        # humana do MOVIMENTO 2 (a propriedade é consenso real, ou invenção?).
        consensos = output.get("consensos_usados") or []
        if consensos:
            L.append("")
            L.append("Consensos do movimento 2:")
            for c in consensos:
                grupos = ", ".join(c.get("grupos_de_origem") or [])
                temas = "; ".join(c.get("temas_de_origem") or [])
                L.append(f"  • {c.get('propriedade')} — grupos: {grupos} — temas: {temas}")

        # v1.4.1: bloco compacto de quantificadores_usados — mesmo padrão do
        # bloco acima. Cada par declarado vem com a CONFERÊNCIA contra a
        # fração real do tema (o número é o que torna a telemetria útil; um
        # par sozinho não diria se está inflado).
        quantificadores = output.get("quantificadores_usados") or []
        if quantificadores:
            from .synthesize import conferencia_quantificador
            L.append("")
            L.append("Quantificadores do movimento 3:")
            for q in quantificadores:
                tema = q.get("tema", "")
                conf = conferencia_quantificador(output, tema)
                if conf is None:
                    detalhe = "⚠️  tema inexistente no relatório"
                else:
                    pct, rotulo = conf
                    detalhe = f"fração real {pct}% → rótulo: {rotulo}"
                L.append(f"  • \"{q.get('quantificador')}\" — tema: {tema} "
                         f"({detalhe})")

        # v1.5.0: bloco compacto de marcadores_perspectiva — mesmo padrão.
        marcadores = output.get("marcadores_perspectiva") or []
        if marcadores:
            L.append("")
            L.append("Marcadores de perspectiva:")
            for m in marcadores:
                L.append(f"  • {m.get('grupo')} — \"{m.get('trecho')}\"")

        # v1.5.0: métricas de fluência — resumo numérico, telemetria de
        # ritmo (não bloqueia, só informa).
        metricas = output.get("metricas_fluencia") or {}
        # v1.6.0: telemetria do passe de edição [E2].
        ed = output.get("edicao_flags") or {}
        if ed:
            L.append("")
            if ed.get("edicao_descartada"):
                L.append(f"  ⚠️  edição [E2] DESCARTADA ({ed.get('motivo_descarte')}) "
                         f"— publicada a narrativa do narrador, sem edição. "
                         f"({ed.get('n_tentativas', 1)} tentativa(s))")
                if ed.get("protegidos_perdidos"):
                    for p in ed["protegidos_perdidos"]:
                        L.append(f"        · trecho perdido: {p}")
                if ed.get("motivos_por_tentativa"):
                    for i, m in enumerate(ed["motivos_por_tentativa"], 1):
                        L.append(f"        · tentativa {i}: {m}")
            else:
                L.append(f"Edição [E2]: aplicada · {ed.get('n_protegidos', 0)} "
                         f"trechos protegidos preservados · retentativa="
                         f"{ed.get('houve_retentativa')} · "
                         f"{ed.get('n_tentativas', 1)} tentativa(s)")
                if ed.get("capitalizacao_ajustada"):
                    L.append("        · capitalização de rótulo movido ajustada")
            if ed.get("similaridade") is not None:
                L.append(f"  similaridade bruta×editada: {ed['similaridade']:.3f}")

        if metricas:
            L.append("")
            L.append(
                "Fluência (diagnóstico, não critério): "
                f"n_frases={metricas.get('n_frases')} · "
                f"media_palavras={metricas.get('media_palavras')} · "
                f"cv_comprimento={metricas.get('cv_comprimento')} · "
                f"frase_mais_curta={metricas.get('frase_mais_curta')} · "
                f"aberturas_repetidas={metricas.get('aberturas_repetidas')} · "
                f"verbos_reporte={metricas.get('verbos_reporte')} · "
                f"adverbios_mente={metricas.get('adverbios_mente')}")

    L.append("")
    L.append(f"Total de reviews observadas na coleta: "
             f"{output['total_reviews_observadas']}")
    return "\n".join(L)
