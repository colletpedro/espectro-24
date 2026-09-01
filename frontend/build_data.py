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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTADO = ROOT / "resultado"
FRONTEND = ROOT / "frontend"

sys.path.insert(0, str(ROOT / "src"))
from espectro24 import eixos as _E  # noqa: E402


# [v1.9.34] O bloco `eixos` do filme sintético passa a ser GERADO pelo mesmo
# código que gera o dos 35 reais, em vez de escrito à mão.
#
# **O motivo é um defeito medido, não elegância.** O bloco hardcoded já havia
# divergido: seus `bullet_de` não eram os que `eixos.bullets()` produziria
# para aquelas frequências. Numa mudança de schema ele fica para trás **e o
# fixture continua verde**, testando um schema que não existe mais — que é
# exatamente o modo de falha que um fixture de conformidade deve impedir.
# Agora ele não pode divergir: é a mesma função.
#
# `fonte_classificacao` e `rotulagem` continuam à mão e são anexados depois —
# eles são fixtures de OUTRA coisa (divergência entre amostra classificada e
# analisada; telemetria de §[D3]) e não têm como sair de uma classificação
# sintética sem inventar uma segunda camada de mentira.
_DEG_FREQ = {
    # bucket: (n, {eixo: quantas reviews carregam})
    "negativas": (7, {"ritmo": 5, "tom_atmosfera": 3}),
    "medianas": (2, {"ritmo": 1, "tom_atmosfera": 1}),
    "positivas": (30, {"ritmo": 6, "som_trilha": 9, "tom_atmosfera": 18}),
}
_DEG_TEMAS = {
    "negativas": {"ritmo": {"tema": "Ritmo arrastado", "exemplo_parafraseado": ""},
                  "tom_atmosfera": {"tema": "Roteiro raso",
                                    "exemplo_parafraseado": ""}},
    "positivas": {"som_trilha": {"tema": "Trilha marcante",
                                 "exemplo_parafraseado": ""},
                  "tom_atmosfera": {"tema": "Atmosfera envolvente",
                                    "exemplo_parafraseado": ""}},
}


def _eixos_do_degradado() -> dict:
    """O bloco `eixos` do filme sintético, pelo caminho de produção.

    **Ele fica ABAIXO DO PISO de `n` (§2.5) e NÃO tem `contraste` — e isso é
    estrutural, não uma escolha desta função.** O bucket `negativas` tem n=7
    para exercitar `estado_piso: sem_numero`, que exige `3 <= n < 8`; o piso do
    estado de contraste é `n >= 10`. **Um filme com bucket `sem_numero` está
    abaixo do piso do contraste POR CONSTRUÇÃO** — não existe fixture que
    exercite os dois ao mesmo tempo.

    **Coberturas que isto MOVE, declaradas:**
    · GANHA a LINHA DE AUSÊNCIA de veredito (`.verdict-absent`), que no mundo
      real só `obsession-2026` exercita.
    · PERDE o fallback de render de `filme.js` (`veredito()`), que era a razão
      declarada de este filme não ter bloco `veredito` desde a v1.9.21. Depois
      da republicação da v1.9.34 nenhum filme real o exercita tampouco — ele
      vira código de compatibilidade sem exercitador. Registrado como lacuna
      conhecida, não escondido: a decisão entre mantê-lo sem teste ou removê-lo
      é do dono do projeto, e não foi tomada aqui.
    """
    cls = {b: {f"{b}:{i}": [e for e, k in eixos.items() if i < k]
               for i in range(n)}
           for b, (n, eixos) in _DEG_FREQ.items()}
    analisadas = {b: set(rs) for b, rs in cls.items()}
    bloco = _E.montar_bloco(cls, analisadas, _DEG_TEMAS)
    bloco["fonte_classificacao"] = {
        "arquivo": "resultado/votacao-3/consenso.jsonl",
        "criterio": "votacao_3_consenso_2_de_3",
        "por_bucket": {
            "negativas": {"n_classificadas": 7, "n_analisadas": 7,
                          "sobreposicao_com_analisadas": 5},
            "medianas": {"n_classificadas": 2, "n_analisadas": 2,
                         "sobreposicao_com_analisadas": 2},
            "positivas": {"n_classificadas": 30, "n_analisadas": 30,
                          "sobreposicao_com_analisadas": 22}}}
    bloco["rotulagem"] = {"n_chamadas": 2, "falharam": [],
                          "fora_da_taxonomia": {}, "houve_retentativa": []}
    # Carimbo que `pipeline.montar_eixos` põe no caminho real e `montar_bloco`
    # não põe (o bloco carrega a PRÓPRIA versão, não a do arquivo). Fixo em
    # 1.9.14 desde sempre neste fixture: ele documenta um bloco ANTIGO, e é
    # essa divergência com o arquivo que a política de carimbo quer visível.
    bloco["spec_version"] = "1.9.14"
    return bloco

def _catalogo() -> list[str]:
    """[v1.9.16] Os 35 slugs de `votacao-3/consenso.jsonl` — a mesma fonte
    única que decide o catálogo em `scripts/publicar_catalogo.py` — em vez
    de uma lista redigitada que podia divergir dele (era só os 3 primeiros
    filmes publicados). `the-invite-2026` continua primeiro por curadoria
    (era o filme novo quando só 3 existiam); os outros 34, alfabético.
    """
    slugs = set()
    for linha in (RESULTADO / "votacao-3" / "consenso.jsonl").read_text(
            encoding="utf-8").splitlines():
        if linha.strip():
            slugs.add(json.loads(linha)["slug"])
    destaque = "the-invite-2026"
    resto = sorted(slugs - {destaque})
    return ([destaque] if destaque in slugs else []) + resto


# Ordem no catálogo da home (curadoria: o filme em destaque primeiro).
CATALOGO = _catalogo()


def _nivel(nivel, n_validas, n_brutas, filtro, spoiler=0, curtas=0):
    return {
        "nivel": nivel, "n_validas": n_validas, "n_brutas": n_brutas,
        "filtro_aplicado": filtro, "n_sem_nota": 0,
        "n_descartadas_spoiler": spoiler, "n_descartadas_curtas": curtas,
        "n_descartadas_truncamento": 0, "paginas_buscadas": 1,
    }


def _filme_degradado():
    """Filme fictício exercitando os 3 modos: reduzido, sem_analise, completo.
    Fica FORA do catálogo — acessível só por filme.html?slug=teste-degradado.

    [v1.9.21] **Ele NÃO tem o bloco `veredito`, e isso é DELIBERADO — não é
    esquecimento.** A partir da v1.9.21 o veredito é gerado na publicação
    (§3[V]) e vem pronto em `f.veredito.texto`; `veredito()` em `filme.js`
    passa a ser o FALLBACK DE RENDER para JSON publicado antes disso. Esse
    caminho de compatibilidade precisa de alguém que o exercite, e os 35
    filmes reais deixam de exercitá-lo assim que forem regerados. É o mesmo
    papel que este filme já cumpre para `sem_numero`/`sem_analise`: ser o
    único lugar onde o estado que o mundo real não tem continua sendo
    testado.

    Se você veio até aqui para "consertar" a ausência do campo, o conserto
    apaga a cobertura. Para testar o caminho NOVO de render, use qualquer
    filme real.
    """
    return {
        "slug": "teste-degradado",
        "data_coleta": "2026-07-20T00:00:00Z",
        "spec_version": "1.3.1",
        "total_reviews_observadas": 41,
        "reviews_url": "https://letterboxd.com/film/teste-degradado/reviews/",
        "ficha": None,  # exercita o caminho sem ficha
        "buckets": [
            {
                "bucket": "negativas", "alvo": 40, "modo": "reduzido",
                "estado_piso": "sem_numero", "n_validas": 7,
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
                "bucket": "medianas", "alvo": 40, "modo": "sem_analise",
                "estado_piso": "sem_analise", "n_validas": 2,
                "niveis": [_nivel(3.0, 1, 2, 150), _nivel(3.5, 1, 1, 0)],
                "temas": [],
                "observacao_geral": "Bucket sem análise temática: apenas 2 review(s) válida(s) (piso é 3).",
                "idioma_invalido": False, "escopo_suspeito": False,
            },
            {
                "bucket": "positivas", "alvo": 40, "modo": "completo",
                "estado_piso": "completa", "n_validas": 30,
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
        # v1.9.14: o bloco de eixos do filme sintético existe para exercitar
        # os estados que os 3 filmes REAIS não têm. É o único lugar onde
        # `sem_numero` (célula com tema e sem número), `sem_analise` (coluna
        # indisponível) e célula VAZIA (eixo que o grupo não menciona)
        # aparecem lado a lado com uma célula normal.
        "eixos": _eixos_do_degradado(),
        "_oculto_do_catalogo": True,
    }


def main():
    filmes = {}
    catalogo_presente = []
    for slug in CATALOGO:
        caminho = RESULTADO / f"{slug}.json"
        if not caminho.exists():
            print(f"  ⚠️  {slug}: sem resultado/{slug}.json — pulado do catálogo")
            continue
        catalogo_presente.append(slug)
        data = json.loads(caminho.read_text(encoding="utf-8"))
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

    payload = {"catalogo": catalogo_presente, "filmes": filmes}
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
    print(f"    catálogo (home): {len(catalogo_presente)} filmes")
    print(f"    + filme oculto de teste: {deg['slug']}")


if __name__ == "__main__":
    main()
