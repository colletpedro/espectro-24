#!/usr/bin/env python3
"""Runner instrumentado da bateria de aceite v1 (§5) — Espectro 24.

Roda o pipeline REAL (mesmas funções da CLI: collect_all_levels →
assemble_buckets → synthesize_bucket → build_output/write_json →
render_terminal). A ÚNICA instrumentação é um wrapper de contagem/espaçamento
em volta do `gemini_client_call` real, para:
  - contar EXATAMENTE as chamadas Gemini (a CLI não conta);
  - registrar, por bucket, se o LLM foi chamado — verificação do critério
    §5.3.d (bucket `sem_analise` NÃO deve chamar o LLM).

Uso: python scripts/run_acceptance.py <slug> [--gemini-cap N]
Restrições: delay ≥2s no Letterboxd é do próprio Fetcher; espaçamento ≥10s
entre chamadas Gemini é imposto aqui; 429/503 → 1 backoff de 60s + 1
retentativa; NÃO lê nem imprime o .env.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=ROOT / ".env")

from espectro24.collector import assemble_buckets  # noqa: E402
from espectro24.config import PROVIDER_DEFAULT_MODELS  # noqa: E402
from espectro24.fetcher import AntiBotError, Fetcher  # noqa: E402
from espectro24.pipeline import collect_all_levels, total_observado  # noqa: E402
from espectro24.render import build_output, render_terminal, write_json  # noqa: E402
from espectro24.synthesize import gemini_client_call, synthesize_bucket  # noqa: E402

CACHE_DIR = ROOT / "resultado" / "cache"
OUT_DIR = ROOT / "resultado"
MODEL = PROVIDER_DEFAULT_MODELS["gemini"]  # gemini-2.5-flash (default de produção)
MIN_SPACING_S = 10.0
BACKOFF_S = 60.0


class BudgetExceeded(RuntimeError):
    pass


def _is_rate_limit(exc: Exception) -> bool:
    from google.genai import errors
    return isinstance(exc, errors.APIError) and exc.code in (429, 503)


class CountingGemini:
    """Wrapper de contagem/espaçamento em volta do gemini_client_call real."""

    def __init__(self, cap: int):
        self.cap = cap
        self.calls = 0                 # nº de chamadas reais à API (inclui retentativas)
        self._last_start: float | None = None

    def __call__(self, system: str, user: str, model: str) -> str:
        if self.calls >= self.cap:
            raise BudgetExceeded(f"cap de {self.cap} chamadas Gemini atingido")
        # espaçamento ≥ MIN_SPACING_S entre inícios de chamadas reais
        if self._last_start is not None:
            resta = MIN_SPACING_S - (time.monotonic() - self._last_start)
            if resta > 0:
                time.sleep(resta)
        self._last_start = time.monotonic()
        self.calls += 1
        try:
            return gemini_client_call(system, user, model)
        except Exception as e:
            if not _is_rate_limit(e):
                raise
            print(f"    [gemini] 429/503 — backoff de {BACKOFF_S:.0f}s + 1 "
                  f"retentativa...", file=sys.stderr)
            time.sleep(BACKOFF_S)
            if self.calls >= self.cap:
                raise BudgetExceeded(f"cap de {self.cap} chamadas atingido no backoff")
            self._last_start = time.monotonic()
            self.calls += 1
            return gemini_client_call(system, user, model)


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: run_acceptance.py <slug> [--gemini-cap N]", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    cap = 9
    if "--gemini-cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--gemini-cap") + 1])

    print(f"=== Aceite: {slug} — {datetime.now(timezone.utc).isoformat()} ===",
          file=sys.stderr)

    fetcher = Fetcher(cache_dir=CACHE_DIR)
    gemini = CountingGemini(cap=cap)

    def _on_level(lvl):
        print(f"  [{lvl.nivel}★] {lvl.n_validas} válidas / {lvl.n_brutas} brutas "
              f"/ {lvl.paginas_buscadas}p (filtro {lvl.filtro_aplicado}c, "
              f"spoiler-desc {lvl.n_descartadas_spoiler}, curtas-desc "
              f"{lvl.n_descartadas_curtas}, trunc-desc "
              f"{lvl.n_descartadas_truncamento})", file=sys.stderr)

    try:
        print("Coletando (Letterboxd)...", file=sys.stderr)
        niveis = collect_all_levels(fetcher, slug, on_level=_on_level)
    except AntiBotError as e:
        print(f"\n⛔ ANTI-BOT: {e}\nParando conforme restrição.", file=sys.stderr)
        return 4

    buckets = assemble_buckets(niveis)
    letterboxd_reqs = fetcher.n_network

    # síntese por bucket, rastreando chamadas Gemini por bucket.
    # Falha de um bucket (429 persistente, budget) NÃO descarta a coleta já
    # paga — registra e segue; o JSON é escrito com o que houver.
    por_bucket_gemini = {}
    for b in buckets:
        antes = gemini.calls
        try:
            synthesize_bucket(b, client_call=gemini, model=MODEL)
        except BudgetExceeded as e:
            por_bucket_gemini[b.nome] = gemini.calls - antes
            print(f"\n⛔ {e} — parando síntese (buckets restantes ficam sem "
                  f"temas).", file=sys.stderr)
            break
        except Exception as e:  # noqa: BLE001 — falha de LLM não perde a coleta
            por_bucket_gemini[b.nome] = gemini.calls - antes
            b.observacao_geral = f"[falha na síntese: {type(e).__name__}: {e}]"
            print(f"  ⚠️  bucket {b.nome}: falha na síntese ({type(e).__name__}: "
                  f"{e})", file=sys.stderr)
            continue
        chamou = gemini.calls - antes
        por_bucket_gemini[b.nome] = chamou
        print(f"  bucket {b.nome}: modo={b.modo} n_validas={b.n_validas} "
              f"-> {chamou} chamada(s) Gemini", file=sys.stderr)

    output = build_output(
        slug=slug, buckets=buckets,
        data_coleta=datetime.now(timezone.utc).isoformat(),
        origens=fetcher.origins, total_observado=total_observado(niveis),
    )
    path = write_json(output, OUT_DIR)

    render = render_terminal(output)
    print(render)  # stdout = output literal do terminal (para captura)

    print(f"\n--- MÉTRICAS DE ACEITE ({slug}) ---", file=sys.stderr)
    print(f"Requisições Letterboxd (coleta): {letterboxd_reqs} "
          f"(cache hits: {fetcher.n_cache})", file=sys.stderr)
    print(f"Chamadas Gemini (total, inclui retentativas): {gemini.calls}",
          file=sys.stderr)
    print(f"Chamadas Gemini por bucket: {por_bucket_gemini}", file=sys.stderr)
    for b in buckets:
        chamou = por_bucket_gemini.get(b.nome, 0)
        if b.modo == "sem_analise" and chamou > 0:
            print(f"  ⛔ BUG §5.3.d: bucket {b.nome} é sem_analise mas fez "
                  f"{chamou} chamada(s) Gemini!", file=sys.stderr)
        elif b.modo == "sem_analise":
            print(f"  ✅ §5.3.d: bucket {b.nome} sem_analise, 0 chamadas Gemini",
                  file=sys.stderr)
    print(f"JSON salvo em {path.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
