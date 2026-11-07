"""Avaliação de PRODUÇÃO do treinado nos filmes do C22 (2026-11-05), pelo
`finetune/PREREGISTRO_C22.md`. Filmes nunca vistos, sem publicado para comparar:
os critérios são ABSOLUTOS, ancorados no publicado da Fase 2.

Subcomandos (onde roda):
    escopo          (Mac)     quais filmes do C22 entram, e por que os outros não → `c22/escopo.json`
    plano           (Mac)     entradas congeladas dos buckets + tokens e `num_ctx` → `c22/entrada/`, `c22/plano.json`
    gerar           (Windows) síntese do treinado + a guarda de quantidade → `c22/sintese_treinado/`
    preparar        (Mac)     recuperação e5 dos bullets → `c22/juiz/entrada.jsonl`
    medir-contexto  (Windows) os 10 maiores prompts do juiz no servidor
    julgar          (Windows) juiz v2.2 congelado, parada no 2º "sim", retomável
    calcular        (Mac)     C1–C4 (IC por bootstrap por filme) → `c22/cego/c1_c4_c22.json`
    leitura montar  (Mac)     documento do C6 (5 filmes sorteados, só os bullets)
    leitura avaliar (Mac)     C6 (≥ 4 de 5 "S")

Cegueira do dono até o C6: `gerar`, `preparar`, `julgar` e `calcular` mandam
o que imprimiriam para `finetune/c22/cego/*.log`; a tela mostra progresso e sha256.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import _cego  # noqa: E402
import avaliar_c1_c4 as A  # noqa: E402
import gerar_sintese_teste as G  # noqa: E402
import limpar_treino as L  # noqa: E402

C, J = L.C, L.J

PASTA = K.FINETUNE_DIR / "c22"
ARQ_ESCOPO = PASTA / "escopo.json"
ARQ_PLANO = PASTA / "plano.json"
DIR_ENTRADA = PASTA / "entrada"
DIR_SINTESE = PASTA / "sintese_treinado"
DIR_JUIZ = PASTA / "juiz"
DIR_CEGO = PASTA / "cego"
ARQ_RESULTADO = DIR_CEGO / "c1_c4_c22.json"
ARQ_C6_MAPA = PASTA / "c6_mapa.json"
ARQ_C6_RESULTADO = PASTA / "c6_resultado.json"
ARQ_PREREGISTRO = K.FINETUNE_DIR / "PREREGISTRO_C22.md"
ARQ_FLUENCIA = K.FINETUNE_DIR / "guarda" / "fluencia_resultado.json"
DOC_DIR = K.RAIZ / "docs" / "arquivo-de-estudos" / "finetune-c22"
DOC_C6, CSV_C6 = "leitura_c6.md", "leitura_c6_respostas.csv"
MARCA_PREREGISTRO = "<!-- preregistro_c22 "

_cego.PASTA = DIR_CEGO          # o `Saida` do modo cego passa a escrever em c22/cego/

# --- critérios (PREREGISTRO_C22.md) ------------------------------------------
SEMENTE_BOOT = 20261108
N_BOOT = 10_000
SEMENTE_C6 = 20261109
N_C6, MIN_C6 = 5, 4
C1_PONTUAL_PP, C1_SUPERIOR_PP = 5.6, 7.6        # publicado 3,6% + 2,0 / + 4,0 (Fase 2)
C2_INFERIOR_PP = 77.8                           # publicado 85,6% − δ₂ 7,8 (Fase 2)
C3_PONTUAL_PP, C3_SUPERIOR_PP = 10.0, 15.0
C4_FRACAO = 0.97
GGUF_TREINADO_SHA = "e488697e7215f12c35c7fdfe9206a5af4438bfe47512a91a8698ad98cdcd6eac"
MODELO_TREINADO = "espectro-qwen3-8b-treinado"
LISTA_QUANTIDADE_SHA = "a7fcd5a5663c3ebdc0112b27bd8821c839d47de86673ef4ebdea83c0524c14af"


# ===========================================================================
# 1. escopo
# ===========================================================================

def decidir_filme(slug: str, tem_resultado: bool, publicado: bool, catalogo: dict | None,
                  analisadas: dict | None, meta: dict | None, checar) -> tuple[str, str]:
    """('incluido' | 'excluido' | 'ja_publicado', motivo). `checar` é a guarda C14.8
    (`eixos.checar_amostra_classificada`): levanta se a amostra analisada tem review
    que a classificação nunca viu."""
    if tem_resultado or publicado:
        return "ja_publicado", "já tem resultado/<slug>.json ou está em dados/publicados.json"
    if not catalogo:
        return "excluido", "sem classificação no consenso verificado (ainda não classificado)"
    ident = (meta or {}).get("identidade_letterboxd") or {}
    if not ident.get("titulo") or not ident.get("tmdb_id_letterboxd"):
        return "excluido", "pendência de identidade: bloco identidade_letterboxd incompleto no bruto"
    ano = (meta or {}).get("ano_lancamento")
    m = re.search(r"-(\d{4})$", slug)
    if ident.get("ano") != ano or (m and int(m.group(1)) != ano):
        return "excluido", (f"pendência de identidade: ano da identidade ({ident.get('ano')}), do "
                            f"coletor ({ano}) e do slug não concordam")
    try:
        checar(catalogo, analisadas or {})
    except ValueError as e:                              # AmostraNaoClassificada
        return "excluido", ("pendência de corpus (C14.8): " + str(e).split(". ")[1][:140]
                            if ". " in str(e) else "pendência de corpus (C14.8)")
    return "incluido", ""


def _sha_bruto(slug: str) -> str:
    base = K.BRUTO_DIR / slug
    return K.sha256_texto("".join(f"{n} {K.sha256_arquivo(base / n)}\n"
                                  for n in ("meta.json", "reviews.jsonl")))


def cmd_escopo(a) -> None:
    from espectro24 import eixos as E
    from espectro24.excecao_c22 import SLUGS
    from espectro24.pipeline import amostra_do_bruto

    if ARQ_ESCOPO.exists():
        raise SystemExit(f"{ARQ_ESCOPO} já existe: o escopo é congelado UMA vez")
    catalogo = E.carregar_classificacao(K.RAIZ / E.CONSENSO_VERIFICADO)
    pub = set(K.ler_json(K.RAIZ / "dados" / "publicados.json")["slugs"])
    com_resultado = {p.stem for p in K.RESULTADO_DIR.glob("*.json")}
    incluidos, excluidos, entradas = [], [], {}
    for slug in sorted(SLUGS):
        meta = K.ler_json(K.BRUTO_DIR / slug / "meta.json")
        analisadas = {b: {r.id for r in rs} for b, rs in amostra_do_bruto(slug).items()}
        estado, motivo = decidir_filme(slug, slug in com_resultado, slug in pub, catalogo.get(slug),
                                       analisadas, meta, E.checar_amostra_classificada)
        n_por_bucket = {b: len(v) for b, v in analisadas.items()}
        if estado == "incluido":
            incluidos.append({"slug": slug, "titulo": meta["identidade_letterboxd"]["titulo"],
                              "ano": meta["ano_lancamento"], "n_por_bucket": n_por_bucket,
                              "bucket_abaixo_de_40": sorted(b for b, n in n_por_bucket.items() if n < 40)})
            entradas[slug] = _sha_bruto(slug)
        else:
            excluidos.append({"slug": slug, "estado": estado, "motivo": motivo})
    arqs = {"resultado/votacao-3/consenso_verificado.jsonl": K.RAIZ / E.CONSENSO_VERIFICADO,
            "resultado/votacao-3/recusas_conteudo.json": K.RAIZ / "resultado/votacao-3/recusas_conteudo.json",
            "dados/publicados.json": K.RAIZ / "dados" / "publicados.json",
            "src/espectro24/excecao_c22.py": K.RAIZ / "src/espectro24/excecao_c22.py"}
    doc = {"gerado_por": "scripts/finetune/c22.py escopo", "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "regra": "C22 (55) − já publicados − sem classificação no consenso verificado − pendência de "
                    "identidade (bloco do bruto) − pendência de corpus (guarda C14.8)",
           "n_c22": len(SLUGS), "incluidos": incluidos, "excluidos": excluidos,
           "buckets": 3 * len(incluidos),
           "entradas_sha256": {k: K.sha256_arquivo(p) for k, p in arqs.items()},
           "bruto_sha256": entradas,
           "limite": "A identidade foi conferida só pelo que o bruto guarda (título, ano, id do "
                     "Letterboxd, ano do slug); a conferência contra o TMDB roda na publicação (ficha) "
                     "e não foi feita aqui."}
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_ESCOPO.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"escopo: {len(incluidos)} filmes ({doc['buckets']} buckets) incluídos, "
          f"{len(excluidos)} fora · sha256 {K.sha256_arquivo(ARQ_ESCOPO)}")
    for e in excluidos:
        print(f"  fora: {e['slug']}: {e['motivo']}")


def conferir_escopo(escopo: dict) -> None:
    """As entradas não mudaram desde o `escopo` (a árvore de trabalho do C22 continua a andar)."""
    for k, esperado in escopo["entradas_sha256"].items():
        if K.sha256_arquivo(K.RAIZ / k) != esperado:
            raise SystemExit(f"{k} mudou desde o `escopo`: o conjunto de filmes é o do escopo congelado, "
                             f"mas as entradas não são as mesmas — pare e avise o Claude")
    for slug, sha in escopo["bruto_sha256"].items():
        if _sha_bruto(slug) != sha:
            raise SystemExit(f"dados/bruto/{slug} mudou desde o `escopo`")


# ===========================================================================
# 2. plano e entradas congeladas
# ===========================================================================

def entrada_do_bucket(slug: str, b) -> dict:
    return {"slug": slug, "bucket": b.nome, "alvo": b.alvo, "modo": b.modo,
            "estado_piso": b.estado_piso,
            "reviews": [{"viewing_id": r.viewing_id, "rating": r.rating, "text": r.effective_text}
                        for r in b.reviews_analisadas]}


def bucket_da_entrada(d: dict):
    """O `BucketResult` mínimo que `build_user_message` / `synthesize_bucket` leem."""
    from espectro24.models import BucketResult, LevelResult, Review
    revs = [Review(viewing_id=r["viewing_id"], rating=r["rating"], text=r["text"], truncated=False,
                   full_text_url=None, spoiler=False) for r in d["reviews"]]
    nivel = LevelResult(nivel=0.0, filtro_aplicado=0, paginas_buscadas=0, n_brutas=len(revs),
                        n_sem_nota=0, n_descartadas_spoiler=0, n_descartadas_curtas=0,
                        n_descartadas_truncamento=0, validas=revs, n_alvo=len(revs))
    return BucketResult(nome=d["bucket"], alvo=d["alvo"], modo=d["modo"],
                        estado_piso=d["estado_piso"], niveis=[nivel])


def arq_entrada(slug: str, bucket: str) -> Path:
    return DIR_ENTRADA / f"{slug}__{bucket}.json"


def cmd_plano(a) -> None:
    from espectro24.prosa_local import _buckets_do_bruto

    if ARQ_PLANO.exists():
        raise SystemExit(f"{ARQ_PLANO} já existe: o plano é feito UMA vez")
    escopo = K.ler_json(ARQ_ESCOPO)
    conferir_escopo(escopo)
    tok = K.carregar_tokenizer(G.TOKENIZER, a.tokenizers)
    DIR_ENTRADA.mkdir(parents=True, exist_ok=True)
    linhas = []
    for f in escopo["incluidos"]:
        slug = f["slug"]
        meta = K.ler_json(K.BRUTO_DIR / slug / "meta.json")
        bs = _buckets_do_bruto(slug, meta, K.BRUTO_DIR)
        if sorted(b.nome for b in bs) != sorted(K.BUCKETS):
            raise SystemExit(f"{slug}: buckets {[b.nome for b in bs]}, esperados os 3")
        for b in bs:
            s, u = K.prompt_sintese(b)
            d = entrada_do_bucket(slug, b)
            d["system_sha256"], d["user_sha256"] = K.sha256_texto(s), K.sha256_texto(u)
            # a entrada congelada reproduz o prompt: é o que o Windows usa (sem bruto, sem consenso)
            if K.prompt_sintese(bucket_da_entrada(d)) != (s, u):
                raise SystemExit(f"{slug}/{b.nome}: a entrada congelada não reproduz o prompt")
            arq_entrada(slug, b.nome).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
            n = K.contar(tok, K.chat("qwen", s, u, None))
            linhas.append({"slug": slug, "bucket": b.nome, "tokens_prompt": n,
                           "num_ctx": G.num_ctx_da_chamada(n), "n_reviews": len(d["reviews"]),
                           "system_sha256": d["system_sha256"], "user_sha256": d["user_sha256"],
                           "entrada_sha256": K.sha256_arquivo(arq_entrada(slug, b.nome))})
    linhas.sort(key=lambda p: (p["num_ctx"], p["slug"], p["bucket"]))
    plano = {"gerado_por": "scripts/finetune/c22.py plano", "tokenizer": G.TOKENIZER,
             "escopo_sha256": K.sha256_arquivo(ARQ_ESCOPO),
             "regra_num_ctx": "(tokens do prompt + 3.000) × 1,10, arredondado para cima no múltiplo de 1.024",
             "num_predict": G.TETO_SAIDA, "pares": linhas}
    ARQ_PLANO.write_text(json.dumps(plano, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"plano: {len(linhas)} pares, {sum(p['tokens_prompt'] for p in linhas)} tokens de prompt, "
          f"num_ctx máx. {max(p['num_ctx'] for p in linhas)} · sha256 {K.sha256_arquivo(ARQ_PLANO)}")


# ===========================================================================
# 3. gerar (Windows)
# ===========================================================================

def ler_marca_preregistro(texto: str) -> dict:
    linha = next((l for l in texto.splitlines() if l.startswith(MARCA_PREREGISTRO)), None)
    if linha is None or not linha.endswith(" -->"):
        raise SystemExit(f"{ARQ_PREREGISTRO.name} sem a linha `{MARCA_PREREGISTRO.strip()} {{…}} -->`")
    return json.loads(linha[len(MARCA_PREREGISTRO):-len(" -->")])


def exigir_preregistro(arq: Path = ARQ_PREREGISTRO, escopo: Path = ARQ_ESCOPO,
                       plano: Path = ARQ_PLANO) -> dict:
    """O C22 só é gerado com o `PREREGISTRO_C22.md` COMMITADO (igual ao HEAD) e com o
    `escopo.json` e o `plano.json` de que ele dá o sha256."""
    if not arq.exists():
        raise SystemExit(f"sem {arq.name}: o C22 só é gerado depois do pré-registro, commitado")
    real = arq.resolve()
    repo, nome = real.parent, real.name
    if K.rodar_texto(["git", "-C", str(repo), "ls-files", "--error-unmatch", nome]).returncode:
        raise SystemExit(f"{nome} existe mas não está commitado: commite-o antes")
    if K.rodar_texto(["git", "-C", str(repo), "diff", "--quiet", "HEAD", "--", nome]).returncode:
        raise SystemExit(f"{nome} difere do commitado (HEAD): o pré-registro é o commitado")
    marca = ler_marca_preregistro(real.read_text(encoding="utf-8"))
    for chave, f in (("escopo_sha256", escopo), ("plano_sha256", plano)):
        if not f.exists() or K.sha256_arquivo(f) != marca.get(chave):
            raise SystemExit(f"{f.name} ausente ou diferente do que o {nome} registra")
    import espectro24.guarda_quantidade as GQ
    if K.sha256_arquivo(Path(GQ.__file__)) != marca.get("guarda_sha256"):
        raise SystemExit("guarda_quantidade.py não é a do pré-registro (rode o bloco 0: "
                         "`git checkout origin/main -- src/espectro24`)")
    if GQ.LISTA_SHA256 != LISTA_QUANTIDADE_SHA or K.sha256_arquivo(GQ.LISTA) != LISTA_QUANTIDADE_SHA:
        raise SystemExit("a lista de palavras de quantidade não é a congelada")
    return marca


def exigir_fluencia(arq: Path = ARQ_FLUENCIA) -> dict:
    """A checagem de fluência do dono (≥ 27 de 30) tem de ter PASSADO."""
    if not arq.exists():
        raise SystemExit("sem fluencia_resultado.json: a guarda só vale depois da checagem de fluência")
    r = K.ler_json(arq)
    if not r.get("passa"):
        raise SystemExit("a checagem de fluência da guarda REPROVOU: o C22 não é gerado")
    return r


def executar_par(b, nome: str, num_ctx: int, chamar) -> tuple[dict, list]:
    """Uma chamada da produção (`synthesize_bucket`, com a guarda dentro de
    `_construir_temas`) com o `chamar` injetado. Devolve (campos do registro, tentativas)."""
    import copy
    from espectro24.synthesize import synthesize_bucket
    s, _ = K.prompt_sintese(b)
    tentativas: list[dict] = []
    final = synthesize_bucket(copy.deepcopy(b), model=nome,
                              client_call=G.cliente_registrado(chamar, s, nome, num_ctx, tentativas))
    reg = {"ok": True, "bucket_final": G.bucket_final(final),
           "json_parseia": final.observacao_geral != "Falha ao obter JSON válido do LLM.",
           "json_parseia_1a_tentativa": None}
    if tentativas:
        try:
            G.parse_estrito(tentativas[0]["texto"])
            reg["json_parseia_1a_tentativa"] = True
        except ValueError:
            reg["json_parseia_1a_tentativa"] = False
    return reg, tentativas


def cmd_gerar(a) -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    G.recusar_temperatura_do_ambiente()
    marca = exigir_preregistro()
    exigir_fluencia()
    from espectro24 import synthesize as S
    from espectro24.local_ollama import LLMLocalFalhou, resposta_json_local
    from _latencia import GuardaDeLatencia, LatenciaAnomala
    import viabilidade_ollama as V
    import espectro24.guarda_quantidade as GQ

    S._parse_llm_json = G.parse_estrito            # DESVIO_P04: estrutura impossível = JSON inválido
    origem = G.conferir_modelo("treinado", None, a.log_kernel, a.log_kernel_base)
    if origem["gguf_sha256"] != GGUF_TREINADO_SHA or origem["nome_ollama"] != MODELO_TREINADO:
        raise SystemExit(f"o modelo não é o do pré-registro ({MODELO_TREINADO}, GGUF {GGUF_TREINADO_SHA[:8]}…)")
    nome = origem["nome_ollama"]
    plano = K.ler_json(ARQ_PLANO)
    DIR_SINTESE.mkdir(parents=True, exist_ok=True)
    ordem = [(p["slug"], p["bucket"]) for p in plano["pares"]]
    por = {(p["slug"], p["bucket"]): p for p in plano["pares"]}
    falta = [k for k in ordem if not G.ja_feito(DIR_SINTESE / f"{k[0]}__{k[1]}.json")]
    out = _cego.Saida("treinado", "gerar.log")
    print(f"treinado: {nome} · {origem['importacao']} · {len(ordem) - len(falta)} feitos, "
          f"{len(falta)} a fazer", flush=True)
    if not falta:
        G.gravar_manifesto(DIR_SINTESE)
        return
    partida = V.partida_limpa(a.ram_partida_min_gb, a.espera_ram_s)
    if not partida["limpa"]:
        raise SystemExit(f"partida contaminada, nada foi gerado: {partida}")
    guarda = GuardaDeLatencia()
    guarda.ignorar_proxima()
    chamar = guarda.envolver(resposta_json_local)
    srv = V.subir_ollama()
    try:
        for n_par, chave in enumerate(falta, 1):
            slug, bucket = chave
            p = por[chave]
            d = K.ler_json(arq_entrada(slug, bucket))
            if K.sha256_arquivo(arq_entrada(slug, bucket)) != p["entrada_sha256"]:
                raise SystemExit(f"{slug}/{bucket}: a entrada mudou desde o plano")
            b = bucket_da_entrada(d)
            s, u = K.prompt_sintese(b)
            if (K.sha256_texto(s), K.sha256_texto(u)) != (p["system_sha256"], p["user_sha256"]):
                raise SystemExit(f"{slug}/{bucket}: o prompt remontado não é o do plano")
            reg = {"lado": "treinado", "modelo": nome, "origem": origem, "slug": slug, "bucket": bucket,
                   "num_ctx": p["num_ctx"], "tokens_prompt_plano": p["tokens_prompt"],
                   "num_predict": G.TETO_SAIDA, "think": "false", "amostragem": G.AMOSTRAGEM,
                   "seed": G.SEED, "system_sha256": p["system_sha256"], "user_sha256": p["user_sha256"],
                   "preregistro": marca, "partida": partida,
                   "guarda_sha256": K.sha256_arquivo(Path(GQ.__file__)),
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            arq = DIR_SINTESE / f"{slug}__{bucket}.json"
            mon = V.Monitor(G.RAM_LIVRE_MIN_GB, ao_estourar=V.matar_ollama)
            mon.start()
            t0 = time.time()
            tentativas: list = []
            try:
                campos, tentativas = executar_par(b, nome, p["num_ctx"], chamar)
                reg.update(campos)
            except LLMLocalFalhou as e:
                reg.update({"ok": False, "erro": str(e)[:500]})
            except LatenciaAnomala as e:
                reg.update({"ok": False, "erro": f"retentativa barrada pela guarda de latência: {e}"})
            finally:
                mon.parar.set()
                mon.join(timeout=5)
            reg["parede_s"] = round(time.time() - t0, 1)
            reg["memoria"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in mon.pico.items()}
            reg["tentativas"] = tentativas
            reg["n_chamadas"] = len(tentativas)
            reg["abortado_por_memoria"] = mon.estourou
            reg["abortos_memoria"] = G.abortos_anteriores(arq) + (1 if mon.estourou else 0)
            reg["fora_por_memoria"] = reg["abortos_memoria"] >= G.MAX_ABORTOS_MEMORIA
            anomala = guarda.pendente
            if anomala is not None:
                reg["latencia_anomala"] = str(anomala)
            arq.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
            G.gravar_manifesto(DIR_SINTESE)
            refazer = not (reg.get("ok") or reg["fora_por_memoria"])
            out(f"{slug}/{bucket}: ok {reg.get('ok')} · json {reg.get('json_parseia')} · "
                f"{reg['n_chamadas']} chamada(s) · ctx {p['num_ctx']} · {reg['parede_s']} s",
                curto=f"[{n_par}/{len(falta)}] {slug}/{bucket}: gravado"
                      + (" (erro do servidor: refeito ao rodar de novo)" if refazer else ""))
            if mon.estourou:
                destino = ("fica FORA POR MEMÓRIA" if reg["fora_por_memoria"]
                           else "será tentado UMA vez mais na próxima execução (partida limpa)")
                raise SystemExit(f"{slug}/{bucket}: a guarda de RAM derrubou o servidor. Par gravado; "
                                 f"{destino}; a série parou. Rode de novo para seguir.")
            if anomala is not None:
                raise anomala
    except LatenciaAnomala as e:
        raise SystemExit(f"PAUSA pela guarda de latência ({e}); o par lento foi gravado. "
                         f"Confira o Ollama e rode de novo (retoma).")
    finally:
        srv.terminate()
        V.matar_ollama()


# ===========================================================================
# 4. conjunto, juiz
# ===========================================================================

def pares_do_plano() -> list[tuple[str, str]]:
    return sorted((p["slug"], p["bucket"]) for p in K.ler_json(ARQ_PLANO)["pares"])


def registros_sintese(pares: list[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    manifesto = K.ler_json(DIR_SINTESE / "manifesto.json")
    out = {}
    for slug, bucket in pares:
        arq = DIR_SINTESE / f"{slug}__{bucket}.json"
        if not arq.exists() or K.sha256_arquivo(arq) != manifesto.get(arq.name):
            raise SystemExit(f"{arq.name} ausente ou fora do manifesto")
        r = K.ler_json(arq)
        if not (r.get("ok") or r.get("fora_por_memoria")):
            raise SystemExit(f"{arq.name} não terminou (nem ok, nem fora por memória)")
        out[(slug, bucket)] = r
    return out


def mantidos_e_fora(pares, regs) -> tuple[list, list]:
    fora = {k for k, r in regs.items() if r.get("fora_por_memoria")}
    return [k for k in pares if k not in fora], sorted(fora)


def bucket_publicavel(reg: dict) -> dict:
    return {**(reg.get("bucket_final") or {}), "json_parseia": bool(reg.get("json_parseia"))}


def montar_pares(regs: dict, mantidos: list) -> list[dict]:
    """Recuperação e5 → pares (bullet, review), como a Fase 4, sobre os buckets mantidos."""
    import encoder_e5 as E5
    from espectro24.pipeline import amostra_do_bruto

    enc = L._CacheQueries(E5.Encoder.do_disco())
    montar_pares.e5_snapshot = enc.enc._dir.name
    ref = C.textos_de_referencia(K.RESULTADO_DIR)
    pares, t0 = [], time.time()
    filmes = sorted({s for s, _ in mantidos})
    for n, slug in enumerate(filmes, 1):
        meta = K.ler_json(K.BRUTO_DIR / slug / "meta.json")
        reviews = amostra_do_bruto(slug, coleta=meta, raiz=K.BRUTO_DIR)
        bl, grupos = [], {}
        for s, bucket in mantidos:
            if s != slug:
                continue
            d = K.ler_json(arq_entrada(slug, bucket))
            if [r.id for r in reviews[bucket]] != [r["viewing_id"] for r in d["reviews"]]:
                raise SystemExit(f"{slug}/{bucket}: a amostra do bruto difere da entrada congelada")
            grupos[(slug, bucket)] = reviews[bucket]
            bl += A.bullets_do_bucket("treinado", slug, bucket, bucket_publicavel(regs[(slug, bucket)]))
        rec = C.recuperar(bl, grupos, enc, ref)
        por_id = {b["id_bullet"]: b for b in bl}
        rev = {(bk, r.id): r for (s, bk), rs in grupos.items() for r in rs}
        for r in rec:
            b = por_id[r["id_bullet"]]
            for t in r["top"]:
                rv = rev[(b["bucket"], t["id"])]
                p = {"id_par": f"{b['id_bullet']}|{t['id']}", "id_bullet": b["id_bullet"],
                     "lado": "treinado", "slug": slug, "bucket": b["bucket"], "i": b["i"],
                     "tema": b["tema"], "exemplo": b["exemplo"], "review_id": t["id"],
                     "nivel": rv.nivel, "texto": rv.texto, "rank": t["rank"], "sim": t["sim"],
                     "score": t["score"]}
                ch = J.chars_do_prompt(p, J.CONGELADA)
                p["chars_prompt"] = ch
                p["cota_tokens"] = math.ceil(J.RAZAO_TOKENS_POR_CHAR * ch)
                p["julgavel_estimado"] = p["cota_tokens"] + J.NUM_PREDICT <= J.num_ctx(J.CONGELADA)
                pares.append(p)
        print(f"  {n}/{len(filmes)} {slug} · {time.time() - t0:.0f}s", flush=True)
    return pares


def cmd_preparar(a) -> None:
    import encoder_e5 as E5

    L.exigir_juiz()
    escopo = K.ler_json(ARQ_ESCOPO)
    conferir_escopo(escopo)
    exigir_preregistro()
    pares_plano = pares_do_plano()
    regs = registros_sintese(pares_plano)
    mantidos, fora = mantidos_e_fora(pares_plano, regs)
    if (DIR_JUIZ / "entrada.jsonl").exists():
        raise SystemExit("entrada.jsonl já existe: a entrada é montada UMA vez")
    out = _cego.Saida("treinado", "preparar.log")
    t0 = time.time()
    with out.silenciar():
        pares = montar_pares(regs, mantidos)
    DIR_JUIZ.mkdir(parents=True, exist_ok=True)
    (DIR_JUIZ / "entrada.jsonl").write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pares), encoding="utf-8")
    meta = {"gerado_por": "scripts/finetune/c22.py preparar", "juiz_config_sha256": L.HASH_CONGELADO,
            "modelo_e5": E5.MODELO_ID, "e5_snapshot": montar_pares.e5_snapshot, "k": C.K_RECUPERADAS,
            "pares": len(pares), "bullets": len({p["id_bullet"] for p in pares}),
            "buckets_mantidos": len(mantidos), "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
            "pares_nao_julgaveis_estimados": sum(not p["julgavel_estimado"] for p in pares),
            "escopo_sha256": K.sha256_arquivo(ARQ_ESCOPO), "plano_sha256": K.sha256_arquivo(ARQ_PLANO),
            "manifesto_sha256": K.sha256_arquivo(DIR_SINTESE / "manifesto.json"),
            "entrada_sha256": K.sha256_arquivo(DIR_JUIZ / "entrada.jsonl"),
            "script_sha256": K.sha256_arquivo(Path(__file__)), "tempo_s": round(time.time() - t0, 1)}
    (DIR_JUIZ / "entrada_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    out(json.dumps(meta, ensure_ascii=False, indent=1),
        curto=f"preparado, entrada_meta.json sha256 {K.sha256_arquivo(DIR_JUIZ / 'entrada_meta.json')}")


def entrada_juiz() -> list[dict]:
    pares = C._ler_jsonl(DIR_JUIZ / "entrada.jsonl")
    if not pares:
        raise SystemExit("sem a entrada do juiz — rode `preparar` no Mac")
    meta = K.ler_json(DIR_JUIZ / "entrada_meta.json")
    if meta["entrada_sha256"] != K.sha256_arquivo(DIR_JUIZ / "entrada.jsonl"):
        raise SystemExit("entrada.jsonl mudou desde o `preparar`")
    return pares


def registros_do_juiz() -> dict[str, dict]:
    return {r["id_par"]: r for r in C._ler_jsonl(DIR_JUIZ / "saida.jsonl")
            if r.get("ok") and r.get("config_sha256") == L.HASH_CONGELADO}


def cmd_medir_contexto(a) -> None:
    L._fora_do_claude()
    L.exigir_juiz()
    J._exigir_ambiente()
    julgaveis = [p for p in entrada_juiz() if p["julgavel_estimado"]]
    J._exigir_modelo()
    chamar = J._chamador(num_ctx=J.MEDICAO_NUM_CTX, num_predict=1, schema=J.schema(J.CONGELADA))
    medidos = []
    for p in J.maiores_pares(julgaveis, versao=J.CONGELADA):
        r = chamar(J.system(J.CONGELADA), J.user(p, J.CONGELADA))
        medidos.append({"id_par": p["id_par"], "chars_prompt": p["chars_prompt"],
                        "prompt_eval_count": r["prompt_eval_count"]})
    jul = J.julgar_medicao(medidos, J.CONGELADA)
    (DIR_JUIZ / "contexto_medido.json").write_text(json.dumps(
        {"config_sha256": L.HASH_CONGELADO, "medidos": medidos, **jul}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(("CABE" if jul["cabe"] else "NÃO CABE") + f": {jul}")
    if not jul["cabe"]:
        raise SystemExit(1)


def cmd_julgar(a) -> None:
    import viabilidade_ollama as V
    from _latencia import GuardaDeLatencia, LatenciaAnomala

    L._fora_do_claude()
    sha = L.exigir_juiz()
    J._exigir_ambiente()
    pares = entrada_juiz()
    m = DIR_JUIZ / "contexto_medido.json"
    m = K.ler_json(m) if m.exists() else {}
    if m.get("config_sha256") != L.HASH_CONGELADO or not m.get("cabe"):
        raise SystemExit("sem contexto_medido.json válido — rode `medir-contexto` antes")
    J._exigir_modelo()
    guarda = GuardaDeLatencia(janela=a.latencia_janela, fator=a.latencia_fator)
    guarda.ignorar_proxima()
    chamar = guarda.envolver(J._chamador(num_ctx=J.num_ctx(J.CONGELADA), num_predict=J.NUM_PREDICT,
                                         schema=J.schema(J.CONGELADA)))
    saida = DIR_JUIZ / "saida.jsonl"
    out = _cego.Saida("treinado", "julgar.log")
    filmes = sorted({p["slug"] for p in pares})
    print(f"juiz {J.MODELO} · {sha[:8]}… · {len(filmes)} filmes · parada no {A.PARADA}º sim", flush=True)
    base_ws, t0 = None, time.time()
    for n, slug in enumerate(filmes, 1):
        ps = [p for p in pares if p["slug"] == slug]
        for _ in range(2 * C.K_RECUPERADAS):
            est = A.estados(ps, registros_do_juiz())
            lote = sorted((e["proximo"] for e in est.values() if e["estado"] == "pendente"),
                          key=lambda p: (p["bucket"], p["review_id"], p["i"]))
            if not lote:
                break
            try:
                with out.silenciar():
                    J.rodar(lote, saida, chamar, versao=J.CONGELADA, progresso_a_cada=50)
            except LatenciaAnomala as e:
                print(f"\nPAUSADO em {slug}: {e}. A chamada lenta foi gravada; rode `julgar` "
                      f"de novo para retomar.", flush=True)
                raise SystemExit(3)
        c = collections.Counter(e["estado"] for e in A.estados(ps, registros_do_juiz()).values())
        out(f"[{n}/{len(filmes)}] {slug}: {dict(c)} · {(time.time() - t0) / 60:.0f} min",
            curto=f"[{n}/{len(filmes)}] {slug} · {(time.time() - t0) / 60:.0f} min")
        ws = V.ws_ollama_gb()
        if n == 1:
            base_ws = ws
        elif n % L.N_FILMES_REINICIO == 0 and ws and base_ws and ws > base_ws * (1 + L.CRESCIMENTO_MAX):
            V.matar_ollama()
            V.subir_ollama()
            guarda.ignorar_proxima()
    print("fim — rode `calcular`")


# ===========================================================================
# 5. calcular (funções puras + comando)
# ===========================================================================

def ic_absoluto(pf: dict, filmes: list[str], metrica: str, boot: list[list[str]]) -> dict:
    """Taxa (em %) e IC 95% percentil do bootstrap por filme (razão das somas)."""
    ponto = A.taxa(pf, filmes, metrica)
    xs = sorted(100 * t for amostra in boot if (t := A.taxa(pf, amostra, metrica)) is not None)
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {"ponto_pct": None if ponto is None else 100 * ponto,
            "ic95_pct": [q(0.025), q(0.975)], "reamostras_validas": len(xs)}


def criterios_absolutos(pf: dict, filmes: list[str], boot: list, n_buckets: int) -> dict:
    c1 = ic_absoluto(pf, filmes, "sem_apoio", boot)
    c2 = ic_absoluto(pf, filmes, "apoio_2", boot)
    c3 = ic_absoluto(pf, filmes, "m1", boot)
    ok = sum(pf.get(s, {}).get("c4_ok", 0) for s in filmes)
    piso = math.ceil(C4_FRACAO * n_buckets)
    out = {"C1": {**c1, "limites": f"ponto ≤ {C1_PONTUAL_PP}% e limite superior < {C1_SUPERIOR_PP}%",
                  "passa": c1["ponto_pct"] <= C1_PONTUAL_PP and c1["ic95_pct"][1] < C1_SUPERIOR_PP},
           "C2": {**c2, "limites": f"limite inferior > {C2_INFERIOR_PP}%",
                  "passa": c2["ic95_pct"][0] > C2_INFERIOR_PP},
           "C3": {**c3, "limites": f"ponto ≤ {C3_PONTUAL_PP}% e limite superior < {C3_SUPERIOR_PP}%",
                  "passa": c3["ponto_pct"] <= C3_PONTUAL_PP and c3["ic95_pct"][1] < C3_SUPERIOR_PP},
           "C4": {"ok": ok, "buckets": n_buckets, "piso": piso, "fracao": ok / n_buckets,
                  "limites": f"≥ {100 * C4_FRACAO:.0f}% dos buckets válidos", "passa": ok >= piso}}
    out["C1_a_C4_passam"] = all(v["passa"] for v in out.values())
    return out


def descritivo_da_guarda(buckets: dict) -> dict:
    """Quanto a guarda agiu nesta rodada (sobre os textos que o modelo escreveu)."""
    from espectro24 import guarda_quantidade as GQ
    n = antes = depois = alterados = pendentes = 0
    for bp in buckets.values():
        for t in bp.get("temas") or []:
            n += 1
            original = t.get("exemplo_antes_da_guarda") or t["exemplo_parafraseado"]
            antes += GQ.tem_quantidade(original)
            depois += GQ.tem_quantidade(t["exemplo_parafraseado"])
            alterados += bool(t.get("quantidade_reescrita"))
            pendentes += bool(t.get("quantidade_pendente"))
    return {"bullets": n, "m1_antes_da_guarda": antes, "m1_depois_da_guarda": depois,
            "textos_alterados": alterados, "textos_pendentes": pendentes}


def cmd_calcular(a) -> None:
    import metricas as M

    if K.sha256_arquivo(M.LISTA) != LISTA_QUANTIDADE_SHA:
        raise SystemExit("a lista de palavras de quantidade não é a congelada")
    L.exigir_juiz()
    if ARQ_RESULTADO.exists():
        raise SystemExit(f"{ARQ_RESULTADO} já existe: o C1–C4 do C22 é calculado UMA vez")
    pares_plano = pares_do_plano()
    regs = registros_sintese(pares_plano)
    mantidos, fora = mantidos_e_fora(pares_plano, regs)
    meta = K.ler_json(DIR_JUIZ / "entrada_meta.json")
    if meta["manifesto_sha256"] != K.sha256_arquivo(DIR_SINTESE / "manifesto.json"):
        raise SystemExit("a síntese mudou desde o `preparar`")
    filmes = sorted({s for s, _ in mantidos})
    boot = A.reamostras(filmes, N_BOOT, SEMENTE_BOOT)
    buckets = {k: bucket_publicavel(regs[k]) for k in mantidos}
    pares = [p for p in entrada_juiz() if (p["slug"], p["bucket"]) in set(mantidos)]
    est = A.estados(pares, registros_do_juiz())
    pf = A.por_filme(est, buckets, M.compilar(M.carregar_lista()))
    primeira = [A.bucket_da_1a_tentativa(regs[k]) for k in mantidos]
    out = {"gerado_por": "scripts/finetune/c22.py calcular",
           "script_sha256": K.sha256_arquivo(Path(__file__)), "juiz": L.HASH_CONGELADO,
           "semente_bootstrap": SEMENTE_BOOT, "reamostras": N_BOOT, "filmes": len(filmes),
           "buckets_mantidos": len(mantidos), "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
           "estados_do_juiz": dict(collections.Counter(e["estado"] for e in est.values())),
           "decisao": criterios_absolutos(pf, filmes, boot, len(mantidos)),
           "guarda": descritivo_da_guarda(buckets),
           "c4_ok_1a_tentativa": sum(A.c4_do_bucket(b) for b in primeira),
           "chamadas": dict(collections.Counter(regs[k].get("n_chamadas") for k in mantidos)),
           "parede_s": [regs[k].get("parede_s") for k in mantidos],
           "por_filme": pf, "escopo_sha256": K.sha256_arquivo(ARQ_ESCOPO),
           "manifesto_sha256": K.sha256_arquivo(DIR_SINTESE / "manifesto.json")}
    DIR_CEGO.mkdir(parents=True, exist_ok=True)
    ARQ_RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    _cego.Saida("treinado", "calcular.log")(
        json.dumps(out, ensure_ascii=False, indent=1),
        curto=f"calculado, {ARQ_RESULTADO.name} sha256 {K.sha256_arquivo(ARQ_RESULTADO)}")


# ===========================================================================
# 6. C6 — leitura cega (só os bullets)
# ===========================================================================

def sortear_c6(filmes_completos: list[str], semente: int = SEMENTE_C6, n: int = N_C6) -> list[str]:
    """`n` filmes entre os que têm os 3 buckets válidos, `random.Random(semente).sample` sobre a
    lista ordenada; a ordem do sorteio é a ordem do documento."""
    return random.Random(semente).sample(sorted(filmes_completos), n)


def bloco_c6(bucket: dict | None) -> list[str]:
    if bucket is None or not bucket.get("temas"):
        return ["_(sem síntese neste bucket)_", ""]
    return [f"- **{t['tema']}** — {t['exemplo_parafraseado']}" for t in bucket["temas"]] + [""]


def documento_c6(escopo: dict, filmes: list[str], buckets: dict, selo: str) -> str:
    titulos = {f["slug"]: f"{f['titulo']} ({f['ano']})" for f in escopo["incluidos"]}
    rot = {"negativas": "Negativas", "medianas": "Medianas", "positivas": "Positivas"}
    L_ = ["# Leitura cega — C22 (5 filmes)", "",
          f"Para cada filme, leia os bullets dos três grupos e responda na coluna `publicavel` de "
          f"`{CSV_C6}`:", "",
          "> **publicável? S ou N**", "",
          "`S` = você publicaria esta síntese como está. `N` = há algo que impediria a publicação. "
          "Se hesitar, é `N`.", "", f"Passa com {MIN_C6} ou mais `S` entre {len(filmes)}.", "", "---", ""]
    for i, slug in enumerate(filmes, 1):
        L_ += [f"## Filme {i} — {titulos[slug]}", ""]
        for b in K.BUCKETS:
            L_ += [f"**{rot[b]}**", ""] + bloco_c6(buckets.get((slug, b)))
        L_ += ["---", ""]
    L_ += [f"Selo: `{selo}`"]
    return "\n".join(L_) + "\n"


def avaliar_c6(filmes: list[str], respostas: list[dict]) -> dict:
    if [int(r["filme"]) for r in respostas] != list(range(1, len(filmes) + 1)):
        raise SystemExit("as respostas não têm uma linha por filme, na ordem")
    val = [r["publicavel"].strip().upper() for r in respostas]
    if any(v not in ("S", "N") for v in val):
        raise SystemExit("resposta inválida: só S ou N")
    n_s = sum(v == "S" for v in val)
    return {"por_filme": [{"slug": s, "publicavel": v == "S"} for s, v in zip(filmes, val)],
            "publicaveis": n_s, "criterio": f"≥ {MIN_C6} de {len(filmes)}", "C6_passa": n_s >= MIN_C6}


def cmd_leitura_montar(a) -> None:
    if ARQ_C6_MAPA.exists():
        raise SystemExit(f"{ARQ_C6_MAPA.name} já existe: o sorteio é feito UMA vez")
    if not ARQ_RESULTADO.exists():
        raise SystemExit("o C6 vem depois do `calcular`")
    escopo = K.ler_json(ARQ_ESCOPO)
    pares_plano = pares_do_plano()
    regs = registros_sintese(pares_plano)
    mantidos, fora = mantidos_e_fora(pares_plano, regs)
    buckets = {k: bucket_publicavel(regs[k]) for k in mantidos}
    completos = [s for s in sorted({s for s, _ in mantidos})
                 if all((s, b) in buckets and buckets[(s, b)].get("temas") for b in K.BUCKETS)]
    filmes = sortear_c6(completos)
    mapa = {"gerado_por": "scripts/finetune/c22.py leitura montar", "semente": SEMENTE_C6,
            "filmes": filmes, "elegiveis": len(completos),
            "manifesto_sha256": K.sha256_arquivo(DIR_SINTESE / "manifesto.json"),
            "script_sha256": K.sha256_arquivo(Path(__file__))}
    ARQ_C6_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_C6_MAPA)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    (DOC_DIR / DOC_C6).write_text(documento_c6(escopo, filmes, buckets, selo), encoding="utf-8")
    with open(DOC_DIR / CSV_C6, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["filme", "publicavel"])
        for n in range(1, len(filmes) + 1):
            w.writerow([n, ""])
    print(json.dumps({"documento": str(DOC_DIR / DOC_C6), "respostas": str(DOC_DIR / CSV_C6),
                      "selo": selo}, ensure_ascii=False, indent=1))


def cmd_leitura_avaliar(a) -> None:
    if ARQ_C6_RESULTADO.exists():
        raise SystemExit(f"{ARQ_C6_RESULTADO.name} já existe: o C6 é avaliado UMA vez")
    if a.selo and K.sha256_arquivo(ARQ_C6_MAPA) != a.selo:
        raise SystemExit("o mapa não tem o selo impresso no documento")
    mapa = K.ler_json(ARQ_C6_MAPA)
    resp = list(csv.DictReader(open(a.respostas, encoding="utf-8")))
    out = {"gerado_por": "scripts/finetune/c22.py leitura avaliar",
           "respostas_sha256": K.sha256_arquivo(Path(a.respostas)),
           "mapa_sha256": K.sha256_arquivo(ARQ_C6_MAPA), **avaliar_c6(mapa["filmes"], resp)}
    ARQ_C6_RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"avaliado, {ARQ_C6_RESULTADO.name} sha256 {K.sha256_arquivo(ARQ_C6_RESULTADO)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("escopo")
    p = sub.add_parser("plano")
    p.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    g = sub.add_parser("gerar")
    g.add_argument("--log-kernel", type=Path, required=True)
    g.add_argument("--log-kernel-base", type=Path, required=True)
    g.add_argument("--ram-partida-min-gb", type=float, default=6.0)
    g.add_argument("--espera-ram-s", type=float, default=90.0)
    sub.add_parser("preparar")
    sub.add_parser("medir-contexto")
    j = sub.add_parser("julgar")
    j.add_argument("--latencia-janela", type=int, default=20)
    j.add_argument("--latencia-fator", type=float, default=4.0)
    sub.add_parser("calcular")
    lt = sub.add_parser("leitura")
    lt.add_argument("acao", choices=["montar", "avaliar"])
    lt.add_argument("--respostas", default=str(DOC_DIR / CSV_C6))
    lt.add_argument("--selo", default="")
    a = ap.parse_args()
    if a.cmd == "leitura":
        {"montar": cmd_leitura_montar, "avaliar": cmd_leitura_avaliar}[a.acao](a)
        return
    {"escopo": cmd_escopo, "plano": cmd_plano, "gerar": cmd_gerar, "preparar": cmd_preparar,
     "medir-contexto": cmd_medir_contexto, "julgar": cmd_julgar, "calcular": cmd_calcular}[a.cmd](a)


if __name__ == "__main__":
    main()
