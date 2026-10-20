"""Teste de FUMAÇA do fine-tuning no Kaggle (Fase 0 → critério E1–E4).

Roda como `code_file` de um kernel PRIVADO (`kernel-metadata.json`), em segundo
plano ("Save & Run All" / `kaggle kernels push`). Sem argumentos, é o
ORQUESTRADOR: instala o Unsloth, roda cada candidato num SUBPROCESSO (a VRAM
volta inteira entre um e outro) e grava `/kaggle/working/smoke/resumo.json`.
Com `--modelo`, mede um candidato:

1. carrega em 4-bit pelo Unsloth (confirma o repositório no Hugging Face e
   grava o `sha` da revisão);
2. LoRA r=16 em todas as projeções lineares, gradient checkpointing
   "unsloth", fp16, batch 1, seed 3407;
3. template de chat com raciocínio DESLIGADO; confere o texto renderizado
   contra o `chat_esperado` do dataset (montado no Mac com `comum.chat`);
4. treina SÓ nas respostas (máscara no prompt) e confere a máscara;
5. 10 passos no exemplo mais longo a 14.336; em OOM, o orquestrador repete
   tudo a 12.288 com o mais longo que cabe nesse corte;
6. 5 passos nos medianos (s/passo para o E3);
7. funde o adaptador e exporta GGUF Q4_K_M (tempo, pico de RAM, tamanho,
   sha256, Modelfile), num disco de rascunho, e copia só o GGUF e o
   Modelfile para /kaggle/working;
8. grava `/kaggle/working/smoke/<modelo>/log.json` com versões.

T4 ÚNICA: o Kaggle só oferece T4 ×2 (`NvidiaTeslaT4`); este processo enxerga
uma GPU só (`CUDA_VISIBLE_DEVICES=0`, antes de importar o torch).

Nada aqui avalia qualidade. JSON inválido do modelo não treinado não é medido.
"""
from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import argparse
import glob
import hashlib
import json
import math
import platform
import shutil
import statistics
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

SAIDA = Path("/kaggle/working/smoke")
RASCUNHO = Path("/tmp/espectro24_smoke")          # fora de /kaggle/working (20 GB)
ENTRADA_GLOB = "/kaggle/input/**/smoke.jsonl"
SEED = 3407
PASSOS_LONGO = 10
PASSOS_MEDIANO = 5
SEQ = {"14336": 14336, "12288": 12288}

MODELOS = {
    "gemma-4-12b": {"repo": "unsloth/gemma-4-12b-it", "familia": "gemma",
                    "template": "gemma-4", "loader": "FastModel"},
    "gemma-4-e4b": {"repo": "unsloth/gemma-4-E4B-it-unsloth-bnb-4bit", "familia": "gemma",
                    "template": "gemma-4", "loader": "FastModel"},
    "qwen3-8b": {"repo": "unsloth/Qwen3-8B-unsloth-bnb-4bit", "familia": "qwen",
                 "template": "qwen3", "loader": "FastLanguageModel"},
}
# Treinar só na resposta: o prefixo de cada turno, como o template o escreve.
PARTES = {"gemma": ("<|turn>user\n", "<|turn>model\n"),
          "qwen": ("<|im_start|>user\n", "<|im_start|>assistant\n")}
PROJECOES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def _json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    return h.hexdigest()


def _ler_dataset() -> list[dict]:
    achados = glob.glob(ENTRADA_GLOB, recursive=True)
    if len(achados) != 1:
        raise SystemExit(f"esperava 1 smoke.jsonl em /kaggle/input, achei {achados}")
    linhas = [json.loads(l) for l in Path(achados[0]).read_text(encoding="utf-8").split("\n")
              if l.strip()]
    for l in linhas:
        if l.get("conjunto") != "treino":
            raise SystemExit(f"exemplo fora do treino no dataset: {l.get('slug')}")
    return linhas


def _versoes() -> dict:
    import importlib.metadata as md
    v = {"python": platform.python_version()}
    for pkg in ("unsloth", "unsloth_zoo", "transformers", "trl", "torch", "peft",
                "bitsandbytes", "accelerate", "datasets", "xformers", "triton"):
        try:
            v[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            v[pkg] = None
    v["kaggle_env"] = {k: val for k, val in os.environ.items()
                       if k.startswith("KAGGLE_") and not any(
                           s in k for s in ("TOKEN", "KEY", "SECRET", "PASS"))}
    try:
        v["imagem_kaggle"] = Path("/etc/kaggle_image").read_text().strip()  # se existir
    except OSError:
        v["imagem_kaggle"] = os.environ.get("KAGGLE_DOCKER_IMAGE")
    return v


class PicoRAM(threading.Thread):
    """Pico de RAM do SISTEMA (inclui o llama.cpp que o Unsloth chama)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.parar, self.pico_gb = threading.Event(), 0.0

    def run(self):
        import psutil
        while not self.parar.is_set():
            vm = psutil.virtual_memory()
            self.pico_gb = max(self.pico_gb, (vm.total - vm.available) / 2**30)
            self.parar.wait(0.5)


# ---------------------------------------------------------------------------
# um candidato
# ---------------------------------------------------------------------------

def _renderizar(tok, mensagens: list[dict], familia: str) -> str:
    """Texto de treino pelo template do tokenizer, raciocínio desligado."""
    base = getattr(tok, "tokenizer", tok)
    try:
        txt = base.apply_chat_template(mensagens, tokenize=False, add_generation_prompt=False,
                                       enable_thinking=False)
    except Exception:  # noqa: BLE001 — processadores multimodais pedem partes
        partes = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                  for m in mensagens]
        txt = tok.apply_chat_template(partes, tokenize=False, add_generation_prompt=False,
                                      enable_thinking=False)
    return txt


def _comparar(obtido: str, esperado: str) -> dict:
    a, b = obtido.removeprefix("<bos>"), esperado.removeprefix("<bos>")
    if a == b:
        return {"igual": True}
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return {"igual": False, "posicao": i, "obtido": a[max(0, i - 80):i + 80],
            "esperado": b[max(0, i - 80):i + 80], "len_obtido": len(a), "len_esperado": len(b)}


def medir_modelo(nome: str, seq: int) -> dict:
    import torch
    from datasets import Dataset
    from huggingface_hub import HfApi
    import unsloth  # noqa: F401 — tem de vir antes de transformers/trl
    from unsloth import FastLanguageModel, FastModel
    from unsloth.chat_templates import get_chat_template, train_on_responses_only
    from transformers import TrainerCallback
    from trl import SFTConfig, SFTTrainer

    cfg = MODELOS[nome]
    reg = {"modelo": nome, "repo": cfg["repo"], "max_seq_length": seq, "seed": SEED,
           "dispositivos_cuda": torch.cuda.device_count(),
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "bf16_suportado": torch.cuda.is_bf16_supported() if torch.cuda.is_available() else None,
           "versoes": _versoes()}
    info = HfApi().model_info(cfg["repo"])
    reg["repo_confirmado"] = {"id": info.id, "sha": info.sha}
    dados = _ler_dataset()
    papel_longo = "mais_longo" if seq >= 14336 else "mais_longo_12k"
    longo = next(l for l in dados if l["papel"] == papel_longo)
    medianos = [l for l in dados if l["papel"].startswith("mediano_")]

    Loader = FastModel if cfg["loader"] == "FastModel" else FastLanguageModel
    t0 = time.time()
    extra = {"full_finetuning": False} if cfg["loader"] == "FastModel" else {}
    model, tok = Loader.from_pretrained(model_name=cfg["repo"], max_seq_length=seq,
                                        load_in_4bit=True, dtype=torch.float16, **extra)
    reg["carga_s"] = round(time.time() - t0, 1)
    if cfg["loader"] == "FastModel":
        model = FastModel.get_peft_model(
            model, finetune_vision_layers=False, finetune_language_layers=True,
            finetune_attention_modules=True, finetune_mlp_modules=True,
            r=16, lora_alpha=16, lora_dropout=0, bias="none",
            use_gradient_checkpointing="unsloth", random_state=SEED)
    else:
        model = FastLanguageModel.get_peft_model(
            model, r=16, lora_alpha=16, lora_dropout=0, bias="none", target_modules=PROJECOES,
            use_gradient_checkpointing="unsloth", random_state=SEED)
    reg["modulos_lora"] = sorted({n.split(".")[-1] for n, m in model.named_modules()
                                  if hasattr(m, "lora_A")})
    reg["projecoes_faltando"] = [p for p in PROJECOES if p not in reg["modulos_lora"]]
    tok = get_chat_template(tok, chat_template=cfg["template"])

    textos = {l["papel"]: _renderizar(tok, l["messages"], cfg["familia"]) for l in dados}
    reg["template_confere"] = {p: _comparar(textos[p], l["chat_esperado"][cfg["familia"]])
                               for p, l in ((l["papel"], l) for l in dados)}

    class Tempos(TrainerCallback):
        def __init__(self):
            self.t, self.inicio = [], None

        def on_step_begin(self, args, state, control, **kw):
            self.inicio = time.time()

        def on_step_end(self, args, state, control, **kw):
            self.t.append(round(time.time() - self.inicio, 3))

    def treinar(textos_lista: list[str], passos: int, rotulo: str) -> dict:
        ds = Dataset.from_list([{"text": t.removeprefix("<bos>")} for t in textos_lista])
        kw = dict(dataset_text_field="text", per_device_train_batch_size=1,
                  gradient_accumulation_steps=1, max_steps=passos, learning_rate=2e-4,
                  warmup_steps=0, logging_steps=1, optim="adamw_8bit", weight_decay=0.0,
                  lr_scheduler_type="constant", seed=SEED, fp16=True, bf16=False,
                  output_dir=str(RASCUNHO / nome / rotulo), report_to="none",
                  save_strategy="no", packing=False, dataset_num_proc=1)
        params = SFTConfig.__init__.__code__.co_varnames
        kw["max_length" if "max_length" in params else "max_seq_length"] = seq
        tr = SFTTrainer(model=model, tokenizer=getattr(tok, "tokenizer", tok),
                        train_dataset=ds, args=SFTConfig(**kw))
        u, r = PARTES[cfg["familia"]]
        tr = train_on_responses_only(tr, instruction_part=u, response_part=r)
        lote = tr.train_dataset[0]
        # Máscara: só a resposta conta. Se o Unsloth montar os rótulos no
        # collator (sem coluna `labels`), a contagem fica None e o log diz.
        rot = ([x for x in lote["labels"] if x != -100] if "labels" in lote else None)
        cb = Tempos()
        tr.add_callback(cb)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        res = tr.train()
        perdas = [h["loss"] for h in tr.state.log_history if "loss" in h]
        return {"passos": passos, "tokens_entrada": len(lote["input_ids"]),
                "tokens_treinados": None if rot is None else len(rot),
                "pico_vram_reserved_gib": round(torch.cuda.max_memory_reserved() / 2**30, 3),
                "pico_vram_allocated_gib": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                "s_por_passo": cb.t,
                "s_por_passo_mediana_sem_1o": statistics.median(cb.t[1:]) if len(cb.t) > 1 else None,
                "perdas": perdas, "perdas_finitas": all(math.isfinite(p) for p in perdas),
                "train_runtime_s": res.metrics.get("train_runtime")}

    reg["longo"] = {"papel": papel_longo, "slug": longo["slug"], "bucket": longo["bucket"],
                    **treinar([textos[papel_longo]] * PASSOS_LONGO, PASSOS_LONGO, "longo")}
    _json(SAIDA / nome / "log.json", reg)               # parcial: o OOM do GGUF não apaga
    reg["mediano"] = treinar([textos[l["papel"]] for l in medianos] * 2, PASSOS_MEDIANO, "mediano")
    _json(SAIDA / nome / "log.json", reg)

    # ---- fundir e exportar GGUF Q4_K_M ----
    dst = RASCUNHO / nome / "gguf"
    shutil.rmtree(dst, ignore_errors=True)
    pico = PicoRAM()
    pico.start()
    t0 = time.time()
    try:
        model.save_pretrained_gguf(str(dst), tok, quantization_method="q4_k_m")
        reg["gguf_ok"] = True
    except Exception as e:  # noqa: BLE001
        reg["gguf_ok"] = False
        reg["gguf_erro"] = f"{type(e).__name__}: {e}"[:2000]
    finally:
        pico.parar.set()
        pico.join(timeout=5)
    reg["gguf_tempo_s"] = round(time.time() - t0, 1)
    reg["gguf_pico_ram_sistema_gib"] = round(pico.pico_gb, 2)
    arquivos = []
    destino = SAIDA / nome
    # o Unsloth grava em `dst` ou numa pasta irmã (`<dst>_gguf`): procura sob a
    # pasta do modelo tudo o que nasceu depois de t0
    gerados = [p for p in sorted((RASCUNHO / nome).rglob("*"))
               if p.is_file() and p.stat().st_mtime >= t0]
    for p in gerados:
        if (p.suffix == ".gguf" and "Q4_K_M" in p.name.upper()) or p.name == "Modelfile":
            alvo = destino / p.name
            shutil.copy2(p, alvo)
            arquivos.append({"nome": p.name, "bytes": alvo.stat().st_size, "sha256": _sha256(alvo)})
    reg["gguf_arquivos"] = arquivos
    reg["gguf_todos_arquivos_gerados"] = [str(p.relative_to(RASCUNHO / nome)) for p in gerados]
    mf = destino / "Modelfile"
    reg["modelfile"] = mf.read_text(encoding="utf-8") if mf.exists() else None
    _json(SAIDA / nome / "log.json", reg)
    return reg


# ---------------------------------------------------------------------------
# orquestrador
# ---------------------------------------------------------------------------

def instalar() -> dict:
    t0 = time.time()
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade",
                        "unsloth", "unsloth_zoo"], capture_output=True, text=True)
    return {"rc": r.returncode, "s": round(time.time() - t0, 1), "stderr_fim": r.stderr[-2000:]}


def rodar_um(nome: str, seq: int, timeout_s: int) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, __file__, "--modelo", nome, "--seq", str(seq)],
                           capture_output=True, text=True, timeout=timeout_s)
        rc, err = r.returncode, r.stdout[-3000:] + "\n" + r.stderr[-6000:]
    except subprocess.TimeoutExpired:
        rc, err = "timeout", ""
    log = SAIDA / nome / "log.json"
    reg = json.loads(log.read_text()) if log.exists() else {}
    return {"modelo": nome, "seq": seq, "rc": rc, "s": round(time.time() - t0, 1),
            "oom": "OutOfMemoryError" in err or "CUDA out of memory" in err,
            "log": reg, "saida_fim": err[-4000:]}


def orquestrar(incluir_qwen: bool) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    resumo = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "instalacao": instalar(),
              "execucoes": []}
    _json(SAIDA / "resumo.json", resumo)
    nomes = ["gemma-4-12b", "gemma-4-e4b"] + (["qwen3-8b"] if incluir_qwen else [])
    for nome in nomes:
        for seq in (SEQ["14336"], SEQ["12288"]):
            ex = rodar_um(nome, seq, timeout_s=4 * 3600)
            resumo["execucoes"].append(ex)
            _json(SAIDA / "resumo.json", resumo)
            if not ex["oom"]:
                break                       # 12.288 só depois de OOM a 14.336
            shutil.move(str(SAIDA / nome), str(SAIDA / f"{nome}__oom_{seq}"))
    resumo["fim"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _json(SAIDA / "resumo.json", resumo)
    shutil.rmtree(RASCUNHO, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=list(MODELOS))
    ap.add_argument("--seq", type=int, default=SEQ["14336"])
    ap.add_argument("--incluir-qwen", action="store_true",
                    help="só se nenhum Gemma passar (decisão do dono)")
    a, _ = ap.parse_known_args()
    if a.modelo is None:
        orquestrar(a.incluir_qwen or os.environ.get("ESPECTRO24_INCLUIR_QWEN") == "1")
        return
    try:
        medir_modelo(a.modelo, a.seq)
    except Exception:
        log = SAIDA / a.modelo / "log.json"
        reg = json.loads(log.read_text()) if log.exists() else {"modelo": a.modelo, "max_seq_length": a.seq}
        reg["erro"] = traceback.format_exc()[-6000:]
        _json(log, reg)
        raise


if __name__ == "__main__":
    main()
