#!/usr/bin/env python3
"""Gera frontend/js/indice.js — o ÍNDICE ENXUTO que a home nova lê.

A fonte é `frontend/js/data.js`, isto é, os DADOS PUBLICADOS (o que o site
já serve), e não `resultado/`: o índice não pode saber de um filme que o
site não publica, nem divergir do que a página do filme mostra. Roda
offline, zero rede, zero LLM — só lê JSON e copia campos.

POR QUE UM ARQUIVO À PARTE, e não a home lendo `data.js` direto: `data.js`
tem ~5,6 MB (narrativa, bullets, condições, histograma por nível de nota de
99 filmes) e a home nova precisa de uma fração disso — título, ano, imagens,
o estado de contraste e QUAIS eixos passam a margem de lift. Separar também
é o que mantém a lógica da home (busca, filme do dia, prateleiras) longe do
conteúdo das reviews: **o índice não carrega texto derivado de review
nenhuma** (nem tema, nem exemplo, nem narrativa, nem veredito), e o teste
de invariante de `tests/test_home_nova.py` confere isso campo a campo. É a
garantia estrutural do anti-spoiler dos textos da home: o que não está no
índice não pode vazar na justificativa do filme do dia.

Também NÃO entra no índice nada que seja nota: o histograma por nível de
estrela (`distribuicao.por_nivel`) fica de fora. Entra só a proporção dos
TRÊS grupos (`por_bucket`), que é a faixa fina que o mosaico já mostra.

DATA DE ENTRADA NO CATÁLOGO (para "Recém-chegados"): vem do registro
versionado `frontend/entrada_no_catalogo.json`, slug → data (America/
Sao_Paulo). O registro foi SEMEADO do histórico do git (`--semear-do-git`:
a data do primeiro commit em que o slug aparece no `catalogo` de
`frontend/js/data.js`). Depois disso o git não é mais consultado: um slug
novo no catálogo que ainda não está no registro recebe a data de HOJE, no
fuso de São Paulo, no momento do build — que é quando o filme passa a ser
publicado — e o build avisa. Um slug que sai do catálogo continua no
registro (é histórico) e simplesmente não aparece no índice.

Uso:
    python3 frontend/build_indice.py                  # gera js/indice.js
    python3 frontend/build_indice.py --semear-do-git  # completa o registro
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DATA_JS = FRONTEND / "js" / "data.js"
INDICE_JS = FRONTEND / "js" / "indice.js"
REGISTRO = FRONTEND / "entrada_no_catalogo.json"

FUSO = ZoneInfo("America/Sao_Paulo")

# Os campos de IMAGEM da ficha que `poster.js` lê (`montar` e
# `montarBackdrop`). O índice leva só estes — a home reaproveita os mesmos
# construtores de pôster e backdrop do resto do site.
CAMPOS_IMAGEM = (
    "poster_path", "poster_largura", "poster_altura",
    "poster_sem_texto_path", "poster_sem_texto_largura",
    "poster_sem_texto_altura",
    "backdrop_path", "backdrop_largura", "backdrop_altura",
)

GRUPOS = ("negativas", "medianas", "positivas")


def ler_data_js(caminho: Path = DATA_JS) -> dict:
    texto = caminho.read_text(encoding="utf-8")
    inicio = texto.index("=") + 1
    return json.loads(texto[inicio:].strip().rstrip(";"))


def chave_do_slug(slug: str) -> str:
    """O slug do Letterboxd como CHAVE DE BUSCA (nunca exibida): hífens
    viram espaço e o sufixo de desambiguação sai (`-2019`, `-2015-1`).
    Existe porque 33 dos 99 filmes não têm o título canônico do Letterboxd
    persistido na ficha, e o slug é derivado dele — sem isto, "the
    godfather" não acharia "O Poderoso Chefão"."""
    # Só o sufixo de ANO (com o contador opcional) sai: `district-9` e
    # `friday-the-13th-2009` mostram que um número no fim pode ser título.
    return re.sub(r"-\d{4}(-\d+)?$", "", slug).replace("-", " ").strip()


def eixos_acima(eixos: dict | None) -> list[dict]:
    """Os eixos que passam a margem de lift (`acima_da_margem`, já calculado
    pelo pipeline com limiar(n) = 144,4/√n pp), na ordem da taxonomia.

    Por construção do lift (frequência do grupo MENOS a maior frequência
    entre os outros dois), no máximo UM grupo passa a margem por eixo; o
    índice guarda só a magnitude, e NÃO qual grupo — a home não precisa
    saber, e não saber é a forma mais simples de não favorecer nenhum."""
    saida = []
    for linha in (eixos or {}).get("linhas") or []:
        lifts = [c.get("lift_pp") for c in (linha.get("por_bucket") or {}).values()
                 if c and c.get("acima_da_margem")]
        if lifts:
            saida.append({"eixo": linha["eixo"], "lift_pp": max(lifts)})
    return saida


def entrada_do_indice(slug: str, filme: dict, data_entrada: str | None) -> dict:
    ficha = filme.get("ficha") or {}
    identidade = ficha.get("identidade") or {}
    pb = (filme.get("distribuicao") or {}).get("por_bucket") or {}
    eixos = filme.get("eixos") or {}
    return {
        "slug": slug,
        "titulo": ficha.get("titulo") or slug,
        # O título canônico do LETTERBOXD (`ficha.identidade`, v1.9.49) —
        # para a maioria é o original ou o internacional em inglês. Ausente
        # em 33 filmes (fichas anteriores ao selo de identidade).
        "titulo_letterboxd": identidade.get("titulo_letterboxd"),
        "chave_slug": chave_do_slug(slug),
        "ano": ficha.get("ano"),
        "imagens": {k: ficha.get(k) for k in CAMPOS_IMAGEM if ficha.get(k)},
        "distribuicao": ({g: pb.get(g, 0) for g in GRUPOS} if pb else None),
        "contraste": eixos.get("contraste"),
        "eixos_acima": eixos_acima(eixos),
        "entrada": data_entrada,
    }


def ler_registro() -> dict:
    if not REGISTRO.exists():
        return {}
    return json.loads(REGISTRO.read_text(encoding="utf-8"))["entradas"]


def gravar_registro(entradas: dict) -> None:
    REGISTRO.write_text(json.dumps({
        "_leia": ("Data em que cada slug entrou no catálogo publicado "
                  "(America/Sao_Paulo). Semeado do git por "
                  "build_indice.py --semear-do-git; slug novo recebe a data "
                  "do build. Não reescrever à mão sem motivo registrado."),
        "entradas": dict(sorted(entradas.items())),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def datas_do_git() -> dict[str, str]:
    """slug → data (SP) do primeiro commit em que ele aparece no `catalogo`
    de `frontend/js/data.js`."""
    log = subprocess.run(
        ["git", "log", "--reverse", "--format=%H %aI", "--",
         "frontend/js/data.js"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    primeira: dict[str, str] = {}
    for linha in log.splitlines():
        if not linha.strip():
            continue
        commit, quando = linha.split(" ", 1)
        conteudo = subprocess.run(
            ["git", "show", f"{commit}:frontend/js/data.js"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
        m = re.search(r'"catalogo":\s*\[(.*?)\]', conteudo, re.S)
        if not m:
            continue
        dia = (_dt.datetime.fromisoformat(quando).astimezone(FUSO)
               .date().isoformat())
        for slug in json.loads("[" + m.group(1) + "]"):
            primeira.setdefault(slug, dia)
    return primeira


def hoje_sp() -> str:
    return _dt.datetime.now(FUSO).date().isoformat()


def montar_indice(dados: dict, registro: dict) -> dict:
    filmes = []
    for slug in dados["catalogo"]:
        filme = dados["filmes"].get(slug)
        if filme is None:
            continue
        filmes.append(entrada_do_indice(slug, filme, registro.get(slug)))
    return {"versao": 1, "fonte": "frontend/js/data.js", "filmes": filmes}


def serializar(indice: dict) -> str:
    return (
        "// GERADO por frontend/build_indice.py — NÃO editar à mão.\n"
        "// Fonte: frontend/js/data.js (dados publicados) + "
        "frontend/entrada_no_catalogo.json.\n"
        "window.ESPECTRO_INDICE = "
        + json.dumps(indice, ensure_ascii=False, indent=1)
        + ";\n"
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--semear-do-git", action="store_true",
                    help="completa o registro de entrada com as datas do git")
    args = ap.parse_args(argv)

    dados = ler_data_js()
    registro = ler_registro()

    if args.semear_do_git:
        do_git = datas_do_git()
        for slug, dia in do_git.items():
            registro.setdefault(slug, dia)

    novos = [s for s in dados["catalogo"] if s not in registro]
    if novos:
        dia = hoje_sp()
        for slug in novos:
            registro[slug] = dia
        print(f"  ⚠️  {len(novos)} slug(s) sem data de entrada — registrados "
              f"com {dia}: {', '.join(novos)}")
    if novos or args.semear_do_git:
        gravar_registro(registro)

    indice = montar_indice(dados, registro)
    INDICE_JS.write_text(serializar(indice), encoding="utf-8")
    print(f"OK: {len(indice['filmes'])} filmes em frontend/js/indice.js")


if __name__ == "__main__":
    main(sys.argv[1:])
