#!/usr/bin/env python3
"""Experimento 6 (NÃO é bump de versão): corrige o RECALL do classificador
de temas (estágio 2), motivado por `AUDITORIA_PRECISAO.md`.

Contexto: no bucket `cure`/negativas (50 reviews), o tema `t1` (ritmo lento)
foi marcado em 23 reviews pelo experimento 5, com precisão alta (~96%,
auditoria humana: 22/23 corretas). O problema é RECALL — 8 das 13 reviews
sem NENHUM tema deveriam ter recebido um (7 para t1, 1 para t4), e o viés
identificado é que o classificador reage a VOLUME DE TEXTO: reviews curtas e
diretas ("boring", "cure me from the boredom") ficam sem tema, enquanto a
review mais longa do bucket (índice 9) recebeu os 6 temas — inclusive t1,
apesar de dizer explicitamente que o ritmo NÃO é o problema (negação
ignorada). Contagem humana verificada: ~30 das 50 reviews reclamam de
ritmo/tédio; o alvo desta rodada é o t1 chegar perto de 30, sem estourar.

Desenho: 3 variantes sobre o MESMO bucket, reusando os 6 temas do estágio 1
já persistidos em `resultado/experimento_local/v5/cure/negativas.json`
(campo `estagio1_temas_propostos`) — o estágio 1 NÃO é executado de novo. A
única variável entre variantes é o prompt/lote do estágio 2:

  V1 = estágio 2 do exp.5 + bloco RECALL, lote de 25 reviews
  V2 = estágio 2 do exp.5 + bloco RECALL, lote de 10 reviews
  V3 = estágio 2 do exp.5 SEM o bloco, lote de 10 reviews (controle)

O bloco RECALL instrui o modelo a (a) não usar o tamanho da review como
proxy para quantos temas marcar, (b) tratar correspondência semântica ou
indireta como suficiente, e (c) respeitar negação explícita (tema mencionado
só para dizer que NÃO foi um problema não conta).

Reviews 100% do cache (`Fetcher(offline=True)`) — confirma `n_network=0`
antes de qualquer chamada. ZERO Gemini, ZERO Letterboxd, ZERO TMDB.
think=false em TODAS as chamadas, timeout de 300s por chamada. Grava por
lote assim que termina; falha de 1 lote não aborta a variante.

Reusa (import, não reescreve) do experimento 5: `_prompt_estagio2` (para o
texto-base do estágio 2), `_build_user_message_reviews`, `_lotes`, `_chamar`.
A montagem da resposta final e do bloco RECALL é própria deste script.

NÃO toca em resultado/*.json de produção, nos experimentos 1-5, em
SPEC.md, nem em `build_system_prompt`/`synthesize.py` (só leitura).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import run_pipeline  # noqa: E402

import comparar_sintese_local_v5 as v5  # noqa: E402

SLUG = "cure"
BUCKET_NOME = "negativas"
MODEL = "qwen3-espectro"
OUT_DIR = ROOT / "resultado" / "experimento_local" / "v6"
TEMAS_FONTE = ROOT / "resultado" / "experimento_local" / "v5" / "cure" / "negativas.json"

BLOCO_RECALL = """\

COMO CLASSIFICAR
O tamanho da review não indica quantos temas ela aborda. Uma review de uma \
linha que diz apenas que o filme é entediante aborda o tema de ritmo tão \
claramente quanto uma resenha longa — marque-a. Reviews curtas e diretas \
são frequentemente as mais claras.
Marque o tema quando a review o aborda, mesmo com outras palavras ou de \
forma indireta.
ATENÇÃO À NEGAÇÃO: se a review menciona um tema apenas para dizer que ele \
NÃO foi um problema para ela, não marque. Exemplo: alguém que escreve que \
o ritmo é lento mas que isso não a incomodou não deve ser marcada com o \
tema de ritmo."""

VARIANTES = [
    {"nome": "v1_bloco_lote25", "com_bloco": True, "lote_tamanho": 25},
    {"nome": "v2_bloco_lote10", "com_bloco": True, "lote_tamanho": 10},
    {"nome": "v3_sembloco_lote10", "com_bloco": False, "lote_tamanho": 10},
]

# Índices (0-based, mesma indexação de `amostra_completa`/AUDITORIA_PRECISAO.md)
# que o gabarito humano diz que DEVERIAM ter recebido tema, mas o exp.5 deixou
# sem nenhum:
GABARITO_T1_FALTANTES = [6, 21, 23, 24, 26, 34, 49]
GABARITO_T4_FALTANTES = [11]
INDICE_NEGACAO = 9  # diz explicitamente que ritmo NÃO é o problema


def _prompt_estagio2_variante(temas: list[dict], com_bloco: bool) -> str:
    base = v5._prompt_estagio2(temas)
    if com_bloco:
        return base + "\n" + BLOCO_RECALL
    return base


def _rodar_estagio2_variante(reviews, temas: list[dict], *, com_bloco: bool,
                              lote_tamanho: int):
    """Mesma lógica de `v5._rodar_estagio2`, mas com prompt e lote
    parametrizáveis por variante (o estágio 2 de v5 tem lote fixo via
    constante de módulo — aqui reimplementamos o laço para poder variar o
    tamanho do lote por chamada sem mutar estado global do módulo v5)."""
    ids_validos = {t["id"] for t in temas}
    contagem = {t["id"]: 0 for t in temas}
    atribuicoes: dict[int, list[str] | None] = {}
    ids_invalidos_total = 0
    log_lotes = []
    system = _prompt_estagio2_variante(temas, com_bloco)

    for offset, lote in v5._lotes(reviews, lote_tamanho):
        user = v5._build_user_message_reviews(lote)
        parsed, log = v5._chamar(system, user)
        registro_lote = {
            "offset": offset, "tamanho": len(lote), "chamadas": log,
            "ok": parsed is not None,
        }
        if parsed is None:
            for i in range(len(lote)):
                atribuicoes[offset + i] = None
            registro_lote["reviews_nao_classificadas"] = len(lote)
            log_lotes.append(registro_lote)
            continue

        invalidos_neste_lote = 0
        for chave, ids in (parsed.items() if isinstance(parsed, dict) else []):
            try:
                idx_local = int(chave) - 1
            except (TypeError, ValueError):
                continue
            if not (0 <= idx_local < len(lote)):
                continue
            ids_lista = ids if isinstance(ids, list) else []
            validos = []
            for tid in ids_lista:
                if tid in ids_validos:
                    validos.append(tid)
                    contagem[tid] += 1
                else:
                    invalidos_neste_lote += 1
            atribuicoes[offset + idx_local] = validos
        for i in range(len(lote)):
            atribuicoes.setdefault(offset + i, [])
        registro_lote["ids_invalidos"] = invalidos_neste_lote
        ids_invalidos_total += invalidos_neste_lote
        log_lotes.append(registro_lote)

    return contagem, atribuicoes, ids_invalidos_total, log_lotes


def _carregar_reviews_e_confirmar_offline():
    print(f"Carregando reviews de '{SLUG}' do cache (offline, zero rede)...",
          file=sys.stderr)
    fetcher = Fetcher(cache_dir=str(ROOT / "resultado" / "cache"), offline=True)
    buckets, _niveis, _distrib = run_pipeline(
        fetcher, SLUG, datetime.now(timezone.utc).isoformat(),
        synth=False, distribuicao=False,
    )
    n_network = fetcher.n_network
    bucket = next((b for b in buckets if b.nome == BUCKET_NOME), None)
    if bucket is None:
        raise SystemExit(f"bucket '{BUCKET_NOME}' não encontrado para '{SLUG}'")
    return bucket.reviews_analisadas, n_network


def _confirmar_paridade_com_fonte(reviews, fonte_amostra: list[dict]) -> None:
    """Confere que a ordem/conteúdo das reviews carregadas agora bate
    índice a índice com `amostra_completa` do experimento 5 — sem essa
    paridade, os índices do gabarito humano (que se referem ao JSON do
    exp.5) não seriam comparáveis aos resultados desta rodada."""
    if len(reviews) != len(fonte_amostra):
        raise SystemExit(
            f"paridade quebrada: {len(reviews)} reviews carregadas vs "
            f"{len(fonte_amostra)} em negativas.json")
    for i, (r, item) in enumerate(zip(reviews, fonte_amostra)):
        if r.rating != item["rating"] or r.effective_text != item["texto"]:
            raise SystemExit(
                f"paridade quebrada no índice {i}: cache atual difere de "
                f"resultado/experimento_local/v5/cure/negativas.json")


def _rodar_variante(nome: str, reviews, temas: list[dict], *, com_bloco: bool,
                    lote_tamanho: int) -> dict:
    print(f"\n=== variante '{nome}' (bloco={com_bloco}, lote={lote_tamanho}) ===",
          file=sys.stderr)
    t0 = time.time()
    contagem, atribuicoes, ids_invalidos, log_lotes = _rodar_estagio2_variante(
        reviews, temas, com_bloco=com_bloco, lote_tamanho=lote_tamanho)
    tempo_total = time.time() - t0
    n_chamadas = sum(len(lote["chamadas"]) for lote in log_lotes)
    print(f"  concluída em {tempo_total:.1f}s, {len(log_lotes)} lote(s), "
          f"{n_chamadas} chamada(s)", file=sys.stderr)

    n_sem_tema = sum(1 for v in atribuicoes.values() if v == [])
    n_nao_classificadas = sum(1 for v in atribuicoes.values() if v is None)

    resultado = {
        "variante": nome,
        "com_bloco_recall": com_bloco,
        "lote_tamanho": lote_tamanho,
        "n_reviews": len(reviews),
        "tempo_total_s": round(tempo_total, 2),
        "n_chamadas": n_chamadas,
        "tempo_medio_por_chamada_s": (round(tempo_total / n_chamadas, 2)
                                       if n_chamadas else None),
        "contagem_por_tema": contagem,
        "n_reviews_sem_tema": n_sem_tema,
        "n_reviews_nao_classificadas_falha_lote": n_nao_classificadas,
        "estagio2_ids_invalidos_total": ids_invalidos,
        "estagio2_lotes": log_lotes,
        "atribuicoes": {str(k): v for k, v in sorted(atribuicoes.items())},
    }
    out_path = OUT_DIR / f"{nome}.json"
    out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"  gravado em {out_path}", file=sys.stderr)
    return resultado


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fonte = json.loads(TEMAS_FONTE.read_text(encoding="utf-8"))
    temas = fonte["estagio1_temas_propostos"]
    print(f"Reusando {len(temas)} tema(s) do estágio 1 (exp.5): "
          f"{[t['tema'] for t in temas]}", file=sys.stderr)

    reviews, n_network = _carregar_reviews_e_confirmar_offline()
    print(f"n_network={n_network} (esperado 0)", file=sys.stderr)
    if n_network != 0:
        print("ABORTANDO: requisição(ões) de rede detectada(s).", file=sys.stderr)
        return 1

    _confirmar_paridade_com_fonte(reviews, fonte["amostra_completa"])
    print("Paridade com resultado/experimento_local/v5/cure/negativas.json "
          "confirmada (mesma ordem/conteúdo de reviews).", file=sys.stderr)

    resumo = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "slug": SLUG, "bucket": BUCKET_NOME, "n_reviews": len(reviews),
        "n_network": n_network,
        "estagio1_temas_reusados_de": str(TEMAS_FONTE.relative_to(ROOT)),
        "estagio1_temas_propostos": temas,
        "variantes": [],
    }

    for v in VARIANTES:
        r = _rodar_variante(v["nome"], reviews, temas,
                            com_bloco=v["com_bloco"], lote_tamanho=v["lote_tamanho"])
        resumo["variantes"].append({
            "variante": r["variante"], "com_bloco_recall": r["com_bloco_recall"],
            "lote_tamanho": r["lote_tamanho"], "tempo_total_s": r["tempo_total_s"],
            "n_chamadas": r["n_chamadas"],
            "n_reviews_sem_tema": r["n_reviews_sem_tema"],
            "contagem_por_tema": r["contagem_por_tema"],
        })

    resumo_path = OUT_DIR / "resumo.json"
    resumo_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"\nResumo gravado em {resumo_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
