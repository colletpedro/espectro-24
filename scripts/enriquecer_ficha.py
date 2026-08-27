#!/usr/bin/env python3
"""[v1.9.29, §3[F]] Retrofit dos campos de IMAGEM e RASTREABILIDADE na ficha
de `resultado/*.json` já publicados.

**Isto NÃO é republicar o filme.** Nenhum estágio a montante roda: sem
coleta, sem seleção, sem classificação, sem verificação, sem síntese, sem
[D3], sem narrativa, sem veredito, sem histograma. O harness lê o JSON que
já está em disco, faz **uma** consulta ao TMDB (a mesma chamada única de
`ficha.buscar_ficha`) e grava **apenas as chaves novas dentro do bloco
`ficha`**:

    tmdb_id · tmdb_fetched_at · poster_path · poster_largura ·
    poster_altura · backdrop_paths

**Por que harness PRÓPRIO, e não `publicar_catalogo.py`.** Mesmo argumento
da v1.9.21 e da v1.9.25: aquele script tem o checkpoint por `spec_version` e
a guarda de lote (`LIMITE_LOTE_SEM_CONFIRMACAO = 5`), e as duas existem
porque republicar faz REDE PESADA — raspagem do superset do Letterboxd,
horas — e sobrescreve o histórico `passadas` do bruto. Este harness faz uma
requisição de API por filme e não toca em bruto nenhum, então herdar a
guarda seria cerimônia sem risco. **Ele não passa pela guarda de lote e não
deve passar** — e, o que importa mais, não dispara republicação por nenhum
caminho: não importa `publicar_catalogo`, não invoca `espectro24.cli`, não
abre subprocesso.

A contrapartida é a mesma lição de sempre: *harness novo com "cuidado
diferente" é exatamente como se abre o próximo footgun*. Por isso o escopo
deste arquivo é travado por TESTE, não por disciplina —
`tests/test_enriquecer_ficha.py`:

  - substitui os pontos de entrada de coleta, seleção, síntese, [D3],
    narrativa, veredito e publicação por `pytest.fail` e roda o harness;
  - compara o documento campo a campo antes/depois e exige que **só** as
    chaves de `CHAVES_NOVAS`, **dentro de `ficha`**, tenham mudado — todo o
    resto byte-idêntico.

**Guarda de identidade.** Reconsultar o TMDB é reabrir a desambiguação que
o pipeline já fez uma vez. Se a resposta de agora descrever um filme
DIFERENTE do que está no disco (título, ano ou diretor divergentes), o filme
é abortado sem gravar — melhor ficar sem pôster do que colar o pôster de
outro filme numa página publicada. Mesmo princípio da guarda de ano
divergente da v1.7.0.

**Aditivo, como toda a ficha desde a v1.3.0.** Filme sem bloco `ficha`
(`null`) é PULADO, não é erro. Falha de rede, HTTP, chave ausente ou filme
sem pôster também não são erro: o filme fica sem os campos novos e o
relatório diz quais.

Uso:
    python scripts/enriquecer_ficha.py --slug the-godfather
    python scripts/enriquecer_ficha.py --todos
    python scripts/enriquecer_ficha.py --todos --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24.ficha import buscar_ficha, titulo_ano_de_slug  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"

# As ÚNICAS chaves que este harness escreve, e só dentro de `ficha`.
# Literais, e conferidas contra o documento antes de gravar: se o estágio um
# dia passar a mexer noutra coisa, a guarda de campo a campo quebra, e este
# nome é onde o leitor descobre qual era o contrato.
CHAVES_NOVAS = (
    "tmdb_id", "tmdb_fetched_at",
    "poster_path", "poster_largura", "poster_altura", "backdrop_paths",
)

# Campos que precisam BATER entre a ficha em disco e a resposta de agora
# para que a resposta seja aceita como sendo do mesmo filme.
CHAVES_IDENTIDADE = ("titulo", "ano", "diretor")


def slugs_com_ficha() -> list[str]:
    """Todo `resultado/<slug>.json` com bloco `ficha` não-nulo."""
    saida = []
    for caminho in sorted(RESULTADO_DIR.glob("*.json")):
        try:
            d = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if d.get("ficha"):
            saida.append(caminho.stem)
    return saida


def _sem_chaves_novas(ficha: dict) -> dict:
    return {k: v for k, v in ficha.items() if k not in CHAVES_NOVAS}


def _identidade_bate(antiga: dict, nova: dict) -> list[str]:
    """Campos de identidade que DIVERGEM entre a ficha em disco e a nova.

    Um campo ausente de um dos lados não conta como divergência — a ficha
    antiga pode não ter diretor, e isso não é sinal de filme trocado.
    """
    return [
        k for k in CHAVES_IDENTIDADE
        if antiga.get(k) and nova.get(k) and antiga[k] != nova[k]
    ]


def enriquecer_um(slug: str, *, cache_dir: Path, dry_run: bool = False,
                  saida: Path | None = None) -> dict:
    """Busca as imagens de UM filme e grava as chaves novas. Telemetria."""
    origem = RESULTADO_DIR / f"{slug}.json"
    documento = json.loads(origem.read_text(encoding="utf-8"))

    ficha_antiga = documento.get("ficha")
    if not ficha_antiga:
        return {"slug": slug, "ok": False, "motivo": "sem_ficha"}

    # A MESMA resolução que o pipeline fez, e nesta ordem por um motivo
    # MEDIDO: o título de busca vem do SLUG (`titulo_ano_de_slug`), não do
    # `ficha.titulo`. O `ficha.titulo` é o título pt-BR que o TMDB devolveu —
    # usá-lo como query reabre a busca com um termo diferente do original e
    # resolve outro filme. Observado em `mother-2017`: o disco tem
    # `titulo="mãe!"`, e buscar "mãe!" + 2017 devolve "Perfeita é a Mãe 2"
    # (dir. Scott Moore). A guarda de identidade pegou; a causa era esta.
    #
    # O ANO, ao contrário, vem da ficha em disco: é o ano já VALIDADO na
    # publicação (a guarda da v1.7.0 passou por ele), mais confiável que o
    # sufixo do slug — e, para os 21 slugs sem ano no nome, é o único ano
    # disponível sem ir à rede do Letterboxd.
    titulo_slug, ano_slug = titulo_ano_de_slug(slug)
    titulo = titulo_slug or ficha_antiga.get("titulo")
    ano = ficha_antiga.get("ano") or ano_slug

    nova, aviso, _descartada = buscar_ficha(titulo, ano, cache_dir=cache_dir)
    if not nova:
        return {"slug": slug, "ok": False, "motivo": aviso or "sem_resultado"}

    divergentes = _identidade_bate(ficha_antiga, nova)
    if divergentes:
        return {"slug": slug, "ok": False,
                "motivo": f"identidade_divergente: {divergentes} "
                          f"(disco={[ficha_antiga.get(k) for k in divergentes]}, "
                          f"tmdb={[nova.get(k) for k in divergentes]})"}

    antes_ficha = dict(ficha_antiga)
    antes_resto = {k: v for k, v in documento.items() if k != "ficha"}

    ficha_nova = dict(ficha_antiga)
    for chave in CHAVES_NOVAS:
        ficha_nova[chave] = nova.get(chave)
    documento["ficha"] = ficha_nova

    # A guarda que o teste trava, aqui também em produção: nada fora das
    # chaves novas, e nada fora de `ficha`, pode ter mudado.
    depois_resto = {k: v for k, v in documento.items() if k != "ficha"}
    if depois_resto != antes_resto:
        mudou = sorted(k for k in set(antes_resto) | set(depois_resto)
                       if antes_resto.get(k) != depois_resto.get(k))
        raise SystemExit(f"ABORTADO em {slug}: campos fora de `ficha` "
                         f"mudaram: {mudou}. Nada foi gravado.")
    if _sem_chaves_novas(ficha_nova) != _sem_chaves_novas(antes_ficha):
        mudou = sorted(k for k in set(antes_ficha) | set(ficha_nova)
                       if k not in CHAVES_NOVAS
                       and antes_ficha.get(k) != ficha_nova.get(k))
        raise SystemExit(f"ABORTADO em {slug}: campos da ficha fora de "
                         f"CHAVES_NOVAS mudaram: {mudou}. Nada foi gravado.")

    tem_poster = bool(ficha_nova.get("poster_path"))
    if not dry_run:
        destino_dir = Path(saida) if saida else RESULTADO_DIR
        destino_dir.mkdir(parents=True, exist_ok=True)
        (destino_dir / f"{slug}.json").write_text(
            json.dumps(documento, ensure_ascii=False, indent=2),
            encoding="utf-8")

    return {"slug": slug, "ok": True, "poster": tem_poster,
            "poster_path": ficha_nova.get("poster_path"),
            "dimensoes": (ficha_nova.get("poster_largura"),
                          ficha_nova.get("poster_altura")),
            "n_backdrops": len(ficha_nova.get("backdrop_paths") or []),
            "tmdb_id": ficha_nova.get("tmdb_id")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", action="append", help="slug (repetível)")
    ap.add_argument("--todos", action="store_true",
                    help="todos os filmes com bloco `ficha`")
    ap.add_argument("--dry-run", action="store_true",
                    help="consulta e reporta, sem gravar nada")
    ap.add_argument("--saida", help="diretório alternativo (inspeção)")
    ap.add_argument("--cache-dir", default=str(RAIZ / "dados" / "cache" / "_tmdb"),
                    help="cache do TMDB (mesmo formato de ficha.buscar_ficha)")
    args = ap.parse_args()

    load_dotenv(RAIZ / ".env")
    slugs = args.slug or (slugs_com_ficha() if args.todos else [])
    if not slugs:
        raise SystemExit("nada a fazer: use --slug X ou --todos.")

    cache_dir = Path(args.cache_dir)
    com = []
    sem = []
    falhas = []
    for slug in slugs:
        r = enriquecer_um(slug, cache_dir=cache_dir, dry_run=args.dry_run,
                          saida=Path(args.saida) if args.saida else None)
        if not r["ok"]:
            falhas.append((slug, r["motivo"]))
            print(f"  [!] {slug}: {r['motivo']}")
            continue
        if r["poster"]:
            com.append(slug)
            l, a = r["dimensoes"]
            print(f"  [✓] {slug}: id={r['tmdb_id']} {l}x{a} "
                  f"backdrops={r['n_backdrops']} {r['poster_path']}")
        else:
            sem.append(slug)
            print(f"  [·] {slug}: id={r['tmdb_id']} SEM PÔSTER "
                  f"backdrops={r['n_backdrops']}")

    print(f"\n{len(com)} com pôster · {len(sem)} sem pôster · "
          f"{len(falhas)} sem ficha/falha"
          + ("  (DRY RUN — nada gravado)" if args.dry_run else ""))
    if sem:
        print("  sem pôster: " + ", ".join(sem))
    if falhas:
        print("  falhas: " + ", ".join(s for s, _ in falhas))


if __name__ == "__main__":
    main()
