"""Dataset do TREINO do Qwen3-8B no Kaggle (Fase 3) — `finetune/TREINO_CONFIG.md`.

Os exemplos são os do conjunto LIMPO (`conjunto_limpo.json`): 140 de TREINO
(o `satantango/positivas` fora por comprimento) e 19 de VALIDAÇÃO. Para cada um:
o prompt atual da síntese sobre o bucket remontado do bruto, o alvo publicado
(`comum.serializar_alvo`) e o `chat_esperado` pelo `comum.chat` corrigido (sem
aparar), com os tokens do tokenizer do Qwen3-8B.

Confere, antes de gravar:
- o conjunto limpo bate com split + inventário + resumo (hash dos ids);
- nenhum filme de TESTE nem excluído; cada exemplo no conjunto do seu filme;
- nenhum alvo com bloco de raciocínio;
- nenhum exemplo acima de `MAX_SEQ` (12.288) tokens: o kernel não trunca.

Saída (`--saida`): `treino.jsonl` (o sha256 dele é o "sha do dataset" do
TREINO_CONFIG), `treino.sha256`, `dataset-metadata.json` (`USUARIO` no lugar do
usuário) e `meta.json`. O `meta.json` leva também, com `--log-kernel-base`, o
commit do llama.cpp e o sha256 do GGUF da BASE (o kernel de treino clona o
llama.cpp NESSE commit e aborta sem ele) e o `tensores.json` da base, copiado
ao lado (para conferir que só as 7 projeções mudaram).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import conjunto_limpo as CL  # noqa: E402

TOKENIZER = "Qwen3-8B"
MAX_SEQ = 12288
SLUG_DATASET = "espectro24-finetune-treino-qwen3-dados"


def exemplos(split: dict, limpo: dict, tok) -> list[dict]:
    proibidos = set(split["teste"]) | set(K.EXCLUIR_FILMES)
    fora = []
    for conjunto in ("treino", "validacao"):
        for slug, bucket in limpo["fica"][conjunto]:
            if slug in proibidos or slug not in split[conjunto]:
                raise SystemExit(f"{slug}/{bucket}: fora do conjunto {conjunto} (ou de teste)")
            pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
            b = {y.nome: y for y in K.buckets_remontados(slug, pub)}[bucket]
            bp = next(y for y in pub["buckets"] if y["bucket"] == bucket)
            s, u = K.prompt_sintese(b)
            alvo = K.serializar_alvo(K.alvo_publicado(bp))
            if "<think>" in alvo or "</think>" in alvo:
                raise SystemExit(f"{slug}/{bucket}: o alvo traz bloco de raciocínio")
            esperado = K.chat("qwen", s, u, alvo)
            entrada = K.contar(tok, K.chat("qwen", s, u, None))
            total = K.contar(tok, esperado)
            if total > MAX_SEQ:
                raise SystemExit(f"{slug}/{bucket}: {total} tokens > max_seq_length {MAX_SEQ}")
            fora.append({"conjunto": conjunto, "slug": slug, "bucket": bucket,
                         "messages": [{"role": "system", "content": s},
                                      {"role": "user", "content": u},
                                      {"role": "assistant", "content": alvo}],
                         "tokens": {TOKENIZER: {"entrada": entrada, "saida": total - entrada,
                                                "total": total}},
                         "chat_esperado": {"qwen": esperado},
                         "chat_esperado_sha256": {"qwen": K.sha256_texto(esperado)}})
    return fora


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--resumo", type=Path, default=K.FINETUNE_DIR / "limpeza" / "resumo.json")
    ap.add_argument("--conjunto", type=Path, default=K.FINETUNE_DIR / "limpeza" / "conjunto_limpo.json")
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    ap.add_argument("--log-kernel-base", type=Path,
                    help="log.json do kernel exportar_base (commit do llama.cpp e GGUF da base)")
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR / "kaggle" / "treino_dataset_qwen3")
    a = ap.parse_args()

    split = K.ler_json(a.split)
    limpo = CL.calcular(split, K.ler_json(a.inventario), K.ler_json(a.resumo))
    if K.ler_json(a.conjunto)["sha256_ids"] != limpo["sha256_ids"]:
        raise SystemExit("conjunto_limpo.json não bate com split + inventário + resumo")
    tok = K.carregar_tokenizer(TOKENIZER, a.tokenizers)
    linhas = exemplos(split, limpo, tok)
    a.saida.mkdir(parents=True, exist_ok=True)
    arq = a.saida / "treino.jsonl"
    arq.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas), encoding="utf-8")
    sha = K.sha256_arquivo(arq)
    (a.saida / "treino.sha256").write_text(f"{sha}  treino.jsonl\n", encoding="utf-8")
    (a.saida / "dataset-metadata.json").write_text(json.dumps(
        {"title": "espectro24 finetune treino qwen3 (privado)", "id": f"USUARIO/{SLUG_DATASET}",
         "licenses": [{"name": "other"}]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tot = [l["tokens"][TOKENIZER]["total"] for l in linhas]
    meta = {"gerado_por": "scripts/finetune/kaggle/montar_dataset_treino.py",
            "tokenizer": TOKENIZER, "tokenizer_repo": K.CANDIDATOS_EXTRA[TOKENIZER]["repo"],
            "tokenizer_revisao": K.CANDIDATOS_EXTRA[TOKENIZER]["revisao"],
            "max_seq_length": MAX_SEQ, "treino_sha256": sha,
            "n_treino": sum(l["conjunto"] == "treino" for l in linhas),
            "n_validacao": sum(l["conjunto"] == "validacao" for l in linhas),
            "sha256_ids_conjunto_limpo": limpo["sha256_ids"],
            "fora_por_comprimento": limpo["motivo_comprimento"],
            "split_sha256": K.sha256_arquivo(a.split),
            "filmes": {"treino": sorted(split["treino"]), "validacao": sorted(split["validacao"]),
                       "teste": sorted(split["teste"])},
            "tokens_total_qwen3_8b": K.quantis(tot),
            "tokens_validacao": K.quantis([l["tokens"][TOKENIZER]["total"] for l in linhas
                                           if l["conjunto"] == "validacao"]),
            "llama_cpp_commit": None, "base": None}
    if a.log_kernel_base:
        log = K.ler_json(a.log_kernel_base)
        commit = (log.get("llama_cpp") or {}).get("commit")
        g = [x for x in log.get("gguf_arquivos") or [] if x["nome"].endswith(".gguf")]
        if not commit or len(g) != 1 or not log.get("gguf_ok"):
            raise SystemExit("o log da base não tem llama.cpp, GGUF único e gguf_ok")
        meta["llama_cpp_commit"] = commit
        meta["base"] = {"log_sha256": K.sha256_arquivo(a.log_kernel_base), "gguf_sha256": g[0]["sha256"],
                        "unsloth": (log.get("versoes") or {}).get("unsloth"),
                        "repo_revisao": (log.get("repo_confirmado") or {}).get("sha")}
        tens = a.log_kernel_base.with_name("tensores.json")
        if tens.exists():
            shutil.copy2(tens, a.saida / "tensores_base.json")
            meta["base"]["tensores_sha256"] = K.sha256_arquivo(a.saida / "tensores_base.json")
    (a.saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "filmes"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
