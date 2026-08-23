"""[v1.9.16, Entrega 4] Publica os filmes do catálogo (35, `consenso.jsonl`)
que ainda não têm `resultado/*.json` sob o pipeline CORRENTE — síntese,
narrativa (best-of-3) e o bloco `eixos` sob a classificação VERIFICADA
(default de `pipeline._carregar_consenso_producao` desde a Entrega 1).

Cada filme roda como SUBPROCESSO de `espectro24.cli` (`--tom ambos`, para
gravar tanto os temas estruturados quanto a prosa) — isolamento: um filme
que trave ou estoure não derruba o lote, mesmo padrão de falha isolada do
harness de coleta (`espectro24.lote`, §3[H]).

**Checkpoint é o próprio filesystem, não um arquivo de estado à parte:** um
filme conta como feito quando `resultado/{slug}.json` existe, tem
`spec_version` igual ao corrente, E `eixos.verificador.aplicado` — os dois
juntos, porque um JSON de versão antiga (`oppenheimer-2023`, `1.1.1`) não
pode ser confundido com "já publicado sob o pipeline de hoje" só por
existir. Resume = pular quem já atende os dois critérios.

Telemetria por filme (flags mecânicas, contraste, piso, custo, latência) vai
para `resultado/v1916/publicacao_log.jsonl`, um registro por tentativa
(sucesso ou falha) — append-only, então reprocessar não perde histórico.

Uso:
    python scripts/publicar_catalogo.py                  # os pendentes (default: os 32)
    python scripts/publicar_catalogo.py --slug X --slug Y
    python scripts/publicar_catalogo.py --relatorio       # só agrega o que já rodou
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.config import SPEC_VERSION  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
CONSENSO = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"
LOG_DIR = RAIZ / "resultado" / "v1916"
LOG = LOG_DIR / "publicacao_log.jsonl"
JA_PUBLICADOS_ANTES = {"cure", "cidade-de-deus", "the-invite-2026"}
TIMEOUT_S = 300


def catalogo_completo() -> list[str]:
    """Os 35 slugs de `consenso.jsonl`, ordenados — a fonte única do
    catálogo (não uma lista redigitada que pode divergir dele)."""
    slugs = set()
    for linha in CONSENSO.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            slugs.add(json.loads(linha)["slug"])
    return sorted(slugs)


def filmes_pendentes() -> list[str]:
    return [s for s in catalogo_completo() if s not in JA_PUBLICADOS_ANTES]


def _ja_publicado(slug: str) -> bool:
    p = RESULTADO_DIR / f"{slug}.json"
    if not p.exists():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False
    if d.get("spec_version") != SPEC_VERSION:
        return False
    verificador = (d.get("eixos") or {}).get("verificador") or {}
    return verificador.get("aplicado") is True


def publicar_um(slug: str) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, "-m", "espectro24.cli", "--slug", slug,
             "--tom", "ambos"],
            cwd=RAIZ, capture_output=True, text=True, timeout=TIMEOUT_S)
        rc, stdout, stderr, expirou = r.returncode, r.stdout, r.stderr, False
    except subprocess.TimeoutExpired as e:
        rc = None
        stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        expirou = True
    dt = time.time() - t0
    ok = rc == 0 and _ja_publicado(slug)
    return {"slug": slug, "ok": ok, "elapsed_s": round(dt, 1),
            "returncode": rc, "expirou": expirou,
            "stdout_tail": stdout[-3000:], "stderr_tail": stderr[-6000:]}


def cmd_publicar(slugs: list[str]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pulados = feitos = falhas = 0
    for slug in slugs:
        if _ja_publicado(slug):
            print(f"  [·] {slug}: já publicado sob {SPEC_VERSION}, pulado")
            pulados += 1
            continue
        print(f"  [ ] {slug}: publicando...", flush=True)
        res = publicar_um(slug)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
        if res["ok"]:
            print(f"  [✓] {slug}: {res['elapsed_s']}s")
            feitos += 1
        else:
            motivo = "TIMEOUT" if res["expirou"] else f"rc={res['returncode']}"
            print(f"  [✗] {slug}: FALHOU ({motivo}, {res['elapsed_s']}s)")
            print(f"      stderr: {res['stderr_tail'][-800:]}")
            falhas += 1
    print(f"\n{feitos} publicados · {pulados} pulados (já em dia) · "
          f"{falhas} falharam")
    print(f"→ {LOG.relative_to(RAIZ)}")


def cmd_relatorio() -> None:
    """Agrega os JSONs publicados: contraste, piso, flags, tokens/latência
    (do log de tentativas). Não chama LLM nenhum — só lê o que está no
    disco."""
    slugs = catalogo_completo()
    linhas_log = {}
    if LOG.exists():
        for l in LOG.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                linhas_log[r["slug"]] = r  # última tentativa prevalece

    print(f"{'slug':<38} {'contraste':<11} {'piso (n/m/p)':<20} "
          f"{'flags':<6} {'s'}")
    n_tematico = n_valorativo = n_com_flag = 0
    for slug in slugs:
        p = RESULTADO_DIR / f"{slug}.json"
        if not p.exists():
            print(f"{slug:<38} — não publicado —")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        e = d.get("eixos") or {}
        contraste = e.get("contraste", "?")
        n_tematico += contraste == "tematico"
        n_valorativo += contraste == "valorativo"
        piso = "/".join((b.get("estado_piso") or "?")[:4] for b in d.get("buckets", []))
        flags = (d.get("verificacao_narrativa") or {}).get("n_flags")
        n_com_flag += bool(flags)
        dt = linhas_log.get(slug, {}).get("elapsed_s", "?")
        print(f"{slug:<38} {contraste:<11} {piso:<20} "
              f"{str(flags):<6} {dt}")
    print(f"\ncontraste: {n_tematico} tematico / {n_valorativo} valorativo "
          f"de {n_tematico + n_valorativo}")
    print(f"filmes com alguma flag mecânica: {n_com_flag}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", action="append",
                    help="slug a publicar (repetível); default: os pendentes")
    ap.add_argument("--relatorio", action="store_true",
                    help="só agrega o que já está publicado, sem rodar nada")
    args = ap.parse_args()
    if args.relatorio:
        cmd_relatorio()
        return
    cmd_publicar(args.slug or filmes_pendentes())


if __name__ == "__main__":
    main()
