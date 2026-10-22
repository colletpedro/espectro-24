"""Limpeza do TREINO e da VALIDAÇÃO com o juiz v2.2 CONGELADO (gate 0, decisão 8).

Regra (do dono): julgar os bullets PUBLICADOS dos filmes de treino e de
validação, nas 5 reviews mais parecidas, em ordem de similaridade, parando no
1º par com apoio; um bucket com QUALQUER bullet sem apoio sai inteiro do
treino/validação. O TESTE nunca é filtrado nem lido aqui.

O juiz é importado sem alteração (`scripts/juiz_bullets_v2.py`): este script
confere, ao iniciar, que a versão congelada é a v2.2 e que o `config_sha256`
dela é `HASH_CONGELADO`; chama `J.rodar` (uma chamada por par, seed fixa,
retomável: par já feito com esta configuração não é refeito) e decide o apoio
de cada par com `J.motivo_da_versao` — a mesma leitura de `J.vereditos`.
A decisão "sem apoio" é a do juiz completo: um bullet sem apoio é julgado nos
5 pares; um com apoio para no 1º "sim" e continua "com apoio".

Subcomandos:
    preparar        (Mac) recuperação e5 das 5 reviews por bullet → entrada.jsonl
    medir-contexto  (Windows) conta no servidor os 10 maiores prompts julgáveis
    julgar          (Windows, de madrugada) rodadas por posto, filme a filme
    resumir         buckets removidos por filme e por época do professor

**Par que não cabe na janela do juiz.** A janela é parte da configuração
congelada (`num_ctx` 4.096, `num_predict` 1.024). Par cuja cota conservadora
(0,35 token/caractere, a do juiz) não cabe é marcado `nao_julgavel` e pulado:
o bullet segue para o próximo posto. Bullet sem nenhum "sim" e com algum par
não julgável fica `indeterminado` e, por PROPOSTA conservadora, o bucket dele
também sai (`resumir --indeterminado-fica` muda isso). O número sai no resumo.

**Reinício do Ollama.** A cada `N_FILMES_REINICIO` = 10 filmes (~10 × 18 ×
1,46 ≈ 260 pares ≈ 70 min a 16 s/par), se o working set do Ollama cresceu
mais de 25% sobre o medido depois do 1º filme, o servidor é reiniciado. Dez
filmes limitam a ~1 h o que um vazamento acumula; reiniciar custa a recarga
do gpt-oss:20b (~1 min, < 2% do bloco) e o prefixo de KV, que é refeito no 1º
par. Guarda: LATÊNCIA (`_latencia.py`) — uma chamada acima de 4× a mediana das
últimas 20 pausa o processo e avisa (código 3); a retomada continua de onde
parou. A guarda de RAM livre saiu: com o gpt-oss:20b carregado a RAM livre fica
em ~0,3 GB por construção (a rodada de 20–21/10 correu com `--ram-livre-min-gb
0`, 1.863 chamadas a 14,7 s de mediana, sem paginação).
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  (localhost passa; nenhuma API paga)
import comum as K  # noqa: E402
from _latencia import GuardaDeLatencia, LatenciaAnomala  # noqa: E402

import checagem_bullets as C  # noqa: E402
import juiz_bullets_v2 as J  # noqa: E402

HASH_CONGELADO = "44606cf17c88338692139cf3dc9c6d46fbbbb90e07da80f26350b68c40ce6669"
DIR = K.FINETUNE_DIR / "limpeza"
ARQ_ENTRADA = DIR / "entrada.jsonl"
ARQ_META = DIR / "entrada_meta.json"
ARQ_CONTEXTO = DIR / "contexto_medido.json"
ARQ_SAIDA = DIR / "saida_v2.2.jsonl"
N_FILMES_REINICIO = 10
CRESCIMENTO_MAX = 0.25


def exigir_juiz() -> str:
    if J.CONGELADA != "v2.2":
        raise SystemExit(f"juiz congelado é {J.CONGELADA!r}, esperado 'v2.2'")
    sha = J.config_sha256(J.CONGELADA)
    if sha != HASH_CONGELADO:
        raise SystemExit(f"config_sha256 do juiz {sha} ≠ congelado {HASH_CONGELADO}: "
                         f"juiz_bullets_v2.py mudou — a limpeza não roda")
    return sha


def conjuntos(split_path: Path) -> tuple[dict, list[str]]:
    sp = K.ler_json(split_path)
    alvo = sorted(sp["treino"]) + sorted(sp["validacao"])
    assert not set(alvo) & set(sp["teste"])
    return sp, alvo


def recusar_teste(slugs, sp: dict) -> None:
    ruins = sorted(set(slugs) & (set(sp["teste"]) | set(K.EXCLUIR_FILMES)))
    if ruins:
        raise SystemExit(f"filme(s) de TESTE/excluído(s) na limpeza: {ruins}")


# ---------------------------------------------------------------------------
# preparar (Mac): recuperação
# ---------------------------------------------------------------------------

class _CacheQueries:
    """Encoder com cache de `queries` (a referência é a mesma para todos os
    filmes, menos os bullets do próprio filme)."""

    def __init__(self, enc):
        self.enc, self.cache = enc, {}

    def queries(self, textos):
        import numpy as np
        falta = [t for t in dict.fromkeys(textos) if t not in self.cache]
        if falta:
            for t, v in zip(falta, self.enc.queries(falta)):
                self.cache[t] = v
        return np.stack([self.cache[t] for t in textos])

    def passagens(self, textos):
        return self.enc.passagens(textos)


def cmd_preparar(a) -> None:
    import encoder_e5 as E5
    from espectro24.pipeline import amostra_do_bruto

    exigir_juiz()
    sp, alvo = conjuntos(a.split)
    recusar_teste(alvo, sp)
    excl = {(x["slug"], x["bucket"]) for x in sp.get("buckets_excluidos", [])}
    enc = _CacheQueries(E5.Encoder.do_disco())
    t0 = time.time()
    pares, por_filme = [], {}
    ref_total = C.textos_de_referencia()
    for n, slug in enumerate(alvo, 1):
        doc = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        bl = [b for b in C.bullets_do_doc(doc, "publicado") if (slug, b["bucket"]) not in excl]
        reviews = amostra_do_bruto(slug, coleta=doc["coleta"], raiz=K.BRUTO_DIR)
        for b in doc["buckets"]:
            if len(reviews.get(b["bucket"], [])) != b["n_validas"]:
                raise SystemExit(f"{slug}/{b['bucket']}: amostra refeita difere do publicado")
        grupos = {(slug, bk): rs for bk, rs in reviews.items() if (slug, bk) not in excl}
        ref = C.textos_de_referencia(excluir={slug})      # a regra da referência: sem o próprio filme
        rec = C.recuperar(bl, grupos, enc, ref)
        por_id = {b["id_bullet"]: b for b in bl}
        rev = {(bk, r.id): r for (s, bk), rs in grupos.items() for r in rs}
        for r in rec:
            b = por_id[r["id_bullet"]]
            for t in r["top"]:
                rv = rev[(b["bucket"], t["id"])]
                p = {"id_par": f"{b['id_bullet']}|{t['id']}", "id_bullet": b["id_bullet"],
                     "lado": "publicado", "slug": slug, "conjunto": "treino" if slug in sp["treino"]
                     else "validacao", "bucket": b["bucket"], "i": b["i"], "tema": b["tema"],
                     "exemplo": b["exemplo"], "review_id": t["id"], "nivel": rv.nivel,
                     "texto": rv.texto, "rank": t["rank"], "sim": t["sim"], "score": t["score"]}
                ch = J.chars_do_prompt(p, J.CONGELADA)
                p["chars_prompt"] = ch
                p["cota_tokens"] = math.ceil(J.RAZAO_TOKENS_POR_CHAR * ch)
                p["julgavel_estimado"] = p["cota_tokens"] + J.NUM_PREDICT <= J.num_ctx(J.CONGELADA)
                pares.append(p)
        por_filme[slug] = {"bullets": len(bl), "referencia": len(ref),
                           "referencia_sha256": K.sha256_texto("\n".join(ref))}
        print(f"  {n}/{len(alvo)} {slug}: {len(bl)} bullets · {time.time() - t0:.0f}s", flush=True)
    DIR.mkdir(parents=True, exist_ok=True)
    ARQ_ENTRADA.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pares),
                           encoding="utf-8")
    nj = [p for p in pares if not p["julgavel_estimado"]]
    meta = {"gerado_por": "scripts/finetune/limpar_treino.py preparar",
            "juiz_config_sha256": HASH_CONGELADO, "modelo_e5": E5.MODELO_ID,
            "e5_snapshot": enc.enc._dir.name,
            "e5_pesos_sha256": C._sha256_arquivo(enc.enc._dir / "model.safetensors"),
            "k": C.K_RECUPERADAS, "referencia_catalogo": len(ref_total),
            "regra_referencia": "bullets publicados do catálogo fora do C22 e do PRÓPRIO filme",
            "filmes": len(alvo), "bullets": sum(f["bullets"] for f in por_filme.values()),
            "pares": len(pares), "pares_nao_julgaveis_estimados": len(nj),
            "bullets_com_par_nao_julgavel": len({p["id_bullet"] for p in nj}),
            "split_sha256": K.sha256_arquivo(a.split),
            "entrada_sha256": K.sha256_arquivo(ARQ_ENTRADA),
            "tempo_s": round(time.time() - t0, 1), "por_filme": por_filme}
    ARQ_META.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "por_filme"}, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Windows: medir-contexto, julgar
# ---------------------------------------------------------------------------

def _entrada(sp: dict) -> list[dict]:
    pares = C._ler_jsonl(ARQ_ENTRADA)
    if not pares:
        raise SystemExit(f"sem {ARQ_ENTRADA} — rode `preparar` no Mac")
    recusar_teste({p["slug"] for p in pares}, sp)
    return pares


def _fora_do_claude() -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")


def cmd_medir_contexto(a) -> None:
    _fora_do_claude()
    exigir_juiz()
    J._exigir_ambiente()
    sp, _ = conjuntos(a.split)
    julgaveis = [p for p in _entrada(sp) if p["julgavel_estimado"]]
    J._exigir_modelo()
    chamar = J._chamador(num_ctx=J.MEDICAO_NUM_CTX, num_predict=1, schema=J.schema(J.CONGELADA))
    medidos = []
    for p in J.maiores_pares(julgaveis, versao=J.CONGELADA):
        r = chamar(J.system(J.CONGELADA), J.user(p, J.CONGELADA))
        medidos.append({"id_par": p["id_par"], "chars_prompt": p["chars_prompt"],
                        "prompt_eval_count": r["prompt_eval_count"]})
        print(f"  {p['id_par']}: {p['chars_prompt']} chars → {r['prompt_eval_count']} tokens",
              flush=True)
    jul = J.julgar_medicao(medidos, J.CONGELADA)
    ARQ_CONTEXTO.write_text(json.dumps({"config_sha256": HASH_CONGELADO, "medidos": medidos,
                                        **jul}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(("CABE" if jul["cabe"] else "NÃO CABE") + f": {jul}")
    if not jul["cabe"]:
        raise SystemExit(1)


def _apoio(reg: dict, par: dict) -> bool | None:
    """O apoio do par pela regra da versão (None = sem veredito válido)."""
    if not reg or not reg.get("ok") or reg.get("config_sha256") != HASH_CONGELADO:
        return None
    v = J._versao(J.CONGELADA)
    lida = {k: reg[k] for k in v["schema"]["required"]}
    return J.motivo_da_versao(lida, par["texto"], J.CONGELADA) is None


def _registros() -> dict[str, dict]:
    fora = {}
    for r in C._ler_jsonl(ARQ_SAIDA):
        if r.get("ok") and r.get("config_sha256") == HASH_CONGELADO:
            fora[r["id_par"]] = r
    return fora


def estado_dos_bullets(pares: list[dict], regs: dict) -> dict[str, dict]:
    """Para cada bullet: 'com_apoio' | 'sem_apoio' | 'indeterminado' |
    'pendente', e o próximo par a julgar (o de menor posto ainda sem veredito)."""
    por = collections.defaultdict(list)
    for p in pares:
        por[p["id_bullet"]].append(p)
    fora = {}
    for b, ps in por.items():
        ps.sort(key=lambda p: p["rank"])
        estado, prox, pulados = None, None, 0
        for p in ps:
            if not p["julgavel_estimado"]:
                pulados += 1
                continue
            ap = _apoio(regs.get(p["id_par"]), p)
            if ap is True:
                estado = "com_apoio"
                break
            if ap is None:
                prox = p
                break
        if estado is None:
            estado = "pendente" if prox else ("indeterminado" if pulados else "sem_apoio")
        fora[b] = {"estado": estado, "proximo": prox, "pulados": pulados,
                   "slug": ps[0]["slug"], "bucket": ps[0]["bucket"]}
    return fora


def cmd_julgar(a) -> None:
    import viabilidade_ollama as V

    _fora_do_claude()
    sha = exigir_juiz()
    J._exigir_ambiente()
    sp, alvo = conjuntos(a.split)
    pares = _entrada(sp)
    m = K.ler_json(ARQ_CONTEXTO) if ARQ_CONTEXTO.exists() else {}
    if m.get("config_sha256") != HASH_CONGELADO or not m.get("cabe"):
        raise SystemExit(f"sem {ARQ_CONTEXTO} válido — rode `medir-contexto` antes")
    J._exigir_modelo()
    guarda = GuardaDeLatencia(janela=a.latencia_janela, fator=a.latencia_fator)
    guarda.ignorar_proxima()                    # a 1ª chamada paga a carga do modelo
    chamar = guarda.envolver(J._chamador(num_ctx=J.num_ctx(J.CONGELADA),
                                         num_predict=J.NUM_PREDICT,
                                         schema=J.schema(J.CONGELADA)))
    filmes = [s for s in alvo if any(p["slug"] == s for p in pares)]
    print(f"juiz {J.MODELO} think={J.THINK} · {sha[:8]}… · {len(filmes)} filmes · "
          f"guarda de latência {a.latencia_fator:g}× a mediana das últimas "
          f"{a.latencia_janela}", flush=True)
    base_ws, t0 = None, time.time()
    for n, slug in enumerate(filmes, 1):
        ps = [p for p in pares if p["slug"] == slug]
        for tentativa in range(2 * 5):          # até 5 postos; 2× para refazer falha de rede
            est = estado_dos_bullets(ps, _registros())
            lote = sorted((e["proximo"] for e in est.values() if e["estado"] == "pendente"),
                          key=lambda p: (p["bucket"], p["review_id"], p["i"]))
            if not lote:
                break
            try:
                J.rodar(lote, ARQ_SAIDA, chamar, versao=J.CONGELADA, progresso_a_cada=50)
            except LatenciaAnomala as e:
                print(f"\nPAUSADO em {slug}: {e}. A chamada lenta foi gravada. Veja a RAM, o "
                      f"swap e o `ollama ps`; rode `julgar` de novo para retomar.", flush=True)
                raise SystemExit(3)
        est = estado_dos_bullets(ps, _registros())
        c = collections.Counter(e["estado"] for e in est.values())
        print(f"[{n}/{len(filmes)}] {slug}: {dict(c)} · {(time.time() - t0) / 60:.0f} min",
              flush=True)
        ws = V.ws_ollama_gb()
        if n == 1:
            base_ws = ws
        elif n % N_FILMES_REINICIO == 0 and ws and base_ws and ws > base_ws * (1 + CRESCIMENTO_MAX):
            print(f"  working set do Ollama {ws:.1f} GB > {base_ws:.1f} × {1 + CRESCIMENTO_MAX}: "
                  f"reiniciando", flush=True)
            V.matar_ollama()
            V.subir_ollama()
            guarda.ignorar_proxima()            # recarga do modelo
    print("fim — rode `resumir`")


# ---------------------------------------------------------------------------
# resumir
# ---------------------------------------------------------------------------

def cmd_resumir(a) -> None:
    sp, _ = conjuntos(a.split)
    pares = _entrada(sp)
    est = estado_dos_bullets(pares, _registros())
    sai = {"sem_apoio"} | (set() if a.indeterminado_fica else {"indeterminado"})
    buckets = collections.defaultdict(lambda: collections.Counter())
    for b, e in est.items():
        buckets[(e["slug"], e["bucket"])][e["estado"]] += 1
    linhas, por_epoca = [], collections.defaultdict(collections.Counter)
    for (slug, bucket), c in sorted(buckets.items()):
        removido = any(c[s] for s in sai)
        pendente = c["pendente"] > 0
        epoca = sp["filmes"][slug]["epoca_professor"]
        conj = sp["filmes"][slug]["conjunto"]
        linhas.append({"slug": slug, "bucket": bucket, "conjunto": conj, "epoca": epoca,
                       "estados": dict(c), "removido": removido, "pendente": pendente})
        por_epoca[(conj, epoca)]["buckets"] += 1
        por_epoca[(conj, epoca)]["removidos"] += removido
        por_epoca[(conj, epoca)]["pendentes"] += pendente
    n_pares_feitos = sum(1 for p in pares if p["id_par"] in _registros())
    out = {"juiz_config_sha256": HASH_CONGELADO, "regra_remocao": sorted(sai),
           "pares_julgados": n_pares_feitos, "pares_na_entrada": len(pares),
           "estados_bullets": dict(collections.Counter(e["estado"] for e in est.values())),
           "buckets": linhas,
           "por_conjunto_e_epoca": {f"{k[0]}|{k[1]}": dict(v) for k, v in sorted(por_epoca.items())},
           "buckets_removidos": [f"{x['slug']}/{x['bucket']}" for x in linhas if x["removido"]]}
    (DIR / "resumo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# Limpeza com o juiz v2.2 — resumo", "",
         f"Juiz `{HASH_CONGELADO[:8]}…`. Pares julgados {n_pares_feitos} de {len(pares)} "
         f"na entrada (parada no 1º sim). Estados dos bullets: {out['estados_bullets']}. "
         f"Um bucket sai se tiver bullet em {sorted(sai)}.", "",
         "| conjunto | época | buckets | removidos | pendentes |", "|---|---|---|---|---|"]
    for k, v in out["por_conjunto_e_epoca"].items():
        c, e = k.split("|")
        L.append(f"| {c} | {e} | {v.get('buckets', 0)} | {v.get('removidos', 0)} | {v.get('pendentes', 0)} |")
    L += ["", "## Por filme", "", "| filme | conjunto | época | bucket | estados | sai? |",
          "|---|---|---|---|---|---|"]
    for x in linhas:
        L.append(f"| {x['slug']} | {x['conjunto']} | {x['epoca']} | {x['bucket']} | "
                 f"{x['estados']} | {'SAI' if x['removido'] else ('pendente' if x['pendente'] else 'fica')} |")
    (DIR / "resumo.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:12]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preparar")
    sub.add_parser("medir-contexto")
    j = sub.add_parser("julgar")
    j.add_argument("--latencia-fator", type=float, default=4.0,
                   help="pausa se uma chamada passar de FATOR × a mediana das últimas JANELA")
    j.add_argument("--latencia-janela", type=int, default=20)
    r = sub.add_parser("resumir")
    r.add_argument("--indeterminado-fica", action="store_true")
    a = ap.parse_args()
    {"preparar": cmd_preparar, "medir-contexto": cmd_medir_contexto, "julgar": cmd_julgar,
     "resumir": cmd_resumir}[a.cmd](a)


if __name__ == "__main__":
    main()
