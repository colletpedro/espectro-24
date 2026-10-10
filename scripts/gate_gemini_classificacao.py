"""Gate de qualidade: a classificação em Gemini contra o gabarito humano de 100.

**Por que existe (2026-09-22).** O saldo do DeepSeek acabou com o lote de 55
no passe 3 (38%) e o dono não vai recarregar. Decisão dele: os 55 refazem os
TRÊS passes em Gemini — um provider por filme, nunca dois votos de um modelo e
um de outro na mesma review. Mas a qualidade da classificação em Gemini nunca
foi medida: o desenho de C15(c) foi arquivado sem rodar, porque a decisão de
provider era por custo. Antes de 55 filmes irem ao ar classificados por esse
modelo, este script roda o MESMO gabarito que mediu o DeepSeek.

**O que é comparado com o quê.**
- Gemini: `gemini-3.7-flash`, `thinking_budget=0`, teto de 2.000 tokens (os
  parâmetros do fallback de conteúdo, `synthesize.resposta_json_gemini`; a
  C15.a mediu 20% de truncamento a 300). Prompt de produção
  (`classificar_10.SYSTEM`, taxonomia `ebab2667de74`) e a mensagem de usuário
  byte a byte igual à de `votacao_3.classificar_passe`. Verificador `V2_alvo`
  com o prompt e a mensagem de `verificador_impacto.rodar_passe`.
- DeepSeek: o que JÁ ESTÁ EM DISCO, sem chamada nova —
  `variantes/A_regra_passe_{1,2,3}.jsonl` e `verificador/V2_alvo_passe_*.jsonl`
  (2026-08-13/14; modelo V4-Flash, anterior ao roteamento para o V4.1-Flash,
  ver C21). É a referência que `CLASSIFICACAO_CONSOLIDADO.md` §4/§5b publica.
- Gabarito: `leitura.md` fechado (duas rodadas de correção de 2026-08-14).
- Configuração DECISIVA = a de produção: consenso 2-de-3 + `V2_alvo` passada
  única (passe 1 do verificador) removendo `impacto_emocional`.

**CRITÉRIO DO GATE — registrado ANTES de rodar, não ajustado depois.**
Para cada eixo, na configuração decisiva, bootstrap pareado por review
(Gemini − DeepSeek, B=5000, semente 20260922) sobre F1 do eixo. PARAR se, em
QUALQUER eixo ou no micro geral:
  (a) o IC95 de ΔF1 fica inteiro abaixo de zero (pior com significância); ou
  (b) ΔF1 pontual ≤ −0,10 (pior em magnitude, mesmo sem significância —
      com n=100 e 17-69 positivos por eixo, o bootstrap tem pouco poder, e
      um gate que só dispara com significância quase nunca dispara).
Eixo com menos de 20 positivos no gabarito leva a marca `poder_baixo`.
Também PARAR se a taxa de falha (JSON inválido/truncado) no primeiro passe
ficar acima de 2% — a C3(B) mede 0,87% de falha no DeepSeek.
O gate não decide publicar: ele diz se PARA e mostra a tabela; o dono decide.

**Reprodutibilidade.** Fração das 100 com os três passes idênticos (conjunto
de eixos, `livre` incluído) e Jaccard médio entre pares de passes — a mesma
conta nos dois providers, sobre os mesmos arquivos. NÃO é o 26,5%→65% de
`VOTACAO_3.md` (consenso 1-2-3 contra 2-3-4, exige 4 passes e foi medido no
corpus); não há 4º passe DeepSeek nestas 100.

**Custo.** Medido por chamada, `thoughts_token_count` incluído como saída
(US$ 0,75/M entrada, US$ 3,75/M saída — o preço de `comparar_narrador.py` e
da C15.a, thinking cobrado como saída). Tokens de entrada em cache implícito
são cobrados a preço CHEIO aqui (pior caso; o desconto não está ancorado no
repo). A projeção dos 55 ajusta tokens de entrada por `n_chars` (regressão
linear sobre as chamadas do gate) e aplica sobre os `n_chars` reais das
6.559 reviews dos 55 na amostra.

Uso:
    python scripts/gate_gemini_classificacao.py passes      # 3 × 100 (LLM, ~US$0,35)
    python scripts/gate_gemini_classificacao.py verificar   # V2_alvo × 3 sobre o consenso Gemini
    python scripts/gate_gemini_classificacao.py comparar    # zero rede: métricas + gate + custo

Saídas em `resultado/auditoria-acuracia/gemini/`.

**Provider `local` (Ollama), 2026-10-08.** O MESMO gate, o MESMO critério de
parada (IC95 de ΔF1 inteiro abaixo de zero, ΔF1 <= -0,10, falha > 2%), a
MESMA referência (DeepSeek em disco), com `--provider local --modelo <nome>`:
    python scripts/gate_gemini_classificacao.py --provider local --modelo qwen3:8b passes
    python scripts/gate_gemini_classificacao.py --provider local --modelo qwen3:8b verificar
    python scripts/gate_gemini_classificacao.py --provider local --modelo qwen3:8b comparar
Saídas em `resultado/auditoria-acuracia/local/<modelo>/` (`:` e `/` do nome
do modelo viram `-` e `_`: o Windows não aceita `:` em caminho). Chamadas
SEQUENCIAIS (o Ollama reaproveita o prefixo de 929 tokens entre chamadas
consecutivas), custo zero, tempo por chamada em cada registro. O resumo de
tempo vai em `gate.json` → `custo.tempo_local`. Detalhes: `espectro24.local_ollama`
e `docs/SETUP_WINDOWS.md`.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import auditoria_acuracia as aa  # noqa: E402
import variante_impacto_estrito as vie  # noqa: E402
import verificador_impacto as vi  # noqa: E402
from classificar_10 import EIXOS, EIXOS_VALIDOS, SYSTEM, _normalizar, taxonomia_id  # noqa: E402
from espectro24.preco import GEMINI_3_7_FLASH, agora_utc_iso, custo_gemini  # noqa: E402
from espectro24.synthesize import resposta_json_gemini  # noqa: E402
from espectro24 import local_ollama  # noqa: E402

SAIDA = RAIZ / "resultado" / "auditoria-acuracia" / "gemini"
SAIDA_BASE = RAIZ / "resultado" / "auditoria-acuracia"
# Provider do gate em curso. `gemini` é o de sempre; `local` é o Ollama
# (`_configurar` troca SAIDA e os rótulos antes de qualquer leitura/escrita).
PROVIDER_GATE = "gemini"
MODELO_LOCAL: str | None = None
DIR_DEEPSEEK_CLASS = RAIZ / "resultado" / "auditoria-acuracia" / "variantes"
DIR_DEEPSEEK_VERIF = RAIZ / "resultado" / "auditoria-acuracia" / "verificador"
ARQ_RELATORIO = SAIDA / "gate.json"
ARQ_AMOSTRA_PRODUCAO = RAIZ / "resultado" / "votacao-3" / "amostra.json"

N_PASSES = 3
CONCORRENCIA = 8
EIXO_V = vi.EIXO

PRECO_GEMINI_ENTRADA = GEMINI_3_7_FLASH.miss_por_token
PRECO_GEMINI_SAIDA = GEMINI_3_7_FLASH.saida_por_token

SEMENTE = 20260922
N_BOOTSTRAP = 5000
LIMIAR_DELTA_F1 = -0.10
LIMIAR_FALHA_PASSE1 = 0.02
MIN_POSITIVOS_PODER = 20


def _slug_modelo(modelo: str) -> str:
    return modelo.replace(":", "-").replace("/", "_")


def _configurar(provider: str, modelo: str | None) -> None:
    """Aponta o gate para o provider pedido. `local` exige `--modelo` e grava
    em `local/<modelo>/`; as chaves do relatório (`gemini` no gate original)
    passam a levar o nome do provider."""
    global SAIDA, ARQ_RELATORIO, ARQ_SONDA_FLEX, PROVIDER_GATE, MODELO_LOCAL
    if provider == "gemini":
        if modelo:
            raise SystemExit("--modelo só vale com --provider local "
                             "(o Gemini é fixo em FALLBACK_CONTEUDO_MODELO)")
        return
    if not modelo:
        raise SystemExit("--provider local exige --modelo <nome do Ollama>")
    try:
        local_ollama.nivel_think()
    except ValueError as e:
        raise SystemExit(str(e))
    PROVIDER_GATE, MODELO_LOCAL = "local", modelo
    SAIDA = SAIDA_BASE / "local" / _slug_modelo(modelo)
    ARQ_RELATORIO = SAIDA / "gate.json"
    ARQ_SONDA_FLEX = SAIDA / "flex_classificacao_passe_1.jsonl"


def _arq_class(n: int) -> Path:
    return SAIDA / f"classificacao_passe_{n}.jsonl"


def _arq_verif(n: int) -> Path:
    return SAIDA / f"V2_alvo_passe_{n}.jsonl"


# ===========================================================================
# Chamadas
# ===========================================================================

def _ids_ok(arq: Path) -> set[str]:
    feitos = set()
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                if r.get("ok"):
                    feitos.add(r["id"])
    return feitos


CAMPOS_LOCAL = ("custo_usd", "think", "leitura_prompt_s", "geracao_s", "carga_s",
                "total_s", "prompt_eval_count", "eval_count")


def _chamar(system: str, user: str, estagio: str, camada: str | None,
            schema: dict | None) -> dict:
    if PROVIDER_GATE == "local":
        return local_ollama.resposta_json_local(
            system, user, estagio=estagio, modelo=MODELO_LOCAL, schema=schema)
    return resposta_json_gemini(system, user, estagio=estagio, camada=camada)


def _rodar(arq: Path, reviews: list[dict], system: str, montar_user,
           interpretar, estagio: str, rotulo: str, camada: str | None = None,
           concorrencia: int = CONCORRENCIA, schema: dict | None = None) -> None:
    """Uma passada. Falha vira `ok: False` com a resposta crua e o
    `finish_reason`; a reexecução retenta só as que não têm `ok: True` — o
    mesmo contrato dos passes de produção."""
    feitos = _ids_ok(arq)
    pendentes = [r for r in reviews if r["id"] not in feitos]
    print(f"  {rotulo}: {len(feitos)} feitas · {len(pendentes)} pendentes")
    if not pendentes:
        return
    if PROVIDER_GATE == "local":
        # um de cada vez, na ordem do gabarito: o Ollama só reaproveita o
        # prefixo entre chamadas CONSECUTIVAS
        concorrencia = 1
    lock, contador, t0 = Lock(), [0], time.time()
    arq.parent.mkdir(parents=True, exist_ok=True)
    saida = arq.open("a", encoding="utf-8")

    def tarefa(review: dict) -> None:
        resp = None
        base = {"id": review["id"], "bucket": review["bucket"],
                "nivel": review["nivel"], "n_chars": review["n_chars"],
                "ts": agora_utc_iso()}
        try:
            resp = _chamar(system, montar_user(review), estagio, camada, schema)
            registro = {"ok": True, **base, **interpretar(json.loads(resp["texto"]))}
        except Exception as e:  # noqa: BLE001
            registro = {"ok": False, **base, "erro": f"{type(e).__name__}: {e}"}
            if resp is not None:
                registro["resposta_crua"] = resp["texto"]
            elif PROVIDER_GATE == "local":
                # falha sem resposta: provider, modelo e o tempo gasto até ela
                registro.update({"provider": "local", "modelo": MODELO_LOCAL,
                                 "custo_usd": 0.0,
                                 "think": local_ollama.nivel_think(),
                                 "latencia_s": getattr(e, "latencia_s", None)})
        if resp is not None:
            registro.update({k: resp[k] for k in (
                "provider", "modelo", "modelo_efetivo", "uso",
                "thinking_tokens", "finish_reason", "latencia_s",
                "camada", "motivo_camada", "traffic_type")})
            registro.update({k: resp[k] for k in CAMPOS_LOCAL if k in resp})
        with lock:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
            saida.flush()
            contador[0] += 1
            if contador[0] % 25 == 0 or contador[0] == len(pendentes):
                print(f"    {contador[0]}/{len(pendentes)} · "
                      f"{time.time() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(max_workers=concorrencia) as ex:
        list(ex.map(tarefa, pendentes))
    saida.close()
    print(f"  {rotulo}: {time.time() - t0:.0f}s de parede")


def _user_classificacao(review: dict) -> str:
    # byte a byte a mensagem de `votacao_3.classificar_passe`
    return (f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
            f"{review['texto']}")


def _interpretar_classificacao(data: dict) -> dict:
    eixos, livres, invalidos = _normalizar(data)
    return {"eixos": eixos, "temas_livres": livres, "eixos_invalidos": invalidos}


def _user_verificador(review: dict) -> str:
    # byte a byte a mensagem de `verificador_impacto.rodar_passe`
    return (f"Review (nota {review['nivel']} de 5 estrelas):\n\n"
            f"{review['texto']}\n\n"
            f"Esta review foi marcada com `impacto_emocional`. "
            f"Confirma ou remove?")


def _interpretar_verificador(data: dict) -> dict:
    confirma, frase, alvo = vi._normalizar_veredito(data)
    return {"confirma": confirma, "frase": frase, "alvo": alvo}


# O texto das 100 vem da amostra em que o DeepSeek as classificou
# (`4d8e6db`, 2026-08-13), lida do git sem tocar o disco: 6 delas são de
# `obsession-2026`, que saiu do corpus na v1.9.50 e não está mais na amostra
# de produção; as outras 94 têm o texto idêntico ao de hoje (conferido).
COMMIT_TEXTOS = "4d8e6db"


ARQ_TEXTOS_GABARITO = RAIZ / "resultado" / "auditoria-acuracia" / "textos_gabarito.json"


def _reviews() -> list[dict]:
    """Índice do gabarito + texto. O texto vem de `textos_gabarito.json`
    (versionado: um clone limpo, inclusive raso e sem `git` no PATH, roda o
    gate); se o arquivo faltar, cai para o git, como antes."""
    idx = json.loads(aa.ARQ_INDICE.read_text(encoding="utf-8"))
    if ARQ_TEXTOS_GABARITO.exists():
        textos = json.loads(ARQ_TEXTOS_GABARITO.read_text(encoding="utf-8"))["textos"]
        return [{**r, "texto": textos[r["id"]]} for r in idx["reviews"]]
    import subprocess
    bruto = subprocess.run(
        ["git", "show", f"{COMMIT_TEXTOS}:resultado/votacao-3/amostra.json"],
        cwd=RAIZ, check=True, capture_output=True).stdout
    por_id = {r["id"]: r for r in json.loads(bruto)["reviews"]}
    return [{**r, "texto": por_id[r["id"]]["texto"]} for r in idx["reviews"]]


def _carregar_env() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")


def _exigir_modelo_instalado() -> None:
    """Falha CEDO, antes de 300 chamadas: servidor fora do ar ou modelo não
    baixado (`ollama pull <modelo>`)."""
    try:
        nomes = local_ollama.modelos_instalados()
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"Ollama inacessível em {local_ollama.url_base()} "
                         f"({type(e).__name__}: {e}) — suba o servidor "
                         f"(`ollama serve`) ou ajuste ESPECTRO24_OLLAMA_URL")
    base = MODELO_LOCAL if ":" in MODELO_LOCAL else MODELO_LOCAL + ":latest"
    if base not in nomes and MODELO_LOCAL not in nomes:
        raise SystemExit(f"modelo {MODELO_LOCAL!r} não está no Ollama "
                         f"({local_ollama.url_base()}). Instalados: {nomes}. "
                         f"Rode `ollama pull {MODELO_LOCAL}`")


def cmd_passes() -> None:
    _carregar_env()
    if taxonomia_id() != "ebab2667de74":
        raise SystemExit(f"taxonomia {taxonomia_id()} ≠ ebab2667de74 — o "
                         f"gabarito do DeepSeek foi medido sob ebab2667de74")
    reviews = _reviews()
    print(f"{len(reviews)} reviews · {N_PASSES} passes · "
          f"{'Ollama ' + MODELO_LOCAL if PROVIDER_GATE == 'local' else 'Gemini'}")
    for n in range(1, N_PASSES + 1):
        _rodar(_arq_class(n), reviews, SYSTEM, _user_classificacao,
               _interpretar_classificacao, "classificacao", f"classificação passe {n}",
               schema=local_ollama.schema_classificacao(EIXOS_VALIDOS))


ARQ_SONDA_FLEX = SAIDA / "flex_classificacao_passe_1.jsonl"


def cmd_sonda_flex(concorrencia: int, rodada: int = 1) -> None:
    """Um passe de classificação das 100 na camada FLEX (2026-09-22): mede
    latência e vazão reais antes de projetar o prazo dos 55, e a
    concordância com o passe 1 da camada padrão (mesmo modelo — deveria
    concordar tanto quanto dois passes padrão concordam entre si)."""
    _carregar_env()
    arq = ARQ_SONDA_FLEX if rodada == 1 else SAIDA / f"flex_classificacao_passe_1_r{rodada}.jsonl"
    _rodar(arq, _reviews(), SYSTEM, _user_classificacao,
           _interpretar_classificacao, "classificacao", "FLEX passe 1",
           camada="flex", concorrencia=concorrencia)


# --- sondas de BATCH (2026-09-22) ------------------------------------------
# Os 3 passes + o verificador pelo batch, sobre as mesmas 100: mede o tempo
# real de retorno E aplica o critério do gate ao modo batch (mesmo modelo,
# outra camada de serviço — medido em vez de suposto).

def _arq_sonda_batch(tipo: str, passe: int) -> Path:
    return SAIDA / f"sonda_batch_{tipo}_{passe}.json"


def _arq_regs_batch(tipo: str, passe: int) -> Path:
    prefixo = "batch_classificacao" if tipo == "classificacao" else "batch_V2_alvo"
    return SAIDA / f"{prefixo}_passe_{passe}.jsonl"


def consenso_batch() -> dict[str, dict]:
    return _consenso(SAIDA, "batch_classificacao")


def _alvos_batch(tipo: str) -> list[dict]:
    if tipo == "classificacao":
        return _reviews()
    cons = consenso_batch()
    return [r for r in _reviews() if EIXO_V in cons.get(r["id"], {}).get("eixos", [])]


def cmd_sonda_batch_submeter(tipo: str, passe: int) -> None:
    from espectro24.synthesize import gemini_batch_submeter
    _carregar_env()
    info = _arq_sonda_batch(tipo, passe)
    if info.exists():
        raise SystemExit(f"já submetido: {info.read_text()}")
    if tipo == "classificacao":
        pedidos = [(r["id"], SYSTEM, _user_classificacao(r)) for r in _alvos_batch(tipo)]
    else:
        pedidos = [(r["id"], vi.SYSTEM_V2_ALVO, _user_verificador(r))
                   for r in _alvos_batch(tipo)]
    nome = gemini_batch_submeter(pedidos, f"sonda-gabarito-{tipo}-p{passe}",
                                 SAIDA / "batch")
    info.write_text(json.dumps({"job": nome, "submetido": agora_utc_iso(),
                                "n": len(pedidos)}), encoding="utf-8")
    print(f"job {nome} · {len(pedidos)} pedidos")


def cmd_sonda_batch_coletar(tipo: str, passe: int) -> None:
    from espectro24.synthesize import gemini_batch_estado, gemini_batch_resultados
    _carregar_env()
    info = json.loads(_arq_sonda_batch(tipo, passe).read_text(encoding="utf-8"))
    est = gemini_batch_estado(info["job"])
    print(json.dumps(est, ensure_ascii=False))
    if est["estado"] != "JOB_STATE_SUCCEEDED":
        return
    res = gemini_batch_resultados(info["job"])
    por_id = {r["id"]: r for r in _alvos_batch(tipo)}
    interpretar = (_interpretar_classificacao if tipo == "classificacao"
                   else _interpretar_verificador)
    with _arq_regs_batch(tipo, passe).open("w", encoding="utf-8") as f:
        for rid, resp in res.items():
            review = por_id[rid]
            base = {"id": rid, "bucket": review["bucket"], "nivel": review["nivel"],
                    "n_chars": review["n_chars"], "ts": agora_utc_iso()}
            try:
                if resp.get("erro"):
                    raise ValueError(resp["erro"])
                reg = {"ok": True, **base, **interpretar(json.loads(resp["texto"]))}
            except Exception as e:  # noqa: BLE001
                reg = {"ok": False, **base, "erro": f"{type(e).__name__}: {e}",
                       "resposta_crua": resp.get("texto")}
            reg.update({k: resp.get(k) for k in (
                "provider", "modelo", "modelo_efetivo", "uso", "thinking_tokens",
                "finish_reason", "camada", "traffic_type",
                "campos_desconhecidos_do_sdk")})
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    print(f"{len(res)} respostas → {_arq_regs_batch(tipo, passe).name} · retorno "
          f"{est['criado']} → {est['fim']}")


def cmd_verificar() -> None:
    _carregar_env()
    cons = consenso_gemini()
    reviews = [r for r in _reviews() if EIXO_V in cons.get(r["id"], {}).get("eixos", [])]
    print(f"{len(reviews)} reviews com {EIXO_V} no consenso Gemini · "
          f"{N_PASSES} passes · Gemini")
    for n in range(1, N_PASSES + 1):
        _rodar(_arq_verif(n), reviews, vi.SYSTEM_V2_ALVO, _user_verificador,
               _interpretar_verificador, "verificador", f"V2_alvo passe {n}",
               schema=local_ollama.SCHEMA_VERIFICADOR)


# ===========================================================================
# Leitura
# ===========================================================================

def _linhas(arq: Path) -> list[dict]:
    if not arq.exists():
        return []
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]


def _ultimo_ok(arq: Path) -> dict[str, dict]:
    return {r["id"]: r for r in _linhas(arq) if r.get("ok")}


def consenso_gemini() -> dict[str, dict]:
    # mesma leitura de `vie._ler_passe` (recupera eixo inválido), mesmo voto
    return _consenso(SAIDA, "classificacao")


def _consenso(base: Path, prefixo: str) -> dict[str, dict]:
    """`vie.consenso` com o nome de arquivo deste diretório. O arquivo do
    Gemini chama-se `classificacao_passe_N`; o do DeepSeek, `A_regra_passe_N`
    — `vie._ler_passe` monta `<variante>_passe_<n>.jsonl`, então a variante
    aqui é o prefixo."""
    return vie.consenso(prefixo, base)


def vereditos_gemini(modo: str) -> dict[str, bool]:
    passes = [_ultimo_ok(_arq_verif(n)) for n in range(1, N_PASSES + 1)]
    if modo == "passe1":
        return {rid: r["confirma"] for rid, r in passes[0].items()}
    ids = set(passes[0]) & set(passes[1]) & set(passes[2])
    return {rid: sum(p[rid]["confirma"] for p in passes) >= 2 for rid in sorted(ids)}


# ===========================================================================
# Métricas
# ===========================================================================

def _prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else None
    return {"tp": tp, "fp": fp, "fn": fn, "precisao": p, "recall": r, "f1": f1}


def _contagens(anot: dict, gab: dict, ids: list[str]) -> dict[str, tuple[int, int, int]]:
    eixos = set(EIXOS)
    c = {e: [0, 0, 0] for e in list(EIXOS) + ["_micro"]}
    for rid in ids:
        h = set(anot[rid]["eixos"]) & eixos
        m = set(gab[rid]["eixos"]) & eixos
        for e in EIXOS:
            c[e][0] += (e in h and e in m)
            c[e][1] += (e in m and e not in h)
            c[e][2] += (e in h and e not in m)
        c["_micro"][0] += len(h & m)
        c["_micro"][1] += len(m - h)
        c["_micro"][2] += len(h - m)
    return {k: tuple(v) for k, v in c.items()}


def _f1(t: tuple[int, int, int]) -> float:
    tp, fp, fn = t
    d = 2 * tp + fp + fn
    return 2 * tp / d if d else 0.0


def _tabela(anot: dict, gab: dict) -> dict:
    ids = sorted(gab)
    c = _contagens(anot, gab, ids)
    exatos = sum(1 for rid in ids
                 if set(gab[rid]["eixos"]) - {"livre"} == set(anot[rid]["eixos"]) - {"livre"})
    return {"por_eixo": {e: _prf(*c[e]) for e in EIXOS},
            "micro": _prf(*c["_micro"]),
            "concordancia_exata": exatos / len(ids) if ids else None,
            "n": len(ids)}


def _bootstrap(anot: dict, ds: dict, gm: dict) -> dict:
    ids = sorted(set(ds) & set(gm))
    rng = random.Random(SEMENTE)
    acc = {k: [] for k in list(EIXOS) + ["_micro"]}
    for _ in range(N_BOOTSTRAP):
        am = [rng.choice(ids) for _ in ids]
        cd, cg = _contagens(anot, ds, am), _contagens(anot, gm, am)
        for k in acc:
            acc[k].append(_f1(cg[k]) - _f1(cd[k]))
    saida = {}
    for k, xs in acc.items():
        xs.sort()
        lo, hi = xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]
        saida[k] = {"delta_f1_mediano": round(xs[len(xs) // 2], 4),
                    "ic95": [round(lo, 4), round(hi, 4)]}
    return saida


def _reprodutibilidade(passes: list[dict[str, dict]], campo: str) -> dict:
    ids = sorted(set(passes[0]) & set(passes[1]) & set(passes[2]))
    if not ids:
        return {}
    if campo == "eixos":
        conj = [{rid: frozenset(p[rid]["eixos"]) for rid in ids} for p in passes]
        iguais = sum(1 for rid in ids if conj[0][rid] == conj[1][rid] == conj[2][rid])
        jac = []
        for a, b in combinations(range(3), 2):
            for rid in ids:
                u = conj[a][rid] | conj[b][rid]
                jac.append(len(conj[a][rid] & conj[b][rid]) / len(u) if u else 1.0)
        return {"n": len(ids), "tres_passes_identicos": iguais,
                "fracao_identica": iguais / len(ids),
                "jaccard_medio_entre_pares": sum(jac) / len(jac)}
    iguais = sum(1 for rid in ids
                 if passes[0][rid][campo] == passes[1][rid][campo] == passes[2][rid][campo])
    return {"n": len(ids), "tres_passes_identicos": iguais,
            "fracao_identica": iguais / len(ids)}


def _passes_class(base: Path, prefixo: str) -> list[dict[str, dict]]:
    # a leitura do consenso (`vie._ler_passe`, eixo inválido recuperado)
    return [{rid: {"eixos": e} for rid, e in vie._ler_passe(prefixo, n, base).items()}
            for n in (1, 2, 3)]


def _passes_ds_verif() -> list[dict[str, dict]]:
    return [_ultimo_ok(DIR_DEEPSEEK_VERIF / f"V2_alvo_passe_{n}.jsonl") for n in (1, 2, 3)]


def _falhas(arqs: list[Path]) -> dict:
    """Taxa de falha por TENTATIVA (toda linha é uma chamada cobrada) e,
    à parte, a do PRIMEIRO registro de cada review no passe — a que o
    critério do gate usa."""
    linhas = [r for a in arqs for r in _linhas(a)]
    primeira = {}
    for a in arqs:
        vistos = set()
        for r in _linhas(a):
            if r["id"] not in vistos:
                vistos.add(r["id"])
                primeira[(a.name, r["id"])] = r
    fr = Counter(r.get("finish_reason") for r in linhas)
    thinking = [r.get("thinking_tokens", 0) for r in linhas if "thinking_tokens" in r]
    n1 = len(primeira)
    f1 = sum(1 for r in primeira.values() if not r.get("ok"))
    return {"n_chamadas": len(linhas),
            "n_falhas": sum(1 for r in linhas if not r.get("ok")),
            "n_primeira_tentativa": n1, "falhas_primeira_tentativa": f1,
            "taxa_falha_primeira_tentativa": f1 / n1 if n1 else None,
            "finish_reason": dict(fr),
            "erros": [r["erro"][:160] for r in linhas if not r.get("ok")],
            "thinking": {"n_com_thinking": sum(1 for t in thinking if t > 0),
                         "media": sum(thinking) / len(thinking) if thinking else None,
                         "max": max(thinking) if thinking else None},
            "modelo_efetivo": dict(Counter(r.get("modelo_efetivo") for r in linhas))}


def _custo_chamada(r: dict) -> float:
    u = r.get("uso") or {}
    return (u.get("prompt_tokens", 0) * PRECO_GEMINI_ENTRADA
            + (u.get("completion_tokens", 0) + r.get("thinking_tokens", 0))
            * PRECO_GEMINI_SAIDA)


def _regressao(pts: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    b = sum((x - mx) * (y - my) for x, y in pts) / sxx
    return my - b * mx, b


def _custo(slugs_55: list[str]) -> dict:
    cl = [r for n in (1, 2, 3) for r in _linhas(_arq_class(n)) if "uso" in r]
    ve = [r for n in (1, 2, 3) for r in _linhas(_arq_verif(n)) if "uso" in r]
    medido = {"classificacao_usd": sum(map(_custo_chamada, cl)),
              "verificador_usd": sum(map(_custo_chamada, ve)),
              "n_classificacao": len(cl), "n_verificador": len(ve),
              "cache_hit_tokens_cobrados_cheio": sum(
                  (r["uso"].get("cache_hit_tokens", 0)) for r in cl + ve)}

    def modelo(regs):
        a_in, b_in = _regressao([(r["n_chars"], r["uso"]["prompt_tokens"]) for r in regs])
        saida = sum(r["uso"]["completion_tokens"] + r.get("thinking_tokens", 0)
                    for r in regs) / len(regs)
        return a_in, b_in, saida

    amostra = json.loads(ARQ_AMOSTRA_PRODUCAO.read_text(encoding="utf-8"))
    alvo = set(slugs_55)
    chars = [r["n_chars"] for r in amostra["reviews"] if r["slug"] in alvo]
    a_c, b_c, s_c = modelo(cl)
    custo_class_1 = sum((a_c + b_c * x) * PRECO_GEMINI_ENTRADA + s_c * PRECO_GEMINI_SAIDA
                        for x in chars)
    # fração de reviews que chega ao verificador: medida no consenso Gemini
    # destas 100 (amostra ESTRATIFICADA — não é a do corpus) e, como
    # referência, a do DeepSeek na produção (consenso dos 99)
    cons = consenso_gemini()
    frac_gab = sum(EIXO_V in g["eixos"] for g in cons.values()) / len(cons)
    linhas_prod = [json.loads(l) for l in
                   (RAIZ / "resultado" / "votacao-3" / "consenso.jsonl").read_text(
                       encoding="utf-8").splitlines() if l.strip()]
    frac_prod = sum(EIXO_V in l["eixos"] for l in linhas_prod) / len(linhas_prod)
    media_chars = sum(chars) / len(chars)
    if ve:
        a_v, b_v, s_v = modelo(ve)
        custo_verif_por = (a_v + b_v * media_chars) * PRECO_GEMINI_ENTRADA + s_v * PRECO_GEMINI_SAIDA
    else:
        custo_verif_por = 0.0
    proj = {}
    for nome, frac in (("frac_gabarito_gemini", frac_gab),
                       ("frac_producao_deepseek", frac_prod)):
        n_v = round(frac * len(chars))
        total = 3 * custo_class_1 + n_v * custo_verif_por
        proj[nome] = {"fracao_ao_verificador": round(frac, 4),
                      "n_verificador": n_v,
                      "classificacao_3_passes_usd": round(3 * custo_class_1, 2),
                      "verificador_usd": round(n_v * custo_verif_por, 2),
                      "total_usd": round(total, 2),
                      "por_filme_usd": round(total / len(slugs_55), 4)}
    return {"medido_no_gate": medido,
            "modelo_por_chamada_classificacao": {
                "tokens_entrada": f"{a_c:.1f} + {b_c:.4f}·n_chars",
                "tokens_saida_com_thinking_media": round(s_c, 1)},
            "n_reviews_55": len(chars), "n_chars_medio_55": round(media_chars, 1),
            "projecao_55": proj,
            "nota": "entrada em cache implícito cobrada a preço cheio (pior caso)"}


# ===========================================================================
# Comparação + gate
# ===========================================================================

def _slugs_55() -> list[str]:
    amostra = json.loads(ARQ_AMOSTRA_PRODUCAO.read_text(encoding="utf-8"))
    return [f["slug"] for f in amostra["filmes"]
            if not (RAIZ / "resultado" / f"{f['slug']}.json").exists()]


def cmd_comparar(modo: str = "padrao") -> None:
    """`modo="batch"`: as mesmas contas sobre os passes e o verificador
    feitos pelo BATCH (verificador em passada única — só o passe 1 existe).
    Saída em `gate_batch.json`."""
    batch = modo == "batch"
    L = PROVIDER_GATE  # chave do lado "novo" nas tabelas: gemini | local
    prefixo = "batch_classificacao" if batch else "classificacao"
    arqs_class = ([_arq_regs_batch("classificacao", n) for n in (1, 2, 3)]
                  if batch else [_arq_class(n) for n in (1, 2, 3)])
    arqs_verif = ([_arq_regs_batch("verificador", 1)] if batch
                  else [_arq_verif(n) for n in (1, 2, 3)])
    ver_p1 = {rid: r["confirma"] for rid, r in _ultimo_ok(arqs_verif[0]).items()}
    anot = aa.ler_anotacoes_humanas()
    ds_cons = _consenso(DIR_DEEPSEEK_CLASS, "A_regra")
    gm_cons = _consenso(SAIDA, prefixo)
    faltam = sorted(set(ds_cons) - set(gm_cons))

    ds_final = vi.aplicar(ds_cons, {rid: r["confirma"] for rid, r in _passes_ds_verif()[0].items()})
    gm_final = vi.aplicar(gm_cons, ver_p1)
    # comparação PAREADA: só as reviews presentes nos dois lados
    comuns = sorted(set(ds_cons) & set(gm_cons))
    if not comuns:
        raise SystemExit(f"nenhum passe de classificação em {SAIDA} — rode "
                         f"`passes` e `verificar` antes de `comparar`")
    sub = lambda g: {rid: g[rid] for rid in comuns}  # noqa: E731

    tab = {
        "consenso": {"deepseek": _tabela(anot, sub(ds_cons)),
                     L: _tabela(anot, sub(gm_cons))},
        "producao_consenso_mais_v2_passe1": {"deepseek": _tabela(anot, sub(ds_final)),
                                             L: _tabela(anot, sub(gm_final))},
    }
    boot = {k: _bootstrap(anot, sub(ds_final if k.startswith("producao") else ds_cons),
                          sub(gm_final if k.startswith("producao") else gm_cons))
            for k in tab}

    positivos = {e: sum(e in anot[rid]["eixos"] for rid in comuns) for e in EIXOS}
    decisiva = "producao_consenso_mais_v2_passe1"
    motivos = []
    linhas_gate = {}
    for e in list(EIXOS) + ["_micro"]:
        b = boot[decisiva][e]
        fd = (tab[decisiva]["deepseek"]["micro"] if e == "_micro"
              else tab[decisiva]["deepseek"]["por_eixo"][e])["f1"] or 0.0
        fg = (tab[decisiva][L]["micro"] if e == "_micro"
              else tab[decisiva][L]["por_eixo"][e])["f1"] or 0.0
        delta = fg - fd
        sig = b["ic95"][1] < 0
        mag = delta <= LIMIAR_DELTA_F1 + 1e-12
        linhas_gate[e] = {"f1_deepseek": round(fd, 4), f"f1_{L}": round(fg, 4),
                          "delta_f1": round(delta, 4), "ic95": b["ic95"],
                          "pior_com_significancia": sig, "pior_em_magnitude": mag,
                          "poder_baixo": e != "_micro" and positivos[e] < MIN_POSITIVOS_PODER}
        if sig:
            motivos.append(f"{e}: IC95 de ΔF1 {b['ic95']} inteiro abaixo de zero")
        if mag:
            motivos.append(f"{e}: ΔF1 {delta:+.3f} ≤ {LIMIAR_DELTA_F1}")

    falhas_gm = _falhas(arqs_class)
    falhas_gm_v = _falhas(arqs_verif)
    if (falhas_gm["taxa_falha_primeira_tentativa"] or 0) > LIMIAR_FALHA_PASSE1:
        motivos.append(f"falha na 1ª tentativa {falhas_gm['taxa_falha_primeira_tentativa']:.1%}"
                       f" > {LIMIAR_FALHA_PASSE1:.0%}")
    if faltam:
        motivos.append(f"{len(faltam)} review(s) sem os 3 passes Gemini: {faltam[:5]}")

    rel = {
        "criterio": {"limiar_delta_f1": LIMIAR_DELTA_F1,
                     "limiar_falha_primeira_tentativa": LIMIAR_FALHA_PASSE1,
                     "configuracao_decisiva": decisiva,
                     "bootstrap": {"B": N_BOOTSTRAP, "semente": SEMENTE}},
        "referencia_deepseek": "A_regra_passe_1-3 + V2_alvo passe 1, em disco "
                               "(2026-08-13/14, V4-Flash); nenhuma chamada nova",
        "n_pareado": len(comuns), "positivos_no_gabarito": positivos,
        "tabelas": tab, "bootstrap_delta_f1": boot, "gate_por_eixo": linhas_gate,
        "reprodutibilidade": {
            "classificacao": {"deepseek": _reprodutibilidade(
                                  _passes_class(DIR_DEEPSEEK_CLASS, "A_regra"), "eixos"),
                              L: _reprodutibilidade(
                                  _passes_class(SAIDA, prefixo), "eixos")},
            "verificador_V2": {"deepseek": _reprodutibilidade(_passes_ds_verif(), "confirma"),
                               L: _reprodutibilidade(
                                   [_ultimo_ok(a) for a in arqs_verif], "confirma")
                               if len(arqs_verif) == 3 else "só passe 1 (produção)"},
        },
        "falhas": {f"classificacao_{L}": falhas_gm, f"verificador_{L}": falhas_gm_v,
                   "classificacao_deepseek_no_gabarito": {
                       "n_falhas": sum(1 for n in (1, 2, 3) for r in _linhas(
                           DIR_DEEPSEEK_CLASS / f"A_regra_passe_{n}.jsonl") if not r.get("ok"))}},
        "danos_verificador": {"deepseek": vi._dano_e_acerto(anot, {
                                  rid: r["confirma"] for rid, r in _passes_ds_verif()[0].items()}),
                              L: vi._dano_e_acerto(anot, ver_p1)},
        "custo": (_custo_local(arqs_class + arqs_verif) if L == "local"
                  else _custo(_slugs_55()) if not batch else {
                      "medido_batch_usd": sum(custo_gemini(r) for a in arqs_class + arqs_verif
                                              for r in _linhas(a) if "uso" in r)}),
        "modo": modo, "provider": L, "modelo_local": MODELO_LOCAL,
        "think": local_ollama.nivel_think() if L == "local" else None,
        "lado": L,
        "gate": {"parar": bool(motivos), "motivos": motivos},
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / "gate_batch.json" if batch else ARQ_RELATORIO
    destino.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    _imprimir(rel)


def _quantis(xs: list[float]) -> dict:
    if not xs:
        return {}
    v = sorted(xs)
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]  # noqa: E731
    return {"n": len(v), "soma": round(sum(v), 1), "media": round(sum(v) / len(v), 2),
            "p50": round(q(0.5), 2), "p95": round(q(0.95), 2), "max": round(v[-1], 2)}


def _custo_local(arqs: list[Path]) -> dict:
    """Custo zero (gravado por chamada) e o TEMPO: parede, leitura do prompt
    e geração separados. `prompt_eval_count` da 1ª chamada contra a mediana
    é a evidência de que o Ollama reaproveitou o prefixo fixo."""
    regs = [r for a in arqs for r in _linhas(a)]
    com_tempo = [r for r in regs if "leitura_prompt_s" in r]
    leitura_tokens = [r["prompt_eval_count"] for r in com_tempo]
    return {"usd": sum(r.get("custo_usd", 0.0) for r in regs),
            "n_chamadas": len(regs),
            "tempo_local": {
                "parede_s": _quantis([r["latencia_s"] for r in regs
                                      if r.get("latencia_s") is not None]),
                "leitura_prompt_s": _quantis([r["leitura_prompt_s"] for r in com_tempo]),
                "geracao_s": _quantis([r["geracao_s"] for r in com_tempo]),
                "carga_s": _quantis([r["carga_s"] for r in com_tempo]),
                "prompt_eval_count": _quantis([float(x) for x in leitura_tokens]),
                "tokens_gerados": _quantis([float(r["eval_count"]) for r in com_tempo]),
            },
            "think": dict(Counter(r.get("think") for r in regs)),
            "modelo_efetivo": dict(Counter(r.get("modelo_efetivo") for r in regs))}


def _fmt(x) -> str:
    return "  —  " if x is None else f"{x:.3f}"


def _imprimir(rel: dict) -> None:
    L = rel["lado"]
    for k, t in rel["tabelas"].items():
        print(f"\n== {k} (n={rel['n_pareado']}) ==")
        print(f"{'eixo':22} {'pos':>4} | {'DS P':>6} {'DS R':>6} {'DS F1':>6} | "
              f"{'GM P':>6} {'GM R':>6} {'GM F1':>6} | ΔF1 IC95")
        for e in list(EIXOS) + ["_micro"]:
            d = t["deepseek"]["micro" if e == "_micro" else "por_eixo"]
            g = t[L]["micro" if e == "_micro" else "por_eixo"]
            d = d if e == "_micro" else d[e]
            g = g if e == "_micro" else g[e]
            b = rel["bootstrap_delta_f1"][k][e]
            pos = rel["positivos_no_gabarito"].get(e, "")
            print(f"{e:22} {pos:>4} | {_fmt(d['precisao'])} {_fmt(d['recall'])} {_fmt(d['f1'])} | "
                  f"{_fmt(g['precisao'])} {_fmt(g['recall'])} {_fmt(g['f1'])} | "
                  f"{(g['f1'] or 0) - (d['f1'] or 0):+.3f} {b['ic95']}")
        print(f"concordância exata: DS {t['deepseek']['concordancia_exata']:.2f} · "
              f"{L[:2].upper()} {t[L]['concordancia_exata']:.2f}")
    print("\n== reprodutibilidade ==")
    print(json.dumps(rel["reprodutibilidade"], ensure_ascii=False, indent=1))
    print("\n== falhas ==")
    f = rel["falhas"]
    for k in (f"classificacao_{L}", f"verificador_{L}"):
        x = f[k]
        print(f"{k}: {x['n_falhas']}/{x['n_chamadas']} chamadas · 1ª tentativa "
              f"{x['falhas_primeira_tentativa']}/{x['n_primeira_tentativa']} · "
              f"finish {x['finish_reason']} · thinking {x['thinking']} · "
              f"modelo {x['modelo_efetivo']}")
    print(f"classificação DeepSeek no gabarito: {f['classificacao_deepseek_no_gabarito']}")
    print("\n== danos do verificador ==")
    for k, v in rel["danos_verificador"].items():
        print(f"{k}: {({kk: vv for kk, vv in v.items() if kk != 'ids_dano'})}")
    print("\n== custo ==")
    print(json.dumps(rel["custo"], ensure_ascii=False, indent=1))
    print("\n== GATE ==")
    print("PARAR" if rel["gate"]["parar"] else "PASSA")
    for m in rel["gate"]["motivos"]:
        print(f"  - {m}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("passes", "verificar", "comparar", "comparar-batch",
                                    "sonda-flex",
                                    "sonda-batch", "sonda-batch-coletar"))
    ap.add_argument("--provider", choices=("gemini", "local"), default="gemini",
                    help="gemini (padrão) ou local (Ollama; exige --modelo)")
    ap.add_argument("--modelo", default=None,
                    help="nome do modelo no Ollama, ex.: qwen3:8b")
    ap.add_argument("--concorrencia", type=int, default=CONCORRENCIA)
    ap.add_argument("--rodada", type=int, default=1)
    ap.add_argument("--tipo", choices=("classificacao", "verificador"),
                    default="classificacao")
    ap.add_argument("--passe", type=int, default=1)
    a = ap.parse_args()
    _configurar(a.provider, a.modelo)
    if a.provider == "local" and a.cmd not in ("passes", "verificar", "comparar"):
        raise SystemExit(f"{a.cmd!r} é do Gemini (flex/batch); "
                         f"com --provider local use passes | verificar | comparar")
    if a.provider == "local" and a.cmd in ("passes", "verificar"):
        _exigir_modelo_instalado()
    if a.cmd == "sonda-flex":
        return cmd_sonda_flex(a.concorrencia, a.rodada)
    if a.cmd == "comparar-batch":
        return cmd_comparar("batch")
    if a.cmd == "sonda-batch":
        return cmd_sonda_batch_submeter(a.tipo, a.passe)
    if a.cmd == "sonda-batch-coletar":
        return cmd_sonda_batch_coletar(a.tipo, a.passe)
    {"passes": cmd_passes, "verificar": cmd_verificar, "comparar": cmd_comparar}[a.cmd]()


if __name__ == "__main__":
    main()
