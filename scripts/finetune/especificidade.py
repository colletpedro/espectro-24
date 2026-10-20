"""Fase 1 — medida de ESPECIFICIDADE do título do bullet, por código (sem LLM).

Definição (do dono, uma linha): GENÉRICO = o título caberia, sem mudança, em
bullets de muitos filmes diferentes; ESPECÍFICO = só faz sentido para este
filme ou para poucos. A unidade é o TÍTULO do bullet (`tema`).

Protocolo pré-registrado: `finetune/especificidade/PROTOCOLO.md` (commit
próprio, ANTES do documento de rotulagem).

Medidas (forma fixa, sem ajuste fino):
- **M-disp** (dispersão entre filmes; ALTO = genérico). e5
  (`multilingual-e5-base`, prefixo `query: ` nos dois lados), cosseno corrigido
  pelo viés do título de referência como no juiz: s(t,u) = cos(t,u) − d_F(u),
  com d_F(u) = média de cos(v,u) sobre a referência fora do filme de u e do
  filme F do item. Para cada OUTRO filme G: s_G = máx_{u∈G} s(t,u). M-disp =
  média dos K_DISP = 10 maiores s_G.
- **M-anc** (ancoragem lexical; ALTO = específico). Palavras de conteúdo do
  título (minúsculas, sem acento, ≥ 4 letras, fora das stopwords): para cada
  uma, idf(w) = ln((N+1)/(df(w)+1)), com N = filmes da referência fora de F e
  df(w) = quantos deles têm w nas reviews analisadas; M-anc = máx_w de
  presente_F(w)·idf(w), onde presente_F(w) = 1 se w aparece nas reviews
  analisadas do próprio filme F (0 se o título não tem palavra de conteúdo).
- **M-comb**: regressão logística (ponderada pelos estratos) com exatamente
  M-disp e M-anc, padronizados.

Toda medida é calculada contra a REFERÊNCIA congelada
(`finetune/especificidade/referencia.jsonl`: títulos publicados de treino e
validação), sempre sem o próprio filme do item. Nenhum filme de teste, nenhuma
saída de modelo na referência.

Subcomandos:
    referencia            grava a referência e o sha256
    amostrar-calibracao   80 títulos de TREINO (20 por quartil de M-disp no pool
                          de treino) + 10 repetidos; documento cego FORA do git,
                          respostas em branco, mapa com selo — sem exibir medida
    selecionar-validacao  os 5 filmes de TREINO para a geração do modelo base
    medir                 (depois dos rótulos) limiar por Youden ponderado,
                          M-comb, consistência do dono; congela em limiares.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _guarda  # noqa: E402,F401
import comum as K  # noqa: E402

DIR = K.FINETUNE_DIR / "especificidade"
ARQ_REF = DIR / "referencia.jsonl"
ARQ_PROTOCOLO = DIR / "PROTOCOLO.md"
ARQ_MAPA_CAL = DIR / "mapa" / "calibracao_mapa.json"
ARQ_VAL_FILMES = DIR / "validacao_filmes.json"
ARQ_LIMIARES = DIR / "limiares.json"
DOC_DIR = K.RAIZ / "docs" / "arquivo-de-estudos" / "finetune-fase1"
DOC = DOC_DIR / "rotulagem_calibracao.md"
RESPOSTAS = DOC_DIR / "rotulos_calibracao.csv"

DEFINICAO = ("GENÉRICO (G) = o título caberia, sem mudança, em bullets de muitos filmes "
             "diferentes; ESPECÍFICO (E) = só faz sentido para este filme ou para poucos.")
K_DISP = 10
SEMENTE_CAL = 20261021
SEMENTE_VAL = 20261022
N_POR_QUARTIL = 20
N_REPETIDOS = 10
DIST_MIN_REPETIDO = 40          # posições entre o original e a repetição
N_FILMES_GERACAO = 5
MIN_LETRAS = 4
STOPWORDS = set("""
a o os as um uma uns umas de do da dos das e em no na nos nas por para com sem sobre
entre que se ao aos à às ou mas mais menos muito muita muitos muitas pouco pouca
este esta estes estas esse essa esses essas isso isto aquele aquela seu sua seus suas
como quando onde ate até pelo pela pelos pelas tambem também ainda apenas nao não
filme filmes obra the and of to in is for with on are as this that by from or an its
""".split())


# ---------------------------------------------------------------------------
# referência
# ---------------------------------------------------------------------------

def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def palavras_de_conteudo(titulo: str) -> list[str]:
    toks = re.findall(r"[^\W\d_]+", _sem_acento(titulo))
    return sorted({t for t in toks if len(t) >= MIN_LETRAS and t not in STOPWORDS})


def montar_referencia(split: dict) -> list[dict]:
    excl = {(x["slug"], x["bucket"]) for x in split.get("buckets_excluidos", [])}
    fora = []
    for conj in ("treino", "validacao"):
        for slug in sorted(split[conj]):
            assert slug not in split["teste"] and slug not in K.EXCLUIR_FILMES
            doc = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
            for b in doc["buckets"]:
                if (slug, b["bucket"]) in excl:
                    continue
                for i, t in enumerate(b.get("temas") or []):
                    fora.append({"id_titulo": f"{slug}|{b['bucket']}|{i}", "slug": slug,
                                 "bucket": b["bucket"], "i": i, "tema": t["tema"],
                                 "conjunto": conj})
    return fora


def ler_referencia() -> list[dict]:
    return [json.loads(l) for l in ARQ_REF.read_text(encoding="utf-8").split("\n") if l.strip()]


# ---------------------------------------------------------------------------
# M-disp
# ---------------------------------------------------------------------------

class Disp:
    """M-disp contra a referência. `queries` do e5 com cache."""

    def __init__(self, ref: list[dict], encoder):
        import numpy as np
        self.np, self.enc, self.ref = np, encoder, ref
        self.filme = np.array([r["slug"] for r in ref])
        self.R = self._q([r["tema"] for r in ref])               # (n, d)
        S = self.R @ self.R.T
        self.S = S
        self.filmes = sorted(set(self.filme))
        self.idx = {f: np.where(self.filme == f)[0] for f in self.filmes}
        # soma por coluna u das similaridades vindas de cada filme
        self.soma_por_filme = {f: S[self.idx[f]].sum(axis=0) for f in self.filmes}
        self.n_por_filme = {f: len(self.idx[f]) for f in self.filmes}
        self.soma_total = S.sum(axis=0)

    def _q(self, textos):
        v = self.enc.queries(textos)
        return self.np.asarray(v)

    def deslocamento(self, filme_item: str):
        """d_F(u): média de cos(v,u) sobre v fora do filme de u e do filme F."""
        np = self.np
        n = len(self.ref)
        d = np.empty(n)
        for f in self.filmes:
            cols = self.idx[f]
            excl = self.soma_por_filme[f][cols]
            cont = self.n_por_filme[f]
            if filme_item != f and filme_item in self.soma_por_filme:
                excl = excl + self.soma_por_filme[filme_item][cols]
                cont += self.n_por_filme[filme_item]
            d[cols] = (self.soma_total[cols] - excl) / (n - cont)
        return d

    def medir(self, titulos: list[str], filmes: list[str]) -> list[float]:
        np = self.np
        Q = self._q(titulos)
        fora, cache_d = [], {}
        for q, f in zip(Q, filmes):
            if f not in cache_d:
                cache_d[f] = self.deslocamento(f)
            s = self.R @ q - cache_d[f]
            maximos = [s[self.idx[g]].max() for g in self.filmes if g != f]
            maximos.sort(reverse=True)
            fora.append(float(np.mean(maximos[:K_DISP])))
        return fora


# ---------------------------------------------------------------------------
# M-anc
# ---------------------------------------------------------------------------

def vocabulario_das_reviews(slugs) -> dict[str, set[str]]:
    from espectro24.pipeline import amostra_do_bruto
    fora = {}
    for slug in slugs:
        doc = K.ler_json(K.RESULTADO_DIR / f"{slug}.json")
        am = amostra_do_bruto(slug, coleta=doc["coleta"], raiz=K.BRUTO_DIR)
        toks = set()
        for rs in am.values():
            for r in rs:
                toks |= set(re.findall(r"[^\W\d_]+", _sem_acento(r.texto)))
        fora[slug] = toks
    return fora


def m_anc(titulo: str, filme: str, vocab: dict[str, set[str]], filmes_ref: list[str]) -> float:
    outros = [g for g in filmes_ref if g != filme]
    N = len(outros)
    melhor = 0.0
    proprio = vocab.get(filme)
    if proprio is None:
        raise ValueError(f"sem vocabulário de reviews para {filme}")
    for w in palavras_de_conteudo(titulo):
        if w not in proprio:
            continue
        df = sum(1 for g in outros if w in vocab[g])
        melhor = max(melhor, math.log((N + 1) / (df + 1)))
    return melhor


# ---------------------------------------------------------------------------
# estatística ponderada
# ---------------------------------------------------------------------------

def auc_ponderada(score: list[float], y: list[int], w: list[float]) -> float:
    """P(score de um G > score de um E), ponderada; empates contam 1/2."""
    pos = [(s, wi) for s, yi, wi in zip(score, y, w) if yi == 1]
    neg = [(s, wi) for s, yi, wi in zip(score, y, w) if yi == 0]
    num = sum(wp * wn * (1.0 if sp > sn else 0.5 if sp == sn else 0.0)
              for sp, wp in pos for sn, wn in neg)
    return num / (sum(w for _, w in pos) * sum(w for _, w in neg))


def youden(score: list[float], y: list[int], w: list[float]) -> dict:
    """Limiar que maximiza TPR − FPR (ponderados); classifica G se score ≥ limiar."""
    tp_tot = sum(wi for yi, wi in zip(y, w) if yi == 1)
    tn_tot = sum(wi for yi, wi in zip(y, w) if yi == 0)
    melhor = None
    for lim in sorted(set(score)):
        tpr = sum(wi for s, yi, wi in zip(score, y, w) if yi == 1 and s >= lim) / tp_tot
        fpr = sum(wi for s, yi, wi in zip(score, y, w) if yi == 0 and s >= lim) / tn_tot
        j = tpr - fpr
        if melhor is None or j > melhor["J"]:
            melhor = {"limiar": lim, "J": j, "tpr": tpr, "tnr": 1 - fpr,
                      "acuracia_balanceada": (tpr + 1 - fpr) / 2}
    return melhor


def logistica(X: list[list[float]], y: list[int], w: list[float]) -> dict:
    """Regressão logística ponderada (sem penalização), entradas padronizadas."""
    import numpy as np
    from scipy.optimize import minimize
    X = np.asarray(X, float)
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-12
    Z = np.c_[np.ones(len(X)), (X - mu) / sd]
    y, w = np.asarray(y, float), np.asarray(w, float)

    def nll(b):
        z = Z @ b
        return float(np.sum(w * (np.logaddexp(0, z) - y * z)))

    def grad(b):
        p = 1 / (1 + np.exp(-(Z @ b)))
        return Z.T @ (w * (p - y))

    r = minimize(nll, np.zeros(Z.shape[1]), jac=grad, method="BFGS")
    return {"coef": r.x.tolist(), "media": mu.tolist(), "desvio": sd.tolist(),
            "convergiu": bool(r.success)}


def prob_logistica(m: dict, x: list[float]) -> float:
    z = m["coef"][0] + sum(c * (xi - mu) / sd for c, xi, mu, sd
                           in zip(m["coef"][1:], x, m["media"], m["desvio"]))
    return 1 / (1 + math.exp(-z))


# ---------------------------------------------------------------------------
# comandos
# ---------------------------------------------------------------------------

def _git_limpo_e_versionado(p: Path) -> bool:
    rel = str(p.relative_to(K.RAIZ))
    ls = subprocess.run(["git", "-C", str(K.RAIZ), "ls-files", "--error-unmatch", rel],
                        capture_output=True).returncode == 0
    dif = subprocess.run(["git", "-C", str(K.RAIZ), "diff", "--quiet", "HEAD", "--", rel]).returncode
    return ls and dif == 0


def cmd_referencia(a) -> None:
    ref = montar_referencia(K.ler_json(a.split))
    DIR.mkdir(parents=True, exist_ok=True)
    ARQ_REF.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ref),
                       encoding="utf-8")
    c = collections.Counter(r["conjunto"] for r in ref)
    print(json.dumps({"titulos": len(ref), "por_conjunto": c,
                      "filmes": len({r["slug"] for r in ref}),
                      "sha256": K.sha256_arquivo(ARQ_REF)}, ensure_ascii=False))


def _encoder():
    import encoder_e5 as E5
    return E5.Encoder.do_disco()


def cmd_amostrar_calibracao(a) -> None:
    if not _git_limpo_e_versionado(ARQ_PROTOCOLO):
        raise SystemExit(f"{ARQ_PROTOCOLO} não está commitado (ou mudou): o protocolo vem "
                         f"ANTES do documento de rotulagem")
    split = K.ler_json(a.split)
    ref = ler_referencia()
    pool = [r for r in ref if r["conjunto"] == "treino"]
    assert all(r["slug"] in split["treino"] for r in pool)
    disp = Disp(ref, _encoder())
    valores = disp.medir([r["tema"] for r in pool], [r["slug"] for r in pool])
    ordem = sorted(range(len(pool)), key=lambda i: (valores[i], pool[i]["id_titulo"]))
    quartil = {}
    for pos, i in enumerate(ordem):
        quartil[pool[i]["id_titulo"]] = 1 + (4 * pos) // len(pool)
    del valores, ordem                       # nenhum valor sai daqui (só o quartil)
    rng = random.Random(SEMENTE_CAL)
    amostra = []
    tamanhos = collections.Counter(quartil.values())
    for q in (1, 2, 3, 4):
        ids = sorted(r["id_titulo"] for r in pool if quartil[r["id_titulo"]] == q)
        amostra += [{"id_titulo": i, "quartil": q} for i in rng.sample(ids, N_POR_QUARTIL)]
    rng.shuffle(amostra)
    repetir = rng.sample(range(len(amostra)), N_REPETIDOS)
    seq = [dict(x) for x in amostra]
    for k in sorted(repetir):
        # repetição inserida a ≥ DIST_MIN_REPETIDO posições do original
        orig_pos = next(p for p, x in enumerate(seq) if x["id_titulo"] == amostra[k]["id_titulo"]
                        and not x.get("repete"))
        alvo = orig_pos + DIST_MIN_REPETIDO if orig_pos + DIST_MIN_REPETIDO <= len(seq) else max(
            0, orig_pos - DIST_MIN_REPETIDO)
        seq.insert(alvo, {**amostra[k], "repete": True})
    por_id = {r["id_titulo"]: r for r in ref}
    itens = []
    for n, x in enumerate(seq, 1):
        r = por_id[x["id_titulo"]]
        itens.append({"id": f"T{n:02d}", "id_titulo": r["id_titulo"], "slug": r["slug"],
                      "bucket": r["bucket"], "i": r["i"], "tema": r["tema"],
                      "quartil": x["quartil"], "repete": bool(x.get("repete"))})
    origem = {}
    for it in itens:
        if it["repete"]:
            o = next(y for y in itens if y["id_titulo"] == it["id_titulo"] and not y["repete"])
            it["repete_de"] = o["id"]
            origem[it["id"]] = o["id"]
    dist = [abs(int(k[1:]) - int(v[1:])) for k, v in origem.items()]
    if min(dist) < DIST_MIN_REPETIDO:
        raise SystemExit(f"repetição a {min(dist)} posições do original (< {DIST_MIN_REPETIDO})")
    pesos = {q: tamanhos[q] / N_POR_QUARTIL for q in (1, 2, 3, 4)}
    mapa = {"gerado_por": "scripts/finetune/especificidade.py amostrar-calibracao",
            "semente": SEMENTE_CAL, "k_disp": K_DISP,
            "referencia_sha256": K.sha256_arquivo(ARQ_REF),
            "protocolo_sha256": K.sha256_arquivo(ARQ_PROTOCOLO),
            "script_sha256": K.sha256_arquivo(Path(__file__)),
            "pool_treino": len(pool), "tamanho_quartis": dict(sorted(tamanhos.items())),
            "peso_por_quartil": pesos, "distancia_minima_repeticao": min(dist),
            "itens": itens}
    ARQ_MAPA_CAL.parent.mkdir(parents=True, exist_ok=True)
    ARQ_MAPA_CAL.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    selo = K.sha256_arquivo(ARQ_MAPA_CAL)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    L = ["# Rotulagem manual (calibração) — o título do bullet é GENÉRICO ou ESPECÍFICO?", "",
         f"> **{DEFINICAO}**", "",
         f"São {len(itens)} títulos de bullets. Leia só o título. Responda em "
         f"`{RESPOSTAS.name}` (mesma pasta), uma linha por id: `G` ou `E`. "
         "Não deixe em branco — item sem rótulo trava a calibração.", ""]
    for it in itens:
        L += ["---", "", f"**{it['id']}** — {it['tema']}", "", f"{it['id']}: G / E", ""]
    L += ["---", "", f"_Selo do mapeamento (sha256): `{selo}`_", ""]
    DOC.write_text("\n".join(L), encoding="utf-8")
    with open(RESPOSTAS, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["id", "rotulo"])
        for it in itens:
            wr.writerow([it["id"], ""])
    print(json.dumps({"itens": len(itens), "repetidos": len(origem),
                      "distancia_minima_repeticao": min(dist), "documento": str(DOC),
                      "respostas": str(RESPOSTAS), "mapa": str(ARQ_MAPA_CAL), "selo": selo},
                     ensure_ascii=False))


def cmd_selecionar_validacao(a) -> None:
    split = K.ler_json(a.split)
    mapa = K.ler_json(ARQ_MAPA_CAL) if ARQ_MAPA_CAL.exists() else {"itens": []}
    rng = random.Random(SEMENTE_VAL)
    filmes = sorted(rng.sample(sorted(split["treino"]), N_FILMES_GERACAO))
    assert all(f in split["treino"] for f in filmes)
    out = {"semente": SEMENTE_VAL, "filmes_geracao": filmes,
           "regra": "5 filmes de TREINO; os 30 títulos gerados vêm do modelo base escolhido, "
                    "sem treino; os 30 publicados vêm de validação e de títulos de treino "
                    "fora da calibração",
           "titulos_calibracao_excluidos": sorted({i["id_titulo"] for i in mapa["itens"]})}
    ARQ_VAL_FILMES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "titulos_calibracao_excluidos"},
                     ensure_ascii=False))


def ler_rotulos(caminho: Path, ids: list[str]) -> dict[str, int]:
    rot = {}
    for linha in csv.DictReader(open(caminho, encoding="utf-8")):
        v = (linha.get("rotulo") or "").strip().upper()
        if v not in ("G", "E"):
            raise SystemExit(f"{linha.get('id')}: rótulo {v!r} — use G ou E")
        rot[linha["id"].strip()] = 1 if v == "G" else 0
    faltam = [i for i in ids if i not in rot]
    if faltam:
        raise SystemExit(f"{len(faltam)} itens sem rótulo (ex.: {faltam[:3]})")
    return rot


def cmd_medir(a) -> None:
    """Calibração: SÓ depois dos rótulos. Congela limiares e o M-comb."""
    if ARQ_LIMIARES.exists():
        raise SystemExit(f"{ARQ_LIMIARES} já existe: o limiar é escolhido UMA vez")
    mapa = K.ler_json(ARQ_MAPA_CAL)
    if K.sha256_arquivo(ARQ_REF) != mapa["referencia_sha256"]:
        raise SystemExit("a referência mudou desde o sorteio")
    itens = mapa["itens"]
    rot = ler_rotulos(Path(a.rotulos), [i["id"] for i in itens])
    rep = [i for i in itens if i["repete"]]
    concord = sum(rot[i["id"]] == rot[i["repete_de"]] for i in rep) / len(rep)
    base = [i for i in itens if not i["repete"]]
    ref = ler_referencia()
    disp = Disp(ref, _encoder())
    md = disp.medir([i["tema"] for i in base], [i["slug"] for i in base])
    filmes_ref = sorted({r["slug"] for r in ref})
    vocab = vocabulario_das_reviews(filmes_ref)
    ma = [m_anc(i["tema"], i["slug"], vocab, filmes_ref) for i in base]
    y = [rot[i["id"]] for i in base]
    w = [mapa["peso_por_quartil"][str(i["quartil"])] for i in base]   # chaves viram texto no JSON
    # orientação FIXA: score alto = genérico (G = 1)
    s_disp, s_anc = md, [-x for x in ma]
    comb = logistica([[d, x] for d, x in zip(md, ma)], y, w)
    s_comb = [prob_logistica(comb, [d, x]) for d, x in zip(md, ma)]
    out = {"rotulos_sha256": K.sha256_arquivo(Path(a.rotulos)), "n": len(base),
           "n_G": sum(y), "consistencia_dono": round(concord, 3), "n_repetidos": len(rep),
           "medidas": {}}
    for nome, s in (("M-disp", s_disp), ("M-anc", s_anc), ("M-comb", s_comb)):
        out["medidas"][nome] = {"auc_calibracao": round(auc_ponderada(s, y, w), 4),
                                **youden(s, y, w)}
    out["medidas"]["M-comb"]["modelo"] = comb
    out["orientacao"] = "score alto = G; M-anc entra com sinal trocado"
    ARQ_LIMIARES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=K.FINETUNE_DIR / "split.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("referencia")
    sub.add_parser("amostrar-calibracao")
    sub.add_parser("selecionar-validacao")
    m = sub.add_parser("medir")
    m.add_argument("--rotulos", default=str(RESPOSTAS))
    a = ap.parse_args()
    {"referencia": cmd_referencia, "amostrar-calibracao": cmd_amostrar_calibracao,
     "selecionar-validacao": cmd_selecionar_validacao, "medir": cmd_medir}[a.cmd](a)


if __name__ == "__main__":
    main()
