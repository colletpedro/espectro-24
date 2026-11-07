"""Confere a saída de um smoke do Kaggle contra os exemplos do dataset que DEVERIA
ter sido lido (preparado para a versão 4 do kernel do Qwen3-8B, cujo dataset é
`smoke_dataset_qwen3/smoke.jsonl`, sha256 `ae74737d…`, 140 exemplos de treino).

Motivo: as versões 2 e 3 do kernel rodaram antes de o dataset ser versionado no
Kaggle, sobre uma versão antiga que não se pôde verificar (FINETUNE_REGISTRO.md).
Esta conferência prova, pelos LOGS, que a rodada treinou os exemplos certos.

O que confere (tudo MEDIDO do que o kernel gravou; nada é inferido):
1. o `smoke.jsonl` local tem o sha256 esperado e é o do `meta.json` local;
2. `resumo.json`: o `meta_dataset.smoke_sha256` que o kernel leu do Kaggle é o
   esperado; se houver `dataset.sha256_lido` (kernel de 2026-10-30 em diante),
   o sha do arquivo LIDO também;
3. em cada execução com `log.json`:
   - `template_confere` cobre exatamente os 6 papéis do dataset, todos `igual`
     (o texto renderizado no Kaggle é o `chat_esperado` de cada exemplo: isso
     identifica o conteúdo dos 6, inclusive dos medianos 2–4);
   - `longo`: slug, bucket e papel batem com o exemplo do papel; `tokens_entrada`
     = `tokens.total` e `tokens_treinados` = `tokens.saida` (a saída de
     `comum.tokens_do_par` já inclui o fim de turno, que a máscara treina);
   - `mediano`: o 1º lote é o `mediano_1`; a mesma igualdade de tokens.
   O log só grava a contagem de tokens do 1º lote de cada treino: os medianos
   2–4 ficam conferidos pelo texto (item acima), não por contagem.

Igualdade EXATA; nenhuma tolerância. Uma divergência é reportada com os dois
números, e o código de saída é 1.

Revisão de 2026-10-30, depois da v4 e por decisão do dono: o `chat_esperado` e
o `tokens` gravados no dataset vieram de um `comum.chat` que APARAVA o
conteúdo do usuário, e o template do Qwen3 não apara. O texto esperado passa a
ser REMONTADO dos `messages` pelo `comum.chat` corrigido, e os tokens são
recontados com o tokenizer do Qwen3-8B:
- entrada = tokens do exemplo inteiro (o template termina em `<|im_end|>\n`);
- treinados = tokens de `alvo + <|im_end|>`: a máscara treina a resposta e o fim
  de turno, não o `\n` depois dele.
A comparação com os campos gravados continua no relatório como INFORMATIVA
(`conta: false`), sem entrar no código de saída. Quando `template_confere` não
deu `igual`, o log só guarda o comprimento e a janela de 160 caracteres em
volta da 1ª diferença: a conferência exige que os dois batam com o texto
remontado, e a contagem de tokens cobre o exemplo inteiro.

Uso:
    python scripts/finetune/kaggle/conferir_saida_smoke.py --saida <pasta baixada>
        [--dataset finetune/kaggle/smoke_dataset_qwen3] [--sha ae74737d…]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comum as K  # noqa: E402

SHA_V4 = "ae74737defb435017b763f11e13e0f82bdf5bcdc1f136f2366d2765cd81ac14f"
TOKENIZER = "Qwen3-8B"


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _item(nome: str, ok: bool, **det) -> dict:
    return {"conferencia": nome, "ok": bool(ok), **det}


def _informativo(nome: str, ok: bool, **det) -> dict:
    return {**_item(nome, ok, **det), "conta": False}


def remontar(linha: dict, tok) -> dict:
    """Texto e tokens do exemplo pelo template real do Qwen3 (`comum.chat`)."""
    s, u, a = (m["content"] for m in linha["messages"])
    texto = K.chat("qwen", s, u, a)
    return {"texto": texto, "total": K.contar(tok, texto),
            "treinados": K.contar(tok, a + "<|im_end|>")}


def _texto_confere(tc: dict, texto: str, gravado: str) -> bool:
    """`igual` no log = o Kaggle renderizou o `chat_esperado` gravado; senão, o
    comprimento e a janela da 1ª diferença têm de bater com o texto remontado."""
    if tc.get("igual"):
        return gravado.removeprefix("<bos>") == texto
    i = tc.get("posicao")
    return (i is not None and tc.get("len_obtido") == len(texto)
            and tc.get("obtido") == texto[max(0, i - 80):i + 80])


def conferir(saida: Path, dataset: Path, sha: str, tok) -> list[dict]:
    fora = []
    arq = dataset / "smoke.jsonl"
    meta = json.loads((dataset / "meta.json").read_text(encoding="utf-8"))
    lido = _sha256(arq)
    fora.append(_item("dataset local = sha esperado = meta.json", lido == sha == meta.get("smoke_sha256"),
                      sha256_local=lido, esperado=sha, meta=meta.get("smoke_sha256")))
    linhas = [json.loads(l) for l in arq.read_text(encoding="utf-8").split("\n") if l.strip()]
    por_papel = {l["papel"]: l for l in linhas}
    real = {p: remontar(l, tok) for p, l in por_papel.items()}

    resumo_p = saida / "resumo.json"
    if not resumo_p.exists():
        return fora + [_item("resumo.json presente", False, caminho=str(resumo_p))]
    resumo = json.loads(resumo_p.read_text(encoding="utf-8"))
    sha_meta_kaggle = (resumo.get("meta_dataset") or {}).get("smoke_sha256")
    fora.append(_item("resumo.meta_dataset.smoke_sha256 = esperado", sha_meta_kaggle == sha,
                      lido_no_kaggle=sha_meta_kaggle))
    if "dataset" in resumo:
        fora.append(_item("resumo.dataset.sha256_lido = esperado",
                          resumo["dataset"].get("sha256_lido") == sha,
                          lido_no_kaggle=resumo["dataset"].get("sha256_lido")))
    else:
        fora.append(_item("resumo.dataset (sha do arquivo lido)", True,
                          nota="ausente: kernel anterior a 2026-10-30; vale só o meta_dataset"))

    execucoes = [e for e in resumo.get("execucoes", []) if e.get("pasta")]
    if not execucoes:
        fora.append(_item("execuções com pasta", False, execucoes=len(resumo.get("execucoes", []))))
    for ex in execucoes:
        log_p = saida / ex["pasta"] / "log.json"
        rot = ex["pasta"]
        if not log_p.exists():
            fora.append(_item(f"{rot}: log.json presente", False))
            continue
        log = json.loads(log_p.read_text(encoding="utf-8"))
        if "dataset" in log:
            fora.append(_item(f"{rot}: log.dataset.sha256_lido = esperado",
                              log["dataset"].get("sha256_lido") == sha,
                              lido_no_kaggle=log["dataset"].get("sha256_lido")))
        tc = log.get("template_confere") or {}
        fora.append(_informativo(
            f"{rot}: template_confere = chat_esperado gravado, nos {len(por_papel)} papéis",
            set(tc) == set(por_papel) and all(v.get("igual") for v in tc.values()),
            diferentes=sorted(k for k, v in tc.items() if not v.get("igual"))))
        fora.append(_item(
            f"{rot}: texto do Kaggle = texto remontado pelo template real, nos {len(por_papel)} papéis",
            set(tc) == set(por_papel)
            and all(_texto_confere(tc[p], real[p]["texto"], por_papel[p]["chat_esperado"]["qwen"])
                    for p in por_papel),
            papeis_log=sorted(tc), papeis_dataset=sorted(por_papel),
            por_papel={p: {"len_log": tc.get(p, {}).get("len_obtido"),
                           "len_remontado": len(real[p]["texto"]),
                           "confere": p in tc and _texto_confere(
                               tc[p], real[p]["texto"], por_papel[p]["chat_esperado"]["qwen"])}
                       for p in por_papel}))
        lg = log.get("longo")
        if lg:
            x = por_papel.get(lg.get("papel"))
            if x is None:
                fora.append(_item(f"{rot}: longo.papel existe no dataset", False, papel=lg.get("papel")))
            else:
                t, r = x["tokens"][TOKENIZER], real[x["papel"]]
                fora.append(_item(f"{rot}: longo = {x['papel']} ({x['slug']}/{x['bucket']})",
                                  (lg.get("slug"), lg.get("bucket")) == (x["slug"], x["bucket"])
                                  and lg.get("tokens_entrada") == r["total"]
                                  and lg.get("tokens_treinados") == r["treinados"],
                                  slug_bucket_log=f"{lg.get('slug')}/{lg.get('bucket')}",
                                  tokens_entrada=[lg.get("tokens_entrada"), r["total"]],
                                  tokens_treinados=[lg.get("tokens_treinados"), r["treinados"]]))
                fora.append(_informativo(f"{rot}: longo = tokens gravados no dataset",
                                         lg.get("tokens_entrada") == t["total"]
                                         and lg.get("tokens_treinados") == t["saida"],
                                         tokens_entrada=[lg.get("tokens_entrada"), t["total"]],
                                         tokens_treinados=[lg.get("tokens_treinados"), t["saida"]]))
        else:
            fora.append(_item(f"{rot}: longo no log", False, erro=log.get("erro")))
        md = log.get("mediano")
        if md:
            t, r = por_papel["mediano_1"]["tokens"][TOKENIZER], real["mediano_1"]
            fora.append(_item(f"{rot}: mediano (1º lote = mediano_1)",
                              md.get("tokens_entrada") == r["total"]
                              and md.get("tokens_treinados") == r["treinados"],
                              tokens_entrada=[md.get("tokens_entrada"), r["total"]],
                              tokens_treinados=[md.get("tokens_treinados"), r["treinados"]]))
            fora.append(_informativo(f"{rot}: mediano = tokens gravados no dataset",
                                     md.get("tokens_entrada") == t["total"]
                                     and md.get("tokens_treinados") == t["saida"],
                                     tokens_entrada=[md.get("tokens_entrada"), t["total"]],
                                     tokens_treinados=[md.get("tokens_treinados"), t["saida"]]))
        else:
            fora.append(_item(f"{rot}: mediano no log", False, erro=log.get("erro")))
    return fora


def main() -> None:
    raiz = Path(__file__).resolve().parents[3]
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, required=True,
                    help="pasta baixada do kernel (a que tem resumo.json)")
    ap.add_argument("--dataset", type=Path,
                    default=raiz / "finetune" / "kaggle" / "smoke_dataset_qwen3")
    ap.add_argument("--sha", default=SHA_V4)
    ap.add_argument("--tokenizers", type=Path, default=K.TOKENIZERS_DIR_PADRAO)
    a = ap.parse_args()
    itens = conferir(a.saida, a.dataset, a.sha, K.carregar_tokenizer(TOKENIZER, a.tokenizers))
    contam = [i for i in itens if i.get("conta", True)]
    print(json.dumps({"todas_ok": all(i["ok"] for i in contam), "itens": itens},
                     ensure_ascii=False, indent=1))
    sys.exit(0 if all(i["ok"] for i in contam) else 1)


if __name__ == "__main__":
    main()
