"""Exporta o Qwen3-8B BASE (sem treino) pelo MESMO caminho do modelo treinado.

Fase 2: a linha de base tem de diferir do modelo treinado SÓ pelo adaptador.
Este kernel repete, do `smoke_treino.py` (v4, a que gerou o GGUF importado no
E4), tudo o que leva do repositório ao GGUF, e pula só o treino:

1. mesma pilha: `unsloth`/`unsloth_zoo` 2026.10.7 (fixados), a imagem do Kaggle
   do dia (gravada), T4 única (`CUDA_VISIBLE_DEVICES=0`);
2. mesmo repositório (`unsloth/Qwen3-8B-unsloth-bnb-4bit`) e a MESMA chamada de
   carga (`max_seq_length` 14.336, 4-bit, fp16); aborta se a revisão no HF não
   for a do smoke (`62efd7f9…`);
3. mesmo `get_peft_model` (r=16, alpha 16, dropout 0, as 7 projeções, seed
   3407). O PEFT inicializa `lora_B` com ZEROS: o adaptador recém-criado é a
   identidade. O kernel PROVA isso antes de exportar:
   - `max |lora_B|` = 0 em todos os módulos;
   - a perda e os logits num texto fixo com o adaptador e com
     `disable_adapter()` (igualdade exata esperada);
4. mesmo `get_chat_template(tok, "qwen3")` e a MESMA função de exportação
   (`save_pretrained_gguf(..., quantization_method="q4_k_m")`);
5. depois da exportação, confere a FUSÃO: o Unsloth baixa os shards 16-bit
   originais e funde o LoRA neles (no smoke v4: "Preparing safetensor model
   files" 4/4 e `.cache/huggingface/download/model-0000k-of-00004.safetensors`).
   Cada tensor fundido é comparado com o do shard original (mesmo repositório e
   revisão, baixado à parte): com B = 0 a fusão tem de deixar TODOS iguais;
6. grava o sha256 do GGUF, o tipo e o sha256 de CADA tensor do GGUF
   (`tensores.json`, via `gguf-py` do llama.cpp fixado) e o commit do
   llama.cpp. O llama.cpp é um commit FIXO (`LLAMA_CPP_COMMIT`, o mesmo bloco
   do `treino.py`), compilado do código-fonte ANTES de carregar o modelo; o
   kernel aborta se o compilado não for esse commit, e de novo depois da
   exportação se o Unsloth não tiver usado ESSE llama.cpp. Com os dois
   `tensores.json`, os tensores fora das 7 projeções têm de ser idênticos;
7. (`ESPECTRO24_COMPARAR_BIBLIOTECA`, padrão 1) baixa o Q4_K_M de
   `unsloth/Qwen3-8B-GGUF` — o que o Ollama puxa como
   `hf.co/unsloth/Qwen3-8B-GGUF:Q4_K_M` — e compara tensor a tensor. É a
   evidência de equivalência (ou não) com a biblioteca; NÃO muda a regra: a
   base da Fase 2 sai deste kernel.

Saída (`/kaggle/working/base/qwen3-8b-base__14336/`): `Qwen3-8B.Q4_K_M.gguf`,
`Modelfile` (o do Unsloth; o import no Windows o troca pelo canônico, como no
E4), `log.json`, `tensores.json`. O nome da pasta e o `modelo` do log dão o nome
`espectro-qwen3-8b-base` no `viabilidade_ollama.py importar-pasta`.

Sem dataset: nenhum exemplo de treino, validação ou teste entra aqui.
"""
from __future__ import annotations

import os

SCRIPT = os.path.abspath(__file__)        # antes do chdir abaixo
RASCUNHO = "/tmp/espectro24_base"
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("HF_HOME", f"{RASCUNHO}/hf")
os.environ.setdefault("HF_HUB_CACHE", f"{RASCUNHO}/hf/hub")
os.environ.setdefault("TRITON_CACHE_DIR", f"{RASCUNHO}/triton")
# A prova da identidade compara logits; sem isto o Unsloth devolve logits vazios
# quando há `labels` (versão 1 deste kernel: NotImplementedError). Só aqui: no
# treino materializaria os logits de 12k tokens. Não toca nos pesos exportados.
os.environ["UNSLOTH_RETURN_LOGITS"] = "1"
os.makedirs(RASCUNHO, exist_ok=True)
os.chdir(RASCUNHO)            # llama.cpp e unsloth_compiled_cache nascem no cwd

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

NOME = "qwen3-8b-base"
SEQ = 14336                                   # o do smoke v4 (E1 passou a 14.336)
SAIDA = Path("/kaggle/working/base") / f"{NOME}__{SEQ}"
TMP = Path(RASCUNHO)
SEED = 3407
REPO = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
REVISAO = "62efd7f9d748e394734a7adae2adf96e13a2abc8"     # a do smoke v4 (`repo_confirmado`)
PACOTES_FIXOS = ["unsloth==2026.10.7", "unsloth_zoo==2026.10.7"]
PROJECOES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
REPOS_16BIT = ("unsloth/Qwen3-8B", "Qwen/Qwen3-8B")      # onde procurar a revisão da fusão
REPO_BIBLIOTECA = "unsloth/Qwen3-8B-GGUF"
# Texto fixo (nenhum dado do projeto) para a prova de que o adaptador é identidade.
TEXTO_PROVA = ("As reviews destacam a fotografia, o ritmo lento do segundo ato e a "
               "atuação da protagonista; algumas criticam o final, que acham apressado. "
               "O filme divide o público entre quem vê profundidade e quem vê pretensão.")


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
                "bitsandbytes", "accelerate", "safetensors", "huggingface_hub"):
        try:
            v[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            v[pkg] = None
    v["imagem_kaggle"] = os.environ.get("KAGGLE_DOCKER_IMAGE") or os.environ.get("KAGGLE_IMAGE")
    return v


def _pico_ram_gib() -> float:
    import psutil
    vm = psutil.virtual_memory()
    return round((vm.total - vm.available) / 2**30, 2)


# >>> llama.cpp fixo — bloco IDÊNTICO em exportar_base.py e treino.py (o teste confere)
# ggml-org/llama.cpp, tag b11985 (commit de 2026-10-29): a base upstream da release
# `b11985-mix-c116c32` da fork unslothai/llama.cpp, a mais nova quando o smoke v4
# rodou (2026-10-30). O kernel compila ESTE commit do código-fonte e aponta o
# Unsloth para ele: quantizador e gguf-py (`UNSLOTH_LLAMA_CPP_PATH`) e conversor
# (`UNSLOTH_LLAMA_CPP_SCRIPTS_DIR`). Com `UNSLOTH_AUTO_INSTALL=0`, se o Unsloth não
# aceitar a pasta, a exportação falha em vez de baixar um pré-compilado.
LLAMA_CPP_URL = "https://github.com/ggml-org/llama.cpp"
LLAMA_CPP_COMMIT = "6d194531e1e5876d5d1a0641ce3ca7dae23f94ad"
LLAMA_CPP_DIR = Path(RASCUNHO) / "llama.cpp"
ALVOS_LLAMA = ["llama-quantize", "llama-gguf-split"]
# do que o `install_llama_cpp` do Unsloth instalaria para o conversor, só o que o
# Qwen3 pode usar, e só se faltar (o gguf vem do gguf-py do checkout; o
# mistral_common é só para modelos Mistral)
DEPS_CONVERSOR = {"sentencepiece": "sentencepiece", "google.protobuf": "protobuf"}


def _tem_modulo(nome: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(nome) is not None
    except ModuleNotFoundError:
        return False
os.environ["UNSLOTH_LLAMA_CPP_PATH"] = str(LLAMA_CPP_DIR)
os.environ["UNSLOTH_LLAMA_CPP_SCRIPTS_DIR"] = str(LLAMA_CPP_DIR)
os.environ["UNSLOTH_AUTO_INSTALL"] = "0"


def _commit_compilado(d: Path) -> str | None:
    """O commit que o CMake gravou no build-info do llama.cpp compilado."""
    for p in (d / "build").rglob("build-info.cpp"):
        for linha in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "LLAMA_COMMIT" in linha and '"' in linha:
                return linha.split('"')[1]
    return None


def _confere_commit(d: Path) -> dict:
    head = _rodar(["git", "-C", str(d), "rev-parse", "HEAD"]).stdout.strip()
    curto = _commit_compilado(d)
    q = d / "llama-quantize"
    r = _rodar([str(q), "--help"], timeout=60) if q.exists() else None
    saida = ((r.stdout + r.stderr) if r else "")
    no_binario = q.exists() and (curto or "?").encode() in q.read_bytes()
    fora = {"commit_pedido": LLAMA_CPP_COMMIT, "commit_clonado": head, "commit_compilado": curto,
            "commit_no_binario": no_binario,
            "llama_quantize_sha256": _sha256(q) if q.exists() else None,
            "llama_quantize_versao": next((l for l in saida.splitlines() if l.startswith("version:")), None)}
    fora["ok"] = bool(head == LLAMA_CPP_COMMIT and curto and LLAMA_CPP_COMMIT.startswith(curto)
                      and len(curto) >= 7 and no_binario)
    return fora


def preparar_llama_cpp() -> dict:
    """Clona e compila o llama.cpp em LLAMA_CPP_COMMIT, ANTES de carregar o modelo.
    Aborta se o que compilou não for exatamente esse commit."""
    d = LLAMA_CPP_DIR
    shutil.rmtree(d, ignore_errors=True)
    t0 = time.time()
    passos = [["git", "init", "-q", str(d)],
              ["git", "-C", str(d), "remote", "add", "origin", LLAMA_CPP_URL],
              ["git", "-C", str(d), "fetch", "-q", "--depth", "1", "origin", LLAMA_CPP_COMMIT],
              ["git", "-C", str(d), "checkout", "-q", "--detach", "FETCH_HEAD"],
              ["cmake", "-S", str(d), "-B", str(d / "build"), "-DCMAKE_BUILD_TYPE=Release",
               "-DGGML_CUDA=OFF", "-DLLAMA_OPENSSL=OFF", "-DBUILD_SHARED_LIBS=OFF",
               "-DLLAMA_BUILD_TESTS=OFF", "-DLLAMA_BUILD_EXAMPLES=OFF", "-DLLAMA_BUILD_SERVER=OFF"],
              ["cmake", "--build", str(d / "build"), "--config", "Release", "-j",
               str(os.cpu_count() or 4), "--target", *ALVOS_LLAMA]]
    for p in passos:
        r = _rodar(p, timeout=3600)
        if r.returncode != 0:
            raise SystemExit(f"llama.cpp: `{' '.join(p)}` falhou: {(r.stdout + r.stderr)[-1500:]}")
    for alvo in ALVOS_LLAMA:                       # o Unsloth procura na raiz da pasta
        shutil.copy2(d / "build" / "bin" / alvo, d / alvo)
    faltando = [pip for mod, pip in DEPS_CONVERSOR.items() if not _tem_modulo(mod)]
    if faltando:
        r = _rodar([sys.executable, "-m", "pip", "install", "-q", *faltando])
        if r.returncode != 0:
            raise SystemExit(f"pip install {faltando} falhou: {r.stderr[-1500:]}")
    fora = _confere_commit(d)
    fora.update({"s": round(time.time() - t0, 1), "deps_instaladas": faltando,
                 "cmake": passos[4][5:]})
    print(f"[llama.cpp] {json.dumps(fora, ensure_ascii=False)}", flush=True)
    if not fora["ok"]:
        raise SystemExit(f"llama.cpp compilado não é {LLAMA_CPP_COMMIT}: {fora} — abortado")
    return fora


def conferir_llama_cpp_depois(preparo: dict) -> dict:
    """Depois do `save_pretrained_gguf`: o mesmo checkout, o mesmo binário e nenhum
    llama.cpp baixado pelo Unsloth no lugar padrão."""
    fora = _confere_commit(LLAMA_CPP_DIR)
    padrao = Path.home() / ".unsloth" / "llama.cpp"
    fora["llama_cpp_padrao_do_unsloth_existe"] = padrao.exists()
    fora["mesmo_binario_do_preparo"] = fora["llama_quantize_sha256"] == preparo["llama_quantize_sha256"]
    fora["arvore_alterada"] = _rodar(["git", "-C", str(LLAMA_CPP_DIR), "status", "--porcelain",
                                      "--untracked-files=no"]
                                     ).stdout.splitlines()[:50]
    fora["ok"] = bool(fora["ok"] and fora["mesmo_binario_do_preparo"]
                      and not fora["llama_cpp_padrao_do_unsloth_existe"])
    return fora
# <<< llama.cpp fixo


# ---------------------------------------------------------------------------
# provas
# ---------------------------------------------------------------------------

def prova_adaptador_identidade(model, tok, torch) -> dict:
    """B = 0 em todo LoRA, e a saída com o adaptador = a saída sem ele."""
    b_max, a_norma, n = 0.0, 0.0, 0
    for nome, m in model.named_modules():
        if hasattr(m, "lora_B") and hasattr(m.lora_B, "keys"):
            for k in m.lora_B.keys():
                b_max = max(b_max, float(m.lora_B[k].weight.detach().abs().max()))
                a_norma = max(a_norma, float(m.lora_A[k].weight.detach().abs().max()))
                n += 1
    base = getattr(tok, "tokenizer", tok)
    ids = base(TEXTO_PROVA, return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        com = model(input_ids=ids, labels=ids)
        with model.disable_adapter():
            sem = model(input_ids=ids, labels=ids)
    if com.logits.numel() == 0 or sem.logits.numel() == 0:
        raise SystemExit("logits vazios na prova do adaptador (UNSLOTH_RETURN_LOGITS) — abortado")
    dif = float((com.logits.float() - sem.logits.float()).abs().max())
    return {"modulos_lora": n, "max_abs_lora_B": b_max, "max_abs_lora_A": a_norma,
            "B_zero": b_max == 0.0, "tokens_texto": int(ids.shape[1]),
            "perda_com_adaptador": float(com.loss), "perda_sem_adaptador": float(sem.loss),
            "max_abs_dif_logits": dif, "saida_identica": dif == 0.0}


def _metadata_da_fusao(dst: Path) -> dict:
    """Revisão e etag de cada shard que o Unsloth baixou para fundir."""
    fora = {}
    for m in sorted((dst / ".cache" / "huggingface" / "download").glob("*.safetensors.metadata")):
        linhas = m.read_text(encoding="utf-8").split("\n")
        fora[m.name.removesuffix(".metadata")] = {"revisao": linhas[0].strip(),
                                                  "etag": linhas[1].strip() if len(linhas) > 1 else None}
    return fora


def prova_fusao(dst: Path, torch) -> dict:
    """Cada tensor dos shards FUNDIDOS × o do shard 16-bit original."""
    from huggingface_hub import HfApi, hf_hub_download
    from safetensors import safe_open
    meta = _metadata_da_fusao(dst)
    revs = {v["revisao"] for v in meta.values()}
    if len(revs) != 1:
        return {"ok": False, "erro": f"revisões dos shards: {sorted(revs)}", "metadata": meta}
    rev = revs.pop()
    repo = None
    for r in REPOS_16BIT:
        try:
            if HfApi().model_info(r, revision=rev).sha == rev:
                repo = r
                break
        except Exception:  # noqa: BLE001 — a revisão não é deste repositório
            continue
    if repo is None:
        return {"ok": False, "erro": f"revisão {rev} não achada em {REPOS_16BIT}", "metadata": meta}
    orig_dir = TMP / "orig16"
    fora = {"repo_16bit": repo, "revisao": rev, "metadata": meta, "shards": {}}
    n = iguais = 0
    diferentes = []
    for shard in sorted(meta):
        fundido = dst / shard
        orig = Path(hf_hub_download(repo, shard, revision=rev, cache_dir=str(orig_dir)))
        sha_f, sha_o = _sha256(fundido), _sha256(orig)
        reg = {"sha256_fundido": sha_f, "sha256_original": sha_o, "arquivo_identico": sha_f == sha_o}
        with safe_open(str(fundido), framework="pt") as ff, safe_open(str(orig), framework="pt") as fo:
            kf, ko = set(ff.keys()), set(fo.keys())
            reg["chaves_iguais"] = kf == ko
            for k in sorted(kf & ko):
                a, b = ff.get_tensor(k), fo.get_tensor(k)
                n += 1
                if a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b):
                    iguais += 1
                else:
                    diferentes.append({"tensor": k, "dtype": [str(a.dtype), str(b.dtype)],
                                       "max_abs": (float((a.float() - b.float()).abs().max())
                                                   if a.shape == b.shape else None)})
        fora["shards"][shard] = reg
        orig.unlink(missing_ok=True)
    fora.update({"tensores": n, "iguais": iguais, "diferentes": diferentes[:50],
                 "n_diferentes": len(diferentes),
                 "ok": n > 0 and iguais == n and all(s["chaves_iguais"] for s in fora["shards"].values())})
    return fora


def tensores_gguf(gguf: Path) -> dict:
    """Tipo, forma e sha256 de cada tensor; chaves de metadados (sem os vetores)."""
    sys.path.insert(0, str(LLAMA_CPP_DIR / "gguf-py"))
    from gguf import GGUFReader
    rd = GGUFReader(str(gguf))
    tens = [{"nome": t.name, "tipo": t.tensor_type.name, "forma": [int(x) for x in t.shape],
             "sha256": hashlib.sha256(t.data.tobytes()).hexdigest()} for t in rd.tensors]
    meta = {}
    for k, f in rd.fields.items():
        if k.startswith("tokenizer.ggml.") and k not in ("tokenizer.ggml.model", "tokenizer.ggml.pre"):
            continue                                   # vetores do vocabulário: só a chave
        try:
            v = f.contents()
        except Exception:  # noqa: BLE001
            v = None
        if isinstance(v, str) and len(v) > 200:
            v = {"sha256": hashlib.sha256(v.encode()).hexdigest(), "len": len(v)}
        meta[k] = v
    return {"n_tensores": len(tens), "tensores": tens, "metadados": meta,
            "chaves_metadados": sorted(rd.fields)}


def llama_cpp() -> dict:
    d = LLAMA_CPP_DIR
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


def comparar_biblioteca(meus: dict) -> dict:
    from huggingface_hub import HfApi, hf_hub_download
    info = HfApi().model_info(REPO_BIBLIOTECA, files_metadata=True)
    alvo = [s for s in info.siblings if s.rfilename.lower().endswith("q4_k_m.gguf")
            and "/" not in s.rfilename]
    if len(alvo) != 1:
        return {"ok": False, "erro": f"Q4_K_M na raiz de {REPO_BIBLIOTECA}: {[s.rfilename for s in alvo]}"}
    arq = Path(hf_hub_download(REPO_BIBLIOTECA, alvo[0].rfilename, revision=info.sha,
                               cache_dir=str(TMP / "biblioteca")))
    deles = tensores_gguf(arq)
    a = {t["nome"]: t for t in meus["tensores"]}
    b = {t["nome"]: t for t in deles["tensores"]}
    comuns = sorted(set(a) & set(b))
    tipo_dif = [n for n in comuns if a[n]["tipo"] != b[n]["tipo"]]
    sha_dif = [n for n in comuns if a[n]["sha256"] != b[n]["sha256"]]
    fora = {"repo": REPO_BIBLIOTECA, "revisao": info.sha, "arquivo": alvo[0].rfilename,
            "bytes": arq.stat().st_size, "sha256": _sha256(arq),
            "sha256_lfs_no_hf": getattr(getattr(alvo[0], "lfs", None), "sha256", None),
            "tensores_so_nossos": sorted(set(a) - set(b)), "tensores_so_deles": sorted(set(b) - set(a)),
            "comuns": len(comuns), "tipo_diferente": len(tipo_dif), "sha_diferente": len(sha_dif),
            "exemplos_tipo_diferente": [(n, a[n]["tipo"], b[n]["tipo"]) for n in tipo_dif[:20]],
            "metadados_deles": {k: v for k, v in deles["metadados"].items()
                                if k.startswith(("general.", "quantize."))}}
    fora["quantizacao_identica"] = (not fora["tensores_so_nossos"] and not fora["tensores_so_deles"]
                                    and fora["sha_diferente"] == 0)
    arq.unlink(missing_ok=True)
    return fora


# ---------------------------------------------------------------------------
# exportação
# ---------------------------------------------------------------------------

def exportar() -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    log = SAIDA / "log.json"
    reg = {"modelo": NOME, "repo": REPO, "revisao_esperada": REVISAO, "max_seq_length": SEQ,
           "seed": SEED, "rascunho": RASCUNHO, "treino": "nenhum (adaptador recém-inicializado)"}
    try:
        reg["llama_cpp_preparo"] = preparar_llama_cpp()      # antes do modelo: falha cedo
        _json(log, reg)
        import torch
        from huggingface_hub import HfApi
        import unsloth  # noqa: F401 — tem de vir antes de transformers/trl
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template

        reg.update({"dispositivos_cuda": torch.cuda.device_count(),
                    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    "versoes": _versoes()})
        info = HfApi().model_info(REPO)
        reg["repo_confirmado"] = {"id": info.id, "sha": info.sha}
        if info.sha != REVISAO:
            raise SystemExit(f"{REPO} está em {info.sha}, não em {REVISAO} (a do smoke v4): "
                             f"a base não seria a mesma do treino — abortado")
        t0 = time.time()
        model, tok = FastLanguageModel.from_pretrained(model_name=REPO, max_seq_length=SEQ,
                                                       load_in_4bit=True, dtype=torch.float16)
        reg["carga_s"] = round(time.time() - t0, 1)
        model = FastLanguageModel.get_peft_model(
            model, r=16, lora_alpha=16, lora_dropout=0, bias="none",
            target_modules=PROJECOES, use_gradient_checkpointing="unsloth",
            random_state=SEED)
        reg["modulos_lora"] = sorted({n.split(".")[-1] for n, m in model.named_modules()
                                      if hasattr(m, "lora_A")})
        reg["projecoes_faltando"] = [p for p in PROJECOES if p not in reg["modulos_lora"]]
        tok = get_chat_template(tok, chat_template="qwen3")
        reg["prova_adaptador"] = prova_adaptador_identidade(model, tok, torch)
        _json(log, reg)
        if not reg["prova_adaptador"]["B_zero"]:
            raise SystemExit("lora_B não é zero: o adaptador não é a identidade — abortado")

        dst = TMP / NOME / "gguf"
        shutil.rmtree(dst, ignore_errors=True)
        t0 = time.time()
        model.save_pretrained_gguf(str(dst), tok, quantization_method="q4_k_m")
        reg["gguf_tempo_s"] = round(time.time() - t0, 1)
        reg["pico_ram_depois_da_exportacao_gib"] = _pico_ram_gib()
        reg["gguf_todos_arquivos_gerados"] = [str(p.relative_to(TMP / NOME))
                                              for p in sorted((TMP / NOME).rglob("*")) if p.is_file()]
        reg["llama_cpp"] = llama_cpp()
        reg["llama_cpp_depois"] = conferir_llama_cpp_depois(reg["llama_cpp_preparo"])
        _json(log, reg)
        if not reg["llama_cpp_depois"]["ok"]:
            raise SystemExit(f"a exportação não usou o llama.cpp {LLAMA_CPP_COMMIT}: "
                             f"{reg['llama_cpp_depois']} — GGUF não copiado")

        del model
        torch.cuda.empty_cache()
        reg["prova_fusao"] = prova_fusao(dst, torch)
        _json(log, reg)

        arquivos = []
        for p in sorted((TMP / NOME).rglob("*")):
            if p.is_file() and ((p.suffix == ".gguf" and "Q4_K_M" in p.name.upper())
                                or p.name == "Modelfile"):
                alvo = SAIDA / p.name
                shutil.copy2(p, alvo)
                arquivos.append({"nome": p.name, "bytes": alvo.stat().st_size,
                                 "sha256": _sha256(alvo)})
        reg["gguf_arquivos"] = arquivos
        mf = SAIDA / "Modelfile"
        reg["modelfile"] = mf.read_text(encoding="utf-8") if mf.exists() else None
        ggufs = [SAIDA / a["nome"] for a in arquivos if a["nome"].endswith(".gguf")]
        if len(ggufs) != 1:
            raise SystemExit(f"esperava 1 GGUF Q4_K_M, achei {[g.name for g in ggufs]}")
        tens = tensores_gguf(ggufs[0])
        _json(SAIDA / "tensores.json", tens)
        reg["tensores"] = {"arquivo": "tensores.json", "n": tens["n_tensores"],
                           "sha256": _sha256(SAIDA / "tensores.json"),
                           "tipos": {t: sum(1 for x in tens["tensores"] if x["tipo"] == t)
                                     for t in sorted({x["tipo"] for x in tens["tensores"]})}}
        reg["gguf_ok"] = True
        _json(log, reg)
        shutil.rmtree(dst, ignore_errors=True)
        if os.environ.get("ESPECTRO24_COMPARAR_BIBLIOTECA", "1") == "1":
            try:
                reg["biblioteca"] = comparar_biblioteca(tens)
            except Exception as e:  # noqa: BLE001 — a comparação não invalida a exportação
                reg["biblioteca"] = {"ok": False, "erro": f"{type(e).__name__}: {e}"[:2000]}
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
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    resumo = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "instalacao": instalar()}
    _json(SAIDA.parent / "resumo.json", resumo)
    t0 = time.time()
    try:
        r = _rodar([sys.executable, SCRIPT, "--exportar"], timeout=4 * 3600)
        resumo.update({"rc": r.returncode, "saida_fim": (r.stdout or "")[-4000:] + "\n"
                       + (r.stderr or "")[-6000:]})
    except subprocess.TimeoutExpired:
        resumo["rc"] = "timeout"
    resumo["s"] = round(time.time() - t0, 1)
    resumo["fim"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _json(SAIDA.parent / "resumo.json", resumo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exportar", action="store_true", help="(subprocesso) carrega e exporta")
    a, _ = ap.parse_known_args()
    if a.exportar:
        exportar()
    else:
        orquestrar()


if __name__ == "__main__":
    main()
