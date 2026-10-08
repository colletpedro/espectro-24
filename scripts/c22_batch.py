"""Exceção C22 pelo BATCH do Gemini — os 55, bloco a bloco (2026-09-22).

O batch cobra 50% do preço padrão (ai.google.dev/gemini-api/docs/batch-mode e
/pricing, lidos em 2026-09-22) e é ASSÍNCRONO: o job é submetido, roda do
lado do Google, e o resultado é buscado depois. Isso não cabe dentro de
`lote_em_blocos.processar_bloco`, que chama e espera. Este script é a máquina
de estados que alimenta o driver: por BLOCO de filmes,

    1. passes 1 e 2 — UM job com os dois                     [batch]
    2. passe 3 — só as reviews em que 1 e 2 divergem         [batch]
       (`votacao_3.passe_3_dispensavel`; zero divergentes = sem job)
    3. verificador V2_alvo — só as candidatas do consenso    [batch]
       do bloco (reviews com `impacto_emocional`)
    4. COMMIT pelo driver: `lote_em_blocos.processar_bloco(bloco,
       excecao=True)`. Os passes e o verificador já estão pagos e gravados;
       o driver só retenta de forma SÍNCRONA o que falhou no batch (JSON
       inválido, pedido com erro) e grava consenso, verificado e manifesto,
       atômicos, como sempre.

Cada `avancar` faz tudo o que PODE sem esperar: submete o que falta
submeter, coleta o que terminou, commita o bloco pronto. Rodado em laço
(`--laco`), leva os 55 até o fim. Interromper não perde nada: o nome de cada
job é gravado em `c22_batch_jobs.json` ANTES de qualquer espera, o resultado
fica do lado do Google, e a coleta é idempotente (não regrava review que já
tem registro `ok` da exceção).

**Guardas iguais às da chamada síncrona.** A resposta de cada pedido passa por
`votacao_3.registro_excecao` / `verificador_impacto.registro_excecao` — as
MESMAS funções da chamada síncrona: JSON validado, `ok: False` com a resposta
crua quando inválido, provider, modelo pedido e EFETIVO, `finish_reason`,
camada, marca `excecao`.

**Disjuntor: `--teto-usd`.** O Gemini não tem sonda de saldo. Antes de cada
submissão: gasto MEDIDO da exceção (registros gravados, `preco.custo_gemini`)
+ custo ESTIMADO dos jobs já submetidos e ainda não coletados + o deste job
não pode passar do teto. Estourado, nada mais é submetido; o que já está no
Google é coletado normalmente.

Uso:
    python scripts/c22_batch.py plano                    # zero rede: blocos, chamadas, custo
    python scripts/c22_batch.py avancar --teto-usd N     # um tique
    python scripts/c22_batch.py avancar --teto-usd N --laco 120   # até o fim
    python scripts/c22_batch.py estado                   # os jobs e o que falta
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import excecao_gemini_c22 as C22  # noqa: E402
import lote_em_blocos as D  # noqa: E402
import verificador_impacto as vi  # noqa: E402
import votacao_3 as v3  # noqa: E402
from classificar_10 import SYSTEM  # noqa: E402
from espectro24.atomico import escrever_atomico  # noqa: E402
from espectro24.synthesize import LLMSaldoEsgotado  # noqa: E402
from espectro24.preco import (  # noqa: E402
    GEMINI_3_7_FLASH,
    GEMINI_3_7_FLASH_DESCONTO,
    agora_utc_iso,
)

# [2026-09-23, C22 (e)] Como o TETO é calculado nesta execução — posto por
# `main` a partir de `--preco-cheio` e `--bloco`. O billing não pôde ser
# conferido; a preço cheio, o teto limita o gasto REAL com ou sem desconto.
TETO = {"preco_cheio": False, "slugs": None}

ARQ_JOBS = v3.SAIDA / "c22_batch_jobs.json"
DIR_BATCH = v3.SAIDA / "_c22_batch"
LISTA = RAIZ / "dados" / "lote" / "lista-noturno-2026-09-18.txt"
TAMANHO_BLOCO = 10

# Modelo de custo por pedido, MEDIDO no gate (2026-09-22, 300 + 180 chamadas
# em camada padrão; `gate_gemini_classificacao.py comparar`): tokens de
# entrada lineares em `n_chars`, saída média com thinking. Só para o teto e a
# projeção — o gasto que conta é o medido nos registros.
ENTRADA_CLASS = (941.9, 0.2371)
SAIDA_CLASS = 139.2
ENTRADA_VERIF = (447.0, 0.2371)   # prompt V2 (431 tokens) + mensagem
SAIDA_VERIF = 140.0

TERMINAIS_RUINS = ("JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED")
MAX_ESPERA_429_S = 60 * 60


class Cota429Persistente(RuntimeError):
    """A criação de job segue recusada por cota (429) além da espera
    tolerada — decisão do dono."""


def custo_estimado(n_chars: list[int], verificador: bool = False,
                   preco_cheio: bool = False) -> float:
    a, b = ENTRADA_VERIF if verificador else ENTRADA_CLASS
    saida = SAIDA_VERIF if verificador else SAIDA_CLASS
    p = GEMINI_3_7_FLASH if preco_cheio else GEMINI_3_7_FLASH_DESCONTO
    return sum((a + b * x) * p.miss_por_token + saida * p.saida_por_token
               for x in n_chars)


# --- registro dos jobs --------------------------------------------------------

def ler_jobs() -> dict:
    if not ARQ_JOBS.exists():
        return {"jobs": []}
    return json.loads(ARQ_JOBS.read_text(encoding="utf-8"))


def gravar_jobs(estado: dict) -> None:
    escrever_atomico(ARQ_JOBS, json.dumps(estado, ensure_ascii=False, indent=2))


def _job(estado: dict, bloco: int, etapa: str) -> dict | None:
    for j in estado["jobs"]:
        if j["bloco"] == bloco and j["etapa"] == etapa and j["estado"] not in TERMINAIS_RUINS:
            return j
    return None


def blocos() -> list[list[str]]:
    from espectro24.lote import ler_lista_slugs
    slugs = ler_lista_slugs(str(LISTA))
    C22.exigir_no_escopo(slugs)
    return D.dividir_em_blocos(slugs, TAMANHO_BLOCO)


# --- pedidos ------------------------------------------------------------------

def _chave(slug: str, bucket: str, rid: str, passe: int | str) -> str:
    return f"{slug}|{bucket}|{rid}|{passe}"


def pedidos_passes(bloco: list[str], passes: tuple[int, ...]) -> list[tuple]:
    """`[(chave, system, user, review, passe)]` das reviews PENDENTES."""
    saida = []
    for n in passes:
        _, _, pend = v3.pendentes_do_passe(n, bloco, dispensar_p3=True)
        saida += [(_chave(r["slug"], r["bucket"], r["id"], n), SYSTEM,
                   v3.mensagem_usuario(r), r, n) for r in pend]
    return saida


def _linhas_do_bloco(bloco: list[str]) -> list[dict]:
    passes = [v3._ler_passe(n) for n in (1, 2, 3)]
    amostra = json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))
    atuais = D._linhas_jsonl(v3.ARQ_CONSENSO)
    linhas, _ = v3.consenso_incremental(atuais, passes, amostra, bloco)
    return [l for l in linhas if l["slug"] in set(bloco)]


def pedidos_verificador(bloco: list[str]) -> list[tuple]:
    feitos = {r["id"] for r in D._linhas_jsonl(vi.ARQ_PRODUCAO) if r.get("ok")}
    cands = vi._reviews_producao_a_verificar(_linhas_do_bloco(bloco))
    return [(_chave(c["slug"], "-", c["id"], "V2"), vi.SYSTEM_V2_ALVO,
             vi.mensagem_verificador(c), c, "V2")
            for c in cands if c["id"] not in feitos]


# --- submissão e coleta ---------------------------------------------------------

def custo_sincrono(bloco: list[str]) -> float:
    from espectro24.preco import custo_gemini
    alvo = set(bloco)
    ids = {r["id"] for r in json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))
           ["reviews"] if r["slug"] in alvo}
    regs = [r for n in (1, 2, 3) for r in D._linhas_jsonl(v3.ARQ_PASSE[n])
            if r.get("slug") in alvo]
    regs += [r for r in D._linhas_jsonl(vi.ARQ_PRODUCAO) if r.get("id") in ids]
    return sum(custo_gemini(r) for r in regs
               if r.get("excecao") == C22.EXCECAO and r.get("camada") != "batch")


def gasto_comprometido(estado: dict) -> float:
    """Medido (dos blocos da execução) + estimado dos jobs em voo, no regime
    de preço do teto (`TETO`)."""
    cheio = TETO["preco_cheio"]
    medido = D.gasto_excecao(TETO["slugs"], preco_cheio=cheio)
    chave = "custo_estimado_cheio" if cheio else "custo_estimado"
    em_voo = sum(j.get(chave, j["custo_estimado"] * (2 if cheio else 1))
                 for j in estado["jobs"]
                 if not j.get("coletado") and j["estado"] not in TERMINAIS_RUINS)
    return medido + em_voo


def submeter(estado: dict, i: int, etapa: str, pedidos: list[tuple],
             teto: float) -> bool:
    from espectro24.synthesize import gemini_batch_submeter

    verif = etapa == "verificador"
    chars = [p[3]["n_chars"] for p in pedidos]
    custo_desconto = custo_estimado(chars, verificador=verif)
    custo_cheio = custo_estimado(chars, verificador=verif, preco_cheio=True)
    custo = custo_cheio if TETO["preco_cheio"] else custo_desconto
    comprometido = gasto_comprometido(estado)
    if comprometido + custo > teto:
        print(f"  bloco {i} {etapa}: NÃO submetido — comprometido "
              f"US${comprometido:.2f} + este US${custo:.2f} passa do teto "
              f"US${teto:.2f}")
        return False
    try:
        nome = gemini_batch_submeter([(c, s, u) for c, s, u, _, _ in pedidos],
                                     f"c22-b{i}-{etapa}-{int(time.time())}",
                                     DIR_BATCH)
    except LLMSaldoEsgotado:
        raise
    except Exception as e:  # noqa: BLE001
        # [2026-09-23] 429 RESOURCE_EXHAUSTED na CRIAÇÃO do job (blocos 2-6):
        # o Tier 1 limita o batch do 3.7 Flash a 3.000.000 de tokens
        # ENFILEIRADOS por modelo e o gasto a US$10 por janela de 10 min
        # (ai.google.dev/gemini-api/docs/rate-limits, lido em 2026-09-23); um
        # job de passes 1-2 de um bloco tem ~2,5M. Nada foi criado — o
        # remédio documentado é esperar e tentar de novo, no próximo tique.
        # Persistindo por mais de `MAX_ESPERA_429_S`, a execução PARA.
        if getattr(e, "code", None) != 429:
            raise
        # Com job NOSSO em voo, o 429 é a fila que nós mesmos enchemos (o
        # limite de tokens enfileirados) — espera legítima, o relógio não
        # corre. Só conta como cota travada o 429 com a fila vazia.
        em_voo = [j for j in estado["jobs"] if j.get("job") and not j.get("coletado")
                  and j["estado"] not in TERMINAIS_RUINS]
        if em_voo:
            estado.pop("primeiro_429", None)
            estado["n_429"] = estado.get("n_429", 0) + 1
            gravar_jobs(estado)
            print(f"  bloco {i} {etapa}: 429 na criação — {len(em_voo)} job(s) "
                  f"nosso(s) na fila; espera a fila andar", flush=True)
            return False
        primeiro = estado.setdefault("primeiro_429", agora_utc_iso())
        estado.setdefault("n_429", 0)
        estado["n_429"] += 1
        gravar_jobs(estado)
        from datetime import datetime
        espera = (datetime.fromisoformat(agora_utc_iso())
                  - datetime.fromisoformat(primeiro)).total_seconds()
        print(f"  bloco {i} {etapa}: 429 na criação do job (cota do Tier 1) — "
              f"nada criado; tenta no próximo tique · esperando há "
              f"{espera / 60:.0f} min", flush=True)
        if espera > MAX_ESPERA_429_S:
            raise Cota429Persistente(
                f"429 persistente há {espera / 60:.0f} min ({estado['n_429']} "
                f"tentativas): {str(e)[:200]}") from e
        return False
    estado.pop("primeiro_429", None)
    estado["jobs"].append({"bloco": i, "etapa": etapa, "job": nome,
                           "n": len(pedidos), "submetido": agora_utc_iso(),
                           "estado": "JOB_STATE_PENDING", "coletado": None,
                           "custo_estimado": round(custo_desconto, 4),
                           "custo_estimado_cheio": round(custo_cheio, 4)})
    gravar_jobs(estado)   # o nome do job ANTES de qualquer espera
    print(f"  bloco {i} {etapa}: submetido {nome} · {len(pedidos)} pedidos · "
          f"~US${custo_desconto:.2f} a preço de batch / ~US${custo_cheio:.2f} "
          f"cheio")
    return True


def _ok_existentes(arq: Path) -> set[str]:
    chaves = set()
    for r in D._linhas_jsonl(arq):
        if r.get("ok") and r.get("excecao") == C22.EXCECAO:
            chaves.add(f"{r.get('slug', '-')}|{r.get('bucket', '-')}|{r['id']}")
    return chaves


def coletar(estado: dict, job: dict, bloco: list[str]) -> bool:
    """Grava as respostas de um job TERMINADO. Idempotente."""
    from espectro24.synthesize import gemini_batch_estado, gemini_batch_resultados

    est = gemini_batch_estado(job["job"])
    job["estado"] = est["estado"]
    if est["estado"] in TERMINAIS_RUINS:
        job["erro"] = est["erro"]
        gravar_jobs(estado)
        print(f"  bloco {job['bloco']} {job['etapa']}: {est['estado']} — "
              f"{est['erro']}. Será ressubmetido no próximo tique.")
        return False
    if est["estado"] != "JOB_STATE_SUCCEEDED":
        gravar_jobs(estado)
        return False
    res = gemini_batch_resultados(job["job"])
    tid = json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))["taxonomia_id"]
    alvo = set(bloco)
    amostra = {(r["slug"], r["bucket"], r["id"]): r for r in json.loads(
        v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))["reviews"] if r["slug"] in alvo}
    n_ok = n_falha = 0
    if job["etapa"] == "verificador":
        cands = {c["id"]: c for c in vi._reviews_producao_a_verificar(
            _linhas_do_bloco(bloco))}
        feitos = {k.split("|")[-1] for k in _ok_existentes(vi.ARQ_PRODUCAO)}
        novos = []
        for chave, resp in res.items():
            rid = chave.split("|")[2]
            if rid in feitos or rid not in cands:
                continue
            reg = vi.registro_excecao(vi.VARIANTE_PRODUCAO, 1, cands[rid], resp)
            novos.append(reg)
        with vi.ARQ_PRODUCAO.open("a", encoding="utf-8") as f:
            for reg in novos:
                f.write(json.dumps(reg, ensure_ascii=False) + "\n")
                n_ok += reg["ok"]
                n_falha += not reg["ok"]
    else:
        por_passe: dict[int, list[dict]] = {}
        for chave, resp in res.items():
            slug, bucket, rid, passe = chave.split("|")
            review = amostra[(slug, bucket, rid)]
            por_passe.setdefault(int(passe), []).append(
                v3.registro_excecao(review, int(passe), tid, resp))
        for n, regs in por_passe.items():
            feitos = _ok_existentes(v3.ARQ_PASSE[n])
            with v3.ARQ_PASSE[n].open("a", encoding="utf-8") as f:
                for reg in regs:
                    if f"{reg['slug']}|{reg['bucket']}|{reg['id']}" in feitos:
                        continue
                    f.write(json.dumps(reg, ensure_ascii=False) + "\n")
                    n_ok += reg["ok"]
                    n_falha += not reg["ok"]
    job["coletado"] = agora_utc_iso()
    job["retorno"] = {"criado": est["criado"], "fim": est["fim"]}
    job["n_ok"], job["n_falha"] = n_ok, n_falha
    gravar_jobs(estado)
    print(f"  bloco {job['bloco']} {job['etapa']}: coletado · {n_ok} ok · "
          f"{n_falha} falha(s) (o commit do driver as retenta, síncrono)")
    return True


# --- a máquina de estados --------------------------------------------------------

class ReservaEsgotada(RuntimeError):
    """Um bucket ficou sem substituta para uma recusada — o `n` caiu.
    Decisão do dono: parar e reportar antes de publicar."""


def aplicar_regra_de_aceite(bloco: list[str], estado: dict) -> list[dict]:
    """[2026-09-27] REGRA FIXA do dono para a queda de `n` por reserva
    esgotada. Aceita AUTOMATICAMENTE quando TODAS valem, por bucket:
      1. o bucket já estava abaixo de 40 ANTES do filtro (a seleção sem o
         registro de recusas) — reserva esgotada no bruto, não pelo filtro;
      2. a queda é de no máximo 2 reviews naquele bucket;
      3. o `n` resultante fica em `MARGEM_N_MINIMO` (10) ou mais — abaixo
         disso o contraste do bucket deixa de existir pela lei da margem.
    Fora dessas três, nada é aceito e a execução PARA (`ReservaEsgotada`).
    Cada aceite fica no registro de recusas (a declaração do dado do filme o
    carrega), no log, e em `estado["aceites_automaticos"]` para o relatório."""
    from espectro24 import recusas
    from espectro24.config import COTA_POR_BUCKET, MARGEM_N_MINIMO
    from espectro24.pipeline import ids_analisados_do_bruto

    feitos = []
    pendentes = recusas.reservas_esgotadas(bloco)
    for slug, bucket in sorted({(r["slug"], r["bucket"]) for r in pendentes}):
        coleta = D._coleta(slug)
        antes = len(ids_analisados_do_bruto(slug, coleta=coleta,
                                            ignorar_recusas=True).get(bucket, ()))
        agora = len(ids_analisados_do_bruto(slug, coleta=coleta).get(bucket, ()))
        queda = antes - agora
        conds = {"abaixo_de_40_antes_do_filtro": antes < COTA_POR_BUCKET,
                 "queda_ate_2": queda <= 2,
                 "n_resultante_ao_menos_10": agora >= MARGEM_N_MINIMO}
        if not all(conds.values()):
            print(f"  {slug}/{bucket}: regra de aceite NÃO se aplica "
                  f"(n {antes} → {agora}; {conds}) — para para o dono",
                  flush=True)
            continue
        decisao = (f"ACEITE AUTOMÁTICO pela regra fixa do dono (2026-09-27): "
                   f"o bucket já tinha {antes} < {COTA_POR_BUCKET} antes do "
                   f"filtro (reserva esgotada no bruto), a queda é de {queda} "
                   f"(≤ 2) e o n resultante é {agora} (≥ {MARGEM_N_MINIMO})")
        recusas.aceitar_n_menor(slug, bucket, decisao)
        reg = {"slug": slug, "bucket": bucket, "n_antes_do_filtro": antes,
               "n_depois": agora, "queda": queda, "em": agora_utc_iso()}
        estado.setdefault("aceites_automaticos", []).append(reg)
        gravar_jobs(estado)
        print(f"  ACEITE AUTOMÁTICO {slug}/{bucket}: n {antes} → {agora} "
              f"(regra fixa do dono)", flush=True)
        feitos.append(reg)
    return feitos


def _parar_se_reserva_esgotada(bloco: list[str]) -> None:
    from espectro24 import recusas
    esg = recusas.reservas_esgotadas(bloco)
    if esg:
        raise ReservaEsgotada(
            "reserva esgotada — o n caiu em: " + ", ".join(
                f"{r['slug']}/{r['bucket']} ({r['id']}, {r['bloqueio']})"
                for r in esg))


ARQ_IMPACTO = v3.SAIDA / "recusas_impacto.json"


def medir_impacto_das_recusas(bloco: list[str], estado: dict) -> list[dict]:
    """[2026-09-23] Depois do commit do bloco: `proveniencia_classificacao
    --recusas` em TODO filme do bloco com recusa (decisão do dono). O
    resultado é GRAVADO em `recusas_impacto.json` — a marca ★ de recoleta
    prioritária em DeepSeek passa a ser dado, não só saída de terminal."""
    import proveniencia_classificacao as PC
    from espectro24 import recusas

    com = sorted({r["slug"] for r in recusas.recusas()} & set(bloco))
    medidas = []
    for s in com:
        # a medida é OBSERVAÇÃO do que já foi commitado: uma falha nela vira
        # "indeterminado" com o motivo, nunca derruba o laço de blocos
        try:
            medidas.append(PC.impacto_das_recusas(s))
        except Exception as e:  # noqa: BLE001
            medidas.append({"slug": s, "estado": f"indeterminado: a medida "
                            f"falhou ({type(e).__name__}: {str(e)[:160]})"})
    atual = (json.loads(ARQ_IMPACTO.read_text(encoding="utf-8"))
             if ARQ_IMPACTO.exists() else {})
    for m in medidas:
        atual[m["slug"]] = {**m, "medido_em": agora_utc_iso()}
        marca = "★ PRIORITÁRIO" if m.get("prioritario_recoleta_deepseek") else "·"
        print(f"  recusas {m['slug']}: {marca} {m['estado']}"
              + "".join(f"\n      {x}" for x in m.get("motivos", [])), flush=True)
    escrever_atomico(ARQ_IMPACTO, json.dumps(atual, ensure_ascii=False, indent=2))
    return medidas


def avancar(teto: float, so_blocos: set[int] | None = None) -> bool:
    """Um tique. Devolve True quando os blocos pedidos (`None` = todos os 55)
    estão commitados. Blocos fora de `so_blocos` não são tocados."""
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    v3.exigir_sem_votos_de_fora(C22.SLUGS)
    estado = ler_jobs()
    feitos_todos = True
    for i, bloco in enumerate(blocos(), 1):
        if so_blocos is not None and i not in so_blocos:
            continue
        if any(j["bloco"] == i and j["etapa"] == "commit" for j in estado["jobs"]):
            continue
        feitos_todos = False
        pronto = True
        for etapa in ("p12", "p3", "verificador"):
            j = _job(estado, i, etapa)
            if j is None:
                if etapa == "p12":
                    ped = pedidos_passes(bloco, (1, 2))
                elif etapa == "p3":
                    ped = pedidos_passes(bloco, (3,))
                else:
                    ped = pedidos_verificador(bloco)
                if not ped:
                    estado["jobs"].append({"bloco": i, "etapa": etapa, "job": None,
                                           "n": 0, "estado": "SEM_PEDIDOS",
                                           "coletado": agora_utc_iso(),
                                           "custo_estimado": 0.0})
                    gravar_jobs(estado)
                    print(f"  bloco {i} {etapa}: nada a pedir")
                    continue
                submeter(estado, i, etapa, ped, teto)
                pronto = False
                break
            if not j.get("coletado"):
                if not coletar(estado, j, bloco):
                    pronto = False
                    break
                if etapa == "p12":
                    # [2026-09-23, C22] recusas do filtro de conteúdo: saem da
                    # amostra AGORA, para o passe 3 não as pedir de novo; a
                    # substituta é classificada no commit (síncrono).
                    novas = D.substituir_recusadas(bloco)
                    if novas:
                        j["recusas"] = [{k: r[k] for k in ("slug", "bucket", "id",
                                                            "bloqueio", "substituta")}
                                        for r in novas]
                        gravar_jobs(estado)
                    aplicar_regra_de_aceite(bloco, estado)
                    _parar_se_reserva_esgotada(bloco)
        if not pronto:
            continue
        # tudo pago e gravado: o driver retenta o que falhou e commita
        print(f"  bloco {i}: commit pelo driver ({len(bloco)} filmes)")
        r = D.processar_bloco(bloco, excecao=True)
        # Custo das chamadas SÍNCRONAS do bloco, pela camada gravada em cada
        # registro — não pela janela de tempo de `custo_do_bloco`, que pega o
        # verificador de batch coletado no mesmo segundo (bloco 1, 2026-09-23:
        # a janela disse US$0,3367; as 27 síncronas custaram US$0,021).
        sincrono = custo_sincrono(bloco)
        estado["jobs"].append({"bloco": i, "etapa": "commit", "job": None, "n": 0,
                               "estado": "COMMITADO", "coletado": agora_utc_iso(),
                               "custo_estimado": 0.0,
                               "resumo": {k: r[k] for k in (
                                   "reviews_no_consenso", "incompletas",
                                   "pendentes_verificador")},
                               "recusas_no_commit": [
                                   {k: x[k] for k in ("slug", "bucket", "id",
                                                      "bloqueio", "substituta")}
                                   for x in r.get("recusas", [])],
                               "custo_sincrono_do_commit": round(sincrono, 4)})
        gravar_jobs(estado)
        aplicar_regra_de_aceite(bloco, estado)
        _parar_se_reserva_esgotada(bloco)
        medir_impacto_das_recusas(bloco, estado)
        print(f"  bloco {i}: COMMITADO · {r['reviews_no_consenso']} reviews · "
              f"{r['incompletas']} incompletas · chamadas síncronas "
              f"(todas as do bloco) US${sincrono:.4f}")
    print(f"gasto medido da exceção (blocos desta execução): "
          f"US${D.gasto_excecao(TETO['slugs']):.4f} a preço de batch · "
          f"US${D.gasto_excecao(TETO['slugs'], preco_cheio=True):.4f} cheio "
          f"(o teto usa o {'cheio' if TETO['preco_cheio'] else 'de batch'})")
    return feitos_todos


# Frações MEDIDAS no gabarito (2026-09-22) que o plano usa como faixa:
# passe 3 = 1 − P(p1 == p2): 26% na camada padrão, 29% no batch (os 55
# concordam MAIS que o gabarito no DeepSeek — 42% contra 29% —, então é o
# teto); verificador = fração do consenso com `impacto_emocional`: 60% no
# consenso Gemini do gabarito, 71% no consenso DeepSeek de produção.
FRACAO_P3 = (0.24, 0.29)
FRACAO_VERIF = (0.60, 0.71)


def plano() -> None:
    amostra = json.loads(v3.ARQ_AMOSTRA.read_text(encoding="utf-8"))
    tot_n = tot_c = 0.0
    for i, bloco in enumerate(blocos(), 1):
        chars = [r["n_chars"] for r in amostra["reviews"] if r["slug"] in set(bloco)]
        c = custo_estimado(chars) * 2
        tot_n += len(chars)
        tot_c += c
        print(f"bloco {i}: {len(bloco)} filmes · {len(chars)} reviews · "
              f"passes 1-2 ~US${c:.2f}")
    chars = [r["n_chars"] for r in amostra["reviews"] if r["slug"] in C22.SLUGS]
    um_passe = custo_estimado(chars)
    verif = custo_estimado(chars, verificador=True)
    p3 = [f * um_passe for f in FRACAO_P3]
    v2 = [f * verif for f in FRACAO_VERIF]
    print(f"TOTAL: {int(tot_n)} reviews (batch, 50%)")
    print(f"  passes 1-2:   US${tot_c:.2f}")
    print(f"  passe 3:      US${p3[0]:.2f}–{p3[1]:.2f} "
          f"({FRACAO_P3[0]:.0%}–{FRACAO_P3[1]:.0%} das reviews)")
    print(f"  verificador:  US${v2[0]:.2f}–{v2[1]:.2f} "
          f"({FRACAO_VERIF[0]:.0%}–{FRACAO_VERIF[1]:.0%} das reviews)")
    print(f"  TOTAL:        US${tot_c + p3[0] + v2[0]:.2f}–"
          f"{tot_c + p3[1] + v2[1]:.2f}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("cmd", choices=("plano", "avancar", "estado"))
    ap.add_argument("--teto-usd", type=float)
    ap.add_argument("--laco", type=int, default=0,
                    help="segundos entre tiques; 0 = um tique só")
    ap.add_argument("--bloco", type=int, action="append",
                    help="só estes blocos (repetível); sem ele, todos")
    ap.add_argument("--preco-cheio", action="store_true",
                    help="o teto compara com o gasto A PREÇO CHEIO (sem o "
                         "desconto de batch), restrito aos blocos pedidos")
    a = ap.parse_args(argv)
    if a.cmd == "plano":
        plano()
        return 0
    if a.cmd == "estado":
        print(json.dumps(ler_jobs(), ensure_ascii=False, indent=1))
        return 0
    if a.teto_usd is None:
        ap.error("avancar exige --teto-usd")
    if a.bloco:
        todos = blocos()
        TETO["slugs"] = [s for i in a.bloco for s in todos[i - 1]]
    TETO["preco_cheio"] = a.preco_cheio
    while True:
        print(f"--- tique {agora_utc_iso()}", flush=True)
        try:
            feito = avancar(a.teto_usd, set(a.bloco) if a.bloco else None)
        except ReservaEsgotada as e:
            print(f"PARADO: {e}. Nada mais é submetido; reportar ao dono antes "
                  f"de publicar.", flush=True)
            return 3
        except (LLMSaldoEsgotado, SystemExit) as e:
            # [2026-09-27] 402 do Gemini ("prepayment credits are depleted"):
            # na submissão ou dentro do commit síncrono. Nada é gravado para
            # as não tentadas e o commit do bloco em curso NÃO acontece.
            print(f"PARADO: saldo do Gemini esgotado — {str(e)[:240]}. Jobs "
                  f"já criados seguem registrados e coletáveis; nada foi "
                  f"commitado no bloco em curso.", flush=True)
            return 5
        except Cota429Persistente as e:
            print(f"PARADO: {e}. Os jobs já criados seguem registrados e são "
                  f"coletáveis na próxima execução.", flush=True)
            return 4
        if feito:
            print("FIM: " + (f"blocos {sorted(a.bloco)} commitados."
                             if a.bloco else "os 55 estão commitados."))
            return 0
        if not a.laco:
            return 0
        time.sleep(a.laco)


if __name__ == "__main__":
    sys.exit(main())
