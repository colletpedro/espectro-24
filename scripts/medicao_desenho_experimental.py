#!/usr/bin/env python3
"""
Medição para desenho experimental — projeto paralelo (fora do Espectro 24).

Entrega 1: distribuição de comprimento sobre TODAS as reviews brutas
persistidas nos 35 filmes do catálogo atual, sem min_chars/cascata/seleção.

Não escreve em dados/, não faz requisição nenhuma. Apenas lê dados/bruto/.
"""
import json
import glob
import statistics as st

RAIZ = "dados/bruto"

EN_STOPWORDS = {
    "the", "and", "is", "was", "this", "movie", "film", "of", "to", "a",
    "it", "in", "that", "for", "with", "but", "not", "on", "as", "i",
    "you", "so", "just", "like", "one", "all", "his", "her", "he", "she",
    "are", "be", "have", "has", "at", "my", "an", "if", "or", "what",
}


def eh_ingles(texto):
    palavras = [p.strip(".,!?;:\"'()").lower() for p in texto.split()]
    palavras = [p for p in palavras if p]
    if not palavras:
        return None  # indeterminado
    acertos = sum(1 for p in palavras if p in EN_STOPWORDS)
    razao = acertos / len(palavras)
    # heurística simples: >=15% das palavras batendo em stopwords comuns de EN
    return razao >= 0.15


def percentis(valores, ps):
    if not valores:
        return {p: None for p in ps}
    ordenados = sorted(valores)
    out = {}
    for p in ps:
        k = (len(ordenados) - 1) * (p / 100)
        f = int(k)
        c = min(f + 1, len(ordenados) - 1)
        if f == c:
            out[p] = ordenados[f]
        else:
            out[p] = ordenados[f] + (ordenados[c] - ordenados[f]) * (k - f)
    return out


def resumo(valores):
    if not valores:
        return None
    ps = percentis(valores, [10, 25, 50, 75, 90, 95])
    return {
        "n": len(valores),
        "mediana": round(ps[50], 1),
        "p10": round(ps[10], 1),
        "p25": round(ps[25], 1),
        "p75": round(ps[75], 1),
        "p90": round(ps[90], 1),
        "p95": round(ps[95], 1),
        "media": round(st.mean(valores), 1),
    }


FAIXAS_PALAVRAS = [
    ("<20", 0, 20), ("20-50", 20, 50), ("50-100", 50, 100),
    ("100-200", 100, 200), ("200-400", 200, 400), ("400-800", 400, 800),
    ("800+", 800, float("inf")),
]


def histograma(valores):
    h = {}
    for nome, lo, hi in FAIXAS_PALAVRAS:
        h[nome] = sum(1 for v in valores if lo <= v < hi)
    return h


def carregar_tudo():
    linhas = []
    for path in sorted(glob.glob(f"{RAIZ}/*/reviews.jsonl")):
        slug = path.split("/")[-2]
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                r["_slug"] = slug
                linhas.append(r)
    return linhas


def main():
    reviews = carregar_tudo()
    print(f"total de reviews brutas carregadas: {len(reviews)} (35 filmes)\n")

    palavras_all, chars_all = [], []
    palavras_en, palavras_outro = [], []
    palavras_recente, palavras_antiga = [], []

    for r in reviews:
        texto = r.get("texto", "") or ""
        n_pal = len(texto.split())
        n_char = r.get("n_chars", len(texto))
        palavras_all.append(n_pal)
        chars_all.append(n_char)

        ingles = eh_ingles(texto)
        if ingles is True:
            palavras_en.append(n_pal)
        elif ingles is False:
            palavras_outro.append(n_pal)

        origem = r.get("ordenacao_origem") or "by/added"
        if origem == "by/added-earliest":
            palavras_antiga.append(n_pal)
        else:
            palavras_recente.append(n_pal)

    print("=== Palavras — geral ===")
    print(json.dumps(resumo(palavras_all), indent=2, ensure_ascii=False))
    print("\n=== Caracteres — geral ===")
    print(json.dumps(resumo(chars_all), indent=2, ensure_ascii=False))

    print("\n=== Histograma de faixas (palavras) — geral ===")
    h = histograma(palavras_all)
    for nome, cnt in h.items():
        pct = 100 * cnt / len(palavras_all)
        print(f"  {nome:>8}: {cnt:6d}  ({pct:5.1f}%)")

    print("\n=== Por idioma (heurística stopwords EN) ===")
    print(f"inglês (n={len(palavras_en)}):")
    print(json.dumps(resumo(palavras_en), indent=2, ensure_ascii=False))
    print(f"outro idioma (n={len(palavras_outro)}):")
    print(json.dumps(resumo(palavras_outro), indent=2, ensure_ascii=False))
    indeterminado = len(palavras_all) - len(palavras_en) - len(palavras_outro)
    print(f"indeterminado (texto vazio): {indeterminado}")

    print("\n=== Por recência (12 filmes com passada by/added-earliest) ===")
    print(f"recente/by-added (n={len(palavras_recente)}):")
    print(json.dumps(resumo(palavras_recente), indent=2, ensure_ascii=False))
    print(f"antiga/by-added-earliest (n={len(palavras_antiga)}):")
    print(json.dumps(resumo(palavras_antiga), indent=2, ensure_ascii=False))

    print("\n=== Histograma de faixas (palavras) — inglês vs outro ===")
    for nome_grupo, dados in [("inglês", palavras_en), ("outro", palavras_outro)]:
        h = histograma(dados)
        print(f" -- {nome_grupo} (n={len(dados)}) --")
        for nome, cnt in h.items():
            pct = 100 * cnt / len(dados) if dados else 0
            print(f"  {nome:>8}: {cnt:6d}  ({pct:5.1f}%)")

    print("\n=== Histograma de faixas (palavras) — recente vs antiga ===")
    for nome_grupo, dados in [("recente", palavras_recente), ("antiga", palavras_antiga)]:
        h = histograma(dados)
        print(f" -- {nome_grupo} (n={len(dados)}) --")
        for nome, cnt in h.items():
            pct = 100 * cnt / len(dados) if dados else 0
            print(f"  {nome:>8}: {cnt:6d}  ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
