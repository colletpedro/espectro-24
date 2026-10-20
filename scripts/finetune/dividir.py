"""Fase 0 do fine-tuning — (c) divisão POR FILME em treino / validação / teste.

Regras (do dono, invariantes):
- a unidade é o filme; nenhum filme de teste entra no treino em estágio
  nenhum, nem agora nem depois;
- o teste contém OBRIGATORIAMENTE os 5 da medição de referência
  (`comum.REFERENCIA_5`);
- filmes excluídos (`comum.EXCLUIR_FILMES`) não entram em conjunto nenhum.

Sorteio ESTRATIFICADO, semente fixa. Estratos (PROPOSTO):
1. época do professor da síntese — V4-Flash (até 09/09) × V4.1-Flash (desde
   10/09): é o "lote ou época do pipeline" que muda o alvo;
2. tamanho do corpus — tercil do total de tokens de ENTRADA da síntese do
   filme (soma dos buckets, tokenizer do Qwen3.5);
3. perfil de recepção (`perfil` do consenso: `aclamado` × os demais —
   divisivo, invertido, arthouse, obscuro): é o equilíbrio ENTRE os buckets, o
   quanto da recepção cai em cada grupo.

Alocação: cota proporcional por estrato (maiores restos), os 5 fixos
descontados da cota do estrato deles, o resto sorteado dentro do estrato.
Validação: o mesmo procedimento sobre o que sobra.

Saída: `finetune/split.json` (o sha256 vai no relatório) e `finetune/split.md`.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

SEMENTE = 20261020
# 30 e não os ~20 da proposta inicial (`poder.py`, ESTIMADO): com o ICC medido
# na referência (0,023), o menor aumento detectável na taxa de "sem apoio" é
# +5,3 pp com 20 filmes, +4,6 com 25 e +4,0 com 30 (analítico, conservador).
# A diferença entre o qwen3:14b sem ajuste e o publicado foi +4,4 pp: só 30
# filmes a detectam com poder 0,80. Trocar por 20 ou 25 é decisão do dono
# (`--n-teste`), e o sorteio refeito muda os filmes.
N_TESTE = 30
N_VALIDACAO = 8
TOKENIZER_TAMANHO = "Qwen3.5-9B"
CONSENSO = K.RESULTADO_DIR / "votacao-3" / "consenso_verificado.jsonl"
GABARITO_AMOSTRA = K.RESULTADO_DIR / "auditoria-acuracia" / "amostra.json"


def maiores_restos(total: int, pesos: dict[str, int]) -> dict[str, int]:
    soma = sum(pesos.values())
    bruto = {k: total * v / soma for k, v in pesos.items()}
    base = {k: int(v) for k, v in bruto.items()}
    falta = total - sum(base.values())
    for k in sorted(bruto, key=lambda k: (-(bruto[k] - base[k]), k))[:falta]:
        base[k] += 1
    return base


def alocar(estrato_de: dict[str, str], n: int, fixos: list[str], rng: random.Random) -> list[str]:
    """`n` filmes, os `fixos` inclusos, proporcional aos estratos."""
    por = collections.defaultdict(list)
    for s, e in estrato_de.items():
        por[e].append(s)
    alvo = maiores_restos(n, {e: len(v) for e, v in por.items()})
    fixos_por = collections.Counter(estrato_de[s] for s in fixos)
    sorteio = {e: max(alvo[e] - fixos_por[e], 0) for e in por}
    # estrato cujos fixos passam da cota: o excesso sai dos que têm mais folga
    while len(fixos) + sum(sorteio.values()) > n:
        e = max((e for e in sorteio if sorteio[e] > 0),
                key=lambda e: (fixos_por[e] + sorteio[e] - n * len(por[e]) / len(estrato_de), e))
        sorteio[e] -= 1
    escolhidos = list(fixos)
    for e in sorted(por):
        livres = sorted(s for s in por[e] if s not in fixos)
        escolhidos += rng.sample(livres, sorteio[e])
    return sorted(escolhidos)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventario", type=Path, default=K.FINETUNE_DIR / "inventario.json")
    ap.add_argument("--saida", type=Path, default=K.FINETUNE_DIR)
    ap.add_argument("--n-teste", type=int, default=N_TESTE)
    ap.add_argument("--n-validacao", type=int, default=N_VALIDACAO)
    a = ap.parse_args()

    inv = K.ler_json(a.inventario)
    perfil = {}
    for ln in CONSENSO.read_text(encoding="utf-8").split("\n"):
        if ln.strip():
            r = json.loads(ln)
            perfil.setdefault(r["slug"], r.get("perfil"))
    tam = collections.Counter()
    for x in inv["exemplos_sintese"]:
        if not x["excluido"]:
            tam[x["slug"]] += x["tokens"][TOKENIZER_TAMANHO]["entrada"]

    pool = sorted(s for s, f in inv["filmes"].items() if not f["excluido"])
    faltam = [s for s in K.REFERENCIA_5 if s not in pool]
    if faltam:
        raise SystemExit(f"filmes de referência fora do pool: {faltam}")
    ordenados = sorted(pool, key=lambda s: (tam[s], s))
    tercil = {s: min(3, 1 + (3 * i) // len(ordenados)) for i, s in enumerate(ordenados)}
    var = {s: {"epoca_professor": inv["filmes"][s]["sintese"]["epoca_professor"],
               "tercil_tamanho": tercil[s],
               "perfil": perfil.get(s),
               "perfil_grupo": "aclamado" if perfil.get(s) == "aclamado" else "outros",
               "tokens_entrada_sintese": tam[s],
               "lote": inv["filmes"][s]["sintese"]["lote"],
               "algum_bucket_reduzido": any(b["modo"] == "reduzido"
                                            for b in inv["filmes"][s]["buckets"].values()),
               "n_buckets_sintese": sum(1 for b in inv["filmes"][s]["buckets"].values()
                                        if b["utilizavel"]),
               "n_bullets": sum(b["n_temas"] for b in inv["filmes"][s]["buckets"].values()
                                if b["utilizavel"])}
           for s in pool}
    estrato = {s: f"{v['epoca_professor']}|T{v['tercil_tamanho']}|{v['perfil_grupo']}"
               for s, v in var.items()}

    rng = random.Random(SEMENTE)
    teste = alocar(estrato, a.n_teste, sorted(K.REFERENCIA_5), rng)
    resto = {s: e for s, e in estrato.items() if s not in teste}
    validacao = alocar(resto, a.n_validacao, [], rng)
    treino = sorted(s for s in pool if s not in teste and s not in validacao)
    assert not set(teste) & set(treino) and not set(validacao) & set(treino)
    assert set(K.REFERENCIA_5) <= set(teste)

    conj = {**{s: "teste" for s in teste}, **{s: "validacao" for s in validacao},
            **{s: "treino" for s in treino}}
    balanco = {}
    for chave in ("epoca_professor", "tercil_tamanho", "perfil_grupo", "perfil", "lote",
                  "algum_bucket_reduzido"):
        c = collections.defaultdict(collections.Counter)
        for s in pool:
            c[str(var[s][chave])][conj[s]] += 1
        balanco[chave] = {k: dict(v) for k, v in sorted(c.items())}
    # Buckets fora de TUDO (decisão do dono, gate 0): o filme fica no conjunto
    # dele, mas o bucket não é exemplo de treino nem entra em avaliação nenhuma,
    # em nenhum lado (publicado, base, treinado).
    excl_b = [{"slug": s, "bucket": bn, "conjunto": conj[s], "motivo": b["motivo"],
               "regra": "fora do treino e de toda avaliação, em todos os lados"}
              for s in pool for bn, b in sorted(inv["filmes"][s]["buckets"].items())
              if not b["utilizavel"]]
    gab_teste = sorted(r["id"] for r in K.ler_json(GABARITO_AMOSTRA)["reviews"]
                       if r["slug"] in teste)
    resumo = {c: {"n_filmes": sum(1 for s in pool if conj[s] == c),
                  "n_exemplos_sintese": sum(var[s]["n_buckets_sintese"] for s in pool
                                            if conj[s] == c),
                  "n_bullets": sum(var[s]["n_bullets"] for s in pool if conj[s] == c)}
              for c in ("treino", "validacao", "teste")}
    saida = {
        "versao": 1, "gerado_por": "scripts/finetune/dividir.py",
        "semente": SEMENTE, "n_teste": a.n_teste, "n_validacao": a.n_validacao,
        "unidade": "filme",
        "invariantes": [
            "nenhum filme de teste entra no treino em estágio nenhum, nem agora nem depois",
            "os 5 da referência estão no teste",
            "filmes excluídos não estão em conjunto nenhum",
            "filme publicado DEPOIS deste split vai para o treino (PROPOSTO; o teste é congelado)"],
        "estratos": "época do professor × tercil de tokens de entrada da síntese × "
                    "perfil (aclamado/outros)",
        "inventario_sha256": K.sha256_arquivo(a.inventario),
        "excluidos": K.EXCLUIR_FILMES,
        "buckets_excluidos": excl_b,
        "teste": teste, "validacao": validacao, "treino": treino,
        "fixos_no_teste": sorted(K.REFERENCIA_5),
        "resumo": resumo, "balanco": balanco,
        "gabarito_humano_em_filmes_de_teste": gab_teste,
        "filmes": {s: {**var[s], "estrato": estrato[s], "conjunto": conj[s],
                       "buckets_excluidos": [x["bucket"] for x in excl_b if x["slug"] == s]}
                   for s in pool},
    }
    a.saida.mkdir(parents=True, exist_ok=True)
    arq = a.saida / "split.json"
    arq.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (a.saida / "split.md").write_text(md(saida), encoding="utf-8")
    print(md(saida))
    print("sha256 split.json:", K.sha256_arquivo(arq))


def md(s: dict) -> str:
    L = ["# Divisão por filme (PROPOSTA)", "",
         f"Semente {s['semente']}. Estratos: {s['estratos']}. "
         f"Teste {s['n_teste']} (os 5 da referência + {s['n_teste'] - 5} sorteados), "
         f"validação {s['n_validacao']}, treino o resto.", "",
         "| conjunto | filmes | exemplos de síntese (buckets) | bullets |", "|---|---|---|---|"]
    for c, r in s["resumo"].items():
        L.append(f"| {c} | {r['n_filmes']} | {r['n_exemplos_sintese']} | {r['n_bullets']} |")
    L += ["", f"**Teste:** {', '.join(s['teste'])}", "",
          f"**Validação:** {', '.join(s['validacao'])}", "",
          f"**Treino:** {', '.join(s['treino'])}", "", "## Balanço", ""]
    for chave, tab in s["balanco"].items():
        L.append(f"- **{chave}**: " + "; ".join(
            f"{k} → treino {v.get('treino', 0)} / val {v.get('validacao', 0)} / teste {v.get('teste', 0)}"
            for k, v in tab.items()))
    L += ["", "**Buckets excluídos** (fora do treino e de toda avaliação, em todos os lados): "
          + ("; ".join(f"`{x['slug']}/{x['bucket']}` ({x['conjunto']}) — {x['motivo']}"
                       for x in s["buckets_excluidos"]) or "nenhum")]
    L += ["", f"Reviews do gabarito humano em filmes de teste (nunca treinar classificação "
          f"nelas): {len(s['gabarito_humano_em_filmes_de_teste'])}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
