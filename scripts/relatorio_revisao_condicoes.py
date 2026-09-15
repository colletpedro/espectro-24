#!/usr/bin/env python3
"""[piloto de expansão] RELATÓRIO DE REVISÃO DE CONDIÇÕES — um por lote.

**O fluxo, decisão do dono (2026-09-13).** O §0 exige leitura humana de 100%
das condições antes de publicar (garantia 3 da terceira exceção). A 7,7
condições por filme, os ~300 filmes da expansão dariam ~2.300 itens — gargalo
humano que orçamento não resolve. Então: este script gera UM relatório por
lote; o dono passa o relatório, À MÃO e fora do pipeline, por outra IA, que
separa os duvidosos para a leitura dele e confirma o resto. A decisão de
publicar continua sendo do dono.

**O que este script NÃO é, e a razão é histórica.** Não é validador: não
aprova, não reprova, não pontua, não recomenda — organiza e apresenta. Os
validadores não medidos deste projeto já custaram caro (léxico de valência:
precisão 7,7%, removido; detector de spoiler: 15,8%, recusado como
validador). Por isso cada categoria declara, NO PRÓPRIO RELATÓRIO, o que o
detector dela é — exato, heurístico com precisão medida, ou heurístico NÃO
medido — e a pilha "sem categoria" é descrita como o que é: onde nenhum
detector disparou, não onde não há risco.

**Autocontido.** A revisora não tem o repositório e não sabe o que é rótulo
de força, grupo, eixo ou a regra de zero algarismos. As regras vão no topo,
escritas para quem nunca viu o projeto; os parâmetros que o código controla
(faixas do rótulo, teto de palavras) são lidos do código, não redigitados.

**Numeração estável.** `C001`… na ordem canônica (filme, coluna, posição do
tema na seleção do código), independente da ordem em que os arquivos são
lidos; mais a chave `slug · coluna · tema` e uma impressão digital do lote,
para que o `C017` de um lote nunca seja confundido com o de outro.

**Não chama LLM, não toca rede, não escreve em `resultado/`.**

Uso:
    python scripts/relatorio_revisao_condicoes.py --de DIR --lote NOME
      DIR: saída de `gerar_condicoes.py` (um `<slug>.json` por filme)
      saída default: docs/arquivo-de-estudos/revisao-condicoes/RELATORIO_<NOME>.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from espectro24 import condicoes as C  # noqa: E402
from espectro24 import quantificador as Q  # noqa: E402
from espectro24 import veredito as V  # noqa: E402

RESULTADO_DIR = RAIZ / "resultado"
SAIDA_DIR = RAIZ / "docs" / "arquivo-de-estudos" / "revisao-condicoes"

COLUNA = {"vale_a_pena": "Vale a pena se você...",
          "talvez_evite": "Talvez evite se você..."}
ABERTURA = {"vale_a_pena": "Vale a pena se você",
            "talvez_evite": "Talvez evite se você"}
QUEM = {"vale_a_pena": "escrita a partir de quem RECOMENDA (notas altas)",
        "talvez_evite": "escrita a partir de quem NÃO recomenda (notas baixas)"}
_AUTORIA = {C.ORIGEM_MODELO: "IA", C.ORIGEM_HUMANA: "leitura humana",
            None: "IA"}


# ===========================================================================
# Categorias de risco — ORDEM = prioridade de colocação (cada item aparece
# UMA vez, na primeira que o toca; as outras viram "também toca")
# ===========================================================================

CATEGORIAS = [
    {"codigo": "sem_condicao",
     "titulo": "Sem condição publicável",
     "detector": "EXATO — o gerador (ou a leitura humana) DECLAROU que o tema "
                 "não tem condição honesta e citou a regra; não há frase, e o "
                 "código não pôs outro tema no lugar",
     "pergunta": "A recusa procede? DUVIDOSO = existia uma condição honesta "
                 "(a recusa foi atalho, não impossibilidade). É o que impede "
                 "a abstenção de virar caminho sem custo."},
    {"codigo": "descartada",
     "titulo": "Descartada pelo validador automático",
     "detector": "EXATO — o validador existente reprovou a frase; ela NÃO "
                 "seria publicada",
     "pergunta": "O motivo do descarte procede? DUVIDOSO aqui = a frase "
                 "parecia boa e o validador errou (condição boa perdida)."},
    {"codigo": "integridade",
     "titulo": "Tema de origem não bate com o filme publicado",
     "detector": "EXATO — a condição cita um tema cujo texto hoje é outro "
                 "(o filme foi republicado depois de a condição ser gerada)",
     "pergunta": "Não dá para julgar contra um tema que mudou. Aponte como "
                 "DUVIDOSO."},
    {"codigo": "expectativa",
     "titulo": "Tema do eixo `expectativa` (regra R13 — retido, não publica)",
     "detector": "EXATO — o tema foi classificado no eixo `expectativa`",
     "pergunta": "Estes itens estão aqui só para registro: pela regra R13 "
                 "não serão publicados, qualquer que seja o texto."},
    {"codigo": "par_desfeito",
     "titulo": "Par desfeito — o tema que puxou este foi declarado sem "
               "condição",
     "detector": "EXATO — este tema entrou pelo par obrigatório, puxado por "
                 "um tema do outro grupo; esse tema foi declarado sem "
                 "condição publicável, e sem a afirmação que ele contestava "
                 "esta frase sai da coluna e NÃO é publicada",
     "pergunta": "Sair procede? DUVIDOSO = a frase se sustenta sozinha e a "
                 "informação se perde."},
    {"codigo": "par_recusado",
     "titulo": "Par recusado — a objeção do outro grupo ficou sem condição",
     "detector": "EXATO — este tema puxou, pelo par obrigatório, um tema do "
                 "outro grupo sobre o mesmo assunto, e esse tema foi "
                 "declarado sem condição publicável; esta frase é publicada "
                 "SEM a leitura oposta ao lado",
     "pergunta": "Sozinha, esta condição achata a recepção — recomenda (ou "
                 "desaconselha) um traço que o outro grupo contesta, sem que "
                 "a página mostre a objeção? Se achata, DUVIDOSO."},
    {"codigo": "digito",
     "titulo": "Algarismo no texto (regra R4, com a exceção de ano já aplicada)",
     "detector": "EXATO — algarismo na condição, na paráfrase, ou no nome do "
                 "tema fora da forma de ano admitida",
     "pergunta": "Confira se o número compete com os números do código."},
    {"codigo": "spoiler",
     "titulo": "Possível spoiler / exige ter visto o filme (regra R6)",
     "detector": "HEURÍSTICO MEDIDO — palavras de desfecho/revelação ('final', "
                 "'desfecho', 'reviravolta', 'morte', 'revelação'…) no tema, "
                 "na paráfrase ou na condição. Medido sobre 266 condições: "
                 "precisão 15,8% (a maioria dos alarmes é falsa) e pegou 3 dos "
                 "5 spoilers que a leitura humana marcou — ~2 em 5 spoilers "
                 "reais NÃO disparam este detector. Fonte conhecida de alarme "
                 "falso: o marcador de 'clímax' também casa 'clima' ('clima "
                 "opressivo')",
     "pergunta": "Aplique o teste da R6: a frase diz O QUE PROCURAR, ou QUE "
                 "TIPO DE EXPERIÊNCIA é?"},
    {"codigo": "quantidade",
     "titulo": "Paráfrase com quantidade mais forte que o rótulo do código "
               "(regra R5)",
     "detector": "HEURÍSTICO LÉXICO — palavra de quantidade na paráfrase ('a "
                 "maioria', 'muitos', 'vários', 'amplamente', 'parcela "
                 "significativa'…) numa faixa ACIMA do rótulo que o código "
                 "calculou. É padrão conhecido e vem de uma etapa anterior (a "
                 "síntese). O rótulo do código está certo; quem infla é a "
                 "paráfrase. Calibração: nos 35 filmes do catálogo antigo este "
                 "léxico acha 88 de 629 temas (14,0%) com paráfrase `muitos` "
                 "ou acima e código `poucos`/`alguns`; a medição de referência "
                 "achou 80 de 611 (13,1%) sobre o catálogo de então. Precisão "
                 "não medida: 'vários aspectos' dispara e não fala de pessoas",
     "pergunta": "A CONDIÇÃO herdou a inflação (sugere mais gente, ou "
                 "consenso, do que o rótulo diz)? Se não herdou, CONFIRMO."},
    {"codigo": "acionavel",
     "titulo": "Pode não ser acionável por quem não viu o filme (regra R7)",
     "detector": "HEURÍSTICO NÃO MEDIDO — dois sinais de forma: nome próprio "
                 "na condição (quem é?), ou referência a OUTRA obra no tema ou "
                 "na condição ('clássico', 'original', 'remake', 'releitura', "
                 "'versão'…). NÃO pega referência a cena ou personagem sem "
                 "nome — esse caso só a leitura acha",
     "pergunta": "Quem nunca viu o filme (nem a obra citada) consegue saber "
                 "se isto lhe interessa?"},
]
_POR_CODIGO = {c["codigo"]: c for c in CATEGORIAS}
SEM_CATEGORIA = "sem_categoria"


# --- detectores ------------------------------------------------------------

# A régua da R13 na publicação: a categoria `expectativa` daqui é, por
# construção, o que `publicar_condicoes` retém.
_eixos_do_tema = C.eixos_do_tema


def _marcadores_de_spoiler(texto: str) -> list[str]:
    """Os marcadores de `condicoes.risco_de_spoiler` que casam — o MESMO
    léxico, para que a precisão medida dele valha aqui."""
    plano = V._normalizar(texto or "")
    return [m.rstrip("*") for m, r in zip(C._MARCADORES_SPOILER, C._RE_SPOILER)
            if r.search(plano)]


# Expressões de quantidade que a SÍNTESE escreve nas paráfrases, por faixa do
# mapa de `quantificador`. Parte de `briefing.FAIXAS_QUANTIFICADOR`, mais as
# formas que a medição R6 achou nas paráfrases ("amplamente", "parcela
# significativa", "vários").
_QUANTIDADE_POR_FAIXA = {
    "quase todos": ("quase todos", "quase todas", "praticamente todos",
                    "praticamente todas", "quase totalidade", "unanimidade",
                    "unanime", "unanimes", "praticamente sem excecao"),
    "a maioria": ("maioria", "maior parte", "grande parte", "maior parcela",
                  "amplamente", "majoritariamente"),
    "cerca de metade": ("metade", "meio a meio"),
    "muitos": ("muitos", "muitas", "varios", "varias", "diversos", "diversas",
               "inumeros", "inumeras", "boa parte", "parcela significativa",
               "parcela expressiva", "parcela consideravel",
               "numero consideravel", "grande numero"),
    "alguns": ("alguns", "algumas", "uma parte", "parte do", "parte da",
               "parte dos", "parte das", "parte deles", "fatia"),
    "poucos": ("poucos", "poucas", "minoria", "raros", "raras"),
}
_RE_QUANTIDADE = [(faixa, expr, re.compile(rf"(?<![a-z]){re.escape(expr)}(?![a-z])"))
                  for faixa, exprs in _QUANTIDADE_POR_FAIXA.items()
                  for expr in exprs]


def quantidade_na_parafrase(texto: str) -> tuple[str | None, list[str]]:
    """`(faixa mais forte afirmada, expressões achadas)` na paráfrase."""
    plano = V._normalizar(texto or "")
    achados = [(f, e) for f, e, r in _RE_QUANTIDADE if r.search(plano)]
    if not achados:
        return None, []
    faixa = max(achados, key=lambda a: Q.ROTULOS.index(a[0]))[0]
    return faixa, sorted({e for _, e in achados})


_REFERENCIA_EXTERNA = frozenset({
    "classico", "classica", "classicos", "classicas", "original", "originais",
    "remake", "remakes", "releitura", "adaptacao", "comparacao", "comparacoes",
    "versao", "livro", "franquia", "antecessor", "predecessor"})


def _nomes_proprios(texto: str) -> list[str]:
    """Token Capitalizado fora da primeira posição — a mesma fronteira
    TIPOGRÁFICA de `condicoes.palavras_copiaveis`."""
    toks = re.findall(r"[^\W\d_]+", texto or "", flags=re.UNICODE)
    return [w for i, w in enumerate(toks) if i > 0 and w[:1].isupper()]


def _referencias_externas(texto: str) -> list[str]:
    return sorted({w for w in re.findall(r"[a-z]+", V._normalizar(texto or ""))
                   if w in _REFERENCIA_EXTERNA})


def categorizar(item: dict) -> list[tuple[str, str]]:
    """`[(codigo, nota)]` — o que os detectores acharam neste item, na ordem
    de `CATEGORIAS`. Vazio = nenhum detector disparou (NÃO "sem risco")."""
    achou: dict[str, str] = {}
    if item.get("recusa"):
        r = item["recusa"]
        achou["sem_condicao"] = (f"regra `{r['regra']}` — motivo: {r['motivo']}"
                                 f" — autoria: {_AUTORIA[r['origem']]}")
    if item["flags_validador"]:
        achou["descartada"] = "; ".join(
            f"`{f}` — {C._EXPLICACAO.get(f, f)}" for f in item["flags_validador"])
    if item["tema_mudou"]:
        achou["integridade"] = (f"gerada contra \"{item['tema_na_geracao']}\"; "
                                f"o filme publicado hoje diz \"{item['tema']}\"")
    if "expectativa" in item["eixos"]:
        achou["expectativa"] = "tema classificado no eixo `expectativa`"
    if item.get("par_desfeito"):
        achou["par_desfeito"] = (f"puxado por `{item['par_desfeito']}`, que "
                                 "foi declarado sem condição publicável; esta "
                                 "frase NÃO é publicada")
    if item.get("par_recusado"):
        achou["par_recusado"] = (f"puxou `{item['par_recusado']}` (outro "
                                 "grupo, mesmo assunto), que foi declarado sem "
                                 "condição publicável")

    notas = []
    if re.search(r"\d", item["texto"]):
        notas.append("algarismo NA CONDIÇÃO: "
                     + ", ".join(re.findall(r"\d+", item["texto"])))
    if C.algarismos_proibidos_no_tema(item["tema"]):
        notas.append("algarismo no nome do tema fora da forma de ano: "
                     + ", ".join(C.algarismos_proibidos_no_tema(item["tema"])))
    if re.search(r"\d", item["exemplo"] or ""):
        notas.append("algarismo na paráfrase: "
                     + ", ".join(re.findall(r"\d+", item["exemplo"])))
    if notas:
        achou["digito"] = "; ".join(notas)

    no_tema = _marcadores_de_spoiler(item["tema"] + " " + (item["exemplo"] or ""))
    na_cond = _marcadores_de_spoiler(item["texto"])
    if no_tema or na_cond:
        partes = []
        if na_cond:
            partes.append("na condição: " + ", ".join(na_cond))
        if no_tema:
            partes.append("no tema/paráfrase: " + ", ".join(no_tema))
        achou["spoiler"] = "; ".join(partes)

    faixa, exprs = quantidade_na_parafrase(item["exemplo"])
    rot = item["rotulo_forca"]
    if faixa is not None and (rot is None or Q.mais_forte_que(faixa, rot)):
        achou["quantidade"] = (
            f"a paráfrase diz {', '.join(repr(e) for e in exprs)} (faixa "
            f"`{faixa}`); o código diz "
            + (f"`{rot}`" if rot else "nada (amostra pequena: sem rótulo)"))

    nomes = _nomes_proprios(item["texto"])
    refs = _referencias_externas(item["tema"] + " " + item["texto"])
    if nomes or refs:
        partes = []
        if nomes:
            partes.append("nome próprio na condição: " + ", ".join(nomes))
        if refs:
            partes.append("referência a outra obra: " + ", ".join(refs))
        achou["acionavel"] = "; ".join(partes)
    return [(c["codigo"], achou[c["codigo"]]) for c in CATEGORIAS
            if c["codigo"] in achou]


# ===========================================================================
# Itens
# ===========================================================================

def carregar_lote(de: Path, slugs: list[str] | None = None
                  ) -> list[tuple[str, dict | None]]:
    """`[(slug, bloco condicoes)]` de uma saída de `gerar_condicoes.py`."""
    lote = []
    for p in sorted(Path(de).glob("*.json")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if slugs and d["slug"] not in slugs:
            continue
        lote.append((d["slug"], d.get("condicoes")))
    return lote


def _titulo(doc: dict, slug: str) -> str:
    ficha = doc.get("ficha") or {}
    ident = (doc.get("coleta") or {}).get("identidade_letterboxd") or {}
    return ficha.get("titulo") or ident.get("titulo") or slug


def montar_itens(lote, resultado_dir: Path = RESULTADO_DIR) -> list[dict]:
    """Os itens do lote, numerados na ordem CANÔNICA e categorizados.

    Ordem: slug; coluna (`vale_a_pena`, `talvez_evite`); posição do tema na
    seleção do código (`temas_pedidos`). A condição descartada entra na
    posição do tema dela, para que o dono leia a coluna como ela seria.
    """
    itens = []
    for slug, bloco in sorted(lote, key=lambda x: x[0]):
        if not bloco:
            continue
        doc = json.loads((Path(resultado_dir) / f"{slug}.json").read_text(
            encoding="utf-8"))
        idx = C.indexar(doc)
        titulo = _titulo(doc, slug)
        for lado in C.LADOS:
            pedidos = (bloco.get("temas_pedidos") or {}).get(lado) or []
            # A recusa e o par desfeito entram na posição do tema, como a
            # descartada: o dono lê a coluna como ela seria.
            brutos = ([(c, [], "coluna") for c in bloco.get(lado) or []]
                      + [(c, list(c.get("flags") or []), "descartada")
                         for c in bloco.get("descartadas") or []
                         if c.get("lado") == lado]
                      + [(c, [], "recusa")
                         for c in bloco.get("sem_condicao_publicavel") or []
                         if c.get("lado") == lado]
                      + [(c, [], "par_desfeito")
                         for c in bloco.get("par_desfeito") or []
                         if c.get("lado") == lado])

            def chave(par):
                tid = par[0].get("tema_origem") or ""
                return (pedidos.index(tid) if tid in pedidos else len(pedidos),
                        tid, par[0].get("texto") or "")

            for c, flags, tipo in sorted(brutos, key=chave):
                tid = c.get("tema_origem") or ""
                t = idx.get(tid) or {}
                tema_hoje = t.get("tema") or ""
                tema_geracao = c.get("tema_texto") or tema_hoje
                peso = ((bloco.get("peso") or {}).get(lado) or {})
                item = {
                    "slug": slug, "titulo": titulo, "lado": lado,
                    "tema_origem": tid,
                    "texto": c.get("texto") or "",
                    "tema": tema_hoje,
                    "tema_na_geracao": tema_geracao,
                    "tema_mudou": (not t) or tema_geracao != tema_hoje,
                    "exemplo": t.get("exemplo") or "",
                    "rotulo_forca": (c["rotulo_forca"] if "rotulo_forca" in c
                                     else t.get("rotulo_forca")),
                    "mencoes": t.get("mencoes"), "de_n": t.get("de_n"),
                    "freq_pct": t.get("freq_pct"),
                    "como_entrou": ("par obrigatório" if t.get("ordem", 0)
                                    >= C.N_POR_LADO else "base"),
                    "amostra_pequena": bool(t) and (
                        t.get("estado_piso") != "completa"
                        or t.get("modo") == "reduzido"),
                    "peso_texto": peso.get("peso_texto"),
                    "eixos": (_eixos_do_tema(doc, t["bucket"], tema_hoje)
                              if t else []),
                    "flags_validador": flags,
                    "anos_admitidos": C.anos_em_nome_de_tema(tema_hoje),
                    "origem": c.get("origem"),
                    "recusa": ({"regra": c.get("regra"),
                                "motivo": c.get("motivo"),
                                "origem": c.get("origem")}
                               if tipo == "recusa" else None),
                    "efeito_par": (_efeito_no_par(bloco, tid)
                                   if tipo == "recusa" else None),
                    "par_desfeito": (c.get("tema_base")
                                     if tipo == "par_desfeito" else None),
                    "par_recusado": c.get("par_recusado"),
                }
                item["categorias"] = categorizar(item)
                item["categoria"] = (item["categorias"][0][0]
                                     if item["categorias"] else SEM_CATEGORIA)
                itens.append(item)
    for i, it in enumerate(itens, 1):
        it["numero"] = f"C{i:03d}"
    return itens


def impressao_digital(itens: list[dict]) -> str:
    base = [[it["numero"], it["slug"], it["lado"], it["tema_origem"], it["texto"]]
            for it in itens]
    return hashlib.sha256(json.dumps(base, ensure_ascii=False).encode(
        "utf-8")).hexdigest()[:12]


def _efeito_no_par(bloco: dict, tid: str) -> str:
    """O que a recusa do tema `tid` fez com o par obrigatório."""
    marcados = [c.get("tema_origem") for l in C.LADOS
                for c in bloco.get(l) or [] if c.get("par_recusado") == tid]
    desfeitos = [c.get("tema_origem") for c in bloco.get("par_desfeito") or []
                 if c.get("tema_base") == tid]
    partes = []
    if marcados:
        partes.append("o tema que o puxou pelo par obrigatório ("
                      + ", ".join(f"`{m}`" for m in marcados)
                      + ") continua publicado SEM a objeção ao lado — ver "
                        "`par_recusado`")
    if desfeitos:
        partes.append("o tema que ele puxou pelo par obrigatório ("
                      + ", ".join(f"`{d}`" for d in desfeitos)
                      + ") sai da coluna — ver `par_desfeito`")
    return "; ".join(partes) or "nenhum — o tema não formava par"


def saltados(lote) -> list[tuple[str, str, list[str]]]:
    """Os temas pedidos que ficaram em SILÊNCIO — nem publicados, nem
    descartados, nem declarados sem condição, nem desfeitos pelo par."""
    fora = []
    for slug, bloco in sorted(lote, key=lambda x: x[0]):
        for lado in C.LADOS:
            ts = ((bloco or {}).get("temas_saltados") or {}).get(lado) or []
            descartados = {c.get("tema_origem")
                           for chave in ("descartadas",
                                         "sem_condicao_publicavel",
                                         "par_desfeito")
                           for c in (bloco or {}).get(chave) or []
                           if c.get("lado") == lado}
            ts = [t for t in ts if t not in descartados]
            if ts:
                fora.append((slug, lado, ts))
    return fora


# ===========================================================================
# Renderização
# ===========================================================================

def _bandas() -> str:
    partes = []
    for nome, lo, hi, inclusivo in Q.BANDAS_FRACA_PARA_FORTE:
        if nome == "poucos":
            partes.append(f"`{nome}` abaixo de {hi}%")
        elif hi >= 100:
            partes.append(f"`{nome}` de {lo}% em diante")
        else:
            partes.append(f"`{nome}` de {lo}% a {hi}%")
    return "; ".join(partes)


def regras() -> str:
    """O topo do relatório — para quem NUNCA viu o projeto."""
    return f"""\
## 1. Regras — leia antes de julgar qualquer item

Este relatório é para você, revisora, que **não tem acesso ao projeto**. Tudo
o que é preciso para julgar está nesta seção. Julgue pelas regras abaixo, não
pelo senso comum sobre o que seria uma boa recomendação.

### 1.1 O produto

Uma página por filme, para quem **ainda NÃO assistiu** e está decidindo se
assiste. Tudo o que a página diz vem de reviews de usuários do Letterboxd. As
reviews são separadas em três **grupos** pela nota que a pessoa deu: quem
**não recomenda** (notas baixas), o **meio-termo**, e quem **recomenda** (notas
altas). De cada grupo o sistema lê uma amostra de até 40 reviews e extrai
**temas**: o assunto que aparece, com uma paráfrase do que o grupo diz dele.

### 1.2 O bloco sob revisão: as condições

Duas colunas, no topo da página:

    Vale a pena se você...    ← escrita a partir dos temas de quem RECOMENDA
    Talvez evite se você...   ← escrita a partir dos temas de quem NÃO recomenda

Cada **condição** é uma frase curta que completa a abertura. Uma IA escreveu
a frase; **antes** disso, o código escolheu QUAIS temas viram condição, em que
ordem, e com que rótulo de força. A frase só pode dizer, com outras palavras,
o que o tema e a paráfrase já dizem.

**Por que isto exige leitura.** No resto da página o produto só RELATA o que
as pessoas acharam. Aqui ele RECOMENDA — diz ao leitor em que caso assistir.
É uma exceção deliberada, e uma das condições dela é que nenhuma condição vá
ao ar sem leitura.

### 1.3 Os campos de cada item

- **número** (`C017`) e **chave** (`filme · coluna · tema`) — cite o número.
- **condição** — o texto integral, como apareceria na página.
- **tema de origem** — código e nome. `POS-A` é o tema mais citado de quem
  recomenda, `POS-B` o segundo…; `NEG-` o mesmo para quem não recomenda.
- **o que o grupo diz** — a paráfrase de onde a condição tem de sair.
- **rótulo de força (do código)** — quantos do grupo mencionaram o tema:
  menções ÷ reviews lidas, calculado pelo CÓDIGO e mostrado ao lado da
  condição na página. Faixas: {_bandas()}. Onde duas faixas se sobrepõem,
  vale a mais fraca. "sem rótulo" = grupo com amostra pequena, onde o
  código não afirma quantidade nenhuma.
- **peso da coluna** — `~X% das notas`: quanto do filme aquele grupo é,
  pelo histograma de notas. Também escrito pelo código.
- **como entrou** — `base` (entre os {C.N_POR_LADO} temas mais citados do grupo) ou
  `par obrigatório` (entrou porque o outro grupo fala do MESMO assunto, para
  que a página não recomende um traço sem mostrar a objeção a ele).
- **eixo do tema** — cada tema é classificado em um de dez assuntos (ritmo,
  atuação, expectativa…). Aqui só importa para a regra R13.
- **situação no validador** — um validador automático já roda sobre toda
  condição; os que ele reprovou aparecem como `DESCARTADA`, com o motivo.
- **autoria** — `leitura humana` quando a frase (ou a recusa) foi escrita
  pelo dono do produto; sem a marca, foi escrita pela IA.
- **categorias de risco** — o que os detectores deste relatório acharam.
  Ver 1.6: eles NÃO são julgamento.

Números aparecem neste relatório (contagens, percentuais) porque ele é para
você. Na página, quem escreve número é só o código.

### 1.4 As regras — toda condição publicada tem de cumprir TODAS

- **R1 — Âncora e fidelidade.** Nomeia o assunto do SEU tema. Não introduz
  assunto, adjetivo avaliativo, nome de pessoa ou fato de enredo que não
  esteja no tema ou na paráfrase.
- **R2 — Sinal.** Não afirma mais do que o tema. Um EFEITO ("despertou
  curiosidade") não vira APROVAÇÃO; um INCÔMODO não vira TOLERÂNCIA; "bonito
  mas sem tática" não vira só "bonito". Se a paráfrase traz ressalva
  ("embora…", "mas alguns…"), a condição carrega as duas metades — ou não
  existe.
- **R3 — Discriminação.** Se o outro grupo fala do mesmo assunto, a condição
  diz QUAL leitura oferece: "ritmo contemplativo", não só "ritmo lento".
- **R4 — Zero algarismo na condição.** Nenhum número, em nenhuma forma. A
  razão: a página já mostra números escritos pelo código ("~34% das notas");
  um número na frase competiria com eles, e o leitor não distingue "1940" de
  "34%". **Exceção nova, e estreita:** um ANO de quatro algarismos pode
  aparecer no NOME DE UM TEMA ("Comparação com o clássico de 1940") — nunca
  na condição, nunca na paráfrase, nunca como quantidade.
- **R5 — Quantidade é do código.** A condição não escreve "a maioria",
  "muitos", "alguns", "poucos", "metade" nem nada sobre QUANTAS pessoas
  disseram aquilo, e não sugere consenso. O rótulo de força aparece ao lado.
  Atenção a um padrão conhecido: a PARÁFRASE às vezes usa quantidade mais
  forte que o rótulo ("uma parcela significativa" ao lado de `alguns`). O
  rótulo está certo — é contagem; quem infla é a paráfrase, que vem de uma
  etapa anterior. A condição não pode herdar a inflação.
- **R6 — Anti-spoiler.** A condição é para quem não viu. Proibido usar
  desfecho, reviravolta, morte, revelação ou ponto de chegada de um arco como
  motivo para assistir ou evitar — mesmo quando o tema fala disso. **O
  teste:** se a frase diz ao leitor O QUE PROCURAR durante o filme, é
  spoiler; se diz QUE TIPO DE EXPERIÊNCIA ele é, não é. Permitido: dizer que
  o final é aberto ou ambíguo; dizer que existe uma virada. Proibido: dizer o
  que o final contém, ou o EFEITO da virada ("reviravoltas que transformam a
  história").
- **R7 — Acionável por quem não viu.** O leitor precisa conseguir reconhecer
  se aquilo lhe interessa ANTES de assistir. Personagem pelo nome, cena
  específica, "aquele momento" — referência que só faz sentido para quem viu
  — falha.
- **R8 — Qualidade da obra, não perfil do leitor.** Proibido "você é o tipo
  de pessoa que", "pessoas que gostam"; também não é crítica ("o filme tem
  ótima fotografia"). Nomeia a qualidade concreta e deixa o leitor se
  reconhecer. Oposição "X em vez de Y" só quando os DOIS lados estão na
  paráfrase.
- **R9 — Escopo.** Não fala de "os críticos", "o consenso", "o público".
- **R10 — Palavras próprias.** Não copia o tema nem a paráfrase palavra por
  palavra; sem aspas.
- **R11 — Forma.** Até {C.TETO_PALAVRAS} palavras, português do Brasil, começa
  em minúscula e continua a abertura sem repeti-la.
- **R12 — Especificidade.** A maior abstração que a paráfrase sustenta
  INTEIRA: um detalhe de passagem não vira critério central, e subir de
  abstração além do que está escrito é inventar.
- **R13 — O eixo `expectativa` não vira condição.** Temas sobre hype,
  reputação, "superestimado": o objeto deles não é o filme, é a relação do
  público com a fama dele. Decisão editorial vigente: não são publicados.

### 1.5 "Sem condição publicável" é resposta válida

**Publicar menos não é defeito.** Quando um tema não tem condição honesta, a
IA (ou o dono) o DECLARA sem condição, citando a regra que impede — R1, R2,
R6, R12 ou R13 — e um motivo curto. O código **não** põe outro tema no
lugar: a coluna fica mais curta. Uma coluna com duas condições boas é melhor
que uma com cinco onde uma engana.

O custo da recusa é esta leitura: cada recusa é um item numerado, e a
pergunta dela é se existia, sim, uma condição honesta. Recusar não pode
virar atalho.

### 1.6 O que devolver

Para cada item, uma de duas respostas, citando o número:

    CONFIRMO: C001, C002, C004–C009
    DUVIDOSO: C003 — R6 — diz ao leitor que o desfecho é cruel

- **CONFIRMO** — você não achou violação de nenhuma regra.
- **DUVIDOSO** — cite a(s) regra(s) e o motivo em uma frase. O item vai para
  a leitura do dono.

Para itens sem condição publicável, `DESCARTADA`, de `expectativa` e de par
desfeito ou recusado, a pergunta é outra (está no topo de cada seção). Não
reescreva condições e não decida publicação: quem decide é o dono. Na
dúvida, DUVIDOSO.

### 1.7 O que este relatório NÃO faz

Não aprova, não rejeita, não pontua, não recomenda. As categorias de risco
são o que detectores automáticos acharam — alguns exatos, outros aproximados
com precisão conhecida e baixa, um sem medição nenhuma; cada seção diz qual.
**"Sem categoria" quer dizer que nenhum detector disparou, NÃO que o item não
tem risco.** Leia todos os itens contra as regras.
"""


def _item_md(it: dict) -> str:
    rot = it["rotulo_forca"]
    base = (f"{it['mencoes']} de {it['de_n']} = {it['freq_pct']}%"
            if it["mencoes"] is not None and it["de_n"] else "")
    rotulo = (f"`{rot}` ({base})" if rot else
              f"sem rótulo — amostra pequena ({base})" if base else "—")
    tema = f"{it['tema_origem']} — *{it['tema'] or '(tema ausente)'}*"
    if it["anos_admitidos"]:
        tema += (f" (o ano {', '.join(it['anos_admitidos'])} está no nome do "
                 "tema e é admitido pela exceção da R4)")
    coluna = f"{COLUNA[it['lado']]} — {QUEM[it['lado']]}"
    if it["peso_texto"]:
        coluna += f" · {it['peso_texto']}"
    rec = it.get("recusa")
    if rec:
        situacao = "sem frase — declarado sem condição publicável"
    elif it.get("par_desfeito"):
        situacao = "passou, mas SAI da coluna (par desfeito)"
    else:
        situacao = ("passou" if not it["flags_validador"] else
                    "**DESCARTADA** — " + ", ".join(f"`{f}`" for f in
                                                    it["flags_validador"]))
    cats = it["categorias"]
    frase = it["texto"] if not rec else "— *(sem condição publicável)*"
    L = [f"#### {it['numero']} · `{it['slug']}` · "
         f"{'Vale a pena' if it['lado'] == 'vale_a_pena' else 'Talvez evite'}"
         f" · {it['tema_origem']}",
         "",
         f"> **{ABERTURA[it['lado']]}** {frase}",
         ""]
    if rec:
        regras_ = C.regras_da_recusa(rec["regra"])
        L += [f"- **regra da recusa:** `{rec['regra']}` — "
              + "; ".join(C.REGRAS_DE_RECUSA.get(r, "regra fora do conjunto")
                          for r in regras_),
              f"- **motivo (não vai para a página):** {rec['motivo']}",
              f"- **efeito sobre o par:** {it['efeito_par']}"]
    L += [f"- **autoria:** {_AUTORIA.get(it.get('origem'), 'IA')}",
         f"- **chave:** `{it['slug']} · {it['lado']} · {it['tema_origem']}`",
         f"- **filme:** {it['titulo']} (`{it['slug']}`)",
         f"- **coluna:** {coluna}",
         f"- **tema de origem:** {tema}",
         f"- **o que o grupo diz:** {it['exemplo'] or '—'}",
         f"- **rótulo de força (do código):** {rotulo}",
         f"- **como entrou:** {it['como_entrou']}"
         + (" · amostra do grupo PEQUENA" if it["amostra_pequena"] else ""),
         f"- **eixo do tema:** "
         + (", ".join(f"`{e}`" for e in it["eixos"]) or "—"),
         f"- **situação no validador:** {situacao}"]
    if cats:
        L.append("- **categorias de risco:**")
        for cod, nota in cats:
            L.append(f"    - `{cod}` — {nota}")
    else:
        L.append("- **categorias de risco:** nenhum detector disparou")
    return "\n".join(L)


def renderizar(itens: list[dict], lote, *, nome_lote: str, origem: str) -> str:
    fp = impressao_digital(itens)
    n_filmes = len({it["slug"] for it in itens})
    n_desc = sum(1 for it in itens if it["flags_validador"])
    n_rec = sum(1 for it in itens if it.get("recusa"))
    n_desf = sum(1 for it in itens if it.get("par_desfeito"))
    ordem = [c["codigo"] for c in CATEGORIAS] + [SEM_CATEGORIA]
    secao = {c: i for i, c in enumerate(ordem, 1)}
    prim = {c: [it for it in itens if it["categoria"] == c] for c in ordem}
    toca = {c: [it for it in itens if c in dict(it["categorias"])]
            for c in ordem[:-1]}

    L = [f"# Revisão de condições — lote `{nome_lote}`",
         "",
         f"**Impressão digital do lote: `{fp}`** · {len(itens)} itens "
         f"({len(itens) - n_desc - n_rec - n_desf} publicáveis + {n_desc} "
         f"descartados pelo validador"
         + (f" + {n_rec} sem condição publicável" if n_rec else "")
         + (f" + {n_desf} de par desfeito" if n_desf else "")
         + f") · {n_filmes} filmes · insumo: `{origem}`",
         "",
         "*Para o dono:* este arquivo é o insumo da revisora externa — "
         "passe-o INTEIRO, sem cortar a seção 1. Ao trazer a resposta de "
         "volta, cite o lote pela impressão digital e os itens pelo número.",
         "",
         regras(),
         "## 2. Resumo por categoria",
         "",
         "Cada item aparece UMA vez, na primeira categoria da tabela que o "
         "toca; \"tocam\" conta também os que estão em outra seção.",
         "",
         "| seção | categoria | detector | nesta seção | tocam |",
         "|---|---|---|---:|---:|"]
    for i, c in enumerate(CATEGORIAS, 1):
        L.append(f"| 3.{i} | {c['titulo']} | {c['detector'].split(' —')[0]} "
                 f"| {len(prim[c['codigo']])} | {len(toca[c['codigo']])} |")
    L.append(f"| 3.{len(CATEGORIAS) + 1} | Sem categoria de risco | "
             f"nenhum detector disparou | {len(prim[SEM_CATEGORIA])} | — |")
    L += ["", "## 3. Itens, por categoria de risco", ""]
    for i, cod in enumerate(ordem, 1):
        if cod == SEM_CATEGORIA:
            L += [f"### 3.{i} Sem categoria de risco "
                  f"({len(prim[cod])} itens)", "",
                  "Nenhum detector disparou nestes itens. **Isso não quer "
                  "dizer que estão livres de risco** — os detectores de "
                  "spoiler e de acionabilidade deixam passar casos reais "
                  f"(ver 3.{secao['spoiler']} e 3.{secao['acionavel']}). "
                  "Leia contra as regras R1–R13.", ""]
        else:
            c = _POR_CODIGO[cod]
            L += [f"### 3.{i} {c['titulo']} ({len(prim[cod])} itens)", "",
                  f"*Detector:* {c['detector']}.", "",
                  f"*Pergunta desta seção:* {c['pergunta']}", ""]
            outros = [it["numero"] for it in toca[cod] if it["categoria"] != cod]
            if outros:
                L += [f"*Também tocam esta categoria, listados em outra seção:* "
                      f"{', '.join(outros)}.", ""]
        if not prim[cod]:
            L += ["*(nenhum item)*", ""]
        for it in prim[cod]:
            L += [_item_md(it), ""]

    fora = saltados(lote)
    L += ["## Apêndice A — temas pedidos que o modelo não escreveu", "",
          "Informativo: não há frase para julgar. O código pediu uma "
          "condição para estes temas e o modelo SALTOU (a regra de abstenção "
          "permite — saltar é melhor que forçar).", ""]
    if fora:
        for slug, lado, ts in fora:
            L.append(f"- `{slug}` · {COLUNA[lado]} · {', '.join(ts)}")
    else:
        L.append("*(nenhum)*")
    L += ["", "## Apêndice B — índice por filme", ""]
    por_filme: dict[str, list[str]] = {}
    for it in itens:
        por_filme.setdefault(it["slug"], []).append(it["numero"])
    for slug, ns in por_filme.items():
        L.append(f"- `{slug}`: {ns[0]}–{ns[-1]} ({len(ns)} itens)")
    return "\n".join(L).rstrip() + "\n"


def _checar_saida(destino: Path) -> None:
    alvo = destino.resolve()
    proibido = RESULTADO_DIR.resolve()
    if alvo == proibido or proibido in alvo.parents:
        raise SystemExit(f"RECUSADO: --saida aponta para dentro de {proibido}. "
                         "O relatório é material de estudo, fora de resultado/.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--de", required=True,
                    help="diretório de saída de gerar_condicoes.py")
    ap.add_argument("--lote", required=True, help="nome do lote")
    ap.add_argument("--slug", action="append", help="restringe a estes slugs")
    ap.add_argument("--saida", default=None,
                    help="arquivo .md (default: "
                         "docs/arquivo-de-estudos/revisao-condicoes/)")
    args = ap.parse_args()

    destino = (Path(args.saida) if args.saida
               else SAIDA_DIR / f"RELATORIO_{args.lote}.md")
    _checar_saida(destino)
    lote = carregar_lote(Path(args.de), args.slug)
    itens = montar_itens(lote)
    try:
        origem = str(Path(args.de).resolve().relative_to(RAIZ))
    except ValueError:
        origem = str(Path(args.de))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(renderizar(itens, lote, nome_lote=args.lote,
                                  origem=origem), encoding="utf-8")

    print(f"{len(itens)} itens · lote {impressao_digital(itens)} → {destino}")
    for c in CATEGORIAS:
        n_p = sum(1 for it in itens if it["categoria"] == c["codigo"])
        n_t = sum(1 for it in itens if c["codigo"] in dict(it["categorias"]))
        print(f"  {c['codigo']:<12} nesta seção {n_p:3}   tocam {n_t:3}")
    print(f"  {SEM_CATEGORIA:<12} {sum(1 for it in itens if it['categoria'] == SEM_CATEGORIA):3}")


if __name__ == "__main__":
    main()
