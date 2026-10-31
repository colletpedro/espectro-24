"""Fase 1, versão 2 — monta a VALIDAÇÃO da especificidade do bullet completo.

Pelo `finetune/especificidade/PROTOCOLO_v2.md` (seção "Validação"), sem mudar
nada do que lá está:

- 60 bullets completos NOVOS, semente 20261022:
  - 30 publicados: 15 de filmes de VALIDAÇÃO e 15 de TREINO fora da
    calibração v2, fora da amostra de títulos arquivada (pelo id) e fora das
    exclusões por título (o mesmo `pool_elegivel` da calibração v2);
  - 30 do modelo base escolhido, sem treino, sorteados entre os 90 bullets de
    `finetune/especificidade/geracao_base/` (5 filmes de TREINO × 3 buckets);
- mais 6 repetidos (consistência do dono), a ≥ 30 posições do original.

Este módulo NÃO calcula medida nenhuma (nem M-disp, nem M-anc, nem AUC): o
sorteio é uniforme dentro de cada fonte, e a avaliação contra o critério só
roda depois de os rótulos voltarem, com os limiares congelados em
`limiares_v2.json` (sha gravado no mapa, valores não lidos).

Ordem do sorteio (um único `random.Random(20261022)`): 15 dos ids de
validação ordenados; 15 dos ids de treino elegíveis ordenados; 30 dos ids da
geração base ordenados; embaralha os 60; sorteia os 6 a repetir.

Formato. A unidade e o texto MEDIDO são os do protocolo (`tema` + " — " +
`exemplo`, cada um sem espaços nas pontas; `especificidade_bullet.texto_do_bullet`).
O texto EXIBIDO ao dono passa pela mesma normalização nas duas fontes, para o
formato não denunciar a origem: 1ª letra do tema e do exemplo em maiúscula e
ponto final no exemplo quando ele não termina em pontuação. Motivo (contado
nas fontes inteiras, não nos itens sorteados): o modelo base escreve 90/90
temas com minúscula inicial (o publicado, 18/1.223) e 6/90 exemplos sem ponto
final (o publicado, 0/1.223). O mapa guarda os dois textos.

Subcomando:
    amostrar   documento cego FORA do git, respostas em branco, mapa com selo
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import especificidade_bullet as B  # noqa: E402 — sem alteração (sha ff71747e…)
import comum as K  # noqa: E402

DIR = B.DIR
ARQ_MAPA = DIR / "mapa" / "validacao_v2_mapa.json"
ARQ_FILMES = B.E1.ARQ_VAL_FILMES
PASTA_BASE = DIR / "geracao_base"
ARQ_MANIFESTO_BASE = PASTA_BASE / "manifesto.json"
DOC = "rotulagem_validacao_v2.md"
RESPOSTAS = "rotulos_validacao_v2.csv"
SEMENTE_VAL = B.E1.SEMENTE_VAL                   # 20261022 (PROTOCOLO e PROTOCOLO_v2)
N_VALIDACAO, N_TREINO, N_BASE = 15, 15, 30
N_REPETIDOS = 6
DIST_MIN_REPETIDO = 30                           # não pré-registrado: ~45% de 66, como 40/90
PONTUACAO_FINAL = (".", "!", "?", "…", '"', "”", ")")


def _versionado_e_limpo(p: Path) -> bool:
    """O arquivo está commitado e sem mudança no repositório que o contém (o
    `finetune/` pode ser outro worktree)."""
    p = p.resolve()
    ls = subprocess.run(["git", "-C", str(p.parent), "ls-files", "--error-unmatch", p.name],
                        capture_output=True).returncode == 0
    dif = subprocess.run(["git", "-C", str(p.parent), "diff", "--quiet", "HEAD", "--", p.name],
                         capture_output=True).returncode
    return ls and dif == 0


def exibir(s: str, exemplo: bool) -> str:
    s = s.strip()
    s = s[:1].upper() + s[1:]
    if exemplo and not s.endswith(PONTUACAO_FINAL):
        s += "."
    return s


def bullets_base(split: dict) -> list[dict]:
    """Os 90 bullets da geração base, conferidos contra o manifesto."""
    filmes = K.ler_json(ARQ_FILMES)["filmes_geracao"]
    proibidos = set(split["validacao"]) | set(split["teste"]) | set(K.REFERENCIA_5)
    ruins = [f for f in filmes if f not in split["treino"] or f in proibidos]
    if ruins:
        raise SystemExit(f"filme(s) da geração fora do TREINO: {ruins}")
    manifesto = K.ler_json(ARQ_MANIFESTO_BASE)
    fora = []
    for slug in filmes:
        for bucket in K.BUCKETS:
            arq = PASTA_BASE / f"{slug}__{bucket}.json"
            if K.sha256_arquivo(arq) != manifesto.get(arq.name):
                raise SystemExit(f"{arq.name}: sha256 diferente do manifesto da geração")
            d = K.ler_json(arq)
            if not (d.get("ok") and d.get("json_parseia")):
                raise SystemExit(f"{arq.name}: geração sem ok/json válido")
            for i, b in enumerate(d["bullets"]):
                if not b["completo"]:
                    continue
                fora.append({"id_bullet": f"base:{slug}|{bucket}|{i}", "fonte": "base",
                             "conjunto": "treino", "slug": slug, "bucket": bucket, "i": i,
                             "tema": b["tema"].strip(),
                             "exemplo": b["exemplo_parafraseado"].strip(),
                             "texto": B.texto_do_bullet(b["tema"], b["exemplo_parafraseado"])})
    return fora


def _inserir_repetidos(amostra: list[dict], rng: random.Random) -> list[dict]:
    """O `especificidade_bullet._inserir_repetidos`, com 6 e distância 30."""
    repetir = rng.sample(range(len(amostra)), N_REPETIDOS)
    seq = [dict(x) for x in amostra]
    for k in sorted(repetir):
        orig = next(p for p, x in enumerate(seq) if x["id_bullet"] == amostra[k]["id_bullet"]
                    and not x.get("repete"))
        alvo = (orig + DIST_MIN_REPETIDO if orig + DIST_MIN_REPETIDO <= len(seq)
                else max(0, orig - DIST_MIN_REPETIDO))
        seq.insert(alvo, {**amostra[k], "repete": True})
    return seq


def _documento(caminho: Path, respostas: Path, itens: list[dict], selo: str) -> int:
    L = ["# Rotulagem manual (validação v2) — o bullet é GENÉRICO ou ESPECÍFICO?", "",
         f"> **{B.DEFINICAO}**", "",
         f"São {len(itens)} bullets. Leia o bullet inteiro (título e texto). Responda em "
         f"`{respostas.name}` (mesma pasta), uma linha por id: `G` ou `E`. "
         "Não deixe em branco — item sem rótulo trava a validação.", ""]
    for it in itens:
        L += ["---", "", f"**{it['id']}** — **{it['tema_exibido']}**{B.SEP}{it['exemplo_exibido']}",
              "", f"{it['id']}: G / E", ""]
    L += ["---", "", f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    texto = "\n".join(L)
    caminho.write_text(texto, encoding="utf-8")
    with open(respostas, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["id", "rotulo"])
        for it in itens:
            wr.writerow([it["id"], ""])
    return len(texto.split())


def cmd_amostrar(a) -> None:
    for p in (B.ARQ_DESVIO, B.ARQ_PROTOCOLO, B.ARQ_LIMIARES, B.ARQ_MAPA, ARQ_MANIFESTO_BASE):
        if not _versionado_e_limpo(p):
            raise SystemExit(f"{p} não está commitado (ou mudou): vem ANTES do documento")
    if ARQ_MAPA.exists() and not a.refazer:
        raise SystemExit(f"{ARQ_MAPA} já existe: a validação é montada UMA vez")
    split = K.ler_json(a.split)
    ref = B.ler_referencia()
    if K.sha256_arquivo(B.ARQ_REF) != "da8723a62ebf8de16b8344e1e73a0891cc64bb4c76505a7046ddcd963de54522":
        raise SystemExit("referencia_bullets.jsonl não é a congelada do PROTOCOLO_v2")
    cal = {i["id_bullet"] for i in K.ler_json(B.ARQ_MAPA)["itens"]}
    ids_v1, _ = B.excluidos_v1()
    pool_treino, _ = B.pool_elegivel(ref, split)
    pool_treino = [r for r in pool_treino if r["id_bullet"] not in cal]
    validacao = [r for r in ref if r["conjunto"] == "validacao"]
    assert all(r["slug"] in split["validacao"] for r in validacao)
    base = bullets_base(split)
    teste = set(split["teste"])
    if any(r["slug"] in teste for r in pool_treino + validacao + base):
        raise SystemExit("filme de TESTE entre os candidatos: recusado")

    rng = random.Random(SEMENTE_VAL)
    fontes = (("publicado", "validacao", validacao, N_VALIDACAO),
              ("publicado", "treino", pool_treino, N_TREINO),
              ("base", "treino", base, N_BASE))
    por_id, amostra = {}, []
    for fonte, conjunto, itens, n in fontes:
        por_id.update({r["id_bullet"]: {**r, "fonte": fonte, "conjunto": conjunto} for r in itens})
        amostra += [{"id_bullet": i} for i in rng.sample(sorted(r["id_bullet"] for r in itens), n)]
    rng.shuffle(amostra)
    if len({x["id_bullet"] for x in amostra}) != len(amostra):
        raise SystemExit("item repetido entre as fontes")
    if any(x["id_bullet"] in cal or x["id_bullet"] in ids_v1 for x in amostra):
        raise SystemExit("item da calibração v2 ou da amostra de títulos arquivada no sorteio")
    seq = _inserir_repetidos(amostra, rng)

    itens = []
    for n, x in enumerate(seq, 1):
        r = por_id[x["id_bullet"]]
        itens.append({"id": f"V{n:02d}", "id_bullet": r["id_bullet"], "fonte": r["fonte"],
                      "conjunto": r["conjunto"], "slug": r["slug"], "bucket": r["bucket"],
                      "i": r["i"], "tema": r["tema"], "exemplo": r["exemplo"],
                      "texto": r["texto"], "tema_exibido": exibir(r["tema"], False),
                      "exemplo_exibido": exibir(r["exemplo"], True),
                      "repete": bool(x.get("repete"))})
    origem = {}
    for it in itens:
        if it["repete"]:
            o = next(y for y in itens if y["id_bullet"] == it["id_bullet"] and not y["repete"])
            it["repete_de"] = o["id"]
            origem[it["id"]] = o["id"]
    dist = [abs(int(k[1:]) - int(v[1:])) for k, v in origem.items()]
    if min(dist) < DIST_MIN_REPETIDO:
        raise SystemExit(f"repetição a {min(dist)} posições do original (< {DIST_MIN_REPETIDO})")
    distintos = [i for i in itens if not i["repete"]]
    mudou = collections.Counter(i["fonte"] for i in distintos
                                if (i["tema_exibido"], i["exemplo_exibido"]) != (i["tema"], i["exemplo"]))
    mapa = {"gerado_por": "scripts/finetune/especificidade_validacao.py amostrar",
            "unidade": "bullet completo = tema + ' — ' + exemplo_parafraseado (DESVIO_01)",
            "semente": SEMENTE_VAL,
            "ordem_do_sorteio": "15 validação, 15 treino elegível, 30 base (cada um dos ids "
                                "ordenados); shuffle dos 60; 6 repetidos",
            "texto_medido": "campo `texto` (o do protocolo, sem normalização)",
            "texto_exibido": "1ª letra do tema e do exemplo em maiúscula; ponto final no "
                             "exemplo sem pontuação final — a mesma regra nas duas fontes",
            "itens_distintos_com_exibicao_normalizada": dict(mudou),
            "referencia_sha256": K.sha256_arquivo(B.ARQ_REF),
            "protocolo_v2_sha256": K.sha256_arquivo(B.ARQ_PROTOCOLO),
            "desvio_sha256": K.sha256_arquivo(B.ARQ_DESVIO),
            "limiares_v2_sha256": K.sha256_arquivo(B.ARQ_LIMIARES),
            "mapa_calibracao_v2_sha256": K.sha256_arquivo(B.ARQ_MAPA),
            "mapa_v1_sha256": K.sha256_arquivo(B.ARQ_MAPA_V1),
            "manifesto_geracao_base_sha256": K.sha256_arquivo(ARQ_MANIFESTO_BASE),
            "validacao_filmes_sha256": K.sha256_arquivo(ARQ_FILMES),
            "script_sha256": K.sha256_arquivo(Path(__file__)),
            "especificidade_bullet_sha256": K.sha256_arquivo(Path(B.__file__)),
            "especificidade_v1_sha256": K.sha256_arquivo(Path(B.E1.__file__)),
            "candidatos": {"publicado_validacao": len(validacao),
                           "publicado_treino_elegivel": len(pool_treino), "base": len(base)},
            "distancia_minima_repeticao": min(dist), "itens": itens}
    ARQ_MAPA.parent.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA)
    doc_dir = Path(a.doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    palavras = _documento(doc_dir / DOC, doc_dir / RESPOSTAS, itens, selo)
    print(json.dumps({"itens": len(itens), "distintos": len(distintos),
                      "por_fonte": dict(collections.Counter(
                          f"{i['fonte']}/{i['conjunto']}" for i in distintos)),
                      "repetidos": len(origem), "distancia_minima_repeticao": min(dist),
                      "filmes_distintos": len({i["slug"] for i in distintos}),
                      "candidatos": mapa["candidatos"],
                      "exibicao_normalizada": dict(mudou),
                      "documento": str(doc_dir / DOC),
                      "documento_sha256": K.sha256_arquivo(doc_dir / DOC),
                      "palavras_documento": palavras, "respostas": str(doc_dir / RESPOSTAS),
                      "respostas_sha256": K.sha256_arquivo(doc_dir / RESPOSTAS),
                      "mapa": str(ARQ_MAPA), "selo": selo}, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--doc-dir", default=str(B.DOC_DIR_PADRAO),
                    help="pasta do documento cego (fora do git)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("amostrar")
    s.add_argument("--refazer", action="store_true",
                   help="só se o mapa anterior NÃO chegou ao dono")
    a = ap.parse_args()
    {"amostrar": cmd_amostrar}[a.cmd](a)


if __name__ == "__main__":
    main()
