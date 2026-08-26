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
from espectro24.synthesize import parse_linha_telemetria_llm  # noqa: E402

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


# [v1.9.21] TETO DE LOTE — a guarda que fecha o footgun que a v1.9.21 abriu.
#
# `cmd_publicar` pula quem `_ja_publicado`, e `_ja_publicado` exige
# `spec_version == SPEC_VERSION`. Enquanto a constante ficou em `1.9.16`, os
# 32 slugs default eram todos pulados e rodar este script sem argumento era
# inócuo. Com `SPEC_VERSION` em `1.9.21` e os 35 JSONs em `1.9.16`, NENHUM é
# pulado: um comando de uma linha dispara re-scrape de 32 filmes a 2s por
# requisição sem paralelismo, e apaga o histórico `passadas` do `meta.json`
# (dívida conhecida, `DIAGNOSTICO_OFFLINE.md`). Caro, demorado e irreversível
# para o histórico.
#
# 5 é DECISÃO DE PRODUTO, não número mágico: acima de um punhado, o comando
# deixa de ser "conserta um caso" e vira "republica o catálogo", e a diferença
# entre os dois é de horas de rede.
#
# ESCOPO ESTRITO: isto não muda o checkpoint (`_ja_publicado`), não muda a
# lista default e não toca a dívida do `passadas`.
LIMITE_LOTE_SEM_CONFIRMACAO = 5


def checar_tamanho_do_lote(slugs: list[str], republicar_tudo: bool) -> None:
    """Recusa um lote grande sem confirmação explícita.

    Conta quem SERIA republicado, não o tamanho da lista: passar os 35 slugs
    com 32 já em dia é um lote de 3, e passa.
    """
    if republicar_tudo:
        return
    alvos = [s for s in slugs if not _ja_publicado(s)]
    if len(alvos) <= LIMITE_LOTE_SEM_CONFIRMACAO:
        return
    raise SystemExit(
        f"RECUSADO: isto republicaria {len(alvos)} filmes (teto sem "
        f"confirmação: {LIMITE_LOTE_SEM_CONFIRMACAO}).\n"
        f"Motivo: nenhum deles tem `spec_version` igual a {SPEC_VERSION}, "
        f"então o checkpoint os trata como pendentes.\n"
        f"Cada um refaz coleta de rede (~2s por requisição, sem paralelismo) "
        f"e sobrescreve o histórico `passadas` do meta.json do bruto.\n"
        f"Se é isso mesmo que você quer, repita com --republicar-tudo.\n"
        f"Para regerar SÓ o veredito (§3[V]), sem tocar em rede nem em "
        f"nenhum estágio a montante, use scripts/gerar_veredito.py.")


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
    # [v1.9.25, §3[D]] A telemetria de retentativa do LLM vive no processo
    # FILHO e morre com ele; o stderr é o único canal que atravessa. Extraída
    # aqui para virar campo próprio no log — sem isso ficaria só embutida no
    # `stderr_tail`, legível por grep e invisível no relatório.
    return {"slug": slug, "ok": ok, "elapsed_s": round(dt, 1),
            "returncode": rc, "expirou": expirou,
            "retentativa_llm": parse_linha_telemetria_llm(stderr),
            "stdout_tail": stdout[-3000:], "stderr_tail": stderr[-6000:]}


def cmd_publicar(slugs: list[str], republicar_tudo: bool = False) -> None:
    checar_tamanho_do_lote(slugs, republicar_tudo)
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
    _linha_retentativa_llm(linhas_log)


def _linha_retentativa_llm(linhas_log: dict) -> None:
    """[v1.9.25, §3[D]] Retentativa de transporte do LLM, agregada no LOTE.

    É o lugar certo para ela: por filme seria ruído (a esmagadora maioria é
    zero), e num lote de ~300 uma taxa alta é o sinal de degradação do
    provider que, sem isto, só apareceria como lentidão inexplicada.

    Filmes SEM a linha (publicados antes da v1.9.25, ou execução que morreu
    antes do fim) contam à parte, como `sem telemetria` — "não sei" não é a
    mesma coisa que "foram zero", e somá-los como zero maquiaria a taxa.
    """
    com, sem, total, por_tipo = 0, 0, 0, {}
    for r in linhas_log.values():
        tel = r.get("retentativa_llm")
        if tel is None:
            sem += 1
            continue
        com += 1
        total += tel.get("n_retentativas", 0)
        for k, v in (tel.get("por_tipo") or {}).items():
            por_tipo[k] = por_tipo.get(k, 0) + v
    if not com and not sem:
        return
    detalhe = f" · {por_tipo}" if por_tipo else ""
    print(f"retentativas de transporte do LLM: {total} em {com} execução(ões)"
          f"{detalhe}" + (f" · {sem} sem telemetria" if sem else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", action="append",
                    help="slug a publicar (repetível); default: os pendentes")
    ap.add_argument("--relatorio", action="store_true",
                    help="só agrega o que já está publicado, sem rodar nada")
    ap.add_argument("--republicar-tudo", action="store_true",
                    help=f"autoriza um lote acima de "
                         f"{LIMITE_LOTE_SEM_CONFIRMACAO} filmes (re-scrape "
                         f"completo; ver checar_tamanho_do_lote)")
    args = ap.parse_args()
    if args.relatorio:
        cmd_relatorio()
        return
    cmd_publicar(args.slug or filmes_pendentes(),
                 republicar_tudo=args.republicar_tudo)


if __name__ == "__main__":
    main()
