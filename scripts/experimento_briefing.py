#!/usr/bin/env python3
"""[experimento de briefing] Harness do experimento pareado — desenho B.

Desenho, regra de decisão e poder: `docs/arquivo-de-estudos/
experimento-briefing/ETAPA_0_DESENHO.md` (seção "Pré-registro").

Subcomandos, na ordem:
    preregistro   estratos M/U, temas excluídos, réplicas, ordem dos braços
    gerar         os dois braços (e a 2ª réplica nos filmes com tema em M)
    medir         custo real (raciocínio incluído), recusa, ressalva — SELADO
    relatorio     relatório CEGO de rotulagem + mapeamento selado

**Nada daqui escreve em `resultado/`**, e o briefing de produção é o default
de `condicoes`: o braço controle é `variante=None`, byte a byte a produção.
A geração passa por `condicoes.gerar` com o ponto de injeção `gerar=`, que
chama o MESMO adaptador (`synthesize.resposta`, mesmos `max_tokens` e
`json_mode` de `_gerar_real`) e grava os contadores CRUS do Gemini —
`thoughts_token_count` incluído, que `synthesize.uso()` ignora.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from espectro24 import condicoes as C  # noqa: E402

DIR = RAIZ / "docs" / "arquivo-de-estudos" / "experimento-briefing"
GER = DIR / "geracao"
SELO = DIR / "NAO_ABRIR_ANTES_DA_ROTULAGEM"
PREREG = DIR / "preregistro.json"
RESULTADO_DIR = RAIZ / "resultado"

SEMENTE = "experimento-briefing/2026-09-15"
BRACOS = {"controle": None, "variante": C.VARIANTE_EXPERIMENTO}
N_U = 80
MAX_U_POR_FILME = 2
PRECO_ENTRADA, PRECO_SAIDA = 0.75, 3.75      # US$/M, ABERTO.md item 3

# Os 8 temas cujo texto entra no prompt variante (IN-SAMPLE). Chave = filme e
# código do tema; o nome do tema é conferido contra o publicado de hoje.
IN_SAMPLE = [
    ("C001", "burning-2018", "POS-A", "Ambiguidade e abertura a interpretações", "R1"),
    ("C010", "drive-my-car", "POS-B", "Relação entre Kafuku e Misaki", "arco"),
    ("C058", "memories-of-murder", "POS-A", "Atuações e personagens complexos", "arco"),
    ("C103", "the-second-mother", "POS-A", "Desigualdade social e crítica de classe", "R1"),
    ("C120", "the-turin-horse", "NEG-F", "Comparações desfavoráveis com outras obras ou diretores", "R1"),
    ("C127", "whiplash-2014", "POS-A", "Atuações marcantes", "R1"),
    ("C137", "zama", "POS-C", "Crítica ao colonialismo e à burocracia", "R1"),
    ("C138", "zama", "POS-E", "Dificuldade de envolvimento emocional ou compreensão", "R1"),
]


def _sha(obj) -> str:
    return hashlib.sha256(obj if isinstance(obj, bytes)
                          else json.dumps(obj, ensure_ascii=False,
                                          sort_keys=True).encode()).hexdigest()


def _doc(slug: str) -> dict:
    return json.loads((RESULTADO_DIR / f"{slug}.json").read_text(encoding="utf-8"))


def _escrever(caminho: Path, obj) -> bytes:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    caminho.write_bytes(dados)
    return dados


# ===========================================================================
# PRÉ-REGISTRO
# ===========================================================================

def preregistro() -> None:
    import gerar_condicoes as G

    if PREREG.exists():
        raise SystemExit(f"RECUSADO: {PREREG} já existe — o pré-registro não "
                         "se refaz depois de gravado.")
    temas, excluidos = [], []
    fora = {(s, t): (c, nome, grupo) for c, s, t, nome, grupo in IN_SAMPLE}
    for slug in G.slugs_publicados():
        b = C.montar_briefing(_doc(slug))
        if b is None:
            continue
        for lado in C.LADOS:
            for t in b["selecao"][lado]:
                chave = (slug, t["id"])
                reg = {"slug": slug, "lado": lado, "tema_origem": t["id"],
                       "tema": t["tema"], "ressalvas": C.ressalvas_do_tema(t)}
                if chave in fora:
                    c, nome, grupo = fora.pop(chave)
                    if t["tema"] != nome:
                        raise SystemExit(f"{c}: tema mudou — {t['tema']!r}")
                    excluidos.append({**reg, "item_piloto": c, "grupo": grupo})
                    continue
                temas.append(reg)
    if fora:
        raise SystemExit(f"temas in-sample fora da seleção de hoje: {fora}")

    M = [t for t in temas if t["ressalvas"]]
    pool = [t for t in temas if not t["ressalvas"]]
    rng = random.Random(SEMENTE)
    por_filme: dict[str, list] = {}
    for t in pool:
        por_filme.setdefault(t["slug"], []).append(t)
    U = [rng.choice(por_filme[s]) for s in sorted(por_filme)]
    segundos = [s for s in sorted(por_filme) if len(por_filme[s]) >= 2]
    rng.shuffle(segundos)
    for s in segundos[:N_U - len(U)]:
        U.append(rng.choice([t for t in por_filme[s] if t not in U]))
    assert len(U) == N_U, len(U)

    filmes = sorted({t["slug"] for t in temas} | {t["slug"] for t in excluidos})
    com_replica = sorted({t["slug"] for t in M})
    ordem = {f"{s}#r{r}": (["controle", "variante"]
                           if int(_sha(f"{SEMENTE}|{s}|{r}".encode())[:8], 16) % 2 == 0
                           else ["variante", "controle"])
             for s in filmes for r in ((1, 2) if s in com_replica else (1,))}
    reg = {
        "semente": SEMENTE,
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bracos": {k: v for k, v in BRACOS.items()},
        "n_filmes": len(filmes),
        "n_temas_pedidos": len(temas) + len(excluidos),
        "n_temas_analisaveis": len(temas),
        "excluidos_in_sample": excluidos,
        "M": [{k: t[k] for k in ("slug", "lado", "tema_origem", "tema",
                                 "ressalvas")} for t in M],
        "U": [{k: t[k] for k in ("slug", "lado", "tema_origem", "tema")}
              for t in sorted(U, key=lambda t: (t["slug"], t["tema_origem"]))],
        "analisaveis": [[t["slug"], t["lado"], t["tema_origem"]] for t in temas],
        "filmes_com_replica": com_replica,
        "ordem_dos_bracos": ordem,
        "prompt_sha256": {"controle": _sha(C.PROMPT_CONDICOES.encode()),
                          "variante": _sha(C.PROMPT_CONDICOES_VARIANTE.encode())},
    }
    dados = _escrever(PREREG, reg)
    print(f"filmes {len(filmes)} · pedidos {reg['n_temas_pedidos']} · "
          f"analisáveis {len(temas)} · M {len(M)} · U {len(U)} · "
          f"excluídos {len(excluidos)} · filmes com réplica {len(com_replica)} · "
          f"gerações {len(ordem) * 2}")
    print(f"sha256 {PREREG.name}: {_sha(dados)}")


def _prereg() -> dict:
    return json.loads(PREREG.read_text(encoding="utf-8"))


# ===========================================================================
# GERAÇÃO
# ===========================================================================

_TRAVA = threading.Lock()


def _gerador_instrumentado(modelo: str, crus: list):
    """Espelho de `condicoes._gerar_real` que também guarda os contadores crus."""
    from espectro24 import synthesize as S
    from espectro24.config import PROSA_MAX_TOKENS

    def gerar(system, user):
        t0 = time.time()
        resp = S.resposta(system, user, modelo, provider="gemini",
                          max_tokens=PROSA_MAX_TOKENS, json_mode=True)
        um = getattr(resp, "usage_metadata", None)
        crus.append({k: int(getattr(um, k, 0) or 0) for k in (
            "prompt_token_count", "candidates_token_count",
            "thoughts_token_count", "cached_content_token_count",
            "total_token_count")})
        return (resp.text or ""), S.uso(resp, "gemini"), time.time() - t0
    return gerar


def _arquivo(slug: str, braco: str, rep: int) -> Path:
    return GER / f"{slug}__{braco}__r{rep}.json"


def _gerar_filme(slug: str, unidades: list[tuple[int, str]], modelo: str) -> None:
    from espectro24.config import BEST_OF_N

    d = _doc(slug)
    for rep, braco in unidades:
        destino = _arquivo(slug, braco, rep)
        if destino.exists():
            continue
        crus: list = []
        inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            bloco = C.gerar(d, n=BEST_OF_N, provider="gemini", model=modelo,
                            gerar=_gerador_instrumentado(modelo, crus),
                            variante=BRACOS[braco])
        except Exception as e:  # falha isolada: registra e segue; rerodar retoma
            with _TRAVA:
                with (GER / "_erros.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"slug": slug, "braco": braco, "rep": rep,
                                        "erro": f"{type(e).__name__}: {e}"},
                                       ensure_ascii=False) + "\n")
            print(f"  ERRO {slug} {braco} r{rep}: {type(e).__name__}", flush=True)
            continue
        _escrever(destino, {"slug": slug, "braco": braco, "replica": rep,
                            "inicio": inicio,
                            "fim": datetime.now(timezone.utc).isoformat(
                                timespec="seconds"),
                            "uso_cru": crus, "condicoes": bloco})
        with _TRAVA:
            print(f"  ok {slug:40} r{rep} {braco:9} chamadas {len(crus)}",
                  flush=True)


def gerar(workers: int) -> None:
    from dotenv import load_dotenv
    from espectro24 import synthesize as S

    load_dotenv(RAIZ / ".env")
    if S.provider_do_estagio(C.ESTAGIO, None) != "gemini":
        raise SystemExit("o estágio de condições não está no Gemini")
    modelo = S.modelo_do_estagio(C.ESTAGIO, "gemini")
    reg = _prereg()
    por_filme: dict[str, list] = {}
    for chave, ordem in reg["ordem_dos_bracos"].items():
        slug, rep = chave.split("#r")
        por_filme.setdefault(slug, []).extend((int(rep), b) for b in ordem)
    for u in por_filme.values():
        u.sort(key=lambda x: x[0])
    print(f"modelo {modelo} · {sum(map(len, por_filme.values()))} gerações · "
          f"{len(por_filme)} filmes · {workers} em paralelo", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda s: _gerar_filme(s, por_filme[s], modelo),
                    sorted(por_filme)))
    faltam = [f"{s} {b} r{r}" for s, u in por_filme.items() for r, b in u
              if not _arquivo(s, b, r).exists()]
    print(f"faltam {len(faltam)}: {faltam}")


# ===========================================================================
# LEITURA DAS GERAÇÕES
# ===========================================================================

def _geracoes() -> dict[tuple[str, str, int], dict]:
    saida = {}
    for p in sorted(GER.glob("*__*__r*.json")):
        g = json.loads(p.read_text(encoding="utf-8"))
        saida[(g["slug"], g["braco"], g["replica"])] = g
    return saida


def situacao(bloco: dict, lado: str, tid: str) -> str:
    """O destino do tema pedido: escrita · descartada · recusa · par_desfeito
    · silencio. Exatamente um."""
    if any(c.get("tema_origem") == tid for c in bloco.get("par_desfeito") or []):
        return "par_desfeito"
    if any(c.get("tema_origem") == tid for c in bloco.get(lado) or []):
        return "escrita"
    if any(r.get("tema_origem") == tid
           for r in bloco.get("sem_condicao_publicavel") or []):
        return "recusa"
    if any(c.get("tema_origem") == tid and c.get("lado") == lado
           for c in bloco.get("descartadas") or []):
        return "descartada"
    return "silencio"


def _texto_escrito(bloco: dict, lado: str, tid: str) -> str | None:
    for c in bloco.get(lado) or []:
        if c.get("tema_origem") == tid:
            return c.get("texto")
    return None


def _plano(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


# Proxy de "ressalva carregada" — VISTO, não medido: conector de ressalva OU
# verbo/locução de concessão. O rótulo que conta é o código R2 do dono.
_CARREGA = [r"(?<![a-z])" + re.escape(w) + r"(?![a-z])" for w in (
    "embora", "apesar", "mas", "porem", "contudo", "no entanto", "ainda que",
    "entretanto", "mesmo com", "mesmo que", "mesmo quando", "mesmo diante",
    "a despeito", "em troca de", "em favor de", "ainda assim", "sem se importar")]
_CARREGA += [r"(?<![a-z])" + p for p in ("aceit", "toler", "relev", "compens",
                                         "perdo", "suport")]


def carrega_ressalva(texto: str) -> bool:
    plano = _plano(texto)
    return any(re.search(p, plano) for p in _CARREGA)


def _mcnemar(b: int, c: int) -> float:
    from scipy.stats import binomtest
    return 1.0 if b + c == 0 else binomtest(b, b + c, 0.5).pvalue


# ===========================================================================
# MEDIÇÃO AUTOMÁTICA (sem rotulagem) — SELADA: revela o efeito por braço
# ===========================================================================

def medir() -> None:
    reg = _prereg()
    ger = _geracoes()
    esperadas = [(k.split("#r")[0], b, int(k.split("#r")[1]))
                 for k, ordem in reg["ordem_dos_bracos"].items() for b in ordem]
    faltam = [e for e in esperadas if e not in ger]

    # --- custo real
    tot = {"prompt": 0, "visivel": 0, "raciocinio": 0, "cache": 0, "chamadas": 0}
    uso_gravado = {"prompt": 0, "saida": 0}
    por_braco = {b: {"prompt": 0, "visivel": 0, "raciocinio": 0, "chamadas": 0,
                     "geracoes": 0} for b in BRACOS}
    for (s, b, r), g in ger.items():
        por_braco[b]["geracoes"] += 1
        for u in g["uso_cru"]:
            for alvo in (tot, por_braco[b]):
                alvo["prompt"] += u["prompt_token_count"]
                alvo["visivel"] += u["candidates_token_count"]
                alvo["raciocinio"] += u["thoughts_token_count"]
                alvo["chamadas"] += 1
            tot["cache"] += u["cached_content_token_count"]
        ug = g["condicoes"]["uso"]
        uso_gravado["prompt"] += ug["prompt_tokens"]
        uso_gravado["saida"] += ug["completion_tokens"]

    def custo(x):
        return (x["prompt"] * PRECO_ENTRADA
                + (x["visivel"] + x["raciocinio"]) * PRECO_SAIDA) / 1e6
    custo_real = custo(tot)
    custo_uso = (uso_gravado["prompt"] * PRECO_ENTRADA
                 + uso_gravado["saida"] * PRECO_SAIDA) / 1e6
    n_ger = len(ger)

    # --- situação por tema analisável, réplica 1
    anal = [tuple(x) for x in reg["analisaveis"]]
    sit = {b: {} for b in BRACOS}
    for s, lado, tid in anal:
        for b in BRACOS:
            g = ger.get((s, b, 1))
            sit[b][(s, tid)] = situacao(g["condicoes"], lado, tid) if g else None
    completos = [(s, lado, tid) for s, lado, tid in anal
                 if all(sit[b][(s, tid)] for b in BRACOS)]
    cats = ("escrita", "descartada", "recusa", "par_desfeito", "silencio")
    dist = {b: {c: sum(1 for s, _, t in completos if sit[b][(s, t)] == c)
                for c in cats} for b in BRACOS}
    rc = sum(1 for s, _, t in completos if sit["controle"][(s, t)] == "recusa"
             and sit["variante"][(s, t)] != "recusa")
    rv = sum(1 for s, _, t in completos if sit["variante"][(s, t)] == "recusa"
             and sit["controle"][(s, t)] != "recusa")
    regras = {b: {} for b in BRACOS}
    for (s, b, r), g in ger.items():
        if r != 1:
            continue
        for x in g["condicoes"].get("sem_condicao_publicavel") or []:
            if [s, x["lado"], x["tema_origem"]] in reg["analisaveis"]:
                regras[b][x["regra"]] = regras[b].get(x["regra"], 0) + 1

    # --- M: ressalva carregada (proxy), por braço e réplica
    linhas_m = []
    for b in BRACOS:
        for r in (1, 2):
            n = esc = carr = rec = 0
            for t in reg["M"]:
                g = ger.get((t["slug"], b, r))
                if not g:
                    continue
                n += 1
                st = situacao(g["condicoes"], t["lado"], t["tema_origem"])
                if st == "escrita":
                    esc += 1
                    carr += carrega_ressalva(
                        _texto_escrito(g["condicoes"], t["lado"], t["tema_origem"]))
                rec += st == "recusa"
            linhas_m.append((b, r, n, esc, carr, rec))

    L = [f"# Medições automáticas por braço — SELADO",
         "",
         "**Não abra antes de terminar a rotulagem, se for você quem rotula.** "
         "Estes números mostram o tamanho do efeito em cada braço, e quem os "
         "lê passa a saber que traço denuncia o variante (mais recusa, mais "
         "\"apesar de\") — o mesmo vazamento do motivo da recusa, que já está "
         "escondido.",
         "",
         f"Gerado em {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
         f"· gerações {n_ger} de {len(esperadas)}"
         + (f" · **FALTAM {len(faltam)}: {faltam}**" if faltam else ""),
         "",
         "## Custo real — MEDIDO (contadores crus; raciocínio cobrado como saída)",
         "",
         "| | chamadas | entrada | saída visível | raciocínio | US$ |",
         "|---|---:|---:|---:|---:|---:|"]
    for b, x in por_braco.items():
        L.append(f"| {b} ({x['geracoes']} gerações) | {x['chamadas']} | "
                 f"{x['prompt']:,} | {x['visivel']:,} | {x['raciocinio']:,} | "
                 f"{custo(x):.2f} |")
    L += [f"| **total** | {tot['chamadas']} | {tot['prompt']:,} | "
          f"{tot['visivel']:,} | {tot['raciocinio']:,} | **{custo_real:.2f}** |",
          "",
          f"- por geração: **US$ {custo_real / max(n_ger, 1):.4f}** "
          f"(projeção de 0,025 no desenho)",
          f"- o que o `uso` gravado permite calcular: US$ {custo_uso:.2f} → "
          f"subestima **{custo_real / custo_uso:.2f}×**" if custo_uso else "",
          f"- tokens em cache implícito (não descontados acima): {tot['cache']:,}",
          f"- depois de 1/1/2027 (preço ×2): US$ {2 * custo_real:.2f}",
          "",
          f"## Situação dos temas analisáveis — réplica 1, {len(completos)} "
          f"pares completos de {len(anal)}",
          "",
          "| braço | " + " | ".join(cats) + " |",
          "|---|" + "---:|" * len(cats)]
    for b in BRACOS:
        n = len(completos) or 1
        L.append(f"| {b} | " + " | ".join(
            f"{dist[b][c]} ({100 * dist[b][c] / n:.1f}%)" for c in cats) + " |")
    L += ["",
          f"**G1 — recusa pareada:** recusou só no controle {rc}, só no variante "
          f"{rv}; McNemar exato bilateral p = {_mcnemar(rc, rv):.4f}. "
          f"Guarda PIORA se o variante recusar mais com p < 0,05.",
          "",
          "Recusas por regra: " + " · ".join(
              f"{b}: " + (", ".join(f"{k} {v}" for k, v in sorted(regras[b].items()))
                          or "nenhuma") for b in BRACOS),
          "",
          f"## Estrato M ({len(reg['M'])} temas) — ressalva carregada, PROXY",
          "",
          "Proxy léxico (VISTO, sem precisão medida): a condição escrita tem "
          "conector de ressalva ou verbo/locução de concessão. O desfecho "
          "medido é o código R2 do rotulador.",
          "",
          "| braço | réplica | temas | escritas | carregam (proxy) | recusas |",
          "|---|---:|---:|---:|---:|---:|"]
    for b, r, n, esc, carr, rec in linhas_m:
        L.append(f"| {b} | {r} | {n} | {esc} | {carr} "
                 f"({100 * carr / esc:.0f}% das escritas) | {rec} |"
                 if esc else f"| {b} | {r} | {n} | 0 | — | {rec} |")
    (SELO / "medicoes_por_braco.md").parent.mkdir(parents=True, exist_ok=True)
    (SELO / "medicoes_por_braco.md").write_text("\n".join(L) + "\n",
                                               encoding="utf-8")
    # Resumo que NÃO separa braço — pode ser lido antes da rotulagem.
    geral = {"geracoes": n_ger, "esperadas": len(esperadas), "faltam": faltam,
             "chamadas": tot["chamadas"], "custo_real_usd": round(custo_real, 4),
             "custo_por_geracao_usd": round(custo_real / max(n_ger, 1), 5),
             "custo_pelo_uso_gravado_usd": round(custo_uso, 4),
             "fator_subestimacao_uso": round(custo_real / custo_uso, 2) if custo_uso else None,
             "tokens": tot,
             "recusas_somando_os_dois_bracos_r1": sum(dist[b]["recusa"] for b in BRACOS),
             "pares_completos_r1": len(completos),
             "G1_piora": bool(rv > rc and _mcnemar(rc, rv) < 0.05)}
    _escrever(DIR / "medicoes_gerais.json", geral)
    print(json.dumps(geral, ensure_ascii=False, indent=1))


# ===========================================================================
# RELATÓRIO CEGO
# ===========================================================================

def _chave_cega(it: dict) -> tuple:
    tipo = ("recusa" if it.get("recusa") else
            "par_desfeito" if it.get("par_desfeito") else
            "descartada" if it["flags_validador"] else "coluna")
    regra = (it.get("recusa") or {}).get("regra") or ""
    return (it["slug"], it["lado"], it["tema_origem"], tipo,
            " ".join(_plano(it["texto"]).split()), regra,
            tuple(sorted(it["flags_validador"])))


OCULTO = ("*(oculto até o fim da rotulagem — julgue se existia uma condição "
          "honesta, sem o motivo do modelo)*")


def _tema(it: dict) -> tuple:
    return (it["slug"], it["tema_origem"])


def _viavel(cont: dict, n: int, ant) -> bool:
    """Existe arranjo de `n` itens sem dois do mesmo tema lado a lado, com o
    primeiro diferente de `ant`?"""
    return all(c <= (n + 1) // 2 and (t != ant or c <= n // 2)
               for t, c in cont.items())


def _sem_vizinho_do_mesmo_tema(resto: list[dict], anterior) -> list[dict]:
    """A ordem do hash, desviada só o necessário para que as versões de um
    mesmo tema nunca fiquem lado a lado — nem na virada de seção. Guloso: o
    próximo é o primeiro, na ordem do hash, que ainda deixa o restante
    arrumável; quando nenhum deixa, o menos pior."""
    from collections import Counter

    resto = list(resto)
    saida = []
    ant = _tema(anterior) if anterior else None
    while resto:
        cont = Counter(_tema(it) for it in resto)
        escolha = None
        for j, it in enumerate(resto):
            t = _tema(it)
            if t == ant:
                continue
            cont[t] -= 1
            ok = _viavel(cont, len(resto) - 1, t)
            cont[t] += 1
            if ok:
                escolha = j
                break
        if escolha is None:
            escolha = next((j for j, it in enumerate(resto)
                            if _tema(it) != ant), 0)
        saida.append(resto.pop(escolha))
        ant = _tema(saida[-1])
    return saida


def relatorio() -> None:
    import relatorio_revisao_condicoes as R

    reg = _prereg()
    ger = _geracoes()
    esperadas = [(k.split("#r")[0], b, int(k.split("#r")[1]))
                 for k, ordem in reg["ordem_dos_bracos"].items() for b in ordem]
    faltam = [e for e in esperadas if e not in ger]
    if faltam:
        raise SystemExit(f"gerações faltando — rode `gerar` de novo: {faltam}")
    m = {(t["slug"], t["tema_origem"]): t for t in reg["M"]}
    u = {(t["slug"], t["tema_origem"]) for t in reg["U"]}

    cegos: dict[tuple, dict] = {}
    for (slug, braco, rep), g in sorted(ger.items()):
        for it in R.montar_itens([(slug, g["condicoes"])]):
            chave_tema = (slug, it["tema_origem"])
            estrato = ("M" if chave_tema in m else
                       "U" if chave_tema in u and rep == 1 else None)
            if estrato is None:
                continue
            if it.get("recusa"):
                it["recusa"]["motivo"] = OCULTO
            it["categorias"] = R.categorizar(it)
            it["categoria"] = (it["categorias"][0][0] if it["categorias"]
                               else R.SEM_CATEGORIA)
            it["estrato"] = estrato
            it["ressalvas"] = m[chave_tema]["ressalvas"] if estrato == "M" else []
            k = _chave_cega(it)
            if k not in cegos:
                cegos[k] = {**it, "origens": []}
            cegos[k]["origens"].append({"braco": braco, "replica": rep})

    ordem_cat = [c["codigo"] for c in R.CATEGORIAS] + [R.SEM_CATEGORIA]
    partes = []
    for estrato in ("M", "U"):
        itens = [it for it in cegos.values() if it["estrato"] == estrato]
        for it in itens:
            it["_h"] = _sha(("|".join(map(str, _chave_cega(it))) + SEMENTE).encode())
        seq = []
        for cod in ordem_cat:
            resto = sorted((it for it in itens if it["categoria"] == cod),
                           key=lambda it: it["_h"])
            seq += _sem_vizinho_do_mesmo_tema(resto, seq[-1] if seq else None)
        partes.append((estrato, seq))

    n = 0
    mapa = {}
    for _, seq in partes:
        for it in seq:
            n += 1
            it["numero"] = f"X{n:03d}"
            mapa[it["numero"]] = {"slug": it["slug"], "lado": it["lado"],
                                  "tema_origem": it["tema_origem"],
                                  "estrato": it["estrato"],
                                  "tipo": _chave_cega(it)[3],
                                  "origens": it["origens"]}
    dados_mapa = _escrever(SELO / "mapa.json",
                           {"semente": SEMENTE, "itens": mapa})
    h_mapa = _sha(dados_mapa)

    for estrato, seq in partes:
        nome = ("parte-1-M" if estrato == "M" else "parte-2-U")
        _escrever_relatorio(R, seq, estrato, nome, h_mapa, reg)
    print(f"{n} itens cegos · M {len(partes[0][1])} · U {len(partes[1][1])} · "
          f"sha256 mapa {h_mapa}")


def _escrever_relatorio(R, seq, estrato, nome, h_mapa, reg) -> None:
    ordem_cat = [c["codigo"] for c in R.CATEGORIAS] + [R.SEM_CATEGORIA]
    primeiro, ultimo = seq[0]["numero"], seq[-1]["numero"]
    L = [f"# Rotulagem cega — experimento de briefing — {nome}",
         "",
         f"**sha256 do mapeamento de cegamento:** `{h_mapa}`  ",
         f"(o arquivo `NAO_ABRIR_ANTES_DA_ROTULAGEM/mapa.json` tem de ter este "
         f"hash quando for aberto; se não tiver, os rótulos não valem)",
         "",
         f"**Itens:** {primeiro}–{ultimo} ({len(seq)}) · "
         f"{len({(i['slug'], i['tema_origem']) for i in seq})} temas · "
         f"sessão {'1 de 2' if estrato == 'M' else '2 de 2'}",
         "",
         "## 0. O que muda neste lote em relação ao protocolo de sempre",
         "",
         "- **Cada tema aparece mais de uma vez**, em versões escritas "
         "independentemente"
         + (" (até quatro)" if estrato == "M" else " (até duas)")
         + ". **Julgue cada versão sozinha**, contra as regras, como se fosse "
           "a única. Não compare versões entre si. Versões com texto idêntico "
           "aparecem uma vez só.",
         "- **Nada neste arquivo diz de onde veio cada versão.** A numeração "
           "(`X…`) é embaralhada e estável; o mapeamento está selado.",
         "- **O motivo das recusas está oculto.** Aparece só a REGRA citada. "
           "A pergunta continua a mesma: existia uma condição honesta?",
         "- **Versões de um mesmo tema não ficam lado a lado**, exceto onde "
           "uma seção tem só (ou quase só) versões daquele tema e não há outro "
           "item para intercalar. Aí elas vêm em sequência: julgue cada uma "
           "sozinha mesmo assim.",
         ] + ([
         "- **Todos os temas desta parte têm ressalva na própria paráfrase**, "
           "citada no item (\"ressalva no próprio tema\"). O código a marca em "
           "todo tema com conector de ressalva; ela vale igualmente para "
           "todas as versões do tema."] if estrato == "M" else [
         "- **Os temas desta parte são uma amostra sorteada** dos que não têm "
           "conector de ressalva na paráfrase."]) + [
         "- **DUVIDOSO leva o código da regra — obrigatório neste lote.** Um "
           "de: `R1`, `R2`, `R6`, ou o número de outra regra da seção 1.4 "
           "(conta como \"outro\"). Mais de uma: separe com barra (`R1/R2`).",
         "",
         "**Formato da resposta (substitui o 1.6 abaixo):**",
         "",
         "    CONFIRMO: X001, X002, X004–X009",
         "    DUVIDOSO: X003 — R2 — a condição tira a ressalva sobre o ritmo",
         "    DUVIDOSO: X010 — R1 — \"contundente\" não está na paráfrase",
         "",
         R.regras(),
         "## 2. Resumo por categoria", "",
         "| categoria | itens |", "|---|---:|"]
    for cod in ordem_cat:
        k = sum(1 for it in seq if it["categoria"] == cod)
        tit = ("Sem categoria de risco" if cod == R.SEM_CATEGORIA
               else R._POR_CODIGO[cod]["titulo"])
        L.append(f"| {tit} | {k} |")
    L += ["", "## 3. Itens, por categoria de risco", ""]
    for i, cod in enumerate(ordem_cat, 1):
        sec = [it for it in seq if it["categoria"] == cod]
        if not sec:
            continue
        if cod == R.SEM_CATEGORIA:
            L += [f"### 3.{i} Sem categoria de risco ({len(sec)} itens)", "",
                  "Nenhum detector disparou. **Isso não quer dizer que estão "
                  "livres de risco.** Leia contra as regras R1–R13.", ""]
        else:
            c = R._POR_CODIGO[cod]
            L += [f"### 3.{i} {c['titulo']} ({len(sec)} itens)", "",
                  f"*Detector:* {c['detector']}.", "",
                  f"*Pergunta desta seção:* {c['pergunta']}", ""]
        for it in sec:
            md = R._item_md(it)
            if it["ressalvas"]:
                md = md.replace(
                    "- **rótulo de força",
                    "- **ressalva no próprio tema (marcada pelo código):** "
                    + "; ".join(f"«{t}»" for t in it["ressalvas"])
                    + "\n- **rótulo de força", 1)
            L += [md, ""]
    (DIR / f"ROTULAGEM_CEGA_{nome}.md").write_text(
        "\n".join(L).rstrip() + "\n", encoding="utf-8")


# ===========================================================================

def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preregistro")
    g = sub.add_parser("gerar")
    g.add_argument("--workers", type=int, default=4)
    sub.add_parser("medir")
    sub.add_parser("relatorio")
    a = ap.parse_args()
    if a.cmd == "preregistro":
        preregistro()
    elif a.cmd == "gerar":
        gerar(a.workers)
    elif a.cmd == "medir":
        medir()
    else:
        relatorio()


if __name__ == "__main__":
    main()
