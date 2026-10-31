"""Fase 0 do fine-tuning — (a) inventário por estágio, com tokens por candidato.

Zero rede, zero LLM (`_guarda`). Lê `resultado/*.json` (só leitura), o bruto, o
consenso e o gabarito humano; remonta os prompts com o código de produção.

Saída: `finetune/inventario.json` e `finetune/inventario.md`.

Uso (sem as chaves no ambiente):
    PYTHONPATH=<pasta com o pacote tokenizers> venv/bin/python \\
        scripts/finetune/inventario.py --tokenizers <pasta dos tokenizers>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

CONSENSO = K.RESULTADO_DIR / "votacao-3" / "consenso_verificado.jsonl"
GABARITO = K.RESULTADO_DIR / "auditoria-acuracia" / "gabarito_modelo.json"
GABARITO_TEXTOS = K.RESULTADO_DIR / "auditoria-acuracia" / "textos_gabarito.json"
GABARITO_AMOSTRA = K.RESULTADO_DIR / "auditoria-acuracia" / "amostra.json"

# Teto de saída de PRODUÇÃO de cada estágio (o que o modelo local tem de poder
# escrever na inferência, não só o que o publicado escreveu).
TETO_SAIDA_PRODUCAO = {"sintese": ("LLM_MAX_TOKENS", 3000),
                       "classificacao": ("max_tokens da classificação", 300)}
MARGEM = 0.10  # PROPOSTO: 10% sobre o maior total observado


def _git(*a) -> str:
    return K.rodar_texto(["git", "-C", str(K.RAIZ), *a]).stdout


def _hash_temas(d: dict) -> str:
    return K.sha256_texto(json.dumps(
        [(b["bucket"], b.get("temas"), b.get("observacao_geral")) for b in d.get("buckets", [])],
        ensure_ascii=False, sort_keys=True))[:12]


def proveniencia(slug: str, atual: dict) -> dict:
    """O commit em que os temas PUBLICADOS HOJE apareceram (o mais antigo da
    sequência ininterrupta de commits com o mesmo conteúdo de temas)."""
    p = f"resultado/{slug}.json"
    h = _hash_temas(atual)
    primeiro = None
    linhas = _git("log", "--format=%H|%cI|%s", "--", p).strip().splitlines()
    for ln in linhas:
        sha, data, msg = ln.split("|", 2)
        try:
            d = json.loads(_git("show", f"{sha}:{p}"))
        except ValueError:
            break
        if _hash_temas(d) != h:
            break
        primeiro = (sha, data, msg)
    if primeiro is None:
        return {"commit": None}
    sha, data, msg = primeiro
    lote = K.LOTES.get(sha[:9], {"lote": "?", "professor": "?", "deepseek": None})
    return {"commit": sha[:9], "data": data, "mensagem": msg[:100],
            "spec_na_sintese": json.loads(_git("show", f"{sha}:{p}")).get("spec_version"),
            "lote": lote["lote"], "professor": lote["professor"],
            "epoca_professor": (K.epoca_do_professor(data[:10]) if lote.get("deepseek")
                                else None),
            "n_commits_do_arquivo": len(linhas)}


def carregar_consenso() -> dict:
    por = collections.defaultdict(list)
    for ln in CONSENSO.read_text(encoding="utf-8").split("\n"):
        if ln.strip():
            r = json.loads(ln)
            por[r["slug"]].append(r)
    return por


def textos_do_bruto(slug: str) -> dict[str, dict]:
    """`{id: {"texto"}}` pelo leitor do pacote (`bruto.carregar`): o texto pode
    ter separadores Unicode que `splitlines()` partiria."""
    from espectro24.bruto import carregar
    if not (K.BRUTO_DIR / slug / "reviews.jsonl").exists():
        return {}
    _, todas = carregar(slug, raiz=K.BRUTO_DIR)
    return {r.id: {"texto": r.texto} for r in todas}


# --- Verificação de conteúdo de talk-to-me-2022 (pedido explícito) ----------
# Os termos são do longa de 2022 (Philippou, a mão embalsamada, Mia, sessão de
# possessão) e do outro filme homônimo de 2007 (Kasi Lemmons, Don Cheadle como
# o radialista Petey Greene). É sinal, não prova.
TERMOS_2022 = ("philippou", "hand", "mão", "mano", "main", "mia", "possess",
               "possuí", "seance", "séance", "a24", "talk to me", "tiktok")
TERMOS_2007 = ("cheadle", "petey", "greene", "lemmons", "radio dj", "disc jockey",
               "ejiofor")


def sinais_de_corpus(slug: str, ids: list[str]) -> dict:
    tx = textos_do_bruto(slug)
    def conta(termos):
        return sum(1 for i in ids if any(re.search(re.escape(t), (tx.get(i) or {}).get("texto", "").lower())
                                         for t in termos))
    return {"n_reviews_analisadas": len(ids), "com_termo_2022": conta(TERMOS_2022),
            "com_termo_2007": conta(TERMOS_2007),
            "termos_2022": TERMOS_2022, "termos_2007": TERMOS_2007}


def localizar(arquivo: str, padrao: str) -> str:
    p = K.RAIZ / arquivo
    for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(padrao, ln):
            return f"{arquivo}:{i}"
    return f"{arquivo}:?"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR)
    a = ap.parse_args()

    toks = K.carregar_tokenizers(a.tokenizers)
    pubs = K.publicados()
    consenso = carregar_consenso()
    gab = K.ler_json(GABARITO)
    gab_txt = K.ler_json(GABARITO_TEXTOS)["textos"]
    gab_am = {r["id"]: r for r in K.ler_json(GABARITO_AMOSTRA)["reviews"]}

    from espectro24 import taxonomia as T
    from espectro24.config import MAX_TEMAS

    filmes: dict[str, dict] = {}
    ex: dict[str, list[dict]] = {e: [] for e in
                                 ("sintese", "narrativa", "veredito", "condicoes",
                                  "classificacao_consenso", "classificacao_gabarito")}
    falhas_remontagem: dict[str, list[str]] = collections.defaultdict(list)

    for slug, pub in pubs.items():
        prov = proveniencia(slug, pub)
        ident = (pub.get("ficha") or {}).get("identidade") or {}
        f = {"slug": slug, "spec_version": pub.get("spec_version"),
             "data_coleta": pub.get("data_coleta"), "sintese": prov,
             "identidade_status": ident.get("status"),
             "excluido": K.EXCLUIR_FILMES.get(slug),
             "buckets": {}, "estagios": {}}
        bs = None
        if pub.get("buckets") and any(b.get("modo") != "sem_analise" for b in pub["buckets"]):
            try:
                bs = {b.nome: b for b in K.buckets_remontados(slug, pub)}
            except Exception as e:  # noqa: BLE001
                falhas_remontagem["sintese"].append(f"{slug}: {type(e).__name__}: {e}")
        n_ex_sintese = 0
        for bp in pub.get("buckets", []):
            ok, motivo = K.bucket_e_exemplo_de_sintese(bp)
            temas = bp.get("temas") or []
            f["buckets"][bp["bucket"]] = {"modo": bp.get("modo"), "n_validas": bp.get("n_validas"),
                                         "n_temas": len(temas), "utilizavel": ok,
                                         "motivo": motivo}
            if not ok or bs is None:
                continue
            s, u = K.prompt_sintese(bs[bp["bucket"]])
            alvo = K.serializar_alvo(K.alvo_publicado(bp))
            ex["sintese"].append({"slug": slug, "bucket": bp["bucket"],
                                  "n_temas": len(temas), "chars_user": len(u),
                                  "excluido": bool(f["excluido"]),
                                  "tokens": K.tokens_do_par(toks, s, u, alvo)})
            n_ex_sintese += 1
        f["estagios"]["sintese"] = n_ex_sintese

        for est, fp, fs in (("narrativa", K.prompt_narrativa, K.saida_narrativa),
                            ("veredito", K.prompt_veredito, K.saida_veredito),
                            ("condicoes", K.prompt_condicoes, K.saida_condicoes)):
            saida = fs(pub)
            if not saida or not pub.get("eixos"):
                f["estagios"][est] = 0
                continue
            try:
                pr = fp(pub)
            except Exception as e:  # noqa: BLE001
                falhas_remontagem[est].append(f"{slug}: {type(e).__name__}: {str(e)[:120]}")
                f["estagios"][est] = 0
                continue
            if pr is None:
                f["estagios"][est] = 0
                continue
            ex[est].append({"slug": slug, "excluido": bool(f["excluido"]),
                            "tokens": K.tokens_do_par(toks, pr[0], pr[1], saida)})
            f["estagios"][est] = 1

        regs = consenso.get(slug, [])
        tx = textos_do_bruto(slug) if regs else {}
        n_cls = 0
        for r in regs:
            texto = (tx.get(r["id"]) or {}).get("texto")
            if texto is None:
                continue
            from votacao_3 import mensagem_usuario
            u = mensagem_usuario({"nivel": r["nivel"], "texto": texto})
            out = json.dumps({"eixos": r["eixos"], "temas_livres": []}, ensure_ascii=False)
            ex["classificacao_consenso"].append({"slug": slug, "excluido": bool(f["excluido"]),
                                                 "tokens": K.tokens_do_par(toks, T.SYSTEM, u, out)})
            n_cls += 1
        f["estagios"]["classificacao_consenso"] = n_cls
        filmes[slug] = f

    # gabarito humano: 100 reviews, rótulo final do dono
    for rid, rot in gab.items():
        am = gab_am.get(rid, {})
        texto = gab_txt.get(rid)
        if isinstance(texto, dict):
            texto = texto.get("texto")
        if not texto:
            continue
        from votacao_3 import mensagem_usuario
        u = mensagem_usuario({"nivel": am.get("nivel"), "texto": texto})
        out = json.dumps({"eixos": rot["eixos"], "temas_livres": []}, ensure_ascii=False)
        ex["classificacao_gabarito"].append({"slug": am.get("slug"), "id": rid,
                                             "excluido": am.get("slug") in K.EXCLUIR_FILMES
                                             or (am.get("slug") or "").startswith("obsession"),
                                             "tokens": K.tokens_do_par(toks, T.SYSTEM, u, out)})

    # ---------------- agregados ----------------
    resumo = {}
    for est, lst in ex.items():
        uteis = [x for x in lst if not x["excluido"]]
        por_tok = {}
        for nome in K.CANDIDATOS:
            ent = [x["tokens"][nome]["entrada"] for x in uteis]
            sai = [x["tokens"][nome]["saida"] for x in uteis]
            tot = [x["tokens"][nome]["total"] for x in uteis]
            maior_total = max(tot) if tot else 0
            teto = TETO_SAIDA_PRODUCAO.get(est.split("_")[0])
            por_tok[nome] = {
                "entrada": K.quantis(ent), "saida": K.quantis(sai), "total": K.quantis(tot),
                "ctx_treino": K.arredondar(int(maior_total * (1 + MARGEM)), 512) if tot else None,
                "ctx_inferencia": (K.arredondar(int((max(ent) + teto[1]) * (1 + MARGEM)), 1024)
                                   if (tot and teto) else None),
            }
        filmes_com = sorted({x["slug"] for x in uteis if x.get("slug")})
        resumo[est] = {"n_exemplos": len(uteis), "n_exemplos_excluidos": len(lst) - len(uteis),
                       "n_filmes": len(filmes_com), "tokens": por_tok}

    sem_estagio = {est: sorted(s for s, f in filmes.items()
                               if not f["estagios"].get(est) and not f["excluido"])
                   for est in ("sintese", "narrativa", "veredito", "condicoes",
                               "classificacao_consenso")}

    # bullets
    dist_bucket = collections.Counter(x["n_temas"] for x in ex["sintese"] if not x["excluido"])
    por_filme = collections.Counter()
    for s, f in filmes.items():
        if not f["excluido"]:
            por_filme[sum(b["n_temas"] for b in f["buckets"].values() if b["utilizavel"])] += 1

    lotes = collections.Counter((f["sintese"].get("lote"), f["sintese"].get("epoca_professor"))
                                for f in filmes.values())

    # pendências
    ttm = filmes.get("talk-to-me-2022")
    ttm_ids = []
    if ttm:
        from espectro24.pipeline import amostra_do_bruto
        am = amostra_do_bruto("talk-to-me-2022", coleta=pubs["talk-to-me-2022"]["coleta"],
                              raiz=K.BRUTO_DIR)
        ttm_ids = [r.id for rs in am.values() for r in rs]
    gab_obsession = sorted(rid for rid in gab
                           if (gab_am.get(rid, {}).get("slug") or "").startswith("obsession"))
    pend = {
        "excluir_proposto": K.EXCLUIR_FILMES,
        "sem_bloco_identidade": sorted(s for s, f in filmes.items()
                                       if f["identidade_status"] is None and not f["excluido"]),
        "talk_to_me_2022": {
            "identidade": (pubs["talk-to-me-2022"]["ficha"].get("identidade")
                           if "talk-to-me-2022" in pubs else None),
            "sintese_feita_em": ttm["sintese"] if ttm else None,
            "sinais_no_corpus_analisado": sinais_de_corpus("talk-to-me-2022", ttm_ids),
        },
        "gabarito_com_reviews_de_obsession": gab_obsession,
        "c22_nao_publicados": "55 filmes do lote C22 (excecao_c22.SLUGS) não têm "
                              "resultado/*.json: nenhum exemplo de síntese",
    }

    onde = {
        "MAX_TEMAS": localizar("src/espectro24/config.py", r"^MAX_TEMAS\s*="),
        "prompt_regra_3": localizar("src/espectro24/synthesize.py", r"no máximo \{MAX_TEMAS\}"),
        "corte_no_codigo": localizar("src/espectro24/synthesize.py", r"\[:MAX_TEMAS\]"),
    }
    saida = {"gerado_por": "scripts/finetune/inventario.py", "tokenizers": {
                 n: {"repo": c["repo"], "revisao": c["revisao"],
                     "tokenizer_json_sha256": K.sha256_arquivo(
                         K.pasta_do_candidato(a.tokenizers, n) / "tokenizer.json")}
                 for n, c in K.CANDIDATOS.items()},
             "formato_alvo_sintese": "JSON indent=2 (PROPOSTO; ver comum.serializar_alvo)",
             "margem_contexto": MARGEM, "teto_saida_producao": TETO_SAIDA_PRODUCAO,
             "resumo": resumo, "sem_estagio": sem_estagio,
             "falhas_remontagem": dict(falhas_remontagem),
             "bullets": {"max_temas": MAX_TEMAS, "fixo": False, "onde": onde,
                         "dist_por_bucket": dict(sorted(dist_bucket.items())),
                         "dist_por_filme": dict(sorted(por_filme.items()))},
             "lotes": [{"lote": k[0], "epoca_professor": k[1], "n_filmes": v}
                       for k, v in sorted(lotes.items(), key=lambda x: str(x[0]))],
             "pendencias": pend, "filmes": filmes,
             "exemplos_sintese": ex["sintese"]}
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "inventario.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    (a.saida / "inventario.md").write_text(md(saida), encoding="utf-8")
    print(md(saida)[:6000])


def md(s: dict) -> str:
    L = ["# Inventário — fase 0 do fine-tuning da síntese", "",
         "Gerado por `scripts/finetune/inventario.py` (zero rede, zero LLM). Números de "
         "contagem e de tokens são **MEDIDOS** com os tokenizers reais (revisões abaixo); "
         "a saída da síntese é o publicado reserializado em JSON indent=2 (**formato "
         "PROPOSTO**); a saída de condições é **ESTIMADA** (montada do publicado, que passou "
         "por leitura humana). Contexto = maior total × 1,10 (**PROPOSTO**), em múltiplo de 512 "
         "(treino) ou entrada máxima + teto de saída de produção × 1,10, em múltiplo de 1024 "
         "(inferência).", ""]
    L += ["| candidato | repo@revisão | sha256 do tokenizer.json |", "|---|---|---|"]
    for n, t in s["tokenizers"].items():
        L.append(f"| {n} | `{t['repo']}@{t['revisao'][:10]}` | `{t['tokenizer_json_sha256'][:16]}…` |")
    L += ["", "## Exemplos e tokens por estágio", ""]
    for est, r in s["resumo"].items():
        L += [f"### {est} — {r['n_exemplos']} exemplos utilizáveis em {r['n_filmes']} filmes "
              f"({r['n_exemplos_excluidos']} de filmes excluídos)", "",
              "| tokenizer | entrada med/p90/p99/máx | saída med/p90/p99/máx | total máx | ctx treino | ctx inferência |",
              "|---|---|---|---|---|---|"]
        for n, t in r["tokens"].items():
            e, o = t["entrada"], t["saida"]
            if not e.get("n"):
                continue
            L.append(f"| {n} | {e['mediana']:.0f} / {e['p90']} / {e['p99']} / {e['max']} | "
                     f"{o['mediana']:.0f} / {o['p90']} / {o['p99']} / {o['max']} | "
                     f"{t['total']['max']} | {t['ctx_treino']} | {t['ctx_inferencia'] or '—'} |")
        L.append("")
    L += ["## Filmes sem o estágio (fora os excluídos)", ""]
    for est, lst in s["sem_estagio"].items():
        L.append(f"- **{est}** ({len(lst)}): {', '.join(lst) if lst else '—'}")
    if s["falhas_remontagem"]:
        L += ["", "Falhas ao remontar o prompt com o código atual:", ""]
        for est, lst in s["falhas_remontagem"].items():
            L += [f"- {est}: {x}" for x in lst]
    b = s["bullets"]
    L += ["", "## Bullets (temas) por bucket", "",
          f"- Teto `MAX_TEMAS = {b['max_temas']}` — **não é fixo**: é máximo. Fixado em "
          f"`{b['onde']['MAX_TEMAS']}`, pedido no prompt em `{b['onde']['prompt_regra_3']}` "
          f"(\"no máximo\") e cortado no código em `{b['onde']['corte_no_codigo']}`.",
          f"- Por bucket utilizável (n temas → n buckets): {b['dist_por_bucket']}",
          f"- Por filme (soma dos buckets utilizáveis → n filmes): {b['dist_por_filme']}", "",
          "## Lote e época do professor", "", "| lote | época do professor | filmes |", "|---|---|---|"]
    for x in s["lotes"]:
        L.append(f"| {x['lote']} | {x['epoca_professor']} | {x['n_filmes']} |")
    p = s["pendencias"]
    L += ["", "## Pendências de identidade e corpus", ""]
    for slug, mot in p["excluir_proposto"].items():
        L.append(f"- **excluir de todos os conjuntos (PROPOSTO): `{slug}`** — {mot}")
    t = p["talk_to_me_2022"]
    L.append(f"- `talk-to-me-2022`: identidade `{(t['identidade'] or {}).get('status')}` "
             f"(tmdb {(t['identidade'] or {}).get('tmdb_id_escolhido')}); síntese de "
             f"{(t['sintese_feita_em'] or {}).get('data', '?')[:10]}; sinais no corpus analisado: "
             f"{t['sinais_no_corpus_analisado']['com_termo_2022']}/"
             f"{t['sinais_no_corpus_analisado']['n_reviews_analisadas']} com termo do longa de "
             f"2022, {t['sinais_no_corpus_analisado']['com_termo_2007']} com termo do filme de 2007.")
    L.append(f"- gabarito humano com reviews de obsession-*: {len(p['gabarito_com_reviews_de_obsession'])}")
    L.append(f"- sem bloco `identidade` (guarda v1.9.49 nunca rodou no artefato): "
             f"{len(p['sem_bloco_identidade'])} — {', '.join(p['sem_bloco_identidade'])}")
    L.append(f"- {p['c22_nao_publicados']}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
