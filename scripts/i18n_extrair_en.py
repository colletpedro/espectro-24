#!/usr/bin/env python3
"""Extrai do `resultado/<slug>.json` as strings em PT que CHEGAM À TELA e
mantém os arquivos de tradução EN em `dados/traducao_en/`.

Offline, zero rede, zero LLM. Só lê JSON e escreve JSON.

O QUE É EXTRAÍDO (só o que o `frontend/js/filme.js` renderiza — ver
`dados/traducao_en/_GUIA.md`, seção "Inventário"):

  - `veredito.texto`                                (veredictoBlock)
  - `buckets[].temas[].tema` e `.exemplo_parafraseado`
        (themeRow; só em bucket com `modo != "sem_analise"`)
  - `condicoes.vale_a_pena[].texto` / `talvez_evite[].texto`
                                                    (colunaDeCondicoes)
  - `narrativa`, UM PARÁGRAFO por string           (narrativaCollapsedBlock,
        que faz `split(/\\n{2,}/)` e um <p> por pedaço)
  - `ficha.generos[]`                               (→ vocabulário)

NÃO é extraído, por não renderizar: `buckets[].observacao_geral`,
`buckets[].niveis`, `eixos.*` (só serve de CHAVE de ordenação; a ordem usa o
tema em PT antes da tradução), `condicoes[].tema_texto`/`rotulo_forca`,
`exemplo_antes_da_guarda`, `descartadas`, `ficha.sinopse_oficial` (a página
não mostra sinopse), metadados.

SAÍDAS
  dados/traducao_en/<slug>.json   um por filme publicado:
      {"_leia", "slug", "fonte_sha256", "titulo_en",
       "textos": {"<PT>": "<EN>"|null}, "_orfaos": {...}}
  dados/traducao_en/_vocabulario.json   o mesmo formato de mapa, para o que
      se repete ENTRE filmes: gêneros e temas que aparecem em >= 2 filmes.

IDEMPOTENTE: reexecutar preserva traduções já preenchidas; strings PT que
sumiram vão para `_orfaos` (com a tradução, caso volte); novas entram com
null. Uma string que passa a pertencer ao vocabulário migra, com sua
tradução, do arquivo do filme para o vocabulário.

Uso:  python3 scripts/i18n_extrair_en.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTADO = ROOT / "resultado"
PUBLICADOS = ROOT / "dados" / "publicados.json"
SAIDA = ROOT / "dados" / "traducao_en"
VOCABULARIO = SAIDA / "_vocabulario.json"

# Um tema entra no vocabulário quando aparece em pelo menos tantos filmes.
MIN_FILMES_VOCABULARIO = 2

LEIA_FILME = (
    "Preencha cada valor null com a tradução EN da chave PT (a chave NUNCA "
    "muda). Regras em dados/traducao_en/_GUIA.md. Não edite 'slug' nem "
    "'fonte_sha256'. Strings repetidas entre filmes estão em "
    "_vocabulario.json, não aqui."
)
LEIA_VOCAB = (
    "Vocabulário compartilhado entre filmes: gêneros e temas que se repetem. "
    "Preencha cada null com a tradução EN da chave PT (a chave NUNCA muda). "
    "Regras em dados/traducao_en/_GUIA.md."
)


# --- leitura ---------------------------------------------------------------

def ler_publicados() -> list[str]:
    return list(json.loads(PUBLICADOS.read_text(encoding="utf-8"))["slugs"])


def sha256_do_resultado(slug: str) -> str:
    return hashlib.sha256((RESULTADO / f"{slug}.json").read_bytes()).hexdigest()


def ler_resultado(slug: str) -> dict:
    return json.loads((RESULTADO / f"{slug}.json").read_text(encoding="utf-8"))


# --- o que renderiza ---------------------------------------------------------

def paragrafos(narrativa: str | None) -> list[str]:
    """Mesma regra do render: `texto.split(/\\n{2,}/)`, trim, descarta vazio."""
    return [p.strip() for p in re.split(r"\n{2,}", narrativa or "") if p.strip()]


def temas_renderizados(d: dict) -> list[str]:
    """Os `tema` que `themeRow` desenha (bucket `sem_analise` não lista temas)."""
    return [t["tema"] for b in d.get("buckets") or [] if b.get("modo") != "sem_analise"
            for t in b.get("temas") or [] if t.get("tema")]


def textos_do_filme(d: dict) -> list[str]:
    """Strings PT visíveis de um filme, sem duplicata, na ordem da página:
    veredito, grupos (tema, exemplo), condições, narrativa."""
    saida: list[str] = []
    vistos: set[str] = set()

    def add(s):
        if isinstance(s, str) and s.strip() and s not in vistos:
            vistos.add(s)
            saida.append(s)

    add((d.get("veredito") or {}).get("texto"))
    for b in d.get("buckets") or []:
        if b.get("modo") == "sem_analise":
            continue
        for t in b.get("temas") or []:
            add(t.get("tema"))
            add(t.get("exemplo_parafraseado"))
    c = d.get("condicoes") or {}
    for lado in c.get("ordem_colunas") or ["vale_a_pena", "talvez_evite"]:
        for cond in c.get(lado) or []:
            add(cond.get("texto"))
    for lado in ("vale_a_pena", "talvez_evite"):      # lado fora de ordem_colunas
        for cond in c.get(lado) or []:
            add(cond.get("texto"))
    for p in paragrafos(d.get("narrativa")):
        add(p)
    return saida


def generos_do_filme(d: dict) -> list[str]:
    return [g for g in (d.get("ficha") or {}).get("generos") or [] if g]


def titulo_en_do_filme(d: dict) -> str | None:
    """Título em inglês/original dedutível: o do Letterboxd (a fonte de
    identidade do filme), com a ficha e a coleta como reserva."""
    f = d.get("ficha") or {}
    for v in ((f.get("identidade") or {}).get("titulo_letterboxd"),
              ((d.get("coleta") or {}).get("identidade_letterboxd") or {}).get("titulo"),
              f.get("titulo_original")):
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def vocabulario_de(resultados: dict[str, dict]) -> list[str]:
    """Gêneros (todos) + temas que se repetem em >= MIN_FILMES filmes.
    Ordem: gêneros por primeira aparição, depois temas por primeira aparição."""
    generos: list[str] = []
    contagem: dict[str, set] = {}
    ordem_temas: list[str] = []
    for slug, d in resultados.items():
        for g in generos_do_filme(d):
            if g not in generos:
                generos.append(g)
        for t in temas_renderizados(d):
            if t not in contagem:
                contagem[t] = set()
                ordem_temas.append(t)
            contagem[t].add(slug)
    temas = [t for t in ordem_temas if len(contagem[t]) >= MIN_FILMES_VOCABULARIO]
    return generos + [t for t in temas if t not in generos]


# --- mesclagem preservando o que já foi traduzido ------------------------------

def mesclar(chaves: list[str], antigo: dict | None, extra_preenchido: dict | None = None):
    """-> (textos, orfaos). `antigo` = {"textos": ..., "_orfaos": ...}.
    `extra_preenchido` = traduções vindas de outro arquivo (migração)."""
    antigo = antigo or {}
    velhos = dict(antigo.get("textos") or {})
    orf_velhos = dict(antigo.get("_orfaos") or {})
    extra = extra_preenchido or {}
    textos: dict[str, str | None] = {}
    for k in chaves:
        v = velhos.get(k)
        if v is None:
            v = orf_velhos.get(k)          # string que voltou
        if v is None:
            v = extra.get(k)
        textos[k] = v if isinstance(v, str) and v.strip() else None
    orfaos = {}
    for k, v in {**orf_velhos, **velhos}.items():
        if k not in textos and isinstance(v, str) and v.strip():
            orfaos[k] = v                   # só vale guardar o que foi traduzido
    return textos, orfaos


def _ler_json(caminho: Path) -> dict | None:
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def _escrever(caminho: Path, obj: dict) -> bool:
    texto = json.dumps(obj, ensure_ascii=False, indent=1) + "\n"
    if caminho.exists() and caminho.read_text(encoding="utf-8") == texto:
        return False
    caminho.write_text(texto, encoding="utf-8")
    return True


def montar(saida: Path = SAIDA, slugs: list[str] | None = None, escrever: bool = True):
    """Gera/atualiza os arquivos. Devolve {"vocabulario": dict, "filmes": {slug: dict}}."""
    slugs = slugs if slugs is not None else ler_publicados()
    resultados = {s: ler_resultado(s) for s in slugs}
    vocab_chaves = vocabulario_de(resultados)
    vocab_set = set(vocab_chaves)
    saida.mkdir(parents=True, exist_ok=True)

    # traduções já feitas por filme de strings que agora são vocabulário
    migradas: dict[str, str] = {}
    antigos: dict[str, dict | None] = {}
    for s in slugs:
        antigo = _ler_json(saida / f"{s}.json")
        antigos[s] = antigo
        for k, v in ((antigo or {}).get("textos") or {}).items():
            if k in vocab_set and isinstance(v, str) and v.strip():
                migradas.setdefault(k, v)

    textos_v, orfaos_v = mesclar(vocab_chaves, _ler_json(saida / "_vocabulario.json"), migradas)
    vocab = {"_leia": LEIA_VOCAB, "textos": textos_v, "_orfaos": orfaos_v}
    if escrever:
        _escrever(saida / "_vocabulario.json", vocab)

    filmes = {}
    for s in slugs:
        d = resultados[s]
        chaves = [t for t in textos_do_filme(d) if t not in vocab_set]
        textos, orfaos = mesclar(chaves, antigos[s])
        titulo = (antigos[s] or {}).get("titulo_en") or titulo_en_do_filme(d)
        obj = {"_leia": LEIA_FILME, "slug": s, "fonte_sha256": sha256_do_resultado(s),
               "titulo_en": titulo, "textos": textos, "_orfaos": orfaos}
        filmes[s] = obj
        if escrever:
            _escrever(saida / f"{s}.json", obj)
    return {"vocabulario": vocab, "filmes": filmes}


def main(argv=None) -> int:
    r = montar()
    vocab, filmes = r["vocabulario"], r["filmes"]
    tamanhos = sorted(sum(len(k) for k in f["textos"]) for f in filmes.values())
    n = sum(len(f["textos"]) for f in filmes.values())
    pend = sum(1 for f in filmes.values() for v in f["textos"].values() if v is None)
    pend += sum(1 for v in vocab["textos"].values() if v is None)
    print(f"{len(filmes)} filmes; {n} strings por filme + {len(vocab['textos'])} no vocabulário; "
          f"{pend} pendentes (null)")
    if tamanhos:
        print(f"caracteres PT por filme: min {tamanhos[0]}, mediana {tamanhos[len(tamanhos)//2]}, "
              f"máx {tamanhos[-1]}; total {sum(tamanhos)} (+ vocabulário "
              f"{sum(len(k) for k in vocab['textos'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
