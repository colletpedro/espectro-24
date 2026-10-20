"""Métricas da síntese definidas no gate 0 (FINETUNE_REGISTRO.md, "Duas métricas").

1. **Taxa de palavra de quantidade**: fração dos `exemplo_parafraseado` com ao
   menos uma expressão da lista CONGELADA `finetune/metricas/palavras_quantidade.txt`
   (sem caixa, palavra inteira, acento como escrito, só as flexões listadas).
2. **Concordância de `mencoes_aproximadas`, treinado × publicado**, por bucket:
   temas pareados um a um (similaridade e5, atribuição húngara, par só acima
   de um limiar), e então diferença absoluta média e tau-b de Kendall. Mede
   IMITAÇÃO DO PROFESSOR, não acerto da contagem.

Nesta fase só o TREINO pode ser medido (`taxa --conjunto treino`). Validação e
teste ficam para as Fases 2 e 4, com os limites pré-registrados lá.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

LISTA = K.FINETUNE_DIR / "metricas" / "palavras_quantidade.txt"
_BORDA_ANTES = r"(?<!\w)"     # antes e depois: nem letra, nem dígito, nem "_" (Unicode)
_BORDA_DEPOIS = r"(?!\w)"


def carregar_lista(caminho: Path = LISTA) -> list[str]:
    fora = []
    for ln in Path(caminho).read_text(encoding="utf-8").split("\n"):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            fora.append(ln)
    if len(fora) != len(set(fora)):
        raise ValueError("expressão repetida na lista")
    return fora


def compilar(expressoes: list[str]) -> re.Pattern:
    alternativas = sorted((re.escape(e).replace(r"\ ", " ") for e in expressoes),
                          key=len, reverse=True)
    return re.compile(_BORDA_ANTES + "(?:" + "|".join(alternativas) + ")" + _BORDA_DEPOIS,
                      re.IGNORECASE)


def tem_palavra_de_quantidade(texto: str, padrao: re.Pattern) -> bool:
    return bool(padrao.search(texto or ""))


def taxa(exemplos: list[str], padrao: re.Pattern) -> dict:
    n = len(exemplos)
    k = sum(tem_palavra_de_quantidade(e, padrao) for e in exemplos)
    return {"n": n, "com_quantidade": k, "taxa": round(k / n, 4) if n else None}


# ---------------------------------------------------------------------------
# Métrica 2 — concordância de menções (definição; só roda na Fase 2/4)
# ---------------------------------------------------------------------------

def parear(temas_a: list[dict], temas_b: list[dict], encoder, limiar: float) -> list[tuple[int, int, float]]:
    """Pareamento um a um entre os temas de dois lados do MESMO bucket:
    cosseno e5 entre `query: tema. exemplo` dos dois lados, atribuição que
    maximiza a soma (húngaro), e só os pares com cosseno ≥ `limiar`."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    if not temas_a or not temas_b:
        return []
    qa = encoder.queries([f"{t['tema']}. {t.get('exemplo_parafraseado') or ''}" for t in temas_a])
    qb = encoder.queries([f"{t['tema']}. {t.get('exemplo_parafraseado') or ''}" for t in temas_b])
    s = np.asarray(qa) @ np.asarray(qb).T
    li, co = linear_sum_assignment(-s)
    return [(int(i), int(j), float(s[i, j])) for i, j in zip(li, co) if s[i, j] >= limiar]


def concordancia_bucket(temas_t: list[dict], temas_p: list[dict], pares) -> dict:
    """DAM = média de |m_T − m_P| nos pares (em reviews e em fração do n);
    tau = tau-b de Kendall entre m_T e m_P nos pares (None com < 3 pares ou
    sem variação num dos lados)."""
    from scipy.stats import kendalltau

    if not pares:
        return {"n_pares": 0, "dam": None, "dam_frac": None, "tau_b": None}
    mt = [temas_t[i]["mencoes_aproximadas"] for i, _, _ in pares]
    mp = [temas_p[j]["mencoes_aproximadas"] for _, j, _ in pares]
    n = temas_p[0].get("n_reviews_analisadas") or 0
    dam = sum(abs(a - b) for a, b in zip(mt, mp)) / len(pares)
    tau = None
    if len(pares) >= 3 and len(set(mt)) > 1 and len(set(mp)) > 1:
        tau = float(kendalltau(mt, mp, variant="b").statistic)
    return {"n_pares": len(pares), "n_temas_t": len(temas_t), "n_temas_p": len(temas_p),
            "dam": round(dam, 3), "dam_frac": round(dam / n, 4) if n else None,
            "tau_b": None if tau is None else round(tau, 4)}


def exemplos_do_conjunto(conjunto: str, split: dict) -> list[str]:
    fora = []
    for s in split[conjunto]:
        for b in K.ler_json(K.RESULTADO_DIR / f"{s}.json")["buckets"]:
            ok, _ = K.bucket_e_exemplo_de_sintese(b)
            if ok:
                fora += [t["exemplo_parafraseado"] for t in b["temas"]]
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("taxa", help="taxa de palavra de quantidade no PUBLICADO de um conjunto")
    t.add_argument("--conjunto", choices=["treino"], required=True,
                   help="só treino nesta fase; validação e teste entram na Fase 2/4")
    t.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    a = ap.parse_args()
    split = K.ler_json(a.split)
    lista = carregar_lista()
    r = taxa(exemplos_do_conjunto(a.conjunto, split), compilar(lista))
    print(json.dumps({"conjunto": a.conjunto, "lista_sha256": K.sha256_arquivo(LISTA),
                      "n_expressoes": len(lista), **r}, ensure_ascii=False))


if __name__ == "__main__":
    main()
