#!/usr/bin/env python3
"""Experimento (NÃO é bump de versão): avaliar se um LLM local (Ollama)
pode substituir o Gemini na síntese por bucket (§D) — para viabilizar um
catálogo maior sem depender da cota gratuita.

ZERO chamadas Gemini, ZERO requisições Letterboxd, ZERO requisições TMDB:
as reviews do `cure` vêm do cache já coletado em disco (`resultado/cache/`,
`Fetcher(offline=True)` — levanta se faltar qualquer página, nunca busca na
rede), e os prompts são os MESMOS `build_system_prompt`/`build_user_message`
que o pipeline de produção usa — a única variável é o provider.

NÃO toca em `resultado/cure.json` (o gabarito) — grava só em
`resultado/experimento_local/cure__ollama.json`.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import run_pipeline  # noqa: E402
from espectro24.synthesize import ollama_client_call, synthesize_bucket  # noqa: E402

SLUG = "cure"
MODEL = "qwen3-espectro"
OUT_PATH = ROOT / "resultado" / "experimento_local" / "cure__ollama.json"


def _call_instrumentado(log: list[dict]):
    """Envolve `ollama_client_call` para medir tempo e tamanho de CADA
    chamada real (não só por bucket) — `synthesize_bucket` pode fazer até 3
    chamadas por bucket (inicial + retentativa de JSON + retentativa de
    idioma/escopo), e queremos ver cada uma."""
    def _call(system: str, user: str, model: str) -> str:
        t0 = time.time()
        raw = ollama_client_call(system, user, model)
        dt = time.time() - t0
        log.append({"tempo_s": round(dt, 2), "tamanho_resposta_chars": len(raw)})
        print(f"    chamada {len(log)}: {dt:.1f}s, {len(raw)} chars de resposta",
              file=sys.stderr)
        return raw
    return _call


def main() -> int:
    print(f"Carregando reviews de '{SLUG}' do cache (offline, zero rede)...",
          file=sys.stderr)
    fetcher = Fetcher(cache_dir=str(ROOT / "resultado" / "cache"), offline=True)
    buckets, niveis, _distrib = run_pipeline(
        fetcher, SLUG, datetime.now(timezone.utc).isoformat(),
        synth=False, distribuicao=False,
    )
    if fetcher.n_network != 0:
        print(f"ABORTANDO: {fetcher.n_network} requisição(ões) de rede "
              f"seriam feitas — esperado 0.", file=sys.stderr)
        return 1
    print(f"OK: {len(buckets)} buckets carregados, 0 requisições de rede.",
          file=sys.stderr)

    resultado = {
        "slug": SLUG,
        "provider": "ollama",
        "model": MODEL,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "buckets": [],
    }

    t_total0 = time.time()
    for b in buckets:
        print(f"[{b.nome}] {len(b.reviews_analisadas)} reviews — chamando Ollama...",
              file=sys.stderr)
        chamadas_log: list[dict] = []
        call = _call_instrumentado(chamadas_log)
        t0 = time.time()
        try:
            synthesize_bucket(b, client_call=call, model=MODEL)
        except Exception as e:
            print(f"ABORTANDO: Ollama falhou no bucket '{b.nome}': {e}",
                  file=sys.stderr)
            return 1
        dt_bucket = time.time() - t0
        print(f"[{b.nome}] concluído em {dt_bucket:.1f}s "
              f"({len(chamadas_log)} chamada(s)) — {len(b.temas)} tema(s)",
              file=sys.stderr)

        resultado["buckets"].append({
            "bucket": b.nome,
            "alvo": b.alvo,
            "modo": b.modo,
            "n_validas": len(b.reviews_analisadas),
            "tempo_total_s": round(dt_bucket, 2),
            "n_chamadas": len(chamadas_log),
            "chamadas": chamadas_log,
            "idioma_invalido": b.idioma_invalido,
            "escopo_suspeito": b.escopo_suspeito,
            "temas": [asdict(t) for t in b.temas],
            "observacao_geral": b.observacao_geral,
        })

    resultado["tempo_total_s"] = round(time.time() - t_total0, 2)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\nSalvo em {OUT_PATH}", file=sys.stderr)
    print(f"Tempo total: {resultado['tempo_total_s']:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
