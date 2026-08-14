"""[Entregas 2-4] `impacto_emocional` apertado — a saturação é do corpus ou da definição?

**A hipótese.** Sob `A_regra`, `impacto_emocional` aparece em 75,5% do corpus.
A Entrega 1 da sessão anterior concluiu que nenhuma reponderação do lift
(normalizado, log-odds) recupera discriminação — mas ela reponderava
CONTAGENS, não corrigia quais reviews entram na contagem. Se a saturação for
artefato da DEFINIÇÃO (o eixo engolindo veredicto seco), apertá-la de-satura
o eixo e devolve espaço de lift.

Evidência a favor, já medida: o eixo satura (2º bucket ≥70%) em 30 de 35
filmes, mas nos 5 restantes é o MELHOR discriminador do corpus — lift médio
0,146 contra 0,072 nos saturados. Um eixo que discrimina bem quando não
satura é um eixo bom sendo estragado por marcação excessiva.

**O que a variante muda — e por que precisa mudar DUAS coisas, não uma.**

A tarefa pede alterar "APENAS a definição de `impacto_emocional`". Só que a
definição desse eixo está espalhada em DOIS lugares do prompt de produção:

  (a) a linha `- impacto_emocional: ...` no bloco de eixos;
  (b) os EXEMPLOS da regra 2, que dizem literalmente
      `"chorei", "não gostei", "odiei", ... são impacto_emocional`.

Apertar só (a) deixaria o prompt se contradizendo: a definição diria "não
marque veredicto seco" e a regra 2, duas telas abaixo, mandaria marcar
`"não gostei"` e `"odiei"` — que são exatamente veredicto seco. O modelo
resolveria a contradição de forma imprevisível e a medição não significaria
nada. Então (b) muda junto, e a mudança é cirúrgica: os dois veredictos
secos saem da lista de exemplos POSITIVOS e entram na lista de "elogio sem
eixo", que a regra 2 já mantinha para o polo positivo (`"amei"`,
`"obra-prima"`). É a mesma assimetria que o gabarito humano tinha, e que
`REGRA_ANOTACAO.md` corrigiu — o prompt a tinha também, no espelho.

**O que NÃO muda, e é o ponto crítico da tarefa:** a estrutura das 7 regras
de `A_regra`, as outras 9 definições de eixo, e em especial a regra 6
(`review curta menciona POUCOS eixos, não ZERO`) e a regra 3 (`livre` por
ASSUNTO) — que são as que compraram o ganho de recall em review curta
(`fracao_livre` ≤200 chars: 9,76% → 2,58%). A regra 2 mantém a cláusula
`um efeito DECLARADO é eixo mesmo dito em três palavras`, com os exemplos
que são efeito de verdade (`"chorei"`, `"me deu sono"`, `"passei mal"`,
`"ri alto"`).

**A distinção que decide se a variante é boa ou ruim.** Uma review que diz
só "não gostei" genuinamente NÃO tem conteúdo temático — cair em `livre` ou
vazio ali é recall CORRETO, não perda. O que seria regressão é uma review
com eixo temático real ("os personagens são tão tontos" →
`roteiro_estrutura`) passar a cair em `livre`. `cmd_comparar` mede as duas
coisas separadas, e é essa separação que valida ou reprova a variante.

Uso:
    python scripts/variante_impacto_estrito.py passes    # 3 passadas x 100 reviews (LLM, centavos)
    python scripts/variante_impacto_estrito.py comparar  # métricas vs A_regra, contra o gabarito CORRIGIDO
    python scripts/variante_impacto_estrito.py projetar  # Entrega 4 — projeção no corpus (sem LLM)

Saídas em `resultado/auditoria-acuracia/impacto-estrito/`.
"""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(RAIZ / "scripts"))

import auditoria_acuracia as aa  # noqa: E402
from classificar_10 import (  # noqa: E402
    EIXOS,
    MODELO,
    SYSTEM as SYSTEM_A_REGRA,
    _normalizar,
    recuperar_eixo,
)
from espectro24.previsao_frequencia import fator_pareado  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
)

SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "impacto-estrito"
ARQ_COMPARACAO = SAIDA / "comparacao.json"
ARQ_PROJECAO = SAIDA / "projecao.json"

CONCORRENCIA = 8
MAX_TENTATIVAS = 3
N_PASSES = 3


# ===========================================================================
# A variante — duas substituições cirúrgicas sobre o SYSTEM de produção
# ===========================================================================

_DEF_ANTIGA = (
    "- impacto_emocional: o efeito que o filme causou em quem escreveu, ou na "
    "plateia da sessão — chorou, riu, se arrepiou, sentiu nojo, saiu abalado, "
    "se identificou, teve pesadelo, desistiu no meio de tédio, ficou "
    "indiferente. Inclui reação FÍSICA e VISCERAL e a reação da PLATEIA."
)

_DEF_NOVA = (
    "- impacto_emocional: o EFEITO que o filme causou em quem escreveu, ou na "
    "plateia da sessão — chorou, riu alto, se arrepiou, sentiu nojo, saiu "
    "abalado, passou mal, dormiu, pausou de tédio, teve pesadelo, se "
    "identificou, saiu pensando naquilo. Inclui reação FÍSICA e VISCERAL e a "
    "reação da PLATEIA. NÃO é impacto_emocional o veredicto seco de aprovação "
    "ou reprovação — \"gostei\", \"não gostei\", \"é ruim\", \"é ótimo\", "
    "\"odiei\", \"amei\", \"mid\", \"perda de tempo\" sozinhos são AVALIAÇÃO, "
    "não efeito, tanto no polo positivo quanto no negativo. Também NÃO é "
    "impacto_emocional o que o filme EVOCA ou DEIXA DE ENTREGAR (\"clima de "
    "angústia\", \"faltou emoção\", \"não dá medo\", \"sem intensidade\") — "
    "isso é tom_atmosfera ou roteiro_estrutura. A pergunta é sempre: a review "
    "diz o que o filme FEZ com quem assistiu, ou só diz como o filme É?"
)

_REGRA2_ANTIGA = (
    "2. Só atribua um eixo se a review disser algo sobre ele. Nota alta ou "
    "entusiasmo genérico SEM descrever efeito nenhum (\"obra-prima\", \"amei\", "
    "\"5 estrelas\", \"peak cinema\") NÃO é impacto_emocional nem nenhum outro "
    "eixo — é elogio sem eixo. Mas um efeito DECLARADO é eixo mesmo dito em "
    "três palavras: \"chorei\", \"não gostei\", \"odiei\", \"me deu sono\", "
    "\"passei mal\", \"ri alto\" são impacto_emocional."
)

# Mesma estrutura e mesma função da regra 2 de A_regra — só os EXEMPLOS
# mudam de lado, para o prompt não se contradizer com a definição nova.
_REGRA2_NOVA = (
    "2. Só atribua um eixo se a review disser algo sobre ele. Veredicto seco "
    "SEM descrever efeito nenhum (\"obra-prima\", \"amei\", \"5 estrelas\", "
    "\"peak cinema\", \"não gostei\", \"odiei\", \"é ruim\", \"perda de "
    "tempo\") NÃO é impacto_emocional nem nenhum outro eixo — é avaliação sem "
    "eixo, valha ela para elogiar ou para xingar. Mas um efeito DECLARADO é "
    "eixo mesmo dito em três palavras: \"chorei\", \"me deu sono\", \"passei "
    "mal\", \"ri alto\", \"dormi no meio\" são impacto_emocional."
)


def _montar_variante() -> str:
    """Aplica as duas substituições, exigindo casamento exato de ambas.

    Falhar alto aqui é deliberado: se o prompt de produção mudar e um dos
    dois trechos deixar de casar, a variante silenciosamente mediria outra
    coisa (ou o mesmo prompt duas vezes).
    """
    system = SYSTEM_A_REGRA
    for antigo, novo, nome in ((_DEF_ANTIGA, _DEF_NOVA, "definição do eixo"),
                               (_REGRA2_ANTIGA, _REGRA2_NOVA, "regra 2")):
        if system.count(antigo) != 1:
            raise SystemExit(
                f"variante desatualizada: {nome} não casa exatamente 1× no "
                f"SYSTEM de produção (casou {system.count(antigo)}×). O prompt "
                f"mudou — reveja este script antes de rodar.")
        system = system.replace(antigo, novo)
    return system


SYSTEM_ESTRITO = _montar_variante()

VARIANTES = {"A_regra": SYSTEM_A_REGRA, "impacto_estrito": SYSTEM_ESTRITO}
A_RODAR = ("impacto_estrito",)   # A_regra já está medida em disco


# ===========================================================================
# Passadas — mesma mecânica de `variantes_prompt_curtas`
# ===========================================================================

def _reviews() -> list[dict]:
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    amostra = json.loads(
        (RAIZ / "resultado" / "votacao-3" / "amostra.json").read_text(encoding="utf-8"))
    por_id = {r["id"]: r for r in amostra["reviews"]}
    return [{**r, "texto": por_id[r["id"]]["texto"]} for r in idx["reviews"]]


def _arq_passe(variante: str, n: int) -> Path:
    return SAIDA / f"{variante}_passe_{n}.jsonl"


def rodar_passe(variante: str, n_passe: int, reviews: list[dict]) -> None:
    arq = _arq_passe(variante, n_passe)
    feitos = set()
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok"):
                    feitos.add(r["id"])
    pendentes = [r for r in reviews if r["id"] not in feitos]
    print(f"  {variante} passe {n_passe}: {len(feitos)} feitas · "
          f"{len(pendentes)} pendentes")
    if not pendentes:
        return

    system = VARIANTES[variante]
    client = deepseek_client()
    lock, contador, t0 = Lock(), [0], time.time()
    saida = arq.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        erro = ""
        for tentativa in range(MAX_TENTATIVAS):
            try:
                resp = deepseek_resposta(
                    system,
                    f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
                    f"{review['texto']}",
                    MODELO, max_tokens=300, json_mode=True, client=client)
                data = json.loads(resp.choices[0].message.content)
                eixos, livres, invalidos = _normalizar(data)
                registro = {"ok": True, "variante": variante, "passe": n_passe,
                            "id": review["id"], "bucket": review["bucket"],
                            "nivel": review["nivel"], "n_chars": review["n_chars"],
                            "eixos": eixos, "temas_livres": livres,
                            "eixos_invalidos": invalidos, "uso": deepseek_uso(resp)}
                break
            except Exception as e:  # noqa: BLE001
                erro = f"{type(e).__name__}: {e}"
                time.sleep(2 * (tentativa + 1))
        else:
            registro = {"ok": False, "variante": variante, "passe": n_passe,
                        "id": review["id"], "erro": erro}
        with lock:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
            saida.flush()
            contador[0] += 1
            if contador[0] % 25 == 0 or contador[0] == len(pendentes):
                print(f"    {contador[0]}/{len(pendentes)} · "
                      f"{time.time() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as ex:
        list(ex.map(tarefa, pendentes))
    saida.close()


def cmd_passes() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    SAIDA.mkdir(parents=True, exist_ok=True)
    reviews = _reviews()
    print(f"{len(reviews)} reviews · {len(A_RODAR)} variante(s) · {N_PASSES} passadas")
    for v in A_RODAR:
        for n in range(1, N_PASSES + 1):
            rodar_passe(v, n, reviews)


# ===========================================================================
# Consenso + métricas
# ===========================================================================

def _ler_passe(variante: str, n: int, base: Path | None = None) -> dict[str, list[str]]:
    arq = (base or SAIDA) / f"{variante}_passe_{n}.jsonl"
    por_id: dict[str, list[str]] = {}
    if not arq.exists():
        return por_id
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok"):
            continue
        eixos = list(r["eixos"])
        for bruto in r.get("eixos_invalidos", []):
            alvo = recuperar_eixo(bruto)
            if alvo and alvo not in eixos:
                eixos.append(alvo)
        por_id[r["id"]] = sorted(set(eixos))
    return por_id


def consenso(variante: str, base: Path | None = None) -> dict[str, dict]:
    passes = [_ler_passe(variante, n, base) for n in range(1, N_PASSES + 1)]
    ids = set(passes[0]) & set(passes[1]) & set(passes[2])
    saida = {}
    for rid in sorted(ids):
        por_passe = [p[rid] for p in passes]
        votos = Counter(e for eixos in por_passe for e in eixos)
        finais = sorted(e for e, v in votos.items() if v >= 2)
        conf = ("vazio" if not finais
                else "unanime" if all(votos[e] == 3 for e in finais)
                else "maioria")
        saida[rid] = {"eixos": finais, "votos": dict(votos), "confianca": conf,
                      "eixos_por_passe": por_passe}
    return saida


def _micro(bloco: dict) -> dict:
    tp = sum(v["tp"] for v in bloco.values())
    fp = sum(v["fp"] for v in bloco.values())
    fn = sum(v["fn"] for v in bloco.values())
    return {"tp": tp, "fp": fp, "fn": fn,
            "precisao": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None}


def _metricas(anotacoes: dict, gabarito: dict) -> dict:
    tmp = SAIDA / "_gab_tmp.json"
    tmp.write_text(json.dumps(gabarito, ensure_ascii=False), encoding="utf-8")
    original = aa.ARQ_GABARITO
    try:
        aa.ARQ_GABARITO = tmp
        return aa.calcular_metricas(anotacoes)
    finally:
        aa.ARQ_GABARITO = original
        tmp.unlink(missing_ok=True)


def _fracao_livre_por_faixa(gabarito: dict, meta: dict, anotacoes: dict) -> dict:
    """`fracao_livre` por faixa, separando o caso que IMPORTA.

    `com_eixo_tematico` = reviews em que o HUMANO viu ao menos um eixo da
    taxonomia. Cair em `livre`/vazio nessas é REGRESSÃO do ganho de A_regra.
    `sem_eixo_tematico` = o humano não viu eixo nenhum; cair em `livre` ali é
    acerto, não perda. Misturar as duas foi o que tornaria a comparação
    enganosa.
    """
    def faixa(n):
        return ("<=200" if n <= 200 else "201-400" if n <= 400
                else "401-800" if n <= 800 else "801+")

    saida = defaultdict(lambda: {"com_eixo_tematico": [0, 0],
                                 "sem_eixo_tematico": [0, 0]})
    for rid, g in gabarito.items():
        f = faixa(meta[rid]["n_chars"])
        humano_tem = bool(set(anotacoes[rid]["eixos"]) - {"livre"})
        chave = "com_eixo_tematico" if humano_tem else "sem_eixo_tematico"
        saida[f][chave][1] += 1
        if not (set(g["eixos"]) - {"livre"}):
            saida[f][chave][0] += 1
    return {f: {k: {"sem_eixo_do_modelo": v[0], "n": v[1],
                    "fracao": v[0] / v[1] if v[1] else None}
                for k, v in d.items()}
            for f, d in sorted(saida.items())}


def _diagnostico(anotacoes: dict, gabarito: dict) -> dict:
    rz = vz = 0
    for rid, g in gabarito.items():
        h = set(anotacoes[rid]["eixos"]) - {"livre"}
        m = set(g["eixos"]) - {"livre"}
        if h and not (h & m):
            rz += 1
        if g["confianca"] == "vazio":
            vz += 1
    return {"reviews_com_recall_zero": rz, "consensos_vazios": vz}


SEMENTE_BOOTSTRAP = 20260814
N_BOOTSTRAP = 5000


def _bootstrap(anotacoes: dict, gabs: dict, meta: dict) -> dict:
    eixos = set(EIXOS)
    ids = sorted(anotacoes)

    def pr(sub, g):
        tp = fp = fn = 0
        for rid in sub:
            h = set(anotacoes[rid]["eixos"]) & eixos
            m = set(g[rid]["eixos"]) & eixos
            tp += len(h & m); fp += len(m - h); fn += len(h - m)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return p, r, (2 * p * r / (p + r) if p + r else 0.0)

    def pr_eixo(sub, g, eixo):
        tp = fp = fn = 0
        for rid in sub:
            h = eixo in anotacoes[rid]["eixos"]
            m = eixo in g[rid]["eixos"]
            tp += h and m; fp += m and not h; fn += h and not m
        return (tp / (tp + fp) if tp + fp else 0.0,
                tp / (tp + fn) if tp + fn else 0.0)

    rng = random.Random(SEMENTE_BOOTSTRAP)
    acc = defaultdict(list)
    for _ in range(N_BOOTSTRAP):
        am = [rng.choice(ids) for _ in ids]
        curtas = [r for r in am if meta[r]["n_chars"] <= 200]
        a_g, b_g = pr(am, gabs["A_regra"]), pr(am, gabs["impacto_estrito"])
        acc["precisao_geral"].append(b_g[0] - a_g[0])
        acc["recall_geral"].append(b_g[1] - a_g[1])
        acc["f1_geral"].append(b_g[2] - a_g[2])
        if curtas:
            acc["recall_ate_200"].append(
                pr(curtas, gabs["impacto_estrito"])[1] - pr(curtas, gabs["A_regra"])[1])
        ap, ar = pr_eixo(am, gabs["A_regra"], "impacto_emocional")
        bp, br = pr_eixo(am, gabs["impacto_estrito"], "impacto_emocional")
        acc["precisao_impacto"].append(bp - ap)
        acc["recall_impacto"].append(br - ar)

    saida = {}
    for k, xs in acc.items():
        xs.sort()
        lo, hi = xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]
        saida[k] = {"delta_mediano": round(xs[len(xs) // 2], 4),
                    "ic95": [round(lo, 4), round(hi, 4)],
                    "cruza_zero": lo <= 0 <= hi}
    return saida


def cmd_comparar() -> None:
    anotacoes = aa.ler_anotacoes_humanas()
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    meta = {r["id"]: r for r in idx["reviews"]}

    base_variantes = RAIZ / "resultado" / "auditoria-acuracia" / "variantes"
    gabs = {"A_regra": consenso("A_regra", base_variantes),
            "impacto_estrito": consenso("impacto_estrito")}
    for nome, g in gabs.items():
        if len(g) != len(anotacoes):
            print(f"AVISO: {nome} tem {len(g)}/{len(anotacoes)} completas")

    rel = {}
    for nome, g in gabs.items():
        m = _metricas(anotacoes, g)
        rel[nome] = {
            "n": m["n_pares"],
            "concordancia_exata": m["geral"]["concordancia_exata"],
            "micro_geral": _micro(m["geral"]["por_eixo"]),
            "por_faixa": {f: _micro(b["por_eixo"])
                          for f, b in m["por_faixa_n_chars"].items()},
            "impacto_emocional": m["geral"]["por_eixo"]["impacto_emocional"],
            "por_eixo": {e: {"precisao": m["geral"]["por_eixo"][e]["precisao"],
                             "recall": m["geral"]["por_eixo"][e]["recall"]}
                         for e in EIXOS},
            "fracao_sem_eixo_por_faixa": _fracao_livre_por_faixa(g, meta, anotacoes),
            "diagnostico": _diagnostico(anotacoes, g),
        }
    rel["_bootstrap_estrito_menos_a_regra"] = _bootstrap(anotacoes, gabs, meta)

    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_COMPARACAO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    _imprimir(rel)
    print(f"\n→ {ARQ_COMPARACAO.relative_to(RAIZ)}")


def _imprimir(rel: dict) -> None:
    nomes = [k for k in rel if not k.startswith("_")]
    FAIXAS = ["<=200 (piso)", "201-400", "401-800", "801+"]

    print("\n=== impacto_emocional (contra o gabarito CORRIGIDO) ===")
    for rot in ("precisao", "recall", "f1"):
        linha = f"  {rot:<10}"
        for n in nomes:
            v = rel[n]["impacto_emocional"][rot]
            linha += f"{v:>18.3f}" if v is not None else f"{'-':>18}"
        print(f"{'':<12}" + "".join(f"{n:>18}" for n in nomes) if rot == "precisao" else "", end="")
        print(("\n" if rot == "precisao" else "") + linha)

    print("\n=== GERAL ===")
    print(f"{'':<18}" + "".join(f"{n:>18}" for n in nomes))
    for rot, ch in (("precisao micro", "precisao"), ("recall micro", "recall")):
        print(f"{rot:<18}" + "".join(f"{rel[n]['micro_geral'][ch]:>18.3f}" for n in nomes))
    print(f"{'concord. exata':<18}"
          + "".join(f"{rel[n]['concordancia_exata']:>18.3f}" for n in nomes))

    print("\n=== RECALL MICRO POR FAIXA ===")
    print(f"{'faixa':<18}" + "".join(f"{n:>18}" for n in nomes))
    for f in FAIXAS:
        linha = f"{f:<18}"
        for n in nomes:
            v = rel[n]["por_faixa"][f]["recall"]
            linha += f"{v:>18.3f}" if v is not None else f"{'-':>18}"
        print(linha)

    print("\n=== PRECISAO MICRO POR FAIXA ===")
    print(f"{'faixa':<18}" + "".join(f"{n:>18}" for n in nomes))
    for f in FAIXAS:
        linha = f"{f:<18}"
        for n in nomes:
            v = rel[n]["por_faixa"][f]["precisao"]
            linha += f"{v:>18.3f}" if v is not None else f"{'-':>18}"
        print(linha)

    print("\n=== SEM NENHUM EIXO TEMATICO no consenso, por faixa ===")
    print("   (com_eixo_tematico = o HUMANO viu eixo; cair aqui e REGRESSAO)")
    for grupo in ("com_eixo_tematico", "sem_eixo_tematico"):
        print(f"\n  -- {grupo} --")
        print(f"  {'faixa':<12}" + "".join(f"{n:>20}" for n in nomes))
        for f in ("<=200", "201-400", "401-800", "801+"):
            linha = f"  {f:<12}"
            for n in nomes:
                d = rel[n]["fracao_sem_eixo_por_faixa"].get(f, {}).get(grupo)
                linha += (f"{d['sem_eixo_do_modelo']}/{d['n']} ({d['fracao']:.0%})".rjust(20)
                          if d and d["n"] else "-".rjust(20))
            print(linha)

    print("\n=== DIAGNOSTICO ===")
    for ch, rot in (("reviews_com_recall_zero", "recall zero"),
                    ("consensos_vazios", "consenso vazio")):
        print(f"  {rot:<20}" + "".join(f"{rel[n]['diagnostico'][ch]:>18d}" for n in nomes))

    boot = rel.get("_bootstrap_estrito_menos_a_regra")
    if boot:
        print(f"\n=== BOOTSTRAP PAREADO (estrito - A_regra, B={N_BOOTSTRAP}) ===")
        for m, d in boot.items():
            lo, hi = d["ic95"]
            marca = "" if d["cruza_zero"] else "   <- IC95 nao cruza 0"
            print(f"  {m:<20}{d['delta_mediano']:+.3f}  IC95 [{lo:+.3f}, {hi:+.3f}]{marca}")


# ===========================================================================
# Entrega 4 — projeção no corpus (PROJEÇÃO, não medição)
# ===========================================================================

def cmd_projetar() -> None:
    """Projeta a frequência de `impacto_emocional` no corpus sob a variante,
    e o efeito no lift — usando `fator_pareado`, o preditor validado.

    É PROJEÇÃO. Ela herda os limites registrados em
    `previsao_frequencia`: prevê sinal e ordem de grandeza, não o segundo
    decimal, e NÃO modela competição entre eixos (o sinal que sai de um eixo
    reaparece em outro, e nenhum preditor por eixo isolado enxerga isso).
    A medição real exige reclassificar o corpus.
    """
    import math

    rel = json.loads(ARQ_COMPARACAO.read_text(encoding="utf-8"))
    consenso_corpus = [json.loads(l) for l in
                       (RAIZ / "resultado" / "votacao-3" / "consenso.jsonl")
                       .read_text(encoding="utf-8").splitlines() if l.strip()]

    projecao_eixo = {}
    for e in EIXOS:
        a = rel["A_regra"]["por_eixo"][e]
        b = rel["impacto_estrito"]["por_eixo"][e]
        fator, motivo = fator_pareado(a["precisao"], a["recall"],
                                      b["precisao"], b["recall"])
        obs = sum(1 for r in consenso_corpus if e in r["eixos"]) / len(consenso_corpus)
        projecao_eixo[e] = {
            "freq_atual": round(obs, 4),
            "fator": round(fator, 3) if fator is not None else None,
            "freq_projetada": round(obs * fator, 4) if fator is not None else None,
            "motivo_indefinido": motivo,
        }

    # Projeção do lift: reescala a probabilidade de cada eixo em cada bucket
    # pelo fator, por filme, e recalcula L1 + nulo de permutação.
    fator_ie = projecao_eixo["impacto_emocional"]["fator"]
    lift = None
    if fator_ie is not None:
        lift = _projetar_lift(consenso_corpus, fator_ie)

    saida = {
        "natureza": "PROJECAO, nao medicao — a medicao exige reclassificar o corpus",
        "preditor": "espectro24.previsao_frequencia.fator_pareado",
        "limites": ("preve sinal e ordem de grandeza, nao o segundo decimal; "
                    "NAO modela competicao entre eixos (o sinal que sai de um "
                    "eixo reaparece em outro)"),
        "por_eixo": projecao_eixo,
        "lift_projetado": lift,
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_PROJECAO.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print("=== PROJECAO DE FREQUENCIA NO CORPUS (3990 reviews) ===")
    print(f"{'eixo':<20}{'atual':>10}{'fator':>9}{'projetada':>12}")
    for e, d in sorted(projecao_eixo.items(),
                       key=lambda kv: -(kv[1]["freq_projetada"] or 0)):
        f = f"{d['fator']:.2f}x" if d["fator"] is not None else "-"
        p = f"{d['freq_projetada']:.1%}" if d["freq_projetada"] is not None else "-"
        print(f"{e:<20}{d['freq_atual']:>9.1%}{f:>9}{p:>12}")

    if lift:
        print(f"\n=== LIFT PROJETADO (L1, nulo de permutacao reescalado) ===")
        print(f"{'margem':>8}{'obs':>7}{'nulo':>8}{'ruido':>9}{'filmes':>9}")
        for m, d in lift["por_margem"].items():
            print(f"{float(m):>8.2f}{d['n_pares_acima']:>7}{d['nulo_media']:>8.1f}"
                  f"{d['fracao_ruido']:>8.1%}{d['n_filmes_com_algum']:>9}")
        b = lift["barbie"]
        print(f"\n  barbie: melhor eixo projetado = {b['melhor_eixo']} "
              f"({b['melhor_lift']:.3f}) · impacto_emocional = "
              f"{b['impacto_emocional_lift']:.3f} "
              f"(freqs {', '.join(f'{k}={v:.0%}' for k, v in b['ie_freqs'].items())})")
    print(f"\n→ {ARQ_PROJECAO.relative_to(RAIZ)}")


def _projetar_lift(consenso_corpus: list[dict], fator_ie: float) -> dict:
    """Reescala `impacto_emocional` por `fator_ie` e recalcula lift + nulo.

    **O modelo, declarado:** a marcação de `impacto_emocional` em cada review
    é mantida ou removida com probabilidade `fator_ie` (fator < 1 → remoção
    aleatória). Isso supõe que a definição apertada tira marcações de forma
    NÃO-SELETIVA entre buckets — é a suposição conservadora: se as remoções
    fossem concentradas no bucket que menos precisa delas, o lift subiria
    mais do que esta projeção indica. Nenhum outro eixo é reescalado (os
    fatores dos demais ficam perto de 1 e a competição não é modelada).
    """
    from classificar_10 import MARGENS, _lifts_do_filme, _nulo
    from espectro24.buckets import FRONTEIRAS

    rng = random.Random(f"{SEMENTE_BOOTSTRAP}:projecao_lift")
    ajustado = []
    for r in consenso_corpus:
        eixos = list(r["eixos"])
        if "impacto_emocional" in eixos and rng.random() > fator_ie:
            eixos.remove("impacto_emocional")
        ajustado.append({**r, "eixos": eixos})

    por_filme = defaultdict(list)
    for r in ajustado:
        por_filme[r["slug"]].append(r)
    por_filme = {s: rr for s, rr in por_filme.items()
                 if min(sum(1 for r in rr if r["bucket"] == b)
                        for b in FRONTEIRAS) >= 3}

    lifts, por_filme_melhor = [], {}
    for slug, rr in por_filme.items():
        d = _lifts_do_filme(rr)
        for e, v in d.items():
            lifts.append({"slug": slug, "eixo": e, "lift": v["lift"]})
        melhor = max(d, key=lambda e: d[e]["lift"])
        por_filme_melhor[slug] = {"eixo": melhor, "lift": d[melhor]["lift"],
                                  "d": d}

    nulo = _nulo(por_filme)
    por_margem = {}
    for m in MARGENS:
        acima = [x for x in lifts if x["lift"] >= m]
        media = nulo["pares_acima"][str(m)]["media"]
        por_margem[str(m)] = {
            "n_pares_acima": len(acima),
            "nulo_media": round(media, 2),
            "fracao_ruido": round(media / len(acima), 4) if acima else None,
            "n_filmes_com_algum": len({x["slug"] for x in acima}),
        }

    b = por_filme_melhor.get("barbie")
    barbie = None
    if b:
        barbie = {"melhor_eixo": b["eixo"], "melhor_lift": b["lift"],
                  "impacto_emocional_lift": b["d"]["impacto_emocional"]["lift"],
                  "ie_freqs": b["d"]["impacto_emocional"]["freqs"]}

    return {"modelo": ("remocao aleatoria nao-seletiva de impacto_emocional com "
                       f"prob 1-{fator_ie:.3f}; suposicao conservadora"),
            "fator_aplicado": fator_ie,
            "n_filmes": len(por_filme),
            "por_margem": por_margem, "barbie": barbie}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["passes", "comparar", "projetar"])
    args = ap.parse_args()
    {"passes": cmd_passes, "comparar": cmd_comparar,
     "projetar": cmd_projetar}[args.etapa]()


if __name__ == "__main__":
    main()
