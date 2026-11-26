"""Adaptador de importação MANUAL do Letterboxd -> `dados/bruto/<slug>/`.

O Letterboxd bloqueia a coleta automatizada; o dono exporta à mão, pelo
navegador, dois arquivos por filme:

    meta.json       slug, titulo, ano, tmdb_id, histograma, total_notas, coletado_em
    reviews.jsonl   review_id, url, usuario, nota, data, spoiler, review

Este script grava o MESMO formato que o coletor produz (`bruto.ReviewBruta` +
`meta.json`), então o resto do pipeline não sabe a diferença. **Nenhuma
requisição ao Letterboxd** — a única rede é o TMDB, pelo caminho normal da
ficha (`ficha.buscar_ficha`), para provar a identidade.

    python scripts/importar_manual.py --meta M.json --reviews R.jsonl [--dry-run]
    python scripts/importar_manual.py --pasta dados/importacao/boogie-nights

Decisões (cada uma com a razão, para o dono poder discordar):

- **Recusa do arquivo INTEIRO** (nada é gravado) se faltar campo obrigatório,
  houver nota fora de 0,5-5,0 (ou fora da grade de meias-estrelas), histograma
  cuja soma não bata com `total_notas`, ou uma review cujo `review_id`/`url`
  aponte para OUTRO filme (arquivo misturado).
- **Identidade**: o `tmdb_id` do meta é conferido contra o TMDB por
  `buscar_ficha` (título por igualdade normalizada, duração >= 40 min) e o ano
  contra o do TMDB (tolerância de 1, a mesma da etapa 2). Divergência ->
  QUARENTENA (`dados/importacao/_quarentena/<slug>/`), nada vai para o bruto.
- **spoiler**: o coletor persistia `spoiler_flag` e NÃO excluía na coleta; quem
  exclui é `selecao.selecionar(excluir_spoiler=True)`, o default de produção.
  Aqui acontece o mesmo: o flag é gravado e a seleção decide. (Diferença que
  vale saber: no coletor o texto de uma review-spoiler era o placeholder do
  Letterboxd; na exportação manual vem o texto real. A seleção não o lê.)
- **data**: vem do DIÁRIO e pode não ser a data de publicação. O meta registra
  isso e o adaptador NÃO calcula `janela_temporal` nem `dias_por_100_paginas`.
- **pagina_origem**: não existe na exportação manual. Fica 1 (constante) e o
  meta diz que é "nao_aplicavel"; sem `orcamento_paginas_por_nivel` no meta a
  seleção não estratifica por profundidade.
- **Duplicata**: chave primária `review_id`; secundária `url` (o `id` do coletor
  é `viewing:<n>`, a `url` é a mesma da exportação — sem isso a dedupe contra o
  bruto antigo nunca casaria).
- **Países (`ficha.paises`)**: nem o coletor nem `buscar_ficha` preenchem — a
  lista (ISO 3166-1, ordem do TMDB) sempre veio de um passo EDITORIAL depois
  (`medir_editorial.py`, `preparar_publicacao_29.py`), lendo
  `production_countries` do detalhe do TMDB. Um filme importado sem esse passo
  chegava à publicação com `ficha.paises` vazio (e `test_paises_editorial`
  exige). Aqui o adaptador lê o MESMO detalhe (cache
  `dados/cache/_tmdb_detalhe/<id>.json`, o que o teste de países confere) e
  grava `paises_tmdb` no meta; `ficha_com_paises` o põe na ficha. TMDB sem
  país -> recusa clara.
- **Mesmo usuário, mais de uma review**: a seleção NÃO tem regra por autor
  (`autor_hash` só existe para medir diversidade). Todas são gravadas e o
  relatório lista os casos; nenhuma regra é inventada aqui.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / "src")]

from espectro24.atomico import escrever_atomico  # noqa: E402
from espectro24.bruto import (  # noqa: E402
    ReviewBruta, autor_hash, carregar, persistir)
from espectro24.buckets import NIVEIS  # noqa: E402

ORIGEM = "importacao_manual"
DURACAO_MIN_LONGA = 40
TOLERANCIA_ANO = 1
CAMPOS_META = ("slug", "titulo", "ano", "tmdb_id", "histograma",
               "total_notas", "coletado_em")
CAMPOS_REVIEW = ("review_id", "url", "usuario", "nota", "data", "spoiler",
                 "review")
RAIZ_IMPORTACAO = RAIZ / "dados" / "importacao"
RAIZ_BRUTO = RAIZ / "dados" / "bruto"
CACHE_FICHA = RAIZ / "dados" / "cache" / "ficha_importacao"
CACHE_DETALHE_TMDB = RAIZ / "dados" / "cache" / "_tmdb_detalhe"

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_.]*$")


class ImportacaoRecusada(ValueError):
    """O arquivo inteiro é recusado; nada é gravado."""


class IdentidadeDivergente(ImportacaoRecusada):
    """A identidade (TMDB) não confere: o material vai para a quarentena."""


# --------------------------------------------------------------------------
# normalização e validação (funções puras)
# --------------------------------------------------------------------------

def normalizar_slug(valor: str) -> str:
    """`/film/boogie-nights/` -> `boogie-nights` (também aceita URL completa)."""
    if not isinstance(valor, str) or not valor.strip():
        raise ImportacaoRecusada(f"slug ausente ou vazio: {valor!r}")
    s = valor.strip()
    s = re.sub(r"^https?://[^/]+", "", s)
    partes = [p for p in s.split("?")[0].split("#")[0].split("/") if p]
    if len(partes) == 2 and partes[0] == "film":
        partes = partes[1:]
    if len(partes) != 1 or partes[0] == "film" or not _SLUG_RE.match(partes[0]):
        raise ImportacaoRecusada(f"slug não normalizável: {valor!r}")
    return partes[0]


def _nota_valida(n) -> float:
    if isinstance(n, bool) or not isinstance(n, (int, float)):
        raise ImportacaoRecusada(f"nota não numérica: {n!r}")
    f = float(n)
    if not (0.5 <= f <= 5.0):
        raise ImportacaoRecusada(f"nota fora de 0,5-5: {n!r}")
    if f not in NIVEIS:
        raise ImportacaoRecusada(f"nota fora da grade de meias-estrelas: {n!r}")
    return f


def validar_histograma(hist, total_notas) -> dict[str, int]:
    """Normaliza as chaves para a forma do coletor (`"1.0"`) e confere a soma."""
    if not isinstance(hist, dict) or not hist:
        raise ImportacaoRecusada("histograma ausente ou vazio")
    if isinstance(total_notas, bool) or not isinstance(total_notas, int) or total_notas <= 0:
        raise ImportacaoRecusada(f"total_notas inválido: {total_notas!r}")
    saida: dict[str, int] = {}
    for k, v in hist.items():
        try:
            nivel = float(k)
        except (TypeError, ValueError):
            raise ImportacaoRecusada(f"histograma com chave inválida: {k!r}")
        if nivel not in NIVEIS:
            raise ImportacaoRecusada(f"histograma com nível inexistente: {k!r}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ImportacaoRecusada(f"histograma com contagem inválida em {k!r}: {v!r}")
        chave = str(nivel)
        if chave in saida:
            raise ImportacaoRecusada(f"histograma com nível repetido: {k!r}")
        saida[chave] = v
    for n in NIVEIS:
        saida.setdefault(str(n), 0)
    soma = sum(saida.values())
    if soma != total_notas:
        raise ImportacaoRecusada(
            f"histograma não bate com total_notas: soma={soma} total_notas={total_notas}")
    return {str(n): saida[str(n)] for n in NIVEIS}


def validar_meta(meta) -> dict:
    """Devolve o meta normalizado (slug limpo, histograma na forma do coletor)."""
    if not isinstance(meta, dict):
        raise ImportacaoRecusada("meta.json não é um objeto")
    faltando = [c for c in CAMPOS_META if meta.get(c) in (None, "", {})]
    if faltando:
        raise ImportacaoRecusada(f"meta.json sem campo obrigatório: {', '.join(faltando)}")
    slug = normalizar_slug(meta["slug"])
    if not isinstance(meta["titulo"], str) or not meta["titulo"].strip():
        raise ImportacaoRecusada("titulo inválido")
    try:
        ano = int(meta["ano"])
        tmdb_id = int(str(meta["tmdb_id"]).strip())
    except (TypeError, ValueError):
        raise ImportacaoRecusada(f"ano/tmdb_id não numéricos: {meta['ano']!r}/{meta['tmdb_id']!r}")
    if not (1880 <= ano <= 2100) or tmdb_id <= 0:
        raise ImportacaoRecusada(f"ano/tmdb_id fora do plausível: {ano}/{tmdb_id}")
    try:
        datetime.fromisoformat(str(meta["coletado_em"]))
    except ValueError:
        raise ImportacaoRecusada(f"coletado_em não é ISO-8601: {meta['coletado_em']!r}")
    return {
        "slug": slug, "titulo": meta["titulo"].strip(), "ano": ano,
        "tmdb_id": tmdb_id, "coletado_em": str(meta["coletado_em"]),
        "total_notas": meta["total_notas"],
        "histograma": validar_histograma(meta["histograma"], meta["total_notas"]),
    }


def _data_valida(d) -> str:
    if not isinstance(d, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        raise ImportacaoRecusada(f"data fora do formato AAAA-MM-DD: {d!r}")
    try:
        datetime.strptime(d, "%Y-%m-%d")
    except ValueError:
        raise ImportacaoRecusada(f"data inexistente: {d!r}")
    return d


def validar_review(linha: dict, n_linha: int, slug: str) -> ReviewBruta:
    if not isinstance(linha, dict):
        raise ImportacaoRecusada(f"linha {n_linha}: não é um objeto")
    faltando = [c for c in CAMPOS_REVIEW if c not in linha or linha[c] is None]
    if faltando:
        raise ImportacaoRecusada(f"linha {n_linha}: sem campo obrigatório: {', '.join(faltando)}")
    for c in ("review_id", "url", "usuario", "review"):
        if not isinstance(linha[c], str) or not linha[c].strip():
            raise ImportacaoRecusada(f"linha {n_linha}: campo {c!r} vazio ou não textual")
    if not isinstance(linha["spoiler"], bool):
        raise ImportacaoRecusada(f"linha {n_linha}: spoiler não booleano: {linha['spoiler']!r}")
    try:
        nota = _nota_valida(linha["nota"])
        data = _data_valida(linha["data"])
    except ImportacaoRecusada as e:
        raise ImportacaoRecusada(f"linha {n_linha}: {e}")
    rid = linha["review_id"].strip()
    # O film-slug está em `/<usuario>/film/<slug>/[n/]`; arquivo com review de
    # outro filme é arquivo misturado, não material parcial.
    m = re.fullmatch(r"/([^/]+)/film/([^/]+)/(?:\d+/)?", rid)
    if not m:
        raise ImportacaoRecusada(f"linha {n_linha}: review_id fora do padrão: {rid!r}")
    if m.group(2) != slug:
        raise ImportacaoRecusada(
            f"linha {n_linha}: review_id de outro filme ({m.group(2)!r} != {slug!r})")
    if m.group(1) != linha["usuario"].strip():
        raise ImportacaoRecusada(
            f"linha {n_linha}: review_id de outro usuário ({m.group(1)!r} != {linha['usuario']!r})")
    texto = linha["review"]
    return ReviewBruta(
        id=rid, nivel=nota, texto=texto, n_chars=len(texto),
        spoiler_flag=linha["spoiler"], pagina_origem=1,
        url=linha["url"].strip(), autor_hash=autor_hash(linha["usuario"].strip()),
        truncada=False, texto_completo=True, data=data,
        ordenacao_origem=ORIGEM)


def ler_reviews(caminho: Path, slug: str) -> list[ReviewBruta]:
    """Lê o jsonl INTEIRO. Linha corrompida recusa o arquivo (aqui NÃO se ignora
    linha ruim em silêncio: o material é pequeno e foi feito à mão)."""
    brutas: list[ReviewBruta] = []
    texto = Path(caminho).read_text(encoding="utf-8")
    n = 0
    for i, linha in enumerate(texto.splitlines(), 1):
        if not linha.strip():
            continue
        n += 1
        try:
            obj = json.loads(linha)
        except ValueError as e:
            raise ImportacaoRecusada(f"linha {i}: JSON inválido ({e})")
        brutas.append(validar_review(obj, i, slug))
    if not n:
        raise ImportacaoRecusada("reviews.jsonl sem nenhuma review")
    return brutas


def usuarios_repetidos(caminho: Path) -> dict[str, list[dict]]:
    """`{usuario: [{review_id, nota, n_chars, spoiler}, ...]}` só dos repetidos."""
    por: dict[str, list[dict]] = {}
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        o = json.loads(linha)
        por.setdefault(o["usuario"], []).append(
            {"review_id": o["review_id"], "nota": o["nota"],
             "n_chars": len(o["review"]), "spoiler": o["spoiler"]})
    return {u: v for u, v in por.items() if len(v) > 1}


def sha256_arquivo(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# identidade (TMDB, pelo caminho normal da ficha)
# --------------------------------------------------------------------------

FichaFn = Callable[[dict], tuple]


def chave_tmdb() -> str:
    """A chave do TMDB, do ambiente ou do `.env`. Lê SÓ essa chave: `load_dotenv`
    despejaria no ambiente do processo as de todos os providers, e quem importa
    este módulo (testes, outros scripts) herdaria isso."""
    import os
    from dotenv import dotenv_values
    chave = os.environ.get("TMDB_API_KEY") or dotenv_values(RAIZ / ".env").get("TMDB_API_KEY")
    if not chave:
        raise ImportacaoRecusada("TMDB_API_KEY ausente: identidade não verificável")
    return chave


def ficha_normal(identidade: dict) -> tuple:
    """`buscar_ficha` com a identidade do meta — o MESMO caminho de produção."""
    from espectro24.ficha import buscar_ficha
    return buscar_ficha(identidade["titulo"], identidade["ano"], CACHE_FICHA,
                        api_key=chave_tmdb(), identidade=identidade)


PaisesFn = Callable[[int], list]


def validar_paises(paises, tmdb_id) -> list[str]:
    """Lista de códigos ISO 3166-1 alfa-2, sem repetição; vazia é recusa."""
    if (not isinstance(paises, list) or not paises
            or not all(isinstance(p, str) and re.fullmatch(r"[A-Z]{2}", p) for p in paises)
            or len(set(paises)) != len(paises)):
        raise ImportacaoRecusada(
            f"TMDB {tmdb_id}: production_countries ausente/inválido ({paises!r}); "
            "a ficha não pode ser publicada sem `paises`")
    return list(paises)


def paises_do_tmdb(tmdb_id: int, *, cache: Path | None = None, session=None) -> list[str]:
    """`production_countries` do detalhe do TMDB (cache `_tmdb_detalhe`, o que
    `test_paises_editorial` confere), como lista ISO na ordem do TMDB."""
    cache = Path(cache) if cache else CACHE_DETALHE_TMDB
    arq = cache / f"{tmdb_id}.json"
    if arq.exists():
        det = json.loads(arq.read_text(encoding="utf-8"))
    else:
        import requests
        chave = chave_tmdb()
        r = (session or requests).get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}",
            params={"api_key": chave, "language": "en-US"}, timeout=30)
        r.raise_for_status()
        det = r.json()
        if int(det.get("id") or 0) != int(tmdb_id):
            raise ImportacaoRecusada(f"TMDB devolveu outro id ({det.get('id')}) para {tmdb_id}")
        cache.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(det, ensure_ascii=False, indent=2), encoding="utf-8")
    return validar_paises([c.get("iso_3166_1") for c in det.get("production_countries") or []],
                          tmdb_id)


def ficha_com_paises(ficha: dict, meta_bruto: dict) -> dict:
    """A ficha com `paises` do meta do bruto. Falta de `paises_tmdb` é erro, não
    lista vazia: publicar sem país é exatamente o que este passo existe para evitar."""
    paises = validar_paises(meta_bruto.get("paises_tmdb"), ficha.get("tmdb_id"))
    return {**ficha, "paises": paises}


def identidade_do_import(meta: dict) -> dict:
    return {"slug": meta["slug"], "titulo": meta["titulo"], "ano": meta["ano"],
            "tmdb_id_letterboxd": meta["tmdb_id"], "fonte": ORIGEM}


def verificar_identidade(meta: dict, ficha_fn: FichaFn) -> dict:
    """Levanta `IdentidadeDivergente` se o TMDB não comprovar a obra.

    Confere (1) título e duração >= 40 min, dentro de `buscar_ficha`, e
    (2) duração e ano de novo aqui, de forma independente: quem importa não
    confia só no `None`/dict de um chamador.
    """
    ident = identidade_do_import(meta)
    ficha, aviso, descarte = ficha_fn(ident)
    if ficha is None:
        motivo = (descarte or {}).get("motivo") or "ficha_indisponivel"
        raise IdentidadeDivergente(f"{motivo}: {aviso}")
    if int(ficha.get("tmdb_id") or 0) != meta["tmdb_id"]:
        raise IdentidadeDivergente(
            f"tmdb_id da ficha ({ficha.get('tmdb_id')}) != meta ({meta['tmdb_id']})")
    dur = ficha.get("duracao_min")
    if dur is None or dur < DURACAO_MIN_LONGA:
        raise IdentidadeDivergente(f"duração {dur!r} < {DURACAO_MIN_LONGA} min")
    ano_tmdb = ((ficha.get("identidade") or {}).get("ano_tmdb")
                or ficha.get("ano"))
    if ano_tmdb is None or abs(int(ano_tmdb) - meta["ano"]) > TOLERANCIA_ANO:
        raise IdentidadeDivergente(
            f"ano do meta ({meta['ano']}) vs TMDB ({ano_tmdb}): diferença > {TOLERANCIA_ANO}")
    return ficha


# --------------------------------------------------------------------------
# importação
# --------------------------------------------------------------------------

def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _meta_do_bruto(meta: dict, brutas: list[ReviewBruta], arquivos: dict,
                   resumo: dict, agora: str) -> dict:
    por_nivel: dict[str, int] = {}
    for r in brutas:
        por_nivel[str(r.nivel)] = por_nivel.get(str(r.nivel), 0) + 1
    return {
        "slug": meta["slug"],
        "coletado_em": meta["coletado_em"],
        "versao_coletor": ORIGEM,
        "ordenacao_usada": ORIGEM,
        "histograma_bruto": meta["histograma"],
        "total_notas": meta["total_notas"],
        "contagem_bruta_por_nivel": dict(sorted(por_nivel.items(), key=lambda kv: float(kv[0]))),
        "ano_lancamento": meta["ano"],
        "ano_fonte": ORIGEM,
        "identidade_letterboxd": identidade_do_import(meta),
        "importacao_manual": {
            "origem": ORIGEM,
            "importado_em": agora,
            "arquivos": arquivos,
            **resumo,
            "data_semantica": "diario: pode NAO ser a data de publicacao da review",
            "janela_temporal": "nao_calculada (depende de data)",
            "pagina_origem": "nao_aplicavel: constante 1, sem estratificacao por profundidade",
            "ordenacao_do_export": "desconhecida (o arquivo nao a declara)",
            "texto": "integral declarado pelo exportador (truncada=false)",
            "spoiler": "flag gravado; a exclusao e da selecao (excluir_spoiler=True)",
            "identidade": "tmdb_id do meta conferido no TMDB por buscar_ficha",
        },
    }


def importar(arq_meta: Path, arq_reviews: Path, *,
             raiz_bruto: Path = RAIZ_BRUTO,
             raiz_importacao: Path = RAIZ_IMPORTACAO,
             ficha_fn: FichaFn = ficha_normal,
             paises_fn: PaisesFn = paises_do_tmdb,
             dry_run: bool = False,
             agora: str | None = None) -> dict:
    """Importa UM filme. Devolve o relatório; levanta `ImportacaoRecusada`.

    Ordem: valida tudo (sem tocar o disco) -> confere identidade (TMDB) ->
    grava. Qualquer recusa antes da gravação deixa `dados/bruto` intacto.
    """
    arq_meta, arq_reviews = Path(arq_meta), Path(arq_reviews)
    try:
        bruto_meta = json.loads(arq_meta.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ImportacaoRecusada(f"meta.json inválido: {e}")
    meta = validar_meta(bruto_meta)
    slug = meta["slug"]
    brutas = ler_reviews(arq_reviews, slug)

    ids_no_arquivo: dict[str, ReviewBruta] = {}
    duplicadas_no_arquivo = 0
    for r in brutas:
        if r.id in ids_no_arquivo:
            duplicadas_no_arquivo += 1
            continue
        ids_no_arquivo[r.id] = r
    unicas = list(ids_no_arquivo.values())

    try:
        verificar_identidade(meta, ficha_fn)
    except IdentidadeDivergente as e:
        if not dry_run:
            destino = Path(raiz_importacao) / "_quarentena" / slug
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copy2(arq_meta, destino / "meta.json")
            shutil.copy2(arq_reviews, destino / "reviews.jsonl")
            escrever_atomico(destino / "motivo.json", json.dumps(
                {"motivo": str(e), "em": agora or _agora()}, ensure_ascii=False, indent=2) + "\n")
        raise

    # só depois da identidade provada: país de obra não comprovada não interessa
    paises = validar_paises(paises_fn(meta["tmdb_id"]), meta["tmdb_id"])

    meta_antigo, existentes = carregar(slug, raiz=raiz_bruto)
    ids_existentes = {r.id for r in existentes}
    urls_existentes = {r.url for r in existentes if r.url}
    novas: list[ReviewBruta] = []
    ja_por_id = ja_por_url = 0
    for r in unicas:
        if r.id in ids_existentes:
            ja_por_id += 1
        elif r.url in urls_existentes:
            ja_por_url += 1
        else:
            novas.append(r)

    agora = agora or _agora()
    arquivos = {"meta": {"nome": arq_meta.name, "sha256": sha256_arquivo(arq_meta)},
                "reviews": {"nome": arq_reviews.name, "sha256": sha256_arquivo(arq_reviews)}}
    resumo = {"n_linhas_arquivo": len(brutas),
              "n_duplicadas_no_arquivo": duplicadas_no_arquivo,
              "n_ja_existentes_por_id": ja_por_id,
              "n_ja_existentes_por_url": ja_por_url,
              "n_novas": len(novas)}

    novo_meta = _meta_do_bruto(meta, unicas, arquivos, resumo, agora)
    novo_meta["paises_tmdb"] = paises
    modo = "novo"
    if meta_antigo:
        # Já existe bruto deste filme (coletor ou importação anterior): o meta
        # existente NÃO é sobrescrito — ele descreve a coleta que gerou aquelas
        # reviews (orçamento de páginas, ordenação). A importação entra como
        # bloco aditivo; a mesma dupla de arquivos (mesmos sha256) não é
        # registrada duas vezes.
        modo = "mescla"
        anteriores = list(meta_antigo.get("importacoes_manuais") or [])
        ja_vistos = [a.get("arquivos") for a in anteriores]
        if isinstance(meta_antigo.get("importacao_manual"), dict):
            ja_vistos.append(meta_antigo["importacao_manual"].get("arquivos"))
        novo_meta = dict(meta_antigo)
        novo_meta["paises_tmdb"] = paises
        if arquivos not in ja_vistos:
            novo_meta["importacoes_manuais"] = anteriores + [
                _meta_do_bruto(meta, unicas, arquivos, resumo, agora)["importacao_manual"]]

    relatorio = {
        "slug": slug, "modo": modo, "dry_run": dry_run, **resumo,
        "n_total_apos": len(existentes) + len(novas),
        "usuarios_repetidos": usuarios_repetidos(arq_reviews),
        "paises": paises,
        "spoilers_no_arquivo": sum(1 for r in unicas if r.spoiler_flag),
        "arquivos": arquivos,
    }
    if not dry_run:
        persistir(slug, novo_meta, novas, raiz=raiz_bruto)
    return relatorio


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pasta", help="pasta com meta.json e reviews.jsonl")
    ap.add_argument("--meta")
    ap.add_argument("--reviews")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.pasta:
        meta, revs = Path(a.pasta) / "meta.json", Path(a.pasta) / "reviews.jsonl"
    elif a.meta and a.reviews:
        meta, revs = Path(a.meta), Path(a.reviews)
    else:
        ap.error("informe --pasta ou --meta e --reviews")
    try:
        rel = importar(meta, revs, dry_run=a.dry_run)
    except IdentidadeDivergente as e:
        print(f"QUARENTENA: {e}", file=sys.stderr)
        return 3
    except ImportacaoRecusada as e:
        print(f"RECUSADO (nada gravado): {e}", file=sys.stderr)
        return 2
    print(json.dumps(rel, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
