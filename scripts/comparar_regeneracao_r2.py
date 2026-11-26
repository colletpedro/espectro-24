"""Relatório legível da regeneração com a regra R2: publicado × novo, por filme.

    python scripts/comparar_regeneracao_r2.py [--out execucoes/regeneracao-r2-2026-11-26]

Para cada filme: amostra antes/depois (H/M/F), reviews que saíram e entraram,
diff dos bullets e das condições, validadores e ficha. "Antes" = o `resultado/
<slug>.json` no ar (ou, para Boogie Nights, a primeira geração sem a R2).

**Sinal mecânico de trama** (não substitui a leitura): para cada bullet/condição,
as palavras de 6+ letras que aparecem NO RESUMO EXCLUÍDO e em NENHUMA das outras
reviews da amostra. Bullet que repete vocabulário que só o resumo continha é
candidato a "descreve a trama"; a decisão é de leitura humana.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / "src")]

from espectro24.bruto import carregar  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

FILMES = ("casablanca", "its-a-wonderful-life", "modern-times", "rear-window", "seven-samurai",
          "boogie-nights", "primetime-2026")
ANTES_BOOGIE = RAIZ / "execucoes" / "importacao-manual-2026-11-26" / "boogie-nights" / "bullets.json"
ANTES_COND_BOOGIE = RAIZ / "execucoes" / "importacao-manual-2026-11-26" / "boogie-nights" / "condicoes" / "condicoes.json"
NO_AR = ("casablanca", "its-a-wonderful-life", "modern-times", "rear-window", "seven-samurai")
ANTES_PRIMETIME = RAIZ / "execucoes" / "importacao-manual-2026-11-26" / "primetime-2026" / "bullets.json"
_TODOS_RESUMOS: set[str] = set()
PALAVRA = re.compile(r"[a-zà-ÿ]{6,}")


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _sel(slug, resumo):
    meta, rs = carregar(slug, raiz=RAIZ / "dados" / "bruto")
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    orc = {float(k): v for k, v in (meta.get("orcamento_paginas_por_nivel") or {}).items()}
    from espectro24.recusas import ids_recusados
    sel = selecionar(rs, hist, orcamento_paginas_por_nivel=orc, excluir_ids=ids_recusados(slug),
                     excluir_resumo_de_trama=resumo)
    por_id = {r.id: r for r in rs}
    return sel, por_id


def _ids(sel):
    return {b: [r.id for n in s.niveis.values() for r in n.validas] for b, s in sel.items()}


_VOCAB_GLOBAL: set | None = None


def _vocab_global(ids_resumo: set[str]) -> set[str]:
    """Palavras de 6+ letras de TODAS as reviews dos brutos, menos os resumos.

    Só assim "só do resumo" quer dizer algo: um resumo em português tem
    centenas de palavras comuns que a amostra (em inglês, em sua maioria) não
    tem, e que não revelam trama nenhuma. Nome próprio, lugar e evento do
    enredo, sim, não aparecem em nenhuma outra review do corpus.
    """
    global _VOCAB_GLOBAL
    if _VOCAB_GLOBAL is None:
        v: set[str] = set()
        for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
            if (d / "reviews.jsonl").exists():
                _, rs = carregar(d.name, raiz=RAIZ / "dados" / "bruto")
                for r in rs:
                    if r.id not in ids_resumo:
                        v |= set(PALAVRA.findall(r.texto.lower()))
        _VOCAB_GLOBAL = v
    return _VOCAB_GLOBAL


def _vocab_so_do_resumo(slug, sel_depois, resumos):
    """Palavras do resumo ausentes das outras reviews da amostra E do corpus.

    Texto do FILME no corpus (outras reviews do mesmo filme) conta como
    "outras": é a única fonte legítima de nomes de personagem. Assim o sinal
    é "o bullet repete algo que só o resumo dizia".
    """
    outros: set[str] = set()
    for b in sel_depois.values():
        for n in b.niveis.values():
            for r in n.validas:
                outros |= set(PALAVRA.findall(r.texto.lower()))
    _, todas = carregar(slug, raiz=RAIZ / "dados" / "bruto")
    ids_resumo = {r.id for r in resumos}
    for r in todas:
        if r.id not in ids_resumo:
            outros |= set(PALAVRA.findall(r.texto.lower()))
    glob = _vocab_global({r.id for r in resumos} | _TODOS_RESUMOS)
    so = set()
    for r in resumos:
        so |= set(PALAVRA.findall(r.texto.lower())) - outros - glob
    return so


def _marca(texto, vocab):
    achadas = sorted(set(PALAVRA.findall((texto or "").lower())) & vocab)
    return achadas


def _bullets(doc):
    return {b["bucket"]: b for b in doc["buckets"]}


def _cond(doc_cond):
    """`{lado: [condições]}` — TODAS, não só a primeira (cada lado publica de 2 a 4)."""
    saida = {}
    for lado in ("vale_a_pena", "talvez_evite"):
        c = (doc_cond or {}).get(lado)
        if isinstance(c, dict):
            saida[lado] = [c]
        elif isinstance(c, list):
            saida[lado] = c
    return saida


def _todos_os_resumos() -> set[str]:
    from espectro24.selecao import e_resumo_de_trama
    ids = set()
    for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
        if (d / "reviews.jsonl").exists():
            _, rs = carregar(d.name, raiz=RAIZ / "dados" / "bruto")
            ids |= {r.id for r in rs if e_resumo_de_trama(r.texto)}
    return ids


def relatorio(out: Path) -> str:
    _TODOS_RESUMOS.update(_todos_os_resumos())
    L = []
    custo = ler(out / "relatorio.json") if (out / "relatorio.json").exists() else {}
    L.append("# Regeneração com a regra R2 — publicado × novo\n")
    if custo:
        L.append(f"Custo da sessão: **US$ {custo['sessao']['custo_usd']:.4f}** "
                 f"({custo['sessao']['chamadas']} chamadas, teto US$ {custo['sessao']['teto_usd']}).\n")
    for slug in FILMES:
        p = out / slug
        if not (p / "bullets.json").exists():
            L.append(f"\n## {slug}\n\n(não gerado)\n")
            continue
        novo = ler(p / "bullets.json")
        est = ler(p / "estado.json")
        no_ar = slug in NO_AR
        if no_ar:
            # o `resultado/<slug>.json` da árvore pode já ser o NOVO: o publicado é o do git
            antes = json.loads(subprocess.check_output(
                ["git", "show", f"HEAD:resultado/{slug}.json"], cwd=RAIZ))
            rotulo_antes = "publicado (no ar, HEAD)"
            cond_antes = _cond(antes.get("condicoes"))
        elif slug == "boogie-nights":
            antes, rotulo_antes = ler(ANTES_BOOGIE), "1ª geração (sem R2, 26/11)"
            cond_antes = _cond(ler(ANTES_COND_BOOGIE)) if ANTES_COND_BOOGIE.exists() else {}
        else:
            antes, rotulo_antes = ler(ANTES_PRIMETIME), "1ª geração (26/11, sem países)"
            cond_antes = {}
        sel0, por_id = _sel(slug, False)
        sel1, _ = _sel(slug, True)
        i0, i1 = _ids(sel0), _ids(sel1)
        resumos = [por_id[i] for b in i0 for i in i0[b] if i not in i1[b]]
        vocab = _vocab_so_do_resumo(slug, sel1, resumos)

        L.append(f"\n---\n\n## {slug} — {novo['ficha'].get('titulo')} ({novo['ficha'].get('ano')})\n")
        L.append("### 1. Amostra antes × depois (H/M/F = negativas/medianas/positivas)\n")
        L.append("| bucket | antes | depois |\n|---|---|---|")
        for b in ("negativas", "medianas", "positivas"):
            L.append(f"| {b} | {len(i0[b])} | {len(i1[b])} |")
        saem = [(b, i) for b in i0 for i in i0[b] if i not in i1[b]]
        entram = [(b, i) for b in i1 for i in i1[b] if i not in i0[b]]
        L.append(f"\n**Saíram ({len(saem)}):**")
        for b, i in saem:
            r = por_id[i]
            L.append(f"- `{b}` nível {r.nivel} · {r.n_chars} car. · `{i}` — {r.texto[:90]!r}")
        L.append(f"\n**Entraram ({len(entram)}):**")
        for b, i in entram:
            r = por_id[i]
            L.append(f"- `{b}` nível {r.nivel} · {r.n_chars} car. · `{i}` — {r.texto[:90]!r}")
        if not saem and not entram:
            L.append("- (nenhuma)")

        L.append(f"\n### 2. Bullets — {rotulo_antes} × novo\n")
        ba, bn = _bullets(antes), _bullets(novo)
        for b in ("negativas", "medianas", "positivas"):
            ta, tn = ba[b]["temas"], bn[b]["temas"]
            L.append(f"\n**{b}** (n {ba[b]['n_validas']} → {bn[b]['n_validas']}, modo {bn[b]['modo']})\n")
            L.append("| # | ANTES | NOVO |\n|---|---|---|")
            for k in range(max(len(ta), len(tn))):
                def cel(t, ref=None):
                    if t is None:
                        return "—"
                    m = _marca(t["tema"] + " " + t["exemplo_parafraseado"], vocab)
                    aviso = f" ⚠ vocabulário só do resumo: {', '.join(m)}" if m else ""
                    return (f"**{t['tema']}** ({t['mencoes_aproximadas']}) — {t['exemplo_parafraseado']}{aviso}"
                            ).replace("|", "\\|")
                L.append(f"| {k+1} | {cel(ta[k] if k < len(ta) else None)} | {cel(tn[k] if k < len(tn) else None)} |")
            same = {t["tema"] for t in ta} & {t["tema"] for t in tn}
            L.append(f"\nTemas com o MESMO nome: {len(same)} de {len(ta)}/{len(tn)}.")
            L.append(f"\nobservação ANTES: {ba[b]['observacao_geral']}")
            m = _marca(bn[b]["observacao_geral"], vocab)
            L.append(f"\nobservação NOVA: {bn[b]['observacao_geral']}" + (f" ⚠ {', '.join(m)}" if m else ""))

        L.append("\n### 3. Condições — antes × novo (publicáveis: R13 aplicada)\n")
        cn = _cond(ler(p / "condicoes" / "condicoes_publicaveis.json"))
        for lado in ("vale_a_pena", "talvez_evite"):
            for rot, cs in (("ANTES", cond_antes.get(lado) or []), ("NOVO", cn.get(lado) or [])):
                if not cs:
                    L.append(f"- `{lado}` {rot}: —")
                for c in cs:
                    m = _marca(c["texto"] + " " + c.get("tema_texto", ""), vocab)
                    L.append(f"- `{lado}` {rot} [{c.get('tema_origem')}] {c['texto']!r}"
                             + (f" ⚠ vocabulário só do resumo: {', '.join(m)}" if m else ""))

        L.append("\n### 4. Validadores e ficha\n")
        L.append("- síntese por bucket: " + ", ".join(
            f"{b}={'ok' if v.get('passa_publicado') else v.get('passa_publicado')}"
            for b, v in est["validadores_bullets"].items()))
        vc = est["validadores_condicoes"]
        L.append(f"- condições: aprovadas {vc['aprovadas']}, flags {vc['flags']}, descartadas {vc['descartadas']}, "
                 f"recusas {vc['recusas']}, inconsistências de recusa {vc['inconsistencias_recusa']}")
        L.append(f"- trava de publicação (`validar_bloco`, R13): {est.get('condicoes_validar_bloco')} "
                 f"· retiradas R13: {est.get('condicoes_retiradas_r13')}")
        f = novo["ficha"]
        L.append(f"- ficha ({est.get('ficha_fonte')}): título={f.get('titulo')!r} ano={f.get('ano')} "
                 f"duração={f.get('duracao_min')} países={f.get('paises')} tmdb_id={f.get('tmdb_id')} "
                 f"identidade={(f.get('identidade') or {}).get('status')}")
        L.append(f"- quantidade_fallback: " + str({b["bucket"]: b.get("quantidade_fallback") for b in novo["buckets"]})
                 + f" · spec_version {novo.get('spec_version')}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="execucoes/regeneracao-r2-2026-11-26")
    a = ap.parse_args()
    out = RAIZ / a.out
    txt = relatorio(out)
    (out / "COMPARACAO.md").write_text(txt, encoding="utf-8")
    print(out / "COMPARACAO.md", len(txt))
