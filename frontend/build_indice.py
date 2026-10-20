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
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DATA_JS = FRONTEND / "js" / "data.js"
INDICE_JS = FRONTEND / "js" / "indice.js"
REGISTRO = FRONTEND / "entrada_no_catalogo.json"
SELECAO_JS = FRONTEND / "js" / "selecao.js"

FUSO = ZoneInfo("America/Sao_Paulo")

sys.path.insert(0, str(ROOT / "src"))
# O MESMO detector de alfabeto que a ficha usa para o diretor (v1.6.0).
from espectro24.ficha import _e_escrita_latina  # noqa: E402

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


def frequencias_somadas(eixos: dict | None) -> dict[str, tuple[Fraction, Fraction]]:
    """eixo → (frequência SOMADA nos três grupos, frequência MÍNIMA entre
    eles), fora `livre`.

    Soma de FREQUÊNCIAS (menções / n do grupo), não de menções: cada grupo
    pesa o mesmo mesmo quando o `n` difere (8 filmes do catálogo têm grupo
    com n entre 27 e 39). Aritmética exata (`Fraction`), para que um empate
    seja empate de verdade e não ruído de arredondamento de `freq_pct`."""
    saida = {}
    for linha in (eixos or {}).get("linhas") or []:
        if linha.get("eixo") == "livre":
            continue
        freqs = [Fraction(c["mencoes"], c["de_n"])
                 for c in (linha.get("por_bucket") or {}).values()
                 if c and c.get("de_n")]
        if freqs:
            saida[linha["eixo"]] = (sum(freqs), min(freqs))
    return saida


def excluidos_da_home(caminho: Path = SELECAO_JS) -> set[str]:
    """Os slugs de `EXCLUIDOS` em `js/selecao.js` — a lista vive UM lugar só,
    no código da home, e o build a lê de lá (um teste confere que o que este
    parser lê é o que o node executa)."""
    texto = caminho.read_text(encoding="utf-8")
    bloco = re.search(r"var EXCLUIDOS = \{(.*?)\};", texto, re.S)
    if not bloco:
        raise ValueError("EXCLUIDOS não encontrado em selecao.js")
    return set(re.findall(r'^\s*"([^"]+)"\s*:', bloco.group(1), re.M))


def media_do_catalogo(dados: dict, excluidos: set[str] = frozenset()) -> dict[str, Fraction]:
    """eixo → média, sobre os filmes publicados no catálogo MENOS os da
    lista de exclusão da home (`excluidos`), da frequência somada nos três
    grupos. Filme sem a linha do eixo conta como zero.

    [rodada 3, decisão do dono] Os excluídos saem da média: um corpus sob
    suspeita não deve definir o que é "habitual" para os outros filmes.

    Consequência declarada: a média muda quando o catálogo muda, e o
    assunto comum de um filme JÁ publicado pode mudar com a entrada de
    filmes novos. Medido em 2026-10-19 (99 filmes), em pp somados: roteiro
    201,4 · impacto 116,0 · comparações 112,5 · direção 92,3 · ritmo 88,4
    · atuação 86,9 · crítica social 79,1 · expectativa 70,4 · tom 65,7 ·
    som 37,3."""
    somas = [frequencias_somadas((dados["filmes"].get(s) or {}).get("eixos"))
             for s in dados["catalogo"]
             if s in dados["filmes"] and s not in excluidos]
    eixos = sorted({e for fs in somas for e in fs})
    if not somas:
        return {}
    return {e: sum((fs[e][0] for fs in somas if e in fs), Fraction(0)) / len(somas)
            for e in eixos}


def assunto_comum_dominante(eixos: dict | None,
                            media: dict[str, Fraction]) -> str | None:
    """O ASSUNTO COMUM DOMINANTE de um filme: o eixo (fora `livre`) cuja
    frequência SOMADA nos três grupos mais EXCEDE a média do catálogo
    (`media_do_catalogo`). Em palavras: o assunto de que os três grupos
    juntos falam mais do que o habitual no catálogo.

    [rodada 2, decisão do dono] Substitui "a maior frequência somada, em
    termos absolutos", que punha `roteiro_estrutura` em 66 dos 79
    valorativos — roteiro é simplesmente o eixo mais falado em QUALQUER
    filme (201 pp somados de média, contra 116 do segundo). Medido com a
    regra nova (2026-10-19): os 10 eixos aparecem, de 5 a 12 filmes cada,
    zero empate, e todo valorativo tem excesso positivo (o menor,
    `talk-to-me-2022`, +15,0 pp).

    DESEMPATE, nesta ordem:
      1. a maior frequência MÍNIMA entre os três grupos — o assunto mais
         igualmente compartilhado, que é o sentido de "comum";
      2. a ordem da taxonomia (`eixos.linhas`).

    Sem nenhum eixo ACIMA da média (excesso <= 0), não há assunto comum
    a nomear: devolve None e a home cai no gancho genérico. Eixo ausente
    de `media` conta média zero.

    Calculado para qualquer filme; a home só o usa no estado `valorativo`.
    """
    fs = frequencias_somadas(eixos)
    ordem = [l.get("eixo") for l in (eixos or {}).get("linhas") or []]
    candidatos = [(soma - media.get(e, Fraction(0)), minimo, -ordem.index(e), e)
                  for e, (soma, minimo) in fs.items()]
    if not candidatos:
        return None
    melhor = max(candidatos)
    return melhor[3] if melhor[0] > 0 else None


def titulos_de_exibicao(ficha: dict, slug: str) -> tuple[str, str | None]:
    """(título exibido na home, título nativo como linha secundária).

    Quando `ficha.titulo` não está em alfabeto latino (hoje só
    `woman-of-fire`, "화녀"), a home exibe o título do Letterboxd e, sem
    ele, o título TMDB que provou a identidade da ficha
    (`titulo_tmdb_correspondente`) — desde que ESTES sejam latinos. O
    original vira a linha secundária. Sem alternativa latina, nada muda.
    A página do filme não usa isto (fora do escopo desta rodada)."""
    titulo = ficha.get("titulo") or slug
    if _e_escrita_latina(titulo):
        return titulo, None
    identidade = ficha.get("identidade") or {}
    for alt in (identidade.get("titulo_letterboxd"),
                identidade.get("titulo_tmdb_correspondente")):
        if alt and _e_escrita_latina(alt):
            return alt, titulo
    return titulo, None


def entrada_do_indice(slug: str, filme: dict, data_entrada: str | None,
                      media: dict[str, Fraction] | None = None) -> dict:
    ficha = filme.get("ficha") or {}
    identidade = ficha.get("identidade") or {}
    pb = (filme.get("distribuicao") or {}).get("por_bucket") or {}
    eixos = filme.get("eixos") or {}
    titulo, titulo_nativo = titulos_de_exibicao(ficha, slug)
    return {
        "slug": slug,
        "titulo": titulo,
        "titulo_nativo": titulo_nativo,
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
        "assunto_comum": assunto_comum_dominante(eixos, media or {}),
        # Data de estreia completa (AAAA-MM-DD), para o gancho de
        # aniversário. **A ficha publicada hoje NÃO a tem** — `ficha.py` lê
        # `release_date` do TMDB e guarda só o ano. O campo fica `null` nos
        # 99 até a ficha passar a persistir `data_estreia`; o gancho está
        # pronto e testado, mas não dispara com o dado atual.
        "estreia": ficha.get("data_estreia"),
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
    media = media_do_catalogo(dados, excluidos_da_home())
    for slug in dados["catalogo"]:
        filme = dados["filmes"].get(slug)
        if filme is None:
            continue
        filmes.append(entrada_do_indice(slug, filme, registro.get(slug), media))
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
