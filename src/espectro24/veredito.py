"""[v1.9.21, §3[V]] O VEREDITO — briefing determinístico + LLM para a redação.

**O que o veredito é.** A linha de 1-2 frases no topo de `filme.html`, entre a
ficha e os bullets: a leitura de UMA frase que a tabela "eixo a eixo"
(removida na v1.9.19) pedia ao leitor para fazer de cabeça. Escreve para quem
**ainda não assistiu** e está decidindo se assiste — não é crítica, não é
resenha, não é recomendação; é o mapa de ONDE as opiniões divergem.

**O defeito que este módulo corrige.** Até a v1.9.20 o veredito era template
puro sobre o lift, e **19 dos 35 filmes recebiam texto byte-idêntico** ("Os
grupos falam das mesmas coisas — discordam sobre se elas funcionam"), com 20
caindo no ramo que o produz e 14 textos distintos no catálogo inteiro. A
causa não é o template ser burro — é o BRIEFING ser pobre: a frase relata a
AUSÊNCIA de contraste e nunca a PRESENÇA de assunto, enquanto o `tema` de
cada célula de `eixos` (a única fonte de variedade real, já rotulada por [D3]
e já filtrada de spoiler) era descartado.

**A fronteira, que é a mesma de §D2 desde a v1.9.8:** o código decide O QUÊ
(quais fatos, quais números, qual rótulo, qual eixo, qual grupo); o modelo
decide apenas COMO ESCREVER.

**E uma fronteira a mais, que este estágio acrescenta:** a serialização do
briefing **não contém nenhum algarismo**. O dict carrega `freq_pct`,
`lift_pp` e `share_pct` — para os testes, para a telemetria e para o template
de fallback —, mas o texto que vai ao modelo carrega só rótulos e booleanos.
Com isso a invariante "zero dígitos na saída" é garantida por CONSTRUÇÃO (o
modelo não copia um número que nunca viu), e `lift_pp` não existe para ele,
então "quase passou da margem" também não existe. A validação `digito` em
código continua sendo redundância DELIBERADA — as duas defesas cobrem coisas
diferentes, e remover qualquer uma é mudança de política (SPEC §3[V]).

**Nunca ficar sem veredito, nunca publicar veredito inválido.** Dois degraus
de fallback: retry direcionado, e depois o template determinístico da
v1.9.19/v1.9.20 — que continua no código e é a mesma função que o frontend
usa para JSON publicado antes desta versão.
"""
from __future__ import annotations

import re
import time
import unicodedata

from . import briefing as br
from . import qualidade as q
from . import quantificador as Q
from . import synthesize as S
from .config import BEST_OF_N, MARGEM_LIFT_PP, SPEC_VERSION
from .taxonomia import EIXOS, LIVRE, rotulo_do_eixo

ESTAGIO = "veredito"

# --- parâmetros do estágio, todos declarados (SPEC §3[V]) ------------------

# Piso de `assunto_compartilhado`: abaixo dele o eixo não é "assunto dos dois
# grupos", é ruído que os dois tocaram de passagem. 25 é a fronteira inferior
# da faixa `muitos` do mapa de quantificador (v1.2.3), reusada em vez de um
# número novo.
PISO_ASSUNTO_COMPARTILHADO_PCT = 25

# Teto da chave PRIMÁRIA de seleção. Sem ele, o critério premiaria empilhar
# tema atrás de tema até estourar o limite de palavras — trocaria o defeito
# "vazio" pelo defeito "lista". Duas âncoras é o que 1-2 frases comportam.
TETO_ANCORAS = 2

TETO_PALAVRAS = 55          # alvo ~45
MAX_FRASES = 2

# Casamento de âncora: proxy DECLARADO. Compara por prefixo, o que absorve
# flexão (`ritmos` -> `ritmo`) e SUBCONTA o que não absorve (`lentidão` não
# casa com `lento`). Subcontar é a direção certa: torna a chave primária mais
# difícil de satisfazer, nunca mais fácil.
PREFIXO_PALAVRA = 5
MIN_CHARS_PALAVRA = 4


# ===========================================================================
# Normalização e palavras de conteúdo
# ===========================================================================

def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# Fechadas e genéricas: palavras que aparecem em qualquer veredito e em
# qualquer tema, e que por isso não distinguem assunto nenhum. Inclui os
# rótulos de quantificador — senão "a maioria" contaria como se o texto
# tivesse nomeado o assunto.
_STOPWORDS = {
    "para", "pelo", "pela", "pelos", "pelas", "como", "mais", "menos",
    "muito", "muita", "muitos", "muitas", "pouco", "pouca", "poucos",
    "poucas", "esse", "essa", "esses", "essas", "este", "esta", "isso",
    "aqui", "onde", "quem", "cada", "todo", "toda", "todos", "todas",
    "outro", "outra", "outros", "outras", "ainda", "entre", "sobre",
    "sempre", "nunca", "quase", "metade", "maior", "maioria", "parte",
    "filme", "filmes", "grupo", "grupos", "coisa", "coisas", "gente",
    "publico", "espectador", "espectadores", "review", "reviews",
    "nota", "notas", "quando", "porque", "tambem", "apenas", "assim",
    "sendo", "estao", "estar", "ficar", "fazer", "ter", "acha", "acham",
    "achou", "acharam", "diz", "dizem", "disse", "aponta", "apontam",
    "destaca", "destacam", "elogia", "elogiam", "critica", "criticam",
    "cita", "citam", "menciona", "mencionam", "fala", "falam", "recomenda",
    "recomendam", "discorda", "discordam", "concorda", "concordam",
    "considera", "consideram", "funciona", "funcionam", "lado", "lados",
    "seu", "sua", "seus", "suas", "dele", "dela", "deles", "delas",
    "num", "numa", "sem", "com",
}


def palavras_de_conteudo(texto: str) -> list[str]:
    """Tokens normalizados, sem stopword e com pelo menos
    `MIN_CHARS_PALAVRA` caracteres — na ORDEM em que aparecem (a ordem
    importa para `tema_verbatim`)."""
    brutos = re.findall(r"[a-z]+", _normalizar(texto))
    return [w for w in brutos
            if len(w) >= MIN_CHARS_PALAVRA and w not in _STOPWORDS]


def _prefixos(palavras) -> set[str]:
    return {w[:PREFIXO_PALAVRA] for w in palavras}


# ===========================================================================
# Leitura do bloco `eixos`
# ===========================================================================

def _celula(eixos: dict, eixo: str, bucket: str) -> dict | None:
    for linha in eixos.get("linhas") or []:
        if linha.get("eixo") == eixo:
            return (linha.get("por_bucket") or {}).get(bucket)
    return None


def _celulas_citadas(eixos: dict, bucket: str):
    """`(eixo, celula)` de cada eixo que o bucket MENCIONA. `livre` fica de
    fora: não é um assunto, é o resto (mesma exclusão de `eixos.contraste`)."""
    for linha in eixos.get("linhas") or []:
        eixo = linha.get("eixo")
        if eixo == LIVRE:
            continue
        c = (linha.get("por_bucket") or {}).get(bucket) or {}
        if c.get("mencoes", 0) > 0 and c.get("de_n", 0) > 0:
            yield eixo, c


def _ordem_canonica(eixo: str) -> int:
    return EIXOS.index(eixo) if eixo in EIXOS else len(EIXOS)


def _maior_lift(eixos: dict, bucket: str, margem: int) -> dict | None:
    """O eixo de maior lift — "o que aquele grupo tem de PRÓPRIO"."""
    cands = [(eixo, c) for eixo, c in _celulas_citadas(eixos, bucket)
             if isinstance(c.get("lift_pp"), (int, float))]
    if not cands:
        return None
    eixo, c = max(cands, key=lambda t: (t[1]["lift_pp"], -_ordem_canonica(t[0])))
    return {"eixo": eixo, "eixo_rotulo": rotulo_do_eixo(eixo),
            "lift_pp": c["lift_pp"],
            "acima_da_margem": c["lift_pp"] >= margem,
            "tema": c.get("tema")}


def _maior_frequencia(eixos: dict, bucket: str) -> dict | None:
    """O eixo de maior FREQUÊNCIA — "do que aquele grupo mais fala", sem
    exigir que seja exclusivo dele (a correção da v1.9.20: contraste baixo
    com frequência alta são coisas diferentes)."""
    cands = list(_celulas_citadas(eixos, bucket))
    if not cands:
        return None
    eixo, c = max(cands, key=lambda t: (t[1]["mencoes"] / t[1]["de_n"],
                                        -_ordem_canonica(t[0])))
    pct, rot = Q.fracao_e_rotulo(c["mencoes"], c["de_n"])
    return {"eixo": eixo, "eixo_rotulo": rotulo_do_eixo(eixo),
            "tema": c.get("tema"), "freq_pct": pct,
            "rotulo_quantificador": rot}


def _assunto_compartilhado(eixos: dict) -> dict | None:
    """O eixo que os DOIS extremos mais citam — a substância do caso
    `valorativo`.

    Critério: maximiza `min(freq_negativas, freq_positivas)`, com piso de
    `PISO_ASSUNTO_COMPARTILHADO_PCT` nos dois lados. Desempate pela SOMA e,
    persistindo, pela ordem canônica de `EIXOS`.

    Não é o eixo mais citado no TOTAL: um eixo com 90% num lado e 5% no outro
    não é assunto compartilhado, é assunto de um lado só.
    """
    melhor = None
    for linha in eixos.get("linhas") or []:
        eixo = linha.get("eixo")
        if eixo == LIVRE:
            continue
        por = linha.get("por_bucket") or {}
        neg, pos = por.get("negativas") or {}, por.get("positivas") or {}
        if not (neg.get("de_n") and pos.get("de_n")):
            continue
        f_neg = Q.fracao_percentual(neg.get("mencoes", 0), neg["de_n"])
        f_pos = Q.fracao_percentual(pos.get("mencoes", 0), pos["de_n"])
        if min(f_neg, f_pos) < PISO_ASSUNTO_COMPARTILHADO_PCT:
            continue
        chave = (min(f_neg, f_pos), f_neg + f_pos, -_ordem_canonica(eixo))
        if melhor is None or chave > melhor[0]:
            melhor = (chave, eixo, neg, pos, f_neg, f_pos)
    if melhor is None:
        return None
    _, eixo, neg, pos, f_neg, f_pos = melhor
    return {
        "eixo": eixo,
        "eixo_rotulo": rotulo_do_eixo(eixo),
        "tema_negativas": neg.get("tema"),
        "tema_positivas": pos.get("tema"),
        "freq_negativas_pct": f_neg,
        "freq_positivas_pct": f_pos,
        "rotulo_quantificador_negativas": Q.rotulo(f_neg),
        "rotulo_quantificador_positivas": Q.rotulo(f_pos),
    }


def _bucket_dominante(buckets: list[dict]) -> dict | None:
    com_share = [b for b in buckets
                 if isinstance(b.get("share_real"), (int, float))]
    if not com_share:
        return None
    b = max(com_share, key=lambda x: x["share_real"])
    return {"bucket": b["bucket"], "share_pct": b["share_real"],
            "e_o_meio": b["bucket"] == "medianas"}


# ===========================================================================
# O briefing
# ===========================================================================

def montar_briefing(output: dict) -> dict | None:
    """O documento de decisões do veredito. Código puro, zero LLM.

    `None` quando o filme não tem bloco `eixos` utilizável — mesma política
    aditiva de ficha (§3[F]) e distribuição (§3[G]): sem o insumo, a chave
    não é emitida, nunca um veredito montado sobre buraco.
    """
    eixos = output.get("eixos") or {}
    if not eixos.get("linhas"):
        return None

    margem = eixos.get("margem_lift_pp") or MARGEM_LIFT_PP
    buckets = output.get("buckets") or []
    por_nome = {b.get("bucket"): b for b in buckets if b.get("bucket")}
    dominante = _bucket_dominante(buckets)
    meio_dominante = bool(dominante and dominante["e_o_meio"])

    # `medianas` só entra quando é o grupo DOMINANTE: o meio nunca é um dos
    # dois lados do contraste (v1.9.19, Entrega 4).
    nomes = ["negativas", "positivas"] + (["medianas"] if meio_dominante else [])

    grupos, reduzida = {}, False
    for nome in nomes:
        b = por_nome.get(nome) or {}
        estado = b.get("estado_piso") or "completa"
        modo = b.get("modo") or "completo"
        # Bucket `sem_analise` não empresta eixo nenhum — não há análise
        # temática para esse grupo, então não há assunto confiável a citar.
        mudo = estado == "sem_analise"
        g = {
            "modo": modo,
            "estado_piso": estado,
            "eixo_maior_lift": None if mudo else _maior_lift(eixos, nome, margem),
            "eixo_maior_frequencia": None if mudo else _maior_frequencia(eixos, nome),
        }
        if isinstance(b.get("share_real"), (int, float)):
            g["share_pct"] = b["share_real"]
        if modo == "reduzido" or estado != "completa":
            reduzida = True
        grupos[nome] = g

    ficha = output.get("ficha") or {}
    return {
        "slug": output.get("slug"),
        "titulo": ficha.get("titulo") or (output.get("slug") or ""),
        "ano": ficha.get("ano"),
        "contraste": eixos.get("contraste"),
        "margem_lift_pp": margem,
        "taxonomia_id": eixos.get("taxonomia_id"),
        "bucket_dominante": dominante,
        "assunto_compartilhado": _assunto_compartilhado(eixos),
        "amostra_reduzida": reduzida,
        "grupos": grupos,
    }


def prefixo_de_codigo(b: dict) -> str:
    """O único número que sobrevive no texto renderizado, e ele vem DAQUI.

    Quando o meio é o maior grupo, descrever o filme só pelos dois grupos
    minoritários mentiria por omissão. A menção vem ANTES, como contexto que
    muda a leitura do resto — e é concatenada pelo CÓDIGO, fora da saída do
    modelo (invariante 5 do prompt).
    """
    d = b.get("bucket_dominante")
    if not d or not d["e_o_meio"] or not isinstance(d.get("share_pct"), int):
        return ""
    return (f"O meio-termo é o maior grupo da recepção "
            f"(~{d['share_pct']}% das notas). ")


# ===========================================================================
# Serialização — RÓTULOS, nunca números
# ===========================================================================

_NOME_DO_GRUPO = {"negativas": "QUEM NÃO RECOMENDA",
                  "positivas": "QUEM RECOMENDA",
                  "medianas": "O MEIO-TERMO"}


def serializar_briefing(b: dict) -> str:
    """O briefing como texto, para entrar na mensagem do usuário.

    **Nenhum algarismo sai daqui** — é o que torna "zero dígitos na saída"
    garantia por construção. `lift_pp` fica de fora por outra razão: o limiar
    é BINÁRIO, e o prompt não pode ter nenhuma noção de "chegou perto" (SPEC
    §3[V]; `the-godfather` falha a margem por 0,4pp).

    Determinística: mesma entrada, mesma saída, byte a byte.
    """
    # **O TÍTULO DO FILME NÃO ENTRA.** Duas razões, e a segunda é a forte:
    #
    # (1) `friday-the-13th-2009` se chama "Sexta-Feira 13" — o título CARREGA
    #     algarismo, e emiti-lo abriria na serialização exatamente o buraco
    #     que ela existe para fechar. (É o mesmo falso positivo que a
    #     varredura da v1.9.20 já tinha investigado no frontend.)
    # (2) Nomear o filme CONVIDA o modelo a usar o que ele sabe sobre o
    #     filme — e a invariante 1 proíbe qualquer contexto externo. Um
    #     briefing anônimo torna a fidelidade mais fácil de obedecer do que
    #     de violar. O veredito descreve onde os grupos divergem; ele nunca
    #     precisou dizer de que filme se trata, porque é renderizado logo
    #     abaixo do título na página.
    #
    # `titulo`/`ano` continuam no DICT, para telemetria e depuração.
    L = []

    estado = b.get("contraste")
    if estado == "valorativo":
        L += ["CONTRASTE ENTRE OS GRUPOS: valorativo.",
              "A medição não encontrou NENHUM assunto que um grupo tenha e o "
              "outro não. Os grupos falam das MESMAS coisas e divergem no "
              "JULGAMENTO. É PROIBIDO afirmar que eles falam de assuntos "
              "diferentes.", ""]
    else:
        L += ["CONTRASTE ENTRE OS GRUPOS: temático.",
              "A medição encontrou assunto próprio de pelo menos um grupo — "
              "os marcados abaixo como ASSUNTO PRÓPRIO.", ""]

    a = b.get("assunto_compartilhado")
    if a:
        L.append("ASSUNTO QUE OS DOIS GRUPOS MAIS CITAM: "
                 + a["eixo_rotulo"].lower())
        if a["tema_negativas"]:
            L.append(f"  · como quem NÃO recomenda vê: {a['tema_negativas']}")
        if a["tema_positivas"]:
            L.append(f"  · como quem recomenda vê: {a['tema_positivas']}")
        if not a["tema_negativas"] and not a["tema_positivas"]:
            L.append("  · (sem tema nomeado dos dois lados — use só o nome do "
                     "assunto, não invente detalhe)")
        L.append("")

    for nome, g in b["grupos"].items():
        L.append(f"{_NOME_DO_GRUPO.get(nome, nome.upper())}:")
        lift = g["eixo_maior_lift"]
        if lift and lift["acima_da_margem"]:
            L.append(f"  ASSUNTO PRÓPRIO deste grupo: {lift['eixo_rotulo'].lower()}")
            if lift.get("tema"):
                L.append(f"    tema: {lift['tema']}")
        else:
            L.append("  ASSUNTO PRÓPRIO deste grupo: nenhum — o que este "
                     "grupo fala, os outros também falam.")
        freq = g["eixo_maior_frequencia"]
        if freq:
            L.append(f"  ASSUNTO MAIS FALADO por este grupo: "
                     f"{freq['eixo_rotulo'].lower()}")
            if freq.get("tema"):
                L.append(f"    tema: {freq['tema']}")
            L.append(f"    quantificador AUTORIZADO (não use nenhum mais "
                     f"forte): {freq['rotulo_quantificador']}")
        else:
            L.append("  ASSUNTO MAIS FALADO por este grupo: indisponível "
                     "(amostra insuficiente para análise temática).")
        if g["modo"] == "reduzido" or g["estado_piso"] != "completa":
            L.append("  AMOSTRA PEQUENA neste grupo: escreva com cautela, "
                     "sem apresentar o achado como sólido.")
        L.append("")

    d = b.get("bucket_dominante")
    if d and d["e_o_meio"]:
        L += ["O MEIO-TERMO É O MAIOR GRUPO DA RECEPÇÃO. O peso dele já é "
              "informado por fora, pelo sistema — NÃO escreva percentual, "
              "nem número, nem proporção.", ""]

    return "\n".join(L).rstrip() + "\n"


# ===========================================================================
# Âncoras — o insumo da chave PRIMÁRIA de seleção
# ===========================================================================

def ancoras(b: dict) -> list[dict]:
    """As âncoras substantivas do briefing: o `assunto_compartilhado` e o
    eixo de top-frequência de cada lado, cada um com as palavras de conteúdo
    do seu `tema` e do rótulo do seu eixo.

    A lista NÃO é deduplicada por eixo de propósito — `id` identifica o PAPEL
    da âncora no briefing, e dois papéis podem cair no mesmo eixo (é o normal
    num filme `valorativo`). A deduplicação por EIXO acontece na contagem
    (`n_ancoras`), porque lá a pergunta é quantos ASSUNTOS distintos o texto
    nomeou, não quantos papéis ele satisfez.
    """
    saida = []

    def _add(id_, eixo, rotulo, *temas):
        if not eixo:
            return
        palavras = set(palavras_de_conteudo(rotulo or ""))
        for t in temas:
            palavras |= set(palavras_de_conteudo(t or ""))
        if not palavras:
            return
        saida.append({"id": id_, "eixo": eixo,
                      "tema": next((t for t in temas if t), None),
                      "palavras": sorted(palavras)})

    a = b.get("assunto_compartilhado")
    if a:
        _add("assunto_compartilhado", a["eixo"], a["eixo_rotulo"],
             a["tema_negativas"], a["tema_positivas"])
    for nome, g in b.get("grupos", {}).items():
        freq = g.get("eixo_maior_frequencia")
        if freq:
            _add(f"frequencia_{nome}", freq["eixo"], freq["eixo_rotulo"],
                 freq.get("tema"))
        lift = g.get("eixo_maior_lift")
        if lift and lift["acima_da_margem"]:
            _add(f"lift_{nome}", lift["eixo"], lift["eixo_rotulo"],
                 lift.get("tema"))
    return saida


def _ancora_nomeada(ancora: dict, prefixos_do_texto: set[str]) -> bool:
    """Casamento por PALAVRAS DE CONTEÚDO, nunca por substring do tema.

    Uma âncora conta como nomeada quando `min(2, |palavras|)` das suas
    palavras aparecem no texto. Duas palavras é o que separa "nomeou o
    assunto" de "usou uma palavra por acaso"; âncora de uma palavra só (eixo
    sem tema nomeado) exige essa palavra.
    """
    alvo = _prefixos(ancora["palavras"])
    exigidas = min(2, len(alvo))
    return len(alvo & prefixos_do_texto) >= exigidas


def n_ancoras(texto: str, b: dict) -> int:
    """Quantos ASSUNTOS distintos (eixos) o texto nomeia. Sem teto."""
    prefixos = _prefixos(palavras_de_conteudo(texto))
    return len({a["eixo"] for a in ancoras(b)
                if _ancora_nomeada(a, prefixos)})


def pontuacao_ancoras(texto: str, b: dict) -> int:
    """A chave PRIMÁRIA de seleção, com o teto de `TETO_ANCORAS`."""
    return min(n_ancoras(texto, b), TETO_ANCORAS)


def eixos_do_briefing(b: dict) -> set[str]:
    return {a["eixo"] for a in ancoras(b)}


# ===========================================================================
# [v1.9.22] PADRÃO SINTÁTICO DE ABERTURA — a métrica do Defeito 2
# ===========================================================================
# **O que ela mede, e por que Jaccard não via.** Sob a v1.9.21 a repetição
# saiu do léxico e foi para a ESTRUTURA: 11 dos 17 filmes `valorativo`
# abriam com uma fórmula de divergência ("A divergência central está…", "As
# opiniões divergem…"). As palavras de conteúdo de cada um são distintas, o
# Jaccard médio ficou em 0,06 — e quem navega três filmes seguidos vê a
# mesma frase três vezes. É a versão estrutural do defeito que a v1.9.21
# veio consertar.
#
# **A definição, e ela é um PROXY DECLARADO:** o padrão é o núcleo do
# primeiro sintagma nominal — o primeiro token de conteúdo da frase, fora da
# classe fechada de determinantes/preposições/conjunções —, truncado a 5
# caracteres, com os RÓTULOS DE QUANTIFICADOR colapsados em `QUANT`.
#
# Duas decisões de desenho, as duas medidas antes de fixar:
#
# (1) **Sem o verbo.** A definição "núcleo + verbo principal" foi testada e
#     descartada: sem analisador sintático, o verbo é identificado por
#     terminação, e "está" colide com "esta" ao remover acento, e o primeiro
#     verbo finito costuma estar DENTRO do sujeito ("dos que recomendam").
#     O resultado é que ela reporta 22 padrões distintos em 35 contra 7 da
#     definição sem verbo — **ela parece melhor porque é mais ruidosa**, e
#     uma métrica que melhora o número por imprecisão é pior que não ter
#     métrica.
#
# (2) **Rótulo de quantificador colapsado.** Qual rótulo abre a frase é
#     decisão do CÓDIGO (vem do mapa da v1.2.3, §D2), não do modelo. Contar
#     "A maioria…" e "Cerca de metade…" como aberturas diferentes creditaria
#     ao modelo uma variedade que é do dado.
#
# Linha de base medida nos 35 publicados sob a v1.9.21: **7 padrões para 35
# filmes, com os três maiores cobrindo 28 (80%)** — QUANT 14, `diver` 8,
# `opini` 6.

_FUNCIONAIS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da",
    "dos", "das", "em", "no", "na", "nos", "nas", "por", "pelo", "pela",
    "pelos", "pelas", "para", "com", "sem", "sob", "sobre", "entre", "ate",
    "desde", "apos", "ante", "e", "ou", "mas", "que", "se", "ja",
    "enquanto", "embora", "quando", "porque", "pois", "tanto", "quanto",
    "assim", "tambem", "alem", "ambos", "ambas", "este", "esta", "esse",
    "essa", "aquele", "aquela", "seu", "sua", "seus", "suas", "nesse",
    "neste", "nessa", "desta", "deste", "dessa", "desse", "ao", "aos",
    "mais", "menos", "bem", "aqui", "nao",
}

# Prefixos de 5 dos rótulos do mapa de quantificador, mais as formas que
# abrem frase. Colapsados em `QUANT` — ver decisão (2) acima.
_PREFIXOS_QUANT = ({_normalizar(r)[:PREFIXO_PALAVRA] for r in Q.ROTULOS}
                   | {"maior", "cerca", "quase", "muito", "pouco", "algun",
                      "metad", "grand", "boa p"})

ABERTURA_QUANTIFICADOR = "QUANT"


def padrao_de_abertura(texto: str) -> str:
    """O padrão sintático com que o veredito começa. `""` se não houver."""
    for w in re.findall(r"[a-z]+", _normalizar(texto)):
        if len(w) < 4 or w in _FUNCIONAIS:
            continue
        p = w[:PREFIXO_PALAVRA]
        return ABERTURA_QUANTIFICADOR if p in _PREFIXOS_QUANT else p
    return ""


# ===========================================================================
# [v1.9.23] CONECTIVO CONTRASTIVO — a segunda dimensão da métrica de forma
# ===========================================================================
# **A observação de MÉTODO que este bloco existe para registrar, e que vale
# mais que a métrica em si:** a cada correção, a repetição MIGRA de dimensão,
# e a métrica vigente captura exatamente a dimensão que acabou de ser
# consertada — ficando cega para aquela que a repetição passou a ocupar.
#
#   v1.9.21 consertou o TEXTO IDÊNTICO.        Métrica: Jaccard.
#           A repetição migrou para a ABERTURA — e o Jaccard não via.
#   v1.9.22 consertou a ABERTURA.              Métrica: padrão de abertura.
#           A repetição migrou para o MOLDE CONTRASTIVO — 17 de 17 filmes
#           `valorativo` construindo o contraste com "Enquanto…, …" ou
#           equivalente direto, variando só o substantivo de abertura.
#
# **A regra que fica:** estender a métrica ANTES de declarar vitória, não
# depois. Uma dimensão não medida não é uma dimensão sem defeito — é uma
# dimensão sem número.
#
# **E o que este número NÃO é.** 17/17 no mesmo molde pode ser o PISO DO
# GÊNERO: um produto cujo conteúdo é a divergência entre dois grupos tende
# ao período contrastivo, e não existe forma neutra de dizer "A acha X, B
# acha o contrário" em português que não seja contrastiva. A métrica existe
# para que a decisão seja tomada com o número à vista — ela não decide que
# há defeito, e nada no código reage a ela.

# Ordem importa: a lista é varrida na ordem em que está escrita e o PRIMEIRO
# a casar no texto é o principal. As locuções vêm antes das palavras soltas
# que elas contêm ("ao passo que" antes de "que" não é problema porque "que"
# não está na lista; "no entanto" antes de "entanto" sim).
_CONECTIVOS_CONTRASTIVOS = (
    "ao passo que", "em contrapartida", "por outro lado", "em contraste",
    "por sua vez", "no entanto", "entretanto", "todavia", "contudo",
    "enquanto", "porem", "embora", "ainda que", "apesar de", "ja entre",
    "ja os", "ja as", "ja a ", "ja o ", "mas ",
)

_RE_CONECTIVO = [(c, re.compile(rf"(?<![a-z]){re.escape(c)}"))
                 for c in _CONECTIVOS_CONTRASTIVOS]

CONECTIVO_AUSENTE = "nenhum"


def conectivo_contrastivo(texto: str) -> str:
    """O conectivo contrastivo PRINCIPAL — o primeiro que aparece no texto.

    `CONECTIVO_AUSENTE` quando não há nenhum: o contraste pode estar só na
    pontuação (ponto e vírgula, dois pontos) ou na oposição semântica sem
    marcador, e essas são formas legítimas que a lista não deve inventar.
    """
    plano = _normalizar(texto)
    achados = [(m.start(), c) for c, rx in _RE_CONECTIVO
               for m in [rx.search(plano)] if m]
    return min(achados)[1] if achados else CONECTIVO_AUSENTE


# ===========================================================================
# Validações pós-parsing — em CÓDIGO, nunca só no prompt
# ===========================================================================

# Marcadores lexicais de cada eixo, para `tema_ausente`. A unidade de
# detecção é o EIXO, não o tema: o eixo tem vocabulário FECHADO (10 itens,
# §2.5) e um tema não tem — checar tema a tema exigiria casamento por
# SIGNIFICADO, que só um segundo LLM faz, e este projeto não põe LLM para
# julgar saída de LLM.
#
# A lista é deliberadamente CURTA e específica. Marcador genérico produz
# falso positivo em texto correto, que é o modo de falha caro aqui: ele
# elimina candidatos bons e empurra o filme para o fallback.
# Marcadores lexicais de cada eixo, para `tema_ausente`. A unidade de
# detecção é o EIXO, não o tema: o eixo tem vocabulário FECHADO (10 itens,
# §2.5) e um tema não tem — checar tema a tema exigiria casamento por
# SIGNIFICADO, que só um segundo LLM faz, e este projeto não põe LLM para
# julgar saída de LLM.
#
# CONVENÇÃO: marcador terminado em `*` casa por PREFIXO de token
# (`arrastad*` pega "arrastado"/"arrastada"); sem `*`, casa o TOKEN INTEIRO.
# A distinção não é cosmética — foi um bug real achado na primeira geração
# dos 35: como substring solta, `tom` casava dentro de "tomam", "sintoma" e
# "átomo", e reprovava por `tom_atmosfera` um texto que só dizia "decisões
# que eles tomam". Mesma família do bug de substring da v1.6.2
# (`"1%"` casando dentro de `"91%"`), e mesma correção: fronteira explícita.
#
# A lista é deliberadamente CURTA e ESPECÍFICA. O custo de um falso positivo
# aqui é caro e medido: ele elimina candidatos bons e empurra o filme para o
# `template_fallback` — ou seja, devolve ao leitor exatamente a frase genérica
# que esta versão veio eliminar. Dois marcadores foram REMOVIDOS depois de
# medidos como ambíguos na primeira geração dos 35:
#   · `desenvolvimento` (era de `roteiro_estrutura`): "desenvolvimento
#     arrastado" é RITMO, "desenvolvimento dos personagens" é ROTEIRO. Um
#     marcador que casa nos dois não discrimina nada — reprovou `hereditary`;
#   · `incomod*` (era de `impacto_emocional`): incômodo é como se descreve
#     QUALQUER coisa de que não se gostou, inclusive uma personagem
#     irritante, que é `roteiro_estrutura` — reprovou `pearl-2022`.
_MARCADORES_EIXO = {
    "ritmo": ("ritmo", "ritmos", "arrastad*", "lentid*", "duracao", "tedio",
              "andamento", "cansativ*", "entediant*", "monoton*"),
    "atuacao": ("atuacao", "atuacoes", "elenco", "interpretac*",
                "performance", "atriz", "ator", "atores"),
    "direcao_imagem": ("direcao", "fotografia", "cinematograf*", "visual",
                       "visuais", "planos", "imagem", "imagens"),
    "roteiro_estrutura": ("roteiro", "estrutura", "narrativa", "personagem",
                          "personagens", "dialogo", "dialogos", "trama",
                          "historia", "enredo"),
    "som_trilha": ("trilha", "sonora", "musica", "musicas", "cancao",
                   "cancoes"),
    "tom_atmosfera": ("atmosfera", "clima", "ambientac*", "tensao", "tom"),
    "impacto_emocional": ("emocional", "emocao", "emocoes", "comovent*",
                          "chorar", "choro"),
    "comparacoes": ("comparacao", "comparacoes", "comparativ*", "paralelo",
                    "paralelos", "adaptac*", "refilmagem", "remake"),
    "expectativa": ("expectativa", "expectativas", "superestimad*",
                    "esperava", "esperavam", "decepc*", "hype"),
    "critica_social": ("critica social", "politica", "politico", "metafora",
                       "denuncia", "alegoria"),
}

_RE_MARCADOR = {
    eixo: [re.compile(rf"(?<![a-z]){re.escape(m.rstrip('*'))}"
                      + ("" if m.endswith("*") else r"(?![a-z])"))
           for m in marcadores]
    for eixo, marcadores in _MARCADORES_EIXO.items()
}


_ESCOPO_GENERALIZADO = (
    "os criticos", "as criticas especializadas", "a critica especializada",
    "o consenso", "consenso da critica", "a recepcao do filme",
    "a recepcao critica", "o publico", "os espectadores", "todo mundo",
    "a audiencia",
)

_NOTA_OU_SCORE = (
    r"\bnotas?\b", r"\bestrelas?\b", r"\bscore\b", r"\bpontuac", r"\bmedia\b",
    r"\bavaliacao media\b", r"\bde dez\b", r"\bde cinco\b",
)

# Só valem quando o filme é `valorativo` — num filme `tematico` dizer que os
# grupos falam de coisas diferentes é o trabalho, não uma violação.
_CONTRASTE_FABRICADO = (
    "coisas diferentes", "assuntos diferentes", "temas diferentes",
    "aspectos diferentes", "pontos diferentes", "coisas distintas",
    "assuntos distintos", "outras coisas", "outro assunto",
    "discordam sobre qual", "discordam sobre o que",
    "cada grupo fala de", "cada lado fala de", "falam de coisas",
    "nada em comum", "assunto completamente",
)

_ASPAS = ('"', "“", "”", "«", "»", "‘", "’")

_FIM_FRASE = re.compile(r"(?<=[.!?])\s+")

# Construção -> faixa, derivado do mapa que o briefing da NARRATIVA já usa.
# Os conjuntos são disjuntos e nenhuma construção é substring de outra faixa
# (invariante travada por teste em `test_variantes_prompt.py`).
# [v1.9.22] As CONTRAÇÕES do artigo inicial fazem parte do rótulo, não são
# desvio dele: "de a maioria" vira "da maioria", "por a maioria" vira "pela
# maioria". A regra já vale em §D2 (regra 4, v1.4.1) e faltava aqui — sem
# ela, `dune-2021` escrevia "pela maioria dos que reprovam", usando o rótulo
# EXATO que o briefing forneceu, e a checagem não o reconhecia. Achado ao
# medir o Defeito 1: era um falso NEGATIVO do instrumento, e viraria falso
# POSITIVO assim que a checagem passasse a exigir o rótulo.
_CONTRACOES_ARTIGO_A = ("da", "na", "pela", "a", "à")


def _padroes_da_construcao(construcao: str) -> str:
    c = _normalizar(construcao)
    pads = [rf"(?<![a-z]){re.escape(c)}(?![a-z])"]
    if c.startswith("a "):
        resto = re.escape(c[2:])
        alt = "|".join(_normalizar(x) for x in _CONTRACOES_ARTIGO_A)
        pads.append(rf"(?<![a-z])(?:{alt})\s+{resto}(?![a-z])")
    return "|".join(pads)


_FAIXA_DA_CONSTRUCAO = {
    _normalizar(c): faixa
    for faixa, construcoes in br.FAIXAS_QUANTIFICADOR.items()
    for c in construcoes
}

_RE_CONSTRUCAO = [(faixa, re.compile(_padroes_da_construcao(c)))
                  for c, faixa in _FAIXA_DA_CONSTRUCAO.items()]


# [v1.9.22] DEFLAÇÃO POR HEDGE — o defeito do Defeito 1, e por que ele é do
# §0 e não de estilo.
#
# Um adjetivo de magnitude reduzida ("pontuais", "isoladas", "esparsas",
# "raras") qualificando um substantivo de review afirma um TAMANHO — e
# tamanho é do código, não do modelo. Medido em produção:
#   · `pearl-2022`: negativas e positivas com a MESMA frequência (58%, rótulo
#     `cerca de metade` nos dois). O lado positivo recebeu o rótulo; o
#     negativo virou "impressões negativas pontuais". Mesmo número, dois
#     tratamentos, e o que os separa é o SENTIMENTO do grupo — violação
#     direta da neutralidade de tratamento do §0.
#   · `the-godfather`: "relatos pontuais apontam que a maioria dos que
#     desaprovam..." — pontual e maioria na mesma oração, autocontraditório.
#     O rótulo estava CERTO; o hedge é que o desmente.
#
# A EXCEÇÃO é o que separa deflação de cautela legítima: quando a frase
# ancora explicitamente na AMOSTRA ("analisadas", "disponíveis",
# "coletadas", "amostra"), ela fala de quantas reviews foram lidas, e isso
# é verdade e é obrigatório em modo reduzido (invariante 8 do prompt).
# `wonka` depende dessa exceção: "entre as poucas manifestações
# desfavoráveis ANALISADAS" é uma afirmação sobre a base, não sobre a
# frequência dentro do grupo.
_DEFLATOR = r"(?:pontuais?|isolad[ao]s?|espars[ao]s?|rar[ao]s?)"
_NOME_DE_REVIEW = (r"(?:relatos?|impressoes|impressao|avaliacoes|avaliacao|"
                   r"manifestacoes|mencoes|opinioes|comentarios?|vozes|"
                   r"reacoes|leituras)")
_RE_DEFLACAO = re.compile(
    rf"{_NOME_DE_REVIEW}(?:\s+\w+){{0,2}}\s+{_DEFLATOR}"
    rf"|{_DEFLATOR}\s+{_NOME_DE_REVIEW}")
_RE_ANCORA_DE_AMOSTRA = re.compile(
    r"analisad[ao]s|disponiveis|coletad[ao]s|amostra|examinad[ao]s|lidas")


def _frases(texto: str) -> list[str]:
    return [f.strip() for f in _FIM_FRASE.split(texto or "") if f.strip()]


def _rotulos_autorizados(b: dict) -> set[str]:
    """Todo rótulo que o briefing forneceu, de qualquer grupo."""
    aut = {g["eixo_maior_frequencia"]["rotulo_quantificador"]
           for g in b.get("grupos", {}).values()
           if g.get("eixo_maior_frequencia")}
    a = b.get("assunto_compartilhado")
    if a:
        aut |= {a["rotulo_quantificador_negativas"],
                a["rotulo_quantificador_positivas"]}
    return aut


def _quantificador_divergente(texto: str, b: dict) -> bool:
    """Qualquer faixa usada que o briefing NÃO forneceu — nos dois sentidos.

    **[v1.9.22] Mudança de POLÍTICA, não de checagem.** Até a v1.9.21 esta
    função era `_quantificador_mais_forte` e reprovava só o rótulo mais
    FORTE, porque a invariante 4 do prompt dizia "mais fraco é permitido".
    Essa metade estava errada: **deflação é falsidade tanto quanto
    inflação**, e o §0 ("o código é a autoridade sobre quantidade") não
    distingue direção. Um grupo de 58% descrito como anedota mente sobre o
    dado exatamente como um de 40% descrito como "quase todos".

    Registro honesto do alcance: no catálogo publicado sob a v1.9.21 esta
    checagem reprova ZERO textos — nenhum dos 35 usou faixa fora do
    conjunto autorizado, nem para cima nem para baixo. É trava PREVENTIVA.
    O que realmente conserta os dois casos medidos é `_deflacao_por_hedge`.

    Continua sendo de nível de TEXTO, não por grupo: num veredito de 1-2
    frases não há span por grupo para ancorar a atribuição com segurança —
    a medição do Defeito 1 tentou atribuir por proximidade e errou em 4 de
    35. Comparar contra o CONJUNTO de rótulos autorizados é a leitura que
    não inventa atribuição: deixa passar só o caso em que o modelo aplicou
    a um grupo o rótulo autorizado do outro.
    """
    autorizados = _rotulos_autorizados(b)
    if not autorizados:
        return False
    plano = _normalizar(texto)
    return any(rx.search(plano) for faixa, rx in _RE_CONSTRUCAO
               if faixa not in autorizados)


def _deflacao_por_hedge(texto: str, b: dict) -> bool:
    """Hedge que faz o TAMANHO de um grupo parecer menor que o rótulo dele.

    A regra que isto implementa, e que a invariante 8 do prompt passa a
    dizer por extenso: **cautela é sobre a AMOSTRA (quantas reviews foram
    analisadas), nunca sobre a FREQUÊNCIA (que fatia daquele grupo disse
    aquilo)**. Qualificar a base é obrigatório em modo reduzido; encolher a
    magnitude é afirmar um número, e número é do código.

    A âncora de amostra na vizinhança da ocorrência é o que preserva a
    formulação legítima (`wonka`). A janela é de 60 caracteres para cada
    lado: perto o bastante para ser a mesma oração, larga o bastante para
    alcançar o particípio que ancora ("...manifestações desfavoráveis
    ANALISADAS").
    """
    plano = _normalizar(texto)
    for m in _RE_DEFLACAO.finditer(plano):
        vizinhanca = plano[max(0, m.start() - 60):m.end() + 60]
        if not _RE_ANCORA_DE_AMOSTRA.search(vizinhanca):
            return True
    return False


def _tema_ausente(texto: str, b: dict) -> bool:
    presentes = eixos_do_briefing(b)
    plano = _normalizar(texto)
    for eixo, padroes in _RE_MARCADOR.items():
        if eixo in presentes:
            continue
        if any(p.search(plano) for p in padroes):
            return True
    return False


def _tema_verbatim(texto: str, b: dict) -> bool:
    """Cópia LITERAL de um tema do briefing.

    Só vale para tema com 3+ palavras de conteúdo: um tema de uma ou duas
    palavras não é copiável — é a única forma de nomeá-lo. Existe para que a
    chave primária de seleção não possa ser satisfeita empilhando citação:
    a cópia é REPROVADA, não premiada.
    """
    do_texto = palavras_de_conteudo(texto)
    for a in ancoras(b):
        tema = a.get("tema")
        if not tema:
            continue
        alvo = palavras_de_conteudo(tema)
        if len(alvo) < 3:
            continue
        n = len(alvo)
        for i in range(len(do_texto) - n + 1):
            if do_texto[i:i + n] == alvo:
                return True
    return False


def validar(texto: str, b: dict) -> list[str]:
    """As flags mecânicas de um candidato. Lista ordenada, vazia = limpo.

    Roda sobre o texto do MODELO — nunca sobre o texto final com o prefixo de
    código concatenado, que TEM algarismo por construção e faria a validação
    reprovar a própria correção.
    """
    flags = []
    if not (texto or "").strip():
        return ["vazio"]
    plano = _normalizar(texto)

    if q.formato_invalido(texto):
        flags.append("formato_invalido")
    if re.search(r"\d", texto):
        flags.append("digito")
    if any(c in texto for c in _ASPAS):
        flags.append("aspas")
    if not S._idioma_e_pt_br(texto):
        flags.append("idioma")

    palavras = re.findall(r"\S+", texto)
    if len(palavras) > TETO_PALAVRAS or len(_frases(texto)) > MAX_FRASES:
        flags.append("comprimento")

    if any(m in plano for m in _ESCOPO_GENERALIZADO):
        flags.append("escopo_generalizado")
    if any(re.search(p, plano) for p in _NOTA_OU_SCORE):
        flags.append("nota_ou_score")
    if _quantificador_divergente(texto, b):
        flags.append("quantificador_divergente")
    if _deflacao_por_hedge(texto, b):
        flags.append("deflacao_por_hedge")
    if _tema_ausente(texto, b):
        flags.append("tema_ausente")
    if _tema_verbatim(texto, b):
        flags.append("tema_verbatim")
    if b.get("contraste") == "valorativo" and any(
            m in plano for m in _CONTRASTE_FABRICADO):
        flags.append("contraste_fabricado")
    if q.achar_resenha_speak(texto, q.carregar_blocklist()):
        flags.append("cliche")

    return sorted(flags)


# ===========================================================================
# Seleção — chave DUPLA, e nenhum LLM julga prosa
# ===========================================================================

_EXPLICACAO = {
    "vazio": "veio vazio",
    "formato_invalido": "veio embrulhado em JSON/cerca de código em vez de "
                        "texto puro",
    "digito": "contém algarismo — o veredito não pode ter NENHUM número",
    "aspas": "usa aspas de citação",
    "idioma": "não está em português do Brasil",
    "comprimento": "passou do teto de palavras ou de duas frases",
    "escopo_generalizado": 'generaliza para "os críticos"/"o consenso"/"o '
                           'público" em vez de falar do GRUPO',
    "nota_ou_score": "menciona nota, estrela ou score — proibido em qualquer "
                     "lugar do produto",
    "quantificador_divergente": "usa um quantificador que o briefing NÃO "
                                "forneceu — nem mais forte, nem mais fraco: "
                                "escreva exatamente o rótulo dado",
    "deflacao_por_hedge": "faz o tamanho de um grupo parecer menor do que o "
                          "rótulo dele ('relatos pontuais', 'impressões "
                          "pontuais'). Cautela é sobre a AMOSTRA (quantas "
                          "reviews foram analisadas), nunca sobre a "
                          "FREQUÊNCIA dentro do grupo",
    "tema_ausente": "cita um assunto que não está no briefing",
    "tema_verbatim": "copia um tema do briefing palavra por palavra — diga o "
                     "assunto com as suas palavras",
    "contraste_fabricado": "afirma que os grupos falam de assuntos "
                           "DIFERENTES, e a medição diz que falam dos MESMOS",
    "cliche": "usa expressão de resenha genérica",
}

_CHAVES = ("ancoras", "abertura", "brevidade")


def _medir(texto: str, b: dict, aberturas: dict | None = None) -> dict:
    flags = validar(texto, b)
    abertura = padrao_de_abertura(texto)
    return {"flags": flags, "n_flags": len(flags),
            "n_palavras": len(re.findall(r"\S+", texto or "")),
            "n_ancoras": n_ancoras(texto, b),
            "pontuacao": pontuacao_ancoras(texto, b),
            "abertura": abertura,
            "abertura_freq": (aberturas or {}).get(abertura, 0)}


def _chave(m: dict) -> tuple:
    """Menor é melhor: âncoras entram NEGADAS (mais é melhor); frequência da
    abertura e número de palavras entram diretas (menos é melhor).

    [v1.9.22] `abertura_freq` entra ANTES da brevidade — é o ataque ao
    Defeito 2 pela SELEÇÃO, usando os candidatos que o best-of-3 já gerou,
    sem nenhuma chamada nova. Ver `selecionar` para a política de
    estabilidade que a torna independente da ordem dos filmes.
    """
    return (-m["pontuacao"], m["abertura_freq"], m["n_palavras"])


def _criterio_decisivo(vencedor: dict, resto: list[dict]) -> str:
    if not resto:
        return "unico"
    a = _chave(vencedor)
    for i, nome in enumerate(_CHAVES):
        if all(a[i] < _chave(o)[i] for o in resto):
            return nome
    return "empate"


def selecionar(candidatos: list[str], b: dict,
               aberturas: dict | None = None) -> dict:
    """A escolha, e o registro de por que ela foi feita.

    **A chave NÃO é brevidade.** A primeira proposta desta sessão foi "o mais
    curto" e foi reprovada com razão: os 19 vereditos idênticos que a versão
    veio corrigir não eram longos, eram VAZIOS — otimizar para brevidade
    otimiza na direção do defeito. A chave primária é informatividade
    ancorada (com teto de 2); brevidade só desempata.

    Validação vem antes de qualquer critério de qualidade: um texto que mente
    com riqueza continua mentindo.
    """
    medidos = []
    for i, texto in enumerate(candidatos):
        m = _medir(texto, b, aberturas)
        m["indice"] = i
        m["eliminado"] = m["n_flags"] > 0
        medidos.append(m)

    limpos = [m for m in medidos if not m["eliminado"]]
    if limpos:
        vencedor = min(limpos, key=lambda m: (_chave(m), m["indice"]))
        motivo, precisa_retry, pool = "melhor_entre_limpos", False, limpos
    else:
        vencedor = min(medidos,
                       key=lambda m: (m["n_flags"], _chave(m), m["indice"]))
        motivo, precisa_retry, pool = "menor_severidade", True, medidos

    resto = [m for m in pool if m["indice"] != vencedor["indice"]]
    return {
        "indice": vencedor["indice"],
        "texto": candidatos[vencedor["indice"]],
        "motivo": motivo,
        "precisa_retry": precisa_retry,
        "criterio_decisivo": _criterio_decisivo(vencedor, resto),
        "flags": vencedor["flags"],
        "abertura": vencedor["abertura"],
        "candidatos": [{k: m[k] for k in ("indice", "n_flags", "flags",
                                          "n_palavras", "n_ancoras",
                                          "abertura", "abertura_freq",
                                          "eliminado")}
                       for m in medidos],
    }


def prompt_retry(texto: str, flags: list[str]) -> str:
    """A mensagem do retry DIRECIONADO: diz o que reprovou, não "tente de
    novo". Um retry cego é só uma quarta amostra."""
    L = ["O texto abaixo foi REPROVADO. Reescreva-o corrigindo os problemas "
         "listados, mantendo o mesmo assunto e o mesmo briefing.", "",
         "TEXTO REPROVADO:", texto, "", "PROBLEMAS:"]
    for f in flags:
        L.append(f"  · {f}: {_EXPLICACAO.get(f, f)}")
    L += ["", 'Responda APENAS com JSON puro: {"veredito": "<seu texto>"}']
    return "\n".join(L)


# ===========================================================================
# O TEMPLATE determinístico — a rede, e o caminho de compatibilidade
# ===========================================================================

_PLURAL = {"poucos", "alguns", "muitos", "quase todos"}


def _em_frase(rotulo: str) -> str:
    return rotulo[0].lower() + rotulo[1:] if rotulo else rotulo


def veredito_template(b: dict) -> str:
    """O veredito da v1.9.19/v1.9.20, com a inflação retórica CORRIGIDA.

    É a rede do estágio (quando o LLM não entrega nada válido) e é o mesmo
    texto que `filme.js` produz para JSON publicado antes desta versão.

    **A correção da v1.9.21 (Entrega 6).** O ramo de um-lado-só terminava com
    a frase fixa "— um assunto que todos os grupos citam", disparada sempre
    que existia qualquer eixo com `mencoes > 0`, sem checar se a frequência
    sustenta "todos". Medido em produção: `obsession-2026` afirmava isso a
    partir de 2 de 5 reviews (40%), num grupo que o próprio site rotula como
    amostra pequena; `eighth-grade`, com amostra completa, a partir de 13 de
    34 (38%). É a mesma classe de inflação que as v1.2.2/v1.2.3 resolveram
    para a narrativa, reintroduzida num lugar novo. O quantificador passa a
    vir do mapa comum, e `modo: reduzido` vira caso à parte — cautela
    explícita, nunca generalização.
    """
    g = b["grupos"]
    neg, pos = g.get("negativas") or {}, g.get("positivas") or {}
    lift_neg, lift_pos = neg.get("eixo_maior_lift"), pos.get("eixo_maior_lift")
    neg_ok = bool(lift_neg and lift_neg["acima_da_margem"])
    pos_ok = bool(lift_pos and lift_pos["acima_da_margem"])

    if pos_ok and neg_ok:
        frase = (f"Quem recomenda destaca {_em_frase(lift_pos['eixo_rotulo'])}; "
                 f"quem não recomenda aponta {_em_frase(lift_neg['eixo_rotulo'])}.")
    elif pos_ok or neg_ok:
        com_lift = lift_pos if pos_ok else lift_neg
        lado = "negativas" if pos_ok else "positivas"
        outro = g.get(lado) or {}
        freq = outro.get("eixo_maior_frequencia")
        verbo = ("Quem recomenda destaca " if pos_ok
                 else "Quem não recomenda aponta ")
        verbo_outro = ("quem recomenda fala sobretudo de "
                       if lado == "positivas"
                       else "quem não recomenda fala sobretudo de ")
        if not freq:
            frase = (verbo + _em_frase(com_lift["eixo_rotulo"])
                     + " — do outro lado, nenhum assunto se destaca tanto assim.")
        elif outro.get("modo") == "reduzido" or outro.get("estado_piso") != "completa":
            frase = (verbo + _em_frase(com_lift["eixo_rotulo"]) + "; "
                     + verbo_outro + _em_frase(freq["eixo_rotulo"])
                     + " — amostra pequena demais para dizer mais que isso.")
        else:
            rot = freq["rotulo_quantificador"]
            verbo_mencao = "mencionam" if rot in _PLURAL else "menciona"
            frase = (verbo + _em_frase(com_lift["eixo_rotulo"]) + "; "
                     + verbo_outro + _em_frase(freq["eixo_rotulo"])
                     + f" — um assunto que {rot} naquele grupo "
                     + f"também {verbo_mencao}.")
    else:
        frase = ("Os grupos falam das mesmas coisas — discordam sobre se elas "
                 "funcionam.")

    return prefixo_de_codigo(b) + frase


# ===========================================================================
# O prompt — documentado por extenso na SPEC (§3[V])
# ===========================================================================

PROMPT_VEREDITO = """\
Você escreve o VEREDITO de um filme: UMA a DUAS frases, em português do \
Brasil, para quem AINDA NÃO ASSISTIU e está decidindo se assiste.

Não é crítica, não é resenha, não é recomendação. É o MAPA de onde as \
opiniões divergem: o leitor precisa sair sabendo sobre o que as pessoas \
discordam, não se o filme é bom.

Você recebe um BRIEFING com todas as decisões já tomadas: qual assunto usar, \
de qual grupo, com que palavra de frequência. Você NÃO escolhe assunto, NÃO \
calcula número, NÃO decide grupo — tudo isso já está resolvido.

REGRAS (todas obrigatórias):

1. FIDELIDADE: só existe o que está no briefing. É PROIBIDO introduzir \
assunto, tema, adjetivo avaliativo sobre o filme, nome de pessoa ou \
informação de enredo que não esteja ali.

2. CONTRASTE. Quando o briefing diz "valorativo", a medição NÃO encontrou \
assunto que um grupo tenha e o outro não. É PROIBIDO afirmar que os grupos \
falam de assuntos diferentes. Sua tarefa é NOMEAR o assunto compartilhado e \
dizer que a divergência é sobre se ele FUNCIONA. Concordar sobre o que o \
filme é e discordar sobre se ele funciona é um RESULTADO, não uma falta de \
resultado — escreva com essa segurança.

3. QUANTIFICADORES: escreva EXATAMENTE o quantificador que o briefing \
autoriza para aquele grupo. Um mais FORTE é PROIBIDO ("quase todos" onde o \
briefing diz "a maioria") e um mais FRACO também é PROIBIDO ("cerca de \
metade" onde o briefing diz "a maioria"). Encolher mente sobre o dado \
exatamente como inflar: o número é do sistema, não seu. É PROIBIDO também \
ENVOLVER o quantificador em algo que o desminta — "relatos pontuais apontam \
que a maioria..." diz pontual e maioria na mesma frase, e uma das duas é \
falsa.

4. ZERO DÍGITOS: nenhum algarismo na saída. Nenhuma contagem de review, \
nenhum percentual, nenhuma nota, score ou estrela. Se o briefing disser que \
o peso de um grupo é informado por fora, ele É — não escreva o número.

5. ANTI-SPOILER: nada de reviravolta, final, morte de personagem ou \
mecanismo central da trama. Os temas do briefing já passaram por esse \
filtro; use-os como estão e NÃO os expanda nem os detalhe.

6. ESCOPO: cada afirmação é de um GRUPO. É PROIBIDO generalizar para "os \
críticos", "o consenso", "a recepção do filme" ou "o público". Cada grupo é \
uma perspectiva, nunca uma fatia quantificada do público.

7. PALAVRAS SUAS: é PROIBIDO copiar um tema do briefing palavra por palavra. \
Diga o assunto com as suas palavras, sem aspas de citação.

8. AMOSTRA PEQUENA: quando o briefing marcar amostra pequena num grupo, \
diga isso — mas a cautela é sobre a AMOSTRA, nunca sobre a FREQUÊNCIA. \
Qualifique QUANTAS reviews foram analisadas, não que fatia daquele grupo \
disse aquilo. PERMITIDO: "numa amostra pequena", "entre os poucos relatos \
analisados", "no material disponível". PROIBIDO: "impressões pontuais", \
"relatos isolados", "menções esparsas" — isso afirma um tamanho, e o \
tamanho já veio no quantificador. Um grupo com amostra pequena continua \
recebendo o rótulo que o briefing deu, com a ressalva sobre a base ao lado.

8b. MESMO TRATAMENTO PARA OS DOIS LADOS: quando o briefing der o MESMO \
quantificador a quem recomenda e a quem não recomenda, os dois recebem o \
mesmo tratamento textual. É PROIBIDO nomear a frequência de um lado e \
tratar o outro como anedota. O que separa os dois grupos é o que eles \
dizem, nunca o peso que você dá a eles.

9. FORMA: 1 a 2 frases, no máximo 55 palavras, alvo de cerca de 45. Sem \
aspas, sem subtítulo, sem lista. Tom seco e informativo, nunca publicitário.

Responda APENAS com JSON puro: {"veredito": "<seu texto>"}"""


def extrair_veredito(bruto: str) -> str:
    """O texto da resposta do modelo. Mesma tolerância de
    `briefing.extrair_narrativa`: JSON bem formado no caminho normal, e o
    bruto limpo quando o modelo devolve prosa direta."""
    import json

    bruto = (bruto or "").strip()
    if not bruto:
        return ""
    try:
        d = json.loads(bruto)
    except ValueError:
        return bruto
    if isinstance(d, dict):
        for chave in ("veredito", "texto", "text"):
            if isinstance(d.get(chave), str):
                return d[chave].strip()
    return bruto


# ===========================================================================
# Orquestração: best-of-N, retry, fallback, telemetria
# ===========================================================================

def _gerar_real(system: str, user: str, *, provider: str, modelo: str):
    """Uma amostra, PELO ADAPTADOR (§3[D]) — como todo caminho de LLM do
    projeto. Usa `resposta` (e não `client_call`) porque o best-of-N precisa
    dos contadores de token: sem eles o custo de N chamadas por filme seria
    invisível no JSON."""
    from .config import PROSA_MAX_TOKENS

    t0 = time.time()
    resp = S.resposta(system, user, modelo, provider=provider,
                      max_tokens=PROSA_MAX_TOKENS, json_mode=True)
    bruto = (resp.text if provider == "gemini"
             else resp.choices[0].message.content)
    return (extrair_veredito(bruto or ""), S.uso(resp, provider),
            time.time() - t0)


def _somar(usos: list[dict]) -> dict:
    chaves = ("prompt_tokens", "completion_tokens",
              "cache_hit_tokens", "cache_miss_tokens")
    return {k: sum(u.get(k, 0) for u in usos) for k in chaves}


def gerar(output: dict, *, n: int = BEST_OF_N, provider: str | None = None,
          model: str | None = None, gerar=None,
          aberturas: dict | None = None) -> dict | None:
    """O bloco `veredito` do JSON de resultado, pronto para gravar.

    `gerar` é o ponto de injeção dos testes: `(system, user) -> (texto, uso,
    latencia_s)`. Sem ele, resolve provider e modelo POR ESTÁGIO.

    Uma amostra vazia é uma amostra PERDIDA, não uma falha do estágio: sai da
    disputa e as demais decidem (mesma política de `narrador.narrar`).
    """
    b = montar_briefing(output)
    if b is None:
        return None
    user = serializar_briefing(b)
    prefixo = prefixo_de_codigo(b)

    if gerar is None:
        provider = S.provider_do_estagio(ESTAGIO, provider)
        modelo = model or S.modelo_do_estagio(ESTAGIO, provider)

        def gerar(system, msg):  # noqa: F811 — fechado sobre provider/modelo
            return _gerar_real(system, msg, provider=provider, modelo=modelo)
    else:
        provider, modelo = provider or "injetado", model or "injetado"

    candidatos, usos, latencias = [], [], []
    for _ in range(n):
        texto, uso, dt = gerar(PROMPT_VEREDITO, user)
        usos.append(uso)
        latencias.append(dt)
        if texto:
            candidatos.append(texto)

    base = {"provider": provider, "modelo": modelo,
            "n_candidatos": len(candidatos), "n_chamadas": n,
            "prefixo_codigo": prefixo, "retry": None,
            "spec_version": SPEC_VERSION}

    def _fallback(motivo_flags, escolha=None):
        base.update(
            # `veredito_template` JÁ concatena o prefixo — é a mesma função
            # que o frontend chama para JSON antigo, e lá não há quem
            # prefixe por fora.
            texto=veredito_template(b),
            texto_modelo=None, origem="template_fallback",
            motivo="template_fallback",
            criterio_decisivo=None,
            abertura=padrao_de_abertura(veredito_template(b)),
            indice_escolhido=None,
            flags=motivo_flags,
            candidatos=(escolha or {}).get("candidatos", []),
            n_chamadas=len(usos), uso=_somar(usos),
            latencia_s=round(sum(latencias), 2))
        return base

    if not candidatos:
        return _fallback(["nenhuma_amostra_com_texto"])

    escolha = selecionar(candidatos, b, aberturas)

    # Degrau 1: nenhuma limpa -> retry DIRECIONADO, com as flags explicadas.
    if escolha["precisa_retry"]:
        texto, uso, dt = gerar(
            PROMPT_VEREDITO, prompt_retry(escolha["texto"], escolha["flags"]))
        usos.append(uso)
        latencias.append(dt)
        if texto:
            medida = _medir(texto, b, aberturas)
            # A corrigida só entra se REALMENTE melhorar — um retry que piora
            # não é conserto (mesma regra de §D2).
            aplicado = medida["n_flags"] < len(escolha["flags"])
            base["retry"] = {"flags_antes": escolha["flags"],
                             "flags_depois": medida["flags"],
                             "aplicado": aplicado}
            if aplicado:
                escolha["texto"] = texto
                escolha["flags"] = medida["flags"]
                escolha["motivo"] = "retry_direcionado"

    # Degrau 2: ainda inválida -> o TEMPLATE determinístico.
    if escolha["flags"]:
        return _fallback(escolha["flags"], escolha)

    base.update(
        texto=prefixo + escolha["texto"],
        texto_modelo=escolha["texto"],
        origem="llm",
        motivo=escolha["motivo"],
        criterio_decisivo=escolha["criterio_decisivo"],
        abertura=escolha["abertura"],
        indice_escolhido=escolha["indice"],
        flags=escolha["flags"],
        candidatos=escolha["candidatos"],
        n_chamadas=len(usos), uso=_somar(usos),
        latencia_s=round(sum(latencias), 2))
    return base
