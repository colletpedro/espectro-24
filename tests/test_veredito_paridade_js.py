"""[v1.9.21, §3[V]] O template em PYTHON e o fallback em JS têm de concordar.

Há duas implementações do mesmo veredito determinístico, e é deliberado:

  - `veredito.veredito_template` (Python) é a REDE do estágio [V] — o que é
    gravado no JSON quando o LLM não entrega nada válido;
  - `veredito()` em `frontend/js/filme.js` é o FALLBACK DE RENDER para JSON
    publicado antes da v1.9.21, que não tem o bloco novo.

Duas implementações da mesma regra em linguagens diferentes é uma divergência
esperando acontecer — e o sintoma seria silencioso: um filme antigo e um
filme novo em `template_fallback` dizendo coisas diferentes sobre dados
equivalentes. Este teste roda o JS REAL (o arquivo, não um port) sobre os 35
filmes publicados e exige igualdade byte a byte com o Python.

Pula quando `node` não está disponível — o teste é uma rede a mais, não pode
virar um bloqueio de ambiente.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import veredito as V  # noqa: E402

RUNNER = Path(__file__).parent / "js" / "fallback_filme_js.js"


def test_o_template_python_e_o_fallback_js_produzem_o_MESMO_texto():
    from conftest import exige_resultado_sob_a_lei
    exige_resultado_sob_a_lei()
    node = shutil.which("node")
    if not node:
        pytest.skip("node indisponível — a paridade JS/Python não foi medida")
    if not (RAIZ / "frontend" / "js" / "data.js").exists():
        pytest.skip("frontend/js/data.js ausente neste checkout")

    saida = subprocess.run([node, str(RUNNER)], cwd=RAIZ, capture_output=True,
                           text=True, timeout=120)
    assert saida.returncode == 0, saida.stderr[-2000:]
    do_js = json.loads(saida.stdout)
    assert len(do_js) >= 30, f"o runner leu poucos filmes: {len(do_js)}"

    divergentes = []
    for slug, texto_js in do_js.items():
        caminho = RAIZ / "resultado" / f"{slug}.json"
        if not caminho.exists():
            continue
        b = V.montar_briefing(json.loads(caminho.read_text(encoding="utf-8")))
        texto_py = V.veredito_template(b) if b else None
        if texto_py != texto_js:
            divergentes.append(f"{slug}\n    JS: {texto_js}\n    PY: {texto_py}")
    assert not divergentes, ("template Python e fallback JS divergiram:\n  "
                            + "\n  ".join(divergentes))
