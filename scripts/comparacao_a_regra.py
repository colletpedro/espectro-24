"""[Entregas 2 e 5 da promoção de A_regra] Compara o consenso ANTIGO
(`taxonomia_id` `11871105c0d3`, arquivado em
`_arquivo_taxonomia-11871105c0d3/`) contra o consenso NOVO (`ebab2667de74`,
pós A_regra) — MESMO corpus, MESMA votação de 3, MESMA margem de nulo. A
única variável é o prompt.

`votacao_3.entrega2/entrega4/entrega5` comparam contra a passada única do
gate original (`resultado/taxonomia-10/classificacoes.jsonl`) ou fazem uma
checagem específica de `tom_atmosfera` — nenhum dos dois isola "só o prompt
mudou". Este script faz essa comparação isolada: antigo-sob-votação vs
novo-sob-votação, review a review.

Uso:
    python scripts/comparacao_a_regra.py

Saída em `resultado/votacao-3/comparacao_a_regra.json`.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import EIXOS, MARGENS, _lifts_do_filme, _wilson  # noqa: E402
from espectro24.buckets import FRONTEIRAS  # noqa: E402

SAIDA = RAIZ / "resultado" / "votacao-3"
ARQ_ANTIGO = SAIDA / "_arquivo_taxonomia-11871105c0d3" / "consenso.jsonl"
ARQ_NOVO = SAIDA / "consenso.jsonl"
ARQ_AMOSTRA = SAIDA / "amostra.json"
ARQ_SAIDA = SAIDA / "comparacao_a_regra.json"


def _ler(caminho: Path) -> list[dict]:
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _chave(r: dict) -> tuple:
    return (r["slug"], r["bucket"], r["id"])


def _fracao_livre(regs: list[dict]) -> dict:
    n = len(regs)
    k = sum(1 for r in regs if r["eixos"] == ["livre"])
    return {"n": n, "so_livre": k, "fracao": k / n if n else None, "ic95": _wilson(k, n)}


def _fracao_vazio(regs: list[dict]) -> dict:
    n = len(regs)
    k = sum(1 for r in regs if r["eixos"] == [])
    return {"n": n, "vazio": k, "fracao": k / n if n else None, "ic95": _wilson(k, n)}


def _eixos_por_review(regs: list[dict]) -> dict:
    vals = [len([e for e in r["eixos"] if e != "livre"]) for r in regs]
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    mediana = (vals_sorted[n // 2] if n % 2 else
               (vals_sorted[n // 2 - 1] + vals_sorted[n // 2]) / 2) if n else 0.0
    return {"media": sum(vals) / n if n else None, "mediana": mediana,
            "histograma": dict(sorted(Counter(vals).items()))}


def _freq(regs: list[dict], eixo: str) -> float:
    return sum(1 for r in regs if eixo in r["eixos"]) / len(regs) if regs else 0.0


def entrega2(antigo: list[dict], novo: list[dict]) -> dict:
    categorias = list(EIXOS) + ["livre"]
    freq_tab = []
    for e in categorias:
        fa, fn = _freq(antigo, e), _freq(novo, e)
        freq_tab.append({"eixo": e, "freq_antiga": fa, "freq_nova": fn,
                         "diff_pp": (fn - fa) * 100})
    freq_tab.sort(key=lambda x: -x["freq_nova"])

    antigo_ch = {_chave(r): r for r in antigo}
    novo_ch = {_chave(r): r for r in novo}
    comuns = sorted(set(antigo_ch) & set(novo_ch))
    ganhou = perdeu = ambos = identico = 0
    for c in comuns:
        a = set(antigo_ch[c]["eixos"]) - {"livre"}
        b = set(novo_ch[c]["eixos"]) - {"livre"}
        if a == b:
            identico += 1
        elif a < b:
            ganhou += 1
        elif b < a:
            perdeu += 1
        else:
            ambos += 1

    def por_bucket(fn):
        return {b: fn([r for r in novo if r["bucket"] == b]) for b in FRONTEIRAS}

    return {
        "n_antigo": len(antigo), "n_novo": len(novo), "n_comuns": len(comuns),
        "frequencia_por_eixo": freq_tab,
        "eixos_por_review": {"antigo": _eixos_por_review(antigo),
                             "novo": _eixos_por_review(novo)},
        "fracao_livre": {"antigo_global": _fracao_livre(antigo),
                         "novo_global": _fracao_livre(novo),
                         "novo_por_bucket": por_bucket(_fracao_livre)},
        "fracao_consenso_vazio": {"antigo_global": _fracao_vazio(antigo),
                                  "novo_global": _fracao_vazio(novo)},
        "mudanca_de_conjunto": {"n_comuns": len(comuns), "identico": identico,
                                "ganhou_eixo": ganhou, "perdeu_eixo": perdeu,
                                "ganhou_e_perdeu": ambos},
    }


def _lifts_por_filme(regs: list[dict]) -> dict[str, dict]:
    """Para cada filme: lift de cada eixo + qual eixo 'encabeça a linha'
    (maior lift) em cada margem — mesma noção que `classificar_10.relatorio`
    usa para `melhor_eixo`, mas aplicável a QUALQUER lista de regs (antiga
    ou nova), o que o `entrega4` de `votacao_3.py` não expõe."""
    por_filme = defaultdict(list)
    for r in regs:
        por_filme[r["slug"]].append(r)
    saida = {}
    for slug, rr in por_filme.items():
        tam = {b: sum(1 for r in rr if r["bucket"] == b) for b in FRONTEIRAS}
        if min(tam.values()) < 3:
            continue
        d = _lifts_do_filme(rr)
        saida[slug] = {
            "n_por_bucket": tam,
            "lifts": {e: v["lift"] for e, v in d.items()},
            "melhor_eixo": max(d, key=lambda e: d[e]["lift"]),
            "melhor_lift": max(v["lift"] for v in d.values()),
            "encabeca_por_margem": {
                str(m): (max(d, key=lambda e: d[e]["lift"])
                         if max(v["lift"] for v in d.values()) >= m else None)
                for m in MARGENS},
        }
    return saida


def entrega5(antigo: list[dict], novo: list[dict]) -> dict:
    rank_antigo = sorted(EIXOS, key=lambda e: -_freq(antigo, e))
    rank_novo = sorted(EIXOS, key=lambda e: -_freq(novo, e))
    ranking = []
    for pos_novo, e in enumerate(rank_novo, start=1):
        pos_antigo = rank_antigo.index(e) + 1
        ranking.append({
            "eixo": e, "posicao_antiga": pos_antigo, "posicao_nova": pos_novo,
            "movimento": pos_antigo - pos_novo,
            "freq_antiga_pct": round(100 * _freq(antigo, e), 1),
            "freq_nova_pct": round(100 * _freq(novo, e), 1),
        })

    lifts_antigo = _lifts_por_filme(antigo)
    lifts_novo = _lifts_por_filme(novo)
    filmes_comuns = sorted(set(lifts_antigo) & set(lifts_novo))

    trocas_por_margem = {}
    for m in MARGENS:
        m_str = str(m)
        deixou_de_encabecar, passou_a_encabecar, manteve = [], [], []
        for slug in filmes_comuns:
            a = lifts_antigo[slug]["encabeca_por_margem"][m_str]
            n = lifts_novo[slug]["encabeca_por_margem"][m_str]
            if a and a != n:
                deixou_de_encabecar.append({"slug": slug, "eixo_antigo": a,
                                            "eixo_novo": n})
            if n and a != n:
                passou_a_encabecar.append({"slug": slug, "eixo_novo": n,
                                           "eixo_antigo": a})
            if a and n and a == n:
                manteve.append(slug)
        trocas_por_margem[m_str] = {
            "n_filmes_com_algum_eixo_acima": sum(
                1 for slug in filmes_comuns
                if lifts_antigo[slug]["encabeca_por_margem"][m_str]
                or lifts_novo[slug]["encabeca_por_margem"][m_str]),
            "manteve_o_mesmo_eixo_a_frente": len(manteve),
            "deixou_de_encabecar": deixou_de_encabecar,
            "passou_a_encabecar_eixo_diferente": passou_a_encabecar,
        }

    return {
        "ranking_frequencia": ranking,
        "n_filmes_comparados": len(filmes_comuns),
        "trocas_de_eixo_que_encabeca_por_margem": trocas_por_margem,
    }


ARQ_RELATORIO_ANTIGO = SAIDA / "_arquivo_taxonomia-11871105c0d3" / "relatorio.json"
ARQ_RELATORIO_NOVO = SAIDA / "relatorio.json"


def entrega4(rel_antigo: dict, rel_novo: dict) -> dict:
    """Diff direto dos blocos `entrega4_recalibracao_schema` já calculados
    por `votacao_3.cmd_relatorio` para cada taxonomia — nulo de permutação,
    margem, `contraste`. Nenhum recálculo aqui: só compara o que já existe
    nos dois `relatorio.json` (antigo arquivado, novo corrente)."""
    ea, en = rel_antigo["entrega4_recalibracao_schema"], rel_novo["entrega4_recalibracao_schema"]

    por_margem = {}
    for m in MARGENS:
        m_str = str(m)
        pa, pn = ea["por_margem"][m_str], en["por_margem"][m_str]
        por_margem[m_str] = {
            "n_pares_acima": {"antigo": pa["n_pares_acima"], "novo": pn["n_pares_acima"]},
            "n_filmes_com_ao_menos_um": {"antigo": pa["n_filmes_com_ao_menos_um"],
                                         "novo": pn["n_filmes_com_ao_menos_um"]},
            "sem_contraste_n": {"antigo": pa["sem_contraste"]["n"],
                                "novo": pn["sem_contraste"]["n"]},
            "sem_contraste_filmes_antigo_nao_novo": sorted(
                set(pa["sem_contraste"]["filmes"]) - set(pn["sem_contraste"]["filmes"])),
            "sem_contraste_filmes_novo_nao_antigo": sorted(
                set(pn["sem_contraste"]["filmes"]) - set(pa["sem_contraste"]["filmes"])),
            "fracao_ruido_estimada": {"antigo": pa["fracao_ruido_estimada"],
                                      "novo": pn["fracao_ruido_estimada"]},
        }

    nulo_a, nulo_n = ea["nulo_de_permutacao"], en["nulo_de_permutacao"]
    nulo_por_margem = {
        str(m): {"pares_acima_media": {"antigo": nulo_a["pares_acima"][str(m)]["media"],
                                       "novo": nulo_n["pares_acima"][str(m)]["media"]}}
        for m in MARGENS
    }

    return {
        "n_filmes_avaliados": {"antigo": ea["n_filmes_avaliados"], "novo": en["n_filmes_avaliados"]},
        "n_filmes_todos_buckets_40": {"antigo": ea["n_filmes_todos_buckets_40"],
                                      "novo": en["n_filmes_todos_buckets_40"]},
        "n_filmes_algum_sub40": {"antigo": ea["n_filmes_algum_sub40"],
                                 "novo": en["n_filmes_algum_sub40"]},
        "fracao_livre_global": {"antigo": ea["fracao_livre_global"]["fracao"],
                                "novo": en["fracao_livre_global"]["fracao"]},
        "fracao_consenso_vazio_global": {"antigo": ea["fracao_consenso_vazio_global"]["fracao"],
                                         "novo": en["fracao_consenso_vazio_global"]["fracao"]},
        "por_margem": por_margem,
        "nulo_de_permutacao_por_margem": nulo_por_margem,
    }


def main() -> None:
    if not ARQ_ANTIGO.exists():
        raise SystemExit(f"falta {ARQ_ANTIGO} — arquive o consenso antigo antes")
    if not ARQ_NOVO.exists():
        raise SystemExit(f"falta {ARQ_NOVO} — rode `votacao_3.py consenso` primeiro")

    antigo, novo = _ler(ARQ_ANTIGO), _ler(ARQ_NOVO)
    rel = {"taxonomia_antiga": "11871105c0d3", "taxonomia_nova": "ebab2667de74",
           "entrega2": entrega2(antigo, novo), "entrega5": entrega5(antigo, novo)}

    if ARQ_RELATORIO_ANTIGO.exists() and ARQ_RELATORIO_NOVO.exists():
        rel_antigo = json.loads(ARQ_RELATORIO_ANTIGO.read_text(encoding="utf-8"))
        rel_novo = json.loads(ARQ_RELATORIO_NOVO.read_text(encoding="utf-8"))
        rel["entrega4"] = entrega4(rel_antigo, rel_novo)
    else:
        print("AVISO: entrega4 pulada — rode `votacao_3.py relatorio` (novo) "
              "primeiro; o antigo já está arquivado.")
    ARQ_SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")

    e2 = rel["entrega2"]
    print(f"n_antigo={e2['n_antigo']} n_novo={e2['n_novo']} n_comuns={e2['n_comuns']}")
    fl = e2["fracao_livre"]
    print(f"fracao_livre: antigo {fl['antigo_global']['fracao']:.2%} → "
          f"novo {fl['novo_global']['fracao']:.2%}")
    fv = e2["fracao_consenso_vazio"]
    print(f"consenso vazio: antigo {fv['antigo_global']['fracao']:.2%} → "
          f"novo {fv['novo_global']['fracao']:.2%}")
    ep = e2["eixos_por_review"]
    print(f"eixos/review: antigo {ep['antigo']['media']:.2f} → "
          f"novo {ep['novo']['media']:.2f}")
    mc = e2["mudanca_de_conjunto"]
    print(f"mudanca de conjunto (n={mc['n_comuns']}): identico {mc['identico']} · "
          f"ganhou {mc['ganhou_eixo']} · perdeu {mc['perdeu_eixo']} · "
          f"ganhou_e_perdeu {mc['ganhou_e_perdeu']}")
    print(f"→ {ARQ_SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
