"""Aplica NA ÁRVORE DE TRABALHO a regeneração com a regra R2 (nada é commitado).

    python scripts/aplicar_regeneracao_r2.py --dry-run
    python scripts/aplicar_regeneracao_r2.py --aplicar [--incluir-novos]
    python scripts/aplicar_regeneracao_r2.py --so-resultado SLUG [SLUG ...]

Para cada filme regenerado em `execucoes/regeneracao-r2-2026-11-26/<slug>/`:

1. **classificação** — as linhas do filme em `resultado/votacao-3/consenso.jsonl`
   e `consenso_verificado.jsonl` são SUBSTITUÍDAS pelas da regeneração (a
   amostra mudou: a guarda C14.8 recusa publicar com uma review sem
   classificação) e o `verificador_manifesto.json` registra a incorporação
   (sha256, n_linhas, n_removidas), como na dos 29 de 08/11;
2. **`resultado/<slug>.json`** — o documento novo (`bullets.json`) com o bloco
   `condicoes` PUBLICÁVEL (R13 aplicada, trava de `publicar_condicoes`).

`--so-resultado` reescreve APENAS `resultado/<slug>.json` (depois de regenerar UM item de um filme
já incorporado: consenso e manifesto não mudam e a incorporação não pode rodar duas vezes).

NÃO toca `dados/publicados.json`, `frontend/` nem faz commit. `--incluir-novos`
grava também `boogie-nights` e `primetime-2026` em `resultado/` (continuam FORA
do catálogo até o dono autorizar). Recusa se o documento novo não tiver as
mesmas chaves do publicado, se o consenso novo não cobrir exatamente a amostra
de produção, ou se algum validador do relatório tiver reprovado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "scripts")]

OUT = RAIZ / "execucoes" / "regeneracao-r2-2026-11-26"
VOTACAO = RAIZ / "resultado" / "votacao-3"
NO_AR = ("casablanca", "its-a-wonderful-life", "modern-times", "rear-window", "seven-samurai")
NOVOS = ("boogie-nights", "primetime-2026")


def ler(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def linhas(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def montar_documento(slug: str) -> dict:
    doc = ler(OUT / slug / "bullets.json")
    est = ler(OUT / slug / "estado.json")
    assert est.get("estado") == "gerado", f"{slug}: não gerado"
    assert all(v.get("passa_publicado") for v in est["validadores_bullets"].values()), f"{slug}: síntese reprovada"
    vc = est["validadores_condicoes"]
    assert vc["flags"] == 0 and vc["inconsistencias_recusa"] == 0 and vc["recusas_invalidas"] == 0, f"{slug}: condições"
    assert est["condicoes_validar_bloco"] == {} or all(
        not isinstance(v, str) for v in est["condicoes_validar_bloco"]), f"{slug}: trava de condições"
    assert "REPROVADO" not in est["condicoes_validar_bloco"], f"{slug}: trava de condições reprovou"
    doc["condicoes"] = ler(OUT / slug / "condicoes" / "condicoes_publicaveis.json")
    assert doc["ficha"].get("paises"), f"{slug}: ficha sem paises"
    return doc


def aplicar(dry_run: bool, incluir_novos: bool) -> dict:
    from espectro24 import eixos as E
    from espectro24 import pipeline as P

    slugs = NO_AR + (NOVOS if incluir_novos else ())
    relatorio = {"slugs": list(slugs), "dry_run": dry_run, "filmes": {}}
    docs = {s: montar_documento(s) for s in slugs}

    for s in NO_AR:
        pub = ler(RAIZ / "resultado" / f"{s}.json")
        assert set(docs[s]) == set(pub), f"{s}: chaves diferem {set(docs[s]) ^ set(pub)}"

    for s in slugs:
        cons_novo = OUT / s / "classificacao" / "consenso_verificado.jsonl"
        am = P.ids_analisados_do_bruto(s)
        # a amostra de PRODUÇÃO (com R2) tem de ser exatamente a classificada
        cat = E.carregar_classificacao(cons_novo)
        E.checar_amostra_classificada(cat[s], am)
        relatorio["filmes"][s] = {"n_amostra": {b: len(v) for b, v in am.items()}}

    if dry_run:
        return relatorio

    manifesto_p = VOTACAO / "verificador_manifesto.json"
    manifesto = ler(manifesto_p)
    inc = {"descricao": ("Regeneração com a regra R2 (2026-11-26): a amostra de 4 filmes no ar mudou "
                         "(resumo de trama `### ` excluído) e foi classificada de novo por filme, "
                         "com DeepSeek-V4.1-Flash-1017 via Featherless (3 passadas + verificador). "
                         "As linhas do filme foram SUBSTITUÍDAS em consenso.jsonl e "
                         "consenso_verificado.jsonl."),
           "filmes": []}
    for nome in ("consenso.jsonl", "consenso_verificado.jsonl"):
        alvo = VOTACAO / nome
        atuais = linhas(alvo)
        novas_por_slug = {s: linhas(OUT / s / "classificacao" / nome) for s in slugs}
        mantidas = [l for l in atuais if l["slug"] not in slugs]
        removidas = {s: sum(1 for l in atuais if l["slug"] == s) for s in slugs}
        assert all(removidas[s] == 0 for s in NOVOS), "filme importado já tinha classificação no consenso"
        saida = mantidas + [l for s in slugs for l in novas_por_slug[s]]
        alvo.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in saida), encoding="utf-8")
        for s in slugs:
            relatorio["filmes"][s][nome] = {"n_removidas": removidas[s], "n_novas": len(novas_por_slug[s])}
            if nome == "consenso_verificado.jsonl":
                inc["filmes"].append({"origem": "regeneracao" if s in NO_AR else "importacao_manual",
                    "slug": s,
                    "consenso": str((OUT / s / "classificacao" / "consenso.jsonl").relative_to(RAIZ)),
                    "consenso_sha256": sha(OUT / s / "classificacao" / "consenso.jsonl"),
                    "consenso_verificado": str((OUT / s / "classificacao" / nome).relative_to(RAIZ)),
                    "consenso_verificado_sha256": sha(OUT / s / "classificacao" / nome),
                    "n_linhas": len(novas_por_slug[s]), "n_removidas": removidas[s]})
        if nome == "consenso_verificado.jsonl":
            manifesto["fonte_n_linhas"] = len(saida)
    # `incorporacoes` (dict) é o registro dos 29 de 08/11 e segue como está; as
    # linhas destes 4 filmes são substituídas, então o registro novo é irmão.
    manifesto["incorporacao_regeneracao_r2"] = inc
    manifesto_p.write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for s in slugs:
        (RAIZ / "resultado" / f"{s}.json").write_text(
            json.dumps(docs[s], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--incluir-novos", action="store_true")
    ap.add_argument("--so-resultado", nargs="+", metavar="SLUG")
    a = ap.parse_args()
    if a.so_resultado:
        for s_ in a.so_resultado:
            doc_ = montar_documento(s_)
            alvo_ = RAIZ / "resultado" / f"{s_}.json"
            if s_ in NO_AR:
                assert set(doc_) == set(ler(alvo_)), f"{s_}: chaves diferem"
            alvo_.write_text(json.dumps(doc_, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("reescrito", alvo_.relative_to(RAIZ))
        sys.exit(0)
    if a.dry_run == a.aplicar:
        ap.error("informe --dry-run OU --aplicar")
    print(json.dumps(aplicar(a.dry_run, a.incluir_novos), ensure_ascii=False, indent=2))
