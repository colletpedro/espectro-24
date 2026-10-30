"""Teste de FUMAÇA do fine-tuning no Kaggle (Fase 0 → critério E1–E4).

Roda como `code_file` de um kernel PRIVADO (`kernel-metadata.json`), em segundo
plano ("Save & Run All" / `kaggle kernels push`). Sem argumentos, é o
ORQUESTRADOR: instala o Unsloth e roda cada candidato num SUBPROCESSO, na ordem
E4B → 12B (a VRAM volta inteira entre um e outro; um candidato que cai não
derruba o outro). Com `--modelo`, mede um candidato:

1. carrega em 4-bit pelo Unsloth (confirma o repositório no Hugging Face e
   grava o `sha` da revisão; os repositórios são públicos, sem token);
2. LoRA r=16 em todas as projeções lineares, gradient checkpointing
   "unsloth", fp16, batch 1, seed 3407;
3. template de chat com raciocínio DESLIGADO; confere o texto renderizado
   contra o `chat_esperado` do dataset (montado no Mac com `comum.chat`);
4. treina SÓ nas respostas (máscara no prompt);
5. 10 passos no exemplo mais longo a 14.336; em OOM, o orquestrador repete
   tudo a 12.288 com o mais longo que cabe nesse corte;
6. 5 passos nos medianos (s/passo para o E3);
7. GRAVA E1–E3 em disco (com fsync) ANTES de qualquer exportação;
8. salva o ADAPTADOR LoRA em /kaggle/working ANTES da fusão;
9. registra o disco temporário livre contra a estimativa da exportação
   (fusão 16-bit + GGUF intermediário + Q4_K_M) — só registro: a exportação
   é sempre tentada, e uma falha deixa a causa no log (erro + linha do tempo),
   que é o que o adendo do critério exige para o caminho alternativo;
10. funde e exporta o GGUF Q4_K_M no disco temporário e copia só o Q4_K_M e
    o Modelfile para /kaggle/working.

Disco: em /kaggle/working (20 GB salvos) ficam só o GGUF Q4_K_M, o Modelfile,
o adaptador e os logs. Cache do Hugging Face, `cwd` (onde o Unsloth clona e
compila o llama.cpp e guarda o cache de compilação), modelo fundido e GGUF
intermediário vão para `RASCUNHO`, fora de /kaggle/working.

Monitor: uma linha do tempo (a cada 2 s, gravada e sincronizada no disco a
cada amostra, para sobreviver a um OOM-kill) com a FASE, a RAM usada e
disponível do sistema e o disco livre em /tmp e /kaggle/working; `df -h` em
cada troca de fase; pico de RAM por fase no `log.json`. As fases da
exportação (fusão × conversão) saem das mensagens do Unsloth.

T4 ÚNICA: o Kaggle só oferece T4 ×2 (`NvidiaTeslaT4`); este processo enxerga
uma GPU só (`CUDA_VISIBLE_DEVICES=0`, antes de importar o torch).

Nada aqui avalia qualidade. JSON inválido do modelo não treinado não é medido.

Revisão de 2026-10-22 (Qwen3-8B; o critério e as configurações não mudam):
- os candidatos vêm do `meta.json` do dataset (`candidatos`), não de um flag:
  o kernel do Qwen3-8B roda só o Qwen3-8B; sem `meta.json`, E4B → 12B como antes;
- as pastas de saída têm nome PREVISÍVEL: `<modelo>__<seq>` (ex.:
  `qwen3-8b__14336`), exista erro ou não; o resultado está em `log.json`;
- `unsloth` e `unsloth_zoo` ficam FIXADOS nas versões do primeiro smoke
  (2026.10.7), para a comparação ser com a mesma pilha;
- Qwen3: a parte de resposta da máscara inclui o bloco `<think>` VAZIO que o
  template põe no prompt (`enable_thinking=False`): ele é prompt na inferência,
  então fica mascarado; o log prova com os tokens treinados decodificados;
- `atencao` no `log.json`: o backend de atenção EFETIVO (operadores do ATen e
  kernels CUDA vistos por `torch.profiler` num passo curto) e o dtype;
- `e1`, `e2` e `e3` já calculados no log (E3 com o nº real de exemplos de treino
  depois da limpeza, do `meta.json`).

Revisão de 2026-10-30: ao iniciar (orquestrador e cada subprocesso), o sha256 do
`smoke.jsonl` lido é conferido contra `meta.json["smoke_sha256"]` e gravado em
`resumo.json`/`log.json` (`dataset`); divergência, ou `meta.json` sem o sha,
aborta antes de instalar ou treinar.
"""
from __future__ import annotations

import os

SCRIPT = os.path.abspath(__file__)        # antes do chdir abaixo
RASCUNHO = "/tmp/espectro24_smoke"
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
import statistics
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

SAIDA = Path("/kaggle/working/smoke")
TMP = Path(RASCUNHO)
ENTRADA_GLOB = "/kaggle/input/**/smoke.jsonl"
SEED = 3407
PASSOS_LONGO = 10
PASSOS_MEDIANO = 5
SEQ = {"14336": 14336, "12288": 12288}
ORDEM = ["gemma-4-e4b", "gemma-4-12b"]          # E4B primeiro (pré-voo, item b)
# A pilha do primeiro smoke (log.json: unsloth 2026.10.7). `ESPECTRO24_UNSLOTH_LIVRE=1`
# instala a última versão (a comparação com o primeiro smoke deixa de valer).
PACOTES_FIXOS = ["unsloth==2026.10.7", "unsloth_zoo==2026.10.7"]
LIMITE_E1_GIB = 14.0
LIMITE_E3_H = 20.0

MODELOS = {
    "gemma-4-12b": {"repo": "unsloth/gemma-4-12b-it", "familia": "gemma",
                    "template": "gemma-4", "loader": "FastModel", "gb_16bit": 24.0},
    "gemma-4-e4b": {"repo": "unsloth/gemma-4-E4B-it-unsloth-bnb-4bit", "familia": "gemma",
                    "template": "gemma-4", "loader": "FastModel", "gb_16bit": 16.0},
    "qwen3-8b": {"repo": "unsloth/Qwen3-8B-unsloth-bnb-4bit", "familia": "qwen",
                 "template": "qwen3", "loader": "FastLanguageModel", "gb_16bit": 16.4},
}
# Treinar só na resposta: o prefixo de cada turno, como o template o escreve.
# Qwen3 com `enable_thinking=False`: o template abre o turno do assistente com o
# bloco de raciocínio VAZIO, que na inferência já vem no prompt — não é alvo.
PARTES = {"gemma": ("<|turn>user\n", "<|turn>model\n"),
          "qwen": ("<|im_start|>user\n", "<|im_start|>assistant\n<think>\n\n</think>\n\n")}
PROJECOES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
# Disco para exportar: fusão 16-bit + GGUF intermediário 16-bit + Q4_K_M (~0,3
# do 16-bit) + 10% de folga. ESTIMADO pelo tamanho dos pesos, não medido.
FATOR_DISCO_EXPORT = (1 + 1 + 0.3) * 1.10
# Marcas das mensagens do Unsloth que separam as fases da exportação.
MARCAS_FUSAO = ("merging", "merge", "saving")
MARCAS_CONVERSAO = ("convert", "gguf", "quantiz", "llama.cpp", "llama-quantize")


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


def _df() -> str:
    r = subprocess.run(["df", "-h", "/tmp", "/kaggle/working", "/"], capture_output=True, text=True)
    return r.stdout


def _livre_gb(caminho: str) -> float:
    return shutil.disk_usage(caminho).free / 2**30


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


def _ler_meta() -> dict:
    """`meta.json` do dataset (ao lado do `smoke.jsonl`); {} se não houver."""
    achados = glob.glob(ENTRADA_GLOB, recursive=True)
    if len(achados) != 1:
        return {}
    m = Path(achados[0]).with_name("meta.json")
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}


def _conferir_dataset() -> dict:
    """sha256 do `smoke.jsonl` LIDO contra `meta.json["smoke_sha256"]`; aborta
    se divergir ou se o `meta.json` não trouxer o sha (sem ele não há o que
    conferir). As versões 2 e 3 do kernel do Qwen3-8B rodaram sobre uma versão
    do dataset que não se pôde verificar (FINETUNE_REGISTRO.md): esta conferência
    é o que impede isso de passar calado. Vale para todo kernel de treino."""
    achados = glob.glob(ENTRADA_GLOB, recursive=True)
    if len(achados) != 1:
        raise SystemExit(f"esperava 1 smoke.jsonl em /kaggle/input, achei {achados}")
    lido = _sha256(Path(achados[0]))
    esperado = _ler_meta().get("smoke_sha256")
    conf = {"arquivo": achados[0], "sha256_lido": lido, "sha256_meta": esperado,
            "confere": lido == esperado}
    print(f"[dataset] smoke.jsonl sha256 lido {lido} / meta.json {esperado}", flush=True)
    if not conf["confere"]:
        raise SystemExit(f"smoke.jsonl lido ({lido}) não é o do meta.json ({esperado}): "
                         f"dataset errado ou desatualizado no Kaggle — abortado")
    return conf


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
    v["imagem_kaggle"] = os.environ.get("KAGGLE_DOCKER_IMAGE") or os.environ.get("KAGGLE_IMAGE")
    return v


class Monitor(threading.Thread):
    """Linha do tempo de RAM e disco, por fase, gravada a cada amostra."""

    def __init__(self, arquivo: Path):
        super().__init__(daemon=True)
        self.arquivo, self.fase = arquivo, "inicio"
        self.parar = threading.Event()
        self.picos: dict[str, float] = {}
        self.df: list[dict] = []
        arquivo.parent.mkdir(parents=True, exist_ok=True)

    def mudar(self, fase: str) -> None:
        if fase != self.fase:
            self.fase = fase
            self.df.append({"fase": fase, "ts": time.time(), "df_h": _df()})

    def run(self):
        import psutil
        with open(self.arquivo, "a", encoding="utf-8") as f:
            while not self.parar.is_set():
                vm = psutil.virtual_memory()
                usada = (vm.total - vm.available) / 2**30
                self.picos[self.fase] = max(self.picos.get(self.fase, 0.0), usada)
                f.write(json.dumps({"ts": round(time.time(), 1), "fase": self.fase,
                                    "ram_usada_gib": round(usada, 2),
                                    "ram_disponivel_gib": round(vm.available / 2**30, 2),
                                    "ram_total_gib": round(vm.total / 2**30, 2),
                                    "tmp_livre_gib": round(_livre_gb("/tmp"), 2),
                                    "working_livre_gib": round(_livre_gb("/kaggle/working"), 2)})
                        + "\n")
                f.flush()
                os.fsync(f.fileno())
                self.parar.wait(2.0)


class _Marcas:
    """Repassa o stdout e troca a fase do monitor pelas mensagens do Unsloth."""

    def __init__(self, base, mon: Monitor):
        self.base, self.mon = base, mon

    def write(self, s):
        baixo = s.lower()
        if self.mon.fase.startswith("export"):
            if any(m in baixo for m in MARCAS_CONVERSAO):
                self.mon.mudar("exportacao_conversao")
            elif any(m in baixo for m in MARCAS_FUSAO) and self.mon.fase != "exportacao_conversao":
                self.mon.mudar("exportacao_fusao")
        return self.base.write(s)

    def flush(self):
        return self.base.flush()


# ---------------------------------------------------------------------------
# backend de atenção EFETIVO
# ---------------------------------------------------------------------------

def sondar_atencao(model, tk, texto: str, torch, n_tokens: int = 1024) -> dict:
    """Qual atenção RODA, não qual foi pedida: um passo curto (forward + backward
    em `n_tokens`) sob `torch.profiler`, lendo os operadores do ATen e os kernels
    CUDA que apareceram. O seletor do SDPA decide por dtype, GQA, máscara e
    cabeça, nunca pelo comprimento; então o passo curto vale para o longo. Nunca
    derruba a medição: erro vira `erro` no registro."""
    import re
    info: dict = {}
    try:
        cfg = getattr(model, "config", None)
        info["attn_implementation_config"] = getattr(cfg, "_attn_implementation", None)
        info["sdp_habilitados"] = {
            "flash": torch.backends.cuda.flash_sdp_enabled(),
            "mem_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
            "math": torch.backends.cuda.math_sdp_enabled(),
            "cudnn": getattr(torch.backends.cuda, "cudnn_sdp_enabled", lambda: None)()}
        info["env"] = {k: v for k, v in os.environ.items()
                       if k.startswith(("UNSLOTH", "PYTORCH_CUDA"))}
        try:
            from unsloth.models import _utils as U
            info["unsloth_flags"] = {k: getattr(U, k, None)
                                     for k in ("HAS_XFORMERS", "HAS_FLASH_ATTENTION")}
        except Exception as e:  # noqa: BLE001
            info["unsloth_flags_erro"] = f"{type(e).__name__}: {e}"[:200]
        camada = next((m for n, m in model.named_modules() if n.endswith("self_attn")), None)
        vistos: dict = {}
        hooks = []
        if camada is not None:
            info["classe_atencao"] = f"{type(camada).__module__}.{type(camada).__qualname__}"
            info["forward_atencao"] = (f"{getattr(type(camada).forward, '__module__', '?')}."
                                       f"{getattr(type(camada).forward, '__qualname__', '?')}")

            def pre(_m, args, kw):
                h = kw.get("hidden_states", args[0] if args else None)
                if h is not None:
                    vistos["entrada_dtype"] = str(h.dtype)
                    vistos["entrada_shape"] = list(h.shape)

            def pos(_m, _a, saida):
                o = saida[0] if isinstance(saida, tuple) else saida
                vistos["saida_dtype"] = str(o.dtype)

            hooks = [camada.register_forward_pre_hook(pre, with_kwargs=True),
                     camada.register_forward_hook(pos)]
        ids = tk(texto, return_tensors="pt", truncation=True, max_length=n_tokens)["input_ids"]
        ids = ids.to("cuda")
        model.train()
        from torch.profiler import ProfilerActivity, profile
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
                     record_shapes=True) as prof:
            perda = model(input_ids=ids, labels=ids).loss
            perda.backward()
            torch.cuda.synchronize()
        for h in hooks:
            h.remove()
        model.zero_grad(set_to_none=True)
        torch.cuda.empty_cache()
        info["dtypes_vistos_na_camada_0"] = vistos
        rx = re.compile(r"attention|sdpa|fmha|flash|xformers|cutlass.*f(16|32)", re.I)
        ops, n_softmax = {}, 0
        for e in prof.key_averages():
            if rx.search(e.key):
                ops[e.key] = {"n": e.count, "shapes": [str(x) for x in (e.input_shapes or [])[:1]]}
            elif "softmax" in e.key.lower():
                n_softmax += e.count          # sozinho não diz nada (perda, MLP), só contexto
        info["softmax_chamadas"] = n_softmax
        info["operadores_e_kernels"] = dict(sorted(ops.items(), key=lambda kv: -kv[1]["n"])[:30])
        baixo = " ".join(ops).lower()
        achados = []
        if "xformers" in baixo:
            achados.append("xformers")
        if "efficient_attention" in baixo or "fmha_cutlass" in baixo:
            achados.append("sdpa mem-efficient (cutlass)")
        if "flash" in baixo:
            achados.append("flash")
        if "cudnn" in baixo:
            achados.append("cudnn")
        if "attention_math" in baixo:
            achados.append("sdpa math")
        info["backend_detectado"] = achados or ["nenhum operador de atenção reconhecido: "
                                                "ver operadores_e_kernels"]
        info["aviso"] = ("math = a matriz L×L é materializada; mem-efficient/flash/xformers = "
                         "memória O(L). Kernels CUDA trazem o dtype no nome (f16/f32).")
    except Exception as e:  # noqa: BLE001
        info["erro"] = f"{type(e).__name__}: {e}"[:600]
        try:
            model.zero_grad(set_to_none=True)
            torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass
    return info


# ---------------------------------------------------------------------------
# um candidato
# ---------------------------------------------------------------------------

def _renderizar(tok, mensagens: list[dict]) -> str:
    """Texto de treino pelo template do tokenizer, raciocínio desligado."""
    base = getattr(tok, "tokenizer", tok)
    try:
        return base.apply_chat_template(mensagens, tokenize=False, add_generation_prompt=False,
                                        enable_thinking=False)
    except Exception:  # noqa: BLE001 — processadores multimodais pedem partes
        partes = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                  for m in mensagens]
        return tok.apply_chat_template(partes, tokenize=False, add_generation_prompt=False,
                                       enable_thinking=False)


def _comparar(obtido: str, esperado: str) -> dict:
    a, b = obtido.removeprefix("<bos>"), esperado.removeprefix("<bos>")
    if a == b:
        return {"igual": True}
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return {"igual": False, "posicao": i, "obtido": a[max(0, i - 80):i + 80],
            "esperado": b[max(0, i - 80):i + 80], "len_obtido": len(a), "len_esperado": len(b)}


def medir_modelo(nome: str, seq: int) -> dict:
    cfg = MODELOS[nome]
    pasta = SAIDA / nome
    log = pasta / "log.json"
    mon = Monitor(pasta / "linha_do_tempo.jsonl")
    mon.start()
    reg = {"modelo": nome, "repo": cfg["repo"], "max_seq_length": seq, "seed": SEED,
           "rascunho": RASCUNHO, "df_inicio": _df(), "dataset": _conferir_dataset()}

    def gravar():
        reg["pico_ram_por_fase_gib"] = {k: round(v, 2) for k, v in mon.picos.items()}
        reg["df_por_fase"] = mon.df
        _json(log, reg)

    try:
        mon.mudar("carga")
        import torch
        from datasets import Dataset
        from huggingface_hub import HfApi
        import unsloth  # noqa: F401 — tem de vir antes de transformers/trl
        from unsloth import FastLanguageModel, FastModel
        from unsloth.chat_templates import get_chat_template, train_on_responses_only
        from transformers import TrainerCallback
        from trl import SFTConfig, SFTTrainer

        reg.update({"dispositivos_cuda": torch.cuda.device_count(),
                    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    "bf16_suportado": (torch.cuda.is_bf16_supported()
                                       if torch.cuda.is_available() else None),
                    "versoes": _versoes()})
        info = HfApi().model_info(cfg["repo"])
        reg["repo_confirmado"] = {"id": info.id, "sha": info.sha,
                                  "gated": getattr(info, "gated", None)}
        dados = _ler_dataset()
        papel_longo = "mais_longo" if seq >= 14336 else "mais_longo_12k"
        longo = next(l for l in dados if l["papel"] == papel_longo)
        medianos = [l for l in dados if l["papel"].startswith("mediano_")]

        Loader = FastModel if cfg["loader"] == "FastModel" else FastLanguageModel
        extra = {"full_finetuning": False} if cfg["loader"] == "FastModel" else {}
        t0 = time.time()
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
                model, r=16, lora_alpha=16, lora_dropout=0, bias="none",
                target_modules=PROJECOES, use_gradient_checkpointing="unsloth",
                random_state=SEED)
        reg["modulos_lora"] = sorted({n.split(".")[-1] for n, m in model.named_modules()
                                      if hasattr(m, "lora_A")})
        reg["projecoes_faltando"] = [p for p in PROJECOES if p not in reg["modulos_lora"]]
        tok = get_chat_template(tok, chat_template=cfg["template"])
        textos = {l["papel"]: _renderizar(tok, l["messages"]) for l in dados}
        reg["template_confere"] = {l["papel"]: _comparar(textos[l["papel"]],
                                                         l["chat_esperado"][cfg["familia"]])
                                   for l in dados}
        gravar()
        reg["atencao"] = sondar_atencao(model, getattr(tok, "tokenizer", tok),
                                        textos[papel_longo].removeprefix("<bos>"), torch)
        gravar()

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
                      output_dir=str(TMP / nome / rotulo), report_to="none",
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
            rot = [x for x in lote["labels"] if x != -100] if "labels" in lote else None
            mascara = None
            if rot is not None:
                tk = getattr(tok, "tokenizer", tok)
                treinado = tk.decode([i for i, y in zip(lote["input_ids"], lote["labels"])
                                      if y != -100])
                mascara = {"tokens_treinados": len(rot), "comeco": treinado[:80],
                           "fim": treinado[-60:],
                           "tem_bloco_think": "<think>" in treinado or "</think>" in treinado,
                           "comeca_em_chave": treinado.lstrip().startswith("{")}
                if not rot:
                    raise RuntimeError("máscara vazia: nenhum token treinável (a parte de "
                                       "resposta não foi achada no exemplo)")
                if cfg["familia"] == "qwen" and (mascara["tem_bloco_think"]
                                                 or not mascara["comeca_em_chave"]):
                    raise RuntimeError(f"alvo do Qwen3 fora do esperado: {mascara}")
            cb = Tempos()
            tr.add_callback(cb)
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            res = tr.train()
            perdas = [h["loss"] for h in tr.state.log_history if "loss" in h]
            return {"passos": passos, "tokens_entrada": len(lote["input_ids"]),
                    "tokens_treinados": None if rot is None else len(rot),
                    "mascara": mascara,
                    "pico_vram_reserved_gib": round(torch.cuda.max_memory_reserved() / 2**30, 3),
                    "pico_vram_allocated_gib": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                    "s_por_passo": cb.t,
                    "s_por_passo_mediana_sem_1o": (statistics.median(cb.t[1:])
                                                   if len(cb.t) > 1 else None),
                    "perdas": perdas, "perdas_finitas": all(math.isfinite(p) for p in perdas),
                    "train_runtime_s": res.metrics.get("train_runtime")}

        mon.mudar("treino_longo")
        reg["longo"] = {"papel": papel_longo, "slug": longo["slug"], "bucket": longo["bucket"],
                        **treinar([textos[papel_longo]] * PASSOS_LONGO, PASSOS_LONGO, "longo")}
        gravar()
        mon.mudar("treino_mediano")
        reg["mediano"] = treinar([textos[l["papel"]] for l in medianos] * 2,
                                 PASSOS_MEDIANO, "mediano")
        reg["e1"] = {"limite_gib": LIMITE_E1_GIB, "max_seq_length": seq,
                     "tokens_do_exemplo": reg["longo"]["tokens_entrada"],
                     "pico_reserved_gib": reg["longo"]["pico_vram_reserved_gib"],
                     "passa": reg["longo"]["pico_vram_reserved_gib"] <= LIMITE_E1_GIB}
        reg["e2"] = {"perdas_finitas_longo": reg["longo"]["perdas_finitas"],
                     "perdas_finitas_mediano": reg["mediano"]["perdas_finitas"],
                     "passa": reg["longo"]["perdas_finitas"] and reg["mediano"]["perdas_finitas"]}
        meta, s_passo = _ler_meta(), reg["mediano"]["s_por_passo_mediana_sem_1o"]
        n_ex, epocas = meta.get("n_treino_limpo"), meta.get("epocas_E3", 3)
        if s_passo is not None and n_ex:
            h = s_passo * n_ex * epocas / 3600
            reg["e3"] = {"s_por_passo_mediano": s_passo, "n_exemplos_treino_depois_da_limpeza": n_ex,
                         "epocas": epocas, "horas_projetadas": round(h, 2),
                         "limite_h": LIMITE_E3_H, "passa": h <= LIMITE_E3_H}
        else:
            reg["e3"] = {"erro": "sem s/passo do mediano ou sem n_treino_limpo no meta.json"}
        reg["meta_dataset"] = meta
        reg["e1_e3_gravados_antes_da_exportacao"] = True
        gravar()                                         # E1–E3 no disco (fsync)

        # ---- adaptador ANTES da fusão ----
        mon.mudar("salvar_adaptador")
        ad = pasta / "adaptador_lora"
        model.save_pretrained(str(ad))
        getattr(tok, "tokenizer", tok).save_pretrained(str(ad))
        reg["adaptador"] = [{"nome": p.name, "bytes": p.stat().st_size, "sha256": _sha256(p)}
                            for p in sorted(ad.iterdir()) if p.is_file()]
        gravar()

        # ---- disco antes de exportar ----
        precisa = cfg["gb_16bit"] * FATOR_DISCO_EXPORT
        livre = _livre_gb(RASCUNHO)
        # Só REGISTRO: a exportação é sempre tentada. Pular por estimativa não
        # demonstraria a causa (o adendo do critério exige a causa no log); a
        # falha real deixa o erro e a linha do tempo de disco/RAM.
        reg["exportacao_disco"] = {"precisa_gib_estimado": round(precisa, 1),
                                   "livre_gib": round(livre, 1),
                                   "cabe_pela_estimativa": livre >= precisa, "df_h": _df()}
        gravar()

        # ---- fusão + conversão Q4_K_M ----
        dst = TMP / nome / "gguf"
        shutil.rmtree(dst, ignore_errors=True)
        mon.mudar("exportacao")
        sys.stdout = _Marcas(sys.__stdout__, mon)
        t0 = time.time()
        try:
            model.save_pretrained_gguf(str(dst), tok, quantization_method="q4_k_m")
            reg["gguf_ok"] = True
        except Exception as e:  # noqa: BLE001
            reg["gguf_ok"] = False
            reg["gguf_erro"] = f"{type(e).__name__}: {e}"[:3000]
            txt = str(e).lower()
            reg["gguf_causa"] = ("memoria" if isinstance(e, MemoryError) or "memory" in txt
                                 else "disco" if ("space" in txt or "errno 28" in txt)
                                 else "outra")
            reg["gguf_disco_livre_no_erro_gib"] = round(_livre_gb(RASCUNHO), 2)
        finally:
            sys.stdout = sys.__stdout__
        reg["gguf_tempo_s"] = round(time.time() - t0, 1)
        mon.mudar("copia")
        gerados = [p for p in sorted((TMP / nome).rglob("*"))
                   if p.is_file() and p.stat().st_mtime >= t0]
        arquivos = []
        for p in gerados:
            if (p.suffix == ".gguf" and "Q4_K_M" in p.name.upper()) or p.name == "Modelfile":
                alvo = pasta / p.name
                shutil.copy2(p, alvo)
                arquivos.append({"nome": p.name, "bytes": alvo.stat().st_size,
                                 "sha256": _sha256(alvo)})
        reg["gguf_arquivos"] = arquivos
        reg["gguf_todos_arquivos_gerados"] = [str(p.relative_to(TMP / nome)) for p in gerados]
        mf = pasta / "Modelfile"
        reg["modelfile"] = mf.read_text(encoding="utf-8") if mf.exists() else None
        shutil.rmtree(dst, ignore_errors=True)
        gravar()
        return reg
    except Exception:
        reg["erro"] = traceback.format_exc()[-6000:]
        reg["fase_do_erro"] = mon.fase
        gravar()
        raise
    finally:
        mon.parar.set()
        mon.join(timeout=5)
        gravar()


# ---------------------------------------------------------------------------
# orquestrador
# ---------------------------------------------------------------------------

def instalar() -> dict:
    t0 = time.time()
    livre = os.environ.get("ESPECTRO24_UNSLOTH_LIVRE") == "1"
    pacotes = ["unsloth", "unsloth_zoo"] if livre else PACOTES_FIXOS
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", *pacotes],
                       capture_output=True, text=True)
    return {"rc": r.returncode, "s": round(time.time() - t0, 1), "pacotes": pacotes,
            "stderr_fim": r.stderr[-2000:]}


def rodar_um(nome: str, seq: int, timeout_s: int) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, SCRIPT, "--modelo", nome,
                            "--seq", str(seq)], capture_output=True, text=True,
                           timeout=timeout_s)
        rc, err = r.returncode, r.stdout[-3000:] + "\n" + r.stderr[-6000:]
    except subprocess.TimeoutExpired:
        rc, err = "timeout", ""
    log = SAIDA / nome / "log.json"
    reg = json.loads(log.read_text()) if log.exists() else {}
    tl = SAIDA / nome / "linha_do_tempo.jsonl"
    ultimas = tl.read_text().strip().split("\n")[-5:] if tl.exists() else []
    return {"modelo": nome, "seq": seq, "rc": rc, "s": round(time.time() - t0, 1),
            # rc -9 = o kernel do SO matou o processo (OOM de RAM): as últimas
            # amostras da linha do tempo são a evidência
            "morto_pelo_so": rc == -9,
            "oom": "OutOfMemoryError" in err or "CUDA out of memory" in err,
            "linha_do_tempo_fim": ultimas, "log": reg, "saida_fim": err[-4000:]}


def orquestrar(incluir_qwen: bool) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    dataset = _conferir_dataset()            # antes de instalar ou treinar qualquer coisa
    meta = _ler_meta()
    ordem = list(meta.get("candidatos") or (ORDEM + (["qwen3-8b"] if incluir_qwen else [])))
    resumo = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "dataset": dataset, "df_inicio": _df(), "instalacao": instalar(), "ordem": ordem,
              "meta_dataset": meta, "execucoes": []}
    _json(SAIDA / "resumo.json", resumo)
    for nome in ordem:
        try:
            for seq in (SEQ["14336"], SEQ["12288"]):
                ex = rodar_um(nome, seq, timeout_s=4 * 3600)
                # pasta PREVISÍVEL: <modelo>__<seq>, com ou sem erro (o Windows acha
                # as que têm .gguf; o resultado está em log.json)
                destino = SAIDA / f"{nome}__{seq}"
                shutil.rmtree(destino, ignore_errors=True)
                if (SAIDA / nome).exists():
                    shutil.move(str(SAIDA / nome), str(destino))
                ex["pasta"] = destino.name
                resumo["execucoes"].append(ex)
                _json(SAIDA / "resumo.json", resumo)
                if not ex["oom"]:
                    break                       # 12.288 só depois de OOM de VRAM a 14.336
        except Exception:  # noqa: BLE001 — um candidato não derruba o outro
            resumo["execucoes"].append({"modelo": nome, "erro_orquestrador": traceback.format_exc()})
            _json(SAIDA / "resumo.json", resumo)
        shutil.rmtree(TMP / nome, ignore_errors=True)
    resumo["fim"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    resumo["df_fim"] = _df()
    _json(SAIDA / "resumo.json", resumo)


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
    medir_modelo(a.modelo, a.seq)


if __name__ == "__main__":
    main()
