"""Fase 2 — gera a SÍNTESE nos 30 filmes de TESTE, para o modelo base e, depois,
para o treinado. PREPARADO, NÃO RODADO (2026-10-31).

Os dois lados passam pelo mesmo caminho: GGUF Q4_K_M exportado no Kaggle pela
mesma função, importado no Ollama do Windows com o Modelfile canônico
(`viabilidade_ollama.py importar-pasta`, o do E4) e chamado pelo caminho de
produção: `synthesize.synthesize_bucket` (a mesma retentativa de produção:
1 nova chamada em JSON inválido; 1 retentativa com `_REFORCO_VALIDACAO` se
idioma ou escopo falharem) com `local_ollama.resposta_json_local` injetado
(`think` false, JSON livre, `num_predict` 3.000; amostragem e seed EXPLÍCITAS
em cada chamada — `PREREGISTRO_AVALIACAO.md`, seção 2, com o `DESVIO_P01.md`:
temperature 0,7, top_p 0,8, top_k 20, min_p 0, repeat_penalty 1,0, seed
20261019). A base é o export do kernel
`kaggle/kernel_base/exportar_base.py`, NÃO o `hf.co/unsloth/Qwen3-8B-GGUF`.

Travas:
- `ESPECTRO24_OLLAMA_TEMPERATURE` no ambiente aborta a geração (a amostragem
  é a do DESVIO_P01, passada em cada chamada);
- só filmes de TESTE de `split.json`; recusa qualquer outro (e qualquer filme
  que esteja também em treino ou validação); o bucket do Gemini
  (`a-brighter-summer-day/positivas`, `buckets_excluidos`) fica fora: 89 pares;
- o modelo é ESCOLHIDO pelo sha256 do GGUF do `log.json` do kernel
  (`--log-kernel`): a importação mais recente desse GGUF com
  `E4_importa_e_gera` true dá o nome no Ollama; recusa se o nome foi
  reimportado depois com outro GGUF, se base e treinado têm o mesmo nome ou o
  mesmo GGUF. Na base, o log tem de provar o
  adaptador identidade e a fusão sem alteração; no treinado, o commit do
  llama.cpp tem de ser o da base (`--log-kernel-base`): os dois só diferem
  pelo adaptador;
- `num_ctx` POR CHAMADA pela regra do gate 0: (tokens do prompt + 3.000) × 1,10,
  arredondado para cima no múltiplo de 1.024, com os tokens EXATOS do prompt
  contados no Mac (`plano`, tokenizer do Qwen3-8B, template sem aparar); no
  Windows o prompt é remontado e recusado se o sha256 não bater;
- ordem: `num_ctx` crescente (o outlier `500-days-of-summer/positivas` por
  último: se a memória não der, os 88 outros já estão gravados);
- partida limpa do Ollama antes da série; guarda de LATÊNCIA (4× a mediana das
  últimas 20, mínimo 10; a 1ª chamada, que paga a carga, não entra); guarda de
  RAM livre ≥ 2 GB DURANTE cada chamada (a mesma do `viabilidade_ollama`; não
  se desliga: se ela derrubar o servidor, a série para e o par fica gravado
  com `abortado_por_memoria`), com o pico de RAM/VRAM de cada chamada gravado;
- memória: par derrubado pela guarda de RAM é tentado de novo UMA vez (na
  próxima execução, depois de nova partida limpa); se cair de novo, fica
  `fora_por_memoria` (sai dos DOIS lados de toda comparação e não é refeito);
- retomável: par com `ok: true` (ou `fora_por_memoria`) não é refeito;
- saída: `finetune/fase2/sintese_<lado>/<slug>__<bucket>.json` e
  `manifesto.json` (sha256 de cada arquivo), reescrito a cada par. Grava cada
  tentativa (texto cru, tempos, se levou o reforço) e o bucket FINAL que a
  produção publicaria (`_construir_temas`, flags de idioma e escopo).

Subcomandos:
    plano   (Mac) tokens exatos e `num_ctx` dos 89 pares → `fase2/plano_teste.json`
    gerar   (Windows) `--lado base|treinado`
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

PASTA = K.FINETUNE_DIR / "fase2"
ARQ_PLANO = PASTA / "plano_teste.json"
VIABILIDADE = K.FINETUNE_DIR / "viabilidade"
TOKENIZER = "Qwen3-8B"
TETO_SAIDA = 3000
MARGEM = 0.10
RAM_LIVRE_MIN_GB = 2.0
# nomes que o `importar-pasta` dá (do `modelo` do log.json do kernel); só conferência:
# o modelo chamado é o importado com o sha256 do GGUF do log do kernel
LADOS = {"base": "espectro-qwen3-8b-base", "treinado": "espectro-qwen3-8b-treinado"}
# DESVIO_P01.md (substitui a temperatura 0,8 do PREREGISTRO_AVALIACAO.md, seção 2):
# os valores do model card do Qwen3-8B para o modo SEM raciocínio (README.md:328,
# revisão b968826d), repeat_penalty 1,0 explícito; o seed é o do juiz
# (`juiz_bullets_v2.SEED`). Passados em CADA chamada.
AMOSTRAGEM = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
              "repeat_penalty": 1.0}
SEED = 20261019
VAR_TEMPERATURA = "ESPECTRO24_OLLAMA_TEMPERATURE"
MAX_ABORTOS_MEMORIA = 2


def num_ctx_da_chamada(tokens_prompt: int) -> int:
    return K.arredondar(int((tokens_prompt + TETO_SAIDA) * (1 + MARGEM)))


def filmes_de_teste(split: dict) -> list[str]:
    outros = set(split["treino"]) | set(split["validacao"])
    ruins = [f for f in split["teste"] if f in outros]
    if ruins:
        raise SystemExit(f"filme(s) de teste também em treino/validação: {ruins}")
    return sorted(split["teste"])


def excluidos(split: dict) -> set[tuple[str, str]]:
    return {(b["slug"], b["bucket"]) for b in split["buckets_excluidos"]}


def pares(split: dict):
    for slug, nome, s, u, _ in buckets_de_teste(split):
        yield slug, nome, s, u


def buckets_de_teste(split: dict):
    fora = excluidos(split)
    teste = set(filmes_de_teste(split))
    for slug in sorted(teste):
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        bs = list(K.buckets_remontados(slug, pub))
        if sorted(b.nome for b in bs) != sorted(K.BUCKETS):
            raise SystemExit(f"{slug}: buckets {[b.nome for b in bs]}, esperados os 3")
        for b in bs:
            if (slug, b.nome) in fora:
                continue
            assert slug in teste
            s, u = K.prompt_sintese(b)
            yield slug, b.nome, s, u, b


def cmd_plano(a) -> None:
    split = K.ler_json(a.split)
    tok = K.carregar_tokenizer(TOKENIZER, a.tokenizers)
    linhas = []
    for slug, bucket, s, u in pares(split):
        n = K.contar(tok, K.chat("qwen", s, u, None))
        linhas.append({"slug": slug, "bucket": bucket, "tokens_prompt": n,
                       "num_ctx": num_ctx_da_chamada(n),
                       "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u)})
    linhas.sort(key=lambda p: (p["num_ctx"], p["slug"], p["bucket"]))
    plano = {"gerado_por": "scripts/finetune/gerar_sintese_teste.py plano",
             "tokenizer": TOKENIZER, "split_sha256": K.sha256_arquivo(a.split),
             "regra_num_ctx": "(tokens do prompt + 3.000) × 1,10, arredondado para cima no "
                              "múltiplo de 1.024", "num_predict": TETO_SAIDA,
             "buckets_excluidos": sorted(f"{s}/{b}" for s, b in excluidos(split)),
             "pares": linhas}
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_PLANO.write_text(json.dumps(plano, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"gravado: {ARQ_PLANO} ({len(linhas)} pares, {sum(p['tokens_prompt'] for p in linhas)} "
          f"tokens de prompt, num_ctx máx. {max(p['num_ctx'] for p in linhas)}, "
          f"sha256 {K.sha256_arquivo(ARQ_PLANO)})")


def _gguf_do_log(log: dict) -> str:
    g = [x for x in log.get("gguf_arquivos") or [] if x["nome"].endswith(".gguf")]
    if len(g) != 1:
        raise SystemExit(f"log do kernel sem exatamente 1 GGUF: {g}")
    return g[0]["sha256"]


def _importacoes() -> list[tuple[Path, dict]]:
    """Os `importar_<nome>_<AAAAMMDD_HHMMSS>.json`, do mais antigo ao mais recente."""
    arqs = sorted(VIABILIDADE.glob("importar_*.json"), key=lambda p: p.stem[-15:])
    return [(a, K.ler_json(a)) for a in arqs]


def modelo_pelo_sha(sha: str) -> tuple[str, str]:
    """(nome no Ollama, arquivo da importação) do GGUF com este sha256: a importação
    mais recente dele com E4 true; recusa se o nome foi reaproveitado DEPOIS por
    outro GGUF (o `ollama create` sobrescreve)."""
    imps = _importacoes()
    com = [(a, i) for a, i in imps if i.get("E4_importa_e_gera") is True
           and (i.get("importacao") or {}).get("gguf_sha256") == sha]
    if not com:
        raise SystemExit(f"nenhuma importação com E4 true do GGUF {sha[:12]}… do kernel")
    arq, imp = com[-1]
    nome = imp["importacao"]["nome_ollama"]
    depois = [i for a, i in imps if a.stem[-15:] > arq.stem[-15:]
              and (i.get("importacao") or {}).get("nome_ollama") == nome]
    if any((i.get("importacao") or {}).get("gguf_sha256") != sha for i in depois):
        raise SystemExit(f"o nome {nome} foi reimportado com OUTRO GGUF depois de {arq.name}: "
                         f"reimporte este GGUF (`importar-pasta`) antes de gerar")
    return nome, arq.name


def conferir_modelo(lado: str, nome: str | None, log_kernel: Path, log_base: Path | None) -> dict:
    log = K.ler_json(log_kernel)
    sha = _gguf_do_log(log)
    if lado == "base":
        if not (log.get("prova_adaptador") or {}).get("B_zero"):
            raise SystemExit("o log do kernel da base não prova lora_B = 0")
        if not (log.get("prova_fusao") or {}).get("ok"):
            raise SystemExit("o log do kernel da base não prova a fusão sem alteração")
    else:
        if log_base is None:
            raise SystemExit("--log-kernel-base é obrigatório no lado treinado")
        lb = K.ler_json(log_base)
        cb = (lb.get("llama_cpp") or {}).get("commit")
        ct = (log.get("llama_cpp") or {}).get("commit")
        if not cb or cb != ct:
            raise SystemExit(f"llama.cpp do treinado ({ct}) ≠ o da base ({cb}): os GGUF não "
                             f"diferem só pelo adaptador — reexporte a base com o mesmo commit")
        sha_base = _gguf_do_log(lb)
        if sha_base == sha:
            raise SystemExit("o GGUF do treinado é o da base (mesmo sha256)")
        nome_base, _ = modelo_pelo_sha(sha_base)
    escolhido, importacao = modelo_pelo_sha(sha)
    if lado == "treinado" and escolhido == nome_base:
        raise SystemExit(f"base e treinado com o mesmo nome no Ollama ({escolhido})")
    if nome and nome != escolhido:
        raise SystemExit(f"--nome {nome}, mas o GGUF do kernel está importado como {escolhido}")
    imp = K.ler_json(VIABILIDADE / importacao)
    return {"importacao": importacao, "nome_ollama": escolhido, "gguf_sha256": sha,
            "log_kernel": str(log_kernel), "log_kernel_sha256": K.sha256_arquivo(log_kernel),
            "modelfile_usado": imp["importacao"]["modelfile_usado"]}


def gravar_manifesto(pasta: Path) -> None:
    arqs = sorted(p for p in pasta.glob("*.json") if p.name != "manifesto.json")
    (pasta / "manifesto.json").write_text(json.dumps(
        {p.name: K.sha256_arquivo(p) for p in arqs}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")


def ja_feito(arq: Path) -> bool:
    if not arq.exists():
        return False
    reg = K.ler_json(arq)
    return reg.get("ok") is True or reg.get("fora_por_memoria") is True


def abortos_anteriores(arq: Path) -> int:
    return K.ler_json(arq).get("abortos_memoria", 0) if arq.exists() else 0


def recusar_temperatura_do_ambiente() -> None:
    if VAR_TEMPERATURA in os.environ:
        raise SystemExit(f"{VAR_TEMPERATURA} está no ambiente: a temperatura é a do "
                         f"DESVIO_P01 ({AMOSTRAGEM['temperature']}), passada em cada chamada — remova-a")


def bucket_final(b) -> dict:
    """O que a produção publicaria deste bucket (forma de `validar_publicado`)."""
    from dataclasses import asdict
    return {"temas": [asdict(t) for t in b.temas], "observacao_geral": b.observacao_geral,
            "n_validas": b.n_validas, "n_analisadas": len(b.reviews_analisadas),
            "idioma_invalido": b.idioma_invalido, "escopo_suspeito": b.escopo_suspeito}


def cliente_registrado(chamar, s: str, nome: str, num_ctx: int, tentativas: list):
    """O `client_call` que `synthesize_bucket` recebe: cada chamada vai ao Ollama
    com a configuração do pré-registro e fica gravada em `tentativas`."""
    def client_call(system: str, user: str, model: str) -> str:
        r = chamar(system, user, estagio="sintese", modelo=nome, schema="json", prazo=3600,
                   num_predict=TETO_SAIDA, num_ctx=num_ctx, think="false", seed=SEED,
                   amostragem=dict(AMOSTRAGEM))
        tentativas.append({"reforco": system != s, "system_sha256": K.sha256_texto(system),
                           "texto": r["texto"],
                           **{k: r.get(k) for k in ("modelo_efetivo", "finish_reason",
                                                    "latencia_s", "leitura_prompt_s",
                                                    "geracao_s", "carga_s",
                                                    "prompt_eval_count", "eval_count")}})
        return r["texto"]
    return client_call


def cmd_gerar(a) -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    recusar_temperatura_do_ambiente()
    import copy
    from espectro24.local_ollama import LLMLocalFalhou, resposta_json_local
    from espectro24.synthesize import _parse_llm_json, synthesize_bucket
    from _latencia import GuardaDeLatencia, LatenciaAnomala
    import viabilidade_ollama as V

    origem = conferir_modelo(a.lado, a.nome, a.log_kernel, a.log_kernel_base)
    nome = origem["nome_ollama"]
    split = K.ler_json(a.split)
    plano_doc = K.ler_json(ARQ_PLANO)
    if plano_doc["split_sha256"] != K.sha256_arquivo(a.split):
        raise SystemExit("split.json mudou desde o plano: rode `plano` no Mac")
    plano = {(p["slug"], p["bucket"]): p for p in plano_doc["pares"]}
    todos = {(x[0], x[1]): x for x in buckets_de_teste(split)}
    if set(todos) != set(plano):
        raise SystemExit("plano_teste.json não cobre exatamente os pares de teste: rode `plano`")
    teste = set(split["teste"])
    if any(slug not in teste for slug, _ in plano) or set(plano) & excluidos(split):
        raise SystemExit("o plano tem par fora do teste ou o bucket excluído: recusado")
    pasta = PASTA / f"sintese_{a.lado}"
    pasta.mkdir(parents=True, exist_ok=True)
    ordem = [(p["slug"], p["bucket"]) for p in plano_doc["pares"]]       # num_ctx crescente
    falta = [k for k in ordem if not ja_feito(pasta / f"{k[0]}__{k[1]}.json")]
    print(f"{a.lado}: {nome} · {origem['importacao']} · {len(ordem) - len(falta)} feitos, "
          f"{len(falta)} a fazer", flush=True)
    if not falta:
        gravar_manifesto(pasta)
        return
    partida = V.partida_limpa(a.ram_partida_min_gb, a.espera_ram_s)
    if not partida["limpa"]:
        raise SystemExit(f"partida contaminada, nada foi gerado: {partida}")
    guarda = GuardaDeLatencia()
    guarda.ignorar_proxima()                      # a 1ª paga a carga do modelo
    chamar = guarda.envolver(resposta_json_local)
    srv = V.subir_ollama()
    try:
        for chave in falta:
            slug, bucket, s, u, b = todos[chave]
            p = plano[chave]
            if (K.sha256_texto(s), K.sha256_texto(u)) != (p["system_sha256"], p["user_sha256"]):
                raise SystemExit(f"{slug}/{bucket}: o prompt remontado não é o do plano")
            reg = {"lado": a.lado, "modelo": nome, "origem": origem, "slug": slug,
                   "bucket": bucket, "num_ctx": p["num_ctx"],
                   "tokens_prompt_plano": p["tokens_prompt"], "num_predict": TETO_SAIDA,
                   "think": "false", "amostragem": AMOSTRAGEM, "seed": SEED,
                   "system_sha256": p["system_sha256"],
                   "user_sha256": p["user_sha256"], "partida": partida,
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            arq = pasta / f"{slug}__{bucket}.json"
            tentativas: list[dict] = []
            mon = V.Monitor(RAM_LIVRE_MIN_GB, ao_estourar=V.matar_ollama)
            mon.start()
            t0 = time.time()
            try:
                final = synthesize_bucket(copy.deepcopy(b), model=nome, client_call=cliente_registrado(
                    chamar, s, nome, p["num_ctx"], tentativas))
                reg["ok"] = True
                reg["bucket_final"] = bucket_final(final)
                reg["json_parseia"] = final.observacao_geral != "Falha ao obter JSON válido do LLM."
                reg["json_parseia_1a_tentativa"] = None
                if tentativas:                    # `sem_analise` não chama o modelo
                    try:
                        _parse_llm_json(tentativas[0]["texto"])
                        reg["json_parseia_1a_tentativa"] = True
                    except ValueError:
                        reg["json_parseia_1a_tentativa"] = False
            except LLMLocalFalhou as e:
                reg.update({"ok": False, "erro": str(e)[:500]})
            except LatenciaAnomala as e:      # a guarda barrou a retentativa: par refeito ao retomar
                reg.update({"ok": False, "erro": f"retentativa barrada pela guarda de latência: {e}"})
            finally:
                mon.parar.set()
                mon.join(timeout=5)
            reg["parede_s"] = round(time.time() - t0, 1)
            reg["memoria"] = {k: (round(v, 2) if isinstance(v, float) else v)
                              for k, v in mon.pico.items()}
            reg["tentativas"] = tentativas
            reg["n_chamadas"] = len(tentativas)
            reg["abortado_por_memoria"] = mon.estourou
            reg["abortos_memoria"] = abortos_anteriores(arq) + (1 if mon.estourou else 0)
            reg["fora_por_memoria"] = reg["abortos_memoria"] >= MAX_ABORTOS_MEMORIA
            pec = tentativas[0].get("prompt_eval_count") if tentativas else None
            if reg.get("ok") and pec != p["tokens_prompt"]:
                reg["aviso_tokens"] = f"prompt_eval_count {pec} ≠ plano {p['tokens_prompt']}"
            anomala = guarda.pendente
            if anomala is not None:
                reg["latencia_anomala"] = str(anomala)
            arq.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
            gravar_manifesto(pasta)
            print(f"{slug}/{bucket}: ok {reg.get('ok')} · json {reg.get('json_parseia')} · "
                  f"{reg['n_chamadas']} chamada(s) · "
                  f"ctx {p['num_ctx']} · {reg['parede_s']} s · RAM livre mín. "
                  f"{reg['memoria'].get('ram_livre_min_gb')} GB", flush=True)
            if mon.estourou:
                destino = ("fica FORA POR MEMÓRIA (sai dos dois lados de toda comparação)"
                           if reg["fora_por_memoria"] else
                           "será tentado UMA vez mais na próxima execução (partida limpa)")
                raise SystemExit(f"{slug}/{bucket}: a guarda de RAM derrubou o servidor (RAM "
                                 f"livre < {RAM_LIVRE_MIN_GB} GB). Par gravado; {destino}; a "
                                 f"série parou. Rode de novo para seguir; a guarda não é desligada.")
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
    g = sub.add_parser("gerar", help="(Windows) gera os pares de teste que faltam")
    g.add_argument("--lado", choices=list(LADOS), required=True)
    g.add_argument("--nome", help=f"(só conferência) o nome esperado no Ollama, ex. {LADOS}; "
                                  f"o modelo é escolhido pelo sha256 do GGUF do log do kernel")
    g.add_argument("--log-kernel", type=Path, required=True,
                   help="log.json do kernel que exportou o GGUF deste lado")
    g.add_argument("--log-kernel-base", type=Path,
                   help="(treinado) log.json do kernel da base, para conferir o llama.cpp")
    g.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    g.add_argument("--ram-partida-min-gb", type=float, default=6.0)
    g.add_argument("--espera-ram-s", type=float, default=90.0)
    a = ap.parse_args()
    {"plano": cmd_plano, "gerar": cmd_gerar}[a.cmd](a)


if __name__ == "__main__":
    main()
