"""[2026-10-30] Fine-tuning: a saída de texto dos subprocessos (ollama, git,
nvidia-smi, tasklist) é lida em UTF-8 com `errors="replace"`, sem depender do
locale, e `stdout`/`stderr` nunca voltam None.

No Windows, o `importar-pasta` caiu com UnicodeDecodeError 'charmap' (cp1252,
byte 0x8f) na thread de leitura do `ollama create`, e depois com TypeError
(`c.stderr[-2000:]` com stderr None). Também aqui: o import recria o modelo do
zero (`ollama rm` antes do `create`) e grava o registro quando o SCRIPT cai.
E o `comum.chat` do Qwen3 não apara o conteúdo do usuário (v4 do smoke)."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FINETUNE = RAIZ / "scripts" / "finetune"
sys.path.insert(0, str(FINETUNE))

import comum as K  # noqa: E402

# 0x81, 0x8d, 0x8f, 0x90 e 0x9d não existem no cp1252; o resto é o spinner e um
# acento em UTF-8, como o `ollama create` imprime.
BYTES_FORA_DO_CP1252 = b"\x8f\x81\x9d pulling \xe2\xa0\x8b \xe2\xa0\x99 ol\xc3\xa1\n"
FILHO = ("import sys; b = %r; sys.stdout.buffer.write(b); sys.stderr.buffer.write(b)"
         % BYTES_FORA_DO_CP1252)


def _env_sem_chaves() -> dict:
    return {k: v for k, v in os.environ.items()
            if not k.endswith("_API_KEY") and k != "GOOGLE_API_KEY"}


def test_o_modo_antigo_cai_com_estes_bytes():
    # controle: com o cp1252 (o padrão do Windows), a leitura cai — o teste
    # abaixo exercita o defeito de verdade
    with pytest.raises(UnicodeDecodeError):
        subprocess.run([sys.executable, "-c", FILHO], capture_output=True, text=True,
                       encoding="cp1252")


def test_rodar_texto_le_bytes_fora_do_cp1252_sem_cair():
    r = K.rodar_texto([sys.executable, "-c", FILHO])
    assert r.returncode == 0
    for saida in (r.stdout, r.stderr):
        assert isinstance(saida, str)
        assert "pulling ⠋ ⠙ olá" in saida
        assert "�" in saida                     # os bytes inválidos viram U+FFFD
    assert r.stderr[-2000:]                          # o fatiamento que deu TypeError


def test_rodar_texto_sem_captura_devolve_texto_vazio_e_nao_none():
    r = K.rodar_texto([sys.executable, "-c", "pass"], capture_output=False,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert (r.stdout, r.stderr) == ("", "")


def _chamadas_de_subprocess(arvore):
    for no in ast.walk(arvore):
        if (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and isinstance(no.func.value, ast.Name) and no.func.value.id == "subprocess"
                and no.func.attr in {"run", "Popen", "check_output", "call", "check_call"}):
            yield no


def test_nenhum_script_de_finetune_le_texto_pelo_locale():
    """Toda chamada com `text=True` (ou `universal_newlines`) declara
    `encoding="utf-8"` e `errors="replace"`. Fora o `comum.rodar_texto`, que é
    o caminho normal, só o kernel do Kaggle (autossuficiente) as faz à mão."""
    fora = []
    for arq in sorted(FINETUNE.rglob("*.py")):
        for no in _chamadas_de_subprocess(ast.parse(arq.read_text(encoding="utf-8"))):
            kw = {k.arg: k.value for k in no.keywords if k.arg}
            le_texto = any(isinstance(kw.get(k), ast.Constant) and kw[k].value is True
                           for k in ("text", "universal_newlines"))
            if not le_texto:
                continue
            enc = kw.get("encoding")
            err = kw.get("errors")
            if not (isinstance(enc, ast.Constant) and enc.value == "utf-8"
                    and isinstance(err, ast.Constant) and err.value == "replace"):
                fora.append(f"{arq.relative_to(RAIZ)}:{no.lineno}")
    assert fora == []


def _rodar_viabilidade(codigo: str, tmp_path: Path) -> dict:
    """Executa num subprocesso: o módulo importa `_guarda` (rede bloqueada)."""
    pre = f"""
import json, sys, types
sys.argv = ["x", "--sem-autoteste"]
sys.path.insert(0, {str(FINETUNE)!r})
import viabilidade_ollama as V
import comum as K
from pathlib import Path
tmp = Path({str(tmp_path)!r})
"""
    r = subprocess.run([sys.executable, "-c", pre + codigo], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, env=_env_sem_chaves())
    assert r.returncode == 0, r.stderr[-1500:]
    return json.loads(r.stdout.strip().splitlines()[-1])


FALSO_OLLAMA = """
existe = {estado!r}
cmds = []
def falso(args, **kw):
    cmds.append(args[:2])
    rc = 0
    if args[1] == "show":
        rc = 0 if existe["v"] else 1
    elif args[1] == "rm" and not {rm_falha!r}:
        existe["v"] = False
    return types.SimpleNamespace(returncode=rc, stdout="", stderr="")
K.rodar_texto = falso
"""


def test_import_remove_o_modelo_que_ja_existia_antes_de_criar(tmp_path):
    out = _rodar_viabilidade(FALSO_OLLAMA.format(estado={"v": True}, rm_falha=False) + """
reg = V.remover_modelo("espectro-qwen3-8b")
print(json.dumps({"reg": reg, "cmds": cmds}))
""", tmp_path)
    assert out["reg"]["existia"] is True and out["reg"]["rm_rc"] == 0
    assert out["cmds"] == [["ollama", "show"], ["ollama", "rm"], ["ollama", "show"]]


def test_import_sem_modelo_anterior_nao_chama_rm(tmp_path):
    out = _rodar_viabilidade(FALSO_OLLAMA.format(estado={"v": False}, rm_falha=False) + """
reg = V.remover_modelo("espectro-qwen3-8b")
print(json.dumps({"reg": reg, "cmds": cmds}))
""", tmp_path)
    assert out == {"reg": {"existia": False}, "cmds": [["ollama", "show"]]}


def test_import_aborta_se_o_rm_nao_remove(tmp_path):
    out = _rodar_viabilidade(FALSO_OLLAMA.format(estado={"v": True}, rm_falha=True) + """
try:
    V.remover_modelo("espectro-qwen3-8b")
    print(json.dumps({"abortou": False}))
except SystemExit as e:
    print(json.dumps({"abortou": True, "msg": str(e)}))
""", tmp_path)
    assert out["abortou"] is True and "não removeu" in out["msg"]


def test_import_grava_o_registro_quando_o_script_cai(tmp_path):
    """Uma falha do SCRIPT no meio do import sai gravada, com E4 = None (não é
    reprovação do modelo); antes o JSON se perdia."""
    out = _rodar_viabilidade("""
(tmp / "m.gguf").write_bytes(b"x")
(tmp / "Modelfile").write_text("FROM x\\n", encoding="utf-8")
V._cabecalho = lambda a: ({"medicoes": []}, "s", "u")
V.matar_ollama = lambda: None
V.subir_ollama = lambda: types.SimpleNamespace(terminate=lambda: None)
def cai(nome):
    raise TypeError("'NoneType' object is not subscriptable")
V.remover_modelo = cai
a = types.SimpleNamespace(gguf=str(tmp / "m.gguf"), modelfile=str(tmp / "Modelfile"),
                          familia="qwen", nome="espectro-qwen3-8b", saida=tmp / "saida")
try:
    V.cmd_importar(a)
except TypeError:
    pass
arqs = sorted((tmp / "saida").glob("importar_*.json"))
d = json.loads(arqs[0].read_text(encoding="utf-8"))
print(json.dumps({"n": len(arqs), "E4": d["E4_importa_e_gera"], "erro": d["erro_do_script"]}))
""", tmp_path)
    assert out["n"] == 1 and out["E4"] is None and out["erro"].startswith("TypeError")


def test_chat_do_qwen_nao_apara_o_usuario():
    # o prompt de síntese termina em "\n"; o template do Qwen3 o mantém (v4)
    t = K.chat("qwen", "S", "U\n", "{}")
    assert "<|im_start|>user\nU\n<|im_end|>\n" in t
    assert t.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n{}<|im_end|>\n")


# ---------------------------------------------------------------------------
# kernel do Kaggle: confere o sha256 do smoke.jsonl lido contra o meta.json
# ---------------------------------------------------------------------------

def _conferir_no_kernel(tmp_path: Path, sha_meta: str | None) -> subprocess.CompletedProcess:
    entrada = tmp_path / "input" / "ds"
    entrada.mkdir(parents=True)
    (entrada / "smoke.jsonl").write_text("{}\n", encoding="utf-8")
    meta = {} if sha_meta is None else {"smoke_sha256": sha_meta}
    (entrada / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    codigo = f"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("smoke", {str(FINETUNE / 'kaggle/kernel/smoke_treino.py')!r})
m = importlib.util.module_from_spec(spec); sys.modules["smoke"] = m; spec.loader.exec_module(m)
m.ENTRADA_GLOB = {str(tmp_path / 'input' / '**' / 'smoke.jsonl')!r}
print(json.dumps(m._conferir_dataset()))
"""
    return subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60, env=_env_sem_chaves())


def test_kernel_segue_quando_o_sha_lido_e_o_do_meta(tmp_path):
    import hashlib
    r = _conferir_no_kernel(tmp_path, hashlib.sha256(b"{}\n").hexdigest())
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1])["confere"] is True


@pytest.mark.parametrize("sha_meta", ["0" * 64, None])
def test_kernel_aborta_com_sha_diferente_ou_ausente(tmp_path, sha_meta):
    r = _conferir_no_kernel(tmp_path, sha_meta)
    assert r.returncode != 0 and "abortado" in r.stderr


# ---------------------------------------------------------------------------
# geração do modelo base para a validação da fase 1 (bullet completo, v2)
# ---------------------------------------------------------------------------

def _rodar_gerador(codigo: str) -> dict:
    pre = f"""
import json, sys
sys.argv = ["x"]
sys.path.insert(0, {str(FINETUNE)!r})
import gerar_titulos_base as G
"""
    r = subprocess.run([sys.executable, "-c", pre + codigo], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, env=_env_sem_chaves())
    assert r.returncode == 0, r.stderr[-1500:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_gerador_grava_o_bullet_completo_como_a_medida_le():
    out = _rodar_gerador("""
import especificidade_bullet as EB
d = {"temas": [{"tema": " Ritmo lento ", "exemplo_parafraseado": "As cenas longas cansam.",
                "mencoes_aproximadas": 7, "n_reviews_analisadas": 20},
               {"tema": "Sem exemplo", "exemplo_parafraseado": ""}]}
b = G.bullets(d)
print(json.dumps({"b": b, "eb": EB.texto_do_bullet(" Ritmo lento ", "As cenas longas cansam.")}))
""")
    assert out["b"][0] == {"tema": " Ritmo lento ", "exemplo_parafraseado": "As cenas longas cansam.",
                           "texto": "Ritmo lento — As cenas longas cansam.", "completo": True}
    assert out["b"][0]["texto"] == out["eb"]           # a mesma unidade do PROTOCOLO_v2
    assert out["b"][1]["completo"] is False and out["b"][1]["texto"] is None
    assert not any("mencoes" in k for x in out["b"] for k in x)   # contagens fora


def test_num_ctx_pela_regra_do_gate_0():
    out = _rodar_gerador("print(json.dumps([G.num_ctx_da_chamada(n) for n in (8019, 14267, 4202)]))")
    # (n + 3.000) × 1,10, para cima no múltiplo de 1.024
    assert out == [12288, 19456, 8192]


def test_gerador_recusa_filme_de_validacao_ou_teste(tmp_path):
    out = _rodar_gerador(f"""
from pathlib import Path
arq = Path({str(tmp_path / 'sel.json')!r})
G.ARQ_FILMES = arq
split = {{"treino": list(G.FILMES), "validacao": ["x"], "teste": ["the-wailing"]}}
arq.write_text(json.dumps({{"filmes_geracao": list(G.FILMES)}}))
try:
    G.filmes_conferidos(split)
    r1 = "passou"
except SystemExit as e:
    r1 = str(e)
arq.write_text(json.dumps({{"filmes_geracao": ["fight-club"]}}))
try:
    G.filmes_conferidos(split)
    r2 = "passou"
except SystemExit as e:
    r2 = str(e)
print(json.dumps([r1, r2]))
""")
    assert "the-wailing" in out[0] and "recusados" in out[0]
    assert "mudou" in out[1]


def test_gerador_exige_o_e4(tmp_path):
    out = _rodar_gerador(f"""
from pathlib import Path
G.VIABILIDADE = Path({str(tmp_path)!r})
(G.VIABILIDADE / "importar_espectro-qwen3-8b_20261030_1.json").write_text(json.dumps({{"E4_importa_e_gera": None}}))
try:
    G.exigir_e4(); r1 = "passou"
except SystemExit as e:
    r1 = "recusou"
(G.VIABILIDADE / "importar_espectro-qwen3-8b_20261031_1.json").write_text(json.dumps({{"E4_importa_e_gera": True}}))
r2 = G.exigir_e4().name
print(json.dumps([r1, r2]))
""")
    assert out == ["recusou", "importar_espectro-qwen3-8b_20261031_1.json"]
