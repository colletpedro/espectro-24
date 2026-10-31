"""Treino do Qwen3-8B (Fase 3) — a configuração de `finetune/TREINO_CONFIG.md`.

Idêntico ao smoke v4 onde se aplica (pilha, repositório e revisão, carga 4-bit
fp16, `get_peft_model`, template, perda só na resposta, exportação), mais:

- dados: `treino.jsonl` do dataset privado (140 de TREINO + 19 de VALIDAÇÃO).
  Aborta, antes de instalar ou treinar, se: o sha256 lido ≠ `meta.json` ≠
  `DATASET_SHA256` (o do TREINO_CONFIG); faltar o commit do llama.cpp da base
  no `meta.json`; algum exemplo for de filme fora do seu conjunto (ou de
  teste). Depois de carregar: aborta se `template_confere` for falso em
  QUALQUER exemplo ou se algum passar de `max_seq_length` (sem truncar);
- QLoRA 4-bit, r 16, alpha 16, dropout 0, as 7 projeções, gradient
  checkpointing "unsloth", fp16, seed 3407, `max_seq_length` 12.288;
  lr 2e-4, cosine, warmup 5%, 3 épocas, batch 1 × acumulação 4, adamw_8bit,
  weight decay 0 (os do smoke);
- perda na VALIDAÇÃO ao fim de cada época; checkpoint de cada época em
  `/kaggle/working/treino/checkpoints` (com o estado do otimizador: retoma,
  inclusive de uma saída anterior anexada como entrada do kernel);
- escolha: menor perda na validação (arredondada na 4ª casa); empate → menos
  épocas. A curva completa vai para `curva.json`. Nenhuma busca de
  hiperparâmetros;
- exportação: SÓ o checkpoint escolhido (o adaptador dele é carregado e a
  perda na validação é refeita e conferida), adaptador salvo, depois o MESMO
  `save_pretrained_gguf(..., "q4_k_m")` da base, com o llama.cpp clonado e
  compilado ANTES no commit da base (`meta.json`). Se o commit usado não for o
  da base, o GGUF NÃO é copiado para a saída (o adaptador fica). Com o
  `tensores_base.json` do dataset, confere que só os tensores das 7 projeções
  mudaram.

Saída (`/kaggle/working/treino/qwen3-8b-treinado__12288/`):
`Qwen3-8B.Q4_K_M.gguf`, `Modelfile`, `log.json` (`modelo` qwen3-8b-treinado →
`espectro-qwen3-8b-treinado` no `importar-pasta`), `curva.json`,
`tensores.json`, `adaptador_escolhido/`.
"""
from __future__ import annotations

import os

SCRIPT = os.path.abspath(__file__)        # antes do chdir abaixo
RASCUNHO = "/tmp/espectro24_treino"
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("HF_HOME", f"{RASCUNHO}/hf")
os.environ.setdefault("HF_HUB_CACHE", f"{RASCUNHO}/hf/hub")
os.environ.setdefault("TRITON_CACHE_DIR", f"{RASCUNHO}/triton")
os.makedirs(RASCUNHO, exist_ok=True)
os.chdir(RASCUNHO)            # llama.cpp e unsloth_compiled_cache nascem no cwd

import argparse
import glob
import hashlib
import json
import math
import platform
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

NOME = "qwen3-8b-treinado"
SEQ = 12288
RAIZ_SAIDA = Path("/kaggle/working/treino")
SAIDA = RAIZ_SAIDA / f"{NOME}__{SEQ}"
CHECKPOINTS = RAIZ_SAIDA / "checkpoints"
TMP = Path(RASCUNHO)
ENTRADA_GLOB = "/kaggle/input/**/treino.jsonl"
# sha256 do `treino.jsonl` (TREINO_CONFIG.md); o kernel não treina outro arquivo
DATASET_SHA256 = "36f81ac1a48d11bdc1b7f1fc27e71fb3dd54ca063b29caa862ff4459ee45e53d"
N_TREINO, N_VALIDACAO = 140, 19
REPO = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
REVISAO = "62efd7f9d748e394734a7adae2adf96e13a2abc8"     # a do smoke v4 e da base
PACOTES_FIXOS = ["unsloth==2026.10.7", "unsloth_zoo==2026.10.7"]
PROJECOES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
# os nomes das 7 projeções no GGUF (llama.cpp): o resto tem de sair igual ao da base
PROJECOES_GGUF = ("attn_q.", "attn_k.", "attn_v.", "attn_output.", "ffn_gate.", "ffn_up.",
                  "ffn_down.")
PARTES = ("<|im_start|>user\n", "<|im_start|>assistant\n<think>\n\n</think>\n\n")
HIPER = {"seed": 3407, "r": 16, "lora_alpha": 16, "lora_dropout": 0, "learning_rate": 2e-4,
         "lr_scheduler_type": "cosine", "warmup_ratio": 0.05, "num_train_epochs": 3,
         "per_device_train_batch_size": 1, "gradient_accumulation_steps": 4,
         "optim": "adamw_8bit", "weight_decay": 0.0, "fp16": True, "bf16": False,
         "max_seq_length": SEQ, "use_gradient_checkpointing": "unsloth"}
CASAS_EMPATE = 4
TOL_REAVALIACAO = 1e-3
LLAMA_CPP_URL = "https://github.com/ggml-org/llama.cpp"
ALVOS_LLAMA = ["llama-quantize", "llama-cli", "llama-gguf-split"]


def _json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1, default=str))
        f.flush()
        os.fsync(f.fileno())


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    return h.hexdigest()


def _rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def _versoes() -> dict:
    import importlib.metadata as md
    v = {"python": platform.python_version()}
    for pkg in ("unsloth", "unsloth_zoo", "transformers", "trl", "torch", "peft",
                "bitsandbytes", "accelerate", "datasets", "safetensors", "huggingface_hub"):
        try:
            v[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            v[pkg] = None
    v["imagem_kaggle"] = os.environ.get("KAGGLE_DOCKER_IMAGE") or os.environ.get("KAGGLE_IMAGE")
    return v


# ---------------------------------------------------------------------------
# dataset (conferido ANTES de instalar ou treinar)
# ---------------------------------------------------------------------------

def _arquivo_dataset() -> Path:
    achados = glob.glob(ENTRADA_GLOB, recursive=True)
    if len(achados) != 1:
        raise SystemExit(f"esperava 1 treino.jsonl em /kaggle/input, achei {achados}")
    return Path(achados[0])


def conferir_dataset() -> tuple[list[dict], dict, dict]:
    arq = _arquivo_dataset()
    meta = json.loads(arq.with_name("meta.json").read_text(encoding="utf-8"))
    lido = _sha256(arq)
    conf = {"arquivo": str(arq), "sha256_lido": lido, "sha256_meta": meta.get("treino_sha256"),
            "sha256_config": DATASET_SHA256}
    print(f"[dataset] treino.jsonl {lido} / meta {conf['sha256_meta']} / config {DATASET_SHA256}",
          flush=True)
    if not (lido == conf["sha256_meta"] == DATASET_SHA256):
        raise SystemExit("treino.jsonl não é o do meta.json e do TREINO_CONFIG — abortado")
    if not meta.get("llama_cpp_commit"):
        raise SystemExit("meta.json sem o commit do llama.cpp da base (`--log-kernel-base`) — abortado")
    linhas = [json.loads(l) for l in arq.read_text(encoding="utf-8").split("\n") if l.strip()]
    filmes = meta["filmes"]
    teste = set(filmes["teste"])
    for l in linhas:
        c = l.get("conjunto")
        if c not in ("treino", "validacao") or l["slug"] not in set(filmes[c]) or l["slug"] in teste:
            raise SystemExit(f"{l['slug']}/{l['bucket']}: filme fora de treino/validação — abortado")
    n = {c: sum(l["conjunto"] == c for l in linhas) for c in ("treino", "validacao")}
    if (n["treino"], n["validacao"]) != (N_TREINO, N_VALIDACAO):
        raise SystemExit(f"{n} exemplos (esperados {N_TREINO} + {N_VALIDACAO}) — abortado")
    conf["n"] = n
    return linhas, meta, conf


# ---------------------------------------------------------------------------
# llama.cpp no commit da base
# ---------------------------------------------------------------------------

def preparar_llama_cpp(commit: str) -> dict:
    """Clona o llama.cpp NO commit da base e compila o que a exportação usa, ANTES
    do `save_pretrained_gguf` (que acha a pasta no cwd e não clona de novo)."""
    d = TMP / "llama.cpp"
    shutil.rmtree(d, ignore_errors=True)
    t0 = time.time()
    passos = [["git", "init", str(d)],
              ["git", "-C", str(d), "remote", "add", "origin", LLAMA_CPP_URL],
              ["git", "-C", str(d), "fetch", "--depth", "1", "origin", commit],
              ["git", "-C", str(d), "checkout", "--detach", "FETCH_HEAD"],
              ["cmake", "-S", str(d), "-B", str(d / "build"), "-DGGML_CUDA=OFF",
               "-DLLAMA_CURL=OFF", "-DBUILD_SHARED_LIBS=OFF"],
              ["cmake", "--build", str(d / "build"), "--config", "Release", "-j",
               str(os.cpu_count() or 4), "--target", *ALVOS_LLAMA]]
    for p in passos:
        r = _rodar(p, timeout=3600)
        if r.returncode != 0:
            raise SystemExit(f"llama.cpp: `{' '.join(p)}` falhou: {(r.stdout + r.stderr)[-1500:]}")
    for b in (d / "build" / "bin").glob("llama-*"):
        shutil.copy2(b, d / b.name)
    head = _rodar(["git", "-C", str(d), "rev-parse", "HEAD"]).stdout.strip()
    _rodar([sys.executable, "-m", "pip", "install", "-q", "-e", str(d / "gguf-py")])
    return {"commit_pedido": commit, "commit_clonado": head, "s": round(time.time() - t0, 1),
            "binarios": sorted(p.name for p in d.glob("llama-*") if p.is_file())}


def llama_cpp() -> dict:
    d = TMP / "llama.cpp"
    if not d.exists():
        return {"existe": False}
    fora = {"existe": True,
            "commit": _rodar(["git", "-C", str(d), "rev-parse", "HEAD"]).stdout.strip(),
            "describe": _rodar(["git", "-C", str(d), "describe", "--tags", "--always"]).stdout.strip()}
    conv = d / "convert_hf_to_gguf.py"
    fora["convert_hf_to_gguf_sha256"] = _sha256(conv) if conv.exists() else None
    q = [p for p in d.rglob("llama-quantize") if p.is_file() and os.access(p, os.X_OK)]
    if q:
        r = _rodar([str(q[0]), "--version"], timeout=60)
        fora["llama_quantize"] = {"caminho": str(q[0].relative_to(d)), "sha256": _sha256(q[0]),
                                  "versao": (r.stdout + r.stderr).strip()[-500:]}
    return fora


def tensores_gguf(gguf: Path) -> dict:
    sys.path.insert(0, str(TMP / "llama.cpp" / "gguf-py"))
    from gguf import GGUFReader
    rd = GGUFReader(str(gguf))
    tens = [{"nome": t.name, "tipo": t.tensor_type.name, "forma": [int(x) for x in t.shape],
             "sha256": hashlib.sha256(t.data.tobytes()).hexdigest()} for t in rd.tensors]
    return {"n_tensores": len(tens), "tensores": tens}


def comparar_com_base(meus: dict, base: dict) -> dict:
    a = {t["nome"]: t for t in meus["tensores"]}
    b = {t["nome"]: t for t in base["tensores"]}
    proj = lambda n: any(p in n for p in PROJECOES_GGUF)  # noqa: E731
    fora_proj = [n for n in sorted(set(a) & set(b)) if not proj(n)]
    na_proj = [n for n in sorted(set(a) & set(b)) if proj(n)]
    dif_fora = [n for n in fora_proj if (a[n]["tipo"], a[n]["sha256"]) != (b[n]["tipo"], b[n]["sha256"])]
    mudaram = [n for n in na_proj if a[n]["sha256"] != b[n]["sha256"]]
    return {"mesmos_nomes": set(a) == set(b), "fora_das_projecoes": len(fora_proj),
            "fora_das_projecoes_diferentes": dif_fora[:50], "projecoes": len(na_proj),
            "projecoes_que_mudaram": len(mudaram),
            "so_projecoes_mudaram": set(a) == set(b) and not dif_fora}


# ---------------------------------------------------------------------------
# escolha do checkpoint (função pura)
# ---------------------------------------------------------------------------

def curva_de_validacao(log_history: list[dict]) -> list[dict]:
    return [{"epoca": round(h["epoch"]), "passo": h["step"], "eval_loss": h["eval_loss"]}
            for h in log_history if "eval_loss" in h]


def escolher(curva: list[dict]) -> dict:
    """Menor perda na validação (arredondada na 4ª casa); empate → menos épocas."""
    return min(curva, key=lambda c: (round(c["eval_loss"], CASAS_EMPATE), c["epoca"]))


def _ultimo_checkpoint() -> str | None:
    """O mais avançado em /kaggle/working ou numa saída anterior anexada como entrada."""
    achados = [Path(p) for p in glob.glob(str(CHECKPOINTS / "checkpoint-*"))]
    achados += [Path(p) for p in glob.glob("/kaggle/input/**/checkpoints/checkpoint-*", recursive=True)]
    achados = [p for p in achados if (p / "trainer_state.json").exists()]
    if not achados:
        return None
    melhor = max(achados, key=lambda p: int(p.name.split("-")[1]))
    destino = CHECKPOINTS / melhor.name
    if melhor != destino:
        shutil.copytree(melhor, destino, dirs_exist_ok=True)
    return str(destino)


# ---------------------------------------------------------------------------
# treino + exportação (subprocesso)
# ---------------------------------------------------------------------------

def treinar() -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    log = SAIDA / "log.json"
    linhas, meta, conf = conferir_dataset()
    reg = {"modelo": NOME, "repo": REPO, "revisao_esperada": REVISAO, "hiperparametros": HIPER,
           "dataset": conf, "llama_cpp_esperado": meta["llama_cpp_commit"], "base": meta.get("base"),
           "rascunho": RASCUNHO}
    try:
        import torch
        from datasets import Dataset
        from huggingface_hub import HfApi
        import unsloth  # noqa: F401 — tem de vir antes de transformers/trl
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template, train_on_responses_only
        from trl import SFTConfig, SFTTrainer

        reg.update({"gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    "versoes": _versoes()})
        info = HfApi().model_info(REPO)
        reg["repo_confirmado"] = {"id": info.id, "sha": info.sha}
        if info.sha != REVISAO:
            raise SystemExit(f"{REPO} está em {info.sha}, não em {REVISAO} — abortado")
        t0 = time.time()
        model, tok = FastLanguageModel.from_pretrained(model_name=REPO, max_seq_length=SEQ,
                                                       load_in_4bit=True, dtype=torch.float16)
        reg["carga_s"] = round(time.time() - t0, 1)
        model = FastLanguageModel.get_peft_model(
            model, r=HIPER["r"], lora_alpha=HIPER["lora_alpha"], lora_dropout=HIPER["lora_dropout"],
            bias="none", target_modules=PROJECOES,
            use_gradient_checkpointing=HIPER["use_gradient_checkpointing"], random_state=HIPER["seed"])
        reg["modulos_lora"] = sorted({n.split(".")[-1] for n, m in model.named_modules()
                                      if hasattr(m, "lora_A")})
        if [p for p in PROJECOES if p not in reg["modulos_lora"]]:
            raise SystemExit(f"projeções sem LoRA: {reg['modulos_lora']}")
        tok = get_chat_template(tok, chat_template="qwen3")
        base_tok = getattr(tok, "tokenizer", tok)
        textos, conferencia, longos = {}, {}, []
        for l in linhas:
            chave = f"{l['conjunto']}|{l['slug']}|{l['bucket']}"
            t = base_tok.apply_chat_template(l["messages"], tokenize=False,
                                             add_generation_prompt=False, enable_thinking=False)
            textos[chave] = t.removeprefix("<bos>")
            conferencia[chave] = t.removeprefix("<bos>") == l["chat_esperado"]["qwen"].removeprefix("<bos>")
            n_tok = len(base_tok(textos[chave], add_special_tokens=False).input_ids)
            if n_tok > SEQ:
                longos.append((chave, n_tok))
        reg["template_confere"] = {"todos": all(conferencia.values()),
                                   "falsos": sorted(k for k, v in conferencia.items() if not v)}
        reg["acima_de_max_seq"] = longos
        _json(log, reg)
        if not reg["template_confere"]["todos"]:
            raise SystemExit(f"template_confere falso em {reg['template_confere']['falsos'][:5]} — abortado")
        if longos:
            raise SystemExit(f"exemplos acima de {SEQ} tokens: {longos[:5]} — abortado (sem truncar)")

        ds_t = Dataset.from_list([{"text": textos[k]} for k in textos if k.startswith("treino|")])
        ds_v = Dataset.from_list([{"text": textos[k]} for k in textos if k.startswith("validacao|")])
        params = SFTConfig.__init__.__code__.co_varnames
        kw = dict(dataset_text_field="text", per_device_train_batch_size=1,
                  per_device_eval_batch_size=1,
                  gradient_accumulation_steps=HIPER["gradient_accumulation_steps"],
                  num_train_epochs=HIPER["num_train_epochs"], learning_rate=HIPER["learning_rate"],
                  lr_scheduler_type=HIPER["lr_scheduler_type"], warmup_ratio=HIPER["warmup_ratio"],
                  logging_steps=1, optim=HIPER["optim"], weight_decay=HIPER["weight_decay"],
                  seed=HIPER["seed"], data_seed=HIPER["seed"], fp16=True, bf16=False,
                  output_dir=str(CHECKPOINTS), report_to="none", save_strategy="epoch",
                  save_total_limit=None, save_only_model=False, packing=False, dataset_num_proc=1)
        kw["eval_strategy" if "eval_strategy" in params else "evaluation_strategy"] = "epoch"
        kw["max_length" if "max_length" in params else "max_seq_length"] = SEQ
        tr = SFTTrainer(model=model, tokenizer=base_tok, train_dataset=ds_t, eval_dataset=ds_v,
                        args=SFTConfig(**kw))
        tr = train_on_responses_only(tr, instruction_part=PARTES[0], response_part=PARTES[1])
        mascara = {}
        for nome, ds in (("treino", tr.train_dataset), ("validacao", tr.eval_dataset)):
            x = ds[0]
            if "labels" not in x:
                raise SystemExit(f"{nome}: sem coluna labels depois de train_on_responses_only")
            rot = [i for i, y in zip(x["input_ids"], x["labels"]) if y != -100]
            txt = base_tok.decode(rot)
            mascara[nome] = {"tokens": len(x["input_ids"]), "treinados": len(rot),
                             "comeca_em_chave": txt.lstrip().startswith("{"),
                             "tem_think": "<think>" in txt}
            if not rot or len(rot) == len(x["input_ids"]) or not mascara[nome]["comeca_em_chave"] \
                    or mascara[nome]["tem_think"]:
                raise SystemExit(f"máscara de {nome} fora do esperado: {mascara[nome]}")
        reg["mascara"] = mascara
        retomar = _ultimo_checkpoint()
        reg["retomado_de"] = retomar
        _json(log, reg)
        t0 = time.time()
        res = tr.train(resume_from_checkpoint=retomar)
        reg["treino_s"] = round(time.time() - t0, 1)
        reg["train_metrics"] = res.metrics
        curva = {"treino": [{"passo": h["step"], "epoca": h["epoch"], "loss": h["loss"],
                             "lr": h.get("learning_rate")} for h in tr.state.log_history if "loss" in h],
                 "validacao": curva_de_validacao(tr.state.log_history)}
        _json(SAIDA / "curva.json", curva)
        if len(curva["validacao"]) != HIPER["num_train_epochs"]:
            raise SystemExit(f"perda na validação em {len(curva['validacao'])} épocas, esperadas "
                             f"{HIPER['num_train_epochs']}")
        escolhida = escolher(curva["validacao"])
        reg["curva_validacao"] = curva["validacao"]
        reg["escolhida"] = escolhida
        _json(log, reg)

        # ---- carrega o checkpoint escolhido e confere a perda ----
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        ck = CHECKPOINTS / f"checkpoint-{escolhida['passo']}"
        sd = load_file(str(ck / "adapter_model.safetensors"))
        set_peft_model_state_dict(model, sd)
        reav = tr.evaluate()["eval_loss"]
        reg["reavaliacao"] = {"checkpoint": ck.name, "eval_loss": reav,
                              "confere": abs(reav - escolhida["eval_loss"]) <= TOL_REAVALIACAO}
        _json(log, reg)
        if not reg["reavaliacao"]["confere"]:
            raise SystemExit(f"o checkpoint carregado dá {reav}, a curva diz {escolhida['eval_loss']}")
        ad = SAIDA / "adaptador_escolhido"
        model.save_pretrained(str(ad))
        base_tok.save_pretrained(str(ad))
        reg["adaptador"] = [{"nome": p.name, "bytes": p.stat().st_size, "sha256": _sha256(p)}
                            for p in sorted(ad.iterdir()) if p.is_file()]
        _json(log, reg)

        # ---- exportação: o mesmo caminho da base, com o llama.cpp dela ----
        reg["llama_cpp_preparo"] = preparar_llama_cpp(meta["llama_cpp_commit"])
        _json(log, reg)
        dst = TMP / NOME / "gguf"
        shutil.rmtree(dst, ignore_errors=True)
        t0 = time.time()
        model.save_pretrained_gguf(str(dst), tok, quantization_method="q4_k_m")
        reg["gguf_tempo_s"] = round(time.time() - t0, 1)
        reg["llama_cpp"] = llama_cpp()
        reg["llama_cpp_igual_ao_da_base"] = reg["llama_cpp"].get("commit") == meta["llama_cpp_commit"]
        _json(log, reg)
        gerados = sorted(p for p in (TMP / NOME).rglob("*") if p.is_file()
                         and ((p.suffix == ".gguf" and "Q4_K_M" in p.name.upper()) or p.name == "Modelfile"))
        ggufs = [p for p in gerados if p.suffix == ".gguf"]
        if len(ggufs) != 1:
            raise SystemExit(f"esperava 1 GGUF Q4_K_M, achei {[g.name for g in ggufs]}")
        tens = tensores_gguf(ggufs[0])
        _json(SAIDA / "tensores.json", tens)
        tb = Path(_arquivo_dataset()).with_name("tensores_base.json")
        if tb.exists():
            reg["comparacao_com_base"] = comparar_com_base(tens, json.loads(tb.read_text(encoding="utf-8")))
        if not reg["llama_cpp_igual_ao_da_base"]:
            reg["gguf_ok"] = False
            reg["gguf_motivo"] = (f"llama.cpp {reg['llama_cpp'].get('commit')} ≠ o da base "
                                  f"{meta['llama_cpp_commit']}: GGUF NÃO copiado (o adaptador ficou)")
            return reg
        arquivos = []
        for p in gerados:
            alvo = SAIDA / p.name
            shutil.copy2(p, alvo)
            arquivos.append({"nome": p.name, "bytes": alvo.stat().st_size, "sha256": _sha256(alvo)})
        reg["gguf_arquivos"] = arquivos
        mf = SAIDA / "Modelfile"
        reg["modelfile"] = mf.read_text(encoding="utf-8") if mf.exists() else None
        reg["gguf_ok"] = True
        shutil.rmtree(dst, ignore_errors=True)
        reg["fim"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return reg
    except BaseException:
        reg["erro"] = traceback.format_exc()[-6000:]
        raise
    finally:
        _json(log, reg)


def instalar() -> dict:
    t0 = time.time()
    r = _rodar([sys.executable, "-m", "pip", "install", "-q", "--upgrade", *PACOTES_FIXOS])
    return {"rc": r.returncode, "s": round(time.time() - t0, 1), "pacotes": PACOTES_FIXOS,
            "stderr_fim": (r.stderr or "")[-2000:]}


def orquestrar() -> None:
    RAIZ_SAIDA.mkdir(parents=True, exist_ok=True)
    _, _, conf = conferir_dataset()                 # antes de instalar ou treinar
    resumo = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "dataset": conf,
              "instalacao": instalar()}
    _json(RAIZ_SAIDA / "resumo.json", resumo)
    t0 = time.time()
    try:
        r = _rodar([sys.executable, SCRIPT, "--treinar"], timeout=11 * 3600)
        resumo.update({"rc": r.returncode, "saida_fim": (r.stdout or "")[-4000:] + "\n"
                       + (r.stderr or "")[-6000:]})
    except subprocess.TimeoutExpired:
        resumo["rc"] = "timeout"
    resumo["s"] = round(time.time() - t0, 1)
    resumo["fim"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _json(RAIZ_SAIDA / "resumo.json", resumo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--treinar", action="store_true", help="(subprocesso) treina e exporta")
    a, _ = ap.parse_known_args()
    if a.treinar:
        treinar()
    else:
        orquestrar()


if __name__ == "__main__":
    main()
