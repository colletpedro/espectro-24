#!/usr/bin/env python3
"""Continuação pontual da comparação de modelos (sessão de retomada).

NÃO reimplementa o harness — importa e reusa `scripts/compare_models.py`
(RateLimiter, Budget, run_model, make_instrumented_gemini_call,
render_comparacao_md, etc.) tal como estão. Este script é só orquestração
para: (a) rodar SOMENTE gemini-2.5-flash desta vez, sem re-rodar o
flash-lite já salvo; (b) condicionalmente sondar gemini-2.0-flash com 1
bucket; (c) mesclar o resultado novo com o antigo (recarregado do JSON já
salvo) e re-renderizar o COMPARACAO.md com `render_comparacao_md` existente;
(d) registrar o idioma de saída de cada bucket (checagem factual de
formato, não veredito de qualidade).

Orçamento desta sessão: 8 chamadas Gemini (mais restritivo que o default
de 12 do harness — por isso um Budget próprio é criado aqui).
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=ROOT / ".env")

import compare_models as cm  # noqa: E402 — reusa o harness existente, não reimplementa
from espectro24.collector import assemble_buckets  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.models import BucketResult, Tema  # noqa: E402
from espectro24.pipeline import collect_all_levels  # noqa: E402

SESSAO_BUDGET = 8
PROBE_BUCKET = "medianas"  # menor bucket (20 reviews) — minimiza custo da sondagem


# --- Checagem factual de idioma (heurística por contagem de stopwords) ---
# Não é julgamento de qualidade: é uma contagem mecânica e reproduzível de
# palavras funcionais (stopwords) típicas de cada idioma no texto gerado.
_STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "que", "para", "com", "uma", "um", "e",
    "os", "as", "não", "mais", "como", "por", "sobre", "são", "foi", "ao",
    "à", "às", "seu", "sua", "entre", "também", "muito", "há",
}
_STOPWORDS_EN = {
    "the", "and", "of", "to", "in", "is", "for", "with", "on", "are", "as",
    "this", "that", "by", "from", "or", "an", "its", "be", "was", "were",
}


def detectar_idioma(texto: str) -> str:
    palavras = [w.strip(".,;:!?()\"'").lower() for w in texto.split()]
    n_pt = sum(1 for w in palavras if w in _STOPWORDS_PT)
    n_en = sum(1 for w in palavras if w in _STOPWORDS_EN)
    if n_pt == 0 and n_en == 0:
        return "indeterminado"
    if n_pt > n_en:
        return "pt-BR"
    if n_en > n_pt:
        return "en"
    return "misto/ambíguo"


def texto_do_bucket(bucket: BucketResult) -> str:
    partes = [t.tema for t in bucket.temas]
    return " ".join(partes)


def carregar_resultado_salvo(modelo: str) -> tuple[list[BucketResult], dict] | None:
    """Reconstrói (buckets, metricas) a partir do JSON já salvo por uma
    execução anterior do harness — deserialização, não reimplementação da
    lógica de síntese."""
    path = cm.OUT_DIR / f"{cm.SLUG}__{modelo}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    buckets = []
    for b in data["buckets"]:
        temas = [
            Tema(
                tema=t["tema"],
                mencoes_aproximadas=t["mencoes_aproximadas"],
                n_reviews_analisadas=t["n_reviews_analisadas"],
                exemplo_parafraseado=t["exemplo_parafraseado"],
                mencoes_clampadas=t.get("mencoes_clampadas", False),
                mencoes_valor_original=t.get("mencoes_valor_original"),
            )
            for t in b["temas"]
        ]
        buckets.append(BucketResult(
            nome=b["bucket"], alvo=b["alvo"], modo=b["modo"], temas=temas,
            observacao_geral=b.get("observacao_geral", ""),
        ))
    metricas = data["comparacao"]["metricas_por_bucket"]
    return buckets, metricas


def salvar_json_modelo(modelo: str, buckets, metricas, fetcher, niveis) -> Path:
    output = cm.build_output(
        slug=cm.SLUG, buckets=buckets,
        data_coleta=datetime.now(timezone.utc).isoformat(),
        origens=fetcher.origins,
        total_observado=sum(l.n_brutas for l in niveis.values()),
    )
    output["comparacao"] = {"modelo": modelo, "metricas_por_bucket": metricas}
    path = cm.OUT_DIR / f"{cm.SLUG}__{modelo}.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    horario_inicio = datetime.now(timezone.utc).isoformat()
    print(f"=== Retomada da comparação — {horario_inicio} ===", file=sys.stderr)

    # --- Coleta 100% cache (idêntica ao harness original) ---
    print(f"\n=== Coletando {cm.SLUG} (100% cache, offline) ===", file=sys.stderr)
    fetcher = Fetcher(cache_dir=cm.CACHE_DIR, offline=True)
    niveis = collect_all_levels(fetcher, cm.SLUG)
    if fetcher.n_network != 0:
        print(f"\n⛔ BUG: fetcher fez {fetcher.n_network} requisição(ões) de "
              f"rede — deveria ser 100% cache. Abortando.", file=sys.stderr)
        return 2
    print(f"    rede tocada: {fetcher.n_network} (esperado 0) — OK", file=sys.stderr)
    base_buckets = assemble_buckets(niveis)

    rate_limiter = cm.RateLimiter()
    budget = cm.Budget(limit=SESSAO_BUDGET)

    resultados: dict[str, tuple] = {}
    pulados: dict[str, str] = {}
    contingencia = None

    # --- Recarrega o flash-lite já salvo (NÃO roda de novo) ---
    prev = carregar_resultado_salvo("gemini-2.5-flash-lite")
    if prev is not None:
        resultados["gemini-2.5-flash-lite"] = prev
        print("\n=== gemini-2.5-flash-lite: reaproveitado do JSON já salvo "
              "(não re-executado) ===", file=sys.stderr)
    else:
        print("\n⚠️  aviso: JSON do gemini-2.5-flash-lite não encontrado para "
              "reaproveitar", file=sys.stderr)

    # --- 1. gemini-2.5-flash (3 chamadas) ---
    print("\n=== Modelo: gemini-2.5-flash ===", file=sys.stderr)
    out, motivo = cm.run_model("gemini-2.5-flash", base_buckets, rate_limiter, budget)
    if out is None:
        pulados["gemini-2.5-flash"] = motivo
        print(f"    PULADO: {motivo}", file=sys.stderr)
        houve_backoff = "após backoff" in motivo or "apos backoff" in motivo
        contingencia = {
            "cenario": (
                "429 sobreviveu ao reset diário — problema NÃO é esgotamento "
                "por uso; investigação muda de natureza (limite de projeto no "
                "Google Cloud, não comportamento do código)."
                if houve_backoff else
                "falha não relacionada a rate-limit/quota (não passou pelo "
                "fluxo de backoff)."
            ),
            "horario_utc": datetime.now(timezone.utc).isoformat(),
            "erro_literal": motivo,
            "houve_backoff_e_retentativa": houve_backoff,
        }
        print("    CONTINGÊNCIA ACIONADA — parando completamente, não "
              "tentando gemini-2.0-flash.", file=sys.stderr)
    else:
        buckets, metricas = out
        resultados["gemini-2.5-flash"] = out
        path = salvar_json_modelo("gemini-2.5-flash", buckets, metricas, fetcher, niveis)
        print(f"    JSON salvo em {path.relative_to(ROOT)}", file=sys.stderr)
        print(f"    chamadas usadas até agora: {budget.used}/{budget.limit}",
              file=sys.stderr)

        # --- 2. sondagem condicional gemini-2.0-flash (1 bucket só) ---
        print(f"\n=== Sondagem: gemini-2.0-flash (1 bucket: {PROBE_BUCKET}) ===",
              file=sys.stderr)
        alvo = copy.deepcopy(next(b for b in base_buckets if b.nome == PROBE_BUCKET))
        metrics_log: list[dict] = []
        call = cm.make_instrumented_gemini_call(rate_limiter, budget, metrics_log)
        try:
            from espectro24.synthesize import synthesize_bucket
            synthesize_bucket(alvo, client_call=call, model="gemini-2.0-flash")
            resumo = cm.summarize_bucket_metrics(metrics_log)
            resumo["n_temas"] = len(alvo.temas)
            resumo["soma_mencoes_aproximadas"] = sum(t.mencoes_aproximadas for t in alvo.temas)
            resumo["n_temas_clampados"] = sum(1 for t in alvo.temas if t.mencoes_clampadas)
            resumo["chamadas_detalhe"] = metrics_log
            resultados["gemini-2.0-flash (sondagem parcial)"] = ([alvo], {PROBE_BUCKET: resumo})
            print(f"    sondagem OK: json_valido={resumo['json_valido']}",
                  file=sys.stderr)
        except (cm.BudgetExceededError, cm.ModeloIrrecuperavelError) as e:
            pulados["gemini-2.0-flash"] = (
                f"sondagem de 1 bucket falhou: {e} — confirmação de que a "
                f"alocação zero da sessão anterior persiste após o reset."
            )
            print(f"    PULADO (confirmação da alocação zero): {e}", file=sys.stderr)
        print(f"    chamadas usadas até agora: {budget.used}/{budget.limit}",
              file=sys.stderr)

    # --- Checagem factual de idioma por bucket/modelo ---
    idiomas: dict[str, dict[str, str]] = {}
    for modelo, (buckets, _metricas) in resultados.items():
        idiomas[modelo] = {}
        for b in buckets:
            idiomas[modelo][b.nome] = detectar_idioma(texto_do_bucket(b))

    # --- Re-renderiza o COMPARACAO.md com a função já existente do harness ---
    md = cm.render_comparacao_md(resultados, pulados, budget)
    md += "\n\n## Checagem factual de idioma por bucket (não é veredito de qualidade)\n\n"
    md += (
        "Contagem mecânica de stopwords pt-BR vs. inglês nos nomes dos temas "
        "de cada bucket — checagem de FORMATO (§D.4 da spec exige saída "
        "sempre em pt-BR), não avaliação de conteúdo/coerência/spoiler.\n\n"
    )
    md += "| Modelo | Bucket | Idioma detectado |\n|---|---|---|\n"
    for modelo, por_bucket in idiomas.items():
        for bucket_nome, idioma in por_bucket.items():
            marca = " ⚠️" if idioma not in ("pt-BR",) else ""
            md += f"| {modelo} | {bucket_nome} | {idioma}{marca} |\n"

    if contingencia is not None:
        md += "\n\n## Contingência acionada\n\n"
        md += f"- **Cenário:** {contingencia['cenario']}\n"
        md += f"- **Horário (UTC):** {contingencia['horario_utc']}\n"
        md += f"- **Backoff + retentativa executados:** {contingencia['houve_backoff_e_retentativa']}\n"
        md += f"- **Erro literal (sem chave):** `{contingencia['erro_literal']}`\n"

    md_path = cm.OUT_DIR / "COMPARACAO.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"\n=== Fim ===", file=sys.stderr)
    print(f"Modelos com resultado: {list(resultados)}", file=sys.stderr)
    print(f"Modelos pulados: {list(pulados)}", file=sys.stderr)
    print(f"Chamadas Gemini gastas nesta sessão: {budget.used}/{budget.limit}",
          file=sys.stderr)
    print(f"Contingência acionada: {contingencia is not None}", file=sys.stderr)
    print(f"Relatório: {md_path.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
