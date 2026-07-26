#!/usr/bin/env python3
"""Matriz de diagnóstico modelo × thinking para a FLUÊNCIA do narrador [D2].

Sessão de DIAGNÓSTICO (não é bump de versão): a v1.5.0 adicionou regras de
ritmo/registro/marcação ao §D2 e o resultado foi desigual — o `the-invite`
reproduziu o few-shot quase verbatim (o exemplo fora escrito com os dados
DESSE filme: contaminação), enquanto `cure` e `cidade-de-deus` não
transferiram o estilo. Hipótese a testar: o gargalo não é instrução, é
CONDIÇÃO DE EXECUÇÃO — `thinking_budget=0` (fixado na v1.2.x para resolver
truncamento de JSON) impede o planejamento de ritmo, e/ou o
`gemini-2.5-flash` não tem capacidade de prosa suficiente.

Matriz (4 combinações × 2 filmes = 8 chamadas, teto 16):
  A. gemini-2.5-flash, thinking off   (baseline atual)
  B. gemini-2.5-flash, thinking on
  C. gemini-2.5-pro,   thinking off
  D. gemini-2.5-pro,   thinking on

Restrições desta sessão:
- ZERO rede fora do Gemini: a síntese vem dos JSONs de produção já gerados
  (`resultado/<slug>.json`), no mesmo espírito de `--reuse-synthesis`.
  Nenhuma requisição ao Letterboxd ou TMDB.
- `thinking on` sobe `max_output_tokens` para >= 8000 — foi o teto baixo
  (3000, compartilhado com os tokens de thinking) que causou o truncamento
  de JSON que motivou `thinking_budget=0` na v1.2.x.
- Espaçamento >= 10s entre chamadas; 429/503 => 1 backoff de 60s + 1
  retentativa; se persistir, a COMBINAÇÃO é pulada e o motivo registrado.
- NÃO sobrescreve `resultado/<slug>.json` nem o frontend: as saídas vão para
  `resultado/diagnostico_fluencia/`.

Reusa `RateLimiter`, `Budget` e `_is_rate_limit_or_unavailable` de
`scripts/compare_models.py` (harness já existente) em vez de reimplementá-los.
"""
from __future__ import annotations

import json
import re
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

from espectro24.synthesize import (  # noqa: E402
    LLMError,
    _metricas_fluencia,
    _parse_llm_json,
    build_narrator_prompt,
    narrate_output,
)

OUT_DIR = ROOT / "resultado" / "diagnostico_fluencia"
FILMES = ["the-invite-2026", "cure"]
CALL_BUDGET = 16          # teto da sessão (8 esperadas + margem p/ retentativa)
MIN_SPACING_S = 10.0
THINKING_MAX_TOKENS = 8000   # thinking consome do MESMO orçamento de saída
BASE_MAX_TOKENS = 3000       # LLM_MAX_TOKENS de produção

COMBINACOES = [
    ("A", "gemini-2.5-flash", False),
    ("B", "gemini-2.5-flash", True),
    ("C", "gemini-2.5-pro", False),
    ("D", "gemini-2.5-pro", True),
]


def make_call(model: str, thinking_on: bool, rate_limiter: RateLimiter,
              budget: Budget, log: list[dict]):
    """client_call(system, user, model) instrumentado, com thinking
    CONFIGURÁVEL (o adaptador de produção fixa thinking_budget=0)."""
    import os as _os

    from google import genai
    from google.genai import types

    def _do(client, user, mdl, config):
        rate_limiter.before_call()
        budget.consume(f"{mdl}/thinking-{'on' if thinking_on else 'off'}")
        t0 = time.monotonic()
        resp = client.models.generate_content(model=mdl, contents=user, config=config)
        return resp, time.monotonic() - t0

    def call(system: str, user: str, _model_ignorado: str) -> str:
        key = _os.environ.get("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY não definida no ambiente.")
        client = genai.Client(api_key=key)

        cfg = dict(
            system_instruction=system,
            response_mime_type="application/json",
            max_output_tokens=(THINKING_MAX_TOKENS if thinking_on else BASE_MAX_TOKENS),
        )
        if not thinking_on:
            # replica exatamente a condição de produção (v1.2.x)
            cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        config = types.GenerateContentConfig(**cfg)

        tipo = "chamada"
        try:
            resp, lat = _do(client, user, model, config)
        except Exception as e:
            if not _is_rate_limit_or_unavailable(e):
                log.append({"tipo": tipo, "ok": False, "erro": f"{type(e).__name__}: {e}",
                            "finish_reason": None, "latencia_s": None})
                raise ModeloIrrecuperavelError(f"{model} falhou: {e}") from e
            log.append({"tipo": tipo, "ok": False, "erro": f"{type(e).__name__}: {e}",
                        "finish_reason": None, "latencia_s": None})
            print(f"      429/503 — backoff 60s + 1 retentativa...", file=sys.stderr)
            time.sleep(60.0)
            try:
                resp, lat = _do(client, user, model, config)
            except Exception as e2:
                log.append({"tipo": "retentativa_rate_limit", "ok": False,
                            "erro": f"{type(e2).__name__}: {e2}",
                            "finish_reason": None, "latencia_s": None})
                raise ModeloIrrecuperavelError(
                    f"{model} falhou de novo após backoff: {e2}") from e2
            tipo = "retentativa_rate_limit"

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

        text = resp.text
        json_valido = False
        if text:
            try:
                _parse_llm_json(text)
                json_valido = True
            except Exception:
                json_valido = False

        log.append({"tipo": tipo, "ok": True, "erro": None,
                    "finish_reason": finish_reason, "latencia_s": round(lat, 2),
                    "json_valido": json_valido, "usage": usage})
        return text

    return call


# --- Tarefa 4: verificação mecânica de contaminação pelo few-shot ---
#
# CUIDADO METODOLÓGICO: várias construções são EXIGIDAS por regra (rótulo de
# peso "a grande maioria das notas", marcadores de perspectiva "para eles"/
# "para esse grupo", enquadramento "quem gostou"). Elas aparecem no few-shot
# porque o exemplo obedece às mesmas regras — encontrá-las na narrativa é
# CONFORMIDADE, não cópia. Sem mascará-las, o detector acusa contaminação em
# toda narrativa correta (verificado: a única sobreposição entre a narrativa
# v1.5.0 do the-invite e o few-shot NOVO era exatamente "quem gostou é a
# grande maioria das notas"). Mascaramos as construções mandatórias antes de
# comparar, para medir só a prosa livre.
_FRASES_MANDATORIAS = [
    "uma pequena minoria", "a grande maioria", "uma parcela expressiva",
    "uma minoria", "a maioria", "das notas",
    "quem gostou", "quem não gostou", "quem ficou no meio", "no meio-termo",
    "para esse grupo", "para eles", "nessa leitura", "quem está nessa faixa",
]


def _normalizar_para_shingles(texto: str) -> list[str]:
    t = texto.lower()
    for frase in sorted(_FRASES_MANDATORIAS, key=len, reverse=True):
        t = t.replace(frase, " § ")     # placeholder não-palavra
    t = re.sub(r"~?\d[\d.,]*\s?%?", " § ", t)   # percentuais/números
    return re.findall(r"[^\W\d_]+", t, flags=re.UNICODE)


def _shingles(texto: str, n: int = 8) -> set[str]:
    """N-gramas de palavras do texto, com as construções MANDATÓRIAS
    mascaradas (ver nota acima) — mede sobreposição de prosa livre."""
    palavras = _normalizar_para_shingles(texto)
    return {" ".join(palavras[i:i + n]) for i in range(len(palavras) - n + 1)}


def _few_shot_depois(prompt: str) -> str:
    """Extrai o texto DEPOIS do few-shot do prompt vigente."""
    i = prompt.index("DEPOIS (busque este ritmo)")
    trecho = prompt[i:]
    # o exemplo termina na primeira linha em branco após o bloco entre aspas
    fim = trecho.find('"\n', trecho.find('"') + 1)
    return trecho[:fim] if fim != -1 else trecho[:1200]


def checar_contaminacao(narrativa: str, prompt: str, n: int = 8) -> dict:
    """True se algum n-grama de `n` palavras consecutivas do few-shot DEPOIS
    aparece na narrativa gerada."""
    fs = _few_shot_depois(prompt)
    comuns = _shingles(fs, n) & _shingles(narrativa, n)
    return {
        "contaminacao_detectada": bool(comuns),
        "n_gramas_compartilhados": sorted(comuns)[:5],
    }


def rodar(slug: str, rotulo: str, model: str, thinking_on: bool,
          rate_limiter: RateLimiter, budget: Budget) -> dict:
    """Uma combinação × filme. Reusa `narrate_output` (mesmo caminho de
    produção: validações, retentativa combinada e flags idênticas)."""
    prod = json.loads((ROOT / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
    # entrada do narrador = o output validado, SEM a narrativa anterior
    entrada = {k: v for k, v in prod.items()
               if k not in ("narrativa", "narrativa_flags", "consensos_usados",
                            "quantificadores_usados", "marcadores_perspectiva",
                            "metricas_fluencia")}

    log: list[dict] = []
    call = make_call(model, thinking_on, rate_limiter, budget, log)
    t0 = time.monotonic()
    try:
        res = narrate_output(entrada, client_call=call, model=model)
    except (BudgetExceededError, ModeloIrrecuperavelError) as e:
        return {"combinacao": rotulo, "slug": slug, "modelo": model,
                "thinking": "on" if thinking_on else "off",
                "pulado": True, "motivo": str(e), "chamadas": log}
    total_s = round(time.monotonic() - t0, 2)

    prompt = build_narrator_prompt(bool(entrada.get("distribuicao")))
    contaminacao = checar_contaminacao(res.texto, prompt)
    n_chamadas_normais = sum(1 for m in log if m["tipo"] == "chamada")

    return {
        "combinacao": rotulo, "slug": slug, "modelo": model,
        "thinking": "on" if thinking_on else "off",
        "max_output_tokens": THINKING_MAX_TOKENS if thinking_on else BASE_MAX_TOKENS,
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
        "chamadas": log,
        **contaminacao,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rate_limiter = RateLimiter(MIN_SPACING_S)
    budget = Budget(CALL_BUDGET)
    resultados = []

    for rotulo, model, thinking_on in COMBINACOES:
        for slug in FILMES:
            th = "on" if thinking_on else "off"
            print(f"\n=== {rotulo}: {model} thinking-{th} · {slug} ===", file=sys.stderr)
            if budget.used >= budget.limit:
                print("    PULADO: orçamento esgotado", file=sys.stderr)
                resultados.append({"combinacao": rotulo, "slug": slug,
                                   "modelo": model, "thinking": th,
                                   "pulado": True, "motivo": "orçamento esgotado"})
                continue
            r = rodar(slug, rotulo, model, thinking_on, rate_limiter, budget)
            resultados.append(r)
            path = OUT_DIR / f"{slug}__{model}__thinking-{th}.json"
            path.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            if r.get("pulado"):
                print(f"    PULADO: {r['motivo']}", file=sys.stderr)
            else:
                m = r["metricas_fluencia"]
                print(f"    cv={m['cv_comprimento']} curta={m['frase_mais_curta']} "
                      f"reporte={m['verbos_reporte']} · fluencia_baixa="
                      f"{r['flags']['fluencia_baixa']} · contaminacao="
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
