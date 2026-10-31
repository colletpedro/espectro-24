"""Fase 0 do fine-tuning — (d) viabilidade de inferência dos candidatos no Ollama.

**Rodar no Windows, FORA do Claude Code** (o script recusa se `CLAUDECODE`
estiver no ambiente). Não julga qualidade: mede se o GGUF carrega pelo MESMO
caminho do final (GGUF do Hugging Face importado no Ollama, `hf.co/...`), com o
prompt de síntese de UM filme de TREINO de tamanho perto do p90 e o `num_ctx`
de inferência do inventário, e grava:

- tempo total, leitura do prompt, geração, carga (`local_ollama`);
- tokens/s de leitura e de geração;
- pico de RAM livre/usada do sistema, pico do working set dos processos do
  Ollama e pico de VRAM (`nvidia-smi`, se houver);
- se o texto devolvido parseia como o JSON da síntese
  (`synthesize._parse_llm_json`, e se tem `temas` em lista).

PARTIDA LIMPA (2026-10-22). A 1ª medição do Qwen3-8B (20/10) começou sem memória
livre porque o candidato anterior não tinha sido descarregado. Agora, ANTES de
cada medição: `ollama stop` em todo modelo listado por `ollama ps`, confirmação
de que `ollama ps` ficou VAZIO, reinício do servidor e espera (até
`--espera-ram-s`) pela RAM livre voltar a `--ram-partida-min-gb`; a RAM livre
de partida vai para o registro (`partida`). Se a RAM não voltar, a medição NÃO
roda (`partida_contaminada`): um número medido sobre memória ocupada por outro
modelo não vale.

O Ollama é REINICIADO antes de cada candidato (o script mata `ollama.exe` /
`ollama app.exe` e sobe `ollama serve` próprio, com `OLLAMA_NUM_PARALLEL=1`).
Guarda de memória: se a RAM livre ficar abaixo de `--ram-livre-min-gb`
durante a chamada, o servidor é derrubado e o candidato sai como
`abortado_por_memoria`.

O filme sai de `finetune/split.json`: o script RECUSA filme que não seja de
treino. Nada é escrito em `resultado/`.

Candidatos (gate 0, decisão 7): Gemma 4 12B, Gemma 4 E4B, Qwen3-8B (reserva).
Critério: `finetune/CRITERIO_ESCOLHA_BASE.md` (E4, E5; o probe a 27.648 não é
eliminatório).

Subcomandos:
    baixar      — `ollama pull` dos GGUF (e, com --fallback-biblioteca, das tags)
    medir       — a medição a 18.432 + o probe de memória a 27.648 (mesmo
                  prompt de treino p90); grava `finetune/viabilidade/<data>.json`
    importar    — GGUF + Modelfile exportados no Kaggle: confere o TEMPLATE
                  contra o template do HF com raciocínio desligado (corrige e
                  registra se não reproduzir), `ollama create`, confere a
                  contagem de tokens do prompt e mede como em `medir`
    importar-pasta — percorre uma pasta de saída do Kaggle, ACHA as subpastas
                  que têm `.gguf` Q4_K_M + `Modelfile` (sem supor o nome da
                  pasta) e roda `importar` em cada uma
"""
from __future__ import annotations

import argparse
import ctypes
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401  (localhost passa; nenhuma API paga)
import comum as K  # noqa: E402

# O caminho FINAL: GGUF do Hugging Face importado pelo Ollama. A tag da
# biblioteca do Ollama só entra com --fallback-biblioteca.
CANDIDATOS = {
    "Gemma-4-12B": {"hf": "hf.co/unsloth/gemma-4-12b-it-GGUF:Q4_K_M",
                    "biblioteca": "gemma4:12b-it-q4_K_M", "gguf_gb": 7.12},
    "Gemma-4-E4B": {"hf": "hf.co/unsloth/gemma-4-E4B-it-GGUF:Q4_K_M",
                    "biblioteca": "gemma4:e4b-it-q4_K_M", "gguf_gb": 4.98},
    "Qwen3-8B": {"hf": "hf.co/unsloth/Qwen3-8B-GGUF:Q4_K_M",
                 "biblioteca": "qwen3:8b", "gguf_gb": 5.03},
}
# Filme de TREINO no p90 da entrada da síntese (inventário: p90 = 7.771 tokens
# no Qwen, 7.817 no Gemma; este bucket tem 7.770 / 7.817).
PAR_PADRAO = "do-the-right-thing/negativas"
# `num_ctx` de inferência (inventário, PROPOSTO): (maior entrada fora o outlier
# 13.159 + teto de saída de produção 3.000) × 1,10, em múltiplo de 1024.
NUM_CTX_PADRAO = 18432
NUM_CTX_MAXIMO = 27648      # cobre o outlier (500-days-of-summer/positivas)
NUM_PREDICT = 3000          # = LLM_MAX_TOKENS da síntese de produção
PROBE_NUM_PREDICT = 16      # o probe só mede carga, memória e tempo
E5_LIMITE_S = 20 * 60       # E5: o prompt p90 a 18.432 termina em ≤ 20 min
# Partida limpa (PROPOSTO): a 1ª rodada fechou com 1,05–4,92 GB livres de mínimo
# numa máquina de 15,2 GB; um ponto de partida abaixo de 6 GB livres já é metade
# do notebook ocupada por outra coisa.
RAM_PARTIDA_MIN_GB = 6.0
ESPERA_RAM_S = 90.0
URL = "http://127.0.0.1:11434"


# ---------------------------------------------------------------------------
# memória
# ---------------------------------------------------------------------------

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def ram_gb() -> tuple[float, float]:
    """(total, livre) em GB. Windows via GlobalMemoryStatusEx; outro SO, os.sysconf."""
    if os.name == "nt":
        st = _MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(st)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return st.ullTotalPhys / 2**30, st.ullAvailPhys / 2**30
    pag = os.sysconf("SC_PAGE_SIZE")
    total = os.sysconf("SC_PHYS_PAGES") * pag / 2**30
    try:
        return total, os.sysconf("SC_AVPHYS_PAGES") * pag / 2**30
    except ValueError:      # macOS não tem SC_AVPHYS_PAGES: a guarda não vale aqui
        return total, total


def ws_ollama_gb() -> float | None:
    """Soma do working set dos processos ollama* (tasklist)."""
    if os.name != "nt":
        return None
    try:
        out = K.rodar_texto(["tasklist", "/FO", "CSV", "/NH"], timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    kb = 0
    for ln in out.splitlines():
        cols = [c.strip('"') for c in ln.split('","')]
        if cols and cols[0].lower().startswith("ollama"):
            kb += int("".join(ch for ch in cols[-1] if ch.isdigit()) or 0)
    return kb / 2**20


def vram_gb() -> float | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = K.rodar_texto(["nvidia-smi", "--query-gpu=memory.used",
                             "--format=csv,noheader,nounits"], timeout=10).stdout
        return sum(float(x) for x in out.split()) / 1024
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


class Monitor(threading.Thread):
    def __init__(self, ram_livre_min_gb: float, ao_estourar):
        super().__init__(daemon=True)
        self.min, self.ao_estourar = ram_livre_min_gb, ao_estourar
        self.parar = threading.Event()
        self.pico = {"ram_usada_gb": 0.0, "ram_livre_min_gb": 1e9,
                     "ws_ollama_gb": 0.0, "vram_gb": None}
        self.estourou = False

    def run(self):
        total, _ = ram_gb()
        while not self.parar.is_set():
            _, livre = ram_gb()
            self.pico["ram_usada_gb"] = max(self.pico["ram_usada_gb"], total - livre)
            self.pico["ram_livre_min_gb"] = min(self.pico["ram_livre_min_gb"], livre)
            ws = ws_ollama_gb()
            if ws is not None:
                self.pico["ws_ollama_gb"] = max(self.pico["ws_ollama_gb"], ws)
            v = vram_gb()
            if v is not None:
                self.pico["vram_gb"] = max(self.pico["vram_gb"] or 0.0, v)
            if livre < self.min and not self.estourou:
                self.estourou = True
                self.ao_estourar()
            self.parar.wait(0.5)


# ---------------------------------------------------------------------------
# servidor
# ---------------------------------------------------------------------------

def matar_ollama() -> None:
    if os.name == "nt":
        for im in ("ollama app.exe", "ollama.exe", "ollama_llama_server.exe"):
            subprocess.run(["taskkill", "/F", "/IM", im], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
    time.sleep(3)


def subir_ollama() -> subprocess.Popen:
    env = {**os.environ, "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_HOST": "127.0.0.1:11434"}
    p = subprocess.Popen(["ollama", "serve"], env=env, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    import requests
    for _ in range(60):
        try:
            if requests.get(f"{URL}/api/version", timeout=2).ok:
                return p
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("ollama serve não respondeu em 60 s")


def ollama_ps() -> list[str] | None:
    """Nomes dos modelos carregados (`ollama ps`); None se o servidor não responde."""
    try:
        r = K.rodar_texto(["ollama", "ps"], timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    linhas = [ln for ln in r.stdout.splitlines() if ln.strip()]
    return [ln.split()[0] for ln in linhas[1:]]          # a 1ª linha é o cabeçalho


def partida_limpa(ram_partida_min_gb: float, espera_ram_s: float) -> dict:
    """Descarrega TUDO, confirma `ollama ps` vazio, reinicia o servidor e espera a
    RAM livre voltar. Devolve o registro da partida (`limpa` = pode medir)."""
    reg: dict = {"ram_partida_min_gb": ram_partida_min_gb}
    # Servidor PRÓPRIO antes de qualquer `ollama ps`: sem servidor o CLI tenta subir
    # um, que herda o pipe de captura e pendura o `subprocess.run` (travou 1 h em
    # 22/10, sem nada na tela depois do cabeçalho).
    matar_ollama()
    proprio = subir_ollama()
    reg["ps_antes"] = ollama_ps() or []
    for nome in reg["ps_antes"]:
        subprocess.run(["ollama", "stop", nome], capture_output=True, timeout=120)
    t0 = time.time()
    while ollama_ps() and time.time() - t0 < 60:
        time.sleep(1)
    reg["ps_depois_do_stop"] = ollama_ps() or []
    reg["ps_vazio"] = not reg["ps_depois_do_stop"]
    if proprio is not None:
        proprio.terminate()
    matar_ollama()                          # servidor e runners fora: o resto é do cache do SO
    _, livre = ram_gb()
    t0 = time.time()
    while livre < ram_partida_min_gb and time.time() - t0 < espera_ram_s:
        time.sleep(2)
        _, livre = ram_gb()
    reg.update({"ram_livre_partida_gb": round(livre, 2), "espera_ram_s": round(time.time() - t0, 1),
                "ws_ollama_partida_gb": ws_ollama_gb(), "vram_partida_gb": vram_gb(),
                "limpa": reg["ps_vazio"] and livre >= ram_partida_min_gb})
    return reg


def versao_ollama() -> str:
    try:
        return K.rodar_texto(["ollama", "--version"], timeout=20).stdout.strip()
    except OSError as e:
        raise SystemExit(f"`ollama` não está no PATH: {e}")


# ---------------------------------------------------------------------------
# medição
# ---------------------------------------------------------------------------

def par_de_treino(par: str, split: Path) -> tuple[str, str, str, str]:
    slug, bucket = par.split("/")
    sp = K.ler_json(split)
    if slug not in sp["treino"]:
        raise SystemExit(f"{slug} não é de TREINO em {split} — a viabilidade não usa "
                         f"filme de teste nem de validação")
    pub = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
    b = {x.nome: x for x in K.buckets_remontados(slug, pub)}[bucket]
    s, u = K.prompt_sintese(b)
    return slug, bucket, s, u


def medir_um(nome: str, ref: str, system: str, user: str, num_ctx: int,
             ram_min: float, num_predict: int = NUM_PREDICT, tipo: str = "medicao",
             ram_partida_min_gb: float = RAM_PARTIDA_MIN_GB,
             espera_ram_s: float = ESPERA_RAM_S) -> dict:
    """`tipo="probe"`: mesmo prompt, `num_predict` curto — mede só se carrega,
    o pico de memória e o tempo na janela pedida."""
    from espectro24.local_ollama import LLMLocalFalhou, resposta_json_local
    from espectro24.synthesize import _parse_llm_json

    partida = partida_limpa(ram_partida_min_gb, espera_ram_s)
    reg = {"tipo": tipo, "candidato": nome, "modelo": ref, "num_ctx": num_ctx,
           "num_predict": num_predict, "partida": partida,
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    print(f"   partida: ps antes {partida['ps_antes']} · ps vazio {partida['ps_vazio']} · "
          f"RAM livre {partida['ram_livre_partida_gb']} GB", flush=True)
    if not partida["limpa"]:
        reg.update({"ok": False, "partida_contaminada": True, "abortado_por_memoria": False,
                    "erro": "partida contaminada: o `ollama ps` não esvaziou ou a RAM livre não "
                            f"voltou a {ram_partida_min_gb} GB — feche o que ocupa memória e "
                            "rode de novo; NENHUMA medição foi feita"})
        if tipo == "medicao":
            reg["E5_ate_20_min"] = None          # não medido (≠ reprovado)
        return reg
    srv = subir_ollama()
    mon = Monitor(ram_min, ao_estourar=matar_ollama)
    mon.start()
    t0 = time.time()
    try:
        r = resposta_json_local(system, user, estagio="sintese", modelo=ref, schema="json",
                                prazo=3600, num_predict=num_predict, num_ctx=num_ctx,
                                think="false")
        reg.update({k: r.get(k) for k in ("modelo_efetivo", "finish_reason", "latencia_s",
                                          "leitura_prompt_s", "geracao_s", "carga_s", "total_s",
                                          "prompt_eval_count", "eval_count", "think")})
        g, lp = r.get("geracao_s") or 0, r.get("leitura_prompt_s") or 0
        reg["tokens_s_geracao"] = round(r["eval_count"] / g, 2) if g else None
        reg["tokens_s_leitura"] = round(r["prompt_eval_count"] / lp, 2) if lp else None
        reg["gerou_texto"] = bool((r.get("texto") or "").strip())
        if tipo == "medicao":
            # observação, NÃO critério: JSON inválido de modelo não treinado
            # não elimina ninguém (CRITERIO_ESCOLHA_BASE.md)
            try:
                d = _parse_llm_json(r["texto"])
                reg["json_parseia"] = True
                reg["json_tem_temas_em_lista"] = isinstance(d.get("temas"), list)
                reg["n_temas"] = len(d.get("temas") or [])
            except ValueError as e:
                reg["json_parseia"] = False
                reg["erro_json"] = str(e)[:200]
            reg["texto"] = r["texto"]
        reg["ok"] = True
    except LLMLocalFalhou as e:
        reg.update({"ok": False, "erro": str(e)[:500], "latencia_s": e.latencia_s})
    finally:
        mon.parar.set()
        mon.join(timeout=5)
        reg["parede_s"] = round(time.time() - t0, 1)
        reg["memoria"] = {k: (round(v, 2) if isinstance(v, float) else v)
                          for k, v in mon.pico.items()}
        reg["abortado_por_memoria"] = mon.estourou
        if tipo == "medicao":
            reg["E5_ate_20_min"] = bool(reg.get("ok")) and reg["parede_s"] <= E5_LIMITE_S
        srv.terminate()
        matar_ollama()
    return reg


def _medir_e_sondar(nome: str, ref: str, s: str, u: str, a) -> list[dict]:
    regs = []
    partida = dict(ram_partida_min_gb=a.ram_partida_min_gb, espera_ram_s=a.espera_ram_s)
    if not getattr(a, "so_probe", False):
        print(f"-- {nome} · {ref} · num_ctx {a.num_ctx}", flush=True)
        regs.append(medir_um(nome, ref, s, u, a.num_ctx, a.ram_livre_min_gb, **partida))
        _resumo(regs[-1])
    if not a.sem_probe:
        print(f"-- {nome} · {ref} · PROBE num_ctx {NUM_CTX_MAXIMO}", flush=True)
        regs.append(medir_um(nome, ref, s, u, NUM_CTX_MAXIMO, a.ram_livre_min_gb,
                             num_predict=PROBE_NUM_PREDICT, tipo="probe", **partida))
        _resumo(regs[-1])
    return regs


def _resumo(reg: dict) -> None:
    print({k: reg.get(k) for k in ("tipo", "ok", "gerou_texto", "json_parseia", "parede_s",
                                   "E5_ate_20_min", "tokens_s_leitura", "tokens_s_geracao",
                                   "abortado_por_memoria", "partida_contaminada", "memoria",
                                   "erro")}, flush=True)


def _cabecalho(a) -> tuple[dict, str, str]:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    versao = versao_ollama()
    total, livre = ram_gb()
    slug, bucket, s, u = par_de_treino(a.par, a.split)
    print(f"{versao} · RAM {total:.1f} GB ({livre:.1f} livres) · {slug}/{bucket}", flush=True)
    return ({"gerado_por": "scripts/finetune/viabilidade_ollama.py", "ollama": versao,
             "ram_total_gb": round(total, 2), "par": f"{slug}/{bucket}",
             "chars_system": len(s), "chars_user": len(u),
             "system_sha256": K.sha256_texto(s), "user_sha256": K.sha256_texto(u),
             "ram_livre_min_gb": a.ram_livre_min_gb,
             "ram_partida_min_gb": a.ram_partida_min_gb, "medicoes": []}, s, u)


def _gravar(saida: dict, pasta: Path, prefixo: str) -> None:
    destino = pasta / f"{prefixo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if K.RESULTADO_DIR.resolve() in destino.resolve().parents:
        raise SystemExit("saída dentro de resultado/ é proibida")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado: {destino}")


def cmd_baixar(a) -> None:
    print(versao_ollama())
    refs = [c["hf"] for c in CANDIDATOS.values()]
    if a.fallback_biblioteca:
        refs += [c["biblioteca"] for c in CANDIDATOS.values()]
    for ref in refs:
        print(f"ollama pull {ref}", flush=True)
        subprocess.run(["ollama", "pull", ref], check=False)


def cmd_medir(a) -> None:
    saida, s, u = _cabecalho(a)
    for nome in a.candidato or list(CANDIDATOS):
        refs = [CANDIDATOS[nome]["hf"]] + ([CANDIDATOS[nome]["biblioteca"]]
                                           if a.fallback_biblioteca else [])
        for ref in refs:
            saida["medicoes"] += _medir_e_sondar(nome, ref, s, u, a)
    _gravar(saida, a.saida, "viabilidade")


# ---------------------------------------------------------------------------
# importar o GGUF ajustado no Kaggle
# ---------------------------------------------------------------------------

# O template do HF com o raciocínio DESLIGADO, em Go template do Ollama — o
# mesmo texto que `comum.chat` monta (o BOS do Gemma entra pelo tokenizer do
# GGUF, não pelo template).
TEMPLATES = {
    "gemma": (
        '{{- range .Messages }}'
        '{{- if eq .Role "system" }}<|turn>system\n{{ .Content }}<turn|>\n'
        '{{ else if eq .Role "user" }}<|turn>user\n{{ .Content }}<turn|>\n'
        '{{ else if eq .Role "assistant" }}<|turn>model\n{{ .Content }}<turn|>\n'
        '{{ end }}{{- end }}<|turn>model\n'),
    "qwen": (
        '{{- range .Messages }}'
        '{{- if eq .Role "system" }}<|im_start|>system\n{{ .Content }}<|im_end|>\n'
        '{{ else if eq .Role "user" }}<|im_start|>user\n{{ .Content }}<|im_end|>\n'
        '{{ else if eq .Role "assistant" }}<|im_start|>assistant\n{{ .Content }}<|im_end|>\n'
        '{{ end }}{{- end }}<|im_start|>assistant\n<think>\n\n</think>\n\n'),
}
PARADAS = {"gemma": ["<turn|>"], "qwen": ["<|im_end|>"]}


def _template_do_modelfile(texto: str) -> str | None:
    m = re.search(r'^TEMPLATE\s+"""(.*?)"""', texto, re.S | re.M)
    if m:
        return m.group(1)
    m = re.search(r'^TEMPLATE\s+"(.*?)"\s*$', texto, re.M)
    return m.group(1) if m else None


def conferir_e_corrigir_modelfile(modelfile: Path, gguf: Path, familia: str) -> tuple[str, dict]:
    """Devolve (Modelfile a usar, registro). O TEMPLATE do Unsloth é aceito se
    for, sem espaços nas pontas, o canônico; senão o Modelfile é REESCRITO com
    o canônico (e as paradas), e o diff fica no registro."""
    original = modelfile.read_text(encoding="utf-8")
    tpl = _template_do_modelfile(original)
    canon = TEMPLATES[familia]
    igual = tpl is not None and tpl.strip() == canon.strip()
    reg = {"modelfile_original": original, "template_original": tpl,
           "template_canonico": canon, "template_reproduz_hf": igual}
    if igual:
        usado = re.sub(r"^FROM\s+.*$", f"FROM {gguf.resolve()}", original, count=1, flags=re.M)
    else:
        linhas = [f"FROM {gguf.resolve()}", f'TEMPLATE """{canon}"""']
        linhas += [f'PARAMETER stop "{p}"' for p in PARADAS[familia]]
        usado = "\n".join(linhas) + "\n"
        reg["correcao"] = "".join(difflib.unified_diff(
            (tpl or "").splitlines(keepends=True), canon.splitlines(keepends=True),
            "template_unsloth", "template_canonico"))
    reg["modelfile_usado"] = usado
    return usado, reg


def contagem_template(nome_ollama: str, familia: str, s: str, u: str) -> dict:
    """Prova de comportamento: o prompt que o Ollama monta pelo TEMPLATE e o
    texto cru esperado (`comum.chat`, sem o `<bos>`, que o GGUF acrescenta)
    têm de dar o mesmo `prompt_eval_count`."""
    import requests
    srv = subir_ollama()
    try:
        op = {"num_predict": 1, "num_ctx": NUM_CTX_PADRAO, "seed": 0}
        r1 = requests.post(f"{URL}/api/chat", timeout=3600, json={
            "model": nome_ollama, "stream": False, "think": False, "options": op,
            "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}]}).json()
        cru = K.chat(familia, s, u, None).removeprefix("<bos>")
        r2 = requests.post(f"{URL}/api/generate", timeout=3600, json={
            "model": nome_ollama, "stream": False, "raw": True, "prompt": cru,
            "options": op}).json()
        a_, b_ = r1.get("prompt_eval_count"), r2.get("prompt_eval_count")
        return {"tokens_via_template": a_, "tokens_cru_esperado": b_,
                "iguais": a_ is not None and a_ == b_,
                "erro": r1.get("error") or r2.get("error")}
    finally:
        srv.terminate()
        matar_ollama()


def modelo_existe(nome: str) -> bool:
    """`ollama show` devolve 0 só se o modelo existe (servidor já no ar)."""
    return K.rodar_texto(["ollama", "show", nome], timeout=60).returncode == 0


def remover_modelo(nome: str) -> dict:
    """`ollama rm` antes do `create`: a medição não pode herdar um modelo de mesmo
    nome deixado por uma tentativa anterior (o import de 30/10 caiu depois de
    criar). Aborta se o modelo continuar existindo."""
    existia = modelo_existe(nome)
    reg = {"existia": existia}
    if existia:
        r = K.rodar_texto(["ollama", "rm", nome], timeout=120)
        reg.update({"rm_rc": r.returncode, "rm_saida": (r.stdout + r.stderr)[-500:]})
        if modelo_existe(nome):
            raise SystemExit(f"`ollama rm {nome}` não removeu o modelo: {reg['rm_saida']}")
    return reg


def cmd_importar(a) -> None:
    saida, s, u = _cabecalho(a)
    gguf, mf = Path(a.gguf), Path(a.modelfile)
    if not gguf.exists() or not mf.exists():
        raise SystemExit(f"GGUF ou Modelfile ausente: {gguf} / {mf}")
    usado, reg = conferir_e_corrigir_modelfile(mf, gguf, a.familia)
    reg.update({"gguf": str(gguf), "gguf_sha256": K.sha256_arquivo(gguf),
                "gguf_bytes": gguf.stat().st_size, "nome_ollama": a.nome})
    print("TEMPLATE reproduz o do HF:" if reg["template_reproduz_hf"]
          else "TEMPLATE CORRIGIDO (diff no registro):", reg["template_reproduz_hf"], flush=True)
    arq_mf = a.saida / f"Modelfile.{a.nome}"
    arq_mf.parent.mkdir(parents=True, exist_ok=True)
    arq_mf.write_text(usado, encoding="utf-8")
    matar_ollama()
    srv = subir_ollama()
    try:
        reg["recriado_do_zero"] = remover_modelo(a.nome)
        t0 = time.time()
        c = K.rodar_texto(["ollama", "create", a.nome, "-f", str(arq_mf)])
        reg["create"] = {"rc": c.returncode, "s": round(time.time() - t0, 1),
                         "stderr_fim": c.stderr[-2000:]}
    except Exception as e:
        # Falha do SCRIPT, não do modelo: o registro sai gravado e o E4 fica
        # sem valor (None), para não contar como reprovação.
        saida.update({"importacao": reg, "E4_importa_e_gera": None,
                      "erro_do_script": f"{type(e).__name__}: {e}"})
        _gravar(saida, a.saida, f"importar_{a.nome}")
        raise
    finally:
        srv.terminate()
        matar_ollama()
    saida["importacao"] = reg
    if reg["create"]["rc"] != 0:
        saida["E4_importa_e_gera"] = False
        _gravar(saida, a.saida, f"importar_{a.nome}")
        raise SystemExit(f"ollama create falhou: {reg['create']['stderr_fim'][-400:]}")
    saida["contagem_template"] = contagem_template(a.nome, a.familia, s, u)
    saida["medicoes"] += _medir_e_sondar(a.nome, a.nome, s, u, a)
    m = saida["medicoes"][0]
    saida["E4_importa_e_gera"] = bool(m.get("ok") and m.get("gerou_texto"))
    _gravar(saida, a.saida, f"importar_{a.nome}")


def achar_exportacoes(raiz: Path) -> list[dict]:
    """Subpastas de `raiz` (em qualquer profundidade) que têm um `.gguf` Q4_K_M E um
    `Modelfile` — sem supor o nome da pasta (o smoke grava `<modelo>__<seq>`, mas
    o que vale é haver o arquivo). Família: do `modelo` do `log.json` ao lado,
    senão do nome da pasta."""
    achados = []
    for d in sorted({g.parent for g in Path(raiz).rglob("*.gguf")}):
        ggufs = [g for g in sorted(d.glob("*.gguf")) if "q4_k_m" in g.name.lower()]
        if not ggufs or not (d / "Modelfile").exists():
            continue
        modelo = ""
        if (d / "log.json").exists():
            try:
                modelo = str(json.loads((d / "log.json").read_text(encoding="utf-8")).get("modelo", ""))
            except ValueError:
                pass
        base = (modelo or d.name).lower()
        familia = "qwen" if base.startswith("qwen") else "gemma" if base.startswith("gemma") else None
        nome = re.sub(r"[^a-z0-9.-]+", "-", (modelo or d.name).lower()).strip("-")
        achados.append({"pasta": d, "gguf": ggufs[0], "modelfile": d / "Modelfile",
                        "familia": familia, "nome": f"espectro-{nome}"})
    return achados


def cmd_importar_pasta(a) -> None:
    achados = achar_exportacoes(a.pasta)
    print(f"{len(achados)} exportação(ões) com .gguf Q4_K_M + Modelfile em {a.pasta}:")
    for x in achados:
        print(f"  {x['pasta']} → {x['gguf'].name} · família {x['familia']} · {x['nome']}")
    if not achados:
        raise SystemExit(f"nenhuma pasta com .gguf Q4_K_M e Modelfile em {a.pasta} — o "
                         f"download do `kaggle kernels output` terminou? a exportação falhou "
                         f"(veja gguf_erro no log.json)?")
    sem_familia = [x for x in achados if x["familia"] is None]
    if sem_familia:
        raise SystemExit(f"família desconhecida (nem o log.json nem o nome da pasta dizem): "
                         f"{[str(x['pasta']) for x in sem_familia]}")
    for x in achados:
        print(f"\n== importando {x['pasta']}", flush=True)
        cmd_importar(argparse.Namespace(**{**vars(a), "gguf": x["gguf"], "modelfile": x["modelfile"],
                                           "familia": x["familia"], "nome": x["nome"]}))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baixar")
    b.add_argument("--fallback-biblioteca", action="store_true")

    def comuns(p):
        p.add_argument("--par", default=PAR_PADRAO)
        p.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
        p.add_argument("--num-ctx", type=int, default=NUM_CTX_PADRAO)
        p.add_argument("--sem-probe", action="store_true",
                       help=f"não roda o probe de memória com num_ctx {NUM_CTX_MAXIMO}")
        p.add_argument("--ram-livre-min-gb", type=float, default=2.0,
                       help="guarda DURANTE a chamada: derruba o servidor abaixo disto "
                            "(0 desliga; a guarda já derrubou as sondas de 27.648 de 20/10)")
        p.add_argument("--ram-partida-min-gb", type=float, default=RAM_PARTIDA_MIN_GB,
                       help="RAM livre exigida DEPOIS de descarregar tudo, antes de medir")
        p.add_argument("--espera-ram-s", type=float, default=ESPERA_RAM_S)
        p.add_argument("--saida", type=Path, default=K.FINETUNE_DIR / "viabilidade")

    m = sub.add_parser("medir")
    comuns(m)
    m.add_argument("--candidato", action="append", choices=list(CANDIDATOS))
    m.add_argument("--fallback-biblioteca", action="store_true")
    m.add_argument("--so-probe", action="store_true",
                   help=f"só o probe de memória com num_ctx {NUM_CTX_MAXIMO} (não repete a medição)")
    i = sub.add_parser("importar", help="GGUF + Modelfile do Kaggle → ollama create → mede")
    comuns(i)
    i.add_argument("--gguf", required=True)
    i.add_argument("--modelfile", required=True)
    i.add_argument("--familia", choices=list(TEMPLATES), required=True)
    i.add_argument("--nome", required=True, help="nome do modelo no Ollama")
    ip = sub.add_parser("importar-pasta", help="acha as pastas do Kaggle que têm .gguf e importa cada uma")
    comuns(ip)
    ip.add_argument("--pasta", type=Path, required=True,
                    help="a saída baixada do Kaggle (a pasta que contém `<modelo>__<seq>/`)")
    a = ap.parse_args()
    {"baixar": cmd_baixar, "medir": cmd_medir, "importar": cmd_importar,
     "importar-pasta": cmd_importar_pasta}[a.cmd](a)


if __name__ == "__main__":
    main()
