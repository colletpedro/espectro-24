"""Dataset do teste de fumaça do QWEN3-8B no Kaggle — só exemplos de TREINO do
conjunto LIMPO (depois da limpeza com o juiz v2.2), com os tokens do
tokenizer do Qwen3-8B.

Mesma regra de escolha de `montar_dataset_smoke.py` (decisão 6 do gate 0), só
que sobre os 141 exemplos que sobraram e em tokens do Qwen3-8B:
- `mais_longo`: o maior total que cabe em 14.336 — com o tokenizer do Qwen3
  (mais tokens por texto que o do Gemma) o `satantango/positivas` tem 15.414
  tokens e só o PROMPT dele (14.690) já passa de 14.336: truncado, o alvo
  inteiro cairia fora e o exemplo não teria token treinável. Ele fica fora do
  E1 por construção (é o outlier; a decisão é do dono) e vai listado em
  `meta.json`; o E1 mede, portanto, o maior que cabe;
- `mais_longo_12k`: o maior que cabe em 12.288 (o E1 cai para 12.288 se o
  anterior der OOM). Com este conjunto é o MESMO exemplo do `mais_longo`;
- `mediano_1..4`: os 4 mais próximos da mediana do conjunto limpo, fora os
  anteriores.

Confere, antes de gravar: nenhum filme de teste/validação/excluído; nenhum
alvo com bloco de raciocínio (`<think>`); o conjunto limpo bate com
`conjunto_limpo.json` (hash dos ids).

Saída: `<saida>/smoke.jsonl`, `smoke.sha256`, `dataset-metadata.json`
(`USUARIO` no lugar do usuário do Kaggle) e `meta.json` — que o kernel lê:
`candidatos` (só o Qwen3-8B), o nº REAL de exemplos de treino depois da
limpeza (E3) e os hashes do conjunto.
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
import conjunto_limpo as CL  # noqa: E402

TOKENIZER = "Qwen3-8B"
LIMITES = {"mais_longo": 14336, "mais_longo_12k": 12288}
SLUG_DATASET = "espectro24-finetune-smoke-qwen3-dados"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--resumo", type=Path, default=K.FINETUNE_DIR / "limpeza" / "resumo.json")
    ap.add_argument("--conjunto", type=Path, default=K.FINETUNE_DIR / "limpeza" / "conjunto_limpo.json")
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--saida", type=Path,
                    default=K.FINETUNE_DIR / "kaggle" / "smoke_dataset_qwen3")
    a = ap.parse_args()

    split = K.ler_json(a.split)
    limpo = CL.calcular(split, K.ler_json(a.inventario), K.ler_json(a.resumo))
    gravado = K.ler_json(a.conjunto)
    if gravado["sha256_ids"] != limpo["sha256_ids"]:
        raise SystemExit("conjunto_limpo.json não bate com split + inventário + resumo: "
                         "rode conjunto_limpo.py")
    treino = limpo["fica"]["treino"]
    proibidos = set(split["teste"]) | set(split["validacao"]) | set(K.EXCLUIR_FILMES)
    assert all(s in split["treino"] and s not in proibidos for s, _ in treino)

    tok = K.carregar_tokenizer(TOKENIZER, a.tokenizers)
    exemplos = []
    for slug, bucket in treino:
        pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        b = {y.nome: y for y in K.buckets_remontados(slug, pub)}[bucket]
        bp = next(y for y in pub["buckets"] if y["bucket"] == bucket)
        s, u = K.prompt_sintese(b)
        alvo = K.serializar_alvo(K.alvo_publicado(bp))
        if "<think>" in alvo or "</think>" in alvo:
            raise SystemExit(f"{slug}/{bucket}: o alvo traz bloco de raciocínio")
        entrada = K.contar(tok, K.chat("qwen", s, u, None))
        total = K.contar(tok, K.chat("qwen", s, u, alvo))
        exemplos.append({"slug": slug, "bucket": bucket, "s": s, "u": u, "alvo": alvo,
                         "tokens": {"entrada": entrada, "saida": total - entrada,
                                    "total": total}})
    tot = lambda x: x["tokens"]["total"]  # noqa: E731

    escolha = {}
    for papel, lim in LIMITES.items():
        escolha[papel] = max((x for x in exemplos if tot(x) <= lim), key=tot)
    usados = {(x["slug"], x["bucket"]) for x in escolha.values()}
    med = statistics.median(tot(x) for x in exemplos)
    resto = sorted((x for x in exemplos if (x["slug"], x["bucket"]) not in usados),
                   key=lambda x: (abs(tot(x) - med), x["slug"], x["bucket"]))
    for i, x in enumerate(resto[:4], 1):
        escolha[f"mediano_{i}"] = x

    linhas = []
    for papel, x in escolha.items():
        esperado = K.chat("qwen", x["s"], x["u"], x["alvo"])
        linhas.append({"papel": papel, "slug": x["slug"], "bucket": x["bucket"],
                       "conjunto": "treino",
                       "messages": [{"role": "system", "content": x["s"]},
                                    {"role": "user", "content": x["u"]},
                                    {"role": "assistant", "content": x["alvo"]}],
                       "tokens": {TOKENIZER: x["tokens"]},
                       "chat_esperado": {"qwen": esperado},
                       "chat_esperado_sha256": {"qwen": K.sha256_texto(esperado)}})
    a.saida.mkdir(parents=True, exist_ok=True)
    arq = a.saida / "smoke.jsonl"
    arq.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas),
                   encoding="utf-8")
    sha = K.sha256_arquivo(arq)
    (a.saida / "smoke.sha256").write_text(f"{sha}  smoke.jsonl\n", encoding="utf-8")
    (a.saida / "dataset-metadata.json").write_text(json.dumps(
        {"title": "espectro24 finetune smoke qwen3 (privado)",
         "id": f"USUARIO/{SLUG_DATASET}", "licenses": [{"name": "other"}]},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    conteudo = K.sha256_texto("\n".join(
        f"treino|{x['slug']}|{x['bucket']}|{K.sha256_texto(K.chat('qwen', x['s'], x['u'], x['alvo']))}"
        for x in exemplos) + "\n")
    meta = {"candidatos": ["qwen3-8b"], "tokenizer": TOKENIZER,
            "tokenizer_repo": K.CANDIDATOS_EXTRA[TOKENIZER]["repo"],
            "tokenizer_revisao": K.CANDIDATOS_EXTRA[TOKENIZER]["revisao"],
            "n_treino_limpo": len(treino), "n_validacao_limpo": len(limpo["fica"]["validacao"]),
            "n_treino_antes_da_limpeza": limpo["base"]["treino"],
            "epocas_E3": 3, "sha256_ids_conjunto_limpo": limpo["sha256_ids"],
            "sha256_conteudo_treino_limpo": conteudo,
            "tokens_total_qwen3_8b": K.quantis([tot(x) for x in exemplos]),
            "mediana_total": med, "smoke_sha256": sha,
            # exemplos que NÃO cabem nos cortes (o tokenizer do Qwen3 gera mais
            # tokens que o do Gemma): ficam fora do E1; a decisão é do dono
            "acima_de_14336": sorted(
                f"{x['slug']}/{x['bucket']}:{tot(x)} (prompt {x['tokens']['entrada']})"
                for x in exemplos if tot(x) > 14336),
            "acima_de_12288": sorted(f"{x['slug']}/{x['bucket']}:{tot(x)}"
                                     for x in exemplos if tot(x) > 12288)}
    (a.saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    for l in linhas:
        print(f"{l['papel']:15s} {l['slug']}/{l['bucket']}  total {TOKENIZER} "
              f"{l['tokens'][TOKENIZER]['total']}")
    print(json.dumps({k: v for k, v in meta.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
