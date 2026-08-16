"""[v1.9.15] Recalcula a tabela de trade-off da margem (§2.5) sob `>=` exato.

A medição de referência original (`scripts/classificar_10.py::_lifts_do_filme`
+ `_nulo`) calcula lift em PONTO FLUTUANTE (`sum(...) / len(v)`) e compara com
`>=` também em float — o mesmo bug que fez `barbie` e outros 4 filmes caírem
fora da margem de 20pp por engano (§2.5, "A comparação é `>=`, EXATA").

Este script reproduz a MESMA metodologia (mesmo par real, mesma semente de
permutação `f"{SEMENTE}:nulo10"`, mesmas 2000 rodadas embaralhando o rótulo
de bucket DENTRO de cada filme) trocando só a aritmética: `Fraction` em vez
de `float`, do lift real e de cada rodada do nulo. É a correção mínima —
nenhum parâmetro de metodologia muda, só a representação numérica que
produzia a comparação errada.

Uso:
    python scripts/recalcular_margem_exata.py

Escreve `resultado/votacao-3/margem_exata.json` e imprime a tabela.
"""
from __future__ import annotations

import json
import random
import sys
from fractions import Fraction
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import EIXOS, SEMENTE  # noqa: E402
from espectro24 import eixos as E  # noqa: E402
from espectro24.buckets import FRONTEIRAS  # noqa: E402

MARGENS_PP = (15, 20, 25)
N_RODADAS = 2000
SAIDA = RAIZ / "resultado" / "votacao-3" / "margem_exata.json"


def _lifts_do_filme_exato(regs: list[dict]) -> dict[str, Fraction]:
    """MESMA lógica de `classificar_10._lifts_do_filme`, em `Fraction`."""
    porb = {b: [r for r in regs if r["bucket"] == b] for b in FRONTEIRAS}
    saida = {}
    for e in EIXOS:
        f = {b: (Fraction(sum(1 for r in v if e in r["eixos"]), len(v))
                if v else Fraction(0))
            for b, v in porb.items()}
        ordenado = sorted(f.values())
        saida[e] = ordenado[-1] - ordenado[-2]
    return saida


def main() -> None:
    cat = E.carregar_classificacao(E.CONSENSO_PADRAO)
    por_filme = {
        slug: [{"bucket": b, "eixos": ex}
               for b, reviews in buckets.items() for ex in reviews.values()]
        for slug, buckets in cat.items()
    }

    filmes = []
    for slug, regs in sorted(por_filme.items()):
        tamanhos = [sum(1 for r in regs if r["bucket"] == b) for b in FRONTEIRAS]
        if min(tamanhos) < 3:
            continue
        filmes.append((slug, tamanhos,
                       [[e in r["eixos"] for e in EIXOS] for r in regs]))

    n_pares_totais_no_nulo = len(filmes) * len(EIXOS)

    lifts_reais = [(slug, e, l)
                   for slug, _, _ in filmes
                   for e, l in _lifts_do_filme_exato(por_filme[slug]).items()]
    n_pares_totais = len(lifts_reais)

    resultado = {}
    for m_pp in MARGENS_PP:
        m = Fraction(m_pp, 100)
        pares_m = [x for x in lifts_reais if x[2] >= m]
        resultado[m_pp] = {
            "n_pares_acima": len(pares_m),
            "n_filmes_com_ao_menos_um": len({x[0] for x in pares_m}),
        }

    rng = random.Random(f"{SEMENTE}:nulo10")
    acumulado = {m: [] for m in MARGENS_PP}
    for _ in range(N_RODADAS):
        contagem = {m: 0 for m in MARGENS_PP}
        for _slug, tamanhos, marcas in filmes:
            ordem = list(range(len(marcas)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos:
                fatias.append(ordem[ini:ini + t])
                ini += t
            lifts_i = []
            for i in range(len(EIXOS)):
                fs = sorted(Fraction(sum(marcas[j][i] for j in fat), len(fat))
                           for fat in fatias)
                lifts_i.append(fs[-1] - fs[-2])
            for m_pp in MARGENS_PP:
                m = Fraction(m_pp, 100)
                contagem[m_pp] += sum(1 for v in lifts_i if v >= m)
        for m_pp in MARGENS_PP:
            acumulado[m_pp].append(contagem[m_pp])

    for m_pp in MARGENS_PP:
        media_nulo = sum(acumulado[m_pp]) / len(acumulado[m_pp])
        n_reais = resultado[m_pp]["n_pares_acima"]
        frac_ruido = ((media_nulo / n_pares_totais_no_nulo)
                      / (n_reais / n_pares_totais)) if n_reais else None
        resultado[m_pp]["media_nulo"] = media_nulo
        resultado[m_pp]["fracao_ruido_estimada"] = frac_ruido

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(resultado, indent=2), encoding="utf-8")

    print(f"{'margem':>8} {'pares':>7} {'ruído':>8} {'filmes':>10}")
    for m_pp in MARGENS_PP:
        r = resultado[m_pp]
        print(f"{m_pp:>6}pp {r['n_pares_acima']:>7} "
              f"{r['fracao_ruido_estimada']:>7.0%} "
              f"{r['n_filmes_com_ao_menos_um']:>7}/35")
    print(f"\n→ {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
