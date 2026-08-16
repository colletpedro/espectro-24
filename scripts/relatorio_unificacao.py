"""[v1.9.15, Entrega 1] Relatório da unificação: sobreposição depois, lift
antes/depois, e se algum veredito de contraste mudou.

Uso:
    python scripts/relatorio_unificacao.py [--antes /tmp/lift_antes_e1.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import eixos as E  # noqa: E402
from espectro24.pipeline import amostra_do_bruto  # noqa: E402

CATALOGO = ["cure", "cidade-de-deus", "the-invite-2026"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--antes", default="/tmp/lift_antes_e1.json")
    args = p.parse_args()

    antes = json.loads(Path(args.antes).read_text(encoding="utf-8")) \
        if Path(args.antes).exists() else {}

    cat = E.carregar_classificacao(E.CONSENSO_PADRAO)

    print("=== Sobreposição depois (deve ser 100% em todo bucket) ===")
    algum_gap = False
    for slug in CATALOGO:
        json_path = RAIZ / "resultado" / f"{slug}.json"
        coleta = json.loads(json_path.read_text(encoding="utf-8")).get("coleta") \
            if json_path.exists() else None
        producao = amostra_do_bruto(slug, coleta=coleta,
                                    raiz=str(RAIZ / "dados" / "bruto"))
        classificadas = {b: set(reviews) for b, reviews in cat.get(slug, {}).items()}
        for bucket, reviews in producao.items():
            ids_prod = {r.id for r in reviews}
            ids_cls = classificadas.get(bucket, set())
            sobreposicao = len(ids_prod & ids_cls)
            n = len(ids_prod)
            ok = "✓" if sobreposicao == n else "✗ FALTA " + str(n - sobreposicao)
            if sobreposicao != n:
                algum_gap = True
            print(f"  {slug:18} {bucket:10} {sobreposicao}/{n}  {ok}")

    print("\n=== Lift antes/depois, por filme ===")
    mudou_contraste = []
    for slug in CATALOGO:
        json_path = RAIZ / "resultado" / f"{slug}.json"
        coleta = json.loads(json_path.read_text(encoding="utf-8")).get("coleta") \
            if json_path.exists() else None
        producao = amostra_do_bruto(slug, coleta=coleta,
                                    raiz=str(RAIZ / "dados" / "bruto"))
        analisadas = {b: {r.id for r in rs} for b, rs in producao.items()}
        # v1.9.15: FILTRADO pela amostra analisada — sem isto o denominador
        # infla com classificação órfã da seleção antiga (a regressão real
        # achada nesta sessão, ver eixos._filtrar_pela_analisada).
        cls_filtrada = E._filtrar_pela_analisada(cat[slug], analisadas)
        freqs = E.frequencias(cls_filtrada)
        lifts_depois = E.lifts(freqs)
        contraste_depois = E.contraste(lifts_depois)
        contraste_antes = (antes.get(slug) or {}).get("contraste", "?")
        marca = " ← MUDOU" if contraste_antes not in (contraste_depois, "?") else ""
        if marca:
            mudou_contraste.append(slug)
        print(f"\n{slug}: contraste {contraste_antes} -> {contraste_depois}{marca}")
        for bucket in sorted(freqs):
            n_antes = (antes.get(slug, {}).get("n_por_bucket") or {}).get(bucket, "?")
            n_depois = freqs[bucket]["n"]
            print(f"  {bucket}: n {n_antes} -> {n_depois}")
            lifts_antes_b = (antes.get(slug, {}).get("lifts") or {}).get(bucket, {})
            lifts_depois_b = {e: l for e, l in lifts_depois[bucket].items() if l > 0}
            eixos_todos = sorted(set(lifts_antes_b) | set(lifts_depois_b))
            for eixo in eixos_todos:
                a = lifts_antes_b.get(eixo)
                d = lifts_depois_b.get(eixo)
                a_pp = f"{float(Fraction(a))*100:.1f}pp" if a else "—"
                d_pp = f"{float(d)*100:.1f}pp" if d else "—"
                if a_pp != d_pp:
                    print(f"    {eixo}: {a_pp} -> {d_pp}")

    print(f"\n{'⚠️  Filmes com sobreposição incompleta ainda' if algum_gap else '✓ Sobreposição 100% em todo bucket dos 3 filmes'}")
    print(f"{'⚠️  Contraste mudou em: ' + str(mudou_contraste) if mudou_contraste else 'Nenhum veredito de contraste mudou'}")


if __name__ == "__main__":
    main()
