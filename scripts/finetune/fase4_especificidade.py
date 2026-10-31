"""Fase 4, critério C5 — especificidade do TREINADO pela rotulagem cega do dono.

Pelo `finetune/PREREGISTRO_AVALIACAO.md` (seção 3, C5), sem mudar nada do que
lá está:

- frame de cada lado: os bullets que seriam publicados nos 89 buckets de teste
  (o do Gemini fora); bucket `fora_por_memoria` em QUALQUER lado gerado sai dos
  dois lados; bucket do treinado sem temas não tem bullet;
- 60 do TREINADO (T) e 60 do PUBLICADO (P), 20 por bucket (negativas,
  medianas, positivas) em cada lado, uniformes sem reposição, semente
  20261102, um único `random.Random`, na ordem T negativas, T medianas,
  T positivas, P negativas, P medianas, P positivas (cada um sobre os ids
  ordenados); embaralha os 120; 6 repetidos (3 do T, 3 do P) a ≥ 40 posições
  do original;
- documento cego FORA do git (só id e bullet completo, a mesma normalização de
  exibição nos dois lados, `especificidade_validacao.exibir`; a definição de
  G/E da Fase 1 no topo); mapa com selo em `finetune/fase4/`;
- critério: proporção de E do T entre os 60 distintos (rótulo da 1ª
  ocorrência) ≥ 10%; IC de Wilson 95% nos dois lados; consistência dos
  repetidos.

Subcomandos:
    amostrar   (depois da geração do treinado) documento, respostas em branco,
               mapa com selo — sem medida nenhuma
    avaliar    (depois dos rótulos) proporções de E, Wilson, consistência,
               veredito do C5
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402
import especificidade_bullet as B  # noqa: E402
import especificidade_validacao as V  # noqa: E402
import gerar_sintese_teste as G  # noqa: E402

ARQ_PREREGISTRO = K.FINETUNE_DIR / "PREREGISTRO_AVALIACAO.md"
PASTA = K.FINETUNE_DIR / "fase4"
ARQ_MAPA = PASTA / "especificidade_mapa.json"
ARQ_RESULTADO = PASTA / "especificidade_resultado.json"
DOC_DIR = K.RAIZ / "docs" / "arquivo-de-estudos" / "finetune-fase4"
DOC = "rotulagem_especificidade.md"
RESPOSTAS = "rotulos_especificidade.csv"
SEMENTE = 20261102
N_POR_BUCKET = 20
N_REPETIDOS_POR_LADO = 3
DIST_MIN_REPETIDO = 40
E_MIN = 0.10
LADOS = ("treinado", "publicado")
SIGLA = {"treinado": "T", "publicado": "P"}


# ---------------------------------------------------------------------------
# frames
# ---------------------------------------------------------------------------

def pares_de_teste(split: dict) -> list[tuple[str, str]]:
    fora = G.excluidos(split)
    return [(slug, b) for slug in G.filmes_de_teste(split) for b in K.BUCKETS
            if (slug, b) not in fora]


def pasta_sintese(lado: str) -> Path:
    return G.PASTA / f"sintese_{lado}"


def registros(lado: str, pares: list[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    """Os registros de geração de um lado, conferidos contra o manifesto; todo par
    tem de estar feito (`ok`) ou fora por memória."""
    pasta = pasta_sintese(lado)
    manifesto = K.ler_json(pasta / "manifesto.json")
    out = {}
    for slug, bucket in pares:
        arq = pasta / f"{slug}__{bucket}.json"
        if not arq.exists() or K.sha256_arquivo(arq) != manifesto.get(arq.name):
            raise SystemExit(f"{lado}: {arq.name} ausente ou fora do manifesto")
        r = K.ler_json(arq)
        if not (r.get("ok") or r.get("fora_por_memoria")):
            raise SystemExit(f"{lado}: {arq.name} não terminou (nem ok, nem fora por memória)")
        out[(slug, bucket)] = r
    return out


def fora_por_memoria(*lados: dict) -> set[tuple[str, str]]:
    return {k for regs in lados for k, r in regs.items() if r.get("fora_por_memoria")}


def _bullet(lado: str, slug: str, bucket: str, i: int, tema: str, exemplo: str) -> dict:
    return {"id_bullet": f"{SIGLA[lado]}:{slug}|{bucket}|{i}", "lado": lado, "slug": slug,
            "bucket": bucket, "i": i, "tema": tema.strip(), "exemplo": exemplo.strip(),
            "texto": B.texto_do_bullet(tema, exemplo)}


def bullets_treinado(regs: dict, pares: list[tuple[str, str]]) -> list[dict]:
    fora = []
    for slug, bucket in pares:
        for i, t in enumerate((regs[(slug, bucket)].get("bucket_final") or {}).get("temas") or []):
            fora.append(_bullet("treinado", slug, bucket, i, t["tema"], t["exemplo_parafraseado"]))
    return fora


def bullets_publicado(pares: list[tuple[str, str]]) -> list[dict]:
    fora, docs = [], {}
    for slug, bucket in pares:
        doc = docs.setdefault(slug, K.ler_json(K.RESULTADO_DIR / f"{slug}.json"))
        b = next(b for b in doc["buckets"] if b["bucket"] == bucket)
        for i, t in enumerate(b["temas"]):
            fora.append(_bullet("publicado", slug, bucket, i, t["tema"], t["exemplo_parafraseado"]))
    return fora


# ---------------------------------------------------------------------------
# sorteio (função pura: testável sem dado de teste)
# ---------------------------------------------------------------------------

def sortear(treinado: list[dict], publicado: list[dict], rng: random.Random) -> list[dict]:
    por_id = {b["id_bullet"]: b for b in treinado + publicado}
    amostra = []
    for lado, itens in (("treinado", treinado), ("publicado", publicado)):
        for bucket in K.BUCKETS:
            ids = sorted(b["id_bullet"] for b in itens if b["bucket"] == bucket)
            if len(ids) < N_POR_BUCKET:
                raise SystemExit(f"{lado}/{bucket}: {len(ids)} bullets (< {N_POR_BUCKET})")
            amostra += [por_id[i] for i in rng.sample(ids, N_POR_BUCKET)]
    rng.shuffle(amostra)
    return inserir_repetidos(amostra, rng)


def inserir_repetidos(amostra: list[dict], rng: random.Random) -> list[dict]:
    """3 do T e 3 do P (sorteados nessa ordem, pelas posições), cada um inserido a
    `DIST_MIN_REPETIDO` posições do original (depois dele, ou antes se não couber)."""
    repetir = []
    for lado in LADOS:
        pos = [k for k, x in enumerate(amostra) if x["lado"] == lado]
        repetir += rng.sample(pos, N_REPETIDOS_POR_LADO)
    seq = [dict(x) for x in amostra]
    for k in sorted(repetir):
        orig = next(p for p, x in enumerate(seq) if x["id_bullet"] == amostra[k]["id_bullet"]
                    and not x.get("repete"))
        alvo = (orig + DIST_MIN_REPETIDO if orig + DIST_MIN_REPETIDO <= len(seq)
                else max(0, orig - DIST_MIN_REPETIDO))
        seq.insert(alvo, {**amostra[k], "repete": True})
    return seq


def numerar(seq: list[dict]) -> list[dict]:
    itens = []
    for n, x in enumerate(seq, 1):
        itens.append({**{k: x[k] for k in ("id_bullet", "lado", "slug", "bucket", "i", "tema",
                                           "exemplo", "texto")},
                      "id": f"F{n:03d}", "tema_exibido": V.exibir(x["tema"], False),
                      "exemplo_exibido": V.exibir(x["exemplo"], True),
                      "repete": bool(x.get("repete"))})
    for it in itens:
        if it["repete"]:
            it["repete_de"] = next(y["id"] for y in itens
                                   if y["id_bullet"] == it["id_bullet"] and not y["repete"])
    return itens


def _documento(caminho: Path, respostas: Path, itens: list[dict], selo: str) -> int:
    L = ["# Rotulagem manual (Fase 4) — o bullet é GENÉRICO ou ESPECÍFICO?", "",
         f"> **{B.DEFINICAO}**", "",
         f"São {len(itens)} bullets. Leia o bullet inteiro (título e texto). Responda em "
         f"`{respostas.name}` (mesma pasta), uma linha por id: `G` ou `E`. "
         "Não deixe em branco — item sem rótulo trava a avaliação.", ""]
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
    if not V._versionado_e_limpo(ARQ_PREREGISTRO):
        raise SystemExit(f"{ARQ_PREREGISTRO} não está commitado (ou mudou)")
    if ARQ_MAPA.exists():
        raise SystemExit(f"{ARQ_MAPA} já existe: o sorteio do C5 é feito UMA vez")
    split = K.ler_json(a.split)
    pares = pares_de_teste(split)
    if len(pares) != 89 or any(slug not in set(split["teste"]) for slug, _ in pares):
        raise SystemExit(f"{len(pares)} pares de teste (esperados 89, só filmes de teste)")
    regs_t = registros("treinado", pares)
    regs_b = registros("base", pares) if (pasta_sintese("base") / "manifesto.json").exists() else {}
    fora = fora_por_memoria(regs_t, regs_b)
    ficam = [k for k in pares if k not in fora]
    t = bullets_treinado(regs_t, ficam)
    p = bullets_publicado(ficam)
    rng = random.Random(SEMENTE)
    itens = numerar(sortear(t, p, rng))
    mapa = {"gerado_por": "scripts/finetune/fase4_especificidade.py amostrar",
            "semente": SEMENTE, "preregistro_sha256": K.sha256_arquivo(ARQ_PREREGISTRO),
            "split_sha256": K.sha256_arquivo(a.split),
            "manifesto_treinado_sha256": K.sha256_arquivo(pasta_sintese("treinado") / "manifesto.json"),
            "fora_por_memoria": sorted(f"{s}/{b}" for s, b in fora),
            "frame": {"treinado": len(t), "publicado": len(p)},
            "frame_por_bucket": {lado: dict(collections.Counter(x["bucket"] for x in xs))
                                 for lado, xs in (("treinado", t), ("publicado", p))},
            "script_sha256": K.sha256_arquivo(Path(__file__)), "itens": itens}
    PASTA.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA)
    doc_dir = Path(a.doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    palavras = _documento(doc_dir / DOC, doc_dir / RESPOSTAS, itens, selo)
    print(json.dumps({"itens": len(itens), "frame": mapa["frame"],
                      "fora_por_memoria": mapa["fora_por_memoria"],
                      "documento": str(doc_dir / DOC), "palavras": palavras,
                      "respostas": str(doc_dir / RESPOSTAS), "mapa": str(ARQ_MAPA),
                      "selo": selo}, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------------------
# avaliação
# ---------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, c - m), min(1.0, c + m)]


def avaliar(itens: list[dict], rot: dict[str, int]) -> dict:
    """`rot`: id → 1 (G) ou 0 (E)."""
    distintos = [i for i in itens if not i["repete"]]
    por_lado = {}
    for lado in LADOS:
        xs = [i for i in distintos if i["lado"] == lado]
        e = sum(1 for i in xs if rot[i["id"]] == 0)
        por_lado[lado] = {"E": e, "n": len(xs), "proporcao_E": e / len(xs),
                          "wilson95": wilson(e, len(xs)),
                          "por_bucket": {b: sum(1 for i in xs if i["bucket"] == b
                                                and rot[i["id"]] == 0) for b in K.BUCKETS}}
    rep = [{"id": i["id"], "original": i["repete_de"], "lado": i["lado"],
            "igual": rot[i["id"]] == rot[i["repete_de"]]} for i in itens if i["repete"]]
    passa = por_lado["treinado"]["proporcao_E"] >= E_MIN
    return {"por_lado": por_lado,
            "consistencia_dono": {"iguais": sum(r["igual"] for r in rep), "repetidos": len(rep),
                                  "pares": rep},
            "criterio": f"proporção de E do treinado ≥ {E_MIN:.0%}", "C5_passa": passa}


def cmd_avaliar(a) -> None:
    if ARQ_RESULTADO.exists():
        raise SystemExit(f"{ARQ_RESULTADO} já existe: o C5 é avaliado UMA vez")
    mapa = K.ler_json(ARQ_MAPA)
    if a.selo and K.sha256_arquivo(ARQ_MAPA) != a.selo:
        raise SystemExit("o mapa não tem o selo impresso no documento")
    itens = mapa["itens"]
    ids = [i["id"] for i in itens]
    linhas = list(csv.DictReader(open(a.rotulos, encoding="utf-8")))
    if [l["id"].strip() for l in linhas] != ids:
        raise SystemExit("os ids do CSV não são os do mapa (na mesma ordem)")
    rot = B.E1.ler_rotulos(Path(a.rotulos), ids)
    out = {"gerado_por": "scripts/finetune/fase4_especificidade.py avaliar",
           "rotulos_sha256": K.sha256_arquivo(Path(a.rotulos)),
           "mapa_sha256": K.sha256_arquivo(ARQ_MAPA),
           "script_sha256": K.sha256_arquivo(Path(__file__)), **avaliar(itens, rot)}
    ARQ_RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--doc-dir", default=str(DOC_DIR), help="pasta do documento cego (fora do git)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("amostrar")
    v = sub.add_parser("avaliar")
    v.add_argument("--rotulos", default=None)
    v.add_argument("--selo", default="", help="o selo impresso no fim do documento")
    a = ap.parse_args()
    if a.cmd == "avaliar" and a.rotulos is None:
        a.rotulos = str(Path(a.doc_dir) / RESPOSTAS)
    {"amostrar": cmd_amostrar, "avaliar": cmd_avaliar}[a.cmd](a)


if __name__ == "__main__":
    main()
