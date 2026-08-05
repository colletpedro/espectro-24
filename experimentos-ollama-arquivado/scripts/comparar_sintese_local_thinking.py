#!/usr/bin/env python3
"""Experimento 2 (NÃO é bump de versão): síntese §D local com THINKING
LIGADO, para testar se o raciocínio corrige a inflação de frequências
observada no experimento 1 (think=false) — ver COMPARACAO_LOCAL.md.

Reusa a mesma abordagem do harness do experimento 1
(`scripts/comparar_sintese_local.py`): reviews do `cure` só do cache
(`Fetcher(offline=True)`, zero rede), mesmos prompts byte-idênticos do
pipeline de produção. A ÚNICA variável é thinking ligado + teto de geração
maior (`num_predict=16000`, Tarefa 1) — usa `ollama_chat_bruto` (não
`ollama_client_call`) para capturar `message.thinking`, `done_reason`,
`eval_count`, `prompt_eval_count` por chamada.

ZERO chamadas Gemini, ZERO requisições Letterboxd, ZERO requisições TMDB.
NÃO toca em `resultado/cure.json` nem em `resultado/experimento_local/cure__ollama.json`
(experimento 1) — grava só em `resultado/experimento_local/cure__ollama_thinking.json`.

Se qualquer chamada truncar (`done_reason == "length"`) ou não couber em
`num_ctx` pela estimativa de tokens, o script PARA e reporta — não
prossegue em silêncio com entrada/saída truncada.
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

from espectro24.config import OLLAMA_NUM_CTX  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import run_pipeline  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    build_system_prompt,
    build_user_message,
    ollama_chat_bruto,
    synthesize_bucket,
)

SLUG = "cure"
MODEL = "qwen3-espectro"
NUM_PREDICT_THINKING = 16000   # Tarefa 1.2 — teto de geração com thinking ligado
# ~15 tokens/s medido -> pior caso 16000/15 ~= 1067s. OLLAMA_TIMEOUT_S (300s,
# calibrado para o teto de produção de 3000) estourava ReadTimeout bem antes
# de qualquer geração terminar — não é falha do servidor, é cronômetro curto
# demais para este teto. Margem generosa acima do pior caso medido.
TIMEOUT_THINKING_S = 1400
OUT_PATH = ROOT / "resultado" / "experimento_local" / "cure__ollama_thinking.json"


class Truncamento(RuntimeError):
    """Levantada quando uma chamada bate no teto de geração — o experimento
    PARA em vez de aceitar uma resposta possivelmente incompleta."""


def _aproxima_tokens(texto: str) -> int:
    return round(len(texto) / 3.5)


def _checar_contexto(bucket_nome: str, system: str, user: str) -> int:
    """Tarefa 1.4 — confere que entrada + thinking(<=num_predict) + saída
    cabe em num_ctx ANTES de chamar. Retorna a estimativa de tokens de
    entrada para o relatório."""
    entrada_tokens = _aproxima_tokens(system) + _aproxima_tokens(user)
    pior_caso = entrada_tokens + NUM_PREDICT_THINKING
    print(f"[{bucket_nome}] entrada~{entrada_tokens} tokens + "
          f"num_predict={NUM_PREDICT_THINKING} = {pior_caso} "
          f"(num_ctx={OLLAMA_NUM_CTX})", file=sys.stderr)
    if pior_caso > OLLAMA_NUM_CTX:
        raise Truncamento(
            f"[{bucket_nome}] entrada({entrada_tokens}) + "
            f"num_predict({NUM_PREDICT_THINKING}) = {pior_caso} > "
            f"num_ctx({OLLAMA_NUM_CTX}) — NÃO CABE. Pare e ajuste antes de "
            f"chamar (mais contexto ou menos reviews por chamada).")
    return entrada_tokens


def _call_com_metadados(log: list[dict]):
    """Envolve `ollama_chat_bruto` (think=True) para devolver só o texto
    (contrato que `synthesize_bucket` espera) enquanto registra thinking,
    tokens e done_reason de CADA chamada real."""
    def _call(system: str, user: str, model: str) -> str:
        t0 = time.time()
        data = ollama_chat_bruto(system, user, model, think=True,
                                 num_predict=NUM_PREDICT_THINKING,
                                 timeout_s=TIMEOUT_THINKING_S)
        dt = time.time() - t0
        msg = data.get("message") or {}
        thinking_txt = msg.get("thinking") or ""
        content_txt = msg.get("content") or ""
        done_reason = data.get("done_reason", "?")
        eval_count = data.get("eval_count")
        prompt_eval_count = data.get("prompt_eval_count")

        # divisão thinking/saída é uma ESTIMATIVA proporcional por
        # caracteres sobre eval_count (Ollama não separa os dois em tokens
        # — eval_count é thinking+saída somados, um único orçamento).
        total_chars = len(thinking_txt) + len(content_txt)
        if eval_count and total_chars:
            thinking_tokens_est = round(eval_count * len(thinking_txt) / total_chars)
            saida_tokens_est = eval_count - thinking_tokens_est
        else:
            thinking_tokens_est = eval_count if content_txt == "" else 0
            saida_tokens_est = eval_count - thinking_tokens_est if eval_count else 0

        registro = {
            "tempo_s": round(dt, 2),
            "done_reason": done_reason,
            "prompt_eval_count": prompt_eval_count,
            "eval_count_total": eval_count,
            "thinking_tokens_estimado": thinking_tokens_est,
            "saida_tokens_estimado": saida_tokens_est,
            "thinking_chars": len(thinking_txt),
            "conteudo_chars": len(content_txt),
        }
        log.append(registro)
        print(f"    chamada {len(log)}: {dt:.1f}s | done_reason={done_reason} | "
              f"eval_count={eval_count} (thinking~{thinking_tokens_est}, "
              f"saída~{saida_tokens_est}) | thinking_chars={len(thinking_txt)} | "
              f"conteudo_chars={len(content_txt)}", file=sys.stderr)

        if done_reason == "length":
            raise Truncamento(
                f"Chamada bateu no teto de geração (num_predict="
                f"{NUM_PREDICT_THINKING}) antes de terminar — done_reason="
                f"'length'. eval_count={eval_count}, thinking_chars="
                f"{len(thinking_txt)}, conteudo_chars={len(content_txt)}. "
                f"16000 é INSUFICIENTE para esta chamada.")
        return content_txt
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
        "think": True,
        "num_predict": NUM_PREDICT_THINKING,
        "num_ctx": OLLAMA_NUM_CTX,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "buckets": [],
    }

    t_total0 = time.time()
    for b in buckets:
        system = build_system_prompt(b.nome)
        user = build_user_message(b)
        try:
            _checar_contexto(b.nome, system, user)
        except Truncamento as e:
            print(f"\nPARANDO (Tarefa 1.4): {e}", file=sys.stderr)
            return 1

        print(f"[{b.nome}] {len(b.reviews_analisadas)} reviews — "
              f"chamando Ollama (thinking=on)...", file=sys.stderr)
        chamadas_log: list[dict] = []
        call = _call_com_metadados(chamadas_log)
        t0 = time.time()
        try:
            synthesize_bucket(b, client_call=call, model=MODEL)
        except Truncamento as e:
            print(f"\nPARANDO (Tarefa 1.3 — truncamento detectado): {e}",
                  file=sys.stderr)
            print("16000 tokens de num_predict foram INSUFICIENTES para "
                  "esta chamada com thinking ligado. Reporte, não ajuste "
                  "em silêncio.", file=sys.stderr)
            return 1
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

    algum_truncou = any(
        c["done_reason"] == "length"
        for bd in resultado["buckets"] for c in bd["chamadas"])
    if algum_truncou:
        print("\n⚠️  ATENÇÃO: pelo menos uma chamada teve done_reason="
              "'length' — ver Tarefa 1.3.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
