"""Fase 0 do fine-tuning — (e) custo e efeito de limpar o treino com o juiz v2.2.

Nenhum juiz roda aqui. Estima, com dados já existentes:

1. o custo do juiz v2.2 congelado (`scripts/juiz_bullets_v2.py`,
   `config_sha256` 44606cf1…, sem alteração) sobre TODOS os bullets dos
   filmes de treino — 5 pares por bullet;
2. a variante só de LIMPEZA: julgar as 5 reviews na ordem de similaridade
   (`rank`) e parar no primeiro par com apoio. A decisão "sem apoio" é a
   mesma do juiz completo: sem apoio = nenhum dos 5 pares com apoio
   (`checagem_bullets.apoio_por_bullet` / `resumo`, `n_apoio == 0`), e cada par
   é uma chamada independente (`juiz_bullets_v2.rodar`: um par por chamada,
   seed fixa, sem estado entre pares; `vereditos` recalcula o apoio do par só
   do trecho e do texto dele). Um bullet sem apoio é julgado nos 5 pares nas
   duas variantes; um bullet com apoio para no 1º "sim" e continua "com
   apoio". A economia sai da posição do 1º "sim" na medição de referência;
3. a regra "bucket com qualquer bullet sem apoio sai inteiro do treino":
   quantos exemplos ela remove;
4. três opções — filtrar tudo, filtrar parte, não filtrar.

Entradas: `finetune/split.json`, `finetune/inventario.json` e a saída da
medição de referência (branch `gate-local`, `checagem-bullets/`), lida com
`git show` — `juiz_entrada.jsonl` e `juiz_v2/saida_v2.2.jsonl`.

Saída: `finetune/limpeza.json` e `finetune/limpeza.md`.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

SEG_POR_PAR = 16.0
PARES = 5
RAMO_REFERENCIA = "gate-local"


def _git_show(ramo: str, caminho: str) -> str:
    r = K.rodar_texto(["git", "-C", str(K.RAIZ), "show", f"{ramo}:{caminho}"])
    if r.returncode:
        raise SystemExit(f"sem {ramo}:{caminho}: {r.stderr.strip()}")
    return r.stdout


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - m, 3), round(c + m, 3)]


def posicoes(ramo: str) -> dict:
    import juiz_bullets_v2 as J
    ent = [json.loads(l) for l in _git_show(ramo, "checagem-bullets/juiz_entrada.jsonl").split("\n") if l.strip()]
    regs = [json.loads(l) for l in _git_show(ramo, "checagem-bullets/juiz_v2/saida_v2.2.jsonl").split("\n") if l.strip()]
    sha = J.config_sha256(J.CONGELADA)
    ver = J.vereditos(ent, regs, J.CONGELADA)       # exige config_sha256 == a congelada
    por = collections.defaultdict(list)
    for p in ent:
        por[p["id_bullet"]].append(p)
    fora = {"config_sha256": sha}
    for lado in ("publicado", "local"):
        prim, seg = collections.Counter(), collections.Counter()
        pares_1, pares_2, buckets = 0, 0, collections.defaultdict(int)
        for b, ps in por.items():
            if not b.startswith(lado + "|"):
                continue
            ps = sorted(ps, key=lambda p: p["rank"])
            sims = [i + 1 for i, p in enumerate(ps) if ver[p["id_par"]]["apoio"]]
            prim[sims[0] if sims else None] += 1
            seg[sims[1] if len(sims) > 1 else None] += 1
            pares_1 += sims[0] if sims else len(ps)
            pares_2 += sims[1] if len(sims) > 1 else len(ps)
            _, slug, bucket, _ = b.split("|")
            buckets[(slug, bucket)] += 0 if sims else 1
        nb = sum(prim.values())
        fora[lado] = {"n_bullets": nb,
                      "posicao_1o_sim": {str(k): v for k, v in prim.items()},
                      "pares_parando_no_1o_sim": pares_1,
                      "pares_parando_no_2o_sim": pares_2,
                      "pares_completo": nb * PARES,
                      "pares_por_bullet_1o_sim": round(pares_1 / nb, 3),
                      "pares_por_bullet_2o_sim": round(pares_2 / nb, 3),
                      "bullets_sem_apoio": nb - sum(v for k, v in prim.items() if k),
                      "buckets": len(buckets),
                      "buckets_com_algum_sem_apoio": sum(1 for v in buckets.values() if v)}
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR)
    a = ap.parse_args()
    sp = K.ler_json(a.split)
    treino = sp["treino"]
    bullets = sum(sp["filmes"][s]["n_bullets"] for s in treino)
    exemplos = sum(sp["filmes"][s]["n_buckets_sintese"] for s in treino)

    ref = posicoes(RAMO_REFERENCIA)
    pub = ref["publicado"]
    ppb_1 = pub["pares_por_bullet_1o_sim"]
    p_bucket = pub["buckets_com_algum_sem_apoio"] / pub["buckets"]
    p_bullet = pub["bullets_sem_apoio"] / pub["n_bullets"]
    p_bucket_binom = 1 - (1 - p_bullet) ** 6

    def horas(pares):
        return round(pares * SEG_POR_PAR / 3600, 1)

    v4 = [s for s in treino if sp["filmes"][s]["epoca_professor"] == "V4-Flash"]
    b_v4 = sum(sp["filmes"][s]["n_bullets"] for s in v4)
    ex_v4 = sum(sp["filmes"][s]["n_buckets_sintese"] for s in v4)
    opcoes = {
        "filtrar_tudo": {"filmes": len(treino), "bullets": bullets,
                         "horas_juiz_completo": horas(bullets * PARES),
                         "horas_parando_no_1o_sim": horas(bullets * ppb_1),
                         "exemplos_removidos_estimados": round(exemplos * p_bucket, 1),
                         "exemplos_restantes_estimados": round(exemplos * (1 - p_bucket), 1)},
        "filtrar_parte_v4flash": {"filmes": len(v4), "bullets": b_v4,
                                  "horas_juiz_completo": horas(b_v4 * PARES),
                                  "horas_parando_no_1o_sim": horas(b_v4 * ppb_1),
                                  "exemplos_removidos_estimados": round(ex_v4 * p_bucket, 1),
                                  "nota": "só a época V4-Flash (professor anterior): o "
                                          "critério do recorte é PROPOSTO, não medido"},
        "nao_filtrar": {"horas": 0.0, "exemplos_removidos": 0,
                        "bullets_sem_apoio_esperados_no_treino": round(bullets * p_bullet, 1)},
    }
    saida = {"gerado_por": "scripts/finetune/estimar_limpeza.py",
             "referencia": ref, "seg_por_par": SEG_POR_PAR,
             "treino": {"filmes": len(treino), "bullets": bullets, "exemplos": exemplos},
             "economia_parando_no_1o_sim": round(1 - ppb_1 / PARES, 3),
             "p_bucket_com_sem_apoio": {"medido_na_referencia": round(p_bucket, 3),
                                        "ic95_wilson": wilson(pub["buckets_com_algum_sem_apoio"],
                                                              pub["buckets"]),
                                        "pela_taxa_por_bullet": round(p_bucket_binom, 3)},
             "opcoes": opcoes}
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "limpeza.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    (a.saida / "limpeza.md").write_text(md(saida), encoding="utf-8")
    print(md(saida))


def md(s: dict) -> str:
    r, p = s["referencia"], s["p_bucket_com_sem_apoio"]
    L = ["# Limpeza do treino com o juiz v2.2 congelado (ESTIMADO)", "",
         f"Juiz `config_sha256` {r['config_sha256'][:8]}…; {s['seg_por_par']:.0f} s/par.", "",
         "Posição do 1º par com apoio, na ordem de similaridade (referência, MEDIDO):", ""]
    for lado in ("publicado", "local"):
        x = r[lado]
        L.append(f"- {lado}: {x['posicao_1o_sim']} → {x['pares_parando_no_1o_sim']} de "
                 f"{x['pares_completo']} pares ({x['pares_por_bullet_1o_sim']} por bullet); "
                 f"parando no 2º sim (preserva o \"apoio ≥ 2\"): {x['pares_parando_no_2o_sim']}")
    t = s["treino"]
    L += ["", f"Treino: {t['filmes']} filmes, {t['bullets']} bullets, {t['exemplos']} exemplos "
          f"(buckets). Economia de parar no 1º sim: {100 * s['economia_parando_no_1o_sim']:.0f}% "
          "(lado publicado da referência).", "",
          f"Bucket com algum bullet sem apoio, na referência publicada: {p['medido_na_referencia']} "
          f"(IC95 Wilson {p['ic95_wilson']}; pela taxa por bullet, 1−(1−2/90)^6 = "
          f"{p['pela_taxa_por_bullet']}).", "",
          "| opção | horas de juiz | exemplos removidos (estimado) |", "|---|---|---|"]
    o = s["opcoes"]
    ft, fp = o["filtrar_tudo"], o["filtrar_parte_v4flash"]
    L.append(f"| filtrar tudo ({ft['filmes']} filmes) | {ft['horas_parando_no_1o_sim']} h parando no 1º sim "
             f"({ft['horas_juiz_completo']} h completo) | {ft['exemplos_removidos_estimados']} de {t['exemplos']} |")
    L.append(f"| filtrar parte: só V4-Flash ({fp['filmes']} filmes) | {fp['horas_parando_no_1o_sim']} h "
             f"({fp['horas_juiz_completo']} h completo) | {fp['exemplos_removidos_estimados']} |")
    L.append(f"| não filtrar | 0 h | 0 (≈ {o['nao_filtrar']['bullets_sem_apoio_esperados_no_treino']} "
             "bullets sem apoio ficam no alvo) |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
