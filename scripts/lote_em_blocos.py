"""Classificação + verificador POR BLOCOS de filmes (2026-09-18).

O desenho anterior — `estender_classificacao_producao.py` sobre TODOS os slugs —
rodava o passe 1 em todos os filmes, depois o 2, depois o 3, e só então o
consenso. No lote noturno de 18/09 o saldo zerou no passe 3 e 2,4 passes pagos
(~US$1,75) ficaram presos em `passe_*.jsonl`, fora da produção. A votação não
exigia isso: `votacao_3._consensuar` é função pura dos três votos de UMA review.

Aqui cada BLOCO (~10 filmes) roda, nesta ordem:

    1. registro na amostra (idempotente, sem chamada)
    2. passes 1, 2 e 3 só das reviews do bloco            [paga]
    3. consenso do bloco, EM MEMÓRIA                      [grátis]
    4. verificador `aplicar-producao` só do bloco         [paga]
    5. COMMIT: consenso_verificado → consenso → manifesto (cada um atômico)

O commit só acontece se 2 e 4 terminaram. Interrupção em qualquer ponto
anterior deixa `consenso.jsonl`, `consenso_verificado.jsonl` e
`verificador_manifesto.json` byte a byte como estavam — e o que foi pago fica
em `passe_*.jsonl`/`verificador_producao.jsonl` (append-only), então o resume
não paga de novo. Perde-se no máximo o bloco em curso, e mesmo ele só até o
commit.

Por que os três arquivos andam juntos: `pipeline._carregar_consenso_producao`
compara `fonte_n_linhas` do manifesto com as linhas de `consenso.jsonl` e LEVANTA
se divergirem — um consenso à frente do manifesto quebra `montar_eixos` para os
filmes já publicados. NUNCA rode `votacao_3.py consenso` isolado sobre um
estado com passes adiante do consenso.

A única janela não coberta por atomicidade é a queda ENTRE os dois últimos
`os.replace` do commit (microssegundos). `estado_consistente()` a detecta na
partida do driver, e `--reparar` a fecha sem gastar chamada.

Uso:
    python scripts/lote_em_blocos.py LISTA.txt [--tamanho-bloco 10] [--dry-run]
    python scripts/lote_em_blocos.py --reparar
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import estender_classificacao_producao as est  # noqa: E402
import verificador_impacto as vi  # noqa: E402
import votacao_3 as v3  # noqa: E402
from espectro24 import synthesize as S  # noqa: E402
from espectro24.atomico import escrever_atomico  # noqa: E402
from espectro24.preco import (  # noqa: E402
    agora_utc_iso,
    aviso_de_validade,
    custo_de_registros,
)

TAMANHO_BLOCO = 10


def dividir_em_blocos(slugs: list[str], tamanho: int) -> list[list[str]]:
    if tamanho < 1:
        raise ValueError("tamanho do bloco precisa ser >= 1")
    vistos, unicos = set(), []
    for s in slugs:
        if s not in vistos:
            vistos.add(s)
            unicos.append(s)
    return [unicos[i:i + tamanho] for i in range(0, len(unicos), tamanho)]


def _linhas_jsonl(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8")
            .splitlines() if l.strip()]


def estado_consistente() -> list[str]:
    """Problemas entre `consenso.jsonl`, `consenso_verificado.jsonl` e o
    manifesto do verificador. Lista vazia = consistente. Sem verificado ou sem
    manifesto não há nada a cruzar (é o guard de `pipeline.py`)."""
    if not (vi.ARQ_CONSENSO_VERIFICADO.exists()
            and vi.ARQ_MANIFESTO_VERIFICADOR.exists()):
        return []
    problemas = []
    consenso = _linhas_jsonl(v3.ARQ_CONSENSO)
    verificado = _linhas_jsonl(vi.ARQ_CONSENSO_VERIFICADO)
    manifesto = json.loads(
        vi.ARQ_MANIFESTO_VERIFICADOR.read_text(encoding="utf-8"))
    if manifesto.get("fonte_n_linhas") != len(consenso):
        problemas.append(
            f"manifesto registra {manifesto.get('fonte_n_linhas')} linhas de "
            f"consenso; o consenso tem {len(consenso)} — `montar_eixos` "
            f"levantaria ValueError para TODO filme")
    if len(verificado) != len(consenso):
        problemas.append(
            f"consenso_verificado tem {len(verificado)} linhas; o consenso "
            f"tem {len(consenso)}")
    elif ([(l["slug"], l["bucket"], l["id"]) for l in verificado]
          != [(l["slug"], l["bucket"], l["id"]) for l in consenso]):
        problemas.append("consenso_verificado e consenso têm as mesmas "
                         "quantidades, mas não as mesmas reviews")
    return problemas


def registrar_bloco(bloco: list[str]) -> tuple[int, list[str]]:
    """Registra o bloco em `amostra.json` (idempotente, sem chamada paga)."""
    faltantes = est._faltantes_por_slug(bloco)
    n_novas, filmes_novos = est._acrescentar_a_amostra(faltantes)
    v3.checar_filmes_registrados(
        json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8")), [])
    return n_novas, filmes_novos


def gravar_bloco(linhas_consenso: list[dict], saida: list[dict],
                 manifesto: dict) -> None:
    """O COMMIT. Cada arquivo é atômico; a ordem deixa `montar_eixos` lendo
    arquivo inteiro em todos os instantes exceto entre os dois últimos
    `os.replace` (ver o docstring do módulo)."""
    escrever_atomico(vi.ARQ_CONSENSO_VERIFICADO, v3.serializar_linhas(saida))
    escrever_atomico(v3.ARQ_CONSENSO, v3.serializar_linhas(linhas_consenso))
    escrever_atomico(vi.ARQ_MANIFESTO_VERIFICADOR,
                     json.dumps(manifesto, ensure_ascii=False, indent=2))


def custo_do_bloco(desde_iso: str, bloco: list[str]) -> dict:
    """Custo REAL das chamadas gravadas desde `desde_iso` para o bloco, cada
    uma no preço do seu instante (`ts`)."""
    alvo, regs_passes, regs_ver = set(bloco), [], []
    for n in (1, 2, 3):
        for r in _linhas_jsonl(v3.ARQ_PASSE[n]):
            if r.get("slug") in alvo and (r.get("ts") or "") >= desde_iso:
                regs_passes.append(r)
    por_id_slug = {r["id"]: r["slug"] for r in
                   json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))["reviews"]
                   if r["slug"] in alvo}
    for r in _linhas_jsonl(vi.ARQ_PRODUCAO):
        if r.get("id") in por_id_slug and (r.get("ts") or "") >= desde_iso:
            regs_ver.append(r)
    cp, cv = custo_de_registros(regs_passes), custo_de_registros(regs_ver)
    return {"passes": cp.custo_usd, "verificador": cv.custo_usd,
            "total": cp.custo_usd + cv.custo_usd,
            "n_chamadas": cp.n_chamadas + cv.n_chamadas,
            "pico": cp.custo_pico_usd + cv.custo_pico_usd,
            "fora_de_pico": (cp.custo_fora_de_pico_usd
                             + cv.custo_fora_de_pico_usd)}


def processar_bloco(bloco: list[str]) -> dict:
    """Um bloco de ponta a ponta. Levanta `SystemExit` (saldo) ANTES do commit
    se o dinheiro acabar; nesse caso nenhum dos três arquivos foi tocado."""
    desde = agora_utc_iso()
    n_novas, filmes_novos = registrar_bloco(bloco)
    for n in (1, 2, 3):
        v3.classificar_passe(n, slugs=bloco)

    passes = [v3._ler_passe(n) for n in (1, 2, 3)]
    amostra = json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))
    v3.checar_filmes_registrados(amostra, passes)
    atuais = _linhas_jsonl(v3.ARQ_CONSENSO)
    linhas, n_incompletas = v3.consenso_incremental(atuais, passes, amostra,
                                                    bloco)

    saida, manifesto = vi.calcular_aplicacao(linhas, slugs=bloco)
    gravar_bloco(linhas, saida, manifesto)
    return {"bloco": bloco, "reviews_no_consenso":
            sum(1 for l in linhas if l["slug"] in set(bloco)),
            "incompletas": n_incompletas, "removidas": manifesto["n_removidas"],
            "pendentes_verificador": manifesto["n_falharam"],
            "custo": custo_do_bloco(desde, bloco),
            "linhas_consenso": len(linhas)}


def reparar() -> int:
    """Regrava verificado + consenso + manifesto a partir do consenso ATUAL,
    sem nenhuma chamada (`slugs=[]`). Fecha a janela do commit."""
    linhas = _linhas_jsonl(v3.ARQ_CONSENSO)
    saida, manifesto = vi.calcular_aplicacao(linhas, slugs=[])
    gravar_bloco(linhas, saida, manifesto)
    problemas = estado_consistente()
    print("reparo:", "consistente" if not problemas else problemas)
    return 0 if not problemas else 2


def _saldo() -> dict | None:
    return S.saldo_deepseek()


def _fmt_saldo(s: dict | None) -> str:
    if not s:
        return "indisponível (a sonda falhou; seguindo)"
    infos = s.get("balance_infos") or [{}]
    return (f"US${infos[0].get('total_balance', '?')} "
            f"(is_available={s.get('is_available')})")


def dry_run(blocos: list[list[str]]) -> int:
    total = Counter()
    for i, bloco in enumerate(blocos, 1):
        por_passe = {n: len(v3.pendentes_do_passe(n, bloco)[2])
                     for n in (1, 2, 3)}
        total.update(por_passe)
        print(f"bloco {i}/{len(blocos)} ({len(bloco)} filmes): chamadas "
              f"pendentes p1={por_passe[1]} p2={por_passe[2]} "
              f"p3={por_passe[3]} · {bloco[0]} … {bloco[-1]}")
    print(f"TOTAL de chamadas de classificação pendentes: "
          f"{sum(total.values())} (mais o verificador, ~70% das reviews "
          f"com impacto_emocional)")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("lista", nargs="?", help="arquivo de slugs, um por linha")
    p.add_argument("--tamanho-bloco", type=int, default=TAMANHO_BLOCO)
    p.add_argument("--dry-run", action="store_true",
                   help="só conta as chamadas pendentes por bloco")
    p.add_argument("--reparar", action="store_true",
                   help="regrava os três arquivos a partir do consenso "
                        "atual, sem chamada")
    args = p.parse_args(argv)

    if args.reparar:
        return reparar()
    if not args.lista:
        p.error("informe a LISTA de slugs (ou --reparar)")

    from espectro24.lote import ler_lista_slugs
    blocos = dividir_em_blocos(ler_lista_slugs(args.lista),
                               args.tamanho_bloco)
    aviso = aviso_de_validade()
    if aviso:
        print(aviso)

    problemas = estado_consistente()
    if problemas:
        print("ESTADO INCONSISTENTE antes de começar — nada foi rodado:")
        for x in problemas:
            print("  -", x)
        print("Corrija com `python scripts/lote_em_blocos.py --reparar` "
              "(sem chamada).")
        return 2

    if args.dry_run:
        return dry_run(blocos)

    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    t0, custo_total, feitos = time.time(), 0.0, 0
    for i, bloco in enumerate(blocos, 1):
        saldo = _saldo()
        print(f"\n=== bloco {i}/{len(blocos)} · {len(bloco)} filmes · saldo "
              f"antes: {_fmt_saldo(saldo)}", flush=True)
        if saldo is not None and saldo.get("is_available") is False:
            print("PARADO antes do bloco: a conta não tem crédito. Blocos "
                  f"1..{i - 1} estão COMMITADOS; nada foi tocado neste.")
            return 1
        try:
            r = processar_bloco(bloco)
        except SystemExit as e:
            print(f"\nPARADO no bloco {i}/{len(blocos)}: {e}")
            problemas = estado_consistente()
            print("estado dos arquivos de produção:",
                  "CONSISTENTE — blocos 1.."
                  f"{i - 1} commitados, bloco {i} não tocou o consenso"
                  if not problemas else problemas)
            return 1
        feitos += 1
        custo_total += r["custo"]["total"]
        print(f"bloco {i} commitado: {r['reviews_no_consenso']} reviews no "
              f"consenso, {r['incompletas']} incompletas, "
              f"{r['removidas']} removidas (acumulado do manifesto), "
              f"{r['pendentes_verificador']} sem veredito · custo real "
              f"US${r['custo']['total']:.4f} (pico "
              f"US${r['custo']['pico']:.4f} / fora "
              f"US${r['custo']['fora_de_pico']:.4f}) · saldo depois: "
              f"{_fmt_saldo(_saldo())}", flush=True)
        if r["incompletas"]:
            print(f"  AVISO: {r['incompletas']} review(s) sem os 3 passes "
                  f"ok ficaram FORA do consenso; reexecutar o bloco as retenta.")
    print(f"\nFIM: {feitos}/{len(blocos)} blocos · custo real "
          f"US${custo_total:.4f} · {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
