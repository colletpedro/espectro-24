"""[2026-10-31] llama.cpp num commit FIXO nos dois kernels (base e treino).

- o bloco `# >>> llama.cpp fixo` é IDÊNTICO em `exportar_base.py` e `treino.py`
  e fixa um commit de 40 dígitos;
- as variáveis do Unsloth (`UNSLOTH_LLAMA_CPP_PATH`, `..._SCRIPTS_DIR`,
  `UNSLOTH_AUTO_INSTALL=0`) são postas no nível do módulo, antes de qualquer
  `import unsloth`;
- `UNSLOTH_RETURN_LOGITS` só na base (a prova do adaptador), nunca no treino;
- `_confere_commit` (sintético, num repositório git de mentira): aceita só se o
  HEAD, o build-info e o binário trazem o commit fixo;
- o treino aborta se o commit que a base gravou no `meta.json` não for o fixo;
- (Fases 2 e 4) `comum.entradas_do_commit` lê as entradas de um commit fixo e
  não da árvore de trabalho (sintético, num repositório git de mentira)."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
KAGGLE = RAIZ / "scripts" / "finetune" / "kaggle"
BASE = KAGGLE / "kernel_base" / "exportar_base.py"
TREINO = KAGGLE / "kernel_treino" / "treino.py"
INI, FIM = "# >>> llama.cpp fixo", "# <<< llama.cpp fixo"


def _bloco(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    assert t.count(INI) == 1 and t.count(FIM) == 1
    return t[t.index(INI):t.index(FIM)]


def test_bloco_identico_e_commit_de_40_digitos():
    a, b = _bloco(BASE), _bloco(TREINO)
    assert a == b
    m = re.search(r'^LLAMA_CPP_COMMIT = "([0-9a-f]+)"$', a, re.M)
    assert m and len(m.group(1)) == 40


@pytest.mark.parametrize("p", [BASE, TREINO])
def test_variaveis_do_unsloth_antes_de_qualquer_import(p):
    linhas = p.read_text(encoding="utf-8").splitlines()
    primeira = min(i for i, l in enumerate(linhas) if re.match(r"\s*(import|from) unsloth", l))
    for chave in ("UNSLOTH_LLAMA_CPP_PATH", "UNSLOTH_LLAMA_CPP_SCRIPTS_DIR", "UNSLOTH_AUTO_INSTALL"):
        i = next(i for i, l in enumerate(linhas) if l.startswith(f'os.environ["{chave}"]'))
        assert i < primeira
    assert 'os.environ["UNSLOTH_AUTO_INSTALL"] = "0"' in linhas


def test_return_logits_so_na_base():
    assert 'os.environ["UNSLOTH_RETURN_LOGITS"] = "1"' in BASE.read_text(encoding="utf-8")
    assert "UNSLOTH_RETURN_LOGITS" not in TREINO.read_text(encoding="utf-8")


def _ns(p: Path, *nomes, **extra) -> dict:
    arvore = ast.parse(p.read_text(encoding="utf-8"))
    ns = {"Path": Path, "json": json, "shutil": shutil, "time": time, "os": os, **extra}
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name in nomes:
            exec(compile(ast.Module([no], []), str(p), "exec"), ns)
    return ns


def _rodar(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _checkout(tmp: Path, curto_no_binario: bool = True) -> tuple[Path, str]:
    d = tmp / "llama.cpp"
    d.mkdir(parents=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    for c in (["git", "init", "-q"], ["git", "commit", "-q", "--allow-empty", "-m", "x"]):
        subprocess.run(c, cwd=d, check=True, env=env, capture_output=True)
    head = _rodar(["git", "-C", str(d), "rev-parse", "HEAD"]).stdout.strip()
    curto = head[:7]
    (d / "build" / "common").mkdir(parents=True)
    (d / "build" / "common" / "build-info.cpp").write_text(
        f'int LLAMA_BUILD_NUMBER = 1;\nchar const * LLAMA_COMMIT = "{curto}";\n', encoding="utf-8")
    q = d / "llama-quantize"
    q.write_text("#!/bin/sh\necho 'usage: llama-quantize'\necho 'version: 1 (build 1, commit "
                 + (curto if curto_no_binario else "0000000") + ")'\n", encoding="utf-8")
    q.chmod(0o755)
    return d, head


@pytest.mark.skipif(shutil.which("git") is None, reason="sem git")
def test_confere_commit_sintetico(tmp_path):
    d, head = _checkout(tmp_path)
    ns = _ns(BASE, "_commit_compilado", "_confere_commit", _rodar=_rodar, _sha256=_sha256,
             LLAMA_CPP_COMMIT=head)
    ok = ns["_confere_commit"](d)
    assert ok["ok"] and ok["commit_compilado"] == head[:7] and ok["commit_no_binario"]
    assert ok["llama_quantize_versao"].startswith("version:")

    ns["LLAMA_CPP_COMMIT"] = "f" * 40                    # outro commit pedido
    assert not ns["_confere_commit"](d)["ok"]

    d2, head2 = _checkout(tmp_path / "b", curto_no_binario=False)   # binário de outro commit
    ns["LLAMA_CPP_COMMIT"] = head2
    assert not ns["_confere_commit"](d2)["ok"]


def test_treino_aborta_se_a_base_gravou_outro_commit(tmp_path):
    linhas = [{"conjunto": "treino", "slug": "a", "bucket": "x"}]
    arq = tmp_path / "treino.jsonl"
    arq.write_text("".join(json.dumps(l) + "\n" for l in linhas), encoding="utf-8")
    sha = _sha256(arq)
    meta = {"treino_sha256": sha, "llama_cpp_commit": "e" * 40,
            "filmes": {"treino": ["a"], "validacao": [], "teste": []}}
    (tmp_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    ns = _ns(TREINO, "conferir_dataset", _sha256=_sha256, DATASET_SHA256=sha,
             LLAMA_CPP_COMMIT="d" * 40, N_TREINO=1, N_VALIDACAO=0)
    ns["_arquivo_dataset"] = lambda: arq
    with pytest.raises(SystemExit, match="não é"):
        ns["conferir_dataset"]()
    meta["llama_cpp_commit"] = "d" * 40
    (tmp_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    _, _, conf = ns["conferir_dataset"]()
    assert conf["n"] == {"treino": 1, "validacao": 0}


@pytest.mark.skipif(shutil.which("git") is None, reason="sem git")
def test_entradas_saem_do_commit_e_nao_da_arvore(tmp_path, monkeypatch):
    """`comum.entradas_do_commit` num repositório de mentira: a árvore de
    trabalho mudada (como o consenso de outras sessões) não entra."""
    import sys
    sys.path.insert(0, str(RAIZ / "scripts" / "finetune"))
    import comum as K
    r = tmp_path / "repo"
    arqs = {"resultado/f.json": '{"slug": "f"}', "resultado/votacao-3/consenso_verificado.jsonl": "c1\n",
            "resultado/votacao-3/amostra.json": "{}", "resultado/votacao-3/outro.json": "{}",
            "dados/bruto/f/meta.json": "{}", "dados/bruto/f/reviews.jsonl": "r\n",
            "dados/bruto/g/meta.json": "{}"}
    for c, t in arqs.items():
        (r / c).parent.mkdir(parents=True, exist_ok=True)
        (r / c).write_text(t, encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    for c in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "x"]):
        subprocess.run(c, cwd=r, check=True, env=env, capture_output=True)
    commit = _rodar(["git", "-C", str(r), "rev-parse", "HEAD"]).stdout.strip()
    (r / "resultado/votacao-3/consenso_verificado.jsonl").write_text("MUDADO\n", encoding="utf-8")
    (r / "resultado/novo.json").write_text("{}", encoding="utf-8")         # não rastreado
    monkeypatch.setattr(K, "RAIZ", r)
    antes = K.RESULTADO_DIR, K.BRUTO_DIR
    with K.entradas_do_commit(["f"], commit) as ent:
        assert ent["commit"] == commit and K.RESULTADO_DIR == ent["raiz"] / "resultado"
        assert (ent["raiz"] / "resultado/votacao-3/consenso_verificado.jsonl").read_text() == "c1\n"
        assert sorted(ent["arquivos"]) == ["dados/bruto/f/meta.json", "dados/bruto/f/reviews.jsonl",
                                           "resultado/f.json", "resultado/votacao-3/amostra.json",
                                           "resultado/votacao-3/consenso_verificado.jsonl"]
        assert (K.BRUTO_DIR / "f" / "reviews.jsonl").read_text() == "r\n"
        raiz = ent["raiz"]
        sha = ent["sha256"]
    assert (K.RESULTADO_DIR, K.BRUTO_DIR) == antes and not raiz.exists()
    with K.entradas_do_commit(["f"], commit) as ent2:
        assert ent2["sha256"] == sha                                       # reprodutível
    with pytest.raises(SystemExit, match="não está no commit"):
        with K.entradas_do_commit(["h"], commit):
            pass
