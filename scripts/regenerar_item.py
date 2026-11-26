"""Regenera UM item de um filme já gerado (nada é editado à mão) — 2026-11-26.

    python scripts/regenerar_item.py --out DIR exemplo  <slug> <bucket> "<tema>"
    python scripts/regenerar_item.py --out DIR bucket   <slug> <bucket>
    python scripts/regenerar_item.py --out DIR condicao <slug> <TEMA_ID>

`--out` é a pasta de execução do filme (`<out>/<slug>/bullets.json`, `estado.json`,
`condicoes/`), a mesma da regeneração R2; o livro-caixa é o da própria pasta.

* `exemplo`: o defeito está no TEXTO de um único `exemplo_parafraseado` (ex.:
  "filmepara", palavras coladas, que nenhum validador pega). Reescreve SÓ esse campo, com o
  mesmo modelo, o prompt de síntese do bucket (`build_system_prompt` + a MESMA mensagem
  de usuário, as reviews do bucket) e um reforço de item. O tema, as menções e todos os
  outros temas ficam como estão. Passa pelas mesmas transformações da síntese
  (`_remover_aspas`, guarda de quantidade) e pelos mesmos testes (`_idioma_e_pt_br`).
* `bucket`: refaz a síntese de UM bucket (`synthesize_bucket`, a mesma função) e depois as
  etapas que dependem dele (distribuição, eixos/rotulagem, condições), com o mesmo
  montador. Os outros dois buckets entram do que já foi gerado.
* `condicao`: reescreve só a condição de um tema (`tema_origem`), pelo retry direcionado
  do estágio de condições (mesmo prompt de sistema e mesmo briefing), e a revalida.

Cada execução fica registrada em `estado.json` → `itens_regerados` (antes/depois). Não
toca `dados/publicados.json`, `frontend/` nem `resultado/`.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

import importacao_ponta_a_ponta as IPP  # noqa: E402

DS = IPP.DS

_REFORCO_ITEM = """

TAREFA ESTREITA — nesta resposta você NÃO refaz a análise do bucket. Os temas e as menções já \
estão decididos. Reescreva APENAS o `exemplo_parafraseado` do tema indicado na mensagem do \
usuário, a partir das mesmas reviews, obedecendo TODAS as instruções fixas acima (anti-spoiler: \
nenhum evento da trama, destino de personagem ou final; sem aspas; pt-BR; sem citar quantidades \
vagas). Escreva em português correto, com as palavras separadas por espaço. Responda APENAS \
este JSON puro:
{"tema": "<o mesmo nome de tema>", "exemplo_parafraseado": "<paráfrase>"}"""


def _agora():
    return datetime.now(timezone.utc).isoformat()


def _registrar(p: Path, reg: dict) -> None:
    est = IPP.ler(p / "estado.json")
    est.setdefault("itens_regerados", []).append({**reg, "em_utc": _agora()})
    IPP.salvar(p / "estado.json", est)


def _bucket_do_bruto(slug: str, nome: str):
    from espectro24.prosa_local import _buckets_do_bruto
    meta = IPP.ler(ROOT / "dados" / "bruto" / slug / "meta.json")
    return next(b for b in _buckets_do_bruto(slug, meta, ROOT / "dados" / "bruto") if b.nome == nome)


def _trocar_no_eixos(no, tema: str, antigo: str, novo: str) -> int:
    """Troca `exemplo_parafraseado` (== antigo) do tema nas células de `eixos`."""
    n = 0
    if isinstance(no, dict):
        if no.get("tema") == tema and no.get("exemplo_parafraseado") == antigo:
            no["exemplo_parafraseado"] = novo
            n += 1
        for v in no.values():
            n += _trocar_no_eixos(v, tema, antigo, novo)
    elif isinstance(no, list):
        for v in no:
            n += _trocar_no_eixos(v, tema, antigo, novo)
    return n


REFORCO_RETENTATIVA = (
    "\n\nREFORÇO — a resposta anterior não passou nas validações (JSON, idioma, aspas, "
    "quantidade vaga ou palavras coladas). Refaça com atenção à grafia e SEM nenhum evento da trama.")


class RecusaDeItem(AssertionError):
    """Nenhuma tentativa passou nas validações: nada foi gravado."""


def reescrever_exemplo(chamar, system: str, user: str, tema_nome: str, antigo: str, *,
                       max_tentativas: int = 3) -> tuple[str, bool, list]:
    """Pede o novo `exemplo_parafraseado` e aplica as MESMAS transformações e testes da síntese:
    `_remover_aspas`, guarda de quantidade (`reescrever_quantidade`/`tem_quantidade`) e
    `_idioma_e_pt_br`; recusa vazio, igual ao anterior, JSON inválido e tema com outro nome.
    A partir da 2ª tentativa o prompt de sistema ganha `REFORCO_RETENTATIVA`. Sem tentativa
    válida levanta `RecusaDeItem` (quem chama não grava nada)."""
    from espectro24 import synthesize as S
    tentativas = []
    for i in range(max_tentativas):
        sistema_i = system if i == 0 else system + REFORCO_RETENTATIVA
        raw = chamar(sistema_i, user, DS)
        try:
            d = S._parse_llm_json(raw)
            exemplo = str(d["exemplo_parafraseado"])
            if str(d.get("tema", tema_nome)).strip() != tema_nome:
                raise ValueError("tema com outro nome")
        except Exception as e:  # noqa: BLE001
            tentativas.append({"resposta": raw[:300], "recusada": f"json: {type(e).__name__}"})
            continue
        limpo, aspas = S._remover_aspas(exemplo)
        g = S.reescrever_quantidade(limpo)
        texto = g.texto
        motivo = None
        if not texto.strip():
            motivo = "vazio"
        elif g.residual or S.tem_quantidade(texto):
            motivo = "quantidade_pendente"
        elif not S._idioma_e_pt_br(texto):
            motivo = "idioma"
        elif texto.strip() == antigo.strip():
            motivo = "igual_ao_anterior"
        tentativas.append({"exemplo": texto, "aspas_removidas": aspas, "recusada": motivo})
        if motivo is None:
            return texto, bool(aspas), tentativas
    raise RecusaDeItem(f"nenhuma tentativa passou: {tentativas}")


def regenerar_exemplo(out: Path, slug: str, bucket_nome: str, tema_nome: str, *, max_tentativas: int = 3) -> dict:
    import etapa2_featherless as E2
    from espectro24 import pipeline as P
    from espectro24 import synthesize as S
    from espectro24.validacao_publicado import validar_publicado

    IPP.definir_out(out)
    IPP.ambiente()
    from espectro24 import featherless as F
    F.sessao_ambiente()
    IPP.conferir_invariantes()

    p = IPP.OUT / slug
    dest = p / "bullets.json"
    doc = IPP.ler(dest)
    bdoc = next(b for b in doc["buckets"] if b["bucket"] == bucket_nome)
    tema = next(t for t in bdoc["temas"] if t["tema"] == tema_nome)
    antigo = tema["exemplo_parafraseado"]

    b = _bucket_do_bruto(slug, bucket_nome)
    am = P.amostra_do_bruto(slug, raiz=ROOT / "dados" / "bruto")
    assert sorted(r.effective_text for r in b.reviews_analisadas) == sorted(r.texto for r in am[bucket_nome]), "amostra do bucket diverge"
    assert len(b.reviews_analisadas) == tema["n_reviews_analisadas"]

    system = S.build_system_prompt(bucket_nome) + _REFORCO_ITEM
    user = (S.build_user_message(b)
            + f"\n\nTema cujo `exemplo_parafraseado` deve ser reescrito: {tema_nome}"
              f" (citado por cerca de {tema['mencoes_aproximadas']} das {tema['n_reviews_analisadas']} reviews).")
    chamadas = E2.Chamador(p, slug)
    chamar = chamadas.texto("sintese")

    try:
        texto, aspas, tentativas = reescrever_exemplo(
            chamar, system, user, tema_nome, antigo, max_tentativas=max_tentativas)
    except RecusaDeItem as e:
        raise RecusaDeItem(f"{slug}/{bucket_nome}/{tema_nome}: {e}") from e

    tema["exemplo_parafraseado"] = texto
    tema["aspas_removidas"] = bool(aspas)
    n_eixos = _trocar_no_eixos(doc.get("eixos"), tema_nome, antigo, texto)
    assert n_eixos >= 1, "o exemplo antigo não aparece em `eixos`"
    # a validação do bucket (mesma de `rodar_filme`) e o doc de volta
    estado = IPP.ler(p / "estado.json")
    estado["validadores_bullets"][bucket_nome] = validar_publicado(bdoc)
    assert estado["validadores_bullets"][bucket_nome]["passa_publicado"], "bucket reprovou nos validadores"
    IPP.salvar(dest, doc)
    IPP.salvar(p / "estado.json", estado)
    _registrar(p, {"tipo": "exemplo", "bucket": bucket_nome, "tema": tema_nome, "antes": antigo,
                   "depois": texto, "celulas_eixos": n_eixos, "tentativas": len(tentativas)})
    IPP.conferir_invariantes()
    return {"antes": antigo, "depois": texto, "tentativas": tentativas, "celulas_eixos": n_eixos}


def _arquivar(p: Path, rotulo: str) -> Path:
    """Guarda o que vai ser substituído em `<filme>/anteriores/<rotulo>/` (nada se perde)."""
    import shutil
    d = p / "anteriores" / (rotulo + "_" + datetime.now(timezone.utc).strftime("%H%M%S"))
    d.mkdir(parents=True, exist_ok=True)
    for nome in ("bullets.json", "estado.json"):
        if (p / nome).exists():
            shutil.copy2(p / nome, d / nome)
    if (p / "condicoes").exists():
        shutil.copytree(p / "condicoes", d / "condicoes")
    return d


def regenerar_bucket(out: Path, slug: str, bucket_nome: str) -> dict:
    """Refaz a síntese de UM bucket (mesma função, mesmo prompt, mesmo modelo) e, como os temas
    do bucket entram na distribuição, nos eixos (rotulagem) e nas condições, o resto do
    documento que depende dele, pelo MESMO caminho de `rodar_filme`.

    Os dois outros buckets saem do cache de chamadas (o mesmo prompt devolve a mesma resposta já
    gravada); só o bucket pedido ganha uma amostra NOVA do modelo: o prompt é idêntico e cada
    chamada do bucket (a primeira, a retentativa de JSON, os reforços) usa um ordinal novo do
    `Chamador`, o mecanismo existente para réplicas idênticas. A classificação não muda.
    """
    import etapa2_featherless as E2

    IPP.definir_out(out)
    p = IPP.OUT / slug
    anterior = _arquivar(p, f"bucket_{bucket_nome}")
    doc_antes = IPP.ler(p / "bullets.json")
    for q in [p / "bullets.json", *(p / "condicoes").glob("*.json")]:
        q.unlink()

    original = E2.Chamador.chamar
    marcador = f"Bucket: {bucket_nome}\n"

    def chamar(self, system, user, model, estagio, max_tokens):
        if estagio == "sintese" and user.startswith(marcador):
            import hashlib
            base = hashlib.sha256(json.dumps([system, user, model, estagio, max_tokens],
                                             ensure_ascii=False).encode()).hexdigest()
            existentes = len(list((self.p / "chamadas").glob(base + "_*.json")))
            self.n[base] = max(self.n[base], existentes)
        return original(self, system, user, model, estagio, max_tokens)

    E2.Chamador.chamar = chamar
    try:
        IPP.rodar_filme(slug)
    finally:
        E2.Chamador.chamar = original
    doc = IPP.ler(p / "bullets.json")
    ant = next(b for b in doc_antes["buckets"] if b["bucket"] == bucket_nome)
    novo = next(b for b in doc["buckets"] if b["bucket"] == bucket_nome)
    outros_iguais = all(
        a["temas"] == b["temas"] for a, b in zip(doc_antes["buckets"], doc["buckets"]) if a["bucket"] != bucket_nome)
    _registrar(p, {"tipo": "bucket", "bucket": bucket_nome, "arquivado_em": str(anterior.relative_to(ROOT)),
                   "temas_antes": [t["tema"] for t in ant["temas"]], "temas_depois": [t["tema"] for t in novo["temas"]],
                   "outros_buckets_inalterados": outros_iguais})
    return {"temas_antes": [(t["tema"], t["exemplo_parafraseado"]) for t in ant["temas"]],
            "temas_depois": [(t["tema"], t["exemplo_parafraseado"]) for t in novo["temas"]],
            "observacao_antes": ant["observacao_geral"], "observacao_depois": novo["observacao_geral"],
            "outros_buckets_inalterados": outros_iguais}


_RETRY_ITEM = (
    "Reescreva SOMENTE a condição listada abaixo, mantendo o mesmo tema de origem e o mesmo lado. "
    "Problema apontado pelo revisor: lida depois do cabeçalho da coluna, a frase NÃO completa o sentido "
    "pretendido. O texto de uma condição de `talvez_evite` precisa dizer o que a pessoa NÃO suportaria "
    "ou o que a desagradaria (um incômodo real descrito pelo tema); nunca algo que ela tolera, aprecia "
    "ou aceita. Mantenha as demais regras (concisão, sem citar trecho, sem trama).")


def regenerar_condicao(out: Path, slug: str, tema_id: str, problema: str | None = None) -> dict:
    """Reescreve UMA condição pelo retry DIRECIONADO do estágio (mesmo sistema, mesmo briefing)."""
    import etapa2_featherless as E2
    from espectro24 import condicoes as C
    import publicar_condicoes as PC

    IPP.definir_out(out)
    IPP.ambiente()
    from espectro24 import featherless as F
    F.sessao_ambiente()
    IPP.conferir_invariantes()
    p = IPP.OUT / slug
    _arquivar(p, f"condicao_{tema_id}")
    doc = IPP.ler(p / "bullets.json")
    cond = IPP.ler(p / "condicoes" / "condicoes.json")
    b = C.montar_briefing(doc)
    idx = b["idx"]
    lado = next(l for l in C.LADOS for t in b["selecao"][l] if t["id"] == tema_id)
    atual = next(c for c in cond[lado] if c["tema_origem"] == tema_id)
    system = C.prompt_de(cond.get("variante"))
    user = C.serializar_briefing(b, variante=cond.get("variante"))
    chamadas = E2.Chamador(p, slug)
    gerar = chamadas.condicoes(DS)
    texto_retry = (_RETRY_ITEM if problema is None else problema)
    tentativas = []
    nova = None
    for i in range(3):
        pedido = (user + "\n\n" + texto_retry + f"\n\n[{tema_id}] ({lado}) \u2192 {atual['texto']}"
                  + ("" if i == 0 else "\n\nA tentativa anterior ainda foi reprovada; escreva com mais cuidado."))
        bruto, uso, _ = gerar(system, pedido)
        ext = C.extrair(bruto)
        cands = [c for l in C.LADOS for c in ext[l] if c["tema_origem"] == tema_id]
        if not cands:
            tentativas.append({"resposta": bruto[:300], "recusada": "sem_condicao_no_json"})
            continue
        c = cands[0]
        flags = C.validar(c, idx)
        tentativas.append({"texto": c["texto"], "flags": flags})
        if not flags:
            nova = c
            break
    assert nova is not None, f"{slug} {tema_id}: nenhuma tentativa passou: {tentativas}"
    t = idx[tema_id]
    for i_, c in enumerate(cond[lado]):
        if c["tema_origem"] == tema_id:
            cond[lado][i_] = {"texto": nova["texto"], "tema_origem": tema_id, "bucket_origem": t["bucket"],
                              "tema_texto": t["tema"], "rotulo_forca": t["rotulo_forca"]}
    IPP.salvar(p / "condicoes" / "condicoes.json", cond)
    estado = IPP.ler(p / "estado.json")
    estado["validadores_condicoes"] = E2.validar_condicoes(doc, cond)
    bloco, n_ret = PC.aplicar_retiradas(slug, cond, doc)
    try:
        estado["condicoes_validar_bloco"] = PC.validar_bloco(slug, bloco, C.indexar(doc))
    except Exception as e:  # noqa: BLE001
        estado["condicoes_validar_bloco"] = {"REPROVADO": f"{type(e).__name__}: {e}"}
    estado["condicoes_retiradas_r13"] = n_ret
    IPP.salvar(p / "condicoes" / "condicoes_publicaveis.json", bloco)
    IPP.salvar(p / "estado.json", estado)
    _registrar(p, {"tipo": "condicao", "tema_origem": tema_id, "lado": lado, "antes": atual["texto"],
                   "depois": nova["texto"], "tentativas": len(tentativas)})
    IPP.conferir_invariantes()
    return {"antes": atual["texto"], "depois": nova["texto"], "tentativas": tentativas,
            "validadores_condicoes": estado["validadores_condicoes"],
            "validar_bloco": estado["condicoes_validar_bloco"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("exemplo")
    a1.add_argument("slug"), a1.add_argument("bucket"), a1.add_argument("tema")
    a2 = sub.add_parser("bucket")
    a2.add_argument("slug"), a2.add_argument("bucket")
    a3 = sub.add_parser("condicao")
    a3.add_argument("slug"), a3.add_argument("tema_id")
    a = ap.parse_args()
    if a.cmd == "bucket":
        print(json.dumps(regenerar_bucket(a.out, a.slug, a.bucket), ensure_ascii=False, indent=2))
    elif a.cmd == "condicao":
        print(json.dumps(regenerar_condicao(a.out, a.slug, a.tema_id), ensure_ascii=False, indent=2))
    if a.cmd == "exemplo":
        print(json.dumps(regenerar_exemplo(a.out, a.slug, a.bucket, a.tema), ensure_ascii=False, indent=2))
