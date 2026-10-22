"""O conjunto LIMPO de síntese: o que sobra do treino e da validação depois da
limpeza com o juiz v2.2 (`limpar_treino.py resumir`).

A unidade do exemplo é o BUCKET (filme × bucket). Fica no conjunto limpo todo
bucket de treino/validação do split que (a) é exemplo de síntese utilizável
(`inventario.json`) e (b) NÃO saiu na limpeza. O teste não é lido aqui.

Dois hashes, por definição escrita aqui (o que cada um prende):
- `sha256_ids`: dos identificadores, uma linha `conjunto|slug|bucket` por
  exemplo, em ordem — prende QUAIS exemplos ficaram;
- `sha256_conteudo` (só quando o conteúdo é dado): de uma linha
  `conjunto|slug|bucket|sha256(texto de chat)` por exemplo — prende também o
  PROMPT e o ALVO de cada um.

    python scripts/finetune/conjunto_limpo.py            # grava finetune/limpeza/conjunto_limpo.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def sha256_linhas(linhas: list[str]) -> str:
    return hashlib.sha256(("\n".join(linhas) + "\n").encode("utf-8")).hexdigest()


def calcular(split: dict, inventario: dict, resumo: dict) -> dict:
    """Puro: devolve o conjunto limpo e o que saiu, sem tocar em disco."""
    por_chave = {(b["slug"], b["bucket"]): b for b in resumo["buckets"]}
    pendentes = sorted(k for k, b in por_chave.items() if b["pendente"])
    if pendentes:
        raise ValueError(f"limpeza com bucket pendente: {pendentes[:5]}")
    excl = {(x["slug"], x["bucket"]) for x in split.get("buckets_excluidos", [])}
    conj_do_filme = {s: "treino" for s in split["treino"]}
    conj_do_filme.update({s: "validacao" for s in split["validacao"]})
    base = {c: [] for c in ("treino", "validacao")}
    for x in inventario["exemplos_sintese"]:
        slug, bucket = x["slug"], x["bucket"]
        if x["excluido"] or (slug, bucket) in excl or slug not in conj_do_filme:
            continue                     # teste, excluído ou fora do split
        base[conj_do_filme[slug]].append((slug, bucket))
    fora_do_resumo = sorted(k for c in base.values() for k in c if k not in por_chave)
    if fora_do_resumo:
        raise ValueError(f"exemplo do split sem veredito da limpeza: {fora_do_resumo[:5]}")
    fica, sai = {}, {}
    for c, itens in base.items():
        fica[c] = sorted(k for k in itens if not por_chave[k]["removido"])
        sai[c] = sorted(k for k in itens if por_chave[k]["removido"])
    return {"base": {c: len(v) for c, v in base.items()},
            "fica": fica, "sai": sai,
            "sha256_ids": sha256_linhas([f"{c}|{s}|{b}" for c in ("treino", "validacao")
                                         for s, b in fica[c]])}


def main() -> None:
    import _guarda  # noqa: F401  (só no uso como script: o import instala a guarda de rede)
    import comum as K

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--resumo", type=Path, default=K.FINETUNE_DIR / "limpeza" / "resumo.json")
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR / "limpeza" / "conjunto_limpo.json")
    a = ap.parse_args()
    r = calcular(K.ler_json(a.split), K.ler_json(a.inventario), K.ler_json(a.resumo))
    out = {"gerado_por": "scripts/finetune/conjunto_limpo.py",
           "juiz_config_sha256": K.ler_json(a.resumo)["juiz_config_sha256"],
           "split_sha256": K.sha256_arquivo(a.split),
           "resumo_sha256": K.sha256_arquivo(a.resumo),
           "n_base": r["base"],
           "n_treino": len(r["fica"]["treino"]), "n_validacao": len(r["fica"]["validacao"]),
           "n_removidos": {c: len(v) for c, v in r["sai"].items()},
           "sha256_ids": r["sha256_ids"],
           "treino": [f"{s}/{b}" for s, b in r["fica"]["treino"]],
           "validacao": [f"{s}/{b}" for s, b in r["fica"]["validacao"]],
           "removidos": {c: [f"{s}/{b}" for s, b in v] for c, v in r["sai"].items()}}
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("treino", "validacao", "removidos")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
