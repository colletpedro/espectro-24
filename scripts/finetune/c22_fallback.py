#!/usr/bin/env python3
"""Fallback da guarda de quantidade SÓ nos buckets do C22 que ficaram com `quantidade_pendente`.

Decisão do dono (2026-11-24): as sínteses do C22 (treinado, com guarda, sem fallback) SÃO a saída de
produção; nada é gerado de novo, exceto o fallback nos buckets marcados `quantidade_pendente`. Este script
NÃO refaz a 1ª chamada: lê o `bucket_final` gravado, reconstrói o prompt do bucket a partir da entrada
congelada (conferindo os sha256 do plano) e roda UMA chamada com o reforço (`synthesize.aplicar_fallback_quantidade`,
as mesmas regras de aceite da produção) pelo adaptador de produção (`sintese_local.py`: modelo escolhido pelo
sha do GGUF e488697e…, amostragem do DESVIO_P01, num_ctx pela regra do gate 0).

    listar   (Mac)      conta e lista os buckets pendentes -> finetune/c22/fallback/pendentes.json (sem modelo)
    rodar    (Windows)  uma chamada por bucket pendente    -> finetune/c22/fallback/<slug>__<bucket>.json (retoma)
    regerar  (Windows)  UMA nova geração de um bucket que REPROVOU nos validadores (C4), pela produção
                                                           -> finetune/c22/regeracao/<slug>__<bucket>.json
    aplicar  (Mac)      monta a saída de produção          -> finetune/c22/producao/<slug>__<bucket>.json + manifesto

Nada disso chama API paga. `rodar` fala só com o Ollama local e recusa rodar dentro do Claude Code.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comum as K  # noqa: E402
import c22 as X  # noqa: E402

PASTA = X.PASTA
DIR_FALLBACK = PASTA / "fallback"
DIR_PRODUCAO = PASTA / "producao"
DIR_REGERACAO = PASTA / "regeracao"
ARQ_PENDENTES = DIR_FALLBACK / "pendentes.json"
ARQ_MANIFESTO = DIR_PRODUCAO / "manifesto.json"


def _lista_sintese(dir_sintese: Path) -> list[Path]:
    return sorted(p for p in dir_sintese.glob("*__*.json") if p.name != "manifesto.json")


def pendentes_do_bucket(registro: dict) -> int:
    return sum(1 for t in (registro.get("bucket_final") or {}).get("temas") or [] if t.get("quantidade_pendente"))


def listar_pendentes(dir_sintese: Path) -> dict:
    itens, total = [], 0
    for arq in _lista_sintese(dir_sintese):
        reg = json.loads(arq.read_text(encoding="utf-8"))
        n_temas = len((reg.get("bucket_final") or {}).get("temas") or [])
        total += 1
        n = pendentes_do_bucket(reg) if reg.get("ok") else 0
        if n:
            itens.append({"slug": reg["slug"], "bucket": reg["bucket"], "n_pendentes": n, "n_temas": n_temas,
                          "sintese_sha256": K.sha256_arquivo(arq)})
    return {"buckets_total": total, "buckets_pendentes": len(itens),
            "bullets_pendentes": sum(i["n_pendentes"] for i in itens), "itens": itens}


def cmd_listar(a) -> None:
    out = {"gerado_por": "scripts/finetune/c22_fallback.py listar", **listar_pendentes(X.DIR_SINTESE)}
    DIR_FALLBACK.mkdir(parents=True, exist_ok=True)
    ARQ_PENDENTES.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out['buckets_pendentes']} de {out['buckets_total']} buckets com quantidade_pendente "
          f"({out['bullets_pendentes']} bullets). Gravado: {ARQ_PENDENTES}")
    for i in out["itens"]:
        print(f"  {i['slug']}/{i['bucket']}: {i['n_pendentes']} de {i['n_temas']}")


def _temas_do_registro(registro: dict):
    from espectro24.models import Tema
    return [Tema(**t) for t in registro["bucket_final"]["temas"]]


def rodar_um(registro: dict, entrada: dict, chamar, plano: dict | None = None) -> dict:
    """O fallback de UM bucket. `chamar(system, user) -> str` já embute o modelo. Devolve o registro novo."""
    from espectro24 import synthesize as S
    b = X.bucket_da_entrada(entrada)
    system, user = K.prompt_sintese(b)
    if plano is not None and (K.sha256_texto(system), K.sha256_texto(user)) != (
            plano["system_sha256"], plano["user_sha256"]):
        raise SystemExit(f"{registro['slug']}/{registro['bucket']}: o prompt remontado não é o do plano")
    bf = registro["bucket_final"]
    temas = _temas_do_registro(registro)
    antes = [asdict(t) for t in temas]
    t0 = time.time()
    novos, obs, idioma_ok, escopo_ok, desfecho = S.aplicar_fallback_quantidade(
        chamar, system, user, bf["n_analisadas"], copy.deepcopy(temas), bf["observacao_geral"],
        not bf["idioma_invalido"], not bf["escopo_suspeito"])
    final = dict(bf, temas=[asdict(t) for t in novos], observacao_geral=obs,
                 idioma_invalido=not idioma_ok, escopo_suspeito=not escopo_ok)
    return {"slug": registro["slug"], "bucket": registro["bucket"], "quantidade_fallback": desfecho,
            "pendentes_antes": sum(t.quantidade_pendente for t in temas),
            "pendentes_depois": sum(t.quantidade_pendente for t in novos),
            "n_temas_antes": len(antes), "n_temas_depois": len(final["temas"]),
            "bucket_final_antes": bf, "bucket_final": final,
            "parede_s": round(time.time() - t0, 1)}


def cmd_rodar(a) -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    from espectro24 import sintese_local as SL
    pend = json.loads(ARQ_PENDENTES.read_text(encoding="utf-8"))
    plano = {(p["slug"], p["bucket"]): p for p in K.ler_json(X.ARQ_PLANO)["pares"]}
    DIR_FALLBACK.mkdir(parents=True, exist_ok=True)
    falta = [i for i in pend["itens"] if not (DIR_FALLBACK / f"{i['slug']}__{i['bucket']}.json").exists()]
    print(f"fallback: {len(pend['itens']) - len(falta)} feitos, {len(falta)} a fazer", flush=True)
    SL.resolver_modelo(SL.MODELO_PADRAO)          # recusa cedo se o GGUF e488697e… não estiver no Ollama
    if a.limite:
        falta = falta[:a.limite]
    for n, i in enumerate(falta, 1):
        slug, bucket = i["slug"], i["bucket"]
        arq_sintese = X.DIR_SINTESE / f"{slug}__{bucket}.json"
        if K.sha256_arquivo(arq_sintese) != i["sintese_sha256"]:
            raise SystemExit(f"{slug}/{bucket}: a síntese mudou desde o `listar`")
        reg = json.loads(arq_sintese.read_text(encoding="utf-8"))
        entrada = K.ler_json(X.arq_entrada(slug, bucket))
        n0 = len(SL.REGISTRO)
        try:
            novo = rodar_um(reg, entrada, lambda s, u: SL.client_call_local(s, u, SL.MODELO_PADRAO),
                            plano.get((slug, bucket)))
        except Exception as e:                      # o servidor caiu: nada é gravado, o `rodar` retoma
            raise SystemExit(f"{slug}/{bucket}: falhou ({type(e).__name__}: {str(e)[:300]}). "
                             f"Rode de novo para retomar.") from e
        novo["telemetria"] = SL.REGISTRO[n0:]
        novo["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        (DIR_FALLBACK / f"{slug}__{bucket}.json").write_text(
            json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{n}/{len(falta)}] {slug}/{bucket}: {novo['quantidade_fallback']} · pendentes "
              f"{novo['pendentes_antes']}→{novo['pendentes_depois']} · {novo['parede_s']} s", flush=True)


def validadores_do_bucket(bf: dict, json_parseia: bool = True) -> dict:
    """Os validadores da produção sobre o `bucket_final` (os mesmos do C4)."""
    import reconstruir_sintese as R
    v = R.validar_publicado({**bf, "json_parseia": json_parseia})
    return {"passa_publicado": bool(json_parseia and v["passa_publicado"]),
            "reprovados": [k for k, ok in v["publicado"].items() if ok is False]}


def regerar_um(entrada: dict, slug: str, bucket: str, client_call, model: str = "m") -> dict:
    """UMA nova geração do bucket pela produção (`synthesize_bucket`: parse, retentativa de JSON, validações de
    idioma/escopo, guarda de quantidade e fallback). A chamada leva o reforço `_REFORCO_VALIDACAO` no system:
    com a MESMA semente e o MESMO prompt o Ollama reproduziria a saída reprovada (ESTIMADO), então a nova geração
    usa o prompt de retentativa da produção. PASSA = validadores + guarda (nenhum `quantidade_pendente` sobrando)."""
    from espectro24 import synthesize as S
    b = X.bucket_da_entrada(entrada)
    final = S.synthesize_bucket(
        copy.deepcopy(b), model=model, fallback_quantidade=True,
        client_call=lambda system, user, m: client_call(system + S._REFORCO_VALIDACAO, user, m))
    bf = {"temas": [asdict(t) for t in final.temas], "observacao_geral": final.observacao_geral,
          "n_validas": final.n_validas, "n_analisadas": len(final.reviews_analisadas),
          "idioma_invalido": final.idioma_invalido, "escopo_suspeito": final.escopo_suspeito}
    json_ok = final.observacao_geral != "Falha ao obter JSON válido do LLM."
    val = validadores_do_bucket(bf, json_ok)
    pend = sum(1 for t in bf["temas"] if t["quantidade_pendente"])
    return {"slug": slug, "bucket": bucket, "bucket_final": bf, "quantidade_fallback": final.quantidade_fallback,
            "json_parseia": json_ok, "validadores": val, "pendentes_depois": pend,
            "passa": bool(val["passa_publicado"] and pend == 0)}


def cmd_regerar(a) -> None:
    if os.environ.get("CLAUDECODE"):
        raise SystemExit("rode FORA do Claude Code (CLAUDECODE está no ambiente)")
    from espectro24 import sintese_local as SL
    SL.resolver_modelo(SL.MODELO_PADRAO)
    DIR_REGERACAO.mkdir(parents=True, exist_ok=True)
    for par in a.par:
        slug, bucket = par.split("/")
        arq = DIR_REGERACAO / f"{slug}__{bucket}.json"
        if arq.exists():
            print(f"{par}: já regerado (UMA nova geração por bucket); nada a fazer")
            continue
        n0, t0 = len(SL.REGISTRO), time.time()
        novo = regerar_um(K.ler_json(X.arq_entrada(slug, bucket)), slug, bucket,
                          lambda s, u, m: SL.client_call_local(s, u, SL.MODELO_PADRAO))
        novo.update(telemetria=SL.REGISTRO[n0:], parede_s=round(time.time() - t0, 1),
                    ts=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        arq.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{par}: passa={novo['passa']} · validadores {novo['validadores']} · pendentes {novo['pendentes_depois']} "
              f"· fallback {novo['quantidade_fallback']} · {novo['parede_s']} s")


def montar_producao(dir_sintese: Path, dir_fallback: Path, dir_regeracao: Path | None = None,
                    validar: bool = True) -> list[dict]:
    """A saída de produção por bucket: o C22 como está, com o fallback aceito no lugar e, para o bucket que
    reprovou nos validadores (C4), a nova geração se ela PASSOU. Bucket reprovado sem geração que passe sai com
    `ok: False` (o filme fica fora desta rodada)."""
    dir_regeracao = DIR_REGERACAO if dir_regeracao is None else dir_regeracao
    saida = []
    for arq in _lista_sintese(dir_sintese):
        reg = json.loads(arq.read_text(encoding="utf-8"))
        fb_arq, rg_arq = dir_fallback / arq.name, dir_regeracao / arq.name
        origem, desfecho, bf, ok = "c22_sem_fallback", None, reg.get("bucket_final"), bool(reg.get("ok"))
        if ok and validar and not validadores_do_bucket(bf, bool(reg.get("json_parseia")))["passa_publicado"]:
            ok, origem = False, "c22_reprovado_nos_validadores"
            if rg_arq.exists():
                rg = json.loads(rg_arq.read_text(encoding="utf-8"))
                if rg["passa"]:
                    ok, origem, desfecho, bf = True, "c22_regerado", rg["quantidade_fallback"], rg["bucket_final"]
                else:
                    origem = "c22_regeracao_reprovada"
            reg = {**reg, "bucket_final": bf}
        pend_antes = pendentes_do_bucket(reg) if ok else 0
        if ok and origem == "c22_sem_fallback" and pend_antes and fb_arq.exists():
            fb = json.loads(fb_arq.read_text(encoding="utf-8"))
            desfecho = fb["quantidade_fallback"]
            origem = "c22_fallback_aceito" if desfecho == "aceito" else f"c22_fallback_{desfecho}"
            if desfecho == "aceito":
                bf = fb["bucket_final"]
        elif ok and origem == "c22_sem_fallback" and pend_antes:
            origem = "c22_pendente_sem_fallback_rodado"
        saida.append({"slug": reg["slug"], "bucket": reg["bucket"], "ok": ok,
                      "origem": origem, "quantidade_fallback": desfecho, "bucket_final": bf,
                      "pendentes_antes": pend_antes,
                      "pendentes_depois": sum(1 for t in (bf or {}).get("temas") or []
                                              if t.get("quantidade_pendente")),
                      "sintese_c22_sha256": K.sha256_arquivo(arq)})
    return saida


def cmd_aplicar(a) -> None:
    pend = json.loads(ARQ_PENDENTES.read_text(encoding="utf-8"))
    falta = [i for i in pend["itens"] if not (DIR_FALLBACK / f"{i['slug']}__{i['bucket']}.json").exists()]
    if falta and not a.parcial:
        raise SystemExit(f"{len(falta)} bucket(s) pendente(s) sem fallback rodado; rode `rodar` (ou use --parcial)")
    linhas = montar_producao(X.DIR_SINTESE, DIR_FALLBACK)
    DIR_PRODUCAO.mkdir(parents=True, exist_ok=True)
    for r in linhas:
        (DIR_PRODUCAO / f"{r['slug']}__{r['bucket']}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    cont: dict[str, int] = {}
    for r in linhas:
        cont[r["origem"]] = cont.get(r["origem"], 0) + 1
    man = {"gerado_por": "scripts/finetune/c22_fallback.py aplicar", "buckets": len(linhas),
           "origens": cont, "bullets_pendentes_depois": sum(r["pendentes_depois"] for r in linhas),
           "arquivos_sha256": {f"{r['slug']}__{r['bucket']}.json":
                               K.sha256_arquivo(DIR_PRODUCAO / f"{r['slug']}__{r['bucket']}.json") for r in linhas}}
    ARQ_MANIFESTO.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: man[k] for k in ("buckets", "origens", "bullets_pendentes_depois")}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    r = sub.add_parser("rodar")
    r.add_argument("--limite", type=int, default=0, help="só os N primeiros (teste de fumaça)")
    g = sub.add_parser("regerar")
    g.add_argument("par", nargs="+", help="<slug>/<bucket>")
    p = sub.add_parser("aplicar")
    p.add_argument("--parcial", action="store_true")
    a = ap.parse_args()
    {"listar": cmd_listar, "rodar": cmd_rodar, "regerar": cmd_regerar, "aplicar": cmd_aplicar}[a.cmd](a)


if __name__ == "__main__":
    main()
