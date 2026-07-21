#!/usr/bin/env python3
"""Gera frontend/js/data.js e frontend/data/*.json a partir dos JSONs de
resultado/ (fonte da verdade do pipeline). NÃO faz parte do pacote Python —
é só um passo de geração do site estático (roda offline, zero rede).

Embute os dados como `window.ESPECTRO_DATA` para o site abrir por file://
sem esbarrar em CORS de fetch. Também copia os JSONs crus para data/ (útil
para inspeção/deploy), mas o caminho primário do site é o embutido.

Inclui um filme SINTÉTICO degradado (`teste-degradado`) que NÃO aparece no
catálogo da home — serve só para exercitar os modos reduzido/sem_analise no
render (buckets do mundo real são todos `completo`).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTADO = ROOT / "resultado"
FRONTEND = ROOT / "frontend"

# Ordem no catálogo da home (curadoria: o filme novo primeiro).
CATALOGO = ["the-invite-2026", "cure", "cidade-de-deus"]


def _nivel(nivel, n_validas, n_brutas, filtro, spoiler=0, curtas=0):
    return {
        "nivel": nivel, "n_validas": n_validas, "n_brutas": n_brutas,
        "filtro_aplicado": filtro, "n_sem_nota": 0,
        "n_descartadas_spoiler": spoiler, "n_descartadas_curtas": curtas,
        "n_descartadas_truncamento": 0, "paginas_buscadas": 1,
    }


def _filme_degradado():
    """Filme fictício exercitando os 3 modos: reduzido, sem_analise, completo.
    Fica FORA do catálogo — acessível só por filme.html?slug=teste-degradado."""
    return {
        "slug": "teste-degradado",
        "data_coleta": "2026-07-20T00:00:00Z",
        "spec_version": "1.3.1",
        "total_reviews_observadas": 41,
        "reviews_url": "https://letterboxd.com/film/teste-degradado/reviews/",
        "ficha": None,  # exercita o caminho sem ficha
        "buckets": [
            {
                "bucket": "negativas", "alvo": 50, "modo": "reduzido",
                "n_validas": 7,
                "niveis": [
                    _nivel(0.5, 2, 5, 50), _nivel(1.0, 2, 6, 150),
                    _nivel(1.5, 1, 3, 0), _nivel(2.0, 1, 2, 150),
                    _nivel(2.5, 1, 2, 150),
                ],
                "temas": [
                    {"tema": "Ritmo arrastado", "mencoes_aproximadas": 4,
                     "n_reviews_analisadas": 7,
                     "exemplo_parafraseado": "Parte deste grupo achou o ritmo lento demais para sustentar o interesse.",
                     "mencoes_clampadas": False, "mencoes_valor_original": None,
                     "aspas_removidas": False},
                    {"tema": "Roteiro raso", "mencoes_aproximadas": 3,
                     "n_reviews_analisadas": 7,
                     "exemplo_parafraseado": "Alguns sentiram que o roteiro não aprofunda o que promete.",
                     "mencoes_clampadas": False, "mencoes_valor_original": None,
                     "aspas_removidas": False},
                ],
                "observacao_geral": "Poucas reviews neste grupo — leia como indício, não como retrato fechado.",
                "idioma_invalido": False, "escopo_suspeito": False,
            },
            {
                "bucket": "medianas", "alvo": 20, "modo": "sem_analise",
                "n_validas": 2,
                "niveis": [_nivel(3.0, 1, 2, 150), _nivel(3.5, 1, 1, 0)],
                "temas": [],
                "observacao_geral": "Bucket sem análise temática: apenas 2 review(s) válida(s) (piso é 3).",
                "idioma_invalido": False, "escopo_suspeito": False,
            },
            {
                "bucket": "positivas", "alvo": 30, "modo": "completo",
                "n_validas": 30,
                "niveis": [_nivel(4.0, 10, 14, 150), _nivel(4.5, 10, 13, 150),
                           _nivel(5.0, 10, 12, 150)],
                "temas": [
                    {"tema": "Atmosfera envolvente", "mencoes_aproximadas": 18,
                     "n_reviews_analisadas": 30,
                     "exemplo_parafraseado": "A maioria deste grupo destaca uma atmosfera que prende do início ao fim.",
                     "mencoes_clampadas": False, "mencoes_valor_original": None,
                     "aspas_removidas": False},
                    {"tema": "Trilha marcante", "mencoes_aproximadas": 9,
                     "n_reviews_analisadas": 30,
                     "exemplo_parafraseado": "Muitos elogiam a trilha sonora como parte central da experiência.",
                     "mencoes_clampadas": False, "mencoes_valor_original": None,
                     "aspas_removidas": False},
                ],
                "observacao_geral": "As reviews positivas convergem em uma experiência sensorial forte.",
                "idioma_invalido": False, "escopo_suspeito": False,
            },
        ],
        "narrativa": (
            "Este é um exemplo sintético para demonstrar o modo degradado. "
            "Entre quem não gostou, uma parte apontou ritmo arrastado e roteiro raso, "
            "mas o grupo é pequeno demais para conclusões firmes. As notas medianas "
            "quase não apareceram nesta coleta. Já entre quem gostou, a maioria "
            "destaca a atmosfera envolvente e muitos elogiam a trilha marcante."
        ),
        "narrativa_flags": {
            "idioma_invalido": False, "escopo_suspeito": False,
            "prevalencia_suspeita": False, "quantificador_suspeito": False,
            "consenso_suspeito": False, "aspas_removidas": False, "falhou": False,
        },
        "consensos_usados": [],
        "_oculto_do_catalogo": True,
    }


def main():
    filmes = {}
    for slug in CATALOGO:
        data = json.loads((RESULTADO / f"{slug}.json").read_text(encoding="utf-8"))
        # aliviar o peso: origem_paginas não é usado no frontend
        data.pop("origem_paginas", None)
        filmes[slug] = data
        # cópia crua (referência/deploy), sem origem_paginas
        (FRONTEND / "data" / f"{slug}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    deg = _filme_degradado()
    filmes[deg["slug"]] = deg
    (FRONTEND / "data" / f"{deg['slug']}.json").write_text(
        json.dumps(deg, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {"catalogo": CATALOGO, "filmes": filmes}
    js = (
        "// GERADO por frontend/build_data.py — NÃO editar à mão.\n"
        "// Fonte: resultado/*.json (pipeline Espectro 24). Dados embutidos\n"
        "// para o site abrir por file:// sem CORS.\n"
        "window.ESPECTRO_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (FRONTEND / "js" / "data.js").write_text(js, encoding="utf-8")
    print(f"OK: {len(filmes)} filmes embutidos em frontend/js/data.js")
    print(f"    catálogo (home): {CATALOGO}")
    print(f"    + filme oculto de teste: {deg['slug']}")


if __name__ == "__main__":
    main()
