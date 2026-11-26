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

    novo = None
    tentativas = []
    for i in range(max_tentativas):
        sistema_i = system if i == 0 else system + (
            "\n\nREFORÇO — a resposta anterior não passou nas validações (JSON, idioma, aspas, "
            "quantidade vaga ou palavras coladas). Refaça com atenção à grafia e SEM nenhum evento da trama.")
        raw = chamar(sistema_i, user, DS)
        try:
            d = S._parse_llm_json(raw)
            exemplo = str(d["exemplo_parafraseado"])
            assert str(d.get("tema", tema_nome)).strip() == tema_nome
        except Exception as e:  # noqa: BLE001
            tentativas.append({"resposta": raw[:300], "recusada": f"json: {type(e).__name__}"})
            continue
        limpo, aspas = S._remover_aspas(exemplo)
        g = S.reescrever_quantidade(limpo)
        texto = g.texto
        motivo = None
        if g.residual or S.tem_quantidade(texto):
            motivo = "quantidade_pendente"
        elif not S._idioma_e_pt_br(texto):
            motivo = "idioma"
        elif not texto.strip():
            motivo = "vazio"
        elif texto.strip() == antigo.strip():
            motivo = "igual_ao_anterior"
        tentativas.append({"exemplo": texto, "aspas_removidas": aspas, "recusada": motivo})
        if motivo is None:
            novo = (texto, aspas)
            break
    assert novo is not None, f"{slug}/{bucket_nome}/{tema_nome}: nenhuma tentativa passou: {tentativas}"
    texto, aspas = novo

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


def regenerar_bucket(out: Path, slug: str, bucket_nome: str, *, max_tentativas: int = 3) -> dict:
    """Refaz a síntese de UM bucket e o resto do documento que depende dele.

    A síntese usa `synthesize_bucket` (mesma função, mesmo prompt, mesmo modelo); os outros
    buckets entram como já gerados. Distribuição, eixos (rotulagem) e condições são refeitos
    pelo montador, porque os temas do bucket entram nas três.
    """
    import etapa2_featherless as E2
    from espectro24 import condicoes as C
    from espectro24 import synthesize as S
    from espectro24.config import BEST_OF_N
    from espectro24.montagem_offline import montar_documento
    from espectro24.validacao_publicado import validar_publicado
    import importar_manual as IM
    import publicar_condicoes as PC

    IPP.definir_out(out)
    IPP.ambiente()
    from espectro24 import featherless as F
    F.sessao_ambiente()
    IPP.conferir_invariantes()

    p = IPP.OUT / slug
    doc_antigo = IPP.ler(p / "bullets.json")
    reg_ant = {b["bucket"]: b for b in doc_antigo["buckets"]}
    chamadas = E2.Chamador(p, slug)
    cons = p / "classificacao" / "consenso_verificado.jsonl"
    meta = IPP.ler(ROOT / "dados" / "bruto" / slug / "meta.json")

    # a ficha é a mesma da geração anterior
    ficha = doc_antigo["ficha"]

    # nova síntese SÓ do bucket pedido: o cache `chamadas/` devolve idêntico o que já foi
    # gerado dos outros; para o bucket pedido, um `variante` no sistema muda a chave e força
    # nova chamada (o conteúdo do prompt de síntese não muda).
    chamar_base = chamadas.texto("sintese")
    cont = {"n": 0}

    def chamar_variante(system, user, model):
        cont["n"] += 1
        return chamar_base(system + f"\n\n(nova geração do bucket — tentativa {cont['n']})", user, model)

    def sintese(b):
        if b.nome != bucket_nome:
            # reaplica o que já foi gerado (sem chamada de LLM)
            from espectro24.montagem_offline import aplicar_sintese
            return aplicar_sintese(b, reg_ant[b.nome], reg_ant[b.nome].get("quantidade_fallback"))
        return S.synthesize_bucket(b, client_call=chamar_variante, model=DS, provider="featherless")

    rel = str(cons.relative_to(ROOT))
    doc = montar_documento(
        slug, bruto_raiz=ROOT / "dados" / "bruto", consenso_path=cons, sintese=sintese, ficha=ficha,
        rotular=chamadas.texto("rotulagem"), modelo_rotulagem=DS,
        proveniencia_sintese={"provider": "featherless", "modelo": DS},
        fonte_registrada=rel, classificacao_rotulo=DS)
    return {"doc": doc, "p": p, "meta": meta, "chamadas": chamadas, "doc_antigo": doc_antigo}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("exemplo")
    a1.add_argument("slug"), a1.add_argument("bucket"), a1.add_argument("tema")
    a = ap.parse_args()
    if a.cmd == "exemplo":
        print(json.dumps(regenerar_exemplo(a.out, a.slug, a.bucket, a.tema), ensure_ascii=False, indent=2))
