"""[Entregas 2-4] Classificação dos 35 filmes na taxonomia AMPLIADA de 10 eixos.

Sucede `scripts/gate_taxonomia.py`, que rodou 8 eixos sobre uma amostra de 15
filmes × 20 reviews/bucket. Aqui: **10 eixos**, **35 filmes**, e a **cota real
de produção** (até 40 por bucket, o que a seleção downstream entregaria à
síntese).

O que mudou na taxonomia, e por quê (decisão registrada após o gate):
  + `expectativa`    — recorria em 15/15 filmes, o único tema livre presente
                       em TODOS. PROMOVIDO.
  + `critica_social` — recorria em 14/15 e era o maior contribuinte isolado
                       do excesso de `livre` no bucket negativo. PROMOVIDO.
  ~ `impacto_emocional` — AFROUXADO. A família `reacao` (13/15 filmes, e a
                       maior conversão em reviews só-`livre`) não era eixo
                       faltando: era fronteira mal desenhada. A regra antiga
                       empurrava reação visceral e reação de plateia para
                       fora junto com o elogio vazio. Agora só o elogio vazio
                       fica de fora.
  – `assistir`       — NÃO promovido. A inspeção da Entrega 1 mostrou que 26
                       de 30 exemplos já caem nos 10 eixos (14 em
                       `expectativa`, 14 em `impacto_emocional`).

**Correção de recall em review curta (sessão 2026-08-13, `taxonomia_id`
`11871105c0d3` → `ebab2667de74`).** Auditoria humana de 100 reviews contra o
consenso de votação de 3 (`resultado/auditoria-acuracia/`) achou recall
0,35 em reviews ≤200 chars (23,4% do corpus de produção) contra 0,88 acima
de 400 — com precisão ESTÁVEL em 0,87-0,93 em toda faixa: o modelo não
trocava de eixo em texto curto, ele OMITIA eixo. 27 de 100 reviews tinham
recall zero (23 delas ≤200 chars); em 12 as três passadas foram unânimes em
`livre`, quando o humano via eixo real — unanimidade não protegia contra o
defeito.

Duas variantes de REGRAS foram testadas contra o mesmo gabarito humano
(`scripts/variantes_prompt_curtas.py`, arquivado após esta promoção,
resultado completo em `resultado/auditoria-acuracia/variantes/`):

  A (`regra`, PROMOVIDA) — brevidade não é ausência de conteúdo; `livre`
      redefinido por ASSUNTO (a review não fala do filme) em vez de por
      profundidade (fala pouco do filme). Bootstrap pareado (B=5000): recall
      ≤200 chars 0,35→0,61 (δ +0,265, IC95 [+0,171, +0,370]), recall geral
      0,69→0,76 (δ +0,076, IC95 [+0,030, +0,124]), reviews com recall zero
      27→5, consensos vazios 8→0 — **sem perda de precisão detectável** (δ
      precisão geral IC95 [-0,035, +0,030], cruza zero).
  B (`fewshot`, REJEITADA) — as mesmas regras de A + 6 exemplos resolvidos
      de review curta. Resultado NEGATIVO: os exemplos curtos ancoraram o
      modelo e degradaram review longa (recall 401-800: 0,888→0,847;
      801+: 0,880→0,805), com concordância exata caindo ABAIXO do baseline
      (0,180→0,170). Mesmo padrão que o experimento Ollama do projeto já
      tinha registrado: instrução adicional pode degradar em vez de ajudar.

Só o bloco REGRAS mudou — lista de eixos e as 10 definições seguem
byte-idênticas (testado em `tests/test_variantes_prompt.py` e
`tests/test_promocao_a_regra.py`).

Arquitetura, a de sempre: **o LLM classifica review a review, o CÓDIGO soma.**
Uma chamada por review, a review sozinha no prompt, sem nenhuma contagem à
vista. Toda frequência, fração e lift deste relatório é `Counter`.

Transporte: **sempre pelo adaptador** (`deepseek_client`/`deepseek_resposta`/
`deepseek_uso`, §3[D]). O guard-rail da v1.9.4 reprova qualquer caminho novo
que instancie o SDK por conta própria.

A classificação é persistida VERSIONADA POR TAXONOMIA (`taxonomia_id`, um
hash do prompt + da lista de eixos): uma sessão futura que mude a taxonomia
recebe um id novo e não reaproveita silenciosamente classificação obsoleta;
uma que não mude reusa tudo, sem reclassificar.

Uso:
    python scripts/classificar_10.py amostra
    python scripts/classificar_10.py classificar [--limite N]
    python scripts/classificar_10.py relatorio
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.bruto import carregar  # noqa: E402
from espectro24.buckets import FRONTEIRAS  # noqa: E402
from espectro24.selecao import selecionar  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
    telemetria_retentativa_llm,
)

SAIDA = RAIZ / "resultado" / "taxonomia-10"
ARQ_AMOSTRA = SAIDA / "amostra.json"
ARQ_CLASSIF = SAIDA / "classificacoes.jsonl"
ARQ_RELATORIO = SAIDA / "relatorio.json"

SEMENTE = 20260808
MODELO = "deepseek-v4-flash"
CONCORRENCIA = 8
# [v1.9.25] `MAX_TENTATIVAS` REMOVIDO: a retentativa de transporte passou a
# viver no adaptador (`synthesize._com_retentativa`, §3[D]), com backoff
# exponencial e jitter. O laço local retentava também erro de CONTEÚDO e,
# depois da v1.9.25, empilharia sobre a do adaptador.
MARGENS = (0.10, 0.15, 0.20, 0.25)
N_RODADAS_NULO = 2000

# --- Taxonomia: definida em `src/espectro24/taxonomia.py` (v1.9.14) -------
# EIXOS, SYSTEM e `taxonomia_id()` SAÍRAM daqui e viraram módulo de produção,
# porque a rotulagem de temas por eixo (§[D3]) precisa das MESMAS definições.
# Mudança de lugar, não de conteúdo: `taxonomia_id()` segue `ebab2667de74`, e
# `tests/test_promocao_a_regra.py` trava esse valor. Reexportados aqui porque
# este script (e os de medição ao lado) os consomem por este nome.
from espectro24.taxonomia import (  # noqa: E402
    EIXOS,
    EIXOS_VALIDOS,
    SYSTEM,
    taxonomia_id,
)

# Preços DeepSeek, USD por 1M de tokens (config.py, v1.8.0).
PRECO_ENTRADA_MISS = 0.14 / 1_000_000
PRECO_ENTRADA_HIT = 0.0028 / 1_000_000
PRECO_SAIDA = 0.28 / 1_000_000



# ===========================================================================
# AMOSTRA — a cota REAL de produção, todos os filmes
# ===========================================================================

def montar_amostra() -> dict:
    """A amostra é o que a seleção downstream entregaria à síntese: até 40 por
    bucket, com os parâmetros de produção. Nada é sorteado — ao contrário do
    gate (que amostrava 20 de 40 para baratear), aqui a amostra É a
    população que a síntese veria."""
    itens, resumo = [], []
    for d in sorted((RAIZ / "dados" / "bruto").iterdir()):
        if not (d / "meta.json").exists():
            continue
        slug = d.name
        meta, todas = carregar(slug)
        hist = {float(k): v for k, v in meta.get("histograma_bruto", {}).items()}
        if not hist:
            continue
        sel = selecionar(todas, hist)
        total = sum(hist.values()) or 1
        shares = {nome: round(100 * sum(v for k, v in hist.items() if lo <= k <= hi)
                              / total)
                  for nome, (lo, hi) in FRONTEIRAS.items()}
        linha = {"slug": slug, "total_notas": sum(hist.values()),
                 "shares": shares,
                 "bucket_dominante": max(shares, key=shares.get),
                 "n_por_bucket": {n: b.n_final for n, b in sel.items()},
                 "estado_piso": {n: b.estado_piso for n, b in sel.items()}}
        linha["perfil"] = perfil_de(slug, hist)
        resumo.append(linha)
        for nome, bucket in sel.items():
            for n in sorted(bucket.niveis):
                for r in bucket.niveis[n].validas:
                    itens.append({"slug": slug, "perfil": linha["perfil"],
                                  "bucket": nome, "id": r.id, "nivel": r.nivel,
                                  "n_chars": r.n_chars, "texto": r.texto})
    return {
        "taxonomia_id": taxonomia_id(),
        "taxonomia": list(EIXOS),
        "semente": SEMENTE,
        "criterio": ("selecao.selecionar() com parâmetros de produção (cota 40 "
                     "por bucket, min_chars 150, cascata, spoiler excluído). "
                     "SEM sorteio: a amostra é a população que a síntese veria."),
        "filmes": resumo,
        "reviews": itens,
    }


_ARTHOUSE = {"perfect-days-2023", "anatomy-of-a-fall", "aftersun",
             "im-still-here-2024", "cidade-de-deus", "cure", "parasite-2019"}


def perfil_de(slug: str, hist: dict[float, int]) -> str:
    """Mesma regra do gate (`gate_taxonomia.perfil_de`), reproduzida aqui para
    que este script não dependa do anterior. Precedência: obscuro > invertido
    > divisivo > arthouse > aclamado."""
    total = sum(hist.values())
    def share(lo, hi):  # noqa: E306
        return 100 * sum(v for k, v in hist.items() if lo <= k <= hi) / total
    if total < 10_000:
        return "obscuro"
    if share(*FRONTEIRAS["negativas"]) >= 20:
        return "invertido"
    if share(*FRONTEIRAS["medianas"]) >= 20:
        return "divisivo"
    if slug in _ARTHOUSE:
        return "arthouse"
    return "aclamado"


# ===========================================================================
# CLASSIFICAÇÃO — 1 chamada por review, pelo adaptador
# ===========================================================================

def _sem_acento(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def recuperar_eixo(nome: str, cutoff: float = 0.85) -> str | None:
    """Repara um nome de eixo MALFORMADO, ou devolve `None`.

    Achado desta sessão: com 8 eixos o modelo não errou o nome NENHUMA vez em
    2107 atribuições; com 10 eixos ele erra — `crítica_social` (com acento),
    `ton_atmosfera`, `rotetro_estrutura`, `atuação`. Lista mais longa, mais
    erro de digitação. Descartar esses casos, como o normalizador fazia,
    subestimaria sistematicamente os eixos de nome mais comprido — inclusive
    `critica_social`, que é NOVO e cuja frequência é justamente o que está
    sendo medido.

    A recuperação é MECÂNICA e conservadora, deliberadamente: tira acento,
    ignora separadores, e aceita só se a semelhança com UM único eixo válido
    passar de `cutoff`. Não há tabela de sinônimos escrita à mão — `elenco`,
    `atores`, `humor` e `dialogos` continuam INVÁLIDOS, porque não são erro
    de digitação: são o modelo saindo da taxonomia, e essa é uma informação
    que o relatório precisa preservar, não apagar.
    """
    from difflib import SequenceMatcher

    alvo = _sem_acento(nome).lower().replace("_", "").replace(" ", "")
    if not alvo:
        return None
    escores = sorted(
        ((SequenceMatcher(None, alvo, e.replace("_", "")).ratio(), e)
         for e in EIXOS), reverse=True)
    if escores[0][0] < cutoff:
        return None
    # Empate no topo = ambíguo; não adivinha.
    if len(escores) > 1 and escores[1][0] == escores[0][0]:
        return None
    return escores[0][1]


def _normalizar(data: dict) -> tuple[list[str], list[str], list[str]]:
    crus = data.get("eixos") or []
    if isinstance(crus, str):
        crus = [crus]
    eixos, invalidos = [], []
    for e in crus:
        e = str(e).strip().lower()
        (eixos if e in EIXOS_VALIDOS else invalidos).append(e)
    livres = data.get("temas_livres") or []
    if isinstance(livres, str):
        livres = [livres]
    return (sorted(set(eixos)),
            [str(t).strip().lower() for t in livres if str(t).strip()],
            invalidos)


def classificar(limite: int | None = None) -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    tid = amostra["taxonomia_id"]
    if tid != taxonomia_id():
        raise SystemExit(
            f"amostra gerada sob taxonomia {tid}, prompt atual é "
            f"{taxonomia_id()} — rode `amostra` de novo")

    feitos = set()
    if ARQ_CLASSIF.exists():
        for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                # Classificação de OUTRA taxonomia não conta como feita.
                if r.get("ok") and r.get("taxonomia_id") == tid:
                    feitos.add((r["slug"], r["bucket"], r["id"]))

    pendentes = [r for r in amostra["reviews"]
                 if (r["slug"], r["bucket"], r["id"]) not in feitos]
    if limite:
        pendentes = pendentes[:limite]
    print(f"taxonomia {tid} · {len(feitos)} já classificadas · "
          f"{len(pendentes)} pendentes")
    if not pendentes:
        return

    client = deepseek_client()
    lock, contador, t0 = Lock(), [0], time.time()
    falhas = [0]
    saida = ARQ_CLASSIF.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        # [v1.9.25, §3[D]] SEM laço de retentativa próprio. O adaptador
        # retenta TRANSPORTE (5xx/timeout/conexão) dentro de
        # `deepseek_resposta`; um laço aqui empilharia 3×3 tentativas com
        # backoffs somados. O `except` fica só para REGISTRAR a falha e
        # deixar o lote seguir — sem re-chamar. Erro de CONTEÚDO (JSON
        # malformado) agora custa 1 chamada, não 3, e vira `ok: False`
        # visível no relatório em vez de ser reabsorvido em silêncio.
        try:
            resp = deepseek_resposta(
                SYSTEM,
                f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
                f"{review['texto']}",
                MODELO, max_tokens=300, json_mode=True, client=client)
            data = json.loads(resp.choices[0].message.content)
            eixos, livres, invalidos = _normalizar(data)
            registro = {
                "ok": True, "taxonomia_id": tid, "slug": review["slug"],
                "perfil": review["perfil"], "bucket": review["bucket"],
                "id": review["id"], "nivel": review["nivel"],
                "n_chars": review["n_chars"], "eixos": eixos,
                "temas_livres": livres, "eixos_invalidos": invalidos,
                "uso": deepseek_uso(resp),
            }
        except Exception as e:  # noqa: BLE001
            registro = {"ok": False, "taxonomia_id": tid, "slug": review["slug"],
                        "perfil": review["perfil"], "bucket": review["bucket"],
                        "id": review["id"], "erro": f"{type(e).__name__}: {e}"}
        with lock:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
            saida.flush()
            contador[0] += 1
            if not registro["ok"]:
                falhas[0] += 1
            if contador[0] % 200 == 0 or contador[0] == len(pendentes):
                dt = time.time() - t0
                print(f"  {contador[0]}/{len(pendentes)} · {dt:.0f}s "
                      f"· {contador[0]/dt:.1f}/s", flush=True)

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, pendentes))
    saida.close()
    # [v1.9.25] Taxa VISÍVEL, não só gravada: falha de conteúdo vira `ok:
    # False` no JSONL, e todo consumidor faz `if not r.get("ok"): continue`
    # — sem esta linha, uma taxa alta some entre 8 mil registros.
    tel = telemetria_retentativa_llm()
    print(f"  falhas registradas (ok=False): {falhas[0]}/{len(pendentes)} · "
          f"retentativas de transporte no adaptador: {tel['n_retentativas']}"
          + (f" {tel['por_tipo']}" if tel["por_tipo"] else ""))


# ===========================================================================
# RELATÓRIO — aritmética pura
# ===========================================================================

def _carregar_ok() -> tuple[list[dict], int, dict]:
    """Lê a classificação persistida e REPARA os nomes de eixo malformados.

    O reparo roda na leitura, não na escrita: o JSONL guarda o que o modelo
    de fato devolveu (`eixos_invalidos` intacto), e a auditoria de quanto foi
    recuperado — e de quê — sai no relatório."""
    tid = taxonomia_id()
    regs, vistos, falhas = [], set(), 0
    recuperados = Counter()
    for linha in ARQ_CLASSIF.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if r.get("taxonomia_id") != tid:
            continue
        chave = (r["slug"], r["bucket"], r["id"])
        if not r.get("ok"):
            falhas += 1
            continue
        if chave in vistos:
            continue
        vistos.add(chave)
        sobraram = []
        for bruto in r.get("eixos_invalidos", []):
            alvo = recuperar_eixo(bruto)
            if alvo is None:
                sobraram.append(bruto)
            else:
                recuperados[f"{bruto} → {alvo}"] += 1
                if alvo not in r["eixos"]:
                    r["eixos"].append(alvo)
        r["eixos"] = sorted(r["eixos"])
        r["eixos_invalidos"] = sobraram
        regs.append(r)
    return regs, falhas, dict(recuperados.most_common())


def _wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - m), min(1.0, c + m)]


def _mediana(xs: list[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return 0.0
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _lifts_do_filme(regs: list[dict]) -> dict[str, dict]:
    porb = {b: [r for r in regs if r["bucket"] == b] for b in FRONTEIRAS}
    saida = {}
    for e in EIXOS:
        f = {b: (sum(1 for r in v if e in r["eixos"]) / len(v)) if v else 0.0
             for b, v in porb.items()}
        ordenado = sorted(f.values())
        vencedor = max(f, key=f.get)
        saida[e] = {"bucket": vencedor, "freq": f[vencedor],
                    "lift": ordenado[-1] - ordenado[-2], "freqs": f}
    return saida


def _nulo(por_filme: dict[str, list[dict]], n_rodadas: int = N_RODADAS_NULO
          ) -> dict:
    """Nulo de permutação: embaralha o rótulo de BUCKET dentro de cada filme,
    preservando os tamanhos de bucket e a frequência global de cada eixo
    naquele filme. Mede quantos pares (filme, eixo) cruzariam cada margem sem
    nenhuma associação real — e quantos filmes ficariam sem NENHUM eixo acima
    dela (a contagem da Entrega 4)."""
    filmes = []
    for slug, regs in sorted(por_filme.items()):
        tamanhos = [sum(1 for r in regs if r["bucket"] == b) for b in FRONTEIRAS]
        if min(tamanhos) < 3:
            continue
        filmes.append((slug, tamanhos,
                       [[e in r["eixos"] for e in EIXOS] for r in regs]))

    # O nulo é medido também SEPARADO por tamanho de bucket: a pergunta da
    # Entrega 3 é se o piso de ruído dos buckets sub-40 exige margem maior, e
    # uma média sobre os dois grupos juntos esconderia exatamente isso.
    grupos = {
        "todos": filmes,
        "todos_buckets_40": [f for f in filmes if min(f[1]) >= 40],
        "algum_bucket_sub40": [f for f in filmes if min(f[1]) < 40],
    }

    nomes_do_grupo = {g: {f[0] for f in fs} for g, fs in grupos.items()}
    rng = random.Random(f"{SEMENTE}:nulo10")
    pares = {str(m): [] for m in MARGENS}
    sem_contraste = {str(m): [] for m in MARGENS}
    por_grupo = {g: {str(m): [] for m in MARGENS} for g in grupos}
    for _ in range(n_rodadas):
        c_pares = {str(m): 0 for m in MARGENS}
        c_sem = {str(m): 0 for m in MARGENS}
        c_grupo = {g: {str(m): 0 for m in MARGENS} for g in grupos}
        for _slug, tamanhos, marcas in filmes:
            ordem = list(range(len(marcas)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos:
                fatias.append(ordem[ini:ini + t])
                ini += t
            lifts = []
            for i in range(len(EIXOS)):
                fs = sorted(sum(marcas[j][i] for j in fat) / len(fat)
                            for fat in fatias)
                lifts.append(fs[-1] - fs[-2])
            for m in MARGENS:
                acima = sum(1 for v in lifts if v >= m)
                c_pares[str(m)] += acima
                c_sem[str(m)] += (acima == 0)
                for g, nomes in nomes_do_grupo.items():
                    if _slug in nomes:
                        c_grupo[g][str(m)] += acima
        for m in MARGENS:
            pares[str(m)].append(c_pares[str(m)])
            sem_contraste[str(m)].append(c_sem[str(m)])
            for g in grupos:
                por_grupo[g][str(m)].append(c_grupo[g][str(m)])

    def resumo(xs):
        xo = sorted(xs)
        return {"media": sum(xs) / len(xs), "p5": xo[int(0.05 * len(xo))],
                "p95": xo[int(0.95 * len(xo))], "max": xo[-1]}

    return {
        "n_rodadas": n_rodadas, "n_filmes": len(filmes),
        "n_pares": len(filmes) * len(EIXOS),
        "pares_acima": {str(m): resumo(pares[str(m)]) for m in MARGENS},
        "filmes_sem_contraste": {str(m): resumo(sem_contraste[str(m)])
                                 for m in MARGENS},
        "por_grupo": {
            g: {"n_filmes": len(fs), "n_pares": len(fs) * len(EIXOS),
                "pares_acima": {str(m): resumo(por_grupo[g][str(m)])
                                for m in MARGENS}}
            for g, fs in grupos.items() if fs},
    }


def relatorio() -> dict:
    amostra = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    regs, falhas, recuperados = _carregar_ok()
    perfil = {f["slug"]: f["perfil"] for f in amostra["filmes"]}
    n_por_bucket = {f["slug"]: f["n_por_bucket"] for f in amostra["filmes"]}

    def so_livre(r):
        return r["eixos"] == ["livre"]

    def frac(sub):
        n = len(sub)
        k = sum(1 for r in sub if so_livre(r))
        return {"n": n, "so_livre": k, "fracao": (k / n) if n else None,
                "ic95": _wilson(k, n)}

    por = lambda ch: {v: frac([r for r in regs if ch(r) == v])  # noqa: E731
                      for v in sorted({ch(r) for r in regs})}

    n_eixos = [len([e for e in r["eixos"] if e != "livre"]) for r in regs]
    freq_global = {e: sum(1 for r in regs if e in r["eixos"]) / len(regs)
                   for e in EIXOS}
    freq_bucket = {}
    for b in FRONTEIRAS:
        sub = [r for r in regs if r["bucket"] == b]
        freq_bucket[b] = {e: (sum(1 for r in sub if e in r["eixos"]) / len(sub))
                          if sub else None for e in EIXOS}

    por_filme = defaultdict(list)
    for r in regs:
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
            lifts.append({"slug": slug, "perfil": perfil[slug], "eixo": e,
                          "n_min_bucket": n_min, "todos_buckets_40": todos_40,
                          **v})
        por_filme_lift[slug] = {
            "perfil": perfil[slug], "n_por_bucket": tam, "n_min_bucket": n_min,
            "todos_buckets_40": todos_40,
            "melhor_eixo": max(d, key=lambda e: d[e]["lift"]),
            "melhor_lift": max(v["lift"] for v in d.values()),
            "n_acima": {str(m): sum(1 for v in d.values() if v["lift"] >= m)
                        for m in MARGENS},
        }
    lifts.sort(key=lambda x: -x["lift"])

    def resumo_lift(sub):
        return {
            "n_pares": len(sub), "n_filmes": len({l["slug"] for l in sub}),
            "acima": {str(m): sum(1 for l in sub if l["lift"] >= m)
                      for m in MARGENS},
            "filmes_com_ao_menos_um": {
                str(m): len({l["slug"] for l in sub if l["lift"] >= m})
                for m in MARGENS},
            "por_eixo_15pp": dict(Counter(
                l["eixo"] for l in sub if l["lift"] >= 0.15)),
            "por_bucket_vencedor_15pp": dict(Counter(
                l["bucket"] for l in sub if l["lift"] >= 0.15)),
        }

    cheios = [l for l in lifts if l["todos_buckets_40"]]
    parciais = [l for l in lifts if not l["todos_buckets_40"]]

    sem_contraste = {
        str(m): sorted(s for s, d in por_filme_lift.items()
                       if d["n_acima"][str(m)] == 0)
        for m in MARGENS}

    uso = Counter()
    for r in regs:
        for k, v in r["uso"].items():
            uso[k] += v
    custo = (uso["cache_miss_tokens"] * PRECO_ENTRADA_MISS
             + uso["cache_hit_tokens"] * PRECO_ENTRADA_HIT
             + uso["completion_tokens"] * PRECO_SAIDA)

    return {
        "taxonomia_id": taxonomia_id(),
        "taxonomia": list(EIXOS),
        "amostra": {
            "n_filmes": len(amostra["filmes"]),
            "n_reviews": len(amostra["reviews"]),
            "n_classificadas_ok": len(regs), "n_falhas": falhas,
            "criterio": amostra["criterio"],
            "n_por_bucket_por_filme": n_por_bucket,
        },
        "entrega2_fracao_livre": {
            "global": frac(regs),
            "por_bucket": por(lambda r: r["bucket"]),
            "por_perfil": por(lambda r: perfil[r["slug"]]),
            "por_filme": por(lambda r: r["slug"]),
        },
        "entrega2_distribuicao": {
            "eixos_por_review": {
                "media": sum(n_eixos) / len(n_eixos),
                "mediana": _mediana(n_eixos),
                "histograma": dict(sorted(Counter(n_eixos).items())),
            },
            "freq_global": freq_global,
            "freq_por_bucket": freq_bucket,
        },
        "entrega3_lift": {
            "todos": resumo_lift(lifts),
            "so_filmes_com_3_buckets_a_40": resumo_lift(cheios),
            "filmes_com_algum_bucket_sub40": resumo_lift(parciais),
            "nulo_de_permutacao": _nulo(por_filme),
            "top": lifts[:40],
            "por_filme": por_filme_lift,
        },
        "entrega4_contraste": {
            "sem_contraste_por_margem": {
                str(m): {"n": len(sem_contraste[str(m)]),
                         "filmes": sem_contraste[str(m)]} for m in MARGENS},
            "n_filmes_avaliados": len(por_filme_lift),
            "n_filmes_todos_buckets_40": sum(
                1 for d in por_filme_lift.values() if d["todos_buckets_40"]),
        },
        "entrega5_custo": {
            "modelo": MODELO, "n_classificadas": len(regs),
            "uso_tokens": dict(uso),
            "taxa_cache_hit": (uso["cache_hit_tokens"] / uso["prompt_tokens"]
                               if uso["prompt_tokens"] else 0.0),
            "custo_usd": custo,
            "custo_usd_por_review": custo / len(regs) if regs else 0.0,
        },
        "nomes_de_eixo_reparados": recuperados,
        "eixos_invalidos_remanescentes": dict(Counter(
            e for r in regs for e in r.get("eixos_invalidos", [])).most_common()),
        "temas_livres_mais_comuns": dict(Counter(
            t for r in regs for t in r["temas_livres"]).most_common(40)),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["amostra", "classificar", "relatorio"])
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.etapa == "amostra":
        a = montar_amostra()
        ARQ_AMOSTRA.write_text(json.dumps(a, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"taxonomia {a['taxonomia_id']} · {len(a['filmes'])} filmes · "
              f"{len(a['reviews'])} reviews → {ARQ_AMOSTRA.relative_to(RAIZ)}")
    elif args.etapa == "classificar":
        classificar(args.limite)
    else:
        rel = relatorio()
        ARQ_RELATORIO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(json.dumps(rel["entrega2_fracao_livre"]["global"], indent=1))
        print(f"→ {ARQ_RELATORIO.relative_to(RAIZ)}")
