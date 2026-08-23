"""[Entregas 1-5] Passe de VERIFICAÇÃO de `impacto_emocional`, após o consenso.

**O que motiva.** Contra o gabarito fechado, `impacto_emocional` sob o
prompt de produção (`A_regra`) tem precisão **0,486** e recall **0,921**:
das 72 marcações nas 100 auditadas, 35 são corretas e **37 são falsas** —
quase todas veredicto seco ("não gostei", "amei") contado como efeito.

Três tentativas de corrigir isso por INSTRUÇÃO ao classificador falharam
(SPEC §3[D], "Instrução não remove o que a distribuição do material
impõe"). A terceira é a decisiva: instrução explícita contra veredicto
seco, em DOIS pontos do prompt, mudou o comportamento em 3 de 13 casos.

**A hipótese que este módulo testa.** O padrão que FUNCIONOU historicamente
neste projeto mudou QUEM DECIDE, não o quanto se pede ao mesmo decisor
(v1.2.3: rótulo de quantificador movido para o código; v1.6.0: narrador e
editor separados em dois estágios). Aqui: um estágio de VERIFICAÇÃO,
separado da classificação, que recebe UMA pergunta binária e local — "esta
frase descreve efeito sobre quem assistiu, ou é veredicto sobre o filme?"
— em vez de varrer 10 eixos de uma vez.

**Assimetria estrutural que define o critério de sucesso.** O verificador
só REMOVE, nunca acrescenta. Então o recall só pode cair e a precisão só
pode subir; o teto é precisão 1,000 com recall inalterado em 0,921 (se
removesse os 37 falsos e nenhum verdadeiro). Um verificador serve se o
ganho de precisão superar a perda de recall — e NÃO serve se cortar
metade das marcações levando metade das corretas junto.

**Duas variantes**, porque a fase inteira mostrou que a primeira
formulação raramente é a melhor:

  V1 `regua`  — a régua declarativa de `REGRA_ANOTACAO.md`: confirma isto,
                remove aquilo, com as duas listas de exemplos.
  V2 `alvo`   — a MESMA régua como PROCEDIMENTO: identifique o ALVO da
                frase antes de decidir, e comprometa-se com ele num campo
                estruturado (`alvo`) que precede a decisão. A aposta é que
                forçar o compromisso com o alvo antes do veredicto evita o
                atalho de "tem palavra emocional, logo é impacto".

Ambas pedem a `frase` literal que justificou a decisão — telemetria
declarada, no mesmo padrão das outras verificações do projeto: é o que
permite AUDITAR o verificador depois, em vez de confiar nele.

Transporte: sempre pelo adaptador (guard-rail da v1.9.4).

Uso:
    python scripts/verificador_impacto.py passes     # 3 passadas x 2 variantes (LLM)
    python scripts/verificador_impacto.py comparar   # Entregas 2-3-5
    python scripts/verificador_impacto.py projetar   # Entrega 4 (sem LLM)

Saídas em `resultado/auditoria-acuracia/verificador/`.
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
import variante_impacto_estrito as vie  # noqa: E402
from classificar_10 import EIXOS, MODELO  # noqa: E402
from espectro24.previsao_frequencia import fator_pareado  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
)

SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "verificador"
DIR_A_REGRA = RAIZ / "resultado" / "auditoria-acuracia" / "variantes"
ARQ_COMPARACAO = SAIDA / "comparacao.json"
ARQ_PROJECAO = SAIDA / "projecao.json"

EIXO = "impacto_emocional"
CONCORRENCIA = 8
MAX_TENTATIVAS = 3
N_PASSES = 3

# Preços DeepSeek, USD por 1M de tokens (mesmos de `classificar_10`).
PRECO_ENTRADA_MISS = 0.14 / 1_000_000
PRECO_ENTRADA_HIT = 0.0028 / 1_000_000
PRECO_SAIDA = 0.28 / 1_000_000


# ===========================================================================
# Os dois prompts de verificação
# ===========================================================================

# Deliberadamente CURTOS e sobre UMA decisão. Não reapresentam a taxonomia
# nem pedem reclassificação — isso recriaria a tarefa difícil que já se sabe
# que o modelo não resolve.

SYSTEM_V1_REGUA = """Você verifica UMA decisão de classificação por vez, e responde só com JSON.

Uma review de cinema foi marcada com o eixo `impacto_emocional`. Sua tarefa é CONFIRMAR ou REMOVER essa marcação.

`impacto_emocional` exige que a review descreva o EFEITO que o filme causou em quem escreveu, ou na plateia da sessão.

CONFIRME quando a review diz o que o filme FEZ com quem assistiu:
"me fez chorar", "dormi no meio", "saí exausto", "fiquei desconfortável", "pausei de tédio", "ri alto", "passei mal", "me deu dor de cabeça", "fiquei confuso o filme todo", "aquilo me tirou da experiência", "metade da sala saiu".

REMOVA quando a review só diz que o filme É bom ou ruim. Veredicto seco de aprovação ou reprovação NÃO é impacto_emocional — nem no polo positivo nem no negativo:
"gostei", "não gostei", "é ruim", "é ótimo", "odiei", "amei", "obra-prima", "mid", "perda de tempo", "melhor filme do ano".

REMOVA também quando a review descreve o que o filme EVOCA ou DEIXA DE ENTREGAR, em vez do que ele causou:
"clima de angústia", "faltou emoção", "não dá medo", "sem intensidade", "não conseguiu me fazer apegar aos personagens".

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{"confirma": true, "frase": "..."}

`frase` é o trecho LITERAL da review que justifica a decisão — se confirma, a frase que descreve o efeito; se remove, a frase que você julgou ser veredicto ou descrição do filme."""


SYSTEM_V2_ALVO = """Você verifica UMA decisão de classificação por vez, e responde só com JSON.

Uma review de cinema foi marcada com o eixo `impacto_emocional`. Sua tarefa é CONFIRMAR ou REMOVER essa marcação.

Faça UM teste, nesta ordem:

1. Ache na review a frase que mais parece justificar `impacto_emocional`.
2. Pergunte: qual é o ALVO dessa frase?

   - ALVO = "espectador" — a frase diz O QUE ACONTECEU COM QUEM ASSISTIU (ou com a plateia): "chorei", "dormi", "saí exausto", "pausei de tédio", "fiquei confuso o filme todo", "aquilo me tirou da experiência", "metade da sala saiu". → CONFIRMA.

   - ALVO = "filme" — a frase diz COMO O FILME, UMA CENA OU UM PERSONAGEM É: "o filme é ruim", "não gostei", "amei", "obra-prima", "essa cena é nightmare fuel", "os personagens são idiotas", "faltou emoção", "não dá medo". → REMOVE.

O teste vale IGUAL nos dois polos: "não gostei" e "amei" são os dois veredicto sobre o filme. Nenhum dos dois é efeito sobre quem assistiu.

Atenção ao atalho mais comum: vocabulário emocional forte NÃO decide o teste. "odiooo os personagens" tem o PERSONAGEM como alvo, não quem assistiu — é REMOVE. "aquela cena me deu nojo" tem quem assistiu como alvo — é CONFIRMA.

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{"alvo": "espectador", "confirma": true, "frase": "..."}

`frase` é o trecho LITERAL da review em que você aplicou o teste."""


VARIANTES = {"V1_regua": SYSTEM_V1_REGUA, "V2_alvo": SYSTEM_V2_ALVO}


# ===========================================================================
# Alvos do passe — só reviews em que o CONSENSO marcou o eixo
# ===========================================================================

def _consenso_a_regra() -> dict[str, dict]:
    return vie.consenso("A_regra", DIR_A_REGRA)


def _reviews_a_verificar() -> list[dict]:
    """As reviews com `impacto_emocional` no consenso de produção.

    O passe NÃO reclassifica: ele opera sobre a saída existente, e por
    construção só pode remover marcações que já estão lá.
    """
    consenso = _consenso_a_regra()
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    amostra = json.loads(
        (RAIZ / "resultado" / "votacao-3" / "amostra.json").read_text(encoding="utf-8"))
    texto = {r["id"]: r["texto"] for r in amostra["reviews"]}
    saida = []
    for r in idx["reviews"]:
        if EIXO in consenso[r["id"]]["eixos"]:
            saida.append({**r, "texto": texto[r["id"]]})
    return saida


def _arq(variante: str, n: int) -> Path:
    return SAIDA / f"{variante}_passe_{n}.jsonl"


def _normalizar_veredito(data: dict) -> tuple[bool, str, str | None]:
    """`confirma` do JSON, tolerante a string, com o alvo quando houver.

    Ausência de `confirma` é tratada como CONFIRMAR (não remover) — a
    política conservadora: na dúvida, o passe não mexe na classificação
    original. Um verificador que remove por falha de parsing seria pior que
    não ter verificador.
    """
    bruto = data.get("confirma")
    if isinstance(bruto, str):
        confirma = bruto.strip().lower() not in ("false", "0", "nao", "não", "no")
    elif bruto is None:
        confirma = True
    else:
        confirma = bool(bruto)
    frase = str(data.get("frase", "") or "").strip()
    alvo = data.get("alvo")
    return confirma, frase, (str(alvo).strip().lower() if alvo else None)


def rodar_passe(variante: str, n_passe: int, reviews: list[dict],
                arq: Path | None = None) -> None:
    arq = arq if arq is not None else _arq(variante, n_passe)
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
    arq.parent.mkdir(parents=True, exist_ok=True)
    saida = arq.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        erro = ""
        for tentativa in range(MAX_TENTATIVAS):
            try:
                resp = deepseek_resposta(
                    system,
                    f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
                    f"{review['texto']}\n\n"
                    f"Esta review foi marcada com `impacto_emocional`. "
                    f"Confirma ou remove?",
                    MODELO, max_tokens=300, json_mode=True, client=client)
                data = json.loads(resp.choices[0].message.content)
                confirma, frase, alvo = _normalizar_veredito(data)
                registro = {"ok": True, "variante": variante, "passe": n_passe,
                            "id": review["id"], "n_chars": review["n_chars"],
                            "confirma": confirma, "frase": frase, "alvo": alvo,
                            "uso": deepseek_uso(resp)}
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
            if contador[0] % 20 == 0 or contador[0] == len(pendentes):
                print(f"    {contador[0]}/{len(pendentes)} · "
                      f"{time.time() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as ex:
        list(ex.map(tarefa, pendentes))
    saida.close()


def cmd_passes() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    SAIDA.mkdir(parents=True, exist_ok=True)
    reviews = _reviews_a_verificar()
    print(f"{len(reviews)} reviews com {EIXO} no consenso · "
          f"{len(VARIANTES)} variantes · {N_PASSES} passadas "
          f"= {len(reviews) * len(VARIANTES) * N_PASSES} chamadas")
    for v in VARIANTES:
        for n in range(1, N_PASSES + 1):
            rodar_passe(v, n, reviews)


# ===========================================================================
# Leitura + aplicação do veredito
# ===========================================================================

def _ler(variante: str, n: int) -> dict[str, dict]:
    arq = _arq(variante, n)
    if not arq.exists():
        return {}
    saida = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            r = json.loads(linha)
            if r.get("ok"):
                saida[r["id"]] = r
    return saida


def vereditos(variante: str, modo: str) -> dict[str, bool]:
    """`{id: confirma}`. `modo` = "passe1" (passada única) ou "consenso3".

    Consenso do VERIFICADOR usa a mesma regra do classificador — maioria de
    2 de 3 — para que a comparação entre "com votação" e "sem votação" seja
    a mesma pergunta que a fase já respondeu para a classificação.
    """
    if modo == "passe1":
        return {rid: r["confirma"] for rid, r in _ler(variante, 1).items()}
    passes = [_ler(variante, n) for n in range(1, N_PASSES + 1)]
    ids = set(passes[0]) & set(passes[1]) & set(passes[2])
    return {rid: sum(p[rid]["confirma"] for p in passes) >= 2 for rid in sorted(ids)}


def aplicar(consenso: dict[str, dict], vereditos_: dict[str, bool]) -> dict[str, dict]:
    """Remove `impacto_emocional` de quem o verificador reprovou."""
    saida = {}
    for rid, g in consenso.items():
        eixos = list(g["eixos"])
        if EIXO in eixos and vereditos_.get(rid, True) is False:
            eixos.remove(EIXO)
        saida[rid] = {**g, "eixos": eixos}
    return saida


# ===========================================================================
# Entregas 2, 3 e 5
# ===========================================================================

def _pr_eixo(anotacoes: dict, gab: dict, eixo: str) -> dict:
    tp = fp = fn = 0
    for rid, g in gab.items():
        h = eixo in anotacoes[rid]["eixos"]
        m = eixo in g["eixos"]
        tp += h and m; fp += m and not h; fn += h and not m
    return {"tp": tp, "fp": fp, "fn": fn,
            "precisao": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else None}


def _pr_micro(anotacoes: dict, gab: dict) -> dict:
    eixos = set(EIXOS)
    tp = fp = fn = 0
    for rid, g in gab.items():
        h = set(anotacoes[rid]["eixos"]) & eixos
        m = set(g["eixos"]) & eixos
        tp += len(h & m); fp += len(m - h); fn += len(h - m)
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "precisao": p, "recall": r,
            "f1": (2 * p * r / (p + r)) if p and r else None}


def _dano_e_acerto(anotacoes: dict, vereditos_: dict[str, bool]) -> dict:
    """Das marcações que o verificador REMOVEU: quantas o gabarito também
    remove (acerto) e quantas ele mantinha (dano). É o número que decide."""
    removidas = [rid for rid, ok in vereditos_.items() if ok is False]
    acerto = [r for r in removidas if EIXO not in anotacoes[r]["eixos"]]
    dano = [r for r in removidas if EIXO in anotacoes[r]["eixos"]]
    mantidas = [rid for rid, ok in vereditos_.items() if ok is not False]
    fp_restante = [r for r in mantidas if EIXO not in anotacoes[r]["eixos"]]
    return {"n_removidas": len(removidas),
            "acerto_gabarito_tambem_remove": len(acerto),
            "dano_gabarito_mantinha": len(dano),
            "taxa_de_acerto_das_remocoes": (len(acerto) / len(removidas)
                                            if removidas else None),
            "falsos_positivos_que_sobreviveram": len(fp_restante),
            "ids_dano": sorted(dano)}


def _reprodutibilidade(variante: str) -> dict:
    """[Entrega 3] As 3 passadas concordam? Se >85%, passada única basta."""
    passes = [_ler(variante, n) for n in range(1, N_PASSES + 1)]
    ids = sorted(set(passes[0]) & set(passes[1]) & set(passes[2]))
    if not ids:
        return {}
    iguais = sum(1 for rid in ids
                 if passes[0][rid]["confirma"] == passes[1][rid]["confirma"]
                 == passes[2][rid]["confirma"])
    # quanto o consenso difere da passada única — o que se perde sem votação
    p1 = {rid: passes[0][rid]["confirma"] for rid in ids}
    c3 = {rid: sum(p[rid]["confirma"] for p in passes) >= 2 for rid in ids}
    difere = sum(1 for rid in ids if p1[rid] != c3[rid])
    return {"n": len(ids), "as_3_passadas_identicas": iguais,
            "fracao_identica": iguais / len(ids),
            "passe1_difere_do_consenso3": difere,
            "fracao_passe1_difere": difere / len(ids)}


def _bootstrap(anotacoes: dict, base: dict, verificado: dict) -> dict:
    """Bootstrap pareado (verificado − base), por review."""
    ids = sorted(base)
    eixos = set(EIXOS)

    def metricas(sub, gab):
        tp = fp = fn = 0
        tpe = fpe = fne = 0
        for rid in sub:
            h = set(anotacoes[rid]["eixos"]) & eixos
            m = set(gab[rid]["eixos"]) & eixos
            tp += len(h & m); fp += len(m - h); fn += len(h - m)
            he, me = EIXO in anotacoes[rid]["eixos"], EIXO in gab[rid]["eixos"]
            tpe += he and me; fpe += me and not he; fne += he and not me
        return {
            "precisao_geral": tp / (tp + fp) if tp + fp else 0.0,
            "recall_geral": tp / (tp + fn) if tp + fn else 0.0,
            "precisao_eixo": tpe / (tpe + fpe) if tpe + fpe else 0.0,
            "recall_eixo": tpe / (tpe + fne) if tpe + fne else 0.0,
            "f1_eixo": (2 * tpe / (2 * tpe + fpe + fne)) if (2 * tpe + fpe + fne) else 0.0,
        }

    rng = random.Random(20260814)
    acc = defaultdict(list)
    for _ in range(5000):
        am = [rng.choice(ids) for _ in ids]
        mb, mv = metricas(am, base), metricas(am, verificado)
        for k in mb:
            acc[k].append(mv[k] - mb[k])
    saida = {}
    for k, xs in acc.items():
        xs.sort()
        lo, hi = xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]
        saida[k] = {"delta_mediano": round(xs[len(xs) // 2], 4),
                    "ic95": [round(lo, 4), round(hi, 4)],
                    "cruza_zero": lo <= 0 <= hi}
    return saida


def _custo(variante: str) -> dict:
    uso = Counter()
    n = 0
    for p in range(1, N_PASSES + 1):
        for r in _ler(variante, p).values():
            n += 1
            for k, v in (r.get("uso") or {}).items():
                uso[k] += v
    custo = (uso["cache_miss_tokens"] * PRECO_ENTRADA_MISS
             + uso["cache_hit_tokens"] * PRECO_ENTRADA_HIT
             + uso["completion_tokens"] * PRECO_SAIDA)
    return {"n_chamadas": n, "uso": dict(uso), "custo_usd": custo,
            "custo_por_chamada": custo / n if n else None}


def cmd_comparar() -> None:
    anotacoes = aa.ler_anotacoes_humanas()
    base = _consenso_a_regra()

    rel = {"base_A_regra": {
        "eixo": _pr_eixo(anotacoes, base, EIXO),
        "micro_geral": _pr_micro(anotacoes, base),
        "n_marcadas": sum(1 for g in base.values() if EIXO in g["eixos"])}}

    for variante in VARIANTES:
        rel[variante] = {"reprodutibilidade": _reprodutibilidade(variante),
                         "custo_3_passadas": _custo(variante)}
        for modo in ("passe1", "consenso3"):
            v = vereditos(variante, modo)
            if not v:
                continue
            aplicado = aplicar(base, v)
            rel[variante][modo] = {
                "eixo": _pr_eixo(anotacoes, aplicado, EIXO),
                "micro_geral": _pr_micro(anotacoes, aplicado),
                "n_marcadas": sum(1 for g in aplicado.values() if EIXO in g["eixos"]),
                "remocoes": _dano_e_acerto(anotacoes, v),
                "bootstrap_vs_base": _bootstrap(anotacoes, base, aplicado),
            }

    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_COMPARACAO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    _imprimir(rel)
    print(f"\n→ {ARQ_COMPARACAO.relative_to(RAIZ)}")


def _imprimir(rel: dict) -> None:
    b = rel["base_A_regra"]
    print(f"=== BASE (A_regra, sem verificacao) ===")
    print(f"  {EIXO}: P={b['eixo']['precisao']:.3f} R={b['eixo']['recall']:.3f} "
          f"F1={b['eixo']['f1']:.3f}  (tp{b['eixo']['tp']} fp{b['eixo']['fp']} fn{b['eixo']['fn']})")
    print(f"  micro geral: P={b['micro_geral']['precisao']:.3f} "
          f"R={b['micro_geral']['recall']:.3f}")
    print(f"  marcacoes: {b['n_marcadas']}")

    for variante in VARIANTES:
        d = rel.get(variante, {})
        print(f"\n=== {variante} ===")
        rp = d.get("reprodutibilidade") or {}
        if rp:
            print(f"  reprodutibilidade das 3 passadas: {rp['fracao_identica']:.1%} "
                  f"({rp['as_3_passadas_identicas']}/{rp['n']} identicas) · "
                  f"passe1 difere do consenso em {rp['passe1_difere_do_consenso3']}")
        for modo in ("passe1", "consenso3"):
            m = d.get(modo)
            if not m:
                continue
            e, g, r = m["eixo"], m["micro_geral"], m["remocoes"]
            print(f"  -- {modo} --")
            print(f"     {EIXO}: P={e['precisao']:.3f} R={e['recall']:.3f} "
                  f"F1={e['f1']:.3f}  (tp{e['tp']} fp{e['fp']} fn{e['fn']})")
            print(f"     micro geral: P={g['precisao']:.3f} R={g['recall']:.3f}")
            print(f"     removeu {r['n_removidas']}: {r['acerto_gabarito_tambem_remove']} "
                  f"acerto / {r['dano_gabarito_mantinha']} dano"
                  + (f" (taxa {r['taxa_de_acerto_das_remocoes']:.0%})"
                     if r["taxa_de_acerto_das_remocoes"] is not None else ""))
            print(f"     falsos positivos sobreviventes: "
                  f"{r['falsos_positivos_que_sobreviveram']}")
            bs = m["bootstrap_vs_base"]
            for k in ("precisao_eixo", "recall_eixo", "f1_eixo",
                      "precisao_geral", "recall_geral"):
                x = bs[k]
                lo, hi = x["ic95"]
                marca = "" if x["cruza_zero"] else "  <- IC95 nao cruza 0"
                print(f"     {k:<16}{x['delta_mediano']:+.3f} "
                      f"IC95 [{lo:+.3f}, {hi:+.3f}]{marca}")
        c = d.get("custo_3_passadas")
        if c:
            print(f"  custo 3 passadas ({c['n_chamadas']} chamadas): "
                  f"US$ {c['custo_usd']:.4f}")


# ===========================================================================
# Entrega 4 — projeção
# ===========================================================================

def cmd_projetar() -> None:
    rel = json.loads(ARQ_COMPARACAO.read_text(encoding="utf-8"))
    consenso_corpus = [json.loads(l) for l in
                       (RAIZ / "resultado" / "votacao-3" / "consenso.jsonl")
                       .read_text(encoding="utf-8").splitlines() if l.strip()]
    base = rel["base_A_regra"]["eixo"]
    freq_atual = sum(1 for r in consenso_corpus if EIXO in r["eixos"]) / len(consenso_corpus)

    saida = {"natureza": "PROJECAO, nao medicao — a medicao exige rodar o "
                         "verificador sobre o corpus inteiro",
             "freq_atual": round(freq_atual, 4), "por_variante": {}}

    for variante in VARIANTES:
        for modo in ("passe1", "consenso3"):
            m = rel.get(variante, {}).get(modo)
            if not m:
                continue
            e = m["eixo"]
            fator, motivo = fator_pareado(base["precisao"], base["recall"],
                                          e["precisao"], e["recall"])
            proj = freq_atual * fator if fator is not None else None
            bloco = {"fator": round(fator, 3) if fator else None,
                     "freq_projetada": round(proj, 4) if proj else None,
                     "motivo_indefinido": motivo}
            if proj is not None:
                bloco["lift"] = _projetar_lift(consenso_corpus, fator)
            saida["por_variante"][f"{variante}/{modo}"] = bloco

    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_PROJECAO.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print(f"=== PROJECAO no corpus (3990 reviews) — {EIXO} em {freq_atual:.1%} hoje ===")
    for nome, b in saida["por_variante"].items():
        if b["freq_projetada"] is None:
            print(f"  {nome:<22} indefinido: {b['motivo_indefinido']}")
            continue
        print(f"\n  {nome:<22} fator {b['fator']:.2f}x → {b['freq_projetada']:.1%}")
        lf = b.get("lift")
        if lf:
            for m, d in lf["por_margem"].items():
                if m in ("0.15", "0.2", "0.25"):
                    print(f"      margem {float(m):.2f}: {d['n_pares_acima']:>3} pares · "
                          f"ruido {d['fracao_ruido']:.1%} · "
                          f"{d['n_filmes_com_algum']}/35 filmes")
            bb = lf["barbie"]
            print(f"      barbie: melhor={bb['melhor_eixo']} ({bb['melhor_lift']:.3f}) · "
                  f"{EIXO}={bb['impacto_emocional_lift']:.3f}")
    print(f"\n→ {ARQ_PROJECAO.relative_to(RAIZ)}")


def _projetar_lift(consenso_corpus: list[dict], fator: float) -> dict:
    """Reusa o modelo já declarado em `variante_impacto_estrito._projetar_lift`
    — remoção aleatória NÃO-SELETIVA entre buckets, suposição conservadora."""
    return vie._projetar_lift(consenso_corpus, fator)


# ===========================================================================
# Entrega 4 (corrigida em 2026-08-22) — projeção sob margem EXATA
# ===========================================================================
#
# A projeção acima foi medida em 2026-08-14, ANTES da correção de margem da
# v1.9.15, e herda os dois defeitos que aquela versão consertou no caminho de
# produção (SPEC §3[D]):
#
#   1. compara `lift >= m` em FLOAT — o mesmo `0.2 >= 0.2` avaliando falso em
#      binário que fazia 5 filmes cair fora da margem por engano. A base que
#      ela usava era 13/35; sob `>=` exato sempre foram 18/35.
#   2. sorteia UMA vez um modelo estocástico, sem incerteza declarada.
#
# Esta versão usa a MESMA fonte de verdade do caminho de produção
# (`espectro24.eixos`), `Fraction` do começo ao fim, e roda N sorteios
# reportando a FRAÇÃO em que cada veredito vira. A projeção antiga fica no
# disco como registro do que foi medido quando — não é reescrita.

from fractions import Fraction  # noqa: E402

from espectro24 import eixos as EX  # noqa: E402

ARQ_PROJECAO_EXATA = SAIDA / "projecao_exata.json"
PUBLICADOS = ("cure", "cidade-de-deus", "the-invite-2026")
N_SORTEIOS = 2000
SEMENTE_PROJECAO = 20260822


def _atinge(lift: Fraction) -> bool:
    """A margem do projeto, EXATA. Fonte única: `eixos.acima_da_margem`."""
    return EX.acima_da_margem(lift)


def _corpus_consenso() -> list[dict]:
    caminho = RAIZ / "resultado" / "votacao-3" / "consenso.jsonl"
    return [json.loads(l) for l in
            caminho.read_text(encoding="utf-8").splitlines() if l.strip()]


def _sortear_remocoes(corpus: list[dict], fator: float,
                      semente: int) -> list[dict]:
    """Cada marcação de `EIXO` cai com probabilidade `1 - fator`.

    Remoção NÃO-SELETIVA entre buckets — a mesma suposição conservadora já
    declarada no modelo original. `fator >= 1` não remove nada.
    """
    rng = random.Random(semente)
    fora = []
    for r in corpus:
        eixos = list(r["eixos"])
        if EIXO in eixos and rng.random() > fator:
            eixos.remove(EIXO)
        fora.append({**r, "eixos": eixos})
    return fora


def _por_filme(corpus: list[dict]) -> dict[str, dict[str, dict[str, list[str]]]]:
    """`{slug: {bucket: {id: eixos}}}` — a forma que `eixos.frequencias` come."""
    fora: dict = defaultdict(lambda: defaultdict(dict))
    for r in corpus:
        fora[r["slug"]][r["bucket"]][r["id"]] = r["eixos"]
    return {s: dict(b) for s, b in fora.items()}


def _cobertura_exata(corpus: list[dict]) -> dict:
    """Cobertura de contraste e veredito por filme, sob `>=` exato."""
    filmes = _por_filme(corpus)
    com_algum, contraste, freq_ie = 0, {}, {}
    for slug, buckets in filmes.items():
        freqs = EX.frequencias(buckets)
        lf = EX.lifts(freqs)
        est = EX.contraste(lf)
        contraste[slug] = est
        com_algum += est == "tematico"
        n = sum(f["n"] for f in freqs.values())
        marcadas = sum(f["por_eixo"].get(EIXO, 0) for f in freqs.values())
        freq_ie[slug] = Fraction(marcadas, n) if n else Fraction(0)
    return {"n_filmes": len(filmes), "n_filmes_com_algum": com_algum,
            "contraste": contraste, "freq_ie": freq_ie}


def _freq_media_por_eixo(corpus: list[dict]) -> dict[str, float]:
    n = len(corpus)
    c = Counter()
    for r in corpus:
        for e in set(r["eixos"]):
            c[e] += 1
    return {e: c.get(e, 0) / n for e in EIXOS}


def cmd_projetar_exato() -> None:
    rel = json.loads(ARQ_COMPARACAO.read_text(encoding="utf-8"))
    corpus = _corpus_consenso()
    base = _cobertura_exata(corpus)
    freqs_base = _freq_media_por_eixo(corpus)
    outros = sorted(v for e, v in freqs_base.items() if e != EIXO)

    saida = {
        "natureza": "PROJECAO, nao medicao — a medicao exige rodar o "
                    "verificador sobre o corpus inteiro",
        "corrige": "projecao.json (2026-08-14), medida em float e com 1 sorteio",
        "margem_pp": EX.MARGEM_LIFT_PP,
        "n_sorteios": N_SORTEIOS,
        "base": {
            "n_filmes": base["n_filmes"],
            "n_filmes_com_algum": base["n_filmes_com_algum"],
            "contraste_publicados": {s: base["contraste"][s] for s in PUBLICADOS},
            "freq_ie": round(freqs_base[EIXO], 4),
            "freq_outros_eixos": {"min": round(outros[0], 4),
                                  "mediana": round(outros[len(outros) // 2], 4),
                                  "max": round(outros[-1], 4)},
        },
        "por_variante": {},
    }

    b = rel["base_A_regra"]["eixo"]
    for variante in VARIANTES:
        for modo in ("passe1", "consenso3"):
            m = rel.get(variante, {}).get(modo)
            if not m:
                continue
            e = m["eixo"]
            fator, motivo = fator_pareado(b["precisao"], b["recall"],
                                          e["precisao"], e["recall"])
            if fator is None:
                saida["por_variante"][f"{variante}/{modo}"] = {
                    "fator": None, "motivo_indefinido": motivo}
                continue

            cob, virou, freq_ie_proj = [], Counter(), []
            for i in range(N_SORTEIOS):
                amostra = _sortear_remocoes(corpus, fator, SEMENTE_PROJECAO + i)
                c = _cobertura_exata(amostra)
                cob.append(c["n_filmes_com_algum"])
                freq_ie_proj.append(_freq_media_por_eixo(amostra)[EIXO])
                for s in PUBLICADOS:
                    if c["contraste"][s] != base["contraste"][s]:
                        virou[s] += 1
            cob.sort()
            saida["por_variante"][f"{variante}/{modo}"] = {
                "fator": round(fator, 3),
                "freq_ie_projetada": round(sum(freq_ie_proj) / len(freq_ie_proj), 4),
                "cobertura_contraste": {
                    "base": base["n_filmes_com_algum"],
                    "mediana": cob[len(cob) // 2],
                    "ic95": [cob[int(0.025 * len(cob))],
                             cob[int(0.975 * len(cob))]],
                    "delta_mediano": cob[len(cob) // 2] - base["n_filmes_com_algum"],
                },
                "veredito_publicados": {
                    s: {"base": base["contraste"][s],
                        "fracao_de_sorteios_que_vira": round(virou[s] / N_SORTEIOS, 4)}
                    for s in PUBLICADOS},
            }

    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_PROJECAO_EXATA.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    _imprimir_projecao_exata(saida)
    print(f"\n→ {ARQ_PROJECAO_EXATA.relative_to(RAIZ)}")


def _imprimir_projecao_exata(saida: dict) -> None:
    b = saida["base"]
    fo = b["freq_outros_eixos"]
    print(f"=== PROJECAO EXATA (margem {saida['margem_pp']}pp, `>=` Fraction, "
          f"{saida['n_sorteios']} sorteios) ===")
    print(f"  BASE: {EIXO} em {b['freq_ie']:.1%} · outros eixos "
          f"[{fo['min']:.1%} .. mediana {fo['mediana']:.1%} .. {fo['max']:.1%}]")
    print(f"  BASE: cobertura de contraste {b['n_filmes_com_algum']}/"
          f"{b['n_filmes']} filmes")
    for s, v in b["contraste_publicados"].items():
        print(f"        {s:<18} {v}")
    for nome, d in saida["por_variante"].items():
        if d.get("fator") is None:
            print(f"\n  {nome:<22} indefinido: {d['motivo_indefinido']}")
            continue
        c = d["cobertura_contraste"]
        print(f"\n  {nome:<22} fator {d['fator']:.2f}x → {EIXO} em "
              f"{d['freq_ie_projetada']:.1%}")
        print(f"      cobertura: {c['base']} → mediana {c['mediana']} "
              f"IC95 [{c['ic95'][0]}, {c['ic95'][1]}]  "
              f"({c['delta_mediano']:+d} filmes)")
        for s, vv in d["veredito_publicados"].items():
            print(f"      {s:<18} {vv['base']:<11} vira em "
                  f"{vv['fracao_de_sorteios_que_vira']:.1%} dos sorteios")


# ===========================================================================
# v1.9.16 — aplicação ao consenso de PRODUÇÃO (adoção)
# ===========================================================================
#
# DECISÃO DO DONO DO PROJETO (2026-08-22): adotar `V2_alvo`, passada única,
# sem votação (88,9% de reprodutibilidade medida na Entrega 3 justifica).
#
# O passe roda sobre `resultado/votacao-3/consenso.jsonl` inteiro — as 4181
# reviews classificadas dos 35 filmes, não a amostra de 100 do gabarito —
# filtrado às ~3162 reviews em que `impacto_emocional` está no consenso.
# Escreve TRÊS arquivos, todos em `resultado/votacao-3/`, ao lado do
# `consenso.jsonl` cru (que nunca é sobrescrito):
#
#   verificador_producao.jsonl   telemetria por review (veredito + frase +
#                                 alvo) — checkpoint/resume, no mesmo padrão
#                                 de `rodar_passe`.
#   consenso_verificado.jsonl    o consenso de produção com `impacto_emocional`
#                                 removido onde o passe reprovou — MESMO
#                                 schema de `consenso.jsonl`, só `eixos` muda.
#   verificador_manifesto.json   variante, passada, contagens, custo e
#                                 `fonte_n_linhas` — o número que
#                                 `pipeline._carregar_consenso_producao` usa
#                                 para recusar um verificado desatualizado.

ARQ_PRODUCAO = SAIDA.parent.parent / "votacao-3" / "verificador_producao.jsonl"
ARQ_CONSENSO_PRODUCAO = SAIDA.parent.parent / "votacao-3" / "consenso.jsonl"
ARQ_AMOSTRA_PRODUCAO = SAIDA.parent.parent / "votacao-3" / "amostra.json"
ARQ_CONSENSO_VERIFICADO = SAIDA.parent.parent / "votacao-3" / "consenso_verificado.jsonl"
ARQ_MANIFESTO_VERIFICADOR = SAIDA.parent.parent / "votacao-3" / "verificador_manifesto.json"
VARIANTE_PRODUCAO = "V2_alvo"


def _linhas_consenso_producao() -> list[dict]:
    return [json.loads(l) for l in
            ARQ_CONSENSO_PRODUCAO.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _reviews_producao_a_verificar(linhas: list[dict]) -> list[dict]:
    """As reviews do CORPUS INTEIRO com `impacto_emocional` no consenso —
    ~3162 das 4181, ~75,6% (a saturação medida). Texto vem de
    `votacao-3/amostra.json`, o manifesto da classificação de produção."""
    amostra = json.loads(ARQ_AMOSTRA_PRODUCAO.read_text(encoding="utf-8"))
    por_id = {r["id"]: r for r in amostra["reviews"]}
    saida = []
    for r in linhas:
        if EIXO in r["eixos"]:
            t = por_id.get(r["id"])
            if t is not None:
                saida.append({"id": r["id"], "nivel": t["nivel"],
                              "n_chars": t["n_chars"], "texto": t["texto"]})
    return saida


def gerar_consenso_verificado(linhas: list[dict],
                              vereditos_: dict[str, bool]) -> list[dict]:
    """O transform PURO: aplica os vereditos às linhas do consenso de
    produção. Só remove `EIXO`, e só quando há veredito EXPLÍCITO de
    remoção — linha sem `impacto_emocional`, sem veredito (chamada que
    falhou) ou com veredito de confirmação sai IDÊNTICA à de entrada. Mesma
    política conservadora de `_normalizar_veredito`: na dúvida, não mexe.
    """
    saida = []
    for r in linhas:
        eixos = list(r["eixos"])
        if EIXO in eixos and vereditos_.get(r["id"]) is False:
            eixos.remove(EIXO)
        saida.append({**r, "eixos": eixos})
    return saida


def cmd_aplicar_producao() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    linhas = _linhas_consenso_producao()
    candidatas = _reviews_producao_a_verificar(linhas)
    print(f"consenso de produção: {len(linhas)} linhas · "
          f"{len(candidatas)} com {EIXO} no consenso "
          f"({len(candidatas) / len(linhas):.1%}) · variante "
          f"{VARIANTE_PRODUCAO} · passada única")

    rodar_passe(VARIANTE_PRODUCAO, 1, candidatas, arq=ARQ_PRODUCAO)

    resultados = {}
    for l in ARQ_PRODUCAO.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("ok"):
                resultados[r["id"]] = r
    faltando = [c["id"] for c in candidatas if c["id"] not in resultados]
    if faltando:
        print(f"  AVISO: {len(faltando)} review(s) sem resultado ok (falha "
              "persistente) — ficam com a marcação original, política "
              "conservadora.")
    vereditos_ = {rid: r["confirma"] for rid, r in resultados.items()}

    saida = gerar_consenso_verificado(linhas, vereditos_)
    n_removidas = sum(1 for antes, depois in zip(linhas, saida)
                      if EIXO in antes["eixos"] and EIXO not in depois["eixos"])

    ARQ_CONSENSO_VERIFICADO.parent.mkdir(parents=True, exist_ok=True)
    with ARQ_CONSENSO_VERIFICADO.open("w", encoding="utf-8") as fh:
        for r in saida:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    uso = Counter()
    for r in resultados.values():
        for k, v in (r.get("uso") or {}).items():
            uso[k] += v
    custo = (uso["cache_miss_tokens"] * PRECO_ENTRADA_MISS
            + uso["cache_hit_tokens"] * PRECO_ENTRADA_HIT
            + uso["completion_tokens"] * PRECO_SAIDA)

    manifesto = {
        "variante": VARIANTE_PRODUCAO, "passada": 1, "eixo": EIXO,
        "fonte": str(ARQ_CONSENSO_PRODUCAO.relative_to(RAIZ)),
        "fonte_n_linhas": len(linhas),
        "n_candidatas": len(candidatas),
        "n_verificadas": len(resultados),
        "n_falharam": len(faltando),
        "n_removidas": n_removidas,
        "n_chamadas": len(resultados),
        "uso": dict(uso),
        "custo_usd": custo,
    }
    ARQ_MANIFESTO_VERIFICADOR.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  removidas: {n_removidas}/{len(candidatas)} "
          f"({n_removidas / len(candidatas):.1%})")
    print(f"  custo: US$ {custo:.4f} ({len(resultados)} chamadas)")
    print(f"→ {ARQ_CONSENSO_VERIFICADO.relative_to(RAIZ)}")
    print(f"→ {ARQ_MANIFESTO_VERIFICADOR.relative_to(RAIZ)}")


# ===========================================================================
# v1.9.16 — Entrega 2: relatório MEDIDO (não projetado) da aplicação real
# ===========================================================================

ARQ_RELATORIO_PRODUCAO = SAIDA.parent.parent / "votacao-3" / "relatorio_aplicacao.json"


def _por_filme_bucket(linhas: list[dict]
                      ) -> dict[str, dict[str, dict[str, list[str]]]]:
    fora: dict = defaultdict(lambda: defaultdict(dict))
    for r in linhas:
        fora[r["slug"]][r["bucket"]][r["id"]] = r["eixos"]
    return {s: dict(b) for s, b in fora.items()}


def relatorio_aplicacao(linhas_cru: list[dict],
                        linhas_verificado: list[dict]) -> dict:
    """Compara o consenso CRU com o VERIFICADO, por filme e por bucket —
    remoções, frequência e o veredito de `contraste` antes/depois. Puro:
    só `eixos.py` (Counter/Fraction), nenhuma chamada de LLM aqui — é a
    MEDIÇÃO real, contra a qual a projeção da Entrega 4 anterior se compara.
    """
    from espectro24 import eixos as EX

    cru = _por_filme_bucket(linhas_cru)
    ver = _por_filme_bucket(linhas_verificado)
    slugs = sorted(set(cru) | set(ver))

    por_filme = {}
    total_removidas = 0
    for slug in slugs:
        bc, bv = cru.get(slug, {}), ver.get(slug, {})
        contraste_c = EX.contraste(EX.lifts(EX.frequencias(bc))) if bc else None
        contraste_v = EX.contraste(EX.lifts(EX.frequencias(bv))) if bv else None

        removidas_bucket = {}
        for b in sorted(set(bc) | set(bv)):
            n = sum(1 for rid, ex in bc.get(b, {}).items()
                    if EIXO in ex and EIXO not in bv.get(b, {}).get(rid, ex))
            if n:
                removidas_bucket[b] = n
        n_removidas = sum(removidas_bucket.values())
        total_removidas += n_removidas

        por_filme[slug] = {
            "removidas": n_removidas,
            "removidas_por_bucket": removidas_bucket,
            "contraste_antes": contraste_c,
            "contraste_depois": contraste_v,
            "veredito_mudou": contraste_c is not None and contraste_v is not None
                              and contraste_c != contraste_v,
        }

    tematicos_antes = [s for s, d in por_filme.items()
                       if d["contraste_antes"] == "tematico"]
    tematicos_depois = [s for s, d in por_filme.items()
                        if d["contraste_depois"] == "tematico"]
    return {
        "n_filmes": len(slugs),
        "total_removidas": total_removidas,
        "por_filme": por_filme,
        "cobertura_antes": len(tematicos_antes),
        "cobertura_depois": len(tematicos_depois),
        "vereditos_mudaram": sorted(s for s, d in por_filme.items()
                                    if d["veredito_mudou"]),
    }


def cmd_relatorio_producao() -> None:
    linhas_cru = _linhas_consenso_producao()
    if not ARQ_CONSENSO_VERIFICADO.exists():
        raise SystemExit(
            f"{ARQ_CONSENSO_VERIFICADO} não existe — rode "
            "`python scripts/verificador_impacto.py aplicar-producao` antes.")
    linhas_ver = [json.loads(l) for l in
                 ARQ_CONSENSO_VERIFICADO.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    manifesto = json.loads(ARQ_MANIFESTO_VERIFICADOR.read_text(encoding="utf-8"))

    rel = relatorio_aplicacao(linhas_cru, linhas_ver)
    n_ie_antes = sum(1 for r in linhas_cru if EIXO in r["eixos"])
    n_ie_depois = sum(1 for r in linhas_ver if EIXO in r["eixos"])
    saida = {
        "manifesto": manifesto,
        "freq_impacto_emocional": {
            "antes": round(n_ie_antes / len(linhas_cru), 4),
            "depois": round(n_ie_depois / len(linhas_ver), 4),
        },
        **rel,
    }
    ARQ_RELATORIO_PRODUCAO.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                                      encoding="utf-8")

    print(f"=== APLICAÇÃO MEDIDA (não projetada) — {manifesto['n_candidatas']} "
          f"candidatas, {manifesto['n_removidas']} removidas "
          f"({manifesto['n_removidas'] / manifesto['n_candidatas']:.1%}) ===")
    print(f"  {EIXO}: {saida['freq_impacto_emocional']['antes']:.1%} → "
          f"{saida['freq_impacto_emocional']['depois']:.1%}")
    print(f"  custo real: US$ {manifesto['custo_usd']:.4f} "
          f"({manifesto['n_chamadas']} chamadas)")
    print(f"  cobertura de contraste: {rel['cobertura_antes']}/{rel['n_filmes']} "
          f"→ {rel['cobertura_depois']}/{rel['n_filmes']}")
    if rel["vereditos_mudaram"]:
        print(f"  VEREDITOS QUE MUDARAM: {', '.join(rel['vereditos_mudaram'])}")
    else:
        print("  nenhum veredito de contraste mudou")
    print(f"\n→ {ARQ_RELATORIO_PRODUCAO.relative_to(RAIZ)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["passes", "comparar", "projetar",
                                      "projetar-exato", "aplicar-producao",
                                      "relatorio-producao"])
    args = ap.parse_args()
    {"passes": cmd_passes, "comparar": cmd_comparar,
     "projetar": cmd_projetar,
     "projetar-exato": cmd_projetar_exato,
     "aplicar-producao": cmd_aplicar_producao,
     "relatorio-producao": cmd_relatorio_producao}[args.etapa]()


if __name__ == "__main__":
    main()
