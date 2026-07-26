#!/usr/bin/env python3
"""Reteste do diagnóstico de fluência (v2) — condição de execução corrigida.

Continuação de `scripts/diagnostico_fluencia.py` / `DIAGNOSTICO_FLUENCIA.md`.
Na rodada anterior, as DUAS células com thinking (`max_output_tokens=8000`,
thinking DINÂMICO — sem `thinking_budget` fixo, ou seja, o modelo decidia
quanto pensar) perderam uma chamada por `MAX_TOKENS`: o raciocínio consumiu
até 96% do teto (7676/8000 tokens), e no `cure` foi a RETENTATIVA DE
VALIDAÇÃO que truncou e foi descartada — o que é a explicação mecânica mais
provável para o `perspectiva_nao_marcada` daquela célula, não um efeito do
raciocínio em si. Qualquer conclusão sobre thinking a partir da v1 é
inválida por essa razão; esta sessão corrige a condição e reroda.

Configuração corrigida (Tarefa 1):
  - `thinking_budget` FIXO em 4096 (não dinâmico/-1) quando thinking está
    "on" — antes o SDK escolhia livremente até o teto do modelo.
  - `max_output_tokens=16000` em TODAS as células desta rodada (mesmo as de
    thinking off, para isolar o efeito do budget, não do teto).
  Como os tokens de raciocínio contam DENTRO de max_output_tokens, essa
  combinação garante ~12000 tokens de folga para a saída mesmo no pior caso
  observado na v1 (~7.7k de thinking).

Matriz (Tarefa 2) — a célula A (flash, thinking off) NÃO é refeita: nenhuma
chamada dela truncou na v1, os resultados são válidos e reaproveitados do
relatório anterior para a tabela comparativa.
  B. gemini-2.5-flash, thinking_budget=4096, max_output=16000
  C. gemini-2.5-pro,   thinking_budget=0,    max_output=16000
  D. gemini-2.5-pro,   thinking_budget=4096, max_output=16000
Filmes: the-invite-2026, cure. Previsto: 6 chamadas. Teto: 14.

`gemini-2.5-pro` (C, D): a v1 mostrou `RESOURCE_EXHAUSTED` com `limit: 0`
em todas as cotas (minuto E dia) — erro ESTRUTURAL (a chave/plano não tem
acesso ao modelo), não transitório. Por isso, para modelos "gemini-2.5-pro",
esta sessão faz **1 tentativa, sem backoff**: insistir com espera não muda
uma cota que é 0. Para "gemini-2.5-flash", mantém o protocolo original
(1 backoff de 60s + 1 retentativa em 429/503).

Saídas em `resultado/diagnostico_fluencia/v2/` — NÃO toca em
`resultado/<slug>.json` de produção nem em `frontend/js/data.js`.

Reusa `RateLimiter`/`Budget`/`_is_rate_limit_or_unavailable` de
`scripts/compare_models.py` e o checker de contaminação (com mascaramento
das construções mandatórias) de `scripts/diagnostico_fluencia.py`.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=ROOT / ".env")

from compare_models import (  # noqa: E402  (harness existente — REUSO)
    Budget,
    BudgetExceededError,
    ModeloIrrecuperavelError,
    RateLimiter,
    _is_rate_limit_or_unavailable,
)
from diagnostico_fluencia import checar_contaminacao  # noqa: E402  (REUSO)

from espectro24.synthesize import (  # noqa: E402
    LLMError,
    _parse_llm_json,
    build_narrator_prompt,
    narrate_output,
)

OUT_DIR = ROOT / "resultado" / "diagnostico_fluencia" / "v2"
FILMES = ["the-invite-2026", "cure"]
CALL_BUDGET = 14
MIN_SPACING_S = 10.0
MAX_OUTPUT_TOKENS = 16000     # Tarefa 1: folga real p/ thinking + JSON completo
THINKING_BUDGET_ON = 4096     # Tarefa 1: FIXO, não dinâmico/-1

# (rótulo, modelo, thinking_budget ou None p/ "off" explícito)
COMBINACOES = [
    ("B", "gemini-2.5-flash", THINKING_BUDGET_ON),
    ("C", "gemini-2.5-pro", 0),
    ("D", "gemini-2.5-pro", THINKING_BUDGET_ON),
]


def make_call(model: str, thinking_budget: int, rate_limiter: RateLimiter,
              budget: Budget, log: list[dict]):
    """client_call(system, user, model) instrumentado. `thinking_budget=0`
    replica a condição de produção (raciocínio desligado); qualquer valor
    > 0 fixa o orçamento de raciocínio EXPLICITAMENTE (nunca dinâmico).

    `gemini-2.5-pro`: 1 tentativa, SEM backoff — a v1 mostrou que o 429
    daquele modelo é `limit: 0` estrutural (cota zerada por minuto E por
    dia), não transitório; esperar não muda o resultado.
    """
    import os as _os

    from google import genai
    from google.genai import types

    sem_backoff = model == "gemini-2.5-pro"

    def _do(client, user, mdl, config):
        rate_limiter.before_call()
        budget.consume(f"{mdl}/thinking-{thinking_budget}")
        t0 = time.monotonic()
        resp = client.models.generate_content(model=mdl, contents=user, config=config)
        return resp, time.monotonic() - t0

    def _extrair(resp) -> dict:
        finish_reason = None
        try:
            if resp.candidates:
                finish_reason = str(resp.candidates[0].finish_reason)
        except Exception:
            pass
        usage = {}
        try:
            um = resp.usage_metadata
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", None),
                "output_tokens": getattr(um, "candidates_token_count", None),
                "thinking_tokens": getattr(um, "thoughts_token_count", None),
            }
        except Exception:
            pass
        return {"finish_reason": finish_reason, "usage": usage}

    def call(system: str, user: str, _model_ignorado: str) -> str:
        key = _os.environ.get("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY não definida no ambiente.")
        client = genai.Client(api_key=key)

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            max_output_tokens=MAX_OUTPUT_TOKENS,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
        )

        tipo = "chamada"
        try:
            resp, lat = _do(client, user, model, config)
        except Exception as e:
            if sem_backoff or not _is_rate_limit_or_unavailable(e):
                log.append({"tipo": tipo, "ok": False, "erro": f"{type(e).__name__}: {e}",
                            "finish_reason": None, "latencia_s": None, "usage": {}})
                raise ModeloIrrecuperavelError(f"{model} falhou: {e}") from e
            log.append({"tipo": tipo, "ok": False, "erro": f"{type(e).__name__}: {e}",
                        "finish_reason": None, "latencia_s": None, "usage": {}})
            print("      429/503 — backoff 60s + 1 retentativa...", file=sys.stderr)
            time.sleep(60.0)
            try:
                resp, lat = _do(client, user, model, config)
            except Exception as e2:
                log.append({"tipo": "retentativa_rate_limit", "ok": False,
                            "erro": f"{type(e2).__name__}: {e2}",
                            "finish_reason": None, "latencia_s": None, "usage": {}})
                raise ModeloIrrecuperavelError(
                    f"{model} falhou de novo após backoff: {e2}") from e2
            tipo = "retentativa_rate_limit"

        extra = _extrair(resp)
        text = resp.text
        json_valido = False
        if text:
            try:
                _parse_llm_json(text)
                json_valido = True
            except Exception:
                json_valido = False

        log.append({"tipo": tipo, "ok": True, "erro": None,
                    "finish_reason": extra["finish_reason"],
                    "latencia_s": round(lat, 2), "json_valido": json_valido,
                    "usage": extra["usage"]})
        return text

    return call


def rodar(slug: str, rotulo: str, model: str, thinking_budget: int,
          rate_limiter: RateLimiter, budget: Budget) -> dict:
    prod = json.loads((ROOT / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
    entrada = {k: v for k, v in prod.items()
               if k not in ("narrativa", "narrativa_flags", "consensos_usados",
                            "quantificadores_usados", "marcadores_perspectiva",
                            "metricas_fluencia")}

    log: list[dict] = []
    call = make_call(model, thinking_budget, rate_limiter, budget, log)
    t0 = time.monotonic()
    try:
        res = narrate_output(entrada, client_call=call, model=model)
    except (BudgetExceededError, ModeloIrrecuperavelError) as e:
        return {"combinacao": rotulo, "slug": slug, "modelo": model,
                "thinking_budget": thinking_budget,
                "pulado": True, "motivo": str(e), "chamadas": log}
    total_s = round(time.monotonic() - t0, 2)

    prompt = build_narrator_prompt(bool(entrada.get("distribuicao")))
    contaminacao = checar_contaminacao(res.texto, prompt)
    n_chamadas_normais = sum(1 for m in log if m["tipo"] == "chamada")
    algum_truncou = any(m.get("finish_reason") == "FinishReason.MAX_TOKENS"
                        for m in log)

    return {
        "combinacao": rotulo, "slug": slug, "modelo": model,
        "thinking_budget": thinking_budget,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "pulado": False,
        "narrativa": res.texto,
        "n_palavras": len(res.texto.split()),
        "metricas_fluencia": res.metricas_fluencia,
        "flags": {
            "idioma_invalido": res.idioma_invalido,
            "escopo_suspeito": res.escopo_suspeito,
            "prevalencia_suspeita": res.prevalencia_suspeita,
            "quantificador_suspeito": res.quantificador_suspeito,
            "consenso_suspeito": res.consenso_suspeito,
            "peso_nao_ancorado": res.peso_nao_ancorado,
            "vocabulario_peso_suspeito": res.vocabulario_peso_suspeito,
            "perspectiva_nao_marcada": res.perspectiva_nao_marcada,
            "fluencia_baixa": res.fluencia_baixa,
            "aspas_removidas": res.aspas_removidas,
            "falhou": res.falhou,
        },
        "consensos_usados": res.consensos_usados,
        "quantificadores_usados": res.quantificadores_usados,
        "marcadores_perspectiva": res.marcadores_perspectiva,
        "houve_retentativa": n_chamadas_normais > 1,
        "n_chamadas_llm": len(log),
        "latencia_total_s": total_s,
        "algum_finish_max_tokens": algum_truncou,
        "chamadas": log,
        **contaminacao,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rate_limiter = RateLimiter(MIN_SPACING_S)
    budget = Budget(CALL_BUDGET)
    resultados = []

    for rotulo, model, thinking_budget in COMBINACOES:
        for slug in FILMES:
            print(f"\n=== {rotulo}: {model} thinking_budget={thinking_budget} "
                 f"max_out={MAX_OUTPUT_TOKENS} · {slug} ===", file=sys.stderr)
            if budget.used >= budget.limit:
                print("    PULADO: orçamento esgotado", file=sys.stderr)
                resultados.append({"combinacao": rotulo, "slug": slug,
                                   "modelo": model, "thinking_budget": thinking_budget,
                                   "pulado": True, "motivo": "orçamento esgotado"})
                continue
            r = rodar(slug, rotulo, model, thinking_budget, rate_limiter, budget)
            resultados.append(r)
            path = OUT_DIR / f"{slug}__{model}__tb-{thinking_budget}.json"
            path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            if r.get("pulado"):
                print(f"    PULADO: {r['motivo']}", file=sys.stderr)
            else:
                m = r["metricas_fluencia"]
                print(f"    cv={m['cv_comprimento']} curta={m['frase_mais_curta']} "
                      f"reporte={m['verbos_reporte']} · fluencia_baixa="
                      f"{r['flags']['fluencia_baixa']} · perspectiva_nao_marcada="
                      f"{r['flags']['perspectiva_nao_marcada']} · MAX_TOKENS="
                      f"{r['algum_finish_max_tokens']} · contaminacao="
                      f"{r['contaminacao_detectada']} · {r['latencia_total_s']}s",
                      file=sys.stderr)
            print(f"    chamadas: {budget.used}/{budget.limit}", file=sys.stderr)

    (OUT_DIR / "_resumo.json").write_text(
        json.dumps({"gerado_em": datetime.now(timezone.utc).isoformat(),
                    "chamadas_gemini": budget.used, "teto": budget.limit,
                    "resultados": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n=== Fim === chamadas Gemini: {budget.used}/{budget.limit}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
