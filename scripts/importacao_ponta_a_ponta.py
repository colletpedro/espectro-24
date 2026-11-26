"""Ponta a ponta dos filmes IMPORTADOS à mão (`importar_manual.py`) — sem publicar.

Mesma configuração da sessão Featherless de 08/11 (`etapa2_featherless.py`):
DeepSeek-V4.1-Flash-1017 em TODOS os estágios (3 passadas + verificador de
classificação, síntese, rotulagem, condições), sem mistura de modelos.

    python scripts/importacao_ponta_a_ponta.py [--out DIR] preparar
    python scripts/importacao_ponta_a_ponta.py [--out DIR] rodar boogie-nights primetime-2026
    python scripts/importacao_ponta_a_ponta.py [--out DIR] relatorio
    python scripts/importacao_ponta_a_ponta.py [--out DIR] previa

`--out` troca a pasta de execução (e o livro-caixa): a regeneração com a regra
R2 usa `execucoes/regeneracao-r2-2026-11-26` (teto US$ 1,50). Filme que já está
em `resultado/<slug>.json` (no ar) mantém a FICHA publicada; os importados usam
a do TMDB + `paises_tmdb` do meta.

Nada disto escreve `dados/publicados.json`, `resultado/<slug>.json` ou
`frontend/`. Tudo fica em `execucoes/importacao-manual-2026-11-26/` (fora do
git). Zero requisição ao Letterboxd: bruto vem de `dados/bruto/<slug>` (já
importado), a ficha do TMDB e os LLMs são as únicas redes.

O livro-caixa é uma sessão NOVA (`FEATHERLESS_ETAPA=1`, teto de US$ 1,50, bem
abaixo do máximo de US$ 3,00 que o código aceita nessa etapa). A etapa 2 de
08/11 expirou por construção (prazo 09/11) e não é reaberta.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from espectro24.atomico import escrever_atomico  # noqa: E402

OUT = ROOT / "execucoes" / "importacao-manual-2026-11-26"
DS = "deepseek-ai/DeepSeek-V4.1-Flash-1017"
TETO_USD = "1.50"
SLUGS = ("boogie-nights", "primetime-2026")


SLUGS_PADRAO = SLUGS


def definir_out(caminho, slugs=None):
    global OUT, SLUGS
    OUT = Path(caminho) if Path(caminho).is_absolute() else ROOT / caminho
    if slugs:
        SLUGS = tuple(slugs)


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def salvar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    escrever_atomico(p, json.dumps(d, ensure_ascii=False, indent=2) + "\n")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ambiente():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    os.environ.update(FEATHERLESS_SESSION_DIR=str(OUT), FEATHERLESS_TETO_USD=TETO_USD,
                      FEATHERLESS_ETAPA="1")
    os.environ.pop("FEATHERLESS_PRAZO_UTC", None)


def conta(endpoint):
    import requests
    r = requests.get("https://api.featherless.ai/" + endpoint,
                     headers={"Authorization": "Bearer " + os.environ["FEATHERLESS_API_KEY"]},
                     timeout=30)
    r.raise_for_status()
    return r.json()


def preparar():
    from espectro24 import featherless as F
    ambiente()
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "plano.json").exists():
        salvar(OUT / "plano.json", conta("v1/plan"))
    if not (OUT / "saldo_inicial.json").exists():
        salvar(OUT / "saldo_inicial.json", conta("credits/balance"))
    invariantes = {str(p.relative_to(ROOT)): sha(p) for p in
                   [ROOT / "dados" / "publicados.json",
                    *(ROOT / "dados" / "bruto" / s / n for s in SLUGS for n in ("meta.json", "reviews.jsonl")),
                    *(q for s in SLUGS for q in [ROOT / "resultado" / f"{s}.json"] if q.exists())]}
    if not (OUT / "invariantes.json").exists():
        salvar(OUT / "invariantes.json", invariantes)
    F.sessao_ambiente()
    print("preparado:", OUT)
    print("plano:", {k: v for k, v in ler(OUT / "plano.json").items() if k in ("concurrency", "max_context_length", "name", "plan")})
    print("saldo_inicial:", ler(OUT / "saldo_inicial.json"))


def conferir_invariantes():
    for rel, h in ler(OUT / "invariantes.json").items():
        assert sha(ROOT / rel) == h, f"entrada protegida alterada: {rel}"


def rodar_filme(slug):
    import etapa2_featherless as E2
    from espectro24 import condicoes as C
    from espectro24 import pipeline as P
    from espectro24 import synthesize as S
    from espectro24.config import BEST_OF_N
    from espectro24.montagem_offline import montar_documento
    from espectro24.validacao_publicado import validar_publicado
    import importar_manual as IM

    ambiente()
    from espectro24 import featherless as F
    F.sessao_ambiente()
    conferir_invariantes()

    p = OUT / slug
    p.mkdir(parents=True, exist_ok=True)
    bruto = ROOT / "dados" / "bruto"
    meta = ler(bruto / slug / "meta.json")
    estado_p = p / "estado.json"
    estado = ler(estado_p) if estado_p.exists() else {}
    estado.update(slug=slug, inicio_utc=estado.get("inicio_utc") or datetime.now(timezone.utc).isoformat())

    am = P.amostra_do_bruto(slug, raiz=bruto)
    estado["amostra"] = {b: len(rs) for b, rs in am.items()}
    salvar(estado_p, estado)

    # 1) classificação: 3 passadas + verificador, UM modelo (asserções em E2.classificar)
    cons = p / "classificacao" / "consenso_verificado.jsonl"
    if not cons.exists():
        t0 = time.monotonic()
        E2.classificar(slug, p, am)
        estado["classificacao_s"] = round(time.monotonic() - t0, 1)
        salvar(estado_p, estado)

    chamadas = E2.Chamador(p, slug)

    # 2) ficha: a PUBLICADA, se o filme está no ar; senão TMDB (caminho normal)
    #    + `paises` do meta (lido do TMDB pelo adaptador). Não é Letterboxd.
    pub = ROOT / "resultado" / f"{slug}.json"
    if pub.exists():
        ficha = ler(pub)["ficha"]
        estado["ficha_fonte"] = "publicada"
    else:
        ficha, aviso, descarte = IM.ficha_normal(IM.identidade_do_import(
            {"slug": slug, "titulo": meta["identidade_letterboxd"]["titulo"],
             "ano": meta["identidade_letterboxd"]["ano"],
             "tmdb_id": meta["identidade_letterboxd"]["tmdb_id_letterboxd"]}))
        assert ficha is not None, f"ficha indisponível: {aviso} {descarte}"
        ficha = IM.ficha_com_paises(ficha, meta)
        estado["ficha_fonte"] = "tmdb+paises_tmdb"
    assert ficha.get("paises"), "ficha sem paises"

    # 3) síntese + distribuição + rotulagem = o `bullets.json` dos 29 (montador validado)
    dest = p / "bullets.json"
    if not dest.exists():
        def sintese(b):
            return S.synthesize_bucket(b, client_call=chamadas.texto("sintese"), model=DS,
                                       provider="featherless")
        rel = str(cons.relative_to(ROOT))
        doc = montar_documento(
            slug, bruto_raiz=bruto, consenso_path=cons, sintese=sintese, ficha=ficha,
            rotular=chamadas.texto("rotulagem"), modelo_rotulagem=DS,
            proveniencia_sintese={"provider": "featherless", "modelo": DS},
            fonte_registrada=rel, classificacao_rotulo=DS)
        salvar(dest, doc)
    doc = ler(dest)

    # 4) validadores de síntese (por bucket)
    estado["validadores_bullets"] = {
        b["bucket"]: (validar_publicado(b) if b["modo"] != "sem_analise"
                      else {"passa_publicado": None, "estado": "sem_analise"})
        for b in doc["buckets"]}

    # 5) condições (DeepSeek) + validadores
    cdest = p / "condicoes" / "condicoes.json"
    if not cdest.exists():
        salvar(cdest, C.gerar(doc, n=BEST_OF_N, provider="featherless", model=DS,
                              gerar=chamadas.condicoes(DS)))
    estado["validadores_condicoes"] = E2.validar_condicoes(doc, ler(cdest))
    # a versão PUBLICÁVEL: R13 (retira `expectativa`) + trava de `publicar_condicoes`
    import publicar_condicoes as PC
    pdest = p / "condicoes" / "condicoes_publicaveis.json"
    bloco, n_ret = PC.aplicar_retiradas(slug, ler(cdest), doc)
    try:
        estado["condicoes_validar_bloco"] = PC.validar_bloco(slug, bloco, C.indexar(doc))
    except Exception as e:  # noqa: BLE001 — a trava reprova; registra, não derruba o filme
        estado["condicoes_validar_bloco"] = {"REPROVADO": f"{type(e).__name__}: {e}"}
    estado["condicoes_retiradas_r13"] = n_ret
    salvar(pdest, bloco)

    estado.update(estado="gerado", fim_utc=datetime.now(timezone.utc).isoformat())
    salvar(estado_p, estado)
    conferir_invariantes()
    print(slug, "gerado", F.Sessao(OUT, TETO_USD, etapa="1").resumo())


def custo_por_estagio():
    import collections
    por = collections.defaultdict(lambda: [0.0, 0, 0, 0])
    por_slug = collections.defaultdict(float)
    for l in (OUT / "uso.jsonl").read_text().splitlines():
        r = json.loads(l)
        c = r.get("custo_usd") or 0.0
        k = (r.get("estagio") or "?")
        por[k][0] += c
        por[k][1] += 1
        por[k][2] += r.get("prompt_tokens") or r.get("entrada") or 0
        por[k][3] += r.get("completion_tokens") or r.get("saida") or 0
        por_slug[r.get("slug") or "?"] += c
    return ({k: dict(usd=round(v[0], 6), chamadas=v[1], tok_entrada=v[2], tok_saida=v[3]) for k, v in por.items()},
            {k: round(v, 6) for k, v in por_slug.items()})


def relatorio():
    from espectro24 import featherless as F
    ambiente()
    saida = {"sessao": F.Sessao(OUT, TETO_USD, etapa="1").resumo()}
    saida["custo_por_estagio"], saida["custo_por_filme"] = custo_por_estagio()
    try:
        saida["saldo_final"] = conta("credits/balance")
        salvar(OUT / "saldo_final.json", saida["saldo_final"])
    except Exception as e:  # noqa: BLE001
        saida["saldo_final"] = f"indisponivel: {type(e).__name__}"
    saida["filmes"] = {s: ler(OUT / s / "estado.json") for s in SLUGS if (OUT / s / "estado.json").exists()}
    salvar(OUT / "relatorio.json", saida)
    print(json.dumps(saida, ensure_ascii=False, indent=2)[:6000])


def previa():
    """Cópia do `frontend/` em `<OUT>/previa/` com os filmes importados embutidos.

    O `frontend/` real NÃO é tocado. O catálogo da cópia ganha os slugs para a
    tela do filme abrir; `dados/publicados.json` não muda.
    """
    destino = OUT / "previa"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(ROOT / "frontend", destino, ignore=shutil.ignore_patterns("__pycache__"))
    arq = destino / "js" / "data.js"
    t = arq.read_text(encoding="utf-8")
    payload = json.loads(t[t.index("{"): t.rindex("}") + 1])
    for s in SLUGS:
        if not (OUT / s / "bullets.json").exists():
            continue
        d = ler(OUT / s / "bullets.json")
        pc = OUT / s / "condicoes" / "condicoes_publicaveis.json"
        cond = ler(pc) if pc.exists() else None
        d.pop("origem_paginas", None)
        d.pop("proveniencia_llm", None)
        if cond:
            d["condicoes"] = cond
        if s in payload["filmes"]:
            # já no ar: troca só o que a regeneração gerou e PRESERVA o que o
            # build editorial acrescenta (logo etc.)
            d = {**payload["filmes"][s], **d}
        d["_previa_regeneracao"] = True
        payload["filmes"][s] = d
        if s not in payload["catalogo"]:
            payload["catalogo"].append(s)
        (destino / "data" / f"{s}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    arq.write_text("window.ESPECTRO_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("prévia:", destino, "\n  python3 -m http.server 8778 --directory", destino,
          "\n  http://localhost:8778/filme.html?slug=boogie-nights")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["preparar", "rodar", "relatorio", "previa"])
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--out")
    a = ap.parse_args()
    definir_out(a.out or OUT, a.slugs if a.cmd != "rodar" else None)
    if a.cmd == "preparar":
        preparar()
    elif a.cmd == "rodar":
        for s in a.slugs or SLUGS:
            rodar_filme(s)
    elif a.cmd == "relatorio":
        relatorio()
    else:
        previa()
