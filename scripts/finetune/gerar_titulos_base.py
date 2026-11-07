"""Fase 1 — gera a síntese do MODELO BASE (Qwen3-8B SEM treino) nos 5 filmes de
TREINO sorteados (`finetune/especificidade/validacao_filmes.json`), para os 30
bullets "locais" da validação da medida de especificidade.

Revisão de 2026-10-30 (PROTOCOLO_v2): grava o BULLET COMPLETO da unidade v2
(`tema` + `exemplo_parafraseado`, e o texto `tema — exemplo` que a medida lê),
não só o título. Os números e as contagens não entram no texto.

CONDICIONAL AO E4: só roda depois de o E4 do Qwen3-8B passar. O script recusa
se não houver em `finetune/viabilidade/` um `importar_espectro-qwen3-8b_*.json`
com `E4_importa_e_gera: true`. Windows, FORA do Claude Code.

- Modelo: `hf.co/unsloth/Qwen3-8B-GGUF:Q4_K_M`, o MESMO caminho GGUF do E5,
  raciocínio desligado (`think` false), JSON livre, `num_predict` 3.000 (o teto
  da síntese de produção).
- Prompt: o da produção (`synthesize.build_system_prompt` /
  `build_user_message`, remontados do bruto por `comum.prompt_sintese`).
- `num_ctx` POR CHAMADA, pela regra do gate 0: (tokens do prompt + 3.000) ×
  1,10, arredondado para cima no múltiplo de 1.024. Os tokens do prompt são
  EXATOS, contados no Mac com o tokenizer do Qwen3-8B (`plano`), e gravados em
  `geracao_base/plano.json` com o sha256 do system e do user; no Windows,
  `gerar` remonta o prompt e recusa se o sha não bater (a cota de 0,35
  token/caractere saiu: no par do E5 a contagem exata deu 8.019, o mesmo
  `prompt_eval_count` do Ollama).
- Filmes: os 5 de TREINO, nos 3 buckets; recusa filme de validação ou de teste.
- Partida limpa do Ollama antes da série (`viabilidade_ollama.partida_limpa`);
  servidor próprio depois.
- Guarda de LATÊNCIA (`_latencia.GuardaDeLatencia`), não de RAM: a chamada
  anômala termina e é gravada; a próxima não sai. A 1ª chamada (carga) não
  entra na janela.
- Retomável: um par com `ok: true` gravado não é refeito; um que falhou é.
- Saída: `finetune/especificidade/geracao_base/<slug>__<bucket>.json` e
  `manifesto.json` com o sha256 de cada arquivo, reescrito a cada par.

Subcomandos:
    plano   — (Mac) conta os tokens e grava `plano.json`
    gerar   — (Windows) roda os 15 pares que faltam
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

ARQ_FILMES = K.FINETUNE_DIR / "especificidade" / "validacao_filmes.json"
PASTA = K.FINETUNE_DIR / "especificidade" / "geracao_base"
ARQ_PLANO = PASTA / "plano.json"
ARQ_MANIFESTO = PASTA / "manifesto.json"
VIABILIDADE = K.FINETUNE_DIR / "viabilidade"
MODELO = "hf.co/unsloth/Qwen3-8B-GGUF:Q4_K_M"     # o do E5 (viabilidade_ollama.CANDIDATOS)
NOME_IMPORTADO = "espectro-qwen3-8b"                 # o do E4 (importar-pasta)
TOKENIZER = "Qwen3-8B"
FILMES = ("fight-club", "hereditary", "pinocchio-2022", "soul-2020", "the-wailing")
TETO_SAIDA = 3000
MARGEM = 0.10


def num_ctx_da_chamada(tokens_prompt: int) -> int:
    return K.arredondar(int((tokens_prompt + TETO_SAIDA) * (1 + MARGEM)))  # como o inventário


def texto_do_bullet(tema: str, exemplo: str) -> str:
    """O mesmo de `especificidade_bullet.texto_do_bullet` (não importado: ele
    puxa o numpy da medida, que o Windows não precisa)."""
    return f"{tema.strip()} — {exemplo.strip()}"


def bullets(d: dict) -> list[dict]:
    fora = []
    for t in d.get("temas") or []:
        tema, ex = t.get("tema"), t.get("exemplo_parafraseado")
        completo = isinstance(tema, str) and isinstance(ex, str) and tema.strip() and ex.strip()
        fora.append({"tema": tema, "exemplo_parafraseado": ex,
                     "texto": texto_do_bullet(tema, ex) if completo else None,
                     "completo": bool(completo)})
    return fora


def filmes_conferidos(split: dict) -> list[str]:
    sel = K.ler_json(ARQ_FILMES)["filmes_geracao"]
    if tuple(sel) != FILMES:
        raise SystemExit(f"validacao_filmes.json mudou: {sel} ≠ {list(FILMES)}")
    proibidos = set(split["validacao"]) | set(split["teste"]) | set(K.REFERENCIA_5)
    ruins = [f for f in sel if f not in split["treino"] or f in proibidos]
    if ruins:
        raise SystemExit(f"filme(s) fora do TREINO (validação/teste recusados): {ruins}")
    return list(sel)


def pares(split: dict):
    for slug in filmes_conferidos(split):
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        bs = list(K.buckets_remontados(slug, pub))
        if sorted(b.nome for b in bs) != sorted(K.BUCKETS):
            raise SystemExit(f"{slug}: buckets {[b.nome for b in bs]}, esperados os 3")
        for b in bs:
            s, u = K.prompt_sintese(b)
            yield slug, b.nome, s, u


def cmd_plano(a) -> None:
    tok = K.carregar_tokenizer(TOKENIZER, a.tokenizers)
    linhas = []
    for slug, bucket, s, u in pares(K.ler_json(a.split)):
        n = K.contar(tok, K.chat("qwen", s, u, None))
        linhas.append({"slug": slug, "bucket": bucket, "tokens_prompt": n,
                       "num_ctx": num_ctx_da_chamada(n),
                       "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u)})
    plano = {"gerado_por": "scripts/finetune/gerar_titulos_base.py plano", "modelo": MODELO,
             "tokenizer": TOKENIZER, "regra_num_ctx": "(tokens do prompt + 3.000) × 1,10, "
             "arredondado para cima no múltiplo de 1.024", "num_predict": TETO_SAIDA,
             "pares": linhas}
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_PLANO.write_text(json.dumps(plano, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"gravado: {ARQ_PLANO} ({len(linhas)} pares, sha256 {K.sha256_arquivo(ARQ_PLANO)})")


def exigir_e4() -> Path:
    for arq in sorted(VIABILIDADE.glob(f"importar_{NOME_IMPORTADO}_*.json"), reverse=True):
        if K.ler_json(arq).get("E4_importa_e_gera") is True:
            return arq
    raise SystemExit(f"E4 do Qwen3-8B não passou (nenhum importar_{NOME_IMPORTADO}_*.json "
                     f"com E4_importa_e_gera true em {VIABILIDADE}): a geração é condicional")


def gravar_manifesto() -> None:
    arqs = sorted(p for p in PASTA.glob("*.json") if p != ARQ_MANIFESTO)
    ARQ_MANIFESTO.write_text(json.dumps(
        {p.name: K.sha256_arquivo(p) for p in arqs}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")


def ja_feito(arq: Path) -> bool:
    return arq.exists() and K.ler_json(arq).get("ok") is True


def cmd_gerar(a) -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    from espectro24.local_ollama import LLMLocalFalhou, resposta_json_local
    from espectro24.synthesize import _parse_llm_json
    from _latencia import GuardaDeLatencia, LatenciaAnomala
    import viabilidade_ollama as V

    e4 = exigir_e4()
    plano = {(p["slug"], p["bucket"]): p for p in K.ler_json(ARQ_PLANO)["pares"]}
    todos = list(pares(K.ler_json(a.split)))
    if {(x[0], x[1]) for x in todos} != set(plano):
        raise SystemExit("plano.json não cobre exatamente os 15 pares: rode `plano` no Mac")
    falta = [x for x in todos if not ja_feito(PASTA / f"{x[0]}__{x[1]}.json")]
    print(f"E4: {e4.name} · {len(todos) - len(falta)} feitos, {len(falta)} a fazer", flush=True)
    if not falta:
        gravar_manifesto()
        return
    partida = V.partida_limpa(a.ram_partida_min_gb, a.espera_ram_s)
    if not partida["limpa"]:
        raise SystemExit(f"partida contaminada, nada foi gerado: {partida}")
    guarda = GuardaDeLatencia()
    guarda.ignorar_proxima()                      # a 1ª paga a carga do modelo
    chamar = guarda.envolver(resposta_json_local)
    srv = V.subir_ollama()
    try:
        for slug, bucket, s, u in falta:
            p = plano[(slug, bucket)]
            if (K.sha256_texto(s), K.sha256_texto(u)) != (p["system_sha256"], p["user_sha256"]):
                raise SystemExit(f"{slug}/{bucket}: o prompt remontado não é o do plano.json")
            reg = {"modelo": MODELO, "slug": slug, "bucket": bucket, "num_ctx": p["num_ctx"],
                   "tokens_prompt_plano": p["tokens_prompt"], "num_predict": TETO_SAIDA,
                   "think": "false", "system_sha256": p["system_sha256"],
                   "user_sha256": p["user_sha256"], "partida": partida,
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            t0 = time.time()
            anomala = None
            try:
                r = chamar(s, u, estagio="sintese", modelo=MODELO, schema="json", prazo=3600,
                           num_predict=TETO_SAIDA, num_ctx=p["num_ctx"], think="false")
                reg.update({k: r.get(k) for k in ("modelo_efetivo", "finish_reason", "latencia_s",
                                                  "leitura_prompt_s", "geracao_s", "carga_s",
                                                  "prompt_eval_count", "eval_count")})
                reg["texto"] = r["texto"]
                reg["ok"] = True
                try:
                    reg["bullets"] = bullets(_parse_llm_json(r["texto"]))
                    reg["json_parseia"] = True
                except ValueError as e:
                    reg.update({"json_parseia": False, "erro_json": str(e)[:200]})
            except LLMLocalFalhou as e:
                reg.update({"ok": False, "erro": str(e)[:500]})
            reg["parede_s"] = round(time.time() - t0, 1)
            if guarda.pendente is not None:
                anomala = guarda.pendente
                reg["latencia_anomala"] = str(anomala)
            arq = PASTA / f"{slug}__{bucket}.json"
            arq.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
            gravar_manifesto()
            print(f"{slug}/{bucket}: {len(reg.get('bullets') or [])} bullets · "
                  f"ctx {p['num_ctx']} · {reg['parede_s']} s", flush=True)
            if anomala is not None:
                raise anomala
    except LatenciaAnomala as e:
        raise SystemExit(f"PAUSA pela guarda de latência ({e}); o par lento foi gravado. "
                         f"Confira o Ollama e rode de novo (retoma).")
    finally:
        srv.terminate()
        V.matar_ollama()


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plano", help="(Mac) tokens exatos do prompt e num_ctx de cada par")
    p.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    p.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    g = sub.add_parser("gerar", help="(Windows) gera os pares que faltam")
    g.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    g.add_argument("--ram-partida-min-gb", type=float, default=6.0)
    g.add_argument("--espera-ram-s", type=float, default=90.0)
    a = ap.parse_args()
    {"plano": cmd_plano, "gerar": cmd_gerar}[a.cmd](a)


if __name__ == "__main__":
    main()
