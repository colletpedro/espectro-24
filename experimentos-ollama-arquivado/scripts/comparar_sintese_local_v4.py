#!/usr/bin/env python3
"""Experimento 4 (NÃO é bump de versão): síntese §D local em DOIS ESTÁGIOS,
com a CONTAGEM feita em código em vez de pelo LLM.

Diagnóstico dos experimentos 1 e 3 (ver COMPARACAO_LOCAL.md,
COMPARACAO_LOCAL_V3.md): a razão soma_de_menções/n_reviews oscilou entre
2,03 e 3,50 sem relação com o tamanho do bucket, e o tema mais citado
ficou sempre entre 84% e 93% do bucket — as contagens do LLM não rastreiam
nada real, são texto que se parece com número.

Estágio 1 — IDENTIFICAÇÃO de temas (sem números): 1 chamada por bucket.
Estágio 2 — CLASSIFICAÇÃO review a review, em lotes de 10: para cada
review, quais ids de tema ela aborda (pode ser nenhum, pode ser vários).
O CÓDIGO soma as ocorrências — o LLM nunca vê nem escreve
`mencoes_aproximadas`/`n_reviews_analisadas`.

O prompt de PRODUÇÃO (`build_system_prompt`) não é usado nem editado aqui
— os prompts dos dois estágios são NOVOS, escritos neste script,
preservando as mesmas invariantes (papel do bucket, anti-spoiler, pt-BR,
sem aspas). SPEC.md e synthesize.py não são tocados.

Reviews 100% do cache (`Fetcher(offline=True)`) — confirma `n_network=0`
antes de qualquer chamada. ZERO Gemini, ZERO Letterboxd, ZERO TMDB.
think=false em TODAS as chamadas (dos dois estágios).

Robustez (lição dos experimentos 2 e 3): grava por bucket assim que
termina; timeout de 300s por chamada; falha de 1 lote do estágio 2 não
aborta o bucket — registra e segue (as reviews daquele lote ficam sem
classificação, contabilizadas à parte, não silenciosamente como "zero
temas").

NÃO toca em resultado/cure.json nem nos resultados dos experimentos
1, 2 e 3.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from espectro24.fetcher import Fetcher  # noqa: E402
from espectro24.pipeline import run_pipeline  # noqa: E402
from espectro24.synthesize import (  # noqa: E402
    _intervalo_bucket,
    _parse_llm_json,
    _remover_aspas,
    _idioma_e_pt_br,
    ollama_chat_bruto,
)

SLUG = "cure"
MODEL = "qwen3-espectro"
TIMEOUT_S = 300
LOTE_TAMANHO = 10
MAX_TEMAS = 6
OUT_DIR = ROOT / "resultado" / "experimento_local" / "dois_estagios"


def _chamar(system: str, user: str, *, tentativas: int = 2) -> tuple[dict | None, list[dict]]:
    """Chama o Ollama (think=false) e faz o parsing defensivo com 1
    retentativa em JSON inválido — mesma política da produção. Devolve
    (dict_parseado_ou_None, log_de_chamadas)."""
    log = []
    ultimo_erro = None
    for i in range(tentativas):
        t0 = time.time()
        try:
            data = ollama_chat_bruto(system, user, MODEL, think=False,
                                     num_predict=4000, timeout_s=TIMEOUT_S)
        except Exception as e:
            dt = time.time() - t0
            log.append({"tentativa": i + 1, "tempo_s": round(dt, 2),
                       "erro": str(e), "json_valido": False})
            ultimo_erro = e
            continue
        dt = time.time() - t0
        content = (data.get("message") or {}).get("content") or ""
        registro = {
            "tentativa": i + 1, "tempo_s": round(dt, 2),
            "done_reason": data.get("done_reason"),
            "eval_count": data.get("eval_count"),
            "conteudo_chars": len(content),
        }
        try:
            parsed = _parse_llm_json(content)
            registro["json_valido"] = True
            log.append(registro)
            return parsed, log
        except (json.JSONDecodeError, ValueError) as e:
            registro["json_valido"] = False
            registro["erro"] = str(e)
            log.append(registro)
            ultimo_erro = e
    return None, log


# --- Estágio 1 — identificação de temas, sem números ---

def _prompt_estagio1(bucket_nome: str) -> str:
    intervalo = _intervalo_bucket(bucket_nome)
    return f"""\
Você é uma etapa de um pipeline que agrega reviews de usuários de um filme \
do Letterboxd. O pipeline separa as reviews em três faixas de nota ANTES \
desta etapa (negativas, medianas, positivas); você está recebendo \
EXCLUSIVAMENTE a faixa "{bucket_nome}" ({intervalo}) — um recorte enviesado \
POR CONSTRUÇÃO, que NÃO representa a recepção geral do filme.

Sua função NESTA ETAPA é só IDENTIFICAR OS TEMAS que aparecem neste grupo \
de reviews — NÃO conte quantas vezes cada um aparece; isso é feito depois, \
por outro processo, e não deve aparecer na sua resposta.

Consequência explícita: é PROIBIDO generalizar para "os críticos", "a \
maioria", "o consenso" ou "a recepção do filme".

Instruções fixas (invariáveis):
1. Anti-spoiler: descreva os temas em nível temático (ritmo, atuações, \
fotografia, roteiro em termos abstratos). É PROIBIDO mencionar eventos da \
trama, destinos de personagens, reviravoltas ou o final, mesmo que as \
reviews os mencionem.
2. `descricao_curta` é paráfrase, NUNCA citação literal de nenhuma review.
3. Identifique entre 4 e 6 temas DISTINTOS que realmente aparecem neste \
grupo de reviews — não repita o mesmo tema com nomes diferentes, não \
invente tema que não aparece no texto.
4. As reviews podem estar em qualquer idioma; sua saída é SEMPRE em pt-BR.
5. Responda APENAS o JSON, sem preâmbulo, sem cercas de código.
6. É PROIBIDO usar aspas (simples, duplas ou angulares) dentro de \
`descricao_curta`.
7. TODOS os campos de texto da saída devem estar em pt-BR, incluindo os \
NOMES DOS TEMAS.

Formato de saída (JSON puro):
{{
  "temas": [
    {{"id": "t1", "tema": "<curto>", "descricao_curta": "<paráfrase>"}}
  ]
}}"""


def _build_user_message_reviews(reviews) -> str:
    linhas = ["Reviews (nota em estrelas + texto completo):"]
    for i, r in enumerate(reviews, 1):
        linhas.append(f"[{i}] nota={r.rating} estrelas:")
        linhas.append(r.effective_text)
        linhas.append("")
    return "\n".join(linhas)


# --- Estágio 2 — classificação review a review, em lotes ---

def _prompt_estagio2(temas: list[dict]) -> str:
    linhas_temas = "\n".join(
        f'- {t["id"]}: {t["tema"]} — {t["descricao_curta"]}' for t in temas)
    return f"""\
Você está classificando reviews de um filme quanto aos temas abaixo. Cada \
review está numerada. Para CADA review, decida quais temas (pelo id) ela \
REALMENTE aborda.

Temas:
{linhas_temas}

Uma review pode não abordar NENHUM tema da lista — isso é ESPERADO e \
COMUM, é uma resposta válida. Uma review também pode abordar vários temas \
ao mesmo tempo. Marque um id SOMENTE quando a review realmente fala sobre \
aquele assunto — não marque por proximidade genérica nem para preencher a \
lista.

Responda APENAS um JSON no formato abaixo (chave = número da review, \
valor = lista de ids de tema que ela aborda; lista vazia se nenhum), sem \
preâmbulo, sem cercas de código, sem texto fora do JSON:
{{"1": ["t1", "t3"], "2": [], "3": ["t2"]}}"""


def _lotes(reviews, tamanho):
    for i in range(0, len(reviews), tamanho):
        yield i, reviews[i:i + tamanho]


def _rodar_estagio2(reviews, temas: list[dict]):
    """Devolve (contagem_por_id, review_index -> [ids], reviews_sem_tema,
    ids_invalidos_total, log_de_lotes)."""
    ids_validos = {t["id"] for t in temas}
    contagem = {t["id"]: 0 for t in temas}
    atribuicoes: dict[int, list[str]] = {}
    ids_invalidos_total = 0
    log_lotes = []
    system = _prompt_estagio2(temas)

    for offset, lote in _lotes(reviews, LOTE_TAMANHO):
        user = _build_user_message_reviews(lote)
        parsed, log = _chamar(system, user)
        registro_lote = {
            "offset": offset, "tamanho": len(lote), "chamadas": log,
            "ok": parsed is not None,
        }
        if parsed is None:
            # falha do lote inteiro: reviews ficam SEM classificação —
            # contabilizadas à parte, não como "zero temas" genuíno.
            for i in range(len(lote)):
                atribuicoes[offset + i] = None   # None = não classificado (falha)
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
        # reviews do lote sem chave na resposta -> sem tema (resposta implícita)
        for i in range(len(lote)):
            atribuicoes.setdefault(offset + i, [])
        registro_lote["ids_invalidos"] = invalidos_neste_lote
        ids_invalidos_total += invalidos_neste_lote
        log_lotes.append(registro_lote)

    return contagem, atribuicoes, ids_invalidos_total, log_lotes


def _processar_bucket(bucket):
    reviews = bucket.reviews_analisadas
    n_reviews = len(reviews)

    print(f"  [estágio 1] {bucket.nome}: identificando temas...", file=sys.stderr)
    t0 = time.time()
    system1 = _prompt_estagio1(bucket.nome)
    user1 = _build_user_message_reviews(reviews)
    parsed1, log1 = _chamar(system1, user1)
    tempo_estagio1 = time.time() - t0

    if parsed1 is None or not isinstance(parsed1.get("temas"), list):
        return {
            "bucket": bucket.nome, "n_reviews": n_reviews, "falhou": True,
            "erro": "estágio 1 não produziu JSON válido de temas",
            "estagio1_log": log1, "tempo_estagio1_s": round(tempo_estagio1, 2),
        }

    temas_brutos = parsed1["temas"][:MAX_TEMAS]
    temas = []
    for i, t in enumerate(temas_brutos, 1):
        tid = str(t.get("id") or f"t{i}")
        tema_nome = str(t.get("tema", "")).strip()
        descricao, aspas_removidas = _remover_aspas(str(t.get("descricao_curta", "")))
        if not tema_nome:
            continue
        temas.append({"id": tid, "tema": tema_nome, "descricao_curta": descricao,
                      "aspas_removidas_da_descricao": aspas_removidas})
    print(f"    {len(temas)} tema(s) propostos em {tempo_estagio1:.1f}s: "
          f"{[t['tema'] for t in temas]}", file=sys.stderr)

    print(f"  [estágio 2] {bucket.nome}: classificando {n_reviews} reviews "
          f"em lotes de {LOTE_TAMANHO}...", file=sys.stderr)
    t0 = time.time()
    contagem, atribuicoes, ids_invalidos, log_lotes = _rodar_estagio2(reviews, temas)
    tempo_estagio2 = time.time() - t0
    print(f"    estágio 2 concluído em {tempo_estagio2:.1f}s "
          f"({len(log_lotes)} lote(s))", file=sys.stderr)

    # monta o objeto final no MESMO formato do pipeline de produção
    temas_finais = []
    for t in temas:
        temas_finais.append({
            "tema": t["tema"],
            "mencoes_aproximadas": contagem.get(t["id"], 0),
            "n_reviews_analisadas": n_reviews,
            "exemplo_parafraseado": t["descricao_curta"],
            "id_estagio1": t["id"],
        })
    temas_finais.sort(key=lambda t: t["mencoes_aproximadas"], reverse=True)
    temas_finais = temas_finais[:MAX_TEMAS]

    n_sem_tema = sum(1 for v in atribuicoes.values() if v == [])
    n_nao_classificadas = sum(1 for v in atribuicoes.values() if v is None)
    n_com_tema = n_reviews - n_sem_tema - n_nao_classificadas
    total_atribuicoes = sum(len(v) for v in atribuicoes.values() if v)
    media_temas_por_review = (total_atribuicoes / (n_reviews - n_nao_classificadas)
                              if (n_reviews - n_nao_classificadas) > 0 else 0)

    idioma_ok = all(_idioma_e_pt_br(t["tema"]) and _idioma_e_pt_br(t["exemplo_parafraseado"])
                    for t in temas_finais)

    # amostra para conferência humana: guarda TODAS as atribuições com o
    # texto da review, para o relatório escolher exemplos depois.
    amostra_completa = []
    for i, r in enumerate(reviews):
        amostra_completa.append({
            "indice": i, "rating": r.rating, "texto": r.effective_text,
            "temas_atribuidos": atribuicoes.get(i),
        })

    return {
        "bucket": bucket.nome, "n_reviews": n_reviews, "falhou": False,
        "tempo_estagio1_s": round(tempo_estagio1, 2),
        "tempo_estagio2_s": round(tempo_estagio2, 2),
        "tempo_total_s": round(tempo_estagio1 + tempo_estagio2, 2),
        "estagio1_log": log1,
        "estagio1_temas_propostos": temas,
        "estagio2_lotes": log_lotes,
        "estagio2_ids_invalidos_total": ids_invalidos,
        "n_reviews_sem_tema": n_sem_tema,
        "n_reviews_nao_classificadas_falha_lote": n_nao_classificadas,
        "n_reviews_com_tema": n_com_tema,
        "media_temas_por_review_classificada": round(media_temas_por_review, 3),
        "idioma_pt_br_ok": idioma_ok,
        "temas_finais": temas_finais,
        "amostra_completa": amostra_completa,
    }


def main() -> int:
    print(f"Carregando reviews de '{SLUG}' do cache (offline, zero rede)...",
          file=sys.stderr)
    fetcher = Fetcher(cache_dir=str(ROOT / "resultado" / "cache"), offline=True)
    buckets, _niveis, _distrib = run_pipeline(
        fetcher, SLUG, datetime.now(timezone.utc).isoformat(),
        synth=False, distribuicao=False,
    )
    if fetcher.n_network != 0:
        print(f"ABORTANDO: {fetcher.n_network} requisição(ões) de rede — "
              f"esperado 0.", file=sys.stderr)
        return 1
    print(f"OK: {len(buckets)} buckets, 0 requisições de rede.", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    resumo = {"gerado_em": datetime.now(timezone.utc).isoformat(), "buckets": []}

    for b in buckets:
        print(f"\n=== bucket '{b.nome}' ({len(b.reviews_analisadas)} reviews) ===",
              file=sys.stderr)
        resultado = _processar_bucket(b)
        out_path = OUT_DIR / f"{b.nome}.json"
        out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print(f"  gravado em {out_path} (falhou={resultado['falhou']})",
              file=sys.stderr)
        resumo["buckets"].append({
            "bucket": b.nome, "falhou": resultado["falhou"],
            "tempo_total_s": resultado.get("tempo_total_s"),
        })

    resumo_path = OUT_DIR / "resumo.json"
    resumo_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"\nResumo gravado em {resumo_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
