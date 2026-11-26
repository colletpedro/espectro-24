"""MEDIÇÃO (não é filtro): reviews que são resumo de trama, sem marcação de spoiler.

Caso de teste: `clebcinestats` em boogie-nights (18.735 caracteres, o filme
inteiro contado com o final, `spoiler=false`). Este script NÃO cria regra
nenhuma na seleção; mede quantas reviews cada regra CANDIDATA tiraria dos
brutos existentes, para o dono decidir.

    python scripts/medir_resumo_de_trama.py [--saida caminho.json]

Regras candidatas:
  R1  comprimento: n_chars > T (T em 5k, 8k, 10k, 15k) — a mais simples;
  R2  abertura em título markdown de nível 3 (`### `) — a assinatura que
      aparece nos resumos: título do filme, ano, ficha técnica e "resumo
      completo". Mede-se sozinha e combinada com n_chars >= 10.000.

Candidatas para o que NÃO abre com `### ` (2026-11-26, medição sem aplicar;
`--candidatas`), todas medidas SEM contar o que a R2 já pega:
  R3  cabeçalho de ficha técnica: >= 3 rótulos distintos (Director/Direção,
      Writer/Roteiro, Cinematography/Fotografia, Editing/Montagem, Music/
      Trilha, Starring/Elenco/Cast, Runtime/Duração, Release/Lançamento,
      Country/País, Genre/Gênero) seguidos de ":" nos primeiros 400
      caracteres — o caso school-of-rock;
  (R3 em duas formas: SEM piso de tamanho ela pega também boletins de nota
  curtos — "Roteiro: 9 Direção: 7 …", 276 caracteres, em district-9 no ar —
  falso positivo que fixou o piso de 3.000 caracteres usado abaixo);
  R4  resumo AUTODECLARADO: nos primeiros 300 caracteres, "resumo/sinopse
      completo(a)", "plot summary", "full plot", "complete synopsis",
      "resumen completo" etc., com n_chars >= 2000;
  R6  parede de texto: n_chars >= 8000 e nenhuma quebra de linha (o formato
      do school-of-rock: ficha + ensaio numa linha só);
  R5  texto longo IMPESSOAL: n_chars >= 8000 e nenhum pronome/possessivo de
      1a pessoa (pt/en/es/fr/it). Resumo e ficha não opinam em 1a pessoa;
      ensaios impessoais genuínos são o risco, e é isso que a amostra de
      exclusões existe para mostrar.

Cada regra é medida no POOL (todas as reviews do bruto) e na AMOSTRA
(`pipeline.amostra_do_bruto`, o que a síntese realmente lê), e se cruza com
`dados/publicados.json` para dizer quais filmes NO AR mudariam.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / "src")]

from espectro24.bruto import carregar  # noqa: E402
from espectro24.pipeline import amostra_do_bruto  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402

LIMITES = (5000, 8000, 10000, 15000)
ABRE_H3 = re.compile(r"\A\s{0,3}###\s+\S")


ROTULOS = {
    "direcao": r"direction|director|dire[cç][aã]o|dirigido", "roteiro": r"writer|written by|screenplay|roteiro|escrito por",
    "fotografia": r"cinematography|fotografia", "montagem": r"editing|montagem|edi[cç][aã]o",
    "musica": r"music|trilha|m[uú]sica", "elenco": r"starring|cast|elenco|estrelando",
    "duracao": r"runtime|dura[cç][aã]o|duration", "lancamento": r"release|lan[cç]amento|released",
    "pais": r"country|pa[ií]s", "genero": r"genre|g[eê]nero"}
ROTULOS_RE = {k: re.compile(r"(?i)\b(?:" + v + r")\s*:") for k, v in ROTULOS.items()}
AUTODECLARADO = re.compile(
    r"(?i)(resumo\s+(completo|da\s+(trama|hist[oó]ria)|do\s+filme)|sinopse\s+completa|plot\s+summary|"
    r"full\s+plot|complete\s+(plot|synopsis)|full\s+synopsis|resumen\s+(completo|de\s+la\s+trama)|"
    r"r[eé]sum[eé]\s+(complet|de\s+l'intrigue))")
PRIMEIRA_PESSOA = re.compile(
    r"(?i)\b(?:i|i'm|i've|i'd|i'll|im|my|me|myself|mine|we|our|us|"
    r"eu|meu|minha|meus|minhas|mim|comigo|n[oó]s|nosso|nossa|"
    r"yo|mi|mis|conmigo|nosotros|"
    r"je|j'|mon|ma|mes|moi|nous|"
    r"io|mio|mia|miei|noi)\b")


def _ficha_tecnica(x) -> bool:
    ini = x.texto[:400]
    return x.n_chars >= 3000 and sum(1 for r in ROTULOS_RE.values() if r.search(ini)) >= 3


def _ficha_tecnica_sem_piso(x) -> bool:
    ini = x.texto[:400]
    return sum(1 for r in ROTULOS_RE.values() if r.search(ini)) >= 3


def _parede_de_texto(x) -> bool:
    return x.n_chars >= 8000 and "\n" not in x.texto.strip()


def _autodeclarado(x) -> bool:
    return x.n_chars >= 2000 and bool(AUTODECLARADO.search(x.texto[:300]))


def _impessoal(x) -> bool:
    return x.n_chars >= 8000 and not PRIMEIRA_PESSOA.search(x.texto)


def candidatas():
    return {"R3_ficha_tecnica_no_cabecalho_n>=3000": _ficha_tecnica,
            "R3x_ficha_tecnica_SEM_piso (evidencia de falso positivo)": _ficha_tecnica_sem_piso,
            "R4_resumo_autodeclarado": _autodeclarado,
            "R5_longo_e_impessoal": _impessoal,
            "R6_parede_de_texto_n>=8000": _parede_de_texto}


def medir_candidatas(brutos=RAIZ / "dados" / "bruto", n_exemplos: int = 10) -> dict:
    """Mede R3-R5 sobre o que a R2 NÃO pega. Nada é aplicado."""
    publicados = set(json.loads((RAIZ / "dados" / "publicados.json").read_text())["slugs"])
    C = candidatas()
    res = {k: {"pool": 0, "amostra": 0, "filmes_amostra": set(), "filmes_no_ar": set(),
               "sobreposicao_R2": 0, "exclusoes": []} for k in C}
    for d in sorted(Path(brutos).iterdir()):
        if not (d / "reviews.jsonl").exists():
            continue
        slug = d.name
        _, rs = carregar(slug, raiz=brutos)
        sel = {r.id for b in amostra_do_bruto(slug, raiz=brutos).values() for r in b}
        for r in rs:
            r2 = bool(ABRE_H3.match(r.texto))
            for k, f in C.items():
                if not f(r):
                    continue
                if r2:
                    res[k]["sobreposicao_R2"] += 1
                    continue
                m = res[k]
                m["pool"] += 1
                na = r.id in sel
                if na:
                    m["amostra"] += 1
                    m["filmes_amostra"].add(slug)
                    if slug in publicados:
                        m["filmes_no_ar"].add(slug)
                m["exclusoes"].append({
                    "slug": slug, "nivel": r.nivel, "n_chars": r.n_chars, "na_amostra": na,
                    "no_ar": slug in publicados, "abertura": r.texto[:170].replace("\n", " ")})
    for m in res.values():
        m["filmes_amostra"] = len(m["filmes_amostra"])
        m["filmes_no_ar"] = sorted(m["filmes_no_ar"])
        m["primeiras_10"] = m["exclusoes"][:n_exemplos]
    return res


def regras():
    r = {f"R1_n_chars>{t}": (lambda x, t=t: x.n_chars > t) for t in LIMITES}
    r["R2_abre_com_###"] = lambda x: bool(ABRE_H3.match(x.texto))
    r["R2b_###_e_n_chars>=10000"] = lambda x: bool(ABRE_H3.match(x.texto)) and x.n_chars >= 10000
    return r


def medir(brutos=RAIZ / "dados" / "bruto") -> dict:
    publicados = set(json.loads((RAIZ / "dados" / "publicados.json").read_text())["slugs"])
    R = regras()
    pool = {k: 0 for k in R}
    amostra = {k: 0 for k in R}
    filmes_amostra = {k: set() for k in R}
    filmes_no_ar = {k: set() for k in R}
    exemplos = {k: [] for k in R}
    total_pool = total_amostra = 0
    for d in sorted(Path(brutos).iterdir()):
        if not (d / "reviews.jsonl").exists():
            continue
        slug = d.name
        _, rs = carregar(slug, raiz=brutos)
        sel = {r.id for b in amostra_do_bruto(slug, raiz=brutos).values() for r in b}
        total_pool += len(rs)
        total_amostra += len(sel)
        for r in rs:
            for k, f in R.items():
                if f(r):
                    pool[k] += 1
                    if r.id in sel:
                        amostra[k] += 1
                        filmes_amostra[k].add(slug)
                        if slug in publicados:
                            filmes_no_ar[k].add(slug)
                    if k in ("R2_abre_com_###", "R1_n_chars>10000"):
                        exemplos[k].append({"slug": slug, "nivel": r.nivel, "n_chars": r.n_chars,
                                            "na_amostra": r.id in sel, "no_ar": slug in publicados,
                                            "abertura": r.texto[:70].replace("\n", " ")})
    return {
        "filmes": sum(1 for d in Path(brutos).iterdir() if (d / "reviews.jsonl").exists()),
        "reviews_no_pool": total_pool, "reviews_na_amostra": total_amostra,
        "regras": {k: {"pool": pool[k], "amostra": amostra[k],
                       "filmes_com_amostra_afetada": len(filmes_amostra[k]),
                       "filmes_no_ar_afetados": sorted(filmes_no_ar[k])} for k in R},
        "exemplos": exemplos,
    }


def efeito_no_caso(slug="boogie-nights", usuario="clebcinestats") -> dict:
    """Seleção do caso de teste COM e SEM o id excluído (simulação, nada gravado)."""
    meta, rs = carregar(slug)
    hist = {float(k): v for k, v in meta["histograma_bruto"].items()}
    alvo = next(r for r in rs if f"/{usuario}/" in r.id)
    antes = selecionar(rs, hist)
    depois = selecionar(rs, hist, excluir_ids=frozenset({alvo.id}))

    def ids(sel):
        return {r.id for b in sel.values() for n in b.niveis.values() for r in n.validas}
    a, d = ids(antes), ids(depois)
    return {"id": alvo.id, "nivel": alvo.nivel, "n_chars": alvo.n_chars,
            "selecionada_hoje": alvo.id in a,
            "n_por_bucket_antes": {n: b.n_final for n, b in antes.items()},
            "n_por_bucket_depois": {n: b.n_final for n, b in depois.items()},
            "entram_no_lugar": sorted(d - a), "saem": sorted(a - d)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida")
    ap.add_argument("--candidatas", action="store_true",
                    help="mede R3-R5 (ficha/resumo sem `### `) em vez da R2")
    a = ap.parse_args()
    if a.candidatas:
        res = medir_candidatas()
        texto = json.dumps(res, ensure_ascii=False, indent=2)
        if a.saida:
            Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
            Path(a.saida).write_text(texto + "\n", encoding="utf-8")
        for k, m in res.items():
            print(k, "pool", m["pool"], "amostra", m["amostra"], "filmes_no_ar", m["filmes_no_ar"],
                  "(+R2 em comum:", m["sobreposicao_R2"], ")")
        sys.exit(0)
    res = {"medicao": medir(), "caso_de_teste": efeito_no_caso()}
    texto = json.dumps(res, ensure_ascii=False, indent=2)
    if a.saida:
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.saida).write_text(texto + "\n", encoding="utf-8")
    print(texto)
