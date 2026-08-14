"""[Entregas 1-2] Lift sob SATURAÇÃO — o limiar é a variável certa?

A reclassificação sob A_regra saturou `impacto_emocional` (45,9% → 75,5%
das reviews). Em `barbie` ele ficou 65/70/70% nos três buckets: **lift
0,0pp**, discriminação nula. A fração de ruído do nulo de permutação subiu
de 34% para 41% a 20pp — não porque o nulo ficou mais forte (a média do
nulo CAIU, de 9,6 para 8,5 pares), mas porque o sinal encolheu contra o
teto de 100%.

A hipótese: **lift em pontos percentuais penaliza estruturalmente eixo
frequente.** Um eixo a 70% no bucket perdedor tem no máximo 30pp de espaço
para crescer; um a 25% tem 75pp. A mesma margem fixa cobra dos dois o mesmo
valor absoluto num espaço que não é o mesmo.

Três métricas, todas medindo a separação entre o bucket VENCEDOR e o
SEGUNDO colocado (mesma quantidade, escalas diferentes):

    L1  freq_top − freq_2o                       (atual, pontos percentuais)
    L2  (freq_top − freq_2o) / (1 − freq_2o)     (fração do espaço que sobrava)
    L3  ln OR entre top e 2o, com correção de    (log-odds)
        Haldane-Anscombe (+0,5 por célula)

**Por que a comparação exige calibrar o limiar de cada métrica, e não usar
o mesmo número nas três:** L1, L2 e L3 vivem em escalas diferentes — 0,20
em L1 é "20 pontos percentuais", em L2 é "20% do espaço disponível" e em L3
é "odds 22% maiores". Comparar cobertura a limiar nominal igual compararia
severidades diferentes e favoreceria arbitrariamente a métrica de escala
mais frouxa. O procedimento aqui é: para cada métrica, varrer o limiar até
achar o ponto em que a **fração de ruído** (esperado sob o nulo ÷ observado)
cai a um alvo comum, e só então comparar **cobertura** (filmes com ao menos
um eixo acima). Mesmo risco, cobertura diferente — aí a comparação é justa.

O nulo é o MESMO de `classificar_10._nulo`: 2000 rodadas, embaralhando o
rótulo de bucket DENTRO de cada filme (destrói a associação bucket↔eixo,
preserva tamanhos de bucket e frequência global do eixo naquele filme).
Reimplementado aqui porque `_nulo` calcula só L1 e devolve agregados; este
precisa das três métricas por par e por rodada.

Zero chamadas de LLM. Nenhuma mudança de produção.

Uso:
    python scripts/metricas_lift.py

Saída em `resultado/votacao-3/metricas_lift.json`.
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from classificar_10 import EIXOS, N_RODADAS_NULO, SEMENTE  # noqa: E402
from espectro24.buckets import FRONTEIRAS  # noqa: E402

SAIDA = RAIZ / "resultado" / "votacao-3"
ARQ_CONSENSO = SAIDA / "consenso.jsonl"
ARQ_CONSENSO_ANTIGO = SAIDA / "_arquivo_taxonomia-11871105c0d3" / "consenso.jsonl"
ARQ_SAIDA = SAIDA / "metricas_lift.json"

# Alvo de pureza para calibrar os limiares. 0,35 é o critério que a tarefa
# fixou ("fração de ruído ≤35%"); 0,34 é o que a margem de 20pp entregava no
# corpus ANTIGO, e serve de referência histórica.
ALVO_RUIDO = 0.35
COBERTURA_ALVO = 18  # de 35 filmes, o critério de "recupera cobertura"

BUCKETS = tuple(FRONTEIRAS)


# ===========================================================================
# As três métricas — todas sobre (k_top, n_top, k_2o, n_2o)
# ===========================================================================

def _l1(p_top: float, p_2o: float, *_) -> float:
    return p_top - p_2o


def _l2(p_top: float, p_2o: float, *_) -> float:
    """Fração do espaço que AINDA HAVIA para crescer acima do 2º colocado.

    Denominador `1 − p_2o` é exatamente o teto que a saturação come. Se o 2º
    está em 70%, sobram 30pp: subir 15pp é metade do possível (L2 = 0,50),
    não "15 pontos" como L1 leria. Indefinido quando `p_2o == 1` (não há
    espaço nenhum) — devolve 0,0, que é o valor honesto: um eixo que já está
    em 100% no segundo bucket não separa nada.
    """
    espaco = 1.0 - p_2o
    return (p_top - p_2o) / espaco if espaco > 1e-12 else 0.0


def _l3(p_top: float, p_2o: float, k_top: int, n_top: int,
        k_2o: int, n_2o: int) -> float:
    """log odds ratio com correção de Haldane-Anscombe (+0,5 por célula).

    A correção existe porque frequência 0 ou 1 é comum em bucket de 40
    reviews (e universal em `obsession-2026`, de 5 a 8), e OR sem correção
    diverge para infinito nesses casos. `+0,5` é a escolha padrão e é
    declarada aqui como parâmetro arbitrário: ela encolhe OR extremos em
    célula pequena, o que é conservador na direção certa.
    """
    o_top = (k_top + 0.5) / (n_top - k_top + 0.5)
    o_2o = (k_2o + 0.5) / (n_2o - k_2o + 0.5)
    return math.log(o_top / o_2o)


METRICAS = {
    "L1_absoluto": _l1,
    "L2_normalizado": _l2,
    "L3_log_odds": _l3,
}

# Grades de limiar por métrica — escalas diferentes, varredura fina o
# bastante para o ponto de corte não depender do passo.
GRADES = {
    "L1_absoluto": [round(0.01 * i, 4) for i in range(1, 61)],       # 0,01–0,60
    "L2_normalizado": [round(0.01 * i, 4) for i in range(1, 96)],    # 0,01–0,95
    "L3_log_odds": [round(0.05 * i, 4) for i in range(1, 81)],       # 0,05–4,00
}


# ===========================================================================
# Dados
# ===========================================================================

def _ler(caminho: Path) -> list[dict]:
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _por_filme(regs: list[dict]) -> dict[str, list[dict]]:
    d = defaultdict(list)
    for r in regs:
        d[r["slug"]].append(r)
    # Mesmo corte de `classificar_10._nulo` e de `relatorio`: bucket com
    # menos de 3 reviews não entra (nem no observado, nem no nulo).
    return {s: rr for s, rr in sorted(d.items())
            if min(sum(1 for r in rr if r["bucket"] == b) for b in BUCKETS) >= 3}


def _metricas_do_filme(regs: list[dict]) -> dict[str, dict]:
    """Para cada eixo: as três métricas, o bucket vencedor e as frequências."""
    porb = {b: [r for r in regs if r["bucket"] == b] for b in BUCKETS}
    saida = {}
    for e in EIXOS:
        contagem = {b: (sum(1 for r in v if e in r["eixos"]), len(v))
                    for b, v in porb.items()}
        # ordena por frequência; top = vencedor, 2o = runner-up
        ordem = sorted(BUCKETS,
                       key=lambda b: (contagem[b][0] / contagem[b][1]
                                      if contagem[b][1] else 0.0),
                       reverse=True)
        b_top, b_2o = ordem[0], ordem[1]
        k_top, n_top = contagem[b_top]
        k_2o, n_2o = contagem[b_2o]
        p_top = k_top / n_top if n_top else 0.0
        p_2o = k_2o / n_2o if n_2o else 0.0
        saida[e] = {
            "bucket": b_top,
            "freqs": {b: (contagem[b][0] / contagem[b][1]
                          if contagem[b][1] else 0.0) for b in BUCKETS},
            "valores": {nome: fn(p_top, p_2o, k_top, n_top, k_2o, n_2o)
                        for nome, fn in METRICAS.items()},
        }
    return saida


# ===========================================================================
# Nulo de permutação — as três métricas na MESMA permutação
# ===========================================================================

def _nulo_tres_metricas(por_filme: dict[str, list[dict]],
                        n_rodadas: int = N_RODADAS_NULO) -> dict:
    """Mesma permutação de `classificar_10._nulo`, medindo as 3 métricas.

    Calcular as três sobre a MESMA sequência de permutações (e não em três
    execuções separadas) elimina variação de sorteio da comparação entre
    elas: qualquer diferença que sobrar é da métrica, não do rng.
    """
    filmes = []
    for slug, regs in por_filme.items():
        tamanhos = [sum(1 for r in regs if r["bucket"] == b) for b in BUCKETS]
        filmes.append((slug, tamanhos,
                       [[e in r["eixos"] for e in EIXOS] for r in regs]))

    rng = random.Random(f"{SEMENTE}:metricas_lift")
    # acumuladores: por métrica, por limiar → lista de contagens por rodada
    acima = {m: {t: [] for t in GRADES[m]} for m in METRICAS}
    filmes_com_algum = {m: {t: [] for t in GRADES[m]} for m in METRICAS}

    for _ in range(n_rodadas):
        c_acima = {m: {t: 0 for t in GRADES[m]} for m in METRICAS}
        c_filmes = {m: {t: 0 for t in GRADES[m]} for m in METRICAS}
        for _slug, tamanhos, marcas in filmes:
            ordem = list(range(len(marcas)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos:
                fatias.append(ordem[ini:ini + t])
                ini += t
            # valores das 3 métricas para os 10 eixos deste filme
            vals = {m: [] for m in METRICAS}
            for i in range(len(EIXOS)):
                cont = [(sum(marcas[j][i] for j in fat), len(fat))
                        for fat in fatias]
                cont.sort(key=lambda kn: kn[0] / kn[1], reverse=True)
                (k_top, n_top), (k_2o, n_2o) = cont[0], cont[1]
                p_top, p_2o = k_top / n_top, k_2o / n_2o
                for m, fn in METRICAS.items():
                    vals[m].append(fn(p_top, p_2o, k_top, n_top, k_2o, n_2o))
            for m in METRICAS:
                for t in GRADES[m]:
                    n_ac = sum(1 for v in vals[m] if v >= t)
                    c_acima[m][t] += n_ac
                    c_filmes[m][t] += (n_ac > 0)
        for m in METRICAS:
            for t in GRADES[m]:
                acima[m][t].append(c_acima[m][t])
                filmes_com_algum[m][t].append(c_filmes[m][t])

    return {
        "n_rodadas": n_rodadas,
        "n_filmes": len(filmes),
        "n_pares": len(filmes) * len(EIXOS),
        "pares_acima_media": {
            m: {str(t): sum(xs) / len(xs) for t, xs in acima[m].items()}
            for m in METRICAS},
        "filmes_com_algum_media": {
            m: {str(t): sum(xs) / len(xs) for t, xs in filmes_com_algum[m].items()}
            for m in METRICAS},
    }


# ===========================================================================
# Varredura de limiar + calibração pelo alvo de ruído
# ===========================================================================

def _varredura(observado: dict[str, dict], nulo: dict) -> dict:
    """Para cada métrica e cada limiar: observado, nulo, ruído, cobertura."""
    saida = {}
    for m in METRICAS:
        linhas = []
        for t in GRADES[m]:
            pares = [(slug, e) for slug, d in observado.items()
                     for e, v in d.items() if v["valores"][m] >= t]
            n_obs = len(pares)
            n_nulo = nulo["pares_acima_media"][m][str(t)]
            filmes = {slug for slug, _ in pares}
            # fração de ruído = esperado sob o nulo ÷ observado. Mesma
            # definição de `votacao_3.entrega4.resumo_margem` (lá escrita
            # como razão de frações sobre o mesmo denominador, que cancela).
            ruido = (n_nulo / n_obs) if n_obs else None
            linhas.append({
                "limiar": t, "n_pares_acima": n_obs,
                "nulo_pares_acima_media": round(n_nulo, 2),
                "fracao_ruido": round(ruido, 4) if ruido is not None else None,
                "n_filmes_com_algum": len(filmes),
                "nulo_filmes_com_algum_media": round(
                    nulo["filmes_com_algum_media"][m][str(t)], 2),
            })
        saida[m] = linhas
    return saida


def _calibrar(varredura: dict, alvo: float = ALVO_RUIDO) -> dict:
    """Menor limiar cuja fração de ruído já é ≤ alvo — o ponto em que a
    métrica atinge a pureza pedida gastando o mínimo de cobertura."""
    saida = {}
    for m, linhas in varredura.items():
        escolhido = None
        for ln in linhas:
            if ln["fracao_ruido"] is not None and ln["fracao_ruido"] <= alvo:
                escolhido = ln
                break
        saida[m] = escolhido
    return saida


def _quantum(n_bucket: int = 40) -> list[dict]:
    """Quanto UMA review de diferença vale em cada métrica, por saturação.

    É o diagnóstico central da Entrega 1. Em L1 o quantum é constante
    (`1/n`, independente do nível de saturação). Em L2 ele é
    `(1/n) / (1 − p_2o)` — explode quando o 2º colocado encosta no teto.
    Ou seja: a normalização que deveria devolver poder de discriminação ao
    eixo saturado devolve, na mesma proporção, poder de RUÍDO — porque a
    diferença mínima observável também é amplificada.
    """
    passo = 1.0 / n_bucket
    base = passo / (1 - 0.25)
    return [{"p_segundo_colocado": p,
             "quantum_L1": round(passo, 4),
             "quantum_L2": round(passo / (1 - p), 4),
             "amplificacao_vs_p025": round((passo / (1 - p)) / base, 2)}
            for p in (0.25, 0.50, 0.70, 0.80, 0.90, 0.95)]


def _procedencia_do_ruido(por_filme: dict[str, list[dict]],
                          limiares: dict[str, float],
                          n_rodadas: int = 500) -> dict:
    """De QUAL eixo vem o ruído do nulo, por métrica.

    Se a normalização fosse neutra, o ruído se espalharia pelos 10 eixos.
    Concentração num eixo é a assinatura de que a métrica está amplificando
    flutuação de quantização naquele regime de frequência.
    """
    filmes = []
    for slug, regs in por_filme.items():
        tamanhos = [sum(1 for r in regs if r["bucket"] == b) for b in BUCKETS]
        filmes.append((tamanhos, [[e in r["eixos"] for e in EIXOS] for r in regs]))

    rng = random.Random(f"{SEMENTE}:procedencia")
    contagem = {m: defaultdict(int) for m in limiares}
    for _ in range(n_rodadas):
        for tamanhos, marcas in filmes:
            ordem = list(range(len(marcas)))
            rng.shuffle(ordem)
            fatias, ini = [], 0
            for t in tamanhos:
                fatias.append(ordem[ini:ini + t])
                ini += t
            for i, eixo in enumerate(EIXOS):
                cont = [(sum(marcas[j][i] for j in fat), len(fat)) for fat in fatias]
                cont.sort(key=lambda kn: kn[0] / kn[1], reverse=True)
                (k1, n1), (k2, n2) = cont[0], cont[1]
                for m, lim in limiares.items():
                    if METRICAS[m](k1 / n1, k2 / n2, k1, n1, k2, n2) >= lim:
                        contagem[m][eixo] += 1

    saida = {}
    for m, lim in limiares.items():
        total = sum(contagem[m].values()) or 1
        saida[m] = {
            "limiar": lim,
            "pares_ruido_por_rodada": round(total / n_rodadas, 2),
            "por_eixo": {
                e: {"por_rodada": round(c / n_rodadas, 3),
                    "fracao_do_ruido": round(c / total, 4)}
                for e, c in sorted(contagem[m].items(), key=lambda kv: -kv[1])},
        }
    return saida


def _por_eixo_no_limiar(observado: dict[str, dict], metrica: str,
                        limiar: float) -> dict:
    """Distribuição por eixo dos pares acima do limiar + quem ENCABEÇA
    (maior valor da métrica no filme, entre os que passam)."""
    contagem, encabeca = defaultdict(int), defaultdict(int)
    por_filme_top = {}
    for slug, d in observado.items():
        acima = {e: v["valores"][metrica] for e, v in d.items()
                 if v["valores"][metrica] >= limiar}
        for e in acima:
            contagem[e] += 1
        if acima:
            campeao = max(acima, key=acima.get)
            encabeca[campeao] += 1
            por_filme_top[slug] = campeao
    return {
        "pares_por_eixo": dict(sorted(contagem.items(), key=lambda kv: -kv[1])),
        "encabeca_por_eixo": dict(sorted(encabeca.items(), key=lambda kv: -kv[1])),
        "eixo_que_encabeca_por_filme": dict(sorted(por_filme_top.items())),
    }


# ===========================================================================
# Entrega 2 — eixos de cobertura vs eixos de contraste
# ===========================================================================

# Os 2 bullets de consenso do desenho são por FREQUÊNCIA; os 3 de contraste
# por LIFT. Um eixo alto em frequência e baixo em lift pertence ao primeiro
# grupo por construção — a pergunta é quantos são, e o que sobra sem eles.
N_EIXOS_CONSENSO = 2


def entrega2(observado: dict[str, dict], consenso: list[dict],
             metrica: str, limiar: float) -> dict:
    n_total = len(consenso)
    freq_global = {e: sum(1 for r in consenso if e in r["eixos"]) / n_total
                   for e in EIXOS}
    lift_medio = {
        e: sum(d[e]["valores"][metrica] for d in observado.values()) / len(observado)
        for e in EIXOS}
    freq_media_filmes = {
        e: sum(max(d[e]["freqs"].values()) for d in observado.values()) / len(observado)
        for e in EIXOS}

    tabela = sorted(
        ({"eixo": e, "freq_global": freq_global[e],
          "freq_media_no_melhor_bucket": freq_media_filmes[e],
          "lift_medio": lift_medio[e]} for e in EIXOS),
        key=lambda x: -x["freq_global"])

    # Candidatos a "eixo de consenso": alto em frequência, baixo em lift.
    # Critério declarado: acima da mediana de frequência E abaixo da mediana
    # de lift — quadrante "frequente e pouco discriminante".
    def _mediana(xs):
        xs = sorted(xs)
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    med_freq = _mediana(list(freq_global.values()))
    med_lift = _mediana(list(lift_medio.values()))
    quadrante = sorted(
        (e for e in EIXOS
         if freq_global[e] > med_freq and lift_medio[e] < med_lift),
        key=lambda e: -freq_global[e])

    # Os N mais frequentes são os que o desenho de bullets já consumiria
    # como "consenso" — é esse o conjunto cuja exclusão importa medir.
    consenso_top = [t["eixo"] for t in tabela[:N_EIXOS_CONSENSO]]

    def sem_contraste(excluidos: set[str]) -> list[str]:
        fora = []
        for slug, d in observado.items():
            tem = any(v["valores"][metrica] >= limiar
                      for e, v in d.items() if e not in excluidos)
            if not tem:
                fora.append(slug)
        return sorted(fora)

    cenarios = {
        "nenhum_excluido": sem_contraste(set()),
        f"excluindo_top{N_EIXOS_CONSENSO}_frequencia": sem_contraste(set(consenso_top)),
        "excluindo_quadrante_frequente_e_pouco_discriminante": sem_contraste(set(quadrante)),
    }

    return {
        "metrica_usada": metrica, "limiar_usado": limiar,
        "mediana_freq_global": med_freq, "mediana_lift_medio": med_lift,
        "tabela_por_eixo": tabela,
        "candidatos_a_eixo_de_consenso_quadrante": quadrante,
        f"top{N_EIXOS_CONSENSO}_frequencia": consenso_top,
        "filmes_sem_nenhum_bullet_de_contraste": {
            k: {"n": len(v), "filmes": v} for k, v in cenarios.items()},
        "n_filmes_avaliados": len(observado),
    }


# ===========================================================================
def main() -> None:
    consenso = _ler(ARQ_CONSENSO)
    por_filme = _por_filme(consenso)
    observado = {slug: _metricas_do_filme(regs) for slug, regs in por_filme.items()}

    print(f"{len(por_filme)} filmes · {len(EIXOS)} eixos · "
          f"{len(por_filme) * len(EIXOS)} pares · nulo com {N_RODADAS_NULO} rodadas")
    nulo = _nulo_tres_metricas(por_filme)
    varredura = _varredura(observado, nulo)
    calibrado = _calibrar(varredura)

    # Referência histórica: L1 a 20pp (a margem recomendada antes da
    # saturação) sobre o corpus ANTIGO e sobre o NOVO.
    l1_20 = next(ln for ln in varredura["L1_absoluto"] if ln["limiar"] == 0.20)

    detalhe = {}
    for m, ln in calibrado.items():
        if ln:
            detalhe[m] = _por_eixo_no_limiar(observado, m, ln["limiar"])

    # `barbie` sob cada métrica — o caso que motivou a pergunta.
    barbie = {}
    if "barbie" in observado:
        d = observado["barbie"]
        for m in METRICAS:
            campeao = max(d, key=lambda e: d[e]["valores"][m])
            barbie[m] = {
                "melhor_eixo": campeao,
                "valor_melhor": round(d[campeao]["valores"][m], 4),
                "impacto_emocional": round(d["impacto_emocional"]["valores"][m], 4),
                "impacto_emocional_freqs": d["impacto_emocional"]["freqs"],
                "passa_no_limiar_calibrado": (
                    d["impacto_emocional"]["valores"][m] >= calibrado[m]["limiar"]
                    if calibrado[m] else None),
            }

    # Entrega 2 roda sob a métrica que SOBREVIVE à Entrega 1 (ver relatório:
    # L2 e L3 nunca atingem o alvo de ruído). Dois limiares, para separar o
    # que é conclusão do que é escolha de corte: 0,19 (o ponto de cobertura
    # 18/35) e 0,25 (pureza confortável).
    e2 = {str(t): entrega2(observado, consenso, "L1_absoluto", t)
          for t in (0.19, 0.25)}

    # Melhor ponto COM cobertura ≥ alvo, por métrica — a outra ponta do
    # trade-off (a calibração acima fixa pureza e deixa a cobertura cair).
    melhor_com_cobertura = {}
    for m, linhas in varredura.items():
        cands = [ln for ln in linhas
                 if ln["fracao_ruido"] is not None
                 and ln["n_filmes_com_algum"] >= COBERTURA_ALVO]
        melhor_com_cobertura[m] = (min(cands, key=lambda ln: ln["fracao_ruido"])
                                   if cands else None)

    limiares_diag = {m: (melhor_com_cobertura[m]["limiar"]
                         if melhor_com_cobertura[m] else GRADES[m][len(GRADES[m]) // 2])
                     for m in METRICAS}
    procedencia = _procedencia_do_ruido(por_filme, limiares_diag)

    rel = {
        "fonte": str(ARQ_CONSENSO.relative_to(RAIZ)),
        "n_filmes": len(por_filme), "n_pares": len(por_filme) * len(EIXOS),
        "alvo_ruido": ALVO_RUIDO, "cobertura_alvo": COBERTURA_ALVO,
        "nulo": {k: nulo[k] for k in ("n_rodadas", "n_filmes", "n_pares")},
        "referencia_L1_a_20pp": l1_20,
        "limiar_calibrado_por_metrica": calibrado,
        "melhor_ruido_com_cobertura_alvo": melhor_com_cobertura,
        "quantum_por_saturacao": _quantum(),
        "procedencia_do_ruido": procedencia,
        "varredura": varredura,
        "detalhe_por_eixo_no_limiar_calibrado": detalhe,
        "barbie": barbie,
        "entrega2_cobertura_vs_contraste": e2,
    }
    ARQ_SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"\n=== REFERENCIA: L1 a 20pp (margem recomendada pre-saturacao) ===")
    print(f"  pares {l1_20['n_pares_acima']} · nulo {l1_20['nulo_pares_acima_media']} "
          f"· ruido {l1_20['fracao_ruido']:.1%} · filmes {l1_20['n_filmes_com_algum']}/35")

    print(f"\n=== LIMIAR CALIBRADO PARA RUIDO <= {ALVO_RUIDO:.0%} ===")
    print(f"{'metrica':<18}{'limiar':>9}{'pares':>8}{'nulo':>8}{'ruido':>9}"
          f"{'filmes':>9}{'nulo_filmes':>13}")
    for m, ln in calibrado.items():
        if not ln:
            print(f"{m:<18}{'-- nunca atinge o alvo --':>50}")
            continue
        print(f"{m:<18}{ln['limiar']:>9.2f}{ln['n_pares_acima']:>8}"
              f"{ln['nulo_pares_acima_media']:>8.1f}{ln['fracao_ruido']:>8.1%}"
              f"{ln['n_filmes_com_algum']:>9}{ln['nulo_filmes_com_algum_media']:>13.1f}")

    print(f"\n=== A OUTRA PONTA: menor ruido COM cobertura >= {COBERTURA_ALVO}/35 ===")
    for m, ln in melhor_com_cobertura.items():
        if ln:
            print(f"  {m:<18} limiar {ln['limiar']:>5.2f} · ruido {ln['fracao_ruido']:>6.1%} "
                  f"· pares {ln['n_pares_acima']:>3} · filmes {ln['n_filmes_com_algum']}/35")
        else:
            print(f"  {m:<18} nunca alcanca cobertura {COBERTURA_ALVO}/35")

    print(f"\n  CRITERIO DA TAREFA (cobertura >= {COBERTURA_ALVO}/35 E ruido <= {ALVO_RUIDO:.0%}):")
    for m, ln in melhor_com_cobertura.items():
        ok = (ln is not None and ln["fracao_ruido"] <= ALVO_RUIDO)
        detalhe_txt = (f"melhor ruido com cobertura = {ln['fracao_ruido']:.1%}"
                       if ln else "cobertura inatingivel")
        print(f"    {m:<18} {'SIM' if ok else 'NAO':<4} ({detalhe_txt})")

    print(f"\n=== POR QUE: quantum de 1 review (bucket n=40) por saturacao ===")
    print(f"{'p_2o':<10}{'L1':>10}{'L2':>10}{'amplificacao':>15}")
    for q in rel["quantum_por_saturacao"]:
        print(f"{q['p_segundo_colocado']:<10.2f}{q['quantum_L1']:>10.3f}"
              f"{q['quantum_L2']:>10.3f}{q['amplificacao_vs_p025']:>14.1f}x")

    print(f"\n=== POR QUE: de qual eixo vem o ruido do nulo ===")
    for m, p in procedencia.items():
        top = list(p["por_eixo"].items())[:3]
        print(f"  {m:<18} @ {p['limiar']:.2f} — {p['pares_ruido_por_rodada']:.1f} pares/rodada")
        for e, v in top:
            print(f"      {e:<20} {v['fracao_do_ruido']:>6.1%} do ruido")

    print(f"\n=== BARBIE ===")
    for m, b in barbie.items():
        print(f"  {m:<18} melhor={b['melhor_eixo']} ({b['valor_melhor']}) · "
              f"impacto_emocional={b['impacto_emocional']} · "
              f"passa={b['passa_no_limiar_calibrado']}")

    base = e2["0.19"]
    print(f"\n=== ENTREGA 2 — frequencia vs lift por eixo (L1) ===")
    print(f"{'eixo':<20}{'freq_global':>13}{'lift_medio':>12}")
    for t in base["tabela_por_eixo"]:
        print(f"{t['eixo']:<20}{t['freq_global']:>12.1%}{t['lift_medio']:>12.3f}")
    print(f"\n  quadrante frequente+pouco discriminante: "
          f"{base['candidatos_a_eixo_de_consenso_quadrante']}")
    print(f"  top{N_EIXOS_CONSENSO} por frequencia: "
          f"{base[f'top{N_EIXOS_CONSENSO}_frequencia']}")
    for lim, bloco in e2.items():
        print(f"\n  --- filmes SEM nenhum bullet de contraste, L1 @ {lim} ---")
        for k, v in bloco["filmes_sem_nenhum_bullet_de_contraste"].items():
            print(f"    {k:<52} {v['n']:>2}/35")

    print(f"\n→ {ARQ_SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
