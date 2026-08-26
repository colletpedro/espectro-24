"""[Entrega 1] Inspeção da família `assistir` — o que ela realmente é.

`assistir` recorreu em 13 dos 15 filmes do gate de taxonomia, o que a
colocaria entre os candidatos a promoção por recorrência. A suspeita
registrada na decisão: boa parte pode ser **meta-comentário de logística**
("vi no cinema", "rewatch", "assisti no avião") — que não é eixo nem tema
livre, e sim material que talvez nem devesse chegar à síntese.

Esta inspeção classifica 30 exemplos em três categorias:

  (a) meta-comentário de logística, sem conteúdo sobre o filme
  (b) conteúdo real que a taxonomia (agora de 10 eixos) não cobre
  (c) ambíguo

MEDIÇÃO APENAS. Nenhum filtro é implementado aqui, qualquer que seja o
resultado.

Duas leituras são registradas lado a lado, deliberadamente: a do LLM (um
item por chamada, reproduzível) e a humana/de revisão, no relatório. Onde
divergem, a divergência é o achado.

Uso:
    python scripts/inspecao_assistir.py extrair
    python scripts/inspecao_assistir.py classificar
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24.synthesize import (  # noqa: E402
    deepseek_client,
    deepseek_resposta,
    deepseek_uso,
)

GATE = RAIZ / "resultado" / "gate-taxonomia"
SAIDA = RAIZ / "resultado" / "taxonomia-10"
ARQ_AMOSTRA = SAIDA / "assistir_amostra.json"
ARQ_VEREDITOS = SAIDA / "assistir_vereditos.json"

SEMENTE = 20260808
N_EXEMPLOS = 30
MODELO = "deepseek-v4-flash"
CONCORRENCIA = 8
# [v1.9.25] `MAX_TENTATIVAS` REMOVIDO: a retentativa de transporte
# vive no adaptador (`synthesize._com_retentativa`, §3[D]), com
# backoff exponencial e jitter. O laço local retentava também erro
# de CONTEÚDO e, depois da v1.9.25, empilharia sobre a do adaptador.

SYSTEM = """Você recebe UMA review de cinema que um classificador anterior marcou como falando de "circunstância de assistir" (onde, quando, com quem, em que condições a pessoa viu o filme).

Sua tarefa: dizer em qual das três categorias ela cai.

`logistica` — a review só relata a CIRCUNSTÂNCIA em que assistiu e não diz nada avaliável sobre o filme em si. Ex.: "vi no avião sem legenda", "assisti pela metade no TikTok", "vi duas vezes e nunca presto atenção".

`conteudo` — a review diz algo real sobre o filme ou sobre como ele funciona, que NÃO cabe em nenhum destes eixos: ritmo, atuação, direção/imagem, roteiro/estrutura, som/trilha, tom/atmosfera, impacto emocional, comparações com outras obras, expectativa antes de assistir, crítica social/política ao que o filme representa.

`ambiguo` — mistura as duas coisas de tal forma que separar seria arbitrário.

ATENÇÃO: se o que a review diz JÁ CABE em um dos dez eixos listados acima, ela não é `conteudo` — é `logistica` se o resto for só circunstância, ou `ambiguo`. `conteudo` é reservado para o que a taxonomia de dez eixos realmente não alcança.

Responda APENAS com JSON:
{"categoria": "logistica|conteudo|ambiguo", "eixos_que_ja_cobririam": ["..."], "justificativa": "uma frase"}"""


def extrair() -> None:
    """Sorteia os 30 exemplos, com texto completo, filme e bucket."""
    fam = json.loads((GATE / "familias.json").read_text(encoding="utf-8"))
    atrib = fam["atribuicao"]
    amostra = json.loads((GATE / "amostra.json").read_text(encoding="utf-8"))
    textos = {(r["slug"], r["bucket"], r["id"]): r["texto"]
              for r in amostra["reviews"]}

    itens = []
    for linha in (GATE / "classificacoes.jsonl").read_text(
            encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        r = json.loads(linha)
        if not r.get("ok"):
            continue
        rotulos = [t for t in r["temas_livres"] if atrib.get(t) == "assistir"]
        if not rotulos:
            continue
        itens.append({
            "slug": r["slug"], "perfil": r["perfil"], "bucket": r["bucket"],
            "id": r["id"], "eixos_8": r["eixos"], "rotulos": rotulos,
            # `so_livre` é o campo decisivo: só a review que caiu SÓ em
            # `livre` é candidata a filtro de seleção. Uma review com 5 eixos
            # e um tema `assistir` de brinde continuaria entrando na síntese
            # sob qualquer filtro razoável.
            "so_livre": r["eixos"] == ["livre"],
            "texto": textos.get((r["slug"], r["bucket"], r["id"]), ""),
        })

    rng = random.Random(f"{SEMENTE}:assistir")
    sel = rng.sample(itens, min(N_EXEMPLOS, len(itens)))
    sel.sort(key=lambda i: (i["slug"], i["bucket"], i["id"]))
    SAIDA.mkdir(parents=True, exist_ok=True)
    ARQ_AMOSTRA.write_text(json.dumps(
        {"semente": SEMENTE, "n_ocorrencias_totais": len(itens),
         "n_so_livre_no_total": sum(1 for i in itens if i["so_livre"]),
         "n_filmes_no_total": len({i["slug"] for i in itens}),
         "exemplos": sel}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(itens)} ocorrências de `assistir` em "
          f"{len({i['slug'] for i in itens})} filmes "
          f"({sum(1 for i in itens if i['so_livre'])} em reviews só-livre)")
    print(f"→ {ARQ_AMOSTRA.relative_to(RAIZ)} ({len(sel)} exemplos)")


def classificar() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")

    dados = json.loads(ARQ_AMOSTRA.read_text(encoding="utf-8"))
    exemplos = dados["exemplos"]
    client = deepseek_client()
    saida, lock, uso = [], Lock(), Counter()

    def tarefa(it: dict) -> None:
        # [v1.9.25, §3[D]] Laço de retentativa REMOVIDO — o adaptador
        # retenta TRANSPORTE. Este caminho já propagava o erro na
        # última tentativa, então o contrato não muda.
        resp = deepseek_resposta(
            SYSTEM, f"Review (nota {it.get('nivel', '?')}):\n\n{it['texto']}",
            MODELO, max_tokens=200, json_mode=True, client=client)
        data = json.loads(resp.choices[0].message.content)
        u = deepseek_uso(resp)
        with lock:
            saida.append({**{k: it[k] for k in ("slug", "bucket", "id",
                                                "eixos_8", "rotulos",
                                                "so_livre", "texto")},
                          "categoria": data.get("categoria", "ambiguo"),
                          "eixos_que_ja_cobririam": data.get("eixos_que_ja_cobririam", []),
                          "justificativa": data.get("justificativa", "")})
            for k, v in u.items():
                uso[k] += v

    with ThreadPoolExecutor(max_workers=CONCORRENCIA) as pool:
        list(pool.map(tarefa, exemplos))

    saida.sort(key=lambda r: (r["slug"], r["bucket"], r["id"]))
    contagem = Counter(r["categoria"] for r in saida)
    contagem_so_livre = Counter(r["categoria"] for r in saida if r["so_livre"])
    ja_cobertos = Counter(e for r in saida for e in r["eixos_que_ja_cobririam"])

    ARQ_VEREDITOS.write_text(json.dumps({
        "n": len(saida),
        "contagem": dict(contagem),
        "contagem_em_reviews_so_livre": dict(contagem_so_livre),
        "n_so_livre": sum(1 for r in saida if r["so_livre"]),
        "eixos_que_ja_cobririam": dict(ja_cobertos.most_common()),
        "uso_tokens": dict(uso),
        "vereditos": saida,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(saida)} classificados — {dict(contagem)}")
    print(f"  só-livre ({sum(1 for r in saida if r['so_livre'])}): "
          f"{dict(contagem_so_livre)}")
    print(f"  eixos que já cobririam: {dict(ja_cobertos.most_common(8))}")
    print(f"→ {ARQ_VEREDITOS.relative_to(RAIZ)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("etapa", choices=["extrair", "classificar"])
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    (extrair if args.etapa == "extrair" else classificar)()
