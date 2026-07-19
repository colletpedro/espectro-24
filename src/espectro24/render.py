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


def build_output(slug: str, buckets: list[BucketResult], data_coleta: str,
                 origens: dict[str, str], total_observado: int,
                 ficha: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "origem_paginas": origens,  # cache | network por chave
        "buckets": [
            {
                "bucket": b.nome,
                "alvo": b.alvo,
                "modo": b.modo,
                "n_validas": b.n_validas,
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
    reviews_url = output.get("reviews_url") or reviews_url_de(output["slug"])
    for b in output["buckets"]:
        L.append("")
        decomposicao = " · ".join(
            f"{n['nivel']}★: {n['n_validas']}" for n in b["niveis"]
        )
        # --- metadados + avisos: sempre visíveis, nos dois tons ---
        L.append(f"▸ {b['bucket'].upper()}  {b['n_validas']}/{b['alvo']} válidas "
                 f"[{decomposicao}]  modo={b['modo']}")
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
        if flags.get("aspas_removidas"):
            L.append("  ⚠️  narrativa: aspas de citação removidas mecanicamente.")

    L.append("")
    L.append(f"Total de reviews observadas na coleta: "
             f"{output['total_reviews_observadas']}")
    return "\n".join(L)
