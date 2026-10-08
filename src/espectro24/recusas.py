"""Reviews RECUSADAS pelo filtro de conteúdo do provider — fora da amostra.

**Por que existe (2026-09-23, ABERTO.md C22).** No bloco 1 da exceção C22, o
Gemini recusou 9 reviews de forma determinística (`promptFeedback.blockReason:
PROHIBITED_CONTENT`, 36 de 36 tentativas). Review sem classificação fica fora
do consenso, e a guarda C14.8 (`eixos.checar_amostra_classificada`) recusa o
filme, com razão: publicar encolheria o `n` em silêncio. Decisão do dono: NÃO
reduzir o `n` nem afrouxar a guarda — SUBSTITUIR a recusada pela próxima
elegível do mesmo bucket, pela mesma regra determinística da seleção.

**Como.** A recusada entra neste registro e `selecao.selecionar` a trata como
inelegível (`excluir_ids`), no mesmo passo em que já exclui truncada e
spoiler. A cascata, a alocação por nível e a estratificação seguem iguais, e
a vaga vai para a próxima review na ordem de sempre. Os DOIS chamadores de
produção da seleção — `pipeline.run_pipeline` (a publicação) e
`pipeline.amostra_do_bruto` (a amostra de classificação e a guarda C14.8) —
leem este registro, então análise e classificação enxergam a MESMA amostra e
a guarda passa sem mudar uma linha. Se a reserva do bucket esgotar, a seleção
devolve menos de 40: o `n` cai, `reservas_esgotadas` o aponta, e a execução e a
publicação PARAM antes de publicar.

**Escopo.** Só entram aqui reviews dos filmes da exceção C22
(`registrar` recusa as outras). Um filme sem entrada lê `frozenset()`, e a
seleção dele sai byte a byte como antes.

**O viés é declarado, não escondido:** reviews com linguagem explícita saem da
amostra. O registro guarda, por review, o bucket, o motivo e a substituta.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQ_RECUSAS = RAIZ / "resultado" / "votacao-3" / "recusas_conteudo.json"

# Quantas tentativas BLOQUEADAS (e nenhuma ok) confirmam a recusa. Medido no
# bloco 1: o bloqueio foi determinístico (36/36). Duas confirmações — os
# passes 1 e 2 — separam o determinístico de um soluço do provider.
MIN_TENTATIVAS_BLOQUEADAS = 2


def _ler(caminho: Path | None = None) -> dict:
    arq = caminho or ARQ_RECUSAS
    if not arq.exists():
        return {"recusas": []}
    return json.loads(arq.read_text(encoding="utf-8"))


def recusas(caminho: Path | None = None) -> list[dict]:
    return list(_ler(caminho)["recusas"])


def ids_recusados(slug: str, caminho: Path | None = None) -> frozenset[str]:
    """Os ids a EXCLUIR da seleção deste filme. Vazio = seleção de sempre."""
    return frozenset(r["id"] for r in _ler(caminho)["recusas"]
                     if r["slug"] == slug)


def registrar(novas: list[dict], caminho: Path | None = None) -> list[dict]:
    """Acrescenta recusas (idempotente por `(slug, id)`). Cada uma:
    `{slug, bucket, id, provider, modelo, bloqueio, n_tentativas_bloqueadas,
    evidencia}`. Só aceita filmes da exceção C22. Devolve as de fato novas."""
    from . import excecao_c22 as C22
    from .atomico import escrever_atomico

    arq = caminho or ARQ_RECUSAS
    estado = _ler(arq)
    vistos = {(r["slug"], r["id"]) for r in estado["recusas"]}
    acrescentadas = []
    for r in novas:
        C22.exigir_no_escopo([r["slug"]])
        if (r["slug"], r["id"]) in vistos:
            continue
        vistos.add((r["slug"], r["id"]))
        entrada = {**r, "registrada_em": datetime.now(timezone.utc)
                   .isoformat(timespec="seconds"), "substituta": None}
        if "idioma" not in entrada:
            entrada["idioma"] = _idioma_do_bruto(r["slug"], r["id"])
        estado["recusas"].append(entrada)
        acrescentadas.append(entrada)
    if acrescentadas:
        escrever_atomico(arq, json.dumps(estado, ensure_ascii=False, indent=2))
    return acrescentadas


def _idioma_do_bruto(slug: str, rid: str) -> str:
    """A língua provável da review, lida do bruto persistido. Sem o texto
    (teste, bruto ausente): "indeterminado"."""
    try:
        from .bruto import carregar
        _, todas = carregar(slug)
        texto = next((r.texto for r in todas if r.id == rid), None)
    except Exception:  # noqa: BLE001
        texto = None
    return idioma_provavel(texto) if texto else "indeterminado"


def anotar_idiomas(caminho: Path | None = None, refazer: bool = False) -> int:
    """Preenche `idioma` nas recusas registradas antes do campo existir (ou
    em todas, com `refazer`, quando a heurística muda)."""
    from .atomico import escrever_atomico

    arq = caminho or ARQ_RECUSAS
    estado = _ler(arq)
    n = 0
    for r in estado["recusas"]:
        if refazer or "idioma" not in r:
            novo = _idioma_do_bruto(r["slug"], r["id"])
            n += novo != r.get("idioma")
            r["idioma"] = novo
    if n:
        escrever_atomico(arq, json.dumps(estado, ensure_ascii=False, indent=2))
    return n


def anotar_substitutas(slug: str, antes: dict[str, set[str]],
                       depois: dict[str, set[str]],
                       caminho: Path | None = None) -> dict:
    """Grava, em cada recusa do filme ainda sem substituta, QUAL review
    entrou no lugar dela — pareando por bucket, na ordem do registro. Devolve
    `{bucket: {saiu, entrou, n_antes, n_depois}}` para conferência: fora das
    recusadas não pode sair nada, e o que entra tem de ser o mesmo tanto (ou
    menos, se a reserva esgotou)."""
    from .atomico import escrever_atomico

    arq = caminho or ARQ_RECUSAS
    estado = _ler(arq)
    resumo = {}
    for bucket in sorted(set(antes) | set(depois)):
        a, d = antes.get(bucket, set()), depois.get(bucket, set())
        saiu, entrou = sorted(a - d), sorted(d - a)
        resumo[bucket] = {"saiu": saiu, "entrou": entrou,
                          "n_antes": len(a), "n_depois": len(d)}
        fila = list(entrou)
        for r in estado["recusas"]:
            if r["slug"] == slug and r["bucket"] == bucket and r["id"] in saiu \
                    and r.get("substituta") is None:
                r["substituta"] = fila.pop(0) if fila else RESERVA_ESGOTADA
    escrever_atomico(arq, json.dumps(estado, ensure_ascii=False, indent=2))
    return resumo


RESERVA_ESGOTADA = "RESERVA_ESGOTADA"


def reservas_esgotadas(slugs=None, caminho: Path | None = None,
                       incluir_aceitas: bool = False) -> list[dict]:
    """Recusas cujo bucket NÃO teve substituta — o `n` daquele bucket caiu.
    Decisão do dono (2026-09-23): parar e reportar ANTES de publicar. As que o
    dono ACEITOU (`aceitar_n_menor`) não param mais nada, salvo
    `incluir_aceitas`."""
    alvo = set(slugs) if slugs is not None else None
    return [r for r in _ler(caminho)["recusas"]
            if r.get("substituta") == RESERVA_ESGOTADA
            and (alvo is None or r["slug"] in alvo)
            and (incluir_aceitas or not r.get("aceite_n_menor"))]


def aceitar_n_menor(slug: str, bucket: str, decisao: str,
                    caminho: Path | None = None) -> list[dict]:
    """Registra a DECISÃO do dono de publicar o bucket com o `n` menor. O
    aceite fica na própria recusa (quem decidiu, quando, e o texto)."""
    from .atomico import escrever_atomico

    arq = caminho or ARQ_RECUSAS
    estado = _ler(arq)
    aceitas = []
    for r in estado["recusas"]:
        if (r["slug"], r["bucket"]) == (slug, bucket) \
                and r.get("substituta") == RESERVA_ESGOTADA:
            r["aceite_n_menor"] = {
                "decisao": decisao,
                "em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            aceitas.append(r)
    if not aceitas:
        raise ValueError(f"{slug}/{bucket}: nenhuma recusa com reserva esgotada")
    escrever_atomico(arq, json.dumps(estado, ensure_ascii=False, indent=2))
    return aceitas


MOTIVO_DECLARADO = ("review recusada pelo filtro de conteúdo do provider "
                    "(Gemini, {bloqueio}) e excluída da amostra")


def declaracao_do_bucket(slug: str, bucket: str,
                         caminho: Path | None = None) -> dict | None:
    """O que o DADO do filme declara sobre as recusas de um bucket — `None`
    quando não houve nenhuma (todo filme sem recusa sai como antes)."""
    rs = [r for r in _ler(caminho)["recusas"]
          if r["slug"] == slug and r["bucket"] == bucket]
    if not rs:
        return None
    sem = [r for r in rs if r.get("substituta") == RESERVA_ESGOTADA]
    return {
        "motivo": MOTIVO_DECLARADO.format(bloqueio=rs[0].get("bloqueio")),
        "n_recusadas": len(rs),
        "substituidas": [{"recusada": r["id"], "substituta": r["substituta"]}
                         for r in rs if r not in sem],
        "sem_substituta": [{"recusada": r["id"],
                            "consequencia": "n do bucket menor em 1: a "
                                            "reserva do bruto estava esgotada",
                            "aceite_do_dono": (r.get("aceite_n_menor") or {})
                            .get("decisao")} for r in sem],
    }


# --- a LÍNGUA da recusada (2026-09-27, decisão do dono) ---------------------
# O 1º caso sem motivo aparente (`scream`, azerbaijano, sem palavrão nem sexo)
# levantou a hipótese de viés contra LÍNGUA, não só contra crítica ao conteúdo
# sexual. Para ver se há concentração, cada recusa leva a língua PROVÁVEL.
# HEURÍSTICA declarada, sem dependência nova: alfabeto primeiro; em alfabeto
# latino, a língua com mais palavras funcionais distintivas (mínimo 2 e
# vantagem sobre a 2ª). Sem sinal suficiente: "indeterminado".
_ALFABETOS = (("cirilico", "\u0400", "\u04ff"), ("grego", "\u0370", "\u03ff"),
              ("arabe", "\u0600", "\u06ff"), ("hebraico", "\u0590", "\u05ff"),
              ("devanagari", "\u0900", "\u097f"), ("tailandes", "\u0e00", "\u0e7f"),
              ("hangul", "\uac00", "\ud7af"), ("kana", "\u3040", "\u30ff"),
              ("cjk", "\u4e00", "\u9fff"))
_FUNCIONAIS = {
    "en": "the and is was this that with for but not movie film it of to",
    "pt": "que não uma com para mas filme muito isso ele ela por são foi",
    "es": "que una con para pero película muy esto porque los las del es y el lo por esta eso me",
    "fr": "le la les une est pas mais pour avec des qui film très ce",
    "it": "il che non una per con della sono questo molto film ma è",
    "de": "der die das und ist nicht ein eine mit aber auch sehr film",
    "nl": "het een niet maar ook heel dat van",
    "pl": "nie jest się że na jak ale to tak film bardzo co",
    "tr": "bir ve bu çok ama için ile gibi daha film değil",
    "az": "və bu bir çox amma üçün ilə kimi deyə olur heç də",
    "hu": "az és egy hogy nem nagyon volt ez",
    "id": "yang dan ini itu tidak dengan untuk ada film sangat",
}
_FUNCIONAIS = {k: set(v.split()) for k, v in _FUNCIONAIS.items()}


def idioma_provavel(texto: str) -> str:
    import re
    contagem = {}
    for nome, ini, fim in _ALFABETOS:
        contagem[nome] = sum(1 for c in texto if ini <= c <= fim)
    melhor = max(contagem, key=contagem.get)
    if contagem[melhor] >= 5:
        return melhor
    palavras = re.findall(r"[a-zà-ÿğıəşçöüő]+", texto.lower())
    pontos = {k: sum(1 for w in palavras if w in v) for k, v in _FUNCIONAIS.items()}
    ordem = sorted(pontos.items(), key=lambda kv: -kv[1])
    if ordem[0][1] >= 2 and ordem[0][1] > ordem[1][1]:
        return ordem[0][0]
    return "indeterminado"
