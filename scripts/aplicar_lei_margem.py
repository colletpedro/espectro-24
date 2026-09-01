#!/usr/bin/env python3
"""[v1.9.34, §2.5] Aplica a LEI POR `n` aos `resultado/*.json` publicados.

**Isto NÃO é republicar o filme.** Nenhum estágio a montante roda: sem coleta,
sem seleção, sem síntese, sem [D3]/rotulagem, sem narrativa, sem TMDB, sem
histograma. Confirmado no código, não por dedução:

  - `rotular_output` (a rotulagem [D3], o único LLM do bloco `eixos`) só é
    alcançável por `pipeline.montar_eixos` — este harness chama
    `eixos.montar_bloco` DIRETO, que recebe `temas_por_eixo` como dict puro;
  - os temas vêm remontados do PRÓPRIO JSON publicado (campos `tema`,
    `exemplo_parafraseado`, `temas_no_mesmo_eixo` de cada célula), então
    nenhuma frase é reescrita — elas viajam idênticas;
  - `synthesize` só é alcançável por `cli.py`;
  - `veredito.gerar` → `montar_briefing` (código puro sobre o JSON) → LLM.
    É a ÚNICA chamada de LLM deste harness.

**O que ele escreve, e nada mais:** `eixos` (sempre — o bloco ganha `margem` e
`acima_da_margem` por célula) e `veredito` (só onde o BRIEFING mudou; e
REMOVIDO quando o filme fica sem estado de contraste).

**O critério de regeneração é o BRIEFING, não o estado.** Um filme cujo
`contraste` não mudou pode ter mudado o eixo que o veredito NOMEIA (o de maior
lift acima da margem), porque a margem mudou. Regenerar por "mudou de estado"
deixaria texto publicado descrevendo um briefing que não existe mais.

Uso:
    python scripts/aplicar_lei_margem.py --dry-run      # zero LLM, zero escrita
    python scripts/aplicar_lei_margem.py --aplicar
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import eixos as E  # noqa: E402
from espectro24 import veredito as V  # noqa: E402
from espectro24.pipeline import amostra_do_bruto  # noqa: E402
from espectro24.taxonomia import LIVRE  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
RAIZ_BRUTO = RAIZ / "dados" / "bruto"

# As DUAS únicas chaves que este harness escreve. Conferidas campo a campo
# contra o documento antes de gravar (mesma trava de `gerar_veredito.py`).
CHAVES = ("eixos", "veredito")

# A margem que vigorava ANTES desta versão, usada só para RECONSTRUIR o
# briefing que gerou o texto publicado — nunca para decidir nada novo.
MARGEM_ANTIGA_PP = 20


def _slugs() -> list[str]:
    return sorted(p.stem for p in RESULTADO_DIR.glob("*.json")
                  if json.loads(p.read_text(encoding="utf-8")).get("eixos"))


def _temas_do_publicado(bloco: dict) -> dict:
    """`{bucket: {eixo: {tema, exemplo_parafraseado, temas_no_mesmo_eixo}}}`
    remontado do bloco JÁ PUBLICADO. É isto que garante zero LLM: as frases de
    §[D3] não são reescritas, são relidas."""
    fora: dict[str, dict[str, dict]] = {}
    for linha in bloco.get("linhas") or []:
        for bucket, cel in (linha.get("por_bucket") or {}).items():
            if cel.get("tema") is None and not cel.get("temas_no_mesmo_eixo"):
                continue
            fora.setdefault(bucket, {})[linha["eixo"]] = {
                "tema": cel.get("tema"),
                "exemplo_parafraseado": cel.get("exemplo_parafraseado"),
                "temas_no_mesmo_eixo": list(cel.get("temas_no_mesmo_eixo") or []),
            }
    return fora


def _briefing_antigo(doc: dict) -> dict | None:
    """O briefing que produziu o texto PUBLICADO.

    O bloco publicado não tem `acima_da_margem` (é o campo que a v1.9.34
    introduz), e `veredito._maior_lift` agora exige o campo. Para reconstruir
    o briefing de ANTES sem reintroduzir a comparação em float no código de
    produção, injetamos aqui — e só aqui, sobre uma CÓPIA — a decisão sob a
    regra antiga: `lift_pp >= 20`. É exatamente o que o código fazia até a
    v1.9.33, reproduzido no lugar certo: uma ferramenta de auditoria.
    """
    d = copy.deepcopy(doc)
    for linha in (d.get("eixos") or {}).get("linhas") or []:
        for cel in (linha.get("por_bucket") or {}).values():
            lp = cel.get("lift_pp")
            cel["acima_da_margem"] = (isinstance(lp, (int, float))
                                      and lp >= MARGEM_ANTIGA_PP)
    return V.montar_briefing(d)


def _bloco_novo(slug: str, doc: dict) -> dict:
    """O bloco `eixos` sob a lei — determinístico, zero LLM, zero rede."""
    catalogo, _meta = _consenso()
    coleta = doc.get("coleta")
    prod = amostra_do_bruto(slug, coleta=coleta, raiz=str(RAIZ_BRUTO))
    analisadas = {b: {r.id for r in rs} for b, rs in prod.items()}
    bloco = E.montar_bloco(catalogo[slug], analisadas,
                           _temas_do_publicado(doc["eixos"]))
    # Carimbos que `pipeline.montar_eixos` põe e `montar_bloco` não: eles
    # descrevem a EXECUÇÃO, não o cálculo. Preservamos os do artefato — a
    # rotulagem é a MESMA (as frases vieram dele), e o verificador também.
    for chave in ("rotulagem", "verificador"):
        if chave in doc["eixos"]:
            bloco[chave] = doc["eixos"][chave]
    bloco["spec_version"] = "1.9.34"
    return bloco


_CACHE_CONSENSO: tuple | None = None


def _consenso():
    """`consenso_verificado.jsonl` — o consenso DEPOIS do passe de
    `impacto_emocional`, que é o de produção. Explícito porque a instabilidade
    de classificação (5 filmes trocam de estado conforme o verificador tenha
    rodado ou não) é uma fonte SEPARADA desta versão, e misturar as duas
    tornaria o diff desta republicação ilegível."""
    global _CACHE_CONSENSO
    if _CACHE_CONSENSO is None:
        caminho = RAIZ / E.CONSENSO_VERIFICADO
        _CACHE_CONSENSO = (E.carregar_classificacao(caminho), caminho.name)
    return _CACHE_CONSENSO


def _resumo_briefing(b: dict | None) -> dict | None:
    """Só o que DECIDE o texto — telemetria e números de exibição ficam fora,
    senão qualquer arredondamento marcaria o filme para regeneração."""
    if b is None:
        return None
    def g(nome):
        x = (b.get("grupos") or {}).get(nome) or {}
        lift = x.get("eixo_maior_lift") or {}
        freq = x.get("eixo_maior_frequencia") or {}
        return {
            "lift_eixo": lift.get("eixo") if lift.get("acima_da_margem") else None,
            "freq_eixo": freq.get("eixo"),
            "rotulo": freq.get("rotulo_quantificador"),
            "modo": x.get("modo"), "estado_piso": x.get("estado_piso"),
        }
    a = b.get("assunto_compartilhado") or {}
    # os temas do assunto compartilhado ENTRAM: o texto `valorativo` os cita,
    # então mudar o tema de um lado muda o que a página afirma.
    return {
        "contraste": b.get("contraste"),
        "assunto_compartilhado": [a.get("eixo"), a.get("tema_negativas"),
                                  a.get("tema_positivas"),
                                  a.get("rotulo_quantificador_negativas"),
                                  a.get("rotulo_quantificador_positivas")],
        "bucket_dominante": (b.get("bucket_dominante") or {}).get("bucket"),
        "grupos": {n: g(n) for n in sorted(b.get("grupos") or {})},
    }


def planejar() -> list[dict]:
    """O plano, sem escrever nada e sem uma chamada de LLM."""
    plano = []
    for slug in _slugs():
        doc = json.loads((RESULTADO_DIR / f"{slug}.json").read_text(
            encoding="utf-8"))
        antes_bloco = doc["eixos"]
        b_antes = _resumo_briefing(_briefing_antigo(doc))

        novo = _bloco_novo(slug, doc)
        d2 = copy.deepcopy(doc)
        d2["eixos"] = novo
        b_depois = _resumo_briefing(V.montar_briefing(d2))

        estado_antes = antes_bloco.get("contraste")
        estado_depois = novo.get("contraste")
        plano.append({
            "slug": slug,
            "estado_antes": estado_antes,
            "estado_depois": estado_depois,
            "estado_mudou": estado_antes != estado_depois,
            "n": novo["margem"]["n"],
            "limiar_pp": novo["margem"]["limiar_pp"],
            "briefing_mudou": b_antes != b_depois,
            "regerar_veredito": b_depois is not None and b_antes != b_depois,
            "remover_veredito": b_depois is None and "veredito" in doc,
            "briefing_antes": b_antes,
            "briefing_depois": b_depois,
        })
    return plano


def _custo_medido(plano) -> dict:
    """Custo em TOKENS, medido — não estimado.

    · entrada: o prompt REAL que cada filme mandaria, serializado agora e
      contado (system + user), sem chamar LLM nenhum;
    · saída: os `completion_tokens` que ESTE MESMO estágio gastou nos 35
      filmes publicados (`veredito.uso`), que é histórico medido do estágio,
      não projeção.
    """
    from espectro24.config import BEST_OF_N
    alvos = [p for p in plano if p["regerar_veredito"]]
    n_chars_prompt = 0
    for p in alvos:
        doc = json.loads((RESULTADO_DIR / f"{p['slug']}.json").read_text(
            encoding="utf-8"))
        doc["eixos"] = _bloco_novo(p["slug"], doc)
        b = V.montar_briefing(doc)
        n_chars_prompt += len(V.PROMPT_VEREDITO) + len(V.serializar_briefing(b))

    usos, chamadas = [], []
    for slug in _slugs():
        v = json.loads((RESULTADO_DIR / f"{slug}.json").read_text(
            encoding="utf-8")).get("veredito") or {}
        if v.get("uso"):
            usos.append(v["uso"])
            chamadas.append(v.get("n_chamadas") or BEST_OF_N)
    n = len(usos) or 1
    prompt_medio = sum(u.get("prompt_tokens", 0) for u in usos) / n
    compl_medio = sum(u.get("completion_tokens", 0) for u in usos) / n
    chamadas_medio = sum(chamadas) / (len(chamadas) or 1)
    return {
        "filmes_a_regerar": len(alvos),
        "chars_de_prompt_reais": n_chars_prompt,
        "historico_do_estagio_n_filmes": len(usos),
        "prompt_tokens_medio_por_filme": round(prompt_medio),
        "completion_tokens_medio_por_filme": round(compl_medio),
        "chamadas_medias_por_filme": round(chamadas_medio, 2),
        "projecao_prompt_tokens": round(prompt_medio * len(alvos)),
        "projecao_completion_tokens": round(compl_medio * len(alvos)),
        "projecao_chamadas": round(chamadas_medio * len(alvos)),
        "modelo": next((json.loads((RESULTADO_DIR / f"{s}.json").read_text(
            encoding="utf-8")).get("veredito", {}).get("modelo")
            for s in _slugs()), None),
    }


def aplicar(plano, *, modelo=None, provider=None) -> list[dict]:
    """NÃO carrega `.env` — quem carrega é `main()`.

    A primeira versão chamava `load_dotenv` aqui, e isso POLUIU a suíte: as
    chaves de API entravam no ambiente do processo e três testes de
    `test_provider.py` (auto-detecção de provider por chave presente)
    passavam isolados e falhavam no conjunto. Uma função de biblioteca não
    muda o ambiente de quem a chama; a fronteira do efeito colateral é o
    `main`.
    """
    import gerar_veredito as GV  # noqa: F401  (só para o snapshot de aberturas)

    telemetria = []
    snapshot = GV.snapshot_de_aberturas()
    for p in plano:
        slug = p["slug"]
        origem = RESULTADO_DIR / f"{slug}.json"
        doc = json.loads(origem.read_text(encoding="utf-8"))
        antes = {k: v for k, v in doc.items() if k not in CHAVES}

        doc["eixos"] = _bloco_novo(slug, doc)
        t0 = time.time()
        if p["remover_veredito"]:
            doc.pop("veredito", None)
            info = {"slug": slug, "acao": "veredito_removido"}
        elif p["regerar_veredito"]:
            bloco = V.gerar(doc, model=modelo, provider=provider,
                            aberturas=GV.historico_para(snapshot, slug))
            if bloco is None:
                raise SystemExit(f"ABORTADO em {slug}: briefing devolveu None "
                                 "onde o plano esperava veredito.")
            doc["veredito"] = bloco
            info = {"slug": slug, "acao": "veredito_regerado",
                    "uso": bloco.get("uso"), "n_chamadas": bloco.get("n_chamadas"),
                    "modelo": bloco.get("modelo"), "flags": bloco.get("flags"),
                    "texto": bloco.get("texto")}
        else:
            info = {"slug": slug, "acao": "so_eixos"}

        depois = {k: v for k, v in doc.items() if k not in CHAVES}
        if depois != antes:
            divergentes = sorted(k for k in set(antes) | set(depois)
                                 if antes.get(k) != depois.get(k))
            raise SystemExit(
                f"ABORTADO em {slug}: campos fora de {CHAVES} mudaram: "
                f"{divergentes}. Nada foi gravado para este filme.")

        origem.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        info["elapsed_s"] = round(time.time() - t0, 1)
        telemetria.append(info)
        print(f"  {slug:52s} {info['acao']}", file=sys.stderr)
    return telemetria


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--modelo")
    ap.add_argument("--provider")
    ap.add_argument("--json", type=Path, help="grava o plano/telemetria")
    args = ap.parse_args()

    if args.aplicar:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env")

    plano = planejar()
    regerar = [p for p in plano if p["regerar_veredito"]]
    remover = [p for p in plano if p["remover_veredito"]]
    mudam = [p for p in plano if p["estado_mudou"]]

    print(f"filmes: {len(plano)}", file=sys.stderr)
    print(f"  estado de contraste MUDA:      {len(mudam)}", file=sys.stderr)
    print(f"  veredito a REGERAR (briefing): {len(regerar)}", file=sys.stderr)
    print(f"  veredito a REMOVER (sem estado): {len(remover)}", file=sys.stderr)
    for p in plano:
        marca = ("REGERA" if p["regerar_veredito"] else
                 "REMOVE" if p["remover_veredito"] else "     .")
        print(f"  {marca} {p['slug']:52s} n={p['n']:2d} "
              f"lim={p['limiar_pp']:5.2f} "
              f"{str(p['estado_antes']):10s} -> {str(p['estado_depois']):10s}"
              + ("  [briefing mudou]" if p["briefing_mudou"] else ""),
              file=sys.stderr)

    saida = {"plano": plano, "custo": _custo_medido(plano)}
    print("\ncusto MEDIDO:", json.dumps(saida["custo"], indent=2,
                                        ensure_ascii=False), file=sys.stderr)

    if args.aplicar:
        saida["telemetria"] = aplicar(plano, modelo=args.modelo,
                                      provider=args.provider)
    elif not args.dry_run:
        raise SystemExit("passe --dry-run ou --aplicar")

    if args.json:
        args.json.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                             encoding="utf-8")


if __name__ == "__main__":
    main()
