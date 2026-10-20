"""Fase 1 — gera a síntese do MODELO BASE escolhido (sem treino) nos 5 filmes de
TREINO sorteados (`finetune/especificidade/validacao_filmes.json`), para os 30
títulos "locais" da validação da medida de especificidade.

Só roda DEPOIS da escolha do modelo base (critério pré-registrado). Windows,
FORA do Claude Code. Recusa filme que não seja de treino.

Mesmo prompt da produção (`synthesize.build_system_prompt` /
`build_user_message`, remontados do bruto), raciocínio desligado, saída JSON,
`num_predict` 3.000 (o teto da síntese de produção). `num_ctx` POR CHAMADA,
pela regra do gate 0 (decisão 6): tokens do prompt + teto de saída + 10%,
arredondado para cima a 1.024 — com os tokens do prompt pela cota
conservadora de 0,35 token/caractere (sem tokenizer no Windows).

Saída: `finetune/especificidade/geracao_base/<modelo>/<slug>__<bucket>.json`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

ARQ_FILMES = K.FINETUNE_DIR / "especificidade" / "validacao_filmes.json"
TETO_SAIDA = 3000
MARGEM = 0.10
TOKENS_POR_CHAR = 0.35


def num_ctx_da_chamada(system: str, user: str) -> int:
    prompt = math.ceil(TOKENS_POR_CHAR * (len(system) + len(user)))
    return int(math.ceil((prompt + TETO_SAIDA) * (1 + MARGEM) / 1024) * 1024)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True, help="o modelo base ESCOLHIDO, como o Ollama o chama")
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--ram-livre-min-gb", type=float, default=2.0)
    a = ap.parse_args()
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    from espectro24.local_ollama import LLMLocalFalhou, resposta_json_local
    from espectro24.synthesize import _parse_llm_json
    import viabilidade_ollama as V

    split, sel = K.ler_json(a.split), K.ler_json(ARQ_FILMES)
    filmes = sel["filmes_geracao"]
    ruins = [f for f in filmes if f not in split["treino"]]
    if ruins:
        raise SystemExit(f"filme(s) fora do TREINO: {ruins}")
    pasta = (K.FINETUNE_DIR / "especificidade" / "geracao_base"
             / re.sub(r"[^\w.-]+", "_", a.modelo))
    pasta.mkdir(parents=True, exist_ok=True)
    for slug in filmes:
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        for b in K.buckets_remontados(slug, pub):
            arq = pasta / f"{slug}__{b.nome}.json"
            if arq.exists():
                continue                                    # retomável
            _, livre = V.ram_gb()
            if livre < a.ram_livre_min_gb:
                raise SystemExit(f"RAM livre {livre:.1f} GB < {a.ram_livre_min_gb}: parado")
            s, u = K.prompt_sintese(b)
            ctx = num_ctx_da_chamada(s, u)
            reg = {"modelo": a.modelo, "slug": slug, "bucket": b.nome, "num_ctx": ctx,
                   "num_predict": TETO_SAIDA, "think": "false",
                   "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u),
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            t0 = time.time()
            try:
                r = resposta_json_local(s, u, estagio="sintese", modelo=a.modelo, schema="json",
                                        prazo=3600, num_predict=TETO_SAIDA, num_ctx=ctx,
                                        think="false")
                reg.update({k: r.get(k) for k in ("modelo_efetivo", "finish_reason", "latencia_s",
                                                  "prompt_eval_count", "eval_count")})
                reg["texto"] = r["texto"]
                try:
                    d = _parse_llm_json(r["texto"])
                    reg["temas"] = [t.get("tema") for t in d.get("temas") or []]
                    reg["json_parseia"] = True
                except ValueError as e:
                    reg["json_parseia"] = False
                    reg["erro_json"] = str(e)[:200]
            except LLMLocalFalhou as e:
                reg.update({"ok": False, "erro": str(e)[:500]})
            reg["parede_s"] = round(time.time() - t0, 1)
            arq.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{slug}/{b.nome}: {len(reg.get('temas') or [])} títulos · {reg['parede_s']} s",
                  flush=True)


if __name__ == "__main__":
    main()
