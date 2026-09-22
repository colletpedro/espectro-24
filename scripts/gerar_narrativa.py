"""[2026-09-22, §D2] Regera a NARRATIVA sobre `resultado/*.json` já publicados.

**Isto NÃO é republicar o filme**, mesmo desenho de `scripts/gerar_veredito.py`
(§3[V]): nenhum estágio a montante roda — sem coleta, sem seleção, sem síntese,
sem [D3]/eixos, sem TMDB, sem histograma. O harness lê o JSON que já está em
disco (o bloco `eixos`, se mudou, já precisa estar lá — `republicar_eixos.py`),
monta o briefing (`espectro24.briefing`, código puro), chama `narrador.narrar`
— a MESMA função que `cli.py` chama em produção — e grava só três chaves:
`narrativa`, `verificacao_narrativa`, `narrativa_selecao`.

**Por que existe, em vez de reusar `cli --reuse-synthesis --tom narrativo`:**
esse caminho também chama `montar_eixos`, que pode rotular (`[D3]`, DeepSeek)
mesmo passando o `eixos` já correto — reclassificar o que já está certo seria
gasto e risco fora do escopo de "só a narrativa". Este harness não tem
`montar_eixos` no caminho.

**Escopo travado por TESTE**, não por disciplina (mesma lição do footgun que
`gerar_veredito.py` fechou): `tests/test_gerar_narrativa.py` substitui os
pontos de entrada de coleta, seleção, síntese, [D3] e eixos por
`pytest.fail`, prova que nenhuma chamada de rede sai daqui fora do adaptador
de LLM, e compara o JSON campo a campo antes/depois.

Uso:
    python scripts/gerar_narrativa.py --slug the-godfather
    python scripts/gerar_narrativa.py --todos
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402

from espectro24.narrador import narrar, telemetria_para_json  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"

# As ÚNICAS três chaves que este harness escreve — literal, e conferida
# contra o documento antes de gravar (mesmo contrato de `gerar_veredito.py`).
CHAVES = ("narrativa", "verificacao_narrativa", "narrativa_selecao")


def slugs_publicados() -> list[str]:
    """Todo `resultado/<slug>.json` que já tem narrativa — a população sobre
    a qual regenerar faz sentido (filme sem narrativa nunca foi publicado por
    este caminho; não é este harness que o publica pela primeira vez)."""
    saida = []
    for caminho in sorted(RESULTADO_DIR.glob("*.json")):
        try:
            d = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if d.get("narrativa"):
            saida.append(caminho.stem)
    return saida


def _campos_fora_das_chaves(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in CHAVES}


def gerar_um(slug: str, *, modelo: str | None = None,
            provider: str | None = None, saida: Path | None = None,
            n: int | None = None) -> dict:
    """Regera a narrativa de UM filme e grava. Devolve a telemetria.

    `saida` grava noutro diretório (sandbox de teste / A/B); sem ela, grava
    em `resultado/`, sobrescrevendo o filme."""
    origem = RESULTADO_DIR / f"{slug}.json"
    documento = json.loads(origem.read_text(encoding="utf-8"))
    antes = _campos_fora_das_chaves(documento)

    t0 = time.time()
    kw = {} if n is None else {"n": n}
    res = narrar(documento, provider=provider, model=modelo, **kw)

    documento["narrativa"] = res.texto
    documento["verificacao_narrativa"] = res.verificacao
    documento["narrativa_selecao"] = telemetria_para_json(res)

    # A guarda que o teste de campo a campo trava, aqui também em produção:
    # nada além das três chaves pode ter mudado.
    depois = _campos_fora_das_chaves(documento)
    if depois != antes:
        divergentes = sorted(k for k in set(antes) | set(depois)
                             if antes.get(k) != depois.get(k))
        raise SystemExit(
            f"ABORTADO em {slug}: o estágio de narrativa alterou campos fora "
            f"de {CHAVES}: {divergentes}. Nada foi gravado.")

    if res.falhou:
        return {"slug": slug, "ok": False, "motivo": "nenhuma_amostra_com_texto",
                "n_chamadas": res.n_chamadas, "uso": res.uso}

    destino_dir = Path(saida) if saida else RESULTADO_DIR
    destino_dir.mkdir(parents=True, exist_ok=True)
    (destino_dir / f"{slug}.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")

    v = res.verificacao
    return {"slug": slug, "ok": True, "modelo": res.modelo,
            "provider": res.provider, "n_chamadas": res.n_chamadas,
            "uso": res.uso, "latencia_s": res.latencia_s,
            "escolha": res.escolha.get("motivo") if res.escolha else None,
            "criterio_decisivo": (res.escolha.get("criterio_decisivo")
                                  if res.escolha else None),
            "n_flags": v.get("n_flags") if v else None,
            "retry_aplicado": (res.retry or {}).get("aplicado"),
            "n_palavras": len(res.texto.split()),
            "texto": res.texto, "elapsed_s": round(time.time() - t0, 1)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--slug", action="append", help="slug (repetível)")
    ap.add_argument("--todos", action="store_true",
                    help="todos os filmes com narrativa publicada")
    ap.add_argument("--modelo", help="override do modelo (default: "
                                     "MODELO_POR_ESTAGIO['narrativa'])")
    ap.add_argument("--provider", help="override do provider")
    ap.add_argument("--saida", help="diretório alternativo (não publica)")
    ap.add_argument("--log", help="jsonl com a telemetria de cada filme")
    ap.add_argument("--best-of", type=int,
                    help="override de BEST_OF_N — existe para MEDIR o efeito "
                         "de N, não para uso corrente")
    args = ap.parse_args()

    load_dotenv(RAIZ / ".env")
    slugs = args.slug or (slugs_publicados() if args.todos else [])
    if not slugs:
        raise SystemExit("nada a fazer: use --slug X ou --todos.")

    log = Path(args.log) if args.log else None
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)

    for slug in slugs:
        r = gerar_um(slug, modelo=args.modelo, provider=args.provider,
                    saida=Path(args.saida) if args.saida else None,
                    n=args.best_of)
        if log:
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if not r["ok"]:
            print(f"  [·] {slug}: {r['motivo']}")
            continue
        print(f"  [✓] {slug}: {r['n_chamadas']} chamada(s) · "
              f"{r['n_palavras']} palavras · {r['n_flags']} flags · "
              f"escolha={r['escolha']}/{r['criterio_decisivo']}"
              + (" · retry aplicado" if r["retry_aplicado"] else ""))


if __name__ == "__main__":
    main()
