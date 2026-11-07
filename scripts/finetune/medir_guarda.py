"""Guarda de quantidade — medição no DESENVOLVIMENTO (2026-11-05). Zero rede.

Dados de desenvolvimento (decisão do dono): as saídas da Fase 4 (treinado, base
e o publicado dos 30 filmes de teste, cujo teste está consumido) e o publicado
dos 60 filmes de treino. A avaliação de verdade é em filmes nunca vistos (C22).

Mede, por fonte e no total:
- M1 antes e depois (exemplo_parafraseado, a lista CONGELADA);
- % de textos alterados (de todos e dos que tinham quantidade);
- os textos sem reescrita possível, com o motivo (candidatos ao fallback);
- buckets com pelo menos um texto pendente (a carga do fallback: nova chamada do bucket);
- os temas (`tema`) e a `observacao_geral`: mesma lista, só descritivo;
- invariantes: nenhum bullet some, nenhuma ordem muda, nenhum número aparece,
  nenhum texto sem quantidade é tocado.

    medir_guarda.py medir   → finetune/guarda/dev_medicao.json e .md
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
from espectro24 import guarda_quantidade as G  # noqa: E402

PASTA = K.FINETUNE_DIR / "guarda"
FONTES = ("treinado", "base", "publicado_teste", "publicado_treino")


def carregar(split: dict) -> dict[str, list[dict]]:
    """fonte → lista de buckets {slug, bucket, temas, observacao_geral}."""
    out: dict[str, list[dict]] = {f: [] for f in FONTES}
    for lado in ("treinado", "base"):
        for arq in sorted((K.FINETUNE_DIR / "fase2" / f"sintese_{lado}").glob("*__*.json")):
            reg = K.ler_json(arq)
            if not reg.get("ok"):
                continue
            bf = reg["bucket_final"]
            out[lado].append({"slug": reg["slug"], "bucket": reg["bucket"],
                              "temas": bf["temas"], "observacao_geral": bf["observacao_geral"]})
    for conj, fonte in (("teste", "publicado_teste"), ("treino", "publicado_treino")):
        for slug in sorted(split[conj]):
            pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
            for b in pub["buckets"]:
                ok, _ = K.bucket_e_exemplo_de_sintese(b)
                if ok:
                    out[fonte].append({"slug": slug, "bucket": b["bucket"], "temas": b["temas"],
                                       "observacao_geral": b.get("observacao_geral") or ""})
    return out


def medir_fonte(buckets: list[dict]) -> tuple[dict, list[dict]]:
    n = antes = depois = alterados = 0
    regras = collections.Counter()
    pendentes: list[dict] = []
    motivos = collections.Counter()
    buckets_com_pendente = set()
    tema_m1 = obs_m1 = 0
    n_temas_total = 0
    violacoes = []
    pares: list[dict] = []
    for b in buckets:
        for i, t in enumerate(b["temas"]):
            ex = t["exemplo_parafraseado"]
            r = G.reescrever(ex)
            n += 1
            n_temas_total += 1
            tinha = G.tem_quantidade(ex)
            antes += tinha
            depois += r.residual
            tema_m1 += G.tem_quantidade(t["tema"])
            if r.alterado and not tinha:
                violacoes.append(f"{b['slug']}/{b['bucket']}#{i}: alterou texto sem quantidade")
            if r.alterado and re.findall(r"\d+", r.texto) != re.findall(r"\d+", ex):
                violacoes.append(f"{b['slug']}/{b['bucket']}#{i}: número")
            if G.reescrever(r.texto).texto != r.texto:
                violacoes.append(f"{b['slug']}/{b['bucket']}#{i}: não idempotente")
            if r.alterado:
                alterados += 1
                regras.update(r.regras)
                pares.append({"slug": b["slug"], "bucket": b["bucket"], "i": i, "antes": ex,
                              "depois": r.texto, "regras": r.regras})
            if r.residual:
                buckets_com_pendente.add((b["slug"], b["bucket"]))
                pendentes.append({"slug": b["slug"], "bucket": b["bucket"], "i": i,
                                  "texto": ex, "resultado": r.texto, "motivos": r.pendentes})
                for p in r.pendentes:
                    motivos[p.split(":")[0] + ":" + p.split(":", 1)[1][:70]] += 1
        obs_m1 += G.tem_quantidade(b["observacao_geral"])
    res = {"buckets": len(buckets), "bullets": n,
           "m1_antes": antes, "m1_antes_pct": round(100 * antes / n, 2) if n else None,
           "m1_depois": depois, "m1_depois_pct": round(100 * depois / n, 2) if n else None,
           "alterados": alterados, "alterados_pct_de_todos": round(100 * alterados / n, 2) if n else None,
           "alterados_pct_dos_com_quantidade": round(100 * alterados / antes, 2) if antes else None,
           "sem_reescrita_possivel": len(pendentes),
           "buckets_com_pelo_menos_um_pendente": len(buckets_com_pendente),
           "regras": dict(regras.most_common()),
           "motivos_dos_pendentes": dict(motivos.most_common()),
           "temas_m1": tema_m1, "temas_m1_pct": round(100 * tema_m1 / n_temas_total, 2) if n_temas_total else None,
           "observacao_geral_m1": obs_m1, "observacao_geral_m1_pct": round(100 * obs_m1 / len(buckets), 2),
           "violacoes_de_invariante": violacoes}
    return res, pares, pendentes


def cmd_medir(a) -> None:
    split = K.ler_json(a.split)
    fontes = carregar(split)
    saida = {"gerado_por": "scripts/finetune/medir_guarda.py medir",
             "guarda_sha256": K.sha256_arquivo(Path(G.__file__)),
             "lista_sha256": G.LISTA_SHA256, "fontes": {}, "pendentes": {}}
    todos = collections.Counter()
    pares_all: list[dict] = []
    for nome, bs in fontes.items():
        r, pares, pend = medir_fonte(bs)
        saida["fontes"][nome] = r
        saida["pendentes"][nome] = pend
        for p in pares:
            pares_all.append({"fonte": nome, **p})
        for k in ("buckets", "bullets", "m1_antes", "m1_depois", "alterados",
                  "sem_reescrita_possivel", "buckets_com_pelo_menos_um_pendente", "temas_m1"):
            todos[k] += r[k]
    saida["total"] = dict(todos)
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / "dev_pares.json").write_text(json.dumps(
        {"guarda_sha256": saida["guarda_sha256"], "pares": pares_all}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    (PASTA / "dev_medicao.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n",
                                            encoding="utf-8")
    linhas = ["# Guarda de quantidade — medição no DESENVOLVIMENTO", "",
              "MEDIDO. Dados de desenvolvimento (a avaliação real é o C22, em filmes novos). "
              f"Guarda `{saida['guarda_sha256'][:12]}…`, lista congelada `{G.LISTA_SHA256[:12]}…`.", "",
              "| fonte | bullets | M1 antes | M1 depois | alterados (% de todos) | sem reescrita | buckets c/ pendente |",
              "|---|---|---|---|---|---|---|"]
    for nome, r in saida["fontes"].items():
        linhas.append(f"| {nome} | {r['bullets']} | {r['m1_antes']} ({r['m1_antes_pct']}%) | "
                      f"{r['m1_depois']} ({r['m1_depois_pct']}%) | {r['alterados']} "
                      f"({r['alterados_pct_de_todos']}%) | {r['sem_reescrita_possivel']} | "
                      f"{r['buckets_com_pelo_menos_um_pendente']}/{r['buckets']} |")
    linhas += ["", "Temas (`tema`) com palavra da lista: " +
               ", ".join(f"{n} {r['temas_m1']}/{r['bullets']}" for n, r in saida["fontes"].items()),
               "", "`observacao_geral` com palavra da lista (descritivo): " +
               ", ".join(f"{n} {r['observacao_geral_m1']}/{r['buckets']}" for n, r in saida["fontes"].items()),
               "", "Invariantes violados: " +
               str(sum(len(r["violacoes_de_invariante"]) for r in saida["fontes"].values())), ""]
    (PASTA / "dev_medicao.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"gravado: {PASTA / 'dev_medicao.json'} sha256 {K.sha256_arquivo(PASTA / 'dev_medicao.json')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("medir")
    a = ap.parse_args()
    cmd_medir(a)


if __name__ == "__main__":
    main()
