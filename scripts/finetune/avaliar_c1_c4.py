"""Critérios C1–C4 da avaliação (Fases 2 e 4), pelo `finetune/PREREGISTRO_AVALIACAO.md`.

Implementa a seção 3 (C1–C4) e a 5 (ordem e integridade) sem mudar nada:

- **C1 / C2:** juiz v2.2 CONGELADO (`config_sha256` 44606cf1…), as mesmas 5
  reviews por bullet da limpeza (recuperação e5 centrada,
  `checagem_bullets.recuperar`, referência = bullets publicados do catálogo
  fora do C22 e do próprio filme), **parada no 2º "sim"**: os pares de cada
  bullet são julgados em ordem de posto até o 2º par com apoio. Par que não cabe
  na janela do juiz é pulado (`julgavel_estimado`, a regra da limpeza).
  - sem apoio = bullet julgado com 0 "sim"; apoio ≥ 2 = com ≥ 2 "sim";
  - indeterminado = bullet SEM par julgável: fora do denominador, contado à parte;
  - o bullet julgado é o que seria publicado (`_construir_temas`).
- **Reaproveitamento do publicado dos 5 filmes de referência:** só se o sha256
  das 450 linhas do lado publicado da entrada montada agora, no formato e na
  ordem da `checagem-bullets/juiz_entrada.jsonl` (commit 91397da), for
  `a68a6c9b…`. Bate → os registros v2.2 desses pares
  (`checagem-bullets/juiz_v2/saida_v2.2.jsonl`, commit 3d2174a) são copiados
  para a saída e não são refeitos; não bate → mede-se de novo.
- **C3 (M1):** `metricas.py` com a lista congelada (a7fcd5a5…), um evento por
  `exemplo_parafraseado`.
- **C4:** por bucket, o JSON parseou (depois da retentativa de produção) E
  `reconstruir_sintese.validar_publicado` → `passa_publicado`. A 1ª tentativa
  entra só como descrição.
- **IC:** bootstrap POR FILME, 10.000 reamostras, semente 20261101; as MESMAS
  reamostras de filmes para todas as métricas e comparações (pareado); taxa =
  razão das somas nos filmes sorteados; diferença em pontos percentuais.
- **Regra do outlier / de memória:** bucket `fora_por_memoria` em QUALQUER lado
  gerado sai de TODOS os lados antes de qualquer conta; o bucket do Gemini
  (`buckets_excluidos`) nunca entra.
- **δ₂:** recalculado pela taxa de apoio ≥ 2 do publicado (`fixar-delta2`),
  gravado UMA vez, antes de gerar o treinado.

Subcomandos:
    preparar        (Mac) recuperação e5 → `fase2/juiz/<lado>/entrada.jsonl`
                    (no publicado: a conferência do reaproveitamento)
    medir-contexto  (Windows) os 10 maiores prompts julgáveis no servidor
    julgar          (Windows) parada no 2º "sim", retomável, guarda de latência
    calcular        C1–C4 dos lados disponíveis (na Fase 2, descritivo)
    fixar-delta2    δ₂ pela taxa medida do publicado → `fase2/delta2.json`
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from statistics import NormalDist

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  (localhost passa; nenhuma API paga)
import comum as K  # noqa: E402
import fase4_especificidade as F  # noqa: E402
import limpar_treino as L  # noqa: E402  (exigir_juiz, _apoio, _CacheQueries)

C, J = L.C, L.J

DIR = K.FINETUNE_DIR / "fase2"
DIR_JUIZ = DIR / "juiz"
ARQ_DELTA2 = DIR / "delta2.json"
LADOS = ("publicado", "base", "treinado")
GERADOS = ("base", "treinado")
REFERENCIA_5 = tuple(sorted(K.REFERENCIA_5))
REUSO_SHA = "a68a6c9b16d08d90482566a71cb26afc3e9af5416813cdf394dc85b3cad1e10a"
REUSO_ENTRADA = ("91397da", "checagem-bullets/juiz_entrada.jsonl")
REUSO_SAIDA = ("3d2174a", "checagem-bullets/juiz_v2/saida_v2.2.jsonl")
CAMPOS_ENTRADA_ANTIGA = ("id_par", "id_bullet", "lado", "slug", "bucket", "i", "tema", "exemplo",
                         "review_id", "nivel", "texto", "rank", "sim", "score", "review_tem_eixo")
PARADA = 2                                  # parada no 2º "sim"
N_BOOT = 10_000
SEMENTE_BOOT = 20261101
N_FILMES, M_BULLETS, ICC = 30, 18, 0.023    # o poder do C1 e a fórmula do δ₂
ALFA, PODER = 0.05, 0.80
DELTA2_PADRAO_PP = 8.0
C1_MARGEM_PP, C1_PONTUAL_PP = 4.0, 2.0
C3_MARGEM_PP = 10.0
C4_PISO, C4_TOTAL = 87, 89
FALHA_JSON = "Falha ao obter JSON válido do LLM."


def dir_lado(lado: str) -> Path:
    return DIR_JUIZ / lado


# ---------------------------------------------------------------------------
# conjunto: pares de teste, regra de memória
# ---------------------------------------------------------------------------

def registros_gerados(pares: list[tuple[str, str]]) -> dict[str, dict]:
    """Os lados gerados que existem (base na Fase 2; base e treinado na 4)."""
    return {lado: F.registros(lado, pares) for lado in GERADOS
            if (F.pasta_sintese(lado) / "manifesto.json").exists()}


def buckets_mantidos(pares: list[tuple[str, str]], regs: dict[str, dict]) -> tuple[list, list]:
    fora = F.fora_por_memoria(*regs.values())
    return [k for k in pares if k not in fora], sorted(fora)


# ---------------------------------------------------------------------------
# bullets e buckets de cada lado
# ---------------------------------------------------------------------------

def bucket_do_lado(lado: str, slug: str, bucket: str, regs: dict, docs: dict) -> dict:
    """Forma de `validar_publicado` (+ `json_parseia`)."""
    if lado == "publicado":
        doc = docs.setdefault(slug, K.ler_json(K.RESULTADO_DIR / f"{slug}.json"))
        b = next(b for b in doc["buckets"] if b["bucket"] == bucket)
        return {**b, "json_parseia": True}
    r = regs[lado][(slug, bucket)]
    return {**(r.get("bucket_final") or {}), "json_parseia": bool(r.get("json_parseia"))}


def bullets_do_bucket(lado: str, slug: str, bucket: str, bp: dict) -> list[dict]:
    return [{"id_bullet": f"{lado}|{slug}|{bucket}|{i}", "lado": lado, "slug": slug,
             "bucket": bucket, "i": i, "tema": t["tema"],
             "exemplo": t.get("exemplo_parafraseado") or ""}
            for i, t in enumerate(bp.get("temas") or [])]


# ---------------------------------------------------------------------------
# juiz: estado do bullet com parada no 2º "sim"
# ---------------------------------------------------------------------------

def estado_do_bullet(ps: list[dict], regs: dict, apoio=L._apoio) -> dict:
    """'apoio_2' | 'apoio_1' | 'sem_apoio' | 'indeterminado' | 'pendente'."""
    ps = sorted(ps, key=lambda p: p["rank"])
    sims = julgados = pulados = 0
    prox = None
    for p in ps:
        if not p["julgavel_estimado"]:
            pulados += 1
            continue
        ap = apoio(regs.get(p["id_par"]), p)
        if ap is None:
            prox = p
            break
        julgados += 1
        sims += bool(ap)
        if sims >= PARADA:
            break
    if prox is not None:
        estado = "pendente"
    elif julgados == 0:
        estado = "indeterminado"
    else:
        estado = "apoio_2" if sims >= 2 else "apoio_1" if sims == 1 else "sem_apoio"
    return {"estado": estado, "sims": sims, "julgados": julgados, "pulados": pulados,
            "proximo": prox, "slug": ps[0]["slug"], "bucket": ps[0]["bucket"]}


def estados(pares: list[dict], regs: dict, apoio=L._apoio) -> dict[str, dict]:
    por = collections.defaultdict(list)
    for p in pares:
        por[p["id_bullet"]].append(p)
    return {b: estado_do_bullet(ps, regs, apoio) for b, ps in por.items()}


def registros_do_juiz(lado: str) -> dict[str, dict]:
    return {r["id_par"]: r for r in C._ler_jsonl(dir_lado(lado) / "saida.jsonl")
            if r.get("ok") and r.get("config_sha256") == L.HASH_CONGELADO}


# ---------------------------------------------------------------------------
# reaproveitamento do publicado dos 5
# ---------------------------------------------------------------------------

def linhas_formato_antigo(pares: list[dict], com_eixo: dict[str, set[str]]) -> list[str]:
    """As linhas do lado publicado dos 5, no formato e na ordem da entrada antiga
    (`checagem_bullets.montar_entrada`: filme, grupo, review, bullet)."""
    ps = [p for p in pares if p["slug"] in REFERENCIA_5]
    ps.sort(key=lambda p: (p["slug"], C.BUCKETS.index(p["bucket"]), p["review_id"], p["i"]))
    out = []
    for p in ps:
        d = {k: p[k] for k in CAMPOS_ENTRADA_ANTIGA[:-1]}
        d["review_tem_eixo"] = p["review_id"] in com_eixo.get(p["id_bullet"], set())
        out.append(json.dumps(d, ensure_ascii=False))
    return out


def sha_das_linhas(linhas: list[str]) -> str:
    return K.sha256_texto("".join(l + "\n" for l in linhas))


def ids_com_eixo_publicado(slug: str, doc: dict, reviews: dict, catalogo) -> dict[str, set[str]]:
    """O `ids_com_eixo` da Parte 1a (`checagem_bullets.medida_eixo`), só do lado publicado."""
    analisadas = {b: {r.id for r in rs} for b, rs in reviews.items()}
    cls = C.classificacao_analisada(slug, analisadas, catalogo)
    mapa = C.eixo_por_tema(doc)
    fora = {}
    for bl in C.bullets_do_doc(doc, "publicado"):
        fora[bl["id_bullet"]] = set(C.com_eixo(cls.get(bl["bucket"]) or {},
                                               mapa.get((bl["bucket"], bl["tema"]))))
    return fora


def _git_show(commit: str, caminho: str) -> str:
    r = K.rodar_texto(["git", "-C", str(K.RAIZ), "show", f"{commit}:{caminho}"])
    if r.returncode != 0:
        raise SystemExit(f"git show {commit}:{caminho} falhou: {r.stderr.strip()}")
    return r.stdout


def registros_reaproveitados(pares_5: set[str]) -> list[dict]:
    regs = [json.loads(l) for l in _git_show(*REUSO_SAIDA).split("\n") if l.strip()]
    regs = [r for r in regs if r.get("ok") and r.get("config_sha256") == L.HASH_CONGELADO
            and r["id_par"] in pares_5]
    if {r["id_par"] for r in regs} != pares_5:
        raise SystemExit(f"a saída antiga cobre {len({r['id_par'] for r in regs})} dos "
                         f"{len(pares_5)} pares do publicado dos 5")
    return regs


# ---------------------------------------------------------------------------
# preparar (Mac)
# ---------------------------------------------------------------------------

def cmd_preparar(a) -> None:
    import encoder_e5 as E5
    from espectro24 import eixos as EX
    from espectro24.pipeline import amostra_do_bruto

    L.exigir_juiz()
    split = K.ler_json(a.split)
    pares_teste = F.pares_de_teste(split)
    if len(pares_teste) != C4_TOTAL:
        raise SystemExit(f"{len(pares_teste)} pares de teste (esperados {C4_TOTAL})")
    regs = registros_gerados(pares_teste)
    if a.lado != "publicado" and a.lado not in regs:
        raise SystemExit(f"sem a síntese do lado {a.lado} (`gerar_sintese_teste.py gerar`)")
    destino = dir_lado(a.lado)
    if (destino / "entrada.jsonl").exists():
        raise SystemExit(f"{destino / 'entrada.jsonl'} já existe: a entrada é montada UMA vez")
    enc = L._CacheQueries(E5.Encoder.do_disco())
    catalogo = EX.carregar_classificacao(K.RAIZ / EX.CONSENSO_VERIFICADO) \
        if a.lado == "publicado" else None
    pares, docs, com_eixo, t0 = [], {}, {}, time.time()
    filmes = sorted({s for s, _ in pares_teste})
    for n, slug in enumerate(filmes, 1):
        doc = docs.setdefault(slug, K.ler_json(K.RESULTADO_DIR / f"{slug}.json"))
        reviews = amostra_do_bruto(slug, coleta=doc["coleta"], raiz=K.BRUTO_DIR)
        for b in doc["buckets"]:
            if len(reviews.get(b["bucket"], [])) != b["n_validas"]:
                raise SystemExit(f"{slug}/{b['bucket']}: amostra refeita difere do publicado")
        bl = []
        for slug_, bucket in pares_teste:
            if slug_ == slug:
                bl += bullets_do_bucket(a.lado, slug, bucket,
                                        bucket_do_lado(a.lado, slug, bucket, regs, docs))
        grupos = {(slug, bk): rs for bk, rs in reviews.items() if (slug, bk) in set(pares_teste)}
        ref = C.textos_de_referencia(excluir={slug})
        rec = C.recuperar(bl, grupos, enc, ref)
        por_id = {b["id_bullet"]: b for b in bl}
        rev = {(bk, r.id): r for (s, bk), rs in grupos.items() for r in rs}
        for r in rec:
            b = por_id[r["id_bullet"]]
            for t in r["top"]:
                rv = rev[(b["bucket"], t["id"])]
                p = {"id_par": f"{b['id_bullet']}|{t['id']}", "id_bullet": b["id_bullet"],
                     "lado": a.lado, "slug": slug, "bucket": b["bucket"], "i": b["i"],
                     "tema": b["tema"], "exemplo": b["exemplo"], "review_id": t["id"],
                     "nivel": rv.nivel, "texto": rv.texto, "rank": t["rank"], "sim": t["sim"],
                     "score": t["score"]}
                ch = J.chars_do_prompt(p, J.CONGELADA)
                p["chars_prompt"] = ch
                p["cota_tokens"] = math.ceil(J.RAZAO_TOKENS_POR_CHAR * ch)
                p["julgavel_estimado"] = p["cota_tokens"] + J.NUM_PREDICT <= J.num_ctx(J.CONGELADA)
                pares.append(p)
        if a.lado == "publicado" and slug in REFERENCIA_5:
            com_eixo.update(ids_com_eixo_publicado(slug, doc, reviews, catalogo))
        print(f"  {n}/{len(filmes)} {slug}: {len(bl)} bullets · {time.time() - t0:.0f}s", flush=True)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "entrada.jsonl").write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pares), encoding="utf-8")
    meta = {"gerado_por": "scripts/finetune/avaliar_c1_c4.py preparar", "lado": a.lado,
            "juiz_config_sha256": L.HASH_CONGELADO, "modelo_e5": E5.MODELO_ID,
            "e5_snapshot": enc.enc._dir.name, "k": C.K_RECUPERADAS, "pares": len(pares),
            "bullets": len({p["id_bullet"] for p in pares}),
            "pares_nao_julgaveis_estimados": sum(not p["julgavel_estimado"] for p in pares),
            "split_sha256": K.sha256_arquivo(a.split),
            "entrada_sha256": K.sha256_arquivo(destino / "entrada.jsonl"),
            "script_sha256": K.sha256_arquivo(Path(__file__)), "tempo_s": round(time.time() - t0, 1)}
    if a.lado == "publicado":
        linhas = linhas_formato_antigo(pares, com_eixo)
        sha = sha_das_linhas(linhas)
        meta["reaproveitamento"] = {"linhas": len(linhas), "sha256": sha, "esperado": REUSO_SHA,
                                    "bate": sha == REUSO_SHA}
        if sha == REUSO_SHA:
            ids5 = {json.loads(l)["id_par"] for l in linhas}
            regs5 = registros_reaproveitados(ids5)
            (destino / "saida.jsonl").write_text(
                "".join(json.dumps({**r, "reaproveitado_de": f"{REUSO_SAIDA[0]}:{REUSO_SAIDA[1]}"},
                                   ensure_ascii=False) + "\n" for r in regs5), encoding="utf-8")
            meta["reaproveitamento"]["registros_copiados"] = len(regs5)
    (destino / "entrada_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------------------
# Windows: medir-contexto e julgar
# ---------------------------------------------------------------------------

def _entrada(lado: str, split: dict) -> list[dict]:
    pares = C._ler_jsonl(dir_lado(lado) / "entrada.jsonl")
    if not pares:
        raise SystemExit(f"sem a entrada do lado {lado} — rode `preparar` no Mac")
    meta = K.ler_json(dir_lado(lado) / "entrada_meta.json")
    if meta["entrada_sha256"] != K.sha256_arquivo(dir_lado(lado) / "entrada.jsonl"):
        raise SystemExit("entrada.jsonl mudou desde o `preparar`")
    if any(p["slug"] not in set(split["teste"]) for p in pares):
        raise SystemExit("par fora dos filmes de teste: recusado")
    return pares


def cmd_medir_contexto(a) -> None:
    L._fora_do_claude()
    L.exigir_juiz()
    J._exigir_ambiente()
    split = K.ler_json(a.split)
    julgaveis = [p for p in _entrada(a.lado, split) if p["julgavel_estimado"]]
    J._exigir_modelo()
    chamar = J._chamador(num_ctx=J.MEDICAO_NUM_CTX, num_predict=1, schema=J.schema(J.CONGELADA))
    medidos = []
    for p in J.maiores_pares(julgaveis, versao=J.CONGELADA):
        r = chamar(J.system(J.CONGELADA), J.user(p, J.CONGELADA))
        medidos.append({"id_par": p["id_par"], "chars_prompt": p["chars_prompt"],
                        "prompt_eval_count": r["prompt_eval_count"]})
    jul = J.julgar_medicao(medidos, J.CONGELADA)
    (dir_lado(a.lado) / "contexto_medido.json").write_text(json.dumps(
        {"config_sha256": L.HASH_CONGELADO, "medidos": medidos, **jul}, ensure_ascii=False,
        indent=1), encoding="utf-8")
    print(("CABE" if jul["cabe"] else "NÃO CABE") + f": {jul}")
    if not jul["cabe"]:
        raise SystemExit(1)


def cmd_julgar(a) -> None:
    import viabilidade_ollama as V
    from _latencia import GuardaDeLatencia, LatenciaAnomala

    L._fora_do_claude()
    sha = L.exigir_juiz()
    J._exigir_ambiente()
    split = K.ler_json(a.split)
    pares = _entrada(a.lado, split)
    m = dir_lado(a.lado) / "contexto_medido.json"
    m = K.ler_json(m) if m.exists() else {}
    if m.get("config_sha256") != L.HASH_CONGELADO or not m.get("cabe"):
        raise SystemExit("sem contexto_medido.json válido — rode `medir-contexto` antes")
    J._exigir_modelo()
    guarda = GuardaDeLatencia(janela=a.latencia_janela, fator=a.latencia_fator)
    guarda.ignorar_proxima()
    chamar = guarda.envolver(J._chamador(num_ctx=J.num_ctx(J.CONGELADA), num_predict=J.NUM_PREDICT,
                                         schema=J.schema(J.CONGELADA)))
    saida = dir_lado(a.lado) / "saida.jsonl"
    filmes = sorted({p["slug"] for p in pares})
    print(f"juiz {J.MODELO} · {sha[:8]}… · lado {a.lado} · {len(filmes)} filmes · parada no "
          f"{PARADA}º sim", flush=True)
    base_ws, t0 = None, time.time()
    for n, slug in enumerate(filmes, 1):
        ps = [p for p in pares if p["slug"] == slug]
        for _ in range(2 * C.K_RECUPERADAS):        # até 5 postos; 2× para refazer falha de rede
            est = estados(ps, registros_do_juiz(a.lado))
            lote = sorted((e["proximo"] for e in est.values() if e["estado"] == "pendente"),
                          key=lambda p: (p["bucket"], p["review_id"], p["i"]))
            if not lote:
                break
            try:
                J.rodar(lote, saida, chamar, versao=J.CONGELADA, progresso_a_cada=50)
            except LatenciaAnomala as e:
                print(f"\nPAUSADO em {slug}: {e}. A chamada lenta foi gravada; rode `julgar` "
                      f"de novo para retomar.", flush=True)
                raise SystemExit(3)
        c = collections.Counter(e["estado"] for e in estados(ps, registros_do_juiz(a.lado)).values())
        print(f"[{n}/{len(filmes)}] {slug}: {dict(c)} · {(time.time() - t0) / 60:.0f} min", flush=True)
        ws = V.ws_ollama_gb()
        if n == 1:
            base_ws = ws
        elif n % L.N_FILMES_REINICIO == 0 and ws and base_ws and ws > base_ws * (1 + L.CRESCIMENTO_MAX):
            V.matar_ollama()
            V.subir_ollama()
            guarda.ignorar_proxima()
    print("fim — rode `calcular`")


# ---------------------------------------------------------------------------
# contas (funções puras)
# ---------------------------------------------------------------------------

def c4_do_bucket(bp: dict) -> bool:
    import reconstruir_sintese as R
    return bool(bp.get("json_parseia")) and R.validar_publicado(bp)["passa_publicado"]


def bucket_da_1a_tentativa(reg: dict) -> dict:
    """O bucket que a produção teria SEM retentativa (descrição do C4)."""
    from espectro24 import synthesize as S
    from dataclasses import asdict
    bf = reg.get("bucket_final") or {}
    tent = reg.get("tentativas") or []
    try:
        data = S._parse_llm_json(tent[0]["texto"])
    except (ValueError, IndexError, KeyError):
        return {**bf, "temas": [], "json_parseia": False}
    temas = S._construir_temas(data, bf.get("n_analisadas", 0))
    obs = str(data.get("observacao_geral", ""))
    return {"temas": [asdict(t) for t in temas], "observacao_geral": obs,
            "n_validas": bf.get("n_validas"), "json_parseia": True,
            "idioma_invalido": not S._idioma_e_pt_br(S._texto_para_checagem_idioma(temas, obs)),
            "escopo_suspeito": S._tem_marcador_de_escopo(obs)}


def por_filme(estados_lado: dict[str, dict], buckets: dict[tuple[str, str], dict],
              padrao) -> dict[str, dict]:
    """Contagens por filme de um lado: juiz (C1/C2), M1 (C3), C4."""
    import metricas as M
    f = collections.defaultdict(lambda: collections.Counter())
    for e in estados_lado.values():
        c = f[e["slug"]]
        if e["estado"] == "indeterminado":
            c["indeterminado"] += 1
            continue
        if e["estado"] == "pendente":
            raise SystemExit(f"{e['slug']}/{e['bucket']}: bullet pendente no juiz — termine `julgar`")
        c["julgados"] += 1
        c["sem_apoio"] += e["estado"] == "sem_apoio"
        c["apoio_2"] += e["estado"] == "apoio_2"
    for (slug, _), bp in buckets.items():
        c = f[slug]
        for t in bp.get("temas") or []:
            c["m1_n"] += 1
            c["m1_k"] += M.tem_palavra_de_quantidade(t.get("exemplo_parafraseado") or "", padrao)
        c["buckets"] += 1
        c["c4_ok"] += c4_do_bucket(bp)
    return {s: dict(c) for s, c in f.items()}


METRICAS = {"sem_apoio": ("sem_apoio", "julgados"), "apoio_2": ("apoio_2", "julgados"),
            "m1": ("m1_k", "m1_n")}


def taxa(pf: dict[str, dict], filmes: list[str], metrica: str) -> float | None:
    num, den = METRICAS[metrica]
    d = sum(pf.get(s, {}).get(den, 0) for s in filmes)
    return sum(pf.get(s, {}).get(num, 0) for s in filmes) / d if d else None


def reamostras(filmes: list[str], n: int = N_BOOT, semente: int = SEMENTE_BOOT) -> list[list[str]]:
    rng = random.Random(semente)
    return [rng.choices(filmes, k=len(filmes)) for _ in range(n)]


def diferenca(pf_a: dict, pf_b: dict, filmes: list[str], metrica: str, boot: list[list[str]]) -> dict:
    """(a − b) em pontos percentuais, IC 95% percentil do bootstrap por filme."""
    ponto = 100 * (taxa(pf_a, filmes, metrica) - taxa(pf_b, filmes, metrica))
    ds = []
    for amostra in boot:
        ta, tb = taxa(pf_a, amostra, metrica), taxa(pf_b, amostra, metrica)
        if ta is not None and tb is not None:
            ds.append(100 * (ta - tb))
    ds.sort()
    q = lambda p: ds[min(len(ds) - 1, int(p * len(ds)))]
    return {"ponto_pp": ponto, "ic95_pp": [q(0.025), q(0.975)], "reamostras_validas": len(ds)}


def delta2_pp(p0: float, n_filmes: int = N_FILMES, m: int = M_BULLETS, icc: float = ICC) -> float:
    """A fórmula do pré-registro (C2): a menor queda detectável a partir de p₀."""
    z_a, z_b = NormalDist().inv_cdf(1 - ALFA / 2), NormalDist().inv_cdf(PODER)
    n = n_filmes * m / (1 + (m - 1) * icc)
    lo, hi = 0.0, p0
    for _ in range(60):
        p1 = (lo + hi) / 2
        pb = (p0 + p1) / 2
        lhs = (z_a * math.sqrt(2 * pb * (1 - pb) / n)
               + z_b * math.sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n))
        if p0 - p1 >= lhs:
            lo = p1
        else:
            hi = p1
    return round(100 * (p0 - lo), 1)


def criterios(pf_t: dict, pf_p: dict, filmes: list[str], boot: list, delta2: float,
              n_buckets: int) -> dict:
    """C1–C4 de um lado contra o publicado (o lado julgado é o treinado na Fase 4)."""
    c1 = diferenca(pf_t, pf_p, filmes, "sem_apoio", boot)
    c2 = diferenca(pf_t, pf_p, filmes, "apoio_2", boot)
    c3 = diferenca(pf_t, pf_p, filmes, "m1", boot)
    c4 = sum(pf_t.get(s, {}).get("c4_ok", 0) for s in filmes)
    piso = C4_PISO - (C4_TOTAL - n_buckets)
    out = {"C1": {**c1, "passa": c1["ic95_pp"][1] < C1_MARGEM_PP and c1["ponto_pp"] <= C1_PONTUAL_PP},
           "C2": {**c2, "delta2_pp": delta2, "passa": c2["ic95_pp"][0] > -delta2},
           "C3": {**c3, "passa": c3["ic95_pp"][1] < C3_MARGEM_PP},
           "C4": {"ok": c4, "buckets": n_buckets, "piso": piso, "passa": c4 >= piso}}
    out["C1_a_C4_passam"] = all(v["passa"] for v in out.values())
    return out


# ---------------------------------------------------------------------------
# calcular, fixar-delta2
# ---------------------------------------------------------------------------

def _lado_completo(lado: str, split: dict, mantidos: list, regs: dict) -> tuple[dict, dict, dict]:
    import metricas as M
    docs: dict = {}
    buckets = {k: bucket_do_lado(lado, k[0], k[1], regs, docs) for k in mantidos}
    pares = [p for p in _entrada(lado, split) if (p["slug"], p["bucket"]) in set(mantidos)]
    est = estados(pares, registros_do_juiz(lado))
    pf = por_filme(est, buckets, M.compilar(M.carregar_lista()))
    return pf, est, buckets


def cmd_calcular(a) -> None:
    import metricas as M
    split = K.ler_json(a.split)
    if K.sha256_arquivo(M.LISTA) != "a7fcd5a5663c3ebdc0112b27bd8821c839d47de86673ef4ebdea83c0524c14af":
        raise SystemExit("a lista de palavras de quantidade não é a congelada")
    L.exigir_juiz()
    pares_teste = F.pares_de_teste(split)
    regs = registros_gerados(pares_teste)
    mantidos, fora = buckets_mantidos(pares_teste, regs)
    filmes = sorted({s for s, _ in mantidos})
    boot = reamostras(filmes)
    lados = ["publicado"] + [l for l in GERADOS if l in regs and (dir_lado(l) / "entrada.jsonl").exists()]
    pf, resumo = {}, {}
    for lado in lados:
        pf[lado], est, buckets = _lado_completo(lado, split, mantidos, regs)
        cont = collections.Counter(e["estado"] for e in est.values())
        resumo[lado] = {"estados": dict(cont),
                        **{m: taxa(pf[lado], filmes, m) for m in METRICAS},
                        "c4_ok": sum(c.get("c4_ok", 0) for c in pf[lado].values()),
                        "buckets": len(mantidos)}
        if lado in regs:
            primeira = [bucket_da_1a_tentativa(regs[lado][k]) for k in mantidos]
            resumo[lado]["c4_ok_1a_tentativa"] = sum(c4_do_bucket(b) for b in primeira)
            resumo[lado]["chamadas"] = dict(collections.Counter(
                regs[lado][k].get("n_chamadas") for k in mantidos))
            resumo[lado]["parede_s"] = [regs[lado][k].get("parede_s") for k in mantidos]
    delta2 = K.ler_json(ARQ_DELTA2)["delta2_pp"] if ARQ_DELTA2.exists() else DELTA2_PADRAO_PP
    out = {"gerado_por": "scripts/finetune/avaliar_c1_c4.py calcular",
           "script_sha256": K.sha256_arquivo(Path(__file__)), "juiz": L.HASH_CONGELADO,
           "semente_bootstrap": SEMENTE_BOOT, "reamostras": N_BOOT, "filmes": len(filmes),
           "buckets_mantidos": len(mantidos), "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
           "delta2_pp": delta2, "delta2_fixado": ARQ_DELTA2.exists(), "lados": resumo,
           "descritivo": {}, "decisao": None}
    for lado in lados[1:]:
        out["descritivo"][f"{lado}_contra_publicado"] = criterios(pf[lado], pf["publicado"], filmes,
                                                                  boot, delta2, len(mantidos))
    if "base" in pf and "treinado" in pf:
        out["descritivo"]["treinado_contra_base"] = {
            m: diferenca(pf["treinado"], pf["base"], filmes, m, boot) for m in METRICAS}
    if "treinado" in pf:
        if not ARQ_DELTA2.exists():
            raise SystemExit("o treinado só é avaliado com o δ₂ fixado (`fixar-delta2`)")
        out["decisao"] = out["descritivo"].pop("treinado_contra_publicado")
    if "base" in pf:
        out["achado_base_satisfaz_c1_c4"] = out["descritivo"]["base_contra_publicado"]["C1_a_C4_passam"]
    nome = "c1_c4_fase4.json" if "treinado" in pf else "c1_c4_fase2.json"
    (DIR / nome).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_fixar_delta2(a) -> None:
    if ARQ_DELTA2.exists():
        raise SystemExit(f"{ARQ_DELTA2} já existe: δ₂ é fixado UMA vez")
    if (F.pasta_sintese("treinado") / "manifesto.json").exists():
        raise SystemExit("o treinado já foi gerado: δ₂ tinha de ser fixado ANTES")
    split = K.ler_json(a.split)
    L.exigir_juiz()
    pares_teste = F.pares_de_teste(split)
    mantidos, fora = buckets_mantidos(pares_teste, registros_gerados(pares_teste))
    pf, _, _ = _lado_completo("publicado", split, mantidos, {})
    filmes = sorted({s for s, _ in mantidos})
    p0 = taxa(pf, filmes, "apoio_2")
    out = {"gerado_por": "scripts/finetune/avaliar_c1_c4.py fixar-delta2", "p0_apoio_2": p0,
           "bullets_julgados": sum(c.get("julgados", 0) for c in pf.values()),
           "formula": "poder.mde_analitico no sentido da queda; n = 30·18/(1 + 17·0,023)",
           "delta2_pp": delta2_pp(p0), "fora_por_memoria": [f"{s}/{b}" for s, b in fora],
           "script_sha256": K.sha256_arquivo(Path(__file__))}
    ARQ_DELTA2.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("preparar", "medir-contexto", "julgar"):
        s = sub.add_parser(nome)
        s.add_argument("--lado", choices=LADOS, required=True)
        if nome == "julgar":
            s.add_argument("--latencia-janela", type=int, default=20)
            s.add_argument("--latencia-fator", type=float, default=4.0)
    sub.add_parser("calcular")
    sub.add_parser("fixar-delta2")
    a = ap.parse_args()
    {"preparar": cmd_preparar, "medir-contexto": cmd_medir_contexto, "julgar": cmd_julgar,
     "calcular": cmd_calcular, "fixar-delta2": cmd_fixar_delta2}[a.cmd](a)


if __name__ == "__main__":
    main()
