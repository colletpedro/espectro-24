"""[Entregas 2-3] Duas variantes do prompt contra o gabarito humano das 100.

O defeito que estas variantes atacam (auditoria de 2026-08-13, ver
`resultado/auditoria-acuracia/metricas_relatorio.json`): em review de até 200
caracteres o recall micro é 0,35, contra 0,88 acima de 400 — com a precisão
ESTÁVEL em 0,87-0,93 em toda faixa. O modelo não troca de eixo em texto
curto: ele omite eixo. 27 das 100 reviews ficaram com recall zero, 23 delas
com ≤200 chars, e em 12 as três passadas foram unânimes em `livre`.

Lendo as 27 à mão, a causa aparece nas REGRAS, não nas definições de eixo:

  - a regra 2 (`Seja ESTRITO`) foi escrita para barrar elogio vazio
    ("obra-prima", "amei") e, em texto curto, passa a barrar quase tudo:
    sobra pouca evidência e o modelo resolve a dúvida para o lado de não
    atribuir;
  - a regra 5 (`só xingamento, só piada solta` → `livre`) é lida como se
    valesse por FORMA. Mas review curta costuma ser piada — e a piada é
    SOBRE o filme. "os personagens são tão tontos" é piada e é
    `roteiro_estrutura`; "eu não gostei" é seco e é `impacto_emocional`.

Daí as duas variantes, que diferem em UMA coisa só, para o A/B ser legível:

  A (`regra`)     — só mexe nas REGRAS. Diz que brevidade não é ausência, e
                    redefine `livre` por ASSUNTO (a review não fala do filme)
                    em vez de por PROFUNDIDADE (fala pouco do filme).
  B (`fewshot`)   — as MESMAS regras de A, mais 6 exemplos resolvidos de
                    review curta, cobrindo `impacto_emocional` e
                    `roteiro_estrutura` (os dois eixos mais perdidos) e dois
                    casos de `livre` legítimo, que existem para segurar a
                    precisão.

Nenhuma das duas toca a lista de eixos nem as definições dos 10 eixos — só
o bloco REGRAS, que é onde a evidência aponta.

Os exemplos few-shot vêm do corpus de produção mas de FORA das 100
auditadas (conferido em `_conferir_fewshot_fora_da_auditoria`): treinar no
conjunto de teste inflaria o resultado da Entrega 3.

Transporte: sempre pelo adaptador (`deepseek_client`/`deepseek_resposta`/
`deepseek_uso`), como manda o guard-rail da v1.9.4.

Uso:
    python scripts/variantes_prompt_curtas.py passes         # 3 passadas x 2 variantes (LLM, centavos)
    python scripts/variantes_prompt_curtas.py comparar       # consenso + métricas vs baseline
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
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
    SYSTEM as SYSTEM_BASELINE,
    _normalizar,
    recuperar_eixo,
)
from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
)

SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "variantes"
ARQ_COMPARACAO = SAIDA / "comparacao.json"

CONCORRENCIA = 8
MAX_TENTATIVAS = 3
N_PASSES = 3


# ===========================================================================
# O bloco de regras — o único trecho que as variantes mexem
# ===========================================================================

# Preâmbulo e definições dos 10 eixos são recortados do SYSTEM de produção,
# literalmente: se a definição de um eixo mudar lá, muda aqui junto, e a
# variante continua sendo "o prompt de produção com outras regras".
_CABECALHO = SYSTEM_BASELINE.split("REGRAS:")[0]
_FORMATO = """

Responda APENAS com um objeto JSON, sem cercas de código, exatamente neste formato:
{"eixos": ["..."], "temas_livres": ["..."]}"""

# --- Regras compartilhadas por A e B -------------------------------------
# Mudanças em relação ao baseline, e por quê:
#   [1] inalterada.
#   [2] mantém "elogio vazio não é eixo" — é o que segura a precisão, que
#       está boa e não pode cair. Mas passa a dizer que um efeito DECLARADO
#       conta mesmo quando é dito em três palavras, que é o caso das 27.
#   [3] `livre` redefinido por ASSUNTO, não por profundidade. É a mudança
#       principal: "fala pouco do filme" deixa de ser motivo de `livre`.
#   [4] inalterada.
#   [5] reescrita: a lista "só xingamento, só piada solta" virava licença
#       para mandar para `livre` qualquer review de forma informal. Agora o
#       critério é o assunto, e a piada SOBRE o filme volta a ser eixo.
#   [6] NOVA. Nomeia o viés medido, na direção medida.
#   [7] inalterada (era a 6).
_REGRAS_NOVAS = """REGRAS:
1. Atribua TODOS os eixos que a review realmente menciona, e SÓ esses. Uma review pode ter vários eixos, ou um só.
2. Só atribua um eixo se a review disser algo sobre ele. Nota alta ou entusiasmo genérico SEM descrever efeito nenhum ("obra-prima", "amei", "5 estrelas", "peak cinema") NÃO é impacto_emocional nem nenhum outro eixo — é elogio sem eixo. Mas um efeito DECLARADO é eixo mesmo dito em três palavras: "chorei", "não gostei", "odiei", "me deu sono", "passei mal", "ri alto" são impacto_emocional.
3. "livre" é sobre ASSUNTO, não sobre tamanho. Use "livre" quando a review fala de outra coisa que não o filme: a logística da sessão (legenda, dublagem, cinema, streaming, avião), a vida de quem escreveu, uma piada sobre outro assunto, um recado para outra pessoa. NÃO use "livre" só porque a review é curta ou diz pouco.
4. Sempre que incluir "livre", escreva em `temas_livres` de 1 a 2 rótulos curtos (2 a 4 palavras, em português, minúsculas) descrevendo o que não coube.
5. Uma review pode ter "livre" JUNTO com eixos: a parte que fala do filme vira eixo, a parte que não fala vira "livre". Devolva `["livre"]` sozinho só quando NADA na review fala do filme.
6. Review curta menciona POUCOS eixos, não ZERO eixos. Brevidade não é ausência de conteúdo. Uma frase seca sobre os personagens é roteiro_estrutura; um xingamento ao filme é impacto_emocional; uma piada cujo alvo é o enredo é roteiro_estrutura. Na dúvida entre atribuir o eixo que a review claramente toca e devolver "livre", atribua o eixo.
7. NÃO conte nada. NÃO some. NÃO comente. Devolva só o JSON."""

# --- Few-shot, exclusivo da variante B -----------------------------------
# Seis exemplos, todos ≤200 chars, todos de FORA das 100 auditadas.
# Quatro cobrem os eixos mais perdidos (`impacto_emocional`,
# `roteiro_estrutura`); dois são `livre` legítimo e existem para que o
# few-shot não vire licença para atribuir eixo em tudo — se a precisão cair,
# é aqui que se mexe primeiro.
_FEWSHOT = """

EXEMPLOS RESOLVIDOS (reviews curtas, o caso em que mais se erra):

Review: "Somehow this movie is trying to convince me that Hawkeye taking a sabbatical, moving to Japan to master the language and learn to wield some katana is bad character development"
{"eixos": ["roteiro_estrutura"], "temas_livres": []}
(fala do desenvolvimento de um personagem — é roteiro_estrutura, ainda que em tom de deboche.)

Review: "the most overrated movie in history. it is so, so, so bad. there is no depth or anything. just a fuckin mess"
{"eixos": ["roteiro_estrutura", "expectativa"], "temas_livres": []}
("sem profundidade / uma bagunça" é um juízo sobre a obra: roteiro_estrutura. "overrated" é expectativa. Xingar não anula o conteúdo.)

Review: "The absolute hatred I have for this film should go undocumented, I honestly can't remember why I feel this way towards it but I refuse to watch this excuse of a movie again to remind myself."
{"eixos": ["impacto_emocional"], "temas_livres": []}
(ódio declarado ao filme é efeito declarado: impacto_emocional. Não descrever a causa não anula a reação.)

Review: "they made her so insufferable, i wouldnt be friends with her either. my 8th grade experience was also shitty but the only thing i relate to about her is being awkward. this is straight up buns"
{"eixos": ["roteiro_estrutura", "impacto_emocional"], "temas_livres": []}
(como a personagem foi escrita = roteiro_estrutura; identificar-se ou não com ela = impacto_emocional. Duas coisas em uma linha.)

Review: "Girl this is not my thing at all. I had to watch this for uni and the link my tutor sent was 240p and buffered every 60 seconds. An all-round miserable experience"
{"eixos": ["impacto_emocional", "livre"], "temas_livres": ["qualidade da transmissão", "assistir por obrigação"]}
("not my thing" é reação ao filme; a qualidade do stream e o motivo de ter assistido não são eixo — os dois convivem.)

Review: "Banco Itaú instituição canalha sem alma bandidos de terno e gravata Fogo no banco Itaú até o último tijolo"
{"eixos": ["livre"], "temas_livres": ["protesto contra banco"]}
(não diz NADA sobre o filme — este é o caso em que "livre" sozinho é certo.)"""


SYSTEM_A = _CABECALHO + _REGRAS_NOVAS + _FORMATO
SYSTEM_B = _CABECALHO + _REGRAS_NOVAS + _FEWSHOT + _FORMATO

VARIANTES = {
    "baseline": SYSTEM_BASELINE,
    "A_regra": SYSTEM_A,
    "B_fewshot": SYSTEM_B,
}
# `baseline` não é reclassificado: a comparação usa o `gabarito_modelo.json`
# já em disco, que é o consenso de produção sobre estas mesmas 100.
VARIANTES_A_RODAR = ("A_regra", "B_fewshot")


# ===========================================================================
# Higiene do few-shot
# ===========================================================================

def _conferir_fewshot_fora_da_auditoria() -> None:
    """Nenhum exemplo do few-shot pode sair das 100 auditadas.

    A checagem é por trecho literal do texto da review: se um dos exemplos
    tivesse sido copiado de dentro do conjunto de teste, a Entrega 3 estaria
    medindo memorização, não generalização.
    """
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    auditadas = {r["id"] for r in idx["reviews"]}
    amostra = json.loads(
        (RAIZ / "resultado" / "votacao-3" / "amostra.json").read_text(encoding="utf-8"))
    textos_auditados = [r["texto"] for r in amostra["reviews"]
                        if r["id"] in auditadas]
    # Trechos-âncora de cada exemplo do few-shot.
    ancoras = [
        "Hawkeye taking a sabbatical",
        "the most overrated movie in history",
        "absolute hatred I have for this film",
        "they made her so insufferable",
        "the link my tutor sent was 240p",
        "Banco Ita",
    ]
    for a in ancoras:
        for t in textos_auditados:
            if a in t:
                raise SystemExit(
                    f"few-shot contaminado: o exemplo ancorado em {a!r} está "
                    f"dentro das 100 auditadas — trocar por um de fora.")


# ===========================================================================
# Passadas
# ===========================================================================

def _reviews_da_auditoria() -> list[dict]:
    """As 100 auditadas, com texto — na ordem do índice."""
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    amostra = json.loads(
        (RAIZ / "resultado" / "votacao-3" / "amostra.json").read_text(encoding="utf-8"))
    por_id = {r["id"]: r for r in amostra["reviews"]}
    saida = []
    for r in idx["reviews"]:
        base = por_id[r["id"]]
        saida.append({**r, "texto": base["texto"]})
    return saida


def _arq_passe(variante: str, n: int) -> Path:
    return SAIDA / f"{variante}_passe_{n}.jsonl"


def rodar_passe(variante: str, n_passe: int, reviews: list[dict]) -> None:
    """Uma passada de uma variante — retomável, uma linha JSONL por review."""
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
                registro = {
                    "ok": True, "variante": variante, "passe": n_passe,
                    "id": review["id"], "bucket": review["bucket"],
                    "nivel": review["nivel"], "n_chars": review["n_chars"],
                    "eixos": eixos, "temas_livres": livres,
                    "eixos_invalidos": invalidos, "uso": deepseek_uso(resp),
                }
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
                      f"{time.time() - t0:.0f}s")

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as ex:
        list(ex.map(tarefa, pendentes))
    saida.close()


def cmd_passes() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    _conferir_fewshot_fora_da_auditoria()
    SAIDA.mkdir(parents=True, exist_ok=True)
    reviews = _reviews_da_auditoria()
    print(f"{len(reviews)} reviews · {len(VARIANTES_A_RODAR)} variantes · "
          f"{N_PASSES} passadas")
    for variante in VARIANTES_A_RODAR:
        for n in range(1, N_PASSES + 1):
            rodar_passe(variante, n, reviews)


# ===========================================================================
# Consenso + métricas
# ===========================================================================

def _ler_passe(variante: str, n: int) -> dict[str, list[str]]:
    arq = _arq_passe(variante, n)
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


def consenso_da_variante(variante: str) -> dict[str, dict]:
    """Mesma regra de `votacao_3._consensuar`: eixo entra com ≥2 de 3 votos,
    e só entra review com as três passadas completas."""
    passes = [_ler_passe(variante, n) for n in range(1, N_PASSES + 1)]
    ids = set(passes[0]) & set(passes[1]) & set(passes[2])
    gabarito = {}
    for rid in sorted(ids):
        por_passe = [p[rid] for p in passes]
        votos = Counter(e for eixos in por_passe for e in eixos)
        finais = sorted(e for e, v in votos.items() if v >= 2)
        if not finais:
            confianca = "vazio"
        elif all(votos[e] == 3 for e in finais):
            confianca = "unanime"
        else:
            confianca = "maioria"
        gabarito[rid] = {
            "eixos": finais,
            "votos": {e: votos[e] for e in sorted(votos)},
            "confianca": confianca,
            "eixos_por_passe": por_passe,
        }
    return gabarito


def _micro(bloco: dict) -> dict:
    """Precisão/recall micro de um bloco `por_eixo` — soma tp/fp/fn e divide.

    Micro, e não macro, porque a pergunta é sobre VOLUME de sinal perdido:
    um eixo raro não deve pesar igual a um frequente na conta do viés.
    """
    tp = sum(v["tp"] for v in bloco.values())
    fp = sum(v["fp"] for v in bloco.values())
    fn = sum(v["fn"] for v in bloco.values())
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precisao": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
    }


def _diagnostico(anotacoes: dict, gabarito: dict) -> dict:
    """Os dois contadores que motivaram a correção, recalculados."""
    recall_zero, vazios = 0, 0
    for rid, g in gabarito.items():
        humano = set(anotacoes[rid]["eixos"]) - {"livre"}
        modelo = set(g["eixos"]) - {"livre"}
        if humano and not (humano & modelo):
            recall_zero += 1
        if g["confianca"] == "vazio":
            vazios += 1
    return {"reviews_com_recall_zero": recall_zero, "consensos_vazios": vazios}


SEMENTE_BOOTSTRAP = 20260813
N_BOOTSTRAP = 5000


def _bootstrap(anotacoes: dict, gabaritos: dict, meta: dict) -> dict:
    """Bootstrap PAREADO por review — variante e baseline reamostrados juntos.

    n=100 é pouco para tratar qualquer diferença como dada. O pareamento
    (mesma reamostragem de reviews para as duas colunas) cancela a variação
    que vem do sorteio da amostra e deixa só a diferença entre prompts, que é
    o que se quer decidir. IC95 percentil sobre a DIFERENÇA: se cruza zero, a
    amostra não sustenta o ganho, por maior que o ponto central pareça.
    """
    import random

    eixos = set(EIXOS)
    ids = sorted(anotacoes)

    def pr(sub: list[str], g: dict) -> tuple[float, float, float]:
        tp = fp = fn = 0
        for rid in sub:
            humano = set(anotacoes[rid]["eixos"]) & eixos
            modelo = set(g[rid]["eixos"]) & eixos
            tp += len(humano & modelo)
            fp += len(modelo - humano)
            fn += len(humano - modelo)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return p, r, (2 * p * r / (p + r) if p + r else 0.0)

    rng = random.Random(SEMENTE_BOOTSTRAP)
    variantes = [k for k in gabaritos if k != "baseline"]
    acc = {k: {m: [] for m in ("recall_ate_200", "recall_geral",
                               "precisao_geral", "f1_geral")}
           for k in variantes}
    for _ in range(N_BOOTSTRAP):
        amostra = [rng.choice(ids) for _ in ids]
        curtas = [r for r in amostra if meta[r]["n_chars"] <= 200]
        b_geral = pr(amostra, gabaritos["baseline"])
        b_curtas = pr(curtas, gabaritos["baseline"]) if curtas else (0.0, 0.0, 0.0)
        for k in variantes:
            v_geral = pr(amostra, gabaritos[k])
            v_curtas = pr(curtas, gabaritos[k]) if curtas else (0.0, 0.0, 0.0)
            acc[k]["recall_ate_200"].append(v_curtas[1] - b_curtas[1])
            acc[k]["recall_geral"].append(v_geral[1] - b_geral[1])
            acc[k]["precisao_geral"].append(v_geral[0] - b_geral[0])
            acc[k]["f1_geral"].append(v_geral[2] - b_geral[2])

    saida = {}
    for k, ms in acc.items():
        saida[k] = {}
        for m, xs in ms.items():
            xs.sort()
            lo, hi = xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]
            saida[k][m] = {
                "delta_mediano": round(xs[len(xs) // 2], 4),
                "ic95": [round(lo, 4), round(hi, 4)],
                "cruza_zero": lo <= 0 <= hi,
            }
    return saida


def _metricas_com_gabarito(anotacoes: dict, gabarito: dict | None) -> dict:
    """Roda `aa.calcular_metricas` contra um gabarito arbitrário.

    `calcular_metricas` lê `aa.ARQ_GABARITO` de dentro do corpo; trocar a
    constante é o jeito de reusar a MESMA função de métrica do baseline sem
    duplicar a lógica — o que garante que a comparação é maçã com maçã.
    """
    if gabarito is None:
        return aa.calcular_metricas(anotacoes)
    tmp = SAIDA / "_gabarito_tmp.json"
    tmp.write_text(json.dumps(gabarito, ensure_ascii=False), encoding="utf-8")
    original = aa.ARQ_GABARITO
    try:
        aa.ARQ_GABARITO = tmp
        return aa.calcular_metricas(anotacoes)
    finally:
        aa.ARQ_GABARITO = original
        tmp.unlink(missing_ok=True)


def cmd_comparar() -> None:
    anotacoes = aa.ler_anotacoes_humanas()
    gabaritos = {"baseline": None}
    for v in VARIANTES_A_RODAR:
        g = consenso_da_variante(v)
        if len(g) != len(anotacoes):
            print(f"AVISO: {v} tem {len(g)}/{len(anotacoes)} reviews com as "
                  f"3 passadas completas — rode `passes` de novo.")
        gabaritos[v] = g

    rel = {}
    for nome, g in gabaritos.items():
        m = _metricas_com_gabarito(anotacoes, g)
        gab_efetivo = g if g is not None else json.loads(
            aa.ARQ_GABARITO.read_text(encoding="utf-8"))
        rel[nome] = {
            "n": m["n_pares"],
            "concordancia_exata": m["geral"]["concordancia_exata"],
            "micro_geral": _micro(m["geral"]["por_eixo"]),
            "por_faixa": {f: _micro(b["por_eixo"])
                          for f, b in m["por_faixa_n_chars"].items()},
            "eixos_criticos": {
                e: {"precisao": m["geral"]["por_eixo"][e]["precisao"],
                    "recall": m["geral"]["por_eixo"][e]["recall"],
                    "tp": m["geral"]["por_eixo"][e]["tp"],
                    "fp": m["geral"]["por_eixo"][e]["fp"],
                    "fn": m["geral"]["por_eixo"][e]["fn"]}
                for e in ("impacto_emocional", "roteiro_estrutura")
            },
            "por_eixo": {e: {"precisao": m["geral"]["por_eixo"][e]["precisao"],
                             "recall": m["geral"]["por_eixo"][e]["recall"]}
                         for e in EIXOS},
            "diagnostico": _diagnostico(anotacoes, gab_efetivo),
        }

    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    meta = {r["id"]: r for r in idx["reviews"]}
    gab_completos = dict(gabaritos)
    gab_completos["baseline"] = json.loads(
        aa.ARQ_GABARITO.read_text(encoding="utf-8"))
    rel["_bootstrap_vs_baseline"] = _bootstrap(anotacoes, gab_completos, meta)

    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_COMPARACAO.write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    _imprimir(rel)
    print(f"\n→ {ARQ_COMPARACAO.relative_to(RAIZ)}")


def _imprimir(rel: dict) -> None:
    nomes = [k for k in rel if not k.startswith("_")]
    FAIXAS = ["<=200 (piso)", "201-400", "401-800", "801+"]

    print("\n=== RECALL MICRO POR FAIXA DE n_chars (o numero que motivou a correcao) ===")
    print(f"{'faixa':<16}" + "".join(f"{n:>14}" for n in nomes))
    for f in FAIXAS:
        linha = f"{f:<16}"
        for n in nomes:
            r = rel[n]["por_faixa"][f]["recall"]
            linha += f"{r:>14.3f}" if r is not None else f"{'-':>14}"
        print(linha)

    print("\n=== PRECISAO MICRO POR FAIXA (nao pode cair) ===")
    print(f"{'faixa':<16}" + "".join(f"{n:>14}" for n in nomes))
    for f in FAIXAS:
        linha = f"{f:<16}"
        for n in nomes:
            p = rel[n]["por_faixa"][f]["precisao"]
            linha += f"{p:>14.3f}" if p is not None else f"{'-':>14}"
        print(linha)

    print("\n=== GERAL ===")
    for rotulo, chave in (("precisao micro", "precisao"), ("recall micro", "recall")):
        linha = f"{rotulo:<16}"
        for n in nomes:
            linha += f"{rel[n]['micro_geral'][chave]:>14.3f}"
        print(linha)
    linha = f"{'concord. exata':<16}"
    for n in nomes:
        linha += f"{rel[n]['concordancia_exata']:>14.3f}"
    print(linha)

    print("\n=== EIXOS MAIS PERDIDOS ===")
    for e in ("impacto_emocional", "roteiro_estrutura"):
        print(f"  {e}")
        for rotulo in ("precisao", "recall"):
            linha = f"    {rotulo:<12}"
            for n in nomes:
                v = rel[n]["eixos_criticos"][e][rotulo]
                linha += f"{v:>14.3f}" if v is not None else f"{'-':>14}"
            print(linha)

    print("\n=== DIAGNOSTICO ===")
    for chave, rotulo in (("reviews_com_recall_zero", "recall zero (era 27)"),
                          ("consensos_vazios", "consenso vazio (era 8)")):
        linha = f"  {rotulo:<24}"
        for n in nomes:
            linha += f"{rel[n]['diagnostico'][chave]:>14d}"
        print(linha)

    boot = rel.get("_bootstrap_vs_baseline")
    if boot:
        print(f"\n=== BOOTSTRAP PAREADO vs baseline (B={N_BOOTSTRAP}, n=100) ===")
        rotulos = {"recall_ate_200": "recall <=200", "recall_geral": "recall geral",
                   "precisao_geral": "precisao geral", "f1_geral": "F1 geral"}
        for k, ms in boot.items():
            print(f"  {k}")
            for m, rot in rotulos.items():
                d = ms[m]
                lo, hi = d["ic95"]
                marca = "" if d["cruza_zero"] else "   <- IC95 nao cruza 0"
                print(f"    {rot:<16}{d['delta_mediano']:+.3f}  "
                      f"IC95 [{lo:+.3f}, {hi:+.3f}]{marca}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["passes", "comparar"])
    args = ap.parse_args()
    {"passes": cmd_passes, "comparar": cmd_comparar}[args.etapa]()


if __name__ == "__main__":
    main()
