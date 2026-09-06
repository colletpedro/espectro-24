#!/usr/bin/env python3
"""[v1.9.39] Backfill único: acrescenta `galeria_stills` à `ficha` dos 35
`resultado/*.json` já publicados — SEM reabrir a desambiguação de
`/search/movie` (docstring de `buscar_ficha`, §1.2: "Reconsultar o TMDB é
reabrir a desambiguação que já ocorreu").

Mudança de escopo AUTORIZADA pelo dono do produto: a galeria passa a
mostrar STILLS (backdrops 16:9), não mais pôsteres alternativos —
`galeria_posters` (v1.9.38, `scripts/popular_galeria.py`) foi REMOVIDO, não
convive com o campo novo. RISCO DE SPOILER ASSUMIDO explicitamente: nenhum
filtro anti-spoiler é aplicado (ver docstring de `ficha.py`).

Usa o `tmdb_id` JÁ RESOLVIDO e gravado em cada ficha, chamando só
`/movie/{id}` com o MESMO `include_image_language=pt,null` de sempre — o
mesmo dado que `buscar_ficha` já teria trazido se os 35 fossem buscados de
novo hoje, sem o risco de o `/search/movie` escolher um id diferente numa
segunda chamada. O subconjunto `iso_639_1 is None` não muda entre pedir
`pt,null` ou pedir só `null` (medido ao vivo, ETAPA 0: idêntico nos dois
casos) — o filtro de still não perde nada usando o mesmo parâmetro que o
resto do pipeline já usa.

Aplica o mesmo filtro de duração da lib (`duracao_compativel_com_longa`,
`ficha.py` — NÃO é guarda de identidade, ver a docstring da função — e
fica MAIS importante com a troca para stills, ver o comentário de
`GALERIA_DURACAO_MIN_FEATURE`) e grava o resultado tanto em
`resultado/{slug}.json` (fonte de verdade) quanto no cache
`dados/cache/_tmdb/*.json` (para que uma reexecução futura de
`buscar_ficha` veja a entrada como completa e não regaste rede à toa).

[v1.9.40] Passa a calcular o pHash das candidatas e a entregá-lo a
`_stills`, que agora DEDUPLICA (`_deduplicar`) e AMOSTRA ESPALHADO
(`_amostra_espalhada`) em vez de cortar o top-N. Isso acrescenta REDE ao
backfill — uma imagem `w300` por candidata, ~20 kB — que antes não
existia; o cache em `dados/cache/_stills_w300/` e o memo de hashes em
`dados/cache/_stills_phash.json` (ambos sob `.gitignore`, mesmo estatuto
do cache do TMDB) fazem a segunda execução não baixar nada.

**Diferente de `_hashes_dos_candidatos` dentro da ficha em produção
(`cli.py`/`lote.py`), este script FALHA se Pillow/imagehash não
estiverem instalados — não degrada.** A distinção é deliberada: a ficha
geral é aditiva por princípio (§1.2 — "nenhuma imagem derruba o
pipeline"), porque ela compete por confiabilidade com coleta de reviews,
narrativa e classificação, que não têm nada a ver com still. ESTE script
não tem mais nenhuma outra tarefa: rodar sem dedup e ainda assim
imprimir "35/35 ok" seria publicar de novo o exato defeito que ele
existe para consertar, agora com um "sucesso" que esconde isso. Ver
`_exigir_dependencias_dedup`.

Uso:
    python scripts/popular_stills.py                 # os 35
    python scripts/popular_stills.py --slug talk-to-me-2022
    python scripts/popular_stills.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.ficha import (  # noqa: E402
    _deduplicar,
    _still_16_9,
    TMDB_BASE,
    TMDB_IMAGE_LANGS,
    _cache_key,
    _hashes_dos_candidatos,
    _melhor,
    _stills,
    duracao_compativel_com_longa,
)

RESULTADO = ROOT / "resultado"
CACHE_TMDB = ROOT / "dados" / "cache" / "_tmdb"


def _api_key() -> str:
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key
    for linha in (ROOT / ".env").read_text().splitlines():
        if linha.startswith("TMDB_API_KEY"):
            return linha.split("=", 1)[1].strip()
    raise SystemExit("TMDB_API_KEY não encontrada (nem no ambiente, nem em .env)")


def _exigir_dependencias_dedup() -> None:
    """FALHA alto e cedo se Pillow/imagehash não estiverem instalados —
    não degrada (v1.9.40).

    Este script existe SÓ para popular `galeria_stills` deduplicada.
    `_hashes_dos_candidatos` (`ficha.py`) engole `ImportError` de propósito
    — é código de produção compartilhado com `cli.py`/`lote.py`, onde a
    ficha inteira é aditiva por princípio (§1.2) e uma dependência de
    imagem ausente não pode derrubar a coleta de reviews de 35 filmes.
    ESTE script não tem esse motivo: sem as libs, ele reescreveria os 35
    `resultado/*.json` com o TOP-N por `vote_average` — a lista com
    quadro repetido que a v1.9.40 existe para eliminar — e ainda
    imprimiria "35/35 ok", uma falsa confirmação de que a galeria foi
    consertada. Verificado, não checado por sondar a versão instalada:
    tentar o import de verdade é a única forma de saber que `Image.open`
    e `imagehash.phash` vão funcionar quando `still_hash.py` os chamar.
    """
    faltando = []
    try:
        import PIL  # noqa: F401
    except ImportError:
        faltando.append("Pillow")
    try:
        import imagehash  # noqa: F401
    except ImportError:
        faltando.append("imagehash")
    if faltando:
        raise SystemExit(
            f"Dependência(s) de dedup ausente(s): {', '.join(faltando)}. "
            "Este script (diferente da ficha em produção) NÃO degrada — "
            "instale com `pip install -e '.[stills]'` antes de rodar, ou "
            "a galeria sai com quadro repetido igual à v1.9.39.")


def _catalogo() -> list[str]:
    with open(RESULTADO / "votacao-3" / "consenso.jsonl") as f:
        return sorted({json.loads(l)["slug"] for l in f if l.strip()})


def _cache_path_para(slug: str, d: dict) -> Path | None:
    """Acha o arquivo de cache correspondente a esta ficha pela mesma
    `_cache_key(titulo, ano)` que `buscar_ficha` usa — sem isso o cache
    ficaria desatualizado (`galeria_stills` ausente) e uma reexecução
    futura da ficha completa reabriria rede à toa achando-o incompleto."""
    ficha = d.get("ficha") or {}
    # o título usado na busca original é o do PRÓPRIO slug/ano — mesma
    # derivação de `titulo_ano_de_slug`, já que é essa chamada que
    # `publicar_catalogo`/`cli` fazem antes de bater no TMDB.
    import re as _re
    m = _re.match(r"^(.*)-(\d{4})$", slug)
    if m:
        titulo, ano = m.group(1).replace("-", " "), int(m.group(2))
    else:
        titulo, ano = slug.replace("-", " "), ficha.get("ano")
    chave = _cache_key(titulo, ano)
    p = CACHE_TMDB / f"{chave}.json"
    return p if p.exists() else None


def processar(slug: str, key: str, sess: requests.Session, *, dry_run: bool) -> dict:
    p = RESULTADO / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "status": "sem_resultado"}
    d = json.loads(p.read_text(encoding="utf-8"))
    ficha = d.get("ficha")
    if not ficha or not ficha.get("tmdb_id"):
        return {"slug": slug, "status": "sem_ficha_ou_tmdb_id"}

    tmdb_id = ficha["tmdb_id"]
    duracao_min = ficha.get("duracao_min")

    resp = sess.get(f"{TMDB_BASE}/movie/{tmdb_id}", params={
        "api_key": key, "language": "pt-BR",
        "append_to_response": "images",
        "include_image_language": TMDB_IMAGE_LANGS,
    })
    if resp.status_code != 200:
        return {"slug": slug, "status": f"http_{resp.status_code}"}
    detalhes = resp.json()
    imagens = detalhes.get("images") or {}

    # O hero, e por que agora é o `backdrop_path` PUBLICADO que manda.
    #
    # Até a v1.9.41 este valor era RECALCULADO da resposta viva e servia
    # para EXCLUIR o hero da galeria; recalcular era o certo, porque um
    # engano ali só trocava qual quadro ficava de fora de uma galeria de
    # rodapé. Na v1.9.42 o papel inverteu: o hero é PINADO em 1º e vira a
    # abertura da página, e o `backdrop_path` publicado é o que o frontend
    # usa no caminho estático (filme sem faixa) e de onde saem
    # `backdrop_largura`/`backdrop_altura`, que reservam a proporção.
    #
    # MEDIDO nesta rodada: o acervo do TMDB andou desde a publicação das
    # fichas, e em 2 dos 34 longas (`dune-2021`, `parasite-2019`) o hero
    # recalculado é uma imagem COMPLETAMENTE outra (distância de pHash 32).
    # Com o valor recalculado, esses dois abririam a faixa num quadro e
    # cairiam noutro no caminho estático — duas aberturas diferentes para a
    # mesma página, dependendo de um ramo que o leitor não escolhe.
    #
    # Pinar o PUBLICADO fecha isso por construção: o primeiro quadro da
    # faixa é, sempre, a mesma imagem que o hero estático mostraria. O
    # recálculo continua como reserva para ficha sem `backdrop_path`.
    lista_backdrops = (imagens.get("backdrops") or [])[:10]
    escolhido = _melhor(lista_backdrops, preferir_sem_texto=True)
    hero_path = ficha.get("backdrop_path") or (
        escolhido.get("file_path") if escolhido else None)

    # [v1.9.40] pHash das candidatas — FAZ REDE (uma w300 por candidata),
    # com cache em disco: a segunda execução do backfill não rebaixa nada.
    # `sess` é a MESMA sessão do TMDB acima — reaproveitar a conexão, não
    # abrir uma nova (ver `still_hash._SESSAO`, a alternativa que
    # `session=None` cairia nela). Dependências ausentes já são barradas
    # em `main()` (`_exigir_dependencias_dedup`); o que sobrevive aqui é
    # só falha POR IMAGEM (uma request de rede que falhou), que continua
    # degradando aquela candidata específica — ver `_hashes_dos_candidatos`.
    hashes = _hashes_dos_candidatos(detalhes, session=sess)
    galeria = _stills(imagens, hero_path, hashes=hashes)
    n_candidatas = len([
        b for b in (imagens.get("backdrops") or [])
        if b.get("file_path") and b.get("file_path") != hero_path
        and b.get("iso_639_1") is None and _still_16_9(b)])
    n_pos_dedup = len(_deduplicar([
        b for b in (imagens.get("backdrops") or [])
        if b.get("file_path") and b.get("file_path") != hero_path
        and b.get("iso_639_1") is None and _still_16_9(b)], hashes))
    compativel = duracao_compativel_com_longa(duracao_min)
    if not compativel:
        galeria = []

    if not dry_run:
        ficha.pop("galeria_posters", None)  # campo REMOVIDO, v1.9.39 (substituição, não convivência)
        ficha["galeria_stills"] = galeria
        d["ficha"] = ficha
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

        cache_p = _cache_path_para(slug, d)
        if cache_p:
            cached = json.loads(cache_p.read_text(encoding="utf-8"))
            cached.pop("galeria_posters", None)  # campo removido, v1.9.39
            cached["galeria_stills"] = galeria
            cache_p.write_text(json.dumps(cached, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    return {
        "slug": slug, "status": "ok", "tmdb_id": tmdb_id,
        "duracao_min": duracao_min, "duracao_compativel_com_longa": compativel,
        "n_candidatas": n_candidatas, "n_pos_dedup": n_pos_dedup,
        "n_hashes": len(hashes), "n_stills": len(galeria),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    _exigir_dependencias_dedup()
    key = _api_key()
    slugs = args.slug or _catalogo()
    sess = requests.Session()

    resultados = []
    excecoes = []
    for slug in slugs:
        r = processar(slug, key, sess, dry_run=args.dry_run)
        resultados.append(r)
        marca = "✓" if r["status"] == "ok" else "✗"
        if r["status"] == "ok" and not r["duracao_compativel_com_longa"]:
            excecoes.append(r)
            marca = "⚠"
        print(f"  [{marca}] {slug}: {r}")
        time.sleep(0.05)

    print(f"\n{sum(1 for r in resultados if r['status'] == 'ok')}/{len(resultados)} ok")
    oks = [r for r in resultados if r["status"] == "ok" and r.get("n_candidatas")]
    if oks:
        colapsadas = sum(r["n_candidatas"] - r["n_pos_dedup"] for r in oks)
        print(f"\nDEDUP (v1.9.40): {colapsadas} candidatas colapsadas em "
              f"{sum(r['n_candidatas'] for r in oks)} — "
              f"{sum(r['n_pos_dedup'] for r in oks)} distintas sobraram")
    if excecoes:
        print("\nEXCEÇÕES — duração fora do território de longa (galeria vazia; "
              "NÃO é confirmação de identidade, ver duracao_compativel_com_longa):")
        for r in excecoes:
            print(f"  - {r['slug']} (tmdb_id={r['tmdb_id']}, "
                  f"duracao_min={r['duracao_min']})")


if __name__ == "__main__":
    main()
