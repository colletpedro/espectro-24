"""Fase 1, versão 2 — especificidade do BULLET COMPLETO (DESVIO_01).

A unidade deixa de ser o título (`tema`) e passa a ser o bullet completo:
`tema` + `exemplo_parafraseado`, no formato da leitura cega anterior
("tema — exemplo"). Sem números nem contagens (`mencoes_aproximadas`,
`n_reviews_analisadas`, a barra) e sem o nome do bucket. Decisão do dono em
2026-10-30 (`finetune/especificidade/DESVIO_01.md`): o bloco do bullet no
frontend só mostra o título e a barra (`frontend/js/filme.js:1781`,
`1785–1793`); o único texto além do título é o exemplo ("Aprofundar",
`filme.js:1819–1837`).

Protocolo: `finetune/especificidade/PROTOCOLO_v2.md` (commit próprio, ANTES do
documento). As medidas são as de `especificidade.py`, sem alteração de forma —
este módulo importa M-disp (`Disp`), M-anc (`m_anc`, `vocabulario_das_reviews`),
a AUC/Youden ponderados e a logística de lá, e só troca o texto medido.

Subcomandos:
    referencia            grava `referencia_bullets.jsonl` e o sha256; conta os
                          textos que o e5 truncaria (512 tokens)
    amostrar-calibracao   80 bullets de TREINO (20 por quartil de M-disp no pool
                          elegível) + 10 repetidos; documento cego FORA do git,
                          respostas em branco, mapa com selo — sem exibir medida
    lote-extra            contingência: só se a calibração tiver < 15 E
                          distintos; 40 bullets por quartil de M-anc (5/5/10/20,
                          o mais específico sobreamostrado)
    medir                 (depois dos rótulos) Youden ponderado, M-comb,
                          consistência do dono; congela `limiares_v2.json`
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import especificidade as E1  # noqa: E402 — importa _guarda e comum (sem chave, sem rede)
import comum as K  # noqa: E402

DIR = E1.DIR
ARQ_REF = DIR / "referencia_bullets.jsonl"
ARQ_PROTOCOLO = DIR / "PROTOCOLO_v2.md"
ARQ_DESVIO = DIR / "DESVIO_01.md"
ARQ_MAPA_V1 = E1.ARQ_MAPA_CAL                  # só para EXCLUIR o que o dono já viu
ARQ_MAPA = DIR / "mapa" / "calibracao_v2_mapa.json"
ARQ_MAPA_EXTRA = DIR / "mapa" / "calibracao_v2_extra_mapa.json"
ARQ_LIMIARES = DIR / "limiares_v2.json"
DOC_DIR_PADRAO = E1.DOC_DIR
DOC = "rotulagem_calibracao_v2.md"
RESPOSTAS = "rotulos_calibracao_v2.csv"
DOC_EXTRA = "rotulagem_calibracao_v2_extra.md"
RESPOSTAS_EXTRA = "rotulos_calibracao_v2_extra.csv"

DEFINICAO = ("Genérico = este bullet, como está escrito, poderia aparecer quase sem "
             "mudança em muitos filmes diferentes. Específico = diz algo que só vale "
             "para este filme ou para poucos.")
SEP = " — "                                      # o separador da leitura cega
SEMENTE_CAL = 20261030
SEMENTE_EXTRA = 20261031
N_POR_QUARTIL = E1.N_POR_QUARTIL                 # 20
N_REPETIDOS = E1.N_REPETIDOS                     # 10
DIST_MIN_REPETIDO = E1.DIST_MIN_REPETIDO         # 40
MIN_E_DISTINTOS = 15
EXTRA_POR_QUARTIL_ANC = {1: 5, 2: 5, 3: 10, 4: 20}   # quartil 4 = M-anc mais alta = mais específico


def texto_do_bullet(tema: str, exemplo: str) -> str:
    return f"{tema.strip()}{SEP}{exemplo.strip()}"


def _norm(s: str) -> str:
    return " ".join(E1._sem_acento(s).split())


# ---------------------------------------------------------------------------
# referência
# ---------------------------------------------------------------------------

def montar_referencia(split: dict) -> list[dict]:
    """Os mesmos bullets da referência de títulos (mesmas exclusões), com o texto."""
    fora, docs = [], {}
    for r in E1.montar_referencia(split):
        doc = docs.setdefault(r["slug"], K.ler_json(K.RESULTADO_DIR / f"{r['slug']}.json"))
        b = next(b for b in doc["buckets"] if b["bucket"] == r["bucket"])
        t = b["temas"][r["i"]]
        assert t["tema"] == r["tema"]
        ex = (t.get("exemplo_parafraseado") or "").strip()
        if not ex:
            raise SystemExit(f"{r['id_titulo']}: sem exemplo_parafraseado")
        fora.append({"id_bullet": r["id_titulo"], "slug": r["slug"], "bucket": r["bucket"],
                     "i": r["i"], "tema": r["tema"], "exemplo": ex,
                     "texto": texto_do_bullet(r["tema"], ex), "conjunto": r["conjunto"]})
    return fora


def ler_referencia() -> list[dict]:
    return [json.loads(l) for l in ARQ_REF.read_text(encoding="utf-8").split("\n") if l.strip()]


def truncamento(textos: list[str], enc) -> dict:
    """Tokens do e5 com o prefixo `query: ` (o que `Disp` codifica)."""
    import encoder_e5 as E5
    tok = enc.tokenizador()
    n = [len(tok.encode("query: " + t).ids) for t in textos]
    trunc = [x for x in n if x > E5.MAX_TOKENS]
    return {"limite_tokens": E5.MAX_TOKENS, "textos": len(n), "truncados": len(trunc),
            "comprimentos_truncados": sorted(trunc), "max_tokens": max(n),
            "mediana_tokens": sorted(n)[len(n) // 2]}


def disp(ref: list[dict], enc) -> "E1.Disp":
    # `Disp` lê o texto em `tema`: aqui ele recebe o bullet completo
    return E1.Disp([{"slug": r["slug"], "tema": r["texto"]} for r in ref], enc)


# ---------------------------------------------------------------------------
# pool elegível e exclusões
# ---------------------------------------------------------------------------

def excluidos_v1() -> tuple[set[str], set[str]]:
    """Ids e títulos (normalizados) da amostra de títulos arquivada."""
    itens = K.ler_json(ARQ_MAPA_V1)["itens"]
    return {i["id_titulo"] for i in itens}, {_norm(i["tema"]) for i in itens}


def pool_elegivel(ref: list[dict], split: dict) -> tuple[list[dict], int]:
    ids_v1, temas_v1 = excluidos_v1()
    treino = [r for r in ref if r["conjunto"] == "treino"]
    assert all(r["slug"] in split["treino"] for r in treino)
    pool = [r for r in treino if r["id_bullet"] not in ids_v1 and _norm(r["tema"]) not in temas_v1]
    return pool, len(treino) - len(pool)


def _quartis(pool: list[dict], valores: list[float]) -> dict[str, int]:
    """Quartil pela posição na ordem (valor, id): empates desfeitos pelo id."""
    ordem = sorted(range(len(pool)), key=lambda i: (valores[i], pool[i]["id_bullet"]))
    return {pool[i]["id_bullet"]: 1 + (4 * pos) // len(pool) for pos, i in enumerate(ordem)}


def _inserir_repetidos(amostra: list[dict], rng: random.Random) -> list[dict]:
    repetir = rng.sample(range(len(amostra)), N_REPETIDOS)
    seq = [dict(x) for x in amostra]
    for k in sorted(repetir):
        orig = next(p for p, x in enumerate(seq) if x["id_bullet"] == amostra[k]["id_bullet"]
                    and not x.get("repete"))
        alvo = (orig + DIST_MIN_REPETIDO if orig + DIST_MIN_REPETIDO <= len(seq)
                else max(0, orig - DIST_MIN_REPETIDO))
        seq.insert(alvo, {**amostra[k], "repete": True})
    return seq


def _documento(caminho: Path, respostas: Path, itens: list[dict], selo: str, titulo: str) -> int:
    L = [f"# {titulo}", "", f"> **{DEFINICAO}**", "",
         f"São {len(itens)} bullets. Leia o bullet inteiro (título e texto). Responda em "
         f"`{respostas.name}` (mesma pasta), uma linha por id: `G` ou `E`. "
         "Não deixe em branco — item sem rótulo trava a calibração.", ""]
    for it in itens:
        L += ["---", "", f"**{it['id']}** — **{it['tema']}**{SEP}{it['exemplo']}", "",
              f"{it['id']}: G / E", ""]
    L += ["---", "", f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    texto = "\n".join(L)
    caminho.write_text(texto, encoding="utf-8")
    with open(respostas, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["id", "rotulo"])
        for it in itens:
            wr.writerow([it["id"], ""])
    return len(texto.split())


def _exigir_commitados() -> None:
    for p in (ARQ_DESVIO, ARQ_PROTOCOLO):
        if not E1._git_limpo_e_versionado(p):
            raise SystemExit(f"{p} não está commitado (ou mudou): vem ANTES do documento")


# ---------------------------------------------------------------------------
# comandos
# ---------------------------------------------------------------------------

def cmd_referencia(a) -> None:
    ref = montar_referencia(K.ler_json(a.split))
    ARQ_REF.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ref),
                       encoding="utf-8")
    c = collections.Counter(r["conjunto"] for r in ref)
    print(json.dumps({"bullets": len(ref), "por_conjunto": c,
                      "filmes": len({r["slug"] for r in ref}),
                      "sha256": K.sha256_arquivo(ARQ_REF),
                      "e5": truncamento([r["texto"] for r in ref], E1._encoder())},
                     ensure_ascii=False))


def cmd_amostrar_calibracao(a) -> None:
    _exigir_commitados()
    split = K.ler_json(a.split)
    ref = ler_referencia()
    pool, n_excl = pool_elegivel(ref, split)
    enc = E1._encoder()
    valores = disp(ref, enc).medir([r["texto"] for r in pool], [r["slug"] for r in pool])
    quartil = _quartis(pool, valores)
    del valores                              # nenhum valor sai daqui (só o quartil)
    rng = random.Random(SEMENTE_CAL)
    tamanhos = collections.Counter(quartil.values())
    amostra = []
    for q in (1, 2, 3, 4):
        ids = sorted(r["id_bullet"] for r in pool if quartil[r["id_bullet"]] == q)
        amostra += [{"id_bullet": i, "quartil": q} for i in rng.sample(ids, N_POR_QUARTIL)]
    rng.shuffle(amostra)
    seq = _inserir_repetidos(amostra, rng)
    por_id = {r["id_bullet"]: r for r in ref}
    itens = []
    for n, x in enumerate(seq, 1):
        r = por_id[x["id_bullet"]]
        itens.append({"id": f"B{n:02d}", **{k: r[k] for k in ("id_bullet", "slug", "bucket", "i",
                                                                "tema", "exemplo", "texto")},
                      "quartil_disp": x["quartil"], "repete": bool(x.get("repete"))})
    origem = {}
    for it in itens:
        if it["repete"]:
            o = next(y for y in itens if y["id_bullet"] == it["id_bullet"] and not y["repete"])
            it["repete_de"] = o["id"]
            origem[it["id"]] = o["id"]
    dist = [abs(int(k[1:]) - int(v[1:])) for k, v in origem.items()]
    if min(dist) < DIST_MIN_REPETIDO:
        raise SystemExit(f"repetição a {min(dist)} posições do original (< {DIST_MIN_REPETIDO})")
    mapa = {"gerado_por": "scripts/finetune/especificidade_bullet.py amostrar-calibracao",
            "unidade": "bullet completo = tema + ' — ' + exemplo_parafraseado (DESVIO_01)",
            "semente": SEMENTE_CAL, "k_disp": E1.K_DISP,
            "referencia_sha256": K.sha256_arquivo(ARQ_REF),
            "protocolo_sha256": K.sha256_arquivo(ARQ_PROTOCOLO),
            "desvio_sha256": K.sha256_arquivo(ARQ_DESVIO),
            "script_sha256": K.sha256_arquivo(Path(__file__)),
            "especificidade_v1_sha256": K.sha256_arquivo(Path(E1.__file__)),
            "mapa_v1_sha256": K.sha256_arquivo(ARQ_MAPA_V1),
            "pool_treino_elegivel": len(pool), "excluidos_pela_amostra_v1": n_excl,
            "tamanho_quartis": dict(sorted(tamanhos.items())),
            "peso_por_quartil": {q: tamanhos[q] / N_POR_QUARTIL for q in (1, 2, 3, 4)},
            "distancia_minima_repeticao": min(dist), "itens": itens}
    ARQ_MAPA.parent.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA)
    doc_dir = Path(a.doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    palavras = _documento(doc_dir / DOC, doc_dir / RESPOSTAS, itens, selo,
                          "Rotulagem manual (calibração v2) — o bullet é GENÉRICO ou ESPECÍFICO?")
    print(json.dumps({"itens": len(itens), "repetidos": len(origem),
                      "distancia_minima_repeticao": min(dist), "pool_elegivel": len(pool),
                      "excluidos_v1": n_excl, "documento": str(doc_dir / DOC),
                      "palavras_documento": palavras, "respostas": str(doc_dir / RESPOSTAS),
                      "mapa": str(ARQ_MAPA), "selo": selo}, ensure_ascii=False))


def _rotulos_base(mapa: dict, caminho: Path) -> dict[str, int]:
    """Rótulo de cada item DISTINTO (o da 1ª ocorrência), por id_bullet."""
    itens = mapa["itens"]
    rot = E1.ler_rotulos(caminho, [i["id"] for i in itens])
    return {i["id_bullet"]: rot[i["id"]] for i in itens if not i["repete"]}


def cmd_lote_extra(a) -> None:
    """Contingência pré-registrada. Antes de qualquer limiar; só conta os E."""
    if ARQ_LIMIARES.exists():
        raise SystemExit("os limiares já foram fixados: o lote extra vem ANTES")
    mapa = K.ler_json(ARQ_MAPA)
    base = _rotulos_base(mapa, Path(a.rotulos))
    n_e = sum(1 for y in base.values() if y == 0)
    if n_e >= MIN_E_DISTINTOS:
        raise SystemExit(f"{n_e} E distintos (≥ {MIN_E_DISTINTOS}): a calibração tem poder, "
                         f"sem lote extra")
    split = K.ler_json(a.split)
    ref = ler_referencia()
    if K.sha256_arquivo(ARQ_REF) != mapa["referencia_sha256"]:
        raise SystemExit("a referência mudou desde o sorteio")
    pool, _ = pool_elegivel(ref, split)
    filmes_ref = sorted({r["slug"] for r in ref})
    vocab = E1.vocabulario_das_reviews(filmes_ref)
    valores = [E1.m_anc(r["texto"], r["slug"], vocab, filmes_ref) for r in pool]
    quartil = _quartis(pool, valores)
    del valores
    ja = set(base)
    rng = random.Random(SEMENTE_EXTRA)
    tam_frame = collections.Counter(quartil[r["id_bullet"]] for r in pool if r["id_bullet"] not in ja)
    sorteio = []
    for q in (1, 2, 3, 4):
        ids = sorted(r["id_bullet"] for r in pool
                     if quartil[r["id_bullet"]] == q and r["id_bullet"] not in ja)
        sorteio += [{"id_bullet": i, "quartil_anc": q}
                    for i in rng.sample(ids, EXTRA_POR_QUARTIL_ANC[q])]
    rng.shuffle(sorteio)
    por_id = {r["id_bullet"]: r for r in ref}
    itens = [{"id": f"X{n:02d}", **{k: por_id[x["id_bullet"]][k]
                                    for k in ("id_bullet", "slug", "bucket", "i", "tema",
                                              "exemplo", "texto")},
              "quartil_anc": x["quartil_anc"], "repete": False}
             for n, x in enumerate(sorteio, 1)]
    extra = {"gerado_por": "scripts/finetune/especificidade_bullet.py lote-extra",
             "semente": SEMENTE_EXTRA, "e_distintos_na_calibracao": n_e,
             "mapa_calibracao_sha256": K.sha256_arquivo(ARQ_MAPA),
             "rotulos_calibracao_sha256": K.sha256_arquivo(Path(a.rotulos)),
             "script_sha256": K.sha256_arquivo(Path(__file__)),
             "por_quartil_anc": EXTRA_POR_QUARTIL_ANC,
             "frame_por_quartil_anc": dict(sorted(tam_frame.items())),
             # quartil de M-anc de TODO o pool elegível: entra nos pesos de inclusão
             "quartil_anc_do_pool": quartil, "itens": itens}
    ARQ_MAPA_EXTRA.write_text(json.dumps(extra, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA_EXTRA)
    doc_dir = Path(a.doc_dir)
    palavras = _documento(doc_dir / DOC_EXTRA, doc_dir / RESPOSTAS_EXTRA, itens, selo,
                          "Rotulagem manual (calibração v2, lote extra) — GENÉRICO ou ESPECÍFICO?")
    print(json.dumps({"e_distintos": n_e, "itens": len(itens), "documento": str(doc_dir / DOC_EXTRA),
                      "palavras_documento": palavras, "mapa": str(ARQ_MAPA_EXTRA), "selo": selo},
                     ensure_ascii=False))


def cmd_medir(a) -> None:
    """Calibração: SÓ depois dos rótulos. Congela limiares e o M-comb."""
    if ARQ_LIMIARES.exists():
        raise SystemExit(f"{ARQ_LIMIARES} já existe: o limiar é escolhido UMA vez")
    mapa = K.ler_json(ARQ_MAPA)
    if K.sha256_arquivo(ARQ_REF) != mapa["referencia_sha256"]:
        raise SystemExit("a referência mudou desde o sorteio")
    itens = mapa["itens"]
    rot = E1.ler_rotulos(Path(a.rotulos), [i["id"] for i in itens])
    rep = [i for i in itens if i["repete"]]
    concord = sum(rot[i["id"]] == rot[i["repete_de"]] for i in rep) / len(rep)
    base = {i["id_bullet"]: i for i in itens if not i["repete"]}
    y = {b: rot[i["id"]] for b, i in base.items()}
    ref = ler_referencia()
    split = K.ler_json(a.split)
    enc = E1._encoder()
    D = disp(ref, enc)
    extra = K.ler_json(ARQ_MAPA_EXTRA) if ARQ_MAPA_EXTRA.exists() else None
    n_e = sum(1 for v in y.values() if v == 0)
    if n_e < MIN_E_DISTINTOS and extra is None:
        raise SystemExit(f"{n_e} E distintos (< {MIN_E_DISTINTOS}): calibração SEM PODER — "
                         f"rode `lote-extra` e rotule antes de fixar limiares")
    if extra is None:
        w = {b: mapa["peso_por_quartil"][str(i["quartil_disp"])] for b, i in base.items()}
    else:
        rot_x = E1.ler_rotulos(Path(a.rotulos_extra), [i["id"] for i in extra["itens"]])
        for i in extra["itens"]:
            base[i["id_bullet"]] = i
            y[i["id_bullet"]] = rot_x[i["id"]]
        # π1 precisa do quartil de M-disp de todos os itens: recalculado no pool elegível,
        # com a mesma regra do sorteio (o resultado reproduz `quartil_disp` da 1ª amostra)
        pool, _ = pool_elegivel(ref, split)
        vd = D.medir([r["texto"] for r in pool], [r["slug"] for r in pool])
        qd = _quartis(pool, vd)
        del vd
        for b, i in base.items():
            if "quartil_disp" in i:
                assert qd[b] == i["quartil_disp"], "quartil de M-disp não reproduz o sorteio"
        tam_d = {int(q): n for q, n in mapa["tamanho_quartis"].items()}
        qa = extra["quartil_anc_do_pool"]
        frame = {int(q): n for q, n in extra["frame_por_quartil_anc"].items()}
        n_x = {int(q): n for q, n in extra["por_quartil_anc"].items()}
        w = {}
        for b in base:
            p1 = N_POR_QUARTIL / tam_d[qd[b]]
            p2 = n_x[qa[b]] / frame[qa[b]]
            w[b] = 1 / (p1 + (1 - p1) * p2)
    ids = sorted(base)
    textos = [base[b]["texto"] for b in ids]
    filmes = [base[b]["slug"] for b in ids]
    md = D.medir(textos, filmes)
    filmes_ref = sorted({r["slug"] for r in ref})
    vocab = E1.vocabulario_das_reviews(filmes_ref)
    ma = [E1.m_anc(t, f, vocab, filmes_ref) for t, f in zip(textos, filmes)]
    yy = [y[b] for b in ids]
    ww = [w[b] for b in ids]
    s_disp, s_anc = md, [-x for x in ma]          # orientação FIXA: score alto = G
    comb = E1.logistica([[d, x] for d, x in zip(md, ma)], yy, ww)
    s_comb = [E1.prob_logistica(comb, [d, x]) for d, x in zip(md, ma)]
    out = {"rotulos_sha256": K.sha256_arquivo(Path(a.rotulos)), "n": len(ids),
           "n_G": sum(yy), "n_E": len(yy) - sum(yy), "lote_extra": extra is not None,
           "consistencia_dono": round(concord, 3), "n_repetidos": len(rep),
           "e5": truncamento(textos, enc), "medidas": {}}
    for nome, s in (("M-disp", s_disp), ("M-anc", s_anc), ("M-comb", s_comb)):
        out["medidas"][nome] = {"auc_calibracao": round(E1.auc_ponderada(s, yy, ww), 4),
                                **E1.youden(s, yy, ww)}
    out["medidas"]["M-comb"]["modelo"] = comb
    out["orientacao"] = "score alto = G; M-anc entra com sinal trocado"
    ARQ_LIMIARES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    ap.add_argument("--doc-dir", default=str(DOC_DIR_PADRAO),
                    help="pasta do documento cego (fora do git)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("referencia")
    sub.add_parser("amostrar-calibracao")
    x = sub.add_parser("lote-extra")
    x.add_argument("--rotulos", default=str(DOC_DIR_PADRAO / RESPOSTAS))
    m = sub.add_parser("medir")
    m.add_argument("--rotulos", default=str(DOC_DIR_PADRAO / RESPOSTAS))
    m.add_argument("--rotulos-extra", default=str(DOC_DIR_PADRAO / RESPOSTAS_EXTRA))
    a = ap.parse_args()
    if a.cmd in ("lote-extra", "medir") and a.doc_dir != str(DOC_DIR_PADRAO):
        d = Path(a.doc_dir)
        if a.rotulos == str(DOC_DIR_PADRAO / RESPOSTAS):
            a.rotulos = str(d / RESPOSTAS)
        if a.cmd == "medir" and a.rotulos_extra == str(DOC_DIR_PADRAO / RESPOSTAS_EXTRA):
            a.rotulos_extra = str(d / RESPOSTAS_EXTRA)
    {"referencia": cmd_referencia, "amostrar-calibracao": cmd_amostrar_calibracao,
     "lote-extra": cmd_lote_extra, "medir": cmd_medir}[a.cmd](a)


if __name__ == "__main__":
    main()
