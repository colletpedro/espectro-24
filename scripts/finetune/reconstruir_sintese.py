"""Fase 0 do fine-tuning — (b) reconstrução do par de treino da SÍNTESE.

Zero rede, zero LLM. Responde, com medição:

1. A telemetria/os logs guardam o prompt enviado e a resposta crua? (varre os
   artefatos por marcas do prompt e da resposta);
2. O prompt remontado HOJE (código atual + `dados/bruto` + `coleta` do
   publicado) é byte a byte o que o código E O DADO DA ÉPOCA produziriam? (o
   `src/` de cada commit de síntese é exportado com `git archive` e roda em
   subprocesso — `_remontar_epoca.py`);
3. A amostra remontada é a que o publicado declara (n, composição) e a que o
   bloco `eixos` contou (célula a célula contra o consenso verificado)?
4. O publicado é a saída crua do DeepSeek? (o que o código faz entre a
   resposta e o JSON: `synthesize._construir_temas` e a retentativa);
5. Os validadores mecânicos ATUAIS da síntese, sobre cada síntese publicada;
6. Grava um par completo de um filme de TREINO para leitura.

Saída: `finetune/reconstrucao.json`, `finetune/reconstrucao.md` e
`finetune/par_exemplo/<slug>__<bucket>.{json,md}`.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

AQUI = Path(__file__).resolve().parent
MARCA_SYSTEM = "Você é uma etapa de um pipeline que agrega reviews"
MARCA_USER = "Total de reviews analisadas neste bucket"
# Onde o texto do prompt existe como CÓDIGO ou documentação, não como registro
# do que foi enviado.
NAO_E_REGISTRO = ("src/", "scripts/", "tests/", "experimentos-", "SPEC.md", "HISTORICO_",
                  "CHANGELOG.md", "venv/", ".git/", "finetune/")


def _git(*a) -> str:
    return K.rodar_texto(["git", "-C", str(K.RAIZ), *a]).stdout


# ---------------------------------------------------------------------------
# 1. fonte primária
# ---------------------------------------------------------------------------

def varrer(raizes: list[Path]) -> dict:
    """Arquivos de texto (json/jsonl/log/md/txt) que contêm o prompt da síntese
    ou o cabeçalho da mensagem de usuário. Pula HTML de cache (página raspada)."""
    achados, n = [], 0
    for raiz in raizes:
        for p in Path(raiz).rglob("*"):
            rel = str(p.relative_to(raiz))
            if (not p.is_file() or p.suffix not in (".json", ".jsonl", ".log", ".md", ".txt")
                    or any(rel.startswith(x) or f"/{x}" in f"/{rel}" for x in NAO_E_REGISTRO)):
                continue
            n += 1
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if MARCA_SYSTEM in t or MARCA_USER in t:
                achados.append(str(p))
    return {"raizes": [str(r) for r in raizes], "arquivos_varridos": n, "achados": achados}


# ---------------------------------------------------------------------------
# 2–3. remontagem
# ---------------------------------------------------------------------------

def remontar_atual(pubs: dict, filmes_inv: dict) -> dict:
    import checagem_bullets as C
    from espectro24 import eixos as E
    catalogo = E.carregar_classificacao(K.RAIZ / E.CONSENSO_VERIFICADO)
    fora = {}
    for slug, pub in pubs.items():
        if filmes_inv[slug]["excluido"]:
            continue
        bs = {b.nome: b for b in K.buckets_remontados(slug, pub)}
        reg = {"buckets": {}}
        for bp in pub["buckets"]:
            b = bs[bp["bucket"]]
            s, u = K.prompt_sintese(b)
            reg["buckets"][bp["bucket"]] = {
                "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u),
                "n_igual": b.n_validas == bp["n_validas"],
                "composicao_igual": {str(k): v for k, v in b.composicao_atingida.items()}
                                    == bp.get("composicao_atingida"),
                "ids": [r.viewing_id for r in b.reviews_analisadas]}
        try:
            analisadas = {n: set(v["ids"]) for n, v in reg["buckets"].items()}
            cls = C.classificacao_analisada(slug, analisadas, catalogo)
            reg["celulas_eixos_conferidas"] = C.reconciliar(pub, cls)
            reg["eixos_reconciliados"] = True
        except Exception as e:  # noqa: BLE001
            reg["eixos_reconciliados"] = False
            reg["erro_eixos"] = f"{type(e).__name__}: {str(e)[:200]}"
        for v in reg["buckets"].values():
            v.pop("ids")
        fora[slug] = reg
    return fora


def remontar_por_epoca(filmes_inv: dict, atual: dict) -> dict:
    """Agrupa os filmes pelo commit da síntese; para cada commit exporta o
    `src/` dele e remonta com aquele código, a `coleta` daquele commit e o
    bruto — conferido blob a blob igual ao de HEAD antes de usar."""
    grupos = collections.defaultdict(list)
    for slug, f in filmes_inv.items():
        if slug in atual and f["sintese"].get("commit"):
            grupos[f["sintese"]["commit"]].append(slug)
    resultado, divergencias = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for commit, slugs in sorted(grupos.items()):
            dst = Path(tmp) / commit
            dst.mkdir()
            arq = subprocess.run(["git", "-C", str(K.RAIZ), "archive", commit, "src"],
                                 capture_output=True, check=True).stdout
            subprocess.run(["tar", "-x", "-C", str(dst)], input=arq, check=True)
            coletas, bruto_igual = {}, {}
            for s in slugs:
                coletas[s] = json.loads(_git("show", f"{commit}:resultado/{s}.json"))["coleta"]
                bruto_igual[s] = all(
                    _git("rev-parse", f"{commit}:dados/bruto/{s}/{f}").strip()
                    == _git("rev-parse", f"HEAD:dados/bruto/{s}/{f}").strip()
                    for f in ("reviews.jsonl", "meta.json"))
            (dst / "coletas.json").write_text(json.dumps(coletas), encoding="utf-8")
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            env["PYTHONPATH"] = str(dst / "src")
            env["PYTHONIOENCODING"] = "utf-8"
            r = K.rodar_texto([sys.executable, str(AQUI / "_remontar_epoca.py"),
                               "--src", str(dst / "src"), "--bruto", str(K.BRUTO_DIR),
                               "--coletas", str(dst / "coletas.json")], env=env)
            if r.returncode != 0:
                resultado[commit] = {"erro": r.stderr[-2000:], "slugs": slugs}
                continue
            epoca = json.loads(r.stdout)
            iguais = 0
            for s in slugs:
                for b, h in epoca[s].items():
                    a = atual[s]["buckets"][b]
                    ok = (a["system_sha256"] == h["system_sha256"]
                          and a["user_sha256"] == h["user_sha256"])
                    iguais += ok
                    if not ok:
                        divergencias.append({"slug": s, "bucket": b, "commit": commit,
                                             "system_igual": a["system_sha256"] == h["system_sha256"],
                                             "user_igual": a["user_sha256"] == h["user_sha256"]})
            resultado[commit] = {"n_filmes": len(slugs),
                                 "n_buckets": sum(len(epoca[s]) for s in slugs),
                                 "buckets_byte_a_byte": iguais,
                                 "bruto_igual_ao_de_HEAD": sum(bruto_igual.values())}
    return {"por_commit": resultado, "divergencias": divergencias}


# ---------------------------------------------------------------------------
# 4–5. pós-processamento e validadores
# ---------------------------------------------------------------------------

def validar_publicado(bp: dict) -> dict:
    """Os validadores mecânicos de HOJE (`synthesize`), sobre o bucket
    publicado. `aspas_bruto`/`clamp_bruto` dizem se a RESPOSTA CRUA violava
    (a flag que o código gravou ao corrigir); os demais olham o publicado."""
    from espectro24 import synthesize as S
    from espectro24.config import MAX_TEMAS
    from espectro24.models import Tema
    temas = bp.get("temas") or []
    objs = [Tema(**{k: t[k] for k in ("tema", "mencoes_aproximadas", "n_reviews_analisadas",
                                     "exemplo_parafraseado")}) for t in temas]
    obs = bp.get("observacao_geral") or ""
    n = bp.get("n_validas")
    m = [t["mencoes_aproximadas"] for t in temas]
    v = {
        "idioma_pt_br": S._idioma_e_pt_br(S._texto_para_checagem_idioma(objs, obs)),
        "escopo_sem_marcador": not S._tem_marcador_de_escopo(obs),
        "sem_aspas_no_publicado": not any(c in t["exemplo_parafraseado"]
                                          for t in temas for c in S._ASPAS_CHARS),
        "mencoes_em_0_n": all(0 <= x <= n for x in m),
        "max_temas": len(temas) <= MAX_TEMAS,
        "ordem_decrescente": m == sorted(m, reverse=True),
        "n_reviews_analisadas_igual_n": all(t["n_reviews_analisadas"] == n for t in temas),
        "campos_nao_vazios": all(t["tema"].strip() and t["exemplo_parafraseado"].strip()
                                 for t in temas) and bool(obs.strip()),
        # regra 3 do PROMPT (não é validador de código): sem tema de menção
        # única, salvo bucket com menos de 5 reviews
        "regra3_sem_mencao_unica": n < 5 or all(x >= 2 for x in m),
        "flags_publicadas_ok": not bp.get("idioma_invalido") and not bp.get("escopo_suspeito"),
    }
    bruto = {"aspas_bruto": not any(t.get("aspas_removidas") for t in temas),
             "clamp_bruto": not any(t.get("mencoes_clampadas") for t in temas)}
    return {"publicado": v, "resposta_crua": bruto,
            "passa_publicado": all(v.values()),
            "passa_crua_estimada": all(v.values()) and all(bruto.values())}


def pos_processamento(pubs: dict, filmes_inv: dict) -> dict:
    c = collections.Counter()
    exemplos = {"aspas_removidas": [], "mencoes_clampadas": []}
    validacao = collections.Counter()
    falhas = collections.defaultdict(list)
    for slug, pub in pubs.items():
        if filmes_inv[slug]["excluido"]:
            continue
        for bp in pub["buckets"]:
            ok, _ = K.bucket_e_exemplo_de_sintese(bp)
            if not ok:
                continue
            c["buckets"] += 1
            for i, t in enumerate(bp["temas"]):
                c["temas"] += 1
                if t.get("aspas_removidas"):
                    c["temas_aspas_removidas"] += 1
                    exemplos["aspas_removidas"].append((slug, bp["bucket"], i))
                if t.get("mencoes_clampadas"):
                    c["temas_mencoes_clampadas"] += 1
                    exemplos["mencoes_clampadas"].append((slug, bp["bucket"], i,
                                                          t.get("mencoes_valor_original")))
            if bp.get("idioma_invalido"):
                c["buckets_idioma_invalido"] += 1
            if bp.get("escopo_suspeito"):
                c["buckets_escopo_suspeito"] += 1
            r = validar_publicado(bp)
            validacao["passa_publicado"] += r["passa_publicado"]
            validacao["passa_crua_estimada"] += r["passa_crua_estimada"]
            for k, val in {**r["publicado"], **r["resposta_crua"]}.items():
                if not val:
                    falhas[k].append(f"{slug}/{bp['bucket']}")
    return {"contagens": dict(c), "exemplos": exemplos,
            "validadores": {"n_buckets": c["buckets"], **dict(validacao),
                            "falhas_por_regra": {k: v for k, v in sorted(falhas.items())}}}


# ---------------------------------------------------------------------------
# 6. o par de leitura
# ---------------------------------------------------------------------------

def gravar_par(slug: str, bucket: str, pubs: dict, toks: dict, destino: Path,
               atual: dict, epoca: dict, filmes_inv: dict) -> list[Path]:
    pub = pubs[slug]
    b = {x.nome: x for x in K.buckets_remontados(slug, pub)}[bucket]
    bp = next(x for x in pub["buckets"] if x["bucket"] == bucket)
    s, u = K.prompt_sintese(b)
    alvo = K.serializar_alvo(K.alvo_publicado(bp))
    tk = K.tokens_do_par(toks, s, u, alvo)
    commit = filmes_inv[slug]["sintese"]["commit"]
    meta = {"slug": slug, "bucket": bucket,
            "sintese": filmes_inv[slug]["sintese"],
            "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u),
            "byte_a_byte_com_o_codigo_da_epoca":
                not any(d["slug"] == slug and d["bucket"] == bucket for d in epoca["divergencias"])
                and "erro" not in epoca["por_commit"].get(commit, {}),
            "eixos_reconciliados": atual[slug].get("eixos_reconciliados"),
            "alvo": "publicado (pós-processado), reserializado em JSON indent=2 — PROPOSTO",
            "flags_do_codigo_no_publicado": {
                "aspas_removidas": [t["tema"] for t in bp["temas"] if t.get("aspas_removidas")],
                "mencoes_clampadas": [t["tema"] for t in bp["temas"] if t.get("mencoes_clampadas")],
                "idioma_invalido": bp.get("idioma_invalido"),
                "escopo_suspeito": bp.get("escopo_suspeito")},
            "tokens": tk}
    destino.mkdir(parents=True, exist_ok=True)
    base = destino / f"{slug}__{bucket}"
    (base.with_suffix(".json")).write_text(json.dumps(
        {"meta": meta, "system": s, "user": u, "assistant": alvo}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    md = [f"# Par reconstruído — `{slug}` / {bucket} (filme de TREINO)", "",
          "Contém reviews de terceiros do Letterboxd (as mesmas de `dados/bruto`).", "",
          "```json", json.dumps(meta, ensure_ascii=False, indent=1), "```", "",
          "## system", "", "```text", s, "```", "", "## user", "", "```text", u, "```", "",
          "## assistant (alvo PROPOSTO = publicado)", "", "```json", alvo, "```", ""]
    (base.with_suffix(".md")).write_text("\n".join(md), encoding="utf-8")
    return [base.with_suffix(".json"), base.with_suffix(".md")]


def lado_a_lado(pubs: dict, pos: dict) -> list[dict]:
    """O que se sabe da resposta crua em cada correção do código. Para o
    clamp, o valor cru está gravado; para as aspas, só que existiam (a posição
    não é recuperável)."""
    fora = []
    for slug, bucket, i, orig in pos["exemplos"]["mencoes_clampadas"][:2]:
        t = next(b for b in pubs[slug]["buckets"] if b["bucket"] == bucket)["temas"][i]
        fora.append({"tipo": "clamp", "slug": slug, "bucket": bucket, "tema": t["tema"],
                     "cru": {"mencoes_aproximadas": orig},
                     "publicado": {"mencoes_aproximadas": t["mencoes_aproximadas"],
                                   "n_reviews_analisadas": t["n_reviews_analisadas"]}})
    for slug, bucket, i in pos["exemplos"]["aspas_removidas"][:2]:
        t = next(b for b in pubs[slug]["buckets"] if b["bucket"] == bucket)["temas"][i]
        fora.append({"tipo": "aspas", "slug": slug, "bucket": bucket, "tema": t["tema"],
                     "cru": "o mesmo texto COM aspas de citação (posições não gravadas)",
                     "publicado": t["exemplo_parafraseado"]})
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--varrer", type=Path, action="append", default=None,
                    help="raiz a varrer por prompt/resposta gravados (repetível)")
    ap.add_argument("--par", default="whiplash-2014/negativas")
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR)
    a = ap.parse_args()

    inv = K.ler_json(a.inventario)
    filmes_inv = inv["filmes"]
    split = K.ler_json(a.split)
    slug_par, bucket_par = a.par.split("/")
    if slug_par not in split["treino"]:
        raise SystemExit(f"{slug_par} não é de treino no split — escolha outro")
    if slug_par in K.REFERENCIA_5:
        raise SystemExit("o par de leitura não pode ser de um dos 5 da referência")

    pubs = K.publicados()
    fonte = varrer(a.varrer or [K.RAIZ])
    print(f"varredura: {fonte['arquivos_varridos']} arquivos, {len(fonte['achados'])} achados",
          flush=True)
    atual = remontar_atual(pubs, filmes_inv)
    print("remontagem atual ok", flush=True)
    epoca = remontar_por_epoca(filmes_inv, atual)
    print("remontagem por época ok", flush=True)
    pos = pos_processamento(pubs, filmes_inv)
    toks = K.carregar_tokenizers(a.tokenizers)
    arquivos_par = gravar_par(slug_par, bucket_par, pubs, toks, a.saida / "par_exemplo",
                              atual, epoca, filmes_inv)

    n_buckets = sum(len(v["buckets"]) for v in atual.values())
    sel = collections.Counter((v2["n_igual"], v2["composicao_igual"])
                              for v in atual.values() for v2 in v["buckets"].values())
    saida = {"gerado_por": "scripts/finetune/reconstruir_sintese.py",
             "fonte_primaria": fonte,
             "remontagem_atual": {"n_filmes": len(atual), "n_buckets": n_buckets,
                                  "selecao_n_e_composicao_iguais": sel.get((True, True), 0),
                                  "eixos_reconciliados": sum(1 for v in atual.values()
                                                             if v.get("eixos_reconciliados")),
                                  "celulas_eixos_conferidas": sum(v.get("celulas_eixos_conferidas", 0)
                                                                  for v in atual.values()),
                                  "erros_eixos": {s: v["erro_eixos"] for s, v in atual.items()
                                                  if not v.get("eixos_reconciliados")}},
             "remontagem_por_epoca": epoca, "pos_processamento": pos,
             "lado_a_lado": lado_a_lado(pubs, pos),
             "par_exemplo": [str(p.relative_to(K.RAIZ)) for p in arquivos_par],
             "hashes": {s: v["buckets"] for s, v in atual.items()}}
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "reconstrucao.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    (a.saida / "reconstrucao.md").write_text(md(saida), encoding="utf-8")
    print(md(saida))


def md(s: dict) -> str:
    f, ra, ep, pos = (s["fonte_primaria"], s["remontagem_atual"], s["remontagem_por_epoca"],
                      s["pos_processamento"])
    v = pos["validadores"]
    tot_ep = sum(x.get("n_buckets", 0) for x in ep["por_commit"].values())
    iguais_ep = sum(x.get("buckets_byte_a_byte", 0) for x in ep["por_commit"].values())
    L = ["# Reconstrução do par da síntese", "",
         "## 1. Fonte primária (prompt enviado / resposta crua gravados?)", "",
         f"Varridos {f['arquivos_varridos']} arquivos de texto em {f['raizes']} (fora código, "
         f"documentação e cache HTML). Achados com o prompt ou o cabeçalho da mensagem: "
         f"**{len(f['achados'])}**{': ' + ', '.join(f['achados']) if f['achados'] else ''}. "
         "Nenhum caminho do código grava o prompt nem a resposta crua da síntese: "
         "`synthesize_bucket` guarda só os temas já pós-processados (MEDIDO por leitura do código).",
         "", "## 2. Remontagem byte a byte", "",
         f"- Código atual × código da época: **{iguais_ep}/{tot_ep}** buckets com `system` e "
         f"`user` idênticos (sha256), remontados com o `src/` de cada commit de síntese.",
         "| commit | filmes | buckets | byte a byte | bruto igual ao de HEAD |", "|---|---|---|---|---|"]
    for c, x in ep["por_commit"].items():
        if "erro" in x:
            L.append(f"| `{c}` | {len(x['slugs'])} | — | ERRO | — |")
        else:
            L.append(f"| `{c}` | {x['n_filmes']} | {x['n_buckets']} | {x['buckets_byte_a_byte']} | "
                     f"{x['bruto_igual_ao_de_HEAD']}/{x['n_filmes']} |")
    L += ["", f"- Seleção (n e composição iguais ao publicado): {ra['selecao_n_e_composicao_iguais']}"
          f"/{ra['n_buckets']} buckets.",
          f"- Bloco `eixos` reconciliado célula a célula contra o consenso verificado, sobre a "
          f"amostra remontada: {ra['eixos_reconciliados']}/{ra['n_filmes']} filmes "
          f"({ra['celulas_eixos_conferidas']} células).",
          *(f"  - {k}: {e}" for k, e in ra["erros_eixos"].items()),
          "", "## 3. O publicado é a saída crua? Não.", "",
          f"Contagens nos {pos['contagens'].get('buckets')} buckets utilizáveis "
          f"({pos['contagens'].get('temas')} temas): aspas removidas em "
          f"{pos['contagens'].get('temas_aspas_removidas', 0)} temas; menções corrigidas (clamp) em "
          f"{pos['contagens'].get('temas_mencoes_clampadas', 0)}; buckets com `idioma_invalido` "
          f"{pos['contagens'].get('buckets_idioma_invalido', 0)}, `escopo_suspeito` "
          f"{pos['contagens'].get('buckets_escopo_suspeito', 0)}.", "",
          "Lado a lado (o que o dado guarda da resposta crua):", ""]
    for x in s["lado_a_lado"]:
        L.append(f"- **{x['tipo']}** `{x['slug']}/{x['bucket']}` — {x['tema']}: cru = "
                 f"{x['cru']} → publicado = {x['publicado']}")
    L += ["", "## 4. Validadores mecânicos atuais sobre o publicado", "",
          f"- Passam todos (publicado): **{v.get('passa_publicado', 0)}/{v['n_buckets']}**",
          f"- Passariam todos se o alvo fosse a resposta crua (estimado pelas flags de correção): "
          f"**{v.get('passa_crua_estimada', 0)}/{v['n_buckets']}**", ""]
    for k, lst in v["falhas_por_regra"].items():
        L.append(f"  - `{k}` falha em {len(lst)}: {', '.join(lst[:12])}{' …' if len(lst) > 12 else ''}")
    L += ["", f"## 5. Par de leitura: {', '.join(s['par_exemplo'])}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
