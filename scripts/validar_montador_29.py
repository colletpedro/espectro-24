#!/usr/bin/env python3
"""Valida o montador offline (`montagem_offline.py`) nos 29 filmes de 08/11, campo a campo. Zero LLM, zero custo.

Para cada filme, remonta o documento com:
  - bruto versionado (`dados/bruto/<slug>`) e a classificação que o resultado cita (sha conferido);
  - a SÍNTESE injetada a partir do `resultado/<slug>.json` versionado (o montador não chama modelo de síntese);
  - a ROTULAGEM repetida das respostas gravadas (`execucoes/.../aberto/<slug>/chamadas`, chave = hash do prompt):
    se o prompt remontado diferir byte a byte do original, a resposta não é achada e o filme FALHA;
  - a ficha: (A) a do resultado versionado e (B) a regenerada pelo TMDB (mede a deriva do TMDB desde 08/11).
e compara com (1) o `bullets.json` original e (2) o `resultado/<slug>.json` versionado menos o que as etapas seguintes
acrescentam (`condicoes`, `ficha.paises`).

Uso:  venv/bin/python scripts/validar_montador_29.py [--slug X] [--sem-tmdb]
Saída: resultado/c22-publicacao/validacao_montador_29.json (todas as diferenças, por caminho) e um resumo.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "scripts")]

from espectro24 import montagem_offline as M  # noqa: E402
from espectro24.config import LLM_MAX_TOKENS, SPEC_VERSION  # noqa: E402

DS = "deepseek-ai/DeepSeek-V4.1-Flash-1017"
ABERTO = RAIZ / "execucoes" / "featherless-etapa2-2026-11-08" / "aberto"
SAIDA = RAIZ / "resultado" / "c22-publicacao" / "validacao_montador_29.json"


class Replay:
    """Mesma chave do `Chamador` de etapa2: sha256([system, user, model, estagio, max_tokens]) + ordinal."""

    def __init__(self, pasta: Path):
        self.p, self.n, self.faltou = pasta, collections.Counter(), []

    def __call__(self, system: str, user: str, model: str) -> str:
        base = hashlib.sha256(json.dumps([system, user, model, "rotulagem", LLM_MAX_TOKENS],
                                         ensure_ascii=False).encode()).hexdigest()
        n = self.n[base]
        self.n[base] += 1
        arq = self.p / "chamadas" / f"{base}_{n}.json"
        if not arq.exists():
            self.faltou.append(base[:12])
            raise RuntimeError(f"prompt remontado não existe nas chamadas gravadas ({base[:12]}_{n})")
        return json.loads(arq.read_text(encoding="utf-8"))["texto"]


def diff(a, b, caminho="") -> list[dict]:
    """Diferenças profundas entre dois JSON; cada uma com o caminho e os dois valores (truncados)."""
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        return [{"caminho": caminho, "montado": _t(a), "esperado": _t(b)}]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append({"caminho": f"{caminho}.{k}", "montado": "<ausente>", "esperado": _t(b[k])})
            elif k not in b:
                out.append({"caminho": f"{caminho}.{k}", "montado": _t(a[k]), "esperado": "<ausente>"})
            else:
                out += diff(a[k], b[k], f"{caminho}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [{"caminho": caminho, "montado": f"len={len(a)}", "esperado": f"len={len(b)}"}]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{caminho}[{i}]")]
    return [] if a == b else [{"caminho": caminho, "montado": _t(a), "esperado": _t(b)}]


def _t(v) -> str:
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 160 else s[:157] + "..."


def _sem_etapas_seguintes(pub: dict) -> dict:
    d = json.loads(json.dumps(pub))
    d.pop("condicoes", None)
    (d.get("ficha") or {}).pop("paises", None)
    return d


def validar(slug: str, com_tmdb: bool) -> dict:
    pub = json.loads((RAIZ / "resultado" / f"{slug}.json").read_text(encoding="utf-8"))
    p = ABERTO / slug
    fonte = pub["proveniencia_llm"]["classificacao"]["fonte"]
    original = json.loads((p / "bullets.json").read_text(encoding="utf-8"))
    ficha_pub = json.loads(json.dumps(pub["ficha"]))
    ficha_pub.pop("paises", None)
    replay = Replay(p)
    r = {"slug": slug}
    try:
        doc = M.montar_documento(
            slug, bruto_raiz=RAIZ / "dados" / "bruto", consenso_path=RAIZ / fonte,
            sintese={b["bucket"]: b for b in pub["buckets"]}, ficha=ficha_pub, rotular=replay,
            modelo_rotulagem=DS, proveniencia_sintese=pub["proveniencia_llm"]["sintese"], fonte_registrada=fonte,
            classificacao_rotulo=pub["eixos"]["verificador"]["classificacao"])
    except Exception as e:  # noqa: BLE001
        return {**r, "estado": "FALHOU", "erro": f"{type(e).__name__}: {str(e)[:300]}", "prompts_faltando": replay.faltou}
    r["rotulagem_replay_chamadas"] = sum(replay.n.values())
    esperado = _sem_etapas_seguintes(pub)
    r["vs_resultado_versionado"] = diff(doc, esperado)
    r["vs_bullets_json_original"] = diff(doc, original)
    if com_tmdb:
        from conferir_tmdb_c22 import chave_do_env
        from espectro24 import ficha as F
        ident = (json.loads((RAIZ / "dados" / "bruto" / slug / "meta.json").read_text())
                 .get("identidade_letterboxd"))
        f2, aviso, desc = F.buscar_ficha(ident["titulo"], int(ident["ano"]),
                                         RAIZ / "resultado" / "c22-publicacao" / "cache_tmdb_29",
                                         api_key=chave_do_env(), identidade={**ident, "slug": slug})
        r["ficha_tmdb_hoje_vs_versionada"] = (diff(f2, ficha_pub) if f2 else
                                              [{"caminho": "ficha", "montado": "None", "esperado": aviso}])
    r["estado"] = "IDENTICO" if not r["vs_resultado_versionado"] else "DIFERE"
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append")
    ap.add_argument("--sem-tmdb", action="store_true")
    a = ap.parse_args()
    man = json.loads((RAIZ / "resultado" / "featherless-etapa2-2026-11-08" / "manifesto.json").read_text())
    slugs = a.slug or [f["slug"] for f in man["filmes"]]
    linhas = [validar(s, not a.sem_tmdb) for s in slugs]
    cont = collections.Counter(l["estado"] for l in linhas)
    por_caminho = collections.Counter()
    for l in linhas:
        for d in l.get("vs_resultado_versionado", []):
            import re
            por_caminho[re.sub(r"\[\d+\]", "[]", d["caminho"])] += 1
    out = {"gerado_por": "scripts/validar_montador_29.py", "spec_version_atual": SPEC_VERSION, "contagem": dict(cont),
           "diferencas_por_caminho": dict(por_caminho), "filmes": linhas}
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"contagem": dict(cont), "diferencas_por_caminho": dict(por_caminho)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
