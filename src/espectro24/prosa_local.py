"""Prosa em modelo LOCAL (Ollama) — exceção escopada, 2026-10-12.

**Por que existe.** Os créditos de DeepSeek e Gemini acabaram. O caro do
pipeline é a PROSA (síntese, narrativa, veredito, condições: ~US$ 0,09 por
filme em Gemini), não a classificação. Se um modelo local escrever prosa
aceitável, os filmes do lote C22 — já classificados — poderiam ser
publicados sem gastar nada. Este módulo roda os cinco estágios de prosa com o
provider `local` para UM filme já publicado, em um diretório de saída, para
uma comparação cega com o texto publicado. **Não publica nada.**

**Escopo, travado por código e por teste.**
- `config.PROVIDER_POR_ESTAGIO` NÃO é tocado: o provider entra por injeção,
  o caminho que os estágios sempre aceitaram — `client_call` na síntese e na
  rotulagem, `gerar=` na narrativa, no veredito e nas condições.
- Só roda para slug JÁ publicado em `resultado/` e FORA da exceção C22
  (`excecao_c22.SLUGS`): nada do lote C22 é publicado por aqui.
- A saída nunca pode ficar dentro de `resultado/`.
- Os validadores de sempre rodam, porque são o código dos estágios — este
  módulo só troca quem responde ao prompt.

**O que cada registro leva:** `provider`, `modelo`, `modelo_efetivo`,
`think` (o nível de raciocínio), os tempos (leitura do prompt × geração) e
`finish_reason`, por chamada (`ChamadasLocais.registros`) e resumidos por
estágio em `proveniencia_llm` do documento regenerado.

**Reprodução da seleção.** A síntese relê as MESMAS reviews que a publicada
(`selecionar` sobre o bruto persistido, com o histograma e o orçamento de
páginas gravados no próprio `coleta` do JSON — o caminho de
`pipeline.amostra_do_bruto`). Tudo que não é texto de LLM (ficha,
distribuição, coleta, a telemetria de seleção dos buckets, a classificação
do consenso) vem do publicado; `selecao_reproduz_publicada` registra se a
seleção refeita bate com a publicada.
"""
from __future__ import annotations

import copy
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from . import local_ollama
from .config import COTA_POR_BUCKET, DADOS_BRUTO_DIR
from .local_ollama import LLMLocalFalhou, resposta_json_local

RAIZ = Path(__file__).resolve().parents[2]
RESULTADO_DIR = RAIZ / "resultado"
EXCECAO = "LOCAL_PROSA"
PROVIDER = "local"
ESTAGIOS = ("sintese", "rotulagem", "narrativa", "veredito", "condicoes")

# Janela e tetos próprios da prosa. A janela é UMA para os cinco estágios (mudar
# `num_ctx` recarrega o modelo no Ollama). O teto de saída inclui os tokens de
# RACIOCÍNIO (gpt-oss, `think` != false): a nuvem usa 3.000 (síntese) e 16.000
# (prosa) sem raciocínio contado; aqui há folga para o pensamento. A janela
# cobre prompt + saída: a maior síntese medida nos 5 filmes da comparação é
# ~23.000 caracteres (~7.000 tokens) + 2.200 do system + 6.000 de saída.
NUM_CTX_PROSA = 24576
NUM_PREDICT_ESTRUTURADO = 6000   # síntese, rotulagem
NUM_PREDICT_PROSA = 12000        # narrativa, veredito, condições
# Prazo por chamada: a síntese lê até ~40 reviews (milhares de tokens) e
# gera na CPU a ~10-15 tokens/s. 1.800 s é ~5x o pior caso estimado.
PRAZO_PROSA_PADRAO_S = 1800.0

_CHAVES_SINTESE = ("temas", "observacao_geral", "idioma_invalido", "escopo_suspeito")


def _inteiro_env(nome: str, padrao: int) -> int:
    return int(os.environ.get(nome) or padrao)


def prazo_prosa_s() -> float:
    return float(os.environ.get("ESPECTRO24_OLLAMA_PRAZO_PROSA_S")
                 or PRAZO_PROSA_PADRAO_S)


class ChamadasLocais:
    """Um chamador por estágio, que guarda TODA chamada.

    É os dois adaptadores de uma vez: `__call__(system, user, model=None) ->
    str` (o `client_call` da síntese e da rotulagem) e `gerar(system, user) ->
    (texto, uso, latencia_s)` (o `gerar=` da narrativa, do veredito e das
    condições; `extrair` aplica o extrator do estágio ao texto bruto, como o
    `_gerar_real` de cada um faz)."""

    def __init__(self, estagio: str, modelo: str, extrair=None):
        if estagio not in ESTAGIOS:
            raise ValueError(f"estágio {estagio!r} desconhecido: {ESTAGIOS}")
        self.estagio, self.modelo, self.extrair = estagio, modelo, extrair
        self.registros: list[dict] = []

    def _chamar(self, system: str, user: str) -> dict:
        estruturado = self.estagio in ("sintese", "rotulagem")
        base = {"estagio": self.estagio, "unidade": user.split("\n", 1)[0][:80],
                "provider": PROVIDER, "modelo": self.modelo,
                "think": local_ollama.nivel_think(),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        try:
            resp = resposta_json_local(
                system, user, estagio=self.estagio, modelo=self.modelo,
                schema="json", prazo=prazo_prosa_s(),
                num_predict=_inteiro_env(
                    "ESPECTRO24_OLLAMA_NUM_PREDICT_PROSA",
                    NUM_PREDICT_ESTRUTURADO if estruturado else NUM_PREDICT_PROSA),
                num_ctx=_inteiro_env("ESPECTRO24_OLLAMA_NUM_CTX_PROSA",
                                     NUM_CTX_PROSA))
        except LLMLocalFalhou as e:
            self.registros.append({**base, "ok": False, "erro": str(e),
                                   "latencia_s": e.latencia_s})
            raise
        self.registros.append({**base, "ok": True, **{
            k: resp[k] for k in (
                "modelo_efetivo", "finish_reason", "latencia_s", "leitura_prompt_s",
                "geracao_s", "carga_s", "total_s", "prompt_eval_count",
                "eval_count", "custo_usd", "think")}})
        return resp

    def __call__(self, system: str, user: str, model: str | None = None) -> str:
        return self._chamar(system, user)["texto"]

    def gerar(self, system: str, user: str):
        resp = self._chamar(system, user)
        n_in, n_out = resp["uso"]["prompt_tokens"], resp["uso"]["completion_tokens"]
        uso = {"prompt_tokens": n_in, "completion_tokens": n_out,
               "cache_hit_tokens": 0, "cache_miss_tokens": n_in}
        texto = resp["texto"]
        return (self.extrair(texto) if self.extrair else texto), uso, resp["latencia_s"]

    def resumo(self) -> dict:
        from collections import Counter

        ok = [r for r in self.registros if r["ok"]]
        return {"estagio": self.estagio, "provider": PROVIDER, "modelo": self.modelo,
                "think": local_ollama.nivel_think(),
                "modelos_efetivos": sorted({str(r.get("modelo_efetivo")) for r in ok}),
                "n_chamadas": len(self.registros),
                "n_falhas": len(self.registros) - len(ok),
                "finish_reason": dict(Counter(str(r.get("finish_reason")) for r in ok)),
                "custo_usd": 0.0,
                "tempo_s": {"parede": round(sum(r.get("latencia_s") or 0
                                                for r in self.registros), 1),
                            "leitura_prompt": round(sum(r.get("leitura_prompt_s") or 0
                                                        for r in ok), 1),
                            "geracao": round(sum(r.get("geracao_s") or 0
                                                 for r in ok), 1)},
                "chamadas": self.registros}


# ---------------------------------------------------------------------------
# Guardas de escopo
# ---------------------------------------------------------------------------

class ForaDoEscopo(RuntimeError):
    pass


def exigir_escopo(slug: str, saida: Path, resultado_dir: Path = RESULTADO_DIR) -> None:
    """Recusa o que a exceção não cobre: slug do lote C22, filme não publicado,
    saída dentro de `resultado/`."""
    from .excecao_c22 import SLUGS as C22

    if slug in C22:
        raise ForaDoEscopo(f"{slug!r} é do lote C22: nada dele é publicado "
                           f"nem regenerado por esta exceção")
    if not (resultado_dir / f"{slug}.json").exists():
        raise ForaDoEscopo(f"{slug!r} não está publicado em {resultado_dir} — "
                           f"a exceção compara contra o publicado")
    alvo, proibido = Path(saida).resolve(), Path(resultado_dir).resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise ForaDoEscopo(f"saída {alvo} fica dentro de {proibido}: esta "
                           f"exceção nunca escreve em resultado/")


# ---------------------------------------------------------------------------
# Regeneração de um filme
# ---------------------------------------------------------------------------

def _buckets_do_bruto(slug: str, coleta: dict, bruto_dir):
    from .bruto import carregar
    from .pipeline import montar_buckets
    from .recusas import ids_recusados
    from .selecao import selecionar

    _, todas = carregar(slug, raiz=bruto_dir)
    hist = {float(k): v for k, v in (coleta.get("histograma_bruto") or {}).items()}
    orc = {float(k): v
           for k, v in (coleta.get("orcamento_paginas_por_nivel") or {}).items()}
    sel = selecionar(todas, hist or None, cota_por_bucket=COTA_POR_BUCKET,
                     orcamento_paginas_por_nivel=orc,
                     excluir_ids=ids_recusados(slug))
    return montar_buckets(sel, None)


def regenerar_filme(slug: str, *, modelo: str, saida: Path, n: int | None = None,
                    aberturas: dict | None = None,
                    resultado_dir: Path = RESULTADO_DIR,
                    bruto_dir=DADOS_BRUTO_DIR, estagios=ESTAGIOS) -> dict:
    """Regenera os estágios de prosa de UM filme publicado com o modelo local e
    grava `<saida>/<slug>.json` (+ `<slug>.telemetria.json`). Devolve a
    telemetria. Falha de um estágio é registrada e não derruba os outros."""
    from . import briefing as br
    from . import condicoes as C
    from . import veredito as V
    from .config import BEST_OF_N
    from .narrador import narrar, telemetria_para_json
    from .pipeline import ids_analisados_do_bruto, montar_eixos
    from .render import build_output
    from .synthesize import synthesize_bucket

    saida = Path(saida)
    exigir_escopo(slug, saida, resultado_dir)
    n = n or BEST_OF_N
    pub = json.loads((resultado_dir / f"{slug}.json").read_text(encoding="utf-8"))
    t0 = time.time()
    tele: dict = {"slug": slug, "excecao": EXCECAO, "provider": PROVIDER,
                  "modelo": modelo, "think": local_ollama.nivel_think(),
                  "n_best_of": n, "falhas": {}}

    c = {e: ChamadasLocais(e, modelo) for e in ESTAGIOS}
    c["narrativa"].extrair = br.extrair_narrativa
    c["veredito"].extrair = V.extrair_veredito

    # --- síntese: as mesmas reviews do publicado ---
    buckets = _buckets_do_bruto(slug, pub["coleta"], bruto_dir)
    sel_pub = {b["bucket"]: b for b in pub["buckets"]}
    tele["selecao_reproduz_publicada"] = all(
        sel_pub[b.nome]["n_validas"] == b.n_validas
        and sel_pub[b.nome]["composicao_atingida"] == {
            str(k): v for k, v in b.composicao_atingida.items()}
        for b in buckets)
    for b in buckets:
        try:
            synthesize_bucket(b, client_call=c["sintese"], model=modelo)
        except Exception as e:  # noqa: BLE001
            tele["falhas"][f"sintese/{b.nome}"] = f"{type(e).__name__}: {e}"

    out = build_output(slug, buckets, data_coleta=pub["data_coleta"],
                       origens=pub["origem_paginas"],
                       total_observado=pub["total_reviews_observadas"],
                       ficha=pub["ficha"], distribuicao=None, coleta=pub["coleta"])
    out["distribuicao"] = pub["distribuicao"]
    # tudo que não é texto de LLM vem do publicado (a telemetria de seleção
    # dos buckets inclusive: a coleta de páginas não se refaz offline)
    por_nome = {b["bucket"]: b for b in out["buckets"]}
    for nome, bp in sel_pub.items():
        novo = por_nome[nome]
        for k, v in bp.items():
            if k not in _CHAVES_SINTESE:
                novo[k] = copy.deepcopy(v)

    # --- rotulagem + schema de eixos ---
    if "rotulagem" in estagios:
        try:
            analisadas = ids_analisados_do_bruto(slug, coleta=pub["coleta"],
                                                 raiz=bruto_dir)
            bloco = montar_eixos(slug, out, analisadas, client_call=c["rotulagem"],
                                 model=modelo)
            if bloco is None:
                tele["falhas"]["rotulagem"] = "sem bloco de eixos"
            else:
                out["eixos"] = bloco
        except Exception as e:  # noqa: BLE001
            tele["falhas"]["rotulagem"] = f"{type(e).__name__}: {e}"

    # --- narrativa ---
    if "narrativa" in estagios:
        try:
            res = narrar(out, n=n, provider=PROVIDER, model=modelo,
                         gerar=c["narrativa"].gerar)
            out["narrativa"] = res.texto
            out["verificacao_narrativa"] = res.verificacao
            out["narrativa_selecao"] = telemetria_para_json(res)
            if res.falhou:
                tele["falhas"]["narrativa"] = "nenhuma amostra com texto"
        except Exception as e:  # noqa: BLE001
            tele["falhas"]["narrativa"] = f"{type(e).__name__}: {e}"

    # --- veredito ---
    if "veredito" in estagios:
        try:
            bloco = V.gerar(out, n=n, provider=PROVIDER, model=modelo,
                            gerar=c["veredito"].gerar, aberturas=aberturas)
            if bloco is None:
                tele["falhas"]["veredito"] = "sem bloco de eixos"
            else:
                out["veredito"] = bloco
        except Exception as e:  # noqa: BLE001
            tele["falhas"]["veredito"] = f"{type(e).__name__}: {e}"

    # --- condições ---
    if "condicoes" in estagios:
        try:
            bloco = C.gerar(out, n=n, provider=PROVIDER, model=modelo,
                            gerar=c["condicoes"].gerar)
            if bloco is None:
                tele["falhas"]["condicoes"] = "sem bloco de eixos"
            else:
                out["condicoes"] = bloco
        except Exception as e:  # noqa: BLE001
            tele["falhas"]["condicoes"] = f"{type(e).__name__}: {e}"

    tele["estagios"] = {e: c[e].resumo() for e in ESTAGIOS}
    tele["elapsed_s"] = round(time.time() - t0, 1)
    out["proveniencia_llm"] = {"excecao": EXCECAO, "provider": PROVIDER,
                               "modelo": modelo, "think": tele["think"],
                               "estagios": {e: {k: v for k, v in r.items()
                                                if k != "chamadas"}
                                            for e, r in tele["estagios"].items()},
                               "falhas": tele["falhas"]}
    saida.mkdir(parents=True, exist_ok=True)
    (saida / f"{slug}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (saida / f"{slug}.telemetria.json").write_text(
        json.dumps(tele, ensure_ascii=False, indent=2), encoding="utf-8")
    return tele
