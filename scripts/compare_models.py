#!/usr/bin/env python3
"""Harness de comparação de modelos Gemini sobre o corpus JÁ CACHEADO de
oppenheimer-2023 (Espectro 24, v1.1.1+).

Restrições desta sessão (ver prompt da tarefa):
- ZERO requisições ao Letterboxd. A coleta vem 100% do cache
  (resultado/cache/) via Fetcher(offline=True) — qualquer cache miss
  levanta FetchError em vez de tocar a rede. Após a coleta, este script
  ABORTA se `fetcher.n_network != 0` (checagem defensiva: se isso disparar,
  é bug em outro lugar do pipeline, não deste script).
- Até 12 chamadas Gemini nesta sessão (orçamento GLOBAL, compartilhado por
  todos os modelos/buckets/retentativas). Espaçamento >=10s entre TODAS as
  chamadas reais (limite observado: 10 req/min no free tier do 2.5-flash).
- 429/503: 1 backoff de 60s + 1 retentativa. Se falhar de novo, o MODELO
  INTEIRO é pulado (não escreve JSON parcial) e o motivo é registrado.
- A chave vem do .env já configurado (GEMINI_API_KEY) — nunca lida/impressa
  por este script; só repassada ao SDK.

Saída:
  resultado/comparacao/oppenheimer-2023__<modelo>.json  (um por modelo bem-sucedido)
  resultado/comparacao/COMPARACAO.md                    (tabelas + temas lado a lado)

NÃO escreve em resultado/oppenheimer-2023.json (saída do CLI principal).
"""
from __future__ import annotations

import copy
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=ROOT / ".env")

from espectro24.collector import assemble_buckets  # noqa: E402
from espectro24.config import LLM_MAX_TOKENS  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import collect_all_levels  # noqa: E402
from espectro24.render import build_output  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    LLMError,
    _parse_llm_json,
    gemini_supports_thinking,
    synthesize_bucket,
)

SLUG = "oppenheimer-2023"
CACHE_DIR = ROOT / "resultado" / "cache"
OUT_DIR = ROOT / "resultado" / "comparacao"
MODELOS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
CALL_BUDGET = 12
MIN_SPACING_S = 10.0
BACKOFF_S = 60.0


class BudgetExceededError(RuntimeError):
    pass


class ModeloIrrecuperavelError(RuntimeError):
    pass


class RateLimiter:
    """Garante >=MIN_SPACING_S entre o INÍCIO de chamadas reais consecutivas."""

    def __init__(self, min_spacing: float = MIN_SPACING_S):
        self.min_spacing = min_spacing
        self._last_start: float | None = None

    def before_call(self) -> None:
        if self._last_start is not None:
            elapsed = time.monotonic() - self._last_start
            remaining = self.min_spacing - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_start = time.monotonic()


class Budget:
    """Orçamento GLOBAL de chamadas reais, compartilhado por todos os modelos."""

    def __init__(self, limit: int = CALL_BUDGET):
        self.limit = limit
        self.used = 0

    def consume(self, label: str = "") -> None:
        if self.used >= self.limit:
            raise BudgetExceededError(
                f"orçamento de {self.limit} chamadas Gemini esgotado "
                f"(tentativa: {label})"
            )
        self.used += 1


def _is_rate_limit_or_unavailable(exc: Exception) -> bool:
    from google.genai import errors
    return isinstance(exc, errors.APIError) and exc.code in (429, 503)


def make_instrumented_gemini_call(rate_limiter: RateLimiter, budget: Budget,
                                  metrics_log: list[dict]):
    """Retorna um client_call(system, user, model) -> str instrumentado.

    Cada tentativa real de rede vira uma entrada em `metrics_log` (mutável,
    deve ser passado NOVO por bucket para isolar as métricas). tipo:
    "chamada" = invocação normal (synthesize_bucket pode fazer até 2, se a
    1ª não parsear como JSON); "retentativa_rate_limit" = o backoff único
    de 60s em resposta a 429/503.
    """
    import os as _os

    from google import genai
    from google.genai import types

    def _do_call(client, user, model, config):
        rate_limiter.before_call()
        budget.consume(model)
        t0 = time.monotonic()
        resp = client.models.generate_content(model=model, contents=user, config=config)
        return resp, time.monotonic() - t0

    def call(system: str, user: str, model: str) -> str:
        key = _os.environ.get("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY não definida no ambiente.")
        client = genai.Client(api_key=key)

        config_kwargs = dict(
            system_instruction=system,
            response_mime_type="application/json",
            max_output_tokens=LLM_MAX_TOKENS,
        )
        if gemini_supports_thinking(model):
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        config = types.GenerateContentConfig(**config_kwargs)

        tipo = "chamada"
        try:
            resp, latencia = _do_call(client, user, model, config)
        except Exception as e:
            if not _is_rate_limit_or_unavailable(e):
                metrics_log.append({
                    "tipo": "chamada", "ok": False, "erro": f"{type(e).__name__}: {e}",
                    "finish_reason": None, "latencia_s": None, "json_valido": False,
                })
                raise ModeloIrrecuperavelError(f"modelo {model} falhou: {e}") from e

            metrics_log.append({
                "tipo": "chamada", "ok": False, "erro": f"{type(e).__name__}: {e}",
                "finish_reason": None, "latencia_s": None, "json_valido": False,
            })
            print(f"    [{model}] 429/503 — backoff de {BACKOFF_S:.0f}s + "
                  f"1 retentativa...", file=sys.stderr)
            time.sleep(BACKOFF_S)
            try:
                resp, latencia = _do_call(client, user, model, config)
            except Exception as e2:
                metrics_log.append({
                    "tipo": "retentativa_rate_limit", "ok": False,
                    "erro": f"{type(e2).__name__}: {e2}",
                    "finish_reason": None, "latencia_s": None, "json_valido": False,
                })
                raise ModeloIrrecuperavelError(
                    f"modelo {model} falhou de novo após backoff de "
                    f"{BACKOFF_S:.0f}s: {e2}"
                ) from e2
            tipo = "retentativa_rate_limit"

        finish_reason = None
        try:
            if resp.candidates:
                finish_reason = str(resp.candidates[0].finish_reason)
        except Exception:
            pass

        text = resp.text
        json_valido = False
        if text:
            try:
                _parse_llm_json(text)
                json_valido = True
            except Exception:
                json_valido = False

        metrics_log.append({
            "tipo": tipo, "ok": True, "erro": None,
            "finish_reason": finish_reason, "latencia_s": round(latencia, 2),
            "json_valido": json_valido,
        })
        return text

    return call


def summarize_bucket_metrics(metrics_log: list[dict]) -> dict:
    if not metrics_log:
        return {
            "json_valido": None, "houve_retentativa": False,
            "houve_backoff_rate_limit": False, "finish_reason": None,
            "latencia_s": None, "nota": "sem_analise — LLM não chamado (piso não atingido)",
        }
    ultima = metrics_log[-1]
    n_chamadas_normais = sum(1 for m in metrics_log if m["tipo"] == "chamada")
    return {
        "json_valido": ultima["json_valido"],
        "houve_retentativa": n_chamadas_normais > 1,
        "houve_backoff_rate_limit": any(m["tipo"] == "retentativa_rate_limit" for m in metrics_log),
        "finish_reason": ultima["finish_reason"],
        "latencia_s": ultima["latencia_s"],
    }


def run_model(model: str, base_buckets: list, rate_limiter: RateLimiter, budget: Budget):
    """Roda a síntese dos 3 buckets para `model`. Retorna (buckets, metricas) ou
    (None, motivo_do_skip)."""
    if budget.used >= budget.limit:
        return None, f"orçamento de {budget.limit} chamadas já esgotado antes de iniciar"

    buckets = copy.deepcopy(base_buckets)
    metricas_por_bucket = {}
    try:
        for b in buckets:
            metrics_log: list[dict] = []
            call = make_instrumented_gemini_call(rate_limiter, budget, metrics_log)
            synthesize_bucket(b, client_call=call, model=model)
            resumo = summarize_bucket_metrics(metrics_log)
            resumo["n_temas"] = len(b.temas)
            resumo["soma_mencoes_aproximadas"] = sum(t.mencoes_aproximadas for t in b.temas)
            resumo["n_temas_clampados"] = sum(1 for t in b.temas if t.mencoes_clampadas)
            resumo["chamadas_detalhe"] = metrics_log
            metricas_por_bucket[b.nome] = resumo
    except (BudgetExceededError, ModeloIrrecuperavelError) as e:
        return None, str(e)
    return (buckets, metricas_por_bucket), None


def render_comparacao_md(resultados: dict, pulados: dict, budget: Budget) -> str:
    L = []
    L.append("# Espectro 24 — Comparação de modelos Gemini (oppenheimer-2023)")
    L.append("")
    L.append(f"Gerado em {datetime.now(timezone.utc).isoformat()}. "
             f"Corpus 100% do cache (`resultado/cache/`), zero requisições ao "
             f"Letterboxd. Prompt §D byte-idêntico entre modelos — a única "
             f"variável é o modelo.")
    L.append("")
    L.append(f"**Chamadas Gemini gastas nesta sessão: {budget.used}/{budget.limit}**")
    L.append("")
    if pulados:
        L.append("## Modelos pulados")
        L.append("")
        for modelo, motivo in pulados.items():
            L.append(f"- **{modelo}**: {motivo}")
        L.append("")

    L.append("## Métricas por modelo × bucket")
    L.append("")
    L.append("| Modelo | Bucket | json_valido | houve_retentativa | "
             "houve_backoff | finish_reason | n_temas | soma_mencoes | "
             "n_clampados | latência (s) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for modelo, (buckets, metricas) in resultados.items():
        for b in buckets:
            m = metricas[b.nome]
            L.append(
                f"| {modelo} | {b.nome} | {m['json_valido']} | "
                f"{m['houve_retentativa']} | {m['houve_backoff_rate_limit']} | "
                f"{m['finish_reason']} | {m['n_temas']} | "
                f"{m['soma_mencoes_aproximadas']} | {m['n_temas_clampados']} | "
                f"{m['latencia_s']} |"
            )
    L.append("")

    L.append("## Temas lado a lado (nome + frequência, por bucket)")
    L.append("")
    L.append("Apenas dados organizados para inspeção humana — nenhum veredito "
             "de qualidade/coerência/spoiler é feito por este script.")
    L.append("")
    bucket_nomes = ["negativas", "medianas", "positivas"]
    for nome_bucket in bucket_nomes:
        L.append(f"### Bucket: {nome_bucket}")
        L.append("")
        modelos_com_bucket = [m for m in resultados if nome_bucket in
                              {b.nome for b in resultados[m][0]}]
        if not modelos_com_bucket:
            L.append("_(nenhum modelo produziu dados para este bucket)_")
            L.append("")
            continue
        header = "| # | " + " | ".join(modelos_com_bucket) + " |"
        sep = "|---|" + "|".join(["---"] * len(modelos_com_bucket)) + "|"
        L.append(header)
        L.append(sep)
        max_temas = max(
            len(next(b for b in resultados[m][0] if b.nome == nome_bucket).temas)
            for m in modelos_com_bucket
        ) if modelos_com_bucket else 0
        for i in range(max_temas):
            linha = [f"{i + 1}"]
            for m in modelos_com_bucket:
                b = next(bb for bb in resultados[m][0] if bb.nome == nome_bucket)
                if i < len(b.temas):
                    t = b.temas[i]
                    linha.append(f"{t.tema} (~{t.mencoes_aproximadas})")
                else:
                    linha.append("")
            L.append("| " + " | ".join(linha) + " |")
        L.append("")

    return "\n".join(L)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== Coletando {SLUG} (100% cache, offline) ===", file=sys.stderr)
    fetcher = Fetcher(cache_dir=CACHE_DIR, offline=True)
    niveis = collect_all_levels(fetcher, SLUG)
    if fetcher.n_network != 0:
        print(f"\n⛔ BUG: fetcher fez {fetcher.n_network} requisição(ões) de "
              f"rede durante uma coleta que deveria ser 100% cache. "
              f"Abortando sem gastar chamadas Gemini.", file=sys.stderr)
        return 2
    print(f"    rede tocada: {fetcher.n_network} (esperado 0) — OK", file=sys.stderr)
    base_buckets = assemble_buckets(niveis)
    for b in base_buckets:
        print(f"    bucket {b.nome}: {b.n_validas}/{b.alvo} válidas, "
              f"modo={b.modo}", file=sys.stderr)

    rate_limiter = RateLimiter()
    budget = Budget()
    resultados: dict[str, tuple] = {}
    pulados: dict[str, str] = {}

    for model in MODELOS:
        print(f"\n=== Modelo: {model} ===", file=sys.stderr)
        out, motivo_skip = run_model(model, base_buckets, rate_limiter, budget)
        if out is None:
            print(f"    PULADO: {motivo_skip}", file=sys.stderr)
            pulados[model] = motivo_skip
            continue
        buckets, metricas = out
        resultados[model] = (buckets, metricas)

        output = build_output(
            slug=SLUG, buckets=buckets,
            data_coleta=datetime.now(timezone.utc).isoformat(),
            origens=fetcher.origins,
            total_observado=sum(l.n_brutas for l in niveis.values()),
        )
        output["comparacao"] = {"modelo": model, "metricas_por_bucket": metricas}
        path = OUT_DIR / f"{SLUG}__{model}.json"
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    JSON salvo em {path.relative_to(ROOT)}", file=sys.stderr)
        print(f"    chamadas Gemini usadas até agora: {budget.used}/{budget.limit}",
              file=sys.stderr)

    md = render_comparacao_md(resultados, pulados, budget)
    md_path = OUT_DIR / "COMPARACAO.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"\n=== Fim ===", file=sys.stderr)
    print(f"Modelos concluídos: {list(resultados)}", file=sys.stderr)
    print(f"Modelos pulados: {list(pulados)}", file=sys.stderr)
    print(f"Chamadas Gemini gastas: {budget.used}/{budget.limit}", file=sys.stderr)
    print(f"Relatório: {md_path.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
