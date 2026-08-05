#!/usr/bin/env python3
"""Experimento 3 (NÃO é bump de versão): duas hipóteses contra a inflação
de frequências da síntese §D local (ver COMPARACAO_LOCAL.md, exp. 1 e 2).

Hipóteses:
  (A) o prompt pede "mencoes_aproximadas" e o modelo ESTIMA; uma instrução
      explícita de CONTAGEM corrigiria — think=false, num_predict=3000.
  (B) raciocínio CURTO E LIMITADO ajuda (ao contrário do raciocínio livre
      do experimento 2, que divergiu) — CONTAGEM + instrução de raciocínio
      breve, think=true, num_predict=6000.

O prompt de produção (`build_system_prompt`) NUNCA é editado — os blocos
de experimento são ANEXADOS por cima dele em tempo de execução, via um
monkeypatch temporário e escopado (restaurado logo depois de cada
chamada) de `espectro24.synthesize.build_system_prompt`. SPEC.md e
synthesize.py não são tocados por este script.

Reviews 100% do cache (`Fetcher(offline=True)`) — confirma `n_network=0`
antes de qualquer chamada. ZERO Gemini, ZERO Letterboxd, ZERO TMDB.

Robustez (lição do experimento 2 — 1 bucket nunca rodou porque o
anterior travou o script inteiro):
- grava o resultado de CADA bucket assim que ele termina (sucesso OU
  falha), em arquivo próprio — nunca só no final;
- timeout de 600s por CHAMADA; se estourar, registra a falha DAQUELE
  bucket e segue para o próximo (não aborta o experimento inteiro);
- registra por chamada: thinking_chars, conteudo_chars, eval_count,
  done_reason, tempo.

NÃO toca em resultado/cure.json, resultado/experimento_local/cure__ollama.json
(exp.1) nem resultado/experimento_local/cure__ollama_thinking.json (exp.2).
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

import espectro24.synthesize as synth_mod  # noqa: E402
from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import run_pipeline  # noqa: E402
from espectro24.synthesize import ollama_chat_bruto, synthesize_bucket  # noqa: E402

SLUG = "cure"
MODEL = "qwen3-espectro"
TIMEOUT_S = 600   # Tarefa 2 — timeout por CHAMADA (não por bucket/variante)
OUT_ROOT = ROOT / "resultado" / "experimento_local"

BLOCO_CONTAGEM = """CONTAGEM DAS MENÇÕES
Para cada tema identificado, percorra as reviews recebidas uma a uma e conte quantas delas mencionam aquele tema. O valor de mencoes_aproximadas deve ser o resultado dessa contagem, não uma impressão geral. Um tema mencionado por quase todas as reviews é raro: se você chegar a um número próximo do total, releia e confirme antes de registrá-lo."""

BLOCO_RACIOCINIO_BREVE = """Antes de responder, raciocine de forma breve e objetiva: liste os temas candidatos e faça a contagem de cada um. Não rascunhe a resposta várias vezes nem reescreva formulações alternativas — poucas linhas de raciocínio bastam."""

VARIANTES = {
    "variante_a": {
        "blocos": [BLOCO_CONTAGEM],
        "think": False,
        "num_predict": 3000,
    },
    "variante_b": {
        "blocos": [BLOCO_CONTAGEM, BLOCO_RACIOCINIO_BREVE],
        "think": True,
        "num_predict": 6000,
    },
}


def _prompt_com_blocos(blocos: list[str]):
    """Devolve uma função substituta de `build_system_prompt`: o prompt de
    PRODUÇÃO (função original, byte-idêntica) + blocos anexados por baixo.
    Nunca edita a função original nem qualquer arquivo de prompt."""
    original = synth_mod.build_system_prompt

    def wrapped(bucket_nome: str) -> str:
        partes = [original(bucket_nome)] + blocos
        return "\n\n".join(partes)
    return wrapped


def _call_com_metadados(log: list[dict], *, think: bool, num_predict: int):
    def _call(system: str, user: str, model: str) -> str:
        t0 = time.time()
        data = ollama_chat_bruto(system, user, model, think=think,
                                 num_predict=num_predict, timeout_s=TIMEOUT_S)
        dt = time.time() - t0
        msg = data.get("message") or {}
        thinking_txt = msg.get("thinking") or ""
        content_txt = msg.get("content") or ""
        registro = {
            "tempo_s": round(dt, 2),
            "done_reason": data.get("done_reason", "?"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            # nota técnica confirmada no experimento 2: no Ollama, eval_count
            # NÃO inclui os tokens de thinking — só mede thinking por chars.
            "eval_count": data.get("eval_count"),
            "thinking_chars": len(thinking_txt),
            "conteudo_chars": len(content_txt),
        }
        log.append(registro)
        print(f"      chamada {len(log)}: {dt:.1f}s | "
              f"done_reason={registro['done_reason']} | "
              f"eval_count={registro['eval_count']} | "
              f"thinking_chars={registro['thinking_chars']} | "
              f"conteudo_chars={registro['conteudo_chars']}", file=sys.stderr)
        return content_txt
    return _call


def _rodar_bucket(bucket, variante_nome: str, cfg: dict, out_dir: Path):
    out_path = out_dir / f"{bucket.nome}.json"
    chamadas_log: list[dict] = []
    call = _call_com_metadados(chamadas_log, think=cfg["think"],
                               num_predict=cfg["num_predict"])

    synth_mod.build_system_prompt = _prompt_com_blocos(cfg["blocos"])
    t0 = time.time()
    erro = None
    try:
        synthesize_bucket(bucket, client_call=call, model=MODEL)
    except Exception as e:
        erro = str(e)
        print(f"    FALHOU: {e}", file=sys.stderr)
    finally:
        synth_mod.build_system_prompt = _ORIGINAL_BUILD_SYSTEM_PROMPT
    dt = time.time() - t0

    registro = {
        "variante": variante_nome,
        "bucket": bucket.nome,
        "n_validas": len(bucket.reviews_analisadas),
        "tempo_total_s": round(dt, 2),
        "n_chamadas": len(chamadas_log),
        "chamadas": chamadas_log,
        "falhou": erro is not None,
        "erro": erro,
        "idioma_invalido": bucket.idioma_invalido,
        "escopo_suspeito": bucket.escopo_suspeito,
        "temas": [asdict(t) for t in bucket.temas] if erro is None else [],
        "observacao_geral": bucket.observacao_geral if erro is None else "",
    }
    out_path.write_text(json.dumps(registro, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"    gravado em {out_path} (falhou={registro['falhou']})",
          file=sys.stderr)
    return registro


_ORIGINAL_BUILD_SYSTEM_PROMPT = synth_mod.build_system_prompt


def _carregar_buckets_frescos():
    fetcher = Fetcher(cache_dir=str(ROOT / "resultado" / "cache"), offline=True)
    buckets, _niveis, _distrib = run_pipeline(
        fetcher, SLUG, datetime.now(timezone.utc).isoformat(),
        synth=False, distribuicao=False,
    )
    if fetcher.n_network != 0:
        raise RuntimeError(
            f"{fetcher.n_network} requisição(ões) de rede seriam feitas — esperado 0.")
    return buckets


def main() -> int:
    print(f"Carregando reviews de '{SLUG}' do cache (offline, zero rede)...",
          file=sys.stderr)
    try:
        buckets_check = _carregar_buckets_frescos()
    except RuntimeError as e:
        print(f"ABORTANDO: {e}", file=sys.stderr)
        return 1
    print(f"OK: {len(buckets_check)} buckets, 0 requisições de rede.",
          file=sys.stderr)

    resumo = {"gerado_em": datetime.now(timezone.utc).isoformat(), "variantes": {}}

    for variante_nome, cfg in VARIANTES.items():
        print(f"\n=== {variante_nome} (think={cfg['think']}, "
              f"num_predict={cfg['num_predict']}) ===", file=sys.stderr)
        out_dir = OUT_ROOT / variante_nome
        out_dir.mkdir(parents=True, exist_ok=True)

        buckets = _carregar_buckets_frescos()   # frescos, não reaproveita entre variantes
        registros = []
        for b in buckets:
            print(f"  [{b.nome}] {len(b.reviews_analisadas)} reviews...",
                  file=sys.stderr)
            registros.append(_rodar_bucket(b, variante_nome, cfg, out_dir))

        resumo["variantes"][variante_nome] = {
            "think": cfg["think"],
            "num_predict": cfg["num_predict"],
            "buckets": [
                {"bucket": r["bucket"], "falhou": r["falhou"],
                 "n_temas": len(r["temas"]), "n_chamadas": r["n_chamadas"],
                 "tempo_total_s": r["tempo_total_s"]}
                for r in registros
            ],
        }

    resumo_path = OUT_ROOT / "v3_resumo.json"
    resumo_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"\nResumo gravado em {resumo_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
