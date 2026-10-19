"""Checagem de APOIO dos bullets da síntese: publicado (DeepSeek) × local (qwen3:14b).

**A pergunta (2026-10-19).** Cada bullet afirma que um tema aparece nas
reviews de um grupo. Ele tem apoio nas reviews DAQUELE grupo — as mesmas ~40
que alimentaram a síntese — ou foi inventado/inflado? A leitura humana do
dono achou os bullets do qwen3 genéricos e alguns aparentemente inventados
("direção e estética visual fraca", "atuações insuficientes" nas negativas de
Anatomia de uma Queda). O modelo local de hoje NÃO publica; esta checagem é a
régua para avaliar o fine-tuning.

Só os BULLETS (`buckets[].temas`): no publicado eles são do DeepSeek
(narrativa, veredito e condições são do Gemini e ficam de fora).

**Nenhuma chamada paga.** Tudo roda local: Partes 1 e 3 no Mac, sem modelo de
linguagem; a Parte 2 no notebook Windows, no Ollama.

Partes e subcomandos (todos escrevem em `--dir`, nunca em `resultado/`):

- `eixo` (Parte 1a, sem modelo): pela rotulagem de cada lado, cada tema tem
  um eixo; conta quantas reviews do grupo têm esse eixo no consenso da
  classificação. Eixo em 0-1 review = suspeito. Grosseiro (o eixo é mais
  largo que o tema), mas não depende de modelo.
- `recuperar` (Parte 1b): as 5 reviews do grupo mais parecidas com cada
  bullet, por embedding local (`encoder_e5`, multilingual-e5-base).
- `preparar-juiz` (Parte 2): o arquivo de entrada do juiz — bullet × 5
  reviews recuperadas, dos dois lados — e a estimativa de chamadas e tempo.
- `juiz` (Parte 2, NO WINDOWS): qwen3:14b no Ollama, UM par por chamada,
  `{"menciona": true|false}`. Retoma de onde parou.
- `amostra-rotulo` (Parte 3): ~40 pares sorteados, metade de cada lado, num
  documento para o dono rotular à mão, sem a resposta do juiz e sem o lado.
- `validar-juiz` (Parte 3): precisão e recall do juiz contra o rótulo do dono.
- `relatorio` (resultado final): por lado e por filme. Recusa rodar sem a
  validação; com o juiz reprovado, o relatório diz que NÃO VALE.

Uso (Mac):
    python scripts/checagem_bullets.py eixo --local-dir prosa-local-qwen3 --dir checagem-bullets
    python scripts/checagem_bullets.py recuperar --local-dir prosa-local-qwen3 --dir checagem-bullets
    python scripts/checagem_bullets.py preparar-juiz --dir checagem-bullets
    python scripts/checagem_bullets.py amostra-rotulo --dir checagem-bullets
Uso (Windows, ver docs/SETUP_WINDOWS.md §10):
    python scripts/checagem_bullets.py juiz --modelo qwen3:14b --dir checagem-bullets
Depois do rótulo do dono e do juiz:
    python scripts/checagem_bullets.py validar-juiz --dir checagem-bullets
    python scripts/checagem_bullets.py relatorio --dir checagem-bullets
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import statistics
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

RESULTADO_DIR = RAIZ / "resultado"
LADOS = ("publicado", "local")
AUTOR = {"publicado": "DeepSeek (síntese publicada)", "local": "qwen3:14b (Ollama)"}
BUCKETS = ("negativas", "medianas", "positivas")
GRUPO = {"negativas": "quem não gostou (notas 0,5 a 2)",
         "medianas": "quem ficou no meio (notas 2,5 a 3,5)",
         "positivas": "quem gostou (notas 4 a 5)"}
K_RECUPERADAS = 5
# Eixo presente em até esta quantidade de reviews do grupo = bullet suspeito
# (Parte 1a). Valor do PEDIDO do dono ("0-1 review"), não calibrado.
SUSPEITO_ATE = 1
SEMENTE = 20261019
N_ROTULO_POR_LADO = 20

ARQ_EIXO = "parte1_eixo.json"
ARQ_RECUP = "parte1_recuperacao.json"
ARQ_ENTRADA = "juiz_entrada.jsonl"
ARQ_SAIDA = "juiz_saida.jsonl"
ARQ_ROTULOS = Path("rotulagem") / "rotulos_dono.csv"
ARQ_DOC_ROTULO = Path("rotulagem") / "rotulagem_dono.md"
ARQ_MAPA = Path("mapa") / "rotulagem_mapa.json"
ARQ_VALIDACAO = "validacao_juiz.json"


# ===========================================================================
# Guardas
# ===========================================================================

def exigir_fora_de_resultado(destino: Path, resultado_dir: Path = RESULTADO_DIR) -> None:
    """Nada desta checagem escreve em `resultado/` (os 99 publicados)."""
    alvo, proibido = Path(destino).resolve(), Path(resultado_dir).resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise SystemExit(f"RECUSADO: {alvo} fica dentro de {proibido} — esta "
                         f"checagem nunca escreve em resultado/")


def _escrever(caminho: Path, texto: str) -> None:
    exigir_fora_de_resultado(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def _json(caminho: Path, obj) -> None:
    _escrever(caminho, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def _ler_json(caminho: Path):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def _sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _sha256_arquivo(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


# ===========================================================================
# Bullets, eixos e classificação
# ===========================================================================

def bullets_do_doc(doc: dict, lado: str) -> list[dict]:
    """Um registro por tema publicado na tela (`buckets[].temas`)."""
    fora = []
    for b in doc.get("buckets", []):
        for i, t in enumerate(b.get("temas") or []):
            fora.append({
                "id_bullet": f"{lado}|{doc['slug']}|{b['bucket']}|{i}",
                "lado": lado, "slug": doc["slug"], "bucket": b["bucket"], "i": i,
                "tema": t["tema"], "exemplo": t.get("exemplo_parafraseado") or "",
                "mencoes": int(t.get("mencoes_aproximadas") or 0),
                "n": int(t.get("n_reviews_analisadas") or 0)})
    return fora


def eixo_por_tema(doc: dict) -> dict[tuple[str, str], str]:
    """`{(bucket, tema): eixo}` lido do bloco `eixos` do PRÓPRIO lado — a
    rotulagem [D3] que aquele modelo fez. O tema que ficou com a célula e os
    de `temas_no_mesmo_eixo` têm eixo; tema rotulado `livre` não aparece em
    linha nenhuma e não tem eixo (`None`)."""
    fora: dict[tuple[str, str], str] = {}
    for linha in (doc.get("eixos") or {}).get("linhas") or []:
        for bucket, cel in (linha.get("por_bucket") or {}).items():
            for tema in [cel.get("tema")] + list(cel.get("temas_no_mesmo_eixo") or []):
                if tema is not None:
                    fora.setdefault((bucket, tema), linha["eixo"])
    return fora


def com_eixo(cls_do_bucket: dict[str, list[str]], eixo: str | None) -> list[str]:
    """Ids das reviews do grupo cujo consenso tem `eixo` (ordenados)."""
    if eixo is None:
        return []
    return sorted(rid for rid, eixos in cls_do_bucket.items() if eixo in set(eixos))


def reconciliar(doc: dict, cls: dict[str, dict[str, list[str]]]) -> int:
    """A contagem refeita aqui tem de ser a PUBLICADA no bloco `eixos` de
    `doc`, célula a célula (`mencoes` e `de_n`). Divergência é ERRO: seria
    contar sobre outra classificação ou outra amostra. Devolve o número de
    células conferidas."""
    n = 0
    for linha in (doc.get("eixos") or {}).get("linhas") or []:
        for bucket, cel in linha["por_bucket"].items():
            meu = len(com_eixo(cls.get(bucket) or {}, linha["eixo"]))
            de_n = len(cls.get(bucket) or {})
            if meu != cel["mencoes"] or de_n != cel["de_n"]:
                raise ValueError(
                    f"{doc['slug']}/{bucket}/{linha['eixo']}: contei {meu}/{de_n}, "
                    f"o bloco eixos diz {cel['mencoes']}/{cel['de_n']}")
            n += 1
    return n


def classificacao_analisada(slug: str, analisadas: dict[str, set[str]],
                            catalogo: dict) -> dict[str, dict[str, list[str]]]:
    """O consenso do filme restrito à amostra que a SÍNTESE leu — o mesmo
    filtro de `eixos.montar_bloco`. Review analisada sem classificação é erro
    (seria um `n` menor em silêncio)."""
    do_filme = catalogo.get(slug) or {}
    fora = {}
    for b, ids in analisadas.items():
        cls_b = do_filme.get(b) or {}
        faltam = sorted(set(ids) - set(cls_b))
        if faltam:
            raise ValueError(f"{slug}/{b}: {len(faltam)} reviews analisadas sem "
                             f"classificação no consenso (ex.: {faltam[:3]})")
        fora[b] = {rid: cls_b[rid] for rid in sorted(ids)}
    return fora


def carregar_filmes(slugs, local_dir: Path, resultado_dir: Path = RESULTADO_DIR,
                    bruto_dir=None, catalogo=None) -> dict[str, dict]:
    """`{slug: {docs: {lado: doc}, reviews: {bucket: [ReviewBruta]},
    cls: {bucket: {id: [eixos]}}, celulas_conferidas}}`.

    As reviews são `pipeline.amostra_do_bruto` com a coleta do PUBLICADO — a
    mesma seleção que a síntese dos dois lados leu (`prosa_local` registra
    `selecao_reproduz_publicada`; aqui o `n_validas` de cada bucket é
    conferido nos dois documentos)."""
    from espectro24 import eixos as E
    from espectro24.config import DADOS_BRUTO_DIR
    from espectro24.pipeline import amostra_do_bruto

    if catalogo is None:
        catalogo = E.carregar_classificacao(RAIZ / E.CONSENSO_VERIFICADO)
    fora = {}
    for slug in slugs:
        docs = {"publicado": _ler_json(Path(resultado_dir) / f"{slug}.json"),
                "local": _ler_json(Path(local_dir) / f"{slug}.json")}
        reviews = amostra_do_bruto(slug, coleta=docs["publicado"]["coleta"],
                                   raiz=bruto_dir or DADOS_BRUTO_DIR)
        for lado, d in docs.items():
            for b in d["buckets"]:
                if len(reviews.get(b["bucket"], [])) != b["n_validas"]:
                    raise ValueError(f"{slug}/{lado}/{b['bucket']}: amostra refeita "
                                     f"tem {len(reviews.get(b['bucket'], []))}, o "
                                     f"documento diz n_validas={b['n_validas']}")
        analisadas = {b: {r.id for r in rs} for b, rs in reviews.items()}
        cls = classificacao_analisada(slug, analisadas, catalogo)
        n_cel = sum(reconciliar(d, cls) for d in docs.values())
        fora[slug] = {"docs": docs, "reviews": reviews, "cls": cls,
                      "celulas_conferidas": n_cel}
    return fora


def medida_eixo(filmes: dict[str, dict]) -> list[dict]:
    """Parte 1a: um registro por bullet, dos dois lados."""
    fora = []
    for slug in sorted(filmes):
        f = filmes[slug]
        for lado in LADOS:
            mapa = eixo_por_tema(f["docs"][lado])
            for bl in bullets_do_doc(f["docs"][lado], lado):
                eixo = mapa.get((bl["bucket"], bl["tema"]))
                ids = com_eixo(f["cls"].get(bl["bucket"]) or {}, eixo)
                fora.append({**bl, "eixo": eixo, "n_com_eixo": len(ids),
                             "de_n": len(f["cls"].get(bl["bucket"]) or {}),
                             "ids_com_eixo": ids,
                             "suspeito": eixo is not None and len(ids) <= SUSPEITO_ATE,
                             "sem_eixo": eixo is None,
                             "declarado_acima_do_eixo": eixo is not None
                             and bl["mencoes"] > len(ids)})
    return fora


# ===========================================================================
# Quantificador do texto do bullet
# ===========================================================================

def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


# Palavra do texto → faixa do mapa do site (`quantificador.BANDAS_FRACA_PARA_FORTE`).
# "várias"/"diversas" não têm faixa própria no site; ficam com "muitos" — uma
# LEITURA registrada aqui, não uma medição.
_LEXICO_QUANT = (
    (r"\b(quase|praticamente) tod[oa]s\b", "quase todos"),
    (r"\b(a maioria|a maior parte|grande parte)\b", "a maioria"),
    (r"\b(cerca de )?metade\b", "cerca de metade"),
    (r"\b(muit[oa]s|vari[oa]s|divers[oa]s|inumer[oa]s|numeros[oa]s)\b", "muitos"),
    (r"\b(alguns|algumas|uma parcela|parte d[oa]s|cert[oa]s)\b", "alguns"),
    (r"\b(pouc[oa]s)\b", "poucos"),
)


def quantificador_do_texto(texto: str) -> dict | None:
    """O PRIMEIRO quantificador do texto (posição), com a palavra como escrita
    e a faixa do site em que ela cai. `None` = o texto não quantifica."""
    norm = _sem_acento(texto or "")
    achados = []
    for padrao, faixa in _LEXICO_QUANT:
        m = re.search(padrao, norm)
        if m:
            achados.append((m.start(), m.group(0), faixa))
    if not achados:
        return None
    pos, palavra, faixa = min(achados)
    return {"palavra": palavra, "faixa": faixa}


def faixa_do_declarado(mencoes: int, n: int) -> str:
    """A faixa que a BARRA do site comunica (`quantificador.rotulo`)."""
    from espectro24.quantificador import fracao_e_rotulo

    return fracao_e_rotulo(mencoes, n)[1]


# ===========================================================================
# Parte 1b — recuperação
# ===========================================================================

def texto_da_query(bullet: dict) -> str:
    """`tema. descrição`. Medido contra só o `tema` (2026-10-19, pelo sinal do
    eixo descrito em `recuperar`): empate (lift 1,27 × 1,26 no publicado,
    1,24 × 1,26 no local, sem centrar). Fica a forma longa, que desambigua
    temas curtos como "atuações insuficientes"."""
    return f"{bullet['tema']}. {bullet['exemplo']}".strip()


def textos_de_referencia(resultado_dir: Path = RESULTADO_DIR,
                         excluir: set[str] = frozenset()) -> list[str]:
    """Os bullets PUBLICADOS do catálogo (fora o lote C22 e os filmes em
    `excluir`), como queries. É a referência fixa da centralização de
    `recuperar`: não depende do modelo que está sendo avaliado."""
    from espectro24.excecao_c22 import SLUGS as C22

    fora = []
    for p in sorted(Path(resultado_dir).glob("*.json")):
        d = _ler_json(p)
        if d.get("slug") in C22 or d.get("slug") in excluir or not d.get("eixos"):
            continue
        for b in d.get("buckets", []):
            for t in b.get("temas") or []:
                fora.append(f"{t['tema']}. {t.get('exemplo_parafraseado') or ''}".strip())
    return fora


def recuperar(bullets: list[dict], reviews_por_grupo: dict, encoder,
              referencia: list[str], k: int = K_RECUPERADAS) -> list[dict]:
    """Para cada bullet, a pontuação de CADA review do seu grupo e as `k`
    maiores.

    - `sim`: cosseno entre a query (`query: tema. descrição`) e o MELHOR
      pedaço da review (`encoder_e5.janelas`) — review longa é lida inteira,
      em janelas, e conta pelo trecho mais perto do tema;
    - `score` = `sim` − `deslocamento` da review, que é a média do `sim` dela
      contra os bullets de `referencia`. Ordena-se por `score`; desempate
      por id.

    **Por que centrar (medido, 2026-10-19).** Sem centrar, poucas reviews —
    genéricas, e em português/espanhol como as queries — aparecem no top-5
    de quase todo bullet do grupo (156 reviews distintas em 435 posições do
    lado publicado). O sinal independente do embedding é o EIXO (Parte 1a):
    a fração do top-5 que tem o eixo do bullet, contra a fração do grupo
    ("acaso"). Sem centrar: lift 1,27 (publicado) / 1,24 (local). Centrando
    pela média contra os 180 bullets dos dois lados: 1,61 / 1,47. Contra os
    1.780 bullets publicados do catálogo: 1,58 / 1,40, com 312 reviews
    distintas no top-5. Fica a referência do catálogo: quase o mesmo ganho,
    e ela não muda quando o modelo avaliado muda (é a régua do fine-tuning).
    O eixo é polaridade-cego e mais largo que o tema — serve para comparar
    variantes, não para dizer que a recuperação acerta.

    `reviews_por_grupo`: `{(slug, bucket): [ReviewBruta]}`. `encoder`: tem
    `queries(textos)` e `passagens(textos)` devolvendo vetores L2-normalizados.
    """
    import numpy as np

    from encoder_e5 import janelas

    pedacos, dono = [], []
    for chave in sorted(reviews_por_grupo):
        for r in reviews_por_grupo[chave]:
            for p in janelas(r.texto):
                pedacos.append(p)
                dono.append((chave, r.id))
    P = encoder.passagens(pedacos)
    rids = sorted(set(dono))
    col = {c: i for i, c in enumerate(rids)}

    def por_review(Q):
        """max sobre os pedaços de cada review: (n_queries, n_reviews)."""
        S = Q @ P.T
        M = np.full((S.shape[0], len(rids)), -2.0, dtype=np.float64)
        for j, c in enumerate(dono):
            M[:, col[c]] = np.maximum(M[:, col[c]], S[:, j])
        return M

    if not referencia:
        raise ValueError("referência vazia: sem ela não há como centrar")
    desloc = por_review(encoder.queries(referencia)).mean(axis=0)
    M = por_review(encoder.queries([texto_da_query(b) for b in bullets]))
    fora = []
    for qi, bl in enumerate(bullets):
        chave = (bl["slug"], bl["bucket"])
        cand = [(c[1], float(M[qi, i]), float(M[qi, i] - desloc[i]))
                for c, i in col.items() if c[0] == chave]
        ordem = sorted(cand, key=lambda x: (-x[2], x[0]))
        fora.append({"id_bullet": bl["id_bullet"],
                     "top": [{"rank": n + 1, "id": rid, "sim": round(sim, 4),
                              "score": round(sc, 4)}
                             for n, (rid, sim, sc) in enumerate(ordem[:k])],
                     "score": {rid: round(sc, 4) for rid, _, sc in sorted(cand)},
                     "sim": {rid: round(sim, 4) for rid, sim, _ in sorted(cand)}})
    return fora


# ===========================================================================
# Parte 2 — o juiz
# ===========================================================================

CRITERIO = """- **sim**: a review fala do mesmo ASSUNTO do tema e com o mesmo JUÍZO (elogio, crítica ou observação na mesma direção). Basta uma frase da review, em qualquer idioma.
- **não**: a review não fala do assunto; ou fala do assunto com o juízo oposto; ou é só compatível com o tema, sem dizê-lo.
- A descrição serve só para entender o que o tema quer dizer. Ignore quantas pessoas ela diz que concordam: aqui se julga UMA review."""

SYSTEM_JUIZ = f"""Você confere se UMA review de cinema sustenta UM tema.

O tema resume algo que um grupo de reviews diria sobre o filme. A pergunta é só sobre ESTA review: ela afirma, com as palavras dela, o que o tema afirma?

{CRITERIO}

Responda APENAS com um objeto JSON: {{"menciona": true}} ou {{"menciona": false}}."""

SCHEMA_JUIZ = {"type": "object",
               "properties": {"menciona": {"type": "boolean"}},
               "required": ["menciona"]}
# Teto de saída: a resposta tem ~8 tokens; 64 corta uma geração que
# desembestar sem custar minutos de CPU.
NUM_PREDICT_JUIZ = 64
ESTAGIO_JUIZ = "juiz_bullets"


def user_juiz(par: dict) -> str:
    """A review PRIMEIRO e o tema por último: pares consecutivos da mesma
    review (a entrada é ordenada por review) reaproveitam o prefixo no KV do
    Ollama, e a pergunta fica no fim, perto da resposta."""
    return (f"Review (nota {par['nivel']} de 5 estrelas):\n\n{par['texto']}\n\n"
            f"Tema: {par['tema']}\n"
            f"Descrição do tema: {par['exemplo']}\n\n"
            f"A review menciona este tema?")


def montar_entrada(eixo_bullets: list[dict], recuperacao: list[dict],
                   reviews: dict[tuple[str, str, str], object]) -> list[dict]:
    """Um par por (bullet, review recuperada), dos dois lados. Ordem: filme,
    grupo, review, lado, bullet — agrupado por review (prefixo do KV)."""
    por_id = {b["id_bullet"]: b for b in eixo_bullets}
    pares = []
    for rec in recuperacao:
        bl = por_id[rec["id_bullet"]]
        for t in rec["top"]:
            r = reviews[(bl["slug"], bl["bucket"], t["id"])]
            pares.append({
                "id_par": f"{bl['id_bullet']}|{t['id']}",
                "id_bullet": bl["id_bullet"], "lado": bl["lado"], "slug": bl["slug"],
                "bucket": bl["bucket"], "i": bl["i"], "tema": bl["tema"],
                "exemplo": bl["exemplo"], "review_id": t["id"], "nivel": r.nivel,
                "texto": r.texto, "rank": t["rank"], "sim": t["sim"], "score": t["score"],
                "review_tem_eixo": t["id"] in set(bl["ids_com_eixo"])})
    pares.sort(key=lambda p: (p["slug"], BUCKETS.index(p["bucket"]), p["review_id"],
                              LADOS.index(p["lado"]), p["i"]))
    ids = [p["id_par"] for p in pares]
    if len(ids) != len(set(ids)):
        raise ValueError("id_par repetido na entrada do juiz")
    return pares


def _ler_jsonl(caminho: Path) -> list[dict]:
    if not Path(caminho).exists():
        return []
    return [json.loads(l) for l in Path(caminho).read_text(encoding="utf-8").splitlines()
            if l.strip()]


def veredito_do_juiz(texto: str) -> bool:
    """`{"menciona": bool}` e nada além — qualquer outra forma é falha (o
    par fica sem veredito e é refeito na reexecução)."""
    dados = json.loads(texto)
    if not isinstance(dados, dict) or not isinstance(dados.get("menciona"), bool):
        raise ValueError(f"resposta fora do formato: {texto[:200]!r}")
    return dados["menciona"]


def rodar_juiz(pares: list[dict], saida: Path, chamar, *, modelo: str,
               think: str, progresso_a_cada: int = 25) -> dict:
    """Uma chamada por par, EM SEQUÊNCIA. Anexa um registro por chamada em
    `saida`; par com `ok: true` já gravado não é refeito. `chamar(system,
    user) -> dict` no formato de `local_ollama.resposta_json_local`."""
    feitos = {r["id_par"] for r in _ler_jsonl(saida) if r.get("ok")}
    pendentes = [p for p in pares if p["id_par"] not in feitos]
    print(f"  juiz: {len(feitos)} feitos · {len(pendentes)} pendentes", flush=True)
    exigir_fora_de_resultado(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    sha_system = _sha256_texto(SYSTEM_JUIZ)
    t0, n_falhas = time.time(), 0
    with saida.open("a", encoding="utf-8") as fh:
        for j, p in enumerate(pendentes, 1):
            base = {"id_par": p["id_par"], "modelo": modelo, "think": think,
                    "system_sha256": sha_system,
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            resp = None
            try:
                resp = chamar(SYSTEM_JUIZ, user_juiz(p))
                reg = {"ok": True, **base, "menciona": veredito_do_juiz(resp["texto"])}
            except Exception as e:  # noqa: BLE001
                n_falhas += 1
                reg = {"ok": False, **base, "erro": f"{type(e).__name__}: {e}",
                       "latencia_s": getattr(e, "latencia_s", None)}
                if resp is not None:
                    reg["resposta_crua"] = resp.get("texto")
            if resp is not None:
                reg.update({k: resp[k] for k in (
                    "modelo_efetivo", "finish_reason", "latencia_s", "leitura_prompt_s",
                    "geracao_s", "carga_s", "prompt_eval_count", "eval_count",
                    "custo_usd") if k in resp})
            fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
            fh.flush()
            if j % progresso_a_cada == 0 or j == len(pendentes):
                dt = time.time() - t0
                resta = dt / j * (len(pendentes) - j)
                print(f"    {j}/{len(pendentes)} · {dt / 60:.1f} min · "
                      f"falhas {n_falhas} · faltam ~{resta / 60:.0f} min", flush=True)
    return {"feitos_antes": len(feitos), "rodados": len(pendentes), "falhas": n_falhas,
            "parede_s": round(time.time() - t0, 1)}


def vereditos(entrada: list[dict], saida_regs: list[dict]) -> dict[str, bool]:
    """`{id_par: menciona}` — o ÚLTIMO registro `ok` de cada par. Exige um
    veredito para CADA par da entrada, com o system prompt de hoje: par sem
    veredito não vira "não" em silêncio."""
    sha = _sha256_texto(SYSTEM_JUIZ)
    fora = {}
    for r in saida_regs:
        if r.get("ok"):
            if r.get("system_sha256") != sha:
                raise ValueError(f"{r['id_par']}: julgado com outro system prompt "
                                 f"({r.get('system_sha256')}) — refaça o juiz")
            fora[r["id_par"]] = r["menciona"]
    faltam = [p["id_par"] for p in entrada if p["id_par"] not in fora]
    if faltam:
        raise ValueError(f"{len(faltam)} pares sem veredito do juiz (ex.: {faltam[:2]}) "
                         f"— rode `juiz` de novo: ele refaz só os que faltam")
    extras = set(fora) - {p["id_par"] for p in entrada}
    if extras:
        raise ValueError(f"{len(extras)} vereditos de pares que não estão na entrada")
    return fora


# --- estimativa de tempo ---------------------------------------------------

def medir_velocidade(registros: list[dict]) -> dict:
    """Velocidades do notebook, MEDIDAS nos registros do gate do mesmo modelo
    (uma review por chamada, JSON curto, prefixo fixo no KV): segundos de
    leitura por caractere de review, segundos por token gerado e a sobra por
    chamada (parede − leitura − geração: HTTP, gramática do schema)."""
    ok = [r for r in registros if r.get("ok") and r.get("geracao_s")]
    if not ok:
        raise ValueError("sem registros ok com tempos para medir a velocidade")
    return {
        "n_registros": len(ok),
        "leitura_s_por_char": sum(r["leitura_prompt_s"] for r in ok)
        / max(1, sum(r["n_chars"] for r in ok)),
        "geracao_s_por_token": sum(r["geracao_s"] for r in ok)
        / max(1, sum(r["eval_count"] for r in ok)),
        "sobra_s_mediana": statistics.median(
            r["latencia_s"] - r["leitura_prompt_s"] - r["geracao_s"] for r in ok),
        "latencia_s_mediana_gate": statistics.median(r["latencia_s"] for r in ok),
    }


TOKENS_RESPOSTA_JUIZ = 10   # `{"menciona": false}` + fim, folgado


def estimar_tempo(pares: list[dict], vel: dict) -> dict:
    """Soma, par a par: leitura do que é NOVO no prompt (review + tema +
    descrição; o system fica no KV), geração de ~10 tokens e a sobra. É
    estimativa a partir de medição de outro prompt, não medição."""
    novo = [len(p["texto"]) + len(p["tema"]) + len(p["exemplo"]) + 80 for p in pares]
    por_par = [c * vel["leitura_s_por_char"]
               + TOKENS_RESPOSTA_JUIZ * vel["geracao_s_por_token"]
               + vel["sobra_s_mediana"] for c in novo]
    total = sum(por_par) + 60  # carga do modelo + leitura do system na 1ª chamada
    return {"n_chamadas": len(pares), "chars_novos_total": sum(novo),
            "s_por_chamada_mediana": round(statistics.median(por_par), 2),
            "total_min": round(total / 60, 1),
            "faixa_min": [round(total / 60 * 0.75, 1), round(total / 60 * 2, 1)]}


# ===========================================================================
# Parte 3 — rotulagem do dono e validação do juiz
# ===========================================================================

def sortear_rotulo(pares: list[dict], por_lado: int = N_ROTULO_POR_LADO,
                   semente: int = SEMENTE) -> list[dict]:
    """`por_lado` pares de cada lado, espalhados: por filme (cotas iguais,
    sobra distribuída por sorteio), metade dos ranks 1-2 e metade dos ranks
    3-5 (para não sortear só os pares mais fáceis), no máximo UM par por
    bullet. A ordem final é embaralhada — os lados se misturam."""
    rng = random.Random(semente)
    escolhidos = []
    for lado in LADOS:
        do_lado = [p for p in pares if p["lado"] == lado]
        filmes = sorted({p["slug"] for p in do_lado})
        cota = {s: por_lado // len(filmes) for s in filmes}
        for s in rng.sample(filmes, por_lado % len(filmes)):
            cota[s] += 1
        usados: set[str] = set()
        for s in filmes:
            altos = [p for p in do_lado if p["slug"] == s and p["rank"] <= 2]
            baixos = [p for p in do_lado if p["slug"] == s and p["rank"] >= 3]
            rng.shuffle(altos)
            rng.shuffle(baixos)
            quer = {"alto": (cota[s] + 1) // 2, "baixo": cota[s] // 2}
            for estrato, fonte in (("alto", altos), ("baixo", baixos)):
                for p in fonte:
                    if quer[estrato] == 0:
                        break
                    if p["id_bullet"] in usados:
                        continue
                    escolhidos.append(p)
                    usados.add(p["id_bullet"])
                    quer[estrato] -= 1
            if any(quer.values()):
                raise ValueError(f"{lado}/{s}: bullets de menos para a cota {cota[s]}")
    rng.shuffle(escolhidos)
    return escolhidos


def montar_doc_rotulo(amostra: list[dict], titulos: dict[str, str], selo: str) -> str:
    """O documento que o dono LÊ. Não diz o lado, o modelo, a similaridade, o
    rank, nem a resposta do juiz (que nem existe quando ele é gerado)."""
    L = ["# Rotulagem manual — o bullet tem apoio nesta review?", "",
         f"São {len(amostra)} pares. Em cada um, um TEMA (o bullet da síntese, "
         "com a descrição que aparece em \"Aprofundar\") e UMA review do mesmo "
         "grupo. A pergunta é a mesma que o juiz vai responder, com o mesmo "
         "critério:", "", "> **A review menciona este tema?**", "",
         CRITERIO, "",
         f"Responda em `{ARQ_ROTULOS.name}` (mesma pasta), uma linha por par: "
         "`sim` ou `não`. Não deixe em branco — par sem rótulo trava a "
         "validação.", ""]
    for k, p in enumerate(amostra, 1):
        L += ["---", "", f"## P{k:02d} — {titulos[p['slug']]} · {GRUPO[p['bucket']]}", "",
              f"**Tema:** {p['tema']}", "", f"**Descrição:** {p['exemplo']}", "",
              f"**Review** (nota {p['nivel']} de 5 estrelas):", ""]
        L += ["> " + linha if linha.strip() else ">" for linha in p["texto"].splitlines()]
        L += ["", f"**P{k:02d} — menciona o tema?** sim / não", ""]
    L += ["---", "", f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    return "\n".join(L)


def ler_rotulos(caminho: Path, esperados: list[str]) -> dict[str, bool]:
    """`{par: True/False}` do CSV do dono. Exige TODOS os pares, cada um com
    `sim` ou `não` (`nao` aceito) — nada de rótulo em branco virar "não"."""
    fora: dict[str, bool] = {}
    with Path(caminho).open(encoding="utf-8", newline="") as fh:
        for linha in csv.DictReader(fh):
            par = (linha.get("par") or "").strip()
            v = _sem_acento((linha.get("rotulo") or "").strip())
            if not par:
                continue
            if v not in ("sim", "nao"):
                raise ValueError(f"{par}: rótulo {linha.get('rotulo')!r} — use sim ou não")
            if par in fora:
                raise ValueError(f"{par} rotulado duas vezes")
            fora[par] = v == "sim"
    faltam = [p for p in esperados if p not in fora]
    if faltam:
        raise ValueError(f"{len(faltam)} pares sem rótulo: {faltam}")
    extras = set(fora) - set(esperados)
    if extras:
        raise ValueError(f"pares que não existem na amostra: {sorted(extras)}")
    return fora


def wilson(acertos: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = acertos / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - m, 3), round(c + m, 3)]


def matriz(pares: list[tuple[bool, bool]]) -> dict:
    """`pares`: `(dono, juiz)`. Positivo = "menciona"."""
    vp = sum(1 for d, j in pares if d and j)
    fp = sum(1 for d, j in pares if not d and j)
    fn = sum(1 for d, j in pares if d and not j)
    vn = sum(1 for d, j in pares if not d and not j)
    return {"n": len(pares), "vp": vp, "fp": fp, "fn": fn, "vn": vn,
            "precisao": round(vp / (vp + fp), 3) if vp + fp else None,
            "precisao_ic95": wilson(vp, vp + fp),
            "recall": round(vp / (vp + fn), 3) if vp + fn else None,
            "recall_ic95": wilson(vp, vp + fn),
            "acuracia": round((vp + vn) / len(pares), 3) if pares else None}


# O critério para o resultado da Parte 2 VALER, fixado ANTES do rótulo
# existir (2026-10-19) — fixar depois de ver a matriz seria escolher a régua
# pelo resultado. É uma PROPOSTA do código, não uma medição: o dono pode
# trocá-la antes de rotular; trocá-la depois deve ficar registrado.
# Os dois lados importam: precisão baixa deixa bullet inventado passar como
# apoiado; recall baixo acusa de inventado o bullet que tem apoio.
CRITERIO_JUIZ = {"precisao_min": 0.8, "recall_min": 0.8}


def julgar_validacao(m: dict, criterio: dict = CRITERIO_JUIZ) -> dict:
    motivos = []
    if m["precisao"] is None or m["precisao"] < criterio["precisao_min"]:
        motivos.append(f"precisão {m['precisao']} < {criterio['precisao_min']}")
    if m["recall"] is None or m["recall"] < criterio["recall_min"]:
        motivos.append(f"recall {m['recall']} < {criterio['recall_min']}")
    return {"vale": not motivos, "motivos": motivos, "criterio": criterio}


# ===========================================================================
# Resultado final
# ===========================================================================

def apoio_por_bullet(eixo_bullets: list[dict], entrada: list[dict],
                     ver: dict[str, bool]) -> list[dict]:
    pares_de: dict[str, list[dict]] = {}
    for p in entrada:
        pares_de.setdefault(p["id_bullet"], []).append(p)
    fora = []
    for b in eixo_bullets:
        ps = sorted(pares_de.get(b["id_bullet"], []), key=lambda p: p["rank"])
        sim = [p["review_id"] for p in ps if ver[p["id_par"]]]
        q = quantificador_do_texto(b["exemplo"])
        fora.append({**{k: b[k] for k in ("id_bullet", "lado", "slug", "bucket", "i",
                                          "tema", "exemplo", "mencoes", "n", "eixo",
                                          "n_com_eixo", "suspeito", "sem_eixo",
                                          "declarado_acima_do_eixo")},
                     "n_julgadas": len(ps), "n_apoio": len(sim), "ids_apoio": sim,
                     "apoio_com_eixo": len(set(sim) & set(b["ids_com_eixo"])),
                     "quantificador_texto": q,
                     "faixa_declarada": faixa_do_declarado(b["mencoes"], b["n"])})
    return fora


def resumo(apoios: list[dict]) -> dict:
    n = len(apoios)
    return {"n_bullets": n,
            "apoio_ge1": sum(1 for a in apoios if a["n_apoio"] >= 1),
            "apoio_ge2": sum(1 for a in apoios if a["n_apoio"] >= 2),
            "frac_ge1": round(sum(1 for a in apoios if a["n_apoio"] >= 1) / n, 3) if n else None,
            "frac_ge2": round(sum(1 for a in apoios if a["n_apoio"] >= 2) / n, 3) if n else None,
            "sem_apoio": [a["id_bullet"] for a in apoios if a["n_apoio"] == 0],
            "suspeitos_eixo": sum(1 for a in apoios if a["suspeito"]),
            "sem_eixo": sum(1 for a in apoios if a["sem_eixo"])}


def cruzamento(apoios: list[dict]) -> dict:
    """Parte 1a × juiz: o bullet suspeito pelo eixo é o mesmo sem apoio?"""
    c = Counter()
    for a in apoios:
        p1 = "sem_eixo" if a["sem_eixo"] else ("suspeito" if a["suspeito"] else "eixo_ok")
        c[(p1, "sem_apoio" if a["n_apoio"] == 0 else "com_apoio")] += 1
    return {f"{p1}/{p2}": v for (p1, p2), v in sorted(c.items())}


# ===========================================================================
# Relatórios em markdown
# ===========================================================================

def _titulos(filmes_ou_docs) -> dict[str, str]:
    return {s: ((d["docs"]["publicado"] if "docs" in d else d).get("ficha") or {})
            .get("titulo") or s for s, d in filmes_ou_docs.items()}


def md_eixo(bl: list[dict], meta: dict, titulos: dict[str, str]) -> str:
    L = ["# Parte 1a — o eixo do bullet no consenso da classificação", "",
         "Para cada bullet, o eixo que a rotulagem do PRÓPRIO lado deu ao tema e "
         "quantas reviews do grupo (as mesmas que a síntese leu) têm esse eixo no "
         "consenso. **Grosseiro:** o eixo é mais largo que o tema — `atuacao` "
         "conta elogio e crítica de atuação juntos — então eixo alto não prova "
         "apoio; eixo em 0-1 review é que torna o bullet suspeito. Tema rotulado "
         "`livre` não tem eixo e não é medido aqui.", "",
         f"Consenso: `{meta['consenso']}` (sha256 das linhas dos 5 filmes "
         f"`{meta['consenso_sha256_filmes'][:16]}…`). Contagem conferida contra o "
         f"bloco `eixos` publicado em {meta['celulas_conferidas']} células, sem "
         "divergência.", "",
         "| lado | bullets | sem eixo (livre) | suspeitos (eixo ≤ 1) | declarado > eixo |",
         "|---|---|---|---|---|"]
    for lado in LADOS:
        x = [b for b in bl if b["lado"] == lado]
        L.append(f"| {lado} | {len(x)} | {sum(b['sem_eixo'] for b in x)} | "
                 f"{sum(b['suspeito'] for b in x)} | "
                 f"{sum(b['declarado_acima_do_eixo'] for b in x)} |")
    L += ["", "_declarado > eixo_: a síntese diz que mais reviews citam o tema do "
          "que as que têm o eixo inteiro — inflado mesmo pela régua larga (ou erro "
          "de recall da classificação).", ""]
    for slug in sorted({b["slug"] for b in bl}):
        L += [f"## {titulos[slug]}", ""]
        for lado in LADOS:
            L += [f"### {lado} — {AUTOR[lado]}", "",
                  "| grupo | tema | declarado | eixo | reviews com o eixo | |",
                  "|---|---|---|---|---|---|"]
            for b in [b for b in bl if b["slug"] == slug and b["lado"] == lado]:
                marca = ("**sem eixo**" if b["sem_eixo"] else
                         "**SUSPEITO**" if b["suspeito"] else
                         "declarado > eixo" if b["declarado_acima_do_eixo"] else "")
                L.append(f"| {b['bucket']} | {b['tema']} | {b['mencoes']}/{b['n']} | "
                         f"{b['eixo'] or 'livre'} | {b['n_com_eixo']}/{b['de_n']} | {marca} |")
            L.append("")
    return "\n".join(L)


def md_recuperacao(bl: list[dict], rec: list[dict], textos: dict, meta: dict,
                   titulos: dict[str, str]) -> str:
    por_id = {r["id_bullet"]: r for r in rec}
    L = ["# Parte 1b — as 5 reviews do grupo mais parecidas com cada bullet", "",
         f"Modelo: `{meta['modelo']}` (snapshot `{meta['snapshot']}`, pesos sha256 "
         f"`{meta['pesos_sha256'][:16]}…`), local, em numpy (`scripts/encoder_e5.py`). "
         f"Query = `query: <tema>. <descrição>`; review = `passage: <texto>`, em "
         f"janelas de até {meta['janela_chars']} caracteres, e a similaridade da "
         f"review é a do seu melhor trecho. {meta['n_pedacos']} pedaços para "
         f"{meta['n_reviews']} reviews; {meta['n_truncados']} truncados pelo teto "
         "de 512 tokens.", "",
         "**A ordem é por `score` = `sim` − o deslocamento da review** (a média do "
         f"`sim` dela contra os {meta['n_referencia']} bullets publicados do resto "
         "do catálogo). Sem centrar, poucas reviews genéricas, na língua das "
         "queries, dominavam o top-5 de quase todo bullet; a escolha foi medida "
         "pelo eixo e está em `checagem_bullets.recuperar`.", "",
         "**Como ler os números:** o e5 concentra os cossenos entre ~0,7 e 1,0 "
         "(FAQ do modelo); o que informa é a ORDEM dentro do grupo, não o valor "
         "absoluto. Ser parecida não é apoiar — quem decide apoio é o juiz "
         "(Parte 2). `eixo` ✓ = a review tem o eixo do bullet no consenso.", "",
         "| lado | bullets | `sim` médio do top-1 | `score` médio do top-5 | reviews do top-5 com o eixo do bullet |",
         "|---|---|---|---|---|"]
    for lado in LADOS:
        x = [b for b in bl if b["lado"] == lado]
        t1 = [por_id[b["id_bullet"]]["top"][0]["sim"] for b in x]
        t5 = [t["score"] for b in x for t in por_id[b["id_bullet"]]["top"]]
        com = [t["id"] in set(b["ids_com_eixo"]) for b in x if not b["sem_eixo"]
               for t in por_id[b["id_bullet"]]["top"]]
        L.append(f"| {lado} | {len(x)} | {statistics.mean(t1):.3f} | "
                 f"{statistics.mean(t5):+.3f} | {sum(com)}/{len(com)} |")
    L.append("")
    for slug in sorted({b["slug"] for b in bl}):
        L += [f"## {titulos[slug]}", ""]
        for lado in LADOS:
            L += [f"### {lado} — {AUTOR[lado]}", ""]
            for b in [b for b in bl if b["slug"] == slug and b["lado"] == lado]:
                L += [f"**[{b['bucket']}] {b['tema']}** — eixo `{b['eixo'] or 'livre'}`, "
                      f"declarado {b['mencoes']}/{b['n']}", "",
                      "| # | score | sim | eixo | review |", "|---|---|---|---|---|"]
                for t in por_id[b["id_bullet"]]["top"]:
                    nivel, txt = textos[(slug, b["bucket"], t["id"])]
                    trecho = " ".join(txt.split())
                    trecho = (trecho[:160] + "…") if len(trecho) > 160 else trecho
                    trecho = trecho.replace("|", "\\|")
                    marca = "✓" if t["id"] in set(b["ids_com_eixo"]) else ""
                    L.append(f"| {t['rank']} | {t['score']:+.3f} | {t['sim']:.3f} | {marca} | "
                             f"({nivel}★) {trecho} |")
                L.append("")
    return "\n".join(L)


def md_estimativa(est: dict, vel: dict, pares: list[dict], fonte: list[str]) -> str:
    por_lado = Counter(p["lado"] for p in pares)
    return "\n".join([
        "# Parte 2 — estimativa de chamadas e tempo do juiz", "",
        f"**{est['n_chamadas']} chamadas** ({por_lado['publicado']} do lado publicado, "
        f"{por_lado['local']} do lado local): um bullet × uma review por chamada, "
        f"{K_RECUPERADAS} reviews por bullet.", "",
        f"**Tempo estimado: ~{est['total_min']:.0f} min** (faixa "
        f"{est['faixa_min'][0]:.0f}–{est['faixa_min'][1]:.0f} min), "
        f"~{est['s_por_chamada_mediana']} s por chamada na mediana.", "",
        "**É estimativa, não medição.** Sai das velocidades do qwen3:14b MEDIDAS "
        f"no notebook, nos {vel['n_registros']} registros do gate de classificação "
        "(uma review por chamada, JSON curto, system no KV), aplicadas ao tamanho "
        "real de cada par:", "",
        f"- leitura do prompt: {vel['leitura_s_por_char'] * 1000:.2f} ms por caractere novo "
        "(review + tema + descrição; o system fica no KV);",
        f"- geração: {vel['geracao_s_por_token']:.3f} s por token, ~{TOKENS_RESPOSTA_JUIZ} "
        "tokens por resposta;",
        f"- sobra por chamada (parede − leitura − geração): {vel['sobra_s_mediana']:.2f} s "
        "(mediana);",
        f"- latência mediana do gate, para comparar: {vel['latencia_s_mediana_gate']:.1f} s "
        "(lá a resposta tinha ~35 tokens).", "",
        "A faixa vai de 0,75× a 2×: a ponta de cima cobre a gramática do schema "
        "custar mais que no gate e o notebook mais quente/ocupado.", "",
        "Fontes da velocidade: " + ", ".join(f"`{f}`" for f in fonte), ""])


def md_validacao(val: dict) -> str:
    def linha(nome, m):
        return (f"| {nome} | {m['n']} | {m['vp']} | {m['fp']} | {m['fn']} | {m['vn']} | "
                f"{m['precisao']} {m['precisao_ic95']} | {m['recall']} {m['recall_ic95']} | "
                f"{m['acuracia']} |")
    v = val["julgamento"]
    L = ["# Parte 3 — o juiz contra o rótulo do dono", "",
         ("**O JUIZ PASSOU no critério**" if v["vale"] else
          "**O JUIZ FALHOU — o resultado da Parte 2 NÃO VALE**: " + "; ".join(v["motivos"])),
         "", f"Critério (fixado antes do rótulo): precisão ≥ {v['criterio']['precisao_min']} "
         f"e recall ≥ {v['criterio']['recall_min']}. Positivo = \"menciona\".", "",
         "| recorte | n | VP | FP | FN | VN | precisão [IC95] | recall [IC95] | acurácia |",
         "|---|---|---|---|---|---|---|---|---|",
         linha("todos", val["geral"])]
    for lado in LADOS:
        L.append(linha(lado, val["por_lado"][lado]))
    L += ["", "Com 40 pares os intervalos são largos; a diferença entre os lados "
          "importa porque um juiz que erra mais num lado enviesa a comparação.", "",
          "## Erros do juiz", ""]
    for e in val["erros"]:
        L.append(f"- {e['par']} ({e['lado']}, {e['slug']}/{e['bucket']}): dono "
                 f"{'sim' if e['dono'] else 'não'}, juiz {'sim' if e['juiz'] else 'não'} "
                 f"— tema \"{e['tema']}\"")
    if not val["erros"]:
        L.append("_(nenhum)_")
    return "\n".join(L) + "\n"


def md_final(apoios: list[dict], val: dict, titulos: dict[str, str]) -> str:
    v = val["julgamento"]
    L = ["# Resultado final — apoio dos bullets nas reviews do próprio grupo", ""]
    if not v["vale"]:
        L += ["> **ESTE RESULTADO NÃO VALE.** O juiz falhou na validação contra o "
              "rótulo do dono (" + "; ".join(v["motivos"]) + "). Os números abaixo "
              "estão aqui só para auditoria; nenhuma conclusão sobre os bullets "
              "pode sair deles.", ""]
    else:
        g = val["geral"]
        L += [f"Juiz validado: precisão {g['precisao']} {g['precisao_ic95']}, recall "
              f"{g['recall']} {g['recall_ic95']} em {g['n']} pares rotulados pelo dono.", ""]
    L += [f"Apoio = o juiz disse \"menciona\" para a review. Cada bullet foi julgado "
          f"contra as {K_RECUPERADAS} reviews do grupo mais parecidas com ele, então o "
          f"apoio vai de 0 a {K_RECUPERADAS}: **o teto é {K_RECUPERADAS}**, e um bullet "
          "que declara 25 menções não tem como mostrar mais que 5 aqui.", "",
          "| lado | bullets | apoio ≥ 1 | apoio ≥ 2 | sem apoio |", "|---|---|---|---|---|"]
    for lado in LADOS:
        r = resumo([a for a in apoios if a["lado"] == lado])
        L.append(f"| {lado} | {r['n_bullets']} | {r['apoio_ge1']} ({r['frac_ge1']:.0%}) | "
                 f"{r['apoio_ge2']} ({r['frac_ge2']:.0%}) | {len(r['sem_apoio'])} |")
    L += ["", "## Por filme", "", "| filme | lado | bullets | apoio ≥ 1 | apoio ≥ 2 | sem apoio |",
          "|---|---|---|---|---|---|"]
    for slug in sorted({a["slug"] for a in apoios}):
        for lado in LADOS:
            r = resumo([a for a in apoios if a["lado"] == lado and a["slug"] == slug])
            L.append(f"| {titulos[slug]} | {lado} | {r['n_bullets']} | "
                     f"{r['frac_ge1']:.0%} | {r['frac_ge2']:.0%} | {len(r['sem_apoio'])} |")
    L += ["", "## Bullets sem apoio nenhum", ""]
    for lado in LADOS:
        L += [f"### {lado} — {AUTOR[lado]}", ""]
        x = [a for a in apoios if a["lado"] == lado and a["n_apoio"] == 0]
        for a in x:
            L.append(f"- **{titulos[a['slug']]} / {a['bucket']}: {a['tema']}** — "
                     f"\"{a['exemplo']}\" (declarado {a['mencoes']}/{a['n']}; eixo "
                     f"`{a['eixo'] or 'livre'}` em {a['n_com_eixo']} reviews)")
        if not x:
            L.append("_(nenhum)_")
        L.append("")
    L += ["## Quantificador do bullet × reviews que o sustentam", "",
          "`texto`: o primeiro quantificador da descrição (\"muitas\", \"várias\"…) e a "
          "faixa do site em que ele cai; `barra`: a faixa que a contagem declarada "
          "comunica na tela. `apoio`: reviews que o juiz confirmou, de "
          f"{K_RECUPERADAS}. `eixo`: reviews com o eixo do bullet (Parte 1a).", ""]
    for lado in LADOS:
        L += [f"### {lado}", "", "| filme | grupo | tema | texto | declarado (barra) | apoio | eixo |",
              "|---|---|---|---|---|---|---|"]
        for a in [a for a in apoios if a["lado"] == lado]:
            q = a["quantificador_texto"]
            qt = f"{q['palavra']} → {q['faixa']}" if q else "—"
            L.append(f"| {titulos[a['slug']]} | {a['bucket']} | {a['tema']} | {qt} | "
                     f"{a['mencoes']}/{a['n']} ({a['faixa_declarada']}) | "
                     f"{a['n_apoio']}/{a['n_julgadas']} | {a['n_com_eixo'] if a['eixo'] else 'livre'} |")
        L.append("")
    L += ["## Comparação com a medida grosseira (Parte 1a)", "",
          "| lado | Parte 1a / juiz | bullets |", "|---|---|---|"]
    for lado in LADOS:
        for k, n in cruzamento([a for a in apoios if a["lado"] == lado]).items():
            L.append(f"| {lado} | {k} | {n} |")
    L += ["", "`suspeito/sem_apoio`: as duas medidas concordam que falta apoio; "
          "`eixo_ok/sem_apoio`: o eixo é frequente mas nenhuma das reviews mais "
          "parecidas diz o tema — o caso que a régua larga não pega.", ""]
    return "\n".join(L)


# ===========================================================================
# Subcomandos
# ===========================================================================

def _slugs(a) -> list[str]:
    from gerar_prosa_local import FILMES_COMPARACAO

    return list(a.slug) or list(FILMES_COMPARACAO)


def _meta_consenso(slugs) -> dict:
    from espectro24 import eixos as E

    caminho = RAIZ / E.CONSENSO_VERIFICADO
    linhas = sorted(l for l in caminho.read_text(encoding="utf-8").splitlines()
                    if l.strip() and json.loads(l).get("slug") in set(slugs))
    return {"consenso": E.CONSENSO_VERIFICADO,
            "consenso_sha256_filmes": _sha256_texto("\n".join(linhas))}


def cmd_eixo(a) -> None:
    slugs = _slugs(a)
    filmes = carregar_filmes(slugs, a.local_dir)
    bl = medida_eixo(filmes)
    meta = {**_meta_consenso(slugs), "filmes": slugs, "local_dir": str(a.local_dir),
            "celulas_conferidas": sum(f["celulas_conferidas"] for f in filmes.values()),
            "suspeito_ate": SUSPEITO_ATE}
    _json(a.dir / ARQ_EIXO, {"meta": meta, "bullets": bl})
    _escrever(a.dir / "parte1_eixo.md", md_eixo(bl, meta, _titulos(filmes)))
    print(f"{len(bl)} bullets · {meta['celulas_conferidas']} células conferidas → "
          f"{a.dir / ARQ_EIXO}")


def cmd_recuperar(a) -> None:
    import encoder_e5 as E5

    slugs = _slugs(a)
    eixo = _ler_json(a.dir / ARQ_EIXO)
    filmes = carregar_filmes(slugs, a.local_dir)
    bl = [b for b in eixo["bullets"] if b["slug"] in set(slugs)]
    grupos = {(s, b): rs for s, f in filmes.items() for b, rs in f["reviews"].items()}
    enc = E5.Encoder.do_disco()
    pedacos = [p for rs in grupos.values() for r in rs for p in E5.janelas(r.texto)]
    t0 = time.time()
    ref = textos_de_referencia(excluir=set(slugs))
    rec = recuperar(bl, grupos, enc, ref)
    meta = {"modelo": E5.MODELO_ID, "snapshot": enc._dir.name,
            "n_referencia": len(ref), "referencia_sha256": _sha256_texto("\n".join(ref)),
            "pesos_sha256": _sha256_arquivo(enc._dir / "model.safetensors"),
            "janela_chars": E5.JANELA_CHARS, "k": K_RECUPERADAS,
            "n_reviews": sum(len(rs) for rs in grupos.values()),
            "n_pedacos": len(pedacos),
            "n_truncados": sum(enc.truncou("passage: " + p) for p in pedacos),
            "tempo_s": round(time.time() - t0, 1)}
    if meta["n_truncados"]:
        raise SystemExit(f"{meta['n_truncados']} pedaços passaram de 512 tokens — "
                         f"reduza JANELA_CHARS: o modelo não leria o fim deles")
    _json(a.dir / ARQ_RECUP, {"meta": meta, "recuperacao": rec})
    textos = {(s, b, r.id): (r.nivel, r.texto) for (s, b), rs in grupos.items() for r in rs}
    _escrever(a.dir / "parte1_recuperacao.md",
              md_recuperacao(bl, rec, textos, meta, _titulos(filmes)))
    print(f"{len(rec)} bullets · {meta['n_pedacos']} pedaços · {meta['tempo_s']}s → "
          f"{a.dir / ARQ_RECUP}")


# Os registros do gate do qwen3:14b no notebook (branch `gate-local`).
MEDICAO_DIR = RAIZ / "resultado" / "auditoria-acuracia" / "local" / "qwen3-14b"
ARQS_VELOCIDADE = [f"classificacao_passe_{n}.jsonl" for n in (1, 2, 3)]


def cmd_preparar_juiz(a) -> None:
    eixo = _ler_json(a.dir / ARQ_EIXO)
    rec = _ler_json(a.dir / ARQ_RECUP)
    slugs = eixo["meta"]["filmes"]
    filmes = carregar_filmes(slugs, Path(eixo["meta"]["local_dir"]))
    reviews = {(s, b, r.id): r for s, f in filmes.items()
               for b, rs in f["reviews"].items() for r in rs}
    pares = montar_entrada(eixo["bullets"], rec["recuperacao"], reviews)
    _escrever(a.dir / ARQ_ENTRADA,
              "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pares))
    fontes = [a.medicao_dir / f for f in ARQS_VELOCIDADE if (a.medicao_dir / f).exists()]
    if not fontes:
        raise SystemExit(f"sem os registros do gate do qwen3:14b em {a.medicao_dir} "
                         f"para medir a velocidade — eles estão no branch gate-local")
    regs = [r for f in fontes for r in _ler_jsonl(f)]
    vel = medir_velocidade(regs)
    est = estimar_tempo(pares, vel)
    nomes = [f"{f.parent.name}/{f.name}" for f in fontes]
    _escrever(a.dir / "juiz_estimativa.md", md_estimativa(est, vel, pares, nomes))
    print(f"{len(pares)} pares → {a.dir / ARQ_ENTRADA} · ~{est['total_min']:.0f} min "
          f"({est['faixa_min'][0]:.0f}–{est['faixa_min'][1]:.0f})")


def cmd_amostra_rotulo(a) -> None:
    pares = _ler_jsonl(a.dir / ARQ_ENTRADA)
    if not pares:
        raise SystemExit(f"{a.dir / ARQ_ENTRADA} vazio — rode preparar-juiz")
    if (a.dir / ARQ_ROTULOS).exists():
        with (a.dir / ARQ_ROTULOS).open(encoding="utf-8", newline="") as fh:
            preenchidos = [l for l in csv.DictReader(fh) if (l.get("rotulo") or "").strip()]
        if preenchidos:
            raise SystemExit(f"{a.dir / ARQ_ROTULOS} já tem {len(preenchidos)} rótulos — "
                             f"o sorteio nunca é refeito por cima do rótulo do dono")
        if not a.refazer:
            raise SystemExit(f"{a.dir / ARQ_ROTULOS} já existe (vazio) — use --refazer "
                             f"para sortear de novo")
    amostra = sortear_rotulo(pares)
    mapa = {"semente": SEMENTE, "pares": {f"P{k:02d}": p["id_par"]
                                          for k, p in enumerate(amostra, 1)}}
    selo = _sha256_texto(json.dumps(mapa, sort_keys=True, ensure_ascii=False))
    _json(a.dir / ARQ_MAPA, {**mapa, "sha256": selo})
    eixo = _ler_json(a.dir / ARQ_EIXO)
    titulos = {s: (_ler_json(RESULTADO_DIR / f"{s}.json").get("ficha") or {}).get("titulo") or s
               for s in eixo["meta"]["filmes"]}
    _escrever(a.dir / ARQ_DOC_ROTULO, montar_doc_rotulo(amostra, titulos, selo))
    _escrever(a.dir / ARQ_ROTULOS,
              "par,rotulo\n" + "".join(f"P{k:02d},\n" for k in range(1, len(amostra) + 1)))
    print(f"{len(amostra)} pares → {a.dir / ARQ_DOC_ROTULO} · selo {selo[:16]}…")


def cmd_juiz(a) -> None:
    from gerar_prosa_local import _exigir_modelo

    from espectro24 import local_ollama

    think = local_ollama.nivel_think()
    pares = _ler_jsonl(a.dir / ARQ_ENTRADA)
    if not pares:
        raise SystemExit(f"{a.dir / ARQ_ENTRADA} não encontrado ou vazio")
    _exigir_modelo(a.modelo)
    print(f"{len(pares)} pares · Ollama {a.modelo} · think={think}", flush=True)

    def chamar(system: str, user: str) -> dict:
        return local_ollama.resposta_json_local(
            system, user, estagio=ESTAGIO_JUIZ, modelo=a.modelo, schema=SCHEMA_JUIZ,
            num_predict=NUM_PREDICT_JUIZ)

    r = rodar_juiz(pares, a.dir / ARQ_SAIDA, chamar, modelo=a.modelo, think=think)
    regs = _ler_jsonl(a.dir / ARQ_SAIDA)
    ok = {x["id_par"] for x in regs if x.get("ok")}
    faltam = sum(1 for p in pares if p["id_par"] not in ok)
    print(f"\n{r['rodados']} chamadas em {r['parede_s'] / 60:.0f} min · falhas {r['falhas']} · "
          f"pares sem veredito: {faltam}" + (" — rode de novo" if faltam else " — completo"))


def cmd_validar_juiz(a) -> None:
    mapa = _ler_json(a.dir / ARQ_MAPA)
    selo = _sha256_texto(json.dumps({k: mapa[k] for k in ("semente", "pares")},
                                    sort_keys=True, ensure_ascii=False))
    if selo != mapa["sha256"]:
        raise SystemExit("o mapeamento da rotulagem não confere com o próprio selo")
    entrada = _ler_jsonl(a.dir / ARQ_ENTRADA)
    ver = vereditos(entrada, _ler_jsonl(a.dir / ARQ_SAIDA))
    dono = ler_rotulos(a.dir / ARQ_ROTULOS, list(mapa["pares"]))
    por_par = {p["id_par"]: p for p in entrada}
    linhas = []
    for par, id_par in mapa["pares"].items():
        p = por_par[id_par]
        linhas.append({"par": par, "id_par": id_par, "lado": p["lado"], "slug": p["slug"],
                       "bucket": p["bucket"], "tema": p["tema"],
                       "dono": dono[par], "juiz": ver[id_par]})
    geral = matriz([(x["dono"], x["juiz"]) for x in linhas])
    val = {"selo_mapa": selo, "geral": geral,
           "por_lado": {lado: matriz([(x["dono"], x["juiz"]) for x in linhas
                                      if x["lado"] == lado]) for lado in LADOS},
           "julgamento": julgar_validacao(geral),
           "erros": [x for x in linhas if x["dono"] != x["juiz"]], "pares": linhas}
    _json(a.dir / ARQ_VALIDACAO, val)
    _escrever(a.dir / "validacao_juiz.md", md_validacao(val))
    print(("JUIZ VALE" if val["julgamento"]["vale"] else
           "JUIZ NÃO VALE: " + "; ".join(val["julgamento"]["motivos"])) +
          f" · P={geral['precisao']} R={geral['recall']} (n={geral['n']})")


def cmd_relatorio(a) -> None:
    if not (a.dir / ARQ_VALIDACAO).exists():
        raise SystemExit("sem validacao_juiz.json: o resultado do juiz não se publica "
                         "antes de o juiz ser medido contra o rótulo do dono (Parte 3)")
    val = _ler_json(a.dir / ARQ_VALIDACAO)
    eixo = _ler_json(a.dir / ARQ_EIXO)
    entrada = _ler_jsonl(a.dir / ARQ_ENTRADA)
    ver = vereditos(entrada, _ler_jsonl(a.dir / ARQ_SAIDA))
    apoios = apoio_por_bullet(eixo["bullets"], entrada, ver)
    titulos = {s: (_ler_json(RESULTADO_DIR / f"{s}.json").get("ficha") or {}).get("titulo") or s
               for s in eixo["meta"]["filmes"]}
    final = {"vale": val["julgamento"]["vale"], "validacao": val["geral"],
             "por_lado": {lado: resumo([x for x in apoios if x["lado"] == lado])
                          for lado in LADOS},
             "por_filme": {s: {lado: resumo([x for x in apoios if x["lado"] == lado
                                             and x["slug"] == s]) for lado in LADOS}
                           for s in eixo["meta"]["filmes"]},
             "cruzamento_parte1": {lado: cruzamento([x for x in apoios if x["lado"] == lado])
                                   for lado in LADOS},
             "bullets": apoios}
    _json(a.dir / "resultado_final.json", final)
    _escrever(a.dir / "resultado_final.md", md_final(apoios, val, titulos))
    print(("" if final["vale"] else "NÃO VALE (juiz reprovado) · ") +
          " · ".join(f"{lado}: ≥1 {final['por_lado'][lado]['frac_ge1']:.0%}, "
                     f"≥2 {final['por_lado'][lado]['frac_ge2']:.0%}" for lado in LADOS))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome, func in (("eixo", cmd_eixo), ("recuperar", cmd_recuperar),
                       ("preparar-juiz", cmd_preparar_juiz),
                       ("amostra-rotulo", cmd_amostra_rotulo), ("juiz", cmd_juiz),
                       ("validar-juiz", cmd_validar_juiz), ("relatorio", cmd_relatorio)):
        p = sub.add_parser(nome)
        p.set_defaults(func=func)
        p.add_argument("--dir", type=Path, required=True,
                       help="pasta da checagem (NUNCA dentro de resultado/)")
        if nome in ("eixo", "recuperar"):
            p.add_argument("--local-dir", type=Path, required=True,
                           help="a prosa local (<slug>.json), p.ex. prosa-local-qwen3")
            p.add_argument("--slug", action="append", default=[])
        if nome == "juiz":
            p.add_argument("--modelo", required=True, help="ex.: qwen3:14b")
        if nome == "preparar-juiz":
            p.add_argument("--medicao-dir", type=Path, default=MEDICAO_DIR,
                           help="registros do gate do qwen3:14b (velocidade medida)")
        if nome == "amostra-rotulo":
            p.add_argument("--refazer", action="store_true")
    a = ap.parse_args(argv)
    exigir_fora_de_resultado(a.dir)
    a.func(a)


if __name__ == "__main__":
    main()
