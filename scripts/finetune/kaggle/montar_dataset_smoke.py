"""Monta o dataset MÍNIMO do teste de fumaça no Kaggle — só exemplos de TREINO.

Escolhe, entre os exemplos de síntese dos filmes de treino de `split.json`
(fora os buckets excluídos):
- `mais_longo`: o maior total de tokens (Gemma 4) que cabe em 14.336;
- `mais_longo_12k`: o maior que cabe em 12.288 (o E1 cai para 12.288 se
  14.336 der OOM; nesse corte os 2 maiores saem — decisão 6 do gate 0);
- `mediano_1..4`: os 4 mais próximos da mediana do total, fora os anteriores.

Cada linha do JSONL traz as mensagens (system, user, assistant = alvo
publicado, indentado com 2 espaços) e o texto de chat ESPERADO por família
(`comum.chat`, raciocínio desligado), para o Kaggle conferir contra o
`apply_chat_template` do Unsloth. Há assert explícito contra o split.

Saída: `<saida>/smoke.jsonl`, `<saida>/smoke.sha256`, `<saida>/dataset-metadata.json`
(com `USUARIO` no lugar do usuário do Kaggle).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

TOKENIZER = "Gemma-4-E4B"        # = o do 12B (mesmo tokenizer.json)
LIMITES = {"mais_longo": 14336, "mais_longo_12k": 12288}
SLUG_DATASET = "espectro24-finetune-smoke-dados"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR / "kaggle" / "smoke_dataset")
    a = ap.parse_args()

    split, inv = K.ler_json(a.split), K.ler_json(a.inventario)
    treino = set(split["treino"])
    proibidos = set(split["teste"]) | set(split["validacao"]) | set(K.EXCLUIR_FILMES)
    excl = {(x["slug"], x["bucket"]) for x in split.get("buckets_excluidos", [])}
    cand = [x for x in inv["exemplos_sintese"]
            if x["slug"] in treino and not x["excluido"] and (x["slug"], x["bucket"]) not in excl]
    tot = lambda x: x["tokens"][TOKENIZER]["total"]  # noqa: E731

    escolha = {}
    for papel, lim in LIMITES.items():
        escolha[papel] = max((x for x in cand if tot(x) <= lim), key=tot)
    usados = {(x["slug"], x["bucket"]) for x in escolha.values()}
    med = statistics.median(tot(x) for x in cand)
    resto = sorted((x for x in cand if (x["slug"], x["bucket"]) not in usados),
                   key=lambda x: (abs(tot(x) - med), x["slug"], x["bucket"]))
    for i, x in enumerate(resto[:4], 1):
        escolha[f"mediano_{i}"] = x

    toks = K.carregar_tokenizers(a.tokenizers)
    linhas = []
    for papel, x in escolha.items():
        slug, bucket = x["slug"], x["bucket"]
        assert slug in treino and slug not in proibidos, f"{slug} não é de treino"
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        b = {y.nome: y for y in K.buckets_remontados(slug, pub)}[bucket]
        bp = next(y for y in pub["buckets"] if y["bucket"] == bucket)
        s, u = K.prompt_sintese(b)
        alvo = K.serializar_alvo(K.alvo_publicado(bp))
        esperado = {"gemma": K.chat("gemma", s, u, alvo), "qwen": K.chat("qwen", s, u, alvo)}
        linhas.append({"papel": papel, "slug": slug, "bucket": bucket, "conjunto": "treino",
                       "messages": [{"role": "system", "content": s},
                                    {"role": "user", "content": u},
                                    {"role": "assistant", "content": alvo}],
                       "tokens": K.tokens_do_par(toks, s, u, alvo),
                       "chat_esperado": esperado,
                       "chat_esperado_sha256": {f: K.sha256_texto(t) for f, t in esperado.items()}})
    a.saida.mkdir(parents=True, exist_ok=True)
    arq = a.saida / "smoke.jsonl"
    arq.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas),
                   encoding="utf-8")
    sha = K.sha256_arquivo(arq)
    (a.saida / "smoke.sha256").write_text(f"{sha}  smoke.jsonl\n", encoding="utf-8")
    (a.saida / "dataset-metadata.json").write_text(json.dumps(
        {"title": "espectro24 finetune smoke (privado)", "id": f"USUARIO/{SLUG_DATASET}",
         "licenses": [{"name": "other"}]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for l in linhas:
        print(f"{l['papel']:15s} {l['slug']}/{l['bucket']}  total Gemma "
              f"{l['tokens'][TOKENIZER]['total']}")
    print(f"mediana do treino: {med} · sha256 smoke.jsonl: {sha}")


if __name__ == "__main__":
    main()
