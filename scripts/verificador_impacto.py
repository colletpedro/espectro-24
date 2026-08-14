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


def rodar_passe(variante: str, n_passe: int, reviews: list[dict]) -> None:
    arq = _arq(variante, n_passe)
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["passes", "comparar", "projetar"])
    args = ap.parse_args()
    {"passes": cmd_passes, "comparar": cmd_comparar,
     "projetar": cmd_projetar}[args.etapa]()


if __name__ == "__main__":
    main()
