#!/usr/bin/env python3
"""Conferência da regeneração v1.6.0 (Tarefa 10) — organiza números e textos
para leitura humana. NENHUM veredito de qualidade literária.

Compara, por filme: narrativa BRUTA (narrador) × EDITADA (editor), resultado
das checagens mecânicas do §E2, métricas de fluência das duas versões
(diagnóstico, não critério), e as conferências de honestidade que já existiam
(quantificadores, ancoragem de peso, vocabulário "das notas", marcadores).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.synthesize import (  # noqa: E402
    _ancoragem_de_peso_ok,
    _metricas_fluencia,
    _pesos_por_bucket,
    _rotulo_peso_completo,
    _vocabulario_peso_ok,
    conferencia_quantificador,
)

FILMES = ["the-invite-2026", "cure", "cidade-de-deus"]
BACKUP = Path("/private/tmp/claude-501/-Users-pedrocollet-Downloads-espectro-24/"
              "a64a66b1-4988-45db-9492-7d8c9c0a017d/scratchpad/v160")

FRASE_AGRAMATICAL = "Muitos para eles, há uma falta de tensão"
ANACOLUTO_PUBLICADO = "para quem o filme é superestimado e pretensioso, a maioria considerou"


def _fmt_metricas(m: dict) -> str:
    return (f"n_frases={m.get('n_frases')} · media={m.get('media_palavras')} · "
            f"cv={m.get('cv_comprimento')} · curta={m.get('frase_mais_curta')} · "
            f"abert_rep={m.get('aberturas_repetidas')} · "
            f"reporte={m.get('verbos_reporte')} · mente={m.get('adverbios_mente')}")


def main() -> int:
    for slug in FILMES:
        d = json.loads((ROOT / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
        bruta = d.get("narrativa_bruta", "")
        final = d.get("narrativa", "")
        ed = d.get("edicao_flags") or {}
        pesos = _pesos_por_bucket(d)

        print("=" * 78)
        print(f"### {slug}   (spec v{d.get('spec_version')})")
        print("=" * 78)
        ficha = d.get("ficha") or {}
        print(f"diretor: {ficha.get('diretor')!r}  "
              f"(transliterado={ficha.get('diretor_transliterado')})")
        print(f"shares: " + " · ".join(
            f"{k}={v[0]}% -> {_rotulo_peso_completo(v[0])!r}" for k, v in pesos.items()))
        print()

        print("--- EDIÇÃO [E2] ---")
        print(f"  descartada: {ed.get('edicao_descartada')} "
              f"| motivo: {ed.get('motivo_descarte') or '—'}")
        print(f"  n_protegidos: {ed.get('n_protegidos')} "
              f"| retentativa: {ed.get('houve_retentativa')} "
              f"| numeros_alterados: {ed.get('numeros_alterados')}")
        if ed.get("protegidos_perdidos"):
            for p in ed["protegidos_perdidos"]:
                print(f"    perdido: {p!r}")
        print()

        print("--- MÉTRICAS (diagnóstico, NÃO critério) ---")
        print(f"  BRUTA  : {_fmt_metricas(_metricas_fluencia(bruta))}")
        print(f"  EDITADA: {_fmt_metricas(_metricas_fluencia(final))}")
        print()

        print("--- HONESTIDADE no texto FINAL ---")
        print(f"  narrativa_flags: "
              f"{ {k: v for k, v in (d.get('narrativa_flags') or {}).items() if v} or 'todas limpas'}")
        print(f"  ancoragem de peso: {_ancoragem_de_peso_ok(final, pesos)}")
        print(f"  vocabulário 'das notas': {_vocabulario_peso_ok(final, pesos)}")
        # todo rótulo de peso presente?
        for nome, (pct, _rot) in pesos.items():
            alvo = _rotulo_peso_completo(pct)
            print(f"    {nome}: {alvo!r} literal no texto final? "
                  f"{alvo.lower() in final.lower()}")
        print()

        print("--- QUANTIFICADORES declarados × fração real ---")
        for q in d.get("quantificadores_usados") or []:
            conf = conferencia_quantificador(d, q.get("tema", ""))
            det = (f"fração {conf[0]}% -> rótulo {conf[1]!r}" if conf
                   else "TEMA INEXISTENTE")
            print(f"  {q.get('quantificador')!r} — {q.get('tema')} ({det})")
        print()

        print("--- MARCADORES declarados ---")
        for m in d.get("marcadores_perspectiva") or []:
            ok = m.get("trecho", "") in final
            print(f"  [{m.get('grupo')}] literal no final? {ok} — {m.get('trecho')[:70]!r}")
        print()

        if slug == "cure":
            print("--- FRASES QUEBRADAS DO cure ---")
            print(f"  '{FRASE_AGRAMATICAL}...' presente? "
                  f"{FRASE_AGRAMATICAL in final}")
            print(f"  anacoluto publicado na v1.5.0 presente? "
                  f"{ANACOLUTO_PUBLICADO in final}")
            print()

        print("--- NARRATIVA BRUTA (narrador) ---")
        print(bruta or "(ausente)")
        print()
        print("--- NARRATIVA EDITADA (final) ---")
        print(final or "(ausente)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
