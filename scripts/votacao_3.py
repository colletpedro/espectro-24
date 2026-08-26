"""Classificação por VOTAÇÃO de 3 passadas independentes — SPEC de sessão
"Espectro 24 — Classificação por votação de 3".

A medição de estabilidade (`ESTABILIDADE_AGREGADA.md`) achou: 26,5% de
reprodutibilidade individual; a instabilidade NÃO é troca sistemática entre
eixos vizinhos (94,6% oscila de forma independente); e ela se concentra nos
eixos de fronteira menos determinada (`impacto_emocional`, `livre`,
`tom_atmosfera`). Diagnóstico: o modelo não confunde categoria, hesita SE a
review menciona o eixo perto do limiar — julgamento de grau, não erro
sistemático. Oscilação independente e sem viés é exatamente o que votação
por maioria elimina.

Este script reusa a MESMA amostra/prompt/eixos/adaptador de
`scripts/classificar_10.py` (import direto, não reimplementação) para três
(depois uma quarta) passadas independentes sobre a amostra de PRODUÇÃO
atual — que já cresceu desde a medição de 3948 reviews (v1.9.5/v1.9.6
adicionaram material e fecharam buckets: 87/105 a 40 agora, contra o que
levou à medição original).

Uso:
    python scripts/votacao_3.py amostra                # monta a amostra ATUAL (não reusa a antiga)
    python scripts/votacao_3.py passe 1 [--limite N]   # roda/retoma uma passada
    python scripts/votacao_3.py passe 2 [--limite N]
    python scripts/votacao_3.py passe 3 [--limite N]
    python scripts/votacao_3.py passe 4 [--limite N]   # Entrega 3
    python scripts/votacao_3.py consenso               # Entrega 1: junta 1-3, grava consenso
    python scripts/votacao_3.py relatorio               # Entregas 2, 4, 5
    python scripts/votacao_3.py estabilidade_consenso    # Entrega 3 (precisa do passe 4)

Saídas em `resultado/votacao-3/`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import (  # noqa: E402 — MESMO prompt/eixos/amostra/adaptador
    EIXOS,
    MARGENS,
    MODELO,
    N_RODADAS_NULO,
    PRECO_ENTRADA_HIT,
    PRECO_ENTRADA_MISS,
    PRECO_SAIDA,
    SEMENTE,
    SYSTEM,
    _lifts_do_filme,
    _mediana,
    _normalizar,
    _nulo,
    _wilson,
    montar_amostra,
    recuperar_eixo,
    taxonomia_id,
)
from espectro24.buckets import FRONTEIRAS  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
    telemetria_retentativa_llm,
)

SAIDA = RAIZ / "resultado" / "votacao-3"
ARQ_AMOSTRA = SAIDA / "amostra.json"
ARQ_PASSE = {n: SAIDA / f"passe_{n}.jsonl" for n in (1, 2, 3, 4)}
ARQ_CONSENSO = SAIDA / "consenso.jsonl"
ARQ_RELATORIO = SAIDA / "relatorio.json"
ARQ_ESTABILIDADE_CONSENSO = SAIDA / "estabilidade_consenso.json"

# Fonte da medição ANTERIOR (passada única, corpus de 3948 reviews, ANTES da
# passada by/added-earliest fechar mais buckets) — a base de comparação da
# Entrega 2/4, não tocada por este script.
FONTE_PASSADA_UNICA = RAIZ / "resultado" / "taxonomia-10" / "classificacoes.jsonl"

CONCORRENCIA = 8
# [v1.9.25] `MAX_TENTATIVAS` REMOVIDO: retentativa de transporte agora vive
# no adaptador (`synthesize._com_retentativa`, §3[D]), com backoff
# exponencial e jitter. O laço local retentava também erro de CONTEÚDO e,
# depois da v1.9.25, empilharia sobre a do adaptador.


# ===========================================================================
# Amostra — reusa `classificar_10.montar_amostra`, grava em diretório próprio
# ===========================================================================

def cmd_amostra() -> None:
    """A amostra de PRODUÇÃO atual — não a de `resultado/taxonomia-10/`, que
    foi montada sobre um bruto menor. `montar_amostra()` já não depende de
    nada além do bruto em disco, então chamar de novo aqui reflete
    automaticamente tudo que v1.9.5/v1.9.6 acrescentaram."""
    SAIDA.mkdir(parents=True, exist_ok=True)
    a = montar_amostra()
    ARQ_AMOSTRA.write_text(json.dumps(a, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"taxonomia {a['taxonomia_id']} · {len(a['filmes'])} filmes · "
          f"{len(a['reviews'])} reviews → {ARQ_AMOSTRA.relative_to(RAIZ)}")


# ===========================================================================
# Uma passada — MESMA lógica de `classificar_10.classificar`, parametrizada
# pelo número da passada e pelo arquivo de saída.
# ===========================================================================

def classificar_passe(n_passe: int, limite: int | None = None) -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    tid = amostra["taxonomia_id"]
    if tid != taxonomia_id():
        raise SystemExit(
            f"amostra gerada sob taxonomia {tid}, prompt atual é "
            f"{taxonomia_id()} — rode `amostra` de novo")

    arq = ARQ_PASSE[n_passe]
    feitos = set()
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok") and r.get("taxonomia_id") == tid:
                    feitos.add((r["slug"], r["bucket"], r["id"]))

    pendentes = [r for r in amostra["reviews"]
                 if (r["slug"], r["bucket"], r["id"]) not in feitos]
    if limite:
        pendentes = pendentes[:limite]
    print(f"passe {n_passe} · taxonomia {tid} · {len(feitos)} já feitas · "
          f"{len(pendentes)} pendentes")
    if not pendentes:
        return

    client = deepseek_client()
    lock, contador, t0 = Lock(), [0], time.time()
    falhas = [0]
    saida = arq.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        # [v1.9.25, §3[D]] SEM laço de retentativa próprio. O adaptador
        # retenta TRANSPORTE (5xx/timeout/conexão) dentro de
        # `deepseek_resposta`; um laço aqui empilharia 3×3 tentativas com
        # backoffs somados. O `except` fica só para REGISTRAR a falha e
        # deixar o passe seguir — sem re-chamar. Erro de CONTEÚDO (JSON
        # malformado) agora custa 1 chamada, não 3, e vira `ok: False`
        # visível no resumo em vez de ser reabsorvido em silêncio.
        try:
            resp = deepseek_resposta(
                SYSTEM,
                f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
                f"{review['texto']}",
                MODELO, max_tokens=300, json_mode=True, client=client)
            data = json.loads(resp.choices[0].message.content)
            eixos, livres, invalidos = _normalizar(data)
            registro = {
                "ok": True, "taxonomia_id": tid, "passe": n_passe,
                "slug": review["slug"], "perfil": review["perfil"],
                "bucket": review["bucket"], "id": review["id"],
                "nivel": review["nivel"], "n_chars": review["n_chars"],
                "eixos": eixos, "temas_livres": livres,
                "eixos_invalidos": invalidos, "uso": deepseek_uso(resp),
            }
        except Exception as e:  # noqa: BLE001
            registro = {"ok": False, "taxonomia_id": tid, "passe": n_passe,
                        "slug": review["slug"], "perfil": review["perfil"],
                        "bucket": review["bucket"], "id": review["id"],
                        "erro": f"{type(e).__name__}: {e}"}
        with lock:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
            saida.flush()
            contador[0] += 1
            if not registro["ok"]:
                falhas[0] += 1
            if contador[0] % 200 == 0 or contador[0] == len(pendentes):
                dt = time.time() - t0
                print(f"  passe {n_passe}: {contador[0]}/{len(pendentes)} · "
                      f"{dt:.0f}s · {contador[0]/dt:.1f}/s", flush=True)

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, pendentes))
    saida.close()
    # [v1.9.25] Taxa VISÍVEL: falha vira `ok: False` no JSONL e todo
    # consumidor a pula com `if not r.get("ok")`. Sem esta linha, uma taxa
    # alta some entre 8 mil registros.
    tel = telemetria_retentativa_llm()
    print(f"  passe {n_passe}: falhas (ok=False) {falhas[0]}/{len(pendentes)} "
          f"· retentativas de transporte no adaptador: {tel['n_retentativas']}"
          + (f" {tel['por_tipo']}" if tel["por_tipo"] else ""))


def cmd_passe(n_passe: int, limite: int | None) -> None:
    classificar_passe(n_passe, limite)


def cmd_rodar_1_a_3(limite: int | None) -> None:
    """As três passadas SEQUENCIAIS, no mesmo processo — cache de prefixo
    quente (nenhum intervalo entre elas), mesmo cliente HTTP reaproveitado
    dentro de cada passada."""
    for n in (1, 2, 3):
        classificar_passe(n, limite)


# ===========================================================================
# Leitura + reparo — comum a consenso, relatório e estabilidade do consenso
# ===========================================================================

def _ler_passe(n_passe: int) -> dict[tuple, dict]:
    tid = taxonomia_id()
    por_chave: dict[tuple, dict] = {}
    arq = ARQ_PASSE[n_passe]
    if not arq.exists():
        return por_chave
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok") or r.get("taxonomia_id") != tid:
            continue
        chave = (r["slug"], r["bucket"], r["id"])
        eixos = list(r["eixos"])
        for bruto in r.get("eixos_invalidos", []):
            alvo = recuperar_eixo(bruto)
            if alvo and alvo not in eixos:
                eixos.append(alvo)
        r = dict(r, eixos=sorted(set(eixos)))
        por_chave[chave] = r  # sobrescreve se repetido: última linha vence
    return por_chave


def _consensuar(passes: list[dict[tuple, dict]], chaves: list[tuple],
                minimo: int = 2) -> list[dict]:
    """Uma linha de consenso por chave presente em TODOS os passes recebidos
    — review que falhou em algum passe fica de fora do consenso (não há como
    votar com um voto faltando) e é reportada, não escondida."""
    saida = []
    for chave in chaves:
        registros = [p.get(chave) for p in passes]
        if any(r is None for r in registros):
            continue
        votos = Counter(e for r in registros for e in r["eixos"])
        finais = sorted(e for e, v in votos.items() if v >= minimo)
        base = registros[0]
        saida.append({
            "slug": base["slug"], "perfil": base["perfil"],
            "bucket": base["bucket"], "id": base["id"], "nivel": base["nivel"],
            "n_chars": base["n_chars"], "eixos": finais,
            "votos": {e: votos.get(e, 0) for e in sorted(set(votos) | set(finais))},
            "eixos_por_passe": [r["eixos"] for r in registros],
        })
    return saida


def cmd_consenso() -> None:
    """[Entrega 1] Junta os passes 1-3 por chave e grava o consenso — só
    entra na saída quem tem os TRÊS passes completos."""
    passes = [_ler_passe(n) for n in (1, 2, 3)]
    chaves = sorted(set(passes[0]) & set(passes[1]) & set(passes[2]))
    faltando = (set(passes[0]) | set(passes[1]) | set(passes[2])) - set(chaves)
    consenso = _consensuar(passes, chaves)

    SAIDA.mkdir(parents=True, exist_ok=True)
    with ARQ_CONSENSO.open("w", encoding="utf-8") as f:
        for r in consenso:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"consenso: {len(consenso)} reviews com os 3 passes completos "
          f"({len(faltando)} incompletas, fora do consenso)")
    print(f"→ {ARQ_CONSENSO.relative_to(RAIZ)}")


# ===========================================================================
# Entrega 2 — o que a votação mudou (+ decomposição corpus-vs-votação)
# ===========================================================================

def _ler_passada_unica_antiga() -> list[dict]:
    tid_atual = taxonomia_id()
    regs = []
    for linha in FONTE_PASSADA_UNICA.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok") or r.get("taxonomia_id") != tid_atual:
            continue
        eixos = list(r["eixos"])
        for bruto in r.get("eixos_invalidos", []):
            alvo = recuperar_eixo(bruto)
            if alvo and alvo not in eixos:
                eixos.append(alvo)
        regs.append(dict(r, eixos=sorted(set(eixos))))
    return regs


def _freq(regs: list[dict], eixo: str) -> float:
    return sum(1 for r in regs if eixo in r["eixos"]) / len(regs) if regs else 0.0


def _fracao_livre(regs: list[dict]) -> dict:
    """MESMA definição estrita de `classificar_10.relatorio`
    (`r["eixos"] == ["livre"]`) — não "nenhum eixo real", que é uma
    categoria DIFERENTE (ver `_fracao_consenso_vazio`, só existe sob votação:
    quando nem `livre` nem eixo nenhum alcança 2/3, o resultado é `[]`, não
    `["livre"]`). Misturar as duas inflaria `fracao_livre` e tornaria a
    comparação com o número publicado (4,81%) incomparável."""
    n = len(regs)
    k = sum(1 for r in regs if r["eixos"] == ["livre"])
    return {"n": n, "so_livre": k, "fracao": k / n if n else None,
           "ic95": _wilson(k, n)}


def _fracao_consenso_vazio(regs: list[dict]) -> dict:
    """Só existe sob votação: quando NENHUM eixo (incluindo `livre`)
    alcança 2 dos 3 votos, o consenso é `[]` — nem classificado, nem
    "livre" por consenso. É "abstenção coletiva", categoria que a passada
    única não tinha como produzir (o modelo, sozinho, sempre declara algo,
    por regra do prompt)."""
    n = len(regs)
    k = sum(1 for r in regs if r["eixos"] == [])
    return {"n": n, "vazio": k, "fracao": k / n if n else None,
           "ic95": _wilson(k, n)}


def entrega2(consenso: list[dict], antiga: list[dict],
            passe1: list[dict]) -> dict:
    categorias = list(EIXOS) + ["livre"]

    tabela_freq = []
    for e in categorias:
        fa, fp1, fc = _freq(antiga, e), _freq(passe1, e), _freq(consenso, e)
        tabela_freq.append({
            "eixo": e, "freq_antiga_corpus_menor": fa,
            "freq_passe1_corpus_atual": fp1, "freq_consenso": fc,
            "diff_pp_antiga_para_consenso": (fc - fa) * 100,
            "diff_pp_corpus_isolado_antiga_para_passe1": (fp1 - fa) * 100,
            "diff_pp_votacao_isolada_passe1_para_consenso": (fc - fp1) * 100,
        })

    def n_eixos_medio(regs):
        vals = [len([e for e in r["eixos"] if e != "livre"]) for r in regs]
        return {"media": sum(vals) / len(vals) if vals else None,
               "mediana": _mediana(vals)}

    # Quantas reviews (por chave comum antiga∩consenso) mudaram de conjunto,
    # e em que direção — só faz sentido para reviews que EXISTEM nos dois
    # (a antiga é subconjunto do corpus atual quase sempre, mas nem toda
    # review antiga sobrevive à seleção sob o bruto maior).
    chave = lambda r: (r["slug"], r["bucket"], r["id"])  # noqa: E731
    antiga_por_chave = {chave(r): r for r in antiga}
    consenso_por_chave = {chave(r): r for r in consenso}
    comuns = sorted(set(antiga_por_chave) & set(consenso_por_chave))
    ganhou, perdeu, ambos, identico = 0, 0, 0, 0
    for c in comuns:
        a = set(antiga_por_chave[c]["eixos"]) - {"livre"}
        b = set(consenso_por_chave[c]["eixos"]) - {"livre"}
        if a == b:
            identico += 1
        elif a < b:
            ganhou += 1
        elif b < a:
            perdeu += 1
        else:
            ambos += 1

    # Voto único (1/3) que NÃO sobrevive ao consenso: fração da frequência de
    # cada eixo em pelo menos-1-voto que era sustentada só por 1 voto.
    voto_unico = []
    for e in EIXOS:
        n_algum_voto = sum(1 for r in consenso if r["votos"].get(e, 0) >= 1)
        n_so_1_voto = sum(1 for r in consenso if r["votos"].get(e, 0) == 1)
        voto_unico.append({
            "eixo": e, "n_mencionado_em_ao_menos_1_passe": n_algum_voto,
            "n_so_1_de_3": n_so_1_voto,
            "fracao_da_mencao_que_e_voto_unico": (
                n_so_1_voto / n_algum_voto if n_algum_voto else None),
        })
    voto_unico.sort(key=lambda x: -(x["fracao_da_mencao_que_e_voto_unico"] or 0))

    ta = next(v for v in voto_unico if v["eixo"] == "tom_atmosfera")

    return {
        "n_antiga": len(antiga), "n_passe1_atual": len(passe1),
        "n_consenso": len(consenso), "n_reviews_comuns_antiga_consenso": len(comuns),
        "frequencia_por_eixo": tabela_freq,
        "eixos_por_review": {"antiga": n_eixos_medio(antiga),
                             "passe1_atual": n_eixos_medio(passe1),
                             "consenso": n_eixos_medio(consenso)},
        "fracao_livre": {"antiga": _fracao_livre(antiga),
                         "passe1_atual": _fracao_livre(passe1),
                         "consenso": _fracao_livre(consenso)},
        "fracao_consenso_vazio": _fracao_consenso_vazio(consenso),
        "mudanca_de_conjunto_reviews_comuns": {
            "n_comuns": len(comuns), "identico": identico, "ganhou_eixo": ganhou,
            "perdeu_eixo": perdeu, "ganhou_e_perdeu": ambos},
        "fracao_voto_unico_por_eixo": voto_unico,
        "tom_atmosfera_voto_unico": ta,
    }


# ===========================================================================
# Entrega 3 — estabilidade do CONSENSO (passe 4)
# ===========================================================================

def cmd_estabilidade_consenso() -> None:
    p1, p2, p3, p4 = (_ler_passe(n) for n in (1, 2, 3, 4))
    if not p4:
        raise SystemExit("passe 4 vazio — rode `passe 4` primeiro")

    chaves_a = sorted(set(p1) & set(p2) & set(p3))
    chaves_b = sorted(set(p2) & set(p3) & set(p4))
    chaves_comuns = sorted(set(chaves_a) & set(chaves_b))

    consenso_a = {(r["slug"], r["bucket"], r["id"]): r
                 for r in _consensuar([p1, p2, p3], chaves_a)}
    consenso_b = {(r["slug"], r["bucket"], r["id"]): r
                 for r in _consensuar([p2, p3, p4], chaves_b)}

    identicos = sum(1 for c in chaves_comuns
                    if set(consenso_a[c]["eixos"]) == set(consenso_b[c]["eixos"]))
    n = len(chaves_comuns)

    uso = Counter()
    for r in p4.values():
        for k, v in r.get("uso", {}).items():
            uso[k] += v
    custo = (uso["cache_miss_tokens"] * PRECO_ENTRADA_MISS
            + uso["cache_hit_tokens"] * PRECO_ENTRADA_HIT
            + uso["completion_tokens"] * PRECO_SAIDA)

    rel = {
        "n_comparadas": n,
        "fracao_identica": identicos / n if n else None,
        "fracao_identica_passada_unica_para_referencia": 0.265,
        "consenso_A": "maioria(passe1, passe2, passe3)",
        "consenso_B": "maioria(passe2, passe3, passe4)",
        "custo_passe4_usd": custo,
        "leitura": (
            "consenso substancialmente mais reprodutível que passada única"
            if n and identicos / n >= 0.60 else
            "consenso mais reprodutível, mas não o bastante para tratar como "
            "estável — reportar como achado, não presumir resolvido"
            if n and identicos / n > 0.265 else
            "consenso NÃO é mais reprodutível que passada única — votação de "
            "3 deslocou o problema, não o resolveu"),
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_ESTABILIDADE_CONSENSO.write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"n={n} · fração idêntica: {rel['fracao_identica']:.1%} "
          f"(passada única era 26,5%)")
    print(rel["leitura"])
    print(f"→ {ARQ_ESTABILIDADE_CONSENSO.relative_to(RAIZ)}")


# ===========================================================================
# Entrega 4 — recalibração dos números do schema, sobre o consenso
# ===========================================================================

def entrega4(consenso: list[dict]) -> dict:
    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    perfil = {f["slug"]: f["perfil"] for f in amostra["filmes"]}

    por_filme = defaultdict(list)
    for r in consenso:
        por_filme[r["slug"]].append(r)

    lifts, por_filme_lift = [], {}
    for slug, rr in sorted(por_filme.items()):
        tam = {b: sum(1 for r in rr if r["bucket"] == b) for b in FRONTEIRAS}
        if min(tam.values()) < 3:
            continue
        d = _lifts_do_filme(rr)
        n_min = min(tam.values())
        todos_40 = all(v >= 40 for v in tam.values())
        for e, v in d.items():
            lifts.append({"slug": slug, "perfil": perfil.get(slug, "?"),
                          "eixo": e, "n_min_bucket": n_min,
                          "todos_buckets_40": todos_40, **v})
        por_filme_lift[slug] = {
            "n_por_bucket": tam, "n_min_bucket": n_min,
            "todos_buckets_40": todos_40,
            "n_acima": {str(m): sum(1 for v in d.values() if v["lift"] >= m)
                        for m in MARGENS},
        }
    lifts.sort(key=lambda x: -x["lift"])

    nulo = _nulo(por_filme)

    def sem_contraste(m):
        return sorted(s for s, d in por_filme_lift.items()
                     if d["n_acima"][str(m)] == 0)

    def resumo_margem(m):
        pares_m = [x for x in lifts if x["lift"] >= m]
        n_pares_totais = len(lifts)
        media_nulo = nulo["pares_acima"][str(m)]["media"]
        n_pares_totais_no_nulo = nulo["n_pares"]
        frac_ruido = (media_nulo / n_pares_totais_no_nulo) / \
            (len(pares_m) / n_pares_totais) if n_pares_totais and pares_m else None
        return {
            "n_pares_acima": len(pares_m),
            "n_filmes_com_ao_menos_um": len({x["slug"] for x in pares_m}),
            "sem_contraste": {"n": len(sem_contraste(m)), "filmes": sem_contraste(m)},
            "fracao_ruido_estimada": frac_ruido,
        }

    grupo_cheio = [d for d in por_filme_lift.values() if d["todos_buckets_40"]]
    grupo_sub40 = [d for d in por_filme_lift.values() if not d["todos_buckets_40"]]

    return {
        "n_filmes_avaliados": len(por_filme_lift),
        "n_filmes_todos_buckets_40": len(grupo_cheio),
        "n_filmes_algum_sub40": len(grupo_sub40),
        "fracao_livre_global": _fracao_livre(consenso),
        "fracao_livre_por_bucket": {
            b: _fracao_livre([r for r in consenso if r["bucket"] == b])
            for b in FRONTEIRAS},
        "fracao_consenso_vazio_global": _fracao_consenso_vazio(consenso),
        "nulo_de_permutacao": nulo,
        "por_margem": {str(m): resumo_margem(m) for m in MARGENS},
        "top_lifts": lifts[:20],
    }


# ===========================================================================
# Entrega 5 — tom_atmosfera sob a nova régua
# ===========================================================================

def entrega5(consenso: list[dict], e4: dict) -> dict:
    TA, ST = "tom_atmosfera", "som_trilha"
    freq_ta = _freq(consenso, TA)
    freq_st = _freq(consenso, ST)

    n_com_ta = sum(1 for r in consenso if TA in r["eixos"])
    n_3de3 = sum(1 for r in consenso if r["votos"].get(TA, 0) == 3)
    n_2de3 = sum(1 for r in consenso if r["votos"].get(TA, 0) == 2)

    top = e4["top_lifts"]
    encabeca_20pp = sorted({l["slug"] for l in top
                            if l["eixo"] == TA and l["lift"] >= 0.20})
    encabeca_qualquer_margem_20pp_geral = [
        l for l in top if l["lift"] >= 0.20]
    # "encabeça uma linha" = é o eixo de MAIOR lift daquele filme, entre os
    # que passam a margem — não só "aparece acima da margem".
    melhor_por_filme = {}
    for l in top:
        if l["lift"] >= 0.20:
            atual = melhor_por_filme.get(l["slug"])
            if atual is None or l["lift"] > atual["lift"]:
                melhor_por_filme[l["slug"]] = l
    filmes_onde_ta_encabeca = sorted(
        s for s, l in melhor_por_filme.items() if l["eixo"] == TA)

    return {
        "freq_tom_atmosfera": freq_ta, "freq_som_trilha": freq_st,
        "diff_pp_tom_atmosfera_menos_som_trilha": (freq_ta - freq_st) * 100,
        "n_filmes_onde_tom_atmosfera_encabeca_margem_20pp": len(
            filmes_onde_ta_encabeca),
        "filmes": filmes_onde_ta_encabeca,
        "distribuicao_votos_tom_atmosfera": {
            "n_com_ao_menos_1_voto": n_com_ta,
            "3_de_3": n_3de3, "2_de_3": n_2de3,
            "fracao_3_de_3": n_3de3 / n_com_ta if n_com_ta else None,
        },
    }


# ===========================================================================
# Relatório completo — Entregas 2, 4, 5
# ===========================================================================

def cmd_relatorio() -> None:
    if not ARQ_CONSENSO.exists():
        raise SystemExit("falta consenso.jsonl — rode `consenso` primeiro")
    consenso = [json.loads(l) for l in
               ARQ_CONSENSO.read_text(encoding="utf-8").splitlines() if l.strip()]
    antiga = _ler_passada_unica_antiga()
    passe1 = list(_ler_passe(1).values())

    e2 = entrega2(consenso, antiga, passe1)
    e4 = entrega4(consenso)
    e5 = entrega5(consenso, e4)

    rel = {"taxonomia_id": taxonomia_id(), "n_consenso": len(consenso),
          "entrega2_o_que_a_votacao_mudou": e2,
          "entrega4_recalibracao_schema": e4,
          "entrega5_tom_atmosfera": e5}
    ARQ_RELATORIO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    print(f"n_consenso={len(consenso)}")
    fl = e2["fracao_livre"]

    def _pct(x):
        # `antiga` vem de FONTE_PASSADA_UNICA filtrada pelo taxonomia_id
        # ATUAL (§_ler_passada_unica_antiga) — muda a taxonomia (como a
        # promoção de A_regra mudou), e essa fonte fica vazia por
        # construção: nenhuma linha do arquivo single-pass antigo carrega o
        # id novo. `fracao` sai `None`, não um bug de aritmética; formatar
        # sem essa guarda derrubava o relatório DEPOIS do JSON já gravado.
        return f"{x:.2%}" if x is not None else "n/a (antiga sob outra taxonomia)"

    print(f"fracao_livre: antiga {_pct(fl['antiga']['fracao'])} → "
          f"passe1(corpus atual) {_pct(fl['passe1_atual']['fracao'])} → "
          f"consenso {_pct(fl['consenso']['fracao'])}")
    print(f"consenso vazio (abstenção coletiva, sem paralelo na passada "
          f"única): {e2['fracao_consenso_vazio']['fracao']:.2%}")
    print(f"tom_atmosfera: freq consenso {e5['freq_tom_atmosfera']:.2%} "
          f"(som_trilha {e5['freq_som_trilha']:.2%}) · "
          f"encabeça linha em {e5['n_filmes_onde_tom_atmosfera_encabeca_margem_20pp']} "
          f"filmes (era 3)")
    print(f"→ {ARQ_RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="etapa", required=True)
    sub.add_parser("amostra")
    p_passe = sub.add_parser("passe")
    p_passe.add_argument("n", type=int, choices=[1, 2, 3, 4])
    p_passe.add_argument("--limite", type=int, default=None)
    p_rodar = sub.add_parser("rodar_1_a_3")
    p_rodar.add_argument("--limite", type=int, default=None)
    sub.add_parser("consenso")
    sub.add_parser("relatorio")
    sub.add_parser("estabilidade_consenso")
    args = ap.parse_args()

    SAIDA.mkdir(parents=True, exist_ok=True)
    if args.etapa == "amostra":
        cmd_amostra()
    elif args.etapa == "passe":
        cmd_passe(args.n, args.limite)
    elif args.etapa == "rodar_1_a_3":
        cmd_rodar_1_a_3(args.limite)
    elif args.etapa == "consenso":
        cmd_consenso()
    elif args.etapa == "relatorio":
        cmd_relatorio()
    else:
        cmd_estabilidade_consenso()
